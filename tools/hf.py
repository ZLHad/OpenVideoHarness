"""bin/vh hf: HyperFrames' registry of blocks and components, at the version this repo pins. Stdlib only.

usage: bin/vh hf catalog [words…] [--type block|component] [--tag T] [--json] [--refresh] [--offline DIR]
       bin/vh hf add <project> <name> [--force] [--vars JSON] [--json] [--offline DIR]

  catalog  the registry's blocks and components as the pinned version's tag has them (tools/modules.json pins
           hyperframes; the registry is raw.githubusercontent.com/heygen-com/hyperframes/v<pin>/registry): name, type,
           title, tags, a block's length and frame, the licence when the item names one. Each word must appear in the
           name, the title, the description or a tag (any case). The list is kept in ~/.cache/ovh/hyperframes-registry/
           v<pin>.json, since a tag does not move; --refresh reads it again. The registry has examples too; they are
           whole projects (hyperframes init --example), not something to add, so they are left out, as HyperFrames'
           own catalog does.
  add      install a block or a component into a project with HyperFrames' own add (the items it depends on too),
           after pointing the project's hyperframes.json at the pinned tag: HyperFrames reads the newest registry on
           GitHub's main otherwise, which moves under a project. Then each file it wrote goes into the project's ledger
           (assets/ledger.json, tools/assets): its sha256, the item's licence (the item's own, else the repository's
           Apache-2.0, which covers the registry), where it came from and who made it. A file the item fetches from
           elsewhere (its own https URL) and that names no licence is recorded as unknown: assets check says so until
           it is cleared. The files are scanned for what hard rule 1 asks a page not to use (CSS @keyframes, animation
           and transition, Math.random, Date.now, new Date, performance.now, requestAnimationFrame, timers) and for
           what they load from the network when the film renders (an offline render hangs on it: vendor it). Both are
           warnings: HyperFrames' runtime seeks CSS animations and bin/vh's host holds them and the clock at t, so run
           bin/vh determinism <project> to see whether the frames still hold. --force: overwrite a file edited since it
           was installed (HyperFrames keeps it otherwise). --vars: values baked into a block's snippet (JSON, as a
           catalog page gives them).
           The command HyperFrames runs is the project's own (node_modules/.bin/hyperframes, which bin/vh hf-init
           pins), else npx hyperframes@<pin>; a project on another version is said.
--offline DIR: no network. catalog and add read the registry from DIR/responses.json (recorded with OVH_RECORD,
CONTRIBUTING.md 联网的命令), and add writes the item's files itself, by HyperFrames' rules (dependencies first, targets
under hyperframes.json's paths, an edited file kept unless --force, the items recorded in hyperframes.json's
registryItems), instead of running HyperFrames, which fetches by itself. --vars needs HyperFrames: not offline.
--json: catalog {"version": 1, "tool", "pin", "registry", "items": [{name, type, title, description, tags, license,
duration, dimensions, author}]}; add {"version": 1, "tool", "pin", "registry", "project", "name", "type",
"installed", "written", "preserved", "records", "scan", "snippet", "warnings"}. The lines go to stderr.
Exit: 0 · 1 a fetch failed, or HyperFrames' add did · 2 usage: no project, no such item, an example.
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "assets"))
sys.path.insert(0, str(HERE))
import fetch, ledger   # noqa: E402,E401

PROG = "bin/vh hf"
REPO = "https://raw.githubusercontent.com/heygen-com/hyperframes"
DEFAULT_REGISTRY = REPO + "/main/registry"   # what HyperFrames' own config falls back to
TYPE_DIRS = {"hyperframes:block": "blocks", "hyperframes:component": "components", "hyperframes:example": "examples"}
PATHS = {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}   # hyperframes.json's defaults
SCAN_EXT = {".html", ".htm", ".js", ".mjs", ".css", ".json", ".svg"}
# hard rule 1 (CLAUDE.md): what a page must not lean on; each a warning, with the line it is on
CLOCK = [("CSS @keyframes", r"@keyframes\b"), ("CSS animation", r"(?<![\w-])animation(?:-name)?\s*:"),
         ("CSS transition", r"(?<![\w-])transition\s*:"), ("Math.random", r"\bMath\.random\s*\("),
         ("Date.now", r"\bDate\.now\s*\("), ("new Date", r"\bnew\s+Date\s*\("), ("performance.now", r"\bperformance\.now\s*\("),
         ("requestAnimationFrame", r"\brequestAnimationFrame\s*\("), ("a timer", r"\bset(?:Timeout|Interval)\s*\(")]
# a load from the network when the page renders (an attribute, a CSS url(), an import, a fetch): not the xmlns of an SVG
NET = re.compile(r"""(?:\b(?:src|href)\s*=\s*["']?|url\(\s*["']?|\bimport\s*(?:[\w*{}\s,]+from\s*)?["']|\bfetch\(\s*["'])(https?://[^"')\s>]+)""", re.I)
out = sys.stdout


class Usage(Exception):
    """A usage error: exit 2."""


def say(*a):
    print(*a, file=out)


def pin():
    """The version bin/vh pins (tools/modules.json's hyperframes), or HYPERFRAMES_VERSION when that is set, as bin/vh does."""
    if os.environ.get("HYPERFRAMES_VERSION"):
        return os.environ["HYPERFRAMES_VERSION"]
    mods = json.loads((HERE / "modules.json").read_text(encoding="utf-8"))["modules"]
    return next(m for m in mods if m["name"] == "hyperframes")["version"]["pin"]


def registry_of(version):
    return f"{REPO}/v{version}/registry"


def item_url(base, typ, name, path="registry-item.json"):
    return f"{base}/{TYPE_DIRS[typ]}/{name}/{path}"


def cache_file(version):
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "ovh" / "hyperframes-registry" / f"v{version}.json"


def load_registry(version, opener, refresh=False, offline=False):
    """Every item of the tag's registry with its manifest: [{name, type, title, …}], examples included. Cached per tag."""
    cf = cache_file(version)
    if not refresh and not offline and cf.is_file():
        try:
            d = json.loads(cf.read_text(encoding="utf-8"))
            if d.get("version") == 1 and d.get("pin") == version and isinstance(d.get("items"), list):
                return d["items"]
        except (OSError, ValueError):
            pass
    base = registry_of(version)
    man = fetch.get_json(base + "/registry.json", opener=opener)
    entries = [e for e in man.get("items", []) if isinstance(e, dict) and e.get("type") in TYPE_DIRS and valid_name(e.get("name"))]
    say(f"{PROG}: reading {len(entries)} items of the v{version} registry …")

    def one(e):
        it = fetch.get_json(item_url(base, e["type"], e["name"]), opener=opener)
        return it if isinstance(it, dict) and it.get("name") == e["name"] else {"name": e["name"], "type": e["type"], "unreadable": True}
    with ThreadPoolExecutor(max_workers=1 if offline else 16) as ex:
        items = list(ex.map(one, entries))
    if not offline:
        try:
            cf.parent.mkdir(parents=True, exist_ok=True)
            tmp = cf.with_suffix(".part")
            tmp.write_text(json.dumps({"version": 1, "pin": version, "registry": base, "fetched_at": ledger.iso(), "items": items},
                                      ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, cf)
        except OSError as e:
            say(f"{PROG}: could not keep the list in {cf} ({e}); it is read again next time")
    return items


def valid_name(n):
    return isinstance(n, str) and len(n) <= 128 and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", n) is not None


def short_type(t):
    return t.split(":", 1)[-1] if isinstance(t, str) else "?"


def summary(it):
    keep = ("name", "type", "title", "description", "tags", "license", "author", "duration", "dimensions", "registryDependencies", "minCliVersion", "deprecated")
    return {k: it[k] for k in keep if k in it}


# ---- catalog ----

def cmd_catalog(a):
    version = pin()
    opener = fetch.opener_from(a.offline)
    try:
        items = load_registry(version, opener, refresh=a.refresh, offline=bool(a.offline))
    except fetch.FetchError as e:
        say(f"{PROG} catalog: {e}")
        return 1
    want = {"block": "hyperframes:block", "component": "hyperframes:component"}.get(a.type)
    words = [w.lower() for w in a.words]
    hits = []
    for it in items:
        if it.get("type") == "hyperframes:example" or (want and it.get("type") != want):
            continue
        tags = [str(t).lower() for t in it.get("tags") or []]
        if a.tag and a.tag.lower() not in tags:
            continue
        hay = " ".join([it.get("name", ""), str(it.get("title", "")), str(it.get("description", ""))] + tags).lower()
        if all(w in hay for w in words):
            hits.append(it)
    hits.sort(key=lambda it: (it.get("type", ""), it.get("name", "")))
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} catalog", "pin": version, "registry": registry_of(version),
                          "query": {"words": a.words, "type": a.type, "tag": a.tag}, "items": [summary(it) for it in hits]},
                         ensure_ascii=False, indent=1))
    n_all = sum(1 for it in items if it.get("type") != "hyperframes:example")
    for it in hits:
        extra = []
        if it.get("type") == "hyperframes:block":
            d, dim = it.get("duration"), it.get("dimensions") or {}
            extra.append((f"{d:g} s" if isinstance(d, (int, float)) else "") + (f" {dim.get('width')}x{dim.get('height')}" if dim else ""))
        if it.get("license"):
            extra.append(it["license"])
        if it.get("deprecated"):
            extra.append("deprecated")
        tags = ", ".join(it.get("tags") or [])
        line = f"  {it.get('name', ''):30} {short_type(it.get('type')):9} {str(it.get('title', ''))[:44]:44}"
        say(line + (f"  [{tags}]" if tags else "") + (f"  {' · '.join(x for x in extra if x)}" if any(extra) else ""))
    unread = sum(1 for it in items if it.get("unreadable"))
    say(f"{PROG} catalog: {len(hits)} of {n_all} (blocks and components, HyperFrames v{version}; examples left out)"
        + (f"; {unread} manifest(s) unreadable" if unread else "") + ". Install one: bin/vh hf add <project> <name>")
    return 0


