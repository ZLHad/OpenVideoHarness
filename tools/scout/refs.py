"""bin/vh ref: a project's references (a video, a post, an image, a page it learns from), one asset record each in
<project>/research/refs.json, in the shape of tools/assets/asset.schema.json. A reference is studied, not shown: it
stays out of bin/vh assets check and credits. The day any of it goes on screen it is material: clear it and register
it with bin/vh assets add (its derived_from can name the reference's id).

usage: bin/vh ref add <project> <url|file> [--why TEXT] [--type video|post|image|page] [--title T] [--author A]
                  [--license TEXT] [--class C] [--tags a,b] [--id ID] [--thumb] [--offline DIR] [--sleep S] [--json]
       bin/vh ref list <project> [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

  add   a URL: a YouTube video, a Bilibili BV or an X post is looked up the way bin/vh scout post looks one up (its
        title, author, followers, counts, date, cover), and the look is kept as research/refs/<id>/meta.json; --thumb
        also fetches its cover there (thumb.jpg). A page scout does not read (Douyin, Xiaohongshu, an article) is
        recorded as given: --title, --author and the rest read off it in the built-in browser. A file (a frame, a
        screenshot, a clip the user gave) is recorded where it is (inside the project: relative; else absolute).
        The record: kind (video, image, other), path (the folder, or the file) and its sha256 (a folder's: of its
        listing), source (origin download for a URL, else user; url, provider, provider_id, title, author,
        retrieved), the licence (--license is classified, --class given outright; else what the platform says, which
        is all rights reserved by its author unless it names a Creative Commons licence: unknown, not cleared), aigc
        false, and ref: {type, why, platform, followers, metrics, date, method}. --why: what it is a reference for
        (its opening, the cover, how it moves). An id is <platform>-<its id> (yt-, bili-, x-, dy-, xhs-) or the
        title's slug; ids are never reused, and a URL or a file on record already is refused
  list  the references: id, type, platform, the counts at the time, title, why

--json: {"version": 1, "project", "file", "refs": [record…]} on stdout (add: "ref": the record), the lines on stderr.
--offline DIR: the look and the cover from DIR/responses.json (tools/assets/fetch.py), no network. Exit: 0 · 1 a look
failed or was blocked · 2 usage.
"""
import argparse, fcntl, json, os, re, sys, time, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "assets"))
import fetch, ledger, licenses, sources   # noqa: E402,E401
from sources import Blocked, SourceError   # noqa: E402

PROG = "bin/vh ref"
FILE = Path("research") / "refs.json"
LOCK = Path("research") / ".refs.lock"
FOLDER = Path("research") / "refs"
SHORT = {"youtube": "yt", "bilibili": "bili", "x": "x", "douyin": "dy", "xiaohongshu": "xhs"}
TYPES = ("video", "post", "image", "page")
out = sys.stdout


class Usage(Exception):
    """A usage error: exit 2."""


def say(*a):
    print(*a, file=out)


def find(arg):
    import scout
    try:
        return scout.project(arg)
    except scout.Usage as e:
        raise Usage(str(e))


def empty():
    return {"v": 1, "note": "the project's references: studied, not shown (bin/vh ref; tools/assets/asset.schema.json)", "assets": [], "events": []}


def read(project):
    f = Path(project) / FILE
    if not f.is_file():
        return empty()
    try:
        return ledger.read_ledger(f)
    except ledger.LedgerError as e:
        raise Usage(str(e))


class Locked:
    def __init__(self, project):
        self.f = Path(project) / LOCK

    def __enter__(self):
        self.f.parent.mkdir(parents=True, exist_ok=True)
        self.h = open(self.f, "a")
        fcntl.flock(self.h.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.h.fileno(), fcntl.LOCK_UN)
        self.h.close()


CC = re.compile(r"creative\s*commons|\bcc[\s-]*(?:by|0)\b|public\s*domain", re.I)


