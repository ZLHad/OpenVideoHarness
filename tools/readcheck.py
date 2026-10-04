"""Reading-time check: is every text on screen long enough to be read?

usage: python3 tools/readcheck.py <texts.json | project_dir | composition.html> [--pace relaxed|normal|brisk]
                                  [--mode onscreen|label|subtitle] [--lang zh|en] [--cjk-cps N] [--latin-cps N] [--pad S] [--min S]
       python3 tools/readcheck.py --budget <seconds> [--pace …] [--mode …] [--lang …] [project]   how much text fits in a span
       python3 tools/readcheck.py <composition.html | project_dir> --export [--out texts.json] [--force]

Input: a JSON list of {text, start, end} in seconds (`t0`/`t1` also accepted; `text` may be a list of lines),
or a dict holding that list under "captions" / "texts" / "items" / "cues". Items without `text` but with `zh` / `en`
(the captions.json that `bin/vh captions` writes) are checked once per language; --lang picks one.
A directory means <dir>/audio/captions.json. `start` must be the moment the text is fully shown and readable
(typing, decode and fly-in finished), `end` the moment it starts to leave.

No fixed seconds: on-screen text has a floor and a target (templates/TASTE_CHECKLIST.md #5, playbook/03-motion-design.md §2).
  seconds at a pace = CJK chars / CJK rate + other non-space chars / other rate + pad; mixed zh/en lines count both.
  floor     one read at a brisk speed, any film: CJK/7 + other/20 + 0.5 s, never under 1 s (only so a flash can't pass).
            Below it the text FAILs (exit 1).
  target    the film's pace, a taste default: the BRIEF's "- Pace:" line, else normal; --pace overrides it.
              relaxed  CJK/4.5 + other/15 + 1.0 s     explainers, papers, letters: the viewer reads and thinks
              normal   CJK/6   + other/18 + 0.6 s     most films
              brisk    CJK/7   + other/20 + 0.5 s     fast cuts, memes, beat-cut MVs; the same as the floor
            Below it (but over the floor) the text gets a WARN, exit 0: a look, not a fix list. --cjk-cps, --latin-cps,
            --pad and --min retune the target for one run; the floor never moves.

Three kinds of text:
  onscreen  (default) titles, claims, number cards that nobody reads aloud: the floor, and the film's pace as the target.
  label     a short label in a moving shot, there to point at something (node names, station names, a gate's caption):
            its target is brisk, i.e. one read. Mark it data-read="label". A sentence the viewer must take away stays
            onscreen.
  subtitle  lines that follow the voice: reading-speed ceiling, plus a 1.8 s floor; the voice sets the pace
            CJK text ≤ 9 chars/s (half-width characters count 0.5), Latin text ≤ 20 chars/s (spaces and punctuation count)

Per text: spoken captions that repeat the narration are subtitles, whatever the run's default. A timed element of a
HyperFrames composition carrying data-read="subtitle", on the clip itself or on a clip or scene around it (a
sub-composition's host included), is checked with the subtitle rule; everything else stays on the on-screen rule.
data-read="label" uses the label rule; data-read="onscreen" says the default aloud, and the nearest mark wins, so one
text can opt out of a marked scene. data-pace="relaxed|normal|brisk" works the same way and changes the target of
the texts under it (a brisk montage in a normal film; text the viewer already knows, such as a caption saying what the
picture just showed, may run at brisk).
Marked texts get a `sub` or `lab` tag in the output and count in the totals. A texts.json item takes the same keys,
"read": "subtitle" or "label" and "pace": "brisk" (--export writes them). --mode is the rule for texts that carry no
mark; a mark always wins over it.

The shape of the on-screen formula (characters / rate + pad) comes from lemo-opuscar's core/render/readcheck.mjs and
DIRECTOR.md §7 (MIT, © 2026 LemoLab), whose 4.5 CJK / 15 other chars a second the relaxed pace keeps. The floor, the
paces and the label rule are ours (2026-10-04: a fixed 2.5 s minimum and a 1.5 s pad made fast films drag; the
maintainer asked for no hard-coded intervals). The subtitle ceilings are the Netflix Timed Text Style Guide figures for
adult programmes (Chinese Simplified 9 cps, English USA 20 cps); the 1.8 s floor is lemo's DIRECTOR.md §7.
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

--budget <seconds> answers the question before the text exists: how many characters fit in that span, at the pace
and at the floor, as a subtitle, plus the spoken estimate for Chinese narration from playbook/04-audio.md (4.5–5.5 字/s
for a knowledge short, 3.5–4.5 for an explainer or a paper, within a sentence; x 0.85 for the pauses).

Exit: 0 nothing under the floor (WARNs allowed) · 1 some text under the floor / subtitles too fast · 2 nothing to
check (bad input). Writes nothing, except --export.
"""
import argparse, json, math, os, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

