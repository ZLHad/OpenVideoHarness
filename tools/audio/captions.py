"""Captions from a TTS timeline → SRT (zh / en / bilingual) + captions.json for engines.

usage (via bin/vh captions): python tools/audio/captions.py <project_dir> [--lang zh|en] [--zh-max 16] [--en-max 42] [--media-end S]

Reads audio/timeline.<lang>.json (or audio/timeline.json) written by bin/vh tts. Writes into <project>/audio/:
  captions.zh.srt, captions.en.srt (when that side exists), captions.bi.srt (zh line + en line) and
  captions.json: [{"id","start","end","zh":[lines],"en":[lines]}] — engines burn captions in from this file
  (HyperFrames / p5 / Manim read it; every caption stays a pure function of t).
Soft subtitle tracks for players/platforms: bin/vh mux <video> <audio> <out> audio/captions.zh.srt audio/captions.en.srt
Vertical video: pass --zh-max 11 (72 px in the 810 px safe box).
Word timing (timeline from bin/vh tts … --align gemini, or elevenlabs): each captions.json item also gets
  "words": [{"w","start","end"}] (narrated side, absolute seconds) for karaoke / pop-in captions, and
  captions.<lang>.lines.srt splits every caption into one cue per wrapped line, each starting when its first word is
  spoken, so a long line no longer sits on screen as a two-line block for its whole duration.
Minimum duration: a caption shorter than the subtitle floor (readcheck.SUB_FLOOR, 1.8 s; a one-line "Take a square
  wave." is spoken in 1.1 s) has its end moved into the silence after it, never its start: up to 1.8 s, or as far as the
  next caption's start minus 0.1 s, or the end of the media, whichever comes first. The media end is the length of the
  picture, which runs past the last spoken word: --media-end S, else the composition's root data-duration in
  <project>/index.html, else the length of <project>/media/final.mp4 (ffprobe), else the timeline's "duration".
  Every file above carries the extended end (the .lines.srt too: its last line ends with the caption), and captions.json
  keeps the spoken end as "speech_end" on the items it moved. A caption the gap cannot lengthen to 1.8 s is listed on
  stdout (bin/vh readcheck <project> --mode subtitle fails it too). The timeline itself is not touched.
"""
import argparse, json, math, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from readcheck import SUB_FLOOR, composition_duration   # SUB_FLOOR: the one number readcheck's subtitle rule and this tool share

CUE_GAP = 0.1   # seconds left between an extended caption and the next one

def ts(t: float) -> str:
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def wrap_zh(text: str, n: int):
    """Wrap Chinese to <= n full-width units per line. Latin words / paths never split; ASCII counts as half.
    Prefer breaking right after punctuation; otherwise at the last token boundary that fits."""
    text = text.strip()
    toks = re.findall(r"[A-Za-z0-9_./<>:@#%&+=\-]+|\s+|.", text)
    width = lambda t: sum(0.5 if ord(c) < 128 else 1 for c in t)
    if width(text) <= n:
        return [text] if text else []
    lines, cur, cur_w, last_punct = [], [], 0.0, -1
    for tok in toks:
        w = width(tok)
        closing = re.fullmatch(r"[，。！？；、,.!?;：:）)」』”’]", tok) is not None
        if cur and cur_w + w > n and not closing:   # closing punctuation hangs on the line instead of starting one
            cut = last_punct + 1 if last_punct >= len(cur) // 2 else len(cur)
            lines.append(cur[:cut]); cur = cur[cut:]
            cur_w = sum(width(t) for t in cur); last_punct = -1
        cur.append(tok); cur_w += w
        if re.fullmatch(r"[，。！？；、,.!?;：:]", tok):
            last_punct = len(cur) - 1
    if cur:
        lines.append(cur)
    j = lambda l: "".join(l).strip()
    lines = [l for l in lines if j(l)]
    if len(lines) > 1 and width(j(lines[-1])) < 2.5 and len(j(lines[-2])) > 3:   # no one-character orphan line:
        prev, k = lines[-2], len(lines[-2])          # pull whole tokens down, ≈ 2 CJK characters or one Latin word
        while k > 1 and width(j(prev[k:])) < 2:
            k -= 1
        if width(j(prev[:k])) >= 2 and width(j(prev[k:] + lines[-1])) <= n:     # and leave no new orphan behind
            lines[-2:] = [prev[:k], prev[k:] + lines[-1]]
    return [j(l) for l in lines]

