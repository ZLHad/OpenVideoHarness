// Internal bridge for storyboard/rhythm: read resolved shots after ready as JSON on stdout.
// --capture reads {out, frames: [{name, t}]} from stdin and draws those frames through the same host.
import fs from "node:fs";
import path from "node:path";
import { openTarget } from "./edit.mjs";   // a page, or an edit list's film (engines/EDIT.md: storyboard's tiles when there is no video)

let film, timer;
// a watchdog per step, not one budget for the whole run: 120 s for the page to be ready, then 60 s for each frame
const arm = (s, what) => {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    console.error(`shots: stopped after ${s} s ${what}`);
    if (film) await film.close();
    process.exit(2);
  }, s * 1000);
  timer.unref();
};
arm(120, "waiting for the page");
try {
  const [target, flag, browser, mode] = process.argv.slice(2);
  if (!target || flag !== "--browser" || !browser || (mode && mode !== "--capture"))
    throw new Error("use shots.mjs <page> --browser <chrome> [--capture]");
  film = await openTarget(target, { browser, runtime: "auto" });
  if (film.loadProblems.length) throw new Error(film.loadProblems.join(" | "));
  // Capture may be requested by a hand-written JSON table; do not read an unselected registry.
  const shots = mode === "--capture" ? null : await film.field("shots");
  if (shots !== null && !Array.isArray(shots)) throw new Error("window.film.shots must be an array");
  const result = { shots, page: film.page, duration: film.duration, width: film.width, height: film.height };
  if (mode === "--capture") {
    const request = JSON.parse(fs.readFileSync(0, "utf8"));
    if (!Array.isArray(request.frames) || typeof request.out !== "string") throw new Error("invalid frame request");
    for (const { name, t } of request.frames) {
      if (typeof name !== "string" || path.basename(name) !== name || !name.endsWith(".png")) throw new Error("invalid frame filename");
      if (!Number.isFinite(t) || t < 0) throw new Error(`${t} s is not a time in the film`);
    }
    if (!(film.duration > 0)) throw new Error("the page gives no duration");
    // a planned shot past the page's end is not an error at gate ②: storyboard leaves its tile grey, as for a short video
    result.late = request.frames.filter(({ t }) => t > film.duration + 1e-6).map(({ name }) => name);
    fs.mkdirSync(request.out, { recursive: true });
    for (const { name, t } of request.frames) {
      if (result.late.includes(name)) continue;
      arm(60, `drawing the frame at ${t} s`);
      // to the millisecond, as bin/vh frames --at, so a tile can be drawn again; --at 1: just inside the final frame
      const { png, touched } = await film.frame(Math.min(Math.round(t * 1000) / 1000, film.duration - 1e-6));
      if (touched.includes("Math.random")) console.error(`shots: warning: frame at ${t} s reads Math.random; use a seeded hash`);
      const problems = film.problems();
      if (problems.length) throw new Error(`at ${t} s: ${problems.join(" | ")}`);
      fs.writeFileSync(path.join(request.out, name), png);
    }
  }
  const late = await film.lateProblems();
  if (late.length) throw new Error(late.join(" | "));
  process.stdout.write(JSON.stringify(result) + "\n");
} catch (e) {
  console.error("shots: " + e.message);
  process.exitCode = 2;
} finally {
  clearTimeout(timer);
  if (film) await film.close();
}
