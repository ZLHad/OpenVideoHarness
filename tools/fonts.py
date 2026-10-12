"""Fonts on this machine, by the names a page's @font-face local() uses, and subsets of them for a project.

usage (via bin/vh fonts, which runs it with fontTools and brotli through uv):
  python tools/fonts.py list [words…] [--cjk] [--all]
  python tools/fonts.py subset <project | page.html> [--family "Film Sans"] [--font <file | local name>] [--out dir]
                              [--chars-from f.txt] [--keep-hinting]

list     every face on this machine (PostScript name, full name, family, style, file), filtered by the words given
         (all of them, in any of those names: `list noto sc black`); --cjk keeps faces that have 中, 文 and 字. The names
         are what local() takes: the PostScript name ("PingFangSC-Semibold") and the full name ("PingFang SC Semibold").
         Default: one line per family and style; --all lists the faces inside collections (.ttc) as they are.
subset   a copy of each font the page declares with @font-face local(), cut down to the characters the project uses,
         as woff2 in <project>/assets/fonts/ (--out), and the src line that puts it first. The characters: every
         character in the project's own text sources (html, css, js and json outside node_modules and out, audio/script*.txt,
         audio/timeline*.json), the ones bin/vh fonts check last saw drawn in that family (out/check/fonts.json), and printable
         ASCII with the common CJK punctuation. --family: only that family's faces · --font: subset this one font instead
         (a file, or a local() name), its family named by --family · --chars-from: more characters, from a file.
         Characters the font does not have are listed: the browser would draw those in another font (bin/vh fonts check).

Licences: most fonts that come with an operating system (PingFang, Songti, Hiragino, Microsoft YaHei) may be used on this
machine but not handed on. A subset is a copy: keep it inside the project (projects/ is not committed), and do not publish
it or put it in the repo. Fonts under the SIL Open Font License (Noto CJK, Source Han) may be subset and shared, with the
licence beside them.

Where fonts are looked for: fc-list's list when fontconfig is installed, and these folders (read with fontTools, cached in
~/.cache/ovh/fonts.json): macOS /System/Library/Fonts (+ Supplemental), /Library/Fonts, ~/Library/Fonts and the fonts
macOS downloads on demand (/System/Library/AssetsV2/com_apple_MobileAsset_Font*); Linux /usr/share/fonts,
/usr/local/share/fonts, ~/.fonts, ~/.local/share/fonts.
Exit: 0 done · 1 subset: a font the page names is not on this machine, or characters it lacks · 2 bad arguments, no fontTools.
"""
import argparse, json, logging, os, re, subprocess, sys
from pathlib import Path

try:
    from fontTools.ttLib import TTCollection, TTFont
except ImportError:   # bin/vh fonts brings it through uv
    sys.exit("fonts: needs fontTools: run it as bin/vh fonts (it uses uv), or pip install fonttools brotli")

logging.getLogger("fontTools").setLevel(logging.ERROR)   # its warnings about odd tables in system fonts are not ours
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "ovh" / "fonts.json"
EXTS = (".ttf", ".otf", ".ttc", ".otc", ".woff", ".woff2")
CJK_PUNCT = "，。、：；！？（）《》〈〉「」『』【】“”‘’—…·～　"


def folders():
    h = Path.home()
    if sys.platform == "darwin":
        fixed = [Path("/System/Library/Fonts"), Path("/Library/Fonts"), h / "Library/Fonts"]
        assets = sorted(Path("/System/Library/AssetsV2").glob("com_apple_MobileAsset_Font*"))
        return fixed + assets
    return [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), h / ".fonts", h / ".local/share/fonts"]


def name_of(font, *ids):
    """The first English (else any) name for these name IDs."""
    t = font["name"]
    for i in ids:
        for rec in t.names:
            if rec.nameID == i and rec.platformID == 3 and rec.langID == 0x409:
                try: return rec.toUnicode().strip()
                except Exception: pass
        n = t.getDebugName(i)
        if n: return n.strip()
    return ""


def faces_in(path):
    """[{file, index, ps, full, family, style}] for one font file (several for a collection)."""
    try:
        fonts = TTCollection(str(path), lazy=True).fonts if path.suffix.lower() in (".ttc", ".otc") else [TTFont(str(path), lazy=True, fontNumber=0)]
    except Exception:
        return []
    out = []
    for i, f in enumerate(fonts):
        try:
            out.append({"file": str(path), "index": i, "ps": name_of(f, 6), "full": name_of(f, 4),
                        "family": name_of(f, 16, 1), "style": name_of(f, 17, 2)})
        except Exception:
            continue
    return out


