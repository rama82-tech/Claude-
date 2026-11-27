import json, sys, numpy as np, trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union, polygonize
from shapely import affinity

def build(plan, out):
    H = plan["wall_height"]
    W = {w["id"]: w for w in plan["walls"]}
    ext = []
    for w in plan["walls"]:
        a, b = np.array(w["a"]), np.array(w["b"]); d = (b-a)/np.linalg.norm(b-a)
        ext.append(LineString([a-d*w["t"]/2, b+d*w["t"]/2]).buffer(w["t"]/2, cap_style="flat"))
    foot = unary_union(ext)
    cutters = {}
    for o in plan["openings"]:
        w = W[o["wall"]]; a, b = np.array(w["a"]), np.array(w["b"])
        d = (b-a)/np.linalg.norm(b-a); c = a + d*o["at"]
        r = box(-o["w"]/2, -w["t"]/2-0.01, o["w"]/2, w["t"]/2+0.01)
        r = affinity.rotate(r, np.degrees(np.arctan2(d[1], d[0])), origin=(0,0))
        cutters[o["id"]] = affinity.translate(r, c[0], c[1])
    allcut = unary_union(list(cutters.values()))
    meshes = []
    def ext_poly(poly, z0, z1, name, color):
        polys = [poly] if poly.geom_type == "Polygon" else list(getattr(poly, "geoms", []))
        for p in polys:
            if p.geom_type != "Polygon" or p.area < 1e-6: continue
            m = trimesh.creation.extrude_polygon(p, z1 - z0)
            m.apply_translation([0, 0, z0]); m.visual.face_colors = color
            meshes.append(m)
    wc = [235,232,225,255]
    ext_poly(foot.difference(allcut), 0, H, "walls", wc)
    for o in plan["openings"]:
        piece = foot.intersection(cutters[o["id"]])
        if o["sill"] > 0: ext_poly(piece, 0, o["sill"], o["id"]+"_sill", wc)
        ext_poly(piece, o["head"], H, o["id"]+"_head", wc)
    lines = unary_union([LineString([w["a"], w["b"]]) for w in plan["walls"]])
    floors = {"oak":[176,140,98,255], "carpet":[150,150,160,255]}
    for r in polygonize(lines):
        lab = next((q for q in plan["rooms"] if r.contains(Point(q["at"]))), None)
        fl = r.difference(foot)
        print(f"room {lab['label'] if lab else '?'}: clear floor {fl.area:.2f} m2 = {fl.area*10.7639:.0f} sq ft")
        if lab: ext_poly(fl, -0.1, 0, "floor", floors[lab["floor"]])
    ext_poly(Polygon(foot.exterior), -0.2, -0.1, "slab", [120,120,120,255])
    trimesh.Scene(meshes).export(out)
    return meshes

if __name__ == "__main__":
    plan = json.load(open(sys.argv[1])); meshes = build(plan, sys.argv[2])
    print("meshes", len(meshes), "watertight", all(m.is_watertight for m in meshes))
    print("bounds", trimesh.util.concatenate(meshes).bounds.round(3).tolist())
