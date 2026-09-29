"""Beat grid + accents for an external music track → beats.json (feeds bpm/offset in engines, cut timing, SFX and hit placement).

usage (via bin/vh beats): python tools/audio/beats.py <audio> [out.json] [--no-drums]
Output: {"bpm","offset","beats":[s…],"downbeats":[s…],"duration","note",
         "hits":[{"t","strength"}…],                                   every onset peak (any instrument)
         "kick":[{"t","strength"}…], "snare":[{"t","strength"}…]}      drums only (omitted with --no-drums)
strength is 0..1 relative to the track's own strong hits (1 = at or above the 90th percentile), for scaling accents.
kick/snare: percussive part of the track (librosa HPSS) → zero-phase band split → onset = sharpest rise of a trailing
energy window. Low band 40–150 Hz = kick; mid/high 1.2–5 kHz = snare/clap, kept only if noise-like (spectral flatness),
so hats (above the band) and pitched plucks drop out. Timing on synthetic loops with known hits: ~0–3 ms mean, ≤ 25 ms max
(playbook/04-audio.md); design for ±1 frame (33 ms at 30 fps). Limits: a plucked bass in the kick register reads as kick,
toms as kick, very soft ghost notes can be missed — check against the beat grid before hard-cutting.
downbeats assume 4/4 and start on the first detected beat — check them against the music and shift if needed.
On calm music the detected BPM is an imposed metronome; don't hard-cut to it (see playbook/04-audio.md).
For higher-accuracy downbeats use beat_this (CPJKU) instead.
"""
import json, sys
from pathlib import Path
import numpy as np
import librosa  # provided by `uv run --with librosa` (with numpy + scipy)
from scipy.signal import butter, sosfiltfilt

HOP = 128                                                  # accent frames: 5.8 ms at 22.05 kHz
DRUMS = {"kick": (40, 150, .020), "snare": (1200, 5000, .010)}   # band (Hz) and trailing energy window (s)

def rel(v):  # strengths relative to the strong hits (90th percentile), so one huge impact doesn't flatten the rest
    return np.minimum(1, v / (np.percentile(v, 90) or 1)) if len(v) else v

def hits(y, sr):
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP, n_fft=1024)
    fr = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=HOP, units="frames")
    return [{"t": round(float(f * HOP / sr), 3), "strength": round(float(s), 3)} for f, s in zip(fr, rel(env[fr]))]

def flatness(x, i, lo, hi, sr, n=1024):  # geometric / arithmetic mean power in the band just after an onset (noise ≈ 0.5+)
    X = np.abs(np.fft.rfft(np.pad(x[i:i + n], (0, max(0, i + n - len(x)))) * np.hanning(n))) ** 2 + 1e-12
    f = np.fft.rfftfreq(n, 1 / sr); B = X[(f >= lo) & (f < hi)]
    return float(np.exp(np.log(B).mean()) / B.mean())

def drums(y, sr):
    yp = librosa.effects.percussive(y, margin=3.0); k = lambda s: max(1, int(s * sr / HOP)); out = {}
    for name, (lo, hi, win) in DRUMS.items():
        x = sosfiltfilt(butter(4, [lo, hi], "band", fs=sr, output="sos"), yp)
        c = np.concatenate([[0], np.cumsum(x ** 2)]); w = int(win * sr); n = np.arange(0, len(x), HOP)
        e = (c[n + 1] - c[np.maximum(0, n + 1 - w)]) / w                       # trailing window: rises AT the onset
        L = 10 * np.log10(e + e.max() * 1e-3 + 1e-20)                            # dB above a −30 dB floor
        rise = np.concatenate([[0], np.maximum(0, L[2:] - L[:-2]), [0]]); rise /= rise.max() or 1
        fr = librosa.util.peak_pick(rise, pre_max=k(.03), post_max=k(.03) + 1, pre_avg=k(.1), post_avg=k(.1) + 1, delta=.1, wait=k(.06))
        fr = [f for f in fr if rise[f] >= .3 and (name == "kick" or flatness(yp, f * HOP, lo, hi, sr) >= .35)]
        amp = np.sqrt(np.array([e[f:f + k(.05)].max() for f in fr]))
        out[name] = [{"t": round(float(f * HOP / sr), 3), "strength": round(float(s), 3)} for f, s in zip(fr, rel(amp))]
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = args[0]
    out = Path(args[1]) if len(args) > 1 else Path(src).with_suffix(".beats.json")
    y, sr = librosa.load(src, sr=22050, mono=True)
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beats = [round(float(t), 3) for t in librosa.frames_to_time(frames, sr=sr)]
    bpm = round(float(tempo[0] if hasattr(tempo, "__len__") else tempo), 2)
    res = {"bpm": bpm, "offset": beats[0] if beats else 0.0, "beats": beats, "downbeats": beats[::4],
           "duration": round(len(y) / sr, 3),
           "note": "downbeats assume 4/4 from the first beat; verify by ear and shift if needed"}
    res["hits"] = hits(y, sr)
    if "--no-drums" not in sys.argv: res.update(drums(y, sr))
    out.write_text(json.dumps(res, indent=2))
    extra = f"  kick {len(res['kick'])}  snare {len(res['snare'])}" if "kick" in res else ""
    print(f"bpm {bpm}  offset {res['offset']}s  {len(beats)} beats  {len(res['hits'])} hits{extra} → {out}")

if __name__ == "__main__":
    main()
