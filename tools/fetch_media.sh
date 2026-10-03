#!/usr/bin/env bash
# Download the showcase and style-gallery videos from the GitHub release "media" to the paths the build scripts and
# READMEs use (tools/media.txt lists them; git doesn't keep videos, so a clone stays small). A file already present
# with the right checksum is skipped; one that differs (a local render, say) is kept unless you pass --force.
# usage: tools/fetch_media.sh [--force] [word…]      (run from anywhere; words filter the paths, e.g. "04-intro" or "styles")
# Exit status: 0 when every matching file is in place, 1 when a download or a checksum failed or nothing matched.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
BASE=${VH_MEDIA_URL:-https://github.com/ZLHad/OpenVideoHarness/releases/download/media}
force=0; if [ "${1:-}" = "--force" ]; then force=1; shift; fi
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
got_n=0 matched=0 failed=0
while read -r path asset sum || [ -n "${path:-}" ]; do
  case "${path:-}" in ''|'#'*) continue ;; esac
  if [ $# -gt 0 ]; then hit=0; for w in "$@"; do case "$path" in *"$w"*) hit=1 ;; esac; done; [ $hit = 1 ] || continue; fi
  matched=$((matched + 1))
  if [ -f "$path" ]; then
    if [ "$(sha "$path")" = "$sum" ]; then echo "ok    $path"; continue; fi
    if [ $force = 0 ]; then echo "keep  $path (it differs from the release copy, a local render perhaps; --force replaces it)"; continue; fi
  fi
  mkdir -p "$(dirname "$path")"
  echo "fetch $path  ←  $asset"
  if ! curl -fL --retry 3 --progress-bar -o "$path.part" "$BASE/$asset"; then
    rm -f "$path.part"; echo "could not download $asset from $BASE (is it in the release?)" >&2; failed=$((failed + 1)); continue
  fi
  got=$(sha "$path.part")
  if [ "$got" != "$sum" ]; then
    rm -f "$path.part"; echo "checksum mismatch for $asset: got $got, tools/media.txt says $sum" >&2; failed=$((failed + 1)); continue
  fi
  mv "$path.part" "$path"; got_n=$((got_n + 1))
done < tools/media.txt
if [ $matched = 0 ]; then echo "no path in tools/media.txt matches: $*" >&2; exit 1; fi
if [ $failed -gt 0 ]; then echo "$got_n downloaded, $failed failed" >&2; exit 1; fi
echo "$got_n downloaded"
