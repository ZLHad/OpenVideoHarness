"""Which groups of tools/ci.sh a change needs: tools/ci.sh --changed [base] runs them (stdlib only, and bash).

usage: python3 tools/ci_select.py [base] [--why]   the groups, one a line, in the order of the group table
       python3 tools/ci_select.py --check          tools/ci-paths.txt and tools/ci.sh's functions against the repo

The change is what differs between HEAD's merge base with base (origin/main unless given) and the working tree, files
not yet added to git included. Each changed path runs the groups of every line of tools/ci-paths.txt it matches, and
the table's "always" groups run whatever changed. A path that no line matches runs every group, and so does a line
that names ALL: when in doubt, more. Two files are read for what changed inside them, not by their name:
  - tools/ci.sh: a change inside a group's function runs that group; inside a helper, the groups that call it; in a
    comment just above a function, that function's groups; anywhere else (the top, the dispatch) every group;
  - tools/ci-shards.txt: a group it adds runs; a change to the seconds runs nothing more.
The group table is tools/ci-shards.txt, or OVH_CI_SHARDS when tools/ci.sh runs another; OVH_CI_PATHS another path table
(tools/ci.sh's own checks use both). --why says on stderr, for each path, what it runs.
--check: each group the path table names is a group of tools/ci-shards.txt; each pattern matches a file git tracks;
bash finds every group's function in tools/ci.sh, a line inside each one maps to that group alone, and the dispatch
maps to every group.
Exit: 0 · 1 --check found a problem · 2 no such base, not a git checkout, or a table that cannot be read.
"""
import os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CI = "tools/ci.sh"
SHARDS = "tools/ci-shards.txt"
PATHS = "tools/ci-paths.txt"
ALL = "ALL"


class Stop(Exception):   # exit 2
    pass


def git(*a, ok=False):
    p = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)
    if p.returncode and not ok:
        raise Stop(f"git {' '.join(a[:3])}: {(p.stderr or p.stdout).strip()[:300]}")
    return p.stdout if p.returncode == 0 else ""


def table_groups_text(text):
    """The groups of a group table's text, in its order."""
    return [ln.split()[0] for ln in (x.split("#")[0].strip() for x in text.splitlines()) if ln]


