"""Checks for music.wav against music.beats.json: spectrogram, RMS per beat, onset cue check, stop silence,
no-hole RMS check, pump check and click check (v3).

usage: uv run --with numpy --with scipy --with matplotlib --with librosa \
         python audio/check_score.py audio/music.wav [--stems DIR] [--wave assets/wave.json]
writes audio/check/spectrogram.png, audio/check/rms-per-beat.png, audio/check/cuecheck.txt,
       audio/check/mixcheck.txt (holes, pumping, clicks)
--stems DIR: stems from `score_engine.py --stems DIR`; swell/riser peaks are then measured on fx.wav alone
--wave PATH: {"rms": [400 values]} of the mix RMS envelope, normalised to 0..1, for the film to draw
"""
import json
import sys
from pathlib import Path

import librosa
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft

FPS = 30
PEAK_KINDS = ("swell>", "riser>")          # hits that are the peak of a swell, not a transient onset


def load(path):
    sr, x = wavfile.read(path)
    x = x.astype(np.float64) / 32768.0
    return sr, x, x.mean(axis=1)


def rms_db(x, sr, win=0.02, hop=0.005):
    w, h = int(win * sr), int(hop * sr)
    frames = librosa.util.frame(np.pad(x, (w // 2, w // 2)), frame_length=w, hop_length=h)
    r = np.sqrt((frames ** 2).mean(axis=0))
    return np.arange(len(r)) * hop, 20 * np.log10(r + 1e-10)


def marker_hits(bm):
    keys = ("braam", "impact", "fail", "pass", "gate", "spark", "hold")
    return [h for h in bm["hits"] if any(h["what"].startswith(k) for k in keys) and ">" not in h["what"]]


def plot_spectrogram(sr, mono, bm, out):
    f, t, Z = stft(mono, fs=sr, nperseg=4096, noverlap=4096 - 512)
    S = 20 * np.log10(np.abs(Z) + 1e-9)
    S -= S.max()
    fig, ax = plt.subplots(figsize=(26, 9), dpi=90)
    keep = (f >= 20) & (f <= 20000)
    ax.pcolormesh(t, f[keep], S[keep], vmin=-90, vmax=0, cmap="magma", shading="auto")
    ax.set_yscale("log")
    ax.set_ylim(20, 20000)
    for i, d in enumerate(bm["downbeats"]):
        ax.axvline(d, color="white", lw=0.6, alpha=0.5)
        ax.text(d + 0.05, 16000, str(i + 1), color="white", fontsize=8)
    for s in bm["stops"]:
        ax.axvspan(s["start"], s["end"], color="cyan", alpha=0.25)
        ax.text(s["start"], 25, "STOP", color="cyan", fontsize=8)
    for h in marker_hits(bm):
        ax.axvline(h["t"], color="lime", lw=1.2, ls="--")
        ax.text(h["t"] + 0.05, 40 if "fail" not in h["what"] else 60, h["what"], color="lime", fontsize=8, rotation=90)
    for s in bm["sections"]:
        ax.text(s["start"] + 0.1, 11000, s["name"], color="yellow", fontsize=11, weight="bold")
    ax.set_xlabel("seconds")
    ax.set_ylabel("Hz (log)")
    ax.set_title("music.wav: log-frequency spectrogram (dB re max), bar lines white, stops cyan, key hits green")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_rms(sr, mono, bm, out):
    t, r = rms_db(mono, sr)
    beat = 60 / bm["bpm"]
    per_beat = []
    for b in bm["beats"]:
        seg = mono[int(b * sr): int((b + beat) * sr)]
        per_beat.append(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-10))
    fig, ax = plt.subplots(figsize=(26, 7), dpi=90)
    ax.plot(t, r, lw=0.5, color="0.35", label="RMS 20 ms")
    ax.step(np.array(bm["beats"]), per_beat, where="post", color="tab:orange", lw=1.8, label="RMS per beat")
    for b in bm["beats"]:
        ax.axvline(b, color="0.85", lw=0.4, zorder=0)
    for i, d in enumerate(bm["downbeats"]):
        ax.axvline(d, color="0.5", lw=0.9, zorder=0)
        ax.text(d + 0.05, 1, str(i + 1), fontsize=8)
    for s in bm["stops"]:
        ax.axvspan(s["start"], s["end"], color="cyan", alpha=0.3)
    for s in bm["sections"]:
        ax.text(s["start"] + 0.1, -6, s["name"], fontsize=11, weight="bold", color="tab:blue")
    for h in marker_hits(bm):
        ax.axvline(h["t"], color="green", lw=1, ls="--")
    ax.set_ylim(-80, 3)
    ax.set_xlim(0, bm["duration"])
    ax.set_xlabel("seconds")
    ax.set_ylabel("dBFS")
    ax.legend(loc="lower right")
    ax.set_title("music.wav: RMS envelope and RMS per beat (stops cyan, key hits green)")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def cue_check(sr, mono, bm, fx=None):
    hop = 256
    env = librosa.onset.onset_strength(y=mono.astype(np.float32), sr=sr, hop_length=hop, n_fft=2048)
    onsets = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, units="time",
                                        backtrack=False, delta=0.05)
    t_rms, r = rms_db(mono if fx is None else fx, sr, win=0.01, hop=0.001)
    rows, worst = [], 0.0
    for h in bm["hits"]:
        if h["what"].startswith(PEAK_KINDS):
            # on the fx stem the window stops before t, so an impact landing on t cannot win
            win = (t_rms > h["t"] - 0.5) & (t_rms < h["t"] + (0.03 if fx is None else -0.005))
            found = t_rms[win][np.argmax(r[win])]
            kind = "peak"
        else:
            found = onsets[np.argmin(np.abs(onsets - h["t"]))]
            kind = "onset"
        err = (found - h["t"]) * 1000
        worst = max(worst, abs(err))
        rows.append((h["t"], h["what"], kind, found, err))
    return rows, worst, onsets


def stop_silence(sr, x, bm):
    res = []
    for s in bm["stops"]:
        seg = x[int((s["start"] + 0.006) * sr): int((s["end"] - 0.001) * sr)]
        res.append((s["start"], s["end"], 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-12),
                    20 * np.log10(np.abs(seg).max() + 1e-12)))
    return res


