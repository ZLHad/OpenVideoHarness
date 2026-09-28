# 07 手绘 / 水彩 / 白板 / 剪纸 / 角色短片

**适用**：角色小短片、手绘风的叙事科普、白板讲解、剪纸风动画；绘画式 MV 的画面部分也归这一类。

## 引擎

| 画风 | 引擎 |
|---|---|
| 水彩、墨线、角色动画 | **ClaudeAnimationBase**（p5.js + p5.brush）。本机已装好，渲染约 0.13 秒一帧 |
| 更浓的笔触画面 | 参考 functional-emotions-video 的 WebGL 笔触渲染器：先画 Canvas2D 底稿，GPU 再用约 6 万个带纹理的笔触重画 |
| 白板手绘 | rough.js、perfect-freehand、excalidraw-animate，放进 HyperFrames 或自己写的 `renderAt(t)` |
| 剪纸 | HyperFrames 或 p5：3–5 层纸，带软投影，12fps 步进 |

## 工作流（ClaudeAnimationBase）

1. **建项目**，不要在引擎模板里直接改：

   ```bash
   bin/vh new handdrawn <slug>    # 复制引擎、装依赖、放入模板；BRIEF 开头会注明以 ANIMATION_GUIDE 为准
   ```

2. **完整读一遍 `ANIMATION_GUIDE.md`**。它就是这一类视频的规范，下面只摘要点。
3. **先写 `STORYBOARD.md`**，格式照 guide 的 Workflow 一节：logline、世界观、母题、角色情绪弧线；每个镜头写清事件、反应、镜头运动和 reads，reads 带起止时间。写完给用户看。
4. **改配置**：在 `src/config.js` 里设 `duration` 和 `bpm`。有音乐时，`offset` 设为第一个强拍的时间。
5. **新建场景文件**：在 `src/scenes/` 下新建场景文件，然后在 `studio.html` 里把 `demo.js` 的 script 标签换成你的。
6. **逐个镜头做**：先摆关键姿势，用 `--sheet` 在关键时刻检查静帧；姿势能读懂了，再补中间的运动。
7. **三层自查**：用 `--sheet`、`--strip`、`--crop`（命令见 `playbook/02-verification.md`）。预算是每个镜头一张 sheet，每个关键动作一条 strip，每张承载剧情的脸一个 crop。
8. **出片**：`node render.mjs --clip --out=out/final.mp4`。长片用 `--frames --workers=4`，渲完再 `--encode --out=out/final.mp4`。

## 引擎使用技巧（showcase 01 踩出来的）

- **侧视角拿道具**：侧视时手臂挂点会随 `(.7 − aL)` 一起旋转，道具不反向旋转就会跟着歪；侧视只露一只眼，道具举到眼睛高度会把它挡住，所以要放在眼线以下，或者换成 3/4 视角。
- **描边透过填充**：p5.brush 的描边绘制得晚，几个 `paint()` 形状重叠时，先画的描边会透过后画的填充显出来，`flushBrush()` 也解决不了。互相遮挡的形状，要么去掉被遮部分的描边（`ink: null`），要么拆成不重叠的轮廓。
- **`--crop-at` 用表达式**：场景代码包在 IIFE 里，页面表达式访问不到场景函数。需要跟踪某个点时，把姿势函数挂到 `window` 上（例如 `window.SCENE = { poseB }`），再写 `--crop-at=SCENE.poseB(2.1).x,…`。
- **并行渲染**：同时运行的 `render.mjs` 进程 worker 总数控制在 4 个左右。进程太多时可能出现静默卡死（`protocolTimeout: 0` 不会超时报错），而且 `studio.html` 每次加载都会请求 Google Fonts；网络差时，把字体下载到本地再引用。
- **起步参考**：`showcase/01-handdrawn-clawd-leaf/` 是一支完整的 12 秒成片，包含分镜、20 条自评修复记录和场景源码。

## 审美要点（摘自 ANIMATION_GUIDE）

- **三个目标**：
  - **手工感**：笔触、会"boil"的墨线、纯 2D、不写字；
  - **活着**：画面上永远有东西在动、在发生；
  - **浑然一体**：动手前先规划，每个场景都和下一个衔接。
- **7 条规则**：
  1. 媒介统一；
  2. 不写字；
  3. 每个场景都要发生一件事；
  4. 按观众的理解速度定节奏（最常出错的一条）；
  5. 活着；
  6. 每个接缝都有转场；
  7. 写代码前先有完整构想。
