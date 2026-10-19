"""Voice measures for bin/vh tts --candidates and bin/vh voices audition (numpy only; audio read through ffmpeg, 16 kHz mono).

features(x): the pitch median (Hz, voiced frames, autocorrelation 70–400 Hz), the spectral centroid (Hz, median over the
voiced frames), an MFCC profile (the mean of c1–c12 over the voiced frames: timbre without loudness) and the seconds of
speech (from the first voiced 10 ms to the last, every silence of 0.12 s or more left out, as bin/vh pace counts it).
pick(takes): per block, the take closest to the median voice of every take: distance² = (pitch difference / 1 semitone)²
+ (centroid difference / 2 semitones)² + (MFCC distance / its median over the takes)². The weights are a starting point,
not a rule: the table it prints is there to listen against.
"""
import subprocess
import numpy as np

SR = 16000
HOP, WIN = 0.01, 0.04             # frame step and length (s)
BELOW, FLOOR = 32.0, -45.0        # voiced = within BELOW dB of the take's speech level (95th percentile), never under FLOOR
PAUSE = 0.12                      # a silence this long inside the speech is a pause (shorter: between syllables)
FMIN, FMAX = 70.0, 400.0
WEIGHTS = {"pitch_st": 1.0, "centroid_st": 2.0}   # one unit of distance: 1 semitone of pitch, 2 of centroid

def read(wav, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(sr), "-f", "f32le", "pipe:1"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)

def _frames(x, sr):
    h, w = int(HOP * sr), int(WIN * sr)
    n = max(0, (len(x) - w) // h + 1)
    if n == 0:
        return np.zeros((0, w))
    return np.lib.stride_tricks.as_strided(x, shape=(n, w), strides=(x.strides[0] * h, x.strides[0])).copy()

def voiced(x, sr=SR):
    """10 ms frames → True where the voice is."""
    h = int(HOP * sr); n = len(x) // h
    if n == 0:
        return np.zeros(0, bool)
    db = 10 * np.log10(np.mean(x[: n * h].reshape(n, h) ** 2, axis=1) + 1e-18)
    return db > max(FLOOR, float(np.percentile(db, 95)) - BELOW)

def speech_seconds(x, sr=SR):
    v = voiced(x, sr); idx = np.flatnonzero(v)
    if not len(idx):
        return 0.0
    q = ~v[idx[0]: idx[-1] + 1]; pauses = 0; run = 0
    for z in np.append(q, False):
        if z:
            run += 1
        else:
            pauses += run if run * HOP >= PAUSE - 1e-9 else 0; run = 0
    return (len(q) - pauses) * HOP

def _mel(n_fft, sr, n=26, lo=60.0, hi=7600.0):
    mel = lambda f: 2595 * np.log10(1 + f / 700); inv = lambda m: 700 * (10 ** (m / 2595) - 1)
    edges = inv(np.linspace(mel(lo), mel(min(hi, sr / 2)), n + 2)); f = np.fft.rfftfreq(n_fft, 1 / sr)
    fb = np.zeros((n, len(f)))
    for k in range(n):
        a, c, b = edges[k], edges[k + 1], edges[k + 2]
        fb[k] = np.clip(np.minimum((f - a) / (c - a), (b - f) / (b - c)), 0, None)
    return fb

def features(x, sr=SR):
    F = _frames(x, sr); n = len(F)
    hv = voiced(x, sr)
    k = min(n, len(hv)); sel = np.zeros(n, bool); sel[:k] = hv[:k]   # a frame starts at its 10 ms step
    out = {"speech_s": round(speech_seconds(x, sr), 3), "pitch_hz": None, "centroid_hz": None, "mfcc": None, "voiced_frames": int(sel.sum())}
    if not sel.any():
        return out
    V = F[sel] * np.hanning(F.shape[1]); n_fft = 1024
    S = np.abs(np.fft.rfft(V, n_fft)) ** 2
    L = int(sr / FMIN) + 2; wac = np.fft.irfft(np.abs(np.fft.rfft(np.hanning(F.shape[1]), n_fft)) ** 2, n_fft)[:L]
    ac = np.fft.irfft(S, n_fft)[:, :L] / (wac / wac[0]); ac /= ac[:, :1] + 1e-12   # the window's own taper taken out
    lo, hi = int(sr / FMAX), int(sr / FMIN)
    seg = ac[:, lo:hi + 1]; best = seg.max(axis=1); f0 = []
    for r, b in zip(seg, best):
        if b <= 0.5:
            continue
        j = int(np.argmax(r >= 0.85 * b))                  # the shortest lag near the best (no octave drop), then its peak
        while j + 1 < len(r) and r[j + 1] > r[j]:
            j += 1
        y0, y1, y2 = r[max(j - 1, 0)], r[j], r[min(j + 1, len(r) - 1)]
        dj = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if y0 - 2 * y1 + y2 < 0 else 0.0   # parabolic: between two lags
        f0.append(sr / (j + lo + dj))
    f0 = np.array(f0)
    f = np.fft.rfftfreq(n_fft, 1 / sr); mag = np.sqrt(S)
    cent = (mag * f).sum(axis=1) / (mag.sum(axis=1) + 1e-12)
    logmel = np.log10(S @ _mel(n_fft, sr).T + 1e-10)
    m = logmel.shape[1]; dct = np.cos(np.pi / m * (np.arange(m) + 0.5)[None, :] * np.arange(13)[:, None])
    mfcc = (logmel @ dct.T)[:, 1:13]
    out.update(pitch_hz=round(float(np.median(f0)), 1) if len(f0) else None, centroid_hz=round(float(np.median(cent)), 1),
               mfcc=[round(float(v), 4) for v in mfcc.mean(axis=0)])
    return out

def st(a, b):
    return 12 * np.log2(a / b) if a and b else 0.0

def pick(takes):
    """takes: {block: [features, …]} → ({block: index of the chosen take}, median voice, {block: [distance, …]})."""
    allf = [f for fs in takes.values() for f in fs if f.get("pitch_hz")]
    if not allf:
        return {b: 0 for b in takes}, None, {b: [None] * len(fs) for b, fs in takes.items()}
    med = {"pitch_hz": float(np.median([f["pitch_hz"] for f in allf])), "centroid_hz": float(np.median([f["centroid_hz"] for f in allf])),
           "mfcc": np.median(np.array([f["mfcc"] for f in allf]), axis=0)}
    md = lambda f: float(np.linalg.norm(np.array(f["mfcc"]) - med["mfcc"]))
    scale = float(np.median([md(f) for f in allf])) or 1.0
    def dist(f):
        if not f.get("pitch_hz"):
            return float("inf")
        return float(np.sqrt((st(f["pitch_hz"], med["pitch_hz"]) / WEIGHTS["pitch_st"]) ** 2
                             + (st(f["centroid_hz"], med["centroid_hz"]) / WEIGHTS["centroid_st"]) ** 2 + (md(f) / scale) ** 2))
    d = {b: [dist(f) for f in fs] for b, fs in takes.items()}
    return {b: int(np.argmin(v)) for b, v in d.items()}, {"pitch_hz": round(med["pitch_hz"], 1), "centroid_hz": round(med["centroid_hz"], 1)}, d
