"""Shared helpers for the decision pictures: bin/vh storyboard, rhythm, style compare, cover-preview and music --roll.

Everything here is deterministic: the same inputs and fonts give the same PNG bytes. Fonts: VH_FONT / VH_FONT_BOLD
(a .ttf/.ttc path, optionally "path#index"), then the system CJK fonts below, then fc-match. Without a CJK font,
Chinese labels draw as boxes; the tools still run and say so once.
"""
import json, os, re, subprocess, sys
from pathlib import Path
from PIL import ImageFont

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
        cands = [(p, int(i or 0))] + cands
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

def check_cjk_font(texts):
    """Warn once when there is Chinese to draw but only a Latin font was found (the labels would be boxes)."""
    if any(has_cjk(t) for t in texts):
        p, _ = _face(REGULAR, "VH_FONT")
        if p is None or p in {c[0] for c in LATIN}:
            warn_once("no CJK font found: Chinese labels will draw as boxes (install fonts-noto-cjk, or set VH_FONT=/path/font.ttc)")

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
def project_dir(arg):
    """A project given as a path, or as a name under $OVH_PROJECTS / <harness>/projects (the date prefix may be left out)."""
    p = Path(arg).expanduser()
    if p.is_dir():
        return p.resolve()
    base = Path(os.environ.get("OVH_PROJECTS") or ROOT / "projects").expanduser()
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

def load_shots(path):
    """→ (shots, meta). Each shot: id, start, end, segment, reads (list), label, frame, at, unsure (str or None)."""
    data = load_json(path)
    meta = data if isinstance(data, dict) else {}
    raw = data.get("shots") if isinstance(data, dict) else data
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"{shown(path)}: expected a list of shots, or {{\"shots\": [...]}}\n{SHOTS_SCHEMA}")
    shots = []
    for i, s in enumerate(raw):
        if not isinstance(s, dict):
            raise SystemExit(f"{shown(path)}: shot {i + 1} is not an object\n{SHOTS_SCHEMA}")
        t0, t1 = _first(s, "start", "t0"), _first(s, "end", "t1")
        if t0 is None or t1 is None:
            raise SystemExit(f"{shown(path)}: shot {s.get('id', i + 1)} needs start and end (or t0 / t1)\n{SHOTS_SCHEMA}")
        t0, t1 = float(t0), float(t1)
        if t1 <= t0:
            raise SystemExit(f"{shown(path)}: shot {s.get('id', i + 1)} ends at {t1} s, not after its start {t0} s")
        reads = _first(s, "reads", "read", "what")
        reads = [str(r) for r in reads] if isinstance(reads, list) else ([str(reads)] if reads else [])
        uns = _first(s, "unsure", "flag", "risk")
        uns = None if uns in (None, False) else ("" if uns is True else str(uns))
        seg = _first(s, "segment", "stage", "section")
        shots.append({"id": str(s.get("id") or f"S{i + 1:02d}"), "start": t0, "end": t1, "dur": t1 - t0,
                      "segment": str(seg) if seg is not None else "", "reads": reads, "label": s.get("label") or "",
                      "frame": _first(s, "frame", "image"), "at": _first(s, "at", "snapshot"), "unsure": uns})
    shots.sort(key=lambda x: (x["start"], x["end"]))
    return shots, meta

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
