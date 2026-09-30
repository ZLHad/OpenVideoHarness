# 05 混合管线：生成式视频 + 代码

纯代码擅长排版、图形、手绘和数据可视化，但做不好写实人物、真实物理和实拍感。遇到后者，就把生成式视频模型接进来。这条路要花钱，而且结果不确定，所以动手前先在 BRIEF 里和用户确认预算、发布平台，以及素材里有没有真人；用了生成片段，还要记许可和披露（见"许可、条款与披露台账"）。

**本章的核对状态（2026-10-01）**：模型、价格、参数对着官方页面核对过（Sora、Seedance 2.5、Veo 3.1、Gemini Omni、Runway，以及 Runway 和 Google 的条款），查不到官方页的标【二手】。匹配与 QA 的方法，凡是能在本机用 ffmpeg 8.0.1 和 numpy 跑的都跑了，标【本机实测】。**本机没有视频模型的 key，没有调用过任何一个视频模型**，所以凡是涉及真实生成结果的阈值都是【推测】，要在第一个真实项目里校准。模型和价格半年就会过时，每个项目开工时重查（见"时效"）。引用编号 `[n]` 见文末"来源"。

## 四种模式

| 模式 | 做法 | 门槛 | 例子 |
|---|---|---|---|
| **A. Opus 当导演** | Opus 写角色设定、首帧和逐镜 prompt，再调用图像和视频模型出片，最后用代码剪辑合成 | 中 | 社区经验：prompt 里要讲清楚谁拿着相机、站在哪里、怎么移动 |
| **B. 生成素材做底，代码叠图形** | 在 HyperFrames 或 Remotion 里放一条 `<video>` 轨道，上面叠字幕、图形、数据 | 低 | 最常用；口播加图解也属于这一类 |
| **C. 代码做 blockout，喂给模型当参考** | 先在 Blender 里搭粗模、定机位，导出 mp4，作为视频模型的参考输入 | 中高 | 社区案例：参考视频按 15fps 抽帧，Opus 逐镜在 Blender 里搭 blockout，再交给 Seedance 2.5。Seedance 2.5 最多收 10 个视频参考；Blender 的做法见 `engines/blender.md`（实验性） |
| **D. 转描（rotoscope）** | 生成视频只当动作和构图参考；JS 在上面逐帧重画，成片只保留 JS 那一层 | 高 | donald jewkes 的 Claude Pop，见 `cases/mv-claude-pop.md` |

## 选模型（2026-10-01）

这张表半年就会过时。规格和价格以官方页面为准，随时会变；"备注"里只写对我们有影响的。

| 模型 | 时长 | 分辨率与帧率 | 参考与一致性 | 音频 | 备注 |
|---|---|---|---|---|---|
| **Seedance 2.5**（ByteDance；fal、Runway） | 4–30 s | fal：480p、720p，没有 fast 档。Runway：480p、720p，**2026-08-15 起另有 1080p** [3]。帧率页面没写，计费公式里的 ×24 暗示 24 fps【推测】 | 最多 50 个参考：30 图、10 视频、10 音频；有 `seed` 参数 [1][2] | 原生，`generate_audio` 默认开 [2]；对白写在双引号里触发口型 [1] | 2.0（2026-02）是 4–15 s、480p–4K、12 个参考。2.0 遇到好莱坞的侵权投诉后，ByteDance 在 2026-02-15 宣布暂停生成逼真的人脸和受 IP 保护的角色，3 月中旬暂停全球推广 [11]；另有报道称含真人脸的图像和视频输入也被拦截【二手】 |
| **Kling 3.0 / 3.0 Turbo / 3.0 Omni**（Kuaishou） | 单镜头 3–15 s；多镜头 2–6 镜 | 720p、1080p、4K 三档【二手】[4] | Omni：最多 7 张参考图、持久 element、首尾帧、参考视频【二手】[4] | 原生，多语言口型 | 3.0 于 2026-02 发布；Turbo 与 Omni 升级 2026-06-17 发布【二手】。**Kling 4.0 在 2026-09-28 宣布，截至 2026-10-01 尚未上线**：Flash 小范围内测（3–20 s，720p，8 位），完整版十月上线，计划 ≤ 30 s、4K、10 个关键帧、最多 15 个输入（报道写图像最多 10、视频最多 5、已保存主体最多 7，三项相加超过 15，原文如此）、10 位 HDR"即将推出"，价格未公布【二手】[5] |
| **Veo 3.1 / Fast / Lite**（Google；Gemini API、Vertex） | 4、6、8 s；1080p、4K、参考图、延长时必须 8 s | 720p 默认、1080p、4K（Lite 没有 4K）；**24 fps**；16:9 或 9:16 | 最多 3 张参考图；首尾帧；延长最多 20 次、每次 7 s，只限 720p，总长最多 148 s [6] | 原生，始终开启 | 输出带 SynthID；服务器只保留 2 天，要及时下载；欧盟、英国、瑞士、中东北非的 `personGeneration` 只允许 `allow_adult` [6]。模型 ID 仍带 `preview`（`veo-3.1-generate-preview` 等）。Veo 2.0 与 3.0 已在 2026-06-30 下线 [8] |
| **Gemini Omni Flash 1.1**（Google） | — | `gemini-omni-1.1-flash`，2026-08-27 正式发布；360p–4K 分辨率可选 [8] | 对话式视频编辑：视频延长、图像间插值 [8] | — | Google 在 I/O 2026 没有推 Veo 4，而是推了 Omni 这条新线【二手】 |
| **Sora**（OpenAI） | **已停** | — | — | — | **API 于 2026-09-24 移除**：2026-03-24 通知，涵盖 Videos API、`sora-2`、`sora-2-pro` 及各快照，官方没有给替代 [9]。应用和网页 2026-04-26 关闭【二手】[9]。不要再为它做计划。手上若有 Sora 时期的素材，保留当时的台账和水印、C2PA 元数据，不要重新编码后丢掉来源信息 |
| **Runway Gen-4.5**、**Aleph 2.0**、**Act-Two** | Gen-4.5：2–10 s，文生、图生视频，2026-02-10 发布。Aleph 2.0（2026-06-02）：视频编辑，输入 2–30 s 加最多 5 个关键帧图。Act-Two：用表演视频驱动角色 | 输出格式见下 | 图像侧有 GPT Image 2.5（最多 16 张参考图）[3] | — | 同一个 API 里还能调 Seedance 2.5、Veo 3.1、Gemini Omni Flash、Wan 3.0、Grok Imagine Video 1.5、MiniMax H3 等，并有按成本或延迟路由的 Model Router（2026-07-23）[3][10] |

**Runway 的输出格式**（Gen-4.5、Aleph 2.0；`outputFormat`）[3]：
- SDR：`prores`、`png_sequence`，每秒加 5 积分；
- 10 位和 HDR 系：`sdr_rec709_10bit`、`hdr10`、`hlg`、`hdr_pq_12bit_master`、`hdr_prores`、`hdr_png_sequence`、`hdr_exr_sequence`、`hdr_exr_acescg_sequence_1_3`、`hdr_exr_acescg_sequence_2_0`，每秒加 20 积分（输出超过 4 MP 时加 40）。HDR 系是按 BT.2020 或 ACES 出的真 HDR，EXR 是线性 BT.2020 光或 ACEScg；我们交付的是 BT.709 SDR，用它们要多一步色域和色调转换；本机 ffmpeg 没有 zscale、libplacebo、OCIO，只有 `colorspace` 和 `tonemap` 两个滤镜，做不了精细的转换，没有试过；
- 这些格式自 2026-08-20 起**按账号逐步开放**，没有开通时只能拿 mp4。

**其他**：
- **Wan 3.0**（Alibaba）：闭源；经 Runway 调用时单次最长 30 s，带原生音频，480p、720p、1080p [3]；开放权重的 Wan 线停在 2.2（Apache-2.0）【二手】[12]。
- **LTX-2.x**：开放权重，社区有 MLX 移植可在 Apple Silicon 上跑【二手】。本仓库 `references/open-source.md` 已列 Wan2.2 和 LTX-2，许可证要逐个核对。
- 没有出现的版本：Seedance 3、Veo 4、Runway Gen-5，截至今天都没有官方发布（搜索结果均无官方页面【二手】）。

