# 08 · ManimGX 当 Manim 的后端：showcase 03 换过去，要改几行、差多少、快多少

*记录于 2026-10-29 · 状态：ManimGX 0.1.1 在本笔记的 PR 里登记为可选后端（`tools/modules.json`，`bin/vh doctor` 报它），类型 01、06 的首选仍是 Manim CE · [English](en/08-manimgx.md)*

## 问题

ManimGX 照 Manim CE 的 Python API 写场景，内核是 Rust 和 wgpu。它的 README 说，在一台 Apple M4 Pro 上的五个 1080p60 场景里，它比 CE 快 90.6 倍（"90.6× faster than ManimCE"，从启动到写完 MP4，各家都用最快的编码预设；没说是哪五个场景）。拿本仓库的 showcase 03（傅里叶方波，25 s，Manim CE 0.21）原样搬过去：要改几行，画面差多少，快多少，出来的文件能不能直接进本仓库的流程？

## 做法

- 同一台机器（M3 Max，macOS 15.8），同一份 `scenes/`：Manim CE 0.21.0 / Python 3.12（uv），`-qh --fps 30 --disable_caching`；ManimGX 0.1.1 / Python 3.13（uvx，不进项目环境），`-r 1920x1080 --fps 30`。各渲两遍，记第二遍：LaTeX、着色器和字体的缓存都热了。
- 只改到能跑为止（下面第 1 条）。
- 比画面：ManimGX 的片子换成恒定 30 fps 后，和 CE 的逐帧比 PSNR：全尺寸，两边都转成 RGB，用 ffmpeg 的 psnr 滤镜；再比一次 480×270 的，先解码成全尺寸的 RGB，再按面积平均缩小，抹掉描边的抗锯齿。每一帧在对方前后 12 帧里找最像的一帧，看两边同一时刻画的是不是同一刻；并排看 3、8、16、20 s（图 8.1）。
- 比文件：帧数、时长、颜色标签；`bin/vh check`；ManimGX 渲两遍的帧是不是逐字节相同。

## 发现

1. **改的地方**：场景和它的辅助模块里，每一处 `from manim import …` 都换成 `manimgx`，这里是两处（`fourier.py` 的 `from manim import *`，`style.py` 的 `from manim import VMobject, ManimColor, config`）；ManimGX 导出一个叫 `Path` 的图形类，盖掉了文件开头导入的 `pathlib.Path`（场景里 `Path("out/check/…").unlink()` 报错），星号导入之后再导一次 pathlib；`rate_functions.ease_in_out_sine` 写成顶层的 `ease_in_out_sine`（没有 `rate_functions` 这个模块）。合起来四处。0.1.1 的星号导入会把 `np` 一起带出来，显式 `import numpy as np` 不是必需的。其余照跑：`always_redraw` 加 `z_index` 的写法、`ValueTracker`、`MathTex` 的分段上色、`Brace`、`DashedLine`。
2. **快 5 倍左右**：第二遍 CE 18.3 s，ManimGX 3.6 s（它自己记的渲染时间是 3.0 s，其余是启动）；第一遍 CE 37.8 s（含 LaTeX 编译），ManimGX 3.7 s。README 的 90.6 倍和这里条件不同：60 fps 对 30 fps，最快的编码预设对两边各自的默认（ManimGX 是 CRF 23、medium），M4 Pro 对 M3 Max，场景也不同，所以两个倍数不能直接比。
3. **看得出是同一支片子，像素不一样**：全尺寸逐帧 PSNR 中位数 25.8 dB（最低 16.9）；480×270 的中位数 31.6 dB，其中画面在动的帧 27.5 dB（"在动"：CE 那一帧和它的前一帧，在 480×270 的 RGB 上平均每个通道差 0.5 以上，满分 255；750 帧里有 148 帧）。差别主要来自排版和描边：公式由 Typst 排，括号和省略号的字形、间距和 LaTeX 的不一样；曲线描边的抗锯齿不一样。时间上：每一帧在对方前后 12 帧里最像的那一帧，偏移的中位数是 0；各段 play 的起点（CE 的分段文件对 `manimgx inspect` 的时间表）相差不到半帧。但 16 s 处的同一帧上，CE 的计数到了 N = 15，ManimGX 是 13，差一档（图 8.1 第三行），原因没查出。
4. **文件要先整理，再进本仓库的流程**：ManimGX 写的是可变帧率的 MP4，画面不变的一段编成一个长帧（25 s 只有 482 帧，最后一帧长 2.63 s），而且在场景结尾多一帧（重定成 30 fps 是 751 帧，CE 是 750）；颜色是 BT.601 的矩阵，标 `smpte170m` 和 sRGB 原色。本仓库的工具各自这样对它：剪辑表拒收可变帧率的文件；`bin/vh mux` 直接拷贝视频流，不管帧率和色彩；`bin/vh check` 只对色彩标签给警告，不报可变帧率，帧数和时长按文件里的帧算（读成 482 帧、16.07 s）。按片长截、`fps=30`、BT.601 换成 BT.709 再打标签，用 ffmpeg 整理一遍（命令在 `engines/manimgx.md`）之后，`bin/vh check` 全过：750 帧、25.00 s、BT.709，报的提醒和 CE 版一样（开头的黑场、1–4 s 的静止）。整理前后 8 s 处的同一帧（两边各按自己的色彩标签解码成 RGB）是 44.9 dB。按时刻抽帧也要用整理过的那支：在原文件上 `-ss 24.5` 落在最后那个长帧里，抽不出画面。
5. **两遍渲出的帧逐字节相同**（解码后逐帧比 md5），在这台机器的 GPU 上。

