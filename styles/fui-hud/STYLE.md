# 电影界面 HUD · fui-hud

一句话：电影里的虚构界面（FUI）：点阵网格、发丝线框、等宽数字读数、示意图叠层，而且每一个读数都是真数据。适合讲系统、任务、监测、航天与工程、AI agent 的"内部视角"，以及任何需要"把过程可视化"的段落。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 1 帧起，FRAME 计数在点阵中央放大跑数，0.65–0.95 s 飞回右上角，面板框随即画出。标题逐字解码。一道扫描线揭出样片自己的内容规格（四条甘特条：establish / title / motif / outro），播放头就是 t。下方是轨迹 schematic：三个航点在 2.0 / 2.2 / 2.4 s 依次启动（先画圆，再出数据），每个带线框图标和它真实的启动时刻；初版的图标是一格胶片，不用播放键。橙色括号锁定初版航点：2 Hz 闪两下，这时配乐只剩 drone。2.8 和 3.2 s 各一道扫描线扫过，读数跟着闪；3.6 s 标记点锁定。镜头慢慢漂移：点阵 0.9×、HUD 1.0×、一层淡淡的准星前景 1.1×，形成视差。4.0 s 初版航点的括号框展开成全屏结束卡。实际字体：DIN Condensed Bold、Menlo（SF Mono 回落）、PingFang SC Medium。配乐 150 BPM：`pad` drone + 16 分音符 `arp`，2.4–3.2 s 告警段只留 `pad`。拟音：计数用 tick，航点启动用 toggle，解码用 typing，扫描线用 swish_rev，3.6 s 锁定用 success，展开用 whoosh。拟音的落点写在 swatch.js 的 `FOLEY` 常量里，`events.json` 由它生成。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《火星救援》*The Martian* 屏幕图形 | 2015 · 导演 Ridley Scott；屏幕图形 Territory Studio | 约 400 个屏幕，和 NASA、ESA 的专家核对过；每块屏"在情境里都有真实用途"。不同场景配色不同：飞船是黑底上的蓝、绿、白，头盔和臂载电脑是黑底上的白和橙，为的是看得清 |
| 《遗落战境》*Oblivion* 界面与 HUD | 2013 · 导演 Joseph Kosinski；界面设计 GMUNK（Bradley G. Munkowitz）等 | 所有元素都挂在一张点阵网格上，形成统一的系统；功能优先、极简、统一色板 |
| 《银翼杀手 2049》屏幕图形 | 2017 · Territory Studio | 老化的技术：扭曲、重影、色彩衰减、故障，用来暗示设备"过时"了。质感在为叙事服务 |
| "FUI" 这个词 | 2000 年代初 · Mark Coleran（通常认为这个词由他提出，他为当时一批电影做了屏幕图形） | 虚构界面的第一原则：让观众一秒内看懂"发生了什么"，而不是让它真的能用 |

核实：Territory Studio 的两项来自其官网项目页；*Oblivion* 的点阵网格与分工来自界面设计者本人的官网和 AWN 的报道。FUI 一词的提出者来自访谈和博客等二手来源，他具体参与了哪些影片，本次没有查到一手资料，**未核实**。

**不照搬**：不做 NASA、ESA 的标志和任务徽章，不画原片飞船和探测车的示意图，不做面罩式的钢铁侠 HUD，不抄原片的界面布局；也不堆 "SYSTEM ONLINE"、"ACCESS GRANTED" 这类假文字。

## 视觉语法

- **色板**：

  | token | hex | 语义 |
  |---|---|---|
  | bg 深底 | `#05080A` | 偏蓝的黑，不用 `#000` |
  | fg 冷白 | `#CFE7EA` | 主读数、主线条 |
  | accent 警示橙 | `#FF8A2B` | 只给"此刻最重要的那个东西"：告警、目标、正在变化的数 |
  | extra 暗青 | `#4E8C8A` | 次级线条、刻度 |
  | extra 网格点 | `#1C2A2E` | 点阵 |
  | extra 失败红 | `#E5484D` | 只用于失败状态，不和橙同时出现 |

  线条亮度分三级：主线 100%，次线 55%，纹理 25%。
