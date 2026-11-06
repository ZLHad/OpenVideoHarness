"""bin/vh timeline <project> --resolved: one timeline to read. The shots or the edit list, the narration lines, the captions and the beats
in one document, each in seconds and in frames, with the sha256 of each source file. Stdlib only; it reads, and writes nothing.

usage: bin/vh timeline <project> --resolved [zh|en] [--words] [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

Where each part comes from:
  shots      edit.json as bin/vh edit build resolves it (its out/edit.resolved.json while that is of this edit.json and of the very
             files it read: the narration it was timed on, the footage, each by its sha256, but a file over 64 MB not newer than the record;
             else the same code in memory); else shots.json; else, for a page
             with neither, the shots its current film's .render.json kept (window.film.shots when it was rendered: no browser is started
             here). Each row with the table's other fields, as written. A film rendered as a part (first_frame): its shots from its own first
             frame, what lies outside it left out and what crosses its ends cut there; with a table of the whole film, its frames and length are
             not the film's, and the table's are taken
  chapters   edit.json's, else the current film's .render.json (the same way for a part); a page with neither is a row of missing
  narration  an edit list's merged timeline (out/edit.timeline.<lang>.json) when there is one, else audio/timeline.<lang>.json, else
             audio/timeline.json; the template's example is no take. zh or en picks the language
  captions   audio/captions.json. beats: the music an edit list names, else the newest audio/*.beats.json
  fps        edit.json, else the current film's .render.json, else the BRIEF's Output line, else 30 (fps_from says which)
  duration   edit.json, else the film's frames, else the last end among the parts (duration_from says which)
A part that is not there, or cannot be read (no permission, not UTF-8, not JSON, a time that is NaN), is an empty list, or without the rows it spoils, and
a row of missing; a value that is NaN elsewhere is null. Frames are bin/vh's own (tools/timegrid.py): start_frame
is the first frame of a span (a chapter's too), end_frame the first after it; a beat's frame is the one on screen then.
--json: {"version": 1, "tool", "project", "fps", "fps_from", "duration", "duration_from", "frames", "size", "shots_from", "shots": [{"id", "start", "end",
"start_frame", "end_frame", the table's other fields}], "chapters": [{"t", "frame", "title"}], "narration": [{"id", "start", "end", "start_frame", "end_frame",
"text", "word_count", "words" with --words: [{"w", "start", "end"}], "speaker", "from"}], "captions": [{"id", "start", "end", "start_frame", "end_frame", "zh", "en",
"part"}], "beats": [{"t", "frame", "downbeat"}], "bpm", "sources": {"shots" | "narration" | "captions" | "beats": {"path", "sha256"}}, "missing": [{"part", "why"}]}.
Exit: 0, with parts missing too · 2 usage, or no project.
"""
import hashlib, json, math, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "audio"))
import activity, jsonerr   # noqa: E402,E401
from timegrid import frame_at, frame_from   # noqa: E402


BIG = 64 << 20    # bytes: a file a build's record takes by its time, not its hash


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def source(project, p):
    return {"path": Path(os.path.relpath(p, project)).as_posix(), "sha256": sha(p)}


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else None


def finite(x):
    """A value as JSON can hold it: a file's NaN or Infinity is null."""
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, list):
        return [finite(v) for v in x]
    if isinstance(x, dict):
        return {k: finite(v) for k, v in x.items()}
    return x


def spanned(row, fps):
    """A row with start and end, its frames added."""
    return dict(row, start_frame=frame_from(row["start"], fps), end_frame=frame_from(row["end"], fps))


