#!/usr/bin/env bash
# render.sh — render one style swatch (5 s, 30 fps, 1920×1080 canvas) with the pinned HyperFrames, then
# write styles/<slug>/media/swatch.mp4 (1280×720 H.264, ≤ 1.5 MB) and media/poster.jpg (t = 3.0 s, ≤ 200 KB).
#
#   styles/_swatch/render.sh <slug> [--draft] [--workers N] [--hud] [--png] [--stage-only] [--timeout S]
#
#   <slug>        a folder styles/<slug>/ with swatch.js + tokens.json, or a built-in: demo | catalog | fontprobe,
#                 or a path containing "/" to a scene folder anywhere (slug = its basename; media/ goes inside it)
#   --draft       HyperFrames --quality draft (faster, softer); outputs go to out/<slug>/media, never over styles/<slug>/media
#   --workers N   parallel Chrome workers (default 2; 1 when another `hyperframes render` is already running);
#                 the count only changes the speed, the frames are byte-identical
#   --hud         burn a t / frame readout into the corner (for checking only; never ship it)
#   --png         ONLY render a lossless PNG sequence to styles/_swatch/out/<slug>/png-w<N>/ (see determinism.sh)
#   --stage-only  build the stage (see README) and print how to snapshot / preview it; no render
#   --timeout S   kill the render after S seconds (default 300 draft / 600 final); a render whose log stays
#                 silent for SWATCH_STALL seconds (default 120) is treated as hung and killed too
#
# Built-in scenes (demo, catalog, fontprobe) write to styles/_swatch/out/<slug>/media/ instead of styles/<slug>/media/.
# HyperFrames runs with --no-browser-gpu (SwiftShader WebGL, 2D canvas and compositing on the CPU), its deterministic
# mode: on the GPU, Chrome rasterised text edges differently from process to process (a few dozen pixels, one level),
# x264 turned that into a different mp4 and poster on every run, and 1- and 2-worker renders took different capture
# paths. Frames are now the same bytes at any worker count and on every run (README.md, "确定性").
# Needs: node ≥ 22, ffmpeg/ffprobe, uv (contact sheet + music). Run `npm ci` in styles/_swatch once.
set -euo pipefail
SW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SW/../.." && pwd)"
HF="$SW/node_modules/.bin/hyperframes"
FPS=30; DUR=5; FRAMES=150; POSTER_FRAME=90
MP4_LIMIT=1500000; JPG_LIMIT=200000          # bytes (decimal MB/KB, so both readings of "1.5 MB" hold)
ok=$'\033[32m✓\033[0m'; no=$'\033[31m✗\033[0m'; wa=$'\033[33m!\033[0m'
die() { echo "$no $*" >&2; exit 1; }
fsize() { wc -c < "$1" | tr -d ' '; }         # bytes; `stat` flags differ between BSD and GNU

slug=""; draft=0; workers=""; hud=false; png=0; stage_only=0; timeout=""
while [ $# -gt 0 ]; do
  case "$1" in
    --draft) draft=1 ;; --hud) hud=true ;; --png) png=1 ;; --stage-only) stage_only=1 ;;
    --workers) workers=${2:?}; shift ;; --workers=*) workers=${1#*=} ;;
    --timeout) timeout=${2:?}; shift ;; --timeout=*) timeout=${1#*=} ;;
    -h|--help) sed -n '2,23p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) die "unknown option $1" ;;
    *) [ -z "$slug" ] && slug=$1 || die "one slug at a time" ;;
  esac; shift
