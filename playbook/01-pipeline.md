# 01 十阶段流程（阶段 0–9）

## 总表

下表是 `standard` 档位的做法。`quick` 会省掉人工关卡、独立评审和大部分逐场景自查；`studio` 会加上 look-dev、animatic 和多轮打分。各档位具体做多少，见 CLAUDE.md 的"努力程度"一节（`bin/vh effort <档位>`）。

| 阶段 | 产物 | 工具 | 通过条件 |
|---|---|---|---|
| 0 选路径 | — | `00-paradigm.md` 的选型表和 `video-types/` | 能说清验收标准 |
| 1 Brief + 大纲 | `BRIEF.md`（受众、平台、时长、画幅、fps、有无声音、验收项）+ 3–7 段大纲 | `templates/BRIEF.md` | **人工关卡 ①** |
| 2 风格 | `STYLE.md`：调色板、字体、缓动、安全区或锚点网格、禁止项 | `templates/STYLE.md` + 类型文档 | 一页纸能讲清 |
| 3 脚本与分镜 | `SCRIPT.md`（有旁白时写，关键词标 `{cue}`）、`STORYBOARD.md`（每镜的时间、reads、转场）、分镜预览图 `out/check/storyboard.png`；节奏要紧的片子再加一版 animatic `out/animatic.mp4` | `templates/STORYBOARD.md` | 每镜都有事件，reads 不重叠；**人工关卡 ②** |
| 4 音频先行 | `audio/*`、`timeline.json`（词级时间）、`beats.json` | 见 `04-audio.md` | 用实测时长回写分镜 |
| 5 搭引擎 | 渲染脚本、公共库（hash、ease、keyframe、camera、pulse），先做一个样板场景 | `engines/README.md` | 乱序跳到同一帧，结果一致 |
| 6 写场景 | 每个场景一个文件；长片按 chapter 分给多个 subagent | Claude Code subagents | 每个场景都过 lint、sheet、strip、crop |
| 7 Review | `out/check/*.jpg` 和 `NOTES.md` 里的评分记录 | 全新上下文的 reviewer subagent，对照 `TASTE_CHECKLIST.md` | 20 条全 PASS；整片 draft 的打分层七个维度都 ≥ 8，至少 3 轮 |
| 8 渲染 | 先出 draft，给人审阅后再出 final | 并行 worker；ffmpeg 合成，加 `loudnorm` | `ffprobe`、`blackdetect`、`freezedetect` 都通过；**人工关卡 ③**（draft） |
| 9 交付 | mp4、源码、渲染命令、素材台账、`LESSONS.md` | — | 用户完整看一遍、听一遍 |

## 项目目录约定

```
projects/2026-10-01-leo-doppler/
├── BRIEF.md  STYLE.md  STORYBOARD.md  SCRIPT.md  NOTES.md  LESSONS.md  TASTE_CHECKLIST.md
├── audio/            voiceover.wav、bgm.mp3、timeline.json、beats.json
├── assets/           图片、字体、图标（记录来源和许可）
├── src/ 或 compositions/ 或 scenes/   场景代码（结构按引擎惯例）
├── out/check/        联系表、strip、crop
└── out/final.mp4
```

## reads：节奏的计量单位

这个概念来自 ClaudeAnimationBase 的 `ANIMATION_GUIDE.md`，是整个流程里最值得掌握的一条。

一个 read 是观众必须看懂的一条信息。每个镜头按顺序列出它的 reads，每条标出起止时间。每条 read 都需要时间让观众"找到 → 看懂 → 消化"，而且两条重要的 read 不能同时发生。

原文的说法是：reads 就是 timing sheet。镜头的长度由 reads 决定：reads 放不下就把镜头加长或删掉一条 read，不要硬挤。

几条推论：

- **快动作，慢含义**：动作本身可以很快，前提是有预备动作提示观众往哪看；动作之后要留出停顿，让观众理解它意味着什么。
- **先把视线引过去**：观众会看正在动的、亮的、大的，或者角色正在看的东西。重要的 read 出现之前，先把视线引到那个位置。
- **一次只讲一件事**：原因和反应要依次发生，不要叠在一起。

反例：demo 结尾的第一版把 7 个 reads 塞进 1.3 秒，没人看得懂发生了什么；拉到 4 秒后才成立。模型最常犯的错误就是节奏：所有东西一个速度，事件一个压着一个，没有停顿。

## 三道人工关卡

人的判断力最值钱的地方，是在改动还便宜的时候。按 `templates/REVIEW.md` 给出审阅包，然后停下来：

1. **大纲（关卡 ①）**：视频是什么、给谁看、多长、什么风格，再加 3–7 段大纲。不确认就往下做，后面几乎所有工作都可能白做。
2. **分镜（关卡 ②）**：逐镜头的画面、reads 和转场，外加一张**分镜预览图**，每镜一张关键帧，可以是草图或灰盒。人看图比读文字快得多。改分镜只要几分钟，改写好的代码要几小时。节奏要紧的片子（卡配乐、有旁白、长于约 30 秒），这一关再附一版 animatic，做法见下。
3. **初版（关卡 ③）**：draft 成片加联系表。agent 要主动说出自己最不满意的 2–3 处，并给出可选的修法，比等人来挑更高效。

