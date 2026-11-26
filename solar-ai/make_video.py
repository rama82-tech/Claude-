"""Renders solar_ai_training.mp4: learning curve, side-by-side storm day (fixed vs untrained vs trained AI), results.
   python make_video.py [out.mp4]   (needs results.json, solar_agent*, evaluate.py; PIL + ffmpeg)"""
import math, json, subprocess, sys
import numpy as np, h5py
from PIL import Image, ImageDraw, ImageFont
import evaluate as E

W, H, FPS, S = 1280, 720, 20, 1.5
FD = "/usr/share/fonts/truetype/dejavu/"
def font(sz, bold=False): return ImageFont.truetype(FD + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), int(sz * S))
class Cv:
    def __init__(s, color="white"): s.im = Image.new("RGB", (int(W*S), int(H*S)), color); s.d = ImageDraw.Draw(s.im)
    def sc(s, p): return [v*S for v in p]
    def rect(s, b, fill=None, outline=None, w=1, r=0):
        if r: s.d.rounded_rectangle(s.sc(b), r*S, fill=fill, outline=outline, width=int(w*S))
        else: s.d.rectangle(s.sc(b), fill=fill, outline=outline, width=int(w*S))
    def ell(s, b, fill=None, outline=None, w=1): s.d.ellipse(s.sc(b), fill=fill, outline=outline, width=int(w*S))
    def line(s, pts, fill, w=2): s.d.line(s.sc(sum(([x, y] for x, y in pts), [])), fill=fill, width=max(1, int(w*S)), joint="curve")
    def poly(s, pts, fill, outline=None): s.d.polygon(s.sc(sum(([x, y] for x, y in pts), [])), fill=fill, outline=outline)
    def text(s, xy, t, sz=24, fill="#222", bold=False, anchor="la"): s.d.text((xy[0]*S, xy[1]*S), t, font=font(sz, bold), fill=fill, anchor=anchor)
    def out(s): return s.im.resize((W, H), Image.LANCZOS)
def ease(t): t = max(0, min(1, t)); return t*t*(3-2*t)
def seg(t, a, b): return ease((t-a)/(b-a))
NAVY, ORANGE = "#10243f", "#ffb02e"

# ---------------------------------------------------------------- data
RES = json.load(open("results.json"))
with h5py.File("solar_agent_training_data.h5") as hf: TRAIN = np.array(hf["epsiode_returns"][()])
DEMO_SEED = 912
ai = E.load("solar_agent")
REC = {
    "Fixed panel (never moves)": E.episode(E.fixed, DEMO_SEED, True, True)[3],
    "Untrained AI (random moves)": E.episode(E.rnd_policy(np.random.default_rng(DEMO_SEED)), DEMO_SEED, True, True)[3],
    "Trained AI": E.episode(lambda o, e: ai.act(o), DEMO_SEED, True, True)[3],
}
NSTEP = 144

def caption(c, title, sub, prog):
    c.rect((0, 640, W, H), fill=NAVY); c.rect((0, 640, W*prog, 645), fill=ORANGE)
    c.text((34, 652), title, 26, "white", True); c.text((34, 690), sub, 19, "#c9d6e6")

# ---------------------------------------------------------------- scenes
def s_title(c, t, tm):
    c.rect((0, 0, W, H), fill=NAVY)
    for i in range(12):
        a = i*math.pi/6 + tm*.5; c.line([(1020+80*math.cos(a), 250+80*math.sin(a)), (1020+120*math.cos(a), 250+120*math.sin(a))], ORANGE, 5)
    c.ell((960, 190, 1080, 310), fill="#ffd34d")
    a = 0.6*math.sin(tm*1.5)
    pts = [(1020 + 150*math.cos(a)*u, 520 + 150*math.sin(a)*u) for u in (-1, 1)]
    c.line([(1020, 640), (1020, 520)], "#9aa7b5", 10); c.line(pts, "#2f6fd0", 22); c.line(pts, "#7fb2ff", 4)
    k = seg(t, .05, .35)
    c.text((70, 190-(1-k)*20), "An AI learns to run", 44, "white", True); c.text((70, 250-(1-k)*20), "a solar panel", 72, ORANGE, True)
    c.text((72, 360), "from zero.  Track the sun. Survive the storm.", 28, "#c9d6e6")
    c.text((72, 420), "Deep Q-learning (DQN)  ·  PyTorch  ·  gymnasium", 20, "#8fa6c0")
    return "Solar AI", "Built on the uploaded lunar-lander DQN agent (agent_class.py)", 0

