# Changelog

## Unreleased

**Linux fixes, found while setting up a cloud (Ubuntu 24.04) machine**
- `bin/vh` used the macOS-only `sed -i ''`, which GNU sed reads as a file name. On Linux, `new … --effort` silently kept `standard` in BRIEF.md, and `hf-init` left GSAP on the CDN, so `hyperframes render` refused to run offline. Both now go through a portable `sedi` helper.
- `styles/_swatch/package-lock.json` pinned every package to `registry.npmmirror.com`, so `npm ci` failed wherever that mirror is unreachable. It now records `registry.npmjs.org`, which npm swaps for whatever registry you have configured, so mirror users are unaffected.
- The swatch renderer used BSD-only `stat -f` (every swatch render died on Linux after rendering) and the determinism check used macOS-only `md5 -q`. The determinism check also ran ffmpeg in a `while read` loop without `-nostdin`, so it could pass without comparing every frame; it now fails unless every PNG was compared.
- `bin/vh doctor` probes headless WebGL, finds Playwright's Chromium, and gives install hints for the OS it runs on; `bin/vh setup` retries its smoke test with `--soft-gl` on machines without a GPU.

**Found in a full review of v0.2.1**
- Determinism (hard rule 1): with `--soft-gl`, ClaudeAnimationBase frames differed on every launch (~39 dB). The main cause was Chrome's canvas readback noise (fingerprinting protection), now disabled on every path; `--soft-gl` also keeps 2D canvases on the CPU. Frames are now pixel-identical across launches and render orders, and about 3× faster in software.
- `render.mjs --encode` ignored `PROJECT.audio` (the parallel `--frames` → `--encode` path made a silent video), read fps only from `--fps`, assumed frames start at 0, encoded stale frames after a shorter cut, and shared `out/frames` with `--loop`. It now reads PROJECT in Node, records the fps in `frames.json`, encodes exactly `duration × fps` frames, stops on a hole between rendered frames, and gives loops their own folder. `--clip` and `--encode` pad or trim the audio to the picture instead of `-shortest`, which cut the video when the audio was shorter; `--clip` fails when ffmpeg does.
- Narration and captions: an English-only script produced Chinese captions; `|x|` and `x<y … y>z` were deleted from speech and captions outside dialogue; `wrap_zh` split Latin words; several lines inside one ASR word became zero-length cues; `--align` crashed on a line with no words; a second `[direction]` stayed in the text; `say` on Linux crashed with a traceback.
- `bin/vh sfx` read every WAV as 16-bit: 24-bit recordings became noise and float WAVs crashed. It now decodes through ffmpeg.
- `bin/vh mix`: loudnorm's linear mode silently fell back to dynamic normalisation while the tool reported "two-pass linear". It now applies one static gain, adds a 4×-oversampled true-peak limiter only when needed, and prints the measured output. The default ducking is now `duck=voice` with a voice bus and `duck=off` without one; the old default (`duck=on`) made the documented mix fail `bin/vh qa`.
- `bin/vh qa` detected digital silence in 5 ms windows, so whether a 20–25 ms gap was caught depended on where it started; it now works sample by sample and reports exact times.
- `bin/vh mux` tagged subtitle languages from the whole path (everything under `/home/zhang/…` became Chinese). Unknown commands exit 1; `new` removes a half-built project; `install-skill` escapes the clone path and rejects unknown targets; `gif` and `sheet` name outputs from the file, not a dotted folder; `sheet` no longer reports success when nothing was written. `references/fetch.sh` skips an unreachable upstream instead of aborting the installer.
- `lib.motionBlur` averaged transparent layers wrongly (a comet trail); `lib.drawGlyphs` ignored `sx: 0`.
- Docs: `CLAUDE.md` omitted `bin/vh style` and `sync-agents`; `bin/vh style --gallery/--check` were documented with dashes; the pipeline table asked `standard` for three scoring rounds; and a few counts and file names were stale.

**Checks and branch rules**
- `tools/ci.sh` runs the repo's own checks: shell syntax (also under macOS `/bin/bash` 3.2), shellcheck, a ban on BSD-only or GNU-only commands, Python and JS syntax, pyflakes, docs against the CLI, and `bin/vh` smoke tests. `--committed` checks HEAD in a clean checkout. GitHub Actions runs it on Linux and macOS.
- `main` accepts pull requests only: `.github/rulesets/main.json`, enabled on 2026-09-30. `CONTRIBUTING.md` has the branch, PR and push rules for people and agents.

