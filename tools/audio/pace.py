"""Bring the pace of the lines in one narration take closer together, without synthesizing again.

usage (via bin/vh pace): python tools/audio/pace.py <project> [zh|en] [--ref ID[-ID] | --target N] [--strength 0.8]
                                                 [--clamp 0.92,1.18] [--tolerance 0.05] [--pause 0.26] [--extra id=s,…]
                                                 [--align map|gemini|whisper] [--dry-run] [--restore]

Optional and gentle: lines in a take are meant to differ in pace, and nothing needs doing when the take sounds fine.
When it audibly runs fast and slow (a one-request take, --join all, often does), this moves each line part of the way
towards one reference pace and keeps the rest of the natural variation (playbook/04-audio.md, "一条 take 里快慢差得明显时").
The numbers are a reference; the ear decides. --dry-run prints them and writes nothing.

Input  audio/voiceover.<lang>.wav + audio/timeline.<lang>.json with word times (bin/vh tts … --align gemini, or minimax);
       audio/script.txt for the blocks (blank lines) and for pause tags. Without word times: --align gemini|whisper
       transcribes the take first. A timeline on a beat grid (--beats) or a dialogue is refused: re-pacing would move
       lines off the grid, and two voices keep their own pace.
Per line:
  1. cut points from the waveform: two lines split at the silence nearest their ASR boundary (within 0.2 s of it, at
     least 0.12 s long when there is one: shorter dips are between syllables). A line's voice is everything voiced
     (within 32 dB of the take's speech level) between the silences on either side, so an ASR start placed late by a
     misheard first syllable, an end placed early, or a boundary inside a syllable cannot cut anything off. A blip under
     0.12 s at a line's edge, set off by 0.06 s of quiet, is a breath: kept in the audio, not counted as speech;
  2. silences inside the line longer than --pause (0.26 s) are shortened to it, 6 ms fades on both sides of each cut.
     A line whose script has <short pause>, <long pause> or a <#s#> mark keeps its pauses (they were asked for);
  3. pace = spoken units / voiced seconds after step 2: CJK characters (digits read out: 75 = 七十五, 3; 1953年 = 5), or
     syllables in English. Reference: the median of the lines (default), --ref the pooled pace of lines a person
     approved (--ref hook, --ref s1-s3), or --target N. Each line moves by tempo (ffmpeg atempo, pitch kept)
     x = (reference / pace) ^ --strength, within --clamp; lines within --tolerance of it, and lines under 4 units or
     0.5 s, are left as they are;
  4. pauses between lines are the take's own, measured voice to voice, kept inside a range by the line's end:
     comma (or no punctuation) 0.12–0.40 s, full stop 0.25–0.70 s, end of a block 0.45–1.20 s; --extra id=s adds
     (or, negative, takes away) after a line. A pause with a "……" line (no words) in it is the pause that line asks for:
     kept as it is. The silence before the first line (--lead) and after the last is kept.
     Lines are joined in numpy, never with anullsrc + concat (playbook/04-audio.md, "旁白晚一点进来").
Output voiceover.<lang>.wav and timeline.<lang>.json written back (timeline.json / voiceover.wav too when they are
       copies of this language), the originals kept as voiceover.<lang>.raw.wav / timeline.<lang>.raw.json, then
       bin/vh captions <project> <lang>. A second run starts again from the .raw take, so settings never compound;
       after a new bin/vh tts run the new take is the original (the timeline's "pace" block records a sha256 of the
       paced file to tell them apart). --restore puts the original back and removes the .raw files, only when the take
       is the one bin/vh pace wrote (otherwise the .raw files may be the only copy of the original: nothing is touched).
       Word times: --align map (default) carries each word through the cuts and the tempo change, which atempo does not
       apply evenly, so the loudness envelopes before and after are aligned and the words follow the audio; offline,
       free, deterministic. A take without word times is transcribed once (--align gemini|whisper) and kept in
       audio/pace.<lang>.asr.json under its sha256. --align gemini transcribes the new take (one call per ≤ 9 min,
       GEMINI_API_KEY; checked before anything is written) and --align whisper with a local mlx-whisper (Apple Silicon;
       WHISPER_MODEL, default mlx-community/whisper-large-v3-turbo); both go
       through tts.py's align_lines like bin/vh tts --align, refresh asr {similarity, flag} and print how far the
       mapped times were (a failed transcription keeps the mapped times, exit 1). A whisper "1953" against a script's
       一九五三 is spread over the heard word.
       The timeline's "pace" block: reference, settings, and per line its pace before, the tempo, and after.
"""
import argparse, hashlib, importlib.util, json, math, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts   # noqa: E402  parse_script, align_lines, transcribe, asr_record: one alignment for the whole harness
try:
    import numpy as np
except ImportError:              # -h on a plain python3; bin/vh pace runs it with numpy
    np = None

