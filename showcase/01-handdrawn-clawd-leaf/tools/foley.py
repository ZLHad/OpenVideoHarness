"""Foley for "Clawd and the Leaf": synthesize the cartoon sounds the built-in library lacks into audio/sfx/ and write
audio/events.json. Every event time comes from src/scenes/leaf.js (the shot constants A, B, Cc and the pose/camera code,
cited per event); pans come from the sounding thing's screen x under that shot's camera. Seeded, no downloads, and the
same bytes on every run.

usage (from the repo root):
  uv run -q --with numpy --with scipy python showcase/01-handdrawn-clawd-leaf/tools/foley.py
  bin/vh sfx lib showcase/01-handdrawn-clawd-leaf/audio/sfx          # the 15 built-ins, next to the custom ones
  bin/vh sfx place showcase/01-handdrawn-clawd-leaf/audio/events.json showcase/01-handdrawn-clawd-leaf/audio/sfx.wav 12 \
      --lib showcase/01-handdrawn-clawd-leaf/audio/sfx
Custom sounds start at sample 0 on their hit (sfx.py aligns a non-library sound's first sample to t); sounds that build
up (gusts, the camera whirr) sit at gain_db ≤ −18 so bin/vh qa's cue check, which wants an onset at t, skips them.
"""
import json, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt

SR, FPS = 48000, 24
FILM = Path(__file__).resolve().parent.parent
OUT = FILM / "audio" / "sfx"

# ---------------------------------------------------------------- engine helpers (engines/ClaudeAnimationBase/src/core.js)
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
lerp = lambda a, b, x: a + (b - a) * x
ease = lambda x: clamp(x) ** 2 * (3 - 2 * clamp(x))
ease_out = lambda x: 1 - (1 - clamp(x)) ** 3
seg = lambda t, a, b: clamp((t - a) / (b - a))
frame = lambda t: max(0.0, np.ceil(t * FPS - 1e-9) / FPS)         # first frame that shows an action starting at t
pan_of = lambda x: round(clamp((2 * x / 1920 - 1) * 0.75, -1, 1), 2)   # screen x → pan, softened ×0.75 (playbook/04)

# ---------------------------------------------------------------- synthesis kit
def T(d): return np.arange(int(round(d * SR))) / SR
def noise(d, seed): return np.random.default_rng(seed).standard_normal(int(round(d * SR)))
def filt(x, kind, f, order=2):
    w = np.array(f, float) / (SR / 2)
    return sosfilt(butter(order, np.clip(w, 1e-4, 0.95), kind, output="sos"), x)
def glide(f, t):  # f: array of instantaneous frequencies → phase-continuous sine
    return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(f, t.shape)) / SR)
def ramp(x, a=0.002, b=0.008):  # no hard edges: short fade in and out (a click detector would flag a step)
    n, m = int(a * SR), int(b * SR)
    x = x.copy()
    if n: x[:n] *= np.linspace(0, 1, n)
    if m: x[-m:] *= np.linspace(1, 0, m)
    return x
def put(dst, x, at):
    i = int(round(at * SR)); j = min(len(dst), i + len(x)); dst[i:j] += x[: j - i]; return dst
def write(name, x):
    x = ramp(np.asarray(x, float))
    x = np.clip(x / max(1e-9, np.abs(x).max()) * 0.89, -1, 1)     # peak −1 dBFS; the level is gain_db in events.json
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())

def tick(seed, lo=2000, hi=7000, dec=0.004, ring=0.0, f=2400, d=0.03):
    """a small click with a 1.5 ms attack (a real mechanism, and no single-sample step)"""
    t = T(d); x = filt(noise(d, seed), "band", [lo, hi]) * np.exp(-t / dec)
    if ring: x += ring * np.sin(2 * np.pi * f * t) * np.exp(-t / (dec * 2.5))
    return x * np.minimum(1, t / 0.0015)

