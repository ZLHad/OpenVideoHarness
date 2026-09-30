"""Foley for the launch film: synthesize the few UI sounds the built-in library lacks into audio/sfx/ and write
audio/events.json. Event times come from the GSAP timelines (index.html and compositions/*.html, cited per event) and
are snapped to the first 30 fps frame that shows the action; pans come from the on-screen x of what makes the sound.
Seeded, no downloads, and the same bytes on every run.

usage (from the repo root):
  uv run -q --with numpy --with scipy python showcase/00-promo-launch-film/tools/foley.py
  bin/vh sfx lib showcase/00-promo-launch-film/audio/sfx
  bin/vh sfx place showcase/00-promo-launch-film/audio/events.json showcase/00-promo-launch-film/audio/sfx.wav 20 \
      --lib showcase/00-promo-launch-film/audio/sfx
Custom sounds start on their first hit (sfx.py aligns a non-library sound's first sample to t).
"""
import json, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt

SR, FPS = 48000, 30
FILM = Path(__file__).resolve().parent.parent
OUT = FILM / "audio" / "sfx"
frame = lambda t: max(0.0, float(np.ceil(t * FPS - 1e-9) / FPS))   # first frame that shows an action set at t
pan_of = lambda x, k=0.6: round(max(-1.0, min(1.0, (2 * x / 1920 - 1) * k)), 2)   # screen x → pan (softened; UI, not a room)
MIDI = lambda m: 440 * 2 ** ((m - 69) / 12)

def T(d): return np.arange(int(round(d * SR))) / SR
def noise(d, seed): return np.random.default_rng(seed).standard_normal(int(round(d * SR)))
def filt(x, kind, f, order=2):
    return sosfilt(butter(order, np.clip(np.array(f, float) / (SR / 2), 1e-4, 0.95), kind, output="sos"), x)
def put(dst, x, at):
    i = int(round(at * SR)); j = min(len(dst), i + len(x)); dst[i:j] += x[: j - i]; return dst
def write(name, x):
    x = np.asarray(x, float); n, m = int(0.001 * SR), int(0.006 * SR)
    x[:n] *= np.linspace(0, 1, n); x[-m:] *= np.linspace(1, 0, m)
    x = np.clip(x / max(1e-9, np.abs(x).max()) * 0.89, -1, 1)      # peak −1 dBFS; level = gain_db in events.json
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())

def thock(seed, f0):
    """a word landing: a soft, woody key 'thock' (a short body tone that drops a little, and a dull tap)"""
    t = T(0.12); body = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.25 * np.exp(-t / 0.01))) / SR) * np.exp(-t / 0.03)
    tap = filt(noise(0.12, seed), "band", [400, 2200]) * np.exp(-t / 0.006) * 0.6
    return (body + tap) * np.minimum(1, t / 0.0015)

def key(seed, amp):
    t = T(0.03); x = filt(noise(0.03, seed), "band", [1800, 6500]) * np.exp(-t / 0.004)
    return (x + 0.3 * np.sin(2 * np.pi * 1450 * t) * np.exp(-t / 0.006)) * np.minimum(1, t / 0.0012) * amp

def keys(times, seed):
    """auto-typing: one soft key click per time in `times` (s from the first); levels vary like real key presses"""
    x = np.zeros(int((times[-1] + 0.05) * SR)); r = np.random.default_rng(seed)
    for k, at in enumerate(times):
        put(x, key(seed * 100 + k, r.uniform(0.55, 1.0)), at)
    return x

def blip(f, d=0.12, dec=0.035, seed=0):
    """a soft mallet note: a sine with a little octave, plus a 3 ms mallet tick so it reads as a hit"""
    t = T(d); tone = (np.sin(2 * np.pi * f * t) + 0.15 * np.sin(4 * np.pi * f * t)) * np.exp(-t / dec)
    mallet = filt(noise(d, 500 + seed), "band", [2500, 9000]) * np.exp(-t / 0.003) * 0.35
    return (tone + mallet) * np.minimum(1, t / 0.0015)

