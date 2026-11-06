# 06 论文讲解 / 学术会议视频

**适用**：
- 自己或别人论文的讲解视频；
- 会议 teaser（约 30 秒）；
- 3–5 分钟的讲解；
- 10 分钟以上的报告或讲解：主类型是 `10-long-explainer.md`，章节、节奏和引擎按它，读源文件、事实、公式和图的规矩按本篇；
- 投稿附带的补充视频。

**不适用**：只讲论文里某一个数学原理，这种情况看 `01-math-science-explainer.md`。

## 引擎

按内容分工，可以在同一个项目里混用：

- **机制、公式、系统模型**（信道、拓扑、算法流程）用 Manim CE。
- **结构、结果、标题卡、论文信息**用 HyperFrames。它对版式、数字计数、字幕更顺手。
- **报告录像型**（幻灯片 + 讲者）可以参考 Paper2Video 的通道拆分；本机没有 NVIDIA GPU，数字人部分做不了。

最后用 ffmpeg 把各段拼接起来。

## 工作流

写代码前先把第 2–4 步写出来。这个顺序来自 3brown1blue 的 `paper-explainer.md`，它把这三步叫 Gate 1/2/3；在这里它们只是步骤，并入 CLAUDE.md 的关卡，只在关卡 ①②③ 和导演模式点名的地方停（`quick` 不设关卡）：

1. **读源文件**：优先读 `.tex`，没有再读 PDF。把以下内容**照抄**进 `NOTES.md`：标题、作者、单位、会议或期刊、年份、每个要上屏的数字和它所在的表格或图的位置。
   **没附论文时**：先问用户要 `.tex`、PDF 或 arXiv id，这时什么都不写，不出立意卡和稿子，也不凭记忆写作者、年份和数字。用户只给了题目，查到的 arXiv id 先请他确认是这一篇。
2. **步骤一：口播稿**，写进 `SCRIPT.md`（模板在 `templates/SCRIPT.md`），随关卡 ② 给人看；人点名 `script=own` 时在 E1 先停。写稿并估算时间，字数按 `playbook/04-audio.md` 语速表的句内语速（原理讲解、论文 3.5–4.5 字/秒）乘 0.85 倒推，3 分钟约 540–690 字。不要照念摘要。定稿后逐句拆进 `audio/script.txt`，运行 `bin/vh tts <项目>` 得到 `timeline.json`（默认用本地的 `qwen`，不要 key；别的 provider 见 `playbook/04-audio.md`）。Manim 片段按其中每句的实测时长安排 `run_time`，HyperFrames 片段则直接读这个文件。
3. **步骤二：场景表（curriculum）**，写进 STORYBOARD.md，就是关卡 ② 的分镜。每个场景写清时间范围、唯一的 insight 和视觉模式。
4. **步骤三：STYLE.md**。方向写在关卡 ① 立意卡的"画面"一行，选卡就定了；选定后再写 STYLE.md，定调色板和字体，并约定语义色：输入绿、处理蓝、输出黄，本文方法用强调色，基线用灰色。
5. **重画图**：论文里的图全部用矢量重画，不截 PDF。系统框图按从左到右的顺序逐个出现，两端的框都出现之后才画箭头。
6. **公式**：先整体显示 2 秒，再变暗到 30%，然后逐项讲解并上色。
7. **结果**：不要把整张结果表放上屏。只挑支撑结论的 1–2 个对比，做成图表（参考 `05-data-story.md`），本文方法高亮，基线灰色。
8. **音画对齐**：动画比旁白提前约 0.5 秒开始，每句话说完停约 1 秒。5 秒的旁白大约配 4 秒动画加 1 秒停留。

## 结构模板【综合】

| 形式 | 结构 |
|---|---|
| 30 秒 teaser | 问题 5s → 关键想法的图 10s → 结果里最有说服力的一幕 10s → 标题、会议、链接 5s |
| 3–5 分钟 | 动机和问题 → 系统模型 → 关键想法（1–2 个机制动画）→ 结果（1–2 张图）→ 一句话总结 + 论文信息 |
| 10 分钟以上 | 按 `10-long-explainer.md` 做：一个贯穿的问题、按内容起名的章节，不必一节论文一章；报告录像（幻灯片加讲者）看 `cases/paper-paper2video.md` 的通道拆分 |

