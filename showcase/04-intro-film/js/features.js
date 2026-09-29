// S7 (bars 19–21): three feature modules as holographic panels; S8 (bar 22): the cases star map.
// Copy is verbatim from README.md / README.zh-CN.md ("What is this" bullets, the 30-second install, the cases/ line)
// and playbook/03-motion-design.md (the 810 px vertical safe box). Every panel element is a function of t.
export function buildFeatures(THREE, X) {
  const { scene, key, textPlane, dynPlane, quiet, hero, slamView, barMat, setAmber, sprite, glowTex, softTex, FONT_MONO, FONT_ZH, FONT_EN, P, bar, BEAT, S16, seg, win, lerp, eOutExpo, eOutCubic, clamp, hash, WAVE, DUR } = X;
  const FO = new THREE.Vector3(0, 0, -462);
  const W = (x, y, z) => new THREE.Vector3(FO.x + x, FO.y + y, FO.z + z);
  const PPU = 165; // canvas px per world unit: 1 canvas px ≈ 0.94 screen px at the 9.6 m viewing distance, fov 40
  const AMBC = new THREE.Color(1.0 * 1.6, 0.698 * 1.6, 0.141 * 1.6);
  const AMB = "#FFB224", FG = "#EDEDEF", ZHC = "#C9C9D0", DIMC = "#8B8B94";

  // ---- panel shell: dark glass + hairline frame + corner ticks ----
  function shell(w, h) {
    const g = new THREE.Group();
    const glass = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: 0x0c0c0f, transparent: true, opacity: 0, depthWrite: false, toneMapped: false, fog: false }));
    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(w, h)), new THREE.LineBasicMaterial({ color: 0x46464e, transparent: true, opacity: 0, toneMapped: false, fog: false }));
    edge.position.z = 0.005; g.add(glass, edge);
    const ticks = []; for (const [sx, sy] of [[-1, 1], [1, 1], [-1, -1], [1, -1]]) for (const hz of [true, false]) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(hz ? 0.42 : 0.035, hz ? 0.035 : 0.42), new THREE.MeshBasicMaterial({ color: AMBC, transparent: true, opacity: 0, toneMapped: false, fog: false }));
      m.position.set(sx * (w / 2 - (hz ? 0.21 : 0)), sy * (h / 2 - (hz ? 0 : 0.21)), 0.01); g.add(m); ticks.push(m);
    }
    g.userData = { glass, edge, ticks, fades: [] };
    return g;
  }
  const txt = (lines, o = {}) => { const m = textPlane(lines, { pxPerUnit: PPU, lineGap: 0.22, ...o }); m.material.fog = false; return m; };
  const add = (panel, m, x, y) => { m.position.set(x, y, 0.02); m.userData.base = m.position.clone(); panel.add(m); panel.userData.fades.push(m); return m; };
  const lineMat = (c = 0x5a5a63) => new THREE.LineBasicMaterial({ color: c, transparent: true, opacity: 0, toneMapped: false, fog: false });

  // =============== panel 1: Taste written down as numbers ===============
  const PW = 8.8, PH = 3.9; // panel sits in the lower 60% of frame; the title above it is a real main read (>= 96 px)
  const p1 = shell(PW, PH); p1.position.copy(W(-6.2, 2.0, 0)); p1.rotation.y = 0.32; scene.add(p1);
  // easing curve (easeOutExpo), drawn progressively with a dot riding it
  const gx0 = -4.05, gx1 = -1.75, gy0 = -0.5, gy1 = 1.45;
  const axes = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(gx0, gy0, 0.02), new THREE.Vector3(gx1, gy0, 0.02), new THREE.Vector3(gx0, gy0, 0.02), new THREE.Vector3(gx0, gy1, 0.02)]), lineMat(0x6a6a72)); p1.add(axes); p1.userData.fades.push(axes);
  const NC = 96, cpts = []; for (let i = 0; i <= NC; i++) { const u = i / NC, v = u >= 1 ? 1 : 1 - Math.pow(2, -10 * u); cpts.push(new THREE.Vector3(lerp(gx0, gx1, u), lerp(gy0, gy1, v), 0.03)); }
  const curve = new THREE.Line(new THREE.BufferGeometry().setFromPoints(cpts), new THREE.LineBasicMaterial({ color: AMBC, transparent: true, opacity: 0, toneMapped: false, fog: false })); p1.add(curve);
  const cdot = new THREE.Mesh(new THREE.CircleGeometry(0.07, 20), barMat(2.4)); cdot.material.transparent = true; p1.add(cdot);
  add(p1, txt([{ text: "Easing curves", size: 48, weight: 600, color: FG }, { text: "缓动曲线", size: 46, weight: 500, font: FONT_ZH, color: ZHC }]), (gx0 + gx1) / 2, -1.15);
  // vertical safe box: 9:16 frame with the 810 px-wide safe area inside
  const vw = 1.0, vh = vw * 16 / 9, vx = -0.3, vy = 0.5;
  const vframe = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(vw, vh)), lineMat(0x7a7a82)); vframe.position.set(vx, vy, 0.02); p1.add(vframe); p1.userData.fades.push(vframe);
  const sw = vw * 810 / 1080, sh = vh * 0.82;
  const sbox = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(sw, sh)), new THREE.LineBasicMaterial({ color: AMBC, transparent: true, opacity: 0, toneMapped: false, fog: false })); sbox.position.set(vx, vy, 0.03); p1.add(sbox);
  const sLab = add(p1, txt([{ text: "810px", size: 46, weight: 500, font: FONT_MONO, color: AMB }]), vx, vy + sh / 2 - 0.22);
  add(p1, txt([{ text: "vertical-video", size: 48, weight: 600, color: FG }, { text: "safe zones", size: 48, weight: 600, color: FG }, { text: "竖屏安全区", size: 46, weight: 500, font: FONT_ZH, color: ZHC }]), vx, -1.28);
  // 20-item checklist: boxes tick on 32nds
  const boxes = []; const bx0 = 1.98, by0 = 1.35, bs = 0.32, bg = 0.1;
  for (let i = 0; i < 20; i++) {
    const c = i % 4, r = Math.floor(i / 4), x = bx0 + c * (bs + bg), y = by0 - r * (bs + bg);
    const fr = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(bs, bs)), lineMat(0x6a6a72)); fr.position.set(x, y, 0.02); p1.add(fr); p1.userData.fades.push(fr);
    const fill = new THREE.Mesh(new THREE.PlaneGeometry(bs * 0.62, bs * 0.62), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.85, 0.6, 0.14), transparent: true, opacity: 0, toneMapped: false, fog: false })); fill.position.set(x, y, 0.03); p1.add(fill);
    boxes.push({ fill, tOn: bar(19, 2) + i * S16 * 0.5 });
  }
  add(p1, txt([{ text: "20-item self-review", size: 48, weight: 600, color: FG }, { text: "checklist", size: 48, weight: 600, color: FG }, { text: "20 条的自查清单", size: 46, weight: 500, font: FONT_ZH, color: ZHC }]), bx0 + 1.5 * (bs + bg), -1.28);
  const H1 = hero("Taste written down\nas numbers.", "把品味写成数字", { enSize: 150 });

  // =============== panel 2: Sound, end to end ===============
  const p2 = shell(PW, PH); p2.position.copy(W(0, 2.0, -17)); scene.add(p2);
  const NB = 44, bars2 = [];
  for (let i = 0; i < NB; i++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 1), new THREE.MeshBasicMaterial({ color: AMBC, transparent: true, opacity: 0, toneMapped: false, fog: false })); m.position.set(-4.15 + i * 0.07, 0.2, 0.02); p2.add(m); bars2.push(m); }
  const wLab = add(p2, txt([{ text: "this film's own score", size: 46, weight: 400, font: FONT_MONO, color: DIMC }]), -2.6, -1.35);
  const ROWS = [
    ["Chinese and English voiceover", "中英双语配音", "Qwen3-TTS"],
    ["bilingual captions", "双语字幕", "bin/vh captions"],
    ["code-composed music", "代码作曲", "bin/vh music"],
    ["sound effects and the final mix", "音效、混音", "15 SFX · −14 LUFS"],
  ];
  const rows2 = ROWS.map(([en, zh, tag], i) => {
    const m = add(p2, txt([{ text: en, size: 48, weight: 600, color: FG }, { text: `${zh} · ${tag}`, size: 46, weight: 500, font: FONT_ZH, color: ZHC }], { align: "left" }), 0, 1.35 - i * 0.92);
    m.position.x = -0.75 + m.geometry.parameters.width / 2; m.userData.base = m.position.clone();
    const dot = new THREE.Mesh(new THREE.CircleGeometry(0.06, 16), barMat(2.4)); dot.material.transparent = true; dot.position.set(-0.85, 1.35 - i * 0.92 + 0.15, 0.03); p2.add(dot);
    return { m, dot, tOn: bar(20, i) };
  });
  const H2 = hero("Sound, end to end.", "声音一条龙", { enSize: 150 });

  // =============== panel 3: Ready to run (a terminal types the install) ===============
  const p3 = shell(PW, PH); p3.position.copy(W(6.2, 2.0, -34)); p3.rotation.y = -0.32; scene.add(p3);
  const TL = ["$ curl -fsSL https://raw.githubusercontent.com/", "  ZLHad/OpenVideoHarness/main/install.sh | bash", "$ bin/vh new <type> <slug>"];
  const tc = document.createElement("canvas"), tg = tc.getContext("2d"); tc.width = 1440; tc.height = 350;
  const ttx = new THREE.CanvasTexture(tc); ttx.colorSpace = THREE.SRGBColorSpace; ttx.anisotropy = 8;
  const term = new THREE.Mesh(new THREE.PlaneGeometry(tc.width / PPU, tc.height / PPU), new THREE.MeshBasicMaterial({ map: ttx, transparent: true, opacity: 0, toneMapped: false, fog: false, depthWrite: false }));
  term.position.set(0, 0.45, 0.02); p3.add(term);
  const tbar = new THREE.Mesh(new THREE.PlaneGeometry(PW - 0.02, 0.36), new THREE.MeshBasicMaterial({ color: 0x1a1a1f, transparent: true, opacity: 0, toneMapped: false, fog: false })); tbar.position.set(0, PH / 2 - 0.18, 0.015); p3.add(tbar);
  const dots3 = [0, 1, 2].map((i) => { const d = new THREE.Mesh(new THREE.CircleGeometry(0.055, 16), new THREE.MeshBasicMaterial({ color: 0x55555d, transparent: true, opacity: 0, toneMapped: false, fog: false })); d.position.set(-PW / 2 + 0.3 + i * 0.2, PH / 2 - 0.18, 0.02); p3.add(d); return d; });
  add(p3, txt([{ text: "One command installs it, one command scaffolds a project.", size: 46, weight: 500, color: FG }, { text: "一条命令安装，一条命令建项目", size: 46, weight: 500, font: FONT_ZH, color: ZHC }]), 0, -1.4);
  const TOTAL1 = TL[0].length + TL[1].length;
  let termKey = null;
  function drawTerm(t) {
    // chars typed: the curl line on the 8 sixteenths 21:1–21:2.75, the scaffold line over beat 3
    const k1 = t < bar(21) ? 0 : Math.min(8, Math.floor((t - bar(21)) / S16) + 1), n1 = Math.round(TOTAL1 * k1 / 8);
    const n3 = t < bar(21, 2) ? 0 : Math.min(TL[2].length, Math.round(TL[2].length * Math.min(1, (Math.floor((t - bar(21, 2)) / S16) + 1) / 4)));
    const cur = Math.floor(t * 2.5) % 2; // cursor blink at 2.5 Hz
    const kk = `${n1}|${n3}|${cur}|${t >= bar(21, 3) ? 1 : 0}`; if (kk === termKey) return; termKey = kk;
    tg.clearRect(0, 0, tc.width, tc.height); tg.font = `400 48px ${FONT_MONO}`; tg.textBaseline = "top";
    const shown = [TL[0].slice(0, Math.min(n1, TL[0].length)), TL[1].slice(0, Math.max(0, n1 - TL[0].length)), TL[2].slice(0, n3)];
    let cx = 0, cy = 0;
    shown.forEach((s, i) => {
      const y = 20 + i * 106 + (i === 2 ? 10 : 0);
      if (i === 2 && n3 === 0) return;
      const pre = s.startsWith("$") ? "$" : "";
      tg.fillStyle = AMB; if (pre) tg.fillText(pre, 20, y);
      tg.fillStyle = i === 2 && t >= bar(21, 3) ? "#FFD27A" : FG; tg.fillText(s.slice(pre.length), 20 + tg.measureText(pre).width, y);
      cx = 20 + tg.measureText(s).width + 6; cy = y;
    });
    if (n1 === 0) { cx = 20; cy = 20; }
    if (cur) { tg.fillStyle = AMB; tg.fillRect(cx, cy + 4, 26, 50); }
    ttx.needsUpdate = true;
  }
  const H3 = hero("Ready to run.", "开箱即用", { enSize: 150 });

  // =============== S8: cases star map ===============
  const CO = new THREE.Vector3(0, 3.2, -530);
  const NS = 389, sp = new Float32Array(NS * 3), sLit = new Float32Array(NS), sSz = new Float32Array(NS);
  for (let i = 0; i < NS; i++) {
    const r = 15 * Math.sqrt(hash(i * 3.17 + 0.5)), arm = i % 2, a = arm * Math.PI + r * 0.33 + (hash(i * 5.3) - 0.5) * 0.9;
    const x = Math.cos(a) * r, z = Math.sin(a) * r, y = (hash(i * 7.1) - 0.5) * 1.2 * (1 - r / 17);
    const v = new THREE.Vector3(x, y, z).applyAxisAngle(new THREE.Vector3(1, 0, 0), 0.62);
    sp[3 * i] = CO.x + v.x; sp[3 * i + 1] = CO.y + v.y; sp[3 * i + 2] = CO.z + v.z;
    sLit[i] = bar(22) + (r / 15) * 0.7; sSz[i] = 2.2 + 3.2 * hash(i * 9.7); // a smooth ripple outward (no banded 32nd-note strobe)
  }
  const sGeo = new THREE.BufferGeometry(); sGeo.setAttribute("position", new THREE.BufferAttribute(sp, 3)); sGeo.setAttribute("aLit", new THREE.BufferAttribute(sLit, 1)); sGeo.setAttribute("aSz", new THREE.BufferAttribute(sSz, 1));
  const stars = new THREE.Points(sGeo, new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uAmt: { value: 0 }, uConv: { value: 1 }, uPre: { value: 0 }, uC: { value: CO } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `attribute float aLit; attribute float aSz; uniform float uTime, uConv, uPre; uniform vec3 uC; varying float vA;
      void main(){ vec3 p = uC + (position - uC) * mix(2.6, 1.0, uConv); vec4 mv = modelViewMatrix * vec4(p, 1.0); float age = uTime - aLit; float on = step(0.0, age);
        vA = max(on * (1.3 + 1.6 * exp(-max(age, 0.0) / 0.18)), 0.6 * uPre); gl_PointSize = min(26.0, aSz * (1.0 + 1.2 * on * exp(-max(age,0.0)/0.18)) * 64.0 / -mv.z); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform float uAmt; varying float vA; void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d); float a = smoothstep(0.5, 0.0, r);
      gl_FragColor = vec4(vec3(1.0, 0.78, 0.42) * a * vA * uAmt, a * vA * uAmt); }`,
  })); stars.frustumCulled = false; scene.add(stars);
  const CASES = Array.from({ length: 11 }, (_, j) => { const i = Math.floor(hash(j * 13.7 + 2.0) * NS); const s = sprite(glowTex, 0.5); s.position.set(sp[3 * i], sp[3 * i + 1], sp[3 * i + 2]); return { s, tOn: bar(22) + (j + 1) * S16 }; });
  // chart rings in the disc plane (a star *map*), and the 11 case studies as one constellation, drawn star to star as each lights
  const rings8 = [5, 10, 15].map((R) => { const pts = []; for (let k = 0; k <= 128; k++) { const a = (k / 128) * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(a) * R, 0, Math.sin(a) * R).applyAxisAngle(new THREE.Vector3(1, 0, 0), 0.62).add(CO)); }
    const m = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x6a5a3a, transparent: true, opacity: 0, toneMapped: false, fog: false })); scene.add(m); return m; });
  const cPts = CASES.map((c) => c.s.position.clone()).sort((a, b) => Math.atan2(a.z - CO.z, a.x - CO.x) - Math.atan2(b.z - CO.z, b.x - CO.x));
  const constel = new THREE.Line(new THREE.BufferGeometry().setFromPoints(cPts), new THREE.LineBasicMaterial({ color: new THREE.Color(1.0, 0.72, 0.2), transparent: true, opacity: 0, toneMapped: false, fog: false })); scene.add(constel);
  const H4 = quiet(dynPlane([{ text: "11 case studies", size: 170, weight: 600, color: FG, track: -0.025 }, { text: "+ curated picks from 389 community videos", size: 96, weight: 500, color: "#E4E4E8" }, { text: "11 个案例拆解 + 389 支社区作品精选", size: 84, weight: 500, font: FONT_ZH, color: "#D6D6DC" }], { lineGap: 0.3 }));

  // ---- camera ----
  const camFor = (panel, d, dy = 0.55) => { const n = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), panel.rotation.y); return [panel.position.clone().addScaledVector(n, d).add(new THREE.Vector3(0, dy, 0)), panel.position.clone().add(new THREE.Vector3(0, dy - 0.05, 0))]; };
  [[p1, 19], [p2, 20], [p3, 21]].forEach(([pn, k]) => { const dy = pn === p1 ? 1.25 : 1.1, [a0, l0] = camFor(pn, 10.0, dy), [a1, l1] = camFor(pn, 9.3, dy); key(bar(k, 0.75), a0, l0, 40, false, "f"); key(bar(k, 3.3), a1, l1, 40, false, "b"); });
  key(bar(22, 0.7), CO.clone().add(new THREE.Vector3(0, 5.5, 17)), CO.clone().add(new THREE.Vector3(0, -0.5, 0)), 44, false, "f");
  key(bar(22, 3.3), CO.clone().add(new THREE.Vector3(0.6, 4.6, 13.5)), CO.clone().add(new THREE.Vector3(0, -0.6, 0)), 44, false, "b");
  const whips = [[bar(19) + 0.02, 0.5], [bar(20) - 0.05, 0.45], [bar(21) - 0.05, 0.45], [bar(22) - 0.05, 0.5]];
  const samples = []; for (let z = 0; z > -85; z -= 2) samples.push(W((hash(z * 1.3) - 0.5) * 14, 2, z));

  const PANELS = [[p1, bar(19) - 0.3, bar(20) + 0.25, bar(19)], [p2, bar(20) - 0.3, bar(21) + 0.25, bar(20)], [p3, bar(21) - 0.3, bar(22) + 0.25, bar(21)]];
  function update(t, ctx) {
    const on = t > bar(18, 3) && t < bar(23) + 0.3;
    [p1, p2, p3].forEach((p) => { p.visible = on; }); stars.visible = on && t > bar(21, 3);
    if (!on) { [H1, H2, H3, H4].forEach((h) => { h.visible = false; }); CASES.forEach((c) => { c.s.visible = false; }); return; }
    PANELS.forEach(([pn, a, b, t0]) => {
      const o = win(t, a, b, 0.35, 0.3), U = pn.userData;
      U.glass.material.opacity = 0.86 * o; U.edge.material.opacity = 0.9 * o;
      U.ticks.forEach((m) => { m.material.opacity = o * (0.6 + 0.4 * Math.exp(-Math.max(0, t - t0) / 0.3)); });
      U.fades.forEach((m) => { m.material.opacity = o; });
      pn.visible = o > 0.002;
    });
    // panel 1
    const o1 = win(t, bar(19) - 0.3, bar(20) + 0.25, 0.35, 0.3);
    const cu = eOutCubic(seg(t, bar(19, 0.1), bar(19, 1.0)));
    curve.geometry.setDrawRange(0, Math.max(2, Math.round(cu * (NC + 1)))); curve.material.opacity = o1;
    const ph = ((t - bar(19)) / (BEAT * 2)) % 1, pu = t < bar(19) ? 0 : ph, pv = 1 - Math.pow(2, -10 * pu);
    cdot.position.set(lerp(gx0, gx1, pu), lerp(gy0, gy1, pv), 0.04); cdot.material.opacity = o1 * (t > bar(19, 1.0) ? 1 : 0);
    const sOn = t >= bar(19, 1); sbox.material.opacity = o1 * (sOn ? 0.75 + 0.25 * Math.exp(-(t - bar(19, 1)) / 0.3) : 0); sLab.material.opacity = o1 * (sOn ? 1 : 0);
    boxes.forEach((b) => { b.fill.material.opacity = o1 * (t >= b.tOn ? 0.9 : 0); });
    // panel 2: bars follow the film's own music (assets/wave.json RMS), centred on the playhead
    const o2 = win(t, bar(20) - 0.3, bar(21) + 0.25, 0.35, 0.3);
    bars2.forEach((m, i) => {
      let a = 0.2; if (WAVE && WAVE.rms) { const N = WAVE.rms.length, tt = t + (i - NB / 2) * 0.05, j = clamp(Math.round((tt / DUR) * (N - 1)), 0, N - 1); a = WAVE.rms[j]; }
      const h = 0.08 + 2.2 * a * (0.75 + 0.25 * Math.sin(i * 1.7 + t * 9.0)); m.scale.y = h; m.material.opacity = o2 * (i === NB / 2 ? 1 : 0.75);
    });
    const newest = rows2.filter((r) => t >= r.tOn).length - 1;
    rows2.forEach((r, i) => { const k = t < r.tOn ? 0.22 : i === newest ? 1 : 0.55; r.m.material.opacity = o2 * k; r.dot.material.opacity = o2 * (t >= r.tOn ? 1 : 0); setAmber(r.dot.material, 1.2 + 2.2 * (t >= r.tOn ? Math.exp(-(t - r.tOn) / 0.2) : 0)); });
    wLab.material.opacity = o2;
    // panel 3
    const o3 = win(t, bar(21) - 0.3, bar(22) + 0.25, 0.35, 0.3);
    drawTerm(t); term.material.opacity = o3; tbar.material.opacity = o3; dots3.forEach((d) => { d.material.opacity = o3; });
    // heroes
    slamView(H1, t, bar(19) + 0.08, bar(20) - 0.12, 11, 0.44, 0, 0.55);
    slamView(H2, t, bar(20) + 0.05, bar(21) - 0.12, 11, 0.52, 0, 0.68);
    slamView(H3, t, bar(21) + 0.05, bar(22) - 0.12, 11, 0.42, 0, 0.68);
    // stars
    stars.material.uniforms.uTime.value = t; stars.material.uniforms.uAmt.value = win(t, bar(22) - 0.35, bar(23) + 0.3, 0.2, 0.4) * (1 + 0.8 * Math.exp(-Math.max(0, t - bar(22)) / 0.25));
    stars.material.uniforms.uConv.value = eOutExpo(seg(t, bar(22) - 0.35, bar(22) + 0.05)); stars.material.uniforms.uPre.value = seg(t, bar(22) - 0.35, bar(22) - 0.15);
    CASES.forEach((c) => { const a = t - c.tOn; c.s.visible = a >= 0 && t < bar(23) + 0.3; c.s.material.opacity = c.s.visible ? (0.7 + 0.8 * Math.exp(-a / 0.2)) * win(t, c.tOn, bar(23) + 0.3, 0.02, 0.4) : 0; c.s.scale.setScalar(0.45 + 0.6 * Math.exp(-Math.max(0, a) / 0.25)); });
    rings8.forEach((m, i) => { m.material.opacity = 0.5 * win(t, bar(22) + i * S16, bar(23) + 0.3, 0.3, 0.4); m.visible = m.material.opacity > 0.002; });
    const nLit = CASES.filter((c) => t >= c.tOn).length; constel.geometry.setDrawRange(0, nLit); constel.material.opacity = 0.55 * win(t, bar(22), bar(23) + 0.3, 0.1, 0.4); constel.visible = nLit > 1;
    slamView(H4, t, bar(22) + 0.1, bar(23) - 0.1, 11, 0.78, 0, 0.0);
  }
  return {
    update, whips, samples, heroes: [H1, H2, H3, H4], labels: [],
    punches: [bar(22)], shakes: [[bar(19), 0.01], [bar(20), 0.008], [bar(21), 0.008], [bar(22), 0.014]],
    light: (t) => (t < bar(20) ? p1.position : t < bar(21) ? p2.position : t < bar(22) ? p3.position : CO),
    rays: (t) => { let r = 0.1; for (const k of [19, 20, 21, 22]) { const u = t - bar(k); if (u >= 0 && u < 1.5) r += 0.3 * Math.exp(-u / 0.4); } return r; },
  };
}
