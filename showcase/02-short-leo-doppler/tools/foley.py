"""Foley for the Doppler short: the satellite's beacon made audible, plus the few seams and reveals.

Knowledge-short density (playbook/04: only key reveals get a sound). The one idea is the film's own subject: a beacon
"ping" whose pitch follows the same normalised Doppler curve the chart draws (index.html PHYS: n = +1 approaching,
0 overhead, −1 receding), panned with the satellite across the sky dome. The shift is exaggerated to ±3 semitones, as the
picture exaggerates the wave density (and says so on screen); the pings sit on the planned score's beat (100 BPM, first
beat at 0.2 s, see the music brief). At the end the pings come back at one fixed pitch: compensated, no more "变调".

usage (from the repo root):
  uv run -q --with numpy --with scipy python showcase/02-short-leo-doppler/tools/foley.py
  bin/vh sfx lib showcase/02-short-leo-doppler/audio/sfx
  bin/vh sfx place showcase/02-short-leo-doppler/audio/events.json showcase/02-short-leo-doppler/audio/sfx.wav 24.8 \
      --lib showcase/02-short-leo-doppler/audio/sfx
Seeded, no downloads, the same bytes on every run. Custom sounds start on their first hit (sample 0 = t).
The beacon events carry "layer": "sonification", so a mix profile classes them as signal (bin/vh mix … profile=short).
"""
import json, math, wave
from pathlib import Path
import numpy as np

SR, FPS = 48000, 30
FILM = Path(__file__).resolve().parent.parent
OUT = FILM / "audio" / "sfx"
F0 = 880.0                                   # A5: the 5th of the planned D major score, above the voice's formants
BEAT, BEAT0 = 0.6, 0.2                       # planned score: 100 BPM, first beat at 0.2 s (bar lines on the 3.2 / 6.2 /
                                             # 14.6 / 17.6 cuts, see the music brief)
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
lerp = lambda a, b, x: a + (b - a) * x
seg = lambda t, a, b: clamp((t - a) / (b - a))
e_in_out = lambda x: 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2     # index.html eInOut (cubic)
frame = lambda t: max(0.0, math.ceil(t * FPS - 1e-9) / FPS)

# ---------------------------------------------------------------- index.html PHYS (same constants and formulas)
GM, RE, H = 3.986004418e14, 6371e3, 550e3
R = RE + H; V = math.sqrt(GM / R); MASK = math.radians(10)
LAM = math.acos(RE * math.cos(MASK) / R) - MASK
def vr(th): return V * RE * math.sin(th) / math.hypot(R * math.sin(th), R * math.cos(th) - RE)
VRMAX = abs(vr(LAM))
n_at_x = lambda x: -vr((2 * x - 1) * LAM) / VRMAX
def x_at_alpha(a_deg):
    a = math.radians(a_deg); side = -1 if a < math.pi / 2 else 1; e = a if side < 0 else math.pi - a
    return (side * (math.acos(RE * math.cos(e) / R) - e) / LAM + 1) / 2
alpha_at = lambda t: 10 + (t - 6.4) * (160 / 7.6)          # dome angle: 10° at 6.4 s → 170° at 14.0 s
T_ZERO = 6.4 + 80 / (160 / 7.6)                             # overhead, 10.2 s
sat_x = lambda t: 495 - 380 * math.cos(math.radians(clamp(alpha_at(t), -8, 186)))   # U.x − DOME_R·cos α
pan_of = lambda x: round(clamp((2 * x / 1080 - 1) * 0.75, -1, 1), 2)             # 1080 px wide frame

def hook_lambda(t):                                         # drawHook: wavelength squeezes, stretches, relaxes
    c, s, rl = e_in_out(seg(t, 0.85, 1.45)), e_in_out(seg(t, 1.6, 2.3)), e_in_out(seg(t, 2.45, 3.1))
    return lerp(lerp(lerp(96, 40, c), 170, s), 96, rl)

# ---------------------------------------------------------------- synthesis
def T(d): return np.arange(int(round(d * SR))) / SR
def put(dst, x, at):
    i = int(round(at * SR)); j = min(len(dst), i + len(x)); dst[i:j] += x[: j - i]; return dst
def write(name, x):
    x = np.asarray(x, float); n, m = int(0.001 * SR), int(0.006 * SR)
    x[:n] *= np.linspace(0, 1, n); x[-m:] *= np.linspace(1, 0, m)
    x = np.clip(x / max(1e-9, np.abs(x).max()) * 0.89, -1, 1)     # peak −1 dBFS; level = gain_db in events.json
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())

