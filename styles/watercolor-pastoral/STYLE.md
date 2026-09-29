# 水彩田园 · watercolor-pastoral

湿画法的大片天空，远山偏蓝变淡，风从左边吹来，草浪一波一波地传过去，云影慢慢掠过田野。安静、温暖、有空气。适合治愈系短片、季节和自然题材、旅行与回忆、慢歌 MV，以及需要"喘口气"的片尾。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

样片实况：0.0–0.3 s 一笔很宽的湿笔触带着天色从左往右扫过天空上部，0.1 s 时已扫过约七成、占画面两成；随后湿接湿的天空从上往下晕开，带着回流形成的水花和积色的湿边。远山、树林、草地由远及近依次渲染出来，颜料有沉淀颗粒，整张画面再乘一层纸纹。风以波的形式从左往右吹过草地：每 1.2 s 一波，波长 1100 px，草叶弯 8–13°。三棵树（铅笔稿 → 平涂 → 完成稿）的树冠各分成 4 团叶簇，每团在风波到达它的位置 0.4 s 后才摆动、倾斜、被压扁，阵风时迎风一侧的叶缘翻亮；花瓣和落叶顺着同一阵风从左往右飘过。4.0 s 暖光从太阳处涨到满屏纸白（4.4 s 最亮）再退去，露出结束画面。标签英文 40 px。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《龙猫》（となりのトトロ） | 1988 · 吉卜力工作室，美术监督男鹿和雄 | 夏日田园的光和空气：远景偏蓝、变淡、对比降低；云影掠过田野；植物按大色块分组，细节只给前景 |
| 《岁月的童话》（おもひでぽろぽろ） | 1991 · 吉卜力工作室，美术监督男鹿和雄 | 乡村全景的色彩分组：大片田地只用少数几种绿，靠冷暖区分远近 |
| 《小鹿斑比》（Bambi） | 1942 · 华特迪士尼制片厂；前期概念画黄齐耀（Tyrus Wong） | 以宋代山水为源的印象式背景：前景细致，背景只用几笔暗示，大片留空与雾，情绪靠光和气氛 |

**只学光、气氛和层次，不学角色**：不画龙猫、猫巴士、斑比或任何片中生物，不复刻标志性的场景和构图（大树、特定村落、神社鸟居），不描原画。

## 视觉语法

- **色板**：
  - 纸 `#F4EEDF`：底色，留白处就是光；
  - 暖光 `#F2C46D`：强调色，只属于阳光：光斑、逆光的草尖、窗里的灯；
  - 天 `#A9C7DF`，远山 `#9DB3BF`，中景树林 `#7FA36B`，近处草地 `#B9CF7E`，前景草丛和叶丛暗部 `#3F6B4A`（最近的一层最深、最饱和）；
  - 冷影 `#8E8FB5`：所有阴影，包括云影；阴影不用黑，也不用同色加深；
  - 花 `#E58A7B`：零星点缀，每个画面不超过 3%；
  - 线和字 `#3E3A34`：少量描线和手写注。
- **字体**：
  - 标题：`Palatino` → `Georgia`，常规字重，字距 +0.01em；
  - 中文：`Songti SC` Light 用于标题，`Kaiti SC` 用于手写注；
  - 字幕：`Songti SC` 44–50px，颜色 `#3E3A34`，下衬 12px 纸色光晕，不加底框。
  - 样片实际用字：`Palatino` Italic 96px（英文）、`Kaiti SC` 66px（中文）、标签 `Kaiti SC` 50px + `Palatino` Italic 40px，结束画面 `Kaiti SC` 76px + `Palatino` Italic 44px。
- **构图**：
  - 大天空：地平线在 0.6–0.66H，天空占画面 55–65%；
  - 四层纵深：远山、中景树林、近处草地、前景草丛（被画面下沿裁掉一部分）；
  - 空气透视：每往远一层，明度 +10%、饱和度 −15%、色相向蓝偏约 10°；
  - 一个光源（默认左上），光斑落在中景；主体（一座房子、一条小路、一个人）不超过 0.25H，放在三分线上。
