"""Check a Blender swatch scene before anything runs it, and resolve its fonts.

usage: python3 styles/_swatch/blender_prep.py scan <swatch.py>
       uv run -q --no-project --with fonttools python styles/_swatch/blender_prep.py fonts <swatch.py> <out_dir>

scan   reads swatch.py as a syntax tree, never runs it, and fails (exit 1, one line per finding) on what an agent-written
       bpy script must not do here (engines/blender.md, "安全"; CLAUDE.md hard rule 1):
       - imports outside ALLOWED: no os, subprocess, socket, urllib, shutil, pathlib, importlib, and no random, time or
         datetime, so the frames cannot depend on anything but t;
       - eval, exec, compile, __import__, open, and dunder escapes such as __subclasses__ or __globals__;
       - bpy calls that write or load files, run text blocks, or keep state between frames: saving or opening .blend
         files, execfile, as_module, save_render, app.handlers, app.timers.
       render.sh then runs Blender with no inherited environment (env -i: no API keys) and, on macOS, under sandbox-exec
       with no network and writes only inside out/<slug>/.
fonts  writes <out_dir>/fonts.json from the scene's FONTS, read as a literal (so the scene is not executed): each role is
       a fontconfig pattern ("Songti SC:weight=bold", "Big Caslon") matched with fc-match to a system font file, the same
       machine fonts the HyperFrames swatches reach through fonts.css. Blender loads only the first face of a .ttc
       collection, so when the match is another face (Songti SC Bold is face 1 of Songti.ttc) that face is written out as
       its own font under <out_dir>/fonts/: a local cache in the git-ignored out/ folder, never committed or shipped. A
       match from another family is a fallback: it is printed, and the STYLE.md names the font the swatch really used."""
import ast, json, os, re, shutil, subprocess, sys

ALLOWED = {"bpy", "bmesh", "mathutils", "math", "colorsys", "json", "sys"}
BANNED_NAMES = {"eval", "exec", "compile", "__import__", "open", "input", "breakpoint", "globals", "vars",
                "__builtins__", "__subclasses__", "__globals__", "__code__", "__getattribute__", "__loader__", "__spec__"}
BANNED_ATTRS = {"save_mainfile", "save_as_mainfile", "save_copy", "open_mainfile", "recover_last_session", "execfile",
                "as_module", "save_render", "handlers", "timers", "script", "addon_install", "addon_enable",
                "modules", "_getframe", "settrace", "setprofile"}


def scan(path):
    tree = ast.parse(open(path).read(), path)
    bad = []
    for n in ast.walk(tree):
        where = f"{os.path.basename(path)}:{getattr(n, 'lineno', '?')}"
        if isinstance(n, ast.Import):
            bad += [f"{where} import {a.name}" for a in n.names if a.name.split(".")[0] not in ALLOWED]
        elif isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] not in ALLOWED or n.level: bad.append(f"{where} from {n.module} import …")
        elif isinstance(n, ast.Name) and n.id in BANNED_NAMES: bad.append(f"{where} {n.id}")
        elif isinstance(n, ast.Attribute) and (n.attr in BANNED_ATTRS or n.attr in BANNED_NAMES):
            bad.append(f"{where} .{n.attr}")
    return bad


def literal(path, name):
    for n in ast.parse(open(path).read(), path).body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
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
            print(f"[swatch] font {role}: {asked} is not on this machine, fell back to {family} ({full})")
        load = path
        if index and path.lower().endswith((".ttc", ".otc")):     # Blender reads face 0 only: write the face out
            from fontTools.ttLib import TTCollection
            os.makedirs(os.path.join(out_dir, "fonts"), exist_ok=True)
            name = re.sub(r"[^A-Za-z0-9]+", "-", full or f"{family}-{index}").strip("-")
            font = TTCollection(path, lazy=False).fonts[index]
            load = os.path.join(out_dir, "fonts", f"{name}.{'otf' if 'CFF ' in font else 'ttf'}")
            if not os.path.exists(load): font.save(load)
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
