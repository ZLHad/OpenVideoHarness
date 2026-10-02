# 浅色界面讲解 · pastel-ui

一句话：把讲解装进一个干净、友好的界面里。粉彩渐变墙纸上放白色圆角卡片，界面只有一个蓝紫强调色，每个概念各有一个颜色、从头带到尾，一次只聚焦一张卡片，最后答案本身变成画面。动起来像一个做得好的操作系统：弹簧只过冲一两个百分点，字被打出来、发出去，卡片被选中、被点开。适合"X 是怎么运作的"：知识短视频、App 和 SaaS 的功能讲解、轻量的数据故事。

样片：`media/swatch.mp4`（5 s，含配乐和拟音）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 0 帧是粉彩墙纸，五团大色块（薰衣草两团，桃、薄荷、丁香各一团）慢慢漂。0.07 s 画面中部的白色输入框亮起，一个粗描边的胶囊从它身上长出来，铺到画面四分之一以上，圈身分三段、颜色饱满，正是后面三个概念的颜色（珊瑚、薄荷绿、向日葵）；光圈散去，一圈同样三色的细环留在输入框外慢慢转。0.17–0.73 s 打出 "Every frame is code."，0.8 s 在小节线上发送：它变成蓝紫气泡，沿弧线飞到上方，1.2 s 前停稳。1.0 s 底部出现"正在输入"，1.1 s 中间先浮出三张骨架卡片；1.24–1.53 s 回复逐词流进来，"代码"是强调色，这就是中文字幕。2.0–2.24 s 三张卡片盖掉骨架抬进来：大纲（要点逐行画出）、分镜（六格里一个球往前跳）、初版（正在渲染的预览，内容是这面墙纸的缩小版）。白点沿下面的轨道走，2.4 / 2.8 / 3.2 s 每到一个节点，节点填色、荡一圈波纹，焦点移过去：那张卡片放大到 1.2 倍，另外两张退到 60% 不透明，`STEP n/3` 滚一格。3.3 s 初版开始回放，球跳两下，卡片同时被"拿起来"：原地往上抬、再放大一点；3.6 s 三个节点依次再荡一圈。4.0 s 初版卡片展开成整个屏幕（容器变换），它的预览变成画面本身：球跳完最后一下落地，底部三色进度条走到头，"Pastel UI / 浅色界面讲解"落在中间，下面依次弹出三个概念签（大纲、分镜、初版，各带自己的颜色）。实际字体：Avenir Next Demi Bold / Medium、PingFang SC Semibold、Menlo Regular。配乐 150 BPM、D 大调：卡林巴、Rhodes、拨弦低音提琴、弦乐 pad、响指。

## 学习对象

| 作品 | 年份 · 出处 | 从它身上学什么 |
|---|---|---|
| 《你问 AI 一句话之后的 3 秒钟》 | 2026-09-29 · 科了个喵，抖音（拆片见 `cases/oneshot-five.md` 第 1 节） | 浅色界面讲解可以很耐看：柔和的三色底、白卡片、一个蓝紫强调色；每个 token 一个颜色一路带到输出；常驻读数告诉观众走到哪了；结尾答案变成画面 |
| Material You（Material Design 3） | 2021 · Google，2021-05-18 在 Google I/O 上和 Android 12 预览版一起公布（当时 Android 12 还在 beta） | 动态取色：从墙纸里提取颜色，生成一套柔和的色调板，界面跟着墙纸换色 |

核实（2026-10-02）：科了个喵那支片子的日期、配色和读数以 `cases/oneshot-five.md` 的拆片为准；Material You 的公布场合、日期和动态取色按维护方核对过的事实写。

**不照搬**：开场在输入框里打字再发送，和原片前 5 秒是同一种镜头（原片打的是一个问题）。样片保留它，因为"打出来、发出去"是这个风格的签名；换掉的是节奏（0.8 s 内发出）和颜色的来历（三个概念色从输入框里长出来）。想彻底避开，可以让标题以一条通知或一张卡片进场。其余不用原片的镜头和它的"回车后 x 秒 / 慢放 ×N"读数，不用 Google 的组件和字体，聊天界面是通用的，不仿任何真实 App。

## 视觉语法

