#!/usr/bin/env bash
# Review evidence for a draft: strips on camera moves / type slams (10 fps) and full frames for type crops.
set -euo pipefail
V=${1:?video}; O=${2:-out/check/review}; mkdir -p "$O"
while read -r t d name; do
  n=$(python3 -c "print(int(round($d*10)))")
  ffmpeg -nostdin -v error -y -ss "$t" -t "$d" -i "$V" -vf "fps=10,scale=384:-1,tile=${n}x1" -frames:v 1 -update 1 "$O/strip-$name.png"
done <<'L'
5.0 0.8 reveal
10.2 0.8 cardflythrough
16.0 0.8 pushthroughscreen
21.1 0.8 braam
23.9 0.9 ringstoarch
29.8 1.0 typeslist-whip
34.4 1.4 portaldive
38.5 0.8 gate1stamp
41.2 0.9 gate2stamp
42.5 1.8 loopfails
46.5 1.8 pass-gate3-final
48.9 0.9 finaltofeatures
57.0 0.8 starburst
59.8 0.8 hallentry
75.8 0.8 titlehit
L
for t in 25.9 30.3 32.9 34.9 36.8 43.9 45.4 48.9 50.9 53.4 56.4 59.0 61.4 72.9 75.1 80.9; do ffmpeg -v error -y -ss "$t" -i "$V" -frames:v 1 -update 1 "$O/frame-$t.jpg"; done
ls "$O" | wc -l
