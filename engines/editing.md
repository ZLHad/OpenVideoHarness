# 真人素材剪辑：机制、算法和出处（实验性）

这一页是 `video-types/09-editing-talking-head.md` 的细节：EDL、用测量定切点、口水词和重录的规则、重转写对账、两两对比评审、重构图、避脸字幕、导出，以及借来的思路和出处。类型文档管"做什么、先后顺序、禁什么"，这一页管"具体怎么算"。

> **实验性：下面标【实测】的数字只在合成材料上标定过**（macOS `say` 合成的中文语音加噪声、手写的字符串和 EDL），没有用真人口播素材试过，也没有在任何剪辑软件里导入过导出的文件。缺口测量、逐接缝指标、重转写对账、EDL 审阅页、EDL 到 HyperFrames 的编译器都**还没有实现**（顺序见"建议的落地顺序"），现在按这里写的算法自己做。
>
> 标记：【实测】在维护者的 Mac（macOS 15，ffmpeg 8.0.1，numpy）上跑过；【二手】没能读到原文；【推测】没有证据的推断。引用编号 `[n]` 见文末"来源"。依据是 2026-09-30 对同类项目的调研，2026-10-01 把相关仓库的源码重新读了一遍、重新核对了阈值。

## EDL

EDL 是剪辑的唯一事实来源，综合了 video-use 的 EDL、open-edit 的 `apply-edl` 和 kinocut 的审批哈希 [4][6][7]。

```json
{
  "version": 1, "fps": 30,
  "sources": { "A": { "path": "footage/A.mov", "sha256": "…", "cfr": true, "src_fps": "30000/1001", "duration": 612.4 } },
  "ranges": [
    { "id": "r01", "source": "A", "in": 73, "out": 206, "beat": "HOOK",
      "quote": "…", "reason": "最干净的一遍，在 38.46 s 的口误之前停",
      "snap": { "in": "valley", "out": "valley", "handle_in_ms": 50, "handle_out_ms": 20 },
      "seam_out": "xfade40" }
  ],
  "removed": [
    { "source": "A", "in": 206, "out": 273, "class": "retake", "text": "我觉得吧我觉得", "confidence": 0.8 }
  ],
  "approval": { "edl_sha256": "…", "approved_by": "user", "at": "…" }
}
```

- **入出点存整数帧**，`fps` 是渲染用的整数帧率。先吸附到缺口里的能量谷，再落到帧格，取整规则写死（四舍五入，恰好一半往后取），之后只存整数。存秒数会出事：6.85 s 在 30 fps 下是 205.5 帧，恰好平局，取整方式一换，切点就差一帧。
- 总时长是各区间帧数之和，offset 也按帧数累加，不在秒数上累加浮点误差（open-edit 的做法）[6]。
- **29.97、23.976、59.94 fps 的素材**：先转成 CFR 的整数帧率再渲（HyperFrames 0.8.82 其实也能按 `--fps 30000/1001`、`25` 这类帧率渲，测试合成上实测过；按素材原生帧率渲还没拿真实素材验证，验证之前照下面的做法）：29.97 用 `fps=30`，23.976 用 `fps=24`，59.94 用 `fps=60`；EDL 记转换后的整数帧号，`src_fps` 记素材自己的帧率。导出给剪辑软件时，用时间把入出点换回素材自己的帧格（29.97 的帧时长是 1001/30000 s）再取整，不要直接沿用转换后的帧号：转换每 1001 帧补 1 帧，画面看不出来，10 分钟之后帧号就差了 18 帧。
- `class` 取值：`filler`、`retake`、`false_start`、`silence`、`offscript`、`take_loser`、`process_talk`。
- **审批哈希**：人批准的是这份 EDL 的哈希；渲染前核对，不一致拒绝渲染。kinocut 对"已批准的 EDL 与时间线差异"做六项检查：审批哈希、源时间覆盖、顺序、只删批准的段、音画同映射、字幕重映射 [7]。我们至少做审批哈希、只删批准的段和音画同映射。
- 源文件颜色或帧率不一致时拒绝拼接，不悄悄改标签（open-edit 的做法）[6]。

## 用测量定切点

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

**【实测】**（合成材料）：用 macOS 的 `say` 合成 5 句中文，句间插入 300、120、600、180 ms 的已知停顿，叠一层峰值约 −42 dBFS 的粉红噪声当房间底噪，共 18.7 s，用上面第 1–3 步的算法测缺口。`gap = 250 ms` 时，两个长停顿检出 340 和 650 ms（插入的是 300 和 600；合成语音句尾自带一点静音，所以比插入值长 40–50 ms）；改成 `gap = 100 ms` 后，再检出 170 和 240 ms 两个（插入的是 120 和 180）。所有插入的停顿都找到了，没有漏报。句内的逗号处也检出约 310–320 ms 的缺口，这是正常的短语边界；片头片尾的静音也会被当成缺口。这是合成语音，不是真人口播的结论。

