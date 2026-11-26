"""Renders 'Solar Panel Training' - an animated agent demonstrating the steps. PIL + ffmpeg only."""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, S = 1280, 720, 20, 1.5
FD = "/usr/share/fonts/truetype/dejavu/"
def font(sz, bold=False): return ImageFont.truetype(FD + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), int(sz * S))

class Cv:
    def __init__(s):
        s.im = Image.new("RGB", (int(W*S), int(H*S)), "white"); s.d = ImageDraw.Draw(s.im)
    def sc(s, p): return [v*S for v in p]
    def rect(s, b, fill=None, outline=None, w=1, r=0):
        if r: s.d.rounded_rectangle(s.sc(b), r*S, fill=fill, outline=outline, width=int(w*S))
        else: s.d.rectangle(s.sc(b), fill=fill, outline=outline, width=int(w*S))
    def ell(s, b, fill=None, outline=None, w=1): s.d.ellipse(s.sc(b), fill=fill, outline=outline, width=int(w*S))
    def line(s, pts, fill, w=2): s.d.line(s.sc(sum(([x, y] for x, y in pts), [])), fill=fill, width=int(w*S), joint="curve")
    def poly(s, pts, fill, outline=None): s.d.polygon(s.sc(sum(([x, y] for x, y in pts), [])), fill=fill, outline=outline)
    def text(s, xy, t, sz=24, fill="#222", bold=False, anchor="la"):
        s.d.text((xy[0]*S, xy[1]*S), t, font=font(sz, bold), fill=fill, anchor=anchor)
    def out(s): return s.im.resize((W, H), Image.LANCZOS)

def ease(t): t = max(0, min(1, t)); return t*t*(3-2*t)
def seg(t, a, b): return ease((t-a)/(b-a))
def lerp(a, b, k): return a + (b-a)*k
def lerp2(p, q, k): return (lerp(p[0], q[0], k), lerp(p[1], q[1], k))

def bg(c, ground=520, sun=True, tm=0):
    for y in range(0, ground, 6):
        k = y/ground; c.rect((0, y, W, y+6), fill=(int(150+70*k), int(200+35*k), int(250-10*k)))
    c.rect((0, ground, W, H), fill="#6aa05a"); c.rect((0, ground, W, ground+8), fill="#527f45")
    if sun:
        for i in range(10):
            a = i*math.pi/5 + tm*0.6
            c.line([(1130+62*math.cos(a), 90+62*math.sin(a)), (1130+88*math.cos(a), 90+88*math.sin(a))], "#ffc83a", 4)
        c.ell((1085, 45, 1175, 135), fill="#ffd34d", outline="#f0a800", w=3)

def panel(c, x, y, w, h, tilt=0, glow=0, clean=1.0):
    # parallelogram panel with cell grid; tilt skews the top edge
    sk = tilt
    P = lambda u, v: (x + u*w + (1-v)*sk, y + v*h)
    base = "#17356b" if clean > .5 else "#2c4468"
    c.poly([P(0,0),P(1,0),P(1,1),P(0,1)], fill=base, outline="#c8d0da")
    for i in range(1, 6): c.line([P(i/6,0), P(i/6,1)], "#4f78b8", 2)
    for j in range(1, 4): c.line([P(0,j/4), P(1,j/4)], "#4f78b8", 2)
    if glow: c.poly([P(0,0),P(.5,0),P(.3,1),P(0,1)], fill=(60+int(40*glow), 100+int(60*glow), 170+int(50*glow)))

