"""Reading-time check: is every text on screen long enough to be read?

usage: python3 tools/readcheck.py <texts.json | project_dir | composition.html> [--mode onscreen|label|subtitle] [--lang zh|en]
                                  [--cjk-cps 4.5] [--latin-cps 15] [--pad 1.5] [--min 2.5]
       python3 tools/readcheck.py --budget <seconds> [--mode …] [--lang …]    how much text fits in a span
       python3 tools/readcheck.py <composition.html | project_dir> --export [--out texts.json] [--force]

Input: a JSON list of {text, start, end} in seconds (`t0`/`t1` also accepted; `text` may be a list of lines),
or a dict holding that list under "captions" / "texts" / "items" / "cues". Items without `text` but with `zh` / `en`
(the captions.json that `bin/vh captions` writes) are checked once per language; --lang picks one.
A directory means <dir>/audio/captions.json. `start` must be the moment the text is fully shown and readable
(typing, decode and fly-in finished), `end` the moment it starts to leave.

Three rules, templates/TASTE_CHECKLIST.md #5 (rationale in playbook/03-motion-design.md §2):
  onscreen  (default) titles, labels, number cards that nobody reads aloud: minimum time on screen
            need = max(--min, CJK chars / --cjk-cps + other non-space chars / --latin-cps + --pad)
            defaults 4.5 CJK chars/s, 15 chars/s, pad 1.5 s, floor 2.5 s.
  label     a short label in a moving shot, there to point at something, read once: need = max(1.5 s, CJK chars / 7
            + other non-space chars / 20 + 0.8 s). For tags, node names, captions on a passing gate; a sentence the viewer
            must take away (a claim, a number to remember) stays on the on-screen rule. Mark it data-read="label".
  subtitle  lines that follow the voice: reading-speed ceiling, plus a 1.8 s floor
            CJK text ≤ 9 chars/s (half-width characters count 0.5), Latin text ≤ 20 chars/s (spaces and punctuation count)

Per text: spoken captions that repeat the narration are subtitles, whatever the run's default. A timed element of a
HyperFrames composition carrying data-read="subtitle", on the clip itself or on a clip or scene around it (a
sub-composition's host included), is checked with the subtitle rule; everything else stays on the on-screen rule.
data-read="label" uses the label rule; data-read="onscreen" says the default aloud, and the nearest mark wins, so one
text can opt out of a marked scene.
Marked texts get a `sub` or `lab` tag in the output and count in the totals. A texts.json item takes the same key,
"read": "subtitle" or "label" (--export writes it). --mode is the rule for texts that carry no mark; a mark always wins over it.

The onscreen formula comes from lemo-opuscar's core/render/readcheck.mjs and DIRECTOR.md §7 (MIT, © 2026 LemoLab);
the floor is ours (2.5 s). The label rule is ours too (2026-10-04, from the intro film: holds that met the on-screen
rule everywhere made a promo drag, so short labels get one read). The subtitle ceilings are the Netflix Timed Text Style Guide figures for adult programmes
(Chinese Simplified 9 cps, English USA 20 cps); the 1.8 s floor is lemo's DIRECTOR.md §7.
lemo's tool renders the page and asks window.TEXTS(t) for boxes; this one only reads timings, so it cannot see
cropping or text that leaves the frame. Check those on the contact sheet.

A HyperFrames composition (an .html file) is read without a browser. The clip spans come from HyperFrames itself
(`hyperframes timeline --json`, 0.4 s) when the file is a project's index.html and the project has its pinned
hyperframes; otherwise they are resolved here the way HyperFrames does: a number is seconds, "id" starts when that
clip ends, "id + n" / "id - n" shift it; a data-composition-src file is offset by its host's start and built from
its <template> when it has one. The text of each clip becomes one item (split at block elements: two <div>s or an
<h1> and a <p> in one scene are two items). The span is the clip's, so a text that fades in, or that a script shows
and hides, is readable for less than that: set the start by hand for those (--export writes the list to edit).
Left out, and counted: text in a clip as long as the whole film (the usual "draw(t)" script decides when it shows),
and clips whose data-start resolves to nothing (HyperFrames silently puts those at 0).

--budget <seconds> answers the question before the text exists: how many characters fit in that span, by the same
rules (on-screen, subtitle), plus the spoken estimate for Chinese narration from playbook/04-audio.md (4.5–5.5 字/s
for a knowledge short, 3.5–4.5 for an explainer or a paper, within a sentence; x 0.85 for the pauses).

Exit: 0 all pass · 1 some too short / too fast · 2 nothing to check (bad input). Writes nothing, except --export.
"""
import argparse, json, math, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

