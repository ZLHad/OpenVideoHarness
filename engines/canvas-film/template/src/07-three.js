// canvas-film · the Three.js layer's hook (optional): nothing here does anything unless src/50-shots.js sets FILM.three.
// With it, ready imports three/layer.js (a project made with bin/vh new … --engine canvas-film --three has it: the layer
// and a pinned three.js, from engines/canvas-film/three/; film.html's import map points "three" there), loads the models
// and builds the world. A shot with a three field gets its 3D drawn first, under everything its draw(t, s) paints; the
// chapter bar and the caption go over both as ever (ENGINE_README.md, Three.js 层).
let THREE_LAYER = null;
async function loadThree() {
  if (!FILM.three) return;
  let mod;
  try { mod = await import(new URL("three/layer.js", document.baseURI).href); }
  catch (e) {
    throw new Error(`canvas-film: FILM.three is set, and three/layer.js did not load (${e.message}): bin/vh new … --engine canvas-film --three ` +
      "puts the layer in a project; an older project copies engines/canvas-film/three/ in as three/ (ENGINE_README.md, Three.js 层)");
  }
  THREE_LAYER = await mod.load(FILM.three, { width: W, height: H, dpr: PRX });
}
// in ready, once the shots' cues are seconds: each shot's three against the models (its clips are there, and long enough
// for the shot); a problem joins the others ready lists
function checkThree(problems) {
  const shots = SHOT_T.filter((S) => S.three);
  if (!shots.length) return;
  if (!THREE_LAYER) { for (const S of shots) problems.push(`shot ${S.id}: three, and FILM.three is not set (the layer's models, camera and lights)`); return; }
  THREE_LAYER.check(shots.map((S) => ({ id: S.id, t0: S.a, t1: S.b + S.dout, three: S.three })), problems);
}
// shot S's 3D at t into X, under the shot's own drawing (src/90-main.js, drawShot); posed but not drawn while the recorder samples
function drawThree(t, S) { if (THREE_LAYER) THREE_LAYER.draw(X, t, SHOT, S.three, { record: !!REC }); }
