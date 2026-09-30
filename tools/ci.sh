#!/usr/bin/env bash
# ci.sh — the repo's own checks: the same run locally before a push and in GitHub Actions (.github/workflows/ci.yml).
#
#   tools/ci.sh                      everything the installed tools allow (shellcheck, pyflakes, ffmpeg are optional locally)
#   tools/ci.sh --smoke              only the bin/vh smoke tests
#   tools/ci.sh --committed          check HEAD in a clean temporary checkout: what a push sends, not the working tree
#   VH_BASH=/bin/bash tools/ci.sh    run bin/vh and the syntax checks under another bash (macOS ships bash 3.2)
#
# Why each group exists: the v0.2.1 review found macOS-only sed/stat/md5 flags that broke every Linux user, a
# doc/CLI mismatch, and a CLI that exited 0 on typos. These checks keep those from coming back.
# Exit status: the number of failed checks (0 = all passed).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
ROOT=$(pwd)
VH_BASH=${VH_BASH:-bash}
fails=0
ok() { printf '\033[32m✓\033[0m %s\n' "$*"; }
bad() { printf '\033[31m✗\033[0m %s\n' "$*"; fails=$((fails + 1)); }
skip() { printf '\033[33m-\033[0m %s (skipped: %s)\n' "$1" "$2"; }
files() { git ls-files "$@" | grep -v -E '^references/|(^|/)node_modules/|\.min\.js$'; }

