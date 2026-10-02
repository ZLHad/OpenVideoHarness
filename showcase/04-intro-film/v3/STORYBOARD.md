# STORYBOARD v3：一镜到底 · 产品宣传片（camera path）

<!-- v3 Phase B（2026-09-29 中午）。v2 的分镜存档在 out/v2/STORYBOARD-v2.md。
     用户意见（原话）："这个介绍片音乐部分感觉部分地方卡顿或者消失。修改 然后我觉得不够炫酷"；
     "毕竟介绍片是本产品的宣传片 所以关于本产品的一些架构、特色、案例、工作流流程图之类的可以做成炫酷动效放入"。
     Phase A 的 look-dev 选定 fx=B。时间以 js/*.js 为准，与 audio/score.json 共用网格。 -->

**Logline**：同一台摄像机、同一条时间轴 t。开场的 hook 压缩到 3 小节；harness 出现之后，镜头依次穿过它的**架构网络**，钻进 `projects/` 节点，沿着**工作流流程图**一路走到成片，再掠过三块**特色模块**、一片**案例星图**和**放映厅**，最后拉远看到这支片子自己的联系表，揭晓"连配乐都是代码"，片名落下。

**变化（相对 v2）**：
- 删掉：路由车道、三道关卡门、审阅厅。它们的内容由"架构网络 + 工作流流程图"承担，信息更全，而且都来自 README 和架构图的原文。
- 新增：架构网络（第 10–13 小节）、工作流（第 14–18 小节，由 look-dev 第 2 段扩成 5 小节）、特色模块（第 19–21 小节）、案例星图（第 22 小节）。
- hook 压到 3 小节，S2 压到 3 小节（T3 和 T4 合成一句）。
- 全片 30 小节 = 80.000 s = 2400 帧（v2 是 26 小节）。

**网格**：90 BPM，1 拍 = 20 帧，16 分音符 = 5 帧，1 小节 = 80 帧。bar k 的起点 = (k−1) × 2.6667 s。下文 `k:b` 里的 b 从 1 开始，与 score.json 一致。

**事实来源**（一律照抄）：
- 架构节点：`docs/assets/architecture.en.svg` / `.zh.svg`；
- 8 类名称：README 首段 "explainers, science shorts, launch films, music videos, data stories, paper talks, hand-drawn shorts and memes" / "科普、讲解、发布片、MV、数据、论文、手绘、梗"；
- 工作流节点：README "How it works" 的 mermaid 图；
- 特色：README "What is this" 的要点（Taste written down as numbers / Sound, end to end / Ready to run）；
- 案例：README 目录说明 "cases/ 11 case studies + curated picks from 389 community videos"；
- 安装命令：README "30 秒开始"。

## 镜头路径（一个镜头，十一段）

| 段 | t（s）· 小节 | 摄像机 | reads（依次） | 声音 / 重拍 |
|---|---|---|---|---|
| S1 hook | 0–8.0 · 1–3 | 贴近光点 → 光线拉出 → 第 3 小节升起后拉，揭示帧墙，沿轴前推 | 0.35–2.5 `frame = f(t)`；2.7–5.2 EVERY FRAME；5.33–7.9 IS A FUNCTION OF TIME / 每一帧，都是时间的函数。 | 0.167 spark；5.333 impact:corridor |
| S2 程序 | 8.0–16.0 · 4–6 | 沿轴穿过代码峡谷 | 8.2–10.9 请求卡（showcase 02 的请求原文）；10.67–13.2 Claude Opus 5.5 doesn't paint pixels. It writes the program.（合成一句）；两侧代码墙在 16 分音符上亮起；13.3 瓷砖飞回拼成竖屏；13.8–15.8 One sentence in. A film out. | 8.0 wake；10.667 program；13.333 film |
| S3 问题 | 16.0–21.33 · 7–8 | 穿过竖屏进入闪烁的档案走廊；20.67 全黑 | 16.0–18.7 Stunning, once.；16.67 / 17.33 / 18.0 三张错帧盖章 #11 / #10 / #19 FAIL；18.67–20.67 Dependable? Not yet. | stamp ×3；riser；20.667 hold（按钮音，pad 不断） |
| S4 出现 | 21.33–24.0 · 9 | 9 圈光环依次点亮，慢推 | OpenVideoHarness / turns Claude Code & Codex into a video studio / 把 Claude Code 和 Codex 变成一间视频工作室 | 21.333 braam + 最大冲击 |
| S5 架构网络 | 24.0–34.67 · 10–13 | 穿环 whip → 站点 1（正面）→ 左移到站点 2 → 右移到站点 3 → 升起俯瞰整张网络 → 俯冲进 `projects/` 六边形 | 10：You: a one-line request → Claude Code / Codex → CLAUDE.md · AGENTS.md router（pick type · hard rules · 3 human gates）；11：video-types/ · 8 video workflows，8 条支线在八分音符上逐条点亮（01 explainers · 讲解 … 08 memes · 梗）；12：playbook/ 8 know-how docs、templates/ 7 project templates、Cases & showcase、bin/vh scaffold · QA tools（每拍一张卡）；13：engines/ renderers（HyperFrames · Manim · p5.brush）、references/repos/ 20+ repos · read-only、projects/date-slug（outline → storyboard → draft → final） | arch:you/agent/router；types ×8（八分）；mod ×4（四分）；engines、refs、projects；riser 进入工作流 |
| S6 工作流 | 34.67–48.0 · 14–18 | 从六边形里出来，在流程图上方 3/4 视角跟拍；到循环处稳住慢推；升起俯瞰规则句；落到终点节点并停 2 拍 | How it works / 它是怎么工作的；节点 A→F 依次上电（README mermaid 原文）；37.33 / 40.0 人工审阅 ①② approved · 通过；循环：Scene code → Contact sheet / strip / crop → Taste checklist · 20 items，41.33 / 42.0 / 42.67 三次 fail · 不合格；43.0–45.2 Review every scene against the checklist, and fix it until it passes.；45.33 pass · 通过；46.0 人工审阅 ③；46.67–48.0 Final cut + LESSONS.md / 成片 + LESSONS.md（停 2 拍） | gate hold → approve ×2；fail ×3；pass；gate3；final + hold:final |
| S7 特色 | 48.0–56.0 · 19–21 | 三块全息面板排成弧形，每小节 whip 到下一块，面板前慢推 | 19：Taste written down as numbers. / 把品味写成数字（缓动曲线在画、安全框、20 条清单在打勾）；20：Sound, end to end. / 声音一条龙（配音 Qwen3-TTS、双语字幕、代码作曲、音效，逐拍亮起，波形是本片配乐）；21：Ready to run. / 开箱即用（终端里打出安装命令，再打 `bin/vh new`） | feat ×3；每拍的 tick / 声音演示；打字 16 分音符 |
| S8 案例星图 | 56.0–58.67 · 22 | 冲进一片星云：389 个点在 16 分音符上涟漪般亮起，11 颗亮星 | 11 case studies + curated picks from 389 community videos / 11 个案例拆解 + 389 支社区作品精选 | stars burst；11 音琶音 |
| S9 放映厅 | 58.67–69.33 · 23–26 | 从星图落入放映厅；每 3 拍贴一块屏滑过 | 58.9–61.2 Made by an agent, following only these docs.；61.33 01 手绘；63.33 03 数学；65.33 02 竖屏科普；67.33 00 发布片（静音） | impact:hall；八音盒 / 傅里叶 / 多普勒 / 默片 tick |
| S10 揭晓 | 69.33–74.67 · 27–28 | 升起拉远，面对纪念碑墙（本片联系表） | This film, too.；Even the soundtrack is code.；72.0 起每拍亮一行配乐代码，对应乐器同时进入 | breakdown；stems 逐拍进入 |
| S11 片名 | 74.67–80.0 · 29–30 | 推向墙面，稳住 | 74.67 OpenVideoHarness；75.3 Video as code, for coding agents.；76.67 `$ bin/vh new <type> <slug>` + github.com/ZLHad/OpenVideoHarness，保持到结束 | 74.667 最后一击；CTA 打字音 |

## 可读性规则（Phase B 修正）

- HUD 显示的是全片的真实 t、帧号和小节号（v3 look-dev 第 2 段显示的是偏移时间）。
- 必读文字（片名、关键数字、命令、GitHub 地址、节点标签）解码 ≤ 0.3 s。
- 节点标签按屏幕像素定尺寸：中文行 ≥ 44 px，英文 ≥ 52 px；只在自己的读窗内出现，离开站点就淡出。
- 标签可见时运动模糊、色差冲击都压低（guard），循环段的 fail 标签在 41.3–43.0 常驻，不闪没。
- 光晕峰值不压字：关卡的 approved 章在门框下沿外面，闪光先于字 0.1 s 衰减。
- 终点节点停 2 拍（46.67–48.0），音乐是持续和弦，不是空拍。

## 转场

1. 沿轴推进（S1→S3，S5 各站点之间用 whip）。
2. 穿帧：竖屏（S2→S3）、光环（S4→S5）、`projects/` 六边形（S5→S6）。
3. 升起 / 拉远：帧墙揭示、架构网络俯瞰、规则句俯瞰、纪念碑墙。

## 对照检查

- [ ] 每条 read 在下一条开始前能落地（draft 后用联系表 + strip 核对）。
- [ ] 标签实际字号（draft 后 crop 核对）。
- [ ] 数字和名称逐字对照来源（NOTES.md 事实表）。
