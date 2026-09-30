"""Instrument voices for the `parts` of tools/audio/music.py: synthesis only (numpy + scipy), no samples, no downloads.

Every voice is registered in INSTR with a kind, a default octave and a level:
  note     polyphonic; one render per note, cached by the engine: fn(m, dur, vel, rng, P) -> (n,) or (2, n)
  mono     monophonic phrase with glides, scoops and vibrato (bowed solo, winds, 808): fn(f, amp, onsets, P, rng)
           f = Hz per sample, amp = envelope per sample, onsets = [(sample, vel, legato)]
  drum     one hit, optionally pitched: fn(vel, art, dur, rng, P, f) — art "" is the normal stroke, "o" the other one
           (open hat, rim, slap, bell, swish, choke, low block…)
  texture  a continuous bed over a span: fn(n, rng, P)
m is a MIDI number (float), dur the held time in seconds (voices add their own natural tail), vel 0..1 shapes the
timbre only (the engine scales the amplitude). P is the part's params merged over the voice's defaults.
LEVEL puts every voice at a comparable loudness at gain_db 0: a hit or pluck at velocity 1 peaks near 0.5, a held voice
sits near -20 dBFS RMS, a texture near -34 dBFS RMS (a bed under the music).
The braam, celesta, metal, frame-drum, 808-hat and saw recipes follow showcase/04-intro-film/audio/score_engine.py; ks()
is music.ks with a pluck position and a hammer option. The physically modelled voices (the ones ending in _pm, and guitar,
koto, shamisen, banjo, kalimba) are digital waveguides and modal bars; their parameter ranges and several preset values
come from lemo-opuscar core/audio/pluck.py (MIT, © LemoLab). Everything else is written for this file.
"""
import functools, sys, zlib
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, lfilter, lfiltic, fftconvolve, oaconvolve

SR = 48000
TAU = 2 * np.pi


# ---------- helpers ----------
def secs(n): return np.arange(n) / SR
def mtof(m): return 440.0 * 2 ** ((np.asarray(m, dtype=float) - 69) / 12)
def crc(s): return zlib.crc32(str(s).encode()) & 0x7FFFFFFF


def lpf(x, fc, order=2):
    return sosfilt(butter(order, min(float(fc), 0.45 * SR), "low", fs=SR, output="sos"), x, axis=-1)


def hpf(x, fc, order=2):
    return sosfilt(butter(order, max(float(fc), 5.0), "high", fs=SR, output="sos"), x, axis=-1)


def bpf(x, lo, hi, order=2):
    lo = min(max(float(lo), 5.0), 0.45 * SR / 1.1); hi = max(min(float(hi), 0.45 * SR), lo * 1.1)   # both edges stay below Nyquist
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x, axis=-1)


def peq(x, f0, gain_db, q=1.0):
    """RBJ peaking EQ: a body resonance or a formant."""
    w = TAU * min(float(f0), 0.45 * SR) / SR; A = 10 ** (gain_db / 40); al = np.sin(w) / (2 * q); c = np.cos(w)
    b = np.array([1 + al * A, -2 * c, 1 - al * A]); a = np.array([1 + al / A, -2 * c, 1 - al / A])
    return lfilter(b / a[0], a / a[0], x, axis=-1)


def body(x, modes):
    for f0, g, q in modes:
        x = peq(x, f0, g, q)
    return x


def _biquad_lp(fc, q):
    w = TAU * fc / SR; c, al = np.cos(w), np.sin(w) / (2 * q); b0, a0 = (1 - c) / 2, 1 + al
    return [b0 / a0, 2 * b0 / a0, b0 / a0, 1.0, -2 * c / a0, (1 - al) / a0]


def sweep_lp(x, fc, res=1.0, block=64):
    """4-pole low-pass whose cutoff follows fc (Hz per sample), updated every block; x is (n,) or (ch, n)."""
    x2 = np.atleast_2d(x); y = np.empty_like(x2); zi = np.zeros((2, x2.shape[0], 2))
    for s in range(0, x2.shape[1], block):
        f = min(max(float(fc[s]), 30.0), 0.45 * SR)
        sos = np.array([_biquad_lp(f, 0.5412), _biquad_lp(f, 1.3066 * res)])
        y[:, s:s + block], zi = sosfilt(sos, x2[:, s:s + block], axis=-1, zi=zi)
    return y if x.ndim == 2 else y[0]