def run(times, freqs, amp=1.0):
    """a run of soft blips at `times` (s from the first) with rising `freqs`; the first one a little stronger"""
    x = np.zeros(int((times[-1] + 0.15) * SR))
    for k, (at, f) in enumerate(zip(times, freqs)):
        put(x, blip(f, seed=k) * amp * (1.0 if k else 1.4), at)
    return x

E_PENTA = [64, 66, 68, 71, 73]                                   # E major pentatonic (the score is planned in E)
penta = lambda k, base=76: MIDI(base + 12 * (k // 5) + E_PENTA[k % 5] - 64)

def main():
    ev, sounds = [], {}
    def add(t, sfx, gain_db, pan=0.0, why=""):
        ev.append({"t": round(float(t), 3), "sfx": sfx, "gain_db": gain_db, **({"pan": pan} if pan else {}), "why": why})

    # ---- A · hook (compositions/s-hook.html): words whip up at spec[i][0]; centres measured with SF Pro at 136 px ----
    sounds.update(thock_hi=thock(1, 330), thock_mid=thock(2, 262), thock_lo=thock(3, 196))
    hook = [(0.25, "Your", 316, "thock_hi", -15), (0.40, "coding", 783, "thock_hi", -15), (0.52, "agent,", 1313, "thock_hi", -15),
            (0.85, "now", 312, "thock_mid", -13), (0.96, "a", 561, "thock_mid", -15), (1.04, "video", 849, "thock_mid", -11),
            (1.20, "studio.", 1338, "thock_lo", -9)]
    for t, w, x, s, g in hook:
        add(frame(t), s, g, pan_of(x, 0.5), f"A: hook word '{w}' lands (s-hook spec, t = {t})")
    add(2.5, "whoosh", -12, -0.2, "A→B: words peel LEFT 2.16–2.5, problem line enters mid-flight at 2.5 (whoosh peaks at the cut)")
    add(2.6, "boom", -18, 0, "B: 'One catch: it can't watch video.' lands (cascade 2.5–2.68): sub weight under the doubt (34 Hz, no attack: kept at −18 so the onset cue check skips it)")
    add(4.7, "whoosh", -12, -0.2, "B→C: cut-the-curve LEFT at 4.7")
    # ---- C · scaffold (index.html cursor + compositions/s-scaffold.html; C starts at 4.7) ----
    add(frame(4.7 + 0.52), "click", -9, pan_of(470), "C: cursor clicks the prompt, tap(5.22); focus ring same frame")
    T0, TD = 4.7 + 0.52 + 0.08, 28 * 0.028                          # 'bin/vh new promo launch-film' = 28 chars, 28 ms each
    sounds["keys_cmd"] = keys([0.028 * (k - 1) for k in range(1, 29, 2)], 11)   # a click every 2nd char (36 chars/s would buzz)
    add(T0 + 0.028, "keys_cmd", -9, pan_of(480), "C: the command types 5.33–6.08 (28 ms/char)")
    RET = T0 + TD + 0.1
    add(frame(RET), "click", -10, pan_of(480), "C: Return at RET = 6.184")
    add(frame(RET + 0.04), "tick", -12, pan_of(700), "C: '→ scaffolding' line at RET+0.04")
    add(frame(RET + 0.26 + 0.05), "toggle", -9, pan_of(620), "C: '✓ created projects/…' line at RET+0.31 (the key read)")
    tree = [frame(RET + 0.36 + 0.03 * i) for i in range(14)]        # 14 tree items, 30 ms apart, from RET+0.36
    sounds["tree_run"] = run([x - tree[0] for x in tree], [penta(k) for k in range(14)], 0.8)
    add(tree[0], "tree_run", -14, pan_of(1572), "C: the file tree fills, 14 items from RET+0.36 (a rising E-pentatonic run)")
    add(8.0, "whoosh", -12, -0.2, "C→D: cut at 8.0 (cursor carries)")
    # ---- D · route (compositions/s-route.html; D starts at 8.0) ----
    add(frame(8.0 + 0.5), "click", -9, pan_of(1692), "D: cursor presses ↵ at CLICK 0.5 (8.5)")
    add(frame(8.0 + 0.92), "tick", -10, 0, "D: scan box lands on row 02 (0.72–0.92, power3.inOut)")
    add(frame(8.0 + 0.96 + 0.26 * (1 - 0.1 ** 0.25)), "tick", -10, 0, "D: scan box lands on row 03 (0.96–1.22 power4.out, 90% of the way)")
    add(frame(8.0 + 1.55), "ding", -9, 0, "D: LOCK at 1.55 (9.55): row 03 → video-types/03-product-promo.md")
    add(11.3, "whoosh", -12, -0.2, "D→E: cut at 11.3")
    # ---- E · review (compositions/s-review.html; E starts at 11.3) ----
    add(11.3 + 0.6, "whoosh", -16, 0.1, "E: the playhead scans the sheet 0.34–0.84")
    add(frame(11.3 + 0.85), "error", -8, pan_of(144 + 4 * 272 + 136), "E: FLAG at 0.85 (12.15): tile 0:10.50 boxed, '#3 FAIL'")
    sounds["keys_note"] = keys([0.036 * k for k in range(10)], 12)
    add(frame(11.3 + 0.85), "keys_note", -10, pan_of(440), "E: the NOTES line types in with the flag (30 chars in 0.36 s)")
    add(frame(11.3 + 2.4), "click", -9, pan_of(940), "E: cursor clicks the flagged tile, tap(13.7)")
    add(11.3 + 2.4 + 0.07, "shutter", -10, 0, "E: rack-focus blur spike 13.7–13.84")
    add(frame(11.3 + 2.4 + 0.14), "success", -8, 0, "E: swap to the fixed frame, '✓ #3 PASS' at CLICK+0.14 (13.84)")
    add(15.0, "whoosh", -17, -0.2, "E→F: cut at 15.0 (softer: the count-up starts 0.1 s later)")
    # ---- F · proof (compositions/s-proof.html): column i at 0.06 i, count 0 → N over 0.7 s (power2.out) from +0.05 ----
    for i, (n, x, note) in enumerate([(8, 235, 76), (10, 685, 80), (3, 1051, 83), (20, 1501, 88)]):
        t0, shown, ticks = 15.0 + 0.06 * i + 0.05, 0, []
        for f in range(int(t0 * FPS), int((t0 + 0.75) * FPS) + 2):  # one tick per frame on which the number changes
            p = min(1.0, max(0.0, (f / FPS - t0) / 0.7)); v = int(np.floor(n * (1 - (1 - p) ** 2) + 0.5))
            if v != shown:
                ticks.append(f / FPS); shown = v
        sounds[f"count_{n}"] = run([x - ticks[0] for x in ticks], [MIDI(note)] * len(ticks), 0.7)
        add(ticks[0], f"count_{n}", -11 if i == 0 else -14, pan_of(x), f"F: '{n}' counts up, {len(ticks)} changes on screen (column {i + 1})")
    add(17.0, "swish_rev", -12, 0, "F→G: proof shrinks 1 → 0.8 over 16.8–17.0 (swish_rev ends at t)")
    add(17.0, "impact", -11, 0, "G: the wordmark ARRIVES (inverse zoom-through, 17.0–17.5)")
    tag = [(0.65, "Video", 387), (0.78, "as", 533), (0.86, "code,", 672), (0.98, "for", 818), (1.06, "coding", 985), (1.18, "agents.", 1226)]
    for t, w, x in tag:                                              # s-lockup spec; centres measured with SF Pro at 56 px
        add(frame(17.0 + t), "thock_hi" if w != "agents." else "thock_mid", -18, pan_of(x, 0.5), f"G: tagline word '{w}' rises (17.0 + {t})")

    for k, v in sounds.items():
        write(k, v)
    ev.sort(key=lambda e: e["t"])
    (FILM / "audio").mkdir(exist_ok=True)
    (FILM / "audio" / "events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(sounds)} custom sounds → {OUT.relative_to(FILM)}/, {len(ev)} events → audio/events.json")

if __name__ == "__main__":
    main()
