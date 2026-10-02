// S5 (bars 10–13): the repo's architecture as a powered 3D node network.
// Every label is copied from docs/assets/architecture.en.svg / architecture.zh.svg; the 8 type names are the README's
// first paragraph ("explainers, science shorts, …" / "科普、讲解、…"), paired in README order with video-types/01..08.
// Four stations along the camera path; each node powers on the beat its conduit delivers energy, then its label decodes.
export function buildArch(THREE, X) {
  const { scene, key, dynPlane, quiet, barMat, setAmber, sprite, glowTex, softTex, FONT_MONO, FONT_ZH, P, bar, BEAT, seg, win, lerp, eOutCubic, clamp, pin, tubeMat, hash } = X;
  const AO = new THREE.Vector3(0, 0, -262);
  const W = (x, y, z) => new THREE.Vector3(AO.x + x, AO.y + y, AO.z + z);
  const root = new THREE.Group(); scene.add(root);

  // bilingual label (screen-pixel sized by pin(): English 54 px, supporting lines 44–46 px)
  function label(en, zh, o = {}) {
    const lines = [{ text: en, size: o.enSize || 54, weight: 600, color: "#EDEDEF", font: o.mono ? FONT_MONO : undefined, track: o.mono ? 0 : -0.01 }];
    if (o.sub) lines.push({ text: o.sub, size: 48, weight: 400, color: "#C8C8D0", font: o.subMono ? FONT_MONO : undefined });
    if (zh) lines.push({ text: zh, size: o.zhSize || 48, weight: 500, font: FONT_ZH, color: "#D6D6DC" });
    if (o.zhSub) lines.push({ text: o.zhSub, size: 48, weight: 400, font: FONT_ZH, color: "#C4C4CC" });
    const m = quiet(dynPlane(lines, { pxPerUnit: 100, lineGap: 0.26, decodeDur: 0.1 }), 1.4); scene.add(m); return m;
  }
  // a card frame + amber tab that scale with their label (station 3)
  function card(m) {
    const w = m.geometry.parameters.width * (m.userData.contentFrac || 1) + 0.3, h = m.geometry.parameters.height + 0.12;
    const fr = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(w, h)), new THREE.LineBasicMaterial({ color: 0x4a4a52, transparent: true, opacity: 0, depthTest: false, toneMapped: false }));
    fr.renderOrder = 10; fr.position.z = -0.01; m.add(fr);
    const body = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: 0x0b0b0e, transparent: true, opacity: 0, depthTest: false, toneMapped: false })); body.renderOrder = 9; body.position.z = -0.02; m.add(body);
    const tab = new THREE.Mesh(new THREE.PlaneGeometry(0.1, h * 0.8), barMat(2.0)); tab.material.depthTest = false; tab.material.transparent = true; tab.renderOrder = 11; tab.position.set(-w / 2 - 0.02, 0, 0); m.add(tab); // the amber tab sits on the card's edge, clear of the text
    m.userData.card = { fr, tab, body }; return m;
  }

  const TYPES = [["explainers", "讲解"], ["science shorts", "科普"], ["product films", "产品片"], ["music videos", "MV"], ["data stories", "数据"], ["paper talks", "论文"], ["hand-drawn", "手绘"], ["meme edits", "梗图快剪"], ["your footage", "素材剪辑"]];
  // stations: 1 = request → agent → router; 2 = video-types/ + 8 spokes; 3 = four doc/tool cards; 4 = engines, references, projects/ (the portal)
  const N = [
    { id: "you", p: W(-4.6, 2.5, 0), on: bar(10, 0), labAt: bar(10) + 0.55, off: bar(11) - 0.15, st: 1, L: () => label("You: a one-line request", "你：一句话需求"), pl: { dy: -58, ay: "t" } },
    { id: "agent", from: "you", p: W(4.6, 2.5, 0), on: bar(10, 1), off: bar(11) - 0.15, st: 1, L: () => label("Claude Code / Codex", null, { enSize: 58 }), pl: { dy: -58, ay: "t" } },
    { id: "router", from: "agent", p: W(0, -0.4, -6), on: bar(10, 2), off: bar(11) - 0.15, st: 1, shape: "diamond", R: 0.95,
      L: () => label("CLAUDE.md router", "CLAUDE.md 路由", { enSize: 58 }), pl: { dy: -78, ay: "t" } },   // short: read in the station's hold
    { id: "vt", from: "router", p: W(-11.2, 1.3, -20), on: bar(11, 0), off: bar(12) - 0.15, st: 2, R: 0.85,
      L: () => label("video-types/", "9 类视频工作流", { mono: true, enSize: 58, sub: "9 video workflows" }), pl: { dy: -74, ay: "t" } },
    ...TYPES.map(([en, zh], j) => ({ id: "t" + j, from: "vt", p: W(-5.6, 4.45 - j * 0.78, -20 - 0.4 * Math.sin(j * 0.9)), on: bar(11, 0.5 * j), off: bar(12) - 0.15, st: 2, shape: "dot",
      L: () => label(`0${j + 1}  ${en}${j === 8 ? " (exp.)" : ""} · ${zh}`, null, { enSize: 50 }), pl: { dx: 46, ax: "l" } })),
    { id: "pb", from: "router", p: W(3.1, 3.0, -36), on: bar(12, 0), off: bar(13) - 0.1, st: 3, shape: "card", L: () => card(label("playbook/", "通用知识 13 篇", { mono: true, sub: "13 know-how docs" })) },
    { id: "tp", from: "router", p: W(9.9, 3.0, -36), on: bar(12, 0.5), off: bar(13) - 0.1, st: 3, shape: "card", L: () => card(label("templates/", "11 个项目模板", { mono: true, sub: "11 project templates" })) },
    { id: "cs", from: "router", p: W(3.1, -0.1, -36), on: bar(12, 2.0), off: bar(13) - 0.1, st: 3, shape: "card", L: () => card(label("styles/", "31 种风格 · 各带样片", { mono: true, sub: "31 styles · real samples" })) },
    { id: "bv", from: "router", p: W(9.9, -0.1, -36), on: bar(12, 2.4), off: bar(13) - 0.1, st: 3, shape: "card", L: () => card(label("bin/vh", "建项目 · 自查工具", { mono: true, sub: "scaffold · QA tools" })) },
    { id: "eng", from: "cs", p: W(-5.2, 0.9, -54), on: bar(13, 0), off: bar(13, 3.1), st: 4, L: () => label("engines/", "p5.brush · Blender", { mono: true, sub: "HyperFrames · Manim", zhSub: "渲染引擎" }), pl: { dx: 30, dy: -50, ax: "l", ay: "t" } }, // below, toward the centre: clear of its feed, the portal and the frame edge
    { id: "ref", from: "bv", p: W(5.2, 0.9, -54), on: bar(13, 1.3), off: bar(13, 3.1), st: 4, L: () => label("references/", "30 个参考仓库，只读", { mono: true, sub: "30 repos, read-only" }), pl: { dx: -30, dy: -50, ax: "r", ay: "t" } },
    { id: "prj", from: "bv", p: W(0, 3.0, -62), on: bar(13, 2), off: bar(13, 2), noLab: 1, st: 4, shape: "portal", R: 2.4,
      L: () => label("projects/date-slug", "大纲 → 分镜 → 初版 → 成片", { mono: true, enSize: 60, sub: "outline → storyboard → draft → final", zhSize: 48 }), pl: { dy: -250, ay: "t" } },
  ];
  const NID = Object.fromEntries(N.map((n) => [n.id, n]));

  // ---- node bodies ----
  N.forEach((n) => {
    const g = new THREE.Group(); g.position.copy(n.p); root.add(g); n.g = g;
    n.mat = barMat(0.25);
    if (n.shape === "card") {
      const core = new THREE.Mesh(new THREE.CircleGeometry(0.1, 16), n.mat); g.add(core);
    } else if (n.shape === "dot") {
      const core = new THREE.Mesh(new THREE.CircleGeometry(0.11, 16), n.mat); g.add(core);
    } else {
      const sides = n.shape === "diamond" ? 4 : 6, R = n.R || 0.62;
      const pts = []; for (let k = 0; k <= sides; k++) { const a = (k / sides) * Math.PI * 2 + (sides === 4 ? 0 : Math.PI / 6); pts.push(new THREE.Vector3(Math.cos(a) * R, Math.sin(a) * R, 0)); }
      if (n.shape === "portal") { // a thick hexagon of light the camera flies through
        for (let k = 0; k < sides; k++) { const a = pts[k], b = pts[k + 1]; const len = a.distanceTo(b); const bm = new THREE.Mesh(new THREE.BoxGeometry(len, 0.07, 0.07), n.mat); bm.position.copy(a).add(b).multiplyScalar(0.5); bm.rotation.z = Math.atan2(b.y - a.y, b.x - a.x); g.add(bm); }
      } else {
        n.line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x5a5a63, transparent: true, toneMapped: false })); g.add(n.line);
        g.add(new THREE.Mesh(new THREE.CircleGeometry(R * 0.3, 24), n.mat));
      }
    }
    n.halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: softTex, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, toneMapped: false, opacity: 0 }));
    n.halo.scale.setScalar(n.shape === "portal" ? 7 : n.shape === "dot" ? 0.9 : 2.2); g.add(n.halo);
    n.lab = n.L();
  });
  // ---- conduits (parent → child), a gentle arc; energy arrives on the child's beat ----
  const tubes = [];
  N.filter((n) => n.from).forEach((n) => {
    const a = NID[n.from].p, b = n.p, mid = a.clone().lerp(b, 0.5);
    mid.y += 0.6 + 0.02 * a.distanceTo(b);
    // feeds that would pass by the lens run low and come up from behind their target instead
    const pts = n.st === 3 ? [a, W(6.5, -5.5, -48), b] : n.id === "vt" ? [a, W(-6, -4.5, -26), b] : [a, mid, b];
    const curve = new THREE.CatmullRomCurve3(pts, false, "centripetal");
    const lead = n.st === 2 && n.id !== "vt" ? 0.2 : 0.34;
    const m = new THREE.Mesh(new THREE.TubeGeometry(curve, 80, n.st === 2 && n.id !== "vt" ? 0.018 : 0.045, 6, false), tubeMat(THREE, 0.16)); root.add(m);
    tubes.push({ m, t0: n.on - lead, t1: n.on, st: n.st, id: n.id });
  });

  // ---- camera: a key per station, a pull-up reveal, then a dive through projects/ ----
  // arrival keys take the tangent of the slow hold that follows ("f"), departure keys the hold before them ("b"),
  // so the whips between stations are clean S-curves with no overshoot into the labels
  const K = [
    [bar(10) + 0.85, W(0, 3.5, 14.5), W(0, 1.1, -3), 40, "f"],
    [bar(10, 3.2), W(0, 3.3, 13.0), W(0, 1.0, -3), 40, "b"],
    [bar(11, 0.8), W(-6.1, 2.2, -5.4), W(-6.6, 1.3, -20), 40, "f"],
    [bar(11, 5.3), W(-6.2, 2.05, -7.2), W(-6.6, 1.3, -20), 40, "b"],
    [bar(12, 0.75), W(6.5, 2.1, -22.4), W(6.5, 1.45, -36), 40, "f"],
    [bar(12, 3.3), W(6.5, 2.05, -23.6), W(6.5, 1.45, -36), 40, "b"],
    [bar(13, 0.7), W(0, 2.9, -39.5), W(0, 1.9, -58), 42, "f"],
    [bar(13, 2.6), W(0, 3.0, -43.0), W(0, 2.3, -60), 42, "b"],
    [bar(13, 3.5), W(0, 3.1, -55.5), W(0, 3.0, -70), 42, null],
  ];
  K.forEach(([t, p, l, f, tm]) => key(t, p, l, f, false, tm));
  const whips = [[bar(10) + 0.15, 0.5], [bar(11) - 0.1, 0.45], [bar(12) - 0.1, 0.45], [bar(13) - 0.05, 0.5]];
  const samples = []; for (let z = 5; z > -70; z -= 2) samples.push(W((hash(z) - 0.5) * 16, 1.5, z));

  const LAB_ALL = N.map((n) => n.lab); const NODEC = { decode: 0 };
  function update(t, ctx) {
    const on = t > bar(9, 3) && t < bar(14) + 0.4; root.visible = on;
    if (!on) { N.forEach((n) => { n.lab.visible = false; }); return; }
    const wide = 0;
    // the request's thread: once the list is up, its type (02) lights and the other eight become texture; among the
    // folders, styles/ (the one a request borrows from) stays lit
    const hlT = seg(t, bar(11, 4.5), bar(11, 4.5) + 0.4), hlC = seg(t, bar(12, 2.8), bar(12, 2.8) + 0.4);
    const dimOf = (id) => (/^t[0-8]$/.test(id) && id !== "t1" ? 1 - 0.65 * hlT : ["pb", "tp", "bv"].includes(id) ? 1 - 0.55 * hlC : 1);
    tubes.forEach((tb) => { const U = tb.m.material.uniforms; U.uFill.value = eOutCubic(seg(t, tb.t0, tb.t1)); U.uGain.value = (1 + 1.3 * wide) * (tb.id === "t1" ? 1 + 1.5 * hlT : dimOf(tb.id)); tb.m.visible = !(tb.st === 1 && t > bar(11) - 0.1) && !(tb.id === "prj" && t > bar(13, 3.1)); });
    N.forEach((n) => {
      const age = t - n.on, powered = age >= 0, flash = powered ? Math.exp(-age / 0.22) : 0;
      setAmber(n.mat, powered ? 1.15 + 1.8 * flash : 0.25);
      if (n.line) n.line.material.color.setRGB(powered ? 1.6 : 0.35, powered ? 1.1 : 0.35, powered ? 0.25 : 0.38);
      n.halo.material.opacity = powered ? (n.shape === "portal" ? 0.12 + 0.3 * flash : 0.14 + 0.26 * flash + 0.3 * wide) : 0;
      n.halo.scale.setScalar((n.shape === "portal" ? 7 : n.shape === "dot" ? 0.9 : 2.2) * (1 + 2.2 * wide));
      // label: decodes on power-up, fades when the camera leaves the station
      // station-1 bodies go away once the camera has left (its whip to station 2 passes right by them)
      n.g.visible = !(n.st === 1 && t > bar(11) - 0.1) && !(n.id === "prj" && t > bar(14) - 0.15);
      if (n.id === "prj") setAmber(n.mat, (powered ? 1.15 + 1.8 * flash : 0.25) * clamp((bar(14) - 0.1 - t) / 0.35));
      const la = t - (n.labAt || n.on); // the request label waits for the whip into station 1 to land
      const big = n.id === "t1" ? 1 + 0.15 * hlT : n.id === "cs" ? 1 + 0.08 * hlC : 1;
      const L = n.lab, near = pin(L, n.p, n.shape === "card" ? { dx: 0, dy: 0, k: big } : { ...n.pl, k: big });
      const o = n.noLab ? 0 : (la >= 0 ? eOutCubic(seg(la, 0, 0.22)) : 0) * (1 - seg(t, n.off - 0.25, n.off)) * near * dimOf(n.id);
      if (n.id === "t1" && hlT > 0) setAmber(n.mat, 1.15 + 2.0 * hlT);
      L.material.opacity = o; L.visible = o > 0.002; L.userData.quiet.material.opacity = (n.shape === "card" ? 0.94 : 0.92) * o;
      if (L.visible) {
        L.userData.dyn.draw(la, NODEC); L.material.uniforms.uSweep.value = -1; L.material.uniforms.uFrame.value = ctx.frame;
        L.material.uniforms.uGlitch.value = 0;
      }
      if (L.userData.card) { L.userData.card.fr.material.opacity = 0.9 * o; L.userData.card.tab.material.opacity = o; L.userData.card.body.material.opacity = 0.9 * o; }
    });
  }
  return {
    update, root, whips, samples, labels: LAB_ALL, heroes: [],
    punches: [], shakes:   // no shock ring at the portal: it swept across the engines/references labels (round 3)
      [[bar(10, 2), 0.012], [bar(11), 0.008], [bar(13, 2), 0.02]],
    light: (t) => (t < bar(11) ? NID.router.p : t < bar(12) ? NID.vt.p : t < bar(13) ? W(6.5, 1.4, -36) : NID.prj.p),
    rays: (t) => { let r = 0.12; for (const n of [NID.router, NID.vt, NID.prj]) { const u = t - n.on; if (u >= 0 && u < 2) r += 0.35 * Math.exp(-u / 0.5); } return r; },
  };
}
