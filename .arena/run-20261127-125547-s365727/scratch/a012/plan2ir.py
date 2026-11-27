#!/usr/bin/env python3
"""plan2ir.py  plan.png --ppm 100 [--wall-min 0.08] [--out plan.json]
Axis-aligned wall + opening extraction from a clean raster plan. Units: metres, y down (image order)."""
import argparse, json, cv2, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("image"); ap.add_argument("--ppm", type=float, required=True, help="pixels per metre")
ap.add_argument("--wall-min", type=float, default=0.08, help="thinnest real wall (m)")
ap.add_argument("--min-len", type=float, default=0.6, help="shortest wall bar kept (m)")
ap.add_argument("--height", type=float, default=2.7)
ap.add_argument("--out", default="plan.json")
a = ap.parse_args()

g = cv2.imread(a.image, cv2.IMREAD_GRAYSCALE)
if g is None: raise SystemExit("cannot read image")
_, ink = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
ppm = a.ppm
k = max(2, int(a.wall_min * ppm))            # kill text / dimension lines thinner than this
solid = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
L = max(3, int(a.min_len * ppm))
bars = []
for orient, ker in (("h", (L, 1)), ("v", (1, L))):
    m = cv2.morphologyEx(solid, cv2.MORPH_OPEN, np.ones((ker[1], ker[0]), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    for x, y, w, h, _ar in st[1:]:
        if orient == "h" and w >= h * 1.5: bars.append(("h", y + h / 2, x, x + w, h))
        if orient == "v" and h >= w * 1.5: bars.append(("v", x + w / 2, y, y + h, w))

# merge collinear bars separated by a door/window-sized gap -> one wall + one opening
walls, openings = [], []
tol = 0.5 * k
for o in ("h", "v"):
    bs = sorted([b for b in bars if b[0] == o], key=lambda b: (round(b[1] / tol), b[2]))
    cur = None
    def flush():
        if cur: walls.append(cur)
    for _, c, s, e, t in bs:
        if cur and cur["o"] == o and abs(cur["c"] - c) <= tol and 0.5 * ppm <= s - cur["e"] <= 2.6 * ppm:
            cur["gaps"].append((cur["e"], s)); cur["e"] = e; cur["t"] = max(cur["t"], t)
        else:
            flush(); cur = dict(o=o, c=c, s=s, e=e, t=t, gaps=[])
    flush()

out = {"units": "m", "height": a.height, "source": a.image, "walls": [], "openings": [], "rooms": []}
for i, w in enumerate(walls):
    s, e, c = w["s"] / ppm, w["e"] / ppm, w["c"] / ppm
    A, B = ([s, c], [e, c]) if w["o"] == "h" else ([c, s], [c, e])
    out["walls"].append({"id": f"w{i}", "a": [round(v, 3) for v in A], "b": [round(v, 3) for v in B],
                         "t": round(w["t"] / ppm, 3), "h": a.height})
    for j, (gs, ge) in enumerate(w["gaps"]):
        wid = (ge - gs) / ppm
        out["openings"].append({"id": f"o{i}_{j}", "wall": f"w{i}", "type": "door",   # type is a GUESS: review it
                                "offset": round(((gs + ge) / 2 - w["s"]) / ppm, 3), "width": round(wid, 3),
                                "sill": 0.0, "height": 2.05, "confidence": "low"})
json.dump(out, open(a.out, "w"), indent=1)
print(f"{len(out['walls'])} walls, {len(out['openings'])} openings -> {a.out}")