def index(refresh=False):
    """Every face this machine has, read once and cached by file, size and time."""
    try: cache = {} if refresh else json.loads(CACHE.read_text())
    except (OSError, ValueError): cache = {}
    files = set()
    for d in folders():
        if d.is_dir():
            for p in d.rglob("*"):
                if p.suffix.lower() in EXTS and p.is_file(): files.add(p)
    if _which("fc-list"):   # fontconfig knows the folders it was told about too
        r = subprocess.run(["fc-list", "-f", "%{file}\n"], capture_output=True, text=True)
        files |= {Path(l) for l in r.stdout.splitlines() if l.strip() and Path(l).suffix.lower() in EXTS and Path(l).is_file()}
    new, faces = {}, []
    for p in sorted(files):
        st = p.stat(); k = f"{p}|{st.st_size}|{int(st.st_mtime)}"
        got = cache.get(k)
        if got is None: got = faces_in(p)
        new[k] = got; faces += got
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True); CACHE.write_text(json.dumps(new))
    except OSError:
        pass
    return faces


def _which(cmd):
    return any((Path(d) / cmd).is_file() for d in os.environ.get("PATH", "").split(os.pathsep) if d)


norm = lambda s: re.sub(r"[\s_-]", "", str(s or "")).lower()


def find(name, faces):
    """The face local(name) means: PostScript name or full name, as Chrome matches it."""
    n = norm(name)
    for key in ("ps", "full"):
        for f in faces:
            if norm(f[key]) == n: return f
    return None


def open_face(f):
    p = Path(f["file"])
    return TTCollection(str(p)).fonts[f["index"]] if p.suffix.lower() in (".ttc", ".otc") else TTFont(str(p))


def cmd_list(a):
    faces = index(a.refresh)
    words = [w.lower() for w in a.words]
    pick = [f for f in faces if all(any(w in str(f[k]).lower() for k in ("ps", "full", "family", "style")) for w in words)]
    if a.cjk:
        keep = []
        for f in pick:
            try:
                cm = TTCollection(f["file"], lazy=True).fonts[f["index"]].getBestCmap() if f["file"].lower().endswith((".ttc", ".otc")) else TTFont(f["file"], lazy=True).getBestCmap()
            except Exception:
                continue
            if cm and all(ord(c) in cm for c in "中文字"): keep.append(f)
        pick = keep
    if not a.all:   # one line per PostScript name: the same face is often in several places
        seen, one = set(), []
        for f in pick:
            if f["ps"] not in seen: seen.add(f["ps"]); one.append(f)
        pick = one
    pick.sort(key=lambda f: (f["family"].lower(), f["style"].lower(), f["ps"]))
    home = str(Path.home())
    for f in pick:
        where = f["file"].replace(home, "~", 1) + (f"#{f['index']}" if f["file"].lower().endswith((".ttc", ".otc")) else "")
        print(f"  {f['ps']:<34} {f['full']:<36} {f['family']} · {f['style']}   {where}")
    print(f"fonts: {len(pick)} face(s){' with 中文字' if a.cjk else ''}{(' matching ' + ' '.join(a.words)) if a.words else ''}; "
          "local() takes the first name (PostScript) or the second (full name)")


FACE = re.compile(r"@font-face\s*\{([^}]*)\}", re.S)


def page_of(target):
    p = Path(target)
    if p.is_dir():
        for n in ("film.html", "index.html", "studio.html"):
            if (p / n).is_file(): return p / n
        sys.exit(f"fonts: {target} has no page (film.html, index.html, studio.html)")
    if not p.is_file(): sys.exit(f"fonts: no such file or folder: {target}")
    return p


def declared(html):
    """[(family, weight, style, [local names])] of the page's @font-face rules (its own <style> and the CSS files it links)."""
    texts = [html.read_text(encoding="utf-8", errors="replace")]
    for href in re.findall(r"""<link[^>]+href=["']([^"']+\.css)["']""", texts[0]):
        f = (html.parent / href).resolve()
        if f.is_file() and html.parent.resolve() in f.parents: texts.append(f.read_text(encoding="utf-8", errors="replace"))
    out = []
    for t in texts:
        for body in FACE.findall(t):
            prop = lambda k: (re.search(rf"{k}\s*:\s*([^;]+)", body) or [None, ""])[1].strip()
            fam = prop("font-family").strip("\"'")
            names = [(m[0] or m[1] or m[2]).strip() for m in re.findall(r"""local\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*?))\s*\)""", prop("src"))]
            out.append((fam, prop("font-weight") or "400", prop("font-style") or "normal", names))
    return out


def project_chars(root):
    """Every character in the project's own text sources, and what fonts check last saw drawn, by family."""
    chars = set()
    skip = {"node_modules", "out", ".git", "media", "references"}
    for p in root.rglob("*"):
        if any(part in skip for part in p.relative_to(root).parts) or not p.is_file(): continue
        rel = p.relative_to(root).as_posix()
        if p.suffix.lower() in (".html", ".htm", ".css", ".js", ".mjs", ".json") or re.fullmatch(r"audio/(script.*\.txt|timeline.*\.json)", rel):
            if p.stat().st_size > 8_000_000: continue
            chars |= set(p.read_text(encoding="utf-8", errors="ignore"))
    seen = {}
    f = root / "out" / "check" / "fonts.json"
    if f.is_file():
        try:
            for g in json.loads(f.read_text()).get("fonts", []):
                seen.setdefault(norm(g.get("first", "")), set()).update(g.get("all", ""))
        except (OSError, ValueError):
            pass
    return chars, seen


