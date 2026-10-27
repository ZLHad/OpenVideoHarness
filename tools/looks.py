"""bin/vh looks: the cross-film look ledger. Each film delivered leaves one record of how it looked and sounded, and a
new film asks, at gate ①, which of the last ones it looks like. The ledger lives outside the repo; the repo holds the
format (an asset record, tools/assets/asset.schema.json, with a "look" field) and this tool. Stdlib and ffmpeg.

usage: bin/vh looks add <project> [--film F] [--ledger DIR] [--json]
       bin/vh looks check <project> [--film F | --images a.png,b.png] [--last 8] [--ledger DIR] [--json]
       bin/vh looks list [--ledger DIR] [--json]

  add    measure a delivered film and append its record to <ledger>/ledger.jsonl (one line, O_APPEND): the film's
         path, sha256 and size; look: the background (the commonest colour along the frames' edges), the palette (the
         five commonest colours after it, merged within ΔE 12, each with its share), a layout fingerprint (an 8×5
         grid of brightness and of edge energy, averaged over the frames: up to 24, spread over the film), the fonts its page loaded (.render.json),
         the transitions and recipes of its storyboard (the 转场出 and 配方 columns of STORYBOARD.md, shots.json's
         transition, seam and recipe fields), the sound files of its newest mix that sit under an sfx folder, the
         style presets it attached. --film: that video, else the project's newest film (bin/vh render's)
  check  the same measures of the project now (--film, or --images: the concept cards' frames at gate ①, else its
         newest film) against the last --last films in the ledger: the same background (ΔE under 8), three or more
         of five palette colours shared (ΔE under 10), a layout correlation of 0.85 or more, a font, a transition, a
         sound file or a preset in common. It reports and exits 0: a film may repeat a look on purpose
  list   the films on record, newest last: when, the background and palette, what it is

The ledger: --ledger DIR, else $OVH_LOOKS, else ~/.ovh/looks (the user's own account keeps it where it keeps its
other notes). Each line is an asset record (v 1): id <project>-<film>, kind video, path (absolute), sha256, bytes,
license own, source {origin self, title}, aigc false, added_at, and look: {"bg", "palette": [{"hex", "share"}],
"layout": [80 numbers], "fonts", "transitions", "sounds", "styles", "type", "frames"}; a later line with the same id
supersedes an earlier one. --json: add {"version": 1, "ledger", "record"}; check {"version": 1, "ledger", "look",
"against": n, "hits": [{"id", "added_at", "same": [...]}]}; list {"version": 1, "ledger", "records"}. Exit: 0 ·
1 nothing to measure · 2 usage.
"""
import argparse, json, math, os, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "assets"))
sys.path.insert(0, str(ROOT / "tools"))
import ledger, uses   # noqa: E402,E401

W, H, N = 96, 54, 24          # the frames are measured this small: colours and layout, not detail
GW, GH = 8, 5                 # the layout grid
FONT_EXT = {".woff2", ".woff", ".ttf", ".otf", ".ttc"}


class Usage(Exception):
    """A usage error: exit 2."""


def where(a):
    return Path(a.ledger or os.environ.get("OVH_LOOKS") or "~/.ovh/looks").expanduser().resolve()


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


# ---- pictures, through ffmpeg ----

def duration(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise Usage(f"{video}: not a video ffprobe can read")


def raw(src, video=True):
    """Frames as rgb24 bytes, W×H each: N spread over a video (at the middle of N equal parts), or one picture."""
    vf = f"scale={W}:{H}:flags=area,format=rgb24"
    if video:
        d = duration(src)
        vf = f"fps={N / d:.6f}:start_time={d / N / 2:.6f}," + vf
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vf", vf, "-frames:v", str(N if video else 1), "-f", "rawvideo", "-"],
                       capture_output=True)
    n = W * H * 3
    return [r.stdout[i:i + n] for i in range(0, len(r.stdout) - n + 1, n)]


def lab(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(c)) for c in rgb)
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116   # noqa: E731
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def de(a, b):
    """ΔE (CIE76) between two hex colours."""
    la, lb = lab(rgb_of(a)), lab(rgb_of(b))
    return math.dist(la, lb)


