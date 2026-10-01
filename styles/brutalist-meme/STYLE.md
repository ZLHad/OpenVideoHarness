# 野兽派梗 · brutalist-meme

系统字、裸网格、原生截图、每拍一刀的硬切：互联网原住民的快剪语法，丑得有体系，笑点一秒内落地。这是 `video-types/08-brutalist-meme.md` 的风格预设版本，数值与该类型文档一致，冲突时以类型文档为准。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

样片实况：所有"截图"都是本仓库的真实素材，不画假界面。第 0 帧就是全屏的原始终端，`bin/vh style list` 的真实输出按 12 fps 滚出；0.4 s 在拍上硬切到其中一行（brutalist-meme），放大到 96 px，用强调色粗暴地划一道线。0.8 s 硬切到标题，12 栏网格露在外面；1.6 s 再硬切出中文。2.0 / 2.2 / 2.4 s 三个直角窗口按八分音符砸进来：`templates/BRIEF.md` 的原文（大纲）、从 `styles/gallery.jpg` 裁下再压成 q28 的烂 JPEG（分镜）、这支样片早先一次 `render.sh` 的真实输出逐行打出（初版，斜 3° 破网格）。标签故意混排 Times New Roman 斜体、Arial Black 和 Menlo。2.0 / 2.4 / 2.8 s 一个手画的鼠标箭头跳到下一个窗口，每拍一次 115% 的 punch-in；3.2 s 推近后定格屏息到 3.6 s，3.6 s 橙色徒手框圈住 DRAFT，写上 "← SHIP IT"；4.0 s 5 帧 glitch 硬切到出血的大字，4.2 和 4.4 s 再各踩一次 punch-in。截图里的字只要求认得出是什么（`TASTE_CHECKLIST` #5）。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《The Face》杂志 | 1981–1986 · 艺术指导 Neville Brody | 字体就是图形：每期变形的刊头、倾斜和出框的排版、构成主义式的粗重对比 |
| "It's Supposed to Look Like Shit: The Internet Ugly Aesthetic"（Journal of Visual Culture 13(3)） | 2014 · Nick Douglas | 刻意的丑是一种方言：鼠标徒手画、粗糙拼贴、人为的故障、错字；业余感本身传达"这是自己人做的" |
| brutalistwebsites.com | 2014 · Pascal Deville | 系统默认字体、裸露的网格和边框、零装饰；把"不讨好"当成态度 |

**不照搬**：不复刻《The Face》的刊头和具体版面；不直接用有版权的梗图原图；真实推文、聊天截图里的他人头像和昵称要重做或打码；不用任何真实品牌 logo。

## 视觉语法

- **色板**（与 08 类型文档一致）：
  - 底 `#111111`、字 `#F0F0F0`；
  - 警报橙红 `#D4501E`：唯一的强调色，只用于包袱处的标注框、箭头和一个关键词；
  - 网格线 `#2A2A2A`，占位灰 `#5C5C5C`，截图外框灰 `#8A8A8A`。
- **字体**：
  - 标签：`Space Mono` 大写，28–36px，字距 +0.08em；本机没有时退回 `Menlo`；
  - 主标题：`Space Grotesk` Bold，120–220px，字距 −0.03em；退回 `Helvetica Neue` Bold；
  - 中文：`PingFang SC` Semibold → `Hiragino Sans GB` W6；中文标签不做全大写，改用 `【】` 括住；
  - Space Mono、Space Grotesk 是 OFL 字体，本机未装，放进项目的 `assets/fonts/`。
  - 样片实际用字：`Space Grotesk` 和 `Space Mono` 本机没有，样片实际回落为 `Helvetica Neue` Bold 150px（英文）和 `Menlo` Bold（标签）；中文 `PingFang SC` Semibold 80px / 52px；三元素的英文标签故意混排系统字体：`Times New Roman` Bold Italic 42px、`Arial Black` 34px、`Menlo` Bold 36px；截图里的终端和编辑器文字用 `Menlo` 16–40px，0.4 s 放大的那一行 96px。
- **构图**：
  - 先建一个看得见的 12 栏网格（1px `#2A2A2A` 线，1920 宽时边距 96px），所有元素先吸附到网格；
  - 再故意打破：每个画面只打破一处（一张截图旋转 2–4°、一个大字出框 10–20%、一块元素压住网格线）；
  - 截图按原生分辨率放，保留 UI 外框；放大只用整数倍并用最近邻采样，不做平滑缩放；
  - 所有角都是 0px，没有投影、没有模糊、没有渐变；
  - 竖屏 1080×1350 时，关键内容留在 x 90–990。
- **质感**：默认无（none）。Internet Ugly 的"脏"来自素材本身：鼠绘圈、截图压缩痕、错位拼贴，不靠滤镜。glitch 只在 1–2 个段落分界处出现。

## 运动语法

帧数按 30 fps 计。

