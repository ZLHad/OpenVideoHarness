"""Reading-time check: is every text on screen long enough to be read?

usage: python3 tools/readcheck.py <texts.json | project_dir> [--mode onscreen|subtitle] [--lang zh|en]
                                  [--cjk-cps 4.5] [--latin-cps 15] [--pad 1.5] [--min 2.5]

Input: a JSON list of {text, start, end} in seconds (`t0`/`t1` also accepted; `text` may be a list of lines),
or a dict holding that list under "captions" / "texts" / "items" / "cues". Items without `text` but with `zh` / `en`
(the captions.json that `bin/vh captions` writes) are checked once per language; --lang picks one.
A directory means <dir>/audio/captions.json. `start` must be the moment the text is fully shown and readable
(typing, decode and fly-in finished), `end` the moment it starts to leave.

Two rules, templates/TASTE_CHECKLIST.md #5 (rationale in playbook/03-motion-design.md §2):
  onscreen  (default) titles, labels, number cards that nobody reads aloud: minimum time on screen
            need = max(--min, CJK chars / --cjk-cps + other non-space chars / --latin-cps + --pad)
            defaults 4.5 CJK chars/s, 15 chars/s, pad 1.5 s, floor 2.5 s.
  subtitle  lines that follow the voice: reading-speed ceiling, plus a 1.8 s floor
            CJK text ≤ 9 chars/s (half-width characters count 0.5), Latin text ≤ 20 chars/s (spaces and punctuation count)

The onscreen formula comes from lemo-opuscar's core/render/readcheck.mjs and DIRECTOR.md §7 (MIT, © 2026 LemoLab);
the floor is ours (2.5 s). The subtitle ceilings are the Netflix Timed Text Style Guide figures for adult programmes
(Chinese Simplified 9 cps, English USA 20 cps); the 1.8 s floor is lemo's DIRECTOR.md §7.
lemo's tool renders the page and asks window.TEXTS(t) for boxes; this one only reads timings, so it cannot see
cropping or text that leaves the frame. Check those on the contact sheet.

Exit: 0 all pass · 1 some too short / too fast · 2 nothing to check (bad input). Reads JSON only, writes nothing.
"""
import argparse, json, sys
from pathlib import Path

CJK_RANGES = [(0x3040, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
              (0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F), (0x20000, 0x2FA1F)]   # kana, Han, Hangul
SUB_FLOOR, SUB_CPS_CJK, SUB_CPS_LATIN = 1.8, 9.0, 20.0

def is_cjk(ch: str) -> bool:
    o = ord(ch)
    return any(a <= o <= b for a, b in CJK_RANGES)

def load_items(path: Path):
    if path.is_dir():
        path = path / "audio" / "captions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = next((data[k] for k in ("captions", "texts", "items", "cues") if isinstance(data.get(k), list)), None)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON list of {{text, start, end}}")
    return path, data

def pieces(items, lang):
    """Yield (label, start, end, text) for every text to check."""
    for i, it in enumerate(items):
        t0, t1 = it.get("start", it.get("t0")), it.get("end", it.get("t1"))
        if t0 is None or t1 is None:
            raise ValueError(f"item {i}: needs start/end (or t0/t1)")
        label = str(it.get("id", i + 1))
        if "text" in it:
            fields = [("", it["text"])]
        else:
            keys = [lang] if lang else [k for k in ("zh", "en") if k in it]
            fields = [(k, it.get(k)) for k in keys if it.get(k)]
        for k, txt in fields:
            if isinstance(txt, list):   # wrapped lines: CJK lines join without a space, Latin lines with one
                txt = ("" if any(is_cjk(c) for c in "".join(map(str, txt))) else " ").join(map(str, txt))
            txt = str(txt)
            if txt.strip():
                yield (f"{label}{'·' + k if k else ''}", float(t0), float(t1), txt)

def onscreen_need(text, a):
    cjk = sum(1 for c in text if is_cjk(c))
    other = sum(1 for c in text if not c.isspace() and not is_cjk(c))
    return max(a.min, cjk / a.cjk_cps + other / a.latin_cps + a.pad)

def subtitle_check(text, dur):
    if any(is_cjk(c) for c in text):   # Netflix CJK rule: half-width characters count 0.5
        n, limit = sum(0.5 if ord(c) < 128 else 1.0 for c in text.strip()), SUB_CPS_CJK
    else:
        n, limit = float(len(text.strip())), SUB_CPS_LATIN
    need = max(SUB_FLOOR, n / limit)
    return need, n / dur if dur > 0 else float("inf"), limit

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", type=Path)
    ap.add_argument("--mode", choices=("onscreen", "subtitle"), default="onscreen")
    ap.add_argument("--lang", choices=("zh", "en"))
    ap.add_argument("--cjk-cps", type=float, default=4.5)
    ap.add_argument("--latin-cps", type=float, default=15.0)
    ap.add_argument("--pad", type=float, default=1.5)
    ap.add_argument("--min", type=float, default=2.5)
    a = ap.parse_args()
    if a.cjk_cps <= 0 or a.latin_cps <= 0:
        ap.error("--cjk-cps and --latin-cps must be > 0")
    try:
        path, items = load_items(a.path)
        todo = list(pieces(items, a.lang))
    except (OSError, ValueError) as e:
        print(f"readcheck: NOT CHECKED — {e}", file=sys.stderr); sys.exit(2)
    if not todo:
        print(f"readcheck: NOT CHECKED — no text found in {path}. This is not a pass.", file=sys.stderr); sys.exit(2)

    bad = 0
    for label, t0, t1, text in todo:
        dur = t1 - t0
        if a.mode == "onscreen":
            need = onscreen_need(text, a)
            ok = dur >= need - 1e-6
            detail = f"shown {dur:5.2f}s  need {need:5.2f}s"
        else:
            need, rate, limit = subtitle_check(text, dur)
            ok = dur >= need - 1e-6
            detail = f"shown {dur:5.2f}s  need {need:5.2f}s  ({rate:4.1f}/s, limit {limit:g}/s)"
        bad += not ok
        short = text if len(text) <= 28 else text[:27] + "…"
        print(f"{'OK ' if ok else 'BAD'} {label:<8} {t0:7.2f}–{t1:7.2f}s  {detail}  {json.dumps(short, ensure_ascii=False)}")
    print(f"readcheck ({a.mode}): {len(todo) - bad}/{len(todo)} pass · {path}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
