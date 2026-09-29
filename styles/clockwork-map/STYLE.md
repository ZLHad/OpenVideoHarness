# 机械钟表地图 · clockwork-map

一句话：一张铺在台面上的羊皮纸地图，每个地点都是一台黄铜机械，被齿轮一格一格顶出地面、展开、咔哒锁定；镜头从头到尾低空飞行，不切。适合讲"地点之间的关系"：历史版图、路线与迁徙、供应链、多城市的产品发布，也适合系列片的片头和章节导航。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《Game of Thrones》片头 | 2011 · Elastic；创意总监 Angus Wall，美术指导 Robert Feng，动画 Kirk Shintani，设计 Hameed Shaukat；获 2011 年艾美奖最佳片头设计 | 地图就是舞台：地点由看得见的机械从地面升起、展开、咬合；镜头在地点之间连续俯冲，一镜到底；木、石、锡、黄铜的手工质感；每集按剧情换地点，结构不变 |
| 布拉格天文钟（Orloj） | 1410 · 钟表匠 Mikuláš of Kadaň 与天文学教授 Jan Šindel | 同心圆环和刻度的层级：外环慢、内环快；指针一格一格走；黄铜、深蓝、金三色的配色逻辑 |
| 波特兰海图（portolan chart），现存最早的是 Carta Pisana | 13 世纪后半叶 · 地中海制图者（佚名），藏于法国国家图书馆 | 从罗盘玫瑰放射出的方位线网是整张图的骨架；海岸线外侧用平行细线"描边"；地名沿海岸排成一圈 |

核实：GoT 片头的制作方、团队名单和艾美奖来自 Wikipedia 与 Art of the Title；Orloj 的年份和作者来自 Wikipedia 与布拉格旅游局；Carta Pisana 的年代来自 Wikipedia 与美国国会图书馆的海图指南。

**不照搬**：不用维斯特洛的地形、家族纹章、城堡造型和片头主题旋律；不做"球壳内壁 + 中心太阳的浑天仪"这个构图；不复刻原片任何一段镜头路径。

## 视觉语法

- **色板**：羊皮纸、墨、黄铜三类材料，加一个朱砂。

  | token | hex | 语义 |
  |---|---|---|
  | bg 台面暗 | `#16120D` | 地图以外、远处的暗、片头字的底 |
  | fg 纸白 | `#EADBB8` | 标题和铭牌上的字 |
  | land 羊皮纸 | `#D8C49B` | 陆地 |
  | sea 旧铜绿 | `#5E6F68` | 海；海岸外侧的平行细线用它加深 30% |
  | ink 墨 | `#3A2A1A` | 海岸线、方位线、地名 |
  | brass 黄铜 | `#B08D57` | 机械本体；高光 `#E6C98A`，阴影 `#6E5634` |
  | accent 朱砂 | `#A8322A` | 唯一强调：当前路线、当前地点的小旗。同一帧只有一处 |

- **字体**：标题用 Baskerville SemiBold，句首大写，字距 +0.04em（刻出来的铭文感）；地名和铭牌用 Copperplate，全大写，字距 +0.12em；中文用 Songti SC Bold（宋体的刻本感和 Baskerville 搭）。不用 Blackletter 和花体。
- **构图**：地平线（地图远端）放在画面上 40–45% 处，上方是暗台面，标题放在那里；地图占下方 55–60%。镜头俯角 25–35°，高度约为地点间距的 0.6 倍。主角机械升起后占画面高 25–40%；铭牌正对镜头（billboard），离机械底座不超过一格。远处的地图可以微微上卷（曲率半径 ≥ 画面宽的 3 倍），但不做完整球壳。
- **质感**：羊皮纸用两层 fbm（大斑 ±6% 亮度、细纹 ±2%）加边缘焦暗；黄铜用三段平涂（阴影、本色、一条锐利高光），不做 PBR 反射。整体一盏暖色主光从地图中央偏上照下，离光越远越暗（径向压暗 35%），机械在地图上投出朝前的影子。颗粒 ≤ 0.05。

## 运动语法

帧数按 30 fps 计。