def robot(c, x, y, la, ra, tm=0, helmet=0, gloves=0, glasses=0, mood="ok", hold=None):
    """x,y = feet centre. la/ra = hand target points (absolute) or None for relaxed."""
    bob = 3*math.sin(tm*4)
    y += 0
    c.ell((x-50, y-8, x+50, y+8), fill="#4a7a3d")                       # shadow
    for dx in (-18, 18): c.rect((x+dx-9, y-50, x+dx+9, y), fill="#5b6770", r=4)   # legs
    c.rect((x-38, y-130+bob, x+38, y-45+bob), fill="#e8eef5", outline="#5b6770", w=3, r=14)  # body
    c.rect((x-20, y-110+bob, x+20, y-80+bob), fill="#ffb02e", r=6)     # chest panel
    c.text((x, y-95+bob), "BL", 17, "#222", True, "mm")
    # head
    hx, hy = x, y-170+bob
    c.line([(hx, hy-38), (hx, hy-56)], "#5b6770", 3); c.ell((hx-6, hy-64, hx+6, hy-52), fill="#ff5252")
    c.rect((hx-34, hy-36, hx+34, hy+30), fill="#e8eef5", outline="#5b6770", w=3, r=16)
    blink = (int(tm*1.3) % 4 == 3) and (tm*1.3 % 1 < .15)
    for ex in (-14, 14):
        if blink: c.line([(hx+ex-7, hy-4), (hx+ex+7, hy-4)], "#1a2a3a", 3)
        else: c.ell((hx+ex-7, hy-11, hx+ex+7, hy+3), fill="#1a2a3a"); c.ell((hx+ex-3, hy-9, hx+ex, hy-5), fill="white")
    if mood == "ok": c.line([(hx-12, hy+14), (hx-4, hy+19), (hx+4, hy+19), (hx+12, hy+14)], "#1a2a3a", 3)
    else: c.line([(hx-10, hy+19), (hx+10, hy+19)], "#1a2a3a", 3)
    if glasses: c.rect((hx-27, hy-17, hx+27, hy+4), outline="#2a9df4", w=4, r=7)
    if helmet:
        c.rect((hx-40, hy-52, hx+40, hy-30), fill="#ffd400", outline="#b89600", w=3, r=12)
        c.rect((hx-48, hy-34, hx+48, hy-28), fill="#ffd400", outline="#b89600", w=2, r=3)
    # arms
    for side, tgt in ((-1, la), (1, ra)):
        sx, sy = x+side*38, y-118+bob
        if tgt is None: tgt = (x+side*62, y-52+bob+6*math.sin(tm*3+side))
        ex_, ey_ = (sx+tgt[0])/2 + side*8, (sy+tgt[1])/2 + 14
        c.line([(sx, sy), (ex_, ey_), tgt], "#5b6770", 12)
        c.ell((tgt[0]-12, tgt[1]-12, tgt[0]+12, tgt[1]+12), fill="#f4b400" if gloves else "#cfd8e0", outline="#5b6770", w=3)

def caption(c, step, title, line2, prog):
    c.rect((0, 610, W, H), fill="#10243f")
    c.rect((0, 610, W*prog, 616), fill="#ffb02e")
    c.text((34, 632), step, 22, "#ffb02e", True); c.text((34+ (130 if step else 0), 628), title, 30, "white", True)
    c.text((34, 674), line2, 22, "#c9d6e6")

def checklist(c, x, y, items, t, title=None, w=470):
    c.rect((x, y, x+w, y+(len(items)*44)+(52 if title else 16)), fill=(255, 255, 255), outline="#c8d0da", w=2, r=12)
    yy = y+12
    if title: c.text((x+18, yy), title, 22, "#10243f", True); yy += 40
    for i, it in enumerate(items):
        k = seg(t, i/len(items)*0.85, i/len(items)*0.85+.12)
        c.rect((x+18, yy+4, x+44, yy+30), outline="#10243f", w=2, r=5)
        if k > .5:
            c.line([(x+23, yy+17), (x+30, yy+25), (x+41, yy+8)], "#1fa84f", 5)
            c.text((x+56, yy+2), it, 21, "#10243f")
        else: c.text((x+56, yy+2), it, 21, "#9aa7b5")
        yy += 44

