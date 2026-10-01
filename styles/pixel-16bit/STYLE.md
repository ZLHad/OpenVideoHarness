# 16 位像素 · pixel-16bit

一句话：一台 16 位游戏机的画面：320 × 180 的逻辑画布按整数倍放大，最近邻、不平滑，固定 24 色，每个像素都落在整数格上；角色是一张张关键帧姿态，每秒换 10 次；信息装在对话窗里一个字一个字地打出来，转场靠硬件式的马赛克和亮度台阶。适合把一件事讲成"游戏里的一个系统"：升级、背包、存档、打怪、地图。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐和 `events.json` 拟音）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：前 3 帧是黑屏；0.1 s 起 8 × 8 的图块沿对角线从左下角装进画面，前沿那一排闪一帧金色，0.1 s 这一帧已经有超过 20% 的画面亮起来，0.37 s 装满。装载的同时镜头横移入场，从每帧约 11 px 减速到 0.9 s 的每帧 1 px，之后五层视差一直按整像素卷动：云、远山、树丘、地面、前景灌木。0.2–2.3 s 三只鸟排成一小队飞过天空（翅膀 7.5 fps），0.4 s 一颗流星划过。0.8 s 对话窗分 4 帧打开，英文标题每帧打两个字，中文每帧打一个字，1.57 s 打完，1.67 s 右下角出现上下跳的 ▼。母题是像素画师的三步：大纲（2.0 s，三个关键帧先是墨线草图，在白纸上按 12 fps 分 4 步描出来）→ 分镜（2.4 s，一张动作表上三个平涂的关键帧，每 0.1 s 蹦出一个）→ 初版（2.8 s，角色在世界里先白、再平涂、再上完阴影，接着开始走路）。站与站之间的路点用调色板循环点亮。2.8 s 起分镜表上的金框跟着角色当前的姿态走；3.2、3.6 s 角色各跳一下，闪一颗星。4.0 s 马赛克从 2 px 升到 16 px，亮度同时降 6 级；4.2 s 在最糊的时候世界停下、换成夜晚调色板，名字出现在同样的对话窗里；4.4 s 马赛克退回 1 px，角色继续往前走。实际字体：拉丁字母是 `swatch.js` 里手画的两套点阵字（15 行粗体标题字、5 × 7 大写字），中文是 Hiragino Sans GB W3 16 px 栅格化后二值化。配乐 150 BPM、F 大调，和声走 I–vi–IV–IV–V–I，是 SNES 式的 JRPG：0 s 图块装载时，`pulse` 主旋律（25% 占空比、延迟颤音）带着 240 ms 的乒乓硬件回声吹一句上行琶音 C–F–A–C；0.8 s 对话窗打开后只剩低通的铜管垫、二分音符的拨弦和三角波低音，把位置让给打字音；2.0 s 面板弹出时进 `chipkick`；2.4–2.8 s 只剩铜管垫，这是角色活过来之前的屏息；2.8 s 起主旋律、八分音符的拨弦分解和弦、按八分音符弹跳的三角波低音、`noise` 军鼓和镲一起进来（轻摇摆），4.0 s 在 I 级上解决，主旋律 F–C–A–F 落下来。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《Chrono Trigger》（超级任天堂） | 1995 · Square；角色设计鸟山明；音乐光田康典，植松伸夫、松枝贤子参与 | 几十像素高的小人靠剪影和一两处标志色被认出来；对话窗是一个能换皮肤的 UI 系统，字随声音一个个出来；整部游戏在几个年代之间穿梭，同一片大陆换一副面貌。本预设把最后这一点借成"同一张图换一套调色板" |
| 《The Legend of Zelda: A Link to the Past》 | 1991 · Nintendo EAD | 用硬件马赛克做转场：进出迷失森林、踩传送点、走漩涡水路时，画面先糊成大方块再清回来 |
| Super Famicom / SNES 的图像与声音硬件 | 1990（日本发售）· Nintendo | 马赛克寄存器（$2106，1–16 px，每块取左上角像素的颜色）；主亮度 16 级（INIDISP）；精灵每组 16 色，其中 1 色透明；15 位色（每通道 5 位）；声音是 8 个 BRR 采样声部加硬件回声 |
| 社区的"像素巫师"提示词 | @majidmanzarpour，发在 X 上 | 逻辑画布按最大整数倍放大并关掉平滑；固定约 24 色；精灵约 24 × 32；姿态参数量化到每秒 8–12 个；固定步长模拟。本预设把这些数字当社区经验值用 |

