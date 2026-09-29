"""OpenVideoHarness intro film: score engine.

A project-local, extended copy of tools/audio/music.py (the shared engine is untouched).
score.json -> stereo 48 kHz / 16-bit WAV + <out>.beats.json

usage:
  uv run --with numpy --with scipy python audio/score_engine.py audio/score.json audio/music.wav [--stems DIR]

What it adds to the shared engine
  - stereo stems, per-event pan and reverb sends, two decorrelated noise-IR reverbs (hall, plate)
  - cinematic instruments: sub drone, detuned-saw pad with filter automation, 16th pulse ostinato,
    taiko / frame drum / metal / shaker, risers, reverse swells, impacts, one braam, celesta,
    an additive odd-harmonic lead (optionally Doppler-shifted)
  - a driving 16th synth bass (one phase-continuous oscillator), trailer snare, hi-hats, taiko ensemble,
    an FM bell hook and a sub drop under every impact
  - exact scheduling: layers per section plus events at "bar:beat" positions ("12:1.5" = bar 12,
    the eighth after beat 1) and "holds" (a held breath: drums out, bass and ostinato darken,
    pad and sub keep sounding)
  - kick sidechain on the synth bass and ostinato only, 2 ms / 5 ms edge fades on every placed sound,
    a look-ahead limiter, loudness targeting, and a beat map that lists every placed hit at its landing
    time (transient onset, or the peak of a swell / riser)
Everything is seeded: the same score renders the same samples.

Score schema (see score.json)
  bpm, bars, meters{bar: beats} (default 4/4), seed, chords[bar] -> voicings{name: [note names]}
  sections: [{name, bars: [first, last], layers: [{inst, gain, bars?, from?, hit?, ...}]}]
  events:   [{at, do, gain, label?, repeat?, every?, ...}]      (do = an EVENTS key below)
  holds:    [[from, to], ...]                                    (held breath, never silence)
  reverb:   {hall|plate: {rt60, return, seeds}},  master: {lufs, ceiling_db, true_peak_db, fade}
"""
import json
import math
import sys
import wave
from pathlib import Path

import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

SR = 48000
TAU = 2 * np.pi
PITCH = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


# ---------- pitch, time, level ----------
def midi(name):
    """'Bb2' -> 46 (C4 = 60)."""
    pc, rest = PITCH[name[0]], name[1:]
    while rest[0] in "#b":
        pc, rest = pc + (1 if rest[0] == "#" else -1), rest[1:]
    return 12 * (int(rest) + 1) + pc


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def hz(name):
    return mtof(midi(name))


def root_pc(chord):
    """'Bbmaj7' -> 10, 'Dm9' -> 2."""
    return (PITCH[chord[0]] + {"b": -1, "#": 1}.get(chord[1:2], 0)) % 12


def db(x):
    return 10 ** (x / 20)


def secs(n):
    return np.arange(n) / SR


def norm(x):
    peak = np.max(np.abs(x))
    return x / peak if peak > 0 else x


def fade(n, attack, release=0.0):
    """Raised-cosine attack and release, n samples long."""
    e = np.ones(n)
    a, r = min(n, int(attack * SR)), min(n, int(release * SR))
    if a:
        e[:a] = 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if r:
        e[n - r:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(r) / r)
    return e


def gate_from(n, t_on, ramp=0.006):
    """0 before t_on, a short raised-cosine ramp, then 1."""
    t = secs(n)
    k = np.clip((t - t_on) / ramp, 0, 1)
    return 0.5 - 0.5 * np.cos(np.pi * k)


def pan2(x, pan=0.0):
    """Mono -> stereo (constant power, centre = unity per side); stereo input is balanced instead."""
    if x.ndim == 2:
        return x * np.array([[min(1.0, 1 - pan)], [min(1.0, 1 + pan)]])
    a = (np.asarray(pan) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)]) * np.sqrt(2)


# ---------- oscillators and filters ----------
def saw(freq, n, phase=0.0):
    """Band-limited (polyBLEP) sawtooth; freq is a scalar or one value per sample."""
    dt = np.broadcast_to(np.asarray(freq, dtype=float) / SR, (n,))
    p = (phase + np.cumsum(dt)) % 1.0
    y = 2.0 * p - 1.0
    lo, hi = p < dt, p > 1.0 - dt
    a = p[lo] / dt[lo]
    y[lo] -= a + a - a * a - 1.0
    b = (p[hi] - 1.0) / dt[hi]
    y[hi] -= b * b + b + b + 1.0
    return y


def lowpass(x, fc, order=2):
    return sosfilt(butter(order, min(fc, 0.45 * SR), "low", fs=SR, output="sos"), x, axis=-1)


def highpass(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x, axis=-1)


def bandpass(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, min(hi, 0.45 * SR)], "band", fs=SR, output="sos"), x, axis=-1)


def peaking(x, f0, gain_db, q=0.9):
    """RBJ peaking EQ (used to carve the 150-300 Hz mud out of the pad)."""
    w = 2 * math.pi * f0 / SR
    a, alpha = 10 ** (gain_db / 40), math.sin(w) / (2 * q)
    b = [1 + alpha * a, -2 * math.cos(w), 1 - alpha * a]
    d = [1 + alpha / a, -2 * math.cos(w), 1 - alpha / a]
    return sosfilt(np.array([[*(v / d[0] for v in b), *(v / d[0] for v in d)]]), x, axis=-1)


def _biquad_lp(fc, q):
    w = 2 * math.pi * fc / SR
    c, alpha = math.cos(w), math.sin(w) / (2 * q)
    b0, a0 = (1 - c) / 2, 1 + alpha
    return [b0 / a0, 2 * b0 / a0, b0 / a0, 1.0, -2 * c / a0, (1 - alpha) / a0]


def sweep_lowpass(x, fc, res=1.0, block=64):
    """4-pole low-pass whose cutoff follows fc (Hz, one value per sample), updated every block."""
    x = np.atleast_2d(x)
    y = np.empty_like(x)
    zi = np.zeros((2, x.shape[0], 2))
    for s in range(0, x.shape[1], block):
        f = min(max(float(fc[s]), 20.0), 0.45 * SR)
        sos = np.array([_biquad_lp(f, 0.5412), _biquad_lp(f, 1.3066 * res)])
        y[:, s:s + block], zi = sosfilt(sos, x[:, s:s + block], axis=-1, zi=zi)
    return y


def noise_ir(rt60, seed, predelay=0.02, split=2500.0):
    """Synthetic room: exponentially decaying noise, highs dying faster than lows. Unit energy."""
    rng = np.random.default_rng(seed)
    n = int(rt60 * SR)
    t = secs(n)
    noise = rng.standard_normal(n)
    low = lowpass(noise, split)
    tau = rt60 / 6.91                                   # amplitude time constant for -60 dB at rt60
    ir = low * np.exp(-t / tau) + (noise - low) * np.exp(-t / (0.4 * tau))
    ir *= 1 - np.exp(-t / 0.008)                        # diffuse build-up instead of a click
    ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
    return ir / np.sqrt(np.sum(ir ** 2))


