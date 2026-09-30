# Blender 引擎指南（实验性）

> **实验性（experimental）：本指南没有在本机验证过（not yet verified on this machine）。本机没有装 Blender**，下面所有 Blender 命令、API 和数字都来自官方文档、release notes 和 issue，没有在本机跑过。ffmpeg、色彩、alpha、EXR 和 `sandbox-exec` 相关的结论在本机跑过，标【本机实测】。**渲染时间只是推算：开工前先渲 5 帧校准，把结果写进 BRIEF**（见"渲染时间"）。
>
> 标记：【本机实测】自己跑过；【二手】只读到搜索摘要或第三方转述，没能打开原文；【推测】没有证据的推断。引用编号 `[n]` 见文末"来源"。本机是 Apple M3 Max、36 GB、macOS 15、ffmpeg 8.0.1。命令里的 `bin/vh` 子命令（blender 的 doctor / build / render 等）**尚未实现**，下文写的都是直接调用 `blender` 的做法。
>
> 首次在本机装上 Blender 之后，先做"待验证"一节里的冒烟项，把结果写回本文，再去掉这段警告。

## 要点

1. **路线**：`blender -b` 两段式：`build`（`timeline.json` → `scene.blend`）和 `render`（`scene.blend` → PNG 序列）。合成走 HyperFrames 或 ffmpeg。MCP 只在"探索"阶段用，不进管线，而且只在沙箱里用。
2. **版本**：固定 **5.2 LTS**（2026-07-14 发布，维护到 2028-07；最新点版本 5.2.2，2026-09-15）[1][2a]。5.0 起只支持 Apple Silicon，macOS ≥ 13 [3]。5.0 对 Python API 做了破坏性改动（EEVEE 引擎 id、compositor 节点树、Action 和 F-Curve 等），凭 2.8–4.x 的记忆写的脚本多半会报错（见"5.0 起的 Python API 破坏性改动"）。
3. **引擎分工**：分镜和 draft 用 EEVEE（或 Workbench），final 用 Cycles（Metal）加 OIDN；风格化镜头可以直接 EEVEE final。渲染时间只有推算，开工前必须在本机渲 5 帧校准。
4. **确定性**：只承诺"同一台机器、同一 Blender 构建、同一设置"下，按硬规则 1 的口径（无损 PNG，PSNR ≥ 45 dB）乱序渲染一致。跨设备不保证，OIDN 官方文档明说设备之间会有数值差异 [10]。所以**渲好的 PNG 序列是带哈希的素材（产物），合成时不重渲**。
5. **纯函数**：时间线用我们自己的缓动、样条和节拍函数，逐帧采样写成关键帧；不用 Python handler，不靠 live simulation。物理分三级：解析式、烘焙成关键帧、缓存当素材。
6. **合成**：默认交 PNG（straight alpha，视图变换已烘进去）。EXR 是 scene-linear、premultiplied、不带 AgX 这类 look，进 ffmpeg 必须显式 `-apply_trc iec61966_2_1`。最后一步 YUV 编码不写 BT.709 矩阵，饱和色会偏 20 个色阶左右。
7. **安全**：官方 MCP 自己在页面上警告：它会直接执行 LLM 生成的代码，没有任何防护 [16]。**不要把 LLM 生成的 bpy 代码交给任何 MCP 直接执行，除非在沙箱里**；管线里跑 agent 写的脚本同理，默认加静态检查和 `sandbox-exec`。
8. **许可证**：输出归自己；但 Blender 明确要求公开发布的、调用 bpy 的 Python 脚本要以 GPL 兼容协议发布 [17]。仓库是 MIT，`engines/blender/` 里放 bpy 脚本要怎么写，**维护者待定**（见"许可证"）。
9. **什么时候不用 Blender**：样板 `showcase/04-intro-film` 已经用 HyperFrames + Three.js 做了 3D 世界、产品光影甚至 SDF ray-marcher。Blender 的增量只在路径追踪的光传输（玻璃、SSS、焦散、体积）、物理模拟、真实运动模糊和景深、导入真实 3D 资产这几件事上。

## 什么时候用 Blender

| 需求 | 首选 | 原因 |
|---|---|---|
| 3D 世界里的文字、节点标签、UI，一镜到底 | HyperFrames + Three.js | 文字和相机是同一份代码，实时；样板已有（`showcase/04-intro-film`） |
| 玻璃、水、皮肤（SSS）、焦散、体积光的产品镜头 | Blender（Cycles） | 路径追踪的光传输 |
| 布料、液体、烟 | Blender + 烘焙（缓存当素材） | Three.js 没有 |
| 非写实的 3D（toon、平涂、线稿） | Three.js 或 Blender（EEVEE） | 看有没有模型、要不要真运动模糊和景深 |
| 公式曲面、向量场、几何对象 | Manim 的 `ThreeDScene` | 精确 |
| 超过 30 秒、4K、大量镜头 | 先算渲染账 | 见"渲染时间" |

reviewer 看 3D 镜头时，额外给它"为什么这个镜头需要 Blender（一句话）"；说不出来，就降级成 Three.js 或 2D（借用 `playbook/08` 的原则 1）。

## 版本与安装

| 版本 | 发布日期 | 与我们相关的点 |
|---|---|---|
| 4.5 LTS | 2025-07-15 | 最后支持 Intel Mac 的版本 [1][3] |
| 5.0 | 2025-11-18 | 要求 Apple Silicon，macOS ≥ 13（2026-10-01 核对）；新增 ACES 1.3/2.0 与 AgX HDR 视图、可选工作色彩空间（Linear Rec.709 / Rec.2020 / ACEScg）；Python API 破坏性改动 [1][3][4] |
| 5.1 | 2026-03-17 | `bpy` 轮子从 cp311 换到 cp313；官方 MCP 要求 5.1+ [1][18][16] |
| **5.2 LTS** | **2026-07-14**（2026-10-01 核对） | LTS 到 2028-07；EEVEE 大改（实例化最多 2 倍速、Fast GI 修复）；Cycles 纹理缓存；后台模式新增 `gpu.init()`（2026-10-01 核对）[2][4] |

