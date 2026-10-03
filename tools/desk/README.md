# 审阅台（bin/vh desk）

审阅台是一个本地网页：人在页面里逐条勾选"可以 / 要改 / 疑问"、写一句、提交；agent 在后台等着，人一提交就接着做。它是 `studio` 档位默认的审阅界面，`standard` 想用也可以（什么时候用、agent 怎么挂等待，见 `playbook/01-pipeline.md` 的"审阅台"）。这一页讲它读什么、写什么，也就是项目文件要怎么写，审阅台才排得出来。

**文件是唯一的事实来源。** 审阅台每次刷新都从项目文件重新读，自己不存状态；人的草稿只留在浏览器里，提交以后才落进项目。读不出结构的文档不会被藏起来：每份文档都在"文档"页原样排版，结构化的页面空着时，就地显示那份文档的原文，"文档"页顶上列出哪些没按约定读出来。

## 命令

```bash
bin/vh desk <项目> [--port N]                  # 起服务，只听 127.0.0.1；默认 8780–8799 里第一个空闲端口；这个项目已经有一个在跑，就只打印它的地址
bin/vh desk wait <项目> [--timeout 秒]          # 等人提交：打印反馈，退出码 0；超时退出码 3（默认 7100 s）
bin/vh desk feedback <项目> [--round 1b] [--json]   # 打印最近一次提交，并记为"已交给 agent"
bin/vh desk data <项目>                        # 审阅台从项目里读出了什么（JSON），排查"为什么这一页是空的"时用
```

只用 Python 标准库，不联网，页面不从 CDN 拉任何东西，浅色和深色都有，界面有中文和英文。

## 读什么

表格按表头的**开头几个字**认列（中英文都行，英文不分大小写），列的顺序随意，多出来的列不管。

### BRIEF.md

| 位置 | 读什么 | 英文项目 |
|---|---|---|
| 第一行 `# BRIEF：片名` | 片名 | `# BRIEF: title` |
| `## Spec` 的 `- 键: 值` | 全部列出；`Effort`、`Review language`（`zh` / `en`，界面语言；这一轮的 gate JSON 写了 `lang` 时以它为准，和 `bin/vh review` 同一条规则）、`Output`、`Watch on` 放在立意卡上 | 同左 |
| `## Content` 的 `- 键: 值` | `Concept (one line)`、`Spine (one line)`、`Recurring motif`、`What the viewer should know/feel at the end`；`Specifics` 下面缩进的几条 | 同左 |
| `## Outline`（或 `## 大纲`）里的表 | 每段一行，见下 | `## Outline` |

大纲表的列：

| 列（开头是） | 用途 | 英文 |
|---|---|---|
| `#` | 段号；不写就按顺序编 | `#` |
| `段落` | **段名，按内容或阶段起**（"按下发送""信道编码与调制"） | `Segment` |
| `标签` | 可选的小标签，起承转合、幕之类，显示在段名旁边的小框里 | `Tag` |
| `环节` / `阶段` | 可选，这一段讲的环节 | `Stage` |
| `时间` | `0–10 s`、`1:30–1:52`；时间条按它画 | `Time` |
| `小节` | `4–7`；没有"时间"列时，用配乐的节拍表换成秒 | `Bars` |
| `观众` | 观众看完知道 / 感到什么 | `Viewer`、`Takeaway` |
| `关键画面` / `画面` | 关键画面 | `Key visual`、`Visual` |

旧写法的段名"承 · 发出去"会拆成标签"承"和段名"发出去"。

### SCRIPT.md

第一张带 `字幕`（字幕稿）或 `旁白`（旁白稿）列的表。

| 列（开头是） | 用途 | 英文 |
|---|---|---|
| `#` | 条目编号，点评按它记 | `#`、`ID` |
| `段` / `段落` | 属于大纲哪一段：写段名或段号；对不上时按时间归段 | `Segment` |
| `时间` 或 `小节` | 同大纲 | `Time`、`Bars` |
| `术语` | 可选，术语卡上的词（`video-types/02` 的"术语卡"） | `Term` |
| `字幕` / `旁白` | 正文；读速按"这一条占的时间"粗算 | `Caption`、`On-screen`、`Narration`、`VO` |
| `画面` | 画面 | `Visual` |
| `素材` | NOTES 素材清单的编号（`#2 #4`） | `Facts`、`Source` |