数字是样片在 1920×1080 里的值，换题材、换画幅时按理由调。

- **色板**：

  | 角色 | 颜色 | 含义 |
  |---|---|---|
  | 墙纸 | 底 `#F6F4FB`；薰衣草 `#DCD2FA`、桃 `#FFD9C7`、薄荷 `#C9EEDF`、丁香 `#EBD3F2` | 只是气氛 |
  | 卡片、输入框 | `#FFFFFF` | 界面本身 |
  | 主字 / 次要字 | `#1E2034` / `#4F5270` | 所有要读的字（次要字对白底 7.6:1） |
  | 强调色 | `#5B5BEF` 蓝紫 | 界面在做事：发送键、我发出的气泡、关键词、轨道上的白点和播放头 |
  | 概念色 | 珊瑚 `#FF8A66`、薄荷绿 `#2DBE94`、向日葵 `#F2B33D` | 一个概念一个颜色，开场的光圈、卡片、轨道、结尾的进度条都是同一个 |
  | 阴影 | `#3A2E80`，11% 和 7% | 带一点紫，比灰黑的软 |

  强调色只有一个；概念色可以有几个，每个只代表一样东西。概念色对白底只有 1.9–2.4:1，只做色块和填充，不写字；要读的字用主字、次要字，或白字配强调色（5.0:1）。概念多于五六个就按组上色。
- **字体**：Avenir Next（标题 Demi Bold，标签 Medium），像系统界面；中文 PingFang SC Semibold；读数 Menlo。换圆体更童趣，但少一点"真界面"的感觉。
- **字号**：按 BRIEF 的 `Watch on` 定下限（`playbook/03-motion-design.md` §4，1080p 合成里的 px）：

  | 在哪看 | 主标题 | 辅助、标签、读数 | 字幕 |
  |---|---|---|---|
  | `phone` | ≥ 84 | ≥ 44 | ≥ 65 |
  | `desktop` | ≥ 84 | ≥ 44 | ≥ 48 |
  | `feed` | ≥ 150 | ≥ 80 | ≥ 115 |

  样片按 `desktop` 做：过下限的是停稳后的标题，92 px（≥ 84）。打字的 0.6 s 里它是输入框中 72 px 的字，这是一个过渡状态，按标题算并不够 84，样片是靠"发出去就长大"让它过线的；正片里如果标题要在输入框里停留，就把输入框里的字也做到 84 以上。卡片中文 56 px、英文 44 px（聚焦时 67 / 53 px），读数 46 px，字幕 60 px，片名 124 / 64 px，结尾的概念签 56 px。这套版式过不了 `feed` 的下限，发信息流要重排。把 App 的字号（14–17 pt）照搬进视频是最常见的错。
- **构图**：开场只有一个居中的输入框；之后分三条带：顶上标题，中间图解，底部字幕。一排卡片同时只有一张是主角，其余退后但仍读得出。留出至少三分之一的墙纸。竖屏时卡片竖着叠。
- **形状和阴影**：卡片圆角 36 px，输入框、气泡、字幕是胶囊；阴影两层（大而淡加小而实），聚焦时加深。
- **质感**：墙纸是几团很大的径向渐变，衰减接近高斯，各自以 ±50 px 慢慢漂；盖一层固定的细噪声（约 ±1.5 个色阶）防色带。不加颗粒。磨砂玻璃最多用在一个有功能的地方（固定的顶栏）。

## 运动语法

- **弹簧**：进场都用闭式弹簧（`lib.spring`），默认 `w 13, ζ 0.8`，过冲约 1.5%；停稳用 `ζ 0.9`。只有节点、小圆点这种"冒出来"的小东西用 `ζ 0.62`（约 8%）。
- **先有因，再有果**：打字 → 发送 → 正在输入 → 回答流进来；白点到节点 → 焦点移过去 → 读数加一。跟着因果走，不用旁白也看得懂。
- **焦点**：讲到哪一步，哪张卡片就放大，其余退后，每一拍都是看得出不同的画面。同一件事只用一两种方式表达（样片只留轨道和 `STEP n/3`）。
- **路径**：东西从一处飞到另一处时，纵向比横向快一点，走弧线。
- **占位**：内容还没到的地方放骨架卡片加一道加载扫光，真内容到了直接盖上去，等待也有东西看。
- **文字动画**：签名是"打出来、发出去"：标题先逐键打出，再变成气泡；回答逐词流进来，气泡先长、字后到；读数的数字往上滚。
- **转场**：样片的招牌是容器变换：被聚焦的卡片展开成整个屏幕，里面的内容变成下一屏。同家族的还有信息流滚动（一甩，按惯性滚过一屏，越过停靠点一点再弹回）。不用交叉淡化，不用圆形遮罩。
- **镜头**：没有摄影机。动的是界面：聚焦、点开、滚动。
- **读数**：要真的在数东西（步骤、进度、计时），并且和画面上别的进度表示不重复。