static_checks() {
  local f n out
  # shell: parse with the bash that will run it, lint, and ban commands that only exist on one platform
  n=0; while IFS= read -r f; do "$VH_BASH" -n "$f" || { bad "bash -n $f"; n=$((n + 1)); }; done < <(files bin/vh '*.sh')
  [ $n = 0 ] && ok "shell syntax ($("$VH_BASH" -c 'echo $BASH_VERSION'))"
  if command -v shellcheck >/dev/null; then
    if out=$(files bin/vh '*.sh' | xargs shellcheck -S warning 2>&1); then ok "shellcheck -S warning"; else echo "$out"; bad "shellcheck"; fi
  else skip "shellcheck" "not installed"; fi
  # BSD-only or GNU-only flags, matched where a command starts: a statement start, a pipe, after if / while / until / do /
  # then / else, after `{`, `(`, `!` or a case arm, and behind a wrapper (xargs, sudo, exec, env, time, nohup, nice, command)
  # with its flags, VAR=value tokens or arguments. A small quote-aware scanner blanks comments, single-quoted strings,
  # double-quoted strings without $ or backticks, and heredoc bodies first (line numbers kept): a heredoc opens only at a
  # `<<name` outside quotes and comments with whitespace before it (not `<<<`, `1<<n` or a `<<EOF` in a comment), and its
  # terminator is matched ignoring leading tabs and trailing blanks, so a stray `<<` cannot blank the rest of a file.
  # A line may opt out with a trailing "# portable-ok: <why>"
  local np='(^|[;&|(){}!`]|\$\()[[:space:]]*((if|while|until|do|then|else|elif|xargs|sudo|exec|env|time|nohup|nice|command)([[:space:]]+(-[^[:space:]]*|[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*|[A-Za-z0-9_.{}-]+))*[[:space:]]+)*(sed -i|stat -[cf] |md5 -q|md5sum|readlink -f|grep -[a-zA-Z]*P|date -[djv] |xargs -r|find [^;|]*-printf|base64 -D|sort -V|tac( |$))'   # portable-ok: the list itself
  local awkprog=''; IFS= read -r -d '' awkprog <<'AWK' || true   # a heredoc, not $(…): the awk text has a backtick
BEGIN { term = "" }
term != "" { t = $0; sub(/^\t+/, "", t); sub(/[ \t]+$/, "", t); if (t == term) term = ""; print ""; next }
/portable-ok/ { print ""; next }
{ line = $0; out = ""; q = ""; buf = ""; n = length(line); i = 1
  while (i <= n) {
    c = substr(line, i, 1)
    if (q == "") {
      if (c == "#" && (i == 1 || substr(line, i - 1, 1) ~ /[ \t;]/)) break
      if (c == "\\") { out = out c substr(line, i + 1, 1); i += 2; continue }
      if (c == "'" || c == "\"") { q = c; buf = ""; i++; continue }
      if (c == "<" && substr(line, i, 2) == "<<" && substr(line, i + 2, 1) != "<" && (i == 1 || substr(line, i - 1, 1) ~ /[ \t]/)) {
        rest = substr(line, i + 2); sub(/^-/, "", rest)
        if (match(rest, /^["']?[A-Za-z_][A-Za-z0-9_]*/)) { term = substr(rest, RSTART, RLENGTH); gsub(/["']/, "", term) }
      }
      out = out c; i++
    } else {
      if (q == "\"" && c == "\\") { buf = buf c substr(line, i + 1, 1); i += 2; continue }
      if (c == q) { out = out ((q == "\"" && buf ~ /[$`]/) ? q buf q : q q); q = ""; i++; continue }
      buf = buf c; i++
    }
  }
  print out }
AWK
  out=$(while IFS= read -r f; do awk "$awkprog" "$f" | grep -n -E "$np" | sed "s#^#$f:#"; done < <(files bin/vh '*.sh'))
  if [ -n "$out" ]; then echo "$out"; bad "non-portable shell commands (use a helper that works with both BSD and GNU tools)"
  else ok "no BSD-only / GNU-only shell commands"; fi
  # python: compile everything, then pyflakes when available
  n=0; while IFS= read -r f; do python3 -m py_compile "$f" 2>/dev/null || { bad "py_compile $f"; n=$((n + 1)); }; done < <(files 'tools/*.py' 'styles/_swatch/*.py')
  [ $n = 0 ] && ok "python syntax"
  if python3 -m pyflakes --version >/dev/null 2>&1; then
    if out=$(files 'tools/*.py' 'styles/_swatch/*.py' | xargs python3 -m pyflakes 2>&1); then ok "pyflakes"; else echo "$out"; bad "pyflakes"; fi
  else skip "pyflakes" "pip install pyflakes"; fi
  # js: node --check detects ES modules by syntax (node ≥ 22)
  n=0; while IFS= read -r f; do node --check "$f" 2>/dev/null || { node --check "$f"; bad "node --check $f"; n=$((n + 1)); }; done < <(files '*.js' '*.mjs')
  [ $n = 0 ] && ok "js syntax"
}

doc_checks() {
  local head
  head=$(head -3 AGENTS.md)
  if [ "$(tail -n +4 AGENTS.md)" = "$(cat CLAUDE.md)" ] && [ -n "$head" ]; then ok "AGENTS.md generated from CLAUDE.md"
  else bad "AGENTS.md is out of sync with CLAUDE.md: run bin/vh sync-agents"; fi
  # every `bin/vh <command>` in the docs exists, and CLAUDE.md's command list names exactly the commands bin/vh dispatches
  if python3 - <<'PY'
import re, subprocess, sys
src = open("bin/vh", encoding="utf-8").read()
block = src[src.index('case "${1:-help}" in'):]
block = block[:block.index("\nesac")]
cmds = {c for pat in re.findall(r"(?:^|;;)\s*([a-z|-]+)\)", block, re.M) for c in pat.split("|") if c and not c.startswith("-")}
cmds.discard("help")
listed = set(re.search(r"命令行：(.+)", open("CLAUDE.md", encoding="utf-8").read()).group(1).split(" · "))
bad = []
if listed != cmds:
    bad.append(f"CLAUDE.md command list vs bin/vh dispatch: missing {sorted(cmds - listed)}, unknown {sorted(listed - cmds)}")
docs = subprocess.run(["git", "ls-files", "*.md"], capture_output=True, text=True).stdout.split()
for d in docs:   # commands written as code: inside `backticks` or a fenced block (prose like "bin/vh · QA tools" is a label)
    if d.startswith("references/") or d == "CHANGELOG.md":
        continue
    fence = False
    for n, line in enumerate(open(d, encoding="utf-8"), 1):
        if line.lstrip().startswith("```"):
            fence = not fence; continue
        for code in [line] if fence else re.findall(r"`([^`]*)`", line):
            for c in re.findall(r"bin/vh ([a-z][a-z-]*)", code):
                if c not in cmds and c != "help":
                    bad.append(f"{d}:{n}: bin/vh {c} is not a command")
print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
  then ok "docs name only real bin/vh commands"; else bad "docs vs bin/vh commands"; fi
}

vh() { "$VH_BASH" "$ROOT/bin/vh" "$@"; }
smoke_checks() {
  local slug="ci-smoke-$$" dir t rc langs a
  vh help >/dev/null && vh --help >/dev/null && ok "bin/vh help exits 0" || bad "bin/vh help"
  vh no-such-command >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "unknown command exits 1" || bad "unknown command exited $rc"
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")   # a throwaway HOME: an old bin/vh would install the skill for a bad target
  HOME="$t" vh install-skill no-such-target >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "install-skill rejects unknown targets" || bad "install-skill bad target exited $rc"
  rm -rf "$t"
  vh types >/dev/null && vh effort quick >/dev/null && vh style list >/dev/null && ok "types · effort · style list" || bad "types / effort / style list"
  # a project: effort and style are written in, and the quick gate waiver is recorded
  dir=$(ls -d "$ROOT"/projects/*-"$slug" 2>/dev/null); [ -z "$dir" ] || rm -rf "$dir"
  if vh new math "$slug" --effort quick --style dark-math >/dev/null; then
    dir=$(ls -d "$ROOT"/projects/*-"$slug")
    grep -q '^- Effort: quick' "$dir/BRIEF.md" && grep -q 'Effort: quick' "$dir/REVIEW.md" && [ -f "$dir/STYLE_PRESET.md" ] \
      && ok "bin/vh new --effort quick --style" || bad "bin/vh new: effort or style not written into the project"
    rm -rf "$dir"
  else bad "bin/vh new math"; fi
  # tts picks the uv dependencies from --provider too (a fake uv prints the command instead of running it)
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); printf '#!/bin/sh\necho "$*"\n' > "$t/uv"; chmod +x "$t/uv"
  a=$(PATH="$t:$PATH" vh tts "$t" --provider edge --lang en; PATH="$t:$PATH" vh tts "$t" --provider=dashscope)
  case "$a" in *"--with edge-tts "*"--provider edge"*"--with dashscope "*) ok "tts --provider picks the provider's dependencies" ;;
    *) bad "tts --provider: uv got '$a'" ;; esac
  rm -rf "$t"
  # recipes: every recipe's frontmatter validates, list filters agree with the files, bad values are errors
  vh recipes check >/dev/null && ok "recipes check (frontmatter, README index, sketches)" || bad "bin/vh recipes check"
  a=$(vh recipes list --intent carry,enter --energy 5 --engine three --ids)
  if python3 - "$a" <<'PY'
import pathlib, re, sys   # the expectation, read straight from the files with plain regexes (not tools/recipes.py)
want = set()
for p in pathlib.Path("recipes").glob("*/*.md"):
    t = p.read_text(encoding="utf-8")
    f = lambda k: re.findall(r"[a-z0-9-]+", (re.search(rf"^{k}: (.*)$", t, re.M) or [None, ""])[1])
    e = [int(x) for x in f("energy")]
    if p.parent.name != "sequences" and e and {"carry", "enter"} & set(f("intent")) and min(e) <= 5 <= max(e) and "three" in f("engines"):
        want.add(f("id")[0])
got = set(sys.argv[1].split())
sys.exit(0 if want and got == want else 1)
PY
  then ok "recipes list --intent --energy --engine match the files"; else bad "recipes list filters: got '$(echo $a)'"; fi
  vh recipes list --intent no-such-intent >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "recipes list rejects an unknown vocabulary value" || bad "recipes list --intent no-such-intent exited $rc"
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  sed 's/^id: .*/id: ci-copy/' recipes/seam/flash-cut.md > "$t/ok.md"; sed 's/^energy: .*/energy: 9/' "$t/ok.md" > "$t/bad.md"
  a=$(vh recipes check "$t/bad.md" 2>&1); rc=$?
  vh recipes check "$t/ok.md" >/dev/null && [ $rc = 1 ] && case "$a" in *energy*) true ;; *) false ;; esac \
    && ok "recipes check passes a valid copy and names the bad field" || bad "recipes check on a copy (bad one exited $rc)"
  rm -rf "$t"
  if ! command -v ffmpeg >/dev/null; then skip "mux / gif smoke" "ffmpeg not installed"; return; fi
  # subtitle languages come from the file name, never from folders (a home dir like /home/zhang used to tag everything chi)
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); mkdir -p "$t/zhang/en.v1.2"
  ffmpeg -nostdin -v error -f lavfi -i color=c=black:s=64x64:d=1 -pix_fmt yuv420p -f mp4 "$t/zhang/en.v1.2/final" \
    && ffmpeg -nostdin -v error -f lavfi -i sine=d=0.5 "$t/a.wav" \
    && printf '1\n00:00:00,000 --> 00:00:00,900\nhi\n' | tee "$t/zhang/captions.en.srt" "$t/zhang/captions.zh.srt" "$t/zhang/en.v1.2/subs.srt" >/dev/null
  if vh mux "$t/zhang/en.v1.2/final" "$t/a.wav" "$t/out.mp4" "$t/zhang/captions.en.srt" "$t/zhang/captions.zh.srt" "$t/zhang/en.v1.2/subs.srt" >/dev/null; then
    langs=$(ffprobe -v error -select_streams s -show_entries stream_tags=language -of csv=p=0 "$t/out.mp4" | tr '\n' ' ')
    [ "$langs" = "eng chi und " ] && ok "mux tags subtitle languages by file name" || bad "mux subtitle languages: got '$langs', want 'eng chi und'"
    a=$(ffprobe -v error -select_streams a -show_entries stream=duration -of csv=p=0 "$t/out.mp4"); python3 -c "import sys; sys.exit(0 if abs(float('$a') - 1) < 0.05 else 1)" \
      && ok "mux pads short audio to the video length" || bad "mux audio duration $a, want 1.0"
  else bad "bin/vh mux"; fi
  # no subtitle files: an empty array under set -u, which bash before 4.4 (macOS /bin/bash) treats as unbound
  vh mux "$t/zhang/en.v1.2/final" "$t/a.wav" "$t/out-nosubs.mp4" >/dev/null && [ -s "$t/out-nosubs.mp4" ] \
    && ok "mux without subtitle files" || bad "bin/vh mux without subtitle files"
  vh gif "$t/zhang/en.v1.2/final" 64 5 >/dev/null && [ -f "$t/zhang/en.v1.2/final.gif" ] && ok "gif names the output after the file, not a dotted folder" || bad "bin/vh gif output name"
  rm -rf "$t"
}

case "${1:-all}" in
  --smoke) smoke_checks ;;
  --committed)   # exactly what a push would send: HEAD in a clean temporary checkout, uncommitted changes left out
    w="$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")/head"; git worktree add -q --detach "$w" HEAD || exit 2
    (cd "$w" && tools/ci.sh); rc=$?; git worktree remove --force "$w"; rmdir "$(dirname "$w")"; exit $rc ;;
  all) static_checks; doc_checks; smoke_checks ;;
  *) echo "usage: tools/ci.sh [--smoke | --committed]"; exit 2 ;;
esac
[ $fails = 0 ] && ok "all checks passed" || printf '\033[31m%s check(s) failed\033[0m\n' "$fails"
exit $fails
