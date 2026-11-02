---
id: browser-walkthrough
name: 浏览器演示
one_liner: 每个页面状态一张真截图，光标走向量好的目标、停稳再点，页面在点下去之后才换，镜头比光标沉稳，只在要看的区域变了才推过去
family: interaction
role: [feature]
intent: [interact, process, locate]
energy: [1, 2]
duration_f: [120, 360]
types: [promo, short]
engines: [canvas, hyperframes]
aspect: [landscape, portrait, square]
needs: [ui-page]
sound: recommended
pitfalls: [fake-ui, too-fast, text-blur, motion-sickness, no-hold]
qa: {peak: 60, settle: 84}
status: tuned
conflicts: [oversized-cursor]
pairs_with: [type-and-filter, zoom-callout]
derived_from:
  - {repo: github.com/MengTo/Skills, commit: "a45892d", path: agent-skills/codex/browser-video-recording/SKILL.md, license: MIT, note: 只截浏览器内容、量目标坐标；光标少走直线、停稳再点、点后换页、点击只缩一下、镜头比光标沉稳}
  - {repo: github.com/MengTo/Skills, commit: "a45892d", path: agent-skills/codex/browser-video-recording/scripts/render_browser_demo.py, license: MIT, note: 点击缩放、按水平速度倾斜和换页淡入的数值；状态图加光标和镜头关键帧的数据形状}
sketch_sha: "b8fcc52dcf3f"
---

# 浏览器演示 · browser-walkthrough

## 意图

观众要跟着看一遍"在这个网站上怎么做成一件事"：点哪里，点了以后页面变成什么样。画面得是真的：每个状态一张真截图，光标的落点从页面里量出来，不靠目测。读起来要像一段剪过的录屏：光标少走路、走直线，停稳了再点，页面在点下去之后才变；镜头比光标沉稳，只在要看的区域变了才推过去。

和 `oversized-cursor` 不是一回事：那张用画面宽度 7% 的风格化光标在发布片里引视线；这张保留录屏的质感，光标约是真实大小的 3 倍，界面铺满画面，要看清的地方靠推近。两种光标不在同一支片子里混用。

## 取材

先把页面真的走一遍，取两样东西：每个状态一张截图，每个要点的元素一个框。

- **视口和倍率**：横屏用 1280×720 的视口、`deviceScaleFactor: 3`，图是 3840×2160。整页铺满 1080p 画面是 1.5 倍，16 px 的正文在画面里是 24 px，推近到 2 倍以内都不糊。竖屏用手机的视口（如 390×844，3 倍）。
- **只截网页内容**：不带浏览器边框和桌面。每个状态一张，按顺序命名（`01-list.png`、`02-detail.png`）；要滚动的页面截整页长图（`fullPage: true`）。
- **截之前让页面静下来**：等网络空闲、字体加载完，注入一段 CSS 关掉动画、过渡和输入框里闪烁的光标；关掉 cookie 条和弹窗。
- **目标框是量的**：`boundingBox()` 给的是视口里的 CSS px，光标落在框的中心。片子代码里的坐标都用 CSS px，画的时候乘 1.5 和推近倍数。
- **个人信息和素材**：用演示账号，截图里的姓名、邮箱、头像打码；截图逐张 `bin/vh assets add`，第三方网站写清来源。

用 Playwright（或者手边能按视口截图、能在页面里跑脚本的浏览器工具）：

```js
// capture.mjs：npm i -D playwright 以后 node capture.mjs。没装 Playwright 自带的浏览器时，launch({ channel: "chrome" }) 用本机的 Chrome
import { chromium } from "playwright";
import { writeFileSync } from "node:fs";
const CALM = "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}";
const browser = await chromium.launch(), page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 3 });
const boxes = {}, shot = (name) => page.screenshot({ path: `assets/ui/${name}.png` });
const settle = async () => { await page.waitForLoadState("networkidle"); await page.addStyleTag({ content: CALM }); await page.evaluate(async () => { await document.fonts.ready; }); };
const measure = async (id, sel) => { const b = await page.locator(sel).first().boundingBox(); boxes[id] = [b.x, b.y, b.width, b.height]; };
await page.goto("https://shop.example/list"); await settle();
await measure("card", ".product-card"); await shot("01-list");
await page.locator(".product-card").first().click(); await settle();
await measure("add", "button.add-to-cart"); await shot("02-detail");
await page.locator("button.add-to-cart").click(); await settle(); await shot("03-added");
writeFileSync("assets/ui/targets.json", JSON.stringify({ viewport: [1280, 720], dpr: 3, boxes }, null, 1));
await browser.close();
```

