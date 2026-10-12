"""Clear a finished project's intermediate files: keep the film, its covers, captions, publishing copy, sources, docs and the
narration in use; put the rest in the Trash (or delete what the tools can make again, with --delete).

usage (via bin/vh clean): python tools/clean.py <project> [--yes] [--delete] [--keep path …] [--final path …] [--dry-run]

Without --yes it only lists (a dry run; --dry-run says so, and wins over --yes). What goes, by kind:
  rebuilt   out/frames, render chunks (.<film>.parts) and patch work folders (.<film>.patch), node_modules (npm ci brings it
            back), snapshots/, __pycache__, .venv and venv folders
  renders   video files under out/ that are not the film: drafts, video-only renders, segments, patches (*.mp4 *.mov *.webm
            *.mkv *.m4v *.avi), with their .render.json and .lock beside them. Only once a film is found (below)
  sound     sound files directly in audio/ that are not the narration in use (voiceover.wav, voiceover.<lang>.wav and its
            .raw.wav original, any of wav, mp3, m4a, flac, aac; <lang> like zh, en or zh-CN), not a mix (mix*, *_mix*) and not
            named in any of the project's text files (a page's <audio src>, a timeline, the notes); audio/takes/; and stem
            folders directly in audio/ (*stems*). Sound in other folders under audio/ (samples, a song's source) stays.
            Only once a film is found
The film: video files in out/final/ (not in a covers or 封面 folder inside it), else out/final*.<video> directly in out/,
media/*.<video>, or what --final names (an existing video file, relative to the project or to here). Covers and
out/publish/ stay, but do not count as the film. A project with no film found keeps its videos and its sound: name the
film with --final. --keep protects a path, also inside a folder that would otherwise go (the folder is then cleared item
by item around it).
What stays besides: out/review/, out/check/, every other file in out/ that is not a video, timelines, scripts, src/,
assets/, lookdev/, tools/, the markdown, and any folder below the project that is a project of its own (has a BRIEF.md).
Everything goes to the Trash (macOS: /usr/bin/trash where there is one, which also handles other disks and Put Back, else
~/.Trash; Linux: the freedesktop Trash, refused for an item on another disk); --delete deletes the "rebuilt" kind outright
(the tools make it again). A video is never deleted outright: a mistaken render can come back from the Trash. Refused:
a folder without BRIEF.md, the harness itself (bin/vh, projects/), and a project where a render or a patch holds a live
lock. Nothing outside the project is touched; a symbolic link is removed as a link, never followed. On macOS, Time
Machine's local snapshots can hold deleted data for a while: `df` may not grow at once.
Exit: 0 listed or cleared · 1 something could not be moved or deleted · 2 not a project, or refused.
"""
import argparse, os, re, shutil, subprocess, sys, time
from pathlib import Path

VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
SOUND = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".aiff", ".aif", ".ogg", ".opus", ".m4s"}
REBUILT_DIRS = {"node_modules", "snapshots", "__pycache__", ".venv", "venv"}
TEXT = {".json", ".md", ".txt", ".html", ".htm", ".js", ".mjs", ".css", ".py", ".sh", ".srt", ".csv", ".yaml", ".yml", ".toml"}
VOICE = re.compile(r"voiceover(\.[a-z]{2,3}(-[a-z0-9]{2,4})?)?(\.raw)?\.(wav|mp3|m4a|flac|aac)")   # the narration in use
COVERS = {"covers", "cover", "封面"}


def size(p):
    if p.is_symlink() or p.is_file():
        try: return p.lstat().st_size
        except OSError: return 0
    total = 0
    for root, dirs, files in os.walk(p):
        for f in files:
            try: total += (Path(root) / f).lstat().st_size
            except OSError: pass
    return total


def human(n):
    return f"{n / 1e9:.2f} GB" if n >= 1e9 else f"{n / 1e6:.1f} MB" if n >= 1e5 else f"{n / 1e3:.0f} KB"


def low(rel):   # folder names compared as a case-blind disk does
    return tuple(x.casefold() for x in rel.parts)