# ---- add ----

def find_project(arg):
    p = Path(arg).expanduser()
    if p.exists():
        proj = ledger.project_of(p if p.is_dir() else p.parent)
        if proj is None:
            raise Usage(f"{arg} is not in a project (no BRIEF.md at or above it)")
        return proj
    from vhdraw import project_dir, Usage as NameUsage
    try:
        proj = project_dir(arg)
    except (NameUsage, SystemExit) as e:
        raise Usage(str(e))
    if not (proj / "BRIEF.md").is_file():
        raise Usage(f"{proj} is not a project (no BRIEF.md)")
    return proj


def read_config(project):
    f = project / "hyperframes.json"
    if not f.is_file():
        return f, None
    try:
        d = json.loads(f.read_text(encoding="utf-8").lstrip("﻿"))
    except ValueError as e:
        raise Usage(f"{f}: not JSON ({e})")
    if not isinstance(d, dict):
        raise Usage(f"{f}: not a JSON object")
    return f, d


def pin_registry(project, base):
    """Point hyperframes.json at the pinned tag's registry. → (the registry it now reads, a note or None). A registry
    that is neither HyperFrames' default nor another of its tags is the project's own choice: kept, and said."""
    f, d = read_config(project)
    if d is None:
        if not (project / "index.html").is_file():
            raise Usage(f"{project} has no hyperframes.json nor index.html: bin/vh hf-init {project} first")
        d = {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json", "registry": base, "paths": dict(PATHS)}
        f.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        return base, f"wrote {f.name} (registry: v{base.split('/v', 1)[1].split('/')[0]})"
    cur = d.get("registry")
    if cur == base:
        return base, None
    if cur in (None, DEFAULT_REGISTRY, DEFAULT_REGISTRY + "/") or (isinstance(cur, str) and cur.startswith(REPO + "/v")):
        d["registry"] = base
        indent = re.search(r"\n([ \t]+)\"", f.read_text(encoding="utf-8"))
        f.write_text(json.dumps(d, indent=indent.group(1) if indent else 2, ensure_ascii=False) + "\n", encoding="utf-8")
        return base, f"{f.name}: registry {cur or '(HyperFrames default: main)'} → the pinned tag"
    return cur, f"{f.name} names its own registry ({fetch.redact(cur)}): kept; the ledger records what it served"


def resolve(name, base, opener, seen=None):
    """The item and the items it depends on, dependencies first (as HyperFrames installs them)."""
    seen = set() if seen is None else seen
    if name in seen:
        return []
    seen.add(name)
    man = fetch.get_json(base + "/registry.json", opener=opener)
    entry = next((e for e in man.get("items", []) if isinstance(e, dict) and e.get("name") == name), None)
    if entry is None or entry.get("type") not in TYPE_DIRS:
        raise Usage(f"no {name!r} in the registry ({base}): bin/vh hf catalog lists them")
    it = fetch.get_json(item_url(base, entry["type"], name), opener=opener)
    if not isinstance(it, dict) or it.get("name") != name or not isinstance(it.get("files"), list):
        raise fetch.FetchError(f"{name}: the registry's manifest is not one ({item_url(base, entry['type'], name)})")
    plan = []
    for dep in it.get("registryDependencies") or []:
        plan += resolve(dep, base, opener, seen)
    return plan + [it]


def target_of(item, file, paths):
    """Where a file lands in the project: its target, under hyperframes.json's paths (HyperFrames' remapTarget)."""
    t = str(file.get("target", ""))
    if item["type"] == "hyperframes:block":
        t = re.sub(r"^compositions/", paths.get("blocks", PATHS["blocks"]).rstrip("/") + "/", t)
    elif item["type"] == "hyperframes:component":
        t = re.sub(r"^compositions/components/", paths.get("components", PATHS["components"]).rstrip("/") + "/", t)
    parts = Path(t).parts
    if not t or Path(t).is_absolute() or ".." in parts or re.match(r"^[A-Za-z]:[\\/]", t):
        raise fetch.FetchError(f"{item['name']}: an unsafe target {t!r}")
    return t


def source_url(base, item, file):
    return file["url"] if file.get("url") else item_url(base, item["type"], item["name"], file["path"])


def install_offline(project, plan, base, opener, force):
    """HyperFrames' add without HyperFrames: the files from the recorded responses, written by its rules."""
    _, d = read_config(project)
    paths = {**PATHS, **((d or {}).get("paths") or {})}
    written, preserved = [], []
    stage = []
    for it in plan:
        for fl in it["files"]:
            t = target_of(it, fl, paths)
            r = opener.open(source_url(base, it, fl))
            try:
                if r.status != 200:
                    raise fetch.FetchError(f"{fetch.redact(source_url(base, it, fl))}: HTTP {r.status}")
                body = r.read()
            finally:
                r.close()
            stage.append((project / t, body))
    for dest, body in stage:
        if dest.exists() and not force and dest.read_bytes() != body:
            preserved.append(str(dest))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        written.append(str(dest))
    f, d = read_config(project)
    d = d or {}
    have = [x for x in d.get("registryItems") or [] if isinstance(x, dict)]
    for it in plan:
        prim = next((fl for fl in it["files"] if fl.get("type") == "hyperframes:snippet"), None) \
            or next((fl for fl in it["files"] if fl.get("type") == "hyperframes:composition"), None) or it["files"][0]
        rec = {"name": it["name"], "type": it["type"], "target": target_of(it, prim, paths)}
        have = [x for x in have if x.get("name") != it["name"]] + [rec]
    d["registryItems"] = have
    f.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    item = plan[-1]
    prim_t = next((x["target"] for x in have if x["name"] == item["name"]), "")
    snippet = (f'<div data-composition-src="{prim_t}" data-duration="{item.get("duration")}"></div>' if item["type"] == "hyperframes:block"
               else f"<!-- paste from {prim_t} into your composition -->")
    return {"ok": True, "name": item["name"], "type": item["type"], "written": written, "preserved": preserved,
            "installed": [it["name"] for it in plan], "snippet": snippet, "warnings": []}


def hf_command(project, version):
    """HyperFrames' CLI to run: the project's own, else npx at the pin. → (argv, its version or None)."""
    local = project / "node_modules" / ".bin" / "hyperframes"
    if local.exists():
        v = None
        pj = project / "node_modules" / "hyperframes" / "package.json"
        if pj.is_file():
            try:
                v = json.loads(pj.read_text(encoding="utf-8")).get("version")
            except ValueError:
                v = None
        return [str(local)], v
    if not shutil.which("npx"):
        raise Usage("no node_modules/.bin/hyperframes in the project and no npx: bin/vh hf-init the project, or install Node")
    return ["npx", "--yes", f"hyperframes@{version}"], version


def install_online(project, name, version, force, vars_):
    argv, v = hf_command(project, version)
    cmd = argv + ["add", name, "--dir", str(project), "--json", "--no-clipboard"] + (["--force"] if force else []) + \
        (["--vars", vars_] if vars_ else [])
    env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1", DO_NOT_TRACK="1", HYPERFRAMES_NO_UPDATE_CHECK="1", NO_COLOR="1")
    r = subprocess.run(cmd, cwd=str(project), capture_output=True, text=True, env=env, timeout=600)
    res = None
    for line in reversed(r.stdout.strip().splitlines()):
        try:
            res = json.loads(line)
            break
        except ValueError:
            continue
    if r.returncode != 0 or not isinstance(res, dict) or not res.get("ok"):
        why = (res or {}).get("error") or (res or {}).get("message") or (r.stderr.strip().splitlines() or [f"exit {r.returncode}"])[-1]
        raise fetch.FetchError(f"HyperFrames' add {name} failed: {why}")
    return res, v


def scan(project, files):
    """{relpath: [{"what", "line", "text"}]} for the lines that lean on the clock or the network (warnings)."""
    found = {}
    for f in files:
        p = Path(f)
        if p.suffix.lower() not in SCAN_EXT or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            for what, pat in CLOCK:
                if re.search(pat, line):
                    hits.append({"what": what, "line": i, "text": line.strip()[:120]})
            for m in NET.finditer(line):
                if "www.w3.org/" not in m.group(1):
                    hits.append({"what": "loads from the network", "line": i, "text": fetch.redact(m.group(1))})
        if hits:
            found[ledger.rel(project, p)] = hits
    return found


def record(project, files, plan, base, version):
    """Each file written into the project's ledger: a new record, or the one at its path updated (--force)."""
    recs = []
    by_target = {}
    _, d = read_config(project)
    paths = {**PATHS, **((d or {}).get("paths") or {})}
    for it in plan:
        for fl in it["files"]:
            by_target[(project / target_of(it, fl, paths)).resolve()] = (it, fl)
    lic_url = f"https://github.com/heygen-com/hyperframes/blob/v{version}/LICENSE"
    for f in files:
        p = Path(f).resolve()
        it, fl = by_target.get(p, (plan[-1], {}))
        lic, cls, note = it.get("license"), None, None
        if not lic and fl.get("url"):
            cls, note = "unknown", f"fetched from {fetch.redact(fl['url'])}, outside the registry's repository; the item names no licence for it"
        elif not lic:
            lic = "Apache-2.0"
        src = {"origin": "download", "url": item_url(base, it["type"], it["name"]), "file_url": source_url(base, it, fl) if fl else None,
               "provider": "hyperframes-registry", "provider_id": it["name"], "title": it.get("title"),
               "author": it.get("author") or "HeyGen, Inc. (heygen-com/hyperframes)", "retrieved": time.strftime("%Y-%m-%d")}
        credit = f"{it.get('title') or it['name']}: HyperFrames registry (heygen-com/hyperframes v{version}, {lic or 'licence not stated'})"
        at = ledger.rel(project, p)
        on = any(r.get("path") == at and "removed" not in r for r in ledger.read_ledger(project / ledger.LEDGER)["assets"] if isinstance(r, dict))
        rec, _, _ = ledger.add(project, str(p), license=lic, license_url=lic_url if lic and not it.get("license") else None,
                               license_class=cls, source=src, attribution=credit, tags=["hyperframes", short_type(it["type"])],
                               note=note, update=on, by=f"{PROG} add")
        recs.append(rec)
    return recs


def cmd_add(a):
    version = pin()
    project = find_project(a.project)
    if not valid_name(a.name):
        raise Usage(f"{a.name!r} is not a registry name (lowercase letters, digits and -)")
    if a.vars and a.offline:
        raise Usage("--vars is baked in by HyperFrames' add, which --offline does not run")
    base, note = pin_registry(project, registry_of(version))
    if note:
        say(f"{PROG} add: {note}")
    opener = fetch.opener_from(a.offline)
    try:
        plan = resolve(a.name, base, opener)
    except fetch.FetchError as e:
        say(f"{PROG} add: {e}")
        return 1
    item = plan[-1]
    if item["type"] == "hyperframes:example":
        raise Usage(f"{a.name} is an example, a whole project: npx hyperframes@{version} init <dir> --example {a.name}")
    warnings = []
    try:
        if a.offline:
            res, used = install_offline(project, plan, base, opener, a.force), version
        else:
            res, used = install_online(project, a.name, version, a.force, a.vars)
    except (fetch.FetchError, subprocess.TimeoutExpired) as e:
        say(f"{PROG} add: {e}")
        return 1
    if used and used != version:
        warnings.append(f"the project runs HyperFrames {used}; the registry is v{version}'s (bin/vh pins {version})")
    warnings += [str(w) for w in res.get("warnings") or []]
    written = [str(Path(p) if Path(p).is_absolute() else project / p) for p in res.get("written") or []]
    try:
        recs = record(project, written, plan, base, version)
    except (ledger.LedgerError, ledger.Refused, ValueError) as e:
        say(f"{PROG} add: installed, but the ledger refused a record: {e}")
        return 1
    found = scan(project, written)
    for at, hits in found.items():
        for h in hits:
            warnings.append(f"{at}:{h['line']}: {h['what']} ({h['text']})")
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} add", "pin": version, "registry": base, "project": str(project),
                          "name": item["name"], "type": item["type"], "installed": res.get("installed") or [it["name"] for it in plan],
                          "written": [ledger.rel(project, Path(p)) for p in written],
                          "preserved": [ledger.rel(project, Path(p)) for p in res.get("preserved") or []],
                          "records": [{"id": r["id"], "path": r["path"], "class": r["license"]["class"]} for r in recs],
                          "scan": found, "snippet": res.get("snippet") or "", "warnings": warnings}, ensure_ascii=False, indent=1))
    names = ", ".join(res.get("installed") or [item["name"]])
    say(f"{PROG} add: {names} → {ledger.rel(Path.cwd(), project) if project.is_relative_to(Path.cwd()) else project}"
        f" (HyperFrames v{used or version}, registry v{version})")
    for r in recs:
        say(f"  {r['path']}  {r['license']['class']}  (ledger id {r['id']})")
    for p in res.get("preserved") or []:
        say(f"  kept, edited since it was installed: {ledger.rel(project, Path(p))} (--force overwrites it)")
    if res.get("snippet"):
        say(f"  use it: {res['snippet']}")
    if found:
        say("  hard rule 1 and offline renders: the lines below are warnings; bin/vh determinism <project> says whether the frames still hold")
    for w in warnings:
        say(f"  ⚠ {w}")
    return 0


