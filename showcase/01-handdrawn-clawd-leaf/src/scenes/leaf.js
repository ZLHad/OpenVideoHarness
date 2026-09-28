// leaf.js: "Clawd and the Leaf", 12 s. Shots, reads and timings are in STORYBOARD.md.
//   A (0–4.0):   a viewfinder opens on a golden leaf; Clawd films it falling; a gust snatches it; Clawd turns and bolts.
//   B (4.0–8.2): the leaf settles on a pumpkin; Clawd sneaks up and frames it; gust #2 takes it; Clawd stomps, turns the
//                camera round and peers into the lens; the camera pushes into the lens.
//   C (8.2–12):  POV through the viewfinder: Clawd's face; the leaf lands on its head; Clawd notices, delights, waves;
//                the viewfinder closes on it.
(() => {
  // ---------- palette (see STYLE.md) ----------
  const K = {
    skyA: '#C9D7E6', skyB: '#C9CCE0', skyC: '#BBA6C6',
    warmA: '#F0CDA2', warmB: '#EDC1A4', warmC: '#F2AA66',
    hillFar: '#B99DA8', hillMid: '#99976A',
    meadow: '#C4A553', meadowDk: '#977B33',
    trunk: '#6E4A3A', trunkDk: '#4E3329',
    crown: ['#C4553A', '#D9773E', '#A8452F', '#CE6A3C'],
    leaf: '#F2B632', leafFill: '#E3862A', vein: '#B0602A',
    pumpkin: '#D9692E', pumpkinDk: '#A9481F', stem: '#6B6A34', squash: '#7E978A', squashDk: '#56705F',
    walnut: '#7B4B33', camDk: '#4A3036', brass: '#D9A441', reel: '#5E4038',
    wind: '#9C8FA8', rec: '#D8394E',
  };
  const PI = Math.PI;

  // ---------- the hero leaf: a maple leaf, stem down, about 2r tall ----------
  const LEAF_SHAPE = (() => {
    const lobes = [[-PI / 2, .5, .72], [-PI / 2 + 1.25, .36, .7], [-PI / 2 - 1.25, .36, .7], [-PI / 2 + 2.3, .16, .6], [-PI / 2 - 2.3, .16, .6]];
    const P = [];
    for (let i = 0; i < 60; i++) {
      const a = -PI / 2 + i / 60 * TAU;
      let r = .5;
      for (const [la, h, w] of lobes) { const d = Math.abs((((a - la + PI) % TAU) + TAU) % TAU - PI); r += h * Math.pow(Math.max(0, 1 - d / w), 1.25); }
      r += .045 * Math.abs(Math.sin(a * 13)) * (r > .62 ? 1 : .25);   // serrated edge
      P.push([Math.cos(a) * r * .95, Math.sin(a) * r * .88 + .08]);
    }
    return P;
  })();
  // (x, y) is the leaf's centre; the stem tip is at (0, .95r) in leaf space.
  function drawLeaf(x, y, r, rot = 0, o = {}) {
    const sw = o.sw ?? clamp(r / 45, .3, 1.1);
    push(); translate(x, y); rotate(rot); scale(o.sx ?? 1, o.sy ?? 1);
    paint(LEAF_SHAPE.map(([a, b]) => [a * r, b * r]), { wash: K.leaf, fill: K.leafFill, fillOp: 105, bleed: .12, tex: .6, border: .5, ink: PAL.ink, sw });
    const base = [0, .42 * r];
    for (const a of [-PI / 2, -PI / 2 + 1.15, -PI / 2 - 1.15]) inkLine([base, [Math.cos(a) * .62 * r, Math.sin(a) * .62 * r + .12 * r]], sw * .6, K.vein, 'inkfine', 0);
    inkLine([base, [.1 * r, .8 * r], [.02 * r, 1.12 * r]], sw * 1.1, PAL.ink, 'ink', .6);
    pop();
  }
  // A leaf falling like a leaf: it rocks side to side on a pendulum arc, lifting a little at each end of the swing and
  // tilting toward where it's going. s = seconds since release. Returns [dx, dy, rot] to add to a drifting centre.
  function rock(s, amp = 60, period = 1.2, lift = 16) {
    const a = amp * clamp(s / .45), ph = s / period * TAU, sw = Math.sin(ph);
    return [a * sw, -lift * sw * sw * clamp(s / .45), .55 * Math.cos(ph) * clamp(s / .45)];
  }

  // ---------- the tiny hand-cranked movie camera ----------
  // Drawn around the hand that holds it at (0, 0), lens toward +x, the hand under the body's back half.
  // spin 0..1 turns it round through drawn key views (lens right → lens at the viewer → lens left), mirrored about its
  // own middle so it stays in the hand. crank = crank angle in radians (it turns while filming).
  function movieCam(s, o = {}) {
    const sw = o.sw ?? clamp(s / 16, .4, 1.6), crank = o.crank || 0, sp = o.spin || 0;
    const view = sp < .34 ? 'side' : sp < .67 ? 'front' : 'back';
    push(); translate(0, -.8 * s);
    if (view === 'back') { translate(1.3 * s, 0); scale(-1, 1); }
    if (view === 'front') {
      paint(ellPts(.65 * s, -1.42 * s, .17 * s, .62 * s, 14), { wash: K.reel, ink: PAL.ink, sw: sw * .7 });
      paint(rrPts(-.25 * s, -.8 * s, 1.8 * s, 1.6 * s, .22 * s), { wash: K.walnut, fill: K.camDk, fillOp: 70, tex: .6, ink: PAL.ink, sw });
      paint(ellPts(.65 * s, 0, .6 * s, .6 * s, 20), { wash: K.brass, ink: PAL.ink, sw: sw * .7 });
      paint(ellPts(.65 * s, 0, .44 * s, .44 * s, 18), { wash: PAL.ink, ink: null });
      inkLine([[.45 * s, -.2 * s], [.58 * s, -.3 * s], [.72 * s, -.32 * s]], sw * .6, PAL.cream, 'inkfine', .5);
      inkLine([[1.55 * s, -.05 * s], [1.85 * s, -.05 * s]], sw * 1.1, K.brass, 'ink', 0);   // crank stub on the edge
      const sm = Math.sin(sp * PI);   // smear arcs: it's turning fast
      for (const k of [-1, 1]) inkLine([[.65 * s + k * 1.3 * s, -.9 * s], [.65 * s + k * 1.6 * s, 0], [.65 * s + k * 1.3 * s, .9 * s]], sw * 1.2 * sm, K.walnut, 'dry', .5);
      pop(); return;
    }
    // reels behind the body, their holes turning with the crank
    for (const [cx, cy, r, k] of [[-.05, -1.45, .62, 1], [1.2, -1.35, .5, 1.35]]) {
      paint(ellPts(cx * s, cy * s, r * s, r * s, 18), { wash: K.reel, ink: PAL.ink, sw: sw * .7 });
      for (let i = 0; i < 3; i++) {
        const a = crank * .45 * k + i * TAU / 3;
        paint(ellPts(cx * s + Math.cos(a) * r * .52 * s, cy * s + Math.sin(a) * r * .52 * s, r * .2 * s, r * .2 * s, 8), { wash: K.brass, ink: null });
      }
      paint(ellPts(cx * s, cy * s, .09 * s, .09 * s, 8), { wash: PAL.ink, ink: null });
    }
    paint(rrPts(-.7 * s, -.8 * s, 2.7 * s, 1.6 * s, .22 * s), { wash: K.walnut, fill: K.camDk, fillOp: 70, tex: .6, ink: PAL.ink, sw });
    paint(rrPts(-.4 * s, -.5 * s, 1.5 * s, 1.0 * s, .14 * s), { wash: mixCol(K.walnut, K.brass, .28), ink: PAL.ink, sw: sw * .45 });
    paint(rectPts(2.0 * s, -.42 * s, .55 * s, .84 * s), { wash: K.camDk, ink: PAL.ink, sw: sw * .8 });
    paint(ellPts(2.6 * s, 0, .22 * s, .56 * s, 14), { wash: K.brass, ink: PAL.ink, sw: sw * .5 });
    paint(ellPts(2.62 * s, 0, .13 * s, .42 * s, 14), { wash: PAL.ink, ink: null });
    inkLine([[2.6 * s, -.3 * s], [2.63 * s, -.12 * s]], sw * .5, PAL.cream, 'inkfine', 0);
    // the crank: an arm on the side panel, turning, with a brass knob
    const cx = .35 * s, cy = 0, R = .4 * s, hx = cx + Math.cos(crank) * R, hy = cy + Math.sin(crank) * R;
    inkLine([[cx, cy], [hx, hy]], sw * 1.3, K.brass, 'ink', 0);
    paint(ellPts(hx, hy, .13 * s, .13 * s, 8), { wash: K.brass, ink: PAL.ink, sw: sw * .45 });
    paint(ellPts(cx, cy, .09 * s, .09 * s, 8), { wash: PAL.ink, ink: null });
    pop();
  }
  // Clawd's side-view near arm (aL) carries the camera: cancel the arm's own angle, then tilt by aim.
  const camHook = (a, aim, o = {}) => (u, sw) => {
    rotate(-(.7 - a) + aim);
    if (o.shift) translate(o.shift[0] * u, o.shift[1] * u);
    movieCam(u * .82, { ...o, sw: sw * .85 });
  };
  // World position of a point in Clawd's body space (mirrors clawd()'s own transform).
  function bodyPt(x, y, u, o, lx, ly) {
    const sq = o.sq || 0, sm = clamp(o.smear || 0);
    const sx = (o.flip ? -1 : 1) * (o.sx ?? 1) * (1 + sq * .6) * (1 + sm * .35), sy = (o.sy ?? 1) * (1 - sq);
    const px = lx * sx, py = ly * sy, r = o.rot || 0, c = Math.cos(r), s = Math.sin(r);
    return [x + (o.dx || 0) * u + px * c - py * s, y + (o.dy || 0) * u + px * s + py * c];
  }
  // World position of a point given in camera-hook space (units of u), for a side-view Clawd holding the camera.
  function camPt(x, y, u, o, a, aim, cx, cy) {
    const th = .7 - a, tx = 1.6 * u + 2.1 * u * Math.cos(th), ty = -4.2 * u + 2.1 * u * Math.sin(th);
    const c = Math.cos(aim), s = Math.sin(aim);
    return bodyPt(x, y, u, o, tx + (cx * c - cy * s) * u, ty + (cx * s + cy * c) * u);
  }

  // ---------- set pieces ----------
  function sky(col, warm, t, key) {
    boilSeed('sky' + key);
    paint(rectPts(-500, -400, W + 1000, H + 800), { wash: col, ink: null });
    paint(ellPts(W * .5, H * .9, W * .95, H * .42, 30, 8), { fill: warm, fillOp: 130, bleed: .3, tex: .5, ink: null });
    for (let i = 0; i < 4; i++) {   // soft clouds drifting right, with the wind
      boilSeed('cloud' + key + i);
      const x = ((hash(i + 3) * (W + 900) + t * (10 + 6 * i)) % (W + 900)) - 450, y = 90 + hash(i + 7) * 230;
      paint(ellPts(x, y, 150 + 90 * hash(i + 2), 34 + 10 * hash(i), 22, 3), { fill: PAL.cream, fillOp: 140, bleed: .25, tex: .4, ink: null });
    }
  }
  function hills(key, yFar, yMid) {
    boilSeed('hills' + key);
    paint(ellPts(W * .25, yFar + 260, W * .7, 300, 36, 3), { wash: mixCol(K.hillFar, K.skyA, .25), fill: K.hillFar, fillOp: 60, bleed: .1, tex: .5, ink: null });
    paint(ellPts(W * 1.05, yFar + 230, W * .6, 260, 36, 3), { wash: K.hillFar, fill: mixCol(K.hillFar, K.hillMid, .3), fillOp: 60, bleed: .1, tex: .5, ink: null });
    paint(ellPts(W * .65, yMid + 300, W * .9, 300, 40, 3), { wash: mixCol(K.hillMid, K.hillFar, .35), fill: K.hillMid, fillOp: 70, bleed: .1, tex: .6, ink: PAL.ink, sw: .5 });
    for (let i = 0; i < 7; i++) {   // little far-off autumn trees along the ridge: smaller, paler, bluer = farther
      boilSeed('farTree' + key + i);
      const x = 180 + i * 290 + 90 * hash(i + 21), cx = W * .65, top = yMid + 300 - 300 * Math.sqrt(Math.max(0, 1 - ((x - cx) / (W * .9)) ** 2)), r = 26 + 16 * hash(i + 4);
      inkLine([[x, top + 6], [x, top - r * 1.2]], .6, mixCol(K.trunk, K.hillFar, .4), 'inkfine', 0);
      paint(ellPts(x, top - r * 1.45, r * .8, r, 16, 1.5), { wash: mixCol(K.crown[i % 4], K.hillFar, .45), ink: null });
    }
  }
  function meadow(G, key, x0 = -500, x1 = W + 500) {
    boilSeed('meadow' + key);
    paint(rectPts(x0, G - 14, x1 - x0, H + 400 - G, 2), { wash: K.meadow, fill: K.meadowDk, fillOp: 90, bleed: .05, tex: .7, ink: null });
    const n = Math.ceil((x1 - x0) / 1400);
    for (let i = 0; i < n; i++) { const a = lerp(x0, x1, i / n), b = lerp(x0, x1, (i + 1) / n); inkLine([[a, G - 12 + 3 * Math.sin(i)], [(a + b) / 2, G - 16], [b, G - 12 + 3 * Math.sin(i + 1)]], .9, PAL.ink, 'ink', .5); }
    for (let i = 0; i < 26; i++) {   // fallen rust leaves lying in the grass (not gold: the gold one is the hero)
      const x = lerp(x0, x1, hash(i + 40)), y = G + 30 + hash(i + 60) * 160;
      paint(ellPts(x, y, 11 + 6 * hash(i), 5, 8, 0, hash(i + 9) * 3), { wash: mixCol(K.crown[i % 4], K.meadow, .35), ink: null });
    }
  }
  // Grass tufts that sway, and lean with the gust (lean in px at the tip).
  function tufts(G, t, key, x0, x1, n, lean) {
    for (let i = 0; i < n; i++) {
      boilSeed('tuft' + key + i);
      const x = lerp(x0, x1, (i + .5 * hash(i + 11)) / n), h = 26 + 16 * hash(i + 5), sw = wob(t, .45, hash(i) * 3) * 4 + lean * (.8 + .4 * hash(i + 2));
      for (const k of [-1, 0, 1]) inkLine([[x + k * 7, G - 10], [x + k * 9 + sw * .5, G - 10 - h * .55], [x + k * 11 + sw, G - 10 - h - 6 * hash(i + k + 3)]], .75, mixCol(K.meadowDk, PAL.ink, .2), 'inkfine', .5);
    }
  }
  // Wind: cream dry-brush streaks with a curl at the head, sweeping left → right. rows: [y, delay, length]
  function gust(t, t0, key, rows, span = [-500, W + 700]) {
    rows.forEach(([y, d, len], i) => {
      const p = seg(t, t0 + d, t0 + d + .6); if (p <= 0 || p >= 1) return;
      boilSeed('gust' + key + i);
      const hx = lerp(span[0], span[1], easeOut(p) * .7 + p * .3), fade = 1 - seg(p, .7, 1), P = [];
      for (let k = 0; k <= 8; k++) { const x = hx - len * (1 - k / 8); P.push([x, y + 16 * Math.sin(k * .8 + i + p * 4)]); }
      for (let k = 1; k <= 7; k++) { const a = -PI / 2 + k * .9; P.push([hx + 26 * Math.cos(a) * (1 - k * .08), y - 26 + 26 * Math.sin(a) * (1 - k * .08)]); }
      if (fade > .05) {
        inkLine(P.slice(0, 9), 1.5 * fade, PAL.cream, 'dry', .4);
        inkLine(P, .6 * fade, K.wind, 'inkfine', .6);
        if (i % 2 === 0) {   // a small rust leaf riding the head of every other streak
          const lx = hx - 40, ly = y - 20 + 12 * Math.sin(p * 9 + i);
          push(); translate(lx, ly); rotate(p * 14 + i); paint(LEAF_SHAPE.map(([a, b]) => [a * 16, b * 16]), { wash: K.crown[i % 4], ink: PAL.ink, sw: .35 }); pop();
        }
      }
    });
  }
  const gustEnv = (t, t0) => ease(seg(t, t0 - .15, t0 + .08)) * (1 - ease(seg(t, t0 + .35, t0 + 1.1))) + .35 * spring(t, t0 + .6, 3, 9);
  // The maple: trunk from the ground, one long branch reaching right, a rust crown. Returns the twig tip (the hero
  // leaf's stem hangs from it). shake: px of sway from the gust.
  function maple(t, G, shake) {
    boilSeed('trunk');
    paint(ribbon([[150, G + 30], [175, 600], [165, 380], [200, 180], [240, -40]], 150, 90), { wash: K.trunk, fill: K.trunkDk, fillOp: 90, tex: .7, ink: PAL.ink, sw: 1 });
    const sway = shake + 3 * wob(t, .3);
    const B = [[190, 300], [330, 262], [480, 272], [600 + sway * .5, 312 + sway * .1]];
    paint(ribbon(B, 48, 12), { wash: K.trunk, fill: K.trunkDk, fillOp: 80, tex: .7, ink: PAL.ink, sw: .9 });
    const tip = [656 + sway, 348 + sway * .15];
    inkLine([[590 + sway * .5, 308], [626 + sway * .8, 330], tip], 1.3, PAL.ink, 'ink', .5);
    const blobs = [[80, 150, 190, 150], [300, 110, 200, 140], [470, 170, 170, 115], [590, 235, 120, 80], [210, 10, 220, 130], [430, 40, 190, 110], [30, 330, 120, 110]];
    blobs.forEach(([x, y, rx, ry], i) => {
      boilSeed('crown' + i);
      const dx = sway * (.3 + .4 * hash(i + 1)) + 4 * wob(t, .25, hash(i));
      paint(ellPts(x + dx, y, rx, ry, 26, rx * .07), { wash: K.crown[i % 4], fill: K.crown[(i + 2) % 4], fillOp: 110, bleed: .15, tex: .7, ink: PAL.ink, sw: .6 });
    });
    return tip;
  }
  function pumpkin(x, y, r, key, o = {}) {   // (x, y) = the ground point under it. One silhouette + painted ribs.
    boilSeed('pumpkin' + key);
    const h = r * .78, cy = y - h, c0 = o.col || K.pumpkin, c1 = o.dk || K.pumpkinDk, sw = o.sw ?? 1, P = [];
    for (let i = 0; i < 40; i++) { const a = i / 40 * TAU, pinch = 1 - .13 * Math.exp(-Math.pow(Math.cos(a) * 4, 2)); P.push([x + Math.cos(a) * r * 1.12, cy + Math.sin(a) * h * pinch]); }
    paint(P, { wash: c0, fill: c1, fillOp: 85, bleed: .1, tex: .6, border: .5, ink: PAL.ink, sw });
    for (const k of [-.62, -.22, .22, .62]) inkLine([[x + k * r * .35, cy - h * .86], [x + k * r * 1.02, cy], [x + k * r * .35, cy + h * .86]], sw * .7, mixCol(c1, PAL.ink, .35), 'ink', .8);
    paint(ribbon([[x - .04 * r, cy - h * .85], [x, cy - h * 1.05], [x + .1 * r, cy - h * 1.22]], .16 * r, .1 * r), { wash: K.stem, ink: PAL.ink, sw: (o.sw ?? 1) * .8 });
    if (o.vine) inkLine([[x + .08 * r, cy - h * .95], [x + .3 * r, cy - h * 1.2], [x + .42 * r, cy - h * 1.05], [x + .35 * r, cy - h * .98]], .8, K.stem, 'ink', .7);
    return [x, cy - h * .95];   // top of the pumpkin, beside the stem
  }
  function fence(G, x0, n, gap, key) {
    for (let i = 0; i < n; i++) {
      boilSeed('fence' + key + i);
      const x = x0 + i * gap;
      paint(rectPts(x, G - 150, 16, 150, 1.5), { wash: mixCol(K.trunk, K.skyB, .45), ink: PAL.ink, sw: .45 });
    }
    boilSeed('rail' + key);
    for (const yy of [G - 120, G - 70]) inkLine([[x0 - 30, yy], [x0 + (n - 1) * gap + 40, yy + 4]], 1.2, mixCol(K.trunk, K.skyB, .4), 'ink', .2);
  }
  // Tiny cream dust puffs kicked up at t0 by a skid.
  function dust(x, y, t, t0, key) {
    const a = t - t0; if (a < 0 || a > .7) return;
    for (let i = 0; i < 4; i++) {
      boilSeed('dust' + key + i);
      const k = easeOut(a / .7), px = x - (20 + 70 * i) * k - 20 * i, py = y - 10 - 30 * k * (1 + hash(i)), r = (14 + 12 * i) * (0.4 + k) * (1 - seg(a, .45, .7));
      if (r > 2) paint(ellPts(px, py, r, r * .8, 14, 2), { wash: PAL.cream, washOp: 230, ink: PAL.ink, sw: .45 });
    }
  }
  // The viewfinder: an ink surround with a rounded-rect window (w × h at cx, cy) and cream corner brackets.
  function viewfinder(cx, cy, w, h, brackets = 1) {
    boilSeed('viewfinder');
    if (w < 8 || h < 8) { paint(rectPts(-80, -80, W + 160, H + 160), { wash: PAL.ink, ink: null }); return; }
    irisShape(rrPts(cx - w / 2, cy - h / 2, w, h, Math.min(w, h) * .1), PAL.ink);
    if (brackets > .02) {
      const ins = Math.min(w, h) * .075, L = Math.min(w, h) * .14;
      for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
        const x = cx + sx * (w / 2 - ins), y = cy + sy * (h / 2 - ins);
        inkLine([[x - sx * L, y], [x, y], [x, y - sy * L]], 2.2 * brackets, PAL.cream, 'ink', 0);
      }
    }
  }

  // ======================================================================================================
  // Shot A (0–4.0): the first try
  // ======================================================================================================
  const A = { G: 900, u: 34, X: 1190, r: 50, tRel: 1.15, tGust: 2.55, tSurp: 3.0, tTurn: 3.5 };
  // the leaf, in world space: hanging (trembling) → rocking fall → snatched on an arc out right
  function leafA(lt, tip) {
    const r = A.r;
    if (lt < A.tRel) {
      const tug = lt > .95 ? .35 * Math.sin((lt - .95) * 30) * seg(lt, .95, 1.1) : 0;   // it tugs at its stem before letting go
      const rot = PI + .12 * Math.sin(lt * 5.5) + .06 * Math.sin(lt * 13) + tug;
      return { x: tip[0] - Math.sin(rot - PI) * .95 * r, y: tip[1] + Math.cos(rot - PI) * .95 * r, rot };
    }
    const fall = s => {
      const [dx, dy, rr] = rock(s, 62, 1.25, 18);
      const hang = [tip[0], tip[1] + .95 * r];
      return { x: hang[0] + 62 * s + dx, y: hang[1] + 125 * s * clamp(s / .35) + dy, rot: lerp(PI, rr, ease(seg(s, 0, .6))) };
    };
    const s = lt - A.tRel;
    if (lt < A.tGust) return fall(s);
    const p0 = fall(A.tGust - A.tRel), k = Math.pow(seg(lt, A.tGust, A.tGust + .42), 1.8), p = arcPt([p0.x, p0.y], [2350, 330], 190, k);
    return { x: p[0], y: p[1], rot: p0.rot + k * 9, k };
  }
  function poseA(lt) {
    const mood = emotions(lt, [[0, 'hopeful', { lookX: .7, lookY: -.8 }], [1.6, 'excited', { lookX: .7, lookY: -.6 }], [2.1, 'determined', { lookX: .8, lookY: -.4 }],
                               [A.tSurp, 'surprised', { lookX: -.9, lookY: -.5 }], [A.tTurn + .02, 'determined', { lookX: .6 }]]);
    let o = { ...mood, view: 'side', flip: true };
    let a = .75 + .06 * wob(lt, .5);   // the camera arm: steady, just ahead of the eye
    if (lt > 1.6 && lt < 2.1) a += .15 * Math.sin((lt - 1.6) * 18) * Math.exp(-(lt - 1.6) * 5);
    if (lt > A.tSurp - .05) a = lerp(a, 1.2, backOut(seg(lt, A.tSurp - .05, A.tSurp + .2)));   // jolted up and forward with the take
    if (lt > A.tTurn) {   // drawn turn to face right, crouch, launch (cut mid-launch)
      a = lerp(1.2, .3, ease(seg(lt, A.tTurn, A.tTurn + .2)));
      if (lt < A.tTurn + .16) o = { ...o, ...turn(lt, A.tTurn, A.tTurn + .16, -.25, .25) };
      else o = { ...o, view: 'side', flip: false };
      const crouch = ease(seg(lt, 3.66, 3.84)), go = seg(lt, 3.84, 4.0);
      o.sq = (o.sq || 0) * .5 + .24 * crouch * (1 - go) - .22 * easeOut(go);
      o.dx = 2.2 * easeIn(go); o.dy = (o.dy || 0) * .3 - .5 * easeOut(go);
      if (go > 0) { o.walk = go * 2; o.smear = .55 * go; o.smearDir = 1; }
    }
    o.aL = a;
    return o;
  }
  function shotA(t, lt, dur) {
    const { G, u, X } = A;
    const reveal = ease(seg(lt, .55, 1.05)), whip = ease(seg(lt, 2.62, 3.1)) * (1 - ease(seg(lt, 3.3, 3.9)));
    const cx = lerp(680, 905, reveal) + 12 * Math.sin(lt * .7) + 70 * whip, cy = lerp(430, 560, reveal), z = lerp(2.1, 1.1, reveal) + .01 * lt;
    camBegin(lerp(960, cx, .4), lerp(540, cy, .4), 1 + (z - 1) * .4);   // background layer, parallax
    sky(K.skyA, K.warmA, t, 'A');
    hills('A', 560, 640);
    camEnd();
    camBegin(cx, cy, z);
    const env = gustEnv(lt, A.tGust);
    const tip = maple(t, G, 26 * env + 8 * spring(lt, A.tRel, 5, 16));
    meadow(G, 'A');
    tufts(G, t, 'A', 380, 1900, 12, 30 * env);
    // the leaf (behind Clawd once it passes over)
    const L = leafA(lt, tip);
    boilSeed('leafA');
    if (L.k != null && L.k > 0) {   // a streak trails the snatched leaf
      const P = []; for (let i = 6; i >= 0; i--) { const q = leafA(Math.max(A.tGust, lt - i * .03), tip); P.push([q.x, q.y]); }
      if (Math.hypot(P[6][0] - P[0][0], P[6][1] - P[0][1]) > 10) paint(ribbon(P, 2, 22), { wash: PAL.cream, washOp: 200, fill: K.leaf, fillOp: 60, ink: null });
    }
    drawLeaf(L.x, L.y, A.r, L.rot);
    // Clawd with the camera, tracking the leaf (the aim lags the leaf by a beat of follow-through)
    const o = poseA(lt);
    const hand = camPt(X, G, u, o, o.aL, 0, 0, 0), Ld = leafA(Math.max(0, lt - .12), tip);
    let aim = -Math.atan2(hand[1] - Ld.y, Math.abs(Ld.x - hand[0]));
    if (lt > A.tGust) { const La = leafA(A.tGust - .12, tip); aim = -Math.atan2(hand[1] - La.y, Math.abs(La.x - hand[0])) * (1 - ease(seg(lt, A.tSurp, A.tSurp + .3))); }
    const elev = clamp(-aim, -.2, 1.0);
    o.rot = (o.rot || 0) + .22 * elev * (lt < A.tTurn ? 1 : 0);   // lean back to look up; the camera tilts the rest
    aim = clamp(aim + .22 * elev, -.45, .2);
    const crank = lt > 1.65 && lt < A.tGust + .2 ? (lt - 1.65) * 13 : lt >= A.tGust + .2 ? (A.tGust - 1.45) * 13 : 0;
    const spin = lt > A.tTurn && lt < A.tTurn + .16 ? 0 : 0;
    if (lt > A.tSurp - .05) aim -= .5 * spring(lt, A.tSurp, 5, 14);   // the camera jolts with the take
    clawd(X, G, u, { ...o, armL: camHook(o.aL, aim, { crank, spin, shift: [.85, 0] }) });
    gust(lt, A.tGust - .2, 'A', [[300, 0, 420], [470, .06, 520], [610, .12, 380], [760, .03, 460], [180, .15, 300]]);
    const leafScreen = toScreen(L.x, L.y);
    camEnd();
    // transition in: the viewfinder opens on the leaf, holds, then widens out as the camera pulls back
    if (lt < 1.2) {
      const open = easeOut(seg(lt, 0, .3)), wide = easeIn(seg(lt, .55, 1.0));
      const cx = lerp(leafScreen[0], 960, wide), cy = lerp(leafScreen[1], 540, wide), w = lerp(760 * open, 4400, wide);
      viewfinder(cx, cy, w, w * .5625, 1 - wide);
    }
  }

  // ======================================================================================================
  // Shot B (4.0–8.2): the second try, and blaming the camera
  // ======================================================================================================
  const B = { G: 900, u: 30, PX: 1340, tStop: .95, tSneak: 1.35, tGust: 2.0, tStomp: 2.5, tSusp: 3.1, tSpin: 3.3, tPush: 3.8 };
  function leafB(lt, top) {
    const r = 30;
    if (lt < .6) {   // drifting down onto the pumpkin
      const k = ease(seg(lt, -.3, .6)), [dx, dy, rr] = rock(lt + 1.5, 50 * (1 - k), 1.1, 12);
      return { x: lerp(1160, top[0] - 20, k) + dx, y: lerp(300, top[1] - 26, k) + dy, rot: rr * (1 - k) + .25 * k };
    }
    const settle = .12 * spring(lt, .6, 5, 14), flutter = lt > 1.8 && lt < B.tGust ? .12 * Math.sin(lt * 60) * seg(lt, 1.8, 2.0) : 0;
    const rest = { x: top[0] - 20, y: top[1] - 26, rot: .25 + settle + .04 * Math.sin(lt * 2.2) + flutter };
    if (lt < B.tGust) return rest;
    // gust #2: lifts, loops once, zips up and out of the top
    const P = through([[rest.x, rest.y], [rest.x + 60, rest.y - 70], [rest.x + 150, rest.y - 110], [rest.x + 175, rest.y - 200], [rest.x + 100, rest.y - 250],
                       [rest.x + 40, rest.y - 190], [rest.x + 120, rest.y - 130], [rest.x + 290, rest.y - 260], [rest.x + 480, rest.y - 620], [rest.x + 620, rest.y - 1000]], 8);
    const k = Math.pow(seg(lt, B.tGust, B.tGust + .5), 1.25), f = k * (P.length - 1), i = Math.min(P.length - 2, Math.floor(f)), q = f - i;
    return { x: lerp(P[i][0], P[i + 1][0], q), y: lerp(P[i][1], P[i + 1][1], q), rot: rest.rot + k * 11, k };
  }
  function poseB(lt) {
    const mood = emotions(lt, [[0, 'determined'], [1.0, 'mischief', { lookX: .6 }], [B.tGust + .06, 'neutral', { eyes: 'blank', lookY: -1, lookX: .4 }],
                               [B.tStomp, 'angry'], [B.tSusp, 'suspicious', { lookX: .8, lookY: .1, emote: '?' }]], { take: .8 });
    const o = { ...mood, view: 'side', flip: false };
    // the dash (continues A's launch) decelerating into a skid, then a tiptoe
    const x = lt < B.tStop ? lerp(300, 830, easeOut(seg(lt, 0, B.tStop))) : lerp(830, 900, ease(seg(lt, B.tSneak, 1.95)));
    o.x = x;
    if (lt < B.tStop) { o.walk = (x - 300) / (2.6 * B.u); o.dy = (o.dy || 0) * .3 - .6 * Math.abs(Math.sin(o.walk * PI)); o.smear = .35 * (1 - seg(lt, 0, .6)); o.smearDir = 1; o.sq = (o.sq || 0) - .1 * (1 - seg(lt, 0, .7)); }
    else if (lt < B.tSneak) { const a = lt - B.tStop; o.sq = (o.sq || 0) + .26 * Math.exp(-a * 7) * Math.cos(a * 14); o.rot = -.2 * Math.exp(-a * 6); }
    else if (lt < 1.95) { o.walk = (x - 830) / (2.2 * B.u); o.sq = (o.sq || 0) - .08; o.dy = (o.dy || 0) * .3 - .35 * Math.abs(Math.sin(o.walk * PI)); }
    // the camera arm
    let a = lt < B.tStop ? .35 : lt < B.tSneak ? .35 + .2 * Math.exp(-(lt - B.tStop) * 6) : lerp(.35, .85, ease(seg(lt, B.tSneak, 1.75)));
    if (lt > B.tStomp) a = lerp(a, -.55, ease(seg(lt, B.tStomp, B.tStomp + .2)));
    if (lt > B.tSusp) a = lerp(-.55, 1.05, ease(seg(lt, B.tSusp, B.tSusp + .25)));
    o.aL = a;
    if (lt > B.tStomp) { const j = jump(lt, B.tStomp + .06, B.tStomp + .26, 1.0); o.dy = (o.dy || 0) + j.dy; o.sq = (o.sq || 0) + j.sq; }
    if (lt > B.tSusp) { const lean = ease(seg(lt, 3.5, 3.85)); o.dx = .75 * lean; o.rot = (o.rot || 0) + .07 * lean; o.lookX = 1; o.lookY = .15; }   // leaning in to peer into the lens
    return o;
  }
  // the camera's hold offset (hook space, in u): just ahead of the eye; once turned round, the lens sits at the eye
  const shiftB = spin => [lerp(.85, 1.55, seg(spin, .3, .7)), lerp(0, -.45, seg(spin, .3, .7))];
  const lensB = (o, aim, spin) => { const sh = shiftB(spin); return camPt(o.x, B.G, B.u, o, o.aL, aim, sh[0] + (spin > .67 ? -1.07 : 2.13), sh[1] - .66); };
  function shotB(t, lt, dur) {
    const { G, u } = B;
    const o = poseB(lt);
    const land = lt > B.tStomp + .26 ? shakeXY(t, 9 * Math.exp(-(lt - B.tStomp - .26) * 8)) : [0, 0];
    const aim = lt < B.tStomp ? -.3 * ease(seg(lt, B.tSneak, 1.8)) : lt < B.tSusp ? 0 : -.05;
    const spin = seg(lt, B.tSpin, B.tSpin + .2);
    const lens = lensB(o, aim, spin);
    const push = ease(seg(lt, B.tPush - .1, dur - .05));
    const cx0 = (lt < 1.2 ? lerp(80, 1110, easeOut(seg(lt, 0, 1.2))) : lerp(1110, 1080, seg(lt, 1.2, 3.8))) + land[0], cy0 = 690 + land[1], z0 = 1.35 + .03 * lt;
    const cx = lerp(cx0, lens[0], push), cy = lerp(cy0, lens[1], push), z = z0 * Math.pow(3.2, easeIn(seg(lt, B.tPush - .15, dur)));
    // background layer: moves at a third of the speed (parallax)
    camBegin(lerp(960, cx, .35), lerp(540, cy, .35), 1 + (z - 1) * .35);
    sky(K.skyB, K.warmB, t, 'B');
    hills('B', 560, 650);
    camEnd();
    camBegin(cx, cy, z);
    fence(G - 40, 1560, 6, 150, 'B');
    const env = gustEnv(lt, B.tGust);
    meadow(G, 'B', -1300, 2600);
    pumpkin(-90, G + 30, 60, 'p1', { sw: .6, col: mixCol(K.pumpkin, K.hillFar, .25) });
    pumpkin(1840, G + 20, 80, 'p2', { sw: .7, vine: true, col: mixCol(K.pumpkin, K.hillFar, .2) });
    const top = pumpkin(B.PX, G + 6, 125, 'hero', { vine: true, col: K.squash, dk: K.squashDk });
    tufts(G, t, 'B', -700, 2400, 22, 28 * env);
    const L = leafB(lt, top);
    boilSeed('leafB');
    drawLeaf(L.x, L.y, 36, L.rot);
    dust(o.x - 2 * u, G, lt, B.tStop - .05, 'skid');
    dust(o.x - 1 * u, G, lt, B.tStomp + .26, 'stomp');
    const crank = lt > 1.75 && lt < B.tGust + .15 ? (lt - 1.75) * 13 : 0;
    clawd(o.x, G, u, { ...o, armL: camHook(o.aL, aim, { crank, spin, shift: shiftB(spin) }) });
    gust(lt, B.tGust - .2, 'B', [[430, 0, 460], [560, .05, 520], [690, .1, 400], [820, .02, 480], [330, .13, 340]], [-100, 2400]);
    const ls = toScreen(lens[0], lens[1]);
    camEnd();
    // push into the lens: the dark glass swells (growing exponentially, like a push) until it fills the frame
    if (lt > B.tPush) {
      boilSeed('lensglass');
      const g = seg(lt, B.tPush, dur - .04), R = .4 * u * .82 * z * Math.pow(260, easeIn(g) * .6 + g * .4);
      if (R < 1600) paint(ellPts(ls[0], ls[1], R * 1.16, R * 1.16, 48), { wash: K.brass, ink: null });
      paint(ellPts(ls[0], ls[1], R, R, 48), { wash: PAL.ink, ink: null });
      if (R < 1500) inkLine([[ls[0] - R * .62, ls[1] - R * .3], [ls[0] - R * .48, ls[1] - R * .55], [ls[0] - R * .22, ls[1] - R * .68]], clamp(R / 50, .5, 3.5), PAL.cream, 'ink', .6);
    }
  }

  // ======================================================================================================
  // Shot C (8.2–12.0): POV through the viewfinder
  // ======================================================================================================
  const Cc = { X: 960, G: 1185, u: 84, tIn: .8, tLand: 1.7, tNotice: 1.85, tJoy: 2.4, tWave: 2.7, tClose: 3.15 };
  function poseC(lt) {
    const mood = emotions(lt, [[0, 'suspicious'], [Cc.tNotice, 'surprised', { lookY: -1, lookX: .25 }], [Cc.tJoy, 'happy', { emote: 'hearts' }]], { take: 1.2 });
    const o = { ...mood };
    if (lt < Cc.tNotice) { o.lookX = .5 * Math.sin(lt * 5.5); o.lookY = .15 * Math.sin(lt * 3.1); }   // pupils darting: inspecting the lens
    const land = spring(lt, Cc.tLand, 7, 22);
    o.sq = (o.sq || 0) + .05 * land;
    if (lt > Cc.tWave) o.aL = lerp(o.aL ?? .4, 1.25 + .5 * Math.sin((lt - Cc.tWave) * 13), ease(seg(lt, Cc.tWave, Cc.tWave + .2)));
    return o;
  }
  // the top of Clawd's head, where the leaf sits (body space → world)
  const headC = (o) => bodyPt(Cc.X, Cc.G, Cc.u, o, 1.4 * Cc.u, -8.05 * Cc.u);
  function leafC(lt) {
    const hl = headC(poseC(lt)), r = 88;
    if (lt < Cc.tIn) return null;
    if (lt < Cc.tLand) {
      const endP = headC(poseC(Cc.tLand)), k = seg(lt, Cc.tIn, Cc.tLand), [dx, dy, rr] = rock(lt - Cc.tIn + .3, 90 * (1 - ease(k)), 1.0, 20);
      return { x: lerp(1230, endP[0], ease(k)) + dx, y: lerp(-60, endP[1] - .55 * r, k) + dy * (1 - k), rot: rr * (1 - ease(k)) + .3 * ease(k), r };
    }
    const a = lt - Cc.tLand, o = poseC(lt);
    return { x: hl[0], y: hl[1] - .55 * r * (1 - .12 * spring(lt, Cc.tLand, 6, 20)), rot: .3 + .35 * spring(lt, Cc.tLand, 4, 13) + (o.rot || 0) + .08 * Math.sin(a * 6) * seg(lt, Cc.tJoy, Cc.tJoy + .3), r };
  }
  function shotC(t, lt, dur) {
    const hh = [7 * Math.sin(lt * 1.7) + 3 * Math.sin(lt * 4.1), 5 * Math.sin(lt * 2.3 + 1)];   // handheld
    camBegin(960 + hh[0], 530 + hh[1], kf(lt, [[0, 1.08], [.9, 1.02], [2.3, 1.0], [3.3, 1.04]]));
    sky(K.skyC, K.warmC, t, 'C');
    boilSeed('sun');
    glow(1500, 700, 520, '#FFB65C', .75);
    hills('C', 600, 700);
    meadow(930, 'C');
    pumpkin(330, 1010, 120, 'c1', { sw: .7 });
    pumpkin(1640, 1030, 150, 'c2', { sw: .8, vine: true, col: K.squash, dk: K.squashDk });
    tufts(930, t, 'C', 100, 1850, 10, 0);
    const o = poseC(lt);
    clawd(Cc.X, Cc.G, Cc.u, o);
    const L = leafC(lt);
    boilSeed('leafC');
    if (L) drawLeaf(L.x, L.y, L.r, L.rot);
    const face = toScreen(Cc.X + (o.dx || 0) * Cc.u, Cc.G - 6.3 * Cc.u);
    camEnd();
    // the recording dot, blinking on the beat
    boilSeed('rec');
    if (frac(bpOf(t) / 2) < .6) { glow(1650, 185, 80, K.rec, .9); paint(ellPts(1650, 185, 24, 24, 16), { wash: K.rec, ink: PAL.ink, sw: .7 }); }
    // viewfinder: opens out of the dark lens, then closes onto Clawd's face at the end
    let cx = 960, cy = 540, w = 1640, h = 910;
    if (lt < .4) { const k = easeOut(seg(lt, .02, .38)); w = lerp(0, 1640, k); h = lerp(0, 910, k); }
    if (lt > Cc.tClose) {
      const k = ease(seg(lt, Cc.tClose, Cc.tClose + .38)), z = easeIn(seg(lt, 3.6, dur - .06));
      cx = lerp(960, face[0], k); cy = lerp(540, face[1] - 60, k);
      w = lerp(1640, 980, k) * (1 - z); h = lerp(910, 660, k) * (1 - z);
    }
    viewfinder(cx, cy, w, h, 1);
  }

  shots([[0, shotA], [4.0, shotB], [8.2, shotC]]);

  // model sheet for the new prop and the leaf: studio.html?loop=props, or render.mjs --loop=props --stills=...
  LOOPS.props = t => {
    boilSeed('bg'); paint(rectPts(-50, -50, W + 100, H + 100), { wash: PAL.paper, ink: null });
    [0, .5, 1].forEach((sp, i) => { push(); translate(300 + i * 420, 420); boilSeed('cam' + i); movieCam(90, { spin: sp, crank: t * 13 }); pop(); });
    drawLeaf(1600, 360, 120, .2 * Math.sin(t * 2));
    for (let i = 0; i < 5; i++) { const [dx, dy, rr] = rock(t + i * .25, 60, 1.25, 18); drawLeaf(300 + i * 320 + dx, 820 + dy, 45, rr); }
  };
  LOOPS.props.len = 2.5;
})();
