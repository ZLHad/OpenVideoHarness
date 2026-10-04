# 对称粉彩绘本 · symmetry-pastel

一句话：画面沿中轴对称，每一章换一套粉彩色，章节字卡像翻绘本，镜头用干脆的甩镜连接。它把一个故事讲成一本精致的小书。适合带点幽默的知识短片，生活方式和食品品牌，人物小传，以及"一步一步来"的流程讲解。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 0 帧是一道合着的胭脂红幕布，0.03–0.42 s 从中线向两侧对称拉开（ease-out，0.1 s 已开约四成），配一下拉绳的 click 和 swish_rev。幕后是一间剖开的粉色玩偶屋，有天花板、地板、两侧墙的剖面，两扇对称的窗、窗帘和壁灯。第 0 帧就在沿轨道从右侧横移，停在中线上。象牙色章节卡直切入画（约 60% 宽，标题 92 px，中文 64 px），各行间隔 150 ms 出现；1.5 s 窗帘拉开，1.2–4.0 s 慢推 1.00 → 1.03。三幅画在 2.0 / 2.4 / 2.8 s 依次落到钉子上，晃几下停稳：大纲、分镜，初版是一枚胭脂红奖章花结。3.2 s 铭牌翻面，3.6 s 两盏壁灯亮起。4.0 s 一个 9 帧甩镜，到薄荷色的第二章，第二章继续慢推。实际字体：Futura Medium / Bold、Songti SC Bold / Regular。配乐 150 BPM，G 大调，是 Desplat《布达佩斯大饭店》式的巴拉莱卡小进行曲，每段多一件乐器，房间小而亮：第 0 帧起 `balalaika` 用轮指（11 Hz tremolo）奏旋律，另一把巴拉莱卡低 6 dB 轮指和弦垫底，`pizzicato` 在强拍上拨低音；0.8 s 章节字卡进来时加 `cimbalom` 的十六分分解和弦和一声 `glockenspiel`；2.0 s 画落钉子时再加 `harpsichord` 的断奏反拍，低音和反拍组成"嘣—嚓"的行进；4.0 s 第二章加一面进行曲 `snare`（带滚奏），钟琴再敲一次。拟音：开幕用 click + swish_rev，甩镜用 whoosh，字卡用 ding，窗帘用 swish_rev，画落钉子用 tick，铭牌翻面用 toggle，壁灯用 click。拟音的落点写在 swatch.js 的 `FOLEY` 常量里，`events.json` 由它生成。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《布达佩斯大饭店》*The Grand Budapest Hotel* | 2014 · 导演 Wes Anderson；摄影 Robert Yeoman；平面设计 Annie Atkins；配乐 Alexandre Desplat | 中心对称构图；甩镜停下时落在另一个对称画面上；三个年代用三种画幅（1932 年那段用 1.37:1）；配乐用巴拉莱卡、齐特琴、扬琴这类民间弹拨乐器 |
| 《月升王国》*Moonrise Kingdom* | 2012 · 导演 Wes Anderson；摄影 Robert Yeoman（Super 16mm）；原创配乐 Alexandre Desplat，大量使用 Britten《青少年管弦乐队指南》 | 横移和横摇穿过一个个房间，像在看剖开的玩偶屋；一首曲子把乐器一件件介绍出来，正好对应"一层层展开"的结构 |
| 《天才一族》*The Royal Tenenbaums* | 2001 · 导演 Wes Anderson；摄影 Robert Yeoman | 整部片被当作一本书来讲，段落之间插章节书页；字卡本身就是道具 |

核实：画幅、摄影、甩镜和配乐乐器已对照 Slate、No Film School、Slant、Fast Company 与 Wikipedia 的资料。《布达佩斯大饭店》分几个 Part、各章标题是什么，以及《天才一族》的书页式章节，凭观片印象写成，**未核实**。

**不照搬**：不做粉色饭店外立面、甜点盒、紫色门童制服、童子军营地；不模仿演员造型，不用原片的字体和片名页；也不要每一镜都是粉色，粉只是其中一章的颜色。

## 视觉语法

