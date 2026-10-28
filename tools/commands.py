"""bin/vh's commands from one table, tools/commands.json: bin/vh -h, bin/vh <command> -h, bin/vh commands and the 命令行
line of CLAUDE.md are all printed from it (stdlib only).

usage: python3 tools/commands.py help                         bin/vh -h: every usage, by stage
       python3 tools/commands.py usage <command>              bin/vh <command> -h (exit 1: no such command)
       python3 tools/commands.py list [--stage S] [--json]    bin/vh commands
       python3 tools/commands.py unknown <word>               bin/vh's message for a command it does not have (exit 2)
       python3 tools/commands.py claude-line [--write FILE]   the names for CLAUDE.md's 命令行 line; --write puts them in
                                                              (bin/vh sync-agents does, then writes AGENTS.md)
       python3 tools/commands.py check                        the table against its rules and playbook/01 (tools/ci.sh)

The table: {"version": 1, "stages": [{"id", "name", "note"?}], "commands": [{"name", "summary", "when", "stages", "reads",
"writes", "usage": [{"synopsis", "text"}], "subcommands"?: [{"name", "summary"}]}]}. The stages are the 阶段 of
playbook/01-pipeline.md's 总表 (ids "0"–"9", their names as written there; check holds them to it), plus "env" (this
machine and the repo) and "any" (a project at any stage). A command's first stage is its main one, where bin/vh -h lists
it; every list prints the commands in that order (by first stage, then as in the file). reads and writes are text to
show, with placeholders (<project>/…, <x>), not paths to parse; a subcommand's name in angle brackets (<preset>) is a
placeholder too. bin/vh commands -h has the --json fields.
"""
import difflib, json, re, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "tools" / "commands.json"
PIPELINE = ROOT / "playbook" / "01-pipeline.md"
COL = 30        # where the descriptions start in bin/vh -h
WIDTH = 118     # bin/vh commands wraps its sentences here


