# BRIEF — OpenVideoHarness launch film (README hero)

<!-- Gate 1: the user authorised skipping approval gates for this showcase ("still write BRIEF/STYLE/STORYBOARD before coding"). Written 2026-09-28 before any scene code. -->

> 2026-10-01: the picture below was made and finished silent, as briefed. A code-composed score and foley were fitted to it afterwards (README › Soundtrack); the timings here are unchanged.

## Spec
- Output: 1920x1080, 30 fps, exactly 20.0s (600 frames)
- Engine: HyperFrames 0.8.82 (HTML + GSAP 3.14.2), installed locally in this project (`npm i -D hyperframes@0.8.82`)
- Platform / audience: GitHub README hero (autoplay GIF + linked MP4). Developers who already use Claude Code or Codex; watched muted.
- Language: en on-screen copy; the real UI shown (CLAUDE.md routing table) stays in its original Chinese. Narration: none.
- Deliverables: final.mp4, preview.gif (800 px, 15 fps, < 8 MB), sheet.png, poster.png (README top), composition source.

## Content
- Spine (one line): a coding agent can now make videos, but it can't watch them — so OpenVideoHarness gives it a studio where every frame is code it can render, look at and fix.
- Recurring motif: a running timecode `t 00.00 · f 000` in the lower-left — every frame literally prints the t it is a function of; it lands on `t 19.97 · f 599` under the wordmark.
- What the viewer should know/feel at the end: "one command, the agent picks the right playbook, and it reviews its own frames" — and the name OpenVideoHarness.
- Source material (real, from this repo):
  - `bin/vh new promo launch-film` and its actual stdout (first: the run that created this project; after the rename: a re-run into a throwaway project, see NOTES);
  - the tree that command created (BRIEF.md … TASTE_CHECKLIST.md, audio/, assets/, out/check/);
  - the `CLAUDE.md` routing table, rows 01–05, verbatim;
  - the contact sheet of this film's own draft (`bin/vh sheet`), and the real FAIL line from NOTES.md;
  - counts: 8 video types (`video-types/`), 10 stages (`playbook/01-pipeline.md` 十阶段流程 0–9; called 九阶段 when this brief was written), 3 review gates (CLAUDE.md step 5; 2 when this brief was written, see NOTES), 20 taste checks (`templates/TASTE_CHECKLIST.md`).

## Style
- Refs: Linear / Vercel launch pages (hairline UI on near-black); `hyperframes-launches/timeline-launch` (cursor-led, 3-act, 15–20s); `cut-the-curve` seams.
- Explicitly NOT: purple-cyan gradients, glowing orbs, glassmorphism, gradient text, bouncing, six equal cards, fake dashboards, brand logos.
- Palette: bg #0A0A0B, fg #EDEDEF, ONE accent #FFB224 (amber "tally light" = what the harness is acting on now)
- Type: SF Pro (system-ui) 400/600 + SF Mono (ui-monospace); hierarchy by weight/size only

## Motion defaults (override per type doc)
Entrances easeOutExpo cubic-bezier(0.16,1,0.3,1) / power3.out; exits ease-in at ~75% of entry; entries <=0.8s; total stagger <=0.5s. No bounce/elastic, no idle breathing loops, no crossfades between scenes; transitions grow out of content; 0.3–0.75s stillness before each climax.

## Text rules
<= 8 words on screen at once (UI text inside a pane excluded, but its key read gets >= 44px after the push-in); each copy block visible >= 2.3s (20s film, 7 beats — see NOTES); min sizes: display 96px, support 44px; everything inside the safe box x 96–1824, y 54–1026.

## Determinism
Every frame is a pure function of t. No Math.random / Date.now / CSS transitions / @keyframes; grain offsets from a seeded hash of the frame index; no state carried between frames.

## Process
1. STORYBOARD.md with reads and timings (gate skipped by user, file still written).
2. No audio while the picture was made (silent film): timings come from reads, not from a track. The soundtrack was fitted to the finished picture later (README › Soundtrack).
3. Build scene by scene; `hyperframes lint` / `check` / `snapshot`; draft render → `bin/vh sheet` + seam strips; critique against TASTE_CHECKLIST.md into NOTES.md; fix; final render.
4. Uncertain facts and creative decisions go in NOTES.md.
5. Deliver: MP4, GIF, sheet, poster, NOTES.md, the spots I'm least happy with.

## Acceptance
- [ ] Hook readable within 1s, muted
- [ ] Every on-screen string, path and number exists in the repo (checked against files)
- [ ] 20.0s ±0.1s, 1920x1080, 30 fps; the picture render has no audio stream (the soundtrack is muxed on afterwards)
- [ ] Each feature beat readable in ~1s; a cursor click causes each feature beat's action
- [ ] `hyperframes lint` 0 errors; `check` reviewed; no black/freeze segments except the deliberate end hold
- [ ] GIF < 8 MB

## TYPE
+ TYPE: product launch film. 1920x1080 30fps 20s, **silent** (user: no TTS/music) — so no SFX; beats are cut to reads, not to music. (Picture phase. Music and SFX were added on 2026-10-01, fitted to these cuts.)
Register: Linear/Vercel: near-black #0A0A0B, 1px hairlines, blueprint grid at 6% opacity. Font: SF-like grotesk (SF Pro via system-ui) + SF Mono. No gradient text, glassmorphism, or purple-cyan gradients.
One continuous virtual camera; camera moves 1.5–3s easeInOutCubic, about half your default speed; motion blur on fast moves; light grain.
Beats: hook promise (0–3s) → problem (1 beat) → 3 feature beats, each = the real UI doing the thing, triggered by an oversized cursor click → proof count-up → 0.5s stillness → logo lockup.
Use real copy/assets from this repo; recreate the UI accurately; no placeholder text or invented numbers.
Re-framed 4:5 / 9:16 cuts: out of scope for this showcase (README hero only) — noted in NOTES.

<!-- from 03-product-promo.md (edited: music/SFX and multi-aspect lines adapted to this brief) -->