- **色板**：每章一套三色，全片 3–4 套轮换。

  | 套色 | 底 | 主体 | 点缀 |
  |---|---|---|---|
  | 糖霜 | `#F3C6CF` 粉 | `#B9A7D8` 薰衣草 | `#C8374A` 胭脂红 |
  | 薄荷 | `#CFE8DA` 薄荷 | `#F4E2A1` 黄油黄 | `#2F6B5A` 松绿 |
  | 卡其 | `#E8D6A8` 卡其 | `#D98B4A` 杏橙 | `#4B6A8C` 褪色蓝 |

  全片常量：字和线用 `#2B2D5C` 墨蓝，不用黑；卡片底用 `#F7F1E3` 象牙。每套色只在它那一章出现。章节字卡用象牙底、墨蓝字，再用该章的点缀色画一条细线。
- **字体**：
  - 章节标签用 Futura Medium，全大写，字距 0.18em（如 "CHAPTER TWO"）；
  - 标题用 Futura Bold，84–120 px；
  - 叙述和说明用 Baskerville Regular，44–52 px，不用斜体；
  - 中文标题用 Songti SC Bold，叙述用 Songti SC Regular。

  所有文字居中对齐。
- **构图**：
  - 主体中心落在 x = 960 ± 4 px，画面左右镜像对称；小道具可以不对称，轮廓必须对称；
  - 机位与后墙垂直（planimetric），人物和物件取正面或正侧面；
  - 前、中、后三层平行排列，画面里没有透视斜线；
  - 俯拍插入：物件平铺在桌面上，正上方 90° 拍，按网格排列。
- **画幅也有含义**（可选）：回忆和过去用 1.37:1，1080p 下左右各留 190 px；现在用 1.85:1 或完整的 16:9。边框用象牙色，不用黑边。
- **质感**：grain，强度 0.06。以平涂色块为主，只在模型或布景感的场景加极轻的纸纹。不加暗角，不做景深模糊，从前到后全部清楚。

## 运动语法

帧数一律按 30 fps 计。

- **缓动**：
  - 镜头横移用 `cubic-bezier(0.45,0,0.55,1)`（inOutQuad）：起步和停止都干脆，中段接近匀速，像轨道车；
  - 甩镜用 `cubic-bezier(0.7,0,0.3,1)`，9 帧，中间 3 帧是横向运动模糊，模糊长度 ≥ 画面宽度的 15%；
  - 物件入画用 `cubic-bezier(0.33,1,0.68,1)`，10 帧。

  不用 bounce。角色和道具可以"一拍二"，做出定格动画的感觉。
- **时长**：一个对称画面至少停 2 s；每 2.5 s 一个新事件，比如道具出现、人物转头、镜头横移到下一格；章节字卡停 2.5 s（风格节拍，像翻过一页书；比读时底线长）。
- **转场**（全片只用这 3 种）：
  - 甩镜（whip pan），左右交替；在模糊最大的那一帧切，下一场从同方向的模糊中停下；
  - 直切到章节字卡，再直切回来；
  - 90° 横摇到同一空间的另一面墙，新画面同样居中对称。
- **镜头**：以横移、横摇、竖摇为主，像沿着玩偶屋的剖面走。推拉只在每章开头用一次慢推（3 s 内 1.00 → 1.06）。禁止手持。
- **文字动画**：字卡整张直切出现；叙述文字逐行 stagger，每行间隔 150 ms，淡入 8 帧，不逐字出。

## 声音语法

- **配乐**：室内民谣 / 巴洛克小品，拨弦乐器的颤音、钟琴、羽管键琴，120 BPM，G 大调，2/4 拍的行进感。`bin/vh music` 的做法（`parts`）：
  - `balalaika` 主奏，`tremolo` 11 Hz，`tremolo_min` 0.45 拍（八分音符也轮两下），另一把低几 dB 的巴拉莱卡轮指和弦垫底；
  - `cimbalom` 用 `figure: arp-up`（`rate` 16，`damp`）；
  - `figure: oompah` 分给 `pizzicato`（`role: bass`）和 `harpsichord`（`role: chord`，`len` 0.3，断奏）；
  - `glockenspiel` 只在章节字卡上敲，新的一章加 `snare` 滚奏。

  样片的 `score.json` 就是这么写的。

  每一章多加一件乐器，像乐器介绍曲那样一层层叠上去。
- **音效**：
  - 0.25–0.35 s 的 `whoosh` 配每次甩镜，`pan` 跟甩镜方向走；
  - `ding` 配章节字卡；
  - `click` / `pop` 配道具落位。
