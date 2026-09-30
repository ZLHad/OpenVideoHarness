"""Audio QA on the FINAL mix: scan for silence, dropouts, pumping and clicks; cue-check audible onsets against the grid.

usage (via bin/vh qa):
  python tools/audio/qa.py <mix> [beats.json] [events.json] [--fps 30] [--from 1.0] [--to S] [--voice vo.wav]
                          [--click-grace 0.04] [--out report.txt]                                              both
  python tools/audio/qa.py scan <mix> [beats.json] [--events events.json] [...]                               scan only
  python tools/audio/qa.py cues <mix> <beats.json|-> [events.json] [...]                                       cues only
<mix>: anything ffmpeg decodes (wav, m4a, the muxed mp4). beats.json: music.beats.json (sections, hits, fade) or the
output of beats.py; events.json: the SFX event list. Exit status 1 if silence, dropouts, pumping or the cue check fail
(usable as a gate); clicks are only a warning.

scan (checked span: --from, default 1.0 s, to --to, default the beat map's fade start, else the last 2.8 s)
  silence   digital-silence runs (< −60 dBFS, ≥ 20 ms). Inside the span they FAIL: a dramatic "stop" must keep a bed.
  dropouts  0.1 s RMS windows < their section's median − 12 dB (sections from beats.json, else 8 s blocks).
  pumping   50 ms RMS vs a 600 ms rolling median: a dip > 4 dB for ≥ 60 ms that does not start within −0.05…+0.40 s
            of a transient music hit. A music ducker keyed on every SFX shows up here. Not counted: a gradual sag that
            ends in an attack (a sparse bell/pluck decaying before the next strike), and with --voice, dips that start
            while the voiceover is speaking (the designed duck under narration).
  clicks    WARNING only (a machine can't tell a designed sharp attack — a saw note head, a hard-gated glitch — from a
            fault): per channel, |2nd difference| > 15 × its local RMS (5 ms window, the ±1 ms around the sample left
            out, so an isolated click can stand out) and > −40 dBFS, outside ±--click-grace (0.04 s) of a designed onset
            (beat map hits and beats, SFX event times). Lists the total and the 10 worst (time, bar:beat, ratio) to
            listen to by ear.
cues: onsets of the mix (librosa, hop 128 at 48 kHz) vs every transient music hit (riser/swell peaks and kind ≠ transient
  skipped) and every SFX event louder than −18 dB (gain_db − 20·log10(dist); swells whoosh/swish_rev/riser skipped).
  OK = nearest onset within 1 frame (1/fps).
Known limits: pumping misses long shallow dips (≈ 300 ms at −8 dB fills half the 600 ms median; only the −12 dB dropout
  check catches it); cue check normalises onsets to the loudest one in the file, so one huge onset elsewhere can hide a
  weak cue; clicks are judged against local HF content, so a click deep inside noise can still pass, and designed
  attacks off the grace windows (16th-note ostinato heads, a typing burst, glitch gating) are listed too.
"""
import json, subprocess, sys
import numpy as np
from scipy.ndimage import median_filter, maximum_filter1d

SWELLS = ("whoosh", "swish_rev", "riser")

def load(path, sr=None):  # → float32 (n, ch), sr — via ffmpeg, so containers and codecs all work
    st = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate,channels",
                                    "-of", "json", path], capture_output=True, text=True, check=True).stdout)["streams"][0]
    sr = sr or int(st["sample_rate"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ar", str(sr), "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, int(st["channels"])), sr

def rms_db(x, sr, win, hop):  # O(n) windowed RMS in dBFS + window centre times
    w, h = int(win * sr), int(hop * sr); c = np.concatenate([[0], np.cumsum(x.astype(np.float64) ** 2)]); s = np.arange(0, len(x) - w + 1, h)
    return 10 * np.log10(np.maximum(c[s + w] - c[s], 0) / w + 1e-12), (s + w / 2) / sr

def runs(mask, t, step, min_len):  # contiguous True runs ≥ min_len s → [(t_start, t_end, i, j)]
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]: j += 1
            if (j - i) * step >= min_len: out.append((t[i], t[j - 1], i, j))
            i = j
        else: i += 1
    return out

def transient_hits(bm):  # → [(t, label)]: audible onsets only (riser / swell peaks have no transient)
    return [(h["t"], h.get("what", "hit")) for h in bm.get("hits", []) if h.get("kind", "transient") == "transient"
            and not any(k in h.get("what", "") for k in ("riser", "swell"))]