每一关，人的意见都逐条记进 `REVIEW.md`。只有用户明确说"不用审、直接出"才能跳过，做法见下面的"授权的无人值守模式"。跳过也不等于不写这些文件：BRIEF 和 STORYBOARD 仍然是后续自查的依据。

### animatic：打磨之前先定节奏

animatic 是整片长度的灰盒预演，属于阶段 3，放进关卡 ② 的审阅包，不是一个新阶段。

- **怎么做**：960×540，draft 质量。几何块代替真素材，字用最终文案、按最终比例的字号，镜头运动和切点按分镜走。配上真实音频，没有就用占位音频（节拍器、临时配乐、TTS 草稿）。
- **看什么**：只看节奏，不评审美。每条 read 来不来得及读完？哪里拖？哪里挤？对照 `STORYBOARD.md` 的 reads 表逐镜读一遍。
- **为什么值得**：reads 的时长只有放到真实速度下才看得准，而在灰盒阶段改节奏只是改时间表；等到画面打磨完再改，就要改代码、重渲。
- **之后**：通过后，animatic 的时间线就是阶段 5–6 的骨架，场景代码往里填，时间点不再手改。

### look-dev：意见说不清时，先给变体

人的意见常常是"不够炫酷""感觉不对"，说不出具体要什么。这时不要猜着改全片：

- 挑最能代表全片的一段，10–20 s；
- 只用一个预设变量切出 2–3 个变体，例如 HyperFrames 的 composition 变量 `fx` = A / B / C，渲染时用 `--variables '{"fx":"B"}'` 切换；同一段音频，其他都不变；
- 附一张对照联系表：每行一个变体，每列是同一个时刻；
- 人挑一个方向，再按选中的那档做全片。

变体之间只差一个变量，人挑的是方向，不用描述细节。本仓库介绍片的 v3 就是这样做的：先用 `fx` = A / B / C 渲了一版 22.7 s 的 look-dev（12 s 片中段落加 10.7 s 新做的产品信息图），选定 B 档之后才重构全片。

### 授权的无人值守模式

用户可以授权 agent 跳过关卡、一口气做到成片，比如让它通宵做，第二天早上直接看成片。规则如下：

- **只认用户本人的原话。** 必须是用户在对话里明确说的；协调者或别的 agent 转述的不算。subagent 收到"直接做完"的转述时，由持有原话的主会话去记录授权。
- **原话逐字记进 `REVIEW.md`**，写在每道被跳过的关卡下，附日期和范围（跳哪几关）。格式见 `templates/REVIEW.md` 文末。
- **独立 reviewer 代审。** 被跳过的关卡由全新上下文的 reviewer 代替人来审：`02-verification.md` 第 5 层的人设，TASTE_CHECKLIST 的 20 条加打分层。每轮的问题和修法记进 `NOTES.md`。
- **交付时说清楚**哪些关卡是代审的。用户看完成片的意见照常记进 `REVIEW.md`，之后回到正常流程。

本仓库的介绍片是一个例子（项目在 `projects/` 下，不入库，这里只描述）：关卡 ① 之后，用户在对话里说"你自己做好 早上9点我希望能看到成片"。关卡 ②③ 由协调者和两轮独立 reviewer 代审，第一轮的结论是"修完才能发"，第二轮是"小修即可发"。REVIEW.md 里记着原话、日期和代审记录。用户看完成片后的意见按正常流程处理，见文末"多轮迭代是常态"的最后一条。

## 长片：用 subagent 并行

这是 PDoom（9 个 chapter）和 Functional Emotions（7 个 subagent）实际用过的模式：

1. **主 agent（director）先写三份契约**：`STORYBOARD.md` 和 `ANIMATION_GUIDE.md`（画布、调色板、API、禁止项、安全区），加上共享库。
2. **主 agent 亲手做第一个 chapter**，当作参考样板。Functional Emotions 就是先重做 chapter I，再派其余的。
3. **每个 subagent 负责一个 chapter**，只改自己的文件。发现共享文件有 bug 时报告给主 agent，不自己改。
4. **主 agent 看每个 chapter 的联系表**，写批注退回修改，满意才验收。
5. **每个 chapter 的首尾各 0.5 秒**要和相邻 chapter 对齐：方向、颜色、转场都要衔接上。

给 subagent 的指令要自包含。写清楚这几项：chapter 的时间范围、对应分镜段落、要读的契约文件、只许改哪个文件、自查预算、交付时要附上哪些联系表。

## 多轮迭代是常态

没有一个优秀案例是一轮做完的：

- **PDoom** 做了两轮：第一轮只给歌词和音频；第二轮提高 effort，要求用 p5 笔刷，每镜都要有趣，而且每镜都要衔接下一镜。
- **Functional Emotions** 第一版是精致的排版歌词视频，被否掉了，理由是"还是歌词视频"。用户第二次要求"要真正的 MV，歌词不是主角"；第三次拿 PDoom 当节奏参考，推动"别让画面静止太久"。
- **mexicat** 的版本也"调了几轮"。
- **本仓库的介绍片**：v2 逐条过了 TASTE_CHECKLIST，也过了两轮独立评审，用户看完仍说"不够炫酷"，还听出音乐有几处像卡住。v3 先修音频、做 look-dev，再重构全片。这也是 TASTE_CHECKLIST 加了打分层的原因。

给用户交付 draft 时，主动说出你自己最不满意的两三处，比等用户来挑更高效。
