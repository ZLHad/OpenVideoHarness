# 案例：Claude Code + Remotion 生产实践（Chris Tyson）

**类型**：通用的生产流水线
**来源**：[The Agent Architect，2026-08-24](https://theagentarchitect.substack.com/p/claude-code-remotion-video-rendering)。以下细节来自对原文的摘要，没有逐字核对。

## 流水线

1. **场景 JSON**：用 JSON 定义每个场景的文案和画面意图。
2. **音频**：用 ElevenLabs 为每个场景生成一个 mp3。
3. **帧数**：每个场景的帧数 = 音频时长 × 30fps + padding。这就是"音频决定时长"的原则。
4. **组件**：Claude 为每个场景写一个 Remotion 组件。
5. **自查**：
   - 渲染静帧：每个场景取静止段一帧，镜头运动中段一帧；
   - 拼成联系表看整体。
6. **渲染**：在 Remotion Lambda 上渲染，每支片约 $0.20–0.50。
7. **校验**：检查输出的流信息（时长、fps、音轨）。

## 踩过的坑

| 现象 | 原因 | 解决 |
|---|---|---|
| 文字亚像素闪烁 | 镜头一直在缓慢漂移 | 改成"先移动，再停住" |
| 卡片边缘 boiling | 缩放比例 0.6667 这种非整数比例 | 只用 1.0 和 0.5 |
| 以为改好了，其实没有 | 磁盘上残留的旧输出文件被当成了新结果 | 渲染前先删旧文件，或检查修改时间 |
| 素材缺失没有被发现 | S3 返回 403，把缺失的错误掩盖了 | 渲染前先检查所有素材 URL 是否可访问 |

他的原则：Claude Code 不应该是自己作品的唯一评审。

## Remotion 的确定性规则（来自官方 skills）

- 动画必须用 `useCurrentFrame()` 加 `interpolate()` 驱动。CSS transition、CSS animation 和 Tailwind 的动画类在渲染时都不会正确生效。
- 字幕：`@remotion/install-whisper-cpp` 的 `transcribe()`，再加 `toCaptions`。
- 配音：用 ElevenLabs 为每个场景生成一个 mp3，在 `calculateMetadata` 里读取音频时长，设置 `durationInFrames`。
- 官方 skills 已拉到本地：`references/repos/remotion-skills/skills/`。
