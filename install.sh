#!/usr/bin/env bash
# OpenVideoHarness one-line installer.
#   curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
#   bash install.sh [--dir ~/OpenVideoHarness] [--refs] [--no-skill] [--skill claude|codex|all] [--obscura] [--icon | --no-icon]
# What it does, and where it puts things:
#   1. clone the repo into --dir, newest commit only (about 200 MB on disk; a re-run moves it to the newest commit, keeping LOCAL.md and projects/)
#   2. npm install in engines/ClaudeAnimationBase and npm ci in styles/_swatch (HyperFrames 0.8.202), both inside --dir (about 180 MB of
#      node_modules; npm also writes its own cache, ~/.npm). The read-only reference repos references/fetch.sh lists are not fetched:
#      an agent fetches the one a doc points to when it first needs it (bash references/fetch.sh <name>, which says its size first);
#      --refs fetches them all now into references/repos/ (about 300 MB, git-ignored; --no-refs, the old way to skip them, is the default)
#   3. copy LOCAL.example.md to LOCAL.md (git-ignored) if there is no LOCAL.md
#   4. unless --no-skill, write the skills (skills/*: open-video-harness, open-video-harness-web) to ~/.claude/skills and
#      ~/.agents/skills (--skill claude|codex: only one): short stubs that read skills/ in --dir, so a re-run or git pull updates them
#   4b. with --obscura, bin/vh web install: the pinned Obscura release (a headless browser, about 70 MB from its GitHub releases)
#      into ~/.local/share/ovh/obscura, linked from ~/.local/bin; bin/vh web checks facts against web pages with it
#   5. run bin/vh doctor --fill-local --first as the last lines: ready for a first film or not, what it still needs and how to get it,
#      how a voice comes on this machine (the full report: bin/vh doctor); it also writes LOCAL.md's machine lines (硬件, 已装工具,
#      已装引擎) where they still hold the template, never a line you wrote
#   6. put OVH Studio, Studio's own window, in your applications (macOS: ~/Applications/OVH Studio.app; a Linux desktop: a
#      desktop entry in ~/.local/share/applications): Electron, about 130 MB downloaded once and 260 MB on disk (without npm or
#      a network, a small launcher that opens a browser's window instead). No question. A run again leaves it alone when it is
#      there and up to date, and never replaces it while it is open. --no-icon leaves it out, this time and every later run
#      (kept as ~/.local/share/ovh-studio/no-app); --icon puts it in again. A Linux machine with no desktop gets none
# Nothing asks a question: a missing tool or a failed step says what to do next in one sentence.
# It never runs sudo and leaves your PATH and shell profile alone. Not done here: the first use of the tools downloads more, into caches under
# your home directory, without asking:
#   - the first hyperframes render: HyperFrames' own chrome-headless-shell (about 200 MB, ~/.cache/hyperframes)
#   - the first bin/vh beats, music, sfx, qa or sheet: their Python packages, through uv (about 700 MB, ~/.cache/uv)
#   - the first bin/vh tts with the default qwen provider (skipped with another one): its Python packages (about 750 MB, ~/.cache/uv)
#     and the Qwen3-TTS model (1.8 GB, ~/.cache/huggingface); bin/vh tts says so before it starts and shows the progress
#   - every bin/vh new short, promo, data or meme: about 140 MB of node_modules in that project
# The wiki's Getting Started ("What gets downloaded") has the same list.
set -euo pipefail
REPO="${OVH_REPO:-https://github.com/ZLHad/OpenVideoHarness.git}"
DIR="${OVH_DIR:-$HOME/OpenVideoHarness}"; REFS=0; SKILL=all; OBSCURA=0; ICON=default
while [ $# -gt 0 ]; do case "$1" in
  --dir) DIR="$2"; shift 2 ;; --refs) REFS=1; shift ;; --no-refs) REFS=0; shift ;; --no-skill) SKILL=none; shift ;; --skill) SKILL="${2:?--skill needs claude|codex|all|none}"; shift 2 ;; --obscura) OBSCURA=1; shift ;;
  --icon) ICON=yes; shift ;; --no-icon) ICON=no; shift ;;
  -h|--help) sed -n '2,32p' "$0"; exit 0 ;; *) echo "unknown option: $1"; exit 1 ;; esac; done
