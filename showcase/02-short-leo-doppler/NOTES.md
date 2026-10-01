# NOTES

## 待核实的事实
<!-- 数字全部自己算过；计算脚本见下方"计算记录"，可复跑 -->
- [x] LEO 500–550 km 轨道速度约 7.6 km/s — 来源：圆轨道 v = √(GM/r)，GM = 3.986004418e14 m³/s²，R⊕ = 6371 km → 500 km: 7.617 km/s，550 km: 7.589 km/s — 状态：已核实，视频写"7.6 km/s""离地 500–550 km"
- [x] 频移 f_d ≈ (v_r / c)·f，v_r 是视向（朝向观察者的）速度分量 — 来源：一阶（非相对论）多普勒，v_r/c ≈ 2.3e-5，二阶项可忽略 — 状态：已核实，视频写"Δf ≈ (v/c)·f，v = 朝向你的速度"
- [x] 2 GHz 时最大约 ±50 kHz — 计算：过顶弧段里视向速度最大值 = v·(R⊕/r)·cos(仰角)。550 km、0° 仰角 → 6.99 km/s → 46.6 kHz；10° 仰角 → 45.9 kHz；上界（v_r = 全速 7.6 km/s）50.6 kHz — 状态：已核实。视频措辞用"**接近** ±50 kHz"，比"约 ±50 kHz"更贴近 46–47 kHz 的真实值；图表刻度画在 ±50，曲线峰值落在刻度线下方约 8%
- [x] Ka 20 GHz 时约 ±500 kHz — 同上 ×10：466 kHz（0°）/ 459 kHz（10°）/ 上界 506 kHz — 状态：已核实，视频写"20 GHz：再大 10 倍"，刻度 ±500 kHz
- [x] 一次过顶几分钟 — 非旋转地球、正过顶：550 km 时 0° 仰角门限 12.2 min，10° 门限 7.9 min，25° 门限 4.5 min — 状态：已核实，视频写"一次过顶：几分钟"
- [x] 频移从正（靠近）→ 0（正头顶，最近点）→ 负（远离） — 由 v_r = v·R⊕·sinθ / d 推出，θ 为地心角，θ=0 时 v_r=0 — 状态：已核实，图表曲线就是用这个式子逐点算的（10° 仰角门限、550 km）
- [x] 系统用已知轨道预补偿 — 来源：3GPP NTN（Rel-17，TS 38.300 NTN 部分 / TR 38.821）：终端用自身 GNSS 位置 + 广播的卫星星历计算并预补偿上行频偏和定时；下行残余频偏由接收机跟踪 — 状态：概念核实（凭已知规范内容，未逐条引用条款号）。视频只说"轨道已知，能提前算出 → 提前反向补偿"，不写具体规范，也不声称"补偿到正好 0"（图上写"≈ 0"）
- [x] 地球自转影响 — 赤道自转速度 0.465 km/s，会让实际最大频移偏几个百分点，方向取决于轨道倾角和纬度 — 状态：不进视频，属于"约/接近"的误差范围
- [ ] 过顶时频移变化率（550 km：2 GHz ≈ 640 Hz/s，20 GHz ≈ 6.4 kHz/s）— 状态：算了但**没放进视频**（一镜一意，放不下）

## 计算记录
```text
$ node tools/doppler_calc.mjs     （同一套公式也写在 index.html 的 PHYS 段，图表曲线逐点用它算）
h=500 km  v=7.617 km/s  period=94.5 min
  mask 0°: pass 11.5 min, max v_r 7.06 km/s, fd@2GHz 47.1 kHz, fd@20GHz 471 kHz
  mask 10°: pass 7.4 min, max v_r 6.96 km/s, fd@2GHz 46.4 kHz, fd@20GHz 464 kHz
  mask 25°: pass 4.1 min, max v_r 6.40 km/s, fd@2GHz 42.7 kHz, fd@20GHz 427 kHz
  upper bound (v_r=v): 2GHz 50.8 kHz, 20GHz 508 kHz
h=550 km  v=7.589 km/s  period=95.5 min
  mask 0°: pass 12.2 min, max v_r 6.99 km/s, fd@2GHz 46.6 kHz, fd@20GHz 466 kHz
  mask 10°: pass 7.9 min, max v_r 6.88 km/s, fd@2GHz 45.9 kHz, fd@20GHz 459 kHz
  mask 25°: pass 4.5 min, max v_r 6.33 km/s, fd@2GHz 42.2 kHz, fd@20GHz 422 kHz
  upper bound (v_r=v): 2GHz 50.6 kHz, 20GHz 506 kHz
  max Doppler rate at zenith: 2GHz 643 Hz/s, 20GHz 6.4 kHz/s
Earth rotation speed at equator 0.465 km/s
fractional shift v_r/c 2.33e-05
```

