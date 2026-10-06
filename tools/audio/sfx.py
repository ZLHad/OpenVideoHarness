"""Code-synthesised sound effects + an event placer → an SFX track that lines up with on-screen actions.

usage (via bin/vh sfx):
  python tools/audio/sfx.py lib <out_dir>                         the built-in library: 48 kHz mono WAVs, the plain variant 0
  python tools/audio/sfx.py place <events.json> <out.wav> [duration_s] [--lib DIR]   → 48 kHz STEREO track
                                                                  + <out>.events.json: levels, variants
  python tools/audio/sfx.py audition <name|all> [n] [key=value …] [--walk] [--out FILE.wav] [--png]
       hear a family: n variants of one built-in (default 8: the first event of n different films), 0.6 s of silence
       between them; --walk: one film's n events of it in a row; `all`: the plain sound of every built-in. key=value
       shapes each variant (dur=1.2 dir=down tone=0.5). Writes FILE.wav (default
       ./sfx-audition-<name>.wav), FILE.txt (one line per sound: its parameters, and what it measures: length, spectral
       centroid, sweep in octaves per second), FILE.json (the event list it placed, for bin/vh qa) and, with --png,
       FILE.png: a spectrogram with each sound labelled, for anyone who has to judge it without listening.
events.json: [{"t": 3.20, "sfx": "click", "gain_db": -6}, {"t": 7.95, "sfx": "whoosh", "pan": -0.6, "dist": 3}, …]
  "sfx" is a library name or a path to your own sound (recorded / licensed: log its source in NOTES.md; any format,
  bit depth or sample rate ffmpeg decodes; stereo files are folded to mono and treated as a point source).
  t is when the sound should LAND; each built-in sound's landmark (its perceptual hit) is aligned to t,
  so a whoosh peaks on the cut and a riser peaks on the drop (a shaped or varied swell: the middle of its loudest 50 ms;
  swish_rev, tape and riser end on t, on their last sample; shimmer starts on it).
  pan  (optional, −1 left … 0 centre … 1 right): equal-power, normalised so centre = the mono level on both channels
       (events without pan are sample-identical to the old mono placement); hard left/right = +3 dB on that side, total
       power constant. Derive it from the sounding object's on-screen x: pan = 2 · x / width − 1 (clamp; soften × 0.7).
  pan_from / pan_to (optional, −1 … 1): the sound travels across the stereo field while it plays (a smoothstep over its
       length; a missing end is pan), e.g. a whoosh that follows the move from left to right. Any sound, files too.
  dist (optional, ≥ 1, distance in units of the reference distance; 1 = as recorded): level × 1/dist (−6 dB per
       doubling) plus a gentle 1st-order low-pass at 16 kHz / dist (≥ 1 kHz). Filter delay < 0.2 ms: landmarks hold.
  role (optional: hero | detail | ambience | signal): the event's class for a mix profile (bin/vh mix … profile=…),
       which levels each class relative to the narration or the music. Without it the class comes from "layer":
       "sonification" (→ signal) or from a name hint (impact → hero, click → detail, gust → ambience …); write it when
       the hint is wrong for the film, e.g. a gust that is the gag's action (detail) or the one thock that lands the hook
       (hero). `place` checks it and writes it into the sidecar.
SHAPING A BUILT-IN TO ITS MOVE (optional; the transitions take all of these, typing dur and pitch, riser dur, pitch and
  bright, the other gestures and hits pitch, the signals none: SPEC below; `sfx audition` to hear them). Every tool that
  renders an event (sfx place, bin/vh mix … events=, audition; qa only when one of its checks renders it) checks these
  and stops on a wrong one.
  dur     length in s: follow the transition (a 0.3 s slide gets a 0.3 s whoosh). Without pitch or center, a longer
          sound is also lower (−4 semitones per doubling): small, fast moves come out higher and airier, big, slow ones
          lower and fuller.
  pitch   semitones from the sound's own centre; center: that centre in Hz instead (pitch then shifts from it), within
          the family's range (whoosh 350–5000, whip 600–8000, swoosh_tonal 150–3000, air 600–7000, paper 800–9000, tape
          55–880, shimmer 440–4000); where pitch and a variant would take it past the range, it stops at the edge.
  dir     "up" (a rising sweep) or "down" (falling), either case. swish_rev's is as heard; tape: down = a stop, up = a rewind.
  bright  −1 … 1: darker (a 1.5 kHz low-pass blended in, all of it at −1) … brighter (up to +6 dB above 3 kHz).
  tone    0 … 1: pure air … a pitched, resonant layer that follows the sweep.
VARIANTS: an event of a varying built-in that pins no "variant" gets one from its film's walk for that sound. The film's
  salt is which sounds the event list uses and how often ("click×6 pop×3 whoosh×5"), not when; the walk starts at a
  base from (name, salt) and takes one step per event of that sound in time order, so the variant is base · 1000 + step
  (e.g. 4821003: base 4821, the 4th whoosh). A step moves each dimension 25–60 % of its half-range, mostly the way it
  moved last time, and turns back at the ends: consecutive whooshes are never the same and never far apart, and over a
  film the gesture drifts, like one hand. Films differ from each other, and the same events.json renders the same
  bytes. Retiming events re-rolls nothing unless two of one sound swap order; adding or removing an event re-rolls the
  film's unpinned events. Pin "variant": n (the sidecar lists each event's) to keep one wherever it moves.
  A variant moves only what the event leaves out, within a range that keeps the family: the transitions' length (±25 %),
  pitch (±3 semitones, and lower when longer), where the peak sits, how far the sweep travels, brightness, tone and level
  (±1.5 dB); the gestures' pitch (≤ ±1.5 semitones), length and level; impact and boom their attack (the crack's band,
  decay and level, the body's delay), decay and level, never the body's pitch; riser its pitch, brightness and level.
  Variant 0 is the plain sound, what `sfx lib` writes. ding, success, error and toggle are signals and never vary: a
  viewer learns what they mean.
  --lib: `sfx lib` also writes sfx-lib.json (each WAV's built-in name and sha256). A listed WAV with its hash unchanged is
  that built-in and varies like it; any other WAV (your own, under a built-in's name or not) is used as recorded and
  takes no variant or shaping, and a listed WAV that changed is named on stderr. A folder without the manifest (an older
  `sfx lib`) falls back to comparing bytes with today's plain sound, with a note.
The sidecar <out>.events.json lists, per event: its class and why, where it starts, the variant and shape it got, and
  its own level as placed: fast (loudest 100 ms, K-weighted LUFS), m400 (loudest 400 ms), tp (true peak, dBTP), len
  (s within 20 dB of fast), lf (share of its energy under 150 Hz: above 0.6 a phone or laptop speaker barely plays it).
  The windows stop at the event's edges, so a short or front-loaded sound reads high (tick +7, click +5, pop +3 LU): the
  mix profiles' class ranges are calibrated on exactly this. A mix profile does not need the sidecar (it measures each
  event itself); it is for reading the foley's levels before mixing.
Built-ins (all original, deterministic and license-free: MIT, part of this repo, synthesised in numpy):
  transitions  whoosh (band-swept noise, the general one) · swish_rev (a reversed swish that ends on t) · whip (short
               and sharp: cartoon, fast cuts) · swoosh_tonal (a pitched glide: sci-fi, UI) · air (a soft breath: calm,
               data, documentary) · paper (a paper slide with grain: hand-drawn, collage, cut-out) · tape (a tape stop
               or rewind that ends on t: retro, VHS) · shimmer (a bright pentatonic sparkle for reveals, in A: set pitch
               to fit the score)
  gestures     click tick pop typing shutter glitch     builds and hits  riser impact boom
  signals      ding success error toggle
Each built-in draws from its own random stream, seeded by its name and variant, so the same event gives the same
samples whatever else was rendered first. A shaped or varied sound is levelled to the loudest 50 ms of its plain one
(± the variant's level) and goes through the same soft knee over 0.9 as the plain one. impact, boom, ding, success and
glitch end in a 50 ms raised-cosine fade, riser in 4 ms, tape in 10 ms (their tails used to stop dead and click).
"""
import json, subprocess, sys, wave, zlib
from pathlib import Path
import numpy as np
from scipy.signal import butter, lfilter, sosfilt

