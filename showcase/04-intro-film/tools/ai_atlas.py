"""Build assets/films-ai.jpg: the AI stills (assets/ai/NN.jpg) as 16-frame films, a slow push or pan on each
(they ping-pong on the cards, so the move goes in and back out), one film per row, 256x144 tiles like the other atlases.
Also writes the 1/4-size atlases the far cards use: films-proc-small.png, films-small.jpg, films-ai-small.jpg.

usage (from the project root): uv run --no-project --with pillow python tools/look/ai_atlas.py
"""
import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "assets"
TW, TH, NF = 256, 144, 16
imgs = sorted((A / "ai").glob("*.jpg"))
atlas = Image.new("RGB", (TW * NF, TH * len(imgs)), (8, 9, 10))
for r, f in enumerate(imgs):
    im = Image.open(f).convert("RGB"); W, H = im.size
    h = (r * 2654435761 % 1000) / 1000.0                       # a fixed per-image choice of move
    ang = h * 2 * math.pi; zoom1 = 1.06 + 0.06 * ((r * 40503 % 1000) / 1000.0)
    for k in range(NF):
        u = k / (NF - 1); z = 1.0 + (zoom1 - 1.0) * (u * u * (3 - 2 * u))
        cw, ch = W / z, W / z * 9 / 16
        if ch > H / z: ch = H / z; cw = ch * 16 / 9
        cx = W / 2 + math.cos(ang) * (W - cw) * 0.5 * u; cy = H / 2 + math.sin(ang) * (H - ch) * 0.5 * u
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        atlas.paste(im.resize((TW, TH), Image.LANCZOS, box=box), (k * TW, r * TH))
atlas.save(A / "films-ai.jpg", quality=90, optimize=True)
(A / "films-ai.json").write_text(json.dumps({"tile": [TW, TH], "frames": NF, "fps": 8, "films": [f.stem for f in imgs]}, indent=1))
for src, dst in (("films-proc.png", "films-proc-small.png"), ("films.jpg", "films-small.jpg"), ("films-ai.jpg", "films-ai-small.jpg")):
    im = Image.open(A / src).convert("RGB")
    im.resize((im.width // 4, im.height // 4), Image.LANCZOS).save(A / dst, **({"quality": 90} if dst.endswith(".jpg") else {"optimize": True}))
print(f"{len(imgs)} AI films → {A / 'films-ai.jpg'} ({atlas.size[0]}x{atlas.size[1]}); small atlases written")
