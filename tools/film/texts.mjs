// texts: a page's window.film.texts (its reads and captions, engines/CONTRACT.md) written as readcheck's texts.json,
// for a page whose texts exist only once it runs (the canvas-film engine). bin/vh readcheck <project> runs it first
// when the project's page is film.html, then checks the file.
//
// usage: node tools/film/texts.mjs <project | page.html> --browser <chrome> [--out <project>/out/texts.json]
//
// Exit: 0 written · 1 the page gives no texts · 2 could not open it (no page, no window.film, not ready).
import fs from "node:fs";
import path from "node:path";
import { openFilm } from "./host.mjs";

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP.trimEnd() + "\n"); process.exit(argv.length ? 0 : 2); }
const die = (msg, code = 2) => { console.error("texts: " + msg); process.exit(code); };
let target = null, out = null, browser = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], next = () => { const v = argv[++i]; if (v === undefined) die(`${a} needs a value`); return v; };
  if (a === "--out") out = next();
  else if (a === "--browser") browser = next();
  else if (a.startsWith("-")) die(`unknown option ${a} (-h for the options)`);
  else if (target) die(`one project or page, got ${target} and ${a}`);
  else target = a;
}
if (!target) die("which project or page? (-h for the usage)");
if (!browser) die("no browser: pass --browser <chrome>, or run it as bin/vh readcheck");

let film;
try { film = await openFilm(target, { browser, runtime: "auto" }); } catch (e) { die(e.message); }
const texts = await film.list("texts").catch((e) => die(e.message));
const late = film.loadProblems;
await film.close();
if (!texts) die(`${film.page} gives no window.film.texts`, 1);
const file = path.resolve(out || path.join(film.root, "out", "texts.json"));
fs.mkdirSync(path.dirname(file), { recursive: true });
fs.writeFileSync(file, JSON.stringify(texts, null, 1) + "\n");
const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
console.log(`texts: ${texts.length} from ${rel(film.page)} (window.film.texts) → ${rel(file)}`);
for (const p of late) console.log(`  while loading: ${p}`);