done
[ -n "$slug" ] || die "usage: styles/_swatch/render.sh <slug> [--draft] [--workers N] [--hud] [--png] [--stage-only]"
SRCDIR=""
case "$slug" in */*) [ -d "$slug" ] || die "no such directory: $slug"; SRCDIR="$(cd "$slug" && pwd)"; slug=$(basename "$SRCDIR") ;; esac
[[ "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]] || die "slug must be lowercase letters, digits and dashes: $slug"
[ -x "$HF" ] || die "HyperFrames not installed: (cd styles/_swatch && npm ci)"
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || die "ffmpeg/ffprobe not found"
[ "$(uname)" = Darwin ] || echo "$wa swatch fonts are macOS system fonts (fonts.css local() faces): on $(uname) they fall back, so this output will differ from the published media (see the font table in styles/_swatch/README.md, or render the fontprobe built-in)"

builtin=0; [ -z "$SRCDIR" ] && case "$slug" in demo|catalog|fontprobe) builtin=1 ;; esac
if [ $builtin = 1 ]; then SRC="$SW/$slug"; MEDIA="$SW/out/$slug/media"
elif [ -n "$SRCDIR" ]; then SRC="$SRCDIR"; MEDIA="$SRC/media"        # a scene folder anywhere (drafts, tests)
else SRC="$ROOT/styles/$slug"; MEDIA="$SRC/media"; fi
# drafts never overwrite a shipped swatch: they go to out/<slug>/media (final renders, without --draft, write styles/<slug>/media)
[ $draft = 1 ] && [ $builtin = 0 ] && [ -z "$SRCDIR" ] && MEDIA="$SW/out/$slug/media"
[ -f "$SRC/swatch.js" ] || die "missing $SRC/swatch.js"
[ -f "$SRC/tokens.json" ] || die "missing $SRC/tokens.json"
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SRC/tokens.json" 2>/dev/null || die "$SRC/tokens.json is not valid JSON"
# (plain `node --check file.js` misses ESM syntax errors in Node 22; stdin + --input-type=module does not)
if ! err=$(node --input-type=module --check < "$SRC/swatch.js" 2>&1); then
  echo "$err" | grep -E "^\[stdin\]:|SyntaxError" | head -3 >&2; die "syntax error in $SRC/swatch.js"; fi

OUT="$SW/out/$slug"; STAGE="$SW/out/stage/$slug"; LOCK="$SW/out/stage/$slug.lock"
mkdir -p "$SW/out/stage" "$OUT" "$MEDIA"
mkdir "$LOCK" 2>/dev/null || die "another render of '$slug' holds $LOCK (remove it if that render is dead)"
HFPID=""
cleanup() {
  [ -n "$HFPID" ] && kill -0 "$HFPID" 2>/dev/null && { kill -TERM -- "-$HFPID" 2>/dev/null || kill -TERM "$HFPID" 2>/dev/null || true; }
  rmdir "$LOCK" 2>/dev/null || true
}
trap cleanup EXIT; trap 'exit 130' INT TERM

# ── stage: a throwaway HyperFrames project root with exactly one composition. The shell files are copied
#    from styles/_swatch/, the style folder goes to scenes/<slug>/, and the `style` variable default is set
#    to <slug> so `hyperframes snapshot|preview` on the stage (which take no --variables) show this style.
rm -rf "$STAGE"; mkdir -p "$STAGE"
for f in index.html boot.js lib.js fonts.css hyperframes.json meta.json package.json; do cp "$SW/$f" "$STAGE/"; done
for d in demo catalog fontprobe; do [ -d "$SW/$d" ] && cp -R "$SW/$d" "$STAGE/"; done
[ -d "$SW/vendor" ] && cp -R "$SW/vendor" "$STAGE/"
if [ $builtin = 0 ]; then
  mkdir -p "$STAGE/scenes"
  rsync -a --exclude media --exclude '*.md' --exclude '.DS_Store' "$SRC/" "$STAGE/scenes/$slug/"
  if find "$STAGE/scenes/$slug" -name '*.html' | grep -q .; then die "styles/$slug/ must not contain .html files (one composition per root)"; fi
fi
python3 - "$STAGE/index.html" "$slug" <<'PY' || die "could not set the style default in the staged index.html"
import html, json, re, sys
p, slug = sys.argv[1], sys.argv[2]; s = open(p).read()
m = re.search(r"data-composition-variables='([^']*)'", s)
v = json.loads(html.unescape(m.group(1)))
for d in v:
    if d["id"] == "style": d["default"] = slug
open(p, "w").write(s[:m.start(1)] + json.dumps(v, ensure_ascii=False, separators=(",", ":")) + s[m.end(1):])
PY
if [ $stage_only = 1 ]; then
  echo "$ok stage ready: ${STAGE#$ROOT/}"
  echo "   snapshot: HYPERFRAMES_SKIP_SKILLS=1 $HF snapshot ${STAGE#$ROOT/} --at 0.4,1.7,3.0,4.6 --output ${OUT#$ROOT/}/snapshots"
  echo "   preview : HYPERFRAMES_SKIP_SKILLS=1 $HF preview ${STAGE#$ROOT/}"
  echo "   (fonts: judge them on render.sh output, not snapshots)"
  exit 0
fi

# ── render with a watchdog
if [ -z "$workers" ]; then
  if pgrep -f "hyperframes render" >/dev/null 2>&1; then workers=1; echo "$wa another hyperframes render is running → --workers 1"; else workers=2; fi
fi
[ -n "$timeout" ] || { [ $draft = 1 ] && timeout=300 || timeout=600; }
STALL=${SWATCH_STALL:-120}
quality=$([ $draft = 1 ] && echo draft || echo delivery)
HFMP4="$OUT/hf.mp4"; LOG="$OUT/render.log"
rm -f "$HFMP4" "$LOG"
vars="{\"style\":\"$slug\",\"hud\":$hud}"

run_hf() { # $@ = extra render args; runs in its own process group so a timeout kills Chrome too
  local rc=0 t0 now size last=-1 lastchg
  set -m
  # --no-browser-gpu: every frame is a pure function of t only when nothing in the pipeline depends on GPU state (header)
  (cd "$STAGE" && exec env HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1 "$HF" render . --fps $FPS --workers "$workers" \
     --no-browser-gpu --variables "$vars" "$@") >>"$LOG" 2>&1 &
  HFPID=$!
  set +m
  t0=$(date +%s); lastchg=$t0
  while kill -0 "$HFPID" 2>/dev/null; do
    sleep 1; now=$(date +%s); size=$(fsize "$LOG" 2>/dev/null || echo 0)
    [ "$size" != "$last" ] && { last=$size; lastchg=$now; }
    if [ $((now - t0)) -gt "$timeout" ]; then
      kill -TERM -- "-$HFPID" 2>/dev/null || true; sleep 3; kill -KILL -- "-$HFPID" 2>/dev/null || true
      echo "$no render timed out after ${timeout}s (log: ${LOG#$ROOT/})"; tail -5 "$LOG"; HFPID=""; return 124; fi
    if [ $((now - lastchg)) -gt "$STALL" ]; then
      kill -TERM -- "-$HFPID" 2>/dev/null || true; sleep 3; kill -KILL -- "-$HFPID" 2>/dev/null || true
      echo "$no render log silent for ${STALL}s: treated as hung (CDN fetch? infinite loop in renderAt?)"; tail -5 "$LOG"; HFPID=""; return 125; fi
  done
  wait "$HFPID" || rc=$?
  HFPID=""
  return $rc
}

T0=$(date +%s)
if [ $png = 1 ]; then       # lossless frames only (determinism checks); no mp4 / poster
  PNGDIR="$OUT/png-w$workers"; rm -rf "$PNGDIR"
  echo "→ PNG sequence '$slug' (${workers} worker(s)) → ${PNGDIR#$ROOT/}"
  rc=0; run_hf --format png-sequence --output "$PNGDIR" || rc=$?
  [ $rc = 0 ] || { echo "$no png-sequence render failed ($rc)"; tail -15 "$LOG"; exit 1; }
  np=$(find "$PNGDIR" -name '*.png' | wc -l | tr -d ' ')
  [ "$np" = "$FRAMES" ] || die "$np PNG frames, expected $FRAMES"
  echo "$ok $np frames in $(( $(date +%s) - T0 ))s"; exit 0
fi
echo "→ rendering '$slug' (${quality}, ${workers} worker(s), timeout ${timeout}s)"
rc=0; run_hf --quality "$quality" --output "$HFMP4" || rc=$?
T1=$(date +%s)
[ $rc = 0 ] || { echo "$no hyperframes exited with $rc — last lines of ${LOG#$ROOT/}:"; tail -15 "$LOG"; exit 1; }
[ -s "$HFMP4" ] || die "hyperframes exited 0 but wrote no $HFMP4"

# ── checks: frame count, drawn canvas, error card, frozen output
n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$HFMP4")
wh=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$HFMP4")
[ "$n" = "$FRAMES" ] || die "frame count $n ≠ $FRAMES in ${HFMP4#$ROOT/}"
[ "$wh" = "1920x1080" ] || die "render is $wh, expected 1920x1080"
fail=0; drew=0; sums=""
for f in 12 51 90 138; do     # t = 0.4 / 1.7 / 3.0 / 4.6 — one frame per content-spec segment
  crop=""; [ "$hud" = true ] && crop="crop=iw:ih-100:0:0,"      # keep the HUD strip out of the "did it draw" stats
  st=$(ffmpeg -v error -i "$HFMP4" -vf "select=eq(n\\,$f),${crop}signalstats,metadata=mode=print:file=-" -frames:v 1 -f null - 2>/dev/null | tr '\n' ' ')
  get() { echo "$st" | sed -n "s/.*lavfi.signalstats.$1=\([0-9.]*\).*/\1/p"; }
  yavg=$(get YAVG); ymin=$(get YMIN); ymax=$(get YMAX); uavg=$(get UAVG); vavg=$(get VAVG)
  [ -n "$yavg" ] || { echo "$no could not read frame $f"; fail=1; continue; }
  range=$(python3 -c "print(int(float('$ymax')-float('$ymin')))")
  printf "   frame %3d (t=%.1f)  YAVG %5.1f  Y range %3d  U %5.1f  V %5.1f\n" "$f" "$(python3 -c "print($f/$FPS)")" "$yavg" "$range" "$uavg" "$vavg"
  [ "$range" -ge 24 ] && drew=1
  if python3 -c "import sys; sys.exit(0 if float('$uavg')>175 and float('$vavg')>185 else 1)"; then
    # HyperFrames doesn't always forward console.error into the log, so save the card itself: its text is the stack
    ffmpeg -v error -y -i "$HFMP4" -vf "select=eq(n\\,$f)" -frames:v 1 "$OUT/error-frame-$f.png" 2>/dev/null
    grep -h "\[swatch\]" "$LOG" 2>/dev/null | head -5
    echo "$no frame $f is the magenta SWATCH ERROR card: the scene threw — read the stack on ${OUT#$ROOT/}/error-frame-$f.png"; fail=1; fi
  sums="$sums $(ffmpeg -v error -i "$HFMP4" -vf "select=eq(n\\,$f)" -frames:v 1 -f md5 - 2>/dev/null)"
