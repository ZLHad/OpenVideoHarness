# 社区 skill 参考（2026-09-28）

这份清单从 183 个社区视频 skill 里，按 OpenVideoHarness 的 8 个类型挑出值得读的，并对已拉取到 `references/repos/` 的 16 个仓库逐个读了 README、LICENSE 和主 SKILL.md。它只回答"遇到某类视频时去哪个仓库找什么"，不替代 `open-source.md`（框架与引擎）和 `cases/`（案例拆解）。2026-09-29 又补了 Opus 5.5 发布周出现的 6 个仓库，它们不在那 183 个里面，见第 6 节。

- 下文"本地路径"都相对 `references/repos/`；写"未拉取"的只看过清单里的一句话描述，借用点标【推测】。
- ⭐ 与许可证字段来自 `skills.json`（2026-09-28 生成）；标"本地核对"的以仓库里的 LICENSE / README 为准。标"清单外"的条目，⭐ 是 2026-09-29 在 GitHub 页面上读到的数，许可证读的是仓库里的 LICENSE。

---

## 0. 来源与用法

**来源**：[zhuyansen/awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills)。收录"给 agent 用的、做视频/剪视频/做动效"的仓库，共 183 个，分 10 类：框架与通用 29、产品宣传 26、讲解科普 32、剪辑与后期 37、短视频与口播 19、数字人 5、故事与动画 13、动效与 Logo 11、剧本与学习 9、音乐视频 2。清单本身（选择、分组、文字）以 CC0 1.0 放入公有领域；各项目保留自己的许可证。

**安全评级**：每个仓库都由 Agent Skills Hub 读过 README 后评级。当前 181 个 SAFE、2 个 CAUTION（`wshuyi/remotion-video-skill`、`ops120/video-recap-skills-plus`）。评级依据是 README，不等于审过代码。

**怎么查**：
- 本地：`awesome-claude-video-skills/data/skills.json`，字段有 `repo_full_name / stars / description / kind / security_grade / language / license`。`kind` 取值为 `general / promo / explainer / editing / shorts / avatar / story / motion / craft / music`。
  ```bash
  jq -r '.skills[] | select(.kind=="editing") | [.stars,.repo_full_name,.license,.security_grade] | @tsv' \
    references/repos/awesome-claude-video-skills/data/skills.json
  ```
- 在线：<https://agentskillshub.top/best/claude-video-skills/>，可按类型筛选，每 8 小时刷新。

**用前三条原则**：
1. **看许可证，而且要打开 LICENSE 看。** `skills.json` 的 `license` 是 GitHub 自动识别的结果：`NOASSERTION` 或空值只说明没识别出来。本地核对时有 4 个仓库与字段不符（lemo-opuscar、video-talkcraft、remotion-guofeng-starter、MathLens，见第 5 节）。
2. **看安全评级。** CAUTION 的不装；SAFE 的也先读 SKILL.md 再装，尤其是会跑安装脚本或要 API key 的。
3. **只读参考，不直接复用。** OpenVideoHarness 自身是 MIT。要用社区代码就复制到 `projects/` 下再改，并按第 5 节保留声明；AGPL 和非商用许可的内容不能并进本仓库。

---

## 1. 按类型挑选

### 01 数学 / 科学讲解

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| shuyicc/MathLens（360⭐） | 贴一道数学题（图或文字），8 步走完：分析 → HTML/SVG 讲解页 → 分镜 → TTS → 音频校验 → Manim 脚手架 → 动画 → 渲染 | Manim + edge-tts（免费、需联网）；无 GPU 要求；README 写的是在 Cursor 里用 | 无 LICENSE 文件；README 声明 CC BY-NC 4.0 | `MathLens/SKILL.md`、`MathLens/templates/script_scaffold.py`、`MathLens/scripts/validate_audio.py` | `wait_for_narration(keyword)`：动画等到旁白说出含该关键词的句子才触发；`assert_geometry()` 先校验题目事实和画布范围；TTS 实测时长回写分镜 |
| adithya-s-k/manim_skill（1.1k⭐） | Manim CE 与 ManimGL 的 agent skills | Manim | MIT | 未拉取（`open-source.md` §2 已收） | 【推测】CE 和 GL 分开写，能减少 LLM 混用两套 API |
| lemo-opuscar 的 `whiteboard` 风格 | 白板讲解样片《Einstein in Your Pocket》：GPS、原子钟、相对论每天多出 38 微秒 | Canvas2D + 无头 Chrome，无付费 API | MIT | `lemo-opuscar/styles/whiteboard/STYLE.md` | 不想要 3b1b 黑底时的替代画风：一块板一镜到底，字迹逐笔写出，最后拉远看整块板 |

### 02 知识 / 科普短视频

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| hassancs91/claude-faceless-shorts-creator（272⭐） | 不露脸 Shorts 工厂，三条轨道：纯 TSX、视频模型、Vox 纸拼贴 | Remotion；配音、音效、音乐用 ElevenLabs（付费）；生成式轨道另需 fal.ai（付费） | MIT | `faceless-shorts-creator/_upstream_claude/skills/make-short/SKILL.md`、`faceless-shorts-creator/brand.md`、`faceless-shorts-creator/shorts/short-*/beats.json` | 节拍语法 HOOK（0–3.4s，第 0 帧就是完整画面，兼作缩略图）→ SETUP → QUIZ → REVEAL → TWIST → LOOP（末帧 = 首帧）；结尾不放"评论区告诉我"式 CTA；`<Sequence>` 内帧号是局部的，要换算 `local_f = global_s*fps − sequence_from` |
| coding-ax/docvideoer（5⭐） | 文档 URL、文章、Markdown → 带中文旁白的 Remotion 讲解视频 | Remotion；描述写"免费 TTS" | MIT | 未拉取 | 【推测】中文文章转视频的全链路参考 |
| pyang5166/gbro-collage-info | 从口播逐字稿挑段落，做成 1080×1920 半调纸拼贴信息动画 | 见第 4 节 | MIT | `gbro-collage-info/SKILL.md` | 信息只放在画面上 2/3（y ≤ 1280），底部 640px 留给字幕 |
| kuhnhomeuk-cell/procedural-film（460⭐，清单外） | 给一个题材，出一支 30 秒上下的竖屏短片；样片是帝王蝶的一生（17 镜、32 秒、120 BPM、1080×1920、24 fps）。另有照片涂鸦和像素复古两种模式，还能做一个可玩的平台跳跃游戏 | 原生 JS Canvas 绘制、Web Audio 合成声音，零媒体素材；Playwright + ffmpeg 出片；一镜一个 agent，README 提醒一支片子很耗额度；游戏会部署到用户自己的 Vercel | MIT | `procedural-film/skills/procedural-film/SKILL.md`、`.../foundation/tools/check.cjs`、`.../reference/shot-types.md`、`procedural-film/examples/butterfly-life/docs/` | 六项关卡 `check.cjs`（媒体扫描、确定性、源码扫描、时间线、绘制、单帧耗时），从桩场景那一步起就必须全绿；确定性检查把每镜首、中、尾帧按正序、倒序、混入干扰帧、冷启动、顺序绘制几种方式分别画出来比哈希；先用桩场景把时间线、渲染和音频整条跑通再画真镜头；一个 agent 只拥有一个镜头文件，评审 subagent 分波次出 P1/P2 修改单，并在像素上量几何；竖屏底部 380px 留给平台 UI，必须读的文字不能落进去。也适合 07 |

