# 案例：Code2Video 与 TheoremExplainAgent

**类型**：教学讲解视频，用 Manim 实现；属于学术系统
**源码**：`references/repos/Code2Video/`，只检出了 `prompts/` 和 `src/`（MIT）
**来源**：[Code2Video 论文](https://arxiv.org/abs/2510.01174)（ICML 2026）、[repo](https://github.com/showlab/Code2Video)；[TheoremExplainAgent](https://arxiv.org/abs/2502.19400)（ACL 2025）

## Code2Video 的流水线

**Planner**
1. 先生成大纲：每节包含 id、标题、摘要和例子，并按受众层级调整。
2. 再生成分镜：每节由若干行讲稿（lecture line）加对应的动画组成。
3. 从外部补充素材：用 Google Images 找参考图，以 CLIP 相似度过滤；从 IconFinder 找图标。素材缓存后跨章节复用，以保持风格一致。

**Coder**
- 各节并行生成代码，都继承一个固定的 `TeachingScene` 基类：左侧放讲稿，右侧是动画区。
- 用 `manim -ql` 渲染，超时 180 秒。
- 报错时用 **ScopeRefine** 修复（`src/scope_refine.py`），范围逐级扩大：
  1. 报错行前后 ±1 行；
  2. 整段 lecture block；
  3. 整节重新生成。
- 辅助手段：
  - **dry-run**：把 `construct` 换成 `self.wait(0.1)`，先快速检查 import 和语法；
  - 按错误类型（NameError、AttributeError 等）附上对应 Manim API 的提示；
  - 默认上限：修 bug 最多 10 次，重新生成最多 10 次。

**Critic 与视觉锚点**（`prompts/stage3.py`）
- 右侧画布划成 6×6 格，编号 A1–F6。代码只能调用 `self.place_at_grid(obj,'B2',scale_factor=0.8)` 或 `place_in_area(obj,'A1','C3')` 来摆放元素。
- 同时维护一张占用表，记录每个元素占用的锚点、缩放比例和对应代码行。
- Critic 把三样东西一起交给 VLM：渲染出的该节 mp4、网格参考图、占用表。VLM 检查五类问题：
  1. 遮挡左侧讲稿；
  2. 元素相互重叠；
  3. 出界；
  4. 网格空间浪费；
  5. 该淡出的元素没有淡出。
- 输出 JSON，最多列 3 个问题，每条都必须是"Line X: self.place_at_grid(...)"这种可以直接执行的修改。共 2 轮反馈，每轮最多改 3 次。
- **为什么这样设计**：VLM 能看出哪里有问题，但说不准该往哪移、移多少。锚点网格把连续的坐标判断变成了离散的选格子。消融实验里，6×6 网格效果最好。

**音频**
- 开源代码里没有 TTS。讲稿以文字形式显示在左侧，靠变色与动画同步。
- 最后用 `ffmpeg -f concat -c copy` 把各节拼起来。

**耗时**（论文数据，每个主题）

| 配置 | 耗时 | tokens | 质量 |
|---|---|---|---|
| Claude Opus 4.1 | 13.8 分钟 | 43.1K | AES 87.9，TeachQuiz 86.0 |
| 去掉并行 | 86.6 分钟 | — | — |
| 去掉并行和 ScopeRefine | 149.8 分钟 | — | — |

- README 推荐用 Claude 写 Manim 代码，用 Gemini 做 Critic。
- 注意：代码固定依赖 `manim==0.19.0`，当前最新版是 0.21.0。

## TheoremExplainAgent 的流水线

- **Planner** 依次产出：场景大纲 → 视觉分镜 → 技术实现方案 → 动画和旁白计划。之后交给 Coding agent 写代码。
- **agentic RAG**：分三个阶段检索 Manim 文档，分别用于分镜、实现和纠错。
- **配音**：用 `manim-voiceover` 加 Kokoro TTS。
- **纠错**：把报错回灌给模型重写，最多 5 次，成功率约 90%。可选用 VLM 看渲染结果来修代码。
- **结论**：即使渲染成功率很高，多数视频仍有小的布局问题。所以只看"能渲染"不够，一定要看图。

## 在 Claude Code 里怎么借用

- 在 STYLE.md 里定义锚点网格和放置函数，禁止手写坐标（`video-types/01-math-science-explainer.md` 的 prompt 增量块已经包含这一条）。
- Manim 报错时，按 ScopeRefine 的顺序修。
- 按节派 subagent，并行生成。
- 写 Manim 代码前，先读 `references/repos/3brown1blue/src/three_b1b/skill/rules/troubleshooting.md`。
