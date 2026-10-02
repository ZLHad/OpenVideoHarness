# 02 验证闭环

读代码看不出运动的效果，必须渲染出来看。下面按成本从低到高排列各层检查。调研的结论是：第 1–3 层，再加上一个按 rubric 打分的 reviewer，是真正起作用的部分；第 6 层（Gemini 看整片）只能算补充。

## 七层检查

做到第几层，按努力程度定（CLAUDE.md"努力程度"）：
- `quick`：第 1、2 层，加上整片一张联系表、一张按目标屏缩的联系表和前 2 s 的逐帧 strip（命令见下文"手机测试"），出片前跑 `bin/vh check`；
- `standard`：七层都做，第 5 层的独立评审做 1 轮；
- `studio`：七层都做，第 5 层至少 3 轮，外加下文的循环接缝、无损确定性和音频 QA（手机测试每一档都做）。

1. **能不能跑**：lint、编译、dry-run。Manim 的报错按 ScopeRefine 的顺序修：先改出错行前后 ±1 行，不行就改整个代码块，再不行就重写整个场景。
2. **不看图的结构检查**（确定性检验：从中间抽几帧单独渲染，和整片里的同一帧比对，要逐像素相同，或者 PSNR ≥ 45 dB；比的是无损 PNG 帧，不是编码后的 mp4，原因见下文"确定性"；`ffmpeg -i a.png -i b.png -lavfi psnr -f null -`）：
   - 渲染器自带的检查，例如 HyperFrames `check` 会查 DOM 包围盒、文字溢出和对比度；
   - 打印所有对象的包围盒，检查有没有重叠（SGA 的做法）；
   - 用像素统计找空白帧和卡住的帧：逐帧 YAVG 找突降，逐帧和第 0 帧比 PSNR，见下文"静默失败"；
   - 黑场、冻结、静音检测（命令见下文）；
   - `ffprobe` 核对时长、fps、音轨和色彩标签（命令见下文"色彩标签"）；
   - 检查输出文件的修改时间，防止把旧文件当成新结果。
3. **看静帧**（用 Read 工具读图），分三种粒度：
   - **联系表**：看构图和整片的形状，每个镜头取首、中、末三帧。
   - **strip**：看时序。按固定步长 0.1–0.15 秒出一串帧，从头到尾像观众那样读，数一数每个 read 分到几帧（24 帧 = 1 秒）。
   - **crop**：局部放大，看脸、手、接触点、发光区域。
   - 另外，每个转场前后各 0.5 秒都要单独看；整片再按目标屏的尺寸看一遍（BRIEF 的 `Watch on`）；循环播放的交付物还要看末帧接首帧（两条命令见下文"手机测试与循环接缝"）。
4. **VLM 批评要给离散选项**：让模型从锚点网格里选位置（Code2Video 的做法），或者从几个渲染出来的变体里挑一个（Paper2Video 的做法）。不要让它输出"往左移 12px"这种数值微调。每轮最多列 3 个问题，每个问题都附一条可以直接执行的修改。
5. **reviewer subagent**：开一个全新上下文，只给它联系表、`TASTE_CHECKLIST.md` 和 `STORYBOARD.md`，让它逐条打分；不合格的退回给写代码的 agent。
   - **人设**：严苛的动效导演，不是为作品自豪的作者。提示词的大意是："这支片子不是你做的。你是一位挑剔的动效导演，任务是找出它为什么还不能发。"作者自己看久了会习以为常，换一个没有感情投入的人才看得出。
   - **输入**：除了上面三样，整片 draft 还要给目标屏联系表、关键动作和转场的 strip、cue check 结果。不给作者的 NOTES 自评，免得 reviewer 被作者的解释带偏；只另外给 BRIEF 的立意一行和 `DECISIONS.md` 里口味覆盖的几行，让它判断立意落没落到画面上、每个覆盖站不站得住。
   - **输出**：20 条 PASS/FAIL，加上 `TASTE_CHECKLIST.md` 文末打分层的八个维度（1–10 分，含立意），再列出最差的 3 个问题，每个都写时间点和改法。有 FAIL，或任何维度低于 8，就退回；至少跑 3 轮，每轮只重渲受影响的时间段。
6. **整片理解**（可选）：Gemini 能直接读视频，但默认按每秒 1 帧采样，只适合检查叙事和粗略的音画对齐，快速动作里的问题它看不出来。
7. **人**：最终对听感和品味把关。