HOP = 0.01                        # envelope step (s)
BELOW = 32.0                      # "voice" = within this many dB of the take's speech level (95th percentile of the envelope)
FLOOR_DB = -45.0                  # … and never below this
HEAD, TAIL = 0.03, 0.06           # margins kept around the voiced extent of a line (s)
EDGE_FADE, CUT_FADE = 0.010, 0.006
MIN_UNITS, MIN_VOICED = 4, 0.5    # shorter lines keep their pace: too few units to measure one
SPLIT_NEAR = 0.2                  # look this far around the ASR boundary between two lines for the silence between them
GAP_MIN = 0.12                    # … a silence at least this long when there is one (shorter dips are between syllables)
BREATH, BREATH_GAP = 0.12, 0.06   # a voiced blip this short at a line's edge, set off by this much quiet: a breath, not speech
GAPS = {"comma": (0.12, 0.40), "stop": (0.25, 0.70), "block": (0.45, 1.20)}   # voice-to-voice silence after a line (s)
ASR_PIECE = 540.0                 # longest piece per gemini transcription (16 kHz inline audio: ≈ 10 min fits 20 MB)
STOPS = tuple("。！？!?….")
CLOSERS = " ”’」』）)》\"'"
DIG = "零一二三四五六七八九"
CJK = re.compile(rf"[{tts._CJK}]")
TOKEN = re.compile(rf"[{tts._CJK}]|\d+(?:\.\d+)?%?年?|[A-Za-z]+(?:['’][A-Za-z]+)*")
ASKED_PAUSE = re.compile(r"<\s*(?:short|long)\s+pause\s*>|<#\s*\d", re.I)

# ---------- spoken units ----------

def zh_int(n, head=True):
    """The Chinese reading of an integer (1953 → 一千九百五十三); head: 10–19 read 十… at the start."""
    if n >= 10 ** 8:
        r = n % 10 ** 8
        return zh_int(n // 10 ** 8, head) + "亿" + (("零" if r < 10 ** 7 else "") + zh_int(r, False) if r else "")
    if n >= 10 ** 4:
        r = n % 10 ** 4
        return zh_int(n // 10 ** 4, head) + "万" + (("零" if r < 1000 else "") + zh_int(r, False) if r else "")
    s, z = "", False
    for p, u in ((1000, "千"), (100, "百"), (10, "十"), (1, "")):
        d = n // p % 10
        if d:
            s += ("零" if z else "") + DIG[d] + u; z = False
        elif s:
            z = True
    s = s or "零"
    return s[1:] if head and s.startswith("一十") else s

def en_syllables(w):
    if w.isupper() and len(w) <= 5:                      # an acronym is read letter by letter
        return len(w)
    v = re.findall(r"[aeiouy]+", w.lower())
    n = len(v) - (len(v) > 1 and w.lower().endswith("e") and not w.lower().endswith(("le", "ee", "ie", "ye")))
    return max(1, n)

def units(text, lang):
    """Spoken units of a line: CJK characters, digits as read (zh: 七十五 / 一九五三年; en: ~1.3 per digit), English syllables."""
    n = 0
    for t in TOKEN.findall(text):
        if CJK.fullmatch(t):
            n += 1
        elif t[0].isdigit():
            num, pct, year = t.rstrip("%年"), "%" in t, t.endswith("年")
            whole, _, frac = num.partition(".")
            if lang == "zh" or CJK.search(text):
                k = len(whole) if year and len(whole) == 4 else len(zh_int(int(whole)))
                n += k + (1 + len(frac) if frac else 0) + 3 * pct + year
            else:
                n += max(1, round(1.3 * len(whole.lstrip("0") or "0"))) + (1 + len(frac) if frac else 0) + 2 * pct
        else:
            n += en_syllables(t)
    return n

# ---------- audio in and out (ffmpeg, float32 mono) ----------

def probe(wav):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate,codec_name",
                          "-of", "json", str(wav)], check=True, capture_output=True, text=True).stdout
    st = json.loads(out)["streams"][0]
    return int(st["sample_rate"]), st["codec_name"]

def read_wav(wav, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(sr), "-f", "f32le", "pipe:1"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)

def write_wav(x, sr, codec, dst):
    codec = codec if codec.startswith("pcm_") else "pcm_s16le"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0", "-c:a", codec, "-f", "wav", str(dst)],
                   input=np.clip(x, -1, 1).astype("<f4").tobytes(), check=True, capture_output=True)

def atempo(x, sr, f):
    if abs(f - 1) < 1e-4 or len(x) < 0.05 * sr:          # nothing to stretch, or too little for atempo's windows
        return x.copy()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0", "-af", f"atempo={f:.5f}",
                          "-f", "f32le", "pipe:1"], input=x.astype("<f4").tobytes(), check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)

