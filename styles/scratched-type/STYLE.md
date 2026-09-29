# 刮擦字片头 · scratched-type

一句话：字是手在黑色片基上刮出来的，一格一格地抖；画面由强迫症式的微距插入和神经质的剪辑拼成，底下是工业噪音的节奏。适合悬疑、犯罪、心理和黑暗题材的开场，工业、后朋克、噪音类音乐的 MV，以及任何要让观众"不安"的片头。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：0.0 s taiko 一击，第 1–4 帧一道刮痕带着火花撕过全屏；第 6 帧血红闪一下，0.4 s 一个 2 帧的微距，第 15–16 帧片头打孔闪亮，之后留下一个刮出的叉。片名和中文都是"刮"出来的，不是字体：每个字先栅格化，做 Zhang–Suen 细化，再追踪成骨架折线；每一笔用 2–4 条粗细不均、会断的细刮痕沿骨架走，有起笔顿点和乳剂崩口的白点，每 2 帧换一次抖动相位，保留重影和偶发跳帧。母题是三格散开的片格，各自在片门里错位跳动，只在一侧露出半个片孔；大纲、分镜，以及初版的红色换卷标记（cue mark）刮在里面。1.2 s 以及 2.0 / 2.4 / 2.8 / 3.2 / 3.6 s 每拍切入一个 2–3 帧的微距插入：字形、片孔、刮痕，片孔和刮痕两种故意做成暗的。4.0 s 血红闪帧，叠印 5 帧后转到刻着风格名的黑片头。红色全片共出现 3 次，亮的全屏闪每秒不超过 2 次。骨架来源字体：Helvetica Neue Regular（拉丁字母）、Kaiti SC（中文）；标签用 American Typewriter。配乐 150 BPM，taiko 隔拍一记，最后一段只剩 drone。拟音：刮痕落点用 swish_rev，红闪用 impact，打孔和片孔插入用 shutter，其他插入用 glitch，每个词开刻时一声轻 swish_rev。拟音的落点写在 swatch.js 的 `FOLEY` 常量里，`events.json` 由它生成。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《七宗罪》*Se7en* 片头 | 1995 · Kyle Cooper（R/GA West）；剪辑 Angus Wall；摄影 Harris Savides；音乐为 Coil 与 Danny Hyde 重混的 Nine Inch Nails《Closer》（Art of the Title 拼作 Danny Hide） | 字手刻在黑色刮画板上，转印时再抹花、抖动；画面是极短的微距插入加胶片杂质，大部分靠光学印片手工拼成 |
| *Blinkity Blank* | 1955 · Norman McLaren（加拿大国家电影局 NFB） | 图形直接刻在黑色片基上，一闪即逝，故意留下空白帧，像"在时间上撒点"；声音也是刻在光学声轨上的 |
| *Free Radicals* | 1958 年初版，1979 年定剪 · Len Lye | 白色刮痕在黑底上随打击乐跳动：刮痕本身就是节奏 |

核实：《七宗罪》片头的职员表和技法描述来自 Art of the Title；另外两部的年份和技法来自 Wikipedia、NFB 与 LUX 的页面。

**不照搬**：不做原片的笔记本内页、剃刀、指纹、剪照片的手这些具体镜头；不用《Closer》或任何 NIN 的声音；不写"无名凶手"式的剧情暗示。

## 视觉语法

- **色板**：

  | token | hex | 语义 |
  |---|---|---|
  | bg 片基黑 | `#0C0B0A` | 永远的底，不用 `#000` |
  | fg 刮痕白 | `#E6DFCF` | 字和刮痕：乳剂刮掉后透出来的光 |
  | accent 干血红 | `#9E1B14` | 全片最多出现 3 次，每次是 ≤ 3 帧的闪帧或一个词 |
  | extra 棕褐 | `#5C4E3D` | 过曝的微距插入 |
  | extra 灰片头 | `#2B2926` | 引导片、分隔段 |
  | extra 骨白 | `#B8AE98` | 次要字、刮痕余光 |