def iris_open(d):
    """the viewfinder iris: a latch releases (click at 0), the blades slide (bright hiss with a mechanical flutter) and
    lock with a second click at the end"""
    t = T(d + 0.06); n = filt(noise(d + 0.06, 3), "band", [1500, 6000])
    env = np.where(t < d, 0.25 + 0.75 * (t / d) ** 1.5, np.exp(-(t - d) / 0.01)) * (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 38 * t)))
    x = put(n * env * 0.35 * np.minimum(1, t / 0.01), tick(9, 2200, 7000, 0.004, 0.4, 2100) * 0.9, 0.0)
    return put(x, tick(4, 1800, 6500, 0.005, 0.5, 1650) * 1.2, d - 0.01)

def iris_hiss():
    """the iris blades closing at the very end: 0.14 s of hiss that ends where the thunk starts"""
    t = T(0.15); return filt(noise(0.15, 5), "band", [1200, 5000]) * np.clip(t / 0.14, 0, 1) ** 2 * (t < 0.145)

def iris_thunk():
    """the iris shut: a soft low thunk (the frame goes to ink), 40 ms so it ends before the film does"""
    tt = T(0.04); thunk = glide(140 * np.exp(-tt / 0.02) + 70, tt) * np.exp(-tt / 0.012) * np.minimum(1, tt / 0.002)
    return thunk + tick(6, 600, 2500, 0.004, d=0.04) * 0.5

def twig_creak():
    """the stem creaking while the leaf tugs at it (0.2 s, building)"""
    t = T(0.2); saw = ((t * 190 + 0.3 * np.sin(2 * np.pi * 7 * t)) % 1) * 2 - 1
    return filt(saw, "band", [300, 1400]) * (0.2 + 0.8 * np.abs(np.sin(2 * np.pi * 23 * t))) * (t / 0.2)

def twig_snap():
    """the stem snapping: two cracks 8 ms apart with a little woody ring"""
    return put(tick(7, 1500, 6000, 0.006, 0.8, 900, 0.08), 0.7 * tick(8, 2000, 7000, 0.003), 0.008)

def sparkle():
    """the excited take's spark: two quick bell pings a fifth apart (E6, B6: the score is in E)"""
    x = np.zeros(int(0.35 * SR))
    for at, f in [(0.0, 1318.5), (0.07, 1975.5)]:
        t = T(0.28); put(x, (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.03))
                        * np.exp(-t / 0.08) * np.minimum(1, t / 0.002), at)
    return x

def crank(d, seed):
    """the hand-cranked camera: a ratchet click every 1/8 turn plus the film-gate whirr, for d seconds.
    leaf.js turns the crank at 13 rad/s (crank = (lt − t0) · 13), so a click every (2π/8)/13 = 60.4 ms."""
    t = T(d); step = (2 * np.pi / 8) / 13
    x = filt(noise(d, seed), "band", [700, 2000]) * (0.5 + 0.5 * np.sin(2 * np.pi * t / step) ** 2) * 0.12
    for k, at in enumerate(np.arange(0.0, d - 0.02, step)):
        put(x, tick(seed * 100 + k, 2500, 8000, 0.003, 0.35, 3100) * (0.8 + 0.2 * (k % 2)), at)
    return x * np.minimum(1, t / 0.02)

def gust(seed, d=1.35, rise=0.28, hold=0.27):
    """a wind gust: noise through a low-pass that opens with the gust (leaf.js gustEnv: up in 0.23 s, down over ~0.75 s)
    plus a faint whistle; the level envelope has the same shape"""
    t = T(d); x = noise(d, seed)
    env = np.where(t < rise, (t / rise) ** 2, np.where(t < rise + hold, 1.0, np.exp(-(t - rise - hold) / 0.28)))
    y, out = 0.0, np.empty_like(x)
    fc = 250 + 2300 * env
    coef = 1 - np.exp(-2 * np.pi * fc / SR)
    for i in range(len(x)):                                  # one-pole low-pass with a moving cutoff
        y += coef[i] * (x[i] - y); out[i] = y
    whistle = filt(noise(d, seed + 1), "band", [900, 1100], 2) * 0.6
    y = (out * 2.2 + whistle) * env
    return np.tanh(2.5 * y / np.abs(y).max())            # soft-saturate the noise peaks: more body at the same peak level

