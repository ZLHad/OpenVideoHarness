# 案例：I'm Upping My P(doom)

**类型**：歌词 MV，手绘水彩风格；长 156.6 秒，1080p，24fps
**源码**：`references/repos/PDoomVideo/`。仓库**没有 license**，只能阅读参考，不要复用其中的代码或资源。
**来源**：[repo](https://github.com/JohnHeibel/PDoomVideo)、[NotinReality 的原帖](https://x.com/other__reality/status/2102514581684052169)

## 来龙去脉

1. deckard 发了一首 AI 生成的歌《Claude-Pop - I'm Upping My P(Doom)》。
2. NotinReality（John Heibel）用 Claude Opus 5.5 在 Claude Code 里给这首歌做了 MV，并开源了代码。之后他又整理出一个通用的起步模板 ClaudeAnimationBase，也就是本工作台的 `engines/ClaudeAnimationBase/`。
3. 有人在这个基础上继续创作：
   - donald jewkes 写了一个超长 prompt，做了升级版，见 `mv-claude-pop.md`；
   - pleometric 照 donald 的流程做了一版；
   - mexicat 换成暗色示波器、终端、表格文档的风格，"调了几轮"；
   - YC 做了中文版：重新填中文词，用 Suno 翻唱，再让 Claude Code 把动画重新对齐到新音轨。他称之为 "Video-as-code：视频可以像代码一样 Fork & Remix"。

## 怎么做的

**两轮生成**
- 第一轮在 `legacy/` 目录，用的是 Opus 5.5（Medium）。
- 第二轮是仓库里的其他部分，用的是 Opus 5.5。README 称所有内容都由模型生成，场景创意也没有人工指定。人只给了两条方向：使用 Clawd 角色形象；每句歌词都要有有趣的画面和转场。
- 第一轮之后，人追加了三条要求：改用 p5 笔刷，每个场景都要有意思，每个场景都要衔接到下一个。模型据此写出了 `STORYBOARD.md`。

**文件结构**
- `STORYBOARD.md`：逐镜头的时间、歌词、画面和出场转场，另有调色板的变化弧线。
- `ANIMATION_GUIDE.md`：模型写给并行 subagent 的简报，内容包括画布、安全字带、调色板、绘画 API、角色 API、节拍函数。
- `src/ch/c01_lab.js` 到 `c09_finale.js`：9 个章节，每章一个文件。
- `src/` 下的公共文件：角色、道具、歌词、时间线。
- `render.mjs`：Puppeteer 驱动无头 Chrome，调用 `renderAt(t)` 逐帧渲染。它支持联系表（`--sheet`）、静帧、带音频的短片段、4 个 worker 并行且可续跑的全帧渲染，最后由 ffmpeg 合成。

**给 subagent 定的规矩**（见 `ANIMATION_GUIDE.md`）
- 每个章节包在一个 IIFE 里。
- shot 函数写成 `fn(t, lt, dur)`，每次都要画完整一帧，背景也要画。
- 帧是乱序并行渲染的，所以每个镜头必须是 t 的纯函数：不能用 `Math.random()`，要用 `hash(i)`。
- `jit` 每秒重设种子 12 次，让线条"boil"。
- 每人只改自己的章节文件；共享文件发现 bug 要报告，不能自己改。

**时间**
- 88 BPM，一拍 0.682 秒，重音落在 0.21 + n×0.682 秒。
- 章节之间的画笔擦除转场放在 1.5 / 38.5 / 73.0 / 109.4 秒。

## 为什么有效

- **故事有反转**：整支 MV 是一场失控的舞台剧，从剧院幕布开场，也以幕布收尾。最后一句 "Was it all for show?" 揭示前面的末日只是一场戏：巨型 Clawd 是三个小 Clawd 套的戏服，蛇怪是木偶。
- **每个镜头都有事发生**：每镜必须有一个角色在做事，或者有东西在坏掉、变形、追逐、坠落。
- **文字很少**：笑话全靠画面讲；全片只用了少数几个大的拟声词（FOOM、BOOM、CHOMP）；不给东西贴标签，也不让牌子重复歌词，因为卡拉 OK 字带已经显示了歌词。
- **副歌每次升级**：四段副歌都回到同一个舞台，一次比一次夸张：派对 → 烟火和蛇怪 → 回形针洪水 → 红色警报。P(doom) 计量表依次从 8 → 34 → 61 → 86 → 99.9 往上泵。
- **配色有弧线**：暖奶油色的灯光 → 天蓝 → 太空紫金 → 钢蓝和爵士蓝 → 数据中心青 → 警报红 → 回到剧院的深红和金色。
- **转场有动机**：一口咬到黑屏、火箭升空、坠落、从眼睛推进去、心形泡泡破裂、炸弹闪光、穿破地板、门猛地关上。

## 能借用什么

- 长片的"契约文件 + 按章节并行 subagent"结构：`playbook/01-pipeline.md`。
- STORYBOARD 的表格格式：每镜一行，列为"时间 | 歌词 | 画面 | 出场"。
- 副歌回到同一布景并逐次升级；配色弧线；首尾呼应。
- 视频就是代码，所以换歌、换语言、换风格都是 fork 一份再改（YC 的中文版）。
