# 图形统计 · isotype

一句话：维也纳图形统计法的语法。一个符号代表一份固定的数量，数量多就多排几个一模一样的符号，从不把符号放大；符号是平涂的剪影，没有轮廓线，没有透视，整整齐齐排成行；画面上唯一的变化，是某一行在拍点上加一个或减一个。适合讲"有多少""谁比谁多""从几个变成几个"。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐和 `events.json` 拟音）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：0.1 s，这支样片自己的 150 帧化成 25 个胶片符号（每个符号 = 6 帧），5 × 5 一整块同时盖章落下，每个高 160 px，占满画面中部（hook）。黑色表示还没播到，红色表示已经播过：从这一刻起，每 6 帧（150 BPM 的一个八分音符）就有一格变红，一直到片尾，这张图就是片子自己的钟。0.5 s 起，符号一行接一行移到右上角缩小成一块小图，下面落下图例"每个符号 = 6 帧"。标题每个八分音符落一个词，中文每个十六分音符落一个字；字从右边推 18 px 进位，用 3 帧，不淡入。母题是一行，从左到右三组：铅笔（大纲，黑）、画架（分镜，蓝）、摄影机（初版，红）。2.0 s 起每个十六分音符盖一个符号，每组下面的计数随之跳动；摄影机落定以后片盘每个八分音符转 45°。3.2 s 多加一台摄影机（4 → 5）；3.6 s 剪掉一个分镜（3 → 2），摄影机那一组随即左移补上空位。4.0 s 是签名转场"清点归零"：母题符号和标题每帧减掉一个，从右往左（英文词先走，给帧图让路）；同时帧图从最下一行开始逐行重排到右半边，放大成结束图版。4.4 s 名字落下，旁边是图例，4.8 s 最后一格变红。实际字体：Futura Bold / Medium、PingFang SC Semibold。配乐 150 BPM、G 大调，事件即音符：木鱼（`woodblock`）每个八分音符敲一下，就是帧图每变红一格（嘀、嗒交替），一直敲到 4.8 s 最后一格；玩具钢琴（`toypiano`）弹符号：0.1 s 整块落下是一个和弦，英文标题每个词一个音，2.0 s 起每盖一个符号一个音，一路往上数；拨弦（`pizzicato`）拨低音和中文标题的前五个字；3.2–4.0 s 撤掉低音，是转场前的屏息，画面照常走，加一台摄影机、剪一个分镜各是一个音；4.0 s 清点归零时玩具钢琴往下数，4.4 s 名字落下时一个和弦。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《Gesellschaft und Wirtschaft: Bildstatistisches Elementarwerk》（社会与经济：图形统计基础图集） | 1930 · 维也纳社会与经济博物馆（Otto Neurath 主持）；Leipzig: Bibliographisches Institut；100 幅彩色图版 | 一整本图集共用一套符号、一套颜色、一套版式：翻到任何一页，读法都一样 |
| 维也纳图形统计法（Wiener Methode der Bildstatistik），约 1935 年改称 Isotype | 1925 年起 · Otto Neurath（1882–1945）与维也纳社会与经济博物馆 | 核心规则：数量多就多画符号，不把符号放大；不用透视。按行排列、一个符号代表固定数量、颜色区分类别，是这套方法的通行读法 |
| Marie Neurath（本姓 Reidemeister，1898–1986）的"转换者"（transformer）工作 | 维也纳时期起；1942 年起 Oxford 的 Isotype Institute | 在数据和画面之间做翻译：先定下这张图要让人看懂哪一个比较，再定符号、行和颜色 |
| Gerd Arntz 的符号 | 1926 年起与 Neurath 合作，1929 年初进馆 · Gerd Arntz（1900–1988）；约 4,000 个符号，刻在油毡上；档案由海牙市立美术馆（Kunstmuseum Den Haag）管理 | 剪影用圆、矩形、梯形拼成；细节只用镂空（透出纸色）；靠一个特征（裙子、帽子、工具）区分类别 |
| 《International Picture Language》 | 1936 · Otto Neurath；London: Kegan Paul, Trench, Trubner & Co. | 这套方法的文字版 |

