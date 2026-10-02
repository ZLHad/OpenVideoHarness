#!/usr/bin/env bash
# Render frames [a, b] of blender/galaxy.py in chunks of 30 (a fresh Blender per chunk), resumable; extra args go to galaxy.py.
# usage: tools/bl_render.sh <first> <last> <out dir under blender/out> [galaxy.py args…]
set -euo pipefail
cd "$(dirname "$0")/.."
a=$1 b=$2 out=$3; shift 3
for ((s = a; s <= b; s += 30)); do
  e=$(( s + 29 < b ? s + 29 : b ))
  list=$(seq -s, "$s" "$e" | sed "s/,*$//")
  t0=$(date +%s)
  tools/bl.sh -b --factory-startup --python-exit-code 1 --python blender/galaxy.py -- --frames "$list" --out "blender/out/$out" --resume "$@" \
    2>&1 | grep -E "\[galaxy\] frame|Error|Traceback" || true
  echo "[bl_render] frames ${s}-${e} done in $(( $(date +%s) - t0 )) s"
done
echo "[bl_render] all done: $(ls blender/out/$out/*.png | wc -l) frames"
