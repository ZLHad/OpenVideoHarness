# 03 · 同一份代码，为什么渲出两份不同的像素

*记录于 2026-10-01 · 状态：已合并（[#17](https://github.com/ZLHad/OpenVideoHarness/pull/17)）；入库的样片媒体原来是 GPU 渲的版本，已在 [#31](https://github.com/ZLHad/OpenVideoHarness/pull/31) 里全部重渲 · [English](en/03-render-determinism.md)*

> **现状（2026-10-01）**
>
> - **落地**：修复已在 [#17](https://github.com/ZLHad/OpenVideoHarness/pull/17) 合并：[`styles/_swatch/render.sh`](../../styles/_swatch/render.sh) 的 `--no-browser-gpu` 和 `-threads 1`，以及改成严格比对的 [`styles/_swatch/determinism.sh`](../../styles/_swatch/determinism.sh)。之后 [#21](https://github.com/ZLHad/OpenVideoHarness/pull/21) 改了 `render.sh`（`profile=swatch` 混音、编码后的真峰值回路），这两项保留。
> - **混音一侧**：默认链的确定性是 [#15](https://github.com/ZLHad/OpenVideoHarness/pull/15) 修的；新的 profile 混音在 numpy 里做压低，信号链里没有 ffmpeg 滤镜，#21 里两次构建逐字节相同。
> - **媒体**：入库的样片媒体原来是 GPU 渲的版本；28 个样片按 CPU 全部重渲，已在 [#31](https://github.com/ZLHad/OpenVideoHarness/pull/31) 合并，现在入库的是 CPU 渲的版本。#31 还在最终链路上又验了 crt-terminal、ink-wash（`determinism.sh`，150/150 帧逐字节相同）和 blueprint（两次 `render.sh`，mp4 与海报逐字节相同）。
> - **和笔记里不同的**：#31 把新旧两版并排看过：看得出差别的是 ink-wash、synthwave-outrun、scratched-type 和 risograph（4.0–4.5 s 的粉版滑动，#17 没列）；cutout-jazz 和 halftone-comic 有变化但不易看出，其余样片新旧两版的 PSNR 在 37 dB 以上（编码级的差别）。也就是说，下面"局限"里点名的四个，risograph 取代了 cutout-jazz。

## 问题

样片的每一帧都是 `t` 的纯函数：没有随机数、没有时间、没有跨帧状态。为什么重渲一次，mp4 和海报却不一样？怎样才能逐字节相同？

## 做法

- **症状**：`styles/_swatch/render.sh <slug>` 重渲同一个样片，产物每次不同：halftone-comic 在 1.5 MB 的体积上限处，在 CRF 24（1.48 MB）和 CRF 26（1.31 MB）之间跳；fui-hud 每次一张新海报（互差约 44 dB）；guochao-festive 入库的海报与新渲的差 49.9 dB。
- **环境**：M3 Max（14 核）、HyperFrames 0.8.82、chrome-headless-shell 152。
- **比较方法**：先用 `--png` 渲无损 PNG 序列（150 帧），再逐帧逐像素比解码后的 RGB，不同的帧再用 ffmpeg 算 PSNR。mp4 和海报的比较用 `render.sh` 的真实输出，在样片文件夹的临时副本上跑。变量有三个：worker 数（1、2、3）、GPU 还是 CPU 光栅、x264 的线程数。
- **命令**：

```bash
styles/_swatch/determinism.sh <slug>        # 无损 PNG，1 个 worker 对 3 个 worker，逐帧比；bin/vh style check <slug> 等价
styles/_swatch/render.sh <slug> --workers 2 [--png]
ffmpeg -i a.png -i b.png -lavfi "[0:v]format=rgb24[a];[1:v]format=rgb24[b];[a][b]psnr" -f null -
```

来源：[#17 的描述](https://github.com/ZLHad/OpenVideoHarness/pull/17)（症状、环境、方法）；1 个 worker 对 3 个 worker 的比对，入库的就是 [`styles/_swatch/determinism.sh`](../../styles/_swatch/determinism.sh)。GPU 对 CPU 的比较（表里"GPU（修之前）"一列）用的是临时脚本，没有入库，修复之后 [`render.sh`](../../styles/_swatch/render.sh) 也不再有 GPU 路径；做法就是上面的逐帧 PSNR 命令。

## 发现

**1. 画面差得很小，但不是零，而且不是顺序的问题。** 修之前（GPU 光栅，`--use-angle=metal`）：

| 无损 PNG，150 帧 | GPU（修之前） | CPU（修之后） |
|---|---|---|
| halftone-comic，1 个 worker，重复 3 次 | 逐字节相同 | 逐字节相同 |
| halftone-comic，不同 worker 数的重复渲染 | 2 个 worker ×2 / 3 个 worker ×2：86 / 122 帧不同，标题字母边缘几十个像素差 1 个色阶，最差 73.7 dB（第 129 帧） | 1 个 ×2、3 个 ×2 加 `determinism.sh`：六次渲染 150/150 逐字节相同 |
| fui-hud，不同 worker 数的重复渲染 | 2 个 / 3 个 worker：第 22–23 帧不同，飞行中的帧计数器里 39–49 个像素差 1 个色阶 | 同上，六次渲染 150/150 逐字节相同 |
| 整条 `render.sh`，halftone-comic | 1 个 worker：CRF 24、1.48 MB；2 个 worker：CRF 26、1.31 MB；同样的 2 个 worker 跑两次，两次也不同 | `hf.mp4`、`poster.jpg`、`swatch.mp4` 在 1 个和 2 个 worker 下逐字节相同（CRF 26，1 341 164 B） |

3 个 worker 时 worker 0 每次都按同样的顺序画第 0–49 帧，这些帧仍然不同，所以不是渲染历史；单进程渲三次逐字节相同，所以也不是 Chrome 的 canvas 读回噪声（那是 ClaudeAnimationBase 的另一个问题，见下）。原因是 GPU 上 2D canvas 的文字边缘光栅化，在不同的 Chrome 进程里不可重复。

![halftone-comic 的 150 帧：GPU 对 GPU、GPU 对 CPU、CPU 对 CPU 三种比较的逐帧 PSNR](figs/03-psnr-per-frame.zh.png)

*图 1 · 三种比较的逐帧 PSNR：蓝是 GPU 对 GPU（122 帧不同，73.7–105.3 dB），橙是 GPU 对 CPU（150 帧全不同，33.5–43.6 dB），绿是 CPU 对 CPU（全部逐字节相同）。*

**2. 三个互相独立的来源。** (a) 上面说的 GPU 文字光栅化。(b) 截帧路径随 worker 数变：HyperFrames 给 1 个 worker 用 `drawElement` 加 `toDataURL`，给 2 个以上用 `Page.captureScreenshot`，两条路差约 80 dB，而 `render.sh` 会看机器上有没有别的 `hyperframes render` 在跑，来选 1 个还是 2 个 worker。(c) x264：带 `-maxrate`/`-bufsize`（VBV）和帧线程时，同一个 `hf.mp4` 加同一条音轨编四次，体积是 1 493 473、1 495 461、1 497 684、1 503 291 B，正好跨着 1 500 000 B 的上限，于是 CRF 循环在 24 和 26 之间跳；`-threads 1` 时三次都是 1 593 576 B，逐字节相同。

![同一个 hf.mp4 和音轨编多次：带帧线程的四次大小跨在上限两侧，单线程三次完全相同](figs/03-x264-size-vs-cap.zh.png)

*图 2 · x264 的体积实验（CRF 24，上限 1 500 000 B）：左，帧线程加 VBV，四次四个不同的文件；右，`-threads 1`，三次相同，总超出上限，CRF 循环每次都升到 26。*

**3. 编码把几个像素放大成整条码流的差别。** 无损帧至少 73 dB 才分开，编成 mp4 之后，两次 2 个 worker 的 halftone-comic 有 122/150 帧的 `hf.mp4` 不同、海报差 34.7 dB；fui-hud 是 129/150 帧、海报差 43.9 dB。

**4. 检查本身把它放过了。** 旧的 `determinism.sh` 用"最差帧 ≥ 45 dB 就算过"（硬规则 1 给 GPU 光栅留的余地）：halftone-comic 最差 73.7 dB，照样通过。有一轮在九个样片上跑（GPU）：七个 150/150 相同，halftone-comic 只有 28 帧相同，risograph 139 帧相同（最差 92.4 dB）。现在 `determinism.sh` 改成只要有一帧不同就失败。

**5. 代价：画面变了一次，渲染慢了一些。** 切到 CPU 后每个样片的画面变一次（每帧 PSNR，GPU 渲的对 CPU 渲的）：

| 样片 | 中位数 | 最差（帧号） | 海报帧 | 变了什么 |
|---|---|---|---|---|
| pixel-16bit | 相同 | — | 相同 | 无（整数像素画） |
| crt-terminal | 77.8 dB | 72.0（123） | 74.7 | 着色器边缘的几个像素 |
| fui-hud | 52.5 | 41.0（22） | 50.8 | 文字和线条的抗锯齿 |
| guochao-festive | 51.5 | 39.3（127） | 49.1 | 同上 |
| symmetry-pastel | 48.4 | 29.6（125） | 46.6 | 甩动的拖影（子帧采样） |
| ink-wash | 46.6 | 20.2（124） | 47.3 | 洇墨轮廓：CPU 的 `feTurbulence` 噪声不同，并排看得出 |
| cutout-jazz | 46.4 | 41.2（121） | 45.6 | 毛边：同上 |
| archival-pan-zoom | 43.3 | 40.5（23） | 43.4 | 颗粒和模糊的抗锯齿 |
| halftone-comic | 36.4 | 33.5（61） | 36.2 | 每个网点边缘和文字；放大 2 倍看不出 |

PNG 序列（1 个 / 3 个 worker）：halftone-comic 22 s / 13 s（GPU 是 17 / 11），fui-hud 31 / 14（10 / 6）；整条 `render.sh` 在 CPU 上 20–50 s，GPU 上 13–19 s。

![halftone-comic 第 61 帧：GPU 渲的、CPU 渲的，和放大 8 倍的差](figs/03-gpu-cpu-diff.png)

*图 3 · 同一帧分别用 GPU 和 CPU 渲，再加两者之差放大 8 倍（halftone-comic 第 61 帧，33.5 dB）：差别在字母轮廓和每个网点的边缘。*

**6. 音频里有同类问题。** ffmpeg 8.0.1 的 `sidechaincompress` 在主输入的帧用完时就结束输出，丢掉侧链队列里还没配上的音乐；音乐和侧链来自不同的解码线程，丢多少每次不同。同一条 `bin/vh mix` 命令跑 12 次得到 6 种不同的文件，最差的一个在 25.3–26.0 s 之间是数字静音。修法是把各总线补齐到同样长度、让压缩器的两路输入来自同一条流，之后 12 次只有 1 种结果（[#15](https://github.com/ZLHad/OpenVideoHarness/pull/15)）。

来源：[#17 的描述](https://github.com/ZLHad/OpenVideoHarness/pull/17)（表格、x264 四次的体积、PSNR、时间）；九个样片那一轮（GPU）的比对输出、图 1 的逐帧 PSNR 日志（halftone-comic）和图 3 的放大图，都是当时留下的本地文件，没有入库；[#15 的描述](https://github.com/ZLHad/OpenVideoHarness/pull/15)（第 6 点）。

## 因此改了什么

- [#17](https://github.com/ZLHad/OpenVideoHarness/pull/17)：[`styles/_swatch/render.sh`](../../styles/_swatch/render.sh) 给 `hyperframes render` 加 `--no-browser-gpu`（HyperFrames 文档里的确定性模式：SwiftShader 渲 WebGL，2D canvas 和合成都在 CPU 上，截帧路径不再随 worker 数变），`swatch.mp4` 的 x264 编码加 `-threads 1`（码率模型不变，每次同样的字节，720p 一遍约 3 s）；[`styles/_swatch/determinism.sh`](../../styles/_swatch/determinism.sh) 改为严格比对，失败信息指向日志里的 `gl=` 一行；[`styles/_swatch/README.md`](../../styles/_swatch/README.md) 和 [`playbook/02-verification.md`](../../playbook/02-verification.md) 写清了原因。
- 独立复核的结论（写在 #17 里）：28 个样片在 1 个和 3 个 worker 下的 PNG 序列逐字节相同，整条渲染的 mp4 和海报也逐字节相同。
- [#15](https://github.com/ZLHad/OpenVideoHarness/pull/15)：`bin/vh mix` 确定。混音的新 profile（[#21](https://github.com/ZLHad/OpenVideoHarness/pull/21)）用 numpy 做压低，信号链里没有 ffmpeg 滤镜，两次构建的 sha256 相同（见[笔记 01](01-mix-hierarchy.md)）。
- 更早的一例是另一个原因：[#1](https://github.com/ZLHad/OpenVideoHarness/pull/1) 里 ClaudeAnimationBase 在 `--soft-gl` 下每次启动帧相差约 39 dB，主因是 Chrome 的 canvas 读回噪声，关掉后逐像素相同；[#2](https://github.com/ZLHad/OpenVideoHarness/pull/2) 在带 Metal 的 Mac 上验证了。

来源：PR #1、#2、#15、#17、#21 的描述；profile 混音的信号链里没有 ffmpeg 滤镜，见 [`tools/audio/mix.py`](../../tools/audio/mix.py) 的文件头；两次构建 sha256 相同，记录在 #21 的描述里。

## 局限与没解决的

- **一台机器、一个版本**：M3 Max、HyperFrames 0.8.82。CPU 路径在这里跨 worker 数和重复运行都逐字节相同，跨机器、跨操作系统没验证。
- **根因只到"GPU 文字光栅不可重复"**：没有深入到 ANGLE/Metal 里哪一步不可重复，也没试别的 Chrome 版本。
- **画面一次性变了**：ink-wash、cutout-jazz（`feTurbulence`）、scratched-type（字形骨架是从渲染出来的文字里描的）、synthwave-outrun（GLSL 颗粒和 VHS 错位）四个并排看得出，入库的媒体要全部重渲（在重写配乐的分支上做；后来是 [#31](https://github.com/ZLHad/OpenVideoHarness/pull/31)，并排看的结果见"现状"）。
- **硬规则 1 的 45 dB 余地还在**：对无法做到逐字节相同的引擎（例如介绍片的 Three.js 场景：v3 的无损帧里 2040/2440 帧逐比特相同，最低 80.7 dB），它仍是可用的判据；但 x264 会放大差异，比较要在无损帧上做，不能拿 mp4。
- `-threads 1` 的 x264 在不同 x264 版本之间是否仍逐字节相同，没测。

来源：[#17 的描述](https://github.com/ZLHad/OpenVideoHarness/pull/17)；介绍片 v3 那一轮（2040/2440 帧逐比特相同、最低 80.7 dB）来自介绍片修订方案里的核对，方案没有入库（见[笔记 04](04-readability.md)）；做法见 [`playbook/02-verification.md`](../../playbook/02-verification.md) 的"确定性：比无损帧，不比 mp4"一节，那里引的是另一轮：v3 的 1 个和 3 个 worker 的无损帧，最低 PSNR 60–92 dB。