def s_how(c, t, tm):
    c.rect((0, 0, W, H), fill="#eaf1f8")
    boxes = [("SEES", "time of day · sun position · panel angle\ncloud cover · wind speed · wind trend", 80),
             ("DOES", "rotate east  ·  rotate west\nhold  ·  stow flat (safe mode)", 470),
             ("EARNS", "+ energy harvested each 5 min\n− small motor cost\n− big penalty if a storm damages it", 860)]
    for i, (h, body, x) in enumerate(boxes):
        k = seg(t, i*.22, i*.22+.2)
        if k <= 0: continue
        y = 190 + (1-k)*40
        c.rect((x, y, x+340, y+250), fill="white", outline=NAVY, w=3, r=16); c.text((x+170, y+40), h, 34, ORANGE, True, "mm")
        for j, ln in enumerate(body.split("\n")): c.text((x+170, y+95+j*34), ln, 18, NAVY, False, "mm")
        if i < 2: c.text((x+372, y+125), "→", 40, NAVY, True, "mm")
    c.text((W/2, 90), "How the AI learns", 46, NAVY, True, "mm")
    c.text((W/2, 520), "It starts knowing nothing. It only learns from the reward.", 26, "#35506f", False, "mm")
    return "The setup", "One episode = one daylight day (144 steps of 5 minutes). Storms hit about half the days.", 0

def s_curve(c, t, tm):
    c.rect((0, 0, W, H), fill="white")
    X0, X1, Y0, Y1 = 130, 1030, 130, 560; n = len(TRAIN); ymin, ymax = -70, 110
    px = lambda i: X0 + (X1-X0)*i/(n-1); py = lambda v: Y1 - (Y1-Y0)*(v-ymin)/(ymax-ymin)
    c.rect((X0, Y0, X1, Y1), outline="#c8d0da", w=2)
    for v in (-50, 0, 50, 100): c.line([(X0, py(v)), (X1, py(v))], "#e6ebf1", 1); c.text((X0-12, py(v)), str(v), 17, "#667", False, "rm")
    for name, key, col in (("expert rule", None, "#1fa84f"), ("random", None, "#9aa7b5"), ("fixed panel", None, "#c62828")):
        v = {"expert rule": RES["baselines"]["expert rule"]["mean"], "random": RES["baselines"]["random (untrained)"]["mean"], "fixed panel": RES["baselines"]["fixed panel"]["mean"]}[name]
        for x in range(X0, X1, 16): c.line([(x, py(v)), (x+8, py(v))], col, 3)
        c.text((X1+8, py(v)), f"{name} {v:.0f}", 16, col, True, "lm")
    m = max(2, int(n * ease(t/0.85))) if t < .85 else n
    for i in range(1, m): c.line([(px(i-1), py(TRAIN[i-1])), (px(i), py(TRAIN[i]))], "#9cc3f5", 2)
    run = np.convolve(TRAIN, np.ones(15)/15, mode="valid")
    for i in range(1, max(2, m-14)): c.line([(px(i+13), py(run[i-1])), (px(i+14), py(run[i]))], NAVY, 5) if i < len(run) else None
    c.text((X0+(X1-X0)/2, 90), "Learning from zero: reward per training day", 34, NAVY, True, "mm")
    c.text((X0+(X1-X0)/2, Y1+40), f"training episodes (days)  -  {m} / {n}", 20, "#445", False, "mm")
    c.text((X0+10, Y1-22), "early: random moves, panels break", 18, "#c62828", True) if m < n*.35 else None
    if m > n*.6: c.text((X1-10, Y1-22), "later: tracks the sun, stows in storms", 18, "#1fa84f", True, "rm")
    c.text((70, 345), "reward", 20, "#445", False, "mm")
    return "Training", f"Trained in {n} days of simulated sun. Thin = each day, thick = 15-day average.", 0

