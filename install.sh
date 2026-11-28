#!/usr/bin/env bash
# OpenVideoHarness one-line installer.
#   curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
#   bash install.sh [--dir ~/OpenVideoHarness] [--refs] [--no-skill] [--skill claude|codex|all] [--mirror cn|off] [--obscura] [--studio]
# What it does, and where it puts things:
#   1. clone the repo into --dir, newest commit only (about 200 MB on disk; a re-run moves it to the newest commit, keeping LOCAL.md and projects/)
#   1b. the download mirrors (tools/mirrors.txt): with neither --mirror nor a choice made before (bin/vh settings), try the official
#      npm registry (through npm, so its own proxy setting counts), Hugging Face and Google's storage (Chrome), twice each, 5 s a try;
#      when one does not answer and its mainland-China mirror does, use the mirrors from here on, say which and why in one line,
#      and keep the choice in ~/.config/ovh/settings.json, so later bin/vh downloads use them too (bin/vh settings mirror off turns
#      that off). --mirror cn uses them without trying, --mirror off never. Never guessed from the language or time zone
#   2. npm install in engines/ClaudeAnimationBase and npm ci in styles/_swatch (HyperFrames 0.8.202), both inside --dir (about 180 MB of
#      node_modules; npm also writes its own cache, ~/.npm). The read-only reference repos references/fetch.sh lists are not fetched:
#      an agent fetches the one a doc points to when it first needs it (bash references/fetch.sh <name>, which says its size first);
#      --refs fetches them all now into references/repos/ (about 300 MB, git-ignored; --no-refs, the old way to skip them, is the default)
#   3. copy LOCAL.example.md to LOCAL.md (git-ignored) if there is no LOCAL.md
#   4. unless --no-skill, write the skills (skills/*: open-video-harness, open-video-harness-web) to ~/.claude/skills and
#      ~/.agents/skills (--skill claude|codex: only one): short stubs that read skills/ in --dir, so a re-run or git pull updates them
#   4b. with --obscura, bin/vh web install: the pinned Obscura release (a headless browser, about 70 MB from its GitHub releases)
#      into ~/.local/share/ovh/obscura, linked from ~/.local/bin; bin/vh web checks facts against web pages with it
#   4c. with --studio, install the v0.10.0 Studio preview from its release into a separate checkout
#      (~/OpenVideoHarness-Studio-Preview), and put its launcher in your applications
#   5. run bin/vh doctor --fill-local --first as the last lines: ready for a first film or not, what it still needs and how to get it,
#      how a voice comes on this machine (the full report: bin/vh doctor); it also writes LOCAL.md's machine lines (硬件, 已装工具,
#      已装引擎) where they still hold the template, never a line you wrote
# Nothing asks a question: a missing tool or a failed step says what to do next in one sentence.
# It never runs sudo and leaves your PATH and shell profile alone. Not done here: the first use of the tools downloads more, into caches under
# your home directory, without asking:
#   - the first hyperframes render: HyperFrames' own chrome-headless-shell (about 200 MB, ~/.cache/hyperframes)
#   - the first bin/vh beats, music, sfx, qa or sheet: their Python packages, through uv (about 700 MB, ~/.cache/uv)
#   - the first bin/vh tts with the default qwen provider (skipped with another one): its Python packages (about 0.8 GB, ~/.cache/uv)
#     and the Qwen3-TTS model (1.8 GB, ~/.cache/huggingface); --align local adds the local Whisper (about 3.6 GB); bin/vh tts says
#     so before it starts and shows the progress (the sizes: tools/audio/firstuse.py)
#   - every bin/vh new short, promo, data or meme: about 140 MB of node_modules in that project
# The wiki's Getting Started ("What gets downloaded") has the same list.
set -euo pipefail
REPO="${OVH_REPO:-https://github.com/ZLHad/OpenVideoHarness.git}"
DIR="${OVH_DIR:-$HOME/OpenVideoHarness}"; REFS=0; SKILL=all; OBSCURA=0; STUDIO=0; MIRROR=""
while [ $# -gt 0 ]; do case "$1" in
  --dir) DIR="$2"; shift 2 ;; --refs) REFS=1; shift ;; --no-refs) REFS=0; shift ;; --no-skill) SKILL=none; shift ;; --skill) SKILL="${2:?--skill needs claude|codex|all|none}"; shift 2 ;; --obscura) OBSCURA=1; shift ;; --mirror) MIRROR="${2:?--mirror needs cn or off}"; shift 2 ;;
  --studio|--icon) STUDIO=1; shift ;;
  --no-icon) STUDIO=0; shift ;;
  -h|--help) awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; exit 0 ;; *) echo "unknown option: $1"; exit 1 ;; esac; done
