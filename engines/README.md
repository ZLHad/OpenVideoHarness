# 引擎：初始化与安装

新项目一律建在 `projects/<date>-<slug>/` 下。本目录里的东西是模板，不要直接在里面改。

最快的方式是 `bin/vh new <type> <slug>`：它会建好目录、复制模板；手绘和 MV 类还会复制 ClaudeAnimationBase 并装好依赖，short、promo、data、meme 类会自动运行 `bin/vh hf-init` 装好 HyperFrames（离线失败时会提示稍后重跑）。只有 Remotion、Manim 要在建好目录后，按下面对应的一节手动初始化；MV 或论文类改用 HyperFrames 时，以及 edit 类（实验性，首选 HyperFrames，做法见 [`editing.md`](editing.md)），对项目目录单独运行一次 `bin/vh hf-init`。

## ClaudeAnimationBase（p5.js + p5.brush），已装好

```bash
cp -R engines/ClaudeAnimationBase projects/<date>-<slug>
cd projects/<date>-<slug> && npm install
node render.mjs --sheet=0.5,2,4 --cols=3 --w=480 --out=out/check/sheet.jpg   # 验证环境，约 5 秒
```

- 使用前完整读一遍 `ANIMATION_GUIDE.md`。
- 在 `src/scenes/` 下新建自己的场景文件，然后把 `studio.html` 里 `demo.js` 的 script 标签换成它。
- 在 `src/config.js` 里设置 `duration`、`bpm`、`offset`，需要时再设 `fps`（默认 24，`--fps=` 可以临时覆盖）；有音乐时在配置里设 `PROJECT.audio`（路径相对项目根目录），或者加 `--audio=audio/song.mp3`。`--clip` 和 `--encode` 都会混入音频，并截到或补到画面的精确长度：音频比画面短时补静音并打出警告（硬规则 2：让 `duration` 跟着音频走），不会像 `-shortest` 那样把画面截掉。
- 长片用 `--frames --workers=4` 渲 JPEG 帧（可并行、可续渲），再 `--encode`。`--encode` 不开浏览器，自己读 `src/config.js` 里的 PROJECT，按 `out/frames/frames.json` 记下的 fps 编码；只编 `duration × fps` 帧，从磁盘上的第一帧开始。时长改短后多出来的旧帧会被排除并提示。开头或结尾缺帧（只渲了一段 `--range`）只给警告；两段已渲染的帧中间有缺口时直接报错并列出缺的帧，因为编出来的视频会停在缺口处。`--loop=<name>` 的帧单独放在 `out/frames_loop_<name>`，编成 `out/loop_<name>.mp4`，不会和正片混在一起。
- 没有 GPU 时加 `--soft-gl`，用 SwiftShader 软件渲染 WebGL。它同时关掉 2D canvas 的 GPU 加速：开着加速时，同一帧每次启动渲出来都不一样（PSNR 约 39 dB，过不了硬规则 1 的 45 dB）；关掉后，跨进程、乱序渲染都逐像素一致，demo 单帧也从约 40 s 降到约 12 s（无 GPU 的 Linux 实测）。另外，所有路径都关掉了 Chrome 的 CanvasNoise：它给 GPU 加速的 2D canvas 读回加每次启动都不同的噪声（反指纹功能），是上面那种差异的主因。有 GPU 的机器上 2D canvas 默认也走 GPU 加速，同样受 CanvasNoise 影响；关掉以后，2026-09-30 在 macOS 的 Metal GPU 上实测：同一帧跨启动、乱序渲染都逐像素一致（见 CHANGELOG 里的 “Verified on macOS with a GPU”）。
- 本机实测：1080p 约 0.13 秒/帧（Metal），11 秒的 demo 渲染 37 秒。
- 来源：[JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase)，MIT。复制过来时没有带 `.git`。

## HyperFrames（HTML + GSAP）

要求 Node ≥ 22 和 FFmpeg。**版本固定在实测过的 0.8.82**（`bin/vh` 默认使用；想试新版，就设 `HYPERFRAMES_VERSION=0.8.84`，先跑 lint 和一次冒烟渲染确认没有回归，再把默认版本改上去）。**`bin/vh new short|promo|data|meme <slug>` 会自动初始化**，也可以对已有项目单独运行 `bin/vh hf-init <项目目录> [landscape|portrait|square]`。