def silent_runs(sr, x, thresh_db=-60.0, win=0.005, min_len=0.02):
    """Every stretch where the 5 ms RMS stays below thresh_db for at least min_len seconds."""
    w = int(win * sr)
    m = len(x) // w
    r = np.sqrt((x[: m * w] ** 2).mean(axis=1).reshape(m, w).mean(axis=1))
    quiet = 20 * np.log10(r + 1e-12) < thresh_db
    runs, start = [], None
    for i, q in enumerate(np.append(quiet, False)):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * win >= min_len:
                runs.append((start * win, i * win))
            start = None
    return runs


CHECK_FROM, CHECK_TO = 1.0, 66.5         # the final fade is exempt (overridden from the beat map's "fade")


def hole_check(sr, mono, bm, win=0.1, margin=12.0):
    """Every 0.1 s RMS window must be >= its section's median RMS - margin dB."""
    n = int(win * sr)
    m = len(mono) // n
    r = 20 * np.log10(np.sqrt((mono[: m * n].reshape(m, n) ** 2).mean(axis=1)) + 1e-12)
    t = (np.arange(m) + 0.5) * win
    rows, bad = [], []
    for s in bm["sections"]:
        sel = (t >= max(s["start"], CHECK_FROM)) & (t < min(s["end"], CHECK_TO))
        if not sel.any():
            continue
        med = np.median(r[sel])
        low = r[sel].min()
        rows.append((s["name"], med, low, low - med))
        bad += [(tt, rr, med) for tt, rr in zip(t[sel], r[sel]) if rr < med - margin]
    return rows, bad


