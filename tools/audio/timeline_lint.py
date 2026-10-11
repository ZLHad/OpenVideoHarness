"""Is a narration timeline sound? The checks every step that reads one relies on (bin/vh timeline).

usage: python3 tools/audio/timeline_lint.py <project | timeline.json> [zh|en]

A timeline is what bin/vh tts writes and bin/vh pace rewrites: audio/timeline.<lang>.json, segments with start and end
and, after alignment, words [{w, start, end}]. Captions, pace, the picture's cues and the sound's cues all read times
off it, so a slip here moves everything after it. Checked, per line:
  order      a line starts no earlier than the one before it ends (50 ms of overlap allowed) and ends after it starts.
             Lines bin/vh tts heard nothing of get 0.1 s each, centred where their neighbours meet, so next to a run of k
             of them (k up to 4) the overlap may be k × 0.05 s; three or more lines with one and the same span are a
             block the take was not split into, said once
  words      word times run forward (start ≤ end; a word may start up to 0.15 s before the one before it, as aligners
             jitter on short words, but no more than that behind the latest start so far), inside the line (50 ms
             either side)
  spelling   the words put together read as the line's text (spaces, punctuation and symbols left out; NFKC): an
             aligner that spelled "Bingo" as 宾果, or dropped or doubled a word, shows here
A line without words is checked for its order only. Exit: 0 sound · 1 a problem (each printed with the line's id, the
first 12 and a count of the rest) · 2 no timeline, or a file that is not one. bin/vh captions and bin/vh pace refuse a timeline with problems unless given --skip-lint; bin/vh tts
prints them after it writes one.
"""
import json, sys, unicodedata
from pathlib import Path

SLACK = 0.05       # seconds a word or line may stray: aligners round to tens of milliseconds
WORD_BACK = 0.15   # a word may start this much before the word before it (a real take had a 90 ms slip on a 0 s word)
PLACED = 0.1       # the span bin/vh tts gives a line it heard nothing of (tts.MIN_SPAN), centred where its neighbours meet
RUN = 4            # the longest run of such lines that is allowed for: more in a row is a take to redo anyway
EPS = 1e-6         # times are written to the millisecond: a limit met to within float rounding is met
SHOWN = 12         # report(): this many problems, then a count of the rest

def _plain(s):
    """the letters of a text: NFKC, no spaces, punctuation or symbols"""
    s = unicodedata.normalize("NFKC", s or "")
    return "".join(ch for ch in s if not ch.isspace() and unicodedata.category(ch)[0] not in "PSZ").lower()

def _text(seg, lang):
    return seg.get("text") or seg.get(lang or "", "") or seg.get("zh") or seg.get("en") or ""

