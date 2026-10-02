"""The request's own artifacts for the gates (the film walks one request through the harness: showcase 02, the vertical
science short on Doppler shift). Built from showcase/02's final film, contact sheet and STORYBOARD.md:
  assets/tex/02-storyboard.png  gate ② door: its eight shots (S1–S7) as 9:16 keyframes with their captions
  assets/tex/02-draft-sheet.png gate ③ door: the top of its contact sheet, cropped to 16:9
  assets/tex/02-loop.png        the self-review loop: nine frames, 3×3 (three of them go red on the fails)
usage (from the film folder): uv run --no-project --with pillow python tools/request_tex.py <showcase/02 folder>"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S2 = Path(sys.argv[1]); OUT = Path(__file__).resolve().parents[1] / "assets/tex"
FILM = S2 / "media/final.mp4"
ZH = next((f for f in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/STHeiti Medium.ttc"] if Path(f).exists()), None)
MONO = "/System/Library/Fonts/SFNSMono.ttf"
font = lambda p, n: ImageFont.truetype(p, n) if p and Path(p).exists() else ImageFont.load_default()


def frame(t, tmp):
    p = Path(tmp) / f"{t:.2f}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(FILM), "-frames:v", "1", str(p)], check=True)
    return Image.open(p).convert("RGB")


# shot, the middle of its window, its caption (STORYBOARD.md "字幕（= 旁白）", verbatim, shortened at the first ；)
SHOTS = [("S1", 1.8, "卫星信号会变调"), ("S2", 4.7, "低轨卫星，飞得极快"), ("S3", 7.7, "靠近：波变密，频率升高"), ("S4", 10.2, "正头顶：频移归零"),
         ("S5", 12.9, "远离：波变疏，频率降低"), ("S6a", 16.1, "2 GHz：接近 ±50 kHz"), ("S6b", 19.0, "20 GHz：再大 10 倍"), ("S7", 23.6, "轨道已知，能提前算出")]
with tempfile.TemporaryDirectory() as tmp:
    sb = Image.new("RGB", (1600, 900), (13, 13, 16)); d = ImageDraw.Draw(sb)
    d.text((48, 26), "STORYBOARD.md · 02 低轨卫星的多普勒 · 分镜", font=font(ZH, 34), fill=(139, 139, 148))
    fw, fh = 170, 302
    for i, (s, t, cap) in enumerate(SHOTS):
        x = 48 + (i % 4) * 384; y = 92 + (i // 4) * 404
        sb.paste(frame(t, tmp).resize((fw, fh), Image.LANCZOS), (x, y)); d.rectangle((x - 1, y - 1, x + fw, y + fh), outline=(74, 74, 82))
        d.text((x + fw + 18, y + 4), s, font=font(MONO, 34), fill=(255, 178, 36))
        cl = [cap[k:k + 6] for k in range(0, len(cap), 6)]       # six characters a line: clear of the next frame
        for j, ln in enumerate(cl):
            d.text((x + fw + 18, y + 58 + j * 36), ln, font=font(ZH, 25), fill=(214, 214, 220))
    sb.save(OUT / "02-storyboard.png")
    loop = Image.new("RGB", (3 * 180 + 4 * 12, 3 * 320 + 4 * 12), (13, 13, 16))
    for i in range(9):
        t = 1.0 + i * 2.8
        loop.paste(frame(t, tmp).resize((180, 320), Image.LANCZOS), (12 + (i % 3) * 192, 12 + (i // 3) * 332))
    loop.save(OUT / "02-loop.png")
sh = Image.open(S2 / "media/sheet.png").convert("RGB"); w = sh.width
sh.crop((0, 0, w, round(w * 9 / 16))).resize((1600, 900), Image.LANCZOS).save(OUT / "02-draft-sheet.png")
print("02-storyboard.png 02-draft-sheet.png 02-loop.png")
