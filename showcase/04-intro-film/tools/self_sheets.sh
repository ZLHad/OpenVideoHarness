#!/usr/bin/env bash
# Two-pass self-reference: bake this film's OWN frames (from a draft render) into the textures the film shows.
#   gate ② art  → assets/tex/storyboard-sheet.png  (16 storyboard keyframes, 4×4, 16:9)
#   gate ③ art  → assets/tex/draft-sheet.png       (16 evenly spaced draft frames, 4×4, 16:9)
#   S6 monument → assets/tex/self-sheet.png        (60 evenly spaced frames, 10×6)
# usage: tools/self_sheets.sh out/draftN.mp4        (run from the project root; deterministic)
set -euo pipefail
V=${1:?draft mp4}
T=$(mktemp -d)
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
# storyboard keyframes: one per camera-path beat (seconds), see STORYBOARD.md
KEYS="1.8 4.4 7.0 12.0 14.8 18.0 20.4 23.0 27.8 31.0 33.6 39.6 41.9 47.2 52.0 67.8"
i=0; for k in $KEYS; do ffmpeg -v error -y -ss "$k" -i "$V" -frames:v 1 -vf scale=480:270 "$T/sb$(printf %02d $i).png"; i=$((i+1)); done
ffmpeg -v error -y -framerate 1 -i "$T/sb%02d.png" -vf tile=4x4 -frames:v 1 assets/tex/storyboard-sheet.png
for i in $(seq 0 15); do t=$(python3 -c "print(round(($i+0.5)*$D/16,3))"); ffmpeg -v error -y -ss "$t" -i "$V" -frames:v 1 -vf scale=480:270 "$T/d$(printf %02d $i).png"; done
ffmpeg -v error -y -framerate 1 -i "$T/d%02d.png" -vf tile=4x4 -frames:v 1 assets/tex/draft-sheet.png
for i in $(seq 0 59); do t=$(python3 -c "print(round(($i+0.5)*$D/60,3))"); ffmpeg -v error -y -ss "$t" -i "$V" -frames:v 1 -vf scale=384:216 "$T/s$(printf %02d $i).png"; done
ffmpeg -v error -y -framerate 1 -i "$T/s%02d.png" -vf tile=10x6 -frames:v 1 assets/tex/self-sheet.png
echo "baked from $V: storyboard-sheet.png draft-sheet.png self-sheet.png"
