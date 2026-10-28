"""bin/vh know: what the repo knows about a few words, from the cards and sections that are read when needed, not
before: a few recipes (and components), a style, a section of the playbook (or a type doc, an engine doc), a case.
It answers "what do we have for this" without reading the documents first; the must-read list is not changed by it.

usage: bin/vh know <words…> [--kind recipe,component,style,doc,case] [-n N] [--json]
       bin/vh know --index [--json]

  the index   built each time from the files (no cache to go stale): every recipe, skeleton and shot-grammar card in
              recipes/ (its frontmatter: name, one_liner, family, role, intent, needs, types, engines, pitfalls; a
              card's grammar and code), every style
              (styles/<slug>/STYLE.md's title and 一句话, tokens.json's family, transitions, camera, type_anim,
              texture), every component (components/<name>/slots.json: its name, summary and painters, its tags if
              it has some, and each slot's name and text; lib/ and LICENSES/ have none, so they are not components),
              and the ## and ### sections of playbook/*.md, video-types/*.md, engines/*.md
              and cases/*.md, cut where tools/readpath.py cuts them (readpath.outline). A section, a recipe or a card
              can carry tags of its own in a comment, for the words a seeker uses that its text lacks: <!-- know: 翻页,
              纸面 -->
  matching    the words as they are written: Latin words in lower case, Chinese as pairs of characters (章节进度条:
              章节 节进 进度 度条), scored BM25 over each unit's title and tags (×3), its one-line summary (×2) and its
              text (×1), weighed by how many of the words it has, with a bonus for a word found whole in the title or
              tags. No vectors, no model
  answer      by kind, best first: up to 3 recipes, 2 components, 1 style, 1 doc section, 1 case (-n N: N of each;
              --kind: only these kinds, 5 of each unless -n), each with half the words or more; a kind that has none
              shows its best one, marked partial. Each: where (file:line), its title, its summary, the words that
              matched. --index: the index itself, the metadata of every unit, without its text

--json: {"version": 1, "query", "terms", "hits": [{"kind", "id", "title", "file", "line", "summary", "tags",
"score", "matched", "partial"}], "units": n, "by_kind": {kind: n}}; --index --json: {"version": 1, "units": [{"kind", "id",
"title", "file", "line", "summary", "tags", "chars"}], "by_kind"}. Exit: 0 · 1 nothing matched · 2 usage.
"""
import argparse, json, math, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import readpath   # noqa: E402

KINDS = ("recipe", "component", "style", "doc", "case")
QUOTA = {"recipe": 3, "component": 2, "style": 1, "doc": 1, "case": 1}
RECIPE_TAGS = ("family", "role", "intent", "needs", "types", "engines", "pitfalls", "grammar", "code")   # grammar, code: a shot-grammar card's
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*|[㐀-鿿豈-﫿]+")
OWN_TAGS = re.compile(r"<!--\s*know:\s*(.*?)-->", re.S)


def terms(text):
    """The words of a text as the index counts them: Latin in lower case (a hyphenated word also as its parts),
    Chinese as overlapping pairs of characters (one character alone stays one)."""
    out = []
    for m in WORD.finditer(text or ""):
        w = m.group(0)
        if w[0].isascii():
            w = w.lower().strip(".+-")
            out.append(w)
            parts = [x for x in re.split(r"[-_.+]", w) if x]
            if len(parts) > 1:
                out += parts
        else:
            out += [w[i:i + 2] for i in range(len(w) - 1)] or [w]
    return out


def first_sentence(text):
    """The first sentence of a section's prose: no heading, list marker, table, code or comment."""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "|", "```", "<!--", ">")):
            continue
        s = re.sub(r"^[-*] +|^\d+\. +", "", s)
        s = re.sub(r"\*\*|`", "", s)
        m = re.match(r"(.+?[。！？.!?])(\s|$)", s)
        return (m.group(1) if m else s)[:160]
    return ""


def unit(kind, uid, title, file, line, summary, tags, body):
    return {"kind": kind, "id": uid, "title": title, "file": file, "line": line, "summary": summary,
            "tags": sorted({t for t in tags if t}), "body": body}


