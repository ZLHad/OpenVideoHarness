"""Contact gallery of every style swatch.

    uv run --with pillow python styles/_swatch/gallery.py            # → styles/gallery.jpg (≤ 2 MB)
    uv run --with pillow python styles/_swatch/gallery.py --mp4      # + styles/gallery.mp4 (~1.5 s per style, ≤ 12 MB)
    options: --cols N (default 5) · --out-dir DIR · --clip-start 1.9 --clip-len 1.5 · [style folders …]

Scans styles/*/media/poster.jpg (folders starting with "_" are skipped) unless folders are given. The label under
each poster comes from the STYLE.md title line "# <风格名> · <slug>", else tokens.json "name", else the slug.
"""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "styles"
JPG_LIMIT, MP4_LIMIT = 2_000_000, 12_000_000
BG, FG, MUTED = (20, 20, 23), (236, 234, 228), (138, 135, 127)

def font(size, mono=False):
    cands = (["/System/Library/Fonts/Menlo.ttc"] if mono else []) + [
        "/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for f in cands:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def label_of(d: Path):
    slug = d.name
    md = d / "STYLE.md"
    if md.exists():
        first = (md.read_text(encoding="utf-8").splitlines() or [""])[0]
        m = re.match(r"#\s*(.+?)\s*$", first)
        if m and "<" not in m.group(1):
            title = re.sub(rf"\s*[·|-]\s*{re.escape(slug)}\s*$", "", m.group(1)).strip()
            return title or slug, slug
    tk = d / "tokens.json"
    if tk.exists():
        try:
            name = json.loads(tk.read_text(encoding="utf-8")).get("name")
            if name: return str(name), slug
        except json.JSONDecodeError:
            pass
    return slug, slug

def fit(draw, text, fnt, width):
    if draw.textlength(text, font=fnt) <= width: return text
    while text and draw.textlength(text + "…", font=fnt) > width: text = text[:-1]
    return text + "…"

def build_jpg(dirs, out: Path, cols: int):
    tw, th, pad, band, head = 512, 288, 24, 70, 110
    rows = (len(dirs) + cols - 1) // cols
    W, H = cols * tw + (cols + 1) * pad, head + rows * (th + band) + (rows + 1) * pad // 2 + pad
    img = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(img)
    f_title, f_name, f_slug = font(40), font(26), font(18, mono=True)
    dr.text((pad, 34), f"OpenVideoHarness · style library · {len(dirs)} swatches", font=f_title, fill=FG)
    for i, d in enumerate(dirs):
        r, c = divmod(i, cols)
        x, y = pad + c * (tw + pad), head + r * (th + band + pad // 2)
        poster = Image.open(d / "media" / "poster.jpg").convert("RGB").resize((tw, th), Image.LANCZOS)
        img.paste(poster, (x, y))
        name, slug = label_of(d)
        dr.text((x, y + th + 10), fit(dr, name, f_name, tw), font=f_name, fill=FG)
        if slug != name: dr.text((x, y + th + 44), slug, font=f_slug, fill=MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    for q in (90, 85, 80, 75, 70, 60, 50):
        img.save(out, "JPEG", quality=q, optimize=True, progressive=True)
        if out.stat().st_size <= JPG_LIMIT: break
    print(f"✓ {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}  {img.width}×{img.height}  {out.stat().st_size/1e6:.2f} MB (q {q})")

def build_mp4(dirs, out: Path, start: float, length: float):
    ff = lambda *a: subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
    tmp = Path(tempfile.mkdtemp(prefix="swatch-gallery-"))
    try:
        parts = []
        for i, d in enumerate(dirs):
            src = d / "media" / "swatch.mp4"
            name, slug = label_of(d)
            lab = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); dr = ImageDraw.Draw(lab)
            f1, f2 = font(30), font(18, mono=True)
            w = max(dr.textlength(name, font=f1), dr.textlength(slug, font=f2)) + 40
            dr.rectangle((0, 720 - 96, w, 720 - 20), fill=(12, 12, 14, 200))
            dr.text((20, 720 - 90), name, font=f1, fill=FG + (255,))
            if slug != name: dr.text((20, 720 - 48), slug, font=f2, fill=MUTED + (255,))
            lab.save(tmp / f"l{i}.png")
            part = tmp / f"p{i:03d}.mp4"
            ff("-ss", f"{start}", "-t", f"{length}", "-i", str(src), "-i", str(tmp / f"l{i}.png"),
               "-filter_complex", "[0:v]scale=1280:720,fps=30,format=yuv420p[v];[v][1:v]overlay=0:0,format=yuv420p",
               "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", str(part))
            parts.append(part)
        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        for crf in (20, 23, 26, 29, 32):
            ff("-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(out))
            if out.stat().st_size <= MP4_LIMIT: break
        print(f"✓ {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}  {len(dirs)} × {length}s  {out.stat().st_size/1e6:.2f} MB (crf {crf})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*", type=Path)
    ap.add_argument("--mp4", action="store_true"); ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--out-dir", type=Path, default=STYLES)
    ap.add_argument("--clip-start", type=float, default=1.9); ap.add_argument("--clip-len", type=float, default=1.5)
    a = ap.parse_args()
    dirs = [d.resolve() for d in a.dirs] if a.dirs else sorted(d for d in STYLES.iterdir() if d.is_dir() and not d.name.startswith("_"))
    have = [d for d in dirs if (d / "media" / "poster.jpg").exists()]
    for d in dirs:
        if d not in have: print(f"! skip {d.name}: no media/poster.jpg (run styles/_swatch/render.sh {d.name})")
    if not have: sys.exit("no swatches rendered yet")
    build_jpg(have, a.out_dir / "gallery.jpg", a.cols)
    if a.mp4:
        vids = [d for d in have if (d / "media" / "swatch.mp4").exists()]
        build_mp4(vids, a.out_dir / "gallery.mp4", a.clip_start, a.clip_len)

if __name__ == "__main__":
    main()
