"""bin/vh hf-init's font fix: the scaffold's fonts declared on the machine, so no render fetches one.

usage: python3 tools/hfinit.py fonts <index.html>    rewrite the scaffold's stacks to local fonts (exit 1: nothing to rewrite)
       python3 tools/hfinit.py check <file.html…>    what would make HyperFrames fetch a font at render time (exit 1: some)

HyperFrames 0.8.202 (core/dist/fonts/deterministicFonts.js) embeds the fonts a composition names when it renders: a family
with an @font-face is used as declared; a font-family whose first family is generic (sans-serif, system-ui …), directly or
through a var(), gets Inter put in front of it, fetched from Google Fonts, and so does a family with no @font-face, plain
names like Arial or Menlo included. Where Google is blocked that fetch hangs the render, the snapshot and the check. The
scaffold says `--font-display: sans-serif` (0.8.82 said `font-family: Inter, …`). `fonts` declares system fonts through
local() @font-face rules, as styles/_swatch/fonts.css does, and puts them first in those stacks.
"""
import re
import sys

GENERIC = {"sans-serif", "serif", "monospace", "cursive", "fantasy", "system-ui", "ui-sans-serif", "ui-serif",
           "ui-monospace", "ui-rounded", "math", "emoji", "fangsong", "inherit", "initial", "unset", "revert"}
STACK = '"Helvetica Neue", "Liberation Sans", "DejaVu Sans", sans-serif;'
FACES = """\
      /* Local fonts only. At render time HyperFrames fetches a font from Google Fonts for every family without an @font-face
         (it hangs where that is blocked), lint-clean names like Arial or Menlo included, and for a stack that starts with a
         generic family (it puts Inter first). Declare each font you add like these; more macOS faces: styles/_swatch/fonts.css */
      @font-face { font-family: "Helvetica Neue"; src: local("HelveticaNeue"), local("Helvetica Neue"); font-weight: 400; }
      @font-face { font-family: "Helvetica Neue"; src: local("HelveticaNeue-Bold"), local("Helvetica Neue Bold"); font-weight: 700; }
      @font-face { font-family: "Liberation Sans"; src: local("LiberationSans"), local("Liberation Sans"); font-weight: 400; }
      @font-face { font-family: "Liberation Sans"; src: local("LiberationSans-Bold"), local("Liberation Sans Bold"); font-weight: 700; }
      @font-face { font-family: "DejaVu Sans"; src: local("DejaVuSans"), local("DejaVu Sans"); font-weight: 400; }
      @font-face { font-family: "DejaVu Sans"; src: local("DejaVuSans-Bold"), local("DejaVu Sans Bold"); font-weight: 700; }
"""


def fonts(html):
    """The scaffold with its Inter and --font-display stacks pointing at the local faces above; None when neither is there."""
    s, n = re.subn(r"font-family: Inter\b[^;]*;", "font-family: " + STACK, html)
    s, m = re.subn(r"(--font-display:)[^;]*;", lambda g: g.group(1) + " " + STACK, s)
    if not (n or m) or "<style>\n" not in s:
        return None
    return s.replace("<style>\n", "<style>\n" + FACES, 1)


def families(value):
    return [f.strip().strip("\"'").strip() for f in value.split(",") if f.strip()]


def problems(html):
    """Each reason HyperFrames would fetch a font for this page at render time."""
    out = [f"a stylesheet from {h} (fetched when the page loads)" for h in sorted(set(re.findall(r"fonts\.(?:googleapis|gstatic)\.com", html)))]
    props = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", html))
    declared = {f.lower() for block in re.findall(r"@font-face\s*{([^}]*)}", html) for f in re.findall(r"font-family\s*:\s*([^;]+)", block)
                for f in families(f)}
    for value in re.findall(r"(?<![\w-])font-family\s*:\s*([^;}]+)", re.sub(r"@font-face\s*{[^}]*}", "", html)):
        stack = re.sub(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)", lambda g: props.get(g.group(1), g.group(2) or ""), value).strip()
        fams = families(stack)
        if not fams:
            continue
        if fams[0].lower() in GENERIC:
            out.append(f"font-family: {value.strip()} starts with the generic {fams[0]}: HyperFrames puts Inter in front and fetches it")
        for f in fams:
            if f.lower() not in GENERIC and f.lower() not in declared:
                out.append(f"font-family: {value.strip()} names {f} with no @font-face: HyperFrames fetches it")
    return list(dict.fromkeys(out))


def main(argv):
    if len(argv) < 2 or argv[0] not in ("fonts", "check") or (argv[0] == "fonts" and len(argv) != 2):
        print(__doc__.strip().split("\n\n")[0] + "\n\n" + __doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    if argv[0] == "fonts":
        s = fonts(open(argv[1], encoding="utf-8").read())
        if s is None:
            return 1
        open(argv[1], "w", encoding="utf-8").write(s)
        return 0
    bad = 0
    for p in argv[1:]:
        for line in problems(open(p, encoding="utf-8").read()):
            print(f"{p}: {line}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
