// The host prelude (engines/CONTRACT.md, "宿主做什么"): runs before any page script. It sets window.filmHost, so a page
// knows it is being drawn and must not advance on its own, and from the first frame on holds every clock a page can read
// at the frame's t: performance.now() and requestAnimationFrame timestamps read t in ms, Date reads t after 2026-01-01,
// CSS and Web Animations stand at t (a CSS transition, whose progress is history, is finished), and Math.random restarts
// from a seed of t. Until the first frame (loading, `ready`) everything runs on real time; Math.random runs from a fixed
// seed. Hard rule 1 still says "don't read these": this keeps a page that does from drawing different pictures for the
// same t, and touched() tells the host which of them a frame read, so it can say so.
// The same idea as OpenFilm's FILM_CLOCK (MIT, packages/openfilm/src/host.mjs), written for this repo.
(() => {
  if (window.filmHost && window.filmHost.time) return;
  const H = (window.filmHost = { version: "0.1", name: "ovh" });
  const P = performance, realNow = P.now.bind(P), RealDate = Date, realRaf = window.requestAnimationFrame.bind(window);
  const EPOCH = RealDate.UTC(2026, 0, 1);
  let ms = null, seed = 0x5eed1e55 | 0, inFrame = false;
  const touched = new Set();
  const note = (what) => { if (inFrame) touched.add(what); };
  H.realNow = realNow;
  P.now = () => { if (ms === null) return realNow(); note("performance.now"); return ms; };
  function FilmDate(...a) {
    if (!a.length && ms !== null) note("Date");
    const d = a.length || ms === null ? new RealDate(...a) : new RealDate(EPOCH + ms);
    return new.target ? d : d.toString();
  }
  FilmDate.prototype = RealDate.prototype;
  FilmDate.now = () => { if (ms === null) return RealDate.now(); note("Date"); return EPOCH + ms; };
  FilmDate.parse = RealDate.parse; FilmDate.UTC = RealDate.UTC;
  window.Date = FilmDate;
  window.requestAnimationFrame = (cb) => realRaf((ts) => cb(ms === null ? ts : ms));
  // mulberry32: small, fast, and the same numbers in every browser
  const next = () => { seed = (seed + 0x6d2b79f5) | 0; let x = Math.imul(seed ^ (seed >>> 15), 1 | seed); x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x; return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
  Math.random = () => { note("Math.random"); return next(); };
  const mine = new WeakSet();
  // before frame(t): every clock reads t; Math.random starts again from t's seed
  H.time = (t) => { ms = t * 1000; seed = (Math.round(t * 1e6) ^ 0x5eed1e55) | 0; inFrame = true; touched.clear(); };
  // after frame(t): animations the page left running stand at t
  H.settle = (t) => {
    for (const a of (document.getAnimations ? document.getAnimations() : [])) {
      if (typeof CSSTransition !== "undefined" && a instanceof CSSTransition) { a.finish(); continue; }
      if (!mine.has(a)) { if (a.playState === "paused" || a.playState === "idle") continue; mine.add(a); }
      a.pause(); a.currentTime = t * 1000;
    }
    inFrame = false;
  };
  H.touched = () => [...touched];
})();
