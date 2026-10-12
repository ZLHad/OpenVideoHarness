"""The publishing copy against each platform's length limits: titles, descriptions and tags in PACKAGING.md.

usage: python3 tools/packcheck.py <PACKAGING.md | project>      (bin/vh check runs it for the project of the video)

Reads the "## 发布文案" section of PACKAGING.md (templates/PACKAGING.md shows it): one "### <platform>" heading per
platform (B站, 抖音, YouTube, 小红书, 视频号, or any other name; a heading that names several is held to the smallest
limit of each), and under it
    标题：<one line>
    标签：<tags, separated by commas, 、 or spaces>
    简介：<the first line, and every line after it up to the next 标题/标签/简介 or heading>
(English labels work too: Title:, Tags:, Description:). Placeholders in braces ({…}) and HTML comments are skipped.
Characters are counted as the platforms count them in their boxes, one per character whatever the script (a Chinese
character is one, so is a letter); a line break counts one. The limits (LIMITS below) are in playbook/10 with their
sources and the date they were checked; where a platform's limit is not known, only the counts are printed.
Exit: 0 every field within its limit (or nothing to check) · 1 a field over its limit · 2 no such file.
"""
import re, sys
from pathlib import Path

# platform: (names it goes by, {field: (limit, how sure)}); playbook/10-hooks-and-packaging.md, 发布文案的长度
LIMITS = {
    "youtube": (("youtube", "油管"), {"title": (100, "official"), "desc": (5000, "official")}),
    "bilibili": (("b站", "bilibili", "哔哩哔哩"), {"title": (80, "second-hand"), "desc": (2000, "second-hand")}),
    "douyin": (("抖音", "douyin"), {"title": (30, "second-hand")}),
    "xiaohongshu": (("小红书", "xiaohongshu", "rednote"), {"title": (20, "second-hand")}),
    "channels": (("视频号", "channels"), {}),
}
FIELDS = {"标题": "title", "title": "title", "简介": "desc", "description": "desc", "描述": "desc", "标签": "tags", "tags": "tags"}
NAMES = {"title": "标题 title", "desc": "简介 description", "tags": "标签 tags"}


def platforms_of(name):
    """Every platform a heading names ("B站 / YouTube 双发" names two)."""
    n = name.strip().lower()
    return [key for key, (names, _) in LIMITS.items() if any(x in n for x in names)]


def limits_of(keys):
    """The smallest limit of each field over the platforms named, with whose it is."""
    out = {}
    for k in keys:
        for f, (cap, sure) in LIMITS[k][1].items():
            if f not in out or cap < out[f][0]: out[f] = (cap, f"{sure}, {k}" if len(keys) > 1 else sure)
    return out


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
    if len(sys.argv) != 2:
        sys.exit("usage: python3 tools/packcheck.py <PACKAGING.md | project>")
    p = Path(sys.argv[1])
    if p.is_dir():
        p = p / "PACKAGING.md"
    if not p.is_file():
        print(f"packcheck: no {p}", file=sys.stderr); sys.exit(2)
    got = parse(p.read_text(encoding="utf-8"))
    if not any(got.values()):
        print(f"packaging: {p.name} has no 发布文案 to measure (## 发布文案, a ### heading per platform: templates/PACKAGING.md)")
        sys.exit(0)
    over = 0
    for head, fields in got.items():
        if not fields:
            continue
        lim = limits_of(platforms_of(head))
        parts = []
        for f in ("title", "desc", "tags"):
            if f not in fields:
                continue
            v = fields[f]
            n = len(tags_of(v)) if f == "tags" else len(v)
            unit = "tags" if f == "tags" else "characters"
            if f in lim:
                cap, sure = lim[f]
                bad = n > cap
                over += bad
                parts.append(f"{'✗' if bad else '✓'} {NAMES[f]} {n} {unit} (limit {cap}, {sure})")
            else:
                parts.append(f"· {NAMES[f]} {n} {unit}")
        print(f"packaging · {head}: " + " · ".join(parts))
    if over:
        print("  over a limit: shorten it there, or move the long part (credits, sources) to a pinned comment; the upload page has the last word")
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
