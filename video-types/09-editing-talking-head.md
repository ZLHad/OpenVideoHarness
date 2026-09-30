# 09 写实剪辑 / 口播（真人素材，实验性）

> **实验性：本类型是 2026-10-01 根据同类项目的调研写出来的，还没有做过一支完整的片子。** 文中标【本机实测】的阈值（缺口、字级对账、FCPXML 帧对齐……）**只在合成材料上标定过**：macOS `say` 合成的中文语音加噪声、手写的字符串、手写的 EDL。没有用真人口播素材试过，也没有在 Final Cut Pro、Resolve、Premiere、CapCut、剪映里导入过导出的文件。当起点用，拿第一批真实素材校准后再回来改这里。
>
> 下文提到的缺口测量、逐接缝指标、重转写对账、EDL 审阅页、EDL 到 HyperFrames 的编译器**都还没有实现**（顺序见"建议的落地顺序"）：现在按各节写的算法自己做。已经有的是 HyperFrames 的 `transcript-cut.mjs`，以及本仓库的 `bin/vh qa`、`bin/vh sheet`、`bin/vh check`、`bin/vh mix`。
>
> 标记：【本机实测】在本机（macOS 15、ffmpeg 8.0.1、numpy）跑过；【二手】没能读到原文；【推测】没有证据的推断。引用编号 `[n]` 见文末"来源"。依据是 2026-09-30 对同类项目的调研，这次把相关仓库的源码重新读了一遍，重新核对了阈值。

**适用**：
- 用户自己录的口播、访谈、Vlog、播客视频，要剪干净、加字幕、加图解、出竖屏版；
- 多条素材（主机位、录屏、B-roll）剪成一条；
- 单人口播为主，轻对谈次之。

**不适用**：
- 没有真人素材、要生成人物：走 `playbook/05-hybrid-genvideo.md`；
- 用历史影像剪纪录片：05 的"边界"一节；
- 多机位、影视调色、复杂音频修复：导出 FCPXML 或 OTIO 交给 NLE（本篇"导出"一节）；
- 素材里有他人出镜却没有授权，或用户不能说明来源。

**素材是用户的脸和声音**：转写默认在本机做；要把音频传给云端 ASR 或把视频传给云端评审，先问用户，在 BRIEF 里记一句；不把用户素材当参考图送给生成模型。

## 引擎

- **首选**：HyperFrames。它已经有这类剪辑需要的原语：`data-start`、`data-media-start`、`data-duration` 选取素材区间，视频静音加单独的 `<audio>`，配方里有硬切、修剪、拼接、重排、冻结、变速、缩放、裁切重构图、交叉淡化、音量淡入淡出 [1]。`bin/vh new edit <slug>` 建项目，再按交付画幅运行 `bin/vh hf-init <项目目录> portrait`（或 `landscape`）：`bin/vh new` 不会替这个类型自动初始化 HyperFrames。
- **两种接法，按素材长度和需求选**：

  | 接法 | 做法 | 什么时候选 |
  |---|---|---|
  | A 单次合成 | 编译器把 EDL 的每个区间写成一对 `<video>` 和 `<audio>`，字幕、图解、重构图都在同一个页面里，只编码一次 | 默认。画面仍是 t 的纯函数，叠层像素精确，没有中间代际损失。长素材（> 10 分钟）的抽帧耗时没测【推测】 |
  | B 先剪后包 | ffmpeg 按 EDL 出 `cut.mp4`（中间文件 CRF ≤ 14 或 ProRes），再用 `talking-head-recut` 或 `embedded-captions` 包装 | 素材很长，或只要粗剪 |

  `references/repos/hyperframes/skills/media-use/scripts/transcript-cut.mjs` 已经能做 `--remove`、`--remove-words`、`--remove-fillers`、`--cut-silence`（`--plan` 只打印保留的区间），可以当 B 的起点，也是 `quick` 档的最快路线 [1]。它默认发用量统计，先 `export DO_NOT_TRACK=1`（和 `engines/README.md` 对 HyperFrames 的要求一样）。
- **转写**：本地词级 ASR，结果缓存，保留口水词（见"口水词"一节的校准）。选项：Parakeet（英语与 25 种欧洲语言，不含中文）、whisper.cpp（99 种语言，Metal 加速）、FunASR（中文，字级时间戳）、Gemini 3.5 Transcribe（云端；目前封装在 `bin/vh tts … --align gemini` 里，给合成语音对稿用，对真人素材要另写入口）[1][2]。
- **人脸**：OpenCV 的 YuNet（MIT），5 fps [3]。
- **评审**：Gemini 直接读两段 mp4（`playbook/02` 第 6 层的用法，这里用在两两对比）。

**与硬规则的关系**：
- 规则 1：EDL 加上冻结的素材文件，使合成成为 t 的纯函数；乱序抽帧比对照常适用。
- 规则 2：切点由测量到的音频决定，时长由音频决定。
- 规则 3：EDL 审阅包就是本类的分镜。
- 规则 5：字幕照实转写，不改写原话的意思；图解里的数字照抄。
- 规则 7：ASR 和评审的 key 只从环境变量读。

## 工作流