CJK_RANGES = [(0x3040, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
              (0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F), (0x20000, 0x2FA1F)]   # kana, Han, Hangul
SUB_FLOOR, SUB_CPS_CJK, SUB_CPS_LATIN = 1.8, 9.0, 20.0
LABEL_FLOOR, LABEL_CPS_CJK, LABEL_CPS_LATIN, LABEL_PAD = 1.5, 7.0, 20.0, 0.8   # a short label, read once
TAGS = {"subtitle": "sub", "onscreen": "on", "label": "lab"}   # the tag column of a run that mixes rules
PAUSE = 0.85   # playbook/04-audio.md: script length = seconds x rate x 0.85, the rest is pauses between sentences
LAST_STATS = {}   # what the last composition read left out (export_html)

def is_cjk(ch: str) -> bool:
    o = ord(ch)
    return any(a <= o <= b for a, b in CJK_RANGES)

def load_items(path: Path):
    if path.suffix.lower() in (".html", ".htm"):
        items, stats = export_html(path)
        LAST_STATS.clear(); LAST_STATS.update(stats)
        return path, items
    if path.is_dir():
        path = path / "audio" / "captions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = next((data[k] for k in ("captions", "texts", "items", "cues") if isinstance(data.get(k), list)), None)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON list of {{text, start, end}}")
    return path, data

def read_mode(v):
    """"subtitle" / "onscreen" / "label" from a data-read or "read" value (case, spaces and a hyphen are ignored); None otherwise."""
    v = re.sub(r"[\s_-]", "", str(v or "")).lower()
    return v if v in ("subtitle", "onscreen", "label") else None

def pieces(items, lang):
    """Yield (label, start, end, text, mode) for every text to check; mode is the item's own rule ("subtitle" /
    "onscreen" from its "read" key) or None, which means the run's default."""
    for i, it in enumerate(items):
        t0, t1 = it.get("start", it.get("t0")), it.get("end", it.get("t1"))
        if t0 is None or t1 is None:
            raise ValueError(f"item {i}: needs start/end (or t0/t1)")
        label = str(it.get("id", i + 1))
        mode = read_mode(it.get("read"))
        if it.get("read") not in (None, "") and mode is None:
            raise ValueError(f"item {label}: \"read\" is {it['read']!r}; use \"subtitle\", \"onscreen\" or \"label\"")
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
                yield (f"{label}{'·' + k if k else ''}", float(t0), float(t1), txt, mode)

def onscreen_need(text, a):
    cjk = sum(1 for c in text if is_cjk(c))
    other = sum(1 for c in text if not c.isspace() and not is_cjk(c))
    return max(a.min, cjk / a.cjk_cps + other / a.latin_cps + a.pad)

def label_need(text):
    cjk = sum(1 for c in text if is_cjk(c))
    other = sum(1 for c in text if not c.isspace() and not is_cjk(c))
    return max(LABEL_FLOOR, cjk / LABEL_CPS_CJK + other / LABEL_CPS_LATIN + LABEL_PAD)

def subtitle_check(text, dur):
    if any(is_cjk(c) for c in text):   # Netflix CJK rule: half-width characters count 0.5
        n, limit = sum(0.5 if ord(c) < 128 else 1.0 for c in text.strip()), SUB_CPS_CJK
    else:
        n, limit = float(len(text.strip())), SUB_CPS_LATIN
    need = max(SUB_FLOOR, n / limit)
    return need, n / dur if dur > 0 else float("inf"), limit

def verdict(text, dur, mode, a):
    """(ok, need, rate, limit): one text against the rule of its mode; rate and limit are None for the on-screen rule."""
    if mode == "subtitle":
        need, rate, limit = subtitle_check(text, dur)
        return dur >= need - 1e-6, need, rate, limit
    need = label_need(text) if mode == "label" else onscreen_need(text, a)
    return dur >= need - 1e-6, need, None, None

# ---------- on-screen text straight from a HyperFrames composition ----------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "param"}
SKIP = {"script", "style", "noscript", "title", "head"}
BLOCK = {"div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "section", "article", "header", "footer", "figure",
         "figcaption", "blockquote", "pre", "table", "tr", "td", "th", "svg", "g", "text", "foreignobject", "main", "aside", "nav"}

