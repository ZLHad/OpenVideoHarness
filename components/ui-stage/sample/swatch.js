// ui-stage's sample: on the left a terminal and a keyboard (the DOM painter): "claude" typed by hand, then a request in
// pinyin through the input method's composition and candidate box, Enter, two lines printed. On the right a player of
// an interface's captures (the canvas painter): a row clicked, a note typed letter by letter, added; the camera pushes
// in on the column, a spotlight and a ring mark it, the step chip counts. The captures are grey boxes drawn here in
// setup, one picture a step, standing in for a real app's screenshots. Render: bin/vh components sample ui-stage.
import { state, canvas, build, dom } from "../../components/ui-stage/component.js";

const NOTE = "开头这一镜，再亮一点";
const N = Array.from(NOTE).length;
let L, R, els, pics, font, mono;

export function setup(ctx, tokens, lib) {
  font = lib.fontStack(tokens, "zh"); mono = lib.fontStack(tokens, "mono");
  const accent = lib.color(tokens, "accent");
  L = {
    window: { kind: "terminal", x: 70, y: 80, w: 1000, h: 420, title: "~/films/demo" },
    lines: [
      { at: 0.25, prompt: "$ ", text: "claude", how: "type", enter: true },
      { at: 1.25, prompt: "> ", parts: [["把开头", "bakaitou"], ["改亮", "gailiang"], ["一点", "yidian"]], cps: 15, enter: true },
      { at: 3.25, text: "⏺ Read(STORYBOARD.md)", how: "print", color: "#ad97f2" },
      { at: 3.75, text: "✓ S01 改好了", how: "print", color: "#8fbf95" },
    ],
    keyboard: { x: 70, y: 560, w: 1000 }, size: 44, mono, font, colors: { accent },
  };
  // the captures: a rail, a player, a timeline, a column of notes; step k changes one thing
  const states = [[0, "c0"], [2.15, "c1"]];
  for (let i = 1; i <= N; i++) states.push([2.55 + i * 0.085, `t${i}`]);
  states.push([3.6, "add"]);
  R = {
    capture: { states, size: [1440, 900], at: [1495, 470], view: [1130, 50, 740, 830], camera: [[0, 720, 450, 0.51], [1.9, 720, 450, 0.51], [2.5, 1235, 300, 1.6]] },
    cursor: { keys: [[0, 1480, 980], [1.6, 1480, 980], [2.1, 1180, 140], [2.6, 1215, 300], [3.45, 1350, 216], [5, 1360, 230]], clicks: [2.15, 3.55], space: "capture" },
    marks: [{ t0: 2.45, t1: 5.2, box: [1046, 86, 378, 260], kind: "spot" }, { t0: 3.7, t1: 5.2, box: [1060, 270, 350, 76], kind: "ring" }],
    steps: [[0.2, "1", "在终端里说"], [2.0, "2", "在界面上点"]], chip: [1120, 908], font, colors: { accent },
  };
  pics = {};
  const draw = (name, k, typed, added) => {
    const c = document.createElement("canvas"); c.width = 2880; c.height = 1800; const x = c.getContext("2d"); x.scale(2, 2);
    x.fillStyle = "#f3f1ec"; x.fillRect(0, 0, 1440, 900); x.fillStyle = "#1d1c1a"; x.fillRect(0, 0, 64, 900);
    for (let i = 0; i < 6; i++) { x.fillStyle = i === 4 ? "#5ec9dc" : "#4a4843"; x.beginPath(); x.roundRect(18, 90 + i * 64, 28, 28, 7); x.fill(); }
    x.fillStyle = "#111"; x.fillRect(96, 60, 900, 506); x.fillStyle = "#2b2a27"; x.fillRect(96, 600, 900, 260);
    for (let i = 0; i < 3; i++) for (let j = 0; j < 7; j++) { x.fillStyle = ["#5ec9dc", "#ad97f2", "#e2a63f"][i]; x.globalAlpha = 0.7; x.fillRect(110 + j * 126, 630 + i * 70, 110, 44); }
    x.globalAlpha = 1; x.fillStyle = "#e85a50"; x.fillRect(420, 610, 4, 240);
    x.fillStyle = "#ffffff"; x.fillRect(1030, 0, 410, 900); x.font = `600 26px ${font}`; x.fillStyle = "#1d1c1a"; x.fillText("意见", 1060, 64);
    const rows = added ? [NOTE, "字幕再大一号", "结尾别停太久"] : ["字幕再大一号", "结尾别停太久"];
    rows.forEach((s, i) => { const y = 270 + i * 92; x.fillStyle = added && i === 0 ? "#e8f6f9" : "#f3f1ec"; x.beginPath(); x.roundRect(1060, y, 350, 76, 12); x.fill(); x.fillStyle = "#3b3833"; x.font = `500 22px ${font}`; x.fillText(s, 1080, y + 46); });
    x.strokeStyle = k ? "#5ec9dc" : "#d6d2ca"; x.lineWidth = k ? 3 : 2; x.beginPath(); x.roundRect(1060, 100, 350, 76, 12); x.stroke();
    x.fillStyle = "#3b3833"; x.font = `500 24px ${font}`; x.fillText(added ? "" : typed || (k ? "" : "写一句意见…"), 1080, 146);
    if (k && !added) { x.fillStyle = "#1d1c1a"; x.fillRect(1082 + x.measureText(typed || "").width, 124, 2, 30); }
    x.fillStyle = "#5ec9dc"; x.beginPath(); x.roundRect(1290, 192, 120, 48, 24); x.fill(); x.fillStyle = "#fff"; x.font = `600 22px ${font}`; x.fillText("加一条", 1317, 224);
    pics[name] = c;
  };
  draw("c0", 0); draw("c1", 1, "");
  for (let i = 1; i <= N; i++) draw(`t${i}`, 1, Array.from(NOTE).slice(0, i).join(""));
  draw("add", 1, "", true);
  els = build(document.getElementById("root"), L);
}

export function renderAt(t, ctx, tokens, lib) {
  ctx.fillStyle = lib.color(tokens, "bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  dom(els, state(L, t));
  canvas(ctx, state(R, t), R, pics);
}