## 预算

以下是 `standard` 和 `studio` 的最低量（`quick` 的量见上面第 8 行）。来自 ClaudeAnimationBase：
- 每个镜头至少一张联系表；
- 每个关键动作和每个转场各一条 strip；
- 每张承载剧情的脸一个 crop。

本机实测一张 6 帧联系表只要 5 秒，这一步不要省。

## 各引擎的取帧命令

**ClaudeAnimationBase / p5（在你的项目目录下运行，项目由 `bin/vh new handdrawn|mv <slug>` 从 `engines/ClaudeAnimationBase/` 复制而来）**

```bash
node render.mjs --sheet=0.1,0.8,1.6,2.4 --cols=4 --w=320 --out=out/check/sheet.jpg   # 联系表
node render.mjs --strip=2.1:2.6 --cols=6 --w=320 --out=out/check/strip.jpg            # 这段时间里的每一帧
node render.mjs --sheet=2.3,2.4 --crop=760,420,500,400 --w=500 --out=out/check/face.jpg  # 全分辨率局部
node render.mjs --strip=2.1:2.6 --crop-at=960,700,500,400 --out=out/check/feet.jpg      # 跟着世界坐标的一个点裁切
```

**HyperFrames**

```bash
npx hyperframes lint                       # 写 HTML 过程中随时跑
npx hyperframes check --snapshots          # 最终关卡：lint + 运行时错误 + 布局 + 对比度，附带标注帧
npx hyperframes snapshot --at 1.5,4.2,8.0 --describe false  # 指定时刻的静帧；不带 --describe false，设了 GEMINI_API_KEY 时帧会发给 Gemini（见 engines/README.md）
npx hyperframes preview --background       # 给用户看，确认后再 render
npx hyperframes render --quality draft     # 快速出片；最终交付用 --quality delivery --output out.mp4
# 命令前先 export HYPERFRAMES_SKIP_SKILLS=1（见 engines/README.md）
# snapshot 在 tween 起点可能和渲染结果不一致，关键帧以 mp4 为准。逐帧 strip：
ffmpeg -i out/draft.mp4 -vf "select='between(n,95,106)',scale=320:-1,tile=6x2" -vsync vfr -frames:v 1 out/check/strip.png
```

**Remotion**

```bash
npx remotion still <CompositionId> out/check/f120.png --frame=120
npx remotion render <CompositionId> out/draft.mp4 --scale=0.5
```

**Manim CE**

```bash
manim -ql scene.py MyScene                 # 480p15 快速渲染
manim -ql -s scene.py MyScene              # 只存最后一帧
manim -qh --fps 30 scene.py MyScene        # 成片 1080p30（-qh 默认 60fps，-qk 是 4K60）
manim -ql --format png -n 30,31 scene.py MyScene   # 只渲染第 30–31 个动画为 PNG：与整片同帧做哈希比对，就是 Manim 的确定性检查
# 拿到 mp4 后，用下面的 ffmpeg 通用命令拼联系表
```

**通用：从任何 mp4 取帧（ffmpeg，本机实测可用）**

```bash
ffmpeg -i out.mp4 -vf "fps=1,scale=480:-1,tile=6x5" -frames:v 1 out/check/sheet.png                  # 每秒 1 帧的总览
ffmpeg -ss 11.7 -i out.mp4 -t 0.6 -vf "fps=10,scale=320:-1,tile=6x1" -frames:v 1 out/check/seam.png  # 某个切点 ±0.3 秒
ffmpeg -i out.mp4 -vf "blackdetect=d=0.3,freezedetect=d=1.5" -af silencedetect=d=1.5 -f null - 2>&1 | grep -E "black_|freeze_|silence_"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact out.mp4
```

## 手机测试与循环接缝

**手机测试**（按目标屏缩）：缩到多宽看 BRIEF 的 `Watch on`。`phone`（竖屏）和 `feed`（横屏片放进手机信息流、不转屏）都按 360 px：常见手机在 360–430 个 CSS 像素之间，取下限。`desktop`（电脑，或手机转成横屏全屏）按 640 px：手机比 16:9 长，转成横屏全屏时画面按屏幕高度放，约 640–760 px 宽；电脑播放器默认约 850–1000，取下限。把每格缩到这个宽度，按原尺寸看：必读字读不出、主体认不出，就对应 TASTE_CHECKLIST 的 #5、#6，也是打分层"目标屏可读"一项的证据。