核实：
- Chrono Trigger 的发行年份、开发商和主创来自 Wikipedia 条目。它的小人大约多高（常见说法是 32 px 左右）只在论坛里看到过，**未核实**；设置里可以换对话窗样式也只见于攻略站和玩家讨论，**未核实**。
- A Link to the Past 的年份和开发商来自 Wikipedia。它在哪些场合用马赛克，来自 SnesLab 的 Mosaic 词条。
- 硬件参数来自 fullsnes 技术文档和 SnesLab；Super Famicom 1990-11-21 在日本发售，来自 Wikipedia。
- 像素巫师提示词的原帖（X）打不开，逐字内容是从 GitHub 上 `awesome-opus-5-5-video-prompts` 的转录里读到的；xilo 那篇转述文章没有找到。本仓库 `cases/opus55-gallery.md` 收的是 @zacxbt 用这段提示词做的衍生作品，不是提示词的出处。

**不照搬**：不用任何游戏里的角色、对话窗边框、字体、图标、曲子和音效。也不仿这些常见的做法：Final Fantasy 式的蓝色渐变窗、"PRESS START"、HP 数字、宝箱开启音。样片里的角色、两套拉丁点阵字、窗框和调色板都是这里自己画的。

## 视觉语法

- **分辨率**：逻辑画布 **320 × 180**，放大 ×6 到 1920 × 1080，交付时是 ×4 到 1280 × 720，两边都是整数倍。`render.sh` 会把 1920 缩到 1280，比例是 2/3，不是整数；但因为 320 × 4 = 1280，每个逻辑像素正好落进 4 × 4 个输出像素，缩放后格子依然对齐。像素画常用的 16:9 尺寸里，同时能整除 1080p 和 720p 的是 128 × 72、160 × 90、320 × 180、640 × 360。社区常用的 128 × 96 是 4:3，放进 16:9 时 1080 ÷ 96 不是整数，不要用。
- **色板**：全片固定 24 色，按 15 位色存（每通道 5 位，样片在 setup 里量化一遍）。任意一帧的颜色数不超过 24；亮度台阶和调色板切换都是"索引 → 索引"或"索引 → 亮度表"，不做混色。

  | 名字 | hex | 语义 |
  |---|---|---|
  | ink | `#0B0A1C` | 描边、最深的阴影；不用纯黑 |
  | night / indigo / violet / plum | `#1C1A3E` `#2C2A5E` `#4B3478` `#7B3F7E` | 夜空到黄昏的上层天色；对话窗底 |
  | rose / coral / amber / gold | `#B94F6E` `#E27659` `#F5A953` `#FFD984` | 地平线的暖色、云的受光面；标题字的渐变带、路点、光标 |
  | cream | `#FFF6DA` | 字、窗框、星、闪光 |
  | mist / slate | `#A8A6D0` `#6A6AA6` | 远山（空气透视）、动作表的透明棋盘格 |
  | pine / leaf / grass / lime | `#1F4A55` `#2E7A58` `#5DBB5E` `#B3E36F` | 树丘、前景灌木、草地的四级 |
  | soil / clay / tan | `#4A2C2C` `#7F4B3A` `#C4875A` | 土地、头发、靴子 |
  | skin / skinsh | `#F6C9A0` `#C98062` | 皮肤两级 |
  | red / wine | `#E0423D` `#862536` | 主角的围巾，也就是它的剪影标志；全片只有它用红 |
  | blue | `#3E6AD6` | 主角的上衣 |

- **渐变只用两种办法**：天空分 8 条色带，每条带的下缘有 3 行 2 × 2 Bayer 抖动（25%、50%、75%）；标题字按行分色带（奶油 → 金 → 琥珀 → 珊瑚）。不用任何连续渐变、透明度或模糊。
- **字体**：
  - 标题：15 行粗体点阵字，大写高 12 px、x 高 8 px、下伸 3 px，竖笔 2 px 宽，外面描一圈 8 邻域墨线；
  - 小字：5 × 7 大写点阵字，金色加墨线描边；
  - 中文：Hiragino Sans GB W3 16 px（回落 Heiti SC、PingFang SC）。在 setup 里用 CPU canvas 栅格化一次，覆盖率 ≥ 50% 的像素算墨；窗口里的标题加 1 px 墨色投影，天空上的站点标签描一圈墨线；折合 1080p 字高 96 px；
  - 同一画面里所有东西的像素大小必须一样：字不能按 2 倍画，精灵也不能按 2 倍画。