done
[ $drew = 1 ] || { echo "$no every sampled frame is flat: the canvas never drew"; fail=1; }
[ "$(echo $sums | tr ' ' '\n' | sort -u | wc -l | tr -d ' ')" -gt 1 ] || { echo "$no sampled frames are identical: output is frozen (renderAt not called per seek?)"; fail=1; }
grep -h "\[swatch\]" "$LOG" 2>/dev/null | sort -u | head -10 | sed 's/^/   log: /' || true
[ $fail = 0 ] || exit 1
echo "$ok ${n} frames at ${wh}, canvas drew, no error card ($((T1 - T0))s render)"

# ── optional score → 5 s music bed, optional events.json → foley placed on the frame of each action
AUDIO=""; MIXARGS=()
if [ $builtin = 0 ] && [ -f "$SRC/score.json" ]; then   # (SRC = styles/<slug> or the given folder)
  echo "→ music from ${SRC#$ROOT/}/score.json"
  "$ROOT/bin/vh" music "$SRC/score.json" "$OUT/music_raw.wav" >/dev/null
  ffmpeg -v error -y -i "$OUT/music_raw.wav" -af "atrim=0:$DUR,afade=t=out:st=$(python3 -c "print($DUR-0.45)"):d=0.45,apad=whole_dur=$DUR" "$OUT/music5.wav"
  MIXARGS+=(music="$OUT/music5.wav" music_db=0)
