# LESSONS

## M+ 好用的做法
- Build a `LOOPS.props` model sheet for every new prop before using it in a shot — scene: the movie camera + leaf — effect: caught "the leaf reads as a star" in 5 s, before any shot was built around it.
- Put the review crops on WORLD points (`--crop-at=x,y,w,h`) for moving shots — scene: B, Clawd moving with a panning camera — effect: one command shows the face at every key time.
- Held props: compute the prop's world position by mirroring clawd()'s transform (`bodyPt` / `camPt` helpers) — scene: aiming the camera at the leaf, pushing into the lens — effect: the aim tracks the leaf with a 0.12 s lag (free follow-through), and the lens push starts exactly at the lens.
- A background camera layer (sky + hills) at 35–40 % of the foreground camera — scene: A reveal and B pan — effect: cheap parallax/depth; two sequential camBegin/camEnd pairs are fine.
- Give the hero object the only saturated colour of its hue family, and pick perches and backgrounds against it — scene: gold leaf, rust crown, blue-green squash, sage hill — effect: the leaf is findable at 55 px in a wide frame.
- Repeat a gag faster the second time — scene: gust #2 is 0.45 s vs 0.4 s + anticipation the first time — effect: the audience expects it, so it reads.

## M− 踩过的坑
- Clawd's side view has ONE eye near the leading edge; any prop held at the arm tip at eye level covers it — cause: arm pivot at (1.6u, −4.5u), eye at (2.73u, −6u) — fix: hold the prop ~0.85u ahead of the eye, cap its tilt, and let the body lean (`rot`) take the rest of the aim.
- Clawd's terracotta disappears against warm orange hills and pumpkins — cause: same hue and value — fix: sage/olive mid hills and a blue-green hero squash; keep orange for small, far things.
- Overlapping `paint()` shapes: the ink outlines of earlier shapes show through later washes (p5.brush defers strokes); `flushBrush()` between them did not help — fix: one silhouette + painted rib lines ("one shape, one outline").
- A symmetric 5-lobed maple leaf reads as a star at small size — fix: broader, rounder lobes and a longer curved stem.
- The first pass of every shot was framed too wide (u 24–26, leaf r 34): generated staging defaults to "establishing shot" — fix: start medium (u ≥ 30) and push close-ups to u ≥ 80.
- `--crop-at` expressions must be page globals; values inside the scene IIFE (e.g. a pose function) aren't reachable — fix: fixed world coordinates, or expose a global.
- Running several `render.mjs` processes in parallel once left one hung with no output (0.2 s CPU after an hour) — fix: rerun it alone. When batching, watch for a missing output file.
- A "notice" beat (eyes roll up) got 7 frames on the first pass — fix: give the notice its own emotion key (surprised take) with ≥ 12 frames before the payoff emotion.

## 可用命令
```bash
bin/vh new handdrawn <slug>                                          # from repo root
node render.mjs --loop=props --sheet=0.3 --cols=1 --w=1280 --out=out/check/props.jpg   # prop model sheet
node render.mjs --sheet=4.05,4.5,... --cols=5 --w=384 --out=out/check/B_sheet.jpg
node render.mjs --strip=2.35:3.2 --cols=7 --w=270 --out=out/check/strip.jpg
node render.mjs --sheet=5.3,6.35 --crop-at=900,770,640,460 --w=400 --out=out/check/face.jpg
rm -rf out/frames && node render.mjs --frames --workers=4 && node render.mjs --encode --out=out/final.mp4   # 57 s for 288 frames
bin/vh check <mp4>; bin/vh sheet <mp4> 6 2; bin/vh gif <mp4> 560 12      # 640/12 gave 6.3 MB, 560/12 gave 4.9 MB
```
