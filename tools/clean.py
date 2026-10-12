"""Clear a finished project's intermediate files: keep the film, its covers, captions, publishing copy, sources, docs and the
narration in use; put the rest in the Trash (or delete what can be made again, with --delete).

usage (via bin/vh clean): python tools/clean.py <project> [--yes] [--delete] [--keep path …] [--final path …]

Without --yes it only lists (a dry run). What goes, by kind:
  rebuilt   out/frames, render chunks (.<film>.parts) and patch work folders (.<film>.patch), node_modules (npm ci brings it
            back), snapshots/, __pycache__, .venv and venv folders
  renders   video files under out/ (and out/**) that are not the film: drafts, video-only renders, segments, patches
            (*.mp4 *.mov *.webm *.mkv *.m4v *.avi), with their .render.json, .lock and .log beside them
  sound     sound files directly in audio/ that are not the narration in use, its untouched original or the mix (old takes,
            music and effect renders: bin/vh music, sfx and mix make them again), audio/takes/, and stems (audio/*stems*/);
            sound in other folders under audio/ (samples, a song's source) stays
What stays: everything else. In particular the film (out/final/ when there is one, else out/final*.*; media/; out/publish/), covers (out/cover*,
out/covers/, out/**/封面), out/review/ (the record of the gates), out/check/ (contact sheets), every small file in out/
(cue lists, captions, logs), audio/voiceover.wav, voiceover.<lang>.wav, voiceover.<lang>.raw.wav (bin/vh pace --restore
needs it), mix*.wav, every timeline, script and json, and all of src/, assets/, lookdev/, tools/ and the markdown.
A project with no film found (none of the places above) keeps its videos: say which is the film with --final, and
--keep protects any other path.
By default every item goes to the Trash (macOS ~/.Trash, Linux ~/.local/share/Trash): nothing is lost, and the disk space
comes back when the Trash is emptied. --delete deletes the "rebuilt" and "renders" kinds outright instead (they can be made
again); sound still goes to the Trash. Nothing outside the project is touched; a symbolic link is removed as a link, never
followed. On macOS, Time Machine's local snapshots can hold deleted data for a while: `df` may not grow at once.
Exit: 0 listed or cleared · 1 something could not be moved or deleted · 2 not a project.
"""
import argparse, os, re, shutil, subprocess, sys, time
from pathlib import Path

VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
SOUND = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".aiff", ".aif", ".ogg", ".opus", ".m4s"}
REBUILT_DIRS = {"node_modules", "snapshots", "__pycache__", ".venv", "venv"}


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


def is_final(rel, final_dir):
    """The film and what is published with it. With an out/final/ folder, that folder is the film, and out/final-4k-a.mp4
    and the like beside it are the renders it was made from; without one, out/final*.* are the film."""
    parts, name = rel.parts, rel.name.lower()
    return (parts[:2] in (("out", "final"), ("out", "publish"), ("out", "covers")) or parts[0] == "media" or "封面" in parts or "covers" in parts
            or (parts[0] == "out" and len(parts) == 2 and (name.startswith("cover") or (name.startswith("final") and not final_dir))))


VOICE = re.compile(r"voiceover(\.[a-z]{2,3})?(\.raw)?\.wav")   # the narration in use and its untouched original (bin/vh pace)


def dir_kind(rel, name):
    if name in REBUILT_DIRS and rel.parts[0] not in ("src", "assets"):
        return "rebuilt"
    if rel.parts[0] == "out" and (rel == Path("out/frames") or name.endswith(".parts") or name.endswith(".patch")):
        return "rebuilt"
    if rel.parts[0] == "audio" and "stems" in name.lower():
        return "sound"
    return None


def candidates(root, finals, keeps):
    """([(kind, path)] of what can go, a folder standing for everything in it; whether a film was found)."""
    out, film = [], False
    final_dir = any(f.suffix.lower() in VIDEO for f in (root / "out" / "final").rglob("*")) if (root / "out" / "final").is_dir() else False
    kept = lambda rel: any(rel == k or k in rel.parents for k in keeps)
    for dirpath, dirs, files in os.walk(root):
        d = Path(dirpath); reld = d.relative_to(root)
        for name in sorted(dirs):
            rel = reld / name
            if name == ".git" or kept(rel) or (d / name).is_symlink():
                dirs.remove(name); continue
            kind = dir_kind(rel, name)
            if kind:
                out.append((kind, d / name)); dirs.remove(name)
        for name in sorted(files):
            rel, ext = reld / name, Path(name).suffix.lower()
            if kept(rel) or not rel.parts:
                continue
            top = rel.parts[0]
            if ext in VIDEO and (top == "media" or (top == "out" and (is_final(rel, final_dir) or rel in finals))):
                film = True
            elif top == "out" and ext in VIDEO and not set(rel.parts[1:-1]) & {"review", "check"}:
                out.append(("renders", d / name))
            elif top == "audio" and ext in SOUND and ((len(rel.parts) == 2 and not (VOICE.fullmatch(name.lower()) or name.lower().startswith("mix")))
                                                      or rel.parts[1] == "takes"):
                out.append(("sound", d / name))   # audio/ itself and audio/takes/; other folders (samples, sources) stay
    # the files beside a render that goes: its sidecar and lock
    gone = {p for k, p in out if k == "renders"}
    for p in list(gone):
        for suf in (".render.json", ".lock"):
            q = p.with_name(p.name + suf)
            if q.exists() and not kept(q.relative_to(root)): out.append(("renders", q))
    return out, film or any((root / f).exists() for f in finals)