![Manim CE（左）和 ManimGX（右）在 3、8、16、20 s](figs/08-ce-vs-gx.jpg)

图 8.1 · Manim CE 0.21（左）和 ManimGX 0.1.1（右）在 3、8、16、20 s。公式的字形和间距不同；16 s 处计数一边是 15、一边是 13。

## 因此改了什么

- `tools/modules.json` 登记 `manimgx`，钉 0.1.1，装成 uv 的工具；`bin/vh doctor` 报它在不在、是不是钉的版本（doctor 对程序也比钉的版本了，以前只比 npm 包）。
- 新的 `engines/manimgx.md`：怎么装、场景改哪几行、出片前怎么整理、时间和许可要注意什么；`engines/README.md` 的 Manim 一节加一行指过去（类型 01、06 每一档的读量因此多约 60 个字符）。
- 类型 01、06 的首选引擎不变。换不换由项目定，写进它的 `DECISIONS.md`。

## 还没弄清楚的

- 只比了一支 2D 片子。3D 场景、长片、带旁白的场景（它的 `self.say`）都没比。
- 16 s 处计数差一档的原因没查出：各段 play 的起点对得上。卡点要和旁白对齐的片子，换后端之后要重新核对时间。
- Linux 没有 GPU 时它用 lavapipe，速度和确定性没量。
- 许可：据它的 README 和 LICENSE-THIRD-PARTY，ManimGX 自己的代码是 MIT，原生 wheel 打包了 x264，整体按 GPL-3.0-or-later 发。本仓库的理解是：在本机装来出片不受影响，`import manimgx` 的场景调用的是它的 MIT 代码，可以照本仓库的 MIT 放；本仓库不承担 GPL 的义务，所以不带它的 wheel。这不是法律意见。

来源：本机实测，2026-10-29（showcase/03-math-fourier 的 `scenes/`，Manim CE 0.21.0 和 ManimGX 0.1.1；各段 play 起点的对照在 PR 评审时复测）；ManimGX 0.1.1 的 README（速度和 License 两节）、LICENSE-THIRD-PARTY 和 "Coming from Manim CE" 一页（manimgx.academa.ai）。
