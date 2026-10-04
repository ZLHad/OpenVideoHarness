# NOTES · v5（关卡 ① 的工作笔记）

> 这是做片时的工作日志，路径按当时项目的布局写：项目的 `film/` 就是现在这个文件夹，`tools/look/` 现在是 `tools/`，`look/assets/`、`open/assets/` 现在是 `assets/`，`look/js/films.js` 现在是 `opening/films.js`，`audio/v5/` 现在是 `audio/`。`look/`、`look-*/`、`proto/`、`audio/score/` 等 look-dev 文件夹没有进仓库。

## 待核实的事实（屏幕上会出现的每个数字和原文，渲染前按当时的 main 再核）

核对基准：`main` 的 9f60db7（行号都按这一版；README 每合并一次行号就会移）。4398f27（#22）之后，05:38 又合并了 #23（playbook 09 叙事、10 钩子与封面、11 作曲，playbook 现在是 00–11 共 12 篇）。在途的 PR 还会改计数：recipes/、新乐器、导演模式。所以下面的数字**现在不冻结**，渲染前再核一遍，逐条改“状态”。

| # | 屏幕上（计划） | 现在的值 | 出处 | 状态 |
|---|---|---|---|---|
| 1 | 8 类里的 02 类 / type 02 of 8 | 8 | `video-types/` 8 个文件；README.md:7、README.zh-CN.md:7 | 渲染前再核（路线图有第 9、10 类） |
| 2 | 8 个类型名（路由环上，纹理） | 科普、讲解、产品片、MV、数据、论文、手绘、梗图快剪 | README 首段（v4 #2 已改名：product films、meme edits） | 渲染前再核 |
| 3 | 02 · 竖屏科普 · HyperFrames | — | README 展示表；`showcase/02-short-leo-doppler/` | 渲染前再核 |
| 4 | standard（quick · standard · studio） | 三档 | CLAUDE.md“努力程度”；README.zh-CN.md:166–173 | 渲染前再核 |
| 5 | 终端里打的需求 | README 的例子，截到第一句 | README.md:62、README.zh-CN.md:62 | 文字已对；屏幕用弯引号（排版），README 是直引号 |
| 6 | 关卡 ①②③ | 3 道 | CLAUDE.md 第 5 步；README.zh-CN.md:34、152–160 | 渲染前再核 |
| 7 | 大纲 + 两三个风格 | 2–3 个 | README.zh-CN.md:66、153 | 已对（草稿一度写成“3 种”，已改） |
| 8 | 28 种风格 | 28 | `styles/` 28 个预设；README 7、35、105 | 渲染前再核（shotcraft 调研提了 6 个新预设候选） |
| 9 | 声音先行，再写画面 | — | README.zh-CN.md:155 | 渲染前再核 |
| 10 | 代码作曲：N 种乐器 | 88（`--instruments` 列 88 个，其中 11 个是旧 layers 音色；v4 写 77 = 只算新乐器） | `bin/vh music --instruments` | **口径要定**；plucked-models 等 PR 在改，渲染前再核 |
| 11 | 旁白有表情、有节奏 / 双语字幕 / 音效、混音与质检 | — | README.zh-CN.md 的“声音”表（216–221 行） | 渲染前再核 |
| 12 | 自查闭环 · 20 条清单 · 7 项都到 8 分 | 20、7、8 | `templates/TASTE_CHECKLIST.md`；README.zh-CN.md:157–159 | 渲染前再核 |
| 13 | frame = f(t) | — | CLAUDE.md 硬规则 1 | 不会变 |
| 14 | 01 手绘短片 · p5.brush；03 数学讲解 · Manim；00 发布短片 · HyperFrames | — | README 展示表（v4 #11：00 不再写 SILENT，样板片在加配乐） | 渲染前再核；样板片的新版 final 出来要重做代理 |
| 15 | 都是 agent 只看本仓库的文档做出来的 / Made by an agent reading only this repo's docs. | — | README.zh-CN.md:74、README.md:74 | 已对 9f60db7。**v4 #14 的写法（reading only these docs）又过期了** |
| 16 | 这支片子也是 · 连配乐都是代码 | — | README.md:19、README.zh-CN.md:19 | 渲染前再核 |
| 17 | Video as code, for coding agents. / 给 coding agent 的视频工作台 | — | 不在 README；和 v3、showcase 00 一致 | 你定留不留 |
| 18 | `$ bin/vh new <type> <slug>` · github.com/ZLHad/OpenVideoHarness | — | CLAUDE.md 第 3 步；README 安装命令 | 渲染前再核 |
| 19 | 不缺工具，缺门道。/ Not more tools. Know-how. | — | 新写的主张，不是数字。依据：README“问题不在模型不够聪明，而在于它手里没有一套做视频的行规”，加你 10-01 的话“不是规则写死，更多是有这些知识，可以引导” | 你定文案 |
| 20 | 工具瀑布的卡片 | 文生视频、AI 剪辑、数字人、对口型、AI 配音、自动字幕…（中英各半） | 通用类别名，不是产品名，没有 logo | 真名只在你选了才加，而且只用纯文字 |

v5 计划里**不上屏**、但 v3/v4 上过的数：30 个参考仓库（README.zh-CN.md 50、295、368 行）、15 个音效和 -14 LUFS（219–220 行）、11 个案例和 389 支社区作品（101、365 行）、playbook（#23 之后是 00–11，12 篇；v3 写的是 9）、7 个模板、`bin/vh` 二十多个命令。回到哪个就按当时的 README 核。

### v4 过期文字表 #1–14 在 v5 里的去向

