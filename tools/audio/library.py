"""bin/vh sfx search|pick, bgm search|pick and sound add|list: a sound library outside the repo, Openverse searched with
no key, and every pick into the project's ledger with its licence and credit. Stdlib only, and ffmpeg (bgm pick's beat
grid: bin/vh beats, librosa through uv).

usage: bin/vh sfx search <query> [--top 8] [--dur 0.3-2] [--where all|library|openverse] [--source freesound] [--project P]
                  [--audition [--out f.wav]] [--json] [--offline DIR]
       bin/vh sfx pick <project> <ref> --as NAME [--used-by S03] [--json] [--offline DIR]
       bin/vh bgm search <query> [--top 8] [--len 60] [--where all|library|openverse] [--project P] [--json] [--offline DIR]
       bin/vh bgm pick <project> <ref> [--as music] [--len 60] [--fade 1.5] [--beats f.beats.json | --no-beats] [--json]
                  [--offline DIR]
       bin/vh sound add <file|folder …> --source NAME [--kind sfx|bgm] [--license TEXT] [--license-url U] [--class C]
                  [--author A] [--attribution TEXT] [--restrict no_resell,no_ai_train] [--json]
       bin/vh sound list [--kind sfx|bgm] [--source NAME] [--json]
--lib DIR on any of them: the library (else $OVH_SOUND_LIB, else LOCAL.md's 声音库 / Sound library line, else ~/.ovh/sound).

The library: <lib>/ledger.jsonl, one asset record a line (tools/assets/asset.schema.json; appended, a later line with the
same id supersedes), with "sound": {"kind": sfx|bgm, "duration", "channels", "rate", "restrictions"}; the files a pick
downloaded under <lib>/<kind>/openverse/, previews for --audition under <lib>/cache/ (not on record, deletable). The
library is the user's, outside the repo (its files are other people's work); the repo has only this tool and the format.

  search   the library first (each query word against the title, the tags and the path; --dur keeps that length range,
           seconds), then Openverse (api.openverse.org, no key: anonymously 20 searches a minute, 200 a day): sfx from
           Freesound (--source another Openverse source), bgm from its music (mostly Jamendo, CC BY). Each result: the ref
           to pick, its title, length, licence class and whether the project's Assets policy takes it (--project; without
           one, strict). Under strict only CC0 and CC BY are asked for. Search in English: the sites and most packs are
           indexed so. --audition: the top results one after another, 0.6 s apart, into one WAV (--out, default
           ./sfx-search.wav) and a .txt of what plays when, to listen to as bin/vh sfx audition does. The last search's
           results stay in <lib>/cache/search.json, so a pick takes the ref's first 8 characters
  pick     <ref>: lib:<id> (the library's), or openverse:<id or its first 8 characters>. An Openverse item is
           downloaded into the library first (Freesound's HQ preview, an MP3: fine for effects; the original WAV needs a
           Freesound account) and recorded there; only an http(s) link, of at most 100 MB, is taken. Then into the
           project, as 48 kHz PCM: sfx to audio/sfx/<NAME>.wav (a
           name taken: <NAME>_a.wav, _b …, which bin/vh qa reads as takes of one sound), bgm to audio/<as>.wav with
           audio/<as>.beats.json. Each is one record in the project's assets/ledger.json (origin library; the source, the
           licence, and the site's credit line verbatim as attribution), so bin/vh assets credits and deliver have its
           credit. Under Assets: strict, a licence strict does not take is refused before anything is downloaded.
           bgm pick: --len cuts at the last downbeat at or before that many seconds (bin/vh beats on the whole track,
           or --beats a grid you made, or --no-beats to cut at --len itself), with 8 ms off at the cut so it does not
           click, and --fade seconds of fade-out before it; the beats file keeps the grid up to the cut. An outside
           track's beats are detected, not exact the way bin/vh music's are: check them before cutting hard to them
  add      register files already on disk (a pack: Sonniss, Kenney, Incompetech, a folder of your own) in the library,
           where they are: one record a sound file (WAV, FLAC, MP3, OGG, AIFF, M4A), its sha256, length and channels,
           tags from its folders and name. --license is classified (tools/assets/licenses.py: Kenney is CC0, Sonniss and
           Pixabay free, Incompetech's free tier CC BY); --restrict notes what the terms forbid (Sonniss: no_resell,
           no_ai_train). A file whose bytes are on record already is skipped
  list     the library: counts by kind, source and licence class, and each record
--json: {"version": 1, "tool", …}; the lines go to stderr. --offline DIR: the answers (and files) from DIR/responses.json,
recorded before (CONTRIBUTING.md, 联网的命令): no network.
Exit: 0 · 1 a download, a conversion or a licence refused · 2 usage: no project, no such ref, a name or an id taken.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile, time, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools" / "assets"))
sys.path.insert(0, str(ROOT / "tools"))
import assets as A, fetch, ledger, licenses   # noqa: E402,E401

OPENVERSE = "https://api.openverse.org/v1/audio/"
AUDIO = (".wav", ".flac", ".mp3", ".ogg", ".oga", ".aif", ".aiff", ".m4a", ".opus")
LICENCE_NAMES = {"cc0": "CC0", "pdm": "Public Domain Mark", "by": "CC BY", "by-sa": "CC BY-SA", "by-nc": "CC BY-NC", "by-nd": "CC BY-ND",
                 "by-nc-sa": "CC BY-NC-SA", "by-nc-nd": "CC BY-NC-ND", "sampling+": "CC Sampling+", "nc-sampling+": "CC NC-Sampling+"}
PROVIDERS = {"freesound": "freesound", "jamendo": "jamendo", "wikimedia_audio": "wikimedia-commons", "ccmixter": "ccmixter"}
out = sys.stdout   # the lines; stderr under --json


class Usage(A.Usage):
    pass


class Failed(Exception):
    """A download, a conversion or a licence refused: exit 1."""


def say(*a):
    print(*a, file=out)


# ---- the library ----

def lib_dir(arg=None):
    if arg:
        return Path(arg).expanduser()
    if os.environ.get("OVH_SOUND_LIB"):
        return Path(os.environ["OVH_SOUND_LIB"]).expanduser()
    try:
        t = ledger.local_md().read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^[ \t]*[-*]?[ \t]*(?:\*\*)?(?:声音库|sound library)(?:\*\*)?[ \t]*[:：][ \t]*`?([^`\n]+?)`?[ \t]*$", t, re.I | re.M)
        if m and not m.group(1).startswith("{"):
            return Path(m.group(1).strip()).expanduser()
    except OSError:
        pass
    return Path("~/.ovh/sound").expanduser()


def lib_records(lib):
    f = lib / "ledger.jsonl"
    return ledger.read_jsonl(f) if f.is_file() else []


def lib_path(lib, r):
    return Path(r["path"]) if os.path.isabs(r["path"]) else lib / r["path"]


def probe(path):
    """(duration s, channels, rate) of a sound file, or (None, None, None)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels,sample_rate:format=duration", "-of", "json",
                        str(path)], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
        s = (j.get("streams") or [{}])[0]
        return round(float(j["format"]["duration"]), 3), int(s.get("channels") or 0) or None, int(s.get("sample_rate") or 0) or None
    except (ValueError, KeyError, TypeError, IndexError):
        return None, None, None


