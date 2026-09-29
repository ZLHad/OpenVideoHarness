# Changelog

## Unreleased

**Linux fixes, found while setting up a cloud (Ubuntu 24.04) machine**
- `bin/vh` used the macOS-only `sed -i ''`, which GNU sed reads as a file name. On Linux, `new … --effort` silently kept `standard` in BRIEF.md, and `hf-init` left GSAP on the CDN, so `hyperframes render` refused to run offline. Both now go through a portable `sedi` helper.
- `styles/_swatch/package-lock.json` pinned every package to `registry.npmmirror.com`, so `npm ci` failed wherever that mirror is unreachable. It now records `registry.npmjs.org`, which npm swaps for whatever registry you have configured, so mirror users are unaffected.

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