### 03 产品宣传 / 发布片

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| Vincentwei1021/video-shotcraft（10k⭐，2026-10-01 为 10,029） | 电影感产品片：157 张镜头配方卡（214 个样式；清单写 152）、Ink Press 成片模板、浏览器工作台、剪映工程导出 | Remotion（README 提醒：公司使用可能要买 Remotion 许可）；真实页面用无头浏览器截图；不用生成模型 | Apache-2.0 | `video-shotcraft/SKILL.md`、`video-shotcraft/references/shots/`、`video-shotcraft/references/pipeline.md`、`video-shotcraft/references/aesthetic-rules.md` | 视觉语言从产品自身的设计系统提取 tokens，模板只继承镜头结构和节奏；复刻页面必须用真实截图；每个镜头只讲一个动效，信息落定后要"呼吸"；开工前让用户在"模板 / 自主创作 / 共同创作"三种模式里选一种。本仓库的 `recipes/`（镜头配方）和 `recipes/sequences/`（全片骨架）由它改写，拆解见 `cases/promo-video-shotcraft.md` |
| op7418/guizang-product-video-skill（473⭐） | 接入真实产品组件做软件更新片，配原创配乐和动作音效 | React + esbuild + Playwright 出帧、FFmpeg 编码，GSAP / Three.js；也支持 HyperFrames；配乐可用代码合成 | AGPL-3.0；`assets/fallback/` 为 BSL 1.1 | `guizang-product-video/SKILL.md`、`guizang-product-video/references/direction.md`、`guizang-product-video/references/visual-vocabulary.md` | 写 `DIRECTION.md`：沿不同的轴提三个方向再选一个；列 3–5 条"因为产品有 X，所以用 Y"的专属手法；同一工作区不复用上一支片子的开场和背景；1080p 下界面正文 ≥ 22px |
| norahe0304-art/30x-video（63⭐） | 输入一个 URL，输出发布片；自带 16 条审美准则，不用模板 | Remotion + React | MIT | 未拉取 | 【推测】审美准则可对照 `templates/TASTE_CHECKLIST.md` |
| kangarooking/promo-creator-skills（101⭐） | 从产品判断、分镜、素材、HyperFrames 剪辑到 BGM 设计的整条工作流 | HyperFrames | MIT | 未拉取 | 【推测】中文产品片全流程参考 |
| Rieranthony/product-film-skill（358⭐，清单外） | 在产品自己的代码库里做落地页循环片、发布片、演示片，复用真实组件和设计 tokens | Remotion（README 提醒：较大的公司要买 Remotion 许可）+ Bun + uv；配乐要自带有授权的歌；不用生成模型 | MIT | `product-film-skill/plugins/product-film/skills/product-film/SKILL.md`、`.../templates/BRAND.md`、`.../reference/render.md`、`.../scripts/verify.py` | 先从设计系统（规则文件、tokens、组件、官网、能说和不能说的宣称）整理出 `videos/BRAND.md`，它优先于 skill 自带的默认值；节拍表写完先交 3 张风格帧再开工；母版按 240 fps 渲，用 ffmpeg `tmix` 每 4 个子帧平均成 60 fps，得到运动模糊；交付静音循环版、带音乐版、WebM 和海报（取标题帧，不取空白的第 0 帧）；`verify.py` 解码每个成品，核对时长、第 0 帧背景色（误差 ±2，防止 Remotion 的有限色域把 #0a0a0a 抬成 #171717）和首尾接缝 |

lemo-opuscar 的 `dark-keynote`、`living-screencast`、`glass-product` 三种风格也适合本类，2026-09-29 新加的 `hologram-hud`（产品参数扫描）和 `midcentury-toon`（分步上手指南）同样适用，见第 2 节。

### 04 歌词视频 / MV

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| ledbetterljoshua/functional-emotions-video | 已在 `cases/mv-functional-emotions.md` 拆解 | 自写 WebGL 笔触渲染器 | MIT（代码；歌曲、歌词和 `assets/` 音频不在内） | `functional-emotions-video/analysis/` | 歌词对齐脚本（已写进 `video-types/04-lyric-music-video.md`） |
| lemo-opuscar 的时间线与卡点检查 | 一个 `timeline.js`（段落、BPM、拍号、卡点）导出 JSON，配乐、混音、字幕和检查脚本共用 | Node + Python，采样库 CC0 / CC BY | MIT | `lemo-opuscar/TECHNIQUE.md` §3、`lemo-opuscar/styles/microgame/demo/tools/cuecheck.py`、`lemo-opuscar/styles/game-show/STYLE.md` | 用脚本逐个比对画面卡点和音乐 cue，目标偏差 0 ms；每个风格用自己的编制，不用通用的"钢琴 + 弦乐" |
| bestagentkits/motion-video-skill（97⭐） | HyperFrames 卡点 1080p 动态图形视频，带 AI 配音、卡拉 OK 字幕、音效和生成音乐 | HyperFrames；供应商描述未写 | MIT | 未拉取 | 【推测】对应 04 的 B 路线（动态排版 / 歌词视频） |
| ZiadAbdelkarim/beat-synced-edit（10⭐） | 给一首歌和一堆素材，分析节拍、能量和场景后自动卡点剪 | 纯 Python + ffmpeg CLI | MIT | 未拉取 | 有实拍素材的 MV 可用 |

PDoomVideo 已在 `cases/mv-pdoom.md`，没有 LICENSE，只读。

### 05 数据叙事 / 动画图表

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| iart-ai/data-animation-skills（6⭐） | 三个 skill：`chart-animation`（bar chart race、折线、计数器、一个模板批量套多份 CSV）、`animated-infographic`、`presentation-video` | Remotion + d3-scale；README 未提付费 API | MIT | `data-animation-skills/skills/chart-animation/SKILL.md`、`.../references/bar-chart-race.md`、`.../references/data-pipeline.md` | 每个值都由当前帧算出，关掉 Chart.js / D3 的内置动画，D3 只用比例尺；计数器先取整再格式化，用 `tabular-nums` 固定数字宽度；缓动作用在"值"上；排名也插值，超车才是滑过去而不是跳 |
| lemo-opuscar 的 `dataviz`、`iso-infographic` | 《A Hundred Summers》：一百年夏季气温，红蓝铅笔逐点画出，图表本身就是镜头和节奏；等距信息图一镜到底，最后拉远成一张可打印的信息图 | Canvas2D | MIT | `lemo-opuscar/styles/dataviz/STYLE.md`、`lemo-opuscar/styles/iso-infographic/STYLE.md` | 手写批注钉在具体数字上 |
| pyang5166/gbro-collage-info | 数字冲击、清单收敛类段落 | HyperFrames | MIT | `gbro-collage-info/references/motion-grammar.md` | 屏幕文字只用稿子里有的数字，稿子没给的用空白卡占位，不替内容编数据 |

### 06 论文讲解 / 学术视频

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| ssrajadh/paperview（9⭐） | 把论文、代码库等做成讲解视频，本地渲染 + TTS，Claude Code 插件 | 描述写"本地渲染"，引擎未写 | Apache-2.0 | 未拉取 | 【推测】清单里和本类最贴近的一个，值得拉下来细读 |
| data-animation-skills 的 `presentation-video` | 把幻灯片重建成带旁白、自动翻页的视频，每页的元素按旁白依次出现 | Remotion（`@remotion/transitions`） | MIT | `data-animation-skills/skills/presentation-video/SKILL.md` | 对应 06 的"报告录像型"：每页标题写成一个论断而不是标签；每页时长由该页旁白实测时长决定 |
| runesleo/claude-video-kit（120⭐） | brief/script → review receipt → 带旁白的 9:16 讲解视频 | Remotion | MIT | 未拉取 | 【推测】"review receipt"可对照 06 的三道关 |

