#!/usr/bin/env bash
# The intro film at 4K (3840×2160), run from the film folder after tools/deliver.sh (it reuses that run's mix):
#   1. the Blender plate at 4K: frames from `tools/bl_render.sh 0 474 final4k --pct 200` (native 4K, about 4× the
#      1080p time: roughly 6 h on an M3 Max) → a 4K plate, swapped in for the render and swapped back afterwards
#   2. HyperFrames at device scale 2 (`--resolution 4k`): the WebGL layers, the type canvases and the point sprites
#      draw at that density (js/main.js, js/fx.js, js/features.js, js/grid.js read window.devicePixelRatio); DOM type is
#      sharp by itself. WebGL lines stay one device pixel wide, so they are thinner than at 1080p.
#   3. mux with the 1080p cut's mix → out/final-4k.mp4 (the release asset intro-film-4k.mp4), then bin/vh check against
#      out/final.mp4: the first 4K render drew its pinned labels and the end card at twice the size (pin() and drawCTA
#      read canvas pixel sizes, fixed with / PR); the check fails on that, and lists glow and 1 px line differences as WARN
set -euo pipefail
export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1
B=../../bin/vh; FRAMES=3090; DUR=103.0; PLATE=blender/out/final4k; A=audio
[ -f $A/mix.wav ] || { echo "no $A/mix.wav: run tools/deliver.sh (or tools/build_audio.sh) first" >&2; exit 1; }
[ -f out/final.mp4 ] || { echo "no out/final.mp4: run tools/deliver.sh first (the 4K render is checked against it)" >&2; exit 1; }
mkdir -p out
if [ -d "$PLATE" ]; then   # the frames win; without them (7 GB), the encoded plate from an earlier run is used
  n=$(find "$PLATE" -name 'f_*.png' | wc -l | tr -d ' '); [ "$n" -ge 475 ] || { echo "4K plate has $n frames, need 475" >&2; exit 1; }
  ffmpeg -v error -y -framerate 30 -start_number 0 -i "$PLATE/f_%04d.png" -frames:v 475 \
    -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
    -c:v libx264 -crf 12 -preset slow -g 15 -movflags +faststart out/plate-4k.mp4
elif [ -s out/plate-4k.mp4 ]; then echo "no frames at $PLATE: using out/plate-4k.mp4 (CRF 12) from an earlier run"
else echo "no 4K plate: render it with tools/bl_render.sh 0 474 final4k --pct 200 (about 6 h)" >&2; exit 1; fi
cp assets/plate.mp4 out/plate-1080.mp4
restore() { cp out/plate-1080.mp4 assets/plate.mp4; }
trap restore EXIT
cp out/plate-4k.mp4 assets/plate.mp4
env -u GEMINI_API_KEY node_modules/.bin/hyperframes render . --resolution 4k --quality high --workers 2 --variables '{"grain":0}' --output out/final-4k-silent.mp4 > out/render-4k.log 2>&1
grep -q "rendered in" out/render-4k.log || { tail -5 out/render-4k.log >&2; exit 1; }
restore; trap - EXIT
nf=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 out/final-4k-silent.mp4)
[ "$nf" = "$FRAMES" ] || { echo "FAIL: $nf frames, expected $FRAMES" >&2; exit 1; }
CT="-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv"
AF="[1:a]apad,atrim=0:${DUR}[a]"
# shellcheck disable=SC2086   # $CT is several flags on purpose
ffmpeg -v error -y -i out/final-4k-silent.mp4 -i $A/mix.wav -filter_complex "$AF" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 18 -tune film -pix_fmt yuv420p $CT -c:a aac -b:a 256k -movflags +faststart out/final-4k.mp4
$B check out/final-4k.mp4 --against out/final.mp4   # the same picture as the approved 1080p cut (engines/README.md, 出 4K)
ls -la out/final-4k.mp4