# ---------------------------------------------------------------- scenes
def s_title(c, t, tm):
    bg(c, 560, tm=tm)
    panel(c, 760, 360, 330, 200, tilt=60, glow=.5+.5*math.sin(tm*3))
    c.line([(850, 560), (850, 480)], "#555", 8); c.line([(1000, 560), (1000, 480)], "#555", 8)
    wave = (880 - 880 + 235 + 28*math.sin(tm*8), 380)
    robot(c, 330, 560, None, (300+90, 395+25*math.sin(tm*8)), tm)
    k = seg(t, .05, .4)
    c.text((60, 110 - (1-k)*30), "How to Use", 44, "#10243f", True)
    c.text((60, 165 - (1-k)*30), "Solar Panels", 70, "#e07b00", True)
    c.text((64, 262), "Install  ·  Wire  ·  Operate  ·  Maintain", 28, "#10243f")
    c.text((64, 305), "A hands-on walkthrough by the BL Agent", 22, "#35506f")
    return ("", "Solar Panel Training", "Presented by the BL Agent  -  safety first, always", 0)

def s_safety(c, t, tm):
    bg(c, 560, sun=False, tm=tm)
    helmet, glasses, gloves = seg(t, .12, .3), seg(t, .3, .45), seg(t, .45, .6)
    robot(c, 300, 560, (360, 410) if 0 < gloves < 1 else None, None, tm,
          helmet=helmet > .5, gloves=gloves > .5, glasses=glasses > .5)
    for i, (n, k) in enumerate((("Hard hat", helmet), ("Safety glasses", glasses), ("Insulated gloves", gloves))):
        a = ease(k)
        if 0 < a < 1:
            c.text((470 + 0, 480 - 120*a + i*0), n, 22, "#e07b00", True)
    checklist(c, 690, 90, ["Panels covered with opaque sheet", "DC isolator / breaker OFF", "Dry hands, no metal jewelry", "Ladder secured, never work alone",
                           "Know your local electrical code"], seg(t, .5, 1), "Before you touch anything")
    return ("STEP 1", "Safety first", "Solar panels make voltage whenever light hits them - even when 'switched off'.", .0)

def s_site(c, t, tm):
    bg(c, 520, tm=tm)
    # house
    c.poly([(230, 300), (470, 170), (710, 300)], "#8b3a2e"); c.rect((260, 300, 680, 520), fill="#efe3cf", outline="#8b7a60", w=3)
    c.rect((310, 380, 380, 520), fill="#6b4a2f"); c.rect((520, 350, 620, 440), fill="#9fd3f0", outline="#8b7a60", w=3)
    # panel on roof
    panel(c, 395, 190, 150, 70, tilt=24, glow=.6)
    # tree shade
    c.rect((820, 360, 850, 520), fill="#6b4a2f"); c.ell((760, 250, 910, 400), fill="#2f6b34")
    k = seg(t, .55, .8)
    if k > 0: c.text((835, 220), "Shade = lost power", 22, "#c62828", True, "mm"); c.line([(775, 240), (905, 270)], "#c62828", 5) if k > .5 else None
    # sun-path arc
    c.line([(60 + i*20, 180 - 130*math.sin(i/20*math.pi)) for i in range(21)], "#ffc83a", 3)
    # angle
    c.line([(960, 500), (1180, 500)], "#444", 4); c.line([(960, 500), (1150, 410)], "#17356b", 8)
    a = seg(t, .3, .6)
    c.text((1080, 470), f"tilt ≈ {int(20+10*a)}°+", 22, "#10243f", True) if a > 0 else None
    robot(c, 215, 560, (350, 320) if t > .5 else None, None, tm, helmet=True, gloves=True, glasses=True)
    checklist(c, 720, 40, ["Face the sun: South (N. hemisphere)", "Tilt ≈ your latitude as a start", "No shade 9am - 3pm", "Roof / ground strong enough"],
              seg(t, .1, .8), "Choose the spot", 520) if False else None
    c.rect((700, 40, 1060, 190), fill="white", outline="#c8d0da", w=2, r=12)
    for i, ln in enumerate(["Face the sun (south in N. hemisphere,", "north in S. hemisphere)", "Tilt ≈ your latitude as a start", "No shade between 9am and 3pm"]):
        if seg(t, .1+i*.15, .25+i*.15) > .4: c.text((718, 54 + i*32), ln, 19, "#10243f")
    return ("STEP 2", "Choose the site", "Sunlight + direction + tilt decide how much energy you get.", 0)