def trash_dir():
    if sys.platform == "darwin":
        (Path.home() / ".Trash").mkdir(exist_ok=True)
        return Path.home() / ".Trash"
    d = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "Trash"
    (d / "files").mkdir(parents=True, exist_ok=True); (d / "info").mkdir(parents=True, exist_ok=True)
    return d


def to_trash(p, tdir):
    """Moved (renamed) into the Trash under a name not taken; on another disk the move would be a copy: refused."""
    files = tdir if sys.platform == "darwin" else tdir / "files"
    name, k = p.name, 1
    while (files / name).exists() or os.path.lexists(files / name):
        k += 1; name = f"{p.stem} {k}{p.suffix}" if p.is_file() else f"{p.name} {k}"
    if os.stat(p.parent).st_dev != os.stat(files).st_dev:
        raise OSError(f"the Trash is on another disk; use --delete for rebuilt files, or move {p.name} yourself")
    if sys.platform != "darwin":
        from urllib.parse import quote
        (tdir / "info" / f"{name}.trashinfo").write_text(f"[Trash Info]\nPath={quote(str(p))}\nDeletionDate={time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    os.rename(p, files / name)


def remove(p, root):
    if root not in p.parents:   # never outside the project
        raise OSError(f"{p} is not inside {root}")
    if p.is_symlink() or p.is_file():
        p.unlink()
    else:
        shutil.rmtree(p)


def main():
    ap = argparse.ArgumentParser(prog="bin/vh clean", usage="bin/vh clean <project> [--yes] [--delete] [--keep path …] [--final path …]")
    ap.add_argument("project")
    ap.add_argument("--yes", action="store_true", help="clear them; without it, only list (a dry run)")
    ap.add_argument("--dry-run", action="store_true", help="only list (the default)")
    ap.add_argument("--delete", action="store_true", help="delete the rebuilt and render kinds outright instead of the Trash")
    ap.add_argument("--keep", action="append", default=[], help="a path in the project to keep (repeatable)")
    ap.add_argument("--final", action="append", default=[], help="the film, when it is not in out/final, out/final*.*, media/ or out/publish/")
    a = ap.parse_args()
    root = Path(a.project).resolve()
    if not root.is_dir() or not any((root / f).exists() for f in ("BRIEF.md", "film.html", "index.html", "studio.html")):
        print(f"clean: {a.project} is not a project folder (no BRIEF.md or page)", file=sys.stderr); sys.exit(2)
    keeps = [Path(os.path.relpath(Path(k).resolve(), root)) for k in a.keep]
    finals = [Path(os.path.relpath(Path(f).resolve(), root)) for f in a.final]
    for k in keeps + finals:
        if str(k).startswith(".."):
            print(f"clean: {k} is not inside the project", file=sys.stderr); sys.exit(2)
    items, film = candidates(root, finals, keeps + finals)
    if not film:
        held = [p for k, p in items if k == "renders"]
        items = [x for x in items if x[0] != "renders"]
        if held:
            print(f"clean: no film found (out/final/, out/final*.*, media/, out/publish/), so the {len(held)} video(s) under out/ stay: "
                  "name the film with --final <file> to clear the others")
    sizes = {p: size(p) for _, p in items}
    total = sum(sizes.values())
    say = {"rebuilt": "made again by the tools", "renders": "renders that are not the film", "sound": "sound not in use"}
    print(f"clean: {root.name} · {human(size(root))} now · {len(items)} item(s), {human(total)} " + ("to clear" if a.yes else "would go (a dry run: --yes clears them)"))
    for kind in ("rebuilt", "renders", "sound"):
        xs = [p for k, p in items if k == kind]
        if not xs: continue
        where = "deleted" if a.delete and kind != "sound" else "to the Trash"
        print(f"  {kind} ({say[kind]}; {where}): {human(sum(sizes[p] for p in xs))}")
        for p in sorted(xs, key=lambda q: -sizes[q])[:25]:
            print(f"    {human(sizes[p]):>9}  {p.relative_to(root)}{'/' if p.is_dir() and not p.is_symlink() else ''}")
        if len(xs) > 25: print(f"    … {len(xs) - 25} more")
    if not a.yes:
        sys.exit(0)
    failed, trashed, deleted = 0, 0, 0
    tdir = trash_dir()
    for kind, p in items:
        try:
            if a.delete and kind != "sound":
                remove(p, root); deleted += sizes[p]
            else:
                to_trash(p, tdir); trashed += sizes[p]
        except OSError as e:
            failed += 1; print(f"  ✗ {p.relative_to(root)}: {e}")
    print(f"clean: {human(deleted)} deleted, {human(trashed)} moved to the Trash" + (f", {failed} could not be cleared" if failed else "") +
          f"; {root.name} is {human(size(root))} now")
    if trashed:
        print("  the space comes back when the Trash is emptied (that is yours to do)")
    if sys.platform == "darwin" and (deleted or trashed):
        r = subprocess.run(["tmutil", "listlocalsnapshots", "/"], capture_output=True, text=True)
        n = len([l for l in r.stdout.splitlines() if "com.apple" in l]) if r.returncode == 0 else 0
        if n:
            print(f"  Time Machine holds {n} local snapshot(s): data deleted since the last one stays on the disk until macOS drops them (hours; sooner when space runs short)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
