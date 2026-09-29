# 案例库：Opus 5.5 社区代码视频精选

**来源**：[yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)，由 `references/fetch.sh` 拉到 `references/repos/awesome-opus5-5-videos/`（本文基于 2026-09-28 的提交 `6cdcea6`）。共 389 支用 Claude Opus 5.5 写代码做出的视频，来自 362 位作者，去重后是 328 个不同的 prompt。每条有 `prompts/<slug>.md`（作者分享的 prompt，文件顶部有原帖和 Skillry 并排对比页的链接）和 `data/videos.json` 里的元数据。

**许可**：仓库没有 LICENSE，prompt 归各自作者所有，只读。我们只做三件事：链接、指向本地路径、写自己的分析。不要把原文复制进本仓库的任何文件，也不要原样贴进项目的 BRIEF。下文全部是转述，引文不超过 12 个词。

**怎么用**：

1. 做某类视频前，从第 3 节挑 2–3 条同类型的条目，打开它们的 prompt 文件，逐项对照 `templates/BRIEF.md`。看两件事：它把哪些东西写死了，而我们留给了默认值（时长、节拍、禁用清单、自查方式）；我们的 BRIEF 又多了哪些它没有的（reads、事实来源、音频时间表）。
2. 用户说"照这支做一个"时，配合 [playbook/07-reverse-engineer.md](../playbook/07-reverse-engineer.md) 使用：先从作者链接看原片拉片，再读作者的 prompt 对照。
3. 接到很短的需求时，先读第 1 节最后两条。

[community-prompts.md](community-prompts.md) 拆的是另一份二手合集；本文做的是整本目录的统计和精选。Claude Pop 和 P(doom) 的完整拆解见 [mv-claude-pop.md](mv-claude-pop.md)、[mv-pdoom.md](mv-pdoom.md)。

第 1–4 节只基于上面这份 389 支的目录。第 5、6 节是 2026-09-29 补的，和它分开读：第 5 节介绍第二份目录（Jason Zhu 整理的 962 支，只有元数据），第 6 节深读一支不在 389 支里、但源码公开的 5 分钟 3D 历史长片。

## 1. 统计

口径：统计对象是 `data/videos.json`，计算日期 2026-09-29。词数按空格分词，中日文每 2 个字折合 1 词。各项特征先用正则初筛，再逐条人工核对，结果是近似值。

| category | 条数 | 其中 `prompt_partial=true` | 完整 prompt 词数中位 |
|---|---|---|---|
| motion | 223 | 6 | 27 |
| interactive | 68 | 50 | 64 |
| 3d | 51 | 31 | 64 |
| explainer | 47 | 23 | 24 |
| 合计 | 389 | 110（28%） | 29 |

- **partial 条目多半不是 prompt**：`prompt_partial=true` 的条目里放的多是推文正文。这类条目集中在 interactive、3d、explainer 三类，所以这三类里真正能拿来学写法的，分别只有 18、20、24 条。
- **tech_tags 记录的是重做版的技术栈**：canvas 288（74%）、threejs 130（33%）、svg 125、shader 95、gsap 59、css 39、audio 36（9%）、particles 26、playable 21、pixel 15，ai-image / webgl / physics 各 9。这些标签和每个 prompt 文件里的 "Remake built with" 逐条一致，说的是 Skillry 重做时用的技术，不是作者原片的工具（例如点名要 Manim 的那条被标成 svg · audio）。作者在完整 prompt 里亲自点名的工具很少：ffmpeg 18 条、seek(t) 或"每帧是时间的纯函数" 18、Playwright 17、numpy 11、Remotion 3、Blender 2、HyperFrames 1、Manim 1。
- **长度**：全部 389 条按空格分词，中位数是 31 词（CLAUDE.md 引用的就是这个口径）；只看 279 条完整 prompt，中位数 29 词，四分位 21 / 69，最长 4142 词。分布：≤15 词 46 条，16–30 词 101，31–60 词 55，61–150 词 36，151–400 词 15，401–1000 词 18，>1000 词 8。72% 的完整 prompt 不超过 60 词。超过 400 词的 26 条里，有 11 条是 `<inputs>` 输入槽模板（来自 4 个不同的模板）。
- **showreel 原句与人设**：71 条含有 "showreel for a résumé … go all out" 这句原话。其中 46 条原样照搬，只改了时长或标点；25 条在后面追加了产品、主题或约束。另有 28 条是改写版，三者合计 99 条（25%）。另外 13 条用了显式的角色设定（"你是世界级动效设计师"、"假装你是……"、"证明你有多强"）。两种人设写法合计 112 条（29%）。还有 7 条让模型把自己当成片子的主角。
- **时长**：162/279 条完整 prompt 写了时长（58%），但去掉 showreel 系之后只剩 69/180（38%）。写了时长的，中位数是 15 秒：101 条 ≤15 秒，超过 60 秒的只有 11 条。
- **声音**：约 55 条（20%）要音乐或音效。其中约 20 条自带歌曲或指定了免版税曲目，约 12 条要求在代码里合成，约 30 条提到节拍或同步。要旁白的只有 4 条（linearuncle、tak3sh8、astrothewizard、1stnoel），没有一条提到词级时间戳。
- **流程**：明确要求先交分镜（storyboard）的只有 2 条，而且出自同一个模板。另有 5 条是用户自己写好了带时间码的分镜；10 条要求先在节拍网格上列出状态表或节拍图。写了"动手前先给我看"这类关卡的共 14 条。要求自查（逐拍出一帧、联系表、截图、检查后修改）的 24 条（9%），去重后只有 16 个不同的 prompt。
- **复刻与模板**：约 8 条以一支具体的参考视频或 repo 为底；约 5 条致敬名作的风格（Apple 1984、Sledgehammer、布达佩斯大饭店）。`<inputs> Ask me for` 这种输入槽写法有 12 条，其实只来自 5 个模板，其中一个被 7 人原样使用。要求先调研（查官网、拉数据、找素材）的约 24 条，其中 8 条是同一个 SaaS 发布模板。
- **含义一：短 prompt 是常态，不代表用户没想清楚。** 一句话里真正带信息的是格式、题材和约束：时长、画幅、风格参照、声音。showreel 句式和人设句式基本不带信息。agent 应该用类型文档的默认值把缺的项补进 BRIEF，在关卡 ① 列出"我替你定了什么"让人改，不要逐项反问。
- **含义二："go all out" 授权的是审美，不是跳过关卡或事实纪律。** 长 prompt 里反复出现的东西，比如节拍网格、禁用清单、逐拍出帧自查、按实测峰值摆放音效，我们的默认流程里本来就有。所以收到短 prompt 也照完整流程走，只是把关卡 ① 做轻。

