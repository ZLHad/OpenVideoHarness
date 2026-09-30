# 弹性扁平 2D · bouncy-flat-2d

一句话：亮底、四种平涂色、几何形状当角色，靠挤压拉伸、预备动作和夸张的时间感演戏。它是社区常见"暗底 + 霓虹 + 玻璃"的反面口味。适合轻松的知识短片、App 功能小剧场、品牌吉祥物、儿童向内容。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：0.03 s 一座大薄荷色山丘从地面弹起（hook），芥末色太阳跟着弹入；番茄红主角在 0.1 s 从画外落下，拉长 3 帧，落在 0.5 s 的拍子上压扁，配一声拍手；标题字母一个个落下，落地压扁再回弹，中文逐字带过冲弹出；地面线在 0.78H，三个道具和主角都是 1.4 倍大：大纲（三行字）、分镜（三格）、初版（一幅小画：山和太阳，不用 ▶）；主角每拍跳一次，预备下蹲、沿抛物线跳上道具，落地时自己压扁、道具也一沉；4.0 s 主角压扁后朝镜头跳起，带一帧 smear，用自己的身体铺满画面，变成结束画面的底色。实际字体：Futura Bold、PingFang SC Semibold。配乐 120 BPM、F 大调：尤克里里扫弦加口哨主旋律，钟琴给每个落地点"叮"一下，逐段见"声音语法"里的"样片配乐"。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《Gerald McBoing-Boing》 | 1950 · UPA，导演 Robert Cannon，制片 John Hubley；获 1950 年度奥斯卡最佳动画短片 | 有限动画：背景只做暗示（一条线就是墙，一块色就是房间）；角色只动该动的部分；平涂色块可以不贴合线稿；声音本身就是笑点 |
| 《Disney Animation: The Illusion of Life》 | 1981 · Frank Thomas、Ollie Johnston | 12 条动画原则；本风格重点用挤压拉伸、预备、跟随与重叠、时间、夸张 |
| Headspace 品牌短片 | 年份未核实 · Buck | 几何形状就是角色：圆、胶囊、半圆靠姿态和时机传达情绪；克制，每个形状周围都有留白 |
| 《Dumb Ways to Die》 | 2012 · McCann Melbourne 为墨尔本地铁制作，动画 Julian Frost | 极简豆形角色、纯色底、一镜一个动作一个笑点，动作卡在歌的节拍上 |

核实：UPA 片目、导演和奥斯卡来自 Wikipedia 与 Cartoon Research；《The Illusion of Life》出版年来自 Wikipedia；Buck 的 Headspace 项目来自 buck.co，页面没有写年份；《Dumb Ways to Die》的代理商和动画作者来自 Wikipedia 与 The Drum。

**不照搬**：不用 Gerald 这个男孩、Headspace 的橙色圆脸、Dumb Ways 的豆子角色和"死法"笑点；不照抄任何一部作品的配色原值。

## 视觉语法

- **色板**：底色 + 四个平涂色 + 墨。同屏最多四色加墨，不用渐变。

  | token | hex | 语义 |
  |---|---|---|
  | bg 奶油 | `#FFF4E0` | 默认底色；换场时可以整屏换成下面任一色（UPA 式的纯色场景） |
  | fg 墨 | `#2B2A3A` | 眼睛、嘴、地面线、文字，只做小面积 |
  | accent 番茄红 | `#FF5A3C` | 主角 |
  | 芥末黄 | `#FFC53D` | 环境、道具、太阳 |
  | 薄荷绿 | `#2EC4A6` | 环境、第二道具 |
  | 天蓝 | `#4C8DFF` | 配角 |

  阴影用同色相明度降 12% 的平涂块，不做投影和渐变。
- **字体**：展示用 Futura Bold（几何、圆润，和形状语言一致），正文 Avenir Next Demi Bold；中文用 PingFang SC Semibold，拟声词可以换 Hannotate SC Bold。字距 −0.01em，不用斜体。
- **构图**：地面线在 y = 0.72H，一条墨线或一块色带就是整个地面；主角高度占画面 30–45%，放在三分线上；背景最多两层（纯色底 + 一两个大色块），不做透视。留白 ≥ 40%。
- **角色**：几何体 + 墨色小五官（两个竖椭圆眼睛、一条弧线嘴），不描边。手脚可以没有；要有就用等粗的胶囊。可选的"UPA 偏移"：色块相对线稿错开 6–10 px。
- **质感**：默认无。要纸感就叠 0.03 的纸纹，不加颗粒。

## 运动语法

帧数按 30 fps 计。这是允许 overshoot 的俏皮语域，但重量必须分得开。

