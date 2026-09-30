"""Code-synthesised sound effects + an event placer → an SFX track that lines up with on-screen actions.

usage (via bin/vh sfx):
  python tools/audio/sfx.py lib <out_dir>                         write the built-in library (48 kHz mono WAVs)
  python tools/audio/sfx.py place <events.json> <out.wav> [duration_s] [--lib DIR]   → 48 kHz STEREO track
events.json: [{"t": 3.20, "sfx": "click", "gain_db": -6}, {"t": 7.95, "sfx": "whoosh", "pan": -0.6, "dist": 3}, …]
  "sfx" is a library name or a path to your own WAV (recorded / licensed: log its source in NOTES.md; any bit depth,
  float or sample rate, decoded by ffmpeg; stereo files are folded to mono and treated as a point source).
  t is when the sound should LAND; each built-in sound's landmark (its perceptual hit) is aligned to t,
  so a whoosh peaks on the cut and a riser peaks on the drop.
  pan  (optional, −1 left … 0 centre … 1 right): equal-power, normalised so centre = the mono level on both channels
       (events without pan are sample-identical to the old mono placement); hard left/right = +3 dB on that side, total
       power constant. Derive it from the sounding object's on-screen x: pan = 2 · x / width − 1 (clamp; soften × 0.7).
  dist (optional, ≥ 1, distance in units of the reference distance; 1 = as recorded): level × 1/dist (−6 dB per
       doubling) plus a gentle 1st-order low-pass at 16 kHz / dist (≥ 1 kHz). Filter delay < 0.2 ms: landmarks hold.
Built-ins: click tick pop toggle typing whoosh swish_rev riser impact boom ding success error glitch shutter
All are original, deterministic (seeded) and license-free (MIT, part of this repo).
"""
import json, subprocess, sys, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, lfilter

SR = 48000
rng = np.random.default_rng(11)

def lp(x, f): b, a = butter(2, min(f, SR * .45) / (SR / 2), "low"); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), min(hi, SR * .45) / (SR / 2)], "band"); return lfilter(b, a, x)
def T(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))
def tone(freqs, t): return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(freqs, t.shape)) / SR)

def click():   t = T(.03); return hp(noise(.03), 2500) * np.exp(-t / .004) * .5 + np.sin(2*np.pi*1800*t) * np.exp(-t / .006) * .3
def tick():    t = T(.02); return np.sin(2*np.pi*3200*t) * np.exp(-t / .003) * .45
def pop():     t = T(.12); return tone(900 * np.exp(-t / .02) + 250, t) * np.exp(-t / .03) * .6
def toggle():  t = T(.09); return tone(np.where(t < .03, 1300, 1900), t) * np.exp(-t / .03) * .35
def typing():
    out = np.zeros(int(.6 * SR))
    for k in range(6):
        i = int((k * .09 + rng.uniform(0, .02)) * SR); x = click() * rng.uniform(.5, .9)
        out[i:i + len(x)] += x[: len(out) - i]
    return out
def whoosh(d=.7):
    t = T(d); k = np.sin(np.pi * t / d) ** 2
    x = np.zeros_like(t); n = noise(d)
    for i, fc in enumerate(np.linspace(400, 5000, 8)):   # sweep through bands for motion
        w = np.exp(-((t / d - i / 7) ** 2) / .03); x += bp(n, fc * .7, fc * 1.4) * w
    return x * k * .5
def swish_rev(): return whoosh(.5)[::-1] * .8
def riser(d=2.0):
    t = T(d); k = t / d
    return hp(noise(d), 500) * k ** 2.2 * .3 + tone(300 + 2400 * k ** 2, t) * k ** 3 * .15
def impact():
    t = T(1.6); return tone(40 + 90 * np.exp(-t / .05), t) * np.exp(-t / .6) * .9 + lp(noise(1.6), 1200) * np.exp(-t / .2) * .35
def boom():    t = T(2.4); return tone(34 + 40 * np.exp(-t / .1), t) * np.exp(-t / 1.0) * .95
def ding():
    t = T(1.2); x = sum(a * np.sin(2*np.pi*f*t) * np.exp(-t / d) for f, a, d in [(1318, .5, .5), (2637, .2, .25), (3951, .08, .12)])
    return x * np.minimum(1, t / .002) * .6
