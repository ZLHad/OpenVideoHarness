# ManimGX：Manim 场景的可选后端

[ManimGX](https://github.com/academa-labs/manimgx) 照 Manim CE 的 Python API 写场景，内核是 Rust 和 wgpu（macOS 上走 Metal；Linux 没有 GPU 时用 wheel 里带的 Mesa lavapipe），`MathTex` 由 Typst 排，不用装 LaTeX，编码器自带。本仓库钉 0.1.1，要 Python 3.13+，装成 uv 的工具，不进项目自己的环境；`bin/vh doctor` 报它在不在、是不是钉的版本。

它是可选的：类型 01、06 的首选仍是 Manim CE（`engines/README.md` 的 Manim 一节）。换不换由项目定，写进它的 `DECISIONS.md`。showcase 03 换过去以后，在一台 M3 Max 上快约 5 倍，看得出是同一支片子，但像素不同（`docs/research/08-manimgx.md`）。

## 装和跑

```bash
uv tool install --python 3.13 manimgx==0.1.1    # 装进 ~/.local/bin
manimgx inspect scenes/scene.py MyScene         # 不出视频：每段 play 的时间表、2D 版面检查和分镜图
manimgx render scenes/scene.py MyScene -r 1920x1080 --fps 30 -o out/gx.mp4   # 默认 60 fps；草稿 -r 1280x720
```

- `~/.local/bin` 要在 PATH 里，`manimgx` 才找得到（uv 装完会提醒）；不在时 `bin/vh doctor` 报 not found。机器上没有 Python 3.13 时，uv 会自己下载一个 CPython 3.13。
- 钉的只是 manimgx 本身，它的依赖（numpy、pillow 等）不钉，什么时候装，就是那时的版本。
- `inspect` 把分镜图（`<Scene>.storyboard*.png`）写在场景文件旁边，`render` 写在视频旁边：场景放在项目的 `scenes/` 里，用完删掉，或者别提交。
- `render` 默认 CRF 23、preset medium（`--crf`、`--preset` 可改）。下面的整理还要再编一次，两次都有损，要发布的片子在 render 时就给低一点的 `--crf`。

## 场景改几处

- 场景和它的辅助模块里，每一处 `from manim import …` 都换成 `from manimgx import …`。showcase 03 有两处：`fourier.py` 的星号导入，`style.py` 的 `from manim import VMobject, ManimColor, config`。
- 它导出一个叫 `Path` 的图形类，会盖掉先导入的 `pathlib.Path`：要用 pathlib，就在星号导入之后再导一次。
- `rate_functions.xxx` 写成顶层的 `xxx`（没有 `rate_functions` 这个模块）。
- 0.1.1 的星号导入会把 `np` 一起带出来；建议照旧显式 `import numpy as np`，但不是必需。
- 其余差别看它的 [Coming from Manim CE](https://manimgx.academa.ai/user-guide/coming-from-manim-ce/)：没有 `-ql`、`-qh`，用 `-r` 和 `--fps`；`Tex`、`MathTex` 转成 Typst，LaTeX 的宏包和 `\def` 转不过去；竖屏时画面的短边是 8 个单位（CE 是 4.5 宽）。

## 出片前整理一遍

它写的是可变帧率的 MP4：画面不变的一段编成一个长帧，结尾多一帧（场景结束那一刻），颜色是 BT.601 矩阵，标 `smpte170m`。本仓库的工具各自这样对它：

- 剪辑表（`edit.json`）拒收可变帧率的文件；
- `bin/vh mux` 直接拷贝视频流，不管帧率和色彩，没整理的文件原样进成片；
- `bin/vh check` 报出可变帧率，时长按视频流自己的长度算，不再是帧数除以标称帧率（以前 showcase 03 的 25 s 读成 482 帧、16.07 s），色彩标签也报警告；它只报，不改文件。

所以先整理一遍再进流程：按片长截（`-t` 后面写场景的秒数），换成 30 fps 和 BT.709：

```bash
ffmpeg -i out/gx.mp4 -t 25 -vf "fps=30,scale=in_color_matrix=bt601:in_range=tv:out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
  -c:v libx264 -crf 16 -preset medium -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 out/final.mp4
```

按时刻抽帧、做联系表也用整理过的这支：原文件上的 `-ss` 会落进长帧里，抽不出画面。

## 时间

showcase 03 上，各段 play 的起点和 CE 相差不到半帧；但 16 s 处同一帧上，CE 的计数是 N = 15，ManimGX 是 13，差一档，原因没查出。卡点要和旁白、配乐对齐的片子，换后端之后重新核对（`bin/vh check` 的切点，`bin/vh cues`）。同一台机器上渲两遍，帧逐字节相同。

## 许可

出处是 ManimGX 的 README（License 一节）和它随轮子发的 LICENSE-THIRD-PARTY：它自己的代码是 MIT；原生轮子打包了 x264（GPL-2.0-or-later），所以轮子整体按 GPL-3.0-or-later 发。下面是本仓库的理解，不是法律意见：

- 在本机装来出片不受影响，渲出的画面归你（Blender 一项也是这样理解的）；
- `import manimgx` 的场景调用的是 ManimGX 自己的 MIT 代码，场景文件可以照本仓库的 MIT 放在项目里；
- 本仓库不承担 GPL 的义务，所以不带它的轮子；要再分发轮子的人照 GPL 的条款办（它每个 release 都附源码包）。
