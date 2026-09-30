# 孔版印刷 · risograph

一句话：两三种半透明专色一版一版叠印在暖白纸上：颜色靠叠印相乘得到，版永远套不准，油墨有颗粒和针孔；每一帧都像刚从印刷机里出来的一张纸。适合温暖、独立、手作感的故事和 MV。它的叙事招式是"加一块版 = 加一层意思"。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 0 帧滚筒已经压在纸上，蓝版随滚筒整幅扫过去（前沿一道浓蓝的滚筒带，后面是半调天空、底部地面带和四角套准十字），同拍 Rhodes 弹下第一个和弦；标题印在蓝版上；三个形状依次是一版（大纲，只有蓝）、两版（分镜：黄版滚上来，蓝网点压在黄上变绿）、三版（初版：粉版滚上来，三圆全叠印，中间镂空一个纸白的四角星，不用 ▶），粉版同时给标题"双击"一次，每加一版就踢一下；2.9–4.0 s 每拍重印一版：3.0 s 粉版、3.5 s 黄版各踢一下，落到新的套准位置，对应的形状同时压印一下（放大 12% 再回位）；右上角的太阳（黄 + 粉 45%）缩小并挪到标题右侧，不再压着初版三圆；4.0 s 整块矩形粉版从上方滑下盖住整张纸，落地时错位踢开 14 px；4.5 s 切到结束印张：蓝版一次整行印出"RISOGRAPH"，4.75 s 粉版偏 4–5 px 再印一次。实际字体：Futura Bold、PingFang SC Semibold。配乐是 120 BPM、A 大调的 lo-fi hip-hop，每加一版进一件乐器：只有蓝版时是 Rhodes（`epiano`，轻颤音）的 Amaj9 和弦，按 3–7–9–5 的无根音排法，第二下里 9 音落到根音，底下只有黑胶噼啪；2.0 s 黄版进来时低音提琴（`upright`）用三连音 F♯–A–C♯ 走上来，正好对上三个形状 2.0 / 2.17 / 2.33 s 的印出；2.5 s 粉版进来时鼓进来：发灰的 `bb_kick`、晚 22 ms 的 `rim` 边击、十六分摇摆的 `hihat`（`swing` 0.62，懒）；4.0 s 整块粉版盖下时加 `vibraphone`，E–C♯–A 往下走。整轨过 `lofi`（低通 5.5 kHz、wow、噼啪、嘶声）和 `tape` 饱和。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| Risograph 数码速印机与它的专色油墨 | 理想科学工业（Riso Kagaku）1946 年由羽山昇（Noboru Hayama）创立；Risograph 各机型的年份未核实 | 一次只印一种颜色；油墨半透明，叠印等于相乘；每一版单独对位，偏差是常态；实地有针孔，走纸方向有条纹 |
| 《報道ステーション》（Hodo Station）片头动画 | 2021 · Hiromu Oka | 把每一帧真的分色、逐张用 Riso 印出来再扫描：三色、A3 纸上千张；颗粒和套版随帧"沸腾"，这是数字滤镜模仿不出的一点 |
| 《Sunday Ride》（lemo-opuscar 的样片） | 2026 · LemoLab（CC BY 4.0） | 用 RGB 三个通道存三块版的密度，着色器负责网点、错位和颗粒；"版即叙事"：开场一版，每个转折加一版 |

核实：Riso Kagaku 的创立年份和创始人来自 Wikipedia；Hiromu Oka 的作品、年份和工艺（三色、上千张 A3、逐帧扫描）来自 It's Nice That 的制作专访。

**不照搬**：不出现 RISO 的商标和机器外观，油墨名只当颜色参考；不照搬 Oka 片头的画面，也不照搬 lemo 样片的骑车人、鸽子和"粉色圆盘吞掉公园"这一具体镜头（"叠印盖满"这个语法可以用，但样片改成了矩形整版滑入）。

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
  - 整版滑入（plate-slide）：整块矩形色版从画外滑进来盖住画面，下面的一切变成叠印色，落地时这块版错位踢一下；不用"一个圆长大铺满"，那在风格库里撞车了；
  - 抽纸（sheet-pull）：整张画面像纸一样被抽走，下一张落下，只用在开头和结尾。
- **镜头**：慢速横移（pan）或固定。
- **文字动画**：版印（cutout 式）：字随着滚筒一次整行印出，不逐字；需要强调时第二块版再印一次。

## 声音语法