## 2. prompt 原型

| 原型 | 长什么样（转述） | 什么时候管用 | 典型长度 | 例子 | 对应类型 |
|---|---|---|---|---|---|
| 一句话 showreel | 一段 15 秒动效，让模型把它当成简历作品集，"go all out" | 没有题材，只要炫技，能接受多抽几次。99 条同源，成片风格趋同 | 25–40 词 | `ajith-io-890146`（原句）、`prasenx-693512`（加了代码作曲、切点落在拍上） | 没有直接对应的类型：有产品按 03，纯炫技快剪按 08 |
| 产品 / SaaS 发布加调研 | 让模型自己挑一个知名 SaaS 或读官网，抓真实素材做发布片 | 产品有公开的官网和素材。风险是编造功能，这类 prompt 里没人写事实护栏 | 30–100 词 | `moritzkremb-466494`、`jhylee95-452427` | 03 |
| 输入槽模板 | 分成 inputs / direction / structure / build / gotchas / start 几节，开头让模型先问要哪些素材，结尾要求先交节拍状态表再写代码 | 可重复的格式（UI 变形、产品 promo）。和我们的 BRIEF 加关卡最接近 | 260–960 词 | `twoclipping-402193`、`verbove-268381` | 03 |
| 概念讲解 | "讲清楚 X"，再加一个硬约束（引擎、画风、声音，或者"每帧是时间的纯函数"） | 概念本身有现成的视觉隐喻。讲得多深全靠模型自觉 | 10–40 词 | `parkerrex-701462`、`linearuncle-971663` | 01 / 02 |
| 叙事 / 氛围短片 | 一个固定画面或一个设定，加一个名作风格参照 | 画面单一，时间流逝本身就是叙事；可以重抽 | 10–30 词 | `itsolelehmann-762215`、`kamstudiolabs-100086` | 07（叙事类也可以按 02） |
| 音乐驱动 | 附一首歌，先测 BPM 和各段能量，规定切点规则和特效强度 | 已经有音频。最依赖节拍分析 | 40–800 词 | `pound75423-464968`、`samaote-124569` | 04 |
| 复刻参考 | 给一支视频、一个 repo 或一部名作，要求同风格换内容，或者做一个更新版 | 参考能拿到，用户能判断像不像 | 20–1750 词 | `doubleunplussed-181894`、`ajith-io-615243` | 对应类型，加上 playbook/07 |
| 长篇导演 brief | 写死规格、色板、字体系统、带时间码的分镜、禁用清单和质检 | 用户心里已经有明确的画面；相当于用户替 agent 写好了 BRIEF 和 STORYBOARD | 500–4100 词 | `howdevelop-733090`、`techhalla-498547`、`alexwtlf-981005` | 03 / 08（按内容定） |
| 3D / 着色器场景 | 一句话要一个空间（"inside an AI data centre"），或者要求照史料建模 | 空间本身就是内容。镜头路径和信息层要另外补 | 10–170 词 | `mdaman010-111079`、`alexalbert-274839` | 暂无专属类型：讲机制的按 01/02，要写实的走 playbook/05 |
| 交互 / 可玩 | 游戏 PRD、单文件 HTML 状态机、点击触发的演出 | 只能当审美和工程参数的参考；成片要另外录屏 | 20–1900 词 | `zacxbt-944604`、`op7418-814408` | 不对应视频类型 |

## 3. 精选

标记的含义：【音】音乐或音效，【旁白】配音，【分镜】分镜或时间码，【自查】渲染后检查，【关卡】动手前先给人看，【复刻】以参考为底，【调研】先查资料，【事实】有事实护栏，【模板】输入槽模板。词数的算法同第 1 节。路径都相对于仓库根目录，均已核对存在。

