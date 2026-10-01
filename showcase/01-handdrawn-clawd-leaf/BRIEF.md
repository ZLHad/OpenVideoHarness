# BRIEF — "Clawd and the Leaf"

Approval gates: the user explicitly authorized skipping both gates for this showcase ("still write BRIEF.md and STORYBOARD.md with reads and timings before coding"). Both files are written before any scene code and serve as the review contract.

> 2026-10-01: the picture below was made and finished silent, as briefed. A cartoon score and foley were fitted to it afterwards on the same 120 bpm grid (README › Soundtrack), and the video was re-encoded to limited-range BT.709 at the same time (NOTES); the timings here are unchanged.

## Spec
- Output: 1920x1080, 24 fps, exactly 12.0 s (288 frames)
- Engine: ClaudeAnimationBase (p5.js + p5.brush), copied into this project by `bin/vh new handdrawn clawd-leaf`
- Platform / audience: README showcase for OpenVideoHarness (GitHub page, autoplay GIF + MP4), watched muted
- Language: none on screen; narration: none; made silent (no audio track), soundtrack added afterwards (README › Soundtrack)
- Deliverables: final.mp4, preview.gif (<6 MB), sheet.png, plus BRIEF / STORYBOARD / NOTES / LESSONS and scene source

## Content
- Spine (one line): Clawd wants to film a falling autumn leaf with a tiny hand-cranked movie camera, but the wind snatches the leaf every time Clawd frames it, so Clawd gives up and checks the camera — and the leaf lands on Clawd's own head, right in the viewfinder. Clawd films itself, delighted.
- Recurring motif: the viewfinder frame (rounded rectangle with corner brackets). The film opens by irising out of a viewfinder on the leaf and closes by irising into a viewfinder on Clawd wearing the leaf.
- What the viewer should know/feel at the end: the thing you chase lands on you when you stop chasing; a small warm laugh.
- Source material: the one-paragraph premise from the user (see showcase README). No facts, no data.

## Style
- Refs: hand-painted watercolour cartoon shorts; ClaudeAnimationBase model sheets (docs/emotions.jpg, docs/views.jpg) for Clawd on-model.
- Explicitly NOT: the demo's night sky / hills / star story; lettering of any kind; 3D spins; plain p5 shapes; digital glows.
- Palette: warm autumn — paper cream, apricot sky, ochre/rust foliage, olive-ochre ground, walnut camera, ONE hero accent: the golden maple leaf. No pure #000/#fff (PAL.ink / PAL.cream).
- Type: none (no text).

## Motion defaults (override per type doc)
Type doc 07 / ANIMATION_GUIDE win over the template defaults here: cartoon register, so overshoot, takes, beat-locked idle motion and boil ARE wanted (the template's "no bounce/elastic, no idle breathing" line is for HyperFrames promo work and is overridden). Anticipation before every fast action, holds after every important one.

## Text rules
No text at all. Reactions are painted emotes only.

## Determinism
Every frame is a pure function of t. No Math.random / Date.now; hash(i) for stable values; boilSeed(key) per element.

## Process
1. STORYBOARD.md with reads and start–end times (written before code; gate skipped by user).
2. No audio while the picture was made: bpm 120 (BEAT = 0.5 s) sets the pulse; key hits land on beats where possible. (The score added later runs on this same grid.)
3. Build shot by shot; per shot a contact sheet, strips for key motions and every seam, crops for faces and prop contacts; log in NOTES.md; fix before moving on.
4. Deliver: MP4, GIF, sheet, NOTES, LESSONS, and the 2–3 spots I'm least happy with.

## Acceptance
- [ ] 12.0 s ±1 frame, 1920x1080, 24 fps; the picture render has no audio stream (the soundtrack is muxed on afterwards)
- [ ] Story reads muted from the frames alone: leaf falls → snatched → snatched again → lands on Clawd in the viewfinder → delight
- [ ] Every read ≥ 12 frames; no two important reads overlap
- [ ] Transition at every seam including first and last frame; no text anywhere
- [ ] Clawd on model in every shot; prop (camera) touches the arm tip; leaf touches the head when it lands
- [ ] preview.gif < 6 MB

## TYPE
+ TYPE: hand-made short. Engine: ClaudeAnimationBase copied into this project. Read ANIMATION_GUIDE.md fully first; its rules apply unless I say otherwise.
Idea: Clawd tries to film a falling autumn leaf with a tiny hand-cranked movie camera; the wind keeps snatching the leaf just as Clawd frames it; it ends with the leaf landing on Clawd's head in the viewfinder — Clawd films itself, delighted. Length 12s, bpm 120.
Character: Clawd (default design) + a new prop: a tiny hand-cranked movie camera (walnut box, two reels, lens barrel, side crank) with drawn key views (lens right / lens toward viewer / lens left).
Budget: at least one sheet per shot, a strip for every key motion and transition, a crop for every face that carries the story.

<!-- from 07-hand-drawn.md -->
