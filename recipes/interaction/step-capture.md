---
id: step-capture
name: 真界面逐步回放
one_liner: 一个真界面每走一小步截一张（打一个字一张、拖一格一张、播放中的视频每 0.4 s 一张），按时间一张张换、相邻两张交叉 0.09 s；镜头在截图自己的像素里推，光标在同一套坐标里走，讲到哪一块，其余压暗或给它一圈光
family: interaction
role: [feature]
intent: [interact, process, locate, detail]
energy: [1, 2]
duration_f: [90, 600]
types: [tutorial, promo]
engines: [canvas, hyperframes]
aspect: [landscape]
needs: [ui-page]
sound: recommended
pitfalls: [too-fast, text-blur, fake-ui, no-hold, motion-sickness]
qa: {peak: 84, settle: 132}
status: battle-tested
conflicts: [oversized-cursor]
pairs_with: [browser-walkthrough, zoom-callout, ime-typing]
impl: [components/ui-stage/component.js]
derived_from: []
sketch_sha: "adb8d5015387"
---

# 真界面逐步回放 · step-capture

## 意图

教程讲的是一个真产品，界面就该是它自己：字、按钮、状态都是真的，观众打开产品看到的就是片子里这一个。录屏推近会糊、鼠标小、等待只能剪掉；凭印象重画又不准。这一式在两者之间：把产品真的走一遍，每一小步截一张，片子按时间放这些截图。步子截得够密，打字、拖动、播放看起来就是活的；镜头和光标是另画的，所以能推到任何一块还锐利，动作能对上旁白的字。

和 `browser-walkthrough` 的区别：那张每个页面状态一张图，讲"点了以后变成什么"；这张把一个状态里的过程也截出来（逐字、逐格、逐帧），讲"它在动"，并且加了聚光和光圈。取材的写法（视口、倍率、量框、等页面静下来）照那张的"取材"一节。

## 阶段与时值

| 段 | 帧 | 发生什么 |
|---|---|---|
| 全景 | 0–18 | 整个窗口露一眼，观众知道在哪 |
| 光标过去 | 18–42 | 光标走向量好的目标，停稳 |
| 点 | 42–44 | 按下（缩 16%）、一圈光；截图在按下之后才换（交叉 0.09 s） |
| 推近 | 48–72 | 要读的那一块变了，镜头才推过去（0.8 s，缓入缓出），其余压暗 |
| 过程 | 75–110 | 逐字的截图一张张换：打一个字、换一张 |
| 落定 | 110–150 | 最后一张停住，光圈框住结果，停到读完 |

## 参数

| 参数 | 值 | 调节手感 | ★ |
|---|---|---|---|
| 截图 | 1440×900 的视口按 3 倍截（4320×2700），JPG 质量 90；一个有状态的流程（写一句、发出去、被取走）在一个浏览器会话里一口气截完 | 分几次截，中间的状态会丢（草稿按窗口存的界面尤其如此） | ★ |
| 步子多密 | 打字一个字一张；拖动 16–30 张；播放中的视频每 0.4 s 一张，或者把真视频的帧贴在播放器的框里 | 稀了读作幻灯片 | |
| 交叉 | 0.09 s | 0 是硬跳，有闪；超过 0.2 s 两张叠着读不清 | |
| 推近多少 | 要读的界面字 × 推近后每 CSS px 占的屏幕像素 ≥ 44 px（desktop）；13–14 px 的界面字要推到每 CSS px 约 3.1–3.4 个屏幕像素，也就是整窗铺满 1080p 之后再推 2.4–2.5 倍 | 推不够只能当质感，不算读到 | ★ |
| 推近还锐利 | 截图倍率 ≥ 每 CSS px 占的屏幕像素；3 倍截图在 1080p 里推到约 2.25 倍还锐利，再推会软一点；出 4K 要推近，按 6 倍截 | | ★ |
| 聚光 | 其余压到 62% 暗，0.25 s 进出 | 全黑像出错；太淡等于没做 | |
| 光标 | 约画面宽的 3.9%（74 px），坐标写在截图的 CSS px 里，跟着镜头换算 | 光标坐标写在屏幕上，镜头一推就对不上 | |