- **缓动**：入场 easeOutBack `cubic-bezier(0.34,1.56,0.64,1)`；退场 easeInBack `cubic-bezier(0.36,0,0.66,-0.56)`（先往回缩一下再走）。弹簧三档：主角 stiffness 260 / damping 20（ζ≈0.62）；道具 ζ≈0.8；大物件 ζ = 1，不回弹。
- **挤压拉伸**：落地一帧内压到 `sy = 0.7`，`sx = 1 / sy`（面积守恒），再按主角弹簧回到 1；腾空时沿速度方向拉长 `sy = 1 + 0.004 × 速度（px/帧）`，上限 1.35。变形的锚点在接触点（脚底），不在中心。
- **预备**：每个大动作前 4–6 帧反向压缩到 `sy = 0.85`，停 2 帧，再出手。跳跃走抛物线（弧线），不走直线。
- **两套时间**：位移和挤压用连续的 t（丝滑是现代的一面）；表情、眨眼、口型、手型按 12 fps 换张（`lib.step(t, 12)`，有限动画的一面）。
- **时长**：入场 10–14 帧；每个状态至少停 1.0 s；每 1.5–2.5 s 一个新动作或笑点；笑点前 0.4 s 停顿。
- **转场**（只用这 2 种）：
  - 身体吞没（body-wipe）：主角压扁后朝镜头跳起，中间插一帧 smear，身体放大到铺满画面，变成下一场的底色（"一个圆长大铺满"在风格库里撞车太多，不用）；
  - 跟着动作切（cut-on-action）：主角跳出画面顶端，下一场它从顶端落进来。
- **镜头**：固定机位，平面舞台。最多做横向跟拍，不推拉。
- **文字动画**：逐字弹入（stagger），每字错开 45 ms，从上方 80 px 落下，落地压扁再回弹；中文每字 70 ms。

## 声音语法

