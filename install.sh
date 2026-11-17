#!/usr/bin/env bash
# OpenVideoHarness one-line installer.
#   curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
#   bash install.sh [--dir ~/OpenVideoHarness] [--no-refs] [--no-skill] [--skill claude|codex|all] [--obscura] [--icon | --no-icon]
# What it does, and where it puts things:
#   1. clone the repo into --dir, newest commit only (about 200 MB on disk; a re-run moves it to the newest commit, keeping LOCAL.md and projects/)
#   2. npm install in engines/ClaudeAnimationBase and npm ci in styles/_swatch (HyperFrames 0.8.202), both inside --dir (about 210 MB of
#      node_modules; npm also writes its own cache, ~/.npm); unless --no-refs, fetch the read-only reference repos references/fetch.sh lists
#      into references/repos/ (about 250 MB, git-ignored; references/fetch.sh <name> fetches one later)
#   3. copy LOCAL.example.md to LOCAL.md (git-ignored) if there is no LOCAL.md
#   4. unless --no-skill, write the skills (skills/*: open-video-harness, open-video-harness-web) to ~/.claude/skills and
#      ~/.agents/skills (--skill claude|codex: only one): short stubs that read skills/ in --dir, so a re-run or git pull updates them
#   4b. with --obscura, bin/vh web install: the pinned Obscura release (a headless browser, about 70 MB from its GitHub releases)
#      into ~/.local/share/ovh/obscura, linked from ~/.local/bin; bin/vh web checks facts against web pages with it
#   5. run bin/vh doctor --fill-local as a final check: it also writes LOCAL.md's machine lines (硬件, 已装工具, 已装引擎)
#      where they still hold the template, never a line you wrote
#   6. put OVH Studio, Studio's own window, in your applications (macOS: ~/Applications/OVH Studio.app; a Linux desktop: a
#      desktop entry in ~/.local/share/applications): Electron, about 130 MB downloaded once and 260 MB on disk (without npm or
#      a network, a small launcher that opens a browser's window instead). No question: --no-icon skips it (--icon is the
#      default, still accepted); a Linux machine with no desktop gets none, and bin/vh studio --install-icon makes it later
# Nothing asks a question: a missing tool or a failed step says what to do next in one sentence.
# It never runs sudo and leaves your PATH and shell profile alone. Not done here: the first use of the tools downloads more, into caches under
# your home directory, without asking:
#   - the first hyperframes render: HyperFrames' own chrome-headless-shell (about 200 MB, ~/.cache/hyperframes)
#   - the first bin/vh beats, music, sfx, qa or sheet: their Python packages, through uv (about 700 MB, ~/.cache/uv)
#   - the first bin/vh tts with the default qwen provider (skipped with another one): its Python packages (about 750 MB, ~/.cache/uv)
#     and the Qwen3-TTS model (about 2 GB, ~/.cache/huggingface)
#   - every bin/vh new short, promo, data or meme: about 140 MB of node_modules in that project
# The wiki's Getting Started ("What gets downloaded") has the same list.
set -euo pipefail
REPO="${OVH_REPO:-https://github.com/ZLHad/OpenVideoHarness.git}"
DIR="${OVH_DIR:-$HOME/OpenVideoHarness}"; REFS=1; SKILL=all; OBSCURA=0; ICON=yes
while [ $# -gt 0 ]; do case "$1" in
  --dir) DIR="$2"; shift 2 ;; --no-refs) REFS=0; shift ;; --no-skill) SKILL=none; shift ;; --skill) SKILL="${2:?--skill needs claude|codex|all|none}"; shift 2 ;; --obscura) OBSCURA=1; shift ;;
  --icon) ICON=yes; shift ;; --no-icon) ICON=no; shift ;;
  -h|--help) sed -n '2,29p' "$0"; exit 0 ;; *) echo "unknown option: $1"; exit 1 ;; esac; done