def take_bwip():
    """a cartoon take: a lip 'pop' on the hit, then a slide-whistle zip up (300 → 1500 Hz) with a little wobble"""
    t = T(0.22); f = 300 * (5 ** np.clip(t / 0.12, 0, 1)) * (1 + 0.03 * np.sin(2 * np.pi * 28 * t))
    pop = glide(900 * np.exp(-t / 0.01) + 250, t) * np.exp(-t / 0.012) * 0.8 + filt(noise(0.22, 17), "band", [1200, 6000]) * np.exp(-t / 0.005) * 2.0
    return (pop + glide(f, t) + 0.3 * glide(2 * f, t)) * np.minimum(1, t / 0.002) * np.exp(-np.maximum(t - 0.12, 0) / 0.04)

def zip_off():
    """launching into the dash: the foot pushing off (a soft thump at 0), then a rising swish, loudest at +0.16 s (the
    cut at 4.0, where the launch is fastest: A's dx = 2.2·easeIn(go) ends there and B's dash starts at full speed)"""
    t = T(0.36); n = noise(0.36, 12)
    push = (glide(90 * np.exp(-t / 0.03) + 60, t) * np.exp(-t / 0.03) * 1.5
            + filt(noise(0.36, 18), "band", [900, 5000]) * np.exp(-t / 0.006) * 1.2) * np.minimum(1, t / 0.0015)   # thump + scuff
    x = sum(filt(n, "band", [fc * .7, fc * 1.4]) * np.exp(-((t - 0.04 - 0.04 * i) ** 2) / 0.003) for i, fc in enumerate([700, 1100, 1700, 2600, 3900]))
    x *= np.minimum(1, t / 0.16) ** 1.5 * np.exp(-np.maximum(t - 0.16, 0) / 0.05)
    return push + 0.6 * (x + 0.25 * glide(500 + 2500 * np.clip(t / 0.2, 0, 1) ** 2, t) * np.exp(-((t - 0.15) ** 2) / 0.003))

def step(seed, f0):
    """a soft cartoon footfall: a small low thud plus a short brush of grass"""
    t = T(0.09); thud = glide(f0 * np.exp(-t / 0.03) + f0 * 0.6, t) * np.exp(-t / 0.02)
    brush = filt(noise(0.09, seed), "band", [900, 4000]) * np.exp(-t / 0.008) * 0.7 + filt(noise(0.09, seed + 50), "band", [2500, 8000]) * np.exp(-t / 0.002) * 0.6
    return (thud + brush) * np.minimum(1, t / 0.0015)

def tiptoe(seed):
    t = T(0.05); return (np.sin(2 * np.pi * 2300 * t) * np.exp(-t / 0.008) * 0.6 + filt(noise(0.05, seed), "band", [3000, 7000]) * np.exp(-t / 0.004)) * np.minimum(1, t / 0.001)

def skid():
    """the skid stop: a scrape (band noise) and a squeak sliding down 1900 → 900 Hz, 0.45 s"""
    t = T(0.45); env = np.minimum(1, t / 0.02) * np.exp(-t / 0.18)
    scrape = filt(noise(0.45, 13), "band", [700, 3200]) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t)) * 0.8
    squeak = glide((1900 - 1000 * np.clip(t / 0.3, 0, 1)) * (1 + 0.02 * np.sin(2 * np.pi * 31 * t)), t) * 0.35
    return (scrape + squeak) * env

def leaf_pat(seed):
    """a leaf landing: a soft paper pat with a little body"""
    t = T(0.08); pat = filt(noise(0.08, seed), "band", [900, 4000]) * np.exp(-t / 0.012)
    return (pat + 0.3 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.02)) * np.minimum(1, t / 0.0015)