- **安装**：`brew install --cask blender`。Homebrew 的 cask 现在是 5.2.2，装到 `/Applications/Blender.app`，并把 `blender` 链到 `$(brew --prefix)/bin/blender` [18]。macOS arm64 的 dmg 约 346 MB [2a]。cask 永远跟最新版走；要钉住点版本，就从 download.blender.org 取固定文件（`…/release/Blender5.2/blender-5.2.2-macos-arm64.dmg`，目录里 5.2.0、5.2.1、5.2.2 都在）并记下 sha256 [2a]：Homebrew 元数据里 5.2.2 的 sha256 是 `dc4125399b8bfefe283cc1624d6cfc7809d1cac20ace51072127eb371f31f210`（2026-10-01 取自 cask 的 JSON）[18]。没有核对过 cask 是否提供旧版本【推测】。
- **`bpy` 模块**：PyPI 上 5.0.x 是 cp311，5.1.x、5.2.x 是 cp313，都有 `macosx_11_0_arm64` 轮子 [18]。本机默认 Python 是 3.14，要用 `uv venv --python 3.13`。取舍：模块方式可以在常驻 worker 里复用进程，但参数顺序、`-f` 列表、`--cycles-device` 这些官方文档描述的行为都是 CLI 的，**默认走 `blender -b`**，模块只留给单元测试。
- **固定环境**：`blender.lock` 记录 `bpy.app.version_string`、`bpy.app.build_hash`、设备类型、预设名、OIDN 开关。5.2 的 EEVEE 做了能量守恒修复，release notes 提示部分场景会比 5.1 更暗 [4]，版本之间输出本来就不一致。
- **`bin/vh doctor` 将来可以加的检查**（尚未实现）：`blender --version`；`blender -b --factory-startup --python-expr "import bpy; print(bpy.app.version_string)"`；一张 64×64、1 spp 的 Cycles 场景用 `-- --cycles-device METAL` 渲一次，日志里应出现 Metal 设备名【推测：具体日志措辞没见过】。

## 两段式：build → render

### 目录与产物

```
projects/<date>-<slug>/blender/
├── timeline.json        # 唯一事实来源，单位秒
├── assets/              # glb/usd/blend/HDRI；每件在 NOTES.md 素材台账有来源、许可、sha256
├── build/scene.blend    # build 的产物，可删可重建
├── caches/              # 烘焙缓存（关键帧 JSON、点缓存/Alembic/VDB），带 sha256
├── out/draft/ out/plate/ out/alpha/    # PNG 序列
└── blender.lock         # version, build_hash, device, preset, denoiser, seed
```

### timeline.json（最小 schema）

```json
{
  "schema": "vh-blender-timeline/1",
  "fps": 30, "duration": 8.0, "resolution": [1920, 1080], "seed": 20261001,
  "look": { "view_transform": "Khronos PBR Neutral", "display": "sRGB", "exposure": 0.0 },
  "camera": { "fov_deg": 35, "path": [
    { "t": 0.0, "pos": [0, -6, 1.6], "look_at": [0, 0, 1.0] },
    { "t": 3.0, "pos": [2.5, -4, 1.4], "look_at": [0, 0, 1.0], "ease": "inOutCubic" } ] },
  "objects": [ { "id": "product", "asset": "assets/product.glb",
                 "xform": [ { "t": 0, "rot_z_deg": 0 }, { "t": 8, "rot_z_deg": 360 } ] } ],
  "lights":  [ { "id": "key", "type": "AREA", "size": 2.0, "energy": 600, "pos": [3, -3, 4], "color": "#fff4e5" } ],
  "events":  "audio/music.beats.json"
}
```

`events` 指向节拍表，`build` 按 `beats`、`hits` 给发光强度、镜头冲击之类的量采样，做法和 `playbook/08` 的 `k = exp(-(t-beat)/0.12)` 相同，不手填时间。

### build 阶段的规则

- 命令：`blender -b --factory-startup --python-exit-code 1 -noaudio --python lib/build.py -- timeline.json build/scene.blend`。Blender 的参数按给出顺序执行，先读文件再改设置 [5]。命令没有在本机跑过。
- 从 `bpy.ops.wm.read_factory_settings(use_empty=True)` 开始，不读用户偏好和启动场景。
- `frame_start = 0`；每帧采样关键帧；不写 fcurve；不注册 handler（见"每帧是 t 的纯函数"）。
- Cycles：`seed` 取自 timeline，`use_animated_seed = True`，`time_limit = 0`；降噪器按预设；不写 `METAL+CPU`（见"确定性"）。
- 视图变换和显示设备来自 `look`；枚举值以当前版本 `view_settings.bl_rna.properties['view_transform'].enum_items` 为准，不凭记忆写字符串（5.x 名称有变化：Filmic 已弃用，新增 ACES）[7][4]。
- 引擎 id 按版本选（`BLENDER_EEVEE` / `BLENDER_EEVEE_NEXT`），用 `bpy.app.version` 门控。
- 物理按三级选法；烘焙和缓存的产物写进 `caches/` 并登记哈希。
- 导入资产之后立刻写素材台账（来源、许可、sha256）。
- `lib/` 里提供一层 API shim 和一条 5 帧冒烟测试，版本升级时先跑冒烟。

骨架只写流程，不放可运行的 bpy 脚本（许可问题见"许可证"，维护者待定）。循环的做法是：

```text
对每一帧 n，从 frame_start 到 frame_end：
    t = n / fps
    (pos, look) = 相机路径在 t 的值     # 我们自己的样条和缓动，与 HyperFrames 同一实现
    相机的位置和旋转 = pos，以及由 look 算出的朝向
    对相机的位置和旋转各打一个关键帧，帧号 = n     # bpy 里是 keyframe_insert(frame=n)
```

### 渲染预设

数值是起点，全部【推测】，以 5 帧校准为准。

| 预设 | 引擎 | 关键设置 | 用途 |
|---|---|---|---|
| `draft` | EEVEE | 分辨率 50%，其余默认 | 分镜、animatic、联系表 |
| `final` | Cycles，Metal | 96–256 spp，OIDN 高质量，关自适应，`time_limit=0`，间接光 clamp | 定稿底片 |
| `final-eevee` | EEVEE | 100% 分辨率，采样按画质 | 风格化镜头 |
| `alpha` | 同 `final` | `film_transparent=True`，`color_mode=RGBA`，PNG 16 位 | 带 alpha 的合成路径 |

### render 阶段的命令

命令行顺序按官方手册：`-f`、`-a` 放最后，Cycles 选项在 `--` 之后 [5]。`-o` 里的 `//` 是 `.blend` 所在的目录，这里是 `build/`，所以输出要写 `//../out/…` 才落在 `out/` 下。没有在本机跑过。

```bash
# 分块渲染，可续跑；一个进程一块
blender -b build/scene.blend -E CYCLES -o //../out/plate/f_#### -F PNG -s 0 -e 59 -a -- --cycles-device METAL --cycles-print-stats
# 抽帧（联系表用）：-f 接逗号列表或 a..b
blender -b build/scene.blend -E BLENDER_EEVEE -o //../out/draft/f_#### -F PNG -f 0,60,120,180
```

将来的 render 封装（尚未实现）应该带看门狗（沿用 `playbook/02` 的做法）、检查退出码、核对帧数和每帧 YAVG、按块记录墙钟时间。

### 已知的坑

