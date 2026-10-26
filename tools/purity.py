"""Hard rule 1 (CLAUDE.md) as patterns: what a page, a component or a sketch must not lean on, a clock or chance.

One table for the three readers: bin/vh hf add (tools/hf.py, warnings on what a registry item brings), bin/vh components
check (tools/components.py) and bin/vh recipes check (tools/recipes.py). scan(text) → [(what, line number, the line)].
Comments are left out (/* … */, <!-- … -->, and // not after a colon, so a URL's // stays code). A line that says
purity-ok is left out too: put the reason after it (a guard that names the API, a frame-driven clock).
"""
import re

CLOCK = [("CSS @keyframes", r"@keyframes\b"), ("CSS animation", r"(?<![\w-])animation(?:-name)?\s*:"),
         ("CSS transition", r"(?<![\w-])transition\s*:"), ("Math.random", r"\bMath\.random\s*\("),
         ("Date.now", r"\bDate\.now\s*\("), ("new Date", r"\bnew\s+Date\s*\("), ("performance.now", r"\bperformance\.now\s*\("),
         ("requestAnimationFrame", r"\brequestAnimationFrame\s*\("), ("a timer", r"\bset(?:Timeout|Interval)\s*\("),
         ("a CSS transition or animation set from script", r"\.style\.(?:transition|animation)\w*\s*=(?!=)")]
_PATS = [(what, re.compile(pat)) for what, pat in CLOCK]
_COMMENT = re.compile(r"/\*.*?\*/|<!--.*?-->|(?<![:\w\"'/\\])//[^\n]*", re.S)


def code_of(text):
    """The text with its comments blanked out, newlines kept, so line numbers still match."""
    return _COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def scan(text):
    """[(what, line, the line as written)] for each line of code that leans on a clock or chance."""
    lines, hits = text.splitlines(), []
    for i, line in enumerate(code_of(text).splitlines(), 1):
        if "purity-ok" in lines[i - 1]:
            continue
        hits += [(what, i, lines[i - 1].strip()[:120]) for what, pat in _PATS if pat.search(line)]
    return hits