## 创作决策
- 2026-09-28 引擎 HyperFrames 0.8.82，按类型文档首选。**没有**走 `/faceless-explainer` 的全自动脚本链（build-frame / audio.mjs / frame-packets / 每帧一个 subagent / assemble-index）——24.8s、静音、一个连续舞台，拆成 7 个 subagent 各写一帧反而会破坏"同一舞台"的连续性；借用它的方法（结构 = concept-explainer with process、hook 策略、VO/字幕驱动的逐步揭示、不前置堆满、Video direction）手写一个单体 `index.html`。
- 2026-09-28 没有运行 `npx hyperframes skills update`：读 CLI 源码（dist/cli.js 的 `GLOBAL_INSTALL_ARGS_TAIL`）发现它带 `--global --agent claude-code universal`，会写 `~/.claude/skills` 和 `~/.agents/skills`，违反"不碰 ~/.claude"。`init` 也会检查并刷新全局 skills，所以用 `HYPERFRAMES_SKIP_SKILLS=1` 关掉；技能文档直接读 `references/repos/hyperframes/skills/`。
- 2026-09-28 `init` 拒绝非空目录，而 `bin/vh new` 已经建好了带模板的项目目录 → 在 scratch 里 `init` 一个空项目，再把 6 个脚手架文件拷进项目根。
- 2026-09-28 静音片：没有 SCRIPT.md；STORYBOARD 头部 `music: none`（HyperFrames 的静音标记）；字幕脚本写在 STORYBOARD 的 Caption script 表里。
- 2026-09-28 地球 / 天穹 / 轨道高度都是示意，不按比例（真实 550 km 只有地球半径的 8.6%）；信号波的疏密变化**放大了约 1 万倍**（真实 v/c ≈ 2.3e-5），画面上用 44px 小字"示意：波长变化已放大"说明。
- 2026-09-28 过顶段的时间映射：物理时间匀速时卫星在头顶附近角速度最快、几乎一闪而过（node 试算：线性时间下 α 从 62° 到 118° 只用 1.2s）。改成**天穹角 α 匀速**（10°→170°，6.4–14.0s，21°/s），再由 α 反推地心角 θ 和视向速度；图表横轴仍是物理时间 x = (θ/λ+1)/2，所以曲线形状是真的，只是"画曲线的速度"在中段变慢，让"正头顶：归零"有 ~1.9s 可读。
- 2026-09-28 字体：本机没有 Noto Sans SC / 思源黑体；用 Google Fonts `<link>` 加载 Noto Sans SC（OFL）。HyperFrames lint 认可 Google Fonts 链接，渲染时自己本地化。和脚手架从 jsDelivr 加载 GSAP 是同一个信任级别。
- 2026-09-28 c1（hook 副标题）1.2–3.2s，2.0s，8 字。
- 2026-09-28 STYLE 里写的"S6–S7 字幕上移一次打破节奏"没做：图表放大后上方被公式占用；24.8s 不到类型文档说的"每 30 秒打破一次"，hook 大字本身已是一次变化。
- 2026-09-28 保持单体 index.html（~430 行）。lint 建议拆成 compositions/ 子合成（composition_file_too_large、nested_structure_needs_subcomposition 等 5 条 warning），但 S3–S7 是一个连续舞台、由同一个 draw(t) 驱动，拆开反而要跨文件共享状态；warning 保留。
- 2026-09-28 成片没有音轨（静音片，HyperFrames 不写空音轨；2026-10-01 起有音轨，见下）。多数平台接受无音轨视频；如平台要求，可用 ffmpeg 补一条 anullsrc 静音 AAC。

