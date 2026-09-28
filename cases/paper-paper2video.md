# 案例：Paper2Video / PaperTalker

**类型**：由论文生成学术报告视频（幻灯片 + 字幕 + 语音 + 光标 + 数字人）
**源码**：未拉取到本地；需要时直接看 [repo](https://github.com/showlab/Paper2Video)（MIT）
**来源**：[论文 arXiv 2510.05096](https://arxiv.org/abs/2510.05096)

## 流水线

学术视频被拆成五个需要相互对齐的通道：幻灯片、字幕、语音、光标定位、讲者头像。

1. **幻灯片**：生成 LaTeX Beamer 代码，编译时的报错信息回灌给模型修复。
2. **版面溢出**：某页内容溢出时，用 **Tree Search Visual Choice** 处理：
   - 按规则生成多个变体（图片缩放 1.25 / 0.75 / 0.5 / 0.25，以及不同字号）；
   - 渲染后拼成一张图；
   - 交给 VLM **挑一个**。
3. **字幕与讲稿**：VLM 读每页幻灯片的图像，生成逐句字幕，并给出每句对应的视觉焦点描述。
4. **光标**：UI-TARS 定位光标坐标；WhisperX 的词级时间戳决定光标何时出现、何时消失。
5. **语音与头像**：F5-TTS 克隆作者声音，Hallo2 生成说话的头像。
6. **成本**：约 62K tokens。含数字人时 48.1 分钟（并行后提速 6 倍），不含时 15.6 分钟。建议使用 A6000 48G 显卡。

## 关键结论

**让 VLM 从变体里挑，比让它调数值参数更有效。** 这条和 Code2Video 的锚点网格是同一个思路：把连续调参变成离散选择。

## 在本机怎么借用

- 本机没有 NVIDIA GPU，做不了数字人部分，但前四个通道的思路都可以用：
  - 幻灯片用 HyperFrames 或 Manim 做，不必用 Beamer；
  - 字幕由 TTS 的时间戳生成；
  - 光标可以用 HyperFrames 的超大光标技法（`references/repos/hyperframes/_upstream_claude/skills/oversized-cursor/`）。
- 版面拿不准时，渲染 3–4 个变体拼成一张图，再让 agent 挑一个。
- 需要讲者出镜时，用自己录的口播，按 `playbook/05-hybrid-genvideo.md` 的 B 模式叠加。
- 相关工作：
  - PresentAgent：文档 → 幻灯片 → 讲稿 → TTS → 合成；
  - PPTAgent（`icip-cas/PPTAgent`）：论文生成 PPT。