case "$SKILL" in claude|codex|all|none) ;; *) echo "unknown --skill '$SKILL' (claude|codex|all|none)"; exit 1 ;; esac
say() { printf '\033[1m→ %s\033[0m\n' "$*"; }
put_icon() {   # OVH Studio in the applications, without a question: macOS and a Linux desktop; --no-icon skips it
  local err
  case "$(uname -s)" in Darwin) ;; Linux) [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] || { ICON_LATER=1; return 0; } ;; *) return 0 ;; esac
  [ "$ICON" = no ] && { ICON_LATER=1; return 0; }
  say "putting OVH Studio in your applications (Studio's own window: about 130 MB to download once, 260 MB on disk; --no-icon skips this)"
  err=$(bin/vh studio --install-icon 2>&1 >/dev/null) && { ICON_DONE=1; return 0; }
  ICON_LATER=1; echo "! OVH Studio was not put in your applications ($(printf '%s' "$err" | tail -n 1)); bin/vh studio --install-icon tries again"
}
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
if [ "$REFS" = 1 ]; then n=$(grep -cE '^(full|sparse|textonly) ' references/fetch.sh || true)   # counted from the list, so it cannot go stale
  say "fetching $n reference repos (about 250 MB, read-only, git-ignored; --no-refs skips them)"
  references/fetch.sh || echo "! some reference repos were not fetched; bash references/fetch.sh fetches them later"; fi
say "installing the style swatch renderer (HyperFrames, for bin/vh style)"
(cd styles/_swatch && npm ci --silent) || echo "! swatch renderer not installed; bin/vh style retries it on first use (or: cd styles/_swatch && npm ci)"
[ -f LOCAL.md ] || cp LOCAL.example.md LOCAL.md
[ "$SKILL" = none ] || { say "registering the skills"; bin/vh install-skill "$SKILL" || echo "! the skills were not registered; bin/vh install-skill $SKILL registers them"; }
[ "$OBSCURA" = 0 ] || { say "installing Obscura (bin/vh web)"; bin/vh web install || echo "! Obscura not installed; bin/vh web install retries it"; }
say "final check (and this machine's lines in LOCAL.md)"; bin/vh doctor --fill-local || true
ICON_LATER=""; ICON_DONE=""; put_icon
arm=""   # Linux arm64: HyperFrames has no Chrome of its own there (engines/README.md, its notes), so a missing browser is said again below
if [ "$(uname -s)" = Linux ]; then case "$(uname -m)" in aarch64|arm64)
  bin/vh doctor --json 2>/dev/null | python3 -c 'import json, sys; sys.exit(0 if any(c["name"] == "browser" and c["state"] == "ok" for c in json.load(sys.stdin)["checks"]) else 1)' 2>/dev/null || arm=1 ;; esac; fi
cat <<MSG

  Docs:  README.md · CLAUDE.md · bin/vh help
  Note:  the first render downloads Chrome (about 200 MB) and the first sound commands download Python packages (about 700 MB)
         into ~/.cache; see "What gets downloaded" on the wiki's Getting Started page
MSG
[ "$REFS" = 1 ] || echo "  Refs:  not fetched (--no-refs). Where a doc points into references/repos/<dir>/, bash references/fetch.sh <dir> fetches that one"
[ -z "$arm" ] || echo "  ! Linux arm64: no browser yet, and HyperFrames has none of its own here; set one up before the first render (engines/README.md, \"Linux：渲染前要先备好的三样\")"
echo
echo "✓ OpenVideoHarness is ready at $DIR. Two ways to start:"
if [ -n "$ICON_DONE" ]; then echo "  1. Click OVH Studio in your applications: your films, their stops and the agent, in one window."
else echo "  1. Studio, your films in one window: cd \"$DIR\" && bin/vh studio$([ -z "$ICON_LATER" ] || printf ' (bin/vh studio --install-icon puts it in your applications)')"; fi
echo "  2. Open Claude Code or Codex in that folder (cd \"$DIR\" && claude) and say what film you want, e.g. \"做一个 30 秒的竖屏科普：为什么低轨卫星的信号会变调\""
