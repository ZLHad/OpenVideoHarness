"""Shared helpers for the decision pictures: bin/vh storyboard, rhythm, style compare, cover-preview and music --roll.

Everything here is deterministic: the same inputs and fonts give the same PNG bytes. Fonts: VH_FONT / VH_FONT_BOLD
(a .ttf/.ttc path, optionally "path#index"), then the system CJK fonts below, then fc-match. Without a CJK font,
Chinese labels draw as boxes; the tools still run and say so once.
"""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (path, face index): macOS first, then the usual Linux packages (fonts-noto-cjk, wqy), then Latin-only fallbacks
REGULAR = [("/System/Library/Fonts/Hiragino Sans GB.ttc", 0), ("/System/Library/Fonts/STHeiti Light.ttc", 1),
           ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2), ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 2),
           ("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", 2), ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
           ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0)]
BOLD = [("/System/Library/Fonts/Hiragino Sans GB.ttc", 2), ("/System/Library/Fonts/STHeiti Medium.ttc", 1),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 2), ("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc", 2),
        ("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc", 2)] + REGULAR
LATIN = [("/System/Library/Fonts/Helvetica.ttc", 0), ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0)]
MONO = [("/System/Library/Fonts/Menlo.ttc", 0), ("/System/Library/Fonts/SFNSMono.ttf", 0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 0)]

# a light "paper" theme, close to the hand-made review prototypes
BG, INK, MUTED, FAINT, RULE = (248, 246, 241), (34, 34, 38), (128, 126, 120), (222, 219, 211), (205, 201, 192)
RED, RED_SOFT, AMBER, BLUE = (200, 65, 43), (236, 190, 178), (214, 151, 26), (43, 92, 158)
SEGMENT = [(43, 92, 158), (217, 151, 26), (58, 138, 116), (122, 85, 165), (46, 143, 163), (150, 110, 60),
           (110, 128, 56), (80, 96, 130), (140, 90, 130), (120, 120, 128)]   # no reds: red means "look here"

_fonts, _warned = {}, set()

def _face(cands, env):
    spec = os.environ.get(env)
    if spec:
        p, _, i = spec.partition("#")
        if Path(p).is_file():
            cands = [(p, int(i) if i.isdigit() else 0)] + cands
        else:
            warn_once(f"{env}={spec}: no such font file; using the system fonts")
    for p, i in cands:
        if Path(p).exists():
            return p, i
    try:   # Linux without the usual packages: ask fontconfig for a Chinese-capable face
        out = subprocess.run(["fc-match", "-f", "%{file}", "sans:lang=zh-cn"], capture_output=True, text=True, timeout=10).stdout
        if out and Path(out).exists():
            return out, 0
    except (OSError, subprocess.SubprocessError):
        pass
    for p, i in LATIN:
        if Path(p).exists():
            return p, i
    return None, 0

def font(size, bold=False, mono=False):
    from PIL import ImageFont   # here, not at the top: review.py imports this module without pillow
    key = (int(size), bold, mono)
    if key not in _fonts:
        p, i = _face(MONO, "VH_FONT_MONO") if mono else _face(BOLD if bold else REGULAR, "VH_FONT_BOLD" if bold else "VH_FONT")
        try:
            _fonts[key] = ImageFont.truetype(p, int(size), index=i) if p else ImageFont.load_default(size=int(size))
        except OSError:
            _fonts[key] = ImageFont.load_default(size=int(size))
    return _fonts[key]

def warn_once(msg):
    if msg not in _warned:
        _warned.add(msg); print(f"! {msg}", file=sys.stderr)

def is_cjk(ch):
    o = ord(ch)
    return 0x2E80 <= o <= 0x9FFF or 0xAC00 <= o <= 0xD7AF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or 0x20000 <= o <= 0x2FA1F

def has_cjk(s):
    return any(is_cjk(c) for c in str(s))

def missing_glyphs(f, text):
    """The characters of text that font f has no glyph for (FreeType draws its .notdef box, or nothing)."""
    nd = f.getmask("\U0010FFFF"); notdef = (nd.size, bytes(nd))
    out = []
    for ch in sorted(set(str(text))):
        if ch.isspace() or not ch.isprintable(): continue
        m = f.getmask(ch)
        if m.getbbox() is None or (m.size, bytes(m)) == notdef:
            out.append(ch)
    return out

def is_emoji(ch):
    o = ord(ch)
    return 0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0xFE00 <= o <= 0xFE0F

