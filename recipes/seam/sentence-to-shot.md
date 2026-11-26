---
id: sentence-to-shot
name: 一句话散开，落成新镜头
one_liner: 人打给 agent 的那句意见发出去以后，句子本身的笔画碎成几千个点，按从左到右的顺序起飞，沿弧线落进改好的镜头的形状里；新画面在点下面亮起来，点淡去，镜头交给改完的版本
family: seam
role: [seam, climax]
intent: [transform, payoff, carry]
energy: [3, 5]
duration_f: [60, 105]
jump: [rise]
types: [tutorial, promo, short]
engines: [canvas, three]
aspect: [landscape, portrait, square]
needs: [text, footage]
sound: recommended
pitfalls: [no-hold, text-blur, overuse]
qa: {seam: 45, settle: 96}
status: battle-tested
max_per_film: 2
pairs_with: [ime-typing]
derived_from: []
sketch_sha: "43cc7b0bb13b"
---

# 一句话散开，落成新镜头 · sentence-to-shot

## 意图

教程里最要紧的一刻常常是"说了一句，它就改了"。直接切到改好的画面，观众看见的是两个镜头；让那句话自己变成新画面，观众看见的是因果：这一句，变成了这个。点是从句子的像素里取的、落点是从新画面里取的，所以起点认得出是那句话，终点认得出是新镜头。

## 阶段与时值

| 段 | 帧 | 发生什么 |
|---|---|---|
| 句子停住 | 0–18 | 句子已经打完、回车，停一拍，让人读完（读的时间按字数算，不够就加） |
| 碎开 | 18–30 | 笔画碎成点，从左边的字先起，左右错开约 0.4 s |
| 飞 | 30–60 | 每个点各飞 0.9 s（outCubic），沿一条往上拱的弧线；整团在中段最散 |
| 落定 | 55–75 | 点落进新画面的形状（一句大字、一个主体的轮廓），新画面在下面从暗到亮 |
| 交接 | 75–105 | 点淡去，新画面接管，之后照常播放 |

## 参数

| 参数 | 值 | 调节手感 | ★ |
|---|---|---|---|
| 点数 | 1080p 约 4000–5500（教程片用 5200），每隔 3 px 取一次样 | 太少认不出字，太多一团雾 | |
| 起飞错开 | 按点的起点横坐标，从左到右约 0.4 s | 同时起飞读作爆炸，不是"一句话被读走" | ★ |
| 单点飞行 | 0.9 s，outCubic，弧线拱起 80–200 px（按种子） | 直线飞读作吸进去 | |
| 落点 | 新画面里认得出的形状：改动要求的那几个字，或主体的轮廓 | 落进一片随机的点，等于没有终点 | ★ |
| 句子停住多久 | ≥ 读一遍的时间（`bin/vh readcheck` 的下限） | 没读完就碎了，观众不知道刚才说了什么 | ★ |
| 新画面亮起 | 落定前 0.3 s 开始，0.5 s 亮满 | 点落完画面才亮，中间有一帧空 | |

一支片子用一两次：最重要的那一处改动用它，其余的改动直接切、或者并排对比。

## 声音

碎开一声细碎的高频（像纸屑），飞的时候一层很轻的上升音，落定那一下和新画面的第一个重音对齐。

## 风格适配

- 结构参数（跟配方走）：停住、从左到右起飞、弧线、落进新形状、新画面在下面亮起。
- 皮肤参数（跟风格走）：点的颜色（取原字的颜色或强调色）、大小、拖不拖尾。
- 量化风格（像素）：点改成方块，位置取整到像素格，飞行照旧。

## 实现

点的起点和落点都从画出来的像素里取：把句子和目标形状各画进一张离屏画布，`getImageData` 取不透明的像素，再用种子挑。只和参数有关，所以按文字缓存一次，帧与帧之间不留别的状态。

