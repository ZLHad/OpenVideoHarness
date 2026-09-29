# SCRIPT：旁白草稿（DRAFT，关卡 ①）

<!-- 给关卡 ① 判断语气用。还没有合成任何音频。定稿后改写成 audio/script.txt（格式 `中文 || English`，bin/vh tts 读取）。
     时间按 28 小节 @ 112.5 BPM 的大纲来排；如果选了带旁白的方案，时长由实测旁白决定，配乐代码按实测长度重排。 -->

**语气**：平静、笃定，不煽情。像一个设计师在 meetup 上给你演示，不像预告片配音。句子短，动词在前，不用"革命性""颠覆"这类词。

**怎么用**：
- **方案 A（推荐主版本）**：不配音。下表"屏幕字"一列就是片中的动态字。en 主版是英文大字加中文小字，zh 主版反过来。
- **方案 B / C**：念"旁白"两列。全稿中文约 45 s、英文约 47 s，对一支 60 s 的音乐片太满。标 ◇ 的句子改用括号里的短版，可以压到约 35 s。
- **候选音色**（`bin/vh tts <p> qwen <voice> <lang>`）：中文 Serena（温暖女声）或 Vivian，英文 Ryan 或 Aiden。选定 B / C 后各合成一版给你试听。首次运行要下载约 2 GB 权重，下载前先问你。

| 段 | 时间 | 屏幕字（方案 A） | 旁白 · 中文 | Narration · English |
|---|---|---|---|---|
| 1 Hook | 0:00–0:04 | Every frame is a function of time.<br>每一帧，都是时间的函数。 | 每一帧，都是时间的函数。 | Every frame is a function of time. |
| 2 Code2video | 0:04–0:11 | Claude Opus 5.5 doesn't paint pixels. → It writes the program. → One sentence in. A film out. | Claude Opus 5.5 不画像素，它写程序。一句话进去，一支片子出来。 | Claude Opus 5.5 doesn't paint pixels. It writes the program. One sentence in, a film out. |
| 3 转折 | 0:11–0:15 | Stunning, once. / Dependable? Not yet.<br>惊艳，一次。/ 稳定？还不行。 | 一句话能做出惊艳的片子，但做不出稳定的片子。 | One sentence can make something stunning. Not something dependable. |
| 4a 名字 | 0:15–0:17 | OpenVideoHarness<br>turns Claude Code & Codex into a video studio | ◇ 这是 OpenVideoHarness，把 Claude Code 和 Codex 变成一间视频工作室。（短：这是 OpenVideoHarness。） | ◇ This is OpenVideoHarness. It turns Claude Code and Codex into a video studio. (short: This is OpenVideoHarness.) |
| 4b 路由 | 0:17–0:21 | Routed to 1 of 8 video types.<br>先路由：8 类视频选一类。 | 每个需求，先路由到 8 类视频中的一类。 | Every request is routed to one of eight video types. |
| 4c 关卡 | 0:21–0:28 | It stops 3 times. You decide.<br>停三次，等你拍板。 | 它会停三次：大纲、分镜、初版，等你拍板。 | It stops three times: outline, storyboard, first draft. And waits for you. |
| 4d 自查 | 0:28–0:34 | It can't watch video. → It reads its own frames. → 20 taste checks. Fix. Re-render. | ◇ 它看不了视频，就读自己渲染出的帧，对照 20 条品味清单，不合格就返工。（短：它看不了视频，就读自己的帧，不合格就返工。） | ◇ It can't watch video, so it reads its own frames, checks them against twenty rules of taste, and fixes what fails. (short: It can't watch video, so it reads its own frames and fixes what fails.) |
| 5 成片 | 0:34–0:49 | 每支片子一个标签：类型 · 引擎 · 时长 · 渲染耗时，加一句 premise（都取自 README 原文） | ◇ 手绘短片、数学讲解、竖屏科普、发布片，都是 agent 只照着这套文档做出来的。（短：都是 agent 只照着这套文档做的。） | ◇ A hand-drawn short. A math explainer. A vertical science short. A launch film. All made by an agent following only these docs. (short: All made by an agent, following only these docs.) |
| 6 揭晓 | 0:49–0:53 | This film, too. → Even the soundtrack is code.<br>这支片子也是。→ 连配乐都是代码。 | 这支片子也是。连配乐，都是代码。 | This film, too. Even the soundtrack is code. |
| 7 CTA | 0:53–0:60 | OpenVideoHarness · Video as code, for coding agents.<br>`bin/vh new <type> <slug>` · github.com/ZLHad/OpenVideoHarness | OpenVideoHarness，开源。一条命令就能开始。 | OpenVideoHarness. Open source. One command to start. |

## 写进 audio/script.txt 的样子（预览，短版）

```text
# DRAFT — gate ①; not synthesized. Format: 中文 || English
@p1   每一帧，都是时间的函数。 || Every frame is a function of time.
@p2a  Claude Opus 5.5 不画像素，它写程序。 || Claude Opus 5.5 doesn't paint pixels. It writes the program.
@p2b  一句话进去，一支片子出来。 || One sentence in, a film out.
@p3   一句话能做出惊艳的片子，但做不出稳定的片子。 || One sentence can make something stunning. Not something dependable.
@p4a  这是 OpenVideoHarness。 || This is OpenVideoHarness.
@p4b  每个需求，先路由到 8 类视频中的一类。 || Every request is routed to one of eight video types.
@p4c  它会停三次：大纲、分镜、初版，等你拍板。 || It stops three times: outline, storyboard, first draft. And waits for you.
@p4d  它看不了视频，就读自己的帧，不合格就返工。 || It can't watch video, so it reads its own frames and fixes what fails.
@p5   都是 agent 只照着这套文档做的。 || All made by an agent, following only these docs.
@p6   这支片子也是。连配乐，都是代码。 || This film, too. Even the soundtrack is code.
@p7   OpenVideoHarness，开源。一条命令就能开始。 || OpenVideoHarness. Open source. One command to start.
```
