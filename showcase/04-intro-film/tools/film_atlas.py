"""Build look/assets/films.jpg: real footage for the opening's waterfall cards.

Every film is one row of 16 tiles (256x144, 8 fps, 2 s loop) cut from this repo's own films:
the 28 style swatches and showcases 00-04 (all MIT, made in this repo). The procedural films
(cosmos, glass, landscapes) are rendered in the page itself, see look/js/films.js.

usage (from the project root):
  uv run --no-project --with pillow python tools/look/film_atlas.py
"""
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]          # the project
REPO = ROOT.parents[1]
OUT = ROOT / "assets"
TW, TH, NF, FPS = 256, 144, 16, 8

# (name, file, start s, crop as fractions of the frame: x, y, w, h)
SW_CROP = (0.15, 0.30, 0.70, 0.70)                 # swatches: lower centre, so the shared title line is mostly out
films = []
for d in sorted((REPO / "styles").iterdir()):
    f = d / "media" / "swatch.mp4"
    if f.exists():
        films.append((d.name, f, 2.0, SW_CROP))
SC = REPO / "showcase"
FULL = (0.0, 0.0, 1.0, 1.0)
films += [
    ("00-launch-a", SC / "00-promo-launch-film/media/final.mp4", 3.0, FULL),
    ("00-launch-b", SC / "00-promo-launch-film/media/final.mp4", 12.5, FULL),
    ("01-leaf-a", SC / "01-handdrawn-clawd-leaf/media/final.mp4", 2.0, FULL),
    ("01-leaf-b", SC / "01-handdrawn-clawd-leaf/media/final.mp4", 8.0, FULL),
    ("02-doppler-a", SC / "02-short-leo-doppler/media/final.mp4", 5.0, (0.0, 0.34, 1.0, 0.316)),
    ("02-doppler-b", SC / "02-short-leo-doppler/media/final.mp4", 15.0, (0.0, 0.34, 1.0, 0.316)),
    ("03-fourier-a", SC / "03-math-fourier/media/final.mp4", 6.0, FULL),
    ("03-fourier-b", SC / "03-math-fourier/media/final.mp4", 18.0, FULL),
    ("04-intro-a", SC / "04-intro-film/media/final.mp4", 5.0, FULL),
    ("04-intro-b", SC / "04-intro-film/media/final.mp4", 21.0, FULL),
    ("04-intro-c", SC / "04-intro-film/media/final.mp4", 38.0, FULL),
    ("04-intro-d", SC / "04-intro-film/media/final.mp4", 55.0, FULL),
    ("04-intro-e", SC / "04-intro-film/media/final.mp4", 70.0, FULL),
]


def probe(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(f)], capture_output=True, text=True, check=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


atlas = Image.new("RGB", (TW * NF, TH * len(films)), (8, 9, 10))
with tempfile.TemporaryDirectory() as tmp:
    for row, (name, f, t0, (cx, cy, cw, ch)) in enumerate(films):
        w, h = probe(f)
        x, y, ww, hh = int(cx * w), int(cy * h), int(cw * w), int(ch * h)
        pat = Path(tmp) / f"{row:02d}_%02d.png"
        vf = f"crop={ww}:{hh}:{x}:{y},fps={FPS},scale={TW}:{TH}:force_original_aspect_ratio=increase:flags=lanczos,crop={TW}:{TH}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-i", str(f), "-vf", vf, "-frames:v", str(NF), str(pat)], check=True)
        for k in range(NF):
            p = Path(tmp) / f"{row:02d}_{k + 1:02d}.png"
            if not p.exists():                       # short source: hold the last frame
                p = sorted(Path(tmp).glob(f"{row:02d}_*.png"))[-1]
            atlas.paste(Image.open(p).convert("RGB"), (k * TW, row * TH))
OUT.mkdir(parents=True, exist_ok=True)
atlas.save(OUT / "films.jpg", quality=86, optimize=True)
(OUT / "films.json").write_text(json.dumps({"tile": [TW, TH], "frames": NF, "fps": FPS,
                                            "films": [n for n, *_ in films]}, indent=1))
print(f"{len(films)} films → {OUT / 'films.jpg'} ({atlas.size[0]}x{atlas.size[1]})")
