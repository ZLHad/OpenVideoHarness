# 案例库

每个案例都按四个方面拆解：做了什么、怎么做的、为什么有效、能借用什么。源码在本地的，列出了 `references/repos/` 下的路径。

| 案例 | 类型 | 引擎 | 源码 | 最值得借用的一点 |
|---|---|---|---|---|
| [mv-pdoom.md](mv-pdoom.md)：I'm Upping My P(doom)，以及它的翻拍和中文版 | MV、手绘 | p5.js + p5.brush | `PDoomVideo/`（无 license，只读） | 契约文件加并行 subagent；每个镜头都要有事发生；视频可以像代码一样 fork |
| [mv-functional-emotions.md](mv-functional-emotions.md)：Functional Emotions | MV、绘画 | 自写 WebGL 笔触渲染器 | `functional-emotions-video/`（MIT） | 歌词对齐流水线；主 agent 先做样板章节，再派 7 个 subagent；"这不是歌词视频" |
| [mv-claude-pop.md](mv-claude-pop.md)：Claude Pop | MV、混合 | Seedance 2.5 + JS 转描 | 无 | 生成视频只当底片，最终画面由 JS 画；审美立场怎么写进 prompt |
| [explainer-interstellar-blackhole.md](explainer-interstellar-blackhole.md)：星际穿越里的真物理·黑洞篇 | 横屏科普 | 未公开（推测为着色器 + HTML） | 无 | 一句话 prompt 加一个贯穿全片的主视觉；纪录片式的克制视觉系统；标准的科普结构 |
| [promo-applore.md](promo-applore.md)：Applore 宣传片 | 产品宣传 | 未公开（推测为 HTML/JS） | 无 | 一句话 prompt 加真实素材；让模型把自己当成动效设计师 |
| [promo-hyperframes-launches.md](promo-hyperframes-launches.md)：HeyGen 发布片合集 | 产品宣传、论文发布、梗复刻 | HyperFrames | `hyperframes-launches/`（Apache-2.0） | 20 支可以直接读源码的成片，以及它们的 STORYBOARD 和 DESIGN 文件 |
| [explainer-code2video.md](explainer-code2video.md)：Code2Video 和 TheoremExplainAgent | 教学讲解 | Manim | `Code2Video/`（prompts、src） | 锚点网格、ScopeRefine、并行生成 |
| [paper-paper2video.md](paper-paper2video.md)：Paper2Video / PaperTalker | 论文报告 | Beamer + TTS + 数字人 | 无（仓库在 GitHub） | 多通道对齐；让 VLM 从变体里选 |
| [remotion-production.md](remotion-production.md)：Claude Code + Remotion 生产实践 | 通用 | Remotion | 无 | 真实踩过的坑（亚像素闪烁、缩放抖动、旧文件） |
| [community-prompts.md](community-prompts.md)：社区公开的 prompt | 各类 | 各类 | 二手合集 | 成功 prompt 的八个共同点 |

## 按需求查案例

- 要做 MV：pdoom → functional-emotions → claude-pop，按从易到难的顺序看。
- 要做产品片：applore（最简单的做法）→ hyperframes-launches（看工业级怎么做）。
- 要做讲解或论文视频：interstellar-blackhole（一句话能做到什么程度）→ code2video → paper2video，外加 hyperframes-launches 里的 `claude-paper-launch/`。
- 想拆解一支别人的视频：按 `playbook/07-reverse-engineer.md` 走，产出格式参考 interstellar-blackhole。
- 想知道 prompt 怎么写：community-prompts。
