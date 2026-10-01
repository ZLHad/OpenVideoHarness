# Showcase 01: Clawd and the Leaf (hand-drawn / ClaudeAnimationBase)

![preview](media/preview.gif)

**Full video:** [media/final.mp4](media/final.mp4) · **Contact sheet:** [media/sheet.png](media/sheet.png)

| | |
|---|---|
| Type / route | `handdrawn` → `video-types/07-hand-drawn.md`, engine ClaudeAnimationBase (p5.js + p5.brush), scaffolded with `bin/vh new handdrawn clawd-leaf` |
| Output | 1920x1080, 24 fps, **12.0 s** (288 frames), h264 in limited-range BT.709 + a stereo AAC soundtrack (cartoon score + foley, −14 LUFS, mix profile `cartoon`, added after the picture was finished: [Soundtrack](#soundtrack)), 9.0 MB |
| Render time (M3 Max) | final `--frames --workers=4` + `--encode`: **57 s** wall (≈173 ms/frame effective). Review sheets and strips: 100–300 ms/frame, 3–10 s per image |
| Review iterations | 3 rounds + a final QA pass, 28 check images in the project's `out/check/` (see [NOTES.md](NOTES.md)): ① contact sheet per shot + prop model sheet → ② face and contact crops, re-staged sheets → ③ strips of every key motion and all four seams, plus a boil check → final 24-frame sheet + `bin/vh check`. About 20 logged FAILs, all fixed. |
| Agent wall time | ~40 min of active work from reading `CLAUDE.md` to delivery (not counting a ~70 min pause for an API rate limit) |

## The request this was built from

> Showcase type `handdrawn` (video-types/07-hand-drawn.md). 12 seconds, 1920x1080, 24 fps, silent. Premise (refine it, keep it original, don't reuse the demo's story/night sky/star): Clawd tries to film a falling autumn leaf with a tiny hand-cranked movie camera; the wind keeps snatching the leaf just as Clawd frames it; it ends with the leaf landing on Clawd's head in the viewfinder, and Clawd films itself, delighted. Warm autumn palette. Follow ANIMATION_GUIDE's rules (handmade, alive, one piece, no text, transitions at every seam, reads timed for the viewer). Do the full review loop: a contact sheet per shot, strips for key motions and transitions, crops for faces; log every self-critique in NOTES.md and fix what fails. Approval gates skipped by the user; BRIEF.md and STORYBOARD.md still written, with reads and timings, before coding.

## What's in the video
**A (0–4 s).** A rounded viewfinder opens out of ink onto a golden maple leaf trembling on a twig. It widens and pulls back to reveal Clawd below with a tiny walnut-and-brass movie camera at its eye. The leaf lets go and rocks down. Clawd gets excited, cranks, and holds the leaf in frame. A gust (cream dry-brush streaks, grass leaning first) snatches the leaf over Clawd's head and out to the right. Clawd does a surprise take, turns through the drawn key views and bolts.
**B (4–8.2 s).** Cut on action. Clawd dashes right, the camera catches up, and the leaf settles on a blue-green squash. Clawd skids, sneaks, frames it, cranks, and gust #2 loops the leaf up and away. Clawd gives a blank stare, then an angry stomp. Then it turns the camera round (lens right → lens at viewer → lens at Clawd), a "?" pops, and it peers suspiciously into the lens. The camera pushes in until the brass-rimmed glass fills the frame.
**C (8.2–12 s).** POV through the viewfinder (ink border, cream corner brackets, blinking painted red dot). Clawd's huge suspicious face peers into the lens. The leaf drifts down from the top and lands on its head. "Oh!" take, then delight, hearts and a wave at the camera. The viewfinder closes on the beaming face and leaf, which rhymes with the opening.

## Soundtrack

The picture was made and finished silent, as briefed; the soundtrack was fitted to it afterwards (2026-10-01). It is a pantomime, so there is no narration: a cartoon underscore plus foley, mickey-mousing the storyboard's actions.

- **Score** (`audio/score.json`, `bin/vh music` with instrument parts): E major, 120 BPM from 0.0 s. That is the grid the animation already runs on (`src/config.js`: bpm 120, offset 0), so Clawd's beat-locked idles and the rec dot (it blinks every 2 beats) sit on the music's beats. Six bars of 4/4: A 0–4 s, B 4–8 s (the cut at 4.0 s is bar 3's downbeat), C 8–12 s. The POV music starts on bar 5 (8.0 s) as the lens glass fills the frame; the cut itself is at 8.2 s. A string section is the legato bed throughout, and the note lists land on the actions:
  - A: a celesta "wonder" motif as the iris opens; a flute that rocks down with the falling leaf; pizzicato 8ths while the crank turns; a xylophone "!" on the surprise take (3.0 s); a run into the cut.
  - B: pizzicato on the dash footfalls; a stop-time on the skid; a chromatic sneak; the music drops to the string bed for gust #2 and the blank stare; a muted-brass grumble and a timpani stroke on the stomp (6.78 s); a harp glissando into the lens.
  - C: vibraphone chords; a music box on the rec dot's seconds; the harp repeats the flute's falling-leaf zigzag as the leaf drifts onto Clawd's head; the same xylophone "!" on the notice (10.08 s); a harp arpeggio with the hearts (10.625 s); a pizzicato ta-da at 11.375 / 11.75 s as the viewfinder closes.
- **Foley** (`tools/foley.py` → `audio/events.json`, 38 events, 22 sounds synthesized in code):
  - The iris opening and shutting, with a latch, blades and a thunk on the last frame.
  - The stem creaking and snapping, a spark on the excited take, and a ratchet crank that clicks every 1/8 turn at leaf.js's 13 rad/s.
  - Two-layer gusts that cross from left to right, shaped like `gustEnv`; leaf whooshes peaking where the leaf moves fastest; cartoon takes (a pop and a slide whistle).
  - A zip into the dash, and six footfalls solved from `poseB`'s walk cycle, plus two tiptoes.
  - A skid, leaf pats on the pumpkin and the head, the stomp with the camera rattling, and a "?".
  - The spin, a swish into the lens, the film gate chattering at 24 fps inside the camera for the whole POV shot, and hearts.
  - Event times come from the shot constants and pose code in `src/scenes/leaf.js`, cited per event (`why`). Pan comes from the character's screen x under that shot's camera.
- **Mix** (`bin/vh mix … profile=cartoon`, see playbook/04-audio.md 混音): the foley leads. There is no narration, so the music's 3 s loudness is the anchor; each SFX event is classed by its `role` in `events.json`, else by its name, and moved half way toward its class's range, and events ≤ 0.2 s apart (the dash footfalls, the landing and the take) move together. The gusts have `role: detail`: their name reads as ambience, but they are the gag's action. SFX peaks are held at 9 dB over the anchor, the music dips 2 dB under each hero hit (the snap, the takes, the stomp, the iris thunk), and the SFX share one short room. The film ends on a 40 ms fade, so the thunk on the last frame keeps its attack. One static gain to −14.0 LUFS, true peak −1.79 dBTP in the WAV, −1.65 dBTP after the AAC encode.
- **QA** (`bin/vh qa --fps 24` on the WAV, the gate; `--stems` adds the mix report):
  - no digital silence, dropouts, pumping or clicks;
  - 30 of 30 cues (the SFX events above −18 dB and the xylophone hits) within one frame (41.7 ms), median 7.2 ms, max 27.0 ms. Five in the dense 1.6–4.9 s stretch are marginal (`OK~`): the crank's first click, the push-off and the xylophone run into the cut (one shared onset), the first footfall and the skid;
  - mix report: targets met. Hero median +1.6 LU re the anchor (range −2…4), detail −2.0 (−6…0), ambience −12.7 (−16…−8). Nine single events sit up to 2 LU outside their class's range; see NOTES.md;
  - the mp4 passes the scan and the cue check too (30 of 30), and `bin/vh check` finds no black, frozen or silent stretch.
- The maintainer listened to the first candidate mixes on 2026-10-01 and chose a mix profile for each film. This profile mix has not been listened to yet; NOTES.md lists what to listen for.

Rebuild (from the repo root; needs uv and ffmpeg):
```bash
showcase/01-handdrawn-clawd-leaf/tools/build_audio.sh                  # → audio/mix.wav, audio/stems/, audio/qa.txt
showcase/01-handdrawn-clawd-leaf/tools/build_audio.sh --mux out.mp4    # … plus out.mp4 = the picture of media/final.mp4 + that mix
```
The script runs `tools/foley.py`, `bin/vh sfx lib`, `bin/vh music`, `bin/vh mix … profile=cartoon`, `bin/vh qa` and, with `--mux`, `bin/vh mux` (the picture is copied, not re-encoded), then measures the true peak of the AAC encode and mixes again with a lower ceiling if it is over −1.5 dBTP. Every run gives the same bytes. Committed: `audio/score.json`, `audio/events.json`, `audio/music.beats.json`, `tools/foley.py`, `tools/build_audio.sh`. The WAVs, stems and reports are regenerated and ignored (`audio/.gitignore`).

**Colour.** The engine used to encode Chrome's full-range BT.601 frames as they were (`yuvj420p`, tagged `pc` / `bt470bg`), and Chromium shows such a file with shifted colours. `media/final.mp4` was re-encoded once, with the soundtrack, to limited-range BT.709 with all four colour tags, as the engine now writes (#28): x264 `slow`, CRF 19, the same 288 frames at 24 fps. CRF 17–18 would have grown the file by 34–49 %. Measured over five frames, the saturated colours now decode within 1.4 levels on average of the original's own decode (it was 6.4 levels off when read as BT.709); see NOTES.md.

## Files
- `BRIEF.md`, `STYLE.md` (palette, colour arc, 3 transition kinds), `STORYBOARD.md` (logline/world/motif/arc, shots, reads with shipped timings), `NOTES.md` (decisions + the full review log + the 3 spots I like least), `LESSONS.md`
- `src/scenes/leaf.js`: the whole film (3 shots, the leaf, the movie-camera prop with drawn key views, wind, viewfinder transition, a `LOOPS.props` model sheet). Also `src/config.js` (12 s, 120 bpm) and `studio.html` (scene tag swapped from `demo.js`)
- To re-render: `bin/vh new handdrawn x`, copy these three files over the new project, then `node render.mjs --frames --workers=4 && node render.mjs --encode --out=out/final.mp4`
- Soundtrack: `audio/score.json`, `audio/events.json`, `audio/music.beats.json`, `tools/foley.py`, `tools/build_audio.sh` (see [Soundtrack](#soundtrack))

## Three things the harness docs got right
1. **Reads as the timing sheet** (`ANIMATION_GUIDE.md` §4 "Timing: model the viewer", restated in `playbook/01-pipeline.md` "reads"). Writing the reads with start and end times before coding gave the strip review a yardstick. It caught two real failures that sheets alone would have hidden: the leaf's release overlapping the reveal pull-back, and a 7-frame "notice" beat (below the 12-frame floor in `video-types/07-hand-drawn.md` §自查重点).
2. **Cheap, layered self-review** (`playbook/02-verification.md` §七层检查 + `ANIMATION_GUIDE.md` §Workflow 3). Sheet, strip, crop and especially `--crop-at` on a world point cost 3–10 s each, so 28 checks were affordable. Crops found the biggest staging bug: the camera prop hid Clawd's only side-view eye, so no face acting was visible.
3. **The "Common failures" list and the medium rules** (`ANIMATION_GUIDE.md` §Common failures, §1 "one shape, one outline", "Clawd is big", drawn key views instead of 3D). Every first-pass failure (tiny Clawd, star-like leaf, props covering the face, overlapping-outline pumpkin) mapped straight onto a named rule, and so did every fix. The drawn key-view idea transferred directly to the new camera prop.

## Friction and confusing instructions (most important first)
1. **Template defaults contradict the hand-drawn guide.** `templates/BRIEF.md` §"Motion defaults" says "No bounce/elastic, no idle breathing loops", and `templates/TASTE_CHECKLIST.md` #12 flags "bounce/elastic… 卡片呼吸循环" as a FAIL. `ANIMATION_GUIDE.md` §5 "Alive" and §Animation principles require takes, `backOut` overshoot and beat-locked idle motion. `bin/vh new handdrawn` copies both templates unchanged. `playbook/03-motion-design.md` §0 admits the conflict, but nothing in the project files says which wins, so I had to resolve it myself in BRIEF.md. The BRIEF template's "Type", "Text rules" and "safe box / caption band" lines are also meaningless for a no-text film.
2. **`bin/vh sheet` writes into the repo root.** The helper changed mid-session. The new default output is `./out/check/<name>-sheet-<HHMMSS>.png` relative to the *current directory* (header comment of `bin/vh`). Running it from the repo root, as instructed, created `OpenVideoHarness/out/check/` outside `projects/`, which breaks the spirit of CLAUDE.md hard rule 6. I moved the file into the project by hand. The earlier version wrote next to the video (`<video dir>/check/sheet.png`).
3. **Engine commands point into `engines/`.** `playbook/02-verification.md` §各引擎的取帧命令 says the ClaudeAnimationBase commands run "在 `engines/ClaudeAnimationBase/` 下". With CLAUDE.md hard rule 6 ("只在 `projects/` 里改东西") it should say "in your project directory". A new agent following it literally would render into the template.
4. **README names a CLI that doesn't exist.** `README.md` (rewritten mid-session as "OpenVideoHarness") uses `bin/vh doctor / setup / new` in §Quick start, but only `bin/vh` exists. CLAUDE.md §本机环境 still says `bin/vh doctor`.
5. **Holding props near the face isn't documented.** `ANIMATION_GUIDE.md` §Hooks says a held prop "just draws around (0, 0)". It doesn't say that in side view the hook space is rotated by `(.7 − aL)`, so a prop tilts with the arm unless you counter-rotate. It also doesn't say that side view has one eye at (≈2.7u, −6u), which any eye-level prop covers. I had to read `clawd.js` and reverse-engineer the transform (`bodyPt`/`camPt` in `leaf.js`) to aim the camera and start the lens push at the lens.
6. **Overlapping `paint()` shapes let earlier outlines bleed through.** p5.brush defers strokes, so the ink outlines of the pumpkin's side lobes showed through the front lobe's full-opacity wash, and `flushBrush()` between them did not fix it. `ANIMATION_GUIDE.md` §p5.brush quirks mentions deferral only for glow and letters. The only fix was a single silhouette plus painted ribs, so this deserves a line in the quirks list.
7. **`--crop-at` expressions can't reach scene code.** `ANIMATION_GUIDE.md` §Workflow 3 says `--crop-at` accepts "an expression evaluated in the page" (render.mjs cites `PLK.MX(1.38)`). The recommended scene template (§Build) wraps everything in an IIFE, so no scene function is reachable and the obvious `--crop-at='poseB(0).x,…'` crashes. Say "expose a global" or give an example.
8. **A parallel render hung silently.** I launched seven `render.mjs --strip` processes at once. One never produced output (0.2 s CPU after an hour, no error) until I killed it and reran it alone. Cause unverified. `render.mjs` launches Chrome with `protocolTimeout: 0`, so a stalled CDP call never errors; `studio.html` also fetches a Google Font over the network on every page load. The pipeline doc encourages parallel workers, so a per-call timeout or a note would help.
9. **The project root ends up with two sets of instructions.** `bin/vh new` copies the engine's own `README.md` into the project root. That README says to render `out/video.mp4` and to "open it in Claude Code", while `playbook/01-pipeline.md` expects `out/final.mp4`. `video-types/07-hand-drawn.md` §工作流 step 1 still shows the manual `cp -R … && npm install` path instead of `bin/vh new`.
10. **Resolved mid-session:** CLAUDE.md hard rule 2 ("音频决定时长") first had no clause for silent videos. It has since been amended to "静音视频的时长由分镜里的 reads 决定", which matches what I did.