def wrap_en(text: str, n: int):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + ([cur] if cur else [])

def srt(items, key_fn):
    blocks, i = [], 1
    for c in items:
        lines = key_fn(c)
        if lines:
            blocks.append(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n" + "\n".join(lines) + "\n"); i += 1
    return "\n".join(blocks)

def _positive(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0 else None

def find_media_end(project, timeline_duration, explicit=None):
    """(seconds, where it came from) for the end of the media, the first of: --media-end, the root data-duration of
    <project>/index.html, the length of <project>/media/final.mp4, the timeline's duration; (None, "") when none is known."""
    if _positive(explicit):
        return float(explicit), "--media-end"
    html = project / "index.html"
    if html.is_file():
        try:
            d = _positive(composition_duration(html))
        except OSError:
            d = None
        if d: return d, "index.html data-duration"
    final = project / "media" / "final.mp4"
    if final.is_file():
        try:
            out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(final)],
                                 capture_output=True, text=True, timeout=60).stdout.strip()
            d = _positive(float(out))
        except (OSError, subprocess.SubprocessError, ValueError):
            d = None
        if d: return d, "media/final.mp4"
    d = _positive(timeline_duration)
    return (d, "timeline duration") if d else (None, "")

def extend_short(items, media_end=None, floor=SUB_FLOOR, gap=CUE_GAP):
    """Give every caption shorter than `floor` seconds the missing time after its end, never before its start:
    up to start + floor, or the next caption's start - `gap`, or `media_end`, whichever is least; a caption is never
    shortened and never made to overlap. An item moved keeps its spoken end as "speech_end". Returns [(item, why)] for
    the captions still under `floor` (why: what stopped them), in time order. items are changed in place."""
    live = sorted((c for c in items if c["zh"] or c["en"]), key=lambda c: c["start"])
    still = []
    for i, c in enumerate(live):
        if c["end"] - c["start"] >= floor - 1e-6:
            continue
        limit, why = math.inf, ""
        if i + 1 < len(live):
            limit, why = live[i + 1]["start"] - gap, f"the next caption starts at {live[i + 1]['start']:g} s"
        if media_end is not None and media_end < limit:
            limit, why = media_end, f"the media ends at {media_end:g} s"
        want = math.ceil((c["start"] + floor) * 1000 - 1e-6) / 1000          # whole milliseconds: the SRT rounds to them
        end = min(want, math.floor(limit * 1000 + 1e-6) / 1000)
        if end > c["end"] + 1e-6:
            c["speech_end"], c["end"] = c["end"], round(end, 3)
        if c["end"] - c["start"] < floor - 1e-6:
            still.append((c, why))
    return still