- **构图**：对话窗居中靠上（180 × 48）；两块面板一样大（84 × 38），三个站点的中心在 x = 74、176、262；地平线 y = 148；角色站在地平线上，面朝前进方向。文字留在 16 px 的安全边距里。
- **质感**：没有。不加扫描线、CRT 弯曲、颗粒、暗角、泛光。像素本身就是质感。

## 运动语法

帧数按 30 fps 计，所有坐标都是帧号的整数函数（一个能随意跳到任何一帧的"固定步长模拟"）。

- **姿态量化**：角色每秒换 10 个姿态，走路循环 A–P–B–P 四拍正好 0.4 s，等于 150 BPM 的一拍。落脚的 A、B 两帧身体低 1 px。闪光、光标一类的小动画 8–12 fps，光标上下跳 4 fps。
- **位移**：只走整像素。视差各层都跟同一个镜头函数走，速度是整数比：地面 1 px/帧、前景 2 px/帧、树丘 1/3、远山 1/6，云自己按 1/10 飘。镜头入场时的减速横移也是帧号的整数函数（先快后慢，取整）；结束画面里世界停住，角色每帧走 1 px。跳跃按逐帧表格走：−4, −8, −11, −12, −11, −8, −4 px。
- **缓动**：没有贝塞尔曲线，全部是台阶。窗口打开分 4 帧：一条线、1/3、2/3、全开。
- **时长**：窗口里的字打完以后至少停 1.8 s；每 1–1.5 s 要有一件新事；角色一旦出场就一直在动（走路或待机），画面里不许全部静止。
- **转场**（只用这 3 种）：
  - 马赛克：块大小每帧一档（2、4、6、8、12、16、16、12…2），最大 16 px（硬件上限），同时主亮度降 6 级；在最糊的那一帧换场景或换调色板，0.4 s 内退回 1 px；
  - 窗口开合：分 4 帧打开，关上时倒着走一遍；
  - 图块装载：8 × 8 的图块沿对角线出现，前沿闪一帧金色。只用在开场，或者"进入一个新地图"的时候。
- **镜头**：只有横向卷动，由视差表现。开场一次减速横移入场，结束时停住。镜头不推不拉、不旋转（Mode 7 式的旋转缩放要单独立项，不在这个预设里）。
- **文字动画**：签名是对话窗逐字打印。样片里英文每帧两个字（60 字/秒，相当于游戏设置里的"快速"），中文每帧一个字，打完出现 ▼。长句用每帧一个字。

## 声音语法

- **配乐**：16 位机的声音是 8 个采样声部加回声，不是 8 位机的方波。所以这里要的是短促的拨弦分解和弦，外加一条只在关键处出现的旋律。不要满屏的十六分音符"芯片乐乱弹"：分解和弦负责和声，旋律只在开场、揭晓那一小节和结尾出现。150 BPM（一拍 12 帧），大调。
  - `bin/vh music` 里的对应声部：主旋律是 `pulse`（25% 占空比、`vib` 颤音），和其他声部一样低通过（主旋律 5.5 kHz、拨弦 2.5 kHz、铜管 1.8 kHz、噪声鼓 6 kHz），因为 SNES 的采样经过高斯插值，本来就发闷；硬件回声用声部级的 `delay`：`beats` 0.6（150 BPM 下 240 ms，正好是 SNES 回声的上限）、`fb` 0.35、`lp` 2500、`pingpong`；"采样"的和声是 `brass`（`swell` 铜管垫）和 `pizzicato` 拨弦分解和弦；低音是低通过的 `triangle`；鼓是 `chipkick` 和 `noise`（`x` 军鼓、`o` 镲）。`space: dry`，回声就是空间；整体轻摇摆（`swing` 0.58），弹跳感来自它。
  - 样片 `score.json`：`meters` 为 2 + 3 + 1 + 1 + 3 + 3 拍，段落边界落在 0.8、2.0、2.4、2.8、4.0 s，和弦 I–vi–IV–IV–V–I：
    - `tilemap`：`pulse` 主旋律带回声吹一句上行琶音，拨弦、铜管垫、三角波低音一起进；
    - `window`：对话窗里只剩铜管垫（压低）、二分音符的拨弦和三角波低音，打字的 `tick` 都要听得见；
    - `panels`：拨弦回到八分音符，加 `chipkick`，铜管和弦一直延到下一段；
    - `breath`（2.4–2.8 s）：只剩这个铜管和弦，这是屏息；
    - `draft`（2.8–4.0 s）：全部进来，主旋律 C–B♭–A–G–C–E 停在导音上，三角波低音按八分音符弹根音–五度–八度–五度，`noise` 军鼓在第 2 拍；
    - `save`（4.0 s 起）：回到 I 级，主旋律 F–C–A–F 解决。
  - `master_db` 设为 −2：配乐比默认低 1 dB，对话窗里的文字音才压得住。