def draw_panel_col(c, x0, label, rec, step, tm):
    cw, top, bot = 380, 110, 440
    r = rec[min(step, len(rec)-1)]; ended = step >= len(rec) and rec[-1]["damage"] >= 3
    wind, cloud = r["wind"], r["cloud"]
    dark = min(1, max(0, (wind-.3)/.6))
    for y in range(top, bot, 5):
        k = (y-top)/(bot-top)
        c.rect((x0, y, x0+cw, y+5), fill=(int((150+70*k)*(1-.55*dark)), int((200+35*k)*(1-.5*dark)), int((250-10*k)*(1-.35*dark))))
    c.rect((x0, bot-45, x0+cw, bot), fill="#6aa05a" if dark < .5 else "#4c7a43")
    px_, py_ = x0+cw/2, bot-95
    ts = r["sun"]; sx = px_ + 150*math.sin(math.radians(ts)); sy = py_ - 190*math.cos(math.radians(ts)) + 40
    c.line([(x0+cw/2+150*math.sin(math.radians(a)), py_-190*math.cos(math.radians(a))+40) for a in range(-75, 76, 5)], "#ffe28a", 2)
    if cloud < .98: c.ell((sx-20, sy-20, sx+20, sy+20), fill="#ffd34d", outline="#f0a800", w=2)
    nc = int(1 + cloud*4)
    for i in range(nc):
        cx = x0 + 60 + ((i*83 + tm*6) % (cw-80)); cy = top + 25 + (i*29) % 50; g = int(240-80*dark)
        for dx, rr in ((-14, 15), (0, 20), (16, 14)): c.ell((cx+dx-rr, cy-rr*.7, cx+dx+rr, cy+rr*.7), fill=(g, g, g+5))
    for i in range(int(wind*9)):
        wy = top + 70 + (i*37) % 180; wx = x0 + ((i*131 + tm*220) % (cw+60)) - 30
        c.line([(wx, wy), (wx+34, wy)], "#ffffff" if dark < .5 else "#d7e3f1", 2)
    ang = r["angle"]; dam = r["damage"]
    c.line([(px_, bot-45), (px_, py_)], "#555", 9)
    a = math.radians(ang); L = 66
    p1 = (px_ - L*math.cos(a), py_ - L*math.sin(a)); p2 = (px_ + L*math.cos(a), py_ + L*math.sin(a))
    col = "#2f6fd0" if dam == 0 else "#b3382c"
    if ended: p2 = (p2[0], p2[1] + 22); col = "#7a2a22"
    c.line([p1, p2], col, 15); c.line([p1, p2], "#8fbaff" if dam == 0 else "#e88", 3)
    # sunlight ray when panel catches it
    if cloud < .9 and not ended and r["power"] > .05:
        c.line([(sx, sy), (px_, py_)], (255, 226, 120), 2)
    st = "STOWED (safe)" if abs(ang) <= 15 and wind > .6 else ("DAMAGED!" if dam and not ended else "TRACKING")
    if ended: st = "PANEL BROKEN"
    if abs(ang) > 15 and wind > .8 and not ended: c.text((x0+cw/2, top+16), "! STORM DAMAGE !", 22, "#ff3b30", True, "mm")
    energy = sum(q["power"] for q in rec[:min(step+1, len(rec))] if not (q["wind"] > .8 and abs(q["angle"]) > 15))
    c.rect((x0, bot+8, x0+cw, bot+168), fill="white", outline="#c8d0da", w=2, r=10)
    c.text((x0+14, bot+16), label, 21, NAVY, True)
    c.text((x0+14, bot+42), f"energy {energy:5.1f}", 30, "#c26a00", True)
    c.text((x0+14, bot+86), st, 16, "#c62828" if ("DAM" in st or "BROKEN" in st) else ("#1565c0" if "STOWED" in st else "#1fa84f"), True)
    bw = (cw-28) * min(1, r["power"]); c.rect((x0+14, bot+110, x0+cw-14, bot+128), fill="#e6ebf1", r=5); c.rect((x0+14, bot+110, x0+14+max(2, bw), bot+128), fill=ORANGE, r=5)
    c.text((x0+14, bot+134), f"power now · wind {wind:.2f} · cloud {cloud:.2f}", 15, "#667")

