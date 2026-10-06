// textcheck's side of the page: injected before the composition's own scripts (Page.addScriptToEvaluateOnNewDocument).
// It records every fillText / strokeText on a canvas in the document (the string, the transform, the font state and the
// alpha) and can skip chosen calls, so a frame can be drawn again without one read; it replays a read alone as a mask;
// and it measures. The composition only provides window.__vh.draw(t) (engines/README.md, "画面文字检查").
(() => {
  if (window.__vhTC) return;
  window.__timelines = window.__timelines || {};   // HyperFrames' runtime makes this; compositions register into it

  const KEYS = ["font", "textAlign", "textBaseline", "direction", "letterSpacing", "wordSpacing", "fontKerning", "fontStretch", "fontVariantCaps", "textRendering"];
  const SKEYS = ["lineWidth", "lineJoin", "miterLimit"];
  const H = { rec: false, calls: [], skip: null, n: 0, t: null, errors: [] };
  const alphaOf = (style) => {   // "rgba(r, g, b, a)" → a; gradients, patterns and opaque colours → 1
    if (typeof style !== "string") return 1;
    const m = style.match(/^rgba?\(([^)]*)\)$/);
    if (!m) return 1;
    const p = m[1].split(/[\s,/]+/).filter(Boolean);
    return p.length >= 4 ? parseFloat(p[3]) / (p[3].endsWith("%") ? 100 : 1) : 1;
  };
  const P = CanvasRenderingContext2D.prototype;
  const wrap = (orig, op) => function (s, x, y, maxWidth) {
    const i = H.n++;
    if (H.rec && this.canvas && this.canvas.isConnected) {
      const st = {};
      for (const k of KEYS) st[k] = this[k];
      if (op === "stroke") for (const k of SKEYS) st[k] = this[k];
      H.calls.push({ i, op, s: String(s), x: +x, y: +y, mw: arguments.length > 3 ? +maxWidth : undefined, m: this.getTransform(), st,
        a: this.globalAlpha * alphaOf(op === "fill" ? this.fillStyle : this.strokeStyle), col: op === "fill" ? this.fillStyle : this.strokeStyle, cv: this.canvas });
    }
    if (H.skip && H.skip.has(i)) return;
    return arguments.length > 3 ? orig.call(this, s, x, y, maxWidth) : orig.call(this, s, x, y);
  };
  P.fillText = wrap(P.fillText, "fill");
  P.strokeText = wrap(P.strokeText, "stroke");
  // a scene that throws inside the frame function, or catches and logs it, shows up as an error at that time
  const logError = console.error;
  console.error = function (...a) {
    if (H.t !== null) H.errors.push({ t: H.t, msg: a.map((x) => (x && x.stack) || String(x)).join(" ") });
    return logError.apply(this, a);
  };
  window.addEventListener("error", (e) => { if (H.t !== null) H.errors.push({ t: H.t, msg: String((e.error && e.error.stack) || e.message) }); });

  // ---- helpers ----
  const LIN = new Float32Array(256);
  for (let i = 0; i < 256; i++) { const c = i / 255; LIN[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  const lum = (d, p) => 0.2126 * LIN[d[p]] + 0.7152 * LIN[d[p + 1]] + 0.0722 * LIN[d[p + 2]];   // relative luminance (WCAG)
  const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  const median = (a, n) => (n ? a.subarray(0, n).sort()[n >> 1] : NaN);
  // a read matches calls by its letters: whitespace, punctuation and symbols are left out on both sides, because a film
  // often draws a "·", an arrow or a fraction bar as a shape, or puts the parts of a line in separate calls
  const strict = (s) => String(s).normalize("NFKC").replace(/[\s\p{P}\p{S}]/gu, "");
  const loose = (s) => String(s).normalize("NFKC").replace(/\s/g, "");
  const keyOf = (s) => strict(s) || loose(s);
  const EMPTY = new Set();

  async function draw(t, skip) {
    H.n = 0; H.skip = skip || null; H.rec = !skip; H.t = t;
    if (!skip) H.calls = [];
    try { await window.__vh.draw(t); } catch (e) { H.errors.push({ t, msg: String((e && e.stack) || e) }); }
    H.rec = false; H.skip = null; H.t = null;
    return H.n;
  }

  // contiguous calls of one kind on one canvas whose letters spell the read; else one call that contains it
  function runsFor(calls, text) {
    const T0 = strict(text), f = T0 ? strict : loose, T = T0 || loose(text), out = [];
    if (!T) return out;
    const lists = ["fill", "stroke"].map((op) => calls.filter((c) => c.op === op).map((c) => [c, f(c.s)]).filter((x) => x[1]));
    for (const L of lists) {
      for (let a = 0; a < L.length; a++) {
        let acc = "";
        for (let b = a; b < L.length && L[b][0].cv === L[a][0].cv; b++) {
          acc += L[b][1];
          if (acc === T) { out.push(L.slice(a, b + 1).map((x) => x[0])); break; }
          if (acc.length >= T.length || !T.startsWith(acc)) break;
        }
      }
    }
    if (!out.length && T.length >= 2) for (const L of lists) for (const [c, k] of L) if (k.includes(T)) out.push([c]);
    return out;
  }

  // the glyph box of a call in canvas pixels (its transform applied), from the font's own metrics
  const scratch = document.createElement("canvas").getContext("2d");
  function boxOf(c) {
    for (const k in c.st) try { scratch[k] = c.st[k]; } catch (e) { /* a state the browser rejects */ }
    const m = scratch.measureText(c.s);
    let l = -m.actualBoundingBoxLeft, r = m.actualBoundingBoxRight;
    if (c.mw !== undefined && m.width > c.mw && m.width > 0) { l *= c.mw / m.width; r *= c.mw / m.width; }   // maxWidth squeezes the line
    const pad = c.op === "stroke" ? (c.st.lineWidth || 1) / 2 : 0;
    const pts = [[l - pad, -m.actualBoundingBoxAscent - pad], [r + pad, -m.actualBoundingBoxAscent - pad], [l - pad, m.actualBoundingBoxDescent + pad], [r + pad, m.actualBoundingBoxDescent + pad]]
      .map(([dx, dy]) => c.m.transformPoint(new DOMPoint(c.x + dx, c.y + dy)));
    const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
  }
  const overlap = (a, b) => !(a[0] > b[2] || a[2] < b[0] || a[1] > b[3] || a[3] < b[1]);
  const union = (a, b) => [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])];

  // runs drawn over each other (a glow pass and a crisp pass, the outline and the fill) are one copy of the read
  function groupsOf(runs) {
    const groups = [];
    for (const r of runs) {
      const box = r.map(boxOf).reduce(union);
      const g = groups.find((g) => g.cv === r[0].cv && overlap(g.box, box));
      if (g) { g.calls.push(...r); g.box = union(g.box, box); } else groups.push({ cv: r[0].cv, calls: [...r], box });
    }
    for (const g of groups) {
      const fills = g.calls.filter((c) => c.op === "fill");
      g.ink = fills.length ? fills : g.calls;
      g.alpha = Math.min(...g.ink.map((c) => c.a));
      g.skip = new Set(g.calls.map((c) => c.i));
    }
    return groups;
  }

  // pixels of a canvas, copied into a canvas of our own first: after a few getImageData calls Chrome moves a canvas off
  // the GPU, and the film would then draw every later frame on the CPU, many times slower
  let copy = null;
  function pixels(cv, x, y, w, h) {
    if (!copy) copy = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
    copy.canvas.width = w; copy.canvas.height = h;
    copy.drawImage(cv, x, y, w, h, 0, 0, w, h);
    return copy.getImageData(0, 0, w, h).data;
  }
  const rgba = (c) => {   // a CSS colour string as [r, g, b] (its alpha is in the call's own alpha), else null
    if (typeof c !== "string") return null;
    let m = c.match(/^#([0-9a-f]{6})$/i);
    if (m) return [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16));
    m = c.match(/^rgba?\(([^)]*)\)$/);
    return m ? m[1].split(/[\s,/]+/).filter(Boolean).slice(0, 3).map(Number) : null;
  };

  let off = null;
  function maskOf(ink, x, y, w, h) {   // the read alone, opaque white, in a w x h window at (x, y) of its canvas
    if (!off) off = document.createElement("canvas");
    off.width = w; off.height = h;
    const g = off.getContext("2d", { willReadFrequently: true });
    for (const c of ink) {
      g.setTransform(new DOMMatrix().translate(-x, -y).multiply(c.m));
      for (const k in c.st) try { g[k] = c.st[k]; } catch (e) { /* as above */ }
      g.globalAlpha = 1; g.globalCompositeOperation = "source-over"; g.shadowBlur = 0; g.shadowColor = "transparent"; g.filter = "none";
      g.fillStyle = g.strokeStyle = "#fff";
      const args = c.mw === undefined ? [c.s, c.x, c.y] : [c.s, c.x, c.y, c.mw];
      if (c.op === "fill") g.fillText(...args); else g.strokeText(...args);
    }
    return g.getImageData(0, 0, w, h).data;
  }
  function dilate(src, w, h, r) {
    const tmp = new Uint8Array(w * h), out = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let v = 0; for (let d = Math.max(0, x - r), e = Math.min(w - 1, x + r); d <= e && !v; d++) v = src[y * w + d];
      tmp[y * w + x] = v;
    }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let v = 0; for (let d = Math.max(0, y - r), e = Math.min(h - 1, y + r); d <= e && !v; d++) v = tmp[d * w + x];
      out[y * w + x] = v;
    }
    return out;
  }
  // share: the glyph pixels that show the read: they differ from the picture without it, or they are the read's own
  // colour (white text on a white panel is not covered; its contrast says the rest). The others are covered.
  // under: the glyphs' contrast with the picture under them; edge: with what is right around them (an outline, a
  // shadow, a plate). col: the read's colour and alpha, when one solid colour
  function measure(A, B, M, w, h, col) {
    const N = w * h, core = new Uint8Array(N), ink = new Uint8Array(N);
    for (let k = 0; k < N; k++) { const a = M[k * 4 + 3]; core[k] = a > 160; ink[k] = a > 8; }
    const d4 = dilate(core, w, h, 4), d1 = dilate(core, w, h, 1);
    const pc = new Float32Array(N), ga = new Float32Array(N), rg = new Float32Array(N);
    let n = 0, vis = 0, nr = 0;
    for (let k = 0; k < N; k++) {
      const p = k * 4;
      if (core[k]) {
        if (Math.abs(A[p] - B[p]) + Math.abs(A[p + 1] - B[p + 1]) + Math.abs(A[p + 2] - B[p + 2]) > 36) vis++;
        else if (col) { let d = 0; for (let c = 0; c < 3; c++) d += Math.abs(A[p + c] - (col[3] * col[c] + (1 - col[3]) * B[p + c])); if (d <= 36) vis++; }
        const la = lum(A, p); pc[n] = ratio(la, lum(B, p)); ga[n] = la; n++;
      } else if (d4[k] && !d1[k] && !ink[k]) rg[nr++] = lum(A, p);
    }
    if (n < 20) return null;
    const under = median(pc, n), edge = nr >= 10 ? ratio(median(ga, n), median(rg, nr)) : under;
    return { px: n, share: vis / n, under, edge, contrast: Math.max(under, edge) };
  }

  // DOM captions: elements marked data-read="subtitle" (readcheck's mark) that show now, with their line boxes
  function shown(el) {
    if (!el.textContent.trim() || !el.getClientRects().length) return false;
    let o = 1;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.display === "none") return false; o *= +cs.opacity; }
    return getComputedStyle(el).visibility === "visible" && o >= 0.5;
  }
  function captions() {
    const out = [];
    for (const el of document.querySelectorAll('[data-read="subtitle"]')) {
      if ((el.parentElement && el.parentElement.closest('[data-read="subtitle"]')) || !shown(el)) continue;
      const r = document.createRange(); r.selectNodeContents(el);
      const rects = [...r.getClientRects()].filter((q) => q.width > 1 && q.height > 1).map((q) => [q.left, q.top, q.right, q.bottom]);
      if (rects.length) out.push({ el, text: el.textContent.replace(/\s+/g, " ").trim(), rects });
    }
    return out;
  }
  const toPage = (cv, b) => { const r = cv.getBoundingClientRect(), sx = r.width / cv.width, sy = r.height / cv.height; return [r.left + b[0] * sx, r.top + b[1] * sy, r.left + b[2] * sx, r.top + b[3] * sy]; };
  const toCanvas = (cv, b) => { const r = cv.getBoundingClientRect(), sx = cv.width / r.width, sy = cv.height / r.height; return [(b[0] - r.left) * sx, (b[1] - r.top) * sy, (b[2] - r.left) * sx, (b[3] - r.top) * sy]; };
  const colour = (s) => { const v = (String(s).match(/[\d.]+/g) || []).map(Number); return v.length >= 3 ? v.slice(0, 3).map((x) => (x <= 1 && /^color\(/.test(s) ? x * 255 : x)) : [255, 255, 255]; };

  // one read at time t: every copy measured, the most legible one returned
  async function sample(text, t, o, near) {
    const nA = await draw(t);
    let groups = groupsOf(runsFor(H.calls, text));
    if (near) groups = groups.filter((g) => overlap(g.box, near));
    groups = groups.slice(0, 12);
    if (!groups.length) return { t, found: false };
    const caps = captions();
    for (const g of groups) {
      const W = g.cv.width, Hh = g.cv.height, b = g.box;
      g.flags = [];
      if (b[2] < 0 || b[0] > W || b[3] < 0 || b[1] > Hh) { g.flags.push("outside"); continue; }
      if (b[0] < -1 || b[1] < -1 || b[2] > W + 1 || b[3] > Hh + 1) g.flags.push("cut");
      const x = Math.max(0, Math.floor(b[0]) - 8), y = Math.max(0, Math.floor(b[1]) - 8);
      g.win = [x, y, Math.min(W, Math.ceil(b[2]) + 8) - x, Math.min(Hh, Math.ceil(b[3]) + 8) - y];
      g.A = pixels(g.cv, ...g.win);
      g.page = toPage(g.cv, b);
      if (caps.some((c) => c.rects.some((r) => overlap(r, g.page)))) g.flags.push("caption");
    }
    for (const g of groups) if (g.win) { g.same = (await draw(t, g.skip)) === nA; g.B = pixels(g.cv, ...g.win); }
    if (groups.some((g) => g.win)) {   // the frame drawn again must be the same frame (hard rule 1), or the numbers mean nothing
      await draw(t, EMPTY);
      for (const g of groups) if (g.win) {
        const A2 = pixels(g.cv, ...g.win);
        let diff = 0; for (let p = 0; p < A2.length; p += 4) if (Math.abs(A2[p] - g.A[p]) + Math.abs(A2[p + 1] - g.A[p + 1]) + Math.abs(A2[p + 2] - g.A[p + 2]) > 24) diff++;
        if (!g.same || diff > (A2.length / 4) * 0.002) g.flags.push("unstable");
      }
    }
    const res = groups.map((g) => {
      const r = { t, found: true, copies: groups.length, alpha: g.alpha, flags: g.flags, box: g.page || toPage(g.cv, g.box) };
      if (!g.win) return r;
      const [x, y, w, h] = g.win, c0 = g.ink[0].col, rgb = g.ink.every((c) => c.col === c0) && rgba(c0);
      const m = measure(g.A, g.B, maskOf(g.ink, x, y, w, h), w, h, rgb ? [...rgb, g.alpha] : null);
      if (!m) { if (!g.flags.includes("cut")) g.flags.push("tiny"); return r; }
      if (m.share < o.minVisible) g.flags.push("covered");
      else if (m.contrast < o.minContrast) g.flags.push("contrast");   // a covered read's few visible pixels say nothing about contrast
      return Object.assign(r, m);
    });
    const bad = (r) => r.flags.filter((f) => f !== "unstable" && f !== "tiny").length;
    res.sort((a, b) => bad(a) - bad(b) || (b.contrast || 0) * (b.share || 0) - (a.contrast || 0) * (a.share || 0));
    return res[0];
  }

  // canvas text drawn as lines: consecutive fills on one canvas in one font and scale, on one baseline, side by side
  function linesOf(calls) {
    const lines = [];
    let cur = null;
    for (const c of calls) {
      if (c.op !== "fill" || !c.s.trim()) continue;
      const b = boxOf(c), m = c.m, em = (parseFloat((c.st.font.match(/([\d.]+)px/) || [0, 16])[1]) || 16) * Math.hypot(m.a, m.b), base = m.transformPoint(new DOMPoint(c.x, c.y)).y;
      const join = cur && cur.cv === c.cv && cur.font === c.st.font && Math.abs(cur.m.a - m.a) + Math.abs(cur.m.b - m.b) + Math.abs(cur.m.c - m.c) + Math.abs(cur.m.d - m.d) < 1e-3
        && Math.abs(cur.base - base) < 0.2 * em && b[0] - cur.box[2] < 0.8 * em && b[0] - cur.box[2] > -0.5 * em;
      if (join) { cur.text += c.s; cur.box = union(cur.box, b); cur.a = Math.min(cur.a, c.a); }
      else lines.push(cur = { cv: c.cv, font: c.st.font, m, base, text: c.s, box: b, a: c.a });
    }
    return lines;
  }

  window.__vhTC = {
    keyOf,
    // what the page offers: the frame function, an in-page registry, the length
    info() {
      const v = window.__vh, root = document.querySelector("[data-composition-id]");
      let texts = null;
      if (v && v.texts) try { texts = JSON.parse(JSON.stringify(typeof v.texts === "function" ? v.texts() : v.texts)); } catch (e) { texts = { error: String(e) }; }
      return { draw: !!(v && typeof v.draw === "function"), texts, duration: +((v && v.duration) || (root && root.dataset.duration) || 0),
        canvases: document.querySelectorAll("canvas").length, subtitles: document.querySelectorAll('[data-read="subtitle"]').length };
    },
    async read(text, times, o, near) {
      const out = [];
      for (const t of times) out.push(await sample(text, t, o, near));
      return out;
    },
    // a read not found as canvas text: is it DOM text showing at t?
    async dom(text, t) {
      await draw(t, EMPTY);
      const T = keyOf(text), w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let n; (n = w.nextNode());) {
        const el = n.parentElement;
        if (!el || /^(SCRIPT|STYLE|TEMPLATE)$/.test(el.tagName) || !keyOf(el.innerText || "").includes(T) || !shown(el)) continue;
        const mark = el.closest("[data-read]");
        return { dom: true, subtitle: !!(mark && mark.dataset.read === "subtitle") };
      }
      return { dom: false };
    },
    // every line of canvas text drawn at these times (for the texts outside the registry)
    async lines(times) {
      const seen = new Map();
      for (const t of times) {
        await draw(t);
        for (const l of linesOf(H.calls)) {
          const k = keyOf(l.text);
          if (!k) continue;
          if (!seen.has(k)) seen.set(k, { text: l.text.trim(), hits: [] });
          seen.get(k).hits.push([t, l.a, l.box.map(Math.round)]);
        }
      }
      return [...seen.values()];
    },
    // the picture under each DOM caption's lines: the share of its pixels within 3:1 of the caption's colour
    async captions(times) {
      const out = [];
      for (const t of times) {
        await draw(t, EMPTY);
        for (const c of captions()) {
          const col = colour(getComputedStyle(c.el).color), Lc = 0.2126 * LIN[Math.round(col[0])] + 0.7152 * LIN[Math.round(col[1])] + 0.0722 * LIN[Math.round(col[2])];
          let n = 0, close = 0, box = null;
          for (const r of c.rects) {
            const cv = document.elementsFromPoint((r[0] + r[2]) / 2, (r[1] + r[3]) / 2).find((e) => e.tagName === "CANVAS");
            if (!cv) continue;
            const q = toCanvas(cv, r), x = Math.max(0, Math.floor(q[0])), y = Math.max(0, Math.floor(q[1])), w = Math.min(cv.width, Math.ceil(q[2])) - x, h = Math.min(cv.height, Math.ceil(q[3])) - y;
            if (w <= 0 || h <= 0) continue;
            const d = pixels(cv, x, y, w, h);
            for (let p = 0; p < d.length; p += 8) { n++; if (ratio(lum(d, p), Lc) < 3) close++; }
            box = box ? union(box, r) : r;
          }
          if (n) out.push({ t, text: c.text, close: close / n, box });
        }
      }
      return out;
    },
    errors() { const e = H.errors; H.errors = []; return e; },
    async show(t) { await draw(t, EMPTY); },
  };
})();
