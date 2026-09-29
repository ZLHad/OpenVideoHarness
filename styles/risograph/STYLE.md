# 孔版印刷 · risograph

一句话：两三种半透明专色一版一版叠印在暖白纸上：颜色靠叠印相乘得到，版永远套不准，油墨有颗粒和针孔；每一帧都像刚从印刷机里出来的一张纸。适合温暖、独立、手作感的故事和 MV。它的叙事招式是"加一块版 = 加一层意思"。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| Risograph 数码速印机与它的专色油墨 | 理想科学工业（Riso Kagaku）1946 年由羽山昇（Noboru Hayama）创立；Risograph 各机型的年份未核实 | 一次只印一种颜色；油墨半透明，叠印等于相乘；每一版单独对位，偏差是常态；实地有针孔，走纸方向有条纹 |
| 《報道ステーション》（Hodo Station）片头动画 | 2021 · Hiromu Oka | 把每一帧真的分色、逐张用 Riso 印出来再扫描：三色、A3 纸上千张；颗粒和套版随帧"沸腾"，这是数字滤镜模仿不出的一点 |
| 《Sunday Ride》（lemo-opuscar 的样片） | 2026 · LemoLab（CC BY 4.0） | 用 RGB 三个通道存三块版的密度，着色器负责网点、错位和颗粒；"版即叙事"：开场一版，每个转折加一版 |

核实：Riso Kagaku 的创立年份和创始人来自 Wikipedia；Hiromu Oka 的作品、年份和工艺（三色、上千张 A3、逐帧扫描）来自 It's Nice That 的制作专访。

**不照搬**：不出现 RISO 的商标和机器外观，油墨名只当颜色参考；不照搬 Oka 片头的画面，也不照搬 lemo 样片的骑车人、鸽子和"粉色圆盘吞掉公园"这一具体镜头（"叠印吞没"这个转场语法可以用）。

## 视觉语法

- **色板**：纸 + 三种专色。下面的 hex 是社区常用色卡的屏显近似值（未核实，不是官方色）。

  | token | hex | 语义 |
  |---|---|---|
  | bg 纸 | `#F4EFE4` | 暖白纸；高光全部是纸（knockout），不画白 |
  | fg 蓝 | `#0078BF` | 第一块版：轮廓、文字、"开场的世界"。每个元素都要含一点蓝，单版时画面才完整 |
  | accent 荧光粉 | `#FF48B0` | 情感、主角、转折时加上的版 |
  | 黄 | `#FFE800` | 光、温度、最后加上的版 |
  | 备选专色 | 联邦蓝 `#3D5588`、亮红 `#F15060`、青绿 `#00838A` | 换一套专色时用，全片只用一套 |

  叠印的理想相乘值：蓝 + 粉 ≈ `#002284`（深靛），蓝 + 黄 ≈ `#006D00`（绿），粉 + 黄 ≈ `#FF4100`（橙红）。真实油墨密度约 80–90%，屏幕上会比这些值浅一些。
- **字体**：Futura Bold 做标题（粗、几何、像海报），Avenir Next Demi Bold 做说明；中文用 PingFang SC Semibold。所有字都"印"在一块版上（默认蓝版），跟着那块版一起错位、起颗粒；标题可以在第二块版上再印一次，偏 6–10 px，就是 riso 的"双击"。
- **构图**：大色块、少线条、不描边。一条地平线、一个大圆（太阳、盘子、钟面）、一个小主体；主体的头放在画面里最平的色块前面。同一块区域最多两块版，其中最多一块是网点，否则发泥发褐。天空和阴影用网点，按 20% / 38% / 62% / 100% 几档分层。
- **网点与颗粒**：网点周期 6–8 px（1080p），网角 蓝 15°、黄 0°、粉 75°；网点固定在纸上，镜头平移时画面在网点下面滑过。颗粒：每个网点的阈值带 ±0.08 的噪声；实地里噪声 > 0.93 的地方露出纸（针孔）；沿走纸方向拉长 10 倍的噪声做条纹，墨量在 0.80–1.0 之间起伏。
- **套版**：每个镜头一组固定偏移（每版 ±1–3 px，外加 ±0.0005 rad 旋转）。

## 运动语法

帧数按 24 或 30 fps 计。

- **两套帧率**：角色和道具按 12 fps 换张；镜头平移每帧更新。颗粒按 12 fps "重印"一次，每次只有 35% 的网点重新掷骰子，不整屏闪。
- **缓动**：入场 easeOutQuint `cubic-bezier(0.22,1,0.36,1)`；退场 easeInQuint；镜头慢移用 easeInOutSine。
- **版踢一下**：加版、标题落下、大动作时，这块版踢开 8–14 px，用弹簧 stiffness 900 / damping 33（ζ≈0.55）在约 0.25 s 内回位。音乐停的那一小节可以让各版慢慢漂开，最多约 25 px，在强拍上一起弹回。
- **时长**：加一块版（滚筒擦过画面）15–24 帧；每个状态至少停 2 s；每 2.5–4 s 一个新事件。
- **转场**（只用这 3 种）：
  - 滚筒擦除（roller-sweep）：新的一块版从左往右被"滚"上去，前沿有一条更浓的墨带；
  - 叠印吞没（overprint-grow）：一个大色块长大盖满画面，下面的一切变成叠印色，再收缩成下一场的主形状；
  - 抽纸（sheet-pull）：整张画面像纸一样被抽走，下一张落下，只用在开头和结尾。
- **镜头**：慢速横移（pan）或固定。
- **文字动画**：版印（cutout 式）：字随着滚筒一次整行印出，不逐字；需要强调时第二块版再印一次。

## 声音语法

