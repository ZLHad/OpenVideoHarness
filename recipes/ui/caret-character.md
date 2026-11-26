---
id: caret-character
name: 光标是个角色
one_liner: 终端里的光标换成一个小角色，字从它身后一个个落下；换行时它跳到下一行开头，报错那一下它被撞倒，修好了再跳起来，镜头始终跟着它所在的那一行
family: ui
role: [feature]
intent: [process, interact]
energy: 3
duration_f: [90, 600]
types: [tutorial, promo, short]
engines: [canvas, hyperframes]
aspect: [landscape, portrait]
needs: [text]
sound: recommended
pitfalls: [copy-drift, too-fast, text-blur]
qa: {peak: 66, settle: 126}
status: battle-tested
max_per_film: 1
pairs_with: [ime-typing, terminal-run]
derived_from: []
sketch_sha: "b959cd2a464b"
---

# 光标是个角色 · caret-character

## 意图

安装、构建、一次检查，终端里一屏一屏的输出本身没有戏：观众只看到字往上滚。把光标块换成一个角色（产品的图标、片子里的讲解员，一个圆角方块带两只眼睛就够），输出就有了一个"正在走过去"的东西：哪一行是现在的、哪一行出错了、哪一行修好了，看它在哪、什么姿势就知道，不用读完每一行。输出照抄真实的一次运行，角色只是把它演出来。

和 `terminal-run` 的区别：那张是终端的标准写法，光标就是光标；这张一支片子用一次，放在要讲"它替你一步步做完"的那一段。

## 阶段与时值

| 段 | 帧 | 发生什么 |
|---|---|---|
| 贴进命令 | 0–10 | 命令整行出现、亮一层底色，0.6 s 后用 0.7 s 褪掉；角色站在行尾 |
| 跳行 | 每次 8 帧 | 下一行开始前 0.28 s，角色沿抛物线从上一行的尾巴跳到新一行的开头，起跳压扁、落地回弹 |
| 跑 | 按输出长度 | 字从它身后落下（每个字在角色身后 5 个字的距离里从 16 px 高处落定、淡入）；它微微前倾，脚下有几粒尘 |
| 报错 | 约 12 帧 | 红色一行出来时屏幕红闪一下（< 0.25 s，一次）、画面抖 0.4 s，角色向后倒、头上一个"!" |
| 修好 | 按输出长度 | 修复那一行出来，它跳起来，接着跑到最后一行 |
| 停 | ≥ 30 帧 | 最后一行（结论）停着可读，角色站定眨眼 |

## 参数

| 参数 | 值 | 调节手感 | ★ |
|---|---|---|---|
| 输出 | 照抄真实的一次运行；太长就截中间，用"…"标出 | 编一行"✓ all good"，是编造 | ★ |
| 出字速度 | 普通输出每秒 60–110 个字符；结论行慢一点（每秒 30–40） | 一下全出来，角色就没有路可跑 | |
| 跳行 | 0.28 s，抛物线高约 1.3 个行高 | 太快读作瞬移 | |
| 镜头 | 跟着当前行上下走（0.3 s 缓入缓出），横向只跟一点（最多 80 px） | 横向也死跟，看着晕 | |
| 错误的样子 | 红字、红闪一次、抖 0.4 s、角色倒下 | 每行都抖，就没有"这一下出事了" | |
| 字号 | 按"在哪看"的下限（desktop 44 px），镜头推近后再大一点 | | ★ |

## 声音

跳行一声轻的"跳"，每行输出一声很轻的"出行"，错误一声低的撞击，修好一声上扬的"叮"。全片配音时，这一段的旁白落在报错和修好两处，其余让声音和画面自己走。

## 风格适配

- 结构参数（跟配方走）：贴进、跳行、跑、报错、修好、停；字落在角色身后。
- 皮肤参数（跟风格走）：角色的样子、终端的配色、像素风或平面。
- 量化风格（像素、12 fps）：跳行取整到 2 帧，抛物线保持，落字改成整字出现。

## 实现

