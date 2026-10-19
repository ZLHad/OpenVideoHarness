# canvas-film：跟随旁白或配乐时间的 canvas 引擎

一页 `film.html` 加几份 `src/*.js`，在一块 2D canvas 上画出每一帧。旁白片的镜头、字幕、章节条时间挂在旁白的字上：重配一句、改一个词、整片插进停顿，画面跟着走，不用手改秒数。它按页面合约（仓库里的 `engines/CONTRACT.md`）写了 `window.film`，`bin/vh frames` 取帧、`bin/vh textcheck` 查字都直接能用。这份说明在项目里有一份副本，叫 `ENGINE_README.md`。

## 什么时候用

- 旁白撑着的横屏长片：几分钟到十几分钟的科普、人物、讲解，几十上百个镜头，镜头跟着旁白的字切。
- 画面是代码画的 2D：纸面、卡片、图表、示意图、照片和截图。Three.js 底层以后再收进来，现在没有。
- 不合适的：DOM 排版和 GSAP 动效为主的短片（HyperFrames）、手绘角色（ClaudeAnimationBase）、数学推导（Manim）。

## 建项目

```bash
bin/vh new <type> <slug> --engine canvas-film      # 任何类型都行；画幅固定 16:9（1920×1080），--res 4k 照常
bin/vh frames projects/<date>-<slug> --at 1,5,9    # 模板自带一支 23 秒的示例片，建好就能取帧
```

| 文件 | 是什么 |
|---|---|
| `film.html` | 页面：`@font-face`（只用 `local()` 本机字体，不下载）、一块 canvas、按顺序载入 `src/` 的脚本。不用构建 |
| `src/00-core.js` | 设定 `FILM` 的默认值、时间（旁白时间轴、cue、镜头、章节、字幕）、录制器 |
| `src/05-music-clock.js` | 可选：配乐小节、拍与音符时间；从 `music.beats.json` 读取，不设 `FILM.music` 就不起作用（见"可选模块"） |
| `src/06-time-map.js` | 可选：时间映射，片子时间对另一条轴（数据的日期、步数、旧版的秒数）的折点，和轴上带 id 的事件；不设 `FILM.timemap` 就不起作用 |
| `src/10-draw.js` | 画字（字号下限在这一层）、量字、折行、形状、图片、缓存的纹理 |
| `src/15-fx.js` | 颗粒、暗角、整幅压暗 |
| `src/20-ui.js` | `label`、`drop`、`stamp`，章节进度条，字幕 |
| `src/30-transitions.js` | 转场 |
| `src/50-shots.js` | **这支片子**：`FILM` 设定、章节、镜头。其余文件是引擎，一般不用改 |
| `src/90-main.js` | 画第 t 秒，`ready` 时载入和检查，`window.film` |
| `audio/timeline.zh.json` | 示例旁白的时间轴（合成的，不是配音）。真片子跑 `bin/vh tts` 覆盖它 |
| `assets/` | 图片等素材，在 `FILM.images` 里登记 |

示例片的 `src/50-shots.js` 和 `audio/timeline.zh.json` 是成对的，开工时两样一起换掉：写 `audio/script.txt`（每行 `@id 一句旁白`），跑 `bin/vh tts`，再照着新的 id 写镜头。

设定都在 `src/00-core.js` 开头的 `FILM` 里，每项一行注释（语言、旁白前后留多久、字号下限、字幕、颗粒、片头片尾的淡入淡出、界面颜色、图片）；这支片子要改的，在 `src/50-shots.js` 里用 `Object.assign(FILM, {…})` 改。

## 时间：挂在旁白的字上

`bin/vh tts` 写出的 `audio/timeline.<lang>.json` 里，每句有 id、起止时间，对齐过的还有每个字的时间（`--align gemini`）。时间轴上的秒数就是片子里的秒数。旁白要晚一点开口，就在配音时加 `bin/vh tts … --lead <秒>`：人声和时间轴一起推后，画面不用另外挪。只有手上的时间轴从 0 开始、又想让画面先走一会儿，才设 `FILM.lead`：引擎把时间轴整体后移这么多秒，混音前人声也要垫上同样长的静音（`tools/audio/README.md` 的"手动的响度和合成命令"）。片长是 `FILM.lead + 时间轴长度 + FILM.tail`。

时间写成 cue：

| 写法 | 意思 |
|---|---|
| `"@b2"` | b2 这句开口 |
| `"@b2:跟着走"` | b2 里第一次说到"跟着走"的那一刻 |
| `"@b2>"` | b2 这句说完 |
| `"@b2:跟着走-0.3"`、`"@b2>+0.5"` | 再提前或推后几秒 |
| `3.2` | 就是第 3.2 秒 |