def load(path=TABLE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ordered(t):
    """The commands by their first stage, then as in the file."""
    at = {s["id"]: i for i, s in enumerate(t["stages"])}
    return sorted(t["commands"], key=lambda c: at.get(c["stages"][0], len(at)))   # sorted() is stable


def in_stage(t, sid):
    """The commands of a stage: those listed under it first, then those listed under another that are used here too."""
    cmds = ordered(t)
    return [c for c in cmds if c["stages"][0] == sid] + [c for c in cmds if sid in c["stages"][1:]]


def stage_title(s):
    return f"{s['id']} {s['name']}" + (f" · {s['note']}" if s.get("note") else "")


def form_lines(f, first, indent):
    """One usage form: its synopsis behind `first`, its text below at `indent`; a short synopsis takes the first line of
    text beside it, at the same column."""
    out, text = [], list(f["text"])
    head = first + f["synopsis"]
    if text and len(head) < indent - 1:
        out.append(head.ljust(indent) + text.pop(0))
    else:
        out.append(head)
    out += [" " * indent + line for line in text]
    return out


def help_text(t):
    out = ["vh — OpenVideoHarness helper. Run from anywhere: bin/vh <command>",
           "The commands by the stages of playbook/01-pipeline.md (总表, 0–9), each under the first stage it is used in.",
           "bin/vh commands [--stage S] [--json]: what each one is for and when · bin/vh <command> -h: one command's usage"]
    cmds = ordered(t)
    for s in t["stages"]:
        here = [c for c in cmds if c["stages"][0] == s["id"]]
        if not here:
            continue
        out += ["", " " + stage_title(s)]
        for c in here:
            for f in c["usage"]:
                out += form_lines(f, "  ", COL)
    return "\n".join(out)


def usage_text(c):
    """bin/vh <command> -h: each form as "usage: bin/vh <synopsis>", its text below it."""
    out = []
    for f in c["usage"]:
        out += ["usage: bin/vh " + f["synopsis"]] + [" " * 14 + line for line in f["text"]]
    return "\n".join(out)


def find_stage(t, word):
    """A stage by its id, its name, or a part of its name (any case); None and the candidates when it is not one."""
    w = word.strip().lower()
    for s in t["stages"]:
        if w in (s["id"].lower(), s["name"].lower()):
            return s, []
    hits = [s for s in t["stages"] if w and w in s["name"].lower()]
    return (hits[0], []) if len(hits) == 1 else (None, hits)


def wrap(text, first, indent):
    return textwrap.wrap(text, WIDTH, initial_indent=first, subsequent_indent=" " * indent, break_on_hyphens=False,
                         break_long_words=False)


def list_text(t, stage=None):
    cmds, name_w = ordered(t), 16
    out = []
    if stage is None:
        out += ["bin/vh commands by the stages of playbook/01-pipeline.md. --stage <id or name>: one stage, with what each",
                "command reads and writes · bin/vh <command> -h: how to call it · --json: all of it, for a client"]
    for s in t["stages"]:
        if stage is not None and s is not stage:
            continue
        here = in_stage(t, s["id"]) if stage is not None else [c for c in cmds if c["stages"][0] == s["id"]]
        if not here:
            continue
        out += ["", stage_title(s)]
        for c in here:
            also = [x for x in c["stages"] if x != s["id"]]
            out += wrap(c["summary"] + (f" (also {', '.join(also)})" if also else ""), "  " + c["name"].ljust(name_w - 2), name_w)
            out += wrap("when: " + c["when"], " " * name_w, name_w + 6)
            if stage is None:
                continue
            for key in ("reads", "writes"):
                if c[key]:
                    out += wrap(f"{key}: " + "; ".join(c[key]), " " * name_w, name_w + len(key) + 2)
            if c.get("subcommands"):
                out += wrap("subcommands: " + " · ".join(f"{x['name']}: {x['summary']}" for x in c["subcommands"]), " " * name_w, name_w + 13)
    return "\n".join(out[1:] if stage is not None else out)


def claude_names(t):
    return " · ".join(c["name"] for c in ordered(t))


def write_claude(path, t):
    """Put the names in CLAUDE.md's one 命令行： line, after the colon; the rest of the file stays as it is."""
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    hits = re.findall(r"^.*命令行：.*$", s, re.M)
    if len(hits) != 1:
        sys.exit(f"{p}: {len(hits)} lines with 命令行：, not one")
    line = hits[0]
    new = line[:line.index("命令行：") + len("命令行：")] + claude_names(t)
    if new != line:
        p.write_text(s.replace(line, new, 1), encoding="utf-8")
    return new != line


def pipeline_stages(path=PIPELINE):
    """The 阶段 of playbook/01's 总表: [(id, name)] from its rows ("| 0 选路径 | …")."""
    s = Path(path).read_text(encoding="utf-8")
    table = s[s.index("## 总表"):]
    table = table[:table.index("\n## ", 1)]
    return re.findall(r"^\| (\d) ([^|]+?) \|", table, re.M)


def problems(t):
    """What breaks the table's rules, a line each."""
    bad = []
    if t.get("version") != 1:
        bad.append('"version" is not 1')
    stages = t.get("stages") or []
    ids = [s.get("id") for s in stages]
    if len(set(ids)) != len(ids):
        bad.append(f"stage ids repeat: {ids}")
    for s in stages:
        if not isinstance(s.get("id"), str) or not isinstance(s.get("name"), str) or not s["name"]:
            bad.append(f"a stage needs an id and a name: {s}")
    want = [(i, n) for i, n in pipeline_stages()]
    have = [(s["id"], s["name"]) for s in stages if str(s.get("id")).isdigit()]
    if have != want:
        bad.append(f"the numbered stages are not playbook/01's 总表: {have} vs {want}")
    known, names = set(ids), []
    for c in t.get("commands") or []:
        n = c.get("name")
        where = f"command {n!r}"
        if not isinstance(n, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", n):
            bad.append(f"{where}: the name is not lower-case letters, digits and -, a letter first"); continue
        names.append(n)
        for k in ("summary", "when"):
            if not isinstance(c.get(k), str) or not c[k].strip():
                bad.append(f"{where}: no {k}")
        st = c.get("stages")
        if not isinstance(st, list) or not st or len(set(st)) != len(st) or not set(st) <= known:
            bad.append(f"{where}: stages {st!r} are not distinct ids of the stages list")
        for k in ("reads", "writes"):
            if not isinstance(c.get(k), list) or not all(isinstance(x, str) and x for x in c[k]):
                bad.append(f"{where}: {k} is not a list of strings")
        forms = c.get("usage")
        if not isinstance(forms, list) or not forms:
            bad.append(f"{where}: no usage"); continue
        for f in forms:
            syn = f.get("synopsis") if isinstance(f, dict) else None
            if not isinstance(syn, str) or syn.split(" ")[0] != n:
                bad.append(f"{where}: a usage synopsis does not start with the name: {syn!r}")
            if not isinstance(f, dict) or not isinstance(f.get("text"), list) or not all(isinstance(x, str) for x in f["text"]):
                bad.append(f"{where}: a usage text is not a list of strings")
        words = " ".join(f.get("synopsis", "") + " " + " ".join(f.get("text", [])) for f in forms if isinstance(f, dict))
        for sub in c.get("subcommands", []):
            if not isinstance(sub, dict) or not isinstance(sub.get("name"), str) or not isinstance(sub.get("summary"), str):
                bad.append(f"{where}: a subcommand needs a name and a summary: {sub!r}")
            elif not re.search(r"(?<![\w-])" + re.escape(sub["name"]) + r"(?![\w-])", words):
                bad.append(f"{where}: its usage does not mention the subcommand {sub['name']!r}")
    if len(set(names)) != len(names):
        bad.append(f"names repeat: {sorted(n for n in set(names) if names.count(n) > 1)}")
    return bad


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip()); return 0
    what, rest = argv[0], argv[1:]
    t = load()
    if what == "help":
        print(help_text(t)); return 0
    if what == "usage":
        c = next((c for c in t["commands"] if rest and c["name"] == rest[0]), None)
        if c is None:
            return 1
        print(usage_text(c)); return 0
    if what == "unknown":
        word = rest[0] if rest else ""
        near = difflib.get_close_matches(word, [c["name"] for c in t["commands"]], n=3, cutoff=0.6)
        print(f"unknown command: {word}" + (f" (did you mean {' or '.join(near)}?)" if near else ""), file=sys.stderr)
        print("bin/vh commands lists the commands by stage, with what each is for; bin/vh -h every usage", file=sys.stderr)
        return 2
    if what == "list":
        stage, js, i = None, False, 0
        while i < len(rest):
            a = rest[i]
            if a == "--json":
                js = True
            elif a == "--stage" or a.startswith("--stage="):
                v = a.split("=", 1)[1] if "=" in a else (rest[i + 1] if i + 1 < len(rest) else None)
                i += 0 if "=" in a else 1
                if not v:
                    print("bin/vh commands: --stage needs a stage: an id (env, any, 0–9) or a part of its name", file=sys.stderr)
                    return 2
                stage, cands = find_stage(t, v)
                if stage is None:
                    some = cands or t["stages"]
                    print(f"bin/vh commands: {'more than one stage' if cands else 'no stage'} matches {v!r}: "
                          + " · ".join(f"{s['id']} {s['name']}" for s in some), file=sys.stderr)
                    return 2
            else:
                print(f"bin/vh commands: unknown option {a} (usage: bin/vh commands [--stage <stage>] [--json])", file=sys.stderr)
                return 2
            i += 1
        if js:
            out = {"version": 1, "stages": t["stages"], "commands": ordered(t)}
            if stage is not None:
                out = {"version": 1, "stage": stage["id"], "stages": t["stages"], "commands": in_stage(t, stage["id"])}
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(list_text(t, stage))
        return 0
    if what == "claude-line":
        if rest[:1] == ["--write"] and len(rest) == 2:
            changed = write_claude(rest[1], t)
            print(f"CLAUDE.md's 命令行 line {'rewritten from' if changed else 'already matches'} tools/commands.json ({len(t['commands'])} commands)")
            return 0
        print(claude_names(t)); return 0
    if what == "check":
        bad = problems(t)
        for b in bad:
            print(f"tools/commands.json: {b}", file=sys.stderr)
        if not bad:
            print(f"tools/commands.json: {len(t['commands'])} commands, {len(t['stages'])} stages")
        return 1 if bad else 0
    print(f"tools/commands.py: unknown {what!r}\n\n{__doc__.strip()}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