| v4 # | 内容 | v5 |
|---|---|---|
| 1 | references 20+ → 30 | 不上屏（不展开目录）；如果回来，用当时的数 |
| 2 | 类型名改成 product films / meme edits | 路由环上的 8 个名字照 README 首段 |
| 3 | “Cases & showcase”卡 → styles 28 | 变成关卡 ① 里的 28 种风格墙 |
| 4 | bin/vh 20+ commands | 不上屏 |
| 5 | 工作流 14 个旧节点标签 | 按 overview 图重写成 Ch1–Ch3 的 7 块标签，每块停够 |
| 6 | human review → Gate ①②③ | 照改 |
| 7 | Taste written down as numbers | 删，换成风格墙 |
| 8 | Sound, end to end | 改成“声音先行，再写画面”加面板 |
| 9 | 声音面板四行（Qwen3-TTS · Gemini、77 种乐器、15 SFX · -14 LUFS） | 保留四行；乐器数口径待定（第 10 条） |
| 10 | Ready to run → Start in 30 seconds | 并进片尾 CTA；要不要加安装命令你定 |
| 11 | 00 LAUNCH FILM · SILENT → LAUNCH SHORT | 照改 |
| 12 | S4 副行 video studio → dependable at video | 由开场的答句取代 |
| 13 | one-line → one-sentence request | 开场直接在终端打出一句需求 |
| 14 | Made by an agent reading only these docs | README 又改了，用第 15 条 |

片子定稿后要跟着改的“81 秒”：README.md:19、README.zh-CN.md:19 和展示表那一格、`video-types/03-product-promo.md` 第 4 行、`showcase/04-intro-film/README*.md`、wiki。

## 创作决策

- 2026-10-01 路由：`promo`（03）为主。开场的特效借 `playbook/08` 的预设栈思路，但灰盒阶段不做后期。
- 2026-10-01 结构：跟着“一句需求”走完全片。v3 的架构站（目录）并进路由，特色（风格、声音）放进它们被用到的那一步，放映厅变成“那句话变成的片子”。理由：你说 harness“不一定面面俱到”；v3 的目录清单正是一闪而过的来源。
- 2026-10-01 长度：按 readcheck 公式倒推每章时长（`review/onscreen-plan.json`，26 条中英都过），得到 106 s。紧凑版 78 s 是删内容，不是压时间。
- 2026-10-01 开场三案：A 压平（推荐）、B 降临、C 坍缩。A 的理由：特效就是论点（3D 的乱被压成 2D、再变成一行字），全片只有一次大打点，不懂《三体》也读得出“被压扁”。四个比喻（瘫坐眩晕、超新星、二向箔、大罗金仙）在 10 s 内全用会“处处打点”，所以每个方案取两三个：A = 眩晕 + 超新星 + 二向箔；B = 瘫坐 + 降临 + 冲击；C = 眩晕 + 超新星。
- 2026-10-01 开场 22 s，比你说的 15–20 s 多 2 s。卡在两处：问句要停 3.4 s，片名 + 答句要停 4.3 s（中文最慢）。压回 20 s 的办法：去掉开头那句 So many AI video tools（瀑布自己会说）。
- 2026-10-01 速度 120 BPM：一拍 15 帧，一小节 2 s，秒数好算；在帧对齐速度表里（playbook/04）。v3 是 90 BPM。
- 2026-10-01 主旋律推荐 B：问句里 F# A B 往上走、悬住，像问句的语调；揭晓时爬到 D；片尾放慢，把悬着的 B 落到 D。可以当 4 个音的声音 logo。A（1-5-4-3）更“电影”，但开头的上行五度是很常见的英雄式手势，你嫌套路的正是这一类。
- 2026-10-01 旁白：主版不配（v3 的方案 A），标“旁白（待定）”。没跑 TTS。

### 知识草稿怎么用的（这是它们第一次实战）

草稿在我做这页时（05:38）合并成了 `playbook/09-narrative.md`、`10-hooks-and-packaging.md`、`11-composition.md`（#23）。这页按草稿做；阈值我对过合并版的 11 篇，一致（段落最大差 ≥ 8 LU、最响段唯一且高 ≥ 2 LU、落在 60–85 %、前三分之一后有低谷）。关卡 ② 前按合并版再过一遍。

| 草稿 | 用了什么 | 没照做的地方和原因 |
|---|---|---|
| narrative-longform | 起承转合；节拍表六件事；缺口/能量两条曲线；软回环；“转”要让人重新解释看过的东西（Ch5） | 90 s 模板按 106 s 拉长；“问题卡停 2–3 s”改成 3.4 s，因为中文问句按 readcheck 要 2.7 s，再留余量 |
| viral-craft | 钩子梯子的 0–1 s：第 0 帧就是完整画面（原型修过这一处）；软回环 | 1–3 s 的“承诺”换成处境句（So many AI video tools），真正的承诺是 10 s 的问句。B站/README 的观众比信息流宽容，但 X 版要盯住前 3 s |
| composition（playbook-04 草稿） | 篇章 → 起伏曲线 → 主题地图；唯一最高点放在 60–85 %；前三分之一后有低谷；动机藏 → 半句 → 完整 → 发展 → 回归；按八度叠旋律；打点预算 | 示范 1 的动机 1-5-4-3 作为 A 保留；推荐的是新写的 B。示范是 56 s，这里按 106 s 写了 15 段 |
| hooks（合并后的 playbook/10） | 标题、封面、前 6 s 承诺同一件事；标题备选写在 REVIEW-gate1.md 的折叠里 | 它要求关卡 ① 出 3 种**不同类型**的钩子卡。这支片子的钩子类型你已经定了（打断 + 好奇缺口：先被淹没，再问差什么），所以三案是同一钩子的三种画面。封面在关卡 ② 出 |
| shotcraft | 整画面冲击设上限（全片 1 次大 + 3 次中）；重拳之后留白；打字按真人速度的思路 | 打字 40 字/秒，比它建议的 10 字/秒快：英文需求 95 个字符，照真人速度要 9 s，开场放不下。要更像真人，就换一句更短的需求 |

