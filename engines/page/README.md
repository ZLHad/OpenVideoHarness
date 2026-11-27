# page：不用引擎，自己写页面

一支片子就是一个 `film.html`：页面按页面合约交出 `window.film`（[`engines/CONTRACT.md`](../CONTRACT.md)），画什么、怎么画、用哪个库，都由你定。仓库的取帧、出片、检查和审阅只认这个合约，不认引擎，所以走这条路拿到的工具，和用现成引擎时一样。

## 什么时候走这条路

- 用户说"自由发挥""不用照模板""你自己定怎么做"，或者路由表里没有贴切的类型。
- 任何类型、任何画幅都能用：`bin/vh new <type> <slug> --engine page`（可以加 `--aspect`、`--res 4k`、`--effort`）。不装任何依赖，只要 Chrome、Node 和 FFmpeg。
- 档位、关卡和底线照旧（CLAUDE.md）；`standard` 和 `studio` 开工前照 CLAUDE.md 第 2 步，再读 `playbook/01-pipeline.md` 的"总表"和"规格"。放开的只是"怎么做"：不按类型分配引擎，类型文档、playbook、配方、风格都不是开工前的必读。想参考时用 `bin/vh know <几个词>` 去查；类型文档的"禁止"和"自查重点"两节写着平台的规矩和这类片子常见的翻车，最值得翻。

## 合约

`bin/vh new` 放进项目的 `film.html` 已经是一个合格的空页面，换掉 `frame(t)` 里的东西就是你的片子。

| 字段 | 意思 |
|---|---|
| `frame(t)` | 画出第 t 秒的完整画面。同一个 t 永远画出同一帧，不管之前画过什么（硬规则 1）：不用 `Math.random()`、`Date.now()`、`requestAnimationFrame`、CSS 动画，不留跨帧的状态；要随机就用带种子的 `hash(i)`。宿主会把这些时钟钉在 t 上兜底，并报出哪些帧调了 `Math.random` |
| `duration`、`fps`、`width`、`height` | 片长（秒）、帧率、画面的 CSS 尺寸。出 4K 不改尺寸，渲染时加 `--dpr 2`（模板的画布已经按 `devicePixelRatio` 分配像素） |
| `ready` | 字体、图片、数据都在这里载好，宿主等它 resolve 才画。网页字体要按名字一个个 `document.fonts.load('700 80px X')` |
| `texts` | 观众要读的字：`[{text, start, end}]`，从完全显示到消失。写了它，读时和被挡的字才量得到 |
| `shots` | 可选，镜头的起止：`[{id, start, end, reads}]`，分镜页按它每镜画一帧 |

`events`、`chapters`、`covers`、`ui(t)` 这些扩展字段见合约原文，用得到再写。页面可以是 canvas、SVG、DOM、WebGL 或它们的组合，只要每一帧只由 t 决定。

## 工具，和查得到的底线

| 想做的事 | 命令 |
|---|---|
| 看几个时刻 | `bin/vh frames <项目> --at 1,5,9` |
| 出片（分块并行，断了接着渲，每次留一个版本） | `bin/vh render <项目> --out <项目>/out/draft.mp4` |
| 只重画成片里的几秒 | `bin/vh patch <成片> --seconds 4-7` |
| 联系表 | `bin/vh sheet <成片>` |
| 分镜页（读 `shots`） | `bin/vh storyboard <项目>` |
| 缺字、字体落到别的字体上 | `bin/vh fonts check <项目>` |
| 配乐、音效、混音、声音质检、合上音轨 | `bin/vh music`、`bin/vh sfx`、`bin/vh mix`、`bin/vh qa`、`bin/vh mux`（`playbook/04-audio.md`） |
| 在 Studio 里审 | `bin/vh studio <项目>` |

CLAUDE.md"任何档位都不降的底线"里，有命令在查的这几样，以命令的结果为准：

| 底线 | 谁来查 |
|---|---|
| 每一帧是 t 的纯函数 | `bin/vh determinism <项目>` |
| 规格、黑场、定格、片中静音、闪白 | `bin/vh check <成片>`（出片前必跑），有声片再加 `bin/vh qa` |
| 字停够读一遍的时间 | `bin/vh readcheck <项目>`（读 `texts`） |
| 要读的字被画面挡住、出了画面、对比不够 | `bin/vh textcheck <项目>`（读 `texts`） |
| 素材许可 | `bin/vh assets add` 登记，`bin/vh assets check` 自查 |
| 付费接口要预算 | 付费命令自己会拒绝 |

