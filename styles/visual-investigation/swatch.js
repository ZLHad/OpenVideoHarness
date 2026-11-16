// 视觉调查 · visual-investigation — swatch spec 2 (8 s, four beats, landscape and portrait).
//
// A night drawing of one floor of an office building, reconstructed: a scan draws the plan, the walls rise into a
// wireframe model as the camera tilts, and a subject's route runs through it against a running timecode. Each event
// gets a numbered callout that says when and where it comes from (the access log, a corridor camera, a light coming
// on). The event is invented for the swatch (a late round through an empty floor); nothing in it refers to a real place.
//
//   0.0–1.5  world      a scan line crosses the frame (0.1 s) and draws the plan behind it; the timecode comes up
//   1.5–4.5  signature  the walls extrude into wireframe as the camera tilts; the route runs, events ①②③ are called out
//   4.5–7.0  type       the model dims; the title as a figure caption; the caption; read once
//   7.0–8.0  close      the walls sink, a scan runs back and erases the plan; the camera returns to top-down
//
// The 3D is a few dozen line segments projected by hand (yaw, pitch, a pinhole): no library. One timing table T drives
// picture, foley and reads.

const T = {
  scan: [0.1, 1.05], hud: [0.3, 0.6], extrude: [1.5, 2.3], route: [2.2, 4.2],
  dim: [4.45, 4.8], fig: 4.5, title: 4.6, caption: 4.8, read: [4.95, 7.0],
  sink: [7.0, 7.45], erase: [7.1, 7.9], back: [7.0, 7.95],
};
// story time (seconds after midnight) against swatch time: slow, then fast while the route runs, then real time
const S0 = 2 * 3600 + 13 * 60 + 40, S1 = 2 * 3600 + 14 * 60 + 5, S2 = 2 * 3600 + 16 * 60 + 45;
const EVENTS = [   // when, where (plan metres), what, where the callout sits (screen offset px)
  { s: 2 * 3600 + 14 * 60 + 7, at: [0.6, 9], zh: "入口门禁", src: "ACCESS LOG", dx: -120, dy: 190 },
  { s: 2 * 3600 + 15 * 60 + 10, at: [12, 9], zh: "走廊 CAM-2", src: "CCTV", dx: 40, dy: 230 },
  { s: 2 * 3600 + 16 * 60 + 20, at: [16.6, 14.2], zh: "302 室亮灯", src: "LIGHTING", dx: 120, dy: -200 },
];
const story = (t) => {
  if (t < T.route[0]) return S0 + (S1 - S0) * Math.max(0, t - T.hud[0]) / (T.route[0] - T.hud[0]);
  if (t < T.route[1]) return S1 + (S2 - S1) * (t - T.route[0]) / (T.route[1] - T.route[0]);
  return S2 + (t - T.route[1]);
};
const swatchTime = (s) => T.route[0] + ((s - S1) / (S2 - S1)) * (T.route[1] - T.route[0]);   // inverse, inside the route

export const FOLEY = [
  { t: 0.55, sfx: "air", gain_db: -10, dur: 0.95, tone: 0.5, bright: 0.4, pan_from: -0.7, pan_to: 0.7 },        // the scan
  { t: 1.95, sfx: "swoosh_tonal", gain_db: -12, dur: 0.8, dir: "up", tone: 0.4, pan: 0 },                       // walls rise
  ...EVENTS.map((e, k) => ({ t: Math.round(swatchTime(e.s) * 1000) / 1000, sfx: "click", gain_db: -8, role: "hero", pitch: [3, 6, -2][k], pan: [-0.5, -0.1, 0.25][k] })),
  { t: T.fig, sfx: "tick", gain_db: -12, pitch: 4, pan: -0.4 },                                                 // FIG. 4
  { t: 7.5, sfx: "air", gain_db: -11, dur: 0.8, tone: 0.5, bright: 0.3, pan_from: 0.7, pan_to: -0.7 },         // the scan erases
];