# ---------- instruments: each returns a peak-normalised mono (n,) or stereo (2, n) array ----------
def spark(rng):
    n = int(2.5 * SR)
    t = secs(n)
    f = hz("A6")
    x = np.sin(TAU * f * t) * np.exp(-t / 0.5) + 0.25 * np.sin(TAU * 2.76 * f * t) * np.exp(-t / 0.1)
    return norm(x * fade(n, 0.002))


def tick(freq, rng, click=0.3, tau=0.018):
    n = int(0.15 * SR)
    t = secs(n)
    x = np.sin(TAU * freq * t) * np.exp(-t / tau)
    x += click * highpass(rng.standard_normal(n), 3000) * np.exp(-t / 0.0015)
    return norm(x * fade(n, 0.0008))


def drone(freqs, dur, swell=0.25):
    """Sub drone: sines with a touch of 2nd harmonic and slow, deterministic breathing."""
    n = int(dur * SR)
    t = secs(n)
    x = np.zeros(n)
    for i, f in enumerate(freqs):
        breath = 1 + swell * np.sin(TAU * (0.09 + 0.05 * i) * t + 1.7 * i)
        x += (np.sin(TAU * f * t) + 0.2 * np.sin(TAU * 2 * f * t)) * breath / (i + 1)
    return norm(x)


def pad_chord(notes, n, rng, voices=5, cents=14.0, width=0.7):
    """Detuned saw stack, each voice at its own place in the stereo field."""
    out = np.zeros((2, n))
    for m in notes:
        for v in range(voices):
            d = 2 * v / (voices - 1) - 1                # -1 .. 1 across the stack
            x = saw(mtof(m + d * cents / 100), n, rng.random())
            out += pan2(x, width * d * (1 if m % 2 else -1))
    return out / (len(notes) * voices)


def pulse(freq, cutoff, rng, drive=2.2, dur=0.3):
    """One 16th of the ostinato: two detuned saws (L/R), a filter 'pluck', tanh drive."""
    n = int(dur * SR)
    t = secs(n)
    x = np.stack([saw(freq * 2 ** (-7 / 1200), n, rng.random()), saw(freq * 2 ** (7 / 1200), n, rng.random())])
    body = lowpass(x, cutoff) * np.exp(-t / 0.14) + lowpass(x, min(cutoff * 3.5, 16000)) * np.exp(-t / 0.035)
    y = np.tanh(drive * body) / np.tanh(drive)
    return highpass(y * fade(n, 0.0015, 0.04), 90)


def taiko(f0=70.0, f1=40.0, decay=0.9, rng=None):
    """Pitch-enveloped sine (f0 -> f1) + skin noise + stick click."""
    n = int(decay * 1.6 * SR)
    t = secs(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.06)
    ph = TAU * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / (decay / 3)) + 0.25 * np.sin(1.52 * ph) * np.exp(-t / 0.12)
    skin = bandpass(rng.standard_normal(n), 90, 500) * np.exp(-t / 0.08)
    click = highpass(rng.standard_normal(n), 1800) * np.exp(-t / 0.003)
    return norm(highpass((body + 0.45 * skin + 0.25 * click) * fade(n, 0.0005), 30))


_ROOM = {}


def frame_drum(rng):
    """Band-passed noise head + a short tuned body, through a small room."""
    if "ir" not in _ROOM:
        _ROOM["ir"] = noise_ir(0.35, 404, predelay=0.004)
    n = int(0.5 * SR)
    t = secs(n)
    head = bandpass(rng.standard_normal(n), 220, 2400) * np.exp(-t / 0.05)
    f = 175 + 60 * np.exp(-t / 0.02)
    body = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.09)
    x = (head + 0.8 * body) * fade(n, 0.0005)
    return norm(x + 0.3 * fftconvolve(x, _ROOM["ir"])[:n])


def metal(rng, base=380.0, decay=0.6):
    """Inharmonic plate: partials that do not line up, each dying at its own rate."""
    n = int(decay * 2.5 * SR)
    t = secs(n)
    x = np.zeros(n)
    for i, r in enumerate((1.0, 1.47, 1.98, 2.56, 3.21, 4.03, 5.17)):
        x += np.sin(TAU * base * r * t + TAU * rng.random()) * np.exp(-t * (1 + 0.6 * i) / decay) / (1 + 0.35 * i)
    x += 0.5 * bandpass(rng.standard_normal(n), 2000, 7000) * np.exp(-t / 0.004)
    return norm(lowpass(x * fade(n, 0.0005), 7000))


def clack(rng):
    """Gate approval: a short, high, woody-metal clack."""
    ring = metal(rng, base=820.0, decay=0.09)
    n = len(ring)
    t = secs(n)
    x = ring + 0.6 * bandpass(rng.standard_normal(n), 1200, 5000) * np.exp(-t / 0.0015)
    return norm(x * fade(n, 0.0005))


def shaker(rng):
    n = int(0.09 * SR)
    t = secs(n)
    hats = bandpass(rng.standard_normal(n), 6000, 11000)
    return norm(hats * np.exp(-t / 0.02) * fade(n, 0.001))


def riser(dur, rng, lo=250.0, hi=8000.0, tone=("D3", "D6")):
    """Noise through an opening filter + a rising tone; loudest on its last sample."""
    n = int(dur * SR)
    t = secs(n)
    k = t / dur
    air = sweep_lowpass(rng.standard_normal((2, n)), lo * (hi / lo) ** (k ** 1.6), block=256)
    air = highpass(air, 150) * k ** 2.4
    f = hz(tone[0]) * (hz(tone[1]) / hz(tone[0])) ** (k ** 2)
    whine = np.sin(TAU * np.cumsum(f) / SR) * k ** 3
    suck = 1 + 0.5 * np.exp(-(dur - t) / 0.08)          # the last ~80 ms leans in: the peak is the last sample
    return norm((air + 0.35 * pan2(whine)) * suck * fade(n, 0.0, 0.005))


def reverse_swell(notes, dur, rng, irs):
    """A chord's reverb tail played backwards, shaped so that its peak is the last sample."""
    m = int(0.25 * SR)
    src = lowpass(pad_chord(notes, m, rng, voices=3, cents=10), 3500) * np.exp(-secs(m) / 0.04)
    tails = [ir[np.argmax(np.abs(ir) > 0):] for ir in irs]        # no pre-delay: the tail starts at once
    wet = np.stack([fftconvolve(src[c], tails[c]) for c in (0, 1)])
    wet[:, :m] += 0.6 * src                              # reversed dry attack lands exactly on the target
    rev = wet[:, ::-1]
    n = int(dur * SR)
    rev = rev[:, -n:] if rev.shape[1] >= n else np.pad(rev, ((0, 0), (n - rev.shape[1], 0)))
    grow = np.linspace(0, 1, n) ** 3
    return norm(rev * grow * fade(n, 0.0, 0.004))


IMPACTS = {  # boom f0 -> f1 (Hz), boom decay (s), noise low-pass (Hz), noise amount
    "soft": dict(f0=65, f1=36, tau=0.5, lp=900, crack=0.2, length=3.0),
    "big": dict(f0=100, f1=34, tau=0.7, lp=3500, crack=0.45, length=4.0),
    "final": dict(f0=90, f1=34, tau=0.9, lp=2500, crack=0.4, length=5.0),
}