class Doc:
    def __init__(self, project):
        self.project = Path(project)
        self.missing, self.sources = [], {}

    def lack(self, part, why):
        self.missing.append({"part": part, "why": str(why).replace(str(self.project) + os.sep, "")})

    def part(self, name, empty, fn, *args):
        """fn(*args), or what a part is when it cannot be read: empty, and a row of missing. A file's trouble is one row, never a traceback."""
        try:
            return fn(*args)
        except (Exception, SystemExit) as e:
            self.lack(name, f"{type(e).__name__}: {e}")
            return empty

    def source(self, name, p):
        """The part's source row, its file's sha256; OSError when it cannot be read."""
        self.sources[name] = source(self.project, p)

    def rows(self, name, raw, make):
        """make(row) of the rows that have finite times; how many do not is a row of missing."""
        out = []
        for s in raw:
            r = make(s)
            if r is not None:
                out.append(r)
        if len(out) < len(raw):
            self.lack(name, f"{len(raw) - len(out)} of {len(raw)} rows have no time that can be read: left out")
        return out

    # ---- the film the page's shots and the frame grid can come from
    def film_side(self):
        import proxy as P, versions as V
        try:
            film = P.current_film(self.project)[0]
            side = V.load_json(str(film) + ".render.json") if film else None
        except (Exception, SystemExit) as e:
            self.lack("film", f"{type(e).__name__}: {e}")
            return None, None
        return film, side if isinstance(side, dict) else None

    def side_part(self, side):
        """(the film's own first frame in seconds, its length in seconds or None) of a .render.json."""
        fps = num(side.get("fps")) or 1
        n = num(side.get("frames"))
        return (num(side.get("first_frame")) or 0) / fps, (n / fps if n else None)

    def side_chapters(self, film, side, fps):
        """The chapters a film's .render.json kept, from its own first frame; a page with no record says so."""
        raw = (side or {}).get("chapters")
        if isinstance(raw, list) and raw:
            off, dur = self.side_part(side)
            out = []
            for c in raw:
                t = num(c.get("t")) if isinstance(c, dict) else None
                if t is not None and t - off >= 0 and (dur is None or t - off < dur):
                    out.append({"t": round(t - off, 6), "frame": frame_from(t - off, fps), "title": c.get("title")})
            return out
        if not side and any((self.project / n).is_file() for n in ("film.html", "index.html", "studio.html")):
            self.lack("chapters", "a page's own chapters need a browser: a render keeps them in its .render.json")
        return []

    # ---- shots
    def holds(self, old, f):
        """Is a build's record of this edit.json, and of the very files it read? A cue-timed list moves when its narration is taken again, with edit.json as it was."""
        if not (isinstance(old, dict) and isinstance(old.get("edit"), dict) and old["edit"].get("sha256") == sha(f) and isinstance(old.get("entries"), list)):
            return False
        read = [r for r in old.get("refs") or [] if isinstance(r, dict)]
        for v in (old.get("files") or {}).values() if isinstance(old.get("files"), dict) else ():
            read += [x for x in (v, v.get("audio")) if isinstance(x, dict)] if isinstance(v, dict) else []
        try:
            import edit
            built = (self.project / edit.RESOLVED).stat().st_mtime

            def same(r):
                f = self.project / r["path"]
                s = f.stat()
                return (s.st_size > BIG and s.st_mtime < built) or sha(f) == r["sha256"]   # footage older than the record is not read through again
            return all(same(r) for r in {(x["path"], x["sha256"]): x for x in read if x.get("path") and x.get("sha256")}.values())
        except OSError:
            return False

    def edit_doc(self):
        """edit.json as bin/vh edit build resolves it: its record while that is of this edit.json and the files it read, else the same code in memory. None, said, when it does not resolve."""
        import edit
        f = self.project / edit.FILE
        old = edit.read_resolved(self.project)
        if self.holds(old, f):
            return old
        try:
            return edit.resolve(self.project)
        except edit.EditError as e:
            self.lack("shots", "edit.json does not resolve: " + "; ".join(e.problems[:5]))
            return None

    def shots(self):
        """(rows, where from, fps or None, frames or None, duration or None, size, chapters, the edit doc)."""
        import shot_source
        try:
            table = shot_source.table(self.project)
        except SystemExit as e:
            self.lack("shots", e)
            return [], None, None, None, None, None, [], None
        if table and shot_source.is_edit(table):
            self.source("shots", table)
            doc = self.edit_doc()
            if doc is None:
                return [], "edit.json", None, None, None, None, [], None
            import edit
            rows = []
            by_id = {e["id"]: e for e in doc["entries"]}
            for r in edit.shot_rows(doc):
                a, b = by_id[r["id"]]["frames"]
                rows.append(dict(r, start_frame=a, end_frame=b))
            fps = doc["fps"]
            chapters = [{"t": c["t"], "frame": frame_from(c["t"], fps), "title": c.get("title")} for c in doc.get("chapters") or [] if num(c.get("t")) is not None]
            return rows, "edit.json", fps, doc["frames"], doc["duration"], doc.get("size"), chapters, doc
        if table:
            import vhdraw
            self.source("shots", table)
            try:
                shots, _ = vhdraw.load_shots(table)
                written = shot_source.rows(self.project)[0]
            except (SystemExit, ValueError) as e:
                self.lack("shots", e)
                return [], table.name, None, None, None, None, [], None
            keep = ("id", "start", "end", "segment", "reads", "label", "frame", "at", "unsure", "camera")
            rows = [dict({k: v for k, v in w.items() if k not in ("t0", "t1")}, **{k: s.get(k) for k in keep}) for s, w in zip(shots, written)]   # the table's other fields, as written
            return self.rows("shots", rows, lambda r: r if num(r["start"]) is not None and num(r["end"]) is not None else None), table.name, None, None, None, None, [], None
        film, side = self.film_side()
        raw = (side or {}).get("shots")
        if isinstance(raw, list) and raw:
            off, dur = self.side_part(side)

            def row(s):
                """A shot from the film's own first frame, cut to what the film holds; None for one outside it (a part of the film)."""
                if not isinstance(s, dict) or "id" not in s or num(s.get("start")) is None or num(s.get("end")) is None:
                    return None
                a, b = float(s["start"]) - off, float(s["end"]) - off
                if b <= 0 or (dur is not None and a >= dur):
                    return False
                r = dict({k: v for k, v in s.items() if k not in ("id", "start", "end")}, id=str(s["id"]), start=max(a, 0.0), end=min(b, dur) if dur is not None else b)
                if num(s.get("at")) is not None:
                    r["at"] = s["at"] - off
                return r
            rows = self.rows("shots", [r for r in map(row, raw) if r is not False], lambda r: r)
            side_path = str(film) + ".render.json"
            self.source("shots", side_path)
            return rows, Path(os.path.relpath(side_path, self.project)).as_posix(), None, None, None, None, [], None
        pages = [n for n in ("film.html", "index.html", "studio.html") if (self.project / n).is_file()]
        self.lack("shots", (f"no shot table, and {pages[0]}'s own shots need a browser: a render keeps them in its .render.json; bin/vh storyboard reads them live" if pages
                            else "no edit.json or shots.json, and no page or film that gives shots"))
        return [], None, None, None, None, None, [], None

    # ---- narration
    def narration(self, lang, doc, fps, words):
        import timeline_lint as TL
        f = None
        if doc is not None:
            import edit
            merged = self.project / "out" / f"edit.timeline.{lang}.json" if lang else edit.merged_path(doc, self.project)
            f = merged if merged.is_file() else None
        f = f or TL.find(self.project, lang)
        no = f"no audio/timeline.{lang or '<lang>'}.json (bin/vh tts makes it)"
        if f is None or (lang and f.name in ("timeline.zh.json", "timeline.en.json") and f.name != f"timeline.{lang}.json"):   # (find falls back on another language's)
            self.lack("narration", no)
            return []
        self.source("narration", f)
        tl, why = TL.load(f)
        if tl is None:
            self.lack("narration", f"{f.name}: {why}")
            return []
        if tl.get("provider") == "example":
            self.sources.pop("narration")
            self.lack("narration", f"{f.name} is the template's example, not a take (bin/vh tts makes one)")
            return []
        if lang and f.name == "timeline.json" and tl.get("lang") not in (None, lang):   # the copy of the latest take, whatever its language
            self.sources.pop("narration")
            self.lack("narration", no)
            return []

        def row(s):
            if not isinstance(s, dict) or num(s.get("start")) is None or num(s.get("end")) is None:
                return None
            ws = s.get("words") if isinstance(s.get("words"), list) else []
            r = {"id": s.get("id"), "start": s["start"], "end": s["end"], "text": s.get("text") or s.get(lang or "") or s.get("zh") or s.get("en") or "", "word_count": len(ws)}
            r.update({k: s[k] for k in ("speaker", "from") if k in s})
            if words:
                r["words"] = [{"w": w.get("w"), "start": w.get("start"), "end": w.get("end")} for w in ws if isinstance(w, dict)]
            return spanned(r, fps)
        return self.rows("narration", tl["segments"], row)

    # ---- captions
    def captions(self, fps):
        f = self.project / "audio" / "captions.json"
        if not f.is_file():
            self.lack("captions", "no audio/captions.json (bin/vh captions makes it)")
            return []
        self.source("captions", f)
        try:
            caps = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            self.lack("captions", f"audio/captions.json: not JSON ({e})")
            return []
        if not isinstance(caps, list):
            self.lack("captions", "audio/captions.json: not a list of captions")
            return []
        return self.rows("captions", caps, lambda c: spanned({k: c[k] for k in ("id", "start", "end", "zh", "en", "part") if k in c}, fps)
                         if isinstance(c, dict) and num(c.get("start")) is not None and num(c.get("end")) is not None else None)

    # ---- beats
    def beats(self, doc, fps):
        f = None
        for r in (doc or {}).get("refs") or []:
            if r.get("kind") == "music":
                f = self.project / r["path"]
        if f is None:
            found = sorted((self.project / "audio").glob("*.beats.json"), key=lambda x: -x.stat().st_mtime) if (self.project / "audio").is_dir() else []
            f = found[0] if found else None
        if f is None or not f.is_file():
            self.lack("beats", "no audio/*.beats.json (bin/vh beats makes one, for a film with music)")
            return [], None
        self.source("beats", f)
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            self.lack("beats", f"{f.name}: not JSON ({e})")
            return [], None
        if not isinstance(d, dict) or not isinstance(d.get("beats"), list):
            self.lack("beats", f"{f.name}: no list of beats")
            return [], None
        downs = {round(x, 3) for x in d.get("downbeats") or [] if num(x) is not None}
        return self.rows("beats", d["beats"], lambda t: {"t": t, "frame": frame_at(t, fps), "downbeat": round(t, 3) in downs} if num(t) is not None else None), num(d.get("bpm"))