export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: T.read[0], end: T.read[1] },
    { text: lib.TITLE_EN, start: T.read[0], end: T.read[1] },
    { text: lib.CAPTION_ZH, start: T.read[0], end: T.read[1] },
  ];
}

// ── the plan (metres): one floor, 32 × 18; a corridor across it, three rooms each side ─────────────────────────────
const WALLS = (() => {
  const w = [];
  const seg = (x0, y0, x1, y1, gaps = []) => {        // a wall with door gaps [from, to] along it
    const len = Math.hypot(x1 - x0, y1 - y0), ux = (x1 - x0) / len, uy = (y1 - y0) / len;
    let a = 0;
    for (const [g0, g1] of [...gaps, [len, len]]) { if (g0 > a) w.push([x0 + ux * a, y0 + uy * a, x0 + ux * g0, y0 + uy * g0]); a = g1; }
  };
  seg(0, 0, 32, 0); seg(32, 0, 32, 18); seg(32, 18, 0, 18); seg(0, 18, 0, 10.5); seg(0, 7.5, 0, 0);
  seg(3, 7.5, 32, 7.5, [[6, 7.2], [15, 16.2], [24, 25.2]]);              // the corridor's south wall, doors to 3 rooms
  seg(3, 10.5, 32, 10.5, [[4, 5.2], [13, 14.2], [23, 24.2]]);            // its north wall
  seg(3, 0, 3, 7.5); seg(3, 10.5, 3, 18);
  seg(14, 0, 14, 7.5); seg(23, 0, 23, 7.5); seg(12, 10.5, 12, 18); seg(21, 10.5, 21, 18);
  return w;
})();
const ROOMS = [{ name: "301", x: [3, 12], y: [10.5, 18] }, { name: "302", x: [12, 21], y: [10.5, 18] }, { name: "303", x: [21, 32], y: [10.5, 18] },
  { name: "304", x: [3, 14], y: [0, 7.5] }, { name: "305", x: [14, 23], y: [0, 7.5] }, { name: "306", x: [23, 32], y: [0, 7.5] }];
const DOORS = [[[9, 7.5], 1.2, 1], [[18, 7.5], 1.2, 1], [[27, 7.5], 1.2, 1], [[7, 10.5], 1.2, -1], [[16, 10.5], 1.2, -1], [[26, 10.5], 1.2, -1]];
const ROUTE = [[-3, 9], [0.6, 9], [12, 9], [16.6, 9], [16.6, 11], [16.6, 14.2]];
const ROUTE_S = [S1 - 4, EVENTS[0].s, EVENTS[1].s, EVENTS[1].s + 34, EVENTS[1].s + 48, EVENTS[2].s];   // when it passes each point
const HWALL = 3.1;

// ── camera ────────────────────────────────────────────────────────────────────────────────────────────────────────
function camera(t, lib) {
  const { seg, lerp, ease } = lib;
  const k = [
    [0, 90, 0], [1.5, 82, -5], [2.3, 56, -16], [4.45, 52, -24], [7.0, 50, -30], [7.95, 90, 0],
  ];
  let i = 0; while (i < k.length - 2 && t > k[i + 1][0]) i++;
  const [t0, p0, y0] = k[i], [t1, p1, y1] = k[i + 1];
  const e = i === k.length - 2 ? ease.inOutCubic : i === 1 ? ease.inOutCubic : ease.inOutSine;
  const u = e(seg(t, t0, t1));
  return { pitch: lerp(p0, p1, u) * Math.PI / 180, yaw: lerp(y0, y1, u) * Math.PI / 180 };
}
function projector(cam, lib) {
  const { W, H, PORTRAIT } = lib, D = PORTRAIT ? 54 : 45, f = PORTRAIT ? 1640 : 1700;
  const cx = W / 2, cy = H * (PORTRAIT ? 0.5 : 0.54), sp = Math.sin(cam.pitch), cp = Math.cos(cam.pitch);
  const yaw = cam.yaw + (PORTRAIT ? Math.PI / 2 : 0), cs = Math.cos(yaw), sn = Math.sin(yaw);   // portrait: the long side runs up the frame
  return (x, y, z = 0) => {
    const px = x - 16, py = y - 9;
    const x1 = px * cs - py * sn, y1 = px * sn + py * cs;
    const yc = y1 * sp + z * cp, zc = y1 * cp - z * sp + D;
    return [cx + (f * x1) / zc, cy - (f * yc) / zc];
  };
}