def frontmatter(path):
    """A lenient read of a --- frontmatter block: key: value lines and [a, b] lists; {} when there is none."""
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, "\n".join(lines)
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, "\n".join(lines)
    fm = {}
    for line in lines[1:end]:
        m = re.match(r"([A-Za-z_]+):\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            fm[m.group(1)] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()] if v.startswith("[") and v.endswith("]") else v.strip("'\"")
    return fm, "\n".join(lines[end + 1:])


def own_tags(body):
    """The tags a section gives itself: <!-- know: 翻页, 纸面 --> (commas, Chinese commas or 、 between them)."""
    return [t.strip() for m in OWN_TAGS.finditer(body) for t in re.split(r"[,，、]", m.group(1)) if t.strip()]


def flat(v):
    return [str(x) for x in v] if isinstance(v, list) else [str(v)] if v not in (None, "") else []


def build():
    """Every unit of the index, in a fixed order."""
    units = []
    for f in sorted((ROOT / "recipes").rglob("*.md")):
        if f.name in ("README.md", "_TEMPLATE.md") or "LICENSES" in f.parts:
            continue
        fm, body = frontmatter(f)
        if not fm:
            continue
        rel = f.relative_to(ROOT).as_posix()
        tags = [t for k in RECIPE_TAGS for t in flat(fm.get(k))] + [fm.get("id", f.stem)] + own_tags(body)   # a card's other names too
        units.append(unit("recipe", fm.get("id", f.stem), fm.get("name") or f.stem, rel, 1, fm.get("one_liner", ""), tags, body))
    for f in sorted((ROOT / "components").glob("*/slots.json")):   # a component is a folder with its slots.json (components/README.md)
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict):
            continue
        name = str(d.get("name") or f.parent.name)
        slots = [x for x in d.get("slots") or [] if isinstance(x, dict)] if isinstance(d.get("slots"), list) else []
        tags = [name] + flat(d.get("painters")) + flat(d.get("tags")) + [str(x["name"]) for x in slots if x.get("name")]
        body = "\n".join(f"{x.get('name', '')}: {x.get('text', '')}" for x in slots)
        units.append(unit("component", name, name, f.relative_to(ROOT).as_posix(), 1, str(d.get("summary") or ""), tags, body))
    for d in sorted(p for p in (ROOT / "styles").iterdir() if p.is_dir() and not p.name.startswith("_")):
        f = d / "STYLE.md"
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        head = re.search(r"^# (.+)$", text, re.M)
        one = re.search(r"^一句话：(.+)$", text, re.M)
        tags = [d.name]
        try:
            tok = json.loads((d / "tokens.json").read_text(encoding="utf-8"))
            tags += flat(tok.get("family")) + flat(tok.get("transitions")) + flat(tok.get("camera")) + flat(tok.get("type_anim"))
            tags += flat((tok.get("texture") or {}).get("type")) + flat((tok.get("name") or {}).get("en"))
        except (OSError, ValueError, AttributeError):
            pass
        units.append(unit("style", d.name, head.group(1).strip() if head else d.name, f.relative_to(ROOT).as_posix(), 1,
                          one.group(1).strip() if one else first_sentence(text), tags, text))
    for folder, kind in (("playbook", "doc"), ("video-types", "doc"), ("engines", "doc"), ("cases", "case")):
        for f in sorted((ROOT / folder).glob("*.md")):
            if f.name == "README.md" and kind == "case":
                continue
            rel = f.relative_to(ROOT).as_posix()
            secs = readpath.outline(rel)
            title = next((h for lv, h, _, _ in secs if lv == 1 and h), f.stem)
            for lv, h, line, body in secs:
                name = title if lv == 1 else f"{title} › {h}"
                units.append(unit(kind, f"{rel}#{line}", name, rel, line, first_sentence(body), own_tags(body), body))
    return units