- **字体**：
  - 数字和数据一律等宽：SF Mono → Menlo，`tabular-nums`；
  - 标签用 DIN Condensed Bold（fallback Avenir Next Condensed Demi Bold），全大写，字距 0.12em；
  - 主读数 120–200 px；标签 30–36 px，属于纹理级，不要求观众读完；需要读的说明 ≥ 44 px；
  - 中文标签用 PingFang SC Medium。

  这台机器上 SF Mono 只在 Terminal.app 的包里，没有注册成系统字体。要用它，得用 `@font-face { src: url(...) }` 指向字体文件，或者把文件拷进项目的 `assets/fonts/`，否则会落到 Menlo。
- **网格**：24 px 点阵（点径 2 px，颜色 `#1C2A2E`）铺满画面，所有面板、刻度和示意图都对齐点阵。
- **层级**：一个主读数（大数字或状态），2–4 个次级面板，背景里是纹理级的数据（滚动的数值列、刻度）。每个面板都必须回答一个问题，比如"现在是多少""往哪去""还剩多久"；答不出来的就删掉。
- **线**：主线 1.5 px，次线 1 px。面板只有装着数据时才加 L 形角标（12 px）。示意图用线框（wireframe）、剖面和轨迹线，不做实体渲染。
- **质感**：scanline，强度 0.08（2 px 一个周期，只在暗部看得见）；轻微 bloom，阈值设高，只让橙色告警发光。可选一档"老化"：3 px 重影加色彩衰减，用来表示旧系统。

## 运动语法

帧数一律按 30 fps 计。

- **缓动**：面板和数值进场用 `cubic-bezier(0.19,1,0.22,1)`（easeOutExpo），8 帧；退场用 `cubic-bezier(0.95,0.05,0.8,0.04)`（easeInExpo），6 帧。线的绘制、扫描和进度一律线性。
- **启动**（签名）：面板分两步出现。先画出框线：从一个角点向两边生长，线性，6 帧；再往框里填数据，4 帧。多个面板之间错开 3 帧，整组不超过 0.5 s。
- **数字**：计数用 `steps`，每帧更新末位，然后从右往左按位锁定。decode 乱码不超过 0.3 s（9 帧），定住之后才算"可读"。
- **扫描**：一条扫描线用 1.2–2 s 扫过示意图，扫过之处的元素亮度从 25% 升到 100%。
- **告警**：橙色的括号或框以 2 Hz 闪 2 次，然后常亮，不持续闪。
- **时长**：每 1.5 s 一个新事件（新读数、新面板或状态变化）；主读数定住后至少停 1.5 s。
- **转场**（全片只用这 3 种）：
  - 面板展开：一个面板放大到全屏，成为下一镜；
  - 扫描擦除：扫描线扫过之后就是下一个画面；
  - 硬切。
- **镜头**：以固定为主；可以做轻微的 2.5D 视差（最前层 1.1×）。不甩镜，不手持。
- **文字动画**：decode。字符用带种子的 `hash(i, frame)` 循环，9 帧内从左到右依次锁定。

## 声音语法

- **配乐**：冷的电子 drone 加脉冲，100 BPM，C 小调。`bin/vh music` 的做法：
  - `pad` 低通，energy 0.3；
  - `arp` 走 16 分音符，energy 0.4–0.6，像数据流；
  - `bass` 垫底，紧张段再加 `hats`。
- **音效**：一个家族，全部调到同一个调。
  - `tick` 配数字锁定；
  - `click` 配面板框线闭合；
  - `toggle` 配状态切换；
  - `typing` 配 decode；
  - `error` 只配失败状态，`success` 配最终确认；
  - `glitch` 只在"老化 / 故障"档里用。
- **声画关系**：每个读数定住的那一帧都有一声 tick。UI 音效的声像跟着面板在画面上的横向位置走（`bin/vh sfx place` 的 `pan` 字段）。告警时音乐减半，只留 drone。

## 适合与不适合