- **质感**：
  - 水彩纸颗粒 + 颜料沉淀（granulation）；
  - 湿边：每块渲染的外缘比内部深约 8%；
  - 天空用两三道湿接湿的横向渲染叠出，允许颜色在交界处互相渗；
  - 不加胶片颗粒，不加暗角，不加镜头光晕。

## 运动语法

帧数按 30 fps 计；ClaudeAnimationBase 默认 24 fps，换算时乘 0.8。

- **缓动**：
  - 进场 easeOutQuint `cubic-bezier(0.22,1,0.36,1)`，出场 easeInQuint `cubic-bezier(0.64,0,0.78,0)`；位移和镜头用 easeInOutSine；
  - spring 无回弹：stiffness 90、damping 19（ζ≈1.0）；
  - 禁止 bounce 和 overshoot。
- **风**（签名动作）：
  - 草叶角度 `θ(x,t) = A·(0.6 + 0.4·g(t))·sin(2π(f·t − x/λ))`，每 1.2 s 一波（f ≈ 0.83 Hz），λ = 1100px，A = 8–12°，风从左往右；`g(t)` 是用 `hash` 做种子的平滑噪声，模拟阵风；
  - 树冠摆 1–2°，频率 0.2 Hz，比草晚 0.4 s（风后到）；
  - 云 8–15px/s 漂移，云影在地面上以同样速度移动。
- **时长**：进场 36 帧（1.2 s）；每个画面至少停 2.5 s；每 4 s 发生一件新事（一阵风、一片叶子飞过、光斑移过来）。
- **转场**：全片只用三种：水彩擦除（`brushWipe` 用天色和草色）、光晕过曝（`glow()` 从一点涨到满屏暖白 12 帧，再退 18 帧）、风带过去（一片叶子或花瓣横穿接缝，飞过画面中线时切，下一镜接着飞）。
- **镜头**：缓慢推进（dolly），每镜不超过 3%；或横移，多层视差：远 0.2、中 0.5、近 1.0、前景 1.6。
- **文字动画**：手写（handwrite）。只用在少量手写注上，每字 0.2–0.3 s；片子大多数时候不出字。

## 声音语法

- **配乐**：`bin/vh music`，`bpm: 84`，`key: "F"`，`mode: "major"`。编制：`pad` 做温暖的底，`arp` 用软拨弦、低 `energy`（0.3–0.5），`dizi` 吹一条简单的旋律，`bell` 每段只响一两下。不要鼓组；需要推进时只加 `bass`。
- **音效**：风（低通噪声，随 `g(t)` 起伏）、草叶沙沙、远处的风铃 `ding`（很轻）、溪水。风可以先用低通、拉长的 `whoosh` 占位；鸟鸣和溪水需要有授权的录音，内置库没有，记进 NOTES 的素材台账。
- **声画关系**：卡点很松，按乐句对齐，不按拍子。阵风的音量和画面里草浪的幅度用同一个 `g(t)`，声画自然同步。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：150 BPM 记谱、听感很慢，F 宫；`pad` 铺底，0.8 s 起竹笛长音，2.0 s 加软拨弦，4.0 s 光晕时一声编钟。拟音（`events.json`）：0.1 s 开场那一笔湿笔触一声 `whoosh`，每个风波经过画面中线时一声很轻的 `whoosh`（1.35 / 2.55 / 3.75 s），4.4 s 光晕最亮时一声 `swish_rev` 吸进去。

## 适合与不适合

- 适合：`07` 治愈系手绘短片、`04` A 路线的慢歌 MV、`02` 自然和季节科普、`03` 生活方式类产品的氛围段落、任何片子的片尾。
- 不适合：快剪、信息密度高的讲解、需要紧张感的叙事。硬套会变成"很美但什么都没发生"：记住 ANIMATION_GUIDE 的规则 3，每个镜头都要发生一件事。

## 禁止项

- 数码线性渐变的天空、镜头光晕、bloom：光一律用 `glow()`；
- 饱和的纯绿：所有绿都要偏黄或偏蓝、降饱和；
- 远近一样清楚：没有空气透视；
- 所有草同相位摆动：风没有方向；
- 纯黑或同色加深的阴影：阴影是冷紫蓝；
- 画成某部动画的同人：出现可识别的角色、生物、建筑。

