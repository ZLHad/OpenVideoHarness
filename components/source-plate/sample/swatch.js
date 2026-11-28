// source-plate's sample: two plates over a sheet of paper. The lower one is the DOM painter (its lines are DOM text, as
// in a HyperFrames composition), the upper one the canvas painter; each stays up as long as the normal pace needs to
// read it, from its own words. Render: bin/vh components sample source-plate.
import { layout, state, canvas, build, dom } from "../../components/source-plate/component.js";

let P1, P2, lay1, lay2, els;

export function setup(ctx, tokens, lib) {
  const font = lib.fontStack(tokens, "zh"), mono = lib.fontStack(tokens, "mono"), accent = lib.color(tokens, "accent");
  P1 = { kind: "person", title: "Ada Lovelace", detail: "数学家 · 1815–1852", t: 0.3, font, mono, colors: { accent } };
  P2 = { kind: "data", title: "世界人口展望 2024", detail: "联合国人口司", t: 0.6, anchor: "upper-right", font, mono, colors: { accent } };
  const m = (s, f) => { ctx.font = f; return ctx.measureText(s).width; };
  lay1 = layout(P1, m); lay2 = layout(P2, m);
  els = build(document.getElementById("root"), P1, lay1);
}

export function renderAt(t, ctx, tokens, lib) {
  lib.paper(ctx, { tone: lib.color(tokens, "bg"), seed: 7 });
  // something for the plates to sit over: a big quiet numeral
  lib.setFont(ctx, tokens, "display", 520, { weight: 700 }); ctx.fillStyle = lib.rgba(lib.color(tokens, "fg"), 0.06);
  ctx.textAlign = "center"; ctx.fillText("1815", 960, 760); ctx.textAlign = "left";
  dom(els, state(P1, t, lay1));
  canvas(ctx, state(P2, t, lay2), P2, lay2);
  lib.setFont(ctx, tokens, "mono", 26); ctx.fillStyle = lib.color(tokens, "extra.1");
  ctx.fillText("canvas painter ↗", 96, 300); ctx.fillText("DOM painter ↙", 96, 760);
}
