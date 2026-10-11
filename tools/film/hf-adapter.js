// window.film for a HyperFrames composition that does not write its own (engines/CONTRACT.md). The host puts this right
// after HyperFrames' own runtime (hyperframe.runtime.iife.js) before </head>, where HyperFrames' preview puts it, and
// leaves the composition untouched. A frame is the runtime's own seek, window.__player.renderSeek(t): clips shown by
// their data-start and data-duration, the registered GSAP timelines and the runtime's other adapters at t.
// HyperFrames' renderer also injects things this does not (virtual time, a GSAP tween buffer), so these frames are
// close to its render, not guaranteed identical: the film itself is still rendered with `npx hyperframes render`.
(() => {
  if (window.film) return;
  const H = window.filmHost, now = () => (H && H.realNow ? H.realNow() : performance.now());
  const root = () => document.querySelector("[data-composition-id]");
  const player = () => (window.__player && typeof window.__player.renderSeek === "function" ? window.__player : null);
  window.film = {
    get duration() {
      const p = player(), d = p ? Number(p.getDuration()) : 0;
      return d > 0 ? d : Number((root() && root().dataset.duration) || 0);
    },
    // the runtime is ready when it has bound the composition's timelines (window.__renderReady) and knows the length
    ready: () => new Promise((ok, no) => {
      const t0 = now();
      const wait = () => {
        const p = player();
        if (p && window.__renderReady && Number(p.getDuration()) > 0) return ok();
        if (now() - t0 > 60000) {
          return no(new Error(p ? "the HyperFrames runtime did not bind the timelines within 60 s (is the root timeline registered as window.__timelines[\"<data-composition-id>\"]?)"
            : "the HyperFrames runtime did not start within 60 s"));
        }
        setTimeout(wait, 50);
      };
      wait();
    }),
    async frame(t) {
      const p = player();
      if (!p) throw new Error("the HyperFrames runtime is not loaded");
      p.renderSeek(t);
      if (typeof window.__hfWaitForSeekCompletion === "function") await window.__hfWaitForSeekCompletion();
    },
  };
  window.film.__adapter = "hyperframes";
})();
