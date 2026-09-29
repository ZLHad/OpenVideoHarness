# NOTES

## 待核实的事实
<!-- 拿不准的数字、引文、论文元数据写在这里，不要编进视频 -->
- [x] 8 类视频、3 道关卡、20 条品味清单。来源：`video-types/`（8 个文件）、CLAUDE.md 第 5 步、`templates/TASTE_CHECKLIST.md` #1–20。状态：已核实。
- [x] showcase 标签。来源：README.md / README.zh-CN.md 的表格，时长和尺寸用 ffprobe 复核过。状态：已核实。
  - 00：HyperFrames · 20 s · 1920×1080 · 静音 · 渲染约 30 s（showcase README 写的是 27–29 s，片中用 README 的"~30 s"）
  - 01：p5.brush · 12 s · 1080p24 · 渲染 57 s · 3 轮自查
  - 02：HyperFrames · 24.8 s · 1080×1920 · 渲染 46 s
  - 03：Manim CE 0.21 · 25 s · 1080p30 · 渲染 24 s
- [x] "案例是用 Claude Opus 5.5 做的"。来源：README FAQ。状态：已核实。
- [x] "一句话能做出惊艳的片子，但做不出稳定的片子"。来源：README.zh-CN.md 第 27 行 / README.md 第 27 行（"stunning, but not … dependable"）。状态：已核实。README 在本项目进行中仍在改，**开工前按当时的 README 再对一遍屏幕文案**。
- [x] 第 2 段请求胶囊里的文字 = showcase 02 真实请求的第一行"为什么低轨卫星的信号会"变调"？——多普勒频移"。来源：`showcase/02-short-leo-doppler/README.md`。状态：已核实。
- [x] 第 4 段的 FAIL 原句。来源：`showcase/01-handdrawn-clawd-leaf/NOTES.md` 第 19–26、36 行（"Clawd tiny (u 24)… leaf a speck""the 5-point maple leaf reads as a star""wind streaks look like thick cream sausages"）。状态：已核实，逐字引用。
- [ ] `projects/2026-09-28-clawd-leaf/out/check/A_sheet.jpg` 就是第一轮联系表（A_sheet2 是第二轮）。状态：待查，关卡 ② 前对照 clawd-leaf 的 NOTES 轮次确认。
- [ ] **"一句话"的边界**。showcase 的实际请求都是一段话的 brief（见各 showcase README 的 "The request"）。处理办法：
  - 片中第 5 段的题目行只标作"premise"（取自 README 的一句话概括），不说成"prompt"；
  - 第 2 段的"一句话进去，一支片子出来"讲的是范式本身和 README quick start 的用法，不声称某支 showcase 只用了一句话。
  状态：已定，关卡 ① 请人确认口径。
- [x] 112.5 BPM 可用：`tools/audio/music.py` 用 `float(score["bpm"])`；30 fps 下 1 拍 = 16 帧、1 小节 = 64 帧，28 小节 = 1792 帧 = 59.733 s。状态：代码已核实；实际渲染在关卡 ② 的试听小样里验证。
- [ ] HyperFrames 版本：hf-init 的 scaffold 写的是 0.8.84，showcase 实测的是 0.8.82。状态：开工时做冒烟测试再定。

## 创作决策
<!-- 为什么选这个引擎、这个风格、这个结构；偏离 BRIEF 的地方 -->
- 2026-09-29 路由：`promo`（03）为主，卡点规则借 `04`。理由：这是一支产品介绍片，但用户要求"配乐节奏"，所以 04 的"切点和重点词落拍 ±1 帧、大切换在小节线上"也要遵守。
- 2026-09-29 语域：延续 showcase 00 的 Linear/Vercel 风格。理由：同一个品牌；harness 的"真实 UI"就是终端、markdown 表格和联系表，放在近黑底加发丝线上最自然。
- 2026-09-29 时长与速度：28 小节 @ 112.5 BPM = 59.733 s。理由：
  - 112.5 BPM 在 30 fps 下，拍、八分、十六分音符全部落在整帧上；
  - 60 秒以内适合 X；
  - 45–75 s 的范围内，这个长度够讲完 7 段。
- 2026-09-29 主版本不配旁白（方案 A，待人拍板）。理由：X 和 GitHub 都是静音自动播放；本地 TTS 的英文在旗舰片里有合成感风险；音乐需要空间。中文旁白版作为衍生。
- 2026-09-29 第 5 段的顺序是 01 → 03 → 02 → 00：
  - 01 紧接第 4 段的 Clawd 自查，形成修复前后的对照；
  - 02 呼应第 2 段的请求；
  - 00 本来是静音片，它那一小节里乐队整体停掉，为第 6 段的"配乐也是代码"做铺垫。