def s_mount(c, t, tm):
    bg(c, 520, tm=tm)
    c.poly([(150, 420), (640, 190), (1130, 420)], "#8b3a2e"); c.rect((200, 420, 1080, 520), fill="#efe3cf", outline="#8b7a60", w=3)
    # rails
    c.line([(330, 340), (330, 280)], "#9aa7b5", 8)  # decorative
    c.rect((470, 275, 810, 285), fill="#c8d0da"); c.rect((470, 335, 810, 345), fill="#c8d0da")
    k = seg(t, .1, .55)
    px = lerp(120, 480, k); py = lerp(430, 260, k)
    panel(c, px, py, 320, 90, tilt=28, glow=.5)
    hand = (px+30, py+55) if t < .55 else (500 + 40*seg(t, .6, .75), 330)
    robot(c, lerp(90, 120, k) if t < .55 else 120, 560, (hand[0], hand[1]) if t < .85 else (470, 340), (px+10, py+90) if t < .55 else None, tm, helmet=True, gloves=True, glasses=True)
    # clamps
    for i, (cx, cy) in enumerate(((505, 340), (780, 340), (505, 280), (780, 280))):
        kk = seg(t, .6+i*.07, .68+i*.07)
        if kk > 0: c.ell((cx-8, cy-8, cx+8, cy+8), fill="#ffb02e", outline="#333", w=2)
    c.rect((820, 100, 1230, 205), fill="white", outline="#c8d0da", w=2, r=12)
    for i, ln in enumerate(["Fix rails to rafters / ground frame", "Clamp panel to rails, torque to spec", "Leave gaps for airflow"]):
        if seg(t, .15+i*.2, .3+i*.2) > .4: c.text((838, 114+i*30), ln, 19, "#10243f")
    return ("STEP 3", "Mount the panel", "Secure the frame first, then clamp the panel. Keep it covered while you work.", 0)

def wire_path(c, pts, prog, color, w=7):
    total = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1)); run = total*prog; out = [pts[0]]
    for i in range(len(pts)-1):
        d = math.dist(pts[i], pts[i+1])
        if run >= d: out.append(pts[i+1]); run -= d
        else: out.append(lerp2(pts[i], pts[i+1], run/d)); break
    c.line(out, color, w); return out[-1]