case "$SKILL" in claude|codex|all|none) ;; *) echo "unknown --skill '$SKILL' (claude|codex|all|none)"; exit 1 ;; esac
[ -z "$MIRROR" ] || case "$MIRROR" in cn|off) ;; *) echo "unknown --mirror '$MIRROR' (cn|off)"; exit 1 ;; esac
say() { printf '\033[1m→ %s\033[0m\n' "$*"; }
install_studio_preview() {
  local version=v0.10.0 commit=68ee234e71757c0b77829ec11b25ad3a445aae3b
  local preview="${OVH_STUDIO_PREVIEW_DIR:-$HOME/OpenVideoHarness-Studio-Preview}" status changed
  if [ ! -e "$preview" ]; then
    say "downloading Studio $version to $preview"
    git clone --quiet --single-branch --depth 1 --branch "$version" "$REPO" "$preview" || return 1
  fi
  if [ ! -d "$preview/.git" ] || [ "$(git -C "$preview" rev-parse --verify HEAD 2>/dev/null)" != "$commit" ]; then
    echo "! $preview is not a Studio $version checkout. Set OVH_STUDIO_PREVIEW_DIR to an unused path and retry." >&2
    return 1
  fi
  changed=$(git -C "$preview" status --porcelain) || return 1
  if [ -n "$changed" ]; then
    echo "! $preview has local edits. Set OVH_STUDIO_PREVIEW_DIR to an unused path and retry." >&2
    return 1
  fi

  # The preview owns its engine dependencies and its launcher. The skills are registered above for the main checkout.
  if [ ! -d "$preview/engines/ClaudeAnimationBase/node_modules" ]; then
    (cd "$preview/engines/ClaudeAnimationBase" && npm ci --silent) || return 1
  fi
  if [ ! -d "$preview/styles/_swatch/node_modules" ]; then
    (cd "$preview/styles/_swatch" && npm ci --silent) || return 1
  fi
  status=$("$preview/bin/vh" studio --icon-status --json 2>/dev/null) || status=""
  case "$status" in
    *'"state": "ok"'*) ;;
    *'"running": true'*) echo "! Close the running OVH Studio before installing the $version launcher, then retry." >&2; return 1 ;;
    *) "$preview/bin/vh" studio --install-icon || return 1 ;;
  esac
  echo "  Open OVH Studio from your applications, or run: \\"$preview/bin/vh\\" studio"
}

if [ "$(uname -s)" = Darwin ] && [ "$(command -v git)" = /usr/bin/git ] && ! xcode-select -p >/dev/null 2>&1; then   # git is Apple's stub until they are there
  echo "✗ First this Mac needs Apple's command line tools (git comes with them): run xcode-select --install, then run this installer again."; exit 1