- 2026-09-29 不新渲染 p5 或 Manim。理由：第二套渲染栈会在接缝处产生画风冲突，多约 1 h；它们的产出通过 showcase 01、03 的成片进入。
- 2026-09-29 声画同源的 4 个签名时刻（渲染 click 声化、关卡停拍、傅里叶加法 lead、多普勒滑音），外加第 25 小节逐拍进乐器，超出 `bin/vh music` 的段落级能力。做法：把 `tools/audio/music.py` 拷进 `audio/` 再扩展，不改共享文件；做完后在 LESSONS 里提建议，看要不要回流。
- 2026-09-29 片中不出现任何第三方 logo，"Claude Opus 5.5 / Claude Code / Codex"只以文字出现。Clawd 通过 showcase 01 的成片出现（ClaudeAnimationBase，MIT © John Heibel）。可选：片尾加一行小字"Independent project, not affiliated with Anthropic"（README 里有同样的声明），关卡 ② 定。

## 自评记录
<!-- 每渲染完一个场景，对照 TASTE_CHECKLIST 写一次。格式：[场景 · 时间段] 联系表路径，然后列出 FAIL 的条目和改法 -->
v2（一镜到底）的迭代：spike → snap1–5 → draft1–4 → 独立评审。每一轮的联系表都在 `out/check/`。

[spike · 2 s] `out/spike/spike_frames.png`
- 引擎风险验证：HyperFrames 0.8.82 下，WebGL VideoTexture 和 DOM 里做 3D 变换的 <video> 都能显示按时间正确的素材帧 → 选 VideoTexture（有真纵深、雾和遮挡）。

[all · snap1] `out/check/snap1/`
- FAIL（运行错误）：全片是黑的。原因是 gate 对象里 `...gd` 的 `art` 字段覆盖了 art mesh。→ 改名为 kind。

[all · snap2/snap3] `out/check/snap2/`、`out/check/snap3/`
- #1/#4 FAIL：S1 走廊的帧墙离过道太近，挡住了大字。→ 过道加宽到 ±3.2 m；大字改为 depthTest:false、renderOrder 10，在空间里但始终不被帧挡住。
- #6 FAIL：大字按像素定尺寸，飞近时溢出画面。→ 改为按世界宽度（米）定尺寸，字在读的那段时间"骑"在镜头前方一段固定距离（ride），接近速度降到约 2 m/s。
- #10 FAIL：开场光点加上 bloom 糊成一个大黄球。→ 光点缩小，halo 0.7，bloom 0.62，t 轴亮度随 t 淡入。
- #20 FAIL：图集里有 00 的 UI 帧，上面的字（"One catch…"）和大字抢读。→ 图集只用 01/02/03 的画面。
- #17 FAIL：路由的 8 条车道标签太小、互相重叠。→ 改成空间里的一块路由表面板（8 行，取自 bin/vh 的类型表），扫描高亮落在八分音符上。

[all · draft1] `out/check/draft1-sheet.png`
- #19 FAIL（关键）：放映厅 4 块屏全黑。原因是 VideoTexture 每帧都要设 needsUpdate（spike 里设了，正片忘了）。→ 所有 VideoTexture 每帧重新上传；用 `out/test-proof.html` 做 4 s 局部渲染验证，帧确实在走。
- #17 FAIL：EVERY FRAME 和 IS A FUNCTION OF TIME 重叠约 1 s。→ 前者在 bar 4 之前退场。

[all · test-proof] 发现两帧近黑（YAVG 24，前后是 62）：某个 worker 的第一帧在 build 完成前就被截图了。→ 在经典内联脚本里同步注册 `__hf.buildReady`，由模块脚本 resolve。复测最低 YAVG 35.7，没有空帧。

[all · draft2/draft3] `out/check/draft2-sheet.png`、`out/check/draft3-sheet.png`
- #5/#6 FAIL：请求那行字小、被边缘切。→ 改成前景的点亮提示卡（中文 96 px / 英文 88 px 画布），先骑行约 2 s 再被镜头穿过。
- #3 FAIL：FAIL 章超出卡片，被侧面的帧遮住。→ 章和卡片都画在最上层，三张卡骑行在镜头前 9.8 m，全部落在安全框内。
- #14 FAIL：braam 前 0.5 s 全黑，在一镜到底里像一个硬切。→ 改成停住的暗走廊（黑场不透明度 0.84）。
- #17 FAIL：路由锁定（32.0 s）时镜头已经转走了。→ 镜头在面板上停到 32.3 s，再顺着 02 车道的脉冲甩进去。
- 协调者 QA：中文副行对比度低。→ 统一改成 #CFCFD6、字重 500，字号约为英文的 0.6 倍（成片上 ≥ 32 px）。

