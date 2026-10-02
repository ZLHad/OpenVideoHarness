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
  n=0; while IFS= read -r f; do python3 -m py_compile "$f" 2>/dev/null || { bad "py_compile $f"; n=$((n + 1)); }; done < <(files 'tools/*.py' 'styles/_swatch/*.py' 'styles/*/swatch.py')
  [ $n = 0 ] && ok "python syntax"
  if python3 -m pyflakes --version >/dev/null 2>&1; then
    if out=$(files 'tools/*.py' 'styles/_swatch/*.py' 'styles/*/swatch.py' | xargs python3 -m pyflakes 2>&1); then ok "pyflakes"; else echo "$out"; bad "pyflakes"; fi
  else skip "pyflakes" "pip install pyflakes"; fi
  # Blender style scenes: the static check render.sh runs before Blender (no os, subprocess, open, random, handlers …),
  # and the GPL header every file that imports bpy carries (engines/blender.md, "许可证")
  n=0; while IFS= read -r f; do
    python3 styles/_swatch/blender_prep.py scan "$f" || { bad "blender_prep.py scan $f"; n=$((n + 1)); }
  done < <(files 'styles/*/swatch.py')
  out=$(files '*.py' | python3 -c '
import ast, sys
BLENDER = {"bpy", "bmesh", "mathutils", "bpy_extras", "gpu", "gpu_extras", "freestyle", "bl_math", "idprop", "aud", "imbuf", "blf", "bgl"}
for f in sys.stdin.read().splitlines():
    src = open(f, encoding="utf-8").read()
    try: tree = ast.parse(src, f)
    except SyntaxError: continue
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    mods |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    if mods & BLENDER and "SPDX-License-Identifier: GPL-3.0-or-later" not in "".join(src.splitlines(True)[:3]): print(f)
')
  [ -z "$out" ] || { echo "$out" | sed 's/$/: imports a Blender module but has no GPL-3.0-or-later SPDX header in its first 3 lines/'; n=$((n + 1)); bad "GPL header on Blender scripts"; }
  [ $n = 0 ] && ok "Blender scenes: static check and GPL headers"
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
  local slug="ci-smoke-$$" dir t rc langs a h o
  vh help >/dev/null && vh --help >/dev/null && ok "bin/vh help exits 0" || bad "bin/vh help"
  vh no-such-command >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "unknown command exits 1" || bad "unknown command exited $rc"
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")   # a throwaway HOME: an old bin/vh would install the skill for a bad target
  HOME="$t" vh install-skill no-such-target >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "install-skill rejects unknown targets" || bad "install-skill bad target exited $rc"
  rm -rf "$t"
  vh types >/dev/null && vh effort quick >/dev/null && vh style list >/dev/null && ok "types · effort · style list" || bad "types / effort / style list"
  # -h prints a usage and exits 0 without running the command (setup -h used to install everything, sync-agents -h rewrote
  # AGENTS.md, and others took -h as a video, project or preset name). Every dispatched command without a help of its own
  # is tried, on a copy of bin/vh whose ROOT has only tools/: if the check ever broke, setup would stop at its first cd
  local cmds n
  cmds=$(python3 - <<'PY'
import re, sys
src = open("bin/vh", encoding="utf-8").read()
block = src[src.index('case "${1:-help}" in'):]
block = block[:block.index("\nesac")]
cmds = {c for pat in re.findall(r"(?:^|;;)\s*([a-z|-]+)\)", block, re.M) for c in pat.split("|") if c and not c.startswith("-")} - {"help"}
own = set(re.search(r'case "\$1" in ([a-z|-]+)\) ;;   # these print their own', src).group(1).split("|"))
if own - cmds: sys.exit(f"own-help list names commands bin/vh does not dispatch: {sorted(own - cmds)}")
print(" ".join(sorted(cmds - own)))
PY
) || bad "bin/vh's own-help list"
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); mkdir "$t/bin"; cp bin/vh "$t/bin/vh"; ln -s "$ROOT/tools" "$t/tools"
  rc=0; for a in $cmds "style check"; do
    for h in -h --help; do
      # shellcheck disable=SC2086   # "style check" is two words on purpose
      o=$(HOME="$t" "$VH_BASH" "$t/bin/vh" $a "$h" 2>&1) && case "$o" in "usage: bin/vh $a "*) continue ;; esac
      bad "bin/vh $a $h: '$(printf '%s' "$o" | head -1)'"; rc=1
    done
  done; rm -rf "$t"
  n=$(printf '%s\n' $cmds | grep -c .)
  if [ $rc = 1 ]; then :; elif [ "$n" -gt 15 ]; then ok "-h and --help print a usage for the $n commands without a help of their own, and style check"
  else bad "only $n commands found in bin/vh's dispatch for the -h check"; fi
  # a project: effort and style are written in, and the quick gate waiver is recorded
  dir=$(ls -d "$ROOT"/projects/*-"$slug" 2>/dev/null); [ -z "$dir" ] || rm -rf "$dir"
  if vh new math "$slug" --effort quick --style dark-math >/dev/null; then
    dir=$(ls -d "$ROOT"/projects/*-"$slug")
    grep -q '^- Effort: quick' "$dir/BRIEF.md" && grep -q 'Effort: quick' "$dir/REVIEW.md" && [ -f "$dir/style-refs/dark-math/STYLE.md" ] \
      && grep -q '^- Style refs (repo presets): `styles/dark-math`' "$dir/BRIEF.md" && ! grep -q '^## Style preset' "$dir/BRIEF.md" \
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
  sed 's/^qa: .*/qa: {peak:4}/' "$t/ok.md" > "$t/yaml.md"   # YAML reads {peak:4} as one key, "peak:4"
  a=$(vh recipes check "$t/yaml.md" 2>&1); rc=$?
  [ $rc = 1 ] && case "$a" in *"space after"*) true ;; *) false ;; esac \
    && ok "recipes check refuses frontmatter that YAML would read differently" || bad "recipes check on {peak:4} exited $rc"
  vh recipes check --json >/dev/null 2>&1; rc=$?
  [ $rc = 2 ] && ok "recipes check treats an option as bad usage" || bad "recipes check --json exited $rc"
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

