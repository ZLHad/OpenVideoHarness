# BRIEF — OpenVideoHarness intro film (README hero + X launch post)

> **v2 (2026-09-29, after gate ①: "一镜到底 动画动效 音乐动态字等风格 叙事感 科幻感大片感").** What changed from the v1 draft below:
> - **Length:** 69.333 s = 2080 frames = 26 bars at **90 BPM** (1 beat = 20 frames, 16th = 5 frames).
> - **Picture:** ONE continuous camera through one sci-fi world, "the archive of frames". HyperFrames with a Three.js layer; showcase films are VideoTextures on floating screens.
> - **Sound:** a code-composed cinematic hybrid score (one braam, at 26.667 s) plus synthesized SFX.
> - **Type:** bilingual kinetic type lives in the world, English hero with a Chinese subline; soft zh/en SRT.
> - **Where things live now:** camera path and reads in STORYBOARD.md, world rules in STYLE.md, decisions and review log in NOTES.md.
> - **Kept from v1:** audience, message and acceptance criteria. Replaced: the 28-bar 59.7 s outline and the flat-UI register sections.

<!-- Gate ① draft, 2026-09-29. Written before any scene, audio or render work. Status: waiting for the human (REVIEW.md 关卡 ①).
     Route: promo (video-types/03) is primary; beat-locking rules borrowed from video-types/04 (music-driven). -->

## Spec
- Output: 1920x1080, 30 fps, exactly **59.733 s = 1792 frames = 28 bars × 64 frames at 112.5 BPM** (request allows 45–75 s).
- Engine: **HyperFrames** (HTML + GSAP) is the only compositor. Pin locally: showcases verified 0.8.82; the scaffold pulled 0.8.84, which we keep only if it passes the same lint + render smoke test. Every `npx hyperframes` call is prefixed with `HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1`. Showcase finals are composited as muted `<video>` clips. No new p5.brush or Manim renders.
- Platform / audience:
  1. GitHub README hero (README.md and README.zh-CN.md): developers who use Claude Code / Codex. GIF teaser autoplays; the MP4 is linked.
  2. X/Twitter launch post: tech Twitter, including the Chinese AI-video community. The video autoplays **muted** in the feed.
  → It must read with the sound off. Sound on is the reward: cuts, hits and sonified UI events are locked to the beat.
