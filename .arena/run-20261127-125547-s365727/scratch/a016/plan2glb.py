#!/usr/bin/env python3
"""v0: plan image -> GLB. Usage: plan2glb.py plan.png --px-per-m 50 [--height 2.7] [--min-wall-m 0.08] [-o house.glb]"""
import argparse, cv2, numpy as np, trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

def extract_wall_polys(path, px_per_m, min_wall_m):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None: raise SystemExit(f"cannot read {path}")
    _, bw = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    k = max(3, int(round(min_wall_m * px_per_m)))
    walls = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    cnts, hier = cv2.findContours(walls, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None: raise SystemExit("no walls found")
    hier = hier[0]; H = img.shape[0]
    def to_m(c):
        c = cv2.approxPolyDP(c, 1.5, True)[:, 0, :].astype(float)
        return [(x / px_per_m, (H - y) / px_per_m) for x, y in c]
    polys = []
    for i, c in enumerate(cnts):
        if hier[i][3] != -1 or len(c) < 3: continue          # outer contours only
        holes = [to_m(cnts[j]) for j in range(len(cnts)) if hier[j][3] == i and len(cnts[j]) >= 3]
        p = Polygon(to_m(c), holes).buffer(0)
        if p.area > 0.05: polys.append(p)
    return unary_union(polys)

def build(walls, height, slab=0.15):
    meshes = []
    geoms = list(walls.geoms) if hasattr(walls, "geoms") else [walls]
    for g in geoms:
        m = trimesh.creation.extrude_polygon(g, height); m.visual.face_colors = [225, 225, 220, 255]; meshes.append(m)
    env = unary_union([Polygon(g.exterior) for g in geoms])
    envs = list(env.geoms) if hasattr(env, "geoms") else [env]
    for e in envs:
        f = trimesh.creation.extrude_polygon(e, slab); f.apply_translation([0, 0, -slab]); f.visual.face_colors = [150, 130, 110, 255]; meshes.append(f)
    return trimesh.Scene(meshes)

if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("plan"); a.add_argument("--px-per-m", type=float, required=True)
    a.add_argument("--height", type=float, default=2.7); a.add_argument("--min-wall-m", type=float, default=0.08)
    a.add_argument("-o", default="house.glb"); a = a.parse_args()
    w = extract_wall_polys(a.plan, a.px_per_m, a.min_wall_m)
    sc = build(w, a.height); sc.export(a.o)
    print(f"wall area {w.area:.2f} m2, bounds {[round(v,2) for v in w.bounds]}, wrote {a.o}")