没有命令能替你查的，注意力留给它们：事实和引文对不对得上原文，许可记的是不是真的，当事人同不同意，平台和法律的红线，文件里有没有 key，字号够不够目标屏（下限按 BRIEF 的 `Watch on`，见 `playbook/03-motion-design.md` §4；按目标屏缩一张联系表看，命令见 `playbook/02-verification.md` 的"手机测试"）。

## 时间是数据

画面跟着什么走，就从那里取时间，不手写秒数（硬规则 2）：

- **旁白**：稿子怎么写得像人写的，见 `playbook/09-narrative.md` 第 10 节，写完跑 `bin/vh words <项目>` 看模型顺手的句式落在哪；分镜里每一镜写一件旁白没说、画面要多说的事（`templates/STORYBOARD.md`）。写 `audio/script.txt`，`bin/vh tts <项目>` 配音，出来的 `audio/timeline.<语言>.json` 里每句、每个字都有秒数。模板里的 `at("a2", "看不到")` 取这几个字开口的时刻（在 `ready` 里先载入时间轴）。逐字的时间要靠对齐，`bin/vh tts -h` 说哪种方式这台机器能用。
- **音乐**：`bin/vh music` 用代码作曲，同时写出每一拍、每一小节的秒数；用现成的曲子时 `bin/vh beats` 分析节拍。
- **音效**：动作发生的时刻写进一份事件表，例如 `audio/sfx.json`（`[{"t": 3.2, "sfx": "click"}]`）。页面在 `ready` 里读它来画动作，`bin/vh sfx place audio/sfx.json audio/sfx.wav <片长>` 读同一份来放声音，一份时间，两边对得上。`t` 也能写成挂在旁白或小节上的引用（`bin/vh sfx -h`），这时页面要按同样的规则换算。
- **字幕**：`bin/vh captions <项目>` 从旁白时间轴出 SRT 和 `captions.json`；可以由页面画出来，也可以 `bin/vh mux` 作为可开关的字幕轨。

没有旁白也没有音乐的无声片，时长由字和画面要读多久决定（`texts` 和 `bin/vh readcheck`）。

## 先撑开，再收拢

放开让模型自己做，最容易滑回它最熟的样子：暗底、发光、玻璃卡片、居中的大字。动手写整片之前，先用三种明显不同的做法各画一帧，配色、构图、运动方式各至少换一样。用 `bin/vh frames` 出图，放进一个文件夹，`bin/vh sheet <文件夹>` 拼在一起比，挑一个，在 `DECISIONS.md` 记一行为什么。要停关卡 ① 的片子，这三帧正好是立意卡上要配的画面。

## 交之前

- 看整片：`bin/vh sheet <成片>` 拼一张联系表，再按目标屏缩一张，必读的字在手机上读不读得出（`playbook/02-verification.md` 的"手机测试"）；要进信息流的片子，再看前 2 秒的逐帧 strip，第 0 帧是不是就在动、有没有让人停下来的东西。
- 跑一遍上面那张表里的检查，`bin/vh check <成片>` 必跑，它报失败就修到不报。
- 交的时候说清：选了哪个立意、刻意没用的最典型做法（换掉了哪个默认样子）、自己最不满意的一两处，在 `DECISIONS.md` 各记一行。`quick` 档到这里就交；`standard` 和 `studio` 还有关卡和评审，`bin/vh status <项目>` 会说下一步。

## 想用现成的东西时

- **组件和公共库**：`bin/vh components list` 看有哪些，`bin/vh components add <项目> <名字>` 复制进项目，它们和 `components/lib/`（随机、噪声、缓动、弹簧、颜色、安全框、文字排版）一起进来，模板的 `<script type="module">` 里直接 `import`。
- **Three.js**：canvas-film 钉好版本的那一份在 `engines/canvas-film/three/`，复制进项目再 `import`（它的用法见 `engines/canvas-film/README.md` 的"Three.js 层"）。
- **拼别的页面和素材**：剪辑表 `edit.json`（`engines/EDIT.md`）能把这一页和别的页面、图片、实拍素材、纯色排成一列，一起渲染。
- **现成的手法**：镜头配方 `bin/vh recipes list`，风格预设 `bin/vh style list`，都是参考，不是规则。

## 局限

- Studio 里放的是渲出来的片子，不是页面本身：改完看效果，用 `bin/vh frames` 取几帧，或者 `bin/vh render <项目> --range 4:7` 只渲那几秒。
- 页面里用 `<video>` 取画面时，宿主还不会精确地跳到那一帧（合约原文"还没做的"）；实拍素材走剪辑表。
- canvas-film 那套挂在旁白上的镜头表、字幕排版和章节条，这里没有；长片需要它们时，用 `--engine canvas-film` 更省事。