## 口水词、重录与中文规则

**先校准 ASR 会不会保留口水词。** Whisper 系倾向省略 um、uh 这类词，给它一个带口水词的提示能让它更愿意写出来，但也更容易幻觉出没说过的词 [10]；video-use 直接不建议用本地 Whisper，改用云端逐字转写 [4]；mandarin 用火山的录音识别，并显式关掉"语义顺滑"（`enable_ddc: false`）以保留语气词 [9]；CrisperWhisper 专为逐字和准确时间戳训练，但只保证英语和德语，许可证是 CC-BY-NC，中文不能用 [10]。所以每个 ASR 候选都先跑一遍标定样本：录 15 秒带已知"嗯、呃、这个、我觉得吧我觉得"的话，看它写不写出来，结果记进 `LOCAL.md`。没有标定就不承诺"自动删口水词"。ASR 不转写的单字口水词，只能靠缺口和回听处理，diff 也看不到（见"重转写对账"）。

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

**剪的是结构，不是时长**：不用目标时长或删减比例倒推要删什么，时长和比例只是完成后的统计 [9]。开头找真正的话头（设问、观点、现象、结果前置），结果前置不能改变原句的条件，也不能把后文才建立的指代一起搬到开头；结尾要收束，结论之后的"好了、过了吗"删掉 [9]。

## 重转写对账

**核心是比词序，不比时间。** proofcut 的发现：Whisper 会把紧挨着的重录吞进相邻词的时长里，时间戳证明不了重录被删了，但重转写出来的文本里那句话会出现两次，而 EDL 期望的序列里只有一次 [11]。

- **英文起点值**（proofcut，PolyForm Shield，只借思路）：用 `difflib` 对词序列做 diff；多出来的片段至少 2 个词才算（单词多半是某一遍转写出来的口水词）；与期望序列的相似度 ≥ 0.5 判为残留重录（0.5 是因为第二遍总是被转写得更差）；干净的成片整体相似度约 0.97；相邻重复检测要求片段 ≥ 4 个词，向前看 40 个词，与期望重复的吻合度 ≥ 0.75 才算是 EDL 自己留的重复 [11]。
- **中文要改成字级**：中文没有空格分词，token 取汉字，去掉标点，阿拉伯数字转汉字（避免"30"与"三十"的逆文本规整差异）。起点值 `MIN_RUN = 4` 字、`SIMILAR = 0.5`、`ADJ_MIN = 6` 字、`ADJ_LOOK = 60` 字，用 `difflib.SequenceMatcher` 对字符序列做 diff。在 5 个合成字符串上【实测】：

  | 情形 | 相似度 | 结果 |
  |---|---|---|
  | 干净（ASR 把"三十"写成"30"） | 0.982 | 无提示 |
  | 残留重录（整句多说一遍） | 0.887 | 多出的 14 字被判"残留重录？" |
  | 残留假开头（"我觉得吧我觉得"） | 0.94 | 被判"期望里没有的插入" |
  | 删过头（少了一句） | 0.854 | 报出缺失的 14 字 |
  | 单字口水词"嗯" | 0.991 | **不会被 diff 发现**，需要口水词表计数 |

  这些阈值是在合成字符串上得到的，换真实 ASR 要重新校准【推测】。相邻重复检测对重叠片段会多报，取不重叠的最强候选。
- **与 open-edit 的"不要重转写成片"不矛盾**：open-edit 的 `retime-transcript` 按 EDL 平移已有的词时间，不再付一次 ASR，用来生成字幕时间；跨在切点上的词，只有超过一半落在保留区间内才留下 [6]。重转写是独立的验证，用本地 ASR 转成片的音轨（ASR 的选项见 `playbook/04-audio.md` [2]）。两件事都做：retime 给字幕，重转写给验证。
- **逐接缝指标**（timecode-agent，MIT）：切在词内（`word_interior`）；词尾余量小于 0.12 s 而缺口本来足够（`tight_tail`）；接缝两侧 RMS 差超过 12 dB（`loud_step`）；接缝两侧画面的 SSIM 超过 0.75，说明是同机位跳切，需要遮盖 [5]。这些只出旗标，取舍由 agent 决定。

## 两两对比评审

