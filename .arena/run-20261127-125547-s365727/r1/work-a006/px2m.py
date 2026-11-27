"""px_plan.json (pixels, y down) -> plan.json (metres, y up). Two printed dimensions give separate x and y scales."""
import json, sys
def convert(px, wall_h=2.7):
    c = px["calibration"]      # {"x":[px0,px1,metres], "y":[py0,py1,metres]}  (y: py0 = top end of the printed dimension)
    sx = c["x"][2]/abs(c["x"][1]-c["x"][0]); sy = c["y"][2]/abs(c["y"][1]-c["y"][0])
    skew = abs(sx-sy)/max(sx, sy)
    if skew > 0.02: print(f"WARNING: x/y scale differ by {skew:.1%}: using separate x and y scales; check the overlay")
    x0 = min(c["x"][:2]); y0 = max(c["y"][:2])           # origin: left end of x dimension, bottom end of y dimension
    f = lambda p: [round((p[0]-x0)*sx, 4), round((y0-p[1])*sy, 4)]
    walls = [{"id":w["id"], "a":f(w["a"]), "b":f(w["b"]), "t":w.get("t", .2032 if w["kind"]=="exterior" else .1143), "kind":w["kind"]} for w in px["walls"]]
    wl = {w["id"]: w for w in walls}
    ops = []
    for o in px["openings"]:           # px opening: wall, "at_px" = pixel point on the wall at the opening centre, "w_px"
        w = wl[o["wall"]]; a, b = w["a"], w["b"]; L = ((b[0]-a[0])**2+(b[1]-a[1])**2)**.5
        p = f(o["at_px"]); at = ((p[0]-a[0])*(b[0]-a[0])+(p[1]-a[1])*(b[1]-a[1]))/L   # project onto the wall
        wm = o["w_px"]*(sx if abs(b[0]-a[0]) >= abs(b[1]-a[1]) else sy)
        ops.append({"id":o["id"], "wall":o["wall"], "at":round(at,4), "w":round(wm,4), "type":o["type"],
                    "sill":o.get("sill", 0 if o["type"]=="door" else .9), "head":o.get("head", 2.1)})
    rooms = [{"label":r["label"], "at":f(r["at_px"]), "floor":r.get("floor","floor_default")} for r in px["rooms"]]
    return {"units":"m", "wall_height":wall_h, "walls":walls, "openings":ops, "rooms":rooms}
if __name__ == "__main__":
    json.dump(convert(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=1)