def words(s):
    return [w for w in re.split(r"[^0-9a-z一-鿿]+", (s or "").lower()) if w]


def dur_range(s):
    if not s:
        return None
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)?\s*-\s*(\d+(?:\.\d+)?)?\s*", s)
    if not m or not (m.group(1) or m.group(2)):
        raise Usage(f"--dur {s!r}: seconds as a-b (0.3-2), a- or -b")
    return float(m.group(1) or 0), float(m.group(2) or math.inf)


def search_library(lib, q, kind, dur):
    qs = words(q)
    found = []
    for r in lib_records(lib):
        if "removed" in r or (r.get("sound") or {}).get("kind") != kind:
            continue
        d = (r.get("sound") or {}).get("duration")
        if dur and (d is None or not dur[0] <= d <= dur[1]):
            continue
        hay = set(words(" ".join([str((r.get("source") or {}).get("title") or ""), " ".join(r.get("tags") or []), r.get("path", "")])))
        score = sum(1 for w in qs if w in hay or any(h.startswith(w) for h in hay))
        if score:
            found.append({"ref": f"lib:{r['id']}", "where": "library", "title": (r.get("source") or {}).get("title") or Path(r["path"]).stem,
                          "duration": d, "class": ledger.class_of(r), "license": (r.get("license") or {}).get("name") or "",
                          "author": (r.get("source") or {}).get("author") or "", "source": (r.get("source") or {}).get("provider") or "",
                          "score": score, "record": r})
    found.sort(key=lambda x: (-x["score"], x["title"]))
    return found


# ---- Openverse ----

