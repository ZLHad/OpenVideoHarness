# 工程蓝图 · blueprint

一句话：一张普鲁士蓝的晒图纸，白色工程线按制图顺序画出来：中心线 → 轮廓 → 细节 → 剖面线 → 尺寸 → 引出编号；尺寸会跟着零件的移动实时改变。适合讲结构、机制、硬件构造、系统架构，以及一切"被设计出来的东西"。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 0 帧起晒图纸从画面顶端展开，0.3 s 铺满（hook，第一拍两台马林巴和颤音琴一起进来）；0.3 s 一条 5 px 的点划线基准中心线从画外射入，竖向中心线随后落下，0.55 s 交点上落一个十字准星；0.6 s 起标题在两条字高导线之间逐笔写出，笔头发亮；三张图放大到约 440×280：FIG. 1 大纲（中心线和构造线）→ FIG. 2 分镜（轮廓和隐藏线，2.6–3.0 s 一条剖切线 A–A 扫过）→ FIG. 3 初版（剖面排线、尺寸、编号）；3.1–3.7 s 初版零件拉长，58 px 的尺寸数字按整数从 440 数到 520，外面圈一圈审图黄修订云；4.0 s 镜头横移并推近到标题栏，镜头被限制在图纸以内，不露桌面。实际字体：DIN Condensed Bold、DIN Alternate Bold、STFangsong（横向压到 72%）。配乐 90 BPM、D 大调，小节排成 3 + 2 + 1 + 3 拍，是 Steve Reich 式的极简主义：左右两台 `marimba` 弹同一个 12 格的十六分音符音型（D–A–F♯–E–A–D–B–E，每三格空一格），右边那台晚两格，合起来是连续的十六分音符；`sub808` 当干净的正弦低音按四分音符打拍，每段第一拍 `vibraphone` 敲一个和弦报段落。2.0 s 进 V 级，右边那台再晚两格，合成出另一条旋律；3.33–4.0 s 定稿前一小节马林巴全停，只剩颤音琴的 vi7 和弱低音，计数的 `tick` 在这里听得最清楚；4.0 s 两台马林巴错开半圈回来，节奏对齐，像落定。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 蓝晒法（cyanotype） | 1842 · John Herschel | 白线蓝底的由来：曝光处变成普鲁士蓝，线条处留白；纸上有涂布不匀、折痕和晒白的边 |
| 19 世纪美国专利图纸的通行画法 | 19 世纪 · 美国专利局的图纸惯例（不指定具体图） | Fig. 1 / Fig. 2 的编号；零件引出线 + 编号圆圈；用细密排线表现曲面和剖面 |
| 《Iron Man》片尾字幕 | 2008 · Prologue Films，创意总监 Danny Yount | 技术图解动起来：爆炸视图里零件沿轴飞出又归位；画面再跳，镜头移动始终稳定 |
| 技术制图线型与字体标准 | ISO 128（现行版本号未核实）；GB/T 14691-1993《技术制图 字体》 | 线型就是语义：粗实线 = 可见轮廓，虚线 = 隐藏线，点划线 = 中心线，粗点划线 = 剖切面；中文字写成长仿宋体，字宽约为字高的 1/√2 |

核实：蓝晒法的发明人和年份来自 Wikipedia（Cyanotype、Blueprint 条目）；《Iron Man》片尾的制作方和创意总监来自 Art of the Title 与 Motionographer；GB/T 14691 对长仿宋体的规定来自国家标准全文公开系统的条目和机械制图手册摘录。ISO 128 当前的分部版本号没有核对。

**不照搬**：不用任何真实专利图、盔甲造型或真实品牌产品的外形；不复刻 lemo 样片里"修订云变成真云"这一桥段（"一个制图符号变成真东西"这个语法可以用，但换一个符号）。

## 视觉语法

- **色板**：蓝和白两种，外加一个"审图黄"。

  | token | hex | 语义 |
  |---|---|---|
  | bg 深纸蓝 | `#173A6E` | 晒图纸暗处；纸面在它和浅纸蓝之间做低频起伏 |
  | 浅纸蓝 | `#2A5C9E` | 晒图纸亮处 |
  | fg 线白 | `#E8F1FA` | 已画定的线和字 |
  | 辅线蓝白 | `#A9C6E8` | 尺寸线、引出线、构造线（构造线再降到 35%） |
  | 晒白边 | `#5B83B8` | 纸边漂白、折痕的亮边 |
  | 台面 | `#0E1218` | 纸以外的桌面 |
  | accent 审图黄 | `#F4C542` | 本镜的改动或重点：修订云、被改的尺寸。每个镜头最多一处 |

