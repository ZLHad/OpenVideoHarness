"""bin/vh concept: optional parts of the concept cards at gate ① (playbook/ideation-extras.md). Neither changes what a
gate ① stop hands over; each widens what the cards are chosen from.

usage: bin/vh concept roulette <project> [--from styles,sequences,levers] [--not a,b] [--n 1] [--reroll K] [--json]
       bin/vh concept board <project> <candidates.json> [--pick A,C,E] [--cols 3] [--out f.png] [--json]

  roulette  a framework the model would not reach for by itself, drawn with the project's name as the seed: a style
            preset (styles/), a whole-film skeleton (recipes/sequences/) or a lever of playbook/12 §3 (its table).
            The draw is the same each time for a project (the name without its date); --not leaves out the ones
            already thought of (the agent's own candidates, by id or name), and a style the project has attached
            (style-refs/) is left out too. --n draws that many, spread over the pools; --reroll K is the K-th draw
            instead of the first, said as such (a reroll goes into DECISIONS.md: the point is a framework no one
            picked). The card it asks for: what this framework makes of this material, whether it fits, and why.
  board     the "six, then three" page: up to nine candidate directions, a picture and a line each, on one page
            to look at before three of them are written up as cards. candidates.json: {"candidates": [{"id": "A",
            "title", "image" (a path, from the project or from the JSON's folder), "source" (designer, screenshot,
            library, roulette, other), "note"}]}. --pick marks the ones taken (a frame round each). The sources are
            counted on the page: two from designers' work, two from real screenshots, two from the library is the
            spread huashu-design suggests, a default, not a quota. Default out: <project>/out/check/concept-board.png
            (pillow, through uv; the same bytes for the same input)

--json: roulette {"version": 1, "project", "seed", "reroll", "picks": [{"pool", "id", "name", "line", "path"}],
"left_out": [...]}; board {"version": 1, "out", "candidates", "sources": {source: n}, "picked": [...]}.
Exit: 0 · 1 nothing to draw from, or a picture that cannot be read · 2 usage.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
POOLS = ("styles", "sequences", "levers")
SOURCES = {"designer": ("设计师作品", "a designer's work"), "screenshot": ("真实截图", "a real screenshot"),
           "library": ("风格库", "the style library"), "roulette": ("轮盘", "the roulette"), "other": ("其他", "other")}


class Usage(Exception):
    """A usage error: exit 2."""


def project(arg):
    from vhdraw import project_dir, Usage as NameUsage
    p = Path(arg).expanduser()
    try:
        d = p.resolve() if p.is_dir() else project_dir(arg)
    except (NameUsage, SystemExit) as e:
        raise Usage(str(e))
    if not (d / "BRIEF.md").is_file():
        raise Usage(f"{d} is not a project (no BRIEF.md)")
    return d


def slug_of(proj):
    """The project's name without its date: the seed stays when a project is made again on another day."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", proj.name)


def pool(name):
    """[{id, name, line, path}] of one pool, in a fixed order (by id)."""
    out = []
    if name == "styles":
        for t in sorted((ROOT / "styles").glob("*/tokens.json")):
            d = t.parent
            try:
                tok = json.loads(t.read_text(encoding="utf-8"))
            except ValueError:
                continue
            m = re.search(r"^一句话：(.+)$", (d / "STYLE.md").read_text(encoding="utf-8"), re.M) if (d / "STYLE.md").is_file() else None
            nm = tok.get("name") or {}
            out.append({"id": d.name, "name": nm.get("zh") or nm.get("en") or d.name, "line": m.group(1).strip() if m else "",
                        "path": f"styles/{d.name}/STYLE.md"})
    elif name == "sequences":
        import recipes
        for f in sorted((ROOT / "recipes" / "sequences").glob("*.md")):
            if f.name == "README.md":
                continue
            try:
                fm, _ = recipes.read(f)
            except recipes.FMError:
                continue
            out.append({"id": fm.get("id") or f.stem, "name": fm.get("name") or f.stem, "line": fm.get("one_liner") or "",
                        "path": f"recipes/sequences/{f.name}"})
    elif name == "levers":
        text = (ROOT / "playbook" / "12-ideation.md").read_text(encoding="utf-8")
        sec = text[text.index("## 3."):text.index("## 4.")]
        for row in re.findall(r"^\| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", sec, re.M):
            if row[0].strip() in ("撬法",) or set(row[0].strip()) <= set("-: "):
                continue
            out.append({"id": row[0].strip(), "name": row[0].strip(), "line": row[1].strip(), "path": "playbook/12-ideation.md §3"})
    return sorted(out, key=lambda x: x["id"])