class _Node:
    __slots__ = ("tag", "attrs", "kids", "parent")
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.kids, self.parent = tag, attrs, [], parent

class _Tree(HTMLParser):
    """A small DOM. A <template> keeps its content as children: the page ignores it, but HyperFrames builds a
    sub-composition from its file's template."""
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

def _elements(n, templates=False):
    """Element nodes under n in document order; a <template>'s content only when asked."""
    for k in n.kids:
        if isinstance(k, _Node):
            if k.tag == "template" and not templates: continue
            yield k
            yield from _elements(k, templates)

def _num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def _parse_start(v):
    """data-start → ("abs", s) or ("ref", id, offset). HyperFrames' own rules: a number is absolute; "id" starts
    when that clip ends; "id + n" / "id - n" shift it (the minus needs spaces: "intro-0.5" is an id)."""
    v = (v or "").strip()
    x = _num(v)
    if x is not None: return ("abs", x)
    m = re.fullmatch(r"(.+?)\s*\+\s*(\d+(?:\.\d+)?)", v)
    if m: return ("ref", m.group(1).strip(), float(m.group(2)))
    m = re.fullmatch(r"(.+?)\s+-\s+(\d+(?:\.\d+)?)", v)
    if m: return ("ref", m.group(1).strip(), -float(m.group(2)))
    return ("ref", v, 0.0)

def _text(n, timed):
    """All text under n, leaving out timed descendants (they are items of their own); CJK runs join without spaces."""
    parts = []
    for k in n.kids:
        if isinstance(k, str): parts.append(k)
        elif k.tag == "br": parts.append(" ")
        elif k.tag != "template" and k not in timed: parts.append(_text(k, timed))
    s = re.sub(r"\s+", " ", "".join(parts)).strip()
    return re.sub(r"(?<=[　-鿿＀-￯]) (?=[　-鿿＀-￯])", "", s)

def _blocks(n, timed):
    """n's text as items: a wrapper with one text-bearing block is looked into; two or more blocks (or blocks beside
    loose text) give one item each; inline-only content (spans, a <br>) stays one item."""
    kids = [k for k in n.kids if (k.strip() if isinstance(k, str) else (k.tag != "template" and k not in timed and _text(k, timed)))]
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

def _timeline(html):
    """{(file, id): (start, end)} from `hyperframes timeline --json`, HyperFrames' own resolver (0.4 s, no browser),
    when the project has its pinned hyperframes and the file is its index.html; else None."""
    proj = Path(html).resolve().parent   # absolute: the command runs with the project as its working directory
    hf = proj / "node_modules" / ".bin" / "hyperframes"
    if html.name != "index.html" or not hf.exists():
        return None
    env = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1", "DO_NOT_TRACK": "1"}
    try:
        r = subprocess.run([str(hf), "timeline", "--json"], cwd=str(proj), capture_output=True, text=True, env=env, timeout=120)
        rows = [row for t in json.loads(r.stdout)["timeline"]["tracks"] for row in t.get("rows", [])]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return None
    spans = {}
    for row in rows:
        ident = row.get("elementId") or row.get("id")
        a, b = _num(row.get("absStart")), _num(row.get("absEnd"))
        if ident and a is not None and b is not None:
            spans[(str(row.get("file") or "index.html"), str(ident))] = (a, b)
    return spans

def _mark(n, inherit):
    """(mode, raw) from the nearest data-read on n or above it, else (inherit, None); mode is None when raw is no known rule."""
    while n is not None:
        if "data-read" in n.attrs:
            return read_mode(n.attrs["data-read"]), n.attrs["data-read"]
        n = n.parent
    return inherit, None