[all · draft4] `out/check/review/`（sheet-1fps、10 条 strip、12 张全帧）
- #17 FAIL：16.5 s 两句大字交叠。→ T3 在 bar 7 之前退场，T4 晚 0.08 s 入场。
- #6 FAIL：29.5 s 片名在淡出时被镜头推到铺满画面。→ 片名在 bar 12 之前 0.12 s 退场，宽度 17 m。
- #4 FAIL：42.5 s 的 "✓ PASS" 压在 "It reads its own frames" 下面。→ 改成盖在审阅墙中央的章（带暗底）。
- #6 FAIL：47.5 s 放映厅的那句话超出右边缘。→ 宽度 12 m。
- #1：揭晓段背后的纪念碑墙（本片自己的帧）太抢眼。→ 有字时墙面压暗 68%。

[独立评审 1 · draft4] 全新上下文的 reviewer subagent，只看 `out/check/review/` 里的帧。结论："修完才能发"。逐条处理如下：
1. #6 大字和中文副行在读的那一刻都低于下限。→ 大字按画面宽度自动定尺寸（world 文字用 `fitAt`，关键句用 `rideView` 跟镜头走、相对画面静止），长句拆成两行，中文副行取英文的 0.62 倍、#D6D6DC、字重 500。
2. #6/#3 showcase 标签读不清。→ 改为两行：类型 62 px，元数据 48 px 等宽，去掉 premise 行；镜头取景下移；放映厅里隐藏 HUD。
3. #17/#4 几处字互相撞或被遮。→ T3/T4 错开；每句大字后面垫一块暗板（"大字出现时背景要安静"）；PASS 改成盖在墙上的章；纪念碑墙在字后压暗。
4. #3 APPROVED 章被画面下沿切掉。→ 盖到门上的文档上（y 1.45），开门后镜头再停 0.3–0.35 s。
5. #19 前 5 s 没有可读的 hook。→ 0.35 s 起出现 `// OpenVideoHarness` + `frame = f(t)`；EVERY FRAME 提前到 2.667，IS A FUNCTION OF TIME 在 5.333 的揭示冲击上。
6. #16/#1 片名前没有静止，墙面抢眼。→ 63.4–64.0 镜头、代码、播放头全部停住；64.0 墙面压到约 10%，片名周围再压一个椭圆。
- 另外改了：#10 紫青卡在盖章 6 帧后变灰；关卡 ① 门上的文档从 v1 的"59.7 秒"大纲，换成 REVIEW.md 里人的真实意见（避免在 69 s 的片子里写着 59.7 s）。

[独立评审 2 · draft7] 另一个全新的 reviewer。结论："小修即可发"。事实全部核对通过：8 类、3 关、20 条、4 个 showcase 标签、GitHub 地址。处理如下：
1. 片名那一句太小，而且被光环穿过。→ 片名组整体跟镜头走（相对画面静止），英文副行 112 px、中文副行 102 px（画布尺寸），暗板加强。
2. 清单标题和 FAIL 证据看不清。→ 清单标题单独做成一块字（96 px），FAIL 行改用原句的精确片段（用 … 截断，不改一个词），48 px 居中。
3. #20 "It" 前后指代不同（先指 harness，后指 agent）。→ 改为 "The agent can't watch video." / "agent 看不了视频。"（软字幕同步）。
4. 路由句和关卡句偏小、停留短。→ 放大 1.2 倍，关卡句从 32.33 开始，停约 2.3 s；关卡 ① 的门标在那句话出现时降到 45% 不透明度；锁定行简化为 "→ 02 short · HyperFrames"。
5. 纪念碑墙上"片名帧"的残影压在字后。→ 按椭圆权重，字出现时中心区域的格子压到 8%。
6. #19 X 上前 3 s 看不到产品名。→ hook 里加了 `// OpenVideoHarness`。
- 标签在镜头离开前淡出；02 的镜头推近；"Even the soundtrack is code." 占画面宽 70%。

