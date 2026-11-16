# 深空语义科普 · deep-space-explainer

一句话：深空黑底上讲宇宙和前沿科学，每一种东西从头到尾只用一个颜色：光是金色，物质是珊瑚红，观测者（地球的大气、城市的灯、探测器）是蓝色；主镜头是着色器做的黑洞和地球。适合天文、物理、科学新闻和长讲解：颜色攒下含义以后，后面的画面不用解释也读得懂。

**怎么借**：可以借走的是三样。语义色是一份契约：开头说一次（样片用左上角的色标），之后哪怕换了镜头、换了尺度，同一种东西还是那个颜色，别的东西不借用它；强调用暖白，不用金色，金色只留给光。一两个"哇"镜头用着色器做真的物理形状（黑洞的阴影和被弯过来的吸积盘、地球的晨昏线和大气），其余画面克制。镜头是一条连续的路：跟着一束光从一处走到另一处，不硬切。下面的色值、速度、镜头参数是样片的数，供试做。不能放的是：物理形状要对（黑洞的阴影、盘在阴影上下各出现一次、月相和晨昏线的方向），颜色的含义一旦定了不能中途改；字照字号下限来、停够读完。

样片：`media/swatch.mp4`（9 s，完整视频在 Release `styles-media`，`tools/fetch_media.sh deep-space-explainer` 取回）· 竖版 `media/swatch-portrait.mp4` · 封面 `media/poster.jpg`（t = 6.2 s）· 2 秒预览 `media/preview.mp4`（2.0–4.0 s）

样片里：一片三层深度的星空和一道淡淡的银河带，一排金色的光并排从左边出发，镜头跟着往里漂；一个黑洞从右边进来，它的吸积盘是珊瑚红的，盘的背面被引力弯到阴影的上方和下方；左上角依次出现色标"光、物质、观测"；金色的光经过黑洞时被弯开，靠得最近的一束掉进去，其余的往右汇聚；镜头跟着弯得最多的那一束穿过黑暗，到了夜里的地球，光落在地球的边缘，一圈蓝色的环亮起来；标题在地球上方，字幕在地球的夜面上，下面垫一条淡暗带。最后镜头离开地球，拉回星空，回到第一帧。实际字体：标题 Songti SC Black，英文 Avenir Next，字幕和色标 PingFang SC Semibold。

## 样片

| 拍 | 时间 | 这一拍做什么 | 本风格的做法 |
|---|---|---|---|
| 立住世界 | 0–1.5 s | 色板和质感一眼看清 | 三层星空和银河带，0.1 s 一排金色的光从左边出发（光速在画面上是每秒 1850 px），镜头跟着漂进来，黑洞从右边入画 |
| 招牌动作 | 1.5–4.5 s | 语义色和着色器主镜头 | 色标一条一条出现；黑洞的着色器（光线在引力里一步步弯，盘的背面绕到阴影上下）；金色的光弯开、一束落进去；镜头跟着一束光甩到地球，带横向拖影 |
| 真实字号的字 | 4.5–7.5 s | 标题和字幕，停够读完 | 4.58 s 光落在地球上，蓝环亮起；标题 96 px 暖白宋体黑、英文 44 px、字幕 48 px，一个字一个字浮上来；地球在慢慢转 |
| 收住 | 7.5–9.0 s | 落定，接回第一帧 | 字和色标淡出，光散掉，镜头拉远离开地球回到星空；星空每走 12 000 px 重复一次，镜头正好走了这么远，最后一帧就是第一帧 |