### 07 手绘 / 水彩 / 剪纸

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| hi-nikola/hand-drawn-explainer-video-nikola（349⭐） | 中文手绘知识讲解，两条路线：逐笔故事动画、程序动画 | 逐笔路线用仓库内置的 MIT 后端，传统图像算法，不需要 GPU；程序动画用 HyperFrames + GSAP；配音默认火山引擎 seed-tts-2.0（需授权账号）；生图可选 | Apache-2.0；`examples/` 媒体 CC BY 4.0 | `hand-drawn-explainer/SKILL.md`、`.../references/stroke-story-workflow.md`、`.../references/semantic-island-storytelling.md` | 先分清"画面被逐笔画出来"和"手绘风元素在动"，不能用整图淡入或卡片飞入冒充落墨；左右双语义岛：先画左边讲完，再画右边，保留前文；没有合格配音就报告缺口，不静默换成低质 TTS |
| gnipbao/story-to-handdrawn-video（2.1k⭐） | 中文故事或有序图片 → 3:4 竖屏手绘日记漫画动画（静音画面轨） | Remotion；需要 agent 能调用的生图工具 | MIT | `story-to-handdrawn-video/skill-package/story-to-handdrawn-video/SKILL.md`、`.../references/handdrawn-style-library.json`、`.../references/style-library.html` | "文字 → 黑白画稿 → 彩色插画"三段揭示；327 项画风与配色资产，全部用同一个标准场景出示意图，便于横向比较 |
| AllenAI2014/remotion-guofeng-starter（25⭐） | 国风纸片拼贴：给一首诗或一个成语，白描纸片叠在墨线山水上，盖朱红印章 | Remotion；纸片要外部生图（README 说 Claude Code 自己不出图）再手动抠透明底；配音用 MiniMax（付费）；依赖宋体、楷体等系统字体 | 代码 MIT；`public/` 演示素材不授予商用 | `remotion-guofeng-starter/SKILL.md`、`.../style/design.md`、`.../style/分镜与图层规范.md`、`.../src/components/PaperCollageLayer.tsx` | 风格资产（色卡 token、纸片规范、图层运动预设）和具体故事分开放；纸片入场回弹 + 呼吸浮动 + 纸投影 |
| EverMind-AI/Raven（4.3k⭐） | 从一个仓库的 Git 历史导演一部两分钟手绘动画片：故事、角色、分镜、HTML 审片台、4K/60fps | 描述未写 | Apache-2.0 | 未拉取 | 【推测】HTML 审片台可对照我们的联系表自查 |
| buildwithhanif/claude-animation-skill（21⭐，清单外） | 纯代码的手绘 2D 动画：纸纹、排线、毛笔水彩、带解剖结构的蚂蚁骨架、蚁巢剖面；附 4 支 30 秒上下的样片 | Node + `@napi-rs/canvas` + ffmpeg，不用浏览器、GPU 和 API key；音效和配乐都由代码合成 | MIT | `claude-animation-skill/plugins/claude-animation/skills/claude-animation/SKILL.md`、`.../references/detail.md`、`.../lib/film.mjs`、`.../references/prior-art.md` | 细节圣经：每个表面都画三层（底色 → 纹理 → 边缘），线宽和细节随景深递减，逐种材质写明纹理怎么画；笔触种子取自稳定的名字而不是帧号，线条抖不抖要明确决定；`verify` 把 5 个帧按正序、倒序、再正序渲三遍比 MD5；`render` 先写进暂存目录，编码成功才替换旧文件；音效从画面时间线生成，比接触帧早约 0.03 秒 |

lemo-opuscar 的蜡笔、水彩、水墨、厚涂、红色剪纸、皮影、纸雕灯影等风格见第 2 节。它的笔触引擎在 `styles/watercolor/`、`ink-wash/`、`impasto/`。

### 08 野兽派 / 网络梗 / 快剪

社区里专门做这一类的很少，以下以借结构、借风格为主。

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| sharon-laicc/viral-video-decomposer（6⭐） | 拆解爆款短视频：镜头级拉片、爆款机制、AI 生产蓝图、变量槽、JSON brief、HTML 报告 | 纯 skill，输入链接、逐字稿、截图或录屏 | MIT | `viral-video-decomposer/skill/SKILL.md`、`.../skill/references/output-contract.md` | 只复用结构，换成自己的选题，不复刻原文案和具体镜头，与 08"梗格式自己重做"一致；可配合 `playbook/07-reverse-engineer.md` |
| lemo-opuscar 的 `halftone-dossier`、`microgame`、`swiss-motion`、`ascii-crt` | 半调案卷式"模拟调查"、越来越快的微游戏、瑞士网格排版、字符终端 | Canvas2D / SVG | MIT | `lemo-opuscar/styles/<slug>/STYLE.md` | 见第 2 节 |
| smwbev/framewright（21⭐） | 单个 HTML 文件，每帧都是 (frame, seed, width) 的纯函数 | HTML | MIT | 未拉取 | 与我们的硬规则 1 同构 |

### 剪辑与口播（有现成素材时）

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| Vincentwei1021/video-talkcraft（1.3k⭐） | 口播稿 + 成品配音 → 字级时间戳 → SHOTBOOK 分镜 → Remotion 成片；108 张动效卡 | Remotion；时间戳在本机 CPU 上用 FireRed ASR 做；可选 Fish Audio 合成配音；共享依赖约 760 MB | PolyForm Noncommercial 1.0.0，商用需作者事先授权 | `video-talkcraft/SKILL.md`、`.../references/cinematography.md`、`.../references/layout.md`、`.../scripts/voice_trim.py` | 真人录音先预剪（口水词、结巴重说、过长停顿）再做时间戳，顺序不能反；以稿子为真值，ASR 听错的字不剪；新元素只在语义拍边界进场，禁止"一句一个新元素"；稿子里的数字写汉字，方便逐字对齐 |
| Agentchengfeng/chengfeng-videocut-skills（3.0k⭐） | 用 Claude Code Skills 做的视频剪辑 Agent | 描述未写 | Apache-2.0 | 未拉取 | 【推测】中文剪辑场景下星数最高 |
| FireRedTeam/FireRed-OpenStoryline（3.4k⭐） | 用自然语言驱动的剪辑 agent，LLM 规划 + 工具编排，人在环中，可复用 Style Skills | 描述未写 | Apache-2.0 | 未拉取 | 【推测】"风格 skill"可对照 lemo 的 STYLE.md |
| louisedesadeleer/cut-video（104⭐） | 收紧长录音：去静音、口头禅和空白，保留笑声和喜剧停顿 | Apple Silicon 上较快 | MIT | 未拉取 | 口播粗剪 |
| zenstory-ai/video-recap-skills（539⭐） | 视频 → 中文解说成片：场景检测、ASR、VLM、脚本、TTS、ffmpeg 合成，可导出剪映草稿 | 本地 ffmpeg + 一个 MiMo key，不需要 GPU | MIT | 未拉取 | 剪映草稿导出（shotcraft 的 `jianying-export/` 也有） |

同类的 `ops120/video-recap-skills-plus` 评级为 CAUTION，不用。

