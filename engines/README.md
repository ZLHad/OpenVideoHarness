# 引擎：初始化与安装

新项目一律建在 `projects/<date>-<slug>/` 下。本目录里的东西是模板，不要直接在里面改。

最快的方式是 `bin/vh new <type> <slug>`：它会建好目录、复制模板；手绘和 MV 类还会复制 ClaudeAnimationBase 并装好依赖。HyperFrames、Remotion、Manim 类建好目录后，再按下面对应的一节初始化引擎。

## ClaudeAnimationBase（p5.js + p5.brush），已装好

```bash
cp -R engines/ClaudeAnimationBase projects/<date>-<slug>
cd projects/<date>-<slug> && npm install
node render.mjs --sheet=0.5,2,4 --cols=3 --w=480 --out=out/check/sheet.jpg   # 验证环境，约 5 秒
```

- 使用前完整读一遍 `ANIMATION_GUIDE.md`。
- 在 `src/scenes/` 下新建自己的场景文件，然后把 `studio.html` 里 `demo.js` 的 script 标签换成它。
- 在 `src/config.js` 里设置 `duration`、`bpm`、`offset`；有音乐时加 `--audio=audio/song.mp3`，或者在配置里设 `PROJECT.audio`。
- 本机实测：1080p 约 0.13 秒/帧（Metal），11 秒的 demo 渲染 37 秒。
- 来源：[JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase)，MIT。复制过来时没有带 `.git`。

## HyperFrames（HTML + GSAP）

要求 Node ≥ 22 和 FFmpeg。**`bin/vh new short|promo|data|meme <slug>` 会自动初始化**，也可以对已有项目单独运行 `bin/vh hf-init <项目目录> [landscape|portrait|square]`。

> ⚠️ HyperFrames 0.8.x 的 `init` 和 `skills update` 会把 skills 装进**全局**的 `~/.claude/skills` 和 `~/.agents/skills`。`--skip-skills` 参数目前不生效，只能用环境变量 `HYPERFRAMES_SKIP_SKILLS=1` 跳过。`bin/vh hf-init` 已经设置了这个变量，并且只把工程文件拷进项目，不拷它生成的 CLAUDE.md 和 AGENTS.md，避免和本仓库的路由冲突。自己手动运行 npx 时，也要带上这个变量：

```bash
export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1          # 每次开终端先设置
npx hyperframes lint                                    # 写的过程中随时检查
npx hyperframes check --snapshots                       # 最终关卡
npx hyperframes snapshot --at 1.5,4.2                   # 单帧
npx hyperframes preview                                 # 浏览器预览
npx hyperframes render --quality draft --fps 30 --output out/draft.mp4
npx hyperframes render --quality delivery --fps 30 --output out/final.mp4
```

- **不要运行 `npx hyperframes skills update`**。skill 文档已经拉到本地，直接读：`references/repos/hyperframes/skills/`（工作流和参考资料）、`references/repos/hyperframes/_upstream_claude/skills/`（motion-doctrine 等内部规范，写动画前先读 motion-doctrine）。
- 想让所有项目都能用 `/hyperframes`、`/faceless-explainer` 等命令，可以装成 Claude Code 的用户级插件（`claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes`）。这会修改全局配置，**必须先征得用户同意**。
- **中文字体**：lint 会拒绝没有 `@font-face` 或 Google Fonts `<link>` 的字体。Noto Sans SC 不在它的自动字体列表里（列表里只有 Noto Sans JP），要显式用 `<link>` 引入，或者把字体文件放进 `assets/` 并写 `@font-face`。
- **0.8.82 实测的上游问题**：
  - 两条 lint 规则互相矛盾：`gsap_repeated_fromto_without_baseline` 建议加 `tl.set(…,0)`，加了又会触发 `gsap_timeline_set_initial_hide`。解法是在时间线外用 `gsap.set()` 设初始状态，同时给 tween 加 `immediateRender:false`。
  - 某次渲染后，本机被切换到较慢的截帧路径，之后每次渲染的耗时约为原来的 3 倍。这是本机设置，不跟着项目走；用 `HF_DE_PARALLEL_ROUTER=true` 可以恢复。
- 空格会被吞：sub-composition 模板里的连续空格和词间空格、JS 设置的文本前导空格，都可能被 HTML 合并掉。需要保留时用 `&nbsp;` 或 `white-space: pre`。
- **等宽字体的坑**：`ui-monospace, monospace` 能通过字体 lint，快照里看起来也是等宽，但 `hyperframes render` 渲染出来却是比例字体（showcase 00 在第一版全片都中了招）。要用 `@font-face` 显式声明，例如 `@font-face{font-family:"LF Mono";src:local("SF Mono"),local("Menlo")}`。**判断字体要看 mp4 渲染出的帧，不要看快照。**`check --snapshots` 只保存对比度检查用的 PNG，不能替代 `snapshot --at`。
- `snapshot` 在 tween 刚开始的那一刻，可能和最终渲染出的帧不一致。关键帧以渲染出的 mp4 为准，逐帧 strip 的做法见 `playbook/02-verification.md`。
- 完整样板：`showcase/02-short-leo-doppler/`（竖屏科普，单个 `index.html`）。

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

## Blender，未安装，按需使用

- 安装：`brew install --cask blender`，也可以从官网下载。
- 渲染用脚本方式，保证结果可复现：`blender -b scene.blend --python build.py -- --out out/`。同时固定随机种子，并烘焙好模拟缓存。
- 需要交互式控制时，可以用 Blender 官方的 MCP server，或者社区的 `ahujasid/mcp-for-blender`。这两种方式都会直接执行 LLM 生成的 Python，使用前要先告诉用户。

## 生成式视频（fal 等），按需使用

见 `playbook/05-hybrid-genvideo.md`。API key 从环境变量读取（例如 `FAL_KEY`），不要写进文件。花钱前先在 BRIEF 里和用户确认预算。
