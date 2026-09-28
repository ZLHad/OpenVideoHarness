# 案例库：Opus 5.5 社区代码视频精选

**来源**：[yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)，由 `references/fetch.sh` 拉到 `references/repos/awesome-opus5-5-videos/`（本文基于 2026-09-28 的提交 `6cdcea6`）。共 389 支用 Claude Opus 5.5 写代码做出的视频，来自 362 位作者，去重后是 328 个不同的 prompt。每条有 `prompts/<slug>.md`（作者分享的 prompt，文件顶部有原帖和 Skillry 并排对比页的链接）和 `data/videos.json` 里的元数据。

**许可**：仓库没有 LICENSE，prompt 归各自作者所有，只读。我们只做三件事：链接、指向本地路径、写自己的分析。不要把原文复制进本仓库的任何文件，也不要原样贴进项目的 BRIEF。下文全部是转述，引文不超过 12 个词。

**怎么用**：

1. 做某类视频前，从第 3 节挑 2–3 条同类型的条目，打开它们的 prompt 文件，逐项对照 `templates/BRIEF.md`。看两件事：它把哪些东西写死了，而我们留给了默认值（时长、节拍、禁用清单、自查方式）；我们的 BRIEF 又多了哪些它没有的（reads、事实来源、音频时间表）。
2. 用户说"照这支做一个"时，配合 [playbook/07-reverse-engineer.md](../playbook/07-reverse-engineer.md) 使用：先从作者链接看原片拉片，再读作者的 prompt 对照。
3. 接到很短的需求时，先读第 1 节最后两条。

[community-prompts.md](community-prompts.md) 拆的是另一份二手合集；本文做的是整本目录的统计和精选。Claude Pop 和 P(doom) 的完整拆解见 [mv-claude-pop.md](mv-claude-pop.md)、[mv-pdoom.md](mv-pdoom.md)。

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