### 价格

| 模型与通道 | 价格 |
|---|---|
| Seedance 2.5，fal | $0.0214 每千 token，token = 高 × 宽 × (输入视频秒数 + 输出秒数) × 24 ÷ 1024。页面给出 720p ≈ $0.473/s，带视频参考 ≈ $0.284/s；480p ≈ $0.2205/s 和 $0.1323/s [1][2]。美国托管的 `…/us/…` 端点更贵（约 $0.5676/s）【二手】[1] |
| Seedance 2.5，Runway | 输出每秒 480p 20、720p 30、1080p 68 积分；输入和参考视频每秒另加 10、15、34 积分（合计最多 30 s）；参考图和音频免费；每次最低 80 积分。1 积分 = $0.01 [3] |
| Veo 3.1 | 每秒：标准 $0.40（720p、1080p）、$0.60（4K）；Fast $0.10 / $0.12 / $0.30（720p / 1080p / 4K）；Lite $0.05 / $0.08（720p / 1080p）[7] |
| Gemini Omni Flash 1.1 | 约 $0.10/s（720p）[7] |
| Runway Gen-4.5 | 12 积分/s（$0.12/s），另加输出格式的积分（见上）；Aleph 2.0 28 积分/s，最低 56；Act-Two 5 积分/s；Enhance Frame Rate 每 2 秒 1 积分 [3] |
| Wan 3.0，Runway | 480p 5、720p 10、1080p 20 积分/s [3] |
| Kling 3.0 | 第三方统计约 $0.084–0.168/s（720p–1080p），4K 约 $0.42/s【二手】[4]；官方价目页没能抓到 |

同一个模型，不同通道的价格和分辨率档位不一样（Seedance 2.5 在 Runway 的 720p 比 fal 便宜，还有 1080p），开工前两边都查。

### 什么情况下怎么选

| 需求 | 倾向 | 理由与代价 |
|---|---|---|
| 长镜头（≥ 15 s）、多参考、要在一次生成里锁角色、场景、色板 | Seedance 2.5 | 30 s、50 个参考。经 fal 上限 720p：交付 1080p 要放大，放大后和代码层的清晰度对不上，要补颗粒（见"匹配清单"(b)）；Runway 有 1080p 档，每秒 68 积分，不用放大 |
| 原生 1080p 或 4K 的画质，要调色余量 | Veo 3.1（8 s，24 fps）；Kling 3.0（4K 档）；Runway Gen-4.5 | Veo 标准档 $0.40/s，价格最高，有 Fast 与 Lite 两档便宜的 |
| **抠像或合成密集的镜头** | Runway Gen-4.5，要 `prores` 或 `png_sequence` | 省掉一次 H.264 压缩，抠像边缘更干净【推测：没有对比过抠像质量】；只有 2–10 s，每秒加 5 积分；格式要账号已开通。HDR 系（含 EXR）见上，先用 SDR 的两种 |
| 预算敏感，草稿和探索 | Veo 3.1 Lite（$0.05–0.08/s）、Seedance 480p、Kling Turbo、Wan 3.0 的 480p | 先用便宜档试 prompt 和构图，再上贵档 |
| 需要真人的表演或口型（例如借演员的动作） | Runway Act-Two；或自己录（类型 09） | 生成真人脸有肖像权和平台限制（见"许可、条款与披露台账"） |
| 要在已有素材上改光、改风格（视频到视频） | Runway Aleph 2.0；Gemini Omni Flash；Kling Omni 编辑 | 不确定性高。先用确定性的调色（匹配清单 (a)），不够再用它们 |
| 素材保密，或要完全本地 | LTX-2.x（MLX）、Wan 2.2 | 本机没有 NVIDIA GPU，速度和画质都要实测；先看许可证 |

模式对应：模式 A、B 用上表任何一个；模式 C（Blender blockout 当参考）选能收视频参考的（Seedance 2.5、Kling Omni、将来的 Kling 4.0）；模式 D（转描）选参考音频和参考视频最强的 Seedance 2.5；绿幕选 Runway，或背景纯色遵循度高的模型。

### 时效

每个项目开工时重新查三样：版本、价格、条款，并把查询日期和网址写进 NOTES.md 的台账。

## 给视频模型写运镜

只要让视频模型出片（模式 A、B、C），就要替它写运镜。只写"FPV""无人机镜头""一镜到底"这类名词，模型只能自己猜。每个镜头按下面写：

- **先分四层**，每层各定一个答案：
  - 稳定方式：画面晃多少。
  - 运动路线：摄影机沿什么路径走。
  - 观看视角：观众站在角色外面，还是借角色的眼睛。
  - 时间结构：这段中间切不切。
- **写成"起点 → 路径 → 终点 → 约束"**：从哪里出发，经过什么，停在哪里，最后列出不许发生的事（不切镜头、不穿透物体、不做完整翻滚、不超越人物、不瞬移）。距离、高度、角度、时长尽量写成数字。
- **5–8 秒的片段最多两个主动作。** 两个动作之间给一个触发点，可以是人物的动作，也可以是空间位置，例如"走过第二根立柱时"。没有触发点，模型常常一开始就把两个动作混在一起。
- **写明保持项**：人物大小、视线、焦点、轴线、服装和身份，哪些全程不变。
- **容易写错的几对概念**：
  - 手持不是乱抖：写"轻微的脚步起伏、呼吸漂移"，需要冲击感时再加大。
  - 稳定器也有惯性：写"绝对静止"反而丢了行走感。
  - 摇臂是弧线，升降是垂直换高度。
  - POV 看不到自己的完整正面。
  - 翻滚是持续在转，荷兰角是倾斜后停住。
  - 希区柯克变焦要"摄影机和变焦方向相反，主体大小不变"。
- **"一镜到底"也会出跳切**：写成"单一连续镜头，全程无剪切，不瞬移，空间方向保持一致"，而且每一段都从上一段的结束位置接着走。
- **要抠像合成的片段**（见"绿幕角色 + 代码场景"）用固定机位。镜头运动交给代码层的虚拟摄像机，前景和背景才出自同一台摄像机，合成后不穿帮。