def licence_of(o, a):
    """(license dict) for a reference: given (--class outright, --license classified), else the licence its platform
    names when that is a Creative Commons one or the public domain (YouTube's CC BY), else unknown: all rights reserved
    by its author, not cleared. A platform's own label is never classified ("original" is the uploader's claim, not
    the project's own material)."""
    if a.license_class:
        return {"class": a.license_class, "by": "given", **({"name": a.license} if a.license else {})}
    if a.license:
        c, _ = licenses.classify(a.license)
        return {"class": c, "name": a.license, "by": "classifier"}
    name = (o or {}).get("license")
    if name and CC.search(name):
        c, _ = licenses.classify(name)
        return {"class": c if c not in ("own", "generated", "managed") else "unknown", "name": name, "by": "classifier"}
    plat = (o or {}).get("platform")
    said = {"youtube": "YouTube's standard licence: all rights reserved by the author", "x": "the author's post on X: all rights reserved",
            "bilibili": "Bilibili: all rights reserved by the uploader", "douyin": "Douyin: all rights reserved by the author",
            "xiaohongshu": "Xiaohongshu: all rights reserved by the author"}.get(plat, "not stated")
    return {"class": "unknown", "name": said, "by": "classifier"}


def cmd_add(a):
    project = find(a.project)
    target = a.target.strip()
    net = sources.Net(a.offline, a.sleep)
    is_url = target.startswith(("http://", "https://"))
    obs, plat, nid, kind = None, None, None, None
    if is_url:
        plat, what, nid = sources.platform_of(target)
        if (plat, what) in (("youtube", "video"), ("bilibili", "video"), ("x", "status")):
            try:
                obs = sources.lookup(net, target)
            except (Blocked, SourceError) as e:
                say(f"✗ {'blocked: ' if isinstance(e, Blocked) else ''}{e}")
                if isinstance(e, Blocked):
                    say("  nothing was retried: read it in the built-in browser and give --title, --author (and the counts in --why or a note)")
                return 1
        rtype = a.type or ("post" if plat == "x" or what == "post" else "video" if what == "video" else "page")
        kind = {"video": "video", "image": "image"}.get(rtype, "other")
    else:
        f = ledger.find_file(project, target)
        if f is None:
            raise Usage(f"no such file: {target} (from here, nor in the project)")
        kind = ledger.guess_kind(f)
        rtype = a.type or ("video" if kind == "video" else "image" if kind == "image" else "page")
    title = a.title or (obs or {}).get("title")
    author = a.author or (obs or {}).get("author")
    with Locked(project):
        d = read(project)
        recs = [r for r in d["assets"] if isinstance(r, dict)]
        taken = {r.get("id") for r in recs}
        if is_url:
            url = (obs or {}).get("url") or target
            same = next((r for r in recs if (r.get("source") or {}).get("url") in (url, fetch.redact(url), target)), None)
        else:
            same = next((r for r in recs if r.get("path") == ledger.rel(project, f)), None)
        if same is not None:
            raise Usage(f"{target} is on record already as {same['id']}")
        if a.id:
            if a.id in taken:
                raise Usage(f"the id {a.id} is taken (ids are never reused)")
            rid = a.id
        else:
            if plat in SHORT and nid:
                base = f"{SHORT[plat]}-{nid}"
            elif is_url:   # a page: its address, which a title in another script would not give
                u = urllib.parse.urlsplit(target)
                base = ledger.slug(f"{u.hostname or 'page'}-{u.path.rstrip('/').rsplit('/', 1)[-1] or 'index'}")
            else:
                base = ledger.slug(Path(target).stem)
            base = base[:64]
            rid, n = base, 1
            while rid in taken:
                n += 1
                rid = f"{base[:60]}-{n}"
        if not ledger.ID.match(rid):
            raise Usage(f"the id {rid!r}: letters, digits, . _ - (up to 64, not starting with . _ -)")
        now = ledger.iso()
        if is_url:
            folder = project / FOLDER / rid
            folder.mkdir(parents=True, exist_ok=True)
            meta = {"v": 1, "url": url, "fetched_at": now, **({k: v for k, v in obs.items() if k != "url"} if obs else
                                                               {"platform": plat, "method": "given by hand"})}
            for k, v in (("title", title), ("author", author)):
                if v:
                    meta[k] = v
            (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            if a.thumb and (obs or {}).get("thumb"):
                try:
                    net.pace.wait(obs["thumb"])
                    fetch.download(obs["thumb"], folder / "thumb.jpg", opener=net.opener, retries=1)
                except fetch.FetchError as e:
                    say(f"! the cover was not fetched: {e}")
            elif a.thumb:
                say("! no cover to fetch: the look gave none")
            path = ledger.rel(project, folder)
        else:
            path = ledger.rel(project, f)
        h, size = ledger.digest(project / path if not os.path.isabs(path) else Path(path))
        src = {"origin": a.origin or ("download" if is_url else "user")}
        if is_url:
            src["url"] = fetch.redact(url) if "?" in url and plat not in SHORT else url
            src["provider"] = plat
            if nid:
                src["provider_id"] = nid
            src["retrieved"] = now[:10]
        for k, v in (("title", title), ("author", author)):
            if v:
                src[k] = v
        ref = {"type": rtype}
        if a.why:
            ref["why"] = a.why
        if is_url:
            ref["platform"] = plat
        for k in ("followers", "metrics", "date", "duration", "method"):
            if (obs or {}).get(k) is not None:
                ref[k] = obs[k]
        rec = {"v": 1, "id": rid, "kind": kind, "path": path, "sha256": h, "bytes": size, "license": licence_of(obs or {"platform": plat}, a),
               "source": src, "aigc": False, "added_at": now, "ref": ref}
        if a.tags:
            rec["tags"] = [t.strip() for t in a.tags.split(",") if t.strip()]
        bad = ledger.validate(rec)
        if bad:
            raise Usage("; ".join(bad))
        d["assets"].append(rec)
        d["events"].append({"t": round(time.time(), 3), "at": now, "event": "add", "id": rid, "sha256": h, "by": "bin/vh ref add"})
        ledger.write_ledger(project / FILE, d)
    say(f"✓ {rid} · {rtype} · {cut(title or target, 60)}" + (f" · {sources_line(ref)}" if ref.get("metrics") else ""))
    say(f"  {FILE.as_posix()} · {path} · licence {rec['license']['class']} (studied, not shown: on screen it is material, bin/vh assets add)")
    if a.json:
        print(json.dumps({"version": 1, "project": str(project), "file": str(project / FILE), "ref": rec}, ensure_ascii=False, indent=1))
    return 0


def sources_line(ref):
    m = ref.get("metrics") or {}
    import scout
    parts = [f"{scout.human(m[k])} {k}" for k in ("views", "likes", "comments") if m.get(k) is not None]
    if ref.get("followers"):
        parts.append(f"{scout.human(ref['followers'])} followers")
    return ", ".join(parts)


def cut(s, n):
    import scout
    return scout.cut(s, n)


def cmd_list(a):
    project = find(a.project)
    d = read(project)
    recs = [r for r in d["assets"] if isinstance(r, dict)]
    say(f"{FILE.as_posix()} · {len(recs)} reference{'s' if len(recs) != 1 else ''} (studied, not shown)")
    for r in recs:
        ref = r.get("ref") or {}
        say(f"  {r.get('id', ''):<24} {ref.get('type', ''):<6} {ref.get('platform', 'file'):<10} {cut((r.get('source') or {}).get('title') or r.get('path'), 44)}"
            + (f"  · {sources_line(ref)}" if ref.get("metrics") else ""))
        if ref.get("why"):
            say(f"  {'':<24} why: {cut(ref['why'], 80)}")
    if a.json:
        print(json.dumps({"version": 1, "project": str(project), "file": str(project / FILE), "refs": recs}, ensure_ascii=False, indent=1))
    return 0


def parser():
    ap = argparse.ArgumentParser(prog=PROG, description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    sp = ap.add_subparsers(dest="cmd", metavar="{add,list}")
    p = sp.add_parser("add", prog=f"{PROG} add", help="record a reference")
    p.add_argument("project")
    p.add_argument("target", metavar="url|file")
    p.add_argument("--why", help="what it is a reference for")
    p.add_argument("--type", choices=TYPES)
    p.add_argument("--title")
    p.add_argument("--author")
    p.add_argument("--license", help="the licence as the source writes it")
    p.add_argument("--class", dest="license_class", choices=licenses.CLASSES, help="the licence class outright")
    p.add_argument("--origin", choices=ledger.ORIGINS)
    p.add_argument("--tags")
    p.add_argument("--id")
    p.add_argument("--thumb", action="store_true", help="also fetch its cover")
    p.add_argument("--offline", metavar="DIR")
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("list", prog=f"{PROG} list", help="the references")
    p.add_argument("project")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv):
    global out
    if not argv:
        parser().print_usage(sys.stderr)
        print(f"{PROG}: a subcommand (add, list)", file=sys.stderr)
        return 2
    a = parser().parse_args(argv)
    if a.cmd is None:
        parser().print_usage(sys.stderr)
        return 2
    if a.json:
        out = sys.stderr
    try:
        return {"add": cmd_add, "list": cmd_list}[a.cmd](a)
    except Usage as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 2
    except (OSError, fetch.FetchError) as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
