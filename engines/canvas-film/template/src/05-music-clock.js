// Music time comes from bin/vh music's beat map, never a second meter table in the film.
// Bar and beat are both 1-based; beat may be fractional. Map seconds already include
// any placement/offset: do not add the map's beat-detection `offset` again.
class MusicClock {
  constructor(map) {
    const fail = (s) => { throw new Error(`music clock: ${s}`); };
    const num = (v) => typeof v === "number" && Number.isFinite(v);
    if (!map || !num(map.bpm) || map.bpm <= 0 || !num(map.duration) || map.duration <= 0)
      fail("a beat map needs positive bpm and duration");
    if (!Array.isArray(map.bars) || !map.bars.length)
      fail("no bars table; regenerate the beat map with bin/vh music (an analysed audio beat map is not a score)");
    this.beat = 60 / map.bpm; this.duration = map.duration;
    this.bars = map.bars.map((row, i) => {
      if (!Array.isArray(row) || row.length !== 3) fail(`bar ${i + 1}: expected [number, start, beats]`);
      const [id, start, beats] = row;
      if (id !== i + 1 || !num(start) || start < 0 || start >= this.duration || !Number.isInteger(beats) || beats < 1)
        fail(`bar ${i + 1}: invalid number, start or beat count`);
      if (i) {
        const prev = map.bars[i - 1];
        if (start <= prev[1] || Math.abs(start - prev[1] - prev[2] * this.beat) > 0.002)
          fail(`bar ${id}: start disagrees with the preceding bar and bpm`);
      }
      return Object.freeze([...row]);
    });
    Object.freeze(this.bars);
    if (map.notes !== undefined && !Array.isArray(map.notes)) fail("notes must be a list");
    this.noteMap = map.notes === undefined ? null : map.notes.map((n, i) => {
      if (!n || !num(n.t) || !num(n.end) || n.end < n.t || typeof n.part !== "string" || !n.part)
        fail(`note ${i + 1}: expected part, finite t and end >= t`);
      return Object.freeze({ ...n });
    }).sort((a, b) => a.t - b.t);
    if (this.noteMap) Object.freeze(this.noteMap);
    Object.freeze(this);
  }
  at(bar, beat = 1, offset = 0) {
    const row = Number.isInteger(bar) && this.bars[bar - 1];
    if (!row) throw new Error(`music clock: no bar ${bar} (1–${this.bars.length})`);
    if (typeof beat !== "number" || !Number.isFinite(beat) || beat < 1 || beat > row[2] + 1)
      throw new Error(`music clock: bar ${bar} beat ${beat} is outside 1–${row[2] + 1} (the last value is the boundary)`);
    if (typeof offset !== "number" || !Number.isFinite(offset)) throw new Error("music clock: offset must be finite seconds");
    const next = this.bars[bar], t = (beat === row[2] + 1 && next ? next[1] : row[1] + (beat - 1) * this.beat) + offset;
    if (t < -1e-9 || t > this.duration + 0.001) throw new Error(`music clock: ${t} s is outside the rendered music (0–${this.duration} s)`);
    return Math.max(0, Math.min(this.duration, t));
  }
  notes(part) {
    if (this.noteMap === null) throw new Error('music clock: no notes table; set "note_map": true on the score part and regenerate the music');
    return this.noteMap.filter((n) => n.part === part).map((n) => ({ ...n }));
  }
}

let MUSIC = null, MUSIC_SOURCE = null;
// Declarations run before ready: leave a reference for resolver(), rather than
// looking up a map that has not loaded yet. Numeric queries belong inside draw().
function musicAt(bar, beat = 1, offset = 0) { return { $music: [bar, beat], offset }; }
function musicT(bar, beat = 1, offset = 0) {
  if (!MUSIC) throw new CueError("no loaded music clock: set FILM.music to a bin/vh music beat map; use musicAt() in declarations before ready");
  return MUSIC.at(bar, beat, offset);
}
function musicNotes(part) {
  if (!MUSIC) throw new CueError("no loaded music clock (FILM.music)");
  return MUSIC.notes(part);
}
function musicNotesT(part) { return musicNotes(part).map((n) => n.t); }
const isMusicAt = (v) => v && typeof v === "object" && Object.hasOwn(v, "$music");
function resolveMusicAt(v) {
  if (!Array.isArray(v.$music) || v.$music.length !== 2) throw new CueError("invalid musicAt reference");
  return musicT(...v.$music, v.offset ?? 0);
}
async function loadMusic() {
  if (!FILM.music) return;
  if (typeof FILM.music !== "string") throw new Error("canvas-film: FILM.music must be a beat-map path");
  const r = await fetch(FILM.music, { cache: "no-store" });
  if (!r.ok) throw new Error(`canvas-film: no ${FILM.music} (FILM.music, HTTP ${r.status})`);
  const bytes = await r.arrayBuffer();
  try { MUSIC = new MusicClock(JSON.parse(new TextDecoder().decode(bytes))); }
  catch (e) { throw new Error(`canvas-film: ${FILM.music}: ${e.message}`); }
  const sha = await crypto.subtle.digest("SHA-256", bytes);
  MUSIC_SOURCE = { path: FILM.music, sha256: [...new Uint8Array(sha)].map((x) => x.toString(16).padStart(2, "0")).join("") };
}
