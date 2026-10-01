# 00 · promo — OpenVideoHarness launch film (README hero)

![OpenVideoHarness launch film](media/preview.gif)

[media/final.mp4](media/final.mp4) · poster: [media/poster.png](media/poster.png) · contact sheet: [media/sheet.png](media/sheet.png)

| | |
|---|---|
| Type / route | `promo` → `video-types/03-product-promo.md` (via the CLAUDE.md routing table) |
| Engine | HyperFrames **0.8.82** (HTML + GSAP 3.14.2), installed as a project devDependency |
| Output | 20.0 s, 1920×1080, 30 fps, 600 frames; stereo AAC soundtrack (code-composed score + foley, −14 LUFS, mix profile `promo`) added after the picture was finished, see [Soundtrack](#soundtrack) |
| Render time (M3 Max) | final master `--quality high`: **27–29 s** (capture ~9 s + encode ~17 s, 5 workers, hardware GPU); draft: ~10 s; grain-free GIF source: ~11 s; web re-encode (x264 slow, CRF 23): ~12 s |
| Files | master 72 MB (grain) → `media/final.mp4` 6.8 MB (the 6.3 MB web encode, copied, + AAC 192 kb/s); `media/preview.gif` 5.5 MB (800 px, 15 fps, grain-free cut) |
| Review iterations | first cut: 5 snapshot rounds, 2 drafts, 2 final candidates, 1 fresh-context reviewer (12 FAILs fixed). Rebrand pass: 1 snapshot round, 3 drafts (incl. the rebuilt draft v1), 1 final (4 more FAILs fixed). All logged in NOTES.md 自评记录 |
| Wall time | first cut ≈ 115 min (incl. one API rate-limit interruption); rebrand pass ≈ 25 min |

## The request

> Produce the README hero video — a short launch film for OpenVideoHarness itself — following the harness exactly as a new user's agent would. Type `promo`, engine HyperFrames. 15–20 s, 1920×1080, 30 fps, silent. Pick ONE register (Apple or Linear/Vercel) and justify it. Beats: hook → problem → 3 real "UI doing the thing" beats → proof → stillness → wordmark + tagline. Real assets only, no brand logos, no paid APIs. Approval gates waived for this showcase, but BRIEF/STYLE/STORYBOARD still written before code.
>
> Follow-up (after the harness was renamed and the CLI became `bin/vh`): rebrand every on-screen string, show what `bin/vh new promo launch-film` prints *now*, regenerate the baked review images so beat 03 stays honest, re-render.

## What's on screen (and where it comes from)

| t (s) | Beat | Real source |
|---|---|---|
| 0.0–2.5 | Hook: "Your coding agent, now a video studio." | — |
| 2.5–4.7 | Problem: "One catch: it can't watch video." | CLAUDE.md intro ("你看不了视频本身，只能看渲染出的帧") |
| 4.7–8.0 | 01 · cursor clicks a terminal, `bin/vh new promo launch-film` types, its real stdout (hf-init lines, `✓ created projects/2026-09-29-launch-film`, type doc, next) + the 14 entries that project had | a re-run on 2026-09-29 01:38 into a throwaway project, deleted afterwards — `assets/vh-new-stdout.txt`, `assets/vh-new-tree.txt` |
| 8.0–11.3 | 02 · a request is routed: CLAUDE.md routing table rows 01–05, row 03 → `video-types/03-product-promo.md` · HyperFrames | CLAUDE.md 路由表, verbatim |
| 11.3–15.0 | 03 · the timestamped `bin/vh sheet` of **this film's draft v1**, the real `#3 FAIL` (push-in cuts the row), click → the current frame 315, `✓ #3 PASS` | `tools/draft-v1.sh` → `out/draft-v1.mp4`, `bin/vh sheet`, NOTES.md |
| 15.0–17.0 | Proof: 8 video types · 10 stages · 3 review gates · 20 taste checks, then 0.5 s still | `video-types/`, `playbook/01-pipeline.md` (十阶段流程 0–9), CLAUDE.md step 5, `templates/TASTE_CHECKLIST.md` |
| 17.0–20.0 | Wordmark "OpenVideoHarness" + "Video as code, for coding agents." | — |

Motif: the lower-left `t 00.00  f 000` is written from the playhead on every frame — the film prints the t each frame is a pure function of. It also makes every contact-sheet tile self-labelled.

Register: **Linear/Vercel** — the harness has no glossy product surface to macro-crop; its real UI is a terminal, a markdown table and a contact sheet, which read natively as near-black + 1px hairlines + mono. One amber accent with one meaning ("what the harness is acting on now"). Full reasoning in NOTES.md 创作决策.

**How beat 03 stays honest after a rename.** The draft it critiques is rebuilt, not faked: `tools/draft-v1.sh` copies the source, flips `const DRAFT = "final"` → `"v1"` in `s-route.html` and `s-review.html` (the draft-v1 table widths + 1.4× push that produced #3, and the draft-v1 stand-in review beat), and renders `out/draft-v1.mp4`. Everything else in that rebuild is the current film (the other v1 bugs were already fixed). The flaw on screen is the real one, with the same numbers, under the new name.

## Soundtrack

The picture was made and finished silent, as the brief asked; the soundtrack was fitted to it afterwards (2026-10-01). So here the picture's timing is fixed and the audio fits it, the reverse of the harness's usual "audio decides the timing". The film has no narration: the type is the voice.

- **Score** (`audio/score.json`, `bin/vh music` with instrument parts): minimal electronic in E major at 120 BPM (15 frames a beat). Bar lengths (`meters`) put a bar head on the cuts at 2.5, 8.0, 15.0 and 17.0 s. The cuts at 4.7 and 11.3 s fall between beats (meters take whole beats), so the music turns 0.3 s / 0.2 s after them and the whoosh on the cut frame carries the cut.
  - Legato bed: a detuned drone, a CS-80-style pad and a string section.
  - Rhythm: `sq_bass` 8ths, a soft kit (kick, hats, a clap in D and F) and a `seq` arpeggio with an echo.
  - Accents: a glockenspiel doubles the ding on the routed row, and a felt-piano chord lands with the wordmark.
  - It breathes three times: the problem line (2.5–5.0 s, no rhythm, a minor iv chord), a comma before the PASS click (13.5–14.0 s, kick and bass out) and the stillness before the wordmark (16.0–17.0 s).
- **Foley** (`tools/foley.py` → `audio/events.json`, 41 events): a soft "thock" as each hook and tagline word lands, a whoosh peaking on every cut (where the motion is fastest), the prompt click, the typed command, Return, the `✓ created` chirp, a rising run as the file tree fills, ↵ and the scan ticks, the ding on the routed row, error → shutter → success for FAIL → PASS, odometer ticks on the exact frames where each proof number changes, and an impact on the wordmark. Times come from the GSAP timelines and are snapped to the first frame that shows the action; each event carries a `why`. Pan follows the sounding thing's on-screen x. Ten sounds are synthesized in code (numpy/scipy, seeded); the rest are `bin/vh sfx` built-ins.
- **Mix** (`bin/vh mix … profile=promo`, see playbook/04-audio.md 混音): there is no narration, so the music's 3 s loudness is the anchor. Each SFX event is classed (hero, detail, ambience, signal) by its `role` in `events.json`, else by its name, and moved half way toward its class's range; events ≤ 0.2 s apart (the hook's word thocks, the count-up) move together. The last hook thock (`thock_lo`, "studio.") has `role: hero`: its name reads as a detail, but it lands the whole hook. The music dips 2.5 dB under each hero hit, and the SFX share one short room. One static gain to −14.0 LUFS; true peak −1.65 dBTP in the WAV (no limiting needed) and −1.71 dBTP after the AAC encode.
- **QA** (`bin/vh qa` on the WAV, the gate; `--stems` adds the mix report):
  - no digital silence, dropouts, pumping or clicks;
  - 29 of 29 cues (the SFX events above −18 dB and the score's two hits) within one frame, median 6.3 ms, max 25.7 ms. Three rows are marginal (`OK~`): the NOTES line typing at 12.17 s, which starts with the error sound (that one is confirmed by its own sound), and the impact and piano chord at 17.0 s, where the detector fires on the first 2.7 ms hop of a steep onset that the next hop clears by +0.22;
  - mix report: targets met. Hero median −2.1 LU re the anchor (range −4…2), detail −5.3 (−11…−3). Warnings: three detail events a little HIGH (the "video" thock at 1.07 s, the whoosh over the quiet problem line at 2.5 s, the first count-up column), and the sub boom under "One catch" is 100 % under 150 Hz, so it is felt rather than heard and may vanish on laptop speakers;
  - the mp4 passes the scan and the cue check too (29 of 29), and `bin/vh check` finds no black, frozen or silent stretch.
- The maintainer listened to the first candidate mixes on 2026-10-01 and chose a mix profile for each film. This profile mix has not been listened to yet; NOTES.md lists what to listen for.

Rebuild (from the repo root; needs uv and ffmpeg):
```bash
showcase/00-promo-launch-film/tools/build_audio.sh                  # → audio/mix.wav, audio/stems/, audio/qa.txt
showcase/00-promo-launch-film/tools/build_audio.sh --mux out.mp4    # … plus out.mp4 = the picture of media/final.mp4 + that mix
```
The script runs `tools/foley.py`, `bin/vh sfx lib`, `bin/vh music`, `bin/vh mix … profile=promo`, `bin/vh qa` and, with `--mux`, `bin/vh mux` (the picture is copied, not re-encoded, and the moov goes first so a browser can start playing at once), then measures the true peak of the AAC encode and mixes again with a lower ceiling if it is over −1.5 dBTP. Every run gives the same bytes. Only the sources are committed: `audio/score.json`, `audio/events.json`, `audio/music.beats.json`, `tools/foley.py`, `tools/build_audio.sh`. The WAVs, stems and reports are regenerated and ignored (`audio/.gitignore`).

## Reproduce

```bash
cd showcase/00-promo-launch-film
npm i                                              # installs hyperframes 0.8.82 locally
export HYPERFRAMES_SKIP_SKILLS=1 HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
npx hyperframes lint && npx hyperframes check
npx hyperframes render --quality high --output out/final.mp4
npx hyperframes render --quality high --variables '{"grain":0}' --output out/final-nograin.mp4   # GIF source
```
The soundtrack is rebuilt separately: see [Soundtrack](#soundtrack). Needs macOS (SF Pro via `system-ui`, SF Mono/Menlo via `local()`, PingFang for the CJK table) (GSAP is installed by `npm i`; no network at render time). Beat-03 asset regeneration and every other command: LESSONS.md → 可用命令. Working project: `projects/2026-09-28-launch-film/` (drafts, snapshots, seam strips in `out/`).

## Install commands that worked

First cut (2026-09-28, before `hf-init` existed):
```bash
bin/vh new promo launch-film
cd projects && HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.8.82 init _hf-launch-film \
  --non-interactive --example=blank --resolution=landscape --skill=product-launch-video
# init refuses a non-empty dir → init into a sibling, move the project files in (never its CLAUDE.md/AGENTS.md into the showcase)
cd 2026-09-28-launch-film && npm i -D hyperframes@0.8.82
```
Today `bin/vh new promo <slug>` runs `hf-init` itself (with `HYPERFRAMES_SKIP_SKILLS=1`); only `npm i -D hyperframes@0.8.82` is still worth adding for a local, pinned CLI. `npx hyperframes skills update` was never run; `init` only ever ran with `HYPERFRAMES_SKIP_SKILLS=1`.

## What the harness docs helped with

- **Routing was instant**: CLAUDE.md → `03-product-promo.md` → beat structure, register choice, bans and the prompt block were a ready-made storyboard skeleton. `bin/vh new` pastes the prompt block into BRIEF.md.
- **reads as timing** (`playbook/01-pipeline.md`): every beat was timed from its reads — the only way a silent 20 s film with 7 beats fits.
- **The verification ladder caught real bugs** (`playbook/02-verification.md`): snapshot → draft → sheet → seam strips found a dead frame on a cut, a 2-frame cursor flash, a push-in that truncated the answer, collapsed word spaces, and (this pass) mono text rendering proportional.
- **TASTE_CHECKLIST's numbered format** turned critiques into one-line log entries; one of them (`#3 FAIL`) is the content of beat 03.
- **HeyGen doctrine, locally readable** (`references/repos/hyperframes/_upstream_claude/skills/`): `motion-doctrine`, `cut-the-curve`, `oversized-cursor` gave exact numbers (230 px partial travel, power4 in/out, 7cqw cursor, tip pivot `21% 14%`, 0.1/0.22 s tap) and seek-safe patterns (set-then-to).
- **Fresh-context reviewer** (pipeline stage 7) found three things I had stopped seeing (NOTES line too wordy, a second colour family in the embedded sheet, a doubled-looking cursor).
- **Timestamped `bin/vh sheet`** (new in this pass) labels each tile with its exact time — the flagged tile is now "0:10.50" on screen, matching the timecode motif.

## Friction points

Still open (most important first):
1. **`ui-monospace` isn't mono in renders** — `engines/README.md` § HyperFrames (0.8.82 实测) says `system-ui` / `ui-monospace` pass the font lint when Geist isn't installed. They pass, and `hyperframes snapshot` shows a real mono, but `hyperframes render` (chrome-headless-shell) sets `ui-monospace, monospace` in a **proportional** face. Every terminal and path in the first cut was SF Pro, and nothing flagged it. Fix used here: `@font-face { font-family: "LF Mono"; src: local("SF Mono"), local("SFMono-Regular"), local("Menlo-Regular"), local("Menlo") }` — lint accepts it, render honours it. Also worth a line in `playbook/02-verification.md`: judge type from a frame of the MP4, not from snapshots.
2. **Self-referential beats vs renames** — nothing in the harness anticipates a film that shows its own drafts (common for tool promos). A rename forced a reproducible "draft v1" (`const DRAFT` switch + `tools/draft-v1.sh`). Could be a pattern note in `video-types/03-product-promo.md`.
3. **`bin/vh sheet` tile labels are saturated yellow** (`tools/sheet.py`, `fill=(255,220,0)`) — fine for review, but a sheet shown *in* a film adds a second accent; here the sheet is greyscaled and the hi-res overlays re-labelled in matching grey (`tools/label-tile.py`). A `--label-color` flag would help.
4. **`bin/vh new` output is long** — with `hf-init` it prints 6 lines (two of 115 and 161 chars). Honest on screen, but a promo's terminal beat now needs a smaller mono (26 px) and a push-in to stay legible; beat C grew by 0.3 s.
5. **Checklist #5 vs the 7-beat budget** — hook/problem text is on screen ~2.2 s (rule: 2.5 s). The checklist now scopes #5 to text that must be read; the promo beat structure still makes 2.5 s per block hard inside 15–20 s.

Resolved in the repo during this project (reported in the first cut, now fixed): global skill installs by `hyperframes init` / `skills update` (warning + `bin/vh hf-init`); `init` refusing the directory `bin/vh new` created; the `_upstream_claude` vs `.claude` path mismatch; `/product-launch-video` described as the pipeline to run (now "borrow its references"); silent promos (type doc §5 + checklist #18); grain vs GIF size (type doc §4); hard rule 1's testability (PSNR ≥ 45 dB); "九阶段" over a 10-row table (now 十阶段); untimestamped sheets; `check --snapshots` semantics and swallowed spaces (engines/README); harness changes mid-run (now a CHANGELOG).

## Where the wordmark / CLI name lives

Live text (edit, then re-render):
- `compositions/s-lockup.html` — `<div class="lk-word">OpenVideoHarness</div>` · frames **510–599** (17.0–20.0 s), and `media/poster.png` (frame 570).
- `compositions/s-scaffold.html` — `zsh — OpenVideoHarness`, two `OpenVideoHarness $` prompts, `const CMD = "bin/vh new promo launch-film"`, and the stdout lines · frames **141–239** (4.7–8.0 s).
- `compositions/s-route.html` — request pill "a 15–20 s launch film for OpenVideoHarness" · frames **240–338** (8.0–11.3 s).
- `compositions/s-review.html` — caption `bin/vh sheet projects/2026-09-28-launch-film/out/draft-v1.mp4 6 1` · frames **339–449** (11.3–15.0 s).
- `index.html` `<title>` (not rendered).

Baked into images (frames 339–449; regenerate with the commands in LESSONS.md, never edit): `assets/review-sheet.png`, `assets/review-flagged.png`, `assets/review-fixed.png`.

## Files

```
00-promo-launch-film/
├── README.md  BRIEF.md  STYLE.md  STORYBOARD.md  NOTES.md  LESSONS.md
├── index.html            root: grid, 7 scene hosts, cursor (root timeline = cross-scene carrier), timecode, grain
├── compositions/         s-hook · s-problem · s-scaffold · s-route · s-review · s-proof · s-lockup
├── assets/               cursor.svg · grain.png (seeded) · vh-new-stdout.txt · vh-new-tree.txt
│   ├── review-sheet.png  review-flagged.png  review-fixed.png   (this film's own drafts)
│   └── draft-v1/         the draft-v1 stand-in sheet (ClaudeAnimationBase demo, MIT) for the rebuild
├── tools/                draft-v1.sh (rebuild the critiqued draft) · label-tile.py (tile label for the crop overlays)
│                         foley.py (custom sounds + audio/events.json) · build_audio.sh (the whole soundtrack)
├── audio/                score.json · events.json · music.beats.json (film time) · .gitignore (the WAVs are regenerated)
├── hyperframes.json  meta.json  package.json
└── media/                final.mp4 · preview.gif · sheet.png · poster.png
```
HyperFrames' generated CLAUDE.md / AGENTS.md are left out on purpose. Credits: HyperFrames (Apache-2.0, HeyGen) and its motion-doctrine / oversized-cursor / cut-the-curve skills as technique references; the draft-v1 stand-in sheet is a render of the bundled ClaudeAnimationBase demo (Clawd, MIT, © John Heibel) and appears only as tiny greyscale thumbnails inside beat 03.
