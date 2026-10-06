// A headless Chrome driven over the DevTools protocol through a pipe (--remote-debugging-pipe), and a static file server
// for the composition. No npm dependencies: Node's child_process and http are enough for what textcheck needs, so it runs
// in any project and in CI without puppeteer.
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";

// launch(exe, flags) → { send(method, params, sessionId), once(event, sessionId), close(), version }
export async function launch(exe, flags = []) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "vh-textcheck-"));
  const args = ["--headless", "--remote-debugging-pipe", "--no-first-run", "--no-default-browser-check", `--user-data-dir=${profile}`,
    "--hide-scrollbars", "--mute-audio", "--force-color-profile=srgb", ...flags, "about:blank"];
  const proc = spawn(exe, args, { stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"] });
  let stderr = "";
  proc.stderr.on("data", (d) => { stderr = (stderr + d).slice(-4000); });
  const exited = new Promise((res) => { proc.on("exit", res); proc.on("error", (e) => { stderr += String(e); res(); }); });
  const out = proc.stdio[3], inp = proc.stdio[4];
  const pending = new Map(), waiters = [], listeners = [];
  let buf = Buffer.alloc(0), id = 0;
  inp.on("data", (d) => {
    buf = Buffer.concat([buf, d]);
    for (let i; (i = buf.indexOf(0)) >= 0;) {
      const m = JSON.parse(buf.subarray(0, i).toString("utf8"));
      buf = buf.subarray(i + 1);
      if (m.id !== undefined && pending.has(m.id)) {
        const p = pending.get(m.id); pending.delete(m.id);
        if (m.error) p.reject(new Error(`${p.method}: ${m.error.message}${m.error.data ? " (" + m.error.data + ")" : ""}`)); else p.resolve(m.result);
      } else if (m.method) {
        for (const w of waiters.slice()) if (w.method === m.method && (!w.session || w.session === m.sessionId)) { waiters.splice(waiters.indexOf(w), 1); w.resolve(m.params); }
        for (const l of listeners) if (l.method === m.method) l.fn(m.params);
      }
    }
  });
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const i = ++id; pending.set(i, { resolve, reject, method });
    out.write(JSON.stringify({ id: i, method, params, ...(sessionId ? { sessionId } : {}) }) + "\0");
  });
  const once = (method, session) => new Promise((resolve) => waiters.push({ method, session, resolve }));
  const on = (method, fn) => listeners.push({ method, fn });
  const close = async () => {
    try { await Promise.race([send("Browser.close"), new Promise((r) => setTimeout(r, 3000))]); } catch { /* already gone */ }
    proc.kill(); await exited;
    fs.rmSync(profile, { recursive: true, force: true });
  };
  let version;
  try {
    version = await Promise.race([send("Browser.getVersion"), exited.then(() => { throw new Error("the browser exited at start: " + stderr.trim().split("\n").slice(-3).join(" | ")); }),
      new Promise((_, rej) => setTimeout(() => rej(new Error("the browser did not answer within 30 s")), 30000))]);
  } catch (e) { proc.kill(); fs.rmSync(profile, { recursive: true, force: true }); throw e; }
  return { send, once, on, close, version: version.product };
}

const TYPES = { ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif",
  ".svg": "image/svg+xml", ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf", ".wav": "audio/wav", ".mp3": "audio/mpeg",
  ".m4a": "audio/mp4", ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".wasm": "application/wasm", ".glsl": "text/plain", ".txt": "text/plain" };

// serve(dir) → { url, close() }: the folder on 127.0.0.1 (so module scripts, fetch and fonts work as they do in
// HyperFrames' own preview, which file:// would block); no path out of it
export async function serve(dir) {
  const root = fs.realpathSync(dir);
  const server = http.createServer((req, res) => {
    let f;
    try { f = path.join(root, decodeURIComponent(new URL(req.url, "http://x").pathname)); } catch { res.writeHead(400); return res.end(); }
    // inside the folder by its path (a symlinked node_modules or assets folder is followed, as HyperFrames' preview does)
    let ok = false;
    try { ok = f.startsWith(root + path.sep) && fs.statSync(f).isFile(); } catch { /* missing */ }
    if (!ok) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "content-type": TYPES[path.extname(f).toLowerCase()] || "application/octet-stream", "cache-control": "no-store" });
    fs.createReadStream(f).pipe(res);
  });
  await new Promise((res) => server.listen(0, "127.0.0.1", res));
  return { url: `http://127.0.0.1:${server.address().port}/`, close: () => new Promise((res) => server.close(res)) };
}