## 阶段与时值

第 0 帧 = 第一张截图出现。样片走两步：点开一张卡，再点"加入"。下表是第一步；第二步（第 93–136 帧）一样，只是镜头不动，点完以后光标挪到旁边，不压着按钮上变出来的勾。

| 段 | 帧 | 发生什么 |
|---|---|---|
| 认页面 | 0–24 | 第一张完整可见，光标静止：先让人认出这是哪个页面 |
| 走 | 24–44 | 光标走向量好的目标，一段一个目标，几乎是直线（`lib.cursorPath`：首尾缓，带 6% 的弧），按距离 0.4–0.8 s |
| 停稳 | 44–51 | 到了先停 0.2 s 左右，让人看清要点的是哪个 |
| 点 | 49–56 | 以尖端为轴缩到 0.85，带一点回弹（`lib.presses`）；点击声钉在第 51 帧 |
| 换页 | 54–59 | 点下 0.1 s 后换成下一张截图，0.18 s 交叉淡入；页面不在点击之前变 |
| 镜头跟 | 54–78 | 换页的同一帧镜头改目标，弹簧推到新页面要看的区域（样片是 1.6 倍），约 0.8 s 落定 |
| 读 | 78 起 | 停到新页面上要读的那一处读完，再走下一步；样片为了塞进 5 s，只停了 0.5 s |

## 参数

| 参数 | 值 | 调节手感 | ★ |
|---|---|---|---|
| 素材 | 每个状态一张真截图，加量出来的目标框 | 手画的界面、目测的坐标，一眼就假 | ★ |
| 截图倍率 | 视口 1280×720、3 倍（3840×2160）；铺满画面是 1.5 倍 | 1 倍的图一推近字就糊；视口取 1920 宽，正文在画面里只剩 16 px | ★ |
| 光标大小 | 箭头高约画面高的 5%（1080p 下 54 px），约是真实的 3 倍；大小不随镜头变 | 真实大小在视频里看不见；做到画面宽的 7% 就成了 `oversized-cursor` | |
| 路径 | 一段一个目标，几乎直线；不从无关的界面上绕过去 | 绕路、来回晃，读作没剪过的录屏 | ★ |
| 到达后停 | 0.15–0.25 s 再点 | 不停就点，观众来不及看清点的是哪个 | ★ |
| 点击 | 缩到 0.85 再带一点回弹，约 0.25 s；不加光圈 | 光圈和大幅缩放是另一种语言 | |
| 换页时机 | 点下后 0.08–0.12 s 开始，0.18 s 淡入；滚动用整页长图平移 0.5–0.8 s | 页面先变、光标后点，因果就反了 | ★ |
| 镜头 | 只在要看的区域变了才改目标（`lib.track` 加 `SPRINGS.cam`，约 0.8 s 落定）；1–2 倍；不出页面边 | 跟着光标每一下都动，看着晕；推得超过截图倍率，字糊 | ★ |
| 光标倾斜 | 按屏幕上的水平速度，1400 px/s 时到 8°，尾巴拖在后面 | 设成 0 也成立；超过 10° 像在甩 | |
| 读的时间 | 新页面上要读的那一处停到读完（`bin/vh readcheck` 的底线），再走下一步 | 初版几乎总是太快 | ★ |

## 声音

每次点击一声真实的点击（鼠标或触控板），钉在点击那一帧；打字时每个字一声很轻的键盘声。换页不配声，最多一声很轻的 swish；不用游戏或系统的提示音。有旁白时，点击落在说出那个动作的词上（"点开第一张卡"的"点开"）。写进 `audio/events.json`。静音也成立：每一下都看得见。