1. **定档位和 BRIEF**：素材清单（文件、时长、帧率、是不是 VFR、分辨率、语言、说话人数）、发布平台和画幅、必须保留和必须删掉的内容、素材来源与授权、能不能用云端服务。先用大白话写一段 4–8 句的策略（结构、删什么、包装、时长），等用户确认再动剪辑（关卡 ①）。**没有确认的策略，不碰剪辑**（video-use 的规则 11 [4]）。
2. **入库**：`ffprobe` 每个源文件。手机素材常是 VFR（`r_frame_rate` 与 `avg_frame_rate` 不等），先转 CFR，否则 EDL 的帧对齐和 FCPXML 导出都会出错（timecode-agent 直接拒绝导出 VFR [5]）。抽 16 kHz 单声道音频用于测量，记录每个源文件的 sha256。色彩标签也查一遍（`playbook/02-verification.md` 的"色彩标签"）。
3. **转写**：词级、保留口水词、缓存（源文件没变就不重转）。转写后打成"短语行"视图：按 ≥ 0.5 s 的静音或换人断行，`[起-止] S0 文字`，token 约为原始 JSON 的十分之一 [4]。
4. **测量**：对每个源文件测缺口（见"用测量定切点"），得到噪声底、阈值、每个 ≥ 250 ms 的缺口。
5. **决策**：模型读短语行和缺口，写 EDL（见 EDL 一节）：选 take、删口水词、重录、假开头、场外话、无功能的重复。每处删除都带 `class` 和 `reason`。**停下来等人审 EDL**，这是关卡 ②。人批准后记下 EDL 的哈希，渲染只认这个哈希。
6. **吸附与渲染**：每个区间吸附到缺口里的能量谷，再落到帧格和过零点；留 handle；音频接缝交叉淡化 40 ms、画面硬切；一次编码。
7. **验证**：逐接缝指标、重转写对账、按播放顺序连读一遍、接缝 strip（见各节）。有问题只改受影响的区间重渲。
8. **包装**：避脸字幕、必要的重构图、图解叠层（只用真实截图或录屏）、配乐和声音。
9. **评审**：两两对比加硬伤清单；`standard` 做 1 轮，`studio` 至少 3 轮；再交人，关卡 ③。
10. **导出与交付**：`final.mp4`、`captions.srt`、`edl.json`；按需 FCPXML、OTIO、CapCut 或剪映包；素材台账和授权记录。

**档位**：
- `quick`（降档只能来自用户本人）：`transcript-cut.mjs` 自动粗剪加字幕，一张联系表，没有人工关卡；改动仍然先写成 `edl.json`，方便回溯。
- `standard`：EDL 关卡、逐接缝指标、重转写对账、1 轮两两对比。
- `studio`：再加重构图检查、至少 3 轮两两对比、导出到 NLE、人耳逐个接缝复听。

## 关键机制

### EDL

EDL 是剪辑的唯一事实来源。下面的结构综合了 video-use 的 EDL、open-edit 的 `apply-edl` 和 kinocut 的审批哈希 [4][6][7]。

```json
{
  "version": 1, "fps": 30,
  "sources": { "A": { "path": "footage/A.mov", "sha256": "…", "cfr": true, "duration": 612.4 } },
  "ranges": [
    { "id": "r01", "source": "A", "in": 2.42, "out": 6.85, "beat": "HOOK",
      "quote": "…", "reason": "最干净的一遍，在 38.46 s 的口误之前停",
      "snap": { "in": "valley", "out": "valley", "handle_in_ms": 50, "handle_out_ms": 20 },
      "seam_out": "xfade40" }
  ],
  "removed": [
    { "source": "A", "in": 6.85, "out": 9.10, "class": "retake", "text": "我觉得吧我觉得", "confidence": 0.8 }
  ],
  "approval": { "edl_sha256": "…", "approved_by": "user", "at": "…" }
}
```

规则：
- 区间吸附到帧格后再累加，总时长是各区间之和，不在秒数上累加浮点误差（open-edit 做法）[6]。
- `class` 取值：`filler`、`retake`、`false_start`、`silence`、`offscript`、`take_loser`、`process_talk`。
- **审批哈希**：人批准的是这份 EDL 的哈希；渲染前核对，不一致拒绝渲染。kinocut 对"已批准的 EDL 与时间线差异"做六项检查：审批哈希、源时间覆盖、顺序、只删批准的段、音画同映射、字幕重映射 [7]。我们至少做其中的审批哈希、只删批准的段和音画同映射。
- 源文件颜色或帧率不一致时拒绝拼接，不悄悄改标签（open-edit 做法）[6]。

### 用测量定切点

**转写里的词边界不是切点**：ASR 报出的两个词之间的空隙，波形上可能是连续发声，切下去会切断音素；词的时间戳本身还会漂移 50–100 ms [4][6]。

**起点算法**（综合几个来源 [4][6][8][9]）：
1. 16 kHz 单声道，10 ms 窗口的 RMS 包络。
2. 噪声底 = 包络的第 10 百分位；阈值 = min(噪声底 + 12 dB, 噪声底 + 0.35 × (峰值 − 噪声底))；动态范围小于 6 dB 时报告"没有语音"，不给缺口 [6]。
3. 连续低于阈值且 ≥ 250 ms 的段是安全缺口。宁可漏报一个缺口，也不要误报（误报是一次坏切，漏报只是少了一个机会）[6]。
4. **切点**取缺口里的能量谷，用 −30、−35、−40 dBFS 三个阈值各测一次边界再取中位数，避免被一个宽松阈值拉晚（cut-motion）[8]；再落到过零点（±6 ms 内）和帧格（mandarin 与 open-edit）[9][6]。
5. **留 handle**：出点之后留 20 ms，入点之前留 50 ms，不对称；handle 是保护语音的，不是要人为制造的静音 [8]。video-use 的工作窗口是 30–200 ms，示例值是首个保留词前 50 ms、最后一个保留词后 80 ms [4]。
6. **找不到缺口就不切**，保留那个口水词 [6]。缺口小于 120 ms 的句间不在此切，挪走 [9]。谷值高于 −45 dB 时警告"没有明显气口"[9]。
7. **接缝**：音频交叉淡化，画面硬切。数字各家不同：video-use 每段 30 ms 淡入淡出，open-edit 示例 40 ms，mandarin 60 ms，cut-motion 是 0–2 帧（30 fps），并且只有在起音和尾音审计通过时才用 [4][6][9][8]。起点取 40 ms。
8. **按缺口长度分类**（video-use）：≥ 400 ms 通常最干净；150–400 ms 的短语边界要配合画面检查；< 150 ms 不安全 [4]。

**画面证据**（cut-motion 的"表现力分类"）：音频缺口只说明声音停了。保留一个停顿要看它是不是思考或强调的一部分：视线还在镜头上、呼吸是连续表达的一部分，就留；视线离开镜头去看稿、嘴型停了在找下一句、头和躯干在"复位"、下一句像重新开始，就删。证据冲突时留 50–120 ms 并标低置信度，只把这个接缝提给人看 [8]。被删的 reset 和失败重来接缝，残留静音不超过 80 ms；保留的自然停顿超过 180 ms 时，附一张胶片条加波形的诊断图 [8]。