- 参数按给出的顺序执行，顺序错了设置会被静默忽略（手册的警告，`-f`、`-a` 必须放最后）[5]。
- `-o` 里的 `//` 相对 `.blend`；不含 `#` 时自动补 `####`。
- 5.x API 破坏性改动（下一节）。
- EEVEE 命令行渲染在 4.2 的内存问题（见"Metal 上的 Cycles 与 EEVEE"）：分块。
- `Time Limit`、自适应采样、跨设备（见"确定性"）。
- 颜色三件事：视图变换、YUV 矩阵、alpha（见"合成"）。
- LLM 生成代码的安全（见"安全"）。

## 5.0 起的 Python API 破坏性改动

模型凭记忆写的 2.8–4.x 脚本多半会在这里出错。下面这些都对着 5.0 的 release notes 原文核对过（2026-10-01）[4]：

| 旧 | 5.0 起 |
|---|---|
| 渲染引擎 id `BLENDER_EEVEE_NEXT` | `BLENDER_EEVEE` |
| `scene.node_tree`（合成器节点树） | 已删除，改用 `scene.compositing_node_group`；`scene.use_nodes` 已弃用（6.0 删除） |
| File Output 节点的 `file_slots`、`layer_slots`、`base_path` | 已删除，改用 `directory`、`file_name`、`file_output_items` |
| `ImageFormatSettings`：直接设 `file_format` | 要**先**设 `media_type`，再设 `file_format` |
| 渲染通道名 `DiffCol`、`Z` 等缩写 | 改成全称：`Diffuse Color`、`Depth` 等 |
| `Action.fcurves`、`Action.groups`、`Action.id_root`（旧 Action API） | 已删除，要走每个 slot 的 channelbag |

所以只用 `keyframe_insert`，不去改 fcurve 的插值类型。另外要核对：引擎 id、视图变换枚举、通道名都用 `bpy.app.version` 门控或枚举查询，不写死字符串。

## 每帧是 t 的纯函数：关键帧与物理

**映射**：`scene.frame_start = 0`，帧 n 对应 t = n / fps；`render.fps = fps`，`fps_base = 1`。从 0 开始，不要用默认的 1，省去一个差一帧的坑。

**关键帧，不要 handler**：时间线 JSON 里的相机路径、物体变换、灯光、材质参数，用我们自己的缓动、样条、节拍函数（和 HyperFrames 里同一套）**每帧采样一次**，用 `keyframe_insert(frame=n)` 写进去。理由：Blender 的运动模糊是在快门区间内对动画曲线做子帧插值，`frame_change` handler 不会在每个子帧里被调用【推测：Cycles 运动模糊读的是求值后的动画系统】，用 handler 驱动的运动没有运动模糊。逐帧密采样加默认的 Bezier 插值，整数帧上的值精确等于我们的函数，子帧上平滑。

**物理，三级选法**

| 级别 | 做法 | 什么时候选 | 状态 |
|---|---|---|---|
| L0 解析式 | 用公式算：弹跳、阻尼弹簧、轨道、齿轮（转角 = 齿数比 × 主动轮角度）。写成 t 的函数再采样成关键帧 | 默认。大多数"看起来有物理"的镜头够用 | 纯函数 |
| L1 烘焙成关键帧 | 刚体模拟一次，`bpy.ops.rigidbody.bake_to_keyframes(frame_start, frame_end, step)` 转成关键帧，再删掉 rigid body world，渲染时不再有状态 [14] | 需要碰撞、堆叠、倒塌 | 烘焙后是纯函数；烘焙本身跨机器是否一致【推测：否】，所以把烘出的关键帧 JSON 入项目并记哈希 |
| L2 缓存当素材 | 布料、软体、流体、烟、毛发：烘焙到磁盘（point cache、Alembic、VDB），渲染只按帧读缓存 | 必须要这类效果时 | 缓存文件带 sha256 进素材台账，换种子或参数才重烘。**乱序渲染烘焙缓存要单独测**：有 issue 说烘焙过的刚体缓存在乱序渲染时行为异常【二手】[14] |

不要用：渲染时现算的模拟；没烘焙的粒子系统；没烘焙的 Geometry Nodes Simulation zone；带状态的 `frame_change` handler；`bpy.app.timers`。

## 确定性：种子、采样数、降噪

官方手册说明 `Seed` 决定噪声图案，`Animated Seed` 让种子逐帧变化，动画里推荐开，因为变化的噪声不那么显眼 [6]。种子随帧变化，机制应是按帧号偏移【推测：手册没写实现】，这样画面仍是（帧号, seed）的纯函数。

| 来源 | 影响 | 对策 |
|---|---|---|
| Cycles `Time Limit` | 到时限就停，哪怕没到目标采样数 [6]，结果随机器速度变化 | 固定为 0（关） |
| 自适应采样 | 像素是否停止取决于噪声估计。同设备是否逐位一致【推测：没找到官方说法】 | final 预设默认关自适应，固定 spp；要开就先做下面的验收 |
| 设备 | 同一场景在 CPU、CUDA、OptiX 上渲出的像素不同（#101561）；Cycles 开发者 Brecht Van Lommel 回复：不同设备之间总会有差异，不算 bug，归因于硬件精度差异；提问者的结论是最终片不要混用不同的计算方式 [12] | 一个项目只用一种设备（Metal）；不用 `METAL+CPU` |
| OIDN 降噪 | 官方文档称不同设备之间可能有小的数值差异，非高质量模式差异更大；RT 滤波器不具备时间稳定性 [10] | final 用默认（高质量）模式；降噪是逐帧的，可能闪，见下 |
| 版本 | 5.2 EEVEE 输出与 5.1 不同 [4] | `blender.lock` 钉死 |
| 模拟与缓存 | 见"每帧是 t 的纯函数" | 缓存当素材 |
| Python | `random`、时间、`os.urandom` 会破坏纯函数 | 用带种子的 `hash(name, i)`，和硬规则 1 一致 |
| 文件哈希 | PNG 元数据可能含渲染时间等字段【推测】 | 比较像素，不比文件哈希 |

- **闪烁**：逐帧降噪的残余噪声不会在相邻帧之间对齐，静态区域会"沸腾"。OIDN 3 已在 2026-01 宣布带时间降噪，Blender 合成器里的时间降噪节点还是一个未合并的 PR（#151020，与 OIDN 组合使用，没有版本里程碑）[10]，先不用。现在的办法：提高 spp 压低噪声；开 albedo 和 normal 辅助通道；静态镜头可以固定 `seed` 关 animated seed（噪声"粘"在画面上，但不闪）【推测：这是一个要做 A/B 的取舍】。
- **验收口径**：同硬规则 1。`blender -b scene.blend -f N` 单独渲第 N 帧，与整段 `-a` 渲出来的第 N 帧，逐帧比无损 PNG：`ffmpeg -i a.png -i b.png -lavfi psnr -f null -`，要求 ≥ 45 dB。预期同机同设置下是逐像素相同【推测】，实测结果要记进 `LOCAL.md`。

