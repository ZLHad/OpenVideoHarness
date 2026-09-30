# 生成式视频：模型、价格和出处（2026-10-01）

这一页是**会过期的数字**：模型版本、规格、价格、各通道的差别。方法（怎么入库、对齐画面、抠像、QA）在 `playbook/05-hybrid-genvideo.md`，许可和披露台账在 `references/genvideo-ledger.md`。

- **核对过**（2026-10-01，对着官方页面）：Sora、Seedance 2.5（fal 和 Runway）、Veo 3.1 和 Gemini Omni、Runway 的规格和价格。Kling 只有第三方资料，标【二手】。
- **每个项目开工时重查三样**：版本、价格、条款，把查询日期和网址写进 `NOTES.md`。半年后这页就该重写。
- 标记：【二手】只读到第三方转述或搜索摘要；【推测】没有证据的推断。引用编号 `[n]` 见文末。

## 规格

| 模型 | 时长 | 分辨率与帧率 | 参考与一致性 | 音频 | 备注 |
|---|---|---|---|---|---|
| **Seedance 2.5**（ByteDance；fal、Runway） | 4–30 s | fal：480p、720p，没有 fast 档。Runway：480p、720p，**2026-08-15 起另有 1080p** [3]。帧率页面没写，计费公式里的 ×24 暗示 24 fps【推测】 | 最多 50 个参考：30 图、10 视频、10 音频；有 `seed` 参数 [1][2] | 原生，`generate_audio` 默认开 [2]；对白写在双引号里触发口型 [1] | 2.0（2026-02）是 4–15 s、480p–4K、12 个参考。2.0 遇到好莱坞的侵权投诉后，ByteDance 在 2026-02-15 宣布暂停生成逼真的人脸和受 IP 保护的角色，3 月中旬暂停全球推广 [11]；另有报道称含真人脸的图像和视频输入也被拦截【二手】 |
| **Kling 3.0 / 3.0 Turbo / 3.0 Omni**（Kuaishou） | 单镜头 3–15 s；多镜头 2–6 镜 | 720p、1080p、4K 三档【二手】[4] | Omni：最多 7 张参考图、持久 element、首尾帧、参考视频【二手】[4] | 原生，多语言口型 | 3.0 于 2026-02 发布；Turbo 与 Omni 升级 2026-06-17 发布【二手】。**Kling 4.0 在 2026-09-28 宣布，截至 2026-10-01 尚未上线**：Flash 小范围内测（3–20 s，720p，8 位），完整版十月上线，计划 ≤ 30 s、4K、10 个关键帧、最多 15 个输入（报道写图像最多 10、视频最多 5、已保存主体最多 7，三项相加超过 15，原文如此）、10 位 HDR"即将推出"，价格未公布【二手】[5] |
| **Veo 3.1 / Fast / Lite**（Google；Gemini API、Vertex） | 4、6、8 s；1080p、4K、参考图、延长时必须 8 s | 720p 默认、1080p、4K（Lite 没有 4K）；**24 fps**；16:9 或 9:16 | 最多 3 张参考图；首尾帧；延长最多 20 次、每次 7 s，只限 720p，总长最多 148 s [6] | 原生，始终开启 | 输出带 SynthID；服务器只保留 2 天，要及时下载；欧盟、英国、瑞士、中东北非的 `personGeneration` 只允许 `allow_adult` [6]。模型 ID 仍带 `preview`（`veo-3.1-generate-preview` 等）。Veo 2.0 与 3.0 已在 2026-06-30 下线 [8] |
| **Gemini Omni Flash 1.1**（Google） | — | `gemini-omni-1.1-flash`，2026-08-27 正式发布；360p–4K 分辨率可选 [8] | 对话式视频编辑：视频延长、图像间插值 [8] | — | Google 在 I/O 2026 没有推 Veo 4，而是推了 Omni 这条新线【二手】 |
| **Sora**（OpenAI） | **已停** | — | — | — | **API 于 2026-09-24 移除**：2026-03-24 通知，涵盖 Videos API、`sora-2`、`sora-2-pro` 及各快照，官方没有给替代 [9]。应用和网页 2026-04-26 关闭【二手】[9]。手上若有 Sora 时期的素材，保留当时的台账、水印和 C2PA 元数据，重新编码会丢掉来源信息 |
| **Runway Gen-4.5**、**Aleph 2.0**、**Act-Two** | Gen-4.5：2–10 s，文生、图生视频，2026-02-10 发布。Aleph 2.0（2026-06-02）：视频编辑，输入 2–30 s 加最多 5 个关键帧图。Act-Two：用表演视频驱动角色 | 输出格式见下 | 图像侧有 GPT Image 2.5（最多 16 张参考图）[3] | — | 同一个 API 里还能调 Seedance 2.5、Veo 3.1、Gemini Omni Flash、Wan 3.0、Grok Imagine Video 1.5、MiniMax H3 等，并有按成本或延迟路由的 Model Router（2026-07-23）[3][10] |