**【本机实测】**（合成材料）：用 macOS 的 `say` 合成 5 句中文，句间插入 300、120、600、180 ms 的已知停顿，叠一层峰值约 −42 dBFS 的粉红噪声当房间底噪，共 18.7 s，用上面第 1–3 步的算法测缺口。`gap = 250 ms` 时，两个长停顿检出 340 和 650 ms（插入的是 300 和 600；合成语音句尾自带一点静音，所以比插入值长 40–50 ms）；改成 `gap = 100 ms` 后，再检出 170 和 240 ms 两个（插入的是 120 和 180）。所有插入的停顿都找到了，没有漏报。句内的逗号处也检出约 310–320 ms 的缺口，这是正常的短语边界；片头片尾的静音也会被当成缺口。这是合成语音，不是真人口播的结论。

### 口水词、重录与中文规则

**先校准 ASR 会不会保留口水词**。Whisper 系倾向省略 um、uh 这类词，给它一个带口水词的提示能让它更愿意写出来，但也更容易幻觉出没说过的词 [10]；video-use 直接不建议用本机 Whisper，改用云端逐字转写 [4]；mandarin 用火山的录音识别，并显式关掉"语义顺滑"（`enable_ddc: false`）以保留语气词 [9]；CrisperWhisper 专为逐字和准确时间戳训练，但只保证英语和德语，许可证是 CC-BY-NC，中文不能用 [10]。所以**每个 ASR 候选都先跑一遍标定样本**：录 15 秒带已知"嗯、呃、这个、我觉得吧我觉得"的话，看它写不写出来，结果记进 `LOCAL.md`。没有标定就不要承诺"自动删口水词"。ASR 不转写的单字口水词，只能靠缺口和回听处理，diff 也看不到（见"重转写对账"）。

**中文规则**（来源 mandarin-talking-head-rough-cut，Apache-2.0；以下是意思相同的转述，不是原文）[9]：

| 类别 | 规则 |
|---|---|
| 词表只是线索 | 嗯、啊、呃、哦、唉、这个、那个、就是说、然后呢、对吧、你知道吧、怎么说呢、其实呢、就是那个、这样子。**看语境删大部分，留少量保人味**；同一短段连着好几个就留一个，全删像机器念稿 |
| 这个、那个 | 后面紧跟名词时是实词（"这个方法"），不能删 |
| 句首的对、然后、那、其实、就是、所以、但是 | 不按词表机械处理。**承接测试**：分别连读"上一句 + 原句"和"上一句 + 删掉短词后的句子"，后者更直接且不损失逻辑才删。例："接下来怎么安排？对，先把素材按主题分类……"里的"对"没有承接作用，应删 |
| 磕巴重复 | 相邻两个短语意思几乎一样，**留后一遍，删前一遍**（"我觉得吧…我觉得这个事儿"删前半）。前一遍若带着后一遍需要的主语或连接词，只清磕巴，留骨架 |
| 假开头 | 说一半重来，删没说完的半截，留完整版。信号词：不对、等下、我重说、又讲偏了。**ASR 可能把口头的"不对"听成"对"**，出现无法解释的搭配（如"英语对录播课"）时回听，把错误起头和纠错词一起删 |
| 自我否定的范围 | 只作用于它直接指向的未完成分句，向前遇到已经完整成立的内容就停止扩大删除 |
| 停顿 | 纯空白拖沓、卡壳的尴尬停顿删；斟酌措辞、动情处的短停顿留 |
| 场外提示 | "再来一遍、刚才那句不行"表示前一个 take 作废：先读信号，再删提示，**并且删掉它判废的旧 take** |
| 信息覆盖门 | 整句删除前回答：被删句有哪些独有信息？保留句是否逐项覆盖？两句主题相同不等于信息重复；抽象观点和具体案例、信息来源和结论通常功能不同，要都留 |
| 不碰的东西 | 限定词（可能、大概、部分）不删，以免把审慎的话剪成绝对结论；不补写主讲人没说过的话；不通过改字幕掩盖原声错误；ASR 的错字记进 `corrections.json`，不据此删原声 |
| 拿不准 | 留下并标 `%待确认：理由%`。漏删可以复核，误删可能改变事实与信任 |
| 带货和引流口播 | 检查广告法绝对化用语（最好、最佳、最强、第一、顶级、绝对、100%、根治、永久、最低价、独家、唯一等）：优先保留现场已经重录的合规版；没有就删违规词或整句，删后重做承接测试；无法安全处理时停下来问用户，**不改写原声** |
| 完成后通读 | 按观众实际听到的顺序连读一遍。重点查句首悬空的这、那、他、它、所以、但是、而且、然后、因为、于是（`review_readthrough.py` 对这些词自动预警）[9] |

**英文口水词**：um、uh、like、you know 等，同样先标定再删，`transcript-cut.mjs` 的 `--remove-fillers` 按词表删 [1]。

**剪的是结构，不是时长**：不要用目标时长或删减比例倒推要删什么，时长和比例只是完成后的统计 [9]。开头找真正的话头（设问、观点、现象、结果前置），结果前置不能改变原句的条件，也不能把后文才建立的指代一起搬到开头；结尾要收束，结论之后的"好了、过了吗"删掉 [9]。

### 重转写对账

**核心是比词序，不比时间**。proofcut 的发现：Whisper 会把紧挨着的重录吞进相邻词的时长里，时间戳证明不了重录被删了，但重转写出来的文本里那句话会出现两次，而 EDL 期望的序列里只有一次 [11]。