// ── frame ─────────────────────────────────────────────────────────────────────────────────────────────────────────
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  grid(ctx, tokens, lib);
  const cam = camera(t, lib), pr = projector(cam, lib);
  const dim = 1 - 0.62 * lib.ease.inOutSine(lib.seg(t, ...T.dim)) * (1 - lib.seg(t, T.sink[0], T.sink[0] + 0.3));
  // the scan reveals (world) and erases (close): everything of the model is clipped to the left of it
  const scanIn = lib.ease.inOutSine(lib.seg(t, ...T.scan)), scanOut = lib.ease.inOutSine(lib.seg(t, ...T.erase));
  const reveal = t < T.erase[0] ? -60 + (W + 120) * scanIn : (W + 60) - (W + 120) * scanOut;
  ctx.save();
  ctx.beginPath(); ctx.rect(0, 0, Math.max(0, reveal), H); ctx.clip();
  ctx.globalAlpha = dim;
  model(ctx, t, pr, tokens, lib);
  route(ctx, t, pr, tokens, lib);
  ctx.restore();
  if ((t > T.scan[0] && t < T.scan[1]) || (t > T.erase[0] && t < T.erase[1])) scanLine(ctx, reveal, tokens, lib);
  callouts(ctx, t, pr, dim, tokens, lib);
  hud(ctx, t, tokens, lib);
  type(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 12, seed: 9 });
  lib.vignette(ctx, { strength: 0.45, inner: 0.5, color: "#000000" });
}

function grid(ctx, tokens, lib) {
  const { W, H } = lib, P = (k) => lib.color(tokens, k);
  ctx.save();
  ctx.strokeStyle = lib.rgba(P("line"), 0.05); ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = 0; x <= W; x += 60) { ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, H); }
  for (let y = 0; y <= H; y += 60) { ctx.moveTo(0, y + 0.5); ctx.lineTo(W, y + 0.5); }
  ctx.stroke();
  ctx.strokeStyle = lib.rgba(P("line"), 0.16);
  ctx.beginPath();
  for (let x = 240; x < W; x += 240) for (let y = 240; y < H; y += 240) { ctx.moveTo(x - 7, y + 0.5); ctx.lineTo(x + 7, y + 0.5); ctx.moveTo(x + 0.5, y - 7); ctx.lineTo(x + 0.5, y + 7); }
  ctx.stroke();
  ctx.restore();
}

function scanLine(ctx, x, tokens, lib) {
  const { H } = lib, P = (k) => lib.color(tokens, k);
  ctx.save();
  const g = ctx.createLinearGradient(x - 140, 0, x + 6, 0);
  g.addColorStop(0, lib.rgba(P("line"), 0)); g.addColorStop(0.9, lib.rgba(P("line"), 0.10)); g.addColorStop(1, lib.rgba(P("line"), 0.30));
  ctx.fillStyle = g; ctx.fillRect(x - 140, 0, 146, H);
  ctx.fillStyle = lib.rgba(P("bright"), 0.9); ctx.fillRect(x - 1, 0, 2, H);
  ctx.restore();
}