- **字体**：标题栏和大字用 DIN Condensed（工程感的窄体），尺寸数字和注释用 DIN Alternate，数字 `tabular-nums`；中文用 STFangsong（仿宋），横向压到 72% 宽，接近国标的长仿宋体。所有字先画两条淡淡的字高导线，再写字，这是手工制图的习惯。
- **构图**：整片在一张图纸上：外框、右下角标题栏、一侧的注释栏。主图占画面高 55–70%，放在图纸左 2/3，右 1/3 留给零件表和注释。镜头像一双读图的眼睛，推近局部、横移到下一个 Fig.。
- **线宽**（1080p 屏幕像素）：轮廓 3.0，细节 2.0，尺寸与引出 1.2，构造线 1.0 @ 35%。虚线：中心线 `[24, 6, 4, 6]`，隐藏线 `[10, 6]`，剖切线 `[28, 5, 4, 5, 4, 5]`。镜头推近时线宽按 `w × zoom^0.6` 变粗，不按 zoom 线性放大。
- **质感**：纸面 fbm 亮度 ±8%、横向涂布条纹、十字折痕（亮边 + 暗边）、晒白的纸边；线条轻微洇开（0.6 px 模糊加 3 px、10% 的光晕）。纸纹强度 0.35，不加电子扫描线。

## 运动语法

帧数按 30 fps 计。

- **画线**：每一笔用 easeInOutSine `cubic-bezier(0.37,0,0.63,1)`，整体笔速约 900 px/s；笔头有一个 4 px 的亮点；同一层内各笔错开 60 ms。每一层（中心线、轮廓、剖面线、尺寸……）从一个拍点开始。
- **活的尺寸**（签名）：尺寸线量的是真实比例的东西；零件伸长或移动时，尺寸线跟着伸缩，数字按整数跳变（`tabular-nums`，单位 mm）。
- **爆炸视图**：零件沿各自的轴飞出，每个零件间隔一个八分音符，easeInOutCubic；归位时用临界阻尼弹簧（stiffness 600 / damping 49，ζ = 1，不回弹）加一声咔哒。
- **时长**：一层 0.5–1.2 s；一张图画完后停 ≥ 1.5 s；每 2–3 s 一个新层或新动作。
- **转场**（只用这 3 种）：
  - 图号横移（fig-pan）：把 "FIG. 1" 划掉改写成 "FIG. 2"，镜头横移到图纸的下一块区域；
  - 剖切扫过（section-sweep）：一条剖切线 A–A 扫过零件，扫过的地方露出剖面排线；
  - 爆炸与归位（explode）。
- **镜头**：横移加推拉（pan），分段内连续；段与段之间可以在强拍上硬切一次。
- **文字动画**：手写（handwrite）：导线先出，字母左到右逐笔写出，每字约 50 ms。

## 声音语法