`playbook/02` 的打分层是绝对分数（8 项；`studio` 要求每项 ≥ 8）。SeeCut 做过校准实验：绝对打分下，"假满屏"的坏版本和参考原片同分；改成两两对比后，判断与人一致 [12]。所以本类在绝对打分层**之外**再加一道两两对比，决定"新版能不能取代当前版"。**打分层照旧：按档位做（硬规则 4）**，绝对分里的 FAIL 项当硬伤清单逐条修，不把分数加总去比较。

流程（SeeCut 的做法，PolyForm NC，只借思路）[12]：
1. 对手是**当前采纳版**（不一定是上一版）。第一版没有对手时，用 `auto-editor` 或 `transcript-cut.mjs` 出一个笨办法的粗剪当基线【推测：这是我们的补充】。
2. **A/B 交换位置各跑一次**，两次都判新版赢才采纳。结论不一致算平手。**跑失败算"对比没有发生"，不算输，也不算赢**，也不能按"没输"交付。LLM 评委有位置偏好 [13]，交换位置是标准缓解办法。
3. **防编造**：要求评委照抄画面上 3 处文字并报出视频时长，脚本核对源码里至少命中 2 处、时长误差 ≤ 3 s，不过就判"无效"，重跑一次。
4. **评委隔离**：把视频复制到项目目录之外再交给评委，不让它读到项目源文件；每次新开会话。
5. **评委报的每条 FAIL，必须打开它标的那一秒的帧去核实**；判误报要写清时间和看的帧。评委有"把相邻两拍当同屏"的毛病。
6. **盲区**：两两对比会被"更满但是假"的版本骗过（SeeCut 实测干净版输给假满屏版）。所以"假证据"由硬门禁直接拒绝，不指望评委扣分。
7. **云端评委默认不用**：用 Gemini 读两段 mp4，用户素材就离开了这台机器，先问用户；没同意就只做本地检查，再交给人。这套两两对比先只在本类试，不推广到别的类型。

**本类的评审维度**（建议）：话头与钩子、承接与逻辑连续、节奏与接缝自然度、字幕与构图、画面证据真实性、声音（响度、人声清晰）、整体像不像本人自然说话。

## 重构图

- **算账**：1920×1080 横屏取 9:16，裁出 608×1080，再放大到 1080×1920，放大 1.78 倍，会发软；4K 横屏源文件裁出 1215×2160，缩到 1080×1920 是缩小，画质没有损失。所以竖屏成片优先用 4K 源，或接受 1080p 源的发软，并在交付说明里写明。
- **规划器**（kinocut，Apache-2.0）：用人脸或主体追踪的轨迹，裁剪窗口中心每个采样点最多移动 0.10（归一化），追踪置信度低于 0.70、丢失目标、多人歧义、超出裁剪预算时**放弃裁剪（abstain），不硬裁**；多人对话按说话人切换主体 [7]。追踪用 YuNet，5 fps [3]。
- **在 HyperFrames 里**：把平滑后的轨迹写成分段线性表，`cropX(t)`、`scale(t)` 作用在 `<video>` 的 CSS transform 上，仍是 t 的纯函数；换说话人时硬切，不平移。
- **遮盖跳切**：同机位跳切可以在每个切点和多数句首打 1.0 与 1.1 交替的 snap zoom（ghost-editor 的做法 [3]）。这是一种风格，不是必须：`clean` 风格每句一次，过度使用会显得廉价。
- **验证**：挑头部动作最大的 5 个时刻出 strip；眼睛大致落在上三分线，脸不被裁。

## 避脸字幕

**竖屏平台的遮挡**：`playbook/03-motion-design.md` §5 有抖音、视频号、小红书、TikTok、Shorts 的近似值（第三方给的，发布前用真机截图校准）。下面是 ghost-editor 在 1080×1920 上量的 Reels、TikTok、Shorts [3]，和 03 有出入（TikTok 的下沿 03 写约 324，这里是 480）：**两边取较大的当安全框**，发布前用真机截图校准；抖音、小红书、视频号只有 03 的值，以及关键内容框 x 90–900、y 330–1520【推测】。

| 平台 | 上 | 下 | 右 |
|---|---|---|---|
| Instagram Reels | 220 | 420 | 130 |
| TikTok | 160 | 480 | 150 |
| YouTube Shorts | 140 | 380 | 140 |
| 三者并集 | 220 | 480 | 150 |

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
- 措辞的优先级：录音与表现 > 用户提供的参考稿 > ASR；断句由 agent 按语义写，不让代码按字数硬切。

