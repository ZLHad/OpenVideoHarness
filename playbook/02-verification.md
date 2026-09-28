# 02 验证闭环

读代码看不出运动的效果，必须渲染出来看。下面按成本从低到高排列各层检查。调研的结论是：第 1–3 层，再加上一个按 rubric 打分的 reviewer，是真正起作用的部分；第 6 层（Gemini 看整片）只能算补充。

## 七层检查

1. **能不能跑**：lint、编译、dry-run。Manim 的报错按 ScopeRefine 的顺序修：先改出错行前后 ±1 行，不行就改整个代码块，再不行就重写整个场景。
2. **不看图的结构检查**（确定性检验：从中间抽几帧单独渲染，和整片里的同一帧比对，要逐像素相同，或者 PSNR ≥ 45 dB；`ffmpeg -i a.png -i b.png -lavfi psnr -f null -`）：
   - 渲染器自带的检查，例如 HyperFrames `check` 会查 DOM 包围盒、文字溢出和对比度；
   - 打印所有对象的包围盒，检查有没有重叠（SGA 的做法）；
   - 用像素统计找空白帧；
   - 黑场、冻结、静音检测（命令见下文）；
   - `ffprobe` 核对时长、fps 和音轨；
   - 检查输出文件的修改时间，防止把旧文件当成新结果。
3. **看静帧**（用 Read 工具读图），分三种粒度：
   - **联系表**：看构图和整片的形状，每个镜头取首、中、末三帧。
   - **strip**：看时序。按固定步长 0.1–0.15 秒出一串帧，从头到尾像观众那样读，数一数每个 read 分到几帧（24 帧 = 1 秒）。
   - **crop**：局部放大，看脸、手、接触点、发光区域。
   - 另外，每个转场前后各 0.5 秒都要单独看。
4. **VLM 批评要给离散选项**：让模型从锚点网格里选位置（Code2Video 的做法），或者从几个渲染出来的变体里挑一个（Paper2Video 的做法）。不要让它输出"往左移 12px"这种数值微调。每轮最多列 3 个问题，每个问题都附一条可以直接执行的修改。
5. **reviewer subagent**：开一个全新上下文，只给它联系表、`TASTE_CHECKLIST.md` 和 `STORYBOARD.md`，让它逐条打分；不合格的退回给写代码的 agent。
6. **整片理解**（可选）：Gemini 能直接读视频，但默认按每秒 1 帧采样，只适合检查叙事和粗略的音画对齐，快速动作里的问题它看不出来。
7. **人**：最终对听感和品味把关。

## 预算

来自 ClaudeAnimationBase：
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
npx hyperframes snapshot --at 1.5,4.2,8.0  # 指定时刻的静帧
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

## 自评的写法

每次自评都写进 `NOTES.md`，格式见 `templates/TASTE_CHECKLIST.md` 的末尾：先写场景编号、时间范围和联系表路径，再写 FAIL 的条目编号，最后写具体改法。只写"看起来不错"不算自评。

## 已知的坑

- **亚像素文字闪烁**：镜头一直漂移时会出现，改成先移动、再停住（Chris Tyson 的 Remotion 实践）。
- **卡片边缘 boiling**：非整数缩放比例（例如 0.6667）会导致，缩放只用 1.0 和 0.5。
- **手绘风里静止的物体跟着抖**：前面某个运动物体打乱了随机数流。给每个元素设置独立的 `boilSeed()`。
- **p5.brush 颜色发灰发绿**：它按颜料的方式混色，所以黄色光叠在蓝底上会变灰绿。发光效果要用 `glow()`。
- **把旧的输出文件当成新结果**：渲染前先删掉旧文件，或者检查修改时间。
