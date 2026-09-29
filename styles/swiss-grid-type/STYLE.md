# 瑞士网格动态字 · swiss-grid-type

一句话：让国际主义字体设计动起来。画面上有可见的模块网格，只用一个无衬线字体家族和红、黑、白三色，每个元素沿网格线进场、在拍点上停死。适合把结构讲清楚：规则、流程、数据、时间线，以及宣言式的品牌片。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：网格本身就是 hook：第 2 帧起 12 栏的色带和 2 px 边线在 6 帧内刷满全屏。700 px 的数字"3"分四步爬进第 10–12 栏，落在 0.4 s 的拍上。标题逐词从基线升起。母题在 1–3 / 4–6 / 7–9 栏：大纲是三根黑条；分镜是纯排字，没有图形——"01 02 03"三个数字沿网格的字号阶梯递增（60 / 108 / 156 px），齐左、共用模块基线，逐个从基线的 clip 里升起；初版是唯一的红块（2.4 s 落位）。标签只写 Outline / Storyboard / Draft 和中文，不再带编号。之后每拍一个事件：2.8 s 短条跳到顶行；3.03 s 大"3"上跳一个模块；3.2 s 红块离开网格，直线、不吸附，一边走一边长大，读数变成红色的"off grid"，这一小节鼓全部撤掉；3.6 s 分镜的三个数字按离红块由近到远依次升一级字号（72 / 120 / 168 px），整行重排进红块让出的位置。4.0 s 墨色按栏从右往左填满，结束卡在黑底上升起。样片用 150 BPM（1 拍 = 12 帧，1/16 = 3 帧），因为 5 s 样片的段落点 0.8 / 2.0 / 4.0 s 都落在这个速度的拍上；正片仍可用下文的 112.5 BPM。实际字体：Helvetica Neue Bold / Medium、PingFang SC。拟音：干、近、不加混响——每个词和分镜数字落位用 click，大数字爬升和分镜数字升级用 tick，红块落位用 pop，4.0 s 墨色擦除用 shutter（裁纸刀）。拟音的落点写在 swatch.js 的 `FOLEY` 常量里，`events.json` 由它生成。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 贝多芬音乐会海报（为 Tonhalle-Gesellschaft Zürich 设计） | 1955 · Josef Müller-Brockmann | 几何形按音乐的节奏排列，字是独立、克制的一块：图形负责情绪，字负责信息 |
| *musica viva* 音乐会海报 | 1959 年的一张为例，这个系列延续了多年 · Josef Müller-Brockmann | 同一套网格和字体跨越几十张海报保持不变，每张只换构成：系统比单张重要 |
| *Der Film* 展览海报 | 1960 · Josef Müller-Brockmann | 字就是构图：两个词在黑底上按极端的大小对比摆放，尺寸和位置本身产生纵深 |
| 《平面设计中的网格系统》*Grid Systems in Graphic Design* | 1981 · Josef Müller-Brockmann | 栏、槽、基线的换算方法：先定网格，再放内容 |

核实：年份与出处来自 Wikipedia、The Graphic Design School 与 Museum für Gestaltung Zürich。*musica viva* 系列各张的具体年份，以及系列的起止时间，**未核实**。

**不照搬**：不复刻贝多芬海报的同心弧、*Der Film* 的版式，或任何一张海报的构成；海报上不写真实机构名（Tonhalle、musica viva）；不用 Akzidenz-Grotesk 的仿制品冒充历史海报。

## 视觉语法

- **色板**：

  | token | hex | 语义 |
  |---|---|---|
  | bg 纸白 | `#F2F0EB` | 纸面 |
  | fg 墨黑 | `#111111` | 字、条、线 |
  | accent 信号红 | `#E1251B` | 唯一的主角：一个画面里只允许一个红色元素 |
  | extra 网格线 | `#CFCCC4` | 可见的网格 |
  | extra 浅灰块 | `#E2E0DA` | 次要色块 |
  | extra 海报白 | `#FAFAF7` | 画面中的"海报"纸面 |

  反相段落可以用黑底 `#111111` 加白字和红，全片最多反相一次。
