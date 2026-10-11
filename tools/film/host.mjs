// The film host (engines/CONTRACT.md): opens a page in headless Chrome, served from its folder on 127.0.0.1, sets
// window.filmHost and the clock before the page's scripts run, waits for window.film (or the older window.__vh) and its
// `ready`, then draws any t and captures the viewport as a lossless PNG. A HyperFrames composition that writes neither
// gets HyperFrames' own runtime and tools/film/hf-adapter.js before </head>, where HyperFrames' preview puts its runtime.
// No npm packages: the browser is driven over the DevTools protocol (tools/textcheck/browser.mjs).
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { launch } from "../textcheck/browser.mjs";

const HERE = path.dirname(new URL(import.meta.url).pathname);
const HARNESS = path.resolve(HERE, "..", "..");
const RUNTIME = path.join("node_modules", "hyperframes", "dist", "hyperframe.runtime.iife.js");
export const PAGES = ["film.html", "index.html", "studio.html"];   // what a project folder offers, in this order
export class HostError extends Error {}                            // could not draw at all: the caller exits 2

// the page a target names: the file itself, or the first of PAGES in a folder
export function findPage(target) {
  const p = path.resolve(target);
  if (!fs.existsSync(p)) throw new HostError(`no such file or folder: ${target}`);
  if (fs.statSync(p).isFile()) return p;
  const page = PAGES.map((n) => path.join(p, n)).find((f) => fs.existsSync(f));
  if (!page) throw new HostError(`${target} has no page to draw (${PAGES.join(", ")})`);
  return page;
}