/** The floor: the plan's walls, doors, room numbers, the corridor camera; walls extruded to h. */
function model(ctx, t, pr, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const h = HWALL * lib.ease.outCubic(lib.seg(t, ...T.extrude)) * (1 - lib.ease.inOutSine(lib.seg(t, ...T.sink)));
  const lit = lib.seg(t, swatchTime(EVENTS[2].s), swatchTime(EVENTS[2].s) + 0.25);
  ctx.save(); ctx.lineCap = "round";
  // floor slab and the lit room
  const slab = [[0, 0], [32, 0], [32, 18], [0, 18]].map(([x, y]) => pr(x, y));
  ctx.fillStyle = lib.rgba(P("line"), 0.035); poly(ctx, slab); ctx.fill();
  if (lit > 0) {
    const r = ROOMS[1];
    ctx.fillStyle = lib.rgba(P("subject"), 0.22 * lit);
    poly(ctx, [[r.x[0], r.y[0]], [r.x[1], r.y[0]], [r.x[1], r.y[1]], [r.x[0], r.y[1]]].map(([x, y]) => pr(x, y))); ctx.fill();
  }
  // walls: the plan line, the top edge, the uprights at each end; far walls fainter
  for (const [x0, y0, x1, y1] of WALLS) {
    const a = pr(x0, y0), b = pr(x1, y1);
    ctx.strokeStyle = lib.rgba(P("line"), 0.85); ctx.lineWidth = 2.2;
    line(ctx, a, b);
    if (h > 0.02) {
      const at = pr(x0, y0, h), bt = pr(x1, y1, h);
      ctx.strokeStyle = lib.rgba(P("line"), 0.55); ctx.lineWidth = 1.4; line(ctx, at, bt);
      ctx.strokeStyle = lib.rgba(P("line"), 0.32); ctx.lineWidth = 1.1; line(ctx, a, at); line(ctx, b, bt);
      ctx.fillStyle = lib.rgba(P("line"), 0.05); poly(ctx, [a, b, bt, at]); ctx.fill();
    }
  }
  // door swings
  ctx.strokeStyle = lib.rgba(P("line"), 0.4); ctx.lineWidth = 1.2;
  for (const [[x, y], w, s] of DOORS) {
    const pts = [];
    for (let i = 0; i <= 10; i++) { const a = (i / 10) * Math.PI / 2; pts.push(pr(x + Math.cos(a) * w, y + s * Math.sin(a) * w)); }
    ctx.beginPath(); pts.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py))); ctx.stroke();
  }
  // the corridor camera: a small mount and its cone of view along the corridor
  const cam = pr(12, 7.7, h * 0.95), c1 = pr(6, 8.4, 0), c2 = pr(6, 10.2, 0);
  ctx.fillStyle = lib.rgba(P("line"), 0.08); poly(ctx, [cam, c1, c2]); ctx.fill();
  ctx.fillStyle = P("bright"); ctx.beginPath(); ctx.arc(cam[0], cam[1], 5, 0, Math.PI * 2); ctx.fill();
  // room numbers, small
  lib.setFont(ctx, tokens, "mono", 24); ctx.fillStyle = lib.rgba(P("line"), 0.75); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  for (const r of ROOMS) { const [x, y] = pr((r.x[0] + r.x[1]) / 2, (r.y[0] + r.y[1]) / 2); ctx.fillText(r.name, x, y); }
  // a 5 m scale bar under the plan and a north mark beside it: the drawing says how big and which way
  ctx.strokeStyle = lib.rgba(P("line"), 0.7); ctx.lineWidth = 2;
  const s0 = pr(0, -2.2), s1 = pr(5, -2.2), s5 = pr(2.5, -2.2);
  line(ctx, s0, s1); line(ctx, pr(0, -1.8), pr(0, -2.6)); line(ctx, pr(5, -1.8), pr(5, -2.6)); line(ctx, pr(2.5, -2), pr(2.5, -2.4));
  ctx.fillText("5 m", s1[0] + 34, s1[1]);
  const n0 = pr(34.2, 15.5), n1 = pr(34.2, 18.2);
  line(ctx, n0, n1); ctx.beginPath(); ctx.arc(n1[0], n1[1], 4, 0, Math.PI * 2); ctx.fill();
  ctx.fillText("N", n1[0], n1[1] - 22);
  ctx.restore();
}
const line = (ctx, a, b) => { ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); };
const poly = (ctx, pts) => { ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath(); };

