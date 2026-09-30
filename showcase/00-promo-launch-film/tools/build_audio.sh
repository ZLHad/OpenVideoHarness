#!/usr/bin/env bash
# Rebuild this film's soundtrack from source: foley (tools/foley.py → audio/events.json + audio/sfx/), the score
# (audio/score.json → bin/vh music), the mix (−14 LUFS), the audio QA, and optionally the mux onto the picture.
#   showcase/00-promo-launch-film/tools/build_audio.sh                  → audio/mix.wav + audio/qa.txt
#   showcase/00-promo-launch-film/tools/build_audio.sh --mux out.mp4    … and out.mp4 = media/final.mp4's picture + the mix
# Needs uv, ffmpeg and the repo's bin/vh.
set -euo pipefail
FILM=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VH="$FILM/../../bin/vh"
A="$FILM/audio"
DUR=20 FPS=30 FADE=0.4          # the film's length; the score ends on a held chord, faded over the last FADE s
MUSIC_DB=-5                     # no narration here: the music is not ducked (bin/vh mix: duck=off)
PAD=3                           # every bus runs PAD s past the film and the mix is cut afterwards (see step 3)
out=""
while [ $# -gt 0 ]; do
  case $1 in
    --mux) out=${2:?--mux needs an output path}; shift ;;
    *) echo "usage: $0 [--mux out.mp4]" >&2; exit 2 ;;
  esac
  shift
done
calc() { python3 -c "print(round($1, 3))"; }
LEN=$(calc "$DUR + $PAD")

# 1 foley: custom sounds + event list, the 15 built-ins beside them, then one stereo SFX track
uv run -q --with numpy --with scipy python "$FILM/tools/foley.py"
"$VH" sfx lib "$A/sfx" >/dev/null
"$VH" sfx place "$A/events.json" "$A/sfx.wav" "$LEN" --lib "$A/sfx"
# 2 music: render the score (it starts with the film: no offset)
"$VH" music "$A/score.json" "$A/score.wav"
ffmpeg -v error -y -i "$A/score.wav" -af "atrim=0:$LEN" "$A/music.wav"
mv "$A/score.beats.json" "$A/music.beats.json"
rm -f "$A/score.wav"
# 3 mix at −14 LUFS (one static gain; a true-peak limiter only if needed), then cut to the film with a short fade.
#   The buses run PAD s past the film because with ffmpeg 8.0.1 the last ~1.2 s of a `bin/vh mix` output changed from
#   run to run (zeroed or garbled near the end of the streams); the film itself then comes out the same every time.
"$VH" mix "$A/mix.full.wav" music="$A/music.wav" sfx="$A/sfx.wav" music_db="$MUSIC_DB" duck=off
ffmpeg -v error -y -i "$A/mix.full.wav" -af "atrim=0:$DUR,afade=t=out:st=$(calc "$DUR - $FADE"):d=$FADE" "$A/mix.wav"
rm -f "$A/mix.full.wav"
# the cut moves the integrated loudness a little (the second past the film is gone): if it is now louder, one static
# gain brings it back to −14 (a cut never makes it much quieter; that case is only reported)
python3 - "$A/mix.wav" <<'PY'
import json, re, shutil, subprocess, sys
p = sys.argv[1]
def meter(f):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True, check=True).stderr
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S).group(0))
g = -14 - float(meter(p)["input_i"])
if g < -0.05:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", f"volume={g:.2f}dB", p + ".tmp.wav"], check=True)
    shutil.move(p + ".tmp.wav", p)
m = meter(p)
print(f"  mix.wav: {m['input_i']} LUFS, true peak {m['input_tp']} dBTP, LRA {m['input_lra']} LU")
PY
# 4 QA on the mix: silence, dropouts, pumping, clicks, and every cue (music hits + SFX events) within one frame
qa=0
"$VH" qa "$A/mix.wav" "$A/music.beats.json" "$A/events.json" --fps "$FPS" --to "$(calc "$DUR - 0.3")" --out "$A/qa.txt" || qa=$?
# 5 optional: the picture of media/final.mp4 (video stream only) + this mix
if [ -n "$out" ]; then "$VH" mux "$FILM/media/final.mp4" "$A/mix.wav" "$out"; fi
exit "$qa"
