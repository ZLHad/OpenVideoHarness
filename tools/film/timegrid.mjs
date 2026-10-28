// Seconds to frames, the one way the repo does it: tools/timegrid.py in JS, written the same way, so that in IEEE doubles
// the two give the same frame for the same seconds (tools/ci.sh checks it). frameFrom(t, fps): the first frame at or
// after t, ceil(t * fps - 1e-6), every boundary (a film's frame count, an edit list's entry, render --range, patch
// --seconds). frameAt(t, rate): the frame on screen at t, floor(t * rate + 1e-6) (a clip's in point, a thumbs tile).
// rate: a number, "24000/1001" or [24000, 1001]. Neither rounds t to the millisecond first.
export const EPS = 1e-6;

export function rateOf(rate) {
  let num, den;
  if (Array.isArray(rate) && rate.length === 2) [num, den] = rate;
  else if (typeof rate === "string") { const [a, b] = rate.trim().split("/"); num = Number(a); den = b === undefined ? 1 : Number(b); if (a === "" || b === "") num = NaN; }
  else { num = rate; den = 1; }
  if (typeof num !== "number" || typeof den !== "number" || !Number.isFinite(num) || !Number.isFinite(den) || !(num > 0) || !(den > 0))
    throw new Error(`not a frame rate: ${JSON.stringify(rate)}`);
  return [num, den];
}

export function frameFrom(t, fps) { const [num, den] = rateOf(fps); return Math.ceil(t * num / den - EPS); }
export function frameAt(t, rate) { const [num, den] = rateOf(rate); return Math.floor(t * num / den + EPS); }