def line_cues(lines, words, start, end):
    """One cue per wrapped line: a line starts when its first character is spoken (matched by non-space character
    count, scaled when the two texts differ slightly, and interpolated inside a word that spans a line break) and runs
    until the next line starts. Cues never overlap and each lasts ≥ 0.1 s (less only when the caption is that short),
    so several lines inside one coarse ASR word no longer collapse into zero-length cues."""
    key = lambda x: re.sub(r"\s+", "", x)
    ll, wl = [len(key(l)) for l in lines], [len(key(w["w"])) for w in words]
    if len(lines) < 2 or not sum(ll) or not sum(wl):
        return [(start, end, lines)]
    starts, acc = [], 0
    for n in ll:
        pos, c, t = acc * sum(wl) / sum(ll), 0, words[-1]["start"]
        for w, k in zip(words, wl):
            if c + k > pos:
                t = w["start"] + (w["end"] - w["start"]) * (pos - c) / k; break
            c += k
        starts.append(min(max(t, starts[-1] if starts else start), end)); acc += n
    starts[0], gap = start, min(.1, (end - start) / len(lines))
    for i in range(1, len(starts)):                  # push apart lines that start together …
        starts[i] = max(starts[i], starts[i - 1] + gap)
    for i in range(len(starts) - 1, 0, -1):          # … and keep the last ones inside the caption
        starts[i] = min(starts[i], (starts[i + 1] if i + 1 < len(starts) else end) - gap)
    return [(starts[i], starts[i + 1] if i + 1 < len(lines) else end, [lines[i]]) for i in range(len(lines))]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--lang"); ap.add_argument("--zh-max", type=int, default=16)
    ap.add_argument("--en-max", type=int, default=42)
    ap.add_argument("--media-end", type=float, metavar="S", help="the length of the picture in seconds, the limit for lengthening a caption "
                    "(default: index.html's data-duration, else media/final.mp4, else the timeline's duration)")
    a = ap.parse_args()
    if a.media_end is not None and not (math.isfinite(a.media_end) and a.media_end > 0):
        ap.error("--media-end must be > 0 seconds")
    audio = Path(a.project).resolve() / "audio"
    tl_path = audio / f"timeline.{a.lang}.json" if a.lang else audio / "timeline.json"
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    items = [{"id": s["id"], "start": s["start"], "end": s["end"],
              "zh": wrap_zh(s.get("zh", ""), a.zh_max), "en": wrap_en(s.get("en", ""), a.en_max),
              **({"words": s["words"]} if s.get("words") else {})} for s in tl["segments"]]
    end_s, end_from = find_media_end(Path(a.project).resolve(), tl.get("duration"), a.media_end)
    if end_from == "timeline duration" and (Path(a.project) / "media").is_dir() and not (Path(a.project) / "media" / "final.mp4").is_file():
        print("captions: media/final.mp4 is missing, so the media end falls back to the timeline's duration; for a showcase,"
              " tools/fetch_media.sh puts its film there (the videos are in the GitHub release \"media\")", file=sys.stderr)
    n_short = sum(1 for c in items if (c["zh"] or c["en"]) and c["end"] - c["start"] < SUB_FLOOR - 1e-6)
    still = extend_short(items, end_s)
    moved = [c for c in items if "speech_end" in c]
    items = [{k: c[k] for k in ("id", "start", "end", "speech_end", "zh", "en", "words") if k in c} for c in items]   # speech_end beside end
    (audio / "captions.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    wrote = ["captions.json"]
    narr = tl.get("lang") if tl.get("lang") in ("zh", "en") else None
    if narr and not any(c[narr] for c in items):      # a one-language script under the other --lang: that side was spoken
        narr = "en" if narr == "zh" else "zh"
    if narr and any(c.get("words") for c in items) and any(c[narr] for c in items):   # word timing → one cue per wrapped line
        cues = [{"start": t0, "end": t1, "l": ls} for c in items if c[narr]
                for t0, t1, ls in (line_cues(c[narr], c["words"], c["start"], c["end"]) if c.get("words") else [(c["start"], c["end"], c[narr])])]
        (audio / f"captions.{narr}.lines.srt").write_text(srt(cues, lambda c: c["l"]), encoding="utf-8"); wrote.append(f"captions.{narr}.lines.srt")
    if any(c["zh"] for c in items):
        (audio / "captions.zh.srt").write_text(srt(items, lambda c: c["zh"]), encoding="utf-8"); wrote.append("captions.zh.srt")
    if any(c["en"] for c in items):
        (audio / "captions.en.srt").write_text(srt(items, lambda c: c["en"]), encoding="utf-8"); wrote.append("captions.en.srt")
    if any(c["zh"] for c in items) and any(c["en"] for c in items):
        (audio / "captions.bi.srt").write_text(srt(items, lambda c: c["zh"] + c["en"]), encoding="utf-8"); wrote.append("captions.bi.srt")
    print(f"timing from {tl_path.name} ({tl.get('lang', '?')} narration) → audio/" + ", ".join(wrote))
    if n_short:
        print(f"  {n_short} caption(s) under the {SUB_FLOOR:g} s minimum: {len(moved)} extended into the gap after them ("
              + ", ".join(f"{c['id']} +{c['end'] - c['speech_end']:.2f} s" for c in moved) + ")"
              + (f"; media end {end_s:g} s ({end_from})" if end_s else "; media end unknown"))
    for c, why in still:
        print(f"  still {c['end'] - c['start']:.2f} s, under {SUB_FLOOR:g} s: {c['id']} ({c['start']:g}–{c['end']:g} s): {why}")

if __name__ == "__main__":
    main()
