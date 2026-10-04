# BRIEF

<!-- 由 agent 根据用户需求填写。standard / studio 在关卡 ① 给人看；quick 不停，人点名要定的事除外（CLAUDE.md"导演模式"）。花括号里的都要替换。类型文档里的 "Prompt 增量块" 贴在文末 TYPE 一节。 -->

## Spec
- Effort: standard  <!-- quick | standard | studio：做多认真，规则见 CLAUDE.md "努力程度"。用户在对话里说的优先 -->
- Director: default  <!-- 谁拍板：default = 按 Effort 的默认；人点名的写成 hook=own, character=own, packaging=own, rest=delegate（own 人选 / review 人过目 / delegate agent 定），stop=E3 加一个检查点。规则见 CLAUDE.md "导演模式"，对话里说的优先 -->
- Output: {W}x{H}, {fps} fps, exactly {N}s ({frames} frames)
- Watch on: {watch}  <!-- 主要在哪看，定字号下限和可读性检查缩到多宽（playbook/03 §4）：phone 手机竖屏；feed 横屏片放在手机信息流里，竖着拿、不转屏；desktop 电脑，或手机转成横屏全屏。bin/vh new 按画幅填了默认值，人说了发在哪就照着改 -->
- Pace: normal  <!-- relaxed | normal | brisk：画面文字读得多从容，定 bin/vh readcheck 的目标（playbook/03 §2）。relaxed 讲解、论文、书信体，观众边读边想；normal 大多数片子；brisk 快剪、梗、卡点 MV。bin/vh new 给 math、paper 写 relaxed，meme 写 brisk，其余 normal。底线（够快读一遍）不随它变；某一段要换挡，在合成里标 data-pace -->
- Resolution: {res}  <!-- 默认 1080p。4k：照常按 1080p 写合成和字号，出片时渲成 4K（HyperFrames `render --resolution 4k`，竖屏 `portrait-4k`，方形 `square-4k`，4:5 没有 4K 预设；Manim `-qk --fps 30`；Remotion `--scale=2`）；canvas、Three.js 要按像素密度开大，否则会糊（engines/README.md"出 4K"）；手绘引擎暂不支持 4K；draft 用 1080p，4K 成片裁一两帧看锐不锐 -->
- Review language: zh  <!-- zh | en：审阅页和审阅台的界面语言，按用户第一句话的语言定（bin/vh new --lang）；字幕和项目文档照旧用项目自己的语言 -->
- Engine: {HyperFrames | Remotion | Manim CE | ClaudeAnimationBase (p5.brush) | other}
- Platform / audience: {where it plays, who watches, sound-on or muted}
- Language: {zh-CN | en}, narration: {TTS voice | user recording | song | none}
- Deliverables: {final.mp4 (+ 9:16 / 3:4 cuts?), cover image?, SRT?}

## Content
- Concept (one line): {the device that makes the form tell the content, e.g. "the 3 seconds after Enter, slowed to 2 minutes, a clock always on screen". Chosen at gate ① from 2–3 concept cards (playbook/12-ideation.md); everything below follows from it}
- Specifics: {the 3–5 items from NOTES.md 素材清单 the film is built on: numbers, verbatim quotes, artifacts, each with its source}
- Spine (one line): {the story in one sentence: X wants/asks ___, but ___, so ___}
- Recurring motif: {one object/visual that evolves and pays off}
- What the viewer should know/feel at the end: {…}
- Source material: {paper path / product URL / data.csv / song path / script}

## Outline
<!-- 关卡 ① 的 3–7 段大纲（playbook/09-narrative.md 第 3 节）。段名按内容或阶段起，看名字就知道这段讲什么，例如"按下发送 / 信道编码与调制 / 基站接住"；起承转合、幕这类结构标签最多写进"标签"列，可以不写。
     审阅台按这张表画时间条（列名的约定见 tools/desk/README.md）；时间写"0–10 s"，有配乐时也可以加"小节"列。 -->
