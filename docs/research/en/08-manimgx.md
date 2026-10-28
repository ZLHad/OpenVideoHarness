# 08 · ManimGX as a Manim backend: showcase 03 moved over, the lines it took, how alike, how fast

*Recorded 2026-10-29 · Status: ManimGX 0.1.1 is registered as an optional backend in this note's PR (`tools/modules.json`, reported by `bin/vh doctor`); Manim CE stays the first engine for types 01 and 06 · [中文](../08-manimgx.md)*

## Question

ManimGX takes scenes written against Manim CE's Python API and renders them on a Rust and wgpu core; its authors measure it far faster than CE (90× over five 1080p60 scenes on an M4 Pro, 3D among them). Moving this repo's showcase 03 (a square wave from sine waves, 25 s, Manim CE 0.21) over as it is: how many lines change, how alike are the pictures, how much faster is it, and can its file go straight into the repo's pipeline?

## Method

- One machine (M3 Max, macOS 15.8), one `scenes/` folder: Manim CE 0.21.0 / Python 3.12 (uv), `-qh --fps 30 --disable_caching`; ManimGX 0.1.1 / Python 3.13 (uvx, outside the project's environment), `-r 1920x1080 --fps 30`. Each rendered twice, the second run timed, with the LaTeX, shader and font caches warm.
- Changed only as far as it took to run (finding 1).
- The pictures: ManimGX's film re-timed to a constant 30 fps and compared with CE's frame by frame (PSNR on full-size RGB, and again at 480×270, which smooths the strokes' anti-aliasing); each frame matched to the most alike frame of the other within 12 frames either side, to see whether the two draw the same moment at the same time; 3, 8, 16 and 20 s side by side (figure 8.1).
- The files: frame counts, length, colour tags; `bin/vh check`; whether two ManimGX renders give the same frames.

## Findings

1. **Four changes**: `from manim import *` becomes `from manimgx import *`; numpy is imported by hand (ManimGX's star import brings no `np`); ManimGX exports a shape called `Path`, which shadowed the `pathlib.Path` the file imports first (the scene's `Path("out/check/…").unlink()` failed), so pathlib is imported again after the star import; `rate_functions.ease_in_out_sine` becomes the top-level `ease_in_out_sine` (there is no `rate_functions` module). The rest runs as it is: `always_redraw` with its `z_index` fix, `ValueTracker`, per-part colouring of `MathTex`, `Brace`, `DashedLine`.
2. **About 5× as fast**: on the second run CE took 18.3 s, ManimGX 3.6 s (its own log says 3.0 s of rendering, the rest is start-up); on the first, CE 37.8 s (LaTeX compiling) and ManimGX 3.7 s. The authors' 90× comes from five scenes, 3D among them; this 2D film is 5× on this machine.
3. **Plainly the same film, not the same pixels**: per-frame PSNR at full size has a median of 25.8 dB (lowest 16.9); at 480×270 the median is 31.7 dB, 27.7 dB over the frames where the picture moves. Most of it is typesetting and strokes: Typst sets the equation, so the brackets and the ellipsis have other shapes and spacing than LaTeX's, and the curves' strokes are anti-aliased differently. In time the two mostly line up (each frame's most alike frame is, in the median, the same frame), but a few fast number animations are 6–10 frames apart: at 16 s CE's counter reads N = 15 and ManimGX's 13 (figure 8.1, third row). CE rounds each play's length to frames, ManimGX draws every frame at its exact time, so after a run of short plays the two land at different frames.
4. **Its file needs conforming before the repo's pipeline takes it**: ManimGX writes a variable-frame-rate MP4, a held picture as one long frame (482 frames in 25 s, the last one 2.63 s long), plus one frame at the scene's very end (751 frames once re-timed to 30 fps, against CE's 750); its colour is a BT.601 matrix, tagged `smpte170m` with sRGB primaries. `bin/vh check`, `mux` and edit lists want a constant rate and BT.709 with all four tags. One ffmpeg pass (cut to the scene's length, `fps=30`, BT.601 to BT.709, tagged; the command is in `engines/manimgx.md`) and `bin/vh check` passes: 750 frames, 25.00 s, BT.709, with the same notes as the CE film (the black opening, the still 1–4 s). The same frame before and after: 44.9 dB. Frames taken by time should come from the conformed file too: on the original, `-ss 24.5` falls inside the last long frame and yields no picture.
5. **Two renders give the same frames**, byte for byte once decoded (per-frame md5), on this machine's GPU.

![Manim CE (left) and ManimGX (right) at 3, 8, 16 and 20 s](../figs/08-ce-vs-gx.jpg)

Figure 8.1 · Manim CE 0.21 (left) and ManimGX 0.1.1 (right) at 3, 8, 16 and 20 s. The equation's glyphs and spacing differ; at 16 s the counter reads 15 on one side and 13 on the other.

## What changed in the repo

- `tools/modules.json` registers `manimgx`, pinned at 0.1.1, installed as a uv tool; `bin/vh doctor` says whether it is there and whether it is the pinned version (doctor now holds programs to their pin too, not only npm packages).
- A new `engines/manimgx.md`: how to install it, the lines a scene changes, how to conform its film, what to watch in timing and licence; `engines/README.md`'s Manim section points to it in one line (about 200 more characters read for types 01 and 06 at every level).
- The first engine of types 01 and 06 is unchanged. Whether a project switches is the project's call, written into its `DECISIONS.md`.

## Still unclear

- Only one 2D film was compared. 3D scenes (ManimGX's strength), long films and narrated scenes (its `self.say`) were not.
- Whether the 6–10 frames in the number animations come from rounding or from a different meaning of combined `.animate` calls was not taken apart. A film whose beats must sit on the narration should have its timing checked again after a switch.
- On Linux without a GPU it renders through lavapipe; its speed and determinism there were not measured.
- Licence: ManimGX's own code is MIT, while its native wheels bundle x264 and are GPL-3.0-or-later as a whole. Installing it locally to render is unaffected, but it cannot be shipped with this repo.

Sources: measured on this machine, 2026-10-29 (showcase/03-math-fourier's `scenes/`, Manim CE 0.21.0 and ManimGX 0.1.1); ManimGX 0.1.1's README and its "Coming from Manim CE" page (manimgx.academa.ai).
