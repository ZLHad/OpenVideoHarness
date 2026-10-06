# 案例库

每个案例都按四个方面拆解：做了什么、怎么做的、为什么有效、能借用什么。源码在本地的，列出了 `references/repos/` 下的路径。

从别人转来的视频写新案例时，记内容（选题、结构、规格、量出来的数），不写账号名，也不写视频是谁、怎么转来的；不是随机抽的样本，就照实写"不是随机抽样"。早先几篇点了作者，没有回头改。

| 案例 | 类型 | 引擎 | 源码 | 最值得借用的一点 |
|---|---|---|---|---|
| [mv-pdoom.md](mv-pdoom.md)：I'm Upping My P(doom)，以及它的翻拍和中文版 | MV、手绘 | p5.js + p5.brush | `PDoomVideo/`（无 license，只读） | 契约文件加并行 subagent；每个镜头都要有事发生；视频可以像代码一样 fork |
| [mv-functional-emotions.md](mv-functional-emotions.md)：Functional Emotions | MV、绘画 | 自写 WebGL 笔触渲染器 | `functional-emotions-video/`（MIT） | 歌词对齐流水线；主 agent 先做样板章节，再派 7 个 subagent；"这不是歌词视频" |
| [mv-claude-pop.md](mv-claude-pop.md)：Claude Pop | MV、混合 | Seedance 2.5 + JS 转描 | 无 | 生成视频只当底片，最终画面由 JS 画；审美立场怎么写进 prompt |
| [explainer-interstellar-blackhole.md](explainer-interstellar-blackhole.md)：星际穿越里的真物理·黑洞篇 | 横屏科普 | 未公开（推测为着色器 + HTML） | 无 | 一句话 prompt 加一个贯穿全片的主视觉；纪录片式的克制视觉系统；标准的科普结构 |
| [promo-applore.md](promo-applore.md)：Applore 宣传片 | 产品宣传 | 未公开（推测为 HTML/JS） | 无 | 一句话 prompt 加真实素材；让模型把自己当成动效设计师 |
| [promo-hyperframes-launches.md](promo-hyperframes-launches.md)：HeyGen 发布片合集 | 产品宣传、论文发布、梗复刻 | HyperFrames | `hyperframes-launches/`（Apache-2.0） | 20 支可以直接读源码的成片，以及它们的 STORYBOARD 和 DESIGN 文件 |
| [promo-video-shotcraft.md](promo-video-shotcraft.md)：video-shotcraft 镜头配方库 | 产品宣传 | Remotion | `video-shotcraft/`（Apache-2.0） | 镜头写成"意图 + 参数表 + 命门 + 参考实现"；全片能量骨架和 hold 预算；终检对照计划。本仓库的 `recipes/` 由它改写 |
| [explainer-code2video.md](explainer-code2video.md)：Code2Video 和 TheoremExplainAgent | 教学讲解 | Manim | `Code2Video/`（prompts、src） | 锚点网格、ScopeRefine、并行生成 |
| [paper-paper2video.md](paper-paper2video.md)：Paper2Video / PaperTalker | 论文报告 | Beamer + TTS + 数字人 | 无（仓库在 GitHub） | 多通道对齐；让 VLM 从变体里选 |
| [remotion-production.md](remotion-production.md)：Claude Code + Remotion 生产实践 | 通用 | Remotion | 无 | 真实踩过的坑（亚像素闪烁、缩放抖动、旧文件） |
| [community-prompts.md](community-prompts.md)：社区公开的 prompt | 各类 | 各类 | 二手合集 | 成功 prompt 的八个共同点 |
| [opus55-gallery.md](opus55-gallery.md)：Opus 5.5 社区代码视频精选 | 各类，另有 3D 长片深读 | 各类；Austerlitz 为 WebGL2 | `awesome-opus5-5-videos/`、`opus55-catalog-zhuyansen/`、`Battle-of-Austerlitz-Film/`（均无 license，只读） | 389 支作品的 prompt 统计和精选；Austerlitz 用旁白实测时长驱动镜头，从画面推导音效 |
| [oneshot-five.md](oneshot-five.md)：五支社区代码视频（3 秒钟、我眼中的你、用做法讲做法、FunTech、Mirage） | 科普、肖像、自我介绍、showreel、发布片 | 未公开（推测为 HTML/WebGL，FunTech 混有生成素材） | 无 | 立意装置先于风格；具体的数字和原话；和我们口味规则的出入 |
| [douyin-vibe-knowledge.md](douyin-vibe-knowledge.md)：抖音上的十支 AI 动画（9 支发于 2026-09 底） | 知识讲解为主，横屏中视频 | 未公开（多数自述用 Claude / Opus 写代码；1 支生成式视频） | 无 | 前四支的几处相似；横屏 2.5–5 分钟、字幕偏小；一个号 15 支的赞数分布；同题的两种立意 |

## 按需求查案例

- 要做 MV：pdoom → functional-emotions → claude-pop，按从易到难的顺序看。
- 要做产品片：applore（最简单的做法）→ hyperframes-launches（看工业级怎么做）→ video-shotcraft（镜头配方和节奏预算，落地在 `recipes/`）。
- 要做讲解或论文视频：interstellar-blackhole（一句话能做到什么程度）→ code2video → paper2video，外加 hyperframes-launches 里的 `claude-paper-launch/`。
- 想拆解一支别人的视频：按 `playbook/07-reverse-engineer.md` 走，产出格式参考 interstellar-blackhole。
- 想找"一个点子撑起全片"的做法（时间放大镜、机器视角的肖像、用做法讲做法、吉祥物穿越风格、工作流即故事）：oneshot-five。
- 要做抖音上的横屏知识中视频，或者想看同一个题目被做成两支不同的片子：douyin-vibe-knowledge。
- 想知道 prompt 怎么写：community-prompts，再从 opus55-gallery 第 3 节挑同类型的。
- 要做 3D 场景或几分钟的长片：opus55-gallery 第 6 节（Austerlitz 深读）。