def attached(proj):
    """The style presets the project has attached as references (style-refs/<preset>/)."""
    d = proj / "style-refs"
    return {p.name for p in d.iterdir() if p.is_dir()} if d.is_dir() else set()


def draw(seed, items, k):
    """The k-th item of a seeded order of items: each ranked by sha256(seed|id), so adding a preset moves few draws."""
    ranked = sorted(items, key=lambda x: hashlib.sha256(f"{seed}|{x['id']}".encode("utf-8")).hexdigest())
    return ranked[k % len(ranked)] if ranked else None


def cmd_roulette(a):
    proj = project(a.project)
    pools = [p.strip() for p in a.src.split(",") if p.strip()]
    bad = [p for p in pools if p not in POOLS]
    if bad or not pools:
        raise Usage(f"--from takes {', '.join(POOLS)}" + (f" (not {', '.join(bad)})" if bad else ""))
    seed = slug_of(proj)
    nots = {x.strip().lower() for x in (a.no or "").split(",") if x.strip()}
    have = attached(proj)
    picks, left = [], []
    for i in range(a.n):
        name = pools[i % len(pools)]
        items = []
        for it in pool(name):
            if it["id"].lower() in nots or it["name"].lower() in nots or (name == "styles" and it["id"] in have):
                left.append(f"{name}/{it['id']}")
                continue
            if any(p["id"] == it["id"] for p in picks):
                continue
            items.append(it)
        it = draw(f"{seed}|{name}", items, a.reroll)   # a pool drawn again: the picks are out of it, so the next in its order
        if it is None:
            print(f"bin/vh concept roulette: nothing left to draw in {name}", file=sys.stderr)
            return 1
        picks.append(dict(it, pool=name))
    out = sys.stderr if a.json else sys.stdout
    print(f"roulette · seed {seed}" + (f" · reroll {a.reroll} (say why in DECISIONS.md)" if a.reroll else "")
          + (f" · left out: {', '.join(sorted(set(left)))}" if left else ""), file=out)
    for p in picks:
        print(f"  {p['pool']}: {p['name']}" + (f" ({p['id']})" if p['id'] != p['name'] else "") + f" · {p['path']}", file=out)
        if p["line"]:
            print(f"    {p['line']}", file=out)
    print("  the card: 轮盘卡：{这个框架放到这份材料上是什么样}；合不合适：{…}；为什么：{…}", file=out)
    if a.json:
        print(json.dumps({"version": 1, "project": str(proj), "seed": seed, "reroll": a.reroll, "left_out": sorted(set(left)),
                          "picks": [{k: p[k] for k in ("pool", "id", "name", "line", "path")} for p in picks]}, ensure_ascii=False, indent=1))
    return 0


def lang_of(proj):
    m = re.search(r"^\s*[-*]\s*Review language\s*[:：]\s*(zh|en)\b", (proj / "BRIEF.md").read_text(encoding="utf-8"), re.M | re.I)
    return m.group(1).lower() if m else "zh"


