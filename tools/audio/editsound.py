"""The sounds an edit list places (engines/EDIT.md), for bin/vh mix … edit= (stdlib and ffmpeg).

An edit list says where footage's own sound and the sound tracks' entries play in the film, with their role, gain, fades,
lead and lag; the mix does everything else (the narration, the music, the effects, the levels). edit= takes the project's
edit.json (it is resolved here, as bin/vh edit build resolves it) or the resolved out/edit.resolved.json.

  load(path)            → (the resolved document, the project folder)
  files(doc, project)   → every file the placed sounds and the time sources read (bin/vh mix's record keeps them, so
                          bin/vh mux refuses a mix made before the edit list or one of them changed)
  apply(kv, tmp)        → (kv with voice=, sfx= and timeline= as the mix should take them, events for a mix profile,
                          what was said): each sound cut from its file into tmp (in, length, fades, gain); role voice
                          joins the voice bus (it is narration: the anchor, VMR and making way follow it), the others
                          become events of their class for a profile, or one more layer of the SFX bus for the default
                          chain; timeline= is out/edit.timeline.<lang>.json (bin/vh edit build: the narration with the
                          footage's words) when the edit list places a voice and none is given
"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SR = 48000


def load(path):
    """edit= as given: a project folder or its edit.json (resolved now), or a resolved document (out/edit.resolved.json)"""
    p = Path(path).resolve()
    sys.path.insert(0, str(HERE.parent))
    import edit
    if p.is_dir() or p.name == "edit.json":
        project = p if p.is_dir() else p.parent
        try:
            return edit.resolve(project), project
        except edit.EditError as e:
            raise ValueError(f"edit={path}: the edit list does not resolve: " + "; ".join(e.problems[:3])) from None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"edit={path}: not readable ({e})") from None
    if not (isinstance(d, dict) and isinstance(d.get("entries"), list) and d.get("fps")):
        raise ValueError(f"edit={path}: an edit.json, its project, or bin/vh edit build's out/edit.resolved.json")
    project = p.parent.parent if p.parent.name == "out" else p.parent
    return d, project


def files(doc, project):
    """the edit list itself, the time sources it read, and every sound file it places: absolute paths"""
    out = {Path(project) / "edit.json"}
    out |= {Path(project) / r["path"] for r in doc.get("refs") or [] if isinstance(r, dict) and r.get("path")}
    for s in doc.get("sound") or []:
        f = Path(s["file"])
        out.add(f if f.is_absolute() else Path(project) / f)
    return sorted(str(Path(os.path.abspath(f))) for f in out)


def cut(s, project, dst, end):
    """one placed sound as a stereo 48 kHz WAV: its file from `in` for its length (cut at the film's end), faded in
    and out, at its gain → (dst, its length in seconds) or None when nothing of it is inside the film"""
    f = Path(s["file"]) if Path(s["file"]).is_absolute() else Path(project) / s["file"]
    t0, t1 = s["film"][0], min(s["film"][1], end)
    dur = t1 - max(0.0, t0)
    if dur <= 0:
        return None
    skip = s["in"] + max(0.0, -t0)   # a lead before the film's start is cut off
    fi, fo = min(s["fade"][0], dur / 2), min(s["fade"][1], dur / 2)
    af = f"aresample={SR},aformat=channel_layouts=stereo,apad,atrim=0:{dur:.6f}" + (f",afade=t=in:st=0:d={fi:.4f}" if fi > 0 else "") + \
         (f",afade=t=out:st={dur - fo:.6f}:d={fo:.4f}" if fo > 0 else "") + f",volume={s['gain_db']:.3f}dB"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{skip:.6f}", "-i", str(f), "-map", "0:a:0", "-af", af, "-c:a", "pcm_s16le", str(dst)],
                   check=True, capture_output=True)
    return dst, dur


def bus(pieces, dst, end):
    """pieces [(wav, film start)] mixed into one stereo track of the film's length (silence between them)"""
    if not pieces:
        return None
    ins, f = [], []
    for i, (w, t) in enumerate(pieces):
        ins += ["-i", str(w)]
        f.append(f"[{i}:a]adelay={max(0, round(t * 1000))}:all=1[a{i}]")
    f.append("".join(f"[a{i}]" for i in range(len(pieces))) + f"amix=inputs={len(pieces)}:normalize=0:duration=longest,apad=whole_dur={end:.6f},atrim=0:{end:.6f}[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(f), "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_s16le", str(dst)],
                   check=True, capture_output=True)
    return dst


def plus(a, b, dst):
    """two tracks summed (no normalising), as long as the longer"""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-i", str(b), "-filter_complex",
                    f"[0:a]aresample={SR},aformat=channel_layouts=stereo[x];[1:a]aresample={SR},aformat=channel_layouts=stereo[y];"
                    "[x][y]amix=inputs=2:normalize=0:duration=longest[out]", "-map", "[out]", "-c:a", "pcm_s16le", str(dst)], check=True, capture_output=True)
    return dst


