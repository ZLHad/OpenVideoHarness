// config.js: project settings.
//   duration: the video's length in seconds.
//   bpm:      the rhythm that bounces, dances and pulse() follow. Clawd always moves to some beat; if the video has music,
//             set this to the song's tempo, and set offset to the time in seconds of its first downbeat.
// "Clawd and the Leaf": 12 s, silent, 120 bpm (BEAT = 0.5 s) so key hits can land on half-seconds.
const PROJECT = { duration: 12, bpm: 120, offset: 0 };
