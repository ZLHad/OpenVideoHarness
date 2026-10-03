#!/usr/bin/env bash
# OpenVideoHarness one-line installer.
#   curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
#   bash install.sh [--dir ~/OpenVideoHarness] [--no-refs] [--no-skill] [--skill claude|codex|all]
# What it does, and where it puts things:
#   1. clone the repo into --dir, newest commit only (about 420 MB; a re-run moves it to the newest commit, keeping LOCAL.md and projects/)
#   2. npm install in engines/ClaudeAnimationBase and npm ci in styles/_swatch (HyperFrames 0.8.82), both inside --dir (about 210 MB of
#      node_modules; npm also writes its own cache, ~/.npm); unless --no-refs, fetch 30 read-only reference repos into references/repos/
#      (about 195 MB, git-ignored; references/fetch.sh <name> fetches one later)
#   3. copy LOCAL.example.md to LOCAL.md (git-ignored) if there is no LOCAL.md
#   4. unless --no-skill, write the open-video-harness skill file to ~/.claude/skills and ~/.agents/skills (--skill claude|codex: only one)
#   5. run bin/vh doctor as a final check
# It never runs sudo and leaves your PATH and shell profile alone. Not done here: the first use of the tools downloads more, into caches under
# your home directory, without asking:
#   - the first hyperframes render: HyperFrames' own chrome-headless-shell (about 200 MB, ~/.cache/hyperframes)
#   - the first bin/vh beats, music, sfx, qa or sheet: their Python packages, through uv (about 700 MB, ~/.cache/uv)
#   - the first bin/vh tts with the default qwen provider (skipped with another one): its Python packages (about 750 MB, ~/.cache/uv)
#     and the Qwen3-TTS model (about 2 GB, ~/.cache/huggingface)
#   - every bin/vh new short, promo, data or meme: about 140 MB of node_modules in that project
# The README's "What gets downloaded" has the same list.
set -euo pipefail
REPO="${OVH_REPO:-https://github.com/ZLHad/OpenVideoHarness.git}"
DIR="${OVH_DIR:-$HOME/OpenVideoHarness}"; REFS=1; SKILL=all
while [ $# -gt 0 ]; do case "$1" in
  --dir) DIR="$2"; shift 2 ;; --no-refs) REFS=0; shift ;; --no-skill) SKILL=none; shift ;; --skill) SKILL="${2:?--skill needs claude|codex|all|none}"; shift 2 ;;
  -h|--help) sed -n '2,20p' "$0"; exit 0 ;; *) echo "unknown option: $1"; exit 1 ;; esac; done
case "$SKILL" in claude|codex|all|none) ;; *) echo "unknown --skill '$SKILL' (claude|codex|all|none)"; exit 1 ;; esac
say() { printf '\033[1m→ %s\033[0m\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "✗ $1 is required ($2)"; MISSING=1; }; }
MISSING=0
need git "https://git-scm.com"; need node "Node.js ≥ 22: https://nodejs.org"; need ffmpeg "macOS: brew install ffmpeg"
[ "$MISSING" = 0 ] || { echo "install the missing tools above, then re-run"; exit 1; }
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
  else git -C "$DIR" pull --ff-only -q; fi   # a full clone (made by hand, or by an installer from before shallow clones) keeps its history
else say "cloning into $DIR (newest commit only)"; git clone -q --depth 1 --single-branch "$REPO" "$DIR"; fi
cd "$DIR"
say "installing the bundled engine (ClaudeAnimationBase)"; (cd engines/ClaudeAnimationBase && npm install --silent)
if [ "$REFS" = 1 ]; then say "fetching 30 reference repos (about 195 MB, read-only, git-ignored; --no-refs skips them)"; references/fetch.sh; fi
say "installing the style swatch renderer (HyperFrames, for bin/vh style)"
(cd styles/_swatch && npm ci --silent) || echo "! swatch renderer not installed; bin/vh style retries it on first use (or: cd styles/_swatch && npm ci)"
[ -f LOCAL.md ] || cp LOCAL.example.md LOCAL.md
[ "$SKILL" = none ] || { say "registering the skill"; bin/vh install-skill "$SKILL"; }
say "final check"; bin/vh doctor || true
cat <<MSG

✓ OpenVideoHarness is ready at $DIR
  Next:  cd "$DIR" && claude        (or: codex)
         then say what you want, e.g. "做一个 30 秒的竖屏科普：为什么低轨卫星的信号会变调"
  Or scaffold first:  bin/vh new short my-first-video
  Docs:  README.md · CLAUDE.md · bin/vh help
  Note:  the first render downloads Chrome (about 200 MB) and the first sound commands download Python packages (about 700 MB)
         into ~/.cache; see "What gets downloaded" in README.md
MSG