来源：Adrian Punk 的《AI 视频运镜词典》[上篇](https://x.com/AdrianPunk115/status/2104172387575222768)、[下篇](https://x.com/AdrianPunk115/status/2104523576020017575)（X，2026-09-27、28）。版权归作者，这里只摘了方法；每个运镜词的示例提示词和可填空的模板，请看原文。本仓库还没有对照实测过。

## 模式 D 的落地方案（【综合】，未经实测）

1. **生成底片**：通过 fal 调 `bytedance/seedance-2.5/reference-to-video`。单次最长 30s，fal 上支持 480p 或 720p，最多可带 50 个图像、视频、音频参考；fal 页面称音频参考能作为时序信号。价格见"价格"一节：720p 每秒 $0.473，带视频参考时 $0.284（2026-10-01 对着 fal 页面核实过，按 token 计费）。备选：Runway 上的 Seedance 2.5（有 1080p 档）、Veo 3.1（单次 ≤ 8s）、Kling 3.0；端点名和价格以当天的官方页为准，这里不写没核对过的端点。
2. **抽取结构**：用 `ffmpeg -vf fps=24` 抽帧，再用 MediaPipe 提姿态、SAM 2 提遮罩、OpenCV 提边缘和光流，每一帧存成一个 `track/NNNNN.json`。
3. **重画**：在 `renderAt(t)` 里读取 `track[round(t*fps)]`，用 p5.brush 或 SVG 描线。这一步依然要保持纯函数。
4. **验证**：
   - 出三联联系表：底片、叠加层、两者合成；
   - 对嘴部做 crop strip，检查口型；
   - 把成片重新转写，核对时间。

## 片段入库：生成片段是冻结素材

像下文"边界：档案素材纪录片"里的素材一样：下载、记账、算哈希，渲染时不再调用模型。入库时做一次"合约归一化"。

1. **下载即冻结**：`assets/genclips/<id>/clip.mp4`，同目录放 `prompt.txt` 和 `ledger.json`（字段见"台账"一节），算 sha256。渲染时只读这个文件，不调用 API。供应商的下载链接会过期（Veo 只保留 2 天 [6]），所以**生成完立刻下载**。
2. **先 `ffprobe`**：编码、像素格式、分辨率、`r_frame_rate` 与 `avg_frame_rate`（不相等就是 VFR）、时长、色彩标签、音轨数量。
3. **归一化**（按需）：

   ```bash
   # CFR：生成片段偶尔是 VFR；不同步会让剪辑和合成的时间全错
   ffmpeg -i clip.mp4 -vf "fps=24" -c:v libx264 -crf 14 -pix_fmt yuv420p -c:a copy clip_cfr.mp4
   # 转 RGB 序列时要按片子真实的矩阵和范围读；未标记的高清片先假设 BT.709 tv【推测】，并用灰卡或肤色块复核
   ffmpeg -i clip.mp4 -vf "scale=in_color_matrix=bt709:in_range=tv,format=rgb24" frames/%05d.png
   # 黑边（letterbox）：cropdetect 给出 crop= 值；本机在合成的 640×360 加 40 px 黑边片上检出 crop=640:280:0:40【本机实测】
   ffmpeg -i clip.mp4 -vf "cropdetect=limit=24:round=2" -an -f null - 2>&1 | grep -o "crop=[0-9:]*" | sort | uniq -c | sort -rn | head -1
   # 内部硬切（Kling 3.0 的多镜头输出；别的模型也可能出现）：scdet 在硬切处给出分数和时间，本机在一条 2.0 s 处硬切的合成片上检出 time 2【本机实测】
   ffmpeg -i clip.mp4 -vf "scdet=t=10:s=1" -an -f null - 2>&1 | grep scdet
   ```

4. **色彩合约**：最后一步编码一律显式 BT.709（矩阵、范围、四个标签），命令和检查方法见 `playbook/02-verification.md` 的"色彩标签"。生成片段如果是无标签的 H.264，ffmpeg 默认按 BT.601 读，会读错：本机用一段按 BT.709 编码、再把标签改成 unspecified 的片子实测，默认解码最大偏 25 个色阶，显式给 `in_color_matrix=bt709:in_range=tv` 后是 3（8 位往返的基线）【本机实测】。
5. **音轨分离**：生成片段自带的音频（对白、环境声）单独抽成 wav 进音频管线，画面里的 `<video>` 保持静音（HyperFrames 的规则：视频静音，音频用单独的 `<audio>`）。
6. **工作格式**：要抠像或叠层的，转成 PNG 序列（straight alpha）或 ProRes 4444，不要存成 H.264，H.264 没有透明通道。

## 与代码画面匹配：逐项清单

合成后所有图层要像出自同一台摄像机。顺序建议：先各自归一（上一节），再按 (a)–(f) 逐项匹配，最后在**合成之后**整体做一次调色和一次颗粒。遮罩与抠像在下一节"绿幕角色 + 代码场景"。

### (a) 色彩与调色：先测量，再调，再测量

- **方法**：从代码画面里取一帧内容相近的参考帧，从生成片段里取一帧；在**背景区域**（排除主体）上分别算 CIELAB 的均值和标准差，用 Reinhard 等人的统计转移（逐通道把均值和标准差拉齐）[13]，把结果烘成 33³ 的 `.cube`，用 `lut3d=interp=tetrahedral` 套到**整段片段**（整段同一个 LUT，不逐帧算，避免闪烁）。调完重新测量。

  ```bash
  ffmpeg -i clip.mp4 -vf "lut3d=file=match.cube:interp=tetrahedral" -c:v libx264 -crf 14 -pix_fmt yuv420p clip_graded.mp4
  ```

- **【本机实测】**：在一对合成帧（暖色参考帧、冷色高反差帧）上，调前 Lab 均值 [39.1, 2.9, −32.6]、标准差 [24.7, 19.2, 17.8]；调后 [40.5, 9.5, 13.5]、[13.6, 15.6, 21.9]；参考帧是 [40.7, 9.4, 13.5]、[13.6, 15.7, 22.1]。ffmpeg 读 `.cube` 的方向没有搞反（R 变化最快）。本次复核换了一对合成帧，均值和标准差同样被拉到 0.2 个单位以内，`--strength 0.6` 只走了约六成。这只是合成图，**真实素材上全局统计会误伤肤色和高光**，所以：`--strength` 取 0.5–0.8 起步；人物单独用遮罩别套（或套更弱的）；目标是背景区域 ΔL* < 2、Δa*、Δb* < 3【推测的阈值】。
- **本机测试用的脚本**（numpy 加 Pillow，`uv run --with numpy --with pillow python match_grade.py ref.png src.png match.cube --strength 0.7`）：

  <details>
  <summary>match_grade.py：Lab 统计转移，输出 33³ 的 .cube</summary>

  ```python
  # match_grade.py ref.png src.png out.cube [--strength 1.0]
  # ref = 代码画面里内容相近的一帧（要匹配的样子），src = 生成片段里的一帧；两张都只留背景区域，主体先裁掉或遮掉
  import sys
  import numpy as np
  from PIL import Image

  M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
  WP = np.array([0.95047, 1.0, 1.08883])  # sRGB 原色，D65 白点


  def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
  def enc(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)
  def f(t): d = 6 / 29; return np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4 / 29)
  def finv(t): d = 6 / 29; return np.where(t > d, t ** 3, 3 * d * d * (t - 4 / 29))


  def to_lab(rgb):  # rgb 取 0–1，形状 (…, 3)
      fx = f(lin(rgb) @ M.T / WP)
      return np.stack([116 * fx[..., 1] - 16, 500 * (fx[..., 0] - fx[..., 1]), 200 * (fx[..., 1] - fx[..., 2])], -1)


  def to_rgb(lab):
      fy = (lab[..., 0] + 16) / 116
      fx, fz = fy + lab[..., 1] / 500, fy - lab[..., 2] / 200
      return enc((np.stack([finv(fx), finv(fy), finv(fz)], -1) * WP) @ np.linalg.inv(M).T)


  def stats(path):
      lab = to_lab(np.asarray(Image.open(path).convert("RGB"), np.float64) / 255).reshape(-1, 3)
      return lab.mean(0), lab.std(0)


  ref, src, out = sys.argv[1:4]
  k = float(sys.argv[sys.argv.index("--strength") + 1]) if "--strength" in sys.argv else 1.0
  (mr, sr), (ms, ss) = stats(ref), stats(src)
  gain = 1 + (np.where(ss > 1e-6, sr / ss, 1.0) - 1) * k  # 逐通道把标准差拉向参考……
  target = ms + (mr - ms) * k                              # ……再把均值拉过去；k < 1 只走一部分
  n = 33
  g = np.linspace(0, 1, n)
  B, G, R = np.meshgrid(g, g, g, indexing="ij")            # .cube 的顺序：R 变化最快，B 最慢
  rgb = to_rgb((to_lab(np.stack([R, G, B], -1).reshape(-1, 3)) - ms) * gain + target)
  with open(out, "w") as fh:
      fh.write(f'TITLE "match_grade"\nLUT_3D_SIZE {n}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
      fh.writelines(f"{r:.6f} {g_:.6f} {b:.6f}\n" for r, g_, b in rgb)
  print("ref", mr.round(1), sr.round(1), "src", ms.round(1), ss.round(1))
  ```

  </details>

- **HyperFrames 里也能做**：`media-use` 有 `.cube` LUT 和 `media-treatment` 的调色路径（`references/repos/hyperframes/skills/media-use/`），我推测都是 t 的纯函数【推测：没有读实现】，可以不预烘。
- **顺序**：先匹配生成片段，再对合成整体做一次风格调色。不要在每一层上各做各的风格。

### (b) 颗粒与清晰度

- **测量**：空间估计用 Immerkær 的快速噪声方差估计 [14]，时间估计用帧间差除以 √2（仅适用于静止区域）。【本机实测】在平灰底（640×360）上用 ffmpeg 的 `noise` 加噪、x264 crf 10 编码后量，空间和时间两个估计相差在 0.12 以内：

  | `noise=alls=k` | 2 | 4 | 6 | 8 | 12 |
  |---|---|---|---|---|---|
  | `allf=t`（`playbook/08` 用的这种） | σ 0.8 | 2.2 | **3.5** | 4.9 | 7.6 |
  | `allf=t+u`（均匀噪声） | σ 0.5 | 1.15 | 1.8 | 2.7 | 4.1 |

  所以 08 篇里的 `noise=alls=6:allf=t` 是 σ 约 3.5（crf 18 编码时约 3.0–3.4），不要和 `t+u` 的数字混用。σ 随后面的编码参数而变，用之前按自己的编码设置量一次。

  <details>
  <summary>grain_est.py：量一段片子的颗粒 σ</summary>

  ```python
  # grain_est.py clip.mp4 [秒数=2]：亮度噪声的 σ（8 位色阶）。空间估计用 Immerkaer 1996；时间估计只对静止内容有效
  import subprocess
  import sys
  import numpy as np

  clip, secs = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "2")
  probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0:s=x", clip], capture_output=True, text=True).stdout.strip()
  W, H = map(int, probe.split("x"))
  raw = subprocess.run(["ffmpeg", "-v", "error", "-t", secs, "-i", clip, "-vf", "format=gray", "-f", "rawvideo",
                        "-pix_fmt", "gray", "-"], capture_output=True).stdout
  fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float64)


  def immerkaer(a):  # 卷积核 [[1,-2,1],[-2,4,-2],[1,-2,1]]
      c = (a[:-2, :-2] - 2 * a[:-2, 1:-1] + a[:-2, 2:] - 2 * a[1:-1, :-2] + 4 * a[1:-1, 1:-1] - 2 * a[1:-1, 2:]
           + a[2:, :-2] - 2 * a[2:, 1:-1] + a[2:, 2:])
      return np.sqrt(np.pi / 2) * np.abs(c).sum() / (6 * (H - 2) * (W - 2))


  spatial = np.mean([immerkaer(a) for a in fr])
  temporal = np.median(np.std(fr[1:] - fr[:-1], axis=(1, 2))) / np.sqrt(2)
  print(f"frames={len(fr)} spatial_sigma={spatial:.2f} temporal_sigma={temporal:.2f}")
  ```

  </details>

- **做法**：量生成片段静止区域的 σ，代码层是 0。匹配时只给代码层（或合成整体）加颗粒，不去降生成片段的噪声。要压"纹理沸腾"再用时域降噪：【本机实测】σ = 4.0 的合成噪声，`fftdnoiz=sigma=3:amount=0.7` 降到 1.3，`hqdn3d=2:1.5:3:3` 只降到 3.4，`atadenoise` 降到 3.7。真实 AI 纹理沸腾的效果没测。
- **颗粒放在合成之后**，一次加。先放大再加颗粒，颗粒才不会被放大糊掉。
- **分辨率**：经 fal 调 Seedance 2.5 最高 720p，放大到 1080p 用 `scale=1920:1080:flags=lanczos`，再补一点锐化和颗粒；Veo、Kling、Runway 的 Seedance 有 1080p 以上的档位时，优先直接要 1080p 原生。AI 放大器（HyperFrames 的 `media-use` 里提到 `realesrgan-ncnn-vulkan`）可选，本机速度要实测。

### (c) 帧率与节奏

- **事实**：Veo 3.1 是 24 fps [6]；Seedance 2.5 按计费公式推断是 24 fps【推测】，下载后用 `ffprobe` 核对；Kling 3.0 资料写到最高 60 fps【二手】。HyperFrames 的 `--fps` 文档只列 24、30、60。
- **选法**：

  | 情况 | 做法 |
  |---|---|
  | 生成片段是主体，或想要电影感 | **整个项目用 24 fps**，零转换 |
  | 项目必须 30 或 60 fps（平台、其他素材） | 转换生成片段，见下表 |
  | 动作很快、位移很大 | 避免光流插帧，会出伪影 |
  | 想把 24 fps 片段做慢放 | 光流插帧合适（等于生成更多中间帧） |

- **24 → 30 fps 三种转换**，【本机实测】在一段 4 s、24 fps 的合成片上（方块匀速横移，每帧 5 px）：

  | 滤镜 | 帧数 | 结果 |
  |---|---|---|
  | `fps=30` | 120 | 每 5 帧有 1 个重复帧（帧号从 0 起：2、7、12……），运动中出现周期性 judder；`tools/motion.py` 标出其中 21 个，漏掉 27、67、82 三个：按 5 帧的周期它们也是重复帧，但再编码后能量不接近零 |
  | `framerate=fps=30` | 120 | 运动段里没有重复帧（`tools/motion.py` 没有标出）；它做的是帧混合，运动物体会有重影，程度没量 |
  | `minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1` | **118**，比理论少 2 帧 | 没有重复帧；运动物体边缘的伪影没有量。用它之前核对总帧数和时长 |

- **云端选项**：Runway 的 Enhance Frame Rate（2026-09-17 上线，每 2 秒输入 1 积分）可把片段转到 24、25、30、48、50、60、120 fps（含 23.98、29.97、59.94），单段输入最长 300 s [3]；效果没有测，【推测】与光流插帧同类，会有伪影。
- **cadence 检查**：`python3 tools/motion.py clip.mp4` 用 `tblend=difference` 加 `signalstats` 得到逐帧运动能量，在运动段里找"前后都在动，自己却接近零"的帧（能量低于 75 分位的 15%，两侧都高于 50%），就是重复帧。它只给候选帧，看一眼标出的帧再下结论。`mpdecimate` 不适合这个目的：静止段也会被它丢掉。
- 默认是把片段转成项目的帧率，而不是让项目迁就片段；只有生成片段是主体时，才让项目跟着片段走（见上表第一行）。

### (d) 运动模糊

- 代码层默认没有运动模糊；`playbook/08` 已有子帧累积，按 180° 快门（s = 0.5）。生成片段自带模糊，近似电影快门。
- **匹配原则**：同一屏里既有生成内容又有代码运动物体时，代码运动物体用 s = 0.5、N = 4–8；**不要**对生成片段再加模糊，也不要对跟着镜头走的字加（08 已写）。
- 量化（可选）：估一个运动物体的拖影长度除以每帧位移，得到等效快门角；没做过，【推测】这个值通常在 180° 上下，以实测为准。

### (e) 切点

- **生成片段首尾不稳**：首段常在"建立"画面，末尾一秒容易漂移或融化。多生成 1–2 s，两头留 handle。
- **cut on action**：用 `python3 tools/motion.py clip.mp4` 找运动能量的峰。进点放在动作起步之后、出点放在峰值之后 2–4 帧（让动作完成，不在动作前切）【推测的经验值】。峰值位置只是粗定位【本机实测】：合成样例里方块按 smoothstep 加速再减速，速度峰在 2.00 s，顶部很平，平滑后的峰值出现在 1.83 s，早了 4 帧（图像不缩小时是 1.92 s，早 2 帧）。所以再用逐帧 strip 定稿。代码层的冲击点（节拍）落在同一帧。
- **中位数滤波**：编码会在运动能量曲线上造出孤立的尖峰（本机测到过比邻帧高一个数量级的），先用 5 帧中位数再 5 帧均值平滑，`tools/motion.py` 已经这样做。
- **匹配切**（形状或运动方向相同）和 **J/L 切**（用生成片段自带的音频提前或延后）都可以用，节拍优先。
- **速度匹配的转场**：`references/repos/hyperframes/_upstream_claude/skills/cut-the-curve/` 有现成做法。
- **多镜头输出**：先 `scdet` 找内部硬切（见上一节），拆成单镜头片段再用。

### (f) 光向、透视与相机

光向和色温用离散判断：看生成片段里高光和影子的方向，在"左、右、上、前"里选一个，代码层的灯光和投影对齐它。代码场景里有 3D 时，视场角用与生成镜头接近的值，地平线高度与人物脚线对齐。这些写进 NOTES.md，给 reviewer 对照。

## 绿幕角色 + 代码场景（模式 B 反过来用）

写实人物和复杂的舞蹈动作，代码画不好；场景、大字和卡拍，正是代码的长项。这时让视频模型只出人物，其余全部归代码：

1. **模型只出角色，背景是一块纯色**：prompt 里要求纯绿背景，人物全身入镜、不出画。【综合】角色身上有绿色时改用纯蓝；再要求固定机位、影子不落在背景上，后面抠得干净。
2. **抠像加去溢色**：ffmpeg 的 `chromakey` 按颜色把背景变透明，`despill` 去掉绿幕反射到头发和轮廓上的那层绿。键色取抽帧里实测的背景色，不用理论值；先抠一帧放大看边缘，再批量处理。

   ```bash
   # 带 alpha 的 PNG 序列
   ffmpeg -i char_green.mp4 -vf "chromakey=0x19FF0A:0.16:0.08,despill=type=green,format=rgba" char/%05d.png
   # 或 ProRes 4444
   ffmpeg -i char_green.mp4 -vf "chromakey=0x19FF0A:0.16:0.08,despill=type=green,format=yuva444p10le" -c:v prores_ks -profile:v 4444 char.mov
   ```

   `0x19FF0A:0.16:0.08` 依次是键色、相似度、边缘过渡，是 xilo-opus-video 给的示例值，每段素材都要重调。
3. **中间文件必须带 alpha**：H.264 的 mp4 没有透明通道，抠完存成 mp4，背景又变回一块实色。用 PNG 序列或 ProRes 4444。上面两条命令用合成的测试片在本机 ffmpeg 8.0.1 上跑过，两种文件都能用 `overlay` 正确叠回背景上。
4. **代码拥有场景、字和节拍**：背景、大字、贴纸、分屏、3D 环绕字都由代码画，换景和换字卡在配乐的拍上，人物片段本身不改。合成有两种接法【综合】：
   - 在页面里按 `floor(t × 素材帧率)` 取 PNG 序列的那一张画进去。仍然是 t 的纯函数，字可以压在人物前面，也可以绕到身后；
   - 代码层单独渲成视频，再用 ffmpeg `overlay` 叠。字要压在人物前面时，把代码层拆成背景、前景两层分别渲，前景层同样要带 alpha。分屏就是同一段人物错开几帧，叠几次。
5. **验证**：抠像边缘单独出一条放大的 crop strip，头发、手指和快速动作的运动模糊处最容易留绿边或被抠穿。人物和背景的光向、色温对不上时，在代码层补光，不去调素材。下面的三项检查把这一步量化。

来源：xilo 的文章《零基础入门Opus5.5做视频》（X，2026-09-29）拆了 [@Gorden_Sun](https://x.com/Gorden_Sun/status/2104009748874141941) 2026-09-27 的一条帖子：Grok 在纯绿背景前生成 15 秒的舞蹈片段，Opus 5.5 抠像后用网页代码搭出背景、大字、胶带、分屏和 3D 环绕字，背景和大字跟着拍子换。原帖只并排放了成片和绿幕原片，配了一句"Opus 5.5 剪辑后的视频"，抠像和搭场景的细节是 xilo 的拆解，没有得到原作者确认。命令和做法出自 xilo 的 [xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video)（MIT）的 `skills/xilo-opus-video/references/code-stack.md`；带 alpha 的中间文件和两种合成接法是本仓库补的。

### 先判断绿幕路线靠不靠谱，再选抠像方法

要求纯绿背景是一个 prompt 级别的请求，模型不一定听。常见失败：背景不纯或有渐变、绿色溢到头发和衣物、角色本身含绿、影子落在背景上、镜头其实有漂移。第一帧放大看，键色方差大、边缘有明显绿晕，就换抠像方法。

| 方法 | 什么时候用 | 许可证 | 备注 |
|---|---|---|---|
| ffmpeg `chromakey` + `despill`（上面已有） | 背景纯、边缘简单 | ffmpeg | 起步方案 |
| SAM 2（提示点或框，视频分割） | 背景不是纯色、主体边缘清晰 | **Apache-2.0** [15] | 输出是二值遮罩，要做羽化和边缘细化；原理论文 arXiv 2408.00714 |
| Robust Video Matting（RVM） | 人像、要时间稳定的 alpha | **GPL-3.0** [15] | 只能作为外部命令行工具调用，不并入本仓库（MIT）；论文 WACV 2022 [16] |
| MatAnyone | 更稳的通用视频抠像 | S-Lab License 1.0，**商用需联系作者** [15] | 非商业项目才可用 |
| Apple Vision 的前景遮罩 | 本机，不想下载模型 | 系统 API | 【推测】macOS 14+ 的 `VNGenerateForegroundInstanceMaskRequest` 可用，没有实测 |
| HyperFrames 的 `embedded-captions` 里的本地视频抠像 | 已经有现成流程（字幕绕到人物身后用） | 见该 skill | 先读 `references/repos/hyperframes/skills/embedded-captions/`，看它用的模型和许可 |

### 抠完必做的三项检查

| 检查 | 做法 | 阈值 |
|---|---|---|
| 溢色 | 取 alpha 在 0.05–0.95 的边缘带，再向外膨胀 3 px，算 `G − max(R, B)` 的均值 | 大于约 4 个色阶就有可见绿边【推测的阈值】 |
| 边缘光晕 | 把 RGBA 分别合成到黑、白、品牌色上，裁边缘放大看（命令见下）；`overlay` 的 alpha 模式要对：PNG 是 straight；premultiplied 数据要写 `overlay=format=auto:alpha=premultiplied`，漏写最大偏 57 个色阶（暗边），写对后最大偏 1（本机实测）| 目视无暗边亮边 |
| 时间稳定 | 静止区域 alpha 的帧间差均值；前景面积相邻帧的变化率 | 面积突变 > 10% 是抠穿或洞【推测】；alpha 抖动阈值要在第一个真实片段上校准 |

```bash
# 三种底色上的边缘放大（straight alpha 的 PNG）：crop=宽:高:x:y 取边缘，scale 用 neighbor 放大
for bg in black white 0xF5EFE6; do
  ffmpeg -y -f lavfi -i "color=c=$bg:s=1920x1080" -i char/00100.png \
    -filter_complex "[0][1]overlay=format=auto,crop=400:300:700:300,scale=800:-1:flags=neighbor" -frames:v 1 "edge_$bg.png"
done
```

### 放进代码场景之后

- **光包裹**：把背景模糊后，按 alpha 内缘向人物边缘混入 2–6 px，让背景色"渗"到边缘上。
- **接触阴影**：人物脚的位置从遮罩底部取，代码在地面画椭圆软影，随人物移动。
- **颜色协调**：对人物单独做一个弱一点的匹配清单 (a) 的 LUT，而不是改素材。光向、色温对不上时在代码层补光，不动素材。
- **镜头**：固定机位，镜头运动交给代码层的虚拟摄像机。若生成片段仍有漂移，先做背景稳定，或者让代码层背景按同一运动平移。
- **输出格式**：PNG 序列（straight alpha）或 ProRes 4444；HyperFrames 输出侧可以出 WebM、MOV 带 alpha，但**输入侧 `<video>` 是否保留 alpha，文档没写，未验证**，所以接法仍以上面"按 `floor(t × fps)` 取 PNG"为准。

## 角色跨片段一致性

一致性是分层策略，不是一个开关：从"根本不需要一致"到"强行拉回一致"。

| 层 | 做法 | 什么时候选 |
|---|---|---|
| L0 结构规避 | 少镜头；一镜到底不超过模型单次上限；角色只在一个片段里出现；背影、局部、剪影；或者角色由代码画 | 首选。一致性最好的方案是不需要一致 |
| L1 参考锁定 | 每个镜头都传同一组参考（设定图、服装、场景、色板）。Seedance 2.5：30 图、10 视频、10 音频 [2]；Kling：element 和最多 7 张参考图，4.0 计划 7 个主体 [4][5]；Veo 3.1：最多 3 张 [6]；Runway：Act-Two 用表演驱动，图像用 GPT Image 2.5 的 16 张参考 [3] | 多镜头且必须同一角色 |
| L2 首帧链 | 用同一个图像模型先出每个镜头的关键帧（设定图 + 姿态 + 场景），再做图生视频；首尾帧插值（Veo 的首尾帧、Kling 4.0 计划的 10 个关键帧） | 要控制每个镜头的开头和结尾 |
| L3 视频延续 | Veo 延长最多 20 次，但只限 720p [6]；漂移会累积，切点放在动作中途（见"风险"） | 要长镜头且能接受漂移 |
| L4 后处理统一 | 代码层统一调色、颗粒、字幕、配乐、光照；角色用转描（模式 D）让最终画面只保留 JS 那一层 | 最强的一致性，也最费工 |

**角色设定表（character bible）**：外观文字描述（发型、服装、配饰、肤色用 hex）、参考图文件名、比例、常用镜头距离、视线方向、每个镜头 prompt 里的"保持项"段（谁不变）。所有镜头的 prompt 共用这张表。

**验证身份漂移**

| 方法 | 做法 | 许可与限制 |
|---|---|---|
| 客观：嵌入相似度曲线 | 用 SAM 2 或人脸框裁出主体，每 0.5 s 一个点，用 DINOv2 特征对参考图的余弦相似度画曲线，找骤降 | DINOv2 代码与权重 **Apache-2.0** [17]；阈值要按角色校准【推测】；VBench 的 subject consistency 也基于 DINO 特征 [18] |
| 客观：人脸嵌入 | InsightFace 等，对真人脸更准 | **InsightFace 的预训练模型只限非商业研究，商用要联系作者** [17]，商业项目不要默认用它 |
| 离散：VLM | 把参考图和各镜头主体裁图拼成一张 identity sheet，让 VLM 对发型、服装、配饰、脸型、年龄感各选"一致、轻微偏差、明显偏差"，并给出镜头号 | 遵守 `playbook/02` 第 4 层"只给离散选项"；人过关卡 |

失败的降级：缩短镜头数、换成背影或遮挡、改成代码画的角色、拉参考重生成。

## QA：检测伪影

三层，对应 `playbook/02` 的七层检查：

| 层 | 内容 | 成本 | effort |
|---|---|---|---|
| L1 确定性 | `ffprobe`（分辨率、帧率、VFR、色彩标签、音轨）、时长是否等于请求、`cropdetect`、`blackdetect`、`freezedetect`、`scdet`、运动能量曲线里的重复帧 | 秒级 | quick 起 |
| L2 度量 | 颗粒 σ、Lab 统计、静态区域闪烁、身份相似度曲线、OCR 文字对照、抠像三项检查；可选 VBench 的若干维度 | 分钟级 | standard 选做，studio 必做 |
| L3 VLM 与人 | 每个片段的 strip 与 crop，问固定清单，核对它标的那一秒 | 逐片段 | standard 起 |

**伪影分类**

| 伪影 | 症状 | 怎么发现 | 处理 |
|---|---|---|---|
| 身份漂移 | 脸、服装、配饰变化 | L2 相似度曲线；L3 identity sheet | 见"角色跨片段一致性" |
| 变形融化（morphing） | 手指、肢体、物体形变 | L3，strip 每 0.1 s 一格；L2 可选特征匹配内点率【推测】 | 裁切避开或重生成 |
| 纹理沸腾、闪烁 | 高频纹理逐帧抖 | L2 静态区域帧间差 | 时域降噪（`fftdnoiz`）或重生成 |
| 重复帧、节奏不均 | 卡顿 | L1 `tools/motion.py` | 重生成或重定时 |
| 文字乱码 | 画面里的字、logo | L2 OCR 对照期望文字（Apple Vision 或别的 OCR，没有实测） | **不用生成画面里的字**，由代码层画（硬规则 5） |
| 物理违规 | 穿模、漂浮、脚不着地 | L3 | 重生成 |
| 首段不稳、末尾漂移 | 首末 0.5 s | 运动曲线、身份曲线 | 修剪 handle |
| 内部硬切 | 多镜头输出 | L1 `scdet` | 拆分 |
| 水印、黑边 | 免费档水印、letterbox | L1 `cropdetect` + 目视 | 用付费档或裁切；**不要主动去除 SynthID、C2PA 之类的来源标记**（见台账一节） |
| 音频 | 口型对不上、语言不对、爆音 | `bin/vh qa`；转写对稿 | 重生成或重配音 |
| 抠像 | 溢色、边缘、抖动 | "抠完必做的三项检查" | — |

VBench 是一套评测文生视频的基准，CVPR 2024 [18]，有 16 个维度，包括 subject consistency、background consistency、temporal flickering、motion smoothness、dynamic degree、aesthetic quality、imaging quality 等；VBench-2.0 加了物理、常识、人体运动等"内在忠实度"。我们不必引入依赖，除非要批量比较不同模型；每个维度用哪个模型测，见其 README。

## 许可、条款与披露台账

**每个生成片段一条台账**，放 `assets/genclips/<id>/ledger.json`，汇总进 NOTES.md 的素材台账。

```json
{
  "id": "gc-0007",
  "purpose": "scene 3, hero character, 6 s",
  "vendor": "fal", "route": "bytedance/seedance-2.5/reference-to-video", "model_version": "Seedance 2.5",
  "requested_at": "2026-10-01T10:22:00+08:00", "request_id": "…", "seed": 123456,
  "prompt_file": "assets/genclips/gc-0007/prompt.txt", "prompt_sha256": "…",
  "inputs": [ { "file": "assets/char/sheet.png", "origin": "self-generated | user-provided", "rights": "…", "real_person": false } ],
  "output": { "file": "assets/genclips/gc-0007/clip.mp4", "sha256": "…", "duration_s": 6.0, "fps": 24, "size": "1280x720" },
  "attempts": 3, "cost_usd": 8.5,
  "terms": { "url": "…", "retrieved": "2026-10-01", "snapshot_sha256": "…", "tier": "paid API",
             "commercial_use": "per vendor page; verify", "inputs_outputs_used_for_training": "unknown | yes | no",
             "verified_by_human": false },
  "provenance_marks": { "synthid": "n/a", "c2pa": "unknown", "visible_watermark": false },
  "disclosure": { "cn_label_required": true, "platforms": ["douyin", "xiaohongshu", "bilibili"] },
  "restrictions_checked": ["no real faces", "no third-party IP characters", "no minors"]
}
```

**条款要点**（只列读到原文的；标【二手】的要人去官方页核对，所有条款都可能变）

| 通道 | 输出归属与商用 | 输入输出用于训练 | 来源标记 | 其他限制 |
|---|---|---|---|---|
| Runway | 不主张输入和输出的所有权；在遵守协议的前提下不限制商用 | **Runway 取得永久、不可撤销、全球、免版税的许可，可把输入输出用于训练和改进模型**（2026-10-01 对着条款 4.4 节核对） | — | 用 API 做应用要显示 "Powered by Runway" [19] |
| Google Gemini API（Veo、Omni） | Google 不主张输出的所有权 | 付费服务不用你的提示和响应改进产品，免费服务会（2026-10-01 核对）[20] | Veo 输出带 SynthID；视频只保留 2 天 [6] | 必须遵守 Google 的 Generative AI Prohibited Use Policy [20] |
| Kling | 付费档可商用、无水印；免费档有水印【二手】 | 提交内容授予平台永久、全球、可再许可的使用权，含训练【二手】 | 据报道输出带 C2PA【二手】 | 官方条款页是 JS 渲染，没能抓到，**必须人去读** |
| Seedance（经 fal 等） | fal 页面标记为可商用、合作伙伴通道 [2]；条款是 fal 与 ByteDance 各自的，未核对 | 未核对 | — | 2.0 起暂停生成逼真人脸和受 IP 保护的角色 [11]；含真人脸的输入被拦截、fal 上线 2.0 时带内容过滤，只见于搜索摘要【二手】 |
| Sora | 已停服 | — | API 输出只带 C2PA，无可见水印（应用下载带动态水印）【二手】 | — |
| 开放权重（Wan 2.2、LTX-2.x） | 各自许可证：Wan 2.2 是 Apache-2.0；LTX-2 系列许可证要逐版本核对 | 本地运行，不上传 | 无 | — |

**披露**

- **中国**：《人工智能生成合成内容标识办法》（国家网信办、工信部、公安部、广电总局联合发布）自 2025-09-01 起施行：生成合成内容要加显式标识（用户能明显感知）和写入文件元数据的隐式标识，不得恶意删除、篡改、伪造或隐匿标识，传播平台要采取技术措施规范传播；配套强制性国家标准同日实施 [21]。平台侧（按澎湃等媒体 2025-09 的报道）：抖音支持创作者添加 AI 标识，并能读写元数据里的隐式标识，未声明但疑似 AI 生成的内容，平台会自动补标识；B站在发布页的【创作声明】里选【该视频使用人工智能合成技术】，未声明的按规则补标识 [22]。小红书、视频号也有发布页的声明入口，但入口名称各来源说法不一，这里不写死【二手】。**不同平台的入口名称会改，以用户发布时的界面为准。** 做法：BRIEF 里问发布平台；片中含生成片段，交付说明里写明，并提醒用户发布时打开声明开关；NOTES.md 台账里记"需声明"。
- **欧盟**：AI Act 的一般适用日期是 2026-08-02，第 50 条不在第 113 条列出的提前或推迟之列，所以同日适用 [23]。第 50 条要求：生成合成内容的提供方要让输出带机器可读的标记并可被识别；深度伪造的部署方要披露其人工生成或篡改的性质，最晚在受众首次接触时，方式要清楚、可区分；明显属于艺术、创意、讽刺、虚构的作品，义务缩减为以不妨碍作品展示和欣赏的方式披露 [23]。过渡期：对 2026-08-02 之前已经上市的生成系统，提供方要在 2026-12-02 前满足第 50 条第 2 款（第 111 条第 4 款）[23]。罚款上限 1500 万欧元或全球营业额 3%，取高者【二手：律所文章 [24]】。以上条文来自 artificialintelligenceact.eu 对法规文本的转载（已含数字综合法案之后的修订），不是 EUR-Lex 原站，**也不是法律意见**。受众在欧盟的片子，BRIEF 里要问。
- **来源标记**：Veo 用 SynthID，OpenAI 与 Google 在 2026-05 宣布 C2PA 加 SynthID 的双层方案【二手】。C2PA 元数据很脆弱，重新编码和平台转码会丢；SynthID 是隐形水印。**规则：不主动去除任何来源标记**；我们自己 ffmpeg 重新编码后元数据会丢，披露就靠平台声明和交付说明。
- **真人与版权**：不要把真人照片或视频作为生成输入（Seedance 2.0 风波之后 ByteDance 收紧了人脸相关的限制 [11]，也涉及肖像权和深度伪造风险）；需要真人出镜，走类型 09 用户自己录的素材（`video-types/09-editing-talking-head.md`，实验性）。不生成第三方 IP 角色，不含未成年人。参考图、参考视频会上传给供应商，而 Runway 和 Kling 的条款都含训练授权（上表），含真人或保密素材先问用户。

## 成本与重试预算

**公式**：片段成本 = 秒数 × 单价 × 预计重试次数。预算写进 BRIEF，超过 1.5 倍就停下告诉用户。

| 例子 | 计算 | 结果 |
|---|---|---|
| Seedance 2.5（fal），10 s，720p，无视频参考 | 10 × $0.473 | $4.73 |
| 同上，带视频参考 | 10 × $0.284（参考视频的秒数也按公式计入 token，先算一次再开跑） | $2.84 起 |
| Seedance 2.5（Runway），10 s，720p | 10 × 30 积分 | 300 积分（$3.00） |
| 同上，1080p | 10 × 68 积分 | 680 积分（$6.80） |
| Veo 3.1 标准，8 s，1080p | 8 × $0.40 | $3.20 |
| Veo 3.1 Fast，8 s，720p | 8 × $0.10 | $0.80 |
| Veo 3.1 Lite，8 s，720p | 8 × $0.05 | $0.40 |
| Kling 3.0，10 s，1080p 带音频（第三方价） | 10 × $0.168 | $1.68【二手】 |
| Runway Gen-4.5，10 s | 10 × 12 积分 | 120 积分（$1.20） |
| 同上，要 PNG 序列 | 10 × (12 + 5) 积分 | 170 积分（$1.70） |
| 30 s 成片里 12 s 生成片段，Seedance（fal）720p，平均 4 次尝试 | 12 × $0.473 × 4 | 约 $22.7 |

## 风险

- **角色漂移**：同一个角色在不同片段里长得不一样。先想能不能不需要一致，再按"角色跨片段一致性"的分层做，做完用那里的方法验证。
- **片段拼接**：单次上限按模型：Seedance 2.5 和 Wan 3.0 30 s，Veo 3.1 8 s（可延长，见"选模型"），Kling 3.0 15 s，Runway Gen-4.5 10 s。拼接处跨镜头的一致性差，切点尽量放在动作中途或转场处。
- **成本**：donald 给了约 2000 美元的 fal 额度，外加 Max 套餐的全部用量，Claude 跑了 12 小时。做小项目前先估算：秒数 × 单价 × 预计重试次数（公式和算例见"成本与重试预算"）。
- **API key**：一律从环境变量读取（例如 `FAL_KEY`、`ELEVENLABS_API_KEY`），不写进文件。参考图、参考视频会上传给供应商，含真人素材先问用户（见"许可、条款与披露台账"）。

## 数字人和口播

需要说话人头像时，本机没有 NVIDIA GPU，所以本地方案（InfiniteTalk 等）要上云。更实际的做法是 B 模式：用户自己录口播，或者直接用现成的口播素材，agent 负责剪辑、字幕和图解叠加，这就是类型 09（`video-types/09-editing-talking-head.md`，实验性）。Seedance 2.5、Kling 3.0、Veo 3.1 都能带原生音频和口型，但真人素材建议直接走类型 09（用户自己录）；生成数字人的条款限制见台账一节。社区里有一个做法值得参考：把人像缩成右下角的圆形画中画，讲到哪个概念就画出哪个概念，原声、字幕和时长都保持不变。

## 边界：档案素材纪录片

用真实的历史影像剪纪录片（老新闻片、档案照片、修复或上色过的旧片），是本仓库不走的路线：画面不是代码画的，版权和史实的风险也都更高。确实要做时守住几条：素材只用 CC 许可、公有领域或已获授权的，每一段都记进 `NOTES.md` 的素材台账（来源、许可、原片时间码）；超分、上色这类处理只做一次，结果缓存成文件，再当作一条素材轨，由 t 的纯函数按时间取帧合成，渲染时不重跑模型；修复或上色过的镜头要在画面上标明，这属于硬规则 5 的事实纪律；从视频平台下载素材要遵守平台条款。需要这条路线的完整工具链，看 OpenMontage 的 `documentary-montage` 管线：它从 CLIP 索引的免费素材和开放档案里剪主题蒙太奇，见 `references/community-skills.md` 第 3 节（AGPL，只读）。

## 待验证

要在第一个真实项目里验证的：
1. 各供应商输出的实际帧率、色彩标签、VFR 情况（没有 key，没调用）。
2. 匹配清单和抠像检查里的各个阈值（色彩 ΔE、溢色、alpha 抖动、身份相似度）。
3. Runway 的 ProRes 与 PNG 序列输出，抠像质量是否真的比 H.264 好；账号是否已开通这些格式。
4. HyperFrames 的 `<video>` 是否保留输入视频的 alpha。
5. `fftdnoiz` 对真实 AI 纹理沸腾的效果。
6. Kling 官方条款原文（页面 JS 渲染，本次没抓到）；Seedance 经各渠道的条款；C2PA 是否随各供应商输出。

维护者待定：
1. 是否把 RVM（GPL-3.0）作为可选外部工具写进文档（现在只写了"只能当外部命令行工具调用，不并入本仓库"）；InsightFace、MatAnyone 的许可证不允许默认商用，文档已标明，是否要在 `references/` 里单独列出。
2. 台账 schema 是否直接并进 `templates/NOTES.md`（现在只写在本章）。
3. 是否采用"项目 fps 跟着生成片段走（24 fps）"作为默认建议（现在只是"生成片段是主体时"的条件建议）。

## 来源

- [1] fal，Seedance 2.5 对比 2.0：https://fal.ai/learn/devs/seedance-2-5-vs-seedance-2-0 （2026-08-13；2026-10-01 核对：4–30 s、480p/720p、50 个参考 = 30 图 + 10 视频 + 10 音频、$0.0214 每千 token、无 fast 档、fal 上无 1080p/4K）。美国托管端点价格来自搜索摘要【二手】：https://fal.ai/models/bytedance/seedance-2.5/us/reference-to-video 。
- [2] fal，Seedance 2.5 reference-to-video：https://fal.ai/models/bytedance/seedance-2.5/reference-to-video （2026-10-01 核对：参数、计费公式、720p ≈ $0.4730/s 与 $0.2838/s、480p ≈ $0.2205/s 与 $0.1323/s、`generate_audio`、`seed`、Commercial use 标记）。
- [3] Runway：API 更新日志 https://docs.dev.runwayml.com/api-details/api_changelog/ ，模型总览 https://docs.dev.runwayml.com/guides/models/ ，价目表 https://docs.dev.runwayml.com/guides/pricing/ （均于 2026-10-01 核对：Gen-4.5 2026-02-10，Aleph 2.0 2026-06-02；Seedance 2.5 于 2026-08-07 上线、2026-08-15 加 1080p；Gen-4.5 的 HDR 与专业输出格式 2026-08-20、ACEScg EXR 2026-08-31；Wan 3.0 2026-08-26；Enhance Frame Rate 2026-09-17；Model Router 2026-07-23；每种模型和输出格式的积分价，1 积分 = $0.01）。
- [4] Kling 3.0 资料（第三方）：https://www.atlascloud.ai/blog/tips/kling-ai ；Turbo 与 Omni：https://www.atlascloud.ai/blog/guides/kling-3.0-turbo-kling-omni ；价格统计 https://costgoat.com/pricing/kling ；官方文档站 https://kling.ai/document-api/ （JS 渲染，没能抓到）。均为【二手】。
- [5] Kling 4.0：TechTimes 2026-09-30 https://www.techtimes.com/articles/328285/20260930/kling-40-promises-30-second-4k-video-broadcast-spec-coming-october-not-today.htm 【二手】（2026-10-01 重读：2026-09-28 宣布，十月上线，当时尚未提供）；Bloomberg 2026-09-28 的报道页 403，未读到。
- [6] Gemini API Veo 3.1：https://ai.google.dev/gemini-api/docs/veo （2026-10-01 核对：模型 ID、时长、分辨率、24 fps、参考图、首尾帧、延长、SynthID、保留 2 天、`personGeneration`）。
- [7] Gemini API 价格：https://ai.google.dev/gemini-api/docs/pricing （2026-10-01 核对）。
- [8] Gemini API 更新日志：https://ai.google.dev/gemini-api/docs/changelog （2026-10-01 核对：Veo 3.1 Lite 2026-03-31；Veo 2.0 与 3.0 于 2026-06-30 下线；`gemini-omni-1.1-flash` 2026-08-27）。
- [9] Sora 停服：OpenAI API 弃用页 https://developers.openai.com/api/docs/deprecations （2026-10-01 核对：2026-03-24 通知，Videos API 与 `sora-2`、`sora-2-pro` 及各快照于 2026-09-24 移除，未指定替代）；应用和网页 2026-04-26 关闭见 OpenAI 社区帖转述 https://community.openai.com/t/is-the-sora2-api-still-working/1379946 、The Decoder https://the-decoder.com/openai-sets-two-stage-sora-shutdown-with-app-closing-april-2026-and-api-following-in-september/ 与 Wikipedia https://en.wikipedia.org/wiki/Sora_(text-to-video_model) ；OpenAI 帮助中心页 403。
- [10] Runway 模型与输出格式见 [3]；Runway 新闻 https://techcrunch.com/2026/07/23/runway-bets-on-ai-model-routing-as-generative-media-gets-crowded/ 【二手】。
- [11] Seedance 2.0 风波：财新 https://www.caixinglobal.com/2026-03-17/bytedance-halts-global-rollout-of-seedance-20-amid-copyright-dispute-102423674.html （2026-02-15 宣布暂停生成逼真人脸和 IP 角色；到 2026-03-16 暂停全球推广）；CNBC https://www.cnbc.com/2026/02/16/bytedance-safegaurds-seedance-ai-copyright-disney-mpa-netflix-paramount-sony-universal.html 与 TNW https://thenextweb.com/news/bytedance-seedance-watermarking-ip-global-rollout 均 403；输入侧限制与 fal 上线时间见搜索摘要【二手】。
- [12] Wan 3.0：TechNode https://technode.com/2026/08/24/alibaba-launches-wan3-0-video-model-with-30-second-generation-and-document-input/ 【二手】；经 Runway 的规格见 [3]。
- [13] Reinhard E., Adhikhmin M., Gooch B., Shirley P., "Color transfer between images", IEEE Computer Graphics and Applications 21(5), 2001，DOI 10.1109/38.946629（Crossref 核对）。
- [14] Immerkær J., "Fast noise variance estimation", Computer Vision and Image Understanding 64(2), 1996，DOI 10.1006/cviu.1996.0060（Crossref 核对）。
- [15] 许可证（GitHub API 与仓库文件核对）：SAM 2 https://github.com/facebookresearch/sam2 （Apache-2.0）；RVM https://github.com/PeterL1n/RobustVideoMatting （GPL-3.0）；MatAnyone https://github.com/pq-yang/MatAnyone （S-Lab License 1.0，商用要联系作者）。
- [16] Lin S. 等，"Robust High-Resolution Video Matting with Temporal Guidance", WACV 2022，DOI 10.1109/wacv51458.2022.00319（Crossref 核对）。
- [17] DINOv2 https://github.com/facebookresearch/dinov2 （代码与权重 Apache-2.0）；InsightFace https://github.com/deepinsight/insightface （代码 MIT；带标注的训练数据和据此训练的模型仅限非商业研究；`buffalo_l` 商用联系作者）。
- [18] VBench：Huang 等，CVPR 2024，DOI 10.1109/cvpr52733.2024.02060，arXiv 2311.17982；VBench++，TPAMI，DOI 10.1109/tpami.2025.3633890；维度列表见 https://github.com/Vchitect/VBench 。
- [19] Runway 使用条款 https://runway.com/terms-of-use （2026-10-01 核对 4.4 节与第 1 节）。
- [20] Gemini API 附加条款 https://ai.google.dev/gemini-api/terms （2026-10-01 核对）。
- [21] 《人工智能生成合成内容标识办法》：新华网 https://www.news.cn/politics/20250314/b7a24028f2924b7681e6ed1bfbd8fade/c.html （发布机构、2025-09-01 施行、显式与隐式标识定义、禁止恶意删除或篡改标识）；央视网 https://news.cctv.com/2025/09/01/ARTI3ZlXK7MyM39Pm3PuZ5Hm250901.shtml 。
- [22] 平台做法：澎湃 https://www.thepaper.cn/newsDetail_forward_31523045 （抖音、B站、快手、腾讯）；新华网 http://www.news.cn/tech/20250909/fb164c6d092146aa8e13ddc283fe416a/c.html （微信、抖音、DeepSeek）；小红书与视频号的入口名称只见于第三方博客 https://www.byerisk.com/blog/aigc-content-labeling-2026-9-faq ，说法与上面不一致【二手】。
- [23] 欧盟 AI Act 条文（转载站）：第 50 条 https://artificialintelligenceact.eu/article/50/ ，第 113 条 https://artificialintelligenceact.eu/article/113/ ，第 111 条 https://artificialintelligenceact.eu/article/111/ 。
- [24] 律所文章（罚款、创意作品放宽、行为守则进展）：Jones Day https://www.jonesday.com/en/insights/2026/01/european-commission-publishes-draft-code-of-practice-on-ai-labelling-and-transparency ；TrueScreen https://truescreen.io/insights/ai-act-article-50-labelling-synthetic-content-august-2026/ 【二手】。