def _export(path, base, offset, until, depth, tl, stats, items, read=None):
    """The timed text of one composition file, its sub-compositions included, offset by the host's start.
    `read` is the rule a host clip's data-read hands down to a sub-composition."""
    root = _Tree(); root.feed(path.read_text(encoding="utf-8", errors="replace")); root.close(); root = root.root
    if depth:   # a sub-composition is built from its file's <template>, when it has one
        root = next((n for n in _elements(root, True) if n.tag == "template"), root)
    rel = path.relative_to(base).as_posix() if base in path.parents or path.parent == base else path.name
    nodes = list(_elements(root))
    comp = next((n for n in nodes if "data-composition-id" in n.attrs), None)
    comp_dur = _num(comp.attrs.get("data-duration")) if comp is not None else None
    comp_end = offset + comp_dur if comp_dur is not None else until
    if until is not None and comp_end is not None: comp_end = min(comp_end, until)
    by_id = {}
    for n in nodes:   # HyperFrames looks up getElementById, then [data-composition-id]
        for key in (n.attrs.get("id"), n.attrs.get("data-composition-id")):
            if key: by_id.setdefault(key, n)
    timed = [n for n in nodes if n is not comp and ("data-start" in n.attrs or "data-composition-src" in n.attrs)]
    tset = set(timed)
    spans, busy = {}, set()
    def parent_span(n):
        p = n.parent
        while p is not None and p not in tset: p = p.parent
        return span(p) if p is not None else (offset, comp_end, comp_end)
    def span(n):   # absolute (start, shown until, own end or None); None when the start cannot be resolved
        if n in spans: return spans[n]
        key = (rel, n.attrs.get("id") or "")
        if tl is not None and key in tl and tl[key][1] > tl[key][0]:
            spans[n] = (*tl[key], tl[key][1]); return spans[n]
        if n in busy: return None   # a cycle: HyperFrames puts it at 0
        busy.add(n)
        ps = parent_span(n)
        raw = n.attrs.get("data-start")
        if raw is None: a = ps[0] if ps else offset   # a host without data-start starts with its parent
        else:
            kind = _parse_start(raw)
            if kind[0] == "abs": a = offset + kind[1]
            else:   # when the target clip ends; a target with no duration of its own: when it starts
                tgt = by_id.get(kind[1]); ts = span(tgt) if tgt is not None and tgt is not n else None
                a = None if ts is None else (ts[2] if ts[2] is not None else ts[0]) + kind[2]
        busy.discard(n)
        if tl is not None and key in tl:   # HyperFrames knows the start but not the end (no duration): keep its start
            a = tl[key][0]
        if a is None:
            spans[n] = None; return None
        du, en = _num(n.attrs.get("data-duration")), _num(n.attrs.get("data-end"))
        own = a + du if du is not None else (offset + en if en is not None else None)
        b = own if own is not None else (ps[1] if ps else comp_end)
        if until is not None and b is not None: b = min(b, until)
        spans[n] = (a, b, own); return spans[n]
    whole = None if comp_end is None else comp_end - offset
    for k in timed:
        s = span(k)
        if s is None:
            stats["unresolved"].append(f"{rel}#{k.attrs.get('id') or k.tag}: data-start=\"{k.attrs.get('data-start')}\""); continue
        a, b = s[0], s[1]
        raw = k.attrs.get("data-start")
        if tl is not None and raw is not None and _parse_start(raw)[0] == "ref" and _parse_start(raw)[1] not in by_id:
            stats["zeroed"].append(f"{rel}#{k.attrs.get('id') or k.tag}: data-start=\"{raw}\"")   # the render puts it at 0
        src = k.attrs.get("data-composition-src")
        if src:
            sub = (path.parent / src)
            if depth < 4 and sub.is_file():
                inner = _export_dur(sub)
                end = b if k.attrs.get("data-duration") or k.attrs.get("data-end") else (a + inner if inner is not None else b)
                _export(sub, base, a, end, depth + 1, tl, stats, items, _mark(k, read)[0])
            else:
                stats["unresolved"].append(f"{rel}#{k.attrs.get('id') or k.tag}: sub-composition {src} not found")
            continue
        if b is None or b <= a:
            if _blocks(k, tset): stats["unresolved"].append(f"{rel}#{k.attrs.get('id') or k.tag}: no duration and nothing to end it")
            continue
        full = depth == 0 and whole is not None and a - offset <= 0.05 and b - offset >= whole - 0.05
        for node, txt in _blocks(k, tset):
            if full:
                stats["untimed"] += 1; continue   # no timing of its own: a script decides when it shows
            ident = node.attrs.get("id") or k.attrs.get("id") or f"{node.tag}@{a:g}"
            it = {"id": ident, "text": txt, "start": round(a, 3), "end": round(b, 3), "from": rel}
            mode, raw = _mark(node, read)
            if mode: it["read"] = mode
            elif raw is not None: stats["badread"].append(f"{rel}#{ident}: data-read=\"{raw}\"")
            if node is not k:   # the span is the enclosing clip's (a scene), not a timing of the text's own
                it["clip"] = k.attrs.get("id") or k.tag
            items.append(it)