## 测量记录

**配乐草图** `audio/sketch-v5.wav`（`audio/score/make_sketch.py` → `sketch-v5.json`，53 小节，51 个声部）：
- 整体 -15.6 LUFS，LRA 10.9 LU，真峰值 -1.0 dBTP；段落平均最大差 11.4 LU（草稿目标 ≥ 8）。
- 唯一最高点：climax -10.6（72–80 s，全片 68–75 %），比第二高的 proof（-14.2）高 3.7 LU（目标 ≥ 2）。最静：question -21.9。
- 计划 vs 实测（每段平均）：15 段里 14 段在 ±2 LU 以内；proof 低 2.7 LU（高潮之后掉得太快），coda 低 1.9 LU（片尾偏静），sound 高 1.8 LU（55 s 那一下有点抢）。见 `review/music-arc.png`、`review/music-arc.json`。
- 主旋律压不压得住（`stems.py`，主旋律比最响伴奏高多少）：question +2.4，reveal +4.9，route +6.8，code +4.3，climax +7.6，proof +6.2，coda +8.8 dB；**gates -2.1 dB**（关卡段的铜管模进被伴奏盖住，正式作曲改配器）。
- `bin/vh qa`：0 静音、0 掉音、0 抽吸、0 click；18 个 cue 全在 1 帧内（最大 11 ms）。重渲一次 md5 相同（220024c7…）。
- 一个坑：28 音的风格琶音每个音都标成 hit 时，cue check 把相邻的十六分音符当成对象，报 8 个偏 118 ms。十六分音符太密，不适合当 cue；画面按十六分音符网格算就行。

**主旋律 A / B**：各 5 小节（最后一小节 6/4），11 s 旋律加 1 s 余音淡出，文件正好 12 s；同一套伴奏；响度对齐到 -15.9 LUFS（静态增益，真峰值 A -4.6、B -5.9 dBFS）。主旋律比最响伴奏高 A +4.1 dB、B +4.6 dB。`bin/vh qa` 都通过。

**开场灰盒**（`proto/`，HyperFrames 0.8.82 + Three.js，960×540）：
- 渲染：690 帧，draft，2 个 worker，15.7–17.9 s。
- 闪白：逐帧 YAVG，只有 8.0 s 一次跳变（+173），任意 1 s 内最多 1 次。
- 第 0 帧：YAVG 26.6（修之前卡片要 0.33 s 才淡入，第 0 帧近黑）。
- 确定性：乱序 snapshot，9.5 s 和 12.0 s 逐字节相同；16.5 s 有 3 个像素差 1 级（PSNR 103 dB，GPU 光栅化）。
- animatic 的混音：-14.1 LUFS，真峰值 -1.47 dBTP，限幅器压了 10 个峰、最多 4.2 dB，都在超新星那一下。正式混音要么把那一下的瞬态收一点，要么整片定在 -15 LUFS。

**readcheck**：开场 5/5（中、英）；全片计划 26/26（中、英）。需求那一行要从打完（21.6 s）停到 28.6 s，所以它在 Ch1 里一直钉在画面上方。

## 已知问题（关卡 ② 之前处理）
- 压平的侧面一瞥（9.5 s）是开场最难的一镜，灰盒里读得出“一张薄片”，但还不够“被压扁”。备选见 STORYBOARD。
- 关卡段主旋律压不住（-2.1 dB）；放映厅段偏低 2.7 LU；片尾偏静 1.9 LU。
- 开场需求在英文主版打英文，95 个字符打得很快（40 字/秒）；zh 版打中文会自然很多。
- 灰盒只有配乐和几个占位音效（`audio/events-opening.json`），音效设计在关卡 ② 做。
- `bin/vh check` 把 19.0–21.2 s 判成黑场：终端浮在几乎全黑的底上。正片里终端要放在世界里（压平的那张纸还在后面、压暗），不要落在纯黑上。

## 怎么重做
```bash
# 配乐（在项目根目录）
(cd audio/score && python3 make_sketch.py)    # 生成 audio/score/sketch-v5.json
# 主旋律：bin/vh music audio/score/motif-A.json audio/motif-A.wav（B 同理），再做静态增益到 -16 LUFS、11.3–12.0 s 淡出截到 12 s
../../bin/vh music audio/score/sketch-v5.json audio/sketch-v5.wav && ../../bin/vh qa audio/sketch-v5.wav audio/sketch-v5.beats.json
# 开场灰盒：proto/switch.sh A|B|C 选方案，再 snapshot 或 render（不带 GEMINI_API_KEY，--describe false）
proto/switch.sh A && (cd proto && HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1 env -u GEMINI_API_KEY node_modules/.bin/hyperframes render . --quality draft --workers 2 --output ../out/animatic/opening-A-silent.mp4)
# 图：uv run --with matplotlib --with numpy --with scipy python tools/figs/chapters.py（music_arc.py、motif_options.py 同理；opening_options.py 用 --with pillow）
../../bin/vh readcheck review/onscreen-plan.json --lang zh   # 和 --lang en
```
`proto/node_modules` 是从 v3 工程 `cp -c` 克隆的（APFS，不占额外空间），可以随时删。
`tools/figs/` 里的 `arc.py`、`dump_events.py`、`stems.py` 是从知识草稿的示范工具复制来的（EBU R128 曲线、按小节的密度、主旋律余量），项目不再依赖 scratchpad。

