# OpenVideoHarness 介绍片 v5：星河开场 + 一镜到底

1920×1080 · 30 fps · **103 秒（3090 帧）** · −14 LUFS · 成片：[`intro-film-1080p.mp4`](https://github.com/ZLHad/OpenVideoHarness/releases/download/media/intro-film-1080p.mp4)（295 MB，在 GitHub Release 里）· 封面 [`media/poster.jpg`](media/poster.jpg) · 联系表 [`media/sheet.jpg`](media/sheet.jpg) · English: [README.md](README.md)

按精品档（studio）做的。前 15.8 秒是代码驱动 Blender 路径追踪渲出来的，之后交给 HyperFrames 和 Three.js。屏幕上的每个数字都照抄仓库，出处在 [NOTES.md](NOTES.md)。上一版（v3，81 秒）在 [v3/](v3/)。

## 观看：6 段 1080p

每段都能在这里直接播放，有声音（1080p，每段不到 10 MB，这是 GitHub 在 README 里放视频的上限）。整片一个文件，见上面的 Release 链接。

**1 · 星河开场和那句需求**（0–25 s）

https://github.com/user-attachments/assets/48923404-eff1-41cd-b303-82c9ede51c1f

**2 · 路由、9 类视频、文档**（25–42.25 s）

https://github.com/user-attachments/assets/71f1b4b9-a111-48f0-bd11-c20046a1dffc

**3 · 它是怎么工作的：关卡、自查回环、成片**（42.25–61.3 s）

https://github.com/user-attachments/assets/cd98390a-a333-4350-9afe-05c8f871eb75

**4 · 风格、声音、开箱即用、案例**（61.3–74.5 s）

https://github.com/user-attachments/assets/811ce8ee-dd7b-4f7e-9278-7b4f9eca6438

**5 · 放映厅：四支真实的片子**（74.5–89.75 s）

https://github.com/user-attachments/assets/ad345818-f36b-44e1-88b0-d939bcda3814

**6 · 这支片子也是；片名**（89.75–103 s）

https://github.com/user-attachments/assets/a7ff6e5e-24af-49de-b005-b68e48188b57

## 你说了什么（原话）

- 关卡 ①（2026-10-01）："开场还可以，但是不够震撼，特效不好，不连贯，而且瀑布流看起来都是一样的片子，最好各种各样很多片子，玻璃、宇宙、星穹等感觉要让人已看到开头就被吸引，令人瘫坐眩晕的感觉"
- 看完 WebGL 版的 look-dev（10-02）："有一点点廉价特效的感觉？……是否这些片子可以以星河、恒星等形式展现？或者使用blender？好莱坞大片质感"
- 看完 Blender 版（10-02）："不过是否很多地方存在一些抖动，前面有几处不是特别连贯……从15秒开始还是正常非blender的渲染1080p，就前15秒blender……直接做最终版吧"
- 看完 150.5 秒那版（10-04）："整体片子开头之后的内容节奏都太慢了，文字显示后停顿时间过长了最早的版本节奏是合理的，除了当时个别镜头太快"；"很多字的停顿就太长了  但也不是那种一闪而过的 要优化体验"。看完这一版："节奏可以（个别bgm音效要和视频内容节奏同步就好了）"

完整的原话、每一关的决定和代审记录在 [REVIEW.md](REVIEW.md)，agent 自己定的事和理由在 [DECISIONS.md](DECISIONS.md)。

## 片子讲什么

立意：**每颗星都是一支片子。** AI 视频工具多到成了一个星系；星系坍缩、爆开，被二向箔压平，再由 harness 整理成网格，收成一句需求：不缺工具，缺门道。

| 时间 | 画面 | 引擎 |
|---|---|---|
| 0–4.2 s | 一张玻璃卡片里是地球；镜头飞速拉远，四周都是片子，原来这张卡只是一个星系里的一颗星。"AI 视频工具，多到数不清。" | Blender |
| 4.2–8.0 s | 星系越转越快，镜头螺旋着往下坠，一层影片从镜头前扫过 | Blender |
| 8.0 s | 星系坍缩、爆开：冲击环、带红青丝缕的气体壳、四散的影片（全片唯一一次全屏闪白） | Blender |
| 9.0–10.4 s | 二向箔：一圈光扫过平面，把碎片压成一片影片之海 | Blender |
| 10.4–13.8 s | "差的是什么？" | Blender |
| 14.0–18.8 s | 琥珀色扫光把影片整理成通向地平线的网格；OpenVideoHarness · Not more tools. Know-how. / 不缺工具，缺门道。 | Blender，15.0–15.6 s 溶解进 WebGL |
| 18.6–25.0 s | 一行行收成文字；终端里打出一句需求（"做一个竖屏科普：为什么低轨卫星的信号会'变调'"，也就是样片 02 回答的那个问题）；回车，镜头扎进去 | WebGL + DOM |
| 25.0–42.25 s | 路由：需求 → Claude Code / Codex → CLAUDE.md 路由 → 9 类视频（需求所属的 02 科普短视频亮起，其余变暗）→ playbook、模板、风格、bin/vh → 引擎、参考仓库 → projects/ | Three.js |
| 42.25–61.3 s | 这句需求走一遍流程：三道人工关卡，每道都是用被审的东西做成的门（02 的大纲、分镜、初版联系表）；自查回环（三次报错各有一帧 02 变红，最后全部通过）；成片处播的就是 02，外加 LESSONS.md | Three.js |
| 61.3–70.75 s | 31 种风格的样片墙 · 声音一条龙 · 开箱即用 | Three.js |
| 70.75–74.5 s | 13 个案例拆解，一颗星一颗星亮起 + 389 支社区作品 | Three.js |
| 74.5–88.75 s | 放映厅：样片 01、03、02、00 的真实片子 | Three.js |
| 88.75–95.5 s | 这支片子也是 · 连配乐都是代码 | Three.js |
| 95.5–103 s | 片名、安装命令、GitHub 地址 | Three.js |

开场那些影片的小画框在正文的世界里一直飘着，"每颗星都是一支片子"从第一帧贯穿到最后一帧。

## 怎么做的

- **开场（0–15.8 s）：Blender 5.2，Cycles，Metal。** [`blender/galaxy.py`](blender/galaxy.py) 用 numpy 逐帧算出 118 万颗星、1.6 万颗靠近镜头会变成玻璃卡片的"片星"，以及帘幕里的 260 张卡片的位置，写进网格再渲染。运动模糊靠每个点的 `velocity` 属性和逐帧的相机关键帧。旋臂光雾、尘埃带、爆开的气体都是体积着色器，[`blender/nodexpr.py`](blender/nodexpr.py) 把数学式编译成着色器节点。1080p，64 采样（特写 96），不降噪，475 帧在 M3 Max 上用了 1 小时 28 分。Blender 在沙箱里跑（不联网、只能写输出目录、不继承环境变量，见 [`tools/bl.sh`](tools/bl.sh)），分块、可续渲（[`tools/bl_render.sh`](tools/bl_render.sh)）。
- **交接（15.0–25 s）：WebGL。** [`tools/export_state.py`](tools/export_state.py) 不启动 Blender，从同一份 `galaxy.py` 导出每张卡片的格位、片源和逐帧相机；[`js/grid.js`](js/grid.js) 用同一个相机重画同一批卡片，两边在 15.0–15.6 s 交叉溶解。字和终端是 DOM（[`js/open-overlay.js`](js/open-overlay.js)），不经过任何后期。
- **正文（25 s 起）：v3 的一镜到底世界**（[`js/main.js`](js/main.js)、[`js/arch.js`](js/arch.js)、[`js/pipeline.js`](js/pipeline.js)、[`js/features.js`](js/features.js)），速度从 90 BPM 改成 80 BPM，数字更新到现在的仓库（9 类、13 篇 playbook、11 个模板、31 种风格、30 个参考仓库、13 个案例、21 个音效、102 种乐器），加了 31 种风格的样片墙和路边飘着的影片，去掉了时码 HUD。
- **节奏。** 故事写在一条 87.5 秒的时间线上，经过一张时间表（[`js/tmap.js`](js/tmap.js)）播放：只有 15 处会一闪而过的地方放慢一点，每条字停到中英文任选一种能读完一遍为止（英文约每秒 20 个字符，中文约每秒 7 个字，再加 0.8 秒，最少 1.5 秒），然后镜头就走。飘着的影片、火花、手持晃动按片子自己的时间走，放慢的那几处世界不会停。之前有一版按更严的读时公式拉长了 26 处，片长 150.5 秒，每条字后面都像卡住了；这一版回到 87.5 秒的节奏，只多了 15.5 秒。
- **片源：109 段。** 28 段是着色器（星云、黑洞、玻璃、极光、海……，[`opening/films.js`](opening/films.js)），41 段截自本仓库的风格样片和样片成片（[`tools/film_atlas.py`](tools/film_atlas.py)），40 张 AI 静图（`gemini-3.1-flash-image`，16:9、512 px，约 1.8 美元；图和提示词在 [`assets/ai/`](assets/ai/)，[`tools/gen_images.py`](tools/gen_images.py)）加慢推，看起来像在播放。只画虚构的人和地方，没有品牌和商标。
- **声音。** 开场用关卡 ① 的配乐草图（120 BPM，主旋律 B：F# A B 往上走，停在问句上），终端那一停把它的第 11 小节奏两遍。25 秒起接 v3 的电影感配乐（[`audio/score.json`](audio/score.json)，80 BPM，D 小调），从它的第 10 小节进；[`tools/retime.py`](tools/retime.py) 把含放慢处的 12 个小节按整拍加长，加长的部分织体照常往下走，音乐不会为读字停下来。124 个音效落在画面事件上（[`audio/events.json`](audio/events.json)，片子时间）。做过一次声画同步检查：把配乐里每个有名字的重音和同一画面事件的音效配对，挪回了之前几轮改画面时没跟着动的四处：第二对目录卡片、13 颗案例星（13 个钢片琴音，一颗星一个）、"这支片子也是"、片尾打字。`bin/vh mix profile=promo` 混到 −14 LUFS；[`tools/build_audio.sh`](tools/build_audio.sh) 从源文件重建全部声音并跑 `bin/vh qa`。

## 检查

- `bin/vh check`：没有黑场、定格、静音；yuv420p、limited range、BT.709，四个颜色标签齐全。
- 全片只有一次全屏闪白（8.0 s 爆开）。
- 读时：之前几版出过问题的字，逐帧（每秒 4 帧）量过，每条停 1.4–2.75 秒。
- 声画同步，量过：每个大的画面事件（爆开、每次到站、关卡通过、报错、通过、片名）都有声音落在一帧之内；配乐里每个有名字的重音都和它对应画面事件的音效重合（偏差 0.00 秒）。
- 镜头连贯，量过：Blender 的 475 帧算了帧差曲线（平滑起落；只有爆开和 5.1 s 一张卡片掠过镜头两处跳变，都是设计的），每次改时间以后整片也算一遍（放慢处没有一顿一顿；剩下的跳变是甩镜、上电和放映厅片子里的剪辑点）。
- Blender 确定性（正式底片）：第 100、300 帧在新进程里重渲，和序列比 PSNR 71.3 dB、47.3 dB（底线 45 dB）。
- 声音（`bin/vh qa`）：没有数字静音、掉音、抽吸；62 个卡点全部在一帧以内（中位 6.0 ms）；−14.0 LUFS，−1.65 dBTP。click 提醒见下面。

## 独立评审

你授权跳过关卡 ②③（"直接做最终版"），所以由全新上下文的 reviewer 代审，对照 `templates/TASTE_CHECKLIST.md` 的 20 条和 8 项打分：

| 轮 | 版本 | 立意 | 钩子 | 桌面可读 | 运动 | 变化 | 完成度 | 准确 | 声画 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | draft 2（第一版 Blender 底片） | 6 | 7 | 5 | 6 | 6 | 5 | 7 | 7 |
| 2 | draft 3，87.5 s | 6 | 7 | 6 | 7 | 8 | 5 | 7 | 7 |
| 3 | 正式底片，87.5 s | 7 | 8 | 6 | 7 | 7 | 6 | 7 | 8 |
| 4 | 130 s（拉长 21 处） | 8 | 7 | 8 | 7 | 7 | 7 | 9 | 8 |
| 5 | 147.5 s（拉长 26 处） | 7 | 7 | 8 | 8 | 6 | 7 | 7 | 7 |

每轮改了什么在 [NOTES.md](NOTES.md)。改动最大的一处来自第 5 轮：开头打的那句需求贯穿了正文（9 类里它那一类亮起来，三道关卡的门是它的大纲、分镜、初版，自查回环里是它的帧变红，成片处播的就是它）。五轮之后你自己看了：第 3–5 轮把停留按严格的读时公式越拉越长，150.5 秒那版看着很慢。这一版 103 秒就是针对这个改的，节奏你认可了；reviewer 没有再给它打分。

## 复现

```bash
tools/fetch_media.sh 00-promo 01-hand 02-short 03-math v3            # 在仓库根目录：从 GitHub Release 下载截片源要用的样片和 v3
cd showcase/04-intro-film
npm i && bash tools/make_clips.sh                                    # HyperFrames、three；样片 00–03 的代理 → assets/clips/
bash tools/opening_export.sh                                         # 着色器片源 → assets/films-proc.png，开场那张片 → assets/hero-earth.png
uv run --no-project --with pillow python tools/film_atlas.py         # 41 段本仓库样片 → assets/films.jpg（逐字节相同）
uv run --no-project --with pillow python tools/ai_atlas.py           # 40 张 AI 生图 → assets/films-ai.jpg（以及远处卡片用的小图集）
tools/bl_render.sh 0 474 final2                                      # Blender 开场，1080p，约 1 小时 28 分（只在 macOS 上）
uv run --no-project --with numpy python tools/export_state.py       # 卡片和相机 → assets/state.json
uv run --no-project --with pillow python tools/request_tex.py ../02-short-leo-doppler   # 关卡的门和自查回环：02 的分镜、初版联系表、帧
bash tools/deliver.sh                                                # 底片、HyperFrames 渲染、声音（tools/build_audio.sh）、质检、编码、封面、联系表、README 的 6 段
```

Blender 这几步只在 macOS 上跑：`tools/bl.sh` 用 `sandbox-exec` 套沙箱，`galaxy.py` 用 Metal 渲染（别的系统自己跑 Blender，并改 Cycles 的设备）。`tools/deliver.sh` 写出的 `out/final.mp4` 就是 Release 里那个文件；`tools/chapters.sh` 切出 README 里的 6 段（1080p，每段不到 10 MB），`tools/watermark.sh` 加角上的小字（其他样片在 README 里的播放版也是用它加的）。AI 生图不能逐字节重来，`assets/ai/` 里就是用的那 40 张。改了 [`js/tmap.js`](js/tmap.js) 以后跑 `python3 tools/retime.py`（配乐、音效、几段素材的窗口），再重建声音。`tools/self_sheets.sh <draft.mp4>` 把这支片子自己的帧烤进"这支片子也是"后面那面墙（先渲 draft，再出正式版）。

## 已知的不完美

- **8 项没有全到 8 分。** 最低是"变化"（6）：25 秒以后每一站都是同一套语法（滑进来、停、标签、甩走），在同一条琥珀色的走廊里。
- **配乐里的 click 提醒。** `bin/vh qa` 在配乐 stem 里报了约 140 处硬边，来自 v3 配乐 pulse 声部锯齿波的门限。现在放慢处鼓不撤了，没有 150.5 秒那版（约 190 处）那么露，但还没有人耳复听过。
- **8.0 秒爆开那一下**大部分能量在 150 Hz 以下，笔记本扬声器上偏弱；起音靠叠的一层 whip。
- **终端那一停**是把开场草图的一个小节奏了两遍。
- **重新导出着色器图集**（`tools/opening_export.sh`）时第 27 行（地球片）会和 Blender 用的那版略有不同：地球着色器在导出之后改过（其余 27 行逐像素相同）。
- **无损帧确定性**只量了 Blender 底片，这一版的 HyperFrames 正文没有量过。