## 风格适配

- 结构参数（跟配方走）：停稳再点、点后换页、镜头只在区域变了才动、读的时间、光标大小不随镜头变。
- 皮肤参数（跟风格走）：光标的造型（macOS 的黑身白边、Windows 的白身黑边，或者产品自己的光标）；界面铺满画面，或者整个浏览器窗口浮在片子的底色上（四周留 5–8%，圆角 12–16 px，带投影，推近时窗口边出画）；点击声的音色。
- 量化风格（一拍二）：光标位置和镜头按 2 帧取整；停稳和读的时间照秒数给足。

## 实现

草图里的"截图"是灰盒，页面坐标是 1280×720 的 CSS px。放进真实项目时，`PAGE` 换成 `ctx.drawImage(截图, 0, 0, 1280, 720)`，`CARD`、`ADD` 换成 `targets.json` 里量出来的框，时间换成分镜里的片内时间。

```js
// browser-walkthrough：每个状态一张截图（这里是灰盒），光标走向量好的目标、停稳再点，点下 0.1 s 后换页（0.18 s 淡入）；
// 镜头只在换页那一帧改目标，弹簧约 0.8 s 落定；光标画在屏幕上，大小不随镜头变。
const F = (f) => f / 30, S = 1920 / 1280;                                  // 1280 宽的视口铺满画面是 1.5 倍
const CARD = [366, 150, 266, 240], ADD = [640, 400, 228, 56];             // 量出来的目标框 [x, y, w, h]
const mid = (b) => [b[0] + b[2] / 2, b[1] + b[3] / 2];
const CLICKS = [F(51), F(115)], SCENES = [[0, "list"], [F(54), "detail"], [F(118), "added"]];
const KEYS = [[0, 930, 102], [F(24), 930, 102], [F(44), ...mid(CARD)], [F(93), ...mid(CARD)], [F(108), ...mid(ADD)],
  [F(124), ...mid(ADD)], [F(136), 880, 476]];                              // 点完挪到旁边的空白处，不压着结果
const CAM = [[F(54), 830, 290, 1.6]];                                      // [t, x, y, 推近倍数]
export function renderAt(t, ctx, tokens, lib) {
  const C = { bg: lib.color(tokens, "bg"), fg: lib.color(tokens, "fg"), ac: lib.color(tokens, "accent") };
  const cam = (k, v0) => lib.track(v0, CAM.map((c) => [c[0], c[k]]), lib.SPRINGS.cam)(t);
  const z = cam(3, 1), vw = 1280 / z, vh = 720 / z;                        // 看得见的那一块，不出页面边
  const left = lib.clamp(cam(1, 640), vw / 2, 1280 - vw / 2) - vw / 2;
  const top = lib.clamp(cam(2, 360), vh / 2, 720 - vh / 2) - vh / 2;
  let i = 0; while (i + 1 < SCENES.length && t >= SCENES[i + 1][0]) i++;
  ctx.save(); ctx.scale(S * z, S * z); ctx.translate(-left, -top);
  if (i > 0) PAGE[SCENES[i - 1][1]](ctx, lib, C);                          // 上一张垫底，新的一张淡入
  ctx.globalAlpha = i > 0 ? lib.smoothstep(0, 0.18, t - SCENES[i][0]) : 1;
  PAGE[SCENES[i][1]](ctx, lib, C);
  ctx.restore();
  const path = lib.cursorPath(KEYS), p = path(t), vx = (p.x - path(t - F(1)).x) * 30 * S * z;   // 屏幕上的水平速度
  const tilt = Math.sign(vx) * 8 * Math.PI / 180 * Math.min(1, Math.abs(vx) / 1400) ** 0.72;    // 尾巴拖在后面
  cursor(ctx, (p.x - left) * S * z, (p.y - top) * S * z, 66 * (1 - 0.15 * lib.presses(CLICKS)(t)), tilt);
}
const PAGE = {
  list(ctx, lib, C) {
    chrome(ctx, lib, C); box(ctx, lib.mixColor(C.bg, "#ffffff", 0.9), 320, 80, 640, 44, 22); box(ctx, lib.rgba(C.fg, 0.3), 344, 96, 150, 12, 6);
    for (let k = 0; k < 8; k++) {
      const x = 80 + (k % 4) * 286, y = 150 + Math.floor(k / 4) * 270;
      box(ctx, lib.mixColor(C.bg, "#ffffff", 0.95), x, y, 266, 240, 10); box(ctx, lib.rgba(C.fg, 0.1), x, y, 266, 140, 10);
      box(ctx, lib.rgba(C.fg, 0.55), x + 16, y + 158, 90 + 110 * lib.hash(3, k), 12, 6);
      box(ctx, lib.rgba(C.fg, 0.2), x + 16, y + 184, 200, 8, 4); box(ctx, lib.rgba(C.fg, 0.2), x + 16, y + 202, 150, 8, 4);
    }
  },
  detail: (ctx, lib, C) => product(ctx, lib, C, false),
  added: (ctx, lib, C) => product(ctx, lib, C, true),
};
function product(ctx, lib, C, added) {
  chrome(ctx, lib, C); box(ctx, lib.rgba(C.fg, 0.1), 80, 96, 500, 560, 12);
  box(ctx, lib.rgba(C.fg, 0.75), 640, 112, 420, 30, 6); box(ctx, C.ac, 640, 164, 140, 34, 6);   // 标题（要读的那一处）、价格
  for (let r = 0; r < 4; r++) box(ctx, lib.rgba(C.fg, 0.22), 640, 236 + r * 26, 420 - 60 * lib.hash(7, r), 10, 5);
  box(ctx, added ? lib.mixColor(C.ac, C.fg, 0.4) : C.ac, ...ADD, 28);
  ctx.strokeStyle = lib.rgba(C.fg, 0.3); ctx.lineWidth = 2; ctx.beginPath(); ctx.roundRect(884, 400, 132, 56, 28); ctx.stroke();
  if (!added) { box(ctx, lib.rgba(C.bg, 0.9), 704, 423, 100, 10, 5); return; }
  ctx.strokeStyle = C.bg; ctx.lineWidth = 5; ctx.lineCap = "round";                 // 加入以后：按钮上换成勾，下面一行确认
  ctx.beginPath(); ctx.moveTo(686, 428); ctx.lineTo(696, 438); ctx.lineTo(714, 418); ctx.stroke();
  box(ctx, lib.rgba(C.bg, 0.9), 728, 423, 80, 10, 5); box(ctx, C.ac, 640, 472, 14, 14, 7); box(ctx, lib.rgba(C.fg, 0.5), 664, 474, 170, 10, 5);
}
function chrome(ctx, lib, C) {                                              // 页面底色和顶栏
  ctx.fillStyle = lib.mixColor(C.bg, "#ffffff", 0.75); ctx.fillRect(0, 0, 1280, 720);
  ctx.fillStyle = lib.rgba(C.fg, 0.06); ctx.fillRect(0, 0, 1280, 56);
  box(ctx, lib.rgba(C.fg, 0.6), 40, 18, 90, 20, 4);
  for (let k = 0; k < 4; k++) box(ctx, lib.rgba(C.fg, 0.25), 860 + k * 96, 24, 64, 8, 4);
}
function box(ctx, fill, x, y, w, h, r) { ctx.fillStyle = fill; ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.fill(); }
function cursor(ctx, x, y, size, rot) {                                     // 黑身白边的箭头：24 单位的箱子，尖端在 (0, 0)，绕尖端转
  const u = size / 24;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(u, u);
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 17); ctx.lineTo(4.2, 13); ctx.lineTo(7, 19.5); ctx.lineTo(9.6, 18.4); ctx.lineTo(6.9, 12); ctx.lineTo(12.4, 12); ctx.closePath();
  ctx.shadowColor = "rgba(0,0,0,0.3)"; ctx.shadowBlur = 6; ctx.shadowOffsetY = 3;    // 投影不随变换缩放，写的是屏幕上的 px
  ctx.lineJoin = "round"; ctx.lineWidth = 5 / u; ctx.strokeStyle = "#ffffff"; ctx.stroke();
  ctx.shadowColor = "transparent"; ctx.fillStyle = "#111111"; ctx.fill();
  ctx.restore();
}
```

