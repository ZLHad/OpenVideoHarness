"""Reading-time check: is every text on screen long enough to be read?

usage: python3 tools/readcheck.py <texts.json | project_dir | composition.html> [--mode onscreen|subtitle] [--lang zh|en]
                                  [--cjk-cps 4.5] [--latin-cps 15] [--pad 1.5] [--min 2.5]
       python3 tools/readcheck.py --budget <seconds> [--mode …] [--lang …]    how much text fits in a span
       python3 tools/readcheck.py <composition.html | project_dir> --export [texts.json] [--force]

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

A HyperFrames composition (an .html file) is read without a browser: every element with data-start / data-duration
(or data-end) is a clip, nested data-composition-src files are offset by their host's start, and the text of each
clip becomes one item (split at block elements: two <div>s or an <h1> and a <p> in one scene are two items). The
span is the clip's, so a text that fades in, or that a script shows and hides, is readable for less than that: set
the start by hand for those (--export writes the list to edit). Text in a clip that spans the whole composition has
no timing of its own (the usual "draw(t)" script) and is left out, with a count.

--budget <seconds> answers the question before the text exists: how many characters fit in that span, by the same
rules (on-screen, subtitle), plus the spoken estimate for Chinese narration (4–5 字/s, video-types/02 and 06).

Exit: 0 all pass · 1 some too short / too fast · 2 nothing to check (bad input). Writes nothing, except --export.
"""
import argparse, json, math, re, sys
from html.parser import HTMLParser
from pathlib import Path

CJK_RANGES = [(0x3040, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
              (0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F), (0x20000, 0x2FA1F)]   # kana, Han, Hangul
SUB_FLOOR, SUB_CPS_CJK, SUB_CPS_LATIN = 1.8, 9.0, 20.0

def is_cjk(ch: str) -> bool:
    o = ord(ch)
    return any(a <= o <= b for a, b in CJK_RANGES)

def load_items(path: Path):
    if path.suffix.lower() in (".html", ".htm"):
        return path, export_html(path)
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

# ---------- on-screen text straight from a HyperFrames composition (no browser) ----------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "param"}
SKIP = {"script", "style", "template", "noscript", "title", "head"}
BLOCK = {"div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "section", "article", "header", "footer", "figure",
         "figcaption", "blockquote", "pre", "table", "tr", "td", "th", "svg", "g", "text", "foreignobject", "main", "aside", "nav"}

class _Node:
    __slots__ = ("tag", "attrs", "kids", "parent")
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.kids, self.parent = tag, attrs, [], parent

class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {}, None); self.cur = self.root; self.skip = 0
    def handle_starttag(self, tag, attrs):
        if self.skip:
            if tag in SKIP: self.skip += 1
            return
        if tag in SKIP:
            self.skip = 1; return
        n = _Node(tag, {k: (v or "") for k, v in attrs}, self.cur); self.cur.kids.append(n)
        if tag not in VOID: self.cur = n
    def handle_startendtag(self, tag, attrs):
        if not self.skip and tag not in SKIP:
            self.cur.kids.append(_Node(tag, {k: (v or "") for k, v in attrs}, self.cur))
    def handle_endtag(self, tag):
        if self.skip:
            if tag in SKIP: self.skip -= 1
            return
        n = self.cur
        while n is not self.root and n.tag != tag: n = n.parent   # tolerate unclosed tags
        if n is not self.root: self.cur = n.parent
    def handle_data(self, data):
        if not self.skip and data.strip(): self.cur.kids.append(data)

