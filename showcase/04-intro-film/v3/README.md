# 04 · promo — OpenVideoHarness intro film (one-take 3D, code-composed score)

> This is the v3 film (2026-09-29), kept for the record. The current intro film is [v5](../README.md); its body is this film's world, updated and slowed from 90 to 80 BPM. The v5 files replaced v3's in the film folder; v3's own source (`js/`, `tools/`, `audio/` below) is at commit 7057c74: `git checkout 7057c74 -- showcase/04-intro-film` (the installer's clone has only the newest commit, so fetch it there first: `git fetch --depth 1 origin 7057c74725c42b38fe545d85916cab11fe78bed4`).

![OpenVideoHarness intro film](preview.gif)

[final.mp4](final.mp4) (with sound and zh/en subtitle tracks) · poster: [poster.png](poster.png) · contact sheet: [sheet.png](sheet.png) · 中文说明：[README.zh-CN.md](README.zh-CN.md)

| | |
|---|---|
| Type / route | `promo` → `video-types/03-product-promo.md`, with the one-take 3D notes in `playbook/08-vfx-and-motion-sources.md` |
| Engine | HyperFrames **0.8.82** + Three.js **0.181.2**, both pinned in `package.json` and loaded from `node_modules` (no CDN at render time) |
| Output | 81.333 s, 1920×1080, 30 fps, 2440 frames, stereo music and SFX at −14.0 LUFS, zh/en soft subtitles |
| Sound | score composed in code (`audio/score.json` + `audio/score_engine.py`, 90 BPM, D minor, 30 bars, bar 11 in 6/4); 97 SFX events |
| Render time (M3 Max) | draft ≈ 53 s; `--quality high` master 2 min 0 s; the whole delivery script ≈ 6 min |
| Files | `final.mp4` is the 20.8 MB web encode (two-pass 1900 kbps). The CRF 16 master (266 MB) is not in the repo; `tools/deliver.sh` rebuilds it |
| Iterations | v1 outline rejected at gate ① → v2 (8 drafts, 2 fresh-context reviewers) → user feedback → look-dev in 3 intensities → v3 (20 drafts, 2 more reviewers) |

## What was asked, and what changed

The first brief was a 60 s flat-UI promo. At gate ① the user asked instead for **"一镜到底 动画动效 音乐动态字等风格 叙事感 科幻感大片感"**: a single continuous shot, kinetic type on music, a narrative arc, sci-fi blockbuster scale. The user then authorized skipping gates ② and ③ for an overnight run ("你自己做好 早上9点我希望能看到成片"), recorded verbatim in [REVIEW.md](REVIEW.md).

The v2 film (69 s) came back with two notes:

- **"音乐部分感觉部分地方卡顿或者消失"**: the music stutters or disappears. The cause was a design error, not an encoding one. Each review gate "stopped" the score with 0.6 s of digital silence while the camera froze, which reads exactly like a stalled player. v3 keeps a bed under every pause and never lets the camera go dead-still. This became a rule for the whole harness: `TASTE_CHECKLIST` #18 and `playbook/04-audio.md`.
- **"不够炫酷"** (not cool enough) and **"介绍片是本产品的宣传片…架构、特色、案例、工作流流程图之类的可以做成炫酷动效放入"** (it's a product promo, so show the architecture, features, cases and workflow). Before rebuilding, we rendered the same 22 s segment at three FX intensities: A restrained, B blockbuster, C cyber-glitch. We picked B and rebuilt the film around the product.

## What's on screen

| t (s) | Section | Source |
|---|---|---|
| 0–8.0 | Hook: a spark stretches into the time axis, a wall of frames renders: `frame = f(t)` | — |
| 8.0–16.0 | A real request card (showcase 02), then a canyon of its real `draw(t)` code: "Claude Opus 5.5 doesn't paint pixels. It writes the program." | `showcase/02-short-leo-doppler/` |
| 16.0–21.3 | "Stunning, once. Dependable? Not yet." Three bad frames get stamped FAIL | checklist items #11 / #10 / #19 |
| 21.3–24.0 | Title reveal on the one braam | — |
| 24.0–36.0 | **Architecture**: the node network from `docs/assets/architecture.*.svg`: request → agent → router → 8 video types → playbook / templates / cases / `bin/vh` → engines / references → dive through `projects/` | README, CLAUDE.md |
| 36.0–49.3 | **Workflow**: the README flowchart as a powered 3D circuit; gates ① ② ③ approve; the self-review loop fails three times, then passes | README "How it works", `templates/REVIEW.md` |
| 49.3–57.3 | **Features**: taste as numbers, sound end to end (the waveform is this film's score), the one-line install | README, `bin/vh` |
| 57.3–60.0 | **Cases**: 389 points gather into a disc; 11 stars form a constellation | `cases/` |
| 60.0–70.7 | Screening hall: showcase 01, 03, 02, 00 on floating screens | `showcase/*/media/final.mp4` |
| 70.7–76.0 | "This film, too. Even the soundtrack is code." Four real lines of the score engine light up as their instruments enter | `audio/score_engine.py` |
| 76.0–81.3 | Title, tagline, `bin/vh new <type> <slug>`, GitHub URL, typed on the score's 16ths | — |

Every number and label on screen is copied from the repo; the source table is in [NOTES.md](NOTES.md).

## How it's built

- **One world, one camera.** `js/main.js` holds the time axis, the camera (a Hermite spline over real time), the screening hall and the reveal; `js/arch.js`, `js/pipeline.js` and `js/features.js` hold the three product sections; `js/fx.js` holds the FX presets. Every frame is `renderAt(t)`.
- **FX as a preset.** The HyperFrames variable `fx` switches A / B / C, so changing intensity costs one re-render. Each effect has a written reason (NOTES.md): grading, bloom, anamorphic flares, velocity motion blur that backs off while must-read text is on screen, shake and chromatic bursts on hits, a depth particle field, decode-in type.
- **One grid for picture and sound.** At 90 BPM and 30 fps a beat is 20 frames. Picture, score, SFX and captions all read time from one `bar(k, beat)`. Making bar 11 a 6/4 bar meant one change in `score.json` and one in `bar()`.

## Checks

| Check | Result |
|---|---|
| Loudness | −14.0 LUFS, LRA 8.2 LU, true peak −1.7 dBTP |
| Cue check on the final mix | 180/180 within 1 frame (median 10.6 ms) |
| Silence, dropouts, pumping (`bin/vh qa`) | 0 / 0 / 0; digital silence only in the first 0.09 s and the last 0.07 s |
| Click warnings | 136, all traced to designed onsets: the sawtooth ostinato's note heads, and one glitch SFX that is hard-gated by design. The first "0 clicks" came from a detector that could never fire; see `playbook/02-verification.md` |
| Frozen / empty frames | none; every frame compared with frame 0 |
| Determinism | lossless PNG, 4 vs 3 workers: 2040/2440 frames bit-identical, the rest ≥ 80.7 dB |
| Offline render | local three.js vs CDN three.js: bit-identical at 4 time points |

## Known imperfections

- The architecture section flashes its secondary labels; the headings and numbers land, the small lines read as texture.
- The screening hall runs about 10.7 s, which one reviewer found a little long.
- Nobody has *listened* to the score except the user; it was judged by measurement.

## Reproduce

```bash
cd showcase/04-intro-film
npm i                                                   # hyperframes 0.8.82 + three 0.181.2, exact
bash tools/make_clips.sh                                # 30 fps proxies of showcase 00–03 → assets/clips/
uv run -q --with numpy --with scipy python audio/score_engine.py audio/score.json audio/music.wav
export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1
mkdir -p out/check && npx hyperframes render --quality draft --output out/draft.mp4
bash tools/deliver.sh out/draft.mp4                     # self-sheets, master, SFX, mix, mux, web encode, GIF, poster, checks
```

The proxies are re-encoded, so screen frames can differ slightly from `final.mp4`. The built-in `error` SFX was later smoothed in `tools/audio/sfx.py`, so the mix differs slightly at 44.0 s. Everything else is deterministic. All working notes are in Chinese: [NOTES.md](NOTES.md) (decisions, sources, every review round), [LESSONS.md](LESSONS.md), [REVIEW.md](REVIEW.md), [STORYBOARD.md](STORYBOARD.md), [audio/SCORE_NOTES.md](https://github.com/ZLHad/OpenVideoHarness/blob/7057c74/showcase/04-intro-film/audio/SCORE_NOTES.md).