def s_wire(c, t, tm):
    c.rect((0, 0, W, H), fill="#eaf1f8")
    nodes = {"pv": (110, 200, 290, 320, "Solar\npanels"), "cc": (470, 200, 650, 320, "Charge\ncontroller"),
             "bat": (470, 410, 650, 520, "Battery"), "inv": (850, 200, 1030, 320, "Inverter"), "load": (1060, 380, 1230, 480, "Loads")}
    def box(key, col="#10243f", lit=True):
        x1, y1, x2, y2, name = nodes[key]
        c.rect((x1, y1, x2, y2), fill="white" if lit else "#dde5ee", outline=col, w=4, r=14)
        for i, ln in enumerate(name.split("\n")): c.text(((x1+x2)/2, (y1+y2)/2 + (i-(len(name.split('\n'))-1)/2)*30), ln, 24, col, True, "mm")
    # steps: battery->controller (0.05-.3), pv->controller (.35-.6), controller->inverter (.62-.78), inverter->load (.78-.9)
    p1 = seg(t, .05, .28); p2 = seg(t, .35, .58); p3 = seg(t, .62, .76); p4 = seg(t, .76, .88)
    for k in nodes: box(k)
    hands = None
    if p1 > 0: e = wire_path(c, [(560, 410), (560, 320)], p1, "#c62828"); c.text((575, 345), "+ / −", 18, "#c62828", True); hands = e
    if p2 > 0: e = wire_path(c, [(290, 260), (470, 260)], p2, "#222"); hands = e if p2 < 1 else hands
    if p3 > 0: e = wire_path(c, [(650, 260), (850, 260)], p3, "#222"); hands = e if p3 < 1 else hands
    if p4 > 0: e = wire_path(c, [(1030, 260), (1145, 260), (1145, 380)], p4, "#222"); hands = e if p4 < 1 else hands
    # fuse markers
    if p1 > .9: c.rect((545, 350, 575, 375), fill="#ffb02e", outline="#333", w=2); c.text((590, 392), "fuse", 17, "#333")
    if p2 > .9: c.rect((350, 245, 380, 275), fill="#ffb02e", outline="#333", w=2); c.text((338, 285), "MC4", 17, "#333")
    # agent small at bottom-left, reaching to current wire end
    robot(c, 130, 600 if False else 590, hands, None, tm, helmet=True, gloves=True, glasses=True) if False else None
    hx = hands if hands else (260, 470)
    robot(c, 110, 585, (min(hx[0], 300) if hx else 200, max(hx[1], 380)), None, tm, helmet=True, gloves=True, glasses=True)
    order = [("1", "Battery  →  controller first", t > .05), ("2", "Then panels  →  controller (covered)", t > .35), ("3", "Then inverter and loads", t > .62)]
    for i, (n, ln, on) in enumerate(order):
        y = 380 + i*58 if False else 50 + i*52
        c.ell((330, y, 372, y+42), fill="#ffb02e" if on else "#c8d0da"); c.text((351, y+21), n, 24, "#10243f", True, "mm")
        c.text((386, y+7), ln, 22, "#10243f" if on else "#9aa7b5", on)
    c.text((700, 400), "Red = positive   Black = negative", 20, "#444") if False else None
    c.text((670, 440), "Match polarity. Use correct wire size", 20, "#444"); c.text((670, 470), "and a fuse / breaker on every source.", 20, "#444")
    return ("STEP 4", "Wire it safely", "Battery first, panels second. To shut down, reverse the order.", 0)

def s_operate(c, t, tm):
    bg(c, 520, tm=tm)
    panel(c, 720, 260, 300, 160, tilt=50, glow=.5+.5*math.sin(tm*4))
    c.line([(790, 420), (790, 520)], "#555", 8); c.line([(950, 420), (950, 520)], "#555", 8)
    # controller box on post
    c.rect((470, 300, 590, 400), fill="#2b3a4d", outline="#111", w=3, r=8); c.rect((488, 316, 572, 350), fill="#9dffb0" if t > .45 else "#334", r=4)
    c.text((530, 333), "14.2V" if t > .45 else "OFF", 18, "#0a4d1e" if t > .45 else "#778", True, "mm")
    c.text((530, 372), "CHARGING" if t > .45 else "", 12, "#9dffb0", True, "mm")
    # flow dots panel->controller
    if t > .45:
        for i in range(8):
            u = ((tm*0.9) + i/8) % 1; p = lerp2((720, 340), (590, 350), u); c.ell((p[0]-5, p[1]-5, p[0]+5, p[1]+5), fill="#ffd34d")
        for i in range(8):
            u = ((tm*0.9) + i/8) % 1; p = lerp2((470, 350), (330, 460), u); c.ell((p[0]-5, p[1]-5, p[0]+5, p[1]+5), fill="#ffd34d")
        c.line([(470, 350), (330, 460)], "#555", 3)
        c.rect((230, 440, 340, 520), fill="#d9e2ec", outline="#334", w=3, r=8); c.text((285, 480), "Battery", 17, "#10243f", True, "mm")
    sw = seg(t, .2, .4)
    robot(c, 390, 560, (480, 345) if t < .5 else (500, 330 + 6*math.sin(tm*5)), None, tm, helmet=True, gloves=True, glasses=True, mood="ok")
    c.rect((780, 460, 1240, 590), fill="white", outline="#c8d0da", w=2, r=12) if False else None
    c.rect((60, 60, 480, 190), fill="white", outline="#c8d0da", w=2, r=12)
    for i, ln in enumerate(["1  Remove the cover, close the breaker", "2  Check controller shows 'charging'", "3  Voltage within expected range", "4  Switch on inverter, then loads"]):
        if seg(t, .1+i*.2, .25+i*.2) > .4: c.text((78, 72+i*28), ln, 18, "#10243f")
    return ("STEP 5", "Switch on and operate", "Watch the controller display: charging current and battery voltage.", 0)

