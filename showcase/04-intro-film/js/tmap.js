// The film's time map. The picture is written on the "old" 87.5 s timeline; 15 short holds are stretched where a read
// went by too fast (user 2026-10-04: the 150.5 s cut, with 26 stretches, paused too long after every line; the 87.5 s
// cut's pacing was right apart from a few shots that flashed by). A line holds long enough to read once in either
// language (the slower of English at ~20 characters/s and Chinese at ~7/s, plus 0.8 s, at least 1.5 s), then moves on.
// (terminal, router, types, catalog, engines, gate 2, pass, gate 3, final cut, sound, cases, made by an agent,
// the request → this film, this film too, the title.)
// [a, b, add] in old film seconds: the hold a..b plays over (b − a + add) s and everything after it moves later by add.
// The music has the same map (audio/score.json: the bar that holds a stretch is longer by add / beat and its pattern
// keeps going; the opening sketch plays its bar 11 twice for the first one), and so do the SFX (audio/events.json).
// Ambient motion (sparks, the films' playback, the hand-held drift) runs on the new time, so a stretched hold slows
// the story, never the world.
window.__STRETCH = [[21.3, 22.0, 2.0], [24.75, 25.4, 1.5], [29.25, 29.975, 0.75], [32.5, 32.975, 0.75], [34.3, 35.45, 0.75], [42.54, 42.95, 0.75], [48.54, 49.02, 0.75], [49.29, 49.55, 0.75], [50.375, 51.35, 1.5], [56.825, 56.975, 0.75], [62.6, 62.975, 0.75], [64.625, 66.125, 0.75], [71.45, 72.5, 1.5], [76.625, 78.125, 0.75], [85.5, 87.0, 1.5]];
window.__OLD_DUR = 87.5;
window.__tNew = (o) => { let s = 0; for (const [a, b, add] of window.__STRETCH) { if (o < a) return o + s; if (o < b) return a + s + (o - a) * (b - a + add) / (b - a); s += add; } return o + s; };
window.__tOld = (f) => { let s = 0; for (const [a, b, add] of window.__STRETCH) { const na = a + s, nb = b + s + add; if (f < na) return f - s; if (f < nb) return a + (f - na) * (b - a) / (b - a + add); s += add; } return f - s; };
window.__NEW_DUR = window.__tNew(window.__OLD_DUR);
