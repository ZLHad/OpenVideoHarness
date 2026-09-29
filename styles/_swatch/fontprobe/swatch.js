// Font probe (tool, not a style): loads EVERY @font-face in fonts.css inside the render Chrome and shows each
// family in its own face. Red = a face failed to open or the family falls back. Run on a new machine or after
// regenerating fonts.css:   styles/_swatch/render.sh fontprobe --draft   → out/fontprobe/sheet.png + render.log
let R = null;

export async function setup(ctx, tokens, lib) {
  const fams = new Map(), jobs = [];
  for (const face of document.fonts) {
    const fam = face.family.replace(/^["']|["']$/g, "");
    if (!fams.has(fam)) fams.set(fam, { ok: 0, bad: [] });
    const tag = `${face.weight}${face.style === "italic" ? "i" : ""}${face.stretch !== "normal" && face.stretch !== "100%" ? "@" + face.stretch : ""}`;
    jobs.push(face.load().then(() => fams.get(fam).ok++, () => fams.get(fam).bad.push(tag)));
  }
  await Promise.all(jobs);
  await document.fonts.ready;
  R = [...fams.entries()].map(([f, v]) => ({ f, ok: v.ok, bad: v.bad, avail: lib.fontAvailable(f) }));
  const bad = R.filter((r) => r.bad.length || !r.avail);
  console.warn(`[swatch] fontprobe: ${R.length - bad.length}/${R.length} families OK` +
    (bad.length ? `; problems: ${bad.map((r) => `${r.f}${r.avail ? "" : " (falls back)"}${r.bad.length ? " faces " + r.bad.join(",") : ""}`).join(" | ")}` : ""));
}

export function renderAt(t, ctx, tokens, lib) {
  ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, lib.W, lib.H);
  const rows = 30, colW = 480;
  R.forEach((r, i) => {
    const x = 20 + Math.floor(i / rows) * colW, y = 34 + (i % rows) * 35;
    ctx.fillStyle = r.bad.length || !r.avail ? lib.color(tokens, "bad") : lib.color(tokens, "ink");
    ctx.font = `400 24px "${r.f}", monospace`;
    ctx.fillText(`${r.f} 永帧 Ag`, x, y);
  });
}
