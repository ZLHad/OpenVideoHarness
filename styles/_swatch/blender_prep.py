"""Check a Blender swatch scene before anything runs it, and resolve its fonts.

usage: python3 styles/_swatch/blender_prep.py scan <swatch.py>
       uv run -q --no-project --with fonttools python styles/_swatch/blender_prep.py fonts <swatch.py> <out_dir>

scan   reads swatch.py as a syntax tree, never runs it, and fails (exit 1, one line per finding) on what a scene has no
       business doing (engines/blender.md, "安全"; CLAUDE.md hard rule 1). It is a lint: it catches mistakes and the plain
       ways out, not a determined author. The boundary is the sandbox render.sh puts Blender in on macOS (no network, writes
       only in out/<slug>/, final renders read nothing in the home folder but the repo and fonts); Linux has no sandbox, so
       render only scenes you have read. What the scan refuses:
       - imports outside ALLOWED (no os, subprocess, socket, urllib, shutil, pathlib, importlib, and no random, time or
         datetime, so the frames cannot depend on anything but t); of json only dumps and loads, of sys only argv;
       - any name or attribute that starts with "_" (except _ and __name__), and strings that contain "__": the dunder routes
         to builtins, frames and modules (bpy.utils._os, x.__dict__["__import__"], sys.__dict__["modules"]);
       - eval, exec, compile, open, input, breakpoint, globals, locals, vars, getattr, setattr, delattr, type, dir;
       - bpy that loads, saves or runs anything: .blend files (wm, libraries), text blocks (texts, run_script, as_module),
         drivers (driver_add, driver_namespace, drivers), bpy.utils, render output (save_render), add-ons, and the per-frame
         state of handlers and timers.
fonts  writes <out_dir>/fonts.json from the scene's FONTS, read as a literal (so the scene is not executed): each role is
       a fontconfig pattern ("Songti SC:weight=bold", "Big Caslon") matched with fc-match to a system font file, the same
       machine fonts the HyperFrames swatches reach through fonts.css. A match from another family stops the render (a
       Chinese role falling back to a Latin font would print tofu). Blender loads only the first face of a .ttc
       collection, so when the match is another face (Songti SC Bold is face 1 of Songti.ttc) that face is written out as
       its own font under <out_dir>/fonts/ on every run (about 0.3 s): a local copy in the git-ignored out/ folder, never
       committed or shipped."""
import ast, json, os, re, shutil, subprocess, sys

ALLOWED = {"bpy", "bmesh", "mathutils", "math", "colorsys", "json", "sys"}
ONLY = {"json": {"dumps", "loads"}, "sys": {"argv"}}      # of these two modules, nothing else
BANNED_NAMES = {"eval", "exec", "compile", "open", "input", "breakpoint", "globals", "locals", "vars", "getattr",
                "setattr", "delattr", "type", "dir"}
BANNED_ATTRS = {"save_mainfile", "save_as_mainfile", "save_copy", "open_mainfile", "recover_last_session", "execfile",
                "as_module", "save_render", "handlers", "timers", "script", "run_script", "texts", "libraries", "wm",
                "utils", "driver_add", "driver_namespace", "drivers", "addon_install", "addon_enable", "modules",
                "settrace", "setprofile"} | BANNED_NAMES


def scan(path):
    tree = ast.parse(open(path).read(), path)
    bad = []
    for n in ast.walk(tree):
        where = f"{os.path.basename(path)}:{getattr(n, 'lineno', '?')}"
        if isinstance(n, ast.Import):
            bad += [f"{where} import {a.name}" for a in n.names if a.name.split(".")[0] not in ALLOWED]
            bad += [f"{where} import {a.name} as {a.asname}" for a in n.names if a.asname and a.name in ONLY]   # keeps ONLY on
        elif isinstance(n, ast.ImportFrom):
            mod = (n.module or "").split(".")[0]
            if mod not in ALLOWED or n.level: bad.append(f"{where} from {n.module} import …")
            elif mod in ONLY: bad += [f"{where} from {mod} import {a.name}" for a in n.names if a.name not in ONLY[mod]]
        elif isinstance(n, ast.Name) and (n.id in BANNED_NAMES or (n.id.startswith("_") and n.id not in ("_", "__name__"))):
            bad.append(f"{where} {n.id}")
        elif isinstance(n, ast.Attribute):
            if n.attr in BANNED_ATTRS or n.attr.startswith("_"): bad.append(f"{where} .{n.attr}")
            elif isinstance(n.value, ast.Name) and n.value.id in ONLY and n.attr not in ONLY[n.value.id]:
                bad.append(f"{where} {n.value.id}.{n.attr}")
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and "__" in n.value and n.value != "__main__":
            bad.append(f"{where} a string with __ in it")
    return bad


def literal(path, name):
    for n in ast.parse(open(path).read(), path).body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return ast.literal_eval(n.value)
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name and n.value is not None:
            return ast.literal_eval(n.value)
    return None


def fonts(scene_py, out_dir):
    want = literal(scene_py, "FONTS") or {}
    if not (isinstance(want, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in want.items())):
        sys.exit("[swatch] FONTS must be a literal {role: \"fontconfig pattern\"}")
    os.makedirs(out_dir, exist_ok=True)
    if want and not shutil.which("fc-match"):
        sys.exit("[swatch] the scene's FONTS need fontconfig's fc-match (macOS: brew install fontconfig)")
    res = {}
    for role, pattern in want.items():
        f = subprocess.run(["fc-match", "-f", "%{file}\n%{index}\n%{family[0]}\n%{fullname[0]}", pattern],
                           capture_output=True, text=True, check=True).stdout.split("\n")
        path, index, family, full = f[0], int(f[1] or 0), f[2], f[3] if len(f) > 3 else ""
        asked = pattern.split(":")[0].strip()
        if family.lower() != asked.lower():
            sys.exit(f"[swatch] font {role}: {asked} is not on this machine (fc-match offers {family}, {full}); install it or "
                     "name a font that is (python3 styles/_swatch/fonts.py --list)")
        load = path
        if index and path.lower().endswith((".ttc", ".otc")):     # Blender reads face 0 only: write the face out
            from fontTools.ttLib import TTCollection
            os.makedirs(os.path.join(out_dir, "fonts"), exist_ok=True)
            name = re.sub(r"[^A-Za-z0-9]+", "-", full or f"{family}-{index}").strip("-")
            font = TTCollection(path, lazy=False).fonts[index]
            load = os.path.join(out_dir, "fonts", f"{name}.{'otf' if 'CFF ' in font else 'ttf'}")
            font.save(load + ".part"); os.replace(load + ".part", load)   # never a half-written font after a Ctrl-C
        res[role] = {"pattern": pattern, "source": path, "index": index, "family": family, "face": full, "file": load}
    with open(os.path.join(out_dir, "fonts.json"), "w") as fh: json.dump(res, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "scan":
        found = scan(a[1])
        for b in found: print(f"[swatch] not allowed in a Blender scene: {b}")
        sys.exit(1 if found else 0)
    if len(a) == 3 and a[0] == "fonts": fonts(a[1], a[2]); sys.exit(0)
    sys.exit(__doc__.split("\n\n")[0])