def stomp():
    """one angry stomp: a low thump, a slap of the foot, the camera rattling in the hand 40–90 ms later"""
    t = T(0.3); thump = glide(75 * np.exp(-t / 0.05) + 42, t) * np.exp(-t / 0.12)
    slap = filt(noise(0.3, 14), "band", [200, 1200]) * np.exp(-t / 0.03) * 0.8
    x = (thump + slap) * np.minimum(1, t / 0.002)
    for k, at in enumerate([0.045, 0.07, 0.095]):
        put(x, tick(140 + k, 2000, 6000, 0.003, 0.3, 2800) * 0.25, at)
    return x

def whirr(d):
    """inside the camera for the whole POV shot: the film gate chattering at 24 frames a second and a faint motor"""
    ph = (t := T(d)) * 24 % 1                            # each gate pulse opens over 2 ms (a hard step would click)
    x = filt(noise(d, 15), "band", [1000, 3500]) * np.exp(-ph / 0.12) * np.minimum(1, ph / 0.048) * 0.5
    x += 0.25 * np.sin(2 * np.pi * 110 * t) * (1 + 0.3 * np.sin(2 * np.pi * 24 * t)) + filt(noise(d, 16), "low", 400) * 0.3
    return x * np.clip(t / 0.25, 0, 1) * np.clip((d - t) / 0.2, 0, 1)

def hearts():
    """delight + hearts: three bell notes up the E major triad (E6 G#6 B6), 70 ms apart"""
    x = np.zeros(int(0.6 * SR))
    for k, f in enumerate([1318.5, 1661.2, 1975.5]):
        t = T(0.45); put(x, np.sin(2 * np.pi * f * t) * np.exp(-t / 0.12) * np.minimum(1, t / 0.002) * (0.8 + 0.1 * k), 0.07 * k)
    return x

# ---------------------------------------------------------------- cameras (leaf.js shotA / shotB) → screen x
A = dict(G=900, u=34, X=1190, tRel=1.15, tGust=2.55, tSurp=3.0, tTurn=3.5)                  # leaf.js const A
B = dict(G=900, u=30, PX=1340, tStop=.95, tSneak=1.35, tGust=2.0, tStomp=2.5, tSusp=3.1, tSpin=3.3, tPush=3.8)  # const B
C = dict(tIn=.8, tLand=1.7, tNotice=1.85, tJoy=2.4, tWave=2.7, tClose=3.15)                 # const Cc

def screen_a(x, lt):   # shotA: reveal pull-back, drift, whip; camBegin(cx, cy, z) → screen x = (x − cx)·z + 960
    reveal = ease(seg(lt, .55, 1.05)); whip = ease(seg(lt, 2.62, 3.1)) * (1 - ease(seg(lt, 3.3, 3.9)))
    cx = lerp(680, 905, reveal) + 12 * np.sin(lt * .7) + 70 * whip; z = lerp(2.1, 1.1, reveal) + .01 * lt
    return (x - cx) * z + 960

def x_b(lt):           # poseB: the dash (easeOut 300 → 830 by tStop), then the tiptoe (830 → 900, ease, 1.35–1.95)
    return lerp(300, 830, ease_out(seg(lt, 0, B["tStop"]))) if lt < B["tStop"] else lerp(830, 900, ease(seg(lt, B["tSneak"], 1.95)))

def screen_b(x, lt):   # shotB camera before the push (tPush): pans with the dash, then drifts
    cx = lerp(80, 1110, ease_out(seg(lt, 0, 1.2))) if lt < 1.2 else lerp(1110, 1080, seg(lt, 1.2, 3.8))
    return (x - cx) * (1.35 + .03 * lt) + 960

def solve(f, target, a, b):   # bisection for a monotone f on [a, b]
    for _ in range(60):
        m = (a + b) / 2; a, b = (m, b) if f(m) < target else (a, m)
    return (a + b) / 2