- **擒纵步进**：所有可见齿轮按八分音符一格一格走。90 BPM 下每个八分音符 10 帧：前 4 帧用 easeOutCubic 转过一个齿（12 齿 = 30°），后 6 帧静止。啮合的两个齿轮转角比等于齿数反比、方向相反，初相差半个齿，齿不能穿插。齿轮只允许这种步进，不许匀速空转。
- **机械升起**：一个地点的完整动作 36–54 帧：舱盖滑开 8 帧 → 本体顶起 18 帧（`cubic-bezier(0.76,0,0.24,1)`）→ 面板绕铰链逐块翻开，每块 12 帧、错开 2 帧 → 锁止，弹簧 stiffness 500 / damping 36（ζ≈0.8，约 1.5% 回弹），配一声咔哒。沉回地下用 `cubic-bezier(0.5,0,0.75,0)`。
- **一次只动一台**：同一时刻只有一个主机械在升起，其他地点只有齿轮在走。每 2.5–3.5 s 一个新地点或新动作；每个地点至少停留 2.5 s 让铭牌读完。
- **镜头**：一镜到底（oner）。沿地点之间的样条飞行，整段用 easeInOutSine，经过地点时减速到 20–30% 但不停；镜头的俯角和高度也是 t 的函数，不做手持抖动。
- **转场**（只用这 3 种）：
  - 飞越（fly-over）：地点之间不切，镜头沿方位线飞过去；
  - 铰链翻板（hinge-flip）：一块地图沿铰链翻面，背面是下一层地图（下一个时代、下一张图）；
  - 拉远（pull-back）：结尾镜头抬高、俯角转到 90°，整张地图连同朱砂路线一次看全。
- **文字动画**：压印式逐字（stagger）。每个字母 60 ms 错开，从 112% 缩到 100%，同时从高光色 `#FFF1C8` 压暗到纸白，像字被冲压进铜牌。中文每字 90 ms。

## 声音语法

- **配乐**：D 小调，90 BPM（30 fps 下一拍正好 20 帧），低音固定音型（`bass`）+ 持续 `pad` + 八分音符的 `arp` 当作机芯；每到一个地点响一次 `bell`，大机械锁止时加一记 `taiko`。用 3/4 拍（`meters` 把每小节设成 3 拍，90 BPM 下正好 2 s 一小节），机芯的走动有华尔兹式的回旋感；只借"三拍子 + 低音固定音型"的语法，不借任何旋律。
- **音效**：签名是擒纵的 `tick`，每个齿轮步进一声，落在八分音符上；锁止用 `click` 叠低通的 `impact`；镜头飞越用 `whoosh`，峰值对准镜头速度最大的那一帧。有授权的钟表机芯、木头吱呀录音优先。
- **声画关系**：机械锁止落在小节线上，面板翻开落在八分音符上。结尾拉远前留半小节只有 tick 的"屏息"，pad 不停。

## 适合与不适合

- **适合**：02 知识短片（历史版图、地理、路线）；05 数据故事里"地点 + 少量数字"的部分；03 多城市或多模块的发布片；长片的片头和章节导航。
- **不适合**：需要精确地理和边界的地图（这是舞台化地图，不是 GIS）；数字密集的分级设色图；只有一个地点的故事。
- **容易被误用成**：奇幻 cosplay（龙、纹章、中世纪字体），或者"旋转的 3D 地球 + 发光航线"。

## 禁止项

1. 齿轮只是装饰：不和任何在动的部件啮合，或者匀速空转。
2. 奇幻套装：纹章、龙、羊皮卷轴标题、Blackletter 字体。
3. 地点之间硬切或 crossfade；整片应该是一次飞行。
4. 几台机械同时升起，画面没有主次。
5. 发光、霓虹或粒子的航线；这是黄铜和墨的世界，路线是一条朱砂墨线。
6. 用真实国家地图却自己画边界。涉及中国的地图必须用有审图号的底图，否则改成示意地形、不画国界。

## Prompt 块

