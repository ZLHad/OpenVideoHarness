"""bin/vh timeline <project> --resolved: one timeline to read. The shots or the edit list, the narration lines, the captions and the beats
in one document, each in seconds and in frames, with the sha256 of each source file. Stdlib only; it reads, and writes nothing.

usage: bin/vh timeline <project> --resolved [zh|en] [--words] [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

Where each part comes from:
  shots      edit.json as bin/vh edit build resolves it (its out/edit.resolved.json while that is of this edit.json, else the same
             code in memory); else shots.json; else, for a page with neither, the shots its current film's .render.json kept
             (window.film.shots when it was rendered: no browser is started here)
  narration  an edit list's merged timeline (out/edit.timeline.<lang>.json) when there is one, else audio/timeline.<lang>.json, else
             audio/timeline.json; the template's example is no take. zh or en picks the language
  captions   audio/captions.json. beats: the music an edit list names, else the newest audio/*.beats.json
  fps        edit.json, else the current film's .render.json, else the BRIEF's Output line, else 30 (fps_from says which)
  duration   edit.json, else the film's frames, else the last end among the parts (duration_from says which)
A part that is not there, or cannot be read, is an empty list and a row of missing. Frames are bin/vh's own (tools/timegrid.py): start_frame
is the first frame of a span (a chapter's too), end_frame the first after it; a beat's frame is the one on screen then.
--json: {"version": 1, "tool", "project", "fps", "fps_from", "duration", "duration_from", "frames", "size", "shots_from", "shots": [{"id", "start", "end",
"start_frame", "end_frame", the table's other fields}], "chapters": [{"t", "frame", "title"}], "narration": [{"id", "start", "end", "start_frame", "end_frame",
"text", "word_count", "words" with --words: [{"w", "start", "end"}], "speaker", "from"}], "captions": [{"id", "start", "end", "start_frame", "end_frame", "zh", "en",
"part"}], "beats": [{"t", "frame", "downbeat"}], "bpm", "sources": {"shots" | "narration" | "captions" | "beats": {"path", "sha256"}}, "missing": [{"part", "why"}]}.
Exit: 0, with parts missing too · 2 usage, or no project.
"""
import hashlib, json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "audio"))
import jsonerr   # noqa: E402
from timegrid import frame_at, frame_from   # noqa: E402


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def source(project, p):
    return {"path": Path(os.path.relpath(p, project)).as_posix(), "sha256": sha(p)}


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def spanned(row, fps):
    """A row with start and end, its frames added."""
    return dict(row, start_frame=frame_from(row["start"], fps), end_frame=frame_from(row["end"], fps))