- 2026-10-01 **给做好的画面补声音**（README › Soundtrack）：中文配音 + 轻配乐 + 音效。画面时间不动，声音去对齐画面。
  - **旁白为 AI 合成（Gemini TTS，音色 Aoede，含 SynthID 水印）**，发布时按平台要求标注。
  - 配音稿就是 STORYBOARD 的字幕 c0–c9，只加了"时"之类的口语连接，事实一个没加。英文一侧只进软字幕。
  - 选音色：同两句稿子试了 Leda、Aoede、Puck、Sulafat，比语音识别相似度、语速、音高起伏。Puck（0.42，"我的星星…"）和 Sulafat（0.74）听不清；Leda 太慢（7 个字 2.0 s），塞不进镜头。Aoede 配上"语速快、一口气说完"的整体指示后，每秒 4.4–5.1 字，全部放得下。
  - 落点：手写的行网格 `audio/vo_grid.json`（每个镜头起点后 0.2–0.35 s）加 `bin/vh tts … --beats`。每句都在自己的格点上起，并在它的字幕消失前念完；最紧的一句 fix 念到 24.51 s，离片尾还有 0.29 s。没有一句需要变速。
  - 对稿：旁白合成那天（09-30）Gemini 转写的日配额已经用完，先用本机 whisper-large-v3-turbo 按 tts.py 的算法临时对了一遍：leo、far 1.00；s2g、s20g 按读音比 1.00（念的是"吉赫兹""千赫兹"）；why 和 zero 里的"频移"听成"平移"，hook 里的"信号"听成"型号"。Gemini 的词级时间 10-01 才补上，见下一条。
  - 2026-10-01 **词级时间**：在现成的 take 上跑 Gemini 对齐（gemini-3.5-transcribe），不重新合成。用的是一次性脚本 align_existing.py（不在仓库里），它调用 tts.py 自己的 transcribe → align_lines → asr_record，写进 timeline 的字段和 `--align gemini` 一样；`--min-sim 0.9`，复核的自定义词表加了"多普勒频移,频移,GHz,kHz"。每句的 `words` 和 `asr` 写进了 `audio/timeline.zh.json`（`timeline.json` 是同一份）。08:21 和 12:12 两次都只过了 1 次调用就被每日配额拒了，14:30 换了一个新的 API key 才跑完。配额什么时候重置没有查清：报错的倒计时指向北京时间 08:00，Google 文档却写每日配额在太平洋时间午夜重置（夏令时是北京 15:00），所以之前以为"08:00 重置后 21 分钟内就被用完了"，未必成立。
  - 逐句相似度（第一遍 → 带词表复核，只有第一遍低于 0.9 的句子才复核）：hook 0.53 → 1.00（第一遍听成"我已经信号回变调。"）、why 1.00、leo 0.82 → 1.00（"第一轨卫星飞的极快。"）、near 0.80 → 1.00（"靠近时拨便密，频率升高。"）、zero 0.86 → 1.00（"正头顶平移归零。"）、far 0.95（"远离时，波变频率降低。"）、s2g 0.50 → 0.94（旧 take："二级 THD在接近正负 50千赫兹。"；重录后的见下）、s20g 0.61 → 1.00（"20赫兹，再大十倍。"）、known 0.89 → 1.00（"轨道已知，能提前算准。"）、fix 0.75 → 0.75（"反向不长，补在变调。"，复核"补偿不再，不在变调。"，仍被标记）。复核的词表会把识别往稿子上拉，复核到 1.00 只说明这段声音可以听成稿子，不能证明念对了。
  - **待人听**（第一遍低于 0.9 的 8 句，再加 far）：fix 22.95–24.35 s 两遍都没过，"补偿""不再"可能声调不对；s20g 17.95–18.95 s 听成"20 赫兹"，要确认"吉"念出来了，不然意思就变了；s2g 15.0–15.8 s 的"2 GHz"（维护者听过：GHz 念成了 G、H、Z 三个字母，已重录，见下）；hook 0.3–0.6 s 的"卫星"；zero 10.2–10.7 s 的"频移"（whisper 也听成"平移"；why 里的"频移"这次听对了）；far 12.25–12.85 s 没听到"疏"（0.95 过了线，所以没复核）；leo 3.65–3.85 s 的"低轨"；known 21.75–22.05 s 的"算出"。near 的"拨便"和"波变"同音，可以不听。哪句真念错了，只能重录那一句。
  - 两处词级时间不可靠：fix 第一遍把"补偿，不再"听成"不长，补在"，"补偿"其实在 23.25–23.65 s，对齐却把"补"放到了 23.75 s（"补在"的"补"），"偿""不"成了 0 长度；far 的"疏"没被听到，也是 0 长度（12.45 s）。字幕不受影响：fix 一行放得下，lines.srt 只在两行的字幕里按词换行。
  - `bin/vh captions showcase/02-short-leo-doppler zh 11` 给 `captions.json` 加了 `words`，并写出 `captions.zh.lines.srt`：两行的字幕拆成一行一条，每条从这一行第一个字念出来时开始（near 在 8.15 s 换行，far 在 12.45 s）。`captions.zh.srt`、`captions.en.srt`、`captions.bi.srt` 逐字节没变，所以 `media/final.mp4` 没有重新封装（后来重录 s2g 时封装了，见下）。
  - `tools/build_audio.sh` 重跑：mix.wav 和全部 stems 与对齐前逐字节相同（mix.wav 的 md5 是 5baa1c5f…）。混音报告的遮蔽检查从按 0.4 s 一段（48 段里 6 %）改成逐词：78 个词里 7 个（9 %）低于 6 dB 的 presence 地板，没过 10 % 的上限，只警告。最危险的是 near 的"波"（7.35 s，−5.1 dB，压住它的是 7.4 s 那声信标 ping_02）、s2g 的"负"（16.10 s，+0.5 dB，音乐）、near 的"近"（6.75 s，+2.9 dB，ping_01）、far 的"率"（12.95 s，+3.3 dB，音乐）、why 的"频""移"（2.95 / 3.15 s，+4.4 / +5.1 dB，音乐和 3.2 s 的 whoosh 都有份）。第 7 个标成 fix 的"补"（23.75 s，+4.0 dB，音乐），那里其实念的是"不再"的"不"。混音没改。
  - 配乐：100 BPM（每拍 18 帧），D 大调，从 0.2 s 起（build_audio.sh 把谱子延后 0.2 s，节拍表也一起平移）。小节长度 [5, 5, 4, 4, 6, 5, 5, 5, 2] 让 3.2、6.2、14.6、17.6、20.6 都落在小节头上，最后正好 24.8 s。和声跟着物理走：靠近用 I，头顶用 IV，远离用 vi → ii，主和弦 D 落在 23.6 s（"补偿后 ≈ 0"）。
  - 配乐修改：S6a 本来是"屏息"，太弱，旁白两句之间降到 −30 dBFS，qa 报了掉音。改成持续的弦乐 + drone，bed 抬高 3 dB。进 S7 的 riser 去掉了：它的噪声盖住了"再大 10 倍"和 Ka 曲线出现那一下。
  - 音效：卫星信标的"声化"（sonification，事件带 `"layer": "sonification"`）。开场的音高跟着被挤紧、拉松的波变；过顶时每拍一声，音高按图表同一条多普勒曲线变化（夸张成 ±3 半音，和画面一样是示意），声像跟着卫星走；过零响一声钟，结尾两声同一个音高，就是"不再变调"。候选阶段另做过一版不带信标的，维护者两版都听过，选了带信标的这一版（2026-10-01）。
  - 第一版候选的混音：`duck=voice duck_ratio=1.6`，−14 LUFS。qa：无数字静音、掉音、抽吸，18 个 cue 全在 1 帧内；click 警告是旁白里的辅音（原始 take 里就有，7–29 个采样宽）。混音实验量出来它的 VMR 中位数只有 7.9 LU，最差一句 1.3 LU，句间音乐一度比人声还响 2.6 LU。
  - 还要听的（维护者听的是第一版候选，不是下面这版 profile 混音）：信标声会不会和旁白打架，它的滑音和配乐跑调；"不再变调"的两声平音听不听得出来；S6b 每拍一下 kick 的推进够不够。