# scaffolding and the decision pictures (bin/vh storyboard, rhythm, style compare/apply, cover-preview, music --roll/--length)
decision_checks() {
  local t p a rc out
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  # new: --dir and $OVH_PROJECTS make the project outside the harness; quick does not promise a review stop
  a=$(vh new math ci-dir --dir "$t/elsewhere" --effort quick 2>&1); rc=$?
  p=$(ls -d "$t"/elsewhere/*-ci-dir 2>/dev/null)
  if [ $rc = 0 ] && [ -n "$p" ] && [ -z "$(ls -d "$ROOT"/projects/*-ci-dir 2>/dev/null)" ]; then ok "new --dir makes the project in that folder"; else bad "new --dir: rc $rc, made '$p'"; fi
  if [ -z "$p" ] || [ ! -d "$p" ]; then   # everything below writes into $p: never let it fall back to /
    bad "decision checks stopped: no project to work in"; rm -rf "$t"; return; fi
  case "$a" in *"stops for your review"*) bad "new --effort quick still says it stops for review" ;; *"renders straight through"*) ok "new --effort quick does not promise a review stop" ;;
    *) bad "new --effort quick: no next-step line in '$a'" ;; esac
  OVH_PROJECTS="$t/env" vh new math ci-env >/dev/null 2>&1 && [ -f "$(ls -d "$t"/env/*-ci-env 2>/dev/null)/BRIEF.md" ] && ok "OVH_PROJECTS sets where projects go" || bad "OVH_PROJECTS ignored"
  vh new math ci-x --aspect 16:9 >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "new --aspect is refused for a non-HyperFrames type" || bad "new math --aspect exited $rc"
  vh new short ci-x --aspect 4:3 >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "new --aspect rejects 4:3" || bad "new --aspect 4:3 exited $rc"
  a=$(vh new handdrawn ci-x --res 4k 2>&1); rc=$?; [ $rc = 1 ] && case "$a" in *"no 4K output"*) true ;; *) false ;; esac && ok "new --res 4k is refused for the hand-drawn engine" || bad "new handdrawn --res 4k exited $rc: $a"
  a=$(vh new short ci-x --watch tv 2>&1); rc=$?; [ $rc = 1 ] && case "$a" in *"unknown --watch"*) true ;; *) false ;; esac && ok "new --watch rejects an unknown target" || bad "new --watch tv exited $rc: $a"
  a=$(vh new short ci-x --watch feed 2>&1); rc=$?; [ $rc = 1 ] && case "$a" in *"already --watch phone"*) true ;; *) false ;; esac && ok "new refuses a feed target for a vertical frame" || bad "new short --watch feed exited $rc: $a"
  a=$(vh new promo ci-x --watch phone 2>&1); rc=$?; [ $rc = 1 ] && case "$a" in *"--watch feed"*) true ;; *) false ;; esac && ok "new refuses a phone target for a landscape frame" || bad "new promo --watch phone exited $rc: $a"
  vh new math ci-x --watch phone >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "new refuses a phone target for a Manim (landscape) type" || bad "new math --watch phone exited $rc"
  for bad_style in "dark-math,_swatch" "Dark-Math" "../styles/ink-wash" ","; do
    vh new math ci-x --style "$bad_style" >/dev/null 2>&1; rc=$?; [ $rc = 1 ] || bad "new --style '$bad_style' exited $rc"; done
  ok "new --style rejects a bad name anywhere in the list, paths and an empty list"
  [ -z "$(ls -d "$ROOT"/projects/*-ci-x 2>/dev/null)" ] || bad "a refused new left a project behind"
  # new: where it is watched and the output resolution land in the BRIEF (defaults from the frame, flags override)
  if grep -q '^- Watch on: desktop' "$p/BRIEF.md" && grep -q '^- Resolution: 1080p' "$p/BRIEF.md" \
    && OVH_PROJECTS="$t/w" vh new math ci-w --watch feed --res 4k >/dev/null 2>&1 \
    && grep -q '^- Watch on: feed' "$(ls -d "$t"/w/*-ci-w)/BRIEF.md" && grep -q '^- Resolution: 4k' "$(ls -d "$t"/w/*-ci-w)/BRIEF.md" \
    && OVH_PROJECTS="$t/w2" vh new edit ci-e --res 4K >/dev/null 2>&1 && grep -q '^- Watch on: phone' "$(ls -d "$t"/w2/*-ci-e)/BRIEF.md" \
    && grep -q '^- Resolution: 4k' "$(ls -d "$t"/w2/*-ci-e)/BRIEF.md"; then ok "new writes Watch on and Resolution into the BRIEF (defaults, flags, the 4K alias)"
  else bad "new: Watch on / Resolution missing or wrong in the BRIEF"; fi
  # style apply: presets are references; two attach side by side, re-attaching one adds nothing; by name under OVH_PROJECTS
  vh style apply blueprint "$p" >/dev/null && vh style apply ink-wash "$p" >/dev/null && OVH_PROJECTS="$t/elsewhere" vh style apply ink-wash ci-dir >/dev/null
  if grep -q '^- Style refs (repo presets): `styles/blueprint`, `styles/ink-wash`  <!--' "$p/BRIEF.md" && ! grep -q '^## Style preset' "$p/BRIEF.md" \
    && [ "$(grep -c '^> 参考的风格预设：`styles/blueprint`、`styles/ink-wash`' "$p/STYLE.md")" = 1 ] && [ "$(grep -c '风格参考 · ' "$p/DECISIONS.md")" = 2 ] \
    && [ -f "$p/style-refs/blueprint/tokens.json" ] && [ -f "$p/style-refs/ink-wash/STYLE.md" ]; then ok "style apply attaches presets as references, side by side, without repeats"
  else bad "style apply: references missing, repeated, or an instruction block pasted into the BRIEF"; fi
  # a comma list in one call, and a project made the old way (STYLE_PRESET.md + a pasted block + the 为底 pointer) keeps its base as a reference
  if OVH_PROJECTS="$t/m" vh new math ci-m >/dev/null 2>&1; then
    q=$(ls -d "$t"/m/*-ci-m)
    cp "$ROOT/styles/cutout-jazz/STYLE.md" "$q/STYLE_PRESET.md"; cp "$ROOT/styles/cutout-jazz/tokens.json" "$q/style.tokens.json"
    printf '\n\n## Style preset: cutout-jazz\n\n```text\nold block\n```\n' >> "$q/BRIEF.md"
    { printf '> 本项目以风格预设 `styles/cutout-jazz` 为底：先读 `STYLE_PRESET.md`。\n\n'; cat "$q/STYLE.md"; } > "$q/STYLE.md.new" && mv "$q/STYLE.md.new" "$q/STYLE.md"
    vh style apply blueprint,ink-wash "$q" >/dev/null 2>&1
    if [ -f "$q/style-refs/cutout-jazz/STYLE.md" ] && [ -f "$q/style-refs/cutout-jazz/tokens.json" ] && [ ! -e "$q/STYLE_PRESET.md" ] \
      && grep -q '^- Style refs (repo presets): `styles/cutout-jazz`, `styles/blueprint`, `styles/ink-wash`' "$q/BRIEF.md" \
      && ! grep -q '^## Style preset' "$q/BRIEF.md" && ! grep -q '为底' "$q/STYLE.md" && [ "$(grep -c '风格参考 · ' "$q/DECISIONS.md")" = 3 ]; then
      ok "style apply a,b: one call attaches both; an old base preset becomes a reference"
    else bad "style apply: comma list or migration of an old project's preset failed"; fi
  else bad "new math ci-m failed"; fi
  vh style apply no-such-style "$p" >/dev/null 2>&1; rc=$?; [ $rc = 1 ] && ok "style apply rejects an unknown preset" || bad "style apply unknown preset exited $rc"
  # readcheck: a budget, and the timed text of a composition without a browser
  a=$(vh readcheck --budget 3.2)
  case "$a" in *"up to 7 CJK"*"up to 28 CJK"*) ok "readcheck --budget" ;; *) bad "readcheck --budget 3.2 said: $a" ;; esac
  printf '%s\n' '<html><body><div id="root" data-composition-id="m" data-start="0" data-duration="10">' \
    '<section id="s" class="clip" data-start="0" data-duration="10"><h1 id="t">script-driven</h1></section>' \
    '<div id="c1" class="clip" data-start="1" data-duration="4"><span>四个汉字</span></div>' \
    '<div id="c2" class="clip" data-start="6" data-duration="1.2">太短了的字</div></div><script>var x="<div>";</script></body></html>' > "$p/index.html"
  a=$(vh readcheck "$p/index.html"); rc=$?
  case "$rc:$a" in 1:*"OK  c1"*"BAD c2"*"NOT checked: 1 text block"*) ok "readcheck reads a composition's clips (and says what it left out)" ;; *) bad "readcheck index.html (rc $rc): $a" ;; esac
  vh readcheck --export "$p" >/dev/null && grep -q '"id": "c2"' "$p/texts.json" && { vh readcheck "$p" --export >/dev/null 2>&1; [ $? = 2 ]; } \
    && ok "readcheck --export writes texts.json and will not overwrite it" || bad "readcheck --export"
  # HyperFrames timing the way HyperFrames resolves it: "id", "id+n", a sub-composition's <template>, a typo'd reference
  mkdir -p "$t/rel/sub"
  printf '%s\n' '<html><body><div id="root" data-composition-id="m" data-start="0" data-duration="12">' \
    '<div id="a" data-start="1" data-duration="3"><h1>第一句标题文字</h1></div>' \
    '<div id="b" data-start="a" data-duration="0.8"><p>第二句</p></div>' '<div id="c" data-start="b + 0.5" data-duration="1"><p>第三句</p></div>' \
    '<div id="x" data-start="typo" data-duration="1"><p>没有这个片段</p></div>' \
    '<div id="host" data-start="6" data-duration="4" data-composition-src="sub/child.html"></div></div></body></html>' > "$t/rel/index.html"
  printf '%s\n' '<template id="t"><div data-composition-id="child" data-duration="4">' \
    '<div id="k1" data-start="0.5" data-duration="1"><span>子合成里的字</span></div></div></template>' > "$t/rel/sub/child.html"
  a=$(vh readcheck "$t/rel/index.html")
  case "$a" in *"a "*"1.00–   4.00s"*"b "*"4.00–   4.80s"*"c "*"5.30–   6.30s"*"k1"*"6.50–   7.50s"*"NOT checked"*"typo"*)
      case "$a" in *"every timed text"*) bad "readcheck claims it checked everything: $a" ;; *) ok "readcheck resolves relative starts and sub-composition templates" ;; esac ;;
    *) bad "readcheck relative / template timing: $a" ;; esac
  # with the project's own hyperframes the spans are HyperFrames' (a stand-in prints its timeline), from a relative path too
  mkdir -p "$t/rel/node_modules/.bin"
  cat > "$t/rel/node_modules/.bin/hyperframes" <<'SH'
#!/bin/sh
echo '{"timeline": {"tracks": [{"rows": [{"id": "a", "absStart": 2, "absEnd": 5.5, "file": "index.html"}]}]}}'
SH
  chmod +x "$t/rel/node_modules/.bin/hyperframes"
  a=$(cd "$t" && vh readcheck rel/index.html)
  case "$a" in *"a "*"2.00–   5.50s"*"HyperFrames' own timeline"*) ok "readcheck takes the spans from the project's hyperframes timeline" ;;
    *) bad "readcheck with a project hyperframes: $a" ;; esac
  if ! command -v uv >/dev/null || ! command -v ffmpeg >/dev/null; then skip "storyboard · rhythm · style compare · cover-preview · music --roll" "needs uv and ffmpeg"; rm -rf "$t"; return; fi
  # a small project: 3 shots (one over the type's 5 s, one unsure), a video, narration, captions (one too short) and a score
  printf '%s\n' '# BRIEF' '<!-- from 02-knowledge-short.md -->' > "$p/BRIEF.md"; rm -f "$p/texts.json"
  printf '%s\n' '[{"id": "S1", "start": 0, "end": 2, "segment": "hook", "reads": "a title"},' \
    '{"id": "S2", "start": 2, "end": 8.5, "segment": "body", "reads": ["a long shot", "second read"], "unsure": "too slow?"},' \
    '{"id": "S3", "start": 8.5, "end": 10, "segment": "body", "reads": "the end"}]' > "$p/shots.json"
  ffmpeg -nostdin -v error -f lavfi -i testsrc=s=320x180:d=10:r=10 -pix_fmt yuv420p "$p/out/final.mp4"
  printf '%s\n' '{"segments": [{"id": "l1", "text": "first line of narration", "start": 0.2, "end": 3.9}, {"id": "l2", "text": "second", "start": 4.2, "end": 9.5}]}' > "$p/audio/timeline.json"
  printf '%s\n' '[{"id": "l1", "start": 0.2, "end": 3.9, "en": ["first line of narration"]}, {"id": "l2", "start": 4.2, "end": 5.0, "en": ["second"]}]' > "$p/audio/captions.json"
  printf '%s\n' '{"bpm": 120, "key": "C", "mode": "major", "seed": 1, "sections": [{"name": "a", "bars": 2, "chords": ["I", "V"], "layers": ["pad"]},' \
    '{"name": "b", "bars": 3, "chords": ["vi", "IV", "V"], "layers": ["pad"]}], "parts": [{"inst": "piano", "pattern": [[0, 1, "c0"], [1, 1, "c2"], [2, 2, "c1"]]}]}' > "$p/audio/score.json"
  if vh music "$p/audio/score.json" "$p/audio/music.wav" --length auto --roll >/dev/null; then
    a=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$p/audio/music.wav")
    python3 -c "import json, sys; b = json.load(open(sys.argv[1])); sys.exit(0 if abs(float(sys.argv[2]) - 10) < 0.01 and b['fade']['end'] == 10.0 and max(b['beats']) < 10 else 1)" "$p/audio/music.beats.json" "$a" \
      && ok "music --length auto ends where the last bar ends, with a fade" || bad "music --length auto: $a s, beat map $(head -c 200 "$p/audio/music.beats.json")"
    [ -s "$p/audio/music.roll/overview.png" ] && [ -s "$p/audio/music.roll/01-piano-0.png" ] && ok "music --roll draws an overview and a page per part" || bad "music --roll pictures missing"
    vh music "$p/audio/score.json" "$t/m7.wav" --length 7 >/dev/null && a=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$t/m7.wav") \
      && python3 -c "import sys; sys.exit(0 if abs(float(sys.argv[1]) - 7) < 0.01 else 1)" "$a" && ok "music --length 7 trims the render to 7 s" || bad "music --length 7 gave '$a' s"
  else bad "bin/vh music --length auto --roll"; fi
  # at 60 bpm a bar is 4 s: the fade still starts on a beat, 1-3 s before the end
  printf '%s\n' '{"bpm": 60, "key": "C", "mode": "major", "seed": 1, "sections": [{"name": "a", "bars": 4, "chords": ["I", "V", "vi", "IV"], "layers": ["pad"]}]}' > "$t/s60.json"
  vh music "$t/s60.json" "$t/m60.wav" --length 9.5 >/dev/null \
    && python3 -c "import json, sys; f = json.load(open(sys.argv[1]))['fade']; s = f['start']; sys.exit(0 if s == round(s) and 6.5 <= s <= 8.5 and f['end'] == 9.5 else 1)" "$t/m60.beats.json" \
    && ok "music --length at 60 bpm fades from a beat" || bad "music --length 9.5 at 60 bpm: $(head -c 300 "$t/m60.beats.json" 2>/dev/null)"
  # a section stop, a cresc and a pickup (motif-era scores): --roll draws them, --length fades from a beat and keeps the stop: hit
  printf '%s\n' '{"bpm": 100, "key": "D", "mode": "major", "seed": 1, "sections": [{"name": "a", "bars": 2, "chords": ["I", "V"], "stop": {"at": "2:3", "keep": ["pad"]}},' \
    '{"name": "b", "bars": 2, "chords": ["IV", "I"]}], "parts": [{"inst": "strings", "id": "pad", "figure": "sustain", "octave": 3, "gain_db": -14},' \
    '{"inst": "brass", "sections": ["a"], "octave": 4, "by_section": {"a": {"cresc": [-8, 0]}}, "pattern": [[0, 1, "d1"], [1, 1, "d3"], [2, 1, "d5"], [3, 1, "d3"]]},' \
    '{"inst": "celesta", "sections": ["b"], "octave": 5, "loop": 2, "pattern": [[-1, 1, "d5"], [0, 2, "d1"], [2, 2, "d3"]]}]}' > "$t/stop.json"
  if vh music "$t/stop.json" "$t/stop.wav" --roll --length 8 >/dev/null && [ -s "$t/stop.roll/overview.png" ] && [ -s "$t/stop.roll/03-celesta-0.png" ] \
    && python3 -c "import json, sys; b = json.load(open(sys.argv[1])); f = b['fade']; sys.exit(0 if f['end'] == 8.0 and any(abs(f['start'] - x) < 1e-6 for x in b['beats']) and [h['t'] for h in b['hits'] if h['what'] == 'stop:a'] == [3.6] else 1)" "$t/stop.beats.json"
  then ok "music --roll and --length with a section stop, a cresc and a pickup"; else bad "music with a stop: $(head -c 300 "$t/stop.beats.json" 2>/dev/null)"; fi
  # storyboard: a page per segment + an overview; the unsure and the long shot are flagged; the same input, the same bytes
  # review.json is tools/review.py's shape: a gate JSON that includes it builds the page
  if vh storyboard "$p" >/dev/null && mkdir -p "$p/out/review" \
    && printf '%s\n' '{"summary": "ci", "decisions": [], "include": "out/check/storyboard/review.json"}' > "$p/out/review/gate-2.json" \
    && a=$(vh review "$p" 2 2>&1) && grep -q '"frame": "out/check/storyboard/frames/S2.png"' "$p/out/check/storyboard/review.json"; then
    case "$a" in *"2 segment(s)"*"3 shot(s)"*"S2"*) ok "storyboard review.json feeds bin/vh review through include" ;; *) bad "review with include said: $a" ;; esac
  else bad "storyboard review.json + bin/vh review: $a"; fi
  # a duplicate id stops it; a shot the video never reaches gets a grey tile, not the clamped last frame
  printf '%s\n' '[{"id": "D", "start": 0, "end": 1}, {"id": "D", "start": 1, "end": 2}]' > "$t/dup.json"
  vh storyboard "$p" --shots "$t/dup.json" >/dev/null 2>&1; rc=$?; [ $rc != 0 ] && ok "storyboard rejects a duplicate shot id" || bad "storyboard took a duplicate id"
  printf '%s\n' '[{"id": "P1", "start": 0, "end": 4}, {"id": "P2", "start": 4, "end": 9}, {"id": "P3", "start": 9, "end": 14}]' > "$t/past.json"
  a=$(vh storyboard "$p" --shots "$t/past.json" --out "$t/sbpast" 2>&1)
  case "$a" in *"past the end of out/final.mp4"*"P3"*) [ ! -f "$t/sbpast/frames/P3.png" ] && ok "storyboard leaves a shot past the end of the video grey" || bad "storyboard grabbed a frame past the end" ;;
    *) bad "storyboard past the end: $a" ;; esac
  # inside a uv project (bin/vh new math suggests uv init) the tools still run: uv must not sync that project
  mkdir -p "$t/uvp" && printf '%s\n' '[project]' 'name = "uvp"' 'version = "0"' 'dependencies = ["this-package-does-not-exist-xyz==1.0"]' > "$t/uvp/pyproject.toml"
  (cd "$t/uvp" && vh storyboard "$p" >/dev/null 2>&1) && [ ! -e "$t/uvp/uv.lock" ] && ok "bin/vh's uv runs ignore the project they are started in" || bad "uv run synced the surrounding project"
  # 26 shots at 6 a page split evenly (5 5 5 5 6), not 6 6 6 6 and a page of 2
  python3 -c "import json; print(json.dumps([{'id': 'E%02d' % i, 'start': i * 0.3, 'end': i * 0.3 + 0.3} for i in range(26)]))" > "$t/even.json"
  vh storyboard "$p" --shots "$t/even.json" --out "$t/sbeven" >/dev/null 2>&1 \
    && python3 -c "import json, sys; i = json.load(open(sys.argv[1])); sys.exit(0 if [len(x['shots']) for x in i['pages']] == [5, 5, 5, 5, 6] else 1)" "$t/sbeven/index.json" \
    && ok "storyboard splits 26 shots 5-5-5-5-6" || bad "storyboard page split: $(head -c 400 "$t/sbeven/index.json" 2>/dev/null)"
  if vh storyboard "$p" >/dev/null && cp "$p/out/check/storyboard/overview.png" "$t/ov1.png" && vh storyboard "$p" >/dev/null; then
    [ -s "$p/out/check/storyboard/01-hook.png" ] && [ -s "$p/out/check/storyboard/02-body.png" ] \
      && python3 -c "import json, sys; i = json.load(open(sys.argv[1])); p = i['pages'][1]; sys.exit(0 if p['unsure'] == ['S2'] and p['long'] == ['S2'] and i['limit_s'] == 5 else 1)" "$p/out/check/storyboard/index.json" \
      && ok "storyboard: a page per segment, the unsure and the too-long shot flagged" || bad "storyboard pages or flags: $(cat "$p/out/check/storyboard/index.json")"
    cmp -s "$t/ov1.png" "$p/out/check/storyboard/overview.png" && ok "storyboard is deterministic" || bad "storyboard gave different bytes on a second run"
  else bad "bin/vh storyboard"; fi
  a=$(vh rhythm "$p")
  case "$a" in *"S2 6.5 s > 5 s"*"l2"*"0.8 s < 1.8 s"*) [ -s "$p/out/check/rhythm.png" ] && ok "rhythm: long shot and short caption in red" || bad "rhythm.png missing" ;; *) bad "rhythm said: $a" ;; esac
  vh rhythm "$p" --segment body >/dev/null && [ -s "$p/out/check/rhythm-body.png" ] && ok "rhythm --segment zooms in" || bad "rhythm --segment"
  printf '%s\n' '{"segments": [{"id": "e1", "text": "an English line", "start": 0.5, "end": 2.0}]}' > "$p/audio/timeline.en.json"
  a=$(vh rhythm "$p" --lang en)
  case "$a" in *"from: "*"audio/timeline.en.json"*) ok "rhythm --lang en reads timeline.en.json" ;; *) bad "rhythm --lang en: $a" ;; esac
  vh style compare blueprint,ink-wash --out "$t/sc.png" >/dev/null && vh style compare blueprint,ink-wash --frame 2 --out "$t/sc2.png" >/dev/null && [ -s "$t/sc.png" ] && [ -s "$t/sc2.png" ] \
    && ok "style compare: posters and swatch frames" || bad "bin/vh style compare"
  vh style compare blueprint,no-such >/dev/null 2>&1; rc=$?; [ $rc != 0 ] && ok "style compare rejects an unknown preset" || bad "style compare accepted an unknown preset"
  out=$(vh cover-preview "$ROOT/styles/blueprint/media/poster.jpg" --out "$t/cover.png")
  case "$out" in *"smallest text"*|*"no text line found"*) [ -s "$t/cover.png" ] && ok "cover-preview draws the feed sizes and a legibility line" || bad "cover-preview wrote nothing" ;; *) bad "cover-preview said: $out" ;; esac
  rm -rf "$t"
}

case "${1:-all}" in
  --smoke) smoke_checks; decision_checks ;;
  --committed)   # exactly what a push would send: HEAD in a clean temporary checkout, uncommitted changes left out
    w="$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")/head"; git worktree add -q --detach "$w" HEAD || exit 2
    (cd "$w" && tools/ci.sh); rc=$?; git worktree remove --force "$w"; rmdir "$(dirname "$w")"; exit $rc ;;
  all) static_checks; doc_checks; smoke_checks; decision_checks ;;
  *) echo "usage: tools/ci.sh [--smoke | --committed]"; exit 2 ;;
esac
[ $fails = 0 ] && ok "all checks passed" || printf '\033[31m%s check(s) failed\033[0m\n' "$fails"
exit $fails
