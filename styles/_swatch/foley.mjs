// Write styles/<slug>/events.json from the FOLEY export of styles/<slug>/swatch.js, so picture and foley share one
// source of timing:  export const FOLEY = [{ t: T_STAMP, sfx: "click", gain_db: -6, pan: -0.4 }, …]  (dist, role optional)
// usage: node styles/_swatch/foley.mjs <slug> [<slug> …]      (render.sh then mixes events.json under the score)
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const STYLES = resolve(dirname(fileURLToPath(import.meta.url)), "..");
for (const slug of process.argv.slice(2)) {
  const m = await import(pathToFileURL(`${STYLES}/${slug}/swatch.js`).href);
  if (!Array.isArray(m.FOLEY)) { console.error(`${slug}: swatch.js has no FOLEY export`); process.exitCode = 1; continue; }
  const ev = m.FOLEY.map((e) => ({ t: Math.round(e.t * 1000) / 1000, sfx: e.sfx, gain_db: e.gain_db ?? 0, pan: e.pan ?? 0,
                                   ...(e.dist ? { dist: e.dist } : {}), ...(e.role ? { role: e.role } : {}) })).sort((a, b) => a.t - b.t);
  const perSec = {}; ev.forEach((e) => { const k = Math.floor(e.t); perSec[k] = (perSec[k] || 0) + 1; });
  const busy = Object.entries(perSec).filter(([, n]) => n > 6);
  writeFileSync(`${STYLES}/${slug}/events.json`, "[\n" + ev.map((e) => "  " + JSON.stringify(e)).join(",\n") + "\n]\n");
  console.log(`${slug}: ${ev.length} events, per second ${JSON.stringify(perSec)}${busy.length ? "  ⚠ more than 6/s: keep foley sparse" : ""}`);
}