SR = 48000
CLASSES = ("hero", "detail", "ambience", "signal")
rng = np.random.default_rng(11)   # re-seeded for every built-in by render()

def lp(x, f): b, a = butter(2, min(f, SR * .45) / (SR / 2), "low"); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), min(hi, SR * .45) / (SR / 2)], "band"); return lfilter(b, a, x)
def T(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))
def tone(freqs, t): return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(freqs, t.shape)) / SR)

# ── helpers for the shaped sounds
def nrm(x): r = np.sqrt(np.mean(x ** 2)) if len(x) else 0; return x / r if r > 0 else x
def smooth(x): return x * x * (3 - 2 * x)
def swell(x, pk, rise=1.0, fall=1.0):
    """0 → 1 at pk (0…1 of the sound) → 0, sin²-shaped on each side; rise / fall > 1 make that side steeper"""
    a = np.sin(np.pi / 2 * np.clip(x / max(pk, 1e-6), 0, 1)) ** 2
    b = np.sin(np.pi / 2 * np.clip((1 - x) / max(1 - pk, 1e-6), 0, 1)) ** 2
    return np.where(x < pk, a ** rise, b ** fall)
def sweep(c, octaves, s): return c * 2 ** (octaves * (s - .5))   # a centre c Hz moving over `octaves` as s goes 0 → 1
def nb(fc, bw):
    """narrowband noise around a moving centre fc (Hz per sample): two independent low-passed noises (bandwidth bw Hz)
    on a cosine / sine pair, so the band follows fc exactly, however fast it moves"""
    sos = butter(4, min(bw / 2, SR * .2) / (SR / 2), "low", output="sos")
    i, q = sosfilt(sos, rng.standard_normal(len(fc))), sosfilt(sos, rng.standard_normal(len(fc)))
    ph = 2 * np.pi * np.cumsum(fc) / SR
    return nrm(i * np.cos(ph) - q * np.sin(ph))
def osc(fc, partials=((1, 1.0),)):
    """an oscillator following fc (Hz per sample): harmonics h with amplitude a, each silent where it would pass 21.6 kHz"""
    ph = 2 * np.pi * np.cumsum(fc) / SR
    return sum(a * np.sin(h * ph) * (h * fc < SR * .45) for h, a in partials)
def fl(p): return (1.0, 1.0) if p is None else (p["f"], p["len"])   # frequency and length factors (1.0 = the plain sound)
def tail(y, s=.05):
    """a raised-cosine fade over the last s seconds: a body or a bell cut off mid-ring ended in a click (qa: up to 1593×)"""
    m = min(len(y), int(s * SR)); y = np.array(y, dtype=np.float64); y[len(y) - m:] *= .5 + .5 * np.cos(np.pi * np.arange(m) / m)
    return y

# ── gestures, hits and signals. With p None or plain (factors of exactly 1.0) each is sample for sample the old sound.
def click(p=None):
    f, L = fl(p); t = T(.03 * L)
    return hp(noise(.03 * L), 2500 * f) * np.exp(-t / (.004 * L)) * .5 + np.sin(2*np.pi*1800*f*t) * np.exp(-t / (.006 * L)) * .3
def tick(p=None):
    f, L = fl(p); t = T(.02 * L); x = np.sin(2*np.pi*3200*f*t) * np.exp(-t / (.003 * L)) * .45
    if p is not None and p["variant"]:   # a faint inharmonic partial (1.7–2.7×, 0–24 %): wood or metal; 3 ms of sine alone barely differs
        fp = 3200 * f * (2.2 + .5 * p["x"][0])
        if fp < SR * .45: x = x + np.sin(2*np.pi*fp*t) * np.exp(-t / (.002 * L)) * .45 * .12 * (1 + p["x"][1])
    return x
def pop(p=None):     f, L = fl(p); t = T(.12 * L); return tone(900 * f * np.exp(-t / (.02 * L)) + 250 * f, t) * np.exp(-t / (.03 * L)) * .6
def toggle(p=None):  t = T(.09); return tone(np.where(t < .03, 1300, 1900), t) * np.exp(-t / .03) * .35
def typing(p=None):
    if p is None or p["plain"]:
        out = np.zeros(int(.6 * SR))
        for k in range(6):
            i = int((k * .09 + rng.uniform(0, .02)) * SR); x = click() * rng.uniform(.5, .9)
            out[i:i + len(x)] += x[: len(out) - i]
        return out
    d, L = p["dur"], p["len"]; keys = max(1, int(round((d - .06) / (.09 * L)))); out = np.zeros(int((d + .05) * SR))
    for k in range(keys):   # every key a little different: a keyboard's keys are not one sample
        i = int((k * .09 * L + rng.uniform(0, .025)) * SR)
        x = click(dict(p, f=p["f"] * 2 ** (rng.uniform(-1, 1) / 12), len=2 ** rng.uniform(-.2, .2))) * rng.uniform(.5, .9)
        out[i:i + len(x)] += x[: len(out) - i]
    return out
def whoosh(p):
    """noise through 8 bands whose turns sweep across the sound; warp moves the peak, span widens the sweep"""
    d = p["dur"]; t = T(d); u = (t / d) ** p["warp"]
    k = np.sin(np.pi * t / d) ** 2 if p["warp"] == 1 else np.sin(np.pi * u) ** 2   # the first: the plain whoosh's own arithmetic
    x = np.zeros_like(t); n = noise(d)
    lo, hi = 400 * p["f"], min(14000.0, 5000 * p["f"] * 2 ** p["span"])
    up = p["dir"] == "up"
    q = p["q"]   # band width: < 1 narrower (more pitched), > 1 wider (more airy); 1.0 for the plain whoosh
    for i, fc in enumerate(np.linspace(lo, hi, 8)):   # sweep through bands for motion
        w = np.exp(-((u - (i / 7 if up else 1 - i / 7)) ** 2) / .03); x += bp(n, fc * .7 ** q, fc * 1.4 ** q) * w
    x = x * k * .5
    if p["tone"] > 0:   # a resonance an octave and a half under the moving band: air through a tube
        fc = np.clip((lo + (hi - lo) * (u if up else 1 - u)) / 3, 90, 4000)
        r = (osc(fc, ((1, 1), (2, .3))) + nb(fc, 60)) * k
        x = x * (1 - .5 * p["tone"]) + p["tone"] * nrm(r) * np.sqrt(np.mean(x ** 2))
    return x
def swish_rev(p): return whoosh(dict(p, dir="down" if p["dir"] == "up" else "up"))[::-1] * .8   # dir is as heard
def riser(p=None):
    f = 1.0 if p is None else p["f"]; d = 2.0 if p is None else p["dur"]
    t = T(d); k = t / d
    return tail(hp(noise(d), 500 * f) * k ** 2.2 * .3 + tone(300 * f + 2400 * f * k ** 2, t) * k ** 3 * .15, .004)
def crack(d=.05, tau=.005, peak=.8, band=(1000, 4000)):
    """a 1–4 kHz attack: the part of a hit that phone and laptop speakers actually play"""
    t = T(d); x = sosfilt(butter(4, [band[0] / (SR / 2), band[1] / (SR / 2)], "band", output="sos"), noise(d)) * np.exp(-t / tau)
    return x / np.abs(x).max() * peak
def attack(p):
    """a hit's attack for p: the plain one (1–4 kHz crack, 5 ms decay, the body 2 ms behind), or a variant's: the crack's
    band ±0.6 octave, its decay ×0.6–1.6, its level ±2.5 dB and the body 1–3 ms behind. The body's pitch stays put: a
    moved 40 Hz body beat against a score's bass (a 7 dB "pump" in one swatch); the attack is what a phone plays."""
    if p is None or not p["variant"]: return dict(crack=dict(), delay=.002)
    x = p["x"]; b = 2 ** (.6 * x[0])
    return dict(crack=dict(tau=.005 * 1.6 ** x[1], peak=.8 * 10 ** (2.5 * x[2] / 20), band=(1000 * b, 4000 * b)), delay=.002 + .001 * x[3])