class Doc:
    def __init__(self, project):
        self.project = Path(project)
        self.missing, self.sources = [], {}

    def lack(self, part, why):
        self.missing.append({"part": part, "why": str(why).replace(str(self.project) + os.sep, "")})

    # ---- the film the page's shots and the frame grid can come from
    def film_side(self):
        import proxy as P, versions as V
        versioned = P.versioned_film(self.project)
        film = versioned.resolve() if versioned else P.newest_film(self.project)
        side = V.load_json(str(film) + ".render.json") if film else None
        return film, side if isinstance(side, dict) else None

    # ---- shots
    def edit_doc(self):
        """edit.json as bin/vh edit build resolves it: its record while that is of this edit.json, else the same code in memory. None, said, when it does not resolve."""
        import edit
        f = self.project / edit.FILE
        old = edit.read_resolved(self.project)
        if old and (old.get("edit") or {}).get("sha256") == sha(f) and isinstance(old.get("entries"), list):
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
            doc = self.edit_doc()
            self.sources["shots"] = source(self.project, table)
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
            self.sources["shots"] = source(self.project, table)
            try:
                shots, _ = vhdraw.load_shots(table)
            except SystemExit as e:
                self.lack("shots", e)
                return [], table.name, None, None, None, None, [], None
            keep = ("id", "start", "end", "segment", "reads", "label", "frame", "at", "unsure", "camera")
            return [{k: s.get(k) for k in keep} for s in shots], table.name, None, None, None, None, [], None
        film, side = self.film_side()
        raw = (side or {}).get("shots")
        if isinstance(raw, list) and raw:
            off = (side.get("first_frame") or 0) / (side.get("fps") or 1)
            rows = [dict(id=str(s["id"]), start=float(s["start"]) - off, end=float(s["end"]) - off, **{k: s[k] for k in ("segment", "reads", "label", "at", "unsure") if k in s})
                    for s in raw if isinstance(s, dict) and num(s.get("start")) is not None and num(s.get("end")) is not None and "id" in s]
            side_path = str(film) + ".render.json"
            self.sources["shots"] = source(self.project, side_path)
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
        tl, why = TL.load(f)
        if tl is None:
            self.sources["narration"] = source(self.project, f)
            self.lack("narration", f"{f.name}: {why}")
            return []
        if tl.get("provider") == "example":
            self.lack("narration", f"{f.name} is the template's example, not a take (bin/vh tts makes one)")
            return []
        if lang and f.name == "timeline.json" and tl.get("lang") not in (None, lang):   # the copy of the latest take, whatever its language
            self.lack("narration", no)
            return []
        self.sources["narration"] = source(self.project, f)
        rows = []
        for s in tl["segments"]:
            if not isinstance(s, dict) or num(s.get("start")) is None or num(s.get("end")) is None:
                continue
            ws = s.get("words") if isinstance(s.get("words"), list) else []
            row = {"id": s.get("id"), "start": s["start"], "end": s["end"], "text": s.get("text") or s.get(lang or "") or s.get("zh") or s.get("en") or "", "word_count": len(ws)}
            row.update({k: s[k] for k in ("speaker", "from") if k in s})
            if words:
                row["words"] = [{"w": w.get("w"), "start": w.get("start"), "end": w.get("end")} for w in ws if isinstance(w, dict)]
            rows.append(spanned(row, fps))
        return rows

    # ---- captions
    def captions(self, fps):
        f = self.project / "audio" / "captions.json"
        if not f.is_file():
            self.lack("captions", "no audio/captions.json (bin/vh captions makes it)")
            return []
        self.sources["captions"] = source(self.project, f)
        try:
            caps = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            self.lack("captions", f"audio/captions.json: not JSON ({e})")
            return []
        if not isinstance(caps, list):
            self.lack("captions", "audio/captions.json: not a list of captions")
            return []
        rows = []
        for c in caps:
            if isinstance(c, dict) and num(c.get("start")) is not None and num(c.get("end")) is not None:
                rows.append(spanned({k: c[k] for k in ("id", "start", "end", "zh", "en", "part") if k in c}, fps))
        return rows

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
        self.sources["beats"] = source(self.project, f)
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            self.lack("beats", f"{f.name}: not JSON ({e})")
            return [], None
        if not isinstance(d, dict) or not isinstance(d.get("beats"), list):
            self.lack("beats", f"{f.name}: no list of beats")
            return [], None
        downs = {round(x, 3) for x in d.get("downbeats") or [] if num(x) is not None}
        return [{"t": t, "frame": frame_at(t, fps), "downbeat": round(t, 3) in downs} for t in d["beats"] if num(t) is not None], num(d.get("bpm"))


def document(project, lang=None, words=False):
    """The record --json prints."""
    D = Doc(project)
    rows, shots_from, fps, frames, duration, size, chapters, doc = D.shots()
    film, side = D.film_side()
    fps_from = "edit.json" if fps else None
    if not fps and side and num(side.get("fps")):
        fps, fps_from = side["fps"], Path(os.path.relpath(str(film) + ".render.json", project)).as_posix()
    if not fps:
        import edit
        fps = edit.brief_spec(project)[0]
        fps_from = "BRIEF.md" if fps else None
    if not fps:
        fps, fps_from = 30, "the default"
    if shots_from and shots_from != "edit.json":
        rows = [spanned(r, fps) for r in rows]
    narration = D.narration(lang, doc, fps, words)
    captions = D.captions(fps)
    beats, bpm = D.beats(doc, fps)
    duration_from = "edit.json" if duration is not None else None
    if duration is None and side and num(side.get("frames")) and num(side.get("fps")):
        frames, duration, duration_from = side["frames"], round(side["frames"] / side["fps"], 6), fps_from if fps_from != "BRIEF.md" else "the film"
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


def find_project(word):
    import gatecheck as G, review as R
    p = Path(word).expanduser()
    project = G.project_of(p) if p.exists() else None
    if project is None:
        project = R.find_project(word)
        if project is None:
            jsonerr.mark("no_project")
            return None
        if not (project / "BRIEF.md").is_file():
            jsonerr.fail("no_project", f"timeline: {project} is not a project (no BRIEF.md)")
            return None
    return project


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
    project = find_project(a.project)
    if project is None:
        return 2
    t0 = time.time()
    rec = document(project, a.lang, a.words)
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
