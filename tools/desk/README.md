# 审阅台（bin/vh desk）

审阅台是一个本地网页：人在页面里逐条勾选"可以 / 要改 / 疑问"、写一句、提交；agent 在后台等着，人一提交就接着做。它是 `studio` 档位默认的审阅界面，`standard` 想用也可以（什么时候用、agent 怎么挂等待，见 `playbook/01-pipeline.md` 的"审阅台"）。这一页讲它读什么、写什么，也就是项目文件要怎么写，审阅台才排得出来。

**文件是唯一的事实来源。** 审阅台每次刷新都从项目文件重新读，自己不存状态；人的草稿只留在浏览器里，提交以后才落进项目。读不出结构的文档不会被藏起来：每份文档都在"文档"页原样排版，结构化的页面空着时，就地显示那份文档的原文，"文档"页顶上列出哪些没按约定读出来。

## 命令

```bash
bin/vh gate <项目> <n> [--desk|--page|--chat] [--wait]   # 一次停一条命令：查 gate-<n>.json，出静态页并记成这一轮，审阅方式是审阅台时在后台起服务（12 小时没人访问自己停），打印聊天消息；--wait 再像 desk wait 一样等
bin/vh desk <项目> [--port N] [--idle 秒]       # 起服务，只听 127.0.0.1；默认 8780–8799 里第一个空闲端口；这个项目已经有一个在跑，就只打印它的地址；--idle：这么久没人访问就自己停
bin/vh desk wait <项目> [--timeout 秒]          # 等人提交：打印反馈，退出码 0；超时退出码 3（默认 7100 s）
bin/vh desk feedback <项目> [--round 1b] [--json]   # 打印最近一次提交，并记为"已交给 agent"
bin/vh desk data <项目>                        # 审阅台从项目里读出了什么（JSON），排查"为什么这一页是空的"时用
```

只用 Python 标准库，不联网，页面不从 CDN 拉任何东西，浅色和深色都有，界面有中文和英文。

`bin/vh gate`（`tools/gate.py`）把一次停要做的事做完：审阅方式取 `--desk` / `--page` / `--chat`，没有就取 `LOCAL.md` 的"审阅方式"一行，再没有就按档位（`studio` 审阅台，`standard`、`quick` 静态页）。每种方式都出静态页、打印聊天消息；审阅台方式再起服务，把地址加进消息。退出码：0 发出去了（`--wait` 时是收到了提交）；1 页面写了但不合规矩，不发消息也不起服务；2 没东西可发（没有 gate JSON、服务起不来、不是审阅台却要 `--wait`）；3 `--wait` 超时。

**一站的数据就是 `out/review/gate-<n>.json` 这一个文件。** 静态页（`bin/vh review`）、审阅台和以后的客户端都只渲染它（审阅台另外读下面这些项目文件），各自不另存一份。

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

和 `bin/vh review` 是同一份文件，字段见 `playbook/01-pipeline.md` 的"审阅页"（`include` 照样生效）。"这一轮"是 `bin/vh review <项目> <n>`（`bin/vh gate` 也一样）最后做的那一页：它每次把页名写进 `out/review/.current`，审阅台和 `bin/vh desk wait` 都先读它。所以关卡 ② 之后回头出一页立意 `1b`、关卡 ③ 之后重定配音出 `E3b`、自己起名的 `final`，都会是"这一轮"。`.current` 没有，或者它指的那一页已经删了，才按流程顺序取最后一页：先按站（1、E0、E1、2、E2、E3、E4、3、E5），同一站再按页（1、1b、1c……，不分大小写）；不合这个写法的页名排在最前，彼此之间看修改时间。复制项目、碰一下旧文件，都不会改变哪一页是"这一轮"。`bin/vh review <项目>` 不写页名时，渲染的也是这一轮；要出新的一页，写上它的名字。页名是 1–24 个字母、数字、`-` 或 `_`，按磁盘上文件本来的写法算（APFS 不分大小写：写 `1D` 找到的是 `gate-1d.json`，这一页就叫 `1d`）；链接到项目外面的 gate 文件不读。审阅台另外认几个可选字段，`bin/vh review` 不管它们：

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
    {"target": "time:12.4", "status": "ask", "label": "小样 0:12.4", "text": "这里看不清", "t": 12.4},
    {"target": "range:20-24.5", "status": "change", "label": "小样 0:20.0–0:24.5", "text": "这一段太慢", "t": 20, "t1": 24.5}
  ],
  "general": "大体可以"
}
```

- `decisions`：这一页每个决定选了哪个选项；`defaulted` 列出人没动、按推荐算的。
- `items[].status`：`ok` 可以、`change` 要改、`ask` 疑问。没标的条目都算通过。
- `items[].target` 的前缀说明点评的是什么：`dec:` 决定、`least:` 没把握的、`deleg:` 替人定的（gate JSON `delegated` 的序号）、`concept:line` 立意、`seg:` 大纲段、`cap:` 字幕或旁白条、`shot:` 镜头、`fact:` 素材、`time:` 小样的某一秒、`range:<a>-<b>` 小样的一段（秒，a < b；小样页按 I、O 选）、`atime:` 音轨的某一秒、`chapter:<id>` 一章、`asset:<路径>` 项目里的一件素材（相对项目的路径，不出项目）、`card:<id>` 一张立意卡、`led:` DECISIONS 里 agent 定的事（序号）、`doc:<文件>#<小节>` 文档的某一节。
- `t` 是秒；`range:` 的条目另有 `t1`，两个都按 target 里的数存，页面发来的不算。没写 `label` 的，`desk feedback` 和 REVIEW.md 按 target 起一个（"片段 0:12.4–0:15.0""章节 c2""素材 assets/a.jpg""立意卡 B"）；一段的 `label` 后面总带着它的起止。
- `suggest` 是人直接写的"改成"，`orig` 是原句。

