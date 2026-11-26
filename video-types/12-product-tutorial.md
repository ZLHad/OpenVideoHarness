# 12 产品使用教程（操作用代码重做，不录屏）

**适用**：
- 3–8 分钟、有旁白的软件教程：怎么装、从哪里开始、一件事一步步怎么做成；命令行工具、Web App、桌面软件、开源项目都行；
- 产品介绍里讲"怎么用"的那一大段。

**不适用**：
- 10–90 秒、靠一句主张和几个功能拍撑起来的发布片：`03-product-promo.md`（里面的操作镜头照样可以用本篇的做法）；
- 剪人自己录的屏幕和口播：`09-editing-talking-head.md`；
- 10 分钟以上、讲原理的长片：`10-long-explainer.md`。

做法一句话：操作不是录下来的，是用代码重做的。界面能截到真图的就用真图，一小步一张，按时间放；光标、打字、镜头、标注另画在上面。镜头因此能推到任何一块还锐利，动作能落在旁白说出它的那个字上，改一句配音，画面跟着走。录屏做不到这几样：推近就糊，鼠标和字都小，等待只能剪掉。

这一类是从本仓库自己的一支 5 分 17 秒的使用教程提炼的（2026-11，1080p 和 4K）。下面带单位的数都是在那一支上量的，当起点用，第二支做完再校。

## 引擎

`bin/vh new tutorial <slug>` 建 canvas-film 项目（`ENGINE_README.md`）：镜头、字幕、章节挂在旁白的字上，光标点下去可以正好落在说出那个动作的字上。操作的画面用组件 `ui-stage`（`bin/vh components add <项目> ui-stage`）：终端、浏览器或应用的窗口，逐字打出、粘贴、打印的行（中文走拼音和候选框），跟着按下的键盘，光标和按压，步骤标签，真截图回放（镜头、聚光、光圈）。在 `film.html` 里加一行 `<script type="module">import * as S from "./components/ui-stage/component.js"; window.UISTAGE = S;</script>`，镜头的 `draw` 里 `UISTAGE.canvas(X, UISTAGE.state(P, t), P, pics)`。

截图的多少决定走哪条路：

- **截图不多**（几十张以内，或者按 2 倍以下截）：登记进 `FILM.images`（键就用状态名），引擎在 `ready` 时全部载好，`pics` 传 `IMG`，组件的 canvas 落笔直接画。
- **截图多**（逐字、逐格截下来上百张，3 倍的一张解码后约 46 MB）：canvas-film 的 `frame(t)` 是同步画的，图要事先全载入，放不下。那支片子是按页面合约自己写的页面（`engines/CONTRACT.md`，`frame(t)` 可以返回 Promise）：每帧只载这一帧要的两张（组件的 `needs(st)`），留十几张的缓存（组件的 `loader()`）。这样写，字幕用 `bin/vh captions <项目> --cards` 生成，词的时间自己从时间轴读。
- 界面要在三维里转（透视、倾斜、一块块飞来）时，用组件的 DOM 落笔，在画布上叠一层 DOM，同样是自己写页面。

90 秒以内的短教程也可以按 `03-product-promo.md` 用 HyperFrames（`bin/vh new promo`，两份类型文档都读），组件用 DOM 落笔。

## 工作流

1. **先把产品真走一遍，边走边记（关卡 ① 之前）**：在隔离的环境里真装、真用：新的 HOME 或一份干净的副本，演示数据另建一份，不碰人自己的账号和项目（那支片子的控制台是从 `git archive` 的副本起的，本机的项目一个都没露出来）。每一步的命令和输出、点了哪里、页面变成什么，记进 `NOTES.md` 的素材清单。出错的那一下也要真跑出来："缺 ffmpeg"那一句，是在去掉 ffmpeg 的 PATH 里真跑出来的。输出照抄，截短的地方用"…"标出。
2. **大纲按"看完能做"排**。下面是默认骨架，立意自带结构时以立意为准：
   1. 为什么要它：一个看得见的具体麻烦（那支是：想把第十秒那行字往上挪一挪，AI 却一遍遍整支重做），第一帧就在动，直接从问题开口，不先放一串成果；
   2. 装：一行命令，缺什么、怎么补；
   3. 入口：有几种用法，主界面分几块；
   4. 一个真案例从头走一遍：一步一镜，看得见人说了什么、它回了什么、界面怎么变；
   5. 这个产品真正不一样的那一步（那支是"说一句，改一个镜头"和"在 Studio 里审片"两段），给足时间；
   6. 做出来的东西；
   7. 收回开头那个麻烦，再给地址。

   每段写一句"看完能答出什么"（STORYBOARD 的段落理解表），观众带着这一句进下一段。