```text
Visual style: clockwork map. The film is one continuous low flight over a parchment map on a dark table (#16120D): land #D8C49B, sea #5E6F68, ink #3A2A1A coastlines with parallel offshore echo lines and windrose bearing lines radiating from compass roses. One warm key light from the map centre; light falls off 35% toward the edges. Each location is a brass mechanism (#B08D57, highlight #E6C98A, shadow #6E5634) that rises out of the map: a hatch slides open, a shaft lifts it (18 frames, easeInOutQuart), hinged panels unfold one after another (12 frames each) and lock with a small 1.5% settle. Every visible gear meshes with a moving part and advances like an escapement, one tooth per eighth note in 4 frames, then holds; no free-spinning gears. Only one mechanism moves at a time. The camera never cuts: it glides along bearing lines on a smooth spline, slows near each site without stopping, and at the end rises to a top-down view of the whole map. Place names are stamped into brass plates in engraved caps (Copperplate), titles in Baskerville; letters press in one by one (60 ms stagger). One accent only: vermilion #A8322A for the current route. No heraldry, dragons, blackletter, neon routes or particles. Sound: escapement ticks on eighths, a lock on each downbeat, a low minor-key ostinato at 90 BPM with a bell on each arrival.
```

## 引擎做法

- **首选 HyperFrames + Three.js 层**：地图是一张大平面，纹理在 setup 里程序化生成一次（fbm 羊皮纸、阈值化的虚构海岸、方位线），机械用 Box/Cylinder 组合，每块面板一个铰链 pivot；光只用一盏暖色方向光加 0.25 环境光，打开阴影贴图，升起的机械投影随高度变长。镜头用 `CatmullRomCurve3`，`u = easeInOutSine(段进度)`。一切由 t 算出，不用 AnimationMixer 的时钟。
- **纯 Canvas2D 的做法（样片用的就是这个）**：俯仰相机下，平面上同一屏幕行对应地图上的一条水平线段，所以可以逐行 `drawImage` 地图纹理（mode-7 式），俯角从 30° 连续转到 90° 也成立。行的深度 `d = h / (sinθ + v·cosθ)`，地图坐标 `X = camX + u·d`、`Z = camZ + (cosθ − v·sinθ)·d`。远处行一次采很多纹素，要预先做 1/2、1/4 的 mip 纹理按缩放比挑，否则闪烁。机械按同一个投影函数算底座和顶部的屏幕位置，再画成 2D 的黄铜形体。
- **擒纵函数**：`k = floor(b)`、`f = clamp(fract(b) · 10 / 4)`、`angle = (k + easeOutCubic(f)) · 2π / teeth`，其中 `b = (t − t0) · BPM / 60 · 2`。从动轮 `angle2 = −angle · teeth1 / teeth2 + π / teeth2`。
- **海岸线**：低分辨率 fbm 场放大后取阈值；离海岸 0.04、0.08、0.12 的等值线画成海里的平行细线，这就是老海图的味道，一次算好缓存。

## 自查重点

- 取 8 帧 strip：每个可见齿轮都在驱动东西；相邻齿轮转向相反，齿没有穿插；步进落在八分音符上（±1 帧）。
- 任意时刻只有一台主机械在动。
- 暂停在任意一帧，镜头都在运动（飞行中）；停下的只能是机械，不能是镜头。
- 铭牌上的地名：英文 ≥ 30 px、中文 ≥ 46 px（1080p），铭牌倾角 < 35°，停留 ≥ 2.5 s。
- 黄铜高光不能比铭牌上的字亮；远处的地平线压暗后不能出现摩尔纹和闪烁。
- 用了真实地理的话，边界来自合规底图，并在 NOTES.md 记下来源。

## 相关资源

- lemo-opuscar 没有对应风格。最接近的是 `references/repos/lemo-opuscar/styles/blueprint/STYLE.md`（LemoLab，CC BY 4.0）：齿轮按八分音符擒纵步进、零件按顺序展开归位的做法来自它，本文改写了数值和用途；`iso-infographic` 的"一个立体模型一镜讲完"也可对照。
- `playbook/08-vfx-and-motion-sources.md` 的"一镜到底（3D 世界）"和"声画联动"两节；`playbook/03-motion-design.md` §6。
- `video-types/02-knowledge-short.md`、`video-types/05-data-story.md`、`video-types/03-product-promo.md`。
- 外部：Art of the Title 的 GoT 片头页（<https://www.artofthetitle.com/title/game-of-thrones/>），只看语法，不取素材。