## 已知坑

- **界面字太小**：1080p 横屏要读的字至少 44 px（`playbook/03-motion-design.md` §4），网页正文却只有 14–16 CSS px。画面里的字号 = CSS 字号 × 1.5（1280 宽的视口）× 推近倍数：16 px 的字要推到约 1.85 倍。只有一个数要读时，用 `zoom-callout` 单独放大。只当背景、没人需要读的界面字不算。`bin/vh textcheck` 量不到截图里的字，要自己算。
- **截图里还在动**：轮播、加载转圈、闪烁的输入光标，让前后两张对不上，换页时跳一下。截之前注入关动画的 CSS，等网络空闲和字体；页面一直有请求、等不到空闲时，改等某个元素出现（`locator.waitFor()`）。
- **一推近就糊**：截图是 1 倍的。按 3 倍截，推近不超过 2 倍。
- **镜头追光标**：每一下小移动都跟，看着晕。镜头只在页面变了、要看的区域变了时改目标，光标在画面里走动时镜头不动。
- **光标跟着镜头变大**：光标画进了被推近的那一层。先算出它在屏幕上的位置，再按固定大小画在最上面。
- **光标压着结果**：点完光标停在原地，正好盖住按钮上变出来的勾。结果就在光标底下时，换页后 0.2 s 把光标挪到旁边的空白处（0.4 s 左右），镜头不动。
- **假滚动**：用交叉淡入假装滚动，内容会跳。截整页长图，按滚动距离平移，0.5–0.8 s，首尾缓。页面有吸顶导航时，把导航单独截一条，叠在最上面不动。