- **配乐**：lo-fi hip-hop，A 大调，120 BPM（24 fps 下一拍 12 帧，30 fps 下 15 帧），暖、原声感。签名是 Rhodes（`epiano`）的 maj7 / maj9 和弦，无根音排法（3–7–9–5），一小节只弹两三下；鼓懒、摇摆、发灰：`bb_kick`、比拍子晚一点点的 `rim`（负的 `onset_ms`，懒）、十六分摇摆的 `hihat`；低音是软的 `upright`；整轨带 `lofi` 的黑胶噼啪和磁带抖动、`tape` 饱和。**分层 = 分版**：一版时只有 Rhodes；加一版进低音提琴；再加一版进鼓；全叠印时加 `vibraphone`。
- **音效**：签名是印刷机：走纸"唰"（高通的短 `whoosh`）+ 滚筒"咔嗒"（`click` 叠低通 `impact`），每加一版响一次；纸落下用 `swish_rev`。
- **声画关系**：每加一版 = 一件新乐器进来 = 一声滚筒。各版漂开时音乐抽掉一小节（保留混响尾巴），回位落在强拍上。
- **样片拟音**：`events.json` 15 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs <slug>` 生成，落点全部引用动作所用的同一张时间表，声像取发声物体的屏幕 x（`(2x/W − 1)·0.7`），−3 dB 混在配乐下：蓝版咬纸 `click`、滚筒扫过 `whoosh`；标题和中文的局部滚筒各一声轻 `whoosh`；三个形状印出各一声 `pop`（按一拍二换算到出现的帧）；黄版、粉版滚筒各一声 `whoosh`；3.0、3.5 s 每拍重印一版各一声 `click`；整块粉版落下 `swish_rev` + 落地 `click`；结束印张蓝版、粉版双击各一声 `click`。

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
Visual style: risograph print in motion. Warm paper #F4EFE4 and three translucent spot inks only: blue #0078BF, fluorescent pink #FF48B0, yellow #FFE800. Inks multiply where they overlap (blue+pink = deep indigo, blue+yellow = green, pink+yellow = orange-red); highlights are bare paper. Flat colour fields and silhouettes, no outlines, no gradients, no shadows; mid-tones are halftone dots (6–8 px, blue 15°, yellow 0°, pink 75°) fixed to the paper, never to the objects. Each plate is slightly misregistered (±1–3 px per shot), kicks 8–14 px on accents and springs back; ink has grain, pinholes and feed-direction streaks, and 35% of the dots re-roll 12 times a second like a fresh print. At most two plates in any area, only one of them as a tint. The story is told in plates: the opening is blue only, and each turning point adds a plate with a roller sweep (a denser ink band at the leading edge). Big shapes, one horizon, one big circle, one small figure. Titles are printed on the blue plate in a heavy geometric sans (Futura Bold), sometimes double-hit on pink with an 8 px offset; Chinese in PingFang SC. Figures step at 12 fps, camera pans stay smooth. Transitions: roller sweep, an ink shape growing over everything and becoming the next scene, the sheet pulled away. Sound: warm 120 BPM lo-fi hip-hop: Rhodes maj7/maj9 chords, lazy swung dusty drums, a soft upright bass, vinyl crackle and tape wobble; one instrument per plate, a print-drum clunk whenever a plate arrives.
```

## 引擎做法

- **首选 HyperFrames + `lib.shader`**。整片画进一张"版画布"：R = 蓝版密度，G = 粉版密度，B = 黄版密度（0 = 无墨，255 = 实地）。`source-over` 画出的是镂空（knockout），`globalCompositeOperation = "lighter"` 只往指定通道加墨，就是叠印。
- **着色器**：每块版按自己的偏移和微旋转采样密度 → 旋转网格上的余弦网点，`smoothstep` 阈值 ±0.07 抗锯齿，密度 ≥ 0.9 印成实地 → 阈值加每点噪声（颗粒）、实地针孔、走纸条纹 → `纸 × Π mix(1, 油墨色, 覆盖率)`。哈希用混合充分的整数哈希，`fract(sin())` 在 1080p 下会出竖条纹。
- **颗粒重印**：噪声种子取 `floor(t · 12)`，每个网点以 `hash(点, 种子) < 0.35` 决定这一"印"要不要重掷，全由 t 决定。
- **编码**：交付前看 100% 和 50% 有没有摩尔纹。网点和颗粒重印都很吃码率：样片以 1080p 渲染、720p 交付，网点周期用 11 px（交付尺寸上约 7 px），颗粒重印限定在 12 fps，而且只让密度 > 0.45 的网点重印（30%），浅网（天空）保持不动，在 1.5 MB 上限内 CRF 约 22。
- 样片 `swatch.js`：逐段做法见开头"样片里"。实现要点：滚筒带就是着色器里闸门前沿的一道密度加成（`u_mark`），不需要单独画；结束印张每块版一次整行出现，只靠版与版之间的偏移和"踢"来动。

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