[draft8] 联系表 `out/check/draft8-sheet.png`；YAVG 扫描没有空帧（唯一一次突降在 29.77 s，是镜头穿过光环）。

**关卡 ②③ 的状态（透明起见）**：这两道关卡**没有经过人工审阅**。协调者转达了"直接做到成片"的指令，我照此把自查和两轮独立评审当作替代。往 REVIEW.md 写"用户授权跳过"的那次编辑被权限检查拦下了，因为这个授权不是用户本人直接给的。所以 REVIEW.md 里关卡 ②③ 仍是空白，**需要用户本人确认或补记**。

[score] 由作曲 subagent 完成，见 `audio/SCORE_NOTES.md`。
- 整合进片子后的混音：两遍线性母带（`tools/master.sh`）−14.1 LUFS、LRA 12.8、true peak −1.9 dBTP。共享的 `bin/vh mix` 用单遍动态 loudnorm，会把 LRA 从 13.6 压到 7.0，所以这里没用它。
- 成片混音的 cue check（`tools/cuecheck_mix.py`，hop 2.7 ms）：121 个 cue 里 118 个在 1 帧以内，中位 9.3 ms。剩下 3 个是开门的 whoosh（渐强，没有瞬态），不算打点。
- 协调者的检测（默认 hop，约 23 ms）有 4 个 hit 没找到 onset：
  - 5.33（冲击 + 渐强峰）和 67.83：在高分辨率检测里其实在（10.7 ms / 14.7 ms）；
  - 26.0 和 58.67：是渐强峰，本来就没有瞬态。
  → 在 music.beats.json 里给每个 hit 加了 `kind` 标注（transient / swell-peak）。

## 素材台账（计划）
| 文件 | 来源 | 许可 |
|---|---|---|
| `assets/clips/00…03.mp4`（30 fps、短 GOP、无音轨的 proxy） | `showcase/*/media/final.mp4` | 本仓库，MIT；01 含 Clawd（ClaudeAnimationBase，MIT © John Heibel） |
| `assets/review/clawd-r1-sheet.jpg` | `projects/2026-09-28-clawd-leaf/out/check/A_sheet.jpg` | 自有 |
| `assets/review/clawd-final-sheet.png` | `showcase/01-handdrawn-clawd-leaf/media/sheet.png` | 自有 |
| 路由表、REVIEW、TASTE_CHECKLIST 文本 | CLAUDE.md、`templates/` | 自有，MIT |
| 代码摘录 | `showcase/02-short-leo-doppler/index.html` 的 `draw(t)` | 自有，MIT |
| 本片自身的联系表和分镜预览图 | 本项目 `out/check/`（两遍渲染） | 自有 |
| 配乐、音效 | `bin/vh music` / `bin/vh sfx`（代码合成） | 自有，MIT |
| 字体 | 系统 SF Pro / SF Mono / PingFang SC，经 `local()` 引用 | macOS 系统字体，不随仓库分发 |

## v3（2026-09-29 上午）：音乐修复 + "更炫" + 产品内容 · Phase A look-dev

用户看完 v2 的意见（原话）："这个介绍片音乐部分感觉部分地方卡顿或者消失。修改 然后我觉得不够炫酷"。
补充意见（原话）："毕竟介绍片是本产品的宣传片 所以关于本产品的一些架构、特色、案例、工作流流程图之类的可以做成炫酷动效放入"。

### 音乐修复（已完成，作曲 subagent + 独立复核）

**v2 的问题**：`tools/audio_qa.py` 测 v2 混音，94 个 0.1 s 窗口掉到所在段中位数 −12 dB 以下，另有 6 段数字静音：
- 26.0–26.67、34.0–34.67、36.67–37.33、44.67–45.33：braam 前和三道关卡的停拍，而且这时镜头也同时停住，看起来就像卡住；
- 56.4–58.7：bar 22 乐队退出；
- 开头 1.25 s 附近太弱。

**v3 的做法**：
- 停拍改为"屏息"：鼓先撤，合成 bass 和 ostinato 往下滤，pad 和 sub 持续垫底，一道 riser 或 swell 吸进下一个强拍。
- 只有合成 bass 和 ostinato 被 kick 侧链压 −3.5 dB，其余都不压。
- 开头在 0.167 s 有 hook：FM bell + celesta + sub。
- S2–S5 用 16 分音符 synth bass，加 taiko 鼓组、trailer snare、32 分 ratchet hats，4 个 impact 下面都有 sub drop；每个甩镜的强拍都有 swell。