## 渲染时间：先用 5 帧校准

没有直接的 M3 Max 逐帧数据。能找到的锚点：

| 锚点 | 数字 | 来源 |
|---|---|---|
| Blender Open Data 总分（样本/分钟之和） | M4 Max 平均 5208（28 次测试，Blender 4.2），约等于台式 RTX 4070 | [13] 9to5Mac |
| 同上，M3 Max 40 核 | 约 4146 | [13] MacRumors 帖子，搜索摘要【二手】 |
| Classroom 场景（1080p，300 spp，无降噪） | RTX 4070 约 15.6 s | [13] renderjuice【二手】 |
| EEVEE，Mac Studio M2 Max（32 GB），用户自己的一个含体积的场景 | Blender 4.1.1 每帧 1–3 s；4.2.2 同等画质约 75 s；关体积或体积分辨率 1:16 后 14–17 s | [11] issue #128253。**单个场景，不是通用数字** |

由此推算（全部【推测】，没有实测）：

| 场景 | 设置 | 每帧 | 10 秒（300 帧） |
|---|---|---|---|
| 产品转台、棚拍，少量材质 | EEVEE 默认 | 1–3 s | 5–15 分钟 |
| 同上 | Cycles 128 spp + OIDN | 3–8 s | 15–40 分钟 |
| Classroom 级室内 | Cycles 300 spp，无降噪 | 约 20 s（15.6 s ÷ 0.8） | 约 100 分钟 |
| Classroom 级室内 | Cycles 96 spp + OIDN | 7–10 s | 35–50 分钟 |
| 含体积、EEVEE 最高画质（#128253 的用户场景，M2 Max） | 体积 1:1 | 约 75 s | 6 小时以上 |

**校准协议**（写进 BRIEF 的费用预算）：挑最重的镜头，渲 t=0、⅓、⅔、末尾各 1 帧，加上一帧最重的特写，记下每帧墙钟时间和 `--cycles-print-stats` 的内存；预算 = 帧数 × 中位数 × 1.5（重试）。结果写进 `LOCAL.md` 的渲染速度一行，和 `engines/README.md` 里 ClaudeAnimationBase 的"1080p 约 0.13 秒/帧（Metal）"并列。超过预算 1.5 倍就停下告诉用户。

## Metal 上的 Cycles 与 EEVEE

- **Cycles**：Metal 只支持 Apple Silicon，macOS ≥ 13 [5a]；4.3 起 Metal 渲染只保留 Apple Silicon，Intel/AMD 的已移除 [9b]。MetalRT 硬件光追：4.0 release notes 写明 M3 支持硬件光追，Cycles 默认使用（MetalRT 设为 Auto）；M1、M2 上则默认关闭 [9a]。我们的 M3 Max 属于前者。OIDN 的 GPU 加速从 4.1 起在 Apple Silicon（macOS 13.0 及以上）上可用 [10]。
- **EEVEE**：4.2 起新的 EEVEE 在 Apple Silicon 上走 Metal。4.2 有两个已记录的坑 [11]：(1) 命令行渲染动画时内存不释放，渲到一半卡死（#125333，M2、Metal：4.1 正常、4.2.0 出问题）。根因是 EEVEE 的渲染循环里缺了 `GPU_render_step`，Metal 显存没有被回收；修复（PR 126781）在 4.3 合入，并回溯到 4.2.4；有用户在 2024-11 反馈 4.3 上仍然出现，没有核实。(2) 同一场景明显变慢（#128253，M2 Max：4.1.1 约 1–3 s，4.2.2 约 75 s；用户定位到体积，关掉体积或把体积分辨率降到 1:16 后约 14–17 s）。5.x 是否还有残留，本机要用 **5.2 跑一次 300 帧的耐久测试并监控内存**；稳妥的做法是分块渲染，每个进程不超过 60 帧，崩了只重跑那一块。
- **省电模式**：M4 Pro 上开"低电量模式"，Cycles 渲染性能降到正常的 65–71% [13]。渲染前确认插电、关低电量模式，长任务外面包 `caffeinate -i`。
- **5.2 对后台模式的改动**：`gpu.init()` 用来在 `--background` 下初始化 GPU 后端 [4]。如果 EEVEE 在无头脚本里拿不到 GPU 上下文，先试这个【推测】。

## 与 HyperFrames、ffmpeg 合成：alpha、EXR、色彩管理

**合成路径**

| 路径 | 什么时候 | 格式 | 注意 |
|---|---|---|---|
| A 不透明底片 | Blender 出整个背景或英雄镜头，HTML 叠字和 UI | PNG 序列 → mp4（BT.709 tv，CRF 12–16），当 `<video>` 底层 | 最常用，最省事 |
| B 带 alpha 的 PNG 序列 | 3D 物体要和 HTML 图层前后穿插 | RGBA PNG，页面里按 `floor(t × fps)` 取帧，和 `playbook/05` 的绿幕接法同一种 | 1080p RGBA 单帧约 1–3 MB【推测】，300 帧到 GB 级；目前 HyperFrames 的 `<video>` 是否保留输入视频的 alpha，文档没写，未验证 |
| C ffmpeg `overlay` | 代码层和 Blender 层各渲成文件再叠 | PNG 序列或 ProRes 4444 | 见下面 alpha 一段 |
| D 夹心 | 字要夹在 3D 物体之间 | 渲两层：背景（不含英雄物体）和前景（英雄物体 + 阴影，透明底）；字放中间 | Cycles 的 Shadow Catcher（物体只接收阴影射线，并和其他物体有间接光交互；`is_shadow_catcher`）可以把 3D 物体的影子落到我们的 HTML 背景上 [15]；手册没有提到 EEVEE，第三方教程说 EEVEE 要手搭材质【二手】 |
| E Blender 里合成 | 需要景深、AO、Cryptomatte 遮罩 | 多层 EXR，在 Blender 合成器里出 PNG | 5.0 起合成器 Python 接口变了（`compositing_node_group`），见上文 |
| F 深度遮挡 | 要让 HTML 或 Three.js 里的字按 3D 深度躲到物体后面 | 导出 Depth 通道（5.0 起通道名是 `Depth`，旧名 `Z`），浮点 EXR 或归一化后的 16 位 PNG，在 WebGL 层比较深度【推测：没有做过】 | 深度必须和相机的近远裁剪面一起存，否则没法还原 |

**视图变换怎么选**（手册的枚举：Standard、Khronos PBR Neutral、AgX、Filmic、ACES 1.3/2.0、Raw、False Color；Filmic 已标注 deprecated）[7]

