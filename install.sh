#!/usr/bin/env bash
# OpenVideoHarness one-line installer.
#   curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
#   bash install.sh [--dir ~/OpenVideoHarness] [--no-refs] [--no-skill] [--skill claude|codex|all]
# What it does:
#   1. clone (or fast-forward) the repo into --dir
#   2. check the toolchain (bin/vh doctor)
#   3. install the bundled hand-drawn engine's deps and, unless --no-refs, fetch ~25 read-only reference repos
#   4. unless --no-skill, register the open-video-harness skill for Claude Code (~/.claude/skills) and Codex (~/.agents/skills)
# Nothing else is installed globally. Models (e.g. local Qwen3-TTS, ~2 GB) download only when you first use them.
set -euo pipefail
REPO="${OVH_REPO:-https://github.com/ZLHad/OpenVideoHarness.git}"
DIR="${OVH_DIR:-$HOME/OpenVideoHarness}"; REFS=1; SKILL=all
while [ $# -gt 0 ]; do case "$1" in
  --dir) DIR="$2"; shift 2 ;; --no-refs) REFS=0; shift ;; --no-skill) SKILL=none; shift ;; --skill) SKILL="$2"; shift 2 ;;
  -h|--help) sed -n '2,11p' "$0"; exit 0 ;; *) echo "unknown option: $1"; exit 1 ;; esac; done
say() { printf '\033[1m→ %s\033[0m\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "✗ $1 is required ($2)"; MISSING=1; }; }
MISSING=0
need git "https://git-scm.com"; need node "Node.js ≥ 22: https://nodejs.org"; need ffmpeg "macOS: brew install ffmpeg"
[ "$MISSING" = 0 ] || { echo "install the missing tools above, then re-run"; exit 1; }
if [ -d "$DIR/.git" ]; then say "updating $DIR"; git -C "$DIR" pull --ff-only -q
else say "cloning into $DIR"; git clone -q "$REPO" "$DIR"; fi
cd "$DIR"
say "checking toolchain"; bin/vh doctor || true
say "installing the bundled engine (ClaudeAnimationBase)"; (cd engines/ClaudeAnimationBase && npm install --silent)
if [ "$REFS" = 1 ]; then say "fetching reference repos (read-only, git-ignored)"; references/fetch.sh; fi
[ -f LOCAL.md ] || cp LOCAL.example.md LOCAL.md
[ "$SKILL" = none ] || { say "registering the skill"; bin/vh install-skill "$SKILL"; }
cat <<MSG

✓ OpenVideoHarness is ready at $DIR
  Next:  cd "$DIR" && claude        (or: codex)
         then say what you want, e.g. "做一个 30 秒的竖屏科普：为什么低轨卫星的信号会变调"
  Or scaffold first:  bin/vh new short my-first-video
  Docs:  README.md · CLAUDE.md · bin/vh help
MSG
