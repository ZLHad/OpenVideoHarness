// A time map: film time against another axis (days of a data series, steps, the seconds of an earlier cut), as knots
// [t, u] with straight lines between them, plus events on that axis with ids. A script or a tool solves it once
// (slow-downs, holds, read times) and writes the file; the film only looks values up, so a frame stays a function of t.
// t rises from knot to knot; u never falls (a flat stretch is a hold: the axis stands still while the film runs on).
// The Python counterpart is tools/audio/time_map.py; tools/audio/test_time_map.py checks that both read a map alike.
const MAP_ID = /^[A-Za-z0-9_]+$/, MAP_DAY = /^(\d{4})-(\d{2})-(\d{2})$/;
class TimeMap {
  constructor(map) {
    const fail = (s) => { throw new Error(`time map: ${s}`); };
    const num = (v) => typeof v === "number" && Number.isFinite(v);
    if (!map || typeof map !== "object" || Array.isArray(map)) fail("expected an object with version, axis, knots and events");
    if (map.version !== 1) fail(`version ${JSON.stringify(map.version)}: this engine reads version 1`);
    const axis = map.axis ?? { kind: "number" };
    if (!axis || typeof axis !== "object" || Array.isArray(axis)) fail("axis must be an object");
    const kind = axis.kind ?? "number";
    if (!["number", "date", "seconds"].includes(kind)) fail(`axis kind ${JSON.stringify(kind)}: one of number, date, seconds`);
    if (kind === "date" && !(typeof axis.origin === "string" && MAP_DAY.test(axis.origin) && TimeMap.utc(axis.origin) !== null))
      fail('a date axis needs an origin "YYYY-MM-DD" (u is days after it)');
    if (axis.unit !== undefined && typeof axis.unit !== "string") fail("axis unit must be a string");
    this.axis = Object.freeze({ ...axis, kind });
    if (!Array.isArray(map.knots) || map.knots.length < 2) fail("knots must list at least two [t, u] pairs");
    this.knots = Object.freeze(map.knots.map((k, i) => {
      if (!Array.isArray(k) || k.length !== 2 || !num(k[0]) || !num(k[1])) fail(`knot ${i + 1}: expected [t, u], two finite numbers`);
      if (k[0] < 0) fail(`knot ${i + 1}: t ${k[0]} is before the film starts`);
      if (i) {
        const p = map.knots[i - 1];
        if (!(k[0] > p[0])) fail(`knot ${i + 1}: t ${k[0]} does not come after ${p[0]} (t must rise from knot to knot)`);
        if (k[1] < p[1]) fail(`knot ${i + 1}: u ${k[1]} is below ${p[1]} (u may stand still, never go back)`);
      }
      return Object.freeze([k[0], k[1]]);
    }));
    if (map.events !== undefined && !Array.isArray(map.events)) fail("events must be a list");
    const seen = new Set();
    this.byId = new Map();
    this.list = Object.freeze((map.events || []).map((e, i) => {
      if (!e || typeof e !== "object" || Array.isArray(e)) fail(`event ${i + 1}: expected an object`);
      if (typeof e.id !== "string" || !MAP_ID.test(e.id)) fail(`event ${i + 1}: id ${JSON.stringify(e.id)}: letters, digits and _`);
      if (seen.has(e.id)) fail(`event ${e.id}: the id is used twice`);
      seen.add(e.id);
      if (!num(e.u) || !num(e.t)) fail(`event ${e.id}: needs a finite u and t`);
      if (e.u < this.knots[0][1] || e.u > this.knots[this.knots.length - 1][1]) fail(`event ${e.id}: u ${e.u} is outside the axis (${this.knots[0][1]}–${this.knots[this.knots.length - 1][1]})`);
      const [lo, hi] = this.reach(e.u);
      if (e.t < lo - 0.001 || e.t > hi + 0.001) fail(`event ${e.id}: t ${e.t} s is not where the knots put u ${e.u} (${lo === hi ? `${lo} s` : `${lo}–${hi} s`})`);
      if (e.end !== undefined && !(num(e.end) && e.end >= e.t)) fail(`event ${e.id}: end must be a number of seconds, not before t`);
      for (const k of ["lane", "text"]) if (e[k] !== undefined && typeof e[k] !== "string") fail(`event ${e.id}: ${k} must be a string`);
      if (e.data !== undefined && (!e.data || typeof e.data !== "object" || Array.isArray(e.data))) fail(`event ${e.id}: data must be an object`);
      const ev = Object.freeze({ ...e, ...(e.data ? { data: Object.freeze({ ...e.data }) } : {}) });
      this.byId.set(e.id, ev);
      return ev;
    }));
    Object.freeze(this);
  }
  static utc(iso) {   // "YYYY-MM-DD" → ms since 1970 (UTC), or null for a date that does not exist
    const m = MAP_DAY.exec(iso);
    if (!m) return null;
    const ms = Date.UTC(+m[1], +m[2] - 1, +m[3]), d = new Date(ms);
    return d.getUTCFullYear() === +m[1] && d.getUTCMonth() === +m[2] - 1 && d.getUTCDate() === +m[3] ? ms : null;
  }
  // the first and the last film second the axis stands at u (the same one unless u is a hold)
  reach(u) {
    const K = this.knots, t0 = this.t(u);
    let i = 0, hi = K.length - 1;
    while (i < hi) { const m = (i + hi + 1) >> 1; if (K[m][1] <= u) i = m; else hi = m - 1; }   // the last knot at or below u
    return [t0, K[i][1] === u ? K[i][0] : t0];
  }
  u(t) {   // film seconds → the axis at that moment (before the first knot and after the last: the ends)
    if (typeof t !== "number" || !Number.isFinite(t)) throw new Error("time map: t must be finite seconds");
    const K = this.knots, n = K.length;
    if (t <= K[0][0]) return K[0][1];
    if (t >= K[n - 1][0]) return K[n - 1][1];
    let lo = 0, hi = n - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (K[m][0] <= t) lo = m; else hi = m; }
    const [ta, ua] = K[lo], [tb, ub] = K[hi];
    return ua + (ub - ua) * ((t - ta) / (tb - ta));
  }
  t(u) {   // the axis → the first film second it gets there
    if (typeof u !== "number" || !Number.isFinite(u)) throw new Error("time map: u must be a finite number (a date axis: day(\"YYYY-MM-DD\"))");
    const K = this.knots, n = K.length;
    if (u < K[0][1] || u > K[n - 1][1]) throw new Error(`time map: u ${u} is outside the axis (${K[0][1]}–${K[n - 1][1]})`);
    let lo = 0, hi = n - 1;
    while (lo < hi) { const m = (lo + hi) >> 1; if (K[m][1] >= u) hi = m; else lo = m + 1; }   // the first knot at or past u
    if (K[lo][1] === u) return K[lo][0];
    const [ta, ua] = K[lo - 1], [tb, ub] = K[lo];
    return ta + (tb - ta) * ((u - ua) / (ub - ua));
  }
  at(id, edge = "start") {   // an event's film second; "end": its end
    const e = this.byId.get(id);
    if (!e) {
      const near = [...this.byId.keys()].filter((k) => k.toLowerCase().includes(String(id).toLowerCase()) || String(id).toLowerCase().includes(k.toLowerCase())).slice(0, 3);
      throw new Error(`time map: no event "${id}" (${this.list.length} events${near.length ? `; nearest: ${near.join(", ")}` : ""})`);
    }
    if (edge === "start") return e.t;
    if (edge !== "end") throw new Error(`time map: edge ${JSON.stringify(edge)}: "start" or "end"`);
    if (e.end === undefined) throw new Error(`time map: event ${id} has no end`);
    return e.end;
  }
  dur(u0, u1) { return this.t(u1) - this.t(u0); }   // the film seconds a stretch of the axis takes
  rate(t) {   // axis units per film second at t (0 on a hold; past the ends, the end segments' rates)
    if (typeof t !== "number" || !Number.isFinite(t)) throw new Error("time map: t must be finite seconds");
    const K = this.knots;
    let lo = 0, hi = K.length - 1;   // the segment K[lo]..K[lo + 1] that holds t
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (K[m][0] <= t) lo = m; else hi = m; }
    return (K[lo + 1][1] - K[lo][1]) / (K[lo + 1][0] - K[lo][0]);
  }
  day(iso) {   // a date axis: "YYYY-MM-DD" → u (whole days after the origin)
    if (this.axis.kind !== "date") throw new Error(`time map: day() needs a date axis (this one is ${this.axis.kind})`);
    const ms = typeof iso === "string" ? TimeMap.utc(iso) : null;
    if (ms === null) throw new Error(`time map: ${JSON.stringify(iso)} is not a date "YYYY-MM-DD"`);
    return Math.round((ms - TimeMap.utc(this.axis.origin)) / 864e5);
  }
  get events() { return this.list; }
}