**层级**：字幕最后叠（video-use 的规则 1），避免被图解盖住 [4]。字号、强调色、安全框沿用 02 篇。

## B-roll 与图解素材

- 先给每句话定功能（对你说、给你看、给数字、给证据），再定人像露不露、信息层放什么。
- 挑 B-roll 不要把整条素材丢给模型：按约 10 s 一个窗口给素材写画面描述，再按这句话讲的内容挑窗口（proofcut 的 `describe` 思路）[11]。
- 扫描素材出联系表：2 fps 取样，只在画面稳定到新状态时才取一帧，单张联系表不超过 2576×1456、最多 12 格（diffusionstudio，MPL-2.0，只借思路；【二手：来自调研摘要，没有重读源码】）。
- 证据只用真实截图、录屏、数字；素材没有的就先去截，不自己造（和 03 篇一致）。

## 导出：FCPXML、OTIO、CapCut 与剪映

| 目标 | 做法 | 状态和注意 |
|---|---|---|
| 成片 | mp4，H.264，BT.709 tv 四个标签齐全：`scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv` | 响度、黑场等走 `bin/vh check` |
| 字幕 | SRT（按 retime 后的词时间生成）加 `captions.json` | — |
| 我们自己的 EDL | `edl.json` | 是唯一事实来源 |
| Final Cut Pro、DaVinci Resolve | FCPXML：`asset-clip` 放在 `spine` 上，所有时间是帧时长的整数倍（有理数，NTSC 用 1001/30000 这样的精确值），只接受 CFR 素材 | **默认写 1.10**：FCP 10.8.1 用 1.12，FCP 11 用 1.13，FCP 12 用 1.14 [15]；新版通常能读旧版，FCP 会拒绝它不认识的更新版本【二手】；Resolve 19.1 读 1.3–1.10，据报 1.11 也可【二手】。**没有在 FCP 或 Resolve 里导入过，【未验证导入】** |
| Premiere Pro、Resolve、通用 | OTIO：Premiere Pro 的 OTIO 导入导出 2024-10 进入 beta，正式版据报在 26.0（2026-01）【二手】；Resolve 自 18 起原生支持 .otio 和 .otioz；OTIO 官方 wiki 的原生支持列表里没有 Final Cut Pro，FCP 走 FCPXML。Premiere 支持的内容：名称、剪辑表、入出点、起始时码、帧率、多轨、线性变速、标记；外部生成的 OTIO 导入后，部分序列设置要手动调整 [16] | 最中立，首选给不知道用哪款 NLE 的用户 |
| 只有简单剪切 | `auto-editor --export <目标>`，目标有 premiere、resolve、final-cut-pro、shotcut、kdenlive、clip-sequence（Unlicense）[17] | 只适合静音或音量阈值剪切 |
| **CapCut（国际版）** | 草稿是明文 JSON，`capcut-cli`（MIT）能读写；6.2.8 有 fixture 测试，6.5–9.x 只是预期兼容，10.x 有"内容已损坏"的报告，写入默认被护栏拦下 [18] | 实验性。导出前核对用户的版本，先用一个 2 秒样例验证 |
| **剪映（国内版）** | **6.0 起 `draft_content.json` 是 AES 加密的二进制**，5.9.x 是最后广泛使用的明文版本；`capcut-cli` 只检测、不解密，对 6.0+ 的写入默认拒绝 [18]。`pyJianYingDraft`（Apache-2.0）声明支持 5.9+、测到 10.8，导出在 5.9 和 6.8 上测过，但 10.x 有草稿被判损坏的 issue [19] | **不承诺"一键导出剪映草稿"**。稳妥的交付是：`final.mp4` + `captions.srt` + 分层素材包（透明 PNG、音频、时间表），用户手动拖入。剪映不接收带透明通道的视频，叠层只能用 PNG 加淡入淡出，所以成片和素材包要分别交付 [20] |

**FCPXML 的骨架**：导出时，每个区间的入点、出点先各自取整到素材自己的帧格（29.97 就是 1001/30000 s 的整数倍），`offset` 用前面各段帧数的累加，**不要**把秒数加起来最后再取整：后一种做法在区间不是整帧时，会在 spine 里留下 1 帧的缝或重叠（用 8 个 0.51 s 的区间在 29.97 fps 下试出来：8 个里有 2 处错位）。先在帧上取整再累加之后，6 种帧率（24、23.976、25、29.97、30、59.94）下都是格式良好、所有时间是帧时长的整数倍、spine 首尾相接、序列时长等于各段之和【实测，合成 EDL，没有导入过剪辑软件】。29.97 fps、两个区间（2.42–6.85 s 和 14.30–28.90 s）生成的骨架：

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