// what the HTML says before it runs: its size, whether it is a HyperFrames composition, whether it writes its own contract
export function readPage(page) {
  const html = fs.readFileSync(page, "utf8");
  const rootTag = (html.match(/<[^>]*\bdata-composition-id\b[^>]*>/) || [""])[0];
  const attr = (n) => { const m = rootTag.match(new RegExp(`\\b${n}="([\\d.]+)"`)); return m ? +m[1] : 0; };
  const meta = (html.match(/<meta[^>]*name=["']viewport["'][^>]*content=["']([^"']*)["']/i) || [])[1] || "";
  const mv = (n) => { const m = meta.match(new RegExp(`\\b${n}\\s*=\\s*(\\d+)`)); return m ? +m[1] : 0; };
  return {
    html, hyperframes: !!rootTag,
    width: attr("data-width") || mv("width") || 1920, height: attr("data-height") || mv("height") || 1080,
    ownContract: /window\.(film|__vh)\s*=/.test(html),
  };
}

// HyperFrames' runtime for a composition: the project's own (its version), else the one bin/vh setup installed
export function findRuntime(root) {
  for (let d = root; ; d = path.dirname(d)) {
    const f = path.join(d, RUNTIME);
    if (fs.existsSync(f)) return f;
    if (path.dirname(d) === d) break;
  }
  const f = path.join(HARNESS, "styles", "_swatch", RUNTIME);
  return fs.existsSync(f) ? f : null;
}

const TYPES = { ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif",
  ".svg": "image/svg+xml", ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf", ".wav": "audio/wav", ".mp3": "audio/mpeg",
  ".m4a": "audio/mp4", ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".wasm": "application/wasm", ".glsl": "text/plain", ".txt": "text/plain",
  ".glb": "model/gltf-binary", ".gltf": "model/gltf+json" };

// the page's folder on 127.0.0.1; the page itself with `inject` before </head>; /__vh/<name> from `extra`; no path out of the folder
function serve(root, pageRel, inject, extra) {
  const server = http.createServer((req, res) => {
    let rel;
    try { rel = decodeURIComponent(new URL(req.url, "http://x").pathname); } catch { res.writeHead(400); return res.end(); }
    if (rel.startsWith("/__vh/") && Object.hasOwn(extra, rel.slice(6))) {
      res.writeHead(200, { "content-type": "text/javascript", "cache-control": "no-store" });
      return fs.createReadStream(extra[rel.slice(6)]).pipe(res);
    }
    if (rel === "/" + pageRel && inject) {
      const html = fs.readFileSync(path.join(root, pageRel), "utf8");
      const i = html.search(/<\/head>/i);
      res.writeHead(200, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" });
      return res.end(i >= 0 ? html.slice(0, i) + inject + html.slice(i) : inject + html);
    }
    const f = path.join(root, rel);
    let ok = false;
    try { ok = f.startsWith(root + path.sep) && fs.statSync(f).isFile(); } catch { /* missing */ }
    if (!ok) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "content-type": TYPES[path.extname(f).toLowerCase()] || "application/octet-stream", "cache-control": "no-store" });
    fs.createReadStream(f).pipe(res);
  });
  return new Promise((ok) => server.listen(0, "127.0.0.1", () => ok({ url: `http://127.0.0.1:${server.address().port}/`, close: () => new Promise((r) => server.close(r)) })));
}

// openFilm(target, { browser, dpr, width, height, realClock, softGl, runtime }) → a film to draw: { page, kind, width,
// height, duration, frame(t) → { png, touched }, problems(), close() }. runtime: "auto" (HyperFrames' runtime for a
// composition that writes no contract of its own), "on" or "off".
export async function openFilm(target, o = {}) {
  const page = findPage(target), root = fs.realpathSync(path.dirname(page)), pageRel = path.basename(page);
  const info = readPage(page);
  let width = o.width || info.width, height = o.height || info.height;
  const useRuntime = info.hyperframes && (o.runtime === "on" || (o.runtime !== "off" && !info.ownContract));
  const extra = {}, scripts = [];
  if (useRuntime) {
    const rt = findRuntime(root);
    if (!rt) throw new HostError(`${pageRel} is a HyperFrames composition without window.film, and no HyperFrames runtime was found: run npm install in the project (or bin/vh setup)`);
    extra["hf-runtime.js"] = rt; extra["hf-adapter.js"] = path.join(HERE, "hf-adapter.js");
    scripts.push('<script data-hyperframes-preview-runtime="1" src="/__vh/hf-runtime.js"></script>', '<script src="/__vh/hf-adapter.js"></script>');
  }
  const server = await serve(root, pageRel, scripts.join("\n"), extra);
  const flags = o.softGl ? ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
    : process.platform === "darwin" ? ["--use-angle=metal", "--ignore-gpu-blocklist"] : ["--ignore-gpu-blocklist"];
  if (process.platform === "linux") flags.push("--no-sandbox", "--disable-dev-shm-usage");
  flags.push("--font-render-hinting=none");   // as HyperFrames renders: glyph edges otherwise differ from its frames
  let browser;
  try { browser = await launch(o.browser, flags); } catch (e) { await server.close(); throw new HostError(`could not start ${o.browser}: ${e.message}`); }
  const closeAll = async () => { try { await browser.close(); } catch { /* gone */ } await server.close(); };
  try {
    const { targetId } = await browser.send("Target.createTarget", { url: "about:blank" });
    const { sessionId: s } = await browser.send("Target.attachToTarget", { targetId, flatten: true });
    const problems = [], urls = new Map();
    browser.on("Runtime.exceptionThrown", (p) => problems.push("error: " + ((p.exceptionDetails.exception && p.exceptionDetails.exception.description) || p.exceptionDetails.text)));
    browser.on("Runtime.consoleAPICalled", (p) => { if (p.type === "error") problems.push("console.error: " + p.args.map((a) => a.value ?? a.description ?? "").join(" ")); });
    browser.on("Network.requestWillBeSent", (p) => urls.set(p.requestId, p.request.url));
    browser.on("Network.loadingFailed", (p) => { if (!p.canceled) problems.push(`failed to load ${(urls.get(p.requestId) || "?").replace(server.url, "")}: ${p.errorText}`); });
    browser.on("Network.responseReceived", (p) => { if (p.response.status >= 400 && !/\/favicon\.ico$/.test(p.response.url)) problems.push(`failed to load ${p.response.url.replace(server.url, "")}: HTTP ${p.response.status}`); });
    for (const d of ["Page", "Runtime", "Network"]) await browser.send(`${d}.enable`, {}, s);
    const metrics = (w, h) => browser.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: o.dpr || 1, mobile: false }, s);
    await metrics(width, height);
    await browser.send("Emulation.setTimezoneOverride", { timezoneId: "UTC" }, s);   // local time reads the same on every machine
    const prelude = o.realClock ? 'window.filmHost = { version: "0.1", name: "ovh" };' : fs.readFileSync(path.join(HERE, "clock.js"), "utf8");
    await browser.send("Page.addScriptToEvaluateOnNewDocument", { source: prelude }, s);
    const ev = async (expression, what) => {
      const r = await browser.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }, s);
      if (r.exceptionDetails) throw new Error(`${what}: ${(r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text}`);
      return r.result.value;
    };
    const loaded = browser.once("Page.loadEventFired", s);
    loaded.catch(() => { /* a browser that dies first fails it; the race below reports that */ });
    await browser.send("Page.navigate", { url: server.url + encodeURIComponent(pageRel) }, s);
    let timer;
    await Promise.race([loaded, new Promise((_, no) => { timer = setTimeout(() => no(new HostError("the page did not load within 60 s")), 60000); })]).finally(() => clearTimeout(timer));
    // the contract: window.film, else window.__vh; a page has 10 s after load to set it
    const kind = await ev(`new Promise((ok) => { const t0 = Date.now(); const look = () => {
        if (window.film && typeof window.film.frame === "function") return ok(window.film.__adapter || "film");
        if (window.__vh && typeof window.__vh.draw === "function") return ok("__vh");
        if (Date.now() - t0 > 10000) return ok(""); setTimeout(look, 50); }; look(); })`, "looking for window.film");
    if (!kind) {
      throw new HostError(`${pageRel} sets no window.film (nor window.__vh) within 10 s of loading: see engines/CONTRACT.md` +
        (problems.length ? `\npage errors while loading:\n  ${[...new Set(problems)].slice(0, 5).join("\n  ")}` : ""));
    }
    const ready = await ev(`(async () => {
      const wait = (p) => Promise.race([p, new Promise((_, no) => setTimeout(() => no(new Error("not ready after 120 s")), 120000))]);
      try {
        const src = window.film && window.film.frame ? window.film : window.__vh;
        let r = src.ready;
        if (typeof r === "function") r = r.call(src);   // a method: film.ready(), as OpenFilm's hosts call it
        await wait(Promise.resolve(r)); await wait(document.fonts.ready);
      } catch (e) { return String((e && e.message) || e); }
      return "";
    })()`, "waiting for ready");
    if (ready) throw new HostError(`${pageRel}: ${ready} (window.film.ready or the fonts)`);
    const got = await ev(`(() => { const f = window.film && window.film.frame ? window.film : null, v = window.__vh || {};
      const root = document.querySelector("[data-composition-id]");
      return { duration: +((f ? f.duration : v.duration) || (root && root.dataset.duration) || 0), width: f && +f.width || 0, height: f && +f.height || 0 }; })()`, "reading window.film");
    if (got.width > 0 && got.height > 0 && (got.width !== width || got.height !== height)) { width = got.width; height = got.height; await metrics(width, height); }
    const loadProblems = problems.splice(0);
    return {
      page, root, kind, width, height, duration: got.duration, version: browser.version, loadProblems,
      // draw t, let the compositor paint it, capture it (a lossless PNG, or { format: "jpeg", quality } for a render);
      // touched: the clocks the frame read (tools/film/clock.js)
      async frame(t, capture = { format: "png" }) {
        const touched = await ev(`(async (t) => {
          const H = window.filmHost, f = window.film && window.film.frame ? window.film : null;
          if (H && H.time) H.time(t);
          try { if (f) await f.frame(t); else await window.__vh.draw(t); } finally { if (H && H.settle) H.settle(t); }
          await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
          return H && H.touched ? H.touched() : [];
        })(${JSON.stringify(t)})`, `drawing t=${t}`);
        const shot = await browser.send("Page.captureScreenshot", { ...capture, fromSurface: true, captureBeyondViewport: false }, s);
        return { png: Buffer.from(shot.data, "base64"), touched };
      },
      problems: () => problems.splice(0),
      // what arrives after the last frame (an error from a timer a frame set): two paints and 100 ms, then collect
      async lateProblems() {
        try { await ev("new Promise((ok) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(ok, 100))))", "after the last frame"); } catch { /* gone */ }
        return problems.splice(0);
      },
      close: closeAll,
    };
  } catch (e) { await closeAll(); throw e instanceof HostError ? e : new HostError(e.message); }
}
