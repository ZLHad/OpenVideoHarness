"""bin/vh new <type> <slug> --from <project>: the smallest form of a series pack (plan 4.7). A new project made the usual
way, then given what stays the same from one episode to the next, taken from a project made before; what it was
about is left behind. Stdlib only; bin/vh new runs it once the new project is made.

usage: python3 tools/series.py carry <from-project> <new-project> [--given aspect,watch,res,lang,effort,engine]

  carried   BRIEF.md: the Spec lines (effort, director, budget, assets, output, watch on, pace, resolution, review
            language, platform, language and narration, deliverables) and the Style and Text rules sections as the
            earlier project has them; the Outline's rows with their # 标签 and 时间 kept and their content emptied (the
            episode's skeleton and its proportions); Process as it is. The lines this command set from an option
            given now (--given) stay as given; when the frames differ, Output keeps the new size (its fps and length
            come over) and Watch on stays; the Engine and Type doc lines are the new project's.
            STYLE.md and style-refs/ as they are. The recipes the storyboard names (the 配方 and 转场出 columns, those
            in recipes/) and the components its files use (components/<name>), the sound effects its event lists
            place (audio/*events*.json: each sfx and how often), into series.json and one line at the top of
            STORYBOARD.md; DECISIONS.md gets a line saying where the episode comes from
  left      Content (concept, specifics, spine, motif, source material) and Acceptance as the template has them; the
            storyboard's shots, NOTES, REVIEW, the audio and the assets; the earlier project is only read
series.json: {"v": 1, "from", "at", "brief": [the Spec keys carried], "outline": rows, "style": bool, "style_refs",
"recipes", "components", "sfx": {name: count}, "unknown": [names in the storyboard that are no recipe]}.
Exit: 0 · 2 usage.
"""
import json, re, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_KEYS = ("Effort", "Director", "Budget", "Assets", "Output", "Watch on", "Pace", "Resolution", "Review language",
             "Platform / audience", "Language", "Deliverables")
GIVEN = {"effort": ("Effort",), "res": ("Resolution",), "lang": ("Review language",), "watch": ("Watch on",), "aspect": ("Watch on",)}
# (an --aspect given now keeps Output's size; its fps and length still come over: carry() puts the new size in the line)
KEEP_SECTIONS = ("Style", "Text rules", "Process")


def sections(text):
    """[(heading or None, lines)] split at ## headings; the part before the first is (None, lines)."""
    out = [(None, [])]
    for line in text.split("\n"):
        m = re.match(r"## +(.+?)\s*$", line)
        if m:
            out.append((m.group(1), [line]))
        else:
            out[-1][1].append(line)
    return out


def spec_lines(lines):
    """{key: line} of a Spec section ("- Key: value  <!-- … -->")."""
    out = {}
    for line in lines:
        m = re.match(r"- ([^:：]+?)\s*[:：]", line)
        if m and m.group(1) in SPEC_KEYS:
            out[m.group(1)] = line
    return out


def size_of(line):
    m = re.search(r"(\d{3,4})x(\d{3,4})", line or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def placeholder(line):
    return bool(re.search(r"[:：]\s*\{", line))


def skeleton_outline(lines):
    """The Outline table's rows with # 标签 时间 kept, the other cells emptied; (lines, rows kept)."""
    out, header, n = [], None, 0
    for line in lines:
        if line.startswith("|") and header is None:
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append(line)
            continue
        if line.startswith("|") and header is not None:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                out.append(line)
                continue
            keep = [c if h in ("#", "标签", "时间", "小节") else "{…}" for h, c in zip(header, cells)]
            out.append("| " + " | ".join(keep) + " |")
            n += 1
            continue
        if not line.startswith("|"):
            header = None if line.strip() else header
        out.append(line)
    return out, n


def recipe_ids():
    ids = set()
    for f in (ROOT / "recipes").rglob("*.md"):
        m = re.search(r"^id:\s*([a-z0-9-]+)\s*$", f.read_text(encoding="utf-8"), re.M)
        if m:
            ids.add(m.group(1))
    return ids


def storyboard_names(text):
    """The names in the 配方 and 转场出 columns of a storyboard's tables (placeholders left out)."""
    names, idx = [], None
    for line in text.splitlines():
        if not line.startswith("|"):
            idx = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if idx is None:
            idx = [i for i, c in enumerate(cells) if c in ("配方", "转场出")] or []
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        for i in idx:
            if i < len(cells) and cells[i] and not cells[i].startswith("{"):
                names += [x.strip(" `") for x in re.split(r"[,，/、·]| 或 ", cells[i].split("·")[0]) if x.strip(" `")]
    return names


def components_used(src):
    comps = ROOT / "components"
    if not comps.is_dir():
        return []
    known = {p.name for p in comps.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))}
    seen = set()
    for f in src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".mjs", ".html", ".json", ".md") and "node_modules" not in f.parts and f.stat().st_size < 2_000_000:
            for m in re.finditer(r"components/([a-z0-9][a-z0-9-]*)", f.read_text(encoding="utf-8", errors="replace")):
                if m.group(1) in known:
                    seen.add(m.group(1))
    return sorted(seen)


