"""The Groovy Coop: synthwave score + card-flip foley, all made in code.
Run: $LIB/.venv/bin/python mix.py  (from this folder; LIB on sys.path for sfx.py) -> mix.wav (48 kHz stereo)
120 BPM, A minor: Am | F | C | G, one chord per bar (2 s). Drums drop at 4.0, break at 23-24, final chord at 28."""
import json, os, sys
import numpy as np
LIB = os.environ.get('LIB', os.path.expanduser('~/lemo-opuscar'))
sys.path.insert(0, os.path.join(LIB, 'core', 'audio'))
import sfx
from sfx import SR, t_, env_exp, lp, hp, bp, noise, norm
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 30.0
N = int(DUR * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(3)
BEAT = 0.5

def put(sig, at, gain=1.0, pan=0.0):
    i = int(round(at * SR));
    if i >= N: return
    sig = sig[:N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2) * 1.414
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2) * 1.414

mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
def saw(f, d, det=0.0):
    tt = t_(d); ph = (f * (1 + det)) * tt + rng.random()
    return 2 * (ph % 1) - 1
def square(f, d, duty=.5):
    tt = t_(d); return np.where(((f * tt) % 1) < duty, 1.0, -1.0)
def adsr(d, a=.005, dec=.1, s=.6, r=.05):
    n = int(round(d * SR)); e = np.full(n, s)
    na, nd, nr = int(a * SR), int(dec * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) if na else e[:na]
    e[na:na + nd] = np.linspace(1, s, len(e[na:na + nd]))
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

# chord tones (MIDI): root for bass, triad for pad/arp
CHORDS = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]   # Am F C G
def chord_at(bar): return CHORDS[bar % 4]

# ---------- kick envelope for sidechain ----------
kick_times = [b * BEAT for b in range(8, 57) if not (23.5 <= b * BEAT < 24.0)]   # 4.0 .. 28.0
duck = np.ones(N)
for kt in kick_times:
    i = int(kt * SR); n = int(.28 * SR); seg = 1 - .55 * np.exp(-np.arange(n) / SR / .09)
    duck[i:i + n] = np.minimum(duck[i:i + n], seg[:max(0, min(n, N - i))])

# ---------- pad ----------
pad = np.zeros(N)
for bar in range(15):
    t0 = bar * 2.0; d = 2.0 if bar < 14 else 2.0
    _, tri = chord_at(bar)
    if bar == 14: tri = [57, 60, 64, 69]; d = 2.0            # final Am, ringing to the end
    s = sum(saw(mtof(m), d + .3, det) for m in tri for det in (-.006, 0, .007)) / (3 * len(tri))
    e = adsr(d + .3, a=.25, dec=.4, s=.8, r=.35) if bar < 14 else env_exp(d + .3, 1.1) * np.minimum(1, t_(d + .3) / .01)
    i = int(t0 * SR); seg = s * e; pad[i:i + len(seg)] += seg[:N - i]
cut = np.interp(np.arange(N) / SR, [0, 4, 9.75, 10.5, 28, 30], [350, 2400, 2400, 3200, 3200, 1800])
# time-varying lowpass: process in blocks
out = np.zeros(N); B = 2400
from scipy.signal import butter, sosfilt, sosfilt_zi
zi = None
for k in range(0, N, B):
    sos = butter(2, cut[k], 'low', fs=SR, output='sos')
    if zi is None: zi = sosfilt_zi(sos) * 0
    out[k:k + B], zi = sosfilt(sos, pad[k:k + B], zi=zi)
pad = out * duck
put(pad, 0, .55, -.15); put(np.roll(pad, int(.012 * SR)), 0, .45, .3)   # a little width

