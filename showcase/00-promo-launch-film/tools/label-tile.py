"""Burn the contact-sheet tile label onto a 960x540 frame so the hi-res overlay in beat 03
matches its tile in `bin/vh sheet` (tools/sheet.py style at 2x; grey = the tile label after the sheet's greyscale filter).
usage: uv run --with pillow python tools/label-tile.py <in.png> <out.png> <seconds>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
src, out, t = sys.argv[1], sys.argv[2], float(sys.argv[3])
im = Image.open(src).convert("RGB")
k = im.width / 480                      # tile scale relative to the 480-px sheet tiles
f = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", int(max(14, 480 // 22) * k)) if Path("/System/Library/Fonts/Menlo.ttc").exists() else ImageFont.load_default()
d = ImageDraw.Draw(im)
label = f"{int(t // 60)}:{t % 60:05.2f}"
bb = d.textbbox((0, 0), label, font=f)
d.rectangle([4 * k, 4 * k, 12 * k + bb[2], 10 * k + bb[3]], fill=(0, 0, 0))
d.text((8 * k, 6 * k), label, fill=(211, 211, 211), font=f)
im.save(out)
print(out)
