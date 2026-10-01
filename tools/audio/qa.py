"""Audio QA on the FINAL mix: scan for silence, dropouts, pumping and clicks; cue-check audible onsets against the grid;
and the mix report: the level hierarchy of a profile mix (bin/vh mix … profile=… stems=DIR) in numbers.

usage (via bin/vh qa):
  python tools/audio/qa.py <mix> [beats.json] [events.json] [--fps 30] [--from 1.0] [--to S] [--voice vo.wav]
                          [--stems DIR] [--lib DIR] [--root DIR] [--click-grace 0.04] [--out report.txt]     all three
  python tools/audio/qa.py scan <mix> [beats.json] [--events events.json] [--stems DIR] [...]                scan only
  python tools/audio/qa.py cues <mix> <beats.json|-> [events.json] [--lib DIR] [--root DIR] [...]             cues only
  python tools/audio/qa.py mix <DIR> [--profile P] [--words w.json] [--beats b.json] [--timeline t.json]
                          [--out report.txt] [--json report.json]                                            mix report only
<mix>: anything ffmpeg decodes (wav, m4a, the muxed mp4). beats.json: music.beats.json (sections, hits, fade) or the
output of beats.py; events.json: the SFX event list. --stems DIR: the folder `bin/vh mix … stems=DIR` wrote (the buses
as heard + meta.json); with it the scan knows the music's own dips, the cue check finds the events' sounds, and the
mix report runs too. Exit status 1 if silence, dropouts, pumping, the cue check (on a lossless file; on an AAC encode
only when the encode as a whole is off) or a hard target of the mix report fail (usable as a gate); clicks, marginal
cues and single cue problems in an AAC encode are only warnings.

scan (checked span: --from, default 1.0 s, to --to, default the beat map's fade start, else the last 2.8 s)
  silence   digital-silence runs: every channel below −60 dBFS, sample by sample, for ≥ 20 ms (exact start–end).
            Inside the span they FAIL: a dramatic "stop" must keep a bed.
  dropouts  0.1 s RMS windows < their section's median − 12 dB (sections from beats.json, else 8 s blocks).
  pumping   50 ms RMS vs a 600 ms rolling median: a dip > 4 dB for ≥ 60 ms that does not start within −0.05…+0.40 s
            of a transient music hit. A music ducker keyed on every SFX shows up here. Not counted: a gradual sag that
            ends in an attack (a sparse bell/pluck decaying before the next strike), with --voice (or the voice stem)
            dips that start while the voiceover is speaking (the designed duck under narration), and with --stems a dip
            the music stem has too (at least as deep, less 1 dB): the score's own dynamics, not the mix's.
  clicks    WARNING only (a machine can't tell a designed sharp attack — a saw note head, a hard-gated glitch — from a
            fault): per channel, |2nd difference| > 15 × its local RMS (5 ms window, the ±1 ms around the sample left
            out, so an isolated click can stand out) and > −40 dBFS, outside ±--click-grace (0.04 s) of a designed onset
            (beat map hits and beats, SFX event times). Lists the total and the 10 worst (time, bar:beat, ratio) to
            listen to by ear.
cues: onsets of the mix (librosa, hop 128 at 48 kHz) vs every transient music hit (riser/swell peaks and kind ≠ transient
  skipped) and every SFX event louder than −18 dB (gain_db − 20·log10(dist); the swells and transitions whose landmark is
  a peak or an end, not an onset, are skipped: whoosh, swish_rev, riser, whip, swoosh_tonal, air, paper, tape).
  OK = nearest onset within 1 frame (1/fps). Each row prints its margin: how far the onset clears the detector's
  threshold (the normalised onset strength over its local mean + 0.04); under 0.02 it is marginal ("OK~", a warning: a
  small level change can lose it). An onset detector barely sees a near-pure tone (tick, ding, toggle: spectral
  flatness < 0.01) starting under music, so when one of those is OFF or marginal, its own sound (from --lib / --root /
  the built-ins, or the stems' meta.json) is cross-correlated with the mix, 250 Hz – 9 kHz (after motioner's sync_check,
  MIT): a match ≥ 0.3 within the tolerance confirms it; ≥ 0.15 exactly on the planned sample (±1 ms) confirms the sync
  but warns that it is faint; otherwise the best match within ±250 ms is printed with the OFF. Neither counts when the
  peak sits within 4 ms of the search window's edge, or when a match better by 0.05 lies further out within ±250 ms: a
  sustained tone moved 60–100 ms still correlates well at the edge nearest to it. The match can only confirm a cue,
  never fail one: a same-pitch note in the score makes its position unreliable. When a cue sits within 1 frame of the
  start, one frame of silence is put in front first (an onset needs a frame to rise from) and that padded start is left
  out of the normalisation. On a lossy file (AAC in an mp4) the tolerance is 1 frame + 12 ms and a single cue problem
  is a warning: the encode smears onsets, so the gate is the lossless mix (run qa on the WAV) and the mp4 confirms the
  mux. The encode as a whole fails when, with 8 or more cues, more than 20 % are off or their median error is over
  15 ms (a mux offset; the detector's own lag is +3…+8 ms).
mix (the level hierarchy, per bin/vh mix's profile table; see playbook/04-audio.md "混音"):
  [1] loudness: the stems' sum and each bus. [2] speech: per narration line (the timeline, else voiced runs) voice,
  music and bed loudness, VMR = voice − music (LU), its 10th percentile over 400 ms, VBR = voice − (music + SFX), the
  1–4 kHz SNR. [3] masking: each word (--words, else the timeline's words, else 0.4 s chunks) by its 1–4 kHz SNR.
  [4] gaps: the music in each pause, re the anchor and re the lines around it (a big rise is breathing). [5] SFX: each
  event's class, its own loudness re the anchor (the class range is judged on this), re the local bed and re a
  speaking voice. [6] depth: width, correlation, a blind decay time and the dry/wet ratio per bus. [7] limiter: where
  the mix sits under the stems' sum.
  Timeline lines past the end of the mix are left out (as the mixer does); a line with no speech in the voice stem
  (≤ −70 LUFS, or 20 LU under the others) is flagged NO VOICE and one with no music under it "no music", and neither
  is judged. A stretch of music alone of 2 s or more, over 3 LU above the narration, warns.
  Hard fails (exit 1): a line under the profile's VMR floor; a hero over its limit re the voice during speech; more
  words under the presence floor than the profile allows (with word times; 0.4 s chunks only warn: they straddle pauses
  and read a few points pessimistic); an SFX class median more than 3 LU outside its range (a low-frequency hit under
  the range counts at its floor, as for a single event: the mixer never raises one); timeline lines in the mix with
  the voice stem silent under all of them. In a full run with --stems, also a cue that passes the cue check only as
  faint while the report calls it BURIED: on sync, but not heard. On an encoded file the report is not repeated.
repetition (with events, in every mode; a WARNING, never a failure): a sound that renders the same 3 or more times in the
  mix, byte for byte or with a waveform correlation over 0.98 within ±5 ms, rendered alone before gain, pan and distance:
  a whoosh pinned to one variant on every cut, a recorded file reused as is. Two different variants of one built-in
  never count (a short tick's variants can correlate that well: that is the family's range, not a copy), nor do signals
  (ding, success, error, toggle, "role": "signal", a sonification layer), which are meant to sound the same each time.
  Each built-in event varies unless it pins "variant"; shape each to its move (dur, pitch|center, dir, bright, tone;
  bin/vh sfx audition).
Known limits: pumping misses long shallow dips (≈ 300 ms at −8 dB fills half the 600 ms median; only the −12 dB dropout
  check catches it); the onset detector normalises to the loudest onset in the file, so one huge onset elsewhere can
  make a weak cue marginal or OFF (the margin column shows it); clicks are judged against local HF content, so a click
  deep inside noise can still pass, and designed attacks off the grace windows (16th-note ostinato heads, a typing
  burst, glitch gating) are listed too.
"""
import json, os, subprocess, sys
import numpy as np
from scipy.ndimage import median_filter, maximum_filter1d