def rgb_of(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def hexed(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def measure(frames):
    """{bg, palette, layout} of rgb24 frames."""
    counts, sums, edge = Counter(), {}, Counter()
    cells = [[0.0, 0.0, 0] for _ in range(GW * GH)]   # brightness, edge energy, pixels
    for f in frames:
        for y in range(H):
            for x in range(W):
                i = (y * W + x) * 3
                r, g, b = f[i], f[i + 1], f[i + 2]
                k = (r >> 4, g >> 4, b >> 4)
                counts[k] += 1
                s = sums.setdefault(k, [0, 0, 0])
                s[0] += r; s[1] += g; s[2] += b
                if x in (0, W - 1) or y in (0, H - 1):
                    edge[k] += 1
                lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                j = ((y * GH) // H) * GW + (x * GW) // W
                c = cells[j]
                c[0] += lum
                if x + 1 < W and y + 1 < H:
                    n1, n2 = i + 3, i + W * 3
                    c[1] += abs(lum - (0.2126 * f[n1] + 0.7152 * f[n1 + 1] + 0.0722 * f[n1 + 2])) + \
                        abs(lum - (0.2126 * f[n2] + 0.7152 * f[n2 + 1] + 0.0722 * f[n2 + 2]))
                c[2] += 1
    total = sum(counts.values()) or 1
    mean = {k: hexed([v / counts[k] for v in s]) for k, s in sums.items()}
    bg = mean[edge.most_common(1)[0][0]] if edge else "#000000"
    merged = []   # [hex, pixels]: a colour within ΔE 12 of a bigger one joins it
    for k, n in counts.most_common(200):
        h = mean[k]
        near = next((m for m in merged if de(m[0], h) < 12), None)
        if near:
            near[1] += n
        else:
            merged.append([h, n])
    merged.sort(key=lambda m: -m[1])
    pal = [{"hex": h, "share": round(n / total, 3)} for h, n in merged if de(h, bg) >= 8][:5]
    layout = [round(c[0] / max(1, c[2]), 2) for c in cells] + [round(c[1] / max(1, c[2]), 2) for c in cells]
    return {"bg": bg, "palette": pal, "layout": layout}


def corr(a, b):
    if len(a) != len(b) or len(a) < 2:
        return None
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return None if sa < 1e-6 or sb < 1e-6 else sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def layout_r(a, b):
    """How alike two layouts are: the brightness grids correlated, and the edge grids, each on its own (a flat frame
    has no layout to compare), averaged over the ones that can be."""
    n = GW * GH
    rs = [r for r in (corr(a[:n], b[:n]), corr(a[n:], b[n:])) if r is not None] if len(a) == len(b) == 2 * n else []
    return sum(rs) / len(rs) if rs else None


# ---- what the project says about itself ----

def columns(md, names):
    """The cells of the named columns in a markdown file's tables (header row by name), placeholders left out."""
    out, idx = [], None
    for line in md.splitlines():
        if not line.startswith("|"):
            idx = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if idx is None:
            idx = [i for i, c in enumerate(cells) if c in names] or None
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        for i in idx or []:
            if i < len(cells) and cells[i] and not cells[i].startswith("{"):
                out += [x.strip(" `") for x in re.split(r"[,，/、·]| 或 ", cells[i]) if x.strip(" `")]
    return out


def own(proj, film=None):
    """{fonts, transitions, sounds, styles, type} from the project's records: what its film's page loaded, its
    storyboard, its newest mix, its attached presets."""
    try:
        u = uses.uses(proj, film=film) if film else uses.uses(proj)
    except ValueError:
        u = {"films": [], "mixes": []}
    fonts = sorted({Path(p).stem for f in u.get("films", []) for p in f.get("files", {}) if Path(p).suffix.lower() in FONT_EXT})
    sounds = sorted({Path(p).stem for m in u.get("mixes", [])[-1:] for p in m.get("inputs", {}) if "sfx" in p.lower()})
    trans = []
    sb = proj / "STORYBOARD.md"
    if sb.is_file():
        trans += columns(sb.read_text(encoding="utf-8"), ("转场出", "配方", "转场", "transition", "recipe"))
    import shot_source   # the project's shot table: shots.json, or an edit list's entries
    try:
        shots, _, _ = shot_source.rows(proj)
        for s in shots if isinstance(shots, list) else []:
            for k in ("transition", "seam", "recipe"):
                v = s.get(k) if isinstance(s, dict) else None
                v = v.get("type") if k == "transition" and isinstance(v, dict) else v   # an edit list's {"type", "duration"}
                if isinstance(v, str) and v.strip():
                    trans.append(v.strip())
    except (OSError, ValueError, SystemExit):
        pass
    styles = sorted(p.name for p in (proj / "style-refs").iterdir() if p.is_dir()) if (proj / "style-refs").is_dir() else []
    m = re.search(r"<!--\s*from\s+(\d\d)-", (proj / "BRIEF.md").read_text(encoding="utf-8"))
    return {"fonts": fonts, "transitions": sorted(set(trans)), "sounds": sounds, "styles": styles, "type": m.group(1) if m else None}


def newest_film(proj):
    """The project's newest film that bin/vh render made (it has a .render.json), by its file's time."""
    fs = [v for v, side in uses.films(proj) if side.is_file()]
    return max(fs, key=lambda v: v.stat().st_mtime) if fs else None


# ---- the subcommands ----

def look_of(proj, film=None, images=None):
    if images:
        frames = [f for p in images for f in raw(p, video=False)]
        src = "images"
    else:
        film = film or newest_film(proj)
        if film is None:
            return None, None
        frames, src = raw(film), "film"
    if not frames:
        return None, film
    look = measure(frames)
    look.update(own(proj, str(film) if film and not images else None))
    look.update({"frames": len(frames), "measured_from": src})
    return look, film


def cmd_add(a):
    proj = project(a.project)
    film = Path(a.film).expanduser().resolve() if a.film else newest_film(proj)
    if film is None or not film.is_file():
        print(f"bin/vh looks add: {'no such film: ' + a.film if a.film else 'no film in ' + str(proj) + ' (bin/vh render makes one; or --film)'}", file=sys.stderr)
        return 1
    look, _ = look_of(proj, film)
    if look is None:
        print(f"bin/vh looks add: no frames could be read from {film}", file=sys.stderr)
        return 1
    h, size = ledger.digest(film)
    rid = ledger.slug(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", proj.name) + "-" + film.stem)[:64]
    rec = {"v": 1, "id": rid, "kind": "video", "path": str(film), "sha256": h, "bytes": size,
           "license": {"class": "own", "by": "given"}, "source": {"origin": "self", "title": proj.name}, "aigc": False,
           "added_at": ledger.iso(), "look": look}
    bad = ledger.validate(rec)
    if bad:
        raise Usage("; ".join(bad))
    d = where(a)
    ledger.append_jsonl(d / "ledger.jsonl", rec)
    out = sys.stderr if a.json else sys.stdout
    print(f"✓ {rid} onto {d / 'ledger.jsonl'}", file=out)
    print(f"  bg {look['bg']} · palette {' '.join(p['hex'] for p in look['palette'])} · fonts {', '.join(look['fonts']) or '–'}"
          f" · transitions {', '.join(look['transitions']) or '–'} · sounds {len(look['sounds'])} · styles {', '.join(look['styles']) or '–'}", file=out)
    if a.json:
        print(json.dumps({"version": 1, "ledger": str(d), "record": rec}, ensure_ascii=False, indent=1))
    return 0


def same(look, other):
    """What two looks share, as short phrases."""
    o, s = other.get("look") or {}, []
    if o.get("bg") and de(look["bg"], o["bg"]) < 8:
        s.append(f"the background ({o['bg']})")
    shared = sum(1 for p in look["palette"] if any(de(p["hex"], q["hex"]) < 10 for q in o.get("palette", [])))
    if shared >= 3:
        s.append(f"{shared} of {len(look['palette'])} palette colours")
    c = layout_r(look["layout"], o.get("layout") or [])
    if c is not None and c >= 0.85:
        s.append(f"the layout (r = {c:.2f})")
    for k, name in (("fonts", "font"), ("transitions", "transition"), ("sounds", "sound"), ("styles", "preset")):
        both = sorted(set(look.get(k) or []) & set(o.get(k) or []))
        if both:
            s.append(f"{name}{'s' if len(both) > 1 else ''} {', '.join(both)}")
    return s


def cmd_check(a):
    proj = project(a.project)
    images = [x.strip() for x in (a.images or "").split(",") if x.strip()]
    for p in images:
        if not Path(p).expanduser().is_file() and not (proj / p).is_file():
            raise Usage(f"no such picture: {p}")
    images = [str(Path(p).expanduser()) if Path(p).expanduser().is_file() else str(proj / p) for p in images]
    look, film = look_of(proj, Path(a.film).expanduser().resolve() if a.film else None, images or None)
    if look is None:
        print("bin/vh looks check: nothing to measure: --images (the concept cards' frames) or --film, or a film rendered in the project", file=sys.stderr)
        return 1
    d = where(a)
    f = d / "ledger.jsonl"
    recs = ledger.read_jsonl(f) if f.is_file() else []
    mine = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", proj.name)
    recs = [r for r in recs if not str(r.get("id", "")).startswith(ledger.slug(mine) + "-")][-a.last:]
    hits = [{"id": r.get("id"), "added_at": r.get("added_at"), "same": same(look, r)} for r in recs]
    hits = [h for h in hits if h["same"]]
    out = sys.stderr if a.json else sys.stdout
    print(f"{proj.name} ({look['measured_from']}: {look['frames']} frame{'s' if look['frames'] != 1 else ''}) against the last {len(recs)} of {f}"
          + ("" if f.is_file() else " (no ledger yet)"), file=out)
    print(f"  bg {look['bg']} · palette {' '.join(p['hex'] for p in look['palette'])}", file=out)
    for h in hits:
        print(f"  ! like {h['id']} ({(h['added_at'] or '')[:10]}): {'; '.join(h['same'])}", file=out)
    print(f"  {len(hits)} of {len(recs)} alike" + (": say in DECISIONS.md if it is on purpose" if hits else ""), file=out)
    if a.json:
        print(json.dumps({"version": 1, "ledger": str(d), "look": look, "against": len(recs), "hits": hits}, ensure_ascii=False, indent=1))
    return 0


def cmd_list(a):
    d = where(a)
    f = d / "ledger.jsonl"
    recs = ledger.read_jsonl(f) if f.is_file() else []
    out = sys.stderr if a.json else sys.stdout
    print(f"{f} · {len(recs)} film{'s' if len(recs) != 1 else ''}", file=out)
    for r in recs:
        lk = r.get("look") or {}
        print(f"  {(r.get('added_at') or '')[:10]}  {r.get('id', ''):<36} bg {lk.get('bg', '–')}  {' '.join(p['hex'] for p in lk.get('palette', []))}"
              f"  {', '.join(lk.get('styles') or [])}", file=out)
    if a.json:
        print(json.dumps({"version": 1, "ledger": str(d), "records": recs}, ensure_ascii=False, indent=1))
    return 0


def parser():
    ap = argparse.ArgumentParser(prog="bin/vh looks", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    sp = ap.add_subparsers(dest="cmd", metavar="{add,check,list}")
    p = sp.add_parser("add", prog="bin/vh looks add", help="a delivered film's look onto the ledger")
    p.add_argument("project")
    p.add_argument("--film")
    p.add_argument("--ledger")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("check", prog="bin/vh looks check", help="which of the last films the project looks like")
    p.add_argument("project")
    p.add_argument("--film")
    p.add_argument("--images", help="pictures, comma-separated: the concept cards' frames")
    p.add_argument("--last", type=int, default=8)
    p.add_argument("--ledger")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("list", prog="bin/vh looks list", help="the films on record")
    p.add_argument("--ledger")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv):
    if not argv:
        parser().print_usage(sys.stderr)
        print("bin/vh looks: a subcommand (add, check, list)", file=sys.stderr)
        return 2
    a = parser().parse_args(argv)
    if a.cmd is None:
        parser().print_usage(sys.stderr)
        return 2
    if a.cmd == "check" and (a.last < 1 or (a.film and a.images)):
        print("bin/vh looks check: --last is 1 or more; --film or --images, not both", file=sys.stderr)
        return 2
    try:
        return {"add": cmd_add, "check": cmd_check, "list": cmd_list}[a.cmd](a)
    except Usage as e:
        print(f"bin/vh looks {a.cmd}: {e}", file=sys.stderr)
        return 2
    except ledger.LedgerError as e:
        print(f"bin/vh looks {a.cmd}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