def ping(f, d=0.26):
    """one beacon ping: a clean tone with a little octave, a 2 ms attack and a 3 ms bright tick on the front (so the
    ping still reads as a hit under a syllable)"""
    t = T(d); x = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t) + 0.04 * np.sin(6 * np.pi * f * t)
    tick = np.random.default_rng(int(f)).standard_normal(len(t)) * np.exp(-t / 0.003) * 0.25
    tick = np.concatenate([[0.0], np.diff(tick)])      # a crude high-pass: the tick sits above the voice's formants
    return (x * np.exp(-t / 0.07) + tick) * np.minimum(1, t / 0.002)

def bell(f, d=1.2):
    t = T(d); return sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t / dec) for k, a, dec in [(1, 1, .45), (2.76, .3, .18), (5.4, .12, .07)]) * np.minimum(1, t / 0.002)

def hook_beacon():
    """S1: the beacon beeping on eighth notes (0.3 s) while the hook wave squeezes and stretches: its pitch follows the
    wave, f = F0·(96/λ)^0.5 (λ 96 → 40 → 170 → 96 px, so +7.6 then −4.9 semitones), fading in as the wave draws
    (0.25–0.95) and out before the push to S2 (2.9)."""
    x = np.zeros(int(3.2 * SR))
    for k in range(10):
        t = BEAT0 + BEAT / 2 * k
        lvl = (0.5 + 0.5 * clamp((t - 0.1) / 0.6)) * (1 - seg(t, 2.75, 3.0))
        if lvl > 0: put(x, ping(F0 * (96 / hook_lambda(t)) ** 0.5, 0.2) * lvl, t - BEAT0)
    return x

def main():
    sounds, ev = {}, []
    def add(t, sfx, gain_db, pan=0.0, why="", layer=None):
        ev.append({"t": round(float(t), 3), "sfx": sfx, "gain_db": gain_db, **({"pan": pan} if pan else {}),
                   **({"layer": layer} if layer else {}), "why": why})

    sounds["hook_beacon"] = hook_beacon()
    add(BEAT0, "hook_beacon", -17, 0, "S1: beacon beeps on eighths, pitch follows the hook wave (drawHook λ: squeeze 0.85–1.45, stretch 1.6–2.3)", "sonification")
    add(3.2, "whoosh", -18, -0.2, "S1→S2: push-slide LEFT, s1 out 2.9–3.2, s2 in from 3.2 (−18, not −14: at −14 its 1–4 kHz came within 5 dB of '频移', the end of the line under it)")
    add(6.2, "swish_rev", -9, 0, "S2→S3: zoom-through, s2 scales 2.4× over 5.9–6.2 (swish_rev ends at the cut)")
    # S3–S5: one ping per beat while the satellite crosses the dome (α 10° at 6.4 s → 170° at 14.0 s)
    beats = [BEAT0 + BEAT * k for k in range(40) if 6.7 < BEAT0 + BEAT * k < 14.0]
    for i, t in enumerate(beats):
        n = n_at_x(x_at_alpha(alpha_at(t)))
        name = f"ping_{i + 1:02d}"; sounds[name] = ping(F0 * 2 ** (3 * n / 12))
        add(t, name, -14, pan_of(sat_x(t)), f"S3–S5: beacon ping, α {alpha_at(t):.0f}°, Doppler n = {n:+.2f} → {3 * n:+.1f} semitones", "sonification")
    sounds["zero_bell"] = bell(F0)
    add(frame(T_ZERO), "zero_bell", -13, pan_of(495), "S4: overhead, the curve crosses zero: zero-pulse + ring at T_ZERO = 10.2", "sonification")
    add(15.15, "whoosh", -18, 0, "S5→S6a: the dome lifts away (eIn 14.6–15.2), the chart grows to the centre (eInOut 14.7–15.6): fastest ≈ 15.15")
    add(18.2, "whoosh", -16, 0, "S6b: the axis zooms out ×10 (ticks ±50 → ±500 kHz, 2 GHz curve squashed, 17.8–18.6)")
    add(frame(18.95), "impact", -12, 0, "S6b: the Ka 20 GHz curve draws at full height (18.95–19.75) — '再大 10 倍'")
    add(23.5, "swish_rev", -14, 0, "S7: both curves collapse into the flat line (22.7–23.5)")
    for i, t in enumerate([BEAT0 + BEAT * 39, BEAT0 + BEAT * 40]):  # 23.6, 24.2: '补偿后 ≈ 0' is on from 23.35
        name = f"ping_flat_{i + 1}"; sounds[name] = ping(F0)
        add(t, name, -14, 0, "S7: the beacon again, now at one fixed pitch: compensated, no more change", "sonification")

    for k, v in sounds.items():
        write(k, v)
    ev.sort(key=lambda e: e["t"])
    (FILM / "audio").mkdir(exist_ok=True)
    (FILM / "audio" / "events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(sounds)} custom sounds → {OUT.relative_to(FILM)}/, {len(ev)} events → audio/events.json")

if __name__ == "__main__":
    main()
