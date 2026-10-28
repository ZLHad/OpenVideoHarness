# ManimGX：Manim 场景的可选后端

[ManimGX](https://github.com/academa-labs/manimgx) 照 Manim CE 的 Python API 写场景，内核是 Rust 和 wgpu（macOS 上走 Metal；Linux 没有 GPU 时用 wheel 里带的 Mesa lavapipe），`MathTex` 由 Typst 排，不用装 LaTeX，编码器自带。本仓库钉 0.1.1，要 Python 3.13+，装成 uv 的工具，不进项目自己的环境；`bin/vh doctor` 报它在不在、是不是钉的版本。

它是可选的：类型 01、06 的首选仍是 Manim CE（`engines/README.md` 的 Manim 一节）。换不换由项目定，写进它的 `DECISIONS.md`。实测 showcase 03 快约 5 倍，看得出是同一支片子，但像素不同，几段数值动画差几帧（`docs/research/08-manimgx.md`）。

## 装和跑

```bash
uv tool install --python 3.13 manimgx==0.1.1    # manimgx 进 PATH
manimgx inspect scenes/scene.py MyScene         # 不出视频：每段 play 的时间表、2D 版面检查和分镜图
manimgx render scenes/scene.py MyScene -r 1920x1080 --fps 30 -o out/gx.mp4   # 默认 60 fps；草稿 -r 1280x720；视频旁边还写分镜图
```

## 场景改几行

- `from manim import *` 换成 `from manimgx import *`；numpy 自己 `import numpy as np`（它的星号导入不带）。
- 它导出一个叫 `Path` 的图形类，会盖掉先导入的 `pathlib.Path`：要用 pathlib，就在星号导入之后再导一次。
- `rate_functions.xxx` 写成顶层的 `xxx`（没有 `rate_functions` 这个模块）。
- 其余差别看它的 [Coming from Manim CE](https://manimgx.academa.ai/user-guide/coming-from-manim-ce/)：没有 `-ql`、`-qh`，用 `-r` 和 `--fps`；`Tex`、`MathTex` 转成 Typst，LaTeX 的宏包和 `\def` 转不过去；竖屏时画面的短边是 8 个单位（CE 是 4.5 宽）。

## 出片前整理一遍

它写的是可变帧率的 MP4：画面不变的一段编成一个长帧，结尾多一帧（场景结束那一刻），颜色是 BT.601 矩阵，标 `smpte170m`。`bin/vh check`、`mux` 和剪辑表都要恒定帧率和 BT.709 的四个标签，所以按片长截（`-t` 后面写场景的秒数），换成 30 fps 和 BT.709：

```bash
ffmpeg -i out/gx.mp4 -t 25 -vf "fps=30,scale=in_color_matrix=bt601:in_range=tv:out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
  -c:v libx264 -crf 16 -preset medium -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 out/final.mp4
```

按时刻抽帧、做联系表也用整理过的这支：原文件上的 `-ss` 会落进长帧里，抽不出画面。

## 时间

CE 把每段 play 的时长取整到帧，ManimGX 按精确时刻画每一帧，一串短 play 之后两边的落点会差几帧。卡点要和旁白、配乐对齐的片子，换后端之后重新核对（`bin/vh check` 的切点，`bin/vh cues`）。同一台机器上渲两遍，帧逐字节相同。

## 许可

ManimGX 自己的代码是 MIT；原生 wheel 带着 x264，整体按 GPL-3.0-or-later 发（它的 README 和 LICENSE-THIRD-PARTY）。在本机装来出片不受影响，不要把它的 wheel 放进仓库或随项目分发。