def dir_kind(rel):
    p = low(rel)
    if p[-1] in REBUILT_DIRS and p[0] not in ("src", "assets"):
        return "rebuilt"
    if p[0] == "out" and (p == ("out", "frames") or p[-1].endswith(".parts") or p[-1].endswith(".patch")):
        return "rebuilt"
    if p[0] == "audio" and len(p) == 2 and "stems" in p[1]:
        return "sound"
    return None


def walk(root):
    """(folder, relative path, sub-folders, files) for the project, never into a link, .git or a project of its own."""
    for dirpath, dirs, files in os.walk(root):
        d = Path(dirpath); reld = d.relative_to(root)
        for name in list(dirs):
            if name == ".git" or (d / name).is_symlink() or (d / name / "BRIEF.md").exists():
                dirs.remove(name)
        yield d, reld, dirs, files


def mentioned(root):
    """Every sound file name a text file of the project names (an <audio src>, a timeline, a mix command in the notes)."""
    names = set()
    pat = re.compile(r"[\w.\-]+\.(?:wav|mp3|m4a|aac|flac|aiff?|ogg|opus|m4s)\b", re.I)
    for d, reld, dirs, files in walk(root):
        if reld.parts and low(reld)[0] in ("node_modules", "out"):
            dirs[:] = []; continue
        for f in files:
            p = d / f
            try:
                if p.suffix.lower() in TEXT and p.stat().st_size < 4_000_000:
                    names |= {m.lower() for m in pat.findall(p.read_text(encoding="utf-8", errors="ignore"))}
            except OSError:
                pass
    return names


def find_film(root, finals):
    """The film's files: --final, else out/final/ (not its covers), else out/final*.<video>, and media/."""
    found = [f for f in finals if f.suffix.lower() in VIDEO and (root / f).is_file()]
    out = root / "out"
    fdir = next((q for q in out.iterdir() if q.is_dir() and q.name.casefold() == "final"), None) if out.is_dir() else None
    if fdir:
        for d, reld, dirs, files in walk(fdir):
            dirs[:] = [x for x in dirs if x.casefold() not in COVERS]
            found += [(d / f).relative_to(root) for f in files if Path(f).suffix.lower() in VIDEO and not f.casefold().startswith("cover")]
    if out.is_dir() and not any(low(x)[:2] == ("out", "final") and len(x.parts) > 2 for x in found):
        found += [p.relative_to(root) for p in out.iterdir() if p.is_file() and p.suffix.lower() in VIDEO and p.name.casefold().startswith("final")]
    if (root / "media").is_dir():
        found += [p.relative_to(root) for p in (root / "media").iterdir() if p.is_file() and p.suffix.lower() in VIDEO]
    return found


def candidates(root, film, keeps):
    """[(kind, path)] of what can go; a folder stands for everything in it, unless something to keep is inside it."""
    out = []
    film_set = {low(f) for f in film}
    def kept(rel): return any(rel == k or k in rel.parents for k in keeps) or low(rel) in film_set
    def holds(rel): return any(rel in k.parents for k in keeps) or any(f[:len(rel.parts)] == low(rel) for f in film_set)
    said = mentioned(root) if film else set()
    inside = {}   # a folder that would go but holds something to keep: its files go one by one, as this kind
    for d, reld, dirs, files in walk(root):
        kind_here = next((inside[q] for q in [reld, *reld.parents] if q in inside), None)
        for name in sorted(dirs):
            rel = reld / name
            if kept(rel):
                dirs.remove(name); continue
            kind = kind_here or dir_kind(rel)
            if kind == "sound" and not film:
                continue
            if kind and not holds(rel):
                out.append((kind, d / name)); dirs.remove(name)
            elif kind:
                inside[rel] = kind
        for name in sorted(files):
            rel, ext, n = reld / name, Path(name).suffix.lower(), name.lower()
            if not rel.parts or kept(rel):
                continue
            top = low(rel)[0]
            if kind_here:
                if kind_here != "sound" or film: out.append((kind_here, d / name))
            elif not film:
                continue
            elif top == "out" and ext in VIDEO:
                if not set(low(rel)[1:-1]) & ({"review", "check", "publish"} | COVERS) and not n.startswith("cover"):
                    out.append(("renders", d / name))
            elif top == "audio" and ext in SOUND and n not in said:
                direct = len(rel.parts) == 2
                if (direct and not (VOICE.fullmatch(n) or n.startswith("mix") or "_mix" in n or "-mix" in n)) or low(rel)[1] == "takes":
                    out.append(("sound", d / name))
    gone = {p for k, p in out if k == "renders"}   # a render's sidecar and lock go with it
    for p in list(gone):
        for suf in (".render.json", ".lock"):
            q = p.with_name(p.name + suf)
            if q.exists() and not kept(q.relative_to(root)): out.append(("renders", q))
    return out