case "$SKILL" in claude|codex|all|none) ;; *) echo "unknown --skill '$SKILL' (claude|codex|all|none)"; exit 1 ;; esac
say() { printf '\033[1m→ %s\033[0m\n' "$*"; }
NOAPP="${XDG_DATA_HOME:-$HOME/.local/share}/ovh-studio/no-app"   # --no-icon once: kept here, so an update leaves OVH Studio out too (--icon clears it)
put_icon() {   # OVH Studio in the applications, unasked (macOS, a Linux desktop): left alone when it is there and current, never
  # replaced while it is open, left out once --no-icon said so; its own lines (the download) show as it goes
  local st out
  case "$(uname -s)" in Darwin) ;; Linux) [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] || { ICON_HEADLESS=1; return 0; } ;; *) return 0 ;; esac
  case "$ICON" in
    no) mkdir -p "$(dirname "$NOAPP")" && : > "$NOAPP"; ICON_LATER=1; return 0 ;;
    yes) rm -f "$NOAPP" ;;
    *) if [ -f "$NOAPP" ]; then echo "  OVH Studio stays out of your applications, as --no-icon asked before (--icon puts it in)"; ICON_LATER=1; return 0; fi ;;
  esac
  st=$(bin/vh studio --icon-status --json 2>/dev/null) || st=""
  case "$st" in *'"state": "ok"'*) echo "  OVH Studio is in your applications already, and up to date"; ICON_DONE=1; return 0 ;; esac
  case "$st" in *'"running": true'*)
    echo "  OVH Studio is open, so it was left as it is: quit it, then bin/vh studio --install-icon brings it up to date"; ICON_DONE=1; return 0 ;; esac
  say "putting OVH Studio in your applications (Studio's own window: about 130 MB to download once, 260 MB on disk; --no-icon leaves it out)"
  if ! out=$(bin/vh studio --install-icon --json); then   # (its progress and, on a failure, its reason go to the terminal)
    ICON_LATER=1; echo "! OVH Studio was not put in your applications (the line above says why); bin/vh studio --install-icon tries again"; return 0
  fi
  ICON_DONE=1
  case "$out" in *'"kind": "launcher"'*)
    echo "  a small launcher was made instead, which opens Studio in a browser's window: $(printf '%s' "$out" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("note") or "")' 2>/dev/null)" ;; esac
}
if [ "$(uname -s)" = Darwin ] && [ "$(command -v git)" = /usr/bin/git ] && ! xcode-select -p >/dev/null 2>&1; then   # git is Apple's stub until they are there
  echo "✗ First this Mac needs Apple's command line tools (git comes with them): run xcode-select --install, then run this installer again."; exit 1
fi
missing=""
for t in git node ffmpeg; do command -v "$t" >/dev/null 2>&1 || missing="$missing $t"; done
if [ -n "$missing" ]; then
  if [ "$(uname -s)" = Darwin ] && command -v brew >/dev/null 2>&1; then how="brew install${missing}"
  elif [ "$(uname -s)" = Darwin ]; then how="get Homebrew (https://brew.sh), then brew install${missing}"
  else how="install them with your package manager (Node ≥ 22: https://nodejs.org)"; fi
  echo "✗ First this computer needs${missing}: ${how}, then run this installer again."; exit 1
fi
if [ -d "$DIR/.git" ]; then say "updating $DIR"
  if [ -f "$DIR/.git/shallow" ]; then
    # A shallow install: fetch the newest commit alone and move to it. Its parent isn't fetched, so there is nothing to fast-forward
    # along; reset --keep leaves untracked and ignored files (LOCAL.md, projects/) and edits to files this update doesn't touch as they
    # are, and stops rather than overwrite an edited file. It would leave commits of your own behind, so look for those first.
    up=$(git -C "$DIR" rev-parse -q --verify '@{u}' 2>/dev/null) ||
      { echo "✗ $DIR is not on a branch that tracks the repo (a detached HEAD, or a branch of your own): git -C \"$DIR\" switch main, then re-run"
        echo "  (already on main? then origin/main is missing: git -C \"$DIR\" fetch, then re-run)"; exit 1; }
    own=$(git -C "$DIR" rev-list '@{u}..HEAD')
    grep -qx "$(git -C "$DIR" rev-parse HEAD)" "$DIR/.git/shallow" || [ -z "$own" ] ||
      { echo "✗ $DIR has commits of your own, which this update would leave behind; update it yourself: git -C \"$DIR\" pull --rebase"; exit 1; }
    git -C "$DIR" fetch -q --depth 1
    git -C "$DIR" reset -q --keep '@{u}' || {
      # put origin/main back where it was, so git status and the next run see the checkout as it was before this run
      git -C "$DIR" update-ref "$(git -C "$DIR" rev-parse --symbolic-full-name '@{u}')" "$up"
      echo "✗ $DIR not updated: it would overwrite the files named above. Edited ones: git -C \"$DIR\" stash, re-run, then git -C \"$DIR\" stash pop."
      echo "  Untracked ones: move them out of the way, then re-run."; exit 1; }
  else git -C "$DIR" pull --ff-only -q || {   # a full clone (made by hand, or by an installer from before shallow clones) keeps its history
      echo "✗ $DIR could not fast-forward to origin/main: a network error (above), commits of your own, or a clone made"
      echo "  before the 2026-10-04 history rewrite (every commit hash changed). For the rewrite, don't merge or rebase (that"
      echo "  brings the old videos back): clone again and move LOCAL.md and projects/ over. Details:"
      echo "  git -C \"$DIR\" show origin/main:CHANGELOG.md (\"The git history no longer carries the old videos\")"; exit 1; }
  fi