> ⚠️ HyperFrames 0.8.x 的 `init` 和 `skills update` 会把 skills 装进**全局**的 `~/.claude/skills` 和 `~/.agents/skills`。`--skip-skills` 参数目前不生效，只能用环境变量 `HYPERFRAMES_SKIP_SKILLS=1` 跳过。`bin/vh hf-init` 已经设置了这个变量，并且只把工程文件拷进项目，不拷它生成的 CLAUDE.md 和 AGENTS.md，避免和本仓库的路由冲突。自己手动运行 npx 时，也要带上这个变量：

```bash
export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1          # 每次开终端先设置
npx hyperframes lint                                    # 写的过程中随时检查
npx hyperframes check --snapshots                       # 最终关卡
npx hyperframes snapshot --at 1.5,4.2 --describe false  # 单帧；--describe false 不能省，见下
npx hyperframes preview                                 # 浏览器预览
npx hyperframes render --quality draft --fps 30 --output out/draft.mp4
npx hyperframes render --quality delivery --fps 30 --output out/final.mp4
```

### 最小写法（0.8.82）

`bin/vh hf-init` 搭出来的 `index.html` 就是最小的合成（`bin/vh new short|promo|data|meme` 会自动跑它），手写时照着改；完整样板见 `showcase/02-short-leo-doppler/index.html`。`<body>` 里是这样：

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="10" data-width="1080" data-height="1920">
  <h1 id="title" class="clip" data-start="0" data-duration="10" data-track-index="0">标题</h1>
</div>
<script>
  const tl = gsap.timeline({ paused: true });   // 必须 paused：时间由渲染器推进，不是 GSAP 自己走
  tl.fromTo("#title", { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.6 }, 0);   // 第 3 个参数是绝对时间（秒）
  window.__timelines["main"] = tl;              // 用 data-composition-id 当 key 登记，渲染器只认这里