def hit(body, delay=.002, fade=.01, peak=.95, **ck):
    """a crack on t, the body 2 ms behind it and faded in over 10 ms, the sum at most a 0.95 peak. Without the crack,
    impact and boom had 98–100 % of their energy under 150 Hz: a thump on headphones, next to nothing on a phone."""
    x = np.zeros(len(body)); i = int(delay * SR)
    x[i:] = (body * np.minimum(1, np.arange(len(body)) / SR / fade))[:len(body) - i]
    c = crack(**ck); x[:len(c)] += c
    return x * min(1.0, peak / np.abs(x).max())
def impact(p=None):
    f, L = fl(p); t = T(1.6); a = attack(p); n = 1200 * f * (1 if p is None or not p["variant"] else 2 ** (.5 * p["x"][4]))
    return tail(hit(tone(40 * f + 90 * f * np.exp(-t / (.05 * L)), t) * np.exp(-t / (.6 * L)) * .9 + lp(noise(1.6), n) * np.exp(-t / (.2 * L)) * .35,
                    a["delay"], **a["crack"]))
def boom(p=None):
    f, L = fl(p); t = T(2.4); a = attack(p)
    return tail(hit(tone(34 * f + 40 * f * np.exp(-t / (.1 * L)), t) * np.exp(-t / (1.0 * L)) * .95, a["delay"], **a["crack"]))
def ding(p=None):
    t = T(1.2); x = sum(a * np.sin(2*np.pi*f*t) * np.exp(-t / d) for f, a, d in [(1318, .5, .5), (2637, .2, .25), (3951, .08, .12)])
    return tail(x * np.minimum(1, t / .002) * .6)   # (success's two dings get the fade too: the first one was cut at 1.2 s)
def success(p=None):
    out = np.zeros(int(1.3 * SR)); a, b = ding() * .7, ding() * .8
    b = np.interp(np.arange(len(b)) * 1.335, np.arange(len(b)), b)  # up a fourth
    out[:len(a)] += a[:len(out)]; i = int(.14 * SR); out[i:i + len(b)] += b[: len(out) - i]; return out
def error(p=None):   # two beeps: the second rises from the first one's tail in 2 ms, and the end fades in 5 ms (hard edges clicked)
    t = T(.35); u = np.where(t < .17, t, t - .17)
    e = np.maximum(np.minimum(1, u / .002) * np.exp(-u / .08), np.where(t >= .17, np.exp(-t / .08), 0)) * np.clip((.35 - t) / .005, 0, 1)
    return tone(np.where(t < .16, 330, 247), t) * e * .35
