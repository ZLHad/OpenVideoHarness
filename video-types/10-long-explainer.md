# 10 长讲解（10 分钟以上的横屏）

**适用**：
- 10 分钟以上、有旁白的横屏讲解：把一个原理讲透的长科普，把一件大事讲清来龙去脉的片子，前面讲几件真事、后面讲"这意味着什么"的思考型长片；
- 10 分钟以上的论文讲解：章节、节奏和引擎按本篇，读源文件、事实、公式和图的规矩按 `06-paper-explainer.md`。

**不适用**：
- 2–5 分钟的横屏知识片：`02-knowledge-short.md` 的"变体：抖音横屏中视频"；
- 用户自己录的讲课、口播：`09-editing-talking-head.md`；
- 单独一段数学推导：`01-math-science-explainer.md`。长片里的推导也可以单独用 Manim 做，再排进来。

## 引擎

`bin/vh new long <slug>` 建的就是 canvas-film（项目里的 `ENGINE_README.md`，和 `engines/canvas-film/README.md` 是同一份）：镜头、字幕、章节的时间挂在旁白的字上，重配一句、插一个停顿，画面跟着走，几十上百个镜头也管得住。模板里是一支示例片，开工时换掉。要 3D 镜头加 `--three`。某一章要换引擎（Manim 推导、HyperFrames 排版），单独做成页面或片子，用剪辑表 `edit.json` 排进来（`engines/EDIT.md`）。

## 工作流

长片最贵的是改：定稿之后每改一句都要重配、重渲。所以前面几步都是为了让人早看到、早改。档位和关卡照 CLAUDE.md。

1. **素材和主线（关卡 ①）**：先把数字、原话、物件和出处记进 `NOTES.md`，再定一个贯穿全片的问题。立意卡写这个问题和它的答案怎么走，不写一串知识点。大纲按内容分 8–13 章，章名要让没看过片的人也看得懂。
2. **先排"反转和钩子"表，再写稿（随关卡 ② 给人看；人点名 `script=own` 时在 E1 停）**：表头是约在几分钟、观众先信什么、接着看到什么、在哪一章，写在 `SCRIPT.md` 开头。哪一段两三分钟没有新问题，表上一眼看得出。句子的写法见 `playbook/09-narrative.md` 第 10 节；字数按 `playbook/04-audio.md` 的语速表倒推，再用配音实测。结尾早点给人看。
3. **配音先于画面**：`bin/vh tts`（要按词挂镜头加 `--align local` 或 `--align gemini`），`bin/vh timeline` 查时间轴，`bin/vh pace` 调句间停顿。长稿要查从头到尾是不是一个声音（`tools/audio/README.md` 的"整段合成"）。
4. **全片灰卡骨架（关卡 ②）**：每镜一张灰卡，整片随时能渲（`bin/vh edit init`，再 `bin/vh render`），这就是 animatic。每一帧都在的东西（章节进度条、字幕、字体）和前 5 s 在这一关带上实拍的样子，到最后才改就是整片重渲（`playbook/01-pipeline.md`，关卡 ②）。再写一张动画词表：每种动画归哪一章。
5. **样片（E4）**：片子里有几种做法（讲理、动情、宏大的镜头），铺开之前各做一小段。人的意见默认落到全片，不重做样片（`playbook/01-pipeline.md` 的"长片"）。
6. **分章做**：主 agent 先做一章当样板。平时整片开 1–3 个子代理，按章铺开留给 `studio` 或人点名。一章一个文件，共用库只由主 agent 改；全局的意见当场改到共用库，再通知各路。
7. **查和改**：`bin/vh textcheck`、`bin/vh readcheck`、`bin/vh fonts check`、`bin/vh check`；合片后给 reviewer 一张跨章联系表，每章一行，专门找重复的动画。只改一处用 `bin/vh patch`，不整片重渲。
8. **交付**：要 4K 时先抽几帧 `--dpr 2` 看过再渲，出片后 `bin/vh check <4K> --against <1080p>`；上传版用 `bin/vh deliver`。开工前留够磁盘（`playbook/01-pipeline.md` 的"磁盘和时间"）。

## 审美要点

下面是做过几支长片试出来的，都是起点，换题材可以改。