- **配乐**：欢快的讲解片配乐。F 大调，120 BPM（30 fps 下一拍 15 帧，24 fps 下 12 帧），写成 `parts`：`ukulele` 扫弦当底（`strum`，`D.xUDUxU`，二、四拍是闷音切音），`whistle`（`kind: lips`，口哨）吹主旋律，`glockenspiel` 专门给落地、弹出这类动作点"叮"一下，`pizzicato` 弹根音—五音的跳跃贝斯，轻 `kick`（一、三拍）加 `clap`（二、四拍）；`space: room`，送混响不超过 0.15。不要 EDM 式的 drop，也不要 hats 铺满。
- **音效**：签名是"每个落地一声"：`pop` 降调叠一段 200→120 Hz 的正弦滑音（库里没有 boing，需要在项目里合成或用有授权的素材）；出现用 `pop`，快速移动用短 `whoosh`，结论用 `ding`。
- **声画关系**：Mickey-mousing，主角每一步、每次落地都对一个音或一个音效，误差 ±1 帧。音符表的拍位可以写小数（`[5.44, 0.3, "D6"]`），不在网格上的落地点也能对准。笑点前音乐留白约 0.4 s：鼓和扫弦在谱子里空出来，只留一件旋律乐器往上走。
- **样片配乐**（`score.json`，3 小节 4/4：`stage` / `hops` / `wipe`）：0.0 s 起尤克里里扫弦、轻底鼓和拨弦贝斯，口哨吹 C–A–F，F 落在 0.5 s 主角落地那一拍，和拍手、`impact` 同时；标题四个词落地时口哨让开，钟琴按 F–A–C–F 往上叮四下（0.98 / 1.25 / 1.52 / 1.655 s，和字母落地的 `pop` 在同一刻）。2.0 s 起和弦换成 IV–V：三个道具弹出时钟琴叮 D–F–B♭；每次起跳口哨吹出一个音，随着跳跃往上滑（`bend`），落地那一帧正好滑到 D / E / G，钟琴同时叮同一个音。3.75 s 起鼓和扫弦让开（4.0 s 只轻扫一下）；4.0 s 主角扑向镜头，口哨从 C6 一口气滑到 A6，4.34 s 撞满画面时底鼓、拍手、重扫弦、贝斯一齐落下，4.5 s 名字出来，钟琴 F 大三和弦和 `ding` 同时响。
- **样片拟音**：`events.json` 19 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs <slug>` 生成，落点全部引用动作所用的同一张时间表，声像取发声物体的屏幕 x（`(2x/W − 1)·0.7`），−3 dB 混在配乐下：小山、太阳、三个道具弹出各一声 `pop`；主角落地 `impact`；标题每个词第一个字母落地一声轻 `pop`；每次跳跃空中一声很轻的 `whoosh`（峰值在跳跃正中），落地压扁一声 `pop`；扑向镜头 `whoosh` + 撞满画面 `impact`；名字出来一声 `ding`。boing 滑音库里没有，样片没做。

## 适合与不适合

- **适合**：02 知识短片（轻松话题、儿童向）；03 App 或产品功能小剧场（一个按钮变成角色）；07 角色小短片；04 轻快歌曲。
- **不适合**：严肃新闻、灾难、医疗决策、悼念；数据密集的讲解；奢侈品和高端品牌。
- **容易被误用成**：企业扁平插画（Corporate Memphis：大手大脚的紫色小人），或者幼儿园 PPT。

## 禁止项

1. Corporate Memphis：比例怪异、没有表情的人群，大片紫色。
2. 暗底、霓虹描边、紫青渐变、玻璃拟态（本预设存在的意义就是换口味）。
3. 所有东西都用同一个弹簧参数，轻的重的一样弹，没有重量差。
4. 原地匀速"呼吸"缩放当 idle。idle 只能是踩拍的小动作：眨眼、换脚、看一眼别处。
5. 渐变、投影、描边，或者同屏超过四色加墨。
6. 挤压不守恒：压扁时不变宽，看起来像被 CSS scaleY 拍扁。

## Prompt 块

```text
Visual style: playful flat 2D character animation on a light ground. Cream background #FFF4E0, four flat colours only (tomato #FF5A3C for the hero, mustard #FFC53D, mint #2EC4A6, sky #4C8DFF) plus ink #2B2A3A for tiny eyes, mouths and one ground line at 72% height. No outlines, gradients, drop shadows, glass or neon. Characters are simple geometric shapes that act: every big move has 4–6 frames of anticipation (squash to 85%), jumps follow arcs, landings squash to 70% height with width 1/0.7 so the area stays constant, anchored at the feet, then spring back (hero spring stiffness 260 / damping 20; heavy props settle with no bounce). Position and squash run smoothly at 30 fps; faces, blinks and hand poses change on 12 fps steps like limited animation. Locked camera, flat staging, generous empty space. Transitions: a circle grows out of the hero to become the next scene's solid background, or the hero jumps out the top and lands in the next scene. Title letters drop in one by one (45 ms stagger) and squash on landing, set in a geometric sans (Futura Bold); Chinese in PingFang SC Semibold. Sound: 120 BPM major-key pluck-and-clap groove, a sound on every landing, a 0.4 s pause before each gag.
```

## 引擎做法

- 首选 HyperFrames（SVG 或 Canvas2D，GSAP 时间线按 t seek）；需要逐笔手感时用 ClaudeAnimationBase。
- **挤压的纯函数**：落地时刻 `t0` 已知，`sy(t) = 1 − 0.3 · e^(−ζω·τ) · cos(ω_d·τ)`（τ = t − t0），`sx = 1 / sy`；也可以直接用 `lib.spring(τ, {stiffness: 260, damping: 20})` 做回弹。跳跃高度用抛物线 `y = y0 − 4h·u·(1−u)`，u 是这一跳的进度。
- **眨眼**：眨眼时刻由 `hash(seed, k)` 在每 1.6–3.2 s 的窗口里挑出来，眼睛高度按 12 fps 换张：开 → 半 → 闭 → 开。
- **身体吞没**：主角的中心从它所在的位置插值到画面中心，缩放 `S = 1 + 13·u^2.1`，前 60% 的时间里在身后画 2–3 个低透明度、落后几帧的自己当 smear；身体颜色就是下一场的底色，放大到盖满画面时直接切到结束画面。
- 样片 `swatch.js`：逐段做法见开头"样片里"。实现要点：道具和主角统一乘 1.4 倍画，挤压锚点在脚底；结尾的"身体吞没"见上一条。

## 自查重点

- 落地前后 6 帧 strip：`sx · sy` 在 1 ± 5% 以内，锚点在脚底，落地前有预备帧。
- 轻的和重的东西，回弹是否明显不同？
- 同屏颜色数 ≤ 4 加墨；缩到 20% 做剪影测试，主角还认得出。
- 手机上（360 px 宽）眼睛直径 ≥ 画面高的 1.5%，表情读得出。
- 两种转场之外没有别的转场，没有 crossfade。

## 相关资源

- `references/repos/lemo-opuscar/styles/rubber-hose/STYLE.md`（LemoLab，CC BY 4.0）：踩拍的 idle、"预备—停—出手"、一拍二配平滑镜头；本文取其语法，改成亮底彩色平面、去掉胶片损伤。`game-show`（豆形吉祥物、卡拍网格）也可对照。
- `references/repos/OpenMontage/styles/flat-motion-graphics.yaml`（AGPL-3.0，只读）：它的默认值是暗底 `#0F172A`、紫 `#7C3AED`、霓虹描边、处处弹性，正是本预设要反着来的口味。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 第 7 节 Folk Frequency（亮底、back.out 入场）。
- `engines/ClaudeAnimationBase/ANIMATION_GUIDE.md` 的 Animation principles；`playbook/03-motion-design.md` §3；`video-types/07-hand-drawn.md`、`video-types/02-knowledge-short.md`。
