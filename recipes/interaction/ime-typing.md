---
id: ime-typing
name: 拼音打字，键盘跟着按
one_liner: 一句中文像真人用输入法打出来：拼音字母先落在光标处、带下划线，候选框弹出，空格一按词才上屏；桌上的键盘同一时刻按下对应的键、亮一下再弹起
family: interaction
role: [feature]
intent: [interact, process]
energy: 2
duration_f: [45, 240]
types: [tutorial, promo, short]
engines: [canvas, hyperframes]
aspect: [landscape, portrait]
needs: [text]
sound: recommended
pitfalls: [too-fast, uniform-timing, copy-drift]
qa: {peak: 45, settle: 120}
status: battle-tested
pairs_with: [step-capture, caret-character]
impl: [components/ui-stage/component.js]
derived_from: []
sketch_sha: "a5d561a9cb4f"
---

# 拼音打字，键盘跟着按 · ime-typing

## 意图

教程里人对 agent、对搜索框说的那句话，观众要看见它是"打"出来的，而且是中文用户真实的打法：拼音、候选、上屏。逐字冒出来的汉字读作贴进去的，像假的；拼音和候选框一出来，观众就认出这是自己每天在做的事。键盘放进画面时，每个字母都有一次按键，声音、键、屏上的字是同一个时刻。

## 阶段与时值

| 段 | 帧 | 发生什么 |
|---|---|---|
| 就位 | 0–12 | 输入框和键盘都在，光标在闪 |
| 打一个词 | 每个字母 2–5 帧 | 字母一个个落在光标处，带一条下划线；候选框在下面，第一项就是要的词 |
| 上屏 | 字母打完后 3 帧 | 空格按下，候选消失，汉字换掉拼音；下一个词隔 2–3 帧开始 |
| 打完、回车 | 最后一个词后 9 帧 | 停一拍再按回车，键盘上回车亮 |
| 停 | 回车后 ≥ 30 帧 | 整句停着，读的时间按字数给 |

## 参数

| 参数 | 值 | 调节手感 | ★ |
|---|---|---|---|
| 字母速度 | 每秒 14–18 个，每个字母的间隔在 0.6–1.4 倍之间按种子抖 | 匀速读作机器；超过每秒 25 个读作快进。一句话必须在旁白那几个字之内打完时可以提到每秒 30 左右（教程片里最快用到 31） | ★ |
| 上屏 | 最后一个字母后 0.09 s 按空格 | 不停就上屏，候选框只闪一帧，看不出是输入法 | |
| 词与词之间 | 0.05–0.10 s | | |
| 键的按下和弹起 | 字母出现前 0.05 s 按下，0.32 s 弹起；按下时下沉、换强调色并发光 | 弹得太快，键盘上只看得到闪 | |
| 回车 | 打完后停 0.25 s 再按 | 打完立刻回车，像预录的 | |
| 字号 | 输入框里的字按"在哪看"的下限（desktop 44 px），候选框比正文小一点点 | | ★ |
| 打的内容 | 照抄人真说过的那句话；数字、英文名按原样 | 编一句更顺口的，等于编原话 | ★ |

拼音写全拼，不写声调；英文词和数字直接打，不走候选（组件里一个部分的汉字和拼音相同、或只有一个字母，就直接上屏）。

## 声音

每个字母一声键盘，至少 6–9 个不同的键声轮换、电平上下差 2 dB，否则听起来像机关枪；空格重一点，回车最重。音效时间从同一份计划里取（`ui-stage` 的 `events()`），不要另写一张表。

## 风格适配

- 结构参数（跟配方走）：字母、候选、空格上屏、键盘同步、回车前的停顿。
- 皮肤参数（跟风格走）：输入框和候选框的样子、键帽的颜色、按下时发的光。
- 量化风格（一拍二）：字母时间取整到 2 帧，但每个字母仍然是一帧帧可见的，候选框至少停 2 帧。

## 实现

做片子时用组件 `components/ui-stage`：一行写成 `{ at, how: "ime", parts: [["把开头", "bakaitou"], …], enter: true }`，加上 `keyboard: { x, y, w }`。下面的草图把同一件事写短了，只为说明时序。

