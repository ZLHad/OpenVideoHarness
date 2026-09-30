#!/usr/bin/env bash
# determinism.sh — prove a swatch is a pure function of t (CLAUDE.md hard rule 1).
#
#   styles/_swatch/determinism.sh <slug> [workers_b=3]
#
# Renders the lossless PNG sequence twice: once with 1 worker (frames in order) and once with <workers_b>
# workers, where every chunk after the first starts cold in a fresh Chrome (frames rendered out of order, no
# history). Then compares all 150 frames. PASS = every frame identical, or every differing frame ≥ 45 dB PSNR.
set -euo pipefail
SW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
slug=${1:?usage: styles/_swatch/determinism.sh <slug> [workers_b=3]}; wb=${2:-3}
[ "$wb" -gt 1 ] || { echo "workers_b must be > 1 (the second run has to split the frames)"; exit 1; }
OUT="$SW/out/$slug"
"$SW/render.sh" "$slug" --png --workers 1
"$SW/render.sh" "$slug" --png --workers "$wb"
A="$OUT/png-w1"; B="$OUT/png-w$wb"
na=$(find "$A" -name '*.png' | wc -l | tr -d ' '); nb=$(find "$B" -name '*.png' | wc -l | tr -d ' ')
same=0; diff=0; worst=inf; worst_f=""
# every ffmpeg in this loop gets -nostdin: otherwise it reads the loop's stdin and eats the rest of the file list
while IFS= read -r f; do
  name=$(basename "$f")
  [ -f "$B/$name" ] || { echo "✗ $name missing in $B"; exit 1; }
  if cmp -s "$f" "$B/$name"; then same=$((same + 1)); continue; fi
  # PNG bytes can differ with identical pixels (encoder metadata): compare decoded pixels (ffmpeg's md5 muxer, no md5/md5sum needed)
  pa=$(ffmpeg -nostdin -v error -i "$f" -pix_fmt rgba -f md5 -); pb=$(ffmpeg -nostdin -v error -i "$B/$name" -pix_fmt rgba -f md5 -)
  if [ "$pa" = "$pb" ]; then same=$((same + 1)); continue; fi
  diff=$((diff + 1))
  p=$(ffmpeg -nostdin -v info -i "$f" -i "$B/$name" -lavfi "[0:v]format=rgb24[a];[1:v]format=rgb24[b];[a][b]psnr" -f null - 2>&1 | sed -n 's/.*average:\([0-9.inf]*\).*/\1/p' | tail -1)
  echo "  differs: $name  PSNR ${p} dB"
  if [ "$worst" = inf ] || python3 -c "import sys; sys.exit(0 if float('$p') < float('$worst') else 1)"; then worst=$p; worst_f=$name; fi
done < <(find "$A" -name '*.png' | sort)
total=$((same + diff))
echo "frames: $total · pixel-identical: $same · differing: $diff$([ $diff -gt 0 ] && echo " · worst ${worst} dB ($worst_f)")"
[ "$total" -gt 0 ] && [ "$total" = "$na" ] && [ "$total" = "$nb" ] \
  || { echo "✗ FAIL: compared $total frames, but ${A#$SW/} has $na PNGs and ${B#$SW/} has $nb"; exit 1; }
# PNG sequences are big (demo: ~560 MB for both runs); they are kept only when the check fails
if [ $diff = 0 ]; then echo "✓ PASS: identical across 1 and $wb workers"; rm -rf "$A" "$B"; exit 0; fi
python3 -c "import sys; sys.exit(0 if float('$worst') >= 45 else 1)" && { echo "✓ PASS: worst frame ≥ 45 dB"; rm -rf "$A" "$B"; exit 0; }
echo "✗ FAIL: a frame depends on render order (hidden state, Math.random, unloaded font, time-based cache)"
echo "  frames kept for inspection: ${A#$SW/} and ${B#$SW/}"; exit 1
