# 08 · ManimGX 当 Manim 的后端：showcase 03 换过去，要改几行、差多少、快多少

*记录于 2026-10-29 · 状态：ManimGX 0.1.1 在本笔记的 PR 里登记为可选后端（`tools/modules.json`，`bin/vh doctor` 报它），类型 01、06 的首选仍是 Manim CE · [English](en/08-manimgx.md)*

## 问题

ManimGX 照 Manim CE 的 Python API 写场景，内核是 Rust 和 wgpu，作者说比 CE 快得多（M4 Pro 上五个 1080p60 场景合计 90 倍，含 3D）。拿本仓库的 showcase 03（傅里叶方波，25 s，Manim CE 0.21）原样搬过去：要改几行，画面差多少，快多少，出来的文件能不能直接进本仓库的流程？

## 做法

- 同一台机器（M3 Max，macOS 15.8），同一份 `scenes/`：Manim CE 0.21.0 / Python 3.12（uv），`-qh --fps 30 --disable_caching`；ManimGX 0.1.1 / Python 3.13（uvx，不进项目环境），`-r 1920x1080 --fps 30`。各渲两遍，记第二遍：LaTeX、着色器和字体的缓存都热了。
- 只改到能跑为止（下面第 1 条）。
- 比画面：ManimGX 的片子换成恒定 30 fps 后，和 CE 的逐帧比 PSNR（全尺寸 RGB；再缩到 480×270 比一次，抹掉描边的抗锯齿）；每一帧在对方前后 12 帧里找最像的一帧，看两边同一时刻画的是不是同一刻；并排看 3、8、16、20 s（图 8.1）。
- 比文件：帧数、时长、颜色标签；`bin/vh check`；ManimGX 渲两遍的帧是不是逐字节相同。

## 发现

1. **要改 4 处**：`from manim import *` 换成 `from manimgx import *`；numpy 自己导入（ManimGX 的星号导入不带 `np`）；ManimGX 导出一个叫 `Path` 的图形类，盖掉了文件开头导入的 `pathlib.Path`（场景里 `Path("out/check/…").unlink()` 报错），星号导入之后再导一次 pathlib；`rate_functions.ease_in_out_sine` 写成顶层的 `ease_in_out_sine`（没有 `rate_functions` 这个模块）。其余照跑：`always_redraw` 加 `z_index` 的写法、`ValueTracker`、`MathTex` 的分段上色、`Brace`、`DashedLine`。
2. **快 5 倍左右**：第二遍 CE 18.3 s，ManimGX 3.6 s（它自己记的渲染时间是 3.0 s，其余是启动）；第一遍 CE 37.8 s（含 LaTeX 编译），ManimGX 3.7 s。作者的 90 倍来自五个场景、包括 3D；这支 2D 片子在这台机器上是 5 倍。
3. **看得出是同一支片子，像素不一样**：全尺寸逐帧 PSNR 中位数 25.8 dB（最低 16.9）；缩到 480×270 中位数 31.7 dB，画面在动的帧 27.7 dB。差别主要来自排版和描边：公式由 Typst 排，括号和省略号的字形、间距和 LaTeX 的不一样；曲线描边的抗锯齿不一样。时间上大多对齐（每一帧最像的那一帧，中位数是同一帧），但几段快速的数值动画差 6–10 帧：16 s 处 CE 的计数到了 N = 15，ManimGX 是 13（图 8.1 第三行）。CE 把每段 play 的时长取整到帧，ManimGX 按精确时刻算每一帧，一串短 play 之后落点会错开。
4. **文件要先整理，才能进本仓库的流程**：ManimGX 写的是可变帧率的 MP4，画面不变的一段编成一个长帧（25 s 只有 482 帧，最后一帧长 2.63 s），而且在场景结尾多一帧（重定成 30 fps 是 751 帧，CE 是 750）；颜色是 BT.601 的矩阵，标 `smpte170m` 和 sRGB 原色。`bin/vh check`、`mux` 和剪辑表都要恒定帧率和 BT.709 的四个标签。按片长截、`fps=30`、BT.601 换成 BT.709 再打标签，用 ffmpeg 整理一遍（命令在 `engines/manimgx.md`）之后，`bin/vh check` 全过：750 帧、25.00 s、BT.709，报的提醒和 CE 版一样（开头的黑场、1–4 s 的静止）。整理前后同一帧 44.9 dB。按时刻抽帧也要用整理过的那支：在原文件上 `-ss 24.5` 落在最后那个长帧里，抽不出画面。
5. **两遍渲出的帧逐字节相同**（解码后逐帧比 md5），在这台机器的 GPU 上。

![Manim CE（左）和 ManimGX（右）在 3、8、16、20 s](figs/08-ce-vs-gx.jpg)

图 8.1 · Manim CE 0.21（左）和 ManimGX 0.1.1（右）在 3、8、16、20 s。公式的字形和间距不同；16 s 处计数一边是 15、一边是 13。

## 因此改了什么

- `tools/modules.json` 登记 `manimgx`，钉 0.1.1，装成 uv 的工具；`bin/vh doctor` 报它在不在、是不是钉的版本（doctor 对程序也比钉的版本了，以前只比 npm 包）。
- 新的 `engines/manimgx.md`：怎么装、场景改哪几行、出片前怎么整理、时间和许可要注意什么；`engines/README.md` 的 Manim 一节加一行指过去（类型 01、06 每一档的读量因此多约 200 个字符）。
- 类型 01、06 的首选引擎不变。换不换由项目定，写进它的 `DECISIONS.md`。

## 还没弄清楚的

- 只比了一支 2D 片子。3D 场景（ManimGX 的长项）、长片、带旁白的场景（它的 `self.say`）都没比。
- 数值动画差 6–10 帧，是取整的差别，还是它对 `.animate` 叠加的语义不同，没有拆开看。卡点要和旁白对齐的片子，换后端之后要重新核对时间。
- Linux 没有 GPU 时它用 lavapipe，速度和确定性没量。
- 许可：ManimGX 自己的代码是 MIT，原生 wheel 带着 x264，整体按 GPL-3.0-or-later 发。在本机装来出片不受影响，但它不能随本仓库分发。

来源：本机实测，2026-10-29（showcase/03-math-fourier 的 `scenes/`，Manim CE 0.21.0 和 ManimGX 0.1.1）；ManimGX 0.1.1 的 README 和 "Coming from Manim CE" 一页（manimgx.academa.ai）。
