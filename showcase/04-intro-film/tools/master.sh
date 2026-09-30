#!/usr/bin/env bash
# Linear master to -14 LUFS integrated with a true-peak ceiling (keeps the score's dynamics; no dynamic loudnorm).
# usage: tools/master.sh audio/mix_raw.wav audio/mix.wav
set -euo pipefail
IN=$1 OUT=$2
meas() { ffmpeg -hide_banner -nostats -i "$1" -af ebur128=peak=true -f null - 2>&1 | awk '/I:/{i=$2} /Peak:/{p=$2} END{print i, p}'; }
read -r I _ <<<"$(meas "$IN")"
G=$(python3 -c "print(round(-14.0 - $I, 2))")
ffmpeg -v error -y -i "$IN" -af "volume=${G}dB,alimiter=limit=0.79:attack=3:release=80:level=false:asc=1" -ar 48000 "$OUT"
read -r I2 _ <<<"$(meas "$OUT")"
G2=$(python3 -c "print(round(-14.0 - $I2, 2))")
ffmpeg -v error -y -i "$IN" -af "volume=$(python3 -c "print(round($G+$G2,2))")dB,alimiter=limit=0.79:attack=3:release=80:level=false:asc=1" -ar 48000 "$OUT"
echo "master: in ${I} LUFS -> gain $(python3 -c "print(round($G+$G2,2))") dB"; ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|LRA:|Peak:" | tail -3