### 数字人

| 仓库 | 做什么 | 引擎 / 付费 API / GPU | 许可证 | 本地路径 | 值得借用 |
|---|---|---|---|---|---|
| cclank/lanshu-create-ai-presenter-video（1.9k⭐） | 用脚本和一张已授权的主持人照片，生成经过校验的 AI 主持人视频；不绑定供应商 | 【推测】需要外部数字人服务 | MIT | 未拉取 | 输入必须是"已授权"的人像 |
| heygen-com/skills（456⭐） | HeyGen 官方：创建数字人，走 v3 Video Agent 管线出片 | HeyGen API（付费） | MIT | 未拉取 | — |
| Upload-Post/avatar-mix（130⭐） | HeyGen 数字人 + HyperFrames 动态背景 + 音乐音效 + Hormozi 字幕，出 16:9 / 9:16，并发布到各社交平台 | HeyGen API + HyperFrames | MIT | 未拉取 | 数字人叠 HyperFrames 背景的做法；自动发布那一步不要默认打开 |

本机没有 NVIDIA GPU，数字人只能走云服务。video-talkcraft 把数字人素材当输入，OpenMontage 有 `avatar-spokesperson` 管线，都可参考。

---

## 2. 风格库：lemo-opuscar 的 43 种影片风格

lemomo-ai/lemo-opuscar（605⭐，2026-09-30）是作者 Lemomo（X 上是 @lemomo_ai，署名 LemoLab）用 Claude Opus 5.5 做的 43 支纯代码样片：2026-09-26 首发 39 种，09-29 的 `00343a2` 加了 `engraving`、`hologram-hud`、`midcentury-toon`、`silkscreen-poster` 四种。每种风格一份风格 prompt（`STYLE.md`），另有导演指南 `DIRECTOR.md` 和技术指南 `TECHNIQUE.md`。README 说明风格按 Opus 5.5 调过，换别的模型不保证效果；一支片子 agent 大约要做 30–60 分钟。画面用 Canvas / WebGL 逐帧渲染，配乐用免费采样库，配音用 TTS（英文默认离线的 Kokoro，中文可用联网的 edge-tts），不用视频生成，也不用素材库画面。本节按 2026-09-30 拉到的 HEAD `721f0b7` 核对。

**许可（LICENSE 原文）**：现在整个仓库都是 MIT（Copyright 2026 LemoLab），另有一句说明样片里的第三方素材（采样库、字体、音乐、人声）保留各自许可，见每个样片的 `CREDITS`。CC BY 4.0 那一段是 `02dce5b`（2026-09-29，"Slim the library"）删掉的；在那之前（例如本仓库最初读的 `81e8903`），`DIRECTOR.md`、`TECHNIQUE.md`、`docs/`、`styles/*/STYLE.md` 和成片是 CC BY 4.0，只有代码是 MIT。CC 许可不能撤回，本仓库 `styles/` 里按旧快照改写、注明了 CC BY 4.0 的出处照旧成立（一般理解，非法律意见）。GitHub 和 `skills.json` 都把它识别成 `NOASSERTION`，不准确。

**路径**：`02dce5b` 起每种风格拆成两份：`lemo-opuscar/styles/<slug>/STYLE.md` 只写风格本身，统一 11 节（本质与"不是什么"、材质与渲染、色彩逻辑、字体与字幕、运动质感、镜头语法、声音、原生招式、这种媒介的坑、引擎、变化空间）；同目录的 `DEMO.md` 写作者那支样片的故事、镜头、配乐、片尾和制作笔记，`style.json` 是元数据，`styles/README.md` 是由它生成的中英风格索引。新加的四种是"场景风格"，各自承担一件实际的活（参数讲解、分步指南、旅游海报等）。原来的中文版指南 `docs/zh-CN/` 在同一次提交里删掉了，`DIRECTOR.md` 和 `TECHNIQUE.md` 现在只有英文。下表"适合"一列是本文按 OpenVideoHarness 类型给的归类建议，不是原仓库的说法。

| 大类 | slug · 中文名 | 一句话特征 | 适合 |
|---|---|---|---|
| 手绘与绘画 | `crayon-book` 蜡笔儿童绘本 | 粗纹纸上现场画的蜡笔睡前绘本，一层水彩洗出蜡笔藏着的东西 | 07 |
| | `watercolor` 水彩笔刷 | 自然笔记水彩自己画出来，沿一条数据梯度横走，最后拉出手绘地图 | 07 · 05 |
| | `ink-wash` 中国水墨 | 宣纸写意，留白即空间，一笔是山、是浪、是剑 | 07 |
| | `impasto` 油画厚涂 | 刮刀厚涂的大块平面色，侧光照出颜料脊；先明暗后质感 | 07 · 04 |
| | `one-line` 一笔画 | 一根不离纸的墨线画完整个故事，拉远后拼成一幅图 | 07 |
| | `whiteboard` 白板讲解 | 一块白板上逐笔写出的科学讲解，板擦能倒带，结尾拉远看全课 | 01 · 07 |
| | `urban-sketch` 钢笔淡彩 | 抖动不闭合的棕褐细线，上面是略出线的透明水彩 | 07 |
| 东方传统 | `shadow-puppet` 皮影戏 | 镂空染色的皮偶贴在布幕上，油灯背光 | 07 |
| | `ukiyoe` 浮世绘 | 平涂色块、刻线、普鲁士蓝、晕染天空，镜头像展开手卷 | 07 |
| | `papercut-red` 红色窗花剪纸 | 关节式红剪纸，剪处即画，镂空处透光 | 07 |
| | `paper-lantern` 纸雕灯影 | 6–9 层卡纸叠成的背光灯箱，层层透光投影，从真实灯箱推进去 | 07 |
| 印刷与版画 | `risograph` Risograph 丝网印刷 | 2–3 种半透明专色叠印，半调网点，版永远套不准 | 08 · 02 |
| | `halftone-dossier` 复古半调案卷 | 档案纸、四色网点、错位阴影大标题、印章砸下，把片子做成逐件出示证物的调查 | 08 |
| | `woodcut` 木刻版画 | 黑木版上只有刀刻处有光，至多一种颜色，只给"燃烧的东西" | 07 |
| | `engraving` 铜版画 | 博物志图版自己刻出来：雕刀推开铜版，主体一线一线成形，最后手工水彩上色 | 01 · 07 |
| | `silkscreen-poster` 丝印旅行海报 | 海报一色一刮印出来，再沿画面一镜到底，从正午走到黄昏 | 02 · 03 |
| 图形与排版 | `swiss-motion` 瑞士动态排版 | 模块网格、一种字体、一个信号红，动作像印刷机一样精确 | 08 · 03 |
| | `spy-titles` 60s 间谍片头 | 四色剪纸片头，剪影在演职员表搭成的布景里追逐，铜管每一击是一刀 | 08 · 04 |
| | `art-deco` 装饰艺术 | 黑漆、金色刻线、喷枪几何；构图有中轴，灯泡逐个亮起 | 03 |
| | `blueprint` 蓝图 / 工程制图 | 晒图纸上的白色工程线按制图顺序画出，标注会动 | 01 · 06 |
| | `stained-glass` 彩色玻璃窗 | 中世纪彩窗，只有阳光照到的格子才动 | 07 |
| | `pictogram-motion` 象形运动图形 | 方格核心图形 + 几何象形人 + 双语粗体字，每一刀落在鼓点上 | 04 · 08 |
| | `ascii-crt` ASCII / CRT 终端 | 屏上一切都是等宽网格里的真实字符，单色 CRT 荧光 | 08 · 03 |
| 信息与发布 | `dataviz` 数据叙事 | 红蓝铅笔逐点画出真实数据，手写批注钉在数字上，图表就是镜头和情节 | 05 |
| | `iso-infographic` 等距信息图 | 一个等距立体模型一镜讲完整个系统，剖开看内部，最后拉远成一张信息图 | 05 · 06 |
| | `dark-keynote` 暗色科技发布 | 界面即主角：近黑底、发丝网格、一个强调色，扫光揭示，承诺是一个巨大数字 | 03 |
| | `living-screencast` 活体实机录屏 | 像真录屏，低分辨率吉祥物住在高分辨率界面里演出软件在做的事 | 03 |
| | `hologram-hud` 科幻全息界面 | 物体被扫描成发光线框，目标框逐个锁定部件，参数从乱码滚到真值 | 03 |
| 卡通与动画 | `rubber-hose` 1930s 橡皮管卡通 | 黑白手墨卡通，万物有生命，随热爵士摇摆 | 07 · 04 |
| | `cel-anime-80s` 80 年代赛璐璐 | 双色赛璐璐 + 喷笔背景 + 背光霓虹，按 1987 年录像带在 CRT 上播放 | 07 · 04 |
| | `scifi-toon` 科幻情景喜剧卡通 | 抖动粗描边、平涂色、绿色传送门，每个平行宇宙一套配色 | 07 · 08 |
| | `midcentury-toon` 50s 扁平卡通 | 用 50 年代教育片的口吻，扁平卡通一步一步教人上手一样东西 | 03 · 07 |
| 游戏 | `pixel-rpg` 16-bit 像素 RPG | 320×180、有限调色板、打字文本框、存档点、带回声的芯片音乐 | 08 · 07 |
| | `hd-2d` HD-2D | 手工像素精灵像纸片一样立在有光有雾的 3D 立体模型里，高俯角加移轴 | 07 |
| | `microgame` 微游戏快闪 | 一个指令词、几秒、一个动作，每关换一种画风，越来越快 | 08 · 02 |
| | `game-show` 综艺节奏扁平 | 豆形吉祥物、8px 描边、糖果条纹，每一击卡在 150 BPM 网格上 | 04 · 08 |
| 电影与时代 | `silent-film` 1920s 默片 | 雕版插画风默片喜剧，4:3 闪烁胶片，字幕卡代替对白，影院钢琴伴奏 | 07 |
| | `backrooms` 后室 / 新怪谈 | 从无尽荧光灯空间里找回的录像带，用规则代替怪物 | 08 |
| 材质与 3D | `brick-toy` 积木玩具 | 像在真书桌上微距拍的积木定格动画 | 07 · 03 |
| | `paper-popup` 纸片立体书 | 立体书在木桌上打开成舞台，剪纸角色最后跳出书外 | 07 |
| | `tilt-shift` 移轴微缩 | 高处移轴 + 延时拍的真实小镇，看起来像桌面模型 | 05 · 07 |
| | `lowpoly-island` 低多边形等距 | 正交等距的多面体小世界，每出现一样东西就弹一下、响一个音符 | 04 · 07 |
| | `glass-product` 玻璃质感产品 | 透明 / 磨砂玻璃产品，条形灯扫光、焦散，慢速爆炸图在重拍处合拢 | 03 |