3brown1blue 的 `paper-explainer.md` 里有更详细的五分钟模板，也分领域（ML、物理/工程、生物医学）给出了常见套路。3–5 分钟的讲解怎么排节拍、在哪里换挡，见 `playbook/09-narrative.md` 的模板 B。

## 禁止

底线：
- 作者、年份、数字写错或靠猜（硬规则 5）；手上没有原文就开写。

常见误用（参考）：
- 截 PDF 页面：字太小，要用原图就裁一块放大；
- 念摘要：观众自己会读；
- 整张结果表上屏：找不到要看的数；
- 公式没有逐项讲解；
- 用要点清单收尾。

## Prompt 增量块

```text
+ TYPE: paper explainer. {30s teaser | 3–5 min explainer | 10+ min talk: video-types/10-long-explainer.md}, 1920x1080 30fps, TTS {voice} in {zh-CN | en}. Source: {paper.tex path / arXiv id}. No source attached: ask for the .tex or the arXiv id and write nothing yet; invent no numbers.
Before code, in this order: SCRIPT.md (spoken script + estimated timestamps), the curriculum in STORYBOARD.md (per scene: time range, the ONE insight, visual pattern), STYLE.md (palette, fonts, sizes, semantic colors). These are steps inside the project's gates (concept and outline, storyboard, first draft): stop where the gates and the director mode say, not after each step.
Copy title, authors, venue, year, and every on-screen number verbatim from the source, recording where each came from in NOTES.md; put anything uncertain in NOTES.md instead of guessing.
Redraw figures as vectors rather than screenshotting the PDF (too small to read). Pipelines reveal box by box left-to-right; draw each arrow only after both ends exist. Input=green, processing=blue, output=yellow; ours = accent {hex}; baselines gray.
Equations: show whole 2s → dim to 30% → explain term by term, coloring each when done.
Results: the 1–2 comparisons that carry the claim, usually as charts rather than tables.
Animation starts ~0.5s before the narration mentions it; ~1s hold after each narrated sentence.
Engines: Manim CE for mechanisms/equations, HyperFrames for title/structure/results; concat with ffmpeg.
```

## 自查重点

- 屏幕上的每个数字都能在 `NOTES.md` 里找到出处吗？
- 系统框图的箭头是在两端都出现之后才画的吗？
- 基线是不是灰色，本文方法是不是强调色？
- 每个场景是不是只讲了一个 insight？
- 片尾有没有论文信息，信息是否准确？

## 可参考的案例与源码

- `cases/paper-paper2video.md`：报告录像型的通道拆分，以及"让 VLM 从变体里选"。
- `cases/explainer-code2video.md`：左侧讲义、右侧锚点动画区的版式。
- `references/repos/3brown1blue/src/three_b1b/skill/rules/paper-explainer.md`（**必读**），以及同一目录下的 `remotion-integration.md`。
- `references/repos/3brown1blue/src/three_b1b/skill/templates/paper_explainer.py`：论文讲解的场景模板。
- `references/repos/hyperframes-launches/claude-paper-launch/`：HyperFrames 做的论文发布片，带 ElevenLabs 旁白和 `transcript.json`，可以当作用 HyperFrames 做论文视频的样板。

## 社区 skill 参考

以下条目选自 183 个社区视频 skill，完整对照和许可证说明见 `references/community-skills.md`。只读参考；复用代码前，先确认它的许可证。

- **data-animation-skills / presentation-video**（MIT）：把幻灯片重建成带旁白、自动翻页的视频；每页标题写成一句论断，每页时长等于该页旁白的实测时长。见 `references/repos/data-animation-skills/skills/presentation-video/SKILL.md`。
- **ssrajadh/paperview**（Apache-2.0，未拉取）：论文或代码库生成讲解视频，本地渲染加 TTS；清单里和本类最贴近，值得拉下来细读。
