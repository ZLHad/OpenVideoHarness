// canvas-film · drawing library (2D canvas). Everything draws into X, the context of what is being drawn (the frame, or
// an offscreen buffer during a transition), in CSS px of the W x H frame: the device pixel ratio is in X's transform.
// Quantities a canvas does not scale with its transform (shadowBlur, shadow offsets, filter blur) are multiplied by
// PRX here, so a 4K frame (device pixel ratio 2) looks like the 1080p one, only sharper.

// ---- text: every string goes through txt(), which keeps the size floor ----
// the families film.html declares with @font-face (local() faces, nothing downloaded); o.family takes one of these keys
// or a CSS family list of its own
const FAMILIES = { sans: '"Film Sans", sans-serif', serif: '"Film Serif", serif', mono: '"Film Mono", monospace' };
let TEXTURE = 0;   // > 0 while a texture text is drawn: the floor guard (src/90-main.js) leaves it alone
// the CSS font for a size: never under FILM.minText (playbook/03 §4), unless o.texture says the text is deliberately faint
// or small (a page of source text behind the one line that matters). Texture text is never a read.
function font(px, o = {}) {
  const size = o.texture ? px : Math.max(FILM.minText, px);
  return `${o.italic ? "italic " : ""}${o.weight ?? 600} ${size}px ${FAMILIES[o.family || "sans"] || o.family}`;
}
// s at (x, y). o: size (px), weight, family, italic, color, alpha, align, base (textBaseline), ls (letter spacing, px),
// stroke (an outline width under the fill; strokeColor), shadow (a colour; blur, dy), rot (radians about x, y), texture
function txt(s, x, y, o = {}) {
  s = String(s ?? "");
  if (!s) return;
  X.save();
  X.font = font(o.size || FILM.minText, o);
  X.textAlign = o.align || "left"; X.textBaseline = o.base || "alphabetic";
  if (o.ls) X.letterSpacing = o.ls + "px";
  X.globalAlpha *= o.alpha ?? 1;
  if (o.rot) { X.translate(x, y); X.rotate(o.rot); x = y = 0; }
  if (o.texture) TEXTURE++;
  try {
    if (o.stroke) { X.lineJoin = "round"; X.lineWidth = o.stroke; X.strokeStyle = o.strokeColor || "rgba(0,0,0,0.6)"; X.strokeText(s, x, y); }
    if (o.shadow) { X.shadowColor = o.shadow; X.shadowBlur = (o.blur ?? 12) * PRX; X.shadowOffsetY = (o.dy ?? 2) * PRX; }
    X.fillStyle = o.color || FILM.ui.text;
    X.fillText(s, x, y);
  } finally { if (o.texture) TEXTURE--; X.restore(); }
}
// the width txt() would draw s at, with the same o (size, weight, family, ls, texture)
function measure(s, o = {}) {
  X.save(); X.font = font(o.size || FILM.minText, o); if (o.ls) X.letterSpacing = o.ls + "px";
  const w = X.measureText(String(s)).width; X.restore(); return w;
}
// s in lines no wider than maxW at o's font: CJK may break between any two characters, Latin between words; a closing
// mark never starts a line
function wrap(s, maxW, o = {}) {
  const tokens = String(s).match(/[A-Za-z0-9'’.,:;!?%-]+\s*|\s+|./gu) || [], CLOSE = "，。、；：！？）」』”’》,.;:!?)";
  const lines = []; let cur = "";
  for (const tk of tokens) {
    if (cur && measure((cur + tk).trimEnd(), o) > maxW && !CLOSE.includes(tk[0])) { lines.push(cur.trimEnd()); cur = tk.trimStart(); }
    else cur += tk;
  }
  if (cur.trim()) lines.push(cur.trimEnd());
  return lines;
}

// ---- shapes. o: fill, stroke (a colour), w (line width), alpha, r (corner radius), dash, shadow (a colour; blur, dy) ----
function paintPath(o) {
  if (o.shadow) { X.shadowColor = o.shadow; X.shadowBlur = (o.blur ?? 24) * PRX; X.shadowOffsetY = (o.dy ?? 8) * PRX; }
  if (o.fill) { X.fillStyle = o.fill; X.fill(); }
  X.shadowColor = "transparent";
  if (o.stroke) { X.strokeStyle = o.stroke; X.lineWidth = o.w ?? 2; if (o.dash) X.setLineDash(o.dash); X.stroke(); }
}
function rect(x, y, w, h, o = {}) {
  if (w <= 0 || h <= 0) return;
  X.save(); X.globalAlpha *= o.alpha ?? 1; X.beginPath();
  if (o.r) X.roundRect(x, y, w, h, o.r); else X.rect(x, y, w, h);
  paintPath(o); X.restore();
}
function circle(x, y, r, o = {}) {
  if (r <= 0) return;
  X.save(); X.globalAlpha *= o.alpha ?? 1; X.beginPath(); X.arc(x, y, r, o.a0 ?? 0, o.a1 ?? TAU); paintPath(o); X.restore();
}
function line(x1, y1, x2, y2, o = {}) {
  X.save(); X.globalAlpha *= o.alpha ?? 1; X.lineCap = o.cap || "round"; X.beginPath(); X.moveTo(x1, y1); X.lineTo(x2, y2);
  paintPath({ stroke: o.color || FILM.ui.text, w: o.w ?? 2, dash: o.dash }); X.restore();
}
function poly(pts, o = {}) {
  if (pts.length < 2) return;
  X.save(); X.globalAlpha *= o.alpha ?? 1; X.lineCap = "round"; X.lineJoin = "round"; X.beginPath();
  pts.forEach(([x, y], i) => (i ? X.lineTo(x, y) : X.moveTo(x, y)));
  if (o.close) X.closePath();
  paintPath(o); X.restore();
}
// a line from (x1, y1) with a head at (x2, y2)
function arrow(x1, y1, x2, y2, o = {}) {
  const c = o.color || FILM.ui.text, w = o.w ?? 4, s = o.head ?? 6 * w, a = Math.atan2(y2 - y1, x2 - x1), L = Math.hypot(x2 - x1, y2 - y1);
  const k = Math.max(0, (L - s * 0.7) / Math.max(1e-6, L));
  line(x1, y1, x1 + (x2 - x1) * k, y1 + (y2 - y1) * k, { color: c, w, alpha: o.alpha, cap: "butt" });
  X.save(); X.globalAlpha *= o.alpha ?? 1; X.translate(x2, y2); X.rotate(a); X.beginPath();
  X.moveTo(0, 0); X.lineTo(-s, -s * 0.5); X.lineTo(-s * 0.75, 0); X.lineTo(-s, s * 0.5); X.closePath(); X.fillStyle = c; X.fill(); X.restore();
}

// ---- images: FILM.images, loaded in ready ----
const IMG = {};
// image key filling the box x, y, w, h: fit "cover" (default) crops it to the box, "contain" fits it inside; fx, fy
// (0..1) pick the crop's centre, z ≥ 1 zooms in about it
function image(key, x, y, w, h, o = {}) {
  const im = IMG[key];
  if (!im) throw new Error(`image "${key}" is not in FILM.images (src/50-shots.js)`);
  const iw = im.naturalWidth || im.width, ih = im.naturalHeight || im.height;
  X.save(); X.globalAlpha *= o.alpha ?? 1;
  if (o.fit === "contain") {
    const s = Math.min(w / iw, h / ih) * (o.z || 1);
    X.drawImage(im, x + (w - iw * s) / 2, y + (h - ih * s) / 2, iw * s, ih * s);
  } else {
    const s = Math.max(w / iw, h / ih) * (o.z || 1), sw = w / s, sh = h / s;
    X.drawImage(im, clamp((o.fx ?? 0.5) * iw - sw / 2, 0, iw - sw), clamp((o.fy ?? 0.5) * ih - sh / 2, 0, ih - sh), sw, sh, x, y, w, h);
  }
  X.restore();
}

// ---- textures: a picture painted once into its own canvas and reused. paint(w, h) draws it into X; key must name
// everything it depends on, so the cached copy is exactly what painting it again would give ----
const TEX = new Map();
function texture(key, w, h, paint) {
  const k = `${key}|${w}x${h}|${PRX}`;
  if (!TEX.has(k)) {
    const cv = document.createElement("canvas"); cv.width = Math.ceil(w * PRX); cv.height = Math.ceil(h * PRX);
    const g = cv.getContext("2d"), keep = X; g.scale(PRX, PRX); X = g;
    try { paint(w, h); } finally { X = keep; }
    TEX.set(k, cv);
  }
  return TEX.get(k);
}
