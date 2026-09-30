# 生成片段：许可、条款与披露台账（2026-10-01）

这一页记每个生成片段的来历，以及发布前要做的披露。条款会变，每个项目开工时重查；**不是法律意见**。方法在 `playbook/05-hybrid-genvideo.md`，模型和价格在 `references/genvideo-market.md`（下文 `[Mn]` 指那一页的来源 n，`[n]` 指本页文末的来源）。标记：【二手】没能读到原文；【推测】没有证据的推断。

## 台账

每个生成片段一条，放 `assets/genclips/<id>/ledger.json`，汇总进 `NOTES.md` 的素材台账。下面的字段是起点，还没有在真实项目里用过；用过一轮之后再定稿，现在先不并进 `templates/NOTES.md`。

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

## 各通道的条款要点

Runway 和 Google 的条款 2026-10-01 对着原文读过；标【二手】的要人去官方页核对。

| 通道 | 输出归属与商用 | 输入输出用于训练 | 来源标记 | 其他限制 |
|---|---|---|---|---|
| Runway | 不主张输入和输出的所有权；在遵守协议的前提下不限制商用（条款 4.4 节）| **Runway 取得永久、不可撤销、全球、免版税的许可，可把输入输出用于训练和改进模型**（4.4 节）| — | 用 API 做应用要显示 "Powered by Runway"（第 1 节）[5] |
| Google Gemini API（Veo、Omni） | Google 不主张输出的所有权 | 付费服务不用你的提示和响应改进产品，免费服务会 [6] | Veo 输出带 SynthID；视频只保留 2 天 [M6] | 必须遵守 Google 的 Generative AI Prohibited Use Policy [6] |
| Kling | 付费档可商用、无水印；免费档有水印【二手】 | 提交内容授予平台永久、全球、可再许可的使用权，含训练【二手】 | 据报道输出带 C2PA【二手】 | 官方条款页是 JS 渲染，没能抓到，**必须人去读** |
| Seedance（经 fal 等） | fal 页面标记为可商用、合作伙伴通道 [M2]；条款是 fal 与 ByteDance 各自的，未核对 | 未核对 | — | 2.0 起暂停生成逼真人脸和受 IP 保护的角色 [M11]；含真人脸的输入被拦截、fal 上线 2.0 时带内容过滤，只见于搜索摘要【二手】 |
| Sora | 已停服 | — | API 输出只带 C2PA，无可见水印（应用下载带动态水印）【二手】 | — |
| 开放权重（Wan 2.2、LTX-2.x） | 各自许可证：Wan 2.2 是 Apache-2.0；LTX-2 系列许可证要逐版本核对 | 本地运行，不上传 | 无 | — |

## 披露

### 中国

- **规则**：《人工智能生成合成内容标识办法》（国家网信办、工信部、公安部、广电总局联合发布）自 2025-09-01 起施行。生成合成内容要加显式标识（用户能明显感知）和写入文件元数据的隐式标识；不得恶意删除、篡改、伪造或隐匿标识；传播平台要采取技术措施规范传播。配套的强制性国家标准同日实施 [1]。
- **平台**（按澎湃等媒体 2025-09 的报道）：抖音支持创作者添加 AI 标识，并能读写元数据里的隐式标识，未声明但疑似 AI 生成的内容，平台会自动补标识；B站在发布页的【创作声明】里选【该视频使用人工智能合成技术】，未声明的按规则补标识 [2]。小红书、视频号也有发布页的声明入口，但入口名称各来源说法不一，这里不写死【二手】。入口名称会改，以用户发布时的界面为准。
- **怎么做**：BRIEF 里问发布平台；片中含生成片段，就在交付说明里写明，并提醒用户发布时打开声明开关；`NOTES.md` 的台账里记"需声明"。

### 欧盟

- **规则**：AI Act 的一般适用日期是 2026-08-02，第 50 条不在第 113 条列出的提前或推迟之列，所以同日适用 [3]。第 50 条要求：生成合成内容的提供方要让输出带机器可读的标记并可被识别；深度伪造的部署方要披露其人工生成或篡改的性质，最晚在受众首次接触时，方式要清楚、可区分；明显属于艺术、创意、讽刺、虚构的作品，义务缩减为以不妨碍作品展示和欣赏的方式披露 [3]。
- **过渡期和罚则**：对 2026-08-02 之前已经上市的生成系统，提供方要在 2026-12-02 前满足第 50 条第 2 款（第 111 条第 4 款）[3]。罚款上限 1500 万欧元或全球营业额 3%，取高者【二手：律所文章 [4]】。
- **出处的限制**：条文来自 artificialintelligenceact.eu 对法规文本的转载（已含数字综合法案之后的修订），不是 EUR-Lex 原站，也不是法律意见。
- **怎么做**：受众在欧盟的片子，BRIEF 里问；交付说明里写明含 AI 生成内容。

### 来源标记与真人

- **来源标记**：Veo 用 SynthID，OpenAI 与 Google 在 2026-05 宣布 C2PA 加 SynthID 的双层方案【二手】。C2PA 元数据很脆弱，重新编码和平台转码会丢；SynthID 是隐形水印。**不主动去除任何来源标记**；我们自己用 ffmpeg 重新编码后元数据会丢，披露就靠平台声明和交付说明。
- **真人与版权**：默认不把真人照片或视频当生成输入（Seedance 2.0 风波之后 ByteDance 收紧了人脸相关的限制 [M11]，也涉及肖像权和深度伪造风险）。例外：用户自己的脸、用户明确同意、供应商条款允许，三样都满足才做，并记进台账。需要真人出镜，更稳的办法是让用户自己录，再剪辑他的素材。不生成第三方 IP 角色，不含未成年人。
- **上传**：参考图、参考视频会上传给供应商，Runway 和 Kling 的条款都含训练授权（见上表），含真人或保密素材先问用户。

## 来源

- [1] 《人工智能生成合成内容标识办法》：新华网 https://www.news.cn/politics/20250314/b7a24028f2924b7681e6ed1bfbd8fade/c.html （发布机构、2025-09-01 施行、显式与隐式标识定义、禁止恶意删除或篡改标识）；央视网 https://news.cctv.com/2025/09/01/ARTI3ZlXK7MyM39Pm3PuZ5Hm250901.shtml 。
- [2] 平台做法：澎湃 https://www.thepaper.cn/newsDetail_forward_31523045 （抖音、B站、快手、腾讯）；新华网 http://www.news.cn/tech/20250909/fb164c6d092146aa8e13ddc283fe416a/c.html （微信、抖音、DeepSeek）；小红书与视频号的入口名称只见于第三方博客 https://www.byerisk.com/blog/aigc-content-labeling-2026-9-faq ，说法与上面不一致【二手】。
- [3] 欧盟 AI Act 条文（转载站）：第 50 条 https://artificialintelligenceact.eu/article/50/ ，第 113 条 https://artificialintelligenceact.eu/article/113/ ，第 111 条 https://artificialintelligenceact.eu/article/111/ 。
- [4] 律所文章（罚款、创意作品放宽、行为守则进展）：Jones Day https://www.jonesday.com/en/insights/2026/01/european-commission-publishes-draft-code-of-practice-on-ai-labelling-and-transparency ；TrueScreen https://truescreen.io/insights/ai-act-article-50-labelling-synthetic-content-august-2026/ 【二手】。
- [5] Runway 使用条款 https://runway.com/terms-of-use （2026-10-01 核对 4.4 节与第 1 节）。
- [6] Gemini API 附加条款 https://ai.google.dev/gemini-api/terms （2026-10-01 核对）。
