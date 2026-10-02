# 04 · promo — OpenVideoHarness intro film v5 (a galaxy-of-films opening, then one continuous take)


[`media/final.mp4`](media/final.mp4) · 1920×1080 · 30 fps · **150.5 s (4515 frames)** · −14 LUFS · poster [`media/poster.png`](media/poster.png) · contact sheet [`media/sheet.jpg`](media/sheet.jpg) · 中文：[README.zh-CN.md](README.zh-CN.md)

Made at the studio effort level. The first 15.8 s are path-traced in Blender, driven by code; HyperFrames and Three.js take over from there. Every number on screen is copied from the repo; the sources are in [NOTES.md](NOTES.md). The previous version (v3, 81 s) is in [v3/](v3/).

## Watch: eight 1080p chapters

Each chapter plays here with sound (1080p, ≤ 10 MB each: GitHub's limit for an inline video). The single file is [`media/final.mp4`](media/final.mp4).

**1 · The galaxy opening** (0–19 s)

https://github.com/user-attachments/assets/9d305423-0e5b-4276-a347-17a072993b6f

**2 · The request, the router, the nine types** (19–42.5 s)

https://github.com/user-attachments/assets/e8b2244e-ca6b-4f2a-957e-f1df0cf15924

**3 · Docs, tools and engines** (42.5–57 s)

https://github.com/user-attachments/assets/97229621-c60c-4977-93f8-bb193f982fdf

**4 · How it works: the human gates** (57–68 s)

https://github.com/user-attachments/assets/a7e26949-b99b-4bcb-a491-265d77f42354

**5 · The self-review loop and the final cut** (68–87.5 s)

https://github.com/user-attachments/assets/bc9ec77a-a3a8-463e-a622-9f6d6ae8fa4d

**6 · Styles, sound, ready to run, cases** (87.5–111.5 s)

https://github.com/user-attachments/assets/1300a17c-579e-4241-9fbd-c766f197c572

**7 · The proof hall: four real films** (111.5–133 s)

https://github.com/user-attachments/assets/d65a9393-2cb4-497c-8341-97ccb5b80d68

**8 · This film, too; the title** (133–150.5 s)

https://github.com/user-attachments/assets/d0040464-bd4a-43c8-83cd-fe0c9e4119bf

## What was asked

- Gate ① (2026-10-01): the opening was "OK, but not stunning enough, the effects aren't good, it isn't continuous, and the waterfall looks like the same film over and over. Better many different films; glass, cosmos, a starry sky; hook people from the first frame, make them dizzy."
- After the WebGL look-dev (10-02): "a bit of a cheap-effects feel… could the films be shown as a galaxy, as stars? Or use Blender? Hollywood blockbuster quality."
- After the first Blender version (10-02): "some jitter in places, a few spots early on aren't continuous… keep Blender for the first 15 s and render normally at 1080p from 15 s on… just make the final version."

The exact words (in Chinese), every gate's decision and the stand-in reviews are in [REVIEW.md](REVIEW.md); what the agent decided on its own, and why, is in [DECISIONS.md](DECISIONS.md).

## What it shows

The concept: **every star is a film.** There are so many AI video tools that they form a galaxy; it collapses, a two-dimensional foil flattens it, and a harness sorts it into a grid and one line of request: not more tools, know-how.

| Time | Picture | Engine |
|---|---|---|
| 0–4.2 s | The Earth inside one glass card; the camera pulls back fast, films all around, and the card turns out to be one star of a galaxy. "So many AI video tools." | Blender |
| 4.2–8.0 s | The galaxy spins faster and faster while the camera spirals down onto it, a veil of films swept past the lens | Blender |
| 8.0 s | The galaxy collapses into a supernova: a shock ring, a gas shell with red and teal filaments, films flung outward (the film's one white flash) | Blender |
| 9.0–10.4 s | The two-dimensional foil: a ring of light sweeps the plane and flattens the debris into a sea of films | Blender |
| 10.4–13.8 s | "What's missing?" | Blender |
| 14.0–18.8 s | An amber scan sorts the films into a grid that runs to the horizon; "OpenVideoHarness · Not more tools. Know-how." | Blender → WebGL from 15.4 s |
| 18.6–29.0 s | The rows collapse into lines of text; a request is typed into a terminal ("Make a vertical science short: why does a low-orbit satellite's signal change pitch?", the one showcase 02 answers); Enter, and the camera dives in | WebGL + DOM |
| 29.0–56.75 s | Routing: the request → Claude Code / Codex → the CLAUDE.md router → 9 video types, where the request's own (02, science shorts) lights up and the rest dim → playbook, templates, styles, bin/vh → engines, references → projects/ | Three.js |
| 56.75–87.5 s | The workflow on that request: three human gates, each a door made of what is reviewed (02's outline, storyboard, draft sheet); the self-review loop (a frame of 02 turns red on each of three fails, then all pass); the final cut, where 02 plays, + LESSONS.md | Three.js |
| 87.5–106.25 s | A wall of the 31 style samples · sound end to end · ready to run | Three.js |
| 106.25–111.5 s | 13 case studies + 389 community videos | Three.js |
| 111.5–133.25 s | The screening hall: the real films of showcase 01, 03, 02 and 00 | Three.js |
| 133.25–142.25 s | This film, too · even the soundtrack is code | Three.js |
| 142.25–150.5 s | Title, the install command, the GitHub address | Three.js |

Small frames of the opening's films keep drifting past in the body's world, so "every star is a film" runs from the first frame to the last.

## How it was made

- **Opening (0–15.8 s): Blender 5.2, Cycles on Metal.** [`blender/galaxy.py`](blender/galaxy.py) computes, with numpy, every frame's positions for 1.18 million stars, 16,000 "film stars" that turn into glass cards near the camera and 260 cards in the veil, writes them into meshes and renders. Motion blur comes from a `velocity` attribute on every point and from per-frame camera keyframes. The arms' glow, the dust lanes and the supernova's gas are volume shaders; [`blender/nodexpr.py`](blender/nodexpr.py) compiles math expressions into shader nodes. 1080p, 64 samples (96 in the close-up), no denoiser: 475 frames took 1 h 28 min on an M3 Max. Blender runs in a sandbox (no network, writes only to its output folder, no inherited environment: [`tools/bl.sh`](tools/bl.sh)), in resumable chunks ([`tools/bl_render.sh`](tools/bl_render.sh)).
- **Hand-over (15.0–29 s): WebGL.** [`tools/export_state.py`](tools/export_state.py) exports, from the same `galaxy.py` and without starting Blender, every card's grid slot and film and the camera for every frame; [`js/grid.js`](js/grid.js) redraws the same cards through the same camera, and the two renders dissolve into each other at 15.0–15.6 s. Type and terminal are DOM ([`js/open-overlay.js`](js/open-overlay.js)), untouched by any post effect.
- **Body (from 29 s): v3's one-take world** ([`js/main.js`](js/main.js), [`js/arch.js`](js/arch.js), [`js/pipeline.js`](js/pipeline.js), [`js/features.js`](js/features.js)). Changes from v3: 80 BPM instead of 90; and after the third and fourth reviews, 26 holds stretched so every read meets the checklist's reading-time floor ([`js/tmap.js`](js/tmap.js): the story is written on the old 87.5 s timeline and played through this map, while the drifting films, sparks and hand-held drift keep real time; [`tools/retime.py`](tools/retime.py) moves the score's bars and events and the SFX by the same map); the counts brought up to date (9 types, 13 playbook docs, 11 templates, 31 styles, 30 reference repos, 13 case studies, 21 SFX, 102 instruments); the "taste written down as numbers" panel replaced by a wall of the 31 style samples; films drifting beside the path; darker plates behind labels so the conduits pass behind the type; no timecode HUD.
- **Films: 109 sources.** 28 are shaders (nebulae, a black hole, glass, aurora, sea…, [`opening/films.js`](opening/films.js)), 41 are cut from this repo's style samples and showcase films ([`tools/film_atlas.py`](tools/film_atlas.py)), and 40 are AI stills (`gemini-3.1-flash-image`, 16:9 at 512 px, about $1.80; images and prompts in [`assets/ai/`](assets/ai/), [`tools/gen_images.py`](tools/gen_images.py)) given a slow push so they read as playing. Fictional people and places only, no brands or logos.
- **Sound.** The opening uses the gate-① score sketch (120 BPM, motif B: F# A B rising and left hanging in the question); its bar 11 plays four times for the terminal's hold; from 29 s the v3 cinematic score ([`audio/score.json`](audio/score.json), now 80 BPM, D minor, 20 bars lengthened for the holds, each added stretch a held breath with the drums out) takes over from its bar 10. 124 SFX events land on picture events (the opening's are the first 39 in [`audio/events.json`](audio/events.json)). `bin/vh mix profile=promo` to −14 LUFS; `bin/vh qa` passes.

## Checks

- `bin/vh check`: no black, frozen or silent stretch; yuv420p, limited range, BT.709 with all four colour tags.
- One full-screen white flash in the whole film (the supernova at 8.0 s).
- Camera continuity, measured: a frame-difference curve over the 475 Blender frames (smooth rises and falls; the only jumps are the supernova and one card sweeping past the lens at 5.1 s, both designed), and over the whole film after every re-timing (no stepping in the slowed holds; the remaining jumps are whips, power-ons and the cuts inside the proof hall's films).
- Blender determinism: frames 100 and 300 rendered again in a fresh process, PSNR 71.3 dB and 47.3 dB against the sequence (the floor is 45 dB).
- Audio (`bin/vh qa`): no digital silence, dropouts or pumping; 62 of 62 cues within one frame (median 5.1 ms); −14.0 LUFS, −1.65 dBTP. Click warnings: see below.
- Reading time: measured from frames by the reviewers against the checklist's formula, per language; the holds were stretched after rounds 3, 4 and 5 (round 5's last fixes were not re-measured).

## Independent review

You authorised skipping gates ② and ③ ("just make the final version"), so fresh-context reviewers stood in, against the 20 checks and the 8 scores of `templates/TASTE_CHECKLIST.md`:

| Round | Cut | concept | hook | desktop read | motion | variety | finish | accuracy | sync |
|---|---|---|---|---|---|---|---|---|---|
| 1 | draft 2 (the first Blender plate) | 6 | 7 | 5 | 6 | 6 | 5 | 7 | 7 |
| 2 | draft 3, 87.5 s | 6 | 7 | 6 | 7 | 8 | 5 | 7 | 7 |
| 3 | final plate, 87.5 s | 7 | 8 | 6 | 7 | 7 | 6 | 7 | 8 |
| 4 | 130 s (21 holds stretched) | 8 | 7 | 8 | 7 | 7 | 7 | 9 | 8 |
| 5 | 147.5 s (26 holds) | 7 | 7 | 8 | 8 | 6 | 7 | 7 | 7 |

What each round changed is in [NOTES.md](NOTES.md). Round 5's fixes are in this cut and were not reviewed again: you asked to submit after that round. The studio bar (all eight at 8 or more) was not reached; what is left is listed under "Known imperfections". The biggest change came from round 5: the request typed at the start now runs through the body (its type lights up among the nine, the gates show its outline, storyboard and draft, the self-review loop fails three of its frames, and the final cut plays it).

## Reproduce

```bash
cd showcase/04-intro-film
npm ci && bash tools/make_clips.sh                                   # HyperFrames, three; proxies of showcase 00–03 → assets/clips/
uv run --no-project --with pillow python tools/film_atlas.py         # 41 cuts of this repo's films → assets/films.jpg
uv run --no-project --with pillow python tools/ai_atlas.py           # the 40 AI stills → assets/films-ai.jpg (and the small atlases)
bash tools/opening_export.sh                                         # the shader films → assets/films-proc.png, the opening film → assets/hero-earth.png
tools/bl_render.sh 0 474 final2                                      # the Blender opening, 1080p, about 1 h 28 min
uv run --no-project --with numpy python tools/export_state.py       # cards and camera → assets/state.json
uv run --no-project --with pillow python tools/request_tex.py ../02-short-leo-doppler   # the gates' doors and the loop: 02's storyboard, draft sheet, frames
bash tools/deliver.sh                                                # plate, HyperFrames render, audio (tools/build_audio.sh), QA, encodes, poster, sheet
```

The AI stills can't be regenerated byte for byte; `assets/ai/` holds the 40 that were used. The film is written on the old 87.5 s timeline and plays through [`js/tmap.js`](js/tmap.js); after changing that map, run `python3 tools/retime.py` (score, SFX, the footage windows) and rebuild the audio. `tools/self_sheets.sh <draft.mp4>` bakes this film's own frames into the wall behind "This film, too." (render a draft first, then the final).

## Known imperfections

- **Not every score reached 8.** The weakest is variety (6): from 29 s the stations share one grammar (glide in, hold, labels, whip out) in one amber corridor.
- **150.5 s is long for an intro.** The reading-time floor made it grow from 87.5 s; a shorter cut would need fewer stations, not faster ones.
- **Click warnings in the music.** `bin/vh qa` flags about 190 sharp edges in the score stem; they come from the v3 score's gated saw ostinato and stand out more in the held breaths, where the drums drop out. Not checked by ear.
- **The 8.0 s supernova hit** is mostly below 150 Hz, so it is weak on laptop speakers; a whip layer carries its attack.
- **The terminal's hold** repeats one bar of the opening sketch three times.
- **Re-exporting the shader atlas** (`tools/opening_export.sh`) gives a slightly different row 27 (the Earth film): its shader changed after the atlas the Blender render used was exported (the other 27 rows are pixel-identical).
- **Lossless determinism** was measured for the Blender plate, not for this cut's HyperFrames body.
