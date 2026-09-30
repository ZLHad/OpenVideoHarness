# NOTES

## Facts checked (tools/verify_math.py, scipy quad + sici)
- [x] Square wave f(x) = sign(sin x), period 2π, values ±1, jump height 2. Fourier sine coefficients b_n = (1/π)∫_{-π}^{π} f(x) sin(nx) dx: numeric 1.273240, 0, 0.424413, 0, 0.254648, 0, 0.181891, 0, 0.141471 for n = 1..9 = **4/(πn) for odd n, 0 for even n**. Verified.
- [x] Series on screen: f(x) = (4/π)(sin x + sin3x/3 + sin5x/5 + sin7x/7 + ⋯). Matches b_n.
- [x] Gibbs limit: peak of S_N → (2/π)·Si(π) = **1.178980**; overshoot 0.178980 = **8.949% of the jump (2)**. On screen: "1.179" and "≈ 9% of the jump". Verified.
- [x] Peak of S_N at N = 1, 3, 5, 7, 9, 25, 49, 99, 199: 1.27324, 1.20042, 1.18836, 1.18423, 1.18233, 1.17947, 1.17911, 1.17901, 1.17899; located at x = π/(N+1). So on screen the horn at N = 25 and N = 99 both touch the 1.179 line to within 0.0005 (< 1 px in the zoom panel: 1 y-unit = 1050 px there). Horn width shrinks ∝ 1/N. Verified.
- [x] Counter N = highest odd harmonic currently in the yellow sum (2·ceil(w) − 1 for the continuous term count w). During the sweeps a fractional last term fades in; N shows the term being faded in.

