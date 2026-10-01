"""Style presets side by side: one labelled row of swatch frames to choose from at gate ①.

usage: bin/vh style compare a,b,c [--frame T] [--out PNG] [--width 640]

Each preset gets a letter (A, B, C …), its name and slug, the one-line grammar note from its STYLE.md ("一句话："),
its palette from tokens.json (bg, fg, accent, then the extras) and the video types it suits. The picture is the
preset's poster (media/poster.jpg), or with --frame T the frame at T seconds of its 5 s swatch (media/swatch.mp4), so
every preset shows the same moment. 2–6 presets.

Output: --out, else <project>/out/check/style-compare-<a>-<b>-<c>.png when run inside a project folder, else
<harness>/projects/style-compare-<a>-<b>-<c>.png (projects/ is not versioned). Deterministic.
"""
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vhdraw as V

STYLES = V.ROOT / "styles"

def presets():
    return sorted(d.name for d in STYLES.iterdir() if d.is_dir() and not d.name.startswith("_") and (d / "STYLE.md").exists())

def note_of(md):
    """The STYLE.md one-liner ("一句话：…", else the first paragraph under the title), cut after the sentence that
    makes it say something."""
    lines = md.splitlines()
    first = next((l for l in lines[1:] if l.strip() and not re.match(r"\s*(#|>|样片|Swatch|\||-|\*)", l)), "")
    for line in lines + ["一句话：" + first]:
        m = re.match(r"\s*(?:一句话|One line)[:：]\s*(.+)", line)
        if m:
            s, out = m.group(1).strip(), ""
            for sent in re.findall(r".+?(?:[。！？]|[.!?](?=\s|$)|$)", s):   # whole sentences, until the note says something
                out += sent
                if len(out) >= (24 if V.has_cjk(out) else 60): break
            return out.strip()
    return ""

def name_of(md, slug, tokens):
    first = (md.splitlines() or [""])[0]
    m = re.match(r"#\s*(.+?)\s*[·|-]\s*" + re.escape(slug) + r"\s*$", first)
    if m: return m.group(1)
    n = tokens.get("name", {})
    return n.get("zh") or n.get("en") or slug if isinstance(n, dict) else (n or slug)

def frame_at(slug, t, width):
    src = STYLES / slug / "media" / "swatch.mp4"
    if not src.exists():
        raise SystemExit(f"style compare: {slug} has no media/swatch.mp4 (bin/vh style {slug} renders it)")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                               capture_output=True, text=True, check=True).stdout.strip() or 0)
    if not 0 <= t < dur:
        raise SystemExit(f"style compare: --frame {t:g} is outside {slug}'s swatch (0–{dur:.2f} s)")
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "f.png"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
                        "-vf", f"scale={width}:-2", str(p)], check=True)
        return Image.open(p).convert("RGB")

TYPE_NAMES = {"zh": {"01": "数学讲解", "02": "知识短视频", "03": "宣传片", "04": "MV", "05": "数据叙事", "06": "论文讲解",
                     "07": "手绘", "08": "网络梗"},
              "en": {"01": "math", "02": "short", "03": "promo", "04": "mv", "05": "data", "06": "paper", "07": "handdrawn", "08": "meme"}}

def hexrgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if re.fullmatch(r"[0-9A-Fa-f]{6}", h) else None

