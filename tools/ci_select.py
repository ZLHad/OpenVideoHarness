"""Which groups of tools/ci.sh a change needs: tools/ci.sh --changed [base] runs them (stdlib only, and bash).

usage: python3 tools/ci_select.py [base] [--why]   the groups, one a line, in the order of the group table
       python3 tools/ci_select.py --check          tools/ci-paths.txt and tools/ci.sh's functions against the repo
       python3 tools/ci_select.py --suggest        each line of tools/ci-paths.txt as --check says it must be

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
maps to every group. And each narrow line covers what its files reach (class Reach): from each file, what imports it or
names it in code (a .py file's strings but its docstrings; a script's lines but its comments), and on from those;
then the bin/vh commands that name any of them (bash says where bin/vh's functions start; a function goes to the case
arms that call it, a line at the top outside an arm to every command) and the groups that run those commands, and the
groups whose lines in tools/ci.sh name any of them (its dispatch left out: it only picks the groups). A file is named by
its name when no other file has it, else by its folder and name, or by its name from its own folder; a line's other
files by its folder (folder/, or the string "folder") or, for one file at the top, by its name. A line that misses a
group it reaches fails, and so does one that reaches every group. Not seen: a name built at run time (bin/vh's
tools/film/$tool.mjs), bin/vh <command> run from inside Python, a file read by a path that never spells its name.
--suggest prints what each line must name (ALL: take it out).
Exit: 0 · 1 --check found a problem · 2 no such base, not a git checkout, or a table that cannot be read.
"""
import ast, json, os, re, subprocess, sys, tempfile
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

def functions(text, cut=None, what=CI):
    """{name: (first, last)} line numbers of a bash script's functions. bash says where each starts (extdebug), sourcing
    the file up to its dispatch (cut: tools/ci.sh's line that starts usage=), which only defines; set -e is taken out of
    the copy so nothing stops it half way. A function ends at the last line that is a lone } before the next one starts."""
    lines = text.split("\n")
    if cut is None:
        cut = next((i for i, x in enumerate(lines) if x.startswith("usage=")), len(lines))
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "top.sh")
        with open(f, "w", encoding="utf-8") as h:
            top = [re.sub(r"^set -([a-z]+)( -o pipefail| pipefail)?\s*$", r"set +\1", x) for x in lines[:cut]]
            top[0] = "set --; " + top[0]   # no arguments, on the first line so the lines keep their numbers
            h.write("\n".join(top) + "\n")
        p = subprocess.run(["bash", "-c", 'shopt -s extdebug; source "$1" >/dev/null 2>&1 </dev/null; '
                            'for f in $(compgen -A function); do declare -F "$f"; done', "_", f],
                           capture_output=True, text=True, cwd=d)
    starts = []
    for m in re.finditer(r"^(\S+) (\d+) ", p.stdout, re.M):
        name, s = m.group(1), int(m.group(2))
        # bash 3.2 (macOS's own) gives a line further down for a function with a heredoc in it: the line that defines
        # it is the nearest one above (else below) that says name() — what bash 5 gives
        own = re.compile(rf"^\s*(function\s+)?{re.escape(name)}\s*\(\)")
        if not (1 <= s <= len(lines) and own.match(lines[s - 1])):
            s = next((k for k in range(min(s, len(lines)), 0, -1) if own.match(lines[k - 1])), None) \
                or next((k for k in range(max(s, 1), len(lines) + 1) if own.match(lines[k - 1])), s)
        starts.append((s, name))
    starts.sort()
    if not starts:
        raise Stop(f"{what}: bash found no function in it ({(p.stderr or '').strip()[:200]})")
    out = {}
    for k, (s, name) in enumerate(starts):
        nxt = starts[k + 1][0] if k + 1 < len(starts) else cut + 1
        ends = [i for i in range(s, nxt) if lines[i - 1] == "}"]   # a lone } (a } inside a quoted block comes before it)
        ends = ends or [i for i in range(s, nxt) if re.sub(r"\s#.*$", "", lines[i - 1]).rstrip().endswith("}")]   # or "…; }"
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
    # -z: names as they are (git quotes one with a space or a non-ASCII letter otherwise)
    changed = {x for x in git("diff", "--name-only", "--no-renames", "-z", mb).split("\0") + git("ls-files", "-z", "--others", "--exclude-standard").split("\0") if x}
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


