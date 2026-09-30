# 02 知识 / 科普短视频（含竖屏）

**适用**：
- 30–90 秒的概念科普、冷知识、how-to、清单体；
- 投抖音、B站、小红书、视频号、YouTube Shorts、TikTok；
- 没有真人出镜的 faceless 讲解。

**不适用**：
- 需要精确推导的数学，看 `01`；
- 论文，看 `06`，可以借本类的竖屏规格；
- 有真人口播素材要剪辑、加字幕和图解的，走 `09`（实验中）；只在已有口播上叠图解、不剪的，仍可走本类，再加 `playbook/05-hybrid-genvideo.md` 的 B 模式。

## 引擎

- **首选**：HyperFrames。`bin/vh new short <slug>` 会自动以竖屏初始化，不会往全局装 skill。
  - **短片或静音片**：读 `references/repos/hyperframes/skills/faceless-explainer/references/` 里的设计资料，手写一个 `index.html` 最快。showcase 02 就是这么做的。
  - **长片、有旁白、多场景**：可以走 HyperFrames 官方的 `/faceless-explainer` 工作流（每一帧派一个 subagent，带音频同步脚本）。它需要装插件或全局 skills（要用户同意），部分功能依赖 HeyGen 账号。
- **备选**：Remotion + `template-tiktok`（用 whisper.cpp 做字幕）。
- 穿插公式或几何片段时，用 Manim 单独渲染成片段，再嵌进来。

## 工作流

1. **定平台和画幅**：
   - 抖音、Shorts、TikTok、视频号用 1080×1920；
   - 小红书封面要 3:4；
   - B站知识区可以做 16:9 中长视频，信息密度可以更高。
2. **写 SCRIPT.md**：
   - 第 1 秒给出结论、反常识的数字或有冲突的画面，不放 logo，不说"大家好"；
   - 3 秒内讲清看完能得到什么；
   - 之后每 3–5 秒给一个新的视觉回报；
   - 字数按中文语速 4–5 字/秒倒推，45 秒约 200 字【综合】。
3. **音频先行（有旁白时）**。静音版跳过这一步：时长由分镜的 reads 决定，字幕承载全部信息，而且必须静音可读。
   - 把旁白逐句写进 `audio/script.txt`，运行 `bin/vh tts <项目> <provider> [voice]` 生成 `voiceover.wav` 和 `timeline.json`。草稿用 `say`，正式版用 `gemini`、`dashscope` 或 `elevenlabs`（见 `playbook/04-audio.md`）；
   - 旁白要导演：整体语气用"像在跟朋友讲一个惊人的事实：好奇、有起伏，关键词重读"，每句再在 `[ ]` 里单独导演；有配乐时加 `--beats` 让每句从拍点起。细节见 04 篇"让声音有表情、有节奏"；
   - 用 FunASR 拿字级时间戳，写入 `audio/timeline.json`；
   - 删掉口水词，在 ≥250ms 的停顿处断句。
4. **分镜**：
   - 一镜一个观点，切点放在旁白短语的边界上；
   - 剪辑频率（第三方统计）：TikTok 1.5–3s，Reels 2.5–4s，Shorts 教程类 3–5s。
5. **字幕**：
   - 单行，字号 72–90px，字重 800。竖屏安全框只有 810px 宽，所以 72px 时每行最多 11 个汉字，90px 时最多 9 个。横屏 16:9 才能用到每行 16 字；
   - 只用一个强调色，每句最多强调 1–2 个关键词；
   - 不要永远固定在下三分之一，每 30 秒打破一次节奏；
   - 强调的分布大致是：70% 平常，20% 轻强调，8% 完全强调，2% 高潮。
6. **安全框**：关键内容放在 x 90–900、y 330–1520 之内，背景可以铺满。
7. **交付**：
   - 视频在第 1 秒静音状态下就能看懂；
   - 另外出一张封面图；
   - 可选导出 SRT 字幕。要交给人工精修，**不要承诺一键导出剪映草稿**：剪映 6.0 起本地草稿是加密的，`pyJianYingDraft` 只在 5.9 和 6.8 上测过导出，新版（10.x）有草稿被判损坏的报告。稳妥的做法是 `final.mp4` 加 `captions.srt` 加分层素材包，或者走 CapCut 国际版（明文草稿）、FCPXML、OTIO，做法和各自的限制见 `09-editing-talking-head.md` 的"导出"一节。

## 审美要点

