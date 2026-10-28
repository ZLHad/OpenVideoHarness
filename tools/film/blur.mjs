// Motion blur for bin/vh render and bin/vh frames (--motion-blur N): a frame is the mean of N sub-frames, the page drawn
// at N times spread over a shutter centred on the frame's own time (a fraction of a frame: 0.5 by default, a 180°
// shutter), so the blurred picture sits where the sharp one did.
//   Sub-frame j of frame k is drawn at frame k + δj, δj = a + (j + ½) / N · (b − a): the middle of the j-th of N equal
//   parts of [a, b], the shutter [−s/2, s/2] cut short where the frame's picture ends: the frames its run draws (the
//   film's first and last; an edit list's entry), the page's end, and the boundaries of the page's own shots
//   (window.film.shots). So no frame is a double exposure of two shots, and no sub-frame asks the page for a time
//   outside it. Each time comes from k, N and the shutter alone, never from the frame before (hard rule 1: a frame drawn
//   alone, in another render or in another order is the same picture).
// The mean is ffmpeg's tmix, in the frames' own values (sRGB-encoded, as editors blur); a picture with an alpha is
// averaged premultiplied, so a clear pixel's colour counts for nothing.
export const MAX_SAMPLES = 64;
const E = 1e-6;

// a page's shot boundaries in its own seconds (the start and end of each shot of window.film.shots that has both, end
// after start, read as bin/vh render reads them for its sidecar), sorted, each once: the shutter does not reach across
// them. A transition's first frame gets the shorter shutter too, which does not show; a hard cut would otherwise show
// both of its shots in one frame
export function shotCuts(shots) {
  const out = new Set();
  for (const s of Array.isArray(shots) ? shots : []) {
    const a = s ? +s.start : NaN, b = s ? +s.end : NaN;
    if (Number.isFinite(a) && Number.isFinite(b) && b > a) { out.add(a); out.add(b); }
  }
  return [...out].sort((p, q) => p - q);
}

// where frame k's shutter may reach, in film frames: span [K0, K1) the frames its run draws, end the page's end (Infinity
// for a page held past its end), cuts the page's shot boundaries
// a page drawn alone: the film's frames [0, last), its end, its shots (in seconds)
export function pageBounds(last, duration, fps, shots) {
  return { span: [0, last], end: duration > 0 ? duration * fps : Infinity, cuts: shotCuts(shots).map((c) => c * fps).filter((c) => c > E && c < last - E) };
}
// a run of an edit list (tools/film/edit.mjs): its frames; a page's end and shots (page: { duration, shots }, its facts)
// in the film's frames, on the film's clock at u · fps, on its own at K0 + (u − in) · fps / speed
export function runBounds(run, fps, page = null) {
  const span = run.frames;
  if (run.draw !== "page" || !page) return { span, end: Infinity, cuts: [] };
  const toK = run.clock === "film" ? (u) => u * fps : (u) => span[0] + (u - run.in) * fps / run.speed;
  return { span, end: run.hold || !(page.duration > 0) ? Infinity : toK(page.duration),
    cuts: shotCuts(page.shots).map(toK).filter((c) => c > span[0] + E && c < span[1] - E) };
}

// the offsets δ (frames, from frame k's own time) of frame k's n sub-frames; k can be a fraction (bin/vh frames --at)
export function offsets(k, n, shutter, { span, end = Infinity, cuts = [] }) {
  let lo = Math.max(-shutter / 2, span[0] - k), hi = Math.min(shutter / 2, span[1] - k, end - k);
  for (const c of cuts) { if (c <= k + E) lo = Math.max(lo, Math.min(0, c - k)); else hi = Math.min(hi, c - k); }
  if (!(hi > lo)) return Array(n).fill(0);   // nowhere to open (a frame at its page's very end): n times the frame itself
  return Array.from({ length: n }, (_, j) => lo + (j + 0.5) / n * (hi - lo));
}

// which runs of an edit list are drawn as sub-frames: a page's, and an image's that moves. A slate, a colour and an image
// that holds still would draw the same picture n times, and footage keeps the blur it was shot with
export const blurs = (run) => run.draw === "page" || (run.draw === "still" && !!run.move);

// the filter in front of an encoder fed n sub-frames a frame: n frames at a time averaged (tmix: frame m is the mean of
// m − n + 1 … m), the window that holds one frame's own n kept (select), and timed at the film's rate (setpts). alpha: the
// mean of the premultiplied colours, at 16 bits
export function meanFilter(n, fps, alpha = false) {
  const mean = `tmix=frames=${n},select='eq(mod(n\\,${n})\\,${n - 1})',setpts=N/(${fps}*TB)`;
  return alpha ? `format=rgba64le,premultiply=inplace=1,${mean},unpremultiply=inplace=1` : mean;
}
