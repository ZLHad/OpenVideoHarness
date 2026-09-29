"""Independent audio QA for the film mix (v3 brief): dropouts, pumping, clicks, and an RMS evidence plot.

usage: uv run -q --with numpy --with scipy --with matplotlib python tools/audio_qa.py <mix.wav> <beats.json> <label> [--compare other.wav:label2]
writes out/check/audio-qa-<label>.txt and (with --compare) out/check/audio-rms-<label2>-vs-<label>.png

Checks
  1. silence / dropout: 0.1 s RMS windows vs the median of their section; FAIL if < median - 12 dB
     (1.0 s .. 66.5 s; the head and the final fade are exempt). Also lists digital-silence runs (< -60 dBFS, >= 20 ms).
  2. pumping: 50 ms RMS (hop 10 ms) vs a 600 ms rolling median; a dip > 4 dB lasting >= 60 ms that does not start
     within [-0.05, +0.40] s of a designed transient hit is flagged.
  3. clicks: sample-level discontinuities; |second difference| > 25x its local (5 ms) RMS and > -40 dBFS.
"""
import json, sys, wave
import numpy as np
from scipy.ndimage import median_filter

def load(p):
    with wave.open(p) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16 if w.getsampwidth() == 2 else np.int32).astype(np.float64)
    x /= 32768.0 if x.dtype and np.abs(x).max() <= 32768 else 2 ** 31
    x = x.reshape(-1, ch).mean(axis=1) if ch > 1 else x
    return x, sr

def rms_frames(x, sr, win, hop):
    w, h = int(win * sr), int(hop * sr)
    n = 1 + (len(x) - w) // h
    idx = np.arange(w)[None, :] + h * np.arange(n)[:, None]
    r = np.sqrt((x[idx] ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(r), (np.arange(n) * h + w / 2) / sr

def main():
    wav, beats, label = sys.argv[1], sys.argv[2], sys.argv[3]
    cmp = [a.split("=", 1)[1] if a.startswith("--compare=") else None for a in sys.argv[4:]]
    cmp = next((c for c in cmp if c), None)
    x, sr = load(wav); B = json.load(open(beats))
    F = B.get("fade"); END = (F[0] if isinstance(F, list) else F.get("start", F.get("from"))) if F else len(x) / sr - 2.8  # the final fade is exempt
    secs = B.get("sections", [])
    hits = [h["t"] for h in B.get("hits", []) if h.get("kind", "transient") == "transient"]
    out = [f"audio QA · {wav} · {len(x)/sr:.3f} s"]
    # 1. dropouts vs section median
    db, tt = rms_frames(x, sr, 0.1, 0.05)
    viol = []
    for s in secs:
        m = (tt >= s["start"]) & (tt < s["end"])
        if not m.any(): continue
        med = np.median(db[m])
        bad = m & (db < med - 12) & (tt >= 1.0) & (tt <= END)
        for t_, d_ in zip(tt[bad], db[bad]): viol.append((t_, d_, s["name"], med))
    out.append(f"[1] dropouts (0.1 s RMS < section median - 12 dB, 1.0-{END:.1f} s): {len(viol)} windows")
    runs = []
    for t_, d_, name, med in viol:
        if runs and t_ - runs[-1][1] <= 0.06: runs[-1][1] = t_
        else: runs.append([t_, t_, name, d_, med])
    for a, b, name, d_, med in runs: out.append(f"    {a:6.2f}-{b:6.2f} s  {name}: {d_:.1f} dBFS vs median {med:.1f}")
    d5, t5 = rms_frames(x, sr, 0.005, 0.005)
    sil = d5 < -60; srun = []; i = 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]: j += 1
            if (j - i) * 0.005 >= 0.02: srun.append((t5[i], t5[j - 1]))
            i = j
        else: i += 1
    out.append(f"    digital-silence runs (< -60 dBFS, >= 20 ms): " + (", ".join(f"{a:.3f}-{b:.3f}" for a, b in srun) or "none"))
    # 2. pumping
    e, te = rms_frames(x, sr, 0.05, 0.01)
    base = median_filter(e, size=61, mode="nearest")
    dip = base - e; flag = dip > 4; pumps = []; i = 0
    while i < len(flag):
        if flag[i]:
            j = i
            while j < len(flag) and flag[j]: j += 1
            if (j - i) * 0.01 >= 0.06 and 1.0 <= te[i] <= END:
                near = any(-0.05 <= te[i] - h <= 0.40 for h in hits)
                if not near: pumps.append((te[i], te[j - 1], float(dip[i:j].max())))
            i = j
        else: i += 1
    out.append(f"[2] pumping dips > 4 dB for >= 60 ms, not at a designed hit: {len(pumps)}")
    for a, b, d in pumps[:40]: out.append(f"    {a:6.2f}-{b:6.2f} s  depth {d:.1f} dB")
    # 3. clicks
    d2 = np.abs(np.diff(x, 2)); k = int(0.005 * sr)
    loc = np.sqrt(np.convolve(d2 ** 2, np.ones(k) / k, mode="same") + 1e-18)
    cand = np.where((d2 > 25 * loc) & (d2 > 10 ** (-40 / 20)))[0]
    clicks = []
    for c in cand:
        if not clicks or c - clicks[-1] > sr * 0.01: clicks.append(c)
    out.append(f"[3] sample discontinuities (clicks): {len(clicks)}" + ("  at " + ", ".join(f"{c/sr:.3f}" for c in clicks[:30]) if clicks else ""))
    txt = "\n".join(out); print(txt)
    open(f"out/check/audio-qa-{label}.txt", "w").write(txt + "\n")
    if cmp:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        p2, l2 = cmp.split(":")
        y, _ = load(p2); db2, tt2 = rms_frames(y, sr, 0.1, 0.05)
        fig, ax = plt.subplots(figsize=(16, 4.8), dpi=110)
        ax.plot(tt, db, lw=0.8, color="#888", label=f"{label}")
        ax.plot(tt2, db2, lw=1.0, color="#e6a019", label=f"{l2}")
        for s in secs:
            ax.axvline(s["start"], color="#ccc", lw=0.6); ax.text(s["start"] + 0.2, -8, s["name"], fontsize=8, color="#555")
            m = (tt2 >= s["start"]) & (tt2 < s["end"])
            if m.any(): med = np.median(db2[m]); ax.hlines(med - 12, s["start"], s["end"], colors="#d33", lw=0.8, linestyles="--")
        ax.set_ylim(-80, -2); ax.set_xlim(0, len(x) / sr); ax.set_xlabel("s"); ax.set_ylabel("0.1 s RMS (dBFS)")
        ax.set_title(f"RMS envelope: {label} (grey) vs {l2} (amber); red dashed = {l2} section median - 12 dB (dropout floor)")
        ax.legend(loc="lower right"); fig.tight_layout(); fig.savefig(f"out/check/audio-rms-{l2}-vs-{label}.png")

if __name__ == "__main__":
    main()