def impact(size, rng):
    """Sub boom with a pitch drop (mono) + a stereo noise burst."""
    p = IMPACTS[size]
    n = int(p["length"] * SR)
    t = secs(n)
    f = p["f1"] + (p["f0"] - p["f1"]) * np.exp(-t / 0.09)
    boom = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / p["tau"])
    crack = lowpass(rng.standard_normal((2, n)), p["lp"]) * np.exp(-t / 0.14)
    snap = highpass(rng.standard_normal((2, n)), 1200) * np.exp(-t / 0.006)
    x = pan2(boom) + p["crack"] * (crack + 0.6 * snap)
    return norm(x * fade(n, 0.0005))


def braam(rng, dur=5.0):
    """The one braam: detuned saws on D1 D2 F2 A2, a brassy blat, filter 200 -> 2500 -> ~250 Hz."""
    n = int(dur * SR)
    t = secs(n)
    blat = 2 ** (-35 * np.exp(-t / 0.07) / 1200)       # starts 35 cents flat, like a brass attack
    stack = np.zeros((2, n))
    for note, g, width in (("D1", 0.4, 0.0), ("D2", 1.0, 0.3), ("F2", 0.45, 0.6), ("A2", 0.7, 0.8)):
        life = np.exp(-t / 0.6) if note == "D1" else 1.0      # the sub octave is a burst, not a drone
        for d in (-1.0, -0.33, 0.33, 1.0):
            stack += g * life * pan2(saw(hz(note) * 2 ** (d * 12 / 1200) * blat, n, rng.random()), width * d)
    opening = (1 - np.exp(-t / 0.03)) * np.exp(-t / 1.8)
    cutoff = 200 * (2500 / 200) ** (opening / opening.max())
    y = sweep_lowpass(stack, cutoff, res=1.4, block=32)
    y = np.tanh(4.0 * norm(y))                           # dense, brassy saturation
    amp = fade(n, 0.02, 1.0) * (0.35 + 0.65 * np.exp(-t / 1.8))
    return norm(highpass(y * amp, 30))


def celesta(freq, rng):
    """Celesta / music-box tine: a pure fundamental, a weak octave, two short inharmonic partials."""
    n = int(1.8 * SR)
    t = secs(n)
    x = np.zeros(n)
    for r, a, tau in ((1.0, 1.0, 0.9), (2.0, 0.2, 0.35), (4.16, 0.18, 0.07), (6.9, 0.06, 0.03)):
        x += a * np.sin(TAU * r * freq * t) * np.exp(-t / tau)
    x += 0.05 * highpass(rng.standard_normal(n), 4000) * np.exp(-t / 0.002)
    return norm(x * fade(n, 0.001))


def lead(freq, dur, odd=(1, 3, 5, 7), enter=None, release=0.15, spotlight=0.0):
    """Additive lead: the Fourier series of a square wave. enter = {k: seconds} brings harmonic k in late;
    spotlight = s > 0 lets harmonic k arrive at s x the fundamental's level and settle to 1/k over ~0.3 s,
    so each new term is heard arriving."""
    n = int(dur * SR)
    t = secs(n)
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    ph = TAU * np.cumsum(f) / SR
    gates = {}
    for k in odd:
        on = (enter or {}).get(k, 0.0)
        boost = max(0.0, spotlight * k - 1)
        gates[k] = gate_from(n, on) * (1 + boost * np.exp(-np.maximum(t - on, 0) / 0.3))
    lead = sum(np.sin(k * ph) / k * gates[k] for k in odd)
    return lead * fade(n, 0.012, release) / 1.2


def stab(notes, dur, rng, bright=3200.0, tau=0.4):
    """Short chord hit (gate approvals, PASS, the title chord)."""
    n = int(dur * SR)
    t = secs(n)
    x = pad_chord(notes, n, rng, voices=3, cents=9, width=0.6)
    body = lowpass(x, bright) * np.exp(-t / tau) + 0.5 * lowpass(x, bright * 2.5) * np.exp(-t / 0.03)
    return norm(body * fade(n, 0.002, 0.1))


def fail_hit(notes, rng):
    """Low minor-2nd cluster, saturated, with a thud under it."""
    n = int(0.9 * SR)
    t = secs(n)
    x = pad_chord(notes, n, rng, voices=3, cents=6, width=0.3)
    x = np.tanh(3 * norm(lowpass(x, 700))) * np.exp(-t / 0.22) * fade(n, 0.002)
    thud = pan2(taiko(60, 38, 0.5, rng))[:, :n]
    return norm(x + 0.7 * np.pad(thud, ((0, 0), (0, n - thud.shape[1]))))


def synth_bass_line(freq, cutoff, trig_tau, accent, rng, drive=1.8):
    """Driving synth bass rendered as ONE continuous oscillator (no gaps between notes):
    each 16th re-opens the filter and lifts the level; trig_tau = seconds since the last 16th."""
    ph = TAU * np.cumsum(freq) / SR
    bass = saw(freq, len(freq), rng.random()) + 0.6 * np.sin(ph)
    attack = np.minimum(1.0, trig_tau / 0.003)          # 3 ms attack: the envelope never jumps
    snap = np.exp(-trig_tau / 0.03) * attack
    body = 0.6 + 0.4 * np.exp(-trig_tau / 0.07) * attack
    y = sweep_lowpass(bass, np.minimum(cutoff * 3, 12000), block=128)[0] * snap
    y += sweep_lowpass(bass, cutoff, block=128)[0] * body
    y = np.tanh(drive * accent * y) / np.tanh(drive)
    return highpass(y, 35)


def hat(rng, open_=False):
    """Closed / open hi-hat: six inharmonic square waves (the 808 recipe) band-passed high."""
    n = int((0.3 if open_ else 0.07) * SR)
    t = secs(n)
    squares = sum(np.sign(np.sin(TAU * 317 * r * t + TAU * rng.random())) for r in (2.0, 3.0, 4.16, 5.43, 6.79, 8.21))
    air = 0.3 * highpass(rng.standard_normal(n), 8000)
    hats = bandpass(squares, 7000, 14000) + air
    return norm(hats * np.exp(-t / (0.1 if open_ else 0.02)) * fade(n, 0.0005))


def snare(rng):
    """Trailer snare: band-passed noise, a pitched body and a crack, through a small room."""
    if "ir" not in _ROOM:
        _ROOM["ir"] = noise_ir(0.35, 404, predelay=0.004)
    n = int(0.7 * SR)
    t = secs(n)
    noise = bandpass(rng.standard_normal(n), 900, 9000) * np.exp(-t / 0.13)
    f = 185 + 70 * np.exp(-t / 0.015)
    body = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.07)
    crack = highpass(rng.standard_normal(n), 3000) * np.exp(-t / 0.004)
    x = (0.8 * noise + body + 0.4 * crack) * fade(n, 0.0005)
    return norm(x + 0.35 * fftconvolve(x, _ROOM["ir"])[:n])


def bell(freq, rng):
    """FM bell: a bright strike that mellows as the modulation index decays."""
    n = int(3.0 * SR)
    t = secs(n)
    index = 2.5 * np.exp(-t / 0.35)
    x = np.sin(TAU * freq * t + index * np.sin(TAU * 3.5 * freq * t)) * np.exp(-t / 1.1)
    return norm(x * fade(n, 0.001))