3. **讲稿：一句话一个动作**。说界面的每一句，写之前先去界面上找到它：那支片子有两句和界面对不上，是评审照着截图对出来的，重录了。人的原话、命令、按钮上的字照抄（硬规则 5）。
4. **取材：一步一张真截图**。网页和 Web App 用 Playwright 按视口截，写法见 `recipes/interaction/browser-walkthrough.md` 的"取材"一节。教程比演示截得密：一个状态里的过程也截（打一个字一张，拖动 16–30 张，播放中的视频每 0.4 s 一张，或者把真视频的帧贴进播放器的框），细节见 `recipes/interaction/step-capture.md`。
   - 那支片子的主界面是 1440×900 的视口按 3 倍截（4320×2700，JPG 质量 90）。要读的界面字推近后要 ≥ 44 px（desktop），13–14 px 的界面字就要推到每 CSS px 约 3.1–3.4 个屏幕像素，也就是整窗铺满 1080p 以后再推 2.4–2.5 倍；3 倍的截图推到约 2.25 倍还锐利，再推会软一点。出 4K 又要推近的，按 6 倍截。
   - 有状态的流程（写一句、发出去、被取走）在一个浏览器会话里一口气截完，分几次截，中间的状态会丢。
   - 终端和对话窗口的字本来就是文字，可以不截图，照真实的会话记录排进组件的 `lines`；网页按真截图（那支的仓库主页就是截图）。
   - 截完逐张看一遍：本机路径、用户名、别的项目名、账号、邮箱都不能出现。每张 `bin/vh assets add`。
5. **配音，然后一处一处定停顿**。先整稿配一条，再定停顿。停顿加在新画面出来以后、下一句开口之前：加在旧画面的尾巴上，观众照样觉得赶。那支片子的经过：原录音 257 s；为了配画面一律撑长到 311 s，听着走一步停一步；按规则一刀切收紧到 280 s，用户说"现在的节奏又比之前那个太快了，中间有几个画面都没有看清楚"；最后逐处写停顿，317 s，多出来的 37 s 里有 20 s 落在前 95 s。最后的数：
   - 句与句之间 44 处，中位 1.2 s，多在 0.5–2.0 s；产品窗口第一次打开后停 2.7 s；改好的镜头先自己放一遍时停 3.9 s、4.1 s；一段约 9 s 不配旁白的片头和快切留了 9.25 s；
   - 句子中间 40 处，0.25–1.0 s，中位 0.6 s（念完"复制到终端"，等粘贴落下）；其余逗号 0.2 s、句号 0.4 s；
   - 语速：句子里约 5.9 字/秒，算上全部停顿 4.5 字/秒。

   现在的工具：`bin/vh pace` 管句间停顿的范围（`--comma`、`--stop`）和逐句加减（`--extra id=秒`）；句子中间某一处要多停，把那句在稿子里拆成两句，再给前半句 `--extra`。
6. **画面：一步一镜**。整窗露一眼，光标走过去，点下去以后界面才变，要读的那一块变了镜头才推过去，做完停住，再拉开。推完就停，DOM 文字一直漂会闪。讲到哪一块，其余压暗（压到 62%），或者给它一圈光。打字、粘贴、回车、出字照组件的默认值（`components/ui-stage/slots.json`）。
7. **字幕**：一句一条或几条，句号处必断，开口前 0.1 s 才出。canvas-film 自带的字幕就是这样；自己写页面的用 `bin/vh captions <项目> --cards`。`bin/vh readcheck` 报短的，给它后面的停顿加一点，或者改稿把那一截并进前后句。那支片子 109 条，最短 1.83 s，中位 2.3 s，每条一行。
8. **评审：单独一轮只看叙事节奏**。打分层的评审照档位做；另给一个全新上下文的 reviewer 只看节奏：逐句列出"这一句的画面什么时候读得清、读得清多久、下一句什么时候开口"，前 2 分钟和结尾每 0.5 s 一帧、其余每 1 s 一帧，停顿按静音实测。那支片子这一轮比八项打分有用：查出了字幕跨句号、一个词的时间早了 1.1 s、要揭晓的画面在站牌和导览里提前露了、两句旁白和界面对不上。
9. **交付前**：`bin/vh check`；对着截图把说界面的每一句再点一遍；全片的镜头表里搜一遍每个揭晓画面，确认之前没露过。

## 审美要点

下面都是起点，立意需要时可以改。

- **真界面锐利、按真的比例**。周围可以换画法、换世界，界面本身不跟着变画风。
- **看不见的东西做成看得见的小物件**：复制的那一刻内容变成一张小卡，粘贴进去的字亮一下底色，左下角一枚步骤标签（数字和一句话，下一步时翻上来），每个毛病配一件看得懂的工具（字小配放大镜，一顿一顿配一排帧格）。
- **镜头跟着手**：全景 → 光标 → 推近 → 停 → 拉开，一步一个来回。操作段收着，炫的地方留给换段的那一下、产品出场和成果段。
- **颜色的意思跟产品走**：产品界面里某个颜色是"你"、某个是"agent"，片子里就用这个意思，观众打开产品用得上。
- **改之前、改之后要看得出因果**：人说的那一句留在画面上，让它变成新镜头（`recipes/seam/sentence-to-shot.md`），或者两版并排拖着同一个时间点看；改完的画面让它完整走一遍，不配旁白。
- **快切的成果墙每张 ≥ 0.6 s**（那支一开始 0.43 s，看不清）；数字卡停 2.7 s；拉远看全貌的定格停 1.4 s；状态变绿以后再多停 1 s 左右。
- **结尾回到开头那个麻烦**。那支片子开头说想把第十秒那行字往上挪一挪，结尾回到同一个画面，那行字真的挪上去了，然后才是"开源"和地址；初版的最后一句话没有接住开头，用户说"有点突兀的冒出来"。