def check_glyphs(texts):
    """Warn once, naming them, when the labels hold characters the drawing font cannot draw (they come out as boxes):
    Chinese without a CJK font, emoji, rare symbols. Checks the glyphs, not the font's name."""
    missing = missing_glyphs(font(20), "".join(str(t) for t in texts))
    if not missing: return
    sample = "".join(missing[:12]) + ("…" if len(missing) > 12 else "")
    cjk, emoji = [c for c in missing if is_cjk(c)], [c for c in missing if is_emoji(c)]
    why = ("no CJK font: install fonts-noto-cjk, or set VH_FONT=/path/font.ttc" if cjk else
           "emoji are not in the drawing font; write them as words" if emoji and len(emoji) == len(missing) else
           "set VH_FONT to a font that has them")
    warn_once(f"{len(missing)} character(s) will draw as boxes ({sample}): {why}")

def tw(draw, s, f):
    return draw.textlength(str(s), font=f)

def fit(draw, s, f, width):
    """s cut with … so it fits in width px."""
    s = str(s)
    if tw(draw, s, f) <= width:
        return s
    while s and tw(draw, s + "…", f) > width:
        s = s[:-1]
    return s + "…" if s else ""

CLOSING = set("，。、；：？！）」』】》〉,.;:?!)]}…")

def wrap(draw, s, f, width, max_lines=2):
    """Lines of s within width: CJK breaks between any two characters, Latin at spaces; the last line ends in … if cut."""
    tokens = re.findall(r"[A-Za-z0-9_.,:;!?%/+\-–'’()\[\]<>=#&@$€£¥·×→←°ΔΣπμ]+|\s+|.", str(s))
    lines, cur = [], ""
    for tok in tokens:
        if tok.isspace():
            if cur: cur += " "
            continue
        if cur and (tw(draw, cur + tok, f) <= width or tok in CLOSING):   # closing punctuation hangs, never starts a line
            cur += tok; continue
        if cur:
            lines.append(cur.rstrip())
        cur = tok
        while tw(draw, cur, f) > width and len(cur) > 1:   # a single token wider than the line: hard break
            cut = len(cur)
            while cut > 1 and tw(draw, cur[:cut], f) > width: cut -= 1
            lines.append(cur[:cut]); cur = cur[cut:]
    if cur.strip():
        lines.append(cur.rstrip())
    if len(lines) > max_lines:
        lines = lines[:max_lines]; lines[-1] = fit(draw, lines[-1] + "…", f, width) if not lines[-1].endswith("…") else lines[-1]
        if not lines[-1].endswith("…"): lines[-1] = fit(draw, lines[-1], f, width - tw(draw, "…", f)) + "…"
    return lines

def text(draw, xy, s, f, fill=INK, anchor="la"):
    draw.text(xy, str(s), font=f, fill=fill, anchor=anchor)

def seg_color(i):
    return SEGMENT[i % len(SEGMENT)]

def mix(c1, c2, a):
    """c1 blended toward c2 by a (0..1)."""
    return tuple(int(round(x + (y - x) * a)) for x, y in zip(c1, c2))

def dashed_hline(draw, x0, x1, y, fill, dash=8, gap=6, width=2):
    x = x0
    while x < x1:
        draw.line([(x, y), (min(x + dash, x1), y)], fill=fill, width=width); x += dash + gap

