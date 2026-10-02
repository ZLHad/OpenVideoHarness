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
# random 10 ms gates, exp decay) with 1 ms edges on the square and 2 ms ramps on every gate: no sample-level steps.
# Two takes, alternated A B A B over the four cuts (bin/vh qa warns when one file plays three times in a row): b has
# its own gates and hops a fifth higher
def glitch_cut(path, seed, hops):
    n = int(0.25 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    sq = np.sign(np.sin(2 * np.pi * rng.choice(hops, n // 600 + 1).repeat(600)[:n] * t))
    gate = (rng.random(n // 480 + 1) > .35).astype(float).repeat(480)[:n]; gate[:480] = 1.0          # always open on the hit
    k = int(0.002 * SR); ramp = np.convolve(gate, np.ones(k) / k, mode="same")                      # 2 ms ramps on every gate edge
    sq = np.convolve(sq, np.ones(48) / 48, mode="same")                                               # 1 ms edges: a buzz, not a click
    x = sq * ramp * .25 * np.exp(-t / .2) * np.minimum(1, t / 0.0005)
    x[-int(0.005 * SR):] *= np.linspace(1, 0, int(0.005 * SR))
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
glitch_cut("styles/brutalist-meme/sfx/glitch_cut.wav", 23, [80, 160, 640, 1280])
glitch_cut("styles/brutalist-meme/sfx/glitch_cut_b.wav", 31, [120, 240, 960, 1920])
# tabletop-miniature: small, close, physical sounds for a desk at 2 cm scale
def modes(n, freqs, decays, amps, rng=None, jitter=0.0):
    """a struck object: decaying sines (wood, plastic, metal), each mode a little detuned by the seed"""
    t = np.arange(n) / SR; x = np.zeros(n)
    for f, d, a in zip(freqs, decays, amps):
        f = f * (1 + (rng.uniform(-jitter, jitter) if rng is not None else 0)); x += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    return x
def burst(n, lo, hi, dec, rng, rise=0.0005):
    t = np.arange(n) / SR; return band(rng.standard_normal(n), lo, hi) * np.exp(-t / dec) * np.minimum(1, t / rise)
def place(x, y, at):
    i = int(at * SR); x[i:i + len(y)] += y[:len(x) - i]; return x
def mixed(*parts):
    """the parts summed from 0, padded to the longest"""
    x = np.zeros(max(len(a) for a in parts))
    for a in parts: x[:len(a)] += a
    return x
def lamp_switch(path, seed, first, second, gap):
    """a desk-lamp push switch: the press (plastic) and, gap s later, the latch (a sharper click with a spring ring)"""
    r = np.random.default_rng(seed); n = int(0.2 * SR); x = np.zeros(n)
    place(x, burst(int(0.03 * SR), *first, 0.004, r) * 0.7 + modes(int(0.03 * SR), [first[0] * 0.9], [0.006], [0.3]), 0.0)
    place(x, mixed(burst(int(0.05 * SR), *second, 0.003, r), modes(int(0.08 * SR), [4100, 6300], [0.022, 0.012], [0.22, 0.1], r, 0.03),
                   modes(int(0.04 * SR), [180], [0.012], [0.35])), gap)
    write(path, x)
lamp_switch("styles/tabletop-miniature/sfx/lamp_on.wav", 41, (1200, 3200), (2500, 7000), 0.028)
lamp_switch("styles/tabletop-miniature/sfx/lamp_off.wav", 43, (1000, 2600), (2000, 5600), 0.034)
# the felt puck landing on a wooden block: a soft felt impulse into a block's few wood modes and a low body thump;
# three takes (a, b, c), the blocks step up in pitch as they step up in height
for name, seed, k in [("a", 51, 1.0), ("b", 52, 1.12), ("c", 53, 1.26)]:
    r = np.random.default_rng(seed); n = int(0.16 * SR)
    felt = burst(n, 200, 1600, 0.006, r, rise=0.0015) * 0.5
    wood = modes(n, [820 * k, 1930 * k, 3150 * k], [0.032, 0.018, 0.010], [0.5, 0.28, 0.12], r, 0.02)
    thump = modes(n, [150 * k], [0.03], [0.8]) * np.minimum(1, np.arange(n) / SR / 0.003)
    write(f"styles/tabletop-miniature/sfx/felt_land_{name}.wav", felt + wood + thump)
# the title card reaching the end of its threads: a dry jolt of card and a short fibre creak
r = np.random.default_rng(61); n = int(0.18 * SR); x = np.zeros(n)
place(x, mixed(burst(int(0.03 * SR), 900, 4200, 0.005, r), modes(int(0.05 * SR), [110], [0.02], [0.6])), 0.0)
cr = burst(int(0.09 * SR), 700, 2400, 0.04, r, rise=0.01) * (1 + 0.6 * np.sin(2 * np.pi * 95 * np.arange(int(0.09 * SR)) / SR))
place(x, cr * 0.35, 0.02)
write("styles/tabletop-miniature/sfx/thread_tug.wav", x)
# one morning bird outside the window: two rising chirps with a quick trill
def chirp(n, f0, f1, vib, rng):
    t = np.arange(n) / SR; f = f0 + (f1 - f0) * (t / t[-1]) ** 0.7 + 180 * np.sin(2 * np.pi * vib * t)
    ph = 2 * np.pi * np.cumsum(f) / SR; env = np.sin(np.pi * t / t[-1]) ** 1.5
    return (np.sin(ph) + 0.18 * np.sin(2 * ph)) * env
r = np.random.default_rng(71); x = np.zeros(int(0.42 * SR))
place(x, chirp(int(0.07 * SR), 3200, 4500, 38, r), 0.0)
place(x, chirp(int(0.06 * SR), 3600, 4900, 42, r) * 0.85, 0.11)
place(x, chirp(int(0.12 * SR), 4200, 3900, 55, r) * 0.6, 0.22)
write("styles/tabletop-miniature/sfx/bird.wav", x)
print("ok")