- 找词时去掉空格、标点和符号再比，所以"“第一”"写成"第一"就行。同一句里出现两次的词取第一次；要后面那次，多写几个字把它和前一次分开。
- 字的时间按最长公共子序列对到对齐结果上：识别把某个字听成别的，就跳过它，用前后对上的字插值。没有逐字时间的句子，按字数在整句里均分。
- id 只用字母、数字和下划线（`@intro-1` 会被读成 id `intro` 加 `-1` 秒）。
- 词本身以"-数字"结尾（GPT-4、COVID-19）时，`"@g1:GPT-4"` 有两种读法：这个词，或者"GPT"之前 4 秒。这句里正好有"GPT-4"时，`ready` 会停下来让你写清楚：`"@g1:GPT-4+0"` 是这个词，`"@g1:GPT-4.0"` 是提前 4 秒。
- 镜头的 `at`，以及 `o` 里任何一层的 cue 字符串，都在 `ready` 时换成秒。**解析不了就立刻停**：`ready` 失败，`bin/vh frames` 和 `bin/vh textcheck` 退出码 2，一次列出出问题的地方（前 12 处，其余给个数）：哪个镜头、哪个字段、cue 原文、这一句现在的文字、句子里最像的几个词。时间轴里缺 id、起止时间的行，转场的长度写错（`["turn", -1]`，或者给 `cut` 写了长度），也在这里一起报。不会等到超时。

  ```
  shot S02 (o.two), cue "@a2:第三张": line a2 has no "第三张"; it now reads "说到第一张，卡片落下；说到第二张，第二张跟上。"; nearest: "第一张", "第二张", "到第一张"
  ```

- `draw` 里也可以直接调 `cueT("@b2:跟着走")`，但那样要到画到这一帧才检查。要在 `ready` 就查到，把它写进 `o`。
- 不配旁白的片子：`FILM.timeline = false`，再给 `FILM.duration`，时间都写秒。

## 镜头、章节、转场

```js
const SHOTS = [
  { id: "S02", at: "@a2", tin: "settle",
    see: "两张卡片：说到“第一张”，第一张落下；说到“第二张”，第二张落下",
    o: { one: "@a2:第一张", two: "@a2:第二张" },
    draw(t, s) { … card(t, s.o.one, 660, 580, "1", "第一张"); … } },
];
const CHAPTERS = [{ at: 0, title: "挂在字上" }, { at: "@b1", title: "翻一页" }];
```

- 一个镜头从它的 `at` 开始，到下一个镜头的 `at` 结束；第一个镜头从 0 开始。镜头顺序不对、短于 0.2 s、短于自己的转场，`ready` 都会报出来。
- `draw(t, s)`：`t` 是整片的秒数，`s` = `{ id, t0, t1, lt, u, o, din, dout }`（镜头起止、镜内秒数、镜内进度 0–1、解析好的 `o`、进出转场的长度）。
- 其他字段：`see` 写观众要看懂什么（分镜和审阅用）；`cam: [z0, z1, cx, cy]` 让镜头在整镜里从 z0 缓推到 z1，停着的画面也不会冻住；`light: true` 表示浅色画面，字幕改垫一块深色底；`nocap: ["a1"]` 表示画面上已经用大字写了这句，整句不出字幕。
- 转场 `tin` 写名字，或者 `["turn", 1.2]` 改时长。新镜头从自己的 cue 开始计时，旧镜头在下面接着走到转场结束；两边每帧都整幅重画（需要时画进离屏画布），不留跨帧的状态。

  | 名字 | 默认时长 | 样子 |
  |---|---|---|
  | `cut` | 0 | 硬切（默认） |
  | `settle` | 0.5 s | 硬切，新画面从 1.06 倍收回原大，没有叠化 |
  | `dim` | 1.0 s | 暗下去，再从暗处亮起新画面 |
  | `fold` | 0.85 s | 旧画面像一块板，绕左边转开，露出下面的新画面 |
  | `turn` | 1.0 s | 翻书页：旧画面的右半页翻过来，背面是新画面的左半页 |
  | `blot` | 1.2 s | 墨从几处晕开，软边，晕到的地方露出新画面 |

- 章节进度条（顶上）：每章一格，宽度按章名；当前一章随进度填满，章名一直显示；每章开头约 3 s 显示全部章名（章名太多、一行放不下时，只显示当前一章）。显示的时段由 `FILM.bar = { from, to }` 定，默认从第一章到片尾。

### 用同一份镜头表生成分镜和节奏图

`ready` 后，`window.film.shots` 给出每个实际镜头的 `id/start/end`，首镜从 0 开始、末镜到片尾，时间包含旁白的 lead/tail。它直接读引擎解析的镜头边界，保留 `S04a` 等完整 id，不再需要从源码里用正则抄一份时间表。

`SHOTS` 可加 `segment`（默认取镜头开始时所在章的标题）、`reads`（默认用 `see`）、`label`、`unsure`。`reads` 是观众要看懂的内容，不是 `window.film.texts` 的实测字卡。转场另附 `transition: {type, duration}`，起止按切入点算，不把叠化重叠算成镜头加长。

```bash
bin/vh storyboard <项目>             # 无 shots.json 时直接读 film.html；没有成片时直接取页面帧
bin/vh storyboard <项目> --snapshot  # 即使已有成片，也取当前代码的帧
bin/vh rhythm <项目> --segment 章名
bin/vh rhythm <项目> --shots film.html # 有手写 shots.json 时，明确改用页面
```

