"""python overlay.py plan_image.png px_plan.json overlay.png  -> walls red, doors green, windows blue, ids and labels"""
import json, sys
from PIL import Image, ImageDraw
img = Image.open(sys.argv[1]).convert("RGB"); px = json.load(open(sys.argv[2])); d = ImageDraw.Draw(img)
W = {w["id"]: w for w in px["walls"]}
for w in px["walls"]:
    d.line([*w["a"], *w["b"]], fill=(255,0,0), width=3); d.text(((w["a"][0]+w["b"][0])/2+4, (w["a"][1]+w["b"][1])/2+4), w["id"], fill=(255,0,0))
for o in px["openings"]:
    x, y = o["at_px"]; h = o["w_px"]/2; horiz = abs(W[o["wall"]]["b"][0]-W[o["wall"]]["a"][0]) >= abs(W[o["wall"]]["b"][1]-W[o["wall"]]["a"][1])
    col = (0,160,0) if o["type"] == "door" else (0,0,255)
    d.line([x-h, y, x+h, y] if horiz else [x, y-h, x, y+h], fill=col, width=7); d.text((x+4, y-14), o["id"], fill=col)
for r in px["rooms"]: d.text(tuple(r["at_px"]), r["label"], fill=(0,0,0))
img.save(sys.argv[3])
