# OpenVideoHarness 介绍片 v5：星河开场 + 一镜到底


成片 [`media/final.mp4`](media/final.mp4) · 1920×1080 · 30 fps · **150.5 s（4515 帧）** · −14 LUFS · 封面 [`media/poster.png`](media/poster.png) · 联系表 [`media/sheet.jpg`](media/sheet.jpg) · English: [README.md](README.md)

做法：精品档（studio）。开场 15.8 秒用代码驱动 Blender 路径追踪渲出来，之后交给 HyperFrames + Three.js。片里的每个数字都照抄自仓库，出处在 [NOTES.md](NOTES.md)。上一版（v3，81 秒）在 [v3/](v3/)。

## 观看：8 段 1080p

每段都能在这里直接播放，有声音（1080p，每段不到 10 MB，这是 GitHub 内嵌视频的上限）。整片一个文件：[`media/final.mp4`](media/final.mp4)。

**1 · 星河开场**（0–19 s）

https://github.com/user-attachments/assets/9d305423-0e5b-4276-a347-17a072993b6f

**2 · 一句话需求、路由、9 类视频**（19–42.5 s）

https://github.com/user-attachments/assets/e8b2244e-ca6b-4f2a-957e-f1df0cf15924

**3 · 文档、工具、引擎**（42.5–57 s）

https://github.com/user-attachments/assets/97229621-c60c-4977-93f8-bb193f982fdf

**4 · 它是怎么工作的：人工关卡**（57–68 s）

https://github.com/user-attachments/assets/a7e26949-b99b-4bcb-a491-265d77f42354

**5 · 自查回环和成片**（68–87.5 s）

https://github.com/user-attachments/assets/bc9ec77a-a3a8-463e-a622-9f6d6ae8fa4d

**6 · 风格、声音、开箱即用、案例**（87.5–111.5 s）

https://github.com/user-attachments/assets/1300a17c-579e-4241-9fbd-c766f197c572

**7 · 放映厅：四支真实的片子**（111.5–133 s）

https://github.com/user-attachments/assets/d65a9393-2cb4-497c-8341-97ccb5b80d68

**8 · 这支片子也是；片名**（133–150.5 s）

https://github.com/user-attachments/assets/d0040464-bd4a-43c8-83cd-fe0c9e4119bf

## 你说了什么（原话）

- 关卡 ①（2026-10-01）："开场还可以，但是不够震撼，特效不好，不连贯，而且瀑布流看起来都是一样的片子，最好各种各样很多片子，玻璃、宇宙、星穹等感觉要让人已看到开头就被吸引，令人瘫坐眩晕的感觉"
- 看完 WebGL 版的 look-dev（10-02）："有一点点廉价特效的感觉？……是否这些片子可以以星河、恒星等形式展现？或者使用blender？好莱坞大片质感"
- 看完 Blender 版（10-02）："不过是否很多地方存在一些抖动，前面有几处不是特别连贯……从15秒开始还是正常非blender的渲染1080p，就前15秒blender……直接做最终版吧"

完整的原话、每一关的决定和代审记录在 [REVIEW.md](REVIEW.md)，agent 自己定的事和理由在 [DECISIONS.md](DECISIONS.md)。

## 片子讲什么

立意：**每颗星都是一支片子。** AI 做视频的工具多到成了一个星系；它坍缩、被二向箔压平，再被 harness 整理成网格和一行需求：不缺工具，缺门道。

| 时间 | 画面 | 引擎 |
|---|---|---|
| 0–4.2 s | 一张玻璃片里的地球；镜头飞速拉远，四周全是片子，原来它只是一个星系里的一颗星。字：So many AI video tools. / AI 视频工具，多到数不清。 | Blender |
| 4.2–8.0 s | 星系越转越快，镜头在上方螺旋下坠，一层片子被卷着掠过（眩晕） | Blender |
| 8.0 s | 星系坍缩成超新星：冲击环、带红青两色丝缕的气体壳、四散的片子（全片唯一一次闪白） | Blender |
| 9.0–10.4 s | 二向箔：一道光环扫过，三维的碎片被压成一片影片之海 | Blender |
| 10.4–13.8 s | What's missing? / 差的是什么？ | Blender |
| 14.0–18.8 s | 琥珀扫光把影片整理成通向地平线的网格；OpenVideoHarness · Not more tools. Know-how. / 不缺工具，缺门道。 | Blender → 15.4 s 起 WebGL |
| 18.6–29.0 s | 网格收成一行行文字，终端里打出一句需求（“做一个竖屏科普：为什么低轨卫星的信号会‘变调’”，就是 showcase 02 回答的那一句）；回车，镜头钻进终端 | WebGL + DOM |
| 29.0–56.75 s | 路由：这句需求 → Claude Code / Codex → CLAUDE.md 路由 → 9 类视频，它自己那一类（02 科普）亮起来，其余变暗 → playbook、templates、styles、bin/vh → engines、references → projects/ | Three.js |
| 56.75–87.5 s | 这句需求走一遍工作流：三道人工关卡，每道门都是被审的东西（02 的大纲、分镜、初版联系表）；自查回环（三次不合格，每次 02 的一帧变红，然后全部通过）；成片处播的就是 02，+ LESSONS.md | Three.js |
| 87.5–106.25 s | 31 种风格的样片墙 · 声音一条龙 · 开箱即用 | Three.js |
| 106.25–111.5 s | 13 个案例拆解 + 389 支社区作品 | Three.js |
| 111.5–133.25 s | 放映厅：showcase 01、03、02、00 的真实成片 | Three.js |
| 133.25–142.25 s | 这支片子也是 · 连配乐都是代码 | Three.js |
| 142.25–150.5 s | 片名、安装命令、GitHub 地址 | Three.js |