两个命令的优先级都是：显式 `--shots JSON或页面` > 项目 `shots.json` > `film.html` 的 `window.film.shots`。JSON 仍可离线使用；live 读取需要 Node 和 `bin/vh` 选用的 Chrome。每次运行都等 `ready` 后重读，来源打印在输出中，并写入分镜 `index.json`、节奏图页脚，不会写回或覆盖手工镜头表。分镜仍优先用每镜的 `frame`，再用指定或已有成片；没成片才自动取页面帧，`--snapshot` 可优先取页面。页面加载、ready 或取帧错误会让命令失败；rhythm 只在可选 `shots` 字段缺失时省略该轨，格式错误不会跳过。

旧项目复制过引擎的，把新版 `src/90-main.js` 的 `get shots()` 合入自己的 `window.film`；项目的 `src/50-shots.js` 保留。迁移前继续用手写 `shots.json`。其他引擎也可实现该字段，再用 `--shots page.html` 明确读取。

## 字

- 画字一律用 `txt(s, x, y, o)`。字号在最底层兜住：`font()` 不会给出小于 `FILM.minText`（默认 44 px，按 BRIEF 的"在哪看"改，见 `playbook/03` §4）的字号，`measure()` 用的是同一个字号，排版不会和画出来的对不上。字幕的字号另有一档，`minText` 管不到：`FILM.caption.size`（默认 52；`playbook/03` §4 的字幕下限 desktop 48、feed 115），改"在哪看"时两样一起改。
- 故意要小、要淡的字（一页原文当底纹、时间轴的刻度）写 `texture: true`：它可以小于下限，也不算 read。
- `ready` 时每个镜头抽 5 个时刻各画一遍，绕过 `txt()` 自己设 `X.font` 写下的小字也会被抓到，打成一行 `console.error`（`bin/vh frames` 在开头"while loading"下面列出来），写明镜头和那段字。判的是代码要的字号，不是动画缩放途中的大小。
- `label(t, at, s, x, y, o)`：一行字在 `at` 升起，停到镜头结束（或 `o.until` 前淡出）；完全出来以后登记成 read，`bin/vh textcheck` 按它查遮挡和对比。`stamp()` 盖下以后也算 read。自己画的字要登记，就在 `draw` 里调 `read(text, start, end)`。
- 跨过切点或转场一直在屏上的字（HUD、角标、跨段的字卡）：`read()` 默认只记本镜头直接画进画面的那一段（转场进来以后到镜头结束），跨切点的一张卡会被记成两段短的，`bin/vh readcheck` 报出假的 FAIL。写 `read(text, start, end, { overlay: true })`（`label()` 写 `overlay: true`），按 start 到 end 记成一条，只受片头片尾的淡入淡出和片长约束。卡要由它跨过的每个镜头画（或者画在镜头之上的一层里）；录制器只画镜头，所以登记写在镜头的 `draw` 里，哪个镜头都行，几处一样的调用只留一条。第 4 个参数照旧可以只写种类（`"label"`），也可以写进对象：`{ kind: "label", overlay: true }`。区间是你声明的：`bin/vh textcheck` 照样在区间里抽样（跨过切点的那几次也抽），哪个时刻没画出来，列成 "missing from some samples"。
- 旧项目复制过引擎的：把新版 `src/00-core.js` 的 `read()` 和 `src/20-ui.js` 的 `label()` 合入（项目改过这两个文件就按差异合）；以前为了过 readcheck 直接往 `REC.reads` 里塞的跨镜头字卡，改成 `overlay: true` 的 `read()`，再跑一次 `bin/vh readcheck` 和 `bin/vh textcheck`。不迁移的项目照旧能用，只是跨切点的字仍按镜头裁。
- 三个字体族 `"Film Sans"`、`"Film Serif"`、`"Film Mono"` 在 `film.html` 里声明，`o.family` 写 `sans`、`serif`、`mono`。换字体改 `@font-face` 的 `local()`，族名不动；`ready` 逐个载入，本机没有的会报出名字，画的时候落到后备字体。
- 字体在，某个字它没有，也会悄悄换字体画（`"Film Mono"` 的 Menlo 没有中文，宋体的 Black 没有"–"）。`bin/vh fonts check <项目>` 一个字一个字查，`bin/vh render` 出片时也会说。`local()` 写什么名字，`bin/vh fonts list --cjk` 列出本机有的；要让片子不靠本机字体，`bin/vh fonts subset <项目>` 把用到的字抽成 woff2 放进 `assets/fonts/`，按它打出的那行写进 `src` 的最前面（系统字体的子集是一份拷贝，只留在项目里，不发出去）。

## 字幕

