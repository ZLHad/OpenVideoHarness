// An edit list's chunk cache (bin/vh render; engines/EDIT.md, 块缓存): a finished chunk is kept in
// <project>/out/cache/chunks/<key>.mp4 under its key (tools/film/edit.mjs chunkKey: the run's drawing, its frames' index
// in it, the render's settings, the browser for what a browser draws) and taken again by a later render whose chunk has
// the same key. What a page loads is known only once it has drawn, so <key>.json records the files the chunk's page was
// sent and their sha256 then: the chunk is taken only while every one of them is still those bytes, and while the chunk
// itself is (its size and sha256 are on record too).
// A size cap: after a render, the chunks used longest ago go first (a record's mtime is its last use).
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

export const CACHE = path.join("out", "cache", "chunks");

function sum(f) {   // a file's sha256, or null
  try {
    const h = crypto.createHash("sha256"), fd = fs.openSync(f, "r"), buf = Buffer.alloc(1 << 22);
    try { for (let n; (n = fs.readSync(fd, buf, 0, buf.length, null)) > 0;) h.update(buf.subarray(0, n)); } finally { fs.closeSync(fd); }
    return h.digest("hex");
  } catch { return null; }
}

export class ChunkCache {
  // dir: the cache folder; root: the project (the records name files from it); max: bytes kept after a render
  constructor(dir, root, max) {
    this.dir = dir; this.root = root; this.max = max; this.hashes = new Map();
    fs.mkdirSync(dir, { recursive: true });
  }

  hash(f) {   // a file's sha256, once a render: the same page files are asked of every chunk
    if (!this.hashes.has(f)) this.hashes.set(f, sum(f));
    return this.hashes.get(f);
  }
  rel(f) { const r = path.relative(this.root, f); return r && !r.startsWith("..") && !path.isAbsolute(r) ? r.split(path.sep).join("/") : f; }
  abs(f) { return path.isAbsolute(f) ? f : path.join(this.root, f); }

  // the cached chunk for key when it is there, n frames long, and every file its page was sent is still the same bytes:
  // → { file, files: {absolute path: sha256} } (its last use is now), or null
  get(key, n) {
    const file = path.join(this.dir, `${key}.mp4`), rec = path.join(this.dir, `${key}.json`);
    let r;
    try { r = JSON.parse(fs.readFileSync(rec, "utf8")); } catch { return null; }
    if (!r || r.key !== key || r.frames !== n || !fs.existsSync(file) || fs.statSync(file).size !== r.bytes) return null;   // cut short or not ours
    if (sum(file) !== r.sha256) return null;   // its bytes are not the chunk it was (a chunk is small: this is quick)
    const files = {};
    for (const [f, h] of Object.entries(r.files || {})) {
      const a = this.abs(f);
      if (!h || this.hash(a) !== h) return null;
      files[a] = h;
    }
    const now = new Date();
    try { fs.utimesSync(rec, now, now); } catch { /* a read-only cache still serves */ }
    return { file, files };
  }

  // a finished chunk kept under its key (linked when the disk allows, else copied), with the files its page was sent
  put(key, chunk, n, files) {
    const file = path.join(this.dir, `${key}.mp4`), rec = path.join(this.dir, `${key}.json`), tmp = path.join(this.dir, `.${key}.${process.pid}`);
    try {
      try { fs.linkSync(chunk, `${tmp}.mp4`); } catch { fs.copyFileSync(chunk, `${tmp}.mp4`); }
      fs.renameSync(`${tmp}.mp4`, file);
      const record = { key, frames: n, bytes: fs.statSync(file).size, sha256: sum(file), files: Object.fromEntries(Object.entries(files).map(([f, h]) => [this.rel(f), h]).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))) };
      fs.writeFileSync(`${tmp}.json`, JSON.stringify(record, null, 1) + "\n");
      fs.renameSync(`${tmp}.json`, rec);
      return true;
    } catch {
      for (const f of [`${tmp}.mp4`, `${tmp}.json`]) { try { fs.rmSync(f, { force: true }); } catch { /* none */ } }
      return false;
    }
  }

  // a chunk out of the cache (one a check of the joined film did not pass)
  drop(key) {
    for (const ext of [".mp4", ".json"]) { try { fs.rmSync(path.join(this.dir, key + ext), { force: true }); } catch { /* gone */ } }
  }

  // the cache within its cap: the chunks used longest ago go first; a chunk without its record, and what an earlier
  // render left half written, go too. → { kept, bytes, evicted (chunks past the cap), cleared (leftovers) }
  prune() {
    let names = [];
    try { names = fs.readdirSync(this.dir); } catch { return { kept: 0, bytes: 0, evicted: 0, cleared: 0 }; }
    const items = [];
    let cleared = 0, evicted = 0;
    for (const f of names) {
      const p = path.join(this.dir, f);
      if (f.startsWith(".")) {   // a put another render is making now is young; one left by a killed render is not
        try { if (Date.now() - fs.statSync(p).mtimeMs > 3600e3) { fs.rmSync(p, { force: true }); cleared++; } } catch { /* gone */ }
        continue;
      }
      if (!f.endsWith(".mp4")) continue;
      const rec = p.replace(/\.mp4$/, ".json");
      try { items.push({ p, rec, used: fs.statSync(rec).mtimeMs, size: fs.statSync(p).size }); }
      catch { fs.rmSync(p, { force: true }); cleared++; }
    }
    for (const f of names) if (f.endsWith(".json") && !names.includes(f.replace(/\.json$/, ".mp4"))) { fs.rmSync(path.join(this.dir, f), { force: true }); cleared++; }
    items.sort((a, b) => a.used - b.used);
    let bytes = items.reduce((s, x) => s + x.size, 0);
    while (items.length && bytes > this.max) {
      const x = items.shift();
      fs.rmSync(x.p, { force: true }); fs.rmSync(x.rec, { force: true });
      bytes -= x.size; evicted++;
    }
    return { kept: items.length, bytes, evicted, cleared };
  }
}