- **英文起点值**（proofcut，PolyForm Shield，只借思路）：用 `difflib` 对词序列做 diff；多出来的片段至少 2 个词才算（单词多半是某一遍转写出来的口水词）；与期望序列的相似度 ≥ 0.5 判为残留重录（0.5 是因为第二遍总是被转写得更差）；干净的成片整体相似度约 0.97；相邻重复检测要求片段 ≥ 4 个词，向前看 40 个词，与期望重复的吻合度 ≥ 0.75 才算是 EDL 自己留的重复 [11]。
- **中文要改成字级**：中文没有空格分词，token 取汉字，去掉标点，阿拉伯数字转汉字（避免"30"与"三十"的逆文本规整差异）。**【本机实测】**（合成字符串）起点值 `MIN_RUN = 4` 字、`SIMILAR = 0.5`、`ADJ_MIN = 6` 字、`ADJ_LOOK = 60` 字，用 `difflib.SequenceMatcher` 对字符序列做 diff。在 5 个合成字符串上：

  | 情形 | 相似度 | 结果 |
  |---|---|---|
  | 干净（ASR 把"三十"写成"30"） | 0.982 | 无提示 |
  | 残留重录（整句多说一遍） | 0.887 | 多出的 14 字被判"残留重录？" |
  | 残留假开头（"我觉得吧我觉得"） | 0.94 | 被判"期望里没有的插入" |
  | 删过头（少了一句） | 0.854 | 报出缺失的 14 字 |
  | 单字口水词"嗯" | 0.991 | **不会被 diff 发现**，需要口水词表计数 |

  这些阈值是在合成字符串上得到的，换真实 ASR 要重新校准【推测】。相邻重复检测对重叠片段会多报，取不重叠的最强候选。
- **与 open-edit 的"不要重转写成片"不矛盾**：open-edit 的 `retime-transcript` 按 EDL 平移已有的词时间，不再付一次 ASR，用来生成字幕时间；跨在切点上的词，只有超过一半落在保留区间内才留下 [6]。重转写是**独立的验证**，用本地 ASR 转成片的音轨，不用付费的那个。两件事都做：retime 给字幕，重转写给验证。
- **逐接缝指标**（timecode-agent，MIT）：切在词内（`word_interior`）；词尾余量小于 0.12 s 而缺口本来足够（`tight_tail`）；接缝两侧 RMS 差超过 12 dB（`loud_step`）；接缝两侧画面的 SSIM 超过 0.75，说明是同机位跳切，需要遮盖 [5]。这些只出旗标，取舍由 agent 决定。

### 两两对比评审

`playbook/02` 现在的打分层是绝对分数（7 项，每项 ≥ 8）。SeeCut 做过校准实验：绝对打分下，"假满屏"的坏版本和参考原片同分；改成两两对比后，判断与人一致 [12]。所以本类**在绝对打分层之上，用两两对比决定"新版能不能取代当前版"**，绝对 rubric 保留为硬伤清单，不求和。

流程（SeeCut 的做法，PolyForm NC，只借思路）[12]：
1. 对手是**当前采纳版**（不一定是上一版）。第一版没有对手时，用 `auto-editor` 或 `transcript-cut.mjs` 出一个笨办法的粗剪当基线【推测：这是我们的补充】。
2. **A/B 交换位置各跑一次**，两次都判新版赢才采纳。结论不一致算平手。**跑失败算"对比没有发生"，不算输，也不算赢**，也不能按"没输"交付。LLM 评委有位置偏好 [13]，交换位置是标准缓解办法。
3. **防编造**：要求评委照抄画面上 3 处文字并报出视频时长，脚本核对源码里至少命中 2 处、时长误差 ≤ 3 s，不过就判"无效"，重跑一次。
4. **评委隔离**：把视频复制到项目目录之外再交给评委，不让它读到项目源文件；每次新开会话。
5. **评委报的每条 FAIL，必须打开它标的那一秒的帧去核实**；判误报要写清时间和看的帧。评委有"把相邻两拍当同屏"的毛病。
6. **盲区**：两两对比会被"更满但是假"的版本骗过（SeeCut 实测干净版输给假满屏版）。所以"假证据"由硬门禁直接拒绝，不指望评委扣分。

**本类的评审维度**（建议）：话头与钩子、承接与逻辑连续、节奏与接缝自然度、字幕与构图、画面证据真实性、声音（响度、人声清晰）、整体像不像本人自然说话。

### 重构图

- **算账**：1920×1080 横屏取 9:16，裁出 608×1080，再放大到 1080×1920，放大 1.78 倍，会发软；4K 横屏源文件裁出 1215×2160，缩到 1080×1920 是缩小，画质没有损失。所以**竖屏成片优先用 4K 源**，或接受 1080p 源的发软，并在交付说明里写明。
- **规划器**（kinocut，Apache-2.0）：用人脸或主体追踪的轨迹，裁剪窗口中心每个采样点最多移动 0.10（归一化），追踪置信度低于 0.70、丢失目标、多人歧义、超出裁剪预算时**放弃裁剪（abstain），不硬裁**；多人对话按说话人切换主体 [7]。
- **追踪**：YuNet，5 fps [3]。
- **在 HyperFrames 里**：把平滑后的轨迹写成分段线性表，`cropX(t)`、`scale(t)` 作用在 `<video>` 的 CSS transform 上，仍是 t 的纯函数；换说话人时硬切，不平移。
- **遮盖跳切**：同机位跳切可以在每个切点和多数句首打 1.0 与 1.1 交替的 snap zoom（ghost-editor 的做法 [3]）。这是一种风格，不是必须：`clean` 风格每句一次，过度使用会显得廉价。
- **验证**：挑头部动作最大的 5 个时刻出 strip；眼睛大致落在上三分线，脸不被裁。

### 避脸字幕

**竖屏平台 UI 遮挡**（1080×1920，ghost-editor 实测值）[3]：

| 平台 | 上 | 下 | 右 |
|---|---|---|---|
| Instagram Reels | 220 | 420 | 130 |
| TikTok | 160 | 480 | 150 |
| YouTube Shorts | 140 | 380 | 140 |
| 三者并集 | 220 | 480 | 150 |

抖音、小红书、视频号、B站没有这样的实测值，**沿用 02 篇的安全框**（关键内容 x 90–900、y 330–1520）【推测】。