## 声音语法

- **配乐**：轻、干净的器乐，像 App 的提示音放大成一首曲子。样片 150 BPM、D 大调，小节拍数 2/3/3/2/3，段落落在 0.8、2.0、3.2、4.0 s：卡林巴（`kalimba`）担当所有事件（光圈一个和弦，发送三个上行音，焦点每移一次高一级，展开一串琶音，落地一个和弦）；Rhodes 每段一个和弦；拨弦低音提琴走根音；弦乐 pad 从头垫到尾，不会有数字静音；2.0–4.0 s 反拍上一层轻响指（`clap` 的 `o`）。邻近的 `bubble-chart-story` 用马林巴加沙锤，这里刻意避开。
- **音效**：全是界面声音，小、亮、近：`air` 配光圈，`typing`，发送是 `click` 加短的 `swoosh_tonal`，`pop` 配东西出现和球落地，`tick` 配小读点，`toggle` 配焦点移动（固定提示音，三次一样是故意的），`whoosh` 往上配卡片展开，`shimmer`（降 7 个半音，落在 D 五声音阶上）配片名。声像按物体的 x 算：`pan = (2x/1920 − 1) × 0.75`。发送、落位、焦点移动都和卡林巴落在同一帧。

## 适合与不适合

- **适合**：02 知识短视频里的流程讲解（一次请求、一次支付）；03 App、SaaS 的功能讲解；05 轻量的数据故事。
- **不适合**：沉重的题材（粉彩显得轻佻）；奢侈品和电影感品牌片；信息极密的长表格；需要手作笔触的作品。
- **容易被误用成**：通用的"AI SaaS 模板片"，或者某个真实 App 的仿冒界面。

## 容易翻车的地方

反着做也可以，但要知道换来了什么。

1. **粉彩上写浅色字**：底已经很浅，字再用灰或概念色，手机上第一个看不清。
2. **颜色变成装饰**：同一个概念前后换色，"一个概念一个颜色"这条线就断了。
3. **离"AI 默认片"只差一步**：加了紫色光晕、渐变字、满屏磨砂，就成了 `TASTE_CHECKLIST` 第 10 条那种片子。开场的光用概念色、做成清楚的形状，别做成一团发光的紫球。
4. **同一件事说四遍**：打勾、亮灯、读数、进度条同时表示进度，画面挤成仪表盘，每一拍又都差不多。选一两种，力气留给焦点。
5. **整片都在弹**：每个元素都过冲 10%，看起来像儿童 App。
6. **读数不数东西**：和内容无关的跳动数字是装饰（`TASTE_CHECKLIST` 第 20 条）。
7. **渐变出色带**：大面积柔和渐变在 8 bit 和 H.264 里会出一圈圈台阶。墙纸画进不透明图层、衰减取接近高斯、再加一层固定噪声，代价是码率多约 30%。

## Prompt 块

