"""Ways out of what a check finds (tools/remedies.json): what to look at next, never a verdict. Stdlib only.

usage: python3 tools/remedies.py check      the table against its rules (tools/ci.sh)
       python3 tools/remedies.py show <kind…>   the entries of these kinds, as bin/vh check prints them

for_kind(kind) → the entries of one finding kind ([] when it has none); lines(findings) → the lines bin/vh check prints
after its results: one block a kind, for the warnings and failures not confirmed in confirmed.json, in the order the
kinds were found. The rules (check): each kind is one tools/checkrec.py writes (its docstring lists them) or one named
in kinds_to_come (a check another branch adds); each entry has say, and a run that names a real bin/vh command
(tools/commands.json) or a doc that is a file in the repo (its #section a heading in it); a `bin/vh recipes list`
filter finds at least one recipe.
"""
import json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLE = HERE / "remedies.json"
_table = None


def table():
    global _table
    if _table is None:
        _table = json.loads(TABLE.read_text(encoding="utf-8"))
    return _table


def for_kind(kind):
    return [dict(e) for e in table()["kinds"].get(kind, [])]


def lines(findings):
    """The lines for the findings bin/vh check would have the reader act on: not info, not confirmed."""
    seen, out = [], []
    for f in findings:
        k = f.get("kind")
        if f.get("severity") not in ("fail", "warn") or f.get("confirmed") or k in seen or not for_kind(k):
            continue
        seen.append(k)
    if not seen:
        return []
    out.append("→ ways out (tools/remedies.json: options to look at, not rules):")
    for k in seen:
        n = sum(1 for f in findings if f.get("kind") == k and f.get("severity") in ("fail", "warn") and not f.get("confirmed"))
        head = f"   {k.split('.', 1)[-1]} ({n}): "
        for i, e in enumerate(for_kind(k)):
            what = e.get("run") or e.get("doc")
            out.append((head if i == 0 else " " * len(head)) + f"{e['say']} · {what}")
    return out


def checkrec_kinds():
    """The kinds tools/checkrec.py writes, read from its docstring's kind paragraph; None when that paragraph is not found."""
    doc = (HERE / "checkrec.py").read_text(encoding="utf-8")
    a, b = doc.find("kind      "), doc.find("severity  ")
    if a < 0 or b < a:
        return None
    return set(re.findall(r"\bcheck\.[a-z]+", doc[a:b]))


def heading_slugs(path):
    """GitHub's anchors for a markdown file's headings (lowercase, spaces to -, punctuation but - and _ dropped)."""
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"#{1,6}\s+(.*)", line)
        if m:
            s = re.sub(r"[^\w\- ]", "", m.group(1).strip().lower()).replace(" ", "-")
            out.add(s)
    return out


def check():
    bad = []
    t = table()
    if t.get("version") != 1 or not isinstance(t.get("kinds"), dict):
        return ["tools/remedies.json: version 1 and a kinds object"]
    kinds = checkrec_kinds()
    if kinds is None:   # a sentence, not a traceback, when checkrec.py's docstring is reworded
        bad.append("tools/checkrec.py: its docstring has no `kind      …` paragraph before `severity  `, where the kinds of finding are listed")
        kinds = set()
    known = kinds | set(t.get("kinds_to_come") or {})
    cmds = {c["name"] for c in json.loads((HERE / "commands.json").read_text(encoding="utf-8"))["commands"]}
    for kind, entries in t["kinds"].items():
        if kind not in known:
            bad.append(f"{kind}: not a kind tools/checkrec.py writes, nor in kinds_to_come")
        for e in entries if isinstance(entries, list) else [None]:
            if not isinstance(e, dict) or not isinstance(e.get("say"), str) or not e["say"].strip():
                bad.append(f"{kind}: an entry without say")
                continue
            if bool(e.get("run")) == bool(e.get("doc")):
                bad.append(f"{kind}: {e['say']!r} needs one of run and doc")
            if e.get("run"):
                w = e["run"].split()
                if w[:1] != ["bin/vh"] or len(w) < 2 or w[1] not in cmds:
                    bad.append(f"{kind}: run {e['run']!r} is not a bin/vh command")
                elif w[1:3] == ["recipes", "list"]:
                    r = subprocess.run([sys.executable, str(HERE / "recipes.py"), "list"] + w[3:], capture_output=True, text=True)
                    m = re.search(r"(\d+) of \d+ recipes", r.stdout + r.stderr)
                    if r.returncode != 0 or not m or m.group(1) == "0":
                        bad.append(f"{kind}: {e['run']!r} finds no recipe")
            if e.get("doc"):
                f, _, sec = e["doc"].partition("#")
                p = ROOT / f
                if not p.is_file():
                    bad.append(f"{kind}: doc {f} is not a file in the repo")
                elif sec and sec not in heading_slugs(p):
                    bad.append(f"{kind}: doc {e['doc']}: no heading {sec!r} in it")
    return bad


def main(argv):
    if argv[:1] == ["check"]:
        bad = check()
        for b in bad:
            print(b, file=sys.stderr)
        if not bad:
            print(f"tools/remedies.json: {len(table()['kinds'])} kinds, each entry a real command, recipe filter or doc")
        return 1 if bad else 0
    if argv[:1] == ["show"] and len(argv) > 1:
        print("\n".join(lines([{"kind": k, "severity": "warn"} for k in argv[1:]])))
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
