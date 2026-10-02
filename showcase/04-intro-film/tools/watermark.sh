#!/usr/bin/env bash
# README playback copies: a small "ZLHad/OpenVideoHarness" in the bottom-right corner, ≤ MAXMB (GitHub user-attachments).
# usage: watermark.sh <in.mp4> <out.mp4> [max MB = 9.6] [scale filter, e.g. scale=1280:-2] [x264 extra params]
set -euo pipefail
in=$1 out=$2 MAXMB=${3:-9.6} SC=${4:-} XP=${5:-}
FONT=${FONT:-/System/Library/Fonts/SFNSMono.ttf}   # macOS; elsewhere pass FONT=<a .ttf>
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$in")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$in")
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
if [ -n "$SC" ]; then OW=$(python3 -c "import sys; w=int(sys.argv[1]); print(w)" "$(echo "$SC" | sed -E 's/scale=([0-9]+):.*/\1/')"); OH=$(( H * OW / W / 2 * 2 )); else OW=$W OH=$H; fi
S=$(( (OW < OH ? OW : OH) )); FS=$(( S * 22 / 1000 )); [ $FS -lt 14 ] && FS=14; M=$(( S * 30 / 1000 ))
ABR=$(ffprobe -v error -select_streams a:0 -show_entries stream=bit_rate -of csv=p=0 "$in"); ABR=${ABR:-128000}
VBR=$(python3 -c "import sys; d,mb,a=map(float,sys.argv[1:]); print(int(min(9000, (mb*8e6/d - a)/1000*0.97)))" "$DUR" "$MAXMB" "$ABR")
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
# the mark as a PNG (this ffmpeg has no drawtext): white at 55 %, a soft dark shadow, SF Mono
uv run -q --no-project --with pillow python - "$FONT" "$FS" "$tmp/wm.png" <<'PYI'
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
font = ImageFont.truetype(sys.argv[1], int(sys.argv[2])); t = "ZLHad/OpenVideoHarness"
x0, y0, x1, y1 = font.getbbox(t); w, h = x1 - x0 + 8, y1 - y0 + 8
sh = Image.new("RGBA", (w, h)); ImageDraw.Draw(sh).text((4 - x0 + 1, 4 - y0 + 1), t, font=font, fill=(0, 0, 0, 115)); sh = sh.filter(ImageFilter.GaussianBlur(1))
im = Image.new("RGBA", (w, h)); ImageDraw.Draw(im).text((4 - x0, 4 - y0), t, font=font, fill=(255, 255, 255, 140))
Image.alpha_composite(sh, im).save(sys.argv[3])
PYI
VF="[0:v]${SC:+$SC,}null[b];[b][1:v]overlay=W-w-$M:H-h-$M:format=auto,format=yuv420p[v]"
CT="-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv"
X=""; [ -n "$XP" ] && X="-x264-params $XP"
ffmpeg -v error -y -i "$in" -i "$tmp/wm.png" -filter_complex "$VF" -map "[v]" -c:v libx264 -preset slow -b:v ${VBR}k -maxrate $(( VBR * 4 ))k -bufsize $(( VBR * 8 ))k $X -pass 1 -passlogfile "$tmp/p" -pix_fmt yuv420p $CT -an -f null /dev/null
ffmpeg -v error -y -i "$in" -i "$tmp/wm.png" -filter_complex "$VF" -map "[v]" -map 0:a:0 -c:v libx264 -preset slow -b:v ${VBR}k -maxrate $(( VBR * 4 ))k -bufsize $(( VBR * 8 ))k $X -pass 2 -passlogfile "$tmp/p" -pix_fmt yuv420p $CT -c:a copy -movflags +faststart "$out"
sz=$(wc -c < "$out" | tr -d " "); echo "$out  ${OW}x${OH}  ${DUR}s  video ${VBR}k  $(python3 -c "print(round($sz/1e6,2))") MB  watermark ${FS}px"
python3 -c "import sys; sys.exit(0 if $sz <= $MAXMB*1e6*1.02 else 1)" || { echo "too big: $sz" >&2; exit 1; }
