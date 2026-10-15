// src/50-shots.js · THIS FILM: its settings, chapters and shots. The rest of src/ is the engine (engines/canvas-film/).
// What is here now is an example that goes with the example narration in audio/timeline.zh.json: replace both.
//
// A shot: { id, at, tin, cam, light, nocap, see, o, draw(t, s) }
//   at     when it starts: a cue ("@a2", "@a2:第一张", "@a2>", each with an optional +0.3 / -0.2) or seconds; it runs
//          until the next shot starts (the first shot starts the film)
//   tin    how it comes in: cut (default), settle, dim, fold, turn, blot (src/30-transitions.js), or [name, seconds]
//   cam    [z0, z1, cx, cy]: a slow camera drift over the shot · light: a pale picture (the caption goes on a plate)
//   nocap  narration lines whose captions the film leaves out (the picture already shows those words large)
//   see    what the viewer must get from it, for the storyboard and the review
//   segment / reads / label / unsure: optional storyboard metadata. segment defaults to the chapter at the cut;
//          reads defaults to see. window.film.shots exports these with the resolved start/end (not the cue strings).
//   o      the shot's own times and values: every cue in it, at any depth, becomes seconds before the first frame, and
//          one that no longer resolves stops the film in ready, naming the shot and the cue
//   draw(t, s)  paints the shot at film time t: s = { id, t0, t1, lt, u, o, … } (src/90-main.js, drawShot)

Object.assign(FILM, {
  lang: "zh",                          // audio/timeline.zh.json (its first line starts 0.5 s in, as bin/vh tts --lead 0.5 writes it)
  tail: 2.5,                           // the film ends 2.5 s after the narration
  images: { bulb: "assets/bulb.svg" },
});

// this film's colours
const PAL = { night: "#1B1F27", paper: "#EEEAE1", ink: "#22252B", soft: "#98A1B0", amber: "#E8A33D", rust: "#B0620E", teal: "#4FB0A5" };

const CHAPTERS = [
  { at: 0, title: "挂在字上" },
  { at: "@b1", title: "翻一页" },
];

// a word that pops up at `at` on a light chip (a read once it is up), with an event "pop"
function chip(t, at, word, x, y, hot) {
  cue("pop", at, { x, y });
  read(word, at + 0.3, Infinity);
  const k = eOutBack(seg(t, at, at + 0.3), 2.2);
  if (k <= 0) return;
  const w = measure(word, { size: 48 }) + 44;
  X.save(); X.translate(x, y); X.scale(k, k);
  rect(-w / 2, -40, w, 76, { fill: hot ? PAL.amber : PAL.paper, r: 12 });
  txt(word, 0, 16, { size: 48, color: PAL.ink, align: "center" });
  X.restore();
}
// a numbered card that drops in at `at` (an event "drop") onto a dashed outline; its word is a read once it has landed
function card(t, at, cx, cy, n, word) {
  read(word, at + 0.45, Infinity);
  rect(cx - 210, cy - 160, 420, 320, { stroke: PAL.soft, w: 3, r: 18, dash: [14, 12], alpha: 0.5 * (1 - show(t, at, 0.3)) });
  drop(t, at, cx, cy, () => {
    rect(cx - 210, cy - 160, 420, 320, { fill: PAL.paper, r: 18, shadow: "rgba(0,0,0,0.45)" });
    txt(n, cx, cy + 20, { size: 160, weight: 900, family: "serif", color: PAL.rust, align: "center" });   // amber on paper is under 3:1
    txt(word, cx, cy + 115, { size: 48, color: PAL.ink, align: "center" });
  });
}

// covers: a frame picked by cue (it follows the narration when the opening changes), the camera nudged for room, a title
//   at     a cue or seconds, as a shot's · cam { z, x, y }: zoom about the middle, then move by x, y px (within
//          (z - 1) x 960 and (z - 1) x 540, or the frame's edge shows)
//   title  { text: [lines], size: [px per line], x, y (first baseline), align, color, band } in "Film Heavy"
//   bar, caption: true to keep the chapter bar or the caption (off by default)
// bin/vh frames <project> --covers draws them into out/covers/<id>.png (--dpr 2 for 3840 x 2160)
const COVERS = [
  { id: "A", at: "@a2:第二张+0.6", cam: { z: 1.12, x: 0, y: -60 }, title: { text: ["改一个字，镜头跟着走"], size: 150, x: 960, y: 1010, align: "center" } },
];

