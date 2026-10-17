# 编辑部数据叙事 · editorial-data

一句话：报纸图表部的语法。标题就是结论句，用衬线字；图里大多是灰，只有结论说的那条用强调色；注释用细引线钉在具体数据点上；图表按"先让观众猜，再给真相"的顺序展开。适合严肃的数据新闻、研究结果、社会和政策话题。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：0–0.1 s 基线、刻度线和四条灰色背景线一口气画满整宽（hook，0.1 s 一声 `tick`），0.1 s 起衬线标题逐词出现（80 ms/词）；1.2–1.6 s 一条灰虚线 "expected"（40 px 标签）画出并停到 2.0 s；砖红真实线在 2.0 s 强拍上开始线性画过，线头带着实时数值往上跳（14 → 122），三处注释（大纲、分镜、初版）在线经过时钉上；2.8 s 线冲出图框、端点标上"122 Code"，紧接着 2.8–3.33 s 纵轴从 0–100 重新定标到 0–150，注释跟着点走；3.33、3.67 s 端点各发一圈"最新值"脉冲；4.0 s 整版上滚到下一节。刻度和年份 36 px，注释英文 32 px。数据是示意的，画面左下角写明。实际字体：Charter Bold、Helvetica Neue、Songti SC Bold、PingFang SC。配乐 90 BPM，小节排成 2 + 1 + 3 + 3 拍，A 小调，Glass / Richter 式的极简：钢琴（`piano` 的 `bright`）反复弹同一个三音分解和弦，八分三连音，每拍一组，一段里音型不变，只有和声在走（Am → F → Dm）；大提琴（`cello`）在 A 上拉一个长音当持续低音，揭示时换一次弓；一只秒表式的 `clock` 按八分音符轻轻滴答；1.33–2.0 s 钢琴停下，只剩大提琴和滴答（揭示前的屏息）；2.0 s 红线开画时钢琴回来，每两拍的头上加一个低八度的 F；2.8 s 红线冲出图框时高音区一个 A；4.0 s 整版上滚时换到 Dm，音型照旧。

**怎么借**：这种风格的性格是编辑部图表的清晰层级（结论句标题 → 单位和范围 → 图 → 钉在数据上的注释 → 来源）、直接标注和有依据的观察。下面的色板、字体、节拍和配乐是样片的做法，供试做；纸面是一个起点，同样的层级和注释也能放进三维空间、地图或实物里。数据的含义（出处、单位、条形从 0 起）不能因为画法而变。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《You Draw It: How Family Income Predicts Children's College Chances》 | 2015 · The New York Times / The Upshot（Gregor Aisch、Amanda Cox、Kevin Quealy） | 先让读者画出自己以为的曲线，再揭示真实的那条；预期和现实的落差就是故事 |
| 《Women's Pockets are Inferior》 | 2018 · The Pudding（Jan Diehm、Amber Thomas） | 具体的实物轮廓（真实尺寸叠在一起）比抽象柱子更有说服力；一段话配一张图，一次只讲一个意思 |
| 新冠死亡轨迹对比图 | 2020 · Financial Times（John Burn-Murdoch） | 对数纵轴 + 对齐起点（"第 N 例之后的天数"）；国家名直接写在线尾，没有图例；只高亮两三条，其余全灰；注释标出每国封城的时刻 |
| Visual Vocabulary 图表选择海报 | 首版年份未核实（约 2016）· FT Visual Journalism Team（Alan Smith 等） | 按数据关系选图（偏差、相关、排序、分布、随时间变化、部分与整体、量级、空间、流向），不按好看选 |

核实：NYT 与 Pudding 两篇的作者和日期来自原文页与作者主页；FT 轨迹图的日期和做法来自 Nightingale 的专访与作者当年的推文；Visual Vocabulary 的九类关系来自 FT 在 GitHub 的 `chart-doctor` 仓库（CC BY-SA 4.0），首版年份没有找到一手出处。

**不照搬**：不仿三家的刊头、专有字体和 FT 的鲑鱼粉底色；不复刻任何一张具体的图和它的数据框架；数据一律自己取、自己标出处。

## 视觉语法

- **色板**：新闻纸白底，墨黑字，系列默认灰，只有故事主角用强调色。

  | token | hex | 语义 |
  |---|---|---|
  | bg 纸 | `#FAF8F3` | 页面底色（不是纯白，也不是 FT 粉） |
  | fg 墨 | `#1F1D1A` | 标题、正文、数值标签 |
  | accent 砖红 | `#B8312F` | 标题结论里说的那一条系列，全片只此一个 |
  | 对照墨蓝 | `#2F5E8C` | 需要"对照组"时才用，面积小于强调色 |
  | 系列灰 | `#A9A39A` | 其余所有系列，线宽比强调线细 |
  | 轴线 | `#D9D4CA` | 基线和至多 3 条水平参考线 |
  | 次要字 | `#6B655C` | 副标题、单位、来源行 |