### 01 数学、科学讲解

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@LinearUncle](https://x.com/LinearUncle/status/2103128559174971663) | 01 | svg · audio | 20 | 中文一句话，同时点名了引擎（Manim）和配音（edge-tts），还要求有例子、能引人思考。可借：一句话里先把引擎和声音定下来。缺时长和 reads，要补进 BRIEF。【旁白】 | `references/repos/awesome-opus5-5-videos/prompts/linearuncle-971663.md` |
| [@ParkerRex](https://x.com/ParkerRex/status/2103206747846701462) | 01 | canvas · physics | 23 | 一句话说出了我们的硬规则 1："every frame a pure function of time"，并给了理由：方便渲染器截图。可借：约束附上理由，模型更守得住 | `references/repos/awesome-opus5-5-videos/prompts/parkerrex-701462.md` |
| [@emollick](https://x.com/emollick/status/2103688362960019567) | 01 | canvas | 21 | 讲递归，每一层解释换一种截然不同的画风，形式本身就是内容。风险是风格跳来跳去压过信息，要靠 reads 兜底 | `references/repos/awesome-opus5-5-videos/prompts/emollick-019567.md` |

### 02 知识短视频

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@AstroTheWizard](https://x.com/AstroTheWizard/status/2103629247751618782) | 02 | canvas | 398 | 目录里最接近我们整条流水线的一条。60 秒的光子之旅，要求：用真实数字并说明估计的不确定性；随机游走要真算出来；TTS 旁白加烧录字幕；代码作曲；音效对准动作；混音时音乐给人声让位，并统一响度；每个场景出静帧自评，逐帧检查转场。它的交付清单可以直接拿来对照 BRIEF 的 Spec 和 Acceptance。【旁白】【音】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/astrothewizard-618782.md` |
| [@x4b47x](https://x.com/x4b47x/status/2103019799614034026) | 02 | canvas · particles · audio | 31 | 31 个词写全了画幅（9:16）、时长区间、画风（剪纸皮影）、声音（代码生成）和题目，是一句话 prompt 的最小完整集合。【音】 | `references/repos/awesome-opus5-5-videos/prompts/x4b47x-034026.md` |
| [@songkeys](https://x.com/songkeys/status/2102743212922384673) | 02 | canvas | 72 | 用折纸涂鸦讲人类文明一路发展到 AI，要求不同文明的人都能看懂，所以不用口语，也少用文字。可借："静音也能看懂"写成对受众的约束，而不是技术约束 | `references/repos/awesome-opus5-5-videos/prompts/songkeys-384673.md` |
| [@Michaelzsguo](https://x.com/Michaelzsguo/status/2102592355165782312) | 02 | shader · canvas | 29 | 两分钟沙画讲 250 年美国史，带配乐和音效。可借：用一种媒介（沙）当贯穿全片的母题。两分钟的片子只给了 29 个词，节奏和事实全交给模型，适合拿来对照我们的分镜关卡。【音】 | `references/repos/awesome-opus5-5-videos/prompts/michaelzsguo-782312.md` |

### 03 产品宣传

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@moritzkremb](https://x.com/moritzkremb/status/2103066071838466494) | 03 | svg · gsap | 88 | 发布片模板：自己挑一个知名 SaaS，去网上找真实素材。被 5 人原样照搬，3 人改写。可借：真实素材优先。它没写时长，也没有事实护栏，既是反例也是基线。【调研】 | `references/repos/awesome-opus5-5-videos/prompts/moritzkremb-466494.md` |
| [@HowDevelop](https://x.com/HowDevelop/status/2103840883812733090) | 03 | canvas | 515 | 15 秒的开发者工具发布片：6 段带时间码的分镜，内容留在 9:16 安全区内，静音也要讲得通，配原创电子音效。附一节 "Accuracy guardrails"，禁止把 RC 版说成稳定版，也不许把规划中的功能说成已发布。可借：事实护栏的写法。【分镜】【音】【自查】【事实】 | `references/repos/awesome-opus5-5-videos/prompts/howdevelop-733090.md` |
| [@twoclipping](https://x.com/twoclipping/status/2103273003555402193) | 03 | svg | 464 | "一个形状、永不切镜"的 UI 变形模板：先问用户要素材；用 numpy 测拍；seek(t) 配闭式弹簧；Playwright 渲子帧做运动模糊；先每拍出一帧检查，再全片渲染；动手前先交节拍状态表。被 7 人原样使用。可借：它 gotchas 一节的写法。【模板】【音】【关卡】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/twoclipping-402193.md` |
| [@twoclipping](https://x.com/twoclipping/status/2102554209166000267) | 03 | svg · css | 448 | 同一作者的产品 promo 模板：素材用用户自己的竖屏片段；10 小节的节拍结构；音效按实测峰值对位；响度 -14 LUFS；渲染前抽查 20 帧；动手前必须交一份标好节拍时间的分镜。几乎就是社区版的"关卡 ② 加音频管线"。【模板】【分镜】【音】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/twoclipping-000267.md` |
| [@Bilimfili1](https://x.com/Bilimfili1/status/2103743617848459762) | 03 | canvas · svg | 132 | 竖屏 App 片：每个功能都在模拟器里真实录屏，屏幕上的数字只能来自录屏，每个功能至少停留 2.5 秒，文字避开平台的 UI。目录里少见的、写法接近 reads 的约束。【事实】 | `references/repos/awesome-opus5-5-videos/prompts/bilimfili1-459762.md` |
| [@jake11moran](https://x.com/jake11moran/status/2103237884564414633) | 03 | canvas · svg · gsap · ai-image | 364 | 目录里唯一点名 HyperFrames 的一条：一镜到底，推拉摇各 1.5–3 秒，"用你默认速度的一半"，7 个编号节拍，照着原帖视频复刻 UI。拆解已收在 community-prompts.md。【复刻】 | `references/repos/awesome-opus5-5-videos/prompts/jake11moran-414633.md` |

### 04 歌词视频、MV

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@pound75423](https://x.com/pound75423/status/2103722556918464968) | 04 | canvas · css | 433 | 日文的迷幻 glitch MV：Canvas 逐帧画，Playwright 截帧，ffmpeg 合成。先测出 BPM、首拍、各小节开头和各段能量；每拍切一次镜；特效强度按前奏、主歌、副歌分别设为 40%、70%、100%；正式渲染前先交各段截图。可借：把剪辑规则写成一张能照做的表。【音】【关卡】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/pound75423-464968.md` |
| [@doubleunplussed](https://x.com/doubleunplussed/status/2103697580421181894) | 04 | canvas | 396 | 用 PDoomVideo 的风格给一首 Suno 歌做 MV，要求用 AI 圈的典故，不要逐句图解歌词；后面附了两轮具体的返修意见（角色的嘴型、手臂）。可借：返修意见怎么写。配合 mv-pdoom.md 看。【复刻】【音】 | `references/repos/awesome-opus5-5-videos/prompts/doubleunplussed-181894.md` |
| [@anabology](https://x.com/anabology/status/2103534482930491441) | 04 | canvas · ai-image | 1751 | Claude Pop 那条长 prompt：用同一条音轨重做 MV，先用 Seedance 出底片，再用 JS 重画，反复看全片截图自评。目录把它记在 @anabology 名下，但正文和 mv-claude-pop.md 里 @donaldjewkes 更早公开的 prompt 基本一致，归属以原帖为准（未核实）。`anjmaxx-459455` 是它的删改版。【复刻】【音】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/anabology-491441.md` |
| [@samaote](https://x.com/samaote/status/2103510974796124569) | 04 | shader · canvas · svg | 39 | 把 showreel 原句改成：按附带的音乐做歌词动效，对齐人声和节拍。这是最短的歌词 MV prompt，但没说歌词时间从哪来，这正是 playbook/04 的词级时间表要补的。【音】 | `references/repos/awesome-opus5-5-videos/prompts/samaote-124569.md` |
| [@KamStudioLabs](https://x.com/KamStudioLabs/status/2102899866762440893) | 04 | canvas · physics · audio | 19 | 一台 45 秒的机器，每个音符都来自一次看得见的碰撞。声音和画面出自同一个来源，同步自然成立，适合拿来做音乐类的一句话探索。【音】 | `references/repos/awesome-opus5-5-videos/prompts/kamstudiolabs-440893.md` |

### 05 数据故事

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@GroundControl](https://x.com/GroundControl/status/2103678647777230877) | 05 | canvas · audio | 107 | 3 分钟的 2026 年日本高温可视化：先拉在线数据，和往年比较；铅笔手绘风加一点色差；用 JS 合成器配旋律。数据来源、画风、声音三样都写了，唯独缺核对数据这一步。【调研】【音】 | `references/repos/awesome-opus5-5-videos/prompts/groundcontrol-230877.md` |
| [@RetropunkAI](https://x.com/RetropunkAI/status/2103237989065277590) | 05 | canvas · svg · gsap · ai-image | 126 | 拉斯维加斯 Sphere 的简史时间线：给了 Wikipedia 来源和本地图片目录，时长"按信息量定在 30–60 秒"，允许先提问。可借：时长随内容定，来源直接写进 prompt。【调研】 | `references/repos/awesome-opus5-5-videos/prompts/retropunkai-277590.md` |
| [@nummanali](https://x.com/nummanali/status/2103565570310340931) | 05 | canvas | 82 | 口述式 prompt，要讲今年以来 LLM 能力的走势，要"bang, bang, boom"的冲劲。可当反面样本：没给数据源，数字全靠模型的记忆。我们的事实纪律在这种题材上最用得上 | `references/repos/awesome-opus5-5-videos/prompts/nummanali-340931.md` |

### 06 论文讲解

目录里没有真正的论文讲解样本。做 06 时以类型文档为准，事实护栏参考上面的 `howdevelop-733090` 和下面的 `alexalbert-274839`。

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@tak3sh8](https://x.com/tak3sh8/status/2103667481139441895) | 06 | canvas · audio | 24 | 用白板手绘讲 SK 模型的复本对称破缺，第二轮才要带旁白的 mp4。这是目录里最接近论文级概念的一条。可借：先做静音版把讲法定下来，再加旁白。【旁白】 | `references/repos/awesome-opus5-5-videos/prompts/tak3sh8-441895.md` |
| [@henkvaness](https://x.com/henkvaness/status/2103801351993975279) | 06 | svg | 6 | "把文章做成教学视频"，一共 6 个词，说明社区在这一类上还没有写法积累。原文的读取、提炼和核对都要靠我们的流程来补 | `references/repos/awesome-opus5-5-videos/prompts/henkvaness-975279.md` |

### 07 手绘、剪纸、角色短片

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@eric_khun](https://x.com/eric_khun/status/2103112385380667455) | 07 | canvas | 195 | 中秋手绘片：把附带的台湾黑熊角色逐项描述下来（剪影、耳朵、眼圈、胸前的 V 字），锁住形象；先调研台湾人怎么过中秋；文字中英双语；流程写作"plan it out, draft and render"。可借：角色身份锁的写法。【调研】 | `references/repos/awesome-opus5-5-videos/prompts/eric-khun-667455.md` |
| [@itsolelehmann](https://x.com/itsolelehmann/status/2103124033365762215) | 07 | canvas | 21 | 火车窗外四季流转，布达佩斯大饭店的风格。一个固定机位，加上时间流逝，再加一个具名的风格参照，一句话就够了 | `references/repos/awesome-opus5-5-videos/prompts/itsolelehmann-762215.md` |
| [@KamStudioLabs](https://x.com/KamStudioLabs/status/2102908742518100086) | 07 | canvas · audio | 18 | 45 秒的无对白短片，让声音讲一半的故事，故事自己编。可借：把声音放进叙事结构里；我们的 sfx 管线可以直接接上。【音】 | `references/repos/awesome-opus5-5-videos/prompts/kamstudiolabs-100086.md` |
| [@koldo2k](https://x.com/koldo2k/status/2103129343253778767) | 07 | canvas · ai-image | 269 | 复古拼贴风的无限缩放：生成的图按深度分成三层做视差；指数缩放保证速度恒定；96 BPM 的 8 小节正好 20 秒；每一步花钱之前，先列清单等确认、给截图。可借：费用关卡和写成数学的镜头规格。属于混合路线，配合 playbook/05 看。【关卡】【自查】【音】 | `references/repos/awesome-opus5-5-videos/prompts/koldo2k-778767.md` |

### 08 野兽派、网络梗、科技推特风

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@techhalla](https://x.com/techhalla/status/2103411244468498547) | 08 | canvas | 634 | 街头海报式的品牌片头：严格的三色色板，三种字体各有分工，文案锁死不许改，6 段带时间码的叙事弧，seek(t) 配闭式弹簧，正式渲染前每个大拍出一张静帧，外加一长串禁用项。几乎可以直接当 08 类 STYLE.md 的范本。【分镜】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/techhalla-498547.md` |
| [@kloss_xyz](https://x.com/kloss_xyz/status/2103664956482941143) | 08 | canvas · audio | 61 | 用 Python 生成 9:16 的 brain rot 视频，看重动效和声音设计，用 ffmpeg 出片，从模型自己的视角来讲。可借：prompt 很短，但画幅、工具链、声音都写明了。【音】 | `references/repos/awesome-opus5-5-videos/prompts/kloss-xyz-941143.md` |
| [@Gdgtify](https://x.com/Gdgtify/status/2103458245213929495) | 08 | canvas | 675 | 20 秒的动态排版演讲：每个关键词都担任一个建筑构件；节奏跟着短语和停顿走，不跟节拍；至少有一次 400ms 的完全静止；质检时看 8 帧，确认阅读顺序没乱。可借：reads 在社区里的写法（先让人读完，再变形）。风格偏编辑排版，也能用在 02。【分镜】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/gdgtify-929495.md` |

### 3D / 着色器

我们还没有这一类的类型文档，这里标出每条借到哪一类。

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@alexalbert__](https://x.com/alexalbert__/status/2102466523164274839) | 01 / 02 | threejs · shader · canvas | 165 | 用 Blender Python 重建 1906 年地震前一天的旧金山市场街：先建一份来源表，每栋楼的每条事实都记下来源和置信度，再用生成器把整条街搭起来，最后出一段 10 秒的视频。是事实纪律方面最强的样本。【调研】【事实】 | `references/repos/awesome-opus5-5-videos/prompts/alexalbert-274839.md` |
| [@zeezomb](https://x.com/zeezomb/status/2102906701552726206) | 07 | threejs · shader | 68 | 80 秒的方形 WebGL2 短片，不用任何库和素材文件：一面没粘牢的马赛克墙，角色由成群的瓷砖组成。可借：一个材质设定就撑起整片的视觉系统 | `references/repos/awesome-opus5-5-videos/prompts/zeezomb-726206.md` |
| [@mdaman010](https://x.com/mdaman010/status/2103845689713111079) | 02 | threejs · shader · svg | 10 | "Show me what goes on inside an AI data centre." 另有一人原句照搬。可以看出 3D 穿越类一句话 prompt 的上限；镜头路径和信息层要另外写 | `references/repos/awesome-opus5-5-videos/prompts/mdaman010-111079.md` |
| [@FornYapayZeka](https://x.com/FornYapayZeka/status/2102971287224135914) | 02 | threejs · shader | 153 | 土耳其语：做出最有冲击力的爆炸，起爆、扩散和爆后的变化都要看得见；动手前先比较几个想法，挑最原创的那个。可借："不要第一个想法"的写法 | `references/repos/awesome-opus5-5-videos/prompts/fornyapayzeka-135914.md` |
| [@AxtonLiu](https://x.com/AxtonLiu/status/2103119648271290566) | 07 | shader · webgl | 56 | 中文：画一个最复杂、最精细的"鹈鹕骑自行车"动画，"画一天都可以"。给时间预算而不是给规格，适合探索方向，但成片不可控 | `references/repos/awesome-opus5-5-videos/prompts/axtonliu-290566.md` |
| [@abhinayguptha](https://x.com/abhinayguptha/status/2103565090721259981) | 03 / 08 | shader · webgl · canvas | 25 | 给一部不存在的 Netflix 惊悚剧做 20 秒片头，要有拿艾美奖的水准。可借：用一个虚构的委托加上奖项标准，代替风格描述 | `references/repos/awesome-opus5-5-videos/prompts/abhinayguptha-259981.md` |

### 交互（仅作参考）

这些作品不是视频，只借它们的审美参数和自查清单。

| 作者 | 类型 | tech tags | 词数 | 值得学什么 | 本地路径 |
|---|---|---|---|---|---|
| [@op7418](https://x.com/op7418/status/2103724883301814408) | — | threejs · shader · canvas · gsap | 977 | 中文的手游"高光时刻"演出：分五段节奏；Three.js 卡通着色，用法线和深度做描边；Web Audio 实时合成音效；交付前在四个关键时刻各截一张图，逐项自检。它的自检问题（主体有没有被挡住、有没有过曝、描边有没有穿帮、小字能不能看清、停下后还在不在抖）可以并进 TASTE_CHECKLIST。【音】【自查】 | `references/repos/awesome-opus5-5-videos/prompts/op7418-814408.md` |
| [@zacxbt](https://x.com/zacxbt/status/2103808699466944604) | 07 | canvas · pixel · playable | 347 | 像素巫师：128×96 的逻辑分辨率按整数倍放大，固定 24 色色板，姿态参数量化出 8–12fps 的像素动画手感。可当像素风的参数表用。注意它用的是固定步长模拟，不是 t 的纯函数，搬过来要改写 | `references/repos/awesome-opus5-5-videos/prompts/zacxbt-944604.md` |
| [@gandamu_ml](https://x.com/gandamu_ml/status/2102919394775220530) | 04 | threejs · shader · canvas · audio | 161 | 用给定的 S3M 曲目做一支 90 年代风格的 demoscene：动手前先分析曲目各段的情绪，调研合适的特效，用 C/C++ 加 OpenGL 实现。可借：先分析音乐、再定场景的顺序。【音】【调研】 | `references/repos/awesome-opus5-5-videos/prompts/gandamu-ml-220530.md` |

## 4. 我们的 harness 在这之上多了什么

- **关卡**：目录里只有 14 条写了"动手前先给我看"，而且都集中在少数几个模板里；我们默认有三道人工关卡。代价是慢。像 itsolelehmann、mdaman010 这种一句话、可以重抽、不涉及事实的片子，一句话直接出更划算。用户说"直接出"就跳过关卡，并记进 REVIEW.md。
- **reads**：社区 prompt 几乎不写"观众在第几秒必须看懂什么"，最接近的是 bilimfili1 的"每个功能至少停 2.5 秒"和 gdgtify 的"先读完再变形"。我们把 reads 写进分镜，并且不许重叠。对长片、讲解和数据类，这是最该多出来的一层；对 15 秒的炫技片，收益很小。
- **自查**：24 条要求自查，写法各不相同：每拍一帧、抽 20 帧、看 8 帧、截图。我们用 TASTE_CHECKLIST 加联系表、strip、crop 把它固定下来，并要求交片时写出自己最不满意的 2–3 处。op7418 那份自检问题清单值得并进来。
- **音频**：约 55 条要声音，但只有 4 条要旁白，没有一条提到词级时间戳，也没有一条说"由音频决定时长"。社区里好的做法（numpy 测拍、按实测峰值摆音效、-14 LUFS）已经写在 playbook/04 和 `bin/vh music / sfx / beats` 里；我们多出来的是这一步：TTS 生成时间表，再用它回写分镜。
- **事实纪律**：写了事实护栏的只有 howdevelop、alexalbert、bilimfili1 等寥寥几条，而 nummanali 这种口述式的数据题材恰恰最需要。我们的硬规则 5 和 NOTES.md 就是为这种情况准备的。
- **一句话够用的时候**：三个条件同时满足时，一句话就够用：格式本身足够具体，允许风格自由发挥，可以接受重抽（和 community-prompts.md 的结论一致）。这时 harness 的价值主要在确定性渲染、出片和音频，不在创意本身。不要为了走流程，把一句话需求扩写成 BRIEF，再逐项去问用户。

## 5. 第二份目录：awesome-opus-5.5-video（962 支，只有元数据）

**来源**：[zhuyansen/awesome-opus-5.5-video](https://github.com/zhuyansen/awesome-opus-5.5-video)，Jason Zhu（@GoSailGlobal）整理；网页版在 <https://jasonzhu.ai/en/prompts/claude-opus-5-5>，中文版把 `/en/` 换成 `/zh/`。`references/fetch.sh` 把它拉到 `references/repos/opus55-catalog-zhuyansen/`，本节基于 2026-09-28 的提交 `ffb3c5a`，数据快照时间是 2026-09-28 09:27 UTC。

**许可**：仓库没有 LICENSE，README 写明收录不授予任何许可，作品和提示词归各自作者。和第 1–4 节一样只读：只链接、只转述。

**和上面那份的关系**：两份目录是独立收集的，口径不同。按原帖 status id 比对，389 支里只有 55 支也在这份目录里。所以两边的数字不能相加，也不能拿来改第 1 节的统计。

**规模**（逐项按 `cases.json` 核对）：962 个作品，638 位创作者，原帖播放量合计 122,860,185（约 1.23 亿）。其中 252 个附了能追溯出处的提示词：94 条是完整提示词（`kind: full`），158 条是一句话指令（`kind: brief`）。出处分别是主帖正文 145 条、作者本人的回复 101 条、作者给的链接 3 条、截图 3 条。另有 267 条标了 `reference_assets`，意思是作者除了文字还喂了图片、视频、音频或代码，光看提示词复现不了。

**收录标准**（README 原意）：
- 创作者本人的原帖，帖子自带视频，原帖播放量不低于 5,000（快照 2026-09-28）；
- 帖子明确说是用 Claude Opus 5.5 做的，模型归属以作者自述为准，没有逐条复现；
- 提示词只收有出处的（主帖、作者回复、回复里的截图、作者给的链接），一律原文照录，不改写、不翻译；
- 有视频但找不到指令来源的作品照样收录，提示词一栏留空。

**8 个分类**：

| category | 中文名 | 条数 |
|---|---|---|
| motion | 动效设计 | 172 |
| game | 游戏 | 158 |
| art3d | 3D 场景 | 131 |
| product | 产品广告 | 128 |
| comparison | 模型对比 | 104 |
| stories | 角色故事 | 101 |
| education | 科普讲解 | 93 |
| production | 制作流程 | 75 |
| 合计 | | 962 |

**提示词原文不在仓库里**：`cases.json` 的 `prompt` 字段只有 `kind`、`length`（字符数）、`source`、`source_url` 和 `page_url`，原文要去网页上看。所以这份目录适合用来找作品、按播放量或收藏排序、看作者自述用了什么工具（`tools_reported` 里 Three.js 67 条、Blender 54、Higgsfield 40 最多，Remotion 15，HyperFrames 9）；要学写法，还是回到第 3 节读本地的 prompt 文件。查询示例：

```bash
jq -r '.cases[] | select(.category=="art3d") | [.bookmarks,.views,.creator.handle,.title.zh,.original_post_url] | @tsv' \
  references/repos/opus55-catalog-zhuyansen/cases.json | sort -rn | head
```

**3D 场景类值得看的三条**（按收藏数，2026-09-28 快照）：art3d 类收藏前五里有两条要先排除，它们其实是 MV 翻拍：第 1 名 @anabology 和第 3 节 04 里的 `anabology-491441` 是同一条帖子，照 Claude Pop 那份共享长 prompt 做的；第 3 名 @pleometric 的标题是"根据流传提示词制作的场景"，多半就是 Movez 的课程（见 `community-prompts.md`）提到的那条：拿同一份长 brief 配上自己的图库重跑（未看原片核对）。剩下三条是：

| 作者 | 作品 | 时长 | 播放 / 收藏 | 提示词 | 值得看什么 |
|---|---|---|---|---|---|
| [@MengTo](https://x.com/MengTo/status/2102760783344189761) | 日式风景里可操控的小船，Three.js | 60 秒 | 466,671 / 3,760 | 完整提示词 | 交互场景，成片是录屏；按第 3 节"交互"一类的方式参考 |
| [@dangreenheck](https://x.com/dangreenheck/status/2102878170089169235) | 程序化生成的海岛模拟 | 227 秒 | 852,410 / 3,371 | 无 | 接近 4 分钟的程序化场景，镜头怎么在一个世界里连续移动 |
| [@Aurelien_Gz](https://x.com/Aurelien_Gz/status/2102786378282987591) | 开源的浅水面模拟 | 27 秒 | 242,931 / 2,628 | 无 | 源码公开：[Aureliengmz/clearwater](https://github.com/Aureliengmz/clearwater)（MIT），单个 HTML 文件、WebGL2、不用库，说明写实水面可以是实时着色 |

第 6 节的 Austerlitz 在这份目录里归在 stories 类（播放 607,719，收藏 1,657）。

## 6. 3D 长片深读：Battle of Austerlitz

在源码公开的社区作品里，这是最接近"用代码拍一部 5 分钟纪录片"的一支。它的做法是：先生成旁白，把实测时长折算成时间线，再让镜头、配乐、音效和字幕都挂在这条时间线上。这和我们的硬规则 2 是同一个思路，只是它做得更彻底，连回写都是自动的。

**基本信息**：
- 作者 Winter，原帖 [@WinterArc2125](https://x.com/WinterArc2125/status/2103116235009347650)（2026-09-24），源码 [WinterArc21/Battle-of-Austerlitz-Film](https://github.com/WinterArc21/Battle-of-Austerlitz-Film)，只有一次提交 `86dae32`。成片 5:01，1920×1080，24 fps，立体声，另附英文 SRT。
- 本地在 `references/repos/Battle-of-Austerlitz-Film/`，按 textonly 拉取：89 MB 的成片、混音 m4a 和字体文件都没有拉。
- 作者在原帖里说搭建用了 90 分钟、渲染 4 小时、花了约 40 美元的云端 agent 额度（作者自述，未复现）。
- 提示词只有 847 个字符，作者在回复里公开，全文在第 5 节目录的网页上。大意是：做一支 4–5 分钟的历史影片，自己调研战役、自己决定怎么讲；要史实准确、好懂；附几幅战争油画当氛围参考，但允许另创更好的视觉语言；不要做成信息图或策略游戏的样子。也就是说，结构、引擎、配乐和配音都是模型自己定的。

**结构**：10 个场景（夜营、片名、战役背景、陷阱、晨雾、奥斯特里茨的太阳、中央高地、冰湖、战后、片尾），26 句旁白，22 个镜头。战役背景和陷阱两场各只有一个长镜头，分别是烛光下的战役地图和真实地形做成的沙盘，路线、箭头和地名按旁白逐句出现。

| 文件 | 管什么 |
|---|---|
| `web/script.js` | 旁白稿。每个场景有 `pre`（开口前的静默）、若干句 `[id, 文本, gap]` 和 `tail`；另有发音改写表 `SAY` |
| `data/timings.json` | 每句旁白的实测秒数，由 `tools/tts.py` 写出 |
| `web/film.js` | 导演层。`buildTimeline()` 把稿子和实测时长折算成场景起止；每个场景的 `shots(S)` 返回镜头列表，每个镜头是 `fn(t, tl)`，返回一份视图描述：机位、环境预设、队列、特效、叠字 |
| `web/main.js` | 渲染入口。按全局时间 T 找场景和镜头，处理镜头内溶解（`xfade`）和场景间溶解（`xin`），两路画面在后期阶段按权重混合 |
| `web/engine/` | WebGL2 引擎：地形、程序化精灵士兵、粒子、时段环境、着色器 |
| `web/events.js` | 从画面推导音效事件 |
| `tools/` | `tts.py`（Kokoro 离线配音）、`export.mjs`（导出时间线和音效事件）、`mix.py`（配乐、音效、混音、字幕）、`render.mjs`（出片）、`frames.mjs`（抽静帧） |

构建顺序是 `tts.py` → `export.mjs` → `mix.py` → `render.mjs`：先有声音，后有画面。

**旁白怎么决定镜头时间**：
1. `tts.py` 逐句合成（Kokoro，英式男声 `bm_george`，语速 0.92），去掉首尾静音，把时长写进 `timings.json`。缓存键是"音色、语速、改写后文本"的哈希，改一句只重新合成那一句。
2. `SAY` 表只改喂给 TTS 的文本（例如把 Davout 改拼成 Da-voo），字幕仍用原文，读音和字幕互不干扰。
3. `buildTimeline()` 把 `pre`、每句的实测时长加 `gap`、`tail` 依次累加，得到每个场景的起止，并记下每句旁白在场景内的起止。按现在的 timings，全片 301.35 秒，其中旁白 240.7 秒。
4. 镜头代码不写绝对秒数，而是写 `B('n2')[0] - 0.4` 这样的锚点：第二句旁白开口前 0.4 秒切到下一个镜头，再用 1.2 秒溶过去。机位关键帧、叠字淡入淡出、太阳破雾时的升降镜头也都挂在旁白起止上，例如升降镜头从 `s1` 开口前 1 秒开始，到 `s1` 说完后 1.5 秒收住。
5. 配乐读同一条时间线。`mix.py` 用 `S('sun', 's1')` 这类锚点放定音鼓和和弦转换：全片是 D 小调，太阳出来那一刻转 D 大调。所以改稿、重新合成旁白之后，画面、配乐、音效和字幕会一起移动。字幕也由这条时间线生成：每句按标点切段，每段尽量不超过 84 个字符，时长按字数比例分配。

**events.js 怎么推出音效的距离和声像**：
- 遍历每个场景的每个镜头，在镜头时间的中点取一次视图描述作为样本，从中收集两类声源。一类是特效发射器上挂的 `ev` 元数据：炮击时刻、齐射时刻（沿队列路径取位置）、落弹点、火堆。另一类是队列：奔跑或慢行的骑兵生成马蹄声床，带鼓的纵队生成鼓声，超过 20 人的行军或冲锋生成脚步声床。
- 每个事件在它发生的那一刻重新求一次机位：用 `lookAt` 得到相机的 right 和 forward 向量，取声源到相机的向量 v，距离是 |v|（世界单位是公里，乘 1000 换成米），pan = v·right / |v|，front = v·forward / |v|。镜头在动时，同一门炮在不同时刻的左右位置也不同；持续的声床（马蹄、脚步、鼓）只按镜头中点的机位算一次。
- `mix.py` 再按距离处理：延迟 `dist / 343` 秒，远处的炮先看到闪光、后听到声音；低通截止频率 `16000 / (1 + dist/120)` Hz，最低 250 Hz，模拟空气吸收；增益 `1 / (1 + dist/60)`；声像乘 0.8 后夹在 ±0.9 之内，用等功率声像律。
- 同一时刻同类的声床只保留最近的两个声源，否则几十个队列会叠成一片白噪声；同一场景的火堆合成一条声床。有一处没做完：`front` 算出来了，混音却没有用，镜头背后的声源和前方的听起来一样。
- 环境层另外撒一些远处炮声（距离随机取 1.5–5 km），随机数用固定种子 1805，每次混音结果相同。人群呼喊也来自 TTS：同一句口号用几种音色、三种语速各合成一遍，降调后随机叠 50–90 层。

**渲染和验证**：
- **出片**：页面带 `?render` 打开时暴露 `window.renderAt(T)`、`frameJPEG(T)` 和 `READY`。`render.mjs` 用 Playwright 起无头 Chromium，强制 SwiftShader 软件 WebGL2，逐帧取 JPEG，经管道喂给 ffmpeg（`image2pipe` → x264 CRF 18），每 10 秒一段。已完成的段直接跳过，没写完的段先写成 `.part.mp4` 再改名，所以可以断点续渲。最后拼接各段，封装配乐和 `mov_text` 字幕轨。README 给的速度是软件 GPU 上约 1.7 秒一帧。
- **确定性**：队列（`army.js`）和粒子（`fx.js`）都写成时间的纯函数，随机数全部来自 `hash()`。`web/` 下没有 `Math.random` 和 `Date.now`，`performance.now` 只出现在性能剖析和预览播放器里。SwiftShader 不依赖显卡，换机器渲染结果也更稳定。
- **画面**："油画感"来自后期：半分辨率的 Kuwahara 滤波（4 个象限按方差加权）按 `paint` 参数混回原图，再叠画布纹理、颗粒和暗角，上下黑边把画幅压成约 2.35:1。雾是按高度指数衰减的解析积分，再加噪声扰动；god rays 是朝太阳屏幕位置做 48 次采样的径向模糊。夜、黎明雾、日出、正午、日落等时段各是一整套光照、雾、天空和调色参数，镜头之间用 `blendEnv` 插值；太阳破雾那个镜头就是在 9 秒里从"雾中黎明"插值到"日出"。
- **事实**：地形用的是真实高程（AWS Terrarium 的 SRTM 瓦片，z13，重采样成 512 宽的网格，垂直放大 3 倍）；战役地图用 Natural Earth 的海岸线和河流。太阳按 1805 年 12 月 2 日早晨实际升起的方位摆放，从法军集结的位置看，正好在普拉岑高地背后。README 另有一节史实说明：数字取整并说明各来源有出入，也逐条列出了为画面做的简化（地形夸张三倍、军服用礼服颜色、地图单位只是示意）。
- **缺的部分**：没有自动检查。`frames.mjs` 只能按时间点手动抽静帧，`export.mjs` 只打印各类音效事件的数量。没有联系表，没有乱序一致性比对，没有用 ASR 回听配音，也没有响度标准化：混音按 99.95 百分位归一，峰值超过 0.95 时再过一道 tanh 软限幅。

**我们能借什么**（只借思路，代码自己写）：
1. **稿子就是时间线**：一份旁白稿同时是 TTS 输入、字幕来源和时间骨架；实测时长自动回写，镜头按"第几句旁白的起止加偏移"定时间，不写绝对秒数。可以对照 `playbook/04-audio.md` 的"统一的时间文件"一节。
2. **按句缓存 TTS**：缓存键包含音色、语速和文本，改一句只重合成一句。
3. **发音改写表**：TTS 文本和字幕文本分开，专有名词在表里改读音；中文的多音字、外国人名同样适用。
4. **从画面推导音效**：音效事件不手写，而是从场景里的发射器和队列导出，距离和声像由相机在那一刻的位置算出，再按 343 m/s 延迟、按距离低通和衰减。它比 lemo-opuscar 的 `window.EV` 事件表多了空间信息，适合 3D 和大场景。同类声床只保留最近的两个源，这一条也可以直接用。
5. **分段续渲**：固定时长分段，先写临时文件再改名，已完成的段跳过。长片一渲几个小时时很实用，和 claude-animation-skill"编码失败不覆盖好文件"是同一种纪律。
6. **时段预设插值**：时段和天气写成完整的参数集，镜头只做插值；光线变化本身就能讲故事，调性转换也挂在同一个旁白锚点上。
7. **史实说明的写法**：数字取整并说明来源分歧，列出为画面做的简化。对应我们的硬规则 5 和 `NOTES.md`，适合历史、科普题材的交付物。

要补上的，是我们流程里已经有的部分：联系表和逐帧 strip、乱序渲染比对（硬规则 1 的检验方法）、配音 ASR 回听、−14 LUFS 响度标准化，以及三道人工关卡。

**许可**：仓库没有 LICENSE，README 也没提许可，默认保留所有权利，只读。可以阅读，可以用自己的话转述做法；不能把它的代码、着色器或混音脚本复制进本仓库或项目。需要同类功能时，按上面的思路自己写。
