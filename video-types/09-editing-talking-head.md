# 09 真人素材剪辑 / 口播（实验性）

> **实验性：本类型是 2026-10-01 根据同类项目的调研写出来的，还没有做过一支完整的片子。** 文中标【实测】的数字只在合成材料上标定过（`say` 合成的中文语音加噪声、手写的字符串和 EDL），没有用真人口播素材试过，也没有在任何剪辑软件里导入过导出的文件；当起点用，拿第一批真实素材校准后再回来改。算法、规则表和出处在 `engines/editing.md`。缺口测量、逐接缝指标、重转写对账、EDL 审阅页、EDL 到 HyperFrames 的编译器**都还没有实现**，现在按那里写的算法自己做；已有的是 HyperFrames 的 `transcript-cut.mjs`，以及本仓库的 `bin/vh qa`、`sheet`、`check`、`mix`。

**适用**：
- 用户自己录的口播、访谈、Vlog、播客视频，要剪干净、加字幕、加图解、出竖屏版；
- 多条素材（主机位、录屏、B-roll）剪成一条；
- 单人口播为主，轻对谈次之。

**不适用**：
- 没有真人素材、要生成人物：走 `playbook/05-hybrid-genvideo.md`；
- 用历史影像剪纪录片：05 的"边界"一节；
- 多机位、影视调色、复杂音频修复：导出 FCPXML 或 OTIO 交给剪辑软件（`engines/editing.md` 的"导出"）；
- 素材里有他人出镜却没有授权，或用户不能说明来源。

**素材是用户的脸和声音**：转写默认在本地做；要把音频传给云端 ASR、把视频传给云端评审，先问用户，在 BRIEF 里记一句；不把用户素材当参考图送给生成模型。

## 引擎

- **首选 HyperFrames**：`data-start`、`data-media-start`、`data-duration` 选取素材区间，视频静音加单独的 `<audio>`，配方里有硬切、修剪、拼接、重排、冻结、变速、缩放、裁切重构图、交叉淡化、音量淡入淡出（`references/repos/hyperframes/skills/hyperframes-core/references/creator-editing-recipes.md`）。`bin/vh new edit <slug>` 建项目后，按交付画幅运行 `bin/vh hf-init <项目目录> portrait`（或 `landscape`）：`bin/vh new` 不会替这个类型自动初始化 HyperFrames。
- **两种接法**：
  - **A 单次合成**（默认）：编译器把 EDL 的每个区间写成一对 `<video>` 和 `<audio>`，字幕、图解、重构图都在同一个页面里，只编码一次；画面仍是 t 的纯函数，叠层像素精确，没有中间代际损失。长素材（> 10 分钟）的抽帧耗时没测【推测】。
  - **B 先剪后包**：ffmpeg 按 EDL 出 `cut.mp4`（中间文件 CRF ≤ 14 或 ProRes），再用 `talking-head-recut` 或 `embedded-captions` 包装。素材很长，或只要粗剪时用。
- **`transcript-cut.mjs`**（`references/repos/hyperframes/skills/media-use/scripts/`）已经能做 `--remove`、`--remove-words`、`--remove-fillers`、`--cut-silence`（`--plan` 只打印保留的区间），是 B 的起点，也是 `quick` 档的最快路线。它默认发用量统计，先 `export DO_NOT_TRACK=1`。
- **转写**：本地词级 ASR，结果缓存，保留口水词（先标定，见 `engines/editing.md`）。选项：Parakeet（英语与 25 种欧洲语言，不含中文）、whisper.cpp（99 种语言，Metal 加速）、FunASR（中文，字级时间戳）、Gemini 3.5 Transcribe（云端，`bin/vh tts … --align gemini` 里封装了一个给合成语音对稿的入口，真人素材要另写）。人脸追踪用 OpenCV 的 YuNet（MIT），5 fps。
- **评审**：默认不用云端。要让 Gemini 读两段 mp4，用户素材就离开了这台机器，先问用户；没同意就只做本地检查，再交给人。