**Camera language for video models**
- `playbook/05`: how to write camera moves a video model can execute (four layers, start → path → end → constraints, a trigger between two moves), after Adrian Punk's *AI 视频运镜词典*. `playbook/07` breaks camera motion down the same way; `playbook/08` treats one-take camera paths as a choreography and handheld drift as low-frequency noise.

**Defaults settled on a Mac (Apple M3 Max)**
- `bin/vh mix`: the default `duck_ratio` is now 1.6 (was 6). With narration that pauses ~0.25 s between lines, 6 and 3 made the music drop out between lines (`bin/vh qa`: 3 and 2 pumping dips); 1.6 had none and sounded best in a listening test.
- `bin/vh tts` without a language: an English-only script is now spoken in English (English voice, English ASR, `voiceover.en.wav`) instead of by the Chinese voice. A script with any Chinese line stays `zh`, so one narrator reads it all; `--lang zh` keeps the old behaviour.
- Verified on macOS with a GPU: `tools/ci.sh` under bash 5 and `/bin/bash` 3.2, `bin/vh doctor` (WebGL on Metal), frames pixel-identical across launches and render orders, `--encode` with `PROJECT.audio` and missing frames, a swatch determinism check and draft render, captions for English-only scripts and `|x|`, `--align gemini`, and `install.sh` from a fresh clone.

## v0.2.1 — 2026-09-30

**Narration with feeling and rhythm** (user: "声音是对的，但不够活泼，太僵硬")
- `bin/vh tts` accepts a per-line direction in `[brackets]`, added to the overall `--instruct` for that line only and kept out of captions.
- `--beats map.json [--snap beat|half|downbeat] [--lead s]` starts every line on the next grid point instead of a fixed gap. `@id:downbeat` pins one line, e.g. the answer on the drop. Tested live with Gemini at 120 BPM: lines landed at 0.50 / 4.00 / 5.00 / 10.00 s exactly.
- `playbook/04` "让声音有表情、有节奏":
  - how to direct narration, with a default delivery per video type;
  - riding the beat;
  - frame-aligned tempos at 30 and 24 fps;
  - rhythm density per type;
  - mixing so music stays present (a measured `duck_ratio=3` hole vs a clean `1.6`);
  - writing sound as prompts.
  
  Types 02, 03, 04 and 08 point to it.

**Gemini narration, further**
- Gemini 3.8 Flash TTS is now tested live in Mandarin and English (it was only mock-tested in v0.2.0). Also documented: the default local Qwen3-TTS 0.6B sometimes runs on after short English lines.
- `--align gemini`: every line, whatever the provider, is transcribed by `gemini-3.5-transcribe` for word timestamps and compared with the script. A line below `--min-sim` (default 0.85) is flagged, which catches the Qwen 0.6B run-on and skipped words. `--vocab` passes terms to the transcriber.
- Two-speaker dialogue: an `@speakers A=Kore B=Puck` header, then `A: …` lines. Labels only count when declared, so an ordinary "注意：" line stays narration.
- `--join block|all` sends consecutive lines as one request, so the delivery flows across sentences; the per-line files are then cut at word timestamps. A Gemini dialogue defaults to `block`.
- `bin/vh voices list | design | delete` manages Gemini designed voices.
- `bin/vh captions` writes per-word timing into `captions.json` and a `captions.<lang>.lines.srt` with one cue per wrapped line, each starting on its first spoken word.
- The key is read from `GEMINI_API_KEY` only; nothing is written to the repo.

**Reading time and motion rules**
- `tools/readcheck.py` / `bin/vh readcheck`: on-screen text needs max(2.5 s, CJK ÷ 4.5 + other ÷ 15 + 1.5 s), adapted from lemo-opuscar (MIT); subtitles follow the Netflix ceilings (CJK ≤ 9 chars/s, English ≤ 20) with a 1.8 s floor. Checklist item #5 and `playbook/03` use it.
- `playbook/03`: four spring registers by element (buttons, cards and camera, big type and logos, mascots), from xilo-opus-video, plus the NaN trap at ζ = 1.
- `playbook/08`: sub-frame motion blur must not sample across a cut, and per-subframe sub-pixel jitter gives free anti-aliasing (from abstract-algebra-promo).
- `playbook/02`: CJK web fonts on canvas arrive as unicode-range subsets, so `document.fonts.ready` can pass with glyphs missing. Call `document.fonts.load` once per weight with every character the film uses, and fail loudly on rejection, an empty result or a timeout.
- `playbook/05`: green-screen character + code scene: key and despill with ffmpeg, keep alpha (PNG or ProRes 4444), let code own the scene, type and beat.

