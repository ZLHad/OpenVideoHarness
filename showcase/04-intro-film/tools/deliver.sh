#!/usr/bin/env bash
# Final deliverables from the current source (run from the project root). v3 Phase B: 81.333 s, 2440 frames.
#   1. re-bake the self-reference sheets from the latest draft (two-pass)
#   2. master render (high) + grain-free render (GIF source)
#   3. audio: sfx → stereo mix → linear master (−14 LUFS) → cue check
#   4. mux (+ zh/en soft subtitles), web encode, GIF, poster, sheet, checks
set -euo pipefail
export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1
DRAFT=${1:?latest draft mp4 for the self-sheets}
B=../../bin/vh
FRAMES=2440
# render with a watchdog: a stalled render (e.g. a network hiccup while the page loads) fails loudly instead of hanging
verify() { # frame count + the 3D layer present at 4 moments
  local out=$1 n; n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$out")
  [ "$n" = "$FRAMES" ] || { echo "FAIL: $out has $n frames, expected $FRAMES" >&2; exit 1; }
  for ts in 1.5 30.2 45.2 79.0; do
    local y; y=$(ffmpeg -v error -ss "$ts" -i "$out" -frames:v 1 -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - | grep -o 'YAVG=[0-9.]*' | head -1 | cut -d= -f2)
    awk -v y="$y" 'BEGIN { exit !(y > 20) }' || { echo "FAIL: $out looks empty at ${ts}s (YAVG $y)" >&2; exit 1; }
  done
  echo "verified $out: $n frames, 3D layer present"
}
render() {
  local out=$1; shift
  if [ -n "${SKIP_RENDER:-}" ] && [ -f "$out" ]; then verify "$out"; return; fi
  npx hyperframes render "$@" --output "$out" > "$out.log" 2>&1 &
  local pid=$! t=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 5; t=$((t + 5))
    if [ "$t" -ge "${RENDER_TIMEOUT:-1500}" ]; then kill "$pid"; echo "FAIL: render timed out after ${t}s: $out" >&2; exit 1; fi
  done
  wait "$pid" || { echo "FAIL: render exited non-zero: $out" >&2; tail -5 "$out.log" >&2; exit 1; }
  grep -q "rendered in" "$out.log" || { echo "FAIL: render did not report completion: $out" >&2; exit 1; }
  verify "$out"
  grep "rendered in" "$out.log"
}
tools/self_sheets.sh "$DRAFT"
cp assets/tex/storyboard-sheet.png out/check/storyboard.png
npx hyperframes lint
# grain-free master (per-pixel grain made the master 1.2–1.5 GB even at CRF 17; see LESSONS.md)
render out/final-nograin.mp4 --quality high --fps 30 --workers 4 --variables '{"grain":0}' | tee out/final-render.log
# audio
$B sfx lib audio/sfx >/dev/null
$B sfx place audio/events.json audio/sfx.wav 81.3333 --lib audio/sfx
uv run -q python tools/mix_stereo.py audio/mix_raw.wav music=audio/music.wav sfx=audio/sfx.wav music_db=0 sfx_db=-2 duck=off lufs=off
tools/master.sh audio/mix_raw.wav audio/mix.wav
uv run -q --with librosa python tools/cuecheck_mix.py
python3 tools/captions_from_type.py
# mux + encodes
SRC=out/final-nograin.mp4; AF="[1:a]apad,atrim=0:81.3333333[a]"   # audio padded/trimmed to the exact 2440 frames
ffmpeg -v error -y -i $SRC -i audio/mix.wav -i audio/captions.zh.srt -i audio/captions.en.srt -filter_complex "$AF" -map 0:v -map "[a]" -map 2 -map 3 -c:v libx264 -preset slow -crf 16 -tune film -pix_fmt yuv420p -profile:v high -c:a aac -b:a 256k -c:s mov_text -metadata:s:s:0 language=chi -metadata:s:s:1 language=eng -movflags +faststart out/final.mp4
ffmpeg -v error -y -i $SRC -c:v libx264 -preset slow -b:v 1900k -maxrate 3000k -bufsize 6000k -pass 1 -passlogfile out/web2pass -an -f null /dev/null
ffmpeg -v error -y -i $SRC -i audio/mix.wav -i audio/captions.zh.srt -i audio/captions.en.srt -filter_complex "$AF" -map 0:v -map "[a]" -map 2 -map 3 -c:v libx264 -preset slow -b:v 1900k -maxrate 3000k -bufsize 6000k -pass 2 -passlogfile out/web2pass -pix_fmt yuv420p -c:a aac -b:a 128k -c:s mov_text -metadata:s:s:0 language=chi -metadata:s:s:1 language=eng -movflags +faststart out/final-web.mp4
# GIF: braam → name → architecture → the 8-type list (21.0–30.6 s)
ffmpeg -v error -y -ss 21.0 -t 9.6 -i $SRC -vf "fps=10,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" out/preview.gif
ffmpeg -v error -y -ss 80.9 -i out/final.mp4 -frames:v 1 -update 1 out/poster.png
rm -f out/sheet.png; $B sheet out/final.mp4 8 0.75 out/sheet.png
$B check out/final.mp4
ffprobe -v error -show_entries stream=codec_type,nb_frames,duration -of compact out/final.mp4
ls -la out/final.mp4 out/final-web.mp4 out/preview.gif out/poster.png out/sheet.png