const SHOTS = [
  { id: "S01", at: 0,
    see: "片名“镜头挂在字上”；一条时间轴上，旁白说到“镜头”“时间”“字”，这三个词依次弹出来；说到“字”，一枚图钉落在它上面",
    o: { from: "@a1", to: "@a1>", words: [["镜头", "@a1:镜头"], ["时间", "@a1:时间"], ["字", "@a1:字"]] },
    draw(t, s) {
      const o = s.o, x0 = 160, x1 = 1760, y = 780, at = (time) => lerp(x0, x1, seg(time, o.from, o.to));
      rect(0, 0, W, H, { fill: PAL.night }); vignette(0.45);
      label(t, 0, "镜头挂在字上", 160, 380, { size: 104, weight: 900, family: "serif", fade: 0 });   // there from frame 0
      label(t, 0.8, "每个镜头的起点，是旁白里的一个字", 166, 470, { size: 44, color: PAL.soft });
      // the line a1 as a time axis: half-second ticks (small on purpose: texture), a playhead, the words where they are spoken
      line(x0, y, x1, y, { color: PAL.soft, w: 3, alpha: 0.6 });
      for (let k = 0; o.from + k * 0.5 <= o.to; k++) {
        const x = at(o.from + k * 0.5);
        line(x, y + 8, x, y + 22, { color: PAL.soft, w: 2, alpha: 0.6 });
        if (k % 2 === 0) txt(`${k / 2} s`, x, y + 56, { size: 24, color: PAL.soft, align: "center", alpha: 0.7, texture: true });
      }
      o.words.forEach(([word, when], i) => chip(t, when, word, at(when), y - 60, i === o.words.length - 1));
      const [, pinAt] = o.words[o.words.length - 1];
      drop(t, pinAt + 0.15, at(pinAt), y - 170, () => { line(at(pinAt), y - 170, at(pinAt), y - 100, { color: PAL.amber, w: 5 }); circle(at(pinAt), y - 180, 18, { fill: PAL.amber }); }, { kind: "pin", fall: 40 });
      line(at(t), y - 120, at(t), y + 24, { color: PAL.amber, w: 4 });
    } },

  { id: "S02", at: "@a2", tin: "settle",
    see: "两张卡片：说到“第一张”，第一张落下；说到“第二张”，第二张落下",
    o: { one: "@a2:第一张", two: "@a2:第二张" },
    draw(t, s) {
      rect(0, 0, W, H, { fill: PAL.night }); vignette(0.45);
      label(t, s.t0, "说到哪张，哪张落下", 160, 270, { size: 64, weight: 900, family: "serif", fade: 0 });   // up at the cut: the settle carries it in
      card(t, s.o.one, 660, 580, "1", "第一张");
      card(t, s.o.two, 1260, 580, "2", "第二张");
    } },

  { id: "S03", at: "@b1", tin: "turn", light: true, cam: [1, 1.03],
    see: "翻过一页，浅色的纸上一只灯泡和“新的一章”；说到“进度条”出一行说明，说到“亮起来”，灯泡亮了",
    o: { bar: "@b1:进度条", lit: "@b1:亮起来" },
    draw(t, s) {
      const lit = show(t, s.o.lit, 0.5);
      rect(0, 0, W, H, { fill: PAL.paper });
      cue("light", s.o.lit, { x: 470 });
      if (lit > 0) {
        const g = X.createRadialGradient(470, 450, 40, 470, 450, 380);
        g.addColorStop(0, `rgba(232,163,61,${0.75 * lit})`); g.addColorStop(1, "rgba(232,163,61,0)");
        X.fillStyle = g; X.fillRect(0, 0, W, H);
      }
      image("bulb", 290, 230, 360, 480, { fit: "contain" });
      label(t, s.t0 + 0.9, "新的一章", 800, 470, { size: 104, weight: 900, family: "serif", color: PAL.ink });
      label(t, s.o.bar, "顶上的进度条换到第二格", 806, 570, { size: 48, color: PAL.ink });
    } },

  { id: "S04", at: "@b2", tin: "blot",
    see: "一条旁白的波形，下面是四个镜头格；说到“重新配音”，波形变长，镜头格跟着挪过去；说到“跟着走”，盖一个章“跟上了”",
    o: { redo: "@b2:重新配音", follow: "@b2:跟着走" },
    draw(t, s) {
      const o = s.o, x0 = 160, len = lerp(1100, 1560, eInOut(seg(t, o.redo, o.redo + 0.9))), lenB = lerp(1100, 1560, eInOut(seg(t, o.redo + 0.3, o.redo + 1.2)));
      rect(0, 0, W, H, { fill: PAL.night }); vignette(0.45);
      label(t, s.t0 + 1.1, "改了旁白，镜头跟着走", 160, 300, { size: 84, weight: 900, family: "serif" });
      cue("stretch", o.redo, { x: x0 + 550 });
      for (let i = 0; i < 90; i++) {   // the narration: bars of a waveform, seeded, spread over its length
        const x = x0 + len * (i + 0.5) / 90, h = 16 + 120 * noise1(i * 0.35) * (0.35 + 0.65 * hash(i));
        rect(x - 4, 520 - h / 2, 8, h, { fill: PAL.teal, r: 4, alpha: 0.85 });
      }
      let x = x0;
      for (const [i, part] of [0.26, 0.26, 0.19, 0.29].entries()) {   // the shots under it, a beat behind
        rect(x + 5, 650, lenB * part - 10, 120, { stroke: PAL.soft, w: 3, r: 10 });
        txt(`S0${i + 1}`, x + 28, 728, { size: 44, family: "mono", weight: 400, color: PAL.soft });
        x += lenB * part;
      }
      stamp(t, o.follow, 1580, 300, "跟上了");
    } },
];