fi
if [ $builtin = 0 ] && [ -f "$SRC/events.json" ]; then  # [{"t", "sfx", "gain_db", "pan", "dist"}]; own WAVs relative to the style folder
  echo "→ foley from ${SRC#$ROOT/}/events.json"
  "$ROOT/bin/vh" sfx lib "$OUT/sfxlib" >/dev/null       # rebuilt each time, so library fixes always reach the swatch
  (cd "$SRC" && "$ROOT/bin/vh" sfx place events.json "$OUT/sfx_raw.wav" "$DUR" --lib "$OUT/sfxlib" >/dev/null)
  # same 0.45 s fade as the score, so a long SFX that runs past the end isn't cut off with a click at 5.0 s
  ffmpeg -v error -y -i "$OUT/sfx_raw.wav" -af "atrim=0:$DUR,afade=t=out:st=$(python3 -c "print($DUR-0.45)"):d=0.45,apad=whole_dur=$DUR" "$OUT/sfx.wav"
  MIXARGS+=(sfx="$OUT/sfx.wav" sfx_db=-3)
fi
if [ ${#MIXARGS[@]} -gt 0 ]; then
  "$ROOT/bin/vh" mix "$OUT/music.wav" "${MIXARGS[@]}" duck=off >/dev/null   # no ducker: a 5 s clip has no voice to make way for
  AUDIO="$OUT/music.wav"
fi

# ── swatch.mp4: 1280×720, H.264 High, yuv420p, faststart; CRF climbs until it fits the size cap.
#    -threads 1: x264's VBV rate control (-maxrate/-bufsize) is not repeatable with frame threads — four encodes of the
#    same input spanned 1 493 473–1 503 291 B around the 1 500 000 B cap, flipping halftone-comic between CRF 24 and 26.
#    One thread gives the same bytes every time and costs about 3 s per pass at 720p.
MP4="$MEDIA/swatch.mp4"; TMP="$OUT/swatch.tmp.mp4"
for crf in 18 20 22 24 26 28 30 32 34; do
  if [ -n "$AUDIO" ]; then
    ffmpeg -v error -y -i "$HFMP4" -i "$AUDIO" -map 0:v:0 -map 1:a:0 -vf "scale=1280:720:flags=lanczos,format=yuv420p" \
      -c:v libx264 -preset slow -profile:v high -crf $crf -maxrate 2600k -bufsize 5200k -g 60 -r $FPS -threads 1 \
      -c:a aac -b:a 128k -ac 2 -t $DUR -movflags +faststart "$TMP"
  else
    ffmpeg -v error -y -i "$HFMP4" -vf "scale=1280:720:flags=lanczos,format=yuv420p" \
      -c:v libx264 -preset slow -profile:v high -crf $crf -maxrate 2600k -bufsize 5200k -g 60 -r $FPS -threads 1 \
      -an -t $DUR -movflags +faststart "$TMP"
  fi
  sz=$(fsize "$TMP"); [ "$sz" -le $MP4_LIMIT ] && break
done
[ "$sz" -le $MP4_LIMIT ] || die "swatch.mp4 is still $sz bytes at CRF $crf: reduce full-frame grain/noise"
mv "$TMP" "$MP4"
echo "$ok ${MP4#$ROOT/}  $(python3 -c "print(f'{$sz/1e6:.2f} MB')")  (crf $crf$([ -f "$SRC/score.json" ] && [ $builtin = 0 ] && echo ', +music')$([ -f "$SRC/events.json" ] && [ $builtin = 0 ] && echo ', +foley')$([ -z "$AUDIO" ] && echo ', silent'))"

# ── audio QA on the shipped file: silence / dropouts / pumping over the whole clip (the fade-out tail excluded).
#    Without the beat map, `qa scan` would only look at ~1.0–2.2 s of a 5 s clip, so always pass it.
if [ -n "$AUDIO" ]; then
  QA_ARGS=(); [ -f "$OUT/music_raw.beats.json" ] && [ -f "$SRC/score.json" ] && QA_ARGS+=("$OUT/music_raw.beats.json")
  [ -f "$SRC/events.json" ] && QA_ARGS+=(--events "$SRC/events.json")   # foley onsets are designed, not clicks
  "$ROOT/bin/vh" qa scan "$MP4" "${QA_ARGS[@]}" --from 0.3 --to "$(python3 -c "print($DUR-0.5)")" > "$OUT/qa.txt" 2>&1 \
    && echo "$ok audio qa passed (${OUT#$ROOT/}/qa.txt)" \
    || die "audio qa failed — see ${OUT#$ROOT/}/qa.txt (typical fixes: a pad/sub bed under sparse bars, no hats-only sections)"
fi

# ── poster.jpg: frame 90 (t = 3.0 s) from the 1080p render, 1280×720, ≤ 200 KB
JPG="$MEDIA/poster.jpg"
for q in 2 3 4 5 6 7 8 10 12 15; do
  ffmpeg -v error -y -i "$HFMP4" -vf "select=eq(n\\,$POSTER_FRAME),scale=1280:720:flags=lanczos" -frames:v 1 -q:v $q "$JPG"
  psz=$(fsize "$JPG"); [ "$psz" -le $JPG_LIMIT ] && break
done
[ "$psz" -le $JPG_LIMIT ] || die "poster.jpg is still $psz bytes at q $q"
echo "$ok ${JPG#$ROOT/}  $((psz / 1000)) KB (q $q)"

# ── contact sheet for self-review (not shipped): 10 frames, t = 0.25 … 4.75
if command -v uv >/dev/null 2>&1 && uv run -q --with pillow python "$ROOT/tools/sheet.py" "$HFMP4" "$OUT/sheet.png" 5 2 384 >/dev/null 2>&1; then
  echo "$ok sheet ${OUT#$ROOT/}/sheet.png"
else
  ffmpeg -v error -y -i "$HFMP4" -vf "fps=2,scale=384:-1,tile=5x2" -frames:v 1 "$OUT/sheet.png" && echo "$ok sheet ${OUT#$ROOT/}/sheet.png (no timestamps)"
fi
echo "   total $(( $(date +%s) - T0 ))s · render log ${LOG#$ROOT/}"