- 按旁白的每句自动生成，画在底部一条软的暗带上（`light` 的镜头改成一块底板）：一行，不超过 `FILM.caption.max` 个汉字宽（默认 16，拉丁字母按 0.55 个算；英文片调到 24 左右）；句号、问号、叹号处必断，两句话不进同一条（半角的句点、逗号后面紧跟字母或数字时不算，3.5、1,000、12:30、Node.js 不会被切开；e.g.、Dr. 这类缩写和"1. 2."这样的编号会被当成句末，看到了就改旁白稿）；一句太长时按逗号分，分得尽量一样长；逗号显示成空格，末尾标点不显示（问号、叹号和省略号留着）。
- 时间取每段第一个字的时间（提前 0.1 s），一句的最后一条可以留到停顿里（`hold`，0.8 s）；不到 1.8 s 的往后借停顿，不占下一条；两条之间的缝小于 0.25 s 就首尾相接，字幕带不会闪一帧。
- 引擎自己切字幕时，太长的一段没有逗号就按宽度从中间切，可能切在词中间（不会切在拉丁字母的词和数字中间）。要按词切：跑 `bin/vh captions <项目> --cards`（用 jieba 找词边界，读 `audio/capbreaks.json` 的手工断点表），再在 `src/50-shots.js` 里写 `FILM.caption = { ...FILM.caption, from: "audio/captions.json" }`，引擎就用这份字幕的切法和时间（加上 `FILM.lead`），最短停留、短缝相接照旧在引擎里做。改了配音要重跑 `bin/vh captions --cards`（`bin/vh pace` 会照原来的模式重做）。这份文件不是一行一条的卡（不带 `--cards` 跑出来的）、有卡宽过 `FILM.caption.max`、或者卡对应的句子在现在的时间轴里没有（换过稿子）、卡的时间落在它那句之外（换过一条配音），`ready` 都会报出来，不会悄悄照画；单独一个比 `FILM.caption.max` 还宽的英文词（一个链接）照画。
- 一句里紧跟着又一句、前一句又很短时（"他说："走吧。""），那一条可能只亮半秒：`bin/vh readcheck <项目>` 按字幕的下限查得出来。

## 封面

`src/50-shots.js` 里写 `COVERS`，每张一项：

```js
const COVERS = [
  { id: "A", at: "@a2:第二张+0.6", cam: { z: 1.12, x: 0, y: -60 }, title: { text: ["改一个字，镜头跟着走"], size: 150, x: 960, y: 1010, align: "center" },
    ratios: { "9:16": { focus: [1260, 540], title: { text: ["改一个字", [{ text: "镜头", color: PAL.amber }, "跟着走"]], size: 190, x: 540, y: 1420, align: "center" } } } },
];
```

- `at` 和镜头的一样写成 cue：改了开场、重配一句，封面跟着取到同一个画面，不会过期。`bin/vh cues` 把它列成 `cover.A.at`。
- `cam: { z, x, y }`：只在这张封面上生效的机位微调，绕画面中心放大 z 倍，再挪 x、y 像素，给标题让出地方。挪动不能超过放大留出的余量（横向 (z − 1) × 960，纵向 (z − 1) × 540），超了 `ready` 会报出来，免得露出画面的边。
- `title: { text: [行…], size: [每行字号] 或一个数, x, y（第一行的基线）, align, color, band, gap, family, weight }`：默认用 `"Film Heavy"` 画（`family: "heavy"`、`weight: 900`），这一档是各系统最粗的中文黑体，带深色描边和一条压暗的底；`band: false` 不要底。`family` 也可以写 `sans`、`serif` 或一串 CSS 字体名（字体要在 `film.html` 里声明）。章节条和字幕默认不上封面，要的话写 `bar: true`、`caption: true`。
- 多种颜色：`color` 可以写一个，也可以每行一个（`color: ["#F4F1EA", PAL.amber]`）；一行里要分段配色，这一行写成一串 run：`["改一个字，", { text: "镜头", color: PAL.amber }, "跟着走"]`，没写颜色的 run 用这一行的颜色。先描完整行的边、再填字，前一段的描边不会压到后一段的字上。只写字符串的旧写法照旧，画出来和以前一样。
- 封面换个机位：画封面时，每个镜头 `draw(t, s)` 的 `s.cover` 是这张封面的 `id`，片子本身的帧里是 `null`。镜头可以按它换一个更有冲击力的取景、藏掉一个只在片中需要的标注，片子一帧不变。别在 `cover()` 外面设全局变量：那样既容易留到下一帧，也看不出是哪张封面。
- `bin/vh frames <项目> --covers` 把每张封面画进 `out/covers/<id>.png`（`--covers=A,B` 只画这几张，`--dpr 2` 出 3840 × 2160），再用 `bin/vh cover-preview out/covers/*.png` 看在信息流里的大小。
- `--no-title`：不画标题，出一张干净的底图 `out/covers/<id>-clean.png`，给要在别处排字的项目用，不用为此改 `COVERS`。片子本身的帧本来就没有封面标题，不受影响。

### 其他比例（9:16、3:4、4:3）