```bash
# 每 2 秒 1 格，每格 360 px 宽；片子长会自动出多张，不要为了塞进一张而把格子再缩小（竖屏改 tile=4x2）
ffmpeg -i out.mp4 -vf "fps=1/2,scale=360:-1:flags=area,tile=3x4" out/check/phone_%02d.png
# desktop：每格 640 px 宽，一张 2×3 格
ffmpeg -i out.mp4 -vf "fps=1/2,scale=640:-1:flags=area,tile=2x3" out/check/screen_%02d.png
```

整张图的长边控制在约 1500 px 以内。图太大时，读图会把它再缩一次，测出来就不准了。

字号下限换到屏幕上是多大，见 `03-motion-design.md` §4 的表：同一个 44 px，竖屏手机上约 15 px，横屏片放进手机信息流只有约 8 px（`docs/research/06-concept-first-ab.md`），所以 `feed` 那一档的下限高得多。

**开头 2 秒**：钩子要在第 0 帧就开始。把前 60 帧（30 fps 的 2 s）逐帧拼成一张，看画面是不是一开始就在动、有没有让人停下来的东西：

```bash
# 30 fps 取前 60 帧；每格 150 px 宽，整张 1500 px 宽（长边规则同上）
ffmpeg -i out/draft.mp4 -vf "select='lt(n,60)',scale=150:-1,tile=10x6" -vsync vfr -frames:v 1 out/check/first2s.png
```

**循环接缝**：GIF、网页背景、平台自动循环这类交付物，末帧后面紧跟着首帧。把末 6 帧和首 6 帧拼成一条，像观众那样连着读：

```bash
N=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 out.mp4)
ffmpeg -i out.mp4 -i out.mp4 -filter_complex "[0:v]select='gte(n,$N-6)'[a];[1:v]select='lt(n,6)'[b];[a][b]concat=n=2:v=1,scale=320:-1,tile=6x2" -frames:v 1 out/check/loop_seam.png   # 上行末 6 帧，下行首 6 帧
```

理想的循环是 f(T) = f(0)，T 是片长。这样末帧 f(T − 1/fps) 到首帧只差一步正常的运动。末帧和首帧一模一样反而不对，循环时会多停一帧；差得太远就是跳一下。量化的办法：末帧对首帧的 PSNR，应该和片尾任意相邻两帧之间的 PSNR 差不多。

## 确定性：比无损帧，不比 mp4

硬规则 1 的"PSNR ≥ 45 dB"指的是无损帧。x264 会沿参考帧把 GPU 光栅化带来的几个像素的差异放大。本仓库的介绍片（intro film）v3 做过对照：1 个 worker 和 3 个 worker 渲出的无损 PNG 序列，最低 PSNR 在 60–92 dB 之间，肉眼看不出；同样两次渲染编码成 mp4 再比，最低掉到约 42 dB，会被误判为不确定。

那几个像素来自 GPU 上的 2D canvas 光栅化：文字边缘在不同的 Chrome 进程里差 1 个色阶，同一台机器上每次都不一样。要逐字节相同，给 `hyperframes render` 加 `--no-browser-gpu`（SwiftShader 渲 WebGL，canvas 和合成都在 CPU 上，截帧路径也不再随 worker 数变）；样片渲染器 `styles/_swatch/render.sh` 就是这么做的，代价是慢一些，原因和数据见 `styles/_swatch/README.md` 的"确定性"。

```bash
# HyperFrames：同一段分别用 1 个和 3 个 worker 渲成 PNG 序列，再逐帧比
npx hyperframes render --format png-sequence --workers 1 --output out/det/w1
npx hyperframes render --format png-sequence --workers 3 --output out/det/w3
ffmpeg -i out/det/w1/frame_%06d.png -i out/det/w3/frame_%06d.png -lavfi psnr=stats_file=out/check/det.txt -f null -   # 看汇总的 min，和每帧的 psnr_avg
```