def apply(kv, tmp):
    doc, project = load(kv["edit"])
    sounds, end = doc.get("sound") or [], doc["frames"] / doc["fps"]
    kv, said, events = dict(kv), [], []
    voice, rest = [], []
    for i, s in enumerate(sounds):
        got = cut(s, project, Path(tmp) / f"edit-{i:03d}-{s['entry']}.wav", end)
        if got:
            (voice if s["role"] == "voice" else rest).append((got[0], max(0.0, s["film"][0]), s))
    if voice:
        v = bus([(w, t) for w, t, _ in voice], Path(tmp) / "edit-voice.wav", end)
        kv["voice"] = str(plus(kv["voice"], v, Path(tmp) / "voice+edit.wav") if kv.get("voice") else v)
        said.append(f"edit: {len(voice)} sound{'s' * (len(voice) != 1)} of footage on the voice bus ({', '.join(s['entry'] for _, _, s in voice)})")
        if "timeline" not in kv and kv.get("profile", "none") != "none":   # a profile rides the music under each line of it
            lang = next((r["path"].split("timeline.")[-1].split(".json")[0] for r in doc.get("refs") or [] if r.get("kind") == "timeline" and "timeline." in r["path"]), "zh")
            merged = Path(project) / "out" / f"edit.timeline.{lang if lang != 'json' else 'zh'}.json"
            if merged.is_file():
                kv["timeline"] = str(merged)
                shown = os.path.relpath(merged)
                said.append(f"edit: timeline={merged if shown.startswith('..') else shown} (the narration with the footage's words: bin/vh edit build)")
    if rest:
        profile = kv.get("profile", "none") != "none"
        if profile and "sfx" not in kv:   # each one an event of its class: levelled, made way for, its room
            events = [{"id": f"edit_{s['entry']}", "t": t, "sfx": str(Path(w).resolve()), "role": s["role"]} for w, t, s in rest]
            said.append(f"edit: {len(rest)} sound{'s' * (len(rest) != 1)} as events of their class ({', '.join(sorted({s['role'] for _, _, s in rest}))})")
        else:
            b = bus([(w, t) for w, t, _ in rest], Path(tmp) / "edit-sfx.wav", end)
            kv["sfx"] = str(plus(kv["sfx"], b, Path(tmp) / "sfx+edit.wav") if kv.get("sfx") else b)
            said.append(f"edit: {len(rest)} sound{'s' * (len(rest) != 1)} on the SFX bus" + (" (with sfx=: one pre-placed bus)" if profile else ""))
    if not sounds:
        said.append("edit: the edit list places no sound (footage is silent unless its source or entry says \"sound\")")
    if "dur" not in kv and kv.get("profile", "none") != "none":
        kv["dur"] = f"{end:.6f}"   # the film's length
    return kv, events, said
