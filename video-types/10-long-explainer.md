# 10 长讲解（10 分钟以上的横屏）

**适用**：
- 10 分钟以上、有旁白的横屏讲解：把一个原理讲透，把一件大事讲清来龙去脉，或者围绕一个问题讲观点；
- 10 分钟以上的论文讲解：章节、节奏和引擎按本篇，读源文件、事实、公式和图的规矩按 `06-paper-explainer.md`。

**不适用**：
- 2–5 分钟的横屏知识片：`02-knowledge-short.md` 的"变体：抖音横屏中视频"；
- 用户自己录的讲课、口播：`09-editing-talking-head.md`；
- 单独一段数学推导：`01-math-science-explainer.md`。长片里的推导也可以单独用 Manim 做，再排进来。

## 引擎

`bin/vh new long <slug>` 建的就是 canvas-film（项目里的 `ENGINE_README.md`，和 `engines/canvas-film/README.md` 是同一份）：镜头、字幕、章节的时间挂在旁白的字上，重配一句、插一个停顿，画面跟着走，几十上百个镜头也管得住。模板里是一支示例片，开工时换掉。要 3D 镜头加 `--three`。某一章要换引擎（Manim 推导、HyperFrames 排版），单独做成页面或片子，用剪辑表 `edit.json` 排进来（`engines/EDIT.md`）。

## 工作流

长片最贵的是改：定稿之后每改一句都要重配、重渲。所以前面几步都是为了让人早看到、早改。档位和关卡照 CLAUDE.md。

1. **素材和主线（关卡 ①）**：先把数字、原话、物件和出处记进 `NOTES.md`，再定一条让人跟到最后的主线：一个问题、一件事的经过、一个人。大纲和别的片子一样是 3–7 段，段名按内容起（`playbook/09-narrative.md` 第 3 节）；章到分镜时再拆，章名要让没看过片的人也看得懂。
2. **先排节奏表，再写稿（随关卡 ② 给人看；人点名 `script=own` 时在 E1 停）**：表头是约在几分钟、观众在这里得到什么新东西、在哪一章，写在 `SCRIPT.md` 开头。哪一段很久没有新东西，表上一眼看得出（`playbook/09-narrative.md` 第 5.3 节的"再钩一次"）。句子的写法见 `playbook/09-narrative.md` 第 10 节；字数按 `playbook/04-audio.md` 的语速表倒推，再用配音实测。结尾早点给人看。
3. **配音先于画面**：`bin/vh tts`（要按词挂镜头加 `--align local` 或 `--align gemini`），`bin/vh timeline` 查时间轴，`bin/vh pace` 调句间停顿。长稿要查从头到尾是不是一个声音（`tools/audio/README.md` 的"整段合成"）。
4. **全片灰卡骨架（关卡 ②）**：先把镜头表写成 `shots.json`（一镜一行，格式见 `bin/vh storyboard -h`；新项目没有它，`bin/vh edit init` 会退出 2），再 `bin/vh edit init` 把它并成 `edit.json`，`bin/vh render` 出片：每镜一张灰卡，写着镜头号、段名、`reads` 和这一镜的秒数，这就是 animatic，之后一镜一镜换上真画面（`engines/EDIT.md`）。每一帧都在的东西（章节进度条、字幕、字体）和前 5 s 在这一关带上实拍的样子，到最后才改就是整片重渲（`playbook/01-pipeline.md`，关卡 ②）。分头做之前再写一张动画词表：每种动画归哪一章（`playbook/01-pipeline.md` 的"长片"）。
5. **样片（E4）**：片子里有几种做法时，铺开之前各做一小段，一段验一种能力。人的意见默认落到全片，不重做样片（`playbook/01-pipeline.md` 的"长片"）。
6. **分章做**：主 agent 先做一章当样板。平时整片开 1–3 个子代理，按章铺开留给 `studio` 或人点名。一章一个文件，共用库只由主 agent 改；全局的意见当场改到共用库，再通知各路。
7. **查和改**：`bin/vh textcheck`、`bin/vh readcheck`、`bin/vh fonts check`、`bin/vh check`；合片后给 reviewer 一张跨章联系表，每章一行，专门找重复的动画。只改一处用 `bin/vh patch`，不整片重渲。
8. **交付**：要 4K 时先抽几帧 `--dpr 2` 看过再渲，出片后 `bin/vh check <4K> --against <1080p>`；上传版用 `bin/vh deliver`。开工前留够磁盘（`playbook/01-pipeline.md` 的"磁盘和时间"）。

