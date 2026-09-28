# 案例：HeyGen HyperFrames 发布片合集

**类型**：产品发布片为主，另有一支论文发布片和一支梗视频复刻
**源码**：`references/repos/hyperframes-launches/`（Apache-2.0，打包的素材另有 NOTICE）。克隆时没有拉取 Git LFS，所以视频、音频、字体都只是指针文件，**代码和文档可以正常读**；需要素材时要先装 git-lfs，再执行 `git lfs pull`。
**来源**：[repo](https://github.com/heygen-com/hyperframes-launches)；成片可以在 README 的 Watch 链接里看

## 每个项目的结构

```
<project>/
├── index.html          顶层 composition
├── compositions/       场景级 composition
├── assets/             素材（LFS）
├── STORYBOARD.md       逐镜头计划（部分项目有）
├── DESIGN.md / FRAME-*.md   设计系统（部分项目有）
└── meta.json / hyperframes.json
```

## 值得先看的几支

| 目录 | 看点 |
|---|---|
| `hyperframes-launch/` | HyperFrames 自己的发布片：15 秒 glass-frame 开场，之后依次展示 CSS、GSAP、Lottie、Shaders、Three.js。有 STORYBOARD |
| `heygen-apple-motion/` | 4 套可以换品牌的 Apple 风格发布片模板，适合直接当产品片的起点 |
| `claude-paper-launch/` | 论文发布片，带 ElevenLabs 旁白、`transcript.json`、`FRAME-claude.md`（设计系统）。做论文视频时的 HyperFrames 样板 |
| `figma-launch/` | 64 秒的集成发布片：真实的设计文件变成实时的 composition。有 STORYBOARD |
| `pr-to-video-launch/` | 30 秒，完整的三段式：开场 → 功能 → CTA |
| `timeline-launch/` | 15–20 秒，三幕结构，带笑点（先是一个音效来晚了的梗，再到对话螺旋）。有 STORYBOARD |
| `codex-five-hour-limit-replica/` | 1:1 复刻一个 10 秒的 X 梗视频。做梗视频时参考 |
| `sfx-music-launch/` | 音效和音乐怎么配合画面。有 STORYBOARD |
| `spacex-launch/`、`texture-launch-video/`、`vfx-heygen-combined/` | 都带 DESIGN 文件，可以看设计系统怎么写 |

## 怎么用

- 做产品片前，先读 1–2 支的 `STORYBOARD.md` 和 `DESIGN.md`，学它们的节拍划分和设计系统写法，再看 `compositions/` 里 GSAP 时间线的组织方式。
- 想直接改一支作为起点：先复制到 `projects/`，再 `git lfs pull` 拉取对应的素材；注意 NOTICE 里对打包素材的限制。
- 配合阅读 `references/repos/hyperframes/_upstream_claude/skills/` 下的 `motion-doctrine`、`oversized-cursor`、`cut-the-curve`、`seam-craft`。这些是 HeyGen 做发布片时的内部规范。