/** Where the subject is at story time s (plan metres). */
function subjectAt(s) {
  if (s <= ROUTE_S[0]) return ROUTE[0];
  for (let i = 1; i < ROUTE.length; i++) if (s <= ROUTE_S[i]) {
    const u = (s - ROUTE_S[i - 1]) / (ROUTE_S[i] - ROUTE_S[i - 1]);
    return [ROUTE[i - 1][0] + (ROUTE[i][0] - ROUTE[i - 1][0]) * u, ROUTE[i - 1][1] + (ROUTE[i][1] - ROUTE[i - 1][1]) * u];
  }
  return ROUTE[ROUTE.length - 1];
}

/** The route so far, dashed, and the subject: an amber point with a pulse. */
function route(ctx, t, pr, tokens, lib) {
  if (t < T.route[0] - 0.1) return;
  const P = (k) => lib.color(tokens, k), s = Math.min(story(t), S2);
  const sink = 1 - lib.ease.inOutSine(lib.seg(t, ...T.sink));
  const pts = [];
  for (let k = 0; k <= 80; k++) { const q = ROUTE_S[0] + ((s - ROUTE_S[0]) * k) / 80; pts.push(pr(...subjectAt(q))); }
  ctx.save(); ctx.globalAlpha *= sink;
  ctx.strokeStyle = P("subject"); ctx.lineWidth = 3; ctx.setLineDash([10, 9]); ctx.lineDashOffset = -t * 40;
  ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke();
  ctx.setLineDash([]);
  const [x, y] = pts[pts.length - 1], pulse = (t * 1.6) % 1;
  ctx.strokeStyle = lib.rgba(P("subject"), 0.8 * (1 - pulse)); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(x, y, 14 + 34 * pulse, 0, Math.PI * 2); ctx.stroke();
  // the subject is an arrow that points where it is going (its heading over the last two seconds of story time)
  let [ax, ay] = pr(...subjectAt(s - 2)), hx = x - ax, hy = y - ay;
  if (Math.hypot(hx, hy) < 1) { const [bx, by] = pr(...subjectAt(s + 2)); hx = bx - x; hy = by - y; }
  if (Math.hypot(hx, hy) < 1) { const [bx, by] = pr(...ROUTE[1]); const [cx, cy] = pr(...ROUTE[0]); hx = bx - cx; hy = by - cy; }
  ctx.save(); ctx.translate(x, y); ctx.rotate(Math.atan2(hy, hx));
  ctx.beginPath(); ctx.moveTo(19, 0); ctx.lineTo(-12, -13); ctx.lineTo(-5, 0); ctx.lineTo(-12, 13); ctx.closePath();
  ctx.fillStyle = P("subject"); ctx.shadowColor = P("subject"); ctx.shadowBlur = 16; ctx.fill();
  ctx.shadowBlur = 0; ctx.strokeStyle = lib.rgba(P("bright"), 0.9); ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.stroke();
  ctx.restore();
  ctx.restore();
}