## 声音

点击、拖动、打字各有自己的声，打字照 `ime-typing`；推近配一声很轻的气流，不配重的 whoosh。

## 风格适配

- 结构参数（跟配方走）：全景、光标、点后才换、推近、逐步截图、落定。
- 皮肤参数（跟风格走）：窗口外的底、阴影、光圈和聚光的颜色。界面本身永远是真的样子，不跟着风格变。
- 量化风格：截图照常交叉，光标和镜头取整到 2 帧。

## 实现

做片子时用组件 `components/ui-stage`：`capture: { states: [[t, "s01"], …], size: [1440, 900], camera: [[t, cx, cy, zoom], …] }`，`cursor.space: "capture"`，`marks` 写聚光和光圈；`needs(st)` 说这一帧要哪两张图，页面先载入再画。草图里截图换成了画出来的灰盒，每个"状态"就是灰盒的一个样子。

```js
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib, bg = lib.color(tokens, "bg"), fg = lib.color(tokens, "fg"), ac = lib.color(tokens, "accent");
  ctx.fillStyle = lib.mixColor(bg, "#000000", 0.5); ctx.fillRect(0, 0, W, H);
  // the states (a capture a step): 0 the list, 1 a row picked, 2..9 a note typed a letter a capture, 10 added
  const NOTE = "BRIGHTER", S = [[0, 0], [1.47, 1]];
  for (let i = 1; i <= NOTE.length; i++) S.push([2.5 + i * 0.12, 1 + i]);
  S.push([3.72, 10]);
  let i = 0; while (i + 1 < S.length && t >= S[i + 1][0]) i++;
  const q = i ? lib.seg(t, S[i][0], S[i][0] + 0.09) : 1;
  // the camera in the capture's own px (1440 x 900): the point (cx, cy) lands at the centre, zoom screen px a capture px
  const K = [[0, 720, 450, 1.25], [1.6, 720, 450, 1.25], [2.4, 1180, 330, 2.2]];
  let k = 0; while (k + 1 < K.length && t >= K[k + 1][0]) k++;
  const a = K[k], b = K[Math.min(k + 1, K.length - 1)], u = a === b ? 0 : lib.ease.inOutCubic(lib.seg(t, a[0], b[0]));
  const cx = lib.lerp(a[1], b[1], u), cy = lib.lerp(a[2], b[2], u), z = lib.lerp(a[3], b[3], u), P = (x, y) => [960 + (x - cx) * z, 540 + (y - cy) * z];
  const ui = (s, alpha) => {   // one capture: drawn here as grey boxes; in a film, drawImage of the real screenshot
    ctx.save(); ctx.globalAlpha = alpha; ctx.translate(960 - cx * z, 540 - cy * z); ctx.scale(z, z);
    ctx.fillStyle = lib.mixColor(bg, fg, 0.92); ctx.beginPath(); ctx.roundRect(0, 0, 1440, 900, 12); ctx.fill();
    ctx.fillStyle = lib.mixColor(bg, fg, 0.15); ctx.fillRect(40, 60, 620, 380);
    for (let r = 0; r < 5; r++) { ctx.fillStyle = s >= 1 && r === 2 ? ac : lib.mixColor(bg, fg, 0.78); ctx.fillRect(40, 480 + r * 76, 620, 60); }
    ctx.fillStyle = lib.mixColor(bg, fg, 0.85); ctx.fillRect(1000, 0, 440, 900);
    ctx.strokeStyle = s >= 2 && s < 10 ? ac : lib.mixColor(bg, fg, 0.6); ctx.lineWidth = 3; ctx.strokeRect(1040, 260, 360, 80);
    lib.setFont(ctx, tokens, "mono", 30); ctx.fillStyle = bg; ctx.fillText(s >= 10 ? "" : NOTE.slice(0, Math.max(0, s - 1)), 1060, 312);
    if (s >= 10) { ctx.fillStyle = ac; ctx.fillRect(1040, 380, 360, 70); ctx.fillStyle = bg; ctx.fillText(NOTE, 1060, 426); }
    ctx.restore();
  };
  if (q < 1) ui(S[i - 1][1], 1);
  ui(S[i][1], q < 1 ? q : 1);
  // the spotlight on the column while it is read, a ring round the result
  const sp = Math.min(lib.seg(t, 2.3, 2.55), 1 - lib.seg(t, 4.75, 5));
  if (sp > 0) { const [x0, y0] = P(1010, 200), [x1, y1] = P(1430, 480); ctx.fillStyle = `rgba(0,0,0,${0.62 * sp})`; ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.roundRect(x0, y0, x1 - x0, y1 - y0, 16); ctx.fill("evenodd"); }
  if (t > 3.8) { const [x0, y0] = P(1034, 374), [x1, y1] = P(1406, 456); ctx.globalAlpha = lib.seg(t, 3.8, 4.05); ctx.strokeStyle = ac; ctx.lineWidth = 6; ctx.beginPath(); ctx.roundRect(x0, y0, x1 - x0, y1 - y0, 14); ctx.stroke(); ctx.globalAlpha = 1; }
  // the cursor, in capture px; a press shrinks it, a ring spreads from it
  const path = lib.cursorPath([[0, 1300, 900], [0.6, 1300, 900], [1.35, 350, 660], [2.2, 360, 660], [2.45, 1220, 300], [3.55, 1330, 300], [5, 1340, 300]]), pr = lib.presses([1.4, 2.5, 3.62])(t);
  const c = path(t), [sx, sy] = P(c.x, c.y);
  for (const p0 of [1.4, 2.5, 3.62]) { const d = t - p0; if (d >= 0 && d < 0.45) { ctx.strokeStyle = ac; ctx.globalAlpha = 0.9 * (1 - d / 0.45); ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(sx, sy, 14 + 70 * lib.ease.outExpo(d / 0.45), 0, lib.TAU); ctx.stroke(); ctx.globalAlpha = 1; } }
  const s = 2.6 * (1 - 0.16 * pr); ctx.save(); ctx.translate(sx - 5 * s, sy - 3 * s); ctx.scale(s, s); ctx.fillStyle = "#fff"; ctx.strokeStyle = "#111"; ctx.lineWidth = 1.5;
  const arrow = new Path2D("M5 3l0 19 5-4.6 3.4 7.6 3.2-1.4-3.4-7.5 6.8 0z"); ctx.fill(arrow); ctx.stroke(arrow); ctx.restore();
}
```

