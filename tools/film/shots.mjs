// Internal bridge for storyboard/rhythm: read resolved shots after ready as JSON on stdout.
// --capture reads {out, frames: [{name, t}]} from stdin and draws those frames through the same host.
import fs from "node:fs";
import path from "node:path";
import { openFilm } from "./host.mjs";

let film;
const timer = setTimeout(async () => {
  console.error("shots: stopped after 120 s waiting for the page");
  if (film) await film.close();
  process.exit(2);
}, 120000);
timer.unref();
try {
  const [target, flag, browser, mode] = process.argv.slice(2);
  if (!target || flag !== "--browser" || !browser || (mode && mode !== "--capture"))
    throw new Error("use shots.mjs <page> --browser <chrome> [--capture]");
  film = await openFilm(target, { browser, runtime: "auto" });
  if (film.loadProblems.length) throw new Error(film.loadProblems.join(" | "));
  const shots = await film.field("shots");
  if (shots !== null && !Array.isArray(shots)) throw new Error("window.film.shots must be an array");
  const result = { shots, page: film.page, duration: film.duration, width: film.width, height: film.height };
  if (mode === "--capture") {
    const request = JSON.parse(fs.readFileSync(0, "utf8"));
    if (!Array.isArray(request.frames) || typeof request.out !== "string") throw new Error("invalid frame request");
    for (const { name, t } of request.frames) {
      if (typeof name !== "string" || path.basename(name) !== name || !name.endsWith(".png")) throw new Error("invalid frame filename");
      if (!Number.isFinite(t) || t < 0 || !(film.duration > 0) || t > film.duration) throw new Error(`${t} s is outside the film (0 up to ${film.duration} s)`);
    }
    fs.mkdirSync(request.out, { recursive: true });
    for (const { name, t } of request.frames) {
      const { png, touched } = await film.frame(Math.min(t, film.duration - 1e-6)); // --at 1: just inside the final frame
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
