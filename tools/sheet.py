"""Contact sheet with a burned-in timestamp on every tile; or a folder of pictures with a caption under each.

usage: uv run --with pillow python tools/sheet.py <video> <out.png> [cols=6] [fps=1] [width=480]
       uv run --with pillow python tools/sheet.py <folder> <out.png> [cols=5] [-] [width=320]
       label colour via env VH_SHEET_LABEL (default #ffdc00)
Frames are sampled at t = (k + 0.5) / fps so each tile sits mid-interval; the label is that exact time.
A time past the last frame is clamped to it, so a clip shorter than one interval (0.4 s at fps 1) still gets a tile.
A folder: its pictures (covers, stills) in the order of their names, each scaled into a 16:9 cell, its caption from
the folder's captions.json ({"file name": "caption"}) under it in two lines, else its file name.
"""
import json, math, os, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

LABEL = os.environ.get("VH_SHEET_LABEL", "#ffdc00")  # tile label colour; use a grey when the sheet appears inside a film

def probe_duration(video: str):
    """→ (duration, latest safe seek time): a seek past the last frame's start extracts nothing, so stop half a frame
    before it (the seek then lands on the last frame, even after rounding to ms)."""
    out = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                     "format=duration:stream=duration,avg_frame_rate", "-of", "json", video],
                                    capture_output=True, text=True, check=True).stdout)
    st = (out.get("streams") or [{}])[0]
    dur = float(st.get("duration") or out["format"]["duration"])          # the video stream, not a longer audio track
    num, _, den = st.get("avg_frame_rate", "0/0").partition("/")
    rate = float(num) / float(den) if float(den or 0) and float(num or 0) else 0
    return dur, max(0.0, dur - 1.5 / rate) if rate else dur / 2

def font(size: int):
    for f in ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/SFNSMono.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

IMAGES = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")

def image_sheet(folder: str, out: str, cols: int, width: int):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from vhdraw import font as cjk_font, wrap   # the CJK faces: a cover's caption is a title in any script
    d = Path(folder)
    files = sorted(p for p in d.iterdir() if p.suffix.lower() in IMAGES and not p.name.startswith("."))
    if not files:
        sys.exit(f"no pictures in {folder} ({' '.join(IMAGES)})")
    try:
        caps = json.loads((d / "captions.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        caps = {}
    ch, f = width * 9 // 16, cjk_font(max(13, width // 22))
    line = int(f.size * 1.35)
    cell_h = ch + 6 + 2 * line + 10
    rows = math.ceil(len(files) / cols)
    sheet = Image.new("RGB", (cols * width + (cols + 1) * 8, rows * cell_h + 8), (24, 24, 26))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(files):
        x, y = 8 + (i % cols) * (width + 8), 8 + (i // cols) * cell_h
        try:
            im = Image.open(p).convert("RGB")
        except OSError:
            draw.rectangle([x, y, x + width - 1, y + ch - 1], outline=(90, 90, 90))
            draw.text((x + 8, y + 8), "not a picture", fill=(160, 160, 160), font=f)
        else:
            im.thumbnail((width, ch))
            sheet.paste(im, (x + (width - im.width) // 2, y + (ch - im.height) // 2))
        for k, s in enumerate(wrap(draw, caps.get(p.name) or p.stem, f, width, max_lines=2)):
            draw.text((x, y + ch + 6 + k * line), s, fill=LABEL if k == 0 else (225, 225, 225), font=f)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out)

def main():
    video, out = sys.argv[1], sys.argv[2]
    if Path(video).is_dir():
        cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        return image_sheet(video, out, cols, int(sys.argv[5]) if len(sys.argv) > 5 else 320)
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    fps = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    width = int(sys.argv[5]) if len(sys.argv) > 5 else 480
    dur, last = probe_duration(video)
    times = [min((k + 0.5) / fps, last) for k in range(max(1, math.floor(dur * fps)))]   # a short clip still gets a tile
    tiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            p = Path(tmp) / f"{i:04d}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                            "-vf", f"scale={width}:-1", str(p)], check=True)
            if p.exists():
                tiles.append((t, Image.open(p).convert("RGB")))
    if not tiles:
        sys.exit("no frames extracted")
    tw, th = tiles[0][1].size
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * tw, rows * th), "black")
    draw, f = ImageDraw.Draw(sheet), font(max(14, tw // 22))
    for i, (t, im) in enumerate(tiles):
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(im, (x, y))
        label = f"{int(t // 60)}:{t % 60:05.2f}"
        bb = draw.textbbox((0, 0), label, font=f)
        draw.rectangle([x + 4, y + 4, x + 12 + bb[2], y + 10 + bb[3]], fill=(0, 0, 0))
        draw.text((x + 8, y + 6), label, fill=LABEL, font=f)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out)

if __name__ == "__main__":
    main()