与硬规则的关系：EDL 加上冻结的素材文件，使合成是 t 的纯函数，乱序抽帧比对照常适用（规则 1）；切点由测量到的音频决定（规则 2）；EDL 审阅包就是本类的分镜（规则 3）；字幕照实转写，图解里的数字照抄（规则 5）；ASR 和评审的 key 只从环境变量读（规则 7）。

## 工作流

1. **定档位和 BRIEF**：素材清单（文件、时长、帧率、是不是 VFR、分辨率、语言、说话人数）、发布平台和画幅、必须保留和必须删掉的内容、素材来源与授权、能不能用云端服务。先用大白话写一段 4–8 句的策略（结构、删什么、包装、时长），等用户确认再动剪辑（关卡 ①）。**没有确认的策略，不碰剪辑。**
2. **入库**：`ffprobe` 每个源文件。手机素材常是 VFR（`r_frame_rate` 与 `avg_frame_rate` 不等），先转 CFR，否则帧对齐和 FCPXML 导出都会出错。29.97、23.976、59.94 的素材先转成 30、24、60（`fps=30` 等；HyperFrames 0.8.82 也能渲有理数帧率，但按素材原生帧率渲还没拿真实素材验证），EDL 按这个整数帧率记帧号，导出时再换回素材自己的帧格。色彩标签也查一遍（应为 `yuv420p`、`tv`、`bt709`；不是的话，先想清楚像素是哪种矩阵，再决定补标签还是重编码）。抽 16 kHz 单声道音频用于测量，记录每个源文件的 sha256。
3. **转写**：词级、保留口水词、缓存。转写后打成"短语行"视图：按 ≥ 0.5 s 的静音或换人断行，`[起-止] S0 文字`，token 约为原始 JSON 的十分之一。
4. **测量**：对每个源文件算噪声底、阈值和每个 ≥ 250 ms 的缺口。切点由缺口里的能量谷决定，不由 ASR 的词时间决定。
5. **决策**：模型读短语行和缺口，写 EDL：选 take、删口水词、重录、假开头、场外话、无功能的重复。入出点存**整数帧**（吸附到帧格后再存，秒数在取整处会有平局）。每处删除都带 `class` 和 `reason`。**停下来等人审 EDL**，这是关卡 ②。人批准后记下 EDL 的哈希，渲染只认这个哈希。
6. **吸附与渲染**：每个区间吸附到缺口里的能量谷，再落到帧格和过零点；留 handle；音频接缝交叉淡化 40 ms、画面硬切；一次编码。
7. **验证**：逐接缝指标、重转写对账、按播放顺序连读一遍、接缝 strip。有问题只改受影响的区间重渲。
8. **包装**：避脸字幕、必要的重构图、图解叠层（只用真实截图或录屏）、配乐和声音。
9. **评审**：**打分层照旧：`TASTE_CHECKLIST` 的 8 项打分（硬规则 4；立意一项问的是这一版的剪辑思路：结构和取舍是不是在讲这段内容）**；再加两两对比，决定新版能不能取代当前版（`engines/editing.md`）。`standard` 做 1 轮、修最差的 3 处，`studio` 至少 3 轮、最多 10 轮、8 项都 ≥ 8 才出片（同一类问题最多改 5 次，小修只做局部复查，见 `TASTE_CHECKLIST` 打分层）；再交人，关卡 ③。
10. **导出与交付**：`final.mp4`、`captions.srt`、`edl.json`；按需 FCPXML、OTIO、CapCut 或剪映包；素材台账和授权记录。

**档位**：
- `quick`（降档只能来自用户本人）：`transcript-cut.mjs` 自动粗剪加字幕，一张联系表，没有人工关卡；它按 ASR 的词边界切，这是本类唯一有意的例外（见"禁止"第一条），交付说明里写明接缝没测过。改动仍然先写成 `edl.json`，方便回溯。
- `standard`：EDL 关卡、逐接缝指标、重转写对账、1 轮两两对比。
- `studio`：再加重构图检查、至少 3 轮两两对比（最多 10 轮）、导出到剪辑软件、人耳逐个接缝复听。

## 审美要点