def sub_drop(dur=1.8, f0=70.0, f1=30.0):
    """Trailer sub drop: a sine falling f0 -> f1 under an impact."""
    n = int(dur * SR)
    t = secs(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.35)
    return np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.8) * fade(n, 0.003, 0.3)


def vowel(freq, rng, dur=0.35, formants=((800, 1.0), (1150, 0.6), (2900, 0.25))):
    """A tiny sung "ah": a saw scooping up 60 cents, through three formant band-passes."""
    n = int(dur * SR)
    t = secs(n)
    src = saw(freq * 2 ** (-60 * np.exp(-t / 0.05) / 1200), n, rng.random())
    x = sum(g * bandpass(src, fc / 1.12, fc * 1.12) for fc, g in formants)
    return norm(x * (0.7 + 0.3 * np.exp(-t / 0.15)) * fade(n, 0.008, 0.08))


def pop_swish(rng, dur=0.45):
    """SFX demo: a pitched pop, then a short band-passed swish."""
    n = int(dur * SR)
    t = secs(n)
    pop = np.sin(TAU * np.cumsum(120 + 900 * np.exp(-t / 0.02)) / SR) * np.exp(-t / 0.03)
    swish = bandpass(rng.standard_normal((2, n)), 1500, 8000) * np.sin(np.pi * np.clip((t - 0.04) / 0.36, 0, 1)) ** 2
    return norm(pan2(pop) + 0.5 * swish * np.array([[1.0], [0.6]]))


def sparkle(rng, dur=1.4, count=48, notes=("D6", "F6", "A6", "C7", "D7", "F7")):
    """A burst of tiny bell points rippling out from t = 0 (the first point is the loudest)."""
    n = int(dur * SR)
    out = np.zeros((2, n))
    m = int(0.12 * SR)
    tm = secs(m)
    for i in range(count):
        at = 0.0 if i == 0 else 0.8 * dur * (i / count) ** 1.6 + rng.uniform(0, 0.03)
        f = hz(notes[rng.integers(len(notes))])
        blip = np.sin(TAU * f * tm) * np.exp(-tm / 0.05) * fade(m, 0.001, 0.01) * (1.0 if i == 0 else 0.5 * (1 - i / count) + 0.15)
        j = int(at * SR)
        out[:, j:j + m] += pan2(blip, 0.0 if i == 0 else rng.uniform(-0.8, 0.8))[:, : n - j]
    return norm(out)


# ---------- mixer ----------
class Mixer:
    """Stereo stems, two reverb sends, a kick sidechain; everything placed by sample index."""

    DUCKED = ("pulse", "bass")          # the kick sidechain touches only the synth bass and the ostinato

    def __init__(self, n, reverb):
        self.n = n
        self.stems = {}
        self.sends = {name: np.zeros((2, n)) for name in reverb}
        self.reverb = reverb
        self.irs = {name: [noise_ir(r["rt60"], s) for s in r["seeds"]] for name, r in reverb.items()}
        self.duck_env = np.ones(n)
        self.log = []                   # (start, end, stem) of every placed sound, for the click check

    def put(self, stem, x, t, gain_db=0.0, pan=0.0, send=0.0, verb="hall"):
        """Add x so that its first sample plays at t seconds."""
        x = pan2(np.asarray(x, dtype=float), pan) * db(gain_db)
        x = x * fade(x.shape[1], 0.002, 0.005)          # no sound starts or ends on a step
        i = int(round(t * SR))
        if i < 0:
            x, i = x[:, -i:], 0
        j = min(self.n, i + x.shape[1])
        if j <= i:
            return
        self.stems.setdefault(stem, np.zeros((2, self.n)))[:, i:j] += x[:, :j - i]
        self.log.append((round(i / SR, 5), round(j / SR, 5), stem))
        if send:
            self.sends[verb][:, i:j] += send * x[:, :j - i]

    def duck(self, t, depth, release):
        """Pull the ducked stems down by `depth` at t, recovering with time constant `release`."""
        i = int(round(t * SR))
        m = min(self.n - i, int(release * 5 * SR))
        if m <= 0:
            return
        s = secs(m)
        g = 1 - depth * np.minimum(1, s / 0.004) * np.exp(-s / release)
        self.duck_env[i:i + m] = np.minimum(self.duck_env[i:i + m], g)

    def bounce(self):
        """Stems (ducked) + reverb returns -> stereo mix."""
        out = np.zeros((2, self.n))
        for name, x in self.stems.items():
            out += x * self.duck_env if name in self.DUCKED else x
        for name, send in self.sends.items():
            send = lowpass(highpass(send, 180), 9000)          # keep the lows dry and mono
            wet = np.stack([fftconvolve(send[c], self.irs[name][c])[: self.n] for c in (0, 1)])
            out += self.reverb[name]["return"] * wet
        return out