## 素材台账
| 文件 | 来源 | 许可 |
|---|---|---|
| `audio/*.wav` | `bin/vh music` 代码合成，谱子在 `audio/score/` | 本仓库 MIT |
| `out/animatic/sfxlib/*`、`sfx-opening.wav` | `bin/vh sfx lib` 内置音效 | 本仓库 MIT |
| `proto/` 的卡片缩略图 | 代码画的抽象图形和通用类别名 | 原创，无第三方商标 |
| 字体 | 系统字体 SF Pro、PingFang SC、SF Mono（渲染时用本机字体） | 系统自带 |

## 开场 look-dev r2（2026-10-01，关卡 ① 的修改）

用户意见见 REVIEW.md 关卡 ①；审阅页 `out/review/gate-1b.html`（`gate-1b.json`）。

- **代码**：`look/`（HyperFrames 0.8.82 + Three.js 0.181）。`js/films.js` 片源图集，`js/cards.js` 玻璃卡片，`js/sky.js` 星穹，`js/world.js` 相机和全部编排，`js/post.js` 子帧运动模糊和后期，`js/overlay.js` 字和终端。变量：`fx` = B | C（眩晕强度）、`mb` 子帧数（默认 6）、`grain`、`hud`、`atlas`（片源一览，审阅用）。
- **渲染**：1080p、mb 6，B 53 s、C 46 s（M3 Max，2 个 worker）；mb 4 的草稿约 30 s。`tools/look/snap.sh <名字> <时刻>` 取关键帧（`--describe false`，不带 GEMINI_API_KEY）。
- **确定性**：3.1、8.07、12.4 s 三帧打乱顺序重渲，PNG 逐字节相同。
- **闪白**（逐帧 YAVG）：B 只有 8.0 s 一次（+131）；C 8.0 s 一次，9.1 s 压平开始时 +43。
- **`bin/vh check`**：无黑场、定格、静音；BT.709 四个标签齐全。
- **混音**：`audio/look/`，promo profile，配乐草图前 23 s + 37 个音效事件；-14.0 LUFS，-1.65 dBTP；`bin/vh qa` 通过，4 条提醒（boom、impact 低频为主，已叠一层 whip 起音）。
- **踩过的坑**（项目结束时整理进 LESSONS）：
  - three 的 ShaderPass 会克隆 uniforms，渲染目标的纹理被丢掉 → 画面全黑；构造完再赋值。
  - 着色器里 `pow(底数, 指数)` 的底数因浮点误差略小于 0 时得 NaN，bloom 把 NaN 扩散到整帧 → 整帧黑；底数一律 clamp，累积时再挡一道 isnan。
  - 二向箔在俯视时读不出“压扁”，改成镜头斜看时再压。

### 素材台账（look-dev）
| 文件 | 来源 | 许可 |
|---|---|---|
| `look/assets/films.jpg` | `tools/look/film_atlas.py` 从本仓库 `styles/*/media/swatch.mp4`（28 个）和 `showcase/00–04` 的 final.mp4 截的 41 段 | 本仓库 MIT |
| 程序生成的 28 段片子 | `look/js/films.js` 里的着色器，渲染时生成 | 原创 |
| `audio/look/sfxlib/*` | `bin/vh sfx lib` 内置音效 | 本仓库 MIT |
| `audio/look/music-opening.wav` | `audio/sketch-v5.wav` 前 23.6 s（`bin/vh music` 代码作曲） | 本仓库 MIT |

### 10-02 复核：别的会话合并 #41–#50 之后变了的事实（渲染前再按当时的 main 核一遍）
| 屏幕上（计划） | 关卡 ① 时 | 现在（main 7057c74） | 出处 |
|---|---|---|---|
| N 类视频 | 8 | **9（09 实验中）**；终端回显已改成“9 类里的 02 类” | README.zh-CN.md:7 |
| N 种风格 | 28 | **31**（#42 加 tabletop-miniature，#49 加 pastel-ui、y2k-chrome） | README.zh-CN.md:7、124 |
| 打分层 | 7 项都到 8 分 | **8 项**，第一项是“立意”（#44） | templates/TASTE_CHECKLIST.md:81；README.zh-CN.md:178、192 |
| playbook | 00–11，12 篇 | **00–12，13 篇**（#44 加 12 立意） | playbook/ |
| 镜头配方 | 24 | **34 个文件**（含骨架；上屏前按 `bin/vh recipes list` 的口径再数） | recipes/ |
| 风格怎么用 | “挑一个风格” | **风格是参考，不是模板**（#48：`--style a,b` 只放进 `style-refs/`） | CLAUDE.md、README |
| Blender | 实验性，没跑过 | **已装 5.2.2，样片路径跑通**（#42，CPU 逐像素确定，Metal 92 dB） | engines/blender.md |

片子定稿后要跟着改：README.md / README.zh-CN.md 第 19 行的“81 秒”和展示表 04 那一格（时长、引擎、BPM、音效数）、`showcase/04-intro-film/README*.md`、wiki。

## 开场 look-dev r3：星河（Blender 5.2，2026-10-02）

用户对 r2 的意见（10-02，原话）：“其实还可以 至少样子像了，但是质感和特效感觉还差一点，有一点点廉价特效的感觉？如果优化？或者你觉得是否这些片子可以以星河、恒星等形式展现？或者使用blender？好友好莱坞大片质感~”