/** Numbered callouts: a ring on the spot, a leader, a plate with the number, the time and where it comes from. */
function callouts(ctx, t, pr, dim, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const fade = 1 - lib.seg(t, T.sink[0], T.sink[0] + 0.25);
  EVENTS.forEach((e, k) => {
    const t0 = swatchTime(e.s);
    if (t < t0 || fade <= 0) return;
    const u = lib.ease.outCubic(lib.seg(t, t0, t0 + 0.3));
    const [px, py] = pr(e.at[0], e.at[1]);
    const A = lib.SAFE.action;
    lib.setFont(ctx, tokens, "zh", 46); const pw = Math.max(ctx.measureText(e.zh).width, 220) + 110;
    const bx = lib.clamp(px + e.dx * (lib.PORTRAIT ? 0.5 : 1), A.x0 + 46, A.x1 - pw + 36);
    const by = lib.clamp(py + e.dy * (lib.PORTRAIT ? 0.8 : 1), A.y0 + 250, A.y1 - 60);
    const quiet = 1 - 0.9 * lib.ease.inOutSine(lib.seg(t, ...T.dim));          // they step back while the title reads
    ctx.save(); ctx.globalAlpha = fade * quiet;
    // the ring and the leader
    ctx.strokeStyle = P("bright"); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(px, py, 22 * u + 0.01, 0, Math.PI * 2); ctx.stroke();
    const dir = by > py ? 1 : -1, ey = dir > 0 ? -58 : 54;                     // to the plate's near edge
    const lx2 = px + (bx - px) * u, ly2 = py + (by + ey - py) * u;
    ctx.beginPath(); ctx.moveTo(px, py + 22 * dir); ctx.lineTo(lx2, ly2); ctx.stroke();
    if (u > 0.6) {
      const a = lib.clamp((u - 0.6) / 0.4);
      ctx.globalAlpha *= a;
      // the plate
      const w = pw, x0 = bx - 46, y0 = by - 58;
      ctx.fillStyle = lib.rgba(P("bg"), 0.82); ctx.fillRect(x0, y0, w, 112);
      ctx.strokeStyle = lib.rgba(P("line"), 0.6); ctx.lineWidth = 1.5; ctx.strokeRect(x0 + 0.5, y0 + 0.5, w - 1, 111);
      // the number
      ctx.fillStyle = P("bright"); ctx.fillRect(x0, y0, 64, 112);
      lib.setFont(ctx, tokens, "mono", 44, { weight: 700 }); ctx.fillStyle = P("bg"); ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(k + 1), x0 + 32, y0 + 58);
      // time and source, then what happened
      ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
      lib.setFont(ctx, tokens, "mono", 26); ctx.fillStyle = lib.rgba(P("line"), 0.9);
      ctx.fillText(`${clock(e.s)} · ${e.src}`, x0 + 82, y0 + 36);
      lib.setFont(ctx, tokens, "zh", 46); ctx.fillStyle = P("bright");
      ctx.fillText(e.zh, x0 + 82, y0 + 92);
    }
    ctx.restore();
  });
}
const pad2 = (n) => String(n).padStart(2, "0");
const clock = (s) => `${pad2(Math.floor(s / 3600))}:${pad2(Math.floor(s / 60) % 60)}:${pad2(Math.floor(s) % 60)}`;

/** The timecode and the event track, top of frame. */
function hud(ctx, t, tokens, lib) {
  const a = lib.ease.outCubic(lib.seg(t, ...T.hud)) * (1 - lib.seg(t, T.erase[0], T.erase[0] + 0.3));
  if (a <= 0) return;
  const P = (k) => lib.color(tokens, k), { W, SAFE, PORTRAIT } = lib, A = SAFE.action;
  const s = story(t), ff = Math.floor((s % 1) * 25);
  ctx.save(); ctx.globalAlpha = a;
  lib.setFont(ctx, tokens, "mono", 26); ctx.fillStyle = lib.rgba(P("line"), 0.8); ctx.textBaseline = "alphabetic";
  ctx.fillText("TC  ·  FLOOR 3", A.x0 + 6, A.y0 + 36);
  lib.setFont(ctx, tokens, "mono", 54, { weight: 700 }); ctx.fillStyle = P("bright");
  ctx.fillText(`${clock(s)}:${pad2(ff)}`, A.x0 + 4, A.y0 + 96);
  // the event track: a rule from 02:13:40 to 02:17:00, a tick per event, the playhead
  const x0 = PORTRAIT ? A.x0 + 6 : A.x0 + 520, x1 = A.x1 - 10, y = PORTRAIT ? A.y0 + 150 : A.y0 + 70;
  const X = (q) => x0 + ((q - S0) / (2 * 3600 + 17 * 60 - S0)) * (x1 - x0);
  ctx.strokeStyle = lib.rgba(P("line"), 0.45); ctx.lineWidth = 2; line(ctx, [x0, y], [x1, y]);
  EVENTS.forEach((e, k) => {
    const on = s >= e.s;
    ctx.fillStyle = on ? P("bright") : lib.rgba(P("line"), 0.5);
    ctx.fillRect(X(e.s) - 2, y - 14, 4, 28);
    lib.setFont(ctx, tokens, "mono", 26, { weight: 700 }); ctx.textAlign = "center";
    ctx.fillText(String(k + 1), X(e.s), y - 22);
  });
  ctx.textAlign = "left";
  ctx.fillStyle = P("subject"); ctx.beginPath(); ctx.moveTo(X(Math.min(s, 2 * 3600 + 17 * 60)), y + 8);
  ctx.lineTo(X(Math.min(s, 2 * 3600 + 17 * 60)) - 9, y + 24); ctx.lineTo(X(Math.min(s, 2 * 3600 + 17 * 60)) + 9, y + 24); ctx.fill();
  ctx.restore();
}