# ---- --check: what a narrow line of the path table must cover ----

CODE = (".py", ".mjs", ".js", ".sh", ".html")
SKIP = ("references/", "projects/")


def code_text(path, text):
    """(what a file's code says, the module names it imports): a .py file's strings but its docstrings, and the names
    in its imports; a script's or a page's text without its comments."""
    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return text, set()
        docs = {id(n.body[0].value) for n in ast.walk(tree)
                if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str)}
        strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names |= {p for a in n.names for p in a.name.split(".")}
            elif isinstance(n, ast.ImportFrom):
                names |= set((n.module or "").split(".")) | {a.name for a in n.names}
        return "\n".join(strings), names - {""}
    if path.endswith(".html"):
        return re.sub(r"<!--.*?-->", "", text, flags=re.S), set()
    if path.endswith((".js", ".mjs")):
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        return "\n".join(x for x in text.split("\n") if not x.lstrip().startswith("//")), set()
    return "\n".join(re.sub(r"(^|\s)#.*$", "", x) for x in text.split("\n")), set()   # bash


NEEDLE = {}   # a regex's pattern → a plain string each of its matches holds, for a quick test before the regex


def word_rx(word, pattern):
    NEEDLE[pattern] = word
    return re.compile(pattern)


def needle_of(rx):
    return NEEDLE.get(rx.pattern, "")


def name_rx(word):
    """A file name as a whole word of a path."""
    return word_rx(word, rf"(?<![A-Za-z0-9_.-]){re.escape(word)}(?![A-Za-z0-9_-])")


def folder_rx(word):
    """A folder named in code: word/ in a path, or the string "word" on its own (a .py file's strings, a line each)."""
    return word_rx(word, rf"(?<![A-Za-z0-9_.-]){re.escape(word)}/|(?m:^{re.escape(word)}$)")


def root_rx(word):
    """A file at the top of the repository: its name on its own or after ROOT/, not the end of a longer path."""
    return word_rx(word, rf"(?m:^{re.escape(word)}$)|ROOT/{re.escape(word)}|(?<![A-Za-z0-9_./-]){re.escape(word)}(?![A-Za-z0-9_-])")


class VhScript:
    """bin/vh: which of its commands reach a line that names something."""

    def __init__(self, text, commands):
        self.lines = text.split("\n")
        cut = max(i for i, x in enumerate(self.lines) if x.startswith("case "))   # the dispatch, the last case at the top
        self.fns = functions(text, cut, "bin/vh")
        self.commands = commands
        self.fn_at = [None] * (len(self.lines) + 2)
        for f, (a, b) in self.fns.items():
            for n in range(a, b + 1):
                self.fn_at[n] = f
        self.code = [re.sub(r"(^|\s)#.*$", "", x) for x in self.lines]
        self.text = "\n".join(self.code)
        self.memo, self.memo_rx = {}, {}

    def arm(self, n, rx):
        """The commands of the case arms (name|name)) a top-level line names rx in; None for every command (no arm)."""
        out = set()
        for seg in self.code[n - 1].split(";;"):
            m = rx.search(seg)
            if not m:
                continue
            labels = re.findall(r"(?:^|[\s(])([A-Za-z0-9*|-]+)\)", seg[:m.start()])
            known = set(labels[-1].split("|")) & self.commands if labels else set()
            if not known or "*" in labels[-1]:
                return None
            out |= known
        return out

    def of_function(self, f, seen=()):
        """The commands that reach function f: the arms that call it, and the commands of the functions that do; None
        for every command (the top calls it outside an arm, or nothing calls it by name)."""
        if f in self.memo:
            return self.memo[f]
        call, out = name_rx(f), set()
        for n, x in enumerate(self.code, 1):
            g = self.fn_at[n]
            if g == f or g in seen or not call.search(x):
                continue
            r = self.of_function(g, seen + (f,)) if g else self.arm(n, call)
            if r is None:
                out = None
                break
            out |= r
        out = out if out else None
        if not seen:
            self.memo[f] = out
        return out

    def commands_naming(self, rx):
        """The commands that reach a line of bin/vh naming rx; None for every command; set() when no line does."""
        if rx.pattern in self.memo_rx:
            return self.memo_rx[rx.pattern]
        out = set()
        if rx.search(self.text):
            for n, x in enumerate(self.code, 1):
                if not rx.search(x):
                    continue
                f = self.fn_at[n]
                r = self.of_function(f) if f else self.arm(n, rx)
                if r is None:
                    out = None
                    break
                out |= r
        self.memo_rx[rx.pattern] = out
        return out