**HyperFrames 的 PNG 序列是 RGBA，不画页面背景。** `--format png-sequence` 写的是带 alpha 的 PNG（命令行帮助里写的就是 RGBA 帧）：`html`、`body` 和合成根元素（带 `data-composition-id` 的那个）上的 `background` 不会画进去，那些地方 alpha = 0；只有元素自己的底色（比如一个铺满全屏的 `div`）会留下。这对上面的比对有三个影响：
- **帧和 mp4 里的不是同一张图。** 没被元素盖住的地方是透明的，PNG 序列直接转成 mp4，背景是黑的（实测 RGB 0,0,0）；同一个合成直接 `render` 出的 mp4 是页面的底色。要和 mp4 的帧比，先把 PNG 叠到底色上。
- **页面背景上的东西查不到。** 背景若画在 `html`、`body` 或根元素上，序列里根本没有它，它不确定也查不出来。要让检查盖住背景，把底色放进一个铺满全屏的子元素：整帧不透明，PNG 也就成了不带 alpha 的 RGB。
- **上面那条 `ffmpeg … psnr` 可能不准。** 画面里只要还有一点透明，帧就是 RGBA；全部不透明了，帧就变成 RGB（比如底色淡入的前几帧是 RGBA，之后是 RGB）。ffmpeg 读到格式变化，会在中途重建滤镜：汇总打印两次，`stats_file` 只剩开头几行。RGBA 输入时 `average` 还把 alpha 当成第 4 个通道，比只算 RGB 高约 1.25 dB（实测 61.02 对 62.27），45 dB 的门槛被悄悄放宽（ffmpeg 8.0.1 实测）。序列里有透明的话，改成一对一对地比，先转成 rgb24，只列字节不同的帧（像素相同的显示 inf）：

  ```bash
  for f in out/det/w1/frame_*.png; do n=${f##*/}; cmp -s "$f" "out/det/w3/$n" || ffmpeg -nostdin -v info -i "$f" -i "out/det/w3/$n" -lavfi "[0:v]format=rgb24[a];[1:v]format=rgb24[b];[a][b]psnr" -f null - 2>&1 | sed -n "s/.*average:\([0-9.inf]*\).*/$n \1 dB/p"; done
  ```

长片不必全片都比。介绍片的做法是单独建一个 4 s 的局部 composition（用一个时间偏移变量把起点挪到要测的段落），6 s 就能渲完。Manim 的对应做法见上面 `--format png` 那一行。

## 静默失败

有几种故障不报错、不崩溃，渲染照样显示"成功"，只有逐帧统计才抓得到：

- **renderAt 抛异常，画面停在上一帧。** 介绍片第 17 版 draft 里，一个 `const` 在声明之前就被读取（TDZ），36–48 s 共 12 秒的每一帧都停在 t=0 的画面，渲染日志里没有任何错误。画面上有 HUD 时间码的话，抽帧读 HUD 最快；通用做法是把每帧和第 0 帧比 PSNR，找异常高的连续段。`freezedetect` 不一定抓得到：只要颗粒或别的图层还在逐帧变化，画面就不算"冻结"。
- **空帧。** 异步 build 还没完成，worker 的第一帧就被截了图。介绍片里是每个 worker chunk 开头的 1–2 帧，YAVG 24，前后都是 62。逐帧读 `signalstats` 的 YAVG，找突降。修法：在一段经典内联脚本里同步注册一个就绪 promise，由模块脚本在 build 完成、第一帧画完之后 resolve，渲染器等它再截图。
- **渲染永远挂住。** importmap 指向 CDN 时，断网会让渲染卡在页面加载处：日志 0 字节，不报错，进程也不退出。依赖一律装进项目（`npm i -D --save-exact`，importmap 指向 `./node_modules/`），渲染外面再包一层看门狗：超时就杀掉，检查退出码，核对帧数，抽几个时间点查 YAVG，确认主画面层确实画出来了。

```bash
ffmpeg -i out.mp4 -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=out/check/yavg.txt" -f null -   # 逐帧平均亮度，找突降
ffmpeg -i out.mp4 -frames:v 1 out/check/f0.png
ffmpeg -i out.mp4 -loop 1 -i out/check/f0.png -lavfi "psnr=stats_file=out/check/psnr_f0.txt:shortest=1" -f null -   # psnr_avg 异常高的连续段 = 画面卡回了 t=0
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 out.mp4   # 帧数应等于时长 × fps

# 看门狗（macOS 默认没有 timeout 命令）：超过 25 分钟就杀掉，退出码非 0 就报错
npx hyperframes render --output out/draft.mp4 > out/draft.log 2>&1 & pid=$!; t=0
while kill -0 $pid 2>/dev/null; do sleep 5; t=$((t+5)); [ $t -ge 1500 ] && { kill $pid; break; }; done
wait $pid || echo "FAIL: render exited $? (timeout or error), see out/draft.log"
```

