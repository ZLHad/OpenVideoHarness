"""Contact sheet with a burned-in timestamp on every tile.

usage: uv run --with pillow python tools/sheet.py <video> <out.png> [cols=6] [fps=1] [width=480]
       label colour via env VH_SHEET_LABEL (default #ffdc00)
Frames are sampled at t = (k + 0.5) / fps so each tile sits mid-interval; the label is that exact time.
A time past the last frame is clamped to it, so a clip shorter than one interval (0.4 s at fps 1) still gets a tile.
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

def main():
    video, out = sys.argv[1], sys.argv[2]
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