### NOTES.md

- `## 素材清单` 里的表：`#`、`素材`、`类别`、`上屏说法`（可选）、`出处`。不再用的素材整格划掉 `~~…~~`（老写法"（关卡 ① 后不用）……"也认），事实核对页把它淡化、不给点评。英文：`## Material`，列 `#`、`Item`、`Kind`、`On screen`、`Source`。
- `## 待核实的事实` 里的 `- [ ]` / `- [x]`。英文：`## To verify`。

### DECISIONS.md

- 表头以 `决定` 开头的表：`决定`、`谁拍板`、`状态`、`在哪看`（导演模式的账本）。英文：`Decision`、`Who`、`Status`、`Where`。
- `## agent 定的事` 下的每条 `- 日期 话题 · 定了什么 — 理由：… — 翻案：…`，中间可以有 `###` 小标题（显示成分组）。**作废的整行划掉**，后面写原因：`- ~~2026-10-03 style · 夜色画面 — 理由：…~~（关卡 ① 后作废）`，审阅台把它收进"已经作废的"，不再给"翻案"按钮。英文：`## Decided by the agent`，`— why: … — undo: …`。

### REVIEW.md

每个 `## ` 小节是一轮：`- 原话（说明）："……"` 是人的原话，`- 定了：…`、`- 改了：…`（同一行写 `定了：A　改了：B` 也行）是之后的处理。只有空占位的小节（模板里还没填的关卡 ②③）和模板最后两节参考文字不算历史。标题以"暂停"开头、又没写"恢复"的小节，让顶栏显示"暂停"。英文：`- Verbatim: "…"`、`- Decided: …`、`- Changed: …`，`Paused`。

### shots.json

和 `bin/vh storyboard` 同一份（格式见 `bin/vh storyboard -h`）：一个列表，或 `{"video", "note", "shots": [...]}`；每镜 `id`、`start`、`end`、`segment`、`label`、`reads`、`caption`、`transition`、`unsure`、`frame`。关键帧取 `frame`，没有就取 `bin/vh storyboard` 写的 `out/check/storyboard/frames/<id>.png`。分镜页播放的视频：`shots.json` 的 `video`，否则最新审阅页的 `animatic`，否则 `out/animatic.mp4`、`out/draft.mp4`。

### out/review/gate-<n>.json

和 `bin/vh review` 是同一份文件，字段见 `playbook/01-pipeline.md` 的"审阅页"（`include` 照样生效）。"这一轮"是按流程排在最后的那一页：先按站（1、E0、E1、2、E2、E3、E4、3、E5），同一站再按页（1、1b、1c……）；不合这个写法的页名排在最前，彼此之间才看修改时间。所以复制项目、碰一下旧文件，都不会让已经过去的一页变回"这一轮"。审阅台另外认几个可选字段，`bin/vh review` 不管它们：

```json
{
  "listen": [{"t": 9.4, "note": "17 个字飞出手机：每个字一个八音盒的音"}],
  "music": {"audio": "audio/film_mix.wav", "beats": "audio/film.beats.json", "roll": "audio/film.roll/overview.png",
            "labels": {"type": "打字", "send": "发送"}},
  "film": "out/review/open-F2.mp4"
}
```

- `listen`：声音页的"请你听这几处"，`t` 是秒。
- `music`：声音页播哪条音轨、读哪份节拍表、乐段在色块上叫什么（`labels` 把乐段的 `name` 换成人看得懂的名字）。不写时，读 `audio/` 里最新的 `*.beats.json`，音轨取同名的 `*_mix.wav`，没有再取 `*.wav`，谱面取同名的 `.roll/overview.png`。节拍表也用来把"小节"换成秒。
- `film`：逐秒点评页放哪支视频；不写就用 `assets` 里第一支视频。时长从视频本身读。

路径都相对项目目录；审阅台只给项目目录里的文件（不给隐藏文件，不出项目目录）。

## 写什么

提交后，服务按这个顺序写：

1. `out/review/feedback/<轮>-<YYYYMMDD-HHMMSS>.md`：一条一行的文字版，人的话原样不动；
2. `REVIEW.md`：插一节 `## 审阅台反馈 · 关卡 <轮> · <日期 时间>`，把上面的文字整段原样放进代码块，下面留一行"定了：　改了："给 agent 填；插在模板的"授权跳过怎么记"之前，没有这一节就接在文末；
3. `out/review/feedback/<轮>-<YYYYMMDD-HHMMSS>.json`：最后写，原子替换。`bin/vh desk wait` 等的就是它。同一秒里的第二份、第三份加 `-2`、`-3`，按数字排。