上面的 FCPXML 只示意格式（29.97 素材、两段首尾相接），数字不是从前面的 EDL 例子推出来的。

导出之后用户在剪辑软件里做的修改不回读，不把剪辑软件当事实来源。

## 社区 skill 参考

以下选自 2026-09-30 的调研，许可证 2026-10-01 按仓库 LICENSE 和 GitHub 元数据核对过。只读参考；复用代码前按 `references/community-skills.md` 的规则处理。这些仓库还没有进 `references/fetch.sh`，本文没有拷它们的代码。

- **video-use**（browser-use，MIT）：EDL、短语视图、12 条硬规则（字幕最后叠、按段提取再无损拼接、每个接缝 30 ms 淡入淡出、绝不在词内切、缓存转写等）、渲染后在每个切点 ±1.5 s 自检、最多 3 轮 [4]。它偏好云端逐字 ASR，与我们"本地优先"的取向不同。
- **open-edit**（veedstudio，Apache-2.0）：`speech-probe`、`apply-edl`（单次编码、帧格吸附、拒绝颜色或帧率不一致的源）、`retime-transcript` [6]。
- **cut-motion**（Endless1936，Apache-2.0）：`tight-talking-head` 的三阈值中位数边界、不对称 handle、画面证据分类；中文字幕切分标准 [8][14]。
- **kinocut**（KyaniteLabs，Apache-2.0）：语义 EDL 与审批哈希、`verify_timeline_diff` 六项检查、重构图规划器 [7]。
- **timecode-agent**（mupozg823，MIT）：接缝指标、FCPXML 与 OTIO 导出、CFR 证明 [5]。
- **ghost-editor**（kurbaitaev，MIT）：避脸字幕放置、平台遮挡像素、YuNet 追踪、snap zoom [3]。
- **mandarin-talking-head-rough-cut**（m15851855393-boop，Apache-2.0）：口水词与重录规则、能量谷吸附、承接测试与通读脚本；它的 ASR 走火山云，我们不用那一段 [9]。
- **proofcut**（tydude001，PolyForm Shield，只借思路）：重转写词序对账 [11]。
- **SeeCut**（YeJe-cpu，PolyForm NC，只借思路）：两两对比评委、功能到打法的决策表、剪映分层交付 [12][20]。
- **clipify**（louisedesadeleer，MIT）：按说话人生成 ffmpeg 的 crop x 表达式，说话人切换时硬切。**doza-assist**（DozaVisuals，MIT）：从用户自己剪完的作品里学剪辑风格（停顿、开头、soundbite），在用户本地运行，导出 FCP、Premiere、Resolve，可以并进 `playbook/07`。
- **auto-editor**（Unlicense）：静音剪切与多个剪辑软件的导出 [17]。**capcut-cli**（MIT）、**pyJianYingDraft**（Apache-2.0）：CapCut 与剪映草稿 [18][19]。**fcp-mcp-server**（DareDev256，MIT）：`fcpxml/rational.py` 的有理数帧率（23.976 → 24000/1001）。

## 建议的落地顺序

下面这些工具现在都不存在：

1. 本地词级 ASR + 口水词标定 + 短语视图。
2. 缺口测量（"用测量定切点"的算法做成命令）+ EDL 结构、审批哈希、EDL 审阅页（文本 diff、时间、理由、样本片段）。
3. EDL → HyperFrames 合成的编译器（`data-media-start` 那一套）+ retime 生成字幕。
4. 逐接缝指标、重转写对账（中文字级）、通读脚本、两两对比评委。
5. 避脸字幕与中文切分、重构图。
6. 导出：SRT、FCPXML 1.10、OTIO；CapCut 作为实验性选项。

## 待验证

1. 候选 ASR 对中文口水词的保留情况；本地中文模型的字级时间戳精度。
2. 接法 A 在长素材上的抽帧耗时和内存。
3. FCPXML 与 OTIO 在 FCP 12、Resolve 20、Premiere 26 里的实际导入。
4. CapCut 与剪映的具体版本行为（用户手上的版本）。
5. 重转写对账的阈值在真实 ASR 输出上的表现。
6. 抖音、小红书、视频号的 UI 遮挡像素。
7. 两两对比评委在剪辑任务上的稳定性，以及"笨办法粗剪"当基线是否有区分度。
8. 缺口测量的阈值在真人口播（有呼吸、口腔音、房间混响）上的表现。
9. 29.97 fps 素材转成 30 fps 后，导出时换回素材帧格的做法在剪辑软件里是否对得上。

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