def warp(kept, y, sr, band=0.15):
    """Where each 10 ms of a line went in its stretched audio. atempo does not stretch a line evenly (pauses and speech by
    different amounts), so the two loudness envelopes are aligned (dynamic time warping in a band of ±band s around the even
    stretch) and the words follow the audio, not the average. → output frame for each input frame (float array)."""
    hop = max(1, round(0.01 * sr))
    env = lambda v: np.maximum(10 * np.log10(np.mean(v[: len(v) // hop * hop].reshape(-1, hop) ** 2, axis=1) + 1e-12), -80.0)
    A, B = env(kept), env(y)
    n, m = len(A), len(B)
    if n < 2 or m < 2:
        return np.arange(n) * (m / max(n, 1))
    w = max(2, int(band / 0.01)); INF = float("inf")
    D = np.full((n, m), INF)
    for i in range(n):
        c = int(round(i * (m - 1) / (n - 1))); lo, hi = max(0, c - w), min(m, c + w + 1)
        cost = np.abs(A[i] - B[lo:hi])
        for j in range(lo, hi):
            best = 0.0 if i == 0 and j == 0 else min(D[i - 1, j] if i else INF, D[i, j - 1] if j else INF, D[i - 1, j - 1] if i and j else INF)
            D[i, j] = cost[j - lo] + best
    i, j, path = n - 1, m - 1, {}
    while i > 0 or j > 0:
        path.setdefault(i, []).append(j)
        steps = [(D[i - 1, j - 1], i - 1, j - 1)] if i and j else []
        steps += [(D[i - 1, j], i - 1, j)] if i else []
        steps += [(D[i, j - 1], i, j - 1)] if j else []
        _, i, j = min(steps)
    path.setdefault(0, []).append(0)
    out = np.array([np.mean(path[k]) for k in range(n)], dtype=float)
    return np.maximum.accumulate(out)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

# ---------- word times from an ASR (gemini or a local whisper), aligned with tts.align_lines ----------

def asr_words(wav, engine, lang, texts, cuts, tmp):
    """→ [{"w","start","end"}] for the whole file. gemini: one call per piece of ≤ ASR_PIECE s, split at line cuts."""
    if engine == "whisper":
        try:
            import mlx_whisper
        except ImportError:
            sys.exit("--align whisper needs mlx-whisper (Apple Silicon; bin/vh pace adds it with --align whisper)")
        r = mlx_whisper.transcribe(str(wav), path_or_hf_repo=os.environ.get("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo"),
                                   word_timestamps=True, language=lang, condition_on_previous_text=False,
                                   initial_prompt="".join(texts)[:120] if lang == "zh" else None)   # simplified characters, the terms
        return [{"w": w["word"].strip(), "start": float(w["start"]), "end": float(w["end"])}
                for sg in r.get("segments", []) for w in sg.get("words", []) if w["word"].strip()]
    dur, pieces, t0, prev = probe_len(wav), [], 0.0, None
    for c in cuts + [None]:                               # close a piece at the last line cut that keeps it under ASR_PIECE
        if prev is not None and prev > t0 and (c if c is not None else dur) - t0 > ASR_PIECE:
            pieces.append((t0, prev)); t0 = prev
        prev = c
    pieces.append((t0, dur))
    words = []
    for a, b in pieces:
        part = tmp / f"asr-{a:.0f}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", f"atrim=start={a:.3f}:end={b:.3f},asetpts=N/SR/TB", str(part)], check=True)
        _, ws = tts.transcribe(part, lang, tmp)
        words += [dict(w, start=w["start"] + a, end=w["end"] + a) for w in ws]
    return words

def align_take(segs, wav, engine, lang, tmp, dur):
    """Transcribe a whole take and place every line on it (start, end, words, asr) like bin/vh tts --align."""
    texts = [s["text"] for s in segs]
    cuts = [(a["end"] + b["start"]) / 2 for a, b in zip(segs, segs[1:]) if "end" in a and "start" in b]
    res = tts.align_lines(texts, asr_words(wav, engine, lang, texts, cuts, tmp), dur)
    return [{"start": round(r["start"], 3), "end": round(r["end"], 3), "words": r["words"],
             "asr": tts.asr_record(r["heard"], r, 0.85)} for r in res]

# ---------- the edit ----------

def gap_kind(seg, nxt, block):
    if nxt is not None and block.get(nxt["id"]) != block.get(seg["id"]):
        return "block"
    return "stop" if seg["text"].rstrip(CLOSERS).endswith(STOPS) else "comma"

def plan(x, sr, segs, lang, block, asked, a):
    """Cut points, inner pauses, pace and tempo of every line with words (nothing written).
    The voice of a line is everything voiced between the silences that part it from its neighbours, each found near the
    ASR boundary between the two; the ASR start and end are not cut points, so an ASR that put them late or early (or a
    line's end and the next one's start at the same instant) cannot cut a syllable off."""
    hop = max(1, round(HOP * sr)); H = hop / sr; n = len(x) // hop
    if n < 2:
        sys.exit("the take is too short to measure")
    db = 10 * np.log10(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-18)
    voiced = db > max(FLOOR_DB, float(np.percentile(db, 95)) - BELOW)
    fr = lambda t: min(max(int(t / H + 1e-6), 0), n)
    dur = len(x) / sr
    U = [units(s["text"], lang) for s in segs]
    spoken = [i for i in range(len(segs)) if U[i]]
    if not spoken:
        sys.exit("no line with words to pace")

    def split(p, q):
        """The silence between lines p and q: the quiet run nearest their ASR boundary, at least GAP_MIN long when there
        is one (shorter dips are between syllables); lines that touch split at the boundary itself."""
        m = (p["end"] + q["start"]) / 2
        k, stop = max(fr(min(p["end"], q["start"]) - SPLIT_NEAR), fr(p["start"])), fr(max(p["end"], q["start"]) + SPLIT_NEAR)
        runs = []
        while k < stop:
            if voiced[k]:
                k += 1; continue
            k0, j = k, k
            while k0 > 0 and not voiced[k0 - 1]:
                k0 -= 1
            while j < n and not voiced[j]:
                j += 1
            runs.append((k0 * H, j * H)); k = j
        near = lambda r: max(r[0] - m, m - r[1], 0.0)
        for floor in (GAP_MIN, 3 * H):
            c = [r for r in runs if r[1] - r[0] >= floor - 1e-9]
            if c:
                return min(c, key=near)
        return (min(max(m, 0.0), dur),) * 2

    sp = [split(segs[i], segs[j]) for i, j in zip(spoken, spoken[1:])]
    lines = []
    for k, i in enumerate(spoken):
        s, u = segs[i], U[i]
        wlo, whi = sp[k - 1][1] if k else 0.0, sp[k][0] if k + 1 < len(spoken) else dur
        mlo, mhi = sum(sp[k - 1]) / 2 if k else 0.0, sum(sp[k]) / 2 if k + 1 < len(spoken) else dur   # margins stop mid-silence
        f0 = fr(wlo); idx = np.flatnonzero(voiced[f0:max(fr(whi), f0)])
        if len(idx):
            v0, v1 = (f0 + idx[0]) * H, min((f0 + idx[-1] + 1) * H, dur)
            c0, c1 = max(mlo, v0 - HEAD, 0.0), min(mhi, v1 + TAIL, dur)
            vr = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)   # voiced runs; the speech is between the breaths at its edges
            while len(vr) > 1 and len(vr[0]) * H < BREATH and (vr[1][0] - vr[0][-1] - 1) * H >= BREATH_GAP:
                vr = vr[1:]
            while len(vr) > 1 and len(vr[-1]) * H < BREATH and (vr[-1][0] - vr[-2][-1] - 1) * H >= BREATH_GAP:
                vr = vr[:-1]
            s0, s1 = (f0 + vr[0][0]) * H, min((f0 + vr[-1][-1] + 1) * H, dur)
        else:                                             # nothing heard for this line: a point, untouched
            v0 = v1 = c0 = c1 = s0 = s1 = min(max(s["start"], wlo), max(whi, wlo), dur)
        sa, sb = int(round(c0 * sr)), min(len(x), int(round(c1 * sr)))
        keep, runs = np.ones(max(sb - sa, 0), bool), []
        q = voiced[fr(s0):fr(s1)] if len(idx) else voiced[:0]   # the speech, first to last voiced frame
        j = 0
        while j < len(q):                                 # quiet runs inside the line (q starts and ends voiced)
            if q[j]:
                j += 1; continue
            e = j
            while e < len(q) and not q[e]:
                e += 1
            if (e - j) * H > a.pause > 0:
                runs.append((s0 + j * H, s0 + e * H))
            j = e
        excess = sum(e - b - a.pause for b, e in runs)
        if runs and not asked.get(s["id"]):               # cut the middle of the long ones (kept when the script asks for them)
            for b, e in runs:
                keep[max(0, int(round((b + a.pause / 2) * sr)) - sa): max(0, int(round((e - a.pause / 2) * sr)) - sa)] = False
        voiced_s = max(s1 - s0 - excess, H)
        lines.append({"i": i, "seg": s, "u": u, "c0": c0, "c1": c1, "v0": v0, "v1": v1, "s0": s0, "s1": s1, "sa": sa, "sb": sb, "keep": keep,
                      "runs": runs, "heard": bool(len(idx)), "rate": u / voiced_s if len(idx) else None, "voiced": voiced_s,
                      "kept_pauses": bool(runs and asked.get(s["id"]))})
    for L in lines:
        L["ok"] = L["heard"] and L["u"] >= MIN_UNITS and L["voiced"] >= MIN_VOICED
    measurable = [L for L in lines if L["ok"]]
    if a.target:
        ref, how = a.target, f"--target {a.target:g}"
    elif a.ref:
        ids = ref_ids(a.ref, segs)
        pool = [L for L in lines if L["seg"]["id"] in ids and L["heard"]]
        if not pool:
            sys.exit(f"--ref {a.ref}: no line there has words that were heard; pick lines with speech")
        ref, how = sum(L["u"] for L in pool) / sum(L["voiced"] for L in pool), f"--ref {a.ref} ({len(pool)} line(s))"
    elif measurable:
        ref, how = float(np.median([L["rate"] for L in measurable])), f"median of {len(measurable)} line(s)"
    else:
        ref, how = None, "no line long enough to measure"
    for L in lines:
        f, why = 1.0, ""
        if not L["ok"]:
            why = "short" if L["heard"] else "nothing heard"
        elif ref and abs(math.log(ref / L["rate"])) > math.log(1 + a.tolerance):
            f = min(a.clamp[1], max(a.clamp[0], (ref / L["rate"]) ** a.strength))
        elif ref:
            why = "close enough"
        L["f"], L["why"] = f, why
    for k, L in enumerate(lines[:-1]):                    # voice-to-voice silence after the line, in the take and in the new one
        nxt = lines[k + 1]
        between = [segs[i]["id"] for i in range(L["i"] + 1, nxt["i"])]   # "……" lines: the pause they stand for is kept
        g = nxt["s0"] - L["s1"]                           # speech to speech: a breath before a line is part of the pause
        kind = "kept" if between else gap_kind(L["seg"], nxt["seg"], block)
        lo_k, hi_k = GAPS.get(kind, (g, g))
        extra = sum(a.extra.get(x_, 0.0) for x_ in [L["seg"]["id"]] + between)
        L["gap"], L["kind"], L["gap0"] = max(0.04, min(max(g, lo_k), hi_k) + extra), kind, g
    return lines, ref, how

def ref_ids(spec, segs):
    ids = [s["id"] for s in segs]
    if spec in ids:
        return {spec}
    for m in re.finditer("-", spec):
        p, q = spec[:m.start()], spec[m.end():]
        if p in ids and q in ids and ids.index(p) <= ids.index(q):
            return set(ids[ids.index(p): ids.index(q) + 1])
    sys.exit(f"--ref {spec}: not a line id or a range of them (first-last) in this timeline: {' '.join(ids)}")

def render(x, sr, lines):
    """→ (new audio, a function: time in the take → time in the new audio); sets each line's real tempo and new span."""
    out = [x[: lines[0]["sa"]]]
    t = len(out[0]) / sr
    for k, L in enumerate(lines):
        chunk, keep = x[L["sa"]:L["sb"]].copy(), L["keep"][: L["sb"] - L["sa"]]
        fz = int(CUT_FADE * sr)
        for e in np.flatnonzero(np.diff(keep.astype(np.int8))):   # fade out before each cut, in after it (length unchanged)
            if keep[e]:
                lo = max(0, e + 1 - fz); chunk[lo:e + 1] *= np.linspace(1, 0, e + 1 - lo)
            else:
                hi = min(len(chunk), e + 1 + fz); chunk[e + 1:hi] *= np.linspace(0, 1, hi - e - 1)
        kept = chunk[keep]
        y = atempo(kept, sr, L["f"])
        fe = min(int(EDGE_FADE * sr), len(y) // 2)
        if fe:
            y[:fe] *= np.linspace(0, 1, fe); y[-fe:] *= np.linspace(1, 0, fe)
        L["ck"], L["scale"] = np.concatenate([[0], np.cumsum(keep)]), len(y) / len(kept) if len(kept) else 1.0
        L["warp"] = warp(kept, y, sr) if len(y) != len(kept) else None
        L["f_real"] = 1 / L["scale"] if L["scale"] else 1.0   # atempo's length is off by up to ~1% (silence stretches unevenly)
        L["n0"] = t; out.append(y); t += len(y) / sr; L["n1"] = t
        if k + 1 < len(lines):                            # the pause: voice-to-voice gap minus the margins already in both chunks
            nxt = lines[k + 1]
            margins = (L["c1"] - L["s1"]) / L["f_real"] + (nxt["s0"] - nxt["c0"]) / nxt["f"]
            pad = np.zeros(int(round(max(0.0, L["gap"] - margins) * sr)))
            out.append(pad); t += len(pad) / sr
    out.append(x[lines[-1]["sb"]:])                       # the take's own tail

    def remap(r):
        """Inside a line: through its cuts and tempo; between lines: linearly across the new pause; lead and tail as they are."""
        prev = None
        for L in lines:
            if r < L["c0"]:
                if prev is None:
                    return min(r, L["n0"])
                w = (r - prev["c1"]) / max(L["c0"] - prev["c1"], 1e-9)
                return prev["n1"] + (L["n0"] - prev["n1"]) * min(max(w, 0.0), 1.0)
            if r < L["c1"]:
                k = min(max(int(round(r * sr)) - L["sa"], 0), len(L["ck"]) - 1)
                if L["warp"] is None or len(L["warp"]) < 2:
                    return L["n0"] + L["ck"][k] * L["scale"] / sr
                hop = max(1, round(0.01 * sr))            # through the aligned envelopes, to the sample within the frame
                return L["n0"] + float(np.interp(L["ck"][k] / hop, np.arange(len(L["warp"])), L["warp"])) * hop / sr
            prev = L
        return prev["n1"] + (r - prev["c1"])
    return np.concatenate(out), remap

def paced_segments(segs, lines, remap):
    """Every line of the timeline on the new take: words through remap, kept inside their own line's new span; the first
    word starts and the last one ends where the speech does (an ASR puts these edges late or early)."""
    by = {L["i"]: L for L in lines}
    out = []
    for i, s0 in enumerate(segs):
        s, L = {k: v for k, v in s0.items() if k != "file"}, by.get(i)   # vo/<lang>/NN.wav are cuts of the original take
        if L and s.get("words"):
            lo, hi = L["n0"], max(L["n1"], L["n0"])
            at = lambda r: round(min(max(remap(r), lo), hi), 3)
            s["words"] = [dict(w, start=at(w["start"]), end=max(at(w["end"]), at(w["start"]))) for w in s["words"]]
            if L["heard"]:
                w0, w1 = s["words"][0], s["words"][-1]
                w0["start"] = min(at(L["s0"]), w0["end"]); w1["end"] = max(at(L["s1"]), w1["start"])
            s["start"], s["end"] = s["words"][0]["start"], s["words"][-1]["end"]
        else:                                             # no words: where its span went
            s["start"] = round(remap(s0["start"]), 3); s["end"] = round(max(remap(s0["end"]), s["start"]), 3)
        out.append(s)
    return out

# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="Bring the pace of the lines in one narration take closer together (see the module doc).")
    ap.add_argument("project"); ap.add_argument("lang", nargs="?", choices=["zh", "en"], help="default: the latest bin/vh tts run's")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--ref", help="line id, or first-last: their pooled pace is the reference (default: the median of the lines)")
    g.add_argument("--target", type=float, help="reference pace in units per second (CJK characters, or English syllables)")
    ap.add_argument("--strength", type=float, default=0.8, help="part of the way: tempo = (reference / pace) ^ strength (0–1)")
    ap.add_argument("--clamp", default="0.92,1.18", help="slowest,fastest tempo of a line")
    ap.add_argument("--tolerance", type=float, default=0.05, help="lines within this fraction of the reference are left as they are")
    ap.add_argument("--pause", type=float, default=0.26, help="longest silence kept inside a line (s); 0 keeps them all")
    ap.add_argument("--extra", default="", help="id=s,… seconds added after a line (negative: taken away)")
    ap.add_argument("--align", default="map", choices=["map", "gemini", "whisper"], help="word times of the new take")
    ap.add_argument("--dry-run", action="store_true", help="measure and print, write nothing")
    ap.add_argument("--restore", action="store_true", help="put the original take and timeline back, remove the .raw files")
    a = ap.parse_intermixed_args()                       # the language may come after the flags too
    if a.restore and a.dry_run:
        ap.error("--restore puts files back; --dry-run only measures: use one of them")
    try:
        a.clamp = tuple(float(v) for v in a.clamp.split(","))
        assert len(a.clamp) == 2 and 0.5 <= a.clamp[0] <= 1 <= a.clamp[1] <= 2
    except (ValueError, AssertionError):
        ap.error("--clamp wants slowest,fastest with 0.5 ≤ slowest ≤ 1 ≤ fastest ≤ 2 (e.g. 0.92,1.18)")
    if not 0 <= a.strength <= 1 or not 0 <= a.tolerance < 1 or a.pause < 0 or (a.target is not None and a.target <= 0):
        ap.error("--strength 0–1, --tolerance 0–1, --pause ≥ 0, --target > 0")
    try:
        a.extra = {k.strip(): float(v) for k, v in (p.split("=", 1) for p in a.extra.split(",") if p.strip())}
    except ValueError:
        ap.error("--extra wants id=seconds,… (e.g. hook=0.3,s4=-0.1)")
    if np is None:
        sys.exit("pace.py needs numpy: run it as bin/vh pace")
    proj = Path(a.project).resolve(); audio = proj / "audio"
    if a.lang is None:
        latest = audio / "timeline.json"
        a.lang = json.loads(latest.read_text(encoding="utf-8")).get("lang") if latest.exists() else None
        a.lang = a.lang or next((l for l in ("zh", "en") if (audio / f"timeline.{l}.json").exists()), "zh")
    wav, tlp = audio / f"voiceover.{a.lang}.wav", audio / f"timeline.{a.lang}.json"
    raw_wav, raw_tl = audio / f"voiceover.{a.lang}.raw.wav", audio / f"timeline.{a.lang}.raw.json"
    latest = audio / "timeline.json"
    copies = latest.exists() and json.loads(latest.read_text(encoding="utf-8")).get("lang") == a.lang   # tts's copies of this run
    rel = lambda p: p.relative_to(proj)

    def captions(old):
        sys.stdout.flush()
        r = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "captions.py"), str(proj), "--lang", a.lang])
        narrow = [c for c in old if len(c.get("zh") or []) > 1 and sum(0.5 if ord(ch) < 128 else 1 for ch in "".join(c["zh"])) <= 16]
        if narrow:                                        # two lines that fit one at the default width: wrapped narrower before
            w = max(sum(0.5 if ord(ch) < 128 else 1 for ch in line) for c in old for line in c.get("zh") or [])
            print(f"  note: the old captions were wrapped narrower (≤ {math.ceil(w)}); bin/vh captions {a.project} {a.lang} {math.ceil(w)} redoes them that way")
        return r.returncode

    old_caps = json.loads((audio / "captions.json").read_text(encoding="utf-8")) if (audio / "captions.json").exists() else []
    if a.restore:
        if not (raw_wav.exists() and raw_tl.exists()):
            sys.exit(f"--restore: no {rel(raw_wav)} / {rel(raw_tl)} to put back")
        cur = json.loads(tlp.read_text(encoding="utf-8")) if tlp.exists() else {}
        if not (wav.exists() and cur.get("pace") and sha256(wav) == cur["pace"].get("sha256")):
            sys.exit(f"--restore: {rel(wav)} is not the take bin/vh pace wrote (a new bin/vh tts run, or a file changed by hand),"
                     f" so nothing was put back. The .raw files may be the only copy of the original take and timeline: keep them"
                     f" until you know which take you want")
        shutil.move(str(raw_wav), str(wav)); shutil.move(str(raw_tl), str(tlp))
        if copies:
            shutil.copyfile(tlp, latest); shutil.copyfile(wav, audio / "voiceover.wav")
        print(f"restored the original take: {rel(wav)}, {rel(tlp)}")
        sys.exit(captions(old_caps))
    if not (wav.exists() and tlp.exists()):
        sys.exit(f"no {rel(wav)} / {rel(tlp)}: make the narration with bin/vh tts first")
    tl = json.loads(tlp.read_text(encoding="utf-8"))
    if tl.get("pace"):                                    # the paced take from an earlier run: start again from the original
        if sha256(wav) != tl["pace"].get("sha256"):
            sys.exit(f"{rel(wav)} changed after bin/vh pace wrote it, but {rel(tlp)} is still the paced one: run bin/vh tts"
                     f" again (it writes both), or put the paced file back")
        if not (raw_wav.exists() and raw_tl.exists()):
            sys.exit(f"{rel(tlp)} is paced, but {rel(raw_wav)} / {rel(raw_tl)} are missing: run bin/vh tts again")
        src_wav, tl = raw_wav, json.loads(raw_tl.read_text(encoding="utf-8"))
    else:
        src_wav = wav                                     # a new take (or the first run): it becomes the original
        if raw_wav.exists() and not a.dry_run:
            print(f"  {rel(wav)} is a new take: it replaces the old {rel(raw_wav)}")
    if tl.get("grid"):
        sys.exit("the lines sit on a beat grid (bin/vh tts --beats): re-pacing would move them off it; change the pace when synthesizing")
    if tl.get("speakers") or any(s.get("speaker") for s in tl["segments"]):
        sys.exit("a dialogue: each voice keeps its own pace, so bin/vh pace leaves it alone")
    segs = tl["segments"]
    if not segs:
        sys.exit(f"{rel(tlp)} has no lines")

    script = audio / "script.txt"
    block, asked = {}, {}
    if script.exists():
        for s in tts.parse_script(script)[0]:
            block[s["id"]] = s["_block"]
            asked[s["id"]] = bool(ASKED_PAUSE.search((s["zh"] if a.lang == "zh" else s["en"]) or s["zh"] or s["en"]))
    unknown = [s["id"] for s in segs if s["id"] not in block]
    if unknown:                                           # the result changes without it: say so
        print(f"  note: {'no ' + str(rel(script)) if not block else str(len(unknown)) + ' line(s) not in ' + str(rel(script))}"
              f" ({', '.join(unknown[:6])}{' …' if len(unknown) > 6 else ''}): no blocks there (a pause after a full stop gets the"
              f" full-stop range) and no pause tags (their pauses are cut like any other)")
    for i in a.extra:
        if i not in {s["id"] for s in segs}:
            sys.exit(f"--extra {i}: no line with that id")

    sr, codec = probe(src_wav)
    x = read_wav(src_wav, sr)
    dur = len(x) / sr
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        missing = [s["id"] for s in segs if units(s["text"], a.lang) and not s.get("words")]
        cache, src_sha = audio / f"pace.{a.lang}.asr.json", sha256(src_wav)
        old = json.loads(cache.read_text(encoding="utf-8")) if missing and cache.exists() else {}
        found = old.get("sha256") == src_sha and len(old.get("segments", [])) == len(segs)
        if missing and not found and a.align == "map":
            sys.exit(f"no word times for {', '.join(missing[:6])}{' …' if len(missing) > 6 else ''}: run bin/vh tts … --align gemini"
                     f" --resume first, or pass --align gemini|whisper here to transcribe the take")
        if (missing and not found) or (a.align != "map" and not a.dry_run):   # before anything is written
            if a.align == "gemini" and not os.environ.get("GEMINI_API_KEY"):
                sys.exit("set GEMINI_API_KEY (Google AI Studio → Get API key) for --align gemini; nothing was written")
            if a.align == "whisper" and importlib.util.find_spec("mlx_whisper") is None:
                sys.exit("--align whisper needs mlx-whisper (Apple Silicon; bin/vh pace adds it with --align whisper); nothing was written")
        if missing:                                       # the take's own word times, transcribed once and kept beside it
            if found:
                got = old["segments"]; print(f"  word times of the take from {rel(cache)} ({old.get('engine')}, transcribed before)")
            else:
                print(f"  {len(missing)} line(s) without word times: transcribing the take ({a.align}) …", flush=True)
                got = align_take(segs, src_wav, a.align, a.lang, tmp, dur)
                if not a.dry_run:
                    cache.write_text(json.dumps({"sha256": src_sha, "engine": a.align, "segments": got}, ensure_ascii=False), encoding="utf-8")
            for s, r in zip(segs, got):
                s.update(r); s.pop("file", None)
            tl["align"] = {"model": old.get("engine") if found else a.align, "by": "bin/vh pace"}
        lines, ref, how = plan(x, sr, segs, a.lang, block, asked, a)
        unit = "chars/s" if a.lang == "zh" else "syll/s"
        y, remap = render(x, sr, lines)
        new = paced_segments(segs, lines, remap)
        print(f"{'line':<8} {'units':>5}  {'pace':>5}   tempo   after   pause after (take → now)")
        by = {L["i"]: L for L in lines}
        for i, s in enumerate(segs):
            L = by.get(i)
            if not L:
                print(f"  {s['id']:<6} {'':5}  (no words: the pause it stands for is kept)"); continue
            r = L["rate"]
            print(f"  {L['seg']['id']:<6} {L['u']:5d}  " + (f"{r:5.2f} → ×{L['f']:.3f} → {r * L['f_real']:5.2f}" if r else f"{'':5}   {'':6}   {'':5}")
                  + (f"   {L['kind']:<5} {L['gap0']:.2f} → {L['gap']:.2f} s" if "gap" in L else "")
                  + (f"   ({L['why']})" if L["why"] else "") + ("   pauses kept (asked for in the script)" if L["kept_pauses"] else "")
                  + (f"   {len(L['runs'])} pause(s) cut to {a.pause:g} s" if L["runs"] and not L["kept_pauses"] else ""))
        m = [L for L in lines if L["ok"]]
        if m:
            before = np.array([L["rate"] for L in m]); after = np.array([L["rate"] * L["f_real"] for L in m])
            print(f"{len(segs)} line(s) · pace {before.min():.2f}–{before.max():.2f} {unit} (sd {before.std():.2f}) → {after.min():.2f}–{after.max():.2f}"
                  f" (sd {after.std():.2f}) · reference {ref:.2f} ({how}) · {dur:.2f} s → {len(y) / sr:.2f} s")
        if a.dry_run:
            print("dry run: nothing written. The numbers are a reference; listen before keeping it.")
            return
        if src_wav == wav:                                # the original files as they are
            shutil.copyfile(wav, raw_wav); shutil.copyfile(tlp, raw_tl)
        part = wav.with_name(wav.name + ".part")
        write_wav(y, sr, codec, part)
        out = {k: v for k, v in tl.items() if k not in ("segments", "duration")}
        out.update(duration=round(probe_len(part), 3), segments=new)
        out["pace"] = {"from": str(rel(raw_wav)), "reference": round(ref, 3) if ref else None, "how": how, "unit": unit,
                       "strength": a.strength, "clamp": list(a.clamp), "tolerance": a.tolerance, "pause": a.pause, "extra": a.extra,
                       "gaps": GAPS, "align": "map", "sha256": sha256(part),   # the engine once its transcription is in
                       "lines": [{"id": L["seg"]["id"], "units": L["u"], "pace": round(L["rate"], 3) if L["rate"] else None,
                                  "tempo": round(L["f"], 4), "after": round(L["rate"] * L["f_real"], 3) if L["rate"] else None,
                                  **({"note": L["why"]} if L["why"] else {})} if L else {"id": s["id"], "units": 0, "note": "no words"}
                                 for s, L in ((s, by.get(i)) for i, s in enumerate(segs))]}
        def save():
            body = json.dumps(out, ensure_ascii=False, indent=2)
            tlp.with_name(tlp.name + ".part").write_text(body, encoding="utf-8"); os.replace(tlp.with_name(tlp.name + ".part"), tlp)
            if part.exists():     # the timeline first: stopped in between, the next run refuses ("changed after bin/vh pace
                os.replace(part, wav)   # wrote it") instead of taking the paced file for a new take and overwriting the original
            if copies:
                latest.write_text(body, encoding="utf-8"); shutil.copyfile(wav, audio / "voiceover.wav")
        save()
        print(f"→ {rel(wav)} ({out['duration']} s) · {rel(tlp)} · the original: {rel(raw_wav)}, {rel(raw_tl)}")
        rc = 0
        if a.align != "map":
            if a.align == "gemini" and not os.environ.get("GEMINI_API_KEY"):
                sys.exit("set GEMINI_API_KEY for --align gemini: the paced take is written with mapped word times")
            try:
                fresh = align_take(new, wav, a.align, a.lang, tmp, out["duration"])
            except Exception as e:                        # quota, network: the mapped word times stay
                print(f"align {a.align} failed: {e}. The paced take keeps the mapped word times; re-run with --align {a.align} later")
                fresh, rc = None, 1
            if fresh:
                d = [abs(s["start"] - r["start"]) for s, r in zip(new, fresh) if s.get("words")] or [0.0]
                for s, r in zip(new, fresh):
                    s.update(r)
                out["align"] = {"model": a.align, "by": "bin/vh pace", "min_sim": 0.85}; out["pace"]["align"] = a.align
                save()
                print(f"align {a.align}: line starts moved by median {np.median(d):.3f} s, max {max(d):.3f} s from the mapped times · similarity "
                      + " ".join(f"{s['id']}={s['asr']['similarity']:.2f}" for s in new))
                for s in (s for s in new if s["asr"].get("flag")):
                    print(f"  FLAG {s['id']}: {s['asr']['flag']} — heard “{s['asr']['text']}”: listen to that line in {rel(wav)}")
    sys.exit(captions(old_caps) or rc)

def probe_len(wav):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                                check=True, capture_output=True, text=True).stdout)

if __name__ == "__main__":
    main()
