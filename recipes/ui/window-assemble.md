---
id: window-assemble
name: 真窗口一块块拼起来
one_liner: 产品的图标落下、被双击，一下亮光，名字从画面中间冲过去；它的真窗口按自己的分区切成几块，从各自的方向带着纵深弹进来、错开 0.13 s，主画面最后从镜头这边落进去，整窗转正，一道光扫过，里面的内容开始动
family: ui
role: [hero, open]
intent: [hero, brand-imprint, transform]
energy: 4
duration_f: [60, 135]
types: [tutorial, promo]
engines: [canvas, hyperframes, three]
aspect: [landscape]
needs: [ui-page, logo]
sound: recommended
pitfalls: [float-not-land, mechanical-stop, flash-rate, text-blur]
qa: {peak: 51, settle: 120}
status: battle-tested
max_per_film: 1
pairs_with: [step-capture, card-to-workspace]
derived_from: []
sketch_sha: "1728ca0c8695"
---

# 真窗口一块块拼起来 · window-assemble

## 意图

教程讲到"现在打开它"的那一刻，是产品第一次完整露面，值得一个揭晓。窗口一下子出现，观众只看到一张截图；按产品自己的分区（顶栏、侧栏、主画面、时间线、右栏）一块块拼起来，观众顺便知道了它由哪几块组成，后面讲"左边这一列""中间是""右边"时，脑子里已经有这张图。每一块都是真截图切出来的，拼完就是那张真窗口。

## 阶段与时值

| 段 | 帧 | 发生什么 |
|---|---|---|
| 图标 | 0–15 | 图标从上方弹落（弹簧，过冲 ≤ 5%），一圈轮廓光在呼吸 |
| 双击 | 18–24 | 两下按压，间隔 0.17 s，图标各缩一下 |
| 打开 | 24–33 | 图标放大、淡去；一下亮光（只此一次，0.17 s 衰到一半）；产品名从画面深处冲过来、变淡，退到后面 |
| 拼 | 33–75 | 各块从自己的方向和纵深弹进来，错开 0.13 s；主画面最后从镜头这一侧落进去；整窗从斜着转正（约 1.8 s） |
| 扫光 | 75–100 | 一道斜的光从左扫到右 |
| 活过来 | 100– | 主画面里开始播放，窗口停在正面，轻微推近 |

## 参数

| 参数 | 值 | 调节手感 | ★ |
|---|---|---|---|
| 切块 | 按产品自己的分区切（教程片切了 6 块），每块是真截图的一部分，拼完严丝合缝 | 随手切成网格，就只是转场，不讲结构 | ★ |
| 每块的弹簧 | 约 1.9 Hz、阻尼 0.68，过冲约 5% | 硬停读作机械；过冲太大像果冻 | |
| 错开 | 0.13 s 一块；主画面最后 | 同时到读作一下闪出来 | |
| 进来的方向 | 每块从离它最近的画面边进来，带 700 px 左右的纵深；主画面从镜头这边（纵深 1700 px） | 都从一个方向来，像幻灯片 | |
| 亮光 | 只在打开那一下，一次 | 每块落地都闪，超过每秒 3 次就是底线问题 | ★ |
| 落定后 | 窗口停在正面，主画面开始动，至少停 1.5 s 再讲下一句 | 拼完立刻推近讲细节，观众没看到全貌 | |

## 声音

图标落下一声轻的"嘟"，双击两下点击，打开一声低频的轰加一层上升音，每块落地一声很轻的撞击（比主音低 5 dB），扫光一声闪亮。名字可以在这里第一次被旁白念出来，念在打开那一下。

## 风格适配

- 结构参数（跟配方走）：图标、双击、打开、按分区拼、扫光、活过来。
- 皮肤参数（跟风格走）：底的颜色、阴影、亮光和扫光的颜色、名字的字体。
- 没有三维的引擎：用缩放代替纵深，用水平拉伸代替转正（草图就是这样）。

## 实现