## Prompt 块

```text
STYLE: pastoral watercolour. Warm cotton paper #F4EEDF shows through as light. Wet-in-wet sky washes (#A9C7DF) take 55–65% of the frame; horizon at 0.6–0.66H. Four depth layers: blue-grey far hills #9DB3BF, mid treeline #7FA36B, near meadow #B9CF7E, cropped foreground grass #3F6B4A. Each step back is lighter, less saturated and bluer.
One warm light #F2C46D from the upper left; every shadow, including drifting cloud shadows, is a cool violet #8E8FB5, never black. Granulating pigment, slightly darker wet edges, no gradients, no lens flares, no digital bloom.
Motion is calm and continuous: wind travels left to right as a wave through the grass (one wave every 1.2s, 1100px wavelength, 8–12°, gusts), trees answer 0.4s later, clouds drift 8–15px/s with their shadows. Sine easing, no bounce. Slow push-ins under 3% or a parallax pan.
Something still happens in every shot: a gust, a leaf crossing, a patch of light arriving. Transitions: a watercolour brush wipe, a warm light bloom to paper white, or a leaf carried by the wind across the cut.
Music: warm pad, soft plucked arpeggio, a simple flute line, a bell or two; F major, 84 BPM, no drums. Wind sound follows the same gust curve as the grass.
```

## 引擎做法

- **首选 ClaudeAnimationBase（p5.brush）**，`bin/vh new handdrawn <slug>` 建项目。
  - 天空：两三块横向的 `paint(pts, { fill, fillOp: 170–200, bleed: .2–.3, tex: .6, ink: null })` 上下交叠；
  - 山和树林：`fill` 渲染，远层 `fillOp` 低、`bleed` 高；前景草丛用 `inkLine(pts, sw, col, 'dry')` 或 `ribbon()`，150–300 根就够，不要上千根（每帧控制在 1.5 s 内）；
  - 光：`glow(x, y, r, '#F2C46D', .5–.7)`，画在被照亮的东西之前；黄叠蓝会变绿灰，所以光不要用 `wash`；
  - 每层先 `boilSeed('far')`、`boilSeed('mid')`……静止的山不能 boil；草叶位置用 `hash(i)`；
  - 转场用 `brushWipe(p, [天色, 草色])`、`glow()` 做光晕过曝。
- **现成样板**：`showcase/01-handdrawn-clawd-leaf/`（12 秒成片：秋天调色、叶子被风吹走的动作、iris 和 brush wipe 转场，附 20 条自评修复记录）。它是暖秋版本；做夏日田园时把色板换成本文的，风和叶子的写法直接参考。
- 不用 ClaudeAnimationBase 时，可以参考 lemo `watercolor` 的 Canvas2D 笔触引擎：可变宽度的带状笔触 + 3–9 条会断开的鬃毛轨迹，画完的植物缓存成 sprite，只做摇摆。

## 自查重点

- 每层抽样算平均明度和饱和度：越远越亮、越灰、越蓝，四层单调变化；
- strip 看 1 s：草浪的波峰是否从左往右移动；树是否比草晚到；
- 有没有纯黑、纯白、饱和纯绿的像素；
- 静止的远山和房子在相邻帧是否逐像素相同；
- 每个镜头能说出"发生了什么"吗？

## 相关资源

- `references/repos/lemo-opuscar/styles/watercolor/STYLE.md`（LemoLab，CC BY 4.0，https://creativecommons.org/licenses/by/4.0/）。本文借鉴了它的空气透视分层、湿边的多遍渲染和"画完即缓存成 sprite 只摇摆"的做法，风格方向从自然笔记改成田园氛围。
- `engines/ClaudeAnimationBase/ANIMATION_GUIDE.md`（`paint`、`glow`、`boilSeed`、`brushWipe` 的用法）、`showcase/01-handdrawn-clawd-leaf/`。
- `video-types/07-hand-drawn.md`、`video-types/04-lyric-music-video.md`、`playbook/03-motion-design.md`、`playbook/04-audio.md`。
- 相近预设：`styles/ink-wash/`（同一引擎的水墨用法）。
