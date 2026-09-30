# Changelog

## Unreleased

**Shot recipes: how a shot moves, and the pacing of a whole film**
- `recipes/` is a new library of engine-agnostic shot recipes. A recipe carries the motion and pacing of one shot or seam: phases in frames at 30 fps, a parameter table with the critical values marked, pitfalls, the frames to check, and a canvas sketch on the `styles/_swatch` scene API, so any preset's `tokens.json` can skin it (`styles/_swatch/render.sh <dir>`). Style presets keep the look. When the two disagree, the order is user > type doc > project `STYLE.md` > style preset > recipe > playbook, and the CLAUDE.md floors beat all of them.
- 24 seed recipes:
  - rewritten from video-shotcraft (Apache-2.0): its six seams, accelerando cuts, paparazzi flash, drop-blackout slam, and the eight shots of its template film;
  - from HyperFrames' skills: cut-the-curve, zoom-through, the oversized cursor;
  - from this repo's intro film: decode type, one-take world travel, gate-as-door;
  - a flash stitch measured from a public showreel.

  Each recipe names its source in `derived_from` and says what it changed. On-screen text holds follow this repo's reading-time rule (shotcraft's title cards held 1.8 s). Emphasis uses weight or colour, not italics; blur is animated only on canvas; readable small text is at least 44 px; the braking whip-pan is one velocity-continuous curve.

  The 24 files modified from video-shotcraft and HyperFrames follow Apache-2.0 §4. Both upstream licences are copied into `recipes/LICENSES/` byte for byte, with their copyright lines. Each file ends its 来源 section with a 许可 paragraph that says it was modified and names the upstream files and commit, `derived_from` records the same repository, commit and paths, and `recipes/NOTICE.md` lists all 24. Neither upstream has a NOTICE file. Our changes are MIT. The six recipes used in showcases 00 and 04 are marked `tuned`: neither film has a human verdict yet (`battle-tested` needs one, and an independent reviewer's score does not count).
- `recipes/sequences/` holds the pacing grammar and three skeletons: a 15 s launch, a 30 s narrated explainer and a 60 s product film. The grammar is an energy scale of 0–5 (the same one as the beat sheets in `playbook/09-narrative.md`), holds reserved before any motion, seams chosen by the energy jump, and caps such as at most 3 full-frame impacts per film.
- `bin/vh recipes list [--intent … --energy … --engine … --have … --seconds …]` filters on fixed-vocabulary frontmatter; an unknown value is an error, not an empty list. `bin/vh recipes check [file…]` validates the frontmatter, the cross-references, the README index (its energy, length and status columns), the licence notices and the sketches' syntax. It refuses frontmatter that YAML parsers read in different ways (`yes`, `1:30`, dates, `{key:value}`, a key with neither a value nor items), so what passes reads the same in PyYAML. CI runs both.
- `templates/STORYBOARD.md` has optional recipe and QA-frame columns. CLAUDE.md routes "how should this shot move" and pacing requests to `recipes/`. New case study: `cases/promo-video-shotcraft.md`, so the README counts now say 12.

**Hand-drawn engine: videos in BT.709, tagged**
- `engines/ClaudeAnimationBase/render.mjs` (`--clip` and `--encode`) fed Chrome's full-range BT.601 JPEG frames straight to x264, so its videos came out as `yuvj420p` tagged `pc`/`bt470bg`. Chromium plays such files with the BT.709 matrix, and saturated colours shift (up to ~40 levels on pure green). It now converts to limited-range BT.709 and writes all four colour tags, like the HyperFrames and swatch videos. Existing hand-drawn videos keep their colours until they are re-encoded (showcase 01 will be, with its new soundtrack).

**Director mode and decision-first review pages**
- Effort says how hard the agent checks its own work; the new director mode says what the human decides. Ten decisions can be named: outline, style, main character, theme music, voice, script, hook, storyboard, edit rhythm, title and cover. Each is `own` (options with a recommendation, then the agent waits), `review` (one result on the next page, which passes unless the human objects) or `delegate` (the agent decides and writes down why). The setting comes from the chat, a `Director:` line in BRIEF or a default in LOCAL.md; decisions nobody named follow the effort defaults. CLAUDE.md keeps a short section on it; `playbook/01-pipeline.md` has one table in time order of when each decision can first be made, what the agent shows (picture first), how many options and what changing it later costs.
- The three gates stay the floor for standard and studio. Director mode only adds stops, at six checkpoints in time order: E0 style frames, E1 script (the voice is chosen here with the script, so the measured line lengths use it), E2 sound (where the theme plays and where it stays quiet), E3 timing lock (after the audio-first stage), E4 sample chapter, E5 picture lock.
- Every stop is by default one page: `bin/vh review <project> [gate]` turns `out/review/gate-<n>.json` into `out/review/gate-<n>.html` (the latest page is also `index.html`). The page shows, in order:
  - the decisions, at most 3 by default, each with the recommended option, its label, the reason, the change-cost label and the reply syntax;
  - the pictures and options for each decision;
  - one page per storyboard segment: keyframes, that segment's stretch of the animatic (it stops at the segment end), least-sure shots in red, planned changes marked apart from the shots that pass;
  - a folded appendix.

  The page opens from disk with images, GIFs, video and audio, and follows the system's light or dark theme. A video can carry a `poster`; without one, it still shows its first frame before playing. Long "already decided" and "decided for you" lists become compact lists, and appendix text can hold simple pipe tables. The command prints the whole chat message: the decisions, the take-all reply, each least-sure item with its note, and the page path. It warns when two decisions on one page share option ids. A choice or two in plain text can go straight into the chat.
- The page escapes every text and accepts only project files and http(s) links. The file name sets the gate. Exit codes: 1 when the page was written but breaks a rule (no recommendation, a missing file, a refused link …; no chat message then); 2 when nothing was written (bad JSON, a field of the wrong shape, a file that can't be read or written).
- Templates: `REVIEW.md` records the human's exact words (the page spec moved to `playbook/01`); new `DECISIONS.md`, copied into every project, is the one place for creative decisions (NOTES keeps facts, self-review and assets); lean `CHARACTER.md`, `SCRIPT.md` and `PACKAGING.md` for when those decisions come up. BRIEF gets a `Director:` line, and its process no longer says "Stop for approval" whatever the effort.
- CLAUDE.md has a quick path card: what to read and which commands to run for a `quick` film. For quick, `bin/vh new` and the REVIEW.md waiver line now say that decisions the human names still stop, and the skill stops by effort and director mode instead of "at each gate".
- `playbook/01` and the STORYBOARD template no longer ask for a 960×540 animatic: HyperFrames only renders at the composition's size or an integer multiple of it, so draft quality at full size is fine.

**Playbook: narrative, hooks and packaging, composition**
- `playbook/09-narrative.md` (new): the shape of a 60 s–5 min film. Which structure fits which driver (three-act, Story Circle, Story Spine, 起承转合 as the default for explainers, question → answer); fillable beat sheets for 90 s and 3 min with word budgets; the curiosity-gap and energy curves; staging information (2+2, show why it is hard before the answer, signposts, Mayer's principles); setup and payoff; pacing and act-break devices for long films; transitions chosen by how two shots relate; a Subject Bible that keeps a character or a concept on model; what Kurzgesagt, 3Blue1Brown, Vox and Pixar have said about their process; a ten-question narrative self-check. The sources table says what was read and what only came from search snippets.
- `playbook/10-hooks-and-packaging.md` (new): six hook types with Chinese and English formulas, the 0–1 / 1–3 / 3–6 / ≤ 15 s hook ladder, a selection matrix and a hook card for gate ①; ten Chinese and eight English title formulas; five cover layouts (a 3:4 master with the key elements inside the central 1:1); what each platform has said publicly; red lines with the official texts (Article 7 of the CAC's 《网络信息内容生态治理规定》, YouTube's spam policy on malicious clickbait).
- `video-types/02`: platform specs checked on 2026-10-01, official and third-party figures marked apart; what TikTok, YouTube, Douyin, WeChat Channels, Bilibili and Xiaohongshu have said about recommendation and retention; the hook ladder; loop endings by length; cut density from reads (the third-party "TikTok 1.5–3 s" figures are marked unverified); caption styles and why a silent-readable film is not a sound-off film; the cover crop; new don'ts, prompt lines and checks.
- `playbook/11-composition.md` (new, 作曲：篇章、主题与起伏): a four-step method (beat sheet → chapters → dynamic curve → theme map); writing a theme (sentence and period, contour, which pitch tokens to use); development techniques in the current score syntax; dynamics from register, orchestration and density rather than volume; scoring by film type (trailer, narrated explainer, product, Chinese) and SFX in key; checking a score without listening (EBU R128 short-term per section, LRA, section spread and where the loudest section falls, with an ffmpeg-only snippet; the melody's margin over its accompaniment per section, from the engine's own stems); four synthesis pitfalls met while writing the examples; two worked examples, a 58.5 s product arc and a 40 s underscore for narration. Measured the same way, the intro film's v4 score is a plateau: LRA 8.5 LU, loudest section at 28%. It is its own doc so that a plain voiceover job does not load composition theory: `playbook/04` keeps the `score.json` reference and says when to read 11 (`studio` effort, MVs, intro and launch films, films over about 45 s whose structure the music carries, or when the human owns the theme or the BGM).
- Speech rate: `video-types/02` said 4–5 字/秒 and `playbook/04` 4.5–5.5 for the same kind of film. `playbook/04`'s figures stay, as within-sentence rates, and now cite Pellegrino et al. 2011 (read Mandarin with pauses removed: 5.18 syllables/s) and Yuan et al. 2006 (phone conversation: 228–247 characters a minute). Script budgets multiply by 0.85 for pauses (45 s ≈ 170–210 characters). `video-types/02` and `06`, which also said 4–5, now point to that table.
- `playbook/` now has 12 docs: README (both languages), the overview and architecture diagrams, and CLAUDE.md's directory tree and routing table (three new rows: long-form or story-driven films → 09, hooks and covers → 10, music with chapters and a theme → 11) are updated; `video-types/01`, `02`, `03`, `04` and `06` point to the new docs where they apply. The intro film still says 9 on screen; it is being remade.

**Onboarding docs: what the install downloads, a China-network section, a HyperFrames primer** (from a cold-start test that installed and used the repo on a clean machine)
- README (en, zh-CN): the install section now says what is downloaded, where, and how big. About 330 MB for the clone, 210 MB of Node packages, 195 MB for the 30 reference repos (`--no-refs` skips them; `references/fetch.sh <name>` fetches one later), and what the first use pulls in silently: HyperFrames' own `chrome-headless-shell` (about 200 MB in `~/.cache/hyperframes`), the Python packages of the sound tools (about 700 MB in `~/.cache/uv`, about 750 MB more for the local voice), the Qwen3-TTS model (about 2 GB), and about 140 MB of `node_modules` for each HyperFrames project. Sizes were measured on macOS (Apple Silicon). The requirements row for uv no longer says "nothing global". Both READMEs link the wiki, and the install section links its Getting Started page.
- `README.zh-CN.md`: a new 国内网络 section. `npm_config_registry` with npmmirror (the repo's lockfiles point at registry.npmjs.org, and npm swaps the host by default: a fresh `npm ci` of `styles/_swatch` fetched only from the mirror), `UV_DEFAULT_INDEX` with the Tsinghua or Aliyun index (uv's docs mark `UV_INDEX_URL` as deprecated), `HF_ENDPOINT=https://hf-mirror.com` for Qwen3-TTS, and the Chrome download of the first HyperFrames render from npmmirror's binary mirror (`browsers install … --base-url`, or `HYPERFRAMES_BROWSER_PATH` for an installed Chrome). URLs and variable names come from each project's own documentation. It also says where renders fetch Google Fonts (ClaudeAnimationBase's `studio.html`, showcase 02, and HyperFrames itself for any font the page does not declare, the scaffold's `Inter` included) and what happens when it is unreachable, and gives three ways off it: system fonts through `local()` as in `styles/_swatch/fonts.css`, font files in `assets/`, and Fontsource packages from npm (Permanent Marker for the hand-drawn engine, variable Noto Sans SC for showcase 02, whose snapshots came out pixel-identical to the Google Fonts version).
- `install.sh`: the header no longer says "Nothing else is installed globally". It lists what goes where (inside the repo; two small skill files in `~/.claude/skills` and `~/.agents/skills`; npm's own cache) and what the first use downloads later. `--help` prints all of it, the reference-repo progress line and the closing message carry the sizes. Only comments, messages and the line range that `--help` prints changed.
- `engines/README.md`: a HyperFrames primer for 0.8.82 (composition root, `.clip` with `data-start` / `data-duration` / `data-track-index`, `window.__timelines`, a paused GSAP timeline and the driver tween, and how lint, snapshot and render are called). Its example was linted and snapshotted on 0.8.82. `data-track-index` only numbers the lane in the Studio timeline: the render does not read it and it does not set stacking. The known issues got three entries with symptom, cause and fix: the first `render` downloads Chrome and prints only "Checking browser…" in a non-interactive shell; `font-weight: 800` on PingFang SC renders pixel-identical to 600; `--format png-sequence` writes RGBA and leaves the page background out.
- `playbook/02-verification.md`: the determinism section explains what the RGBA PNG sequence means for the check. The `html`, `body` and composition-root backgrounds are not painted (alpha 0), so a sequence converted to mp4 has a black background and a non-deterministic page background cannot show up. The shown `ffmpeg … psnr` command reads about 1.25 dB high on RGBA frames (the alpha channel counts as a fourth, error-free component) and mishandles a sequence that changes between RGBA and RGB partway (ffmpeg rebuilds the filter, prints two summaries and keeps a few lines of `stats_file`). A per-pair loop with `format=rgb24` is given instead.
- `hyperframes snapshot --describe false` wherever a doc or a printed hint tells the agent to run `snapshot`: `engines/README.md`, `playbook/02-verification.md`, the command `styles/_swatch/render.sh --stage-only` prints (and the README note about it), and the copy-paste recipes in the LESSONS of showcases 00 and 02. With `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) set, `snapshot` sends every frame to Gemini by default; the flag was checked in 0.8.82 in both `--describe false` and `--describe=false` spellings. `check --snapshots` does not call Gemini. `engines/README.md` explains why.
- `video-types/02-knowledge-short.md`: word timestamps come from `bin/vh tts … --align gemini` (whisper.cpp when it has to be offline), not FunASR, as in `playbook/04-audio.md`; the caption weight 800 carries the PingFang SC note; the HyperFrames route points at the new primer.

**Swatch renders are byte-identical again (hard rule 1)**
- Two renders of the same swatch gave different media: `halftone-comic` flipped between CRF 24 (1.48 MB) and CRF 26 (1.31 MB) at the 1.5 MB cap, and `fui-hud` got a new poster on every run (about 44 dB between posters). Cause: `styles/_swatch/render.sh` let HyperFrames pick the GPU (`--use-angle=metal`), and Chrome's GPU-accelerated 2D canvas does not rasterise text edges the same way in every process: in a 2- or 3-worker render, a few dozen edge pixels of the lettering differ by one level from run to run (the flying frame counter in `fui-hud`, the title row in `halftone-comic`, plus one clip edge). It is not render order (worker 0 draws frames 0–49 in the same order in every run) and not Chrome's canvas readback noise (the ClaudeAnimationBase cause: the screenshot capture never reads pixels back through JS, and single-worker renders were identical three times in a row). The lossless frames were still ≥ 73 dB apart, but x264 turns a few pixels into a different bitstream from that frame on, and the size-capped CRF and JPEG-quality loops then land on different settings. A second, independent source: HyperFrames captures a 1-worker mp4 render through `drawElement` + `toDataURL` and a 2-worker render through `Page.captureScreenshot`, two paths about 80 dB apart, and `render.sh` chose 1 or 2 workers depending on whether another `hyperframes render` happened to be running.
- Fix: `render.sh` passes `--no-browser-gpu`, HyperFrames' documented deterministic mode (SwiftShader WebGL, 2D canvas and compositing on the CPU; the capture path is then always the screenshot one, whatever the worker count). Evidence: the lossless PNG sequences of `halftone-comic` and `fui-hud` are byte-identical across four runs each (two at 1 worker, two at 3 workers), `determinism.sh` reports 150/150 identical, and `hf.mp4` and `poster.jpg` come out the same bytes at 1 and 2 workers. Seven more swatches (`crt-terminal`, `ink-wash`, `cutout-jazz`, `symmetry-pastel`, `pixel-16bit`, `guochao-festive`, `archival-pan-zoom`) are byte-identical across 1 and 3 workers too.
- A third source, found once the frames were stable: the final `swatch.mp4` encode in `render.sh` (libx264, CRF loop under a 1.5 MB cap with `-maxrate`/`-bufsize`) was not repeatable either. x264's VBV rate control with frame threads gives a different bitstream on every run: four encodes of the same `hf.mp4` and the same audio spanned 1 493 473–1 503 291 B around the 1 500 000 B cap, so `halftone-comic` still flipped between CRF 24 and CRF 26 with identical frames. The encode now runs with `-threads 1` (same rate-control model, the same bytes every time, about 3 s per pass at 720p); without VBV or with slice threads it is repeatable too, but both change the bitrate profile. The music and foley stages were already deterministic (identical WAVs and AAC across runs).
- Every swatch's picture changes once, so the shipped media has to be re-rendered (on the re-scoring branch, not here). Against the GPU render, per frame: `pixel-16bit` identical; `crt-terminal` ≥ 72 dB; `fui-hud` median 52.5 dB, worst 41 dB; `guochao-festive` 51.5 / 39.3 dB; `symmetry-pastel` 48.4 / 29.6 dB (the whip smear); `cutout-jazz` 46.4 / 41.2 dB; `archival-pan-zoom` 43.3 / 40.5 dB; `halftone-comic` 36.4 / 33.5 dB (every dot edge of the SwiftShader-rendered print shader); `ink-wash` 46.6 / 20.2 dB. Mostly this is anti-aliasing coverage on text, shape outlines and dot edges, invisible at 2× zoom. Four swatches change visibly side by side: `scratched-type` (its glyph skeletons are traced from rendered text, so the strokes change; poster frame 29.9 dB), `synthwave-outrun` (the GLSL grain and VHS glitch slicing differ; worst 17 dB at the 4.0 s glitch), and `ink-wash`'s ink-bleed outlines and `cutout-jazz`'s roughened edges take a different shape, because Skia's CPU `feTurbulence` (`lib.inkBleed`, `lib.roughen`) is not the same noise as its GPU one; same character, different wobble. Render time on an M3 Max: `halftone-comic` 22 s at 1 worker / 13 s at 3 (was 17 s / 11 s), `fui-hud` 31 s / 14 s (was 10 s / 6 s); a whole `render.sh` run with music, foley and QA is 20–45 s.
- `guochao-festive`'s committed poster differing from a fresh render (49.9 dB) was the same nondeterminism, not the `lib.motionBlur` change from the v0.2.1 review: the swatch never calls `motionBlur`, and a fresh 2-worker GPU render with today's `lib.js` reproduced the committed `poster.jpg` and `hf.mp4` byte for byte while the next identical run differed from both by 45.6 dB.

**Music parts: fixes from the swatch re-scores**
- Figures and grids no longer drop notes when their step doesn't divide the bar. Half notes in a 5-beat bar played 2 of 3 notes, and none in a 1-beat bar (banker's rounding); a step that starts inside the bar now plays, cut at the bar line. A step that used to ring past the bar line and overlap the next bar's note now stops there.
- A section's `params` (`by_section`) now reach the mono voices (sub808, violin, cello, winds …); before, they were silently ignored. A change of params starts a new phrase.
- A section's `gain_db` is now a level applied after the voice. Before, it lowered the velocity, so a driven sub808 dropped only about 8 dB for −12 dB, and voices whose brightness follows velocity (piano, brass, strings …) also got darker. Textures now take a section's `gain_db` and `vel` too.
- `pattern` as a dict by beats per bar can hold one-bar note lists as well as grids; this used to crash with a `TypeError`.
- A guqin harmonic (`harm`) was 9–15 dB louder than a plucked note at the same pitch and velocity (about 18 dB in the reported case); it is now level-matched: −3.2 to +2.2 dB from the pluck between MIDI 24 and 90 (median −0.3 dB).
- `onset_ms` set in `by_section` now also moves that section's beat-map hits; they had used the part's value.
- New, off by default:
  - `retrigger` for mono voices, so back-to-back notes (808 hits) each get their own attack instead of merging into a legato phrase;
  - `attack` for `seq`;
  - `daluo` and `xiaoluo` (Hz) for the `luogu` kit, and its 大锣 follows the part's `pitch` when one is given.
- Docs: which voices take `damp`, `"figure": null` in `by_section`, `loop` counting the part's own bars, the oompah/waltz bass octave (with a waltz example), and why a `lofi.lp` below about 6 kHz hides hi-hats without the audibility check noticing.
- Scores with only `layers` render the same bytes. Of the 28 re-scored swatches, 7 change: 6 through a section `gain_db` (pixel-16bit also through a half note now cut at the bar line), and ink-wash through the guqin harmonic. The PR lists the per-part levels.

**Code-composed music: instrument parts**
- The 28 style swatches sounded alike because `bin/vh music` had one subtractive palette. A score can now add `parts`: 77 new instruments synthesised in `tools/audio/instruments.py` with no samples, plus the 11 old layer voices. They cover:
  - keys: piano (felt or bright), Rhodes, harpsichord, organ; celesta, music box, glockenspiel, toy piano; marimba, xylophone, vibraphone;
  - plucked: nylon guitar, ukulele, harp, pizzicato, upright bass, pipa, guqin, balalaika, cimbalom;
  - bowed and blown: a string section; violin, fiddle, cello and banhu with glides and vibrato; flute, xiao, whistle, suona, sheng; a brass section and a braam;
  - synths: chip pulse and triangle, 808, CS-80-style pad, drone, polysynth;
  - drums and percussion: kit, brushes, ride, boom-bap, trap and gated drums; gongs and cymbals; a 锣鼓经 kit; clock, metal, scratch;
  - textures: vinyl, tape, hum, wind, rain, room tone.
- Patterns:
  - step grids (accent, ghost, roll, flam, the other stroke) that fit bars of any length;
  - note lists with chord-relative pitches (`c0 s2 d5 +7`);
  - figures: `walking`, `oompah` / `waltz`, `strum`, `alberti`, arpeggios, `ostinato`, `tremolo`, `sustain`, `stab`, `roots`;
  - feel: swing (0–0.33, or 0.5–0.75 as a ratio), seeded `humanize`, `onset_ms`, `beats_per_bar`. A triplet grid (`step: 12`) under 8th swing stays straight.
- Sections: `riser` takes a level, `"riser": {"gain_db": -6}` or `"riser_db": -6` beside `true`, so it can sit under a narration line or an on-screen hit. The default is unchanged.
- Buses: optional stereo with pan; reverb sends into `room`, `plate`, `hall`, `cathedral` or `gated`; master `lofi` and `tape`; per-part delay, drive and ducking.
- A score with only `layers` in major or minor renders the same bytes as before (sha256 checked on all 28 swatch scores and both examples). In other modes (dorian, mixolydian …) the layers now take the same chord roots as the parts, and the 羽 pentatonic when the mode has a minor third; before, they fell back to major.
- Parts are deterministic. Adding or removing a part leaves the stems of parts with another instrument, or with their own `id`, bit-identical. Two id-less parts of the same instrument are seeded by position, so removing one re-seeds the other; the render warns and suggests ids. Two parts with the same `id` are an error.
- Every part must be heard. A part with no notes, or quieter than −40 dBFS in the final file, stops the render and names the part. Loudness is power averaged over the channels, so a hard-panned part is not under-read. `"quiet": true` opts out of the level check, but not the no-notes check.
- Scores are checked before rendering, and a wrong field stops the render with the part's name:
  - an unknown instrument, section, space, duck target, or section name in `by_section`;
  - a duplicate id;
  - a number that is not finite or out of range, e.g. `pan` beyond ±1 or `step` 0;
  - a malformed note list or a strum without strokes;
  - a pitch outside MIDI 0–127.
- Long scores: parts are rendered, mixed into the buses and freed one at a time. A 5-minute stereo score with 7 parts peaks at about 1.1 GB (was 2.8 GB) and renders the same bytes.
- `--example list` shows six new starter scores: jazz, waltz, chip, lofi, guqin, trap. `--instruments` lists every instrument and figure with its knobs.

**README: one picture of the whole project**
- `docs/assets/overview.en.svg` / `overview.zh.svg` replace the mermaid flowchart under "How it works". The new diagram shows the path from a one-sentence request to the final film, with the three human gates, sound-first rendering, the self-review loop and gate ③ sending the film back. Beside it, it shows what the repository provides: knowledge, tools and engines, and the records that feed lessons back into the playbook. Both files follow the reader's light or dark theme.

**Narration: found by a second review of v0.2.1 and the PRs since**
- `bin/vh tts … --align gemini` and `--join` no longer lose the take when a transcription fails for good (a daily-quota 429, a 5xx that outlasts its retries, the network): the key is checked before anything is synthesized, `voiceover.<lang>.wav` and the timeline are written right after synthesis, a line the ASR could not check keeps its measured timing with `asr: {"error": …}`, and the command exits 1 with the reason. `--resume` then continues that run: it synthesizes only the files the run did not get to (a synthesis that fails midway is reported the same way), reuses the ASR of the lines that succeeded (`vo/<lang>/*.asr.json`) and redoes the rest, without paying for the finished lines again; with `--join`, a block that could not be transcribed stays whole in `vo/<lang>/_blockNN.wav` and its lines share the block's span until then. The run's script, provider, voice, `--instruct` / `GEMINI_TTS_STYLE` and join mode are recorded in `vo/<lang>/_run.json`; `--resume` refuses a mismatch and names it (the timing flags may change). A file synthesized again on `--resume` gets a fresh transcription, a plain run (no `--align`, no `--join`) that failed midway continues the same way, and a finished plain run gets `--align gemini` without synthesizing again. Before, a missing key or a quota error after the last line was synthesized exited with nothing written.
- `--beats` with a map that has no grid for `--snap` (for example only `downbeats` under the default `beat`) is an error instead of silent plain `--gap` spacing; when the narration outlives the grid, the lines past its end follow `--gap` and say so once (they used to be packed at `--min-gap`, 0.12 s).
- A 429's "retry in Ns" is read from the first 8 KB of the body, not the first 500 bytes: a quota message listing two exceeded metrics put it past that cut, so the wait fell back to 60 s and a daily quota ("retry in 3600s") was retried five times before failing.
- `say` reads a line that starts with `-` (`-1 是负数`) instead of rejecting it as an option.
- With `--join`, a line the ASR skipped entirely (nothing heard between its neighbours) got a zero-length span, a zero-length `vo/<lang>/NN.wav` and a header-only WAV in the vocabulary re-check; it now gets a 0.1 s span around that point (still flagged, similarity 0), consecutive skipped or `……` lines get one slot each, and cuts shorter than 50 ms are not re-checked.
- Word units keep the last piece of a line: `"Hello world ."` used to drop the final `.` and `"Hi 👋"` the emoji, and an interior tail kept its leading space (`"a , b"` gave `"a ,"`, now `"a,"`). `--align` and the elevenlabs word grouping share this.
- Edge trimming ignores a click or pop that stays inside one 10 ms window, before or after the voice: see the trimming entry under "Defaults settled on a Mac".
- `playbook/04`: the `bin/vh qa` digital-silence rule names the checked span; `gemini-lite` is marked as sharing `gemini`'s code path, not separately tested; the `--beats` example uses an unambiguous path and covers the two grid cases above.

**Tools and docs: found by a second review of v0.2.1 and the PRs since**
- `tools/ci.sh`'s ban on BSD-only / GNU-only commands only matched a command at the start of a statement: `for f in …; do sed -i '' …; done`, `if …; then stat -f %z …; fi`, `… | xargs sed -i '' …` and `sudo sed -i …` all passed. It now also looks after `if`, `while`, `until`, `do`, `then`, `else`, `elif`, after `{`, `(`, `!` and a case arm, and behind the wrappers `xargs`, `sudo`, `exec`, `env`, `time`, `nohup`, `nice` and `command` with their flags, `VAR=value` tokens and arguments (`sudo -u root sed -i`, `env FOO=1 sed -i`, `nice -n 5 sed -i`). Comments, single-quoted strings, double-quoted strings without `$` or backticks and heredoc bodies are blanked before the match by a small quote-aware scanner, so `echo "sudo sed -i"` or a prose line inside a heredoc is no longer a hit; a heredoc opens only at a `<<name` outside quotes and comments with whitespace before it (`<<<`, `$((1<<n))`, `"a <<b"` and a `<<EOF` in a comment do not), and its terminator is matched ignoring leading tabs and trailing blanks, so a stray `<<` cannot silently blank the rest of a file.
- `render.mjs --encode` refused to run on a machine without Chrome although it never opens a browser; the Chrome check now comes after the encode path.
- `bin/vh doctor` called uv optional; `bin/vh tts`, `beats`, `music`, `sfx`, `qa` and `sheet` run through it, so a missing uv is now a red ✗ that names them. The README's requirements table (both languages) says the same.
- `bin/vh mix` was not deterministic with ffmpeg 8.0.1: twelve runs of one ducked mix gave six different files, differing from about a second before the end, and a voice bus that ended before the music left the last part of the mix silent. `sidechaincompress` ends its output as soon as its main input's frames are consumed and drops whatever its sidechain FIFO has not matched yet, so with the music and the key decoded in separate threads the ducked music lost a run-dependent tail; the loudness pass measured that truncated mix too. Now every bus is padded or trimmed to the longest one, the ducker's two inputs come from one merged stream (`amerge` → `asplit`, one frame of skew at most) padded a second past the end, the ducked music is trimmed back, and the mix is pinned to 48 kHz so the loudness pass (loudnorm only takes 192 kHz and used to pull the whole graph up to it) runs the same graph as the output pass. Repeated runs are byte-identical, the output is exactly as long as the longest bus, and a mix that came out complete before is byte-identical to it; the runs that were truncated now match those.
- `bin/vh mux` fades the last 40 ms out when it trims a longer audio track to the picture, instead of cutting it hard; a shorter track is still padded with silence.
- `bin/vh mix` with an argument that is not `key=value`, an unknown key, a non-numeric level (`music_db=abc`) or an unknown `duck=` value prints the usage or a one-line error instead of a traceback or silently ignoring it; `-h` / `--help` print the usage.
- `bin/vh sfx place`: `"sfx"` may be a path to any file ffmpeg decodes, not only `.wav`; a missing file, an undecodable file or an unknown built-in name is a clear error instead of a `KeyError`. A `--lib` name is looked up first, so a name with a dot (`v2.1` → `DIR/v2.1.wav`) still works.
- Docs: `styles/README.md` no longer lists the three v0.2.0 review items as unfixed (they were fixed in v0.2.1; the published swatches pass `bin/vh qa scan`); `engines/README.md` records that the CanvasNoise fix was verified on a real GPU (macOS, Metal) instead of "not yet verified".

**ElevenLabs word timing**
- `bin/vh tts … elevenlabs` wrote every character as a "word": an English line became one entry per letter (90 for a 20-word sentence), so word-by-word captions flashed letters and the documented "same shape as --align" was not true. Character timestamps are now grouped into the same units as `--align gemini`: a Latin word or number each, a CJK character each, trailing punctuation kept on the word before it, opening quotes on the word after.

**Repository and community files**
- Releases `v0.1.0`, `v0.2.0` and `v0.2.1` are published on GitHub, with notes taken from this file, and version tags are protected by two rulesets (`.github/rulesets/tags-create.json`, `tags-immutable.json`): only admins can create a `v*` tag, and nobody, admins included, can move or delete one. The rules are split because GitHub applies bypass permissions per ruleset, not per rule. CONTRIBUTING describes how to cut a release.
- GitHub now detects the license as MIT: `LICENSE` holds only the standard MIT text, and its note on third-party components moved to the top of `ACKNOWLEDGMENTS.md` ("License scope").
- Issue forms (bug report, feature request, style proposal), a pull request template with the CONTRIBUTING checklist, `SECURITY.md` (private vulnerability reporting; what counts: key leaks, `fetch.sh` neutralisation bypasses, injection through `bin/vh`), `CODE_OF_CONDUCT.md` (Contributor Covenant 2.0), `CITATION.cff` (matches the README's BibTeX), a Sponsor button pointing to the README's support section, and Dependabot for the CI workflow's actions (npm left out: HyperFrames stays pinned to 0.8.82).

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
- Auto-merge is on (squash only): a PR can be set to merge itself once both required checks pass, so nobody has to wait on CI. The ruleset still applies in full. `.github/rulesets/main.json` now matches the live ruleset field for field.

**Camera language for video models**
- `playbook/05`: how to write camera moves a video model can execute (four layers, start → path → end → constraints, a trigger between two moves), after Adrian Punk's *AI 视频运镜词典*. `playbook/07` breaks camera motion down the same way; `playbook/08` treats one-take camera paths as a choreography and handheld drift as low-frequency noise.

**Generated clips in the hybrid pipeline: method apart from numbers**
- `playbook/05` is now organised by task: taking in a generated clip, matching it to code-rendered footage, keying, character consistency, artefact QA, cost. Specs and prices moved to the dated `references/genvideo-market.md`, licences and disclosure to `references/genvideo-ledger.md`.
- The market page was checked against the official pages on 2026-10-01. It corrects one claim: Seedance 2.5 tops out at 720p on fal only, Runway has had a 1080p tier since 2026-08-15. Sora's API was removed on 2026-09-24.
- New tools, run from the repo root: `tools/motion.py` (window and prominence of the motion peak, frames repeated inside motion), `tools/match_grade.py` (Lab statistics to a `.cube` LUT), `tools/grain_est.py` (grain σ). Checked on synthetic clips; no video model has been called.
- The grain in `playbook/08`, `noise=alls=6:allf=t`, is σ ≈ 3.5 after x264, not 1.8 (that is the `t+u` variant); the `playbook/05` table lists both, measured on a flat grey clip.
- `playbook/02` gets a "色彩标签" section: the ffprobe check, the BT.709 encode command, and why it matters (eight test swatches up to 21 levels off, pure green 40; Chrome reads a file tagged only `bt470bg` with the BT.709 matrix, ffmpeg does not). Two committed showcase finals are off the contract and are not touched here.

**Defaults settled on a Mac (Apple M3 Max)**
- `bin/vh mix`: the default `duck_ratio` is now 1.6 (was 6). With narration that pauses ~0.25 s between lines, 6 and 3 made the music drop out between lines (`bin/vh qa`: 3 and 2 pumping dips); 1.6 had none and sounded best in a listening test.
- `bin/vh tts` without a language: an English-only script is now spoken in English (English voice, English ASR, `voiceover.en.wav`) instead of by the Chinese voice. A script with any Chinese line stays `zh`, so one narrator reads it all; `--lang zh` keeps the old behaviour.
- `bin/vh tts` trims the silence a provider leaves before and after each line (below −50 dBFS, keeping 30 ms before the voice and 80 ms after). qwen's English voice Ryan started every line with ~0.45 s of silence and edge ended every line with ~0.85 s, so gaps were far longer than `--gap` and a beat-snapped line started speaking late. On a Mac, 5-line takes got 4–5 s shorter with Ryan, 2 s with Aiden and 5 s with edge; `say` has no edge silence. The threshold is −50, not −45, because −45 cut up to 70 ms of a soft f or h onset (40 lines measured; local Whisper heard every first and last word after trimming). Breathing or mumbling before the first word is louder than that and stays. A loud 10 ms window counts as voice only when a neighbouring window is loud too, so a click or pop that stays inside one window does not stop the trim, before or after the voice (a burst across two windows still counts). With `--join`, only each block's edges are trimmed. `--keep-edges` keeps the old behaviour.
- qwen's default English voice is now Aiden (was Ryan), chosen in a listening test. With the 0.6B model, Ryan went wrong on 9 of 40 lines across 8 runs (several seconds of mumbling before the first word, or a 5-word line running on for 45 s); Aiden had none in 25 lines and reads about 15% faster. `--voice Ryan` still works.
- `bin/vh tts <project> --provider edge` (tts.py's own flag spelling) installed the qwen dependencies instead of edge-tts and failed with `No such file or directory: 'edge-tts'`; `--provider dashscope` failed the same way. `bin/vh` chose the dependencies only from the positional provider; it now reads `--provider X` and `--provider=X` too.
- `bin/vh doctor` marks missing optional tools (uv, latex) with a yellow `!` instead of a red `✗`.
- `--align gemini` failed on any script of more than 10 lines on Gemini's Tier 1, which allows 10 transcribe calls a minute: a 429 was retried after 3 s and 6 s, then the run exited without writing `voiceover.wav` or the timeline. A 429 now waits as long as the API asks (`Retry-After`, or "retry in 59s" in the message) and is retried up to 5 times; a 12-line script now finishes in 155 s. A 429 asking for more than 90 s (a daily quota) fails at once instead of retrying. This covers every Gemini call, including TTS and voice design.
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