- **立意**：每颗星都是一支片子。开场是一张玻璃片的特写（地球），镜头飞速拉远，原来它只是一个星系里的一颗星；星系越转越快，镜头螺旋下坠（眩晕）；星系坍缩进核心，超新星；二向箔把爆开的碎片压成一张铺满影片的圆盘；扫光把它整理成网格；网格收成终端。
- **代码**：`blender/galaxy.py`（numpy 逐帧算每颗星、每张卡、每个参数，t 的纯函数）、`blender/nodexpr.py`（把数学表达式编译成 Cycles 着色器节点，用来写随星系转动的旋臂光雾、尘埃带、超新星气体）。`tools/look/bl.sh` 套沙箱（不联网、只能写 `blender/out/`、`env -i`），`tools/look/bl_render.sh` 分块可续渲。合成：`look-bl/`（HyperFrames：Blender 底片当 `<video>`，字、终端、闪白在 DOM 上）。
- **片源**：`look/assets/films-proc.png`（28 段程序片源，从 WebGL 导出，`look-atlas/`）、`look/assets/films.jpg`（41 段本仓库样片），开场那张地球片单独 1024 px（`look/assets/hero-earth.png`，`look-hero/`）。
- **规模**：118 万颗星（盘、核球、晕）+ 1.6 万颗“片星”（近处变成玻璃卡）+ 1.2 万个火花 + 星际体积 + 超新星体积 + 3 万颗远景星。
- **速度**（M3 Max，Metal）：草稿 960×540、48 spp 每帧 7–15 s；1080p、64 spp 特写约 37 s、星系约 23 s、压平盘面约 4 s。第一次用到新特性时 Metal 要编译内核 3–6 分钟（之后缓存）。
- **踩过的坑**：
  - 运动模糊：逐帧用 numpy 写位置时，Cycles 不知道上一帧在哪；给点和网格写 `velocity` 属性（快门两端的中心差分）就有拖影（实测）。相机每帧打关键帧。
  - OIDN 会把星点抹成一团团糊：星空不降噪，靠采样数。
  - 体积里贴着镜头的发光会把画面冲白：用 Camera Data 的 View Distance 把镜头 4–60 m 内的体积发光压掉。
  - 压平后影片卡层层重叠，光线要穿过很多层玻璃，超过透射反弹上限就成了黑块：压平的卡片收起玻璃外壳（特写才需要玻璃）。
  - `to_track_quat("-Z", "Z")` 是退化的（追踪轴和上方向同轴），相机要用 `("-Z", "Y")`。
  - macOS 的 `seq -s,` 末尾会多一个逗号。
- **还没做的**：只渲了 C（眩晕强）；配乐还是草图；正式 1080p 渲染约 3–4 小时。
- **正式渲染（10-02）**：1080p、64 spp、不降噪，690 帧，Metal，用时约 2 小时 15 分钟。各段每帧：开场特写约 34 s，拉远到星系约 8 s，螺旋下坠约 20–24 s，坍缩约 34 s，超新星约 24 s，压平以后约 5 s。后来改了片尾镜头高度（终端下面不能是黑场），从 13.8 s 起重渲 276 帧，约 25 分钟（改一个关键帧会通过插值影响前后两段，所以从前一个关键帧开始重渲）。
- **确定性**：新进程里打乱顺序重渲第 600、300、37 帧，和序列比 PSNR：inf（像素相同）、49.3 dB、95.4 dB，都高于 45 dB 的 GPU 底线；PNG 文件哈希不同，是元数据。
- **交付检查**（`out/look/r3-final-web.mp4`）：`bin/vh check` 无黑场、定格、静音，BT.709 四个标签齐全；逐帧亮度只有 8.0 s 一次闪白（+116）。
- **4K**：Cycles 耗时约和像素数成正比，这段开场 4K 约 10–14 小时（64 spp，Metal）；look-dev 和 README 用 1080p，4K 到关卡 ③ 再定。

## 最终版（10-02，用户授权跳过关卡 ②③ 之后）

- **开场**：Blender 只管 0–15.8 s（`blender/out/final2/`，475 帧，1080p，特写 96 spp、其余 64 spp，不降噪）；15.4–15.8 s（第 5 轮后提前到 15.0–15.6 s）和 WebGL 网格（`film/js/grid.js`，同一相机、同一批卡片，`tools/look/export_state.py` 导出）交叉溶解，之后都是 HyperFrames 1080p。
- **确定性（final2 底片）**：新进程里重渲第 100、300 帧，和序列比 PSNR 71.3、47.3 dB（底线 45 dB；300 帧是层层重叠的影片之海，余量最小）。上面 r3 的 inf / 49.3 / 95.4 dB 是 look-dev 那一版底片的数字。
- **抖动和不连贯**（用户 10-02 指出）：`final_patch.py` 改了相机（显式 forward / up、四元数符号连续、爆炸抖动换成平滑噪声），帧差曲线（0–74 帧，480×270 灰度平均差）一路平滑升降，没有尖峰。
- **正文**：K1（琥珀档案馆 + 星），速度 90 → 80 BPM；正文空间里飘着开场的影片（1000 张，最先画，字和面板永远盖在它上面）。

### 独立评审（代审关卡 ②③，全新上下文，TASTE_CHECKLIST 20 条 + 8 项打分）

| 轮 | 片子 | 立意 | 钩子 | 桌面可读 | 运动 | 变化 | 完成度 | 准确 | 声画 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | draft 2（旧底片，90 BPM 正文） | 6 | 7 | 5 | 6 | 6 | 5 | 7 | 7 |
| 2 | draft 3（`out/review-r2/film.mp4`，80 BPM，87.5 s） | 6 | 7 | 6 | 7 | 8 | 5 | 7 | 7 |
| 3 | 最终版 87.5 s（新 Blender 底片，第 2 轮的修改） | 7 | 8 | 6 | 7 | 7 | 6 | 7 | 8 |
| 4 | 130 s（21 个停留段拉长） | 8 | 7 | 8 | 7 | 7 | 7 | 9 | 8 |
| 5 | 147.5 s（26 个停留段） | 7 | 7 | 8 | 8 | 6 | 7 | 7 | 7 |