| 目标 | 选 | 理由 |
|---|---|---|
| 和 HTML 的扁平图形、品牌色无缝拼；非写实、平涂 | Standard，或自发光材质平涂 | 只做显示转换 [7] |
| 产品镜头，要品牌色准 | Khronos PBR Neutral（4.2 release notes 已加入） | 设计目标就是让输出的 sRGB 颜色尽量贴近材质里的 sRGB 基色，面向产品摄影 [7][19] |
| 电影感、强光源、自发光 | AgX（新文件默认） | 高光去饱和，更像胶片；但它会改整片的色彩性格，HTML 层要么补同样的 look，要么整片统一再调一次色 [19] |
| Filmic | 不用 | 手册标注 deprecated |
| Raw、False Color | 只用来检查，不用来出片 | 手册说明 Raw 不用于最终导出 [7] |

**PNG 与 EXR**

- PNG：视图变换和显示变换已经烘进像素，8 位按 straight alpha 存；这是合成默认值。
- EXR：存 scene-linear，premultiplied alpha；AgX 之类的 look **不在里面** [8][7]。
- ffmpeg 读 EXR 时不会自动做 sRGB 编码。**【本机实测】** 6 个 scene-linear 值 `0, 0.0031308, 0.05, 0.18, 0.5, 1.0`，sRGB 公式应得 `0, 10, 63, 118, 188, 255`；ffmpeg 默认得到 `0, 1, 13, 46, 128, 255`（中灰 0.18 → 46，画面发黑）；加 `-apply_trc iec61966_2_1` 后与公式完全一致。`-apply_trc` 在 ffmpeg 里标了 deprecated，但 8.0.1 上仍然有效。本机 ffmpeg 没有 zscale、libplacebo、OCIO，做不了更精细的转换。多层 EXR 用 `-layer` 选层。

**alpha 约定与 ffmpeg**：Blender 内部 premultiplied，存 8 位格式（PNG）时转成 straight，存浮点格式（EXR）保持 premultiplied，这是 2.66 起的约定 [8]；5.x 没看到改动说明，出片前用一张半透明边缘的测试图确认一次【推测】。**【本机实测】** ffmpeg `overlay=format=auto` 把 RGBA 输入当 straight：合成到白底上最大误差 0.9 个色阶；输入是 premultiplied 时必须写 `overlay=format=auto:alpha=premultiplied`（误差 1.0），漏写则边缘最大偏 57 个色阶（暗边）。

**最后一步的 YUV 矩阵（最容易忽略）**：PNG 序列编码成 H.264 时，如果不指定矩阵，swscale 默认用 BT.601，又不写标签；浏览器和手机按 BT.709 解码，饱和色就偏了。8 个色块的实测：不写任何参数，按 BT.709 解码最大偏 21 个色阶；只写 `-colorspace/-color_primaries/-color_trc`，最大偏 3，但 ffprobe 里 primaries 和 trc 仍是 unknown；下面的写法最大偏 3，四个标签齐全【本机实测】。检查方法、修法和本仓库已有的例外见 `playbook/02-verification.md` 的"色彩标签"。

```bash
ffmpeg -framerate 30 -i out/plate/f_%04d.png \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
  -c:v libx264 -crf 14 plate.mp4      # ffprobe 应显示 tv / bt709 / bt709 / bt709
```

## 安全：MCP 与 LLM 生成的 bpy

**规则：不要把 LLM 生成的 bpy 代码交给任何 Blender MCP 直接执行，除非在沙箱里。** 而且 MCP 会话本身不可复现，不算产物。

- **官方 MCP**（Blender Lab，仓库 `projects.blender.org/lab/blender_mcp`，GPL-3.0；v1.0.0 于 2026-04-27 发布，v1.0.3 于 2026-09-11，release notes 里没有提到安全或沙箱方面的改动；要求 Blender 5.1+）：页面明确警告，服务器会直接执行 LLM 生成的代码，没有任何措施防止数据被删除或外发，建议用虚拟机或不含敏感信息的系统（2026-10-01 对着页面核对）[16]。Blender 开发者论坛的讨论里，官方仓库只附了一个承认不足以当安全边界的 `weak_sandbox.py`；社区提出的缓解方向是默认只读、写操作要确认、封网络和子进程 [16]。Anthropic 在 2026-04-28 发布的 9 个创意软件 connector 里包含 Blender，同时成为 Blender Development Fund 的企业赞助者【二手】[16]。
- **社区 `ahujasid/mcp-for-blender`**（原名 `blender-mcp`，2026-10-01 核对：MIT，约 2.98 万星）：`execute_blender_code` 用 `exec()` 执行任意 Python；通过一个无认证、无加密的本地 TCP socket 通信；已有 CVE（CVE-2026-10661，评分低，`input_image_url` 注入）和"无限制代码执行"的 issue #207；新版有 `BLENDER_MCP_SAFE_MODE=1`，拦截文件读写、网络、起子进程、持久化代码 [16]。它还集成了 Poly Haven（CC0）、Sketchfab、Poly Pizza（约 69% 是 CC-BY，需署名）等素材源，每一项都要进素材台账。
- **威胁面**：(1) 模型自己写出破坏性代码；(2) 间接提示注入，`.blend` 文件里的对象名、文本块、网页素材都能带指令；(3) `.blend` 里的自动执行脚本（Python 驱动器、启动脚本），命令行默认 `-Y` 禁用，不要加 `-y` [5]。

**政策（什么时候怎么选）**

| 场景 | 做法 |
|---|---|
| 探索建模，人在旁边看 | 可以用 MCP，放在虚拟机或单独的 macOS 用户下，工作目录之外不放任何东西；每次会话结束，把确认有用的操作**固化成 `build.py`** |
| 管线里跑 agent 写的 `build.py` | ① 静态检查：AST 扫描，禁 `os`、`subprocess`、`socket`、`urllib`、`shutil`、`eval/exec`、`__import__`，`open` 只许写输出目录；② `--factory-startup`、不加 `-y`；③ 套 `sandbox-exec`（下） |
| 第三方 `.blend`、素材 | 当不可信输入：先 `--disable-autoexec`（默认已是）打开，扫描文本块和驱动器再用 |
| 需要联网取素材 | 不在渲染进程里取；单独一步，显式 URL、记来源和许可 |

**`sandbox-exec`**（macOS 手册标注 DEPRECATED，但在 macOS 15 上可用）。下面的 profile 在 `sh`、`curl`、`python3`、`ffmpeg` 上验证过：输出目录可写；其他位置（包括 `/tmp`）写入得到 `Operation not permitted`；网络被拒（`curl` 返回 000，不加沙箱时是 200）【本机实测，2026-10-01 复核】。**没有用 Blender 本体验证过。**

```scheme
(version 1)
(allow default)
(deny network*)
(deny file-write*)
(allow file-write* (subpath "/ABS/PATH/TO/PROJECT/blender/out"))
(allow file-write* (literal "/dev/null") (literal "/dev/dtracehelper"))
```

