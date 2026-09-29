"""Rebuild the custom foley WAVs that some styles ship in styles/<slug>/sfx/ (all synthesized, seeded, no downloads).

usage (from the repo root): uv run -q --with numpy --with scipy python styles/_swatch/custom_sfx.py
Built-in sounds come from `bin/vh sfx lib`; a style adds its own WAV here only when no built-in fits, and names it
in its events.json by relative path (see styles/_swatch/README.md, "拟音"). Output is byte-identical on every run."""
import sys, wave, numpy as np
sys.path.insert(0, "tools/audio")
import music as M
SR = 48000
def write(path, x):
    x = np.clip(x / max(1e-9, np.abs(x).max()) * 0.89, -1, 1)          # peak −1 dBFS; level is set by gain_db in events.json
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())
def band(noise, lo, hi):                                              # FFT band-limit
    F = np.fft.rfft(noise); f = np.fft.rfftfreq(len(noise), 1 / SR); F[(f < lo) | (f > hi)] = 0; return np.fft.irfft(F, len(noise))
# ink-wash: one low guzheng pluck (A2, 110 Hz, the A 羽 tonic), 0.95 s so it ends with its own 50 ms fade before 5.0 s
write("styles/ink-wash/sfx/zheng_A2.wav", M.zheng(M.mtof(45), 0.95, 0.35, np.random.default_rng(7)))
# silhouette: paper footfalls (three variants so no two neighbouring steps are identical) and a scissors snip
for name, seed, lo, hi, dec in [("a", 1, 700, 2600, 0.016), ("b", 2, 900, 3200, 0.012), ("c", 3, 600, 2200, 0.020)]:
    n = int(0.09 * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    fib = band(r.standard_normal(n), lo, hi) * np.exp(-t / dec) * np.minimum(1, t / 0.002)
    thump = np.sin(2 * np.pi * (80 + 20 * seed) * t) * np.exp(-t / 0.025) * 0.35 * np.minimum(1, t / 0.003)
    write(f"styles/silhouette-papercut/sfx/paper_step_{name}.wav", fib + thump)
n = int(0.16 * SR); t = np.arange(n) / SR; r = np.random.default_rng(11); x = np.zeros(n)
for at, amp in [(0.0, 1.0), (0.055, 0.8)]:                            # two blade closes 55 ms apart (2.5–9 kHz) …
    i = int(at * SR); m = int(0.012 * SR); tt = np.arange(m) / SR
    x[i:i + m] += band(r.standard_normal(m), 2500, 9000) * np.exp(-tt / 0.003) * amp
i = int(0.06 * SR); m = n - i; tt = np.arange(m) / SR                 # … and the paper fibre tearing through
x[i:] += band(r.standard_normal(m), 1000, 4000) * np.exp(-tt / 0.03) * 0.35 * np.minimum(1, tt / 0.004)
write("styles/silhouette-papercut/sfx/snip.wav", x)

# brutalist-meme: the built-in glitch recipe (tools/audio/sfx.py: square wave hopping 80/160/640/1280 Hz every 12.5 ms,
# random 10 ms gates, exp decay) with 1 ms edges on the square and 2 ms ramps on every gate: no sample-level steps
n = int(0.25 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(23)
sq = np.sign(np.sin(2 * np.pi * rng.choice([80, 160, 640, 1280], n // 600 + 1).repeat(600)[:n] * t))
gate = (rng.random(n // 480 + 1) > .35).astype(float).repeat(480)[:n]; gate[:480] = 1.0          # always open on the hit
k = int(0.002 * SR); ramp = np.convolve(gate, np.ones(k) / k, mode="same")                      # 2 ms ramps on every gate edge
sq = np.convolve(sq, np.ones(48) / 48, mode="same")                                               # 1 ms edges: a buzz, not a click
x = sq * ramp * .25 * np.exp(-t / .2) * np.minimum(1, t / 0.0005)
x[-int(0.005 * SR):] *= np.linspace(1, 0, int(0.005 * SR))
with wave.open("styles/brutalist-meme/sfx/glitch_cut.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
print("ok")