# ---------- arrangement ----------
class Arrangement:
    def __init__(self, score):
        self.score = score
        self.bpm = float(score["bpm"])
        self.beat = 60.0 / self.bpm
        self.s16 = self.beat / 4
        meters = {int(k): v for k, v in score.get("meters", {}).items()}       # e.g. {"11": 6}: bar 11 is 6/4
        self.bar_beats = [meters.get(k, 4) for k in range(1, score["bars"] + 1)]
        self.starts = np.concatenate([[0.0], np.cumsum(self.bar_beats)]) * self.beat
        self.n = int(round(self.starts[-1] * SR))
        self.mix = Mixer(self.n, score["reverb"])
        self.hits = []
        self.pad_segments, self.sub_segments, self.cutoff_ramps, self.bass_layers = [], [], [], []
        self.holds = [(self.at(a), self.at(b)) for a, b in score.get("holds", [])]

    # time and harmony
    def at(self, pos):
        """'12:1.5' -> seconds (bar 12, beat 1.5). Numbers pass through as seconds."""
        if isinstance(pos, (int, float)):
            return float(pos)
        bar, beat = pos.split(":")
        return self.bar_start(int(bar)) + (float(beat) - 1) * self.beat

    def bar_start(self, k):
        return float(self.starts[k - 1])

    def chord(self, k):
        return self.score["chords"][k - 1]

    def voicing(self, name):
        return [midi(x) for x in self.score["voicings"][name]]

    def sub_root(self, k):
        m = 24 + root_pc(self.chord(k))              # D1 .. C#2 (37-69 Hz)
        return m + 12 if m < 26 else m

    def pulse_root(self, k):
        m = 36 + root_pc(self.chord(k))              # A2 .. G#3
        while m < 45:
            m += 12
        return m

    def hit(self, t, what):
        self.hits.append({"t": round(t, 4), "what": what})

    def rng(self, *key):
        return np.random.default_rng([self.score["seed"], *key])

    # layer helpers
    def span(self, layer, first, last):
        first, last = layer.get("bars", [first, last])
        t0 = self.bar_start(first)
        if "from" in layer:
            t0 = max(t0, self.at(layer["from"]))
        t1 = self.bar_start(last + 1)
        if "until" in layer:
            t1 = min(t1, self.at(layer["until"]))
        return t0, t1, range(first, last + 1)

    def steps(self, pattern, bars, t0, t1, drums=False):
        """Yield (bar, step, symbol, time) for every non-rest 16th of a 16-character pattern in [t0, t1).
        drums=True leaves out the steps inside a hold (the held breath)."""
        for k in bars:
            for i in range(4 * self.bar_beats[k - 1]):             # a pattern repeats if the bar is longer
                sym = pattern[i % len(pattern)]
                t = self.bar_start(k) + i * self.s16
                if sym != "." and t0 - 1e-9 <= t < t1 - 1e-9 and not (drums and self.hold_progress(t) is not None):
                    yield k, i, sym, t

    def hold_progress(self, t):
        """0..1 through the hold that contains t, or None."""
        for a, b in self.holds:
            if a - 1e-9 <= t < b - 1e-9:
                return (t - a) / (b - a)
        return None

    def darken(self, t):
        """Cutoff factor for bass and ostinato: sweeps down across a hold, 1 elsewhere."""
        u = self.hold_progress(t)
        return 1.0 if u is None else max(0.12, (1 - 0.85 * u) ** 2)

    @staticmethod
    def ramp(layer, key, t, t0, t1, log=False):
        v = layer[key]
        if not isinstance(v, list):
            return v
        u = np.clip((t - t0) / max(t1 - t0, 1e-9), 0, 1)
        return v[0] * (v[1] / v[0]) ** u if log else v[0] + (v[1] - v[0]) * u

    # render
    def render(self):
        score = self.score
        for si, sec in enumerate(score["sections"]):
            for li, layer in enumerate(sec["layers"]):
                t0, t1, bars = self.span(layer, *sec["bars"])
                LAYERS[layer["inst"]](self, layer, t0, t1, bars, self.rng(si, li))
                if "hit" in layer:
                    self.hit(t0, layer["hit"])
        for ei, ev in enumerate(score["events"]):
            rng = self.rng(1000, ei)
            for i in range(ev.get("repeat", 1)):
                one = dict(ev)
                if "notes" in ev:
                    one["note"] = ev["notes"][i]
                t = self.at(ev["at"]) + i * ev.get("every", 1) * self.beat
                name = ev.get("label", ev["do"])
                if "labels" in ev:                       # explicit label per repeat
                    one["label"] = ev["labels"][i]
                else:
                    one["label"] = f"{name}:{i + 1}" if ev.get("repeat", 1) > 1 else name
                EVENTS[ev["do"]](self, one, t, rng)
        self.render_pad()
        self.render_sub()
        self.render_bass()
        return self.mix.bounce()

    def render_pad(self):
        """One continuous pad track: chord segments, a high-pass, then the automated low-pass."""
        track = np.zeros((2, self.n))
        rng = self.rng(2000)
        for t0, t1, notes, gain, attack in self.pad_segments:
            i, n = int(round(t0 * SR)), int((t1 - t0 + 0.8) * SR)
            x = pad_chord(notes, n, rng) * fade(n, attack, 0.8) * db(gain)
            j = min(self.n, i + n)
            track[:, i:j] += x[:, : j - i]
        t = secs(self.n)
        fc = np.full(self.n, 800.0)
        for t0, t1, c0, c1 in self.cutoff_ramps:
            i, j = int(round(t0 * SR)), int(round(t1 * SR))
            fc[i:j] = c0 * (c1 / c0) ** np.linspace(0, 1, j - i)
        fc = uniform_filter1d(fc, int(0.3 * SR)) * (1 + 0.12 * np.sin(TAU * 0.06 * t))   # slow drift
        track = peaking(highpass(track, 100), 220, -3.5)                 # leave < 100 Hz to the sub, carve mud
        track = sweep_lowpass(track, fc, block=128)
        self.mix.put("pad", track, 0.0, send=0.3)

    def render_bass(self):
        """The 16th synth bass: per-sample pitch, cutoff, level and trigger clock from every bass layer."""
        n = self.n
        f, cut, amp = np.full(n, hz("D2")), np.full(n, 400.0), np.zeros(n)
        trig_level = np.zeros(n)
        for L, t0, t1, bars in self.bass_layers:
            for k in bars:
                a, b = max(t0, self.bar_start(k)), min(t1, self.bar_start(k + 1))
                i, j = int(round(a * SR)), int(round(b * SR))
                if j <= i:
                    continue
                tt = a + secs(j - i)
                f[i:j] = mtof(self.sub_root(k) + 12)
                coarse = [self.ramp(L, "cutoff", x, t0, t1, log=True) * self.darken(x) for x in tt[::64]]
                cut[i:j] = np.repeat(coarse, 64)[: j - i]
                amp[i:j] = db(np.interp(tt, [t0, t1], np.broadcast_to(L["gain"], 2)))
            for k, step, sym, t in self.steps(L["pattern"], bars, t0, t1):
                trig_level[int(round(t * SR))] = 1.0 if sym == "X" else 0.8
        idx = np.arange(n)
        last = np.maximum.accumulate(np.where(trig_level > 0, idx, 0))
        tau = np.where(trig_level[last] > 0, (idx - last) / SR, 10.0)
        accent = uniform_filter1d(np.where(trig_level[last] > 0, trig_level[last], 0.8), int(0.003 * SR))
        cut = uniform_filter1d(cut, int(0.005 * SR))
        amp = uniform_filter1d(amp, int(0.005 * SR))                    # 5 ms edges, no gap between layers
        live = np.flatnonzero(amp > 1e-6)
        if len(live) == 0:
            return
        i, j = live[0], live[-1] + 1
        line = synth_bass_line(f[i:j], cut[i:j], tau[i:j], accent[i:j], self.rng(3000))
        track = np.zeros(n)
        track[i:j] = line * amp[i:j]
        self.mix.put("bass", track, 0.0, send=0.03, verb="plate")

    def render_sub(self):
        """Sub bass as one phase-continuous oscillator that follows the chord roots."""
        f = np.full(self.n, hz("D1"))
        amp = np.zeros(self.n)
        for t0, t1, freq, gain, decay, origin in self.sub_segments:
            i, j = int(round(t0 * SR)), int(round(t1 * SR))
            f[i:j] = freq
            amp[i:j] = db(gain) * (np.exp(-(secs(j - i) + t0 - origin) / decay) if decay else 1.0)
        f = uniform_filter1d(f, int(0.01 * SR))
        amp = uniform_filter1d(amp, int(0.03 * SR)) * (1 + 0.15 * np.sin(TAU * 0.11 * secs(self.n)))
        ph = TAU * np.cumsum(f) / SR
        bass = np.sin(ph) + 0.25 * np.sin(2 * ph)
        self.mix.put("sub", np.tanh(1.3 * bass) / np.tanh(1.3) * amp, 0.0)


# ---------- layers: (arrangement, layer, t0, t1, bars, rng) ----------
def layer_drone(A, L, t0, t1, bars, rng):
    x = drone([hz(nm) for nm in L["notes"]], t1 - t0 + 1.0, L.get("swell", 0.25))
    x = x * fade(len(x), L.get("fade_in", 2.0), L.get("fade_out", 1.0))
    A.mix.put("drone", x, t0, L["gain"])