核实：
- 图集的年份、出版社和"100 幅彩色图版"来自宾夕法尼亚大学和斯坦福大学图书馆的书目。
- 博物馆 1925 年定名、约 1935 年改称 Isotype、两条核心规则（多画不放大、不用透视），来自 Wikipedia 的 Otto Neurath 和 Isotype 条目，以及 Isotype Revisited 网站。
- Marie Neurath 的生平、"转换者"的说法、1942 年的 Oxford 研究所，来自 Wikipedia 和 University of Reading 的开放论文（Marie Reidemeister and Otto Neurath: interwoven lives and work）。
- Arntz 1929 年初进馆（1926 年起合作）、约 4,000 个符号、油毡版，来自 Wikipedia 和荷兰 Geheugen van Nederland 的档案页。
- Isotype 图表一律用 Futura，来自 Michael Twyman 1975 年的《The significance of Isotype》（isotyperevisited.org 转载）。
- 按行排列、固定单位、颜色分类这三条，Wikipedia 只笼统提到"版式和用色有严格规则"，算**部分核实**。"引导符号"（guide pictogram）这个说法没有找到一手出处，**未核实**，本文不用。

**不照搬**：
- 不描摹任何一个 Arntz 原符号，样片里的胶片、铅笔、画架、摄影机都是按语法从头画的；
- 不复刻任何一张原图的数据、版式和标题；
- 不用图集的德文字样和博物馆标志；
- 不在画面里标"Neurath 风格"。

## 视觉语法

- **色板**：印刷油墨色，平涂在米白纸上；颜色只表示类别，不做装饰。一张图版最多用 4 个类别色。

  | token | hex | 语义 |
  |---|---|---|
  | bg 纸 | `#F2ECDF` | 米白纸 |
  | fg 墨黑 | `#1E1D1B` | 标题、第一类（样片里是大纲）；帧图里表示"还没播到" |
  | accent 朱红 | `#C23B2C` | 第二类，也是故事的主角（初版）；帧图里表示"已经播过" |
  | 蓝 | `#2D5B8C` | 第三类（分镜） |
  | 绿 / 赭黄 / 棕 | `#4E7A3B` `#D9A33F` `#7A5232` | 备用类别色（农业、工业、原料一类的题材） |
  | 灰 | `#9A958B` | 英文副标签、次要文字 |
  | 基线灰 | `#D6CDBA` | 各行站立的基线 |

  色值是按"印刷油墨"这个方向配的，没有照任何一张原图取色。
- **字体**：标题和数字用 Futura Bold，标签用 Futura Medium（Isotype 图表本来就用 Futura）；中文用 PingFang SC Semibold，回落 Heiti SC。中文标签 ≥ 46 px（样片 58 px），英文副标签 38 px。全片只用这一个西文字族。
- **符号**：
  - 剪影由圆、矩形、梯形拼成，放在高 100 的单位框里设计；
  - 细节只能镂空，透出纸色（胶片的齿孔、画板上的山和太阳、摄影机的片盘轴），不描边，不画五官；
  - 同一行里的符号完全一样，同一张图版里所有符号一样高；
  - 符号放大缩小只能用来适应版面，比如帧图开场 160 px、角上 72 px、结束图版 120 px，绝不用大小表示数量。
- **构图**：
  - 符号一个挨一个排在同一条基线上，间距固定，左对齐；
  - 类别标签和计数直接写在行下面；单位写进图例（"每个符号 = 6 帧"），图例紧挨着它说明的那张图；示意数据要注明（样片右下角 "Stage counts are illustrative"）；
  - 标题在左上角，只占两行；第二张小图（帧图）放在右上角，和标题分开；
  - 元素之间不重叠，没有透视、三维、阴影、渐变。
- **质感**：一层很淡的纸纹（`lib.paper`，斑驳 0.035）。没有网点，没有套印错位，那是 `risograph` 的事。

## 运动语法

帧数按 30 fps 计。