let TIMEMAP = null, TIMEMAP_SOURCE = null, TIMEMAP_MADE_ON = null;   // made on: { sources, rebuild } as the file records them
// Declarations run before ready: mapAt(u) leaves a reference for resolver(), like musicAt(); "@#id" names an event.
// In draw: mapU(t) (the axis now), mapT(u), eventT(id). u may be a date "YYYY-MM-DD" on a date axis.
function mapAt(u, offset = 0) { return { $map: u, offset }; }
function needMap() {
  if (!TIMEMAP) throw new CueError("no loaded time map: set FILM.timemap to a time map file; use mapAt() or \"@#id\" in declarations before ready");
  return TIMEMAP;
}
const mapPos = (u) => (typeof u === "string" ? needMap().day(u) : u);
function mapT(u) { return needMap().t(mapPos(u)); }
function mapU(t) { return needMap().u(t); }
function eventT(id, edge = "start") { return needMap().at(id, edge); }
const isMapAt = (v) => v && typeof v === "object" && Object.hasOwn(v, "$map");
function resolveMapAt(v) {
  const off = v.offset ?? 0;
  if (typeof off !== "number" || !Number.isFinite(off)) throw new CueError("mapAt: offset must be finite seconds");
  return mapT(v.$map) + off;
}
const MAP_CUE = /^@#(\w+)(>)?([+-](?:\d+\.?\d*|\.\d+))?$/;
function mapCueT(c) {   // "@#id" (the event's time), "@#id>" (its end), either + or - seconds
  const m = MAP_CUE.exec(c);
  if (!m) throw new CueError(`not an event cue: write "@#id" (the event's time) or "@#id>" (its end), with an optional +0.3 or -0.2; ids are letters, digits and _`);
  try { return needMap().at(m[1], m[2] ? "end" : "start") + (m[3] ? +m[3] : 0); }
  catch (e) { if (e instanceof CueError) throw e; throw new CueError(e.message.replace(/^time map: /, "")); }
}
const sha256hex = async (bytes) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map((x) => x.toString(16).padStart(2, "0")).join("");
async function loadTimeMap() {
  if (!FILM.timemap) return;
  if (typeof FILM.timemap !== "string") throw new Error("canvas-film: FILM.timemap must be a time map path");
  const r = await fetch(FILM.timemap, { cache: "no-store" });
  if (!r.ok) throw new Error(`canvas-film: no ${FILM.timemap} (FILM.timemap, HTTP ${r.status})`);
  const bytes = await r.arrayBuffer();
  let map;
  try { map = JSON.parse(new TextDecoder().decode(bytes)); TIMEMAP = new TimeMap(map); }
  catch (e) { throw new Error(`canvas-film: ${FILM.timemap}: ${e.message}`); }
  TIMEMAP_SOURCE = { path: FILM.timemap, sha256: await sha256hex(bytes) };
  TIMEMAP_MADE_ON = { sources: Array.isArray(map.sources) ? map.sources : [], rebuild: typeof map.rebuild === "string" ? map.rebuild : null };
}
// A map made on a narration take or a beat map records their sha256 ("sources", paths beside the map). When the page
// loaded another version of one of them, the map's times belong to the old one: stop in ready, naming the command that
// rebuilds the map ("rebuild" in the file). Sources the page does not load are left to tools/audio/time_map.py check.
// T: the timeline as loadTimeline() read it; its bytes are hashed, not fetched again (a file rewritten in between would
// pass the check while the film is built from the old take). The beat map's hash is of the bytes loadMusic() parsed.
async function checkTimeMapSources(T) {
  if (!TIMEMAP_SOURCE) return;
  const { sources, rebuild } = TIMEMAP_MADE_ON, base = new URL(FILM.timemap, location.href), href = (p) => new URL(p, location.href).href;
  const loaded = new Map();
  if (MUSIC_SOURCE) loaded.set(href(MUSIC_SOURCE.path), async () => MUSIC_SOURCE.sha256);
  if (T) loaded.set(href(T.file), async () => sha256hex(T.bytes));
  const stale = [];
  for (const s of sources) {
    if (!s || typeof s.path !== "string" || typeof s.sha256 !== "string") continue;
    const get = loaded.get(new URL(s.path, base).href);
    if (!get) continue;
    const now = await get();
    if (now !== s.sha256) stale.push(`${s.path} (recorded sha256 ${s.sha256.slice(0, 12)}, loaded ${now.slice(0, 12)})`);
  }
  if (stale.length) throw new Error(`canvas-film: ${FILM.timemap} was made on another version of ${stale.join(" and ")}: ` +
    (rebuild ? `rebuild it: ${rebuild}` : "rebuild it with the script that wrote it (its \"rebuild\" field can name the command)"));
}