def live_locks(root):
    """Locks a running render or patch holds (bin/vh render: <film>.lock; bin/vh patch: <out>.patch.lock)."""
    held = []
    for d, reld, dirs, files in walk(root):
        if reld.parts and low(reld)[0] == "node_modules":
            dirs[:] = []; continue
        for f in files:
            if not f.endswith(".lock"):
                continue
            try: pid = int((d / f).read_text().strip() or 0)
            except (OSError, ValueError): continue
            if pid <= 0:
                continue
            try:
                os.kill(pid, 0); held.append(((d / f).relative_to(root), pid))
            except PermissionError:
                held.append(((d / f).relative_to(root), pid))
            except OSError:
                pass
    return held


def to_trash(p):
    """Into the Trash. OVH_TRASH_DIR (tests) is a folder to move into; macOS uses /usr/bin/trash where it exists."""
    test = os.environ.get("OVH_TRASH_DIR")
    if not test and sys.platform == "darwin" and Path("/usr/bin/trash").exists():
        r = subprocess.run(["/usr/bin/trash", str(p)], capture_output=True, text=True)
        if r.returncode or os.path.lexists(p):
            raise OSError((r.stderr or r.stdout or f"exit {r.returncode}").strip())
        return
    if test:
        files = Path(test); files.mkdir(parents=True, exist_ok=True); info = None
    elif sys.platform == "darwin":
        files = Path.home() / ".Trash"; info = None
    else:
        tdir = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "Trash"
        files, info = tdir / "files", tdir / "info"
        files.mkdir(parents=True, exist_ok=True); info.mkdir(parents=True, exist_ok=True)
    name, k = p.name, 1
    while os.path.lexists(files / name) or (info and (info / f"{name}.trashinfo").exists()):
        k += 1; name = f"{p.stem} {k}{p.suffix}" if p.is_file() else f"{p.name} {k}"
    if os.stat(p.parent).st_dev != os.stat(files).st_dev:
        raise OSError(f"the Trash is on another disk; move {p.name} yourself")
    if info:
        from urllib.parse import quote
        (info / f"{name}.trashinfo").write_text(f"[Trash Info]\nPath={quote(str(p))}\nDeletionDate={time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    os.rename(p, files / name)


def remove(p, root):
    if root not in p.parents:   # never outside the project
        raise OSError(f"{p} is not inside {root}")
    if p.is_symlink() or p.is_file():
        p.unlink()
    else:
        shutil.rmtree(p)


def main():
    ap = argparse.ArgumentParser(prog="bin/vh clean", usage="bin/vh clean <project> [--yes] [--delete] [--keep path …] [--final path …] [--dry-run]")
    ap.add_argument("project")
    ap.add_argument("--yes", action="store_true", help="clear them; without it, only list (a dry run)")
    ap.add_argument("--dry-run", action="store_true", help="only list, even with --yes")
    ap.add_argument("--delete", action="store_true", help="delete what the tools make again (frames, chunks, node_modules) instead of the Trash")
    ap.add_argument("--keep", action="append", default=[], help="a path in the project to keep (repeatable)")
    ap.add_argument("--final", action="append", default=[], help="the film's file, when it is not in out/final/, out/final*.*, or media/")
    a = ap.parse_args()
    root = Path(a.project).resolve()
    if not (root / "BRIEF.md").is_file():
        print(f"clean: {a.project} is not a project folder (no BRIEF.md)", file=sys.stderr); sys.exit(2)
    if (root / "bin" / "vh").exists() or (root / "projects").is_dir():
        print(f"clean: {a.project} is the harness (or holds projects), not one project", file=sys.stderr); sys.exit(2)

    def inproj(x):   # relative to the project first, else to here
        q = Path(x)
        q = q if q.is_absolute() else (root / q if os.path.lexists(root / q) else Path.cwd() / q)
        r = Path(os.path.relpath(q.resolve(), root))
        if str(r).startswith(".."):
            print(f"clean: {x} is not inside the project", file=sys.stderr); sys.exit(2)
        return r
    keeps = [inproj(k) for k in a.keep]
    finals = [inproj(f) for f in a.final]
    for f in finals:
        if f.suffix.lower() not in VIDEO or not (root / f).is_file():
            print(f"clean: --final {f}: not a video file in the project", file=sys.stderr); sys.exit(2)
    locks = live_locks(root)
    if locks:
        print("clean: something is writing in the project: " + ", ".join(f"{p} (pid {pid})" for p, pid in locks) + "; wait for it", file=sys.stderr)
        sys.exit(2)
    film = find_film(root, finals)
    items = candidates(root, film, keeps + film)
    sizes = {p: size(p) for _, p in items}
    total = sum(sizes.values())
    doing = a.yes and not a.dry_run
    say = {"rebuilt": "made again by the tools", "renders": "renders that are not the film", "sound": "sound not in use"}
    print(f"clean: {root.name} · {human(size(root))} now · {len(items)} item(s), {human(total)} " + ("to clear" if doing else "would go (a dry run: --yes clears them)"))
    if film:
        print("  the film: " + ", ".join(str(f) for f in film[:6]) + (" …" if len(film) > 6 else ""))
    else:
        print("  no film found (out/final/, out/final*.<video>, media/): its videos and sound stay; name the film with --final <file> to clear them")
    for kind in ("rebuilt", "renders", "sound"):
        xs = [p for k, p in items if k == kind]
        if not xs:
            continue
        where = "deleted" if a.delete and kind == "rebuilt" else "to the Trash"
        print(f"  {kind} ({say[kind]}; {where}): {human(sum(sizes[p] for p in xs))}")
        for p in sorted(xs, key=lambda q: -sizes[q])[:25]:
            print(f"    {human(sizes[p]):>9}  {p.relative_to(root)}{'/' if p.is_dir() and not p.is_symlink() else ''}")
        if len(xs) > 25:
            print(f"    … {len(xs) - 25} more")
    if not doing:
        sys.exit(0)
    failed, trashed, deleted = 0, 0, 0
    for kind, p in items:
        try:
            if a.delete and kind == "rebuilt":
                remove(p, root); deleted += sizes[p]
            else:
                to_trash(p); trashed += sizes[p]
        except OSError as e:
            failed += 1; print(f"  ✗ {p.relative_to(root)}: {e}")
    print(f"clean: {human(deleted)} deleted, {human(trashed)} moved to the Trash" + (f", {failed} could not be cleared" if failed else "") +
          f"; {root.name} is {human(size(root))} now")
    if trashed:
        print("  the space comes back when the Trash is emptied (that is yours to do)")
    if sys.platform == "darwin" and (deleted or trashed):
        r = subprocess.run(["tmutil", "listlocalsnapshots", "/"], capture_output=True, text=True)
        n = len([ln for ln in r.stdout.splitlines() if "com.apple" in ln]) if r.returncode == 0 else 0
        if n:
            print(f"  Time Machine holds {n} local snapshot(s): data deleted since the last one stays on the disk until macOS drops them (hours; sooner when space runs short)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