def openverse_url(q, kind, n, policy, source=None):
    p = [("q", q), ("page_size", n)]
    if kind == "bgm":
        p.append(("category", "music"))
    elif source or kind == "sfx":
        p.append(("source", source or "freesound"))
    if policy == "strict":
        p.append(("license", "cc0,by"))
    return OPENVERSE + "?" + urllib.parse.urlencode(p)


def ov_item(r):
    lic = str(r.get("license") or "")
    name = (LICENCE_NAMES.get(lic, lic.upper()) + (f" {r['license_version']}" if r.get("license_version") else "")).strip()
    cls, why = licenses.classify(name, r.get("license_url"))
    tags = [t.get("name") for t in r.get("tags") or [] if isinstance(t, dict) and t.get("name")]
    ext = {"mp32": ".mp3"}.get(str(r.get("filetype") or "").lower(), "." + str(r.get("filetype") or "mp3").lower())
    return {"ref": f"openverse:{r.get('id')}", "where": "openverse", "id": r.get("id"), "title": r.get("title") or "", "author": r.get("creator") or "",
            "duration": round(r["duration"] / 1000, 3) if isinstance(r.get("duration"), (int, float)) else None, "license": name,
            "license_url": r.get("license_url") or "", "class": cls, "why": why, "page": r.get("foreign_landing_url") or "", "file_url": r.get("url") or "",
            "ext": ext if re.fullmatch(r"\.[a-z0-9]{2,5}", ext) else ".mp3", "source": r.get("source") or "", "provider": r.get("provider") or "",
            "attribution": r.get("attribution") or "", "tags": tags[:12], "genres": r.get("genres") or [],
            "pack": (r.get("audio_set") or {}).get("title") if isinstance(r.get("audio_set"), dict) else None}


def search_openverse(q, kind, n, policy, source, opener, dur=None):
    try:
        d = fetch.get_json(openverse_url(q, kind, max(n, 20) if dur else n, policy, source), opener)
    except fetch.FetchError as e:
        hint = " (Openverse lets an anonymous client make 20 searches a minute, 200 a day)" if "429" in str(e) else ""
        raise Failed(f"{e}{hint}")
    items = [ov_item(r) for r in d.get("results") or [] if isinstance(r, dict) and r.get("id")]
    if dur:
        items = [x for x in items if x["duration"] is not None and dur[0] <= x["duration"] <= dur[1]]
    return items[:n], d.get("result_count")