```js
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib, bg = lib.color(tokens, "bg"), fg = lib.color(tokens, "fg"), ac = lib.color(tokens, "accent");
  ctx.fillStyle = lib.mixColor(bg, "#000000", 0.35); ctx.fillRect(0, 0, W, H);
  // the output, as a real run printed it (a stand-in here): [when, text, chars a second, kind]
  const LN = [[0.3, "$ curl -fsSL …/install.sh | bash", 0, "paste"], [0.9, "→ checking git, node, python, ffmpeg", 70, ""],
    [1.9, "✗ ffmpeg is missing: brew install ffmpeg", 80, "err"], [2.9, "✓ ffmpeg installed", 50, "ok"], [3.6, "✓ ready", 30, "ok"]];
  const FS = 48, LH = 110, X0 = 170, Y0 = 330; lib.setFont(ctx, tokens, "mono", FS); const cw = ctx.measureText("M").width;
  const head = (l, at) => X0 + cw * (l[2] ? Math.min(l[1].length, Math.max(0, (at - l[0]) * l[2])) : l[1].length);
  let k = 0; LN.forEach((l, i) => { if (t >= l[0] - 0.28) k = i; });
  const err = LN[2][0], shake = t > err && t < err + 0.4 ? 14 * (1 - (t - err) / 0.4) : 0;
  const camY = lib.lerp(Y0 + (k - 1) * LH, Y0 + k * LH, lib.tween(t, LN[k][0] - 0.28, LN[k][0] + 0.02, lib.ease.inOutCubic));
  ctx.save(); ctx.translate(shake * Math.sin(t * 90), 540 - camY + shake * Math.cos(t * 70));
  ctx.fillStyle = lib.mixColor(bg, fg, 0.06); ctx.beginPath(); ctx.roundRect(110, Y0 - 120, 1700, LN.length * LH + 200, 26); ctx.fill();
  LN.forEach((l, i) => {
    if (t < l[0]) return;
    const y = Y0 + i * LH, col = l[3] === "err" ? "#e85a50" : l[3] === "ok" ? "#8fbf95" : fg, p = l[2] ? (t - l[0]) * l[2] : 1e9;
    if (l[3] === "paste") { ctx.globalAlpha = 0.45 * (1 - lib.seg(t, l[0] + 0.6, l[0] + 1.3)); ctx.fillStyle = ac; ctx.fillRect(X0 - 8, y - FS, head(l, t) - X0 + 16, FS * 1.3); }
    [...l[1]].forEach((c, j) => { const a = lib.clamp((p - j) / 5); if (a <= 0) return; ctx.globalAlpha = (i === k ? 1 : 0.7) * a; ctx.fillStyle = col; ctx.fillText(c, X0 + j * cw, y - 16 * (1 - a)); });
    ctx.globalAlpha = 1;
  });
  // the character: on the line's head; between lines it hops on an arc; the error knocks it back
  const l = LN[k], hop = lib.seg(t, l[0] - 0.28, l[0]), prev = LN[Math.max(0, k - 1)];
  let x = head(l, t) + 54, y = Y0 + k * LH, lift = 0, rot = 0, sq = 0;
  if (k > 0 && hop < 1) { x = lib.lerp(head(prev, l[0] - 0.28) + 54, X0 + 30, lib.ease.inOutCubic(hop)); y = lib.lerp(Y0 + (k - 1) * LH, y, hop); lift = 4 * hop * (1 - hop) * 140; sq = hop < 0.15 ? 0.18 : 0; }
  const down = t > err + 0.3 && t < LN[3][0] - 0.3; if (down) rot = 0.5; else if (l[2] && t < l[0] + l[1].length / l[2]) rot = 0.08 * Math.sin(t * 24);
  ctx.save(); ctx.translate(x, y - 6 - lift); ctx.rotate(rot); ctx.scale(1 + sq, 1 - sq);
  ctx.fillStyle = ac; ctx.beginPath(); ctx.roundRect(-38, -78, 76, 72, 18); ctx.fill();
  const blink = (t * 0.37) % 1 > 0.96 ? 0.15 : 1; ctx.fillStyle = bg; [-14, 14].forEach((ex) => { ctx.beginPath(); ctx.ellipse(ex, -46, 6, 10 * blink, 0, 0, Math.PI * 2); ctx.fill(); });
  ctx.restore();
  if (down) { lib.setFont(ctx, tokens, "display", 80, { weight: 800 }); ctx.fillStyle = "#e85a50"; ctx.fillText("!", x - 14, y - 110); }
  ctx.restore();
  if (t > err && t < err + 0.22) { ctx.fillStyle = `rgba(232,90,80,${0.28 * (1 - (t - err) / 0.22)})`; ctx.fillRect(0, 0, W, H); }
}
```

做片子时，输出和时间用组件 `components/ui-stage` 的 `lines`（`how: "paste"`、`"print"`）排，角色另画在 `planLine()` 给出的行头上：组件管字什么时候出，角色只读它。

## 已知坑

- 输出是编的 → 在一个隔离的环境里真跑一遍（新的 HOME、去掉某个依赖的 PATH 才跑得出"缺什么"那一句），照抄。
- 角色挡住正在出的字 → 它站在字头前面 50–60 px，字从它身后出，不压在字上。
- 每一行都给角色加戏 → 只在报错、修好、最后一行三处有动作，其余只是跑。
- 镜头跟得太死 → 只跟行（纵向），横向最多挪 80 px。
- **判例**：一支 5 分 17 秒的使用教程（2026-11）的安装一段。第一版终端只是一行行出字，用户看小样说终端这一部分"可以润色优化一下"、整体"太平铺直叙"；改成产品图标里的小方块当光标、在终端里跑以后，初版那一关用户没有再提终端，只要求整体停顿放长。

## 验收帧

- `peak`（第 66 帧）：报错那一行出来，角色倒着、头上有"!"，红闪已经过去，字清楚。
- `settle`（第 126 帧）：最后一行结论出完，角色站定在它后面，镜头停住。

## 来源

本仓库原创：从一支 2026-11 的使用教程的安装一段提炼。草图里的输出是照安装程序的样子写的占位，用时换成真实运行的输出。