- **剪的是有效内容**：每段要么增加观点、证据、例子、步骤，要么承担承接；只是换个说法原地重复的删掉。
- **起点参数**（都是起点，不是规定；出处在 `engines/editing.md`）：

  | 项 | 起点 |
  |---|---|
  | 切点留白 | 入点前 50 ms、出点后 20 ms；或 30–200 ms 窗口 |
  | 被删的重来接缝残留静音 | ≤ 80 ms |
  | 保留的自然停顿 | > 180 ms 要有画面证据 |
  | 说话人交接 | 400–600 ms 留气，快节奏更短，文艺更长 |
  | 音频接缝 | 40 ms 交叉淡化，画面硬切 |
  | 峰值保留 | 笑声、强调、包袱之后多留一拍反应 |

- **"对你说"就露脸，"给你看"就藏**：观点、收尾、建立信任这类句子，说话人露出来；演示、列举、给证据的句子，说话人缩小或隐去，信息层当主角。SeeCut 的统计（8 个参考片、536 拍）是演示类 77% 隐去人像、收尾 70% 露半身，样本小、没有复现，当作方向，不当规则【二手】。
- **图解只用真实证据**：真实网页截图、真实录屏、真实数字；不用假 UI、假数据占位（和 03 篇一致，也是硬规则 5）。
- **保持人味**：口头禅删大部分留少量，保留笑声和自然呼吸；剪完要让主讲人看了觉得"这是我实际说过的意思"。
- **字幕**：沿用 02 篇（单行、一个强调色、每句强调 1–2 个词），加上避脸与中文切分；安全框取 `playbook/03-motion-design.md` §5 的表，和 `engines/editing.md` 里的实测值两边较大者。
- **声音**：响度 −14 LUFS，配乐垫在人声之下，用 `bin/vh mix` 的 duck。音效按可见事件挂，不每次转场都来一个（video-use 的经验：18 秒里 20 个音效像素材库，8 个才像设计过）。

## 禁止

- 切在词内；只按 ASR 的词边界切、不测量音频（`quick` 档的 `transcript-cut.mjs` 是有意的例外，见"工作流"）；
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
+ TYPE: editing the user's own footage (talking head). Sources {files, duration, CFR fps, resolution, zh-CN}. Deliver {1080x1920 | 1920x1080} {30}fps {45–90}s + captions.srt + edl.json. Platform: {抖音 | 小红书 | 视频号 | B站 | Shorts}.
Plan first: 4–8 plain sentences (structure, what goes, packaging, length); wait for approval before cutting.
Cut where the audio is quiet, not at ASR word times: measure gaps (>=250 ms), cut in the energy valley, snap to the frame grid, 40 ms audio crossfade, hard picture cut. No gap: keep the word.
Keep the speaker's words: transcribe with fillers, remove retakes, false starts, dead air; keep qualifiers and a few natural fillers; never rewrite or add words. A leading 对/然后/所以 is judged by reading it aloud, not by list.
Write edl.json (integer frames, a reason per cut) and STOP for approval; render only from the approved hash.
One-line captions, face-safe, inside the platform safe area; overlays only from real screenshots or recordings.
Verify: re-transcribe the render and diff it against the EDL; every cut has measured evidence.
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
- 用户素材有没有在未同意的情况下离开这台机器？

## 可参考的案例与源码

- `engines/editing.md`：EDL、测量切点、口水词与重录规则、重转写对账、两两对比、重构图、避脸字幕、导出，以及借来的思路和出处（社区 skill 的许可证都在那里）。
- `references/repos/hyperframes/skills/media-use/`：`scripts/transcript-cut.mjs`、`references/repos/hyperframes/skills/media-use/references/operations.md`（转写、剪切、响度）。
- `references/repos/hyperframes/skills/talking-head-recut/`：在不改动素材的前提下叠图解卡片，本类包装阶段的现成流程；不剪片。
- `references/repos/hyperframes/skills/embedded-captions/`：本地转写、主体抠像、字幕绕到人物身后、安全区；`references/` 下有 `aesthetic-principles.md`、`anti-patterns.md`、`caption-grouping.md`、`layout-heuristics.md`。
- `references/repos/video-talkcraft/`（PolyForm NC，只读）：真人录音先预剪再做时间戳；以稿子为真值，ASR 听错的字不剪。
- `cases/community-prompts.md`：@AxtonLiu 的口播图解做法。