def barpos(bm, t):  # "bar:beat" from the beat map (bars, else 4/4 downbeats), "" without one
    bars = bm.get("bars") or [[i + 1, d, 4] for i, d in enumerate(bm.get("downbeats", []))]
    b = [x for x in bars if x[1] <= t + 1e-9]
    return f"{b[-1][0]}:{1 + (t - b[-1][1]) * float(bm['bpm']) / 60:.2f}" if b and "bpm" in bm else ""

def scan(path, bm, t_from, t_to, voice=None, ev=(), grace=0.04):
    X, sr = load(path); x = X.astype(np.float64).mean(1); dur = len(x) / sr
    F = bm.get("fade"); end = t_to if t_to is not None else (F.get("start", F.get("from")) if isinstance(F, dict) else F[0] if isinstance(F, list)
                                                            else F if F else dur - 2.8)
    secs = bm.get("sections") or [{"name": f"{a:.0f}s", "start": a, "end": a + 8} for a in np.arange(0, dur, 8.0)]
    out, fails = [f"audio QA scan · {path} · {dur:.3f} s · {X.shape[1]} ch · checked {t_from:.2f}–{end:.2f} s"], 0
    d5, t5 = rms_db(x, sr, .005, .005); sil = runs(d5 < -60, t5, .005, .02)
    inside = [r for r in sil if r[1] >= t_from and r[0] <= end]; fails += len(inside)
    out.append(f"[1] digital silence (< −60 dBFS, ≥ 20 ms): {len(inside)} inside the span" +
               ("; all runs: " + ", ".join(f"{a:.3f}-{b:.3f}" for a, b, *_ in sil) if sil else ""))
    db, tt = rms_db(x, sr, .1, .05); viol = []
    for s in secs:
        m = (tt >= s["start"]) & (tt < s["end"])
        if m.any():
            med = np.median(db[m]); bad = m & (db < med - 12) & (tt >= t_from) & (tt <= end)
            viol += [(a, b, s["name"], float(db[i:j].min()), med) for a, b, i, j in runs(bad, tt, .05, 0)]
    fails += len(viol)
    out.append(f"[2] dropouts (0.1 s RMS < section median − 12 dB): {len(viol)}")
    out += [f"    {a:7.2f}-{b:7.2f} s  {n}: {d:.1f} dBFS vs median {m:.1f}" for a, b, n, d, m in viol[:40]]
    e, te = rms_db(x, sr, .05, .01); base = median_filter(e, size=61, mode="nearest"); dip = base - e; hits = transient_hits(bm)
    sag = lambda i, j: e[max(0, i - 6):i + 2].max() - e[i:i + 2].min() < 3 and e[j:j + 7].max() - e[j - 1] >= 3   # slow in, hard out
    talk = np.zeros(len(te), bool)
    if voice:
        V, vsr = load(voice); ve, vt = rms_db(V.astype(np.float64).mean(1), vsr, .05, .01)
        talk = maximum_filter1d((np.interp(te, vt, ve, right=-120) > -45).astype(np.uint8), 41) > 0   # speaking, ±0.2 s
    pumps = [(a, b, float(dip[i:j].max())) for a, b, i, j in runs(dip > 4, te, .01, .06)
             if t_from <= a <= end and not any(-.05 <= a - h <= .40 for h, _ in hits) and not sag(i, j) and not talk[i]]
    fails += len(pumps)
    out.append(f"[3] pumping (dip > 4 dB for ≥ 60 ms, not at a transient music hit): {len(pumps)}")
    out += [f"    {a:7.2f}-{b:7.2f} s  depth {d:.1f} dB" for a, b, d in pumps[:40]]
    cand, k, g = {}, int(.005 * sr) // 2, int(.001 * sr)
    for c in range(X.shape[1]):
        d2 = np.abs(np.diff(X[:, c].astype(np.float64), 2)); q = np.concatenate([[0], np.cumsum(d2 ** 2)]); i = np.arange(len(d2))
        box = lambda h: q[np.minimum(len(d2), i + h + 1)] - q[np.maximum(0, i - h)]           # sum of d2² over i ± h
        loc = np.sqrt(np.maximum(box(k) - box(g), 0) / (2 * (k - g)) + 1e-18)                # 5 ms, without the ±1 ms core
        for j in np.nonzero((d2 > 15 * loc) & (d2 > 10 ** (-40 / 20)))[0]: cand[j + 1] = max(cand.get(j + 1, 0), d2[j] / loc[j])
    groups = []                                                            # one per burst (gaps ≤ 10 ms): its worst sample
    for c in sorted(cand):
        if groups and c - groups[-1][1] <= sr * .01: groups[-1][1] = c; groups[-1][2] = max(groups[-1][2], (cand[c], c))
        else: groups.append([c, c, (cand[c], c)])                                             # [first, last, (worst ratio, at)]
    designed = np.array(sorted([h["t"] for h in bm.get("hits", [])] + list(bm.get("beats", [])) + [e["t"] for e in ev]))
    near = lambda t: len(designed) and np.min(np.abs(designed - t)) <= grace
    clicks = sorted(((r, c / sr) for _, _, (r, c) in groups if not near(c / sr)), reverse=True)
    out.append(f"[4] clicks — WARNING, not a failure: {len(clicks)} sharp discontinuities outside ±{grace * 1000:.0f} ms of designed onsets"
               f" ({len(groups) - len(clicks)} more at designed onsets)." + (" 请人耳复听这几处（最严重的前 10 处）：" if clicks else ""))
    out += [f"    {t:8.3f} s  {barpos(bm, t):>9s}  {r:6.0f}× local level" for r, t in clicks[:10]]
    return out, fails