def fade(x, a=0.0015, r=0.01):
    """Raised-cosine fade in and out (no click at either end)."""
    n = x.shape[-1]; na = min(int(a * SR), n // 2); nr = min(int(r * SR), n - na)
    if na > 0: x[..., :na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    if nr > 0: x[..., n - nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, nr + 1) / nr)
    return x


def release_after(n, hold, r):
    """1 until `hold` seconds, then a cosine fall to 0 over r."""
    k = np.clip((secs(n) - hold) / max(r, 1e-4), 0, 1); return 0.5 + 0.5 * np.cos(np.pi * k)


def phase(f, n, ph=0.0):
    return (ph + np.cumsum(np.broadcast_to(np.asarray(f, float), (n,))) / SR) % 1.0


def saw(f, n, ph=0.0):
    """Band-limited (polyBLEP) sawtooth; f is a scalar or one value per sample."""
    dt = np.broadcast_to(np.asarray(f, float) / SR, (n,)); p = (ph + np.cumsum(dt)) % 1.0; y = 2 * p - 1
    lo, hi = p < dt, p > 1 - dt
    a = p[lo] / dt[lo]; y[lo] -= a + a - a * a - 1
    b = (p[hi] - 1) / dt[hi]; y[hi] -= b * b + b + b + 1
    return y


def pulse(f, n, duty=0.5, ph=0.0):
    """Band-limited pulse (difference of two saws): zero mean, duty 0.125 / 0.25 / 0.5 for chip leads."""
    return saw(f, n, ph) - saw(f, n, ph + duty)


def pan2(x, pan=0.0):
    """Mono -> stereo, constant power with centre = unity per side; a stereo input is balanced instead."""
    if x.ndim == 2:
        return x * np.array([[min(1.0, 1 - pan)], [min(1.0, 1 + pan)]])
    a = (pan + 1) * np.pi / 4; y = np.empty((2,) + x.shape)
    np.multiply(x, np.cos(a), out=y[0]); np.multiply(x, np.sin(a), out=y[1]); y *= np.sqrt(2)   # one buffer, no temporaries
    return y


def wander(rng, n, rate):
    """Smooth random control signal in [-1, 1] with about `rate` new values per second (cosine-interpolated)."""
    k = int(n * rate / SR) + 3; pts = rng.uniform(-1, 1, k); u = np.arange(n) * rate / SR
    i = u.astype(int); w = 0.5 - 0.5 * np.cos(np.pi * (u - i)); return pts[i] * (1 - w) + pts[i + 1] * w


def modal(f0, n, modes, bend=None):
    """Sum of decaying sines: modes = [(ratio, amp, tau)]; bend = pitch factor per sample (a gong's drop or rise)."""
    t = secs(n); x = np.zeros(n); C = np.cumsum(bend) / SR if bend is not None else t
    for r, a, tau in modes:
        fr = f0 * r
        if fr >= 0.45 * SR or a == 0: continue
        k = min(n, int(7 * tau * SR) + 1); x[:k] += a * np.sin(TAU * fr * C[:k]) * np.exp(-t[:k] / tau)
    return x


def burst(rng, n, lo, hi, tau, amp=1.0):
    """A filtered noise burst (mallet, nail, beater) of length n with decay tau."""
    k = min(n, int(max(8 * tau, 0.004) * SR)); x = np.zeros(n)
    x[:k] = bpf(rng.standard_normal(k), lo, hi) * np.exp(-secs(k) / tau) * amp; return x


def ks(f, n, t60, bright, rng, pos=0.15, excite="noise"):
    """Karplus-Strong string (the loop of music.ks) with a pluck position and a noise or hammer excitation."""
    f = np.broadcast_to(np.asarray(f, float), (n,)); D = SR / f - 0.5; M = D.astype(int); q = D - M
    rho = 10 ** (-3 / (t60 * f)); P = int(M.max()) + 3; N0 = int(SR / f[0]); mmin = max(1, int(M.min()))
    if excite == "hammer":
        w = max(2, int(N0 * (0.3 - 0.25 * bright))); x = np.zeros(N0); x[:min(w, N0)] = np.hanning(w + 2)[1:-1][:N0]
        x += 0.04 * rng.uniform(-1, 1, N0)
    else:
        c = 0.6 - 0.45 * bright; x = lfilter([1 - c], [1, -c], rng.uniform(-1, 1, N0))
    k = max(1, int(N0 * pos)); x = x - np.concatenate([np.zeros(k), x[:-k]])
    y = np.zeros(n + P); m = min(N0, n); y[P:P + m] = (x - x.mean())[:m]
    for s in range(0, n, mmin):
        e = min(n, s + mmin); j = np.arange(s, e) - M[s:e] + P
        y[P + s:P + e] += rho[s:e] * 0.5 * ((1 - q[s:e]) * y[j] + y[j - 1] + q[s:e] * y[j - 2])
    return y[P:]


def unbeat(X, inc, depth=0.85):
    """Even out the beating between detuned players: scale by sqrt(incoherent power / actual power), both smoothed
    below ~6 Hz. inc = the sum of the players' own powers, on the same scale as X. Keeps the ensemble's shimmer, drops
    the 10 dB swells that read as pumping."""
    sos = butter(2, 6, "low", fs=SR, output="sos"); act = sosfiltfilt(sos, (X ** 2).mean(0) if X.ndim == 2 else X ** 2)
    g = np.clip(np.sqrt(np.maximum(sosfiltfilt(sos, inc), 1e-12) / np.maximum(act, 1e-12)), 0.33, 3.0) ** depth
    return X * g


def drive(x, d):
    return np.tanh(d * x) / np.tanh(d) if d > 0 else x


def crush(x, bits=10, hold=2):
    """Lo-fi sampler: sample-and-hold by `hold` samples and quantise to `bits`."""
    y = np.repeat(x[::hold], hold)[:len(x)]; q = 2 ** (bits - 1); return np.round(y * q) / q


# ---------- keys ----------
def piano(m, dur, vel, rng, P):
    """Additive piano: stretched partials (inharmonicity B), hammer-position comb, two-stage decay, unison beating,
    hammer noise, damper. tone "felt" = soft felt piano (dark, thumpy), "bright" = concert grand. pedal: let it ring."""
    f0 = float(mtof(m)); felt = P.get("tone", "bright") == "felt"; pedal = bool(P.get("pedal"))
    T = float(np.clip(5.5 * (262 / f0) ** 0.55, 0.6, 12.0)); tau1 = T / 6.91
    L = max(dur + 0.3, min(0.55 * T, 6.0)) if pedal else dur + 0.3
    n = int(L * SR); t = secs(n); x = np.zeros(n)
    B = float(np.clip(8e-5 * (f0 / 110) ** 1.2, 3e-5, 2e-3))
    fmax = min((1400 + 2600 * vel) if felt else (3500 + 7000 * vel), 0.45 * SR)
    slope = (1.9 + 0.9 * (1 - vel)) if felt else (0.85 + 1.0 * (1 - vel))
    det = 2 ** (rng.uniform(0.25, 0.8) / 1200) - 1
    for k in range(1, 40):
        fk = k * f0 * np.sqrt(1 + B * k * k)
        if fk > fmax: break
        tk = tau1 / (1 + 0.45 * (k - 1)); nk = min(n, int(7 * tk * SR) + 1); tt = t[:nk]
        a = abs(np.sin(np.pi * k / 8.3)) / k ** slope
        x[:nk] += a * (0.55 * np.exp(-tt / (0.25 * tk)) + 0.45 * np.exp(-tt / tk)) * np.sin(TAU * fk * tt) * (0.72 + 0.28 * np.cos(TAU * fk * det * tt))
    if felt:
        x += burst(rng, n, 60, 700 + 600 * vel, 0.012, 0.06 * vel); x = lpf(x, 900 + 2600 * vel)
    else:
        x += burst(rng, n, 1200, 7000, 0.003, 0.05 * vel) + burst(rng, n, 40, 300, 0.02, 0.05)
    if not pedal: x *= release_after(n, dur, 0.12)
    return fade(x, 0.001, 0.03)


def epiano(m, dur, vel, rng, P):
    """Rhodes-like: 1:1 FM tine whose index falls after the strike, a high 'tine ping', bark (drive) when hit hard;
    trem = amplitude tremolo depth."""
    f0 = float(mtof(m)); n = int((dur + 0.3) * SR); t = secs(n)
    tau = float(np.clip(2.2 * (262 / f0) ** 0.5, 0.5, 5.0))
    I = (0.5 + 2.2 * vel) * np.exp(-t / 0.25) + 0.25 + 0.3 * vel
    x = np.sin(TAU * f0 * t + I * np.sin(TAU * f0 * t)) * np.exp(-t / tau) + 0.3 * np.sin(TAU * f0 * t) * np.exp(-t / (1.5 * tau))
    ft = min(f0 * 14, 0.4 * SR); x += 0.15 * vel * np.sin(TAU * ft * t) * np.exp(-t / 0.008)
    if vel > 0.55: x = drive(x, 1 + 3 * (vel - 0.55))
    if P.get("trem"): x *= 1 - float(P["trem"]) * (0.5 - 0.5 * np.cos(TAU * 4.8 * t))
    return fade(x * release_after(n, dur, 0.1), 0.001, 0.02)


def harpsichord(m, dur, vel, rng, P):
    """Quill-plucked: bright KS 8' string plus a 4' string an octave up, plucked near the end; damper on release."""
    f0 = float(mtof(m)); n = int((dur + 0.08) * SR); t60 = float(np.clip(2.5 * (262 / f0) ** 0.3, 0.8, 4.0))
    x = ks(f0, n, t60, 0.95, rng, pos=0.07)
    if f0 * 2 < 5000: x += 0.45 * ks(f0 * 2, n, t60 * 0.7, 0.95, rng, pos=0.09)
    x = peq(hpf(x, 110), 2500, 4, 1.2) + burst(rng, n, 2000, 9000, 0.0015, 0.2)
    return fade(x * release_after(n, dur, 0.04), 0.0005, 0.01)


def _ringing(n, dur, P):
    return release_after(n, dur, 0.12) if P.get("damp") else 1.0


def celesta(m, dur, vel, rng, P):
    f0 = float(mtof(m)); T = float(np.clip(1.1 * (523 / f0) ** 0.3, 0.5, 2.0)); n = int(min(7 * T, 4.0) * SR)
    x = modal(f0, n, [(1, 1.0, T), (2, 0.2, T * 0.35), (4.16, 0.12 * vel, 0.07), (6.9, 0.04 * vel, 0.03)])
    x += burst(rng, n, 800, 4000, 0.002, 0.04)
    return fade(x * _ringing(n, dur, P), 0.001, 0.05)


def musicbox(m, dur, vel, rng, P):
    """Comb tine: cantilever modes 1 : 6.27 : 17.55, a slightly detuned twin (beating), a sharp pluck; out of tune by a few cents."""
    f0 = float(mtof(m)) * 2 ** (rng.uniform(-6, 6) / 1200); T = float(np.clip(1.6 * (1047 / f0) ** 0.4, 0.5, 2.5))
    n = int(min(7 * T, 4.0) * SR)
    x = modal(f0, n, [(1, 1.0, T), (1.0015, 0.3, T * 0.8), (6.27, 0.25, 0.09), (17.55, 0.08, 0.02)])
    x += burst(rng, n, 3000, 10000, 0.001, 0.15)
    return fade(x * _ringing(n, dur, P), 0.0005, 0.05)


def glockenspiel(m, dur, vel, rng, P):
    f0 = float(mtof(m)); T = float(np.clip(2.0 * (1047 / f0) ** 0.3, 0.8, 3.0)); n = int(min(6 * T, 4.0) * SR)
    x = modal(f0, n, [(1, 1.0, T), (2.756, 0.45, T * 0.25), (5.404, 0.25 * vel, 0.08), (8.933, 0.1 * vel, 0.03)])
    x += burst(rng, n, 3000, 12000, 0.0008, 0.25)
    return fade(x * _ringing(n, dur, P), 0.0005, 0.05)


def toypiano(m, dur, vel, rng, P):
    """Struck rods: short, clanky, out of tune (±20 cents per note), a plastic key knock."""
    f0 = float(mtof(m)) * 2 ** (rng.uniform(-20, 20) / 1200); n = int(1.2 * SR)
    x = modal(f0, n, [(1, 1.0, 0.55), (1.006, 0.5, 0.45), (2.95, 0.35, 0.12), (6.1, 0.12, 0.04)])
    x += burst(rng, n, 400, 1500, 0.008, 0.3) + burst(rng, n, 60, 250, 0.015, 0.2)
    return fade(x * _ringing(n, dur, P), 0.0005, 0.05)


# ---------- mallets ----------
def marimba(m, dur, vel, rng, P):
    """Tuned bar 1 : 3.93 : 9.2, a resonator tube that blooms the fundamental, a soft mallet thump."""
    f0 = float(mtof(m)); T = float(np.clip(0.9 * (262 / f0) ** 0.8, 0.12, 1.8)); n = int(min(6 * T + 0.05, 3.0) * SR)
    t = secs(n); x = modal(f0, n, [(1, 1.0, T), (3.93, 0.05 + 0.28 * vel, T * 0.22), (9.2, 0.05 * vel, T * 0.08)])
    x += 0.35 * np.sin(TAU * f0 * t) * (1 - np.exp(-t / 0.006)) * np.exp(-t / (1.4 * T))
    x += lpf(burst(rng, n, 60, 3 * f0 + 800, 0.003, 1.0), 3 * f0 + 800) * 0.15 * vel
    return fade(x * _ringing(n, dur, P), 0.0008, 0.03)


def xylophone(m, dur, vel, rng, P):
    f0 = float(mtof(m)); T = float(np.clip(0.5 * (523 / f0) ** 0.5, 0.1, 0.8)); n = int((6 * T + 0.05) * SR)
    x = modal(f0, n, [(1, 1.0, T), (3.0, 0.4, T * 0.35), (6.0, 0.12 * vel, T * 0.15)])
    x += burst(rng, n, 2000, 9000, 0.001, 0.25)
    return fade(x, 0.0005, 0.02)


def vibraphone(m, dur, vel, rng, P):
    """Aluminium bar 1 : 4 : 10, long ring, motor tremolo (motor = Hz, 0 = off; depth), pedal on by default."""
    f0 = float(mtof(m)); T = float(np.clip(3.2 * (523 / f0) ** 0.4, 1.2, 6.0))
    n = int((min(0.7 * T, 4.0) if P.get("pedal", True) else dur + 0.2) * SR); t = secs(n)
    x = modal(f0, n, [(1, 1.0, T / 6.91 * 2.5), (4.0, 0.2 * vel, 0.35), (10.0, 0.05 * vel, 0.05)])
    x += lpf(burst(rng, n, 60, 2500, 0.003, 1.0), 2500) * 0.08
    rate, depth = float(P.get("motor", 5.5)), float(P.get("depth", 0.45))
    if rate > 0: x *= 1 - depth * (0.5 - 0.5 * np.cos(TAU * rate * t))
    if not P.get("pedal", True): x *= release_after(n, dur, 0.15)
    return fade(x, 0.0008, 0.05)


# ---------- plucked ----------
def _plucked(f, n, dur, rng, P, t60, bright, pos, modes=(), lp=None, hp=None, ring=False, damp=0.08, excite="noise"):
    ring = P.get("ring", ring)
    if P.get("mute"): t60, ring = 0.05, False
    x = ks(f, n, t60, bright, rng, pos, excite)
    if modes: x = body(x, modes)
    if lp: x = lpf(x, lp)
    if hp: x = hpf(x, hp)
    if not ring: x *= release_after(n, dur, damp)
    return x


def _len(dur, t60, ring, P):
    return (min(t60, 6.0) if P.get("ring", ring) and not P.get("mute") else dur + 0.12)


def nylon(m, dur, vel, rng, P):
    f0 = float(mtof(m)); t60 = float(np.clip(3.0 * (196 / f0) ** 0.5, 1.0, 5.0)); n = int(_len(dur, t60, False, P) * SR)
    x = _plucked(f0, n, dur, rng, P, t60, 0.3 + 0.3 * vel, 0.18, [(105, 5, 4), (210, 4, 3), (420, 2, 2)], lp=3500 + 2000 * vel, damp=0.12)
    return fade(x, 0.0008, 0.02)


def ukulele(m, dur, vel, rng, P):
    f0 = float(mtof(m)); t60 = float(np.clip(1.2 * (392 / f0) ** 0.4, 0.5, 2.0)); n = int(_len(dur, t60, False, P) * SR)
    x = _plucked(f0, n, dur, rng, P, t60, 0.45 + 0.3 * vel, 0.2, [(260, 5, 3), (520, 3, 3), (1400, 2, 2)], lp=5000, hp=180, damp=0.08)
    return fade(x, 0.0008, 0.02)


def harp(m, dur, vel, rng, P):
    """Plucked mid-string (round), long ring, plus a pure sine layer for the harp's glassy fundamental."""
    f0 = float(mtof(m)); t60 = float(np.clip(4.5 * (262 / f0) ** 0.35, 1.5, 8.0)); n = int(_len(dur, t60, True, P) * SR)
    x = _plucked(f0, n, dur, rng, P, t60, 0.2 + 0.2 * vel, 0.45, lp=3000 + 2000 * vel, ring=True)
    x += 0.35 * np.sin(TAU * f0 * secs(n)) * np.exp(-secs(n) / (t60 / 6.91))
    return fade(x, 0.001, 0.05)


def pizzicato(m, dur, vel, rng, P):
    f0 = float(mtof(m)); t60 = float(np.clip(0.6 * (262 / f0) ** 0.35, 0.25, 1.2)); n = int((t60 + 0.05) * SR)
    x = _plucked(f0, n, dur, rng, {**P, "ring": True}, t60, 0.4 + 0.2 * vel, 0.3, [(280, 6, 3), (460, 4, 3), (2800, 3, 1.5)])
    x += lpf(burst(rng, n, 40, 400, 0.01, 1.0), 400) * 0.2
    return fade(x, 0.0008, 0.02)


def upright(m, dur, vel, rng, P):
    """Acoustic bass for walking lines: dark KS pluck with a finger thump and a small pitch drop at the attack."""
    f0 = float(mtof(m)); t60 = float(np.clip(1.6 * (55 / f0) ** 0.3, 0.8, 2.5)); n = int((dur + 0.1) * SR)
    f = f0 * 2 ** (18 * np.exp(-secs(n) / 0.025) / 1200)
    x = _plucked(f, n, dur, rng, P, t60, 0.25 + 0.2 * vel, 0.12, [(90, 6, 2), (180, 3, 2), (700, 2, 1.5)], lp=2200, damp=0.06)
    x += burst(rng, n, 40, 250, 0.015, 0.25) + burst(rng, n, 1000, 3000, 0.003, 0.04)
    return fade(x, 0.001, 0.02)


def pipa(m, dur, vel, rng, P):
    """Bright nail pluck with a twang (pitch drop at the attack); tremolo (轮指) comes from the part's `tremolo`."""
    f0 = float(mtof(m)); t60 = float(np.clip(1.1 * (392 / f0) ** 0.4, 0.4, 1.8)); n = int(_len(dur, t60, True, P) * SR)
    f = f0 * 2 ** (12 * np.exp(-secs(n) / 0.02) / 1200)
    x = _plucked(f, n, dur, rng, P, t60, 0.75 + 0.2 * vel, 0.1, [(420, 6, 3), (1500, 4, 2), (3200, 3, 2)], hp=150, ring=True)
    x += burst(rng, n, 3000, 9000, 0.0012, 0.15 * vel)
    return fade(x, 0.0005, 0.03)


GUQIN_HARM_DB = ((24, 8.4), (30, 9.5), (36, 9.6), (42, 11.4), (48, 11.9), (54, 13.3), (60, 13.8), (66, 14.9), (72, 19.2), (78, 22.0),
                 (84, 24.4), (90, 24.6), (96, 35.8))   # measured: harmonic minus pluck, loudest 400 ms, mean of velocity 0.5 / 0.7 / 1


def guqin(m, dur, vel, rng, P):
    """Low silk string, very long ring. Per note (art dict or params): slide (start this many semitones away and glide in),
    bend (press after the pluck), yin (吟, small vibrato), nao (猱, wide slow vibrato), harm (泛音: a pure harmonic)."""
    f0 = float(mtof(m)); n = int(min(float(np.clip(6 * (131 / f0) ** 0.3, 3, 9)), 5.0) * SR); t = secs(n)
    if P.get("harm"):   # as loud as a plucked note of the same pitch and velocity (loudest 400 ms), not 9–35 dB louder
        x = modal(f0, n, [(1, 1.0, 1.6), (2, 0.15, 0.6), (3, 0.04, 0.3)]) + burst(rng, n, 2000, 8000, 0.001, 0.1)
        x = x * 10 ** (-float(np.interp(float(m), *zip(*GUQIN_HARM_DB))) / 20)
        return fade(x * _ringing(n, dur, P), 0.0008, 0.05)
    s = np.zeros(n)
    if P.get("slide"):
        u = np.clip((t - 0.04) / 0.25, 0, 1); s += float(P["slide"]) * (1 - u * u * (3 - 2 * u))
    if P.get("bend"):
        u = np.clip((t - 0.25) / 0.3, 0, 1); s += float(P["bend"]) * u * u * (3 - 2 * u)
    if P.get("yin"): s += 0.2 * np.sin(TAU * 4.5 * t) * np.clip((t - 0.2) / 0.3, 0, 1)
    if P.get("nao"): s += 0.5 * np.sin(TAU * 2.5 * t) * np.clip((t - 0.15) / 0.3, 0, 1)
    f = f0 * 2 ** (s / 12)
    x = ks(f, n, float(np.clip(6 * (131 / f0) ** 0.3, 3, 9)), 0.2 + 0.15 * vel, rng, 0.13)
    x = peq(lpf(x, 1800 + 1500 * vel), 200, 3, 1.0)
    if P.get("slide") or P.get("bend"):   # 走手音: the finger squeaks along the silk while the pitch moves
        speed = np.abs(np.gradient(s)) * SR; x += bpf(rng.standard_normal(n), 2000, 5000) * np.clip(speed / 8, 0, 1) * 0.03
    return fade(x * _ringing(n, dur, P), 0.001, 0.05)


def balalaika(m, dur, vel, rng, P):
    """Two unison courses 3 cents apart, thin triangular body, bright; tremolo from the part's `tremolo`."""
    f0 = float(mtof(m)); t60 = float(np.clip(0.9 * (392 / f0) ** 0.3, 0.4, 1.5)); n = int(_len(dur, t60, True, P) * SR)
    x = ks(f0, n, t60, 0.7, rng, 0.12) + ks(f0 * 2 ** (3 / 1200), n, t60, 0.7, rng, 0.12)
    x = hpf(body(x, [(400, 5, 3), (1600, 4, 2.5), (3000, 3, 2)]), 200) * 0.6
    if not P.get("ring", True): x *= release_after(n, dur, 0.06)
    return fade(x, 0.0005, 0.03)


def cimbalom(m, dur, vel, rng, P):
    """Hammered dulcimer: three strings per course (detuned), felt-hammer excitation, long metallic ring."""
    f0 = float(mtof(m)); t60 = float(np.clip(3.0 * (262 / f0) ** 0.3, 1.5, 5.0)); n = int(min(t60, 4.0) * SR)
    x = sum(ks(f0 * 2 ** (c / 1200), n, t60, 0.6 + 0.3 * vel, rng, 0.12, "hammer") for c in (-2.0, 0.0, 2.5)) / 3
    x = hpf(body(x, [(300, 3, 2), (2500, 3, 1.5)]), 100)
    return fade(x * _ringing(n, dur, P), 0.0005, 0.05)


# ---------- physically modelled plucked strings (opt-in: guqin_pm, pipa_pm … guitar, koto, shamisen, banjo, kalimba) ----------
# Digital waveguides (Smith 1992, "Physical modeling using digital waveguides"): each string is a single delay loop with
# the Karplus–Strong extensions of Jaffe & Smith (1983): a one-pole loss filter, so the high partials die first
# (Välimäki, Huopaniemi, Karjalainen & Jánosy 1996; the b1 + b3·f² decay law of Bensa, Bilbao, Kronland-Martinet & Smith
# 2003); first-order allpasses for stiffness; the pluck position and the finger, nail, pick or hammer in the excitation.
# The delay line is read through a third-order Lagrange interpolator (Laakso, Välimäki, Karjalainen & Laine 1996) that may
# move every sample, so slides, bends and vibrato change the string's length. Tension modulation makes a hard pluck start
# sharp (Tolonen, Välimäki & Karjalainen 2000); a bridge contact shortens the string for the shamisen's sawari. Two
# polarisations, or the strings of a course, run as the rows of one array; the body is an impulse response of modes
# (Karjalainen & Smith 1996). The kalimba and music box are modal (clamped-free bars). Parameter ranges and several preset
# values (t60s, the kalimba's decay law, the bass thump, the pipa's body modes) come from lemo-opuscar
# core/audio/pluck.py (MIT, © LemoLab); the code is written for this file, numpy and scipy only.
def _lagrange(q):
    """Third-order Lagrange weights of taps -1, 0, 1, 2 for a read point q in [0, 1] past tap 0."""
    return np.stack([-q * (q - 1) * (q - 2) / 6, (q + 1) * (q - 1) * (q - 2) / 2, -(q + 1) * q * (q - 2) / 2, (q + 1) * q * (q - 1) / 6], -1)


_LAG = _lagrange(np.arange(1025) / 1024)   # a 1024-step table: the read point is off by at most 1/2048 sample
_SMOOTH = butter(2, 3000, "low", fs=SR, output="sos")
LTI_MAX = 100     # a steady loop shorter than this (samples, above ~480 Hz) finishes with one lfilter: faster there
_PRE = 512        # samples a finger's damping filter runs unheard first: its start-up transient dies away (to rounding)
DAMP_FADE = 0.03  # s over which that filter crossfades in
DAMP_LAG = 0.5    # the delay line's retune follows the crossfade this many periods late (see pm_string)
_LMAX = 1 << 30   # a cap on the block length, for tests: the output does not depend on it


def _ss(u):
    u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)


def _tau(p, a, M, w):
    """Phase delay (samples) at w rad/sample of the loop filter: the loss (1-p)/(1-p z^-1) and M allpasses (a + z^-1)/(1 + a z^-1)."""
    t = np.arctan2(p * np.sin(w), 1 - p * np.cos(w)) / w
    return t + M * (1 - 2 * np.arctan2(a * np.sin(w), 1 + a * np.cos(w)) / w) if M else t


def _tau_mix(p, q, u, a, M, w):
    """Phase delay (samples) at w of the loop filter while it crossfades: (1 − u)·loss(p) + u·loss(q), then the allpasses."""
    z = np.exp(-1j * w); t = -np.angle((1 - u) * (1 - p) / (1 - p * z) + u * (1 - q) / (1 - q * z)) / w
    return t + M * (1 - 2 * np.arctan2(a * np.sin(w), 1 + a * np.cos(w)) / w) if M else t


def _loss(f, T0, Th, pmax=0.97):
    """Loss pole p for a string at f whose fundamental falls 60 dB in T0 s and 3 kHz in Th s (decay rate b1 + b3 f²; the
    fundamental wins when both cannot hold). At most pmax: when the wanted darkening is out of a one-pole's reach, the
    filter is as dark as allowed (the delay line is tuned for whatever phase delay that gives)."""
    s0, fd = 6.91 / T0, max(3000.0, 3 * f)
    b3 = min(max(0.0, (6.91 / Th - s0) / (9e6 - f * f)) if f < 3000 else 0.0, s0 / (f * f))
    R = np.exp(-b3 * (fd * fd - f * f) / f)   # the wanted |H(fd)| / |H(f)| for one trip round the loop
    if R >= 0.99999: return 0.0
    c0, cd, R2 = np.cos(TAU * f / SR), np.cos(TAU * fd / SR), R * R; A, Bq = R2 - 1, R2 * cd - c0; disc = Bq * Bq - A * A
    if disc < 0: return pmax
    ok = [float(r) for r in ((Bq - np.sqrt(disc)) / A, (Bq + np.sqrt(disc)) / A) if 0 <= r < 1]   # the roots are p and 1/p
    return min(ok[0], pmax) if ok else pmax


def _gain(f, T, p):
    """Loop gain for a 60 dB decay in T s at f, allowing for the loss filter's own attenuation there."""
    w = TAU * f / SR; return min(np.exp(-6.91 / (T * f)) * np.sqrt(1 - 2 * p * np.cos(w) + p * p) / (1 - p), 0.99999)


@functools.lru_cache(maxsize=4096)
def _disp(f, B, p):
    """Stiffness: M first-order allpasses (0–4) of coefficient a that move partial k to about k·f·sqrt(1 + B k²), fitted
    over the partials below 5 kHz (Jaffe & Smith 1983; Van Duyne & Smith 1994). Returns (a, M)."""
    if B <= 0: return 0.0, 0
    N0 = SR / f; k = np.arange(2, int(min(24, max(3, 5000 / f))) + 1); fk = k * f * np.sqrt((1 + B * k * k) / (1 + B))
    w0, wk = TAU * f / SR, TAU * fk / SR; want = k * SR / fk - N0; a = -np.linspace(0.005, 0.9, 180)[:, None]; best = (np.inf, 0.0, 0)
    for M in (1, 2, 3, 4):
        err = (((_tau(p, a, M, wk) - _tau(p, a, M, w0)) - want) ** 2 / k).sum(1)
        err[M * (1 - a[:, 0]) / (1 + a[:, 0]) > 0.3 * N0] = np.inf   # most of the loop stays in the delay line
        i = int(np.argmin(err))
        if err[i] < 0.8 * best[0]: best = (err[i], float(a[i, 0]), M)
    return best[1], best[2]


