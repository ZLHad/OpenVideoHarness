// canvas-film · effects over a picture: film grain, a vignette, a shade. All of them are functions of t and their
// arguments only; the grain's noise tile is made once from a seeded hash.

let GRAIN = null;
function grainTile() {   // 256 x 256 grey noise, the same every time
  if (GRAIN) return GRAIN;
  const c = document.createElement("canvas"); c.width = c.height = 256;
  const g = c.getContext("2d"), im = g.createImageData(256, 256);
  for (let i = 0; i < 256 * 256; i++) { const v = Math.floor(hash(i * 1.37 + 0.5) * 255); im.data.set([v, v, v, 255], 4 * i); }
  g.putImageData(im, 0, 0);
  return (GRAIN = c);
}
// grain over everything drawn so far: the tile at an offset that changes once a frame (FILM.fps), mixed in "overlay"
function grain(t, a = 0.04) {
  if (a <= 0) return;
  const f = Math.floor(t * FILM.fps + 1e-6), ox = Math.floor(hash(f * 3.1 + 1) * 256), oy = Math.floor(hash(f * 7.7 + 2) * 256), tile = grainTile();
  X.save(); X.globalAlpha = a; X.globalCompositeOperation = "overlay"; X.imageSmoothingEnabled = false;   // 4K: the same grain, not blurred
  for (let x = -ox; x < W; x += 256) for (let y = -oy; y < H; y += 256) X.drawImage(tile, x, y);
  X.restore();
}
// darker towards the corners: a at the edge, nothing inside `inner` (a share of the frame's height)
function vignette(a = 0.5, inner = 0.45) {
  if (a <= 0) return;
  const g = X.createRadialGradient(W / 2, H / 2, H * inner, W / 2, H / 2, H * 1.05);
  g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, `rgba(0,0,0,${a})`);
  X.save(); X.fillStyle = g; X.fillRect(0, 0, W, H); X.restore();
}
// the whole frame under a colour at alpha a (rgb as "r,g,b")
function shade(a, rgb = "0,0,0") {
  if (a <= 0.002) return;
  X.save(); X.fillStyle = `rgba(${rgb},${Math.min(1, a)})`; X.fillRect(0, 0, W, H); X.restore();
}