class Reach:
    """Which groups a change to a file reaches: through the files that import it or name it (and those that import or
    name them, on and on), bin/vh's commands that name one of them and the groups that run those commands, and the
    groups of tools/ci.sh that name one. A file is named by its name when no other file has that name, else by its
    folder and name (or by its name from a file in the same folder)."""

    def __init__(self, groups):
        self.groups = groups
        names = [f for f in git("ls-files", "-z").split("\0") if f and not f.startswith(SKIP) and "/node_modules/" not in f]
        self.files = names
        self.code, self.imports = {}, {}
        for f in names:
            if f.endswith(CODE) and f != CI:
                try:
                    self.code[f], self.imports[f] = code_text(f, (ROOT / f).read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    pass
        count = {}
        for f in names:
            count[Path(f).name] = count.get(Path(f).name, 0) + 1
        self.unique = {n for n, c in count.items() if c == 1}
        stems = {}
        for f in names:
            if f.endswith(".py"):
                stems[Path(f).stem] = stems.get(Path(f).stem, 0) + 1
        self.unique_stem = {n for n, c in stems.items() if c == 1}
        self.ci = Script((ROOT / CI).read_text(encoding="utf-8"), groups)
        # tools/ci.sh's own lines, but its comments and its dispatch (from usage= on: it picks which groups run, the
        # groups' code is above it)
        disp = next((i for i, x in enumerate(self.ci.lines) if x.startswith("usage=")), len(self.ci.lines))
        self.ci_code = ["" if x.lstrip().startswith("#") or i >= disp else x for i, x in enumerate(self.ci.lines)]
        self.ci_text = "\n".join(self.ci_code)
        try:
            commands = {c["name"] for c in json.loads((ROOT / "tools/commands.json").read_text(encoding="utf-8"))["commands"]}
        except (OSError, ValueError, KeyError):
            commands = set()
        self.vh = VhScript((ROOT / "bin/vh").read_text(encoding="utf-8"), commands)
        self.runs = {g: set() for g in groups}   # the bin/vh commands each group runs (a helper's go to the groups that call it)
        for f in self.ci.fns:
            gs = self.ci.of_function(f)
            if ALL not in gs:
                cmds = set(re.findall(r"(?:\bvh|bin/vh)[\"']?[\s,(]+[\"']?([a-z][a-z0-9-]*)", self.ci.body[f])) & commands
                for g in gs & set(groups):
                    self.runs[g] |= cmds
        self.memo_users, self.memo_direct = {}, {}

    def file_rx(self, f):
        p = Path(f)
        return name_rx(p.name) if p.name in self.unique else word_rx(f"{p.parent.name}/{p.name}", re.escape(f"{p.parent.name}/{p.name}"))

    def users(self, node, rx):
        """The code files that use node: name it (rx), name it from its own folder, or import it."""
        if node in self.memo_users:
            return self.memo_users[node]
        p, out = Path(node), []
        bare = name_rx(p.name)
        stem = p.stem if node.endswith(".py") else None
        needle = needle_of(rx)
        for u, text in self.code.items():
            if u == node:
                continue
            same = Path(u).parent == p.parent and not node.startswith("token:")
            imp = stem and stem in self.imports[u] and (stem in self.unique_stem or same or p.parent.name in self.imports[u])
            if imp or (needle in text and rx.search(text)) or (same and p.name in text and bare.search(text)):
                out.append(u)
        self.memo_users[node] = out
        return out

    def direct(self, node, rx):
        """{group: how} the lines of tools/ci.sh and the commands of bin/vh that name node (rx) reach."""
        if node in self.memo_direct:
            return self.memo_direct[node]
        got = {}
        if rx.search(self.ci_text):
            for n, x in enumerate(self.ci_code, 1):
                if x and rx.search(x):
                    for g in self.ci.of_line(n):
                        got.setdefault(g, CI)
        cmds = self.vh.commands_naming(rx)
        if cmds is None:
            got[ALL] = "bin/vh, outside any one command"
        else:
            for g in self.groups:
                if self.runs[g] & cmds:
                    got.setdefault(g, f"bin/vh {sorted(self.runs[g] & cmds)[0]}")
        self.memo_direct[node] = got
        return got

    def reach(self, start, rx=None):
        """{group: how it is reached} for a change to start (a path, or token:… with rx for what a row names); ALL among
        the groups when every group is."""
        got, seen = {}, {start}
        queue = [(start, rx or self.file_rx(start), start.replace("token:", ""))]
        while queue and ALL not in got:
            node, nrx, chain = queue.pop(0)
            for g, why in self.direct(node, nrx).items():
                got.setdefault(g, f"{chain} ← {why}")
            for u in self.users(node, nrx):
                if u not in seen:
                    seen.add(u)
                    queue.append((u, self.file_rx(u), f"{chain} ← {u}"))
        return got


def row_reach(reach, pattern, files):
    """{group: how} a change to the files a row matches reaches: each code file by itself, the rest by what names the
    row's folder (or its one file)."""
    got = {}
    for f in files:
        if f.endswith(CODE):
            for g, why in reach.reach(f).items():
                got.setdefault(g, why)
    if any(not f.endswith(CODE) for f in files):
        lit = re.split(r"[*?]", pattern)[0].rstrip("/")
        if lit == pattern:   # one file
            rx = reach.file_rx(lit) if "/" in lit else root_rx(lit)
        else:
            rx = folder_rx(lit[len("tools/"):] if lit.startswith("tools/") else lit.split("/")[0])
        for g, why in reach.reach("token:" + pattern, rx).items():
            got.setdefault(g, why)
    return got


def suggest():
    """Each line of the path table as its files' reach says it should be: the groups it must name, or ALL."""
    groups = table_groups(ROOT / SHARDS)
    always, rows = path_table(ROOT / PATHS)
    reach = Reach(groups)
    for pat, rx, gs in rows:
        if ALL in gs:
            print(f"{pat:<28}ALL")
            continue
        got = row_reach(reach, pat, [f for f in reach.files if rx.match(f)])
        need = "ALL" if ALL in got else " ".join(g for g in groups if g in got and g not in always)
        print(f"{pat:<28}{need}" + ("" if need == "ALL" or set(need.split()) <= set(gs) else "   # was: " + " ".join(gs)))
    return 0


def check():
    problems = []
    groups = table_groups(ROOT / SHARDS)
    always, rows = path_table(ROOT / PATHS)
    named = always + [g for r in rows for g in r[2]]
    problems += [f"{PATHS}: {g} is no group of {SHARDS}" for g in sorted(set(named)) if g != ALL and g not in groups]
    tracked = git("ls-files", "-z").split("\0")
    problems += [f"{PATHS}: {pat} matches no file git tracks" for pat, rx, _ in rows if not any(rx.match(f) for f in tracked)]
    # a narrow line covers every group its files reach (Reach): one that reaches more says which and how
    reach = Reach(groups)
    for pat, rx, gs in rows:
        if ALL in gs:
            continue
        got = row_reach(reach, pat, [f for f in reach.files if rx.match(f)])
        if ALL in got:
            problems.append(f"{PATHS}: {pat} reaches every group ({got[ALL]}): make it ALL or take the line out")
            continue
        miss = [g for g in groups if g in got and g not in gs and g not in always]
        if miss:
            problems.append(f"{PATHS}: {pat} also reaches {', '.join(miss)} (" + "; ".join(f"{g}: {got[g]}" for g in miss[:3]) + ")")
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
    print(f"{PATHS}: {len(rows)} patterns, each matching a tracked file, naming groups of {SHARDS}, each narrow one every "
          f"group its files reach (imports, names, bin/vh commands, {CI}); {CI}: bash finds "
          f"all {len(groups)} groups, a line inside each maps to it alone, the dispatch to every group")
    return 0


def main():
    a = sys.argv[1:]
    try:
        if a == ["--check"]:
            sys.exit(check())
        if a == ["--suggest"]:
            sys.exit(suggest())
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