- **缓动**：
  - 文字和元素出现用 `steps(6, end)`，退出用 `steps(4, end)`，都是阶梯，不是平滑曲线；
  - 全片只有一次平滑缓动：高潮处一个 1.5–2 s 的慢推，easeInOutCubic `cubic-bezier(0.65,0,0.35,1)`，用反差制造重量；
  - 不用 spring，不用 bounce。
- **时长**：
  - 硬切每 0.5–1.5 s 一次，落在拍子上；
  - punch-in：切点后 2 帧内从 100% 跳到 115%；
  - 每个画面至少停 0.5 s；每 1 s 必须有新东西。
- **笑点时序**：铺垫 1–2 s → 0.4 s 屏息（画面定住；鼓组撤掉，只留低音或底噪垫着，不是数字静音）→ 包袱：定格 + `#D4501E` 标注框用 `steps(3)` 画出 + 音效。每个笑点 1 s 内看懂。
- **转场**：全片只用三种：硬切（默认，语义是"打断、惊醒"）、punch-in 切（切的同时放大到 115%）、glitch（全片最多 2 次，每次 4–6 帧）。
- **镜头**：固定（locked）。所有运动来自剪辑和 punch-in，不做漂移。
- **文字动画**：打字机（typewriter），`steps(4–8)` 逐字出现；大写等宽标签可以带一个方块光标，闪烁周期 0.5 s（按 t 计算，不用 CSS 动画）。

## 声音语法

- **配乐**：phonk / trap 梗片节奏，用 `bin/vh music` 的乐器声部（`parts`）写，`bpm: 120`（一拍 0.5 s，正好对上 0.5–1.5 s 的切点节奏），`key: "E"`，`mode: "minor"`。签名是两件：失真的 808（`sub808`，`drive` 3–4，连奏的音之间滑音，上一个八度或往下滑）和一条 Memphis 式的牛铃 riff（`cowbell` 带音高，3-3-2 切分，带一点弗里几亚的 F，加短回声 `delay`）。鼓是 trap：半速的军鼓（`trap_snare` 叠一记硬 `clap`，每 4 拍一记），八分音符的 `trap_hat` 夹着 32 分和三连音滚奏。干、削顶：`space: dry`，总线 `drive` 1.3，不加混响。包袱前的屏息只撤鼓和牛铃，808 往下滑的长音和一层暗的 `drone` 垫着。
- **音效**：定格 `shutter`、错误 `error`、弹出 `pop`、点击 `click`、打字 `typing`、段落分界 `glitch`、包袱 `impact`。每个音效对应画面上一个动作，不做装饰性铺底。
- **声画关系**：卡点最密的一种风格：每个切点、每个 punch-in 都在拍上（±1 帧）。屏息是笑点的一部分：包袱前 0.4 s 撤掉鼓组、音量降 10 dB 以上，但保留底垫；`TASTE_CHECKLIST` #18 不允许片中出现数字静音。08 类型文档写的是"0.4 秒静默"，按新规则理解为屏息。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：样片按 150 BPM 走（每个切点都在 0.4 s 的格子上），E 小调，小节排成 1 + 1 + 3 + 3 + 1 + 1 + 3 拍。0 s 起 808 和牛铃 riff 同时进，hats 走八分音符；0.4 s 硬切处 808 重打一下，0.6 s 滑上一个八度；0.8 s 标题切入是第一记半速军鼓加 clap；2.0–3.2 s 三个窗口砸进来时 808 换到 C（VI），牛铃第二遍 riff 走到 A–G–F–E，2.4 s 第二记军鼓，2.8 s 808 从 C 滑到 G，hats 用三连音滚奏冲进定格；3.2–3.6 s 屏息：鼓和牛铃撤掉，只剩 808 从 E2 往下滑一个八度（压得很低）、牛铃回声的尾巴和一层暗的 `drone`，比前后低约 11 dB；3.6 s 包袱时军鼓、clap、808 和牛铃一起砸回来；4.0 s 故障处第四记军鼓，808 结巴似地连打三下，hats 满格滚奏，4.2 / 4.4 s 两次 punch-in 都落在牛铃和 808 上。拟音（`events.json`）：0.4 / 0.8 / 1.6 s 三处硬切和 4.0 s 故障转场各一声 glitch，其余每个 punch-in（2.0 2.2 2.4 2.8 3.2 3.6 4.2 4.4 s）一声 `click`，3.27 s 定格一声 `shutter`。glitch 用 `sfx/glitch_cut.wav`：照内置 `glitch` 的做法合成（方波在 80/160/640/1280 Hz 间每 12.5 ms 跳一次，10 ms 随机门控，指数衰减），但方波边沿和门控开合各有 1–2 ms 的斜坡。内置版本的硬门控会在起音后 45–130 ms 留下台阶，qa 把它们报成 click；这一版起音就落在切点上，不需要提前。