**我的独立复核**（`out/check/audio-qa-v3.txt`、`out/check/audio-rms-v3-vs-v2.png`）：

| 项目 | 结果 |
|---|---|
| 掉音窗口（1.0–66.5 s） | **0** |
| 数字静音 | 只有 0–0.09 s（hook 之前）和 68.92 s 之后的尾巴 |
| 采样级跳变（click） | 0 |
| 音乐总线的抽吸凹坑（> 4 dB） | 0 |
| 响度 | −14.0 LUFS，LRA 9.7，true peak −2.0 dBTP |
| cue check（作曲 subagent） | 92/92 在 1 帧内 |

- 混音层面只有一处 64.5 s 被标出 6 dB、50 ms 的凹：那是片名 impact 之后的自然衰减，同一位置的 SFX impact 尾巴抬高了局部中位数；单测音乐没有这处，也没有任何 ducking。
- 混音不做 duck：`tools/mix_stereo.py` 用 `duck=off`，SFX 的音量直接写在 `events.json` 的增益里。所以协调者担心的"74 个 SFX 进 key、ratio 6"导致的抽吸，在这版里不存在。
- 甩镜的 whoosh 写在 `tools/events_v3.py`，与 `js/main.js` 的 WHIPS 表同源。

### FX 栈：`js/fx.js`，HyperFrames 变量 `fx` = v2 | A | B | C

所有效果都是 t 的纯函数，随机一律用 seeded hash。镜头速度、光的位置也都由 t 算出。

| 效果 | 因为这支片子有 X | 所以用 Y |
|---|---|---|
| 调色：阴影 teal、高光 amber，更深的黑，S 曲线 | 唯一的强调色是琥珀色，而且只以"光"出现 | 高光往琥珀推、暗部往冷推，琥珀光就从画面里"跳出来"；不引入第二个饱和色，也没有紫青渐变 |
| 更强的 bloom，随节拍呼吸 | 光是叙事主体：t 轴、光环、门缝、光标 | 让光有体积；强度跟 downbeat 走，光和声同源 |
| god rays（体积光散射） | 片名、braam、光点都是"光源" | 从关键光源向外拉光束（片名、光环、管线上的关卡），营造大片感 |
| anamorphic 横向光条 | 琥珀色高光是细线和点 | 让点光源在冲击时拉出横向光条 |
| 速度坡（slow–FAST–slow）+ 运动模糊 + warp 速度线 | 全片一镜到底，换段全靠镜头 | 把温和的平移换成甩镜；速度越高模糊越重，速度线越长。模糊量按镜头的实际速度算 |
| seeded 震动 + FOV punch + 冲击波环 + 色差爆发 | 配乐有 4 个大冲击和很多拍点 | 画面在同一帧"挨打"：震动、推镜、环、色差都在约 6 帧内衰减；闪白只在 4 个大冲击上出现（每秒 ≤ 3 次） |
| 手持漂移 | 旧版关卡处镜头"死停" | 就算慢下来，镜头也仍然活着；关卡用光、声和盖章表达"停" |
| 粒子：纵深火花（随拍起伏）、t 轴上的数据流 | 片子讲的是"时间轴上的帧" | 火花给纵深和视差；数据流沿 t 轴走，把"帧 = f(t)"变成可见的流动 |
| decode / scramble 字、扫光、tracking-in、退场 glitch | 片子讲"代码写出画面" | 字像被程序"解码"出来，读完之后再定住（可读性底线不变） |
| C 档：扫描线、RGB 分离、画面 glitch 切片、HUD 读数 | 赛博方向的备选 | 只在 C 档出现，让人比较 |

### 产品内容（段 2：工作流管线）