def layer_pad(A, L, t0, t1, bars, rng):
    A.cutoff_ramps.append((t0, t1, *(L["cutoff"] if isinstance(L["cutoff"], list) else [L["cutoff"]] * 2)))
    first = True
    for k in bars:
        start = max(t0, A.bar_start(k))
        prev = A.pad_segments[-1] if A.pad_segments else None
        if prev and abs(prev[1] - start) < 1e-6 and prev[2] == A.voicing(A.chord(k)) and not first:
            A.pad_segments[-1] = (prev[0], A.bar_start(k + 1), *prev[2:])     # same chord: extend
        else:
            attack = L.get("attack", 0.15) if first else 0.15
            A.pad_segments.append((start, A.bar_start(k + 1), A.voicing(A.chord(k)), L["gain"], attack))
        first = False


def layer_sub(A, L, t0, t1, bars, rng):
    for k in bars:
        start = max(t0, A.bar_start(k))
        A.sub_segments.append((start, A.bar_start(k + 1), mtof(A.sub_root(k)), L["gain"], L.get("decay"), t0))


def layer_bass(A, L, t0, t1, bars, rng):
    A.bass_layers.append((L, t0, t1, bars))                       # rendered as one line in render_bass


def layer_pulse(A, L, t0, t1, bars, rng):
    for k, step, sym, t in A.steps(L["pattern"], bars, t0, t1):
        cutoff = A.ramp(L, "cutoff", t, t0, t1, log=True) * A.darken(t)
        note = A.pulse_root(k) + (12 if sym == "X" else 0)
        g = A.ramp(L, "gain", t, t0, t1) + (0 if sym == "X" else -3) + rng.uniform(-0.8, 0.0)
        x = pulse(mtof(note), cutoff, rng)
        if "post_lp" in L:                               # tame the harmonics the drive regenerates
            x = lowpass(x, L["post_lp"])
        A.mix.put("pulse", x, t, g, send=0.08, verb="plate")


def layer_pluck(A, L, t0, t1, bars, rng):
    """Celesta doubling the top of the ostinato, two octaves up."""
    for k, step, sym, t in A.steps(L["pattern"], bars, t0, t1):
        note = A.pulse_root(k) + 24
        A.mix.put("keys", celesta(mtof(note), rng), t, L["gain"], pan=rng.uniform(-0.3, 0.3), send=0.35)


TAIKO_ENSEMBLE = ((105, 62, 0.6, -0.45, -5.0), (140, 85, 0.45, 0.45, -8.0))   # f0, f1, decay, pan, dB


def layer_taiko(A, L, t0, t1, bars, rng):
    for k, step, sym, t in A.steps(L["pattern"], bars, t0, t1, drums=True):
        g = A.ramp(L, "gain", t, t0, t1) + (0 if sym == "X" else -4) + rng.uniform(-0.7, 0.0)
        kick = taiko(f0=70, f1=40, decay=0.9, rng=rng)
        A.mix.put("drums", kick, t, g, send=0.12)
        if L.get("ensemble", True):
            for f0, f1, decay, pan, dg in TAIKO_ENSEMBLE:
                A.mix.put("drums", taiko(f0, f1, decay, rng), t, g + dg, pan=pan, send=0.2)
        A.mix.duck(t, 0.4 if sym == "X" else 0.25, 0.1)          # sidechain: bass + ostinato only


def layer_snare(A, L, t0, t1, bars, rng):
    for k, step, sym, t in A.steps(L["pattern"], bars, t0, t1, drums=True):
        g = A.ramp(L, "gain", t, t0, t1) + (0 if sym == "X" else -7)
        A.mix.put("drums", snare(rng), t, g, pan=-0.05, send=0.25, verb="plate")


def layer_hats(A, L, t0, t1, bars, rng):
    """Hi-hats; R = a 32nd-note ratchet (two hats in one 16th), O = open hat."""
    accent = L.get("accent", [1.0, 0.45, 0.7, 0.45])
    for k, step, sym, t in A.steps(L["pattern"], bars, t0, t1, drums=True):
        g = A.ramp(L, "gain", t, t0, t1) + rng.uniform(-1.0, 0.0)
        pan = 0.3 * (1 if step % 2 else -1)
        if sym == "O":
            A.mix.put("perc", hat(rng, open_=True), t, g - 3, pan=pan, send=0.05, verb="plate")
            continue
        A.mix.put("perc", hat(rng) * accent[step % 4], t, g, pan=pan, send=0.03, verb="plate")
        if sym == "R":
            A.mix.put("perc", hat(rng) * 0.6, t + A.s16 / 2, g, pan=-pan, send=0.03, verb="plate")


def layer_frame(A, L, t0, t1, bars, rng):
    for k, step, sym, t in A.steps(L["pattern"], bars, t0, t1, drums=True):
        g = A.ramp(L, "gain", t, t0, t1) + (-6 if sym == "x" else 0)          # X = accent, x = ghost
        A.mix.put("drums", frame_drum(rng), t, g, pan=0.1, send=0.2, verb="plate")


def layer_metal(A, L, t0, t1, bars, rng):
    for k, step, sym, t in A.steps(L["pattern"], bars, t0, t1, drums=True):
        A.mix.put("perc", metal(rng), t, L["gain"], pan=0.25 if step < 8 else -0.25, send=0.3)


def layer_shaker(A, L, t0, t1, bars, rng):
    accent = L.get("accent", [1.0, 0.35, 0.6, 0.35])
    for k, step, sym, t in A.steps(L.get("pattern", "x" * 16), bars, t0, t1, drums=True):
        hats = shaker(rng) * accent[step % 4]
        g = A.ramp(L, "gain", t, t0, t1) + rng.uniform(-1.0, 0.0)
        A.mix.put("perc", hats, t, g, pan=0.35 * (1 if step % 2 else -1), send=0.05, verb="plate")


def layer_ticks(A, L, t0, t1, bars, rng):
    """Sparse 'render ticks' on 16ths: seeded, getting denser across the layer."""
    for k, step, sym, t in A.steps("x" * 16, bars, t0, t1):
        if rng.random() < A.ramp(L, "density", t, t0, t1):
            f = hz(L["notes"][rng.integers(len(L["notes"]))])
            A.mix.put("fx", tick(f, rng), t, L["gain"] + rng.uniform(-4, 0), pan=rng.uniform(-0.6, 0.6), send=0.4)


def layer_typing(A, L, t0, t1, bars, rng):
    """Keyboard ticks on the pattern's 16ths (code typing out)."""
    for k, step, sym, t in A.steps(L.get("pattern", "x" * 16), bars, t0, t1):
        A.mix.put("fx", tick(rng.uniform(2200, 2800), rng, click=1.0, tau=0.004), t, L["gain"] + rng.uniform(-3, 0),
                  pan=rng.uniform(-0.25, 0.25), send=0.08, verb="plate")


LAYERS = {"typing": layer_typing, "drone": layer_drone, "pad": layer_pad, "sub": layer_sub, "pulse": layer_pulse, "pluck": layer_pluck,
          "bass": layer_bass, "snare": layer_snare, "hats": layer_hats, "taiko": layer_taiko, "frame": layer_frame, "metal": layer_metal, "shaker": layer_shaker,
          "ticks": layer_ticks}