def success():
    out = np.zeros(int(1.3 * SR)); a, b = ding() * .7, ding() * .8
    b = np.interp(np.arange(len(b)) * 1.335, np.arange(len(b)), b)  # up a fourth
    out[:len(a)] += a[:len(out)]; i = int(.14 * SR); out[i:i + len(b)] += b[: len(out) - i]; return out
def error():   # two beeps: the second rises from the first one's tail in 2 ms, and the end fades in 5 ms (hard edges clicked)
    t = T(.35); u = np.where(t < .17, t, t - .17)
    e = np.maximum(np.minimum(1, u / .002) * np.exp(-u / .08), np.where(t >= .17, np.exp(-t / .08), 0)) * np.clip((.35 - t) / .005, 0, 1)
    return tone(np.where(t < .16, 330, 247), t) * e * .35
def glitch():
    t = T(.25); x = np.sign(np.sin(2*np.pi*rng.choice([80, 160, 640, 1280], len(t) // 600 + 1).repeat(600)[: len(t)] * t))
    return x * (rng.random(len(t) // 480 + 1).repeat(480)[: len(t)] > .35) * .25 * np.exp(-t / .2)
def shutter(): t = T(.18); x = hp(noise(.18), 1500) * (np.exp(-t / .01) + .6 * np.exp(-np.maximum(t - .07, 0) / .012) * (t > .07)); return x * .45

LIB = {"click": click, "tick": tick, "pop": pop, "toggle": toggle, "typing": typing, "whoosh": whoosh,
       "swish_rev": swish_rev, "riser": riser, "impact": impact, "boom": boom, "ding": ding, "success": success,
       "error": error, "glitch": glitch, "shutter": shutter}
# landmark = seconds from the start of the sound to its perceptual hit (what should coincide with the action)
LANDMARK = {"whoosh": .35, "swish_rev": .5, "riser": 2.0, "typing": 0.0}

def write(path, x):  # x: (n,) mono or (n, 2) stereo
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1 if x.ndim == 1 else x.shape[1]); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())

def spatial(x, pan=0.0, dist=1.0):
    """mono → (n, 2): distance (1/dist level + gentle air low-pass), then equal-power pan (centre = unity per side)"""
    d = max(1.0, float(dist))
    if d > 1: b, a = butter(1, max(1000.0, 16000.0 / d) / (SR / 2), "low"); x = lfilter(b, a, x) / d
    p = float(np.clip(pan, -1, 1)); th = (p + 1) * np.pi / 4
    gl, gr = (1.0, 1.0) if p == 0 else (np.sqrt(2) * np.cos(th), np.sqrt(2) * np.sin(th))
    return np.stack([x * gl, x * gr], 1)

def read(path):  # → mono float at SR via ffmpeg (as qa.py loads): any bit depth, float or EXTENSIBLE WAV, any rate
    ch = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "json", str(path)],
                                   capture_output=True, text=True, check=True).stdout)["streams"][0]["channels"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ar", str(SR), "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, int(ch)).mean(1, dtype=np.float64)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "lib":
        d = Path(sys.argv[2]); d.mkdir(parents=True, exist_ok=True)
        for name, fn in LIB.items(): write(d / f"{name}.wav", fn())
        print(f"{len(LIB)} SFX → {d}/ ({', '.join(LIB)})"); return
    if cmd == "place":
        events = json.load(open(sys.argv[2])); out = sys.argv[3]
        dur = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else max(e["t"] for e in events) + 3
        lib_dir = Path(sys.argv[sys.argv.index("--lib") + 1]) if "--lib" in sys.argv else None
        track = np.zeros((int(dur * SR), 2)); cache = {}
        for e in events:
            name = e["sfx"]
            if name not in cache:
                p = Path(name)
                cache[name] = read(p) if p.suffix == ".wav" and p.exists() else read(lib_dir / f"{name}.wav") if lib_dir and (lib_dir / f"{name}.wav").exists() else LIB[name]()
            x = spatial(cache[name] * 10 ** (e.get("gain_db", 0) / 20), e.get("pan", 0), e.get("dist", 1))
            i = int(round((e["t"] - LANDMARK.get(name, 0.0)) * SR))
            if i < 0: x, i = x[-i:], 0
            j = min(len(track), i + len(x)); track[i:j] += x[: j - i]
        clip = int((np.abs(track) > 1).sum()); write(out, track)
        print(f"{len(events)} events → {out} ({dur:.2f}s, stereo)" + (f"  ! {clip} samples clipped: lower gain_db" if clip else "")); return
    print(__doc__)

if __name__ == "__main__":
    main()
