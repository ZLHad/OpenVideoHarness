# Changelog

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