**放置顺序**（ghost-editor，MIT）[3]：
1. 下巴以下（自然的阅读位置），理想高度 1180 px，与下巴的间隙 36 px；
2. 放不下，头顶以上、顶栏以下；
3. 头顶上方只剩一条缝，缩小字幕（最多缩到 70%），不压胡子；
4. 最后手段：嘴以下，垫深色底，绝不盖住眼和嘴；
5. 都放不下，这一拍改成整屏卡片，不硬放。

**稳定性**：区域锁定（上一块字幕还放得下就留在同一区域），位移小于 70 px 不动（滞回）；人脸框按字幕存在期每 0.1 s 取样，换算到镜头缩放之后的屏幕坐标；短暂丢脸时沿用上一次位置，最多 1.5 s [3]。

**中文字幕切分**（cut-motion，Apache-2.0，转述）[14]：
- 每条字幕一行，不拆成两行；
- 每条至少 0.5 s，目标 0.8–2.5 s；显示宽度 4–10.5 个单位（个别可到 11.8，但要在该条上缩字号到 88–96 px，不整体缩小）；
- 禁止单字成条；的、了、着、过、啊、吧、吗、呢、与、和、但、所以、因为、而不能单独成条；
- 专名、产品名、数字加单位、固定短语不能跨条；
- 所有条拼起来必须还原审定稿；
- 措辞的优先级：录音与表现 > 用户提供的参考稿 > ASR；断句由 agent 按语义写，**不让代码按字数硬切**。

**层级**：字幕最后叠（video-use 的规则 1），避免被图解盖住 [4]。字号、强调色、安全框沿用 02 篇。

### B-roll 与图解素材

- 先给每句话定功能（对你说、给你看、给数字、给证据），再定人像露不露、信息层放什么（见"审美要点"里的 SeeCut 决策表）。
- 挑 B-roll 不要把整条素材丢给模型：按约 10 s 一个窗口给素材写画面描述，再按这句话讲的内容挑窗口（proofcut 的 `describe` 思路）[11]。
- 扫描素材出联系表：2 fps 取样，只在画面稳定到新状态时才取一帧，单张联系表不超过 2576×1456、最多 12 格（diffusionstudio，MPL-2.0，只借思路；【二手：来自调研摘要，这次没有重读源码】）。
- 证据只用真实截图、录屏、数字；素材没有的就先去截，不自己造（和 03 篇一致）。

### 导出：FCPXML、OTIO、CapCut 与剪映

| 目标 | 做法 | 状态和注意 |
|---|---|---|
| 成片 | mp4，H.264，BT.709 tv 四个标签齐全（命令见 `playbook/02-verification.md` 的"色彩标签"） | 响度、黑场等走 `bin/vh check` |
| 字幕 | SRT（按 retime 后的词时间生成）加 `captions.json` | — |
| 我们自己的 EDL | `edl.json` | 是唯一事实来源 |
| Final Cut Pro、DaVinci Resolve | FCPXML：`asset-clip` 放在 `spine` 上，所有时间是帧时长的整数倍（有理数，NTSC 用 1001/30000 这样的精确值），只接受 CFR 素材 | **默认写 1.10**：FCP 10.8.1 用 1.12，FCP 11 用 1.13，FCP 12 用 1.14 [15]；新版通常能读旧版，FCP 会拒绝它不认识的更新版本【二手】；Resolve 19.1 读 1.3–1.10，据报 1.11 也可【二手】。**没有在 FCP 或 Resolve 里导入过，【未验证导入】** |
| Premiere Pro、Resolve、通用 | OTIO：Premiere Pro 的 OTIO 导入导出 2024-10 进入 beta，正式版据报在 26.0（2026-01）【二手】；Resolve 自 18 起原生支持 .otio 和 .otioz；OTIO 官方 wiki 的原生支持列表里没有 Final Cut Pro，FCP 走 FCPXML。Premiere 支持的内容：名称、剪辑表、入出点、起始时码、帧率、多轨、线性变速、标记；外部生成的 OTIO 导入后，部分序列设置要手动调整 [16] | 最中立，首选给不知道用哪款 NLE 的用户 |
| 只有简单剪切 | `auto-editor --export <目标>`，目标有 premiere、resolve、final-cut-pro、shotcut、kdenlive、clip-sequence（Unlicense）[17] | 只适合静音或音量阈值剪切 |
| **CapCut（国际版）** | 草稿是明文 JSON，`capcut-cli`（MIT）能读写；6.2.8 有 fixture 测试，6.5–9.x 只是预期兼容，10.x 有"内容已损坏"的报告，写入默认被护栏拦下 [18] | 实验性。导出前核对用户的版本，先用一个 2 秒样例验证 |
| **剪映（国内版）** | **6.0 起 `draft_content.json` 是 AES 加密的二进制**，5.9.x 是最后广泛使用的明文版本；`capcut-cli` 只检测、不解密，对 6.0+ 的写入默认拒绝 [18]。`pyJianYingDraft`（Apache-2.0）声明支持 5.9+、测到 10.8，导出在 5.9 和 6.8 上测过，但 10.x 有草稿被判损坏的 issue [19] | **不要承诺"一键导出剪映草稿"**。稳妥的交付是：`final.mp4` + `captions.srt` + 分层素材包（透明 PNG、音频、时间表），用户手动拖入。剪映不接收带透明通道的视频，叠层只能用 PNG 加淡入淡出，所以成片和素材包要分别交付 [20] |

