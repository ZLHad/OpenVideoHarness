# 04 歌词视频 / MV / 音乐动画

**适用**：给一首歌（自己用 Suno 生成的、AI 生成的、或者有授权的）做 MV、歌词视频、配合音乐的宣传动画。

## 两条路线，先选一条

| | A. 绘画式 MV | B. 动态排版 / 歌词视频 |
|---|---|---|
| 核心 | 画面讲故事，**歌词不上屏**（或者只保留一条卡拉 OK 字带） | 文字本身就是画面，排版是主角 |
| 引擎 | ClaudeAnimationBase（p5.brush），或者自己写 WebGL 笔触渲染器 | HyperFrames `/music-to-video` |
| 范例 | PDoom（p5.brush，9 章）、Functional Emotions（自写 WebGL，6 万笔触，8 章） | HyperFrames 风格库里的 Maximalist Type（Paula Scher）、Deconstructed（Neville Brody） |
| 风险 | 工作量大，一般要多个 subagent 并行 | 容易做成"歌词幻灯片" |

Functional Emotions 的教训：第一版是精致的排版歌词视频，被否掉了，用户的理由是"还是歌词视频"。所以用户说要"MV"时，默认走 A 路线，除非用户明确要的是歌词视频。

## 工作流

0. **歌从哪里来**：用户提供（Suno 等网页生成后下载，或有授权的曲目）；需要纯器乐时可以用 `bin/vh music` 写一首，这样节拍表是精确的；带人声的歌曲生成模型只留了接口（见 `playbook/04-audio.md` 的"歌曲"一节）。
1. **音频分析**（`playbook/04-audio.md`）：
   - `bin/vh beats audio/song.mp3 audio/beats.json` 求 BPM、beats 和 downbeats，写入 `audio/beats.json`（不给第二个参数时写到 `audio/song.beats.json`）；需要更准的 downbeat 和段落结构（主歌、副歌、间奏）时，用 beat_this 或 all-in-one；
   - 歌词逐句、逐词对齐：先用 Demucs 分离人声，再用 Whisper 分块转写，最后把真实歌词对齐到转写结果上。functional-emotions-video 的 `analysis/` 目录有完整的脚本（`features.py`、`transcribe.py`、`align.py`、`build_data.py`），可以直接改来用；
   - 结果写入 `audio/timeline.json`。
2. **定故事和世界**：
   - 写 logline、主角、母题、调色板弧线（比如每个章节换一个色调）；
   - 副歌每次回到同一个布景，逐次升级。PDoom 的做法是：派对 → 烟火和蛇怪 → 回形针洪水 → 红色警报。
3. **STORYBOARD.md**：
   - 每句歌词对应一个镜头，每镜 1.4–4 秒；
   - 规则是**每个镜头都要发生一件事**；
   - 转场要有动机：一口咬下去黑屏、火箭升空、坠落、从眼睛推进去、心形泡泡破裂、门砰地关上；
   - 大的切换放在小节线上。
4. **契约**：写 `ANIMATION_GUIDE.md`，内容包括画布、安全字带（PDoom 的卡拉 OK 字带在 y 975–1070，人脸要保持在 y 960 以上）、调色板、API、节拍函数（`pulse`、`beatN`）和禁止项。
5. **主 agent 先做一个样板章节**，再派 subagent，每人负责一个章节（见 `playbook/01-pipeline.md`）。主 agent 看每个章节的联系表，写批注退回，直到满意。
6. **节奏复审**：在交付前，把 PDoom 当作节奏标尺来对照：镜头短，每镜一个动作，镜头一直在动，重音落在拍子上，切换有动机，画面不能静止太久。

## 审美要点

- **A 路线**：
  - 沿用 ClaudeAnimationBase 的三个目标：手绘感、活着、浑然一体；
  - 角色情绪不要硬切，要有预备动作、挤压拉伸和弹出的表情符号；
  - 主角在副歌和舞蹈镜头里要大，约占画面高度的 40%。
- **B 路线**：
  - 文字分两档：主歌用字幕尺寸（60–72px）；hook 和副歌用满屏大字（300–600px，字重 900，字距 -0.04em）；
  - 大字出现时，背景要安静，画面元素让到另一侧的三分之一；
  - 开头的 hook 用大字，这是最强的注意力抓手（donald jewkes 的要求）。