第 1 轮修了：正文加上开场的影片（立意接上）、站点卡字号 ≥ 46 px、09 类标出来、旧的“11 个案例”、22.9 s 的重影、顶部黑带、HUD；8.0 s 的 boom 上面叠了一层 whip 起音（qa 仍提醒 boom 本身 100 % 在 150 Hz 以下，笔记本扬声器上靠 whip 撑）。

第 2 轮指出的（逐条和处理）：
- 飘着的影片盖住字（52–75 s，“102”读成“02”、`bin/vh` 读成 `n/vh`）：影片层 `renderOrder −100` 最先画，近处大卡淡掉（视距 4–9 m 渐入），1600 → 1000 张，亮度降一档。
- 34 s、42.5 s 金线穿字：engines/ references/ 的标签挪到节点上方（导线从下面来）；管线的标签换成下三分之一的字幕条。
- 站点字只停 0.6–1.0 s、互相叠着解码（36.5–46 s）：工作流一节从 17 条字减到 9 条。A–F 不再挂标签（路由和类型 S5 刚讲过）；三道关卡各一条字幕“○ human review ① · outline / 人工审阅 ① · 大纲”，通过那一拍变成琥珀色 ✓（同样的字，不是新的一读）；回环三条字错开 0.45 s 出现，各自 ≥ 2 s；规则句缩到 7 个词“Check every scene. Fix until it passes.”。
- 关卡只是空六边形，看不到产物（#8 #20）：每道关卡的门里是被审的东西：① 这支片子的大纲（STORYBOARD.md 的章节表），② 分镜联系表，③ 初版联系表；镜头穿门而过（recipes/seam/gate-as-door）。
- 三次报错只看得见一次：报错标签带计数 ×1 → ×2 → ×3，每次报错音都换一次字。
- 44.4–45.3 s 镜头往里一冲又退回（第 2 轮帧里看得到，标签被挤出画面）：Hermite 在“停留 → 拉到全景”之间过冲；出发关键帧改用停留段的切线（`"b"`）。整段正文逐帧查相机速度方向，再没有反向。
- 终端字 37–42 px：全部 ≥ 46 px；打字 1.85 s，回车提前到 21.0 s（音效跟着挪），回显“type 02 of 9 · standard”停 1.7 s（原来 0.35 s）。
- 02 竖屏短片太小、左边三分之一空着：镜头推近（片子占画面高约 80 %），左边写“The request from the start → this film. / 开头那句需求，就是这支片子。”，标签字号 ×1.25。
- 片尾网址打完只剩 2.5 s：打字提前一拍（29:3 → 29:2，音效跟着挪），网址停 3.0 s。
- 片名的“O”被光晕吃掉：标题竖条亮度 2.6 → 1.7，往左挪，光线强度减半，片名不再有冲击环。
- 正文每个大拍都闪白：正文闪白 ×0.3，冲击环 ×0.6；字在画面上时色散去掉 95 %。
- 字幕条琥珀字被横向光条吃掉（柠檬黄压在橙色上）：字幕的琥珀色降到 #DCA234（线性亮度 < 0.82，低于光条阈值）。
- 字后面的暗底板读成方块：底板的渐变改成四边都淡到 0 的椭圆。
- 侧标签不再乱码解码（25 个标签同一个入场太单调），只淡入；大标题保留解码。
- 混音：5 个 detail whoosh、8.0 s whip、48.5 s success、63.5 s impact 降 1–7 dB，正文 tick 升 2 dB；提醒从 28 条降到 8 条。90 个 click 提醒都在配乐 stem 里（v3 配乐的打击乐起音），音效 stem 里没有。


第 3 轮（87.5 s 的最终版）：4 条底线 FAIL。
- **#5 读时，贯穿正文**：路由 1.1 s（要 4 s 以上），四张目录卡约 2 s，“How it works” 2.1 s，“Final cut” 1.1 s，“31 styles” 2.35 s，“13 case studies” 2.1 s，“Made by an agent” 2.2 s，“The request from the start → this film.” 1.7 s。
- **#3 安全框**：“Check every scene.” 顶到画面上沿。
- **#17 被盖、叠读**：09 只露 5 帧；“How it works” 压在大纲表上。
- **#19 假数字**：门里的大纲表写着 86–94 s、94–106 s（那是关卡 ① 时 106 s 的计划）。

根子在结构：正文是 v3 的节奏（每站一小节），字多、停得短；80 BPM 只拉长了 12.5 %。处理：
- **加时间，不砍内容**（reviewer 的建议）：`film/js/tmap.js` 把旧的 87.5 s 时间线上 21 个停留段拉长（每段在镜头的慢推里，前后不压任何音乐事件），片长 87.5 → 130.0 s。画面仍写在旧时间上，按这张表取帧；粒子、片子播放、手持漂移走新时间，停留时世界不停；运动模糊按表的局部速率算（停留段里镜头慢，糊得就少）。
- **配乐跟着拉**：`film/tools/retime.py` 从 `audio/score.base.json` 生成 `audio/score.json`：含停留段的那一小节加拍（17 个小节变长，按拍对齐），所有事件、hold、片尾淡出按同一张表搬；每个停留段是一个 hold（鼓撤，贝斯暗下，pad 不停）。开场终端那一段用草图第 11 小节重复一遍。音效按同一张表搬。`bin/vh qa`：0 静音、0 掉音、0 抽吸，62 个卡点都在一帧内。
- **字少一点**：路由只留 “CLAUDE.md router / CLAUDE.md 路由”；engines/、references/ 拆成短行；“Made by an agent / from this repo's docs alone.”。
- 其余：规则句挪进安全框、加底板；大纲表去掉时间列，门在标题退场后才亮；关卡 ✓ 改成硬切（原来交叉溶解有 2 帧重影）；“→ this film.” 改白字；“This film, too.” 等甩镜落地再出、不乱码；镜头光条只留三次大运动；门户的冲击环去掉；09 的标签不再被推出画面。
- **踩到的坑**：拉长的停留段里，画面时间原来按 30 fps 取整，镜头会停几帧再跳一下（帧差每 3–5 帧一个小尖峰）；改成只有片子时间取整、故事时间连续，抖动消失。