**FCPXML 的骨架**：每个区间的入点、出点**先各自取整到帧**，`offset` 用前面各段帧数的累加，**不要**把秒数加起来最后再取整：后一种做法在区间不是整帧时，会在 spine 里留下 1 帧的缝或重叠（本机用 8 个 0.51 s 的区间在 29.97 fps 下试出来：8 个里有 2 处错位）。取整在帧上做之后，6 种帧率（24、23.976、25、29.97、30、59.94）下都是格式良好、所有时间是帧时长的整数倍、spine 首尾相接、序列时长等于各段之和【本机实测，合成 EDL，没有导入过 NLE】。29.97 fps、两个区间（2.42–6.85 s 和 14.30–28.90 s）生成的骨架：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
 <resources>
  <format id="r1" frameDuration="1001/30000s" width="1920" height="1080"/>
  <asset id="r2" name="edit" start="0s" duration="3599596/30000s" hasVideo="1" hasAudio="1" format="r1">
   <media-rep kind="original-media" src="file:///Users/me/footage/A.mp4"/>
  </asset>
 </resources>
 <library>
  <event name="vh">
   <project name="edit">
    <sequence format="r1" duration="569569/30000s" tcStart="0s">
     <spine>
      <asset-clip ref="r2" offset="0/30000s" start="73073/30000s" duration="132132/30000s" name="r01" format="r1"/>
      <asset-clip ref="r2" offset="132132/30000s" start="429429/30000s" duration="437437/30000s" name="r02" format="r1"/>
     </spine>
    </sequence>
   </project>
  </event>
 </library>