# ---------------------------------------------------------------- build
def main():
    sounds = {"iris_open_a": iris_open(0.29), "iris_open_c": iris_open(0.35), "iris_hiss": iris_hiss(), "iris_thunk": iris_thunk(),
              "twig_creak": twig_creak(), "twig_snap": twig_snap(), "sparkle": sparkle(), "crank_a": crank(1.10, 21), "crank_b": crank(0.40, 22),
              "gust_1": gust(31), "gust_2": gust(32, 1.5, 0.3, 0.35), "take_bwip": take_bwip(), "zip_off": zip_off(),
              "step_1": step(41, 120), "step_2": step(42, 105), "step_3": step(43, 135), "tiptoe": tiptoe(44),
              "skid": skid(), "leaf_pat": leaf_pat(45), "stomp": stomp(), "whirr": whirr(3.72), "hearts": hearts()}
    for k, v in sounds.items():
        write(k, v)

    ev = []
    def add(t, sfx, gain_db, pan=0.0, why="", role=None):   # role: the mix profile's class where the name hint is wrong
        ev.append({"t": round(float(t), 3), "sfx": sfx, "gain_db": gain_db, **({"pan": pan} if pan else {}),
                   **({"role": role} if role else {}), "why": why})

    clawd_a = lambda lt: pan_of(screen_a(A["X"] + 1.5 * A["u"], lt))            # the camera sits ~1.5u ahead of Clawd
    # ---- shot A (0–4.0) ----
    add(frame(0.0), "iris_open_a", -10, 0, "A: viewfinder iris opens on the leaf, 0–0.3 s; lock click at +0.28")
    add(0.9, "whoosh", -17, 0, "A: the viewfinder widens (easeIn 0.55–1.0) as the camera pulls back (0.55–1.05): fastest ≈ 0.9")
    add(0.95, "twig_creak", -20, pan_of(screen_a(656, 1.0)), "A: the leaf tugs at its stem, 0.95–1.1")
    add(frame(A["tRel"]), "twig_snap", -9, pan_of(screen_a(656, A["tRel"])), "A: the stem snaps, leaf lets go at tRel 1.15")
    add(frame(1.6), "sparkle", -14, clawd_a(1.6), "A: excited take + spark, emotions() key at 1.6")
    add(1.65, "crank_a", -10, clawd_a(2.2), "A: crank turns 1.65 → tGust+0.2 = 2.75 (13 rad/s, click per 1/8 turn)")
    # the gusts are the gag's action (they snatch the leaf), not a background: detail, though "gust" reads as ambience
    add(A["tGust"] - 0.22, "gust_1", -18, -0.55, "A: gust — streaks from tGust−0.2 = 2.35, gustEnv peaks 2.63–2.9 (left layer)", "detail")
    add(A["tGust"] - 0.10, "gust_2", -18, 0.55, "A: gust, right layer 0.12 s later: the wind crosses left → right", "detail")
    add(2.9, "whoosh", -14, 0.4, "A: leaf snatched on an arc over Clawd, 2.55–2.97 (k^1.8: fastest at the end; it leaves the frame ≈ 2.9)")
    add(frame(A["tSurp"]), "take_bwip", -8, clawd_a(3.0), "A: surprise take + '!' at tSurp 3.0")
    add(3.84, "zip_off", -10, 0.3, "A→B: crouch 3.66–3.84, launch 3.84 (cut on action at 4.0); the swish peaks at +0.16 = the cut")
    # ---- shot B (4.0–8.2), lt = t − 4 ----
    walk = lambda lt: (x_b(lt) - 300) / (2.6 * B["u"])                            # poseB: o.walk during the dash
    for k in range(1, int(walk(B["tStop"] - 1e-6)) + 1):                         # a foot lands at every whole walk value
        lt = solve(walk, k, 0, B["tStop"])
        add(4 + lt, f"step_{1 + (k - 1) % 3}", -9 if k == 1 else -11, pan_of(screen_b(x_b(lt), lt)), f"B: dash footfall {k} (walk = {k})")
    add(frame(4.6), "leaf_pat", -14, pan_of(screen_b(B["PX"] - 20, .6)), "B: leaf settles on the pumpkin at lt 0.6 (4.6)")
    add(4 + B["tStop"] - 0.09, "skid", -9, pan_of(screen_b(830, B["tStop"])), "B: skid stop — dust at tStop−0.05 = 4.90, squash from 4.95")
    tip = lambda lt: (x_b(lt) - 830) / (2.2 * B["u"])                             # poseB: o.walk during the tiptoe
    for lt in (B["tSneak"], solve(tip, 1, B["tSneak"], 1.95)):
        add(4 + lt, "tiptoe", -15, pan_of(screen_b(x_b(lt), lt)), "B: tiptoe footfall (walk = 0, 1)")
    add(4 + 1.75, "crank_b", -10, pan_of(screen_b(900 + 45, 1.9)), "B: crank 1.75 → tGust+0.15 (5.75–6.15)")
    add(4 + B["tGust"] - 0.22, "gust_1", -18, -0.55, "B: gust #2, left layer (gustEnv(lt, 2.0))", "detail")
    add(4 + B["tGust"] - 0.10, "gust_2", -18, 0.55, "B: gust #2, right layer", "detail")
    add(6.35, "whoosh", -11, 0.45, "B: leaf flips off the pumpkin at 6.0, loops, zips out the top by 6.5 (fastest as it leaves ≈ 6.35)")
    add(4 + B["tStomp"] + 0.26 + 0.02, "stomp", -8, pan_of(screen_b(900, 2.76)), "B: angry stomp — jump(lt, 2.56, 2.76) lands 6.76 (visible frame 163 = 6.79)")
    add(frame(4 + B["tSusp"]), "toggle", -13, pan_of(screen_b(900, 3.1)), "B: suspicious '?' at tSusp 3.1 (7.1)")
    add(4 + B["tSpin"] + 0.1, "whoosh", -16, pan_of(screen_b(960, 3.4)), "B: camera turned round 7.3–7.5 (drawn key views)")
    add(frame(4 + B["tSpin"] + 0.2), "click", -15, pan_of(screen_b(960, 3.5)), "B: the camera settles, lens toward Clawd (7.5)")
    add(8.2, "swish_rev", -10, 0, "B→C: push into the lens 7.7–8.2 (swish_rev ends at t)")
    # ---- shot C (8.2–12.0), lt = t − 8.2 ----
    add(8.2 + 0.02, "iris_open_c", -11, 0, "C: viewfinder opens out of the dark lens, 8.22–8.58")
    add(8.2 + 0.02, "whirr", -19, 0, "C: inside the running camera until the iris shuts (11.94)")
    add(frame(8.2 + C["tLand"]), "leaf_pat", -9, pan_of(960 + 1.4 * 84), "C: leaf lands on Clawd's head at tLand 1.7 (9.9): the story's landing, so it reads over the harp")
    add(frame(8.2 + C["tNotice"]), "take_bwip", -8, 0, "C: notices — surprised take + '!' at tNotice 1.85 (10.05)")
    add(frame(8.2 + C["tJoy"]), "hearts", -12, 0.1, "C: delight + hearts at tJoy 2.4 (10.6)")
    add(8.2 + C["tClose"] + 0.38, "swish_rev", -16, 0, "C: viewfinder shrinks onto the face 11.35–11.73")
    add(11.955 - 0.14, "iris_hiss", -18, 0, "C: the iris blades close 11.8–11.94 (easeIn)")
    add(11.955, "iris_thunk", -9, 0, "C: iris shuts to ink between frames 286 and 287 (11.96)")
    ev.sort(key=lambda e: e["t"])
    (FILM / "audio").mkdir(exist_ok=True)
    (FILM / "audio" / "events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(sounds)} custom sounds → {OUT.relative_to(FILM)}/, {len(ev)} events → audio/events.json")

if __name__ == "__main__":
    main()