def _filt(p, a, M):
    b, d = np.array([1 - p]), np.array([1.0, -p])
    for _ in range(M): b, d = np.polymul(b, [a, 1.0]), np.polymul(d, [1.0, a])
    return b, d


def _hist(z, s, k=8):
    return z[s - 1::-1][:k] if s > 0 else z[:0]   # the k samples before s, newest first (lfiltic's order)


def _taps(D):
    """A read D samples back: o = ceil(D) (the taps sit o + 1, o, o − 1, o − 2 samples back) and the four weights for
    q = o − D, which is exact, so a fixed and a gliding delay give the very same weights for the same D."""
    o = np.ceil(D); return o.astype(int), _LAG[((o - D) * 1024 + 0.5).astype(int)]


def waveguide(x, Dl, g, filt, tm=0.0, buzz=None, fade=None):
    """Strings as single delay loops, one per row: y = x + g · (F y, Dl samples back); F the loop filter (b, a), the delay
    line read through the Lagrange interpolator, so Dl (per row, or per row and sample) may glide.
    Vectorised a block at a time like ks(): a block is shorter than the shortest loop, so it reads only samples already
    made, and every sample is computed the same way whatever the block length (tests cap it with _LMAX). Each row's line
    starts o_min − o_row samples later in the buffer, so a fixed delay reads all rows from the same columns.
    tm: tension modulation, the relative tension a pluck adds. The pitch sits sqrt(1 + tm·E/E1) sharp and settles as the
    string's energy E falls: E is the mean power of one period on a fixed grid (E1 the first), and sample t of period k
    glides between the values of periods k − 2 and k − 1, all of them finished samples.
    buzz (depth, threshold): where the returning wave passes the threshold the string wraps round a curved bridge and the
    loop shortens by depth samples per unit, smoothed by a 3 kHz low-pass that runs on across blocks (sawari).
    fade (t0, t1, (b, a)): a finger damps the string. From t0 to t1 the loop filter's output crossfades to that filter's,
    which starts _PRE samples earlier from the old one's recent input and output (lfiltic), so its own transient has
    died away before it is heard; from t1 on it is the loop filter. The caller retunes the delay line to match.
    Once the loop is steady (no excitation, delay, gain or filter change left) and short (under LTI_MAX samples), the rest
    is one lfilter per row whose denominator folds in the delay, the taps and the loop filter: the same recursion."""
    S, n = x.shape; b, a = filt; Dl = np.asarray(Dl, float); gv = np.asarray(g, float); var = Dl.ndim == 2
    Dlo, Dhi = float(Dl.min()), float(Dl.max()); dmax = 0.25 * Dlo if buzz else 0.0
    P = int(np.ceil(Dhi)) + 4; L = min(_LMAX, max(1, int((Dlo - dmax) / np.sqrt(1 + tm)) - 3))
    o0 = np.ceil(Dl[:, 0] if var else Dl).astype(int); sh = o0 - o0.min(); W = n + P + int(sh.max())
    wf = np.zeros(S * W); wb = wf.reshape(S, W); base = np.arange(S) * W + P + sh   # row i's w[t] sits at wf[base[i] + t]
    y = np.zeros((S, n)); zi = np.zeros((S, max(len(a), len(b)) - 1)); zi2 = None
    t0, t1, (b2, a2) = fade if fade else (-1, -1, (None, None)); c0 = max(0, t0 - _PRE) if fade else -1
    ix = np.flatnonzero(np.abs(x).max(0)); xe = int(ix[-1]) + 1 if len(ix) else 0
    calm = xe   # from here on nothing changes: no excitation, delay, gain or filter change (the recursion needs a clean past)
    for z in ((Dl,) if var else ()) + ((gv,) if gv.ndim == 2 else ()):
        ch = np.flatnonzero((z[:, 1:] != z[:, :-1]).any(0)); calm = max(calm, int(ch[-1]) + 2 if len(ch) else 0)
    if fade: calm = max(calm, t1 + int(np.ceil(Dhi)) + 8)
    calm += 16
    live = tm > 0; toff = 0
    if live:
        Dp = np.maximum(4, np.round(Dl[:, 0] if var else Dl).astype(int)).tolist(); R0 = float(np.sqrt(1 + tm))
        Rt = [[R0, R0] for _ in range(S)]; E1 = [None] * S; joff = [None] * S   # Rt[i][j]: the value of grid period j

        def Rj(i, j):   # sqrt(1 + tm·E_j/E_1) of row i; 1 from the first period under 0.35 cent on
            if joff[i] is not None and j >= joff[i]: return 1.0
            while len(Rt[i]) <= j:
                jj = len(Rt[i]); d = Dp[i]; w_ = wf[base[i] + (jj - 1) * d:base[i] + jj * d]
                if E1[i] is None: w1 = wf[base[i]:base[i] + d]; E1[i] = float(np.dot(w1, w1)) / d + 1e-30
                r = float(np.sqrt(1 + tm * min(float(np.dot(w_, w_)) / d / E1[i], 1.0)))
                if r < 1 + 2e-4: joff[i] = jj; r = 1.0
                Rt[i].append(r)
                if joff[i] is not None: return 1.0
            return Rt[i][j]
    if buzz: bzi = np.zeros((_SMOOTH.shape[0], S, 2))

    def steady_tail(tt):   # finish with one recursion: steady from tt, a short loop, enough left and enough past
        Dt = np.ceil(Dl[:, min(tt, n - 1)] if var else Dl)
        return buzz is None and tt < n - 4096 and float(Dt.max()) < LTI_MAX and tt > float(Dt.max()) + 16
    ttail = None if live else calm; lti = (not live) and steady_tail(calm); s = 0; fixed = None
    gcol = None if gv.ndim == 2 else gv[:, None]
    while s < n:
        if lti and s >= ttail:   # the steady rest as one recursion per row
            Dt = Dl[:, s] if var else Dl; gt = gv[:, s] if gv.ndim == 2 else gv; o, c = _taps(Dt)
            for i in range(S):
                cb = np.convolve(c[i][::-1], b); den = np.zeros(max(len(a), o[i] - 2 + len(cb))); den[:len(a)] += a
                den[o[i] - 2:o[i] - 2 + len(cb)] -= gt[i] * cb
                y[i, s:] = lfilter(a, den, np.zeros(n - s), zi=lfiltic(a, den, y[i, s - 1::-1][:len(den) - 1]))[0]
            break
        e = min(n, s + L)
        if s < c0: e = min(e, c0)
        if lti: e = min(e, ttail)
        ln = e - s
        if live:
            rho = np.empty((S, ln))
            for i in range(S):   # a block spans at most two grid periods: a straight glide in each
                d = Dp[i]; k0 = s // d; m = min(ln, (k0 + 1) * d - s)
                for kk, a0, a1 in ((k0, 0, m), (k0 + 1, m, ln)):
                    if a0 < a1:
                        if kk < 3: rho[i, a0:a1] = R0
                        else: ra = Rj(i, kk - 2); rho[i, a0:a1] = ra + (Rj(i, kk - 1) - ra) * ((np.arange(s + a0, s + a1) - kk * d) / d)
            if toff == 0 and all(j is not None for j in joff):   # every row has settled: the steady part starts at ttail
                toff = max((joff[i] + 2) * Dp[i] for i in range(S)); ttail = max(calm, toff + 16); lti = steady_tail(ttail)
            D = (Dl[:, s:e] if var else Dl[:, None]) / rho
        elif var and not (Dl[:, s:e] == Dl[:, s:s + 1]).all():
            D = Dl[:, s:e]
        else:
            D = None
        if D is None and not buzz:   # a fixed delay: four shifted slices (the same arithmetic as the gather below)
            Dn = Dl[:, s] if var else Dl
            if fixed is None or (var and not np.array_equal(fixed[0], Dn)):
                o, c = _taps(Dn); col = P + sh - o - 1   # the column of the first tap, less s
                fixed = (np.array(Dn), col, c, [c[:, k:k + 1] for k in range(4)], bool((col == col[0]).all()))
            _, col, c, ck, same = fixed
            if same:
                q = s + int(col[0]); v = wb[:, q:q + ln] * ck[0] + wb[:, q + 1:q + 1 + ln] * ck[1] + wb[:, q + 2:q + 2 + ln] * ck[2] + wb[:, q + 3:q + 3 + ln] * ck[3]
            else:
                v = np.empty((S, ln))
                for i in range(S):
                    q = s + int(col[i]); c0, c1, c2, c3 = c[i].tolist()
                    v[i] = wb[i, q:q + ln] * c0 + wb[i, q + 1:q + 1 + ln] * c1 + wb[i, q + 2:q + 2 + ln] * c2 + wb[i, q + 3:q + 3 + ln] * c3
        else:
            if D is None: D = Dl[:, s:e] if var else np.broadcast_to(Dl[:, None], (S, ln))
            o, C = _taps(D); j = (np.arange(s, e) - o - 1) + base[:, None]
            v = wf[j] * C[..., 0] + wf[j + 1] * C[..., 1] + wf[j + 2] * C[..., 2] + wf[j + 3] * C[..., 3]
            if buzz:   # the contact shortens the loop, smoothly: a 3 kHz low-pass whose state runs on across blocks
                dd = np.minimum(buzz[0] * np.maximum(v - buzz[1], 0.0), 0.9 * dmax); sm, bzi = sosfilt(_SMOOTH, dd, axis=-1, zi=bzi)
                o, C = _taps(D - np.minimum(sm, dmax)); j = (np.arange(s, e) - o - 1) + base[:, None]
                v = wf[j] * C[..., 0] + wf[j + 1] * C[..., 1] + wf[j + 2] * C[..., 2] + wf[j + 3] * C[..., 3]
        yb = y[:, s:e]; np.multiply(gv[:, s:e] if gcol is None else gcol, v, out=yb)
        if s < xe: yb += x[:, s:e]
        if s == c0:   # the damping filter starts from the old one's recent input and output
            zi2 = np.stack([lfiltic(b2, a2, _hist(wf[base[i]:base[i] + n], s), _hist(y[i], s)) for i in range(S)])
        wo, zi = lfilter(b, a, yb, axis=-1, zi=zi)
        if zi2 is not None:   # the crossfade, sample by sample (the same arithmetic whatever the block)
            wo2, zi2 = lfilter(b2, a2, yb, axis=-1, zi=zi2); u = np.clip((np.arange(s, e) - t0) / (t1 - t0), 0.0, 1.0)
            wo = (1 - u) * wo + u * wo2
            if e >= t1: b, a, zi, zi2 = b2, a2, zi2, None   # from here on the damping filter alone
        for i in range(S): wf[base[i] + s:base[i] + e] = wo[i]
        if live and toff and e >= toff: live = False
        s = e
    return y