**Styles: 28**
- Two new presets, each with a swatch, QA and determinism check, and two rounds of independent review: `pixel-16bit` (Chrono Trigger, A Link to the Past; 320 × 180 integer scaling, a fixed 24-color palette, mosaic transitions; lowest score 7) and `isotype` (Neurath and Arntz; one symbol = a fixed quantity, added or removed on the beat; lowest score 6).
- The deferred fixes from v0.2.0 are done: monumental-scifi has a hook, cutout-jazz and swiss-grid-type no longer share a motif, and the shadow-puppet click is gone. `gallery.jpg` / `gallery.mp4` rebuilt for 28.
- lemo-opuscar is now 43 styles and MIT for the whole repo (since 2026-09-29; older snapshots were CC BY 4.0). Presets adapted from the older snapshot keep their CC BY attribution.

**References**
- `cases/opus55-gallery.md` §7: a deep read of abstract-algebra-promo (sub-frame blur, cut protection, math promo structure); §5 adds the dsxzai catalog.
- `references/fetch.sh`: text-only clones now actually pull on update (the empty checkout used to short-circuit it).

## v0.2.0 — 2026-09-29

**Effort hub: one switch for how hard the agents work**
- Three levels: `quick`, `standard` (default) and `studio`, defined in one table in `CLAUDE.md`. The table sets:
  - the human gates;
  - how many styles are offered;
  - storyboard depth and self-check depth;
  - rounds of independent scoring;
  - sound;
  - deliverables;
  - draft count, subagents, research, and a suggested reasoning effort.
- A floor that never drops at any level: hard rules 1, 5 and 7, no digital silence, flash safety, type minimums, licenses, `bin/vh check`.
- `bin/vh new … --effort <level>` writes `Effort:` into BRIEF.md and, for `quick`, notes the gate waiver in REVIEW.md. `bin/vh effort [level]` prints the rules.
- Only the user can lower the level; an agent may not downgrade to save time.
- The checklist, pipeline, verification and review templates now say what each level does.

**Intro film and a rewritten README**
- `showcase/04-intro-film/`: the project's own 81 s intro film.
  - One continuous 3D shot built with HyperFrames + Three.js, and a score composed in code. It shows the architecture, the workflow with its three gates, the features and the case library.
  - It was made by agents following this repo and revised after two rounds of human notes: the music stuttered, and it wasn't cool enough. The notes, the look-dev in three intensities and every fix are in the folder.
- README (en / zh) rewritten in plain language, with the intro film as the hero.
- WeChat appreciation code at the end of both READMEs.

**Style swatches, reviewed and reworked**
- An independent "harsh motion director" scored all 26 swatches on the 7-dimension layer, twice. The median lowest score rose from about 4.5 to 6, but none has all seven scores at 8 or above yet: the library is honest about being work in progress (see `styles/README.md`).
- Makers' self-scores ran 1–2 points above the independent reviewer's, which is why the checklist insists the scorer is not the author.
- A pre-release fix round after the second review: editorial-data and dark-math got real hooks; ink-wash, silhouette-papercut and brutalist-meme had small rule violations fixed. Deferred to the next version: monumental-scifi (hook), the cutout-jazz / swiss-grid-type look-alike motif, and a shadow-puppet click warning.
- `styles/_swatch/custom_sfx.py` rebuilds the few custom foley WAVs byte for byte, so nothing shipped is hand-made or downloaded.
- Three rounds of fixes followed:
  - a hook at 0.1 s;
  - no freezes after the motif lands;
  - each style draws "draft" in its own language instead of ▶;
  - clones separated (cutout vs Swiss, CRT vs FUI, shadow puppet vs paper-cut, three "growing circle" endings);
  - the Dunhuang flying apsaras redrawn with proper bodies;
  - type sizes raised.