```bash
# 把 TMPDIR 指到白名单里：否则 Python 的 tempfile 在沙箱里找不到可写的临时目录（本机实测）
mkdir -p blender/out/.tmp
sandbox-exec -f vh_blender.sb env TMPDIR="$PWD/blender/out/.tmp" blender -b --factory-startup ...
```

Blender 自己需要写的位置（着色器缓存、`~/Library/Application Support/Blender`）还没验证【未实测】，首次冒烟时按报错补白名单。`sandbox-exec` 不是安全边界的终点：`(allow default)` 只挡了网络和写入，读取 `~/.ssh` 和各种密钥文件仍然是放行的（本机验证过，`ls ~/.ssh` 成功），要更严就把读取也收紧。

## 许可证（维护者待定）

以下是官方原文的要点，不是法律意见。许可页和 FAQ 的原文已在 2026-10-01 对着页面核对 [17]。

| 问题 | 官方说法 | 结论 |
|---|---|---|
| Blender 本体 | GNU GPL v2 或更新；个别模块用 Apache 2.0 等更宽松协议；整体在 GPL v3+ 下兼容 [17] | — |
| **输出**（图片、视频、`.blend`） | 官方许可页和 FAQ 都写明：用 Blender 做出的作品完全归创作者所有；`.blend` 被视为程序输出，版权归用户，可用于任何闭源产品 [17] | **不受 GPL 影响** |
| **调用 bpy 的 Python 脚本** | FAQ：分享或发布的、用了 Blender Python API 调用的脚本，必须以 GNU GPL 提供；许可页的措辞是"符合 GPL 的协议" [17] | **只在分享或发布时触发**，纯自用不触发；MIT 是 GPL 兼容协议，但 FAQ 字面写的是按 GPL，取向偏保守 |
| 完全在 Blender 之外、不调 API 的工具 | 可以闭源、可以卖 [17] | 不 import bpy 的封装（例如将来的命令行封装）属于此类 |
| 官方 MCP | 仓库元数据为 GPL-3.0 [16] | 只读参考 |
| `bpy` PyPI 包 | 元数据标 GPL-3.0 [18] | 同上 |
| 素材 | 各自许可：Poly Haven 等为 CC0，Poly Pizza 多为 CC-BY，Sketchfab 逐件不同 [16] | 一律记素材台账 |

**维护者待定**：本仓库是 MIT。`engines/blender/` 下如果放调用 bpy 的脚本，怎么写许可，有三个选项，本指南不替维护者决定：

1. 仓库里不放 `import bpy` 的文件：`build.py` 由 agent 在项目目录里生成（`projects/` 不入库），仓库只放不 import bpy 的封装和模板 JSON。改动最小。
2. 把 `engines/blender/` 下所有 `import bpy` 的文件标 `SPDX-License-Identifier: GPL-3.0-or-later`，在 `ACKNOWLEDGMENTS.md` 和该目录的 README 里说明。MIT 仓库可以包含 GPL 文件，但这部分文件按 GPL 分发。
3. 保持 MIT，承担 FAQ 字面要求（按 GPL 提供）和 MIT 之间的差距。

决定之前，本指南不含可运行的 bpy 脚本，只有流程、伪代码和 API 名称。Blender 的名称和 logo 受单独的商标政策约束，片子里出现 Blender 界面截图前先看一眼 [17]【页面没给细节，未核对】。

## 流程与验证

### 最小管线

和 `playbook/01` 的阶段 0–9 对齐。

| 阶段 | 做什么 | 产物 / 命令 | 通过条件 |
|---|---|---|---|
| 0–1 | 判断是否需要 Blender（见"什么时候用 Blender"）；BRIEF 里写渲染预算 | `BRIEF.md` 加渲染账：帧数 × 校准时间 × 1.5 | 用户同意预算（**关卡 ①**） |
| 2–3 | `STYLE.md` 选视图变换和灯光语言；分镜里标出哪些镜头是 3D；**blockout animatic** | EEVEE 或 Workbench，50% 分辨率，几何块代替资产；`bin/vh sheet` | 节奏和构图通过（**关卡 ②**） |
| 4 | 有声音就先定音频和 `beats.json`；时间线的时间从这里读 | `audio/`、`timeline.json` | 时长由音频决定 |
| 5 | 搭 `lib/`，先做 5 帧冒烟：build → 渲 5 帧 → 对比 | `blender.lock`、5 帧 PNG | 确定性验收（下表第 6 行）通过；记录每帧耗时 |
| 6 | 写场景：`timeline.json` + 资产；每个镜头一个块 | `build/scene.blend` | lint、静态检查、单镜头联系表 |
| 7 | 自查和评审：联系表、strip、crop、色彩、alpha、降噪检查 | `out/check/` | 见下表 |
| 8 | 分块渲染 final 底片；合成（上面的路径 A–F）；编码；`bin/vh check` | `out/plate/*.png` → `plate.mp4`、`final.mp4` | 帧数、YAVG、时长；**关卡 ③** |
| 9 | 交付：底片、`blender.lock`、素材台账（含许可）、`LESSONS.md` | — | 用户看完 |

### 验证方法（沿用联系表、strip、crop）

| # | 检查 | 做法 | 通过条件 | effort |
|---|---|---|---|---|
| 1 | 能不能跑 | `--python-exit-code 1`；`build.py` 静态扫描；5 帧冒烟；日志里没有 `Traceback` | 退出码 0 | quick |
| 2 | 结构 | 帧数 = 时长 × fps；输出 mtime 是新的；PNG 尺寸；每帧 `signalstats` 的 YAVG 没有突降（5.x API 变了会出空帧）；没有 NaN 或全黑帧 | 与 `playbook/02` 的"静默失败"同口径 | quick |
| 3 | 联系表 | 全片 draft 渲成 mp4（EEVEE，50%），`bin/vh sheet <mp4>`；每个镜头取首、中、末三帧；final 只在关键时刻渲全分辨率抽帧 | 构图、光、材质读得出 | quick |
| 4 | strip | 关键动作每 0.1–0.15 s 一格，`select` + `tile` 拼 | 运动曲线不抖、不漂、运动模糊合理 | standard |
| 5 | crop | 100% 裁切：高光、暗部、边缘、玻璃、头发，每镜头至少 2 处 | 无 fireflies、噪点可接受、alpha 边缘干净 | standard |
| 6 | 确定性 | (a) 单帧 `-f N` 对整段 `-a` 的第 N 帧；(b) 一个进程渲 0–59 对两个进程各渲 0–29、30–59；(c) 重启后重渲同一帧。比无损 PNG 的 PSNR | 最小值 ≥ 45 dB（预期逐像素相同【推测】） | studio；5 帧冒烟时先做 (a) |
| 7 | 色彩合约 | 场景里放一块品牌色平涂块，走完整条链路（Blender PNG → ffmpeg → mp4 → 解码），与 HTML 里同色块的截图比较 | 最大色阶差 ≤ 3（本机基线：BT.709 + tv 的 8 位往返最大差 3）；`ffprobe` 标签见 `playbook/02` | standard |
| 8 | alpha 边缘 | RGBA 分别合成到黑、白、品牌色上，裁边缘放大（命令见 `playbook/05` 的"抠完必做的三项检查"）；`premultiplied` 选项对不对 | 无黑边或亮边 | standard（用到带 alpha 的路径时） |
| 9 | 降噪与闪烁 | 静态区域的帧间差（颗粒 σ 的时间估计见 `playbook/05` 的"颗粒与清晰度"，或 `python3 tools/motion.py`）；OIDN 开、关各一版 | 静态区域的时间 σ 不高于同片其他图层 | studio |
| 10 | 缓存 | 缓存 sha256 和 `blender.lock` 记录一致；关键帧 JSON 的哈希不变 | 一致 | standard（有模拟时） |
| 11 | 速度 | 每块的墙钟时间写进 `LOCAL.md`；超出预算 1.5 倍就停下告诉用户 | — | standard |