服务会检查：轮次对得上一份 `gate-<轮>.json`（还没有审阅页时用 `notes`），决定和选项都在那一页里，每个字段的类型、状态和 target 合法，单条文字不超过 4000 字、整份不超过 256 KiB，正文和 Content-Length 对得上；不合的回 400，不会断开连接。

## 给客户端的数据

客户端（审阅台，以后的 Studio）只是项目文件和 `bin/vh` 外面的一层壳：它要的数据都由命令给出，终端里的 agent 拿到的是同一份。下面的 JSON 都带 `"version": 1`；以后只加字段，改了含义就升版本号。

### 一个项目到哪了：`bin/vh status <项目> [--json]`

只读，只看已有的文件，不开浏览器、不跑 ffprobe（`tools/status.py`，零点一秒左右）。默认几行字；`--json` 的字段：

- `project`：`path`、`slug`、`title`（BRIEF 第一行）、`type`（类型文档，如 `02-knowledge-short`）、`effort` 和 `effort_from`（BRIEF、LOCAL.md 或默认）、`director`（BRIEF 的 Director 一行）、`lang`（审阅语言）、`spec`（BRIEF 的 Spec 各行，原样的键）。
- `stations`：按流程顺序的各站。关卡 ①②③ 总在；检查点 E0–E5 有页面、REVIEW.md 有它的一节或 Director 写了 `stop=E3` 时才在；别的名字的审阅页（`final`）自成一站；最后是交付。每站：`id`、`name`、`kind`（gate、checkpoint、page、deliver）、`state`、`pages`（这一站的页名）、`page`（最新一页的路径）、`current`（是不是这一轮）、`record`（`decided`、`said`、`waived`；关卡 ① 另有 `concept_on_record`）、`feedback`（这一页之后的提交：`submitted`、`handed`、`pending`、`last`）、`note`（一句为什么）。
- `state` 六种：`done`（REVIEW.md 里有它的"定了"：先看关于最新那一页的最后一节，审阅台为提交写的那节、或写了 `gate-<n>.html` 的那节；没有这种节，就看这一站自己的节，而且 REVIEW.md 要晚于这一页）、`skipped`（quick 档、或用户原话授权跳过）、`waiting_person`（这一页是这一轮，还没有回音）、`waiting_agent`（人提交了还没交给 agent，或者交了但 REVIEW.md 还没写定了；或者这一轮已经往后走、这一页没有记录）、`in_progress`（前面都过了，agent 正朝这一站做）、`not_started`。交付：`bin/vh deliver` 写过记录，或成片（`out/final*`、`out/final/`、`media/`）有一份更晚的通过的检查记录，就是 `done`；各站都过了是 `in_progress`。
- `waiting_on`：`person`、`agent` 或 `nobody`（交付了）；REVIEW.md 写了暂停（`paused: true`）也是 `person`。`next`：一句话，谁下一步做什么。
- `review`：`current`（这一轮的页名）、`page`、`desk`（在跑时：`url`、`listening`）。
- `open`：`review_items`（审阅台提交里标了要改、疑问，而 REVIEW.md 那一节还没写定了 / 改了的条目：`round`、`file`、`target`、`status`、`label`、`text`）、`facts_to_verify`（NOTES.md 待核实里没打勾的）。
- `renders`：`out/`（往下三层）、`renders/`、`media/` 里的视频，新的在前，最多 10 个：`path`、`size`、`mtime`、`render`（`.render.json` 的帧数、帧率、像素、时间段）、`patches`、`delivery`（它是 `bin/vh deliver` 出的上传版时）、`check`（它最近的检查记录）。`deliveries`：`bin/vh deliver` 的记录。
- `check`：最近一次 `bin/vh check` 的记录摘要：`record`、`video`、`at`、`verdict`、`exit`、`counts`、`fails`（前三条）、`stale`（视频在检查之后改过）。
- `activity`：`running`（正在跑的命令）、`listening`（在跑的审阅台、`gate --wait`：是在等人，不是在干活）、`recent`（最近结束的五条），每条是下面活动记录里的一个 run。

