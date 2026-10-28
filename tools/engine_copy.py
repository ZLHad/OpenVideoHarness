"""A project's copy of its engine against the engine as it is now (bin/vh doctor <project>). Read-only.

usage: python3 tools/engine_copy.py <project>

bin/vh new copies the engine into a canvas-film project (engines/canvas-film/template, its README as ENGINE_README.md)
and into a hand-drawn one (engines/ClaudeAnimationBase, README.md as ENGINE_README.md). The engine moves on after that;
this lists, file by file, what the copy has that differs: changed, missing (a module the copy lacks, e.g. a newer
src/06-time-map.js, and whether film.html loads it), and extra (the project's own files in the engine's folders). The
film's own files are left out: canvas-film's src/50-shots.js, audio/ and assets/; ClaudeAnimationBase's src/scenes/ and
src/config.js. A canvas-film project made with --three has its three/ held to engines/canvas-film/three/ too (the
Three.js layer and the three.js it pins; an addon of the project's own there is not listed). Nothing is changed; the
diff command it prints shows a file's difference (+ lines are the engine's now).
Exit: 0 the copy is the engine as it is · 1 something differs · 2 not a project with a copied engine.
"""
import difflib, os, re, shlex, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# engine: (the folder new copies from, the files that say a project has it, the film's own files, README's name in it,
# the folders the project's own engine-side files would be in)
ENGINES = {
    "canvas-film": (ROOT / "engines/canvas-film/template", ("film.html", "src/90-main.js"),
                    lambda f: f == "src/50-shots.js" or f.startswith(("audio/", "assets/")), ROOT / "engines/canvas-film/README.md", ("src",)),
    "ClaudeAnimationBase": (ROOT / "engines/ClaudeAnimationBase", ("render.mjs", "src/core.js"),
                            lambda f: f == "src/config.js" or f.startswith("src/scenes/"), ROOT / "engines/ClaudeAnimationBase/README.md", ("src",)),
}
SKIP = ("node_modules", "out", ".DS_Store")
THREE = ROOT / "engines/canvas-film/three"   # canvas-film's Three.js layer: a project made with --three has it as three/


def files(d):
    """Every file under d as a posix path relative to it, outside node_modules and out (what bin/vh new leaves out)."""
    out = []
    for top, dirs, names in os.walk(d):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        out += [Path(top, n).relative_to(d).as_posix() for n in names if n not in SKIP]
    return sorted(out)


def lines(p):
    try:
        return p.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, ValueError):
        return None   # an image or another binary file: same or not, no line count


def scripts(html):
    try:
        return re.findall(r'<script[^>]*\bsrc="([^"]+)"', html.read_text(encoding="utf-8"))
    except OSError:
        return []


def show(p):
    """A path as short as it can be from here."""
    try:
        r = os.path.relpath(p)
        return r if not r.startswith("../../") else str(p)
    except ValueError:
        return str(p)


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip()); sys.exit(0 if len(sys.argv) == 2 else 2)
    proj = Path(sys.argv[1])
    if not proj.is_dir():
        print(f"doctor: no such project folder: {proj}", file=sys.stderr); sys.exit(2)
    name = next((k for k, (_, marks, *_r) in ENGINES.items() if all((proj / m).is_file() for m in marks)), None)
    if not name:
        print(f"doctor: {show(proj)} has no copied engine to compare (a canvas-film project has film.html and src/90-main.js, "
              "a hand-drawn one render.mjs and src/core.js); other engines are not copied into the project", file=sys.stderr)
        sys.exit(2)
    tmpl, _, own, readme, dirs = ENGINES[name]
    want = [f for f in files(tmpl) if not own(f) and f != "README.md"]
    mine_readme = proj / "ENGINE_README.md"
    if not mine_readme.is_file() and name == "ClaudeAnimationBase" and (proj / "README.md").is_file():
        mine_readme = proj / "README.md"   # a project from before bin/vh new renamed the engine's README
    pairs = [(f, proj / f, tmpl / f) for f in want] + [(mine_readme.name, mine_readme, readme)]
    if name == "canvas-film" and (proj / "three" / "layer.js").is_file():   # the Three.js layer (bin/vh new … --three) against the engine's
        pairs += [(f"three/{f}", proj / "three" / f, THREE / f) for f in files(THREE)]
    same, changed, missing = [], [], []
    for f, mine, theirs in pairs:
        if not mine.is_file():
            missing.append(f); continue
        if mine.read_bytes() == theirs.read_bytes():
            same.append(f); continue
        a, b = lines(mine), lines(theirs)
        if a is None or b is None:
            changed.append((f, "")); continue
        d = list(difflib.unified_diff(a, b, lineterm="", n=0))
        plus = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
        minus = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
        changed.append((f, f" +{plus} −{minus}"))
    have = set(want)
    extra = [f for f in files(proj) if f.split("/")[0] in dirs and f not in have and not own(f)]
    loaded = set(scripts(proj / "film.html")) if name == "canvas-film" else set()
    print(f"engine copy: {name} · {show(proj)} against {show(tmpl)} as it is now "
          f"({len(pairs)} engine files; the film's own files are left out)")
    if changed:
        print(f"  changed ({len(changed)}): " + ", ".join(f + n for f, n in changed) + "   (+ lines the engine has now, − lines only the copy has)")
    if missing:
        notes = []
        for f in missing:
            n = f
            if name == "canvas-film" and f.startswith("src/") and f.endswith(".js"):
                n += " (film.html loads it)" if f in loaded else " (film.html does not load it either)"
            notes.append(n)
        print(f"  missing ({len(missing)}): " + ", ".join(notes) + "   (the engine has them now, the copy does not)")
    if extra:
        print(f"  extra ({len(extra)}): " + ", ".join(extra) + "   (the project's own, not in the engine)")
    print(f"  same ({len(same)})" + (f": {', '.join(same)}" if same and len(same) <= 6 else ""))
    if changed or missing:
        f = changed[0][0] if changed else missing[0]
        theirs = next(t for g, _, t in pairs if g == f)
        print(f"  a file's diff: diff -u {shlex.quote(show(proj / f)) if changed else '/dev/null'} {shlex.quote(show(theirs))}"
              + ("   (the same for the others)" if len(changed) + len(missing) > 1 else ""))
        print("  nothing was changed: take what the film needs by hand (the engine's README says what moved, CHANGELOG.md when)")
        sys.exit(1)
    print("  the copy is the engine as it is now")


if __name__ == "__main__":
    main()