- **声画关系**：甩镜 whoosh 的峰值对准切点那一帧。章节字卡出现时音乐换段，新乐器进来，不留静音。
- **样片的转场音效**：`air` 加 `whip`：大幕拉开、窗帘打开是两口气（0.4 / 0.6 s）；4.15 s 甩镜到下一章是一声 whip（0.3 s，声像左到右）；配乐里的 `balalaika` 和 `cimbalom` 换成物理建模的 `balalaika_pm`（主奏 −7.6 dB，和声 −2.6 dB）和 `cimbalom_pm`（−11.4 dB）。

## 适合与不适合

- **适合**：02 知识短片（分步骤、分章节的讲解）；03 生活方式、食品、酒店、文创品牌；07 手绘和角色小片的画面编排；人物小传，"说明书式"的幽默。
- **不适合**：严肃新闻、灾难、悲伤题材；数据密集的图表段落；需要写实人物的内容。
- **容易被误用成**：只学了粉色和居中，节奏却是软绵绵的慢 crossfade。这个风格的节奏其实很干脆。

## 禁止项

1. 主体偏离中线超过 4 px，而且不是刻意的。
2. crossfade、变焦推拉、手持晃动。
3. 纯黑的字或边框；一章里混进另一章的颜色。
4. 斜体、手写体，或同一行里衬线和无衬线混排。
5. 景深模糊、暗角、光晕。画面应该从前到后都清楚。
6. 模仿原片布景（粉色饭店、甜点盒、制服）或演员造型。

## Prompt 块

```text
Visual style: symmetrical pastel storybook. Every frame is centred on the vertical axis (subject at x = 960 ± 4 px) and staged planimetrically: camera square to the back wall, layers parallel, no diagonal perspective, deep focus. Each chapter owns one pastel trio (e.g. pink #F3C6CF / lavender #B9A7D8 / carmine #C8374A, or mint #CFE8DA / butter #F4E2A1 / pine #2F6B5A), with ink navy #2B2D5C for all type and lines and ivory #F7F1E3 for cards. Every chapter opens with a centred title card: a small tracked-caps label in a geometric sans (Futura Medium), a bold title, and a thin rule in the chapter's accent colour. Motion is crisp: lateral dolly moves with short eased ramps, 9-frame whip pans that cut on the blur and land on another centred tableau, 90-degree pans to the next wall, and overhead inserts of objects laid out on a grid. No crossfades, no handheld, no bounce. Optional: memories in a 1.37:1 pillarbox with ivory bars. Sound: 120 BPM G-major chamber folk with plucked tremolo strings and glockenspiel, one new instrument per chapter, a whoosh on every whip pan and a bell on every chapter card.
```

## 引擎做法

- 首选 HyperFrames：DOM / SVG 布景 + GSAP 时间线。布景是平面的，按"层 × 深度"排列；横移时各层同速移动（平面剖面，不做视差），最多给最前景 1.1× 视差。
- **对称**：所有布局函数都以 `cx = W / 2` 为基准，用 `mirror(el)` 生成对侧。自查脚本把画面左右翻转后与原图做差，主体区域的平均差 ≤ 6%。
- **甩镜**：9 帧里的 x 位移按 inOutCubic 走；第 3–7 帧叠加横向运动模糊（8–12 个子采样取平均，或只在 x 方向用 SVG `feGaussianBlur`）；切点在第 5 帧。
- **章节字卡**：做成一个组件 `chapterCard({n, title, accent})`：象牙底、墨蓝字、双线框（外线 3 px、内线 1 px，相距 12 px）。
- **画幅切换**：外层容器用 `clip-path: inset(0 190px)`，在切点上直接切换，不做动画。

## 自查重点

- 左右翻转差分：每个非运动帧的主体区域都对称。
- 1 fps 联系表：每章只用它那套颜色，章与章之间颜色切换清楚。
- 甩镜 strip：切点前后运动方向一致、模糊方向一致，落点画面同样居中。
- 字卡停留 ≥ 2.5 s（风格节拍，见上面的"时长"），标签字号 ≥ 44 px。
- 声音：每个 whoosh 的峰值与甩镜切点同帧（±1 帧）。

## 相关资源

- lemo-opuscar 里最接近的是 `paper-popup`（立体书舞台）和 `art-deco`（中轴构图、沿中轴开合的转场），见 `references/repos/lemo-opuscar/styles/<slug>/STYLE.md`（LemoLab，CC BY 4.0）。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 里的 Velvet Standard（对称、居中、长停留）可以对照，但它慢悠悠的滑行节奏不适合本风格。
- `video-types/02-knowledge-short.md`、`video-types/07-hand-drawn.md`、`playbook/03-motion-design.md` §6。