- **"Kurzgesagt meets Fireship"** 是现成可用的一句风格描述：扁平矢量图形、一个强调色、冷幽默、100 秒讲清一件事（按 what / why / how / when 组织）。
- **中文圈可点名的参考**：
  - 回形针 PaperClip：高信息密度的可视化；
  - 小 Lin 说：口播加图解；
  - 小红书封面：大字、高对比、系列化模板。
- **结尾**：落在回报画面上，不放"关注我"卡片。

## 禁止

- 每个字都上色、描边、放大的"全程 Hormozi 体"；
- 字幕落进平台 UI 遮挡区；
- 蓝紫科技渐变配粒子背景；
- 图库图标；
- 不留停顿的 TTS；
- 超过 3 秒画面没有任何变化。

## Prompt 增量块

```text
+ TYPE: vertical knowledge short. 1080x1920 30fps {30–60}s, {zh-CN narration + burned-in captions | SILENT: captions and visuals carry everything, timing from storyboard reads}. Platform: {抖音 | 小红书 | 视频号 | B站 | Shorts}.
Style: "Kurzgesagt meets Fireship": flat vector shapes, one accent, dry humor. NOT: blue-purple tech gradients, particle backgrounds, stock icons.
0–1s: the counterintuitive claim/number as a full-bleed visual (no logo, no greeting). By 3s: what the viewer will learn.
A new visual payoff every 3–5s; one idea per shot; cut on narration phrase boundaries.
Captions: one line, <=11 CJK chars at 72px (<=9 at 90px; the vertical safe box is 810px wide), 72–90px, weight 800, #F5EFE6 with 3px dark stroke; accent on 1–2 key words max; split at pauses >=250ms; drop filler words. Hook text 140px.
Safe box x 90–900, y 330–1520 (platform UI zones stay clear). End on the payoff visual, not a subscribe card.
Also export a 3:4 cover frame with the hook text.
```

## 自查重点

- 静音观看时，第 1 秒能看懂在讲什么吗？
- 字幕有没有进入遮挡区？
- 有没有超过 3 秒的死画面？
- 数字和事实在 `NOTES.md` 里有出处吗？
- 最好拿一张平台截图叠在联系表上，检查 UI 遮挡。

## 可参考的案例与源码

- `cases/community-prompts.md`：@AxtonLiu 的口播图解做法、@dotey 的中文讲解 prompt。
- `references/repos/hyperframes/skills/faceless-explainer/`：
  - `SKILL.md`：完整流程，包括 BRIEF → frame.md → STORYBOARD → 音频 → 线框草图 → 每个 frame 派一个 subagent；
  - `references/` 下的 `story-design.md`、`visual-design.md`、`motion-language.md`、`cut-catalog.md`。
- `references/repos/hyperframes/skills/embedded-captions/references/`：`aesthetic-principles.md`、`anti-patterns.md`、`caption-grouping.md`、`layout-heuristics.md`，这些是字幕设计最全的资料。
- `references/repos/remotion-skills/skills/remotion-captions/`：Remotion 路线的字幕做法。

## 社区 skill 参考

以下条目选自 183 个社区视频 skill，完整对照和许可证说明见 `references/community-skills.md`。只读参考；复用代码前，先确认它的许可证。

- **claude-faceless-shorts-creator**（MIT）：节拍语法 HOOK → SETUP → QUIZ → REVEAL → TWIST → LOOP；第 0 帧就是完整画面，末帧等于首帧，可以无缝循环；不放"评论区告诉我"式的 CTA。见 `references/repos/faceless-shorts-creator/_upstream_claude/skills/make-short/SKILL.md`。
- **procedural-film**（MIT，不在 183 个 skill 的清单里）：零媒体素材的 30 秒竖屏短片，一个镜头一个 agent；六项关卡 `check.cjs` 从桩场景那一步起就必须全绿，确定性检查把首、中、尾帧按正序、倒序、冷启动分别画出来比哈希；竖屏底部 380px 留给平台 UI。见 `references/repos/procedural-film/skills/procedural-film/SKILL.md`。
- **gbro-collage-info**（MIT）：竖屏半调纸拼贴信息动画，纯 HTML/GSAP，不用图像模型；信息只放在上 2/3，底部 640px 留给字幕。见 `references/repos/gbro-collage-info/SKILL.md`。纸拼贴 / Vox 风的三种做法对比见 `references/community-skills.md` 第 4 节。