- **音效**：每个词或每两三个中文字一声 `tick`，当作文字音，每秒不超过 6 声；窗口和面板弹出用 `pop`；角色活过来时一声 `success`，相当于得到物品的小号角；跳跃用 `pop`；马赛克最糊的时候一声 `whoosh`，结束画面一声 `ding`。
- **声画关系**：姿态每 0.1 s 换一次，正好对齐十六分音符，所以分解和弦就是角色的脚步；屏息的那一拍画面照常在动，声音先退后进。
- **样片拟音**：`events.json` 共 19 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs pixel-16bit` 生成，落点和画面共用同一张帧号表，声像取发声物体的横坐标，`(2x/320 − 1)·0.7`：
  - 0.1 s：`boom` 和 `whoosh`，图块装载；
  - 0.5 s：`ding`，流星；
  - 0.8 s：`pop`，窗口打开；
  - 标题：英文前三个词、中文两处各一声 `tick`（相邻两声至少隔 3 帧），▼ 出现时一声 `click`；
  - 2.0、2.4 s：两个面板各一声 `pop`，第 2、3 个关键帧各一声 `tick`；
  - 2.8 s：`success`；
  - 3.2、3.6 s：各一声 `pop`；
  - 4.17 s：`whoosh`，马赛克最糊；4.4 s：`ding`，画面清回来。

## 适合与不适合

- **适合**：
  - 07 角色小短片，是手绘之外的另一种"有角色"的选择；
  - 08 科技梗，把一件事说成游戏系统；
  - 02 知识短视频，适合讲流程、升级、背包这类比喻；
  - 04 节奏明确的 MV。
- **不适合**：细密的数据图、大段正文、写实产品、奢侈品牌、需要细腻表情的特写（像素脸只有一两颗眼睛像素）。
- **容易被误用成**：用双线性放大的模糊像素；为了显得"复古"再叠一层 CRT 扫描线；满屏的方波乱弹；照搬某部名作的窗框和字体。

## 禁止项

1. 混合像素尺寸：同一画面里有的东西按 2 倍画，有的按 1 倍画。
2. 平滑缩放、非整数倍放大、亚像素位置，以及任何旋转或缩放精灵的做法。
3. 透明度淡入淡出、模糊、发光、连续渐变。明暗只靠亮度台阶和调色板切换。
4. 颜色不设上限。样片一帧最多 24 色，片子全程最多 32 色。
5. 套一层 CRT 或录像带滤镜。那是 `crt-terminal` 和 `synthwave-outrun` 的事。
6. 整片铺十六分音符的"芯片乐"，或者使用任何游戏的原曲、原音效。

## Prompt 块

```text
Visual style: a 16-bit console screen. Draw everything into an indexed 320×180 framebuffer and scale it by an integer factor with nearest-neighbour (×6 for 1080p, ×4 for 720p); no smoothing, no sub-pixel positions, no rotation or scaling of sprites, no alpha, blur or glow. One fixed palette of 24 colours stored as 15-bit colour; gradients are banded skies with 2×2 ordered-dither seams; brightness changes only in 16 hardware-style steps. Layered parallax scrolls at integer speeds (ground 1 px per frame, hills 1/3, far mountains 1/6, clouds 1/10, foreground 2). Characters are about 24×32 px with a 1-px dark outline, a clear silhouette and one signature colour; they change pose about 10 times a second (walk cycle contact–pass–contact–pass, the body one pixel lower on contact frames). Text lives in a message window with a cream-and-ink double border: it opens in four stepped frames, prints one character per frame, and shows a bobbing down-arrow when done; titles use a bold original bitmap font with a row-banded warm fill and an eight-neighbour dark outline; Chinese is a 16-px one-bit bitmap. Transitions: mosaic from 2 to 16 px with the brightness stepping down and a palette swap at the peak; stepped window open and close; an 8×8 tile-load sweep. Sound: a pulse-wave lead with a 240 ms ping-pong hardware echo, heard only at the load-in, the reveal and the end; sample-style plucked arpeggios and a muffled brass pad as harmony, a triangle-ish bass, noise drums with a light swing, a one-beat breath before the reveal, text blips per word, an item-get fanfare; no wall-to-wall chiptune noodling.
```

## 引擎做法

- **首选 HyperFrames + Canvas2D**，不需要 WebGL。做法：
  - 一个 `Uint8Array(320 × 180)` 当索引帧缓冲；所有绘制函数（矩形、精灵、1 位字形）都只写索引；
  - 输出时查一张"亮度 × 索引 → RGBA"的表，写进 `ImageData` 的 `Uint32Array` 视图；需要马赛克时按块取左上角那个像素的索引；
  - `putImageData` 到一张 320 × 180 的小 canvas，再 `imageSmoothingEnabled = false` 画到 1920 × 1080。
- **确定性**：每一帧都从清空帧缓冲开始，模块级只存 setup 算出的纯数据（字形、精灵、高度图、亮度表），滚动量、姿态、打字进度都是帧号的整数函数。小 canvas 用 `willReadFrequently: true`，强制走 CPU 光栅，中文字形在每个 worker 里都一样。
- **精灵**：用字符串画，一个字母对应一个调色板名字。三个关键帧共用头部，只换躯干和腿。"平涂版"用一张"阴影色 → 基础色"的映射表生成，"轮廓版"就是所有墨色像素，按绕中心的角度排序后分 4 步描出。
- **调色板切换**：一张 24 项的"索引 → 索引"表，只作用在背景层上；UI 和主角保持原来的调色板，相当于硬件上用了不同的调色板组。
- 实现要点：先画世界，再做调色板切换，然后画 UI 和精灵，再盖图块装载层，最后统一做马赛克和亮度。顺序反了，马赛克会漏掉一部分画面。

## 自查重点

- **格子要对**：
  - 从无损 PNG 序列里任取一帧，每个 6 × 6 块必须完全同色。样片 150 帧全部满足；
  - 一帧的颜色数不超过 24。样片最多 24 色，全片 145 个颜色值，多出来的都是马赛克时的亮度档。
- **交付尺寸下的清晰度**：从 `swatch.mp4`（1280 × 720）抽一帧，按 4 × 4 块统计。样片第 90 帧的结果：
  - 块内中间 2 × 2 的亮度极差中位数 0、p99 6.1/255；
  - 整块极差中位数 0.3、p90 12.0，只有高对比边缘的那一圈有 lanczos 振铃；
  - 99.98% 的像素离"自己或相邻逻辑像素的应有颜色"不超过 24/255。
  
  放大 2 倍看裁切图，边缘仍然是方的。
- **没有混合像素**：字、精灵、UI 在同一帧里用同样大的像素。
- 中文 16 px 字形不断笔、不糊成一团；在 360 px 宽的手机画面上"每一帧，都是代码。"仍然读得出来。
- 走路循环对拍：姿态每 3 帧换一次，每拍一个循环。屏息那一拍画面不停。
- `determinism.sh`：1 个 worker 和 3 个 worker 渲出的帧逐像素相同。

## 相关资源

- `references/repos/lemo-opuscar/styles/pixel-rpg/STYLE.md`（LemoLab，MIT）：同类风格的完整样片。这几条来自它：
  - 索引帧缓冲加查找表；
  - ×6 最近邻；
  - Bayer 抖动代替渐变；
  - "马赛克 + 在峰值换调色板"的转场；
  - 对话窗就是字幕；
  - 标题用行渐变加 8 邻域描边；
  - 角色要有剪影标志。
  
  本文改用自己画的角色、字体和调色板，把叙事换成"大纲 → 分镜 → 初版"的像素画师流程，并补上交付尺寸下整数倍的算法和实测。
- `cases/opus55-gallery.md`：像素巫师那一条。社区参数的出处和它的衍生作品，注意那一条的做法是固定步长模拟，不是 t 的纯函数，搬过来要改写。
- `video-types/07-hand-drawn.md`、`video-types/08-brutalist-meme.md`、`playbook/04-audio.md`。
- 外部：SnesLab 的 Mosaic 词条（<https://sneslab.net/wiki/Mosaic>）；fullsnes 技术文档（<https://problemkaputt.de/fullsnes.htm>）。
