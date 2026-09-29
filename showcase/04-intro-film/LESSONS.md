# LESSONS：intro film（一镜到底 · HyperFrames + Three.js · 代码作曲）

## 踩过的坑（按代价排序）

1. **VideoTexture 在 HyperFrames 里要每帧手动上传。** HyperFrames 会 seek 源 `<video>`，但 Three.js 的 `VideoTexture` 靠 `requestVideoFrameCallback` 更新，只 seek 不播放时它不会触发，结果屏幕全黑。做法是在 `hf-seek` 的渲染函数里，对每个 `readyState >= 2` 的纹理设 `tx.needsUpdate = true`。spike 里有这一行，正片漏了，draft1 的放映厅整段是黑的。
2. **worker 的第一帧可能在异步 build 完成前就被截图。** 模块脚本是延后执行的，在里面注册 `window.__hf.buildReady[...]` 太晚，每个 worker chunk 开头会出现 1–2 帧空画面（YAVG 24，前后是 62）。做法：在一段**经典内联脚本**里同步注册一个 promise，由模块在 build 完成、第一帧画完之后 resolve。检查方法：每帧 `signalstats` 的 YAVG，找突降。
3. **项目根目录只能有一个带 `data-composition-id` 的 HTML。** 测试用的 composition（`test-proof.html`）放在根目录会触发 lint 的 `multiple_root_compositions`；平时放在 `out/`，要跑时再临时拷回来。
4. **共享的 `bin/vh mix` 用单遍动态 loudnorm，会压扁电影配乐的动态**（LRA 13.6 → 7.0），积分响度也会偏（−12.7 LUFS）。做法：`lufs=off` 出原始混音，再做两遍线性增益加 true-peak 限幅（`tools/master.sh`），结果 −14.1 LUFS、LRA 12.8、TP −1.9。
5. **`bin/vh mix` 会下混成单声道**（`aformat=channel_layouts=mono`）。立体声配乐要用项目内拷贝的 `tools/mix_stereo.py`。
6. **zsh 下 `for s in "a b c"; do set -- $s` 不会拆词。** 需要按空格拆参数的检查脚本写成 bash 文件。
7. **snapshot 不等于 render。** snapshot 里视频纹理不播放、屏幕是暗的；判断画面以 mp4 的帧为准（engines/README 也这么写）。
8. **不要 `rm -rf` 相对路径的 glob**（安全检查会拦）。临时文件直接放 scratchpad 目录，用完不用手动删。

## 好用的做法

- **90 BPM × 30 fps**：1 拍 = 20 帧，16 分音符 = 5 帧，1 小节 = 80 帧，所有细分都落在整帧上。画面代码和 `score.json` 共用同一个 `bar(k, beat)` 函数，不手写秒数。
- **世界尺寸的字 + ride**：大字按"米"定宽；在高速镜头里，字在读的那段时间骑在镜头前方一段固定距离（例如 16 → 11 m），视觉上的接近速度只有 2–3 m/s，读完再淡出或让镜头穿过。字设 `depthTest: false`，仍然在空间里，但不会被档案墙挡住。
- **Hermite 镜头路径**：按真实时间参数化；`stop` 关键帧做完全静止（关卡停拍）；`tm: "f"/"b"` 让镜头滑过每块屏幕而不越过。
- **两遍自引用**：关卡 ②③ 的门面和纪念碑墙都是本片 draft 的真实帧，由 `tools/self_sheets.sh` 重新烘焙，而不是手做的图。
- **一个 4 s 的局部 composition**（`out/test-proof.html`，用 `window.__T0` 偏移时间）只要 6 s 就能验证某一段；同样的方法可以做确定性测试：1 个 worker 和 3 个 worker 各渲一次比 PSNR，结果逐比特相同（PSNR inf）。
- **声画同源**：配乐 hit、音效事件和画面事件都落在同一个网格上。成片混音用 hop 128 的 onset 检测做 cue check。渐强峰（riser / swell）在节拍表里标成 `swell-peak`，不算打点。

## 可以回流到 harness 的（建议，未改共享文件）