### 活动记录：`bin/vh activity <项目> [--json] [--follow] [--limit N]`

每条作用在项目上的 `bin/vh` 命令往 `<项目>/.ovh/activity.jsonl` 追加 JSON 行；只读的 `status`、`activity`、`desk data`、`doctor` 不记，找不到项目的命令也不记。项目从参数里找：第一个是文件夹或文件（含 `--out=f`、`voice=f` 这种）的参数，往上最近的带 BRIEF.md 的文件夹；`review`、`gate`、`desk` 这些也认 projects/ 下的项目名。每行都有 `v`（1）、`event`、`t`（epoch 秒），属于某条命令的还有 `run`：

| event | 字段 | 谁写 |
|---|---|---|
| `start` | `cmd`、`args`（照打的写，名字里带 key、token、secret、pass 的选项和 `k=v` 的值、像 key 的参数都写成 `…`）、`cwd`、`pid`、`parent`（由另一条 `bin/vh` 起的） | `bin/vh` |
| `progress` | `done`、`total`、`unit`（`render`：frames，开头、每 15 s、结尾各一行） | 工具 |
| `note` | `summary`（一行）、`outputs`（写了哪些文件，项目里的写相对路径） | 工具：render、patch、review、gate、mix、qa、tts、check、`desk wait` |
| `end` | `exit`（退出码；被信号 n 停掉是 128 + n）、`duration`（秒；没有 `EPOCHREALTIME` 的 bash，比如 macOS 自带的 3.2，只到整秒） | `bin/vh` 的 EXIT trap；`bin/vh` exec 进去的工具（render、patch、frames 这些页面工具，desk、gate）自己写 |
| `feedback` | `round`、`file`、`items`（按状态计数）、`decisions` | 审阅台存下一份提交时；不属于哪条命令 |

`bin/vh` 把这条命令交给它起的进程：环境变量 `OVH_ACTIVITY_LOG`、`_RUN`、`_PID`、`_T0`、`_CMD`。不写进去的：环境变量、key、文件内容。每行一次 O_APPEND 的 write，不超过 4 KiB，几条命令同时写也不会把行写乱；写不进去（磁盘满、项目只读）就丢掉这一行，命令照常跑完、不多说一句。

`--json` 是 `{"version", "project", "log", "runs", "events"}`。`runs` 里每条命令一项：`run`、`cmd`、`args`、`cwd`、`pid`、`parent`、`start`、`end`、`exit`、`duration`、`summary`、`outputs`、`progress`、`state`。`state` 是 `running`（没有结束行，进程还在，开始不到 7 天）、`ok`（退出码 0）、`failed`、`gone`（没有结束行，进程也没了：被杀掉，或者机器重启过）。`events` 是不属于命令的行（`feedback`）。`--follow` 先打印最近的，再一行一行跟着打印新的；加 `--json` 就是原样的 JSON 行。只读日志最后 4 MB。

### 检查记录：`bin/vh check <视频> --json`

`bin/vh check` 每跑一次，都把结果存成视频所在项目的 `out/check/<名字>.check.json`（名字是文件名去掉扩展名，前面加上 `out/` 之后的文件夹：`out/review/sketch.mp4` 是 `review-sketch`；项目外的视频不存），`bin/vh clean` 留着它。`--json` 把同一份打到标准输出，给人看的那些行改去标准错误；检查本身、退出码和不加 `--json` 时一样（`tools/checkrec.py`）。

