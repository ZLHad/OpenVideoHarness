# LESSONS

## M+ what worked
- **Curves as `always_redraw` of closed-form maths driven by ValueTrackers** — scene: all curves (target, running sum, harmonic, zoomed copies) — effect: every frame is a pure function of tracker values; a render from animation #30 only (`-n 30,31 --format png`) gave frames byte-identical to the full render. Continuous term count `w` (last term weighted by `clip(w-k,0,1)`) makes "N → 99" sweeps smooth instead of stepping.
- **Build polylines yourself** (`VMobject.start_new_path` + `add_points_as_corners` on 4000 numpy samples) instead of `axes.plot` — vectorised, no smoothing overshoot on sin(99x), and trivially clippable to a zoom window (Liang–Barsky) because Manim has no clipping.
- **Layout moves as trackers too** — the parent graph's screen rect is `lerp(BIG, SMALL, z)` and the zoom panel's rect is `lerp(magnifier_box(z), PANEL, zq)`; the panel literally grows out of the magnifier box, and link lines follow for free.
- **Stagger inside one `play()` with windowed rate functions** (`late(t0, t1)`) — parent shrinks over [0, 0.7], panel opens over [0.3, 1.0]: fixes the panel covering the still-large parent (v1 → v2).
- **Merge with z-order, not opacity** (needs the `live()` fix below to actually work) — while the yellow sum morphs onto the stacked blue harmonic, put the blue *under* the yellow and fade it late; the opaque yellow covers it. Opacity cross-fades of blue and yellow gave 1–2 greenish frames (v1) or a yellow arriving at an unmarked place (v2).
- **One colour per entity, with a role change as the "adding" read**: every harmonic is blue while being added, yellow once inside the sum; the equation turns yellow left→right in lock-step with the graph.
- **bbox audit function** printing px boxes + pairwise overlaps with an allow-list, called at three key moments — cheap and caught nothing unexpected, which is the point.
- **Numerical verification script first** (`tools/verify_math.py`): coefficients by quadrature, Gibbs constant via `scipy.special.sici`, peak of S_N for several N → the on-screen "1.179" and "≈ 9%" are backed by numbers in NOTES.md.

- **Sequence layout moves one thing at a time** (reviewer fix): shrink parent → fade in magnifier box → grow panel; overlapping these three was the v1–v3 glitch.
- **A fresh-context reviewer subagent finds what the author normalises**: it caught the zoom blackout, the unshown jump of 2 behind "9%", and the too-short final hold.

## M− pitfalls
- **`always_redraw` loses z_index** — `Mobject.become()` copies points and style but not `z_index`, so a live mobject keeps the z_index of its *first* `func()` result forever (an empty `VMobject()` placeholder → z = 0). Symptoms here: the zoom panel's black fill painted over the parent mid-transition, the grey target sat above the yellow sum, and a z-order trick silently did nothing. Fix: a `live(func)` wrapper whose updater does `m.become(new); m.set_z_index(new.z_index)`, and give every placeholder its layer's z_index too. Found only because the fresh-context reviewer flagged the glitch; my own strips had shown it but I misread it as acceptable.
- **`self.play(..., rate_func=f)` silently overrides every animation's own `rate_func`** (manim/scene/scene.py: `setattr(animation, k, v)` for all play kwargs). Put rate funcs on each `x.animate(rate_func=…)` and pass only `run_time` to `play()`.
- **`uv init` inside a project folder creates a nested `.git`, `main.py`, an empty `README.md`, `.python-version`** → use `uv init --bare --python 3.12`.
- **`manim -qh` is 1080p *60***; the type doc wants 30 fps → `-qh --fps 30`.
- **pydub SyntaxWarnings** on every manim call under Python 3.12 → `export PYTHONWARNINGS=ignore::SyntaxWarning`.
- **`bin/vh check` flags 0–2.8 s as black** on a pure-black explainer with a thin grey curve (blackdetect default `pic_th=0.98`) and flags the intentional final hold as a freeze. Read them as false positives, not errors.
- **`bin/vh sheet` used to always write `<video dir>/check/sheet.png`** (overwriting every iteration). It was updated during this run: now `bin/vh sheet <video> [cols] [fps] [out]`, default `./out/check/<name>-sheet-<HHMMSS>.png` — a script that copies `check/sheet.png` afterwards now grabs a stale file.
- **The type doc's pacing (play 1–3 s + hold 0.5–2 s) does not fit 4 harmonic additions in < 25 s** — compress repeats (D5, D7), keep the first occurrence at full length.

## Commands that worked (macOS, M3 Max, uv 0.10.0, MacTeX)
```bash
cd <local path> && bin/vh new math fourier-square-wave
cd projects/2026-09-28-fourier-square-wave
uv init --python 3.12 && uv add manim          # worked (Manim CE 0.21.0, Python 3.12.2); then rm -rf .git main.py
# cleaner equivalent: uv init --bare --python 3.12 && uv add manim
export PYTHONWARNINGS=ignore::SyntaxWarning
uv run python tools/verify_math.py                                         # maths check
uv run manim -ql scenes/fourier.py FourierSquareWave                       # draft 854x480@15, ~22 s wall
uv run manim -qh --fps 30 scenes/fourier.py FourierSquareWave              # final 1920x1080@30, ~24 s wall (25.0 s video)
cp media/videos/fourier/1080p30/FourierSquareWave.mp4 out/final.mp4
../../bin/vh check out/final.mp4
../../bin/vh sheet out/final.mp4 6 1 out/check/final_sheet.png           # explicit out (updated reel)
../../bin/vh gif out/final.mp4 640 15                                     # -> out/final.gif (1.6 MB)
ffmpeg -ss 8.1 -i out/final.mp4 -t 2.9 -vf "fps=5,scale=480:-1,tile=5x3" -frames:v 1 out/check/strip.png
# determinism: render only animations 30–31 as PNGs and compare hashes with a full PNG render
uv run manim -ql --format png -n 30,31 --media_dir /tmp/jump scenes/fourier.py FourierSquareWave
```