- Foley: `styles/<slug>/events.json` is mixed under the score. `styles/_swatch/foley.mjs` generates it from a `FOLEY` export in `swatch.js`, so picture and sound share one timing table. The foley track fades out with the score.
- The review's systemic findings became rules in the swatch content spec (`styles/_swatch/README.md`).


**Style library `styles/`: 26 tastes instead of one**
- 26 presets in 6 families (film titles, brand, data, illustration and print, Chinese aesthetics, retro). Each is distilled from famous works: Saul Bass titles, *Se7en*, *Blade Runner 2049*, Wes Anderson symmetry, Wong Kar-wai step-printing, Ken Burns, Müller-Brockmann, film FUI, 3Blue1Brown, NYT / The Pudding, Gapminder, *Spider-Verse*, risograph, CRT terminals, 水墨, 敦煌, 皮影, 国潮, Reiniger's silhouettes, watercolor backgrounds, synthwave, and more.
- Each preset has `STYLE.md` (study works, visual / motion / sound grammar, bans, prompt block, engine recipe, self-check), `tokens.json`, and a **real 5 s swatch with its own code-composed score**.
- All 26 swatches show the same content, so the only difference is the style. Overview: `styles/gallery.jpg` and `gallery.mp4`.
- Swatch renderer `styles/_swatch/` (HyperFrames): scene API, shared `lib.js` (easing, springs, decode text, textures, transitions), per-slug staging, a watchdog, and automatic audio QA. Swatches are deterministic, with lossless frames compared across worker counts.
- `bin/vh style list | <preset> | gallery | check`; `bin/vh new <type> <slug> --style <preset>` seeds the project with the preset.
- Gate ① now proposes 2–3 contrasting presets instead of defaulting to one look. Principle: learn the grammar, never copy characters, logos or shots.

**Review and verification**
- A scored layer on top of the 20-item checklist: a harsh-director reviewer scores 7 dimensions, each must reach ≥ 8, over at least 3 rounds. It catches "correct but not exciting".
- Phone-size (360 px) readability sheets, a loop-seam check, and determinism compared on lossless PNG frames rather than mp4.
- Silent-failure detection: frozen frames (renderAt exceptions), empty frames (YAVG), and render watchdogs.
- Look-dev (2–3 variants of one segment) when feedback is vague; optional full-length animatic at gate ②; authorized skips recorded verbatim.
- Motion: superposed springs, leading and trailing edge stiffness, layout functions for multi-aspect renders, decode-text rules.

**Sound**
- `bin/vh tts gemini` / `gemini-lite`: Google Gemini 3.8 Flash TTS and Flash-Lite TTS as cloud providers (`GEMINI_API_KEY`), with a plain-language delivery direction as the 5th argument. Inline tags such as `<short pause>` are voiced by Gemini and stripped for every other provider and from captions. Request and parsing tested against a mocked response; not yet called for real.
- `bin/vh beats`: adds `hits` and `kick` / `snare` accents with strength (HPSS plus band-split onsets, within ±1 frame on test loops).
- `bin/vh sfx place`: stereo, with per-event `pan` and `dist`, so sound follows on-screen position. The built-in `error` SFX loses its hard edges; the library is still 15 sounds.
- `bin/vh music`:
  - Chinese colour layers `bell` 编钟, `zheng` 古筝 (Karplus–Strong with `bend`), `dizi` 竹笛 and `taiko` 大鼓;
  - pentatonic modes;
  - variable `meters` with a `bars` map;
  - `--example zh`.
- `bin/vh mix`: stereo, two-pass linear loudness (keeps LRA), `duck=voice` and `duck_ratio`. **Fix:** music was truncated to the voice length when ducking.
- New `bin/vh qa`: final-mix QA covering digital silence, dropouts, pumping, click warnings to re-listen, and a cue check against the beat map and events.
- Rules learned from the intro film: dramatic stops are held breaths, never digital silence; don't key the ducker on every SFX.

