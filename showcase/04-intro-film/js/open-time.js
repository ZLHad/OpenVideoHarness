// The opening's timeline (0–23 s, 120 BPM: a bar is 2 s), shared by the reads and the terminal.
export const BEAT = 0.5, bar = (k, b = 0) => (k - 1) * 2 + b * BEAT;
export const TL = { t1: [0.6, 4.4], burst: bar(5), t2: [10.4, 13.8], reveal: bar(8), t3: [14.5, 18.8], term: [18.95, 23.0], enter: bar(12), key: 21.2, answer: 21.35 }; // Enter is pressed at 21.2; the push into the terminal still starts on bar 12
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const seg = (t, a, b) => clamp((t - a) / (b - a));
export const eOut = (u) => 1 - Math.pow(1 - u, 3), eIn = (u) => u * u * u;
export const eOutExpo = (u) => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u));
export const eInOut = (u) => u * u * (3 - 2 * u);