`bin/vh frames <项目> --covers --ratios 9:16,3:4,4:3`（可以加 `16:9`、`1:1`，`--no-title`、`--dpr 2` 照用）每张封面每个比例出一张 `out/covers/<id>-9x16.png`。它做的是**裁切**，不是重画：画面还是这张封面 16:9 的那一帧，取其中这个比例最大的一块（整数像素、正好是这个比例：1920 × 1080 的片子里 9:16 是 603 × 1072，3:4 是 810 × 1080），画框外的东西不会出现。输出的短边是 1080 × `--dpr`（9:16 出 1080 × 1920）；页面按裁切需要的像素比来画（9:16 约 1.8 × `--dpr`），画面不会被放大。每张输出都写明裁了哪一块、标题是谁排的。

每个比例在 `ratios` 里自己决定：

- `focus: [x, y]`：裁切围着哪一点（封面画面里的 px，`cam` 已经算进去），默认画面中心；裁不出画框，靠边时自动收回来。
- `cam: { z, x, y }`：这个比例用自己的机位，代替封面的 `cam`。要更紧的取景就在这里放大：画面按这个机位重画，比把裁好的图放大清楚。
- `title`：这个比例自己的标题，写法同上，坐标按这个比例的像素算（9:16 是 1080 × 1920，3:4 是 1080 × 1440，4:3 是 1440 × 1080），暗带只铺这个比例的宽度；`title: false` 这个比例不要标题。不写时，把封面的标题挪过来当起点：同样的行和颜色，居中，整体缩到不超过宽度的 88 %（不放大，也不小于 `FILM.minText`，按实际画出的字号算），这样还放不下的行折成几行（颜色跟着字走），最后一行的基线在 80 % 高度；折了还放不下（一个词就比画面宽，或者行数多到高度装不下），`ready` 报出是哪张封面、哪个比例，要你写 `ratios[r].title`（`--ratios` 临时要的比例在画的时候报）。这只是默认排法，不是版式，先用 `bin/vh cover-preview` 看过，再按画面写自己的 `title`。

章节条和字幕只出现在片子本身的比例上。标题里每一行宽不宽得下，`ready` 按各自的比例检查，超出就报出来；`bin/vh fonts check` 也把每个比例的标题画一遍，查字体缺字。比例出齐以后，`bin/vh cover-preview out/covers/A-*.png` 一次看各平台信息流里的样子（命令最后会打出这一行）。

**复制过引擎的旧项目**：这些都在引擎里，旧拷贝要合进来才能用。把新版 `src/00-core.js` 的 `coverBox()`、`buildCovers()` 和 `COVER_NOW`，`src/20-ui.js` 的封面标题一段（`pickAt` 到 `ratioTitle()`），`src/90-main.js` 的 `drawShot()`（多了 `cover: COVER_NOW`）、`cover()` 和 `window.film` 里的 `covers`、`cover(id, o)` 合进自己的拷贝；项目改过这几个函数就按差异合。以前在 `cover()` 里设全局变量换机位的，改成在镜头里读 `s.cover`；以前为出底图临时去掉 `COVERS` 标题的，改用 `--no-title`。没合的旧拷贝：`--no-title` 会报"页面没说它去掉了标题"而不出图，`--ratios` 会报"页面没给出裁切"，不会悄悄出一张错的。

`"Film Heavy"` 在 `film.html` 里按这个顺序找（`bin/vh fonts list --cjk` 列出本机的中文字体，对一下表里的名字；`ready` 报出本机一个都没有的情况；标题里的字这一档字体有没有，`bin/vh fonts check` 也查，它会把封面画一遍）：

| 系统 | 字体（`local()` 的名字） | 备注 |
|---|---|---|
| macOS | 兰亭黑 Heavy（`FZLTTHK--GBK1-0`、`Lantinghei SC Heavy`） | 系统按需下载的字体：第一次用时才装，没装就落到下一个 |
| macOS | 冬青黑体简体 W6（`HiraginoSansGB-W6`） | 系统自带 |
| Linux | 思源黑体 / Noto Sans CJK SC Black 或 Heavy（`NotoSansCJKsc-Black`、`SourceHanSansSC-Heavy`） | `fonts-noto-cjk-extra` 这类包里才有 Black |
| Windows | 微软雅黑 Bold（`Microsoft YaHei Bold`） | 没有更粗的一档 |
| 最后 | 苹方 Semibold（`PingFangSC-Semibold`） | 每台 Mac 都有；苹方最粗只到 Semibold |

## 事件和 reads：录制器

画东西的小函数开头调一次 `cue(kind, t0, { x })`（`drop`、`stamp` 已经调了），平时什么都不做；`ready` 时每个镜头抽 5 个时刻各画一遍，录下镜头在画面上时发生的事件（落下、盖章、亮起……）和 reads，去掉重复。`x` 写这件事在镜头里的位置（不随 t 变），按变换换算成屏幕横坐标，配音效时给声像用；推镜时取离事件最近的那次抽样的变换（推镜很慢，差不了多少）。同一个调用在几次抽样里各录一次，只留一条。每个镜头边界的转场也记成事件（`kind` 就是转场名，`cut` 也在内），评审前拿它和 STYLE 写的转场对一遍。

## `window.film` 给出什么