def _export_dur(path):
    """A sub-composition's own duration: its root's data-duration."""
    t = _Tree(); t.feed(path.read_text(encoding="utf-8", errors="replace")); t.close()
    n = next((n for n in _elements(t.root, True) if "data-composition-id" in n.attrs), None)
    return _num(n.attrs.get("data-duration")) if n is not None else None

def composition_duration(html):
    """The root composition's data-duration in a HyperFrames index.html (None when it has none)."""
    return _export_dur(Path(html))

def export_html(path):
    """(items, stats): the composition's timed text [{id, text, start, end, from, clip?}], and stats = {"untimed": text
    blocks left out because a clip as long as the whole film holds them, "unresolved": data-start values nothing
    resolves (HyperFrames puts those at 0), "badread": data-read values that name no rule, "source": where the
    spans came from}. An item carries "read": "subtitle" / "onscreen" when its clip, or a clip around it, is marked."""
    path = Path(path)
    tl = _timeline(path)
    stats = {"untimed": 0, "unresolved": [], "zeroed": [], "badread": [], "source": "HyperFrames' own timeline" if tl is not None else "the HTML (no hyperframes in the project to ask)"}
    items = []
    _export(path, path.parent, 0.0, None, 0, tl, stats, items)
    items.sort(key=lambda x: (x["start"], x["end"], x["id"]))
    return items, stats

def skipped_note(stats):
    """What the composition read left out, or "" when nothing was."""
    bits = []
    if stats.get("untimed"): bits.append(f"{stats['untimed']} text block(s) in a clip as long as the whole film (a script shows them)")
    if stats.get("unresolved"): bits.append(f"{len(stats['unresolved'])} clip(s) whose data-start does not resolve: " + "; ".join(stats["unresolved"][:4])
                                           + (" …" if len(stats["unresolved"]) > 4 else ""))
    return " and ".join(bits)

def zeroed_note(stats):
    z = stats.get("zeroed") or []
    return (f"{len(z)} clip(s) start at 0 because their data-start names no clip (HyperFrames does not complain): "
            + "; ".join(z[:4]) + (" …" if len(z) > 4 else "")) if z else ""