def search(units, query, kinds, n):
    q = terms(query)
    if not q:
        return [], []
    whole = [w.lower() for w in query.split() if w.strip()]
    docs = []
    for u in units:
        tf = Counter()
        for t in terms(u["title"]) + [x for tag in u["tags"] for x in terms(tag)]:
            tf[t] += 3
        for t in terms(u["summary"]):
            tf[t] += 2
        for t in terms(u["body"]):
            tf[t] += 1
        docs.append((u, tf, sum(tf.values())))
    N = len(docs)
    avg = sum(d[2] for d in docs) / max(1, N)
    df = Counter(t for _, tf, _ in docs for t in set(tf) if t in set(q))
    hits = []
    for u, tf, length in docs:
        if kinds and u["kind"] not in kinds:
            continue
        score, matched = 0.0, []
        for t in dict.fromkeys(q):
            f = tf.get(t, 0)
            if not f:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            score += idf * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * length / max(1.0, avg)))
            matched.append(t)
        cover = len(matched) / len(set(q))
        score *= 0.5 + cover   # a unit with more of the words outranks one that repeats one of them
        head = (u["title"] + " " + " ".join(u["tags"])).lower()
        for w in whole:
            if w in head:
                score += 2.0
                matched.append(w)
        if score > 0:
            hits.append(dict({k: v for k, v in u.items() if k != "body"}, score=round(score, 3), matched=sorted(set(matched)),
                             partial=len(set(q)) > 1 and cover < 0.5))
    hits.sort(key=lambda h: (-h["score"], h["file"], h["line"]))
    out, seen = [], Counter()
    for h in hits:   # those with half the words or more; a kind with none of them shows its best one, marked partial
        cap = n if n else (QUOTA[h["kind"]] if not kinds else 5)
        if seen[h["kind"]] < cap and not h["partial"]:
            out.append(h)
            seen[h["kind"]] += 1
    for k in KINDS:
        if not seen[k]:
            best = next((h for h in hits if h["kind"] == k), None)
            if best is not None:
                out.append(best)
    order = {k: i for i, k in enumerate(KINDS)}
    return sorted(out, key=lambda h: (order[h["kind"]], -h["score"])), q


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh know", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    ap.add_argument("words", nargs="*")
    ap.add_argument("--kind", help=f"only these kinds, comma-separated ({', '.join(KINDS)})")
    ap.add_argument("-n", type=int, default=0, help="this many of each kind")
    ap.add_argument("--index", action="store_true", help="the index itself, without the texts")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    kinds = [k.strip() for k in (a.kind or "").split(",") if k.strip()]
    if set(kinds) - set(KINDS) or a.n < 0:
        print(f"bin/vh know: --kind takes {', '.join(KINDS)}; -n is 0 or more", file=sys.stderr)
        return 2
    units = build()
    by_kind = dict(Counter(u["kind"] for u in units))
    if a.index:
        if a.words:
            print("bin/vh know: --index takes no words", file=sys.stderr)
            return 2
        meta = [dict({k: v for k, v in u.items() if k != "body"}, chars=len(u["body"])) for u in units]
        if a.json:
            print(json.dumps({"version": 1, "units": meta, "by_kind": by_kind}, ensure_ascii=False, indent=1))
        else:
            print(f"the index: {len(units)} units · " + " · ".join(f"{k} {by_kind.get(k, 0)}" for k in KINDS))
            for m in meta:
                print(f"  {m['kind']:<9} {m['file']}:{m['line']}  {readpath_cut(m['title'], 70)}")
        return 0
    query = " ".join(a.words).strip()
    if not query:
        print("bin/vh know: a few words to look for (bin/vh know 翻页 纸面 转场), or --index", file=sys.stderr)
        return 2
    hits, q = search(units, query, kinds, a.n)
    out = sys.stderr if a.json else sys.stdout
    print(f"know · {query} · {len(units)} units", file=out)
    kind = None
    for h in hits:
        if h["kind"] != kind:
            kind = h["kind"]
            print(f"{kind}", file=out)
        where = f"{h['file']}:{h['line']}" if h["kind"] in ("doc", "case") else h["file"]
        print(f"  {readpath_cut(h['title'], 56)}  ·  {where}", file=out)
        if h["summary"]:
            print(f"      {readpath_cut(h['summary'], 100)}", file=out)
        print(f"      matched: {' '.join(h['matched'])}" + (" (partial: under half the words)" if h["partial"] else ""), file=out)
    if not hits:
        print("  nothing matched: other words, or bin/vh recipes list / bin/vh style list", file=out)
    if a.json:
        print(json.dumps({"version": 1, "query": query, "terms": q, "hits": hits, "units": len(units), "by_kind": by_kind}, ensure_ascii=False, indent=1))
    return 0 if hits else 1


def readpath_cut(s, n):
    """One line, cut to n columns (a CJK character takes two)."""
    s, w, out = re.sub(r"\s+", " ", str(s or "")), 0, ""
    for ch in s:
        cw = 2 if ord(ch) > 0x2E7F else 1
        if w + cw > n:
            return out + "…"
        out, w = out + ch, w + cw
    return out


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
