# Showcase 02: Why does a LEO satellite's signal "change pitch"? (vertical knowledge short / HyperFrames)

![preview](media/preview.gif)

**Full video:** [media/final.mp4](media/final.mp4) · **Contact sheet:** [media/sheet.png](media/sheet.png) · **3:4 cover:** [media/cover.png](media/cover.png)

| | |
|---|---|
| Type / route | `short` → `video-types/02-knowledge-short.md`, engine HyperFrames |
| Output | 1080x1920, 30 fps, **24.8 s** (744 frames), silent (no audio stream), h264, 5.1 MB |
| HyperFrames | **0.8.82** via `npx` (Node 22), GSAP 3.14.2 (originally the scaffold's CDN tag; now vendored via `npm i` so renders don't hang offline), Noto Sans SC via Google Fonts `<link>` (localized at render time) |
| Render time (M3 Max) | final `--quality delivery`: **46.2 s** ("rendered in"), 49.3 s wall. First draft rendered in 13.8 s; after that run HyperFrames printed "parallel drawElement capture fell back to the screenshot path and is now off for this install", and every later render took ~41–46 s |
| Review iterations | 4 review passes: snapshot contact sheets → draft render + seam strips → frame-exact seam strips → final render + `bin/vh check`. Six renders in all (4 draft, 2 delivery). Every FAIL and fix is logged in [NOTES.md](NOTES.md) |
| Agent wall time | ~1 h 45 min from reading `CLAUDE.md` to delivery, including an API rate-limit pause |

## The request this was built from

> Topic (Chinese): 为什么低轨卫星的信号会"变调"？——多普勒频移. Audience: curious general public.
> 20–25 seconds, 1080x1920 vertical, 30 fps, SILENT (no TTS, no music): all information is carried by burned-in Chinese captions and visuals, so it must read with sound off.
> Key facts to get right (verify with your own calculation and log in NOTES.md): LEO at ~500–550 km orbits at ~7.6 km/s; Doppler shift f_d ≈ (v_radial/c)·f; at 2 GHz the maximum is about ±50 kHz, at Ka-band 20 GHz about ±500 kHz; frequency goes from positive (approaching) through zero (closest approach/overhead) to negative (receding) during one pass of several minutes; systems pre-compensate using known orbits. Keep claims modest and correct.
> Follow the type doc: hook in the first second, one idea per shot, new visual payoff every 3–5 s, caption rules, safe box x 90–900 / y 330–1520, "Kurzgesagt meets Fireship" flat look, one accent colour, no purple-cyan tech gradients or particles. Every frame deterministic.
> Do the review loop from playbook/02-verification.md (hyperframes lint/check/snapshot, contact sheets via bin/vh sheet, TASTE_CHECKLIST.md) and log critiques in NOTES.md. Approval gates skipped by the user; BRIEF/STORYBOARD/STYLE still written before coding.

## What's in the video
Hook: "卫星信号 / 会变调" at 140 px over an orange wave that squeezes, then stretches (0–3.2 s) → push left to a flat Earth with a satellite racing round a hugging orbit, `7.6 km/s` counting up, "离地 500–550 km" (3.2–6.2 s) → zoom-through into "you" on the ground: a sky dome, a dish that tracks the satellite, and an orange signal wave from antenna to dish. The wave is dense while the satellite approaches, even overhead and sparse as it recedes, and a chart underneath draws the real S-curve (+ → 0 → −) with a ring on the zero crossing (6.2–14.6 s) → the same chart glides up and grows; the formula Δf ≈ (v/c)·f; ticks ±50 kHz; a readout dot runs +46 → 0 → −46 kHz ("接近 ±50 kHz") → the axis zooms out ×10 to ±500 kHz, the 2 GHz curve flattens and the Ka 20 GHz curve draws at full height ("再大 10 倍") → a dashed mirror curve ("提前反向补偿") appears, both collapse into one flat orange line, "补偿后 ≈ 0", and the last caption is "反向补偿，不再变调" (20.4–24.8 s).

