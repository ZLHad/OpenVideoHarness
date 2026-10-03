#!/usr/bin/env bash
# Download the showcase and style-gallery videos from the GitHub release "media" to the paths the build scripts and
# READMEs use (tools/media.txt lists them; git doesn't keep videos, so a clone stays small). Files already present with
# the right checksum are skipped.
# usage: tools/fetch_media.sh [word…]      (run from anywhere; words filter the paths, e.g. "04-intro" or "styles")
set -euo pipefail
cd "$(dirname "$0")/.."
BASE=${VH_MEDIA_URL:-https://github.com/ZLHad/OpenVideoHarness/releases/download/media}
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
n=0
while read -r path asset sum; do
  case "$path" in ''|'#'*) continue ;; esac
  if [ $# -gt 0 ]; then hit=0; for w in "$@"; do case "$path" in *"$w"*) hit=1 ;; esac; done; [ $hit = 1 ] || continue; fi
  if [ -f "$path" ] && [ "$(sha "$path")" = "$sum" ]; then echo "ok    $path"; continue; fi
  mkdir -p "$(dirname "$path")"
  echo "fetch $path  ←  $asset"
  curl -fL --retry 3 --progress-bar -o "$path.part" "$BASE/$asset"
  got=$(sha "$path.part")
  [ "$got" = "$sum" ] || { rm -f "$path.part"; echo "checksum mismatch for $asset (got $got)" >&2; exit 1; }
  mv "$path.part" "$path"; n=$((n + 1))
done < tools/media.txt
echo "$n downloaded"