def pump_check(sr, mono, bm, win=0.15, hop=0.01, span=0.5, limit=4.0):
    """Dips of the 150 ms RMS below its local (+/-0.5 s) median by more than `limit` dB, >= 30 ms long."""
    w, h = int(win * sr), int(hop * sr)
    frames = librosa.util.frame(np.pad(mono, (w // 2, w // 2)), frame_length=w, hop_length=h)
    e = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=0)) + 1e-12)
    t = np.arange(len(e)) * hop
    k = int(span / hop)
    from scipy.ndimage import median_filter
    ref = median_filter(e, size=2 * k + 1, mode="nearest")
    dip = ref - e
    live = (t >= CHECK_FROM) & (t <= CHECK_TO)
    over = (dip > limit) & live
    runs, start = [], None
    for i, o in enumerate(np.append(over, False)):
        if o and start is None:
            start = i
        elif not o and start is not None:
            if (i - start) * hop >= 0.03:
                runs.append((t[start], t[i - 1], dip[start:i].max()))
            start = None
    return runs, float(dip[live].max())


def click_check(sr, x, placements, thresh_db=24.0):
    """Isolated HF spikes (> thresh_db over the local level) that do not sit on a placed sound's start."""
    from scipy.ndimage import median_filter
    from scipy.signal import butter, sosfilt
    hf = np.abs(sosfilt(butter(4, 10000, "high", fs=sr, output="sos"), x, axis=0)).max(axis=1)
    b = int(0.001 * sr)
    m = len(hf) // b
    pk = hf[: m * b].reshape(m, b).max(axis=1)
    local = median_filter(pk, size=51, mode="nearest") + 1e-7
    ratio = 20 * np.log10(pk / local + 1e-12)
    starts = np.array(sorted(p[0] for p in placements))
    cand = np.flatnonzero((ratio > thresh_db) & (pk > 10 ** (-50 / 20)))      # audible: HF peak above -50 dBFS
    flagged = []
    for c in cand:
        tc = c * 0.001
        near = starts[np.searchsorted(starts, tc - 0.040): np.searchsorted(starts, tc + 0.003)]
        if len(near) == 0:
            flagged.append((tc, ratio[c], 20 * np.log10(pk[c])))
    return len(cand), flagged


def write_wave(mono, sr, dur, path, n=400):
    edges = np.linspace(0, len(mono), n + 1).astype(int)
    r = np.array([np.sqrt((mono[a:b] ** 2).mean()) for a, b in zip(edges[:-1], edges[1:])])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"rms": [round(float(v), 4) for v in r / r.max()], "n": n, "duration": dur,
                                      "note": "linear RMS of audio/music.wav in n equal bins over 0..duration, "
                                              "divided by the loudest bin"}))