reviewer subagent 看的还是联系表、手机联系表、crop 和 `STORYBOARD.md`。

## 类型与风格映射

**八个类型**

| 类型 | 收益 | 典型镜头 | 说明 |
|---|---|---|---|
| 03 产品宣传 | **高** | 产品转台、微距、材质特写、拆解 | 英雄镜头 1–3 个交给 Blender；UI 镜头仍是 HyperFrames。只用用户自己的模型（`product-keynote` 的规定），视图变换选 PBR Neutral |
| 01 数学/科学讲解 | 中 | 需要真实光照或物理的"实景插页"：天体光照与日食、折射、流体、布料；晶体、分子的材质化 | 公式和几何仍用 Manim；Blender 只做插页 |
| 02 知识短片 | 中低 | hook 镜头里的真实感物件；竖屏 1080×1920 直接渲 | 最多 1–2 个 3D 镜头，draft 用 EEVEE，其余矢量 |
| 04 歌词 / MV | 中 | 抽象或科幻 3D 场景、体积光、每拍一个动作 | 片长 3–4 分钟，渲染量大；用 EEVEE 风格化，歌词和字在 HyperFrames |
| 06 论文讲解 | 低中 | 硬件、机器人、场景类论文的 3D 示意 | 机制用 Manim，结构用 HTML，必要时才用 |
| 05 数据故事 | 低 | 3D 地球、柱状雕塑 | Three.js 足够，不建议 |
| 07 手绘 | 不建议 | — | 风格语法是 2D 笔触（Grease Pencil 另议，不在本文范围） |
| 08 野兽派 / 梗 | 不建议 | — | 用不上光影 |

**二十八个风格**（依据各自 `STYLE.md` 里"适合与不适合"和"引擎做法"）

| 级别 | 风格 | 怎么受益、要注意什么 |
|---|---|---|
| **显著受益** | `product-keynote` | 现在的样片是自写 SDF ray-marcher；真实产品模型加路径追踪的软影和高光更可信。规定"只有用户自己的产品才用真实模型"，视图变换用 PBR Neutral |
| | `clockwork-map` | 黄铜齿轮是 PBR 金属加面积光软影；齿轮运动学天然是 t 的解析函数（L0）。现状是 Three.js 或 mode-7 Canvas，Blender 可做"机械特写插镜" |
| | `monumental-scifi` | 体积雾和尺度感，Cycles 体积渲染比 `FogExp2` 更有质感。本仓库介绍片的一镜到底已经在 Three.js 里成型，Blender 只适合加强个别镜头 |
| **局部或可选** | `synthwave-outrun` | 铬字和镜面地面反射用 Cycles 更真；样片用 Canvas2D + WebGL 已经够 |
| | `blueprint` | `STYLE.md` 明令"不做 3D 渲染"。Blender 只可能当**线稿的数据源**：从真实模型出正交线稿（如 Freestyle）再转成 SVG 路径，仍由代码画线【推测，没验证】 |
| | `halftone-comic` | toon 着色的 3D 动作镜头加网点后处理，实验性 |
| | `fui-hud` | 示意图里的真实 3D 线框，少量 |
| | `dark-math`（类型 01） | 3D 数学对象先用 Manim 的 `ThreeDScene` |
| **不建议** | 其余 20 个：`cutout-jazz`、`scratched-type`、`symmetry-pastel`、`neon-step-print`、`archival-pan-zoom`、`swiss-grid-type`、`brutalist-meme`、`editorial-data`、`bubble-chart-story`、`isotype`、`bouncy-flat-2d`、`risograph`、`silhouette-papercut`、`watercolor-pastoral`、`ink-wash`、`dunhuang-mural`、`shadow-puppet`、`guochao-festive`、`crt-terminal`、`pixel-16bit` | 质感来自 2D 工艺、印刷或笔触；引入路径追踪会破坏风格语法。`silhouette-papercut` 的 `STYLE.md` 写明"不做 3D"，多层纸的真实阴影做成 Blender 预渲染 plate 与风格语法冲突，慎用 |

## 待验证与待决策

**要在本机装上 Blender 后验证的**

1. 5.2 上 EEVEE 命令行 300 帧的内存曲线（#125333 的后续）。
2. Cycles Metal 的确定性：`-f N` 对 `-a`、单进程对多进程、重启前后；自适应采样开、关各一组。
3. OIDN 开、关的静态区域闪烁（颗粒 σ 的时间估计）。
4. 刚体烘焙缓存乱序渲染是否一致。
5. Blender 需要的 `sandbox-exec` 写目录白名单（着色器缓存、`~/Library/Application Support/Blender`）。
6. HyperFrames 的 `<video>` 是否保留输入视频的 alpha（WebM VP9、ProRes 4444），PNG 序列方案是否够用。
7. PNG 元数据里是否含渲染时间等字段（影响"文件哈希"）。
8. M3 Max 的真实渲染速度，替换"渲染时间"一节的推算。
9. 上文各条命令（`-o //../out/…`、`-E BLENDER_EEVEE`、`--cycles-device METAL`）在 5.2 上的实际行为。

**维护者待定**

1. `engines/blender/` 下 bpy 脚本的许可写法（"许可证"一节的三个选项）。
2. 是否把"Blender 类型"正式列为类型 10（README 路线图里的类型 10 是 Three.js 和着色器），或只作为 03 和 01 的引擎选项。
3. 官方 MCP 是否允许在 `standard` 档位之外的场景使用，以及隔离环境（虚拟机还是单独用户）。

## 来源

