"""Beat grid + accents for an external music track → beats.json (feeds bpm/offset in engines, cut timing, SFX and hit placement).

usage (via bin/vh beats): python tools/audio/beats.py <audio> [out.json] [--no-drums] [--lift-window 2.0] [--lift-dip 6]
Output: {"bpm","offset","beats":[s…],"downbeats":[s…],"duration","note",
         "hits":[{"t","strength"}…],                                   every onset peak (any instrument)
         "kick":[{"t","strength"}…], "snare":[{"t","strength"}…],      drums only (omitted with --no-drums)
         "lifts":[{"t","dip","depth_db","rise_db","strength","on"}…]}  candidate "breath, then the hit" points
lifts: a downbeat or a strong accent (strength ≥ 0.5) that comes within --lift-window s (2.0) after a dip in the track's
level — the 100 ms level falls at least --lift-dip dB (6) under the median of the 4 s before it — and lands at least
1.5 × that above the dip. t is the accent's own time (so as exact as the beat or hit it is), dip where the level is lowest,
strength 0..1 from the depth, the rise and the accent's strength; one per dip (the first accent after it). Candidates
only, for a person or the project to pick from: where a hero hit, a title or a cut could land (tools/audio/README.md).
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
import json, sys, warnings
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfiltfilt
try:
    import librosa  # provided by `uv run --with librosa` (with numpy + scipy)
except ImportError:  # lifts() needs only numpy: tools/ci.sh tests it without librosa
    librosa = None

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

LIFT = {"window": 2.0, "dip": 6.0}                          # s before the accent the dip may be in; dB under what came before

def level(y, sr, win=0.1, hop=0.01):
    """The track's level (dB) every hop s, each a centred win s mean of the power."""
    c = np.concatenate([[0.0], np.cumsum(np.asarray(y, float) ** 2)]); h, w = int(hop * sr), int(win * sr)
    n = np.arange(0, len(y), h); lo, hi = np.maximum(n - w // 2, 0), np.minimum(n + w // 2, len(y))
    return 10 * np.log10((c[hi] - c[lo]) / np.maximum(hi - lo, 1) + 1e-10)

def lifts(y, sr, events, window=LIFT["window"], dip_db=LIFT["dip"]):
    """Candidate lifts: an accent (events: [{"t","strength","on"}]) soon after a dip in the level → see the module doc."""
    H = 0.01; L = level(y, sr, hop=H); at = lambda t: min(max(int(round(t / H)), 0), len(L))
    out, used = [], set()
    for ev in sorted(events, key=lambda e: e["t"]):
        t = ev["t"]; a, b = at(t - window), at(t - 0.05)
        if b - a < 5:
            continue
        k = a + int(np.argmin(L[a:b]))
        ctx = L[at(k * H - 4.0):at(k * H - 0.25)]             # what came before the dip
        if k in used or len(ctx) < 25:                        # one per dip; a quiet opening is an intro, not a breath
            continue
        depth, rise = float(np.median(ctx) - L[k]), float(L[at(t):max(at(t + 0.3), at(t) + 1)].max() - L[k])
        if depth < dip_db or rise < 1.5 * dip_db:
            continue
        used.add(k)
        s = ev.get("strength", 1.0) * (0.5 * min(1.0, depth / (3 * dip_db)) + 0.5 * min(1.0, rise / (4 * dip_db)))
        out.append({"t": round(t, 3), "dip": round(k * H, 3), "depth_db": round(depth, 1), "rise_db": round(rise, 1),
                    "strength": round(s, 3), "on": ev.get("on", [])})
    return out

def accents(res, floor=0.5):
    """Downbeats and strong hits / kicks / snares, merged within 50 ms: the events a lift can land on."""
    ev = [{"t": t, "strength": 0.5, "on": ["downbeat"]} for t in res.get("downbeats", [])]
    ev += [{"t": h["t"], "strength": h["strength"], "on": [k]} for k in ("hits", "kick", "snare") for h in res.get(k, []) if h["strength"] >= floor]
    out = []
    for e in sorted(ev, key=lambda e: e["t"]):
        if out and e["t"] - out[-1]["t"] <= 0.05:
            m = out[-1]; m["on"] = sorted(set(m["on"]) | set(e["on"]))
            if e["strength"] > m["strength"]:                 # the time of the strongest one (an onset over the beat grid's)
                m["t"], m["strength"] = e["t"], e["strength"]
        else:
            out.append(dict(e))
    return out

def main():
    for k in ("window", "dip"):                               # --lift-window S, --lift-dip DB
        if f"--lift-{k}" in sys.argv:
            i = sys.argv.index(f"--lift-{k}")
            try:
                LIFT[k] = float(sys.argv[i + 1]); del sys.argv[i:i + 2]
            except (IndexError, ValueError):
                sys.exit(f"--lift-{k} wants a number (default {LIFT[k]:g})")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    def no(msg): print(f"beats: {msg}", file=sys.stderr); sys.exit(2)   # one line, not a traceback
    if not args: no("which track? usage: bin/vh beats <audio> [out.json] [--no-drums] [--lift-window 2.0] [--lift-dip 6]")
    src = args[0]
    out = Path(args[1]) if len(args) > 1 else Path(src).with_suffix(".beats.json")
    if not Path(src).is_file(): no(f"no such file: {src}")
    if not out.parent.is_dir(): no(f"no such folder for the beat map: {out.parent}")
    try:
        with warnings.catch_warnings():   # librosa's "PySoundFile failed. Trying audioread instead" on an mp3 or a bad file
            warnings.simplefilter("ignore"); y, sr = librosa.load(src, sr=22050, mono=True)
    except Exception as e:   # soundfile, audioread and ffmpeg each raise their own kind for a file they cannot decode
        why = str(e).strip().splitlines()[-1] if str(e).strip() else ""
        no(f"{src}: not audio librosa can read ({type(e).__name__}{': ' + why if why else ''})")
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beats = [round(float(t), 3) for t in librosa.frames_to_time(frames, sr=sr)]
    bpm = round(float(tempo[0] if hasattr(tempo, "__len__") else tempo), 2)
    res = {"bpm": bpm, "offset": beats[0] if beats else 0.0, "beats": beats, "downbeats": beats[::4],
           "duration": round(len(y) / sr, 3),
           "note": "downbeats assume 4/4 from the first beat; verify by ear and shift if needed"}
    res["hits"] = hits(y, sr)
    if "--no-drums" not in sys.argv: res.update(drums(y, sr))
    res["lifts"] = lifts(y, sr, accents(res), LIFT["window"], LIFT["dip"])
    out.write_text(json.dumps(res, indent=2))
    extra = (f"  kick {len(res['kick'])}  snare {len(res['snare'])}" if "kick" in res else "") + f"  lifts {len(res['lifts'])}"
    print(f"bpm {bpm}  offset {res['offset']}s  {len(beats)} beats  {len(res['hits'])} hits{extra} → {out}")

if __name__ == "__main__":
    main()