- **配乐**：A 大调，120 BPM（24 fps 下一拍 12 帧，30 fps 下 15 帧），暖、原声感。**分层 = 分版**：一版时只有 `pad` 或拨弦 `arp`；加一版进 `bass`；再加一版进 `hats` 和轻 `clap`；全叠印时加 `bell`。
- **音效**：签名是印刷机：走纸"唰"（高通的短 `whoosh`）+ 滚筒"咔嗒"（`click` 叠低通 `impact`），每加一版响一次；纸落下用 `swish_rev`。
- **声画关系**：每加一版 = 一件新乐器进来 = 一声滚筒。各版漂开时音乐抽掉一小节（保留混响尾巴），回位落在强拍上。

## 适合与不适合

- **适合**：04 独立、lo-fi、城市民谣类 MV；07 手作感短片；02 温暖的科普；08 zine 风的海报快剪；03 独立品牌和文创。
- **不适合**：高精度的科技产品界面；需要精确读数的图表（网点伤读数）；需要真实肤色的人物。
- **容易被误用成**：一层"复古滤镜"：普通插画加噪点加 RGB 色差。

## 禁止项

1. 同一区域三块网点版叠在一起（发泥发褐）。
2. 每帧随机抖动套版：画面闪，码率爆炸。
3. 渐变、投影、描边；形体只靠色块和剪影。
4. 超过三种油墨，或者出现叠印得不到的颜色。
5. 网点跟着物体走。网点印在纸上，是固定的。
6. 中间帧用 JPEG 或 4:2:0，网点被糊掉。

## Prompt 块

```text
Visual style: risograph print in motion. Warm paper #F4EFE4 and three translucent spot inks only: blue #0078BF, fluorescent pink #FF48B0, yellow #FFE800. Inks multiply where they overlap (blue+pink = deep indigo, blue+yellow = green, pink+yellow = orange-red); highlights are bare paper. Flat colour fields and silhouettes, no outlines, no gradients, no shadows; mid-tones are halftone dots (6–8 px, blue 15°, yellow 0°, pink 75°) fixed to the paper, never to the objects. Each plate is slightly misregistered (±1–3 px per shot), kicks 8–14 px on accents and springs back; ink has grain, pinholes and feed-direction streaks, and 35% of the dots re-roll 12 times a second like a fresh print. At most two plates in any area, only one of them as a tint. The story is told in plates: the opening is blue only, and each turning point adds a plate with a roller sweep (a denser ink band at the leading edge). Big shapes, one horizon, one big circle, one small figure. Titles are printed on the blue plate in a heavy geometric sans (Futura Bold), sometimes double-hit on pink with an 8 px offset; Chinese in PingFang SC. Figures step at 12 fps, camera pans stay smooth. Transitions: roller sweep, an ink shape growing over everything and becoming the next scene, the sheet pulled away. Sound: warm 120 BPM, one instrument per plate, a print-drum clunk whenever a plate arrives.
```

## 引擎做法

- **首选 HyperFrames + `lib.shader`**。整片画进一张"版画布"：R = 蓝版密度，G = 粉版密度，B = 黄版密度（0 = 无墨，255 = 实地）。`source-over` 画出的是镂空（knockout），`globalCompositeOperation = "lighter"` 只往指定通道加墨，就是叠印。
- **着色器**：每块版按自己的偏移和微旋转采样密度 → 旋转网格上的余弦网点，`smoothstep` 阈值 ±0.07 抗锯齿，密度 ≥ 0.9 印成实地 → 阈值加每点噪声（颗粒）、实地针孔、走纸条纹 → `纸 × Π mix(1, 油墨色, 覆盖率)`。哈希用混合充分的整数哈希，`fract(sin())` 在 1080p 下会出竖条纹。
- **颗粒重印**：噪声种子取 `floor(t · 12)`，每个网点以 `hash(点, 种子) < 0.35` 决定这一"印"要不要重掷，全由 t 决定。
- **编码**：交付前看 100% 和 50% 有没有摩尔纹。网点和颗粒重印都很吃码率：样片以 1080p 渲染、720p 交付，网点周期用 11 px（交付尺寸上约 7 px），颗粒重印限定在 12 fps、35%，在 1.5 MB 上限内 CRF 约 20。
- 样片 `swatch.js`：蓝版先滚上纸，标题印在蓝版上、粉版双击；三个形状依次是一版（大纲，只有蓝）、两版（分镜，蓝 + 黄 = 绿）、三版（初版，全叠印），每加一版踢一下；最后一个粉色圆长大吞掉整张纸。

## 自查重点

- 只开第一块版：画面是否完整可读（剪影测试）？
- 每块区域 ≤ 2 版、≤ 1 块网点？
- 静止镜头连续 6 帧：套版偏移不变，只有踢的时候才变。
- 成片 100% 与 50% 各看一次摩尔纹；编码后网点颜色是否还干净。
- 文字只在一块版上，中文 ≥ 46 px，错位后仍然可读。

## 相关资源

- `references/repos/lemo-opuscar/styles/risograph/STYLE.md`（LemoLab，CC BY 4.0）：本预设的主要来源。三通道存版、着色器印刷、每块区域两版一网点、固定偏移加踢、35% 颗粒重印、"版即叙事"都来自它；本文改写了参数、配乐分层和转场的具体做法，去掉了它的角色和镜头。
- `references/repos/lemo-opuscar/styles/halftone-dossier/STYLE.md`：多网角叠印的另一种用法。
- `video-types/04-lyric-music-video.md`、`video-types/07-hand-drawn.md`。
- 外部：It's Nice That 对 Hiromu Oka 的专访（<https://www.itsnicethat.com/articles/hiromu-oka-hodo-station-process-animation-051222>）。