## 审美要点

下面都是起点，换题材可以改。

- **开头只能靠画面**：旁白定稿以后，开头的字就改不动了，所以前 5 s 放进样片，和 `playbook/10-hooks-and-packaging.md` 的钩子一起看。
- **后半段容易变平**：没有新事件时，一章接一章得出差不多的结论。节奏表上看后半段有没有新东西（`playbook/09-narrative.md` 第 5 节的换挡）。
- **几种素材不能混**：真实资料标出处；概念动画可以简化，不能改含义；生成的画面不冒充资料，观众可能当成史料的就标出来。
- **全片的约定写下来**：颜色各代表什么、字幕和章节条怎么放，写进 `STYLE.md`，分头做的时候才对得上。

## 禁止

底线：
- 数字、人名、引文靠猜，或者没有出处（硬规则 5）；
- 生成的画面冒充资料、实验录像或照片；
- 第三方素材没登记（`bin/vh assets add`）。

常见误用（参考）：
- 一串知识点，没有主线把它们串起来；照论文或教材的章节排；
- 章名只有看过片才懂；
- 每章重新证明同一个结论；
- 一张图讲很久，画面长时间不动；
- 同一种动画在几章里各跑一遍，分头做时最容易这样；
- 进度条、字幕样式到最后才定。

## Prompt 增量块

```text
+ TYPE: long landscape explainer. {length} min, 1920x1080 30fps, narration {TTS | the person's recording} in {zh-CN | en}, canvas-film. Source material: {…}.
A through-line the viewer can follow to the end; 3–7 segments at gate ①, split at the storyboard into chapters named by their content. Before the script, a pacing table (around when, what is new for the viewer there, which chapter).
Voice first: shots, captions and chapters hang on the narration's words. A full-length grey animatic before any polish, with the chapter bar, captions, fonts and the first 5 s as they will be. A short sample of each kind of scene before the chapters fan out.
What each colour means goes in STYLE.md; real sources, concept animation and generated pictures must not be mistaken for each other. A list of animations by chapter, so chapters made apart do not repeat one.
Every number, name and quote from NOTES.md, with its source.
```

## 自查重点

- 节奏表：有没有很久没有新东西的地方？
- 前 5 s 的连帧看过了吗（`bin/vh frames <项目> --strip 0:5 --fps 6`）？
- 跨章联系表里，同一种动画有没有跑两遍？
- 屏幕上的每个数字，`NOTES.md` 里都有出处吗？
- 全片是一个声音吗？句子之间的音高、响度有没有跳？
- 章节条对得上旁白吗（`bin/vh cues --chapters`）？画面上的字和字幕有没有撞（`bin/vh textcheck`）？

## 可参考的案例与源码

- `engines/canvas-film/README.md`：引擎的全部写法；`engines/EDIT.md`：灰卡骨架和按章换引擎。
- `playbook/09-narrative.md`：第 5 节长片的节奏，第 9 节接进流程，第 10 节句子。
- `recipes/sequences/README.md`：骨架都比长片短，可以当一章的节奏（`data-along-time`、`time-dilation-replay`）。
- `cases/opus55-gallery.md` 第 6 节：3D 长片深读。`cases/explainer-interstellar-blackhole.md`、`cases/douyin-vibe-knowledge.md`：横屏讲解。