def s_maint(c, t, tm):
    bg(c, 520, tm=tm)
    clean = seg(t, .25, .65)
    panel(c, 640, 250, 420, 200, tilt=70, clean=clean if False else (1 if clean > .5 else 0))
    # dust overlay fades
    for i in range(14):
        a = (i*53 % 100)/100; xx = 650 + a*420 + (1-.5)*0; yy = 270 + ((i*37) % 100)/100*160
        if clean < .95 and a > clean: c.ell((xx-10, yy-6, xx+10, yy+6), fill="#b49a76")
    c.line([(740, 450), (740, 520)], "#555", 8); c.line([(980, 450), (980, 520)], "#555", 8)
    sx = lerp(660, 1040, (0.5+0.5*math.sin(tm*5))) ; sy = 260 + 160*clean*0 + 120*clean
    hand = (sx - 40, sy + 20) if clean < 1 else (700, 300)
    robot(c, 480, 560, hand if 0.2 < t < .75 else None, None, tm, gloves=True, glasses=True)
    if t > .65:
        for i in range(5):
            a = tm*2 + i; c.text((700 + i*70, 260 + 20*math.sin(a)), "✦", 26, "#fff3b0", False, "mm")
    checklist(c, 40, 40, ["Clean gently with water and a soft cloth", "Do it at dawn or dusk (cool glass)", "Check cables, connectors, clamps",
                          "Look for shade, cracks, hot spots", "Log the output every month"], seg(t, .2, 1), "Monthly routine", 540)
    return ("STEP 6", "Maintain it", "Never use a pressure washer or abrasive pads. Never clean a cracked panel.", 0)

def s_recap(c, t, tm):
    c.rect((0, 0, W, H), fill="#10243f")
    c.text((W/2, 80), "Remember", 52, "#ffb02e", True, "mm")
    items = ["Safety first: cover panels, isolate, wear PPE", "Best site: facing the sun, tilted, no shade", "Mount rigidly, wire battery before panels",
             "Switch on, check the controller, record readings", "Clean monthly, inspect often, call a pro for grid-tie"]
    for i, it in enumerate(items):
        k = seg(t, .05+i*.14, .2+i*.14)
        if k > .1:
            c.ell((140, 160+i*76, 184, 204+i*76), fill="#ffb02e"); c.text((162, 182+i*76), str(i+1), 26, "#10243f", True, "mm")
            c.text((210, 168+i*76), it, 30, "white")
    return ("", "You're ready to go solar!", "Local codes apply. For grid-connected systems hire a licensed electrician.", 0)

SCENES = [(s_title, 4), (s_safety, 8), (s_site, 7), (s_mount, 8), (s_wire, 10), (s_operate, 8), (s_maint, 8), (s_recap, 6)]
TOTAL = sum(d for _, d in SCENES)

def main(out):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    gt = 0.0; frames = int(TOTAL*FPS)
    for f in range(frames):
        gt = f/FPS; acc = 0
        for fn, dur in SCENES:
            if gt < acc+dur: t = (gt-acc)/dur; break
            acc += dur
        c = Cv(); step, title, sub, _ = fn(c, t, gt)
        if fn is not s_wire and fn is not s_recap and fn is not s_maint or True:
            caption(c, step, title, sub, gt/TOTAL)
        fade = min(1, t*8, (1-t)*8) if False else 1
        ff.stdin.write(c.out().tobytes())
        if f % 100 == 0: print(f, "/", frames, file=sys.stderr)
    ff.stdin.close(); ff.wait()

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "solar_training.mp4")
