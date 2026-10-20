# 等轴解剖 · iso-anatomy

一句话：把一个概念做成一台真实的小机器，画成等轴测的技术插图：几十个有厚度的零件，细墨线，按朝向分四阶的明暗，只点亮一个部件；它先按真实的方式动给你看，再沿装配方向拆开给你看。东西本身就是解释，画里没有箭头和悬空的标签。适合讲机制、流程、系统和方法、产品构造，也就是"一件东西是怎么工作的"。

**怎么借**：能借走的是"结构自己解释自己"的那几条：东西本身就是解释；零件多而真，放大了还有东西可看；能拆开，拆的顺序就是装配关系；同一时刻只点亮一个部件（或一条因果链）；读数来自驱动零件的同一个模型；线都落在实处；字放在图外的版面上。配色、纸色、强调色、字体、机位和节奏是样片的取值，换题材可以换（Anatomy 的工具包自带深色、浅色两套主题）。不能放的是事实：照着真实物件画时，尺寸、零件数、开合方式要查清，读数要真。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐和 `events.json` 拟音）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：一台"凸轮定时器"。一根轴上装着三个凸轮，每个凸轮的轮廓不一样；轴每步转 72°，凸轮的凸起依次顶起三根推杆，推杆把三张卡片从夹子里举起来：大纲（几行字）、分镜（六格小画）、初版（一格胶片，里面是一个小立方体）。凸轮的形状就是程序：同一个轴角永远给出同样的三个高度，"每一帧都是代码"在这里是一件看得见的事。第 0 帧这台机器是拆开的，0.10 s 起各个装配体从里往外依次归位（每个错开 35 ms，临界阻尼，不回弹），镜头同时从 58° 方位、40° 俯角落到 32°、30°，约 1.2 s 全部合拢，左下的阶段词从 CLOSING UP 变成 1 SHAFT · 3 CAMS；这段时间左边先画出三条发丝线。0.85 s 起标题从这几条线下面一个字一个字升起来，中文晚 0.2 s；1.72 s 图例的三行一起升起，都是灰的。2.0、2.4、2.8 s 轴各走一步，阶段词是 INDEXING：被顶起的那张卡片连同它的推杆、推杆脚和凸轮一起变成朱红，图例里对应的一行同时变红；右下读数是同一个函数算出的轴角和帧号，右侧表盘的指针跟着跳。3.08 s 轴停住（HOLDING），镜头从最后一步起慢慢推近 8%、转 5°，初版卡片上的小立方体按每秒 12 格一格一格地转。4.0 s 整台机器拆开：卡片先飞，接着是左边的电机齿轮箱、右边的表盘、推杆和导向杆、立柱、轴承盖、轴、轴承座，最后是脚，每个错开 35 ms，略欠阻尼；每个轴承座连同它上面的盖和立柱成一列往外移，归属关系还看得出；镜头拉远 16%、右移、转 6°，到 5.0 s 零件还在落定；读数变成 56 parts · 13 assemblies，阶段词 TAKEN APART。实际字体：Helvetica Neue、Menlo、PingFang SC。配乐 150 BPM、F 大调，闷音钢弦吉他、木琴和钟表擒纵器。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| [Anatomy](https://github.com/wheresryan22/anatomy)（agent skill；[介绍页](https://skills.wheresryan.sh/anatomy)） | 2026 · Ryan（wheresryan22），MIT | 主要学它。"东西本身就是解释"：把概念换成一台机器，机器的工作方式和概念一一对应，零件不少于 40 个；30° 俯角的近似等轴测，四阶明暗按面的朝向选、顶面最亮；同一时刻只有一个点亮的部件；每条线都落在面、线或端点上，不画引线、标号气泡和尺寸箭头；版面四角放图号、标题、操作提示和实时读数；拆开时每个装配体一个弹簧，外面的先走，错开 35 ms |
| [anatomy-reveal](https://github.com/annnguyentt/anatomy-reveal-skill)（agent skill；[介绍页](https://typingmind.com/skills/annnguyentt-anatomy-reveal)） | 2026 · Ann Nguyen（annnguyentt），MIT；工具包来自 Anatomy | 把同一套凸零件做成会转的 3D，拍成揭示片：一镜到底，翻滚入画、约 0.24 s 甩到细节、一个功能动起来、拆开、合拢定格；按真实毫米建模；运动模糊按画面每帧移动多少来定子帧数 |
| 文艺复兴工程师笔记里的爆炸图 | 15 世纪初 Taccola（1382–1453）的笔记本里已经有；Francesco di Giorgio（1439–1502）和达·芬奇（1452–1519）把它画成熟，达·芬奇的往复运动机械设计图是较早的清楚例子 | 拆开不是乱飞：零件沿装配方向离开，彼此的关系还读得出来 |
| *On Isometrical Perspective* | 1822 · William Farish，《剑桥哲学学会会刊》第 1 卷 | 等轴测把三条轴画成一样长，尺寸能在图上直接比；严格的等轴测俯角是 35.26°，Anatomy 用的 30° 俯角是近似的等轴测 |
| 《The Way Things Work》 | 1988 · David Macaulay 文图（技术文字 Neil Ardley），Houghton Mifflin | 一页一台机器，大图本身讲原理：拿一个具体、认得出的东西讲抽象的原理 |

核实（2026-10-21）：两个 skill 读的是仓库里的 LICENSE、SKILL.md 和 `references/`（Anatomy 核对到 `1482e84`，anatomy-reveal 到 `dd01e1c`）；Taccola、Francesco di Giorgio、达·芬奇的年份和说法来自 Wikipedia 的 Exploded-view drawing 条目；Farish 来自 Isometric projection 条目；Macaulay 来自 The Way Things Work 条目。Wikipedia 上"这个词出现于 1940 年代"那句被标了未通过核实，没有用。

**不照搬**：不用两个 skill 的示例物件（千分表、火箭发动机试车台、街机柜、意式咖啡机等），不复制它们的工具包代码（样片的渲染器是另写的），不画任何品牌产品的外形和 logo。"Fig 号加四角"的版面、四阶明暗、错开 35 ms 的拆分这些语法可以用。

## 视觉语法

下面是可借的语法和样片的取值。数字是样片的值，换场景按理由重新定。

- **东西本身就是解释**（这个风格的核心）：先找一台机器，它的工作方式和要讲的概念一一对应，用一句话说出"什么在动、这一动代表什么"。样片的那句是"轴转一步，凸轮的形状决定哪张卡片升起"。Anatomy 列过的对应：一个共享的 GPU 上下文服务很多画布，是一台龙门绘图仪的一个打印头跑 16 个孔；缓存键，是一把弹子锁，弹子全对上锁芯才转。两种失败：太抽象（叠在一起的板、浮在空中的方块、贴标签的盒子，认不出是什么）；太平太空（一块大板上画几条线，没有体积，没有零件可发现）。
- **零件多而真**：缩小看是一台清楚的机器，放大 4 倍每一处还有真东西：螺丝（一个点加一圈）、刻度尺、离边几毫米的凹槽、印着三条线的铭牌、轴上的定位环和它的紧定螺钉。每个零件都坐在另一个零件上，细节来自零件，不靠噪点。样片 56 个零件、11 个装配体。
- **机位**：正交投影，俯角 30°。样片的方位角从物件正面量起（0° 是正对正面）：45° 是经典的等轴测角，30–35° 多露出正面那条长边（样片 32°，开场从 58° 转过来）。Anatomy 的量法不一样（默认 45°，要露长边时用 35–60°），借数的时候先看清从哪边量。不用透视。
- **明暗**：四阶，按面朝哪个方向（和光的方位比）选一阶，顶面最亮；圆的零件用同一条色阶连续过渡，不出台阶。光从左前上方来，所以正面最亮、右侧面暗一阶。
- **层级靠线色**：底座和脚是浅灰线，结构是中灰线，主体是近黑线；只有一个点亮的部件，用强调色。样片点亮的是一整条因果链（凸轮、推杆脚、两段推杆、卡片夹和卡片），一眼看出是哪个凸轮顶起了哪张卡片；同一时刻只有一条链。
- **线**：发丝线，镜头推近也不变粗（样片轮廓 1.3 px、点亮 2.2 px、细节 1.0 px）。每条线都落在东西上：面、另一条线或一个端点；刻度、凹槽、铭牌上的线沿真实的边结束。不画引线、标号气泡、尺寸箭头，也不画透视出来的虚线隐藏线（零件是实心的，前面的挡住后面的）。
- **字在图外**：图里至多一个很小的刻字（样片没有）。说明放在版面上：左上图号，右上物件名，左下一个阶段词，右下实时读数；图例放在图旁边。阶段词和读数取自同一时刻、同一个来源：样片的 θ 来自驱动凸轮的那个函数，帧号来自 t，拆开时数的是真的零件数和装配体数。
- **色板**（样片的取值，可以整套换）：

  | 角色 | 颜色 | 含义 |
  |---|---|---|
  | 纸（版面） | `#F6F4EF`，版面外 `#EBE8E1` | 暖白的纸；版面四周一圈 1.2 px 中灰框 |
  | 零件色阶 | 顶面 `#FFFEFC`，四阶侧面 `#D2CFC8` `#DDDAD4` `#E8E6E0` `#F2F1EC` | 白色零件，靠朝向分出体积 |
  | 钢 | 顶 `#F3F4F6`，四阶 `#B4B8BF` … `#E6E8EB`，高光 `#FFFFFF` | 轴、推杆、电机外壳；圆面上有一条高光 |
  | 橡胶 | `#38383C` … `#6A6A70` | 脚 |
  | 线 | 主体 `#26262A`，结构 `#707075`，底座 `#9C9CA0`，凹槽 `#C4C4C7`，螺丝点 `#3A3A3E` | 层级 |
  | 点亮 | `#E4572E` | 正在看的那一个部件（或那条链）；它的面再混进 10% 的这个颜色 |
  | 光晕 | `#8A8A80`，32%，模糊 18 px | 底座下面一圈软影 |

  Anatomy 原版的浅色主题是冷白（卡片 `#FBFBFA`），点亮的部件变成纯黑线；深色主题卡片 `#131313`、线 `#D4D4D4`、点亮的变纯白。anatomy-reveal 用暖白纸 `#F1ECE2` 加极淡的纸纤维。样片取暖纸色，点亮改成一个朱红：视频里"只点亮一个"要隔着屏幕一眼看到，纯黑线在 1 s 里不够显眼。结构线和底座线也比原版深一截（原版是 `#8A8A8F`、`#B4B4B8`）：近白的零件、浅灰的线落在近白的纸上，第一眼太淡，开场尤其吃亏。
- **字**：英文 Helvetica Neue 500，标题 88 px，两行；中文 PingFang SC 400，64 px；四角和读数用 Menlo，44 px；图例 44–48 px。字号按 `desktop` 一档的下限定（这条是底线，`playbook/03-motion-design.md` §4）：要读的读数也是辅助字。原版网页上四角的字只有约 10 px，在视频里读不到。
- **质感**：不加颗粒和纸纹，矢量的干净本身是这个风格的一部分。想要纸感，anatomy-reveal 的 `look.css` 用 SVG `feTurbulence` 铺一层极淡的纤维和斑驳，可以借。

## 运动语法

- **东西按真实的方式动**：机构怎么动，画面就怎么动，不另加缓动。样片的轴每步转 72°（in-out sine，0.28 s）；推杆的升程直接从画出来的凸轮轮廓算：轮廓转到当前轴角以后，最高点的高度减去基圆半径（平底推杆总是搁在最高点上）。凸轮是半径 24 mm 的基圆和半径 64 mm 的一段凸起弧取凸包，弧的两端用 9 mm 的圆倒角；所以推杆离开基圆时起得快，到顶时自然减速，停在弧上，画面和运动不会对不上。
- **拆开和合拢**（签名转场）：每个装配体一个弹簧，0 是合拢、1 是拆开。拆开时外面的先走，每个错开 35 ms，略欠阻尼（ω 7.5、ζ 0.89，带一点分量，最后一个到 5.0 s 还在落定）；合拢倒过来，从里往外，临界阻尼（ω 10），不回弹：回弹就是零件穿进彼此。沿同一个方向离开时，前面的零件先走、走得更远；穿在一起的东西共用一个弹簧（样片的推杆、推杆脚、卡片夹和导向杆是一个装配体，一起往上走）。叠在一起的零件按归属一起走：样片每个轴承座连同上面的盖和立柱成一列外移，盖和立柱再各自往上抬，拆开以后还看得出谁装在谁上面。开场的散开比结尾大，多往两侧散，从 0.1 s 起整台机器和镜头一起动。
- **点亮就是选中**：选中一个装配体，它换成强调色；样片每走一步换一次，图例里对应的一行跟着变色。图例三行在第一步之前就以灰色升好，变色那一刻马上读得到；阶段词在三步之间保持 INDEXING，不跟着每一步闪。
- **运动模糊**：按这一帧画面移动了多少像素来定子帧数：位移乘快门（180°，即 0.5），每 1.6 px 一个子帧，最多 24 个；停住时只画 1 次。子帧太稀，快的零件会拖出几层分开的残影（第一版每 2.5 px 一个、最多 14 个时，评审在开场的齿轮箱和拆开的卡片上数到 4–6 层）。anatomy-reveal 用的是同一个思路：360° 快门，甩镜时最多 40 个子帧；它的文档说固定的 4:1 混合在甩镜时也会看到分开的残影。
- **镜头**：开场用和零件同类的临界阻尼弹簧落定；合拢以后方位角一直慢慢转（样片 1.2–4.0 s 转 5°），最后一步起推近 8%，停住时画面也在走；拆开时拉远、右移、转一点，让爆炸图整张读得清，也不压到左边的字。10 s 以上的产品揭示片可以借 anatomy-reveal 的节奏：翻滚入画（约 1.6 s 转 180°）、约 0.24 s 甩到一个细节、每处停 0.6–1 s 但一直在漂、一个功能真的动一次、拆开、合拢转向观众，只有片尾那一小段是静止的。
- **文字动画**：从槽里升起。每个字从一条发丝线下面升上来，临界阻尼（ω 18），字间错开 35 ms，和拆分的错开是同一个数；标题的三条线在 0.15 s 先画出来，左半边从开场就有东西在动；图例整行升起。字和零件用的是同一套动作。

## 声音语法

- **配乐**：一台台面上的小仪器。闷音的钢弦吉他（`guitar`，`mute`）弹八分音符当机芯，木琴（`xylophone`）在轴每走一步时敲一个音、沿和弦往上走，钟表擒纵器（`clock`）打 tick-tock，低音是吉他的根音，结尾用吉他泛音（`harm`）。样片 150 BPM、F 大调，I–IV–ii7–Vsus4–I，小节 4 + 1 + 3 + 2 + 3 拍（`meters`），段落落在 1.6 / 2.0 / 3.2 / 4.0 s。小而干的房间（`room`，rt60 0.35）。3.6–4.0 s 屏息：只剩钟和泛音（`stop`，keep）；拆开时木琴往下走一串，钟停了。闷音钢弦吉他和木琴在库里其他样片里都没用过；钟表擒纵器 `editorial-data` 也用过，那里是秒表的滴答。
- **音效**：`click`（装配体落位、推杆到顶、拆开的第一下）、`tick`（每一步、标题和图例开始升）、`air`（零件开始归位）、`whoosh`（拆开）。声像按物体的屏幕 x，音高按动作的大小。
- **声画关系**：机构里每个硬事件（一步、一次落位）都有声音，平滑的段落（推近、漂移）没有。Anatomy 出的是网页上的交互图，anatomy-reveal 的片子是无声的，这一层是本仓库加的。

## 适合与不适合

- **适合**：01 原理讲解里的机制；03 产品构造、"它是怎么工作的"、拆解和爆炸图；06 论文讲解，把系统或方法做成一台机器；02 横屏科普。
- **不适合**：以情绪和人物为主的故事；数据图表（用 `editorial-data`、`isotype`）；需要真实材质、光影的产品片（用 `product-keynote`、`tabletop-miniature`）。
- **容易被误用成**：贴着标签的等轴测方块图，像一页 PPT；或者 `blueprint` 那种线稿。和 `blueprint` 的区别：这里是有体积、互相遮挡的实心零件，`blueprint` 是蓝底白线的制图。和 `fui-hud` 的区别：没有发光，没有屏幕。

## 常见误用及原因

管事实、字形和可读的标【底线】，其余是参考。

1. 【底线】读数和数字只是装饰：零件数、尺寸、角度要从驱动画面的同一个模型里算；照着真实物件画时，尺寸、零件数和开合方式要查（硬规则 5）。不然这个风格最大的说服力（"它是一台真的机器"）就没了。
2. 方块、箭头加标签：观众看到的是流程图，不是机器。把关系做成机构：凸轮顶推杆，而不是一个箭头指过去。
3. 零件太少、大块平面：没有东西可发现，放大一看是空的，像占位图。
4. 线悬在空中：引线、虚线、尺寸箭头、在面中间断掉的刻度。读者会把它们当成零件去找。
5. 同时点亮好几个、用好几种强调色：观众不知道该看哪一个。点亮一条因果链可以，但同一时刻只有一条。
6. 拆开时零件互相穿过，合拢时回弹：一眼就假。按"外面的先走、合拢倒过来"排顺序，合拢用临界阻尼；穿在一起的东西共用一个弹簧。
7. 【底线】版面上的字按原版网页的大小抄过来：视频里读不到。标题、图例、四角的读数按观看档的下限（`desktop`：标题 ≥ 84 px，辅助字 ≥ 44 px）。

## Prompt 块

```text
Visual style: an explanatory isometric anatomy figure. The idea is built as one real, well-made physical object whose working is the concept (a mechanism people recognise: cams and followers, gears, a dial gauge, a chest of drawers, a lock), never boxes, arrows and labels. Dozens of small convex parts with real thickness, each sitting on another part: screws as dots with rings, ruler ticks, grooves inset a few millimetres from edges, label plates with three rule lines; at full view one clear machine, at 4x every region still has a real part to find. Orthographic camera looking down about 30 degrees, azimuth 30-45 degrees, no perspective. Four flat tones chosen by which way a face points relative to a light from the front-left, tops lightest; round parts shade continuously along the same ramp. Hairline ink outlines that do not thicken when the camera pushes in; hierarchy by line colour (base light grey, structure mid grey, subject near-black); exactly one lit part, or one cause-and-effect chain, in a single accent colour at any moment. Every line ends on a face, another line or a dot; no leader lines, balloons, dimension arrows or floating labels. Words sit outside the drawing on a framed plate: figure number top-left, the object's name top-right, a phase word bottom-left, a live readout bottom-right computed from the same model that moves the parts; text sized for the viewing tier. The mechanism moves the way the real one would. The signature transition is the exploded view: assemblies leave outside-in along their mounting directions, 35 ms apart, on slightly under-damped springs, and come home inside-out with no overshoot; sub-frame motion blur sized to how far the picture moves. Type rises out of hairline slots glyph by glyph on critically damped springs. Sample values, free to change: warm paper #F6F4EF, white to warm-grey part ramp, vermilion accent #E4572E, Helvetica Neue with Menlo and PingFang SC. Sound: a small instrument on a bench: muted steel-string guitar eighths as the mechanism, a dry xylophone note on each mechanical step climbing through the chord, a clock escapement as the pulse, clicks when parts seat; when it comes apart, a falling xylophone run and the clock stops.
```

## 引擎做法

- **样片**：Canvas2D 上一条自己写的小 3D 管线（`swatch.js`）。零件都是凸多面体：盒子、圆柱、沿一条轴挤出的凸多边形（凸轮、带圆角的底板），单位是毫米。每帧按三个量摆姿态：轴角（随轴转的零件）、推杆升程、各装配体的拆分量；正交投影。画家顺序：屏幕上包围盒相交的每一对零件，用物体坐标系里沿某条轴的分离平面判断谁在前，再做拓扑排序（遇到环时先画最远的）。这要求零件之间只贴合、不嵌入：轴在每个凸轮和定位环处断开，推杆在导向杆和它的套环处断成上下两段、长度每帧算。Anatomy 的"零件都是凸的，贴合不嵌入"这条规则，在这里就是排序能对的前提。圆柱侧面画成一条线性渐变（按可见半圈的法线取色），平面按四阶取色；运动模糊用 `lib.motionBlur`，只模糊机器那一层，版面和字不糊。面上的画（卡片内容、刻度、铭牌）在零件的局部坐标里写成线和点，跟零件一起摆姿态、投影；初版卡片上转动的小立方体也是这样一张随 t 变的面上的画。整条流程都是 t 的纯函数：正式渲染的 HyperFrames 部分约 11 s，`determinism.sh` 的 1 个和 3 个 worker 150/150 帧逐像素相同。
- **正式片**：物件更复杂时（回转体、管线、上百个零件），用 Anatomy 的工具包（`kit/turn-build.mjs` 的 3D 模式：分离平面加 GJK 排序，`node build.mjs --audit` 查穿模和遮挡顺序，`scripts/lines.mjs` 查线有没有悬空），或者 anatomy-reveal 的整套模板（`frame(t)` 是 t 的纯函数，puppeteer 渲染，按位移自适应的运动模糊）。两者都是 MIT：用 `bash references/fetch.sh anatomy`（或 `anatomy-reveal`）拉到 `references/repos/` 只读，按硬规则 6 复制到项目里再改，保留许可声明。它们自带的渲染和编码不经过本仓库的声音和检查，出片前照常走 `bin/vh mix`、`bin/vh qa`、`bin/vh check`。
- **要真实材质的镜头**（玻璃、金属反光、真实景深）用 Blender（`engines/blender.md`），那就不是这个风格了；两者可以在一支片子里分镜使用。

## 自查重点

- **缩小和放大**：缩到 640 px 宽，是不是一眼认出一台机器；放大 4 倍裁每个接合处（轴和轴承、推杆穿过导向杆、卡片插进夹子），看有没有空面、遮挡错、穿模。
- **拆开的过程**：每 2 帧一张 strip，看有没有零件穿过别的零件，合拢时有没有回弹穿进去。
- **线**：有没有悬在空中的线、在面中间断掉的刻度。
- **点亮**：任何一帧最多一个点亮的部件（或一条链），和图例里亮的那一行对得上。
- **读数**：随便抽一帧，读数和画面上零件的位置对得上（样片：表盘指针和 θ 一致）。
- **字号**：按观看档量 1080p 成片里的 px，四角的读数也算辅助字。

## 相关资源

- Anatomy：<https://github.com/wheresryan22/anatomy>（MIT）；anatomy-reveal：<https://github.com/annnguyentt/anatomy-reveal-skill>（MIT，`template/kit/` 来自 Anatomy）。两者的读法和能借什么见 `references/community-skills.md` 第 9 节。
- 本库里容易混的：`blueprint`（制图线稿、活的尺寸）、`tabletop-miniature`（真实光影的桌面小剧场）、`product-keynote`、`fui-hud`。
- `video-types/01-math-science-explainer.md`、`03-product-promo.md`、`06-paper-explainer.md`；`playbook/03-motion-design.md` §4（字号分档）；`playbook/08-vfx-and-motion-sources.md`（亚帧运动模糊）；`playbook/12-ideation.md`（立意：找一个和概念一一对应的物件）。
