"""bin/vh hdri: environment maps from Poly Haven (polyhaven.com, every HDRI CC0) for the Three.js layer's light and
background, and for Blender. Search the library; get one into the project at a size and a format, on record in the
ledger. Stdlib only.

usage: bin/vh hdri search <words…> [--category C] [-n 12] [--json] [--offline DIR]
       bin/vh hdri get <project> <hdri> [--res 1k|2k|4k|8k|16k] [--format hdr|exr] [--id ID] [--max-mb 600] [--rate 2M]
                  [--json] [--offline DIR]

  search  Poly Haven's HDRIs whose id, name, tags or categories hold every word (as a part of one), most downloaded
          first: the id to get, its name, the largest size it comes in, its categories, who made it. --category keeps
          the ones in that category (Poly Haven's: outdoor, indoor, studio, skies, night, sunrise-sunset, overcast …)
  get     <hdri>'s file into <project>/assets/hdri/<hdri>/ under Poly Haven's own name for it (<hdri>_2k.hdr), through
          tools/assets/fetch.py (a download that stopped is resumed), its md5 checked against Poly Haven's list (a
          mismatch is deleted and fails), and on record in assets/ledger.json: CC0, the asset's page
          (polyhaven.com/a/<hdri>), its authors, the file's sha256 (id hdri-<hdri>-<res>, -exr for an EXR). Then the
          Three.js layer's line for it: FILM.three.env = "assets/hdri/<hdri>/<hdri>_2k.hdr". The same file got again is
          said, and left as it is.
          --res (default 2k): 1k or 2k light a scene; a background seen through a lens wants 8k or more (a 2k map is
          2048 px round the whole horizon). --format (default hdr): hdr (RGBE, smaller to read) or exr (half floats).
          --max-mb: a file over this is refused before it starts (16k is about 400 MB as hdr, 1.3 GB as exr)
Poly Haven's API (api.polyhaven.com; its terms, github.com/Poly-Haven/Public-API ToS.md and polyhaven.com/our-api, read
2026-10-29): free for any use, commercial included, no key. Every request carries a User-Agent naming the tool
(tools/assets/fetch.py's, "OpenVideoHarness …"). A tool on the live API makes clear to its users that the assets come
from Poly Haven: every get says so, and the record names Poly Haven, the page and the authors. The HDRIs are CC0: a film
owes no credit (one is welcome: bin/vh assets credits lists them).
--json: {"version": 1, "tool", …}; search {"query", "category", "results": [{"id", "name", "max_resolution", "categories",
"tags", "authors", "downloads", "page"}]}; get {"project", "record", "file", "env", "download": {"bytes", "resumed"} | null}.
The lines go to stderr with --json.
--offline DIR: Poly Haven's answers from DIR/responses.json, recorded before (CONTRIBUTING.md, 联网的命令): no network;
tools/assets/fixtures/hdri has the ones the tests use.
Exit: 0 · 1 a download that failed, or a file whose md5 is not Poly Haven's · 2 usage: no project, no such HDRI, no such
size or format, an id taken.
"""
import argparse, hashlib, json, re, sys, time, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import assets as A, fetch, ledger, licenses   # noqa: E402,E401

PROG = "bin/vh hdri"
API = "https://api.polyhaven.com"
PAGE = "https://polyhaven.com/a/"
CC0 = ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")
HDRI = Path("assets") / "hdri"
out = sys.stdout   # the lines; stderr under --json


class Usage(A.Usage):
    pass


class Failed(Exception):
    """A download that failed, or a file that is not what Poly Haven lists: exit 1."""


def say(*a):
    print(*a, file=out)


def note_activity(what, paths):
    try:
        import activity
        activity.note(what, [str(p) for p in paths])
    except Exception:   # the log never fails a command
        pass


def authors(x):
    return ", ".join((x.get("authors") or {}).keys())


def size_word(res):
    """[16384, 8192] → 16k."""
    return f"{round(res[0] / 1024)}k" if isinstance(res, list) and res and isinstance(res[0], (int, float)) else "?"


