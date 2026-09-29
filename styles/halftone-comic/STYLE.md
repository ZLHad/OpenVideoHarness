# 半调漫画 · halftone-comic

一句话：把每一帧当成印出来的漫画页：网点代替渐变，四色版故意套不准，远处的东西用更大的错位代替虚化；角色按一拍二动，拟声词是画面的一部分，画面可以像漫画一样被切成几格。适合动作感强、节奏快、有"砰"一下的时刻的内容。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 0 帧标题格砸进来并铺满画面（黄底，品红网点只在边缘，速度线按 6 fps 换张），配一记 `impact`；标题字母像字块一样一拍二砸到位，中文在黄色旁白框里；2.0 s 标题格缩成顶部横幅，三格同时落下："铅笔稿 → 墨线 → 上色"对应大纲、分镜、初版（画的是一道闪电，不用 ▶）；2.5 s 初版格弹出"BAM!"，C/M/Y 三块版一起踢开约 9 px 再回位，3.0 s 再砸一次，3.5 s 格内一抖；3.5–4.0 s 音乐抽空只剩 `pad`；4.0 s 一条斜切把页面切开，只用实色油墨的结束格（黄底红光芒）顺着切口滑进来。实际字体：Futura Condensed ExtraBold、Avenir Next Condensed Demi Bold、HanziPen SC Bold。配乐 120 BPM、E 小调、半速 breakbeat，小节排成 4 + 1 + 2 + 1 + 4 拍：0 s、2.5 s、4.0 s 各一记 `impact`，2.5–3.5 s 加 `taiko`。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《Spider-Man: Into the Spider-Verse》 | 2018 · Sony Pictures Animation（Sony Pictures Imageworks 制作），导演 Bob Persichetti、Peter Ramsey、Rodney Rothman；获第 91 届奥斯卡最佳动画长片 | 一拍一和一拍二在同一场戏里混用，用帧率表达角色的状态；用印刷套版错位代替镜头景深；网点表示明暗；拟声词、旁白框、速度线直接进画面 |
| Ben-Day 网点印刷法 | 1879 · Benjamin Henry Day Jr. | 网点大小就是明度；每块色版一个网角；网点是印刷的物理事实，不是滤镜 |
| 《Whaam!》等网点绘画 | 1963（未核实）· Roy Lichtenstein | 把网点放大到看得见；粗黑轮廓 + 平涂原色 + 拟声字块，三样就够 |

核实：片名、上映年份、导演、制作方和奥斯卡来自 Wikipedia；"一拍一 / 一拍二混用、错位代替景深、网点、拟声词"来自 Wikipedia 的 Animation 一节和多篇制作拆解；Ben-Day 法的发明人和年份来自 Wikipedia（同一条目提到 Lichtenstein 放大网点的做法）。《Whaam!》的年份 1963 是常见馆藏信息，本轮没有单独复核，按未核实处理。

**不照搬**：不用任何漫威角色、制服、面具和蛛网纹样，不复刻片中的具体镜头、标题字体和配色；不临摹 Lichtenstein 的具体画作。

## 视觉语法

- **色板**：新闻纸上的四色印刷（CMYK）加一个击中红。

  | token | hex | 语义 |
  |---|---|---|
  | bg 新闻纸 | `#F5EEDC` | 纸白；高光处留纸，不画白 |
  | fg 黑版 K | `#1A1A1A` | 轮廓、实黑阴影、字的描边；黑版永远对准 |
  | 青 C | `#00A3E0` | 冷、阴影、远处 |
  | 品红 M | `#E5287B` | 情绪、危险 |
  | 黄 Y | `#FFD400` | 能量、拟声字底、旁白框 |
  | accent 击中红 | `#E63B2E` | M+Y 叠印的红，只给击中瞬间和最重要的拟声词 |
  | 夜场靛 | `#1C1F3B` | 夜景的底，网点改用青和品红 |