| 字段 | 内容 |
|---|---|
| `frame(t)` | 清掉画布，画出第 t 秒：镜头（或转场里的两个镜头）、颗粒、章节条、字幕、片头片尾的淡入淡出。`frame(t, { layer: "scene" })` 不画章节条和字幕 |
| `duration` | 片长（秒） |
| `ready` | 字体、图片、时间轴载入，全部 cue 解析，字幕排好，录制器跑完 |
| `width`、`height` | 1920 × 1080；画布按 `devicePixelRatio` 开大，`--dpr 2` 就是 4K |
| `texts` | reads 和字幕：`[{text, start, end, read}]`，字幕的 `read` 是 `subtitle` |
| `events` | `[{t, kind, shot, x?, dur?}]` |
| `chapters` | `[{t, title}]` |
| `cues` | 每个 cue 的解析结果：`[{id, ref, t}]`，`id` 像 `S02.o.one`、`chapter2.at`、`cover.A.at` |
| `covers`、`cover(id, o)` | 封面：`[{id, t, title, ratios}]`，`cover(id)` 按它的机位和标题画这一张；`o.title: false` 不画标题，`o.ratio: "9:16"` 画这个比例的标题并返回裁切 `{crop, size}` |
| `timeline` | 载入的旁白时间轴，相对 `film.html` 的路径；无声片是 `null` |
| `ui(t)` | 章节条和字幕在 t 秒时的框：`[{name, box}]`。全部章名都亮着时，章节条一个框，从进度线上的圆点到章名下沿；只亮当前一章时，进度线一个框（`chapter bar`），当前章名一个框（`chapter title`）；字幕只框字，不框暗带（`caption`） |

页面从不自己往前走，只在 `frame(t)` 被调用时画；直接用浏览器打开 `film.html`（`file://`）读不到时间轴，什么也不画。

## 检查和出片

```bash
bin/vh frames <项目> --at 4.9,12.8           # 单帧，无损 PNG，在 <项目>/out/frames/
bin/vh frames <项目> --strip 12.2:13.4 --fps 10   # 一段的每一帧拼成一张，看转场和动作
bin/vh frames <项目> --at 4.9 --dpr 2        # 4K 的帧
bin/vh textcheck <项目>                       # reads 和字幕有没有被盖住、对比够不够、出没出画；镜头有没有画到章节条、字幕底下
bin/vh frames <项目> --covers                 # 封面：out/covers/<id>.png（COVERS，取帧时间挂在字上）
bin/vh frames <项目> --covers --no-title      # 不带标题的底图：out/covers/<id>-clean.png
bin/vh frames <项目> --covers --ratios 9:16,3:4,4:3   # 其他比例（裁切）：out/covers/<id>-9x16.png …
bin/vh cues <项目> --chapters                 # 章节表，写进简介用：0:00 章名……，也写进 out/chapters.txt
bin/vh cues <项目> --save                     # 每个 cue 落在第几秒，存进 out/cues.json；换了配音再跑，列出哪些镜头挪了、挪了多少
bin/vh readcheck <项目>                       # reads 和字幕够不够时间读：用独立临时快照，不覆盖已有 out/texts.json
bin/vh readcheck <项目> --export              # 只导出 window.film.texts 到 out/texts.json，不检查读时
bin/vh readcheck <项目> --out /tmp/reads.json  # 保存到指定文件，再检查；加 --export 就只导出
bin/vh determinism <项目>                     # 同几个时刻换顺序画、换进程画，看是不是 t 的纯函数
bin/vh render <项目> [--dpr 2]                # 成片画面：<项目>/out/film.mp4（--dpr 2 是 4K），没有声音
bin/vh patch <项目>/out/film.mp4 --seconds 142.2-159.2   # 只重画改过的一镜，接回成片（片子要是 bin/vh render 出的，旁边有 .render.json）
bin/vh mux <项目>/out/film.mp4 <混音.wav> <成片.mp4>   # 套上混音（混音要和画面一样长：mix 写 profile=… dur=<画面秒数>，否则差 0.1 s 以上会被拒绝）
```

`readcheck` 的 `--out` 可以是文件或现存目录（目录里写 `texts.json`），相对路径按当前工作目录解析。持久输出已存在时会退出 2，只有显式加 `--force` 才覆盖。并行检查各用不同的 `--out`；不写 `--out` 的普通检查会各用自己的临时快照。HyperFrames 的 `--export` 仍默认写项目根的 `texts.json`。

## 守硬规则 1

- 随机一律用 `hash(i)`、`hash2(i, j)`、`noise1(x)`；不用 `Math.random`、`Date`、`performance.now`，不在帧和帧之间留状态。
- 只画一次就反复用的东西（`texture()`、颗粒的噪点块、转场的离屏画布）只依赖自己的参数，命中缓存和重画一遍是同一个结果。`texture()` 常常第一次画在 `ready` 的抽样里，那时宿主还没把时钟钉在某个 t 上，所以里面更不能用 `Math.random`、`Date`。
- `frame(t)` 每次先 `reset()` 画布，上一帧哪怕中途抛错留下的状态也会清掉。
- 实测（2026-10-11，M3 Max，`bin/vh frames` 用的 chrome-headless-shell 150）：1080p 下同一个 t 单独画、先画别的帧再画（包括转场中的帧），PNG 逐字节相同。4K（`--dpr 2`）在 GPU 上，先画过别的帧再画，标题字形里有几个像素差 1 级（看先画哪一帧，PSNR 107–119 dB，远高于 45 dB 的线）；同样的顺序跨启动逐字节相同，加 `--soft-gl` 时不管顺序都逐字节相同。