- 2026-10-01 **定稿混音：profile `short`**（`bin/vh mix … profile=short`，playbook/04-audio.md 混音），维护者听过候选后定的。它取代了 ffmpeg 链（`duck=voice`）和"各条总线比片子长、混完再切"的绕路：profile 混音的信号路径里没有 ffmpeg 滤镜，截到片长和淡出都在混音里做（`dur=24.8 fade=0.3`），每次跑出来逐字节相同（查过）。
  - 软字幕轨（中、英）都不设成默认（`bin/vh mux --subs-off`）：画面里已经烧了中文字幕，播放器不该自己再叠一套上去；两条轨都还在，可以手动选。MP4 封装器总会把第一条字幕轨标成启用，`--subs-off` 把它 tkhd 里的启用位清掉，ffprobe 读出来两条都是 default=0。
  - 逐字节相同的前提（混音 WAV，以及加 `--mux` 时的 mp4）是这套工具链：ffmpeg 8.0.1、Python 3.14.7、numpy 2.5.3、scipy 1.18.1（经 uv 0.10.0，Apple Silicon 上的 macOS）。换了版本，混音和 AAC 码流的最低几位可能不同。
  - 旁白是锚点：10 句往中位数拉平（原始跨度 3.8 LU → 1.5 LU），峰值压在锚点 +10.5 dB（161 个峰，最多 2.5 dB）。配乐逐句压到 VMR 11.5 LU（10 句都在 11.2–11.6），1–4 kHz 只挖到词需要的深度，中文旁白连 250 Hz–1 kHz 一起挖；静态增益 −1.4 dB。
  - 音效：信标（`"layer": "sonification"`）是 signal 类，中位数在旁白下 3.9 LU（范围 −8…−2），和候选里差不多（−3.1）；过零钟声 −2.6、开场信标 −6.2。whoosh / swish_rev 是 detail（中位数 −8.6）。3.2 s 那一下 whoosh 从 −14 dB 改成 −18 dB：原来它的 1–4 kHz 离下面那句结尾的"频移"只差 4.6 dB（MASKS-VOICE），这个词本来就容易听成"平移"；改了以后混音里只低 2 dB（profile 往类中心走一半），但离人声超过 6 dB 了。Ka 曲线的 impact 是 hero，因为压在"再大 10 倍"上，按规则压到人声 −3 LU 以下（降了 4.5 dB）。音效共用一个短房间，盖住词的地方挖 1–4 kHz（最多 8 dB）。
  - 母带：静态增益 +3.3 dB，真峰值限幅器只碰了 6 个峰（最多 0.3 dB）：−14.00 LUFS，WAV 里 −1.65 dBTP，AAC 编码后 −1.63 dBTP（ffmpeg ebur128：−14.0 LUFS）。
  - `bin/vh qa`：无数字静音（只有片头 0–0.19 s，在检查区间外）、掉音、抽吸；18 个 cue 全在 1 帧内（中位 8.0 ms，最大 10.7 ms）；9 处 click 警告，全是旁白原始 take 里的辅音：单独扫旁白，8 处在同一个采样上；12.34 s 那处在旁白里是 14.9 倍，刚好低于 15 倍的门槛。
  - 混音报告（`qa mix`）通过，警告：S3 前 5.09–6.45 和 22.17–22.85 两个停顿里音乐回升 5.8 / 7.0 LU（前一个是设计好的 S3 起势，后一个是 S7 的 V→I 往主和弦走）；第 1、2、7 声信标的 1–4 kHz 离人声不到 6 dB（信标的设计本来就在人声上面响，保留）；Ka 的 impact 98 % 能量在 150 Hz 以下，手机外放会偏弱。