- **配乐**：Steve Reich 式的极简主义（《Music for 18 Musicians》那一路），D 大调，90 BPM（30 fps 下一拍 20 帧），3 拍一小节（`meters` 设成每小节 3 拍，2 s 一小节；样片为了卡画面排成 3 + 2 + 1 + 3 拍）。签名是两台 `marimba` 交错的十六分音符：同一个带休止的音型（`ostinato` 的 `cell` 里写 `.`），一台比另一台晚几格，合起来是连续的十六分音符；错开的格数一变，合成出来的旋律就变，这就是相位移动，每进一个新段落多错开一点。低音是干净的正弦（`sub808`，`drop` 0、`drive` 很小），按四分音符打拍；`vibraphone` 关掉电机，每段第一拍敲一个和弦报段落。没有鼓，机械但全是原声；空间是小而干的 `room`，两台马林巴左右拉开。
- **音效**：签名是针管笔划纸声（2–6 kHz 的带通噪声，长度等于这一笔的时长；库里没有，需要在项目里合成或用授权录音）；直尺和圆规用低通过的短 `whoosh`；零件归位 `click`；定稿盖章 `impact`。
- **声画关系**：每层线条开画落在拍上；爆炸视图的零件每个八分音符飞出一个；定稿前一小节马林巴全停，只留颤音琴、弱低音和笔声。
- **样片拟音**：`events.json` 21 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs <slug>` 生成，落点全部引用动作所用的同一张时间表，声像取发声物体的屏幕 x（`(2x/W − 1)·0.7`），按 `profile=swatch` 混在配乐下：纸展开 `whoosh`、铺满 `click`；基准线落笔 `tick`、准星 `click`；标题每个词起笔一声很轻的 `tick`；三张图各一声 `tick`，尺寸出现 `click`；剖切线扫到底 `swish_rev`；修订云 `toggle`；440→520 计数 4 声 `tick`；横移 `whoosh`，修订三角 `click`。针管笔划纸声库里没有，样片没做。
- **样片的转场音效**：`paper` 为主：图纸展开是一声向下的纸张滑动（0.3 s）；剖切线扫过是按扫描时长塑形的亮 `swish_rev`，结尾摇向图框是跟着摇镜走向右边的长 `whoosh`（0.8 s）。

## 适合与不适合

- **适合**：01 物理机制、工程原理；03 硬件产品构造、"它是怎么做出来的"；06 系统架构图；02 横屏科普。
- **不适合**：以人物情感为主的故事；数据图表（用 `editorial-data`）；动物、人脸这类有机形体。
- **容易被误用成**：暗蓝底青色霓虹的科幻 HUD，或者满屏没有意义的网格、数字和圆环装饰。

## 禁止项

1. 发光 HUD、扫描线、青色霓虹。这是纸，不是屏幕。
2. 3D 渲染的实体。只用正交视图和斜轴测线图，深度靠斜投影系数做。
3. 尺寸和数字是装饰：不量任何东西、比例对不上、单位不统一。
4. 所有线一个粗细，没有线型层级。
5. 线条整体淡入，而不是按制图顺序画出来。
6. 满屏网格。图纸只有外框和标题栏，网格至多 5% 可见。

## Prompt 块

```text
Visual style: engineering blueprint on cyanotype paper. The whole film is one sheet: uneven Prussian-blue paper (#173A6E to #2A5C9E low-frequency mottling, coating streaks, fold creases, sun-bleached edges) on a dark table #0E1218, with a border, a title block bottom-right and a notes column. White technical line work #E8F1FA is drawn in drafting order, each layer starting on a beat: centre lines (dash-dot), outlines (3 px), details (2 px), hidden lines (dashed), section hatching at 45°, dimension and leader lines in pale blue-white #A9C6E8 (1.2 px) with numbered balloons. Strokes draw on with a small bright nib, easeInOutSine per stroke, ~900 px/s. Dimensions are alive: when a part moves or stretches, its dimension line follows and the number updates in whole millimetres. Exploded views fly parts out along their axes one per eighth note and snap back with no overshoot. Lettering is condensed engineering caps (DIN Condensed) written stroke by stroke between faint guide lines; Chinese in a long Fangsong. Camera pans across the sheet like an eye reading a drawing; transitions are "FIG. 1" crossed out and rewritten as "FIG. 2" with a pan, a cutting-plane line sweeping to reveal a section, and explode/assemble. One accent only, reviewer yellow #F4C542, at most once per shot. No glow, no HUD, no scanlines, no 3D rendering. Sound: 90 BPM Steve Reich-style minimalism, two marimbas interlocking in 16ths and phasing apart section by section over a clean sine bass, a vibraphone chord on each new section, no drums; pen scratch on every stroke, a click on every assembled part.
```

## 引擎做法

- **首选 HyperFrames**，SVG 或 Canvas2D。画线用弧长截断：SVG 用 `getTotalLength` 在 setup 里算好，逐帧改 `stroke-dashoffset`；Canvas 用 `lib.strokePartial`，笔头亮点画在截断处。
- **斜投影代替 3D**：`x' = x + d·z·cos45°`、`y' = y − d·z·sin45°`，d 从 0 动到 0.5，一张正立面图就"转"出了厚度。
- **纸**：setup 里生成一次，放在图纸坐标里（跟着镜头走，不跟屏幕走）；折痕是两条带亮暗边的线。
- **活的尺寸**：尺寸线两端取零件在当前帧的端点，数字 `Math.round(长度 / 比例尺)`。
- **长仿宋**：`ctx.scale(0.72, 1)` 后逐字绘制，字距按压缩后的字宽算。
- 样片 `swatch.js`：逐段做法见开头"样片里"。实现要点：开场图纸展开是在屏幕空间里对整张纸做裁切，再画一根带阴影的纸卷；结尾镜头的中心被夹在 `[W/2z, SW − W/2z]` 之内，标题栏在图纸角上时也不会露出桌面。

## 自查重点

- 取一层的 strip：制图顺序对不对（中心线在轮廓之前，尺寸在最后）。
- 缩到 360 px 宽的手机联系表：线宽层级还分得出吗？
- 量一处：尺寸数字和图形比例一致吗？
- 审图黄每个镜头最多一处。
- 标题栏和注释里要读的字：英文 ≥ 28 px、中文 ≥ 46 px，停到读完（读时规则，TASTE_CHECKLIST #5）。

## 相关资源

- `references/repos/lemo-opuscar/styles/blueprint/STYLE.md`（LemoLab，CC BY 4.0）：同名风格的完整样片。制图顺序、线宽随缩放的指数、斜投影系数动画、零件按八分音符飞出这几条来自它；本文改写了色值和字体（换成本机可用的 DIN 与仿宋）、改用审图黄代替红印章，并补了国标长仿宋和"活的尺寸"规则。
- `video-types/01-math-science-explainer.md`、`video-types/03-product-promo.md`、`video-types/06-paper-explainer.md`。
- `playbook/03-motion-design.md` §1（缓动表）、`playbook/08-vfx-and-motion-sources.md`。
- 外部：Art of the Title 的《Iron Man》片尾页（<https://www.artofthetitle.com/title/iron-man/>），只看语法。