## 色彩标签：每个 mp4 出片前查一次

PNG（或别的 RGB 画面）编成 H.264 时，如果不指定 BT.709 矩阵和标签，swscale 按 BT.601 算矩阵，又不写标签；浏览器和手机把高清片按 BT.709 解码，饱和色就偏了。用 8 个色块实测，最大偏 21 个色阶（绯红 (225,29,72) 读成 (238,48,69)，翠绿 (16,185,129) 读成 (1,164,126)）；显式写 BT.709 矩阵和四个标签后最大偏 3，这是 8 位 YUV 往返的基线【实测】。这 8 个色块里没有纯色；纯绿 (0,255,0) 用同样的方法量，读成 (0,215,0)，偏 40【实测】。

**浏览器只认一部分标签。** 在 Chrome 154（无头）和 Chromium 152 里，用同一批 BT.601 像素只改标签实测：矩阵写 `smpte170m` 的都按 BT.601 读对（最大偏 1–2，transfer 和 primaries 写不写都一样）；矩阵写 `bt470bg` 的读错，只写矩阵偏 24（绯红读成 (241,50,69)，翠绿读成 (3,165,128)），三项都写成 `bt470bg` 反而偏 38–40；不写标签的高清片按 BT.709 读。ffmpeg 读这几种都对，浏览器不是。旧的手绘引擎输出 `yuvj420p, pc, bt470bg`，所以在浏览器里偏色。不要依赖浏览器怎么处理 BT.601 的各种标签：交付一律用 BT.709，四个标签写全。

```bash
# 查一个文件：期望 pix_fmt=yuv420p，color_range=tv，color_space、color_transfer、color_primaries 都是 bt709
ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt,color_range,color_space,color_transfer,color_primaries -of default=nw=1 out.mp4

# 出片：PNG 序列编成 mp4 时，矩阵、范围和四个标签都显式写
ffmpeg -framerate 30 -i out/plate/f_%04d.png \
  -vf "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
  -c:v libx264 -crf 14 plate.mp4

# 查整个仓库已提交的 mp4：列出不是 yuv420p,tv,bt709,bt709,bt709 的
git ls-files '*.mp4' | while read -r f; do
  t=$(ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt,color_range,color_space,color_transfer,color_primaries -of csv=p=0 "$f" </dev/null | sed 's/,$//')
  [ "$t" = "yuv420p,tv,bt709,bt709,bt709" ] || echo "$f  $t"
done
```

`yuvj420p`、`color_range=pc`（全范围）、`bt470bg` 或 `smpte170m`（BT.601 矩阵）和 `unknown` 都不合本仓库的交付约定。手绘引擎 `engines/ClaudeAnimationBase/render.mjs` 原来把 Chrome 的 JPEG 帧（全范围 BT.601）直接喂给 x264，出的片子正是 `yuvj420p, pc, bt470bg`；它现在已经转成 BT.709 tv 并写全四个标签，改之前渲的片子要重新编码才会变。

**本仓库 2026-10-01 的审计**：已提交的 34 个 mp4 里，32 个是约定值，两个不是，都已在配声音时重编码成 BT.709 tv、写全四个标签（命令和核对数字在各自的 NOTES.md）：
- `showcase/01-handdrawn-clawd-leaf/media/final.mp4` 原来是 `yuvj420p`、全范围、`bt470bg`，就是上面引擎改之前的输出。**浏览器里确实偏色**，不只是不合约定：在 Chrome 154 里，它第 11.5 s 的饱和像素平均 R +6、G +5、B −5。ffmpeg 按标签读没有问题。
- `showcase/03-math-fourier/media/final.mp4` 原来没有任何标签，但像素是 BT.601。按 BT.601 解码，样片调色板里的 `#FFFF00` 原样还原（第 15 s 一帧里约 3000 个像素），按 BT.709 解码（浏览器的做法）变成 (255,240,0)（约 6000 个像素）；`#58C4DD` 变成 (78,187,224)（算出来的值）。没有源帧时，就用已知调色板这样判断矩阵。

`showcase/04-intro-film/assets/clips/` 在 `.gitignore` 里，是 `showcase/04-intro-film/tools/make_clips.sh` 从 00–03 的成片重建的代理；重编码之前建的 `01.mp4`、`03.mp4` 还带着旧标签，重跑脚本即可。