def cues(path, bm, ev, fps):
    import librosa  # provided by `uv run --with librosa`
    X, sr = load(path, 48000); y = X.mean(1)
    on = librosa.onset.onset_detect(y=y, sr=sr, hop_length=128, backtrack=False, units="time", delta=0.04)
    cs = [(t, "music:" + w) for t, w in transient_hits(bm)]
    cs += [(e["t"], "sfx:" + e["sfx"]) for e in ev if e.get("gain_db", 0) - 20 * np.log10(max(1, e.get("dist", 1))) > -18 and e["sfx"] not in SWELLS]
    rows, errs = [], []
    for t, what in sorted(cs):
        d = on - t; near = d[np.argmin(np.abs(d))] if len(d) else 9.0; errs.append(abs(near))
        rows.append(f"{t:8.3f}  {near * 1000:+7.1f} ms  {abs(near) * fps:5.2f} fr  {'OK ' if abs(near) <= 1 / fps else 'OFF'}  {what}")
    errs = np.array(errs); ok = int((errs <= 1 / fps).sum()) if len(errs) else 0
    head = (f"cue check · {path}: {len(errs)} cues, within 1 frame ({1000 / fps:.1f} ms): {ok}" +
            (f", median {np.median(errs) * 1000:.1f} ms, max {errs.max() * 1000:.1f} ms" if len(errs) else ""))
    return [head] + rows, len(errs) - ok

def main():
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    pos = [v for i, v in enumerate(a) if not v.startswith("--") and (i == 0 or not a[i - 1].startswith("--"))]
    mode = pos.pop(0) if pos and pos[0] in ("scan", "cues") else "all"
    if not pos: sys.exit(__doc__)
    mix = pos[0]; bm = json.load(open(pos[1])) if len(pos) > 1 and pos[1] != "-" else {}
    ev = json.load(open(pos[2])) if len(pos) > 2 else []
    out, fails = [], 0
    if mode in ("scan", "all"):
        sev = json.load(open(opt("--events"))) if "--events" in a else ev
        o, f = scan(mix, bm, float(opt("--from", 1.0)), float(opt("--to")) if "--to" in a else None, opt("--voice"), sev,
                    float(opt("--click-grace", 0.04))); out += o; fails += f
    if mode in ("cues", "all") and (bm.get("hits") or ev):
        o, f = cues(mix, bm, ev, float(opt("--fps", 30))); out += o; fails += f
    txt = "\n".join(out)
    if "--out" in a: open(opt("--out"), "w").write(txt + "\n")
    print("\n".join(r for r in out if "  OK  " not in r))   # cue rows that pass are only written to --out
    print(("✓ audio QA passed" if not fails else f"✗ {fails} problem(s)") + (" (click warnings above: 请人耳复听)" if any(r.startswith("[4]") and "请人耳复听" in r for r in out) else "")
          + (f" · full report {opt('--out')}" if "--out" in a else ""))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