```js
const CACHE = new Map();   // the points of a drawing, by what was drawn: depends on the inputs only
function pointsOf(key, draw, n, seed, lib) {
  if (!CACHE.has(key)) {
    const c = document.createElement("canvas"); c.width = lib.W; c.height = lib.H; const x = c.getContext("2d", { willReadFrequently: true });
    draw(x); const d = x.getImageData(0, 0, lib.W, lib.H).data, px = [];
    for (let y = 0; y < lib.H; y += 3) for (let i = 0; i < lib.W; i += 3) if (d[(y * lib.W + i) * 4 + 3] > 120) px.push([i, y]);
    CACHE.set(key, Array.from({ length: n }, (_, k) => px[Math.floor(lib.hash(seed, k) * px.length)]));
  }
  return CACHE.get(key);
}
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib, bg = lib.color(tokens, "bg"), fg = lib.color(tokens, "fg"), ac = lib.color(tokens, "accent");
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  const SAY = "画面更震撼一点，字要有“出发”", N = 2600, t0 = 1.6;
  const font = (x, px) => { x.font = `700 ${px}px ${lib.fontStack(tokens, "zh")}`; };
  const from = pointsOf("say", (x) => { font(x, 72); x.fillStyle = "#fff"; x.fillText(SAY, 260, 420); }, N, 1, lib);
  const to = pointsOf("go", (x) => { font(x, 420); x.fillStyle = "#fff"; x.textAlign = "center"; x.fillText("出发", W / 2, 700); }, N, 2, lib);
  // the new shot comes up under the points
  const up = lib.tween(t, t0 + 1.0, t0 + 1.5, lib.ease.outCubic);
  if (up > 0) { const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, lib.mixColor(bg, ac, 0.35 * up)); g.addColorStop(1, bg); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = up; font(ctx, 420); ctx.textAlign = "center"; ctx.fillStyle = fg; ctx.fillText("出发", W / 2, 700); ctx.textAlign = "left"; ctx.globalAlpha = 1; }
  // the sentence, typed and held, until it breaks
  if (t < t0 + 0.2) { font(ctx, 72); ctx.fillStyle = fg; ctx.fillText(lib.typewriter(SAY, t, { start: 0.1, cps: 14 }), 260, 420); }
  if (t < t0 + 0.2) return;
  // each point leaves by its x (left first, 0.4 s across), flies 0.9 s on an arc, and fades once the shot is up
  const fade = 1 - lib.seg(t, t0 + 1.7, t0 + 2.2);
  ctx.fillStyle = ac;
  for (let k = 0; k < N; k++) {
    const [x0, y0] = from[k], [x1, y1] = to[k], s = t0 + 0.4 * ((x0 - 260) / 1400), u = lib.ease.outCubic(lib.seg(t, s, s + 0.9));
    if (u <= 0) { ctx.globalAlpha = fade; ctx.fillRect(x0 - 2, y0 - 2, 4, 4); continue; }
    const arc = (80 + 120 * lib.hash(3, k)) * 4 * u * (1 - u), x = lib.lerp(x0, x1, u), y = lib.lerp(y0, y1, u) - arc;
    ctx.globalAlpha = fade * (0.7 + 0.3 * lib.hash(4, k)); const r = 3.5 + 4 * Math.sin(Math.PI * u); ctx.fillRect(x - r / 2, y - r / 2, r, r);
  }
  ctx.globalAlpha = 1;
}
```

在三维里做时（教程片的那一处用了 Three.js），点换成一个 `Points`，起点和落点算法照旧，落点取新画面里那几个字在三维空间里的位置。

## 已知坑

- 句子没读完就碎 → 句子停住的时长按读时算；人原话很长时，屏上只打要紧的那半句，另一半交给字幕。
- 新画面里那几个字（改动要求的东西），在这一镜之前已经露过 → 揭晓就不成立。站牌、导览、快闪、片头的成果墙里最容易漏，做之前在全片的镜头表里搜一遍那个画面。
- 改完的画面只放一遍就切走 → 落定以后让新画面完整地走一遍（教程片里这一处只放画面、不配旁白，停了约 4 s）。
- 点的颜色和新画面打架 → 点用原字的颜色，落定前一刻再变成新画面那几个字的颜色。
- **判例**：一支 5 分 17 秒的使用教程（2026-11），"说一句，改一个镜头"那一段：人当时打的那句意见逐字打出，字散成光点，在天上拼成新版的大字。初版那一关用户说中间那一大段问题不大；独立评审指出新版画面在前面的站牌和导览里提前露过，改成同一支片子别的章节后，揭晓才成立。

## 验收帧

- `seam`（第 45 帧）：点在半路，左边的已经快落定、右边的还在弧顶，新画面还没亮。
- `settle`（第 96 帧）：新画面完全接管，点已经淡完，落进去的字清楚。

草图前面多了 1 s 打字，所以草图的时刻 = 配方的帧 ÷ 30 + 1 s（`seam` 在草图的 2.5 s，`settle` 在 4.2 s）。

## 来源

本仓库原创：从一支 2026-11 的使用教程里"一句话改一个镜头"那一处提炼。草图里的句子和目标字是占位，用时换成人真打的那句话和真的新画面。
