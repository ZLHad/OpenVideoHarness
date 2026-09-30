# NOTES

## 待核实的事实
- None. The piece is pure fiction with no facts, numbers or quotes.

## 创作决策
- 2026-09-28 Engine: ClaudeAnimationBase (route: video-types/07-hand-drawn.md). The user authorized skipping both approval gates; BRIEF.md and STORYBOARD.md were still written before any scene code.
- 2026-09-28 The template BRIEF's "Motion defaults" (no bounce/elastic, no idle breathing) contradict ANIMATION_GUIDE (takes, overshoot, beat-locked idles). I followed the type doc and ANIMATION_GUIDE (cartoon register), as playbook/03-motion-design.md §0 allows, and said so in BRIEF.md.
- 2026-09-28 Premise refinement: "Clawd films itself" is staged as a POV shot through the viewfinder (ink border, cream corner brackets, blinking painted red dot). The film opens with the same viewfinder on the leaf, which makes the opening and ending rhyme.
- 2026-09-28 New prop: a hand-cranked movie camera with three drawn key views (lens right / lens at viewer / lens left), checked as a model sheet (`LOOPS.props`) before use.
- 2026-09-28 Colour: the hero leaf is the only saturated gold in the film. The maple crown is rust, and the hero perch in B is a blue-green squash, not an orange pumpkin, so neither the leaf nor Clawd's terracotta gets lost.
- 2026-09-28 Parallax: sky and hills sit on a background camera layer that moves at 35–40 % of the foreground camera. There are two sequential camBegin/camEnd pairs per shot, which the one-level rule allows.

- 2026-10-01 **Soundtrack fitted to the finished picture** (README › Soundtrack): cartoon underscore + foley, no narration (pantomime).
  - Tempo: the score uses the animation's own grid, 120 bpm from 0 s (`src/config.js`), even though 144 bpm would put both cuts within 33 ms. Clawd's beat-locked idles and the rec dot are drawn on 120.
  - Mickey-mousing: the score's note lists sit on the action times that `tools/foley.py` derives from leaf.js. The chase pizzicato plays on the 1st, 4th and 6th footfalls (4.049, 4.243, 4.485 s). The xylophone "!" is on both takes (3.0 and 10.08 s), a timpani stroke on the stomp (6.78 s), and the harp repeats A's falling-leaf zigzag in C.
  - Level and cue fixes (qa + a per-event audibility proxy, no ears): `music_db=-7` so the foley leads. The iris close is split into a hiss and a thunk, so the thunk is its own cue on the last frame (11.955 s). The first chase pluck is softened, so the next footfall 55 ms later still reads as its own onset. The takes and the stomp are 2 dB lower, to stay off the true-peak limiter.
  - Not heard by anyone yet (please audition): the gust layers (they sit at −18 dB, where qa skips custom swells, and may be too polite for a gag gust), the crank ratchet (too mechanical?), the slide-whistle takes (shrill?), the skid squeak (1900 → 900 Hz, harsh?), the film-gate whirr in C (reads as camera or as noise?), the stomp (the loudest event), and whether the flute and harp zigzag reads as "falling leaf".

## 自评记录

Iteration 1: first sheets of A, B and C.

[A · 0.0–4.0s] sheet: out/check/A_sheet.jpg
- #1 FAIL: Clawd (u 26) and the leaf (r 34) too small in a wide frame; the leaf reads as a star speck → u 34, leaf r 50, camera zoom 1.1 after the reveal.
- #20 FAIL: the opening viewfinder frames mostly empty sky with a tiny leaf → camera starts at zoom 2.1 on the leaf, then pulls back.
- #10 FAIL: the palette reads cool and grey rather than warm autumn → warmer hills and meadow, far rust trees on the ridge.
- #12 FAIL: wind streaks look like thick cream sausages → thin dry-brush plus a fine ink curl; small rust leaves ride the streaks.
- others PASS

