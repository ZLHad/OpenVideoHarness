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
unset CDPATH   # an exported one could send this relative cd elsewhere (as in bin/vh)
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
ROOT=$(pwd)
VH_BASH=${VH_BASH:-bash}
export OVH_LOCAL_MD=/dev/null/LOCAL.md   # this machine's LOCAL.md stays out of every check (one that needs it writes its own)
fails=0
ok() { printf '\033[32m✓\033[0m %s\n' "$*"; }
bad() { printf '\033[31m✗\033[0m %s\n' "$*"; fails=$((fails + 1)); }
skipped=""
skip() { printf '\033[33m-\033[0m %s (skipped: %s)\n' "$1" "$2"; skipped="$skipped${skipped:+, }$1"; }
files() { git ls-files "$@" | grep -v -E '^references/|(^|/)node_modules/|\.min\.js$'; }

static_checks() {
  local f n out
  # shell: parse with the bash that will run it, lint, and ban commands that only exist on one platform
  n=0; while IFS= read -r f; do "$VH_BASH" -n "$f" || { bad "bash -n $f"; n=$((n + 1)); }; done < <(files bin/vh '*.sh')
  [ $n = 0 ] && ok "shell syntax ($("$VH_BASH" -c 'echo $BASH_VERSION'))"
  if command -v shellcheck >/dev/null; then
    if out=$(files bin/vh '*.sh' | xargs shellcheck -S warning 2>&1); then ok "shellcheck -S warning"; else echo "$out"; bad "shellcheck"; fi
  else skip "shellcheck" "not installed; CONTRIBUTING.md shows how to run it through uv"; fi
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
  else skip "pyflakes" "not installed; CONTRIBUTING.md shows how to run it through uv"; fi
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
  if python3 tools/audio/test_music_clock.py; then ok "music clock: JS/Python agree on bar time and invalid maps"; else bad "music clock"; fi
  if python3 tools/audio/test_time_map.py; then ok "time map: JS/Python agree on maps and every kind of time reference; events.json headers; time_map.py check"; else bad "time map"; fi
  # the example time-map solver (engines/canvas-film/examples): its synthetic spec solves to a map timemap check takes, and
  # a card's text made longer between two fixed points (a pin at 15 s, a segment end at 32 s) moves knots in that span alone
  local ex="$ROOT/engines/canvas-film/examples" d; d=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  if python3 "$ex/time-map-solve.py" "$ex/time-map-spec.json" "$d/a.map.json" >/dev/null && vh timemap check "$d/a.map.json" >/dev/null \
    && python3 - "$ex/time-map-solve.py" "$ex/time-map-spec.json" "$d" <<'PY'
import json, subprocess, sys
solve, spec, d = sys.argv[1:]
s = json.load(open(spec, encoding="utf-8"))
e = next(e for e in s["events"] if e["id"] == "d0505"); e["text"] += "，比去年同期高出一截"
json.dump(s, open(f"{d}/b.json", "w", encoding="utf-8"), ensure_ascii=False)
subprocess.run([sys.executable, solve, f"{d}/b.json", f"{d}/b.map.json"], check=True, stdout=subprocess.DEVNULL)
A, B = (json.load(open(f"{d}/{n}.map.json", encoding="utf-8")) for n in "ab")
out = lambda m: [k for k in m["knots"] if not 15 < k[0] < 32]
pins = lambda m: [(e["id"], e["t"]) for e in m["events"] if e["id"] in ("d0412", "d1010")]
sys.exit(0 if out(A) == out(B) and A["knots"] != B["knots"] and pins(A) == pins(B) == [("d0412", 15), ("d1010", 48)] else 1)
PY
  then ok "time-map solver example: its spec solves to a map timemap check takes; an edit between two pins moves that span's knots alone"
  else bad "time-map solver example (engines/canvas-film/examples/time-map-solve.py)"; fi
  rm -rf "$d"
  # media: videos live in the GitHub release "media" (tools/media.txt, tools/fetch_media.sh), so a clone stays small;
  # the style swatches (about 1 MB each, read by the tools) are the one exception. No file over 8 MB either.
  out=$(files | while IFS= read -r f; do
      lc=$(printf '%s' "$f" | tr '[:upper:]' '[:lower:]')   # [[ ]], not case: bash 3.2 can't parse case inside $( ); lower-cased: .GIF too
      if [[ ! "$f" =~ ^styles/[^/]+/media/swatch\.mp4$ && "$lc" =~ \.(mp4|mov|webm|mkv|gif)$ ]]; then echo "$f: a video (put it in the media release, see tools/fetch_media.sh)"; continue; fi
      if [ -f "$f" ]; then s=$(wc -c < "$f"); [ "$s" -gt 8000000 ] && echo "$f: $((s / 1000000)) MB, over 8 MB"; fi
    done)
  if [ -n "$out" ]; then echo "$out"; bad "videos or large files in git"; else ok "no videos or files over 8 MB in git"; fi
}

doc_checks() {
  local head out
  head=$(head -3 AGENTS.md)
  if [ "$(tail -n +4 AGENTS.md)" = "$(cat CLAUDE.md)" ] && [ -n "$head" ]; then ok "AGENTS.md generated from CLAUDE.md"
  else bad "AGENTS.md is out of sync with CLAUDE.md: run bin/vh sync-agents"; fi
  # the command table (tools/commands.json): its own rules, its stages those of playbook/01's 总表
  if out=$(python3 tools/commands.py check 2>&1); then ok "$out: each with a summary, when, stages (playbook/01's), reads, writes, usage; subcommands in their usage"
  else echo "$out"; bad "tools/commands.json"; fi
  # the table of outside modules (tools/modules.json): its own rules (commands that exist, adapters in the repo, keys as
  # variable names, probes over https with the key in a header), and its HyperFrames pin the one bin/vh and styles/_swatch install
  if out=$(python3 tools/doctor.py --check 2>&1) && python3 - <<'PY'
import json, re, sys
pins = set(re.findall(r"\$\{HYPERFRAMES_VERSION:-([0-9][0-9.]*)\}", open("bin/vh", encoding="utf-8").read()))
swatch = json.load(open("styles/_swatch/package.json", encoding="utf-8"))["devDependencies"]["hyperframes"]
table = next(m for m in json.load(open("tools/modules.json", encoding="utf-8"))["modules"] if m["name"] == "hyperframes")["version"]["pin"]
if not pins == {swatch} == {table}:
    sys.exit(f"HyperFrames pins differ: bin/vh {sorted(pins)}, styles/_swatch/package.json {swatch}, tools/modules.json {table}")
PY
  then ok "$out: each with a purpose, version, licence, needs, adapters in the repo and real commands; the HyperFrames pin is bin/vh's and styles/_swatch's"
  else echo "$out"; bad "tools/modules.json"; fi
  # every `bin/vh <command>` in the docs exists; the table names exactly the commands bin/vh dispatches, and CLAUDE.md's
  # 命令行 line is the table's (bin/vh sync-agents writes it)
  if python3 - <<'PY'
import json, re, subprocess, sys
src = open("bin/vh", encoding="utf-8").read()
block = src[src.index('case "${1:-help}" in'):]
block = block[:block.index("\nesac")]
cmds = {c for pat in re.findall(r"(?:^|;;)\s*([a-z|-]+)\)", block, re.M) for c in pat.split("|") if c and not c.startswith("-")}
cmds.discard("help")
table = {c.get("name") for c in json.load(open("tools/commands.json", encoding="utf-8")).get("commands", [])}
bad = []
if table != cmds:
    bad.append(f"tools/commands.json vs bin/vh dispatch: not in the table {sorted(cmds - table)}, not dispatched {sorted(table - cmds)}")
line = re.search(r"命令行：(.+)", open("CLAUDE.md", encoding="utf-8").read()).group(1)
want = subprocess.run([sys.executable, "tools/commands.py", "claude-line"], capture_output=True, text=True).stdout.strip()
if line != want:
    bad.append(f"CLAUDE.md's 命令行 line is not tools/commands.json's (bin/vh sync-agents writes it): {line!r} vs {want!r}")
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
  then ok "docs name only real bin/vh commands; tools/commands.json and CLAUDE.md's 命令行 line name the ones bin/vh dispatches"; else bad "docs vs bin/vh commands"; fi
}

readpath_report() {   # how much an agent reads before it starts, per effort level and type: printed as a baseline, no limit yet
  local out
  if out=$(python3 tools/readpath.py 2>&1); then printf '%s\n' "$out" | sed 's/^/  /'; ok "read path printed above (a baseline; no limit yet)"
  else echo "$out"; bad "tools/readpath.py"; fi
}

vh() { "$VH_BASH" "$ROOT/bin/vh" "$@"; }
smoke_checks() {
  local slug="ci-smoke-$$" dir t rc langs a h o u ad
  vh help >/dev/null && vh --help >/dev/null && ok "bin/vh help exits 0" || bad "bin/vh help"
  vh no-such-command >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "unknown command exits 2 (a usage error)" || bad "unknown command exited $rc"
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")   # a throwaway HOME: an old bin/vh would install the skill for a bad target
  HOME="$t" vh install-skill no-such-target >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "install-skill rejects unknown targets" || bad "install-skill bad target exited $rc"
  rm -rf "$t"
  vh types >/dev/null && vh effort quick >/dev/null && vh style list >/dev/null && ok "types · effort · style list" || bad "types / effort / style list"
  # effort: the table comes from playbook/01, the caps and the floors from CLAUDE.md (a renamed heading must not drop them)
  a=$(vh effort studio 2>&1)
  case "$a" in *"独立评审"*"评审有上限"*"任何档位都不降"*"bin/vh check"*) ok "effort studio prints its column, the review caps and the floors" ;;
    *) bad "effort studio: table, caps or floors missing" ;; esac
  # -h prints a usage and exits 0 without running the command (setup -h used to install everything, sync-agents -h rewrote
  # AGENTS.md, and others took -h as a video, project or preset name). Every dispatched command without a help of its own
  # is tried, on a copy of bin/vh whose ROOT has only tools/ and with uv and npm stubbed out: if the check ever broke, setup
  # would stop at its first cd and nothing would be downloaded
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
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); mkdir "$t/bin" "$t/stub"; cp bin/vh "$t/bin/vh"; ln -s "$ROOT/tools" "$t/tools"
  printf '#!/bin/sh\nexit 1\n' > "$t/stub/uv"; cp "$t/stub/uv" "$t/stub/npm"; chmod +x "$t/stub/uv" "$t/stub/npm"
  rc=0; for a in $cmds "style check"; do
    for h in -h --help; do
      # shellcheck disable=SC2086   # "style check" is two words on purpose
      o=$(HOME="$t" PATH="$t/stub:$PATH" "$VH_BASH" "$t/bin/vh" $a "$h" 2>&1) && case "$o" in "usage: bin/vh $a "*|"usage: bin/vh $a"|"usage: bin/vh $a"$'\n'*) continue ;; esac
      bad "bin/vh $a $h: '$(printf '%s' "$o" | head -1)'"; rc=1
    done
  done; rm -rf "$t"
  n=$(printf '%s\n' $cmds | grep -c .)
  if [ $rc = 1 ]; then :; elif [ "$n" -gt 5 ]; then ok "-h and --help print a usage for the $n commands without a help of their own, and style check"
  else bad "only $n commands found in bin/vh's dispatch for the -h check"; fi
  # the help is printed from tools/commands.json: bin/vh -h has a usage for every command there, bin/vh commands lists
  # each one once (--stage: a stage's, by its id or a part of its name, those listed under it first), --json the same in
  # the same order; a stage or an option it does not know is a usage error (2, stderr only), and so is a mistyped command,
  # with the nearest names. sync-agents, on a copy, writes CLAUDE.md's 命令行 line from the table, then AGENTS.md
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); mkdir "$t/bin"; cp bin/vh "$t/bin/vh"; ln -s "$ROOT/tools" "$t/tools"
  if python3 - "$VH_BASH" "$t" <<'PY'
import json, re, subprocess, sys
sh, t = sys.argv[1:3]
vh = lambda *a, bin="bin/vh": subprocess.run([sh, bin, *a], capture_output=True, text=True)
names = [c["name"] for c in json.load(open("tools/commands.json", encoding="utf-8"))["commands"]]
bad = []
h = vh("-h")
miss = [n for n in names if not re.search(rf"^  {re.escape(n)}( |$)", h.stdout, re.M)]
if h.returncode or miss:
    bad.append(f"bin/vh -h (exit {h.returncode}) has no usage for {miss}")
listed = re.findall(r"^  ([a-z][a-z-]*) ", vh("commands").stdout, re.M)
if sorted(listed) != sorted(names):
    bad.append(f"bin/vh commands lists {len(listed)} of the {len(names)} commands, or one twice")
j = json.loads(vh("commands", "--json").stdout)
if j.get("version") != 1 or [c["name"] for c in j["commands"]] != listed:
    bad.append("bin/vh commands --json is not the list's commands in its order")
keys = {"name", "summary", "when", "stages", "reads", "writes", "usage"}
if any(not keys <= set(c) for c in j["commands"]) or any(set(s) - {"id", "name", "note"} for s in j["stages"]):
    bad.append("bin/vh commands --json lacks a field or has an unknown one")
a, b = vh("commands", "--stage", "4", "--json").stdout, vh("commands", "--stage=时间", "--json").stdout
if a != b or json.loads(a).get("stage") != "4":
    bad.append("bin/vh commands: --stage 4 and --stage=时间 differ")
s3 = [c["name"] for c in json.loads(vh("commands", "--stage", "3", "--json").stdout)["commands"]]
if s3[:3] != ["recipes", "storyboard", "rhythm"] or "gate" not in s3:
    bad.append(f"bin/vh commands --stage 3: {s3}")
for args in (["--stage", "nope"], ["--stage"], ["--stage", "e"], ["--bogus"]):   # "e": Brief and Review, two stages
    r = vh("commands", *args)
    if r.returncode != 2 or r.stdout or not r.stderr:
        bad.append(f"bin/vh commands {' '.join(args)}: exit {r.returncode}, stdout {r.stdout[:40]!r}")
r = vh("comands")
if r.returncode != 2 or r.stdout or "did you mean commands" not in r.stderr:
    bad.append(f"bin/vh comands: exit {r.returncode}, {r.stderr[:80]!r}")
c = open("CLAUDE.md", encoding="utf-8").read()
open(f"{t}/CLAUDE.md", "w", encoding="utf-8").write(re.sub(r"命令行：.*", "命令行：doctor · setup", c, count=1))
want = subprocess.run([sys.executable, "tools/commands.py", "claude-line"], capture_output=True, text=True).stdout.strip()
r = vh("sync-agents", bin=f"{t}/bin/vh")
got = open(f"{t}/CLAUDE.md", encoding="utf-8").read()
agents = open(f"{t}/AGENTS.md", encoding="utf-8").read() if r.returncode == 0 else "\n\n\n"
if r.returncode or got != c.replace(re.search(r"命令行：.*", c).group(0), "命令行：" + want) or agents.split("\n", 3)[3] != got:
    bad.append(f"sync-agents (exit {r.returncode}) did not write the 命令行 line from the table, or AGENTS.md from CLAUDE.md")
print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
  then ok "bin/vh -h has a usage for each command of tools/commands.json, bin/vh commands lists each once (--stage by id or name, --json in the same order); a bad stage or option is 2 on stderr, a mistyped command 2 with the nearest name; sync-agents writes CLAUDE.md's 命令行 line from the table"
  else bad "the help and bin/vh commands from tools/commands.json"; fi
  rm -rf "$t"
  # doctor reads tools/modules.json. In a sandbox (stub programs on the PATH, fake keys, empty caches): a node under the
  # minimum and an ffmpeg without libx264 and ffprobe are said, a dated yt-dlp far over its age is outdated, a key is set
  # or not and its value never shown. --probe --offline answers the services from recorded responses: a key taken (and
  # the models bin/vh uses listed), MiniMax's refusal with its hint, a 401 whose message echoes the key masked (only the
  # status and the error code are said, no run of six of the key's characters), no key skipped. Live against two servers
  # on this machine: a redirect is not followed (the second server hears nothing) and a base address over plain http to
  # another host is not called. A module not made for this platform says what to use instead; a needed module that is not
  # usable takes the one needing it off ok (needs.programs, also checked in the table). Without python3 on the PATH,
  # bin/vh doctor still says node, ffmpeg, uv, git and Chrome and exits 0. Usage errors exit 2 before any probe;
  # bin/vh doctor --json on this machine lists every module
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  if python3 - "$VH_BASH" "$t" <<'PY'
import json, os, shutil, subprocess, sys
sh, t = sys.argv[1:3]
stub, rec = os.path.join(t, "stub"), os.path.join(t, "rec")
os.makedirs(stub); os.makedirs(rec)
for name, body in (("node", "echo v18.19.0"), ("ffmpeg", "echo 'ffmpeg version 7.1 Copyright (c) the FFmpeg developers'"),
                   ("yt-dlp", "echo 2020.01.01"), ("uv", 'case "$1" in run) exit 1 ;; esac; echo "uv 0.9.0"')):
    with open(os.path.join(stub, name), "w") as f:
        f.write("#!/bin/sh\n" + body + "\n")
    os.chmod(os.path.join(stub, name), 0o755)
keys = {"GEMINI_API_KEY": "ciK7Hq2Zt9Lm4Wp8Rs3Vb6Xy0Jg", "MINIMAX_API_KEY": "ciQ1Wz5Nx8Pc3Kd7Lf2Hm6Gy4Tq",
        "DASHSCOPE_API_KEY": "ciT4Yb9Rg2Vs6Jn1Uk5Ep8Dw3Zc"}
env = {"PATH": stub, "HOME": t, "HF_HOME": os.path.join(t, "hf"), **keys}
doc = lambda *a: subprocess.run([sys.executable, "tools/doctor.py", *a], capture_output=True, text=True, encoding="utf-8", env=env)
bad, outs = [], []
j = doc("--json"); outs += [j.stdout, j.stderr]
d = json.loads(j.stdout)
m = {x["name"]: x for x in d["modules"]}
if list(m) != [x["name"] for x in json.load(open("tools/modules.json", encoding="utf-8"))["modules"]]:
    bad.append("doctor --json does not list the table's modules in its order")
want = {"node": "outdated", "ffmpeg": "incomplete", "yt-dlp": "outdated", "python-packages": "missing", "gemini": "ok",
        "minimax": "ok", "elevenlabs": "no_key", "chrome": "missing"}
got = {k: m[k]["state"] for k in want}
if got != want:
    bad.append(f"doctor's states: {got}")
if "22 or newer" not in m["node"]["note"] or "libx264" not in m["ffmpeg"]["note"] or "ffprobe" not in m["ffmpeg"]["note"] \
        or "days old" not in m["yt-dlp"]["note"] or m["yt-dlp"]["status"] != "planned":
    bad.append(f"doctor's notes: {m['node']['note']!r}, {m['ffmpeg']['note']!r}, {m['yt-dlp']['note']!r}")
if m["gemini"]["keys"] != {"GEMINI_API_KEY": True} or m["elevenlabs"]["keys"] != {"ELEVENLABS_API_KEY": False} \
        or m["minimax"]["keys"] != {"MINIMAX_TOKEN_PLAN_KEY": False, "MINIMAX_API_KEY": True}:
    bad.append("doctor's keys are not set / not set as given")
if next(c for c in d["checks"] if c["name"] == "browser")["state"] != "missing" or any(x["probe"] for x in d["modules"]):
    bad.append("no browser was found, and nothing is probed without --probe")
txt = doc(); outs += [txt.stdout, txt.stderr]
if txt.returncode or "\033[31m✗\033[0m node  18.19.0" not in txt.stdout:
    bad.append(f"doctor's text: exit {txt.returncode}, no ✗ for the old node")
bodies = {"gemini.json": {"models": [{"name": "models/" + n} for n in ("gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-3.5-transcribe")]},
          "minimax.json": {"base_resp": {"status_code": 1004, "status_msg": "login fail"}},
          "dashscope.json": {"error": {"message": "Incorrect API key provided: " + keys["DASHSCOPE_API_KEY"][:9] + "**********"
                                       + keys["DASHSCOPE_API_KEY"][-6:], "code": "invalid_api_key"}}}
for n, b in bodies.items():
    json.dump(b, open(os.path.join(rec, n), "w"))
json.dump({"v": 1, "responses": [
    {"url": "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000", "status": 200, "headers": {}, "body": "gemini.json"},
    {"url": "https://api.minimax.io/v1/get_voice", "status": 200, "headers": {}, "body": "minimax.json"},
    {"url": "https://dashscope.aliyuncs.com/compatible-mode/v1/models", "status": 401, "headers": {}, "body": "dashscope.json"}]},
    open(os.path.join(rec, "responses.json"), "w"))
p = doc("--json", "--probe", "--offline", rec); outs += [p.stdout, p.stderr]
pr = {x["name"]: x["probe"] for x in json.loads(p.stdout)["modules"] if x["probe"]}
if pr.get("gemini", {}).get("state") != "ok" or "3 models" not in pr["gemini"]["note"] \
        or pr.get("minimax", {}).get("state") != "failed" or "1004" not in pr["minimax"]["note"] or "MINIMAX_BASE_URL" not in pr["minimax"]["note"] \
        or pr.get("dashscope", {}).get("state") != "failed" or "HTTP 401 with DASHSCOPE_API_KEY (invalid_api_key)" != pr["dashscope"]["note"] \
        or pr.get("elevenlabs", {}).get("state") != "skipped":
    bad.append(f"doctor --probe from recordings: {pr}")
pt = doc("--probe", "--offline", rec); outs += [pt.stdout, pt.stderr]
import http.server, threading
heard = []
class Next(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        heard.append(dict(self.headers)); self.send_response(200); self.end_headers(); self.wfile.write(b"{}")
    do_GET = do_POST
    def log_message(self, *a):
        pass
class First(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self.send_response(302); self.send_header("Location", f"http://127.0.0.1:{nxt.server_address[1]}/v1/get_voice"); self.end_headers()
    do_GET = do_POST
    def log_message(self, *a):
        pass
nxt, first = http.server.HTTPServer(("127.0.0.1", 0), Next), http.server.HTTPServer(("127.0.0.1", 0), First)
for srv in (nxt, first):
    threading.Thread(target=srv.serve_forever, daemon=True).start()
live = subprocess.run([sys.executable, "tools/doctor.py", "--json", "--probe"], capture_output=True, text=True, encoding="utf-8",
                      env={"PATH": stub, "HOME": t, "HF_HOME": os.path.join(t, "hf"), "MINIMAX_API_KEY": keys["MINIMAX_API_KEY"],
                           "MINIMAX_BASE_URL": f"http://127.0.0.1:{first.server_address[1]}", "DASHSCOPE_API_KEY": keys["DASHSCOPE_API_KEY"],
                           "DASHSCOPE_BASE_URL": "http://example.invalid/api/v1"})
outs += [live.stdout, live.stderr]
for srv in (nxt, first):
    srv.shutdown()
lp = {x["name"]: x["probe"] for x in json.loads(live.stdout)["modules"] if x["probe"]}
if lp["minimax"]["state"] != "failed" or f"127.0.0.1:{nxt.server_address[1]}" not in lp["minimax"]["note"] or "not followed" not in lp["minimax"]["note"] or heard:
    bad.append(f"a redirect: {lp['minimax']}, the next host heard {len(heard)} request(s)")
if lp["dashscope"]["state"] != "failed" or "not an https address" not in lp["dashscope"]["note"]:
    bad.append(f"an http base address: {lp['dashscope']}")
if any(v[i:i + 6] in o for v in keys.values() for i in range(len(v) - 5) for o in outs):
    bad.append("six or more of a key's characters are in doctor's output")
sys.path.insert(0, "tools")
import datetime, doctor
table = json.load(open("tools/modules.json", encoding="utf-8"))
mod = {x["name"]: x for x in table["modules"]}
doctor.this_platform = lambda: "linux-x86_64"
q = doctor.check_module(mod["qwen3-tts"], {}, datetime.date.today())
if q["state"] != "unsupported" or "edge, gemini, minimax, dashscope or elevenlabs" not in q["note"]:
    bad.append(f"qwen3-tts off Apple Silicon: {q}")
fake = [{"name": "a"}, {"name": "b", "needs": {"programs": ["a"]}}, {"name": "c", "needs": {"programs": ["b"]}}]
res = doctor.apply_needs(fake, [{"state": "outdated", "note": ""}, {"state": "ok", "note": ""}, {"state": "ok", "note": "x"}])
if [r["state"] for r in res] != ["outdated", "incomplete", "incomplete"] or res[1]["note"] != "needs a (outdated)" or res[2]["note"] != "x · needs b (incomplete)":
    bad.append(f"needs.programs: {res}")
mod["hyperframes"]["needs"]["programs"].append("no-such-module")
if not any("no-such-module" in b for b in doctor.problems(table)):
    bad.append("the table's rules take a needs.programs that names no module")
bare = os.path.join(t, "bare")
os.makedirs(bare)
for d in ("/bin", "/usr/bin"):
    for n in sorted(os.listdir(d)):
        if not n.startswith("python") and not os.path.lexists(os.path.join(bare, n)):
            os.symlink(os.path.join(d, n), os.path.join(bare, n))
shell = shutil.which(sh) if os.sep not in sh else sh
for args in ([], ["--json"]):
    r = subprocess.run([shell, "bin/vh", "doctor", *args], capture_output=True, text=True, encoding="utf-8", env={"PATH": stub + os.pathsep + bare, "HOME": t})
    ok_ = r.returncode == 0 and (json.loads(r.stdout)["modules"][1] == {"name": "node", "state": "outdated", "note": "v18.19.0 (22 or newer needed)"} if args
                                 else all(w in r.stdout for w in ("python3  not found", "node  v18.19.0 (22 or newer needed)", "ffmpeg", "uv  uv 0.9.0", "git", "chrome", "needs python3")))
    if not ok_:
        bad.append(f"doctor {' '.join(args)} without python3: exit {r.returncode}, {r.stdout[:300]!r} {r.stderr[-200:]!r}")
for args, via in ((["--bogus"], "bin/vh"), (["--offline", rec], "bin/vh"), (["--probe", "--offline", os.path.join(t, "none")], "doctor.py")):
    r = subprocess.run([sh, "bin/vh", "doctor", *args] if via == "bin/vh" else [sys.executable, "tools/doctor.py", *args],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 2 or r.stdout or not r.stderr:
        bad.append(f"doctor {' '.join(args)}: exit {r.returncode}")
r = subprocess.run([sh, "bin/vh", "doctor", "--json"], capture_output=True, text=True, encoding="utf-8")
try:
    here = [x["name"] for x in json.loads(r.stdout)["modules"]]
except ValueError:
    here = None
if r.returncode or here != list(m):
    bad.append(f"bin/vh doctor --json on this machine: exit {r.returncode}, {r.stderr[-200:]!r}")
print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
  then ok "doctor from tools/modules.json: an old node, an ffmpeg without libx264, an aged yt-dlp and keys set or not are said, no six of a key's characters ever; --probe: a key taken, MiniMax's refusal, a 401 echoing a masked key (status and code only), no key skipped, a redirect not followed, an http base elsewhere not called; the platform's alternative; needs.programs; no python3 still reports and exits 0; usage errors 2 before any probe; bin/vh doctor --json here lists every module"
  else bad "bin/vh doctor and tools/modules.json"; fi
  rm -rf "$t"
  # usage errors exit 2, failures 1: these commands with no arguments or a wrong one (new with an option that has no
  # value included; a project, video or folder that is not there); new into a folder that is there already is a failure.
  # Every message of a usage error or a refusal is on stderr and stdout stays empty; the usage that was asked for (-h)
  # is on stdout, exit 0. Nothing here reaches uv or a browser; a project that is not there is not made (tts did)
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); a=""; u=""; mkdir "$t/empty"; : > "$t/v.mp4"; : > "$t/a.wav"; cp -R tools/assets/fixtures/project "$t/fx"
  for c in deliver clean timeline remap timemap storyboard rhythm cover-preview "style compare" "style apply" "style apply dark-math" \
           "style apply no-such $t" "effort loud" new "new math" "new nope ci-x" "new math ci-x --style" "new math ci-x --effort" \
           "new math ci-x --lang" "new math ci-x --bogus" "new math ci-x --style no-such" versions proxy thumbs \
           textcheck fonts "fonts nope" frames render determinism cues patch activity status gate desk \
           tts "tts $t/no-such" sheet "sheet $t/no-such.mp4" gif "gif $t/no-such.mp4" hf-init "hf-init $t/no-such" "hf-init $t/empty 4k" "hf-init $t/empty 2:3" \
           check "check --bogus" "check $t/no-such.mp4 --bogus" "check $t/no-such.mp4 --allow" "check $t/no-such.mp4 --against" "check $t/no-such.mp4 --against $t/no-such-ref.mp4" \
           "check $t/no-such.mp4" "check $t/no-such.mp4 --json" \
           captions "captions $t/empty --media-end" "captions $t/empty --cps" "captions $t/empty --en-max" "captions $t/empty --bogus" \
           "captions $t/no-such" "captions $t/empty" "captions $t/empty zh" mix "style check" \
           "mux $t/no-such.mp4 $t/no-such.wav $t/o.mp4" "mux $t/v.mp4 $t/a.wav $t/no-dir/o.mp4" \
           assets "assets no-such" "assets list $t/no-such" "assets check $t/empty" "assets add" "assets add $t/no-such $t/v.mp4" "assets credits" \
           "assets remove $t/fx no-such-id" "assets add $t/fx $t/no-such.png" "assets add $t/fx $t/v.mp4 --class nope" "assets check $t/fx --policy loose"; do
    # shellcheck disable=SC2086   # several words on purpose
    OVH_PROJECTS="$t" vh $c >"$t/out" 2>"$t/err"; rc=$?
    [ $rc = 2 ] || a="$a | $c exited $rc"
    { [ ! -s "$t/out" ] && [ -s "$t/err" ]; } || u="$u | $c"
  done
  OVH_PROJECTS="$t" vh new math ci-twice >/dev/null 2>&1; OVH_PROJECTS="$t" vh new math ci-twice >"$t/out" 2>"$t/err"; rc=$?
  { [ ! -s "$t/out" ] && [ -s "$t/err" ]; } || u="$u | new over a project"
  for c in deliver new effort tts sheet gif hf-init status clean "style apply" "style apply dark-math" "new math" "new math ci-h" "new math ci-h --style dark-math" \
           assets "assets add" "assets check"; do
    for h in -h --help; do
      # shellcheck disable=SC2086   # several words on purpose
      OVH_PROJECTS="$t" vh $c $h >"$t/out" 2>"$t/err"; rc2=$?
      { [ $rc2 = 0 ] && [ -s "$t/out" ] && [ ! -s "$t/err" ]; } || u="$u | $c $h"
    done
  done
  [ -z "$(ls -d "$t"/*-ci-h "$t"/*--h "$t"/*---help 2>/dev/null)" ] || u="$u | new -h made a folder"
  [ -z "$a" ] && [ $rc = 1 ] && [ -z "$(ls -d "$t"/*-ci-x 2>/dev/null)" ] && [ ! -e "$t/no-such" ] \
    && ok "usage errors exit 2 (new, effort, style, deliver, clean, timeline, remap, timemap, storyboard, rhythm, cover-preview, versions, proxy, thumbs, textcheck, fonts, frames, render, determinism, cues, patch, activity, status, gate, desk, tts, sheet, gif, hf-init, check, captions, mix, mux, assets: no arguments, an option where the video goes or with no value, a project, video, timeline, input or output folder that is not there, a frame it does not know); new over a project is 1" \
    || bad "usage errors:$a (new twice exited $rc; a project made: $(ls -d "$t"/no-such 2>/dev/null))"
  [ -z "$u" ] && ok "usage errors and refusals are on stderr with nothing on stdout, the usage that was asked for (-h) on stdout with exit 0" \
    || bad "messages on the wrong stream:$u"
  # arg_dir finds the project among a page tool's arguments, to pick the browser it renders with: a flag that takes no value
  # in front of it must not swallow it (frames --covers, --no-title and cues --chapters took the project for their value and
  # found "."). Every such flag of frames, render, determinism, cues, fonts check, patch, textcheck, readcheck, storyboard and
  # thumbs; a flag with a value still hides its value (--out o <project>). The function is read out of bin/vh
  mkdir "$t/proj"; a=""
  ad=$(awk '/^arg_dir\(\) \{/,/^\}/' bin/vh)
  for c in --covers --no-title --chapters --soft-gl --real-clock --png --force --save --export --strict --in-place --keep --snapshot \
           --estimate --no-estimate --full --json -h --help --covers=A,B --out=o; do
    o=$("$VH_BASH" -c "$ad"$'\n''arg_dir "$@"' _ "$c" "$t/proj"); [ "$o" = "$t/proj" ] || a="$a | $c gave '$o'"
  done
  for c in --out --at --range --strip --ratios --fps --browser --runtime --note --shot --texts; do
    o=$("$VH_BASH" -c "$ad"$'\n''arg_dir "$@"' _ "$c" value --covers --no-title "$t/proj"); [ "$o" = "$t/proj" ] || a="$a | $c value gave '$o'"
  done
  o=$("$VH_BASH" -c "$ad"$'\n''arg_dir "$@"' _ --out o "$t/page.html"); [ "$o" = "$t" ] || a="$a | a page gave '$o'"
  [ -z "$a" ] && ok "arg_dir: a flag without a value in front of the project (--covers, --no-title, --chapters …) does not hide it; one with a value hides only its value" \
    || bad "arg_dir:$a"
  rm -rf "$t"
  # a project: effort and style are written in, and the quick gate waiver is recorded
  dir=$(ls -d "$ROOT"/projects/*-"$slug" 2>/dev/null); [ -z "$dir" ] || rm -rf "$dir"
  if vh new math "$slug" --effort quick --style dark-math >/dev/null; then
    dir=$(ls -d "$ROOT"/projects/*-"$slug")
    grep -q '^- Effort: quick' "$dir/BRIEF.md" && grep -q 'Effort: quick' "$dir/REVIEW.md" && [ -f "$dir/style-refs/dark-math/STYLE.md" ] \
      && grep -q '^- Style refs (repo presets): `styles/dark-math`' "$dir/BRIEF.md" && ! grep -q '^## Style preset' "$dir/BRIEF.md" \
      && ok "bin/vh new --effort quick --style" || bad "bin/vh new: effort or style not written into the project"
    # the type doc is named, not pasted, and the marker tools/vhdraw.py reads for the type is there
    grep -q '^- Type doc: `video-types/01-math-science-explainer.md`' "$dir/BRIEF.md" && grep -q '^<!-- from 01-math-science-explainer.md -->$' "$dir/BRIEF.md" \
      && ! grep -q '^+ TYPE:' "$dir/BRIEF.md" && ok "bin/vh new names the type doc and keeps the type marker" || bad "bin/vh new: Type doc line or type marker missing"
    rm -rf "$dir"
  else bad "bin/vh new math"; fi
  # --engine canvas-film: the canvas engine's template instead of the type's engine (nothing to install), 16:9 for any type
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  if vh new short cf --engine canvas-film --dir "$t" >/dev/null; then
    dir=$(ls -d "$t"/*-cf)
    [ -f "$dir/film.html" ] && [ -f "$dir/src/50-shots.js" ] && [ -f "$dir/audio/timeline.zh.json" ] && [ -f "$dir/ENGINE_README.md" ] && [ ! -e "$dir/index.html" ] \
      && grep -q '^- Output: 1920x1080,' "$dir/BRIEF.md" && grep -q '^- Engine: canvas-film' "$dir/BRIEF.md" \
      && ok "bin/vh new --engine canvas-film copies the engine's template at 1920x1080" || bad "bin/vh new --engine canvas-film: the template or the BRIEF's Output and Engine lines are missing"
  else bad "bin/vh new short --engine canvas-film"; fi
  # doctor <project>: the copied engine against the engine now; an older copy (a module missing, a file edited, one of
  # its own) is listed with a diff command, and nothing in the project changes
  if [ -n "${dir:-}" ] && [ -d "$dir" ]; then
    a=$(vh doctor "$dir" 2>&1); rc=$?
    rm "$dir/src/06-time-map.js" && grep -v '06-time-map' "$dir/film.html" > "$t/f.html" && mv "$t/f.html" "$dir/film.html"
    printf '// a tweak\n' >> "$dir/src/00-core.js"; printf '// its own\n' > "$dir/src/40-own.js"; printf '// the film\n' >> "$dir/src/50-shots.js"
    snap() { find "$dir" -type f -exec cksum {} + | LC_ALL=C sort; }
    before=$(snap); b=$(vh doctor "$dir" 2>&1); rc2=$?; after=$(snap)
    case "$rc:$a" in 0:*"the copy is the engine as it is now"*)
      case "$rc2:$b" in 1:*"changed (2): film.html +1 −0, src/00-core.js +0 −1"*"missing (1): src/06-time-map.js (film.html does not load it either)"*"extra (1): src/40-own.js"*"diff -u "*)
          [ "$before" = "$after" ] && ok "doctor <project>: a fresh copy is the engine; an older one lists changed, missing and extra files and a diff command, read-only" \
            || bad "doctor <project> changed the project" ;;
        *) bad "doctor on an older copy (exit $rc2): $b" ;; esac ;;
      *) bad "doctor on a fresh canvas-film project (exit $rc): $a" ;; esac
  fi
  vh new short cf2 --engine canvas-film --aspect 9:16 --dir "$t" >/dev/null 2>&1; rc=$?
  vh new short cf3 --engine no-such --dir "$t" >/dev/null 2>&1; a=$?
  [ $rc = 2 ] && [ $a = 2 ] && [ -z "$(ls -d "$t"/*-cf2 "$t"/*-cf3 2>/dev/null)" ] && ok "bin/vh new refuses a vertical canvas-film and an unknown --engine" \
    || bad "bin/vh new --engine: --aspect 9:16 exited $rc, an unknown engine $a"
  rm -rf "$t"
  # tts picks the uv dependencies from --provider too (a fake uv prints the command instead of running it)
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); printf '#!/bin/sh\necho "$*"\n' > "$t/uv"; chmod +x "$t/uv"
  a=$(PATH="$t:$PATH" vh tts "$t" --provider edge --lang en; PATH="$t:$PATH" vh tts "$t" --provider=dashscope)
  case "$a" in *"--with edge-tts "*"--provider edge"*"--with dashscope "*) ok "tts --provider picks the provider's dependencies" ;;
    *) bad "tts --provider: uv got '$a'" ;; esac
  # Ctrl-C (to the process group, as a terminal sends it) while a command runs through uv run ends bin/vh by SIGINT (130
  # to a shell; the caller sees the Ctrl-C), even when uv itself exits 2 ("Failed to get PID of child process", the race
  # when its Python has just exited): a fake uv that does exactly that, under each command that goes through uv
  printf '#!/bin/sh\ntrap '"'"'echo "error: Failed to get PID of child process" >&2; exit 2'"'"' INT\n: > "$UVMARK"\nwhile :; do sleep 0.05; done\n' > "$t/uv"
  if a=$(python3 - "$t" "$VH_BASH" "$ROOT/bin/vh" <<'PY'
import os, signal, subprocess, sys, time
t, sh, vh = sys.argv[1:]
open(f"{t}/x.mp4", "wb").close()   # sheet looks for its video before it runs uv
os.makedirs(f"{t}/audio", exist_ok=True); open(f"{t}/audio/timeline.json", "w").close()   # and captions for its timeline
mark, env = f"{t}/started", dict(os.environ, PATH=f"{t}:{os.environ['PATH']}", UVMARK=f"{t}/started")
runs = [["music", "x"], ["sfx", "x"], ["beats", "x"], ["qa", "x"], ["mix", "profile=x"], ["tts", t], ["pace", "x"],
        ["cover-preview", "x"], ["style", "compare", "a,b"], ["sheet", f"{t}/x.mp4"], ["fonts", "list", "x"], ["captions", t],
        ["voices", "audition", "--voices", "x", "--text", "x"]]
bad = []
for r in runs:
    if os.path.exists(mark): os.remove(mark)
    p = subprocess.Popen([sh, vh, *r], start_new_session=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(500):
        if os.path.exists(mark) or p.poll() is not None: break
        time.sleep(0.02)
    try: os.killpg(p.pid, signal.SIGINT)
    except OSError: pass
    try: rc = p.wait(timeout=20)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); rc = "hung"
    if rc != -signal.SIGINT: bad.append(f"{' '.join(r[:2])} {rc}")
print(", ".join(bad)); sys.exit(1 if bad else 0)
PY
); then ok "Ctrl-C ends every command that runs through uv run by SIGINT, also when uv exits 2 as its Python exits"
  else bad "Ctrl-C under uv run (command, exit; want -2, death by SIGINT): $a"; fi
  rm -rf "$t"
  # tts: a Gemini 429 that names a per-day quota fails at once, though it asks for 30 s; a per-minute one is still waited
  # out and retried; one naming no daily quota fails at once only past 90 s (a stub on 127.0.0.1; waits recorded, not slept)
  if a=$(GEMINI_API_KEY=ci-stub python3 - 2>&1 <<'PY'
import importlib.util, json, os, threading
os.environ["no_proxy"] = "127.0.0.1"   # urlopen would send the stub's requests through an http_proxy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
spec = importlib.util.spec_from_file_location("tts", "tools/audio/tts.py"); tts = importlib.util.module_from_spec(spec); spec.loader.exec_module(tts)
def body(*ids, delay="30s"):
    return json.dumps({"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaMetric": "generativelanguage.googleapis.com/x", "quotaId": i} for i in ids]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}]}}).encode()
answers = []
class Stub(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"])); code, b = answers.pop(0)
        self.send_response(code); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub); threading.Thread(target=srv.serve_forever, daemon=True).start()
tts.GEMINI_API = f"http://127.0.0.1:{srv.server_address[1]}"
waits = []; tts.time.sleep = waits.append
minute, day = "GenerateRequestsPerMinutePerProjectPerModel", "GenerateRequestsPerDayPerProjectPerModel"
answers[:] = [(429, body(minute, day)), (200, b"{}")]
try:
    tts.gemini_call("interactions", {}); raise SystemExit(f"a per-day 429 was retried (waits {waits})")
except tts.GeminiError as e:
    assert not waits and len(answers) == 1 and day in str(e) and "--resume" in str(e), (waits, str(e))
answers[:] = [(429, body(minute)), (429, body(minute)), (200, b'{"ok": 1}')]
assert tts.gemini_call("interactions", {}) == {"ok": 1} and waits == [31.0, 31.0], waits
answers[:] = [(429, body(minute, delay="120s")), (200, b"{}")]; waits.clear()
try:
    tts.gemini_call("interactions", {}); raise SystemExit("a 429 asking for 120 s was retried")
except tts.GeminiError:
    assert not waits and len(answers) == 1, waits
PY
); then ok "tts: a Gemini 429 naming a per-day quota fails at once; a per-minute one is retried; past 90 s fails at once"
  else bad "tts: Gemini 429 handling: $a"; fi
  # tts --join block --candidates 3 and voices audition against a Gemini stub on 127.0.0.1 that speaks a tone burst per
  # character (pitch by voice; the 2nd take of each block 25 % higher) and transcribes what it spoke (讲一讲 twice; 那 heard as
  # 哪 for one voice): the take nearest the median voice is kept, a slow line and the repeat are warned of, the audition
  # measures each voice's pitch and speech rate and names the misread word; without a key, nothing is synthesized
  if ! command -v uv >/dev/null || ! command -v ffmpeg >/dev/null; then skip "tts --candidates · voices audition" "needs uv and ffmpeg"
  elif a=$(uv run -q --no-project --with numpy python - 2>&1 <<'PY'
import base64, contextlib, hashlib, importlib.util, io, json, os, re, shutil, sys, tempfile, threading, wave
import numpy as np
os.environ["no_proxy"] = "127.0.0.1"; os.environ["GEMINI_API_KEY"] = "ci-stub"
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, "tools/audio")
spec = importlib.util.spec_from_file_location("tts", "tools/audio/tts.py"); tts = importlib.util.module_from_spec(spec); spec.loader.exec_module(tts)
SR, PITCH = 24000, {"Kore": 200.0, "Puck": 130.0, "Charon": 110.0}
st = {"n": 0, "vary": False, "takes": []}                  # takes: (duration, [(unit, start, end)]) of every synthesis
def speak(items, f0):                                      # a burst per CJK character, 0.35 s between the items
    x, words, t = [np.zeros(int(0.05 * SR))], [], 0.05
    for k, text in enumerate(items):
        if k:
            x.append(np.zeros(int(0.35 * SR))); t += 0.35
        for c in re.findall(r"[一-鿿]", text):
            b = 0.4 if c == "慢" else 0.15; m = int(b * SR); tt = np.arange(m) / SR
            x.append(0.3 * np.sin(np.pi * np.arange(m) / m) ** 0.5 * sum(np.sin(2 * np.pi * f0 * h * tt) / h for h in (1, 2, 3)))
            words.append((c, t, t + b)); t += b
            x.append(np.zeros(int(0.05 * SR))); t += 0.05
    x.append(np.zeros(int(0.1 * SR))); y = np.concatenate(x)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue(), len(y) / SR, words
def heard(words, voice):                                   # the transcript: the words, 讲一讲 said twice, 那 heard as 哪 for Charon
    out, k = [], 0
    while k < len(words):
        c, a, b = words[k]; out.append((("哪" if c == "那" and voice == "Charon" else c), a, b))
        if "".join(w[0] for w in words[k - 2:k + 1]) == "讲一讲":
            out += [(w[0], b + 0.01 * j, b + 0.01 * (j + 1)) for j, w in enumerate(words[k - 2:k + 1])]
        k += 1
    return out
class Stub(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if "response_format" in body:                      # synthesis
            voice = body["generation_config"]["speech_config"][0]["voice"]
            f0 = PITCH.get(voice, 160.0) * ((1.0, 1.25, 0.98)[st["n"] % 3] if st["vary"] else 1.0); st["n"] += 1
            data, dur, words = speak([c["text"] for c in body["input"][0]["content"]], f0); st["takes"].append((dur, words, voice))
            r = {"steps": [{"type": "model_output", "content": [{"type": "audio", "data": base64.b64encode(data).decode()}]}]}
        else:                                              # transcription: the take whose length matches (trimmed by ~0.04 s)
            with wave.open(io.BytesIO(base64.b64decode(body["input"][0]["data"]))) as w:
                dur = w.getnframes() / w.getframerate()
            _, words, voice = min(reversed(st["takes"]), key=lambda tk: abs(tk[0] - 0.04 - dur))   # the latest of equal ones
            ws = heard(words, voice)
            r = {"steps": [{"content": [{"type": "text", "text": "".join(w[0] for w in ws), "annotations": [
                {"type": "word_info", "text": w[0], "start_offset": f"{max(0, w[1] - 0.02):.2f}s", "end_offset": f"{max(0, w[2] - 0.02):.2f}s"} for w in ws]}]}]}
        b = json.dumps(r).encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub); threading.Thread(target=srv.serve_forever, daemon=True).start()
tts.GEMINI_API = f"http://127.0.0.1:{srv.server_address[1]}"
def run(argv):
    out = io.StringIO(); rc = 0
    with contextlib.redirect_stdout(out):
        sys.argv = ["tts.py", *argv]
        try:
            tts.main()
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else (1 if e.code else 0); print(e.code if not isinstance(e.code, int) else "")
    return rc, out.getvalue()
bad = []
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "p"; (p / "audio").mkdir(parents=True)
    (p / "audio/script.txt").write_text("@a1 我们今天讲一讲声音的来历。\n@a2 先从一根琴弦说起吧。\n@a3 它振动时推着空气走。\n\n"
                                        "@b1 空气把推挤传到耳朵里。\n@b2 慢慢慢慢慢慢慢慢。\n@b3 耳朵把它变成声音。\n", encoding="utf-8")
    st["vary"] = True
    rc, out = run([str(p), "--provider", "gemini", "--voice", "Kore", "--join", "block", "--candidates", "3"])
    st["vary"] = False
    pick = json.loads((p / "audio/vo/zh/_pick.json").read_text(encoding="utf-8")) if (p / "audio/vo/zh/_pick.json").exists() else {}
    tl = json.loads((p / "audio/timeline.zh.json").read_text(encoding="utf-8")) if rc == 0 else {}
    if rc != 0: bad.append(f"tts --candidates exited {rc}: {out[-600:]}")
    elif [pick["blocks"][b]["chosen"] for b in ("1", "2")] != [1, 1] or len(list((p / "audio/vo/zh").glob("_block0?.c?.wav"))) != 6:
        bad.append(f"picked {pick}")
    elif sum(1 for s in tl["segments"] if s.get("words")) != 6: bad.append("not every line has words")
    for want in ("warning: @b2 takes", "“讲一讲” twice"):
        if want not in out: bad.append(f"no '{want}' in: {out[-900:]}")
    if "warning: @a2" in out or "warning: @b1" in out: bad.append(f"a false warning: {out[-900:]}")
    # --resume reuses a block's transcription only while it is of the same file: nothing changed, none; a cache from before
    # the key (no sha256) beside other takes of its block, each block once (a copy that kept the date would pass for the
    # old take), then none; another candidate copied over _block01.wav by hand, that block
    vo, again = p / "audio/vo/zh", [str(p), "--provider", "gemini", "--voice", "Kore", "--join", "block", "--candidates", "3", "--resume"]
    calls = lambda out: int((re.search(r"align: (\d+) transcribe call", out) or [0, -1])[1])   # noqa: E731
    rc, out = run(again)
    if rc != 0 or calls(out) != 0: bad.append(f"--resume with nothing changed: exit {rc}, {calls(out)} transcribe call(s): {out[-300:]}")
    for f in vo.glob("_block0?.asr.json"):
        c = json.loads(f.read_text(encoding="utf-8")); c.pop("sha256", None); f.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    rc, out = run(again); rc2, out2 = run(again); kept = (vo / "_block02.asr.json").stat().st_mtime_ns
    if rc != 0 or calls(out) != 2 or calls(out2) != 0: bad.append(f"--resume on caches without a key beside other takes: exit {rc}, {calls(out)} then {calls(out2)} transcribe call(s): {out[-300:]}")
    shutil.copyfile(vo / "_block01.c2.wav", vo / "_block01.wav")
    rc, out = run(again); side = json.loads((vo / "_block01.asr.json").read_text(encoding="utf-8"))
    if rc != 0 or calls(out) < 1 or side.get("sha256") != hashlib.sha256((vo / "_block01.wav").read_bytes()).hexdigest() \
            or (vo / "_block02.asr.json").stat().st_mtime_ns != kept:
        bad.append(f"--resume after _block01.wav was swapped by hand: exit {rc}, {calls(out)} call(s), cache key {side.get('sha256')}: {out[-300:]}")
    # minimax gives its own word times (a stand-in for its API: a burst per character, 0.15 s, or 0.24 s every other take, and
    # its subtitles): with --candidates, the other take copied over _block01.wav is cut by that take's own words file, and
    # a take that is no candidate of the block stops the run (no --align gemini to cut it by), saying so
    os.environ["MINIMAX_API_KEY"] = "ci-stub"; mm = {"n": 0}
    def fake_mm(text, voice, lang, emotion):
        b = 0.24 if mm["n"] % 2 else 0.15; mm["n"] += 1
        x, subs, t = [np.zeros(int(0.05 * SR))], [], 0.05
        for part in re.split(r"(<#[\d.]+#>)", text):
            m = re.fullmatch(r"<#([\d.]+)#>", part)
            if m:
                x.append(np.zeros(int(float(m[1]) * SR))); t += float(m[1]); continue
            for c in part.strip():
                if not re.match(r"[一-鿿]", c):
                    subs.append({"text": c, "time_begin": round(t * 1000), "time_end": round(t * 1000)}); continue
                n = int(b * SR); x.append(0.3 * np.sin(2 * np.pi * 180 * np.arange(n) / SR) * np.sin(np.pi * np.arange(n) / n))
                subs.append({"text": c, "time_begin": round(t * 1000), "time_end": round((t + b) * 1000)}); t += b
                x.append(np.zeros(int(0.05 * SR))); t += 0.05
        x.append(np.zeros(int(0.1 * SR))); y = np.concatenate(x); buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
        return buf.getvalue(), subs
    tts.minimax_tts = fake_mm
    q = Path(d) / "m"; (q / "audio").mkdir(parents=True); mvo = q / "audio/vo/zh"
    (q / "audio/script.txt").write_text("@m1 我们今天讲声音。\n@m2 先从琴弦说起。\n\n@n1 空气把它传走。\n", encoding="utf-8")
    mcmd = [str(q), "--provider", "minimax", "--voice", "x", "--join", "block", "--candidates", "2"]
    spans = lambda: [round(s["end"] - s["start"], 2) for s in json.loads((q / "audio/timeline.zh.json").read_text(encoding="utf-8"))["segments"]][:2]   # noqa: E731
    rc, out = run(mcmd)
    if rc != 0: bad.append(f"minimax --candidates exited {rc}: {out[-500:]}")
    else:
        other = 3 - json.loads((mvo / "_pick.json").read_text(encoding="utf-8"))["blocks"]["1"]["chosen"]; before = spans()
        shutil.copyfile(mvo / f"_block01.c{other}.wav", mvo / "_block01.wav")
        rc, out = run(mcmd + ["--resume"]); after = spans()
        own = tts.load_words(mvo / f"_block01.c{other}.words.json")[1]
        if rc != 0 or tts.load_words(mvo / "_block01.words.json")[1] != own or not all(abs(q2 / p2 - (0.29 if other == 2 else 0.2) / (0.2 if other == 2 else 0.29)) < 0.1 for p2, q2 in zip(before, after)):
            bad.append(f"minimax: the other take copied in by hand (exit {rc}): line spans {before} → {after}: {out[-300:]}")
        shutil.copyfile(mvo / "_block02.wav", mvo / "_block01.wav")
        rc, out = run(mcmd + ["--resume"])
        if rc == 0 or "is not the take its word times (_block01.words.json) are of" not in out:
            bad.append(f"minimax: a take that is no candidate of the block, copied in (exit {rc}): {out[-300:]}")
    (Path(d) / "t.txt").write_text("我们那儿的声音从一根琴弦说起。\n", encoding="utf-8")
    rc, out = run(["voices", "audition", "--provider", "gemini", "--voices", "Kore,Puck,Charon", "--text", f"{d}/t.txt", "--out", f"{d}/au", "--align", "gemini"])
    au = json.loads(Path(f"{d}/au/audition.json").read_text(encoding="utf-8")) if Path(f"{d}/au/audition.json").exists() else {"voices": []}
    R = {r["voice"]: r for r in au["voices"]}
    true = 14 / (14 * 0.2 - 0.05)                          # characters over the voice, no pause in it
    if rc != 0 or sorted(R) != ["Charon", "Kore", "Puck"] or not all((Path(d) / "au" / R[v]["file"]).exists() for v in R): bad.append(f"audition exited {rc}: {out[-500:]}")
    else:
        if not all(abs(R[v]["pitch_hz"] / PITCH[v] - 1) < 0.03 for v in R): bad.append(f"pitch {[(v, R[v]['pitch_hz']) for v in R]}")
        if not all(abs(R[v]["speech_rate"] / true - 1) < 0.08 for v in R): bad.append(f"speech rate {[(v, R[v]['speech_rate']) for v in R]} (true {true:.2f})")
        if R["Kore"]["misread"] != [] or not any("那" in m for m in R["Charon"]["misread"]): bad.append(f"misread {[(v, R[v]['misread']) for v in R]}")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
); then ok "tts --candidates keeps the take nearest the median voice per block; a slow line and a repeated phrase are warned of; --resume hears a block swapped by hand again, the rest not; voices audition measures pitch, speech rate and misreads"
  else bad "tts --candidates / voices audition on the Gemini stub: $a"; fi
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); printf '%s\n' '一句试音。' > "$t/t.txt"
  a=$(env -u GEMINI_API_KEY "$VH_BASH" "$ROOT/bin/vh" voices audition --provider gemini --voices Kore,Puck --text "$t/t.txt" 2>&1); rc=$?
  case "$rc:$a" in 1:*"set GEMINI_API_KEY"*"nothing was synthesized"*) [ ! -e "$t/audition-t" ] && ok "voices audition without a key says so and writes nothing" || bad "voices audition without a key wrote files" ;;
    *) bad "voices audition without a key: exit $rc: $a" ;; esac
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
  # packcheck counts X's way (a Chinese character 2, a link 23); "X" names X only standing alone, not inside "xhs"
  { printf '%s\n' '# PACKAGING' '## 发布文案' '### X / 推特'; python3 -c "print('简介：' + '字' * 127 + ' https://example.com/' + 'a' * 40 + '.')"
    printf '%s\n' '### B站 + X' '简介：两个平台'; python3 -c "print('字' * 139)"; printf '%s\n' '### 小红书 xhs' "简介：$(python3 -c "print('字' * 300)")"; } > "$t/PACKAGING.md"
  a=$(python3 "$ROOT/tools/packcheck.py" "$t/PACKAGING.md"); rc=$?
  case "$rc:$a" in 1:*"X / 推特: ✓ 简介 description 279 weighted"*"B站 + X: ✗ 简介 description 287 weighted"*"official, x)"*"小红书 xhs: · 简介 description 300 characters"*)
      ok "packcheck: X's limit in its weighted length (Chinese 2, a link 23), the tightest platform of a heading, a one-letter name standing alone" ;;
    *) bad "packcheck on X copy (rc $rc): $a" ;; esac
  # what X takes for a link (twitter-text's rules): a bare domain with a TLD it knows, with its path, Chinese straight
  # before it staying text; not after - _ . / @ $, not a file name with a TLD it does not know, not a host with no TLD
  if a=$(python3 - <<'PY'
import sys; sys.path.insert(0, "tools"); import packcheck as P
cases = {"example.com/path": 23, "看这里：example.com，很好": 37, "x.com": 23, "packcheck.py": 23, "www.github.com/a/b": 23,
         "b23.tv/BV1x": 23, "example.co.uk": 23, "bit.ly/abc?x=1": 23, "example.com?x=1": 27, "example.com:8080/x": 23,
         "两个 https://a.io 和 b.io": 55, "https://example.com，后面": 29, "https://ex.com/a_(b).": 24, "ex.com/a.": 24,
         "foo_bar.com": 11, "Node.js": 7, "tools/x.py": 10, "-x.com": 6, "a@example.com": 13, "$example.com": 12, "ex.comm": 7,
         "https://localhost:3000/x": 24, "v1.2.3": 6, "a" * 63 + ".com": 23, "x" * 70 + ".com": 74, "看" * 70 + "example.com": 151,
         "a." * 3000 + " example.com": 6024}   # a label over 63 characters (in punycode) is no link, as on X; a long dotted run
bad = [f"{k!r}: {P.x_length(k)} (want {v})" for k, v in cases.items() if P.x_length(k) != v]
print("; ".join(bad)); sys.exit(1 if bad else 0)
PY
  ); then ok "packcheck: X's links as twitter-text finds them, bare domains (example.com/path) included, not foo_bar.com, Node.js or tools/x.py"
  else bad "packcheck, X's links: $a"; fi
  rm -rf "$t"
  if ! command -v ffmpeg >/dev/null; then skip "mux / gif smoke" "ffmpeg not installed"; return; fi
  if python3 tools/audio/test_mixstate.py; then ok "mix/mux: failed and stale builds refused, previous audio preserved, deliberate duration changes"
  else bad "mix/mux build validity"; fi
  # subtitle languages come from the file name, never from folders (a home dir like /home/zhang used to tag everything chi)
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); mkdir -p "$t/zhang/en.v1.2"
  ffmpeg -nostdin -v error -f lavfi -i color=c=black:s=64x64:d=1 -pix_fmt yuv420p -f mp4 "$t/zhang/en.v1.2/final" \
    && ffmpeg -nostdin -v error -f lavfi -i sine=d=0.5 "$t/a.wav" \
    && printf '1\n00:00:00,000 --> 00:00:00,900\nhi\n' | tee "$t/zhang/captions.en.srt" "$t/zhang/captions.zh.srt" "$t/zhang/en.v1.2/subs.srt" >/dev/null
  if vh mux "$t/zhang/en.v1.2/final" "$t/a.wav" "$t/out.mp4" --allow-short "$t/zhang/captions.en.srt" "$t/zhang/captions.zh.srt" "$t/zhang/en.v1.2/subs.srt" >/dev/null; then
    langs=$(ffprobe -v error -select_streams s -show_entries stream_tags=language -of csv=p=0 "$t/out.mp4" | tr '\n' ' ')
    [ "$langs" = "eng chi und " ] && ok "mux tags subtitle languages by file name" || bad "mux subtitle languages: got '$langs', want 'eng chi und'"
    a=$(ffprobe -v error -select_streams a -show_entries stream=duration -of csv=p=0 "$t/out.mp4"); python3 -c "import sys; sys.exit(0 if abs(float('$a') - 1) < 0.05 else 1)" \
      && ok "mux pads short audio to the video length" || bad "mux audio duration $a, want 1.0"
  else bad "bin/vh mux"; fi
  # no subtitle files: an empty array under set -u, which bash before 4.4 (macOS /bin/bash) treats as unbound
  vh mux "$t/zhang/en.v1.2/final" "$t/a.wav" "$t/out-nosubs.mp4" --allow-short >/dev/null && [ -s "$t/out-nosubs.mp4" ] \
    && ok "mux without subtitle files" || bad "bin/vh mux without subtitle files"
  vh gif "$t/zhang/en.v1.2/final" 64 5 >/dev/null && [ -f "$t/zhang/en.v1.2/final.gif" ] && ok "gif names the output after the file, not a dotted folder" || bad "bin/vh gif output name"
  # bin/vh deliver: a 2 s master with sound and a subtitle track, cut to fit 0.5 MB (a ceiling worked out from the size),
  # a keyframe every 2 s, BT.709 tags, the tracks copied, the PSNR measured; a limit too small to hold a picture is refused
  ffmpeg -nostdin -v error -f lavfi -i "testsrc2=s=320x180:r=30:d=2" -f lavfi -i "sine=d=2" -c:v libx264 -crf 10 -pix_fmt yuv420p \
    -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -shortest "$t/m0.mp4" \
    && vh mux "$t/m0.mp4" "$t/a.wav" "$t/master.mp4" --allow-short "$t/zhang/captions.zh.srt" >/dev/null
  a=$(vh deliver "$t/master.mp4" --max-gb 0.0005 --samples 2 2>&1); rc=$?
  if [ $rc = 0 ] && [ -s "$t/master.upload.mp4" ] && printf '%s' "$a" | grep -q 'PSNR against the master' && python3 - "$t/master.upload.mp4" <<'PY'
import json, os, subprocess, sys
f = sys.argv[1]
st = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", f], capture_output=True, text=True).stdout)["streams"]
v = next(s for s in st if s["codec_type"] == "video")
keys = [l.split(",")[0] for l in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", f],
                                                capture_output=True, text=True).stdout.split() if "K" in l.split(",")[1]]
ok = os.path.getsize(f) <= 500_000 and (v["pix_fmt"], v["color_range"], v["color_space"], v["color_transfer"], v["color_primaries"]) == ("yuv420p", "tv", "bt709", "bt709", "bt709")
ok = ok and [s["codec_type"] for s in st] == ["video", "audio", "subtitle"] and [round(float(k), 3) for k in keys] == [0.0]
sys.exit(0 if ok else 1)
PY
  then ok "deliver: the upload copy fits the size asked for, keeps BT.709 and the sound and subtitle tracks, and says its PSNR"
  else bad "deliver (exit $rc): $(printf '%s' "$a" | tail -c 600)"; fi
  a=$(vh deliver "$t/master.mp4" --for bilibili,youtube --out "$t/master.platform.mp4" --psnr off 2>&1); rc=$?
  case "$rc:$a" in 0:*"fits 8 GB with room"*"✓ Bilibili web"*"✓ YouTube"*) ok "deliver --for: a short master far under the limits is encoded at CRF alone, no VBV numbers past x264's range" ;;
    *) bad "deliver --for on a short master: exit $rc: $(printf '%s' "$a" | tail -c 500)" ;; esac
  a=$(vh deliver "$t/master.mp4" --max-gb 0.00001 2>&1); rc=$?
  case "$rc:$a" in 2:*"too little"*) ok "deliver: a limit that leaves no room for the picture is refused (exit 2)" ;; *) bad "deliver with a tiny limit: exit $rc: $a" ;; esac
  # bin/vh clean: a finished project's frames, render chunks, drafts and old takes go (to a stand-in Trash here, OVH_TRASH_DIR);
  # the film in out/final/, its covers, the review pages, the narration in use and its original, sources and docs stay
  c="$t/cl"; mkdir -p "$c/out/frames" "$c/out/.film.mp4.parts" "$c/out/final/covers" "$c/out/review" "$c/audio/takes" "$c/src" "$c/node_modules/x" "$t/home"
  for f in BRIEF.md film.html src/50-shots.js out/frames/a.png out/.film.mp4.parts/part000.mp4 out/draft1.mp4 out/film.mp4 out/film.mp4.render.json \
    out/final/film-4k.mp4 out/final/covers/a.png out/review/gate-1.html out/cues.json audio/voiceover.zh.wav audio/voiceover.zh.raw.wav \
    audio/voiceover.zh.v1.wav audio/music.wav audio/takes/b.wav audio/timeline.zh.json node_modules/x/i.js; do printf x > "$c/$f"; done
  a=$(vh clean "$c" 2>&1); rc=$?; [ -f "$c/out/draft1.mp4" ] && a="$a (draft still there)"
  b=$(OVH_TRASH_DIR="$t/home/trash" vh clean "$c" --yes --delete 2>&1); rc2=$?
  left=$(cd "$c" && find . -type f | sed 's|^\./||' | LC_ALL=C sort | tr '\n' ' ')   # byte order: the runner's locale sorts otherwise
  want=".ovh/activity.jsonl BRIEF.md audio/timeline.zh.json audio/voiceover.zh.raw.wav audio/voiceover.zh.wav film.html out/cues.json out/final/covers/a.png out/final/film-4k.mp4 out/review/gate-1.html src/50-shots.js "   # (the activity log stays)
  if [ $rc = 0 ] && printf '%s' "$a" | grep -q '9 item(s)' && printf '%s' "$a" | grep -q '(draft still there)' && [ $rc2 = 0 ] && [ "$left" = "$want" ] \
    && [ "$(find "$t/home" -name '*.wav' | wc -l | tr -d ' ')" = 3 ] && [ "$(find "$t/home" -name '*.mp4' | wc -l | tr -d ' ')" = 2 ]
  then ok "clean: lists first; then the film, covers, review pages, the narration in use and the sources stay, the rest goes (old takes and renders to the Trash)"
  else bad "clean: exit $rc / $rc2, left: $left | $(printf '%s' "$a$b" | tail -c 700)"; fi
  # what went to the Trash gives no space back until it is emptied, and Time Machine's local snapshots can hold it after that
  # (a stand-in tmutil lists two, so this runs where there is none); what was deleted outright says only the snapshots' part;
  # a run that does both says the two, the Trash's after it is emptied
  mkdir -p "$t/stub" && printf '#!/bin/sh\nprintf "com.apple.TimeMachine.2026-10-25-120000.local\\ncom.apple.TimeMachine.2026-10-25-130000.local\\n"\n' > "$t/stub/tmutil" && chmod +x "$t/stub/tmutil"
  c="$t/cl5"; mkdir -p "$c/out"; c2="$t/cl6"; mkdir -p "$c2/out/frames"; c3="$t/cl7"; mkdir -p "$c3/out/frames"
  for f in BRIEF.md out/final.mp4 out/draft.mp4; do printf x > "$c/$f"; done; for f in BRIEF.md out/final.mp4 out/frames/a.png; do printf x > "$c2/$f"; done
  for f in BRIEF.md out/final.mp4 out/draft.mp4 out/frames/a.png; do printf x > "$c3/$f"; done
  a=$(PATH="$t/stub:$PATH" OVH_TRASH_DIR="$t/home/trash5" vh clean "$c" --yes 2>&1); rc=$?
  b=$(PATH="$t/stub:$PATH" OVH_TRASH_DIR="$t/home/trash5" vh clean "$c2" --yes --delete 2>&1); rc2=$?
  d=$(PATH="$t/stub:$PATH" OVH_TRASH_DIR="$t/home/trash5" vh clean "$c3" --yes --delete 2>&1); rc3=$?
  if [ $rc = 0 ] && [ $rc2 = 0 ] && [ $rc3 = 0 ] && [ -f "$t/home/trash5/draft.mp4" ] \
    && printf '%s' "$d" | grep -q 'what went to the Trash frees its space when the Trash is emptied' \
    && printf '%s' "$d" | grep -q "Time Machine holds 2 local snapshot(s): data deleted since the last one stays on the disk until macOS drops them, the Trash's too once it is emptied" \
    && printf '%s' "$a" | grep -q 'what went to the Trash frees its space when the Trash is emptied' \
    && printf '%s' "$a" | grep -q "Time Machine's 2 local snapshot(s) can still hold it on the disk after that" && ! printf '%s' "$a" | grep -q 'data deleted since the last one' \
    && printf '%s' "$b" | grep -q 'Time Machine holds 2 local snapshot(s): data deleted since the last one stays' && ! printf '%s' "$b" | grep -q 'Trash is emptied'
  then ok "clean: what went to the Trash gives its space back when the Trash is emptied (snapshots can hold it after that); what was deleted says the snapshots' part; a run of both says both"
  else bad "clean's closing lines (exit $rc / $rc2 / $rc3): $(printf '%s' "$a" | tail -n 3 | tail -c 500) | $(printf '%s' "$b" | tail -n 2 | tail -c 300) | $(printf '%s' "$d" | tail -n 3 | tail -c 400)"; fi
  # a cover video inside out/final/ is not the film, so out/final.mp4 is; a path kept inside a folder that goes stays
  c="$t/cl2"; mkdir -p "$c/out/final/covers" "$c/out/frames"
  for f in BRIEF.md out/final/covers/loop.mp4 out/final.mp4 out/draft.mp4 out/frames/a.png out/frames/keep.png; do printf x > "$c/$f"; done
  a=$(vh clean "$c" --keep out/frames/keep.png 2>&1); rc=$?
  if [ $rc = 0 ] && printf '%s' "$a" | grep -q 'the film: out/final.mp4' && printf '%s' "$a" | grep -q 'out/draft.mp4' && printf '%s' "$a" | grep -q 'out/frames/a.png' \
    && ! printf '%s' "$a" | grep -Eq 'keep\.png|  out/final\.mp4|loop\.mp4'
  then ok "clean: a cover video does not make the film a render; a path kept inside a folder that goes stays"
  else bad "clean on covers and a kept path (exit $rc): $(printf '%s' "$a" | tail -c 600)"; fi
  # deliver's copy is the film to clean: its record (<copy>.deliver.json) keeps the copy, its master and itself, so a project
  # with no out/final/ clears its draft; out/check/ is check frames (rebuilt), but a video in it stays; a copy replaced
  # since its record is said and kept
  c="$t/cl3"; mkdir -p "$c/out/check/storyboard/frames"; cp "$t/master.mp4" "$c/out/film-4k.mp4"
  for f in BRIEF.md out/draft.mp4 out/check/sheet.png out/check/storyboard/frames/S01.png; do printf x > "$c/$f"; done
  vh deliver "$c/out/film-4k.mp4" --out "$c/out/film-4k.bili.mp4" --psnr off >/dev/null 2>&1; rc=$?
  a=$(vh clean "$c" 2>&1); rc2=$?
  printf x > "$c/out/check/clip.mp4"; printf x >> "$c/out/film-4k.bili.mp4"
  mkdir -p "$c/out/check/repro"; for f in BRIEF.md source.js cut.mp4; do printf x > "$c/out/check/repro/$f"; done   # a project of its own
  b=$(OVH_TRASH_DIR="$t/home/trash3" vh clean "$c" --yes --delete 2>&1); rc3=$?
  left=$(cd "$c" && find . -type f | sed 's|^\./||' | LC_ALL=C sort | tr '\n' ' ')
  want=".ovh/activity.jsonl BRIEF.md out/check/clip.mp4 out/check/repro/BRIEF.md out/check/repro/cut.mp4 out/check/repro/source.js out/film-4k.bili.mp4 out/film-4k.bili.mp4.deliver.json out/film-4k.mp4 "
  if [ $rc = 0 ] && [ $rc2 = 0 ] && [ $rc3 = 0 ] && [ "$left" = "$want" ] && [ -f "$t/home/trash3/draft.mp4" ] \
    && printf '%s' "$a" | grep -q "record out/film-4k.bili.mp4.deliver.json stays, and what it names): out/film-4k.bili.mp4, out/film-4k.mp4" \
    && printf '%s' "$a" | grep -Eq '^ +[0-9.]+ [KMG]?B  out/check/$' && printf '%s' "$a" | grep -Eq '^ +[0-9.]+ [KMG]?B  out/draft.mp4$' \
    && ! printf '%s' "$a" | grep -Eq '^ +[0-9.]+ [KMG]?B  out/film-4k' \
    && printf '%s' "$b" | grep -q 'the copy out/film-4k.bili.mp4 is not the file recorded' && printf '%s' "$b" | grep -q 'stays in out/check (a video, not a check frame): out/check/clip.mp4' \
    && printf '%s' "$b" | grep -q 'projects of their own inside, kept whole: out/check/repro'
  then ok "clean: deliver's record keeps the copy and its master as the film (a replaced copy is said); out/check goes as rebuilt, a video and a project of its own in it stay"
  else bad "clean after deliver: exit $rc / $rc2 / $rc3, left: $left | $(printf '%s' "$a$b" | tail -c 900)"; fi
  # a record cut short (unreadable): the copy its file name names still stays, never listed as a render to clear
  c="$t/cl4"; mkdir -p "$c/out"; printf x > "$c/BRIEF.md"; cp "$t/master.mp4" "$c/out/final.mp4"
  vh deliver "$c/out/final.mp4" --out "$c/out/upload.mp4" --psnr off >/dev/null 2>&1 && printf '{' > "$c/out/upload.mp4.deliver.json"
  a=$(vh clean "$c" 2>&1); rc=$?
  if [ $rc = 0 ] && printf '%s' "$a" | grep -q 'not a record bin/vh deliver can read; the copy its name names stays' \
    && printf '%s' "$a" | grep -q 'deliver.json stays, and what it names): out/upload.mp4' && ! printf '%s' "$a" | grep -Eq '^ +[0-9.]+ [KMG]?B  out/upload.mp4$'
  then ok "clean: an unreadable delivery record still keeps the copy its name names"
  else bad "clean with a broken delivery record (rc $rc): $(printf '%s' "$a" | tail -c 600)"; fi
  # spec: the file against the BRIEF's Output and Resolution lines (python3 only)
  mkdir -p "$t/sp/out"
  sp() { ffmpeg -nostdin -v error -f lavfi -i "color=c=0x202020:s=${1}:r=${2}:d=${5:-1},${3}" -pix_fmt yuv420p "$t/sp/out/$4.mp4"; }
  sp 320x180 30 "drawbox=x=40:y=40:w=80:h=40:c=white:t=fill,drawbox=x=200:y=100:w=60:h=40:c=orange:t=fill" ref
  sp 640x360 30 "drawbox=x=80:y=80:w=160:h=80:c=white:t=fill,drawbox=x=400:y=200:w=120:h=80:c=orange:t=fill" x2
  sp 640x360 30 "drawbox=x=80:y=80:w=160:h=80:c=white:t=fill,drawbox=x=400:y=200:w=120:h=80:c=orange:t=fill,noise=alls=30:allf=t+u" noisy
  sp 640x360 30 "drawbox=x=80:y=80:w=320:h=160:c=white:t=fill,drawbox=x=400:y=200:w=120:h=80:c=orange:t=fill" big
  sp 320x180 25 "drawbox=x=40:y=40:w=80:h=40:c=white:t=fill" fps25
  sp 160x90 15 "drawbox=x=20:y=20:w=40:h=20:c=white:t=fill" draft
  sp 320x180 30 "drawbox=x=40:y=40:w=80:h=40:c=white:t=fill" long 2
  brief() { printf '%s\n' '# BRIEF' '## Spec' "- Output: $1" "- Resolution: $2  <!-- 1080p | 4k -->" > "$t/sp/BRIEF.md"; }
  brief '320x180, 30 fps, exactly 1.0s (30 frames)' 1080p
  a=$(vh check "$t/sp/out/ref.mp4" 2>&1); rc=$?; b=$(vh check "$t/sp/out/x2.mp4" 2>&1); rb=$?; c=$(vh check "$t/sp/out/fps25.mp4" 2>&1); rcc=$?
  case "$rc:$a|$rb:$b|$rcc:$c" in 0:*"spec: 320x180, 30 fps, 30 frames"*"|1:"*"FAIL frame 640x360"*"Resolution: 1080p, 4k"*"|1:"*"FAIL 25.000 fps, the BRIEF says 30"*)
      ok "check compares the file with the BRIEF: size, a 4K the BRIEF doesn't list, frame rate" ;; *) bad "check against the BRIEF ($rc/$rb/$rcc): $a | $b | $c" ;; esac
  a=$(vh check "$t/sp/out/long.mp4" 2>&1); rc=$?; b=$(vh check "$t/sp/out/draft.mp4" 2>&1); rb=$?
  case "$rc:$a|$rb:$b" in 1:*"FAIL 2.000 s of picture, the BRIEF says exactly 1.0 s"*"|0:"*"WARN 160x90 is smaller than every delivery"*) ok "check: a wrong length fails; a smaller draft only warns" ;;
    *) bad "check length / draft ($rc/$rb): $a | $b" ;; esac
  brief '320x180, 30 fps, exactly 1.0s (30 frames)' '1080p、4k'; a=$(vh check "$t/sp/out/x2.mp4" 2>&1); rc=$?
  brief '320x180, 30 fps, {2–3}s' 1080p; b=$(vh check "$t/sp/out/ref.mp4" 2>&1); rb=$?
  brief '320x180, 30 fps, 约 5 s（150 帧）' 1080p; c=$(vh check "$t/sp/out/ref.mp4" 2>&1); rcc=$?
  case "$rc:$a|$rb:$b|$rcc:$c" in 0:*"spec: 640x360"*"|0:"*"WARN 1.0 s, outside the BRIEF's 2–3 s"*"|0:"*"spec: 320x180"*)
      case "$b$c" in *placeholders*|*FAIL*) bad "check: a range or an approximate length was misread: $b | $c" ;; *) ok "check reads 1080p、4k, warns outside a range, skips approximate lengths" ;; esac ;;
    *) bad "check: separators / range / approximate ($rc/$rb/$rcc): $a | $b | $c" ;; esac
  brief '320x180, 30 fps, exactly 1.0s (30 frames)' '1080p, 4k'
  # check: one odd frame in a moving clip fails with its time; the same clip without it, or with a two-frame flash, passes
  if command -v uv >/dev/null || python3 -c "import numpy" 2>/dev/null; then
    for a in "clean:0" "odd:eq(n,30)" "flash2:between(n,30,31)"; do
      ffmpeg -nostdin -v error -f lavfi -i testsrc=s=320x180:r=30:d=2 -vf "drawbox=c=red:t=fill:enable='${a#*:}'" -pix_fmt yuv420p "$t/${a%%:*}.mp4"; done
    a=$(vh check "$t/clean.mp4" 2>&1) && o=$(vh check "$t/flash2.mp4" 2>&1) && case "$a$o" in *"no isolated frames in 60"*"no isolated frames in 60"*) true ;; *) false ;; esac \
      && ok "check passes a clip without an odd frame, and a two-frame flash" || bad "check on clean / two-frame flash clips: $a $o"
    a=$(vh check "$t/odd.mp4" 2>&1); rc=$?
    case "$rc:$a" in 1:*"1 isolated frame(s) in 60: 1.000 s"*"--no-browser-gpu"*) ok "check fails on one odd frame and names its time" ;; *) bad "check on one odd frame (rc $rc): $a" ;; esac
    a=$(vh check "$t/odd.mp4" --allow 0.4,1.0 2>&1); rc=$?
    case "$rc:$a" in 0:*"no isolated frames in 60"*"declared (--allow, this run only): 1.000 s"*) ok "check --allow: a declared flash is listed and passes" ;; *) bad "check --allow (rc $rc): $a" ;; esac
    a=$(vh check "$t/odd.mp4" --allow 0.9-1.1 2>&1); rc=$?
    case "$rc:$a" in 0:*"declared (--allow, this run only): 1.000 s"*) ok "check --allow takes a span a-b" ;; *) bad "check --allow span (rc $rc): $a" ;; esac
    # an odd frame every 15 frames (a bounce landing on its still point once a cycle) is periodic motion, not a glitch
    ffmpeg -nostdin -v error -f lavfi -i color=c=0x404040:s=320x180:r=30:d=3 -vf "drawbox=x=100:y=60:w=60:h=60:c=white:t=fill:enable='eq(mod(n\,15)\,7)'" -pix_fmt yuv420p "$t/periodic.mp4"
    a=$(vh check "$t/periodic.mp4" 2>&1); rc=$?
    case "$rc:$a" in 0:*"no isolated frames in 90"*"periodic: 6 small frames, one every 15 frames (0.50 s)"*) ok "check: evenly spaced odd frames are periodic motion, said and not failed" ;; *) bad "check on periodic odd frames (rc $rc): $a" ;; esac
    # motion: 2 s of a moving pattern, then a hard cut to a pale still picture for 4 s: a cut that flashes and a still stretch
    ffmpeg -nostdin -v error -f lavfi -i testsrc2=s=320x180:r=30:d=2 -f lavfi -i color=c=0xE0E0E0:s=320x180:r=30:d=4 \
      -filter_complex "[0:v]lutyuv=y=val*0.4,format=yuv420p[a];[1:v]format=yuv420p[b];[a][b]concat=n=2:v=1[v]" -map "[v]" -pix_fmt yuv420p "$t/still.mp4"
    a=$(vh check "$t/still.mp4" 2>&1); rc=$?
    case "$rc:$a" in 0:*"motion: "*"1 hard cut(s)"*"static: 1 stretch(es) of 3 s or more"*"2.00–6.00 s (frozen)"*"cuts: 1 hard cut(s) from dark to bright"*"2.00 s"*) ok "check --motion: a still stretch and a cut from dark to bright are warnings, the exit status untouched" ;;
      *) bad "check on a still stretch and a bright cut (rc $rc): $a" ;; esac
    # the publishing copy in PACKAGING.md: a Bilibili description of 2100 characters is over its 2000 (said, not a failure)
    { printf '%s\n' '# PACKAGING' '## 发布文案' '### B站' '标题：一个够短的标题' '标签：科普, 物理' '简介：'; python3 -c "print('字' * 2100)"; printf '%s\n' '### YouTube' 'Title: short'; } > "$t/sp/PACKAGING.md"
    a=$(vh check "$t/sp/out/ref.mp4" 2>&1); rc=$?
    case "$rc:$a" in 0:*"over a platform's limit"*"B站: ✓ 标题 title 7 characters"*"✗ 简介 description 2100 characters (limit 2000"*"YouTube: ✓ 标题 title 5 characters"*) ok "check measures the publishing copy against the platforms' limits and says what is over" ;;
      *) bad "check on the publishing copy (rc $rc): $(printf '%s' "$a" | tail -c 600)" ;; esac
    rm -f "$t/sp/PACKAGING.md"
    a=$(vh check "$t/odd.mp4" --allow 1s 2>&1); rc=$?
    [ $rc = 1 ] && ok "check --allow with a typo fails instead of skipping the scan" || bad "check --allow 1s exited $rc: $a"
    # confirmed.json: a designed flash confirmed in the project (why, evidence, the key the scan printed) passes while the
    # picture there is the same: a re-encode keeps it, another flash at that time lapses it, a moved flash leaves it unused
    mkdir -p "$t/cf/audio" && printf '%s\n' '# BRIEF' '- Effort: quick' > "$t/cf/BRIEF.md" && printf '%s\n' '# STORYBOARD' 'S01 a red flash' > "$t/cf/STORYBOARD.md"
    cp "$t/odd.mp4" "$t/cf/odd.mp4"
    ffmpeg -nostdin -v error -i "$t/odd.mp4" -c:v libx264 -crf 28 -pix_fmt yuv420p "$t/cf/odd-crf28.mp4"
    for a in "blue:blue:30" "late:red:45"; do IFS=: read -r f c n <<< "$a"
      ffmpeg -nostdin -v error -f lavfi -i testsrc=s=320x180:r=30:d=2 -vf "drawbox=c=$c:t=fill:enable='eq(n,$n)'" -pix_fmt yuv420p "$t/cf/odd-$f.mp4"; done
    fill() { python3 -c 'import json, sys; json.dump({"items": [dict(json.loads(l.split("confirm? ", 1)[1]), why="the red flash", evidence=sys.argv[1]) for l in sys.stdin if "confirm? {" in l]}, open(sys.argv[2], "w"))' "$@"; }
    a=$(vh check "$t/cf/odd.mp4" 2>&1); rc=$?
    case "$rc:$a" in 1:*"1 isolated frame(s) in 60: 1.000 s"*'confirm? {"tool": "check.iso", "at": "1.000", "key": "pic:'*) ok "check in a project offers a confirm? line for an isolated frame" ;; *) bad "check offers no confirm? line (rc $rc): $a" ;; esac
    printf '%s\n' "$a" | fill STORYBOARD.md#S01 "$t/cf/confirmed.json"
    a=$(vh check "$t/cf/odd.mp4" 2>&1); rc=$?; b=$(vh check "$t/cf/odd-crf28.mp4" 2>&1); rb=$?
    case "$rc:$a|$rb:$b" in 0:*"1 isolated frame(s) in 60: 1.000 s · all confirmed (confirmed.json)"*"confirmed (已确认, confirmed.json): isolated frame at 1 s · the red flash"*"|0:"*"all confirmed"*)
        ok "check: a confirmed flash keeps its raw line, says confirmed and passes; a CRF 28 copy keeps the confirmation" ;; *) bad "check with a confirmation ($rc/$rb): $a | $b" ;; esac
    a=$(vh check "$t/cf/odd-blue.mp4" 2>&1); rc=$?; b=$(vh check "$t/cf/odd-late.mp4" 2>&1); rb=$?
    case "$rc:$a|$rb:$b" in 1:*"LAPSED (已失效"*"isolated frame at 1 s: the picture there changed"*"|1:"*"1.500 s"*"unused (confirmed.json): isolated frame at 1 s"*'"at": "1.500"'*)
        ok "check: another flash at the confirmed time lapses it, a moved one leaves it unused and fails" ;; *) bad "check on a changed or moved flash ($rc/$rb): $a | $b" ;; esac
    printf '%s\n' "$a" | fill NOTES-missing.md "$t/cf/c2.json"; printf '%s\n' "$a" | fill STORYBOARD.md "$t/cf/c3.json"
    python3 - "$t/cf" <<'PY'
import json, sys
d = sys.argv[1]; good = json.load(open(d + "/c3.json"))["items"][0]
json.dump({"items": [json.load(open(d + "/c2.json"))["items"][0], dict(good, why=" "), dict(good, tool="check.static"),
                     dict(good, evidence="audio/"), dict(good, evidence="../outside.md"), dict(good, evidence="link.md S01")]}, open(d + "/confirmed.json", "w"))
PY
    echo outside > "$t/outside.md"; ln -s "$t/outside.md" "$t/cf/link.md"
    a=$(vh check "$t/cf/odd-blue.mp4" 2>&1); rc=$?
    case "$rc:$a" in 1:*"item 1"*"evidence: NOTES-missing.md is not in the project"*"item 2"*"no why"*"item 3"*"the motion lines are advice"*"item 4"*"evidence: audio/ is a folder, not a file"*"item 5"*"evidence: ../outside.md is outside the project"*"item 6"*"evidence: link.md is outside the project"*)
        ok "check refuses an entry without evidence on file, without why, for a motion warning, or with evidence that is a folder, outside the project or a link out of it" ;;
      *) bad "check took a bad entry (rc $rc): $a" ;; esac
    printf '{"items": [' > "$t/cf/confirmed.json"; a=$(vh check "$t/cf/odd.mp4" 2>&1); rc=$?
    case "$rc:$a" in 1:*"bad --allow or confirmed.json"*) ok "check fails on an unreadable confirmed.json instead of skipping the scan" ;; *) bad "check on a broken confirmed.json (rc $rc): $a" ;; esac
    rm -f "$t/cf/confirmed.json"
    a=$(vh check "$t/cf/odd.mp4" --allow 1.0 2>&1); rc=$?
    case "$rc:$a" in 0:*"declared (--allow, this run only): 1.000 s; to keep a declaration, confirm it in "*"/cf/confirmed.json"*) ok "check --allow says it is for this run only and where to confirm for good" ;; *) bad "check --allow in a project (rc $rc): $a" ;; esac
    # --json: the same checks as findings (kind, severity, time, frame, evidence, confirmed), on stdout and kept as
    # out/check/<name>.check.json; the exit status as without it; a confirmation from the record's own entry passes it
    a=$(vh check "$t/cf/odd.mp4" --json 2>/dev/null); rc=$?
    python3 - "$t/cf" "$a" <<'PY' > "$t/cf/j1.txt" 2>&1; rc2=$?
import json, os, sys
d, out = sys.argv[1], sys.argv[2]
j = json.loads(out); rec = json.load(open(d + "/out/check/odd.check.json", encoding="utf-8"))
iso = [f for f in j["findings"] if f["kind"] == "check.iso"]
ok = j == rec and j["version"] == 1 and j["exit"] == 1 and j["verdict"] == "fail" and j["video"] == "odd.mp4" and j["record"] == "out/check/odd.check.json"
st = os.stat(d + "/odd.mp4")   # the film's size and mtime_ns as checked: what status and versions compare with the film later
ok = ok and j["size"] == st.st_size and j["mtime_ns"] == st.st_mtime_ns
ok = ok and len(iso) == 1 and iso[0]["severity"] == "fail" and iso[0]["t"] == 1.0 and iso[0]["frame"] == 30 and iso[0]["confirmed"] is False
ok = ok and iso[0]["confirm"]["tool"] == "check.iso" and iso[0]["evidence"]["key"].startswith("pic:") and j["counts"]["fail"] == 1
json.dump({"items": [dict(iso[0]["confirm"], why="the red flash", evidence="STORYBOARD.md S01")]}, open(d + "/confirmed.json", "w"))
print(out[:300]); sys.exit(0 if ok else 1)
PY
    b=$(vh check "$t/cf/odd.mp4" --json 2>/dev/null); rc3=$?
    c=$(vh check "$t/sp/out/fps25.mp4" --json 2>/dev/null); rc4=$?
    d=$(vh check "$t/clean.mp4" --json 2>/dev/null); rc5=$?
    e=$(vh clean "$t/cf" 2>&1)
    if [ $rc = 1 ] && [ $rc2 = 0 ] && [ $rc3 = 0 ] && [ $rc4 = 1 ] && [ $rc5 = 0 ] && [ ! -e "$t/check" ] && python3 - "$b" "$c" "$d" <<'PY'
import json, sys
b, c, d = (json.loads(x) for x in sys.argv[1:4])
iso = [f for f in b["findings"] if f["kind"] == "check.iso"]
spec = [f for f in c["findings"] if f["kind"] == "check.spec"]
sys.exit(0 if iso and iso[0]["confirmed"] is True and iso[0]["severity"] == "info" and iso[0]["evidence"]["entry"]["why"] == "the red flash"
         and b["verdict"] == "pass" and spec and spec[0]["severity"] == "fail" and "25.000 fps" in spec[0]["message"]
         and spec[0]["evidence"]["measured"]["fps"] == 25 and d["record"] is None and d["verdict"] == "pass" else 1)
PY
    then case "$e" in *"stays in out/check (bin/vh check's records): "*"out/check/odd.check.json"*) ok "check --json: findings with kind, severity, time, frame, evidence and confirmation, the same exit status, kept as out/check/<name>.check.json (clean keeps it); none kept outside a project" ;;
        *) bad "clean does not keep check records: $(printf '%s' "$e" | tail -c 300)" ;; esac
    else bad "check --json (rc $rc/$rc2/$rc3/$rc4/$rc5): $(tail -c 300 "$t/cf/j1.txt") | $(printf '%s' "$b$c" | head -c 600)"; fi
    rm -f "$t/cf/confirmed.json"
    # the record keeps the film as it was when the checks began (bin/vh check notes its size and mtime_ns first): a film touched
    # while they run (here, once that note is in the scratch folder, which a private TMPDIR holds alone) is not the one checked, and
    # status says so at once, where the end of the checks would have seen the new film; checkrec.py reads the note, and without it
    # takes the film as it is
    mkdir -p "$t/ck/out" "$t/ck-tmp" && printf -- '- Effort: quick\n' > "$t/ck/BRIEF.md" && cp "$t/clean.mp4" "$t/ck/out/film.mp4"
    TMPDIR="$t/ck-tmp" vh check "$t/ck/out/film.mp4" >/dev/null 2>&1 & pid=$!
    n=0; while [ -z "$(cat "$t"/ck-tmp/vh-check.*/film.txt 2>/dev/null)" ] && [ $n -lt 300 ]; do sleep 0.02; n=$((n + 1)); done
    touch "$t/ck/out/film.mp4"; wait $pid
    a=$(vh status "$t/ck" --json | python3 -c 'import json, sys; c = json.load(sys.stdin)["check"]; print(c["verdict"], c["stale"])')
    mkdir -p "$t/ckd"; printf '12 34\n' > "$t/ckd/film.txt"
    b=$(python3 tools/checkrec.py "$t/ck/out/film.mp4" --dir "$t/ckd" --exit 0 --print | python3 -c 'import json, sys; r = json.load(sys.stdin); print(r["size"], r["mtime_ns"])')
    rm "$t/ckd/film.txt"
    c=$(python3 tools/checkrec.py "$t/ck/out/film.mp4" --dir "$t/ckd" --exit 0 --print | python3 -c 'import json, os, sys; r = json.load(sys.stdin); s = os.stat(sys.argv[1]); print(r["size"] == s.st_size and r["mtime_ns"] == s.st_mtime_ns)' "$t/ck/out/film.mp4")
    [ "$a" = "pass True" ] && [ "$b" = "12 34" ] && [ "$c" = True ] \
      && ok "check: the record keeps the film as it was when the checks began (a film touched meanwhile is stale at once); read from the note, else from the film" \
      || bad "check's record of the film's size and mtime_ns: status said '$a', note read as '$b', no note '$c'"
    # no scratch folder (mktemp -d fails): the same checks, lines and exit, one warning, no record; and freezedetect's
    # duration line (before its end line) goes to its own span, not to the span before
    a=$(vh check "$t/cf/odd.mp4" 2>/dev/null); rc=$?; rm -f "$t/cf/out/check/odd.check.json"
    b=$(TMPDIR="$t/no-such-folder" vh check "$t/cf/odd.mp4" 2>"$t/cf/notmp.err"); rc2=$?
    c=$(TMPDIR="$t/no-such-folder" vh check "$t/cf/odd.mp4" --json 2>/dev/null); rc3=$?
    d=$(python3 -c 'import sys; sys.path.insert(0, "tools"); import checkrec as C
f = C.detect_findings("\n".join("lavfi.freezedetect.freeze_%s: %s" % x for x in [("start", 1), ("duration", 4), ("end", 5), ("start", 10), ("duration", 3.5), ("end", 13.5)]))
print([x["evidence"]["duration"] for x in f])')
    if [ $rc = 1 ] && [ $rc2 = 1 ] && [ "$a" = "$b" ] && [ "$(grep -c 'no scratch folder' "$t/cf/notmp.err")" = 1 ] && [ ! -e "$t/cf/out/check/odd.check.json" ] \
      && [ $rc3 = 1 ] && case "$c" in *'"verdict": "fail", "error": "no scratch folder'*) true ;; *) false ;; esac && [ "$d" = "[4.0, 3.5]" ]
    then ok "check with no scratch folder: the same lines and exit status, one warning, no record; each frozen span keeps its own duration"
    else bad "check without mktemp (rc $rc/$rc2/$rc3): $(tail -c 300 "$t/cf/notmp.err") | $c | freeze durations $d"; fi
    if command -v uv >/dev/null; then   # qa scan: a sparse passage (a dropout), a burst of clicks; the stems' own dip; confirmed.json
      qs() { uv run -q --no-project --with numpy --with scipy python "$ROOT/tools/audio/qa.py" scan "$@"; }
      gen() { ffmpeg -nostdin -v error -f lavfi -i "aevalsrc='0.5*sin(2*PI*220*t)*(1-$1*min(1,max(0,min((t-3)/0.02,(5-t)/0.02))))$2':s=48000:d=10" -ac 2 -c:a pcm_s16le "$3"; }
      k3='+0.4*(eq(n,288000)+eq(n,302400)+eq(n,316800))'
      gen 0.9 "$k3" "$t/cf/audio/mix.wav"; gen 0.97 "$k3" "$t/cf/audio/deeper.wav"; gen 0.9 "${k3%)}+eq(n,309600))" "$t/cf/audio/clicks4.wav"
      ffmpeg -nostdin -v error -i "$t/cf/audio/mix.wav" -af volume=-3dB -c:a aac -b:a 128k "$t/cf/audio/mix.m4a"
      mkdir -p "$t/cf/st1" "$t/cf/st2"; cp "$t/cf/audio/mix.wav" "$t/cf/st1/music.wav"; gen 0 '' "$t/cf/st2/music.wav"
      a=$(qs "$t/cf/audio/mix.wav" --stems "$t/cf/st1" 2>&1); rc=$?; b=$(qs "$t/cf/audio/mix.wav" --stems "$t/cf/st2" 2>&1); rb=$?
      case "$rc:$a|$rb:$b" in 0:*"dropouts (0.1 s RMS < section median − 12 dB): 0 (1 more that the music stem has too: the score's own dynamics)"*"|1:"*"dropouts (0.1 s RMS < section median − 12 dB): 1"*)
          ok "qa scan: a dropout the music stem has too is the score's own; one the music does not have still fails" ;; *) bad "qa dropouts against the music stem ($rc/$rb): $a | $b" ;; esac
      # the music's own dip excuses only the windows it covers: a 3 s dropout over a 0.3 s dip of the stem stays one from 3.35 s;
      # the same for pumping, frame by frame (a 0.25 s dip of the mix over a 60 ms dip of the stem)
      ff() { ffmpeg -nostdin -v error -f lavfi -i "aevalsrc='0.5*sin(2*PI*220*t)*(1-$1)':s=48000:d=10" -ac 2 -c:a pcm_s16le "$2"; }
      mkdir -p "$t/cf/st3" "$t/cf/st4"; ff '0.95*between(t,3,6)' "$t/cf/audio/drop.wav"; ff '0.95*between(t,3,3.3)' "$t/cf/st3/music.wav"
      ff '0.684*between(t,3,3.25)' "$t/cf/audio/pump.wav"; ff '0.684*between(t,3,3.06)' "$t/cf/st4/music.wav"
      a=$(qs "$t/cf/audio/drop.wav" --stems "$t/cf/st3" 2>&1); rc=$?; b=$(qs "$t/cf/audio/pump.wav" --stems "$t/cf/st4" 2>&1); rb=$?
      case "$rc:$a|$rb:$b" in 1:*"dropouts (0.1 s RMS < section median − 12 dB): 1 (1 more that the music stem has too"*"3.35-   5.95 s"*"|1:"*"pumping (dip > 4 dB for ≥ 60 ms, not at a transient music hit): 1"*"3.06-   3.23 s  depth 10.0 dB"*)
          ok "qa scan: a short dip of the music stem excuses only the windows it covers, for dropouts and pumping" ;; *) bad "qa: a short stem dip excused a longer one ($rc/$rb): $a | $b" ;; esac
      a=$(qs "$t/cf/audio/mix.wav" 2>&1); rc=$?
      case "$rc:$a" in 1:*'confirm? {"tool": "qa.dropout", "at": "3.100-4.900"'*'confirm? {"tool": "qa.click", "at": "5.950-6.650", "n": 3'*) ok "qa scan in a project offers confirm? lines for a dropout and a click burst" ;; *) bad "qa scan offers (rc $rc): $a" ;; esac
      printf '%s\n' "$a" | fill STORYBOARD.md#S01 "$t/cf/confirmed.json"
      python3 - "$t/cf/confirmed.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); d["items"].append({"tool": "qa.silence", "at": "7-7.1", "key": "env:V", "why": "a stop", "evidence": "STORYBOARD.md"}); json.dump(d, open(sys.argv[1], "w"))
PY
      a=$(qs "$t/cf/audio/mix.wav" 2>&1); rc=$?; b=$(qs "$t/cf/audio/mix.m4a" 2>&1); rb=$?
      case "$rc:$a|$rb:$b" in 0:*"4.90 s  0s: -32.0 dBFS vs median -12.0  confirmed (已确认)"*"3 in confirmed spans"*"not taken (confirmed.json, item 3"*"digital silence is a floor"*"✓ audio QA passed · 4 confirmed"*"|0:"*"confirmed (已确认, confirmed.json): dropout at 3.1-4.9 s"*"✓ audio QA passed"*)
          ok "qa scan: a confirmed dropout and click burst pass and keep their lines; an AAC copy 3 dB down keeps them; silence is not taken" ;; *) bad "qa scan with confirmations ($rc/$rb): $a | $b" ;; esac
      a=$(qs "$t/cf/audio/deeper.wav" 2>&1); rc=$?; b=$(qs "$t/cf/audio/clicks4.wav" 2>&1); rb=$?
      case "$rc:$a|$rb:$b" in 1:*"LAPSED (已失效, confirmed.json"*"dropout at 3.1-4.9 s: the sound there changed"*"|0:"*"LAPSED (已失效, confirmed.json"*"click span at 5.95-6.65 s: 4 there now, 3 when confirmed"*)
          ok "qa scan: a deeper dip lapses its confirmation and fails; a fourth click lapses the span (a warning)" ;; *) bad "qa scan on changed sound ($rc/$rb): $a | $b" ;; esac
      rm -f "$t/cf/confirmed.json"
      # the score (a beat map's note map): a click on a note's onset is its attack, a rest of the whole score is not a dropout;
      # with a part left out of the map, or none, the dropout counts; every open finding carries its evidence; silence stays
      mkdir -p "$t/qs/st"; gen 0.9 "$k3" "$t/qs/mix.wav"; gen 0 '' "$t/qs/st/music.wav"
      ffmpeg -nostdin -v error -f lavfi -i "aevalsrc='0.5*sin(2*PI*220*t)*(1-between(t,7,7.1))':s=48000:d=10" -ac 2 -c:a pcm_s16le "$t/qs/sil.wav"
      python3 - "$t/qs" <<'PY'
import json, sys
d = sys.argv[1]; n = lambda t, e: {"t": t, "end": e, "midi": 62, "vel": 0.8, "part": "guqin#0"}
base = {"bpm": 60, "offset": 0, "beats": [], "downbeats": [], "sections": [{"name": "a", "start": 0, "end": 10, "bars": 3}], "hits": [],
        "duration": 10, "bars": [[1, 0, 4], [2, 4, 4], [3, 8, 4]], "bars_note": "[bar, start, beats]"}
notes = [n(1.0, 3.0), n(5.0, 5.9), n(6.0, 6.2), n(6.3, 6.5), n(6.6, 6.9), n(7.2, 9.5)]
json.dump({**base, "notes": notes, "unmapped": []}, open(d + "/score.json", "w"))
json.dump({**base, "notes": notes, "unmapped": ["pad#0"]}, open(d + "/partial.json", "w"))
json.dump({**base, "bpm": 480, "bars": [[k + 1, k * 0.5, 4] for k in range(20)], "unmapped": [],
           "notes": [n(k * 0.5 + o, k * 0.5 + o + 0.1) for k in range(20) for o in (0, 0.125)]}, open(d + "/rhythm.json", "w"))
PY
      a=$(qs "$t/qs/mix.wav" "$t/qs/score.json" 2>&1); rc=$?; b=$(qs "$t/qs/mix.wav" 2>&1); rb=$?
      case "$rc:$a" in 0:*"dropouts (0.1 s RMS < section median − 12 dB): 0 (1 more where the score itself is quiet"*"3.10-   4.90 s  a: -32.0 dBFS vs median -12.0 · the score rests here (no note held after 3.00 s; next 5.00 s guqin#0)"*"0 sharp discontinuities outside ±40 ms of designed onsets (0 more at designed onsets, 3 where the score starts a note"*"6.000 s"*"6.00 s guqin#0"*"✓ audio QA passed")
          case "$rb:$b" in *"the score"*) bad "qa scan without a score mentions one: $b" ;;
            1:*"dropouts (0.1 s RMS < section median − 12 dB): 1"*"3.10-   4.90 s"*"3 sharp discontinuities outside ±40 ms of designed onsets (0 more at designed onsets)."*)
              ok "qa scan with a note map: onset clicks are the notes' attacks, a scored rest is not a dropout; without a score both count as before" ;;
            *) bad "qa scan without a score changed (rc $rb): $b" ;; esac ;;
        *) bad "qa scan with a note map (rc $rc): $a" ;; esac
      a=$(qs "$t/qs/mix.wav" "$t/qs/partial.json" --stems "$t/qs/st" --clips "$t/qs/clips" 2>&1); rc=$?
      case "$rc:$a" in 1:*"dropouts (0.1 s RMS < section median − 12 dB): 1"*"8.0 dB under the threshold (-24.0 dBFS: the section median − 12 dB) · bar 1:4.10 · the score rests here"*"parts not in the note map: pad#0"*"stems, the span vs the 0.5 s before: music +0.0 dB"*"3 where the score starts a note"*"clips: 1 excerpt(s)"*)
          if [ -s "$t/qs/clips/0003.100s-dropout.wav" ]; then ok "qa scan: a rest of a partial note map still counts, with its evidence (threshold, bar, score, stems) and a clip named by time"
          else bad "qa scan --clips wrote no 0003.100s-dropout.wav: $(ls "$t/qs/clips" 2>&1)"; fi ;;
        *) bad "qa scan with a partial note map, stems and clips (rc $rc): $a" ;; esac
      a=$(qs "$t/qs/sil.wav" "$t/qs/score.json" 2>&1); rc=$?; b=$(qs "$t/qs/st/music.wav" "$t/qs/rhythm.json" 2>&1); rb=$?
      case "$rc:$a|$rb:$b" in 1:*"digital silence (< −60 dBFS, ≥ 20 ms): 1 inside the span"*"the score rests here (no note held after 6.90 s; next 7.20 s guqin#0) · a failure whatever the score does"*"|0:"*"advice  the score's rhythm (the note map's parts together) is the same 20 bars in a row: bars 1–20"*"✓ audio QA passed (advice above)"*)
          ok "qa scan: digital silence fails where the score rests; 20 identical bars of the note map are advice, not a failure" ;; *) bad "qa scan on silence in a rest, or a repeated rhythm ($rc/$rb): $a | $b" ;; esac
      printf '%s\n' '{"bpm": 120, "sections": [{"name": "a", "bars": 1, "chords": ["i"]}], "parts": [{"inst": "guqin", "note_map": true, "pattern": [[0, 1, "s0"]]},' \
        '{"inst": "piano", "pattern": [[0, 4, "c0"]]}, {"inst": "wind", "gain_db": -20, "quiet": true}]}' > "$t/qs/np.json"
      uv run -q --no-project --with numpy --with scipy python "$ROOT/tools/audio/music.py" "$t/qs/np.json" "$t/qs/np.wav" >/dev/null 2>&1
      a=$(python3 -c 'import json, sys; b = json.load(open(sys.argv[1])); print(b.get("unmapped"), len(b.get("notes", [])))' "$t/qs/np.beats.json" 2>&1)
      case "$a" in "['piano#0'] 1") ok "music: the note map says which parts it leaves out (unmapped; a texture plays no notes)" ;; *) bad "music: unmapped in the beat map: $a" ;; esac
      # what qa and beats are given by mistake (a missing beat map, as --beats too, a missing mix, a list where the beat
      # map goes, a file that is not audio, a missing track, no track): one line that names it and exit 2, no traceback; the
      # event list where the beat map goes, beside --beats, gets the command with - in its place
      printf '[1]' > "$t/qs/list.json"; printf '{}' > "$t/qs/x.wav"; printf '[]' > "$t/qs/ev.json"; printf '{}' > "$t/qs/b.json"; a=""
      for c in "qa.py|nope.json (the beat map)|$t/qs/mix.wav|--beats|$t/qs/nope.json" "qa.py|nope.json (the beat map)|$t/qs/mix.wav|$t/qs/nope.json" \
               "qa.py|nope.wav (the mix)|$t/qs/nope.wav" "qa.py|list.json is not a beat map|$t/qs/mix.wav|$t/qs/list.json" \
               "qa.py|x.wav: no audio ffmpeg can read|$t/qs/x.wav" "beats.py|beats: no such file: $t/qs/nope.wav|$t/qs/nope.wav" "beats.py|beats: which track?|--no-drums" \
               "qa.py|write - in its place: qa $t/qs/mix.wav - $t/qs/ev.json --beats $t/qs/b.json|$t/qs/mix.wav|$t/qs/ev.json|--beats|$t/qs/b.json" \
               "qa.py|--out $t/qs/none/r.txt: no folder $t/qs/none to write it in|$t/qs/mix.wav|--out|$t/qs/none/r.txt" \
               "qa.py|--json $t/qs/none/r.json: no folder $t/qs/none to write it in|mix|$t/qs|--json|$t/qs/none/r.json"; do
        IFS='|' read -r -a cargs <<< "$c"
        b=$(uv run -q --no-project --with numpy --with scipy python "$ROOT/tools/audio/${cargs[0]}" "${cargs[@]:2}" 2>&1); rc=$?
        case "$rc:$b" in *Traceback*) a="$a | ${cargs[0]}: $b" ;; "2:"*"${cargs[1]}"*) [ "$(printf '%s\n' "$b" | wc -l | tr -d ' ')" = 1 ] || a="$a | ${cargs[0]}, more than a line: $b" ;;
          *) a="$a | ${cargs[0]} ${cargs[*]:2} (rc $rc): $b" ;; esac
      done
      [ -z "$a" ] && ok "qa and beats: a missing or wrong input (beat map, --beats, mix, track, a folder for --out / --json) is one line and exit 2, before the analysis, not a traceback" || bad "qa / beats on a wrong input:$a"
      # usage errors of music and qa exit 2 (they were 1): no arguments, one, an unknown option, a bad --length, an unknown example
      a=""
      for c in "music.py" "music.py|$t/qs/np.json" "music.py|$t/qs/np.json|$t/qs/o.wav|--bogus" "music.py|$t/qs/np.json|$t/qs/o.wav|--length|-3" \
               "music.py|--example|nope" "qa.py" "qa.py|mix"; do
        IFS='|' read -r -a cargs <<< "$c"
        uv run -q --no-project --with numpy --with scipy python "$ROOT/tools/audio/${cargs[0]}" "${cargs[@]:1}" >/dev/null 2>&1; rc=$?
        [ $rc = 2 ] || a="$a | ${cargs[*]} exited $rc"
      done
      [ -z "$a" ] && ok "music and qa: usage errors exit 2" || bad "music / qa usage errors:$a"
    fi
    a=$(vh check "$t/a.wav" 2>&1); rc=$?
    case "$rc:$a" in 0:*"isolated"*) bad "check on audio only mentions the frame scan: $a" ;; 0:*) ok "check on an audio file skips the frame scan quietly" ;; *) bad "check on audio only (rc $rc): $a" ;; esac
    # scale: a 2x render against its 1x reference (clips made by the spec tests below)
    a=$(vh check "$t/sp/out/x2.mp4" --against "$t/sp/out/ref.mp4" 2>&1); rc=$?; b=$(vh check "$t/sp/out/noisy.mp4" --against "$t/sp/out/ref.mp4" 2>&1); rb=$?
    case "$rc:$a|$rb:$b" in 0:*"the same picture throughout"*"|0:"*"the same picture throughout"*) ok "check --against: a correct 2x render and a noisy one pass" ;;
      *) bad "check --against on correct clips ($rc/$rb): $a | $b" ;; esac
    a=$(vh check "$t/sp/out/big.mp4" --against "$t/sp/out/ref.mp4" 2>&1); rc=$?
    case "$rc:$a" in 1:*"FAIL 0.00–1.00 s: the picture differs"*"scale-fail-0.000s.png"*"twice the"*) [ -s "$t/sp/out/check/scale-fail-0.000s.png" ] \
        && ok "check --against fails on an element drawn at twice the size, with a comparison image" || bad "check --against wrote no comparison image" ;;
      *) bad "check --against on a 2x element (rc $rc): $a" ;; esac
    a=$(vh check "$t/sp/out/x2.mp4" --against "$t/sp/out/fps25.mp4" 2>&1); rc=$?
    case "$rc:$a" in 1:*"FAIL different frame rate"*"twice the"*) bad "check --against on different cuts points at comparison images: $a" ;;
      1:*"FAIL different frame rate"*) ok "check --against refuses to compare different cuts" ;; *) bad "check --against on different cuts (rc $rc): $a" ;; esac
  else skip "check: isolated frames, --against" "needs uv or numpy"; fi
  rm -rf "$t"
}

# scaffolding and the decision pictures (bin/vh storyboard, rhythm, style compare/apply, cover-preview, music --roll/--length)
# the gate ① record (tools/gatecheck.py): a standard project made from the templates is refused by bin/vh render (before
# any browser) and failed by bin/vh check until REVIEW.md has the decision and DECISIONS.md the concept; the user's
# waiver counts unless it sits under gate ② or ③; quick is not checked
gate_checks() {
  local t p a b c d rc rc2 rc3 rc4
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  vh new math ci-gate --dir "$t" >/dev/null 2>&1; p=$(ls -d "$t"/*-ci-gate 2>/dev/null)
  if [ -z "$p" ] || [ ! -f "$p/REVIEW.md" ]; then bad "gate checks: bin/vh new made no project"; rm -rf "$t"; return; fi
  a=$(vh render "$p" 2>&1); rc=$?
  c=$(vh render "$p" --range 0:1 2>&1)
  mkdir -p "$p/out/review/sketch" && printf '<!doctype html><title>a concept sketch</title>\n' > "$p/out/review/sketch/index.html"
  d=$(vh render "$p/out/review/sketch/index.html" 2>&1)
  case "$rc:$a" in 1:*"no record of gate ①"*"the person's words"*"the decision"*"DECISIONS.md: the concept 立意 row"*"--range a:b"*)
    case "$c|$d" in *"no record of gate"*) bad "render of a part or of a sketch page was held by the gate: $c | $d" ;;
      *) ok "gate record: render refuses a whole standard film made from the templates, naming the lines to write; a part (--range) and a sketch page under out/ still render" ;; esac ;;
    *) bad "render without the gate record (exit $rc): $(printf '%s' "$a" | head -c 600)" ;; esac
  if command -v ffmpeg >/dev/null; then
    mkdir -p "$p/out" && ffmpeg -nostdin -v error -f lavfi -i color=c=0x303030:s=320x180:r=30:d=2 -pix_fmt yuv420p "$p/out/film.mp4"
    b=$(vh check "$p/out/film.mp4" 2>&1); rc2=$?
    case "$rc2:$b" in 1:*"✗"*"no record of gate ①"*) ok "gate record: check fails a standard film without it" ;; *) bad "check without the gate record (exit $rc2): $(printf '%s' "$b" | head -c 400)" ;; esac
  else skip "check without the gate record" "no ffmpeg"; fi
  python3 - "$p" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
r = (p / "REVIEW.md").read_text(encoding="utf-8")
(p / "REVIEW.md").write_text(r.replace("## 关卡 ③ 初版\n", "## 关卡 ③ 初版\n- 用户授权跳过（2026-10-12）。原话：“初版不用给我看”\n", 1), encoding="utf-8")
PY
  python3 tools/gatecheck.py "$p" >/dev/null; rc=$?
  # the template's "定了：{…}" left unfilled is not a decision, whatever record line follows it ("- 改了：…")
  python3 - "$p" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
r = (p / "REVIEW.md").read_text(encoding="utf-8").replace('- 原话："……"', '- 原话："选 B"', 1).replace("- 定了：{…}　改了：{…}", "- 定了：{…}　改了：{…}\n- 改了：结尾短一点", 1)
(p / "REVIEW.md").write_text(r, encoding="utf-8")
d = (p / "DECISIONS.md").read_text(encoding="utf-8").replace("| concept 立意 | {own / review / delegate} | {待定 / 已定（关卡 ①）} |", "| concept 立意 | own | 已定（关卡 ①）：B |", 1)
(p / "DECISIONS.md").write_text(d, encoding="utf-8")
PY
  python3 tools/gatecheck.py "$p" >/dev/null; rc4=$?
  cp "$ROOT/templates/REVIEW.md" "$p/"
  python3 - "$p" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
r = (p / "REVIEW.md").read_text(encoding="utf-8").replace("- 定了：{…}　改了：{…}", "- 定了：立意卡 B　改了：结尾短一点", 1).replace('- 原话："……"', '- 原话："选 B，结尾再短一点"', 1)
(p / "REVIEW.md").write_text(r, encoding="utf-8")
d = (p / "DECISIONS.md").read_text(encoding="utf-8").replace("| concept 立意 | {own / review / delegate} | {待定 / 已定（关卡 ①）} |", "| concept 立意 | own | 已定（关卡 ①）：B |", 1)
(p / "DECISIONS.md").write_text(d, encoding="utf-8")
PY
  a=$(python3 tools/gatecheck.py "$p"); rc2=$?
  cp "$ROOT/templates/REVIEW.md" "$ROOT/templates/DECISIONS.md" "$p/" && python3 - "$p" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
r = (p / "REVIEW.md").read_text(encoding="utf-8")
(p / "REVIEW.md").write_text(r.replace("## 关卡 ① 立意和大纲\n", "## 关卡 ① 立意和大纲\n- 用户授权跳过（2026-10-12）。原话：“你直接做，中间不用我看”\n", 1), encoding="utf-8")
PY
  b=$(python3 tools/gatecheck.py "$p"); rc3=$?
  if [ $rc = 1 ] && [ "$rc4" = 1 ] && [ $rc2 = 0 ] && [ $rc3 = 0 ] && printf '%s' "$a" | grep -q "gate ① decided" && printf '%s' "$b" | grep -q "waived in the user's own words (2026-10-12"
  then ok "gate record: the decision and the concept row pass; an unfilled 定了：{…} with a line after it does not; the user's waiver passes under gate ①, not under gate ③ alone"
  else bad "gate record with the lines filled in ($rc/$rc4/$rc2/$rc3): $a | $b"; fi
  python3 -c "import sys, re; f = sys.argv[1]; s = open(f, encoding='utf-8').read(); open(f, 'w', encoding='utf-8').write(re.sub(r'(?m)^- Effort: standard', '- Effort: quick', s))" "$p/BRIEF.md" && cp "$ROOT/templates/REVIEW.md" "$p/"
  a=$(python3 tools/gatecheck.py "$p"); rc=$?
  [ $rc = 0 ] && printf '%s' "$a" | grep -q "Effort quick" && ok "gate record: a quick project is not checked" || bad "gate record on quick (exit $rc): $a"
  rm -rf "$t"
}

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
  vh new math ci-x --aspect 16:9 >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "new --aspect is refused for a non-HyperFrames type" || bad "new math --aspect exited $rc"
  vh new short ci-x --aspect 4:3 >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "new --aspect rejects 4:3" || bad "new --aspect 4:3 exited $rc"
  a=$(vh new short ci-x --aspect 4:5 --res 4k 2>&1); rc=$?; [ $rc = 2 ] && case "$a" in *"no 4K preset for 4:5"*) true ;; *) false ;; esac \
    && ok "new refuses 4K for a 4:5 frame (HyperFrames has no preset)" || bad "new --aspect 4:5 --res 4k (rc $rc): $a"
  a=$(vh new math ci-x --aspect 9:16 2>&1); rc=$?; case "$rc:$a" in 2:*"manim.cfg"*) ok "new --aspect on a Manim type points to manim.cfg" ;; *) bad "new math --aspect (rc $rc): $a" ;; esac
  mkdir -p "$t/hfi"; a=$(vh hf-init "$t/hfi" landscape-4k 2>&1); rc=$?; b=$(vh hf-init "$t/hfi" 2:3 2>&1); rb=$?
  case "$rc:$a|$rb:$b" in 2:*"4K is a render flag"*"|2:"*"unknown frame 2:3"*) [ -z "$(ls -A "$t/hfi")" ] && ok "hf-init refuses a 4K preset and an unknown frame before scaffolding (exit 2)" || bad "hf-init wrote files after refusing" ;;
    *) bad "hf-init frame check ($rc/$rb): $a | $b" ;; esac
  # 4:5: the BRIEF's lines (a pinned version that does not exist makes the scaffold fail fast, offline too; new goes on without it)
  a=$(HYPERFRAMES_VERSION=0.0.0-ci OVH_PROJECTS="$t/a45" vh new short ci-45 --aspect 4:5 2>&1); d=$(ls -d "$t"/a45/*-ci-45 2>/dev/null)
  if [ -n "$d" ] && grep -q '^- Output: 1080x1350,' "$d/BRIEF.md" && grep -q '^- Watch on: phone' "$d/BRIEF.md" && grep -q '画幅 4:5（1080x1350' "$d/BRIEF.md"; then
    case "$a" in *"retry later: bin/vh hf-init"*" 4:5"*) ok "new --aspect 4:5 writes the BRIEF's frame lines, and a failed scaffold's retry hint keeps 4:5" ;; *) bad "new --aspect 4:5 retry hint: $a" ;; esac
  else bad "new --aspect 4:5 BRIEF: $a"; fi
  a=$(vh new handdrawn ci-x --res 4k 2>&1); rc=$?; [ $rc = 2 ] && case "$a" in *"no 4K output"*) true ;; *) false ;; esac && ok "new --res 4k is refused for the hand-drawn engine" || bad "new handdrawn --res 4k exited $rc: $a"
  # the hand-drawn engine's window.film gives its frame rate (PROJECT.fps, else render.mjs's 24), as canvas-film's does
  a=$(node -e 'const vm = require("vm"), fs = require("fs"), out = [];
for (const extra of ["", "PROJECT.fps = 30;"]) {
  const g = vm.createContext({ console, setTimeout }); g.window = g.self = g; g.location = { search: "" };
  vm.runInContext(fs.readFileSync("engines/ClaudeAnimationBase/src/config.js", "utf8").replace("const PROJECT", "var PROJECT") + extra, g);
  vm.runInContext(fs.readFileSync("engines/ClaudeAnimationBase/src/core.js", "utf8"), g); out.push(vm.runInContext("window.film.fps", g)); }
console.log(out.join(" "))' 2>&1)
  [ "$a" = "24 30" ] && ok "ClaudeAnimationBase: window.film.fps is PROJECT.fps, 24 without it" || bad "ClaudeAnimationBase window.film.fps (want 24 30): $a"
  a=$(vh new short ci-x --watch tv 2>&1); rc=$?; [ $rc = 2 ] && case "$a" in *"unknown --watch"*) true ;; *) false ;; esac && ok "new --watch rejects an unknown target" || bad "new --watch tv exited $rc: $a"
  a=$(vh new short ci-x --watch feed 2>&1); rc=$?; [ $rc = 2 ] && case "$a" in *"already --watch phone"*) true ;; *) false ;; esac && ok "new refuses a feed target for a vertical frame" || bad "new short --watch feed exited $rc: $a"
  a=$(vh new promo ci-x --watch phone 2>&1); rc=$?; [ $rc = 2 ] && case "$a" in *"--watch feed"*) true ;; *) false ;; esac && ok "new refuses a phone target for a landscape frame" || bad "new promo --watch phone exited $rc: $a"
  vh new math ci-x --watch phone >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "new refuses a phone target for a Manim (landscape) type" || bad "new math --watch phone exited $rc"
  for bad_style in "dark-math,_swatch" "Dark-Math" "../styles/ink-wash" ","; do
    vh new math ci-x --style "$bad_style" >/dev/null 2>&1; rc=$?; [ $rc = 2 ] || bad "new --style '$bad_style' exited $rc"; done
  ok "new --style rejects a bad name anywhere in the list, paths and an empty list"
  [ -z "$(ls -d "$ROOT"/projects/*-ci-x 2>/dev/null)" ] || bad "a refused new left a project behind"
  # new: where it is watched and the output resolution land in the BRIEF (defaults from the frame, flags override)
  if grep -q '^- Watch on: desktop' "$p/BRIEF.md" && grep -q '^- Resolution: 1080p' "$p/BRIEF.md" \
    && OVH_PROJECTS="$t/w" vh new math ci-w --watch feed --res 4k >/dev/null 2>&1 \
    && grep -q '^- Watch on: feed' "$(ls -d "$t"/w/*-ci-w)/BRIEF.md" && grep -q '^- Resolution: 1080p, 4k' "$(ls -d "$t"/w/*-ci-w)/BRIEF.md" \
    && OVH_PROJECTS="$t/w2" vh new edit ci-e --res 4K >/dev/null 2>&1 && grep -q '^- Watch on: phone' "$(ls -d "$t"/w2/*-ci-e)/BRIEF.md" \
    && grep -q '^- Resolution: 1080p, 4k' "$(ls -d "$t"/w2/*-ci-e)/BRIEF.md"; then ok "new writes Watch on and Resolution into the BRIEF (defaults, flags, the 4K alias)"
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
  vh style apply no-such-style "$p" >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "style apply rejects an unknown preset" || bad "style apply unknown preset exited $rc"
  # readcheck: a budget, and the timed text of a composition without a browser
  a=$(vh readcheck --budget 3.2)
  case "$a" in *"normal pace"*"up to 14 CJK"*"one brisk read"*"up to 16 CJK"*"up to 28 CJK"*) ok "readcheck --budget: the pace's target, the floor, subtitles" ;; *) bad "readcheck --budget 3.2 said: $a" ;; esac
  # no fixed seconds: under one brisk read (CJK/7 + other/20 + 0.8 s, at least 1.5 s) FAILs; under the pace's target only WARNs
  tl=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  printf '%s' '[{"id":"a","text":"CLAUDE.md router","start":0,"end":1.6,"read":"label"},{"id":"b","text":"CLAUDE.md router","start":0,"end":1.6},' \
    '{"id":"c","text":"CLAUDE.md router","start":0,"end":1.6,"pace":"brisk"}]' > "$tl/label.json"
  a=$(vh readcheck "$tl/label.json"); rc=$?
  case "$rc:$a" in 0:*"OK   a"*"lab"*"WARN b"*"normal  1.63s"*"OK   c"*"pace normal, default"*"3/3 pass · 1 WARN"*)
      ok "readcheck: under the pace's target is a WARN (exit 0); a label and a brisk text need one read" ;; *) bad "readcheck WARN band (rc $rc): $a" ;; esac
  printf '%s' '[{"id":"f","text":"CLAUDE.md router","start":0,"end":1.2},{"id":"g","text":"短","start":2,"end":2.9}]' > "$tl/flash.json"
  a=$(vh readcheck "$tl/flash.json"); rc=$?
  case "$rc:$a" in 1:*"FAIL f"*"floor  1.55s"*"FAIL g"*"floor  1.50s"*"2 FAIL"*) ok "readcheck: under the floor FAILs, and nothing passes under 1.5 s" ;; *) bad "readcheck floor (rc $rc): $a" ;; esac
  printf '%s\n' '# BRIEF' '- Pace: relaxed  <!-- relaxed | normal | brisk -->' > "$tl/BRIEF.md"
  a=$(vh readcheck "$tl/label.json"); b=$(vh readcheck "$tl/label.json" --pace brisk); rc=$?
  case "$a" in *"WARN b"*"relaxed  2.00s"*"pace relaxed, Pace in"*)
      case "$rc:$b" in 0:*"OK   b"*"pace brisk, --pace"*) ok "readcheck takes the pace from the BRIEF, and --pace overrides it" ;; *) bad "readcheck --pace brisk (rc $rc): $b" ;; esac ;;
    *) bad "readcheck with a BRIEF Pace: $a" ;; esac
  printf '%s' '[{"id":"x","text":"t","start":0,"end":2,"pace":"fast"}]' > "$tl/badpace.json"
  vh readcheck "$tl/badpace.json" >/dev/null 2>&1; rc=$?
  [ $rc = 2 ] && ok "readcheck refuses a pace that is not relaxed, normal or brisk" || bad "readcheck with a pace of \"fast\" exited $rc"
  # a project's audio/captions.json (what bin/vh captions writes) is the narration: the subtitle rule, unless --mode says otherwise
  mkdir -p "$tl/cap/audio"
  printf '%s' '[{"id":"a","start":0,"end":2.4,"zh":["慢慢地说一句话"]},{"id":"b","start":2.4,"end":3.1,"zh":["这一句太短"]}]' > "$tl/cap/audio/captions.json"
  a=$(vh readcheck "$tl/cap"); rc=$?; b=$(vh readcheck "$tl/cap" --mode onscreen)
  case "$rc:$a" in 1:*"OK   a·zh"*"need   1.80s"*"FAIL b·zh"*"readcheck (subtitle)"*)
      case "$b" in *"readcheck (onscreen"*) ok "readcheck <project> judges its captions by the subtitle rule; --mode still decides" ;; *) bad "readcheck <project> --mode onscreen: $b" ;; esac ;;
    *) bad "readcheck on a project's captions (rc $rc): $a" ;; esac
  # an exported CDPATH must not move bin/vh's own cd (run as bin/vh, its folder is relative)
  mkdir -p "$tl/cdpath/bin"
  a=$(cd "$ROOT" && CDPATH="$tl/cdpath" "$VH_BASH" bin/vh effort standard 2>&1); rc=$?
  [ $rc = 0 ] && printf '%s' "$a" | grep -q '人工关卡' && ok "bin/vh ignores an exported CDPATH" || bad "bin/vh under a CDPATH (exit $rc): $(printf '%s' "$a" | head -3)"
  rm -rf "$tl"
  printf '%s\n' '<html><body><div id="root" data-composition-id="m" data-start="0" data-duration="10">' \
    '<section id="s" class="clip" data-start="0" data-duration="10"><h1 id="t">script-driven</h1></section>' \
    '<div id="c1" class="clip" data-start="1" data-duration="4"><span>四个汉字</span></div>' \
    '<div id="c2" class="clip" data-start="6" data-duration="1.2">太短了的字</div></div><script>var x="<div>";</script></body></html>' > "$p/index.html"
  a=$(vh readcheck "$p/index.html"); rc=$?
  case "$rc:$a" in 1:*"OK   c1"*"FAIL c2"*"pace relaxed, Pace in"*"NOT checked: 1 text block"*) ok "readcheck reads a composition's clips and the new project's Pace (a math project: relaxed; and says what it left out)" ;; *) bad "readcheck index.html (rc $rc): $a" ;; esac
  vh readcheck --export "$p" >/dev/null && grep -q '"id": "c2"' "$p/texts.json" && { vh readcheck "$p" --export >/dev/null 2>&1; [ $? = 2 ]; } \
    && ok "readcheck --export writes texts.json and will not overwrite it" || bad "readcheck --export"
  mkdir "$t/hf-exports"
  a=$(vh readcheck --out "$t/hf-exports" --export "$p/index.html" 2>&1); rc=$?
  if [ $rc = 0 ] && grep -q '"id": "c2"' "$t/hf-exports/texts.json" \
    && vh readcheck "$p/index.html" --export --out "$t/hf-exports" --force >/dev/null
  then ok "readcheck: HyperFrames --export keeps custom folders, argument order and --force"
  else bad "readcheck HyperFrames custom export (exit $rc): $a"; fi
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
    python3 -c "import json, sys; b = json.load(open(sys.argv[1])); sys.exit(0 if abs(float(sys.argv[2]) - 10) < 0.01 and b['fade']['end'] == 10.0 and max(b['beats']) < 10 and b['bars'] == [[k + 1, k * 2, 4] for k in range(5)] else 1)" "$p/audio/music.beats.json" "$a" \
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
  # a score written for another engine (showcase 04's own score_engine.py: bars as [first, last]) or a list: one line, exit 2
  printf '[]' > "$t/list.json"; a=""
  for f in showcase/04-intro-film/audio/score.json showcase/04-intro-film/audio/score.base.json "$t/list.json"; do
    b=$(vh music "$f" "$t/foreign.wav" 2>&1); rc=$?
    case "$rc:$b" in *Traceback*|*Error*) a="$a | $f: $b" ;; "2:music: $f: not a score bin/vh music reads"*'"sections": [{"name"'*)
        case "$f:$b" in *score*.json:*'"engine" is audio/score_engine.py'*|*list.json:*"(a JSON list)"*) ;; *) a="$a | $f does not say why: $b" ;; esac ;;
      *) a="$a | $f (rc $rc): $b" ;; esac
  done
  [ -z "$a" ] && [ ! -e "$t/foreign.wav" ] && ok "music: another engine's score (bars as [first, last]) or a list says it is not one it reads, and what it reads" \
    || bad "music on a foreign score:$a"
  # the part voices that used to stop on a non-zero sample (taiko, saw_pluck, edm_clap, edm_hat) end on zero, every voice does
  if a=$(uv run -q --no-project --with numpy --with scipy python - 2>&1 <<'PY'
import sys
import numpy as np
sys.path.insert(0, "tools/audio"); import music, instruments as ins
R = lambda *k: np.random.default_rng([7, *k]); bad = []
for name, sp in sorted(ins.INSTR.items()):
    for d in (0.12, 0.5):
        for art in ("", "o"):
            if sp.kind == "note": x = sp.fn(60, d, 0.8, R(1), dict(sp.defaults))
            elif sp.kind == "drum": x = sp.fn(0.8, art, d, R(1), dict(sp.defaults), None)
            else: continue
            x = np.asarray(x)
            if np.abs(x[..., -1]).max() > 1e-3 * np.abs(x).max(): bad.append(f"{name} ({d} s{', ' + art if art else ''})")
print(", ".join(sorted(set(bad)))); sys.exit(1 if bad else 0)
PY
  ); then ok "music: every note and drum voice ends on (near) zero, so a note-off is not a click"; else bad "music voices that end abruptly: $a"; fi
  # beats lifts: a breath (0.8 s, 22 dB down, no hits) and the hit after it is the one candidate, ±2 frames; a fade at the end is not one
  if a=$(uv run -q --no-project --with numpy --with scipy python - 2>&1 <<'PY'
import sys
import numpy as np
sys.path.insert(0, "tools/audio"); import beats
SR = 22050; rng = np.random.default_rng(1); n = int(12 * SR); t = np.arange(n) / SR
gain = np.ones(n); gain[(t >= 6.2) & (t < 7.0)] = 0.08; gain[t >= 11.0] = np.linspace(1, 0.05, int((t >= 11.0).sum()))
y = (0.1 * np.sin(2 * np.pi * 110 * t) + 0.03 * rng.standard_normal(n)) * gain; ev = []
for k in range(24):                                   # a hit every 0.5 s, none in the breath or the fade
    b = k * 0.5
    if 6.2 <= b < 7.0 or b >= 11.0: continue
    i, m = int(b * SR), int(0.08 * SR)
    y[i:i + m] += (0.9 if b == 7.0 else 0.4) * np.exp(-np.arange(m) / (0.015 * SR)) * rng.standard_normal(m)
    ev.append({"t": b, "strength": 1.0 if b == 7.0 else 0.6, "on": ["hits"]})
L = beats.lifts(y, SR, ev)
ok = len(L) == 1 and abs(L[0]["t"] - 7.0) <= 2 / 30 and 6.2 <= L[0]["dip"] < 7.0 and L[0]["strength"] > 0.5
merged = beats.accents({"downbeats": [7.01], "hits": [{"t": 7.0, "strength": 0.9}, {"t": 3.0, "strength": 0.2}]})
ok = ok and merged == [{"t": 7.0, "strength": 0.9, "on": ["downbeat", "hits"]}]
print(L, merged); sys.exit(0 if ok else 1)
PY
  ); then ok "beats lifts: the hit after a breath is the one candidate (±2 frames), a fade-out is not; a downbeat and a hit 10 ms apart are one accent"
  else bad "beats lifts: $a"; fi
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
  vh style compare blueprint,no-such >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "style compare rejects an unknown preset (exit 2)" || bad "style compare on an unknown preset exited $rc"
  out=$(vh cover-preview "$ROOT/styles/blueprint/media/poster.jpg" --out "$t/cover.png")
  case "$out" in *"smallest text"*"title stroke "*" px at the smallest slot"*|*"no text line found"*) [ -s "$t/cover.png" ] && ok "cover-preview draws the feed sizes and a legibility line (with the title's stroke width at the smallest slot)" || bad "cover-preview wrote nothing" ;; *) bad "cover-preview said: $out" ;; esac
  rm -rf "$t"
}

# the review desk (bin/vh desk, tools/desk/README.md): its reader on the committed fixtures (zh, and en with a NOTES.md
# whose table is missing, which must come back as text), a server on a free port (the page, the data, a 206 range, and
# what it refuses), a submission that wakes bin/vh desk wait and lands verbatim in REVIEW.md, the watcher's timeout,
# bin/vh new --lang, and bin/vh review's language default
desk_start() { # desk_start <project> <log>: bin/vh desk on a free port in the background; sets desk_pid and desk_url
  local i a; desk_url=""
  "$VH_BASH" "$ROOT/bin/vh" desk "$1" --port 0 > "$2" 2>&1 & desk_pid=$!   # bin/vh execs python: $! is the server
  for i in $(seq 150); do   # up to 30 s; stop early if the server exits
    desk_url=$(sed -n 's#^desk: \(http://127\.0\.0\.1:[0-9]*/\).*#\1#p' "$2"); [ -n "$desk_url" ] && return 0
    kill -0 "$desk_pid" 2>/dev/null || break; sleep 0.2; done
  if kill -0 "$desk_pid" 2>/dev/null; then a="no address after 30 s, still running"; kill "$desk_pid" 2>/dev/null; wait "$desk_pid" 2>/dev/null
  else wait "$desk_pid"; a="exited with $?"; fi
  bad "desk server for $(basename "$1") did not start ($a); its output: $(tr '\n' ' ' < "$2" | head -c 800)$([ -s "$2" ] || echo '(none)')"
  return 1
}
desk_checks() {
  local t pid wpid url i rc a
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  vh desk data tools/desk/fixtures/zh > "$t/zh.json" && vh desk data tools/desk/fixtures/en > "$t/en.json"
  if python3 - "$t/zh.json" "$t/en.json" <<'PY'
import json, sys
zh, en = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
bad = []
def want(cond, what):
    if not cond: bad.append(what)
o = zh["outline"]
want(zh["lang"] == "zh" and zh["project"]["title"] == "一杯水的旅程" and zh["project"]["effort"] == "studio", "zh: lang, title, effort")
want([x["title"] for x in o] == ["拧开水龙头", "水厂和管道", "落进杯子"] and [x["tag"] for x in o] == ["起", "承", "合"], "zh: outline titles and tags")
want([(x["t0"], x["t1"]) for x in o] == [(0, 8), (8, 16), (16, 24)], "zh: outline times")
c = {r["id"]: r for r in zh["captions"]["rows"]}
want(zh["captions"]["kind"] == "caption" and len(c) == 5 and c["c03"]["term"] == "沉淀" and c["c03"]["seg"] == "2", "zh: captions, terms, segments")
want((c["c05"]["t0"], c["c05"]["t1"]) == (16, 24) and c["c04"]["facts"] == ["#1"], "zh: bars → seconds past the beat map, fact refs")
f = {x["id"]: x for x in zh["facts"]}
want(f["#3"]["dropped"] and not f["#1"]["dropped"] and f["#1"]["onscreen"] and [x["done"] for x in zh["fact_todo"]] == [False, True], "zh: facts, struck rows, to-verify")
a = zh["agent_decided"]
want([x["superseded"] for x in a] == [False, True, False] and a[1]["note"] == "（关卡 ① 后作废）" and a[2]["group"] == "关卡 ① 之后", "zh: DECISIONS strikethrough and groups")
h = zh["history"]
want(len(h) == 1 and h[0]["quotes"][0]["text"].startswith("大纲按内容分段") and [n["k"] for n in h[0]["notes"]] == ["定了", "改了"], "zh: REVIEW history")
r = zh["rounds"]
want([x["id"] for x in r] == ["1"] and r[0]["data"]["listen"][0]["t"] == 7.5 and r[0]["data"]["least_sure"][1] == {"id": "", "note": "配乐会不会太甜"}, "zh: the gate page and its listen prompts")
want([s["label"] for s in zh["music"]["sections"]] == ["拧开", "管道", "杯子"], "zh: music section labels from the gate JSON")
want([s["seg"] for s in zh["shots"]["items"]] == ["1", "2", "3"], "zh: shots matched to the outline")
sb = next((d for d in zh["docs"] if d["file"] == "STORYBOARD.md"), None)
want(sb and sb["sections"][0]["title"] == "Shots" and "<li>S1" in sb["sections"][0]["html"] and not zh["warnings"], "zh: STORYBOARD.md (no table) as formatted text")
want(en["lang"] == "en" and [x["title"] for x in en["outline"]][0] == "Open the tap" and en["outline"][0]["tag"] == "setup", "en: lang, outline from English headers")
c = {r["id"]: r for r in en["captions"]["rows"]}
want(en["captions"]["kind"] == "narration" and c["n3"]["seg"] == "3" and c["n2"]["term"] == "settling" and c["n1"]["t0"] == 0.5, "en: narration table")
notes = next((d for d in en["docs"] if d["file"] == "NOTES.md"), {"sections": []})
want(en["facts"] == [] and any("NOTES.md" in w for w in en["warnings"]) and any("water in city pipes" in s["html"] for s in notes["sections"]), "en: NOTES.md without its table comes back as text, with a warning")
want(en["agent_decided"][1]["superseded"] and en["history"][0]["quotes"][0]["text"] == "Name the parts by what happens in them." and en["rounds"] == [], "en: DECISIONS, REVIEW, no gate page")
if bad:
    print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
  then ok "desk reads the zh and en fixtures (outline, captions and terms, bars, facts, ledger, history, gate extras), and a doc without its table as text"
  else bad "desk reader on tools/desk/fixtures"; fi
  # this round is the page bin/vh review made last (.current), else the last in review order, never the newest file;
  # one language rule; markdown in bounded time;
  # the newest submission within one second is the highest -n. (A file, not a heredoc inside $(…): bash 3.2 counts the
  # parentheses in the heredoc's body.)
  cat > "$t/order.py" <<'PY'
import json, os, shutil, subprocess, sys, time
sys.path.insert(0, "tools/desk")
import feedback, reader
bad = []
def want(cond, what):
    if not cond: bad.append(what)
t0 = time.time()
for s in ("*a " * 20000, "[" * 60000, "**a " * 15000, "~~a " * 15000, "`" * 30000, "a](b " * 12000):
    reader.render_md(s)
want(time.time() - t0 < 3, f"long lines took {time.time() - t0:.1f} s")
try:
    h = reader.render_md(">" * 3000 + " x")
    want(h.count("<blockquote>") <= reader.MAX_QUOTE_DEPTH + 1 and h.endswith("x</p>" + "</blockquote>" * h.count("<blockquote>")), "3000 nested quotes")
except RecursionError:
    bad.append("3000 nested quotes: RecursionError")
want(reader.render_md("a *b* c") == "<p>a <em>b</em> c</p>" and reader.render_md("**b** ~~c~~") == "<p><strong>b</strong> <del>c</del></p>", "inline markup")
d = os.path.join(sys.argv[1], "order")
shutil.copytree("tools/desk/fixtures/zh", d)
g = os.path.join(d, "out", "review")
shutil.copy(os.path.join(g, "gate-1.json"), os.path.join(g, "gate-1b.json"))
os.utime(os.path.join(g, "gate-1.json"), (time.time() + 60, time.time() + 60))   # the earlier page touched later
r = reader.read_project(d)
want([x["id"] for x in r["rounds"]] == ["1", "1b"] and r["lang"] == "zh", f"order after a touch: {[x['id'] for x in r['rounds']]}, lang {r['lang']}")
j = json.load(open(os.path.join(g, "gate-1b.json"), encoding="utf-8"))
json.dump(dict(j, lang="en"), open(os.path.join(g, "gate-1b.json"), "w", encoding="utf-8"))
want(reader.read_project(d)["lang"] == "en", "this round's gate JSON lang should override the BRIEF")
fd = os.path.join(g, "feedback")
os.makedirs(fd)
for n in ("1b-20261004-030440", "1b-20261004-030440-2", "1b-20261004-030440-10"):
    json.dump({"round": "1b", "submitted_at": "2026-10-04T03:04:40", "n": n}, open(os.path.join(fd, n + ".json"), "w"))
want(feedback.latest(d)[1]["n"] == "1b-20261004-030440-10", f"latest within one second: {feedback.latest(d)[1]}")
# the page bin/vh review made last is this round (out/review/.current), whatever the stop order or its name
c = os.path.join(sys.argv[1], "current")
shutil.copytree("tools/desk/fixtures/zh", c)
cg = os.path.join(c, "out", "review")
def publish(n):
    shutil.copy(os.path.join(cg, "gate-1.json"), os.path.join(cg, f"gate-{n}.json"))
    return subprocess.run([sys.executable, "tools/review.py", c, n], capture_output=True, text=True).returncode
cur = lambda: reader.read_project(c)["rounds"][-1]["id"]   # noqa: E731
for seq, page in ((["2", "1b"], "1b"), (["3", "E3b"], "E3b"), (["final"], "final"), (["2B"], "2B")):
    rcs = [publish(n) for n in seq]
    want(rcs == [0] * len(seq) and cur() == page, f"published {seq} (exit {rcs}): this round is {cur()}, not {page}")
fd2 = os.path.join(cg, "feedback")
os.makedirs(fd2)
for rid in ("2B", "E3b"):
    json.dump({"round": rid, "submitted_at": "2026-10-04T12:00:00"}, open(os.path.join(fd2, f"{rid}-20261004-120000.json"), "w"))
want([f.name for f, _ in feedback.pending(c)] == ["2B-20261004-120000.json"], f"pending follows .current: {[f.name for f, _ in feedback.pending(c)]}")
os.remove(os.path.join(cg, "gate-2B.json"))   # .current names a page that is gone: the review order decides
want(cur() == "3", f"with .current pointing at a removed page: {cur()}")
# bin/vh review: the page as spelled on disk (APFS finds gate-1d.json for 1D); no gate: this round, not the newest
# file; ids of 1-24 characters; a gate file that links out of the project is not read
shutil.copy(os.path.join(cg, "gate-1.json"), os.path.join(cg, "gate-1d.json"))
rv = lambda *a: subprocess.run([sys.executable, "tools/review.py", c, *a], capture_output=True, text=True)   # noqa: E731
r = rv("1D")
names = os.listdir(cg)
want(r.returncode == 0 and open(os.path.join(cg, ".current")).read().strip() == "1d" and "gate-1d.html" in names and "gate-1D.html" not in names,
     f"review 1D for gate-1d.json: exit {r.returncode}, .current {open(os.path.join(cg, '.current')).read().strip()!r}, {sorted(n for n in names if n.endswith('.html'))}")
publish("E3b")
os.utime(os.path.join(cg, "gate-3.json"), (time.time() + 60, time.time() + 60))
r = rv()
want(r.returncode == 0 and "gate-E3b.html" in r.stderr and "gate-3.json is newer" in r.stderr, f"review with no gate: {r.returncode} {r.stderr[-300:]}")
r = rv("a" * 25)
want(r.returncode == 2 and "1 to 24" in r.stderr, f"a 25-character id: {r.returncode} {r.stderr}")
shutil.copy(os.path.join(cg, "gate-1.json"), os.path.join(sys.argv[1], "outside.json"))
os.symlink(os.path.join(sys.argv[1], "outside.json"), os.path.join(cg, "gate-9.json"))
want("9" not in [x["id"] for x in reader.read_project(c)["rounds"]] and rv("9").returncode == 2, "a gate file linking out of the project was read")
# writers in several processes at once: each _write has its own temp file, .consumed's read-modify-write is locked
code = ("import sys; sys.path.insert(0, 'tools/desk'); import feedback; from pathlib import Path\n"
        "d, k = sys.argv[1], sys.argv[2]\n"
        "for i in range(40):\n"
        "    feedback._write(Path(d) / 'out' / 'review' / 'feedback' / '.listening', k)\n"
        "    feedback.mark_consumed(d, [f'{k}-{i}.json'])\n")
procs = [subprocess.Popen([sys.executable, "-c", code, c, f"w{k}"], stderr=subprocess.PIPE, text=True) for k in range(8)]
errs = [(p.wait(), p.stderr.read()) for p in procs]
parts = [n for n in os.listdir(fd2) if n.endswith(".part")]
want(all(rc == 0 for rc, _ in errs) and len([n for n in feedback.consumed(c) if n.startswith("w")]) == 320 and not parts,
     f"8 concurrent writers: exits {[rc for rc, _ in errs]}, {len(feedback.consumed(c))} names, leftovers {parts}, {[e[-200:] for _, e in errs if e][:1]}")
# the targets a client points at: a span, a chapter, an asset, a concept card; a span's t / t1 come from its target
sub = lambda *its, lang="zh": {"round": "1", "lang": lang, "items": [dict({"status": "change", "text": "x"}, **i) for i in its]}   # noqa: E731
v = feedback.validate(d, sub({"target": "range:1.5-3", "t": 9}, {"target": "chapter:c2"}, {"target": "asset:assets/a b.png"}, {"target": "card:B"}))
want([(i["target"], i.get("t"), i.get("t1")) for i in v["items"]] == [("range:1.5-3", 1.5, 3.0), ("chapter:c2", None, None), ("asset:assets/a b.png", None, None), ("card:B", None, None)],
     f"new targets: {v['items']}")
for bad_t in ("range:3-1", "range:2-2", "range:-1-2", "range:a-b", "range:1", "asset:/etc/passwd", "asset:../x", "asset:a/../../x", "asset:https://x.test/a.png", "card:", "chapter:",
              "range:1.001-1.004", "range:1-2\n", "cap:c1\n", "asset:..\n", "asset: /etc/passwd", "asset:a/ ../x", "asset:a/.. /x", "asset:x ",
              "range:\u0661-\u0662", "range:1-\uff12", "asset:C:\\x", "seg:a\x7f"):   # rounding to equal, a final newline, spaces, other digits
    try:
        feedback.validate(d, sub({"target": bad_t}))
        bad.append(f"{bad_t!r} was taken")
    except ValueError:
        pass
want(feedback.clock(59.96) == "1:00.0" and feedback.clock(12.44) == "0:12.4", f"clock: {feedback.clock(59.96)}, {feedback.clock(12.44)}")
md = feedback.to_markdown(dict(feedback.validate(d, sub({"target": "range:1.5-3"}, {"target": "card:B"}, {"target": "asset:assets/a.png"}, {"target": "chapter:c2"})), submitted_at="t"))
want("- 片段 0:01.5–0:03.0 [range:1.5-3] · 要改：x" in md and "- 立意卡 B [card:B]" in md and "- 素材 assets/a.png [asset:assets/a.png]" in md and "- 章节 c2 [chapter:c2]" in md, f"zh labels: {md}")
md = feedback.to_markdown(dict(feedback.validate(d, sub({"target": "range:75-80", "label": "the bridge"}, lang="en")), submitted_at="t"))
want("- the bridge (1:15.0–1:20.0) [range:75-80] · change: x" in md, f"en label with its span: {md}")
if bad:
    print("; ".join(bad))
sys.exit(1 if bad else 0)
PY
  if a=$(python3 "$t/order.py" "$t"); then ok "desk: this round is the page bin/vh review made last (1b after 2, E3b after 3, final, 2B; pending follows it), else review order (a touched file doesn't win); the gate JSON's lang overrides the BRIEF; long and deeply nested markdown in bounded time; -10 after -2"
    ok "review: 1D renders gate-1d.json as 1d; no gate renders this round (and names a newer file); ids over 24 characters and gate links out of the project are refused; 8 concurrent writers all exit 0 with every name kept"
  else bad "desk order / lang / markdown / latest / review ids / concurrent writers: $a"; fi
  # a server on a free port, on a copy (a submission writes into the project); a hidden file, a link to it, an upper-case
  # .ENV and an SVG with a script in it: none may be served same-origin
  cp -R tools/desk/fixtures/zh "$t/p" && printf '<img src=x onerror=alert(1)>\n' >> "$t/p/STORYBOARD.md"
  printf 'KEY=secret\n' > "$t/p/.env" && ln -s .env "$t/p/visible.txt" && printf 'KEY=secret\n' > "$t/p/keys.ENV"
  printf '<svg xmlns="http://www.w3.org/2000/svg"><script>fetch("/")</script></svg>\n' > "$t/p/ref.svg"
  if ! desk_start "$t/p" "$t/srv.log"; then rm -rf "$t"; return; fi
  pid=$desk_pid; url=$desk_url
  cat > "$t/client.py" <<'PY'
import http.client, json, socket, sys, urllib.parse
u = urllib.parse.urlsplit(sys.argv[1]); proj = sys.argv[2]; what = sys.argv[3]
def req(method, path, body=None, headers=None):
    c = http.client.HTTPConnection(u.hostname, u.port, timeout=10)
    h = {"Host": f"127.0.0.1:{u.port}"}
    h.update(headers or {})
    c.request(method, path, body=body, headers=h)
    r = c.getresponse(); data = r.read(); c.close()
    return r.status, r.headers, data
bad = []
def want(cond, msg):
    if not cond: bad.append(msg)
s, _, page = req("GET", "/")
token = page.decode().split('name="desk-token" content="')[1].split('"')[0]
fb = lambda **k: json.dumps(dict({"round": "1", "lang": "zh", "decisions": {"look": "L2"}, "defaulted": [], "general": "",
    "items": [{"target": "seg:1", "status": "change", "label": "大纲 第 1 段", "text": "开头再快一点 ``` 第 0 帧就要有水声"}]}, **k)).encode()
H = {"Content-Type": "application/json", "X-Desk-Token": token}
if what == "serve":
    s, _, d = req("GET", "/api/data")
    d = json.loads(d) if s == 200 else {}
    sb = next((x for x in d.get("docs", []) if x["file"] == "STORYBOARD.md"), {"sections": [], "intro": ""})
    html = sb["intro"] + "".join(x["html"] for x in sb["sections"])
    want(s == 200 and d["project"]["slug"] == "p" and "&lt;img src=x" in html and "<img src=x" not in html, f"GET /api/data: {s}, markup in a doc escaped")
    raw = open(proj + "/NOTES.md", "rb").read()
    s, h, body = req("GET", "/p/NOTES.md", headers={"Range": "bytes=2-9"})
    want(s == 206 and h["Content-Range"] == f"bytes 2-9/{len(raw)}" and body == raw[2:10], f"Range: {s} {h.get('Content-Range')}")
    s, h, body = req("GET", "/p/NOTES.md")
    want(s == 200 and body == raw and h["Accept-Ranges"] == "bytes", f"whole file: {s}")
    for p in ("/p/NOTES.md", "/p/ref.svg"):   # opened in the browser, a project page runs in an opaque origin
        csp = req("GET", p)[1].get("Content-Security-Policy", "")
        want(csp.startswith("sandbox") and "allow-same-origin" not in csp, f"{p} not sandboxed: {csp!r}")
    for p in ("/p/%2e%2e/BRIEF.md", "/p/..%2f..%2fetc/passwd", "/p/out/review/.desk.json", "/p/nope.md", "/BRIEF.md",
              "/p/.env", "/p/visible.txt", "/p/keys.ENV", "/p/keys.env"):
        want(req("GET", p)[0] == 404, f"{p} served")
    want(req("POST", "/api/feedback", fb(defaulted=5), H)[0] == 400, "defaulted: 5")
    want(req("POST", "/api/feedback", fb(lang=[1]), H)[0] == 400, "lang: [1]")
    want(req("POST", "/api/feedback", b"[" * 200000, H)[0] == 400, "200,000 nested arrays")
    want(req("POST", "/api/feedback", fb(), dict(H, **{"X-Desk-Token": "tök€n".encode("utf-8")}))[0] == 403, "a non-ASCII token")
    sk = socket.create_connection((u.hostname, u.port), timeout=10)   # a body shorter than its Content-Length
    sk.sendall(f"POST /api/feedback HTTP/1.1\r\nHost: 127.0.0.1:{u.port}\r\nContent-Type: application/json\r\n"
               f"X-Desk-Token: {token}\r\nContent-Length: 100\r\n\r\n".encode() + b'{"round": "1"}')
    sk.shutdown(socket.SHUT_WR)
    resp = sk.recv(200)
    sk.close()
    want(resp.split(b" ")[1:2] == [b"400"], f"a short body: {resp[:40]!r}")
    want(req("GET", "/api/data", headers={"Host": "evil.test"})[0] == 403, "another Host answered")
    want(req("POST", "/api/feedback", fb(), {"Content-Type": "application/json"})[0] == 403, "a post without the token")
    want(req("POST", "/api/feedback", fb(), dict(H, Origin="http://evil.test"))[0] == 403, "a post from another origin")
    want(req("POST", "/api/feedback", fb(), dict(H, **{"Content-Type": "text/plain"}))[0] == 415, "a post that isn't JSON")
    want(req("POST", "/api/feedback", fb(round="9"), H)[0] == 400, "a round with no gate page")
    want(req("POST", "/api/feedback", fb(decisions={"look": "L9"}), H)[0] == 400, "an option the gate page doesn't have")
    want(req("POST", "/api/feedback", fb(items=[{"target": "x", "status": "ok"}]), H)[0] == 400, "a bad target")
    want(req("POST", "/api/feedback", fb(items=[{"target": "range:5-2", "status": "change"}]), H)[0] == 400, "a backward range")
    want(req("POST", "/api/feedback", fb(items=[{"target": "asset:../../etc/passwd", "status": "change"}]), H)[0] == 400, "an asset outside the project")
    want(json.loads(req("GET", "/api/status")[2])["listening"] is False, "listening before the watcher")
elif what == "status":
    print(json.loads(req("GET", "/api/status")[2])["listening"])
elif what == "post":   # no watcher: argv[4] is the comment
    s, _, d = req("POST", "/api/feedback", fb(items=[{"target": "seg:2", "status": "change", "label": "大纲 第 2 段", "text": sys.argv[4]}]), H)
    want(s == 200, f"post: {s} {d[:200]}")
elif what == "targets":   # a span, a chapter, an asset and a concept card, as a client sends them
    s, _, d = req("POST", "/api/feedback", fb(items=[{"target": "range:12.4-15", "status": "change", "text": "这一段太慢"},
        {"target": "chapter:c2", "status": "ask", "text": "这一章要不要"}, {"target": "asset:assets/photo.jpg", "status": "change", "text": "换一张"},
        {"target": "card:B", "status": "ok"}]), H)
    want(s == 200, f"targets: {s} {d[:200]}")
else:
    want(json.loads(req("GET", "/api/status")[2])["listening"] is True, "the page doesn't see the watcher")
    s, _, d = req("POST", "/api/feedback", fb(), H)
    want(s == 200 and json.loads(d)["listening"] is True and json.loads(d)["saved"].startswith("out/review/feedback/1-"), f"submit: {s} {d[:200]}")
if bad:
    print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
  if a=$(python3 "$t/client.py" "$url" "$t/p" serve); then ok "desk server: page, data with markup escaped, a 206 range, project files sandboxed; refuses other hosts, paths out of the project, hidden files (also through a link, any case), posts without the token, from another origin or not JSON, an unknown round, option or target; malformed bodies and tokens get 400/403"
  else bad "desk server: $a"; fi
  "$VH_BASH" "$ROOT/bin/vh" desk wait "$t/p" --timeout 30 > "$t/wait.out" 2>&1 & wpid=$!
  for i in $(seq 50); do [ -f "$t/p/out/review/feedback/.listening" ] && break; sleep 0.2; done
  a=$(python3 "$t/client.py" "$url" "$t/p" submit); rc=$?
  wait "$wpid"; i=$?
  if [ $rc = 0 ] && [ $i = 0 ] && grep -q '第 0 帧就要有水声' "$t/wait.out" && [ ! -e "$t/p/out/review/feedback/.listening" ] \
    && python3 - "$t/p/REVIEW.md" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^## 审阅台反馈 · 关卡 1 · .*?(?=^## )", s, re.M | re.S)
sys.exit(0 if m and "开头再快一点 ``` 第 0 帧就要有水声" in m.group(0) and "\n````text\n" in m.group(0)
         and s.index("## 审阅台反馈") < s.index("## 授权跳过怎么记") and "决定 look：L2" in m.group(0) else 1)
PY
  then ok "desk: a submission wakes bin/vh desk wait (exit 0) and goes into REVIEW.md verbatim, fenced, before the template's reference sections"
  else bad "desk submit + wait: client '$a' rc $rc, wait rc $i: $(head -c 300 "$t/wait.out")"; fi
  a=$(vh desk feedback "$t/p" --round 1) && case "$a" in *"第 0 帧就要有水声"*"json: "*) true ;; *) false ;; esac \
    && vh desk feedback "$t/p" --json | python3 -c "import json, sys; d = json.load(sys.stdin); sys.exit(0 if d['decisions'] == {'look': 'L2'} and d['project'] == 'p' else 1)" \
    && ok "desk feedback prints the latest submission (text and --json)" || bad "desk feedback: $a"
  # a submission made while no watcher runs (after a timeout, say) is handed over by the next wait at once, and only once;
  # what desk feedback printed counts as handed over too
  a=$(python3 "$t/client.py" "$url" "$t/p" post "提前到的一条" && vh desk wait "$t/p" --timeout 20 2>&1); rc=$?
  vh desk wait "$t/p" --timeout 1 >/dev/null 2>&1; i=$?
  case "$rc:$i:$a" in 0:3:*"提前到的一条"*) ok "desk wait hands over a submission made before it was armed, at once and only once" ;;
    *) bad "desk wait with a submission already there: rc $rc, then $i: $(printf '%s' "$a" | head -c 300)" ;; esac
  a=$(python3 "$t/client.py" "$url" "$t/p" post "第三条" && vh desk feedback "$t/p")
  vh desk wait "$t/p" --timeout 1 >/dev/null 2>&1; rc=$?
  case "$rc:$a" in 3:*"第三条"*) ok "desk feedback counts what it printed as handed over" ;; *) bad "desk feedback then wait: rc $rc: $(printf '%s' "$a" | head -c 300)" ;; esac
  # the new targets through the server: kept with the span's seconds, printed and written into REVIEW.md readably
  a=$(python3 "$t/client.py" "$url" "$t/p" targets && vh desk feedback "$t/p" --json) && b=$(vh desk feedback "$t/p")
  if python3 - "$a" "$t/p/REVIEW.md" "$b" <<'PY'
import json, sys
d, rv, txt = json.loads(sys.argv[1]), open(sys.argv[2], encoding="utf-8").read(), sys.argv[3]
it = {i["target"]: i for i in d["items"]}
want = ["- 片段 0:12.4–0:15.0 [range:12.4-15] · 要改：这一段太慢", "- 章节 c2 [chapter:c2] · 疑问：这一章要不要", "- 素材 assets/photo.jpg [asset:assets/photo.jpg] · 要改：换一张", "- 立意卡 B [card:B] · 可以"]
sys.exit(0 if (it["range:12.4-15"]["t"], it["range:12.4-15"]["t1"]) == (12.4, 15.0) and all(w in rv and w in txt for w in want) else 1)
PY
  then ok "desk: range, chapter, asset and card targets are taken, keep the span's seconds, and read plainly in desk feedback and REVIEW.md; a backward span or a path out of the project is refused"
  else bad "desk new targets: $(printf '%s' "$a$b" | tail -c 600)"; fi
  # a copy of the project carries the running server's .desk.json and a .listening that names another folder: neither counts
  cp -R "$t/p" "$t/p2" && printf '{"pid": %s, "since": 0, "until": 99999999999, "project": "%s"}\n' "$$" "$t/p" > "$t/p2/out/review/feedback/.listening"
  if desk_start "$t/p2" "$t/srv2.log"; then
    a=$(python3 "$t/client.py" "$desk_url" "$t/p2" status)
    [ "$a" = False ] && ok "desk: a copied project starts its own server, and a .listening from another folder doesn't count" || bad "desk on a copy: listening said '$a'"
    kill "$desk_pid"; wait "$desk_pid" 2>/dev/null
  fi
  # a .listening of this folder and a live pid whose until is not a number of seconds is not listening, and raises nothing
  a=$(python3 - "$t/p2" <<'PY' 2>&1
import json, os, sys, time
sys.path.insert(0, "tools/desk"); import feedback
p = sys.argv[1]; flag = os.path.join(p, "out/review/feedback/.listening")
def said(until):
    with open(flag, "w") as f: json.dump({"pid": os.getpid(), "since": 0, "until": until, "project": os.path.realpath(p)}, f)
    return feedback.listening(p)["listening"]
print(" ".join(str(said(u)) for u in ("soon", [1], "nan", time.time() + 60)))
PY
  )
  [ "$a" = "False False False True" ] && ok "desk: a .listening whose until is not seconds (a word, a list, NaN) is not listening, and is no error" || bad "desk listening on a bad until: $a"
  # desk wait has its signal handlers before it writes .listening: a TERM right after the write (sent from inside the
  # write, so no timing is involved) ends it with 143 and takes the flag away, as one later does
  rm -f "$t/p2/out/review/feedback/.listening"
  a=$(python3 - "$t/p2" <<'PY' 2>&1
import os, subprocess, sys
child = """import os, signal, sys
sys.path.insert(0, "tools/desk"); import feedback
w = feedback._write
def write(p, text):
    w(p, text)
    if p.name == ".listening": os.kill(os.getpid(), signal.SIGTERM)
feedback._write = write
sys.exit(feedback.wait(sys.argv[1], 30, poll=0.05))"""
rc = subprocess.run([sys.executable, "-c", child, sys.argv[1]], capture_output=True).returncode   # -15: killed by it
print(rc, "flag left" if os.path.exists(os.path.join(sys.argv[1], "out/review/feedback/.listening")) else "no flag")
PY
  )
  [ "$a" = "143 no flag" ] && ok "desk wait: a TERM the moment .listening is written ends it with 143 and no flag left" || bad "desk wait TERMed right after its flag: $a"
  a=$(vh desk "$t/p" --port 0 2>&1); case "$a" in *"already serving p"*) ok "desk: a second start points to the running server" ;; *) bad "desk second start: $a" ;; esac
  kill "$pid"; wait "$pid" 2>/dev/null
  [ ! -e "$t/p/out/review/.desk.json" ] && ok "desk: stopping the server removes out/review/.desk.json" || bad "desk left .desk.json behind"
  vh desk wait "$t/p" --timeout 1 > /dev/null 2>&1; rc=$?; [ $rc = 3 ] && ok "desk wait exits 3 on timeout" || bad "desk wait --timeout 1 exited $rc"
  # the language: bin/vh new --lang writes the BRIEF line; bin/vh review takes it when the gate JSON has no lang
  if OVH_PROJECTS="$t/new" vh new math ci-lang --lang en >/dev/null 2>&1 && grep -q '^- Review language: en ' "$t"/new/*-ci-lang/BRIEF.md \
    && OVH_PROJECTS="$t/new" vh new math ci-zh >/dev/null 2>&1 && grep -q '^- Review language: zh ' "$t"/new/*-ci-zh/BRIEF.md; then
    vh new math ci-x --lang fr >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "new --lang writes Review language (default zh) and rejects fr" || bad "new --lang fr exited $rc"
  else bad "new --lang: Review language not written"; fi
  cp -R tools/desk/fixtures/zh "$t/rz" && cp -R tools/desk/fixtures/zh "$t/re" && sed 's/^- Review language: zh /- Review language: en /' tools/desk/fixtures/zh/BRIEF.md > "$t/re/BRIEF.md"
  sed 's/^{/{"lang": "en",/' tools/desk/fixtures/zh/out/review/gate-1.json > "$t/rz/out/review/gate-1b.json"
  if vh review "$t/rz" 1 >/dev/null 2>&1 && vh review "$t/re" 1 >/dev/null 2>&1 && vh review "$t/rz" 1b >/dev/null 2>&1 \
    && grep -q '<html lang="zh-CN">' "$t/rz/out/review/gate-1.html" && grep -q '<html lang="en">' "$t/re/out/review/gate-1.html" \
    && grep -q '<html lang="en">' "$t/rz/out/review/gate-1b.html"
  then ok "review: the gate JSON's lang, else the BRIEF's Review language (the desk's rule), and the desk's extra keys pass"; else bad "review language rule"; fi
  a=$(vh review "$t/rz" 1 2>&1)
  if grep -q '没回的决定按推荐走' "$t/rz/out/review/gate-1.html" && grep -q 'unanswered goes by its recommendation' "$t/re/out/review/gate-1.html" \
    && case "$a" in *"没回的决定按推荐走"*) true ;; *) false ;; esac
  then ok "review: the page and the chat message say a decision left unanswered goes by its recommendation"; else bad "review: unanswered decisions not explained: $a"; fi
  gate_stop_checks "$t"
  rm -rf "$t"
}
# bin/vh gate: one stop in one command. The page channel (a flag, LOCAL.md's 审阅方式, the effort's default) prints the
# chat message and starts nothing; --wait there is refused; a page that breaks a rule sends nothing and starts no desk; the
# desk channel starts the desk in the background (once), adds its address, and with --wait hands over the submission;
# desk --idle stops a desk nobody asks anything
gate_stop_checks() {
  local t=$1 g a b rc rc2 rc3 i pid url
  g="$t/g"; cp -R tools/desk/fixtures/zh "$g"; rm -rf "$g/out/review/feedback" "$g/out/review/.current"
  printf '%s\n' '# LOCAL' '- 审阅方式：{对话 | 审阅页 | 审阅台}（不填按档位）' > "$t/LOCAL-tpl.md"; printf '%s\n' '# LOCAL' '- 审阅方式：对话' > "$t/LOCAL-chat.md"
  a=$(vh gate "$g" 1 --page 2>"$t/g1.err"); rc=$?
  vh gate "$g" 1 --page --wait >/dev/null 2>"$t/g2.err"; rc2=$?
  b=$(OVH_LOCAL_MD="$t/LOCAL-chat.md" vh gate "$g" 1 2>&1)
  if [ $rc = 0 ] && [ $rc2 = 2 ] && case "$a" in *"要你定 1 件事"*"页面："*"/out/review/gate-1.html") true ;; *) false ;; esac \
    && [ "$(cat "$g/out/review/.current")" = 1 ] && [ ! -e "$g/out/review/.desk.json" ] && grep -q 'waits for the review desk' "$t/g2.err" \
    && case "$b" in *"reviewed on the chat (LOCAL.md)"*) true ;; *) false ;; esac && [ ! -e "$g/out/review/.desk.json" ]
  then ok "gate: --page and LOCAL.md's 审阅方式 print the chat message, make the page this round and start no desk; --wait without the desk is refused"
  else bad "gate on the page (rc $rc/$rc2): $a | $(cat "$t/g1.err" "$t/g2.err") | $b"; fi
  # a page that breaks a rule: written, but no message and no desk; a standard project with LOCAL.md's placeholder: the page
  sed 's/"recommend": "L1", //' "$g/out/review/gate-1.json" > "$g/out/review/gate-1b.json"
  a=$(vh gate "$g" 1b --desk --port 0 2>/dev/null); rc=$?
  vh review "$g" 1b >/dev/null 2>&1; rc3=$?
  cp -R "$g" "$t/gs" && sed 's/^- Effort: studio/- Effort: standard/' "$g/BRIEF.md" > "$t/gs/BRIEF.md"
  b=$(OVH_LOCAL_MD="$t/LOCAL-tpl.md" vh gate "$t/gs" 1 2>&1); rc2=$?
  if [ $rc = 1 ] && [ $rc3 = 1 ] && [ -z "$a" ] && [ -f "$g/out/review/gate-1b.html" ] && [ "$(cat "$g/out/review/.current")" = 1 ] && [ ! -e "$g/out/review/.desk.json" ] \
    && [ $rc2 = 0 ] && case "$b" in *"reviewed on the page (effort standard (BRIEF))"*) true ;; *) false ;; esac && [ ! -e "$t/gs/out/review/.desk.json" ]
  then ok "gate and review: a page that breaks a rule is written but sends nothing, starts no desk and does not become this round; LOCAL.md's unfilled line falls back to the effort (standard: the page)"
  else bad "gate with a broken page or a placeholder (rc $rc/$rc3/$rc2, this round $(cat "$g/out/review/.current")): $a | $b"; fi
  # the desk channel (studio): started once in the background, its address in the message; --wait hands over a submission
  a=$(vh gate "$g" 1 --port 0 2>/dev/null); rc=$?
  b=$(vh gate "$g" 1 --port 0 2>&1); rc2=$?
  pid=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["pid"])' "$g/out/review/.desk.json" 2>/dev/null)
  url=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["url"])' "$g/out/review/.desk.json" 2>/dev/null)
  "$VH_BASH" "$ROOT/bin/vh" gate "$g" 1 --wait --timeout 30 > "$t/gw.out" 2>&1 & i=$!
  for rc3 in $(seq 50); do [ -f "$g/out/review/feedback/.listening" ] && break; sleep 0.2; done
  python3 "$t/client.py" "$url" "$g" submit >/dev/null; wait $i; rc3=$?
  if [ $rc = 0 ] && [ $rc2 = 0 ] && [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && case "$a" in *"审阅台：http://127.0.0.1:"*"然后回到这里说一声"*) true ;; *) false ;; esac \
    && case "$b" in *"already serving this project"*) true ;; *) false ;; esac && [ $rc3 = 0 ] && grep -q '我在后台等着' "$t/gw.out" && grep -q '第 0 帧就要有水声' "$t/gw.out" \
    && python3 - "$g/.ovh/activity.jsonl" <<'PY'
import json, sys
recs = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
gates = {r["run"] for r in recs if r["event"] == "start" and r["cmd"] == "gate"}
desk = [r for r in recs if r["event"] == "start" and r["cmd"] == "desk"]
sys.exit(0 if len(desk) == 1 and desk[0].get("parent") in gates and any(r["event"] == "feedback" for r in recs) else 1)
PY
  then ok "gate: the desk channel starts the desk once in the background (its run's parent is the gate), puts its address in the message; --wait hands over the submission"
  else bad "gate on the desk (rc $rc/$rc2/$rc3): $a | $b | $(tail -c 400 "$t/gw.out")"; fi
  [ -z "$pid" ] || { kill "$pid" 2>/dev/null; for i in $(seq 50); do kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done; }
  # desk --idle: a desk nobody asks anything stops by itself, and takes its .desk.json with it
  "$VH_BASH" "$ROOT/bin/vh" desk "$t/gs" --port 0 --idle 1 > "$t/idle.out" 2>&1 & pid=$!
  for i in $(seq 100); do kill -0 $pid 2>/dev/null || break; sleep 0.1; done
  if ! kill -0 $pid 2>/dev/null && grep -q 'no request for 1 s, stopped' "$t/idle.out" && [ ! -e "$t/gs/out/review/.desk.json" ]; then ok "desk --idle: a desk nobody asks anything stops by itself"
  else kill $pid 2>/dev/null; bad "desk --idle 1: $(cat "$t/idle.out")"; fi
}

# bin/vh status: a new standard project works towards gate ①; a page out waits for the person; a desk submission waits for
# the agent until it is handed over and REVIEW.md has its decision, and then the next gate is in progress; a Director stop
# adds its checkpoint; quick skips the gates; the user's waiver skips what it names; a pause waits for the person; a delivery
# record or a final film with a passing check record is delivered; a command running shows; the human view stays short
assets_checks() {   # the asset ledger (tools/assets): the record and its fixtures, the licence table, the ledger's writes on a
  # copy of the fixture project, the budget, a download from recorded responses (no network), the credits
  local t p q a b c d e rc rc2 rc3 rc4 rc5 tone
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  # the validator takes every valid record and the fixture ledger, and refuses every invalid one; JSON Schema agrees
  if a=$(python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "tools/assets")
import ledger
F = Path("tools/assets/fixtures/records")
load = lambda p: json.loads(p.read_text(encoding="utf-8"))   # noqa: E731
bad = [f"{p.name}: {ledger.validate(load(p))}" for p in sorted((F / "valid").glob("*.json")) if ledger.validate(load(p))]
bad += [f"invalid/{p.name} passes" for p in sorted((F / "invalid").glob("*.json")) if not ledger.validate(load(p))]
d = load(Path("tools/assets/fixtures/project/assets/ledger.json"))
bad += [f"the fixture ledger's {r.get('id')}: {ledger.validate(r)}" for r in d["assets"] if ledger.validate(r)]
bad += [] if len(list((F / "invalid").glob("*.json"))) >= 15 else ["fewer than 15 invalid records"]
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
  ); then ok "assets: the record's validator takes the valid fixtures and the fixture ledger, and refuses each invalid one"
  else bad "assets: the record validator on tools/assets/fixtures: $a"; fi
  if command -v uv >/dev/null 2>&1; then
    if a=$(uv run -q --no-project --with "jsonschema==4.25.1" python - 2>&1 <<'PY'
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
S = json.loads(Path("tools/assets/asset.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(S)
v, F = Draft202012Validator(S), Path("tools/assets/fixtures/records")
load = lambda p: json.loads(p.read_text(encoding="utf-8"))   # noqa: E731
bad = [f"{p.name}: {[e.message for e in v.iter_errors(load(p))]}" for p in sorted((F / "valid").glob("*.json")) if not v.is_valid(load(p))]
bad += [f"invalid/{p.name} is valid to JSON Schema" for p in sorted((F / "invalid").glob("*.json")) if v.is_valid(load(p))]
L = v.evolve(schema=S["$defs"]["ledger"])
d = load(Path("tools/assets/fixtures/project/assets/ledger.json"))
bad += [f"the fixture ledger: {e.message}" for e in L.iter_errors(d)]
bad += [] if not L.is_valid(dict(d, assets=d["assets"] + [{"v": 1}])) else ["a ledger with a bad record is valid"]
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
    ); then ok "assets: asset.schema.json is a valid JSON Schema and agrees with the validator on every fixture"
    else bad "assets: JSON Schema on the fixtures: $(printf '%s' "$a" | tail -c 600)"; fi
  else skip "assets: the JSON Schema check" "no uv"; fi
  if a=$(python3 - <<'PY'
import sys
sys.path.insert(0, "tools/assets")
import licenses
bad, n = [], 0
for k, line in enumerate(open("tools/assets/fixtures/licenses.tsv", encoding="utf-8"), 1):
    if line.startswith("#") or not line.strip("\n"):
        continue
    text, url, want = line.rstrip("\n").split("\t")
    got, n = licenses.classify(text, url or None)[0], n + 1
    if got != want:
        bad.append(f"line {k}: {text!r} {url!r} is {got}, not {want}")
ok = [licenses.risks(c) for c in ("cc-by-nc-nd", "cc-by-sa", "unknown", "cc0")] == [["nc", "nd"], ["sa"], ["unknown"], []] \
    and [licenses.accepted(c, "strict") for c in ("cc-by", "cc-by-sa", "generated", "unknown")] == [True, False, True, False] \
    and licenses.accepted("cc-by-nc", "record")
print("\n".join(bad + ([] if ok else ["risks or accepted"])) or n); sys.exit(1 if bad or not ok or n < 40 else 0)
PY
  ); then ok "assets: the licence table classifies its $a lines (CC by name, legal name, code and deed; PD, permissive, agreements, own, generated; anything else unknown)"
  else bad "assets: the licence table: $a"; fi
  # the ledger's writes on a copy of the fixture project; its generated clip from before v1 gets its bytes here (no video in git)
  p="$t/p"; cp -R tools/assets/fixtures/project "$p"; printf 'fixture clip\n' > "$p/assets/genclips/gc-0001/clip.mp4"
  a=$(vh assets check "$p" 2>&1); rc=$?
  b=$(vh assets check "$p" --policy strict 2>&1); rc2=$?
  case "$rc:$rc2|$a|$b" in "0:1|"*"6 record(s) in assets/ledger.json and 1 from generated clips' ledgers"*"! loop"*"non-commercial (taken: Assets: record)"*"pass (0 fail, 1 warn)"*"|"*"✗ loop"*"fail (1 fail"*)
      ok "assets check: a project's records and a generated clip's ledger from before v1, read as it is; NC listed under Assets: record, failed under strict" ;;
    *) bad "assets check on the fixture (exit $rc, $rc2): $a | $b" ;; esac
  printf 'x' > "$p/assets/img/new.png"
  vh assets add "$p" "$p/assets/img/new.png" >/dev/null 2>"$t/e1"; r1=$?
  vh assets add "$p" "$p/assets/img/new.png" --license "CC BY-SA 4.0" --source-url https://example.org/new --author Someone --cost '$0.25' >"$t/o2" 2>&1; r2=$?
  vh assets add "$p" "$p/assets/img/new.png" --license own >/dev/null 2>"$t/e3"; r3=$?
  vh assets add "$p" "$p/assets/img/new.png" --update --class own >"$t/o4" 2>&1; r4=$?
  vh assets remove "$p" loop --why "a CC0 loop instead" >/dev/null 2>&1; r5=$?
  vh assets remove "$p" gc-0001 >/dev/null 2>&1; r6=$?
  printf 'y' > "$p/assets/img/again.png"; vh assets add "$p" "$p/assets/img/again.png" --class own --id loop >/dev/null 2>"$t/e7"; r7=$?
  printf 'more' >> "$p/assets/sfx/knock.wav"; rm "$p/assets/frames/f0002.png"
  a=$(vh assets check "$p" --json 2>/dev/null); rc=$?
  if [ "$r1:$r2:$r3:$r4:$r5:$r6:$r7:$rc" = "2:0:2:0:0:0:2:1" ] && grep -q "where it came from is not said" "$t/e1" && grep -q "on record already as new" "$t/e3" \
     && grep -q "the id loop is taken" "$t/e7" && grep -q 'spent $0.79 of $1.00' "$t/o2" && grep -q "updated new" "$t/o4" \
     && python3 - "$p" "$a" <<'PY'
import json, sys
p, check = sys.argv[1], json.loads(sys.argv[2])
d = json.load(open(f"{p}/assets/ledger.json", encoding="utf-8"))
R = {r["id"]: r for r in d["assets"]}
ev = [f"{e['event']}:{e['id']}" for e in d["events"]][5:]
new = R["new"]
pay = [json.loads(x) for x in open(f"{p}/assets/spend.jsonl", encoding="utf-8")]
fs = {(f["kind"], f["id"]) for f in check["findings"] if f["severity"] == "fail"}
ok = (ev == ["add:new", "update:new", "remove:loop", "remove:gc-0001"]
      and new["license"] == {"name": "CC BY-SA 4.0", "class": "own", "by": "given"} and new["source"]["author"] == "Someone"
      and new["cost"] == {"amount": 0.25, "currency": "USD"} and "updated_at" in new
      and R["loop"]["removed"]["why"] == "a CC0 loop instead" and R["gc-0001"].get("legacy") == "genclip-ledger" and "removed" in R["gc-0001"]
      and [x["amount"] for x in pay] == [0.04, 0.25] and pay[1]["asset"] == "new"
      and fs == {("sha256", "knock"), ("sha256", "frames")} and check["verdict"] == "fail" and check["records"] == 5)
if not ok:
    print(f"{ev} {new} {pay} {fs} {check['records']}")
sys.exit(0 if ok else 1)
PY
  then ok "assets add and remove: where it came from is required, a path or an id on record is refused (ids never reused), --update keeps the rest, a cost goes into spend.jsonl, a removed record stays (a clip's from before v1 moved in); check fails a changed file and a changed folder"
  else bad "assets add/remove (exits $r1:$r2:$r3:$r4:$r5:$r6:$r7:$rc): $(cat "$t/e1" "$t/e3" "$t/e7" "$t/o2" "$t/o4" | tail -c 600)"; fi
  # the ledger's edges: a class that is no string and an entry that is no object are findings, not tracebacks; a file
  # made from another keeps its licence; a path is found from here or in the project; a URL keeps no secret; a cost that
  # cannot be written is exit 1
  q="$t/q"; cp -R tools/assets/fixtures/project "$q"; printf 'fixture clip\n' > "$q/assets/genclips/gc-0001/clip.mp4"
  cp "$q/assets/music/loop.wav" "$q/assets/music/loop-cut.wav"
  python3 - "$q" <<'PY'
import json, sys
q = sys.argv[1]
f = f"{q}/assets/ledger.json"
d = json.load(open(f, encoding="utf-8"))
d["assets"][0]["license"]["class"] = 5                                  # grey-square: a class that is not a string
d["assets"].append("not a record")
d["assets"].append(dict(d["assets"][4], id="loop-cut", path="assets/music/loop-cut.wav", license={"class": "own", "by": "given"}, derived_from="loop"))
d["assets"][2]["derived_from"] = "nothing-by-this-id"                    # hero: made from a record that is not there
json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False)
PY
  a=$(vh assets check "$q" 2>&1); rc=$?
  b=$(vh assets list "$q" 2>&1; vh assets credits "$q" 2>&1); rc2=$?
  printf 'x' > "$q/assets/img/far.png"
  c=$(cd "$t" && "$VH_BASH" "$ROOT/bin/vh" assets add "$q" assets/img/far.png --class own --source-url 'https://u:p@example.org/page?sig=secret#x' 2>&1); rc3=$?
  d=$(vh assets add "$q" 'https://example.org/files/tone.wav?token=secret' --license CC0 --offline tools/assets/fixtures/responses 2>&1); rc4=$?
  rm -f "$q/assets/spend.jsonl"; mkdir "$q/assets/spend.jsonl"; printf 'y' > "$q/assets/img/paid.png"
  e=$(vh assets add "$q" "$q/assets/img/paid.png" --class managed --origin purchased --cost '$2' 2>&1); rc5=$?
  if [ "$rc:$rc2:$rc3:$rc4:$rc5" = "1:0:0:1:1" ] && ! printf '%s' "$a$b$c$d$e" | grep -q 'Traceback\|secret\|u:p@' \
     && case "$a" in *"grey-square"*"license.class is not one of"*) true ;; *) false ;; esac \
     && case "$a" in *"assets[5] is not a record"*) true ;; *) false ;; esac \
     && case "$a" in *"hero"*"derived_from names nothing-by-this-id"*) true ;; *) false ;; esac \
     && case "$a" in *"loop-cut"*"made from loop (cc-by-nc) but on record as own"*) true ;; *) false ;; esac \
     && grep -q '"url": "https://example.org/page?sig=…#…"' "$q/assets/ledger.json" \
     && case "$e" in *"paid is on record, but its cost could not go into assets/spend.jsonl"*) true ;; *) false ;; esac
  then ok "assets: a class that is no string and an entry that is no object are findings (no traceback); a file made from another keeps its licence; a path is found in the project too; URLs keep no secret; a cost that cannot be written is exit 1"
  else bad "assets edges (exits $rc:$rc2:$rc3:$rc4:$rc5): $(printf '%s | %s | %s | %s | %s' "$a" "$b" "$c" "$d" "$e" | tail -c 900)"; fi
  if a=$(python3 - <<'PY'
import os, sys, tempfile
sys.path.insert(0, "tools/assets")
import fetch
d = tempfile.mkdtemp()
try:
    fetch.Record(d).open("https://example.org/f.wav?X-Amz-Signature=abc")
    print("a signed URL was recorded")
except fetch.FetchError as e:
    print("" if "not recorded" in str(e) and "abc" not in str(e) and not os.listdir(d) else f"Record: {e} {os.listdir(d)}")
except OSError as e:
    print(f"Record went to the network: {e}")
PY
  ) && [ -z "$a" ]; then ok "assets: Record refuses a URL that carries a credential, before it opens anything"
  else bad "assets Record: $a"; fi
  # the budget: the BRIEF's line, else LOCAL.md's 默认预算 (one line each: an empty Budget is not the line below it);
  # amounts with their currency, one a currency, never guessed; spent per currency (spend.jsonl, a clip's cost_usd from
  # before v1); a hold over it, in a currency it lacks, or with no budget is refused, and two at once cannot both pass
  cp -R tools/assets/fixtures/project "$t/b"
  if a=$(OVH_LOCAL_MD="$t/LOCAL.md" python3 - "$t/b" "$t/LOCAL.md" <<'PY'
import subprocess, sys, textwrap, time
sys.path.insert(0, "tools/assets")
import budget, ledger
b, local = sys.argv[1:]
P = budget.parse
bad = []
cases = {"$5": {"USD": 5.0}, "每支片子 20 美元": {"USD": 20.0}, "$5, ¥30": {"USD": 5.0, "CNY": 30.0}, "30 元": {"CNY": 30.0}, "0": {}, "none": {}, "无": {},
         "500 tripo-credits": {"TRIPO-CREDITS": 500.0}, "5 USD (drafts)": {"USD": 5.0}, "€2.5": {"EUR": 2.5}, "$1,000": {"USD": 1000.0}, "$1,000.50, ¥30": {"USD": 1000.5, "CNY": 30.0}}
for v, want in cases.items():
    got = P(v)
    if not got or got["error"] or got["amounts"] != want:
        bad.append(f"parse {v!r}: {got}")
for v in ("default", "{例如每支片子 20 美元}", ""):
    if P(v) is not None:
        bad.append(f"parse {v!r} should say nothing")
for v in ("5", "20 for drafts", "$5 per film, $20 total"):
    if not (P(v) or {}).get("error"):
        bad.append(f"parse {v!r} should be an error")
if not (P("不限") or {}).get("unlimited") or not (P("unlimited") or {}).get("unlimited"):
    bad.append("不限 / unlimited is no cap")
s = budget.spent(b)
if s != {"USD": 0.54}:
    bad.append(f"spent {s}")
for amount, cur, want in ((0.5, "USD", "$0.04 short"), (3, "CNY", "has no CNY")):
    try:
        with budget.hold(b, amount, cur, "image gen"):
            bad.append(f"{amount} {cur} was held")
    except budget.Refused as e:
        if want not in str(e) or not str(e).startswith("image gen: paid call refused"):
            bad.append(f"refusal: {e}")
if budget.check(b, 0.5, "USD")["short"] != 0.04 or not budget.check(b, 0.46, "USD")["ok"]:
    bad.append("check: $0.04 short for 0.50, 0.46 fits")
with budget.hold(b, 0.2, "USD", "a call", asset="img1") as h:   # settled below its estimate, then registered at that cost
    if budget.tally(b)[1] != {"USD": 0.2}:
        bad.append(f"held while in flight: {budget.tally(b)}")
    h.settle(0.1)
try:
    with budget.hold(b, 0.1, "USD", "a call that fails"):
        raise RuntimeError("the vendor is down")
except RuntimeError:
    pass
with budget.hold(b, 0.05, "USD", "a call not billed") as h:
    h.settle(0)
if budget.spent(b) != {"USD": 0.74} or budget.tally(b)[1]:   # 0.54 + 0.1 + 0.1 (an exception: its estimate) + 0
    bad.append(f"after the holds: {budget.tally(b)}")
open(f"{b}/assets/img/img1.png", "wb").write(b"x")
_, _, pay = ledger.add(b, f"{b}/assets/img/img1.png", id="img1", license_class="own", cost={"amount": 0.1, "currency": "USD"})
_, _, pay2 = ledger.add(b, f"{b}/assets/img/img1.png", update=True, cost={"amount": 0.15, "currency": "USD"})
if pay is not None or not pay2 or pay2["amount"] != 0.05 or budget.spent(b) != {"USD": 0.79}:
    bad.append(f"ledger.add's cost: what the log lacks for the id ({pay}, {pay2}, {budget.spent(b)})")
# two processes hold at once: $1 left, each wants 0.6: one is refused
open(f"{b}/BRIEF.md", "w").write("# BRIEF\n\n## Spec\n- Budget: $1.79\n")
racer = textwrap.dedent("""
    import sys, time; sys.path.insert(0, "tools/assets"); import budget
    time.sleep(max(0, float(sys.argv[2]) - time.time()))
    try:
        with budget.hold(sys.argv[1], 0.6, "USD", "racing") as h:
            time.sleep(0.4); h.settle(0.6)
        print("held")
    except budget.Refused:
        print("refused")""")
go = time.time() + 0.5
ps = [subprocess.Popen([sys.executable, "-c", racer, b, str(go)], stdout=subprocess.PIPE, text=True) for _ in range(2)]
got = sorted(p.communicate()[0].strip() for p in ps)
if got != ["held", "refused"] or budget.spent(b) != {"USD": 1.39}:
    bad.append(f"two holds at once: {got}, spent {budget.spent(b)}")
# one line each: an empty Budget or Assets line does not read the next one
open(f"{b}/BRIEF.md", "w").write("# BRIEF\n\n## Spec\n- Budget:\n- Output: 1080p, $5 test\n- Assets:\n- Pace: record\n")
if budget.budget_of(b)["from"] is not None or ledger.policy_of(b) != ("strict", "the default"):
    bad.append(f"an empty line read the next one: {budget.budget_of(b)} {ledger.policy_of(b)}")
open(f"{b}/BRIEF.md", "w").write("# BRIEF\n\n## Spec\n- Budget: default\n")
try:
    with budget.hold(b, 0.1, "USD", "x"):
        bad.append("no budget allowed a call")
except budget.Refused as e:
    if "no budget" not in str(e) or "Budget: $0.10" not in str(e):
        bad.append(f"no-budget refusal: {e}")
open(local, "w").write("- 默认预算：每支片子 20 美元\n")
if not budget.check(b, 0.1, "USD")["ok"] or budget.budget_of(b)["from"] != "LOCAL.md":
    bad.append("LOCAL.md's 默认预算 not read")
budget.spend(b, 18.65, "USD", "a test")
sm = budget.summary(b)
if sm["limit"] != {"USD": 20.0} or sm["left"] != {"USD": -0.04} or sm["over"] != ["USD"] or "over: USD" not in budget.line(b):
    bad.append(f"summary {sm} / {budget.line(b)}")
open(local, "w").write("- 默认预算：不限\n")
if not budget.check(b, 1000, "USD")["ok"] or not budget.summary(b)["unlimited"]:
    bad.append("不限: no cap")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
  ); then ok "assets budget: the BRIEF's Budget, else LOCAL.md's 默认预算, one line each; amounts need a currency, one a currency, \$1,000 is a thousand, 不限 no cap; a hold over it says how much is short, two at once cannot both pass, an exception counts its estimate; ledger.add records only what the log lacks"
  else bad "assets budget: $a"; fi
  # a download from recorded responses (fetch.Replay, no network): whole, resumed from a .part, a server that ignores
  # ranges, a 404, a sha256 that does not match, a rate cap; and add <url> --offline registers what it got
  tone=5fce37f3129150ce7ec3939b54016d9c1fd01364e27b0a788dc634064aec76b1
  if a=$(python3 - "$t/dl" "$tone" <<'PY'
import os, sys, time
sys.path.insert(0, "tools/assets")
import fetch
d, tone = sys.argv[1:]
R, bad = fetch.Replay("tools/assets/fixtures/responses"), []
body = open("tools/assets/fixtures/responses/tone.bin", "rb").read()
r = fetch.download("https://example.org/files/tone.wav", f"{d}/a.wav", sha256=tone, opener=R)
if r["sha256"] != tone or r["resumed"] or open(f"{d}/a.wav", "rb").read() != body or os.path.exists(f"{d}/a.wav.part"):
    bad.append(f"whole: {r}")
open(f"{d}/b.wav.part", "wb").write(body[:1000])
r = fetch.download("https://example.org/files/tone.wav", f"{d}/b.wav", sha256=tone, opener=R)
if not r["resumed"] or r["status"] != 206 or r["sha256"] != tone:
    bad.append(f"resumed: {r}")
open(f"{d}/c.wav.part", "wb").write(b"junk" * 10)
r = fetch.download("https://example.org/files/noranges.wav", f"{d}/c.wav", sha256=tone, opener=R)
if r["resumed"] or r["status"] != 200 or r["sha256"] != tone:
    bad.append(f"no ranges: {r}")
open(f"{d}/e.wav.part", "wb").write(body)
r = fetch.download("https://example.org/files/tone.wav", f"{d}/e.wav", sha256=tone, opener=R)
if r["sha256"] != tone:
    bad.append(f"a complete .part (416): {r}")
for url, want in (("https://example.org/files/missing.wav", "HTTP 404"), ("https://example.org/files/nothing", "no recorded response")):
    try:
        fetch.download(url, f"{d}/x.wav", opener=R); bad.append(f"{url} downloaded")
    except fetch.FetchError as e:
        if want not in str(e):
            bad.append(f"{url}: {e}")
try:
    fetch.download("https://example.org/files/tone.wav", f"{d}/f.wav", sha256="0" * 64, opener=R); bad.append("a wrong sha256 passed")
except fetch.FetchError:
    if os.path.exists(f"{d}/f.wav") or os.path.exists(f"{d}/f.wav.part"):
        bad.append("a wrong sha256 left a file")
t0 = time.monotonic(); fetch.download("https://example.org/files/tone.wav", f"{d}/g.wav", rate="128K", opener=R)
if time.monotonic() - t0 < 0.4:
    bad.append(f"128K/s for 64 kB took {time.monotonic() - t0:.2f} s")
j = fetch.get_json("https://example.org/api/search?q=knock&license=cc0,by", opener=R)
if j["results"][0]["license"] != "by":
    bad.append(f"get_json: {j}")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
  ); then ok "assets download from recorded responses: whole, resumed with Range, over a server that ignores ranges, a complete .part; 404, unrecorded and sha256 mismatch fail with nothing left; a rate cap; get_json"
  else bad "assets download (tools/assets/fetch.py): $a"; fi
  a=$(vh assets add "$p" https://example.org/files/tone.wav --license "CC0" --title Tone --offline tools/assets/fixtures/responses --sha256 "$tone" --to assets/sfx/tone.wav 2>&1); rc=$?
  b=$(vh assets add "$p" https://example.org/files/missing.wav --license CC0 --offline tools/assets/fixtures/responses 2>&1); rc2=$?
  if [ "$rc:$rc2" = "0:1" ] && [ ! -e "$p/assets/missing.wav" ] && python3 - "$p" <<'PY'
import json, sys
r = {x["id"]: x for x in json.load(open(f"{sys.argv[1]}/assets/ledger.json", encoding="utf-8"))["assets"]}["tone"]
s = r["source"]
sys.exit(0 if r["path"] == "assets/sfx/tone.wav" and r["license"]["class"] == "cc0" and s["origin"] == "download"
         and s["file_url"] == "https://example.org/files/tone.wav" and s.get("retrieved") and r["kind"] == "audio" else 1)
PY
  then ok "assets add <url> --offline: downloaded from the recording, then registered (origin download, the URL, the day); a 404 is exit 1 with nothing left"
  else bad "assets add <url> (exit $rc, $rc2): $a | $b"; fi
  # credits: the BY lines with their author, source and deed; public domain as courtesy; the AI notice counts what is generated
  cp -R tools/assets/fixtures/project "$t/c"
  a=$(vh assets credits "$t/c" --lang zh 2>/dev/null); b=$(vh assets credits "$t/c" --json 2>/dev/null); rc=$?
  case "$a" in *"素材署名"*"《Knock》，Fixture Author，example-sounds（https://example.org/sounds/knock），CC BY 4.0（https://creativecommons.org/licenses/by/4.0/）"*"致谢"*"《A grey square》"*"AI 生成内容"*"图片 1 件、视频 1 件"*)
      if [ $rc = 0 ] && python3 -c 'import json,sys; c=json.loads(sys.argv[1]); sys.exit(0 if c["lang"]=="en" and c["aigc"]["count"]==2 and [x["id"] for x in c["required"]]==["knock","loop"] and [x["id"] for x in c["courtesy"]]==["grey-square"] and not c["missing"] else 1)' "$b"
      then ok "assets credits: the lines a licence asks for (title, author, source, licence and their pages), courtesy for public domain, the AI-content notice with what it covers; --json; the BRIEF's language"
      else bad "assets credits --json: $b"; fi ;;
    *) bad "assets credits: $a" ;; esac
  # the commands write their notes into the project's activity log, list and check do not log
  if grep -q '"cmd":"assets"' "$p/.ovh/activity.jsonl" 2>/dev/null && grep -q '"summary":"added new' "$p/.ovh/activity.jsonl" \
     && ! grep -q '"args":\["check"' "$p/.ovh/activity.jsonl"; then ok "assets add and remove are in the activity log with what they did; check and list are not logged"
  else bad "assets in the activity log: $(tail -c 400 "$p/.ovh/activity.jsonl" 2>&1)"; fi
  rm -rf "$t"
}

status_checks() {
  local t p q a b c d e k rc rc2
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  OVH_PROJECTS="$t" vh new math st >/dev/null 2>&1; p=$(ls -d "$t"/*-st)
  cat > "$t/st.py" <<'PY'
import json, subprocess, sys
vh, p, want = sys.argv[1:4]
d = json.loads(subprocess.run([*vh.split("|"), "status", p, "--json"], capture_output=True, text=True).stdout)
got = " ".join(f"{s['id']}:{s['state']}" for s in d["stations"]) + f" | {d['waiting_on']}"
print(got if got == want else f"{got}  (want {want})")
for k in sys.argv[4:]:   # extra checks: a python expression over d
    if not eval(k, {"d": d}):
        print(f"not: {k}")
PY
  st() { python3 "$t/st.py" "$VH_BASH|$ROOT/bin/vh" "$@"; }
  a=$(st "$p" "1:in_progress 2:not_started 3:not_started deliver:not_started | agent" 'd["version"] == 1 and d["project"]["effort"] == "standard" and d["project"]["type"] == "01-math-science-explainer"' \
    'd["review"]["current"] is None and d["renders"] == [] and d["check"] is None and d["open"] == {"review_items": [], "facts_to_verify": []}')
  b=$(vh status "$p"); rc=$?
  [ "$a" = "1:in_progress 2:not_started 3:not_started deliver:not_started | agent" ] && [ $rc = 0 ] && [ "$(printf '%s\n' "$b" | wc -l | tr -d ' ')" -le 8 ] \
    && ok "status: a new standard project works towards gate ①, the rest not started (--json version 1; a short human view)" || bad "status of a new project (rc $rc): $a | $b"
  # a page out (the page channel): waiting for the person; a desk submission: waiting for the agent, until handed over and recorded
  mkdir -p "$p/out/review" && cp tools/desk/fixtures/zh/out/review/gate-1.json "$p/out/review/" && vh gate "$p" 1 --page >/dev/null 2>&1
  a=$(st "$p" "1:waiting_person 2:not_started 3:not_started deliver:not_started | person" 'd["stations"][0]["page"] == "out/review/gate-1.html" and d["review"]["current"] == "1"')
  python3 - "$p" <<'PY'
import sys
sys.path.insert(0, "tools/desk")
import feedback
p = sys.argv[1]
feedback.save(p, feedback.validate(p, {"round": "1", "lang": "zh", "decisions": {"look": "L2"},
                                       "items": [{"target": "range:3-4.5", "status": "change", "text": "这里太快"}, {"target": "card:B", "status": "ok"}]}))
PY
  b=$(st "$p" "1:waiting_agent 2:not_started 3:not_started deliver:not_started | agent" 'd["stations"][0]["feedback"]["pending"] == 1' \
    '[(i["target"], i["label"]) for i in d["open"]["review_items"]] == [("range:3-4.5", "片段 0:03.0–0:04.5")]')
  vh desk feedback "$p" >/dev/null
  c=$(st "$p" "1:waiting_agent 2:not_started 3:not_started deliver:not_started | agent" 'd["stations"][0]["feedback"]["handed"] == 1' 'len(d["open"]["review_items"]) == 1')
  python3 -c 'import sys; f = sys.argv[1] + "/REVIEW.md"; s = open(f, encoding="utf-8").read(); i = s.index("## 审阅台反馈"); open(f, "w", encoding="utf-8").write(s[:i] + s[i:].replace("- 定了：　改了：", "- 定了：L2，开头放慢　改了：0:03–0:04.5", 1))' "$p"   # under the desk's section
  d=$(st "$p" "1:waiting_agent 2:not_started 3:not_started deliver:not_started | agent" '"DECISIONS.md" in d["stations"][0]["note"] and d["stations"][0]["record"]["from"] == "gate1"')
  python3 tools/gatecheck.py "$p" >/dev/null 2>&1; rc=$?   # gate ① as render and check read it: the concept is still missing
  python3 -c 'import sys; f = sys.argv[1] + "/DECISIONS.md"; s = open(f, encoding="utf-8").read(); open(f, "w", encoding="utf-8").write(s.replace("{待定 / 已定（关卡 ①）}", "已定（关卡 ①）：L2", 1))' "$p"
  q=$(st "$p" "1:done 2:in_progress 3:not_started deliver:not_started | agent" 'd["open"]["review_items"] == []')
  python3 tools/gatecheck.py "$p" >/dev/null 2>&1; rc2=$?
  if [ "$a" = "1:waiting_person 2:not_started 3:not_started deliver:not_started | person" ] && [ "$b" = "1:waiting_agent 2:not_started 3:not_started deliver:not_started | agent" ] \
    && [ "$c" = "1:waiting_agent 2:not_started 3:not_started deliver:not_started | agent" ] && [ "$d" = "1:waiting_agent 2:not_started 3:not_started deliver:not_started | agent" ] \
    && [ $rc = 1 ] && [ "$q" = "1:done 2:in_progress 3:not_started deliver:not_started | agent" ] && [ $rc2 = 0 ]
  then ok "status: a page out waits for the person; a submission waits for the agent (pending, then handed over) with its open items; gate ① is done when gatecheck says so (the decision, the words, DECISIONS.md's concept), then gate ② is in progress"
  else bad "status through gate ① (gatecheck $rc/$rc2): $a || $b || $c || $d || $q"; fi
  # a Director stop, a running command, a delivery record
  python3 -c 'import sys; f = sys.argv[1] + "/BRIEF.md"; s = open(f, encoding="utf-8").read(); open(f, "w", encoding="utf-8").write(s.replace("- Director: default", "- Director: hook=own, stop=E3", 1))' "$p"
  printf '{"v":1,"event":"start","run":"9-1","t":%s,"cmd":"render","args":["%s"],"pid":%s}\n' "$(date +%s)" "$p" "$$" >> "$p/.ovh/activity.jsonl"
  a=$(st "$p" "1:done 2:in_progress E3:not_started 3:not_started deliver:not_started | agent" '[r["cmd"] for r in d["activity"]["running"]] == ["render"]')
  b=$(vh status "$p")
  mkdir -p "$p/out" && : > "$p/out/final.mp4" && : > "$p/out/final.upload.mp4"
  printf '{"tool": "bin/vh deliver", "output": "final.upload.mp4", "master": "final.mp4", "time": "2026-10-19T12:00:00"}\n' > "$p/out/final.upload.mp4.deliver.json"
  c=$(st "$p" "1:done 2:in_progress E3:not_started 3:not_started deliver:not_started | agent" 'd["deliveries"][0]["output"] == "out/final.upload.mp4"' \
    'sorted(r["path"] for r in d["renders"]) == ["out/final.mp4", "out/final.upload.mp4"]' '"gate ③ is not decided" in d["stations"][-1]["note"]')
  python3 -c 'import sys; f = sys.argv[1] + "/REVIEW.md"; s = open(f, encoding="utf-8").read(); i = s.index("## 关卡 ③"); open(f, "w", encoding="utf-8").write(s[:i] + s[i:].replace("- 原话：\n", "- 原话：“可以发了”\n", 1).replace("- 定了：　改了：", "- 定了：发布　改了：无", 1))' "$p"
  d=$(st "$p" "1:done 2:not_started E3:not_started 3:done deliver:done | agent" 'd["stations"][-1]["note"] == "bin/vh deliver: out/final.upload.mp4"')
  if [ "$a" = "1:done 2:in_progress E3:not_started 3:not_started deliver:not_started | agent" ] && case "$b" in *"running: render"*) true ;; *) false ;; esac \
    && [ "$c" = "1:done 2:in_progress E3:not_started 3:not_started deliver:not_started | agent" ] && [ "$d" = "1:done 2:not_started E3:not_started 3:done deliver:done | agent" ]
  then ok "status: the Director's stop=E3 adds its checkpoint; a running command shows; bin/vh deliver's record is a delivery once gate ③ is done (before, its note says so)"
  else bad "status with a checkpoint, a run, a delivery: $a | $b | $c | $d"; fi
  # quick skips the gates; a waiver skips what it names; a pause waits for the person; a final film checked and passing
  OVH_PROJECTS="$t" vh new math qk --effort quick >/dev/null 2>&1; q=$(ls -d "$t"/*-qk)
  a=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:in_progress | agent")
  mkdir -p "$q/out/check" && : > "$q/out/final.mp4"
  printf '{"version": 1, "video": "out/final.mp4", "t": %s, "verdict": "pass", "exit": 0, "counts": {"fail": 0, "warn": 1, "info": 0}, "findings": []}\n' "$(($(date +%s) + 5))" > "$q/out/check/final.check.json"
  b=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:done | nobody" 'd["check"]["verdict"] == "pass" and d["check"]["record"] == "out/check/final.check.json"')
  OVH_PROJECTS="$t" vh new math wv >/dev/null 2>&1; q=$(ls -d "$t"/*-wv)
  python3 -c 'import sys; f = sys.argv[1] + "/REVIEW.md"; s = open(f, encoding="utf-8").read(); open(f, "w", encoding="utf-8").write(s.replace("## 关卡 ① 立意和大纲\n", "## 关卡 ① 立意和大纲\n- 用户授权跳过（2026-10-19）。原话：“直接做完给我看”\n- 范围：跳过关卡 ②③\n", 1))' "$q"
  c=$(st "$q" "1:in_progress 2:skipped 3:skipped deliver:not_started | agent")
  printf '\n## 暂停 · 2026-10-19\n- 原话："先停一下"\n' >> "$q/REVIEW.md"
  d=$(st "$q" "1:in_progress 2:skipped 3:skipped deliver:not_started | person" 'd["paused"] is True')
  if [ "$a" = "1:skipped 2:skipped 3:skipped deliver:in_progress | agent" ] && [ "$b" = "1:skipped 2:skipped 3:skipped deliver:done | nobody" ] \
    && [ "$c" = "1:in_progress 2:skipped 3:skipped deliver:not_started | agent" ] && [ "$d" = "1:in_progress 2:skipped 3:skipped deliver:not_started | person" ]
  then ok "status: quick skips the gates; a final film with a passing check record is delivered; a waiver skips the gates it names; a pause waits for the person"
  else bad "status: quick, waiver, pause: $a | $b | $c | $d"; fi
  # a check record keeps the film's size and mtime_ns, and a film that differs from them in either is not the one checked:
  # a film put back with an old modification time (cp -p, rsync -a, bin/vh versions use) is older than the record all the
  # same, which the time alone calls current. A record without the two (made before) goes by the film's time, as it did
  cat > "$t/ck.py" <<'PY'
import json, os, sys, time
q, what, a, b = sys.argv[1:5]
film, rec = q + "/out/final.mp4", q + "/out/check/final.check.json"
if what == "film":   # film <bytes> <modified: seconds from now | rec: the recorded mtime_ns>
    open(film, "wb").write(a.encode())
    ns = json.load(open(rec))["mtime_ns"] if b == "rec" else int((time.time() + float(b)) * 1e9)
    os.utime(film, ns=(ns, ns))
else:                # record <fields | none> <made: seconds from now>
    r = {"version": 1, "video": "out/final.mp4", "t": time.time() + float(b), "verdict": "pass", "exit": 0, "counts": {"fail": 0, "warn": 0, "info": 0}, "findings": []}
    if a == "fields":
        s = os.stat(film); r.update(size=s.st_size, mtime_ns=s.st_mtime_ns)
    json.dump(r, open(rec, "w"))
PY
  OVH_PROJECTS="$t" vh new math ck --effort quick >/dev/null 2>&1; q=$(ls -d "$t"/*-ck); mkdir -p "$q/out/check"
  python3 "$t/ck.py" "$q" film 'film one' -100 && python3 "$t/ck.py" "$q" record fields 5
  a=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:done | nobody" 'd["check"]["stale"] is False')
  python3 "$t/ck.py" "$q" film 'film two!!' -200   # another film, older than the record, as a restore that keeps times puts it
  b=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:in_progress | agent" 'd["check"]["stale"] is True' 'd["renders"][0]["check"]["stale"] is True')
  python3 "$t/ck.py" "$q" film 'film one' -300     # the same size, another modification time
  c=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:in_progress | agent" 'd["check"]["stale"] is True')
  python3 "$t/ck.py" "$q" film 'film one, longer' rec   # the recorded modification time, another size
  d=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:in_progress | agent" 'd["check"]["stale"] is True')
  python3 "$t/ck.py" "$q" film 'film one' -100 && python3 "$t/ck.py" "$q" record none 5   # a record of the old kind: by time
  e=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:done | nobody" 'd["check"]["stale"] is False')
  python3 "$t/ck.py" "$q" record none -1000
  k=$(st "$q" "1:skipped 2:skipped 3:skipped deliver:in_progress | agent" 'd["check"]["stale"] is True')
  if [ "$a" = "1:skipped 2:skipped 3:skipped deliver:done | nobody" ] && [ "$b" = "1:skipped 2:skipped 3:skipped deliver:in_progress | agent" ] \
    && [ "$c" = "$b" ] && [ "$d" = "$b" ] && [ "$e" = "$a" ] && [ "$k" = "$b" ]
  then ok "status: a check record is stale when the film's size or mtime_ns is not the one it kept, though the film is older than the record (and then the delivery is not done); a record without them goes by time"
  else bad "status: a check record and a film put back with an old time: $a | $b | $c | $d | $e | $k"; fi
  # gate ②: read from the section that names its page (the template's), whatever the dates; a section without the 页面
  # line is read by date, and the note says so (older than the page: not counted)
  OVH_PROJECTS="$t" vh new math s2 >/dev/null 2>&1; q=$(ls -d "$t"/*-s2)
  python3 - "$q" <<'PY'
import os, sys, time
p = sys.argv[1]
f = p + "/REVIEW.md"; s = open(f, encoding="utf-8").read()
s = s.replace('- 原话："……"', '- 原话："选 B"', 1).replace("- 定了：{…}　改了：{…}", "- 定了：B　改了：无", 1)
i = s.index("## 关卡 ② 分镜")
open(f, "w", encoding="utf-8").write(s[:i] + s[i:].replace("- 原话：\n", '- 原话："分镜可以"\n', 1).replace("- 定了：　改了：", "- 定了：通过　改了：无", 1))
d = p + "/DECISIONS.md"; s = open(d, encoding="utf-8").read(); open(d, "w", encoding="utf-8").write(s.replace("{待定 / 已定（关卡 ①）}", "已定（关卡 ①）：B", 1))
os.makedirs(p + "/out/review", exist_ok=True)
for n in ("gate-2.json", "gate-2.html"): open(p + "/out/review/" + n, "w").write("{}")
os.utime(f, (time.time() - 100,) * 2)   # REVIEW.md older than the page
PY
  a=$(st "$q" "1:done 2:done 3:in_progress deliver:not_started | agent" 'd["stations"][1]["record"]["from"] == "page" and d["stations"][1]["note"] is None')
  python3 -c 'import os, sys, time; f = sys.argv[1] + "/REVIEW.md"; s = open(f, encoding="utf-8").read(); open(f, "w", encoding="utf-8").write(s.replace("- 页面：`out/review/gate-2.html`（{日期}）\n", "", 1)); os.utime(f, (time.time() - 100,) * 2)' "$q"
  b=$(st "$q" "1:done 2:waiting_person 3:not_started deliver:not_started | person" 'd["stations"][1]["record"]["from"] == "stop_older" and "not counted" in d["stations"][1]["note"]')
  python3 -c 'import os, sys, time; os.utime(sys.argv[1] + "/REVIEW.md", (time.time() + 100,) * 2)' "$q"
  c=$(st "$q" "1:done 2:done 3:in_progress deliver:not_started | agent" 'd["stations"][1]["record"]["from"] == "stop_by_date" and "by date" in d["stations"][1]["note"]')
  if [ "$a" = "1:done 2:done 3:in_progress deliver:not_started | agent" ] && [ "$b" = "1:done 2:waiting_person 3:not_started deliver:not_started | person" ] \
    && [ "$c" = "1:done 2:done 3:in_progress deliver:not_started | agent" ]
  then ok "status: gate ② read from the template's section, which names its page, whatever the dates; without that line, by date, and the note says so"
  else bad "status of gate ② by page and by date: $a | $b | $c"; fi
  # no REVIEW.md (a project from before the templates had one): no record, not "in progress"; machine-written records of
  # the wrong shape (a check record, a render's and a delivery's sidecar, a submission, activity lines) break nothing
  OVH_PROJECTS="$t" vh new math nr >/dev/null 2>&1; q=$(ls -d "$t"/*-nr); rm "$q/REVIEW.md"
  a=$(st "$q" "1:no_record 2:no_record 3:no_record deliver:no_record | unknown")
  mkdir -p "$q/out/check" "$q/out/review/feedback" "$q/.ovh" && : > "$q/out/x.mp4"
  printf '%s\n' '{"version": 1, "video": 5, "t": "x", "findings": "x", "counts": [1], "verdict": 3}' > "$q/out/check/bad.check.json"
  printf '%s\n' '{"version": 1, "video": "out/x.mp4", "t": 1, "findings": [1, {"severity": "fail", "message": 2}], "counts": {"fail": "x"}, "exit": true}' > "$q/out/check/x.check.json"
  printf '%s\n' '{"pixels": 5, "patches": 5, "frames": "x", "span": "y"}' > "$q/out/x.mp4.render.json"
  printf '%s\n' '{"output": 5, "master": [1]}' > "$q/out/x.mp4.deliver.json"
  printf '%s\n' '{"round": 5, "items": 5, "lang": 3}' > "$q/out/review/feedback/1-20261019-120000.json"
  printf '%s\n' '{"round": "1", "items": [{"target": 5}, {"target": "range:1-2", "status": "change", "text": 7, "label": 8, "t": "a", "t1": 2}]}' > "$q/out/review/feedback/1-20261019-120001.json"
  printf '%s\n' '{"v":1,"event":"note","run":"1-1","t":1,"outputs":5,"summary":5}' '{"v":1,"event":"end","run":"1-1","t":2,"duration":"x","exit":"y","cmd":4}' \
    '{"v":1,"event":"start","run":"2-2","t":3,"args":5,"cwd":5,"pid":"z"}' '{"v":true,"event":"x","t":1}' '{"v":1,"event":"progress","run":"2-2","t":true,"done":"x"}' \
    '{"v":1,"event":"feedback","t":4,"items":[1],"round":2}' > "$q/.ovh/activity.jsonl"
  b=""
  for c in status activity; do for d in "" --json; do
    e=$(vh "$c" "$q" ${d:+"$d"} 2>&1) || b="$b $c $d: exit $?"
    case "$e" in *Traceback*) b="$b $c $d: a traceback" ;; esac
  done; done
  [ "$a" = "1:no_record 2:no_record 3:no_record deliver:no_record | unknown" ] && [ -z "$b" ] \
    && ok "status: no REVIEW.md is no record (waiting on: unknown); records of the wrong shape break neither status nor activity" \
    || bad "status without REVIEW.md, or with bad records: $a |$b"
  vh status "$t/no-such" >/dev/null 2>&1; rc=$?; [ $rc = 2 ] && ok "status: no project exits 2" || bad "status of nothing exited $rc"
  python3 -c 'import sys; sys.path.insert(0, "tools"); import status as S; d = S.director_stops
sys.exit(0 if d("hook=own, stop=E1, stop=E3") == d("stop=E1,E3") == d("stop = e1，E3") == {"E1", "E3"} and not d("stop=E12") and not d("nostop=E3") else 1)' \
    && ok "status: every stop= on the Director line counts (stop=E1, stop=E3), E12 and nostop= do not" || bad "status: the Director line's stop= items"
  rm -rf "$t"
}

# the activity log (<project>/.ovh/activity.jsonl, tools/activity.py): a command on a project adds a start, its tool's note
# and an end with the exit status; commands without a project, and the read-only views, add nothing; keys and the
# environment never reach it; 16 commands at once leave 32 whole lines; TERM ends a command at once (no end line), a tool
# that handles it logs 128 + n, a Ctrl-C logs 130 and ends bin/vh by SIGINT; a project that cannot be written to changes
# nothing in what the command does or says; bin/vh activity reads it back (and --follow as it grows). The page tools' lines
# (render's progress, patch) are checked in film_checks
activity_checks() {
  local t p a b c rc rc2 i pid want la
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); p="$t/p q"   # a space in the path
  cp -R tools/desk/fixtures/zh "$p"
  vh review "$p" 1 >/dev/null 2>&1; rc=$?
  vh review "$p" 9 >/dev/null 2>&1; rc2=$?
  (cd "$p" && vh effort quick >/dev/null && vh desk data . >/dev/null && vh activity . >/dev/null)
  OVH_CI_SECRET=topsecret-env vh timeline "$p" --token abc123 API_KEY=sk-123456 --api-key=xyz AIzaFAKEFAKE "$(printf 'a%.0s' $(seq 40))" >/dev/null 2>&1
  vh timeline "$p" "https://user:hunter2pw@example.com/x?sig=s3cr3tsig&v=1#frag=fragval1" -k shortflagval "Authorization: Bearer bearertok1" \
    --auth=authval1 MY_VAR=envval1 cred=credval1 Ab3dEf6.hIj9kLm2n-opQ 0123456789abcdef0123 --out=keynote.wav keepme.wav >/dev/null 2>&1
  a=$(python3 - "$p/.ovh/activity.jsonl" <<'PY'
import json, sys
recs = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
text = open(sys.argv[1], encoding="utf-8").read()
runs = {}
for r in recs:
    runs.setdefault(r.get("run"), []).append(r)
seq = [[r["event"] for r in rs] for rs in runs.values()]
want = [["start", "note", "end"], ["start", "end"], ["start", "end"], ["start", "end"]]
review = list(runs.values())[0]
bad = []
if seq != want: bad.append(f"events {seq}")
if review[0]["cmd"] != "review" or review[0]["args"][-1] != "1" or review[2]["exit"] != 0 or not review[1]["outputs"] == ["out/review/gate-1.html"]: bad.append(f"review run {review}")
if list(runs.values())[1][-1]["exit"] != 2: bad.append("review 9 should end with exit 2")
for s in ("abc123", "sk-123456", "xyz", "AIzaFAKE", "a" * 40, "topsecret", "OVH_CI_SECRET", "hunter2pw", "s3cr3tsig", "fragval1", "shortflagval",
          "bearertok1", "authval1", "envval1", "credval1", "Ab3dEf6", "0123456789abcdef0123"):
    if s in text: bad.append(f"{s} is in the log")
shown = list(runs.values())[3][0]["args"][1:]
if shown != ["https://…@example.com/x?sig=…&v=…#…", "-k", "…", "Authorization: …", "--auth=…", "MY_VAR=…", "cred=…", "…", "…", "--out=keynote.wav", "keepme.wav"]:
    bad.append(f"shown as {shown}")
print("; ".join(bad)); sys.exit(1 if bad else 0)
PY
  )
  if [ $rc = 0 ] && [ $rc2 = 2 ] && [ -z "$a" ]; then ok "activity: a command on a project logs its start, its tool's note and its end with the exit status; effort, desk data and activity log nothing; keys, passwords, URL secrets, tokens and the environment never reach the log, option names and file names stay"
  else bad "activity: review exit $rc/$rc2: $a"; fi
  # 16 at once: every line whole (one write each), also when the arguments would fill 2 KiB (3 bytes a character)
  rm -f "$p/.ovh/activity.jsonl"
  for i in $(seq 16); do vh timeline "$p" >/dev/null 2>&1 & done; wait
  a=$(python3 -c 'import json, sys; ls = open(sys.argv[1], encoding="utf-8").read().splitlines(); [json.loads(l) for l in ls]; print(len(ls))' "$p/.ovh/activity.jsonl" 2>&1)
  rm -f "$p/.ovh/activity.jsonl"; la=(); for i in $(seq 30); do la+=("$(printf '片%.0s' $(seq 100))"); done
  for i in $(seq 16); do vh timeline "$p" "${la[@]}" >/dev/null 2>&1 & done; wait
  c=$(python3 -c 'import json, sys; ls = open(sys.argv[1], "rb").read().splitlines(); r = [json.loads(l) for l in ls]; print(len(ls), max(map(len, ls)) < 1024, r[0]["args"][-1])' "$p/.ovh/activity.jsonl" 2>&1)
  [ "$a" = 32 ] && [ "$c" = "32 True …" ] && ok "activity: 16 commands at once leave 32 whole lines, also with long arguments (cut to stay under 1 KiB)" || bad "activity: 16 concurrent commands left: $a / $c"
  # arguments that are not UTF-8 (a Latin-1 name, a surrogate's bytes, a cut character), and a tool's output path that is
  # not either, are written as \xNN: every line is UTF-8 JSON, a Chinese argument stays as it is; a line an older bin/vh
  # wrote with the raw byte still reads, with the byte as \xNN
  rm -f "$p/.ovh/activity.jsonl"
  vh timeline "$p" $'caf\xe9.wav' "片子" $'\xed\xa0\x80' $'a\xe7\x89' >/dev/null 2>&1
  OVH_ACTIVITY_LOG="$p/.ovh/activity.jsonl" OVH_ACTIVITY_RUN=ci-1 OVH_ACTIVITY_CMD=qa python3 -c 'import os, sys; sys.path.insert(0, "tools"); import activity
activity.note("made", [os.fsdecode(os.fsencode(sys.argv[1]) + b"/out/x\xff.wav")])' "$p"
  printf '{"v":1,"event":"note","run":"old-1","t":1,"cmd":"qa","summary":"raw \351 byte"}\n' >> "$p/.ovh/activity.jsonl"
  a=$(python3 - "$p/.ovh/activity.jsonl" <<'PY' 2>&1
import json, sys
ls = open(sys.argv[1], "rb").read().splitlines(); bad = []
for n, l in enumerate(ls[:-1], 1):   # the last: the older bin/vh's own line
    try: json.loads(l.decode("utf-8"))
    except ValueError as e: bad.append(f"line {n} is not UTF-8 JSON: {e}")
r = [json.loads(l.decode("utf-8")) for l in ls[:3]] if not bad else []
if r and (r[0]["args"][1:] != ["caf\\xe9.wav", "片子", "\\xed\\xa0\\x80", "a\\xe7\\x89"] or r[2]["outputs"] != ["out/x\\xff.wav"]): bad.append(f"written as {r[0]['args'][1:]} {r[2]['outputs']}")
print("; ".join(bad))
PY
  )
  b=$(vh activity "$p" 2>&1); rb=$?
  case "$a|$rb:$b" in "|0:"*'caf\xe9.wav 片子 \xed\xa0\x80 a\xe7\x89'*'out/x\xff.wav'*'raw \xe9 byte'*)
      ok "activity: arguments and paths that are not UTF-8 are written as \\xNN (every line UTF-8 JSON); an older raw line still reads" ;;
    *) bad "activity with bytes that are not UTF-8: $a | exit $rb: $(printf '%s' "$b" | tail -c 400)" ;; esac
  # signals: a tool bin/vh exec'd into writes its own end, 128 + the signal (desk wait, the desk itself); a command bash
  # waits on (a stand-in uv that never ends): TERM ends bin/vh at once, with no end line (the run reads as gone), and a
  # Ctrl-C (SIGINT to the process group) writes the end with 130 and then ends bin/vh by SIGINT (the caller sees -2). The
  # stand-in traps INT: a loop of sleeps without it can miss a Ctrl-C that lands as a sleep ends (sh takes the sleep's
  # normal exit for a child that handled it), and then it never ends, and bin/vh waits on it
  rm -f "$p/.ovh/activity.jsonl"; mkdir -p "$t/stub"
  printf '#!/bin/sh\ntrap "exit 130" INT\n: > "$UVMARK"\nwhile :; do sleep 0.05; done\n' > "$t/stub/uv"; chmod +x "$t/stub/uv"
  : > "$p/audio/mix.wav"
  a=$(python3 - "$VH_BASH" "$ROOT" "$p" "$t" <<'PY'
import json, os, signal, subprocess, sys, time
sh, root, p, t = sys.argv[1:]
env, mark = dict(os.environ, PATH=f"{t}/stub:{os.environ['PATH']}", UVMARK=f"{t}/started"), f"{t}/started"
def start(*args, until):
    if os.path.exists(mark): os.remove(mark)
    pr = subprocess.Popen([sh, f"{root}/bin/vh", *args], start_new_session=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(300):
        if os.path.exists(until) or pr.poll() is not None: break
        time.sleep(0.05)
    return pr
def stub():
    return subprocess.run(["pgrep", "-f", f"{t}/stub/uv"], capture_output=True).returncode == 0
out = []
pr = start("desk", "wait", p, "--timeout", "30", until=f"{p}/out/review/feedback/.listening")
pr.send_signal(signal.SIGTERM); out.append(f"wait {pr.wait(10)}")   # at once: its handlers are in place before the flag
pr = start("desk", p, "--port", "0", until=f"{p}/out/review/.desk.json")
time.sleep(0.5); pr.send_signal(signal.SIGTERM); out.append(f"desk {pr.wait(10)}")
pr = start("qa", f"{p}/audio/mix.wav", until=mark)
t0 = time.time(); pr.send_signal(signal.SIGTERM)   # to bin/vh alone, as kill <pid> does: it must not wait for the stand-in
try: rc = pr.wait(5)
except subprocess.TimeoutExpired: rc = "waited"
out.append(f"qa {rc} " + ("at once" if time.time() - t0 < 2 and stub() else "late"))
subprocess.run(["pkill", "-f", f"{t}/stub/uv"])
pr = start("qa", f"{p}/audio/mix.wav", until=mark)
os.killpg(pr.pid, signal.SIGINT); out.append(f"qa {pr.wait(10)}")
subprocess.run(["pkill", "-f", f"{t}/stub/uv"])
recs = [json.loads(x) for x in open(f"{p}/.ovh/activity.jsonl", encoding="utf-8")]
out.append(" ".join(f"{r['cmd']}:{r['exit']}" for r in recs if r["event"] == "end"))
j = json.loads(subprocess.run([sys.executable, f"{root}/tools/activity.py", p, "--json"], capture_output=True, text=True).stdout)
out.append(" ".join(f"{r['cmd']}:{r['state']}" for r in j["runs"]))
print(" · ".join(out))
PY
)
  want="wait 143 · desk 143 · qa -15 at once · qa -2 · desk:143 desk:143 qa:130 · desk:failed desk:failed qa:gone qa:failed"
  [ "$a" = "$want" ] && ok "activity: TERM ends a command at once (no end line: gone), a tool that handles it logs 128 + n; Ctrl-C logs 130 and ends bin/vh by SIGINT" \
    || bad "activity on signals: '$a' (want '$want')"
  # a closed pipe (bin/vh check … | head): check's scratch folder still goes, nothing stale lands in the log, and the EXIT
  # trap says nothing of its own (bash 5 runs it on SIGPIPE; bash 3.2 wrote the failed output into the next redirect, and
  # into $(date))
  if command -v ffmpeg >/dev/null; then
    mkdir -p "$t/pipetmp" "$p/out"; rm -f "$p/.ovh/activity.jsonl"
    ffmpeg -nostdin -v error -f lavfi -i testsrc=s=160x90:r=10:d=1 -pix_fmt yuv420p "$p/out/pipe.mp4"
    TMPDIR="$t/pipetmp" "$VH_BASH" "$ROOT/bin/vh" check "$p/out/pipe.mp4" 2>"$t/pipe.err" | head -1 >/dev/null
    a=$(python3 -c 'import json, sys; [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]; print("ok")' "$p/.ovh/activity.jsonl" 2>&1)
    if [ "$a" = ok ] && [ -z "$(ls -A "$t/pipetmp")" ] && ! grep -q "arithmetic\|syntax error\|Traceback" "$t/pipe.err"
    then ok "activity: under a closed pipe (check | head) the scratch folder goes, the log stays whole JSON, the trap says nothing"
    else bad "check | head: log $a, left in TMPDIR: $(ls -A "$t/pipetmp"), stderr: $(tail -c 300 "$t/pipe.err")"; fi
    rm -f "$p/out/pipe.mp4" "$p/out/check/pipe.check.json"
  else skip "check under a closed pipe" "needs ffmpeg"; fi
  # a project that cannot be written to: the same exit and the same words
  a=$(vh timeline "$p" 2>&1); rc=$?
  rm -rf "$p/.ovh"; chmod 555 "$p"
  b=$(vh timeline "$p" 2>&1); rc2=$?
  chmod 755 "$p"
  [ $rc = $rc2 ] && [ "$a" = "$b" ] && ok "activity: a project that cannot be written to changes nothing in what the command does or says" || bad "activity on a read-only project: exit $rc/$rc2, '$a' / '$b'"
  # the reader: the human lines, --json, and --follow as the log grows; bin/vh new logs into the project it made
  vh review "$p" 1 >/dev/null 2>&1; vh review "$p" 9 >/dev/null 2>&1
  a=$(vh activity "$p"); b=$(vh activity "$p" --json)
  "$VH_BASH" "$ROOT/bin/vh" activity "$p" --follow --json > "$t/follow.out" 2>&1 & pid=$!
  sleep 1; vh review "$p" 1 >/dev/null 2>&1; sleep 1.2; kill $pid 2>/dev/null; wait $pid 2>/dev/null
  if case "$a" in *"review . 1"*"✓"*"gate-1.html"*"review . 9"*"✗ exit 2"*) true ;; *) false ;; esac && python3 - "$b" "$t/follow.out" <<'PY'
import json, sys
d = json.loads(sys.argv[1]); f = [json.loads(l) for l in open(sys.argv[2], encoding="utf-8") if l.strip()]
st = [r["state"] for r in d["runs"]]
sys.exit(0 if d["version"] == 1 and st[-2:] == ["ok", "failed"] and d["runs"][-2]["outputs"] == ["out/review/gate-1.html"]
         and [r["event"] for r in f][-3:] == ["start", "note", "end"] else 1)
PY
  then ok "activity: bin/vh activity lists the runs (paths relative to the project), --json gives each run's state and outputs, --follow prints the lines as they come"
  else bad "bin/vh activity: $(printf '%s' "$a" | tail -c 400) | $(tail -c 300 "$t/follow.out")"; fi
  OVH_PROJECTS="$t/new" vh new math ci-act >/dev/null 2>&1
  a=$(cat "$t"/new/*-ci-act/.ovh/activity.jsonl 2>&1)
  case "$a" in *'"event":"start"'*'"cmd":"new"'*'"event":"end"'*'"exit":0'*'"summary":"created '*'-ci-act · math · standard"'*) ok "activity: bin/vh new logs itself into the project it made" ;;
    *) bad "activity of bin/vh new: $a" ;; esac
  rm -rf "$t"
}

# bin/vh textcheck on its fixture (tools/textcheck/fixture/index.html: one read per case), with whatever headless Chrome
# the machine has (GitHub's runners come with Chrome); skipped without one
textcheck_checks() {
  local t a rc
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  a=$(vh textcheck tools/textcheck/fixture --out "$t/out" 2>&1); rc=$?
  case "$rc:$a" in 2:*"needs a headless Chrome"*) skip "textcheck" "no Chrome, Chromium or chrome-headless-shell"; rm -rf "$t"; return ;; esac
  if [ $rc = 1 ] && python3 - "$t/out/textcheck.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
got = {r["text"]: (r["status"], sorted(f for f in ((r.get("worst") or {}).get("flags") or []) if f != "unstable")) for r in d["reads"]}
want = {"CLEAR": ("ok", []), "COVERED": ("fail", ["covered"]), "FAINT": ("fail", ["contrast"]), "OUTLINED": ("ok", []), "KINETIC": ("ok", []),
        "TWO · PARTS": ("ok", []), "GONE": ("fail", ["outside"]), "HIDDEN": ("fail", ["caption"]), "LATE": ("ok", []), "NOWHERE": ("not drawn", [])}
bad = [f"{k}: got {got.get(k)}, want {v}" for k, v in want.items() if got.get(k) != v]
late = [r for r in d["reads"] if r["text"] == "LATE"]
if not late or late[0].get("missingAt") != [0.4]: bad.append(f"LATE: missing at {late[0].get('missingAt') if late else None}, want [0.4]")
flagged = [e["text"] for e in d["extra"] if e["flagged"]]
if flagged != ["ghost"]: bad.append(f"outside the registry: flagged {flagged}, want ['ghost']")
bright = [c["text"] for c in d["captions"] if c["worst"]["close"] > 0.12]
if bright != ["a caption over a bright band"]: bad.append(f"captions over a bright picture: {bright}")
print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
  then ok "textcheck: covered, faint, out-of-frame and captioned-over reads fail (exit 1); outlined, kinetic and split reads pass; a late read, a faint line outside the registry and a caption over a bright band warn"
  else bad "textcheck on its fixture (exit $rc): $(printf '%s' "$a" | tail -c 1200)"; fi
  # without the contract: nothing can be drawn on demand, so exit 2 and say what to add
  sed 's/window.__vh = { draw, texts: TEXTS };//' tools/textcheck/fixture/index.html > "$t/index.html"
  a=$(vh textcheck "$t" --out "$t/out2" 2>&1); rc=$?
  case "$rc:$a" in 2:*"window.film = { frame"*) ok "textcheck without the page contract exits 2 and names the line to add" ;;
    *) bad "textcheck without the contract: exit $rc: $(printf '%s' "$a" | tail -c 800)" ;; esac
  # the same fixture written with the page contract (window.film) instead of window.__vh: the same verdicts
  sed 's/window.__vh = { draw, texts: TEXTS };/window.film = { frame: draw, duration: 4, texts: TEXTS };/' tools/textcheck/fixture/index.html > "$t/index.html"
  a=$(vh textcheck "$t" --out "$t/out3" 2>&1); rc=$?
  if [ $rc = 1 ] && python3 -c "import json, sys; d = json.load(open(sys.argv[1], encoding='utf-8')); s = {r['text']: r['status'] for r in d['reads']}; sys.exit(0 if (s.get('CLEAR'), s.get('COVERED'), s.get('NOWHERE')) == ('ok', 'fail', 'not drawn') else 1)" "$t/out3/textcheck.json"
  then ok "textcheck reads window.film as it reads window.__vh"; else bad "textcheck with window.film (exit $rc): $(printf '%s' "$a" | tail -c 800)"; fi
  # the interface over the scene (window.film.ui and frame(t, { layer: "scene" })): a dashed line across the bar and a
  # busy picture under the caption are said, each once, the shaded and grainy paper is not; a warning, exit 0. A page whose
  # scene layer draws the interface too is said so, not checked
  a=$(vh textcheck tools/textcheck/fixture/ui.html --out "$t/out4" 2>&1); rc=$?
  if [ $rc = 0 ] && python3 -c "import json, sys; d = json.load(open(sys.argv[1])); g = [(s['name'], s['from'], s['to'], s['busy']) for s in d['ui']['spans']]; sys.exit(0 if g == [('chapter bar', 2.5, 3.5, False), ('caption', 4.5, 5.5, True)] else 1)" "$t/out4/textcheck.json"
  then ok "textcheck: a line crossing the chapter bar and a busy picture under the caption are said (scene drawn alone, shading and grain left out), exit 0"
  else bad "textcheck on the interface fixture (exit $rc): $(printf '%s' "$a" | tail -c 800)"; fi
  mkdir -p "$t/ig" && sed 's/if (!(o \&\& o.layer === "scene")) ui(t);/ui(t);/' tools/textcheck/fixture/ui.html > "$t/ig/index.html"
  a=$(vh textcheck "$t/ig" --out "$t/out5" 2>&1); rc=$?
  case "$rc:$a" in 0:*'frame(t, { layer: "scene" }) drew the chapter bar too'*) ok "textcheck: a page whose scene layer draws its interface too is said so, and that pass skipped" ;;
    *) bad "textcheck on a page that ignores the scene layer (exit $rc): $(printf '%s' "$a" | tail -c 600)" ;; esac
  rm -rf "$t"
}

# bin/vh frames (tools/film): frames drawn through the page contract (engines/CONTRACT.md) on its fixtures, with
# whatever headless Chrome the machine has; the HyperFrames adapter only where its runtime is installed
film_checks() {
  local t a rc
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  a=$(vh frames tools/film/fixture --at 0.5,2.5 --out "$t/a" 2>&1); rc=$?
  case "$rc:$a" in 2:*"needs a headless Chrome"*) skip "frames" "no Chrome, Chromium or chrome-headless-shell"; rm -rf "$t"; return ;; esac
  vh frames tools/film/fixture --at 2.5 --out "$t/b" >/dev/null 2>&1
  if [ $rc = 0 ] && cmp -s "$t/a/index-t0002.500.png" "$t/b/index-t0002.500.png" && printf '%s' "$a" | grep -q "read Math.random" \
     && python3 -c "import struct, sys; d = open(sys.argv[1], 'rb').read(); sys.exit(0 if struct.unpack('>II', d[16:24]) == (320, 180) else 1)" "$t/b/index-t0002.500.png"
  then ok "frames: a page's frame at t is the same after another frame or alone (the clock holds Math.random at t, and says so), at its meta viewport size; ready is called as a method"
  else bad "frames on its fixture (exit $rc): $(printf '%s' "$a" | tail -c 800)"; fi
  a=$(vh frames tools/film/fixture/throws.html --at 1,2.5 --out "$t/c" 2>&1); rc=$?
  case "$rc:$a" in 1:*"t=2.5 s"*"no picture after 2 s"*) ok "frames: a frame that throws exits 1 and names its t" ;; *) bad "frames on a throwing page: exit $rc: $(printf '%s' "$a" | tail -c 600)" ;; esac
  a=$(vh frames tools/film/fixture/late.html --at 1,2.5 --out "$t/c2" 2>&1); rc=$?
  case "$rc:$a" in 1:*"a late error"*) ok "frames: an error a frame leaves behind (a timer) still fails the run" ;; *) bad "frames on a late error: exit $rc: $(printf '%s' "$a" | tail -c 600)" ;; esac
  a=$(vh frames tools/film/fixture/loaderr.html --at 1 --out "$t/c3" 2>&1); rc=$?
  case "$rc:$a" in 1:*"while loading: failed to load missing.png"*) ok "frames: a request that fails while loading fails the run" ;; *) bad "frames on a failed load: exit $rc: $(printf '%s' "$a" | tail -c 600)" ;; esac
  a=$(vh frames tools/film/fixture/nofilm.html --at 1 --out "$t/d" 2>&1); rc=$?
  case "$rc:$a" in 2:*"no window.film"*) ok "frames: a page without window.film exits 2" ;; *) bad "frames on a page without the contract: exit $rc: $(printf '%s' "$a" | tail -c 600)" ;; esac
  # a frame that never comes back (from 1 s on its promise never settles) stops the run at --frame-timeout, naming its t,
  # with the frames before it written: not at the whole run's --timeout (600 s)
  mkdir -p "$t/hang" && sed 's|if (t >= 2) throw new Error("no picture after 2 s");|if (t >= 1) return new Promise(() => {});|' tools/film/fixture/throws.html > "$t/hang/index.html"
  s0=$SECONDS; a=$(vh frames "$t/hang" --at 0.5,1.5 --frame-timeout 5 --out "$t/hang/o" 2>&1); rc=$?
  case "$rc:$a" in 2:*"t=1.5 s: no picture after 5 s (--frame-timeout)"*) [ -s "$t/hang/o/index-t0000.500.png" ] && [ $((SECONDS - s0)) -lt 120 ] \
      && ok "frames: a frame that never returns stops the run at --frame-timeout (exit 2), naming its t, the frames before it kept" \
      || bad "frames on a frame that never returns: $((SECONDS - s0)) s, $(ls "$t/hang/o" 2>&1)" ;;
    *) bad "frames on a frame that never returns: exit $rc: $(printf '%s' "$a" | tail -c 600)" ;; esac
  # a raised --timeout raises a frame's cap with it (a page whose frames are that slow), unless --frame-timeout says otherwise
  a=$(vh frames tools/film/fixture --at 0.5 --timeout 300 --out "$t/ft" 2>&1); b=$(vh frames tools/film/fixture --at 0.5 --timeout 300 --frame-timeout 7 --out "$t/ft" 2>&1)
  case "$a|$b" in *"a frame may take 300 s (--timeout)"*"|"*"a frame may take 7 s (--frame-timeout)"*) ok "frames: --timeout alone is a frame's cap too; --frame-timeout wins" ;;
    *) bad "frames: a frame's cap from --timeout: $(printf '%s' "$a" | head -1) | $(printf '%s' "$b" | head -1)" ;; esac
  # the other page tools stop at --frame-timeout too (exit 2, naming the t), not at their whole run's --timeout: fonts,
  # determinism and textcheck on the page above, whose frames never return from 1 s on; cues on a page whose cues getter
  # never returns (its script stuck in a loop)
  printf '%s\n' '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=160, height=90"></head><body><script>' \
    'window.film = { duration: 3, frame() {}, get cues() { for (;;) {} } };</script></body></html>' > "$t/hang/cues.html"
  s0=$SECONDS
  a=$(vh fonts check "$t/hang" --frame-timeout 3 --out "$t/hang/f" 2>&1); r1=$?
  b=$(vh determinism "$t/hang" --at 0.5,1.5 --frame-timeout 3 --out "$t/hang/d" 2>&1); r2=$?
  c=$(vh textcheck "$t/hang" --frame-timeout 3 --out "$t/hang/tc" 2>&1); r3=$?
  d=$(vh cues "$t/hang/cues.html" --frame-timeout 3 2>&1); r4=$?
  case "$r1:$r2:$r3:$r4|$a|$b|$c|$d" in "2:2:2:2|"*"t=1.25 s: no picture after 3 s (--frame-timeout)"*"|"*"A t=1.5 s: no picture after 3 s (--frame-timeout)"*"|"*"t=1.5 s: no picture after 3 s (--frame-timeout)"*"|"*"reading window.film.cues: no answer after 3 s (--frame-timeout)"*)
      [ $((SECONDS - s0)) -lt 150 ] && ok "fonts, determinism, textcheck and cues stop at --frame-timeout (exit 2), naming the frame or the read" \
        || bad "frame timeouts of fonts, determinism, textcheck, cues took $((SECONDS - s0)) s" ;;
    *) bad "frame timeouts (exit $r1:$r2:$r3:$r4): $(printf '%s' "$a" | tail -c 200) | $(printf '%s' "$b" | tail -c 200) | $(printf '%s' "$c" | tail -c 200) | $(printf '%s' "$d" | tail -c 200)" ;; esac
  # a browser stuck on its way out (it answers, then ignores Browser.close and SIGTERM: a stand-in on the DevTools pipe)
  # is killed: close() returns within seconds, so no tool waits on it until its watchdog
  printf '%s\n' 'import json, os, signal, time' 'signal.signal(signal.SIGTERM, signal.SIG_IGN); buf = b""' \
    'while b"Browser.getVersion" not in buf: buf += os.read(3, 65536)' \
    'm = json.loads(buf.split(b"\0")[0]); os.write(4, json.dumps({"id": m["id"], "result": {"product": "Stub/1"}}).encode() + b"\0")' \
    'while True: time.sleep(1)' > "$t/stuck.py"
  printf '#!/bin/sh\nexec python3 "%s"\n' "$t/stuck.py" > "$t/stuck"; chmod +x "$t/stuck"
  a=$(node --input-type=module -e 'import { launch } from "./tools/textcheck/browser.mjs";
const b = await launch(process.argv[1]); const t0 = Date.now();
const r = await Promise.race([b.close().then(() => "closed"), new Promise((ok) => setTimeout(() => ok("hung"), 30000))]);
console.log(r, Math.round((Date.now() - t0) / 1000)); process.exit(0);' "$t/stuck" 2>&1)
  case "$a" in "closed "[0-9]|"closed 1"[0-9]) ok "browser: one that ignores Browser.close and SIGTERM is killed, and close() returns ($a s)" ;; *) bad "browser close on a stuck browser: $a" ;; esac
  a=$(vh frames tools/film/fixture --at 5 --out "$t/e" 2>&1); rc=$?
  case "$rc:$a" in 2:*"outside the film"*) ok "frames: a time outside the film exits 2" ;; *) bad "frames outside the film: exit $rc: $(printf '%s' "$a" | tail -c 600)" ;; esac
  if command -v ffmpeg >/dev/null; then
    a=$(vh frames tools/film/fixture --strip 1:1.5 --fps 10 --out "$t/f" 2>&1); rc=$?
    if [ $rc = 0 ] && [ -s "$t/f/index-strip-1-1.5.jpg" ] && [ "$(ls "$t/f/index-strip-1-1.5" | wc -l | tr -d ' ')" = 5 ]; then ok "frames --strip: every frame of a span and one picture of them"
    else bad "frames --strip (exit $rc): $(printf '%s' "$a" | tail -c 600)"; fi
  fi
  a=$(vh determinism tools/film/fixture --samples 2 --out "$t/g" 2>&1); rc=$?
  case "$rc:$a" in 0:*"without the host's clock the frames differ"*"holds, every frame identical"*) ok "determinism: a page that reads Math.random holds under the host's clock, and is told it leans on it" ;;
    *) bad "determinism on its fixture: exit $rc: $(printf '%s' "$a" | tail -c 700)" ;; esac
  a=$(vh determinism tools/film/fixture/stateful.html --samples 2 --out "$t/h" 2>&1); rc=$?
  case "$rc:$a" in 1:*"does not hold"*) ok "determinism: a frame that depends on the frames before it does not hold (exit 1)" ;;
    *) bad "determinism on a stateful page: exit $rc: $(printf '%s' "$a" | tail -c 700)" ;; esac
  if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then
    a=$(vh render tools/film/fixture --workers 2 --gop 30 --out "$t/r/film.mp4" 2>&1); rc=$?
    if [ $rc = 0 ] && python3 - "$t/r/film.mp4" <<'PY'
import json, subprocess, sys
f = sys.argv[1]
st = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames,width,height,pix_fmt,color_range,color_space",
                                "-of", "json", f], capture_output=True, text=True).stdout)["streams"][0]
keys = [l.split(",")[0] for l in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", f],
                                                capture_output=True, text=True).stdout.split() if "K" in l.split(",")[1]]
side = json.load(open(f + ".render.json"))
ok = (st["nb_frames"], st["width"], st["height"], st["pix_fmt"], st["color_range"], st["color_space"]) == ("90", 320, 180, "yuv420p", "tv", "bt709")
ok = ok and [round(float(k), 3) for k in keys] == [0.0, 1.0, 2.0] and side["frames"] == 90 and side["encoder"]["gop"] == 30
sys.exit(0 if ok else 1)
PY
    then ok "render: every frame, BT.709 tv range, a keyframe exactly every --gop frames across the chunks, and how it was made beside it"
    else bad "render on its fixture (exit $rc): $(printf '%s' "$a" | tail -c 700)"; fi
    a=$(vh render tools/film/fixture --out "$t/r/film.mp4" 2>&1); rc=$?
    [ $rc = 0 ] && printf '%s' "$a" | grep -q '^render: done · the sound goes on with bin/vh mux$' \
      && ok "render: a second render of the same file after the first one ended is not locked out, and ends with its done line" || bad "render again (exit $rc): $(printf '%s' "$a" | tail -c 400)"
    a=$(OVH_FREE_BYTES=1000 vh render tools/film/fixture --out "$t/r/full.mp4" 2>&1); rc=$?
    case "$rc:$a" in 2:*"needed at the peak"*"GB free on that disk"*) ok "render: a disk too full for even a flat film stops it before a frame is drawn (exit 2)" ;;
      *) bad "render on a full disk: exit $rc: $(printf '%s' "$a" | tail -c 400)" ;; esac
    # the queue and the resume, on a page whose frames cost unevenly (tools/film/fixture/uneven.html: from 2 s on 30 ms
    # each, frame 75 5 s): chunks of one GOP, so 3 workers make the video 1 makes (PSNR: separate browsers). A render
    # whose frame 75 passes --frame-timeout 3 keeps the 5 chunks it finished; with the page edited they are not used;
    # the same command then draws only the last chunk, and the video is the one a whole render makes. The disk floor of a
    # resume is what it writes: the chunk left and the joined copy, the kept chunks' bytes in it (a disk 1000 bytes over
    # those refuses it, the chunks kept); its glyph check (the page writes a word) says the kept chunks' frames were not checked
    mkdir -p "$t/q" && sed 's|x.fillStyle = "#fc0";|x.font = "16px sans-serif"; x.fillStyle = "#fff"; x.fillText("chunk", 8, 24); x.fillStyle = "#fc0";|' tools/film/fixture/uneven.html > "$t/q/u.html"
    vh render "$t/q/u.html" --workers 1 --gop 15 --out "$t/q/one.mp4" >/dev/null 2>&1
    a=$(vh render "$t/q/u.html" --workers 3 --gop 15 --out "$t/q/three.mp4" 2>&1); rc=$?
    b=$(vh render "$t/q/u.html" --workers 2 --gop 15 --frame-timeout 3 --out "$t/q/r.mp4" 2>&1); rc2=$?
    kb=$(python3 -c 'import os, sys; d = sys.argv[1]; print(sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d) if f.startswith("part")))' "$t/q/.r.mp4.parts" 2>/dev/null || echo 0)
    e=$(OVH_FREE_BYTES=$((kb + 1000)) vh render "$t/q/u.html" --workers 2 --gop 15 --frame-timeout 3 --out "$t/q/r.mp4" 2>&1); rc5=$?
    case "$rc5:$e" in 2:*"needed at the peak for the 15 frames left to draw and the joined copy (5 chunks kept"*)
        kn=0; for kf in "$t/q/.r.mp4.parts"/part*.mp4; do [ ! -e "$kf" ] || kn=$((kn + 1)); done; [ $kn = 5 ] && ok "render: a resume's disk floor is the chunk left and the joined copy with the kept chunks' bytes; refused, it keeps them" \
          || bad "render: a resume refused for the disk did not keep its chunks: $(ls "$t/q/.r.mp4.parts" 2>&1)" ;;
      *) bad "render resume on a disk with room for the kept chunks only (exit $rc5, $kb bytes kept): $(printf '%s' "$e" | tail -c 500)" ;; esac
    printf '<!-- edited -->\n' >> "$t/q/u.html"
    c=$(vh render "$t/q/u.html" --workers 2 --gop 15 --frame-timeout 3 --out "$t/q/r.mp4" 2>&1); rc3=$?
    d=$(vh render "$t/q/u.html" --workers 2 --gop 15 --out "$t/q/r.mp4" 2>&1); rc4=$?
    if [ "$rc:$rc2:$rc3:$rc4" = 0:1:1:0 ] && printf '%s' "$b" | grep -q '5 of 6 chunks are kept' && printf '%s' "$c" | grep -q 'not used (changed: .*u\.html)' \
      && printf '%s' "$d" | grep -q 'resuming: 5 of 6 chunks kept' && printf '%s' "$d" | grep -q 'glyphs: checked in the 15 frames drawn now; the 75 frames of the 5 kept' \
      && [ ! -e "$t/q/.r.mp4.parts" ] && python3 - "$t/q" <<'PY'
import json, re, subprocess, sys
d = sys.argv[1]
def psnr(a, b):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", a, "-i", b, "-lavfi", "psnr", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"average:(inf|[\d.]+)", r)
    return float(m[-1]) if m else 0
side = json.load(open(d + "/r.mp4.render.json"))
ok = side["chunks"] == [[k, k + 15] for k in range(0, 90, 15)] and side["reused_chunks"] == 5 and side["frames"] == 90
sys.exit(0 if ok and psnr(d + "/one.mp4", d + "/three.mp4") >= 45 and psnr(d + "/one.mp4", d + "/r.mp4") >= 45 else 1)
PY
    then ok "render: one-GOP chunks taken in turn (3 workers make what 1 makes); a timed-out frame keeps the finished chunks, an edited page starts over, the same command resumes"
    else bad "render queue and resume: exit $rc:$rc2:$rc3:$rc4: $(printf '%s' "$b$c$d" | tail -c 900)"; fi
    # bin/vh patch passes --frame-timeout to the render of its frames: frames 74-76 of the film above take the GOP from 60,
    # and frame 75 (5 s) is past 2 s
    a=$(vh patch "$t/q/one.mp4" --frames 74-76 --frame-timeout 2 --out "$t/q/p.mp4" 2>&1); rc=$?
    case "$rc:$a" in 1:*"no picture after 2 s (--frame-timeout)"*"rendering frames"*"failed"*) ok "patch: --frame-timeout goes to the render of its frames" ;;
      *) bad "patch --frame-timeout (exit $rc): $(printf '%s' "$a" | tail -c 500)" ;; esac
    # the estimate, the page's own fps and a relative --out, from another folder: the canvas-film template (made for 30 fps)
    # at --fps 60 is over 600 frames, so it is estimated; the disk has room for a flat film (7.2 MB at the peak) but not
    # for what was measured (about 12 MB)
    mkdir -p "$t/e"
    a=$(cd "$t/e" && OVH_FREE_BYTES=8000000 "$VH_BASH" "$ROOT/bin/vh" render "$ROOT/engines/canvas-film/template" --fps 60 --out rel/f.mp4 2>&1); rc=$?
    case "$rc:$a" in
      2:*"--out rel/f.mp4 is from the current folder: "*"/e/rel/f.mp4, outside the project"*"drawn at 60 fps (--fps), the page says 30"*"estimate ("*" frames in about"*"is needed at the peak and 8 MB is free"*)
        [ ! -e "$t/e/rel/.f.mp4.parts" ] && ok "render: a long span is estimated first and refused on a disk that cannot hold it; --fps unlike the page's and an --out outside the project are said" \
          || bad "render: the refused estimate left $t/e/rel/.f.mp4.parts behind" ;;
      *) bad "render estimate, fps and --out (exit $rc): $(printf '%s' "$a" | tail -c 900)" ;;
    esac
    # bin/vh patch: the fixture rendered from 0.5 s with a keyframe every 20 frames (not a whole number of milliseconds) in
    # a folder whose name a filter graph would choke on; then its square turned blue from 1.4 s up to 1.7 s (the film's
    # frames 27–35) and those frames put back: 20–39 drawn again, the rest the film's own bytes and times. Naming only 27–29
    # leaves 30–35 changed outside the span: refused, the film untouched. A film without its sidecar is refused at once
    mkdir -p "$t/p, x" && cp tools/film/fixture/index.html "$t/p, x/index.html" && printf '# BRIEF\n' > "$t/p, x/BRIEF.md"   # a project: its activity log below
    vh render "$t/p, x" --range 0.5:2.5 --gop 20 --workers 2 --out "$t/p, x/out/film.mp4" >/dev/null 2>&1
    sed 's/x.fillStyle = "#fc0";/x.fillStyle = t >= 1.4 \&\& t < 1.7 ? "#0cf" : "#fc0";/' tools/film/fixture/index.html > "$t/p, x/index.html"
    s0=$(cksum < "$t/p, x/out/film.mp4")
    a=$(vh patch "$t/p, x/out/film.mp4" --frames 27-29 2>&1); rc=$?
    b=$(vh patch "$t/p, x/out/film.mp4" --frames 27-35 --verify full 2>&1); rc2=$?
    if [ $rc = 1 ] && printf '%s' "$a" | grep -q 'frames 30–35 are outside 27–29' && [ -s "$t/p, x/out/film.failed.mp4" ] && [ "$(cksum < "$t/p, x/out/film.mp4")" = "$s0" ] \
      && [ $rc2 = 0 ] && printf '%s' "$b" | grep -q '20–39 drawn again' && printf '%s' "$b" | grep -q 'frames: 60 (the film: 60) ✓' \
      && printf '%s' "$b" | grep -q "packets outside 20–39: 40 the film's own ✓" && python3 - "$t/p, x/out/film.patched.mp4" <<'PY'
import json, subprocess, sys
f = sys.argv[1]
def px(t):   # the square's colour at the film's t (the page's t + 0.5): blue inside the page's 1.4–1.7 s, yellow outside
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f, "-frames:v", "1", "-vf", f"crop=8:8:{int(36 + 80 * (t + 0.5))}:106,scale=1:1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return tuple(r.stdout[:3])
side = json.load(open(f + ".render.json"))
blue, yellow = px(1.0), px(0.7)
sys.exit(0 if blue[2] > blue[0] + 80 and yellow[0] > yellow[2] + 80 and side["patches"][0]["frames"] == [27, 35] and side["page"] == "../index.html" else 1)
PY
    then ok "patch: frames put back between keyframes, every packet outside them the film's own; an edit reaching past the frames named is refused, the film untouched"
    else bad "patch on the fixture: exit $rc / $rc2: $(printf '%s' "$a$b" | tail -c 900)"; fi
    # the render of a patch's frames is a step: its "render: done · the sound goes on with bin/vh mux" is left out, so the
    # patch's own last line is the only one that says it is done. A film that failed the patch's checks is kept as
    # <film>.failed.mp4 or the next free name (.failed-2.mp4): an earlier one is never overwritten, and the output names both
    cp -R "$t/p, x" "$t/p3"   # a copy: the activity log of the project below counts its commands
    k0=$(cksum < "$t/p3/out/film.failed.mp4")
    c=$(vh patch "$t/p3/out/film.mp4" --frames 27-29 2>&1); rc3=$?
    if [ $rc3 = 1 ] && ! printf '%s' "$a$b$c" | grep -q 'render: done' && printf '%s' "$b" | grep -q '^patch: done in ' \
      && [ -s "$t/p3/out/film.failed-2.mp4" ] && [ "$(cksum < "$t/p3/out/film.failed.mp4")" = "$k0" ] \
      && printf '%s' "$c" | grep -q 'the new one is in .*film.failed-2.mp4 to look at (.*film.failed.mp4 was there already and is left as it is)'
    then ok "patch: its render's \"render: done\" line is left out (patch says when it is done); a second failed patch keeps its film as .failed-2.mp4, the first one untouched"
    else bad "patch's last line and its failed films (exit $rc3): $(printf '%s' "$b" | tail -n 2 | tail -c 300) | $(printf '%s' "$c" | tail -n 1 | tail -c 400) | $(ls "$t/p3/out" | tr '\n' ' ')"; fi
    cp "$t/p, x/out/film.mp4" "$t/p, x/out/bare.mp4"
    a=$(vh patch "$t/p, x/out/bare.mp4" --frames 1-2 2>&1); rc=$?
    case "$rc:$a" in 2:*"no "*"bare.mp4.render.json"*) ok "patch: a film without its sidecar is refused at once (exit 2)" ;; *) bad "patch without a sidecar: exit $rc: $(printf '%s' "$a" | tail -c 400)" ;; esac
    # the activity log of that project: render's progress and note, and the ends node wrote itself (bin/vh exec'd into it)
    cat > "$t/act.py" <<'PY'
import json, sys
runs = {}
for r in map(json.loads, open(sys.argv[1], encoding="utf-8")):
    runs.setdefault(r["run"], []).append(r)
print(" | ".join(" ".join(r["event"] + (":%s" % r["exit"] if r["event"] == "end" else "") for r in rs) for rs in runs.values()))
render = next(rs for rs in runs.values() if rs[0]["cmd"] == "render")
note = next(r for r in render if r["event"] == "note")
sys.exit(0 if note["outputs"] == ["out/film.mp4", "out/film.mp4.render.json"] and [r["done"] for r in render if r["event"] == "progress"][-1] == 60 else 1)
PY
    a=$(python3 "$t/act.py" "$t/p, x/.ovh/activity.jsonl" 2>&1); rc=$?
    case "$rc:$a" in "0:start progress progress note end:0 | start note end:1 | start note end:0 | start end:2") ok "activity: render logs its progress and what it wrote, patch its outcome; node writes the end line of a run bin/vh exec'd into" ;;
      *) bad "activity of render and patch (rc $rc): $a" ;; esac
    # versions (tools/versions.py): in a project, each render and patch is a version; the film a render or an in-place
    # patch replaces is kept in out/versions/ (moved, the same bytes), its record says what changed; compare draws a
    # moment of two and says the PSNR; use makes an earlier one current again with the newer one kept; a disk under the
    # floor and OVH_KEEP_VERSIONS send the replaced one to the Trash, said and recorded; a film made elsewhere is kept as
    # found; OVH_VERSIONS=off records nothing; status lists them; clean prunes them to the Trash
    v="$t/ver"; mkdir -p "$v" && cp tools/film/fixture/index.html "$v/index.html" && printf '# BRIEF\n' > "$v/BRIEF.md"
    vh render "$v" --gop 15 --workers 2 --out "$v/out/film.mp4" >/dev/null 2>&1
    s1=$(cksum < "$v/out/film.mp4")
    a=$(vh render "$v" --gop 15 --workers 2 --out "$v/out/film.mp4" --note "second take" 2>&1); rc=$?
    sed 's/x.fillStyle = "#fc0";/x.fillStyle = t >= 1.4 \&\& t < 1.7 ? "#0cf" : "#fc0";/' tools/film/fixture/index.html > "$v/index.html"
    b=$(vh patch "$v/out/film.mp4" --frames 42-50 --in-place --note blue 2>&1); rc2=$?
    c=$(vh versions compare "$v" v2 v3 --t 1.5 --wipe --json 2>&1); rc3=$?
    d=$(vh versions use "$v" v2 2>&1); rc4=$?
    if [ "$rc:$rc2:$rc3:$rc4" = 0:0:0:0 ] && printf '%s' "$a" | grep -q 'version v2: out/film.mp4 (from v1)' && printf '%s' "$a" | grep -q 'v1 kept: out/versions/v1/film.mp4' \
      && [ "$(cksum < "$v/out/versions/v1/film.mp4")" = "$s1" ] && printf '%s' "$b" | grep -q 'version v3: out/film.mp4 (from v2)' \
      && printf '%s' "$d" | grep -q 'v2 is the current film at out/film.mp4 again; v3 is kept in out/versions/v3/film.mp4' \
      && python3 - "$v" "$c" <<'PY'
import json, os, subprocess, sys
v, c = sys.argv[1], json.loads(sys.argv[2])
L = json.loads(subprocess.run([sys.executable, "tools/versions.py", v, "--json"], capture_output=True, text=True).stdout)
by = {x["id"]: x for x in L["versions"]}
ch = by["v3"]["changed"]
side = json.load(open(v + "/out/versions/v3/film.mp4.render.json"))
ok = [x["state"] for x in L["versions"]] == ["kept", "current", "kept"] and L["current"] == {"out/film.mp4": "v2"} and by["v2"]["note"] == "second take"
ok = ok and by["v3"]["from"] == "v2" and by["v3"]["made_by"] == "patch" and ch["frames"] == [[42, 50]] and ch["drawn"] == [[30, 59]] and by["v1"]["changed"] == {"whole": True}
ok = ok and side["page"] == "../../../index.html" and os.path.isfile(os.path.join(v, "out/versions/v3", side["page"]))   # a kept sidecar still finds its page
ok = ok and c["a"]["frame"] == 45 and c["b"]["frame"] == 45 and isinstance(c["psnr"], float) and c["psnr"] < 30 and os.path.isfile(os.path.join(v, c["image"]))
sys.exit(0 if ok else 1)
PY
    then ok "versions: each render and patch a version, the one it replaces kept as it was; compare a moment of two (PSNR); use brings one back, the newer one kept"
    else bad "versions: render/patch/compare/use (exit $rc:$rc2:$rc3:$rc4): $(printf '%s' "$a$b$c$d" | tail -c 900)"; fi
    # a disk under the floor: the replaced film goes to the Trash, named for the project, said and recorded; OVH_KEEP_VERSIONS=1
    # sends the oldest kept one there too; a film made elsewhere is kept as found; OVH_VERSIONS=off writes nothing
    a=$(OVH_FREE_BYTES=1000000000 OVH_TRASH_DIR="$t/trash" vh render "$v" --gop 15 --workers 2 --out "$v/out/film.mp4" 2>&1); rc=$?
    cp "$v/out/versions/v3/film.mp4" "$v/out/film.mp4"; touch "$v/out/film.mp4"   # a film put there by hand
    b=$(OVH_KEEP_VERSIONS=1 OVH_TRASH_DIR="$t/trash" vh render "$v" --gop 15 --workers 2 --out "$v/out/film.mp4" 2>&1); rc2=$?
    n0=$(wc -c < "$v/out/versions/versions.json")
    OVH_VERSIONS=off vh render "$v" --gop 15 --workers 2 --out "$v/out/film.mp4" >/dev/null 2>&1
    if [ "$rc:$rc2" = 0:0 ] && printf '%s' "$a" | grep -q 'v2 to the Trash: not kept: 1.0 GB free on that disk' && [ -d "$t/trash/ver v2" ] \
      && printf '%s' "$b" | grep -q 'was not made by bin/vh render or patch' && printf '%s' "$b" | grep -q 'v1 to the Trash: more than 1 earlier version' \
      && printf '%s' "$b" | grep -q 'v3 to the Trash: more than 1 earlier version' \
      && [ "$(wc -c < "$v/out/versions/versions.json")" = "$n0" ] && python3 - "$v" <<'PY'
import json, subprocess, sys
L = json.loads(subprocess.run([sys.executable, "tools/versions.py", sys.argv[1], "--json"], capture_output=True, text=True).stdout)
st = {x["id"]: (x["made_by"], x["state"]) for x in L["versions"]}
S = json.loads(subprocess.run(["bash", "bin/vh", "status", sys.argv[1], "--json"], capture_output=True, text=True).stdout)
ok = st["v1"][1] == "trashed" and st["v2"][1] == "trashed" and st["v5"] == ("found", "kept") and st["v6"][1] == "changed"   # OVH_VERSIONS=off replaced v6
ok = ok and S["versions"]["list"][-1]["id"] == "v6" and S["versions"]["current"] == {} and all(not r["path"].startswith("out/versions") for r in S["renders"])
sys.exit(0 if ok else 1)
PY
    then ok "versions: a full disk and OVH_KEEP_VERSIONS send the replaced film to the Trash (said, recorded); a film made by hand is kept as found; OVH_VERSIONS=off records nothing; status lists them"
    else bad "versions: the Trash, found, off, status (exit $rc:$rc2): $(printf '%s' "$a$b" | tail -c 900)"; fi
    a=$(vh versions 2>&1); rc=$?; b=$(vh versions compare "$v" v4 --t 1 2>&1); rc2=$?; c=$(vh versions use "$v" v1 2>&1); rc3=$?
    d=$(vh versions compare "$v" v4 v5 2>&1); rc4=$?; e=$(vh versions compare "$v" v4 v5 --t 1 --wipe=abc 2>&1); rc5=$?
    case "$rc:$rc2:$rc3:$rc4:$rc5:$c:$d:$e" in 2:2:1:2:2:*"v1 is trashed: its film is not in the project"*"compare needs --t"*"--wipe abc: where the line goes"*)
        ok "versions: usage errors exit 2 (a --wipe that is no share of the width too), a version in the Trash cannot be used (exit 1)" ;;
      *) bad "versions usage (exit $rc:$rc2:$rc3:$rc4:$rc5): $(printf '%s' "$a$b$c$d$e" | tail -c 500)" ;; esac
    a=$(vh clean "$v" 2>&1); b=$(OVH_TRASH_DIR="$t/trash" vh clean "$v" --yes --keep-versions 1 2>&1); rc=$?
    c=$(OVH_TRASH_DIR="$t/trash" vh clean "$v" --yes 2>&1); rc2=$?
    if [ "$rc:$rc2" = 0:0 ] && printf '%s' "$a" | grep -q 'versions (earlier versions of the films' && printf '%s' "$a" | grep -q 'out/versions/v5/' \
      && ! printf '%s' "$b" | grep -q 'out/versions/v5/' && [ ! -e "$v/out/versions/v5" ] && [ -d "$t/trash/ver v5" ] && [ -f "$v/out/versions/versions.json" ] \
      && vh versions "$v" | grep -q 'v5 .*in the Trash'
    then ok "clean: the earlier versions listed, then to the Trash but the newest --keep-versions N; their record says so"
    else bad "clean of versions (exit $rc:$rc2): $(printf '%s' "$a$b$c" | tail -c 700)"; fi
    # patch --shot / --chapter (tools/film/fixture/shots.html: S02 green from 1.4 to 2.2 s, under S03's 0.3 s dissolve to
    # 2.5 s): S02 turned yellow; --shot S02 draws 42–74 (through the dissolve) and passes, naming S02; the frames of S02's
    # own span alone are refused (the dissolve shows it); a chapter by its id, an unknown shot and a chapter outside the
    # film exit 2; shots.json in the project wins over the page
    s="$t/shots"; mkdir -p "$s" && cp tools/film/fixture/shots.html "$s/film.html" && printf '# BRIEF\n' > "$s/BRIEF.md"
    vh render "$s" --gop 15 --workers 2 --out "$s/out/film.mp4" >/dev/null 2>&1
    sed 's/colour: "#3c3"/colour: "#cc3"/' tools/film/fixture/shots.html > "$s/film.html"
    a=$(vh patch "$s/out/film.mp4" --frames 42-65 --out "$s/out/own.mp4" 2>&1); rc=$?
    b=$(vh patch "$s/out/film.mp4" --shot S02 --out "$s/out/shot.mp4" 2>&1); rc2=$?
    c=$(vh patch "$s/out/film.mp4" --chapter ch-two --out "$s/out/ch.mp4" 2>&1); rc3=$?
    d=$(vh patch "$s/out/film.mp4" --shot S09 2>&1); rc4=$?
    printf '[{"id": "X1", "start": "0:01.4", "end": 2.5}]\n' > "$s/shots.json"
    e=$(vh patch "$s/out/film.mp4" --shot X1 --out "$s/out/x.mp4" 2>&1); rc5=$?
    if [ "$rc:$rc2:$rc3:$rc4:$rc5" = 1:0:0:2:0 ] && printf '%s' "$a" | grep -q 'frames 66–74 are outside 42–65' && printf '%s' "$b" | grep -q 'frames 42–74 (1.400–2.500 s) asked' \
      && printf '%s' "$b" | grep -q "S02: 1.400–2.500 s (+0.3 s: S03's transition draws it underneath)" && printf '%s' "$c" | grep -q 'frames 42–89' \
      && printf '%s' "$d" | grep -q 'no shot S09: .*film.html (window.film.shots) has S01, S02, S03' && printf '%s' "$e" | grep -q 'shots from .*shots.json' && python3 - "$s" <<'PY'
import json, subprocess, sys
s = sys.argv[1]
L = json.loads(subprocess.run([sys.executable, "tools/versions.py", s, "--json"], capture_output=True, text=True).stdout)
by = {x["film"]: x for x in L["versions"]}
side = json.load(open(s + "/out/film.mp4.render.json"))
ok = side["shots"][2] == {"id": "S03", "start": 2.2, "end": 3, "transition": 0.3} and side["chapters"][1] == {"t": 1.4, "title": "two", "id": "ch-two"}
ok = ok and by["out/shot.mp4"]["changed"]["shots"] == ["S02", "S03"] and by["out/shot.mp4"]["changed"]["asked"]["shots"] == ["S02"] and by["out/shot.mp4"]["from"] == by["out/film.mp4"]["id"]
ok = ok and by["out/x.mp4"]["changed"]["shots"] == ["X1"] and "out/own.mp4" not in by
sys.exit(0 if ok else 1)
PY
    then ok "patch --shot / --chapter: a shot's frames through the next cut's transition, a chapter by its id, the shots named in the version; shots.json wins; unknown ones exit 2"
    else bad "patch --shot / --chapter (exit $rc:$rc2:$rc3:$rc4:$rc5): $(printf '%s' "$a$b$c$d$e" | tail -c 900)"; fi
    # two spans apart: their windows drawn separately and both joined in, the frames between them the film's own bytes
    a=$(vh patch "$s/out/film.mp4" --frames 5-6,80-82 --out "$s/out/two.mp4" 2>&1); rc=$?
    if [ $rc = 0 ] && printf '%s' "$a" | grep -q '0–14, 75–89 drawn again (keyframe to keyframe, 30 frames)' && printf '%s' "$a" | grep -q "packets outside 0–14, 75–89: 60 the film's own ✓"
    then ok "patch: two spans apart are drawn as two windows, the film's own packets between them"
    else bad "patch on two spans (exit $rc): $(printf '%s' "$a" | tail -c 700)"; fi
    # a link in the project to a film outside it: render and patch --in-place replace the link, never write into what it
    # points to (with versions and with OVH_VERSIONS=off), as before versions
    l="$t/lk"; mkdir -p "$l/out" "$t/outside" && cp tools/film/fixture/index.html "$l/index.html" && printf '# BRIEF\n' > "$l/BRIEF.md"
    vh render "$l" --gop 15 --workers 2 --out "$t/outside/target.mp4" >/dev/null 2>&1
    cp "$t/outside/target.mp4" "$t/outside/t2.mp4"; s1=$(cksum < "$t/outside/target.mp4")
    sig() { python3 -c 'import os, sys; print(" ".join("%d:%d" % (os.stat(f).st_ino, os.stat(f).st_mtime_ns) for f in sys.argv[1:]))' "$@"; }
    g1=$(sig "$t/outside/target.mp4" "$t/outside/t2.mp4")   # the same file, untouched: a re-render of the same page has the same bytes
    ln -s "$t/outside/target.mp4" "$l/out/link.mp4"; ln -s "$t/outside/t2.mp4" "$l/out/off.mp4"; ln -s "$t/outside/target.mp4" "$l/out/p.mp4"
    cp "$t/outside/target.mp4.render.json" "$l/out/p.mp4.render.json"
    a=$(vh render "$l" --gop 15 --workers 2 --out "$l/out/link.mp4" 2>&1); rc=$?
    OVH_VERSIONS=off vh render "$l" --gop 15 --workers 2 --out "$l/out/off.mp4" >/dev/null 2>&1; rc2=$?
    b=$(vh patch "$l/out/p.mp4" --frames 5-6 --in-place 2>&1); rc3=$?
    if [ "$rc:$rc2:$rc3" = 0:0:0 ] && [ "$(sig "$t/outside/target.mp4" "$t/outside/t2.mp4")" = "$g1" ] && [ "$(cksum < "$t/outside/t2.mp4")" = "$s1" ] \
      && [ -f "$l/out/link.mp4" ] && [ ! -L "$l/out/link.mp4" ] && [ ! -L "$l/out/off.mp4" ] && [ ! -L "$l/out/p.mp4" ] \
      && printf '%s' "$a" | grep -q 'out/link.mp4 was a link to .*target.mp4: the link is replaced by the new film, what it points to is left as it was'
    then ok "render and patch --in-place on a link replace the link, never what it points to (versions on and off)"
    else bad "a film path that is a link (exit $rc:$rc2:$rc3; target $( [ "$(cksum < "$t/outside/target.mp4")" = "$s1" ] && echo same || echo changed)): $(printf '%s' "$a$b" | tail -c 600)"; fi
    # an --out inside out/versions (a kept version's folder) is refused before anything is drawn, the kept film untouched
    v="$t/in"; mkdir -p "$v" && cp tools/film/fixture/index.html "$v/index.html" && printf '# BRIEF\n' > "$v/BRIEF.md"
    vh render "$v" --gop 15 --workers 2 --out "$v/out/film.mp4" >/dev/null 2>&1; vh render "$v" --gop 15 --workers 2 --out "$v/out/film.mp4" >/dev/null 2>&1
    s1=$(cksum < "$v/out/versions/v1/film.mp4")
    a=$(vh render "$v" --gop 15 --workers 2 --out "$v/out/versions/v1/film.mp4" 2>&1); rc=$?
    b=$(vh patch "$v/out/film.mp4" --frames 5-6 --out "$v/out/versions/v1/film.mp4" 2>&1); rc2=$?
    c=$(vh patch "$v/out/versions/v1/film.mp4" --frames 5-6 2>&1); rc3=$?
    if [ "$rc:$rc2:$rc3" = 2:2:2 ] && [ "$(cksum < "$v/out/versions/v1/film.mp4")" = "$s1" ] && printf '%s' "$a$b$c" | grep -q 'inside out/versions' \
      && vh versions "$v" | grep -q 'v1 .*kept out/versions/v1/film.mp4'
    then ok "render and patch refuse an --out inside out/versions (exit 2), the kept film untouched"
    else bad "an --out inside out/versions (exit $rc:$rc2:$rc3): $(printf '%s' "$a$b$c" | tail -c 600)"; fi
    # use: the check record at the film's path is the version's own or none. v2 checked (a record made after it), v1 never:
    # after use v1 there is no record at out/check/film.check.json, v2's went into its folder; use v2 brings it back
    mkdir -p "$v/out/check"
    printf '{"version": 1, "tool": "bin/vh check", "video": "out/film.mp4", "t": %s, "at": "now", "exit": 0, "verdict": "pass", "counts": {"fail": 0, "warn": 0, "info": 0}, "findings": []}\n' \
      "$(python3 -c 'import time; print(time.time() + 2)')" > "$v/out/check/film.check.json"
    a=$(vh versions use "$v" v1 2>&1); rc=$?
    b=$(python3 - "$v" <<'PY'
import json, os, subprocess, sys
v = sys.argv[1]
L = json.loads(subprocess.run([sys.executable, "tools/versions.py", v, "--json"], capture_output=True, text=True).stdout)
S = json.loads(subprocess.run(["bash", "bin/vh", "status", v, "--json"], capture_output=True, text=True).stdout)
by = {x["id"]: x for x in L["versions"]}
r = next(x for x in S["renders"] if x["path"] == "out/film.mp4")
print(os.path.exists(v + "/out/check/film.check.json"), by["v1"]["state"], by["v1"]["check"], by["v2"]["state"], (by["v2"]["check"] or {}).get("verdict"), r["check"])
PY
)
    c=$(vh versions use "$v" v2 2>&1); rc2=$?
    d=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["verdict"])' "$v/out/check/film.check.json" 2>&1)
    if [ "$rc:$rc2" = 0:0 ] && [ "$b" = "False current None kept pass None" ] && [ "$d" = pass ]
    then ok "versions use: the check record at the film's path is the version's own or none; the displaced one's goes with it and comes back with it"
    else bad "use and the check record (exit $rc:$rc2): $b | $d | $(printf '%s' "$a$c" | tail -c 400)"; fi
    # a version's check record is the film's by the size and mtime_ns it kept (tools/checkrec.py), not by its time: made after
    # the film, with the film's numbers it is reported (current, and kept with the film that was displaced), with other numbers
    # (size or mtime_ns) it is not; a record of the old kind, without them, goes by time as before
    if python3 - "$v" <<'PY'
import json, os, subprocess, sys, time
v = sys.argv[1]; rec = v + "/out/check/film.check.json"; film = v + "/out/film.mp4"
listing = lambda: {x["id"]: x for x in json.loads(subprocess.run([sys.executable, "tools/versions.py", v, "--json"], capture_output=True, text=True).stdout)["versions"]}
def write(**f):   # a passing record of the film at its path, made after it, with the fields given
    json.dump({"version": 1, "tool": "bin/vh check", "video": "out/film.mp4", "t": time.time() + 2, "at": "now", "exit": 0, "verdict": "pass",
               "counts": {"fail": 0, "warn": 0, "info": 0}, "findings": [], **f}, open(rec, "w"))
st = os.stat(film)
got = []
for f in ({"size": st.st_size, "mtime_ns": st.st_mtime_ns}, {"size": st.st_size + 1, "mtime_ns": st.st_mtime_ns},
          {"size": st.st_size, "mtime_ns": st.st_mtime_ns + 1}, {}):
    write(**f); got.append(listing()["v2"]["check"] is not None)
write(size=st.st_size, mtime_ns=st.st_mtime_ns)
subprocess.run([sys.executable, "tools/versions.py", "use", v, "v1"], capture_output=True)   # v2 is kept, its record with it
kept = listing()["v2"]
got.append(kept["state"] == "kept" and kept["check"] is not None)
kr = os.path.join(v, kept["check"]["record"]); j = json.load(open(kr)); j["size"] += 1; json.dump(j, open(kr, "w"))
got.append(listing()["v2"]["check"] is None)
subprocess.run([sys.executable, "tools/versions.py", "use", v, "v2"], capture_output=True)   # as it was
sys.exit(0 if got == [True, False, False, True, True, True] else 1)
PY
    then ok "versions: a check record is the film's by the size and mtime_ns it kept (current and kept versions), not by its time; a record without them goes by time"
    else bad "versions: a check record and the film's size and mtime_ns"; fi
    # a patch in place commits only over the film it cut: versions use refuses while it runs (its lock), and a film rewritten
    # meanwhile (the same bytes, another file) is left as it is, the patched one beside it (exit 1), the record unchanged
    sed 's|x.fillStyle = "#fc0"; x.fillRect(20 + t \* 80, 90, 40, 40);|x.fillStyle = "#fc0"; x.fillRect(20 + t * 80, 90, 40, 40); return new Promise((ok) => setTimeout(ok, 400));|' \
      tools/film/fixture/index.html > "$v/index.html"
    waitwork() { local n=0; while [ ! -d "$v/out/.film.mp4.patch" ] && [ $n -lt 300 ]; do sleep 0.1; n=$((n + 1)); done; }
    vh patch "$v/out/film.mp4" --frames 20-21 --in-place --workers 1 > "$t/patch-use.log" 2>&1 & pid=$!
    waitwork; a=$(vh versions use "$v" v1 2>&1); rc=$?
    wait $pid; p_use=$?
    vh patch "$v/out/film.mp4" --frames 20-21 --in-place --workers 1 > "$t/patch-swap.log" 2>&1 & pid=$!
    waitwork; cp "$v/out/film.mp4" "$t/same.mp4"; mv "$t/same.mp4" "$v/out/film.mp4"
    nv=$(python3 -c 'import json, sys; print(len(json.load(open(sys.argv[1]))["versions"]))' "$v/out/versions/versions.json")
    wait $pid; p_swap=$?
    b=$(cat "$t/patch-swap.log")
    nv2=$(python3 -c 'import json, sys; print(len(json.load(open(sys.argv[1]))["versions"]))' "$v/out/versions/versions.json")
    if [ "$rc:$p_use:$p_swap" = 1:0:1 ] && printf '%s' "$a" | grep -q 'is writing out/film.mp4' && printf '%s' "$b" | grep -q 'is not the one the patch cut from' \
      && [ -f "$v/out/film.new.mp4" ] && [ "$nv" = "$nv2" ]
    then ok "patch --in-place commits only over the film it cut: use waits for it, a film rewritten meanwhile is left as it is and the patched one goes beside it"
    else bad "patch and a film changed meanwhile (use exit $rc, patches $p_use/$p_swap, versions $nv/$nv2): $a | $(printf '%s' "$b" | tail -c 500)"; fi
    # proxy and thumbs (tools/proxy.py): a film with sound (the shots fixture, a tone muxed on) gets a proxy at --size on
    # its short side with a keyframe every 6 frames, no B-frames and its sound, and thumbs (tiles in a sheet, a picture a
    # shot from the sidecar's shots, a map); run again, both are up to date; after a patch in place only the proxy's
    # window around the frames drawn again is encoded (it decodes as a whole remake does, its sound kept) and only the
    # tiles and shots there are taken; a project with no film: thumbs from the page, no proxy (exit 2)
    x="$t/px"; mkdir -p "$x" && cp tools/film/fixture/shots.html "$x/film.html" && printf '# BRIEF\n' > "$x/BRIEF.md"
    vh render "$x" --gop 15 --workers 2 --out "$x/out/film.mp4" >/dev/null 2>&1
    ffmpeg -v error -nostdin -y -i "$x/out/film.mp4" -f lavfi -i "sine=frequency=440:duration=3" -map 0:v -map 1:a -c:v copy -c:a aac -shortest "$x/out/final.mp4"
    sed 's/colour: "#3c3"/colour: "#cc3"/' tools/film/fixture/shots.html > "$x/film.html"
    vh patch "$x/out/final.mp4" --sidecar "$x/out/film.mp4.render.json" --shot S02 --in-place >/dev/null 2>&1
    a=$(vh proxy "$x/out/final.mp4" --size 90 2>&1); rc=$?
    b=$(vh proxy "$x/out/final.mp4" --size 90 2>&1); rc2=$?
    c=$(vh thumbs "$x" --every 0.5 --width 80 2>&1); rc3=$?
    sed 's/colour: "#c33"/colour: "#c3c"/' "$x/film.html" > "$x/f2.html" && mv "$x/f2.html" "$x/film.html"
    vh patch "$x/out/final.mp4" --shot S01 --in-place >/dev/null 2>&1
    d=$(vh proxy "$x/out/final.mp4" --size 90 2>&1); rc4=$?
    e=$(vh thumbs "$x" --every 0.5 --width 80 --json 2>&1); rc5=$?
    cp "$x/out/proxy/final.mp4" "$t/refreshed.mp4"
    vh proxy "$x/out/final.mp4" --size 90 --full >/dev/null 2>&1
    if [ "$rc:$rc2:$rc3:$rc4:$rc5" = 0:0:0:0:0 ] && printf '%s' "$a" | grep -q '160x90, a keyframe every 6 frames, with sound · made' && printf '%s' "$b" | grep -q 'up to date' \
      && printf '%s' "$c" | grep -q '6 tiles every 0.5 s (80x46) in 1 sheet(s), 3 shot picture(s)' && printf '%s' "$d" | grep -q 'refreshed: 1 window(s) of frames encoded anew, 48 of 90 frames' \
      && python3 - "$x" "$t/refreshed.mp4" "$e" <<'PY'
import json, re, subprocess, sys
x, refreshed, e = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
def run(*a): return subprocess.run(a, capture_output=True, text=True)
keys = [i for i, l in enumerate(run("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=flags", "-of", "csv=p=0", refreshed).stdout.split()) if "K" in l]
st = run("ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,nb_frames,has_b_frames", "-of", "json", refreshed).stdout
st = {s["codec_type"]: s for s in json.loads(st)["streams"]}
m = re.findall(r"average:(inf|[\d.]+)", run("ffmpeg", "-v", "info", "-i", refreshed, "-i", x + "/out/proxy/final.mp4", "-lavfi", "psnr", "-f", "null", "-").stderr)
rec = json.load(open(x + "/out/proxy/final.mp4.json"))
ok = keys == list(range(0, 90, 6)) and st["video"]["nb_frames"] == "90" and (st["video"]["width"], st["video"]["height"]) == (160, 90) and "audio" in st
ok = ok and m and (m[-1] == "inf" or float(m[-1]) >= 50) and rec["made"] == "full" and rec["source_version"] == "v4"
ok = ok and e["made"] == "refreshed" and e["taken"] == {"tiles": 3, "shots": 1} and e["from"] == "proxy" and [s["id"] for s in e["shots"]] == ["S01", "S02", "S03"]
ok = ok and e["tiles"][3] == {"i": 3, "t": 1.5, "frame": 45, "sheet": 0, "x": 240, "y": 0} and e["sheets"][0]["size"] == [480, 46]
sys.exit(0 if ok else 1)
PY
    then ok "proxy and thumbs: a small short-GOP copy with its sound, a tile sheet, a picture a shot and the map; up to date when the film is; after a patch in place only its window is encoded again and its tiles taken"
    else bad "proxy and thumbs (exit $rc:$rc2:$rc3:$rc4:$rc5): $(printf '%s' "$a$b$c$d" | tail -c 900)"; fi
    mkdir -p "$t/nofilm" && cp tools/film/fixture/shots.html "$t/nofilm/film.html" && printf '# BRIEF\n' > "$t/nofilm/BRIEF.md"
    a=$(vh thumbs "$t/nofilm" --every 1 2>&1); rc=$?; b=$(vh proxy "$t/nofilm" 2>&1); rc2=$?; c=$(vh proxy "$x" --size x 2>&1); rc3=$?
    mkdir -p "$x/out/review/proxy" && cp "$x/out/film.mp4" "$x/out/review/proxy/kept.mp4"   # a folder of that name deeper down is the person's own
    s=$(vh status "$x" --json | python3 -c 'import json, sys; print(" ".join(r["path"] for r in json.load(sys.stdin)["renders"]))')
    case "$rc:$rc2:$rc3:$a:$b:$s" in 0:2:2:*"3 tiles every 1.0 s"*"3 shot picture(s)"*"from the page"*:*"no film in"*"to make a proxy of"*:*) case " $s " in *" out/proxy"*|*" out/versions"*) bad "status lists the proxy or a kept version as a render: $s" ;;
        *" out/review/proxy/kept.mp4 "*) ok "thumbs on a project with no film: from the page; proxy needs a film (exit 2); status lists neither out/proxy nor out/versions, but a proxy folder deeper down" ;;
        *) bad "status left out out/review/proxy/kept.mp4: $s" ;; esac ;;
      *) bad "thumbs from the page, proxy without a film (exit $rc:$rc2:$rc3): $(printf '%s' "$a$b$c" | tail -c 600)" ;; esac
  fi
  if node -e 'import("./tools/film/host.mjs").then((m) => process.exit(m.findRuntime(process.cwd()) ? 0 : 1))' 2>/dev/null; then
    mkdir -p "$t/hf"
    cat > "$t/hf/index.html" <<'HTML'
<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#000}.clip{position:absolute;inset:0}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="2" data-width="320" data-height="180">
<div class="clip" data-start="0" data-duration="1" data-track-index="1" style="background:#c33"></div>
<div class="clip" data-start="1" data-duration="1" data-track-index="1" style="background:#3c3"></div>
</div></body></html>
HTML
    a=$(vh frames "$t/hf" --at 0.5,1.5 --out "$t/hf/out" 2>&1); rc=$?
    if [ $rc = 0 ] && printf '%s' "$a" | grep -q "HyperFrames runtime" && python3 - "$t/hf/out" <<'PY'
import sys, zlib, struct
def first_pixel(f):   # the PNG's first pixel, enough to tell the two clips apart
    d = open(f, "rb").read(); i = 8; idat = b""
    while i < len(d):
        n, kind = struct.unpack(">I4s", d[i:i + 8]); body = d[i + 8:i + 8 + n]; i += 12 + n
        if kind == b"IHDR": bpp = {2: 3, 6: 4}[body[9]]
        if kind == b"IDAT": idat += body
    row = zlib.decompress(idat)
    return tuple(row[1:1 + bpp][:3])
a, b = first_pixel(sys.argv[1] + "/index-t0000.500.png"), first_pixel(sys.argv[1] + "/index-t0001.500.png")
sys.exit(0 if a[0] > 150 and a[1] < 100 and b[1] > 150 and b[0] < 100 else 1)
PY
    then ok "frames: a HyperFrames composition without window.film is drawn by its own runtime (clips shown by their data-start)"
    else bad "frames with the HyperFrames runtime (exit $rc): $(printf '%s' "$a" | tail -c 600)"; fi
  else skip "frames on a HyperFrames composition" "no HyperFrames runtime installed (styles/_swatch: npm ci)"; fi
  # the canvas-film engine's template (engines/canvas-film): two frames draw, each the same PNG drawn first and drawn after
  # the other (12.8 s is inside a page turn); a cue whose word is gone stops it in ready at once, naming the shot and the
  # cue; its reads and captions pass textcheck
  if python3 tools/audio/test_music_clock.py --film; then ok "music clock: live cues, reads, chapters and deterministic frames"; else bad "music clock page"; fi
  if python3 tools/audio/test_time_map.py --film; then ok "time map: live event cues move with the map, a map made on other music stops ready, deterministic frames"; else bad "time map page"; fi
  local c="$ROOT/engines/canvas-film/template" s0 pid left seen alive
  a=$(vh frames "$c" --at 4.9,12.8 --out "$t/cf1" 2>&1); rc=$?
  # a machine without the template's CJK faces (the Linux runner) draws in a fallback and says so, which is exit 1; that
  # alone is fine here, as the frames are still compared
  if [ $rc = 1 ] && printf '%s' "$a" | grep -q 'fonts this machine does not have' \
    && ! printf '%s\n' "$a" | grep -E 'while loading:|^  t=[0-9.]+ s:|just after the last frame' | grep -qv 'fonts this machine does not have'; then rc=0; fi
  vh frames "$c" --at 12.8,4.9 --out "$t/cf2" >/dev/null 2>&1
  if [ $rc = 0 ] && cmp -s "$t/cf1/film-t0004.900.png" "$t/cf2/film-t0004.900.png" && cmp -s "$t/cf1/film-t0012.800.png" "$t/cf2/film-t0012.800.png"
  then ok "canvas-film: the template draws, and a frame is the same PNG drawn first or after another (one inside a transition too)"
  else bad "canvas-film template frames (exit $rc): $(printf '%s' "$a" | tail -c 800)"; fi
  mkdir "$t/cfb" && cp -R "$c/." "$t/cfb/" && sed 's/"@a2:第二张"/"@a2:第三张"/' "$c/src/50-shots.js" > "$t/cfb/src/50-shots.js"
  s0=$SECONDS; a=$(vh frames "$t/cfb" --at 1 --out "$t/cfb/out" 2>&1); rc=$?
  case "$rc:$a" in
    2:*'shot S02 (o.two), cue "@a2:第三张"'*'it now reads'*) if [ $((SECONDS - s0)) -lt 60 ]; then ok "canvas-film: a cue whose word is gone stops it in ready ($((SECONDS - s0)) s), naming the shot, the cue and the line as it reads now"
      else bad "canvas-film: the broken cue was reported after $((SECONDS - s0)) s, not at once"; fi ;;
    *) bad "canvas-film with a broken cue: exit $rc: $(printf '%s' "$a" | tail -c 800)" ;;
  esac
  # no face of film.html on this machine: each missing face is named once, the 900 serif and its face for two dashes apart
  mkdir "$t/cfn" && cp -R "$c/." "$t/cfn/" && sed 's/local("[^"]*")/local("No Such Face CI")/g' "$c/film.html" > "$t/cfn/film.html"
  a=$(vh frames "$t/cfn" --at 1 --out "$t/cfn/out" 2>&1 | grep 'fonts this machine does not have')
  if printf '%s' "$a" | python3 -c '
import re, sys
m = re.search(r"drawn in a fallback: (.*) \(film\.html", sys.stdin.read()); L = m.group(1).split(" · ") if m else []
sys.exit(0 if len(L) == len(set(L)) == 8 and {"Film Serif 900", "Film Serif 900 for U+2013, U+2212"} <= set(L) else 1)'
  then ok "canvas-film: a machine without the faces names each missing face once (a face for a few characters says which)"
  else bad "canvas-film missing faces: $a"; fi
  a=$(vh textcheck "$c" --out "$t/cftc" 2>&1); rc=$?
  [ $rc = 0 ] && ok "canvas-film: textcheck passes the template's reads and captions" || bad "textcheck on the canvas-film template (exit $rc): $(printf '%s' "$a" | tail -c 800)"
  mkdir "$t/cfq" && cp -R "$c/." "$t/cfq/"
  a=$(vh cues "$t/cfq" --save 2>&1); rc=$?
  python3 - "$t/cfq/audio/timeline.zh.json" <<'PY'
import json, sys
p = sys.argv[1]; tl = json.load(open(p, encoding="utf-8"))
for s in tl["segments"]:
    if s["id"] in ("b1", "b2"):   # a new take: the last two lines 0.4 s later
        s["start"] = round(s["start"] + 0.4, 3); s["end"] = round(s["end"] + 0.4, 3)
        for w in s.get("words", []): w["start"] = round(w["start"] + 0.4, 3); w["end"] = round(w["end"] + 0.4, 3)
tl["duration"] = round(tl["duration"] + 0.4, 3)
json.dump(tl, open(p, "w", encoding="utf-8"), ensure_ascii=False)
PY
  b=$(vh cues "$t/cfq" 2>&1); rc2=$?
  if [ $rc = 0 ] && [ $rc2 = 0 ] && grep -q '"timeline_sha256": "[0-9a-f]\{64\}"' "$t/cfq/out/cues.json" && printf '%s' "$a" | grep -q 'S02.o.one *@a2:第一张' \
    && printf '%s' "$b" | grep -q 'another take of the narration): 7 moved, 0 new, 0 gone' && printf '%s' "$b" | grep -q 'S03.at .*(+0.400)'
  then ok "cues: the template's cues in order, saved with the timeline's sha256; a new take says which moved and by how much"
  else bad "cues on the canvas-film template: exit $rc / $rc2: $(printf '%s' "$a$b" | tail -c 800)"; fi
  a=$(vh cues "$ROOT/tools/film/fixture/index.html" 2>&1); rc=$?
  [ $rc = 2 ] && printf '%s' "$a" | grep -q 'gives no window.film.cues' && ok "cues: a page without window.film.cues exits 2 and says so" || bad "cues on a page without cues: exit $rc: $a"
  # covers picked by cue: the template's cover A is drawn into out/covers; a longer opening (every line 0.4 s later) moves
  # its time with the narration, and the picture it takes stays the same (only the grain, a function of t, differs)
  mkdir "$t/cov" && cp -R "$c/." "$t/cov/"
  a=$(vh frames "$t/cov" --covers --out "$t/cov/c1" 2>&1); rc=$?
  python3 - "$t/cov/audio/timeline.zh.json" <<'PY'
import json, sys
p = sys.argv[1]; tl = json.load(open(p, encoding="utf-8"))
for s in tl["segments"]:
    s["start"] = round(s["start"] + 0.4, 3); s["end"] = round(s["end"] + 0.4, 3)
    for w in s.get("words", []): w["start"] = round(w["start"] + 0.4, 3); w["end"] = round(w["end"] + 0.4, 3)
tl["duration"] = round(tl["duration"] + 0.4, 3)
json.dump(tl, open(p, "w", encoding="utf-8"), ensure_ascii=False)
PY
  b=$(vh frames "$t/cov" --covers --out "$t/cov/c2" 2>&1)
  t1=$(printf '%s' "$a" | sed -n 's/.*(cover A at \([0-9.]*\) s.*/\1/p'); t2=$(printf '%s' "$b" | sed -n 's/.*(cover A at \([0-9.]*\) s.*/\1/p')
  same=1; if command -v ffmpeg >/dev/null; then
    p=$(ffmpeg -v info -nostdin -i "$t/cov/c1/A.png" -i "$t/cov/c2/A.png" -lavfi psnr -f null - 2>&1 | sed -n 's/.*average:\([0-9.inf]*\).*/\1/p')
    python3 -c "import sys; v = sys.argv[1]; sys.exit(0 if v == 'inf' or float(v or 0) >= 30 else 1)" "$p" || same=0
  fi
  if [ -s "$t/cov/c1/A.png" ] && [ -n "$t1" ] && python3 -c "import sys; sys.exit(0 if abs(float(sys.argv[2]) - float(sys.argv[1]) - 0.4) < 0.002 else 1)" "$t1" "$t2" && [ $same = 1 ]
  then ok "covers: drawn into out/covers by cue; a longer opening moves the cover with the narration (+0.4 s) to the same picture"
  else bad "covers on the canvas-film template (exit $rc; $t1 → $t2, psnr ${p:-}): $(printf '%s' "$a$b" | tail -c 600)"; fi
  # --no-title: the same cover without its title (a clean background): the rows above the title's band are the same picture
  # (PSNR ≥ 40 dB; a second page need not rasterise byte for byte, as GitHub's macOS runner showed), the title's rows differ. --ratios: each ratio a crop at its own size (short side 1080 at --dpr 1), and a ratio that is
  # not one stops before any browser. A page whose cover(id) takes no options (an engine copied before) is not passed off
  # as clean. s.cover: a shot that paints a mark when s.cover is set leaves the film's frames byte for byte the template's
  # (at the cover's own t too), and the mark is in the cover, titled or clean
  a=$(vh frames "$c" --covers --out "$t/cnt" 2>&1); b=$(vh frames "$c" --covers --no-title --out "$t/cnt" 2>&1); rc=$?
  if ! command -v ffmpeg >/dev/null; then skip "covers --no-title compared with the titled cover" "no ffmpeg"
  elif [ -s "$t/cnt/A.png" ] && [ -s "$t/cnt/A-clean.png" ] && printf '%s' "$b" | grep -q '(cover A at [0-9.]* s, no title)' && python3 - "$t/cnt/A.png" "$t/cnt/A-clean.png" <<'PY'
import re, struct, subprocess, sys
def psnr(y, h):   # the two covers on rows y..y+h (two pages, so the same picture to within rasterising, not always byte for byte)
    f = f"[0:v]crop=iw:{h}:0:{y}[a];[1:v]crop=iw:{h}:0:{y}[b];[a][b]psnr"
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", sys.argv[1], "-i", sys.argv[2], "-filter_complex", f, "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"average:(inf|[0-9.]+)", r.stderr)
    return None if r.returncode or not m else float(m.group(1))   # a failed or unread comparison is no comparison
hs = [struct.unpack(">I", open(p, "rb").read()[20:24])[0] for p in sys.argv[1:3]]
top, band = psnr(0, 700), psnr(880, 120)
sys.exit(0 if hs == [1080, 1080] and top is not None and band is not None and top >= 40 and band < 30 else 1)
PY
  then ok "covers --no-title: the cover without its title, the same picture above the title's band, <id>-clean.png"
  else bad "covers --no-title (exit $rc): $(printf '%s' "$a$b" | tail -c 600)"; fi
  a=$(vh frames "$c" --covers --ratios 9:16,3:4,4:3 --out "$t/crat" 2>&1); rc=$?
  [ $rc = 1 ] && printf '%s' "$a" | grep -q 'fonts this machine does not have' && ! printf '%s\n' "$a" | grep -q '^  cover A' && rc=0
  b=$(vh frames "$c" --covers --ratios 9-16 2>&1); rc2=$?
  if [ $rc = 0 ] && [ $rc2 = 2 ] && printf '%s' "$b" | grep -q 'write them as 9:16' && printf '%s' "$a" | grep -q '9:16 1080x1920: a crop of the 1920x1080 picture' \
    && python3 - "$t/crat" <<'PY'
import struct, sys
size = lambda f: struct.unpack(">II", open(f"{sys.argv[1]}/{f}", "rb").read()[16:24])
sys.exit(0 if (size("A-9x16.png"), size("A-3x4.png"), size("A-4x3.png")) == ((1080, 1920), (1080, 1440), (1440, 1080)) else 1)
PY
  then ok "covers --ratios: each ratio a crop of the cover at its own size (9:16 1080x1920, 3:4, 4:3), said to be a crop; a malformed ratio exits 2"
  else bad "covers --ratios (exit $rc / $rc2): $(printf '%s' "$a$b" | tail -c 600)"; fi
  mkdir "$t/cold" && cp -R "$c/." "$t/cold/" && sed 's/cover(id, o) { return cover(id, o || {}); }/cover(id) { cover(id); }/' "$c/src/90-main.js" > "$t/cold/src/90-main.js"
  a=$(vh frames "$t/cold" --covers --no-title --out "$t/cold/o" 2>&1); rc=$?
  case "$rc:$a" in 1:*"cover A: the page drew its cover without saying it left the title out"*) [ ! -e "$t/cold/o/A-clean.png" ] && ok "covers --no-title: a cover(id) that takes no options is named, not passed off as clean" || bad "covers --no-title on an old cover(id) still wrote a clean cover" ;;
    *) bad "covers --no-title on an old cover(id) (exit $rc): $(printf '%s' "$a" | tail -c 500)" ;; esac
  mkdir "$t/cid" && cp -R "$c/." "$t/cid/" && cat >> "$t/cid/src/50-shots.js" <<'JS'
for (const S of SHOTS) { const d = S.draw; S.draw = (t, s) => { d(t, s); if (s.cover === "A") rect(-200, -200, 400, 400, { fill: "#FF00FF" }); }; }
JS
  ct=$(vh frames "$c" --covers --out "$t/cid/x" 2>&1 | sed -n 's/.*(cover A at \([0-9.]*\) s.*/\1/p' | head -1)
  vh frames "$c" --at "4.9,${ct:-10}" --out "$t/cid/f0" >/dev/null 2>&1; vh frames "$t/cid" --at "4.9,${ct:-10}" --out "$t/cid/f1" >/dev/null 2>&1
  vh frames "$t/cid" --covers --out "$t/cid/c" >/dev/null 2>&1; vh frames "$t/cid" --covers --no-title --out "$t/cid/c" >/dev/null 2>&1
  n0=$(find "$t/cid/f0" -name '*.png' 2>/dev/null | wc -l | tr -d ' '); same=1
  for f in "$t/cid/f0"/*.png; do cmp -s "$f" "$t/cid/f1/${f##*/}" || same=0; done
  if [ "$n0" = 2 ] && [ $same = 1 ] && python3 - "$t/cid/c/A.png" "$t/cid/c/A-clean.png" "$t/cid/f1" <<'PY'
import glob, struct, sys, zlib
def first_pixel(p):   # the top-left pixel: row 0's first pixel is stored as it is under every PNG filter
    d = open(p, "rb").read(); i, z = 8, b""
    while i < len(d):
        n, k = struct.unpack(">I4s", d[i:i + 8])
        if k == b"IDAT": z += d[i + 8:i + 8 + n]
        i += 12 + n
    return tuple(zlib.decompress(z)[1:4])
m = lambda p: first_pixel(p) == (255, 0, 255)
sys.exit(0 if m(sys.argv[1]) and m(sys.argv[2]) and not any(m(f) for f in glob.glob(sys.argv[3] + "/*.png")) else 1)
PY
  then ok "s.cover: a shot sees the cover's id only while a cover is drawn; the film's frames stay the template's, byte for byte (at the cover's t too)"
  else bad "s.cover on the canvas-film template (frames $n0, same $same, cover at ${ct:-?} s)"; fi
  # the default title for a ratio is laid out at the size txt() draws (never under FILM.minText): with an 80 px floor, a
  # 20-character title that would need 48 px in 9:16 is broken onto two lines at 80 px instead of running off both sides;
  # one that cannot fit even so (a word wider than the cover) stops ready, naming the cover and the ratio
  mkdir "$t/cmt" && cp -R "$c/." "$t/cmt/" && cat >> "$t/cmt/src/50-shots.js" <<'JS'
FILM.minText = 80;
COVERS.length = 0;
COVERS.push({ id: "L", at: "@a2:第二张+0.6", title: { text: ["二十个字的标题二十个字的标题二十个字的"], size: 80, x: 960, y: 1000, align: "center" }, ratios: { "3:4": {} } });
JS
  # (a browser that stops painting is a stall of the machine, not of the page: frames says so at --frame-timeout and the run
  # is tried once more, said in the line; each run is reported on its own)
  a=$(vh frames "$t/cmt" --covers --ratios 9:16,3:4 --frame-timeout 60 --out "$t/cmt/o" 2>&1); rc=$?; again=""
  case "$rc:$a" in 2:*"(--frame-timeout)"*|2:*"the page does not answer"*) again=" (tried again: $(printf '%s\n' "$a" | tail -1))"; a=$(vh frames "$t/cmt" --covers --ratios 9:16,3:4 --frame-timeout 60 --out "$t/cmt/o" 2>&1); rc=$? ;; esac
  [ $rc = 1 ] && printf '%s' "$a" | grep -q 'fonts this machine does not have' && ! printf '%s\n' "$a" | grep -q '^  cover L' && rc=0
  mkdir "$t/cmt2" && cp -R "$t/cmt/." "$t/cmt2/" && echo 'COVERS[0].title.text = ["Supercalifragilisticexpialidocious-and-more"]; COVERS[0].title.size = 60;' >> "$t/cmt2/src/50-shots.js"
  b=$(vh frames "$t/cmt2" --at 1 --out "$t/cmt2/o" 2>&1); rc2=$?
  if [ $rc = 0 ] && [ "$(printf '%s\n' "$a" | grep -c 're-set for it on 2 lines')" = 2 ] && [ $rc2 = 2 ] \
    && printf '%s' "$b" | grep -q 'cover L (3:4): the cover.s title does not fit 1080 x 1440 at 80 px or more (FILM.minText).*give it ratios\["3:4"\].title'
  then ok "covers --ratios: the default title is laid out at the size drawn (FILM.minText), broken onto more lines when too wide; one that cannot fit stops ready$again"
  else bad "covers --ratios default title under the text floor: the covers (exit $rc$again): $(printf '%s' "$a" | tail -c 500) | the title that cannot fit (exit $rc2): $(printf '%s' "$b" | tail -c 400)"; fi
  # a page whose size is only in window.film (1080x1920, its HTML says nothing): the drawing ratio comes from that size, so
  # its 4:3 crop (1080x810) is drawn at 1.333x and not scaled up from 1x
  mkdir "$t/ctall" && cat > "$t/ctall/film.html" <<'HTML'
<!doctype html><html><head><style>html, body { margin: 0; background: #224; }</style></head><body><script>
window.film = { width: 1080, height: 1920, duration: 2, frame() {}, covers: [{ id: "A", t: 0 }],
  cover(id, o) { return o && o.ratio === "4:3" ? { id, t: 0, title: false, crop: [0, 555, 1080, 810], size: [1440, 1080] } : { id, t: 0, title: false }; } };
</script></body></html>
HTML
  a=$(vh frames "$t/ctall" --covers --ratios 4:3 --out "$t/ctall/o" 2>&1); rc=$?
  if [ $rc = 0 ] && printf '%s' "$a" | grep -q '1080x1920 (drawn @1.333x for the crops)' && ! printf '%s' "$a" | grep -q 'scaled up' \
    && python3 -c "import struct, sys; sys.exit(0 if struct.unpack('>II', open(sys.argv[1], 'rb').read()[16:24]) == (1440, 1080) else 1)" "$t/ctall/o/A-4x3.png"
  then ok "covers --ratios: the drawing ratio follows the page's own size (window.film.width and height), not its HTML's"
  else bad "covers --ratios on a page sized by window.film (exit $rc): $(printf '%s' "$a" | tail -c 600)"; fi
  mkdir "$t/chp" && cp -R "$c/." "$t/chp/"
  a=$(vh cues "$t/chp" --chapters 2>&1); rc=$?
  if [ $rc = 0 ] && printf '%s' "$a" | grep -q '^  0:00 挂在字上' && printf '%s' "$a" | grep -q '^  0:11 翻一页' && printf '%s' "$a" | grep -q 'at least three'; then ok "cues --chapters: the engine's chapters as a description's list, half a second early, with YouTube's conditions"
  else bad "cues --chapters: exit $rc: $(printf '%s' "$a" | tail -c 500)"; fi
  # bin/vh fonts check on a font with only "A" and "B" (tools/film/fixture/fonts/ab.ttf): from 1 s the canvas draws a "C" and
  # U+10FFFD, the DOM a "D"; before that everything is in the font. render says the same, without failing
  a=$(vh fonts check "$ROOT/tools/film/fixture/glyphs.html" --out "$t/fo" 2>&1); rc=$?
  b=$(vh fonts check "$ROOT/tools/film/fixture/glyphs.html" --at 0.5 --out "$t/fo" 2>&1); rc2=$?
  if [ $rc = 1 ] && printf '%s' "$a" | grep -q 'not in "Fix AB", drawn in .*: C D' && printf '%s' "$a" | grep -q 'no font on this machine has 1 character.*U+10FFFD' \
    && [ $rc2 = 0 ] && printf '%s' "$b" | grep -q 'all in "Fix AB"'
  then ok "fonts check: characters a font lacks are named, on a canvas and in the DOM (another font draws them, or none: exit 1); none, exit 0"
  else bad "fonts check on its fixture: exit $rc / $rc2: $(printf '%s' "$a$b" | tail -c 900)"; fi
  if command -v ffmpeg >/dev/null; then
    a=$(vh render "$ROOT/tools/film/fixture/glyphs.html" --workers 2 --gop 30 --out "$t/fo/g.mp4" 2>&1); rc=$?
    [ $rc = 0 ] && printf '%s' "$a" | grep -q '2 workers' && printf '%s' "$a" | grep -q 'glyphs: characters not drawn in the font' && printf '%s' "$a" | grep -q 'C D' \
      && ok "render: says which characters were drawn in another font, or in none (two workers' findings as one), and still renders" \
      || bad "render on the glyph fixture: exit $rc: $(printf '%s' "$a" | tail -c 700)"
  fi
  if command -v uv >/dev/null; then
    a=$(vh fonts subset "$ROOT/tools/film/fixture/glyphs.html" --font "$ROOT/tools/film/fixture/fonts/ab.ttf" --family "Fix AB" --out "$t/fs" 2>&1); rc=$?
    [ $rc = 0 ] && [ -s "$t/fs/OVHFixtureAB-Regular.subset.woff2" ] && printf '%s' "$a" | grep -q 'src: url(".*OVHFixtureAB-Regular.subset.woff2") format("woff2")' \
      && ok "fonts subset: a font cut to the project's characters as woff2, with its src line" || bad "fonts subset: exit $rc: $(printf '%s' "$a" | tail -c 600)"
    a=$(vh fonts list --all 2>&1); rc=$?
    [ $rc = 0 ] && printf '%s' "$a" | tail -1 | grep -q '^fonts: [0-9]* face(s)' && ok "fonts list: the faces on this machine by their local() names" || bad "fonts list: exit $rc: $(printf '%s' "$a" | tail -c 400)"
  else skip "fonts subset and list" "no uv"; fi
  mkdir "$t/cfr" && cp -R "$c/." "$t/cfr/"
  a=$(vh readcheck "$t/cfr" 2>&1); rc=$?
  if [ $rc = 0 ] && [ ! -e "$t/cfr/out/texts.json" ] && printf '%s' "$a" | grep -q 'subtitle'; then ok "canvas-film: readcheck judges the page's reads and captions using a private temporary snapshot"
  else bad "readcheck on a canvas-film project (exit $rc): $(printf '%s' "$a" | tail -c 800)"; fi
  # a HUD card over the cut S01 -> S02 (a settle), drawn by both shots with overlay: true, is one read over its whole time on
  # screen (4.4-8.6 s), not two pieces cut at the shots (the second 1.46 s, a false FAIL); an ordinary read still keeps to its
  # shot (S02's title: from the end of the settle in, 7.138 s, to the next cut, 12.283 s); textcheck samples the card on
  # both sides of the cut and finds it at each
  mkdir "$t/cfh" && cp -R "$c/." "$t/cfh/" && cat >> "$t/cfh/src/50-shots.js" <<'JS'
for (const S of SHOTS.slice(0, 2)) { const d = S.draw; S.draw = (t, s) => { d(t, s); label(t, 4.0, "跨镜头的字卡", 1300, 250, { size: 48, until: 9.0, overlay: true }); }; }
JS
  a=$(vh readcheck "$t/cfh" --out "$t/cfh-texts.json" 2>&1); rc=$?
  b=$(vh textcheck "$t/cfh" --out "$t/cfh-tc" 2>&1); rc2=$?
  if [ $rc = 0 ] && [ $rc2 = 0 ] && python3 - "$t/cfh-texts.json" "$t/cfh-tc/textcheck.json" <<'PY'
import json, sys
texts = json.load(open(sys.argv[1], encoding="utf-8"))
span = lambda s: [(x["start"], x["end"]) for x in texts if x["text"] == s]
r = next(r for r in json.load(open(sys.argv[2], encoding="utf-8"))["reads"] if r["text"] == "跨镜头的字卡")
ts = [q["t"] for q in r["samples"] if q["found"]]
sys.exit(0 if span("跨镜头的字卡") == [(4.4, 8.6)] and span("说到哪张，哪张落下") == [(7.138, 12.283)]
         and len(ts) == len(r["samples"]) and min(ts) < 6.638 < max(ts) else 1)
PY
  then ok "canvas-film: an overlay read spans the cut it is drawn across (readcheck), ordinary reads keep to their shot, and textcheck samples it on both sides"
  else bad "canvas-film overlay read (exit $rc / $rc2): $(printf '%s' "$a$b" | tail -c 800)"; fi
  # A too-short read still exports successfully; checking it fails. Outputs are independent, including concurrent runs,
  # and an existing manual snapshot is never replaced without --force. The output folder must not change the BRIEF's pace,
  # nor the check the export hint names (a file outside the project: --pace and a quoted path). A page with no texts is
  # nothing to check (2, not the 1 of a text under the floor); no browser names the remedies, not bin/vh readcheck itself.
  a=$(python3 - "$VH_BASH" "$ROOT" "$t" <<'PYREAD'
import json, pathlib, shlex, subprocess, sys
bash, root, tmp = sys.argv[1:]
p = pathlib.Path(tmp) / "readcheck args"; p.mkdir()
(p / "film.html").write_text('<!doctype html><head><meta name="viewport" content="width=320,height=180"></head><script>'
    'window.film={duration:4,frame(){},texts:[{id:"label",text:"CLAUDE.md router",start:0,end:1.6},'
    '{id:"short",text:"Too short",start:2,end:2.3}]};</script>', encoding="utf-8")
(p / "BRIEF.md").write_text("# BRIEF\n- Pace: relaxed\n", encoding="utf-8")
(p / "out").mkdir(); default = p / "out" / "texts.json"
manual = '[{"text":"hand edited","start":0,"end":3}]'; default.write_text(manual, encoding="utf-8")
cmd = [bash, str(pathlib.Path(root) / "bin" / "vh"), "readcheck"]
def run(args, code):
    r = subprocess.run(cmd + list(map(str, args)), capture_output=True, text=True)
    assert r.returncode == code, (args, r.returncode, r.stdout, r.stderr)
    return r.stdout + r.stderr
def exported(file):
    assert [i["id"] for i in json.loads(file.read_text(encoding="utf-8"))] == ["label", "short"], file
out = run([p], 1)
assert "WARN label" in out and "FAIL short" in out and "Pace in" in out, out
assert default.read_text(encoding="utf-8") == manual
run([p, "--export"], 2)
assert default.read_text(encoding="utf-8") == manual
out = run(["--export", p, "--force"], 0); exported(default)
assert "exported; check it with" in out and "FAIL short" not in out and "--pace" not in out, out
outside = pathlib.Path(tmp) / "outside export.json"
out = run([p, "--export", "--out", outside], 0); exported(outside)
hint = out.split("check it with ")[1].strip()
assert hint == "bin/vh readcheck " + shlex.quote(str(outside)) + " --pace relaxed", out
out = run(shlex.split(hint)[2:], 1)
assert "pace relaxed, --pace" in out and "WARN label" in out, out
r = subprocess.run([sys.executable, str(pathlib.Path(root) / "tools" / "readcheck.py"), "--browser", "", str(p)], capture_output=True, text=True)
assert r.returncode == 2 and "CHROME_PATH" in r.stderr and "run it as bin/vh" not in r.stderr, (r.returncode, r.stderr)
bare = pathlib.Path(tmp) / "readcheck no texts"; bare.mkdir()
(bare / "film.html").write_text('<!doctype html><head><meta name="viewport" content="width=320,height=180"></head><script>'
    'window.film={duration:2,frame(){}};</script>', encoding="utf-8")
out = run([bare], 2)
assert "gives no window.film.texts" in out and "NOT CHECKED" in out, out
saved = default.read_bytes()
custom = pathlib.Path(tmp) / "outside project.json"
out = run(["--out", custom, p], 1); exported(custom)
assert "Pace in" in out and "WARN label" in out, out
out = run([p, "--out", custom], 2)
assert "exists" in out and "--force" in out, out
run([p / "film.html", "--out", custom, "--force", "--pace", "brisk"], 1)
folder = pathlib.Path(tmp) / "export folder"; folder.mkdir()
run(["--out=" + str(folder), "--export", p], 0); exported(folder / "texts.json")
invalid = p / "invalid.json"
run([p, "--export", "--out", invalid, "--pace", "fast"], 2)
assert not invalid.exists()
# Two distinct outputs stay distinct; two writers to the same output have one success and one refusal (exclusive create).
for names, codes in ((["one.json", "two.json"], [0, 0]), (["shared.json", "shared.json"], [0, 2])):
    procs = [(p / name, subprocess.Popen(cmd + [str(p), "--export", "--out", str(p / name)],
             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)) for name in names]
    got = []
    for f, proc in procs:
        stdout, stderr = proc.communicate(); got.append(proc.returncode)
        assert proc.returncode in codes, (stdout, stderr)
        exported(f)
    assert sorted(got) == codes, got
assert default.read_bytes() == saved
print("canvas-film readcheck: export/check, custom outputs, original Pace (in the export hint too), --force, concurrent writers, a page with no texts, no browser")
PYREAD
  ); rc=$?
  if [ $rc = 0 ]; then ok "$a"; else bad "readcheck export/output regression: $a"; fi
  if command -v uv >/dev/null; then
    if python3 "$ROOT/tools/test_film_shots.py"; then ok "film shots: resolved times, real frames, source precedence and errors"; else bad "film shots"; fi
  else skip "film shots" "needs uv (Pillow for storyboard/rhythm)"; fi
  # Ctrl-C while a page is loading: the browser's profile folder goes too (Node would otherwise die without cleaning up)
  printf '%s\n' '<!doctype html><title>hang</title><script>window.film = { duration: 2, ready: new Promise(() => {}), frame() {} };</script>' > "$t/hang.html"
  mkdir -p "$t/tmpd"
  TMPDIR="$t/tmpd" "$VH_BASH" "$ROOT/bin/vh" frames "$t/hang.html" --at 1 --out "$t/hang-out" >/dev/null 2>&1 & pid=$!
  for _ in $(seq 1 120); do ls -d "$t/tmpd"/vh-textcheck-* >/dev/null 2>&1 && break; sleep 0.25; done
  seen=$(ls -d "$t/tmpd"/vh-textcheck-* 2>/dev/null | wc -l | tr -d ' ')   # a browser was up: otherwise this tests nothing
  sleep 1; kill -INT "$pid" 2>/dev/null; wait "$pid"; rc=$?; sleep 1
  left=$(ls -d "$t/tmpd"/vh-textcheck-* 2>/dev/null | wc -l | tr -d ' '); alive=$(pgrep -f "$t/tmpd" | wc -l | tr -d ' ')
  [ "$seen" -ge 1 ] && [ "$rc" = 130 ] && [ "$left" = 0 ] && [ "$alive" = 0 ] && ok "frames stopped with Ctrl-C ends (exit 130), leaving no browser profile and no Chrome behind" \
    || bad "frames after Ctrl-C: a browser seen $seen, exit $rc, $left profile folder(s) and $alive Chrome process(es) left"
  pkill -KILL -f "$t/tmpd" 2>/dev/null
  # the same Ctrl-C sent to the whole process group, as a terminal sends it, while readcheck or rhythm waits for the page:
  # exit 130, no traceback, no profile and no Chrome left (Python killed node 0.25 s in; uv run could exit 2 instead)
  mkdir -p "$t/hangp" "$t/tmpc" && cp "$t/hang.html" "$t/hangp/film.html"
  for c in readcheck rhythm; do
    if [ $c = rhythm ] && ! command -v uv >/dev/null; then skip "rhythm stopped with Ctrl-C" "needs uv"; continue; fi
    a=$(python3 - "$t/tmpc" "$VH_BASH" "$ROOT/bin/vh" $c "$t/hangp" <<'PY'
import glob, os, signal, subprocess, sys, time
tmp, cmd = sys.argv[1], sys.argv[2:]
p = subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=dict(os.environ, TMPDIR=tmp))
for _ in range(120):
    if glob.glob(f"{tmp}/vh-textcheck-*") or p.poll() is not None: break
    time.sleep(0.25)
seen = len(glob.glob(f"{tmp}/vh-textcheck-*")); time.sleep(1)
try: os.killpg(p.pid, signal.SIGINT)
except OSError: pass   # it ended before the Ctrl-C: the exit code below says how
err = p.communicate(timeout=30)[1]; time.sleep(0.5)
print(seen, p.returncode, len(glob.glob(f"{tmp}/vh-textcheck-*")), "Traceback" in err, repr(err.strip()[-200:]))
PY
)
    alive=$(pgrep -f "$t/tmpc" | wc -l | tr -d ' ')
    want=130; [ $c = readcheck ] || want=-2   # rhythm runs through uv (on_ctrl_c): bin/vh ends by SIGINT itself
    case "$alive $a" in "0 1 $want 0 False "*) ok "$c stopped with Ctrl-C (to the process group) ends with $want and no traceback, leaving no browser profile and no Chrome" ;;
      *) bad "$c after Ctrl-C (Chrome left, browsers seen, exit, profiles left, traceback): $alive $a" ;; esac
    pkill -KILL -f "$t/tmpc" 2>/dev/null
  done
  # Ctrl-C while the profile folder is being removed (a preload sends SIGINT as the removal starts): the folder still goes
  # whole, and the Ctrl-C still ends the process (before, the listeners were gone by then and node died half way through)
  printf '%s\n' 'import fs from "node:fs"; const rm = fs.rmSync; let sent = false;' \
    'fs.rmSync = function (p, ...r) { if (!sent && /vh-textcheck-/.test(String(p))) { sent = true; process.kill(process.pid, "SIGINT"); } return rm.call(this, p, ...r); };' > "$t/rmsig.mjs"
  printf '%s\n' '<!doctype html><canvas id="c" width="64" height="36"></canvas><script>const x = document.getElementById("c").getContext("2d");' \
    'window.film = { duration: 2, frame() { x.fillStyle = "#345"; x.fillRect(0, 0, 64, 36); } };</script>' > "$t/one.html"
  mkdir -p "$t/tmpr"
  TMPDIR="$t/tmpr" NODE_OPTIONS="--import=$t/rmsig.mjs" "$VH_BASH" "$ROOT/bin/vh" frames "$t/one.html" --at 0.5 --out "$t/one-out" >/dev/null 2>&1; rc=$?; sleep 0.5
  left=$(ls -d "$t/tmpr"/vh-textcheck-* 2>/dev/null | wc -l | tr -d ' '); alive=$(pgrep -f "$t/tmpr" | wc -l | tr -d ' ')
  [ "$rc" = 130 ] && [ "$left" = 0 ] && [ "$alive" = 0 ] && ok "Ctrl-C while the browser profile is being removed: the folder goes whole, then the process ends (exit 130)" \
    || bad "Ctrl-C during the profile's removal: exit $rc, $left profile folder(s) and $alive Chrome process(es) left"
  pkill -KILL -f "$t/tmpr" 2>/dev/null
  # Ctrl-C after the last browser closed (determinism comparing its frames, synchronous work): the process ends at once,
  # not after the comparisons (a signal listener left in place would hold the signal until the event loop turned again)
  printf '%s\n' '<!doctype html><canvas id="c" width="64" height="36"></canvas><script>const x = document.getElementById("c").getContext("2d");' \
    'window.film = { duration: 2, frame(t) { x.fillStyle = `rgb(${Math.floor(Math.random() * 255)},90,${Math.floor(t * 100)})`; x.fillRect(0, 0, 64, 36); } };</script>' > "$t/rnd.html"
  "$VH_BASH" "$ROOT/bin/vh" determinism "$t/rnd.html" --at "$(seq -s, 0.02 0.02 1.9 | sed 's/,$//')" --out "$t/rnd-out" >/dev/null 2>&1 & pid=$!
  seen=0; for _ in $(seq 1 600); do if pgrep -P "$pid" -f psnr >/dev/null 2>&1; then seen=1; break; fi; kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done
  if [ $seen = 1 ]; then kill -INT "$pid" 2>/dev/null; wait "$pid"; rc=$?
    [ "$rc" = 130 ] && ok "determinism stopped with Ctrl-C while comparing ends at once (exit 130)" || bad "determinism after Ctrl-C while comparing: exit $rc (it went on)"
  else wait "$pid" 2>/dev/null; skip "Ctrl-C while determinism compares" "the comparisons were not caught running"; fi
  rm -rf "$t"
}

# bin/vh timeline (the narration timeline's checks) and bin/vh remap, and the refusal in bin/vh captions
timeline_checks() {
  local t a rc
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")
  a=$(vh timeline showcase/02-short-leo-doppler zh 2>&1); rc=$?
  [ $rc = 0 ] && printf '%s' "$a" | grep -q "timeline: sound" && ok "timeline: showcase 02's narration is sound" || bad "timeline on showcase 02: exit $rc: $a"
  mkdir -p "$t/p/audio"
  python3 - "$t/p/audio/timeline.zh.json" <<'PY'
import json, sys
tl = json.load(open("showcase/02-short-leo-doppler/audio/timeline.zh.json", encoding="utf-8"))
s = tl["segments"][1]; s["words"][2]["start"] = s["words"][1]["start"] - 0.5   # a word time out of order
s = tl["segments"][3]; s["words"][0]["w"] = "宾果"                               # an aligner that spelled a word its own way
json.dump(tl, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
  a=$(vh timeline "$t/p" zh 2>&1); rc=$?
  case "$rc:$a" in 1:*"out of order"*"the words read"*) ok "timeline: a word time out of order and a word spelled differently from the text are problems (exit 1)" ;;
    *) bad "timeline on a broken timeline: exit $rc: $a" ;; esac
  a=$(vh captions "$t/p" zh 2>&1); rc=$?
  b=$(vh captions "$t/p" zh --skip-lint 2>&1); rc2=$?
  c=$(vh captions "$t/p" zh --skip-lint --media-end 30 2>&1); rc3=$?
  if [ $rc = 1 ] && printf '%s' "$a" | grep -q "timed wrong" && [ $rc2 = 0 ] && [ $rc3 = 0 ] && [ -s "$t/p/audio/captions.json" ]; then ok "captions: refuses a timeline that fails its checks, and goes on with --skip-lint (before or after --media-end)"
  else bad "captions on a broken timeline: exit $rc ($a) / with --skip-lint exit $rc2 ($b) / --skip-lint --media-end exit $rc3 ($c)"; fi
  # captions at word boundaries (jieba through uv): a long line without a comma is cut between words, one-line cards never
  # cross a sentence end, and the break table starts a card at its phrase
  if command -v uv >/dev/null && uv run -q --no-project --with jieba python -c "import jieba" >/dev/null 2>&1; then
    mkdir -p "$t/cw/audio" && printf '# BRIEF\n' > "$t/cw/BRIEF.md"
    python3 - "$t/cw/audio/timeline.zh.json" <<'PY'
import json, sys
def line(i, t0, text):
    cs = [c for c in text if c not in "，。"]; ws, t = [], t0
    for c in cs: ws.append({"w": c, "start": round(t, 3), "end": round(t + 0.2, 3)}); t += 0.2
    return {"id": i, "zh": text, "start": t0, "end": round(t, 3), "words": ws}
segs = [line("c1", 0.0, "今天我们一起来看看这台机器到底是怎么工作的"), line("c2", 6.0, "说到第一张，卡片落下。说到第二张，第二张跟上。")]
json.dump({"lang": "zh", "duration": 12.0, "segments": segs}, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
    printf '["卡片落下"]\n' > "$t/cw/audio/capbreaks.json"
    a=$(vh captions "$t/cw" zh --cards 2>&1); rc=$?
    if [ $rc = 0 ] && printf '%s' "$a" | grep -q 'word boundaries by jieba' && PYTHONWARNINGS=ignore uv run -q --no-project --with jieba python - "$t/cw/audio/captions.json" <<'PY'
import json, logging, sys, jieba
jieba.setLogLevel(logging.ERROR)
cards = json.load(open(sys.argv[1], encoding="utf-8"))
c1 = [c["zh"][0] for c in cards if c["id"] == "c1"]; c2 = [c["zh"][0] for c in cards if c["id"] == "c2"]
text = "今天我们一起来看看这台机器到底是怎么工作的"
bounds, pos = set(), 0
for w in jieba.lcut(text): pos += len(w); bounds.add(pos)
cuts, pos = [], 0
for c in c1[:-1]: pos += len(c); cuts.append(pos)
ok = len(c1) >= 2 and "".join(c1) == text and all(x in bounds for x in cuts)
ok = ok and not any("落下" in c and "第二张" in c for c in c2) and any(c.startswith("卡片落下") for c in c2)
sys.exit(0 if ok else 1)
PY
    then ok "captions --cards: cut between words (jieba), never across a sentence end, a card starting at the break table's phrase"
    else bad "captions --cards (exit $rc): $(printf '%s' "$a" | tail -c 500) $(cat "$t/cw/audio/captions.zh.srt" 2>/dev/null | tr '\n' '|' | tail -c 400)"; fi
    # numbers, times and links stay whole at a narrow width (jieba cuts them at their , and :)
    if a=$(PYTHONWARNINGS=ignore uv run -q --no-project --with jieba python - "$ROOT/tools/audio" 2>&1 <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import capbreak, captions
bad = []
for text, w, keep in (("价格从1,000,000元涨到2,500,000元", 8, ("1,000,000", "2,500,000")), ("价格从1,000,000元涨到", 6, ("1,000,000",)),
                      ("会议定在12:30开始，别迟到", 6, ("12:30",)), ("在12:30:45开始", 6, ("12:30:45",)),
                      ("网址是https://example.com/a/b，记下来。", 8, ("https://example.com/a/b",)), ("网址是https://a.example.com:8080/x/y，记下", 6, ("https://a.example.com:8080/x/y",))):
    for got in ([r for _, r in capbreak.pieces(text, w, True)], captions.wrap_zh(text, w)):
        if not all(any(k in g for g in got) for k in keep): bad.append(f"{text} at {w}: {got}")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
    ); then ok "captions: 2,500,000, 12:30 and a link stay whole at a narrow width, in cards and wrapped lines"
    else bad "captions split a number, a time or a link: $a"; fi
  else skip "captions at word boundaries" "no uv to bring jieba"; fi
  # cards in English stay within --en-max characters and end at . ! ?; half-width ? ! end a Chinese sentence; a card that
  # would start after the media end is left out, and no card ends before it starts
  mkdir -p "$t/ce/audio" "$t/ch/audio" && printf '# BRIEF\n' > "$t/ce/BRIEF.md" && cp "$t/ce/BRIEF.md" "$t/ch/BRIEF.md"
  python3 - "$t" <<'PY'
import json, re, sys
d = sys.argv[1]
def seg(i, lang, text, t0, dt):
    ws, t = [], t0
    for w in (re.findall(r"[A-Za-z0-9']+", text) if lang == "en" else [c for c in text if c.strip() and c not in "?!，。"]):
        ws.append({"w": w, "start": round(t, 3), "end": round(t + dt, 3)}); t += dt
    return {"id": i, lang: text, "start": t0, "end": round(t, 3), "words": ws}
en = "The quick brown fox jumps over the lazy dog and keeps on running. Version 3.5 is out! Is it fast? It is"
json.dump({"lang": "en", "duration": 30.0, "segments": [seg("e1", "en", en, 0.0, 0.3)]}, open(f"{d}/ce/audio/timeline.en.json", "w"))
json.dump({"lang": "zh", "duration": 25.0, "segments": [seg("h1", "zh", "真的吗?我不信!你再说一遍", 0.0, 0.25), seg("h2", "zh", "这一句在画面结束以后才开始", 20.0, 0.25)]},
          open(f"{d}/ch/audio/timeline.zh.json", "w"), ensure_ascii=False)
PY
  a=$(vh captions "$t/ce" en --cards 2>&1); rc=$?
  b=$(vh captions "$t/ch" zh --cards --media-end 19 2>&1); rc2=$?
  if [ $rc = 0 ] && [ $rc2 = 0 ] && printf '%s' "$b" | grep -q "left out, starts after the media end" && python3 - "$t" <<'PY'
import json, sys
d = sys.argv[1]
en = [c["en"][0] for c in json.load(open(f"{d}/ce/audio/captions.json"))]
zh = json.load(open(f"{d}/ch/audio/captions.json", encoding="utf-8"))
ok = all(len(c) <= 42 for c in en) and not any(". " in c or "! " in c or "? " in c for c in en) and "Version 3.5 is out!" in en
ok = ok and [c["zh"][0] for c in zh][:2] == ["真的吗?", "我不信!"] and all(c["id"] == "h1" and c["end"] > c["start"] for c in zh)
sys.exit(0 if ok else 1)
PY
  then ok "captions --cards: English within --en-max and cut at . ! ? (3.5 whole), half-width ? ! end a Chinese sentence, a card after the media end left out"
  else bad "captions --cards in English / half-width / media end (exit $rc, $rc2): $(printf '%s' "$a $b" | tail -c 400) $(head -c 600 "$t/ce/audio/captions.json" 2>/dev/null)"; fi
  # check: an SRT beside the video with an entry too short to read is listed (a warning, not a failure)
  if command -v ffmpeg >/dev/null; then
    mkdir -p "$t/sc" && ffmpeg -nostdin -v error -f lavfi -i color=c=0x303030:s=320x180:r=30:d=3 -pix_fmt yuv420p "$t/sc/film.mp4"
    printf '1\n00:00:00,500 --> 00:00:01,300\n这一句只亮了零点八秒\n\n2\n00:00:01,300 --> 00:00:03,200\n这句够长\n' > "$t/sc/film.zh.srt"
    a=$(vh check "$t/sc/film.mp4" 2>&1); rc=$?
    case "$a" in *"subtitles · film.zh.srt: 1 of 2 entries are shorter than it takes to read them"*"0.80 s, needs 1.80 s"*) ok "check lists subtitle entries too short to read, from the SRT beside the film" ;;
      *) bad "check on a short subtitle (rc $rc): $(printf '%s' "$a" | tail -c 500)" ;; esac
  fi
  python3 - "$t" <<'PY'
import json, sys
d = sys.argv[1]
line = lambda i, t0, text, ws: {"id": i, "text": text, "start": t0, "end": round(t0 + sum(w[1] for w in ws), 3), "words": [
    {"w": w, "start": round(t0 + sum(x[1] for x in ws[:k]), 3), "end": round(t0 + sum(x[1] for x in ws[:k + 1]), 3)} for k, (w, _) in enumerate(ws)]}
for name, gap in (("old", 0.5), ("new", 1.5)):   # the new take has 1 s more before the second line
    json.dump({"lang": "zh", "segments": [line("a", 0.0, "风吹过", [("风", 0.4), ("吹过", 1.1)]), line("b", 1.5 + gap, "纸飞走了", [("纸", 0.5), ("飞走了", 1.5)])]},
              open(f"{d}/{name}.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump([{"t": 0.2, "sfx": "wind"}, {"t": 2.6, "sfx": "paper", "gain_db": -6}, {"name": "x", "start": 1.8, "end": 4.5}], open(f"{d}/events.json", "w"))
PY
  a=$(vh remap "$t/events.json" --from "$t/old.json" --to "$t/new.json" 2>&1); rc=$?
  if [ $rc = 0 ] && python3 -c "import json, sys; e = json.load(open(sys.argv[1])); sys.exit(0 if (e[0]['t'], e[1]['t'], e[1]['gain_db'], e[2]['start'], e[2]['end']) == (0.2, 3.6, -6, 2.4, 5.5) else 1)" "$t/events.json" && [ -s "$t/events.json.bak" ]
  then ok "remap: seconds inside a line move with its words, in a gap in proportion, after the end with the last word; other numbers stay; the original kept as .bak"
  else bad "remap: exit $rc: $a $(cat "$t/events.json" 2>/dev/null)"; fi
  a=$(vh remap "$t/events.json" --from "$t/old.json" --to "$t/new.json" 2>&1); rc=$?
  [ $rc = 2 ] && printf '%s' "$a" | grep -q "is there already" && ok "remap: refuses to overwrite an earlier remap's .bak" || bad "remap with a .bak there: exit $rc: $a"
  python3 - "$t" <<'PY'
import json, sys
d = sys.argv[1]   # two lines that meet at 1.0 s; the new take puts 0.8 s between them
L = lambda i, a, b, t: {"id": i, "text": t, "start": a, "end": b}
json.dump({"segments": [L("a", 0, 1, "风"), L("b", 1, 2, "纸")]}, open(f"{d}/old2.json", "w"))
json.dump({"segments": [L("a", 0, 1, "风"), L("b", 1.8, 2.8, "纸")]}, open(f"{d}/new2.json", "w"))
json.dump([{"t": 0.9}, {"t": 1.1}, {"t": 1.6}], open(f"{d}/ev2.json", "w"))
PY
  a=$(vh remap "$t/ev2.json" --from "$t/old2.json" --to "$t/new2.json" --out "$t/ev2o.json" 2>&1); rc=$?
  if [ $rc = 0 ] && python3 -c "import json, sys; sys.exit(0 if [e['t'] for e in json.load(open(sys.argv[1]))] == [0.9, 1.9, 2.4] else 1)" "$t/ev2o.json"
  then ok "remap: where two lines met and a pause came between them, a time on the later line moves with it"
  else bad "remap across a new pause: exit $rc: $a $(cat "$t/ev2o.json" 2>/dev/null)"; fi
  if command -v uv >/dev/null; then   # an empty event list: no length to take from it
    printf '[]\n' > "$t/none.json"
    a=$(vh sfx place "$t/none.json" "$t/none.wav" 2>&1); rc=$?; b=$(vh sfx place "$t/none.json" "$t/none.wav" 2 2>&1)
    case "$rc:$a:$b" in 2:*"has no events"*"<duration_s>"*:*"0 events"*"2.00s"*) ok "sfx place: an empty event list asks for a duration, and with one writes a silent track" ;;
      *) bad "sfx place on an empty event list (exit $rc): $a / $b" ;; esac
    a=$(vh sfx place "$t/none.json" "$t/none.wav" 2s 2>&1); rc=$?
    case "$rc:$a" in 2:*"duration '2s' is not a number of seconds"*) case "$a" in *Traceback*) bad "sfx place with a duration 2s: a traceback: $a" ;; *) ok "sfx place: a duration that is not a number is said plainly (exit 2)" ;; esac ;;
      *) bad "sfx place with a duration 2s (exit $rc): $a" ;; esac
    # usage errors exit 2 (no command, a typo, place without its files, a missing event list, lib without a folder, an
    # audition value out of range), an event list that cannot become a track exits 1 (an unknown sound, a field out of range)
    printf '[{"t": 0.5, "sfx": "nosuch"}]' > "$t/unk.json"; printf '[{"t": 0.5, "sfx": "whoosh", "dur": 99}]' > "$t/far.json"; a=""
    b=$(vh sfx audition -h 2>/dev/null); rc=$?   # help is not an error: stdout, exit 0, as sfx -h; a bare audition is a one-line one
    case "$rc:$b" in 0:*"audition <name|all>"*) ;; *) a=" | sfx audition -h (exit $rc): $(printf '%s' "$b" | head -c 200)" ;; esac
    for c in "2|" "2|plcae" "2|place" "2|place|$t/unk.json" "2|place|$t/nope.json|$t/o.wav" "2|lib" "2|audition" "2|audition|whoosh|dur=99|--out|$t/au.wav" \
             "1|place|$t/unk.json|$t/o.wav" "1|place|$t/far.json|$t/o.wav"; do
      IFS='|' read -r -a cargs <<< "$c"
      b=$(vh sfx "${cargs[@]:1}" 2>&1); rc=$?
      case "$rc:$b" in *Traceback*) a="$a | sfx ${cargs[*]:1}: $b" ;; "${cargs[0]}:sfx"*) ;; *) a="$a | sfx ${cargs[*]:1} (exit $rc, want ${cargs[0]}): $(printf '%s' "$b" | tail -c 200)" ;; esac
    done
    [ -z "$a" ] && ok "sfx: help exits 0, usage errors exit 2, an event list that cannot become a track exits 1, each in a line and none a traceback" || bad "sfx exit codes:$a"
  fi
  rm -rf "$t"
}

# bin/vh pace on a synthetic take (22.05 kHz): tone-burst "syllables" with known onsets, lines at 4 to 7 a second, a long
# pause inside a line and one the script asks for, gaps too short and too long, an ASR start placed 0.12 s late, one line's
# end and the next one's start put at the same instant inside the first one's last syllable (an aligner did that), and a
# "……" line. Then ASRs that are further off, a line with no audio, and the refusals. Checked against the known syllables,
# not against the tool's own numbers
pace_checks() {
  local t p v a rc
  if ! command -v uv >/dev/null || ! command -v ffmpeg >/dev/null; then skip "pace" "needs uv and ffmpeg"; return; fi
  t=$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX"); p="$t/p"
  python3 - "$p/audio" <<'PY'
import json, math, struct, sys, wave
from pathlib import Path
a = Path(sys.argv[1]); a.mkdir(parents=True); SR = 22050
lines = [("a1", "一二三四五六七八，", 4.0, None, 0.05), ("a2", "九十百千万亿兆京。", 7.0, None, 1.6),    # id, text, per second,
         ("b1", "甲乙丙丁戊己庚辛壬癸。", 5.5, (5, 0.7), 0.4), ("b2", "好。", 3.0, None, 0.3),         # (after unit k, pause),
         ("b3", "子丑寅卯辰巳午未。", 5.0, (4, 0.6), 0.5), ("b4", "东南西北中发白。", 5.6, None, 0.0)]   # gap after the line
(a / "script.txt").write_text("@a1 一二三四五六七八，\n@a2 九十百千万亿兆京。\n\n@b1 甲乙丙丁戊己庚辛壬癸。\n@b2 好。\n"
                              "@b3 子丑寅卯<long pause>辰巳午未。\n@b3x ……\n@b4 东南西北中发白。\n", encoding="utf-8")
x, segs = [0.0] * int(0.4 * SR), []
for k, (sid, text, rate, pause, gap) in enumerate(lines):
    chars = [c for c in text if c not in "，。"]; burst = 0.75 / rate; words = []
    for j, c in enumerate(chars):
        t0, n, f0 = len(x) / SR, int(burst * SR), 140 + 15 * ((j * 7 + k * 3) % 5)
        x += [0.25 * math.sin(math.pi * i / n) ** 0.5 * (math.sin(2 * math.pi * f0 * i / SR) + 0.5 * math.sin(4 * math.pi * f0 * i / SR)) for i in range(n)]
        words.append({"w": c + (text[-1] if j == len(chars) - 1 else ""), "start": round(t0, 3), "end": round(len(x) / SR, 3)})
        if j + 1 < len(chars):
            x += [0.0] * int((1 / rate - burst + (pause[1] if pause and j + 1 == pause[0] else 0)) * SR)
    if sid == "a1":
        words[0]["start"] += 0.12                     # the ASR heard the first syllable late
    if sid == "b2":                                   # b1 ends and b2 starts at the same instant, 20 ms before b1's voice ends
        segs[-1]["words"][-1]["end"] = words[0]["start"] = segs[-1]["end"] = round(segs[-1]["end"] - 0.02, 3)
    if sid == "b4":                                   # "……": no words, its span is the pause
        segs.append({"id": "b3x", "zh": "……", "en": "", "text": "……", "start": segs[-1]["end"], "end": words[0]["start"]})
    segs.append({"id": sid, "zh": text, "en": "", "text": text, "start": words[0]["start"], "end": words[-1]["end"], "words": words})
    x += [0.0] * int(gap * SR)
x += [0.0] * int(0.5 * SR)
with wave.open(str(a / "voiceover.zh.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(struct.pack(f"<{len(x)}h", *(int(round(v * 32767)) for v in x)))
tl = json.dumps({"provider": "say", "lang": "zh", "duration": round(len(x) / SR, 3), "segments": segs}, ensure_ascii=False)
for f in ("timeline.zh.json", "timeline.json"):
    (a / f).write_text(tl, encoding="utf-8")
(a / "voiceover.wav").write_bytes((a / "voiceover.zh.wav").read_bytes())
PY
  cp -R "$p/audio" "$t/orig"
  # the onsets of the syllables in a take (10 ms frames above −40 dBFS) and the quiet before each: what every check below counts
  cat > "$t/onsets.py" <<'PY'
import subprocess, numpy as np
def onsets(wav, sr=22050):
    y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                                     check=True, capture_output=True).stdout, "<f4")
    hop = sr // 100; n = len(y) // hop
    on = 10 * np.log10(np.mean(y[: n * hop].reshape(n, hop) ** 2, 1) + 1e-18) > -40
    up, down = (np.flatnonzero(np.diff(on.astype(int)) == 1) + 1) * 0.01, (np.flatnonzero(np.diff(on.astype(int)) == -1) + 1) * 0.01
    return up, np.array([up[0]] + [u - d for u, d in zip(up[1:], down)]), on
PY
  vh pace "$p" --dry-run >/dev/null && diff -r "$p/audio" "$t/orig" >/dev/null && ok "pace --dry-run writes nothing" || bad "pace --dry-run changed the project"
  if a=$(vh pace "$p" 2>&1) && a=$(PYTHONPATH="$t" uv run -q --no-project --with numpy python - "$p/audio" "$t/orig" 2>&1 <<'PY'
import json, sys
import numpy as np
from onsets import onsets
A, O = sys.argv[1], sys.argv[2]; bad = []
tl = json.load(open(f"{A}/timeline.zh.json", encoding="utf-8")); P = tl["pace"]; S = {s["id"]: s for s in tl["segments"]}
if open(f"{A}/voiceover.zh.raw.wav", "rb").read() != open(f"{O}/voiceover.zh.wav", "rb").read() or \
   open(f"{A}/timeline.zh.raw.json", "rb").read() != open(f"{O}/timeline.zh.json", "rb").read(): bad.append("the .raw files are not the original")
if open(f"{A}/voiceover.wav", "rb").read() != open(f"{A}/voiceover.zh.wav", "rb").read(): bad.append("voiceover.wav is not the paced copy")
ons, quiet, on = onsets(f"{A}/voiceover.zh.wav")
words = [w for s in tl["segments"] for w in s.get("words", [])]
if len(ons) != 42 or len(words) != 42: bad.append(f"{len(ons)} syllables in the paced take, {len(words)} words (42 each)")
else:
    err = np.abs(ons - [w["start"] for w in words])
    if err.max() > 0.035: bad.append(f"a mapped word {err.max():.3f} s from its syllable ({words[int(err.argmax())]['w']})")
L = {l["id"]: l for l in P["lines"]}
paced = [l for l in P["lines"] if l.get("note") not in ("short", "no words")]
sd = lambda k: float(np.std([l[k] for l in paced]))
if not sd("after") < 0.8 * sd("pace"): bad.append(f"spread of paces {sd('pace'):.2f} → {sd('after'):.2f}")
if not all(0.92 - 1e-9 <= l["tempo"] <= 1.18 + 1e-9 for l in P["lines"] if "tempo" in l) or L["b2"]["tempo"] != 1.0 or L["a1"]["tempo"] <= 1 \
   or L["a2"]["tempo"] >= 1 or L["b3x"].get("note") != "no words":
    bad.append(f"tempos {[(l['id'], l.get('tempo'), l.get('note')) for l in P['lines']]}")
def longest_quiet(s):
    q = on[int(s["start"] / 0.01): int(s["end"] / 0.01)]; best = cur = 0
    for v in q:
        cur = 0 if v else cur + 1; best = max(best, cur)
    return best * 0.01
if longest_quiet(S["b1"]) > 0.3 or longest_quiet(S["b3"]) < 0.5: bad.append(f"inner pauses: b1 {longest_quiet(S['b1']):.2f} (cap 0.26), b3 {longest_quiet(S['b3']):.2f} (asked for)")
gap = lambda i, j: S[j]["start"] - S[i]["end"]
if not (0.1 <= gap("a1", "a2") <= 0.2 and 1.1 <= gap("a2", "b1") <= 1.25 and 0.35 <= gap("b1", "b2") <= 0.45 and 0.45 <= gap("b3", "b4") <= 0.56):
    bad.append(f"gaps a1-a2 {gap('a1', 'a2'):.2f} (0.12), a2-b1 {gap('a2', 'b1'):.2f} (1.2), b1-b2 {gap('b1', 'b2'):.2f} (the take's 0.4),"
               f" b3-b4 {gap('b3', 'b4'):.2f} (the 0.5 a \"……\" line stands for)")
if not S["b3"]["end"] - 0.005 <= S["b3x"]["start"] <= S["b3x"]["end"] <= S["b4"]["start"] + 0.005: bad.append(f"the \"……\" line is not between b3 and b4: {S['b3x']}")
caps = json.load(open(f"{A}/captions.json", encoding="utf-8"))
if [c["start"] for c in caps] != [s["start"] for s in tl["segments"]]: bad.append("captions.json is not from the paced timeline")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
  ); then ok "pace: every syllable kept and every mapped word on it, paces closer within the clamp, an inner pause capped and an asked-for one kept, gaps in range, a \"……\" line's pause kept, originals kept, captions redone"
  else bad "pace on a synthetic take: $a"; fi
  cp "$p/audio/voiceover.zh.wav" "$t/once.wav"
  vh pace "$p" >/dev/null && cmp -s "$t/once.wav" "$p/audio/voiceover.zh.wav" && ok "pace runs again from the original take: the same bytes" || bad "pace: a second run gave a different take"
  vh pace "$p" --restore --dry-run >/dev/null 2>&1; rc=$?
  [ $rc = 2 ] && cmp -s "$t/once.wav" "$p/audio/voiceover.zh.wav" && ok "pace --restore --dry-run is refused" || bad "pace --restore --dry-run: exit $rc"
  vh pace "$p" --restore >/dev/null && cmp -s "$p/audio/voiceover.zh.wav" "$t/orig/voiceover.zh.wav" && cmp -s "$p/audio/timeline.zh.json" "$t/orig/timeline.zh.json" \
    && cmp -s "$p/audio/voiceover.wav" "$t/orig/voiceover.zh.wav" && cmp -s "$p/audio/timeline.json" "$t/orig/timeline.json" \
    && [ ! -e "$p/audio/voiceover.zh.raw.wav" ] && ok "pace --restore puts the original back" || bad "pace --restore"
  # ASRs further off: every start 0.2 s late and end 0.3 s early (f), a line break placed 0.1 s inside a2's last syllable (m),
  # the last line with no audio at all (s): no syllable lost or moved behind a pause, no crash
  for v in f m s; do mkdir "$t/$v" && cp -R "$t/orig" "$t/$v/audio"; done
  python3 - "$t" <<'PY'
import json, subprocess, sys
t = sys.argv[1]; F = "audio/timeline.zh.json"
def edit(v, fn):
    tl = json.load(open(f"{t}/{v}/{F}", encoding="utf-8")); fn(tl["segments"]); json.dump(tl, open(f"{t}/{v}/{F}", "w", encoding="utf-8"), ensure_ascii=False)
def late(segs):
    for s in segs:
        if s.get("words"):
            s["start"] = s["words"][0]["start"] = round(min(s["start"] + 0.2, s["words"][0]["end"]), 3)
            s["end"] = s["words"][-1]["end"] = round(max(s["end"] - 0.3, s["words"][-1]["start"]), 3)
def inside(segs):
    p, q = segs[1], segs[2]                           # a2 | b1
    p["end"] = p["words"][-1]["end"] = q["start"] = q["words"][0]["start"] = round(p["end"] - 0.1, 3)
edit("f", late); edit("m", inside)
b4 = json.load(open(f"{t}/s/{F}", encoding="utf-8"))["segments"][-1]["start"]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{t}/orig/voiceover.zh.wav", "-t", f"{b4 - 0.05:.3f}", f"{t}/s/audio/voiceover.zh.wav"], check=True)
PY
  a=""; for v in f m s; do vh pace "$t/$v" >/dev/null 2>"$t/$v.err" || a="$a $v: $(tail -c 300 "$t/$v.err")"; done
  if [ -z "$a" ] && a=$(PYTHONPATH="$t" uv run -q --no-project --with numpy python - "$t" 2>&1 <<'PY'
import json, sys
from onsets import onsets
t = sys.argv[1]; bad = []
for v, want in (("f", 42), ("m", 42), ("s", 35)):
    ons, quiet, _ = onsets(f"{t}/{v}/audio/voiceover.zh.wav")
    if len(ons) != want: bad.append(f"{v}: {len(ons)} syllables, want {want}")
    elif v == "m" and quiet[15] > 0.1: bad.append(f"m: a2's last syllable moved behind a {quiet[15]:.2f} s pause")
L = {l["id"]: l for l in json.load(open(f"{t}/s/audio/timeline.zh.json", encoding="utf-8"))["pace"]["lines"]}
if L["b4"].get("note") != "nothing heard": bad.append(f"s: b4 {L['b4']}")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
  ); then ok "pace: ASR starts 0.2 s late and ends 0.3 s early, a line break inside a syllable, a line with no audio: every syllable kept, none moved"
  else bad "pace with an ASR further off:$a"; fi
  # more cases, each on its own copy: b1 with no audio (u), b1 and b2 spans swapped (o), word times only in the cache (c, and c2
  # without it), no script.txt (n), and a take of its own (t): a quiet breath before one line, three short loud syllables
  # opening the next
  for v in u o c c2 n; do mkdir "$t/$v" && cp -R "$t/orig" "$t/$v/audio"; done
  python3 - "$t" <<'PY'
import hashlib, json, math, struct, sys, wave
from pathlib import Path
t = sys.argv[1]; F = "audio/timeline.zh.json"
tl = json.load(open(f"{t}/orig/timeline.zh.json", encoding="utf-8")); S = {s["id"]: s for s in tl["segments"]}
b1 = S["b1"]                                          # b1's syllables zeroed (its timeline end sits 0.02 s before its voice ends)
with wave.open(f"{t}/orig/voiceover.zh.wav") as r:
    sr, pcm = r.getframerate(), bytearray(r.readframes(r.getnframes()))
z0, z1 = int((b1["words"][0]["start"] - 0.005) * sr), int((b1["words"][-1]["end"] + 0.025) * sr)
pcm[2 * z0: 2 * z1] = bytes(2 * (z1 - z0))
with wave.open(f"{t}/u/audio/voiceover.zh.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(bytes(pcm))
o = json.loads(json.dumps(tl)); a, b = o["segments"][2], o["segments"][3]
a["start"], a["end"], b["start"], b["end"] = b["start"], b["end"], a["start"], a["end"]
json.dump(o, open(f"{t}/o/{F}", "w", encoding="utf-8"), ensure_ascii=False)
for v in ("c", "c2"):                                 # word times removed; for c they are in the cache under the take's sha256
    c = json.loads(json.dumps(tl))
    for s in c["segments"]:
        s.pop("words", None)
    Path(f"{t}/{v}/{F}").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
sha = hashlib.sha256(open(f"{t}/orig/voiceover.zh.wav", "rb").read()).hexdigest()
Path(f"{t}/c/audio/pace.zh.asr.json").write_text(json.dumps({"sha256": sha, "engine": "whisper", "segments": [
    {"start": s["start"], "end": s["end"], **({"words": s["words"]} if s.get("words") else {})} for s in tl["segments"]]}), encoding="utf-8")
Path(f"{t}/n/audio/script.txt").unlink()
SR, x, segs, A = 22050, [0.0] * int(0.4 * 22050), [], Path(f"{t}/t/audio")
A.mkdir(parents=True)
def burst(dur, amp, f0):
    n = int(dur * SR); return [amp * math.sin(math.pi * i / n) ** 0.5 * (math.sin(2 * math.pi * f0 * i / SR) + 0.5 * math.sin(4 * math.pi * f0 * i / SR)) for i in range(n)]
for sid, text, plan in (("t1", "甲乙丙丁戊己庚辛。", [("breath",)] + [(0.15, 0.05)] * 8), ("t2", "子丑寅卯辰巳午未申酉戌亥。", [(0.09, 0.09)] * 3 + [(0.15, 0.05)] * 9),
                        ("t3", "东南西北中发白甲。", [(0.15, 0.05)] * 8)):
    words, chars = [], iter(text[:-1])
    for k, step in enumerate(plan):
        if step == ("breath",):
            x += burst(0.08, 0.0095, 300) + [0.0] * int(0.12 * SR); continue
        t0 = len(x) / SR; x += burst(step[0], 0.25, 150 + 10 * (k % 4))
        words.append({"w": next(chars), "start": round(t0, 3), "end": round(len(x) / SR, 3)}); x += [0.0] * int(step[1] * SR)
    words[-1]["w"] += "。"; segs.append({"id": sid, "zh": text, "en": "", "text": text, "start": words[0]["start"], "end": words[-1]["end"], "words": words})
    x += [0.0] * int(0.45 * SR)
with wave.open(str(A / "voiceover.zh.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(struct.pack(f"<{len(x)}h", *(int(round(v * 32767)) for v in x)))
(A / "timeline.zh.json").write_text(json.dumps({"provider": "say", "lang": "zh", "segments": segs}, ensure_ascii=False), encoding="utf-8")
(A / "script.txt").write_text("".join(f"@{s['id']} {s['text']}\n" for s in segs), encoding="utf-8")
PY
  cp -R "$t/c/audio" "$t/c.before"
  a=""; rc=0
  vh pace "$t/u" >"$t/u.out" 2>&1 || a="$a u: $(tail -c 300 "$t/u.out")"
  vh pace "$t/t" >"$t/t.out" 2>&1 || a="$a t: $(tail -c 300 "$t/t.out")"
  b=$(vh pace "$t/c" --dry-run 2>&1) && diff -r "$t/c/audio" "$t/c.before" >/dev/null || a="$a c --dry-run wrote or failed: $b"
  case "$b" in *"transcribed before"*) ;; *) a="$a c --dry-run did not use the cache: $b" ;; esac
  vh pace "$t/c" >/dev/null 2>&1 && cmp -s "$t/c/audio/timeline.zh.raw.json" "$t/c.before/timeline.zh.json" || a="$a c: the .raw timeline is not the original"
  b=$(vh pace "$t/c2" 2>&1); [ $? = 1 ] && case "$b" in *"no word times"*) ;; *) false ;; esac || a="$a c2 (no words, no cache): $b"
  b=$(vh pace "$t/o" 2>&1); [ $? = 1 ] && case "$b" in *"the timeline has"*"out of order"*) ;; *) false ;; esac || a="$a o (spans swapped, the lint): $b"
  b=$(vh pace "$t/o" --skip-lint 2>&1); [ $? = 1 ] && case "$b" in *"re-align the take"*) ;; *) false ;; esac || a="$a o (spans swapped, pace's own guard): $b"
  b=$(vh pace "$t/n" --dry-run 2>&1); case "$b" in *"no audio/script.txt"*) ;; *) a="$a n (no script.txt): $b" ;; esac
  b=$(PYTHONPATH="$t" uv run -q --no-project --with numpy python - "$t" 2>&1 <<'PY'
import json, sys
from onsets import onsets
t = sys.argv[1]; bad = []
raw = {s["id"]: s for s in json.load(open(f"{t}/orig/timeline.zh.json", encoding="utf-8"))["segments"]}
tl = json.load(open(f"{t}/u/audio/timeline.zh.json", encoding="utf-8")); S = {s["id"]: s for s in tl["segments"]}
L = {l["id"]: l for l in tl["pace"]["lines"]}
ons, _, _ = onsets(f"{t}/u/audio/voiceover.zh.wav")
g0 = raw["b1"]["end"] + 0.02 + 0.4 - raw["a2"]["end"]  # a2's voice to b2's, in the take (b2's timeline start is the shared one)
g1 = S["b2"]["start"] - S["a2"]["end"]
if len(ons) != 32 or L["b1"].get("note") != "nothing heard" or abs(g1 - g0) > 0.05 or S["b1"]["end"] - S["b1"]["start"] < 0.1 - 1e-9 \
   or S["b1"]["start"] < S["a2"]["end"]:
    bad.append(f"u: {len(ons)} syllables (32), b1 {L['b1']} at {S['b1']['start']}–{S['b1']['end']}, a2→b2 {g1:.2f} s (the take's {g0:.2f})")
P = {l["id"]: l for l in json.load(open(f"{t}/t/audio/timeline.zh.json", encoding="utf-8"))["pace"]["lines"]}
true = {"t1": 8 / 1.55, "t2": 12 / 2.29}            # syllables over first onset → last end; the breath is not speech
for k, v in true.items():
    if abs(P[k]["pace"] / v - 1) > 0.06: bad.append(f"t: {k} measured {P[k]['pace']:.2f}, true {v:.2f}")
c = json.load(open(f"{t}/c/audio/timeline.zh.json", encoding="utf-8"))
if sum(len(s.get("words", [])) for s in c["segments"]) != 42: bad.append("c: the cached word times did not reach the paced timeline")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
  ) || a="$a $b"
  if [ -z "$a" ]; then ok "pace: a line with no audio keeps its stretch of the take, a quiet breath is not speech and short loud syllables are, cached word times are used and the .raw stays the original, swapped spans and a missing script.txt are said"
  else bad "pace on the other cases:$a"; fi
  mkdir "$t/k" && cp -R "$t/orig" "$t/k/audio"
  a=$(vh pace "$t/k" --dry-run --target 6 --extra b2=0.3 zh 2>&1); rc=$?
  case "$rc:$a" in 0:*"(--target 6)"*) printf '%s\n' "$a" | grep -q '^  b2 .*→ 0\.59 s' && ok "pace --target, --extra and the language after the flags" || bad "pace --extra b2=0.3: $a" ;;
    *) bad "pace --target 6 … zh: exit $rc: $a" ;; esac
  a=$(env -u GEMINI_API_KEY "$VH_BASH" "$ROOT/bin/vh" pace "$t/k" --align gemini 2>&1); rc=$?
  [ $rc = 1 ] && diff -r "$t/k/audio" "$t/orig" >/dev/null && ok "pace --align gemini without a key stops before writing" || bad "pace --align gemini without a key: exit $rc, $a"
  a=$(vh pace "$t/k" --ref b3x --dry-run 2>&1); rc=$?
  case "$rc:$a" in 1:*"--ref b3x"*) ok "pace --ref on a line without words is refused" ;; *) bad "pace --ref b3x: exit $rc: $a" ;; esac
  python3 -c "import json, sys; t = json.load(open(sys.argv[1])); t['grid'] = {'beats': 'm.json'}; json.dump(t, open(sys.argv[1], 'w'))" "$t/k/audio/timeline.zh.json"
  a=$(vh pace "$t/k" 2>&1); rc=$?
  case "$rc:$a" in 1:*"beat grid"*) ok "pace refuses a timeline on a beat grid" ;; *) bad "pace on a beat grid: exit $rc: $a" ;; esac
  # v2: the speech rate leaves pauses out (q2: a 0.5 s pause, no mark); pause floors lengthen only a silence already at a
  # comma or a full stop (q1's 0.04 s comma; q3 runs through its comma: nothing there) and never touch the voice;
  # --relative moves every line of the current take by one factor
  python3 - "$t/q/audio" <<'PY'
import json, math, struct, sys, wave
from pathlib import Path
a = Path(sys.argv[1]); a.mkdir(parents=True); SR = 22050
# id, text, syllable period (s), {after unit k: silence s}, gap after the line: p1 has a 0.04 s comma, p2 a 0.5 s pause
# (no mark), p3 runs straight through its comma (no silence there at all), then a full stop with 0.1 s to the next line
lines = [("q1", "一二三，四五六七八。", 0.2, {3: 0.04}, 0.5), ("q2", "甲乙丙丁戊己庚辛。", 0.16, {4: 0.5}, 0.1),
         ("q3", "东南西，北中发白。", 0.18, {}, 0.6)]
x, segs = [0.0] * int(0.4 * SR), []
for k, (sid, text, per, pauses, gap) in enumerate(lines):
    chars = [c for c in text if c not in "，。"]; words = []; burst = per * 0.8
    for j, c in enumerate(chars):
        t0, n, f0 = len(x) / SR, int(burst * SR), 150 + 12 * ((j * 5 + k) % 4)
        x += [0.25 * math.sin(math.pi * i / n) ** 0.5 * (math.sin(2 * math.pi * f0 * i / SR) + 0.5 * math.sin(4 * math.pi * f0 * i / SR)) for i in range(n)]
        mark = "，" if j + 1 == 3 and "，" in text else ""
        words.append({"w": c + mark + ("。" if j == len(chars) - 1 else ""), "start": round(t0, 3), "end": round(len(x) / SR, 3)})
        if j + 1 < len(chars):
            if sid == "q3" and j + 1 == 3:
                x += [0.0] * 0  # straight on into the next syllable
            else:
                x += [0.0] * int((per - burst) * SR)
            x += [0.0] * int(pauses.get(j + 1, 0) * SR)
    segs.append({"id": sid, "zh": text, "en": "", "text": text, "start": words[0]["start"], "end": words[-1]["end"], "words": words})
    x += [0.0] * int(gap * SR)
x += [0.0] * int(0.5 * SR)
with wave.open(str(a / "voiceover.zh.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(struct.pack(f"<{len(x)}h", *(int(round(v * 32767)) for v in x)))
(a / "timeline.zh.json").write_text(json.dumps({"provider": "say", "lang": "zh", "duration": round(len(x) / SR, 3), "segments": segs}, ensure_ascii=False), encoding="utf-8")
(a / "script.txt").write_text("".join(f"@{s['id']} {s['text']}\n" for s in segs), encoding="utf-8")
PY
  cp -R "$t/q/audio" "$t/q.orig"
  a=$(vh pace "$t/q" --dry-run 2>&1); rc=$?
  b=$(vh pace "$t/q" --strength 0 --comma 0.3 --stop 0.5 2>&1) || a="$a floors: $b"
  if [ $rc = 0 ] && b=$(PYTHONPATH="$t" uv run -q --no-project --with numpy python - "$t" "$a" 2>&1 <<'PY'
import json, re, sys
from onsets import onsets
t, dry = sys.argv[1], sys.argv[2]; bad = []
m = re.search(r"^  q2 +8 +([0-9.]+)", dry, re.M)
true = 8 / (8 * 0.16 - 0.032 - 0.032)                 # syllables over the voice, the 0.5 s pause and the gap in front of it left out
if not m or abs(float(m.group(1)) / true - 1) > 0.06: bad.append(f"q2's speech rate {m and m.group(1)}, true {true:.2f}")
if "with pauses" not in dry or "speech rate" not in dry: bad.append("the dry run does not print both rates")
tl = json.load(open(f"{t}/q/audio/timeline.zh.json", encoding="utf-8")); S = {s["id"]: s for s in tl["segments"]}
ons0, _, on0 = onsets(f"{t}/q.orig/voiceover.zh.wav"); ons1, quiet, on1 = onsets(f"{t}/q/audio/voiceover.zh.wav")
runs = lambda on: [len(r) for r in "".join("x" if v else " " for v in on).split()]   # each syllable's voiced frames
if len(ons1) != len(ons0) or max(abs(p - q) for p, q in zip(runs(on0), runs(on1))) > 1: bad.append(f"voice changed: {len(ons0)} → {len(ons1)} syllables, {runs(on0)} → {runs(on1)} frames")
else:
    if quiet[3] < 0.28: bad.append(f"q1's comma: {quiet[3]:.2f} s of quiet (floor 0.3)")
    O = {s["id"]: s for s in json.load(open(f"{t}/q.orig/timeline.zh.json", encoding="utf-8"))["segments"]}
    if abs((S["q3"]["end"] - S["q3"]["start"]) - (O["q3"]["end"] - O["q3"]["start"])) > 0.02:   # its comma has no silence: nothing to lengthen
        bad.append(f"q3, whose voice runs through its comma, changed length: {O['q3']['end'] - O['q3']['start']:.2f} → {S['q3']['end'] - S['q3']['start']:.2f} s")
    if quiet[16] < 0.48: bad.append(f"q2 → q3 after a full stop: {quiet[16]:.2f} s (floor 0.5)")
if tl["pace"]["lengthened"][0] != 1: bad.append(f"pauses lengthened: {tl['pace']['lengthened']}")
print("\n".join(bad)); sys.exit(1 if bad else 0)
PY
  ); then ok "pace v2: the speech rate leaves pauses out, the dry run prints it and the rate with pauses; pause floors lengthen a silence at a mark, not where the voice runs on, and the voice is untouched"
  else bad "pace v2 (speech rate, floors): exit $rc: $a $b"; fi
  rm -rf "$t/q" && mkdir "$t/q" && cp -R "$t/q.orig" "$t/q/audio"
  a=""
  vh pace "$t/q" --relative -5% >/dev/null 2>&1 || a="$a raw -5% failed"
  t1=$(python3 -c "import json,sys; print(' '.join(str(l['tempo']) for l in json.load(open(sys.argv[1]))['pace']['lines']))" "$t/q/audio/timeline.zh.json")
  [ "$t1" = "0.95 0.95 0.95" ] || a="$a on the original take: tempos $t1 (0.95 each)"
  vh pace "$t/q" >/dev/null 2>&1 || a="$a default run failed"
  last=$(python3 -c "import json,sys; print(' '.join(str(l['tempo']) for l in json.load(open(sys.argv[1]))['pace']['lines']))" "$t/q/audio/timeline.zh.json")
  vh pace "$t/q" --relative +10% >/dev/null 2>&1 || a="$a paced +10% failed"
  python3 - "$t/q/audio/timeline.zh.json" "$last" <<'PY' || a="$a on a paced take: not its tempos × 1.10 within the clamp"
import json, sys
now = [l["tempo"] for l in json.load(open(sys.argv[1]))["pace"]["lines"]]; last = [float(v) for v in sys.argv[2].split()]
sys.exit(0 if all(abs(n - min(1.18, l * 1.1)) < 1e-3 for n, l in zip(now, last)) else 1)
PY
  if [ -z "$a" ]; then ok "pace --relative: every line of the original take × 0.95; on a paced take, its own tempos × 1.10 within the clamp"
  else bad "pace --relative:$a"; fi
  rm -rf "$t"
}

case "${1:-all}" in
  --smoke) smoke_checks; pace_checks; timeline_checks; decision_checks; gate_checks; desk_checks; activity_checks; status_checks; assets_checks; textcheck_checks; film_checks ;;
  --committed)   # exactly what a push would send: HEAD in a clean temporary checkout, uncommitted changes left out
    w="$(mktemp -d "${TMPDIR:-/tmp}/vh-ci.XXXXXX")/head"; git worktree add -q --detach "$w" HEAD || exit 2
    (cd "$w" && tools/ci.sh); rc=$?; git worktree remove --force "$w"; rmdir "$(dirname "$w")"; exit $rc ;;
  all) static_checks; doc_checks; readpath_report; smoke_checks; pace_checks; timeline_checks; decision_checks; gate_checks; desk_checks; activity_checks; status_checks; assets_checks; textcheck_checks; film_checks ;;
  *) echo "usage: tools/ci.sh [--smoke | --committed]"; exit 2 ;;
esac
[ -n "$skipped" ] && printf '\033[33m! skipped, so not checked: %s\033[0m\n' "$skipped"   # said again at the end: a pass is not a pass of these
[ $fails = 0 ] && ok "all checks passed" || printf '\033[31m%s check(s) failed\033[0m\n' "$fails"
exit $fails