else say "cloning into $DIR (newest commit only)"
  git clone -q --depth 1 --single-branch "$REPO" "$DIR" || { echo "✗ Could not download OpenVideoHarness: check the network (or your proxy) and run this installer again."; exit 1; }; fi
cd "$DIR"
say "installing the bundled engine (ClaudeAnimationBase)"
(cd engines/ClaudeAnimationBase && npm install --silent) || echo "! the hand-drawn engine's packages did not install; running this installer again finishes them"
n=$(grep -cE '^(full|sparse|textonly) ' references/fetch.sh || true)   # counted from the list, so it cannot go stale
if [ "$REFS" = 1 ]; then
  say "fetching $n reference repos (about 300 MB, read-only, git-ignored)"
  references/fetch.sh || echo "! some reference repos were not fetched; bash references/fetch.sh fetches them later"
else had=0; [ ! -d references/repos ] || had=$(find references/repos -mindepth 2 -maxdepth 2 -name .git | wc -l | tr -d ' ')
  if [ "${had:-0}" -gt 0 ]; then echo "  the $had reference repos fetched before stay as they are (--refs updates them and fetches the rest)"; fi
fi
say "installing the renderer for style samples (HyperFrames, for bin/vh style)"
(cd styles/_swatch && npm ci --silent) || echo "! the renderer for style samples did not install; it is tried again the first time a style sample is made"
[ -f LOCAL.md ] || cp LOCAL.example.md LOCAL.md
if [ "$SKILL" != none ]; then   # one line for the stubs it wrote (each says where it went when run by hand: bin/vh install-skill)
  say "telling Claude Code and Codex where this workbench is (skills)"
  if out=$(bin/vh install-skill "$SKILL" 2>&1); then
    echo "  $(printf '%s\n' "$out" | grep -c 'skill →') skill stubs written; restart Claude Code or Codex if it is open, so it sees them"
  else printf '%s\n' "$out"; echo "! the skills were not registered; bin/vh install-skill $SKILL registers them"; fi
fi
[ "$OBSCURA" = 0 ] || { say "installing Obscura (an optional page reader that bin/vh web can use to keep web pages for fact checks)"; bin/vh web install || echo "! Obscura not installed; bin/vh web install retries it"; }
ICON_LATER=""; ICON_DONE=""; ICON_HEADLESS=""; put_icon
echo
# the last lines: ready for a first film or not, what it still needs, how a voice comes here (the full report: bin/vh doctor)
READY=""; bin/vh doctor --fill-local --first && READY=1
echo
if [ -n "$READY" ]; then echo "✓ OpenVideoHarness is ready at $DIR. Two ways to start:"
else echo "✗ OpenVideoHarness is installed at $DIR; a first film still needs what is listed above. Then, two ways to start:"; fi
if [ -n "$ICON_DONE" ]; then echo "  1. Click OVH Studio in your applications: your films, their stops and the agent, in one window."
elif [ -n "$ICON_HEADLESS" ]; then echo "  1. Studio, in a browser on another computer: cd \"$DIR\" && bin/vh studio --print-address (this machine has no desktop)"
else echo "  1. Studio, your films in one window: cd \"$DIR\" && bin/vh studio$([ -z "$ICON_LATER" ] || printf ' (bin/vh studio --install-icon puts it in your applications)')"; fi
echo "  2. Open Claude Code or Codex in that folder (cd \"$DIR\" && claude) and say what film you want, e.g."
echo "     \"快速出一版 15 秒的竖屏无声科普，用方格和画面文字讲清楚为什么正方形边长翻倍，面积变成四倍。\""
echo "  The full report of this machine: bin/vh doctor"