### DIRECTOR.md 讲了什么，能借什么

它把评判顺序定为**音效、节奏、镜头、导演能力**（表演、调度、情绪弧），画面好看只是起点。12 节依次是：接需求、先找对标、故事、写导演方案、定画面、声音、节奏、镜头、表演、常见问题、交付前自检、版权红线。

可以直接借进 OpenVideoHarness 的规则：

1. **对标写两栏**：学什么（构图、节奏、镜头语法、配色逻辑、配乐结构）/ 不学什么（角色、造型、旋律、具体画面、标志、字体）。可加进 `templates/STYLE.md`。
2. **故事三件套**：一个主体、一个目标、一次转折；开场 3 秒内抓人；结尾有回响；一个"只有这种媒介做得到"的原生招式，放在情绪最高点。
3. **TREATMENT 七项**：一句话故事与情绪弧、对标、镜头表（景别 / 角度 / 运动 / 时长 / 为什么这样拍）、按秒的节拍表、cue map、声音设计表、字幕与片名设计。可对照补 `templates/STORYBOARD.md`。
4. **声音**：画面上每个动作都有按材质区分的声音；分环境底、拟音、音乐三层；至少两处真正的静音，静音后的第一个声音要是全片最重要的之一；至少两次用 J-cut / L-cut 做声音转场。
5. **读秒公式**：每句字幕至少停 1.8 秒，且不短于"语音 + 0.6 秒"；文字动画结束后，中文停（字数 ÷ 4.5 + 1.5）秒，英文停（字母数 ÷ 15 + 1.5）秒；标题页至少 4 秒。后一条由 `core/render/readcheck.mjs` 自动查：页面实现 `window.TEXTS(t)`，逐个时间步报出画面上每段文字和它的屏幕框，工具算每段连续完整在画的时长，被裁出画框的也报错。已并入 `playbook/03-motion-design.md` §2 和 `templates/TASTE_CHECKLIST.md` #5（下限改为 2.5 秒），我们按时间表检查的版本是 `tools/readcheck.py`。
6. **镜头**：全片至少 4 种镜头运动，要有一个签名镜头；转场在媒介里设计，全片一套语法；关键时刻主体至少占画面高度的 1/3。
7. **表演**：姿势用关键帧缓动混合，不在 `if` 分支里切姿势；所有跟随主体的效果都走同一个"世界坐标 → 画面坐标"函数。
8. **自检**：配音每句都能被 ASR 正确转写回来（`core/tts/asr_check.py`：英文逐词比对，中日韩按字符相似度，默认 ≥ 0.92）；无黑帧、无 NaN 帧；声音设计表里的每一项都真的进了混音。
9. **别再做一遍样片**：先写自己的 treatment，再打开 `DEMO.md` 对照结构、开场、签名镜头、镜头路径、配乐走向、结尾六项，至少四项要不同；交付前把自己的联系表和样片海报并排看一次。我们 `styles/` 的样片内容都一样，本来没有故事可照搬；这条主要管参考别人样片（包括 lemo 的）的时候。

差异：lemo 默认开工前只问一次，分镜故事板**默认不看**，直接做完；OpenVideoHarness 默认在 BRIEF 和 STORYBOARD 两处停。借规则时保留我们的关卡。

### TECHNIQUE.md 讲了什么，能借什么

它讲整条管线：一条时间线同时驱动画面（`render(t)` → 无头 Chrome 逐帧截图）、配音（逐句 TTS → ASR 校对 → 逐词时间戳）、配乐（采样 + 合成）、程序化音效和字幕，最后混音，用 ffmpeg 两遍 loudnorm 到 −14 LUFS。

可以直接借的：