# ---------- events: (arrangement, event, t, rng); each records its landing time as a hit ----------
def ev_spark(A, E, t, rng):
    A.mix.put("fx", spark(rng), t, E["gain"], send=0.6)
    A.hit(t, E["label"])


def ev_hook(A, E, t, rng):
    """The opening signature: spark + FM bell + celesta on one note, with a short sub hit under it."""
    A.mix.put("fx", spark(rng), t, E["gain"] - 6, send=0.6)
    A.mix.put("keys", bell(hz(E["note"]), rng), t, E["gain"], pan=-0.15, send=0.45)
    A.mix.put("keys", celesta(hz(E["note"]) / 2, rng), t, E["gain"] - 4, pan=0.2, send=0.35)
    A.mix.put("sub", sub_drop(1.2, 90.0, 40.0), t, E["gain"] + E.get("sub_db", 2.0))
    A.hit(t, E["label"])


def ev_button(A, E, t, rng):
    """The last drum hit before a hold: taiko ensemble + snare, then the drums breathe out."""
    A.mix.put("drums", taiko(60, 34, 1.4, rng), t, E["gain"], send=0.3)
    for f0, f1, decay, pan, dg in TAIKO_ENSEMBLE:
        A.mix.put("drums", taiko(f0, f1, decay, rng), t, E["gain"] + dg, pan=pan, send=0.3)
    A.mix.put("drums", snare(rng), t, E["gain"] - 3, send=0.4, verb="plate")
    A.hit(t, E["label"])


def ev_swell(A, E, t, rng):
    dur = E["beats"] * A.beat
    x = reverse_swell(A.voicing(E["chord"]), dur, rng, A.mix.irs["hall"])
    A.mix.put("rise", x, t - dur, E["gain"], send=0.1)        # ends (peaks) exactly on t
    A.hit(t, f"swell>{E['label']}")


def ev_impact(A, E, t, rng):
    A.mix.put("fx", impact(E["size"], rng), t, E["gain"], send=0.35)
    A.mix.put("sub", sub_drop(), t, E["gain"] + E.get("drop_db", -2.0))
    A.hit(t, E["label"])


def ev_braam(A, E, t, rng):
    A.mix.put("fx", braam(rng), t, E["gain"], send=0.5)
    A.hit(t, E["label"])


def ev_metal(A, E, t, rng):
    A.mix.put("perc", metal(rng, decay=1.2), t, E["gain"], send=0.45)
    A.hit(t, E["label"])


def ev_riser(A, E, t, rng):
    end = A.at(E["until"])
    A.mix.put("rise", riser(end - t, rng), t, E["gain"], send=0.2)
    A.hit(end, f"riser>{E['label']}")


def ev_celesta(A, E, t, rng):
    A.mix.put("keys", celesta(hz(E["note"]), rng), t, E["gain"], pan=rng.uniform(-0.35, 0.35), send=0.35)
    A.hit(t, E["label"])


def ev_clack(A, E, t, rng):
    A.mix.put("perc", clack(rng), t, E["gain"], pan=0.15, send=0.25, verb="plate")
    A.hit(t, E["label"])


def ev_stab(A, E, t, rng):
    dur = E["beats"] * A.beat
    x = stab(A.voicing(E["chord"]), dur, rng, bright=E.get("bright", 3200.0), tau=E.get("tau", 0.4))
    A.mix.put("keys", x, t, E["gain"], send=0.3, verb="plate")
    if E.get("ring"):                                    # a bigger landing: add a metal ring
        A.mix.put("perc", metal(rng, decay=1.2), t, E["gain"] - 4, send=0.45)
    A.hit(t, E["label"])


def ev_fail(A, E, t, rng):
    A.mix.put("fx", fail_hit(A.voicing("fail"), rng), t, E["gain"], send=0.25)
    A.hit(t, E["label"])


def ev_lead(A, E, t, rng):
    dur = E["beats"] * A.beat
    n = int((dur + 0.3) * SR)
    s = secs(n)
    vibrato = 2 ** (8 / 1200 * np.sin(TAU * 5.2 * s) * np.clip((s - 0.35) / 0.4, 0, 1))
    A.mix.put("lead", lead(hz(E["note"]) * vibrato, dur + 0.3, release=0.3), t, E["gain"], send=0.3)
    A.hit(t, E["label"])


def ev_fourier(A, E, t, rng):
    """One sustained note; on each beat a new odd harmonic (1, 3, 5, 7) joins: a sine becomes a square."""
    dur = E["beats"] * A.beat
    odd = tuple(E.get("harmonics", (1, 3, 5, 7)))
    enter = {k: i * A.beat for i, k in enumerate(odd)}
    x = lead(hz(E["note"]), dur + 0.1, odd=odd, enter=enter, release=0.1, spotlight=E.get("spotlight", 0.0))
    s = secs(len(x))
    for i in range(len(odd)):                            # a small re-articulation on every beat
        ramp_in = np.clip((s - i * A.beat) / 0.005, 0, 1)                 # 5 ms: no step, no click
        x *= 1 + E.get("accent", 0.25) * np.exp(-np.maximum(s - i * A.beat, 0) / 0.08) * ramp_in
    A.mix.put("lead", x, t, E["gain"], send=0.2)
    for i, k in enumerate(odd):
        A.hit(t + i * A.beat, f"{E['label']}:h{k}")


def ev_doppler(A, E, t, rng):
    """A tone flying past: physical Doppler shift (sharp -> flat, S-curve), 1/r level, left -> right."""
    dur = E["beats"] * A.beat
    n = int((dur + 0.1) * SR)
    s = secs(n)
    x = (s - dur / 2) * (3.0 / (dur / 2))               # position along the path; closest approach = 1
    r = np.sqrt(x ** 2 + 1)
    beta = (1 - 2 ** (-E["cents"] / 1200)) / (3 / math.sqrt(10))   # v/c so the start is `cents` sharp
    freq = hz(E["note"]) / (1 + beta * x / r)
    tone = lead(freq, dur + 0.1, release=0.1) * (0.3 + 0.7 / r) * fade(n, 0.03)
    A.mix.put("lead", pan2(tone, 0.8 * x / r), t, E["gain"], send=0.25)
    A.hit(t, E["label"])


def ev_tick(A, E, t, rng):
    x = tick(hz(E.get("note", "A5")), rng, click=E.get("click", 0.6), tau=E.get("tau", 0.01))
    A.mix.put("fx", x, t, E["gain"], pan=E.get("pan", 0.0), send=0.2)
    A.hit(t, E["label"])


def ev_bell(A, E, t, rng):
    A.mix.put("keys", bell(hz(E["note"]), rng), t, E["gain"], pan=E.get("pan", 0.0), send=0.4)
    A.hit(t, E["label"])


def ev_voice(A, E, t, rng):
    A.mix.put("keys", vowel(hz(E["note"]), rng), t, E["gain"], pan=-0.2, send=0.3)
    A.hit(t, E["label"])


def ev_sfx(A, E, t, rng):
    A.mix.put("fx", pop_swish(rng), t, E["gain"], send=0.2)
    A.hit(t, E["label"])