/** The title as a figure caption over the dimmed model; the caption line low. */
function type(ctx, t, tokens, lib) {
  if (t < T.fig) return;
  const P = (k) => lib.color(tokens, k), { W, H, SAFE, TYPE, PORTRAIT } = lib;
  const out = 1 - lib.seg(t, T.sink[0] - 0.02, T.sink[0] + 0.2);
  if (out <= 0) return;
  const x0 = PORTRAIT ? SAFE.title.x0 : SAFE.title.x0 + 10, y = PORTRAIT ? H * 0.40 : H * 0.44;
  ctx.save();
  // a dark field behind the type
  const g = ctx.createLinearGradient(0, 0, PORTRAIT ? W : W * 0.75, 0);
  g.addColorStop(0, lib.rgba(P("bg"), 0.82 * out)); g.addColorStop(0.7, lib.rgba(P("bg"), 0.55 * out)); g.addColorStop(1, lib.rgba(P("bg"), 0));
  ctx.fillStyle = g; ctx.fillRect(0, y - TYPE.title * (PORTRAIT ? 3.1 : 1.9), W, TYPE.title * (PORTRAIT ? 4.6 : 3.1));
  // FIG. 4, a rule drawn out, then the title
  const ru = lib.ease.outCubic(lib.seg(t, T.fig, T.fig + 0.35));
  lib.setFont(ctx, tokens, "mono", 28, { weight: 700 }); ctx.fillStyle = lib.rgba(P("subject"), out);
  const lines = PORTRAIT ? ["每一帧，", "都是代码。"] : [lib.TITLE_ZH];
  const top = y - (lines.length - 1) * TYPE.title * 1.15;
  ctx.fillText("FIG. 4  ·  RECONSTRUCTION", x0, top - TYPE.title - 22);
  ctx.fillStyle = lib.rgba(P("subject"), out); ctx.fillRect(x0, top - TYPE.title - 8, (PORTRAIT ? 700 : 900) * ru, 3);
  lib.setFont(ctx, tokens, "zh", TYPE.title); ctx.fillStyle = P("bright");
  lines.forEach((ln, i) => {
    const lay = lib.layoutText(ctx, ln, { x: x0, y: top + i * TYPE.title * 1.15, align: "left" });
    lib.drawGlyphs(ctx, lay, (gl, j) => {
      const t0 = T.title + (i * 5 + j) * 0.028; if (t < t0) return null;
      return { alpha: out * lib.clamp((t - t0) / 0.12) };
    });
  });
  lib.setFont(ctx, tokens, "mono", TYPE.label); ctx.fillStyle = lib.rgba(P("line"), out * lib.clamp((t - T.title - 0.25) / 0.2));
  ctx.fillText(lib.TITLE_EN, x0, y + TYPE.label * 1.6);
  // the caption
  ctx.globalAlpha = out * lib.clamp((t - T.caption) / 0.15);
  lib.setFont(ctx, tokens, "zh", TYPE.caption, { weight: 500 }); ctx.fillStyle = P("bright"); ctx.textBaseline = "middle";
  const cy = SAFE.title.y1 - TYPE.caption * 0.55;
  ctx.fillStyle = lib.rgba(P("bg"), 0.75); const cw = ctx.measureText(lib.CAPTION_ZH).width + 60;
  ctx.fillRect(W / 2 - cw / 2, cy - TYPE.caption * 0.85, cw, TYPE.caption * 1.7);
  ctx.fillStyle = P("bright");
  lib.drawText(ctx, lib.CAPTION_ZH, W / 2, cy, { align: "center" });
  ctx.restore();
}