</script>
```

- **根元素**：`data-composition-id` 必填；`data-start`、`data-duration` 是秒；`data-width`、`data-height` 是像素。项目根目录只放一个 composition（`index.html`）。`<head>`（viewport、gsap 的 `<script>`、把 `html, body` 定成画布大小的样式、用 `local()` 声明本机字体的 `@font-face`）照脚手架抄。
- **`.clip`**：要按时间出现的元素加 `class="clip"`，写 `data-start`（第几秒出现）和 `data-duration`（持续几秒），渲染器按它们决定元素什么时候在画面上。`data-track-index` 只是 Studio 时间线上的行号，渲染不读它，也管不了叠放顺序，叠放用 CSS `z-index`。
- **动画都挂在这条 paused 的 timeline 上**（`to`、`from`、`fromTo`、`set`），不用 CSS `animation` / `transition`、`Math.random()`、`Date.now()`（硬规则 1）。
- **驱动 tween**：曲线、轨道、物理这类每帧重算的画面，在同一条 timeline 上挂一个 `ease: "none"` 的代理 tween，在回调里按 t 重画，画面就仍是 t 的纯函数。showcase 02 的 `draw(t)` 这样画出了全部物理画面，`DUR` 是片长（秒）：

  ```js
  const drv = { t: 0 };
  tl.fromTo(drv, { t: 0 }, { t: DUR, duration: DUR, ease: "none", onUpdate: () => draw(drv.t) }, 0);
  ```

- **写一段，查一段**：`npx hyperframes lint` 到 0 error 再往下；`snapshot --at <秒> --describe false` 看几个关键时刻的单帧；`render --quality draft --fps 30 --output out/draft.mp4` 出草稿，字体和接缝以渲出来的 mp4 为准；最后 `--quality delivery` 出成片。完整写法见上面那一块命令。

### 注意事项和已知问题（0.8.82 实测）

- **`snapshot` 一律带 `--describe false`。** 环境里有 `GEMINI_API_KEY`（或 `GOOGLE_API_KEY`）时，`snapshot` 默认把每一帧发给 Gemini 做画面描述，结果写进 `snapshots/descriptions.md`：画面离开本机，还要按 Gemini 计费。本仓库的 `bin/vh tts … --align gemini` 也要这个 key，所以 key 多半是设了的。`--describe false` 和 `--describe=false` 都能关掉；没设 key 时它只打一行 "skipping"。`check` 不受影响。
- **第一次 `render` 会下载 chrome-headless-shell，而且几乎没有提示。** 现象：在非交互的 shell 里（agent 就是这样跑的），终端只有 "Checking browser…" 在转圈，没有大小和百分比，下载期间一直是这一行，网慢时看上去就像卡死了。原因：`render` 用 HyperFrames 自己管理的 chrome-headless-shell（0.8.82 固定为 152.0.7977.30），缓存里没有就先下载：约 100 MB，解压后约 200 MB，放在 `~/.cache/hyperframes/chrome`，所有项目共用；装了 Google Chrome 也一样（`snapshot`、`check` 在缓存为空时直接用系统 Chrome，不下载）。下完会打出 `Browser: download`，以后是 `Browser: cache`。解决：第一次渲染之前先跑 `npx hyperframes browser ensure`，它会写明在下什么、多大，下完打印路径；下不了，看 README.zh-CN.md 的"国内网络"。
- **`font-weight: 800` 在 macOS 自带的 PingFang SC 上等于 600。** 现象：字幕规格写了字重 800，渲出来却不够粗，也没有报错。原因：PingFang SC 只有 6 个字重，从 Ultralight 到 Semibold（CSS 的 100–600），没有 Bold 和 Heavy；请求 700、800、900 都落到 600，实测渲出的字和 600 逐像素相同，浏览器也不会再合成粗体。解决：用 PingFang SC 就写 600，并在 STYLE.md 里记下；真要 800，自己带一个有这个字重的字体（Noto Sans SC 等，不联网的取法见 README.zh-CN.md 的"国内网络"），或者换一个有更粗字重的系统字体（比如 Songti SC 有 900，`styles/_swatch/README.md` 的字体表列了各字体实测可用的字重）。
- **`--format png-sequence` 写出的是 RGBA，而且不画页面背景。** `html`、`body` 和合成根元素上的 `background` 都不会进 PNG（那些地方 alpha = 0），只有元素自己的底色会留下。做确定性检查时要留意，细节和比对办法见 `playbook/02-verification.md` 的"确定性"一节。
- **不要运行 `npx hyperframes skills update`**。skill 文档已经拉到本地，直接读：`references/repos/hyperframes/skills/`（工作流和参考资料）、`references/repos/hyperframes/_upstream_claude/skills/`（motion-doctrine 等内部规范，写动画前先读 motion-doctrine）。
- 想让所有项目都能用 `/hyperframes`、`/faceless-explainer` 等命令，可以装成 Claude Code 的用户级插件（`claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes`）。这会修改全局配置，**必须先征得用户同意**。
- **没有 `@font-face` 的字体，渲染时会去 Google Fonts 取。** `render`、`snapshot`、`check` 每次运行都请求，连不上就挂住（render 停在 5% 的 "Compiling composition"）。lint 拦不住其中两种：它别名表里的名字（Arial、Helvetica Neue、Menlo 等）没有声明也算通过，渲染时被换成 Inter、JetBrains Mono 去取；以 `sans-serif` 这类通用族名开头的栈，前面会被补上 Inter。所以本机字体也写 `@font-face`、`src` 用 `local()`，栈里排第一的写声明过的字体，照 `bin/vh hf-init` 搭的脚手架做。渲染日志里出现 `[Compiler] Injected deterministic @font-face rules`，就是还有字体没声明。国内网络下的做法见 README.zh-CN.md 的"国内网络"。
- **中文字体**：lint 会拒绝没有 `@font-face` 或 Google Fonts `<link>` 的字体。Noto Sans SC 不在它的自动字体列表里（列表里只有 Noto Sans JP），要显式用 `<link>` 引入，或者把字体文件放进 `assets/` 并写 `@font-face`。
- **0.8.82 实测的上游问题**：
  - 两条 lint 规则互相矛盾：`gsap_repeated_fromto_without_baseline` 建议加 `tl.set(…,0)`，加了又会触发 `gsap_timeline_set_initial_hide`。解法是在时间线外用 `gsap.set()` 设初始状态，同时给 tween 加 `immediateRender:false`。
  - 某次渲染后，本机被切换到较慢的截帧路径，之后每次渲染的耗时约为原来的 3 倍。这是本机设置，不跟着项目走；用 `HF_DE_PARALLEL_ROUTER=true` 可以恢复。
- 空格会被吞：sub-composition 模板里的连续空格和词间空格、JS 设置的文本前导空格，都可能被 HTML 合并掉。需要保留时用 `&nbsp;` 或 `white-space: pre`。
- **等宽字体的坑**：`ui-monospace, monospace` 能通过字体 lint，快照里看起来也是等宽，但 `hyperframes render` 渲染出来却是比例字体（showcase 00 在第一版全片都中了招）。要用 `@font-face` 显式声明，例如 `@font-face{font-family:"LF Mono";src:local("SF Mono"),local("Menlo")}`。**判断字体要看 mp4 渲染出的帧，不要看快照。**`check --snapshots` 只保存对比度检查用的 PNG，不能替代 `snapshot --at`。
- `snapshot` 在 tween 刚开始的那一刻，可能和最终渲染出的帧不一致。关键帧以渲染出的 mp4 为准，逐帧 strip 的做法见 `playbook/02-verification.md`。
- 完整样板：`showcase/02-short-leo-doppler/`（竖屏科普，单个 `index.html`）。
- **HyperFrames 加 Three.js（3D 世界、一镜到底）的坑**，来自介绍片的制作：
  - 每一帧都用 `renderAt(t)` 从 t 算出摄像机和所有物体的状态。摄像机路线用按 t 参数化的样条，不用 Three.js 的动画时钟。关卡处可以用 stop 关键帧停站，但要叠一层低幅的手持漂移，镜头不要完全停死（原因见 `playbook/08-vfx-and-motion-sources.md` 的"一镜到底"一节）。
  - `VideoTexture` 必须**每帧**设置 `texture.needsUpdate = true`，否则渲染出的屏幕是全黑的。视频按 t 去 seek，而且要等 seek 完成。
  - `__hf.buildReady` 要在普通 `<script>`（不是 module）里**同步注册**，否则每个并行 worker 的开头都会出现空帧。
  - 项目根目录只能有一个 composition。局部测试文件放在 `out/`，要跑时临时拷回来。
  - `snapshot` 看不到视频纹理（屏幕是暗的），检查必须看渲染出的 mp4 帧。
  - **渲染时不要依赖在线 CDN。** importmap 指向 CDN 时，只要页面加载那一刻断网，渲染就会静默挂住：日志 0 字节，也不报错。介绍片的第一次 final 渲染就卡在这里。把 three.js 装进项目，importmap 指向 `node_modules`，snapshot 和 render 都能读到这些文件：

    ```bash
    npm i -D --save-exact three@0.181.2      # 写精确版本，换版本时重新比对无损帧
    ```
    ```html
    <script type="importmap">{"imports":{"three":"./node_modules/three/build/three.module.js","three/addons/":"./node_modules/three/examples/jsm/"}}</script>
    ```

    渲染命令外面再包一层看门狗：超时就杀掉进程，核对退出码和帧数，再抽几帧查 YAVG，确认 3D 层确实画出来了。

    GSAP 也一样。HyperFrames 的脚手架默认从 CDN 加载 `gsap@3.14.2`；`bin/vh hf-init` 现在会自动把它装进项目，并把 `<script src>` 改成 `node_modules/gsap/dist/gsap.min.js`，如果还有别的 CDN 引用，会打出警告。showcase 00 和 02 已经照此改过。剩下的网络依赖是 Google Fonts 的 `<link>`（showcase 02 的 Noto Sans SC、ClaudeAnimationBase 的 `studio.html`）：离线时要么先用本机字体（见 `styles/_swatch/README.md` 的字体表），要么把字体文件放进项目并在 NOTES 里记下许可；国内网络下的具体做法（系统字体、字体文件、从 npm 镜像装 Fontsource）见 README.zh-CN.md 的"国内网络"。
  - **`renderAt` 里抛异常时，画面会停在上一帧，不报错。** 介绍片有一版 draft 读了一个还没声明的 `const`（TDZ），36–48 s 整整 12 s 都停在 t=0 的画面。画面角落常驻一个 t 读数的 HUD，抽一帧就能看出停帧；成片级的检测方法见 `playbook/02-verification.md`。
  - **Hermite 路径在"快甩、慢推"的站点会冲过头。** 关键帧的切线默认由前后两个邻居估出来，甩镜到站时，站点的切线带着甩镜的速度，镜头会冲进字里（介绍片的架构站把节点标签推出了画面）。给关键帧加一个切线模式：到站的关键帧用 `tm: "f"`，切线只取后面那段慢推；离站的关键帧用 `tm: "b"`，只取前面那段慢推。两站之间的甩镜就成了一条干净的 S 曲线。
  - **世界里的节点标签按屏幕像素定字号**，不要按画面宽度的比例缩放，否则长标签的中文会掉到 20 多 px。介绍片的 `pin()` 每帧把节点投影到屏幕，用 `2·d·tan(fov/2) / 1080` 算出这个深度上 1 px 对应的世界长度（d 是节点沿视线方向的深度，fov 是竖直视场角），据此缩放面向镜头的标签平面，字号就固定了（英文 54–56 px，中文 ≥ 46 px）。另外两件事：标签框夹在安全框里；节点出画、或者标签被推离节点太远时就淡出，否则镜头离开后，标签会在画面边上堆成一摞。
  - **变拍只改一个 `bar(k)`。** 画面、事件表、字幕、HUD 都从同一个 `bar(k, beat)` 取时间，不手写秒数。介绍片把第 11 小节改成 6/4 时，画面这边只在 `bar()` 里给第 12 小节以后统一加 2 拍，HUD 改用按真实拍号换算的 `barBeat()`；作曲那边在 `score.json` 写 `"meters": {"11": 6}`（`bin/vh music` 现在也支持这个字段，beat map 会多出 `bars`）。其他秒数一个都不用手改。

## Remotion（React），未安装

```bash
cd projects && npx create-video@latest     # 选模板；做字幕短视频可选 TikTok 模板
cd <slug> && npx skills add remotion-dev/skills
npx remotion studio                        # 预览
```

- 许可：个人和 3 人以内的公司免费，超过这个规模需要购买授权。
- 官方 skills 已拉到本地：`references/repos/remotion-skills/skills/`。

## Manim CE（Python），未安装

本机已有 MacTeX、cairo、pango、ffmpeg。

```bash
cd projects/<date>-<slug>
uv init --bare --python 3.12 && uv add manim     # 实测：Manim CE 0.21.0 / Python 3.12 / macOS
uv add manim-voiceover                           # 只有要配旁白时才装
export PYTHONWARNINGS=ignore::SyntaxWarning      # 压掉 pydub 在 3.12 下的警告刷屏
uv run manim -ql scene.py MyScene                # 草稿：480p15
uv run manim -qh --fps 30 scene.py MyScene       # 成片：1080p30（-qh 默认是 60fps）
```

- 用 `--bare`：普通的 `uv init` 会在项目里多生成 `.git`、`main.py`、`README.md`、`.python-version`。
- 【综合】选 Python 3.12 是求稳；如果装不上，以 docs.manim.community 的安装说明为准，并把最终可用的命令记进 `LESSONS.md`。
- manim-voiceover 需要的 TTS 后端，按它的 README 选装。
- 锚点网格和包围盒审计有现成实现：`showcase/03-math-fourier/scenes/style.py`，可以复制到自己的项目里用。
- 写代码前先读 `references/repos/3brown1blue/src/three_b1b/skill/SKILL.md` 里的 Gotchas。
- 注意 CE 和 ManimGL 的 API 不能混用，参考 `references/repos/3brown1blue/src/three_b1b/skill/rules/manimgl-differences.md`。

## Blender，未安装，按需使用（实验性）

完整指南：[`blender.md`](blender.md)。**实验性：维护者的 Mac 没有装 Blender，指南没有验证过；渲染时间先渲 5 帧校准。**

- 安装：`brew install --cask blender`，也可以从官网下载。指南钉在 5.2 LTS（5.0 起只支持 Apple Silicon，Python API 有破坏性改动）。
- 渲染用脚本方式，保证结果可复现，分两段：`blender -b --factory-startup --python build.py -- …` 生成 `scene.blend`，再 `blender -b scene.blend … -a` 渲 PNG 序列。同时固定随机种子，并烘焙好模拟缓存。
- 官方的 MCP server 和社区的 `ahujasid/mcp-for-blender` 都会直接执行 LLM 生成的 Python，没有任何防护。**默认不用**：要用先问用户，放在虚拟机或单独的 macOS 用户下；没有沙箱，就不要让 LLM 生成的 bpy 代码经过它们执行。管线里跑 agent 写的脚本，加静态检查、`sandbox-exec` 和 `env -i`（见指南的"安全"一节）。

## 生成式视频（fal 等），按需使用

见 `playbook/05-hybrid-genvideo.md`。API key 从环境变量读取（例如 `FAL_KEY`），不要写进文件。花钱前先在 BRIEF 里和用户确认预算。