## 已知坑

- 旁白说界面怎么样，界面上其实不是那样 → 写每一句说界面的话之前先在截图上找到它；评审时逐句对着截图点。教程片的独立评审照截图对出过两句和界面对不上的旁白，两句都重录了，画面照着新的说法再点一遍。
- 截图露出人自己的东西 → 演示数据另建一份，产品从一份干净的副本起（不带本机的项目、账号、路径）；截完逐张看一遍。
- 页面没静下来就截 → 字体、图片、淡入还在半路；每一步等该出现的元素出现、字体载入，截图关掉动画和光标（`browser-walkthrough` 的"取材"）。
- 推近了字还是小 → 按参数表算推近倍数，不够就把那一块单独截一张更高倍率的。
- 渲染用的无头 Chrome 缺系统的展示字体，片子里的大字掉成衬线 → `bin/vh fonts check`，换成本机有的字体；截图里的界面字不受影响（已经是像素）。
- **判例**：一支 5 分 17 秒的使用教程（2026-11）里审片的那一段：真界面按状态回放，拖播放头 30 张、拉选区 16 张、逐字 12 张，右栏推到 2.4 倍、其余压暗。用户初版那一关说中间那一大段问题不大；独立评审对出的两句旁白和界面不符已重录。

## 验收帧

- `peak`（第 84 帧）：镜头已推到右栏，聚光压着其余，逐字的截图正换到一半，字推近后够大、不糊。
- `settle`（第 132 帧）：结果那一张停着，光圈框住它，光标停稳不挡字。

## 来源

本仓库原创：从一支 2026-11 的使用教程里真界面的回放提炼（截图、镜头、光标、聚光和光圈）。取材的写法沿用 `browser-walkthrough` 的"取材"一节。