1. **页面契约**：`window.DUR`、`window.render(t)`、`window.READY`，外加可选的 `window.EV = [{t, type}]` 事件表（让音效精确落在对应帧上）和 `window.TEXTS(t)`（readcheck 用）。契约全表在 `core/README.md`。与硬规则 1 一致，`EV` 和 `TEXTS` 是我们还没有的部分。
2. **一条时间线驱动一切**：`timeline.js` 写段落、BPM、卡点（`SECS`、`HIT`），导出 JSON 给配乐、字幕和检查脚本共用；`cuecheck.py` 比对卡点，目标偏差 0 ms。
3. **提速**：截图用 JPEG（`81e8903` 版写的是比 PNG 快约 8 倍，现版本删了这个数）；每个 worker 各开一个浏览器；胶片颗粒在 ffmpeg 里加，不画在页面里。
4. **一拍二只作用于画面**：定格、像素、赛璐璐可用 12 fps 步进，但机位和光每帧都要平滑，否则会被看成卡顿。
5. **配音**：英文用本地 Kokoro，中文用 edge-tts（联网，商用前看微软条款）；faster-whisper 逐句转写比对，不通过就重生成；TTS 文本里数字拼成词，字幕里写阿拉伯数字；人声先压缩，再比音乐高约 10 dB。可对照 `playbook/04-audio.md`。
6. **配乐**：CC0 采样库（VSCO 2 CE、VCSL、FreePats、Karoryfer）+ Karplus–Strong 拨弦；混完按频段检查，20–120 Hz 相对其余频段保持在 −3 dB 左右。
7. **代码画的角色**：肩关节先外展、再前屈，反过来举起的双臂会交叉成 X；手臂压在躯干上的那段不描轮廓线。

---

## 3. OpenMontage

**是什么**：calesthio/OpenMontage（61.6k⭐，AGPL-3.0），自称首个开源的 agentic 视频制作系统。架构是"指令驱动"：agent 读管线清单（YAML）→ 读阶段导演 skill（Markdown）→ 调工具（Python `BaseTool`）→ 自审 → 存检查点 → 请人审批；没有 Python 编排器。每条管线都走 `research → proposal → script → scene_plan → assets → edit → compose`。英文 README 写 100+ 工具、700+ skill 与知识文件（中文 README 仍是旧数字 52 / 400+）。依赖 Python 3.10+、FFmpeg、Node 18+；API key 全部可选（fal、ElevenLabs、OpenAI、Suno、HeyGen、Runway、火山方舟等）；零 key 时有 Piper TTS + 开放档案素材 + Remotion / HyperFrames；有 GPU 可装本地视频生成。

**12 条管线**（`OpenMontage/pipeline_defs/`，另有测试用的 `framework-smoke`）：

| 管线 | 产出 | 对应 OpenVideoHarness |
|---|---|---|
| `animated-explainer` | 带调研、旁白、画面、音乐的讲解 | 01 / 02 |
| `animation` | 动态图形、动态排版 | 02 / 08 |
| `avatar-spokesperson` | 数字人主持视频 | 数字人 |
| `character-animation`（v0.1 beta） | 本地可复用卡通角色：角色规格、绑定、姿势库、动作时间线，SVG / Canvas / Remotion / HyperFrames 渲染 | 07 |
| `cinematic` | 预告、前导片、情绪剪辑 | 03 / `playbook/05-hybrid-genvideo.md` |
| `clip-factory` | 从一条长素材批量切出排好序的短片 | 剪辑与口播 |
| `documentary-montage` | 从 CLIP 索引的免费素材和开放档案（Pexels、Archive.org、NASA、Wikimedia）剪主题蒙太奇 | 无（我们不做实拍素材检索） |
| `hybrid` | 源素材 + AI 生成的辅助画面 | `playbook/05-hybrid-genvideo.md` |
| `localization-dub` | 给现有视频加字幕、配音、翻译 | 无 |
| `podcast-repurpose` | 播客精彩片段转视频 | 剪辑与口播 |
| `screen-demo` | 打磨过的软件录屏演示 | 03 |
| `talking-head` | 以真人素材为主的演讲视频 | 剪辑与口播 |

**定位差异**：

| | OpenMontage | OpenVideoHarness |
|---|---|---|
| 形态 | 全套系统：工具注册表、YAML 管线、阶段导演 skill、Remotion composer、成本追踪 | 轻量 harness：类型文档 + playbook + 模板 + 引擎，靠 agent 读文档自己编排 |
| 画面来源 | 以生成式（图像 / 视频模型、素材检索）为主，再用 Remotion / HyperFrames 合成 | video-as-code，每帧是 t 的纯函数；生成式只在 `playbook/05-hybrid-genvideo.md` 里作补充 |
| 选型 | 供应商按 7 个维度打分，写 `decision_log` | BRIEF 和 STORYBOARD 两道关 |
| 许可 | AGPL-3.0 | MIT |

**可借用的规则**（都在 `OpenMontage/AGENT_GUIDE.md`）：
1. **执行前先宣布**：任何付费或有后果的生成调用前，说清工具、供应商、模型、理由，以及这是样片还是批量。
2. **不单方面替换**：换供应商、换模型、从"视频主导"降为"静图主导"、换渲染引擎、删掉旁白或音乐，都要先问。原路被堵时可以准备替代方案，但不能先执行。
3. **需要运动的片子禁止静图降级**：不能悄悄做成 Ken Burns 推拉或幻灯片，也不能静默从 HyperFrames 换到 Remotion。
4. **Templated vs Atelier**：主打作品默认"手写"，原则是"复用引擎知识，不复用创意组件"，收尾做一次"差异审查"（这片能不能套到别的产品上？是不是重复了我做过的样子？）。与 guizang 的"不套模板"同一思路。
5. **决策日志只追加**：改了已记录的选择，追加一条同 category、同 subject 的新记录，不改旧记录。
6. **CLI / 终端演示用合成录屏**（Remotion `TerminalScene`），不录真实屏幕；真实应用界面才录。

**AGPL 的影响**（一般理解，非法律意见）：
- 只读它的文档，用自己的话把规则写进 OpenVideoHarness：不涉及复制，本仓库仍是 MIT。
- 把它的代码、YAML 或 skill Markdown 复制进 OpenVideoHarness 并分发：这部分受 AGPL 约束，合并后的作品要按 AGPL 分发并提供源码，和 MIT 冲突，所以不做。
- 在本机把 OpenMontage 当独立工具运行、用它出片：AGPL 不限制使用；修改后以网络服务形式给别人用时，第 13 条要求向这些用户提供对应源码。

---

## 4. 纸拼贴 / Vox 风：三种做法对比

三个仓库都做"撕纸、网点、剪报、平涂色块"的编辑式纸拼贴，但画面从哪来、谁让它动，差别很大。