def ev_sparkle(A, E, t, rng):
    A.mix.put("keys", sparkle(rng), t, E["gain"], send=0.5)
    A.hit(t, E["label"])


def ev_typing(A, E, t, rng):
    A.mix.put("fx", tick(rng.uniform(2200, 2800), rng, click=1.0, tau=0.004), t, E["gain"],
              pan=rng.uniform(-0.2, 0.2), send=0.1, verb="plate")
    A.hit(t, E["label"])


EVENTS = {"spark": ev_spark, "swell": ev_swell, "impact": ev_impact, "braam": ev_braam, "metal": ev_metal,
          "riser": ev_riser, "celesta": ev_celesta, "hook": ev_hook, "button": ev_button, "clack": ev_clack, "stab": ev_stab,
          "fail": ev_fail, "lead": ev_lead, "fourier": ev_fourier, "doppler": ev_doppler, "tick": ev_tick,
          "typing": ev_typing, "bell": ev_bell, "voice": ev_voice, "sfx": ev_sfx, "sparkle": ev_sparkle}


# ---------- master ----------
def loudness(x):
    """Integrated loudness (ITU-R BS.1770-4, 48 kHz K-weighting, gated), in LUFS."""
    k = np.array([[1.53512485958697, -2.69169618940638, 1.19839281085285, 1.0, -1.69065929318241, 0.73248077421585],
                  [1.0, -2.0, 1.0, 1.0, -1.99004745483398, 0.99007225036621]])
    p = (sosfilt(k, x, axis=-1) ** 2).sum(axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    c = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, len(p) - blk + 1, hop)
    z = (c[starts + blk] - c[starts]) / blk
    z = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    z = z[-0.691 + 10 * np.log10(z) > rel]
    return -0.691 + 10 * np.log10(z.mean())


def true_peak_db(x):
    return 20 * np.log10(np.max(np.abs(resample_poly(x, 4, 1, axis=-1))) + 1e-12)


def limit(x, ceiling_db, release=0.15, lookahead=0.004, block=32):
    """Look-ahead peak limiter at control rate: gain is ready before the peak, recovers smoothly."""
    ceiling = db(ceiling_db)
    peak = np.max(np.abs(x), axis=0)
    nb = -(-len(peak) // block)
    blocks = np.pad(peak, (0, nb * block - len(peak))).reshape(nb, block).max(axis=1)
    need = np.minimum(1.0, ceiling / np.maximum(blocks, 1e-9))
    need = minimum_filter1d(need, 2 * max(1, int(lookahead * SR / block)) + 1)
    g, cur, coef = np.empty(nb), 1.0, math.exp(-block / (release * SR))
    for i, v in enumerate(need):
        cur = v if v < cur else v + (cur - v) * coef
        g[i] = cur
    gain = np.interp(np.arange(len(peak)), np.arange(nb) * block + block / 2, g)
    return x * gain, 20 * np.log10(g.min())


def master(A, mix):
    cfg = A.score["master"]
    mix = highpass(mix, 30, order=4)                                # no rumble below the sub
    a, b = A.at(cfg["fade"][0]), A.at(cfg["fade"][1])
    t = secs(A.n)
    mix *= np.where(t < a, 1.0, np.where(t < b, np.cos(0.5 * np.pi * np.clip((t - a) / (b - a), 0, 1)), 0.0))
    mix *= db(cfg["lufs"] - loudness(mix))
    for _ in range(3):                                              # limiting lowers loudness a little: re-aim
        out, gr = limit(mix, cfg["ceiling_db"])
        miss = cfg["lufs"] - loudness(out)
        if abs(miss) < 0.1:
            break
        mix *= db(miss)
    tp = true_peak_db(out)
    if tp > cfg["true_peak_db"]:
        out *= db(cfg["true_peak_db"] - tp)
    return out, {"lufs": round(loudness(out), 2), "true_peak_db": round(true_peak_db(out), 2),
                 "max_gain_reduction_db": round(gr, 2)}


# ---------- output ----------
def hit_kind(what):
    return "swell-peak (no transient)" if what.startswith(("swell>", "riser>")) else "transient"


HITS_NOTE = ("kind=transient hits are audible onsets (cue-checked in audio/check/cuecheck.txt); swell-peak entries "
             "mark where a riser / reverse swell culminates and are not onset cues. v3 has no stops: each former stop "
             "is a hold (held breath: a button hit on its first sample, drums out, bass and ostinato filter down, "
             "pad and sub sustain, a swell into the next downbeat).")


def beat_map(A):
    bars = [[k, round(A.bar_start(k), 4), A.bar_beats[k - 1]] for k in range(1, A.score["bars"] + 1)]
    beats = [round(start + i * A.beat, 4) for _, start, nb in bars for i in range(nb)]
    sections = [{"name": s["name"], "start": round(A.bar_start(s["bars"][0]), 4),
                 "end": round(A.bar_start(s["bars"][1] + 1), 4), "bars": s["bars"][1] - s["bars"][0] + 1,
                 "first_bar": s["bars"][0]} for s in A.score["sections"]]
    stops = [{"start": round(A.at(a), 4), "end": round(A.at(b), 4)} for a, b in A.score.get("stops", [])]
    holds = [{"start": round(a, 4), "end": round(b, 4)} for a, b in A.holds]
    meter_note = ", ".join(f"bar {k} is {nb}/4" for k, _, nb in bars if nb != 4) or "all bars 4/4"
    return {"bpm": A.bpm, "offset": 0.0, "duration": round(A.n / SR, 4),
            "fps_note": f"90 bpm @ 30 fps: beat = 20 frames; {meter_note}",
            "beats": beats, "downbeats": [start for _, start, _ in bars],
            "bars": bars, "bars_note": "[bar number, start (s), beats in bar]", "sections": sections,
            "hits": [dict(h, kind=hit_kind(h["what"])) for h in sorted(A.hits, key=lambda h: (h["t"], h["what"]))],
            "stops": stops, "holds": holds, "hits_note": HITS_NOTE,
            "fade": {"start": round(A.at(A.score["master"]["fade"][0]), 4),
                     "end": round(A.at(A.score["master"]["fade"][1]), 4)}}


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).round().astype("<i2").T.copy()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    args = sys.argv[1:]
    stems_dir = None
    if "--stems" in args:
        i = args.index("--stems")
        stems_dir, args = Path(args[i + 1]), args[:i] + args[i + 2:]
    score = json.loads(Path(args[0]).read_text())
    out = Path(args[1])
    A = Arrangement(score)
    mix = A.render()
    final, stats = master(A, mix)
    write_wav(out, final)
    bm = beat_map(A)
    bm["master"] = stats
    out.with_suffix(".beats.json").write_text(json.dumps(bm, indent=2))
    (out.parent / "check").mkdir(exist_ok=True)
    (out.parent / "check" / "placements.json").write_text(json.dumps(sorted(A.mix.log)))
    if stems_dir:
        stems_dir.mkdir(parents=True, exist_ok=True)
        for name, x in A.mix.stems.items():
            write_wav(stems_dir / f"{name}.wav", 0.5 * x / (np.max(np.abs(x)) or 1))
    print(f"{out}  {A.n / SR:.3f}s  {stats}  hits={len(A.hits)}")


if __name__ == "__main__":
    main()