- **字体**：标题用 Charter Bold（本机的编辑部衬线，fallback Georgia、Iowan Old Style）；注释、刻度、来源用 Helvetica Neue，数字一律 `tabular-nums`。衬线标题配无衬线注释是新闻图表的常见搭配。中文标题用 Songti SC Bold，中文注释用 PingFang SC。
- **构图**：像一篇文章。标题左对齐在安全框左上（x = 192），下面一行灰色副标题写单位和范围；图表区占画面宽 60–70%，同样左对齐；注释写在图内，贴着数据；来源行在左下，60% 不透明。竖屏时标题在上 1/4，图居中，注释放图的上方。
- **标注**：引线是 1.5 px 的墨线，一端是数据点上 4 px 的小圆圈，一端连着 2–3 行的注释文字；注释离数据点不超过一格，不挡线。直接在线尾写系列名，不用图例。
- **质感**：无，或 0.02 的纸纹。不加阴影、渐变、3D。

## 运动语法

帧数按 30 fps 计。

- **缓动**：注释入场 easeOutCubic `cubic-bezier(0.33,1,0.68,1)`，12–15 帧；图表变化用 easeInOutCubic `cubic-bezier(0.65,0,0.35,1)`；退场 easeInCubic。时间序列的线**线性**画出，因为横轴就是时间。不用 overshoot。
- **先猜后揭示**（签名）：先画一条灰色虚线的"你以为的"曲线，停 1.5 s；再用强调色线性画出真实曲线，画到哪里，那里的注释才出现。
- **重新定标**：数据冲出图框时，先停半拍让观众看见"出界"，再分两段变：坐标轴 0.4 s，数值 0.6 s（Heer & Robertson 2007）。注释钉在数据坐标里（数值 + 像素偏移），跟着点一起走。
- **时长**：每个被注释的状态至少停 2.5 s（风格节拍：要看的是图和它的变化，不只是注释那行字；比读时底线长）；每 3–4 s 一个新的状态或注释；计数不超过 1.5 s，最终状态停 ≥ 2 s。
- **转场**（样片用这 3 种）：同一空间里变值（rescale）；编码变形（morph，点变柱、线变面，分阶段）；整版上滚（scroll-up），像读者往下滚文章，进入下一张图。同一空间里变值最稳；换空间、换形式时，留一个认得出的线索（同一个颜色、同一个标签、一条从旧位置接到新位置的线）。
- **镜头**：样片是固定机位，进入细节时一次 ≤ 1.15× 的慢推。数据放进空间里时镜头可以走，只要观众一直认得出对象、单位和时间。
- **文字动画**：逐词（stagger），80 ms/词，每词上移 12 px 并淡入；中文 60 ms/字。

## 声音语法

