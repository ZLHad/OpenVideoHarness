// Write styles/<slug>/events.json from the FOLEY export of styles/<slug>/swatch.js, so picture and foley share one
// source of timing:  export const FOLEY = [{ t: T_STAMP, sfx: "click", gain_db: -6, pan: -0.4 }, …]  (dist, role optional;
// a built-in's shape and variant pass through too: dur, pitch, center, dir, bright, tone, pan_from, pan_to, variant)
// usage: node styles/_swatch/foley.mjs <slug> [<slug> …]      (render.sh then mixes events.json under the score)
// A Blender scene (swatch.py) is checked by blender_prep.py scan, then run by plain python3 for its FOLEY (no bpy there).
import { execFileSync } from "node:child_process";
import { existsSync, realpathSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const STYLES = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SHAPE = ["dur", "pitch", "center", "dir", "bright", "tone", "pan_from", "pan_to", "variant"];   // tools/audio/sfx.py
const r3 = (x) => (typeof x === "number" ? Math.round(x * 1000) / 1000 : x);
// A Blender scene's FOLEY: the scan first (blender_prep.py), then plain python3 with no inherited environment and, on
// macOS, a sandbox with no network, no writes and no reads in the home folder outside the repo and the interpreter's
// own install; the last line it prints is the JSON
function pyFoley(py) {
  try { execFileSync("python3", [`${STYLES}/_swatch/blender_prep.py`, "scan", py], { encoding: "utf8" }); }
  catch (e) { throw new Error((e.stdout || "").trim() || e.message); }     // the scan's findings, not "Command failed"
  const env = { PATH: process.env.PATH, PYTHONDONTWRITEBYTECODE: "1" };
  let cmd = ["python3", [py, "--foley"]];
  if (process.platform === "darwin" && existsSync("/usr/bin/sandbox-exec")) {
    const [exe, prefix] = execFileSync("python3", ["-c", "import os, sys; print(os.path.realpath(sys.executable)); " +
      "print(os.path.realpath(sys.base_prefix))"], { encoding: "utf8", env }).trim().split("\n");   // pyenv, uv: may be under home
    const home = realpathSync(homedir());
    if ((home + "/").startsWith(prefix.replace(/\/$/, "") + "/")) throw new Error(`python3's install (${prefix}) holds the home folder`);
    const q = (p) => '"' + realpathSync(p).replace(/[\\"]/g, "\\$&") + '"';
    const profile = '(version 1)(allow default)(deny network*)(deny lsopen)(deny appleevent-send)(deny file-write*)' +
      '(allow file-write* (literal "/dev/null"))' + `(deny file-read* (subpath ${q(home)}))` +
      `(allow file-read* (subpath ${q(resolve(STYLES, ".."))}) (subpath ${q(prefix)}))`;
    cmd = ["/usr/bin/sandbox-exec", ["-p", profile, exe, py, "--foley"]];
  }
  const out = execFileSync(cmd[0], cmd[1], { encoding: "utf8", env }).trim().split("\n");
  return JSON.parse(out[out.length - 1]);
}
for (const slug of process.argv.slice(2)) {
  const js = `${STYLES}/${slug}/swatch.js`, py = `${STYLES}/${slug}/swatch.py`;
  let m;
  try {
    if (existsSync(js)) m = await import(pathToFileURL(js).href);
    else if (existsSync(py)) m = { FOLEY: pyFoley(py) };
    else throw new Error("no swatch.js or swatch.py");
  } catch (e) { console.error(`${slug}: ${e.message.trim()}`); process.exitCode = 1; continue; }
  if (!Array.isArray(m.FOLEY)) { console.error(`${slug}: the scene has no FOLEY list`); process.exitCode = 1; continue; }
  const ev = m.FOLEY.map((e) => ({ t: Math.round(e.t * 1000) / 1000, sfx: e.sfx, gain_db: e.gain_db ?? 0, pan: e.pan ?? 0,
                                   ...(e.dist ? { dist: e.dist } : {}), ...(e.role ? { role: e.role } : {}),
                                   ...Object.fromEntries(SHAPE.filter((k) => e[k] != null).map((k) => [k, r3(e[k])])) })).sort((a, b) => a.t - b.t);
  const perSec = {}; ev.forEach((e) => { const k = Math.floor(e.t); perSec[k] = (perSec[k] || 0) + 1; });
  const busy = Object.entries(perSec).filter(([, n]) => n > 6);
  writeFileSync(`${STYLES}/${slug}/events.json`, "[\n" + ev.map((e) => "  " + JSON.stringify(e)).join(",\n") + "\n]\n");
  console.log(`${slug}: ${ev.length} events, per second ${JSON.stringify(perSec)}${busy.length ? "  ⚠ more than 6/s: keep foley sparse" : ""}`);
}