def _excite(N, beta, kind, bright, rng, noise):
    """One period (N samples) of the bridge force a pluck at beta (of the length, from the bridge) starts: an ideal pluck
    gives a pulse beta·N wide (partial k ~ sin(k π beta) / k), a strike its derivative (a pulse pair). The finger, nail,
    pick or hammer rounds it (a low-pass that opens with bright) and a little noise roughens it. Peak 1."""
    N = max(4, int(round(N))); k = min(N - 1, max(1, int(round(beta * N))))
    if kind == "hammer":   # a cotton-wrapped head in contact for tc: a half-sine force, then the same force from the far side
        tc = max(2, int((0.35 + 1.6 * (1 - bright)) * 1e-3 * SR)); h = np.sin(np.pi * np.arange(tc) / tc)
        e = np.zeros(N + tc); e[:tc] += h; e[k:k + tc] -= h
    else:
        e = np.zeros(N); e[:k] = 1.0; e -= e.mean(); e += noise * rng.standard_normal(N)
        fc = {"finger": 700 + 9000 * bright ** 2, "nail": 1500 + 12000 * bright ** 1.5, "pick": 2500 + 14000 * bright}[kind]
        e = sosfilt(butter(2 if kind == "finger" else 1, min(fc, 0.45 * SR), "low", fs=SR, output="sos"), np.concatenate([e, np.zeros(N // 2)]))
    e -= e.mean(); return e / (np.abs(e).max() + 1e-12)


_PM_BODY = {}


def _pm_body(name, S):
    """The body as an impulse response (Karjalainen & Smith 1996): the plate's mean response and its modes (Hz, Q, dB at the
    peak) as decaying cosines (an admittance: in phase with the mean response at resonance, so no deep notch between
    modes), a short tail of dense high modes (lo, hi Hz, decay s, dB), all radiated through a first-order
    high-pass at frad (a plate radiates pressure as the rate of change of its motion). Fixed seed, cached."""
    if name not in _PM_BODY:
        modes, direct, (lo, hi, dec, db) = S["body"]; g = np.random.default_rng([crc("pm-body"), crc(name)])
        n = int(min(0.4, 6 * max(q / (np.pi * f) for f, q, _ in modes) + 0.02) * SR); t = secs(n); h = np.zeros(n); h[0] = direct
        for f, q, gdb in modes:
            tau = q / (np.pi * f); h += 2 * 10 ** (gdb / 20) / (tau * SR) * np.cos(TAU * f * t + g.uniform(-0.3, 0.3)) * np.exp(-t / tau)
        k = min(n, int(8 * dec * SR)); nz = bpf(g.standard_normal(k), lo, hi) * np.exp(-secs(k) / dec)
        h[:k] += nz * 10 ** (db / 20) * direct / np.sqrt(np.sum(nz ** 2))
        _PM_BODY[name] = hpf(h, S["frad"], 1)
    return _PM_BODY[name]


# t60 (T, f_ref, expo, lo, hi): the fundamental's 60 dB decay, T·(f_ref / f)^expo clipped to [lo, hi]; thi: the 60 dB decay
# at 3 kHz (how long the brightness lasts); B: stiffness at f_ref, rising with pitch; pos: the pluck point (fraction of
# the length from the bridge); exc: finger | nail | pick | hammer; bright: (base, + per velocity); rows (cents, t60
# ratio, level, own pluck): the two polarisations of a string, or the strings of a course; tm: cents sharp at the attack of
# a velocity-1 pluck; ring: rings past the note by default; rel: damping time (s) at the note's end; cap: longest render
# (s); frad: radiation corner (Hz, small bodies higher); body: (modes (Hz, Q, dB), mean level, tail (lo, hi, decay, dB));
# extras: click (nail or pick tick), squeak (a finger travelling along silk), thump (a finger on a bass), skin (a
# plectrum hitting a skin head), buzz (sawari)
PM_STRINGS = {
    "guqin_pm": dict(t60=(7.0, 110, 0.45, 3.0, 11.0), thi=0.75, B=1e-5, pos=0.11, exc="finger", bright=(0.35, 0.35), noise=0.04,
                     rows=((0, 1.0, 1.0, 0), (0.5, 1.5, 0.5, 0)), tm=4, ring=True, rel=0.25, cap=8.0, frad=700.0, squeak=1.0,
                     body=([(98, 7, 6), (205, 9, 5), (310, 8, 2), (445, 8, 3), (700, 6, 1), (1050, 5, -1), (1650, 4, -3)], 0.6, (600, 4000, 0.006, -14))),
    "pipa_pm": dict(t60=(1.8, 220, 0.35, 0.6, 3.0), thi=1.0, B=4e-5, pos=0.09, exc="nail", bright=(0.6, 0.4), noise=0.05,
                    rows=((0, 1.0, 1.0, 0), (0.8, 1.5, 0.45, 0)), tm=6, ring=True, rel=0.07, cap=4.0, frad=1200.0, click=0.3,
                    body=([(185, 8, 3), (430, 7, 5), (880, 6, 3), (1800, 5, 3), (3300, 4, 2)], 0.5, (1200, 6000, 0.004, -12))),
    "harp_pm": dict(t60=(5.0, 262, 0.4, 1.5, 10.0), thi=0.7, B=2e-5, pos=0.33, exc="finger", bright=(0.45, 0.3), noise=0.02,
                    rows=((0, 1.0, 1.0, 0), (0.5, 1.5, 0.5, 0)), tm=3, ring=True, rel=0.2, cap=8.0, frad=700.0,
                    body=([(130, 6, 4), (260, 8, 3), (480, 7, 2), (950, 5, 0), (2000, 4, -3)], 0.7, (800, 5000, 0.008, -16))),
    "nylon_pm": dict(t60=(3.2, 196, 0.4, 1.2, 6.0), thi=0.8, B=1.5e-5, pos=0.2, exc="finger", bright=(0.25, 0.35), noise=0.03,
                     rows=((0, 1.0, 1.0, 0), (0.5, 1.6, 0.5, 0)), tm=3, ring=False, rel=0.12, cap=6.0, frad=800.0,
                     body=([(98, 12, 8), (195, 10, 7), (245, 12, 3), (390, 9, 3), (550, 8, 2), (800, 6, 0), (1250, 5, -2), (2500, 4, -4)], 0.45, (1000, 5000, 0.005, -14))),
    "guitar": dict(t60=(4.5, 196, 0.4, 1.5, 8.0), thi=1.5, B=6e-5, pos=0.12, exc="pick", bright=(0.6, 0.4), noise=0.03,
                   rows=((0, 1.0, 1.0, 0), (0.6, 1.6, 0.5, 0)), tm=4, ring=False, rel=0.12, cap=6.0, frad=800.0, click=0.15,
                   body=([(100, 12, 8), (200, 10, 7), (280, 10, 3), (380, 9, 3), (500, 8, 2), (700, 6, 1), (1000, 6, 0), (1500, 5, -2), (2500, 4, -4)], 0.45, (1200, 6000, 0.005, -13))),
    "ukulele_pm": dict(t60=(1.4, 392, 0.4, 0.5, 3.0), thi=0.6, B=1e-5, pos=0.18, exc="finger", bright=(0.45, 0.4), noise=0.04,
                       rows=((0, 1.0, 1.0, 0), (0.6, 1.5, 0.45, 0)), tm=3, ring=False, rel=0.08, cap=3.0, frad=1200.0,
                       body=([(250, 9, 4), (450, 8, 4), (700, 7, 3), (1100, 6, 2), (2000, 5, 1)], 0.5, (1200, 6000, 0.0035, -12))),
    "upright_pm": dict(t60=(2.6, 55, 0.3, 1.0, 4.0), thi=0.5, B=3e-5, pos=0.22, exc="finger", bright=(0.05, 0.25), noise=0.02,
                       rows=((0, 1.0, 1.0, 0), (0.4, 1.4, 0.45, 0)), tm=14, ring=False, rel=0.06, cap=4.0, frad=500.0, thump=1.0,
                       body=([(60, 6, 6), (100, 7, 6), (140, 8, 3), (200, 6, 3), (400, 5, 0), (800, 4, -4)], 0.5, (300, 2500, 0.008, -16))),
    "balalaika_pm": dict(t60=(1.1, 392, 0.3, 0.4, 2.0), thi=0.8, B=3e-5, pos=0.13, exc="nail", bright=(0.6, 0.35), noise=0.05,
                         rows=((-1.0, 1.0, 1.0, 1), (1.0, 1.15, 0.85, 1)), tm=6, ring=True, rel=0.05, cap=2.5, frad=1200.0, click=0.15,
                         body=([(330, 7, 4), (560, 7, 4), (1100, 6, 3), (1900, 5, 3), (3200, 4, 1)], 0.5, (1500, 7000, 0.003, -12))),
    "cimbalom_pm": dict(t60=(4.0, 262, 0.35, 1.5, 7.0), thi=1.5, B=1.2e-4, pos=0.12, exc="hammer", bright=(0.5, 0.45), noise=0.0,
                        rows=((-1.5, 1.0, 1.0, 1), (0.0, 1.25, 0.9, 1), (1.5, 1.1, 0.95, 1)), tm=2, ring=True, rel=0.2, cap=6.0, frad=800.0,
                        body=([(140, 6, 3), (290, 7, 3), (520, 6, 2), (900, 5, 2), (1700, 5, 1), (2800, 4, 0)], 0.6, (1500, 8000, 0.01, -12))),
    "koto": dict(t60=(3.5, 294, 0.35, 1.2, 6.0), thi=0.8, B=2e-5, pos=0.12, exc="pick", bright=(0.45, 0.4), noise=0.04,
                 rows=((0, 1.0, 1.0, 0), (0.6, 1.5, 0.5, 0)), tm=6, ring=True, rel=0.15, cap=6.0, frad=1000.0, click=0.15,
                 body=([(150, 7, 5), (290, 8, 4), (480, 7, 3), (700, 6, 2), (1300, 5, 1), (2400, 4, -2)], 0.55, (1000, 6000, 0.005, -13))),
    "shamisen": dict(t60=(1.5, 262, 0.3, 0.6, 2.5), thi=0.6, B=1.5e-5, pos=0.08, exc="pick", bright=(0.65, 0.35), noise=0.06,
                     rows=((0, 1.0, 1.0, 0), (0.8, 1.4, 0.4, 0)), tm=8, ring=True, rel=0.08, cap=3.0, frad=1200.0, skin=0.5, buzz=0.6,
                     body=([(260, 4, 5), (520, 4, 4), (780, 4, 3), (1250, 4, 3), (2100, 3, 2), (3300, 3, 1)], 0.5, (800, 5000, 0.006, -10))),
    "banjo": dict(t60=(1.1, 294, 0.3, 0.5, 1.8), thi=1.0, B=8e-5, pos=0.08, exc="pick", bright=(0.8, 0.2), noise=0.04,
                  rows=((0, 1.0, 1.0, 0), (1.0, 1.4, 0.5, 0)), tm=5, ring=True, rel=0.05, cap=2.5, frad=2000.0, skin=0.3,
                  body=([(360, 5, 6), (590, 5, 5), (820, 5, 4), (1050, 5, 3), (1600, 4, 3), (2500, 4, 2), (3500, 3, 1)], 0.45, (1500, 8000, 0.003, -10))),
}


def _pm_out(tone, tr, body, taper=0.0):
    """Tone and transients through the body, 25 Hz high-pass, faded ends, the tone's peak at 1 (a click or slap rides on
    top at its own level, so it never pushes the note down). taper (s): a longer fade at the end, so a note cut before it
    has died away ends in a decay, not a cut."""
    n = len(tone); z = np.zeros((2, n)); z[0] = hpf(oaconvolve(tone, body)[:n], 25)
    k = np.flatnonzero(tr); k = int(k[-1]) + 1 if len(k) else 0
    if k:   # a transient is short: its own convolution, with room for the high-pass to settle
        c = oaconvolve(tr[:k], body); m = min(n, len(c) + int(0.1 * SR)); u = np.zeros(m); u[:min(m, len(c))] = c[:m]; z[1, :m] = hpf(u, 25)
    z = fade(z, 0.001, 0.03)
    if taper:
        k = min(n, int(taper * SR)); z[:, -k:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, k + 1) / k)
    pk = float(np.abs(z[0]).max()); return (z[0] + z[1]) / pk if pk > 1e-9 else z[0] + z[1]


def _loud(y, w=int(0.4 * SR)):
    """Mean power of the loudest 400 ms."""
    c = np.concatenate([[0.0], np.cumsum(y * y)]); return max(float((c[w:] - c[:-w]).max()) if len(y) > w else float(c[-1]), 1e-20) / w


_WARNED = set()


def _knob(P, key, default, lo, hi):
    """A knob as a number in [lo, hi]; the default when it is missing or not a finite number."""
    try: v = float(P.get(key, default))
    except (TypeError, ValueError): return default
    return float(np.clip(v, lo, hi)) if np.isfinite(v) else default


def _vib(v):
    """vib: true (5 Hz, 15 cents), cents, or [Hz, cents, delay s] → (Hz, cents, delay), each clipped to a sane range."""
    out = [5.0, 15.0, 0.2]; vals = list(v) if isinstance(v, (list, tuple)) else ([] if v is True else [None, v])
    for i, (lo, hi) in enumerate(((0.1, 20.0), (0.0, 1200.0), (0.0, 10.0))):
        if i < len(vals) and vals[i] is not None:
            try: z = float(vals[i])
            except (TypeError, ValueError): continue
            if np.isfinite(z): out[i] = float(np.clip(z, lo, hi))
    return tuple(out)


def _warn_high(name, what="a note goes above 6 kHz (MIDI 114)"):
    if (name, what) not in _WARNED:   # once per voice and reason
        _WARNED.add((name, what)); print(f"music: warning: {name}: {what}; the string stops there", file=sys.stderr)


def pm_string(name, m, dur, vel, rng, P):
    """A string of the PM_STRINGS table. Knobs (params or a note's): ring, damp, mute; slide, bend (semitones, ±36);
    vib (cents, or [Hz, cents, delay s]); yin, nao; harm (true, or the harmonic 2–8); trem (Hz up to 40, or true:
    re-pluck the same string); pos (0.03–0.5), bright (0–1), decay (0.02–20, × the ring); buzz (0–1, the shamisen).
    The tone peaks at 1: the engine's level and velocity do the rest."""
    S = PM_STRINGS[name]; mute = bool(P.get("mute")); ring = bool(P.get("ring", S["ring"])) and not P.get("damp") and not mute
    f0 = float(mtof(m))
    if f0 > SR / 8: _warn_high(name); f0 = SR / 8
    Tr, fref, ex, lo, hi = S["t60"]; dec = _knob(P, "decay", 1.0, 0.02, 20.0); k = 1; seed = None
    if P.get("harm"):   # a harmonic: the string k times longer, touched at 1/k (the guqin picks k so the string is one of its own)
        k = 0 if P["harm"] is True else int(round(_knob(P, "harm", 2.0, 2.0, 8.0)))
        if not k: k = next((q for q in (2, 3, 4, 5, 6, 8) if m - 12 * np.log2(q) <= 52), 8) if name == "guqin_pm" else 2   # 正调 open strings C2 … D3
        seed = int(rng.integers(1 << 31))
    B = S["B"] * f0 / k / fref; fb = f0 / k / np.sqrt((1 + B * k * k) / (1 + B))   # partial k of the string lands on the note
    T0, Th = float(np.clip(Tr * (fref / fb) ** ex, lo, hi)) * dec, S["thi"] * dec
    if mute: T0, Th = 0.15, 0.05
    rows = S["rows"]; R = len(rows); trem = P.get("trem")
    rate = (_knob(P, "tremolo_rate", 12.0, 1.0, 40.0) if trem is True else _knob(P, "trem", 0.0, 0.0, 40.0)) if trem else 0.0
    Lnat = 0.9 * T0 * max(r[1] for r in rows); cap = min(S["cap"] * max(1.0, dec), 20.0)   # a ring lasts to about −55 dB
    L = min(cap, max(Lnat, dur + 0.3)) if ring else dur + 1.2 * (0.05 if mute else S["rel"]) + 0.03
    n = int(min(L, float(P.get("_n", L))) * SR); t = secs(n); taper = min(1.0, 0.25 * L) if ring and L < Lnat and "_n" not in P else 0.0
    s = np.zeros(n)   # pitch in semitones: slide in, bend after the pluck, vibrato (吟 yin small, 猱 nao wide)
    sl, bd = _knob(P, "slide", 0.0, -36.0, 36.0), _knob(P, "bend", 0.0, -36.0, 36.0)
    if sl: s += sl * (1 - _ss((t - 0.04) / 0.25))
    if bd: s += bd * _ss((t - min(0.25, 0.35 * dur)) / max(min(0.3, 0.4 * dur), 1e-3))
    if P.get("yin"): s += 0.2 * np.sin(TAU * 4.5 * t) * np.clip((t - 0.2) / 0.3, 0, 1)
    if P.get("nao"): s += 0.5 * np.sin(TAU * 2.5 * t) * np.clip((t - 0.15) / 0.3, 0, 1)
    if P.get("vib"): hz, ce, dl = _vib(P["vib"]); s += ce / 100 * np.sin(TAU * hz * t) * np.clip((t - dl) / 0.3, 0, 1)
    moved = bool(s.any()); p = _loss(fb, T0, Th); a, M = _disp(fb, B, p)
    cents = np.array([r[0] for r in rows], float) + rng.uniform(-0.3, 0.3, R) * (np.arange(R) > 0)
    wt = np.array([r[2] * r[1] for r in rows]); cents -= (cents * wt).sum() / wt.sum()   # tuned by ear to the blend of the rows
    fr = fb * 2 ** ((s[None, :] / 12 if moved else 0) + cents[:, None] / 1200)
    if fr.max() > SR / 8: _warn_high(name)
    fr = np.clip(fr, 8.0, SR / 8); Dl = SR / fr - _tau(p, a, M, TAU * fr / SR)   # (R, n) when the pitch moves, else (R, 1)
    g = np.array([_gain(fb, T0 * r[1], p) for r in rows])
    b0, b1 = S["bright"]; br = _knob(P, "bright", b0 + b1 * vel, 0.0, 1.0); pos = _knob(P, "pos", S["pos"], 0.03, 0.5); N = SR / fb
    x = np.zeros((R, n)); gs = np.repeat(g[:, None], n, 1) if rate or not ring else g
    hits = [(0, 1.0)] + ([(int(j / rate * SR), (1.0, 0.8, 0.9, 0.75)[j % 4] * (0.9 + 0.1 * rng.random())) for j in range(1, int(dur * rate - 0.3) + 1)] if rate else [])
    for i0, hv in hits:   # the pluck; for trem (轮指 / 摇指) the same string again and again
        if i0 >= n: break
        e = None
        for i, r in enumerate(rows):
            if e is None or r[3]:   # the strings of a course are plucked one by one; the polarisations share a pluck
                e = _excite(N / k, pos * (1 + rng.uniform(-0.06, 0.06)), S["exc"], br * (0.85 + 0.15 * hv), rng, S["noise"])
                if k > 1:   # the finger at 1/k: the string moves with period N/k, so only the multiples of k sound
                    e1, e = e, np.zeros(int(N) + len(e))
                    for q in range(k): o = int(round(q * N / k)); e[o:o + len(e1)] += e1
                    e /= np.abs(e).max()
            x[i, i0:i0 + len(e)] += r[2] * hv * e[:n - i0]
        if i0:   # the nail catches the ringing string before it plucks: the loop gain dips for a period
            c = max(0, i0 - int(N)); gs[:, c:i0] *= 1 - 0.6 * np.hanning(i0 - c + 2)[1:-1]
    fd = None
    if not ring and dur * SR < n - 10:   # a finger damps the string inside the loop: over 15 ms the loop gain falls, and
        # over DAMP_FADE a darker loss filter crossfades in (never brighter than the ringing string; its pole 0.9 at most)
        ri = int(dur * SR); trel = 0.05 if mute else S["rel"]; pr = max(_loss(fb, trel, trel / 4, 0.9), p)
        u = np.clip((np.arange(n) - ri) / (0.015 * SR), 0, 1); gs = gs * (1 - u) + _gain(fb, trel, pr) * u
        if pr > p:   # that filter delays the wave a few samples more, and the delay line gives them back (at the lowest
            # partial that sounds) half a period behind the crossfade: a sample read now went through the filter a period
            # ago, so the loop's pitch stays within about 5 cents of the ring all through the damp
            K = int(DAMP_FADE * SR); ul = np.clip((np.arange(ri, n) - ri - DAMP_LAG * Dl[:, [min(ri, Dl.shape[1] - 1)]]) / K, 0, 1)
            Dl = np.repeat(Dl, n, 1) if Dl.shape[1] == 1 else Dl.copy(); wk = TAU * k * (fr[:, ri:] if fr.shape[1] > 1 else fr) / SR
            Dl[:, ri:] = np.where(ul > 0, Dl[:, ri:] - (_tau_mix(p, pr, ul, a, M, wk) - _tau(p, a, M, wk)), Dl[:, ri:])
            fd = (ri, ri + K, _filt(pr, a, M))
    nz = 0.0
    if S.get("squeak") and (sl or bd):   # 走手音: the finger travelling along silk rubs the string
        nz = bpf(rng.standard_normal(n), 1500, 5000) * np.clip(np.abs(np.gradient(s)) * SR / 8, 0, 1) * 0.03 * S["squeak"]; x[0] += nz
    bz = _knob(P, "buzz", S["buzz"], 0.0, 1.0) if "buzz" in S else 0.0; tm = (2 ** (S.get("tm", 0) / 600) - 1) * vel * vel
    buzz = (4.0 * bz * vel, 0.02 / max(vel, 0.05)) if bz > 0 else None   # a harder pluck swings wider: touches more, longer
    if Dl.min() < 4: _warn_high(name, "a bend or slide goes higher than the string can reach"); Dl = np.maximum(Dl, 4.0)
    y = waveguide(x, Dl if Dl.shape[1] > 1 else Dl[:, 0], gs, _filt(p, a, M), tm, buzz, fd).sum(0) + 0.3 * nz
    tr = np.zeros(n)   # transients through the same body: the nail or pick tick, a plectrum on skin, a finger on a bass
    if S.get("click"): tr += burst(rng, n, 2500, 9000, 0.0005, S["click"] * br)
    if S.get("skin"): tr += burst(rng, n, 250, 3500, 0.006, S["skin"] * br)
    if S.get("thump"):
        kk = min(n, int(0.08 * SR)); tr[:kk] += 0.35 * S["thump"] * np.sin(TAU * 70 * t[:kk]) * np.exp(-t[:kk] / 0.012)
        tr += burst(rng, n, 900, 3000, 0.003, 0.3 * S["thump"] * max(0.0, vel - 0.55))
    y = _pm_out(y, tr, _pm_body(name, S), taper)
    if k > 1:   # as loud as a plucked note of the same pitch and velocity (loudest 400 ms)
        ref = pm_string(name, m, dur, vel, np.random.default_rng(seed), {**P, "harm": False, "trem": None, "_n": 0.45})
        y *= np.sqrt(_loud(ref) / _loud(y))
    return y


PM_BARS = {   # t60 of mode 1; r2, r3: ratios of modes 2 and 3 (± spread per pitch; a uniform cantilever is 1 : 6.27 : 17.55, a
    # kalimba tine held over its bridge sits lower, a lead-weighted bass tooth higher); a2, a3: level at velocity 1 and
    # decay relative to mode 1; twin: a second tooth (cents, level); click: the thumbnail or pin; detune: ± cents per pitch
    "kalimba": dict(t60=(2.6, 330, 0.4, 0.9, 5.0), detune=1.5, r2=(5.9, 0.15), r3=(16.8, 0.4), a2=(0.45, 0.15), a3=(0.1, 0.05), twin=None, click=0.2, frad=500.0,
                    body=([(215, 6, 6), (520, 7, 3), (1050, 6, 1), (2200, 5, -2)], 0.5, (2000, 7000, 0.003, -16))),
    "musicbox_pm": dict(t60=(3.0, 1047, 0.4, 1.0, 5.0), detune=3.0, r2=(6.27, 0.05), r3=(17.55, 0.2), a2=(0.4, 0.12), a3=(0.12, 0.04), twin=(2.0, 0.35), click=0.3,
                        frad=900.0, body=([(430, 6, 5), (900, 7, 4), (1550, 6, 3), (2600, 5, 1)], 0.45, (1500, 8000, 0.003, -10))),
}


def pm_bar(name, m, dur, vel, rng, P):
    """A tine or comb tooth of the PM_BARS table: three cantilever modes, a thumbnail or pin click, the box. It reads only
    ring (default) or damp, and decay (0.02–20, × the ring). The tone peaks at 1."""
    S = PM_BARS[name]; f0 = float(mtof(m)); Tr, fref, ex, lo, hi = S["t60"]; dec = _knob(P, "decay", 1.0, 0.02, 20.0)
    T = float(np.clip(Tr * (fref / f0) ** ex, lo, hi)) * dec
    g = np.random.default_rng([crc(name), int(round(m * 100))])   # one tine or tooth per pitch: its own tuning and ratios
    heavy = float(np.clip((72 - m) / 24, 0, 1)) if name == "musicbox_pm" else 0.0; f0 *= 2 ** (g.uniform(-1, 1) * S["detune"] / 1200)
    r2 = S["r2"][0] + g.uniform(-1, 1) * S["r2"][1] + 2.5 * heavy; r3 = S["r3"][0] + g.uniform(-1, 1) * S["r3"][1] + 6 * heavy
    ring = bool(P.get("ring", True)) and not P.get("damp"); cap = min(5.0 * max(1.0, dec), 20.0); Lr = max(T, dur + 0.2)
    n = int((min(Lr, cap) if ring else dur + 0.15) * SR); tau = T / 6.91; b = 0.6 + 0.4 * vel
    modes = [(1.0, 1.0, tau), (r2, S["a2"][0] * b * b, tau * S["a2"][1]), (r3, S["a3"][0] * b ** 3, tau * S["a3"][1])]
    if S["twin"]: modes.append((2 ** (S["twin"][0] / 1200), S["twin"][1], 0.9 * tau))
    x = _pm_out(modal(f0, n, modes), burst(rng, n, 2500, 11000, 0.0006, S["click"] * (0.4 + 0.6 * vel)), _pm_body(name, S),
                min(1.0, 0.25 * n / SR) if ring and Lr > cap else 0.0)
    return x * np.clip(1 - (secs(n) - dur) / 0.12, 0, 1) ** 2 if not ring else x


def _pm(name):
    fn = pm_bar if name in PM_BARS else pm_string
    return lambda m, dur, vel, rng, P: fn(name, m, dur, vel, rng, P)


# ---------- bowed ----------
def strings(m, dur, vel, rng, P):
    """String section: six detuned saw players with their own vibrato and entry, a body EQ, bow noise; stereo spread.
    marcato: short bite and accent; attack / release in seconds override the legato swell."""
    f0 = float(mtof(m)); marc = bool(P.get("marcato"))
    att = float(P.get("attack", 0.03 if marc else 0.22)); rel = float(P.get("release", 0.12 if marc else 0.35))
    n = int((dur + rel) * SR); t = secs(n); V = int(P.get("voices", 6)); X = np.zeros((2, n)); inc = np.zeros(n)
    for v in range(V):
        det = rng.uniform(-9, 9); vr = rng.uniform(4.8, 6.2); vp = rng.uniform(0, TAU); vd = rng.uniform(0.0015, 0.003)
        f = f0 * 2 ** (det / 1200) * (1 + vd * np.sin(TAU * vr * t + vp) * np.clip(t / 0.4, 0, 1))
        x = saw(f, n, rng.random()); k = int(rng.uniform(0, 0.02 if not marc else 0.006) * SR)
        if k: x = np.concatenate([np.zeros(k), x[:-k]])
        X += pan2(x, -0.7 + 1.4 * v / max(1, V - 1)); inc += x * x
    X = unbeat(X / V, inc / V ** 2)
    e = np.clip(t / att, 0, 1) ** 1.5
    if marc: e = e * (1 + 0.5 * vel * np.exp(-np.maximum(t - att, 0) / 0.07)) * (0.75 + 0.25 * np.exp(-t / 0.3))
    e *= release_after(n, dur, rel)
    X = hpf(lpf(body(X, [(300, 4, 1.5), (2500, 3, 1.2)]), 2500 + 4000 * vel), 60)
    X += bpf(rng.standard_normal((2, n)), 2000, 7000) * (0.02 + (0.05 * np.exp(-t / 0.05) if marc else 0))
    return fade(X * e, 0.001, 0.02)


BOWED = {   # body modes (Hz, dB, Q), lowpass, highpass, vibrato (Hz, cents, delay s), bow noise, drive
    "violin": dict(modes=[(290, 5, 3), (470, 4, 3), (1050, -3, 2), (2800, 7, 1.2), (4600, 3, 2)], lp=7500, hp=190, vib=(5.8, 22, 0.18), noise=0.6, drive=0),
    "fiddle": dict(modes=[(290, 5, 3), (470, 4, 3), (1800, 3, 2), (2800, 7, 1.2)], lp=8500, hp=190, vib=(6.2, 10, 0.25), noise=1.0, drive=0),
    "cello": dict(modes=[(100, 4, 2), (205, 6, 3), (420, 3, 2), (1500, 4, 1.5)], lp=3800, hp=55, vib=(5.2, 18, 0.2), noise=0.5, drive=0),
    "banhu": dict(modes=[(1100, 9, 4), (2400, 7, 3), (3600, 4, 3)], lp=6500, hp=420, vib=(6.3, 42, 0.12), noise=0.8, drive=1.5),
}


def bowed(f, amp, onsets, P, rng):
    """Solo bow: a sawtooth (Helmholtz motion) through the instrument's body, bow hair noise, rosin bite at each stroke."""
    B = BOWED[P["_name"]]; n = len(f); fm = float(np.median(f)); k = np.exp(-TAU * 6 * fm / SR)
    x = lfilter([1 - k], [1, -k], saw(f, n, rng.random())) * 2.5   # the bridge rounds the Helmholtz corner: −6 dB/oct above 6 f0
    bite = np.zeros(n)
    for i, v, leg in onsets:
        k = min(n - i, int(0.06 * SR)); bite[i:i + k] += (0.25 if leg else 0.6 + 0.6 * bool(P.get("marcato"))) * v * np.exp(-secs(k) / 0.015)
    x = x * (1 + 0.3 * bite) + bpf(rng.standard_normal(n), 1500, 7000) * 0.05 * B["noise"] * (1 + 3 * bite)
    x = hpf(lpf(body(x, B["modes"]), min(B["lp"], max(1200.0, 20 * float(np.median(f))))), B["hp"])   # low notes are darker
    return hpf(drive(x * amp, B["drive"]), 60) if B["drive"] else x * amp   # tanh of a lopsided wave leaves DC


def winds(f, amp, onsets, P, rng):
    """Flute family and double reeds, chosen by P["_name"]: flute xiao whistle suona."""
    name = P["_name"]; n = len(f); ph = phase(f, n); nz = rng.standard_normal(n); fm = float(np.median(f))
    chiff = np.zeros(n)
    for i, v, leg in onsets:
        k = min(n - i, int(0.05 * SR)); chiff[i:i + k] += (0.3 if leg else 1.0) * v * np.exp(-secs(k) / 0.015)
    if name == "suona":   # conical double reed: bright pulse + saw, strong formants, a hard edge
        x = 0.6 * pulse(f, n, 0.33) + 0.5 * saw(f, n)
        x = drive(x, 2.5); x = hpf(lpf(body(x, [(1250, 10, 2.5), (2700, 8, 2.5), (4300, 4, 3)]), 8000), 350)
        x += bpf(nz, 2000, 6000) * 0.05 * (1 + chiff)
    elif name == "xiao":  # low end-blown: nearly pure, a lot of breath around the pitch, slow onset
        x = np.sin(TAU * ph) + 0.05 * np.sin(2 * TAU * ph)
        x += bpf(nz, fm * 0.8, fm * 1.3) * 0.9 + lpf(hpf(nz, 500), 3000) * (0.12 + 0.2 * chiff)
        x = lpf(x, 3200)
    elif name == "whistle":
        tin = P.get("kind", "lips") == "tin"
        x = np.sin(TAU * ph) + (0.2 * np.sin(2 * TAU * ph) + 0.12 * np.sin(3 * TAU * ph) if tin else 0.03 * np.sin(2 * TAU * ph))
        x += hpf(nz, 2500) * (0.03 + (0.1 if tin else 0.02) * chiff) + bpf(nz, fm * 0.9, fm * 1.1) * 0.15
    else:                 # flute
        x = np.sin(TAU * ph) + 0.12 * np.sin(2 * TAU * ph) + 0.04 * np.sin(3 * TAU * ph)
        x += bpf(nz, fm * 0.85, fm * 1.2) * 0.35 + hpf(nz, 3000) * (0.03 + 0.12 * chiff)
        x = lpf(x, 6000)
    return x * amp


def sub808(f, amp, onsets, P, rng):
    """808 bass: a sine that drops from ~+7 semitones at each fresh hit, glides on legato notes, decays per hit, and is
    saturated (drive) so laptop speakers hear its harmonics."""
    n = len(f); t = secs(n); drop = float(P.get("drop", 7)); dec = float(P.get("decay", 1.2))
    s = np.zeros(n); d = np.ones(n); click = np.zeros(n)
    for i, v, leg in onsets:
        if leg: continue
        k = n - i; tt = t[:k]; s[i:] = drop * np.exp(-tt / 0.03); d[i:] = np.exp(-tt / dec)
        c = min(k, int(0.01 * SR)); click[i:i + c] += v * np.exp(-tt[:c] / 0.002)
    x = np.sin(TAU * phase(f * 2 ** (s / 12), n)) * d + bpf(rng.standard_normal(n), 1000, 4000) * click * 0.3
    return lpf(drive(x * amp, float(P.get("drive", 2.5))), 5000)


# ---------- brass ----------
def brass(m, dur, vel, rng, P):
    """Brass section, three players. Additive with the Risset rule: harmonic k rises as the envelope to the power
    1 + (k-1)·c, so loud = bright; lips start ~40 cents flat. stab: short and punchy. swell: slow crescendo.
    mute: harmon-muted (nasal, thin)."""
    f0 = float(mtof(m)); swell, stab, mute = bool(P.get("swell")), bool(P.get("stab")), bool(P.get("mute"))
    att = float(P.get("attack", 0.5 if swell else (0.012 if stab else 0.035))); rel = float(P.get("release", 0.07 if stab else 0.16))
    n = int((dur + rel) * SR); t = secs(n)
    e = np.clip(t / att, 0, 1) ** (2 if swell else 1)   # 0..1: drives the brightness (and the level)
    if not swell: e = e * (0.78 + 0.22 * np.exp(-np.maximum(t - att, 0) / 0.15))   # the bright bite, then the tone settles
    if stab: e = e * (0.35 + 0.65 * np.exp(-np.maximum(t - att, 0) / 0.12))
    e = e * release_after(n, dur, rel) * (0.55 + 0.45 * vel)   # soft = darker all the way through
    acc = 1 + (0 if swell else 0.35 * vel) * np.exp(-np.maximum(t - att, 0) / 0.08)   # the sforzando bump, loudness only
    K = int(min(40, (6000 if mute else 9000) / f0)); c = 0.45 / (0.35 + 0.65 * vel); X = np.zeros((2, n)); inc = np.zeros(n)
    for p, (det, pan) in enumerate(((-6, -0.5), (0, 0.1), (7, 0.5))):
        lag = int(rng.uniform(0, 0.012) * SR); ee = np.concatenate([np.zeros(lag), e[:n - lag]]) if lag else e
        blat = 2 ** ((0 if swell else -40) * np.exp(-t / 0.035) / 1200)
        vib = 1 + 0.002 * np.sin(TAU * 5.2 * t + rng.uniform(0, TAU)) * np.clip((t - 0.3) / 0.3, 0, 1)
        z = np.exp(1j * TAU * phase(f0 * 2 ** ((det + rng.uniform(-2, 2)) / 1200) * blat * vib, n, rng.random())); zk = z.copy(); y = np.zeros(n)
        for k in range(1, K + 1):
            y += ee ** (1 + (k - 1) * c) / k ** 0.7 * zk.imag; zk *= z
        X += pan2(y * acc, pan); inc += (y * acc) ** 2
    X = unbeat(X, inc)
    X = hpf(body(X, [(1500, 12, 3), (3000, 6, 3)]), 700) * 0.5 if mute else lpf(peq(X, 1200, 3, 1.0), 9000)
    return fade(X / 3, 0.001, 0.02)


def braam(m, dur, vel, rng, P):
    """Inception horn: detuned saws on root-24, root-12, the third and the fifth, a brassy blat, a filter that opens
    and closes, hard saturation and a sub; give it one note (the root). third: 3 (minor) or 4."""
    L = max(dur, 2.5); n = int(L * SR); t = secs(n); r = float(m); third = float(P.get("third", 3))
    blat = 2 ** (-35 * np.exp(-t / 0.07) / 1200); X = np.zeros((2, n))
    for off, g, width in ((-24, 0.4, 0.0), (-12, 1.0, 0.3), (-12 + third, 0.45, 0.6), (-5, 0.7, 0.8)):
        life = np.exp(-t / 0.6) if off == -24 else 1.0
        for d in (-1.0, -0.33, 0.33, 1.0):
            X += g * life * pan2(saw(float(mtof(r + off)) * 2 ** (d * 12 / 1200) * blat, n, rng.random()), width * d)
    opening = (1 - np.exp(-t / 0.03)) * np.exp(-t / 1.8); cutoff = 200 * (2500 / 200) ** (opening / opening.max())
    y = sweep_lp(X, cutoff, res=1.4, block=32); y = np.tanh(4.0 * y / (np.max(np.abs(y)) + 1e-9))
    y = hpf(y * np.clip(t / 0.02, 0, 1) * (0.35 + 0.65 * np.exp(-t / 1.8)) * release_after(n, L - 1.0, 1.0), 30)
    sub = np.sin(TAU * float(mtof(r - 24)) * t) * np.exp(-t / 1.5) * 0.5
    return fade(y + pan2(sub), 0.002, 0.1)


# ---------- synth ----------
def pulse_lead(m, dur, vel, rng, P):
    """Chip pulse: duty 0.125 / 0.25 / 0.5, 60 Hz stepped volume envelope (16 levels), delayed vibrato (vib = cents),
    chiparp = semitone offsets cycled at 60 Hz (the chiptune chord)."""
    f0 = float(mtof(m)); n = int((dur + 0.005) * SR); t = secs(n); f = np.full(n, f0)
    if P.get("chiparp"):
        offs = np.asarray(P["chiparp"], float); f = f0 * 2 ** (offs[(t * 60).astype(int) % len(offs)] / 12)
    if P.get("vib"): f = f * 2 ** (float(P["vib"]) * np.sin(TAU * 6 * t) * np.clip((t - 0.2) / 0.1, 0, 1) / 1200)
    fr = np.floor(t * 60) / 60; lvl = np.maximum(float(P.get("sus", 0.55)), np.exp(-fr / float(P.get("decay", 0.6))))
    x = pulse(f, n, float(P.get("duty", 0.25))) * np.floor(lvl * 15 + 0.5) / 15
    return fade(x, 0.001, 0.003)


def triangle(m, dur, vel, rng, P):
    """NES-style 4-bit (16-step) triangle bass: no envelope, just a gate."""
    n = int((dur + 0.004) * SR); p = phase(float(mtof(m)), n)
    return fade(np.round((4 * np.abs(p - 0.5) - 1) * 7.5) / 7.5, 0.002, 0.004)


def sq_bass(m, dur, vel, rng, P):
    """Motorik mono-synth bass: square (duty) + sub sine, resonant low-pass with a fast envelope, short gate."""
    f0 = float(mtof(m)); n = int((dur + 0.03) * SR); t = secs(n)
    x = 0.7 * pulse(f0, n, float(P.get("duty", 0.5))) + 0.5 * np.sin(TAU * f0 * t)
    fc = float(P.get("cutoff", 250)) + (600 + 1800 * vel) * np.exp(-t / float(P.get("env", 0.07)))
    x = sweep_lp(x, fc, res=float(P.get("res", 1.2)), block=32)
    e = (0.3 + 0.7 * np.exp(-t / float(P.get("decay", 0.18)))) * release_after(n, dur, 0.02)
    return fade(x * e, 0.001, 0.005)


def seq(m, dur, vel, rng, P):
    """HUD sequence voice: a short saw (or square) blip through a resonant low-pass with a snappy envelope; attack (s)
    softens the note head (an open filter makes a hard edge that qa lists as a click)."""
    f0 = float(mtof(m)); n = int(min(dur + 0.05, 0.6) * SR); t = secs(n)
    x = pulse(f0, n, 0.5) if P.get("wave") == "square" else saw(f0, n)
    base = float(P.get("cutoff", 1200)); fc = base * (1 + float(P.get("env", 3.0)) * vel * np.exp(-t / 0.06))
    x = sweep_lp(x, fc, res=float(P.get("res", 3.0)), block=32)
    x = x * np.exp(-t / float(P.get("decay", 0.12))) * release_after(n, dur, 0.02)
    att = float(P.get("attack", 0))
    if att > 0: x = x * (0.5 - 0.5 * np.cos(np.pi * np.clip(t / att, 0, 1)))
    return fade(x, 0.001, 0.005)


def cs80(m, dur, vel, rng, P):
    """CS-80-style brassy swell pad: two detuned saws + a pulse, the filter opening with the swell then settling,
    a slow delayed vibrato; stereo."""
    f0 = float(mtof(m)); att = float(P.get("attack", 0.35)); rel = float(P.get("release", 0.9))
    n = int((dur + rel) * SR); t = secs(n); vib = 2 ** (8 * np.sin(TAU * 5 * t) * np.clip((t - 0.5) / 0.5, 0, 1) / 1200)
    X = np.stack([saw(f0 * 2 ** (-7 / 1200) * vib, n, 0.1) + 0.5 * pulse(f0 * vib, n, 0.4),
                  saw(f0 * 2 ** (7 / 1200) * vib, n, 0.6) + 0.5 * pulse(f0 * vib, n, 0.4, 0.3)])
    a = np.clip(t / att, 0, 1) ** 1.5
    fc = f0 * 1.5 + f0 * (3 + 8 * vel) * a * (0.65 + 0.35 * np.exp(-np.maximum(t - att, 0) / 0.6))
    y = sweep_lp(X, fc, res=1.3, block=128) * np.clip(t / (0.8 * att), 0, 1) * release_after(n, dur, rel)
    return fade(y * 0.5, 0.002, 0.05)


def drone(m, dur, vel, rng, P):
    """Detuned low drone: four saws (±4, ±11 cents) and a sub sine, dark low-pass, slow breathing; stereo."""
    f0 = float(mtof(m)); att = float(P.get("attack", 1.2)); rel = float(P.get("release", 1.5))
    n = int((dur + rel) * SR); t = secs(n); X = np.zeros((2, n))
    inc = np.zeros(n)
    for c, pan in ((-11, -0.8), (-4, -0.3), (5, 0.3), (12, 0.8)):
        x = saw(f0 * 2 ** (c / 1200), n, rng.random()); X += pan2(x, pan); inc += x * x
    X = lpf(unbeat(X / 4, inc / 16, 0.7), float(P.get("cutoff", np.clip(4 * f0, 250, 1500)))) + 0.4 * pan2(np.sin(TAU * f0 / 2 * t))
    e = np.clip(t / att, 0, 1) * (0.85 + 0.15 * np.sin(TAU * 0.15 * t + rng.uniform(0, TAU))) * release_after(n, dur, rel)
    return fade(X * e, 0.002, 0.1)


def polysynth(m, dur, vel, rng, P):
    """Synthwave poly: 7-voice supersaw spread in stereo, bright low-pass, quick attack, a little decay."""
    f0 = float(mtof(m)); rel = float(P.get("release", 0.25)); n = int((dur + rel) * SR); t = secs(n); X = np.zeros((2, n))
    inc = np.zeros(n)
    for c, pan in zip((-18, -12, -6, 0, 6, 12, 18), (-0.9, -0.6, -0.3, 0, 0.3, 0.6, 0.9)):
        x = saw(f0 * 2 ** (c / 1200), n, rng.random()); X += pan2(x, pan); inc += x * x
    X = lpf(unbeat(X / 7, inc / 49), float(P.get("cutoff", 2500 + 6000 * vel)))
    e = np.clip(t / 0.005, 0, 1) * (0.75 + 0.25 * np.exp(-t / 0.35)) * release_after(n, dur, rel)
    return fade(X * e, 0.001, 0.02)


# ---------- drums and percussion: fn(vel, art, dur, rng, P, f) ----------
def _pitchdrop(f1, n, amt, tau):
    return np.cumsum(f1 * (1 + amt * np.exp(-secs(n) / tau))) / SR


def kick(vel, art, dur, rng, P, f=None):
    """Acoustic kit kick: beater click, skin, a body around 58 Hz (tune)."""
    n = int(0.5 * SR); t = secs(n); f1 = f or float(P.get("tune", 58))
    x = np.sin(TAU * _pitchdrop(f1, n, 1.2, 0.018)) * np.exp(-t / 0.22)
    x += burst(rng, n, 1500, 6000, 0.002, 0.25 * (0.5 + vel)) + lpf(burst(rng, n, 30, 900, 0.02, 1.0), 900) * 0.25
    return fade(drive(x, 1.5), 0.0003, 0.02)


def snare(vel, art, dur, rng, P, f=None):
    """Acoustic snare: shell body (185 + 330 Hz), wires, stick crack; o = cross-stick rim click."""
    n = int(0.45 * SR); t = secs(n)
    if art == "o": return rim(vel, "", dur, rng, P, f)
    f1 = f or float(P.get("tune", 185))
    x = np.sin(TAU * _pitchdrop(f1, n, 0.4, 0.01)) * np.exp(-t / 0.06) + 0.5 * np.sin(TAU * 1.78 * f1 * t) * np.exp(-t / 0.05)
    x += bpf(rng.standard_normal(n), 1800, 9000) * np.exp(-t / (0.09 + 0.08 * vel)) * (0.6 + 0.6 * vel)
    x += burst(rng, n, 4000, 16000, 0.003, 0.4 * vel)
    return fade(x, 0.0003, 0.02)


def rim(vel, art, dur, rng, P, f=None):
    n = int(0.12 * SR); t = secs(n)
    x = np.sin(TAU * 520 * t) * np.exp(-t / 0.03) + 0.7 * np.sin(TAU * 1650 * t) * np.exp(-t / 0.015)
    return fade(x + burst(rng, n, 2000, 6000, 0.004, 0.5), 0.0003, 0.01)


def brush(vel, art, dur, rng, P, f=None):
    """Brush on a snare: x = tap (soft attack, dry), o = swish (a sweep as long as the step, e.g. "o~~~")."""
    if art == "o":
        L = max(dur, 0.25); n = int(L * SR); k = secs(n) / L; env = np.sin(np.pi * k) ** 1.5
        nz = rng.standard_normal(n); x = bpf(nz, 1500, 3500) * (1 - k) + bpf(nz, 3000, 8000) * k
        return fade(x * env * 0.35, 0.005, 0.01)
    n = int(0.3 * SR); t = secs(n)
    x = bpf(rng.standard_normal(n), 1200, 8000) * np.clip(t / 0.003, 0, 1) * np.exp(-t / 0.07)
    x += 0.2 * np.sin(TAU * 190 * t) * np.exp(-t / 0.04)
    return fade(x, 0.002, 0.02)


def ride(vel, art, dur, rng, P, f=None):
    """Ride cymbal: an inharmonic partial cluster + wash + stick ping; o = the bell."""
    bell = art == "o"; n = int((2.0 if bell else 1.6) * SR); t = secs(n); x = np.zeros(n); b = f or 420.0
    for i, r in enumerate((1, 1.54, 2.12, 2.87, 3.54, 4.21, 5.1, 6.3, 7.4, 8.9)):
        tau = (1.2 if bell else 0.9) / (1 + 0.12 * i); x += np.sin(TAU * b * r * t + rng.uniform(0, TAU)) * np.exp(-t / tau) / (1 + 0.2 * i)
    if bell: x += 1.2 * modal(900, n, [(1, 1, 1.5), (1.5, 0.6, 1.2), (3.0, 0.4, 0.8)])
    x = hpf(x, 400) * 0.25 + hpf(rng.standard_normal(n), 5000) * np.exp(-t / 0.6) * 0.3
    return fade(x + burst(rng, n, 3000, 9000, 0.004, 0.5 * vel), 0.002, 0.05)


def _hat(rng, n, lo, hi, tau, base=317.0):
    t = secs(n); sq = sum(np.sign(np.sin(TAU * base * r * t + TAU * rng.random())) for r in (2.0, 3.0, 4.16, 5.43, 6.79, 8.21))
    return (bpf(sq, lo, hi) + 0.3 * hpf(rng.standard_normal(n), 8000)) * np.exp(-t / tau)


def hihat(vel, art, dur, rng, P, f=None):
    """808-recipe hat (six detuned squares, band-passed); o = open."""
    op = art == "o"; n = int((0.4 if op else 0.08) * SR)
    return fade(_hat(rng, n, 7000, 14000, 0.28 if op else 0.018 + 0.01 * vel) * 0.35, 0.0003, 0.01)


def trap_hat(vel, art, dur, rng, P, f=None):
    op = art == "o"; n = int((0.25 if op else 0.05) * SR)
    return fade(_hat(rng, n, 8000, 16000, 0.18 if op else 0.012 + 0.005 * vel, 360.0) * 0.4, 0.0003, 0.005)


def bb_kick(vel, art, dur, rng, P, f=None):
    """Boom-bap kick: round boom, driven, dusty (12-bit, half-rate)."""
    n = int(0.55 * SR); t = secs(n); f1 = f or 52.0
    x = np.sin(TAU * _pitchdrop(f1, n, 1.7, 0.03)) * np.exp(-t / 0.3) + lpf(burst(rng, n, 30, 3000, 0.004, 1.0), 3000) * 0.3
    return fade(crush(lpf(drive(x, 2.2), 3500), 12, 2), 0.0005, 0.02)


def _room(x, rt=0.25, seed=404, amt=0.35):
    g = np.random.default_rng(seed); k = int(rt * SR); ir = g.standard_normal(k) * np.exp(-secs(k) / (rt / 5)); ir[:int(0.004 * SR)] = 0
    return x + amt * fftconvolve(x, ir / np.sqrt(np.sum(ir ** 2)))[:len(x)]


def bb_snare(vel, art, dur, rng, P, f=None):
    """Boom-bap snare: fat body, loose wires, a small room, drive, dusty."""
    n = int(0.45 * SR); t = secs(n)
    x = np.sin(TAU * _pitchdrop(200, n, 0.3, 0.01)) * np.exp(-t / 0.07) + bpf(rng.standard_normal(n), 1000, 7000) * np.exp(-t / 0.16) * 0.9
    return fade(crush(lpf(drive(_room(x), 1.8), 6500), 12, 2), 0.0005, 0.02)


def trap_snare(vel, art, dur, rng, P, f=None):
    """Trap snare: bright, snappy, with a clap layer; o = rim."""
    if art == "o": return rim(vel, "", dur, rng, P, f)
    n = int(0.35 * SR); t = secs(n)
    x = np.sin(TAU * _pitchdrop(230, n, 0.5, 0.008)) * np.exp(-t / 0.05) + bpf(rng.standard_normal(n), 1800, 10000) * np.exp(-t / 0.12)
    return fade(x + 0.7 * clap(vel, "", dur, rng, P)[:n], 0.0003, 0.02)


def clap(vel, art, dur, rng, P, f=None):
    """Hand clap: three noise bursts ~11 ms apart and a tail; o = finger snap."""
    n = int(0.35 * SR); t = secs(n)
    if art == "o":
        return fade(burst(rng, n, 2000, 5000, 0.01, 1.0) + 0.5 * np.sin(TAU * 1800 * t) * np.exp(-t / 0.008), 0.0003, 0.02)
    nz = bpf(rng.standard_normal(n), 900, 3000); e = np.zeros(n)
    for k, d in enumerate((0.0, 0.011, 0.022)):
        i = int((d + rng.uniform(0, 0.002)) * SR); e[i:] += np.exp(-secs(n - i) / (0.006 if k < 2 else 0.11)) * (0.8 if k < 2 else 1.0)
    return fade(nz * e * 0.8, 0.0003, 0.02)


def gated(vel, art, dur, rng, P, f=None):
    """Synthwave gated snare: a snare through a dense reverb, cut hard at `gate` s (default 0.3)."""
    x = snare(vel, "", dur, rng, P); g = float(P.get("gate", 0.3)); n = int((g + 0.05) * SR); t = secs(n)
    k = int(0.8 * SR); ir = bpf(np.random.default_rng(909).standard_normal(k), 300, 9000) * np.exp(-secs(k) / 0.5)
    wet = fftconvolve(x, ir / np.sqrt(np.sum(ir ** 2)))[:n] * 1.2; y = np.zeros(n); y[:min(n, len(x))] += x[:n]
    return fade((y + wet) * np.clip((g - t) / 0.008, 0, 1), 0.0003, 0.005)


def cowbell(vel, art, dur, rng, P, f=None):
    """808 cowbell: two squares at f and 1.48 f (540 / 800 Hz by default), band-passed; pitched when the part gives
    notes (a phonk riff). o = muted."""
    f1 = f or 540.0; n = int(0.5 * SR); t = secs(n)
    x = bpf(pulse(f1, n) + pulse(f1 * 1.4815, n), f1 * 0.9, f1 * 4.5)
    e = (0.6 * np.exp(-t / 0.018) + 0.4 * np.exp(-t / (0.05 if art == "o" else 0.22)))
    return fade(x * e * 0.5, 0.0003, 0.02)


def shaker(vel, art, dur, rng, P, f=None):
    long_ = art == "o"; n = int((0.2 if long_ else 0.12) * SR); t = secs(n); a = 0.03 if long_ else 0.012
    e = np.where(t < a, 0.5 - 0.5 * np.cos(np.pi * t / a), np.exp(-(t - a) / (0.06 if long_ else 0.03)))
    return fade(bpf(rng.standard_normal(n), 4500, 11000) * e, 0.0005, 0.01)


def _membrane(rng, n, f1, tau, drop=0.08, skin=0.5, lo=800, hi=4000):
    t = secs(n); x = np.sin(TAU * _pitchdrop(f1, n, drop, 0.01)) * np.exp(-t / tau) + 0.3 * np.sin(TAU * 1.59 * f1 * t) * np.exp(-t / (tau * 0.5))
    return x + burst(rng, n, lo, hi, 0.006, skin)


def bongo(vel, art, dur, rng, P, f=None):
    return fade(_membrane(rng, int(0.35 * SR), f or (290.0 if art == "o" else 400.0), 0.09), 0.0003, 0.02)


def conga(vel, art, dur, rng, P, f=None):
    """Conga: open tone; o = slap (short, bright)."""
    n = int(0.5 * SR)
    if art == "o": return fade(_membrane(rng, n, f or 230.0, 0.03, skin=1.2, lo=1000, hi=6000), 0.0003, 0.02)
    return fade(_membrane(rng, n, f or 210.0, 0.22, drop=0.05, skin=0.3), 0.0003, 0.02)


def woodblock(vel, art, dur, rng, P, f=None):
    f1 = f or (850.0 if art == "o" else 1250.0); n = int(0.2 * SR)
    return fade(modal(f1, n, [(1, 1, 0.045), (2.4, 0.3, 0.02)]) + burst(rng, n, 3000, 12000, 0.0005, 0.3), 0.0002, 0.01)


def bangzi(vel, art, dur, rng, P, f=None):
    """梆子: two hard wood sticks, a very sharp high clack; o = softer."""
    f1 = f or 2100.0; n = int(0.15 * SR); soft = art == "o"
    x = modal(f1, n, [(1, 1, 0.03), (1.62, 0.6, 0.02), (2.9, 0.3, 0.012)]) + burst(rng, n, 3000, 15000, 0.0008, 0.4 if soft else 0.8)
    return fade(x, 0.0002, 0.01)


def gong(vel, art, dur, rng, P, f=None):
    """Large gong / tam-tam: ~36 inharmonic partials; the upper ones bloom after the strike; long tail; the pitch sags
    by `drop` semitones (default -1, the opera 大锣 'wang'). o = damped."""
    f1 = f or float(P.get("tune", 70.0)); damp = art == "o"; n = int((1.5 if damp else float(P.get("length", 8.0))) * SR); t = secs(n)
    g = np.random.default_rng([crc("gong"), int(f1)])
    ratios = [1, 1.53, 2.07, 2.61, 3.33, 3.97, 4.64, 5.52] + sorted(g.uniform(4, 40, 28))
    bend = 2 ** (float(P.get("drop", -1.0)) * (1 - np.exp(-t / float(P.get("drop_time", 0.8)))) / 12); C = np.cumsum(bend) / SR; x = np.zeros(n)
    for i, r in enumerate(ratios):
        fr = f1 * r
        if fr >= 0.4 * SR: continue
        tau = (float(P.get("decay", 4.5)) / (1 + 0.08 * i)) * (0.1 if damp else 1.0); k = min(n, int(6 * tau * SR) + 1)
        bloom = (1 - np.exp(-t[:k] / 0.35)) ** 2 if i >= 8 else 1.0
        x[:k] += np.sin(TAU * fr * C[:k] + g.uniform(0, TAU) * (i >= 8)) * bloom * np.exp(-t[:k] / tau) / (1 + 0.25 * i)
    x += lpf(burst(rng, n, 20, 200, 0.05, 1.0), 200) * 0.4
    return fade(x, 0.001, min(2.5, n / SR / 3))


def smallgong(vel, art, dur, rng, P, f=None):
    """小锣: a small opera gong whose pitch jumps UP after the strike (rise, semitones); o = damped."""
    f1 = f or 620.0; damp = art == "o"; n = int((0.4 if damp else 1.6) * SR); t = secs(n)
    bend = 2 ** (float(P.get("rise", 2.5)) * (0.5 if damp else 1) * (1 - np.exp(-t / 0.12)) / 12)
    k = 0.12 if damp else 1.0
    x = modal(f1, n, [(1, 1, 0.9 * k), (1.47, 0.4, 0.5 * k), (2.09, 0.3, 0.35 * k), (2.76, 0.2, 0.25 * k), (3.6, 0.12, 0.15 * k)], bend)
    return fade(x + burst(rng, n, 2000, 8000, 0.001, 0.4), 0.0003, 0.03)


def cymbals(vel, art, dur, rng, P, f=None):
    """铙钹 (naobo): a bright noisy crash with a metallic partial cluster; o = choked 'cha'."""
    ch = art == "o"; n = int((0.3 if ch else 2.0) * SR); t = secs(n); g = np.random.default_rng([crc("naobo")])
    x = sum(np.sin(TAU * 480 * r * t + g.uniform(0, TAU)) * np.exp(-t / ((0.07 if ch else g.uniform(0.6, 1.5)))) for r in g.uniform(1, 12, 30)) / 10
    x = x + hpf(rng.standard_normal(n), 3000) * np.exp(-t / (0.07 if ch else 0.9)) * 0.6 + burst(rng, n, 1000, 8000, 0.05, 0.5)
    return fade(hpf(x, 300), 0.0005, 0.02)


def framedrum(vel, art, dur, rng, P, f=None):
    """Frame drum: band-passed noise head + a tuned body (175 Hz); o = rim tap."""
    n = int(0.5 * SR); t = secs(n)
    if art == "o":
        x = bpf(rng.standard_normal(n), 1000, 5000) * np.exp(-t / 0.02) + 0.5 * np.sin(TAU * 330 * t) * np.exp(-t / 0.03)
    else:
        f1 = f or 175.0; x = bpf(rng.standard_normal(n), 220, 2400) * np.exp(-t / 0.05) + 0.8 * np.sin(TAU * _pitchdrop(f1, n, 0.34, 0.02)) * np.exp(-t / 0.09)
    return fade(_room(x, 0.3, 405, 0.3), 0.0003, 0.02)


def timpani(vel, art, dur, rng, P, f=None):
    """Kettle drum, pitched (the part's chord root by default): modes 1 : 1.5 : 1.98 : 2.44 : 2.94, a soft thud,
    a small pitch sag after the stroke; rolls come from the grid's r / R. o = muted."""
    f1 = f or 98.0; mu = art == "o"; n = int((0.5 if mu else 2.5) * SR); t = secs(n); k = 0.15 if mu else 1.0
    bend = 2 ** (0.3 * np.exp(-t / 0.05) / 12)
    x = modal(f1, n, [(1, 1, 1.3 * k), (1.5, 0.5, 0.9 * k), (1.98, 0.3, 0.6 * k), (2.44, 0.2, 0.45 * k), (2.94, 0.1, 0.3 * k)], bend)
    x += lpf(burst(rng, n, 20, 180, 0.03, 1.0), 180) * 0.5 + burst(rng, n, 400, 2000, 0.004, 0.2 * vel)
    return fade(x, 0.0005, 0.05)


def clock(vel, art, dur, rng, P, f=None):
    """Clock escapement: x = tick, o = tock (lower)."""
    f1 = f or (1900.0 if art == "o" else 3200.0); n = int(0.06 * SR)
    return fade(modal(f1, n, [(1, 1, 0.008), (2.3, 0.5, 0.004)]) + burst(rng, n, 5000, 15000, 0.0005, 0.5), 0.0001, 0.005)


def metal(vel, art, dur, rng, P, f=None):
    """Industrial hit: x = anvil (inharmonic plate), o = pipe (tube modes, longer); driven."""
    if art == "o":
        b = f or 190.0; n = int(2.5 * SR); x = 0.5 * modal(b, n, [(1, 1, 1.3), (2.76, 0.7, 0.6), (5.40, 0.4, 0.3), (8.93, 0.2, 0.15)])
    else:
        b = f or 520.0; n = int(1.5 * SR); t = secs(n); x = np.zeros(n)
        for i, r in enumerate((1.0, 1.47, 1.98, 2.56, 3.21, 4.03, 5.17)):
            x += np.sin(TAU * b * r * t + TAU * rng.random()) * np.exp(-t * (1 + 0.6 * i) / 0.5) / (1 + 0.35 * i)
    x = x + burst(rng, n, 2000, 7000, 0.004, 0.5)
    return fade(lpf(drive(x, 2.0), 7000), 0.0005, 0.05)


def noiseburst(vel, art, dur, rng, P, f=None):
    """Stutter: a gated burst of distorted noise as long as the step (x~~ = longer); o = telephone-band noise; r = stutter."""
    L = max(dur * 0.85, 0.03); n = int(L * SR); x = rng.standard_normal(n)
    x = bpf(x, 1000, 4000) if art == "o" else hpf(x, 300)
    return fade(drive(x * 0.5, 3.0), 0.001, 0.004)


_SCR = {}


def scratch(vel, art, dur, rng, P, f=None):
    """Vinyl scratch: a short 'fresh' horn-ish stab read forward and back (x = baby scratch, o = chirp: forward with
    the fader cut), pitch following the hand speed; length = the step (x~ = a longer scratch)."""
    if "src" not in _SCR:
        g = np.random.default_rng(777); k = int(1.5 * SR); t = secs(k)
        src = saw(220, k) + saw(221.7, k) + 0.3 * g.standard_normal(k)
        _SCR["src"] = body(src, [(700, 12, 3), (1150, 10, 3), (2600, 6, 3)]) * np.exp(-t / 0.8) * 0.25
    src = _SCR["src"]; L = max(dur, 0.12); n = int(L * SR); k = secs(n) / L
    pos = (0.18 * SR) * ((0.5 - 0.5 * np.cos(TAU * k)) if art != "o" else np.sin(np.pi * k / 2)) + 0.02 * SR
    y = np.interp(pos, np.arange(len(src)), src) * (np.clip(np.abs(np.gradient(pos)) * 1.5, 0, 1) ** 0.5)
    if art == "o": y *= (k < 0.55)
    return fade(y + hpf(rng.standard_normal(n), 3000) * 0.02, 0.002, 0.004)


def chipnoise(vel, art, dur, rng, P, f=None):
    """Chip noise channel: 1-bit sample-and-hold noise, stepped decay; x = snare, o = hat."""
    hat = art == "o"; n = int((0.05 if hat else 0.15) * SR); t = secs(n); hold = 1 if hat else 4
    x = np.repeat(np.where(rng.random(n // hold + 1) < 0.5, -1.0, 1.0), hold)[:n]
    lvl = np.floor(np.exp(-np.floor(t * 240) / 240 / (0.02 if hat else 0.08)) * 15 + 0.5) / 15
    return fade(x * lvl * 0.5, 0.0003, 0.003)


def chipkick(vel, art, dur, rng, P, f=None):
    """Chip kick: the 4-bit triangle swept from 180 to 45 Hz."""
    n = int(0.15 * SR); t = secs(n); fr = 45 + 135 * np.exp(-t / 0.02)
    return fade(np.round((4 * np.abs(phase(fr, n) - 0.5) - 1) * 7.5) / 7.5, 0.0005, 0.01)


def danpigu(vel, art, dur, rng, P, f=None):
    """单皮鼓: the opera conductor's small, tight, very high drum (a dry crack); o = the wooden clapper (板)."""
    n = int(0.25 * SR)
    if art == "o": return bangzi(vel, "o", dur, rng, P, 1500.0)
    return fade(_membrane(rng, n, f or 560.0, 0.035, drop=0.12, skin=0.9, lo=1500, hi=7000), 0.0002, 0.01)


LUOGU = {   # 锣鼓经 syllables → gains of (大锣 big gong, 小锣 small gong, 铙钹 open, 铙钹 choked, 单皮鼓 drum)
    "仓": (1.0, 0, 0.8, 0, 0.5), "才": (0, 0, 0, 0.9, 0), "台": (0, 1.0, 0, 0, 0), "七": (0, 0, 0, 0.45, 0),
    "令": (0, 0.5, 0, 0, 0), "顷": (0.5, 0, 0, 0, 0), "冬": (0, 0, 0, 0, 1.0), "大": (0, 0, 0, 0, 1.0), "八": (0, 0, 0, 0, 0.6),
}


def luogu(vel, art, dur, rng, P, f=None):
    """锣鼓经 kit: write the syllables in the grid. 仓 (大锣 + 铙钹 + 鼓), 才 (铙钹 choked), 台 (小锣), 七 (soft 铙钹),
    令 (soft 小锣), 顷 (soft 大锣), 冬 / 大 (单皮鼓), 八 (a light stroke); x and X mean 仓. The 大锣 is an opera gong whose
    pitch falls 2.5 semitones from 240 Hz; retune it with params {"daluo": Hz}, or give the part a "pitch" (e.g. "d1") and
    it follows that note. {"xiaoluo": Hz} retunes the 小锣 (620 Hz, rising)."""
    g = LUOGU.get(art, LUOGU["仓"]); parts = []
    tune = f or float(P.get("daluo", 240.0))
    if g[0]: parts.append(g[0] * gong(vel, "", dur, rng, {"tune": tune, "drop": -2.5, "drop_time": 0.25, "decay": 1.6, "length": 3.0}))
    if g[1]: parts.append(g[1] * smallgong(vel, "", dur, rng, P, P.get("xiaoluo") and float(P["xiaoluo"])) * 0.8)
    if g[2]: parts.append(g[2] * cymbals(vel, "", dur, rng, P) * 0.6)
    if g[3]: parts.append(g[3] * cymbals(vel, "o", dur, rng, P))
    if g[4]: parts.append(g[4] * danpigu(vel, "", dur, rng, P))
    y = np.zeros(max(len(x) for x in parts))
    for x in parts: y[:len(x)] += x
    return y


def organ(m, dur, vel, rng, P):
    """Drawbar organ: sine drawbars 16' 5⅓' 8' 4' 2⅔' 2' 1⅗' 1⅓' 1' ("drawbars": "888000000"), key click, leslie
    (Hz: 0.8 slow, 6.5 fast, 0 off); tone "pipe": a pipe organ (principal chorus, chiff, slow speech, no leslie)."""
    f0 = float(mtof(m)); pipe = P.get("tone") == "pipe"; rel = 0.35 if pipe else 0.05; n = int((dur + rel) * SR); t = secs(n)
    ph = rng.random() + f0 * t; x = np.zeros(n)   # unwrapped phase: the 16' and 5⅓' bars are below / between harmonics
    for r, d in zip((0.5, 1.5, 1, 2, 3, 4, 5, 6, 8), str(P.get("drawbars", "688600040" if pipe else "888000000"))):
        if f0 * r < 0.45 * SR and int(d): x += int(d) / 8 * np.sin(TAU * ((ph * r) % 1.0))
    x /= 3
    if pipe:
        x += burst(rng, n, f0 * 2, f0 * 6, 0.03, 0.15) + bpf(rng.standard_normal(n), 2000, 6000) * 0.01; e = np.clip(t / 0.06, 0, 1) ** 2
    else:
        x += burst(rng, n, 1500, 6000, 0.002, 0.3) if P.get("click", True) else 0; e = np.clip(t / 0.005, 0, 1)
    lz = float(P.get("leslie", 0 if pipe else 0.8))
    if lz: x = x * (1 + 0.25 * np.sin(TAU * lz * t)) + 0.15 * hpf(x, 800) * np.sin(TAU * lz * t + 1.3)
    return fade(x * e * release_after(n, dur, rel), 0.002, 0.02)


def sheng(m, dur, vel, rng, P):
    """笙: free reeds; a reedy sustained tone with a nasal formant, a slow onset and a breath tremolo. It plays chords
    well: "pitch": ["c0", "+7", "+12"] or stacked 4ths and 5ths."""
    f0 = float(mtof(m)); rel = 0.12; n = int((dur + rel) * SR); t = secs(n)
    x = 0.6 * pulse(f0, n, 0.42, rng.random()) + 0.4 * saw(f0 * 2 ** (rng.uniform(-3, 3) / 1200), n, rng.random())
    x = hpf(lpf(body(x, [(1400, 6, 2), (2600, 4, 2)]), 5000), 150) + bpf(rng.standard_normal(n), 1500, 5000) * 0.02
    e = np.clip(t / 0.08, 0, 1) * (1 + 0.06 * np.sin(TAU * 5 * t)) * release_after(n, dur, rel)
    return fade(x * e, 0.002, 0.02)


# ---------- textures: fn(n, rng, P) ----------
def vinyl(n, rng, P):
    """Crackle: Poisson clicks (density ~ per second ×18) and a few bigger pops, faint hiss; stereo."""
    d = float(P.get("density", 1.0)); X = np.zeros((2, n))
    for c in (0, 1):
        imp = np.zeros(n); k = rng.poisson(n / SR * 18 * d); np.add.at(imp, rng.integers(0, n, k), rng.exponential(0.25, k) * rng.choice([-1, 1], k))
        big = np.zeros(n); k = rng.poisson(n / SR * 1.2 * d); np.add.at(big, rng.integers(0, n, k), rng.exponential(0.6, k) * rng.choice([-1, 1], k))
        X[c] = hpf(lfilter([1], [1, -0.6], imp), 1500) + lpf(lfilter([1], [1, -0.9], big), 2500) * 0.3
    return X + hpf(rng.standard_normal((2, n)), 4000) * 0.02


def tape(n, rng, P):
    t = secs(n); return bpf(rng.standard_normal((2, n)), 1500, 14000) * (1 + 0.1 * np.sin(TAU * 0.7 * t))


def hum(n, rng, P):
    """Mains hum (hz 50/60) with harmonics and a buzz, plus a fan (fan 0..1)."""
    f = float(P.get("hz", 60)); t = secs(n)
    x = sum((0.5 if k in (2, 3) else 1.0 / k) * np.sin(TAU * k * f * t) for k in range(1, 13)) * 0.3
    x += np.clip(3 * np.sin(TAU * f * t), -1, 1) * 0.05
    x = hpf(x, 80) + lpf(rng.standard_normal(n), 500) * float(P.get("fan", 0.5)) * (1 + 0.1 * np.sin(TAU * 13 * t))
    return x


def wind(n, rng, P):
    """Wind: four noise bands crossfaded by slow random gusts; stereo."""
    X = np.zeros((2, n))
    for c in (0, 1):
        nz = rng.standard_normal(n); bands = [bpf(nz, lo, hi) for lo, hi in ((200, 500), (400, 900), (800, 1600), (1500, 3000))]
        w = [np.maximum(0, wander(rng, n, 0.3)) ** 2 for _ in bands]; tot = sum(w) + 0.2
        X[c] = sum(b * wi for b, wi in zip(bands, w)) / tot * (0.4 + 0.6 * (0.5 + 0.5 * wander(rng, n, 0.15)))
    return X


def rain(n, rng, P):
    """Rain: dense droplet ticks and a steady wash; stereo."""
    X = np.zeros((2, n))
    for c in (0, 1):
        imp = np.zeros(n); k = rng.poisson(n / SR * 300 * float(P.get("density", 1.0)))
        np.add.at(imp, rng.integers(0, n, k), rng.exponential(0.3, k))
        X[c] = bpf(lfilter([1], [1, -0.7], imp), 2000, 9000) + lpf(hpf(rng.standard_normal(n), 400), 7000) * 0.25 + lpf(rng.standard_normal(n), 300) * 0.1
    return X


def roomtone(n, rng, P):
    nz = rng.standard_normal((2, n)); return hpf(lpf(nz, 900) + 0.3 * lpf(nz, 3000), 40)


# ---------- spaces (deterministic IRs) ----------
SPACES = {  # rt60 (s), pre-delay (s), tail low-pass (Hz), build-up (s), early reflections
    "room": (0.7, 0.004, 7000, 0.004, True), "plate": (2.0, 0.0, 10000, 0.0015, False),
    "hall": (2.8, 0.022, 5000, 0.015, True), "cathedral": (6.5, 0.045, 3200, 0.04, True),
    "gated": (1.0, 0.0, 8000, 0.002, False),
}


def space_ir(name, ch, rt60=None):
    """A synthetic room: decaying noise with the highs dying faster (slower on the plate), a diffuse build-up, early
    reflections, a pre-delay; `gated` is dense and cut at 0.3 s. Fixed seeds: the same space sounds the same in every
    score. Unit energy."""
    rt, pre, lp_hz, build, er = SPACES[name]; rt = float(rt60 or rt)
    g = np.random.default_rng([7331, crc(name), ch]); n = int((0.34 if name == "gated" else rt) * SR); t = secs(n)
    nz = g.standard_normal(n); low = lpf(nz, lp_hz); tau = rt / 6.91
    ir = low * np.exp(-t / tau) + (nz - low) * np.exp(-t / (tau * (0.8 if name == "plate" else 0.4)))
    if name == "gated": ir = low * (0.7 + 0.3 * np.exp(-t / 0.2)) * np.clip((0.3 - t) / 0.01, 0, 1)
    ir *= 1 - np.exp(-t / build)
    if er:
        for k in range(6):
            i = int(g.uniform(0.003, 0.04 if name != "room" else 0.02) * SR); ir[i] += g.choice([-1, 1]) * 3.0 / (1 + k)
    if name == "plate": ir = hpf(ir, 200)
    ir = np.concatenate([np.zeros(int(pre * SR)), ir]); return ir / np.sqrt(np.sum(ir ** 2))


# ---------- registry ----------
class Inst:
    """kind, fn, default octave, level; rr = round-robin variants per note; vt = velocity changes the timbre (so the
    cache keeps one render per velocity step; otherwise one render is scaled)."""
    def __init__(self, kind, fn, octave=4, level=1.0, **defaults):
        self.kind, self.fn, self.octave, self.level, self.defaults = kind, fn, octave, level, defaults
        self.rr, self.vt = (4, False) if kind == "drum" else (3, True)
        about = " ".join((getattr(fn, "__doc__", None) or "").split()).split(". ")[0]
        self.about = about if len(about) <= 120 else about[:about.rfind(" ", 0, 118)] + " …"


def _mono(fn, name, octave, level, **d):
    return Inst("mono", fn, octave, level, _name=name, **d)


INSTR = {
    # keys
    "piano": Inst("note", piano, 4, 1.0), "epiano": Inst("note", epiano, 4, 1.0), "harpsichord": Inst("note", harpsichord, 4, 1.0),
    "celesta": Inst("note", celesta, 5, 1.0), "musicbox": Inst("note", musicbox, 6, 1.0), "glockenspiel": Inst("note", glockenspiel, 6, 1.0),
    "toypiano": Inst("note", toypiano, 5, 1.0),
    # mallets
    "marimba": Inst("note", marimba, 4, 1.0), "xylophone": Inst("note", xylophone, 5, 1.0), "vibraphone": Inst("note", vibraphone, 4, 1.0),
    # plucked
    "nylon": Inst("note", nylon, 3, 1.0), "ukulele": Inst("note", ukulele, 4, 1.0), "harp": Inst("note", harp, 4, 1.0),
    "pizzicato": Inst("note", pizzicato, 3, 1.0), "upright": Inst("note", upright, 2, 1.0), "pipa": Inst("note", pipa, 4, 1.0, tremolo_rate=14),
    "guqin": Inst("note", guqin, 3, 1.0), "balalaika": Inst("note", balalaika, 4, 1.0, tremolo_rate=11), "cimbalom": Inst("note", cimbalom, 4, 1.0),
    # physically modelled plucked strings, tines and teeth (opt-in; see PM_STRINGS and PM_BARS)
    "guqin_pm": Inst("note", _pm("guqin_pm"), 3, 1.0), "pipa_pm": Inst("note", _pm("pipa_pm"), 4, 1.0, tremolo_rate=14),
    "harp_pm": Inst("note", _pm("harp_pm"), 4, 1.0), "nylon_pm": Inst("note", _pm("nylon_pm"), 3, 1.0), "guitar": Inst("note", _pm("guitar"), 3, 1.0),
    "ukulele_pm": Inst("note", _pm("ukulele_pm"), 4, 1.0), "upright_pm": Inst("note", _pm("upright_pm"), 2, 1.0),
    "balalaika_pm": Inst("note", _pm("balalaika_pm"), 4, 1.0, tremolo_rate=11), "cimbalom_pm": Inst("note", _pm("cimbalom_pm"), 4, 1.0),
    "koto": Inst("note", _pm("koto"), 4, 1.0), "shamisen": Inst("note", _pm("shamisen"), 4, 1.0), "banjo": Inst("note", _pm("banjo"), 4, 1.0),
    "kalimba": Inst("note", _pm("kalimba"), 5, 1.0), "musicbox_pm": Inst("note", _pm("musicbox_pm"), 6, 1.0),
    # bowed
    "strings": Inst("note", strings, 4, 1.0),
    "violin": _mono(bowed, "violin", 5, 1.0, vib=BOWED["violin"]["vib"], glide=0.07, attack=0.07, release=0.12, rearticulate=0.25),
    "fiddle": _mono(bowed, "fiddle", 5, 1.0, vib=BOWED["fiddle"]["vib"], glide=0.03, attack=0.03, release=0.08, rearticulate=0.4),
    "cello": _mono(bowed, "cello", 3, 1.0, vib=BOWED["cello"]["vib"], glide=0.06, attack=0.08, release=0.12, rearticulate=0.3),
    "banhu": _mono(bowed, "banhu", 5, 1.0, vib=BOWED["banhu"]["vib"], glide=0.11, attack=0.05, release=0.1, rearticulate=0.3, scoop=-0.8, scoop_time=0.07),
    # winds and brass
    "flute": _mono(winds, "flute", 5, 1.0, glide=0.05, attack=0.06, release=0.1, vib=(5.0, 14, 0.25)),
    "xiao": _mono(winds, "xiao", 4, 1.0, glide=0.08, attack=0.14, release=0.15, vib=(4.6, 8, 0.35)),
    "whistle": _mono(winds, "whistle", 5, 1.0, glide=0.04, attack=0.03, release=0.06, vib=(5.6, 16, 0.12)),
    "suona": _mono(winds, "suona", 5, 1.0, glide=0.06, attack=0.02, release=0.06, vib=(6.0, 28, 0.15), scoop=-1.0, scoop_time=0.06),
    "brass": Inst("note", brass, 4, 1.0), "braam": Inst("note", braam, 3, 1.0),
    # synth
    "pulse": Inst("note", pulse_lead, 5, 1.0), "triangle": Inst("note", triangle, 3, 1.0), "sq_bass": Inst("note", sq_bass, 2, 1.0),
    "sub808": _mono(sub808, "sub808", 1, 1.0, glide=0.08, attack=0.002, release=0.06),
    "seq": Inst("note", seq, 4, 1.0), "cs80": Inst("note", cs80, 3, 1.0), "drone": Inst("note", drone, 2, 1.0), "polysynth": Inst("note", polysynth, 4, 1.0),
    "organ": Inst("note", organ, 4, 1.0), "sheng": Inst("note", sheng, 5, 1.0),
    # drums and percussion
    "kick": Inst("drum", kick), "snare": Inst("drum", snare), "rim": Inst("drum", rim), "brush": Inst("drum", brush), "ride": Inst("drum", ride),
    "hihat": Inst("drum", hihat), "bb_kick": Inst("drum", bb_kick), "bb_snare": Inst("drum", bb_snare), "trap_hat": Inst("drum", trap_hat),
    "trap_snare": Inst("drum", trap_snare), "clap": Inst("drum", clap), "gated": Inst("drum", gated), "cowbell": Inst("drum", cowbell, 5),
    "shaker": Inst("drum", shaker), "bongo": Inst("drum", bongo), "conga": Inst("drum", conga), "woodblock": Inst("drum", woodblock, 6),
    "bangzi": Inst("drum", bangzi, 7), "gong": Inst("drum", gong, 2), "smallgong": Inst("drum", smallgong, 5), "cymbals": Inst("drum", cymbals),
    "framedrum": Inst("drum", framedrum), "timpani": Inst("drum", timpani, 2, pitched=True), "clock": Inst("drum", clock), "metal": Inst("drum", metal),
    "noiseburst": Inst("drum", noiseburst), "scratch": Inst("drum", scratch), "noise": Inst("drum", chipnoise), "chipkick": Inst("drum", chipkick),
    "danpigu": Inst("drum", danpigu), "luogu": Inst("drum", luogu),
    # textures
    "vinyl": Inst("texture", vinyl), "tape": Inst("texture", tape), "hum": Inst("texture", hum), "wind": Inst("texture", wind),
    "rain": Inst("texture", rain), "roomtone": Inst("texture", roomtone),
}

# gain_db 0 = a comparable loudness: measured by rendering one note per voice (C at the default octave, 1 s, velocity 1)
# and scaling hits and plucks to peak 0.5, held voices to -20 dBFS RMS (peak at most 0.45), textures to -34 dBFS RMS
# (crackle peaks at most 0.2)
LEVEL = {
    "piano": 0.266, "epiano": 0.496, "harpsichord": 0.265, "celesta": 0.416, "musicbox": 0.33, "glockenspiel": 0.281,
    "toypiano": 0.275, "marimba": 0.306, "xylophone": 0.425, "vibraphone": 0.425, "nylon": 0.492, "ukulele": 0.422,
    "harp": 0.479, "pizzicato": 0.289, "upright": 0.533, "pipa": 0.244, "guqin": 0.496, "balalaika": 0.288,
    "cimbalom": 0.428, "strings": 0.365, "violin": 0.056, "fiddle": 0.051, "cello": 0.057, "banhu": 0.121,
    "flute": 0.143, "xiao": 0.148, "whistle": 0.143, "suona": 0.09, "brass": 0.173, "braam": 0.168, "pulse": 0.186,
    "triangle": 0.174, "sq_bass": 0.591, "sub808": 0.502, "seq": 0.332, "cs80": 0.436, "drone": 0.545,
    "polysynth": 0.632, "organ": 0.233, "sheng": 0.136, "kick": 0.487, "snare": 0.166, "rim": 0.312, "brush": 0.306,
    "ride": 0.364, "hihat": 0.677, "bb_kick": 0.498, "bb_snare": 0.444, "trap_hat": 0.733, "trap_snare": 0.206,
    "clap": 0.532, "gated": 0.147, "cowbell": 0.38, "shaker": 0.313, "bongo": 0.357, "conga": 0.354,
    "woodblock": 0.356, "bangzi": 0.26, "gong": 0.128, "smallgong": 0.268, "cymbals": 0.195, "framedrum": 0.311,
    "timpani": 0.27, "clock": 0.363, "metal": 0.447, "noiseburst": 0.498, "scratch": 0.397, "noise": 1.0,
    "chipkick": 0.536, "danpigu": 0.254, "luogu": 0.111, "vinyl": 0.307, "tape": 0.039, "hum": 0.087, "wind": 0.378,
    "rain": 0.213, "roomtone": 0.109,
    # the physically modelled voices: every note's tone peaks at 1, so a velocity-1 pluck peaks at 0.5 (measured 0.48–0.51;
    # 0.46–0.63 where a bachi, skin or pick transient rides on top, 0.47–0.57 for a level-matched harmonic)
    "guqin_pm": 0.5, "pipa_pm": 0.5, "harp_pm": 0.5, "nylon_pm": 0.5, "guitar": 0.5, "ukulele_pm": 0.5, "upright_pm": 0.5,
    "balalaika_pm": 0.5, "cimbalom_pm": 0.5, "koto": 0.5, "shamisen": 0.5, "banjo": 0.5, "kalimba": 0.5, "musicbox_pm": 0.5,
}
for _k, _v in LEVEL.items():
    INSTR[_k].level = _v
for _k in ("kick", "snare", "ride", "hihat", "trap_hat", "gated", "timpani"):
    INSTR[_k].vt = True   # drums whose stroke gets brighter or longer when hit harder
for _k in ("gong", "luogu", "cymbals", "smallgong", "metal", "braam"):
    INSTR[_k].rr = 2      # long, heavy renders: two variants are enough

ABOUT = {   # one line for --instruments where the function's docstring is shared or missing
    "celesta": "Celesta: a soft hammered tine (1, 2, 4.16, 6.9 partials), rings; damp: stop at the note end.",
    "glockenspiel": "Glockenspiel: steel bars 1 : 2.76 : 5.40 : 8.93, a hard brass-mallet click, long ring.",
    "xylophone": "Xylophone: rosewood bars tuned 1 : 3, short and dry, hard mallet.",
    "nylon": "Nylon-string guitar: warm KS pluck with guitar body resonances (105 / 210 / 420 Hz); ring, mute.",
    "ukulele": "Ukulele: a small bright body, short ring; with the strum figure (strings 4) it is the explainer strum.",
    "pizzicato": "Pizzicato: plucked violin-family string, short decay, finger thump, violin body.",
    "violin": "Solo violin (mono): bowed saw through a violin body, delayed vibrato, portamento on legato notes.",
    "fiddle": "Fiddle (mono): the violin with less vibrato, quicker bow changes, more bow noise.",
    "cello": "Solo cello (mono): bowed, dark body; params marcato (bite) for driving ostinati.",
    "banhu": "板胡 (mono): high nasal bowed voice, coconut-shell formants, wide vibrato, scoops and slides into notes.",
    "flute": "Flute (mono): nearly pure tone, breath around the pitch, a tongue chiff, delayed vibrato.",
    "xiao": "箫 (mono): low end-blown flute, a lot of breath, slow onset, little vibrato.",
    "whistle": "Whistle (mono): kind lips (a person whistling) or tin (penny whistle), fast vibrato.",
    "suona": "唢呐 (mono): bright nasal double reed, strong formants, scoops into notes, wide vibrato.",
    "rim": "Rim click / cross-stick.",
    "brass": "Brass section (three players): a bright bite that settles, louder = brighter; stab, swell, mute (harmon).",
    "trap_hat": "Trap hat: very tight and bright; r / R rolls; o = open.",
    "shaker": "Shaker: band-passed noise with a soft attack; o = a longer shake.",
    "bongo": "Bongo: high drum (400 Hz); o = the low drum of the pair.",
    "woodblock": "Woodblock: a resonant wooden click (1250 Hz); o = the low block.",
    "tape": "Tape hiss: band-limited noise with a slow wobble; stereo.",
    "roomtone": "Room tone: soft dark noise, the sound of an empty room; stereo.",
    "guqin_pm": "古琴, physical model: silk string, long ring; slide, bend, yin, nao, vib, harm (a real node harmonic), trem, damp.",
    "pipa_pm": "琵琶, physical model: nail pluck, bright, a sharp twang; 轮指 from the part's tremolo or a note's trem; bend, vib, harm.",
    "harp_pm": "Harp, physical model: mid-string finger pluck, round and long; harm (octave harmonic), damp.",
    "nylon_pm": "Nylon-string guitar, physical model: finger pluck, guitar body; ring, mute, slide, bend, vib, harm.",
    "guitar": "Steel-string acoustic guitar, physical model: flatpick, bright long ring; strum it (strings 6), mute, bend, harm.",
    "ukulele_pm": "Ukulele, physical model: soft finger strum, small body, short ring; ring, mute.",
    "upright_pm": "Upright bass pizz, physical model: finger thump, pitch settling after a hard pluck, dark body; ring, slide.",
    "balalaika_pm": "Balalaika, physical model: a course of two unison strings, nail strum, triangular body; tremolo.",
    "cimbalom_pm": "Cimbalom, physical model: three strings per course struck by cotton hammers, shimmering ring; damp.",
    "koto": "箏 (koto), physical model: ivory-pick pluck near the bridge, long ring; bend (押し), vib (揺り), harm, damp.",
    "shamisen": "三味線, physical model: bachi on string and skin, sawari buzz (buzz 0–1, stronger when plucked harder); bend, vib.",
    "banjo": "Banjo, physical model: steel strings on a drum head, metal fingerpicks, bright and short; bend, harm.",
    "kalimba": "Kalimba, physical model: a tine's cantilever modes, thumbnail click, box; reads ring, damp, decay.",
    "musicbox_pm": "Music box, physical model: comb teeth (weighted in the bass), pin click, twin teeth, box; reads ring, damp, decay.",
}
for _k, _v in ABOUT.items():
    INSTR[_k].about = _v
