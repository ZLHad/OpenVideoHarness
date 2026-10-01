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
  - Level and cue fixes for the first candidate (qa + a per-event audibility proxy, no ears): `music_db=-7` so the foley leads. The iris close is split into a hiss and a thunk, so the thunk is its own cue on the last frame (11.955 s). The first chase pluck is softened, so the next footfall 55 ms later still reads as its own onset. The takes and the stomp are 2 dB lower, to stay off the true-peak limiter.
  - Listen for (the maintainer heard the first candidate, not this profile mix): the gust layers (as `detail` the profile lifts them from −18 dB to −2…0 LU re the music's 3 s level; still too polite for a gag gust?), the crank ratchet (too mechanical?), the slide-whistle takes (shrill?), the skid squeak (1900 → 900 Hz, harsh?), the film-gate whirr in C (reads as camera or as noise?), the stomp (the loudest event), and whether the flute and harp zigzag reads as "falling leaf".
- 2026-10-01 **Final mix: profile `cartoon`** (`bin/vh mix … profile=cartoon`, playbook/04-audio.md 混音), chosen by the maintainer after the candidates. It replaces the ffmpeg chain (`duck=off`, one static gain) and the old workaround of running every bus past the film and cutting afterwards; the cut and the fade happen inside the mix, and every run gives the same bytes (checked).
  - Toolchain for the byte-identical rebuilds (the mix WAV and, with `--mux`, the mp4): ffmpeg 8.0.1, Python 3.14.7, numpy 2.5.3, scipy 1.18.1 (through uv 0.10.0, macOS on Apple Silicon). Other versions can change the low bits of the mix and of the AAC stream.
  - Anchor: the music's 3 s loudness (no narration). Each SFX event moves half way toward its class's range. The four gust layers are `role: detail` in `tools/foley.py`: the name hint made them ambience, but they are the gag's action (they snatch the leaf). Hero median +1.6 LU re the anchor (−2…4), detail −2.0 (−6…0), ambience −12.7 (−16…−8); SFX peaks held at anchor +9 dB (46 peaks, up to 3.3 dB); the music dips 2 dB under the five hero hits.
  - Changed by sound design after the first profile mix: (1) the end fade is 40 ms, not 0.1 s. The 0.1 s fade started at 11.9 s and took 7–12 dB off the iris thunk on the last frame (11.955 s); its cue margin went from +0.002 to +0.043. (2) The leaf landing on Clawd's head (9.917 s) is −9 dB, not −12. The cue check had matched a harp note 13 ms early, not the pat; now the pat's own onset is found (+8 ms, margin +0.31), and the take 0.17 s later, which moves with it, stays in range. (3) The leaf settling on the pumpkin (4.625 s) is −14 dB, not −16: it was LOW (−6.7 LU re the anchor, range −6…0) and is now −4.8. Lowering the iris hiss before the thunk made the thunk's margin worse, so it stayed at −18 dB.
  - Master: static gain +4.1 dB and a true-peak limiter on 4 peaks (up to 1.5 dB; the stomp and the takes). The first mux at the profile's default `tp=-1.65` peaked at −1.46 dBTP after the AAC encode, so `tools/build_audio.sh` mixed again at `tp=-1.79` (and now starts there): −14.01 LUFS, −1.79 dBTP in the WAV, −1.65 dBTP in the mp4 (ffmpeg ebur128: −14.1 LUFS, −1.7 dBTP).
  - `bin/vh qa --fps 24`: no silence, dropouts, pumping or clicks; 30/30 cues within a frame. Five are marginal (`OK~`), all in the dense chase stretch: crank_a 1.65 (+0.019), zip_off 3.84 and the xylophone at 3.875, which share one onset (+0.009), the first footfall 4.049 right after the push-off's swish (+0.003) and the skid 4.86 with its 20 ms attack (+0.006). Run with this qa, the first candidate had the crank, the push-off, the xylophone and the skid marginal too (+0.007…+0.017); the first footfall is new, and the changes above did not move any of them.
  - Mix-report warnings left as they are, each within 2 LU of its class's range: sparkle, the first footfall, the gust #2 left layer, the whooshes at 6.35 and 8.2 (HIGH); the second tiptoe, the C iris opening and the swish_rev at 11.73 (LOW); the iris hiss (HIGH for ambience).
- 2026-10-01 **Colour: re-encoded to limited-range BT.709.** The final was `yuvj420p`, full range, tagged `bt470bg` (render.mjs before #28), and Chromium showed it with shifted colours. Re-encoded once, with the new soundtrack, from the committed final:
  `ffmpeg -i final.mp4 -map 0:v:0 -vf "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709" -c:v libx264 -preset slow -crf 19 -r 24 -movflags +faststart out.mp4`
  - ffmpeg reads the source's own tags (full range, BT.601 matrix). `accurate_rnd+full_chroma_int` keep the swscale conversion within a level (without them, pure yellow in 03 came back 3 levels off).
  - CRF 19, not 16–18: the source is an x264 CRF 23 encode with painted texture, and CRF 17 / 18 grew the video by 49 % / 34 %; CRF 19 grows it by 23 % (7.10 → 8.74 MB). With the AAC track the mp4 is 9.04 MB (+27 %).
  - Check: 288 frames at 24 fps, 12.000 s; all four tags (`tv`, `bt709` ×3). Over 1.1 M saturated pixels in frames 30, 100, 160, 230 and 270 (max − min channel > 120, eroded 5 × 5), the new file decoded with its tags is within 1.4 levels on average (p99 6) of the original decoded with its own tags; the original read as BT.709 was 6.4 levels off (p99 13, max 20). RGB PSNR against the original, frame by frame: 40.8 dB at worst, 43.0 dB on average, so no frame moved.

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