def cache_search(lib, items):
    f = lib / "cache" / "search.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    keep = [{k: v for k, v in x.items() if k != "record"} for x in items if x["where"] == "openverse"]
    f.write_text(json.dumps({"v": 1, "t": round(time.time(), 3), "results": keep}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def resolve_ov(lib, key, opener):
    """An Openverse item by its id, or by the first 8+ characters of one in the last search."""
    try:
        cached = json.loads((lib / "cache" / "search.json").read_text(encoding="utf-8")).get("results", [])
    except (OSError, ValueError):
        cached = []
    hits = [x for x in cached if str(x.get("id", "")).startswith(key)]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise Usage(f"openverse:{key} is the start of {len(hits)} results of the last search: give more of it")
    if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", key):
        raise Usage(f"openverse:{key}: not an id, nor the start of one in the last search (bin/vh sfx search first, or the whole id)")
    try:
        return ov_item(fetch.get_json(f"{OPENVERSE}{key}/", opener))
    except fetch.FetchError as e:
        raise Failed(str(e))


# ---- picks ----

MAX_BYTES = 100_000_000   # a sound or a track; a link to more than this is not one


def take(url, dest, opener):
    """fetch.download, for a link from a search's answer (other people's data): http(s) only, at most MAX_BYTES."""
    if urllib.parse.urlsplit(url).scheme not in ("https", "http"):
        raise fetch.FetchError(f"{fetch.redact(url)}: not an http(s) link: not downloaded")
    return fetch.download(url, dest, opener=opener, max_bytes=MAX_BYTES)


def into_library(lib, it, kind, opener):
    """The library's record of an Openverse item, downloading and recording it the first time."""
    rid = f"ov-{it['id']}"
    have = next((r for r in lib_records(lib) if r.get("id") == rid and "removed" not in r), None)
    if have and lib_path(lib, have).is_file():
        return have
    dest = lib / kind / "openverse" / f"{it['id']}{it['ext']}"
    try:
        take(it["file_url"], dest, opener)
    except fetch.FetchError as e:
        raise Failed(str(e))
    h, size = ledger.digest(dest)
    d, ch, sr = probe(dest)
    rec = {"v": 1, "id": rid, "kind": "audio", "path": dest.relative_to(lib).as_posix(), "sha256": h, "bytes": size,
           "license": {"class": it["class"], "name": it["license"], **({"url": it["license_url"]} if it["license_url"] else {}), "by": "classifier"},
           "source": {"origin": "download", "url": fetch.redact(it["page"]) if it["page"] else None, "file_url": fetch.redact(it["file_url"]),
                      "provider": PROVIDERS.get(it["source"], it["source"] or "openverse"), "provider_id": it["id"], "title": it["title"],
                      "author": it["author"], "retrieved": time.strftime("%Y-%m-%d"), "library": "openverse"},
           "aigc": False, "added_at": ledger.iso(), "tags": it["tags"], "sound": {"kind": kind, "duration": d, "channels": ch, "rate": sr}}
    rec["source"] = {k: v for k, v in rec["source"].items() if v}
    if it.get("attribution") and licenses.attribution(it["class"]) == "required":   # the site's line, verbatim (CC0 asks for none)
        rec["attribution"] = it["attribution"]
    bad = ledger.validate(rec)
    if bad:
        raise Failed(f"the library record of {it['ref']} would not be valid: {'; '.join(bad)}")
    ledger.append_jsonl(lib / "ledger.jsonl", rec)
    return rec


def from_ref(lib, ref, kind, opener, policy, project):
    """(the library record, the item it came from or None) for a ref; under the policy's refusal, before any download."""
    m = re.fullmatch(r"(lib|openverse):(.+)", ref.strip())
    if not m:
        raise Usage(f"{ref!r}: lib:<id> or openverse:<id> (bin/vh {kind} search lists them)")
    if m.group(1) == "lib":
        r = next((x for x in lib_records(lib) if x.get("id") == m.group(2) and "removed" not in x), None)
        if r is None:
            raise Usage(f"{ref}: not in the library {lib} (bin/vh sound list)")
        cls = ledger.class_of(r)
        it = None
    else:
        it = resolve_ov(lib, m.group(2), opener)
        cls = it["class"]
    if not licenses.accepted(cls, policy[0]):
        raise Failed(f"{ref}: {cls}: Assets: {policy[0]} ({policy[1]}) does not take it: nothing downloaded. Another one, or, if the user "
                     "takes the risk, their BRIEF says Assets: record")
    return (into_library(lib, it, kind, opener) if it else r), it


def project_record(project, dest, lib, r, kind, used_by, by):
    src = {k: v for k, v in (r.get("source") or {}).items() if k != "origin"}
    src.update({"origin": "library", "library": src.get("library") or lib.name})
    lic = r.get("license") or {}
    note = f"picked from the sound library {lib} ({r['path']}, its record {r['id']})"
    restr = (r.get("sound") or {}).get("restrictions")
    if restr:
        note += "; its terms forbid: " + ", ".join(restr)
    pid = ledger.slug(dest.stem)
    _, ents, _ = ledger.entries(project)
    taken = {e["record"].get("id") for e in ents}
    base, n = pid, 1
    while pid in taken:
        n += 1
        pid = f"{base}-{n}"
    rec, _, _ = ledger.add(project, str(dest), id=pid, kind="audio", license=lic.get("name"), license_url=lic.get("url"),
                           license_class=lic.get("class") if lic.get("by") == "given" else None, source=src, attribution=r.get("attribution"),
                           tags=[kind] + [t for t in r.get("tags") or [] if isinstance(t, str)][:6], used_by=used_by, note=note,
                           extra={"library_id": r["id"], "library_sha256": r.get("sha256")}, by=by)
    return rec


def to_wav(src, dest, start=None, end=None, fade=None):
    """A 48 kHz 16-bit WAV of src (mono or stereo as it is; more channels folded to stereo), cut at end with 8 ms off and
    an optional fade-out of fade seconds before it."""
    af = ["aresample=48000"]
    if end is not None:
        if fade:
            af.append(f"afade=t=out:st={max(0.0, end - fade):.3f}:d={fade:.3f}")
        af.append(f"afade=t=out:st={max(0.0, end - 0.008):.3f}:d=0.008")
    ch = probe(src)[1] or 2
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.stem}.part.wav")
    argv = ["ffmpeg", "-v", "error", "-y", "-i", str(src)] + (["-t", f"{end:.3f}"] if end is not None else []) + ["-vn", "-af", ",".join(af),
            "-c:a", "pcm_s16le"] + (["-ac", "2"] if ch > 2 else []) + [str(tmp)]
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode:
        tmp.unlink(missing_ok=True)
        raise Failed(f"ffmpeg ({src.name} → {dest.name}): {r.stderr.strip()[-400:]}")
    os.replace(tmp, dest)


def note_activity(what, paths):
    try:
        import activity
        activity.note(what, [str(p) for p in paths])
    except Exception:   # the log never fails a command
        pass


# ---- commands ----

def policy_for(project_arg):
    if not project_arg:
        return "strict", "no project: strict"
    return ledger.policy_of(A.find(project_arg))


def show(items, policy):
    for x in items:
        taken = licenses.accepted(x["class"], policy)
        d = f"{x['duration']:.1f} s" if x.get("duration") is not None else "? s"
        say(f" {' ' if taken else '!'} {x['ref'][:18] if x['where'] == 'openverse' else x['ref']}  {x['title'][:56]}  · {d} · {x['class']}"
            + (f" ({x['license']})" if x.get("license") else "") + (f" · {x['author'][:24]}" if x.get("author") else "")
            + (f" · {x['source']}" if x.get("source") else "") + ("" if taken else f" (not taken under {policy})"))


def audition(lib, items, outf, opener):
    files = []
    for x in items:
        if x["where"] == "library":
            files.append((x, lib_path(lib, x["record"])))
            continue
        f = lib / "cache" / "preview" / f"{x['id']}{x['ext']}"
        if not f.is_file():
            try:
                take(x["file_url"], f, opener)
            except fetch.FetchError as e:
                say(f"  ! {x['ref'][:18]}: not fetched for the audition ({e})")
                continue
        files.append((x, f))
    if not files:
        raise Failed("nothing to play")
    graph = "".join(f"[{k}:a]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur=0.6[a{k}];" for k in range(len(files))) \
        + "".join(f"[a{k}]" for k in range(len(files))) + f"concat=n={len(files)}:v=0:a=1[o]"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum((["-i", str(f)] for _, f in files), []) + ["-filter_complex", graph, "-map", "[o]",
                       "-c:a", "pcm_s16le", str(outf)], capture_output=True, text=True)
    if r.returncode:
        raise Failed(f"ffmpeg (the audition): {r.stderr.strip()[-300:]}")
    t, lines = 0.0, []
    for x, f in files:
        d = probe(f)[0] or x.get("duration") or 0
        lines.append(f"{t:7.2f} s  {x['ref']}  {x['title']}  ({x['class']})")
        t += d + 0.6
    Path(str(outf) + ".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def cmd_search(a, kind):
    lib = lib_dir(a.lib)
    policy = policy_for(a.project)
    dur = dur_range(getattr(a, "dur", None))
    if kind == "bgm" and a.len:
        dur = (a.len, math.inf)
    items = []
    if a.where in ("all", "library"):
        items += search_library(lib, a.query, kind, dur)[:a.top]
    total = None
    if a.where in ("all", "openverse"):
        ov, total = search_openverse(a.query, kind, a.top, policy[0], getattr(a, "source", None), fetch.opener_from(a.offline), dur)
        items += ov
        cache_search(lib, ov)
    lines = audition(lib, items[:a.top], Path(a.out or f"./{kind}-search.wav"), fetch.opener_from(a.offline)) if getattr(a, "audition", False) and items else None
    if a.json:
        print(json.dumps({"version": 1, "tool": f"bin/vh {kind} search", "query": a.query, "library": str(lib), "policy": policy[0], "openverse_count": total,
                          "results": [dict({k: v for k, v in x.items() if k != "record"}, taken=licenses.accepted(x["class"], policy[0])) for x in items],
                          "audition": (a.out or f"./{kind}-search.wav") if lines else None}, ensure_ascii=False, indent=1))
    say(f"{kind} search {a.query!r}: {sum(1 for x in items if x['where'] == 'library')} in the library ({lib}), "
        + (f"{sum(1 for x in items if x['where'] == 'openverse')} from Openverse (of {total})" if total is not None else "Openverse not asked")
        + f" · Assets: {policy[0]}")
    show(items, policy[0])
    if lines:
        say(f"  audition: {a.out or f'./{kind}-search.wav'} (what plays when: its .txt)")
    return 0


def cmd_pick(a, kind):
    project = A.find(a.project)
    lib = lib_dir(a.lib)
    policy = ledger.policy_of(project)
    name = a.as_ or ("music" if kind == "bgm" else None)
    if not name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}", name):
        raise Usage("--as NAME: the sound's name in the project (letters, digits, . _ -)" if kind == "sfx" else f"--as {name!r}: letters, digits, . _ -")
    opener = fetch.opener_from(a.offline)
    r, it = from_ref(lib, a.ref, kind, opener, policy, project)
    src = lib_path(lib, r)
    if not src.is_file():
        raise Failed(f"{r['id']}: its file is not there ({src}): bin/vh sound list")
    used = [x.strip() for x in a.used_by.split(",") if x.strip()] if getattr(a, "used_by", None) else None
    if kind == "sfx":
        d = project / "audio" / "sfx"
        dest = d / f"{name}.wav"
        k = 0
        while dest.exists():   # takes of one sound: name_a, name_b …, which bin/vh qa reads as one family
            dest = d / f"{name}_{chr(ord('a') + k)}.wav"
            k += 1
            if k > 25:
                raise Usage(f"{name}: 26 takes already")
        to_wav(src, dest)
        extra = {}
    else:
        dest = project / "audio" / f"{name}.wav"
        if dest.exists():
            raise Usage(f"{ledger.rel(project, dest)} is there already: another --as, or remove it first")
        grid, how = None, None
        with tempfile.TemporaryDirectory() as tmp:
            whole = Path(tmp) / "whole.wav"
            to_wav(src, whole)
            if a.beats:
                bf = ledger.find_file(project, a.beats) or Path(a.beats)
                try:
                    grid, how = json.loads(Path(bf).read_text(encoding="utf-8")), f"the grid in {a.beats}"
                except (OSError, ValueError) as e:
                    raise Usage(f"--beats {a.beats}: {e}")
            elif not a.no_beats:
                b = subprocess.run([str(ROOT / "bin" / "vh"), "beats", str(whole), str(Path(tmp) / "whole.beats.json")], capture_output=True, text=True)
                if b.returncode == 0:
                    grid, how = json.loads((Path(tmp) / "whole.beats.json").read_text(encoding="utf-8")), "bin/vh beats (detected)"
                else:
                    say(f"  ! bin/vh beats failed ({(b.stderr or b.stdout).strip()[-160:]}): cut without a grid (--beats a grid, or --no-beats)")
            whole_d = probe(whole)[0]
            end = None
            if a.len:
                if a.len >= (whole_d or 0):
                    say(f"  · the track is {whole_d:.1f} s: shorter than --len {a.len}, kept whole")
                else:
                    downs = [t for t in (grid or {}).get("downbeats", []) if isinstance(t, (int, float)) and 0 < t <= a.len + 1e-6]
                    end = max(downs) if downs and max(downs) >= a.len * 0.75 else a.len
            to_wav(whole, dest, end=end, fade=a.fade if end is not None else None)
        length = end if end is not None else whole_d
        if grid is not None:
            g = {k: v for k, v in grid.items()}
            for k in ("beats", "downbeats"):
                if isinstance(g.get(k), list):
                    g[k] = [t for t in g[k] if isinstance(t, (int, float)) and t < length - 1e-6]
            for k in ("hits", "kick", "snare", "lifts"):
                if isinstance(g.get(k), list):
                    g[k] = [x for x in g[k] if isinstance(x, dict) and isinstance(x.get("t"), (int, float)) and x["t"] < length - 1e-6]
            g["duration"] = round(length, 3)
            g["note"] = f"bin/vh bgm pick: {how}, kept up to the cut at {length:.3f} s of {r['id']}"
            (project / "audio" / f"{name}.beats.json").write_text(json.dumps(g, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        extra = {"cut": round(length, 3), "grid": how}
    try:
        rec = project_record(project, dest, lib, r, kind, used or (["bgm"] if kind == "bgm" else None), f"bin/vh {kind} pick")
    except (ledger.Refused, ValueError, ledger.LedgerError) as e:
        raise Usage(f"made {ledger.rel(project, dest)}, but not registered: {e}")
    note_activity(f"picked {r['id']} → {ledger.rel(project, dest)} ({rec['license']['class']})", [project / ledger.LEDGER, dest])
    say(f"picked {r['id']} → {ledger.rel(project, dest)} · {rec['license']['class']}" + (f" ({rec['license'].get('name')})" if rec["license"].get("name") else "")
        + f" · on record as {rec['id']}" + (f" · cut at {extra['cut']:.3f} s ({extra['grid'] or 'no grid'})" if kind == "bgm" and extra.get("cut") else ""))
    if licenses.attribution(rec["license"]["class"]) == "required":
        say(f"  credit: {rec.get('attribution') or '(its author and source: bin/vh assets credits)'}")
    if kind == "bgm" and (project / "audio" / f"{name}.beats.json").exists():
        say(f"  beats: {ledger.rel(project, project / 'audio' / f'{name}.beats.json')} (detected: check before cutting hard to them)")
    if a.json:
        print(json.dumps({"version": 1, "tool": f"bin/vh {kind} pick", "project": str(project), "file": ledger.rel(project, dest), "record": rec,
                          "library_record": r, **extra}, ensure_ascii=False, indent=1))
    return 0


def cmd_add(a):
    lib = lib_dir(a.lib)
    if a.license_class and a.license_class not in licenses.CLASSES:
        raise Usage(f"--class {a.license_class}: one of {', '.join(licenses.CLASSES)}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,30}", a.source or ""):
        raise Usage("--source NAME: where the pack is from (sonniss, kenney, incompetech, own …)")
    files = []   # (the file, the folder it was given under: its tags are the path from there)
    for x in a.paths:
        p = Path(x).expanduser()
        if p.is_dir():
            files += [(f, p) for f in sorted(p.rglob("*")) if f.is_file() and f.suffix.lower() in AUDIO and not any(s.startswith(".") for s in f.relative_to(p).parts)]
        elif p.is_file() and p.suffix.lower() in AUDIO:
            files.append((p, p.parent))
        else:
            raise Usage(f"{x}: no such sound file or folder")
    if not files:
        raise Usage("no sound files there (" + ", ".join(AUDIO) + ")")
    have = lib_records(lib)
    shas = {r.get("sha256") for r in have}
    ids = {r.get("id") for r in have}
    cls, _ = licenses.classify(a.license or "", a.license_url) if (a.license or a.license_url) else ("unknown", None)
    if a.license_class:
        cls = a.license_class
    restrict = [x.strip() for x in (a.restrict or "").split(",") if x.strip()]
    added, skipped = [], 0
    for f, under in files:
        h, size = ledger.digest(f)
        if h in shas:
            skipped += 1
            continue
        try:
            rel = f.resolve().relative_to(lib.resolve()).as_posix()
        except ValueError:
            rel = f.resolve().as_posix()
        base = ledger.slug(f"{a.source}-{f.stem}")
        rid, n = base, 1
        while rid in ids:
            n += 1
            rid = f"{base}-{n}"
        d, ch, sr = probe(f)
        tags = list(dict.fromkeys(w for part in [under.name] + list(f.relative_to(under).parent.parts) + [f.stem] for w in words(part)
                                  if len(w) > 2 and not w.isdigit()))[:16]
        rec = {"v": 1, "id": rid, "kind": "audio", "path": rel, "sha256": h, "bytes": size,
               "license": {"class": cls, **({"name": a.license} if a.license else {}), **({"url": a.license_url} if a.license_url else {}),
                           "by": "given" if a.license_class else "classifier"},
               "source": {"origin": a.origin, "provider": a.source, "title": f.stem.replace("_", " "), **({"author": a.author} if a.author else {}),
                          "retrieved": time.strftime("%Y-%m-%d")},
               "aigc": False, "added_at": ledger.iso(), "tags": tags, "sound": {"kind": a.kind, "duration": d, "channels": ch, "rate": sr,
                                                                                **({"restrictions": restrict} if restrict else {})}}
        if a.attribution:
            rec["attribution"] = a.attribution
        bad = ledger.validate(rec)
        if bad:
            raise Usage(f"{f}: the record would not be valid: {'; '.join(bad)}")
        ledger.append_jsonl(lib / "ledger.jsonl", rec)
        shas.add(h)
        ids.add(rid)
        added.append(rec)
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh sound add", "library": str(lib), "added": added, "skipped": skipped}, ensure_ascii=False, indent=1))
    say(f"sound add: {len(added)} file(s) into {lib}/ledger.jsonl ({a.kind}, {a.source}, {cls})" + (f"; {skipped} on record already" if skipped else ""))
    if licenses.risks(cls):
        say(f"  ! {', '.join(licenses.RISK_WORDS[k] for k in licenses.risks(cls))}: a project under Assets: strict will not take these")
    if licenses.attribution(cls) == "required" and not (a.attribution or a.author):
        say("  ! the licence asks for a credit: --attribution or --author (the exact line the pack asks for)")
    return 0


def cmd_list(a):
    lib = lib_dir(a.lib)
    rs = [r for r in lib_records(lib) if "removed" not in r and (not a.kind or (r.get("sound") or {}).get("kind") == a.kind)
          and (not a.source or (r.get("source") or {}).get("provider") == a.source or (r.get("source") or {}).get("library") == a.source)]
    by = {}
    for r in rs:
        k = ((r.get("sound") or {}).get("kind") or "?", (r.get("source") or {}).get("provider") or "?", ledger.class_of(r))
        by[k] = by.get(k, 0) + 1
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh sound list", "library": str(lib), "counts": [{"kind": k[0], "source": k[1], "class": k[2], "n": n}
                          for k, n in sorted(by.items())], "records": rs}, ensure_ascii=False, indent=1))
    say(f"sound library {lib}: {len(rs)} sound(s)" + ("" if (lib / "ledger.jsonl").is_file() else " (no ledger.jsonl yet: bin/vh sound add, or a pick)"))
    for (kind, src, cls), n in sorted(by.items()):
        say(f"  {kind:<4} {src:<20} {cls:<10} {n}")
    return 0