The chart is not hand-drawn. Each point comes from v_r = v·R⊕·sinθ / d for a 550 km orbit and a 10° elevation mask ([tools/doppler_calc.mjs](tools/doppler_calc.mjs), and the `PHYS` block in `index.html`), so the 2 GHz peak lands at 46 kHz, just under the ±50 kHz gridline. The wave-density change is exaggerated about 10⁴×, and the frame says so in small text ("示意：波长变化已放大").

## Files
- `BRIEF.md`, `STYLE.md` (palette with one accent `#FF8A3D`, type, motion tokens), `STORYBOARD.md` (shots, reads with timings, final caption script), `NOTES.md` (fact checks with the calculation output, creative decisions, 4 review passes), `LESSONS.md`, `TASTE_CHECKLIST.md`
- `index.html` (single monolithic composition: GSAP for text and seams, one `draw(t)` pure function for all physics visuals), `hyperframes.json`, `package.json`, `meta.json`, `tools/doppler_calc.mjs`

Reproduce (Node ≥ 22, ffmpeg, Chrome; network for Google Fonts (Noto Sans SC); GSAP comes from `npm i`):
```bash
export DO_NOT_TRACK=1 HYPERFRAMES_SKIP_SKILLS=1   # no telemetry; don't touch global ~/.claude/skills
node tools/doppler_calc.mjs
npx hyperframes@0.8.82 lint && npx hyperframes@0.8.82 check
npx hyperframes@0.8.82 render --quality delivery --fps 30 --output out/final.mp4
```

## What the harness docs helped with
- **Type doc `video-types/02`**: the hook-in-1s / what-you'll-learn-by-3s rule shaped S1, where the subtitle "原因：多普勒频移" lands at 1.2 s. The safe box x 90–900 made me center everything on x = 495 rather than 540. "One accent, flat vectors, no purple-cyan" held the palette to navy + one orange, with orange meaning "signal / frequency" throughout.
- **`playbook/01-pipeline.md` reads**: writing reads with start–end times before coding exposed the too-short captions (the first timeline had c6/c7 at 1.1–1.5 s) and forced the 24.8 s retime before any code existed.
- **HyperFrames `faceless-explainer` references + `motion-doctrine`**: the concept-explainer structure, the "reveal on cue, never front-load" rule, the vector law (push-slide LEFT, zoom-through with the same scale sign on both sides) and the carrier idea. The carrier idea led to the fix that carries "you" across the zoom seam.
- **`hyperframes-core` pitfalls**: `fromTo` instead of CSS transforms, and the rule against tweening `.clip`. Lint came back with 0 errors on the first run.
- **`playbook/02-verification.md` + `TASTE_CHECKLIST.md` + `bin/vh check`**: the reviews found real bugs. Three captions were 936 px wide in an 810 px safe box. A blank frame sat at the S1→S2 cut, visible only in a frame-exact strip. The push seam read as a fade. The "you" carrier jumped 176 px at the zoom. A 1.7 s freeze in S6a was fixed with the live kHz readout.