- [1] Blender 发布页 https://www.blender.org/download/releases/ （4.5 LTS 2025-07-15、5.0 2025-11-18、5.1 2026-03-17、5.2 LTS 2026-07-14）。
- [2] Blender 5.2 LTS https://www.blender.org/download/releases/5-2/ （2026-07-14 发布，LTS 到 2028-07；2026-10-01 核对）。[2a] 下载目录 https://download.blender.org/release/Blender5.2/ （5.2.0 于 2026-07-14、5.2.1 于 2026-08-25、5.2.2 于 2026-09-15；macOS arm64 的 dmg 约 346 MB；2026-10-01 核对）。
- [3] 系统要求 https://www.blender.org/download/requirements/ （macOS 13+，5.0 起需要 Apple Silicon，内存最低 8 GB、建议 32 GB；2026-10-01 核对）。
- [4] Blender 开发者文档 release notes：5.0 Python API 原文 https://projects.blender.org/blender/blender-developer-docs/raw/branch/main/docs/release_notes/5.0/python_api.md （2026-10-01 核对引擎 id、`scene.node_tree`、File Output、`media_type`、通道名、Action 各条）；5.0 色彩 https://developer.blender.org/docs/release_notes/5.0/color_management/ ；5.2 EEVEE https://developer.blender.org/docs/release_notes/5.2/eevee/ ；5.2 Python API https://developer.blender.org/docs/release_notes/5.2/python_api/ （`gpu.init()` 2026-10-01 核对）；5.2 Cycles https://developer.blender.org/docs/release_notes/5.2/cycles/ 。
- [5] 手册：命令行参数 https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html ，命令行渲染 https://docs.blender.org/manual/en/latest/advanced/command_line/render.html （页面是 JS 渲染，内容取自手册仓库的 rst：https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/advanced/command_line/arguments.rst ）。[5a] GPU 渲染 https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html 。
- [6] 手册：Cycles 采样 https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html （rst 原文）。
- [7] 手册：显示与视图变换 https://docs.blender.org/manual/en/latest/render/color_management/displays_views.html ；色彩空间 https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html ；图像格式 https://docs.blender.org/manual/en/latest/files/media/image_formats.html 。
- [8] Blender 2.66 发布说明 "Image Transparency" https://archive.blender.org/wiki/2015/index.php/Dev:Ref/Release_Notes/2.66/Image_Transparency/ （字节精度 straight、浮点 premultiplied；PNG 存 straight，EXR 存 premultiplied）。
- [9b] 官方公告 https://devtalk.blender.org/t/cycles-remove-support-of-metal-with-amd-intel-gpus-for-4-3-and-onwards/35098 。[9a] Blender 4.0 Cycles release notes https://developer.blender.org/docs/release_notes/4.0/cycles/ （M3 硬件光追，MetalRT 设为 Auto）。[9] Metal：Cycles Apple Metal 反馈帖 https://devtalk.blender.org/t/cycles-apple-metal-device-feedback/21868 ；M3 调优 PR https://projects.blender.org/blender/blender/pulls/114296 （标题）【二手：搜索摘要，仅作背景】。
- [10] OIDN 文档 https://www.openimagedenoise.org/documentation.html （设备间数值差异；RT 滤波器不具备时间稳定性）；Blender 4.1 Cycles https://developer.blender.org/docs/release_notes/4.1/cycles/ （OIDN GPU 加速，Apple Silicon、macOS 13.0+）；OIDN 3 时间降噪 https://www.cgchannel.com/2026/01/open-image-denoise-3-will-support-temporal-denoising/ ；合成器时间降噪 PR #151020 https://projects.blender.org/blender/blender/pulls/151020 。
- [11] EEVEE：内存问题 https://projects.blender.org/blender/blender/issues/125333 ，变慢 https://projects.blender.org/blender/blender/issues/128253 （网页 403，内容经 Gitea API 读到：https://projects.blender.org/api/v1/repos/blender/blender/issues/125333 及其 `/comments`）。
- [12] Cycles 设备差异 issue #101561（https://projects.blender.org/api/v1/repos/blender/blender/issues/101561/comments ，读到 Brecht 等人的回复）；#89351 是重复报告，没有开发者解释。
- [13] 基准：9to5Mac https://9to5mac.com/2024/11/17/m4-max-blender-benchmark/ ；MacRumors 帖子 https://forums.macrumors.com/threads/apple-is-falling-behind-m4-max-nowhere-close-to-rtx-5090.2454589/page-4 【二手：403，读到摘要】；RTX 4070 Classroom https://www.renderjuice.com/gpus/rtx-4070-for-blender 【二手】；低电量模式影响 https://eclecticlight.co/2025/01/06/power-modes-and-apple-silicon-gpus/ 。
- [14] 刚体：`bpy.ops.rigidbody.bake_to_keyframes` https://docs.blender.org/api/current/bpy.ops.rigidbody.html ；渲染农场与刚体烘焙 https://www.renderjuice.com/docs/rendering-with-blender/rigid-body-simulations 【二手】。
- [15] Shadow Catcher：手册（Cycles 物体设置）rst 原文 https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/render/cycles/object_settings/object_data.rst 。
- [16] MCP：官方页面 https://www.blender.org/lab/mcp-server/ （2026-10-01 核对警告原文和 5.1+ 要求）；安全讨论 https://devtalk.blender.org/t/blender-mcp-server-after-claude-mcp-security-for-blender-scripting-3d-agent-notes/45131 ；社区实现 https://github.com/ahujasid/mcp-for-blender （原名 blender-mcp，旧链接 https://github.com/ahujasid/blender-mcp 会跳转；MIT）；CVE-2026-10661 https://github.com/advisories/GHSA-qqw9-95ww-prfm （2026-10-01 核对：低危，2026-06-03 发布）；issue #207 https://github.com/ahujasid/mcp-for-blender/issues/207 【二手：搜索摘要】；官方仓库元数据与 release：https://projects.blender.org/api/v1/repos/lab/blender_mcp 及 `/releases`（2026-10-01 核对：GPL-3.0，v1.0.3 于 2026-09-11）；Anthropic connector 报道 https://dataconomy.com/2026/04/29/claude-gains-integrations-with-adobe-blender-and-ableton/ 【二手】。
- [17] 许可：https://www.blender.org/about/license/ ；FAQ https://www.blender.org/about/faq/ （2026-10-01 核对输出归属、脚本须按 GPL 或符合 GPL 的协议提供、Blender 之外的闭源工具）。
- [18] Homebrew cask https://formulae.brew.sh/api/cask/blender.json （2026-10-01 核对：5.2.2）；PyPI `bpy` https://pypi.org/simple/bpy/ 。
- [19] Khronos PBR Neutral：4.2 release notes https://developer.blender.org/docs/release_notes/4.2/rendering/ ；设计讨论 https://devtalk.blender.org/t/adding-pbr-neutral-tone-mapper/33602 ；AgX、Standard、PBR Neutral 的差别见手册 [7]。