第 4 轮（130 s）：底线还剩 #5 和 #17。
- **#5 仍不够的地方**：终端里的需求打完只停 3.6 s，要 6.9 s；Sound 面板同屏约 25 个英文词；“Contact sheets”贴着画面上沿，被推得半透明，只看得到 1.2 s；“pass” 只有 0.6 s；放映厅三张标签各约 2 s；“Even the soundtrack is code.” 2.5 s；gate ③、31 styles、Ready to run、Final cut 各差 0.2–0.5 s。
- **#17**：规则句的解码压在回环三条字上，“Final cut” 进来时 gate ③ 的字幕还没走（各 3–6 帧）。
- 别的意见：Final cut 那一站九成是黑星空；cases 是纯字卡；甩镜的动作十几次都一样；hook 前 0.5 s 只是一张暗卡。

处理：
- 停留段从 21 个加到 26 个，片长 130 → 147.5 s（4425 帧）。终端那段多停 4 s，配乐草图第 11 小节多奏两遍，终端在这几秒里慢推 3 %。新加 pass、放映厅三张片子、“Even the soundtrack is code.”；gate ③、31 styles、Sound、Ready to run 再拉长；最后一段多一拍，让片长落在整帧上。
- Sound 面板每条只留一行（“Voiceover · 配音”“Captions · 字幕”“Score · 102 instruments · 作曲”“Mix · −14 LUFS · 混音”），去掉“this film's own score”，标题在第四条亮起后退场，四条单独停够。
- “Contact sheets”挪进回环里面；规则句等回环三条字走完才出；“Final cut”等 gate ③ 的字幕走完才出；关卡字幕的底板加大、更不透明。
- Final cut 这一站放一块屏，播这支片子自己的一帧（星系），字更大。
- 00 片在放映厅里从 5.5 s 播起（从头播，甩镜出去时正好是半句 “One catch: it can't”）。
- 交接处的溶解提前到 15.0–15.6 s，盖住底片下方那块暗斑；终端标题栏的时码改用片子时间。
- 音频：qa 报的 click 集中在拉长的停留段，是 v3 配乐 pulse 声部锯齿波门限的硬边（3 个采样内跳 0.25），停留段里鼓撤掉以后更露。没改，留给人耳复听（已知问题）。

第 5 轮（147.5 s）：这一轮的 reviewer 更严，把列表、卡片也当成必读字。底线：#3（竖屏片的说明在推镜时出了安全框）、#5（路由、9 类列表、目录卡、引擎、终端、关卡 ①②、Final cut、风格墙）、#17（关卡 ② 字幕和回环三条字同屏）。最重的一条是立意：开头那句需求是 02 竖屏科普，关卡的门里和成片处放的却是这支片子自己（初版联系表里甚至提前 55 s 露出了 “This film, too.”）。

处理（用户 10-03：“这一轮做完就整体提交吧”，所以这一轮的修改没有再审）：
- **需求这条线贯穿正文**：9 类列表全部出来以后，02 科普亮起放大、线也更亮，其余 8 类降到 35 % 当纹理；目录卡里 styles/ 留亮；三道关卡的门换成 02 的大纲（它 STORYBOARD 的分镜表）、分镜（8 个镜头的 9:16 关键帧和字幕）、初版联系表（`film/tools/request_tex.py`）；自查回环中间放 02 的 9 帧，三次报错各有一帧变红、打 ✕，通过时三帧一起转琥珀色 ✓；成片那一站播 02 本身（竖屏）。
- 需求里删掉 “30-second / 30 秒的”（02 是 24.8 s）。
- 底线：竖屏片的镜头离远一点、看点放低，说明回到安全框里；关卡 ② 的字幕在回环的字进来前退场；路由、关卡 ①、Final cut 再拉长；references/ 晚一点出，和 engines/ 不再挤；风格墙底部说明去掉重复的 “31 种风格”；规则句不再乱码解码。片长 147.5 → 150.5 s（4515 帧）。
- 顺手发现并修了两个静默问题：组装正文的 async 失败原来不报错（整片黑场也不响），现在打印出来；`js/arch.js` 里一行注释吞掉了 `m.add(tab)`，目录卡的琥珀小标签一直没加上。

