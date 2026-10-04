# BRIEF · OpenVideoHarness 介绍片 v5

<!-- 关卡 ① 草稿，2026-10-01。只写目标、观众、放在哪、多长；细节在 REVIEW-gate1.md、STORYBOARD.md（节拍表）、NOTES.md。
     v3：showcase/04-intro-film/v3/（81 s，文档和成片；源码在提交 c649392）。v4 修订计划的发现照用，格式不用。 -->

## Spec
- Effort: studio  <!-- 旗舰片：README 首屏、B站、X。档位可以由你降 -->
- 目标：新开场讲清“工具很多，差的是什么”，然后跟着一句需求走完 harness，最后揭晓这支片子也是它做的。
- 观众：用 Claude Code / Codex 的开发者，和中文 AI 视频圈（B站、小红书、X）。
- 放在哪：
  1. README 首屏：一段无颗粒的 GIF（开场“压平 → 终端”约 8–10 s），链到完整 mp4；
  2. B站：完整版，横屏 16:9，可开中英字幕；
  3. X：自动播放、静音 → 必须静音也读得懂；完整版 1:46 在普通账号的时长上限（约 2 分 20 秒，发布前按当时规则再核）以内，可以直接发；另可用开场加片名剪一支约 30 s 的预告（可选）。
- 长度：关卡 ① 时定的是**完整版 1:46**（53 小节 @ 120 BPM，3180 帧），紧凑版 1:18 作为备选（决定 1）；成片是 103 s（3090 帧，见上面的 Output 一行和 DECISIONS.md）。开场 22 s。
- Output：1920×1080，30 fps，exactly 103.0 s（3090 frames）；引擎 HyperFrames 0.8.82 + Three.js（沿用 v3 的一镜到底）。
- Resolution: 1080p, 4k
- 语言：双语动态字，en 主版英文大字 + 中文副行；zh 版反过来（同一套代码切 `lang`）。旁白：（待定），主版不配旁白。
- 声音：代码作曲（`bin/vh music`，按章节写，一个主旋律贯穿）+ 代码音效，-14 LUFS。

## Content
- Spine：AI 做视频的工具多到数不清，人被淹没；差的不是再多一个工具，是做片子的门道；OpenVideoHarness 把这些经验交给写代码的 agent，你说一句话，它读懂、停下来问你、自己检查，交出片子——这支片子也是。
- Takeaway：看完的人知道：它不是又一个工具，是让 Claude Code / Codex 做视频做得稳的“经验 + 引导”；一句话就能开始。
- 母题：一句话需求。开场在终端里打出来，全片跟着它走，Ch4 变成成片；主旋律 B（F# A B）在问句里悬住，片尾落到 D。
- 素材：README / CLAUDE.md / TASTE_CHECKLIST 的原文，showcase 00–03 的成片，本片自己的配乐代码。事实表见 NOTES.md，渲染前再核。

## Style
- 沿用 v3「帧的档案馆」：近黑底、唯一的琥珀强调色只以光出现、一镜到底（showcase/04-intro-film/v3/STYLE.md）。
- v5 的改动：开场的工具卡片允许杂色（代表“市面上的”），harness 出现后回到只有琥珀。
- 不要：真实产品的 logo 和名字（只用通用类别名）、紫青渐变、玻璃拟态、任何一帧照抄真实 App 的界面。

## Acceptance
- [ ] 所有上屏字过 `bin/vh readcheck`（中、英分别算）；关卡 ① 的计划已 26/26 通过（review/onscreen-plan.json）
- [ ] 全屏闪白每秒不超过 3 次（计划全片 1 次）
- [ ] 每个数字在 NOTES.md 有出处，渲染前按当时的 main 再核一遍
- [ ] 配乐：唯一最高点在全片 60–85 %，比第二高的段高 ≥ 2 LU；问句段是全片最静；`bin/vh qa` 通过
- [ ] 第 0 帧就是完整画面；静音看得懂

## TYPE
+ TYPE: product launch film. 1920x1080 (+1080x1350 and 1080x1920 re-framed cuts) 30fps {15–30}s, music-driven, SFX on key hits.
Register: {Apple: black/white, one claim per shot, macro crops of the real UI | Linear/Vercel: near-black #0A0A0B, 1px hairlines, blueprint grid at 6% opacity}. Font {Geist/Geist Mono | SF-like grotesk}. No gradient text, glassmorphism, or purple-cyan gradients.
One continuous virtual camera; camera moves 1.5–3s easeInOutCubic, about half your default speed; motion blur on fast moves; light grain.
Beats: hook promise (0–3s) → problem (1 beat) → 3 feature beats, each = the real UI doing the thing, triggered by an oversized cursor click → proof count-up → 0.5s stillness → logo lockup.
Use real copy/assets from {URL / assets/}; recreate the UI accurately; no placeholder text or invented numbers.
Show the product itself: {architecture | workflow | features | case studies} as motion infographics built from its real diagrams and docs, labels copied verbatim.
{Optional mascot/voice: a character introduces the product; voice via {ElevenLabs | local TTS}, captions synced to word timestamps.}

<!-- from 03-product-promo.md -->