fi
missing=""
for t in git node ffmpeg python3; do command -v "$t" >/dev/null 2>&1 || missing="$missing $t"; done   # (bin/vh's commands run on python3)
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
reach() {   # reach <url> [npm]: does it answer at all (any HTTP reply counts), in 5 s, at the first or the second try? → 0; else 1,
  # and what happened on stdout. With npm: npm ping, so a proxy that lives only in npm's own configuration is used as npm would
  local rc out=""
  for _ in 1 2; do
    if [ "${2:-}" = npm ] && command -v npm >/dev/null 2>&1; then
      out=$(npm ping --registry "$1" --fetch-timeout=5000 --fetch-retries=0 2>&1) && return 0
      case "$out" in *ENOTFOUND*|*EAI_AGAIN*) out="its name did not resolve" ;; *ETIMEDOUT*|*imeout*) out="it did not answer in 5 s" ;;
        *ECONNREFUSED*) out="it refused the connection" ;; *ECONNRESET*) out="the connection was reset" ;; *) out="npm could not reach it" ;; esac
    elif command -v curl >/dev/null 2>&1; then
      rc=0; curl -sS -o /dev/null -m 5 "$1" 2>/dev/null || rc=$?
      [ "$rc" = 0 ] && return 0
      case $rc in 5) out="the proxy's name did not resolve" ;; 6) out="its name did not resolve" ;; 7) out="it refused the connection" ;;
        28) out="it did not answer in 5 s" ;; 35|60) out="the secure connection failed" ;; 52|56) out="the connection was reset" ;; *) out="curl error $rc" ;; esac
    else echo "nothing here to try it with (no curl)"; return 1
    fi
  done
  echo "$out, twice"; return 1
}
PROBES='registry.npmjs.org https://registry.npmjs.org/ https://registry.npmmirror.com/ npm
huggingface.co https://huggingface.co/ https://hf-mirror.com/ curl
storage.googleapis.com https://storage.googleapis.com/chrome-for-testing-public/ https://cdn.npmmirror.com/binaries/chrome-for-testing/ curl'   # each official source: what to try, its mirror, how (npm: through npm itself)
probe_mirrors() {   # with no choice made: each official source, all three at once; cn when one fails and its mirror answers. → the why
  local pt name url mir how n=0 why=""
  pt=$(mktemp -d "${TMPDIR:-/tmp}/ovh-probe.XXXXXX")
  while read -r name url mir how; do
    n=$((n + 1)); ( if r=$(reach "$url" "$how"); then : > "$pt/$n.ok"; else printf '%s' "$r" > "$pt/$n.no"; fi ) &
  done <<<"$PROBES"
  wait
  n=0
  while read -r name url mir how; do
    n=$((n + 1)); [ -f "$pt/$n.no" ] || continue
    mir=${mir#https://}
    if reach "https://$mir" >/dev/null; then why="${why:+$why; }$name: $(cat "$pt/$n.no"), and ${mir%%/*} answered"; fi
  done <<<"$PROBES"
  rm -rf "$pt"
  printf '%s' "$why"
}
NOW=""   # the mirror for this run when it could not be kept (an unwritable ~/.config)
if [ -n "$MIRROR" ]; then
  bin/vh settings mirror "$MIRROR" --why "install.sh --mirror $MIRROR, $(date +%F)" | sed 's/^/  /' || NOW=$MIRROR
elif [ "$(bin/vh settings mirror --get 2>/dev/null)" = auto ]; then
  why=$(probe_mirrors)
  if [ -n "$why" ]; then
    bin/vh settings mirror cn --why "install.sh, $(date +%F): $why" >/dev/null || NOW=cn
    echo "  $why: so downloads come from the mainland-China mirrors from now on (npmmirror.com, TUNA, hf-mirror.com;"
    echo "  tools/mirrors.txt). bin/vh settings mirror off turns that off."
  fi
fi
eval "$(python3 tools/settings.py env ${NOW:+--mode "$NOW"})"   # the mirrors, when they are on, for this script's own downloads too
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
[ "${OVH_MIRROR:-}" != cn ] || bin/vh settings chrome || true   # with the mirrors on: its Chrome from the mirror now (a miss says so, in a line)
[ -f LOCAL.md ] || cp LOCAL.example.md LOCAL.md
if [ "$SKILL" != none ]; then   # one line for the stubs it wrote (each says where it went when run by hand: bin/vh install-skill)
  say "telling Claude Code and Codex where this workbench is (skills)"
  if out=$(bin/vh install-skill "$SKILL" 2>&1); then
    echo "  $(printf '%s\n' "$out" | grep -c 'skill →') skill stubs written; restart Claude Code or Codex if it is open, so it sees them"
  else printf '%s\n' "$out"; echo "! the skills were not registered; bin/vh install-skill $SKILL registers them"; fi
fi
[ "$OBSCURA" = 0 ] || { say "installing Obscura (an optional page reader that bin/vh web can use to keep web pages for fact checks)"; bin/vh web install || echo "! Obscura not installed; bin/vh web install retries it"; }
studio_rc=0
if [ "$STUDIO" = 1 ]; then
  install_studio_preview || studio_rc=$?
  [ "$studio_rc" = 0 ] || echo "! Studio preview setup did not finish. You can retry with --studio." >&2
fi
echo
# the last lines: ready for a first film or not, what it still needs, how a voice comes here (the full report: bin/vh doctor)
st=0; bin/vh doctor --fill-local --first || st=$?   # 0 ready, 3 one thing not checked, else not ready
echo
case $st in 0) echo "✓ OpenVideoHarness is ready at $DIR. Ready to start." ;;
  3) echo "OpenVideoHarness is installed at $DIR; one thing above could not be checked here. Ready to start." ;;
  *) echo "✗ OpenVideoHarness is installed at $DIR; a first film still needs what is listed above. " ;; esac
echo "  Open Claude Code or Codex in that folder (cd \"$DIR\" && claude) and say what film you want, e.g."
case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in   # the example in the person's language (the README's silent first film)
  zh*|ZH*) echo "     \"快速出一版 15 秒的竖屏无声科普，用方格和画面文字讲清楚为什么正方形边长翻倍，面积变成四倍。\"" ;;
  *) echo "     \"Quick draft: make a silent 15-second vertical explainer showing why doubling a square's side length quadruples its area. Use a grid and on-screen text.\"" ;; esac
echo "  The full report of this machine: bin/vh doctor"
exit "$studio_rc"