## 验收帧

- `peak`（第 60 帧）：页面已经换成第二张，镜头正在推近；光标还在刚点的位置，大小和推近前一样。
- `settle`（第 84 帧）：镜头停稳，要读的标题在画面里、够大；光标停在一边，不压字。

## 来源

改写自 Meng To 的 MengTo/Skills（MIT）里的 `browser-video-recording`：取材的纪律（只截浏览器内容，量出每个点击和滚动目标的坐标）、运动的规矩（光标少走直线、停稳再点、页面在点击之后变、点击只缩一下不加光圈、镜头比光标沉稳）、点击缩放和倾斜的幅度（缩 15%，按水平速度最多 8°）、换页的 0.18 s 淡入，以及"状态图加光标关键帧、镜头关键帧"的数据形状。本仓库改了这些：

- 光标路径、点击和镜头换成 `components/lib` 的 `cursorPath`、`presses` 和 `track`（弹簧），镜头只在换页时改目标，不再逐个写关键帧；
- 倾斜的方向改成尾巴拖在后面（上游是朝运动方向甩）；
- 加了截图倍率（3 倍）和字号下限的算法、隐私和素材登记，滚动改成整页长图平移（上游用带位移的交叉淡入）；
- 上游用绿、品红两次全屏截图抠出系统光标，这里自己画；上游出 60 fps、4:3 的 4K，这里按片子的规格出。

草图是本仓库写的灰盒。

**许可**：本文件修改自 [MengTo/Skills](https://github.com/MengTo/Skills) 在 commit `a45892d` 时的 `agent-skills/codex/browser-video-recording/SKILL.md` 和 `agent-skills/codex/browser-video-recording/scripts/render_browser_demo.py`（Copyright (c) 2026 Meng To，MIT），改了什么见上一段。来自上游的部分仍按 MIT 授权，许可全文见 [`LICENSES/MIT-Skills.txt`](../LICENSES/MIT-Skills.txt)；本仓库的改动按仓库根目录的 MIT 许可。所有改编文件和上游出处的清单见 [`NOTICE.md`](../NOTICE.md)。