- **两条路线通用**：
  - 切点和重点词的出现都落在拍子上，误差 ±1 帧；
  - 同一种入场方式不要连续用超过 3 次【综合】；
  - 可以借鉴 K-pop MV 调度注意力的方式：视觉模式的重复与打破、群舞队形、镜头节奏。

## 禁止

- 每个词都用同一种入场动画；
- 对 `letter-spacing` 做动画；
- 整首歌都用打字机效果；
- 落点偏离节拍超过 2 帧；
- 每个词一种颜色；
- 画面静止超过一拍而没有意图；
- 场景之间彼此无关，没有东西串起来。

## Prompt 增量块

```text
+ TYPE: music video. 1920x1080 30fps (or 24), exact song length {N}s. Inputs: {song.mp3}, lyrics {lyrics.txt}.
Route: {A painted MV: visuals carry the story, lyrics only as a karaoke band y 975–1070 (or none) | B kinetic typography: text is the main visual}.
First build beats.json (BPM, downbeats, sections) and word-timed lyrics (Demucs → Whisper → align known lyrics); every cut and every hero hit lands on a beat (±1 frame); big changes on bar lines.
Write a story with one protagonist and a motif; choruses return to the same set and escalate each time; palette arc per section: {arc}.
Shots 1.4–4s; something happens in every shot; motivated transitions (cut on action, match cut, chomp-to-black, push through an eye…), never a plain crossfade.
{B only: two text registers: subtitle-size 60–72px for verses; full-bleed hero words 300–600px weight 900 tracking -0.04em for hooks; when text is huge the background goes quiet. Open with a hero-size hook line.}
Director builds chapter 1 as the reference; then one subagent per chapter, briefed by ANIMATION_GUIDE.md, editing only its own file; review every chapter on contact sheets before accepting.
This is a music video, not a lyric slideshow.
```

## 自查重点

- 把联系表和 `beats.json` 放在一起看：切点在拍子上吗？
- 副歌布景是否每次都有升级？
- 章节接缝处（前后各 0.5 秒）方向和颜色是否衔接？
- 有没有哪段画面在某一拍上什么都没发生？
- 按 Functional Emotions 的标准问一句：这是 MV，还是歌词视频？
- 旁白或念白（如果有）是否贴着拍子、句间留白？每个画面重音是否有声音回应？见 `playbook/04-audio.md`"让声音有表情、有节奏"。

## 可参考的案例与源码

- `cases/mv-pdoom.md`：p5.brush 路线的完整案例，源码在 `references/repos/PDoomVideo/`（`STORYBOARD.md`、`ANIMATION_GUIDE.md`、`src/ch/c01_lab.js` 到 `c09_finale.js`）。**没有 license，只能阅读参考。**
- `cases/mv-functional-emotions.md`：歌词对齐流水线，外加主 agent 先做样板、7 个 subagent 并行；源码在 `references/repos/functional-emotions-video/`（MIT），渲染器是 `js/paint.js`。
- `cases/mv-claude-pop.md`：生成式视频加 JS 转描的混合路线。
- `references/repos/hyperframes/skills/music-to-video/`：B 路线的完整流程，`references/` 下有 `planning.md`、`storyboard-format.md`、`montage.md`、`motion-primitive-catalog.md`、`template-catalog.md`。
- `references/repos/hyperframes/skills/hyperframes-creative/references/beat-direction.md` 和 `audio-reactive.md`。

## 社区 skill 参考

以下条目选自 183 个社区视频 skill，完整对照和许可证说明见 `references/community-skills.md`。只读参考；复用代码前，先确认它的许可证。

- **lemo-opuscar 的时间线**（MIT）：一份 `timeline.js` 同时驱动配乐、字幕和检查脚本；`cuecheck.py` 核对画面卡点，目标误差 0 ms。见 `references/repos/lemo-opuscar/TECHNIQUE.md` §3（中文版已删，只有英文）、`references/repos/lemo-opuscar/styles/microgame/demo/tools/cuecheck.py`。
- **bestagentkits/motion-video-skill**（MIT，未拉取）：HyperFrames 卡点动态图形，带卡拉 OK 字幕，适合 B 路线。