def sfx_used(src):
    counts = {}
    for f in sorted((src / "audio").glob("*events*.json")) if (src / "audio").is_dir() else []:
        if f.name.endswith(".events.json") and (f.parent / f.name[:-len(".events.json")]).exists():
            continue   # what sfx place wrote beside a track: the same events again
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        evs = d.get("events", []) if isinstance(d, dict) else d
        for e in evs if isinstance(evs, list) else []:
            if isinstance(e, dict) and isinstance(e.get("sfx"), str):
                name = Path(e["sfx"]).stem if "/" in e["sfx"] else e["sfx"]
                counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def carry(src, dst, given):
    src, dst = Path(src).resolve(), Path(dst).resolve()
    sb, db = (src / "BRIEF.md").read_text(encoding="utf-8"), (dst / "BRIEF.md").read_text(encoding="utf-8")
    ss, ds = dict(sections(sb)), sections(db)
    from_spec, new_spec = spec_lines(ss.get("Spec", [])), {}
    for h, lines in ds:
        if h == "Spec":
            new_spec = spec_lines(lines)
    locked = {k for g in given for k in GIVEN.get(g, ())}
    if size_of(from_spec.get("Output")) != size_of(new_spec.get("Output")):
        locked |= {"Watch on"}   # another frame: this command's watch default stays with it
    carried = []
    out = []
    for h, lines in ds:
        if h == "Spec":
            new = []
            for line in lines:
                m = re.match(r"- ([^:：]+?)\s*[:：]", line)
                k = m.group(1) if m else None
                if k in from_spec and k not in locked and not placeholder(from_spec[k]):
                    if k == "Output" and size_of(line) and size_of(from_spec[k]) != size_of(line):
                        w, hh = size_of(line)
                        new.append(re.sub(r"\d{3,4}x\d{3,4}", f"{w}x{hh}", from_spec[k], count=1))
                    else:
                        new.append(from_spec[k])
                    carried.append(k)
                else:
                    new.append(line)
            out.append((h, new))
        elif h in KEEP_SECTIONS and h in ss:
            out.append((h, ss[h]))
        elif h == "Outline" and "Outline" in ss:
            lines, rows = skeleton_outline(ss["Outline"])
            out.append((h, lines if rows else dict(ds)[h]))
        else:
            out.append((h, lines))
    rows = skeleton_outline(ss.get("Outline", []))[1]
    (dst / "BRIEF.md").write_text("\n".join("\n".join(lines) for _, lines in out), encoding="utf-8")
    style = (src / "STYLE.md").is_file()
    if style:
        shutil.copyfile(src / "STYLE.md", dst / "STYLE.md")
    refs = sorted(p.name for p in (src / "style-refs").iterdir() if p.is_dir()) if (src / "style-refs").is_dir() else []
    for r in refs:
        if not (dst / "style-refs" / r).exists():
            shutil.copytree(src / "style-refs" / r, dst / "style-refs" / r)
    names = storyboard_names((src / "STORYBOARD.md").read_text(encoding="utf-8")) if (src / "STORYBOARD.md").is_file() else []
    ids = recipe_ids()
    recipes = sorted({n for n in names if n in ids})
    unknown = sorted({n for n in names if n not in ids})
    comps, sfx = components_used(src), sfx_used(src)
    rec = {"v": 1, "from": str(src), "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "brief": carried, "outline": rows, "style": style,
           "style_refs": refs, "recipes": recipes, "components": comps, "sfx": sfx, "unknown": unknown}
    (dst / "series.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    bits = [f"配方 {'、'.join(recipes)}" if recipes else "", f"组件 {'、'.join(comps)}" if comps else "",
            "音效 " + "、".join(f"{k} ×{v}" for k, v in list(sfx.items())[:8]) if sfx else ""]
    bits = [b for b in bits if b]
    sbp = dst / "STORYBOARD.md"
    text = sbp.read_text(encoding="utf-8")
    line = (f"> 系列：沿用 `{src.name}` 的骨架（`bin/vh new --from`，见 series.json）" + (f"：{'；'.join(bits)}" if bits else "")
            + "。照用不用解释，换掉的写进 DECISIONS.md；内容全部重写。\n\n")
    first = text.find("\n") + 1
    sbp.write_text(text[:first] + "\n" + line + text[first:].lstrip("\n"), encoding="utf-8")
    dp = dst / "DECISIONS.md"
    dp.write_text(dp.read_text(encoding="utf-8").rstrip("\n") + f"\n\n- {time.strftime('%Y-%m-%d')} 沿用 `{src.name}` 的 BRIEF 骨架、STYLE、配方和声音分类（`bin/vh new --from`，见 series.json）；内容全部重写。\n",
                  encoding="utf-8")
    return rec


def main(argv):
    if len(argv) < 3 or argv[0] != "carry":
        print(__doc__.strip(), file=sys.stderr)
        return 2
    src, dst = Path(argv[1]), Path(argv[2])
    given = []
    if len(argv) > 3:
        if argv[3] != "--given" or len(argv) != 5:
            print("usage: python3 tools/series.py carry <from-project> <new-project> [--given a,b]", file=sys.stderr)
            return 2
        given = [g for g in argv[4].split(",") if g]
    for p in (src, dst):
        if not (p / "BRIEF.md").is_file():
            print(f"tools/series.py: {p} is not a project (no BRIEF.md)", file=sys.stderr)
            return 2
    rec = carry(src, dst, given)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