REPEAT_CORR, REPEAT_MIN = 0.98, 3   # a sound rendering this alike (waveform correlation) this many times in a mix is a repetition
LOSSLESS = ("flac", "alac", "wavpack", "tta", "ape", "mlp", "truehd", "shorten")
AAC_MARGIN = 0.012     # s: in the mix lab's 16 AAC mp4s, 284 cues' onsets moved ≤ 5.4 ms from their WAV (marginal ones can flip)
TONAL = 0.01           # spectral flatness under which an SFX counts as a (near-)pure tone
MATCH = 0.3            # normalised cross-correlation that confirms a tone's own sound in the mix
FAINT = 0.15           # … or this much, on the planned sample (±1 ms): on sync, but faint under the music (a warning)
ENC_OFF, ENC_SHIFT, ENC_MIN = 0.2, 0.015, 8   # an encode with ≥ ENC_MIN cues fails when more than ENC_OFF of them are off or their
                                              # median error exceeds ENC_SHIFT s (the detector's own lag is +3…+8 ms)
EDGE = 0.004           # s: a match this close to the edge of its search window is a tone that sits beyond it, not a confirmation
MARGINAL = 0.02        # onset strength over the detector's threshold under which a cue is marginal

def load(path, sr=None):  # → float32 (n, ch), sr — via ffmpeg, so containers and codecs all work
    st = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate,channels",
                                    "-of", "json", path], capture_output=True, text=True, check=True).stdout)["streams"][0]
    sr = sr or int(st["sample_rate"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ar", str(sr), "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, int(st["channels"])), sr

def codec(path):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", path],
                          capture_output=True, text=True).stdout.strip()

def lossy(path):
    c = codec(path); return bool(c) and not c.startswith("pcm_") and c not in LOSSLESS

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

def in_stems(stems, p):  # a path from meta.json: relative to the stems folder (bin/vh mix writes it so), else as written
    if not p or os.path.isabs(p) or not stems: return p
    q = os.path.join(stems, p); return q if os.path.exists(q) else p

def stem(stems, name):  # a stem of `bin/vh mix … stems=DIR`, or None
    p = os.path.join(stems, f"{name}.wav") if stems else None
    return p if p and os.path.exists(p) else None

def scan(path, bm, t_from, t_to, voice=None, ev=(), grace=0.04, music_stem=None):
    X, sr = load(path); x = X.astype(np.float64).mean(1); dur = len(x) / sr
    F = bm.get("fade"); end = t_to if t_to is not None else (F.get("start", F.get("from")) if isinstance(F, dict) else F[0] if isinstance(F, list)
                                                            else F if F else dur - 2.8)
    secs = bm.get("sections") or [{"name": f"{a:.0f}s", "start": a, "end": a + 8} for a in np.arange(0, dur, 8.0)]
    out, fails = [f"audio QA scan · {path} · {dur:.3f} s · {X.shape[1]} ch · checked {t_from:.2f}–{end:.2f} s"], 0
    q = np.diff(np.concatenate([[0], (np.abs(X).max(1) < 1e-3).astype(np.int8), [0]]))    # every channel < −60 dBFS
    sil = [(i / sr, j / sr) for i, j in zip(np.nonzero(q == 1)[0], np.nonzero(q == -1)[0]) if j - i >= .02 * sr]   # exact runs
    inside = [r for r in sil if r[1] >= t_from and r[0] <= end]; fails += len(inside)
    out.append(f"[1] digital silence (< −60 dBFS, ≥ 20 ms): {len(inside)} inside the span" +
               ("; all runs: " + ", ".join(f"{a:.3f}-{b:.3f}" for a, b in sil) if sil else ""))
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
    mdip = None
    if music_stem:   # the music bus as heard: its own dips, on the same 10 ms grid
        Ms, msr = load(music_stem, sr); me, mt = rms_db(Ms.astype(np.float64).mean(1), msr, .05, .01)
        mdip = np.interp(te, mt, median_filter(me, size=61, mode="nearest") - me)
    in_music = lambda i, j: mdip is not None and mdip[max(0, i - 2):j + 2].max() >= dip[i:j].max() - 1.0
    cand = [(a, b, i, j, float(dip[i:j].max())) for a, b, i, j in runs(dip > 4, te, .01, .06)
            if t_from <= a <= end and not any(-.05 <= a - h <= .40 for h, _ in hits) and not sag(i, j) and not talk[i]]
    pumps = [(a, b, d) for a, b, i, j, d in cand if not in_music(i, j)]; score = len(cand) - len(pumps)
    fails += len(pumps)
    out.append(f"[3] pumping (dip > 4 dB for ≥ 60 ms, not at a transient music hit): {len(pumps)}" +
               (f" ({score} more that the music stem has too: the score's own dynamics)" if score else ""))
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

def flatness(x, sr):
    """spectral flatness of a sound's first 300 ms in 250 Hz–9 kHz: ~0.5 for noise, ≪ 0.05 for a (decaying) sine"""
    x = x[:int(0.3 * sr)]
    if not len(x) or not np.abs(x).max(): return 1.0
    P = np.abs(np.fft.rfft(x * np.hanning(len(x)), 1 << 15)) ** 2; f = np.fft.rfftfreq(1 << 15, 1 / sr); P = P[(f >= 250) & (f < 9000)] + 1e-20
    return float(np.exp(np.log(P).mean()) / P.mean())

def locate(yb, needle, start, search, sr):
    """normalised cross-correlation of a band-limited template (its first 300 ms) with the band-limited mix, within
    ±search s of where its first sample should be → (offset s, match 0–1)"""
    from scipy.signal import fftconvolve
    lo = max(0, int(round((start - search) * sr))); hi = min(len(yb), int(round((start + search) * sr)) + len(needle))
    hay = yb[lo:hi]
    if len(hay) <= len(needle) or not np.abs(needle).any(): return None, 0.0
    corr = fftconvolve(hay, needle[::-1], mode="valid")
    c = np.concatenate([[0.0], np.cumsum(hay ** 2)]); energy = c[len(needle):] - c[:-len(needle)]
    score = corr / np.sqrt(np.maximum(energy, 1e-18) * (needle ** 2).sum())
    k = int(np.argmax(score)); return (lo + k) / sr - start, float(score[k])

