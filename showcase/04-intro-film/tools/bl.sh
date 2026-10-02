#!/usr/bin/env bash
# Run Blender for this project the way engines/blender.md and styles/_swatch/render.sh do: no inherited environment
# (env -i: no API keys), HOME and TMPDIR inside blender/out/.blender/, and on macOS inside sandbox-exec: no network,
# no lsopen / Apple events, writes only to blender/out/ and Blender's own folder in the per-user cache (Metal keeps its
# compiled kernels there). Metal crashes when the home folder is unreadable, so reads stay open (render.sh drafts do the same).
#
# usage: tools/bl.sh <blender args…>          e.g. tools/bl.sh -b --factory-startup --python blender/test.py -- …
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd -P)"          # the project
O="$P/blender/out"; mkdir -p "$O/.blender/home" "$O/.blender/tmp"
BL="$(command -v blender)"
sbq() { printf '"%s"' "$(printf '%s' "$1" | sed 's/[\\"]/\\&/g')"; }
C="$(cd "$(getconf DARWIN_USER_CACHE_DIR)" && pwd -P)"
SBX="$(mktemp -d "${TMPDIR:-/tmp}/vh-sandbox.XXXXXX")/blender.sb"
trap 'rm -rf "${SBX%/*}"' EXIT
{ echo '(version 1)'; echo '(allow default)'; echo '(deny network*)'; echo '(deny lsopen)'; echo '(deny appleevent-send)'
  echo '(deny file-write*)'
  echo "(allow file-write* (subpath $(sbq "$O")) (subpath $(sbq "$C/org.blenderfoundation.blender")) (literal \"/dev/null\") (literal \"/dev/dtracehelper\"))"
} > "$SBX"
cd "$P"
sandbox-exec -f "$SBX" env -i PATH="$PATH" HOME="$O/.blender/home" TMPDIR="$O/.blender/tmp/" LANG=en_US.UTF-8 PYTHONDONTWRITEBYTECODE=1 \
  "$BL" "$@" </dev/null