def table_groups(path):
    try:
        return table_groups_text(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        raise Stop(f"{path}: {e.strerror}")


def glob_re(pattern):
    """A path pattern as a regular expression: ** any run of characters, * and ? within one folder."""
    out, i = "", 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif c == "*":
            out, i = out + "[^/]*", i + 1
        elif c == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(c), i + 1
    return re.compile(out + r"\Z")


def path_table(path):
    """(always groups, [(pattern, regex, groups)]) of the path table."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise Stop(f"{path}: {e.strerror}")
    always, rows = [], []
    for line in text.splitlines():
        words = line.split("#")[0].split()
        if not words:
            continue
        if words[0] == "always":
            always += words[1:]
        else:
            rows.append((words[0], glob_re(words[0]), words[1:]))
    return always, rows


# ---- tools/ci.sh: which function a line is in, and which groups that means ----

def functions(text):
    """{name: (first, last)} line numbers of tools/ci.sh's functions. bash says where each starts (extdebug), sourcing
    the file up to its dispatch (the line that starts usage=), which only defines; a function ends at the last line
    that is a lone } before the next one starts."""
    lines = text.split("\n")
    cut = next((i for i, x in enumerate(lines) if x.startswith("usage=")), len(lines))
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "ci-top.sh")
        with open(f, "w", encoding="utf-8") as h:
            h.write("\n".join(lines[:cut]) + "\n")
        p = subprocess.run(["bash", "-c", 'shopt -s extdebug; source "$1" >/dev/null 2>&1 </dev/null; '
                            'for f in $(compgen -A function); do declare -F "$f"; done', "_", f],
                           capture_output=True, text=True, cwd=d)
    starts = sorted((int(m.group(2)), m.group(1)) for m in re.finditer(r"^(\S+) (\d+) ", p.stdout, re.M))
    if not starts:
        raise Stop(f"{CI}: bash found no function in it ({(p.stderr or '').strip()[:200]})")
    out = {}
    for k, (s, name) in enumerate(starts):
        nxt = starts[k + 1][0] if k + 1 < len(starts) else cut + 1
        ends = [i for i in range(s, nxt) if lines[i - 1] == "}"]
        out[name] = (s, max(ends) if ends else s)
    return out


class Script:
    def __init__(self, text, groups):
        self.lines = text.split("\n")
        self.fns = functions(text)
        self.groups = groups
        self.body = {f: "\n".join(self.lines[a - 1:b]) for f, (a, b) in self.fns.items()}
        inside = set()
        for a, b in self.fns.values():
            inside.update(range(a, b + 1))
        self.top = "\n".join(x for i, x in enumerate(self.lines, 1) if i not in inside and not x.lstrip().startswith("#"))
        self.memo = {}

    def at(self, n):
        """The function line n is in, or None."""
        for f, (a, b) in self.fns.items():
            if a <= n <= b:
                return f
        return None

    def of_function(self, f, seen=()):
        """The groups a change inside function f runs: f itself when it is a group, else the groups that call it."""
        if f in self.groups:
            return {f}
        if f in self.memo:
            return self.memo[f]
        call = re.compile(rf"(^|[^A-Za-z0-9_]){re.escape(f)}([^A-Za-z0-9_]|$)", re.M)
        if call.search(self.top):
            return {ALL}   # the top or the dispatch calls it: every run does
        out = set()
        for g, body in self.body.items():
            if g != f and g not in seen and call.search(body):
                out |= self.of_function(g, seen + (f,))
        out = out or {ALL}   # nothing calls it by name: no telling who does
        self.memo[f] = out
        return out

    def comment(self, n):
        return 1 <= n <= len(self.lines) and (not self.lines[n - 1].strip() or self.lines[n - 1].lstrip().startswith("#"))

    def of_hunk(self, a, b, removed):
        """The groups a change runs: lines a to b written (b < a: none, a deletion between b and a), what it took out."""
        if b < a:   # taken out between two lines: within one function, that function; else as at the top
            f = self.at(b)
            if f and f == self.at(a):
                return self.of_function(f)
            return {ALL} if removed == "code" else self.of_line(a) if removed == "comment" else set()
        g = set().union(*(self.of_line(n) for n in range(a, b + 1)))
        if removed == "code" and any(not self.at(n) for n in range(a, b + 1)):
            g = {ALL}   # code taken out at the top
        return g

    def of_line(self, n):
        """The groups a change at line n runs. A comment between functions belongs to the function right below it; a
        blank line between functions to none."""
        f = self.at(n)
        if f:
            return self.of_function(f)
        if 1 <= n <= len(self.lines) and not self.lines[n - 1].strip():
            return set()
        if self.comment(n):
            k = n
            while self.comment(k) and not self.at(k):
                k += 1
            f = self.at(k)
            if f and self.fns[f][0] == k:
                return self.of_function(f)
        return {ALL}


def ci_hunks(base):
    """[(first, last, removed)] of each change to tools/ci.sh in the working tree's lines; a pure deletion is (n + 1, n)
    for the lines n and n + 1 it lay between. removed: what the lines it takes out were, "code" when any is more than a
    comment or a blank, else "comment" when any is a comment, else "blank" (or nothing taken out)."""
    out = []
    for line in git("diff", "-U0", "--no-color", "--no-ext-diff", base, "--", CI).splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            c, d = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
            out.append([c, c + d - 1, "blank"] if d else [c + 1, c, "blank"])
        elif out and line.startswith("-") and not line.startswith("---"):
            x = line[1:].strip()
            if x.startswith("#") and out[-1][2] == "blank":
                out[-1][2] = "comment"
            elif x and not x.startswith("#"):
                out[-1][2] = "code"
    return out


def select(base, why):
    if not git("rev-parse", "--is-inside-work-tree", ok=True).strip():
        raise Stop(f"{ROOT} is not a git checkout")
    if not git("rev-parse", "--verify", "-q", f"{base}^{{commit}}", ok=True).strip():
        raise Stop(f"no commit {base} here (git fetch origin, or name another base)")
    mb = git("merge-base", base, "HEAD").strip()
    groups = table_groups(os.environ.get("OVH_CI_SHARDS") or ROOT / SHARDS)
    always, rows = path_table(os.environ.get("OVH_CI_PATHS") or ROOT / PATHS)
    changed = set(git("diff", "--name-only", "--no-renames", mb).split()) | set(git("ls-files", "--others", "--exclude-standard").split())
    say, chosen = [], set(always)
    for p in sorted(changed):
        if p == CI:
            if not (ROOT / CI).is_file():
                runs = [("deleted", {ALL})]
            else:
                script = Script((ROOT / CI).read_text(encoding="utf-8"), groups)
                runs = []
                for a, b, removed in ci_hunks(mb):
                    where = f"lines {a}-{b}" if b > a else f"line {a}" if b == a else f"between lines {b} and {a}"
                    runs.append((where, script.of_hunk(a, b, removed)))
            for where, g in runs:
                chosen |= g
                say.append((f"{p}, {where}", g, ""))
            continue
        if p == SHARDS:
            old = set(table_groups_text(git("show", f"{mb}:{SHARDS}", ok=True)))
            new = set(groups) - old
            chosen |= new
            say.append((p, new, "" if new else "(no group added)"))
            continue
        hit = [r for r in rows if r[1].match(p)]
        g = set().union(*(set(r[2]) for r in hit)) if hit else {ALL}
        chosen |= g
        say.append((p, g, "" if hit else f"no line of {PATHS} matches it"))
    run = groups if ALL in chosen else [g for g in groups if g in chosen]
    if why:
        w = max([len(s[0]) for s in say] + [20])
        print(f"changed since {base} (merge base {mb[:7]}): {len(changed)} path(s)" if changed else
              f"nothing changed since {base} (merge base {mb[:7]})", file=sys.stderr)
        for where, g, note in say:
            text = "every group" if ALL in g else " ".join(x for x in groups if x in g) or "the always groups"
            print(f"  {where:<{w}}  {text}{': ' + note if note and ALL in g else (' ' + note if note else '')}", file=sys.stderr)
        print(f"always: {' '.join(always)}", file=sys.stderr)
        print(f"so: {'every group' if ALL in chosen else f'{len(run)} of the {len(groups)} groups'}", file=sys.stderr)
    return run


def check():
    problems = []
    groups = table_groups(ROOT / SHARDS)
    always, rows = path_table(ROOT / PATHS)
    named = always + [g for r in rows for g in r[2]]
    problems += [f"{PATHS}: {g} is no group of {SHARDS}" for g in sorted(set(named)) if g != ALL and g not in groups]
    tracked = git("ls-files").split("\n")
    problems += [f"{PATHS}: {pat} matches no file git tracks" for pat, rx, _ in rows if not any(rx.match(f) for f in tracked)]
    text = (ROOT / CI).read_text(encoding="utf-8")
    script = Script(text, groups)
    for g in groups:
        if g not in script.fns:
            problems.append(f"{CI}: bash finds no function {g}")
            continue
        a, b = script.fns[g]
        mid = (a + b) // 2
        if script.of_line(mid) != {g}:
            problems.append(f"{CI}: line {mid}, inside {g}, maps to {sorted(script.of_line(mid))}")
    disp = next((i for i, x in enumerate(script.lines, 1) if x.startswith("usage=")), None)
    if disp is None or script.of_line(disp) != {ALL}:
        problems.append(f"{CI}: the dispatch (usage=…) does not map to every group")
    if problems:
        print("\n".join(problems))
        return 1
    print(f"{PATHS}: {len(rows)} patterns, each matching a tracked file, naming groups of {SHARDS}; {CI}: bash finds "
          f"all {len(groups)} groups, a line inside each maps to it alone, the dispatch to every group")
    return 0


def main():
    a = sys.argv[1:]
    try:
        if a == ["--check"]:
            sys.exit(check())
        why = "--why" in a
        rest = [x for x in a if x != "--why"]
        if len(rest) > 1 or any(x.startswith("-") for x in rest):
            print(__doc__.split("\n\n")[0], file=sys.stderr)
            sys.exit(2)
        print("\n".join(select(rest[0] if rest else "origin/main", why)))
    except Stop as e:
        print(f"ci_select: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
