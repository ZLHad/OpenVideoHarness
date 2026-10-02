#!/usr/bin/env bash
# Rebuild the film's soundtrack from source:
#   music  the opening sketch (audio/sketch.json, 120 BPM; bin/vh music) for 0–29 s, its bar 11 (20–22 s) played four
#          times for the terminal's hold (js/tmap.js: +6 s), then the body score (audio/score.json, 80 BPM, D minor, bars
#          stretched for the reads' holds; audio/score_engine.py) from its 27.0 s mark (bar 10), joined at 29.0 s (faded in
#          over the 0.15 s before)
#   SFX    audio/events.json (124 events, the 21 built-ins of bin/vh sfx lib)
#   mix    bin/vh mix profile=promo → −14 LUFS; then bin/vh qa (the gate)
#   tools/build_audio.sh        → audio/music.wav, audio/mix.wav, audio/stems/, out/qa.txt
# audio/make_sketch.py wrote audio/sketch.json; tools/retime.py wrote audio/score.json and audio/events.json.
# Needs uv, ffmpeg and the repo's bin/vh. O= sets the output folder (default audio), VH= the path to bin/vh.
set -euo pipefail
cd "$(dirname "$0")/.."
VH=${VH:-../../bin/vh} A=audio O=${O:-audio} DUR=150.5 REP=3 JOIN=29.0   # REP: extra plays of the sketch's bar 11
mkdir -p out "$O"; tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
"$VH" music $A/sketch.json "$tmp/sketch.wav" >/dev/null
uv run -q --no-project --with numpy --with scipy python $A/score_engine.py $A/score.json "$tmp/body.wav" >/dev/null
# the sketch: 0–22 s, bar 11 (20–22 s) REP more times, 22–23 s; 10 ms crossfades on the bar lines; out over the last 0.4 s
fc="[0:a]atrim=0:22.01,asetpts=PTS-STARTPTS[s0]"; prev=s0
for i in $(seq 1 $REP); do fc="$fc;[0:a]atrim=20:22.01,asetpts=PTS-STARTPTS[r$i];[$prev][r$i]acrossfade=d=0.01:c1=tri:c2=tri[j$i]"; prev=j$i; done
fc="$fc;[0:a]atrim=22:23,asetpts=PTS-STARTPTS[e];[$prev][e]acrossfade=d=0.01:c1=tri:c2=tri,afade=t=out:st=$(python3 -c "print($JOIN - 0.4)"):d=0.4"
ffmpeg -v error -y -i "$tmp/sketch.wav" -filter_complex "$fc" -ar 48000 -ac 2 "$tmp/m1.wav"
ffmpeg -v error -y -ss 26.85 -i "$tmp/body.wav" -af "afade=t=in:st=0:d=0.15" -ar 48000 -ac 2 "$tmp/m2.wav"   # 0.15 s under the sketch's tail: no gap at the join
ffmpeg -v error -y -i "$tmp/m1.wav" -i "$tmp/m2.wav" -filter_complex "[1:a]adelay=$(python3 -c "print(int(($JOIN - 0.15) * 1000))")|$(python3 -c "print(int(($JOIN - 0.15) * 1000))")[b];[0:a][b]amix=inputs=2:duration=longest:normalize=0" \
  -t $DUR -c:a pcm_s24le "$O/music.wav"
"$VH" sfx lib "$O/sfxlib" >/dev/null
"$VH" mix "$O/mix.wav" profile=promo music="$O/music.wav" events="$O/events.json" lib="$O/sfxlib" dur=$DUR fade=0.6 stems="$O/stems" | tail -1
"$VH" qa "$O/mix.wav" - "$O/events.json" --lib "$O/sfxlib" --stems "$O/stems" --to $(python3 -c "print($DUR - 0.6)") --out out/qa.txt | tail -1