- **字体**：字是"刮"出来的，字体只提供骨架。
  - 展示骨架用 Helvetica Neue，UltraLight 和 Condensed Bold 两种（fallback Arial Narrow）；
  - 打字机插入用 American Typewriter（fallback Courier New）；
  - 中文骨架用 Kaiti SC，楷体自带手写感（fallback Songti SC Light）。

  刮法：沿字形中轴描 2–4 条细线，彼此错开 0.6–1.5 px，线宽 1.2–2.5 px；每条线沿弧长加低频抖动，每隔 20–60 px 断开 3–8 px；笔画末端拖出一条 10–40 px 的"失手"余痕。所有随机都来自 `hash(glyphIndex, strokeIndex)`。
- **构图**：一格里只放一件事：一个词、一个微距局部，或一道刮痕。字常偏在画面一侧，或压出画面边缘 5–15%；微距插入占满全屏，主体 ≥ 70%。字号对比拉到 5 倍以上，例如一个 220 px 的词配 44 px 的小字。
- **质感**：film，强度 0.35。
  - 颗粒；
  - 片门抖动（gate weave），x ±1.5 px、y ±2 px，低频；
  - 灰尘和发丝，每秒 2–6 个，每个停 1–2 帧；
  - 偶尔出现片头打孔；光学接缝处 1 帧过曝闪。

  叠印：同一个词错开 4–12 px，以 0.35 的透明度叠一层鬼影。

## 运动语法

帧数一律按 30 fps 计。

- **缓动**：几乎不用补间。字和插入镜头靠**切**出现，唯一的"补间"是抖动和抹花。确实需要位移时，用接近瞬移的 snap：`cubic-bezier(0.9,0,0.1,1)`，4 帧。
- **抖动**：字每 2 帧换一次位置（±2–4 px）和角度（±0.6°），由 `hash(floor(t*15))` 决定。每 8–20 帧有一次"跳帧"：偏移 10–30 px，停 1 帧后回原位。
- **时长**（stutter edit）：插入镜头的长度从 {2, 3, 5, 8, 13} 帧里取。一张字卡整体可见 ≥ 1.2 s，其间至少 70% 的帧能读出这个词。每 0.4–0.6 s 必须有一次新的切。
- **转场**（全片只用这 3 种）：
  - 硬切；
  - 1 帧闪帧，白或干血红，每秒不超过 3 次（WCAG 2.3.1 的闪烁阈值）；
  - 叠印过渡：新旧两格叠 3–6 帧，两格都在抖。这不是 crossfade。
- **镜头**：固定机位加片门抖动；微距插入里允许极慢的推，每秒放大 1–2%。
- **文字动画**：签名是 scratch。刮痕按笔顺在 6–10 帧内"刻"出来，每帧多刻 1–2 笔，刻完就开始抖。退场是被抹花：4 帧内水平拉伸 1.0 → 1.6，透明度降到 0。

## 声音语法

- **配乐**：工业 / 噪音节奏，96 BPM，E 小调；一个低频脉冲、金属打击，加一条失真的持续音。`bin/vh music` 的近似做法：
  - 低 energy 的 `kick`、`hats`、`bass`；
  - 低通的 `pad` 当 drone；
  - energy 保持在 0.4–0.7，不进满编的 drop。

  `taiko` 层隔拍一记，垫在金属打击下面当低鼓。刮擦声、磁带声、放映机噪声要在项目里自己合成（带通噪声 + 随机脉冲）。
- **音效**：
  - `glitch` 配跳帧；
  - `shutter` 配闪帧（放映机快门的感觉）；
  - `typing` 配打字机插入；
  - `click` 配每一道刮痕刻下；
  - 片尾一个 `impact`。
- **声画关系**：每个切都有声音，声音自己也会"卡"：同一个 60–120 ms 的片段重复 2–3 次（stutter）。片中不留数字静音，底下始终垫着低音 drone。最后一个字出现时，其余声音全部收掉，只剩 drone。

## 适合与不适合

- **适合**：04 MV（工业、后朋克、电子噪音）；08 野兽派快剪的片头；03 里偏暗的游戏或安全产品 teaser；悬疑、犯罪、心理题材的开场。
- **不适合**：温暖的品牌片、儿童内容、知识讲解的主体段落（字抖得读不完）；对闪烁敏感的观众（闪烁上限必须守住）。
- **容易被误用成**：把"抖"做成随机 CSS shake，或者在白底上做"脏字"。这个风格的前提是黑片基，和从刮痕里透出的光。

## 禁止项

