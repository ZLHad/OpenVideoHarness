"""Storyboard keyframe preview (v3 Phase B): one labelled frame per read, 5 columns, from a draft render.
usage: uv run -q --with pillow python tools/storyboard_v3.py out/draftN.mp4 [out/check/storyboard-v3.png]"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
V = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else "out/check/storyboard-v3.png"
K0 = [  # (t on the plain 4/4 grid, section, what the viewer reads); bar 11 is 6/4, so times after 29.4 s move +1.333 s
    (1.6, "S1 hook", "frame = f(t)"), (4.2, "S1 hook", "EVERY FRAME"), (6.8, "S1 hook", "IS A FUNCTION OF TIME"),
    (9.8, "S2 program", "request card"), (12.2, "S2 program", "doesn't paint pixels / writes the program"), (14.9, "S2 program", "One sentence in. A film out."),
    (17.6, "S3 problem", "Stunning, once. · FAIL ×3"), (20.2, "S3 problem", "Dependable? Not yet."), (22.8, "S4 braam", "OpenVideoHarness"),
    (25.9, "S5 architecture", "request → agent → router"), (29.4, "S5 architecture", "video-types/ · 8 workflows (held)"), (31.6, "S5 architecture", "playbook · templates · cases · bin/vh"),
    (33.3, "S5 architecture", "engines · references"), (34.1, "S5 → S6", "projects/ portal"), (36.2, "S6 workflow", "How it works"),
    (38.0, "S6 workflow", "human review ① approved"), (42.2, "S6 workflow", "loop · fail ×3"), (44.3, "S6 workflow", "Review every scene … until it passes."),
    (46.3, "S6 workflow", "human review ③ approved"), (47.5, "S6 workflow", "Final cut + LESSONS.md (hold)"), (49.9, "S7 features", "Taste written down as numbers."),
    (52.6, "S7 features", "Sound, end to end."), (55.3, "S7 features", "Ready to run. (install)"), (57.8, "S8 cases", "11 case studies + 389 videos"),
    (60.0, "S9 proof", "Made by an agent …"), (62.3, "S9 proof", "01 hand-drawn"), (66.3, "S9 proof", "02 vertical science short"),
    (70.8, "S10 reveal", "This film, too."), (73.9, "S10 reveal", "Even the soundtrack is code."), (79.2, "S11 title", "title · command · GitHub URL"),
]
K = [(t + (4 / 3 if t > 29.4 else 0), s, w) for t, s, w in K0]
W, H, C = 480, 270, 5
R = (len(K) + C - 1) // C
f = lambda p, s: ImageFont.truetype(p, s) if os.path.exists(p) else ImageFont.load_default()
mono, sans = f("/System/Library/Fonts/SFNSMono.ttf", 17), f("/System/Library/Fonts/SFNS.ttf", 19)
sheet = Image.new("RGB", (C * W + (C + 1) * 10, R * (H + 52) + 10), (14, 14, 16)); d = ImageDraw.Draw(sheet)
tmp = tempfile.mkdtemp()
for i, (t, sec, what) in enumerate(K):
    p = os.path.join(tmp, f"k{i:02d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", V, "-frames:v", "1", "-vf", f"scale={W}:{H}", "-update", "1", p], check=True)
    x, y = 10 + (i % C) * (W + 10), 10 + (i // C) * (H + 52)
    sheet.paste(Image.open(p), (x, y))
    d.text((x + 2, y + H + 5), f"{t:5.1f}s  {sec}", fill=(255, 178, 36), font=mono)
    d.text((x + 2, y + H + 26), what, fill=(210, 210, 216), font=sans)
os.makedirs(os.path.dirname(OUT), exist_ok=True); sheet.save(OUT); print(OUT, sheet.size)