- **字体**：只用 Helvetica Neue 一个家族，两个字重：Bold 做标题，Roman / Medium 做正文和注释。
  - 标题用小写或只有句首大写；字号 ≥ 90 px 时字距 −0.02em；
  - 超大数字 600–800 px，当章节号用，贴着栏的左边放，做光学对齐（减去字形左侧的 bearing）；
  - 中文用 PingFang SC 的 Semibold / Regular，一个汉字的宽度等于网格单元的整数倍。
- **网格**：1920×1080，12 栏，左右边距 96 px，槽宽 24 px（栏宽 122 px），基线 24 px。所有元素的左边、上边和基线都落在网格线上。把画面当成一个跨页：左 5 栏放"规则 / 数字"，右 6 栏放"作品"。
- **构图**：
  - 齐左，右边参差；大面积留白是构图的一部分；
  - 尺寸对比 ≥ 10:1，例如 700 px 的数字配 44 px 的注释；
  - 允许元素出血、出画；
  - 全片最多出现一次主斜线（15° 或 30°），留给"打破网格"的那一刻。
- **质感**：none。无颗粒、无阴影、无渐变。

## 运动语法

帧数一律按 30 fps 计。

- **缓动**：只有两条曲线。snap 用 `cubic-bezier(0.76,0,0.24,1)`（easeInOutQuart）；画线、进度条和那个"唯一的例外"用线性。不用 overshoot、弹簧，也不用淡入淡出。
- **时长 = 音符时值**：速度取 112.5 BPM，1 拍 = 16 帧，1/8 = 8 帧，1/16 = 4 帧。选这个速度，就是为了让所有时值在 30 fps 下都是整数帧。snap 提前一个时值起动，**落在拍点上**。
- **进场**：
  - 词从基线下方的 clip 矩形里升起（1/16，4 帧），离场时向上（1/8，8 帧）；
  - 线沿自身长度生长；
  - 色块用擦除（wipe）出现；
  - 大数字分 4 步"一格一格"爬到位，每步 1/16。
- **删除**：一条 2 px 的线在 4 帧内划过元素，元素随后在 8 帧内向中线压扁消失。
- **连锁**：一个元素到位后，周围的元素按距离由近到远重新排版，每个 1/16 动两个。
- **节奏**：每 2 拍（约 1.07 s）一个新事件；需要读完的一行字停 ≥ 2.5 s。
- **转场**（全片只用这 3 种）：
  - 向左擦除（wipe-left）：一块纸白或墨黑沿网格栏推过去；
  - 网格滑移：整个网格带着内容横移一个跨页；
  - 卡拍硬切。
- **镜头**：固定（locked）。"镜头"只是一个 2D 矩阵，只在拍点上动，只用 easeInOutQuart。
- **文字动画**：stagger。按词从 clip 里升起，词与词间隔 1/16（4 帧），整行不超过 0.5 s。

## 声音语法

- **配乐**：motorik / krautrock 式的稳定律动，112.5 BPM，A 多利亚调式。`bin/vh music` 只有 minor 和 major 两种调式，用 minor 加一个大写的 `IV` 和弦就能近似多利亚。每加一条规则就多一件乐器：`hats` → `kick` + `clap` → `bass` → `arp` → `lead`。"打破规则"的那一小节撤掉鼓。注意第一段不要只放 `hats`：拍与拍之间会出现数字静音，`bin/vh qa scan` 判失败，样片在第一段加了 `bass`。
- **音效**：干、近、不加混响。
  - `click`（活字落版）配每个词到位；
  - `tick` 配网格线生长；
  - `shutter`（裁纸刀）配删除线；
  - `pop`（低沉的一声 thump）配大数字的每一步。
- **声画关系**：画面和音乐共用一张节拍表。每个 snap 的到位帧就是 `music.beats.json` 里的拍点帧，误差 0 帧。

## 适合与不适合