- **角色要大**：中景 `u≈20–28`，特写 `u≈40–70`。小角色只用在远景里。
- **表情不能硬切**：用 `emotions()`，它会自动加上预备、眯眼、反应和回弹。
- **深度的做法**：靠遮挡、大小和颜色表现（越远越小、越偏蓝、越淡），不做 3D 投影。角色转身用画好的关键视角。
- **颜色**：不用纯黑纯白，用 `PAL.ink` 和 `PAL.cream`。发光效果用 `glow()`，否则黄叠蓝会变成灰绿。
- **白板风**：手要在旁白说到的那一刻画出来（RSA Animate 的做法），只画此刻正在讲的东西。
- **剪纸风**【综合】：
  - 3–5 层；
  - 投影偏移 4–8px；
  - 12fps 步进（on twos）；
  - 每层 ±1–2° 的轻微摆动。

## 禁止（ANIMATION_GUIDE 的常见失败清单）

- 带字的牌子、字幕、标签、写字的对话气泡；
- 角色站着微笑，什么事都没发生；
- 所有东西一个速度，事件叠在一起，没有停顿；
- 表情硬切；
- 机械运动：线性移动、所有部件同时动、两只手臂同步；
- 静止物体跟着抖（没设 `boilSeed`）；
- 3D 旋转、透视盒子；
- 用了 p5 原生形状、渐变或数码光效，和颜料风格混在一起；
- 道具浮在手附近，没有真正接触到手；
- 每个镜头都是一个不同的世界，彼此之间没有联系。

## Prompt 增量块

```text
+ TYPE: hand-made short. Engine: ClaudeAnimationBase copied into this project. Read ANIMATION_GUIDE.md fully first; its rules apply unless I say otherwise.
Idea: {one-line premise}. Length {N}s, bpm {..}{, song: audio/song.mp3 with offset ..}.
Show me STORYBOARD.md (logline, world, motif, arc, shots with reads and start–end times) before writing any scene code.
{Character: Clawd | a new character: {description}; build a model sheet (views + emotions) first and check it as stills.}
{Style variant: whiteboard draw-on (a pen leads every stroke; draw only what the narration says now) | paper-cut (3–5 layers, soft 6px shadows, 12fps stepped motion, ±1.5° wobble)}.
Budget: at least one sheet per shot, a strip for every key motion and transition, a crop for every face that carries the story.
```

## 自查重点

ANIMATION_GUIDE 的 Review loop 一节已经很完整，这里只补两条：
- 每个镜头的事件，只看它的联系表能不能看懂？
- 把 strip 按 0.1 秒一帧从头读到尾：每个 read 至少分到 12 帧（0.5 秒）吗？

## 可参考的案例与源码

- `engines/ClaudeAnimationBase/`：`ANIMATION_GUIDE.md`；`engines/ClaudeAnimationBase/docs/emotions.jpg` 和 `engines/ClaudeAnimationBase/docs/views.jpg`（角色设定表）；`src/scenes/demo.js`（一个 11 秒的完整示例，guide 结尾有它结尾部分的定时拆解）。
- `cases/mv-pdoom.md`：同一套 API 做成的 156 秒 MV。
- `cases/mv-functional-emotions.md`：自写 WebGL 笔触渲染器的做法。

## 社区 skill 参考

以下条目选自 183 个社区视频 skill，完整对照和许可证说明见 `references/community-skills.md`。只读参考；复用代码前，先确认它的许可证。

- **hand-drawn-explainer**（Apache-2.0）：区分"逐笔落墨"和"手绘风元素在动"，不用整图淡入冒充落墨；左右双语义岛布局。见 `references/repos/hand-drawn-explainer/SKILL.md`、`references/repos/hand-drawn-explainer/references/stroke-story-workflow.md`。
- **story-to-handdrawn-video**（MIT）：文字 → 黑白画稿 → 彩色插画，三段揭示；附 327 项画风和配色资产，可以离线浏览。见 `references/repos/story-to-handdrawn-video/references/style-library.html`。
- **remotion-guofeng-starter**（代码 MIT，演示素材不能商用）：国风纸片组件 `PaperCollageLayer`，风格资产和故事分开。见 `references/repos/remotion-guofeng-starter/style/design.md`。