[prop sheet] out/check/props.jpg
- FAIL: the 5-point maple leaf reads as a star (the demo's motif!) → broader, rounder lobes and a longer curved stem. It now reads as a leaf at 45 px.

[A · faces] crop: out/check/A_face.jpg
- #1 FAIL: Clawd's terracotta vanishes against the orange mid hill → mid hill changed to sage-olive #99976A.
- #15 FAIL: the camera covers Clawd's only side-view eye, so no face acting is visible → the camera is held 0.85u ahead of the eye, the tilt is capped at −0.45 rad and the body leans back for the rest.
- FAIL: on the surprise take the raised camera lands on the eye → the take jolts the camera forward instead (aL 1.2 + a spring on the aim).

Iteration 2: B and C.

[B · 4.0–8.2s] sheet: out/check/B_sheet.jpg
- #1 FAIL: Clawd tiny (u 24) in a wide frame and the leaf a speck → u 30, camera zoom 1.35 following between Clawd and the perch.
- #9 FAIL: a big orange pumpkin competes with Clawd's colour, and the gold leaf lacks contrast on it → blue-green squash for the hero perch; orange pumpkins only small and far.
- FAIL: side-lobe ink lines show through the front lobe (p5.brush defers strokes; flushBrush did not fix it) → the pumpkin is rebuilt as one silhouette with painted rib lines ("one shape, one outline").
- #14 FAIL: the lens push reads as "a black ball grows"; the zoom barely moves → zoom ×3.2 ease-in toward the lens, a brass rim around the swelling glass, exponential growth.

[B · faces] crop: out/check/B_face.jpg, B_face2.jpg
- #15 FAIL: "turns the camera round and peers in" does not read. The turned camera looks the same as before and hides the eye → the lens gets a brass rim, the turned camera is held at arm's length with the lens facing the eye, a "?" emote is added, then Clawd leans in (dx 0.75u). Now reads in 4 frames: lens out → front view with smear → lens facing Clawd → lean in.
- blank stare (6.35), angry stomp with teeth and anger mark (6.8): PASS.

[C · 8.2–12.0s] sheet: out/check/C_sheet.jpg
- #2 FAIL: planned as a close-up but rendered as a medium shot (u 56, whole body) → u 84 with the feet below the frame; leaf r 88 so it reads as a hat.
- red record dot too small → r 24 with glow.

Iteration 3: strips for key motions and every seam.

[A · open 0–1.3s] strip: out/check/strip_A_open.jpg
- #17 FAIL: the leaf lets go at 1.0 while the reveal pull-back is still moving (two reads overlap) → reveal 0.55–1.05, release at 1.15; excited 1.6, determined 2.1.

[A · gust 2.35–3.2s] strip: out/check/strip_A_gust.jpg
- FAIL: the rocking leaf drifts right into the lens before the gust, so there is no "framed" beat → slower, less drifting fall (62 px/s, 125 px/s). Checked in strip_A_fall.jpg: the leaf stays in front of the lens through 2.55.
- snatch arc, trailing streak and whip pan, then the reaction after the leaf is gone: PASS (reaction starts 0.1 s after exit).

[A→B seam 3.45–4.4s] strip: out/check/strip_AB_seam.jpg, strip_AB_seam2.jpg
- #14 FAIL: cut on action jumps Clawd from the right third (A) to the left third (B) → B's camera starts with Clawd where A left him and eases to catch up, which also reveals the leaf.
- FAIL (after the fix): the meadow's left end shows in B's first frames, and Clawd runs through a small pumpkin at 4.02 → meadow extended to x −1300; the pumpkin moved off his path.

[B gust 5.85–6.6s] strip: out/check/strip_B_gust.jpg
- anticipation streaks → leaf lift, loop and exit → blank stare → angry stomp in sequence: PASS.

[B→C seam 7.75–8.6s] strip: out/check/strip_BC_seam.jpg, strip_BC_seam2.jpg
- after the fix: brass-rimmed lens swells to full cover by 8.1, 3 dark frames, then the viewfinder opens on Clawd's suspicious face: PASS.

[C land 9.7–10.8s] strip: out/check/strip_C_land.jpg, strip_C_land2.jpg
- #17 FAIL: the "notice" read (eyes roll up) got 7 frames → landing at 9.9, the notice is a 'surprised' take ("!" + O mouth, lookY −1) held 10.05–10.6 (13 frames), joy at 10.6.

[C end 11.2–12.0s] strip: out/check/strip_C_end.jpg, C_end2.jpg
- FAIL: the closing rect clips the leaf, then the smile → rect 980×660 centred 60 px above the eye line; leaf, eyes and smile stay in view until ~11.85; ink by 11.96.

[boil] out/check/boil_A.jpg, boil_B.jpg: still elements (crown, squash, fence) hold each drawing for 2 frames: PASS.

[whole] out/check/full_sheet.jpg (24 frames): the story reads from the sheet alone. No text, no 3D, no pure black/white; transitions at every seam: PASS.

## Least happy with (for the user)
1. B's sneak-up (5.0–5.9): in side view the mischief face is small, so the tiptoe carries the "sneaky" read almost alone.
2. The 3 frames of flat ink at 8.1–8.2 between the lens push and the viewfinder: intended as "inside the lens", but it is a near-black hold.
3. The leaf in the wide A frames is ~55 px; it reads because it is the only gold thing, but it is small.

## 素材台账
| 文件 | 来源 | 许可 |
|---|---|---|
| all artwork | painted in code (src/scenes/leaf.js) on ClaudeAnimationBase | engine MIT (JohnHeibel/ClaudeAnimationBase) |
| audio: the music | `audio/score.json`, composed here; rendered by `bin/vh music` (synthesis only, no samples) | original |
| audio: 22 custom foley sounds | `tools/foley.py`, synthesized, seeded | original |
| audio: built-in SFX (whoosh, swish_rev, toggle, click) | `bin/vh sfx lib` (`tools/audio/sfx.py`) | MIT, part of this repo |