```text
Visual style: a light, friendly UI explainer. A soft pastel mesh wallpaper (lavender, peach, mint) of large gaussian-falloff blobs drifting slowly, finely dithered against banding. White rounded cards, pill input, bubbles and caption on it, each with a two-layer violet-tinted soft shadow. One blue-violet accent for what the interface does (send, my message, the key word, the walking dot); each concept owns one colour (coral, mint, sunflower…) carried everywhere it appears, opening to end; concept colours are chips and fills, never text. One card is the focus at a time: it scales to about 1.2× with a deeper shadow while the others step back to about 60 % opacity; progress is shown once (a stepper rail with a walking dot and a monospace step readout). One geometric-humanist sans in two weights, a semibold Chinese sans, a monospace for numbers, at the target screen's size floors. Motion like a good OS: springs with 1–2 % overshoot, a visible bounce only on small pops, curved paths, a title typed and sent as a bubble, an answer streamed token by token into a bubble that grows ahead of it, skeleton cards holding space. The interface can switch on with a crisp capsule of the concept colours growing out of the input (no glow). Signature transition: a container transform, the focused card opening into the full screen so its content becomes the next picture. No camera, no crossfades, no circle wipes. Sound: light instrumental around 150 BPM, major: kalimba on every event, electric piano one chord per section, plucked upright bass, a string pad underneath throughout, soft offbeat finger snaps in the busiest section; UI foley panned to where each thing is.
```

## 引擎做法

- **首选 HyperFrames**。正片里界面用 DOM 和 CSS 最自然（真文字、`border-radius`、`box-shadow`、`backdrop-filter`），但每个属性都由 t 驱动（GSAP 时间线 seek 或 t 的函数），不用 CSS transition 和 `@keyframes`。样片画在一张 canvas 上（`swatch.js`）。
- **墙纸**：径向渐变画进不透明离屏图层再整层贴上，色标取近似高斯的五点（1、0.88、0.58、0.24、0），加固定噪声 `lib.grain(layer, 0, {amount: 0.03, mode: "source-over"})`（t 固定为 0，不闪）。
- **三色胶囊**：`createConicGradient` 以输入框中心为圆心、在三分之一处硬切色标，描一个胶囊；0.55 s 从输入框尺寸长到 1860×620，`outExpo`，线宽 46 → 14，过半才开始淡。细而淡的描边在粉彩上几乎看不见。
- **焦点**：`f = spring(t − t_k) − spring(t − t_{k+1})`，缩放 `1 + 0.2 f`，其余按 `1 − f` 退后，按 f 排序绘制。
- **容器变换**：卡片矩形用 `cubic-bezier(0.2,0,0,1)` 插值到整屏，圆角归零，卡片自己的内容在前 30% 淡出；预览矩形同步插值到整屏，内容按归一化坐标画，球的跳跃在放大中是连续的。预览画的是同一帧的墙纸图层，所以展开后就是背景本身。
- **打字和流式回答**：落键帧和回答的最终版式都在 setup 里算好；气泡宽度用一串弹簧追到每个词的右边界，比词早 0.09 s 起步，字裁在气泡里。
- **概念色**：放在 `tokens.json` 的 `palette.entity`，所有地方按下标取。轨道的进度用分段渐变，只在节点附近短短过渡（珊瑚直接渐变到薄荷，中间会发灰发褐）。
- **拟音**：`swatch.js` 末尾的 `FOLEY` 引用画面的时间常量，`node styles/_swatch/foley.mjs pastel-ui` 生成 `events.json`。

## 自查重点

- **对比度**：要读的字是不是都是深色或白字配强调色；退后的卡片在 60% 不透明下还读得出吗。
- **颜色一致**：同一个概念在光圈、卡片、轨道、进度条上是不是同一个颜色。
- **每一拍不同**：1 fps 联系表上，焦点移动的几拍是不是明显不同的画面。
- **交接帧**：逐帧看发送、第一个流出来的词（不能跑出气泡）、容器展开的头两帧。
- **色带和目标屏**：成片上 1:1 裁一块墙纸；按 `Watch on` 缩到对应宽度看一遍，退后卡片的英文标签最先看不清。

## 相关资源

- lemo-opuscar 的 `living-screencast`（LemoLab，MIT）是近亲：真实产品的界面重画成矢量、镜头在屏幕里推拉，追求"像录屏"；这里是通用的讲解界面，靠概念色、焦点卡片和"答案变成画面"。见 `references/repos/lemo-opuscar/styles/living-screencast/STYLE.md`。
- 本库：`fui-hud`（暗底电影界面）、`bubble-chart-story`（同为讲解，舞台是一张图）、`product-keynote`。
- `cases/oneshot-five.md` 第 1 节；`video-types/02-knowledge-short.md`、`03-product-promo.md`、`05-data-story.md`；`playbook/03-motion-design.md` §4、`playbook/04-audio.md` 的"转场音效按风格选"。
