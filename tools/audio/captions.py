"""Captions from a TTS timeline → SRT (zh / en / bilingual) + captions.json for engines.

usage (via bin/vh captions): python tools/audio/captions.py <project_dir> [--lang zh|en] [--zh-max 16] [--en-max 42]

Reads audio/timeline.<lang>.json (or audio/timeline.json) written by bin/vh tts. Writes into <project>/audio/:
  captions.zh.srt, captions.en.srt (when that side exists), captions.bi.srt (zh line + en line) and
  captions.json: [{"id","start","end","zh":[lines],"en":[lines]}] — engines burn captions in from this file
  (HyperFrames / p5 / Manim read it; every caption stays a pure function of t).
Soft subtitle tracks for players/platforms: bin/vh mux <video> <audio> <out> audio/captions.zh.srt audio/captions.en.srt
Vertical video: pass --zh-max 11 (72 px in the 810 px safe box).
"""
import argparse, json, re
from pathlib import Path

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
            lines.append("".join(cur[:cut]).strip()); cur = cur[cut:]
            cur_w = sum(width(t) for t in cur); last_punct = -1
        cur.append(tok); cur_w += w
        if re.fullmatch(r"[，。！？；、,.!?;：:]", tok):
            last_punct = len(cur) - 1
    if cur:
        lines.append("".join(cur).strip())
    lines = [l for l in lines if l]
    if len(lines) > 1 and width(lines[-1]) < 2.5 and len(lines[-2]) > 3:   # no one-character orphan line
        lines[-1] = lines[-2][-2:] + lines[-1]; lines[-2] = lines[-2][:-2]
    return lines

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--lang"); ap.add_argument("--zh-max", type=int, default=16)
    ap.add_argument("--en-max", type=int, default=42)
    a = ap.parse_args()
    audio = Path(a.project).resolve() / "audio"
    tl_path = audio / f"timeline.{a.lang}.json" if a.lang else audio / "timeline.json"
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    items = [{"id": s["id"], "start": s["start"], "end": s["end"],
              "zh": wrap_zh(s.get("zh", ""), a.zh_max), "en": wrap_en(s.get("en", ""), a.en_max)} for s in tl["segments"]]
    (audio / "captions.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    wrote = ["captions.json"]
    if any(c["zh"] for c in items):
        (audio / "captions.zh.srt").write_text(srt(items, lambda c: c["zh"]), encoding="utf-8"); wrote.append("captions.zh.srt")
    if any(c["en"] for c in items):
        (audio / "captions.en.srt").write_text(srt(items, lambda c: c["en"]), encoding="utf-8"); wrote.append("captions.en.srt")
    if any(c["zh"] for c in items) and any(c["en"] for c in items):
        (audio / "captions.bi.srt").write_text(srt(items, lambda c: c["zh"] + c["en"]), encoding="utf-8"); wrote.append("captions.bi.srt")
    print(f"timing from {tl_path.name} ({tl.get('lang', '?')} narration) → audio/" + ", ".join(wrote))

if __name__ == "__main__":
    main()