```js
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib, bg = lib.color(tokens, "bg"), fg = lib.color(tokens, "fg"), ac = lib.color(tokens, "accent");
  ctx.fillStyle = lib.mixColor(bg, "#000000", 0.4); ctx.fillRect(0, 0, W, H);
  const tIc = 0.15, c1 = 0.62, c2 = 0.79, tB = 0.95, d = t - tB;
  const spring = (d, f = 1.9, z = 0.68) => (d <= 0 ? 0 : lib.spring(d, { w: 2 * Math.PI * f, zeta: z }));
  // the name, from deep in the frame towards the camera, then back behind the window as it builds, and gone
  if (d > 0 && d < 2.5) { const bt = lib.ease.outQuint(lib.clamp(d / 0.55)); lib.setFont(ctx, tokens, "display", 200 * lib.lerp(0.4, 1.5, bt), { weight: 800 }); ctx.textAlign = "center";
    ctx.globalAlpha = lib.clamp(d * 6) * (1 - 0.86 * lib.ease.inOutCubic(lib.seg(d, 0.62, 1.5))) * (1 - lib.seg(d, 1.8, 2.5)); ctx.fillStyle = fg; ctx.fillText("PRODUCT", W / 2, H / 2 + 60); ctx.globalAlpha = 1; ctx.textAlign = "left"; }
  // the window, cut where the product cuts itself (a stand-in of six panels here): [x, y, w, h, from dx, from dy, depth]
  const K = 1.1, OX = (W - 1440 * K) / 2, OY = (H - 900 * K) / 2;
  const PANELS = [[0, 0, 1440, 50, -600, -500, 700], [0, 50, 64, 850, -1400, 100, 700], [1080, 50, 360, 850, 1500, 0, 700],
    [64, 606, 1016, 84, 300, 900, 700], [64, 690, 1016, 210, -300, 1100, 700], [64, 50, 1016, 556, 0, -200, 1700]];
  const turn = lib.ease.inOutCubic(lib.seg(d, 0.3, 2.1));
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(lib.lerp(0.78, 1, turn) * (1 + 0.03 * lib.seg(d, 2.1, 4)), lib.lerp(0.92, 1, turn)); ctx.translate(-W / 2, -H / 2);
  PANELS.forEach(([x, y, w, h, dx, dy, depth], i) => {
    const a = d - (0.42 + i * 0.13); if (a <= 0) return;
    const k = spring(a), m = 1 - k, s = 1 + (depth / 900) * m;
    const px = OX + x * K + dx * m, py = OY + y * K + dy * m, pw = w * K, ph = h * K;
    ctx.save(); ctx.globalAlpha = lib.clamp(a * 7); ctx.translate(px + pw / 2, py + ph / 2); ctx.scale(s, s);
    ctx.fillStyle = lib.mixColor(bg, fg, i === 5 ? 0.08 : 0.16 + 0.05 * (i % 2)); ctx.fillRect(-pw / 2, -ph / 2, pw, ph);
    if (i === 5 && d > 1.4) for (let j = 0; j < 7; j++) { ctx.fillStyle = lib.mixColor(bg, ac, 0.25 + 0.2 * Math.sin((d - 1.4) * 2 + j)); ctx.fillRect(-pw / 2 + 40 + j * 140, -ph / 2 + 60 + 160 * lib.hash(j), 110, 300); }
    ctx.restore();
  });
  ctx.restore();
  // the sweep of light once every panel is in
  const sw = lib.seg(d, 1.65, 2.45);
  if (sw > 0 && sw < 1) { const x = lib.lerp(-500, W + 300, lib.ease.inOutCubic(sw)); const g = ctx.createLinearGradient(x - 200, 0, x + 200, 0); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, "rgba(255,255,255,0.3)"); g.addColorStop(1, "rgba(255,255,255,0)"); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  // the icon: drops in, two presses, grows and fades as the window opens; one flash
  if (d < 0.5) { const i0 = spring(t - tIc, 2.2, 0.5), pr = lib.presses([c1, c2])(t), ex = lib.ease.outCubic(lib.clamp(d / 0.5));
    ctx.save(); ctx.globalAlpha = 1 - ex; ctx.translate(W / 2, H / 2 + (1 - i0) * -700); ctx.scale((1 - 0.1 * pr) * (1 + 1.6 * ex), (1 - 0.1 * pr) * (1 + 1.6 * ex));
    ctx.fillStyle = lib.mixColor(bg, fg, 0.12); ctx.beginPath(); ctx.roundRect(-170, -170, 340, 340, 78); ctx.fill(); ctx.fillStyle = ac; ctx.fillRect(-40, -40, 80, 80); ctx.restore(); }
  if (d > 0) { ctx.fillStyle = `rgba(255,255,255,${0.6 * Math.exp(-d * 6)})`; ctx.fillRect(0, 0, W, H); }
}
```

做片子时，每块用真截图的那一部分当背景（`background: url(…) -x -y / W H`，或 `drawImage` 的源矩形），坐标按截图的 CSS px 乘同一个倍数；有 DOM 或 Three.js 的，纵深和转正用真的 `translateZ`、`rotateY`。

## 已知坑

- 切的块和截图对不上，拼完有缝或错位 → 每块的源矩形和落点用同一个倍数算，拼完的那一帧和整张截图逐像素比一次。
- 每块落地都闪 → 亮光只在打开那一下；落地用很淡（≤ 12%）的一下提亮，或者不提。
- 名字和窗口同时占着画面中心，谁也看不清 → 名字先冲过来，窗口开始拼的时候它已经退到 15% 以下的浓度。
- 拼完马上讲细节 → 至少停 1.5 s 给全貌，下一句"左边这一列"再推近。
- **判例**：一支 5 分 17 秒的使用教程（2026-11），产品窗口第一次出现的那一下。小样里用户说出场要直接说产品名、"加点效果出来，节奏感有一点"；改成这一式（旁白就念产品名，配乐在打开那一下给重音）以后，初版那一关用户没有再提这一处。

## 验收帧

- `peak`（第 51 帧）：几块在半路，带着纵深和方向，名字已经淡到后面，窗口还斜着。
- `settle`（第 120 帧）：窗口拼完、转正，扫光过去了，主画面在动，没有一块错位。

## 来源

本仓库原创：从一支 2026-11 的使用教程里产品窗口的出场提炼。草图的六块是灰盒，用时换成真截图按产品分区切出来的块。