| | Paper-Cut（aijiduonadegou，16⭐） | gbro-collage-info（pyang5166，52⭐） | vox-director（Alisa0808，2.1k⭐） |
|---|---|---|---|
| 输入 | 主题、文案、文章或参考视频 | 口播逐字稿，从中挑段落 | 一句话选题（B-roll）；也可以是已有口播视频（A-roll）或一张照片（C-roll） |
| 图像模型 | **要**：图像模型出完整 hero frame，获批后从原图拆少量运动层 | **不要**：纯 HTML/CSS 卡纸剪片和半调截图 | **要**：`nano-banana-2` 每拍生成一张拼贴海报 |
| 视频模型 | 不用，除非用户明确改方法 | 不用 | 默认用：`gemini-omni-flash` 图生视频，真人或品牌用 `kling-video-o3-pro`；可选本地关键帧引擎把海报拆件驱动，不经视频模型 |
| 渲染 | HyperFrames（GSAP 图层动画、缓慢运镜） | HyperFrames 0.7.56，动效对齐 10 fps 定格网格（`steps()`） | ffmpeg 拼接、配乐闪避、烧字幕和水印 |
| 声音 | 旁白 + 纸片音效，可选接 ChatCut | 只有拟音；默认无口播、无字幕，交给剪辑台合成 | `xai/tts-v1` 旁白 + `minimax/music-2.6` 配乐，可用 `seed-audio` 克隆声音 |
| 画幅 | 横竖都可 | 1080×1920、30 fps、每条 5 秒 | 16:9 / 9:16 等，画幅近似要确认 |
| 关卡 | Gate 1 旁白、故事板、事实与敏感风险 → Gate 2 真实静帧、拆层计划、供应商与最大尝试次数 → Gate 3 完整预览 + QA，通过后才渲交付版 | Gate 1 选段 + 主动效分配 → Gate 2 静态样帧（headless Chrome 截图拼图）→ Gate 3 动画 + 拟音 + QA | 决策点 1 分镜（`beats.json`）→ 决策点 2 风格试片（同一拍渲 3–4 种主题）；另有画幅确认；其余全自动 |
| 付费 | 图像、语音、音效供应商（skill 不带额度） | 无，全部本机 | 必须有 Atlas Cloud API key |
| 本地路径 | `Paper-Cut/SKILL.md`、`Paper-Cut/references/image-led-production.md`、`Paper-Cut/references/hyperframes-assembly.md` | `gbro-collage-info/SKILL.md`、`gbro-collage-info/references/style-system.md`、`gbro-collage-info/references/motion-grammar.md`、`gbro-collage-info/assets/collage.css` | `vox-director/SKILL.zh.md`、`vox-director/references/prompt-guide.md`、`vox-director/references/local-engine.md` |
| 最值得借的一点 | 静帧先行，从获批原图拆层，只动承担叙事的少数元素 | 样帧就是动画的收帧；没拿到截图就用抽象灰条占位，绝不画假界面 | 风格诞生在生图这一步：图不够"拼贴"，后面救不回来；重滚一张图（约 $0.08）比拿弱图去付费做动画便宜 |

**放进 OpenVideoHarness 时**：gbro-collage-info 完全本机、确定性渲染，最贴合硬规则 1，适合 02 / 05 的竖屏信息段。Paper-Cut 的素材一旦定稿，后续动画仍是确定性的，适合 02 / 06 的 B-roll。vox-director 依赖视频模型输出（不可复现），而且涉及真人口型、声音克隆，应走 `playbook/05-hybrid-genvideo.md`，真人与声音必须有授权。

相关仓库：faceless-shorts-creator 的 `/make-vox` 轨道（AI 图层 + 抠图 + Remotion 镜头）；remotion-guofeng-starter 是国风版纸片拼贴；未拉取的 `pyang5166/gbro-collage-broll`（1.3k⭐，MIT）是 gbro 的 B-roll 版，描述写用 Gemini Omni Flash 首尾帧生成动画。

---

## 5. 许可证与复用结论

判定规则：MIT / Apache-2.0 可复用，但要保留版权和许可声明（Apache 还要保留 NOTICE、标注修改）；CC BY 可改写复用，但必须署名；AGPL 复用会传染，不能并入 MIT 的 OpenVideoHarness；非商用许可（CC BY-NC、PolyForm Noncommercial）和没有 license 的只能阅读。

| 仓库 | 本地核对的许可 | 代码 | 文档 / 素材 | 结论 |
|---|---|---|---|---|
| awesome-claude-video-skills | CC0 1.0（清单本身） | — | 清单文字可自由用；条目描述引自各仓库 | 可用 |
| lemo-opuscar | 整仓 MIT（`02dce5b` 起，2026-09-29；核对到 `721f0b7`）。更早的快照里指南、STYLE.md、成片是 CC BY 4.0 | 可复用，保留 MIT 声明（`tools/readcheck.py` 的读秒公式即改写自它的 `core/render/readcheck.mjs`） | 现版本的指南和 STYLE.md 同为 MIT，保留版权和许可声明即可；按旧快照改写的内容照旧署名 LemoLab、注明 CC BY 4.0；第三方采样、字体、音乐、人声见各样片的 `CREDITS` | 可复用（保留声明） |
| OpenMontage | AGPL-3.0 | 复用即传染 | 同左 | 只读 |
| video-shotcraft | Apache-2.0 | 可复用，保留 LICENSE、标注修改 | 音频多为 Mixkit，另有 6 个音效来源未能反查（见 `assets/audio/ATTRIBUTION.md`）；Remotion 自有许可 | 可复用；音频逐条核。`recipes/` 改写卡片文字和参数、不复制代码；改编的文件按第 4 条带许可原文和修改声明，清单见 `recipes/NOTICE.md` |
| guizang-product-video | AGPL-3.0；`assets/fallback/` 为 BSL 1.1 | 复用即传染 | BSL 部分另有使用限制 | 只读 |
| Paper-Cut | MIT | 可复用，保留声明 | — | 可复用 |
| gbro-collage-info | MIT | 可复用，保留声明 | 自带的 `gsap.min.js`（GSAP 3.14.2）和 10 个 Mixkit 音效按各自条款 | 可复用；捆绑件另核 |
| vox-director | MIT | 可复用，保留声明 | 生成内容受 Atlas Cloud 与各模型条款约束【推测】 | 可复用 |
| video-talkcraft | PolyForm Noncommercial 1.0.0；商用需作者事先授权 | 非商用可用，但不能并入 MIT 仓库 | 第三方图标等见 `THIRD_PARTY_NOTICES.md` | 只读 |
| faceless-shorts-creator | MIT | 可复用，保留声明 | — | 可复用 |
| data-animation-skills | MIT | 可复用，保留声明 | — | 可复用 |
| MathLens | 无 LICENSE 文件；README 声明 CC BY-NC 4.0 | 非商用许可，不能并入 MIT 仓库 | 同左 | 只读 |
| hand-drawn-explainer | Apache-2.0；`examples/` 媒体 CC BY 4.0；`vendor/srt-whiteboard-animation` 为 MIT | 可复用，保留 LICENSE 和 `THIRD_PARTY_NOTICES.md` | 示例媒体须署名；"小黑风格"借鉴自 Ian 的项目，不属于本仓库 | 可复用 |
| story-to-handdrawn-video | MIT；部分画风条目改编自其他 MIT 项目 | 可复用，保留声明（含 `references/` 下上游 LICENSE） | 演示 BGM 见 `BGM_CREDITS.md` | 可复用 |
| remotion-guofeng-starter | 代码（`src/`、`style/`、配置）MIT | 可复用，保留声明 | `public/` 演示图和音频、`docs/preview*.png` 不授予商用 | 代码可复用，素材只读 |
| viral-video-decomposer | MIT | 可复用，保留声明 | — | 可复用 |
| 3brown1blue、Code2Video | MIT | 可复用，保留声明 | — | 可复用 |
| hyperframes、hyperframes-launches | Apache-2.0（launches 的捆绑素材见 `NOTICE`，不在 Apache 范围内） | 可复用，保留 LICENSE / NOTICE | launches 素材另核 | 可复用 |
| functional-emotions-video | MIT（代码；歌曲、歌词和 `assets/` 音频不在内） | 可复用，保留声明 | 歌曲和音频不能用 | 代码可复用 |
| remotion-skills | 本地没有 LICENSE 文件 | — | — | 只读 |
| PDoomVideo | 没有 LICENSE | — | — | 只读 |
| claude-animation-skill | MIT（Copyright Hanif） | 可复用，保留声明 | `references/prior-art.md` 写明只借了别家 skill 的思路、没复制代码 | 可复用 |
| product-film-skill | MIT（skill 自身的文字和代码） | 可复用，保留声明 | 依赖的 Remotion 另受 Remotion License 约束；歌曲要自备授权 | 可复用；Remotion 另计 |
| procedural-film | MIT（Copyright Dean Kuhn） | 可复用，保留声明 | 蝴蝶样片的外观和剪辑参照 Kevin Ngo 的片子（见样片的 `docs/reference-analysis.md`）；Claude Quest 是 README 声明的非官方同人作品 | 可复用；样片的形象另慎 |
| opus55-guide-athemeroy | CC BY 4.0（原创文字、注释、表格、图表；整个仓库一份 LICENSE） | `scripts/` 也在 CC BY 4.0 下，复用须署名 | 帧缩略图、链接的帖子和视频、创作者 prompt 不在 CC BY 范围内，见 `THIRD_PARTY.md` | 可改写复用（署名） |
| opus55-catalog-zhuyansen | 没有 LICENSE；README 声明收录不授予许可 | — | 作品和 prompt 归各自作者；prompt 原文不在仓库里 | 只读 |
| Battle-of-Austerlitz-Film | 没有 LICENSE，README 也没提 | — | 成片、混音和字体未拉取 | 只读 |