def cmd_subset(a):
    from fontTools import subset as ft_subset
    page = page_of(a.target); root = page.parent
    faces = index()
    jobs = []   # (family, weight, style, face)
    missing = []
    if a.font:
        f = Path(a.font)
        if f.is_file():
            got = faces_in(f)
            if not got: sys.exit(f"fonts: {a.font} is not a font fontTools can read")
            face = got[0]
        else:
            face = find(a.font, faces)
            if not face: sys.exit(f'fonts: no face "{a.font}" on this machine (bin/vh fonts list shows them)')
        jobs.append((a.family or face["family"], "", "", face))
    else:
        rules = [r for r in declared(page) if not a.family or norm(r[0]) == norm(a.family)]
        if not rules: sys.exit(f"fonts: {page.name} declares no @font-face{' for ' + a.family if a.family else ''} with local() faces")
        for fam, w, st, names in rules:
            face = next((x for x in (find(n, faces) for n in names) if x), None)
            if face: jobs.append((fam, w, st, face))
            elif names: missing.append((fam, w, names))
    src_chars, seen = project_chars(root)
    if a.chars_from: src_chars |= set(Path(a.chars_from).read_text(encoding="utf-8", errors="ignore"))
    base = {chr(c) for c in range(0x20, 0x7F)} | set(CJK_PUNCT)
    out_dir = Path(a.out) if a.out else root / "assets" / "fonts"
    out_dir.mkdir(parents=True, exist_ok=True)
    bad = bool(missing)
    done = {}
    for fam, w, st, face in jobs:
        want = {c for c in (src_chars | base | seen.get(norm(fam), set())) if c.isprintable() and not c.isspace() or c == " "}
        key = (face["file"], face["index"])
        name = re.sub(r"[^A-Za-z0-9_.-]+", "-", face["ps"] or Path(face["file"]).stem) + ".subset.woff2"
        dst = out_dir / name
        if key not in done:
            font = open_face(face)
            cmap = font.getBestCmap() or {}
            drawn = seen.get(norm(fam))   # what fonts check saw drawn in this family; the source scan is every family's text
            lacks = sorted(c for c in drawn if ord(c) not in cmap and not c.isspace()) if drawn is not None else None
            o = ft_subset.Options(); o.flavor = "woff2"; o.layout_features = ["*"]; o.name_IDs = ["*"]; o.name_languages = ["*"]
            o.notdef_outline = True; o.hinting = a.keep_hinting; o.drop_tables += ["DSIG"]
            sub = ft_subset.Subsetter(options=o)
            sub.populate(unicodes=[ord(c) for c in want if ord(c) in cmap])
            sub.subset(font)
            font.flavor = "woff2"
            font.save(str(dst))
            done[key] = (dst, lacks, len([c for c in want if ord(c) in cmap]))
        dst, lacks, n = done[key]
        size = Path(face["file"]).stat().st_size
        rel = os.path.relpath(dst, root)
        print(f'  "{fam}" {w} {st}'.rstrip() + f' → {face["ps"]}: {n} characters, {dst.stat().st_size / 1024:.0f} KB (the font file: {size / 1e6:.1f} MB) → {rel}')
        print(f'      src: url("{rel}") format("woff2"), local("{face["ps"]}"), …;   (first in this face\'s src)')
        if lacks is None:
            print(f"      (which of these characters {fam} draws, and whether the font has them: bin/vh fonts check first)")
        elif lacks:
            bad = True
            show = " ".join(lacks[:30]) + (f" … ({len(lacks)})" if len(lacks) > 30 else "")
            print(f"      ✗ {len(lacks)} character(s) drawn in this family are not in {face['ps']} (the browser draws them in another font): {show}")
    for fam, w, names in missing:
        print(f'  ✗ "{fam}" {w}: none of its local() faces is on this machine ({", ".join(names)}); bin/vh fonts list shows the ones that are')
    print("fonts: a subset is a copy of the font; most system fonts may not be handed on, so keep it in the project and out of anything you publish (tools/fonts.py, Licences)")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(prog="bin/vh fonts", usage=__doc__.split("\n\n")[1].split("\n", 1)[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("words", nargs="*"); l.add_argument("--cjk", action="store_true"); l.add_argument("--all", action="store_true")
    l.add_argument("--refresh", action="store_true", help="read every font file again instead of the cache")
    s = sub.add_parser("subset"); s.add_argument("target"); s.add_argument("--family"); s.add_argument("--font"); s.add_argument("--out")
    s.add_argument("--chars-from"); s.add_argument("--keep-hinting", action="store_true")
    a = ap.parse_args()
    {"list": cmd_list, "subset": cmd_subset}[a.cmd](a)


if __name__ == "__main__":
    main()
