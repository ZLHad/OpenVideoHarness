"""The publishing copy against each platform's length limits: titles, descriptions and tags in PACKAGING.md.

usage: python3 tools/packcheck.py <PACKAGING.md | project> [--json f]      (bin/vh check runs it for the project of the video;
       --json f: every field measured, in a file, for its record)

Reads the "## 发布文案" section of PACKAGING.md (templates/PACKAGING.md shows it): one "### <platform>" heading per
platform (B站, 抖音, YouTube, 小红书, 视频号, or any other name; a heading that names several is held to the smallest
limit of each), and under it
    标题：<one line>
    标签：<tags, separated by commas, 、 or spaces>
    简介：<the first line, and every line after it up to the next 标题/标签/简介 or heading>
(English labels work too: Title:, Tags:, Description:). Placeholders in braces ({…}) and HTML comments are skipped.
Characters are counted as the platforms count them in their boxes: one per character whatever the script (a Chinese
character is one, so is a letter; a line break counts one), except where a platform's own rule is known (COUNTS below:
X weighs a Chinese character as 2). The limits (LIMITS below) are in playbook/10 with their sources and the date they
were checked; where a platform's limit is not known, only the counts are printed.
Exit: 0 every field within its limit (or nothing to check) · 1 a field over its limit · 2 no such file.
"""
import json, re, sys, unicodedata
from pathlib import Path

# platform: (names it goes by, {field: (limit, how sure)}); playbook/10-hooks-and-packaging.md, 发布文案的长度
LIMITS = {
    "youtube": (("youtube", "油管"), {"title": (100, "official"), "desc": (5000, "official")}),
    "bilibili": (("b站", "bilibili", "哔哩哔哩"), {"title": (80, "second-hand"), "desc": (2000, "second-hand")}),
    "douyin": (("抖音", "douyin"), {"title": (30, "second-hand")}),
    "xiaohongshu": (("小红书", "xiaohongshu", "rednote"), {"title": (20, "second-hand")}),
    "channels": (("视频号", "channels"), {}),
    "x": (("x", "twitter", "推特"), {"desc": (280, "official")}),   # a post: no title; the text is the 简介
}
FIELDS = {"标题": "title", "title": "title", "简介": "desc", "description": "desc", "描述": "desc", "标签": "tags", "tags": "tags"}
NAMES = {"title": "标题 title", "desc": "简介 description", "tags": "标签 tags"}


# X's weighted length (docs.x.com/fundamentals/counting-characters; the weights are twitter-text's config/v3.json): after
# NFC, a link is 23 whatever its length, an emoji 2 (with its modifiers and joined parts), a code point in U+0000–10FF,
# U+2000–200D, U+2010–201F or U+2032–2037 is 1 and any other 2, so a Chinese character, a full-width comma or 。 is 2.
# Only links written with http(s):// are taken as links (X counts a bare example.com as 23 too); a keycap emoji counts more
# than X's 2: never under X's count but for those bare links
URL = re.compile(r"https?://[\x21-\x7e]*[A-Za-z0-9/#=_-]")
EMOJI = re.compile("[\U0001F1E6-\U0001F1FF]{2}|[\u2600-\u27BF\U0001F000-\U0001FAFF][\uFE0F\U0001F3FB-\U0001F3FF]*"
                   "(?:\u200D[\u2600-\u27BF\U0001F000-\U0001FAFF][\uFE0F\U0001F3FB-\U0001F3FF]*)*")
ONE = ((0x0000, 0x10FF), (0x2000, 0x200D), (0x2010, 0x201F), (0x2032, 0x2037))


def x_length(s):
    s = unicodedata.normalize("NFC", s)
    n = 23 * len(URL.findall(s)); s = URL.sub("", s)
    n += 2 * len(EMOJI.findall(s)); s = EMOJI.sub("", s)
    return n + sum(1 if any(a <= ord(c) <= b for a, b in ONE) else 2 for c in s)


# platforms that do not count one per character: (count, unit); every other platform counts len()
COUNTS = {"x": (x_length, "weighted characters, Chinese and emoji 2, a link 23")}