**Robustness**
- `bin/vh hf-init` vendors GSAP locally and warns about any remaining CDN links, because an offline render with a CDN import hangs silently. Showcase 00 and 02 were updated the same way.
- `references/fetch.sh` neutralizes agent files (`.claude`, `.agents`, `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `.mcp.json`) at every depth, not only the repo root. New `fetch.sh <dir>` and `--neutralize` options.
- `bin/vh` help lists every command.

**Knowledge and references**
- `playbook/08`: FX preset stack (`fx` = A/B/C) with a reason per effect, flash and readability limits, true sub-frame motion blur, SFX pan from screen position, and one-take 3D world techniques. `engines/README`: Three.js + HyperFrames pitfalls.
- `video-types/03`: a promo shows the product itself; asset inventory before animating; look-dev step; up to ~90 s.
- `video-types/07`: Chinese characters written in true stroke order (Make Me a Hanzi data fetched per project, never vendored).
- `cases/opus55-gallery.md`: a second catalog (962 works) and a deep-dive into the *Battle of Austerlitz* 5-minute WebGL film. `cases/community-prompts.md`: new community data points.
- References grow from 24 to **30** repos: athemeroy's research catalog, claude-animation-skill, product-film-skill, procedural-film, the 962-work catalog, and Battle-of-Austerlitz-Film.

## v0.1.0 — 2026-09-29 · first public release

**Harness**
- `CLAUDE.md` / `AGENTS.md` router over 8 video types, with 7 hard rules and a rule-precedence section. `AGENTS.md` is generated from `CLAUDE.md` (`bin/vh sync-agents`).
- Three mandatory human review gates (outline → storyboard + keyframe preview sheet → first draft), recorded in `templates/REVIEW.md`.
- `playbook/` 00–08: paradigm and engine choice, 10-stage pipeline with "reads" timing, 7-layer verification, motion-design numbers, audio, hybrid generative video, research mechanisms, reverse-engineering a reference video, VFX and motion sources.
- `templates/`: BRIEF, STORYBOARD, STYLE, REVIEW, NOTES, LESSONS, TASTE_CHECKLIST (20 items).
- `cases/`: 11 case studies + `opus55-gallery.md` (curated from 389 community videos). `references/community-skills.md`: curated community skills, a 39-style library and a license table.

**Sound (music · SFX · voice · songs · captions)**
- `bin/vh tts`: local open-source **Qwen3-TTS** by default (Chinese voices Serena, Vivian, Uncle_Fu, Dylan, Eric; English voices Ryan, Aiden), plus `say` / `edge` / `dashscope` / `elevenlabs`. Bilingual scripts (`中文 || English`) with per-language timelines.
- `bin/vh captions`: zh / en / bilingual SRT + `captions.json` for engines, with CJK-aware wrapping; `bin/vh mux` adds soft zh/en subtitle tracks.
- `bin/vh music`: deterministic code-composed soundtrack (score.json → WAV + exact beat/section/hit map).
- `bin/vh sfx`: 15 original synthesized SFX; events placed so each sound lands on its action.
- `bin/vh mix`: voice + music + SFX, music ducks under voice and SFX, −14 LUFS.
- Songs: Suno-import workflow; ElevenLabs Music and local song-model interfaces reserved.

**CLI `bin/vh`**
- `doctor`, `setup`, `types`, `new <type> <slug>` (templates, prompt block pre-filled, engine scaffolded), `hf-init` (HyperFrames without global skill installs), `sync-agents`, `install-skill`.
- `install.sh`: one-line install (clone, deps, references, skill registration for Claude Code and Codex).
- QA: `sheet` (timestamped contact sheets, written into the owning project), `check` (black/freeze/silence, 3 s threshold), `gif`.

**References**
- `references/fetch.sh` fetches 23 read-only repos; media-heavy ones text-only; upstream `CLAUDE.md` / `.claude/` / `AGENTS.md` renamed to `_upstream_*` so they are never auto-loaded as instructions.

**Showcase** (made by agents following only this harness)
- 00 launch film (HyperFrames, 20 s), 01 hand-drawn short (p5.brush, 12 s), 02 vertical science short (HyperFrames, 24.8 s), 03 Fourier explainer (Manim, 25 s).

**Known gaps**
- Tested end to end: `qwen` (zh + en), `say`, captions, music, sfx, mix, mux. Implemented from official docs but not yet tested (no keys): `edge`, `dashscope`, `elevenlabs`. Word-level forced alignment and song-generation providers are reserved interfaces.
- Workflow docs are Chinese-first; English translations welcome.