## Creative decisions
- 2026-09-28 Stacked sines, not epicycles — reason: 24 s, silent; one graph lets the equation and the curve share colours term by term; epicycles need a second representation to explain.
- 2026-09-28 Colours by entity, not by harmonic: every harmonic is blue while being added and yellow once absorbed (avoids the banned rainbow; blue→yellow *is* the "adding" read).
- 2026-09-28 Pure black bg although `templates/TASTE_CHECKLIST.md` #10 flags pure black: the type doc (`video-types/01`) prescribes #000000 and takes precedence.
- 2026-09-28 Grid spans the whole safe box (no lecture column as in Code2Video's right-side grid). Curves/braces/magnifier are placed in *data* coordinates of grid-placed plot rects; only text and plot rects go through `GRID`.
- 2026-09-28 Zoom = inset panel (parent shrinks to C1–E3 and stays, magnifier box + link lines), not a camera zoom — follows the type doc's "parent stays visible, 30–40% of frame" and avoids Cairo stroke widths scaling with camera zoom.
- 2026-09-28 D5/D7 run faster than the type doc's "play 1–3 s + 0.5–2 s hold": third and fourth repetition of the same move, per 3b1b `animation-design-thinking.md` "tempo variation". Every hold ≥ 0.2 s.
- 2026-09-28 Equation font 46 (glyph x-height ≈ 25 px, bbox 133 px with fractions). TASTE #6 "≥ 44 px auxiliary" is interpreted as cap/fraction line height; math needs its own rule (see showcase README friction list).
- 2026-10-01 **Soundtrack fitted to the finished picture** (README › Soundtrack): English narration + piano score + a sonification of the partial sums.
  - **The narration is AI-synthesized (Gemini TTS, voice Iapetus, with a SynthID watermark)**: disclose it where the film is published.
  - Lines are written from the storyboard's reads, and the facts are copied from this file: sin(nx)/n, odd n only, 8.95 % said as "about nine percent". The Gibbs value 1.179 is left to the screen.
  - Voice: Iapetus beat Sadaltager (it misheard "One" as "And", 0.86) and a library tutor voice (flatter pitch range, 10.9 vs 14.2 semitones). The first direction, "calm and curious, thinking aloud", gave 1.5 words/s with long pauses ("The recipe: … odd … sines" took 6.3 s). "Brisk conversational pace, no dramatic pauses" fixed it, and the lines were cut down to fit the windows.
  - Placement: a line grid (`audio/vo_grid.json`) with `bin/vh tts … --beats`. The `over` line was synthesized on 19.15 s and then moved to 19.0 s, the same take rebuilt sample by sample, so it ends by 21.8 s when the brace appears. No line needed speeding up.
  - Alignment: the Gemini transcribe quota (Tier 1, 100 a day) ran out on 09-30, so `--align gemini` has not run and the timeline has no word timings yet. A local whisper-large-v3-turbo check, scored with tts.py's own aligner, gives 1.00 for square, more, except and over. sine, recipe and third are heard as "sign" (a homophone), and gibbs as "9%" (1.00 by sound).
  - Score: 75 BPM (24 frames a beat), D major, delayed 0.3 s so 4.3 s is a bar head. Without drums a chord 0.1–0.2 s off a picture change reads as phrasing; the frame-exact moments are carried by the sonification.
  - Sonification: on D4, so its partials (D, A, F#, a flat C) belong to the D major bed. The tones sit at −20…−26 dB on the SFX bus; that bus is not ducked, so they stay steady under the voice. `tools/build_audio.sh --no-sonify` drops them.
  - `bin/vh qa`: no silence, dropouts or pumping. No cues: the sounds swell, so they sit at or below −18 dB, which the cue check skips.
  - Not heard by anyone yet (please audition): do the tones read as "the sum you see" or as test tones / hum under the voice? The 5th and 7th harmonics are close to masked, and the bell on "≈ 9%" is covered by the piano's D chord that lands with it.

## Self-review log

[v1 · whole piece 0–23.9 s] sheet: out/check/v1_sheet.png, strips: v1_strip_add3.png (9.2–11.0 s), v1_strip_zoom.png (17.1–18.9 s), frame v1_final.png. Render -ql 22 s wall.
- bbox audit: no unexpected overlaps; all boxes inside the safe box (panel right edge 1797 px < 1824). Only "peak_line × brace" touches (0 px high, brace ends on the line by design).
- `bin/vh check`: `black_start 0 → 2.47 s` = false positive (thin grey curve on pure black, >98% black pixels); freeze 22.33 → end = intended final hold.
- #13/#17 PASS: add-harmonic strip reads: blue ⅓-size wave on the axis → rides onto the yellow → yellow absorbs it.
- #10 FAIL (minor): during the merge, blue under a half-faded yellow gives 1–2 greenish frames → fade blue in [0.1, 0.55] of the merge instead of [0.4, 1].
- #4 FAIL: zoom strip frames 3–4 — the panel grows while the parent is still large, so the panel's black background covers the parent's right plateau → split the move: parent shrinks over [0, 0.7], panel opens over [0.3, 1.0] (two trackers).
- #2 FAIL (minor): zoom panel y-range 0.45–1.45 leaves the lower 45% nearly empty; the horn is only ~130 px tall → tighten to 0.62–1.34 (horn ≈ 190 px).
- #6 FAIL (minor): tick values (32) and the Gibbs label (36) are small once the GIF is scaled to 640 px → 38 and 42.
- Considered, kept: rows A empty for the first 4.3 s (graph sits low until the equation arrives). Density ramp; moving the graph would add a move with no meaning.
- others PASS

[v2 · 8.1–11.0 s and 17.0–19.0 s] strips: out/check/v2_strip_merge3.png, v2_strip_zoom.png, frame v2_final.png
- #4 PASS now: parent shrinks first, panel grows out of the magnifier box; horn ≈ 190 px tall, labels readable at 640 px.
- #15 FAIL: early blue fade (v1 fix) makes the yellow arrive at an unmarked place (blue already gone) → keep blue until late (fade in [0.6, 1]) but draw it UNDER the yellow during the merge (z-index 3 → 1.5), so the opaque yellow covers it; no blended colour.
- others PASS

[v3 = final · 0–24.0 s, 1080p30] sheet: out/check/final_sheet.png, strips final_strip_{D3,Dinf,zoom,F}.png, crop final_crop_horn.png, stills final_t*.png
- merge strip (v3_strip_merge3.png): yellow slides onto the blue, thin blue edges visible until covered → PASS.
- ffprobe 1920x1080, 30/1, 23.999 s, h264, no audio stream. `bin/vh check`: black 0–2.77 s (false positive, see v1), freeze 22.40 s → end (intended 1.6 s final hold).
- determinism: `-n 30,31 --format png` frames byte-identical to the full PNG render (21/21).
- Known minor: brace's lower tip touches the N = 99 ringing at the panel's right edge (by design the brace ends at y = 1); rows A empty for the first 4.3 s.

[reviewer pass · fresh-context subagent (playbook/02 layer 5) on the v3 frames] verdict: **don't ship as-is**. Fixes applied in v4:
- Zoom glitch 17.6–18.0 s: the panel's opaque fill blacked out the corner being magnified while the parent was still shrinking. → E is now strictly sequential: parent shrinks 17.2–17.8, magnifier box fades in on the settled parent 17.8–18.0, panel + links grow from the box 18.0–18.7, hold to 18.9; panel fill/curves layered UNDER the parent and the box.
  - Root cause found while fixing: `Mobject.become()` (used by `always_redraw`) copies points and style but **not z_index**, so each live curve kept the z_index of its first `func()` result (mostly an empty VMobject at z = 0). The panel fill therefore sat at the same layer as the parent's yellow and was drawn over it by add order; the grey target (z = 1) was drawn *above* the yellow sum all video; and the v3 "blue under yellow during the merge" z-trick never took effect (the v3 improvement came from the fade timing alone). → `live()` wrapper = always_redraw + `set_z_index(new.z_index)` on every update; explicit layers documented in fourier.py.
- Final hold 1.6 s → 2.6 s (total 24.0 → 25.0 s), so "≈ 9% of the jump" is fully readable for ~2.8 s.
- "9%" didn't match what's on screen (only 1 and 1.179 were visible; the jump of 2 never was). → grey ticks `1` and `−1` on the always-visible parent graph, appearing at 18.9 s with the panel's `1`. Parent shrunk to 0.42× and shifted +0.25 so the `−1` label stays inside the safe box (bbox audit: tick_-1 x 130–183 px ≥ 96).
- N = 7 read too short → `N = 7` held 15.3–15.5, sweep moved to 15.5–16.7 s (1.2 s).

[v4 = final · 0–25.0 s, 1080p30] sheet: out/check/final_sheet.png (= out/check/final-sheet-011502.png), strips: final_strip_zoom.png (17.1–19.0 at 10 fps), final_strip_Dinf.png, v4_strip_merge3.png, crop: final_crop_horn.png
- ffprobe 1920x1080, 30/1, 24.999 s. bbox audit: no unexpected overlaps, nothing outside the safe box.
- `bin/vh check`: black 0–2.77 s and 17.57–18.33 s (the new sequenced zoom has ~0.8 s where only the small parent + faint box are on screen; > 98% black pixels) and freeze 22.40 → end = intended hold. All false positives for a pure-black explainer; the updated `bin/vh check` now prints that caveat itself.
- merge strip: opaque yellow now really slides over the blue (blue underneath, fades late) → PASS.
- determinism re-checked after the `live()` change: `-n 33,35 --format png` frames byte-identical to the full render (21/21).
- Could not fix / left as is: row A empty for the first 4.3 s; the brace's lower tip touches the N = 99 ringing at the panel's right edge (brace ends at y = 1 by design).

## Asset ledger
| file | source | licence |
|---|---|---|
| (none) | all visuals generated by `scenes/fourier.py` | original |
| audio/voiceover.en.flac (narration) | Gemini 3.8 Flash TTS, voice Iapetus, synthesized 2026-09-30; SynthID watermark | AI-synthesized, used under Google's terms; disclose on publication |
| audio/score.json → the music | composed here; rendered by `bin/vh music` (synthesis only, no samples) | original |
| 10 sonification sounds (target square, sums, harmonics, sweep, bell) | `tools/foley.py`, synthesized | original |
| built-in SFX (whoosh) | `bin/vh sfx lib` (`tools/audio/sfx.py`) | MIT, part of this repo |
