#!/usr/bin/env bash
# The intro film for README playback: eight 1080p chapters, each ≤ 9.6 MB (GitHub's free-plan video upload limit is
# 10 MB), cut at the film's section changes, with the corner mark; 0.25 s sound fades at the cuts, a picture fade-out only.
# Source: the CRF 16 master (out/final-master.mp4). usage: tools/chapters.sh <film dir> <out dir> ["2-… 3-…" (only these)]
set -euo pipefail
F=$1 O=$2; mkdir -p "$O"
S=$(cd "$(dirname "$0")" && pwd)
M="$F/out/final-master.mp4"
# name start end (film seconds, the 150.5 s cut)
CH=("1-opening 0 19.0" "2-request-router-types 19.0 42.5" "3-docs-tools-engines 42.5 56.75" "4-how-it-works-gates 56.75 67.75" "5-self-review-final-cut 67.75 87.5" "6-styles-sound-cases 87.5 111.5" "7-proof-hall 111.5 133.25" "8-this-film-too 133.25 150.5")
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
ONLY=${3:-}
for c in "${CH[@]}"; do
  [ -n "$ONLY" ] && ! echo " $ONLY " | grep -q " ${c%% *} " && continue
  set -- $c; n=$1 a=$2 b=$3; d=$(python3 -c "print(round($b - $a, 3))")
  fi=""  # no picture fade-in: frame 0 is the player's thumbnail on GitHub (no poster), so it must not be black
  fo="fade=t=out:st=$(python3 -c "print(round($d - 0.25, 3))"):d=0.25"
  afi=$( [ "$a" = "0" ] && echo "" || echo "afade=t=in:st=0:d=0.25," ); afo="afade=t=out:st=$(python3 -c "print(round($d - 0.25, 3))"):d=0.25"
  [ "$b" = "150.5" ] && { fo="null"; afo="anull"; }
  # cut (frame-accurate, lossless-ish intermediate) with the fades, then the mark and the size-targeted encode
  ffmpeg -v error -y -ss "$a" -t "$d" -i "$M" -vf "${fi}${fo}" -af "${afi}${afo}" -c:v libx264 -crf 10 -preset fast -pix_fmt yuv420p -c:a aac -b:a 192k "$tmp/$n.mp4"
  bash "$S/watermark.sh" "$tmp/$n.mp4" "$O/intro-$n.mp4" 9.6
done