- **适合**：05 数据故事（实时指标、监测）；03 科技产品和 AI agent 的发布片；02 航天与工程类科普；06 论文讲解里系统架构和实验过程的段落。
- **不适合**：温情叙事、人文历史、手作品牌；没有真实数据可显示的主题（会退化成装饰）。
- **容易被误用成**：满屏假数字、四角取景框、毫无意义的旋转圆环，也就是 TASTE #20 点名的"通用 AI 装饰"；再加上青色霓虹和暗底发光，正是本仓库最想摆脱的那种单一口味。

## 禁止项

1. 任何不承载真实信息的读数、滚动乱码、装饰性雷达圈（TASTE #20）。
2. 超过一个饱和强调色；把橙色用在装饰上。
3. 满屏发光、霓虹青紫渐变、玻璃拟态。
4. decode 超过 0.3 s，或者需要读的字在读的时候还在跳。
5. 用比例字体显示数字，导致数字宽度跳动。
6. 真实机构的标志、任务徽章、原片的界面布局。

## Prompt 块

```text
Visual style: a fictional film user interface (FUI) built from real data. Blue-black ground #05080A with a 24 px dot grid; cool white #CFE7EA hairlines and readouts in three brightness levels; one alert orange #FF8A2B reserved for the single thing that matters right now; failure red only for failure. Hierarchy: one primary readout (a large tabular monospace number or a status), two to four secondary panels that each answer a question (how much, where, how long), and faint scrolling tertiary data as texture. Schematics are wireframes, sections and trajectories, revealed by a scan line. Motion: panels boot in two steps (the frame draws linearly from a corner in 6 frames, then the data fills in over 4), staggered 3 frames apart; numbers count in steps and lock digit by digit; text decodes for at most 9 frames and then holds; alerts blink twice at 2 Hz and stay on. Labels are condensed caps (DIN Condensed); numbers are monospace (SF Mono or Menlo) with tabular figures. Subtle scanlines, bloom only on orange. Transitions: a panel expanding to full frame, a scan-line wipe, hard cuts. Sound: a 100 BPM C-minor drone with a sixteenth-note arpeggio, and one tuned family of ticks and clicks panned to where each panel sits.
```

## 引擎做法

- 首选 HyperFrames：面板用 DOM / SVG 加 GSAP；示意图用 SVG path 加 `stroke-dashoffset` 画线；大量滚动数据放在 Canvas 层。
- **数据**：先写一份 `data.json`（真实数值、单位、来源），所有读数都从它取；自查时逐项对照 NOTES 里的出处。
- **计数与 decode**：写成纯函数 `digitsAt(value, t, lockTimes)`；乱码字符取 `CHARS[hash(i, frame) % N]`，不用 `Math.random`。
- **点阵**：一张 SVG `<pattern>`，或一张预渲染好的 Canvas 位图，全片复用。
- **扫描线揭示**：`mask` 用一条随 t 平移的线性渐变；被扫过的元素，opacity 取 `smoothstep(scanX - 40, scanX, x)`。
- **老化档**（可选）：重影 = 同一层偏移 3 px、opacity 0.25 再画一遍；色彩衰减用小角度的 `hue-rotate` 加降饱和。

## 自查重点

- 逐个面板问"它回答什么问题"，答不出就删（TASTE #20）。
- 主读数定住后可读 ≥ 1.5 s；decode 不超过 9 帧。
- 1 fps 联系表：橙色只出现在"此刻最重要"的元素上；画面里没有四角取景框。
- 所有数字都是 `tabular-nums`，逐帧 strip 里计数时数字宽度不跳。
- 数据与 `data.json` 以及 NOTES 里的出处一致，单位写对。

## 相关资源

- lemo-opuscar 里最接近的是 `blueprint`（按制图顺序画出的工程线）、`ascii-crt`（等宽网格里的真实字符）和 `dark-keynote`（界面即主角），见 `references/repos/lemo-opuscar/styles/<slug>/STYLE.md`（LemoLab，CC BY 4.0）。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 里的 Data Drift：本风格反对它的紫青粒子，但可以借"粒子汇成数字"的思路；同目录的 `data-in-motion.md`。
- `showcase/00-promo-launch-film/`（HUD 时间码母题）、`video-types/05-data-story.md`、`templates/TASTE_CHECKLIST.md` #20。