- **配乐**（样片）：克制、低调，Philip Glass / Max Richter 式的极简。A 小调，90 BPM（30 fps 下一拍 20 帧）。签名是钢琴反复弹同一个分解和弦音型（八分三连音），一段里音型不变，只换和声；下面大提琴（`cello`）拉一个持续的 A；一只秒表式的 `clock` 按八分音符很轻地滴答，是编辑部的钟。小厅混响，钢琴在左、大提琴在右。揭示真实数据前 0.5 s 钢琴停下，只留大提琴和滴答。
- **音效**：极少。注释出现一声 −20 dB 的 `tick`，柱子落定一声轻 `click`；不用 whoosh。
- **声画关系**：旁白逐句驱动，每句对应一个图表状态；旁白念到某个数字的那一刻，对应标记高亮。
- **样片拟音**：`events.json` 12 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs <slug>` 生成，落点全部引用动作所用的同一张时间表，声像取发声物体的屏幕 x（`(2x/W − 1)·0.7`），按 `profile=swatch` 混在配乐下：0.1 s 图框和灰线画满一声 `tick`，标题后三个词各一声 −24 dB 的 `tick`；虚线画完、纵轴定标完成（同时第一圈脉冲）、第二圈脉冲各一声 −20 dB 左右的 `tick`；三处注释在红线经过的那一刻各一声轻 `click`（落点 = 红线到达该数据点的时间，同一个函数）；红线画出时唯一一声 `whoosh`（−16 dB）；端点和 "Code" 标签 `toggle`。整版上滚不配声。
- **样片的转场音效**：`air`：唯一一条砖红线画出时一口气，声像跟着线从左走到右（0.8 s）。

## 适合与不适合

- **适合**：05 数据故事（主类型）；06 论文结果部分；02 横屏深度科普。
- **不适合**：情绪化的品牌片、低信息量的 hype、梗视频。
- **容易被误用成**：带图例和满屏网格的 Excel 图、6 格仪表盘、没有叙事的 bar chart race。

## 常见误用及原因

1. 标题写成主题词（"GDP 趋势"），不是结论句（"收入越高，上大学的比例几乎线性上升"）：观众得自己去找结论。
2. 图例、满屏网格、双轴、饼图、3D 图：观众在解码，不在读结论；双轴还容易叠出两条线之间并不存在的关系。
3. 彩色系列太多，或强调色没有落在结论说的那条上：观众不知道该看哪条。
4. 【底线】屏幕上的数字没有出处，或示意数据没有标"示意"。
5. 【底线】条形图的纵轴不从 0 开始：长度就是数值，截掉一段会夸大差距；对数轴、截断轴要在轴上写明。

## Prompt 块

```text
Borrow the clarity of a newspaper graphics desk: a clear hierarchy (the finding as a sentence headline, a dek with units and range, the chart, notes pinned to data points, a source line), direct labels instead of legends, and observations the data supports.
First find the question in the data worth the viewer's attention, then choose how to tell it: compare, follow a turning point, or move between the whole and one part. The printed chart is a starting point; the same hierarchy and pinned notes can live in a 3D space, on a map or on real objects.
Keep objects, units and time easy to recognise, and when the form changes keep enough cues that the viewer knows it is the same thing. Pace follows the data, the weight of each event and the time needed to read. Colour, camera and sound serve the content; the visual treatment never changes what the data means.
The swatch's settings, to try or to depart from: warm newsprint #FAF8F3 and ink #1F1D1A; every series grey #A9A39A except the one the headline is about, thicker, in brick red #B8312F; a serif headline (Charter Bold) over Helvetica Neue notes with tabular numbers; a dashed grey "what you might expect" line, a hold, then the real line drawn linearly with each note appearing as the line reaches it; staged ~1 s rescales (axes first, then values), annotated states held about 2.5 s; quiet 90 BPM minor-key minimalism under the narration, the piano stopping for half a second before the reveal.
```

## 引擎做法

- **首选 HyperFrames + SVG**（或 Canvas），数据在 Python 里算好导出 `data/*.json`；比例尺可以用 `d3-scale`，但不用 d3 的 transition，所有值由 t 算出。
- **线性画线**：`stroke-dasharray = L`、`stroke-dashoffset = L · (1 − u)`，u 对时间线性；Canvas 里用 `lib.strokePartial`。
- **注释跟点走**：注释位置 = `scale(x_data, y_data) + [dx, dy]`，rescale 只改 scale，注释自动跟随。线尾标签的防碰撞在 setup 里做一次竖向松弛，按数值排序，不在逐帧里做。
- **先猜后揭示**：猜测线是一条单独的数组，灰色 `[10, 8]` 虚线，揭示后降到 30% 留作对照，不删。
- 样片 `swatch.js`：逐段做法见开头"样片里"。实现要点：标题在 0.1 s 就开始逐词出现，不等到 0.8 s；"先猜"的虚线要画完并停住至少 0.4 s（样片 1.6–2.0 s），真实线落在强拍上开画，和配乐的屏息对齐。

## 自查重点

- 屏幕上的每个数字都能对上数据文件，抽 3 个手算。
- 标题是结论句吗？强调色是否只落在标题说的那条系列上？
- 放大 crop：每条引线的小圆圈是否正好压在数据点上；rescale 之后是否仍然对准。
- 注释停得够看图和它的变化（样片按 2.5 s，见上面的"时长"），中文注释 ≥ 46 px、英文 ≥ 28 px。
- 纵轴从 0 开始（条形图必须）；对数轴要在轴标题里写明"对数刻度"。

## 相关资源

- `references/repos/lemo-opuscar/styles/dataviz/STYLE.md`（LemoLab，CC BY 4.0）：注释钉在数据坐标里、坐标轴随故事长出来、出界后再定标。本文借了这三条，改成新闻纸、衬线标题和"先猜后揭示"的顺序，去掉了铅笔和声音化。
- `references/repos/hyperframes/skills/hyperframes-creative/references/data-in-motion.md`；`references/repos/data-animation-skills/skills/chart-animation/SKILL.md`（MIT）。
- `video-types/05-data-story.md`（主类型的禁止项和 Prompt 增量块）；`playbook/03-motion-design.md` §2。
- 外部：FT `chart-doctor` 仓库的 Visual Vocabulary（<https://github.com/Financial-Times/chart-doctor>，CC BY-SA 4.0，只读其分类）。