- **第 1 帧就有事发生**：不淡入，不推空景。前 20 s 把全片的问题或最强的对比摆出来。旁白定稿以后，开头只能靠画面，所以放进样片。
- **后半段最难**：没有新事件时，文案容易一章接一章得出差不多的结论，画面容易变成大字加一个符号。用两三个追问撑住，各章分头回答；力气和预算留给这里，不要把好镜头都给开头。
- **先立后破**：最有力的反转，推翻的是观众带进来的现成答案，所以先把那个答案立稳。
- **抽象的话要变成画面**：分镜前写一张表，这句话要说什么、画什么。要有物件、动作和因果，卡片亮起来不算动作。检验：关掉旁白和字幕，它在说什么？字比一个标签多，就配数据图、结构框图、机制动画或真实资料。
- **三种素材一眼分得开**：真实资料（论文页、官方页面、照片）慢推到要读的一行，静停 3–5 s，标出处；概念动画可以简化，不能改科学含义；生成的画面只放在虚构再现里，观众可能当成史料的就标出来。
- **要观众记住的框架不超过三套**：每次出现只停几秒，接在一个具体画面后面。其余比喻只用一次。
- **颜色有含义，全片不变**：一种颜色只给一件事，写进 `STYLE.md`。守住了，后面颜色本身就能当语言用。
- **母题重复的是意思，动画只跑一段**：同一个意思回来时换一种形态（`playbook/01-pipeline.md` 的"动画词表"）。
- **节奏是交替**：幕的边界用一个换挡装置（`playbook/09-narrative.md` 第 5 节）。静音留给最强的一处。

## 禁止

底线：
- 数字、人名、引文靠猜，或者没有出处（硬规则 5）；
- 生成的画面冒充资料、实验录像或照片；
- 第三方素材没登记（`bin/vh assets add`）。

常见误用（参考）：
- 一串知识点，没有问题把它们串起来；照论文或教材的章节排；
- 比喻式的章名，只有看过片才懂；
- 每章重新证明同一个结论；
- 一张图讲六句话，两三分钟画面不动；
- 同一种动画（树、齿轮、粒子）在几章里各跑一遍；
- 进度条、字幕样式到最后才定。

## Prompt 增量块

```text
+ TYPE: long landscape explainer. {10–35} min, 1920x1080 30fps, narration {TTS | the person's recording} in {zh-CN | en}, canvas-film. Source material: {…}.
One question runs through the film and the chapters answer it in turn; 8–13 chapters named by their content. Before the script, a table of turns and hooks (around when, what the viewer believes first, what they see next, which chapter): no 2–3 minutes without a new question.
Voice first: shots, captions and chapters hang on the narration's words. A full-length grey animatic before any polish, with the chapter bar, captions, fonts and the first 5 s as they will be. A short sample of each kind of scene before the chapters fan out.
At most three recurring frameworks; each colour keeps one meaning; real sources, concept animation and re-enactment look different at a glance. A list of animations by chapter: a motif repeats its meaning, an animation runs once.
Every number, name and quote from NOTES.md, with its source.
```

## 自查重点

- 反转和钩子表：有没有两三分钟没有新问题的地方？
- 第 1 帧有事发生吗？前 5 s 的连帧看过了吗（`bin/vh frames <项目> --strip 0:5 --fps 6`）？
- 每个主镜头，关掉声音它在说什么？
- 跨章联系表里，同一种动画有没有跑两遍？要记住的框架有没有超过三套？
- 屏幕上的每个数字，`NOTES.md` 里都有出处吗？
- 全片是一个声音吗？句子之间的音高、响度有没有跳？
- 章节条对得上旁白吗（`bin/vh cues --chapters`）？画面上的字和字幕有没有撞（`bin/vh textcheck`）？

## 可参考的案例与源码

- `engines/canvas-film/README.md`：引擎的全部写法；`engines/EDIT.md`：灰卡骨架和按章换引擎。
- `playbook/09-narrative.md`：第 5 节长片的节奏，第 9 节接进流程，第 10 节句子。
- `recipes/sequences/README.md`：骨架都比长片短，可以当一章的节奏（`data-along-time`、`time-dilation-replay`）。
- `cases/opus55-gallery.md` 第 6 节：3D 长片深读。`cases/explainer-interstellar-blackhole.md`、`cases/douyin-vibe-knowledge.md`：横屏讲解。