# ---------- bass: octave eighths from the drop ----------
for i8 in range(8 * 2, 56 * 2):
    t0 = i8 * BEAT / 2
    if 23.5 <= t0 < 24.0: continue
    root, _ = chord_at(int(t0 // 2))
    m = root - 12 + (12 if i8 % 2 else 0)
    d = .22; s = lp(saw(mtof(m), d) + .5 * square(mtof(m), d, .3), 900) * adsr(d, .003, .12, .5, .04)
    put(s * duck[int(t0 * SR)], t0, .42)
# last low note under the final chord
put(lp(saw(mtof(33), 2.0), 500) * env_exp(2.0, .7), 28.0, .5)

# ---------- arpeggio: sixteenths, soft in the intro, full from the shelf ----------
pattern = [0, 1, 2, 1, 0, 2, 1, 2]
for i16 in range(0, 56 * 4):
    t0 = i16 * BEAT / 4
    if 23.5 <= t0 < 24.0: continue
    _, tri = chord_at(int(t0 // 2))
    m = tri[pattern[i16 % 8]] + 12
    d = .11
    s = lp(square(mtof(m), d, .25), 3800) * adsr(d, .002, .06, .3, .03)
    g = .05 + .07 * min(1, t0 / 4) + (.05 if t0 >= 10 else 0)
    put(s, t0, g, .45 if i16 % 2 else -.45)

# ---------- drums ----------
def kick():
    d = .4; tt = t_(d); f = 45 + 110 * np.exp(-tt / .03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env_exp(d, .16) + hp(noise(d), 3000) * env_exp(d, .002) * .3
def clap():
    d = .25; n = bp(noise(d), 900, 3200)
    e = sum(np.exp(-np.maximum(0, t_(d) - o) / .006) * (t_(d) >= o) for o in (0, .011, .022)) / 3 + env_exp(d, .07) * .7
    return n * e
def hat(open_=False):
    d = .2 if open_ else .05; return hp(noise(d), 7000) * env_exp(d, .06 if open_ else .012)
K, CL = norm(kick()), norm(clap())
for kt in kick_times: put(K, kt, .9)
for b in range(8, 56):
    t0 = b * BEAT
    if 23.5 <= t0 < 24.0: continue
    if b % 2 == 1: put(CL, t0, .45, .05)
    put(norm(hat(b % 4 == 3)), t0 + BEAT / 2, .18, .25)
    put(norm(hat()), t0 + BEAT / 4, .07, -.2); put(norm(hat()), t0 + 3 * BEAT / 4, .07, -.2)
# fills: a snare roll into the drop and into the end card
for a, b_ in ((3.0, 4.0), (23.0, 23.75)):
    n = int((b_ - a) / (BEAT / 4))
    for k in range(n): put(CL, a + k * BEAT / 4, .12 + .3 * k / n, 0)
# risers
def riser(d):
    tt = t_(d); n = noise(d); out = np.zeros_like(n); B2 = 1200
    for k in range(0, len(n), B2):
        f = 400 + 7000 * (k / len(n)) ** 2
        out[k:k + B2] = bp(n[k:k + B2], f * .7, min(f * 1.4, 20000))
    return out * (tt / d) ** 2
put(norm(riser(1.0)), 3.0, .25); put(norm(riser(1.0)), 23.0, .3)
# crash on the drop, the shelf, the vibe, the end card and the final chord
def crash(d=2.2): return hp(noise(d), 4000) * env_exp(d, .6)
for ct, g in ((4.0, .22), (10.0, .14), (18.0, .14), (24.0, .2), (28.0, .26)): put(norm(crash()), ct, g)

# ---------- foley from the picture's events ----------
ev = json.load(open(os.path.join(HERE, 'events.json')))['ev']
buckets = {}
for e in ev:
    k = round(e['t'] / (BEAT / 4)); buckets.setdefault(k, []).append(e)
for k, es in buckets.items():
    small = [e for e in es if e['type'] == 'flip']; t0 = es[0]['t']
    if small:
        g = .16 / np.sqrt(len(small))
        for j, e in enumerate(small[:6]):
            put(sfx.click(pitch=1.1 + rng.random() * .7, v=1), e['t'] + j * .004, g, rng.uniform(-.7, .7))
    for e in es:
        if e['type'] == 'mid': put(sfx.clack(1.0, 1), e['t'], .22, rng.uniform(-.3, .3))
        if e['type'] == 'big':
            put(sfx.thump(1, 85), e['t'], .35); put(sfx.pop(1), e['t'], .18, rng.uniform(-.2, .2))
for wt in (0.3, 9.7, 17.7, 23.7): put(norm(sfx.whoosh(.5)), wt, .16)

# ---------- master bus ----------
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
fade = np.ones(N); fn = int(.6 * SR); fade[-fn:] = np.linspace(1, 0, fn) ** 2
mix *= fade[:, None]
mix = mix / np.abs(mix).max() * .89
sf.write(os.path.join(HERE, 'mix.wav'), mix.astype(np.float32), SR, subtype='PCM_24')
print('mix.wav', mix.shape[0] / SR, 's')
