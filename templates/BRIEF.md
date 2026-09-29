# BRIEF

<!-- 由 agent 根据用户需求填写，填完给用户确认（关卡 1）。花括号里的都要替换。类型文档里的 "Prompt 增量块" 贴在文末 TYPE 一节。 -->

## Spec
- Effort: standard  <!-- quick | standard | studio：做多认真，规则见 CLAUDE.md "努力程度"。用户在对话里说的优先 -->
- Output: {W}x{H}, {fps} fps, exactly {N}s ({frames} frames)
- Engine: {HyperFrames | Remotion | Manim CE | ClaudeAnimationBase (p5.brush) | other}
- Platform / audience: {where it plays, who watches, sound-on or muted}
- Language: {zh-CN | en}, narration: {TTS voice | user recording | song | none}
- Deliverables: {final.mp4 (+ 9:16 / 3:4 cuts?), cover image?, SRT?}

## Content
- Spine (one line): {the story in one sentence: X wants/asks ___, but ___, so ___}
- Recurring motif: {one object/visual that evolves and pays off}
- What the viewer should know/feel at the end: {…}
- Source material: {paper path / product URL / data.csv / song path / script}

## Style
- Refs (2–3 named works): {…}
- Explicitly NOT: {anti-refs, e.g. purple-cyan gradients, Pixar-like 3D, bullet-point slides}
- Palette: bg {hex}, fg {hex}, ONE accent {hex}; no pure #000/#fff unless chosen or required by the type doc (e.g. 3b1b-style black)
- Type: {display} + {mono | serif}; hierarchy by weight/size only

## Motion defaults (override per type doc; cartoon / hand-drawn projects follow ANIMATION_GUIDE.md instead — overshoot, takes and beat-locked idle motion are required there)
Entrances easeOutExpo cubic-bezier(0.16,1,0.3,1) / power3.out; exits ease-in at ~75% of entry; entries <=0.8s; total stagger <=0.5s. No bounce/elastic, no idle breathing loops, no crossfades between scenes; transitions grow out of content; 0.3–0.75s stillness before each climax.

## Text rules
<= {8} words (or {16} CJK chars per line) on screen; each block visible >= {2.5}s; min sizes {..}px; everything inside safe box {x0–x1, y0–y1}.

## Determinism
Every frame is a pure function of t. No Math.random / Date.now / CSS transitions; seed all noise; no state carried between frames.

## Process
1. STORYBOARD.md: per shot = time range, VO/lyric, visual, focal element, the reads (each with start–end), transition out. Stop for approval.
2. Audio first: build audio/timeline.json; rewrite shot timings from measured durations.
3. Build scene by scene; after each scene render first/mid/last stills + a contact sheet + strips for key motions; critique against TASTE_CHECKLIST.md and log in NOTES.md; fix before moving on.
4. Uncertain facts and creative decisions go in NOTES.md, never invented into the video.
5. Deliver: MP4 path, contact sheet of the whole piece, NOTES.md, the 2–3 spots you're least happy with.

## Acceptance
- [ ] {e.g. hook readable within 1s with sound off}
- [ ] {e.g. every number matches source}
- [ ] {e.g. 45s ±0.5s, 1080x1920, loudness -14 LUFS}

## TYPE
<!-- 在这里贴 video-types/*.md 的 "Prompt 增量块" -->