## 可选模块

下面两个模块不设就不起作用：不写 `FILM.music`、`FILM.timemap`，片子照旧按旁白时间走，两份文件留着无妨，也不用读。需要时再看：配乐撑着的片子用小节表，数据有自己的轴（日期、步数、旧版的秒数）时用时间映射。

### 配乐主导片：只维护一份小节表

`bin/vh music` 生成的 `audio/music.beats.json` 是时间来源，默认 4/4 也会带 `bars`。需要音符驱动画面时，在谱子的相应声部设 `"note_map": true`。旧 beats 文件没有 `bars` 时重新生成，不从 BPM 猜一份小节表；`bin/vh beats` 分析外部音频得到的拍点也不等于乐谱小节。

```js
Object.assign(FILM, { timeline: false, music: "audio/music.beats.json" });
// 没有旁白且 duration 为 0 时，片长直接取 music.beats.json 的 duration（已含配乐尾音）。
const CHAPTERS = [{ at: musicAt(1), title: "开场" }, { at: musicAt(3), title: "变化" }];
const SHOTS = [
  { id: "intro", at: 0, draw(t, s) { /* 画开场 */ } },
  { id: "S04a", at: musicAt(3), o: { hit: musicAt(3, 2, -0.1) },
    draw(t, s) {
      const at = musicT(3, 2);  // ready 后查询秒数；第 3 小节、第 2 拍
      const hits = musicNotesT("piano"); // 声部 id；音符实际起音秒数，含 humanize
      // 用 at、hits 或 s.o.hit 驱动画面；musicNotes("piano") 还能取 end/midi/vel
    } },
];
```

小节和拍都从 **1** 开始，拍可以是小数；`musicAt(3, 2, -0.1)` 表示该拍前 0.1 秒。声明先于异步数据加载，须用 `musicAt()` 留下引用；在 `draw()` 内才用 `musicT()` 查询秒数。镜头的 `at`、`o` 内的时间、章节、封面和 `FILM.bar` 都支持这种引用。超出已有小节、拍数或已渲音乐时长会报错，不静默夹到结尾。每小节的“拍数 + 1”可表示它的结束边界。音符查询返回该声部的数组；没有匹配音符时为空，整份表没生成 `notes` 时提示重新生成。

有旁白时仍按原先的 timeline + lead + tail 定片长，音乐只提供附加挂点。音乐的秒数已经位于文件里的时间位置，不再叠加 beats 文件的 `offset` 或旁白的 `FILM.lead`。无旁白时显式 `FILM.duration` 可覆盖音乐片长；不写就跟随音乐。改谱后先重跑 music，再取帧；`bin/vh cues --save` 同时保存实际加载的音乐表路径、SHA-256 和解析结果，下一次会提示音乐表变化。

项目里的 Python 音效生成脚本可复用同一份数据：把仓库根目录加入 `PYTHONPATH`，然后 `from tools.audio.music_clock import MusicClock`，用 `clock = MusicClock.load("audio/music.beats.json")`、`clock.at(3, 2, -0.1)` 和 `clock.notes("piano")`。它只依赖 Python 标准库，编号和边界规则与画面相同。这个入口不自动改写已有 events.json；生成脚本需改用它并重跑。

旧项目按需迁移：添加 `src/05-music-clock.js` 及其 script 标签，并更新 `00-core.js`、`90-main.js` 中的音乐接线；项目已修改过的引擎文件要按差异合入。原来的旁白 cue 和绝对秒数仍可用。

### 时间映射：数据的轴和事件也只维护一份

数据片的时间常常不是旁白也不是小节，而是数据自己的轴：日期一天天往前走，事件处放慢，读完字卡再走。这条曲线由项目自己的脚本解一次，写成一份时间映射文件；画面、字卡、封面和音效都从它取时刻，不各自手写秒数，也不在 2D 和 3D 层各写一份换算。

```json
{ "version": 1, "axis": { "kind": "number", "unit": "step" }, "rebuild": "python3 data/make_map.py",
  "knots": [[2, 0], [4, 10], [6, 10], [10, 30]],
  "events": [ { "id": "e1", "u": 10, "t": 4, "lane": "top", "text": "第一件事" },
              { "id": "e2", "u": 20, "t": 8, "end": 9, "data": { "side": "left" } } ] }
```