| # | 段落 | 标签 | 时间 | 观众看完知道 / 感到 | 关键画面 |
|---|---|---|---|---|---|
| 1 | {按内容起的段名} | {可不写：起 / 承 / 转 / 合} | {0–10 s} | {…} | {…} |

## Style
- Style refs (repo presets): {none}  <!-- styles/ 里拿来参考的预设，bin/vh new --style a,b 或 bin/vh style apply 会填；参考，不是规定：借了什么记进 DECISIONS.md，和它们不一样不用解释 -->
- Refs (2–3 named works): {…}
- Explicitly NOT: {anti-refs, e.g. purple-cyan gradients, Pixar-like 3D, bullet-point slides}
- Palette: bg {hex}, fg {hex}, ONE accent {hex}; no pure #000/#fff unless chosen or required by the type doc (e.g. 3b1b-style black)
- Type: {display} + {mono | serif}; hierarchy by weight/size only

## Motion defaults (taste defaults, not floors: the concept may override any of them, one line each in DECISIONS.md; override per type doc; cartoon / hand-drawn projects follow ANIMATION_GUIDE.md instead — overshoot, takes and beat-locked idle motion are required there)
Entrances easeOutExpo cubic-bezier(0.16,1,0.3,1) / power3.out; exits ease-in at ~75% of entry; entries <=0.8s; total stagger <=0.5s. No bounce/elastic, no idle breathing loops, no crossfades between scenes; transitions grow out of content; 0.3–0.75s stillness before each climax.

## Text rules
<= {8} words (or {16} CJK chars per line) on screen; every must-read block stays at least one brisk read (max(1.5s, CJK/7 + other/20 + 0.8s): the floor) and by default reaches the Pace target (bin/vh readcheck; no fixed seconds); min sizes {..}px; everything inside safe box {x0–x1, y0–y1}.

## Determinism
Every frame is a pure function of t. No Math.random / Date.now / CSS transitions; seed all noise; no state carried between frames.

## Process
0. Concept first: list the material's specifics in NOTES.md (素材清单), write 5–8 one-line ideas before opening styles/, recipes/, cases or the TYPE block below, then 2–3 concept cards, each with its look, hook and taste overrides (playbook/12-ideation.md). Gate ① picks one card, which settles concept, style direction and hook. quick: three one-line ideas, pick one, no cards. If the user already gave a concept, write it here and skip the cards.
1. STORYBOARD.md: per shot = time range, VO/lyric, visual, focal element, the reads (each with start–end), transition out. Then stop where Effort and Director say (CLAUDE.md "导演模式"): gate ② for standard and studio, plus a stop for each decision the human owns; quick stops only for those.
2. Audio first: build audio/timeline.json; rewrite shot timings from measured durations.
3. Build scene by scene; after each scene render first/mid/last stills + a contact sheet + strips for key motions; critique against TASTE_CHECKLIST.md and log in NOTES.md; fix before moving on.
4. Uncertain facts go in NOTES.md, never invented into the video; creative decisions and their reasons go in DECISIONS.md, including every taste default the concept overrides.
5. Deliver: MP4 path, contact sheet of the whole piece, NOTES.md, the 2–3 spots you're least happy with.

## Acceptance
- [ ] {e.g. hook readable within 1s with sound off}
- [ ] {e.g. every number matches source}
- [ ] {e.g. 45s ±0.5s, 1080x1920, loudness -14 LUFS}

## TYPE
<!-- 类型的默认做法：语域、配色、节拍顺序是默认值，立意定了以后再取舍，和立意冲突时以立意为准，在 DECISIONS.md 记一行（playbook/12-ideation.md 第 6 节）。尺寸、事实纪律、平台安全区照旧。 -->
<!-- 在这里贴 video-types/*.md 的 "Prompt 增量块" -->