顶层：`version`、`tool`、`video`（项目里的写相对路径）、`project`、`record`、`t`、`at`、`args`（`allow`、`against`）、`exit`、`verdict`（`pass` / `fail`，和退出码一致）、`counts`（`fail`、`warn`、`info` 各几条）、`probe`（时长、大小、各条流）、`motion`（动着的帧对占比、静止占比、硬切数）、`findings`、`skipped`（没跑成的检查和原因）。读不了视频时只有 `error`。

每条 finding：`kind`、`severity`（`fail` 让退出码是 1，`warn` 要看一眼，`info` 只是说一声）、`message`、`t` 和 `t1`（秒，有时间或时间段的才有）、`frame` 和 `frames`（`[第一帧, 最后一帧]`）、`evidence`（判断依据：量到的数、BRIEF 那一行、画面的 key、确认它的那一条……）、`confirmed`（confirmed.json 盖住了是 true，能确认但没确认是 false，这一类从来不在那里确认就是 null）。没确认的孤立帧还带 `confirm`：填上 why 和 evidence 就能贴进 confirmed.json 的那一条。`kind` 用 confirmed.json 的名字：`check.spec`、`check.gate`、`check.black`、`check.freeze`、`check.silence`、`check.iso`（孤立帧；`declared: true` 是这次 `--allow` 声明的，`lapsed: true` 是确认失效了）、`check.periodic`、`check.static`、`check.cut`（从暗到亮的硬切）、`check.blind`（动得太多、扫描判断不了的一段）、`check.subtitles`、`check.colour`、`check.packaging`、`check.scale`、`check.confirmed`（confirmed.json 里没用上、失效或没收下的条目）。

## 安全

- 只绑定 127.0.0.1，只回答 Host 是自己的请求（挡住 DNS rebinding）。
- 提交要带页面里那一次启动生成的令牌、JSON 格式，浏览器带了 Origin 时必须是同源；所以同一个浏览器里别的网页既读不到项目，也没法冒充人提交反馈。
- `/p/` 下的每个文件都带 `Content-Security-Policy: sandbox allow-scripts allow-popups`（没有 `allow-same-origin`）：项目里的 HTML、SVG（HyperFrames 的 `index.html`、`node_modules` 里的页面、下载来的参考图）在浏览器里打开时是一个不透明的源，脚本照样能跑，但读不到审阅台的页面和令牌，也没法替人提交。
- `/p/` 只给项目目录里的普通文件：不出目录、不跟着符号链接出去；隐藏文件和 `*.env` 不给，按请求的名字和解析后的真实文件各查一遍，不分大小写（指向 `.env` 的链接、`keys.ENV` 都不给）。
- 每个连接 30 s 不动就断开，发了一半的请求不会一直占着线程。

## 限制

- 开着的旧页面不会自己换轮：agent 出了新的一页，人在之前打开、没刷新的标签页里提交，反馈记在旧的那一轮（那一页的 gate JSON 还在，服务照收）。页面右上角的 ↻ 重新读取。
- 几个 `bin/vh desk` 进程同时动手（比如两个 `bin/vh desk wait` 一起启动，或者一边 `wait` 一边 `desk feedback`），最坏是同一份反馈交出去两次：它们各自先看到这份反馈还没交过，各打印一遍。不会崩，也不会丢反馈：每次写文件都用自己的临时文件再原子替换，`.consumed` 的读改写在 `.consumed.lock` 上加了文件锁（flock），谁都不会把别人记下的名字冲掉。

## 测试

`tools/ci.sh` 用 `tools/desk/fixtures/` 里的两个小项目（中文、英文）测读取（包括读不出表格时退回原文、"这一轮"取 `.current`（2 之后的 1b、3 之后的 E3b、自起的页名，`.current` 指向已删的页时退回流程顺序）、语言规则、超长和深层嵌套的 markdown），在空闲端口起一个服务测 `/api/data`、206 Range、`/p/` 的 sandbox、各种拒绝和坏请求、提交到临时副本、REVIEW.md 的追加，测 `wait` 在有提交时退出 0、启动前就到的提交立刻交出、交过的不再交，拷来的 `.desk.json` 和 `.listening` 不算数，以及 `bin/vh desk -h`。
