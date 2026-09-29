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

## 汉字按笔顺书写

水墨、书法、白板一类的片子常要把汉字一笔一笔写出来，比如章节标题。Eian 的《华夏·五千年》就是这么做的（见 `cases/community-prompts.md`）。这和 ANIMATION_GUIDE 的"不写字"不冲突：那条禁的是牌子、字幕、标签这类信息文字；书写本身就是画面时可以用，但要在项目的 `STYLE.md` 里写明这个例外。

**数据**：[Make Me a Hanzi](https://github.com/skishore/makemeahanzi)（skishore）提供 9,000 多个常用简繁汉字的笔顺矢量数据。`graphics.txt` 每行是一个 JSON：`character` 是字；`strokes` 是按正确笔顺排好的每一笔轮廓（SVG path）；`medians` 是每一笔的中线点列。坐标系是 1024×1024、y 轴朝上，左上角在 (0, 900)，显示时要翻转，README 给的变换是 `scale(1, -1) translate(0, -900)`。字形来自文鼎的两款 PL 楷体字库，写出来是楷书的样子。

**许可和存放**：两份数据的许可不同。`graphics.txt`（连同它的动画 SVG）由文鼎字体派生，按 Arphic Public License 发布；`dictionary.txt` 由 Unihan 和 CJKlib 派生，按 LGPL 3.0 或更高版本发布。两者都不是 MIT，`graphics.txt` 又有约 30 MB，所以**不放进本仓库，也不加进 `fetch.sh`**。每个项目自己下载，只留用到的字，并在 `NOTES.md` 的素材台账里记一行：文件、来源（仓库地址和提交号）、许可（APL）。

```bash
# 在项目目录里执行：只取用到的字，记下数据版本
curl -sL https://raw.githubusercontent.com/skishore/makemeahanzi/master/graphics.txt \
  | grep -E '"character":"(商|周|秦)"' > assets/hanzi-strokes.jsonl
git ls-remote https://github.com/skishore/makemeahanzi.git HEAD   # 提交号写进素材台账
```

只发布渲染出来的视频，一般不涉及再分发数据；如果连源码和数据一起公开（例如发布可播放的 HTML），要随附 APL 全文（一般理解，非法律意见）。

**动画：每一笔的进度都由 t 算出来**：
1. **预计算**，只依赖数据、不依赖帧：每一笔中线的弧长 L；这一笔的时长 = 最短时长 + L ÷ 书写速度；笔与笔之间留一个停顿，换部件时可以停得更久；累加得到每一笔的开始时间。一个字要写多久由它自己的笔画决定，先算出来，再回写分镜的 reads。
2. **每一帧**：第 i 笔的进度 u = ease(clamp((t − 开始时间) ÷ 时长))，缓动做成起笔和收笔慢、行笔快。用这一笔的轮廓做遮罩（clip），沿中线从起点画到弧长 u·L，线宽要足够盖满整笔（在 1024 的坐标里约 128）。轮廓保证字形准确，中线决定顺序和方向。Make Me a Hanzi 自带的动画 SVG 也是"轮廓裁剪 + 沿中线描边"，只是用 CSS 关键帧驱动；按硬规则 1，我们要改成由 t 直接算出来。
3. **枯笔**：不用一根实线，而是用 20–30 根平行于中线的"笔毛"，每根有固定的横向偏移和粗细；沿弧长用带种子的噪声决定哪里断墨，断墨的阈值随 a ÷ L 升高，越往后墨越干，透明度也随之降低。起笔处可以加一个稍深的墨点。纹理只依赖"笔画编号 + 弧长 + 种子"，不依赖 t，所以已经写出的部分每一帧都一样，写完的字也不会抖。

```js
// plan：预计算的笔画表 [{outline: new Path2D(strokes[i]), L, t0, d, ...}]；pointAt(s, a) 返回弧长 a 处的点和法线
function drawHanzi(ctx, plan, t, seed) {          // t：这个字开始书写后的秒数
  ctx.save();
  ctx.transform(1, 0, 0, -1, 0, 900);             // 翻转 y 轴
  for (const s of plan) {
    const u = ease(clamp((t - s.t0) / s.d));
    if (u <= 0) continue;
    ctx.save(); ctx.clip(s.outline);              // 笔画轮廓当遮罩
    for (let b = 0; b < 24; b++) {                // 枯笔：24 根笔毛
      const off = (hash(seed + s.i * 97 + b) - 0.5) * 150;
      ctx.lineWidth = 6 + 6 * hash(seed + b * 31);
      let prev = null;
      for (let a = 0; a <= u * s.L; a += 6) {
        const p = pointAt(s, a), q = [p.x + p.nx * off, p.y + p.ny * off];
        const dry = 0.15 + 0.55 * a / s.L;        // 越往后越容易断墨
        if (prev && noise1(seed + s.i * 13 + b * 7.3 + a * 0.015) > dry) {
          ctx.globalAlpha = 1 - 0.5 * a / s.L;
          ctx.beginPath(); ctx.moveTo(...prev); ctx.lineTo(...q); ctx.stroke();
        }
        prev = q;
      }
    }
    ctx.restore();
  }
  ctx.restore();
}
```

种子取自字和笔画编号这类稳定的名字，不要用帧号。在 HyperFrames 或自写的 `renderAt(t)` 页面里，直接用 Canvas 2D。ClaudeAnimationBase 的主画布是 WEBGL 模式，没有 2D 的 clip，可以每帧在 `createGraphics()` 建的 2D 离屏层上重画，再用 `image()` 贴回主画布。

**自查**：对每个字出一条 strip，逐帧确认笔画的先后和方向与 `medians` 一致；乱序渲染几帧和顺序渲染比对，枯笔纹理最容易因为拿帧号当种子而对不上；确认书写时长落在分镜给这个字的 reads 时间里。

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
- **claude-animation-skill**（MIT，不在 183 个 skill 的清单里）：Node canvas 画的手绘 2D，不用浏览器；"细节圣经"要求每个表面画三层（底色 → 纹理 → 边缘），线宽和细节随景深递减；笔触种子取自稳定的名字而不是帧号；`verify` 把 5 个帧正序、倒序、再正序渲三遍比 MD5。见 `references/repos/claude-animation-skill/plugins/claude-animation/skills/claude-animation/SKILL.md`。
- **story-to-handdrawn-video**（MIT）：文字 → 黑白画稿 → 彩色插画，三段揭示；附 327 项画风和配色资产，可以离线浏览。见 `references/repos/story-to-handdrawn-video/references/style-library.html`。
- **remotion-guofeng-starter**（代码 MIT，演示素材不能商用）：国风纸片组件 `PaperCollageLayer`，风格资产和故事分开。见 `references/repos/remotion-guofeng-starter/style/design.md`。