def document(project, lang=None, words=False):
    """The record --json prints."""
    D = Doc(project)
    rows, shots_from, fps, frames, duration, size, chapters, doc = D.part("shots", ([], None, None, None, None, None, [], None), D.shots)
    film, side = D.film_side()
    fps_from = "edit.json" if fps else None
    if not fps and side and num(side.get("fps")) and side["fps"] > 0:
        fps, fps_from = side["fps"], Path(os.path.relpath(str(film) + ".render.json", project)).as_posix()
    if not fps:
        import edit
        fps = D.part("fps", (None, None), edit.brief_spec, project)[0]
        fps_from = "BRIEF.md" if fps else None
    if not fps:
        fps, fps_from = 30, "the default"
    if shots_from and shots_from != "edit.json":
        rows = [spanned(r, fps) for r in rows]
    if doc is None:
        chapters = D.part("chapters", [], D.side_chapters, film, side, fps)
    narration = D.part("narration", [], D.narration, lang, doc, fps, words)
    captions = D.part("captions", [], D.captions, fps)
    beats, bpm = D.part("beats", ([], None), D.beats, doc, fps)
    duration_from = "edit.json" if duration is not None else None
    whole_film = not (side and num(side.get("first_frame")) and shots_from and shots_from != "edit.json" and not shots_from.endswith(".render.json"))   # a part of a film, and a table of the whole: the table's times
    if duration is None and whole_film and side and num(side.get("frames")) and num(side.get("fps")) and side["fps"] > 0:
        frames, duration, duration_from = int(side["frames"]), round(side["frames"] / side["fps"], 6), fps_from if fps_from != "BRIEF.md" else "the film"
    if duration is None:
        ends = [r["end"] for part in (rows, narration, captions) for r in part]
        duration = round(max(ends), 6) if ends else 0
        duration_from = "the last end" if ends else None
    if frames is None:
        frames = frame_from(duration, fps)
    return {"version": 1, "tool": "bin/vh timeline --resolved", "project": str(project), "fps": fps, "fps_from": fps_from, "duration": duration, "duration_from": duration_from,
            "frames": frames, "size": size, "shots_from": shots_from, "shots": rows, "chapters": chapters, "narration": narration, "captions": captions, "beats": beats, "bpm": bpm,
            "sources": D.sources, "missing": D.missing}