def _num(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def _text(n, timed):
    """All text under n, leaving out timed descendants (they are items of their own); CJK runs join without spaces."""
    parts = []
    for k in n.kids:
        if isinstance(k, str): parts.append(k)
        elif k.tag == "br": parts.append(" ")
        elif k not in timed: parts.append(_text(k, timed))
    s = re.sub(r"\s+", " ", "".join(parts)).strip()
    return re.sub(r"(?<=[\u3000-\u9fff\uff00-\uffef]) (?=[\u3000-\u9fff\uff00-\uffef])", "", s)

def _blocks(n, timed):
    """n's text as items: a wrapper with one text-bearing block is looked into; two or more blocks (or blocks beside
    loose text) give one item each; inline-only content (spans, a <br>) stays one item."""
    kids = [k for k in n.kids if (k.strip() if isinstance(k, str) else (k not in timed and _text(k, timed)))]
    blocks = [k for k in kids if not isinstance(k, str) and k.tag in BLOCK]
    if not blocks:
        t = _text(n, timed)
        return [(n, t)] if t else []
    loose = " ".join(re.sub(r"\s+", " ", k).strip() if isinstance(k, str) else _text(k, timed) for k in kids if k not in blocks).strip()
    if len(blocks) == 1 and not loose:
        return _blocks(blocks[0], timed)
    out = [(n, loose)] if loose else []
    for b in blocks:
        out += _blocks(b, timed)
    return out

def export_html(path, offset=0.0, until=None, depth=0):
    """[{id, text, start, end, from}] for the timed text in a composition (see the module doc)."""
    path = Path(path)
    tree = _Tree(); tree.feed(path.read_text(encoding="utf-8", errors="replace")); tree.close()
    comp = None; stack = [tree.root]
    while stack and comp is None:   # the composition root: the first data-composition-id
        n = stack.pop(0)
        if not isinstance(n, str):
            if "data-composition-id" in n.attrs and n is not tree.root: comp = n
            else: stack += [k for k in n.kids if not isinstance(k, str)]
    total = _num((comp.attrs if comp else {}).get("data-duration"))
    spans, timed, items, untimed = {}, set(), [], [0]
    def walk(n, t0, t1):
        for k in n.kids:
            if isinstance(k, str): continue
            a, b = t0, t1
            st = _num(k.attrs.get("data-start"))
            if st is not None and k is not comp:
                a = offset + st
                du, en = _num(k.attrs.get("data-duration")), _num(k.attrs.get("data-end"))
                b = a + du if du is not None else (offset + en if en is not None else t1)
                if until is not None and b is not None: b = min(b, until)
                spans[k] = (a, b); timed.add(k)
                src = k.attrs.get("data-composition-src")
                if src and depth < 4 and (path.parent / src).exists():
                    items.extend(export_html(path.parent / src, a, b, depth + 1)); continue
            walk(k, a, b)
    root_end = offset + total if total is not None else until
    walk(tree.root, offset, root_end)
    whole = (root_end - offset) if root_end is not None else None
    for k, (a, b) in spans.items():
        if b is None or b <= a: continue
        full = whole is not None and a - offset <= 0.05 and b - offset >= whole - 0.05
        for node, txt in _blocks(k, timed):
            if full:
                untimed[0] += 1; continue   # no timing of its own: a script decides when it shows
            ident = node.attrs.get("id") or k.attrs.get("id") or f"{node.tag}@{a:g}"
            it = {"id": ident, "text": txt, "start": round(a, 3), "end": round(b, 3), "from": path.name}
            if node is not k:   # the span is the enclosing clip's (a scene), not a timing of the text's own
                it["clip"] = k.attrs.get("id") or k.tag
            items.append(it)
    if depth == 0:
        items.sort(key=lambda x: (x["start"], x["end"], x["id"]))
        export_html.untimed = untimed[0]
    return items
export_html.untimed = 0

def budget(span, a):
    """Lines saying how much text fits in span seconds."""
    rows = [f"readcheck budget for {span:.2f} s"]
    if a.mode in (None, "onscreen"):
        avail = span - a.pad
        if span < a.min - 1e-9 or avail <= 0:
            rows.append(f"  on-screen text (nobody reads it aloud): nothing: {span:.2f} s is under the {a.min:g} s floor")
        else:
            cjk, lat = math.floor(avail * a.cjk_cps + 1e-9), math.floor(avail * a.latin_cps + 1e-9)
            rows.append(f"  on-screen text (nobody reads it aloud): up to {cjk} CJK characters, or {lat} other characters"
                        f"  [({span:.2f} - {a.pad:g} s) x {a.cjk_cps:g} / {a.latin_cps:g} per s; floor {a.min:g} s; mixed: CJK/{a.cjk_cps:g} + other/{a.latin_cps:g} <= {avail:.2f}]")
    if a.mode in (None, "subtitle"):
        if span < SUB_FLOOR - 1e-9:
            rows.append(f"  subtitle (follows the voice):           nothing: {span:.2f} s is under the {SUB_FLOOR:g} s floor")
        else:
            rows.append(f"  subtitle (follows the voice):           up to {math.floor(span * SUB_CPS_CJK + 1e-9)} CJK characters (half-width count 1/2), "
                        f"or {math.floor(span * SUB_CPS_LATIN + 1e-9)} Latin characters with spaces  [x {SUB_CPS_CJK:g} / {SUB_CPS_LATIN:g} per s; floor {SUB_FLOOR:g} s]")
    if a.lang in (None, "zh"):
        rows.append(f"  narration, Chinese (spoken):            about {math.floor(span * 4 + 1e-9)}-{math.floor(span * 5 + 1e-9)} characters"
                    "  [4-5 per s: video-types/02 and 06; measure with a draft bin/vh tts]")
    return rows

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", type=Path, nargs="?")
    ap.add_argument("--mode", choices=("onscreen", "subtitle"))
    ap.add_argument("--budget", type=float, metavar="SECONDS", help="how many characters fit in a span of this length")
    ap.add_argument("--export", nargs="?", const="", metavar="OUT", help="write the composition's timed texts as JSON "
                    "(default <project>/texts.json) instead of checking them")
    ap.add_argument("--force", action="store_true", help="--export may overwrite an existing file")
    ap.add_argument("--lang", choices=("zh", "en"))
    ap.add_argument("--cjk-cps", type=float, default=4.5)
    ap.add_argument("--latin-cps", type=float, default=15.0)
    ap.add_argument("--pad", type=float, default=1.5)
    ap.add_argument("--min", type=float, default=2.5)
    a = ap.parse_args()
    if a.cjk_cps <= 0 or a.latin_cps <= 0:
        ap.error("--cjk-cps and --latin-cps must be > 0")
    if a.budget is not None:
        if a.budget <= 0: ap.error("--budget must be > 0 seconds")
        print("\n".join(budget(a.budget, a))); sys.exit(0)
    if a.path is None:
        ap.error("give a texts.json, a project folder or a composition .html (or --budget SECONDS)")
    if a.export is not None:
        html = a.path / "index.html" if a.path.is_dir() else a.path
        if html.suffix.lower() not in (".html", ".htm") or not html.exists():
            print(f"readcheck: NOT EXPORTED — {html} is not a composition .html", file=sys.stderr); sys.exit(2)
        items = export_html(html)
        out = Path(a.export) if a.export else html.parent / "texts.json"
        if out.exists() and not a.force:
            print(f"readcheck: {out} exists (maybe edited by hand); pass --force to overwrite, or --export OTHER.json", file=sys.stderr); sys.exit(2)
        out.write_text("[\n" + ",\n".join("  " + json.dumps(it, ensure_ascii=False) for it in items) + ("\n" if items else "") + "]\n", encoding="utf-8")
        print(f"readcheck: {len(items)} timed text(s) from {html.name} → {out}")
        if export_html.untimed:
            print(f"  {export_html.untimed} text block(s) sit in a clip as long as the whole composition (a script shows them): add them by hand")
        print("  a text that fades in is readable later than its clip starts: move its start to that moment, then bin/vh readcheck " + str(out))
        sys.exit(0)
    a.mode = a.mode or "onscreen"
    try:
        path, items = load_items(a.path)
        todo = list(pieces(items, a.lang))
    except (OSError, ValueError) as e:
        print(f"readcheck: NOT CHECKED — {e}", file=sys.stderr); sys.exit(2)
    if not todo:
        extra = (f" ({export_html.untimed} text block(s) have no timing of their own: a script shows them; list them in texts.json)"
                 if path.suffix.lower() in (".html", ".htm") and export_html.untimed else "")
        print(f"readcheck: NOT CHECKED — no text found in {path}{extra}. This is not a pass.", file=sys.stderr); sys.exit(2)

    bad, lw = 0, min(14, max(8, max(len(t[0]) for t in todo)))
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
        print(f"{'OK ' if ok else 'BAD'} {label:<{lw}} {t0:7.2f}–{t1:7.2f}s  {detail}  {json.dumps(short, ensure_ascii=False)}")
    print(f"readcheck ({a.mode}): {len(todo) - bad}/{len(todo)} pass · {path}")
    if path.suffix.lower() in (".html", ".htm"):
        print("  spans are the clips' own (data-start/duration): a text that fades in is readable later; "
              + (f"{export_html.untimed} script-shown block(s) not checked" if export_html.untimed else "all timed text checked"))
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
