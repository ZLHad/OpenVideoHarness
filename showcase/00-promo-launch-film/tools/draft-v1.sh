#!/usr/bin/env bash
# Rebuild "draft v1" — the state that beat 03 critiques — from the current source:
#   route beat with the draft-v1 table + 1.4x push (NOTES.md #3 FAIL), review beat with the draft-v1 stand-in sheet.
# Everything else is the current film. Output: out/draft-v1.mp4. Then:
#   bin/vh sheet <project>/out/draft-v1.mp4 6 1 <project>/assets/review-sheet.png
#   ffmpeg -i out/draft-v1.mp4 -vf "select=eq(n\,315),scale=960:540" -frames:v 1 assets/review-flagged.png
set -euo pipefail
cd "$(dirname "$0")/.."
HF=${HF:-"$PWD/node_modules/.bin/hyperframes"}
B=out/v1-build; rm -rf "$B"; mkdir -p "$B"
cp -R index.html hyperframes.json meta.json package.json compositions assets "$B/"
perl -pi -e 's/const DRAFT = "final";/const DRAFT = "v1";/' "$B/compositions/s-route.html" "$B/compositions/s-review.html"
grep -q 'const DRAFT = "v1"' "$B/compositions/s-route.html" "$B/compositions/s-review.html"
( cd "$B" && HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1 HYPERFRAMES_NO_TELEMETRY=1 "$HF" render --quality draft --output ../draft-v1.mp4 )
rm -rf "$B"
