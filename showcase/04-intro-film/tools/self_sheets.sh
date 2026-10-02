#!/usr/bin/env bash
# Two-pass self-reference: bake this film's OWN frames (from a draft render) into the texture the film shows behind
# "This film, too.": assets/tex/self-sheet.png (60 evenly spaced frames, 10×6).
# (The gates show the request's own artifacts, showcase 02's: tools/request_tex.py.)
# usage: tools/self_sheets.sh out/draftN.mp4        (run from the film folder; deterministic)
set -euo pipefail
V=${1:?draft mp4}
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
for i in $(seq 0 59); do t=$(python3 -c "print(round(($i+0.5)*$D/60,3))"); ffmpeg -v error -y -ss "$t" -i "$V" -frames:v 1 -vf scale=384:216 "$T/s$(printf %02d $i).png"; done
ffmpeg -v error -y -framerate 1 -i "$T/s%02d.png" -vf tile=10x6 -frames:v 1 assets/tex/self-sheet.png
echo "baked from $V: self-sheet.png"
