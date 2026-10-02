#!/usr/bin/env bash
# Export the opening's two shader textures from opening/index.html (opening/films.js: 28 procedural films):
#   assets/films-proc.png  4096×4032, 28 films × 16 frames   (the snapshot at 0.25 s)
#   assets/hero-earth.png  4096×2304, the opening film at 1024×576, 16 frames   (the top of the snapshot at 0.75 s)
# Both are gamma-encoded exactly as stored; blender/galaxy.py and the film read them. Needs `npm ci` in the film folder.
set -euo pipefail
cd "$(dirname "$0")/.."
export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1
ln -sfn ../node_modules opening/node_modules            # the page imports three from the film's own install
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
env -u GEMINI_API_KEY node_modules/.bin/hyperframes snapshot opening --at 0.25,0.75 --no-end --describe false --timeout 120000 -o "$tmp" >/dev/null
mkdir -p assets
ffmpeg -v error -y -i "$tmp/frame-00-at-0.25s.png" -pix_fmt rgb24 assets/films-proc.png
ffmpeg -v error -y -i "$tmp/frame-01-at-0.75s.png" -vf crop=4096:2304:0:0 -pix_fmt rgb24 assets/hero-earth.png
echo "assets/films-proc.png assets/hero-earth.png"