def cues(path, bm, ev, fps, lib=None, root=None):
    import librosa  # provided by `uv run --with librosa`
    import sfx      # which built-ins swell to their landmark instead of starting on it
    X, sr = load(path, 48000); y = X.mean(1); tol = 1 / fps; enc = lossy(path)
    if enc: tol += AAC_MARGIN
    cs = [(t, "music:" + w, None) for t, w in transient_hits(bm)]
    cs += [(e["t"], "sfx:" + e["sfx"], e) for e in ev if e.get("gain_db", 0) - 20 * np.log10(max(1, e.get("dist", 1))) > -18 and e["sfx"] not in sfx.SWELLS]
    # a cue within 1 frame of the start needs a frame of silence before it to rise from; whole onset hops, so every
    # other frame of the onset strength stays where it was
    pad = int(np.ceil(sr / fps / 128)) * 128 if any(t < 1 / fps for t, _, _ in cs) else 0
    env = librosa.onset.onset_strength(y=np.concatenate([np.zeros(pad, y.dtype), y]) if pad else y, sr=sr, hop_length=128)
    n = len(env); k = np.arange(n); ft = k * 128 / sr - pad / sr
    x = env - env.min()
    if pad:   # the silence → mix step at 0 s is now the loudest onset in the file: normalise to the rest, or it would
              # squeeze every other onset toward the threshold; then onset_detect's own peak picking
        x = x / (x[ft >= 1 / fps].max() + 1e-12)
        fr = librosa.util.peak_pick(x, pre_max=0.03 * sr // 128, post_max=0.00 * sr // 128 + 1, pre_avg=0.10 * sr // 128,
                                    post_avg=0.10 * sr // 128 + 1, wait=0.03 * sr // 128, delta=0.04)
    else:
        x = x / (x.max() + 1e-12)
        fr = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=128, backtrack=False, delta=0.04)
    on = fr * 128 / sr - pad / sr
    # the detector's own test (librosa.util.peak_pick with onset_detect's defaults): a peak must clear the mean of the
    # normalised strength over −100…+100 ms by delta; the margin is how far it clears it
    c = np.concatenate([[0.0], np.cumsum(x)]); pre, post = int(np.ceil(0.10 * sr // 128)), int(np.ceil(0.10 * sr // 128 + 1))
    a_, b_ = np.maximum(0, k - pre), np.minimum(n, k + post); margin = x - ((c[b_] - c[a_]) / (b_ - a_) + 0.04)
    yb, cache, rows, errs, signed, warns, bad, faint, nosound = None, {}, [], [], [], 0, 0, [], 0
    family = lambda e: os.path.splitext(os.path.basename(str(e["sfx"])))[0].rsplit("_", 1)[0]   # tick_2 and tick_7: one sound
    sfx_ev = [e for _, _, e in cs if e is not None]
    for t, what, e in sorted(cs, key=lambda c: c[0]):
        d = on - t; j = int(np.argmin(np.abs(d))) if len(d) else None; near = d[j] if j is not None else 9.0
        mg = float(margin[fr[j]]) if j is not None else None; note = ""
        if abs(near) > tol:   # no onset: how close did the strongest candidate come to the threshold
            w = np.abs(ft - t) <= tol; mg = float(margin[w].max()) if w.any() else None
        ok = abs(near) <= tol; marginal = ok and mg is not None and mg < MARGINAL
        if e is not None and (not ok or marginal):
            # a near-pure tone (tick, ding, toggle) barely moves an onset detector under music: look for its own sound
            tm = template(e, lib, root, cache, sr)
            nosound += tm is None
            if tm is not None and tm[2] < TONAL:
                from scipy.signal import butter, sosfiltfilt
                band = butter(4, [250, 9000], "band", fs=sr, output="sos")
                if yb is None: yb = sosfiltfilt(band, y.astype(np.float64))
                nd = sosfiltfilt(band, np.concatenate([tm[1], np.zeros(int(0.02 * sr))]))[:len(tm[1])]   # the same band
                gap = min([abs(o["t"] - e["t"]) for o in sfx_ev if o is not e and family(o) == family(e) and o["t"] != e["t"]] or [9.0])
                w = min(tol, 0.45 * gap)
                off, sc = locate(yb, nd, tm[0] / sr, w, sr)                            # is it there, within the tolerance?
                off2, sc2 = locate(yb, nd, tm[0] / sr, min(0.25, 0.45 * gap), sr)      # … and where is its best match anyway
                # a sustained tone that sits elsewhere still correlates well at the edge of the window nearest to it: a peak
                # on the edge, or a clearly better match outside the tolerance, confirms nothing
                edge = off is not None and abs(off) >= w - EDGE
                elsewhere = off2 is not None and abs(off2) > w and (off is None or sc2 >= sc + 0.05)
                if off is not None and sc >= MATCH and not edge and not elsewhere:
                    near, ok, marginal, note = off, True, False, f"  (its own sound, match {sc:.2f})"
                elif off is not None and sc >= FAINT and abs(off) <= 0.001 and not elsewhere:   # on sync; heard or not is qa mix's question
                    near, ok, marginal, note = off, True, True, f"  (its own sound on the planned sample, but faint: match {sc:.2f})"
                    faint.append((e["t"], e["sfx"]))
                else:   # where is it then, if anywhere within ±250 ms (motioner's search window)
                    note = f"  (its own sound: best match {sc2:.2f} at {off2 * 1000:+.0f} ms)" if off2 is not None else ""
        errs.append(abs(near)); signed.append(near); bad += (not ok) and not enc; warns += marginal or ((not ok) and enc)
        mtxt = f"{mg:+6.3f}" if mg is not None and not note.startswith(("  (its own sound, match", "  (its own sound on")) else "     –"
        rows.append(f"{t:8.3f}  {near * 1000:+7.1f} ms  {abs(near) * fps:5.2f} fr  {('OK~' if marginal else 'OK ') if ok else 'OFF'}  {mtxt}  {what}{note}")
    errs = np.array(errs); ok = int((errs <= tol).sum()) if len(errs) else 0
    head = (f"cue check · {path}: {len(errs)} cues, within {'1 frame + the AAC margin' if enc else '1 frame'} ({1000 * tol:.1f} ms): {ok}" +
            (f", median {np.median(errs) * 1000:.1f} ms, max {errs.max() * 1000:.1f} ms" if len(errs) else "") +
            (f" · margin = onset strength over the detector's threshold; OK~ = under {MARGINAL} (marginal)" if len(errs) else ""))
    if nosound:
        head += f"\n    {nosound} cue(s) off or marginal could not be matched against their own sound: it was not found (--lib / --root, or the stems' meta.json)"
    if enc and len(errs):
        head += (f"\n    {codec(path)} encode: cue problems here are warnings; the gate is the lossless mix (bin/vh qa mix.wav …)"
                 + (f": {len(errs) - ok} cue(s) off in the encode" if ok < len(errs) else ""))
        med = float(np.median(signed))
        if len(errs) >= ENC_MIN and (len(errs) - ok > ENC_OFF * len(errs) or abs(med) > ENC_SHIFT):   # the whole encode is late or early: the mux
            bad += 1
            head += (f"\n    ✗ the encode as a whole is off ({len(errs) - ok}/{len(errs)} cues off, median error {med * 1000:+.1f} ms): "
                     f"a mux, trim or delay offset? AAC alone moved 3 of 284 cues in the mix lab")
    return [head] + rows, bad, warns, faint

def template(e, lib, root, cache, sr):
    """an event's sound as placed (mono) → (first sample in the mix, samples, spectral flatness), or None if unknown"""
    import mix
    try: i, y = mix.place(e, lib, root, cache)
    except SystemExit: return None
    m = y.mean(1); return i, m[:int(0.3 * sr)], flatness(m, sr)

def alike(a, b, lag=240):
    """how alike two renders are: 1.0 when byte-identical, else the peak normalised waveform correlation within ±lag samples
    (their first second each). Different noise seeds of one sound score near 0: this finds copies, not families."""
    if len(a) == len(b) and np.array_equal(a, b): return 1.0
    from scipy.signal import fftconvolve
    a, b = a[:48000], b[:48000]; den = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    if den <= 0: return 0.0
    c = fftconvolve(a, b[::-1]); z = len(b) - 1
    return float(np.abs(c[max(0, z - lag):z + lag + 1]).max() / den)

def repeats(ev, lib=None, root=None):
    """SFX that render the same REPEAT_MIN or more times, each event rendered alone before gain, pan and distance →
    (report lines, number of such groups). Two renders are the same when byte-identical, or alike > REPEAT_CORR unless
    they are two different variants of one built-in (a 20 ms tick a few cents from another correlates that well: that is
    the family's own range, not a copy). Signals are meant to repeat and are left out."""
    import hashlib, sfx
    items, cache = [], {}
    for e in sfx.numbered(ev):
        if e.get("sfx") in sfx.FIXED or e.get("role") == "signal" or e.get("layer") == "sonification": continue
        try: x, _, v, _ = sfx.event_sound(e, None, lib, root, cache)
        except SystemExit: continue      # a sound that cannot be found: the cue check and the mixer say so
        x = np.asarray(x, np.float64); items.append((float(e["t"]), str(e["sfx"]), v, x, hashlib.sha1(x.tobytes()).hexdigest()))
    up = list(range(len(items)))
    def top(k):
        while up[k] != k: up[k] = up[up[k]]; k = up[k]
        return k
    first = {}
    for k, it in enumerate(items):   # byte-identical: one group per render
        if it[4] in first: up[top(k)] = top(first[it[4]])
        else: first[it[4]] = k
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            A, B = items[a], items[b]
            if top(a) == top(b) or (A[2] is not None and B[2] is not None and A[1] == B[1] and A[2] != B[2]): continue
            if not .8 <= len(A[3]) / max(len(B[3]), 1) <= 1.25: continue
            if alike(A[3], B[3]) > REPEAT_CORR: up[top(b)] = top(a)
    groups = {}
    for k in range(len(items)): groups.setdefault(top(k), []).append(k)
    rows = []
    for ks in sorted((g for g in groups.values() if len(g) >= REPEAT_MIN), key=lambda g: items[g[0]][0]):
        names = sorted({items[k][1] for k in ks}); vs = {items[k][2] for k in ks}
        how = "byte-identical" if len({items[k][4] for k in ks}) == 1 else "correlation > 0.98"
        what = names[0] if len(names) == 1 else " / ".join(names)
        ts = [f"{items[k][0]:.2f}" for k in ks]
        rows.append(f"    {what}: {len(ks)} events sound the same ({how}" + (f", variant {vs.pop()}" if len(vs) == 1 and None not in vs else "")
                    + ") at " + ", ".join(ts[:12]) + (f" … ({len(ts) - 12} more)" if len(ts) > 12 else "") + " s")
        built = [n for n in names if n in sfx.LIB]
        takes = ", ".join(sfx.SPEC[built[0]]["takes"]).replace("pitch, center", "pitch|center") if built else ""
        if built:
            rows.append("      → a built-in pinned to one variant (\"variant\": 0 is the plain sound): drop the pins or give each its own"
                        + (f", and shape each to its move ({takes})" if takes else "") + f"; bin/vh sfx audition {built[0]}")
        else: rows.append("      → a recorded sound repeats as it is: more takes, or a built-in, which varies per event")
    n = len(rows) // 2
    head = (f"SFX repetition — WARNING, not a failure: {n} sound(s) render the same {REPEAT_MIN}+ times in this mix (the ear hears the copy)"
            if n else f"SFX repetition: no sound renders the same {REPEAT_MIN}+ times")
    return [head] + rows, n

# ═════════════════════════════ qa mix: the level hierarchy (the mix report) ═════════════════════════════
def targets(name):
    """the checks of a profile, from bin/vh mix's table"""
    import mix
    P = mix.profile(name); vmr = P["music"]["vmr"] or (None, 8.0, 16.0); ck = P["check"]
    return {"vmr": (vmr[1], vmr[2]), "vmr_floor": ck["vmr_fail"], "snr": ck["snr"], "risk": ck["risk"], "gap_rise": ck["gap_rise"],
            "hero_under_voice": P["sfx"]["hero_under_voice"], "buried": ck["buried"], "sfx": P["sfx"]["classes"]}

def width(x):
    """side/mid energy (dB) and L/R correlation: overall, < 250 Hz, 250 Hz–4 kHz, > 4 kHz"""
    import mix
    from scipy.signal import butter, sosfilt
    SR = mix.SR; x = mix.as_stereo(x)
    def one(y):
        m, s = (y[:, 0] + y[:, 1]) / 2, (y[:, 0] - y[:, 1]) / 2; em, es = (m ** 2).sum(), (s ** 2).sum()
        den = np.sqrt((y[:, 0] ** 2).sum() * (y[:, 1] ** 2).sum())
        return (float(10 * np.log10(max(es, 1e-15) / em)) if em > 1e-12 else None,
                float((y[:, 0] * y[:, 1]).sum() / den) if den > 1e-12 else None)
    out = {"all": one(x)}
    for name, sos in (("low", butter(4, 250 / (SR / 2), "low", output="sos")), ("mid", butter(4, [250 / (SR / 2), 4000 / (SR / 2)], "band", output="sos")),
                      ("high", butter(4, 4000 / (SR / 2), "high", output="sos"))):
        out[name] = one(sosfilt(sos, x, axis=0))
    return out

def decay_rt(x):
    """blind reverb estimate: free decays (≥ 12 dB, starting ≥ 25 dB over the floor) of the 0.5–4 kHz envelope; RT60
    from each slope between −5 and −20 dB; the fastest decile is the room's floor (a source can stop fast, a room
    cannot). A bus with a sustained bed has no free decays: None. → (rt60 s or None, number of decays)"""
    import mix
    from scipy.signal import butter, sosfilt
    SR = mix.SR; m = mix.as_stereo(x).mean(1)
    if np.abs(m).max() < 1e-6: return None, 0
    y = sosfilt(butter(4, [500 / (SR / 2), 4000 / (SR / 2)], "band", output="sos"), m)
    _, p = mix.frames(y ** 2, 0.02, 0.01); e = 10 * np.log10(p + 1e-14); floor = np.percentile(e, 5); rts, i, n = [], 1, len(e)
    while i < n - 3:
        if e[i] >= e[i - 1] and e[i] >= e[i + 1] and e[i] > floor + 25:
            j = i
            while j + 1 < n and e[j + 1] <= e[j] + 0.5 and j - i < 150: j += 1
            seg = e[i:j + 1] - e[i]; k = (seg <= -5) & (seg >= -20)
            if seg.min() <= -12 and k.sum() >= 3:
                sl = np.polyfit(np.nonzero(k)[0] * 0.01, seg[k], 1)[0]
                if sl < 0: rts.append(-60 / sl)
            i = j + 1
        else: i += 1
    return (float(np.percentile(rts, 10)), len(rts)) if rts else (None, 0)

def centroid(x):
    import mix
    m = mix.as_stereo(x).mean(1)
    if np.abs(m).max() < 1e-6: return None
    nfft, hop = 4096, 2400; pad = np.concatenate([np.zeros(nfft // 2), m, np.zeros(nfft)]); n = 1 + (len(m) - 1) // hop
    f = np.fft.rfftfreq(nfft, 1 / mix.SR); s = np.zeros(len(f)); win = np.hanning(nfft)
    for a in range(0, n, 256):   # in blocks: bounded memory on a long film
        b = min(n, a + 256); s += (np.abs(np.fft.rfft(pad[np.arange(nfft)[None, :] + hop * np.arange(a, b)[:, None]] * win, axis=1)) ** 2).sum(0)
    return float((f * s).sum() / max(s.sum(), 1e-15))

def events_from_lib(events, bus, lib, root, n):
    """render each event alone, fit one gain to the SFX bus (median of 50 ms RMS ratios: fades and the final gain are in
    the bus) → [(event, levels)] with levels in the bus's scale"""
    import mix, sfx
    cache = {}; placed = [(e, *mix.place(e, lib, root, cache)) for e in sfx.numbered(events)]
    tot = np.zeros((n, 2))
    for e, i, y in placed:
        j = min(n, i + len(y))
        if j > i: tot[i:j] += y[:j - i]
    w = 2400; k = n // w; a = np.sqrt((tot[:k * w] ** 2).reshape(k, -1).mean(1)); b = np.sqrt((bus[:k * w] ** 2).reshape(k, -1).mean(1))
    ok = (a > 10 ** (-50 / 20)) & (b > 1e-7); g = float(np.median(b[ok] / a[ok])) if ok.any() else 1.0
    out = []
    for e, i, y in placed:
        if i >= n: continue
        lv = mix.event_levels(y[:n - i] * g); lv["at"] += i / mix.SR; out.append((e, lv))
    return out

def analyse(voice=None, music=None, sfx=None, mixed=None, events=(), timeline=None, words=None, profile="explainer",
            t1=None, event_levels_list=None, meta=None, beats=None):
    """the mix report (ported from the mix lab's mix_report.py) → a dict with fails / warns"""
    import mix
    SR, lufs, frames, integrated, kpow = mix.SR, mix.lufs, mix.frames, mix.integrated, mix.kpow
    P = targets(profile); buses = {k: v for k, v in (("voice", voice), ("music", music), ("sfx", sfx)) if v is not None and np.abs(v).max() > 1e-6}
    if not buses: sys.exit("qa mix: every stem is silent")
    n = max(len(v) for v in buses.values()); n = min(n, int(t1 * SR)) if t1 else n
    buses = {k: mix.fitn(mix.as_stereo(v), n) for k, v in buses.items()}
    zero = np.zeros((n, 2)); V, M, S = (buses.get(k, zero) for k in ("voice", "music", "sfx"))
    kV, kM, kS = (kpow(buses[k]) if k in buses else np.zeros(n) for k in ("voice", "music", "sfx")); kB = kpow(M + S); kmix = kpow(V + M + S)
    R = {"profile": profile, "duration": n / SR, "has_voice": "voice" in buses}
    R["loudness"] = {"sum_I": integrated(kmix), "sum_TP": mix.true_peak(V + M + S),
                     "bus_I": {k: integrated(kpow(v)) for k, v in buses.items()},
                     "bus_share_dB": {k: float(10 * np.log10(max(kpow(v).sum(), 1e-15) / max(kmix.sum(), 1e-15))) for k, v in buses.items()}}
    tm, mV = frames(kV, 0.4, 0.01, n); _, mM = frames(kM, 0.4, 0.01, n); _, mB = frames(kB, 0.4, 0.01, n)
    _, sM = frames(kM, 3.0, 0.1, n)
    pv, pm, ps = (mix.stft_band(x.mean(1), 1000, 4000) for x in (V, M, S)); tf = np.arange(len(pv)) * int(mix.HOP * SR) / SR
    _, fv = frames(kV, 0.1, 0.01, n); vfast = lufs(fv)[:len(tf)]
    voiced = (vfast > np.percentile(vfast, 95) - 25) if "voice" in buses else np.zeros(len(tf), bool)
    at = lambda t: min(n, max(0, int(round(t * SR))))
    lines = []
    if timeline:   # the lines inside the mix, as bin/vh mix takes them (a line past its end is not in it)
        for s in (timeline.get("segments") if isinstance(timeline, dict) else timeline):
            a, b = float(s["start"]), min(float(s["end"]), n / SR)
            if a < n / SR and b > a: lines.append((a, b, s.get("text") or s.get("en") or s.get("zh") or s.get("id", "")))
    elif "voice" in buses:
        on = np.nonzero(voiced)[0]
        if len(on):
            st = on[0]
            for a, b in zip(on[:-1], on[1:]):
                if b - a > 40: lines.append((tf[st], tf[a], "")); st = b
            lines.append((tf[st], tf[on[-1]], ""))
    R["lines"] = []
    for a, b, txt in lines:
        i, j = at(a), at(b); fr = (tf >= a) & (tf <= b) & voiced; Lv = integrated(kV, i, j)
        k = (tm >= a) & (tm <= b); act = k & (lufs(mV) > Lv - 10); vm = (lufs(mV) - lufs(mM))[act]
        R["lines"].append({"start": a, "end": b, "text": txt, "voice": Lv, "music": integrated(kM, i, j, gate=False),
                           "bed": integrated(kB, i, j, gate=False), "vmr_p10": float(np.percentile(vm, 10)) if len(vm) else None,
                           "snr": float(10 * np.log10((pv[fr].sum() + 1e-12) / (pm[fr].sum() + ps[fr].sum() + 1e-12))) if fr.any() else None})
        ln = R["lines"][-1]; nm = ln["music"] <= -70                     # no music under the line: no VMR to judge
        ln.update(vmr=None if nm else ln["voice"] - ln["music"], vbr=ln["voice"] - ln["bed"], vmr_p10=None if nm else ln["vmr_p10"])
    # a line with no speech in the voice stem (≤ −70 LUFS, or 20 LU under the others): the timeline and the voice file
    # disagree there; it says nothing about the balance, so it stays out of the anchor and the VMR checks
    heard = [ln["voice"] for ln in R["lines"] if ln["voice"] > -70]; m0 = float(np.median(heard)) if heard else None
    for ln in R["lines"]: ln["novoice"] = m0 is None or ln["voice"] <= -70 or ln["voice"] < m0 - 20
    R["timeline_lines"] = len(R["lines"]) if timeline else 0
    vl = [ln for ln in R["lines"] if not ln["novoice"]]
    anchor = float(np.median([ln["voice"] for ln in vl])) if vl else integrated(kM) if "music" in buses else None
    R["anchor"], R["anchor_kind"] = anchor, ("voice" if vl else "music")
    anchor_at = None
    lines = [x for x, ln in zip(lines, R["lines"]) if not ln["novoice"]]   # the spoken lines: words, gaps, SFX under speech
    if not vl and anchor is not None:   # no voice: SFX re the music's 3 s level, floored 8 LU under its integrated
        loc_curve = np.maximum(lufs(sM), anchor - 8.0)
        anchor_at = lambda t: float(loc_curve[min(len(loc_curve) - 1, max(0, int(round(t / 0.1))))])
        R["anchor_kind"] = "music (3 s, floor −8)"
    chunks = []
    if words:
        for w in words:
            fr = (tf >= w["start"]) & (tf <= w["end"]) & voiced
            if fr.sum() >= 3: chunks.append((w["start"], w["end"], w["w"], fr))
    else:
        for a, b, txt in lines:
            for c0 in np.arange(a, b, 0.4):
                fr = (tf >= c0) & (tf < min(b, c0 + 0.4)) & voiced
                if fr.sum() >= 5: chunks.append((c0, min(b, c0 + 0.4), f"{txt[:20]}… +{c0 - a:.1f}s" if txt else f"{c0:.1f}s", fr))
    R["words_from"] = "words" if words else "0.4 s chunks"
    R["words"] = [{"start": float(a), "end": float(b), "w": w,
                   "snr": float(10 * np.log10((pv[fr].sum() + 1e-12) / (pm[fr].sum() + ps[fr].sum() + 1e-12))),
                   "snr_music": float(10 * np.log10((pv[fr].sum() + 1e-12) / (pm[fr].sum() + 1e-12))),
                   "snr_sfx": float(10 * np.log10((pv[fr].sum() + 1e-12) / (ps[fr].sum() + 1e-12)))} for a, b, w, fr in chunks]
    R["gaps"] = []
    if lines:
        edges = [(0.0, lines[0][0], None, 0)] + [(lines[k][1], lines[k + 1][0], k, k + 1) for k in range(len(lines) - 1)] + [(lines[-1][1], n / SR, len(lines) - 1, None)]
        for a, b, k0, k1 in edges:
            if b - a < 0.25: continue
            i, j = at(a + 0.1), at(b - 0.05)
            if j <= i: continue
            under = [vl[k]["music"] for k in (k0, k1) if k is not None]
            g = {"start": a, "end": b, "music": integrated(kM, i, j, gate=False)}
            g["re_anchor"] = g["music"] - anchor if anchor is not None else None
            g["rise"] = g["music"] - float(np.mean(under)) if under else None
            g["designed"] = [h for h in (beats or []) if a - 0.05 <= h[0] <= b]
            R["gaps"].append(g)
    # [5] SFX events: their own levels (meta, or rendered from the lib), else a window of the bus up to the next event
    R["events"] = []; LM, LV = lufs(mM), lufs(mV)
    if event_levels_list is None:
        event_levels_list = []
        import sfx as sfxmod
        evs = sorted(sfxmod.numbered(events), key=lambda e: e["t"])
        for q, e in enumerate(evs):
            nxt = evs[q + 1]["t"] if q + 1 < len(evs) else e["t"] + 0.5
            a, b = at(e["t"] - 0.03 - sfxmod.landmark_of(e)), at(min(e["t"] + 0.45, max(e["t"] + 0.06, nxt - 0.02)))
            lv = mix.event_levels(S[a:b]) if b > a + 480 else None
            if lv: lv["at"] += a / SR
            event_levels_list.append((e, lv))
    for e, lv in event_levels_list:
        if lv is None or e["t"] >= n / SR: continue
        c, why = (lv["class"], "mixer") if lv.get("class") else mix.sfx_class(e)
        ti = min(len(tm) - 1, int(round(lv["at"] / 0.01)))
        loud = min(max(lv.get("len10", 0.1), 0.05), 1.0)            # the loud part: within 10 dB of its max
        span = (tf >= lv["at"] - 0.05) & (tf <= lv["at"] + loud)
        fr = span & voiced & ((vfast > anchor - 15) if (anchor is not None and R["anchor_kind"] == "voice") else True); speaking = bool(fr.any())
        km = (tm >= lv["at"] - 0.05) & (tm <= lv["at"] + loud)
        vv = LV[km]; thr = (anchor if anchor is not None else -70) - 20      # the voice's own level while it speaks
        vref = float(vv[vv > thr].max()) if speaking and (vv > thr).any() else None
        speaking = speaking and vref is not None
        loc = anchor_at(lv["at"]) if anchor_at else anchor
        bed = float(LM[ti]) if LM[ti] > -100 else None                   # no music there: no bed to be buried under
        row = {"t": float(e["t"]), "sfx": e.get("sfx"), "class": c, "why": why, **{k: lv.get(k, 0.0) for k in ("fast", "m400", "tp", "len", "lf")},
               "bed": bed, "re_bed": lv["fast"] - bed if bed is not None else None, "re_anchor": lv["fast"] - loc if loc is not None else None,
               "speaking": speaking, "re_voice": (lv["fast"] - vref) if speaking else None}
        if speaking:   # does it cover the words? its 1–4 kHz energy vs the voice's over the loud part
            row["voice_snr"] = float(10 * np.log10((pv[fr].sum() + 1e-12) / (ps[fr].sum() + 1e-12)))
        R["events"].append(row)
    R["depth"] = {}
    for k, v in buses.items():
        wd = width(v); rt, nd = decay_rt(v)
        R["depth"][k] = {"side_mid_dB": wd["all"][0], "corr": wd["all"][1], "corr_low": wd["low"][1], "corr_mid": wd["mid"][1],
                         "corr_high": wd["high"][1], "rt60_est": rt, "decays": nd, "centroid_Hz": centroid(v)}
        if meta and (meta.get("wet_dry_dB") or {}).get(k) is not None: R["depth"][k]["wet_dry_dB"] = meta["wet_dry_dB"][k]
        if meta and k == "music" and meta.get("music_air_dB") is not None: R["depth"][k]["air_dB"] = meta["music_air_dB"]
    if mixed is not None:
        X = mix.fitn(mix.as_stereo(mixed), n); ssum = V + M + S
        _, a = frames((ssum ** 2).sum(1), 0.01, 0.005, n); _, b = frames((X ** 2).sum(1), 0.01, 0.005, n)
        gr = 10 * np.log10((b + 1e-15) / (a + 1e-15)); loud = lufs(a) > -40
        off = float(np.median(gr[loud])) if loud.any() else 0.0; red = np.where(lufs(a) > -60, gr - off, 0)
        R["limiter"] = {"offset_dB": off, "max_reduction_dB": float(max(0.0, -red.min())),
                        "spans": spans([(i * 0.005, -red[i]) for i in np.nonzero(red < -0.5)[0]])}
    verdict(R, P)
    return R

def spans(pts, gap=0.02):
    out = []
    for t, r in pts:
        if out and t - out[-1][1] <= gap: out[-1][1] = t; out[-1][2] = max(out[-1][2], r)
        else: out.append([t, t, r])
    return [(float(a), float(b), float(r)) for a, b, r in out]

def flag(x, lo, hi): return "LOW" if x < lo else "HIGH" if x > hi else "ok"

def verdict(R, P):
    fails, warns = [], []
    nv = [ln for ln in R["lines"] if ln["novoice"]]
    if R.get("timeline_lines") and len(nv) == len(R["lines"]):
        fails.append(f"the timeline has {len(R['lines'])} line(s) in the mix, but the voice stem is silent under all of them: the narration is not in the mix")
    elif nv:
        warns.append("no speech in the voice stem under " + ", ".join(f"{ln['start']:.2f}–{ln['end']:.2f}" for ln in nv) +
                     ": the timeline and the voice file disagree there (left out of the checks)")
    for ln in R["lines"]:
        if ln["novoice"]: ln["flag"] = "NO VOICE"; continue
        if ln["vmr"] is None: ln["flag"] = "no music"; continue
        ln["flag"] = "FAIL" if ln["vmr"] < P["vmr_floor"] else flag(ln["vmr"], *P["vmr"])
        if ln["flag"] == "FAIL": fails.append(f"line {ln['start']:.2f}–{ln['end']:.2f} '{ln['text'][:24]}' VMR {ln['vmr']:.1f} LU < floor {P['vmr_floor']}")
        elif ln["flag"] != "ok": warns.append(f"line {ln['start']:.2f}–{ln['end']:.2f} VMR {ln['vmr']:.1f} LU {ln['flag']} (target {P['vmr'][0]}–{P['vmr'][1]})")
    if R["words"]:
        risky = [w for w in R["words"] if w["snr"] < P["snr"]]; R["risk_share"] = len(risky) / len(R["words"])
        if R["risk_share"] > P["risk"]:   # a hard fail on real words only: 0.4 s chunks straddle pauses and read pessimistic
            (fails if R["words_from"] == "words" else warns).append(
                f"{len(risky)}/{len(R['words'])} {'words' if R['words_from'] == 'words' else '0.4 s chunks (no word times: --words, or bin/vh tts … --align gemini)'} "
                f"under the presence floor {P['snr']} dB (limit {P['risk'] * 100:.0f} %)")
        elif risky: warns.append(f"{len(risky)} word(s) under the presence floor {P['snr']} dB: " + ", ".join(f"'{w['w']}' {w['start']:.2f}s" for w in risky[:6]))
    for g in R["gaps"]:
        if g["re_anchor"] is not None and g["end"] - g["start"] >= 2.0 and g["re_anchor"] > 3.0:   # a long stretch of music alone
            warns.append(f"{g['start']:.2f}–{g['end']:.2f}: music alone at {g['re_anchor']:+.1f} LU over the narration for {g['end'] - g['start']:.1f} s. "
                         "The music has one static gain, set by the music under the lines: if it is much quieter there, this part comes out loud "
                         "(bin/vh mix holds that gain at +6 dB); lower this part in the score")
        if g["rise"] is not None and g["end"] - g["start"] < 1.5 and g["rise"] > P["gap_rise"]:
            why = (" — the score has " + ", ".join(w for _, w in g["designed"][:2]) + " there (a designed swell?)") if g["designed"] else " (breathing: the bed comes up between lines)"
            warns.append(f"gap {g['start']:.2f}–{g['end']:.2f}: music rises {g['rise']:+.1f} LU to {g['re_anchor']:+.1f} re the voice in a {g['end'] - g['start']:.2f} s pause{why}")
    by = {}
    for e in R["events"]:
        lo, hi = P["sfx"].get(e["class"], P["sfx"].get("detail", (-99, 99))); e["flag"] = flag(e["re_anchor"], lo, hi) if e["re_anchor"] is not None else "ok"
        if e["flag"] == "LOW" and e.get("lf", 0) > 0.6: e["flag"] = "ok"   # a low-frequency hit reads loud on K-weighting: only HIGH counts
        if e["re_anchor"] is not None: by.setdefault(e["class"], []).append((e["re_anchor"], e.get("lf", 0) > 0.6 and e["re_anchor"] < lo))
        if e["speaking"] and e["re_voice"] is not None and e["class"] == "hero" and e["re_voice"] > P["hero_under_voice"]:
            e["flag"] = "OVER-VOICE"; fails.append(f"{e['t']:.2f} s {e['sfx']} (hero) {e['re_voice']:+.1f} LU re the voice under speech")
        elif e.get("voice_snr") is not None and e["voice_snr"] < 6 and e["class"] != "hero":
            e["flag"] = "MASKS-VOICE"; warns.append(f"{e['t']:.2f} s {e['sfx']} ({e['class']}) 1–4 kHz within {e['voice_snr']:+.1f} dB of the voice")
        elif e["re_bed"] is not None and e["re_bed"] < P["buried"] and e["class"] != "ambience":
            e["flag"] = "BURIED"; warns.append(f"{e['t']:.2f} s {e['sfx']} ({e['class']}) {e['re_bed']:+.1f} dB under the local bed")
        elif e["flag"] != "ok":
            warns.append(f"{e['t']:.2f} s {e['sfx']} ({e['class']}) {e['re_anchor']:+.1f} LU re anchor {e['flag']} (range {lo}…{hi})")
        if e["class"] == "hero" and e.get("lf", 0) > 0.6 and e["re_anchor"] is not None and e["re_anchor"] < lo + 2:
            warns.append(f"{e['t']:.2f} s {e['sfx']} (hero): {e['lf'] * 100:.0f} % of its energy under 150 Hz — reads weak on phone/laptop speakers; "
                         "add a 1–4 kHz attack layer rather than more gain")
    R["classes"] = {}
    for c, vv in by.items():
        lo, hi = P["sfx"].get(c, P["sfx"].get("detail", (-99, 99))); v = [x for x, _ in vv]; med = float(np.median(v))
        R["classes"][c] = {"n": len(v), "median": med, "min": float(min(v)), "max": float(max(v)), "range": (lo, hi), "lf_low": sum(f for _, f in vv)}
        judged = float(np.median([lo if f else x for x, f in vv]))   # a low-frequency hit under the range counts at its floor:
        if judged < lo - 3 or judged > hi + 3:                       # the mixer never raises one (as the per-event LOW rule)
            fails.append(f"SFX class {c}: median {med:+.1f} LU re anchor, range {lo}…{hi}")
        elif judged != med and med < lo - 3:
            warns.append(f"SFX class {c}: median {med:+.1f} LU re anchor, under {lo}…{hi} because of {R['classes'][c]['lf_low']} low-frequency hit(s), which the mixer never raises")
    meds = {c: d["median"] for c, d in R["classes"].items()}
    tier = {"hero": 0, "signal": 0, "detail": 1, "ambience": 2}   # hero and signal both over detail, detail over ambience;
    broken = [(a, b) for a in meds for b in meds if tier.get(a, 1) < tier.get(b, 1) and meds[a] < meds[b]]   # hero vs signal: either
    R["order_ok"] = not broken
    if broken: warns.append("SFX class order broken (hero, signal ≥ detail ≥ ambience): " + ", ".join(f"{a} {meds[a]:+.1f} < {b} {meds[b]:+.1f}" for a, b in broken))
    d = R["depth"]
    rv, rs = (d.get(k, {}).get("rt60_est") for k in ("voice", "sfx"))
    if rv and rs and rs < rv * 0.9: warns.append(f"depth: SFX decay ({rs:.2f} s) no wetter than the voice ({rv:.2f} s): they sit on the narrator's plane")
    wm, ws = (d.get(k, {}).get("side_mid_dB") for k in ("music", "sfx"))
    if wm is not None and ws is not None and wm < ws: warns.append("depth: music narrower than the SFX bus")
    if "limiter" in R and R["limiter"]["max_reduction_dB"] > 2: warns.append(f"limiter took {R['limiter']['max_reduction_dB']:.1f} dB: peaks too high before it")
    R["fails"], R["warns"] = fails, warns

def fmt(R):
    o = [f"mix report · profile {R['profile']} · {R['duration']:.2f} s · anchor {R['anchor_kind']} {R['anchor']:.1f} LUFS" if R["anchor"] is not None
         else f"mix report · profile {R['profile']} · {R['duration']:.2f} s"]
    L = R["loudness"]
    o.append(f"[1] loudness: sum {L['sum_I']:.1f} LUFS, TP {L['sum_TP']:.1f} dBTP · " +
             ", ".join(f"{k} {v:.1f} LUFS ({L['bus_share_dB'][k]:+.1f} dB)" for k, v in L["bus_I"].items()))
    if R["lines"]:
        o.append("[2] speech line                                     voice  music   bed    VMR  VMRp10  VBR  SNR1-4k flag")
        nz = lambda v: float("nan") if v is None else v
        for ln in R["lines"]:
            o.append(f"    {ln['start']:6.2f}–{ln['end']:6.2f} {ln['text'][:30]:30s} {ln['voice']:6.1f} {ln['music']:6.1f} {ln['bed']:6.1f} {nz(ln['vmr']):6.1f} "
                     f"{nz(ln['vmr_p10']):6.1f} {ln['vbr']:6.1f} {nz(ln['snr']):6.1f}  {ln['flag']}")
        vl = [ln for ln in R["lines"] if not ln["novoice"]]
        v = np.array([ln["vmr"] for ln in vl if ln["vmr"] is not None]); s = np.array([ln["snr"] for ln in vl if ln["snr"] is not None])
        if len(v): o.append(f"    VMR median {np.median(v):.1f} LU, min {v.min():.1f} · presence SNR median {np.median(s) if len(s) else float('nan'):.1f} dB, "
                        f"min {s.min() if len(s) else float('nan'):.1f} · voice lines span {max(ln['voice'] for ln in vl) - min(ln['voice'] for ln in vl):.1f} LU")
    if R["words"]:
        ws = sorted(R["words"], key=lambda w: w["snr"])[:8]
        o.append(f"[3] masking: {len(R['words'])} {'words' if R['words_from'] == 'words' else '0.4 s chunks'}, {R.get('risk_share', 0) * 100:.0f} % under the floor; most at risk (SNR vs bed / music / sfx, dB): " +
                 " · ".join(f"'{w['w']}' {w['start']:.2f}s {w['snr']:+.1f}/{w['snr_music']:+.0f}/{w['snr_sfx']:+.0f}" for w in ws))
    if R["gaps"]:
        o.append("[4] gaps (music re anchor / rise over the music under the lines, LU): " +
                 " · ".join(f"{g['start']:.1f}–{g['end']:.1f} {g['re_anchor']:+.1f}/{(g['rise'] if g['rise'] is not None else float('nan')):+.1f}" for g in R["gaps"]))
    if R["events"]:
        o.append("[5] SFX       t  sfx              class     fast   TP    re-anchor re-bed re-voice flag")
        for e in R["events"]:
            rv = f"{e['re_voice']:+6.1f}" if e["re_voice"] is not None else "     –"
            ra = f"{e['re_anchor']:+6.1f}" if e["re_anchor"] is not None else "     –"
            rb = f"{e['re_bed']:+6.1f}" if e["re_bed"] is not None else "     –"
            o.append(f"    {e['t']:8.3f}  {str(e['sfx'])[-16:]:16s} {e['class']:8s} {e['fast']:6.1f} {e['tp']:6.1f}   {ra}  {rb} {rv}  {e['flag']}")
        o.append("    classes (re anchor, LU): " + (" · ".join(f"{c} n={d['n']} median {d['median']:+.1f} [{d['min']:+.1f}…{d['max']:+.1f}] target {d['range'][0]}…{d['range'][1]}"
                                                         for c, d in R["classes"].items()) + f" · order {'ok' if R['order_ok'] else 'BROKEN'}"
                                                         if R["classes"] else "not judged: no voice and no music to anchor on"))
    o.append("[6] depth    side/mid  corr all/low/mid/high  RT60est(n)  centroid" + ("  wet/dry" if any("wet_dry_dB" in d for d in R["depth"].values()) else ""))
    for k, d in R["depth"].items():
        sm = "mono" if d["side_mid_dB"] is None or d["side_mid_dB"] < -60 else f"{d['side_mid_dB']:6.1f}"
        c = lambda v: "  –" if v is None else f"{v:.2f}"
        o.append(f"    {k:7s} {sm:>7s}   {c(d['corr'])}/{c(d['corr_low'])}/{c(d['corr_mid'])}/{c(d['corr_high'])}   "
                 f"{('%.2f' % d['rt60_est']) if d['rt60_est'] else '  –'}({d['decays']})   {d['centroid_Hz'] or 0:5.0f} Hz" +
                 (f"   dry/wet {d['wet_dry_dB']:+.1f} dB" if "wet_dry_dB" in d else "") + (f"   + air return at dry/wet {d['air_dB']:+.1f} dB" if "air_dB" in d else ""))
    if "limiter" in R:
        lm = R["limiter"]
        o.append(f"[7] limiter: max {lm['max_reduction_dB']:.1f} dB, {len(lm['spans'])} span(s) ≥ 0.5 dB" +
                 (": " + ", ".join(f"{a:.2f}s −{r:.1f}" for a, b, r in lm["spans"][:10]) if lm["spans"] else ""))
    o += [f"FAIL  {x}" for x in R["fails"]] + [f"warn  {x}" for x in R["warns"][:40]]
    o.append("✓ hierarchy targets met" + (f" ({len(R['warns'])} warnings)" if R["warns"] else "") if not R["fails"] else f"✗ {len(R['fails'])} hard target(s) missed")
    return "\n".join(o)

def jsonable(R):
    def conv(v):
        if isinstance(v, dict): return {k: conv(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)): return [conv(x) for x in v]
        if isinstance(v, np.ndarray): return None
        if isinstance(v, (np.floating, float)): return None if not np.isfinite(v) else round(float(v), 3)
        if isinstance(v, np.integer): return int(v)
        if isinstance(v, np.bool_): return bool(v)
        return v
    return conv(R)

def report(a, stems=None):
    """qa mix: read the stems (and meta.json) or explicit buses → (report text, R)"""
    import mix
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    st = stems or opt("--stems"); meta = {}
    if st:
        if not os.path.isdir(st): sys.exit(f"qa mix: no such folder: {st}")
        mp = os.path.join(st, "meta.json"); meta = json.load(open(mp)) if os.path.exists(mp) else {}
    path = lambda k: opt(f"--{k}") or stem(st, k)
    V, M, S = (mix.load(p) if p else None for p in (path("voice"), path("music"), path("sfx")))
    mp = opt("--mix") or (os.path.join(st, meta["mix"]) if st and meta.get("mix") else None)
    mixed = mix.load(mp) if mp and os.path.exists(mp) else None
    ev = json.load(open(opt("--events"))) if opt("--events") else meta.get("events", [])
    tl = json.load(open(opt("--timeline"))) if opt("--timeline") else meta.get("timeline")
    wd = json.load(open(opt("--words"))) if opt("--words") else None
    if wd is None and tl:   # bin/vh tts --align gemini writes each line's words into the timeline
        segs = tl.get("segments") if isinstance(tl, dict) else tl
        wd = [w for s in segs for w in (s.get("words") or []) if {"w", "start", "end"} <= set(w)] or None
    lvl = None
    if meta.get("event_levels") and not opt("--events"): lvl = list(zip(meta["events"], meta["event_levels"]))
    elif ev and S is not None and (opt("--lib") or opt("--root")):
        n = max(len(x) for x in (V, M, S) if x is not None)
        lvl = events_from_lib(ev, mix.fitn(mix.as_stereo(S), n), opt("--lib"), opt("--root"), n)
    beats = None
    if opt("--beats"):
        bm = json.load(open(opt("--beats")))
        beats = [(s["start"], f"section {s.get('name', '')}") for s in bm.get("sections", [])] + [(h["t"], f"hit {h.get('what', '')}") for h in bm.get("hits", [])]
    prof = opt("--profile", meta.get("profile"))
    if not prof: sys.exit("qa mix: which profile? --profile explainer|short|promo|cartoon|mv|swatch (the stems' meta.json names it)")
    if prof not in mix.PROFILES: sys.exit(f"qa mix: unknown profile {prof}: {', '.join(mix.PROFILES)}")
    R = analyse(V, M, S, mixed, ev, tl, wd, prof, float(opt("--t1")) if opt("--t1") else None, lvl, meta, beats)
    if opt("--json"):
        with open(opt("--json"), "w") as fh: json.dump(jsonable(R), fh, ensure_ascii=False, indent=1)
    return fmt(R), R

def main():
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    pos = [v for i, v in enumerate(a) if not v.startswith("--") and (i == 0 or not a[i - 1].startswith("--"))]
    mode = pos.pop(0) if pos and pos[0] in ("scan", "cues", "mix") else "all"
    if mode == "mix":
        if not pos and "--stems" not in a and "--music" not in a and "--voice" not in a: sys.exit(__doc__)
        txt, R = report(a, pos[0] if pos else None)
        st = pos[0] if pos else opt("--stems"); mp = os.path.join(st, "meta.json") if st else None
        meta = json.load(open(mp)) if mp and os.path.exists(mp) else {}
        rev = json.load(open(opt("--events"))) if opt("--events") else meta.get("events", [])
        if rev: txt += "\n" + "\n".join(repeats(rev, opt("--lib", in_stems(st, meta.get("lib"))), opt("--root", in_stems(st, meta.get("root"))))[0])
        if "--out" in a: open(opt("--out"), "w").write(txt + "\n")
        print(txt); sys.exit(1 if R["fails"] else 0)
    if not pos: sys.exit(__doc__)
    import sfx   # numbered: an event re-rendered alone (the cue check's own-sound match) gets the variant it got in the list
    mix_path = pos[0]; bm = json.load(open(pos[1])) if len(pos) > 1 and pos[1] != "-" else {}
    ev = sfx.numbered(json.load(open(pos[2]))) if len(pos) > 2 else []
    stems = opt("--stems"); meta = json.load(open(os.path.join(stems, "meta.json"))) if stems and os.path.exists(os.path.join(stems or "", "meta.json")) else {}
    lib, root = opt("--lib", in_stems(stems, meta.get("lib"))), opt("--root", in_stems(stems, meta.get("root")))
    out, fails, warns, faint = [], 0, 0, []
    sev = json.load(open(opt("--events"))) if "--events" in a else ev
    if mode in ("scan", "all"):
        o, f = scan(mix_path, bm, float(opt("--from", 1.0)), float(opt("--to")) if "--to" in a else None, opt("--voice") or stem(stems, "voice"), sev,
                    float(opt("--click-grace", 0.04)), stem(stems, "music")); out += o; fails += f
    if mode in ("cues", "all") and (bm.get("hits") or ev):
        o, f, w, faint = cues(mix_path, bm, ev, float(opt("--fps", 30)), lib, root); out += o; fails += f; warns += w
    rev, nrep = ev or sev or meta.get("events") or [], 0   # the same sound again and again: a warning
    if rev: o, nrep = repeats(rev, lib, root); out += o
    if mode == "all" and stems and lossy(mix_path):   # the report reads the stems, not this file: it belongs to the lossless run
        out.append("mix report: not repeated on an encoded file; it reads the stems (bin/vh qa <the mix WAV> … --stems)")
    elif mode == "all" and stems:   # the report reads the stems only: --voice / --events above are the scan's raw inputs
        ra = [x for k in ("--words", "--timeline", "--profile") if k in a for x in (k, opt(k))]
        txt, R = report(ra + (["--beats", pos[1]] if len(pos) > 1 and pos[1] != "-" else []), stems); out += txt.splitlines(); fails += len(R["fails"])
        buried = {(e["t"], e["sfx"]) for e in R["events"] if e["flag"] == "BURIED"}
        for t, x in faint:   # on sync but faint in the cue check, and BURIED under the local bed in the report: nobody hears it
            if (float(t), x) in buried:
                out.append(f"FAIL  {t:.3f} s {x}: on the planned sample but faint in the cue check, and BURIED in the mix report: not heard "
                           "(raise its gain_db, or use a sound with more 1–4 kHz)")
                fails += 1
    txt = "\n".join(out)
    if "--out" in a: open(opt("--out"), "w").write(txt + "\n")
    print("\n".join(r for r in out if "  OK  " not in r))   # cue rows that pass cleanly are only written to --out
    print(("✓ audio QA passed" if not fails else f"✗ {fails} problem(s)") + (" (click warnings above: 请人耳复听)" if any(r.startswith("[4]") and "请人耳复听" in r for r in out) else "")
          + (f" ({warns} cue warning(s) above)" if warns else "") + (f" ({nrep} repeated SFX above)" if nrep else "")
          + (f" · full report {opt('--out')}" if "--out" in a else ""))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