def glitch(p=None):
    f = 1.0 if p is None else p["f"]
    t = T(.25); x = np.sign(np.sin(2*np.pi*(rng.choice([80, 160, 640, 1280], len(t) // 600 + 1) * f).repeat(600)[: len(t)] * t))
    g = rng.random(len(t) // 480 + 1) > .35
    if p is not None and p["variant"]: g[0] = True   # a variant's first 10 ms always sound: it starts on t, as the plain one does
    return tail(x * g.repeat(480)[: len(t)] * .25 * np.exp(-t / .2))
def shutter(p=None):
    f, L = fl(p); t = T(.18)
    x = hp(noise(.18), 1500 * f) * (np.exp(-t / .01) + .6 * np.exp(-np.maximum(t - .07 * L, 0) / .012) * (t > .07 * L)); return x * .45

# ── the transitions added with variants: each takes the shaping parameters (TAKES) and is levelled to TARGET
def whip(p):
    """a fast narrow-to-wide noise band snapping across ~2 octaves, steep attack, quick tail: a cartoon or whip-pan cut"""
    d = p["dur"]; t = T(d); x = t / d; s = smooth(x) if p["dir"] == "up" else 1 - smooth(x)
    c = 2400 * p["f"]; fc = np.clip(sweep(c, 2.2 + p["span"], s), 150, 14000)
    y = .6 * nb(fc, 1.1 * c) + .4 * nb(fc, .3 * c)
    if p["tone"] > 0: y = (1 - .5 * p["tone"]) * y + p["tone"] * nrm(osc(fc / 2, ((1, 1), (2, .25))))
    return hp(y, 250) * swell(x, p["peak"], 1.0, 2.0)
def swoosh_tonal(p):
    """a pitched glide (fundamental, 2nd and 3rd harmonics, a second voice 10 cents up, a slow vibrato) over a band of air
    an octave above it, low-passed at 7 kHz: a sci-fi or UI sweep"""
    d = p["dur"]; t = T(d); x = t / d; s = smooth(x) if p["dir"] == "up" else 1 - smooth(x)
    c = 700 * p["f"]; f0 = np.clip(sweep(c, 1.6 + p["span"], s), 60, 6000) * (1 + .004 * np.sin(2 * np.pi * 5.5 * t))
    voice = osc(f0, ((1, 1), (2, .35), (3, .12))) + .6 * osc(f0 * 1.006, ((1, 1), (2, .3)))
    y = p["tone"] * nrm(voice) + (1 - p["tone"]) * nb(np.clip(f0 * 2, 100, 14000), .5 * c)
    return lp(y, 7000) * swell(x, p["peak"], 1.4, 1.0)
def air(p):
    """breath through a soft band: noise over a gentle high-pass at c/5, under a 12 dB/octave low-pass that opens (up) or
    closes (down) over ~1.4 octaves around c, a whisper of hiss over 5 kHz, a breath formant (tone) that the variant
    moves; a slow swell. Brighter and more various than its first version (52 % of variant pairs alike, all under 4 kHz)"""
    d = p["dur"]; t = T(d); x = t / d; s = x if p["dir"] == "up" else 1 - x; xx = p["x"]
    c = 2400 * p["f"]; sp = 1.4 + p["span"]; n = hp(noise(d), max(80.0, c / 5 * 2 ** (.8 * xx[2])))
    y = sum(np.clip(1 - np.abs(2 * s - k), 0, 1) * lp(n, c * 2 ** (sp * (k / 2 - .5))) for k in range(3))
    y = nrm(y) + (.18 + .1 * xx[1]) * nrm(hp(n, 5000)) * (.4 + .6 * s)
    if p["tone"] > 0: y = (1 - .6 * p["tone"]) * nrm(y) + p["tone"] * nb(np.clip(sweep(c * .6 * 2 ** (.9 * xx[0]), sp * .5, s), 120, 9000), 260)
    return y * swell(x, p["peak"], 1.6, 1.3)
def paper(p):
    """a hiss band sliding up or down half an octave each way, grained by sparse 2 ms bumps (the fibres), with a soft
    low "thp" (tone) where the sheet lands, at the peak"""
    d = p["dur"]; t = T(d); x = t / d; s = x if p["dir"] == "up" else 1 - x; n = len(t)
    c = 3000 * p["f"]; sp = .8 + p["span"]; src = noise(d)
    band = lambda f: sosfilt(butter(4, [f / 1.8 / (SR / 2), min(f * 1.8, SR * .45) / (SR / 2)], "band", output="sos"), src)
    a, b = (float(np.clip(c * 2 ** (sp * h), 200, SR * .45 / 1.9)) for h in (-.5, .5))   # a band's low edge under its high one
    slide = (1 - s) * band(a) + s * band(b)
    g = lp((rng.random(n) < 420 / SR) * rng.uniform(.25, 1, n), 260); g = g / max(np.abs(g).max(), 1e-12)
    y = nrm(slide) * (.55 + 1.2 * np.abs(g)) * swell(x, p["peak"], .7, 1.6)
    if p["tone"] > 0:
        m = int(.06 * SR); tt = np.arange(m) / SR; i = min(n - 1, int(p["peak"] * n))
        th = bp(rng.standard_normal(m), 280, 1400) * np.exp(-tt / .014) * np.minimum(1, tt / .002)
        y = np.pad(y, (0, max(0, i + m - n)))   # a short sheet: the landing rings past its end, not cut off
        y[i:i + m] += p["tone"] * th / max(np.abs(th).max(), 1e-12) * np.abs(y).max() * .8
    return lp(y, 11000)
def tape(p):
    """a root, fifth and octave (8 harmonics each, a moving low-pass) whose speed sinks to nothing (down: a tape stop) or
    spins up from a crawl (up: a rewind), with wow and hiss; tone sets tone ↔ hiss. It ends on t."""
    d = p["dur"]; t = T(d); x = t / d; c = 220 * p["f"]; ph0 = rng.uniform(0, 2 * np.pi)
    if p["dir"] == "down":
        sp = (1 - x) ** (1.5 + p["span"]); amp = sp ** .35 * np.minimum(1, t / .01)
        wow = 1 + .006 * np.sin(2 * np.pi * 5.2 * t + ph0)
    else:
        sp = .12 + .88 * x ** (1.6 + p["span"]); c *= 2
        amp = (.35 + .65 * x) * np.clip((d - t) / .006, 0, 1) * np.minimum(1, t / .01)
        wow = 1 + .03 * np.sin(2 * np.pi * 11 * t + ph0)
    f0 = c * sp * wow + .5; cut = 250 + 7000 * sp; y = np.zeros(len(t))
    for r, a0 in ((1, 1), (1.5, .55), (2, .45)):
        ph = 2 * np.pi * np.cumsum(f0 * r) / SR
        for h in range(1, 9):
            fh = f0 * r * h; y += a0 / h / np.sqrt(1 + (fh / cut) ** 4) * (fh < SR * .45) * np.sin(h * ph)
    hiss = lp(hp(noise(d), 1500), 9000) * sp ** 1.5
    y = sosfilt(butter(2, 22 / (SR / 2), "high", output="sos"), (p["tone"] * nrm(y) + (1 - p["tone"]) * nrm(hiss)) * amp)
    return tail(y, .01)   # the last cycles of a stop sink under 20 Hz: high-passed (no DC or infrasound), then a 10 ms end
PENTA = (0, 2, 4, 7, 9)
def shimmer(p):
    """8–14 glassy grains (a sine and a quieter partial at 2.76×) on a major pentatonic over three octaves around A6,
    arpeggiated up or down across the first ~40 %, over a breath of air; it starts on t"""
    d = p["dur"]; t = T(d); n = len(t); R = 1760 * p["f"]
    N = int(round(11 + 3 * p["x"][0])); deg = [12 * o + s for o in (-1, 0, 1) for s in PENTA]
    notes = sorted(rng.choice(len(deg), N), reverse=p["dir"] == "down")
    on = (.35 + .1 * p["span"]) * d * (np.arange(N) / max(N - 1, 1)) ** 1.25 + np.r_[0, rng.uniform(0, .012, N - 1)]
    g = np.zeros(n)
    for k in range(N):
        f = R * 2 ** (deg[notes[k]] / 12) * (1 + rng.uniform(-.002, .002)); i = int(on[k] * SR); tt = np.arange(n - i) / SR
        tau, a = rng.uniform(.1, .28), rng.uniform(.5, 1)
        if f > 12000: continue
        part = np.sin(2 * np.pi * f * tt) + (.22 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt / (tau * .5)) if 2.76 * f < SR * .45 else 0)
        g[i:] += a * part * np.exp(-tt / tau) * np.minimum(1, tt / .003)
    y = p["tone"] * nrm(g) + (1 - p["tone"]) * .7 * nrm(hp(noise(d), 5000) * swell(t / d, .12, .8, 1.2))
    return y * np.clip((d - t) / (.3 * d), 0, 1)

LIB = {"click": click, "tick": tick, "pop": pop, "toggle": toggle, "typing": typing, "whoosh": whoosh,
       "swish_rev": swish_rev, "riser": riser, "impact": impact, "boom": boom, "ding": ding, "success": success,
       "error": error, "glitch": glitch, "shutter": shutter,
       "whip": whip, "swoosh_tonal": swoosh_tonal, "air": air, "paper": paper, "tape": tape, "shimmer": shimmer}
# landmark of the PLAIN sound = seconds from its start to its perceptual hit (what should coincide with the action);
# a recorded --lib WAV under one of these names keeps it. A shaped or varied built-in's own is landmark(name, p, x).
LANDMARK = {"whoosh": .35, "swish_rev": .5, "riser": 2.0, "typing": 0.0}

# ── what each built-in takes, its defaults, and how far a variant moves what an event leaves out
TRANS = ("dur", "pitch", "center", "dir", "bright", "tone")
SHAPE = TRANS                          # every shaping key there is
#   jitter half-ranges: dur and len in octaves of length (2^±), pitch in semitones, peak as a share of the sound, span in
#   octaves of sweep, bright and tone absolute, level in dB, q (band width) in octaves (2^±). vpeak: where a variant's peak
#   centres; couple: a longer dur is also lower (COUPLE)
SPEC = {
    "whoosh":       dict(takes=TRANS, dur=.7, center=1414, crange=(350, 5000), dir="up", tone=0, peak=.5, couple=1,
                         jitter=dict(dur=.32, pitch=3, peak=.15, span=.6, bright=.35, tone=.25, level=1.5, q=.5)),
    "swish_rev":    dict(takes=TRANS, dur=.5, center=1414, crange=(350, 5000), dir="down", tone=0, peak=.5, vpeak=.25, couple=1,
                         jitter=dict(dur=.3, pitch=3, peak=.08, span=.6, bright=.35, tone=.25, level=1.5, q=.5)),
    "whip":         dict(takes=TRANS, dur=.22, center=2400, crange=(600, 8000), dir="down", tone=.15, peak=.3, couple=1,
                         jitter=dict(dur=.3, pitch=3, peak=.08, span=.5, bright=.3, tone=.15, level=1.5)),
    "swoosh_tonal": dict(takes=TRANS, dur=.6, center=700, crange=(150, 3000), dir="up", tone=.75, peak=.6, couple=1,
                         jitter=dict(dur=.3, pitch=3, peak=.1, span=.5, bright=.3, tone=.15, level=1.5)),
    "air":          dict(takes=TRANS, dur=.9, center=2400, crange=(600, 7000), dir="up", tone=.25, peak=.55, couple=1,
                         jitter=dict(dur=.35, pitch=5, peak=.12, span=.7, bright=.5, tone=.2, level=1.5)),
    "paper":        dict(takes=TRANS, dur=.35, center=3000, crange=(800, 9000), dir="up", tone=.3, peak=.55, couple=1,
                         jitter=dict(dur=.3, pitch=2, peak=.1, span=.4, bright=.3, tone=.2, level=1.5)),
    "tape":         dict(takes=TRANS, dur=.6, center=220, crange=(55, 880), dir="down", tone=.7, peak=1.0,
                         jitter=dict(dur=.25, pitch=3, span=.3, bright=.25, tone=.15, level=1.5)),
    "shimmer":      dict(takes=TRANS, dur=.9, center=1760, crange=(440, 4000), dir="up", tone=.8, peak=0.0,   # no pitch jitter: in key
                         jitter=dict(dur=.25, span=.3, bright=.3, tone=.1, level=1.5)),
    "click":   dict(takes=("pitch",), jitter=dict(pitch=1, len=.2, level=1.5)),
    "tick":    dict(takes=("pitch",), jitter=dict(pitch=1.5, len=.25, level=1.2)),
    "pop":     dict(takes=("pitch",), jitter=dict(pitch=1.5, len=.2, level=1.5)),
    "shutter": dict(takes=("pitch",), jitter=dict(pitch=1, len=.12, level=1.5)),
    "typing":  dict(takes=("dur", "pitch"), dur=.6, jitter=dict(pitch=1, len=.2, level=1.5)),
    "glitch":  dict(takes=("pitch",), jitter=dict(pitch=1, level=1.5)),
    "riser":   dict(takes=("dur", "pitch", "bright"), dur=2.0, jitter=dict(pitch=1, bright=.2, level=1)),
    "impact":  dict(takes=("pitch",), jitter=dict(len=.12, level=1)),   # no pitch jitter: a moved 40 Hz body beats against
    "boom":    dict(takes=("pitch",), jitter=dict(len=.12, level=1)),   # the score's bass (a 7 dB "pump" in one swatch)
    "ding": dict(takes=()), "success": dict(takes=()), "error": dict(takes=()), "toggle": dict(takes=()),
}
FIXED = tuple(n for n, s in SPEC.items() if not s.get("jitter"))          # the signals: one sound each
SWELLS = ("whoosh", "swish_rev", "riser", "whip", "swoosh_tonal", "air", "paper", "tape")   # no onset on t (a peak or an
                                                                          # end): bin/vh qa's cue check skips them
TARGET = {"whip": -13.0, "swoosh_tonal": -14.0, "air": -15.0, "paper": -16.5, "tape": -14.0, "shimmer": -15.0}
# ↑ loudest 50 ms RMS (dBFS) of the new transitions' plain sounds, near the plain whoosh's −12.4 (air softer, as it is
#   meant to be); the old built-ins are levelled to their own plain sound
COUPLE = 4.0                            # semitones lower per doubling of dur, when the event gives no pitch or center
RANGE = {"dur": (.03, 8.0), "pitch": (-24, 24), "center": (40, 12000), "bright": (-1, 1), "tone": (0, 1),
         "pan_from": (-1, 1), "pan_to": (-1, 1)}
DESCRIBE = {
    "click": "a dry UI click: noise tick + 1.8 kHz body", "tick": "a 3.2 kHz sine tick, 20 ms: counters, clocks",
    "pop": "a falling 900 → 250 Hz blip: things appearing", "toggle": "two-step 1.3 → 1.9 kHz chirp (signal, fixed)",
    "typing": "six key clicks over 0.6 s", "whoosh": "band-swept noise swell: the general transition",
    "swish_rev": "a reversed swish that ends on t: sucked into the cut", "riser": "noise + rising tone over 2 s, peaks on t",
    "impact": "a low hit with a 1–4 kHz crack on t", "boom": "a sub boom with a crack on t", "ding": "a bell partial chord (signal, fixed)",
    "success": "ding then a fourth up (signal, fixed)", "error": "two falling beeps (signal, fixed)",
    "glitch": "gated square bursts", "shutter": "two filtered noise clacks 70 ms apart",
    "whip": "short sharp noise snap over 2 octaves: cartoon, fast cut", "swoosh_tonal": "a pitched glide over air: sci-fi, UI",
    "air": "a soft breath, low-pass opening: calm, data, documentary", "paper": "a grainy paper slide with a soft landing: hand-drawn, collage",
    "tape": "a tape stop (down) or rewind (up) that ends on t: retro, VHS", "shimmer": "a pentatonic glass sparkle from t: reveals",
}

STEP = (.25, .6)   # a walk's step: every dimension moves 0.25–0.6 of its half-range, reflected at the ends
KEEP = .7          # … in the direction it moved last time, with this probability
NJ = 16           # uniforms per variant: 9 named dimensions (below) and 7 extras ("x") a sound may use

def ujit(name, v):
    """a variant's uniforms in −1…1 (NJ, fixed order); variant 0 is all zeros. A variant is base · 1000 + step: the start
    of the walk (base, from its own stream) and that many steps along it, so variants n and n + 1 are neighbours, never
    the same and never far apart, and pinning a number gives that sound back wherever it sits"""
    if not v: return np.zeros(NJ)
    base, k = divmod(int(v), 1000); r = np.random.default_rng([5, zlib.crc32(name.encode()), base])
    u = r.uniform(-1, 1, NJ); way = r.choice([-1.0, 1.0], NJ)
    for _ in range(k):   # each dimension keeps its direction with p = KEEP (a drift, not a zig-zag), turning back at the ends
        way = np.where(r.random(NJ) < KEEP, way, -way); u = u + r.uniform(*STEP, NJ) * way
        way = np.where(np.abs(u) > 1, -way, way); u = np.where(u > 1, 2 - u, np.where(u < -1, -2 - u, u))
    return u

def salt(events):
    """the film's fingerprint for the variants: which sounds it uses and how often ("click×6 pop×3 whoosh×5"), not when.
    Retiming an event never re-rolls anything; adding or removing one re-rolls the unpinned events of the film."""
    c = {}
    for e in events: c[str(e.get("sfx"))] = c.get(str(e.get("sfx")), 0) + 1
    return zlib.crc32(" ".join(f"{k}×{c[k]}" for k in sorted(c)).encode())

def derived(name, salt_, occ):
    """the variant of an event that pins none: the film's walk for this sound (base from the name and the film's salt),
    `occ` steps along it, occ = how many events of this sound come before it in time"""
    return (1 + zlib.crc32(f"{name}|{salt_}".encode()) % 9999) * 1000 + min(int(occ), 999)

def check(e, k=None):
    """the event's shaping fields are of the right kind and in range (whether the sound takes them: resolve)"""
    name = e.get("sfx"); where = f"event {k} ({name} at t={e.get('t')})" if k is not None else f"{name}" + (f" at t={e['t']}" if "t" in e else "")
    for key, (lo, hi) in RANGE.items():
        if key in e:
            v = e[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
                sys.exit(f"sfx: {where}: {key} {v!r} must be a number in {lo} … {hi}")
    if "dir" in e and str(e["dir"]).lower() not in ("up", "down"): sys.exit(f"sfx: {where}: dir {e['dir']!r} must be \"up\" or \"down\"")
    if "variant" in e and (isinstance(e["variant"], bool) or not isinstance(e["variant"], int) or e["variant"] < 0):
        sys.exit(f"sfx: {where}: variant {e['variant']!r} must be a whole number ≥ 0")
    if "center" in e and name in SPEC and "crange" in SPEC[name]:
        lo, hi = SPEC[name]["crange"]
        if not lo <= e["center"] <= hi: sys.exit(f"sfx: {where}: center {e['center']!r} must be in {lo} … {hi} Hz for {name}")

def resolve(name, e=None, occ=0):
    """a built-in's parameters for one event → p: the variant (pinned, else derived; None for a signal), the shaping the
    event gives, and the rest from the variant's jitter around the defaults. p["plain"]: variant 0 with no shaping.
    Checks the event first (bin/vh mix, sfx place, qa and audition all come through here)."""
    S, e = SPEC[name], (e or {}); J = S.get("jitter", {}); takes = S["takes"]
    check(dict(e, sfx=name))
    given = {k: e[k] for k in SHAPE if k in e}
    bad = [k for k in given if k not in takes] + (["variant"] if not J and e.get("variant", 0) != 0 else [])
    if bad:
        where = f"{name} at t={e.get('t')}" if "t" in e else name
        sys.exit(f"sfx: {where}: {name} takes no {', '.join(bad)}" + (f" (it takes {', '.join(takes)}{', variant' if J else ''})" if takes or J else
                 " (a signal: one fixed sound, so a viewer learns what it means)"))
    # no event (sfx lib, a --lib check): the plain sound; an event that pins none: derived from where it sits
    v = None if not J else int(e["variant"]) if "variant" in e else derived(name, e.get("_salt", 0), occ) if "t" in e else 0
    u = ujit(name, v); j = lambda k, i: float(J[k] * u[i]) if k in J and v else 0.0
    d0 = S.get("dur", 1.0); dur = float(given["dur"]) if "dur" in given else d0 * 2 ** j("dur", 0)
    if "pitch" in given or "center" in given: pitch = float(given.get("pitch", 0.0))
    else: pitch = j("pitch", 1) - (COUPLE * np.log2(dur / d0) if S.get("couple") else 0.0)
    c0 = S.get("center", 1.0); center = float(given.get("center", c0)); lo, hi = S.get("crange", (0, np.inf))
    eff = float(np.clip(center * 2 ** (pitch / 12), lo, hi)) if "crange" in S else center * 2 ** (pitch / 12)   # held in the family's range
    peak = S.get("peak", .5)
    if v and "peak" in J: peak = float(np.clip(S.get("vpeak", peak) + j("peak", 2), .1, .9))
    p = {"name": name, "variant": v, "plain": not v and not given, "dur": dur, "pitch": pitch, "f": eff / c0,
         "center": eff, "dir": str(given.get("dir", S.get("dir", "up"))).lower(),
         "bright": float(given["bright"]) if "bright" in given else (j("bright", 4) if "bright" in J else 0.0),
         "tone": float(given["tone"]) if "tone" in given else float(np.clip(S.get("tone", 0) + j("tone", 5), 0, 1)),
         "peak": peak, "span": j("span", 3), "level": j("level", 6), "len": 2 ** j("len", 7), "q": 2 ** j("q", 8), "x": list(u[9:]) if v else [0.0] * (NJ - 9)}
    p["warp"] = 1.0 if peak == .5 else float(np.log(.5) / np.log(peak)) if 0 < peak < 1 else 1.0
    return p

PEAKED = ("whoosh", "whip", "swoosh_tonal", "air", "paper")   # a swell whose hit is where it is loudest

def landmark(name, p, x=None):
    """seconds from the start of the built-in to its hit, for these parameters. A swell (PEAKED) with its samples x lands
    on the middle of its loudest 50 ms, except the plain whoosh, which keeps its 0.35 s (the middle of its envelope, about
    a frame before its loudest 50 ms) so a plain whoosh is placed where it always was. swish_rev, tape and riser end on t
    (tape: its last sample; a rewind's last 6 ms fade), shimmer and the gestures start on it."""
    if name in PEAKED and x is not None and not (p["plain"] and name in LANDMARK):
        w = int(.05 * SR); c = np.concatenate([[0.0], np.cumsum(np.asarray(x, np.float64) ** 2)])
        return (int(np.argmax(c[w:] - c[:-w])) + w / 2) / SR if len(x) > w else len(x) / 2 / SR
    if name in PEAKED: return p["peak"] * p["dur"]
    if name in ("swish_rev", "riser"): return p["dur"]
    if name == "tape": return p["peak"] * p["dur"]
    return LANDMARK.get(name, 0.0)

def landmark_of(e, occ=None, lib_dir=None, root=None, cache=None):
    """an event's landmark as it is placed (a built-in is rendered: a swell lands on its loudest 50 ms); a sound that cannot
    be found: LANDMARK by name"""
    try: return event_sound(e, occ, lib_dir, root, cache)[1]
    except SystemExit: return LANDMARK.get(e.get("sfx"), 0.0)

def shape(p):
    """the resolved parameters worth reading in a sidecar or an audition line"""
    S = SPEC[p["name"]]; o = {}
    if "dur" in S["takes"]: o["dur"] = round(p["dur"], 3)
    if "pitch" in S["takes"]: o["pitch"] = round(p["pitch"], 2)
    if "center" in S["takes"]: o["center"] = round(p["center"], 1)
    for k in ("dir", "bright", "tone"):
        if k in S["takes"]: o[k] = p[k] if k == "dir" else round(p[k], 3)
    if p["variant"]:   # what only a variant moves: where the peak sits, how far the sweep travels (octaves ±), the level (dB)
        J = S["jitter"]; o.update({k: round(p[k], 2) for k in ("peak", "span", "q", "len", "level") if k in J})
    return o

def knee(x, k=0.9):
    """a soft knee: samples over k bend smoothly toward 1.0 (continuous slope at k), so no noise peak reaches full scale
    and `sfx lib`'s 16-bit write never hard-clips; a sound that stays under k is untouched"""
    a = np.abs(x); over = a > k
    if not over.any(): return x
    y = x.copy(); y[over] = np.sign(x[over]) * (k + (1 - k) * np.tanh((a[over] - k) / (1 - k)))
    return y

def loud50(y):
    """the loudest 50 ms RMS of y"""
    w = int(.05 * SR)
    if len(y) <= w: return float(np.sqrt(np.mean(y ** 2))) if len(y) else 0.0
    c = np.concatenate([[0.0], np.cumsum(y.astype(np.float64) ** 2)]); return float(np.sqrt((c[w:] - c[:-w]).max() / w))

def tilt(y, b):
    """bright > 0 lifts the top (y + b · a 3 kHz high-pass: up to +6 dB at 1), < 0 blends in a 1.5 kHz low-pass"""
    return y + b * hp(y, 3000) if b > 0 else y + b * (y - lp(y, 1500))

_REF = {}
def ref_level(name):
    """the loudest 50 ms RMS every shaped or varied sound of this name is levelled to: its plain sound's own, or TARGET"""
    if name not in _REF:
        _REF[name] = 10 ** (TARGET[name] / 20) if name in TARGET else loud50(render(name, resolve(name)))
    return _REF[name]

def render(name, p):
    """a built-in for resolved parameters p → mono float. A plain sound goes through the soft knee over 0.9; a shaped or
    varied one gets its brightness, is levelled to the loudest 50 ms of the plain one (± the variant's level: TARGET for the
    new transitions) and goes through the same knee. (A hard 0.9 cap cost peaky variants 1–6 dB: click, shutter, riser.)"""
    ref = None if p["plain"] and name not in TARGET else ref_level(name)
    global rng
    rng = np.random.default_rng([11, zlib.crc32(name.encode())] + ([p["variant"]] if p["variant"] else []))
    y = LIB[name](p)
    if ref is None: return knee(y)
    if p["bright"]: y = tilt(y, p["bright"])
    return knee(y * ref / max(loud50(y), 1e-12) * 10 ** (p["level"] / 20))

def builtin(name):
    """the plain built-in (variant 0), as `sfx lib` writes it"""
    return render(name, resolve(name))

def write(path, x):  # x: (n,) mono or (n, 2) stereo
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1 if x.ndim == 1 else x.shape[1]); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())

def spatial(x, pan=0.0, dist=1.0, pan_from=None, pan_to=None):
    """mono → (n, 2): distance (1/dist level + gentle air low-pass), then equal-power pan (centre = unity per side);
    with pan_from / pan_to the pan moves from one to the other over the sound (a smoothstep)"""
    d = max(1.0, float(dist))
    if d > 1: b, a = butter(1, max(1000.0, 16000.0 / d) / (SR / 2), "low"); x = lfilter(b, a, x) / d
    if pan_from is None and pan_to is None:
        p = float(np.clip(pan, -1, 1)); th = (p + 1) * np.pi / 4
        gl, gr = (1.0, 1.0) if p == 0 else (np.sqrt(2) * np.cos(th), np.sqrt(2) * np.sin(th))
    else:
        a, b = (float(np.clip(pan if v is None else v, -1, 1)) for v in (pan_from, pan_to))
        s = smooth(np.linspace(0, 1, len(x))); th = (a + (b - a) * s + 1) * np.pi / 4
        gl, gr = np.sqrt(2) * np.cos(th), np.sqrt(2) * np.sin(th)
    return np.stack([x * gl, x * gr], 1)

def read(path):  # → mono float at SR via ffmpeg (as qa.py loads): any bit depth, float or EXTENSIBLE WAV, any rate
    ch = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "json", str(path)],
                                   capture_output=True, text=True, check=True).stdout)["streams"][0]["channels"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ar", str(SR), "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, int(ch)).mean(1, dtype=np.float64)