- **字体**：拟声词和大标题用 Futura Condensed ExtraBold，粗黑描边（字高的 8%）加错位的黄色投影；旁白框和标签用 Avenir Next Condensed Demi Bold，全大写。中文拟声词和旁白用 HanziPen SC Bold（翩翩体，手写字母感），标签用 PingFang SC。
- **构图**：画面可以切成 2–4 格：格与格之间 12 px 纸白沟 + 6 px 黑框；同时出现的格表示同时发生的事，斜切的格表示冲突。主体偏心放；速度线从焦点放射；旁白框（黄底黑字矩形）贴在格的左上角。拟声词可以越出格框。
- **网点与错位**：网点周期 10–14 px（1080p 交付；720p 交付或码率吃紧时放大到 16–18 px），网角 C 15°、M 75°、Y 0°、K 45°。网点只用在中间调和阴影，高光留纸白，暗部用实黑。套版错位：静止镜头里 C、M 版固定偏移 ±2 px，黑版对准；越远的东西错位越大（背景 6–10 px），用它代替景深虚化。
- **质感**：halftone 0.6，加一层很淡的油墨不匀，不加胶片颗粒。

## 运动语法

帧数按 24 或 30 fps 计；一拍二写成 `lib.step(t, 12)`。

- **帧率就是表演**：角色、拟声词、速度线按 12 fps 换张（一拍二）；平静段落可以一拍三（8 fps）；高潮的一两个动作一拍一。镜头推拉和整格滑动永远每帧更新，否则会被看成卡顿。
- **击打**：不缓动，3 帧内到位，停 2 帧，再做跟随。入场 easeOutExpo `cubic-bezier(0.16,1,0.3,1)`；退场 easeInExpo。
- **拟声词**：6 帧内从 30% 放到 115% 再回到 100%（弹簧 stiffness 400 / damping 24，ζ≈0.6，俏皮语域允许），落定后停 ≥ 0.6 s；它的出现帧就是对应音效的峰值帧。
- **套版踢一下**：击中时 C、M 版向相反方向踢开 8–12 px，0.25 s 内衰减回固定偏移；平时不抖。
- **时长**：每一格至少 1.2 s；每 1.5–2 s 一个新格或新动作。
- **转场**（只用这 3 种）：
  - 分格切（panel-split）：画面沿斜线切开，新的一格从切口滑进来；
  - 网点擦除（dot-wipe）：网点逐渐长大盖满全屏再缩小，约 0.45 s，换场发生在全覆盖的那一帧；
  - 撞击硬切（smash-cut）：1 帧纸白闪 + 硬切，只在最大的一击用。
- **镜头**：推拉（dolly）加 5–12° 的荷兰角；推近用在击打前的蓄力。
- **文字动画**：剪贴砸入（cutout）：字母像剪下来的字块，一拍二地一个个砸到位，带过冲。

## 声音语法