这一支是 9 秒，80 BPM，四拍落在 1.5、4.5、7.5 s 的小节线上。渲染成本是"分钟级"：黑洞每帧在 640×640 上每个像素最多走 96 步。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 伦敦地铁图 | 1933 · Harry Beck | 每条线一个颜色，所有地方都一样；颜色就是名字，读图的人不用看图例第二遍 |
| 《星际穿越》的黑洞"卡冈图雅" | 2014 · Double Negative（DNGR 渲染器）与 Kip Thorne；论文 James, von Tunzelmann, Franklin & Thorne,《Classical and Quantum Gravity》32, 065001（2015） | 按真实的光线弯曲去渲染：吸积盘的背面出现在阴影的上方和下方，靠近阴影有一圈细的亮环；物理对了，画面自己就好看 |
| 《宇宙》（*Cosmos: A Personal Voyage*） | 1980 · Carl Sagan、Ann Druyan、Steven Soter；PBS | 镜头像一艘"想象之舟"连续地飞过不同尺度，从一处直接航行到下一处，而不是换幻灯片 |

核实：地铁图的出版年份、《星际穿越》黑洞论文的作者、期刊和卷号、《宇宙》的年份和主创，对照了 Wikipedia 和 arXiv:1502.03808（2026-11-16）。

**不照搬**：不用《星际穿越》的镜头和飞船，不用《宇宙》的想象之舟，不仿地铁图的版式。样片的光束、黑洞参数和地球是自己算的。

## 视觉语法

- **语义色**（底 `#04070C`）：

  | 颜色 | 只给 |
  |---|---|
  | 金 `#FFC24B` | 光：每一束光、每一个光子，在每一个镜头里 |
  | 珊瑚红 `#FF5F6D` | 物质：光落上去或发出光的东西（样片里是吸积盘；最热的内圈混向 `#FFE6CF`） |
  | 蓝 `#3FA2FF` | 观测者：地球的大气、夜面的城市灯光、探测到光的那一圈 |
  | 暖白 `#F4E9D0` | 标题和一般的强调（不拿金色当强调，金色只表示光） |

  一个片子里最多四五种语义色；新的东西出场时，要么用已有的颜色（它就是那一类），要么第一次出场时说清楚它的颜色。
- **色标**：开头说一次，放在角落：一短线加两个字，颜色和它代表的东西一样。
- **深空**：三层星星（视差 0.35、0.6、1.0）和一道模糊的银河带；星星很小、很淡，不抢语义色。全片轻颗粒、暗角。
- **字**：标题用宋体黑、暖白；英文用 Avenir Next；字幕和色标用苹方 Semibold。压在亮画面上的字幕下面垫一条淡暗带。

## 运动语法

- **镜头**：一条连续的路，在几个关键位置之间用 smootherstep 缓动；快的时候带半帧快门的拖影（`styles/_swatch/vendor/hand.js` 的 `smear`）。跟着一个东西走（样片是一束光），从一处到下一处。
- **光**：画面上的光速固定（样片每秒 1850 px），所有光一起出发，像一道波前。光线弯曲按真实方程积分（同一个方程，2D 里画金线，3D 里给着色器用）。
- **着色器镜头**：慢慢地变（倾角在 0.06–0.16 rad 之间缓慢摆动、盘按开普勒速度转），不做快速的"炫技"。
- **字**：一个字一个字浮上来（上升 10 px、淡入），整行用掉窗口的六成。

## 声音语法

- **配乐**：太空里的管风琴。80 BPM，D 小调，管风琴长和弦（拉杆 806400000，慢速 leslie），中段加一层高八度的管风琴音型，sub808 的低音心跳，读字时钟琴三个音；大厅混响 3.2 s。
- **音效**：光出发时一声长的气流，越走越亮；黑洞是一层很低的嗡（两条差 0.7 Hz 的正弦慢慢拍打）；一束光掉进去是一声反向的 swish；镜头甩过去一声 whoosh；光落到地球上是一声干净的双音 ping（`styles/_swatch/custom_sfx.py` 合成，`styles/deep-space-explainer/sfx/`）；色标每出一条轻轻一下。
- **声画关系**：稀，跟着光走。

## 适合与不适合

