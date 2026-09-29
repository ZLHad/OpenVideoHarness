#!/usr/bin/env bash
# Rebuild assets/clips/00–03.mp4: silent 30 fps proxies of showcase 00–03, short GOP so HyperFrames seeks fast.
# 01 is 24 fps: the fps filter repeats frames (no interpolation). Re-encoded proxies match the originals within
# encoding tolerance, not bit for bit, so a re-render's screen frames can differ very slightly from media/final.mp4.
set -euo pipefail
cd "$(dirname "$0")/.." && mkdir -p assets/clips
mk() { ffmpeg -v error -y -i "../$1/media/final.mp4" -an -vf "fps=30,scale=$2:flags=lanczos,format=yuv420p" \
         -c:v libx264 -crf 18 -g 15 -keyint_min 15 -sc_threshold 0 -movflags +faststart "assets/clips/$3.mp4"
       echo "ok  assets/clips/$3.mp4"; }
mk 00-promo-launch-film    1280:720 00
mk 01-handdrawn-clawd-leaf 1280:720 01
mk 02-short-leo-doppler    720:1280 02
mk 03-math-fourier         1280:720 03
