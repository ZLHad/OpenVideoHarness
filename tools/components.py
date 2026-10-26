"""bin/vh components: the repo's motion components (components/README.md): list them, check them, copy them into a project,
render a component's sample. Stdlib only (check and add read component.js through node; sample runs the swatch renderer).

usage: bin/vh components [list] [--json]
       bin/vh components check
       bin/vh components add <project> <name…>
       bin/vh components sample <name> [--draft]

  list    each component: its painters (canvas, dom) and what it is for; --json gives every slots.json whole (the
          parameter tables: name, type, default, range, what it does)
  check   each component against its rules: component.js exports defaults, state() and the painters slots.json names,
          and its defaults are slots.json's; slots.json has a version, a name, painters and a slot for each default; a
          sample (sample/swatch.js, sample/tokens.json); provenance from another project has its licence copy in
          components/LICENSES/ and a row in components/NOTICE.md; no file of the library, a component or its sample
          leans on a clock or chance (tools/purity.py: Math.random, Date.now, new Date, performance.now,
          requestAnimationFrame, timers, CSS animations and transitions; hard rule 1)
  add     copy lib/ and the named components (component.js, slots.json) into <project>/components/, and print how the
          project's engine loads them (HyperFrames: a module script; canvas-film: lib/global.js, then OVH.<name> from
          its classic scripts). Copies made before are replaced: a component is the repo's, not the project's to edit;
          one the project changes is the project's own, under another name
  sample  render the component's sample (sample/swatch.js) with the style swatch renderer (styles/_swatch/render.sh, a
          5 s, 1920x1080 scene; --draft: HyperFrames' draft quality), keep its contact sheet as sample/media/sheet.jpg
          (in the repo: what the component looks like moving, for an agent to read) and the video beside it (not in git)
--json (list): {"version": 1, "tool", "components": [slots.json …]}. Exit: 0 · 1 check found a problem, a render failed ·
2 usage (no such component or project).
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import purity   # noqa: E402  tools/purity.py: hard rule 1's patterns
COMP = Path(os.environ.get("OVH_COMPONENTS") or ROOT / "components")   # another folder: the tests
PROG = "bin/vh components"
PAINTERS = {"canvas", "dom"}
TYPES = {"number", "string", "boolean", "array", "object", "null"}


class Usage(Exception):
    """A usage error: exit 2."""


def names():
    return sorted(d.name for d in COMP.iterdir() if d.is_dir() and (d / "slots.json").is_file())


def slots_of(name):
    return json.loads((COMP / name / "slots.json").read_text(encoding="utf-8"))


def exports_of(name):
    """What component.js exports, through node: {name: kind}, and defaults as JSON."""
    js = ("const m = await import(process.argv[1]); const out = {}; for (const [k, v] of Object.entries(m)) out[k] = typeof v;"
          "console.log(JSON.stringify({ exports: out, defaults: m.defaults ?? null }));")
    r = subprocess.run(["node", "--input-type=module", "-e", js, (COMP / name / "component.js").as_uri()], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"node exited {r.returncode}")
    return json.loads(r.stdout)


def check():
    bad = []
    notice = (COMP / "NOTICE.md").read_text(encoding="utf-8") if (COMP / "NOTICE.md").is_file() else ""
    for name in names():
        where = f"components/{name}"
        try:
            s = slots_of(name)
        except ValueError as e:
            bad.append(f"{where}/slots.json: not JSON ({e})")
            continue
        if s.get("version") != 1 or s.get("name") != name:
            bad.append(f"{where}/slots.json: version 1 and name {name!r}")
        painters = s.get("painters")
        if not isinstance(painters, list) or not painters or not set(painters) <= PAINTERS:
            bad.append(f"{where}/slots.json: painters, from {sorted(PAINTERS)}")
            painters = []
        if not isinstance(s.get("summary"), str) or not s["summary"].strip():
            bad.append(f"{where}/slots.json: a summary")
        sl = s.get("slots")
        if not isinstance(sl, list):
            bad.append(f"{where}/slots.json: slots, a list")
            sl = []
        for x in sl:
            if not isinstance(x, dict) or not x.get("name") or not x.get("text") or "default" not in x:
                bad.append(f"{where}/slots.json: a slot needs name, default and text: {x!r}"[:200])
                continue
            ts = set(str(x.get("type", "")).split("|"))
            if not ts <= TYPES:
                bad.append(f"{where}/slots.json: {x['name']}: type {x.get('type')!r} (of {sorted(TYPES)}, | between them)")
        try:
            ex = exports_of(name)
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as e:
            bad.append(f"{where}/component.js: does not load ({e})")
            continue
        e = ex["exports"]
        if e.get("state") != "function":
            bad.append(f"{where}/component.js: exports no state()")
        for pnt in painters:
            if e.get(pnt) != "function":
                bad.append(f"{where}/component.js: slots.json names the {pnt} painter, component.js exports no {pnt}()")
        d = ex.get("defaults")
        if not isinstance(d, dict):
            bad.append(f"{where}/component.js: exports no defaults")
        else:
            table = {x["name"]: x["default"] for x in sl if isinstance(x, dict) and "name" in x}
            for k, v in d.items():
                if k not in table:
                    bad.append(f"{where}: default {k} has no slot in slots.json")
                elif table[k] != v:
                    bad.append(f"{where}: {k}'s default is {json.dumps(v)} in component.js, {json.dumps(table[k])} in slots.json")
            for k in table:
                if k not in d:
                    bad.append(f"{where}/slots.json: slot {k} is not one of component.js's defaults")
        for f in ("sample/swatch.js", "sample/tokens.json"):
            if not (COMP / name / f).is_file():
                bad.append(f"{where}: no {f} (a 5 s sample, components/README.md)")
        for p in s.get("provenance") or []:
            if p.get("repo") == "this repository" or p.get("license") not in ("MIT", "Apache-2.0", "CC-BY-4.0"):
                continue
            repo = str(p.get("repo", "")).rstrip("/").split("/")[-1]
            if not (COMP / "LICENSES" / f"{p['license']}-{repo}.txt").is_file():
                bad.append(f"{where}: provenance {p.get('repo')}: no components/LICENSES/{p['license']}-{repo}.txt")
            if not p.get("commit") or not re.fullmatch(r"[0-9a-f]{7,40}", str(p["commit"])):
                bad.append(f"{where}: provenance {p.get('repo')}: the commit it was taken at")
            if f"`{name}/component.js`" not in notice and f"`{name}/" not in notice:
                bad.append(f"{where}: provenance {p.get('repo')}: no row for it in components/NOTICE.md")
    # hard rule 1 in every file a component is made of: tools/purity.py's table (also bin/vh hf add's and recipes check's)
    for f in sorted((COMP / "lib").glob("*.js")) + sorted(COMP.glob("*/component.js")) + sorted(COMP.glob("*/sample/*.js")):
        for what, i, _ in purity.scan(f.read_text(encoding="utf-8")):
            bad.append(f"{f.relative_to(COMP.parent)}:{i}: {what} (hard rule 1; a line may say purity-ok with its reason)")
    return bad


def find_project(arg):
    p = Path(arg).expanduser()
    if p.is_dir():
        return p.resolve()
    sys.path.insert(0, str(HERE))
    from vhdraw import project_dir, Usage as NameUsage
    try:
        return project_dir(arg)
    except (NameUsage, SystemExit) as e:
        raise Usage(str(e))


def add(project, wanted):
    unknown = [n for n in wanted if n != "lib" and n not in names()]
    if unknown:
        raise Usage(f"no such component: {', '.join(unknown)} (bin/vh components list)")
    dest = project / "components"
    dest.mkdir(exist_ok=True)
    shutil.copytree(COMP / "lib", dest / "lib", dirs_exist_ok=True)
    got = ["lib"]
    for n in [x for x in wanted if x != "lib"]:
        (dest / n).mkdir(exist_ok=True)
        for f in ("component.js", "slots.json"):
            shutil.copy2(COMP / n / f, dest / n / f)
        got.append(n)
    for n in [x for x in wanted if x != "lib"]:   # a component that imports another's file (paper-transition: page-turn's leaf)
        for dep in re.findall(r'from "\.\./([a-z0-9-]+)/component\.js"', (COMP / n / "component.js").read_text(encoding="utf-8")):
            if dep not in got:
                (dest / dep).mkdir(exist_ok=True)
                for f in ("component.js", "slots.json"):
                    shutil.copy2(COMP / dep / f, dest / dep / f)
                got.append(dep)
    print(f"{PROG} add: {', '.join(got)} → {dest}")
    first = next((x for x in got if x != "lib"), None)
    if (project / "hyperframes.json").is_file():
        print("  HyperFrames: in the composition, a module script, and the state drawn from the timeline's driver tween:")
        if first:
            print(f'    <script type="module">import * as {re.sub(r"[^a-z]", "", first)} from "./components/{first}/component.js"; …</script>')
        print("    (engines/README.md 最小写法: a paused timeline, a driver tween that calls your draw(t))")
    if (project / "film.html").is_file():
        print('  canvas-film: in film.html, before your scripts: <script type="module" src="components/lib/global.js"></script>')
        print("    then OVH.grain(X, t, {…}), OVH.paper(X, {…}) … from the classic scripts; in ready: OVH.setFrame({ w: W, h: H, fps: FILM.fps, dpr: PRX })")
    print("  the parameters: components/<name>/slots.json; what it looks like: the repo's components/<name>/sample/media/sheet.jpg")
    return 0


def sample(name, draft):
    if name not in names():
        raise Usage(f"no such component: {name} (bin/vh components list)")
    src = COMP / name / "sample"
    if not (src / "swatch.js").is_file():
        raise Usage(f"components/{name} has no sample/swatch.js")
    tmp = Path(tempfile.mkdtemp(prefix="vh-component-"))
    try:
        scene = tmp / name   # the renderer names the stage after the folder: the component's name, not "sample"
        shutil.copytree(src, scene, ignore=shutil.ignore_patterns("media"))
        r = subprocess.run([str(ROOT / "styles" / "_swatch" / "render.sh"), str(scene)] + (["--draft"] if draft else []))
        if r.returncode != 0:
            return 1
        media = src / "media"
        media.mkdir(exist_ok=True)
        for f in ("swatch.mp4", "poster.jpg"):
            if (scene / "media" / f).is_file():
                shutil.copy2(scene / "media" / f, media / f)
        sheet = ROOT / "styles" / "_swatch" / "out" / name / "sheet.png"
        at = (slots_of(name).get("sample") or {}).get("at")
        if at:   # the sample's own moments (slots.json sample.at): the middle of a turn, not every half second
            hf = ROOT / "styles" / "_swatch" / "out" / name / "hf.mp4"
            subprocess.run(["uv", "run", "-q", "--no-project", "--with", "pillow", "python", str(HERE / "sheet.py"), str(hf), str(sheet), "5", "2", "384"],
                           env=dict(os.environ, VH_SHEET_AT=",".join(str(x) for x in at)), check=True)
        if sheet.is_file():
            out = media / "sheet.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(sheet), "-vf", "scale='min(1600,iw)':-2", "-q:v", "4", str(out)], check=True)
            print(f"{PROG} sample: {out.relative_to(ROOT)} ({out.stat().st_size // 1024} kB, in the repo) and {(media / 'swatch.mp4').relative_to(ROOT)} (not in git)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.split("\n\n")[1] if argv else __doc__.split("\n\n")[1], file=sys.stdout if argv else sys.stderr)
        return 0 if argv else 2
    cmd = argv[0] if argv[0] in ("list", "check", "add", "sample") else "list"
    rest = argv[1:] if argv[0] == cmd else argv
    try:
        if cmd == "list":
            if rest and rest != ["--json"]:
                raise Usage(f"list takes --json only, not {' '.join(rest)}")
            tables = [slots_of(n) for n in names()]
            if rest == ["--json"]:
                print(json.dumps({"version": 1, "tool": f"{PROG} list", "components": tables}, ensure_ascii=False, indent=1))
                return 0
            for s in tables:
                print(f"  {s['name']:18} {'+'.join(s.get('painters', [])):11} {s.get('summary', '')}")
            print(f"{len(tables)} components (components/README.md); the library is components/lib; parameters: bin/vh components list --json")
            return 0
        if cmd == "check":
            bad = check()
            for b in bad:
                print(b, file=sys.stderr)
            if not bad:
                print(f"components: {len(names())} components, each with its defaults in slots.json, its painters, a sample and its provenance; the library holds no clock")
            return 1 if bad else 0
        if cmd == "add":
            if len(rest) < 2:
                raise Usage("add <project> <name…> (lib alone: the library)")
            return add(find_project(rest[0]), rest[1:])
        if cmd == "sample":
            pos = [x for x in rest if not x.startswith("-")]
            if len(pos) != 1 or any(x not in ("--draft",) for x in rest if x.startswith("-")):
                raise Usage("sample <name> [--draft]")
            return sample(pos[0], "--draft" in rest)
    except Usage as e:
        print(f"{PROG} {cmd}: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