**只补标签不等于修好。** 像素本来就是 BT.709 tv、只是缺标签的文件，可以不重编码：`-c copy -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0`。像素是 BT.601 或全范围的文件（比如上面那两个原来的成片），只改标签会让它们"看上去标对了"却错得更多：在按 BT.601 全范围编的色块上试过，只改成 BT.709 标签，最大偏 29 个色阶。这类文件要重编码，用上面"出片"那条的滤镜链就行：

```bash
ffmpeg -i in.mp4 -vf "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" -c:v libx264 -crf 14 out.mp4
```

ffmpeg 有标签时按标签读，没有标签时按 BT.601 tv 读，所以 01（有标签）和 03（没有标签，像素是 601）都能转对：在 Chrome 里量过，转完的 03，第 15 s 的 `#FFFF00` 回到 (255,255,0)，不再是 (255,240,0)；转完的 01，同一帧饱和像素的平均偏差从 R +6 / B −5 变成 R −4 / B −4，没有方向性了，剩下的是重编码的损失。如果像素其实是 BT.709 却没写标签，在 `scale=` 里先加 `in_color_matrix=bt709:in_range=tv`。重编码一次有损，能从源头重出就从源头重出【实测】。

`flags=accurate_rnd+full_chroma_int` 在 YUV 换矩阵时要加：swscale 默认的换算不够准，03 的纯黄 `#FFFF00` 换出来 Y 是 217（该是 219），x264 编码后按 BT.709 解出来 (252,253,0)；加上以后是 (254,254,1)。从 PNG 这类 RGB 源出片时，加不加结果一样（8 个纯色块最大都偏 1.1 个色阶）【实测】。

## 音频 QA

agent 听不见声音，声音也只能靠数字查。介绍片 v2 的画面自查全过了，用户却听出"部分地方卡顿或者消失"。事后扫描，v2 的混音里有 94 个 0.1 s 窗口比所在段落的中位数低 12 dB 以上，另有 6 段数字静音。最终成片上，下面四项扫描都没有问题（cue check 180/180 在 1 帧以内）。

| 扫描 | 对什么做 | 做法 | 判为问题 |
|---|---|---|---|
| 掉音 | 成片混音 | 每 0.1 s 一个 RMS，和所在段落的中位数比 | 比段中位数低 12 dB 以上（片头片尾的淡入淡出除外）；片中任何数字静音（< −60 dBFS，持续 ≥ 20 ms） |
| 抽吸（pumping） | 音乐总线 | 50 ms RMS 对 600 ms 滑动中位数 | 凹下超过 4 dB、持续 ≥ 60 ms，而且不在设计好的打点附近（打点前 0.05 s 到后 0.4 s） |
| 爆音（click） | 成片混音 | 采样级的二阶差分，和前后 5 ms 的局部 RMS 比（不含该采样前后 ±1 ms，否则孤立的 click 永远超不过门槛） | **只报警告，不算失败**：机器分不清设计好的尖锐起音和真故障。超过局部 RMS 的 15 倍且高于 −40 dBFS、又不在设计好的起音附近（节拍表的 `hits`、`beats` 和音效事件落点的前后 40 ms，`--click-grace` 可调）的，按倍数排序列出最严重的 10 处，请人耳复听 |
| cue check | 成片混音（WAV 是门禁；mp4 再查一遍，容差加 12 ms，单个 cue 只作警告） | onset 检测（hop 128 采样，48 kHz 下约 2.7 ms），和节拍表、音效事件表逐条比；每条打印 margin（超出检测门槛多少）；近乎纯音的音效 onset 没找到时，用它自己的声音做互相关确认；第 0 帧的 cue 先垫一帧静音 | 任何一个 cue 离最近的 onset 超过 1 帧；margin 低于 0.02 的标 `OK~`，只作警告；mp4 上整个编码偏了（8 个以上 cue 时超过 20% 对不上，或中位误差超过 15 ms，是封装错位） |
| 层次（`qa mix`） | 混音 profile 写出的各总线（`--stems`） | 逐句 VMR（人声减音乐）、每个词的 1–4 kHz SNR、每个音效相对锚点的响度和类、纵深、限幅器，见 `04-audio.md` 的"混音" | 有一句低于 profile 的 VMR 下限；说话时 hero 盖过人声；危险的词超过比例；某类音效的中位数离范围超过 3 LU；timeline 有句子，人声 stem 却全是静音；一个 cue 只以“弱”对上，报告又判它 `BURIED` |