交给 agent 的提交记在 `out/review/feedback/.consumed`：`bin/vh desk wait` 打印过的、`bin/vh desk feedback` 打印过的，都算交过了。`wait` 一启动，先看这一轮有没有还没交过、又晚于这一页 gate JSON 的提交（比如上一次 `wait` 超时之后人才提交），有就立刻打印、退出 0；没有才开始等新的。`.listening`（有 agent 在等）和 `.desk.json`（服务在跑）里都记着项目目录的完整路径，从别的项目拷来的这两个文件不算数。

JSON 的格式：

```json
{
  "round": "1c", "lang": "zh", "project": "2026-10-01-glass-of-water", "submitted_at": "2026-10-04T02:38:50",
  "decisions": {"look": "F2"}, "defaulted": [],
  "items": [
    {"target": "seg:9", "status": "change", "label": "大纲 第 9 段 这一次", "text": "这个压根没有升华主题……"},
    {"target": "cap:c11", "status": "change", "label": "字幕 c11", "text": "", "orig": "信号好，一次装 8 个；信号差，只装 2 个。", "suggest": "……"},
    {"target": "time:12.4", "status": "ask", "label": "小样 0:12.4", "text": "这里看不清", "t": 12.4}
  ],
  "general": "大体可以"
}
```

- `decisions`：这一页每个决定选了哪个选项；`defaulted` 列出人没动、按推荐算的。
- `items[].status`：`ok` 可以、`change` 要改、`ask` 疑问。没标的条目都算通过。
- `items[].target` 的前缀说明点评的是什么：`dec:` 决定、`least:` 没把握的、`deleg:` 替人定的（gate JSON `delegated` 的序号）、`concept:line` 立意、`seg:` 大纲段、`cap:` 字幕或旁白条、`shot:` 镜头、`fact:` 素材、`time:` 小样的某一秒、`atime:` 音轨的某一秒、`led:` DECISIONS 里 agent 定的事（序号）、`doc:<文件>#<小节>` 文档的某一节。
- `suggest` 是人直接写的"改成"，`orig` 是原句。

服务会检查：轮次对得上一份 `gate-<轮>.json`（还没有审阅页时用 `notes`），决定和选项都在那一页里，每个字段的类型、状态和 target 合法，单条文字不超过 4000 字、整份不超过 256 KiB，正文和 Content-Length 对得上；不合的回 400，不会断开连接。

## 安全

- 只绑定 127.0.0.1，只回答 Host 是自己的请求（挡住 DNS rebinding）。
- 提交要带页面里那一次启动生成的令牌、JSON 格式，浏览器带了 Origin 时必须是同源；所以同一个浏览器里别的网页既读不到项目，也没法冒充人提交反馈。
- `/p/` 下的每个文件都带 `Content-Security-Policy: sandbox allow-scripts allow-popups`（没有 `allow-same-origin`）：项目里的 HTML、SVG（HyperFrames 的 `index.html`、`node_modules` 里的页面、下载来的参考图）在浏览器里打开时是一个不透明的源，脚本照样能跑，但读不到审阅台的页面和令牌，也没法替人提交。
- `/p/` 只给项目目录里的普通文件：不出目录、不跟着符号链接出去；隐藏文件和 `*.env` 不给，按请求的名字和解析后的真实文件各查一遍，不分大小写（指向 `.env` 的链接、`keys.ENV` 都不给）。
- 每个连接 30 s 不动就断开，发了一半的请求不会一直占着线程。

## 测试

`tools/ci.sh` 用 `tools/desk/fixtures/` 里的两个小项目（中文、英文）测读取（包括读不出表格时退回原文、"这一轮"的顺序、语言规则、超长和深层嵌套的 markdown），在空闲端口起一个服务测 `/api/data`、206 Range、`/p/` 的 sandbox、各种拒绝和坏请求、提交到临时副本、REVIEW.md 的追加，测 `wait` 在有提交时退出 0、启动前就到的提交立刻交出、交过的不再交，拷来的 `.desk.json` 和 `.listening` 不算数，以及 `bin/vh desk -h`。
