# Showcase 03: Building a square wave from sine waves (math / Manim CE)

![preview](media/preview.gif)

**Full video:** [media/final.mp4](media/final.mp4) · **Contact sheet:** [media/sheet.png](media/sheet.png)

| | |
|---|---|
| Type / route | `math` → `video-types/01-math-science-explainer.md`, engine Manim CE |
| Output | 1920x1080, 30 fps, **25.0 s** (750 frames), h264 + a stereo AAC soundtrack (English narration, a piano score and the partial sums made audible, added after the picture was finished: [Soundtrack](#soundtrack)), a soft en subtitle track, 2.8 MB |
| Manim | Manim Community **v0.21.0**, Python 3.12.2 (uv), Cairo renderer, MacTeX for `MathTex` |
| Render time (M3 Max) | final `-qh --fps 30`: **24.3 s** wall; draft `-ql`: ~22 s wall |
| Review iterations | 4 renders (v1 → v2 → v3 → **v4 = final**). Each had a contact sheet, strips of the key moves, a horn crop and a bbox audit; one fresh-context reviewer pass came between v3 and v4. Critiques are in [NOTES.md](NOTES.md) |
| Agent wall time | ~20 min to the first delivered cut (v3), plus the reviewer-fix round |

**Reviewer pass:** a fresh-context reviewer subagent (playbook/02 layer 5) judged v3 from its frames alone and said "don't ship as-is". v4 applies its four fixes:
1. The zoom is now strictly sequential: the parent shrinks, then the magnifier box fades in, then the panel grows. The panel sits under the parent, so it no longer blacks out the corner being magnified.
2. The final hold goes from 1.5 s to 2.5 s, so the video is 25.0 s.
3. Grey `1` / `−1` ticks on the parent graph put the jump of 2 on screen, so "≈ 9% of the jump" can be checked.
4. `N = 7` gets its own beat before the sweep, which now runs 15.5–16.7 s.

Fixing (1) exposed a real engine bug in my code: `always_redraw` loses `z_index` (see friction #1).

## The request this was built from

> Topic: "Building a square wave from sine waves": Fourier series partial sums of a square wave, showing the 1st, 3rd, 5th… harmonics adding up (epicycles or stacked sines are both fine), ending with the Gibbs overshoot (~9%) near the jump as a small payoff.
> 18–25 seconds, 1920x1080, 30 fps, SILENT: minimal on-screen text; one LaTeX equation (the series) introduced whole, dimmed, then highlighted term by term; short labels.
> Follow the type doc: black background, one colour per math entity held for the whole video, geometry before algebra, holds after each move, no bounce/glow/particles, place objects via a grid helper, print bounding boxes to check overlaps. Verify the maths (coefficients 4/(πn) for odd n; Gibbs ≈ 8.95% of the jump) and log it in NOTES.md.
> Review loop: render -ql while iterating, contact sheets via ffmpeg (bin/vh sheet), check against TASTE_CHECKLIST.md, log critiques in NOTES.md; final render at 1080p. Approval gates skipped by the user; BRIEF/STORYBOARD/STYLE still written before coding.

## What's in the video
- **Opening:** a grey square wave appears. One blue sine, `(4/π) sin x`, already roughly follows it, then turns yellow: it becomes the running sum.
- **Equation:** the series appears whole, dims to 30%, then lights up term by term. Each new odd harmonic is drawn in blue on the axis (1/n as tall, n× as fast), stacked onto the yellow sum and absorbed. Its term in the equation turns from blue to yellow at the same moment.
- **Many terms:** `⋯` lights, `N = 7` appears, and N runs to 25.
- **Zoom:** the parent graph shrinks left and a magnifier box appears on the jump at x = 2π. A zoom panel grows out of the box.
- **Gibbs payoff:** a red line marks the horn peak at 1.179, with the plateau at 1 and ticks at ±1 on the parent. N runs to 99; the horn gets thinner but not shorter. A brace labels it "≈ 9% of the jump".

Colour contract (STYLE.md): target grey, harmonic-being-added blue `#58C4DD`, running sum yellow `#FFFF00`, overshoot red `#FC6255`.

## Soundtrack

The picture was made and finished silent, as briefed; English narration, a piano score and a sonification of the partial sums were fitted to it afterwards (2026-10-01). The picture's timing is fixed and the audio fits it; the picture still carries the maths, and the voice says where to look.

- **Narration** (`audio/script.txt`, eight lines written from the storyboard's reads): "Take a square wave. / One sine comes close. / Add odd sines, each one smaller. / Sine 3x: a third as tall. / 5x, 7x, and the corners sharpen. / It squares up, except at the jump. / More terms only make the overshoot thinner. / About nine percent of the jump."
  - The facts are the ones on screen and in `tools/verify_math.py`: odd harmonics sin(nx)/n, and 8.95 % said as "about nine percent". 1.179 is left to the screen.
  - Voice: Gemini TTS, voice Iapetus, directed as `Clear, curious math explainer; brisk conversational pace, no dramatic pauses`, plus a short direction per line. It was chosen from three candidates on the same lines, by speech-recognition similarity and pitch range. A "calm, thinking aloud" direction had made it far too slow.
  - Timing: each line starts on a hand-made grid (`audio/vo_grid.json`, from the reads and the play() timings) and ends before the next read. For example, "except at the jump" lands on the spikes and the zoom, and "…thinner" lands inside the N 25 → 99 sweep.
  - The narration is AI-synthesized (Gemini TTS, with an inaudible SynthID watermark). The lossless master `audio/voiceover.en.flac` is committed because the takes cannot be regenerated byte for byte.
- **Score** (`audio/score.json`, `bin/vh music` with instrument parts): felt piano over soft strings and a low D drone, no drums, D major at 75 BPM, starting 0.3 s into the film (the equation's entrance at 4.3 s is a bar head).
  - The piano answers the harmonics. D4's partials spell D, A, F# and a flat C, so the piano plays A on the 3rd harmonic's merge (10.2 s), F# on the 5th (12.5 s) and C on the 7th (14.4 s): a D7 colour that leans into G for the "N → 25" sweep.
  - It hushes to Dsus2 for the zoom, sits on an unresolved Bm7 under the horn, and lands a D major chord with the brace (21.8 s).
- **Sonification** (`tools/foley.py`, tagged `"layer": "sonification"`): a tone on D4 whose waveform is the curve on screen.
  - The grey square wave sounds as it draws (a hollow, clarinet-like tone), then the pure sine.
  - Each new harmonic sounds alone while it draws (n·f0, quieter, as it is 1/n as tall). The sum S3 / S5 / S7 swells as each one merges.
  - A sweep uses the scene's own term weights for N 7 → 25.
  - Plus a zoom whoosh and a bell on "≈ 9% of the jump". `tools/build_audio.sh --no-sonify` leaves the tones out and keeps the whoosh and the bell.
- **Mix**: −14 LUFS integrated, true peak ≤ −1.5 dBTP, the music ducked under the voice (`duck=voice duck_ratio=1.6`). `bin/vh qa`: no digital silence, dropouts or pumping. There are no onset cues: every sound here swells, so each sits at or below −18 dB, where the cue check skips it. The click warnings are consonants in the narration take. Soft subtitle track: `audio/captions.en.srt`.

Rebuild (from the repo root; needs uv and ffmpeg):
```bash
showcase/03-math-fourier/tools/build_audio.sh                   # → audio/mix.wav + audio/qa.txt
showcase/03-math-fourier/tools/build_audio.sh --no-sonify       # … without the partial-sum tones
showcase/03-math-fourier/tools/build_audio.sh --mux out.mp4     # … plus out.mp4 = the picture of media/final.mp4 + that mix + en subtitles
```
Committed: `audio/script.txt`, `audio/vo_grid.json`, `audio/voiceover.en.flac`, `audio/timeline*.json`, `audio/captions.*`, `audio/score.json`, `audio/events.json`, `audio/music.beats.json`, `tools/foley.py`, `tools/build_audio.sh`. The WAVs are regenerated and ignored (`audio/.gitignore`).

## Files
- `BRIEF.md`, `STYLE.md` (entity-colour map, 6×6 grid), `STORYBOARD.md` (shots, reads with timings), `NOTES.md` (maths verification + review log incl. the reviewer pass), `LESSONS.md`
- `scenes/fourier.py` (scene; `live()` = z-index-preserving `always_redraw`), `scenes/style.py` (palette, grid helper, bbox audit, polyline/clip helpers), `tools/verify_math.py`, `pyproject.toml`
- Soundtrack: `audio/` (script, line grid, narration master, timelines, captions, score, events, beat map), `tools/foley.py`, `tools/build_audio.sh` (see [Soundtrack](#soundtrack))

Reproduce (from a project folder created by `bin/vh new math <slug>` with these files copied in):
```bash
uv sync            # or: uv init --bare --python 3.12 && uv add manim
export PYTHONWARNINGS=ignore::SyntaxWarning
uv run python tools/verify_math.py
uv run manim -qh --fps 30 scenes/fourier.py FourierSquareWave
```

## What the harness docs helped with
- **Routing and the type doc** (`CLAUDE.md` route table → `video-types/01`). The whole visual grammar came from here: one colour per entity, the equation shown whole, dimmed, then lit term by term, and the parent graph kept visible at 30–40% while zoomed. The "one colour per entity" rule forced the key design choice: blue means "being added", yellow means "already in the sum", and no rainbow harmonics.
- **3b1b Gotchas plus `equations.md` / `equation-derivations.md`.** The multi-string `MathTex` split and the dim-and-reveal pattern worked on the first try. `animation-design-thinking.md`'s tempo-variation rule justified compressing the repeated add-a-harmonic move.
- **Code2Video anchor grid** (`prompts/stage3.py`, `base_class.py`). It turns placement into choosing cells: `A1–A5` equation, `A6` counter, `C1–E3` parent, `B4–F6` zoom panel.
- **`playbook/01-pipeline.md` reads.** Writing reads with start and end times made the 24 s budget explicit before any code; the first render came in at 23.93 s.
- **`playbook/02-verification.md` plus `bin/vh sheet/gif/check`.** Strips caught the colour blend in the merge. The fresh-context reviewer (layer 5) caught what I had normalised: the zoom blackout, the unshown jump of 2 behind "9%", and the short final hold. Layer 5 earned its place.

## Friction points (most important first)
Status notes: several of these were fixed in the harness while this showcase was being made. They are marked **[fixed during run]** with where the fix landed.

1. **NEW: `always_redraw` silently drops `z_index`.** `Mobject.become()` copies points and style, not `z_index`, so a live mobject keeps the z of its first `func()` result forever; an empty placeholder means z = 0. Here it caused three bugs:
   - the reviewer's zoom blackout (the panel's black fill drew over the parent by add order);
   - the grey target drawn above the yellow sum for the whole of v1–v3;
   - a z-order fix of mine for the merge that did nothing.

   It isn't in the 3b1b Gotchas, `troubleshooting.md` or the type doc's 自查重点. Fix: `live(func)` in `scenes/fourier.py`.
2. **[fixed during run] No path for silent videos.** `CLAUDE.md` hard rule 2, `video-types/01` step 5 and its prompt block all assumed narration, and `bin/vh new` pasted the voiceover line. CLAUDE.md rule 2, the type doc and the prompt block now have a silent branch.
3. **[fixed during run] `engines/README.md` › Manim CE.** `uv init` created a nested `.git`, `main.py`, `README.md` and `.python-version`. It also installed an unneeded `manim-voiceover`, and nothing mentioned the pydub `SyntaxWarning` spam. It now says `uv init --bare`, makes voiceover optional, and sets `PYTHONWARNINGS`.
4. **[fixed during run] fps mismatch.** The prompt block said 30 fps, but the final command was `-qh`/`-qk`, which is 60 fps. `-qh --fps 30` is now documented in engines/README and the prompt block.
5. **[fixed during run] The `play(rate_func=…)` override gotcha** is now in `video-types/01` 自查重点.
6. **Grid wording still assumes a lecture column.** `video-types/01` 工作流 step 4 still says "在右侧动画区定义 6×6 锚点网格", but a silent, full-frame explainer has no lecture column. The doc also doesn't say how grid placement coexists with data-coordinate objects (curves, braces, magnifier boxes). `engines/README.md` now points to this showcase's `scenes/style.py` for a grid and bbox-audit implementation, which covers the practical side.
7. **Checklist and template conflicts, partly fixed.** `TASTE_CHECKLIST.md` #10 now exempts the type doc's pure black. `templates/BRIEF.md` still says "no pure #000/#fff unless chosen". #6's "84 px / 44 px" is still undefined for Manim `font_size` and math: em size, cap height, or bbox?
8. **[fixed during run] `bin/vh check` on dark explainers.** It now prints a caveat. With the new sequenced zoom it also flags 17.6–18.3 s as black (only the small parent is on screen), which is expected.
9. **[fixed during run] `bin/vh sheet` overwrote its output.** It used to write a fixed `check/sheet.png`; it now takes `[out]` and defaults to a timestamped name. Note for scripts: anything that copies `check/sheet.png` afterwards now picks up a stale file (this happened to me once).
10. **[fixed during run] Pacing for short cuts.** `video-types/01` 审美要点 now has a line for videos under 30 s.
11. **Rule collisions inside the 3b1b references, no stated precedence:**
    - `visual-design-principles.md` #17 says Menlo for all `Text()`; the type doc says CMU Serif. I avoided `Text()` entirely.
    - #16 reserves a bottom-20% caption zone.
    - `troubleshooting.md` says "always FadeOut titles"; the type doc says "dim, never delete".
12. **[fixed during run] Determinism recipe for Manim.** `playbook/02` now has `--format png -n A,B` plus a hash comparison. Re-run here after the `live()` change: 21/21 frames identical.

## Known imperfections
- Row A is empty for the first 4.3 s, until the equation arrives. It's a density ramp; moving the graph would add a move with no meaning.
- At N = 99 the brace's lower tip touches the tiny ringing at the panel's right edge. The brace ends at y = 1 by design.