def save(img, path, dpi=None):
    """PNG with no timestamps or other varying metadata (Pillow writes none by default); the folder is made."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    kw = {"dpi": (dpi, dpi)} if dpi else {}
    img.save(path, "PNG", optimize=False, compress_level=6, **kw)
    return path

def shown(path, base=None):
    """A path as the user reads it: relative to base (e.g. the project), the current directory or the harness when it
    is inside one of them, else absolute."""
    p = Path(path).resolve()
    for b in ([Path(base).resolve()] if base else []) + [Path.cwd(), ROOT]:
        try: return str(p.relative_to(b))
        except ValueError: pass
    return str(p)

# ---------- labels in the picture's language (zh when the content is Chinese) ----------
LABELS = {
    "zh": {"shots": "镜头", "narration": "旁白", "captions": "字幕", "onscreen": "画面文字", "music": "配乐", "issues": "问题",
           "unsure": "【?】没把握", "segment": "段落", "avg": "平均", "limit": "上限", "page": "页", "frames": "画面来源",
           "no_frame": "没有画面", "long": "超过", "too_short": "太短", "too_fast": "太快", "shot_n": "{n} 镜", "shot_1": "1 镜",
           "overview": "分镜总览", "seconds": "s", "hits": "重拍"},
    "en": {"shots": "Shots", "narration": "Narration", "captions": "Captions", "onscreen": "On-screen text", "music": "Music",
           "issues": "Issues", "unsure": "[?] unsure", "segment": "Segment", "avg": "avg", "limit": "limit", "page": "page",
           "frames": "frames", "no_frame": "no frame", "long": "over", "too_short": "too short", "too_fast": "too fast",
           "shot_n": "{n} shots", "shot_1": "1 shot", "overview": "Storyboard overview", "seconds": "s", "hits": "hits"},
}

def lang_for(texts, forced=None):
    if forced in LABELS:
        return forced
    return "zh" if any(has_cjk(t) for t in texts) else "en"

# ---------- projects ----------
def projects_base():
    """Where projects live: $OVH_PROJECTS, else <harness>/projects (bin/vh new --dir puts one elsewhere)."""
    return Path(os.environ.get("OVH_PROJECTS") or ROOT / "projects").expanduser()

def project_dir(arg):
    """A project given as a path, or as a name under $OVH_PROJECTS / <harness>/projects (the date prefix may be left out)."""
    p = Path(arg).expanduser()
    if p.is_dir():
        return p.resolve()
    base = projects_base()
    if (base / arg).is_dir():
        return (base / arg).resolve()
    hits = sorted(d for d in base.glob(f"*-{arg}") if d.is_dir()) if base.is_dir() else []
    if len(hits) == 1:
        return hits[0].resolve()
    if len(hits) > 1:
        raise SystemExit(f"{arg}: several projects match: {', '.join(h.name for h in hits)}")
    raise SystemExit(f"no such project: {arg} (a folder, or a name under {shown(base)})")

# the pace rule of each video type: "a new payoff every N s" (upper bound), quoted from video-types/*.md
PAYOFF = {
    "01": (15.0, "01: 每 5–15 秒一个视觉观点"),
    "02": (5.0, "02: 之后每 3–5 秒给一个新的视觉回报"),
    "04": (4.0, "04: 每句歌词对应一个镜头，每镜 1.4–4 秒"),
    "08": (1.5, "08: 每 0.5–1.5 秒一个硬切"),
}

def payoff_limit(project, override=None):
    """(seconds or None, where the number comes from). --max wins; then a 'payoff every A–B s' line in BRIEF.md;
    then the type the project was made from (bin/vh new writes '<!-- from NN-….md -->' into BRIEF.md)."""
    if override:
        return float(override), "--max"
    brief = Path(project) / "BRIEF.md"
    s = brief.read_text(encoding="utf-8", errors="replace") if brief.exists() else ""
    m = re.search(r"payoff every\s*(?:[\d.]+\s*[–-]\s*)?([\d.]+)\s*s", s, re.I)
    if m:
        return float(m.group(1)), f"BRIEF.md: {m.group(0)}"
    m = re.search(r"<!-- from (\d\d)-", s)
    if m and m.group(1) in PAYOFF:
        return PAYOFF[m.group(1)]
    return None, "no payoff interval in the type doc: pass --max N to flag long shots"

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

SHOTS_SCHEMA = """shots.json: a list of shots, or {"video": "out/animatic.mp4", "shots": [...]}. Per shot:
  id       "S01" (default S01, S02 … in order)          start / end   seconds (t0 / t1 also read), required
  segment  the part it belongs to, e.g. "钩子" (stage / section also read); pages follow first appearance
  reads    what the viewer must get: a string or a list (read / what also read)
  label    optional title, e.g. "第一步 · 看见"          frame   an image for the tile, relative to the project
  at       snapshot time for the tile (default: start + 60 % of the shot)
  unsure   true, or why this shot is the least sure one (flag / risk also read): drawn with a red frame"""

def _first(d, *keys):
    for k in keys:
        if d.get(k) not in (None, ""):
            return d[k]
    return None

def seconds(v):
    """12.5, "12.5", "0:12.5" or "1:02:03" → seconds; None when it is none of these."""
    if isinstance(v, bool): return None
    if isinstance(v, (int, float)): x = float(v)
    else:
        m = re.fullmatch(r"\s*(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)\s*", str(v))
        try:
            x = (int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else float(v)
        except (TypeError, ValueError):
            return None
    return x if x == x and abs(x) != float("inf") else None

def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")

def disp(start, end):
    """(start, end, length) as the pictures print them: the ends to 0.1 s and the length derived from those two, so a
    9.25–11.2 s shot reads 9.2–11.2 s (2.0 s), never 9.2–11.2 s (1.9 s)."""
    a, b = f"{start:.1f}", f"{end:.1f}"
    return a, b, round(float(b) - float(a), 1)

def load_shots(path):
    """→ (shots, meta). Each shot: id, start, end, segment, reads (list), label, frame, at, unsure (str or None).
    Ids must be unique; overlapping shots and negative starts are allowed but said once (the pictures hide them)."""
    try:
        data = load_json(path)
    except ValueError as e:
        raise SystemExit(f"{shown(path)}: not valid JSON ({e})")
    meta = data if isinstance(data, dict) else {}
    raw = data.get("shots") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        raise SystemExit(f"{shown(path)}: expected a list of shots, or {{\"shots\": [...]}}\n{SHOTS_SCHEMA}")
    if not raw:
        raise SystemExit(f"{shown(path)}: the list of shots is empty\n{SHOTS_SCHEMA}")
    shots = []
    for i, s in enumerate(raw):
        if not isinstance(s, dict):
            raise SystemExit(f"{shown(path)}: shot {i + 1} is not an object\n{SHOTS_SCHEMA}")
        t0, t1 = _first(s, "start", "t0"), _first(s, "end", "t1")
        if t0 is None or t1 is None:
            raise SystemExit(f"{shown(path)}: shot {s.get('id', i + 1)} needs start and end (or t0 / t1)\n{SHOTS_SCHEMA}")
        a, b = seconds(t0), seconds(t1)
        if a is None or b is None:
            raise SystemExit(f"{shown(path)}: shot {s.get('id', i + 1)}: {t0!r}–{t1!r} are not times (seconds such as 12.5, or 0:12.5)")
        t0, t1 = a, b
        if t1 <= t0:
            raise SystemExit(f"{shown(path)}: shot {s.get('id', i + 1)} ends at {t1} s, not after its start {t0} s")
        at = _first(s, "at", "snapshot")
        if at is not None and seconds(at) is None:
            raise SystemExit(f"{shown(path)}: shot {s.get('id', i + 1)}: at {at!r} is not a time")
        reads = _first(s, "reads", "read", "what")
        reads = [str(r) for r in reads] if isinstance(reads, list) else ([str(reads)] if reads else [])
        uns = _first(s, "unsure", "flag", "risk")
        uns = None if uns in (None, False) else ("" if uns is True else str(uns))
        seg = _first(s, "segment", "stage", "section")
        ds, de, dd = disp(t0, t1)
        shots.append({"id": str(s.get("id") or f"S{i + 1:02d}"), "start": t0, "end": t1, "dur": t1 - t0, "ds": ds, "de": de, "dd": dd,
                      "segment": str(seg) if seg is not None else "", "reads": reads, "label": s.get("label") or "",
                      "frame": _first(s, "frame", "image"), "at": seconds(at) if at is not None else None, "unsure": uns})
    seen, dup = set(), []
    for x in shots:
        if x["id"] in seen: dup.append(x["id"])
        seen.add(x["id"])
    if dup:
        raise SystemExit(f"{shown(path)}: shot id(s) used twice: {', '.join(sorted(set(dup)))} (every shot needs its own id)")
    shots.sort(key=lambda x: (x["start"], x["end"]))
    neg = [x["id"] for x in shots if x["start"] < 0]
    if neg: warn_once(f"shot(s) starting before 0 s: {', '.join(neg)}")
    over = [f"{p['id']}/{q['id']}" for p, q in zip(shots, shots[1:]) if q["start"] < p["end"] - 1e-6]
    if over: warn_once(f"overlapping shots (the pictures draw them side by side, hiding the overlap): {', '.join(over)}")
    return shots, meta

def narration(project, lang=None):
    """The narration lines [{id, start, end, text}] and their file: timeline.<lang>.json first when a language is
    asked for (timeline.json is whichever language bin/vh tts ran last), else timeline.json, then any timeline*.json."""
    audio = Path(project) / "audio"
    cands = (([audio / f"timeline.{lang}.json"] if lang else []) + [audio / "timeline.json"] +
             sorted(audio.glob("timeline*.json")) if audio.is_dir() else [])
    for p in cands:
        if not p.exists(): continue
        try:
            d = load_json(p)
        except ValueError:
            warn_once(f"{shown(p, project)} is not valid JSON; skipped"); continue
        segs = d.get("segments", d) if isinstance(d, dict) else d
        out = []
        for i, s in enumerate(segs if isinstance(segs, list) else []):
            if not isinstance(s, dict): continue
            a, b = seconds(s.get("start")), seconds(s.get("end"))
            if a is None or b is None: continue
            txt = s.get("text") or (s.get(lang) if lang else None) or s.get("zh") or s.get("en") or ""
            out.append({"id": str(s.get("id", i + 1)), "start": a, "end": b, "text": str(txt)})
        if out:
            return out, p
    return [], None

def relpath(path, project):
    """A path for files that live with the project (index.json, review.json): relative to the project when inside it,
    else absolute; never relative to wherever the command was run."""
    p = Path(path).resolve()
    try: return p.relative_to(Path(project).resolve()).as_posix()
    except ValueError: return str(p)

def segments_of(shots):
    """[(name, [shots…])]: runs of consecutive shots with the same segment, in time order (a name that comes back
    later starts a new run); shots without a segment form unnamed runs."""
    runs = []
    for s in shots:
        if runs and runs[-1][0] == s["segment"]:
            runs[-1][1].append(s)
        else:
            runs.append((s["segment"], [s]))
    return runs