- `knots` 是 `[t, u]`：t 是片子秒数，一个比一个大；u 是轴上的位置，不往回走，相邻两点 u 相同就是**停留**（轴停住、片子照走）。两点之间是直线，曲线要多平滑由写文件的脚本把点采多密。
- 轴：`"kind": "number"`（默认）、`"seconds"`（例如旧版片子的秒数，用来整片放慢、局部加快），或 `"date"` 加 `"origin": "YYYY-MM-DD"`，u 是距 origin 的天数。
- 事件：`id` 用字母、数字和 `_`，不重复；`t` 要落在折点给的位置上（停留里任何一刻都行）；`end`、`lane`、`text`、`data` 可选，原样给画面用。id 最好用改稿时不会变的内容拼，不用序号或标题。
- 可选：`"sources": [{ "path", "sha256" }]` 记下它是按哪份旁白时间轴或 beats 解的（路径相对映射文件），`"rebuild"` 写重建它的命令。页面载入的时间轴或 beats 和记下的不一样时，`ready` 失败，报错里带上这条命令。

```js
Object.assign(FILM, { timeline: false, duration: 12, timemap: "data/time.map.json" });
const CHAPTERS = [{ at: 0, title: "开场" }, { at: mapAt(20), title: "后半" }];   // 轴第一次走到 20 的时刻
const COVERS = [{ id: "main", at: "@#e2" }];
const SHOTS = [
  { id: "S01", at: 0, draw(t, s) { /* … */ } },
  { id: "S02", at: "@#e1-0.5", o: { hit: "@#e2" },
    draw(t, s) {
      const u = mapU(t);                   // 此刻轴走到哪：数据画到这里
      for (const e of TIMEMAP.events) if (e.lane === "top") { /* 字卡从 e.t 起，读时用 read() 登记 */ }
      const speed = TIMEMAP.rate(t);       // 每片子秒走多少轴单位，例如"天/秒"
    } },
];
```

- 引用：`"@#e1"` 是事件的时刻，`"@#e1>"` 是它的 `end`，都可以加 `+0.3`、`-0.2`；`mapAt(u, offset)` 是轴第一次走到 u 的时刻（日期轴写 `"YYYY-MM-DD"`）。镜头的 `at`、`o`、章节、封面和 `FILM.bar` 都认，和旁白 cue、`musicAt()` 一样在 `ready` 时一次换成秒。
- `draw()` 里查：`mapU(t)`、`mapT(u)`、`eventT(id, "end")`，或者直接用 `TIMEMAP`（`.u`、`.t`、`.at`、`.dur(u0, u1)`、`.rate(t)`、`.day(iso)`、`.events`）。Three.js 层的模块按名字读同一个 `TIMEMAP`。映射在 `ready` 时载入后冻结，每帧只是查表，仍是 t 的纯函数。
- `bin/vh cues --save` 同时记下实际载入的映射路径和 SHA-256，下一次说出哪些挂点挪了，并提示"time map changed"。不进页面的检查：`bin/vh timemap check data/time.map.json`（列出事件，查记下的 sources 还对不对，和上次 `--save` 的比谁挪了）。
- 折点怎么解由项目定，可以自己写脚本。改一处（一条事件的标题变长、删一条事件）又不想挪已定的落点时，把已定的事件当定点，只在相邻两个定点之间重新分配时间，定点外的折点原样保留；改完 `bin/vh timemap check` 和 `--save` 时的那份比，看谁挪了。
- 仓库里的 `engines/canvas-film/examples/time-map-solve.py` 是一个解法的例子（只用标准库，旁边是一份合成的规格 `time-map-spec.json`），复制到项目里照着改：事件处的高斯减速在跨度边上截断、慢窗、停留、字卡读时按车道查，以及上面说的定点。它不是 `bin/vh` 的命令，策略和参数都归项目。
- 音效、混音用同一份映射：events.json 加表头以后，`t` 可以写 `"@#e1"`（`tools/audio/README.md` 的"音效"）。Python 脚本：`from tools.audio.time_map import TimeMap`，用法和 JS 相同。

旧项目要用时间映射：复制 `src/06-time-map.js` 并在 `film.html` 里 `05-music-clock.js` 之后加它的 script 标签；`00-core.js` 合入 `FILM.timemap`、`cueT` 里的 `@#` 分支和 `resolver` 里的 `$map`；`90-main.js` 合入 `boot()` 里的 `loadTimeMap()`、`checkTimeMapSources()` 和 `window.film.timemap`。不设 `FILM.timemap` 时什么都不变。

## 局限

- 只有 16:9。别的画幅要同时改 `FILM.width`、`FILM.height` 和 `film.html` 里的尺寸，`bin/vh textcheck` 也还是按 1920 × 1080 打开页面。
- SRT 还没有导出；镜头表通过 `window.film.shots` 给 storyboard/rhythm，不自动保存为 `shots.json`。
- 没有 Three.js 底层。
- 引擎自己切字幕时不按词切；按词切要先跑 `bin/vh captions --cards`，见"字幕"。
- 录制器只看得到每镜 5 个时刻画到的东西：一个只在两个时刻之间才调用的 `cue()` 或 `read()` 会漏掉。把它们写在 `if` 外面，先登记，再判断这一帧要不要画。