正文的空间里一直飘着开场那些片子的小画面，"每颗星都是一支片子"从头走到尾。

## 怎么做的

- **开场（0–15.8 s）：Blender 5.2，Cycles，Metal。** [`blender/galaxy.py`](blender/galaxy.py) 用 numpy 逐帧算出 118 万颗星、1.6 万张会变成玻璃卡片的"片星"和 260 张影片帘幕的位置，写进网格再渲；运动模糊来自每个点的 `velocity` 属性和相机的逐帧关键帧。旋臂光雾、尘埃带、超新星的气体都是体积着色器，用 [`blender/nodexpr.py`](blender/nodexpr.py) 把数学式编译成节点。1080p、64 采样（特写 96）、不降噪，475 帧渲了 1 小时 28 分（M3 Max）。Blender 在沙箱里跑：不联网、只能写输出目录、不继承环境变量（[`tools/bl.sh`](tools/bl.sh)）；分块、可续渲（[`tools/bl_render.sh`](tools/bl_render.sh)）。
- **接力（15.0–29 s）：WebGL。** [`tools/export_state.py`](tools/export_state.py) 不启动 Blender，从同一份 `galaxy.py` 导出每张卡片的格位、片源和逐帧相机；[`js/grid.js`](js/grid.js) 用同一个相机重画同一批卡片，两边在 15.0–15.6 s 交叉溶解。字和终端是 DOM（[`js/open-overlay.js`](js/open-overlay.js)），不经过任何后期，永远清晰。
- **正文（29 s 起）：v3 的一镜到底世界。** [`js/main.js`](js/main.js)、[`js/arch.js`](js/arch.js)、[`js/pipeline.js`](js/pipeline.js)、[`js/features.js`](js/features.js)。相对 v3：速度从 90 降到 80 BPM；第 3、4 轮评审之后，又把 26 个停留段拉长，让每句字都停够清单的读时下限（[`js/tmap.js`](js/tmap.js)：故事写在旧的 87.5 s 时间线上，按这张表取帧，飘着的片子、火花和手持漂移走真实时间；[`tools/retime.py`](tools/retime.py) 按同一张表搬配乐的小节、事件和音效）；数字更新到现在的仓库（9 类、13 篇 playbook、11 个模板、31 种风格、30 个参考仓库、13 个案例、21 个音效、102 种乐器）；"把品味写成数字"那块换成 31 种风格的样片墙；路径两边飘着开场的片子；标签加了更深的底板，连线从字后面穿过；去掉了时间码 HUD。
- **片源：109 段。** 28 段是着色器生成的（星云、黑洞、玻璃、极光、海……，[`opening/films.js`](opening/films.js)），41 段截自本仓库的风格样片和样板片（[`tools/film_atlas.py`](tools/film_atlas.py)），40 张是 AI 生图（`gemini-3.1-flash-image`，16:9、512 px，约 1.8 美元；图和提示词在 [`assets/ai/`](assets/ai/)，[`tools/gen_images.py`](tools/gen_images.py)），在卡片里做慢推，看起来像在播放。只用虚构的人物和地点，没有品牌和 logo。
- **声音。** 开场是关卡 ① 的配乐草图（120 BPM，主旋律 B：F# A B 往上走、在问句里悬住）；第 11 小节为终端那一停多奏三遍；29 s 起接 v3 的电影感配乐（[`audio/score.json`](audio/score.json)，改成 80 BPM，D 小调，为停留段加长了 20 个小节，加出来的部分是一口屏住的气，鼓撤掉），从它的第 10 小节开始。124 个音效事件按画面动作摆（开场的在 [`audio/events.json`](audio/events.json) 前 39 条）。`bin/vh mix profile=promo` 混到 −14 LUFS，`bin/vh qa` 通过。

## 检查