def s_demo(c, t, tm):
    c.rect((0, 0, W, H), fill="#f4f7fb")
    step = int(t * (NSTEP + 6)); step = min(step, NSTEP)
    for i, (label, rec) in enumerate(REC.items()): draw_panel_col(c, 30 + i*410, label, rec, step, tm)
    hh = 6 + 12*step/NSTEP * 1.0; c.text((W/2, 60), f"Same stormy day  ·  {int(6+hh-6):02d}:{int((hh%1)*60):02d}" if False else f"Same stormy day  -  {int(6 + 12*step/NSTEP):02d}:{int((12*step/NSTEP*60) % 60):02d}", 30, NAVY, True, "mm")
    return "Live test", "Wind rises mid-day. The trained AI flattens the panel in time; the fixed panel is wrecked.", 0

def s_results(c, t, tm):
    c.rect((0, 0, W, H), fill="white")
    c.text((W/2, 62), "Result on 300 days it never saw in training", 34, NAVY, True, "mm")
    rows = [("Fixed panel", RES["baselines"]["fixed panel"], "#c62828"), ("Random moves", RES["baselines"]["random (untrained)"], "#9aa7b5"),
            ("Trained AI (avg of 5 runs)", dict(mean=RES["ai_avg"]["mean"], broken_pct=RES["ai_avg"]["broken_pct"]), "#2f6fd0"),
            ("Expert rule (hand-written)", RES["baselines"]["expert rule"], "#1fa84f")]
    for i, (name, d, col) in enumerate(rows):
        y = 130 + i*105; k = seg(t, i*.15, i*.15+.3)
        c.text((60, y+10), name, 24, NAVY, True); c.rect((60, y+52, 900, y+84), fill="#eef2f7", r=8)
        c.rect((60, y+52, 60 + 840*max(0, d["mean"])/100*k, y+84), fill=col, r=8)
        if k > .9:
            c.text((920, y+68), f'{d["mean"]:.1f}', 30, col, True, "lm"); c.text((1010, y+68), f'{d["broken_pct"]:.1f}% broken', 17, "#667", False, "lm")
    c.text((60, 560), "score = energy harvested minus penalties (higher is better).", 18, "#445")
    seeds = RES["seeds"]; vals = "  ".join(f'{v["mean"]:.0f}' for v in seeds.values())
    c.text((60, 590), f"Five separate trainings scored: {vals}. Panel broke on 0 to 4% of days; one run is not guaranteed safe.", 18, "#c26a00", True)
    return "Takeaway", "A learned controller reaches about 93% of the hand-written expert, with no rules given.", 0

SCENES = [(s_title, 4), (s_how, 8), (s_curve, 9), (s_demo, 24), (s_results, 9)]
TOTAL = sum(d for _, d in SCENES)

def main(out):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for f in range(int(TOTAL*FPS)):
        gt = f/FPS; acc = 0
        for fn, dur in SCENES:
            if gt < acc+dur: t = (gt-acc)/dur; break
            acc += dur
        c = Cv(); title, sub, _ = fn(c, t, gt); caption(c, title, sub, gt/TOTAL)
        ff.stdin.write(c.out().tobytes())
    ff.stdin.close(); ff.wait()

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--frame":      # debug: --frame scene_idx t out.png
        fn = SCENES[int(sys.argv[2])][0]; c = Cv(); ti, su, _ = fn(c, float(sys.argv[3]), 3.0); caption(c, ti, su, .5); c.out().save(sys.argv[4])
    else: main(sys.argv[1] if len(sys.argv) > 1 else "solar_ai_training.mp4")
