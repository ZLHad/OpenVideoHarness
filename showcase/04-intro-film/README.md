# 04 · promo — OpenVideoHarness intro film v5 (a galaxy-of-films opening, then one continuous take)

1920×1080 · 30 fps · **103 s (3090 frames)** · −14 LUFS · the film: [`intro-film-1080p.mp4`](https://github.com/ZLHad/OpenVideoHarness/releases/download/media/intro-film-1080p.mp4) (297 MB, GitHub release) · poster [`media/poster.jpg`](media/poster.jpg) · contact sheet [`media/sheet.jpg`](media/sheet.jpg) · 中文：[README.zh-CN.md](README.zh-CN.md)

Made at the studio effort level. The first 15.8 s are path-traced in Blender, driven by code; HyperFrames and Three.js take over from there. Every number on screen is copied from the repo; the sources are in [NOTES.md](NOTES.md). The previous version (v3, 81 s) is in [v3/](v3/).

## Watch: six 1080p chapters

Each chapter plays here with sound (1080p, under 10 MB each: GitHub's limit for a video in a README). The whole film is one file in the release linked above.

**1 · The galaxy opening and the request** (0–25 s)

https://github.com/user-attachments/assets/48923404-eff1-41cd-b303-82c9ede51c1f

**2 · The router, the nine types, the docs** (25–41.5 s)

https://github.com/user-attachments/assets/841df5f9-837d-4138-ab6a-3ff9a092fb57

**3 · How it works: the gates, the self-review loop, the final cut** (41.5–62.05 s)

https://github.com/user-attachments/assets/dfa4a89e-ab81-4d2a-abab-5ba3eec57fbe

**4 · Styles, sound, ready to run, cases** (62.05–75.25 s)

https://github.com/user-attachments/assets/341c462f-dfc2-4272-84c2-3a68936fd957

**5 · The proof hall: four real films** (75.25–90.5 s)

https://github.com/user-attachments/assets/27cc7042-f160-4f49-8590-3c93661d4377

**6 · This film, too; the title** (90.5–103 s)

https://github.com/user-attachments/assets/a8bf490c-3fae-4d3b-84a4-39d725def0f5

## What was asked

- Gate ① (2026-10-01): the opening was "OK, but not stunning enough, the effects aren't good, it isn't continuous, and the waterfall looks like the same film over and over. Better many different films; glass, cosmos, a starry sky; hook people from the first frame, make them dizzy."
- After the WebGL look-dev (10-02): "a bit of a cheap-effects feel… could the films be shown as a galaxy, as stars? Or use Blender? Hollywood blockbuster quality."
- After the first Blender version (10-02): "some jitter in places, a few spots early on aren't continuous… keep Blender for the first 15 s and render normally at 1080p from 15 s on… just make the final version."
- After the 150.5 s cut (10-04): "after the opening everything is too slow; the pause after each line of text is too long… the earliest version's pacing was right, apart from a few shots that were too fast", and: "not so long, but not a flash either: make it a good experience." On this cut: "the pacing is fine (a few music and sound cues should land with the picture)."

The exact words (in Chinese), every gate's decision and the stand-in reviews are in [REVIEW.md](REVIEW.md); what the agent decided on its own, and why, is in [DECISIONS.md](DECISIONS.md).

## What it shows

The concept: **every star is a film.** There are so many AI video tools that they form a galaxy; it collapses, a two-dimensional foil flattens it, and a harness sorts it into a grid and one line of request: not more tools, know-how.

| Time | Picture | Engine |
|---|---|---|
| 0–4.2 s | The Earth inside one glass card; the camera pulls back fast, films all around, and the card turns out to be one star of a galaxy. "So many AI video tools." | Blender |
| 4.2–8.0 s | The galaxy spins faster and faster while the camera spirals down onto it, a veil of films swept past the lens | Blender |
| 8.0 s | The galaxy collapses and bursts: a shock ring, a gas shell with red and teal filaments, films flung outward (the film's one white flash) | Blender |
| 9.0–10.4 s | The two-dimensional foil: a ring of light sweeps the plane and flattens the debris into a sea of films | Blender |
| 10.4–13.8 s | "What's missing?" | Blender |
| 14.0–18.8 s | An amber scan sorts the films into a grid that runs to the horizon; "OpenVideoHarness · Not more tools. Know-how." | Blender, dissolving into WebGL over 15.0–15.6 s |
| 18.6–25.0 s | The rows collapse into lines of text; a request is typed into a terminal ("Make a vertical science short: why does a low-orbit satellite's signal change pitch?", the one showcase 02 answers); Enter, and the camera dives in | WebGL + DOM |
| 25.0–41.5 s | Routing: the request → Claude Code / Codex → the CLAUDE.md router → 9 video types, where the request's own (02, science shorts) lights up and the rest dim → playbook, templates, styles, bin/vh → engines, references → projects/ | Three.js |
| 41.5–62.05 s | The workflow on that request: three human gates, each a door made of what is reviewed (02's outline, storyboard, draft sheet); the self-review loop (a frame of 02 turns red on each of three fails, then all pass); the final cut, where 02 plays, + LESSONS.md | Three.js |
| 62.05–71.5 s | A wall of the 31 style samples · sound end to end · ready to run | Three.js |
| 71.5–75.25 s | 13 case studies, lit one star at a time + 389 community videos | Three.js |
| 75.25–89.5 s | The screening hall: the real films of showcase 01, 03, 02 and 00 | Three.js |
| 89.5–96.25 s | This film, too · even the soundtrack is code | Three.js |
| 96.25–103 s | Title, the install command, the GitHub address | Three.js |

Small frames of the opening's films keep drifting past in the body's world, so "every star is a film" runs from the first frame to the last.

## How it was made

- **Opening (0–15.8 s): Blender 5.2, Cycles on Metal.** [`blender/galaxy.py`](blender/galaxy.py) computes, with numpy, every frame's positions for 1.18 million stars, 16,000 "film stars" that turn into glass cards near the camera and 260 cards in the veil, writes them into meshes and renders. Motion blur comes from a `velocity` attribute on every point and from per-frame camera keyframes. The arms' glow, the dust lanes and the burst's gas are volume shaders; [`blender/nodexpr.py`](blender/nodexpr.py) compiles math expressions into shader nodes. 1080p, 64 samples (96 in the close-up), no denoiser: 475 frames took 1 h 28 min on an M3 Max. Blender runs in a sandbox (no network, writes only to its output folder, no inherited environment: [`tools/bl.sh`](tools/bl.sh)), in resumable chunks ([`tools/bl_render.sh`](tools/bl_render.sh)).
- **Hand-over (15.0–25 s): WebGL.** [`tools/export_state.py`](tools/export_state.py) exports, from the same `galaxy.py` and without starting Blender, every card's grid slot and film and the camera for every frame; [`js/grid.js`](js/grid.js) redraws the same cards through the same camera, and the two renders dissolve into each other at 15.0–15.6 s. Type and terminal are DOM ([`js/open-overlay.js`](js/open-overlay.js)), untouched by any post effect.
- **Body (from 25 s): v3's one-take world** ([`js/main.js`](js/main.js), [`js/arch.js`](js/arch.js), [`js/pipeline.js`](js/pipeline.js), [`js/features.js`](js/features.js)), at 80 BPM instead of 90, with the counts brought up to date (9 types, 13 playbook docs, 11 templates, 31 styles, 30 reference repos, 13 case studies, 21 SFX, 102 instruments), a wall of the 31 style samples, films drifting beside the path and no timecode HUD.
- **Pacing.** The story is written on an 87.5 s timeline and plays through a time map ([`js/tmap.js`](js/tmap.js)) that slows 15 short holds where a line would otherwise flash by: each line stays long enough to read once in either language (English at about 20 characters a second, Chinese at about 7, plus 0.8 s, at least 1.5 s), then the camera moves on. The drifting films, sparks and hand-held drift keep the film's own clock, so a slowed hold never freezes the world. An earlier cut stretched 26 holds to a stricter reading formula and ran 150.5 s; it felt slow after every line, so this cut went back to the 87.5 s pacing and added only 15.5 s.
- **Films: 109 sources.** 28 are shaders (nebulae, a black hole, glass, aurora, sea…, [`opening/films.js`](opening/films.js)), 41 are cut from this repo's style samples and showcase films ([`tools/film_atlas.py`](tools/film_atlas.py)), and 40 are AI stills (`gemini-3.1-flash-image`, 16:9 at 512 px, about $1.80; images and prompts in [`assets/ai/`](assets/ai/), [`tools/gen_images.py`](tools/gen_images.py)) given a slow push so they read as playing. Fictional people and places only, no brands or logos.
- **Sound.** The opening uses the gate-① score sketch (120 BPM, motif B: F# A B rising and left hanging in the question); its bar 11 plays twice for the terminal's hold. From 25 s the v3 cinematic score ([`audio/score.json`](audio/score.json), 80 BPM, D minor) takes over from its bar 10; [`tools/retime.py`](tools/retime.py) lengthens the 12 bars that hold a stretch by whole beats, and their patterns keep playing, so the music never stops for a read. 124 SFX events land on picture events ([`audio/events.json`](audio/events.json), in film time). A sync check paired every named music accent with the sound effect of the same picture event and moved four that had drifted when the picture changed in earlier rounds: the second pair of directory cards, the 13 case stars (13 celesta notes, one per star; the case-study hold now starts after the 13th star, so the notes stay on them), "This film, too." and the end card's typing. `bin/vh mix profile=promo` to −14 LUFS; [`tools/build_audio.sh`](tools/build_audio.sh) rebuilds it all and runs `bin/vh qa`.

## Checks

- `bin/vh check`: no black, frozen or silent stretch; yuv420p, limited range, BT.709 with all four colour tags.
- One full-screen white flash in the whole film (the burst at 8.0 s).
- Reading time, measured on frames (4–10 fps) for every line the earlier cuts had trouble with: each now holds at least its short-label time from `templates/TASTE_CHECKLIST.md` #5 (the router line about 2.0 s, gate ② about 2.7 s, "pass" about 2.0 s, gate ③ and "Final cut" about 2.3 s, "This film, too." about 1.9 s).
- Sync, measured: every large picture event (the burst, each arrival, the gate passes, the fails, the pass, the title) has a sound within one frame; every named music accent that shares a picture event with a sound effect sits on it (offset 0.00 s), and the 13 celesta notes land on the 13 case stars (0.000 s). The accents with no effect of their own (the sound panel's rows, "This film, too.") were checked against the frames.
- Camera continuity, measured: a frame-difference curve over the 475 Blender frames (smooth rises and falls; the only jumps are the burst and one card sweeping past the lens at 5.1 s, both designed), and over the whole film after every re-timing (no stepping in the slowed holds; the remaining jumps are whips, power-ons and the cuts inside the proof hall's films).
- Blender determinism (the final plate): frames 100 and 300 rendered again in a fresh process, PSNR 71.3 dB and 47.3 dB against the sequence (the floor is 45 dB).
- Audio (`bin/vh qa`): no digital silence, dropouts or pumping; 62 of 62 cues within one frame (median 6.0 ms); −14.0 LUFS, −1.65 dBTP. Click warnings: see below.

## Independent review

You authorised skipping gates ② and ③ ("just make the final version"), so fresh-context reviewers stood in, against the 20 checks and the 8 scores of `templates/TASTE_CHECKLIST.md`:

| Round | Cut | concept | hook | desktop read | motion | variety | finish | accuracy | sync |
|---|---|---|---|---|---|---|---|---|---|
| 1 | draft 2 (the first Blender plate) | 6 | 7 | 5 | 6 | 6 | 5 | 7 | 7 |
| 2 | draft 3, 87.5 s | 6 | 7 | 6 | 7 | 8 | 5 | 7 | 7 |
| 3 | final plate, 87.5 s | 7 | 8 | 6 | 7 | 7 | 6 | 7 | 8 |
| 4 | 130 s (21 holds stretched) | 8 | 7 | 8 | 7 | 7 | 7 | 9 | 8 |
| 5 | 147.5 s (26 holds) | 7 | 7 | 8 | 8 | 6 | 7 | 7 | 7 |

What each round changed is in [NOTES.md](NOTES.md). The biggest change came from round 5: the request typed at the start now runs through the body (its type lights up among the nine, the gates show its outline, storyboard and draft, the self-review loop fails three of its frames, and the final cut plays it). After the five rounds you watched the result yourself: rounds 3–5 had pushed the holds to a strict reading formula, and the 150.5 s cut felt slow. This 103 s cut is the answer to that, and you approved its pacing; the reviewers did not score it again.

## Reproduce

```bash
tools/fetch_media.sh 00-promo 01-hand 02-short 03-math v3            # from the repo root: the showcase films and v3 that the clips and the atlas are cut from
cd showcase/04-intro-film
npm i && bash tools/make_clips.sh                                    # HyperFrames, three; proxies of showcase 00–03 → assets/clips/
bash tools/opening_export.sh                                         # the shader films → assets/films-proc.png, the opening film → assets/hero-earth.png
uv run --no-project --with pillow python tools/film_atlas.py         # 41 cuts of this repo's films → assets/films.jpg (byte for byte)
uv run --no-project --with pillow python tools/ai_atlas.py           # the 40 AI stills → assets/films-ai.jpg (and the small atlases)
tools/bl_render.sh 0 474 final2                                      # the Blender opening, 1080p, about 1 h 28 min (macOS only)
uv run --no-project --with numpy python tools/export_state.py       # cards and camera → assets/state.json
uv run --no-project --with pillow python tools/request_tex.py ../02-short-leo-doppler   # the gates' doors and the loop: 02's storyboard, draft sheet, frames
bash tools/deliver.sh                                                # plate, HyperFrames render, audio (tools/build_audio.sh), QA, encodes, poster, sheet, the README chapters
```

The Blender steps run on macOS only: `tools/bl.sh` sandboxes Blender with `sandbox-exec`, and `galaxy.py` renders on Metal (elsewhere, run Blender yourself and set the Cycles device). `tools/deliver.sh` writes `out/final.mp4`, the file in the release; `tools/chapters.sh` cuts the six README chapters (1080p, under 10 MB each) and `tools/watermark.sh` adds the corner mark (the other samples' README clips were made with the same script). The AI stills can't be regenerated byte for byte; `assets/ai/` holds the 40 that were used. After changing [`js/tmap.js`](js/tmap.js), run `python3 tools/retime.py` (score, SFX, the footage windows) and rebuild the audio. `tools/self_sheets.sh <draft.mp4>` bakes this film's own frames into the wall behind "This film, too." (render a draft first, then the final).

## Known imperfections

- **Not every score reached 8.** The weakest is variety (6): from 25 s the stations share one grammar (glide in, hold, labels, whip out) in one amber corridor.
- **Click warnings in the music.** `bin/vh qa` flags about 140 sharp edges in the score stem, from the v3 score's gated saw ostinato. Now that the drums keep playing through the holds they are less exposed than in the 150.5 s cut (about 190), but nobody has checked them by ear.
- **The 8.0 s burst** is mostly below 150 Hz, so it is weak on laptop speakers; a whip layer carries its attack.
- **The terminal's hold** plays one bar of the opening sketch twice.
- **Re-exporting the shader atlas** (`tools/opening_export.sh`) gives a slightly different row 27 (the Earth film): its shader changed after the atlas the Blender render used was exported (the other 27 rows are pixel-identical).
- **Lossless determinism** was measured for the Blender plate, not for this cut's HyperFrames body.
