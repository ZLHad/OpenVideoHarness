<div align="center">

# OpenVideoHarness

**一句话需求，交给 Claude Code / Codex，出一支像样的视频，而且每次都靠谱。**

用代码做视频（video-as-code）的开源工作台：科普、讲解、发布片、MV、数据、论文、手绘、梗，8 类视频一套流程。

[English](README.md) · **中文**

![License: MIT](https://img.shields.io/badge/license-MIT-black)
![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-orange)
![Engines](https://img.shields.io/badge/engines-HyperFrames%20%7C%20Remotion%20%7C%20Manim%20%7C%20p5.brush-blue)
![Voice](https://img.shields.io/badge/voice-Qwen3--TTS%20zh%20%7C%20en-purple)
![Video types](https://img.shields.io/badge/video%20types-8-green)

<a href="showcase/00-promo-launch-film/"><img src="showcase/00-promo-launch-film/media/poster.png" width="820" alt="OpenVideoHarness"></a>

</div>

---

## 这是什么

2026 年 9 月，时间线上冒出一大批"Opus 5.5 一句话做出来的视频"：黑洞科普、手绘 MV、产品发布片、数学动画。它们用的是同一种做法：模型不直接生成像素，而是**写一个程序，程序里每一帧都是时间 t 的函数**，再由浏览器或 Manim 逐帧渲染，ffmpeg 合上声音。Show Lab 的 [Code2Video](https://github.com/showlab/Code2Video) 已经在教学视频上验证过这条路。

一句话能做出惊艳的片子，但做不出**稳定**的片子。换个题材，节奏就乱了，AI 味冒出来了，数字也开始编了。

OpenVideoHarness 不是新的渲染器，而是一套**给 agent 用的"挽具"（harness）**。它把论文、开源 skill 和社区实验里零散的经验，整理成 agent 照着就能做的结构：

- **按类型路由**：说"做个科普""做个发布片"，agent 会找到对应的那份工作流，里面写好了用什么引擎、分几步、审美要点、禁止项、提示词模板和参考案例。
- **人始终在回路里**：大纲、分镜、初版三道关卡，agent 每到一关都停下来等你拍板。改动发生在最便宜的时候。
- **把品味写成数字**：缓动曲线、镜头时长、字号下限、竖屏安全区、字幕密度，外加一张 20 条的自查清单。
- **自己看、自己改**：agent 看不了视频，就让它看渲染出的帧。联系表看结构，逐帧条看节奏，局部放大看细节，发现问题就改。
- **声音一条龙**：中英双语配音（默认用本地开源的 Qwen3-TTS）、双语字幕、代码作曲、音效、混音，全在 `bin/vh` 里。
- **开箱即用**：一条命令安装，一条命令建项目；仓库自带一个手绘引擎，装完就能出片。

## 30 秒开始

```bash
curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
```

它会把仓库克隆到 `~/OpenVideoHarness`，安装内置引擎，拉取参考资料，再把 `open-video-harness` skill 注册到 Claude Code 和 Codex。之后在任何目录说"做个视频"，agent 都能找到这里。环境要求见下文。

然后进入仓库，打开 Claude Code（或 Codex），直接说你要什么：

```bash
cd ~/OpenVideoHarness && claude
```

```text
做一个 30 秒的竖屏科普：为什么低轨卫星的信号会"变调"。中文配音，中英双语字幕。
```

agent 会先交一份一屏长的大纲请你确认，再交分镜和一张关键帧预览图，最后交初版成片，并主动说出它自己最不满意的两三处。你点头之后，它才出最终版。

## 你可以这样提需求

不用写长篇 brief，说清楚**讲什么、给谁看、发在哪**就够了。

> **科普短视频**：45 秒竖屏，讲为什么 GPS 必须考虑相对论。发 B 站和小红书，中文旁白，结尾给出一个具体数字。

> **数学讲解**：用 3Blue1Brown 的风格，讲傅里叶级数怎么一点点拼出方波，20 秒，静音也能看懂。

> **产品发布片**：给这个仓库做一支 20 秒发布片，只用真实的终端和目录，配乐要有节奏感，关键动作配音效。

> **论文讲解**：把 `papers/main.tex` 里的核心机制做成 3 分钟讲解。元数据照抄原文，公式逐项讲，英文旁白加中文字幕。

> **MV**：给 `audio/song.mp3` 做手绘风 MV，歌词不上屏，画面讲故事，副歌每次都要升级。

> **拆解别人的片子**：这个视频挺好，拆一下它是怎么做的，然后用我们的工作台做一支类似风格的。

## 案例展示

下面几支片子，都是 agent 在本仓库里**只按 `CLAUDE.md` 和文档**做出来的。每个目录里都有需求书、分镜、自评返工记录和全部源码，可以直接拿来当同类视频的起点。

<table>
<tr>
<td rowspan="2" width="30%" valign="top"><a href="showcase/02-short-leo-doppler/"><img src="showcase/02-short-leo-doppler/media/preview.gif" width="100%" alt="02 · 竖屏科普"></a><br><b>02 · 竖屏科普</b><br><sub>HyperFrames · 24.8s · 1080×1920 · 静音可读 · 渲染 46s</sub><br><sub>“为什么低轨卫星的信号会变调？——多普勒频移”</sub></td>
<td width="35%" valign="top"><a href="showcase/00-promo-launch-film/"><img src="showcase/00-promo-launch-film/media/preview.gif" width="100%" alt="00 · 产品发布片"></a><br><b>00 · 产品发布片</b><br><sub>HyperFrames · 20s · 1920×1080 · 静音 · 渲染约 30s</sub><br><sub>“给这个仓库做一支 15–20 秒发布片，只用真实的终端和目录”</sub></td>
<td width="35%" valign="top"><a href="showcase/01-handdrawn-clawd-leaf/"><img src="showcase/01-handdrawn-clawd-leaf/media/preview.gif" width="100%" alt="01 · 手绘角色短片"></a><br><b>01 · 手绘角色短片</b><br><sub>p5.brush · 12s · 1080p24 · 渲染 57s · 3 轮自查</sub><br><sub>“Clawd 用手摇摄影机拍一片落叶，风总把叶子吹走”</sub></td>
</tr>
<tr>
<td width="35%" valign="top"><a href="showcase/03-math-fourier/"><img src="showcase/03-math-fourier/media/preview.gif" width="100%" alt="03 · 3b1b 式数学讲解"></a><br><b>03 · 3b1b 式数学讲解</b><br><sub>Manim CE 0.21 · 25s · 1080p30 · 渲染 24s · 独立评审后修订</sub><br><sub>“用正弦波一点点拼出方波（傅里叶级数与吉布斯现象）”</sub></td>
<td width="35%" valign="middle" align="center"><b>下一支是你的</b><br><br><code>bin/vh new &lt;type&gt; &lt;slug&gt;</code><br><br><sub>8 类视频任选：讲解 · 科普 · 发布片 · MV · 数据 · 论文 · 手绘 · 梗</sub><br><sub>做好了欢迎 PR 进 <code>showcase/</code></sub></td>
</tr>
</table>

GIF 是压缩后的预览，原片在各目录的 `media/final.mp4`。

<details>
<summary><b>社区里的同类作品（案例库对它们做了拆解）</b></summary>

| 作品 | 类型 | 做法 | 拆解 |
|---|---|---|---|
| [I'm Upping My P(doom)](https://x.com/other__reality/status/2102514581684052169) | 手绘 MV · 156s | p5.brush，9 个章节由 subagent 并行绘制 | [cases/mv-pdoom.md](cases/mv-pdoom.md) |
| [Functional Emotions](https://x.com/eudaemonea/status/2102610626321490404) | 绘画 MV · 372s | 自写 WebGL 笔触渲染器，7 个 subagent | [cases/mv-functional-emotions.md](cases/mv-functional-emotions.md) |
| [Claude Pop](https://x.com/donaldjewkes/status/2102801274173587569) | 混合 MV | Seedance 打底 + JS 转描，连续跑了 12 小时 | [cases/mv-claude-pop.md](cases/mv-claude-pop.md) |
| [星际穿越里的真物理·黑洞篇](https://x.com/AndyL5cc/status/2104519528873103773) | 横屏科普 · 143s | 一句话需求；一个黑洞着色器撑起全片 | [cases/explainer-interstellar-blackhole.md](cases/explainer-interstellar-blackhole.md) |
| [Applore 宣传片](https://x.com/decohack/status/2104502625055949242) | 产品片 · 15s | 一句 showreel 提示词 + 真实素材 | [cases/promo-applore.md](cases/promo-applore.md) |
| [389 支社区作品](https://github.com/yihui-dev/awesome-opus5-5-videos) | 各类 | 提示词统计、原型归类、精选 | [cases/opus55-gallery.md](cases/opus55-gallery.md) |

</details>

## 它是怎么工作的

<p align="center"><img src="docs/assets/architecture.zh.svg" width="680" alt="项目结构图"></p>

```mermaid
flowchart LR
    A["一句话需求"] --> B{"CLAUDE.md<br/>路由"}
    B --> C["video-types/*.md<br/>引擎·步骤·审美·禁止项"]
    C --> D["BRIEF + 大纲"]
    D --> R1{{"👤 人工审阅 ①"}}
    R1 --> E["STORYBOARD + 分镜预览图<br/>每镜 reads + 时间"]
    E --> R2{{"👤 人工审阅 ②"}}
    R2 --> F["声音先行<br/>配音 · 配乐 · 节拍表"]
    F --> G["逐场景写 f(t) 代码<br/>长片：样板章节 + subagent 并行"]
    G --> H["联系表 / 逐帧条 / 局部放大"]
    H --> I{"自查清单<br/>20 条"}
    I -- 不合格 --> G
    I -- 通过 --> J["初版 + 联系表"]
    J --> R3{{"👤 人工审阅 ③"}}
    R3 -- 修改 --> G
    R3 -- 通过 --> K["成片 + LESSONS.md<br/>经验回流"]
```

几条硬规则（完整版见 [CLAUDE.md](CLAUDE.md)）：

1. **每一帧都是 t 的纯函数。** 不用随机数、系统时钟和 CSS 动画，不跨帧保存状态。这样才能并行渲染、断点续渲，也才能随时抽任意一帧出来检查。
2. **有声音时，声音定时长。** 先有旁白或配乐，转成时间表，画面去对齐声音。
3. **先分镜，后代码。** 每个镜头写清观众要依次看懂的几件事（reads）和各自的起止时间。节奏是模型最容易做砸的地方。
4. **每个场景都要自查**，对着清单改到合格为止。
5. **事实照抄原文**，拿不准的记进 NOTES，不编进视频。

## 八类视频

| # | 类型 | 首选引擎 | 核心审美 | 文档 |
|---|---|---|---|---|
| 01 | 数学、科学原理讲解 | Manim CE | 一个概念一个颜色，先几何后代数，方程逐项点亮 | [01](video-types/01-math-science-explainer.md) |
| 02 | 知识科普短视频（竖屏或横屏） | HyperFrames | 第 1 秒抛出钩子，每 3–5 秒一个新看点，字幕不出安全框 | [02](video-types/02-knowledge-short.md) |
| 03 | 产品宣传、发布片 | HyperFrames | 只用真实界面，风格在 Apple 和 Linear 之间二选一，光标点击推动下一拍 | [03](video-types/03-product-promo.md) |
| 04 | 歌词视频、MV | p5.brush 或 HyperFrames | 卡点误差不超过 1 帧，副歌一次比一次升级，拒绝"歌词幻灯片" | [04](video-types/04-lyric-music-video.md) |
| 05 | 数据叙事 | HyperFrames + SVG | 一张图一个结论，转场分阶段，每个数字都能追溯 | [05](video-types/05-data-story.md) |
| 06 | 论文讲解、会议视频 | Manim + HyperFrames | 三道关卡，元数据照抄，图全部用矢量重画 | [06](video-types/06-paper-explainer.md) |
| 07 | 手绘、水彩、白板、剪纸 | ClaudeAnimationBase（p5.brush） | 手工感、画面始终在动、全片一气呵成；画面里不写字 | [07](video-types/07-hand-drawn.md) |
| 08 | 野兽派、网络梗、快剪 | HyperFrames | 先搭网格再故意打破，每个笑点 1 秒内看懂 | [08](video-types/08-brutalist-meme.md) |

还有几份专题文档：
- **写实人物、真实物理**：接入生成式视频模型，最终画面由代码叠加（[playbook/05](playbook/05-hybrid-genvideo.md)）；
- **特效与动画的来源**：[playbook/08](playbook/08-vfx-and-motion-sources.md)；
- **拆解别人的视频**：[playbook/07](playbook/07-reverse-engineer.md)。

## 声音：配音、字幕、配乐、音效、歌曲

| 需求 | 命令 | 说明 |
|---|---|---|
| **中英配音** | `bin/vh tts <项目> qwen Serena zh` | 默认使用本地开源的 **Qwen3-TTS**，离线免费，首次运行下载约 2GB。中文音色 5 个：Serena、Vivian、Uncle_Fu、Dylan（京腔）、Eric（川话）；英文音色 2 个：Ryan、Aiden。云端的阿里云百炼 Qwen3-TTS 和 ElevenLabs 已留好接口 |
| **双语字幕** | `bin/vh captions <项目>` | 旁白稿一行写成 `中文 \|\| English`，自动导出中文、英文、中英双行三种 SRT，外加给引擎用的 `captions.json`；`bin/vh mux` 可以把字幕封装成能开关的软字幕轨 |
| **配乐** | `bin/vh music score.json out.wav` | 代码作曲：段落对齐镜头，同样的谱永远生成同样的音乐，同时输出精确的节拍、段落和冲击点。也可以用你自己的曲子（`bin/vh beats` 分析节拍） |
| **音效** | `bin/vh sfx place events.json …` | 15 个代码合成的原创音效（点击、弹出、呼啸、上升音、冲击、叮咚……），按动作的落点自动摆放 |
| **混音** | `bin/vh mix out.wav voice=… music=… sfx=…` | 人声和音效出现时，音乐自动让位，整体统一到 -14 LUFS |
| **歌曲** | — | Suno 等网页服务生成后导入即可；ElevenLabs Music 和本地歌曲模型留好了接口 |

详见 [playbook/04-audio.md](playbook/04-audio.md)。

## 最后你会拿到什么

- 一支可以直接发布的 **MP4**，可选带中英软字幕轨；
- 一个**能重新渲染的工程**：改一行代码就能出新版本，也能 fork 成别的语言或别的风格；
- 全过程文件：需求书、分镜、审阅记录、自评返工记录、素材台账；
- 联系表和关键帧，方便复盘，也可以直接拿来做封面。

## 命令速查 `bin/vh`

| 命令 | 作用 |
|---|---|
| `doctor` / `setup` | 检查环境 / 安装依赖并拉取参考资料 |
| `types` / `new <type> <slug>` | 列出 8 类视频 / 按类型建项目（模板、提示词和引擎一次到位） |
| `tts` / `captions` | 配音（中英）/ 字幕（中、英、双语） |
| `music` / `sfx` / `beats` | 代码作曲 / 音效库与摆放 / 外部音乐的节拍分析 |
| `mix` / `mux` | 三轨混音 / 给成片合上音轨和字幕 |
| `sheet` / `check` / `gif` | 带时间戳的联系表 / 黑场、冻结、静音检测 / README 用的 GIF |
| `hf-init` / `install-skill` / `sync-agents` | 安全初始化 HyperFrames / 注册 skill / 同步 AGENTS.md |

## 需要什么环境

| 依赖 | 用途 | 必需？ |
|---|---|---|
| macOS 或 Linux、git | 基础 | ✅ |
| Node.js ≥ 22、Google Chrome | 浏览器引擎渲染（HyperFrames、p5） | ✅ |
| FFmpeg | 编码、混音、质检 | ✅ |
| Python 3 + [uv](https://github.com/astral-sh/uv) | 声音工具、Manim、联系表（依赖都临时安装，不污染全局环境） | 推荐 |
| Apple Silicon | 本地 Qwen3-TTS（mlx-audio） | 用本地配音时需要 |
| LaTeX | Manim 公式 | 做数学讲解时需要 |

不需要为渲染额外付费。只有接入云端配音、生成式视频这类外部服务时，才按各家规则收费，而且 API key 一律从环境变量读取。

## 安装与更新

**一键安装**：见上文"30 秒开始"。可选参数：

```bash
bash install.sh --dir ~/code/OpenVideoHarness   # 装到别的位置
bash install.sh --no-refs                        # 先不拉参考资料（之后可以运行 references/fetch.sh）
bash install.sh --no-skill                       # 不注册全局 skill
```

**手动安装**：

```bash
git clone https://github.com/ZLHad/OpenVideoHarness.git && cd OpenVideoHarness
bin/vh setup            # 安装内置引擎、拉取参考资料
bin/vh install-skill    # 可选：注册到 ~/.claude/skills 和 ~/.agents/skills
```

**只装 skill**（例如用 [skills CLI](https://github.com/vercel-labs/skills)）：

```bash
npx skills add https://github.com/ZLHad/OpenVideoHarness --skill open-video-harness
```

这个 skill 只是一个指针。第一次用时，它会征得你同意，再把完整的工作台装好。

**更新**：在仓库目录运行 `git pull`，然后 `references/fetch.sh`。

## 仓库结构

```
OpenVideoHarness/
├── CLAUDE.md · AGENTS.md     agent 入口：路由表、硬规则、目录（两份内容相同）
├── install.sh                一键安装
├── bin/vh · tools/           命令行和背后的脚本（声音、联系表）
├── skills/                   open-video-harness skill
├── video-types/              8 类视频的工作流
├── playbook/                 通用知识 00–08：范式、流程、自查、运动设计、声音、混合、学术、拉片、特效
├── templates/                BRIEF · STORYBOARD · STYLE · REVIEW · NOTES · LESSONS · TASTE_CHECKLIST
├── cases/                    11 个案例拆解 + 389 支社区作品精选
├── showcase/                 本仓库自己做的片子（源码 + 成片 + 过程记录）
├── engines/                  内置手绘引擎 + 其他引擎的安装说明
├── references/               fetch.sh（24 个只读参考仓库）· 开源清单 · 社区 skill 精选
└── projects/                 你的视频项目（不入库）
```

## 和其他项目的关系

| 项目 | 它是什么 | 本项目的不同 |
|---|---|---|
| [Code2Video](https://github.com/showlab/Code2Video) | 教学视频的 Planner–Coder–Critic 研究管线（Manim） | 把它的思路（代码即视频、锚点网格、分级修错、并行生成）推广到 8 类视频，并交给通用 coding agent 来执行 |
| [HyperFrames](https://github.com/heygen-com/hyperframes) / [Remotion](https://github.com/remotion-dev/skills) 的官方 skills | 单个引擎的使用指南 | 位于引擎之上的一层：选引擎、定流程、定审美、做自查，需要时再调用它们 |
| [OpenMontage](https://github.com/calesthio/OpenMontage) | 全套 agent 视频制作系统 | 更轻：主要是 markdown、模板和一个命令行，任何 coding agent 都读得懂、改得动 |
| [归藏 product-video skill](https://github.com/op7418/guizang-product-video-skill) | 专精软件产品更新片 | 覆盖 8 类视频，加上三道人工关卡和中英双语声音；配乐和音效的方法受它启发（代码是独立实现的） |

## 常见问题

**一定要用 Claude 吗？** 不必。`AGENTS.md` 和 `CLAUDE.md` 内容相同，Codex 等能读 markdown 的 agent 都能用。本仓库的案例是用 Claude Opus 5.5 做的。

**要花钱、要 GPU 吗？** 纯代码路线不用：渲染在本地的 Chrome 或 Manim 里跑，配音用本地 Qwen3-TTS，配乐和音效都是代码生成的。只有接入云端配音或生成式视频时才需要付费。

**中文支持怎么样？** 文档以中文为主（技术名词保留英文）。中文字幕排版、竖屏平台安全区、中文配音和双语字幕都做了专门处理。

**参考仓库的版权怎么处理？** `references/repos/` 不入库，由 `fetch.sh` 从原作者那里拉取，只供阅读。拉取后，别家的 `CLAUDE.md`、`.claude/` 会改名为 `_upstream_*`，避免被 agent 当成指令自动加载。每个仓库的许可证见 [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)，其中有些没有许可证或禁止商用，复用前请先确认。

## 路线图

- [ ] 项目介绍片（片头），正在按三道关卡制作
- [ ] 第 9 类：剪辑与口播（给已有素材剪辑、加字幕和 B-roll）
- [ ] 第 10 类：3D 场景（Three.js 和着色器）
- [ ] 字级强制对齐（Qwen3-ForcedAligner），支持逐字高亮字幕
- [ ] 类型文档的英文版
- [ ] 基于联系表的自动质量评测

## 参与贡献

欢迎提交 PR：
- 新的视频类型，放进 `video-types/`；
- 新的案例拆解，放进 `cases/`；
- 你在项目 `LESSONS.md` 里总结出的通用经验，补进 `playbook/`；
- 你用本仓库做出的片子，放进 `showcase/`，附上需求书、分镜、记录和源码。

## 致谢

感谢这些项目、研究和创作者：
- **框架与工具**：HyperFrames、Remotion、Manim、p5.brush、Qwen3-TTS、mlx-audio、FFmpeg；
- **研究**：Code2Video、Paper2Video、TheoremExplainAgent 等；
- **开源 skill 与案例**：ClaudeAnimationBase、PDoomVideo、functional-emotions-video、归藏 product-video skill、lemo-opuscar、OpenMontage、awesome-claude-video-skills、awesome-opus5-5-videos 等；
- **社区创作者**：在时间线上公开分享实验和提示词的各位。

完整名单、许可证和各自的用途，见 **[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)**。

本项目是独立项目，与 Anthropic、HeyGen、Remotion、Show Lab、阿里云均无隶属关系。

## 许可

原创内容采用 [MIT](LICENSE) 许可。内置的 ClaudeAnimationBase 同样是 MIT（© John Heibel）。参考仓库遵循各自的许可证。

## 引用

```bibtex
@misc{openvideoharness2026,
  title        = {OpenVideoHarness: A Code-to-Video Harness for Coding Agents},
  author       = {ZLHad and contributors},
  year         = {2026},
  howpublished = {\url{https://github.com/ZLHad/OpenVideoHarness}}
}
```