</fcpxml>
```

**单向**：导出之后用户在 NLE 里做的修改不回读，不把 NLE 当事实来源。

## 审美要点

- **剪的是有效内容**：每段要么增加观点、证据、例子、步骤，要么承担承接；只是换个说法原地重复的删掉 [9]。
- **起点参数**（都是起点，不是规定）：

  | 项 | 起点 | 来源 |
  |---|---|---|
  | 切点留白 | 入点前 50 ms、出点后 20 ms；或 30–200 ms 窗口 | cut-motion、video-use [8][4] |
  | 被删的重来接缝残留静音 | ≤ 80 ms | cut-motion [8] |
  | 保留的自然停顿 | > 180 ms 要有画面证据 | cut-motion [8] |
  | 说话人交接 | 400–600 ms 留气，快节奏更短，文艺更长 | video-use [4] |
  | 音频接缝 | 40 ms 交叉淡化，画面硬切 | 综合 [4][6][9] |
  | 峰值保留 | 笑声、强调、包袱之后多留一拍反应 | video-use [4] |

- **"对你说"就露脸，"给你看"就藏**：观点、收尾、建立信任这类句子，说话人露出来；演示、列举、给证据的句子，说话人缩小或隐去，信息层当主角。SeeCut 的统计（8 个参考片、536 拍）是演示类 77% 隐去人像、收尾 70% 露半身，样本小、没有复现，当作方向，不当规则【二手】[12]。
- **图解只用真实证据**：真实网页截图、真实录屏、真实数字；不用假 UI、假数据占位（和 03 篇一致，也是硬规则 5）。
- **保持人味**：口头禅删大部分留少量，保留笑声和自然呼吸；剪完要让主讲人看了觉得"这是我实际说过的意思"[9]。
- **字幕**：沿用 02 篇（单行、一个强调色、每句强调 1–2 个词），加上避脸与中文切分。
- **声音**：响度 −14 LUFS，配乐垫在人声之下，用 `bin/vh mix` 的 duck。音效按可见事件挂，不每次转场都来一个（video-use 的经验：18 秒里 20 个音效像素材库，8 个才像设计过）[4]。

## 禁止

- 切在词内；只按 ASR 的词边界切，不测量音频；
- 找不到缺口还硬切；
- 机械地删光所有口水词和"这个、那个、然后"；
- 改写主讲人的观点，删掉限定词把话说绝对，补写没说过的话，拼出他没表达过的新论点；
- 用改字幕的办法掩盖原声的口误；
- 每一刀都加缩放；一句一个新元素；
- 字幕盖住脸、落进平台 UI 遮挡区；
- 把字幕先烧进底片再叠图解（被盖住）；单次滤镜链里既做剪辑又做叠层（多次代际编码）；
- 假 UI、占位文字、编造的数字或引语；
- 未确认策略就动剪辑；未经批准的 EDL 就渲染；
- 用户素材未经同意传到云端；
- 承诺"一键导出剪映草稿"。

## Prompt 增量块

```text
+ TYPE: talking-head / real-footage edit. Sources: {files, duration, CFR fps, resolution, language zh-CN}. Deliver {1080x1920 | 1920x1080} {30}fps {45–90}s + captions.srt + edl.json {+ FCPXML 1.10 | OTIO}. Platform: {抖音 | 小红书 | 视频号 | B站 | Shorts}.
Strategy first: write a 4–8 sentence plain-language plan (structure, what goes, packaging, length) and wait for approval before touching the cut.
Cut from MEASURED audio, never from ASR word times: noise floor = p10 of a 10 ms RMS envelope, speech threshold = min(floor+12 dB, floor+0.35*(peak-floor)); cut only inside gaps >=250 ms; snap to the energy valley (median of the -30/-35/-40 dBFS boundaries), then zero-crossing and the frame grid; handles 50 ms in / 20 ms out; 40 ms audio crossfade, hard picture cut. No gap at a boundary: keep the word.
Transcribe verbatim with fillers (calibrate the ASR on a known filler sample first). Remove recording chatter, false starts, failed takes, repeated phrases (keep the later clean one), dead air. Keep qualifiers (可能/大概/部分), a few natural fillers and breaths, information-bearing repeats. Every deletion must pass the read-through test (previous sentence + next sentence read aloud); a leading 对/然后/所以 is judged by context, not by list; 这个/那个 before a noun is a content word. Never rewrite the speaker or add words.
Write edl.json (sources with sha256; ranges with beat/quote/reason/snap; removed with class/text/confidence) and STOP for approval; render only from the approved hash.
Captions: one line; Chinese cue >=0.5 s, 4–10.5 display units, no function word alone, names and number+unit never split; face-safe placement (below chin > above head > shrink to 70% > under mouth; else a full-screen card), inside the platform safe area; captions on the top layer.
Reframe 16:9->9:16 from a face track (YuNet, 5 fps), centre step <=0.10 per sample, abstain on low confidence or several people; say so when the source is only 1080p.
Overlays only from real screenshots or recordings; no invented UI, numbers or quotes.
Verify before showing: per-seam metrics (cut inside word, tail gap <0.12 s, RMS step >12 dB, SSIM>0.75 = same-camera jump cut); re-transcribe the render and diff word order against the EDL; pairwise review against the current accepted cut with A/B swapped (both must win; a failed comparison is not a win).
```

## 自查重点

- 有没有切在词内？每个接缝有没有测量证据（缺口、谷值、handle）？找不到缺口的地方有没有保留原词？
- 按播放顺序连读成片稿：有没有悬空的这、那、他、它、所以、但是？有没有限定词被删成绝对结论？
- 重转写对账：重转写对 EDL 的词序 diff 有没有残留重录或"期望里没有的插入"？单字口水词有没有用词表计数？
- 渲染用的 EDL 哈希与批准的哈希一致吗？有没有只删批准的段？
- 前 3 秒是不是真正的话头（设问、观点、现象、结果前置），而不是试麦或找状态？
- 字幕有没有盖脸、进遮挡区？一行能读完吗？每条 ≥ 0.5 s？名字和数字加单位有没有被拆开？
- 图解里的每个画面都对应真实截图、录屏或数字吗？素材台账里有吗？
- 接缝：画面跳变（同机位跳切有没有遮盖）、音频爆音、两侧响度差；联系表加接缝 strip（每个切点前后 0.3 s）。
- 竖屏版：裁切有没有切掉脸或手势？源是不是 1080p 而有发软？
- 响度 −14 LUFS、真峰值、黑场、冻结、静音都过了吗（`bin/vh check`、`bin/vh qa`）？
- 导出文件在目标软件里打开过吗？版本是不是写进了交付说明？
- 两两对比有没有"没有发生"的情况被当成通过？评委报的每条 FAIL 看过它标的那一秒吗？
- 用户素材有没有在未同意的情况下离开本机？

## 可参考的案例与源码

**已在本仓库**：
- `references/repos/hyperframes/skills/media-use/`：`scripts/transcript-cut.mjs`（`--remove`、`--remove-words`、`--remove-fillers`、`--cut-silence`、`--plan`）、`references/operations.md`（转写、剪切、响度）[1]。
- `references/repos/hyperframes/skills/talking-head-recut/`：在不改动素材的前提下叠图解卡片，本类包装阶段的现成流程；不剪片。
- `references/repos/hyperframes/skills/embedded-captions/`：本地转写、主体抠像、字幕绕到人物身后、安全区；`references/` 下有 `aesthetic-principles.md`、`anti-patterns.md`、`caption-grouping.md`、`layout-heuristics.md`。
- `references/repos/hyperframes/skills/hyperframes-core/references/creator-editing-recipes.md`：硬切、修剪、拼接、重排、冻结、变速、缩放、裁切、交叉淡化、音量淡入淡出的 HTML 写法。
- `references/repos/video-talkcraft/`（PolyForm NC，只读）：真人录音先预剪再做时间戳；以稿子为真值，ASR 听错的字不剪。
- `cases/community-prompts.md`：@AxtonLiu 的口播图解做法。

**尚未拉取**：下面"社区 skill 参考"里的 video-use、open-edit、cut-motion、kinocut、timecode-agent、ghost-editor、SeeCut 还没有进 `references/fetch.sh`；本文依据 2026-09-30 的调研和这次对它们源码的重读（浅克隆在调研目录，不在本仓库）。

## 社区 skill 参考

以下选自 2026-09-30 的调研，许可证按仓库里的 LICENSE 核对。只读参考；复用代码前按 `references/community-skills.md` 的规则处理。

- **video-use**（browser-use，MIT）：EDL、短语视图、12 条硬规则（字幕最后叠、按段提取再无损拼接、每个接缝 30 ms 淡入淡出、绝不在词内切、缓存转写等）、渲染后在每个切点 ±1.5 s 自检、最多 3 轮 [4]。它偏好云端逐字 ASR，与我们"本地优先"的取向不同。
- **open-edit**（veedstudio，Apache-2.0）：`speech-probe`、`apply-edl`（单次编码、帧格吸附、拒绝颜色或帧率不一致的源）、`retime-transcript` [6]。
- **cut-motion**（Endless1936，Apache-2.0）：`tight-talking-head` 的三阈值中位数边界、不对称 handle、画面证据分类；中文字幕切分标准 [8][14]。
- **kinocut**（KyaniteLabs，Apache-2.0）：语义 EDL 与审批哈希、`verify_timeline_diff` 六项检查、重构图规划器 [7]。
- **timecode-agent**（mupozg823，MIT）：接缝指标、FCPXML 与 OTIO 导出、CFR 证明 [5]。
- **ghost-editor**（kurbaitaev，MIT）：避脸字幕放置、平台遮挡像素、YuNet 追踪、snap zoom [3]。
- **mandarin-talking-head-rough-cut**（m15851855393-boop，Apache-2.0）：口水词与重录规则、能量谷吸附、承接测试与通读脚本；它的 ASR 走火山云，我们不用那一段 [9]。
- **proofcut**（tydude001，PolyForm Shield，只借思路）：重转写词序对账 [11]。
- **SeeCut**（YeJe-cpu，PolyForm NC，只借思路）：两两对比评委、功能到打法的决策表、剪映分层交付 [12][20]。
- **clipify**（louisedesadeleer，MIT）：按说话人生成 ffmpeg 的 crop x 表达式，说话人切换时硬切。**doza-assist**（DozaVisuals，MIT）：从用户自己剪完的作品里学剪辑风格（停顿、开头、soundbite），本机运行，导出 FCP、Premiere、Resolve，可以并进 `playbook/07`。
- **auto-editor**（Unlicense）：静音剪切与多 NLE 导出 [17]。**capcut-cli**（MIT）、**pyJianYingDraft**（Apache-2.0）：CapCut 与剪映草稿 [18][19]。**fcp-mcp-server**（MIT）：`rational.py` 的有理数帧率（23.976 → 24000/1001）。

## 建议的落地顺序

下面这些工具现在都不存在：

1. 本地词级 ASR + 口水词标定 + 短语视图。
2. 缺口测量（"用测量定切点"的算法做成命令）+ EDL 结构、审批哈希、EDL 审阅页（文本 diff、时间、理由、样本片段）。
3. EDL → HyperFrames 合成的编译器（`data-media-start` 那一套）+ retime 生成字幕。
4. 逐接缝指标、重转写对账（中文字级）、通读脚本、两两对比评委。
5. 避脸字幕与中文切分、重构图。
6. 导出：SRT、FCPXML 1.10、OTIO；CapCut 作为实验性选项。

## 待验证与待决策

**要验证的**
1. 候选 ASR 对中文口水词的保留情况；本地中文模型的字级时间戳精度。
2. 接法 A 在长素材上的抽帧耗时和内存。
3. FCPXML 与 OTIO 在 FCP 12、Resolve 20、Premiere 26 里的实际导入。
4. CapCut 与剪映的具体版本行为（用户手上的版本）。
5. 重转写对账的阈值在真实 ASR 输出上的表现。
6. 抖音、小红书、视频号的 UI 遮挡像素。
7. 两两对比评委在剪辑任务上的稳定性，以及"笨办法粗剪"当基线是否有区分度。
8. 缺口测量的阈值在真人口播（有呼吸、口腔音、房间混响）上的表现。

**维护者待定**
1. 评委是否用 Gemini 云端读成片（涉及用户素材离开本机）。
2. 是否把"两两对比"推广到所有类型（调研里提到的影响面），还是先只在 09 试。
3. `video-types/09` 与 `talking-head-recut`、`embedded-captions` 的边界：本类管"剪"，它们管"包装"。

## 来源

- [1] 本仓库 `references/repos/hyperframes/skills/`：`media-use/references/operations.md`、`media-use/scripts/transcript-cut.mjs`（选项和用量统计 2026-10-01 重读）、`hyperframes-core/references/creator-editing-recipes.md`、`tracks-and-clips.md`、`variables-and-media.md`、`talking-head-recut/SKILL.md`、`embedded-captions/SKILL.md`。
- [2] 本仓库 `playbook/04-audio.md`（`--align gemini`、FunASR、whisper.cpp）。
- [3] ghost-editor（MIT）：`scripts/lib/safezone.mjs`、`scripts/face_track.py`、`docs/HOW-IT-WORKS.md`，https://github.com/kurbaitaev/ghost-editor 。
- [4] video-use（MIT）：`SKILL.md`，https://github.com/browser-use/video-use （调研浅克隆 2026-09-23 的提交）。
- [5] timecode-agent（MIT）：`src/video_agent/boundary_eval.py`、`export.py`，https://github.com/mupozg823/timecode-agent 。
- [6] open-edit（Apache-2.0）：`cli/src/commands/speech-probe.ts`、`.claude/skills/open-edit/CUT.md`，https://github.com/veedstudio/open-edit 。
- [7] kinocut（Apache-2.0）：`kinocut/semantic/edl.py`、`kinocut/visual_intelligence/reframe.py`，https://github.com/KyaniteLabs/kinocut 。
- [8] cut-motion（Apache-2.0）：`docs/talking-head-trim-standard.md`，https://github.com/Endless1936/cut-motion 。
- [9] mandarin-talking-head-rough-cut（Apache-2.0）：`references/filler_rules.md`、`editing_rules.md`、`koubo_logic.md`、`scripts/snap_cuts.py`、`scripts/review_readthrough.py`、`scripts/transcribe_volc.py`，https://github.com/m15851855393-boop/mandarin-talking-head-rough-cut 。
- [10] CrisperWhisper：https://huggingface.co/nyralabs/CrisperWhisper （CC-BY-NC-4.0，只保证英语和德语）；论文 https://arxiv.org/pdf/2408.16589 ；Whisper 对口水词的倾向见 Interspeech 2024 论文 https://www.isca-archive.org/interspeech_2024/zusag24_interspeech.pdf 【二手，搜索摘要】。
- [11] proofcut（PolyForm Shield，只借思路）：`src/proofcut/verify.py`，https://github.com/tydude001/proofcut 。
- [12] SeeCut（PolyForm NC，只借思路）：`skill/seecut/references/06-质检闭环spec.md`、`03-编排层决策表.md`，https://github.com/YeJe-cpu/SeeCut 。
- [13] Zheng L. 等，"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"，NeurIPS 2023，DOI 10.52202/075280-2020，arXiv 2306.05685（讨论了位置、冗长和自我偏好偏差，Crossref 与 arXiv 核对）。
- [14] cut-motion：`docs/subtitle-segmentation-standard.md`（同 [8] 仓库）。
- [15] FCPXML 版本：FCP 与 FCPXML 的对应（10.8.1 → 1.12、11.0 → 1.13、12.0 → 1.14）见 https://fcp.cafe/update-guide/ ；Resolve 19.1 读 1.3–1.10、旧版优于新版的说法来自 Blackmagic 论坛搜索摘要（页面 403）https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=212391 【二手，以实际导入为准】。
- [16] OTIO：Adobe 社区的 beta 公告 https://community.adobe.com/t5/premiere-pro-beta-discussions/now-in-beta-otio-import-and-export/td-p/14937493 （2024-10-23，支持的数据和限制）；原生支持列表 https://github.com/AcademySoftwareFoundation/OpenTimelineIO/wiki/Tools-and-Projects-Using-OpenTimelineIO （Resolve 18 起；没有 FCP）；Premiere 26.0 正式版的说法来自搜索摘要【二手】。
- [17] auto-editor（Unlicense）：https://github.com/WyattBlue/auto-editor 的 README（`--export` 目标列表）。
- [18] capcut-cli（MIT）：`docs/jianying-encryption.zh-CN.md`、`docs/version-support.zh-CN.md`，https://github.com/renezander030/capcut-cli 。
- [19] pyJianYingDraft（Apache-2.0）：https://github.com/GuanYixuan/pyJianYingDraft （README：支持剪映 5.9+，测到 10.8；新版剪映的草稿通常不是明文）。
- [20] SeeCut 的 `jianying/README.md`（剪映引擎不收带透明通道的视频；其草稿引擎 jianying-headless 为个人学习、非商业许可）。
