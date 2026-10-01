#!/usr/bin/env bash
# determinism.sh — prove a swatch is a pure function of t (CLAUDE.md hard rule 1).
#
#   styles/_swatch/determinism.sh <slug> [workers_b=3]
#
# Renders the lossless PNG sequence twice: once with 1 worker (frames in order) and once with <workers_b>
# workers, where every chunk after the first starts cold in a fresh Chrome (frames rendered out of order, no
# history). Then compares all 150 frames. PASS = every frame pixel-identical (render.sh renders on the CPU, so it must be).
# render.sh renders on the CPU (--no-browser-gpu), so the frames should be byte-identical: a pass with differing
# frames means Chrome got a GPU path again (check the `gl=` line in out/<slug>/render.log).
#
# A Blender scene (swatch.py) takes minutes per frame set, so it is checked the way hard rule 1 words it: 12 frames
# spread over the clip are rendered again, last to first, in <workers_b> fresh Blender processes, and compared with the
# same frames of the full in-order render (out/<slug>/frames from the last final render.sh, when its stamp still
# matches the scene; otherwise a full --png render with 1 process first). Final renders use Cycles on the CPU, which
# gives the same pixels on every run, so these must be identical too.
set -euo pipefail
SW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
slug=${1:?usage: styles/_swatch/determinism.sh <slug> [workers_b=3]}; wb=${2:-3}
[ "$wb" -gt 1 ] || { echo "workers_b must be > 1 (the second run has to split the frames)"; exit 1; }
name=$(basename "$slug"); OUT="$SW/out/$name"
case "$slug" in */*) SRC=$slug ;; *) SRC="$SW/../$slug" ;; esac
blender=0; [ ! -f "$SRC/swatch.js" ] && [ -f "$SRC/swatch.py" ] && blender=1
if [ $blender = 1 ]; then
  SAMPLE="149,137,120,104,90,75,61,45,30,12,3,0"
  A="$OUT/frames"; own_a=0
  if [ ! -f "$A/inputs.txt" ] || [ "$(cat "$A/inputs.txt")" != "$("$SW/render.sh" "$slug" --stamp)" ]; then
    echo "→ no final frames for the scene as it is now: rendering all of them in order first"
    "$SW/render.sh" "$slug" --png --workers 1; A="$OUT/png-w1"; own_a=1
  fi
  "$SW/render.sh" "$slug" --png --workers "$wb" --frames "$SAMPLE"
  B="$OUT/png-sample-w$wb"; LIST=$B
else
  "$SW/render.sh" "$slug" --png --workers 1
  "$SW/render.sh" "$slug" --png --workers "$wb"
  A="$OUT/png-w1"; B="$OUT/png-w$wb"; LIST=$A; own_a=1
fi
na=$(find "$A" -name '*.png' | wc -l | tr -d ' '); nb=$(find "$B" -name '*.png' | wc -l | tr -d ' ')
same=0; diff=0; worst=inf; worst_f=""
# every ffmpeg in this loop gets -nostdin: otherwise it reads the loop's stdin and eats the rest of the file list
while IFS= read -r f; do
  name=$(basename "$f"); fa="$A/$name"; fb="$B/$name"
  [ -f "$fa" ] && [ -f "$fb" ] || { echo "✗ $name missing in $([ -f "$fa" ] && echo "$B" || echo "$A")"; exit 1; }
  if cmp -s "$fa" "$fb"; then same=$((same + 1)); continue; fi
  # PNG bytes can differ with identical pixels (encoder metadata): compare decoded pixels (ffmpeg's md5 muxer, no md5/md5sum needed)
  pa=$(ffmpeg -nostdin -v error -i "$fa" -pix_fmt rgba -f md5 -); pb=$(ffmpeg -nostdin -v error -i "$fb" -pix_fmt rgba -f md5 -)
  if [ "$pa" = "$pb" ]; then same=$((same + 1)); continue; fi
  diff=$((diff + 1))
  p=$(ffmpeg -nostdin -v info -i "$fa" -i "$fb" -lavfi "[0:v]format=rgb24[a];[1:v]format=rgb24[b];[a][b]psnr" -f null - 2>&1 | sed -n 's/.*average:\([0-9.inf]*\).*/\1/p' | tail -1)
  echo "  differs: $name  PSNR ${p} dB"
  if [ "$worst" = inf ] || python3 -c "import sys; sys.exit(0 if float('$p') < float('$worst') else 1)"; then worst=$p; worst_f=$name; fi
done < <(find "$LIST" -name '*.png' | sort)
total=$((same + diff))
echo "frames: $total · pixel-identical: $same · differing: $diff$([ $diff -gt 0 ] && echo " · worst ${worst} dB ($worst_f)")"
want=$([ $blender = 1 ] && echo "$nb" || echo "$na")
[ "$total" -gt 0 ] && [ "$total" = "$want" ] && { [ $blender = 1 ] || [ "$total" = "$nb" ]; } \
  || { echo "✗ FAIL: compared $total frames, but ${A#$SW/} has $na PNGs and ${B#$SW/} has $nb"; exit 1; }
# PNG sequences are big (demo: ~560 MB for both runs); they are kept only when the check fails. The final render's own
# frames (out/<slug>/frames) are never removed here.
if [ $diff = 0 ]; then
  echo "✓ PASS: identical across 1 and $wb $([ $blender = 1 ] && echo "Blender processes (12 frames, last to first)" || echo workers)"
  rm -rf "$B"; [ $own_a = 1 ] && rm -rf "$A"; exit 0
fi
echo "✗ FAIL: $diff frame(s) differ (worst ${worst} dB): a frame depends on render order (hidden state, Math.random,"
if [ $blender = 1 ]; then
  echo "  random, time.time, a value kept from an earlier apply()) or on the GPU (final renders must say 'final: CPU' in the log)."
else
  echo "  unloaded font, time-based cache) or on the GPU. render.sh renders on the CPU: the gl= line in ${OUT#$SW/}/render.log should say swiftshader."
fi
echo "  frames kept for inspection: ${A#$SW/} and ${B#$SW/}"; exit 1