def cmd_board(a):
    from PIL import Image, ImageDraw
    import vhdraw as V
    proj = project(a.project)
    src = Path(a.candidates).expanduser()
    try:
        cands = json.loads(src.read_text(encoding="utf-8"))["candidates"]
        assert isinstance(cands, list) and all(isinstance(c, dict) and c.get("id") for c in cands)
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as e:
        raise Usage(f"{a.candidates}: not {{\"candidates\": [{{\"id\", \"title\", \"image\", \"source\", \"note\"}}]}} ({e})")
    if not 2 <= len(cands) <= 9:
        raise Usage(f"{len(cands)} candidates: the board takes 2 to 9")
    ids = [str(c["id"]) for c in cands]
    picked = [x.strip() for x in (a.pick or "").split(",") if x.strip()]
    if set(picked) - set(ids):
        raise Usage(f"--pick names no candidate: {', '.join(sorted(set(picked) - set(ids)))}")
    for c in cands:
        if c.get("source", "other") not in SOURCES:
            raise Usage(f"candidate {c['id']}: source {c.get('source')!r} is not one of {', '.join(SOURCES)}")
    zh = lang_of(proj) == "zh"
    cols = max(1, min(a.cols, len(cands)))
    tw_, th_ = 560, 315
    pad, head, foot = 28, 120, 128
    rows = (len(cands) + cols - 1) // cols
    W, H = pad + cols * (tw_ + pad), head + rows * (th_ + foot + pad)
    img = Image.new("RGB", (W, H), V.BG)
    d = ImageDraw.Draw(img)
    counts = {}
    for c in cands:
        counts[c.get("source", "other")] = counts.get(c.get("source", "other"), 0) + 1
    title = ("六选三 · " if zh else "Six, then three · ") + slug_of(proj)
    V.text(d, (pad, 30), title, V.font(40, bold=True))
    tally = " · ".join(f"{SOURCES[s][0 if zh else 1]} {n}" for s, n in counts.items())
    V.text(d, (pad, 80), (("来源：" if zh else "sources: ") + tally) + (("　·　挑中：" if zh else "  ·  picked: ") + ", ".join(picked) if picked else ""),
           V.font(22), fill=V.MUTED)
    missing = []
    for i, c in enumerate(cands):
        x, y = pad + (i % cols) * (tw_ + pad), head + (i // cols) * (th_ + foot + pad)
        d.rectangle([x, y, x + tw_ - 1, y + th_ - 1], fill=V.FAINT)
        pic = None
        if c.get("image"):
            for base in (proj, src.parent, Path.cwd()):
                f = (base / c["image"]) if not Path(c["image"]).is_absolute() else Path(c["image"])
                if f.is_file():
                    pic = f
                    break
        if pic is not None:
            try:
                im = Image.open(pic).convert("RGB")
                im.thumbnail((tw_, th_))
                img.paste(im, (x + (tw_ - im.width) // 2, y + (th_ - im.height) // 2))
            except OSError:
                missing.append(f"{c['id']}: {c['image']} is not a picture")
        elif c.get("image"):
            missing.append(f"{c['id']}: no {c['image']}")
        if pic is None:
            V.text(d, (x + tw_ / 2, y + th_ / 2), "（没有图）" if zh else "(no picture)", V.font(24), fill=V.MUTED, anchor="mm")
        if c["id"] in picked:
            d.rectangle([x - 6, y - 6, x + tw_ + 5, y + th_ + 5], outline=V.RED, width=5)
        f_t, f_s = V.font(26, bold=True), V.font(20)
        V.text(d, (x, y + th_ + 12), V.fit(d, f"{c['id']} · {c.get('title', '')}", f_t, tw_), f_t)
        V.text(d, (x, y + th_ + 48), SOURCES[c.get("source", "other")][0 if zh else 1], f_s, fill=V.BLUE)
        for k, line in enumerate(V.wrap(d, c.get("note", ""), f_s, tw_, max_lines=2)):
            V.text(d, (x, y + th_ + 76 + k * 26), line, f_s, fill=V.MUTED)
    out = Path(a.out).expanduser() if a.out else proj / "out" / "check" / "concept-board.png"
    V.save(img, out)
    print(f"→ {V.shown(out, proj)}" + (f" · {len(picked)} picked" if picked else ""), file=sys.stderr if a.json else sys.stdout)
    for m in missing:
        print(f"! {m}", file=sys.stderr)
    if a.json:
        print(json.dumps({"version": 1, "out": str(out), "candidates": len(cands), "sources": counts, "picked": picked}, ensure_ascii=False, indent=1))
    return 1 if missing else 0


def parser():
    ap = argparse.ArgumentParser(prog="bin/vh concept", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    sp = ap.add_subparsers(dest="cmd", metavar="{roulette,board}")
    p = sp.add_parser("roulette", prog="bin/vh concept roulette", help="a framework drawn with the project's name as the seed")
    p.add_argument("project")
    p.add_argument("--from", dest="src", default=",".join(POOLS), help=f"pools, comma-separated ({', '.join(POOLS)})")
    p.add_argument("--not", dest="no", help="ids or names left out: what has been thought of already")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--reroll", type=int, default=0, metavar="K")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("board", prog="bin/vh concept board", help="the six-then-three page")
    p.add_argument("project")
    p.add_argument("candidates", metavar="candidates.json")
    p.add_argument("--pick", help="the ids taken, comma-separated")
    p.add_argument("--cols", type=int, default=3)
    p.add_argument("--out")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv):
    if not argv:
        parser().print_usage(sys.stderr)
        print("bin/vh concept: a subcommand (roulette, board)", file=sys.stderr)
        return 2
    a = parser().parse_args(argv)
    if a.cmd is None:
        parser().print_usage(sys.stderr)
        return 2
    if a.cmd == "roulette" and (a.n < 1 or a.reroll < 0):
        print("bin/vh concept roulette: --n is 1 or more, --reroll 0 or more", file=sys.stderr)
        return 2
    try:
        return {"roulette": cmd_roulette, "board": cmd_board}[a.cmd](a)
    except Usage as e:
        print(f"bin/vh concept {a.cmd}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