def main():
    args = sys.argv[1:]
    opts = {}
    for flag in ("--stems", "--wave"):
        if flag in args:
            i = args.index(flag)
            opts[flag], args = args[i + 1], args[:i] + args[i + 2:]
    wav = Path(args[0])
    global CHECK_TO
    fade_info = json.loads(wav.with_suffix(".beats.json").read_text()).get("fade")
    if fade_info:
        CHECK_TO = round(fade_info["start"] - 1 / 6, 3)
    bm = json.loads(wav.with_suffix(".beats.json").read_text())
    out = wav.parent / "check"
    out.mkdir(exist_ok=True)
    sr, x, mono = load(wav)
    plot_spectrogram(sr, mono, bm, out / "spectrogram.png")
    plot_rms(sr, mono, bm, out / "rms-per-beat.png")
    fx = load(Path(opts["--stems"]) / "rise.wav")[2] if "--stems" in opts else None      # swells + risers only
    rows, worst, onsets = cue_check(sr, mono, bm, fx)
    stops = stop_silence(sr, x, bm)
    if "--wave" in opts:
        write_wave(mono, sr, bm["duration"], opts["--wave"])
    lines = [f"cue check: {wav.name} vs {wav.with_suffix('.beats.json').name}",
             f"duration {len(x) / sr:.4f} s ({len(x)} samples @ {sr} Hz), {len(onsets)} onsets detected "
             f"(librosa onset_detect, hop 256 = 5.3 ms)",
             "onset hits: error = nearest detected onset - hit time (librosa reports onsets ~5-10 ms late: "
             "hop and window centring)",
             "peak hits (swell>/riser>): time of the RMS maximum of " + ("the swell/riser stem in [t-0.5, t-0.005]"
             if fx is not None else "the mix in [t-0.5, t+0.03]") + " - hit time",
             "", f"{'t (s)':>9}  {'what':<22} {'kind':<5} {'found':>9}  {'err ms':>7}  {'err fr':>6}  ok"]
    for t, what, kind, found, err in rows:
        ok = "OK" if abs(err) <= 1000 / FPS else "OFF"
        lines.append(f"{t:9.4f}  {what:<22} {kind:<5} {found:9.4f}  {err:7.1f}  {err * FPS / 1000:6.2f}  {ok}")
    n_ok = sum(abs(r[4]) <= 1000 / FPS for r in rows)
    errs = np.array([abs(r[4]) for r in rows if r[2] == "onset"])
    lines += ["", f"{n_ok}/{len(rows)} hits within 1 frame (33.3 ms); worst {worst:.1f} ms; "
                  f"onset hits: median |err| {np.median(errs):.1f} ms, max {errs.max():.1f} ms",
              "", "stop windows (5 ms fades excluded):"]
    for a, b, rms, pk in stops:
        lines.append(f"  {a:8.4f}-{b:8.4f}  RMS {rms:7.1f} dBFS  peak {pk:7.1f} dBFS  "
                     f"{'SILENT' if rms < -60 else 'NOT SILENT'}")
    lines += ["", "every silent run in the file (5 ms RMS < -60 dBFS for >= 20 ms):"]
    for a, b in silent_runs(sr, x):
        lines.append(f"  {a:8.3f}-{b:8.3f}  ({(b - a) * 1000:5.0f} ms)")
    # v3 mix checks -> mixcheck.txt
    mix_lines = [f"mix checks: {wav.name}, window {CHECK_FROM}-{CHECK_TO} s (the final fade is exempt)", "",
                 "1. holes: every 0.1 s RMS window >= section median - 12 dB",
                 f"   {'section':<10} {'median':>8} {'lowest':>8} {'margin':>8}"]
    rows, bad = hole_check(sr, mono, bm)
    for name, med, low, mar in rows:
        mix_lines.append(f"   {name:<10} {med:8.1f} {low:8.1f} {mar:8.1f} dB")
    mix_lines.append(f"   violations: {len(bad)}" + "".join(f"\n     {tt:7.2f} s  {rr:6.1f} dBFS (median {md:6.1f})"
                                                      for tt, rr, md in bad[:40]))
    runs, worst = pump_check(sr, mono, bm)
    holds = bm.get("holds", [])
    mix_lines += ["", "2. pumping: 150 ms RMS vs its +/-0.5 s median; dips > 4 dB lasting >= 30 ms",
                  f"   largest dip anywhere: {worst:.1f} dB; dips over 4 dB: {len(runs)}"]
    for a, b, d in runs:
        tag = "in a hold (designed)" if any(h["start"] - 0.05 <= a <= h["end"] for h in holds) else ""
        mix_lines.append(f"     {a:7.2f}-{b:7.2f} s  {d:4.1f} dB  {tag}")
    pl_path = wav.parent / "check" / "placements.json"
    if pl_path.exists():
        placements = json.loads(pl_path.read_text())
        n_cand, flagged = click_check(sr, x, placements)
        mix_lines += ["", "3. clicks: 1 ms HF (>10 kHz) peaks > 24 dB above the local median (50 ms), not on the start",
                      f"   of any of the {len(placements)} placed sounds (a start in the 40 ms before, or 3 ms after:",
                      "   onset transients and the first driven-saw cycles of a pluck); HF peak above -50 dBFS",
                      f"   HF spikes: {n_cand}, all on a placed sound's start except: {len(flagged)}"]
        for tc, rt, lv in flagged[:30]:
            mix_lines.append(f"     {tc:8.3f} s  +{rt:4.1f} dB  ({lv:6.1f} dBFS)")
    (out / "mixcheck.txt").write_text("\n".join(mix_lines) + "\n")
    print("\n".join(mix_lines))
    txt = "\n".join(lines) + "\n"
    (out / "cuecheck.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