- 2026-10-01 **重录 s2g**：维护者听了待听的几处，s2g 确实把"2 GHz"的 GHz 念成了 G、H、Z 三个字母（稿子写的就是 GHz，TTS 照字母念了）。只重录这一句，其余九句的 take 一个采样都没动。
  - 念法改成"2 G赫兹：接近正负 50 千赫兹。"（G赫兹 是维护者说的念法；kHz 原来就念成千赫兹，这次直接写出来）。音色 Aoede、整体指示和这句的指示"报数字，利落"都和原来一样。字幕仍是"2 GHz：接近正负 50 kHz。"，`audio/script.txt` 的注释记了这个念法。
  - 出了 3 条候选（2.51 / 2.30 / 2.04 s）。Gemini 第一遍对这几个词不准，三条都听得乱七八糟（"二级核子仅仅政府…""二张合子…"）。本机两个 Whisper 模型（large-v3-turbo、large-v3）都把 c1 听成"二级赫兹接近正负50千赫兹"（"二级"就是"二 G"）；c2 有一个模型听成"重负"，c3 的 G 听成"涨""兆"。用了 c1。旧 take 两个模型都听成字母"GHz"。
  - c1 长 2.51 s，从原来的 14.90 s 起，到 17.41 s（原来 17.32），在 17.55 s 的期限之前。`audio/voiceover.zh.flac` 里只有 14.90–17.41 s 变了；FLAC 用 `-compression_level 12`，和原来的编码一样，解码逐采样等于拼好的 PCM。重新切出来的 `vo/zh/07.wav` 和 c1 逐采样相同。
  - 对齐只重跑了这一句（其余九句用缓存）：第一遍 0.10（"二级核子仅仅政府 50千核子。"），复核 1.00。和 c1 合成时按念法稿对齐的词级时间相比，"GHz"的起点晚了约 0.1 s（15.22 s，"G"其实在 15.10 s），其余的词相差不到 0.07 s。
  - 字幕：s2g 那一条的结束时间从 17.32 改成 17.41 s（`captions.zh.srt`、`.en.srt`、`.bi.srt`、`.zh.lines.srt` 和 `captions.json`）。
  - 混音：在原来的 `TP=-1.65` 下，AAC 编码的峰值到了 −1.41 dBTP，`build_audio.sh` 自动用 −1.84 重混。现在把 `TP=-1.84` 写进了脚本，一遍就出最终的混音。−14.00 LUFS，WAV 里 −1.84 dBTP，AAC 编码后 −1.59 dBTP；静态增益 +3.58 dB，限幅器碰了 13 个峰（最多 0.5 dB）。和旧成片相比，14–17 s 以外的声音只差 −26…−33 dB（整体增益和限幅的小变化），时间都没动。
  - `media/final.mp4` 重新封装：视频流原样拷贝（md5 和原来相同），两条软字幕仍然都不默认打开，连跑两次构建出来的 mp4 逐字节相同。qa：没有数字静音、掉音、抽吸；18 个 cue 都在 1 帧内；click 警告的位置和重录前完全一样，拼接点上没有；`bin/vh check` 没有黑场、冻帧、静音。混音报告：每句 VMR 11.2–11.6 LU（中位 11.5；s2g 的 VMRp10 从 7.6 升到 9.3）；逐词遮蔽 78 个词里 6 个（8 %）低于 6 dB，s2g 的"负"已经不在里面。
  - **待人听**：新的 s2g，15.0–15.8 s 的"2 G赫兹"。

