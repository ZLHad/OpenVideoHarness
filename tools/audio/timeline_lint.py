"""Is a narration timeline sound? The checks every step that reads one relies on (bin/vh timeline).

usage: python3 tools/audio/timeline_lint.py <project | timeline.json> [zh|en]

A timeline is what bin/vh tts writes and bin/vh pace rewrites: audio/timeline.<lang>.json, segments with start and end
and, after alignment, words [{w, start, end}]. Captions, pace, the picture's cues and the sound's cues all read times
off it, so a slip here moves everything after it. Checked, per line:
  order      a line starts no earlier than the one before it ends (50 ms of overlap allowed) and ends after it starts
  words      word times run forward (start ≤ end, each word starting no earlier than the last), inside the line
             (50 ms either side)
  spelling   the words put together read as the line's text (spaces, punctuation and symbols left out; NFKC): an
             aligner that spelled "Bingo" as 宾果, or dropped or doubled a word, shows here
A line without words is checked for its order only. Exit: 0 sound · 1 a problem (each printed with the line's id) ·
2 no timeline. bin/vh captions and bin/vh pace refuse a timeline with problems unless given --skip-lint; bin/vh tts
prints them after it writes one.
"""
import json, sys, unicodedata
from pathlib import Path

SLACK = 0.05   # seconds a word or line may stray: aligners round to tens of milliseconds

def _plain(s):
    """the letters of a text: NFKC, no spaces, punctuation or symbols"""
    s = unicodedata.normalize("NFKC", s or "")
    return "".join(ch for ch in s if not ch.isspace() and unicodedata.category(ch)[0] not in "PSZ").lower()

def _text(seg, lang):
    return seg.get("text") or seg.get(lang or "", "") or seg.get("zh") or seg.get("en") or ""

def lint(tl, lang=None):
    """[(line id, problem)] for a timeline dict; empty when it is sound"""
    out, prev = [], None
    for i, s in enumerate(tl.get("segments") or []):
        sid = s.get("id") or f"#{i + 1}"
        a, b = s.get("start"), s.get("end")
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            out.append((sid, "no start or end")); continue
        if b < a:
            out.append((sid, f"ends at {b:.3f} s, before it starts at {a:.3f} s"))
        if prev is not None and a < prev[1] - SLACK:
            out.append((sid, f"starts at {a:.3f} s, before {prev[0]} ends at {prev[1]:.3f} s: lines out of order"))
        prev = (sid, b)
        words = s.get("words") or []
        if not words:
            continue
        last = None
        for k, w in enumerate(words):
            ws, we = w.get("start"), w.get("end")
            if not (isinstance(ws, (int, float)) and isinstance(we, (int, float))):
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) has no start or end")); break
            if we < ws - 1e-6:
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) ends at {we:.3f} s, before it starts at {ws:.3f} s"))
            if last is not None and ws < last - 1e-6:
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) starts at {ws:.3f} s, before the word before it ({last:.3f} s): times out of order"))
            if ws < a - SLACK or we > b + SLACK:
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) at {ws:.3f}–{we:.3f} s is outside the line ({a:.3f}–{b:.3f} s)"))
            last = ws
        said, written = _plain("".join(w.get("w", "") for w in words)), _plain(_text(s, lang))
        if written and said != written:
            k = next((j for j in range(min(len(said), len(written))) if said[j] != written[j]), min(len(said), len(written)))
            out.append((sid, f"the words read {said[max(0, k - 6):k + 10]!r} where the text has {written[max(0, k - 6):k + 10]!r}"
                             f" (at letter {k + 1}; words {len(said)} letters, text {len(written)})"))
    return out

def find(target, lang=None):
    """the timeline file a project or path names"""
    p = Path(target)
    if p.is_file():
        return p
    audio = p / "audio"
    for name in ([f"timeline.{lang}.json"] if lang else []) + ["timeline.json", "timeline.zh.json", "timeline.en.json"]:
        if (audio / name).is_file():
            return audio / name
    return None

def report(problems, prefix="  "):
    return "\n".join(f"{prefix}{sid}: {what}" for sid, what in problems)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args or "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__); sys.exit(0 if args else 2)
    lang = args[1] if len(args) > 1 else None
    f = find(args[0], lang)
    if not f:
        print(f"timeline: no timeline in {args[0]} (audio/timeline.<lang>.json)", file=sys.stderr); sys.exit(2)
    tl = json.loads(f.read_text(encoding="utf-8"))
    segs = tl.get("segments") or []
    problems = lint(tl, lang or tl.get("lang"))
    with_words = sum(1 for s in segs if s.get("words"))
    print(f"timeline: {f} · {len(segs)} lines ({with_words} with word times) · {tl.get('duration', '?')} s")
    if problems:
        print(report(problems)); print(f"timeline: {len(problems)} problem(s)"); sys.exit(1)
    print("timeline: sound")

if __name__ == "__main__":
    main()