- **配乐**：E 小调，120 BPM（24 fps 下一拍 12 帧，一拍二正好 6 张；30 fps 下 15 帧），半速感的 breakbeat 律动：`kick`、`clap`、`hats`、`bass`，高潮加 `lead`，大击打加 `taiko`。
- **音效**：每个拟声词都有真实的声音，同一帧：`impact`、`boom`、`whoosh`、`swish_rev`；分格切用 `shutter`；套版踢一下配一声短 `glitch`（音量 −12 dB，不要电子味太重）。
- **声画关系**：拟声词的字号 ∝ 音量；重击前 0.3–0.5 s 全部音乐抽空，再一起砸下去。
- **样片拟音**：`events.json` 15 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs <slug>` 生成，落点全部引用动作所用的同一张时间表，声像取发声物体的屏幕 x（`(2x/W − 1)·0.7`），−3 dB 混在配乐下：标题格砸进来 `impact`；标题每个词砸下、中文字幕框弹出各一声 `pop`，落点按一拍二（12 fps 姿势）换算到实际出现的那一帧；标题格缩成横幅 `whoosh`；三格落下各一声 `pop`；BAM! `impact`，3.0 s 再砸一下小一点的 `impact`，最后一抖 `click`；对角分格 `shutter` + `whoosh`。

## 适合与不适合

- **适合**：08 快剪和梗；04 嘻哈、摇滚、电子 MV；02 竖屏科普里的"高能"段落；03 游戏、运动产品。
- **不适合**：严肃的长讲解、医疗和悲伤题材、需要读大量文字的内容。
- **容易被误用成**：给普通画面盖一层网点滤镜再加 RGB 色差 glitch，没有印刷逻辑。

## 禁止项

1. 网点当全屏滤镜：高光也铺满网点，暗部也是网点。
2. 用 RGB 色差（屏幕 glitch）代替印刷套版错位。错开的是 C/M/Y 油墨版，颜色是减色叠印出来的。
3. 每帧随机抖动套版。错位按镜头固定，只在击打时踢一下。
4. 连镜头也一拍二，推拉变成卡顿。
5. 拟声词没有对应的声音或动作。
6. 挪用超级英雄的制服、面具、蛛网图案。

## Prompt 块

```text
Visual style: printed comic page in motion. Newsprint #F5EEDC, process inks only: black #1A1A1A keyline and solid shadows, cyan #00A3E0, magenta #E5287B, yellow #FFD400, with red #E63B2E (magenta over yellow) reserved for impacts. Shading is Ben-Day halftone, 10–14 px dots, screen angles C 15°, M 75°, Y 0°, K 45°; highlights stay bare paper, darks go solid black. Colour plates are slightly misregistered (C and M ±2 px, black always in register); distant layers get 6–10 px of misregistration instead of depth-of-field blur. The frame can split into 2–4 panels with white gutters and black borders, diagonal cuts for conflict. Characters, speed lines and onomatopoeia animate on twos (12 fps), calm beats on threes, the biggest hit on ones; camera moves and panel slides stay smooth every frame. Hits land in 3 frames with no easing, hold 2 frames, then follow through. Onomatopoeia in condensed heavy caps (Futura Condensed ExtraBold) with a thick black outline and an offset yellow shadow, popping 30%→115%→100% in 6 frames, held at least 0.6 s, always with a matching sound on the same frame. Transitions: diagonal panel split, halftone dot wipe, one white-flash smash cut. No RGB chromatic aberration, no per-frame registration jitter, no superhero costumes or web motifs. Sound: 120 BPM half-time breakbeat, silence 0.3 s before each big hit.
```

## 引擎做法

- **首选 HyperFrames**：Canvas2D 画分版密度，再用 `lib.shader` 做印刷。每块版（C、M、Y、K）先画成一张灰度"密度图"，着色器里按各自网角的旋转网格算网点半径，加上各自的偏移，最后减色合成：`纸 × Π mix(1, 油墨色, 覆盖率)`。
- 不用着色器时，`lib.halftone(ctx, 密度函数, {cell, angle, color})` 逐版画点，版与版之间用 `multiply` 叠。
- **一拍二**：`const tp = lib.step(t, 12)`，只喂给角色、拟声词和速度线；镜头和分格滑动用 t。
- **套版踢**：`off = 固定偏移 + A · e^(−τ/0.08) · cos(2π · 6 · τ)`，τ 是距击中的时间。
- **编码**：网点在 yuv420 下会糊，中间帧用 PNG，交付时看 100% 和 50% 两档有没有摩尔纹。
- **码率**：网点固定在屏幕上，所以任何整屏平移或推拉都会让每一帧的网点重新采样，x264 码率成倍上涨。样片的做法：带网点的格子不整格平移；要滑动的格子（结束格）只用实色油墨（黄底、红光芒、白字），滑进来几乎不花码率；标题格的品红网点只放在边缘，中间是实色；网点周期放大到 17 px（1080p 渲染、720p 交付时 10–14 px 的点会糊，也更费码率）。
- 样片 `swatch.js`：逐段做法见开头"样片里"。实现要点：标题格从铺满画面缩成横幅时，网点区域跟着变形，这 0.2 s 最费码率，要尽量短；三格落下用每帧平滑的位移，格里的角色和字仍然一拍二。

## 自查重点

- 成片缩到 50% 看有没有摩尔纹，编码后品红、青网点是否还干净。
- 错位只发生在 C/M/Y 版，黑版对准。
- 6 帧 strip：角色和拟声词按 12 fps 换张，镜头每帧平滑。
- 每个拟声词：有声音、有动作、停 ≥ 0.6 s、字高 ≥ 画面高的 12%。
- 手机缩略图上主体剪影可读，网点没有抢掉轮廓。

## 相关资源

- `references/repos/lemo-opuscar/styles/halftone-dossier/STYLE.md`（LemoLab，CC BY 4.0）：网点密度场、多网角叠印、网点擦除转场、印章砸下的节奏。本文借了网点与擦除的做法，但方向不同：它是奶油纸上的慢节奏"案卷"，本预设是动作漫画页、一拍二和分格。
- `references/repos/lemo-opuscar/styles/risograph/STYLE.md`：分版密度 + 着色器印刷的管线。
- `video-types/08-brutalist-meme.md`、`video-types/04-lyric-music-video.md`；`playbook/08-vfx-and-motion-sources.md`（闪白每秒不超过 3 次）。