def show(rec):
    print(f"{Path(rec['project']).name}: {rec['duration']} s, {rec['frames']} frames at {rec['fps']} fps ({rec['fps_from']})")
    for k in ("shots", "narration", "captions", "beats"):
        s = rec["sources"].get(k)
        print(f"  {k:<10} {len(rec[k]):>5}" + (f"  {s['path']}  {s['sha256'][:12]}" if s else ""))
    for m in rec["missing"]:
        print(f"  ! {m['part']}: {m['why']}")


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="bin/vh timeline", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("project", help="project folder (or a file inside it), or its name under projects/")
    ap.add_argument("lang", nargs="?", help="the narration's language: zh or en")
    ap.add_argument("--resolved", action="store_true", help="this document (without it: bin/vh timeline's checks)")
    ap.add_argument("--words", action="store_true", help="each narration line's words, with their times")
    ap.add_argument("--json", action="store_true", help="the record, as JSON (version 1)")
    a = ap.parse_intermixed_args(argv)   # (the language after an option: Python before 3.12 takes it only so)
    if a.lang and not re.fullmatch(r"[a-z]{2,3}(-[A-Za-z0-9]{2,4})?", a.lang):
        return jsonerr.fail("usage", f"timeline: {a.lang} is no language (zh, en)")
    project = jsonerr.project_arg(a.project, "timeline")
    if project is None:
        return 2
    t0 = time.time()
    rec = activity._text(finite(document(project, a.lang, a.words)))
    if a.json:
        print(json.dumps(rec, ensure_ascii=False, indent=1))
    else:
        show(rec)
    if time.time() - t0 > 5:   # (an edit list with footage it had to probe, with no build yet)
        print(f"timeline: {time.time() - t0:.1f} s: bin/vh edit build keeps what it resolves", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:
        sys.exit(0)