- **唯一的变化是加一个、减一个、变一格颜色**：
  - 新加的符号像盖章一样落下：4 帧，偏移 −24、−8、+3、0 px（落地压过头 3 px 再回位），不淡入、不缩放；
  - 字从右边推 18 px 进位，用 3 帧（easeOutCubic `cubic-bezier(0.33,1,0.68,1)`）；
  - 减掉是硬切，没有退场动画；空出来的位置由后面那一组在一个十六分音符里平移补上；
  - 变色也是硬切，一格一格变；
  - 计数数字和符号在同一帧变。
- **重排（regroup）**：同一批符号换一个版式时，一行一行沿直线移过去，每行 0.24 s（easeInOutCubic），相邻两行错开 0.03 s，行在移动中始终是直的；往大处展开时从最下一行先走，行与行不重叠；移动中符号可以缩放，那是换版式，不代表数量。
- **符号内部的小动作**：只允许一个，而且跟拍：摄影机的片盘每个八分音符转 45°。
- **拍点**：
  - 符号在十六分音符上加（150 BPM 下每 0.1 s 一个），清点归零时每帧减一个；帧图每个八分音符变红一格；
  - 标题每个八分音符一个词，中文每个十六分音符一个字；
  - 整块一次落下只用在开场的 hook，或者"换一张新图"的那一拍。
- **时长**：一组对比完整以后至少停 2 s（样片压缩到 0.4 s，这是样片的特例）；每 0.4 s 最多一次加或减，除非是清点。
- **转场**（只用这 3 种）：
  - 清点归零（count-down）：从右往左每帧减一个；样片里它和重排同时进行，所以不会出现一帧空白的纸，标题的英文词先走，免得重排的符号压过去；
  - 重排（regroup）：留下来的那张图一个符号一个符号地移到新版式，成为下一张图版的主体；
  - 换版（plate-change）：在强拍上硬切到下一张图版，像翻图集。
- **镜头**：锁定。整张图版就是画面，不推、不摇、不做三维。
- **文字动画**：一个词一个词落下（stagger），推 18 px 进位，不淡入。

## 声音语法

- **配乐**：像节拍器一样干、准，事件即音符。大调，150 BPM：木鱼（`woodblock`）在八分音符上走，就是钟；玩具钢琴（`toypiano`）只弹画面上的事件，加一个符号就是一个音，数量往上数，音也往上走，减一个就往下落；拨弦（`pizzicato`）做低音；一层压得很低的簧片和弦（`sheng` 当小风琴用）垫底，让拍与拍之间不掉空。不用长混响（`space: dry`），不用弦乐铺满，也不做进行曲式的军鼓。
- **样片 `score.json`**：`meters` 为 2 + 3 + 3 + 2 + 3 拍，段落边界落在 0.8、2.0、3.2、4.0 s，和弦 I–vi–IV–V–I，每个音都对着 swatch.js 里的一个事件：
  - `census`：木鱼从 0 s 开始数帧；0.1 s 帧图盖章落下，玩具钢琴一个 G 大调和弦；拨弦在强拍上；
  - `title`：英文标题四个词（0.8 / 1.0 / 1.2 / 1.4 s）是玩具钢琴 E–G–B–E 往上走，中文前五个字（1.5–1.9 s）是拨弦往下走的十六分音符；
  - `count`：2.0–2.8 s 每盖一个符号玩具钢琴一个音，从 G5 一级一级数到 A6（2 支铅笔、3 个画架、4 台摄影机）；
  - `cut`（3.2–4.0 s）：屏息，撤掉拨弦低音，垫底的和弦稍微抬一点。3.2 s 多加一台摄影机是更高的 B6，3.6 s 剪掉一个分镜落到 D6，3.7 s 摄影机补位时再轻轻一个 G6；
  - `plate`：4.0 s 清点归零，玩具钢琴按十六分音符往下数（A–F♯–D–B），拨弦回来；4.4 s 名字落下时一个 G 大调和弦；4.8 s 最后一格变红，木鱼敲最后一下。