```js
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib, bg = lib.color(tokens, "bg"), fg = lib.color(tokens, "fg"), ac = lib.color(tokens, "accent");
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  // the plan: letters at 16 a second, uneven by a seed; a space 0.09 s after a word's last letter commits it
  const PARTS = [["把开头", "bakaitou"], ["那一镜", "nayijing"], ["改亮一点", "gailiangyidian"]], keys = [];
  let tt = 0.4;
  const plan = PARTS.map(([hz, py], k) => {
    const a = [];
    for (let j = 0; j < py.length; j++) { tt += (1 / 16) * (0.6 + 0.8 * lib.hash(3, k, j)); a.push(tt); keys.push([tt, py[j]]); }
    tt += 0.09; keys.push([tt, " "]); const e = tt; tt += 0.05 + 0.05 * lib.hash(3, k, 99);
    return { hz, py, a, e };
  });
  const enter = tt + 0.25; keys.push([enter, "⏎"]);
  let done = "", comp = "", cand = "";
  for (const s of plan) { if (t >= s.e) { done += s.hz; continue; } const n = s.a.filter((v) => t >= v).length; if (n) { comp = s.py.slice(0, n); cand = s.hz; } break; }
  // the input box
  const sent = lib.tween(t, enter, enter + 0.35, lib.ease.outCubic), X = 300, Y = 170;
  ctx.fillStyle = lib.mixColor(bg, fg, 0.1); ctx.beginPath(); ctx.roundRect(X - 40, Y - 20, 1400, 170, 24); ctx.fill();
  lib.setFont(ctx, tokens, "zh", 64); ctx.fillStyle = fg; ctx.fillText(done, X, Y + 92 - 40 * sent);
  let cx = X + ctx.measureText(done).width;
  if (comp) {
    lib.setFont(ctx, tokens, "mono", 58); const cw = ctx.measureText(comp).width; ctx.fillText(comp, cx, Y + 92); ctx.fillStyle = ac; ctx.fillRect(cx, Y + 104, cw, 4);
    lib.setFont(ctx, tokens, "zh", 52); const bw = ctx.measureText(`1 ${cand}   2 ${cand[0]}`).width + 60;
    ctx.fillStyle = lib.mixColor(bg, fg, 0.9); ctx.beginPath(); ctx.roundRect(cx - 10, Y + 130, bw, 84, 14); ctx.fill();
    ctx.fillStyle = bg; ctx.fillText(`1 ${cand}   2 ${cand[0]}`, cx + 20, Y + 190); cx += cw;
  }
  if (t < enter && (comp || lib.step(t, 4) * 4 % 2 === 0)) { ctx.fillStyle = fg; ctx.fillRect(cx + 6, Y + 40, 30, 64); }
  if (sent > 0) { lib.setFont(ctx, tokens, "mono", 44); ctx.globalAlpha = sent; ctx.fillStyle = ac; ctx.fillText("⏎ sent", X + 1100, Y + 92); ctx.globalAlpha = 1; }
  // the keyboard: three rows and a space bar; a key goes down 0.05 s before its letter and comes back over 0.32 s
  const ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"], kw = 112, kh = 100, gap = 14, KY = 560;
  const down = (c) => { let v = 0; for (const [kt, k] of keys) { const d = t - kt; if (k === c && d > -0.05 && d < 0.32) v = Math.max(v, d < 0 ? 1 + d / 0.05 : 1 - d / 0.32); } return v; };
  const key = (x, y, w, label, v) => {
    ctx.fillStyle = lib.mixColor(bg, "#000000", 0.5); ctx.beginPath(); ctx.roundRect(x, y + 8, w, kh, 14); ctx.fill();
    ctx.fillStyle = lib.mixColor(lib.mixColor(bg, fg, 0.28), ac, v); ctx.beginPath(); ctx.roundRect(x, y + 7 * v, w, kh, 14); ctx.fill();
    lib.setFont(ctx, tokens, "mono", 40); ctx.fillStyle = v > 0.4 ? bg : fg; ctx.textAlign = "center"; ctx.fillText(label, x + w / 2, y + 7 * v + 64); ctx.textAlign = "left";
  };
  ROWS.forEach((r, i) => { const x0 = (W - (r.length * (kw + gap) - gap)) / 2 + i * 30; [...r].forEach((c, j) => key(x0 + j * (kw + gap), KY + i * (kh + gap), kw, c.toUpperCase(), down(c))); });
  key((W - 760) / 2, KY + 3 * (kh + gap), 760, "", down(" ")); key((W + 800) / 2, KY + 3 * (kh + gap), 200, "⏎", down("⏎"));
}
```

## 已知坑

- 汉字一个个直接冒出来 → 读作贴的，不是打的；中文一律走拼音和候选。英文命令照常逐字打。
- 键盘的键和屏上的字差几帧 → 两边从同一份计划里取时间（组件的 `planLine`），不要各写一份。
- 打字比旁白念得慢，句子说完了还在打 → 打字从旁白说到"打了一句"前后开始，字母速度按"念完之前打完"倒推，最快到每秒 30 个左右；再快就删短要打的内容，不加速成一闪。
- 光标在打字时也闪 → 打字时实心，停下来才闪（每秒约 1.9 次）。
- **判例**：一支 5 分 17 秒的使用教程（2026-11）。分镜那一关用户要求"有鼠标、有打字机"、"真正的好像就在操作"；这一式和键盘一起用在安装、给素材和改稿几处，初版那一关用户说中间那一大段问题不大，没有再提打字。

## 验收帧

- `peak`（第 45 帧）：第二个词在拼：下划线的拼音、候选框、键盘上亮着一个键，三样同时看得见。
- `settle`（第 120 帧）：整句已上屏、回车已按，键盘全部弹起，句子停着可读。

## 来源

本仓库原创：从一支 2026-11 的使用教程里的输入法打字和键盘提炼。参数是那支片子里用的值。