def parser():
    ap = argparse.ArgumentParser(prog="bin/vh sfx|bgm|sound", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    top = ap.add_subparsers(dest="group")
    for kind in ("sfx", "bgm"):
        g = top.add_parser(kind, prog=f"bin/vh {kind}").add_subparsers(dest="cmd")
        p = g.add_parser("search", prog=f"bin/vh {kind} search")
        p.add_argument("query")
        p.add_argument("--top", type=int, default=8)
        p.add_argument("--where", choices=("all", "library", "openverse"), default="all")
        p.add_argument("--project")
        if kind == "sfx":
            p.add_argument("--dur")
            p.add_argument("--source")
            p.add_argument("--audition", action="store_true")
            p.add_argument("--out")
        else:
            p.add_argument("--len", type=float)
        p.add_argument("--lib")
        p.add_argument("--offline")
        p.add_argument("--json", action="store_true")
        p = g.add_parser("pick", prog=f"bin/vh {kind} pick")
        p.add_argument("project")
        p.add_argument("ref")
        p.add_argument("--as", dest="as_")
        p.add_argument("--used-by")
        if kind == "bgm":
            p.add_argument("--len", type=float)
            p.add_argument("--fade", type=float)
            p.add_argument("--beats")
            p.add_argument("--no-beats", action="store_true")
        p.add_argument("--lib")
        p.add_argument("--offline")
        p.add_argument("--json", action="store_true")
    g = top.add_parser("sound", prog="bin/vh sound").add_subparsers(dest="cmd")
    p = g.add_parser("add", prog="bin/vh sound add")
    p.add_argument("paths", nargs="+")
    p.add_argument("--source", required=True)
    p.add_argument("--kind", choices=("sfx", "bgm"), default="sfx")
    p.add_argument("--origin", choices=ledger.ORIGINS, default="download")
    for flag in ("--license", "--license-url", "--author", "--attribution", "--restrict", "--lib"):
        p.add_argument(flag)
    p.add_argument("--class", dest="license_class")
    p.add_argument("--json", action="store_true")
    p = g.add_parser("list", prog="bin/vh sound list")
    p.add_argument("--kind", choices=("sfx", "bgm"))
    p.add_argument("--source")
    p.add_argument("--lib")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv):
    global out
    a = parser().parse_args(argv)
    if not a.group or not getattr(a, "cmd", None):
        parser().print_usage(sys.stderr)
        return 2
    if getattr(a, "json", False):
        out = sys.stderr
        A.out = sys.stderr
    if not shutil.which("ffmpeg"):
        print(f"bin/vh {a.group} {a.cmd}: needs ffmpeg and ffprobe (bin/vh doctor)", file=sys.stderr)
        return 2
    try:
        if a.group == "sound":
            return cmd_add(a) if a.cmd == "add" else cmd_list(a)
        return cmd_search(a, a.group) if a.cmd == "search" else cmd_pick(a, a.group)
    except (Usage, A.Usage) as e:
        print(f"bin/vh {a.group} {a.cmd}: {e}", file=sys.stderr)
        return 2
    except (Failed, fetch.FetchError) as e:
        print(f"bin/vh {a.group} {a.cmd}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