## 禁止

底线：
- 编出来的界面、输出、对话、数字；截短不标出来（硬规则 5）；
- 截图和输出里露出人自己的东西：账号、邮箱、本机路径、别的项目；
- 旁白说界面是那样，界面上其实不是。

常见误用（参考）：
- 录屏放大：字糊、鼠标小；
- 凭印象重画能截到的界面（截不到的才画，画的照截图对）；
- 停顿加在旧画面的尾巴上，或者为了配画面把整条配音一律撑长；
- 要揭晓的画面提前露：站牌、导览、快闪、开头的成果墙里最容易漏；
- 字幕跨句号，读着像下一句抢跑；
- 开头先放一串成果混剪，不说要解决什么；
- 结尾冒出一句和开头无关的口号。

## Prompt 增量块

```text
+ TYPE: product tutorial, operations rebuilt in code, not screen-recorded. 1920x1080 30fps, {3–8} min, narration in {zh-CN | en}, canvas-film + the ui-stage component.
Walk the product for real first, in a clean copy with demo data: every command and its real output, every click and the page it leads to, the error a missing dependency gives. Nothing of the person's own (paths, accounts, other projects) on screen.
Default spine (a concept with its own structure replaces it): the problem, shown, from the first frame → install → the ways in and the main window's parts → one real case, one step a shot → the step this product does differently, given time → what it makes → back to the opening problem, then the address.
Captures: one picture a small step (a letter typed, a step of a drag, a playing video every 0.4 s), viewport {1440x900} at 3x; text read on screen ≥ 44 px after the push. Terminals and chats from the real transcript as text.
One step a shot: the whole window, the cursor goes, the page changes after the press, push in only when the part to read changes, hold, pull out. Spotlight the part being told (the rest at 62 %), a step chip with a number. Chinese is typed through pinyin and a candidate box, with a keyboard when one is on screen.
Pauses go after a new picture appears and before the next line, set place by place; never stretch the whole take. Captions break at every full stop and never show before the voice.
Every line about the interface checked against the capture; no reveal shown before its moment; the ending answers the opening.
```

## 自查重点

- 旁白里每一句说界面的话，对着截图点过一遍吗？
- 要揭晓的画面（改好的镜头、成果），之前的站牌、导览、快闪、开头里露过吗？
- 每个新画面出来以后，下一句开口前留了多久？前 2 分钟逐句列出来看。
- 字幕有没有跨句号，有没有在开口前出来（`bin/vh readcheck`、`bin/vh textcheck`）？
- 要读的界面字推近后 ≥ 44 px 吗？推近后糊不糊（截图倍率够不够）？
- 截图和终端输出里有没有人自己的东西？
- 渲染用的浏览器里有没有片子要的大字字体（`bin/vh fonts check`）？那支片子渲染用的无头 Chrome 没有系统的展示字体，大字掉成了衬线。
- 结尾回到开头那个麻烦了吗？每段看完能答出段落理解表那一格吗？

## 可参考的案例与源码

- `components/ui-stage/`：窗口、打字和拼音候选、键盘、光标、步骤标签、真截图回放；`sample/media/sheet.jpg` 是它动起来的样子。
- 镜头配方（`bin/vh recipes list --type tutorial`，会连带列出 `promo` 的界面和交互配方）：`interaction/ime-typing`（拼音打字和键盘）、`ui/caret-character`（终端的光标是个角色）、`interaction/step-capture`（真界面逐步回放）、`seam/sentence-to-shot`（一句话散开落成新镜头）、`ui/window-assemble`（真窗口一块块拼起来）；常一起用的：`interaction/browser-walkthrough`（取材）、`ui/terminal-run`、`ui/chat-thread`、`ui/zoom-callout`、`ui/diff-reveal`、`type/highlight-sweep`。
- `video-types/03-product-promo.md`：产品片的语域、素材清单和"不要凭印象重画界面"。
- `playbook/04-audio.md` 的"一条 take 里快慢差得明显时"（`bin/vh pace`）；`playbook/09-narrative.md` 第 5 节（长一点的片子怎么保持有新东西）。
- `engines/canvas-film/README.md` 的"字幕""Three.js 层"；`engines/CONTRACT.md`（自己写页面时的合约）。