def badread_note(stats):
    b = stats.get("badread") or []
    return (f"{len(b)} text(s) have a data-read that is not \"subtitle\", \"onscreen\" or \"label\", so they were checked as on-screen text: "
            + "; ".join(b[:4]) + (" …" if len(b) > 4 else "")) if b else ""

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
    if a.mode in (None, "label"):
        avail = span - LABEL_PAD
        if span < LABEL_FLOOR - 1e-9:
            rows.append(f"  label (short, read once):               nothing: {span:.2f} s is under the {LABEL_FLOOR:g} s floor")
        else:
            rows.append(f"  label (short, read once):               up to {math.floor(avail * LABEL_CPS_CJK + 1e-9)} CJK characters, or "
                        f"{math.floor(avail * LABEL_CPS_LATIN + 1e-9)} other characters  [({span:.2f} - {LABEL_PAD:g} s) x {LABEL_CPS_CJK:g} / {LABEL_CPS_LATIN:g} per s; floor {LABEL_FLOOR:g} s]")
    if a.mode in (None, "subtitle"):
        if span < SUB_FLOOR - 1e-9:
            rows.append(f"  subtitle (follows the voice):           nothing: {span:.2f} s is under the {SUB_FLOOR:g} s floor")
        else:
            rows.append(f"  subtitle (follows the voice):           up to {math.floor(span * SUB_CPS_CJK + 1e-9)} CJK characters (half-width count 1/2), "
                        f"or {math.floor(span * SUB_CPS_LATIN + 1e-9)} Latin characters with spaces  [x {SUB_CPS_CJK:g} / {SUB_CPS_LATIN:g} per s; floor {SUB_FLOOR:g} s]")
    if a.lang in (None, "zh"):   # playbook/04-audio.md, "旁白要导演": rates within a sentence, x 0.85 for the pauses between sentences
        f = lambda r: math.floor(span * r * PAUSE + 1e-9)
        rows.append(f"  narration, Chinese (spoken):            knowledge short about {f(4.5)}-{f(5.5)} characters, explainer or paper about {f(3.5)}-{f(4.5)}"
                    f"  [playbook/04-audio.md: 4.5-5.5 / 3.5-4.5 per s within a sentence, x {PAUSE:g} for the pauses; measure with a draft bin/vh tts]")
    return rows

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", type=Path, nargs="?")
    ap.add_argument("--mode", choices=("onscreen", "label", "subtitle"))
    ap.add_argument("--budget", type=float, metavar="SECONDS", help="how many characters fit in a span of this length")
    ap.add_argument("--export", action="store_true", help="write the composition's timed text as JSON (to --out, default "
                    "<project>/texts.json) instead of checking it")
    ap.add_argument("--out", type=Path, help="where --export writes (a file, or a folder for texts.json in it)")
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
        if not a.budget > 0 or not math.isfinite(a.budget): ap.error("--budget must be > 0 seconds")
        print("\n".join(budget(a.budget, a))); sys.exit(0)
    if a.path is None:
        ap.error("give a texts.json, a project folder or a composition .html (or --budget SECONDS)")
    if a.export:
        html = a.path / "index.html" if a.path.is_dir() else a.path
        if html.suffix.lower() not in (".html", ".htm") or not html.is_file():
            print(f"readcheck: NOT EXPORTED — {html} is not a composition .html", file=sys.stderr); sys.exit(2)
        items, stats = export_html(html)
        out = a.out or html.parent / "texts.json"
        if out.is_dir(): out = out / "texts.json"
        if out.exists() and not a.force:
            print(f"readcheck: {out} exists (maybe edited by hand); pass --force to overwrite, or --out OTHER.json", file=sys.stderr); sys.exit(2)
        try:
            out.write_text("[\n" + ",\n".join("  " + json.dumps(it, ensure_ascii=False) for it in items) + ("\n" if items else "") + "]\n", encoding="utf-8")
        except OSError as e:
            print(f"readcheck: NOT EXPORTED — cannot write {out}: {e.strerror or e}", file=sys.stderr); sys.exit(2)
        print(f"readcheck: {len(items)} timed text(s) from {html.name} → {out}")
        print(f"  spans from {stats['source']}")
        note = skipped_note(stats)
        if note: print(f"  not exported: {note}; add those by hand")
        if zeroed_note(stats): print(f"  note: {zeroed_note(stats)}")
        if badread_note(stats): print(f"  note: {badread_note(stats)}")
        print("  a text that fades in is readable later than its clip starts: move its start to that moment, then bin/vh readcheck " + str(out))
        sys.exit(0)
    a.mode = a.mode or "onscreen"
    try:
        path, items = load_items(a.path)
        todo = list(pieces(items, a.lang))
    except (OSError, ValueError) as e:
        print(f"readcheck: NOT CHECKED — {e}", file=sys.stderr); sys.exit(2)
    is_html = path.suffix.lower() in (".html", ".htm")
    note = skipped_note(LAST_STATS) if is_html else ""
    if not todo:
        print(f"readcheck: NOT CHECKED — no text found in {path}{' (left out: ' + note + ')' if note else ''}. This is not a pass.", file=sys.stderr); sys.exit(2)

    bad, lw = 0, min(14, max(8, max(len(t[0]) for t in todo)))
    own = Counter(t[4] for t in todo if t[4] and t[4] != a.mode)   # texts whose own mark differs from the run's rule
    for label, t0, t1, text, mode in todo:
        dur = t1 - t0
        mode = mode or a.mode
        ok, need, rate, limit = verdict(text, dur, mode, a)
        detail = f"shown {dur:5.2f}s  need {need:5.2f}s" + (f"  ({rate:4.1f}/s, limit {limit:g}/s)" if mode == "subtitle" else "")
        bad += not ok
        short = text if len(text) <= 28 else text[:27] + "…"
        tag = f" {TAGS[mode] if mode != a.mode else '':<3}" if own else ""   # a tag column only when some text is not on the run's rule
        print(f"{'OK ' if ok else 'BAD'} {label:<{lw}}{tag} {t0:7.2f}–{t1:7.2f}s  {detail}  {json.dumps(short, ensure_ascii=False)}")
    mixed = "".join(f", {n} of {len(todo)} as {m}" for m, n in own.items())
    print(f"readcheck ({a.mode}{mixed}): {len(todo) - bad}/{len(todo)} pass · {path}")
    if is_html:   # never claim everything was checked when something was left out
        print(f"  spans from {LAST_STATS.get('source', 'the composition')}; a text that fades in is readable later than its clip starts")
        print(f"  NOT checked: {note}" if note else "  every timed text in the composition was checked")
        if zeroed_note(LAST_STATS): print(f"  note: {zeroed_note(LAST_STATS)}")
        if badread_note(LAST_STATS): print(f"  note: {badread_note(LAST_STATS)}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
