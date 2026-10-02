// The film's time map (review rounds 3–5: every read must hold long enough, TASTE_CHECKLIST #5).
// The picture is written on the "old" 87.5 s timeline; 26 holds are stretched to give their reads time:
// [a, b, add] in old film seconds: the hold a..b plays over (b − a + add) s and everything after it moves later by add.
// The music has the same map (audio/score.json: the bar that holds a stretch is longer by add / beat, its added beats
// are a held breath, drums out; the opening sketch plays its bar 11 four times for the first one), and so do the SFX
// (audio/events.json). Ambient motion (sparks, the films' playback, the hand-held drift) runs on the new time,
// so a stretched hold slows the story, never the world.
window.__STRETCH = [[21.3, 22.0, 6.0], [24.75, 25.4, 3.75], [29.25, 29.975, 2.25], [31.1, 31.95, 2.25], [32.5, 32.975, 3.0], [34.3, 35.45, 3.0], [37.4, 38.3, 1.5], [39.52, 39.72, 1.5], [42.54, 42.95, 1.5], [45.52, 45.575, 2.25], [46.475, 47.9, 2.25], [48.54, 49.02, 2.25], [49.29, 49.55, 2.25], [50.375, 51.35, 2.25], [52.4, 53.975, 2.25], [56.825, 56.975, 4.5], [59.79, 59.975, 3.0], [62.6, 62.975, 2.25], [64.625, 66.125, 2.25], [66.95, 68.4125, 1.5], [69.5, 70.6625, 1.5], [71.45, 72.5, 3.0], [74.8, 75.1625, 1.5], [76.625, 78.125, 1.5], [80.825, 81.425, 1.5], [85.5, 87.0, 2.25]];
window.__OLD_DUR = 87.5;
window.__tNew = (o) => { let s = 0; for (const [a, b, add] of window.__STRETCH) { if (o < a) return o + s; if (o < b) return a + s + (o - a) * (b - a + add) / (b - a); s += add; } return o + s; };
window.__tOld = (f) => { let s = 0; for (const [a, b, add] of window.__STRETCH) { const na = a + s, nb = b + s + add; if (f < na) return f - s; if (f < nb) return a + (f - na) * (b - a) / (b - a + add); s += add; } return f - s; };
window.__NEW_DUR = window.__tNew(window.__OLD_DUR);