## 素材台账（最终版）
| 文件 | 来源 | 许可 |
|---|---|---|
| `blender/out/final2/`（0–15.8 s 底片） | `blender/galaxy.py` 用 Blender 5.2 Cycles 渲染，场景全由代码生成 | 原创；`galaxy.py` 是 GPL-3.0-or-later（调用 bpy），渲出的画面不受 GPL 约束 |
| `look/assets/films-proc.png`、`hero-earth.png` | `look/js/films.js` 的 28 段着色器，`tools/opening_export.sh` 导出 | 原创 |
| `look/assets/films.jpg` | `tools/look/film_atlas.py` 从本仓库 28 个风格样片和 showcase 00–04（当时的 v3）截的 41 段 | 本仓库 MIT |
| `look/assets/ai/00–39.jpg` | 40 张 AI 静图：Gemini API，gemini-3.1-flash-image，2026-10-02 生成（用户批准，约 1.8 美元，用户自己的 key）；提示词逐张在 `look/assets/ai/prompts.json`；只画虚构的人和地方，没有品牌、商标、真人 | 生成图，不是第三方素材；按 Google 的 API 条款使用 |
| `film/assets/tex/02-*.png` | `film/tools/request_tex.py` 从本仓库 showcase/02 的 STORYBOARD 和成片画的 | 本仓库 MIT |
| `film/assets/tex/styles-wall.jpg`、`atlas.jpg`、`self-sheet.png` | 本仓库 31 个风格样片的帧；这支片子自己的草稿帧 | 本仓库 MIT |
| 片中播放的 showcase 00–03 和 02 竖屏（`assets/clips/`） | 本仓库 showcase 的成片 | 本仓库 MIT |
| `audio/score/sketch-v5.json` → 开场配乐 | `bin/vh music` 代码作曲 | 本仓库 MIT |
| `film/audio/score.json` → 正文配乐 | `film/audio/score_engine.py` 代码作曲（v3 的谱子改成 80 BPM，按 `js/tmap.js` 加拍） | 本仓库 MIT |
| 音效 | `bin/vh sfx lib` 的 21 个内置音效（代码合成） | 本仓库 MIT |
| 字体 | 系统字体 SF Pro、PingFang SC、SF Mono（渲染时用本机字体；README 播放用的角标是 SF Mono 画的 PNG） | 系统自带 |

## 交付：README 里的播放器（10-03）
- GitHub 免费账号的 user-attachments 每个视频 ≤ 10 MB；单独一行的附件链接会渲染成播放器（表格单元格里前后留空行也行），`<video>` 标签拿不到签名地址。
- 介绍片切成 8 段 1080p（`film/tools/chapters.sh`，每段 ≤ 9.6 MB），每段右下角一个 “ZLHad/OpenVideoHarness” 小字（`film/tools/watermark.sh`，Pillow 画 PNG 再 overlay，这台 ffmpeg 没有 drawtext）；showcase 00–03 和 31 种风格的样片集锦用同一个脚本加角标。
- 播放器没有 poster、`preload=metadata`，缩略图就是第 0 帧：第 2–8 段起初有 0.25 s 画面淡入，缩略图全黑；改成只淡声音，重切重传。
- 未登录的访客也能播（未登录的浏览器打开分支页面，15 个播放器都拿到签名地址并加载完成）。

## 103 s 版（10-04）
- 用户看完 150.5 s：停顿太长；最早那版节奏对，只有个别镜头太快；“也不是那种一闪而过的”。
- 做法：回到 87.5 s 的时间线，每条字只给读一遍的时间（英文约 20 字符/秒、中文约 7 字/秒，+0.8 s，≥ 1.5 s），逐帧量 87.5 s 版后只补 15 处（`js/tmap.js`），共 +15.5 s → 103.0 s（3090 帧）。拉长的小节织体照常走（`tools/retime.py` 不再把拉长处写成 hold），音乐不再“屏息”。
- 第一版 100 s 草稿里我把 Final cut 的 +1.5 s 错加在了 31 styles 那一处（按快照图对段时编号错了一位）；逐帧量出来以后改正，并补了关卡 ②、pass、关卡 ③、“这支片子也是”各 0.75 s。
- 量过的读时（每秒 4 帧）：路由约 2.75 s，关卡 ② 约 1.9 s，pass 约 1.4 s，关卡 ③ 约 1.5 s，Final cut 约 2.75 s，“这支片子也是”约 1.9 s。
- 声画同步：画面帧差峰值 ↔ 声音，大事件都在一帧内；配乐里有名字的重音 ↔ 同一画面事件的音效，查出四处偏差（第二对目录卡片早 0.75 s、案例 11 个钢片琴音落在静止画面上、reveal 早 1.25 s、片尾打字晚一拍），都是之前几轮改画面时只挪了音效。另有一个 bug：案例星图的点亮时间写在故事时间上，着色器却用片子时间，涟漪在镜头到之前就放完了。都已修。
- 声音：`bin/vh qa` 62/62 卡点在一帧内（中位 5.3 ms），−14.0 LUFS，−1.65 dBTP；click 提醒 152 处（150.5 s 版约 190 处，鼓不撤以后少露一些）。
- README 播放：重切 6 段（0–25、25–42.25、42.25–61.3、61.3–74.5、74.5–89.75、89.75–103），每段 ≤ 9.6 MB，第 0 帧都有画面；第 3/4 段的边界先切在 58.0（那是 Final cut 到站，不是风格墙），改到 61.3。
- 4K：Blender 原生 4K 每帧约是 1080p 的 4 倍（实测 5 帧：3.8–4.1×），整段约 5.7 小时，后台在渲；和 1080p 放大 2 倍比，特写原生明显更清楚，运动模糊段差别很小。

### PR #53 的评审（10-04）
- 阻断：`js/features.js` 里我在一行中间加了注释，把后面案例星图的 `uAmt` 赋值吞掉了（星图整段不显示），1080p 成片和 README 第 4 段都带着。修好后重渲，换掉 Release 里的 `intro-film-1080p.mp4`，重切重传第 2–6 段。
- 同步：案例的 13 个钢片琴音里，12、13 号偏了 0.3、0.68 s（那一停压在最后两颗星上，配乐的 repeat 不经过时间表）；把那一停挪到第 13 颗星之后，13 个音都对上（0.000 s）。
- 读时：pass 逐帧只有约 1.3 s，低于 1.5 s；pass +0.75 s，片尾 −0.75 s 补平。Final cut 约 2.3 s，关卡 ③ 约 2.3 s。第 4 段以后的时间都晚了 0.75 s（风格墙 62.05、放映厅 75.25、"这支片子也是" 89.5、片名 96.25）。
- 声画：有名字的重音里，和音效同属一个画面事件的都在 0.00 s；声音面板四行、案例星、"这支片子也是"、风格墙第一行这几处没有对应音效，前三处对着帧查过。