- **适合**：05 数据故事；03 发布片里的"规格 / 原则"段；06 论文讲解的结构和方法段；宣言、规则、流程、时间线，以及机构品牌。
- **不适合**：情绪化、需要温度和人物的叙事；手作、复古、童趣品牌。
- **容易被误用成**：只是"白底黑字加一点红"，没有真正的网格，元素位置都是手填的；或者把 12 栏当成数据图表的格子，元素切得太碎，没有分量。

## 禁止项

1. 任何元素不在网格线上（手填坐标）。
2. 用了第二个无衬线家族；用斜体；正文居中对齐。
3. 淡入淡出、弹跳、弹簧、阴影、渐变、颗粒。
4. 同一画面里有两个以上的红色元素。
5. snap 的到位帧不在拍点上。
6. 复刻历史海报的具体构成，或写上真实机构名。

## Prompt 块

```text
Visual style: the International Typographic Style in motion. A visible modular grid (12 columns, 96 px margins, 24 px gutters, 24 px baseline) on off-white paper #F2F0EB, with ink #111111 and one signal red #E1251B that only one element per frame may wear. One grotesk family in two weights (Helvetica Neue Bold and Roman), flush left, ragged right, extreme scale contrast (a 700 px chapter numeral beside 44 px notes), large deliberate white space, elements allowed to bleed off the edge. Motion is exact and musical: only two curves (easeInOutQuart for snaps, linear for lines being drawn); durations are note values at 112.5 BPM (a sixteenth is 4 frames at 30 fps) and every snap lands on a beat. Words rise out of a clip box from the baseline, lines grow along their length, numerals climb in four steps, and deletions are a knife line followed by a collapse. No fades, no bounce, no shadows, no gradients, no grain. Transitions: a grid-aligned wipe to the left, a sideways slide of the whole grid, hard cuts on the downbeat. Sound: a 112.5 BPM motorik groove in A dorian that adds one instrument per rule, with dry letterpress clicks on every landing.
```

## 引擎做法

- 首选 HyperFrames：版面用 DOM + CSS grid，时间线用 GSAP seek；数据段再加 SVG。
- **网格工具**：`col(n)`、`span(a, b)`、`base(k)` 三个函数返回像素值，禁止手写坐标。自查时把网格线层打开，单独渲染一张。
- **节拍**：`beat(k) = k * 16` 帧；snap 写成 `snapTo(el, target, arriveFrame = beat(k), dur = 4)`，起点 = 到位帧 − dur。
- **clip 上升**：每个词外面包一层 `overflow: hidden` 的容器，词本身从 `translateY(100%)` 移到 0。
- **光学对齐**：大数字用 `measureText` 的 `actualBoundingBoxLeft` 修正左边。
- **字重**：Chrome 里 Helvetica Neue 的 700 = Bold、500 = Medium、400 = Roman；先 `document.fonts.load` 预载，再渲染。

## 自查重点

- 叠一张网格图：所有元素的左边和基线都落在线上（误差 0 px）。
- 对照节拍表：每个 snap 的到位帧 = 拍点帧（逐帧 strip 配合 `beats.json` 检查）。
- 1 fps 联系表：每帧红色元素不超过 1 个；留白是有意的，主视觉仍然抓住画面 40% 以上的注意力。
- 大数字与注释的比例 ≥ 10:1，而需要读的注释仍然 ≥ 44 px。
- 没有任何淡入淡出：逐帧检查，opacity 只取 0 或 1。

## 相关资源

- `references/repos/lemo-opuscar/styles/swiss-motion/STYLE.md`（LemoLab，CC BY 4.0）：同一语法的完整样片。"时值即时长""删除是一刀""规则加一个例外"来自它；本文改写了网格、BPM 和字体选择（本机渲染直接用系统里的 Helvetica Neue；lemo 要分发字体文件，所以选了 OFL 字体）。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 里的 Swiss Pulse。
- `video-types/05-data-story.md`、`video-types/03-product-promo.md`、`playbook/03-motion-design.md` §4 排版。