## 适合与不适合

- 适合：`08` 梗视频、观点快剪、"这周 AI 圈发生了什么"；`02` 带笑点的科技短视频；`03` 面向开发者的产品吐槽式对比。
- 不适合：温情、治愈、需要氛围的片子；长时间的原理讲解。没有笑点时硬套，就只剩"随机的混乱"。

## 禁止项

- 披着野兽派外衣的圆角玻璃卡片：有圆角、投影、毛玻璃就不是这个风格；
- 没有网格的"破坏"：看不见秩序，就看不出打破；没有笑点的随机混乱；
- 满屏 glitch，或者每个切点都加故障；
- 有版权的梗图原图、真实品牌 logo、截图里他人的头像和昵称；
- 超过 1 秒才能看懂的笑点，或包袱前没有屏息；也不能把屏息做成数字静音；
- 平滑缓动到处都是：全片只允许高潮处那一次慢推。

## Prompt 块

```text
STYLE: internet-brutalist tech cut. #F0F0F0 on #111111, one alarm accent #D4501E used only for punchline annotations. A visible 12-column grid (1px #2A2A2A lines, 96px margins); everything snaps to it, then exactly one element per frame breaks it (a screenshot tilted 2–4°, a word bleeding off the edge). 0px corners, no shadows, no blur, no gradients.
Caps monospace labels (Space Mono, 28–36px, +0.08em) and one heavy grotesk (Space Grotesk Bold, 120–220px, −0.03em). Raw screenshots at native resolution with their UI chrome, integer scaling only, nearest-neighbour.
Motion: hard cuts every 0.5–1.5s on the beat; a 2-frame punch-in to 115% on cuts; text appears with steps(6) like a typewriter; freeze-frame plus a hand-drawn #D4501E box on every punchline; glitch at no more than two section breaks. The only smooth ease in the whole piece is one slow push at the climax.
Comedy timing: setup 1–2s, a 0.4s held breath (drums out, a low bed stays; never digital silence), then the hit with a sound effect; every joke reads in under one second.
Sound: 120 BPM E-minor phonk / trap: a distorted 808 with glides, a Memphis cowbell riff, rolling trap hats, a half-time snare with a hard clap, dry and clipped; shutter, error, pop and impact effects tied one-to-one to on-screen actions. Recreate meme formats from scratch; no copyrighted images, no real logos, no real people's avatars or handles.
```

## 引擎做法

- **首选 HyperFrames**，从它的 Deconstructed 预设出发（`references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 第 3 节）。注意 Deconstructed 预设里的 `back.out(2.5)` 和 `elastic.out` 与本预设冲突：按 08 类型文档，入场改成阶梯，不用回弹。
- **阶梯**：`p_step = Math.floor(p·N) / N`，N = 4–8，p 由 t 算出；不用 CSS 的 `steps()` 动画和 `@keyframes`（硬规则 1）。
- **切点表**：写一张 `cuts = [{t, shot, punch}]`，t 全部取自 `music.beats.json` 的拍点；punch-in 在切点后 2 帧内 `scale = 1.15`，之后保持或回到 1。
- **标注框**：用 3–4 段折线模拟鼠标徒手框，每段端点加 `hash` 抖动 ±6px，线宽 6px，`steps(3)` 画出。
- **截图**：`image-rendering: pixelated`，只做整数倍缩放；需要打码时用 16px 马赛克块，不用高斯模糊。
- 竖屏遵守平台遮挡（`playbook/03-motion-design.md` 第 5 节）。

## 自查重点

- 对照 `music.beats.json`：每个切点、每个 punch-in 是否都在拍上（±1 帧）；
- 每个包袱前是否有 0.4 s 的画面定住加屏息（鼓组撤掉、底垫还在）；
- 把每个笑点的片段单独放 1 秒：看得懂吗？
- 截一帧，网格线还看得见吗？这一帧打破网格的元素是不是只有一个；
- glitch 次数 ≤ 2；有没有圆角、投影、渐变混进来；
- 素材台账：每张截图、每个梗格式的来源和处理方式（重做、打码）。

## 相关资源

- `video-types/08-brutalist-meme.md`：本预设的上位规则，配色、字体、节奏、笑点时序都从这里来。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 第 3 节 Deconstructed、第 4 节 Maximalist Type（Apache-2.0）。
- lemo-opuscar 没有直接对应的风格；相近的是 `references/repos/lemo-opuscar/styles/halftone-dossier/STYLE.md`（半调档案风）、`microgame/`（越来越快的微游戏快闪）、`swiss-motion/`（网格与信号红），均为 CC BY 4.0（LemoLab）。
- `references/repos/viral-video-decomposer/skill/SKILL.md`（MIT）：拆爆款机制，只借结构。
- `cases/mv-claude-pop.md`、`playbook/03-motion-design.md`、`playbook/04-audio.md`。
