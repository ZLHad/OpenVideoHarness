# OpenVideoHarness 介绍片 v3：一镜到底 · 产品宣传片

成片 `media/final.mp4`（网页版 20.8 MB，带立体声和中英软字幕轨）· 1920×1080 · 30 fps · **81.333 s（2440 帧）** · fx 预设 B · −14.0 LUFS

- 预览 `media/preview.gif`（21.0–30.6 s：braam → 片名 → 架构 → 8 类列表）
- 封面 `media/poster.png`
- 联系表 `media/sheet.png`
- 英文说明 [README.md](README.md)，复现步骤也在那里

下文提到的 `out/…` 是制作时的本地产物，不在仓库里。

v2（69.3 s）完整保存在 `out/v2/`。v3 的起因是用户的两条意见（原话）：
- "这个介绍片音乐部分感觉部分地方卡顿或者消失。修改 然后我觉得不够炫酷"
- "毕竟介绍片是本产品的宣传片 所以关于本产品的一些架构、特色、案例、工作流流程图之类的可以做成炫酷动效放入"

## 片子讲什么（一个镜头，十一段）

| t (s) | 段落 | 画面 |
|---|---|---|
| 0–8.0 | hook | 光点拉成 t 轴，帧墙渲染出来：`frame = f(t)` · EVERY FRAME · IS A FUNCTION OF TIME |
| 8.0–16.0 | 程序 | showcase 02 的真实请求卡；穿过由真实 `draw(t)` 代码组成的峡谷："Claude Opus 5.5 doesn't paint pixels. It writes the program."；帧聚拢成一支片子 |
| 16.0–21.3 | 问题 | Stunning, once. / Dependable? Not yet.；三张错帧被盖章 FAIL |
| 21.3–24.0 | 片名 | braam，9 圈光环点亮，打出片名 |
| 24.0–36.0 | **架构网络** | 按 `docs/assets/architecture.*.svg` 搭成的 3D 节点网，四个站点：请求 → agent → 路由；video-types/ 分出 8 条支线（第 11 小节为 6/4，列表多停 2 拍）；playbook / templates / cases / bin/vh 四张卡；engines、references，最后俯冲穿过 `projects/` 六边形 |
| 36.0–49.3 | **工作流** | README 的 How it works 流程图变成通电的 3D 网络：①② 人工审阅 approved；自查循环三次 fail；俯瞰全图时出现规则句；pass；③ 通过；终点节点 Final cut + LESSONS.md 停 2 拍 |
| 49.3–57.3 | **特色** | 三块全息面板，每小节一块：Taste written down as numbers（缓动曲线、810px 安全框、20 格清单）/ Sound, end to end（波形就是本片配乐）/ Ready to run（终端里打出安装命令） |
| 57.3–60.0 | **案例星图** | 389 个点汇聚成盘，11 颗亮星连成星座：11 case studies + curated picks from 389 community videos |
| 60.0–70.7 | 放映厅 | 4 块屏幕放真实成片，每 3 拍一块：01 手绘 / 03 数学 / 02 竖屏 / 00 发布片 |
| 70.7–76.0 | 揭晓 | 本片自己的联系表立成一面墙："This film, too." → "Even the soundtrack is code."，4 行配乐代码逐拍点亮，对应乐器同时进入 |
| 76.0–81.3 | 片名 | OpenVideoHarness · tagline；命令和 GitHub 地址在配乐的打字 16 分音符上打出来 |

事实来源逐条列在 `NOTES.md` 的"v3 Phase B"一节。架构 svg 写的是 playbook 8 篇，片里用实际的 9 篇（00–08），svg 由协调方修正。

## 怎么做的

- **画面**：HyperFrames 0.8.82 + Three.js 0.181.2。three 现在从项目本地 `node_modules` 加载，不依赖 CDN。代码分为：
  - `js/main.js`：S1–S4、放映厅、揭晓、片名、镜头、后期；
  - `js/arch.js`：架构网络；
  - `js/pipeline.js`：工作流；
  - `js/features.js`：特色面板和星图；
  - `js/fx.js`：FX 预设、调速、脉冲、shader、解码字。
  
  每一帧都是 `renderAt(t)` 的纯函数。
- **声音**：
  - 配乐由作曲 subagent 用代码写成：`audio/score.json` + `audio/score_engine.py`，版本 v3.4，30 小节，第 11 小节 6/4；
  - 音效用 `bin/vh sfx`，97 个事件；
  - 立体声混音后做线性母带。
- **网格**：90 BPM × 30 fps，1 拍 = 20 帧。画面、配乐、音效、字幕共用同一个 `bar(k, beat)`，从第 12 小节起统一加上 6/4 多出的 2 拍。

## 数字

| 文件 | 规格 | 大小 |
|---|---|---|
| `final.mp4` | H.264 CRF 16 + AAC 256k 立体声 + zh/en 软字幕（各 23 条），2440 帧 | 266.1 MB |
| `final-web.mp4` | 两遍 1900 kbps（maxrate 3000k）+ AAC 128k + 软字幕 | 20.8 MB |
| `final-nograin.mp4` | HyperFrames `--quality high` 母版，不带音频 | 308.4 MB |
| `preview.gif` | 21.0–30.6 s，640 px，10 fps，64 色 | 7.9 MB |
| `poster.png` | t = 80.9 s（片名 + 命令 + 地址） | 1.8 MB |
| `sheet.png` | `bin/vh sheet`，每 1.33 s 一格 | 9.7 MB |

**渲染**：M3 Max，4 个 worker。draft 约 53 s，high 母版 2 min 0 s。

**检查**（详见 `NOTES.md`）：

| 项目 | 结果 |
|---|---|
| 成片响度 | −14.0 LUFS，LRA 8.2 LU，true peak −1.7 dBTP |
| cue check（成片混音） | 180 个 cue 全部在 1 帧以内（中位 10.6 ms，最大 17.3 ms） |
| 配乐自己的 hit | 143 个全部在 1 帧以内 |
| 掉音 / 数字静音 / 抽吸 | 0 / 只在 0–0.09 s 和最后 0.07 s / 0 |
| 爆音警告（`bin/vh qa`） | 136 处，逐个溯源：都是设计好的起音（锯齿波 ostinato 的音头，以及一个本来就是硬门控的 glitch 音效）。制作时报告的"0 处"来自一个根本不可能报警的旧判据，已在 harness 里修正 |
| blackdetect / freezedetect / silencedetect | 无 |
| 空帧、停帧、单帧闪 | 每帧与第 0 帧比 PSNR，最高 32 dB（braam 前的暗场），没有停帧；没有单帧亮度突变 |
| three 本地化 | 本地版和 CDN 版在 4 个时间点的无损 PNG 逐比特相同 |
| 确定性 | 4 个 worker 对 3 个 worker 的无损 PNG 序列：2040/2440 帧逐比特相同，其余最低 80.7 dB（`out/check/det-final.txt`） |

## 已知的不完美

1. **架构段的二级标签只停很短**：大标题和关键数字（8 workflows、9 know-how docs、7 templates、20+ repos）都读得到，小字当纹理。
2. **放映厅约 10.7 s**，一位评审觉得偏长。保留它，是因为每块屏上都是真实成片。
3. **`final.mp4` 较大（266 MB）**：粒子和星点多，CRF 16 压不小。发 README 或 X 用 `final-web.mp4`。
4. **配乐没有人耳听过**：判断都来自响度曲线、onset 和频谱。
5. **关卡 ②③ 没有经过人工审阅**：用自查加两轮独立评审代替。REVIEW.md 里协调方已注明。