## Friction points (most important first)
1. **`engines/README.md` › HyperFrames: `npx hyperframes skills update` is not project-local.** The doc says "在项目里安装核心 skills（非交互）". The 0.8.82 CLI calls `npx skills add … --global --agent claude-code universal` (`GLOBAL_INSTALL_ARGS_TAIL` in `dist/cli.js`), which writes `~/.claude/skills` and `~/.agents/skills`. `hyperframes init` also refreshes the global skill set on every run (`--skip-skills` is "temporarily ignored"). The only opt-out is `HYPERFRAMES_SKIP_SKILLS=1`, and the harness mentions it nowhere. I never ran `skills update`, set `HYPERFRAMES_SKIP_SKILLS=1` for `init`, and read the skills from `references/repos/hyperframes/skills/` instead.
2. **`bin/vh new` + `engines/README.md` › HyperFrames conflict.** `bin/vh new short <slug>` creates a non-empty `projects/<date>-<slug>/` (templates, `audio/`, `assets/`, `out/`). The documented next step, `cd projects && npx hyperframes init <date>-<slug>`, then fails with "Directory already exists and is not empty". The workaround was to init in a temp dir and copy 6 files (`hyperframes.json`, `index.html`, `package.json`, `meta.json`, `CLAUDE.md`, `AGENTS.md`) into the project. The scaffold's own `CLAUDE.md`/`AGENTS.md` then sit inside the project and tell the agent to run global `skills update` and to route through the `/hyperframes` intent layer, which competes with the harness routing. I did not copy them into this showcase.
3. **`video-types/02-knowledge-short.md` › 字幕 + Prompt 增量块: "≤ 16 CJK chars, 72–90 px" cannot fit the safe box.** x 90–900 is 810 px wide, so 72 px fits 11 full-width characters and 90 px fits 9. Sixteen characters at 72 px is 1152 px, wider than the 1080 px frame. My first cut shipped three 13-character captions at 936 px (x ≈ 99–986) before the sheet caught it.
4. **No silent path in `video-types/02`.** 工作流 step 3 (音频先行 with TTS + FunASR), step 5 (字幕 split at ≥ 250 ms pauses) and the Prompt 增量块 ("zh-CN narration + burned-in captions", 30–60 s) all assume narration, and `bin/vh new` pastes that block into BRIEF.md as-is. `templates/BRIEF.md` › Process step 2 is "Audio first" too. The HyperFrames faceless marker (`music: none` + **no** `SCRIPT.md`) also conflicts with the type doc's "写 SCRIPT.md". I put the caption script in STORYBOARD.md instead. The updated `CLAUDE.md` hard rule 2 now covers silent videos, but the type doc and templates don't.
5. **`video-types/02` › 引擎 names `/faceless-explainer` as the primary route but doesn't say what it costs.** It expects the plugin or global skills, `hyperframes auth status` (HeyGen), `build-frame.mjs` presets, `audio.mjs`, and one sub-agent per frame. For a 25 s single-stage piece I hand-built one `index.html` and borrowed only its method. A sentence saying "for < 30 s or silent pieces, read the references and hand-build" would save the detour.
6. **`playbook/02-verification.md` › HyperFrames has no strip recipe, and `snapshot` is not render-exact at tween starts.** `hyperframes snapshot --at 3.2333` showed the S2 tween at its start state, while the rendered frame 97 at the same time had already moved a third of the way. The blank frame at the S1→S2 cut only showed up with `ffmpeg -vf "select='between(n,91,100)',tile=10x1"` on the mp4. That command belongs in the HyperFrames section.
7. **`bin/vh sheet` writes to a CWD-relative `out/check/`.** Its default output changed during this run. Running it from the repo root, as `CLAUDE.md` implies, created `OpenVideoHarness/out/check/…`, which I moved into the project. `bin/vh check`'s `freezedetect d=1.5` also flags 1.5 s where only a 26 px dot and a number move. The tool already says to review each hit; the TASTE_CHECKLIST #18 threshold (> 3 s) and this 1.5 s gate still disagree.
8. **`playbook/03-motion-design.md` › 4. 排版 (中文字体)** says to install Noto/Source Han locally or put it in `assets/`. HyperFrames lint errors (`font_family_without_font_face`) on any family that is not in its auto-resolved list, has no `@font-face`, and is not loaded through a Google Fonts `<link>`. Noto Sans SC is not in that list (only Noto Sans JP). A one-line "for HyperFrames: Google Fonts `<link>` or `@font-face`" would help.
9. Upstream, not harness, but worth a line in `engines/README.md`: two lint rules contradict each other. `gsap_repeated_fromto_without_baseline` suggests `tl.set(..., 0)`, which then triggers `gsap_timeline_set_initial_hide`. The fix is `gsap.set()` outside the timeline plus `immediateRender:false`. Also, the drawElement → screenshot fallback silently tripled render time for every later project on this machine; it can be re-enabled with `HF_DE_PARALLEL_ROUTER=true`.