- 适合：原理讲解（01）里的天文和物理、知识短视频（02）的科学新闻、长讲解（10）里需要"同一种东西在不同尺度上反复出现"的片子（光、粒子、信号）。横竖都成立。
- 不适合：没有几种需要分清的东西的内容（语义色就成了装饰）；暖调、人文的题材；需要大量文字和表格的段落。

## 常见误用及原因

- **颜色中途改含义**：前面金色是光，后面金色又成了"重点"，观众攒下的颜色语言就作废了。强调用暖白。
- **什么都发光**：每样东西都加光晕，光就不特别了。光晕只给光和最热的物质。
- **着色器镜头太多**：每个镜头都上 3D，重点反而被稀释；一两个就够，其余用干净的 2D。
- **黑洞画成一个黑圆加一圈环**：没有被弯到阴影上下的盘，就不是黑洞，是甜甜圈。【底线】物理形状要对。
- **镜头硬切换场景**：深空讲解靠的是"连续航行"的感觉，硬切会让尺度关系断掉。

## Prompt 块

```text
Deep space (#04070C) where every kind of thing keeps one colour for the whole film, stated once by a small corner key:
light is gold (#FFC24B) — every ray in every shot; matter is coral (#FF5F6D); the observers are blue (#3FA2FF) — the
Earth's air, its night-side lights, the ring that answers when light is detected; titles and plain emphasis are warm
white (#F4E9D0), never gold. One or two hero shots are real shaders with the right physics: a black hole whose disk is
lensed over and under its shadow, the Earth at night with its terminator and its rim of air. The camera makes one
continuous journey — drift in after a front of light, hold on the hole while the rays bend round it and one falls in,
follow a bent ray across the dark to the Earth — with a half-frame smear when it moves fast. Faint stars on three depths,
a soft galaxy band, light grain. Sound: pipe organ chords in a large hall, a low sub heartbeat, a few glockenspiel
notes; the light front is a long brightening breath, the hole a slow-beating low hum, the detection a clean ping.
Sample values (try, then depart): light at 1850 px/s, 96-step ray march at 640², camera 24 rs from the hole.
```

## 引擎做法

- 黑洞：`lib.shader` 上的片元着色器，每个像素一条光线，按 `x'' = −1.5 h² x / r⁵`（史瓦西黑洞的光线方程，以视界半径为单位）一步步走，步长随距离缩放；穿过盘面时按半径和角度取颜色（内圈热、外圈红，迎面来的一侧更亮），落进视界就是黑。输出带透明度，星空在下面的 2D 图层里。
- 地球：另一个着色器，3D 值噪声做陆地、冰和云，从左上照亮；夜面的城市灯光和边缘的大气都是观测者的蓝。
- 光线：setup 里用同一个方程在平面上积分出每一束光的路径，按弧长和时间画到光头；碰到地球就停。
- 镜头和循环：镜头是几个关键位置之间的缓动；星空每层按"总路程 × 视差"重复，镜头最后正好走完 12 000 px，所以最后一帧和第一帧一样。
- 拖影：整幅场景先画进离屏图层，再按镜头这一帧的位移叠几份。

## 自查重点

- 每一种颜色在每一帧里都只表示它那一类东西；暖白没有被金色替代。
- 黑洞的阴影、阴影上下的盘、迎面一侧更亮，三样都在；地球的晨昏线方向和光源一致。
- 镜头快的那几帧是拖影，不是跳帧；字在 1280×720 下读得清，字幕下的暗带没有压住画面的重点。
- 最后一帧是纯星空，和第一帧一样（`bin/vh style check` 量接缝）。

## 相关资源

- `video-types/01-math-science-explainer.md`、`video-types/02-knowledge-short.md`、`video-types/10-long-explainer.md`；`playbook/08-vfx-and-motion-sources.md`（着色器）。
- 同家族的 `monumental-scifi`（巨大的形体和雾，几乎不讲解）；讲数学对象用 `dark-math`。
