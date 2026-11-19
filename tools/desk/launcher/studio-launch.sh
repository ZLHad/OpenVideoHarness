#!/bin/sh
# OVH Studio's launcher on Linux: bin/vh studio --install-icon wrote it from tools/desk/launcher/studio-launch.sh, and the
# desktop entry runs it. What a click does is bin/vh studio's in the clone below, so a git pull needs no reinstall.
REPO=@@REPO@@
@@ENV@@
say() {   # a window if the desktop has a way to show one, and stderr (the session's log) either way
  printf '%s\n' "$1" >&2
  if command -v zenity >/dev/null 2>&1; then zenity --error --title="OVH Studio" --no-wrap --text="$1" 2>/dev/null
  elif command -v kdialog >/dev/null 2>&1; then kdialog --title "OVH Studio" --error "$1" 2>/dev/null
  elif command -v notify-send >/dev/null 2>&1; then notify-send "OVH Studio" "$1" 2>/dev/null
  elif command -v xmessage >/dev/null 2>&1; then xmessage -center "$1" 2>/dev/null; fi
}
if [ ! -x "$REPO/bin/vh" ]; then
  say "找不到 OpenVideoHarness 了（原来在 ${REPO}）。让 agent 在它现在的位置把 Studio 图标重新装一次（bin/vh studio --install-icon）。
OpenVideoHarness is no longer at ${REPO}. Ask your agent to put the Studio icon back from where it is now (bin/vh studio --install-icon)."
  exit 1
fi
out=$(cd "$REPO" && ./bin/vh studio --icon open 2>&1) || { say "Studio 没有打开 / Studio did not open:
$out"; exit 1; }
