# 08 野兽派 / 网络梗 / 科技推特风快剪

**适用**：
- 15–40 秒的梗视频、观点快剪、"这周 AI 圈发生了什么"；
- 带笑点的产品吐槽或对比；
- 面向科技圈社交媒体的视觉 hook。

## 引擎

- **首选**：HyperFrames。可以直接从风格预设 Deconstructed（Neville Brody）出发。
- **备选**：Remotion。

## 工作流

1. **定笑点**：先写 3–5 个笑点（punchline），每个笑点配一个铺垫。整片就是"铺垫 → 包袱"的循环。
2. **素材**：
   - 原生分辨率的截图，保留 UI 外框（推文、终端、论文页、图表）；
   - 梗的格式自己重做（改换内容、重新画），不直接用有版权的梗图原图；
   - 不用真实品牌 logo（Pip prompt 也明确禁止）。
3. **视觉系统**：
   - 先建一个固定网格，再故意打破它。刻意的丑也要成体系（Internet Ugly）。
   - 配色：`#111` 底、`#F0F0F0` 字，加一个警报强调色 `#D4501E`。
   - 字体：大写的等宽标签（Space Mono），配一个粗重的 grotesk（Space Grotesk）。
   - 直角，0px 圆角。
4. **节奏**：
   - 每 0.5–1.5 秒一个硬切，落在拍子上；
   - 2 帧的 punch-in（缩放 100 → 115%）；
   - 文字用 `steps(4–8)` 逐步出现；
   - 包袱处定格，再加标注；
   - glitch 只用在 1–2 个段落分界处。
5. **笑点时序**：铺垫 1–2 秒 → 0.4 秒静默 → 包袱 + 音效。每个笑点要在 1 秒内看懂。
6. **全片只用一次平滑缓动**：留给高潮处的一个慢推镜头，形成反差。

## 审美要点

- 在 HyperFrames 里，硬切的语义是"惊醒、打断"，本类就是要用它。
- donald jewkes 的 prompt 里提到的方向：
  - 用 internet brutalism 的方式直接插入素材；
  - 融入当下时间线上的梗；
  - 面向旧金山科技推特的受众；
  - 开头要有很强的视觉 hook。

## 禁止

- 披着野兽派外衣的圆角玻璃卡片；
- 没有笑点的随机混乱；
- 满屏 glitch；
- 有版权的梗图原图、真实品牌 logo；
- 超过 1 秒才能看懂的笑点。

## Prompt 增量块

```text
+ TYPE: tech-Twitter / internet-brutalist cut. {1080x1350 | 1920x1080}, 30fps, {15–40}s, sound-on.
Start from HyperFrames' "Deconstructed" (Neville Brody) preset. Visual system: raw screenshots at native resolution with UI chrome, caps monospace labels (Space Mono), one heavy grotesk (Space Grotesk), #F0F0F0 on #111 + one alarm accent #D4501E, 0px corners, a visible grid the edit deliberately breaks.
Motion: hard cuts every 0.5–1.5s on beats; 2-frame punch-ins (100→115%); steps(4–8) for text; freeze-frame + label on punchlines; glitch only at 1–2 section breaks. Smooth easing only for one slow push at the climax.
Comedy timing: setup 1–2s → 0.4s silence → hit + SFX; every joke must read in under 1s. Punchlines: {list}.
Recreate meme formats originally; no copyrighted images or real brand logos.
```

## 自查重点

- 每个笑点能在 1 秒内看懂吗？
- 包袱前有没有 0.4 秒的静默？
- 硬切是不是都落在拍子上？
- 所谓"破坏"是不是在一个成立的网格上的破坏？
- 有没有侵权素材？

## 可参考的案例与源码

- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md`：第 3 节 Deconstructed、第 4 节 Maximalist Type，以及文末的 Mood → Style Guide。
- `references/repos/hyperframes/_upstream_claude/skills/cut-the-curve/`：速度匹配的转场技法目录；硬切之外需要一两个炫技转场时参考。
- `cases/mv-claude-pop.md`：prompt 里的 internet brutalism 要求和面向受众的思路。
- `cases/community-prompts.md`：@goodside 的一句话分屏 prompt。

## 社区 skill 参考

以下条目选自 183 个社区视频 skill，完整对照和许可证说明见 `references/community-skills.md`。只读参考；复用代码前，先确认它的许可证。

- **viral-video-decomposer**（MIT）：镜头级拉片 → 爆款机制 → 变量槽 → JSON brief；只借结构，不照搬原片的文案和镜头。见 `references/repos/viral-video-decomposer/skill/SKILL.md`，配合 `playbook/07-reverse-engineer.md` 使用。
- **lemo-opuscar 的 `halftone-dossier` / `microgame` 风格**（CC BY 4.0）：半调档案风的"模拟调查"，以及越来越快的微游戏快闪。见 `references/repos/lemo-opuscar/styles/halftone-dossier/STYLE.md`、`references/repos/lemo-opuscar/styles/microgame/STYLE.md`。