**Runway 的输出格式**（Gen-4.5、Aleph 2.0；`outputFormat`）[3]：
- SDR：`prores`、`png_sequence`，每秒加 5 积分；
- 10 位和 HDR 系：`sdr_rec709_10bit`、`hdr10`、`hlg`、`hdr_pq_12bit_master`、`hdr_prores`、`hdr_png_sequence`、`hdr_exr_sequence`、`hdr_exr_acescg_sequence_1_3`、`hdr_exr_acescg_sequence_2_0`，每秒加 20 积分（输出超过 4 MP 时加 40）。HDR 系是按 BT.2020 或 ACES 出的真 HDR，EXR 是线性 BT.2020 光或 ACEScg；我们交付的是 BT.709 SDR，用它们要多一步色域和色调转换。维护者的 Mac 上的 ffmpeg（8.0.1）没有 zscale、libplacebo、OCIO，只有 `colorspace` 和 `tonemap` 两个滤镜，做不了精细的转换，没有试过；
- 这些格式自 2026-08-20 起**按账号逐步开放**，没有开通时只能拿 mp4。

**其他**：
- **Wan 3.0**（Alibaba）：闭源；经 Runway 调用时单次最长 30 s，带原生音频，480p、720p、1080p [3]；开放权重的 Wan 线停在 2.2（Apache-2.0）【二手】[12]。
- **LTX-2.x**：开放权重，社区有 MLX 移植可在 Apple Silicon 上跑【二手】。`references/open-source.md` 已列 Wan2.2 和 LTX-2，许可证要逐个核对。
- 没有出现的版本：Seedance 3、Veo 4、Runway Gen-5，截至今天都没有官方发布（搜索结果均无官方页面【二手】）。

## 价格

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

## 按需求选

| 需求 | 倾向 | 理由与代价 |
|---|---|---|
| 长镜头（≥ 15 s）、多参考、要在一次生成里锁角色、场景、色板 | Seedance 2.5 | 30 s、50 个参考。经 fal 上限 720p：交付 1080p 要放大，放大后和代码层的清晰度对不上，要补颗粒；Runway 有 1080p 档，每秒 68 积分，不用放大 |
| 原生 1080p 或 4K 的画质，要调色余量 | Veo 3.1（8 s，24 fps）；Kling 3.0（4K 档）；Runway Gen-4.5 | Veo 标准档 $0.40/s，价格最高，有 Fast 与 Lite 两档便宜的 |
| **抠像或合成密集的镜头** | Runway Gen-4.5，要 `prores` 或 `png_sequence` | 省掉一次 H.264 压缩，抠像边缘更干净【推测：没有对比过抠像质量】；只有 2–10 s，每秒加 5 积分；格式要账号已开通。HDR 系（含 EXR）见上，先用 SDR 的两种 |
| 预算敏感，草稿和探索 | Veo 3.1 Lite（$0.05–0.08/s）、Seedance 480p、Kling Turbo、Wan 3.0 的 480p | 先用便宜档试 prompt 和构图，再上贵档 |
| 需要真人的表演或口型（例如借演员的动作） | Runway Act-Two；或让用户自己录 | 生成真人脸有肖像权和平台限制（见 `references/genvideo-ledger.md`） |
| 要在已有素材上改光、改风格（视频到视频） | Runway Aleph 2.0；Gemini Omni Flash；Kling Omni 编辑 | 不确定性高。先用确定性的调色，不够再用它们 |
| 素材保密，或要完全本地 | LTX-2.x（MLX）、Wan 2.2 | 维护者的 Mac 没有 NVIDIA GPU，速度和画质都要实测；先看许可证 |

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