MANIFEST = "sfx-lib.json"   # written by `sfx lib`: which WAV in the folder is which built-in, and its sha256
_NOTED, _MAN, _PLAIN_BYTES, _IS_PLAIN = set(), {}, {}, {}
def note_once(msg):
    if msg not in _NOTED: _NOTED.add(msg); print(f"sfx: {msg}", file=sys.stderr)

def sha256(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def manifest(lib_dir):
    """the folder's sfx-lib.json as {name: sha256}, or None when there is none"""
    key = str(Path(lib_dir).resolve())
    if key not in _MAN:
        f = Path(lib_dir) / MANIFEST
        try: _MAN[key] = {k: v["sha256"] for k, v in json.loads(f.read_text())["sounds"].items()} if f.exists() else None
        except (ValueError, KeyError, TypeError, AttributeError): note_once(f"{f} is not a manifest `sfx lib` wrote: ignored"); _MAN[key] = None
    return _MAN[key]

def is_lib_copy(path, name):
    """is this --lib WAV the built-in `name` as `sfx lib` wrote it (so it may vary and take shaping)? By the folder's
    sfx-lib.json (listed, same sha256); a folder without one (an older `sfx lib`): by comparing its bytes with what `sfx lib`
    would write now, with a note. Never silent: a listed WAV that changed is named."""
    key = (str(Path(path).resolve()), name)
    if key in _IS_PLAIN: return _IS_PLAIN[key]
    m = manifest(Path(path).parent)
    if m is not None:
        same = name in m and sha256(path) == m[name]
        if name in m and not same:
            note_once(f"{path} changed since `sfx lib` wrote it ({MANIFEST}): used as a recording, without variants or shaping")
    else:
        note_once(f"{Path(path).parent} has no {MANIFEST}: its WAVs count as built-ins only where they match today's byte for byte "
                  f"(`bin/vh sfx lib {Path(path).parent}` writes the manifest)")
        if name not in _PLAIN_BYTES: _PLAIN_BYTES[name] = (np.clip(builtin(name), -1, 1) * 32767).astype("<i2").tobytes()
        try:
            with wave.open(str(path), "rb") as w:
                same = (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()) == (1, 2, SR, len(_PLAIN_BYTES[name]) // 2) \
                       and w.readframes(w.getnframes()) == _PLAIN_BYTES[name]
        except (wave.Error, EOFError, OSError): same = False
    _IS_PLAIN[key] = same
    return same

def file_for(name, lib_dir=None, root=None, t=None):
    """where an event's sound comes from: a Path (a recorded or your own file), or None (a built-in). --lib DIR/<name>.wav
    first (so "v2.1" is a name), unless `sfx lib` wrote it for that built-in (is_lib_copy); then a file of your own (relative
    to root, default the working directory; anything ffmpeg decodes); then a built-in"""
    at = f" (event at t={t})" if t is not None else ""
    if lib_dir and (Path(lib_dir) / f"{name}.wav").exists():
        f = Path(lib_dir) / f"{name}.wav"
        return None if name in LIB and is_lib_copy(f, name) else f
    p = Path(root or ".") / name
    if "/" in name or p.exists():
        p.exists() or sys.exit(f"sfx: no such file: {name}{at}")
        return p
    if name in LIB: return None
    sys.exit(f"sfx: unknown sound {name!r}: not in --lib, not a built-in ({', '.join(LIB)}), not a file")

def source(name, lib_dir=None, root=None, t=None):
    """an event's sound, mono float at SR, by name alone: the file (see file_for), else the plain built-in"""
    f = file_for(name, lib_dir, root, t)
    if f is None: return builtin(name)
    try: return read(f)
    except subprocess.CalledProcessError: sys.exit(f"sfx: ffmpeg cannot decode {name}")

def occurrences(events):
    """for each event, how many events of the same sound come before it in time (ties: list order)"""
    seen, out = {}, [0] * len(events)
    for k in sorted(range(len(events)), key=lambda k: (float(events[k].get("t", 0)), k)):
        n = str(events[k].get("sfx")); out[k] = seen.get(n, 0); seen[n] = out[k] + 1
    return out

def numbered(events):
    """copies of the events with their occurrence ("_occ") and the film's salt ("_salt"), so one event rendered alone gets
    the variant it gets in the list"""
    sl = salt(events)
    return [dict(e, _occ=o, _salt=sl) for e, o in zip(events, occurrences(events))]

def event_sound(e, occ=None, lib_dir=None, root=None, cache=None):
    """one event's sound before gain, pan and distance → (mono, landmark s, variant or None, shape or None)"""
    name = e["sfx"]; cache = {} if cache is None else cache; occ = e.get("_occ", 0) if occ is None else occ
    check(e)
    f = file_for(name, lib_dir, root, e.get("t"))
    if f is not None:
        shaped = [k for k in SHAPE + ("variant",) if k in e]
        if shaped: sys.exit(f"sfx: {name} at t={e.get('t')} is a file ({f}), used as recorded: variant and the shaping fields "
                            f"({', '.join(shaped)}) are for the built-ins only")
        if ("file", str(f)) not in cache:
            try: cache[("file", str(f))] = read(f)
            except subprocess.CalledProcessError: sys.exit(f"sfx: ffmpeg cannot decode {name}")
        return cache[("file", str(f))], LANDMARK.get(name, 0.0), None, None
    p = resolve(name, e, occ); key = (name, json.dumps(p, sort_keys=True))
    if key not in cache:
        copy = Path(lib_dir) / f"{name}.wav" if lib_dir else None   # file_for said: the plain `sfx lib` copy, if it exists
        x = read(copy) if p["plain"] and copy is not None and copy.exists() else render(name, p)   # (the plain one as it was read)
        cache[key] = (x, landmark(name, p, x))
    return cache[key][0], cache[key][1], p["variant"], shape(p)

def put(e, occ=None, lib_dir=None, root=None, cache=None):
    """one event as placed on the track → (first sample, (m, 2) samples, {"variant", "shape", "landmark"})"""
    x, lm, v, sh = event_sound(e, occ, lib_dir, root, cache)
    y = spatial(x * 10 ** (e.get("gain_db", 0) / 20), e.get("pan", 0), e.get("dist", 1), e.get("pan_from"), e.get("pan_to"))
    i = int(round((e["t"] - lm) * SR))
    if i < 0: y, i = y[-i:], 0
    return i, y, {"variant": v, "shape": sh, "landmark": lm}

def measure(x):
    """what a sound measures as: length (s within 20 dB of its loudest 10 ms), spectral centroid (Hz, energy-weighted over
    those frames), sweep (octaves per second: the slope of the frame centroid's log2 over the loud frames), peak (s)"""
    n, h = 1024, 240; x = np.asarray(x, dtype=np.float64)
    if len(x) < n: x = np.pad(x, (0, n - len(x)))
    fr = np.lib.stride_tricks.sliding_window_view(x, n)[::h] * np.hanning(n)
    P = np.abs(np.fft.rfft(fr, axis=1)) ** 2; f = np.fft.rfftfreq(n, 1 / SR); E = P.sum(1) + 1e-20
    cen = (P * f).sum(1) / E; db = 10 * np.log10(E); loud = db > db.max() - 20; tt = (np.arange(len(E)) * h + n / 2) / SR
    on = np.nonzero(loud)[0]; L = float((on[-1] - on[0]) * h / SR + .01) if len(on) else 0.0
    w = E[loud]; c = float((cen[loud] * w).sum() / w.sum()) if loud.any() else 0.0
    sl = float(np.polyfit(tt[loud], np.log2(np.maximum(cen[loud], 20)), 1, w=np.sqrt(w))[0]) if loud.sum() >= 3 else 0.0
    return {"len": L, "centroid": c, "sweep": sl, "peak": float(tt[int(np.argmax(E))])}

def audition(args):
    """bin/vh sfx audition <name|all> [n] [key=value …] [--walk] [--out FILE.wav] [--png]"""
    if not args or args[0] in ("-h", "--help"): sys.exit(__doc__)
    what = args[0]; rest = [a for a in args[1:]]
    png, walk = "--png" in rest, "--walk" in rest; rest = [a for a in rest if a not in ("--png", "--walk")]
    out = None
    if "--out" in rest: i = rest.index("--out"); out = rest[i + 1] if i + 1 < len(rest) else sys.exit("sfx audition: --out needs a file"); del rest[i:i + 2]
    n = 8; shp = {}
    for a in rest:
        if a.startswith("n=") and a[2:].isdigit(): n = int(a[2:])
        elif "=" in a:
            k, v = a.split("=", 1)
            if k not in SHAPE: sys.exit(f"sfx audition: {k}= is not a shaping parameter ({', '.join(SHAPE)})")
            try: shp[k] = v if k == "dir" else float(v)
            except ValueError: sys.exit(f"sfx audition: {k}={v}: not a number")
        elif a.isdigit(): n = int(a)
        else: sys.exit(f"sfx audition: what is {a!r}? (a count, key=value, --walk, --out FILE, --png)")
    if n < 1: sys.exit(f"sfx audition: {n} variants: give 1 or more")
    if what == "all":
        if shp: sys.exit("sfx audition all: plays each built-in's plain sound; shape one family at a time (sfx audition whoosh 8 dur=1.2)")
        evs = [{"sfx": k, "variant": 0} for k in LIB]
    elif what in LIB:
        if not SPEC[what].get("jitter"): evs = [{"sfx": what, **shp}]   # a signal: one sound
        # the family's spread: the first step of n different films' walks (variant b·1000); --walk: one film's n steps
        else: evs = [{"sfx": what, "variant": 1000 + k if walk else 1000 * (k + 1), **shp} for k in range(n)]
    else: sys.exit(f"sfx audition: {what!r} is not a built-in ({', '.join(LIB)}) or all")
    out = Path(out or f"sfx-audition-{what}.wav"); stem = out.with_suffix("")
    for e in evs: check(e)
    cache, at, placed, rows = {}, .3, [], []
    for e in evs:   # every variant is pinned, so where it lands does not change it
        x, lm, v, sh = event_sound(dict(e, t=0), 0, None, None, cache)
        e["t"] = round(at + lm, 4); i = int(round((e["t"] - lm) * SR)); placed.append((i, x)); m = measure(x)
        rows.append((e, v, sh, m, len(x) / SR)); at = (i + len(x)) / SR + .6
    track = np.zeros((int(round((at - .3) * SR)), 2))
    for (i, x), (e, *_r) in zip(placed, rows):
        y = spatial(x, e.get("pan", 0)); track[i:i + len(y)] += y
    write(out, track)
    lines = []
    for e, v, sh, m, d in rows:
        head = f"{e['sfx']:13s}" if what == "all" else f"v{v:<7d}" if v else "plain"
        par = DESCRIBE[e["sfx"]] if what == "all" or not sh else \
            " · ".join(f"{k} {val:+.2f}" if k in ("pitch", "bright", "span", "level") else f"{k} {val}" for k, val in sh.items())
        way = "↑ rising" if m["sweep"] > .5 else "↓ falling" if m["sweep"] < -.5 else "→ flat"
        lines.append(f"{head}  lands {e['t']:6.2f} s · {d:4.2f} s long · {par}  │  heard: {m['len']:.2f} s, centroid "
                     f"{m['centroid'] / 1000:5.2f} kHz, sweep {m['sweep']:+5.1f} oct/s {way}")
    Path(f"{stem}.txt").write_text("\n".join(lines) + "\n")
    with open(f"{stem}.json", "w") as fh: json.dump([{k: e[k] for k in ("t", "sfx", "variant", *SHAPE) if k in e} for e, *_r in rows], fh, indent=1)
    print("\n".join(lines))
    print(f"→ {out} ({len(rows)} sound{'s' * (len(rows) != 1)}, {len(track) / SR:.1f} s) · {stem}.txt · {stem}.json (the events: bin/vh qa {out} - {stem}.json)"
          + (f" · {draw(track.mean(1), rows, f'{stem}.png', what)}" if png else ""))

def draw(x, rows, path, what):
    """a spectrogram (log frequency 60 Hz – 18 kHz, dB) with each sound's label over it → path"""
    from PIL import Image, ImageDraw
    sys.path.insert(0, str(Path(__file__).resolve().parents[1])); import vhdraw as V
    n, h = 2048, 480; fr = np.lib.stride_tricks.sliding_window_view(np.pad(x, (n // 2, n // 2)), n)[::h] * np.hanning(n)
    S = 10 * np.log10(np.abs(np.fft.rfft(fr, axis=1)) ** 2 + 1e-12); f = np.fft.rfftfreq(n, 1 / SR)
    H, top, W = 260, 64, S.shape[0]; lf = np.linspace(np.log2(60), np.log2(18000), H)[::-1]
    img = np.empty((H, W))
    for c in range(W): img[:, c] = np.interp(lf, np.log2(np.maximum(f[1:], 1)), S[c, 1:])
    v = np.clip((img - (img.max() - 70)) / 70, 0, 1)
    rgb = (np.array(V.BG)[None, None] * (1 - v[..., None]) + np.array(V.INK)[None, None] * v[..., None]).astype(np.uint8)
    im = Image.new("RGB", (max(W + 140, 760), H + top + 8), V.BG); im.paste(Image.fromarray(rgb), (52, top)); d = ImageDraw.Draw(im)
    for hz in (100, 1000, 10000):
        y = top + int(round((np.log2(18000) - np.log2(hz)) / (np.log2(18000) - np.log2(60)) * (H - 1)))
        d.line([(46, y), (51, y)], fill=V.MUTED); d.text((4, y - 7), f"{hz // 1000}k" if hz >= 1000 else str(hz), font=V.font(12), fill=V.MUTED)
    d.text((52, 6), f"sfx audition {what}: spectrogram, log frequency 60 Hz – 18 kHz, 70 dB range", font=V.font(14, bold=True), fill=V.INK)
    for e, v_, sh, m, dd in rows:
        cx = 52 + int(e["t"] * SR / h); d.line([(cx, top - 4), (cx, top + H)], fill=V.RED, width=1)
        d.text((cx + 3, 28), e["sfx"] if what == "all" else f"v{v_}" if v_ else "plain", font=V.font(12, bold=True), fill=V.RED)
        d.text((cx + 3, 44), f"{m['centroid'] / 1000:.1f}k {m['sweep']:+.0f}", font=V.font(11), fill=V.MUTED)
    im.save(path, optimize=False); return path

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "lib":
        d = Path(sys.argv[2]); d.mkdir(parents=True, exist_ok=True)
        for name in LIB: write(d / f"{name}.wav", builtin(name))
        man = {"written_by": "bin/vh sfx lib", "sr": SR, "sounds": {n: {"file": f"{n}.wav", "sha256": sha256(d / f"{n}.wav")} for n in LIB}}
        (d / MANIFEST).write_text(json.dumps(man, indent=1) + "\n")
        print(f"{len(LIB)} SFX → {d}/ ({', '.join(LIB)}) + {MANIFEST}"); return
    if cmd == "audition": audition(sys.argv[2:]); return
    if cmd == "place":
        events = json.load(open(sys.argv[2])); out = sys.argv[3]
        if Path(side_path(out)).resolve() == Path(sys.argv[2]).resolve():
            sys.exit(f"sfx: the levels sidecar {side_path(out)} would overwrite the event list {sys.argv[2]}: name the output something else")
        dur = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else max(e["t"] for e in events) + 3
        lib_dir = Path(sys.argv[sys.argv.index("--lib") + 1]) if "--lib" in sys.argv else None
        for k, e in enumerate(events):
            if e.get("role") is not None and e["role"] not in CLASSES:
                sys.exit(f"sfx: event {k} ({e.get('sfx')} at t={e.get('t')}): role {e['role']!r} is not one of {', '.join(CLASSES)}")
            check(e, k)
        track = np.zeros((int(dur * SR), 2)); cache = {}; placed = []
        for e in numbered(events):
            i, x, info = put(e, None, lib_dir, None, cache)
            j = min(len(track), i + len(x)); track[i:j] += x[: max(0, j - i)]; placed.append((e, i, x[: max(0, j - i)], info))
        clip = int((np.abs(track) > 1).sum()); write(out, track)
        side = sidecar(out, placed)
        print(f"{len(events)} events → {out} ({dur:.2f}s, stereo) · levels → {side}" + (f"  ! {clip} samples clipped: lower gain_db" if clip else "")); return
    print(__doc__)

def side_path(out): return str(Path(out).with_suffix("")) + ".events.json"

def sidecar(out, placed):
    """<out>.events.json: each event's class, variant and shape, and its own level as placed (see the module docstring)"""
    import mix   # the meter and the class hints live with the mix profiles (tools/audio/mix.py)
    rows = []
    for k, (e, i, x, info) in enumerate(placed):
        c, why = mix.sfx_class(e)
        row = {"i": k, "t": e["t"], "sfx": e["sfx"], "class": c, "why": why, "start": round(i / SR, 4)}
        if info["variant"] is not None: row.update(variant=info["variant"], shape=info["shape"])
        if len(x):
            lv = mix.event_levels(x); lv["at"] += i / SR
            row.update({k2: round(v, 3) for k2, v in lv.items() if k2 in ("fast", "m400", "tp", "at", "len", "lf")})
        else: row["outside"] = True   # starts after the end of the track
        rows.append(row)
    path = side_path(out)
    with open(path, "w") as fh: json.dump({"track": Path(out).name, "sr": SR, "events": rows}, fh, ensure_ascii=False, indent=1)
    return path

if __name__ == "__main__":
    main()