- **音效**：极少，而且短。整行落下一声 `pop` 叠 `boom`；标题每个词一声 `click`；每组第一个符号一声 `toggle`；加一个用 `pop`，减一个用 `click`；清点归零一声 `swish_rev`；结束图版一声 `ding`。单个符号不配声，由玩具钢琴代替，否则一秒会超过 6 声。
- **声画关系**：数量变化必须落在十六分音符的网格上（±1 帧）；帧图变红和片盘转动都在八分音符上，所以木鱼一直有画面对应。屏息那一小节撤掉低音，只剩木鱼、玩具钢琴和垫底的和弦，但画面不停，帧图照常变红，那一次加、一次减因此格外清楚。
- **样片拟音**：`events.json` 共 16 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs isotype` 生成，落点和画面共用同一张时间表，声像取发声物体的横坐标：
  - 0.1 s：`boom` 和 `pop`，帧图落下；0.62 s：`whoosh`，重排到角上；
  - 0.8、1.0、1.2、1.4 s：四个词各一声 `click`；1.5、1.9 s：中文两声 `tick`；
  - 2.0、2.2、2.5 s：三组各开头一声 `toggle`；
  - 3.2 s：`pop`，+1；3.6 s：`click`，−1；
  - 4.0 s：`swish_rev`，清点归零；4.4 s：`ding`，名字落下。

## 适合与不适合

- **适合**：
  - 05 数据故事，这是主类型；
  - 02 知识短视频里讲人口、资源、比例、"每 10 个人里有几个"这类问题；
  - 06 论文里讲样本量、分组、计数类结果；
  - 公共信息、政策说明。
- **不适合**：
  - 带小数的连续量、密集的时间序列、小于一个单位的细微差别；
  - 情绪化的品牌片。
- **容易被误用成**：
  - 一堆风格不一的图标拼盘；
  - 按数量放大图标；
  - 三维或等轴测图标（那是 lemo 的 `iso-infographic`）；
  - 厕所标志式的剪贴画，符号只是装饰，不代表任何数量。

## 禁止项

1. 用符号的大小表示数量，或者把符号拉伸、压扁。
2. 透视、三维、阴影、渐变、描边、五官。
3. 同一张图里混用不同画风的符号，或者同一行里的符号长得不一样。
4. 颜色只是好看，不代表类别；一张图版超过 4 个类别色。
5. 淡入淡出、变形、弹簧式回弹（盖章落地时压过头 3 px 是唯一的例外）；把整张图一次倒上屏以后就不动了。
6. 没有单位、没有出处的数字。示意数据要在画面或说明里标"示意"。

## Prompt 块

```text
Visual style: pictorial statistics in the Vienna-method grammar. Flat, printing-ink colours on warm off-white paper (#F2ECDF): ink black #1E1D1B, vermilion #C23B2C, blue #2D5B8C, with green, ochre and brown in reserve; each colour is one category, never decoration, at most four per plate. Every quantity is shown by repeating one identical pictogram: more means more symbols, never a bigger symbol. Pictograms are solid silhouettes built from circles, rectangles and trapezoids, with detail only as cut-outs showing the paper; no outlines, no faces, no perspective, no shading, no 3D. Symbols stand in strict rows on a shared baseline at a constant pitch, left-aligned, with the category name and the live count written directly under each row, and the unit stated in a key next to its chart ("1 symbol = 6 frames"); illustrative numbers are labelled as such. Type is a geometric sans (Futura Bold for titles and numbers, Futura Medium for labels); Chinese in a clean semibold sans at 46 px or larger. The only changes are one symbol added, removed or re-coloured on the beat: additions stamp down over four frames (−24, −8, +3, 0 px), removals are cuts and the next group closes the gap, re-colouring is a cut, and the count changes on the same frame; a chart of the film's own frames can act as its clock, one symbol turning from black to red every eighth note. Title words slide 18 px into place, one per eighth note. Transitions: count-down (remove one symbol per frame, right to left), regroup (the remaining symbols travel one after another to a new layout), or a hard plate change on a downbeat. Locked camera. Sound: a dry 150 BPM counting grid where every event is a note: a woodblock ticking eighth notes as the clock, one toy-piano note for each symbol added (rising as the count rises, falling on a removal), a pizzicato bass, a low reed-organ bed; the bass drops out for the bar before the change.
```

## 引擎做法

- **首选 HyperFrames + Canvas2D**，也可以做成 SVG；数据先在别处算好，导出每个符号的 `{类别, 序号, 加入时刻, 移除时刻}`。
- **符号**：每种符号写一个绘制函数，在高 100 的单位框里用路径画出来，镂空用 `destination-out` 在离屏 canvas 上挖掉。setup 里按需要的尺寸和颜色各渲一张，逐帧只做 `drawImage`，位置取整。要在重排中缩放的符号（帧图），只渲最大的那一个尺寸，画的时候缩小（`imageSmoothingQuality = "high"`）。
- **一张表驱动一切**：符号是否在场、计数数字、清点归零的顺序、拟音的落点都从同一张时间表算出来。样片里用的是 `ADDS`（加入）和清点顺序（按 x 从右往左排）。
- **清点归零**：把在场的符号按 x 从右往左排序，第 k 个在 `4.0 + k/30` s 移除；文字按字（中文）和词（英文）拆成单元，同时从末尾开始减。
- **帧图当时钟**：第 i 个符号在帧号 ≥ 6i 时变红，这是帧号的纯函数；重排时第 r 行在 `t0 + 0.03·r` 起跑（展开时 r 倒过来数），位置和大小在两个版式的格子之间插值。
- **片盘转动**：摄影机预渲 4 个片盘角度（0°、45°、90°、135°），按"落定后第几个八分音符"取用。
- 样片 `swatch.js`：逐段做法见开头"样片里"。结束图版的大字在不同 worker 里光栅化会有极小差异（见"自查重点"最后一条），肉眼看不出。

## 自查重点

- 每一组的计数等于画面上这一组的符号个数，任取 3 帧手数一遍。
- 同一组里的符号完全相同（同一张离屏图），没有任何一个被单独缩放或变形；帧图整块缩放只发生在重排里。
- 帧图里红格的数目 = floor(帧号 / 6) + 1，任取 3 帧核对。
- 所有符号都站在同一条基线上，间距恒定；加、减、变色只发生在十六分音符的格点上（±1 帧），清点归零除外（每帧一个）。
- 颜色和类别一一对应，全片没有第五个类别色。
- 中文标签 ≥ 46 px；在 360 px 宽的手机画面上，三组的剪影仍然分得清是铅笔、画架还是摄影机。
- `determinism.sh`：132/150 帧逐像素相同，其余 18 帧（结束图版的大字）PSNR ≥ 104 dB。

## 相关资源

- `references/repos/lemo-opuscar/styles/pictogram-motion/STYLE.md`（LemoLab，MIT）：以 1972 年慕尼黑奥运会的几何人形为学习对象，一张卡片一个人形，踩拍切换。和本预设的区别：它讲"一件事"，Isotype 讲"有多少"。本文借了它"每个关键动作落在整拍上"的做法。
- `references/repos/lemo-opuscar/styles/iso-infographic/STYLE.md`（LemoLab，MIT）：把 Isotype 式的数字放进等轴测场景，入场带回弹。本预设反过来：纯平面、不透视，入场只有盖章落地的 3 px。
- 本仓库的 `editorial-data`（同属数据类：一条线加一个强调色）和 `risograph`（同样是 Futura 配暖纸，但靠叠印和错版；本预设是干净的平涂印刷）。
- `video-types/05-data-story.md`；`playbook/03-motion-design.md`。
- 外部资料：
  - Isotype Revisited（<https://isotyperevisited.org>）和 University of Reading 的 Otto and Marie Neurath Isotype Collection；
  - Michael Twyman，《The significance of Isotype》（1975，<https://isotyperevisited.org/1975/01/the-significance-of-isotype.php>）；
  - 海牙市立美术馆的 Gerd Arntz 档案（<https://www.geheugenvannederland.nl/nl/geheugen/pages/collectie/Archief+Gerd+Arntz>）。
