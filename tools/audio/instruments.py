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
is music.ks with a pluck position and a hammer option. Everything else is written for this file.
"""
import zlib
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, lfilter, fftconvolve

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


def guqin(m, dur, vel, rng, P):
    """Low silk string, very long ring. Per note (art dict or params): slide (start this many semitones away and glide in),
    bend (press after the pluck), yin (吟, small vibrato), nao (猱, wide slow vibrato), harm (泛音: a pure harmonic)."""
    f0 = float(mtof(m)); n = int(min(float(np.clip(6 * (131 / f0) ** 0.3, 3, 9)), 5.0) * SR); t = secs(n)
    if P.get("harm"):
        x = modal(f0, n, [(1, 1.0, 1.6), (2, 0.15, 0.6), (3, 0.04, 0.3)]) + burst(rng, n, 2000, 8000, 0.001, 0.1)
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
    """HUD sequence voice: a short saw (or square) blip through a resonant low-pass with a snappy envelope."""
    f0 = float(mtof(m)); n = int(min(dur + 0.05, 0.6) * SR); t = secs(n)
    x = pulse(f0, n, 0.5) if P.get("wave") == "square" else saw(f0, n)
    base = float(P.get("cutoff", 1200)); fc = base * (1 + float(P.get("env", 3.0)) * vel * np.exp(-t / 0.06))
    x = sweep_lp(x, fc, res=float(P.get("res", 3.0)), block=32)
    return fade(x * np.exp(-t / float(P.get("decay", 0.12))) * release_after(n, dur, 0.02), 0.001, 0.005)


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
    pitch falls (240 Hz, -2.5 semitones); the 小锣 rises."""
    g = LUOGU.get(art, LUOGU["仓"]); parts = []
    if g[0]: parts.append(g[0] * gong(vel, "", dur, rng, {"tune": 240.0, "drop": -2.5, "drop_time": 0.25, "decay": 1.6, "length": 3.0}))
    if g[1]: parts.append(g[1] * smallgong(vel, "", dur, rng, P) * 0.8)
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
}
for _k, _v in ABOUT.items():
    INSTR[_k].about = _v