def platforms_of(name):
    """Every platform a heading names ("B站 / YouTube 双发" names two); a one-letter name (X) only standing alone."""
    n = name.strip().lower()
    has = lambda x: re.search(rf"(?<![a-z0-9]){re.escape(x)}(?![a-z0-9])", n) if len(x) == 1 else x in n
    return [key for key, (names, _) in LIMITS.items() if any(has(x) for x in names)]


def binding(keys, field, value):
    """The tightest limit on a field over the platforms named, each counting the value its own way (COUNTS): (count,
    limit, how sure and whose, unit) for the one the value comes closest to or goes furthest over, or None."""
    best = None
    for k in keys:
        if field not in LIMITS[k][1]: continue
        cap, sure = LIMITS[k][1][field]
        count, unit = COUNTS.get(k, (len, "characters"))
        n = count(value)
        if best is None or n - cap > best[0] - best[1]: best = (n, cap, f"{sure}, {k}" if len(keys) > 1 else sure, unit)
    return best


def parse(text):
    """{heading: {field: value}} from the 发布文案 section."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    m = re.search(r"^## *发布文案[^\n]*\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if not m:
        return {}
    out, cur, field = {}, None, None
    for line in m.group(1).split("\n"):
        h = re.match(r"^### *(.+?)\s*$", line)
        if h:
            cur, field = h.group(1), None; out[cur] = {}; continue
        if cur is None:
            continue
        f = re.match(r"^\s*[-*]?\s*(标题|简介|描述|标签|title|description|tags)\s*[：:]\s*(.*)$", line, flags=re.I)
        if f:
            field = FIELDS[f.group(1).lower()]
            out[cur][field] = f.group(2).strip(); continue
        if field == "desc":
            out[cur]["desc"] = (out[cur]["desc"] + "\n" + line) if out[cur].get("desc") else line
    for fields in out.values():
        if "desc" in fields:
            fields["desc"] = fields["desc"].strip("\n")
        for k in list(fields):
            if re.fullmatch(r"\{[^}]*\}", fields[k].strip()) or not fields[k].strip():
                del fields[k]   # a placeholder, or empty
    return out


def tags_of(s):
    return [t for t in re.split(r"[,，、\s]+", s) if t.strip("#")]


def main():
    args, jpath = list(sys.argv[1:]), None
    if "--json" in args:   # the fields measured, in a file: for bin/vh check's record
        i = args.index("--json"); jpath = args[i + 1] if i + 1 < len(args) else None; del args[i:i + 2]
    if len(args) != 1:
        sys.exit("usage: python3 tools/packcheck.py <PACKAGING.md | project> [--json f]")
    p = Path(args[0])
    if p.is_dir():
        p = p / "PACKAGING.md"
    if not p.is_file():
        print(f"packcheck: no {p}", file=sys.stderr); sys.exit(2)
    got = parse(p.read_text(encoding="utf-8"))
    if not any(got.values()):
        print(f"packaging: {p.name} has no 发布文案 to measure (## 发布文案, a ### heading per platform: templates/PACKAGING.md)")
        sys.exit(0)
    over, rec = 0, []
    for head, fields in got.items():
        if not fields:
            continue
        keys = platforms_of(head)
        parts = []
        for f in ("title", "desc", "tags"):
            if f not in fields:
                continue
            v = fields[f]
            lim = binding(keys, f, v) if f != "tags" else None
            n, unit = (len(tags_of(v)), "tags") if f == "tags" else (len(v), "characters")
            if lim:
                n, cap, sure, unit = lim
                bad = n > cap
                over += bad
                parts.append(f"{'✗' if bad else '✓'} {NAMES[f]} {n} {unit} (limit {cap}, {sure})")
                rec.append({"heading": head, "field": f, "count": n, "unit": unit, "limit": cap, "sure": sure, "over": bad})
            else:
                parts.append(f"· {NAMES[f]} {n} {unit}")
                rec.append({"heading": head, "field": f, "count": n, "unit": unit, "limit": None, "over": False})
        print(f"packaging · {head}: " + " · ".join(parts))
    if over:
        print("  over a limit: shorten it there, or move the long part (credits, sources) to a pinned comment; the upload page has the last word")
    if jpath:
        try: Path(jpath).write_text(json.dumps({"file": str(p), "fields": rec}, ensure_ascii=False), encoding="utf-8")
        except OSError as e: print(f"packcheck: could not write {jpath} ({e.strerror or e})", file=sys.stderr)
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
