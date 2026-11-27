import json, sys, numpy as np, trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union, polygonize
from shapely import affinity
from trimesh.visual.material import PBRMaterial

MAT = {  # role -> (baseColor RGBA 0-255, roughness, metallic)
  "wall_ext": ([225,222,214,255], .9, 0), "wall_int": ([240,238,232,255], .9, 0),
  "slab": ([120,120,120,255], .95, 0), "threshold": ([150,140,125,255], .8, 0),
  "oak": ([176,140,98,255], .6, 0), "carpet": ([150,150,160,255], 1, 0),
  "tile": ([200,205,210,255], .3, 0), "floor_default": ([190,190,190,255], .8, 0),
  "glass": ([170,210,230,90], .05, 0), "door": ([120,80,50,255], .6, 0)}

def pbr(role):
    c, r, m = MAT.get(role, MAT["floor_default"])
    return PBRMaterial(name=role, baseColorFactor=c, roughnessFactor=r, metallicFactor=m,
                       alphaMode="BLEND" if c[3] < 255 else "OPAQUE")

def polys(g):
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 1e-6]

def build(plan, out):
    H = plan["wall_height"]
    W = {w["id"]: w for w in plan["walls"]}
    solid = [w for w in plan["walls"] if w.get("kind") != "divider"]   # dividers: labelling only
    def rect(w):
        a, b = np.array(w["a"]), np.array(w["b"]); d = (b-a)/np.linalg.norm(b-a)
        return LineString([a-d*w["t"]/2, b+d*w["t"]/2]).buffer(w["t"]/2, cap_style="flat")
    ext = unary_union([rect(w) for w in solid if w["kind"] == "exterior"] or [Polygon()])
    intr = unary_union([rect(w) for w in solid if w["kind"] != "exterior"] or [Polygon()]).difference(ext)
    foot = unary_union([ext, intr])
    cut = {}
    for o in plan["openings"]:
        w = W[o["wall"]]; a, b = np.array(w["a"]), np.array(w["b"])
        d = (b-a)/np.linalg.norm(b-a); c = a + d*o["at"]
        r = box(-o["w"]/2, -w["t"]/2-0.01, o["w"]/2, w["t"]/2+0.01)
        r = affinity.rotate(r, np.degrees(np.arctan2(d[1], d[0])), origin=(0,0))
        cut[o["id"]] = affinity.translate(r, c[0], c[1])
    allcut = unary_union(list(cut.values()))
    scene = trimesh.Scene(); n = [0]
    def add(poly, z0, z1, role):
        for p in polys(poly):
            m = trimesh.creation.extrude_polygon(p, z1 - z0)
            m.apply_translation([0, 0, z0])
            m.visual = trimesh.visual.TextureVisuals(material=pbr(role))
            n[0] += 1; scene.add_geometry(m, node_name=f"{role}_{n[0]}", geom_name=f"{role}_{n[0]}")
    for role, f in (("wall_ext", ext), ("wall_int", intr)):
        add(f.difference(allcut), 0, H, role)
        for o in plan["openings"]:
            piece = f.intersection(cut[o["id"]])
            if o["sill"] > 0: add(piece, 0, o["sill"], role)
            add(piece, o["head"], H, role)
    # glass panes in windows (thin box in the middle of the wall)
    for o in plan["openings"]:
        if o["type"] == "window":
            piece = foot.intersection(cut[o["id"]])
            c = piece.centroid; ang = np.degrees(np.arctan2(*(np.array(W[o["wall"]]["b"])-np.array(W[o["wall"]]["a"]))[::-1]))
            g = affinity.rotate(box(-o["w"]/2, -0.01, o["w"]/2, 0.01), ang, origin=(0,0))
            add(affinity.translate(g, c.x, c.y), o["sill"], o["head"], "glass")
    lines = unary_union([LineString([w["a"], w["b"]]) for w in plan["walls"]])  # includes dividers
    rooms_union = []
    report = []
    for r in polygonize(lines):
        lab = next((q for q in plan["rooms"] if r.contains(Point(q["at"]))), None)
        fl = r.difference(foot)
        rooms_union.append(fl)
        report.append((lab["label"] if lab else "?", fl.area))
        print(f"room {lab['label'] if lab else '?'}: clear floor {fl.area:.2f} m2 = {fl.area*10.7639:.0f} sq ft")
        add(fl, -0.1, 0, lab["floor"] if lab else "floor_default")
    add(foot.intersection(allcut), -0.1, 0, "threshold")       # floor under every doorway/window
    # slab: fill each footprint polygon's exterior ring, so stray disconnected walls cannot crash this
    slab = unary_union([Polygon(p.exterior) for p in polys(foot)])
    add(slab, -0.2, -0.1, "slab")
    # glTF and three.js are Y-up: rotate the Z-up model -90 deg about X so plan-north becomes -Z, height becomes +Y
    scene.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [1, 0, 0]))
    scene.export(out)
    return scene

if __name__ == "__main__":
    plan = json.load(open(sys.argv[1])); sc = build(plan, sys.argv[2])
    ms = list(sc.geometry.values())
    print("meshes", len(ms), "watertight", all(m.is_watertight for m in ms))
    print("bounds (x, y=up, z)", sc.bounds.round(3).tolist())
    print("names", sorted(sc.geometry)[:6], "...")