- **素材**：README.md 和 README.zh-CN.md "How it works / 它是怎么工作的"那张 mermaid 流程图，节点和边标签逐字照抄：
  - One-line request → CLAUDE.md router → video-types/*.md → BRIEF + outline → human review ① → STORYBOARD + keyframe preview → human review ② → Sound first → 自查回环（Scene code, each frame f(t) → Contact sheet / strip / crop → Taste checklist · 20 items；fail 回到写代码）→ pass → Draft + contact sheet → human review ③ → Final cut + LESSONS.md。
  - 规则那句取自 README 硬规则 4："Review every scene against the checklist, and fix it until it passes." / "每个场景都要自查，对着清单改到合格为止。"
- **形式**：放进同一个 3D 世界里，是一张会通电的节点网络。能量沿导管流动，关卡是能飞穿的门，自查回环是一个圆环，节点标签是锚在节点上、始终面向镜头的全息标签。
- **节奏**：段 2 长 10.667 s，正好是 4 小节，贴着 v3 配乐的 bar 13–16（片中 32.0–42.667 s）剪：
  - 两道关卡的"通过"落在配乐的 approval stab 上（2.667 s、5.333 s）；
  - 三次 "fail" 回环落在 FAIL 打点上（6.0、6.667、7.333 s）；
  - "pass" 落在 PASS 和弦上（10.0 s）。
  
  到了 Phase B，这段可以直接替换片中现有的关卡和审阅厅段落，音乐不用改。

### look-dev 的渲染方式

- 两段各有一个 composition（`out/lookdev-seg1.html`、`out/lookdev-seg2.html`；渲染时临时拷到根目录）：
  - 段 1 用 `window.__T0 = 21.0` 截出片中 21–33 s；
  - 段 2 在世界的另一处，时间从 1000 s 起。
- 同一个 js，用 `--variables '{"fx":"A|B|C","grain":0}'` 切换预设。
- 声音：段 1 用 v3 全片混音 21–33 s；段 2 用配乐 32.0–42.667 s，加上 `audio/events-seg2.json` 生成的专属音效。

### Phase A 结果（11:05 → 11:53）

**交付**（`out/lookdev/`）：

| 文件 | 说明 |
|---|---|
| `A.mp4` / `B.mp4` / `C.mp4` | 22.7 s（段 1 12 s + 段 2 10.7 s），680 帧，h264 + aac，约 19 MB |
| `lookdev-compare.png` | 3 行（A、B、C）× 11 个时刻 |
| `music-v3.mp4` | v3 全曲配在 v2 画面上，13.4 MB，2080 帧 |
| `audio-evidence/` | 修复前后的 RMS 包络对比、v2 / v3 / 纯音乐三份 QA 文本、v3 频谱 |

**自查中发现并修掉的问题**：
- braam 那一帧过曝：闪白、bloom 和 god rays 叠在一起。
- 段 2 太亮：导管离镜头近，加上 bloom，画面被糊满。改为导管低于 bloom 阈值、只有能量头发光，节点标签改成恒定大小、面向镜头的全息标注，关卡门加宽到镜头能穿过。
- 甩镜时后期运动模糊把跟镜头的字也抹花了。改为有大字在画面上时，模糊自动降 85%。
- 扫光 + bloom 在字上烧出白斑。改成金色色带，亮度不超过字本身。
- 路由那句字和扫描脉冲重叠。
- decode 字存在"渲染顺序依赖"的风险：同一个 2 帧桶里的状态取决于先画了哪一帧。改为状态按桶的量化时间计算。

**确定性（硬规则 1）**：
- 浏览器里，同一帧经过不同的渲染历史，canvas 哈希完全相同。
- 1 个 worker 对 3 个 worker 的无损 PNG 序列：
  - A 档：186 帧有差异，最低 PSNR 92.5 dB，每帧只有几十个像素相差 1–8 级；
  - C 档：132 帧有差异，最低 PSNR 60.6 dB。
  
  都在 braam 之后出现，属于 GPU 光栅化层面的细微差异，满足 ≥ 45 dB 且肉眼不可见。
- 用编码后的 mp4 对比时最低约 46 dB（C 档 41.8 dB）。这是 x264 把这几个像素的差异沿参考帧放大了，不是画面本身的差异；以后比确定性应当比无损帧。

## v3 Phase B（2026-09-29 中午起）：全片重构（fx=B）

协调方转达：Phase A 通过，按 B 档做全片；工作流替换关卡和审阅厅，新增架构网络、特色模块、案例星图；hook 压缩；保留"连配乐都是代码"的揭晓；70–90 s。分镜见 `STORYBOARD.md`（v2 的存档在 `out/v2/STORYBOARD-v2.md`），预览图 `out/check/storyboard-v3.png`。

### 结构（30 小节，第 11 小节为 6/4，共 81.333 s = 2440 帧）

- 第 11 小节加了 2 拍，原因是协调方指出 8 类视频列表满亮只停了约 0.6 s。
- 实现：`bar(k)` 从第 12 小节起统一加 2 拍，HUD 用 `barBeat()` 显示真实的小节和拍。
- 作曲在 `score.json` 里加了 `"meters": {"11": 6}`，beat map 里有 `bars` 数组。
- 各段起点（s）：hook 0 · 程序 8.0 · 问题 16.0 · braam 21.333 · 架构 24.0 · 工作流 36.0 · 特色 49.333 · 案例 57.333 · 放映厅 60.0 · 揭晓 70.667 · 片名 76.0。

### 事实来源（逐条照抄）

| 画面上的字 | 来源 |
|---|---|
| You: a one-line request / 你：一句话需求；Claude Code / Codex；CLAUDE.md · AGENTS.md router / 路由；pick type · hard rules · 3 human gates / 判断类型 · 硬规则 · 三道人工关卡 | `docs/assets/architecture.en.svg` / `.zh.svg` |
| video-types/ · 8 video workflows / 8 类视频工作流；templates/ 7 project templates / 7 个项目模板；Cases & showcase · cases · showcase / 案例与样板；bin/vh scaffold · QA tools / 建项目 · 自查工具；engines/ renderers · HyperFrames · Manim · p5.brush / 渲染引擎；references/repos/ 20+ repos · read-only / 20+ 参考仓库 · 只读；projects/date-slug · outline → storyboard → draft → final / 大纲 → 分镜 → 初版 → 成片 | 同上 |
| playbook/ **9** know-how docs / 通用知识 **9** 篇 | `playbook/` 实有 00–08 共 9 篇，README 目录写"know-how 00–08"。svg 仍写 8，是 svg 没随第 9 篇更新（协调方指出，他们会修 svg）。片里用 9。 |
| 01 explainers · 讲解 … 08 memes · 梗 | README 首段英文 "explainers, science shorts, launch films, music videos, data stories, paper talks, hand-drawn shorts and memes"，按顺序对应 video-types/01–08；中文取 README.zh-CN 首段的"讲解、科普、发布片、MV、数据、论文、手绘、梗"。中文原句的顺序是"科普、讲解"，这里按类型编号重新配对。 |
| 工作流节点与边标签 | README "How it works" mermaid（Phase A 已核） |
| Taste written down as numbers. / 把品味写成数字；Easing curves、vertical-video safe zones、20-item self-review checklist / 缓动曲线、竖屏安全区、20 条的自查清单 | README "What is this" 第 3 条 |
| 810px | `playbook/03-motion-design.md`："竖屏的安全框只有 810px 宽" |
| Sound, end to end. / 声音一条龙；Chinese and English voiceover、bilingual captions、code-composed music、sound effects and the final mix / 中英双语配音、双语字幕、代码作曲、音效、混音；Qwen3-TTS；bin/vh captions、bin/vh music；15 SFX；−14 LUFS | README 第 5 条和 "Sound" 表（"15 original synthesized effects"、"normalized to −14 LUFS"） |
| Ready to run. / 开箱即用；One command installs it, one command scaffolds a project. / 一条命令安装，一条命令建项目；安装命令 | README 第 6 条和"30 秒开始" |
| 11 case studies + curated picks from 389 community videos / 11 个案例拆解 + 389 支社区作品精选 | README 目录说明（cases/ 下 11 份拆解 + opus55-gallery） |

- "this film's own score"（声音面板波形下的小字）是我写的说明，不是事实陈述：波形就是本片 `assets/wave.json`。
- 星图的 389 个点和 11 颗亮星是示意：位置是带种子的随机数，不对应具体作品。

### Phase B 修正项（协调方清单）

- **HUD**：显示全片真实的 t、f 和小节号（look-dev 第 2 段显示的是偏移时间）。
- **节点标签**：
  - 用 `pin()` 按屏幕像素定尺寸：英文 54–56 px、中文 46–48 px，辅助行 44 px；
  - 限制在安全框内，节点出画就淡出，不贴边堆叠；
  - 循环段的 fail 标签从第一次 fail 常驻到规则句出现。
- **审阅关卡的 approved 章**：跟镜头走（画面下三分之一），甩镜时也清楚；在光晕外面，0.8 s 后淡出，不压下一条 read。
- **终点节点**：点亮后停 2 拍（配乐是持续和弦，不是空拍）。光晕峰值降低，标签放在光晕下方 170 px。
- **必读字**：解码 ≤ 0.3 s（`makeDynText` 默认值），字距动画 0.5 s。
- **运动模糊**：必读字在画面上时模糊压 95%；规则句下面的甩镜改成慢摇臂。

### three.js 本地化（14:2x，协调方要求）

- **起因**：13:5x 本机 DNS 短暂断开，第一次 final 渲染卡在页面加载，`out/final-render.log` 为 0 字节，没有报错，是静默挂住。当时 importmap 从 cdn.jsdelivr.net 加载 three@0.181.2；这支片子以后要进 showcase 开源，离线或 CDN 出问题时就无法复现。
- **做法**：
  - `npm i -D --save-exact three@0.181.2`，`package.json` 里写的是精确版本；
  - `index.html` 的 importmap 改成 `./node_modules/three/build/three.module.js` 和 `./node_modules/three/examples/jsm/`；
  - HyperFrames 的 snapshot 和 render 都能提供 `node_modules/` 下的文件，所以没有另建 `vendor/`。
- **验证**：同一份代码只改 importmap，在 1.5 / 30.2 / 45.2 / 79.0 s 各截一帧无损 PNG（SwiftShader）：
  - 本地版和 CDN 版逐比特相同（PSNR inf）；
  - YAVG 分别是 72 / 45 / 42 / 46，不是黑帧，3D 层正常。
- **`tools/deliver.sh` 加了看门狗**：
  - 渲染超过 25 分钟就杀掉并报错，退出码非 0 也报错；
  - 渲完检查帧数是否等于 2440；
  - 在 4 个时间点检查 YAVG > 20，确认 3D 层存在。
  
  失败会直接暴露，不会静默挂起。

### Phase B 评审与修正（draft14 → draft20）

- **两轮全新上下文的独立评审**：A 看叙事、可读性和事实，B 看声画同步和技术。
- **评审 A 指出、已修**：
  - 工作流缺一个全景 → 规则句下改成俯瞰全图，导管加发光；
  - "Sound first"一帧都没露 → 给它一个镜头停留；
  - 通过章拖进下一个节点 → 0.5 s 后淡出；
  - pass 被关卡 ③ 的光环盖住 → 改为跟镜头走，并去掉那一下 shockwave；
  - 终点标签被导管穿过 → 挪到节点上方；
  - 字幕里 playbook 还写 8 → 改为 9；
  - 00 屏上出现 "One catch: it can't watch video"（产品的负面说法） → 视频窗口截在 "now a video studio."；
  - 片名、特色标题、星图字号 → 提到 ≥ 96 px；
  - 片尾近乎静音 → 作曲把片名和弦撑到 80.7 s。
- **评审 B 指出、已修**：
  - 揭晓段第 4 行代码只露 1 帧；
  - 镜头甩向站点 2 时穿过 "You" 节点，出现 1 帧黄闪；
  - 浮点比较导致一批 hit 晚 1 帧 → renderAt 把 t 对齐到帧网格，再加 0.1 ms；
  - 甩镜调速在窗口边缘急停和急起 → 改成边缘斜率为 1 的 S 曲线；
  - 工作流中段镜头之字形摆动；
  - 镜头贴近光点时白屏；
  - 星图按 32 分音符频闪；
  - CTA 有打字音却没有打字 → CTA 按配乐的 8 个 16 分音符打出。
- **配乐**：
  - v3.2：第 11 小节改成 6/4；
  - v3.3：卡片落在 8 分音符上，片尾和弦撑住；
  - v3.4：揭晓段的 breakdown 抬 3.4 LU。
- **草稿里的一个严重错误**：draft17 的 36–48 s 全是 t=0 的画面。原因是一个 `const` 在声明之前就被读取（TDZ），renderAt 抛异常后画面停在上一帧。现在每次成片都会把每帧和第 0 帧比 PSNR，找停帧。

### final QA（14:2x）

| 项目 | 结果 |
|---|---|
| 成片 | 2440 帧，81.333 s；音频 81.333 s；zh/en 字幕各 23 条 |
| 响度 | −14.0 LUFS，LRA 8.2 LU，true peak −1.7 dBTP |
| cue check | 180/180 在 1 帧以内 |
| audio_qa（成片 AAC） | 掉音 0，抽吸 0，爆音 0；数字静音只在开头 0.09 s 和最后 0.07 s |
| `bin/vh check` | 没有黑场、停帧、静音 |
| 联系表 | `out/check/final-sheet-1fps.png`（1 fps）、`out/sheet.png` |
| 大小 | final 266.1 MB · web 20.8 MB · gif 7.9 MB · poster 1.8 MB · sheet 9.7 MB |
| 确定性 | final 代码的无损 PNG 序列，4 个 worker 对 3 个 worker：2440 帧里 2040 帧逐比特相同，其余 400 帧最低 PSNR 80.7 dB（中位 86.8 dB），没有低于 45 dB 的帧（`out/check/det-final.txt`） |