- `playbook/02-verification.md` 或 `engines/README.md`（HyperFrames 一节）加三条：
  - VideoTexture 要设 `needsUpdate`；
  - `buildReady` 必须在经典脚本里同步注册；
  - 用 YAVG 突降找空帧。
- `bin/vh mix` 加两个选项：线性母带（不做动态 loudnorm），以及保留立体声。
- `video-types/03-product-promo.md` 加一段"一镜到底 / 3D 世界"的做法：世界尺寸的字、ride、Hermite 路径、停拍关卡。

## 交付时追加的两条

- **逐像素颗粒会让成片失控：** 带颗粒的母版 1.4 GB，CRF 17 重编码仍有 1.2 GB。README 或 X 用的成片直接用无颗粒母版（107 MB）；一定要颗粒的话，改成低频（2×2 以上）、静态种子的颗粒。
- **`-shortest` 会按 AAC 截短，吃掉最后 2 帧**（2078 帧而不是 2080 帧）。混流时用 `apad,atrim=0:<精确时长>` 把音频补齐或截到视频长度。bin/vh mux 就是这样做的。

## v3 Phase B（全片重构）追加

- **Hermite 在"快进、慢停"处会冲过头。** 甩镜到站点后紧接一段慢推，站点那个关键帧的切线按两侧邻居估，会带着甩镜的速度冲进字里（架构站 1 的标签被推出画面）。做法：到站关键帧用 `tm: "f"`（切线取本段慢推），离站关键帧用 `tm: "b"`，两站之间的甩镜就成了干净的 S 曲线。
- **世界里的节点标签按屏幕像素定尺寸（`pin()`），不要按画面宽度的比例。** 按比例缩放时，长标签的中文掉到 20 多 px。按像素定尺寸后字号稳定（中文 ≥ 46 px），另外还要做两件事：
  - 把标签框夹在安全框内；
  - 节点出画时让标签淡出，否则相机离开后标签会在画面边上堆成一摞。
- **跟镜头的字会被后期运动模糊抹花。** 运动模糊是屏幕空间的，字跟不跟镜头都会被抹。必读字在画面上时，把模糊压到 5%；读长句时不要在下面甩镜，改成慢摇臂。
- **审阅"通过"章在甩镜时读不到。** 章要么等镜头停下再出，要么跟镜头走（放在画面下三分之一）。本片用后者，也避开了关卡中心的光晕。
- **加拍要让配乐和画面一起改。** 列表需要多停 2 拍时：作曲在 `score.json` 加 `"meters": {"11": 6}`，beat map 带 `bars` 数组；画面在 `bar(k)` 里给第 12 小节以后统一加 2 拍，HUD 按真实小节显示。其他秒数一个都不用手改，事件表、字幕、分镜预览也都通过 `bar()` 自动跟上。
- **在混音里做 cue check，比只查配乐严。** 配乐单独 143/143 都准，混进音效后有 3 处"跑偏"：
  - 两个 pop 离配乐的按钮音只差 67 ms，onset 检测把它们并成了一个；解决办法是把画面事件对到按钮音上。
  - 请求卡那一处，whoosh 的上升段盖住了配乐的 hit；解决办法是去掉这个 whoosh。
- **渲染不要依赖在线 CDN。** importmap 指向 CDN 时，断网会让渲染在页面加载处静默挂住：日志为 0 字节，也不报错。做法：
  - three.js 用 `npm i -D --save-exact` 装到项目里，importmap 指向 `./node_modules/...`；HyperFrames 的 snapshot 和 render 都能提供这些文件。
  - 改完用同一时间点的无损 PNG 做 A/B 比对，本片是逐比特相同。
  - 渲染外面包一层看门狗：超时就杀掉，再核对退出码、帧数，并抽帧查 YAVG，确认 3D 层确实画出来了。
- **renderAt 里抛异常时，画面会停在上一帧，不会报错。** 本片第 17 版 draft 里，一个 `const` 在声明之前就被读取了（TDZ），36–48 s 的每一帧都停在 t=0 的画面，HUD 显示 `t 00.00`。检查方法有两种：
  - 抽帧看 HUD；
  - 把每帧和第 0 帧算 PSNR，找异常高的。