def parser():
    ap = argparse.ArgumentParser(prog=PROG, description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    sp = ap.add_subparsers(dest="cmd", metavar="{catalog,add}")
    p = sp.add_parser("catalog", prog=f"{PROG} catalog", help="the registry's blocks and components")
    p.add_argument("words", nargs="*")
    p.add_argument("--type", choices=("block", "component"))
    p.add_argument("--tag")
    p.add_argument("--refresh", action="store_true", help="read the registry again (the list is kept per tag)")
    p.add_argument("--offline", help="DIR: the registry's recorded responses")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("add", prog=f"{PROG} add", help="install one into a project, its files on the ledger")
    p.add_argument("project")
    p.add_argument("name")
    p.add_argument("--force", action="store_true", help="overwrite a file edited since it was installed")
    p.add_argument("--vars", help="JSON: variable values baked into a block's snippet")
    p.add_argument("--offline", help="DIR: the registry's recorded responses; the files are written without HyperFrames")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv):
    global out
    if not argv:
        parser().print_usage(sys.stderr)
        print(f"{PROG}: catalog or add", file=sys.stderr)
        return 2
    a = parser().parse_args(argv)
    if a.cmd is None:
        parser().print_usage(sys.stderr)
        return 2
    if a.json:
        out = sys.stderr
    try:
        return {"catalog": cmd_catalog, "add": cmd_add}[a.cmd](a)
    except Usage as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