---

## 6. Opus 5.5 发布周补充（2026-09-29）

这 6 个仓库都不在 183 个的清单里（本地 `skills.json` 是 2026-09-28 的快照），没有 Agent Skills Hub 的安全评级。本文逐个读了 README、LICENSE 和主 SKILL.md（或主源码），都已加进 `fetch.sh`。

| 仓库 | 本地路径 | ⭐（2026-09-29） | 许可 | 写在哪 |
|---|---|---|---|---|
| [athemeroy/awesome-opus-5-5-videos](https://github.com/athemeroy/awesome-opus-5-5-videos) | `opus55-guide-athemeroy/`（textonly） | 318 | CC BY 4.0 | 下文 |
| [zhuyansen/awesome-opus-5.5-video](https://github.com/zhuyansen/awesome-opus-5.5-video) | `opus55-catalog-zhuyansen/` | 33 | 无 | `cases/opus55-gallery.md` 第 5 节 |
| [WinterArc21/Battle-of-Austerlitz-Film](https://github.com/WinterArc21/Battle-of-Austerlitz-Film) | `Battle-of-Austerlitz-Film/`（textonly） | 12 | 无 | `cases/opus55-gallery.md` 第 6 节 |
| [buildwithhanif/claude-animation-skill](https://github.com/buildwithhanif/claude-animation-skill) | `claude-animation-skill/` | 21 | MIT | 第 1 节 07 |
| [Rieranthony/product-film-skill](https://github.com/Rieranthony/product-film-skill) | `product-film-skill/` | 358 | MIT | 第 1 节 03 |
| [kuhnhomeuk-cell/procedural-film](https://github.com/kuhnhomeuk-cell/procedural-film) | `procedural-film/`（textonly） | 460 | MIT | 第 1 节 02 |

claude-animation-skill 和 product-film-skill 带 `.claude-plugin/` 插件清单，那是 `claude plugin marketplace add` 时才读的文件，不会被自动加载，所以 `fetch.sh` 没有改它的名；三个 skill 的 SKILL.md 都放在 `plugins/` 或 `skills/` 下，也不会被当成本仓库的 skill。

### 三个 skill 的自查各管什么

三个 skill 都把"每帧是 t 的纯函数"当硬规则，但检查的重点各不相同，合起来正好是一条完整的链：

| | 逐帧检查 | 流程保护 | 成品检查 |
|---|---|---|---|
| claude-animation-skill | `sheet` 看静帧，`strip` 看快动作前后 12 帧；`verify` 把 5 个帧按正序、倒序、再正序渲三遍比 MD5 | 先写暂存目录，编码失败不覆盖旧文件，另写一份 `render.json` 记参数 | 看编码后母版的联系表 |
| procedural-film | `check.cjs` 六项关卡，确定性一项把同一帧按五种顺序画出来比哈希 | 从桩场景起关卡必须全绿；一个 agent 只拥有一个镜头文件，评审 subagent 分波次出 P1/P2 修改单 | 成片测响度，交付转码归一到约 −14 LUFS；逐镜写一行说明 |
| product-film-skill | 每个交接点出静帧，再出联系表和半分辨率草稿；`--debug` 把量到的坐标直接画进画面（Remotion 渲静帧时不转发 console） | 每次渲染的版本单独保留在 `out/<film>/vN/` | `verify.py` 解码每个交付文件：时长、背景色、首尾接缝、取色探针 |

我们的 `bin/vh check` 目前做 ffprobe 和黑帧、冻帧、静音检测。值得补的两件：一是把硬规则 1 的乱序比对做成命令，claude-animation-skill 的 `verify` 最简单；二是交付前解码成品核对色值，product-film-skill 踩到的色域问题在任何 Remotion 暗底片子上都会出现。

### athemeroy 的指南能借什么

athemeroy/awesome-opus-5-5-videos 是一份带来源的研究型目录：从 X 上 1,511 条候选帖、1,401 个去重后的视频里，挑 168 条逐条核对来源。作者反复提醒，这些数字只描述检索到的样本，不代表 X 上全部 Opus 视频。能借进 OpenVideoHarness 的有四样：

1. **按"像素从哪来"分 7 条制作路径**：代码绘制的 2D、教学讲解、3D 或实时图形、改造已有素材、外部视频模型管线、应用或游戏录屏、混合或无法判断。它强调只看一帧判断不了像素来源，要区分作者自述、公开可对上的源码或 prompt、自己观察到的现象三类证据。拉片时（`playbook/07-reverse-engineer.md`）可以用同样的分级。
2. **制作 brief 模板**（`docs/production-brief.md`）：比我们的 `templates/BRIEF.md` 多出三块：素材与权利表（每项素材的所有者、许可、怎么进片）、"谁做了什么"（模型、每个镜头的像素来源、人工）、实际成本与披露（调用次数、外部服务、人工返修、没核实的宣称）。可以对照 BRIEF 和 NOTES 的素材台账补。
3. **视觉效果适配指南**（`docs/visual-effects-fit.md`）：按任务族给出"怎么判定失败"和"什么时候该换专业工具"。三段验收是 brief 加关键帧 → 最难的 2–4 秒样片（看 12–24 个相邻帧，按不同顺序重渲同一时间点）→ 全片和可复现的交付；中间的样片这一步，我们的三道关卡里没有单列。它还提醒，"液态金属""磁场""碎裂"这类词，先要说清验收目标是看起来像，还是物理上对。
4. **配色模式研究**（`docs/color-modes.md`）：1,119 支预览里，13 种画风有 11 种分成两到三个配色模式，例如动效 / UI 类分成暗中性 198 支和亮中性 152 支。它的结论只到"颜色重要时，在 brief 里写明背景明度、主色和强调色，并逐镜检查色彩一致性"，并说明这不是实验证明的最佳配色，点赞差异也不说明因果。

许可：原创文字、注释、表格和图表是 CC BY 4.0，改写引用要署名 athemeroy 并注明许可；帧缩略图、链接的帖子和视频、创作者的 prompt 都不在 CC BY 范围内。