1. 用 `Math.random()` 做抖动，同一帧渲染两次结果不一样。
2. 全屏闪帧每秒超过 3 次，或者红色闪帧连着出现。
3. 字抖到读不出：关键词在它那 1.2 s 里，可读帧不到 70%。
4. 现成的数字 glitch 滤镜（RGB 分离、datamosh 色块）。这里要的是胶片的毛病，不是数字的毛病。
5. 纯白 `#FFFFFF` 的干净矢量字，或者整段没有一道刮痕。
6. 把原片的具体镜头（笔记本、剃刀、指纹）当作"风格元素"复刻。

## Prompt 块

```text
Visual style: hand-scratched, jittery industrial title design. Warm black film base #0C0B0A; all type is scratched out of the emulsion as thin, broken, doubled strokes of light #E6DFCF (2–4 offset hairlines per stroke, gaps and slips, a trailing mistake at the end of each stroke). Words appear by cutting, never by fading; each word holds for 1.2 s but jitters every 2 frames (±3 px, ±0.6°), with an occasional 1-frame jump and a faint double-exposed ghost. Between words come full-frame macro inserts, 2–13 frames long, of textures related to the topic, plus film grain, dust, gate weave and a punched leader frame. One dried-red #9E1B14 flash frame appears at most three times in the film, never more than 3 flashes per second. No digital glitch effects, no RGB split, no clean vector type. Sound: a 96 BPM industrial pulse in E minor, metallic hits, a stuttering loop on every cut, and a low drone underneath instead of silence.
```

## 引擎做法

- 首选 HyperFrames 的 Canvas 层，或纯 Canvas2D 的 `render(t)`：每帧重画整张，方便叠鬼影和颗粒。p5 也可以。
- **刮字**：给每个字建骨架折线，别用"细字重描边 + 错位"，那样做出来是做旧字体。样片的做法：
  - 字形以 2 倍尺寸画进离屏 canvas；
  - Zhang–Suen 细化；
  - 按 4 邻接优先追踪成折线，闭合的圈（o、e、口）要在离起点最远处拆开再做 RDP 简化，否则会塌成一个点；
  - 标点这类细化后没剩下笔画的字，用墨迹质心补一小道刻痕。

  每笔交给 `scratch(stroke, upto, phase, seed)`：2–4 条细线，宽度按噪声分三档批量描边，噪声超阈值处断开，起笔画顿点，沿线撒崩口白点。骨架在 `setup` 里算一次，逐帧只改相位和抖动。
- **离散时间**：`tj = Math.floor(t * 15)`，抖动量 = `hash(tj, wordId)`。插入镜头的切点表写在 `timeline.json` 里，长度从斐波那契帧数里取。
- **胶片层**：颗粒、灰尘、发丝全部由 `hash(frame, i)` 决定；gate weave 用两个低频正弦叠加（0.7 Hz 和 1.3 Hz）。颗粒也可以交给 ffmpeg 的 `noise=alls=12:allf=t`，强度看成片再调。
- **闪帧检查**：渲染后用 ffmpeg 算出每帧的平均亮度，统计亮度跳变，保证每秒不超过 3 次。

## 自查重点

- 从中间抽 3 帧单独渲染，与整片里的同一帧逐像素比对。抖动最容易破坏"帧是 t 的纯函数"这条硬规则。
- 为每个关键词的 1.2 s 拉一条逐帧 strip，可读帧 ≥ 70%。
- 亮度跳变统计：全片每秒不超过 3 次闪。
- 刮痕 crop 放大到 200% 看：要有断口、错位的双线和末端余痕，不能是一条均匀的描边。
- 1 fps 联系表：干血红一共出现不超过 3 次。

## 相关资源

- lemo-opuscar 里没有直接对应的风格。最接近的是 `references/repos/lemo-opuscar/styles/halftone-dossier/STYLE.md`（逐件出示证物的案卷叙事）和 `backrooms`（找回的录像带质感），均为 LemoLab，CC BY 4.0。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 里的 Deconstructed：同样工业、粗粝，但它用数字 glitch，本风格禁止。
- `video-types/04-lyric-music-video.md`、`video-types/08-brutalist-meme.md`、`playbook/08-vfx-and-motion-sources.md`（闪白上限、子帧运动模糊）。