def main():
    ap = argparse.ArgumentParser(prog="bin/vh style compare", description=__doc__.split("\n\n")[0])
    ap.add_argument("slugs", help="comma-separated presets, e.g. blueprint,bouncy-flat-2d,editorial-data")
    ap.add_argument("--frame", type=float, help="use the swatch frame at this time (s) instead of the poster")
    ap.add_argument("--out", help="output PNG")
    ap.add_argument("--width", type=int, default=640, help="width of each picture (default 640)")
    a = ap.parse_args()
    if not 160 <= a.width <= 2400: ap.error("--width must be 160–2400 (pixels per picture)")
    if a.frame is not None and not a.frame >= 0: ap.error("--frame must be a time in seconds, 0 or more")
    slugs = [s.strip() for s in a.slugs.split(",") if s.strip()]
    have = presets()
    bad = [s for s in slugs if s not in have]
    if bad:
        raise SystemExit(f"style compare: unknown preset(s) {', '.join(bad)}; bin/vh style list shows all {len(have)}")
    if not 2 <= len(slugs) <= 6:
        raise SystemExit("style compare: give 2–6 presets, e.g. bin/vh style compare blueprint,ink-wash,editorial-data")
    if len(set(slugs)) != len(slugs):
        raise SystemExit("style compare: a preset is listed twice")
    tw = a.width; th = int(round(tw * 9 / 16))
    cols = len(slugs) if len(slugs) <= 3 else (2 if len(slugs) == 4 else 3)
    rows = (len(slugs) + cols - 1) // cols
    pad, gap, head_h, foot_h = 36, 28, 64, 160
    W = pad * 2 + cols * tw + (cols - 1) * gap
    H = 70 + rows * (head_h + th + foot_h + gap) + 30
    img = Image.new("RGB", (W, H), V.BG); d = ImageDraw.Draw(img)
    notes = []
    for i, slug in enumerate(slugs):
        md = (STYLES / slug / "STYLE.md").read_text(encoding="utf-8")
        tokens = json.loads((STYLES / slug / "tokens.json").read_text(encoding="utf-8")) if (STYLES / slug / "tokens.json").exists() else {}
        notes.append((slug, name_of(md, slug, tokens), note_of(md), tokens))
    V.check_glyphs([n for _, n, _, _ in notes] + [x for _, _, x, _ in notes])
    zh = any(V.has_cjk(n) for _, n, _, _ in notes)
    what = (f"swatch 第 {a.frame:g} s 的画面" if zh else f"swatch frame at {a.frame:g} s") if a.frame is not None else ("封面（poster）" if zh else "posters")
    V.text(d, (pad, 22), ("风格对照 · " if zh else "Style comparison · ") + what, V.font(30, bold=True), V.INK)
    for i, (slug, name, note, tokens) in enumerate(notes):
        r, c = divmod(i, cols); x = pad + c * (tw + gap); y = 70 + r * (head_h + th + foot_h + gap)
        letter = chr(ord("A") + i)
        V.text(d, (x, y + 10), f"{letter}  ·  {name}", V.font(34, bold=True), V.INK)
        V.text(d, (x + tw, y + 22), slug, V.font(20, mono=True), V.MUTED, "ra")
        if a.frame is not None:
            pic = frame_at(slug, a.frame, tw)
        else:
            poster = STYLES / slug / "media" / "poster.jpg"
            if not poster.exists():
                raise SystemExit(f"style compare: {slug} has no media/poster.jpg (bin/vh style {slug} renders it)")
            try:
                with Image.open(poster) as im: pic = im.convert("RGB")
            except (OSError, ValueError, SyntaxError):
                raise SystemExit(f"style compare: {V.shown(poster)} is not an image (bin/vh style {slug} renders it again)")
        pic = pic.resize((tw, th), Image.LANCZOS) if pic.size != (tw, th) else pic
        img.paste(pic, (x, y + head_h))
        ny = y + head_h + th + 12
        for line in V.wrap(d, note, V.font(22), tw, 2):
            V.text(d, (x, ny), line, V.font(22), V.INK); ny += 30
        # palette chips: bg, fg, accent (with their hex), then the extras; the video types it suits underneath
        pal = tokens.get("palette", {}) if isinstance(tokens, dict) else {}
        chips = [(k, pal.get(k)) for k in ("bg", "fg", "accent")] + [("", e) for e in (pal.get("extra") or [])[:4]]
        cx, cy = x, y + head_h + th + 84
        fm = V.font(15, mono=True)
        for k, hx in chips:
            rgb = hexrgb(hx) if hx else None
            if not rgb: continue
            lab = f"{k} {hx}" if k else ""
            if cx + 28 + (V.tw(d, lab, fm) + 8 if lab else 0) > x + tw: break
            d.rectangle([cx, cy, cx + 26, cy + 26], fill=rgb, outline=V.RULE)
            if lab:
                V.text(d, (cx + 32, cy + 13), lab, fm, V.MUTED, "lm"); cx += 32 + V.tw(d, lab, fm) + 12
            else:
                cx += 32
        types = tokens.get("video_types") if isinstance(tokens, dict) else None
        if types:
            names = TYPE_NAMES["zh" if zh else "en"]
            V.text(d, (x, cy + 44), V.fit(d, ("适合：" if zh else "suits: ") + " · ".join(f"{t} {names.get(t, '')}".strip() for t in types),
                                          V.font(19), tw), V.font(19), V.MUTED)
    if a.out:
        out = Path(a.out)
    else:
        cwd = Path.cwd().resolve(); proj = next((p for p in [cwd, *cwd.parents] if (p / "BRIEF.md").exists()), None)
        name = "style-compare-" + "-".join(slugs) + (f"-t{a.frame:g}" if a.frame is not None else "") + ".png"
        out = (proj / "out" / "check" / name) if proj else (V.ROOT / "projects" / name)
    V.save(img, out)
    print(f"style compare: {V.shown(out)}  ({', '.join(f'{chr(65 + i)} {s}' for i, s in enumerate(slugs))})")

if __name__ == "__main__":
    main()