## 自评记录
<!-- 每渲染完一个场景，对照 TASTE_CHECKLIST 写一次。格式：[场景 · 时间段] 联系表路径，然后列出 FAIL 的条目和改法 -->

### 第 1 轮（snapshot，19 个时刻）— snapshots/contact-sheet-1..3.jpg
[S1–S7 · 0–24.8s] 
- #3 FAIL: c3/c5/c9 字幕 13 字 × 72px = 936px，超出安全框宽 810px（c9 实测 x≈99–986）→ 改成 ≤ 11 字："靠近：波变密，频率升高""远离：波变疏，频率降低""反向补偿，不再变调"
- #1/#7 小问题: hook 第二行 会“变调” 的全角引号左右留白不对称，墨迹中心比第一行偏左 ~30px → 去掉引号，只用强调色
- #2 小问题: S3 地面天线只有 ~80px，"你"的存在感弱 → 天线放大 1.3 倍（同时改馈源点和信号波端点的几何）
- others PASS（一个强调色、无渐变/粒子、数字与 NOTES 一致、每 3–5s 有新画面）

### 第 2 轮（draft 渲染 + 接缝 strip）— out/check/sheet.png、seam1_push.png、seam2_zoom.png、reflow_s5_s6.png
[S1→S2 · 2.85–3.45s] seam1_push.png
- #14 FAIL: push-slide LEFT 读起来像淡出——S1 只移动 ~125px 就被 0.12s 的 opacity 淡掉，S2 从 +260px 进 → 位移加到 −380 / +420，入场 0.42s power4.out
[S2→S3 · 5.85–6.75s] seam2_zoom.png
- #14 FAIL: zoom-through 没有承载物——S2 以"你"(y=724) 为中心放大，S3 却以天线 (y=900) 为中心长出来，"你"在切点跳了 176px → S2 放大时同时下移 176px，"你"正好落到 y=900
[S5 · 14.0–14.7s] reflow_s5_s6.png
- #18 小问题: 卫星在 177° 被 clamp 住，停在地平线上 ~0.7s 不动 → 放开到 186°，把卫星图层移到地面色带后面，α>176° 渐隐 = "落山"
- others PASS（重排 14.6–15.6s 连续，无切）