def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def lint(tl, lang=None):
    """[(line id, problem)] for a timeline dict; empty when it is sound"""
    out, prev = [], None
    segs = [s if isinstance(s, dict) else {} for s in tl.get("segments") or []]
    ids = [s.get("id") or f"#{i + 1}" for i, s in enumerate(segs)]
    span = [(s.get("start"), s.get("end")) if _num(s.get("start")) and _num(s.get("end")) else None for s in segs]
    block, i = [False] * len(segs), 0      # three or more lines in a row with one span: a block the take was not split into
    while i < len(segs):
        j = i
        while span[i] and j + 1 < len(segs) and span[j + 1] == span[i]:
            j += 1
        if j - i >= 2:
            block[i:j + 1] = [True] * (j - i + 1)
            out.append((f"{ids[i]}–{ids[j]}", f"{j - i + 1} lines all span {span[i][0]:.3f}–{span[i][1]:.3f} s: the take was not split into"
                                              f" lines (bin/vh tts … --align gemini splits it)"))
        i = j + 1
    placed = [bool(x) and x[1] - x[0] <= PLACED + EPS for x in span]
    def run(k):                            # the run of placed lines k is in, 0 when it is not one
        if not 0 <= k < len(segs) or not placed[k]:
            return 0
        lo, hi = k, k
        while lo > 0 and placed[lo - 1]:
            lo -= 1
        while hi + 1 < len(segs) and placed[hi + 1]:
            hi += 1
        return hi - lo + 1
    for i, s in enumerate(segs):
        sid = ids[i]
        if not s:
            out.append((sid, "not a line (an object with id, text, start, end)")); continue
        if not span[i]:
            out.append((sid, "no start or end")); continue
        a, b = span[i]
        if b < a - EPS:
            out.append((sid, f"ends at {b:.3f} s, before it starts at {a:.3f} s"))
        inside = i and block[i] and block[i - 1] and span[i] == span[i - 1]   # said once for the block
        allow = max(SLACK, PLACED / 2 * min(RUN, max(run(i), run(i - 1))))
        if prev is not None and not inside and a < prev[1] - allow - EPS:
            out.append((sid, f"starts at {a:.3f} s, before {prev[0]} ends at {prev[1]:.3f} s: lines out of order"))
        prev = (sid, b)
        words = [w if isinstance(w, dict) else {} for w in s.get("words") or []]
        if not words:
            continue
        last = None
        for k, w in enumerate(words):
            ws, we = w.get("start"), w.get("end")
            if not (_num(ws) and _num(we)):
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) has no start or end")); break
            if we < ws - EPS:
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) ends at {we:.3f} s, before it starts at {ws:.3f} s"))
            if last is not None and ws < last - WORD_BACK - EPS:
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) starts at {ws:.3f} s, {last - ws:.2f} s before a word that comes earlier in the line ({last:.3f} s): times out of order"))
            if ws < a - SLACK - EPS or we > b + SLACK + EPS:
                out.append((sid, f"word {k + 1} ({w.get('w', '?')!r}) at {ws:.3f}–{we:.3f} s is outside the line ({a:.3f}–{b:.3f} s)"))
            last = ws if last is None else max(last, ws)   # behind the latest start, so jitter cannot add up
        said, written = _plain("".join(str(w.get("w", "")) for w in words)), _plain(_text(s, lang))
        if written and said != written:
            k = next((j for j in range(min(len(said), len(written))) if said[j] != written[j]), min(len(said), len(written)))
            out.append((sid, f"the words read {said[max(0, k - 6):k + 10]!r} where the text has {written[max(0, k - 6):k + 10]!r}"
                             f" (at letter {k + 1}; words {len(said)} letters, text {len(written)})"))
    return out

def find(target, lang=None):
    """the timeline file a project, its audio folder or a path names"""
    p = Path(target)
    if p.is_file():
        return p
    for d in (p / "audio", p):
        for name in ([f"timeline.{lang}.json"] if lang else []) + ["timeline.json", "timeline.zh.json", "timeline.en.json"]:
            if (d / name).is_file():
                return d / name
    return None

def load(f):
    """a timeline dict from a file, or (None, why not)"""
    try:
        tl = json.loads(Path(f).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"not JSON ({e})"
    if not isinstance(tl, dict) or not isinstance(tl.get("segments"), list):
        return None, "not a timeline (no segments list)"
    return tl, None

def report(problems, prefix="  ", shown=SHOWN):
    lines = [f"{prefix}{sid}: {what}" for sid, what in problems[:shown]]
    return "\n".join(lines + ([f"{prefix}… and {len(problems) - shown} more"] if len(problems) > shown else []))

def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__); sys.exit(0)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print(__doc__); sys.exit(2)
    lang = args[1] if len(args) > 1 else None
    f = find(args[0], lang)
    if not f:
        print(f"timeline: no timeline in {args[0]} (audio/timeline.<lang>.json)", file=sys.stderr); sys.exit(2)
    tl, why = load(f)
    if why:
        print(f"timeline: {f}: {why}", file=sys.stderr); sys.exit(2)
    segs = tl["segments"]
    problems = lint(tl, lang or tl.get("lang"))
    with_words = sum(1 for s in segs if s.get("words"))
    print(f"timeline: {f} · {len(segs)} lines ({with_words} with word times) · {tl.get('duration', '?')} s")
    if problems:
        print(report(problems)); print(f"timeline: {len(problems)} problem(s)"); sys.exit(1)
    print("timeline: sound")

if __name__ == "__main__":
    main()