```bash
# 掉音扫描的原料：每 0.1 s 一个 RMS（48 kHz 下是 4800 采样，44.1 kHz 改成 4410），再按段落求中位数比较
ffmpeg -i audio/mix.wav -af "asetnsamples=n=4800:p=0,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=out/check/rms.txt" -f null -
bin/vh qa audio/mix.wav audio/music.beats.json audio/events.json --stems audio/stems --out out/check/audio-qa.txt   # 四项扫描 + cue check + 混音报告一条命令（tools/audio/qa.py），有问题时退出码为 1
bin/vh qa out/final-av.mp4 audio/music.beats.json audio/events.json --out out/check/audio-qa-mp4.txt              # 成片再查一遍：扫描照常判定，单个 cue 只作警告，整体偏移（封装错位）判失败
```

cue check 必须在最终混音上做，只查配乐不够。介绍片的配乐单独查时每个 hit 都准，混进音效后出了 3 处偏差：两个 pop 离配乐的按钮音只差 67 ms，onset 检测把它们并成了一个；另一处 whoosh 的上升段盖住了配乐的 hit。修法分别是把画面事件改对到按钮音上，以及删掉那个 whoosh。riser、swell 这类渐强没有瞬态，在节拍表里标成 `swell-peak`，不参加打点检查。

## 自评的写法

每次自评都写进 `NOTES.md`，格式见 `templates/TASTE_CHECKLIST.md` 的末尾：先写场景编号、时间范围和联系表路径，再写 FAIL 的条目编号，最后写具体改法。只写"看起来不错"不算自评。

## 已知的坑

- **亚像素文字闪烁**：镜头一直漂移时会出现，改成先移动、再停住（Chris Tyson 的 Remotion 实践）。
- **卡片边缘 boiling**：非整数缩放比例（例如 0.6667）会导致，缩放只用 1.0 和 0.5。
- **手绘风里静止的物体跟着抖**：前面某个运动物体打乱了随机数流。给每个元素设置独立的 `boilSeed()`。
- **p5.brush 颜色发灰发绿**：它按颜料的方式混色，所以黄色光叠在蓝底上会变灰绿。发光效果要用 `glow()`。
- **把旧的输出文件当成新结果**：渲染前先删掉旧文件，或者检查修改时间。
- **镜头推近后字发虚**：被缩放的元素挂着 CSS `will-change: transform` 时，浏览器会按它当时的尺寸栅格化成一张位图，之后的放大只是把这张位图拉大。要被推近、放大的元素不加 `will-change`；或者按放大后的尺寸排版，入场时再缩小。
- **第一帧用了回退字体**：网页字体还没加载完就截了第一帧，前几帧的字宽不同，排版会跳一下。第一次截图之前先 `await document.fonts.ready`，把它并进渲染器等待的就绪 promise 里（见上文"静默失败"的空帧一条）。
- **canvas 上的中文网页字体只加载了一部分**：`document.fonts.ready` 只等"已经开始加载"的字体。canvas 要到第一次画某个字时才去下载它所在的字体文件，这一帧先用回退字体画；而 Google Fonts 把中文字体按 unicode-range 切成上百个分片（Noto Serif SC 的一个字重是 101 个），只有用到的分片才会下载。所以 ready 了也可能缺字，缺的字悄悄用系统字体画出来。做法是对每个字重调一次 `document.fonts.load('700 40px "Noto Serif SC"', 全部要用的字)`，把片中所有中文字一次交给它。abstract-algebra-promo 的取字办法很省事：页面脚本源码里所有非 ASCII 字符去重，再加上 A–Z、a–z、0–9。它的毛病也值得记住：`load()` 的失败被 `.catch(() => {})` 吞掉，15 s 后不管成没成都把就绪标记设为真，断网时导出会用回退字体照常出片。我们的规矩是失败就大声报错：`load()` 被拒、返回的 FontFace 数组为空（字体串没匹配上任何 `@font-face`，常见于族名拼错或样式表没加载进来），或超过时限（例如 60 s）还没好，都抛异常，让渲染器以非 0 退出；不要设"超时就当就绪"的兜底。