- Language: bilingual kinetic type, switched by a `lang` variable. Master `lang=en` (English hero line + Chinese subline) for README.md and X. Second render `lang=zh` (Chinese hero + English subline) for README.zh-CN.md and B站. Soft zh/en SRT on both. **Narration: none in the master** (option A, pending the human's decision; options B/C reuse SCRIPT.md).
- Audio: code-composed soundtrack (`bin/vh music`, `audio/score.json` versioned with the film) + synthesized SFX (`bin/vh sfx place`, `audio/events.json`) + a project-local extension of `music.py` (copied into `audio/`; the shared harness file is untouched) for 4 signature moments. Mixed with `bin/vh mix` to −14 LUFS, true peak ≤ −1.5 dBTP.
- Deliverables: `out/final-en.mp4`, `out/final-zh.mp4` (each muxed with soft zh/en SRT), `out/poster.png` (last frame), `out/teaser.gif` (bars 1–5 ≈ 0–10.7 s, grain-free, ≤ 8 MB, for the README), `out/sheet.png`; `audio/score.json` + `events.json` + stems. Later / optional: a zh-narrated edition (option C) and a re-framed 9:16 cut.

## Content
- Spine: coding agents can now write a film as code: every frame is f(t), one sentence goes in and a film comes out. But one-liners are stunning once and unreliable after that. OpenVideoHarness routes, gates and self-reviews the agent so the result is good every time, and this film (soundtrack included) is the proof.
- Recurring motif:
  1. **This film's own contact sheet.** It opens as a grid of the film's own frames rendering in scrambled, seeded order (part 1 = render). It returns in part 6, sorted, as the review sheet (= review).
  2. **The HUD timecode from showcase 00, now with the music grid**: `t 00.00 · f 0000 · ♩ 01.1`. It ends at `t 59.70 · f 1791 · ♩ 28.4`.
- What the viewer should know/feel at the end:
  - video can be code;
  - OpenVideoHarness makes the agent reliable at it: 8 types, 3 human gates, the agent reads its own frames, 20 taste checks;
  - the results are real;
  - even this film's music is code;
  - how to start: `bin/vh` + github.com/ZLHad/OpenVideoHarness.
- Source material (all real, from this repo; ledger in NOTES.md):
  - README.md / README.zh-CN.md copy: the what-is, "stunning but not reliable", the tagline, the showcase facts;
  - CLAUDE.md routing table (verbatim), `templates/REVIEW.md`, `templates/TASTE_CHECKLIST.md`;
  - this project's own gate artifacts: REVIEW.md, `out/check/storyboard.png`, the draft sheet;
  - `showcase/*/media/final.mp4` ×4;
  - `projects/2026-09-28-clawd-leaf/out/check/A_sheet.jpg` (round-1 sheet), `showcase/01-handdrawn-clawd-leaf/media/sheet.png` (final), and the FAIL lines in `showcase/01-handdrawn-clawd-leaf/NOTES.md`;
  - from showcase 02: the `draw(t)` code in `index.html` and the request's topic line (from its README).

## Outline (28 bars; bar k starts at (k−1) × 2.1333 s)
| # | Time · bars | Part | Viewer learns |
|---|---|---|---|
| 1 | 0:00.0–0:04.3 · 1–2 | Hook: this film's frames render into a grid in scrambled order, then sort themselves | every frame is a function of time; any order gives the same film |
| 2 | 0:04.3–0:10.7 · 3–5 | Code2video: dive into the 0:04.27 tile → real request → Opus 5.5's code streams → frames → film | the model writes the program, not the pixels; one sentence in, a film out |
| 3 | 0:10.7–0:14.9 · 6–7 | Twist: "Stunning, once. / Dependable? Not yet." (README wording) + 3 deliberate failures stamped #11 / #10 / #19 FAIL; 0.53 s silence | one-liners are not reliable; the three usual failures |
| 4 | 0:14.9–0:34.1 · 8–16 | Harness: name on the drop; router (8 rows on 8ths) · 3 gates (music stops, cursor approves) · self-review (round-1 sheet → FAILs → 20-item checklist → round-3 PASS) | what OpenVideoHarness is and the 4 mechanisms |
| 5 | 0:34.1–0:49.1 · 17–23 | Proof: 01 Clawd (2 bars) → 03 Fourier (2) → 02 Doppler (2) → 00 launch film (1, band drops out) | real films: 4 types, 3 engines |
| 6 | 0:49.1–0:53.3 · 24–25 | Reveal: this film's own sheet; 4 lines of score code light and each stem enters on its beat | this film too; even the soundtrack is code |
| 7 | 0:53.3–0:59.7 · 26–28 | CTA: final hit → wordmark + tagline → `bin/vh new <type> <slug>` → github.com/ZLHad/OpenVideoHarness → hold | name, where to get it, first command |

## Style
- Refs (2–3 named works):
  - `showcase/00-promo-launch-film`: the visual system to continue;
  - Ryoji Ikeda, *test pattern* series: picture and sound from one data source, hard sync (the discipline, not the strobe);
  - `hyperframes-launches/sfx-music-launch` + PDoom as the rhythm yardstick.
- Explicitly NOT:
  - AI-trailer slop: purple-cyan gradients, glow orbs, glassmorphism, particle swirls, ✨ icons, chrome 3D logos, trailer braams. The one exception is the part-3 gag: at most 6 frames, stamped #10 FAIL;
  - feature-card grids, slide decks, screen-recording tours;
  - chiptune or random-arpeggio "code music";
  - lyric-slideshow type (same entrance for every word, typewriter everywhere).
- Palette: bg #0A0A0B, surface #111113, hairline #26262B, grid rgba(237,237,239,.06), fg #EDEDEF, muted #8B8B94, dim #55555D.
  - ONE accent #FFB224, meaning "what the harness is acting on now". No pure #000/#fff.
  - Showcase footage keeps its own colours inside hairline frames. It is exempt from the one-accent rule (documented exception, checklist #9).
- Type: SF Pro via `system-ui` (400/600); "LF Mono" = `@font-face` local SF Mono / Menlo (plain `ui-monospace` renders proportional, see engines/README); CJK = `@font-face` local PingFang SC.
  - Sizes: hero 150–200px, subline 44–56px, pane UI 26–32px.
  - Any must-read UI line is ≥ 44px after push-in.

## Motion defaults (override per type doc; cartoon / hand-drawn projects follow ANIMATION_GUIDE.md instead — overshoot, takes and beat-locked idle motion are required there)
Entrances easeOutExpo cubic-bezier(0.16,1,0.3,1) / power3.out; exits ease-in at ~75% of entry; entries <=0.8s; total stagger <=0.5s. No bounce/elastic, no idle breathing loops, no crossfades between scenes; transitions grow out of content; 0.3–0.75s stillness before each climax.
Film-specific:
- One continuous virtual camera; content flows LEFT (the pipeline reads left → right). Camera moves take 1.5–3 s easeInOutCubic, then hold (no drift).
- Exactly 3 transition kinds:
  1. beat cut on a bar line;
  2. cut-the-curve LEFT;
  3. tile zoom-through (sheet tile ↔ footage or live frame).
- No general flash more than 3 times per second (WCAG 2.3.1).

## Rhythm contract
- 112.5 BPM × 30 fps: beat = 16 frames, 16th = 4 frames, bar = 64 frames. Every subdivision lands on a whole frame (120 BPM would give 3.75 frames per 16th).
- Scene changes on bar lines; hero words on beats; UI micro-events (row scans, ticks, typing) on 16ths.
- All times are read from `audio/music.beats.json` + `audio/events.json`, never typed by hand.
- Before delivery: onset cue check of the mix against the beat map, target ≤ 1 frame.

## Text rules
- On screen: ≤ 8 English words or ≤ 16 CJK chars per line.
- Duration: hero blocks stay ≥ one bar (2.13 s); the 3 key claims (f(t) · not reliable · the name) stay ≥ 2.5 s.
- Min sizes: hero 96px, support 44px.
- Safe box: x 96–1824, y 54–1026.
- Real UI text inside panes only has to be recognisable (checklist #5 note).

## Determinism
Every frame is a pure function of t. No Math.random / Date.now / CSS transitions; seed all noise; no state carried between frames.
- Part 1's tile render order comes from a seeded hash.
- The soundtrack re-renders bit-exact from score.json + seed.
- The self-sheet (parts 1/4/6) is built by a script in two passes (draft → `bin/vh sheet` → baked asset → final), like showcase 00's `tools/draft-v1.sh`.

## Process
1. Gate ①: this BRIEF, the REVIEW.md packet and the SCRIPT.md draft. **Stop.**
2. Gate ②:
   - STYLE.md;
   - STORYBOARD.md with reads;
   - `out/check/storyboard.png` (one keyframe per shot);
   - a ~20 s music sketch (bars 8–17) for the human to listen to.
   **Stop.**
3. Audio first: `score.json` → `music.wav` + `music.beats.json`; `events.json` → `sfx.wav`; VO only if option B/C is chosen. Re-time shots from the beat map.
4. Build:
   - the director builds part 4 (the densest) as the reference;
   - subagents may build part 5 (footage) and parts 1/6 (self-sheet) against STYLE + STORYBOARD;
   - for every part: lint / check / snapshot → draft render → sheet + seam strips + crops → TASTE_CHECKLIST notes in NOTES.md → fix.
5. Gate ③: draft + sheet + the 2–3 weakest spots. Then the finals, GIF, poster and LESSONS.md.

## Acceptance
- [ ] 59.733 s ±1 frame (1792 frames), 1920×1080, 30 fps, H.264 yuv420p + AAC 48 kHz
- [ ] Muted test: every claim readable on screen; the hook is moving by 0.3 s; the first frame is not empty
- [ ] Cue check: every bar-line cut and hero hit within ±1 frame of `music.beats.json` (onsets of the final mix)
- [ ] −14 LUFS ±1 integrated, true peak ≤ −1.5 dBTP; SFX audible over the music (ducking)
- [ ] Every number, path and quote on screen traces to a repo file (NOTES ledger); showcase footage unaltered except scale / crop / cut / fps-conform; labels match the README facts
- [ ] No third-party logos; "Claude Opus 5.5", "Claude Code" and "Codex" appear as plain text only
- [ ] TASTE_CHECKLIST 20/20 PASS on the final sheet. Documented exceptions: footage colours (#9); the part-3 gag (#10 / #11 / #19, by design)
- [ ] Determinism: out-of-order frames PSNR ≥ 45 dB, including canvas and video frames; re-rendering score.json gives an identical WAV hash
- [ ] No general flash more than 3 times per second
- [ ] `hyperframes lint` 0 errors; `bin/vh check` shows no unintended black / freeze / silence

## TYPE
+ TYPE: product launch film (primary), with the beat-locking rules of the music-video doc. 1920x1080 30fps, exactly 1792 frames (59.733 s = 28 bars at 112.5 BPM), music-driven, SFX on key hits. The 9:16 re-framed cut is deferred until after the master.
Register: Linear/Vercel: near-black #0A0A0B, 1px hairlines #26262B, blueprint grid at 6% opacity, one amber accent #FFB224. Font: SF-like grotesk (SF Pro via system-ui) + LF Mono. No gradient text, glassmorphism or purple-cyan gradients, except the part-3 gag (≤ 6 frames, stamped FAIL).
One continuous virtual camera; camera moves 1.5–3s easeInOutCubic, about half your default speed, then hold; motion blur on fast moves; light seeded grain (off for the GIF source).
Beats (adapted):
1. hook f(t) (0–4.3 s);
2. the code2video idea;
3. problem: stunning, not reliable;
4. the name, dropped on the music drop;
5. 3 feature beats as real UI: the router; 3 gates, where oversized-cursor clicks trigger the approvals; self-review on contact sheets against the 20-item checklist;
6. proof: 4 real showcase films;
7. reveal: "this film too, even the soundtrack is code";
8. 0.5 s stillness before the final hit;
9. wordmark + CTA.
Every cut on a bar line, every hero word on a beat, every UI micro-event on a 16th (±1 frame); all read from audio/music.beats.json.
Use real copy and assets from this repo (README, CLAUDE.md, templates/, showcase/, projects/*/out/check). Recreate the UI accurately; no placeholder text or invented numbers.
No narration in the master (option A, pending). Bilingual kinetic type via a `lang` variable; soft zh/en SRT.

<!-- from 03-product-promo.md, adapted for this film -->