### 第 3 轮（逐帧 strip，帧 91–100 / 182–191）— out/check/seam1_frames.png、seams_frames_v3.png
[S1→S2 · 帧 95–96]
- #14 FAIL: 帧 96（3.200s）整帧空白——S1 在 3.15–3.20 淡到 0，S2 的 opacity 0→1 从 3.20 起，于是有一帧两边都不可见，看起来是闪黑 → 去掉 S1/S2 的 opacity 淡变，只靠位移切（两侧都在运动中切）；S3 入场从 opacity 0.4 起而不是 0
- 附带发现：`hyperframes snapshot --at 3.2333` 拍到的是 tween 起点状态，而 render 的帧 97（同一时刻）已经走了 1/3；以 render 为准

### 第 4 轮（final 渲染）— out/check/final-sheet.png，`bin/vh check`
[S6a · 15.87–17.37s]
- #18 FAIL（freezedetect 1.67s）: 公式、刻度、字幕在 15.9s 前都落定，之后到 17.75s 画面不动 → 加一个读数：点沿 2 GHz 曲线再走一遍，右上角实时显示 +46 → 0 → −46 kHz（真实峰值），顺便把"接近 ±50"的"接近"讲清楚
- 第一版读数标签跟着点走，会压到曲线（+46 在 16.2s、−46 在 17.2s 都被曲线穿过）→ 改成固定在右上象限（下降的 S 曲线永远不进这个象限），64px tabular-nums
- 重渲后 freezedetect 仍报 15.87–17.37（1.5s）：移动的只有 26px 的点和数字，低于 ffmpeg 默认噪声阈值。人工看过，**接受**
[S7 · 23.5–24.8s] 结尾 1.3s 静止在平线上，刻意的回报停顿，PASS
- 其余：lint 0 error；check 通过（Runtime 0、Motion 0、Contrast 33/33 AA）；Layout 2 条 rotation_pivot_drift 是误报（卫星本来就沿轨道平移、天线碗绕底座转）

### 我自己最不满意的三处
1. S3–S5 画面上半部（y 330–500）只有一行小注释，天穹 + 图表压在中下部，竖屏上部略空。
2. S6–S7 全靠图表，扁平但"图表味"重；Kurzgesagt 式的具象回报（比如卫星本身出现在补偿那一刻）没做。
3. 读数点那 1.5s 按 freezedetect 仍算"冻结"；如果要更稳，可以让 2 GHz 曲线在这段轻微描边高亮。

## 素材台账
| 文件 | 来源 | 许可 |
|---|---|---|
| 卫星、地面天线、地球、曲线（index.html 内联 SVG / JS 生成） | 本项目原创 | 随项目 |
| Noto Sans SC | Google Fonts（渲染时由 HyperFrames 本地化） | SIL OFL 1.1 |
| GSAP 3.14.2 | jsDelivr CDN（HyperFrames 脚手架默认） | GSAP Standard License（免费） |
| audio/voiceover.zh.flac（旁白） | Gemini 3.8 Flash TTS，音色 Aoede，2026-09-30 合成；含 SynthID 水印 | AI 合成，按 Google 的服务条款使用；发布时标注 |
| audio/score.json → 配乐 | 本项目作曲，`bin/vh music` 纯合成（不用采样） | 原创 |
| 17 个自制音效（信标 ping、过零钟声） | `tools/foley.py` 代码合成，带种子 | 原创 |
| 内置音效（whoosh、swish_rev、impact） | `bin/vh sfx lib`（`tools/audio/sfx.py`） | MIT，本仓库 |