CJK_RANGES = [(0x3040, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
              (0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F), (0x20000, 0x2FA1F)]   # kana, Han, Hangul
SUB_FLOOR, SUB_CPS_CJK, SUB_CPS_LATIN = 1.8, 9.0, 20.0
# reading paces: (CJK chars/s, other non-space chars/s, pad s); playbook/03-motion-design.md §2 says why these numbers
PACES = {"relaxed": (4.5, 15.0, 1.0), "normal": (6.0, 18.0, 0.6), "brisk": (7.0, 20.0, 0.5)}
FLOOR_PACE, FLOOR_MIN, DEFAULT_PACE = "brisk", 1.0, "normal"   # the floor: one brisk read, never under 1 s (a flash)
TAGS = {"subtitle": "sub", "onscreen": "on", "label": "lab"}   # the tag column of a run that mixes rules
STATUS = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL"}   # WARN: over the floor, under the pace's target
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

def pace_name(v):
    """"relaxed" / "normal" / "brisk" from a Pace line, a data-pace or a "pace" value (case and spaces are ignored); None otherwise."""
    v = re.sub(r"\s", "", str(v or "")).lower()
    return v if v in PACES else None

def find_pace(path):
    """(pace, brief, raw): the "- Pace:" line of the nearest BRIEF.md at or above path. pace is None when there is no
    BRIEF.md, no Pace line (raw None) or a value that names no pace (raw is that value)."""
    if path is None:
        return None, None, None
    d = Path(path).resolve()
    d = d if d.is_dir() else d.parent
    while True:
        brief = d / "BRIEF.md"
        if brief.is_file():
            m = re.search(r"(?m)^\s*[-*]\s*Pace\s*[:：]\s*([^<\n]*)", brief.read_text(encoding="utf-8", errors="replace"))
            if not m:
                return None, brief, None
            raw = m.group(1).strip()
            return pace_name(raw), brief, raw
        if d.parent == d:
            return None, None, None
        d = d.parent

def settings(pace=DEFAULT_PACE, cjk_cps=None, latin_cps=None, pad=None, min=None):
    """The run settings verdict() and budget() read: the film's pace and the overrides of its target (None: the pace's)."""
    return argparse.Namespace(pace=pace, cjk_cps=cjk_cps, latin_cps=latin_cps, pad=pad, min=min, mode=None, lang=None)

def pieces(items, lang):
    """Yield (label, start, end, text, mode, pace) for every text to check; mode is the item's own rule ("subtitle" /
    "onscreen" / "label" from its "read" key) and pace its own pace ("pace" key), None for the run's."""
    for i, it in enumerate(items):
        t0, t1 = it.get("start", it.get("t0")), it.get("end", it.get("t1"))
        if t0 is None or t1 is None:
            raise ValueError(f"item {i}: needs start/end (or t0/t1)")
        label = str(it.get("id", i + 1))
        mode = read_mode(it.get("read"))
        if it.get("read") not in (None, "") and mode is None:
            raise ValueError(f"item {label}: \"read\" is {it['read']!r}; use \"subtitle\", \"onscreen\" or \"label\"")
        pace = pace_name(it.get("pace"))
        if it.get("pace") not in (None, "") and pace is None:
            raise ValueError(f"item {label}: \"pace\" is {it['pace']!r}; use \"relaxed\", \"normal\" or \"brisk\"")
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
                yield (f"{label}{'·' + k if k else ''}", float(t0), float(t1), txt, mode, pace)

def seconds_at(text, cjk_cps, latin_cps, pad):
    """CJK chars / cjk_cps + other non-space chars / latin_cps + pad."""
    cjk = sum(1 for c in text if is_cjk(c))
    other = sum(1 for c in text if not c.isspace() and not is_cjk(c))
    return cjk / cjk_cps + other / latin_cps + pad

def floor_need(text):
    """The floor (TASTE_CHECKLIST #5): one read at a brisk speed, never under FLOOR_MIN."""
    return max(FLOOR_MIN, seconds_at(text, *PACES[FLOOR_PACE]))

def pace_rule(a, pace=None):
    """(CJK rate, other rate, pad, minimum) of a pace: a text's own pace as it is, the run's (a.pace) with its overrides."""
    run = getattr(a, "pace", None) or DEFAULT_PACE
    if pace and pace != run:
        return (*PACES[pace], 0.0)
    cjk, lat, pad = PACES[run]
    o = lambda k: getattr(a, k, None)
    return (o("cjk_cps") or cjk, o("latin_cps") or lat, pad if o("pad") is None else o("pad"), o("min") or 0.0)

def target_need(text, a, pace=None):
    """The comfortable time at the pace (a taste default), never under the floor."""
    cjk, lat, pad, lo = pace_rule(a, pace)
    return max(floor_need(text), lo, seconds_at(text, cjk, lat, pad))

def subtitle_check(text, dur):
    if any(is_cjk(c) for c in text):   # Netflix CJK rule: half-width characters count 0.5
        n, limit = sum(0.5 if ord(c) < 128 else 1.0 for c in text.strip()), SUB_CPS_CJK
    else:
        n, limit = float(len(text.strip())), SUB_CPS_LATIN
    need = max(SUB_FLOOR, n / limit)
    return need, n / dur if dur > 0 else float("inf"), limit

def verdict(text, dur, mode, a, pace=None):
    """(state, need, target, rate, limit): one text against the rule of its mode. state is "ok", "warn" (over the
    floor, under the pace's target) or "fail"; need is the floor (a subtitle: its own rule), target the time at the
    text's pace (a label: brisk, the floor; None for a subtitle); rate and limit only for a subtitle."""
    if mode == "subtitle":
        need, rate, limit = subtitle_check(text, dur)
        return ("ok" if dur >= need - 1e-6 else "fail"), need, None, rate, limit
    need = floor_need(text)
    target = need if mode == "label" else target_need(text, a, pace)
    return ("fail" if dur < need - 1e-6 else "warn" if dur < target - 1e-6 else "ok"), need, target, None, None

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

def _mark(n, inherit, attr="data-read", parse=read_mode):
    """(value, raw) from the nearest attr (data-read, data-pace) on n or above it, else (inherit, None); value is None
    when raw names nothing known."""
    while n is not None:
        if attr in n.attrs:
            return parse(n.attrs[attr]), n.attrs[attr]
        n = n.parent
    return inherit, None

def _export(path, base, offset, until, depth, tl, stats, items, read=None, pace=None):
    """The timed text of one composition file, its sub-compositions included, offset by the host's start.
    `read` and `pace` are what a host clip's data-read and data-pace hand down to a sub-composition."""
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
                _export(sub, base, a, end, depth + 1, tl, stats, items, _mark(k, read)[0], _mark(k, pace, "data-pace", pace_name)[0])
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
            pm, raw = _mark(node, pace, "data-pace", pace_name)
            if pm: it["pace"] = pm
            elif raw is not None: stats["badread"].append(f"{rel}#{ident}: data-pace=\"{raw}\"")
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
    resolves (HyperFrames puts those at 0), "badread": data-read / data-pace values that name nothing, "source": where
    the spans came from}. An item carries "read" ("subtitle" / "onscreen" / "label") and "pace" when its clip, or a clip
    around it, is marked."""
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
    return (f"{len(b)} text(s) have a data-read that is not \"subtitle\", \"onscreen\" or \"label\", or a data-pace that is not "
            "\"relaxed\", \"normal\" or \"brisk\", so they were checked as on-screen text at the film's pace: "
            + "; ".join(b[:4]) + (" …" if len(b) > 4 else "")) if b else ""

def budget(span, a):
    """Lines saying how much text fits in span seconds."""
    rows = [f"readcheck budget for {span:.2f} s"]
    def fits(name, cjk, lat, pad, lo, how):
        avail = span - pad
        if span < lo - 1e-9 or avail <= 0:
            why = f"under the {lo:g} s minimum" if span < lo - 1e-9 else f"no longer than the {pad:g} s pad"
            rows.append(f"  {name:<44} nothing: {span:.2f} s is {why}")
        else:
            rows.append(f"  {name:<44} up to {math.floor(avail * cjk + 1e-9)} CJK characters, or {math.floor(avail * lat + 1e-9)} other characters"
                        f"  [({span:.2f} - {pad:g} s) x {cjk:g} / {lat:g} per s{how}; mixed: CJK/{cjk:g} + other/{lat:g} <= {avail:.2f}]")
    if a.mode in (None, "onscreen"):
        cjk, lat, pad, lo = pace_rule(a)
        lo = max(lo, FLOOR_MIN)   # the target is never under the floor
        fits(f"on-screen text, {a.pace} pace (the target):", cjk, lat, pad, lo, f"; never under {lo:g} s")
    if a.mode in (None, "onscreen", "label"):
        fits("the floor, one brisk read (also labels):", *PACES[FLOOR_PACE], FLOOR_MIN, f"; never under {FLOOR_MIN:g} s")
    if a.mode in (None, "subtitle"):
        if span < SUB_FLOOR - 1e-9:
            rows.append(f"  {'subtitle (follows the voice):':<44} nothing: {span:.2f} s is under the {SUB_FLOOR:g} s floor")
        else:
            rows.append(f"  {'subtitle (follows the voice):':<44} up to {math.floor(span * SUB_CPS_CJK + 1e-9)} CJK characters (half-width count 1/2), "
                        f"or {math.floor(span * SUB_CPS_LATIN + 1e-9)} Latin characters with spaces  [x {SUB_CPS_CJK:g} / {SUB_CPS_LATIN:g} per s; floor {SUB_FLOOR:g} s]")
    if a.lang in (None, "zh"):   # playbook/04-audio.md, "旁白要导演": rates within a sentence, x 0.85 for the pauses between sentences
        f = lambda r: math.floor(span * r * PAUSE + 1e-9)
        rows.append(f"  {'narration, Chinese (spoken):':<44} knowledge short about {f(4.5)}-{f(5.5)} characters, explainer or paper about {f(3.5)}-{f(4.5)}"
                    f"  [playbook/04-audio.md: 4.5-5.5 / 3.5-4.5 per s within a sentence, x {PAUSE:g} for the pauses; measure with a draft bin/vh tts]")
    return rows

def pace_source(a):
    """Set a.pace (--pace, else the BRIEF's Pace line, else normal) and say where it came from."""
    if a.pace:
        return "--pace"
    pace, brief, raw = find_pace(a.path)
    shown = brief and (os.path.relpath(brief) if not os.path.relpath(brief).startswith("..") else str(brief))
    if pace:
        a.pace = pace
        return f"Pace in {shown}"
    a.pace = DEFAULT_PACE
    if raw:
        return f"default; {shown} says Pace: {raw!r}, which is not relaxed, normal or brisk"
    return f"default; no Pace line in {shown}" if brief else "default"

def main():
    parts = __doc__.split("\n\n")   # -h: the usage, the two rules, the kinds of text and the exit codes
    ap = argparse.ArgumentParser(prog="bin/vh readcheck", formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description="\n\n".join(x for x in parts if x.startswith(("Reading-time", "No fixed", "Three kinds", "Exit:"))),
                                 epilog="data-read and data-pace marks, compositions and --budget: the top of tools/readcheck.py.")
    ap.add_argument("path", type=Path, nargs="?", help="a texts.json, a project folder (its audio/captions.json) or a composition .html")
    ap.add_argument("--pace", choices=tuple(PACES), help="the film's reading pace (default: the BRIEF's Pace line, else normal)")
    ap.add_argument("--mode", choices=("onscreen", "label", "subtitle"), help="the rule for texts without a data-read mark (default onscreen)")
    ap.add_argument("--budget", type=float, metavar="SECONDS", help="how many characters fit in a span of this length")
    ap.add_argument("--export", action="store_true", help="write the composition's timed text as JSON (to --out, default "
                    "<project>/texts.json) instead of checking it")
    ap.add_argument("--out", type=Path, help="where --export writes (a file, or a folder for texts.json in it)")
    ap.add_argument("--force", action="store_true", help="--export may overwrite an existing file")
    ap.add_argument("--lang", choices=("zh", "en"), help="check one language of a bilingual captions.json")
    ap.add_argument("--cjk-cps", type=float, help="retune the target: CJK characters a second (the floor does not move)")
    ap.add_argument("--latin-cps", type=float, help="retune the target: other non-space characters a second")
    ap.add_argument("--pad", type=float, help="retune the target: seconds added to every text")
    ap.add_argument("--min", type=float, help="retune the target: a minimum in seconds")
    a = ap.parse_args()
    if any(v is not None and not (v > 0 and math.isfinite(v)) for v in (a.cjk_cps, a.latin_cps)):
        ap.error("--cjk-cps and --latin-cps must be > 0")
    if any(v is not None and not (v >= 0 and math.isfinite(v)) for v in (a.pad, a.min)):
        ap.error("--pad and --min must be >= 0 seconds")
    if a.budget is not None:
        if not a.budget > 0 or not math.isfinite(a.budget): ap.error("--budget must be > 0 seconds")
        src = pace_source(a)
        print("\n".join(budget(a.budget, a)))
        if a.mode in (None, "onscreen"): print(f"  pace {a.pace} ({src})")
        sys.exit(0)
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
    src = pace_source(a)
    try:
        path, items = load_items(a.path)
        todo = list(pieces(items, a.lang))
    except (OSError, ValueError) as e:
        print(f"readcheck: NOT CHECKED — {e}", file=sys.stderr); sys.exit(2)
    is_html = path.suffix.lower() in (".html", ".htm")
    note = skipped_note(LAST_STATS) if is_html else ""
    if not todo:
        print(f"readcheck: NOT CHECKED — no text found in {path}{' (left out: ' + note + ')' if note else ''}. This is not a pass.", file=sys.stderr); sys.exit(2)

    count, lw = Counter(), min(14, max(8, max(len(t[0]) for t in todo)))
    own = Counter(t[4] for t in todo if t[4] and t[4] != a.mode)   # texts whose own mark differs from the run's rule
    paced = False   # did any text go by a pace (not a subtitle)?
    tuned = any(v is not None for v in (a.cjk_cps, a.latin_cps, a.pad, a.min))   # the run's target retuned by hand
    for label, t0, t1, text, mode, pace in todo:
        dur = t1 - t0
        mode = mode or a.mode
        state, need, target, rate, limit = verdict(text, dur, mode, a, pace)
        if mode == "subtitle":
            detail = f"shown {dur:5.2f}s  need  {need:5.2f}s  ({rate:4.1f}/s, limit {limit:g}/s)"
        elif mode == "label":
            detail = f"shown {dur:5.2f}s  floor {need:5.2f}s  (a label: one read)"
            paced = True
        else:
            name = "target" if tuned and pace in (None, a.pace) else pace or a.pace
            detail = f"shown {dur:5.2f}s  floor {need:5.2f}s  {name} {target:5.2f}s"
            paced = True
        count[state] += 1
        short = text if len(text) <= 28 else text[:27] + "…"
        tag = f" {TAGS[mode] if mode != a.mode else '':<3}" if own else ""   # a tag column only when some text is not on the run's rule
        print(f"{STATUS[state]} {label:<{lw}}{tag} {t0:7.2f}–{t1:7.2f}s  {detail}  {json.dumps(short, ensure_ascii=False)}")
    mixed = "".join(f", {n} of {len(todo)} as {m}" for m, n in own.items())
    rule = f"{a.mode}{mixed}" + (f"; pace {a.pace}, {src}" if paced else "")
    tally = f"{len(todo) - count['fail']}/{len(todo)} pass" + (f" · {count['fail']} FAIL" if count["fail"] else "") \
        + (f" · {count['warn']} WARN (under the {'retuned' if tuned else a.pace} target, over the floor: a look, not a fix list)" if count["warn"] else "")
    print(f"readcheck ({rule}): {tally} · {path}")
    if is_html:   # never claim everything was checked when something was left out
        print(f"  spans from {LAST_STATS.get('source', 'the composition')}; a text that fades in is readable later than its clip starts")
        print(f"  NOT checked: {note}" if note else "  every timed text in the composition was checked")
        if zeroed_note(LAST_STATS): print(f"  note: {zeroed_note(LAST_STATS)}")
        if badread_note(LAST_STATS): print(f"  note: {badread_note(LAST_STATS)}")
    sys.exit(1 if count["fail"] else 0)

if __name__ == "__main__":
    main()
