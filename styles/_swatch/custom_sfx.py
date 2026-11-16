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
# whiteboard: a dry-erase marker. Each stroke sound is as long as its stroke in styles/whiteboard/swatch.js (XS 0.07, S 0.14,
# M 0.34, L 0.62 s) and follows the same minimum-jerk speed curve the picture uses (16u²(1-u)²): the nib's tap on the
# board, then friction noise and a stick-slip squeak that rise and fall with the hand's speed
def marker(dur, seed, squeak=0.55, f0=1150):
    n = int((dur + 0.02) * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    u = np.clip(t / dur, 0, 1); v = 16 * u * u * (1 - u) ** 2; e = 0.18 + 0.82 * v
    e *= np.where(t > dur, np.exp(-(t - dur) / 0.004), 1.0)
    fric = band(r.standard_normal(n), 2400, 7500) * e ** 0.9 * 0.45
    gate = np.repeat(r.random(n // 960 + 2), 960)[:n]; gate = np.convolve((gate > 0.35).astype(float), np.ones(240) / 240, "same")
    f = f0 * (0.75 + 0.5 * v) * (1 + 0.02 * np.sin(2 * np.pi * 31 * t)); ph = 2 * np.pi * np.cumsum(f) / SR
    sq = sum(np.sin(k * ph) / k for k in range(1, 7)) * gate * v * squeak * 0.4
    tap = mixed(burst(int(0.02 * SR), 1500, 6000, 0.0025, r), modes(int(0.03 * SR), [190], [0.008], [0.5]))
    x = fric + sq; x[:len(tap)] += tap * 1.2
    x[-int(0.005 * SR):] *= np.linspace(1, 0, int(0.005 * SR))
    return x
def marker_run(path, n_glyph, period, seed, f0):
    """handwriting: one short stroke group per glyph, a tap at each glyph's start"""
    x = np.zeros(int((n_glyph * period + 0.03) * SR))
    for i in range(n_glyph):
        place(x, marker(period * 0.86, seed + i, 0.4, f0 * (1 + 0.06 * ((i * 7) % 5 - 2))), i * period)
    write(path, x)
WB = "styles/whiteboard/sfx"
write(f"{WB}/marker_L.wav", marker(0.62, 101, 0.6, 1050))
write(f"{WB}/marker_M_a.wav", marker(0.34, 102, 0.55, 1180))
write(f"{WB}/marker_M_b.wav", marker(0.34, 103, 0.7, 1320))
write(f"{WB}/marker_S_a.wav", marker(0.14, 104, 0.5, 1250))
write(f"{WB}/marker_S_b.wav", marker(0.14, 105, 0.45, 1400))
x = np.zeros(int(0.26 * SR))
for i, at in enumerate([0.0, 0.08, 0.16]): place(x, marker(0.07, 106 + i, 0.3, 1300 + 90 * i), at)
write(f"{WB}/marker_taps.wav", x)
marker_run(f"{WB}/marker_write_title.wav", 9, 0.11, 120, 1150)
marker_run(f"{WB}/marker_write_caption.wav", 10, 0.06, 140, 1300)
# chalkboard: chalk is grit, not squeak. Each stroke sound is as long as its stroke in styles/chalkboard/swatch.js (XS 0.07,
# S 0.14, M 0.35, L 0.5 s) and follows the same minimum-jerk speed curve: the stick's "tok" on the slate, then dense
# little impacts of the stick skipping over the board's tooth (more and harder where the hand is fast) over a dry scrape
def chalk(dur, seed, f_tok=1100):
    n = int((dur + 0.02) * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    u = np.clip(t / dur, 0, 1); v = 16 * u * u * (1 - u) ** 2; e = (0.2 + 0.8 * v) * np.where(t > dur, np.exp(-(t - dur) / 0.004), 1.0)
    rate = 300 + 1700 * v                                                  # skips per second
    hits = (r.random(n) < rate / SR).astype(float) * r.uniform(0.3, 1.0, n)
    grit = np.convolve(hits, np.exp(-np.arange(48) / 6.0), "same")
    grit = band(grit, 1500, 8000) * e * 1.6
    scrape = band(r.standard_normal(n), 700, 4500) * e * 0.18
    tok = mixed(burst(int(0.015 * SR), 1200, 6000, 0.002, r), modes(int(0.04 * SR), [f_tok, f_tok * 2.3], [0.007, 0.004], [0.6, 0.25]))
    x = grit + scrape; x[:len(tok)] += tok * 1.3
    x[-int(0.005 * SR):] *= np.linspace(1, 0, int(0.005 * SR))
    return x
def felt(dur, seed, zig, land=True):
    """a felt eraser dragged over slate: soft low noise, louder on each pass, with a turn at each end of a zigzag"""
    n = int((dur + 0.03) * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    u = np.clip(t / dur, 0, 1)
    passes = np.abs(np.sin(np.pi * zig * u)) ** 0.6 if zig > 1 else 16 * u * u * (1 - u) ** 2
    e = (0.25 + 0.75 * passes) * np.minimum(1, t / 0.01) * np.where(t > dur, np.exp(-(t - dur) / 0.01), 1.0)
    x = band(r.standard_normal(n), 220, 2600) * e * 0.5 + band(r.standard_normal(n), 2600, 6000) * e * 0.08
    if land: x[:int(0.04 * SR)] += modes(int(0.04 * SR), [120, 310], [0.012, 0.006], [0.9, 0.4])
    x[-int(0.008 * SR):] *= np.linspace(1, 0, int(0.008 * SR))
    return x
def taps(path, at, seed, dur=0.07):
    x = np.zeros(int((at[-1] + dur + 0.03) * SR))
    for i, a in enumerate(at): place(x, chalk(dur, seed + i, 1000 + 120 * i), a)
    write(path, x)
CB = "styles/chalkboard/sfx"
write(f"{CB}/chalk_L.wav", chalk(0.5, 201, 980))
write(f"{CB}/chalk_M_a.wav", chalk(0.35, 202, 1050))
write(f"{CB}/chalk_M_b.wav", chalk(0.35, 203, 1180))
write(f"{CB}/chalk_S_a.wav", chalk(0.14, 204, 1250))
write(f"{CB}/chalk_S_b.wav", chalk(0.14, 205, 1120))
taps(f"{CB}/chalk_taps.wav", [0.0, 0.14, 0.28], 206)
taps(f"{CB}/chalk_taps_b.wav", [0.0, 0.12, 0.24], 210)
write(f"{CB}/eraser_sweep.wav", felt(0.85, 220, 1))
write(f"{CB}/eraser_scrub.wav", felt(0.6, 221, 10))
x = np.zeros(int((9 * 0.11 + 0.03) * SR))
for i in range(9): place(x, chalk(0.11 * 0.86, 230 + i, 1000 + 60 * (i % 4)), i * 0.11)
write(f"{CB}/chalk_write_title.wav", x)
x = np.zeros(int((10 * 0.06 + 0.03) * SR))
for i in range(10): place(x, chalk(0.06 * 0.86, 250 + i, 1100 + 50 * (i % 3)) * (2.2 if i == 0 else 1.0), i * 0.06)   # the first tok leads
write(f"{CB}/chalk_write_caption.wav", x)
# gold-line-dark: the light pen's head. A faint sparkler crackle and an airy whistle whose pitch and level follow the same
# minimum-jerk speed curve as the line (styles/gold-line-dark/swatch.js: ridge 1.15 s, shore 0.62 s, boat 0.42 s); the gold
# leaf's gleam is a bright metallic shimmer sweeping up
def spark(dur, seed, f0=1800):
    n = int((dur + 0.03) * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    u = np.clip(t / dur, 0, 1); v = 16 * u * u * (1 - u) ** 2
    e = (0.15 + 0.85 * v) * np.minimum(1, t / 0.01) * np.where(t > dur, np.exp(-(t - dur) / 0.01), 1.0)
    hits = (r.random(n) < (150 + 900 * v) / SR).astype(float) * r.uniform(0.2, 1.0, n)
    crackle = band(np.convolve(hits, np.exp(-np.arange(30) / 4.0), "same"), 4000, 12000) * e
    f = f0 * (0.7 + 0.6 * v); ph = 2 * np.pi * np.cumsum(f) / SR
    r.standard_normal(n)                                                   # a draw the committed takes were made with
    whistle = np.sin(ph) * e * 0.18
    air = band(r.standard_normal(n), 1500, 7000) * e * 0.25
    x = crackle * 0.9 + whistle + air
    x[:int(0.012 * SR)] += burst(int(0.012 * SR), 3000, 11000, 0.002, r) * 0.9      # the spark catching
    x[-int(0.008 * SR):] *= np.linspace(1, 0, int(0.008 * SR))
    return x
GL = "styles/gold-line-dark/sfx"
write(f"{GL}/spark_L.wav", spark(1.15, 301, 1500))
write(f"{GL}/spark_M.wav", spark(0.62, 302, 1700))
write(f"{GL}/spark_S.wav", spark(0.42, 303, 2000))
n = int(1.1 * SR); t = np.arange(n) / SR; r = np.random.default_rng(310); x = np.zeros(n)
for k, f in enumerate([2637, 3136, 3951, 4699, 5274]):     # E7-ish partials, entering one after another as the band moves up
    at = 0.03 + k * 0.1; env = np.where(t >= at, np.exp(-(t - at) / 0.35) * np.minimum(1, (t - at) / 0.004), 0)
    x += np.sin(2 * np.pi * f * t * (1 + 0.001 * k)) * env * (0.5 - 0.06 * k)
x += band(r.standard_normal(n), 5000, 12000) * np.exp(-t / 0.25) * np.minimum(1, t / 0.005) * 0.3
x[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
write(f"{GL}/gleam.wav", x)
# era-media-relay: each era's tool makes its own sound (styles/era-media-relay/swatch.js: brush strokes 0.46, 0.40, 0.26 s;
# the roller 0.75 s; the scan beam; the pixels; the drop of water)
def brush(dur, seed):
    """soft hair on rice paper: a hush shaped by the stroke's speed, a soft touch at the start"""
    n = int((dur + 0.03) * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    u = np.clip(t / dur, 0, 1); v = 16 * u * u * (1 - u) ** 2
    e = (0.2 + 0.8 * v) * np.minimum(1, t / 0.006) * np.where(t > dur, np.exp(-(t - dur) / 0.01), 1.0)
    x = band(r.standard_normal(n), 300, 3200) * e * 0.5 + band(r.standard_normal(n), 3200, 8000) * e * v * 0.12
    x[:int(0.03 * SR)] += modes(int(0.03 * SR), [160, 420], [0.01, 0.005], [0.9, 0.35]) + burst(int(0.03 * SR), 1500, 6000, 0.004, r) * 0.6
    x[-int(0.008 * SR):] *= np.linspace(1, 0, int(0.008 * SR))
    return x
EM = "styles/era-media-relay/sfx"
write(f"{EM}/brush_L.wav", brush(0.46, 401))
write(f"{EM}/brush_M.wav", brush(0.40, 402))
write(f"{EM}/brush_S.wav", brush(0.26, 403))
n = int(0.8 * SR); t = np.arange(n) / SR; r = np.random.default_rng(410)     # the roller: rumble, the ink's tack
v = np.sin(np.pi * np.clip(t / 0.75, 0, 1)) ** 0.7
rum = band(r.standard_normal(n), 60, 500) * (1 + 0.4 * np.sin(2 * np.pi * 11 * t)) * v
tack = band((r.random(n) < 300 / SR).astype(float) * r.uniform(0.3, 1, n), 1800, 6000) * v * 2.0
x = rum * 0.8 + tack; x[:int(0.04 * SR)] += modes(int(0.04 * SR), [110, 240], [0.015, 0.008], [0.8, 0.3])
x[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR)); write(f"{EM}/roller.wav", x)
r = np.random.default_rng(411)                                                # the seal: wood on paper
write(f"{EM}/seal.wav", mixed(modes(int(0.2 * SR), [210, 560, 1300], [0.03, 0.015, 0.008], [0.9, 0.4, 0.2]), burst(int(0.05 * SR), 900, 4000, 0.006, r) * 0.5))
n = int(0.6 * SR); t = np.arange(n) / SR; r = np.random.default_rng(412)     # the tube coming on: a thunk, a rising whine, static
thunk = np.sin(2 * np.pi * 55 * t) * np.exp(-t / 0.08) * np.minimum(1, t / 0.003)
f = 300 + 2700 * np.clip(t / 0.5, 0, 1) ** 2; whine = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.08 * np.minimum(1, t / 0.05) * np.exp(-np.maximum(0, t - 0.45) / 0.05)
static = band(r.standard_normal(n), 2000, 9000) * np.exp(-t / 0.15) * 0.3
x = thunk + whine + static; x[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR)); write(f"{EM}/crt_on.wav", x)
def square(f, dur, duty=0.25):
    n = int(dur * SR); t = np.arange(n) / SR; ph = (f * t) % 1.0
    y = np.where(ph < duty, 1.0, -1.0) * 0.3; k = int(0.003 * SR); y[:k] *= np.linspace(0, 1, k); y[-k:] *= np.linspace(1, 0, k)
    return y
x = np.zeros(int(0.62 * SR))                                                  # the pixels: a stepped fall in square waves
for i, semi in enumerate([24, 19, 15, 12, 7, 3, 0, -5]): place(x, square(440 * 2 ** (semi / 12), 0.07, 0.125 if i % 2 else 0.25), i * 0.07)
write(f"{EM}/pixel_down.wav", x)
x = np.zeros(int(1.0 * SR))                                                   # typing in pixels: a blip per glyph, title then caption
for i in range(9): place(x, square(880 * (1 + 0.06 * (i % 3)), 0.03) * (2.0 if i == 0 else 1.0), i * 0.055)   # the first key leads
for i in range(10): place(x, square(660 * (1 + 0.05 * (i % 2)), 0.025, 0.125), 0.45 + i * 0.04)
write(f"{EM}/chip_type.wav", x)
n = int(0.5 * SR); t = np.arange(n) / SR; r = np.random.default_rng(413)     # the drop: a plip and a small splash
f = 500 + 1300 * np.clip(t / 0.035, 0, 1); plip = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05) * np.minimum(1, t / 0.002)
x = plip + band(r.standard_normal(n), 1500, 7000) * np.exp(-t / 0.06) * 0.25
x[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR)); write(f"{EM}/drop.wav", x)
print("ok")
