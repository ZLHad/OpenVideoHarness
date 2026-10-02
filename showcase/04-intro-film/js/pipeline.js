// S6 (bars 14–18): the product's real workflow as a powered 3D node network.
// Labels are README.md / README.zh-CN.md "How it works" mermaid nodes and edge labels, verbatim.
// Local beat b = (t - T0) / BEAT, T0 = bar(14) = 36.0 s (bar 11 is 6/4); 20 beats = 5 bars. Hits (score v3.3):
//   gate ① approve b4 (38.667), gate ② approve b8 (41.333); fail b10 / b11 / b12 (42.667 / 43.333 / 44.0);
//   pass b16 (46.667); gate ③ approve b17 (47.333); final node b18 (48.0), held through b20 (49.333).
// v5 r2: fewer, longer reads. The router and types were just shown (S5), so A–F light without labels; each gate is a
// caption in the lower third ("human review ① · outline") that gets its ✓ on the approve beat, and a door made of the
// artifact under review (this film's outline, storyboard sheet, draft sheet) that the camera flies through.
const AMB = "#FFB224", CAP = "#DCA234"; // CAP: amber type kept under the streak pass's threshold (linear max < 0.82), so captions never flare
export function buildPipeline(THREE, X) {
  const { scene, key, dynPlane, quiet, barMat, gateTex, setAmber, sprite, glowTex, softTex, FONT_MONO, FONT_ZH, P, bar, BEAT, seg, win, lerp, eOutExpo, eOutCubic, clamp, pin, tubeMat } = X;
  const T0 = bar(14), O = new THREE.Vector3(0, 0, -345);
  const W = (x, y, z) => new THREE.Vector3(O.x + x, O.y + y, O.z + z);
  const at = (b) => T0 + b * BEAT; // local beat → film time
  const root = new THREE.Group(); root.position.copy(O); scene.add(root);

  // ---- nodes (mermaid A..K), local positions; `off` = when the label leaves (camera has moved on) ----
  const N = [
    { id: "A", nolab: 1, en: "One-line request", zh: "一句话需求", p: [-3.0, 0.2, 0], on: at(0), off: at(3.2), pl: { dy: -52, ay: "t" } },
    { id: "B", nolab: 1, en: "CLAUDE.md router", zh: "CLAUDE.md 路由", p: [2.4, 0.6, -7], on: at(0.5), off: at(3.6), shape: "diamond", pl: { dy: -52, ay: "t" } },
    { id: "C", nolab: 1, en: "video-types/*.md", sub: "engine · steps · taste · bans", zh: "引擎·步骤·审美·禁止项", p: [-2.8, 0.2, -14], on: at(1.0), off: at(4.2), pl: { dy: -52, ay: "t" } },
    { id: "D", nolab: 1, en: "BRIEF + outline", zh: "BRIEF + 大纲", p: [2.6, 0.5, -21], on: at(1.5), off: at(4.6), pl: { dy: -52, ay: "t" } },
    { id: "R1", en: "human review ① · outline", zh: "人工审阅 ① · 大纲", p: [0, 1.0, -32], on: at(3.0), capOn: at(3.55), off: at(7.0), gate: true, pl: { dy: 120, ay: "b" } },
    { id: "E", nolab: 1, en: "STORYBOARD + keyframe preview", zh: "STORYBOARD + 分镜预览图", p: [-2.4, 0.6, -40], on: at(4.5), off: at(7.9), pl: { dy: 52, ay: "b" } },
    { id: "R2", en: "human review ② · storyboard", zh: "人工审阅 ② · 分镜", p: [0, 1.0, -48], on: at(7.0), capOn: at(7.0), off: at(8.95), gate: true, pl: { dy: 120, ay: "b" } },   // off before the loop's labels come in
    { id: "F", nolab: 1, en: "Sound first", sub: "voice · score · beat map", zh: "声音先行 · 配音 · 配乐 · 节拍表", p: [2.3, 0.9, -56], on: at(8.0), off: at(9.3), pl: { dy: 44, ay: "b" } },
    { id: "G", en: "Scene code · f(t)", zh: "逐场景写代码", p: [-4.4, 2.6, -68], on: at(8.75), labAt: at(9.0), off: at(12.6), loop: 0, pl: { dx: -48, ax: "r" } },
    { id: "H", en: "Contact sheets", zh: "看联系表", p: [0, 7.0, -68], on: at(9.0), labAt: at(9.45), off: at(12.6), loop: 1, pl: { dy: -64, ay: "t" } },   // inside the loop: clear of the frame edge
    { id: "I", en: "20-item checklist", zh: "20 条自查清单", p: [4.4, 2.6, -68], on: at(9.25), labAt: at(9.9), off: at(12.6), loop: 2, shape: "diamond", pl: { dx: 48, ax: "l" } },
    { id: "J", nolab: 1, en: "Draft + contact sheet", zh: "初版 + 联系表", p: [-2.2, 0.6, -80], on: at(16.25), off: at(18.2), pl: { dy: 48, ay: "b" } },
    { id: "R3", en: "human review ③ · draft", zh: "人工审阅 ③ · 初版", p: [0, 1.0, -88], on: at(15.6), capOn: at(16.85), off: at(18.55), gate: true, pl: { dy: 120, ay: "b" } },
    { id: "K", en: "Final cut + LESSONS.md", zh: "成片 + LESSONS.md", p: [0, 1.4, -96], on: at(18), labAt: at(18.62), off: at(20.8), shape: "final", pl: { dy: 270, ay: "b", k: 1.45 } },
  ];
  const NID = Object.fromEntries(N.map((n) => [n.id, n]));
  N.forEach((n) => {
    const g = new THREE.Group(); g.position.set(...n.p); root.add(g); n.g = g; n.w = W(...n.p);
    const mat = barMat(0.35); n.mat = mat;
    if (n.gate) {
      const Wd = 17, Hd = 9.5, T = 0.09;
      [[0, Hd / 2, Wd, T], [0, -Hd / 2, Wd, T], [-Wd / 2, 0, T, Hd], [Wd / 2, 0, T, Hd]].forEach(([x, y, w, h]) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, T), mat); b.position.set(x, y, 0); g.add(b); });
      const tx = gateTex && gateTex[n.id];
      if (tx) { // the door is the artifact under review; the camera flies through it once it is approved
        const art = new THREE.Mesh(new THREE.PlaneGeometry(Wd - 0.5, (Wd - 0.5) * 9 / 16), new THREE.MeshBasicMaterial({ map: tx, color: new THREE.Color().setScalar(0.75), transparent: true, opacity: 0, depthWrite: false, toneMapped: false, fog: false }));
        art.position.z = -0.15; art.renderOrder = 1; g.add(art); n.art = art;
      }
    } else {
      const sides = n.shape === "diamond" ? 4 : 6, R = n.shape === "final" ? 1.3 : 0.62;
      const pts = []; for (let k = 0; k <= sides; k++) { const a = (k / sides) * Math.PI * 2 + (sides === 4 ? 0 : Math.PI / 6); pts.push(new THREE.Vector3(Math.cos(a) * R, Math.sin(a) * R, 0)); }
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x5a5a63, transparent: true, toneMapped: false }));
      g.add(line); n.line = line;
      g.add(new THREE.Mesh(new THREE.CircleGeometry(R * 0.32, 24), mat));
    }
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: softTex, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, toneMapped: false, opacity: 0 }));
    halo.scale.setScalar(n.gate ? 4 : n.shape === "final" ? 2.0 : 2.4); g.add(halo); n.halo = halo;
    if (n.shape === "final" && gateTex && gateTex.K) { // the end of the line is the film the request asked for: showcase 02, playing (9:16)
      const scr = new THREE.Mesh(new THREE.PlaneGeometry(2.48, 4.4), new THREE.MeshBasicMaterial({ map: gateTex.K, color: new THREE.Color().setScalar(1.05), transparent: true, opacity: 0, toneMapped: false, fog: false }));
      scr.position.set(0, 0.2, -0.4); scr.renderOrder = 1; g.add(scr); n.screen = scr;
      const fr = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(2.58, 4.5)), new THREE.LineBasicMaterial({ color: new THREE.Color(1.6, 1.1, 0.25), transparent: true, opacity: 0, toneMapped: false, fog: false }));
      fr.position.copy(scr.position); g.add(fr); n.screenFrame = fr;
    }
    // label: screen-pixel sized (English ≥ 52 px, Chinese ≥ 46 px), pinned beside its node
    if (n.nolab) { n.lab = null; return; }
    if (n.gate) { // caption: the same words twice, the second with its ✓ in amber (crossfaded on the approve beat)
      const cap = (ok) => { const m = quiet(dynPlane([{ text: (ok ? "✓  " : "○  ") + n.en, size: 58, weight: 600, color: ok ? CAP : "#EDEDEF", track: 0 },
        { text: n.zh, size: 50, weight: 500, font: FONT_ZH, color: ok ? "#DCC08A" : "#D6D6DC" }], { pxPerUnit: 100, lineGap: 0.26, decodeDur: 0.1 }), 1.9); scene.add(m); return m; };
      n.lab = cap(false); n.lab2 = cap(true); return;
    }
    const lines = n.en.split("\n").map((tx) => ({ text: tx, size: 56, weight: 600, color: "#EDEDEF", track: -0.01, font: n.en.includes("/*") || n.en.includes(".md") && !n.en.includes("+") ? FONT_MONO : undefined }));
    if (n.sub) lines.push({ text: n.sub, size: 48, weight: 400, color: "#C4C4CC" });
    lines.push({ text: n.zh, size: 48, weight: 500, font: FONT_ZH, color: "#D6D6DC" });
    n.lab = quiet(dynPlane(lines, { pxPerUnit: 100, lineGap: 0.26, decodeDur: 0.1 }), 1.4); scene.add(n.lab);
  });
  // gate stamps sit in the lower third of the portal, clear of the flash at its centre; loop edge labels
  const stamp = (txt, size = 60) => { const m = quiet(dynPlane([{ text: txt, size, weight: 600, font: FONT_ZH, color: CAP, track: 0.03 }], { pxPerUnit: 100 }), 1.5); scene.add(m); return m; };
  const failLabs = [1, 2, 3].map((k) => stamp(`✕  fail · 不合格  ×${k}`, 58)), passLab = stamp("✓  pass · 通过", 58);
  // inside the loop: nine frames of 02 (its contact sheet, 3×3); each fail turns one frame red with an ✕, the pass turns
  // the three amber with a ✓ (the error sounds and the pass get something to see)
  const sheet = gateTex && gateTex.LOOP ? new THREE.Group() : null, marks = [];
  if (sheet) {
    const SW = 2.05, SH = SW * 1008 / 588;
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(SW, SH), new THREE.MeshBasicMaterial({ map: gateTex.LOOP, color: new THREE.Color().setScalar(0.9), transparent: true, opacity: 0, depthWrite: false, toneMapped: false, fog: false }));
    pl.renderOrder = 2; sheet.add(pl); sheet.userData.plane = pl;
    [1, 5, 6].forEach((ti) => { // the tiles that fail: px rects in tools/request_tex.py (12 + c·192, 12 + r·332, 180×320 of 588×1008)
      const c = ti % 3, r = Math.floor(ti / 3), cx = ((12 + c * 192 + 90) / 588 - 0.5) * SW, cy = (0.5 - (12 + r * 332 + 160) / 1008) * SH;
      const tw = 180 / 588 * SW + 0.04, th = 320 / 1008 * SH + 0.04;
      const box = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(tw, th)), new THREE.LineBasicMaterial({ color: 0xff3b30, transparent: true, opacity: 0, depthTest: false, toneMapped: false, fog: false }));
      box.position.set(cx, cy, 0.02); box.renderOrder = 3; sheet.add(box);
      const x = quiet(dynPlane([{ text: "✕", size: 90, weight: 700, color: "#FF5A4F" }], { pxPerUnit: 160 }), 1.2), ok = quiet(dynPlane([{ text: "✓", size: 90, weight: 700, color: CAP }], { pxPerUnit: 160 }), 1.2);
      [x, ok].forEach((m) => { m.position.set(cx, cy, 0.04); sheet.add(m); });
      marks.push({ box, x, ok });
    });
    sheet.position.set(0, 2.6, -68 + 0.6); root.add(sheet);   // the loop's centre (LC below), just in front
  }
  const LC = new THREE.Vector3(0, 2.6, -68), LR = 4.4; // loop G(left) → H(top) → I(right) → bottom arc → G
  const failAt = W(LC.x, LC.y - LR, LC.z), passAt = W(3.4, 0.6, -74);

  // ---- conduits: A → … → G, the loop, then I → J → R3 → K ----
  const path1 = new THREE.CatmullRomCurve3(["A", "B", "C", "D", "R1", "E", "R2", "F", "G"].map((id) => new THREE.Vector3(...NID[id].p)), false, "centripetal");
  const path2 = new THREE.CatmullRomCurve3([new THREE.Vector3(...NID.I.p), new THREE.Vector3(3.4, 0.6, -74), ...["J", "R3", "K"].map((id) => new THREE.Vector3(...NID[id].p))], false, "centripetal");
  const loopPt = (a) => new THREE.Vector3(LC.x - Math.cos(a) * LR, LC.y + Math.sin(a) * LR, LC.z); // a=0 at G, π/2 at H, π at I, 3π/2 bottom
  const loopCurve = new THREE.CatmullRomCurve3(Array.from({ length: 64 }, (_, k) => loopPt((k / 64) * Math.PI * 2)), true);
  const tube1 = new THREE.Mesh(new THREE.TubeGeometry(path1, 600, 0.028, 8, false), tubeMat(THREE)); root.add(tube1);
  const tube2 = new THREE.Mesh(new THREE.TubeGeometry(path2, 300, 0.028, 8, false), tubeMat(THREE)); root.add(tube2);
  const tubeL = new THREE.Mesh(new THREE.TubeGeometry(loopCurve, 256, 0.032, 8, true), tubeMat(THREE)); root.add(tubeL);
  const glowTubes = [[path1, 600, false, tube1], [path2, 300, false, tube2], [loopCurve, 256, true, tubeL]].map(([c, n, closed, src]) => {
    const m = new THREE.Mesh(new THREE.TubeGeometry(c, n, 0.11, 8, closed), tubeMat(THREE, 0)); m.material.transparent = true; m.material.blending = THREE.AdditiveBlending; m.material.depthWrite = false;
    m.userData.src = src; root.add(m); return m; });
  const head = sprite(glowTex, 0.9); root.add(head);
  const title = quiet(dynPlane([{ text: "How it works", size: 150, weight: 600, color: "#EDEDEF", track: -0.025 }, { text: "它是怎么工作的", size: 93, weight: 500, font: FONT_ZH, color: "#D6D6DC" }]));
  const rule = quiet(dynPlane([{ text: "Check every scene.", size: 130, weight: 600, color: "#EDEDEF", track: -0.02 }, { text: "Fix until it passes.", size: 130, weight: 600, color: "#EDEDEF", track: -0.02 }, { text: "每个场景都自查，改到合格为止。", size: 80, weight: 500, font: FONT_ZH, color: "#D6D6DC" }], { lineGap: 0.3 }));
  scene.add(title); scene.add(rule);

  // ---- energy timeline (local beats) ----
  const fill1Keys = [[0, 0], [1.5, 0.39], [4, 0.5], [4.5, 0.62], [8, 0.75], [8.25, 0.87], [8.75, 1.0]];
  const fill2Keys = [[16, 0], [16.25, 0.3], [17, 0.62], [18, 1]];
  const interp = (keys, b) => { if (b <= keys[0][0]) return keys[0][1]; for (let i = 1; i < keys.length; i++) if (b <= keys[i][0]) { const [b0, v0] = keys[i - 1], [b1, v1] = keys[i]; const u = (b - b0) / (b1 - b0); return v0 + (v1 - v0) * (u * u * (3 - 2 * u)); } return keys[keys.length - 1][1]; };
  const FAILS = [10, 11, 12].map(at), PASS = at(16), GATES = { R1: at(4), R2: at(8), R3: at(17) };
  // loop head: first pass G→H→I while the loop nodes power (8.75 → 9.25), then one full lap per fail, ending at G on the fail beat
  const loopA = (b) => {
    if (b < 8.75) return 0;
    if (b < 9.25) return Math.PI * (b - 8.75) / 0.5; // G → I over the top
    if (b < 10) return Math.PI + Math.PI * (b - 9.25) / 0.75; // I → bottom → G (fail 1 at b10)
    if (b < 12) return 2 * Math.PI * ((b - 10) % 1); // laps 2 and 3 (fail at b11, b12)
    if (b < 16) return Math.PI * (b - 12) / 4; // the fixed pass: G → H → I slowly under the rule line, leaving through I on "pass"
    return Math.PI;
  };

  // ---- camera (local beats): out of the projects/ portal into an elevated 3/4 track ----
  const C = [
    [0, [0, 3.0, 12], [0, 1.0, -8], 44], [1.6, [8.05, 6.00, -2], [-0.5, 0.6, -20], 44], [3.4, [4.14, 4.80, -18.5], [0, 1.6, -34], 44],
    [4.3, [2.76, 4.60, -24.5], [0, 1.6, -38], 44], [5.2, [7.82, 5.80, -33], [-1.0, 0.6, -46], 44], [7.4, [3.68, 4.60, -38.5], [0, 1.6, -50], 44],
    [8.6, [3.3, 4.4, -44.5], [0.6, 1.8, -58], 44, "b"], [9.3, [0.69, 4.40, -52.6], [0, 2.9, -68], 46, "f"],
    [12.1, [0.42, 4.30, -54.4], [0, 2.8, -68], 46, "b"], // "b": leaves the loop hold on its own tangent (no lunge in and back before the crane) [13.3, [15.5, 25, -16], [0, -0.5, -52], 50], [15.2, [12.5, 22, -28], [0, -0.5, -58], 50],
    [16.5, [6.4, 9.0, -64], [0, 1.0, -88], 46], [17.0, [5.2, 6.6, -71], [0, 1.0, -90], 44], [18.2, [2.3, 4.6, -85.2], [0, 1.6, -96], 42], [19.8, [2.15, 4.45, -86.4], [0, 1.6, -96], 42],
  ];
  C.forEach(([b, p, l, f, tm]) => key(at(b), W(...p), W(...l), f, false, tm || null));
  const whips = [[at(0.8), 0.4], [at(4.8), 0.42], [at(8.95), 0.3], [at(17.6), 0.35]]; // no whip under the rule line: a slow crane instead
  const samples = []; for (let z = 10; z > -100; z -= 1.5) samples.push(W(0, 1, z));
  const LABELS = [...N.flatMap((n) => [n.lab, n.lab2]).filter(Boolean), ...failLabs, passLab];

  const _sd = new THREE.Vector3();
  function drawDyn(m, age, frame, decode = true) {
    m.userData.dyn.draw(age, decode ? P : { decode: 0 });
    m.material.uniforms.uSweep.value = P.sweep && decode ? lerp(-0.25, 1.25, seg(age, 0.2, 0.7)) : -1; m.material.uniforms.uFrame.value = frame; m.material.uniforms.uGlitch.value = 0;
  }
  function update(t, ctx) {
    const on = t > bar(13, 2) && t < bar(19) + 0.6; root.visible = on;
    if (!on) { LABELS.forEach((m) => { m.visible = false; }); title.visible = rule.visible = false; head.visible = false; return; }
    const b = (t - T0) / BEAT, frame = ctx.frame;
    const pano = win(t, at(12.6), at(15.6), 0.4, 0.4); // panorama: the whole chart glows so it reads as one flow
    N.forEach((n) => {
      const age = t - n.on, powered = age >= 0, flash = powered ? Math.exp(-age / 0.25) : 0;
      setAmber(n.mat, powered ? 1.1 + (n.shape === "final" ? 1.0 : 1.6) * flash : 0.25);
      if (n.line) n.line.material.color.setRGB(powered ? 1.6 : 0.35, powered ? 1.1 : 0.35, powered ? 0.25 : 0.38);
      n.halo.material.opacity = powered ? 0.05 + (n.shape === "final" ? 0.16 : 0.25) * flash + 0.35 * pano : 0;
      if (n.gate) {
        const a2 = t - GATES[n.id];
        if (a2 >= 0) setAmber(n.mat, 0.95 + 0.7 * Math.exp(-a2 / 0.2)); else if (powered) setAmber(n.mat, 0.8);
        // the door: the artifact fills the frame as the camera comes up to it, and thins out before the lens passes through
        if (n.art) { const d = n.w.distanceTo(ctx.camera.position), aa = t - (n.id === "R1" ? at(3.5) : n.on); n.art.material.opacity = (aa >= 0 ? eOutCubic(seg(aa, 0, 0.4)) : 0) * 0.5 * clamp((d - 10) / 8) * (a2 >= 0 ? 1 + 0.2 * Math.exp(-a2 / 0.25) : 1); n.art.visible = n.art.material.opacity > 0.002; }
        // caption in the lower third, riding the view; pending (○) until the approve beat, then ✓ in amber
        const ca = t - n.capOn, sa = ctx.camera.getWorldDirection(_sd).multiplyScalar(10).add(ctx.camera.position);
        const co = ca >= 0 ? eOutCubic(seg(ca, 0, 0.2)) * (1 - seg(t, n.off - 0.3, n.off)) : 0, ok = a2 >= -0.5 / 30 ? 1 : 0;   // a cut, not a crossfade (no double image)
        [[n.lab, 1 - ok], [n.lab2, ok]].forEach(([m, w]) => {
          const o2 = co * w * pin(m, sa, { dy: -330, k: m === n.lab2 ? lerp(1.12, 1, eOutExpo(seg(a2, 0, 0.3))) : 1 });
          m.material.opacity = o2; m.visible = o2 > 0.002; m.userData.quiet.material.opacity = 0.97 * co; if (m.visible) drawDyn(m, 9, frame, false);
        });
        return;
      }
      if (n.screen) { const so = (powered ? eOutCubic(seg(age, 0, 0.5)) : 0) * (1 - seg(t, n.off - 0.3, n.off)); n.screen.material.opacity = so; n.screenFrame.material.opacity = 0.8 * so; n.screen.visible = n.screenFrame.visible = so > 0.002; }
      if (!n.lab) return;
      const L = n.lab, near = pin(L, n.w, n.pl), la = t - (n.labAt || n.on);
      const o = (la >= 0 ? eOutCubic(seg(la, 0, 0.22)) : 0) * (1 - seg(t, n.off - 0.3, n.off)) * near;
      L.material.opacity = o; L.visible = o > 0.002; L.userData.quiet.material.opacity = 0.96 * o;
      if (L.visible) drawDyn(L, la, frame, false);
    });
    // conduits + the head of the energy
    [tube1, tube2, tubeL].forEach((m) => { m.material.uniforms.uGain.value = 1 + 1.6 * pano; });
    glowTubes.forEach((m) => { m.visible = pano > 0.01; const U = m.material.uniforms, S = m.userData.src.material.uniforms; U.uFill.value = S.uFill.value; U.uGain.value = 0.55 * pano; U.uHead.value = 0; });
    tube1.material.uniforms.uFill.value = interp(fill1Keys, b);
    const la = loopA(b);
    tubeL.material.uniforms.uFill.value = b < 8.75 ? 0 : b < 16 ? Math.max(0.02, (la / (2 * Math.PI)) % 1) : 1; tubeL.material.uniforms.uHead.value = b < 16 ? 1 : 0;
    tube2.material.uniforms.uFill.value = interp(fill2Keys, b); tube2.material.uniforms.uHead.value = b >= 16 && b < 18 ? 1 : 0;
    let hp;
    if (b < 8.75) hp = path1.getPointAt(clamp(interp(fill1Keys, b)));
    else if (b < 16) hp = loopPt(la);
    else hp = path2.getPointAt(clamp(interp(fill2Keys, b)));
    head.position.copy(hp); head.visible = b < 18.1; head.scale.setScalar(0.4 + 0.25 * ctx.PUL.down(t));
    // fail label: on from the first fail to the rule line, a pop on each fail (never flashes out mid-read)
    let pop = 0; FAILS.forEach((h) => { const u = t - h; if (u >= 0 && u < 0.5) pop = Math.max(pop, 1 - u / 0.5); });
    const fo = (t >= FAILS[0] - 1 / 30 ? win(t, FAILS[0] - 1 / 30, at(12.7), 0.06, 0.3) : 0);
    const fk = FAILS.filter((f) => t >= f - 1 / 30).length - 1; // which count is showing (×1, ×2, ×3)
    failLabs.forEach((m, k) => {
      const fa = k === Math.max(0, fk) ? fo * pin(m, failAt, { dy: -150, ay: "t", k: 1 + 0.12 * pop }) : 0;   // below the loop's bottom arc
      m.material.opacity = fa; m.visible = fa > 0.002; m.userData.quiet.material.opacity = 0.9 * fa; if (fa) drawDyn(m, 9, frame, false);
    });
    if (pop) setAmber(NID.I.mat, 1.15 + 1.8 * pop);
    if (sheet) { // the 3×3 of 02 inside the loop: from the loop lighting up to the rule line's end
      const so = win(t, at(8.9), at(16.6), 0.3, 0.4); sheet.userData.plane.material.opacity = 0.9 * so; sheet.visible = so > 0.002;
      marks.forEach((mk, k) => {
        const failed = t >= FAILS[k] - 1 / 30, passed = t >= PASS - 1 / 30, fp = failed ? Math.exp(-Math.max(0, t - FAILS[k]) / 0.25) : 0;
        mk.box.material.opacity = so * (failed ? 1 : 0); mk.box.material.color.setRGB(passed ? 1.0 : 1.0 + 1.2 * fp, passed ? 0.7 : 0.23, passed ? 0.14 : 0.19);
        mk.x.material.opacity = so * (failed && !passed ? 1 : 0); mk.ok.material.opacity = so * (passed ? 1 : 0);
        [mk.x, mk.ok].forEach((m) => { m.visible = m.material.opacity > 0.002; m.userData.quiet.material.opacity = 0.5 * m.material.opacity; if (m.visible) drawDyn(m, 9, frame, false); });
      });
    }
    // "pass" rides the view like the approval stamps (same place, in sequence: pass → approved ③ → final node)
    const pa = (t >= PASS - 1 / 30 ? win(t, PASS - 1 / 30, at(16.75), 0.05, 0.12) : 0) * pin(passLab, ctx.camera.getWorldDirection(_sd).multiplyScalar(10).add(ctx.camera.position), { dy: -300, k: lerp(1.25, 1, eOutExpo(seg(t - PASS, 0, 0.25))) });
    passLab.material.opacity = pa; passLab.visible = pa > 0.002; passLab.userData.quiet.material.opacity = 0.92 * pa; if (pa) drawDyn(passLab, 9, frame, false);
    // heroes (camera-stable, in the world)
    X.slamView(title, t, T0 + 0.1, at(3.45), 11, 0.42, -0.42, 0.62);
    X.slamView(rule, t, at(12.65), at(15.8), 11, 0.72, 0, 0.36, 1);   // no scramble: it lands where the loop's labels just were if (rule.visible) rule.userData.quiet.material.opacity = 0.9 * rule.material.opacity;   // inside the title-safe frame; the ring passes behind a scrim
  }
  return {
    whips, samples, update, root, heroes: [title, rule], labels: LABELS,
    shakes: [[GATES.R1, 0.01], [GATES.R2, 0.01], ...FAILS.map((f) => [f, 0.006]), [PASS, 0.018], [GATES.R3, 0.01]],
    punches: [], // no shockwave on "pass": the ring would sit on the pass label
    light: (t) => { const b = (t - T0) / BEAT; if (b < 4.3) return W(0, 1.0, -32); if (b < 8.3) return W(0, 1.0, -48); if (b < 16) return W(...NID.I.p); if (b < 17.5) return W(0, 1.0, -88); return W(0, 1.4, -96); },
    rays: (t) => { const b = (t - T0) / BEAT; let r = 0.06; for (const g of [4, 8, 17]) { const u = b - g; if (u >= 0 && u < 3) r += 0.3 * Math.exp(-u / 0.8); } return r; },
    ca: (t) => { let r = 0; for (const f of FAILS) { const u = t - f; if (u >= 0 && u < 0.2) r += 0.12 * Math.exp(-u / 0.06); } return r; },
  };
}