def cmd_search(a):
    opener = fetch.opener_from(a.offline)
    try:
        lib = fetch.get_json(f"{API}/assets?t=hdris", opener=opener)
    except (fetch.FetchError, ConnectionError) as e:   # ConnectionError: no network
        raise Failed(f"Poly Haven's list did not come: {e}")
    if not isinstance(lib, dict):
        raise Failed("Poly Haven's list is not what its API gives (an object of id: asset)")
    words = [w.lower() for w in a.words]
    hits = []
    for hid, x in lib.items():
        if not isinstance(x, dict):
            continue
        cats = [str(c).lower() for c in x.get("categories") or []]
        hay = " ".join([hid, str(x.get("name", "")), " ".join(map(str, x.get("tags") or [])), " ".join(cats), str(x.get("category", ""))]).lower()
        if all(w in hay for w in words) and (not a.category or a.category.lower() in cats):
            hits.append((hid, x))
    hits.sort(key=lambda h: (-(h[1].get("download_count") or 0), h[0]))
    rows = [{"id": hid, "name": x.get("name", ""), "max_resolution": size_word(x.get("max_resolution")), "categories": x.get("categories") or [],
             "tags": x.get("tags") or [], "authors": authors(x), "downloads": x.get("download_count") or 0, "page": PAGE + hid} for hid, x in hits[:a.n]]
    for r in rows:
        cats = ", ".join(c for c in r["categories"] if not c.startswith("collection"))[:60]
        say(f"  {r['id']:<38} {r['name'][:30]:<30} {r['max_resolution']:>4} · {cats} · {r['authors']}")
    say(f"{len(rows)} of {len(hits)} HDRIs from Poly Haven (CC0) for {' '.join(a.words) or 'everything'}" + (f" in {a.category}" if a.category else "")
        + (f"; get one: {PROG} get <project> {rows[0]['id']} [--res 2k]" if rows else ""))
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} search", "query": a.words, "category": a.category, "results": rows}, ensure_ascii=False, indent=1))
    return 0


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cmd_get(a):
    project = A.find(a.project)
    hid = a.hdri
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]*", hid):
        raise Usage(f"{hid}: a Poly Haven id is lower-case letters, digits and _ (bin/vh hdri search finds them)")
    if a.id and not ledger.ID.match(a.id):
        raise Usage(f"--id {a.id}: letters, digits, . _ - (up to 64, not starting with . _ -)")
    if not re.fullmatch(r"\d+k", a.res):
        raise Usage(f"--res {a.res}: a size as Poly Haven writes it, 1k, 2k, 4k, 8k, 16k")
    try:
        rate = fetch.rate_of(a.rate)
    except ValueError as e:
        raise Usage(str(e))
    opener = fetch.opener_from(a.offline)
    media_opener = opener if isinstance(opener, fetch.Replay) else fetch.Live()   # a recording keeps no one's HDRI
    try:
        info = fetch.get_json(f"{API}/info/{hid}", opener=opener)
    except (fetch.FetchError, ConnectionError) as e:   # ConnectionError: no network
        if " 404" in str(e) or "HTTP 404" in str(e):
            raise Usage(f"Poly Haven has no {hid} (bin/vh hdri search <words> finds the ids)")
        raise Failed(f"Poly Haven's page for {hid} did not come: {e}")
    if not isinstance(info, dict) or info.get("type") != 0:
        raise Usage(f"{hid} is not an HDRI on Poly Haven" + (" (a texture or a model)" if isinstance(info, dict) and "type" in info else ""))
    try:
        files = fetch.get_json(f"{API}/files/{hid}", opener=opener)
    except (fetch.FetchError, ConnectionError) as e:   # ConnectionError: no network
        raise Failed(f"Poly Haven's file list for {hid} did not come: {e}")
    table = (files or {}).get("hdri") or {}
    sizes = sorted(table, key=lambda r: (len(r), r))
    if a.res not in table:
        raise Usage(f"{hid} comes in {', '.join(sizes) or 'no size'}, not {a.res}")
    f = (table[a.res] or {}).get(a.format)
    if not isinstance(f, dict) or not f.get("url"):
        raise Usage(f"{hid} at {a.res} comes as {', '.join(sorted(table[a.res] or {})) or 'nothing'}, not {a.format}")
    url, md5, size = f["url"], str(f.get("md5", "")).lower(), f.get("size")
    name = urllib.parse.unquote(Path(urllib.parse.urlsplit(url).path).name)
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.(hdr|exr)", name):
        name = f"{hid}_{a.res}.{a.format}"
    dest = project / HDRI / hid / name
    rid = a.id or f"hdri-{hid}-{a.res}" + ("-exr" if a.format == "exr" else "")
    policy, pfrom = ledger.policy_of(project)
    if not licenses.accepted("cc0", policy):   # never: CC0 is taken under every policy; said if that ever changes
        raise Failed(f"Assets: {policy} ({pfrom}) does not take CC0")
    say(f"{hid}: {info.get('name', hid)} · by {authors(info) or 'Poly Haven'} · from Poly Haven ({PAGE}{hid}), CC0")
    _, ents, _ = ledger.entries(project)
    mine = next((e["record"] for e in ents if e["record"].get("path") == ledger.rel(project, dest) and "removed" not in e["record"]), None)
    env = ledger.rel(project, dest)
    if mine and dest.is_file() and ledger.sha256_file(dest) == mine.get("sha256"):
        say(f"  {env} is here already, on record as {mine['id']}: left as it is")
        return done(a, project, mine, dest, env, None)
    if not mine and any(e["record"].get("id") == rid for e in ents):
        raise Usage(f"the id {rid} is on record already, for another file: --id another (ids are never reused)")
    t0 = time.monotonic()
    got = None
    if dest.is_file() and md5 and md5_file(dest) == md5:
        say(f"  {env} is here from a get that stopped after its download: kept, not downloaded again")
    else:
        try:
            try:
                dl = fetch.download(url, dest, rate=rate, opener=media_opener, max_bytes=int(a.max_mb * 1e6))
            except fetch.FetchError as e:
                raise Failed(str(e) + (" (--max-mb raises it)" if " cap" in str(e) else ""))
            got = {"bytes": dl["bytes"], "resumed": dl["resumed"]}
            if md5 and md5_file(dest) != md5:
                dest.unlink()
                raise Failed(f"{name}: its md5 is not the one Poly Haven lists ({md5}): deleted; get it again")
        except Failed:
            try:
                dest.parent.rmdir()   # the HDRI's folder, when nothing else is in it (a part kept for a resume is)
            except OSError:
                pass
            raise
    src = {"origin": "download", "url": PAGE + hid, "file_url": url, "provider": "polyhaven", "provider_id": hid, "title": info.get("name") or hid,
           "author": authors(info) or None, "retrieved": time.strftime("%Y-%m-%d")}
    try:
        rec, _, _ = ledger.add(project, str(dest), id=rid if not mine else mine["id"], kind="image", license=CC0[0], license_url=CC0[1], source=src,
                               tags=["hdri", "polyhaven", a.res, a.format], note=f"Poly Haven HDRI, {a.res} {a.format}" + (f", md5 {md5} as Poly Haven lists it" if md5 else ""),
                               update=bool(mine), by=f"{PROG} get")
    except (ledger.Refused, ValueError, ledger.LedgerError) as e:
        raise Usage(f"downloaded to {env}, but not registered: {e}")
    note_activity(f"got {rec['id']} ({hid} {a.res} {a.format}, cc0)", [project / ledger.LEDGER, dest])
    say(f"got {rec['id']}: {env} · {fetch.size_of(dest.stat().st_size)}" + (f" of {fetch.size_of(size)} listed" if size and got and got["resumed"] else "")
        + f" · {time.monotonic() - t0:.0f} s")
    return done(a, project, rec, dest, env, got)