- `bin/vh check`：没有黑场、定格、静音段；yuv420p、limited range、BT.709，四个色彩标签齐全。
- 全片只有一次全屏闪白（8.0 s 的超新星）。
- 镜头连续性用数字查过：475 帧 Blender 底片的帧差曲线平滑起落，只有超新星和 5.1 s 一张卡片掠过镜头两处跳变，都是设计的；每次改时间线以后整片再扫一遍，拉长的停留段里没有“停几帧再跳一下”，剩下的跳变都是甩镜、节点通电和放映厅里那几支片子自己的剪切。
- Blender 确定性：第 100、300 帧在新进程里重渲，和序列比 PSNR 71.3 dB、47.3 dB（底线 45 dB）。
- 音频（`bin/vh qa`）：0 数字静音、0 掉音、0 抽吸；62 个卡点都在 1 帧以内（中位 5.1 ms）；−14.0 LUFS，−1.65 dBTP。click 提醒见下文。
- 读时：reviewer 从帧上按清单公式、分语言量；第 3、4、5 轮之后各拉长过一次停留（第 5 轮最后的修改没有再量）。

## 独立评审

关卡 ②③ 你授权跳过（"直接做最终版吧"），由全新上下文的 reviewer 代审，按 `templates/TASTE_CHECKLIST.md` 的 20 条和 8 项打分：

| 轮 | 片子 | 立意 | 钩子 | 桌面可读 | 运动 | 变化 | 完成度 | 准确 | 声画 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | draft 2（第一版 Blender 底片） | 6 | 7 | 5 | 6 | 6 | 5 | 7 | 7 |
| 2 | draft 3，87.5 s | 6 | 7 | 6 | 7 | 8 | 5 | 7 | 7 |
| 3 | 最终底片，87.5 s | 7 | 8 | 6 | 7 | 7 | 6 | 7 | 8 |
| 4 | 130 s（拉长 21 个停留段） | 8 | 7 | 8 | 7 | 7 | 7 | 9 | 8 |
| 5 | 147.5 s（26 个停留段） | 7 | 7 | 8 | 8 | 6 | 7 | 7 | 7 |

每轮改了什么在 [NOTES.md](NOTES.md)。第 5 轮的修改都在这一版里，没有再审：你说这一轮做完就提交。精品档的线（8 项都 ≥ 8）没有到，剩下的写在“已知的不完美”。改动最大的一处来自第 5 轮：开头打的那句需求现在贯穿正文（9 类里它那一类亮起来，三道关卡的门是它的大纲、分镜、初版，自查回环里是它的帧变红，成片处播的就是它）。

## 复现

```bash
cd showcase/04-intro-film
npm ci && bash tools/make_clips.sh                                   # HyperFrames、three；showcase 00–03 的代理 → assets/clips/
uv run --no-project --with pillow python tools/film_atlas.py         # 41 段本仓库样片 → assets/films.jpg
uv run --no-project --with pillow python tools/ai_atlas.py           # 40 张 AI 生图 → assets/films-ai.jpg（以及远处卡片用的小图集）
bash tools/opening_export.sh                                         # 着色器片源 → assets/films-proc.png，开场那张片 → assets/hero-earth.png
tools/bl_render.sh 0 474 final2                                      # Blender 开场，1080p，约 1 小时 28 分
uv run --no-project --with numpy python tools/export_state.py       # 卡片和相机 → assets/state.json
uv run --no-project --with pillow python tools/request_tex.py ../02-short-leo-doppler   # 关卡的门和自查回环：02 的分镜、初版联系表、帧
bash tools/deliver.sh                                                # 底片、HyperFrames 渲染、声音（tools/build_audio.sh）、质检、编码、封面、联系表
```

AI 生图不能逐字节重来：`assets/ai/` 里就是用的那 40 张。片子写在旧的 87.5 s 时间线上，按 [`js/tmap.js`](js/tmap.js) 播放；改了这张表以后跑 `python3 tools/retime.py`（配乐、音效、几段素材的窗口），再重建声音。`tools/self_sheets.sh <draft.mp4>` 把这支片子自己的帧烤进“这支片子也是”后面那面墙（先渲 draft，再出正式版）。

## 已知的不完美

- **8 项没有全到 8 分。** 最低是“变化”（6）：29 s 以后每一站都是同一套语法（滑进来、停、标签、甩走），在同一条琥珀色的走廊里。
- **150.5 s 对介绍片来说偏长。** 读时下限让它从 87.5 s 长到这么长；要更短得减站点，不能把每站再加快。
- **配乐里的 click 提醒。** `bin/vh qa` 在配乐 stem 里报了约 190 处硬边，来自 v3 配乐 pulse 声部锯齿波的门限；停留段里鼓撤掉以后更露。没有人耳复听过。
- **8.0 s 超新星那一下**大部分能量在 150 Hz 以下，笔记本扬声器上偏弱；起音靠叠的一层 whip。
- **终端那一停**是把开场草图的一个小节多奏了三遍。
- **重新导出着色器图集**（`tools/opening_export.sh`）时第 27 行（地球片）会和 Blender 用的那版略有不同：地球着色器在导出之后改过（其余 27 行逐像素相同）。
- **无损帧确定性**只量了 Blender 底片，这一版的 HyperFrames 正文没有重量。
