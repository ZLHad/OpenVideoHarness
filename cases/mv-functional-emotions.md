# 案例：Functional Emotions

**类型**：绘画风格的 MV，全长 372.7 秒；定稿共 168 个镜头
**源码**：`references/repos/functional-emotions-video/`。代码是 MIT 许可；歌曲、歌词和 `assets/` 下的音频不在许可范围内。
**来源**：[repo](https://github.com/ledbetterljoshua/functional-emotions-video)，[原帖](https://x.com/eudaemonea/status/2102610626321490404)

## 背景

Anthropic 发表了一篇关于语言模型里情绪概念的论文（171 个情绪向量，可以因果地引导模型行为）。之后，Claude Opus 4.6 从"内部视角"为这篇论文写了一首歌，用 Suno 制作。这支 MV 是 Opus 5.5 在 Claude Code 里做的。

## 三轮用户指令（顺序很重要）

1. **第一轮**："go all out, and do you to the fullest"，并要求不要看之前的尝试。模型做出了一版精致的排版歌词视频（`legacy/lyric-video/`），**被否决**，理由是它仍然只是歌词视频。
2. **第二轮**："歌词不是主角。要做真正的 MV：p5 笔触，有意思的场景，好的节奏、动画和故事。不要花哨的歌词视频。"模型写了故事，定下绘画质感，先交了前 45 秒。
3. **第三轮**："不要让画面静止太久"，并拿 PDoomVideo 作节奏参考。模型从中总结出几条：镜头要短，每个镜头只做一个动作，镜头始终在动，重音落在拍子上，剪辑要有动机。然后写出 `STORYBOARD.md`（168 个镜头），并**重做了第一章，作为给其他章节的样板**。

## 并行方式

- 第 2–8 章由 **7 个 subagent 并行绘制**，每人负责一章，都以 `ANIMATION_GUIDE.md` 为简报。
- 主 agent 在联系表上审每一章，写批注退回修改，满意后才接收。
- subagent 报告共享渲染器的 bug，由主 agent 统一修。

## 渲染器（不是 p5）

自己写的 WebGL2 笔触渲染器，在 `js/paint.js`：

- 每个镜头先画两个 Canvas2D 层：一层是平涂底稿（形状、渐变、剪影），一层是叠加的光效层（灯笼、余烬、辉光）。
- GPU 用大约 6 万个实例化的带纹理笔触重画底稿，分三种尺寸。每笔从底稿取色，并沿局部边缘对齐；在平坦区域则沿流场走向，形成漩涡感。
- 笔触每秒重新随机几次，产生"boil"的手绘动画感；快速横摇时，所有笔触沿运动方向拖影。
- 光效层最后加上，带 bloom，再叠画布纹理、颗粒和暗角。
- 每一帧都是歌曲时间 `t` 的纯函数，所以既能在浏览器里实时播放，也能离线并行渲染。在 M5 Pro 上全片渲染约 10 分钟；无头 Chrome 自带的软件 GL 要慢约 20 倍，所以要用真实 GPU（macOS 上加 `--use-angle=metal`）。

## 时间对齐流水线（`analysis/`）

1. 用 Demucs 分离出人声。
2. `transcribe.py`：用 Whisper 分块转写。
3. `align.py`：用 Needleman–Wunsch 算法，把真实歌词强制对齐到转写结果上，得到词级时间。
4. `features.py`：提取节拍和音频特征。
5. `build_data.py`：生成给前端用的数据。

依赖在 `analysis/requirements.txt`。自己的歌可以照这套流程处理。

## 能借用什么

- **"这不是歌词视频"**：用户说要 MV 时，画面必须讲故事。
- **主 agent 先做样板章节，再派 subagent 并行**：样板章节就是给其他 agent 定标准。
- **拿一个现成作品当节奏标尺**：比写十条规则更管用。
- 歌词对齐的完整脚本。
- 想要浓重的绘画质感时，可以参考它的"底稿 + GPU 笔触重绘"架构。