def done(a, project, rec, dest, env, got):
    say(f'  the Three.js layer: FILM.three.env = "{env}" (background: "env" shows it; envRotation turns it)')
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} get", "project": str(project), "record": rec, "file": str(dest), "env": env, "download": got},
                         ensure_ascii=False, indent=1))
    return 0


def parser():
    p = argparse.ArgumentParser(prog=PROG, add_help=False, usage=__doc__.split("\n\n", 2)[1].split("\n\n")[0].replace("usage: ", "", 1))
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("search", add_help=False)
    s.add_argument("words", nargs="*")
    s.add_argument("--category")
    s.add_argument("-n", type=int, default=12)
    s.add_argument("--json", action="store_true")
    s.add_argument("--offline")
    g = sub.add_parser("get", add_help=False)
    g.add_argument("project")
    g.add_argument("hdri")
    g.add_argument("--res", default="2k")
    g.add_argument("--format", choices=("hdr", "exr"), default="hdr")
    g.add_argument("--id")
    g.add_argument("--max-mb", type=float, default=600)
    g.add_argument("--rate")
    g.add_argument("--json", action="store_true")
    g.add_argument("--offline")
    return p


def main(argv):
    global out
    if not argv or argv[0] in ("-h", "--help") or "-h" in argv or "--help" in argv:
        print(__doc__.split("\n\n", 1)[1].rstrip(), file=sys.stdout if argv else sys.stderr)
        return 0 if argv else 2
    if argv[0] not in ("search", "get"):
        print(f"{PROG}: no subcommand {argv[0]!r}: search or get ({PROG} -h)", file=sys.stderr)
        return 2
    try:
        a = parser().parse_args(argv)
    except SystemExit:
        return 2
    if a.json:
        out = sys.stderr
        A.out = sys.stderr
    try:
        if a.cmd == "search" and a.n < 1:
            raise Usage("-n is 1 or more")
        return {"search": cmd_search, "get": cmd_get}[a.cmd](a)
    except (Usage, A.Usage) as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 2
    except (Failed, fetch.FetchError, ConnectionError) as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
