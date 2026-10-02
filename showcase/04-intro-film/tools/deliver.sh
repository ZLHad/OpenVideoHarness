#!/usr/bin/env bash
# Intro film v5 deliverables (run from the film folder): 150.5 s, 4515 frames (js/tmap.js).
#   1. the Blender plate: blender/out/final2/f_0000–0474.png → assets/plate.mp4 (0–15.8 s)
#   2. HyperFrames render, high quality (the plate + the WebGL grid and terminal + the body's world + DOM type)
#   3. audio: music (opening sketch 0–23 s + the body score from its bar 10) + SFX → bin/vh mix profile=promo → qa
#   4. mux, encodes (master, repo copy), the eight README chapters (tools/chapters.sh: 1080p, ≤ 9.6 MB, corner mark), poster, sheet, checks
set -euo pipefail
export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1
B=../../bin/vh; FRAMES=4515; DUR=150.5; mkdir -p out
PLATE=blender/out/final2
n=$(ls "$PLATE"/f_*.png | wc -l | tr -d ' '); [ "$n" -ge 475 ] || { echo "plate has $n frames, need 475" >&2; exit 1; }
ffmpeg -v error -y -framerate 30 -start_number 0 -i "$PLATE/f_%04d.png" -frames:v 475 \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv" \
  -c:v libx264 -crf 12 -preset slow -g 15 -movflags +faststart assets/plate.mp4
env -u GEMINI_API_KEY node_modules/.bin/hyperframes render . --quality high --workers 3 --variables '{"grain":0}' --output out/final-silent.mp4 > out/render.log 2>&1
grep -q "rendered in" out/render.log || { tail -5 out/render.log >&2; exit 1; }
nf=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 out/final-silent.mp4)
[ "$nf" = "$FRAMES" ] || { echo "FAIL: $nf frames, expected $FRAMES" >&2; exit 1; }
# audio: tools/build_audio.sh builds the mix from source (delete it to rebuild)
A=audio
[ -f $A/mix.wav ] || VH=$B O=$A bash tools/build_audio.sh   # music + SFX → mix → qa
$B qa $A/mix.wav - $A/events.json --lib $A/sfxlib --stems $A/stems --to 149.9 --out out/qa.txt | tail -2
CT="-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv"
AF="[1:a]apad,atrim=0:${DUR}[a]"
ffmpeg -v error -y -i out/final-silent.mp4 -i $A/mix.wav -filter_complex "$AF" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 16 -tune film -pix_fmt yuv420p $CT -c:a aac -b:a 256k -movflags +faststart out/final-master.mp4
# repo copy (≤ 50 MB): two-pass 2.5 Mbit/s; the Blender opening (frames 0–474: unbanded star noise) gets 3× the bits of the body
# through x264 zones (SSIM vs the master 0.82 → 0.88 in 0–16 s, body 0.95 → 0.93, same size)
Z1="-x264-params zones=0,474,b=3.0"
ffmpeg -v error -y -i out/final-silent.mp4 -c:v libx264 -preset slow -b:v 2500k -maxrate 16000k -bufsize 32000k $Z1 -pass 1 -passlogfile out/p2 -pix_fmt yuv420p $CT -an -f null /dev/null
ffmpeg -v error -y -i out/final-silent.mp4 -i $A/mix.wav -filter_complex "$AF" -map 0:v -map "[a]" -c:v libx264 -preset slow -b:v 2500k -maxrate 16000k -bufsize 32000k $Z1 -pass 2 -passlogfile out/p2 -pix_fmt yuv420p $CT -c:a aac -b:a 160k -movflags +faststart out/final.mp4
ffmpeg -v error -y -ss 16.2 -i out/final-master.mp4 -frames:v 1 out/poster.png
rm -f out/sheet.png; $B sheet out/final-master.mp4 8 0.5 out/sheet.png
uv run -q --no-project --with pillow python -c "from PIL import Image; Image.open('out/sheet.png').convert('RGB').save('out/sheet.jpg', quality=85, optimize=True)"   # the repo keeps the JPEG (the PNG is ~12 MB)
$B check out/final.mp4
# README players (GitHub user-attachments: ≤ 10 MB per video): eight 1080p chapters cut at the section changes,
# each with the small corner mark (tools/watermark.sh; SF Mono on macOS, FONT=<a .ttf> elsewhere); upload them by hand and put the links in the READMEs
bash tools/chapters.sh . out/chapters
ls -la out/final.mp4 out/final-master.mp4 out/poster.png out/sheet.jpg out/chapters/
