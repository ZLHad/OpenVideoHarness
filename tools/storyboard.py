"""Storyboard sheets for a human to decide from: one labelled page per segment (3–6 shots) and an overview.

usage: bin/vh storyboard <project> [--shots shots.json] [--video out/animatic.mp4 | --snapshot] [--unsure S02,S04]
                                   [--per 6] [--at 0.6] [--max S] [--lang zh|en] [--out DIR]

Reads <project>/shots.json (schema below) and takes one frame per shot:
  1. the shot's "frame" image, if it has one;
  2. else a frame of a rendered video at the shot's "at" time (default: start + 60 % of the shot, --at changes the 60 %):
     --video, else the "video" named in shots.json, else the first of out/animatic.mp4, out/draft.mp4, out/final.mp4,
     media/final.mp4, then the newest out/*.mp4;
  3. --snapshot: capture those times straight from the HyperFrames composition (npx hyperframes snapshot, no render;
     --describe false, so no frame is sent to Gemini); needs the project's own hyperframes and its Chrome;
  4. nothing found: a grey tile that says so. The pages are still useful to read the plan.
Shots marked "unsure" (or listed in --unsure) get a red frame and their reason under the tile. A duration longer
than the type's "new payoff every N s" (see bin/vh rhythm) is printed in red.

Writes <project>/out/check/storyboard/: overview.png, NN-<segment>.png (one per segment; a segment with more than
--per shots is split into pages), frames/ (the tiles' source frames) and index.json (pages, shots, files: for review
pages). Deterministic: the same shots and frames give the same PNG bytes. The shots.json schema: bin/vh storyboard -h.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vhdraw as V
import readcheck as RC

VIDEO_CANDIDATES = ["out/animatic.mp4", "out/draft.mp4", "out/final.mp4", "media/final.mp4"]

def pick_video(project, meta, arg):
    if arg:
        p = Path(arg) if Path(arg).is_absolute() else (Path.cwd() / arg if (Path.cwd() / arg).exists() else project / arg)
        if not p.exists():
            raise SystemExit(f"storyboard: no such video: {arg}")
        return p
    if meta.get("video"):
        p = project / meta["video"]
        if p.exists():
            return p
        V.warn_once(f"shots.json names video {meta['video']}, which does not exist")
    for c in VIDEO_CANDIDATES:
        if (project / c).exists():
            return project / c
    outs = sorted((project / "out").glob("*.mp4"), key=lambda p: (p.stat().st_mtime, p.name), reverse=True) if (project / "out").is_dir() else []
    return outs[0] if outs else None

def probe(video):
    out = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                     "stream=width,height,duration,avg_frame_rate:format=duration", "-of", "json", str(video)],
                                    capture_output=True, text=True, check=True).stdout)
    st = (out.get("streams") or [{}])[0]
    dur = float(st.get("duration") or out.get("format", {}).get("duration") or 0)
    num, _, den = st.get("avg_frame_rate", "0/0").partition("/")
    rate = float(num) / float(den) if float(den or 0) and float(num or 0) else 30.0
    return int(st.get("width", 0)), int(st.get("height", 0)), dur, max(0.0, dur - 1.5 / rate)

def grab(video, t, width, dst):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                    "-vf", f"scale={width}:-2", str(dst)], check=True)
    return dst if dst.exists() else None

def snapshot(project, want, dst):
    """HyperFrames snapshot of the composition: want = [(shot id, file name, t)] → {shot id: path}; {} when it cannot run.
    HyperFrames names its files frame-NN-at-T.png in --at order, NN padded to two digits (frame-100 sorts before
    frame-11 as text), so they are matched by the number."""
    hf = project / "node_modules" / ".bin" / "hyperframes"
    if not (project / "hyperframes.json").exists():
        V.warn_once("--snapshot needs a HyperFrames project (hyperframes.json); using the video instead"); return {}
    if not hf.exists():
        V.warn_once("--snapshot: no node_modules/.bin/hyperframes in the project (bin/vh hf-init installs it); using the video instead"); return {}
    if not want: return {}
    tmp = Path(tempfile.mkdtemp(prefix="vh-snap-"))
    env = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1", "DO_NOT_TRACK": "1"}
    cmd = [str(hf), "snapshot", str(project), "--at", ",".join(f"{t:.3f}" for _, _, t in want), "--no-end", "--describe", "false", "-o", str(tmp)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    got = {}
    for f in tmp.glob("frame-*.png"):
        m = re.match(r"frame-(\d+)-", f.name)
        if m: got[int(m.group(1))] = f
    if r.returncode != 0 or len(got) < len(want):
        V.warn_once(f"hyperframes snapshot failed ({(r.stderr or r.stdout).strip().splitlines()[-1:] or ['no output']}); using the video instead")
        shutil.rmtree(tmp, ignore_errors=True); return {}
    dst.mkdir(parents=True, exist_ok=True); res = {}
    for i, (sid, name, _) in enumerate(want):
        q = dst / name; shutil.move(str(got[i]), q); res[sid] = q
    shutil.rmtree(tmp, ignore_errors=True)
    return res

def safe_names(shots):
    """{shot id: file name for its frame}: the id with anything odd replaced, made unique."""
    out, used = {}, set()
    for s in shots:
        base = re.sub(r"[^\w.-]+", "_", s["id"]).strip("._") or "shot"
        name, k = base, 1
        while name.lower() in used: k += 1; name = f"{base}-{k}"
        used.add(name.lower()); out[s["id"]] = name + ".png"
    return out

def fit(im, w, h, bg=(26, 26, 30)):
    """im in a w×h box: resized when the shapes match, else letterboxed (a portrait frame is never stretched)."""
    iw, ih = im.size
    if abs(iw / ih - w / h) <= 0.02 * (w / h):
        return im.resize((w, h), Image.LANCZOS) if im.size != (w, h) else im
    k = min(w / iw, h / ih); nw, nh = max(1, round(iw * k)), max(1, round(ih * k))
    box = Image.new("RGB", (w, h), bg); box.paste(im.resize((nw, nh), Image.LANCZOS), ((w - nw) // 2, (h - nh) // 2))
    return box

def pages_of(ss, per):
    """A segment's shots over as few pages as --per allows, as evenly as possible: 26 at 6 a page → 5 5 5 5 6."""
    k = max(1, math.ceil(len(ss) / per)); base, extra = divmod(len(ss), k)
    sizes = [base] * (k - extra) + [base + 1] * extra
    out, i = [], 0
    for n in sizes:
        out.append(ss[i:i + n]); i += n
    return out

def slug(s, i):
    keep = "".join(c if (c.isalnum() or V.is_cjk(c)) else "-" for c in s).strip("-")
    return f"{i:02d}-{keep[:24] or 'shots'}"

def fmt(t):
    return f"{t:.1f}"

class Sheet:
    def __init__(self, a, project, shots, frames, notes, aspect, limit, limit_src, lang, source_note):
        self.a, self.project, self.shots, self.frames, self.limit, self.limit_src = a, project, shots, frames, limit, limit_src
        self.notes = notes   # shot id → why its tile is grey
        self.L, self.lang, self.source_note = V.LABELS[lang], lang, source_note
        self.ar = aspect
        if aspect >= 1.2: self.tw, self.cols = 600, 3
        elif aspect >= 0.8: self.tw, self.cols = 420, 4
        else: self.tw, self.cols = 300, 6
        self.th = int(round(self.tw / aspect))

    def tile(self, s, w, h):
        f, note = self.frames.get(s["id"]), self.notes.get(s["id"])
        if f and not note:
            try:
                with Image.open(f) as im:
                    return fit(im.convert("RGB"), w, h)
            except (OSError, ValueError, SyntaxError):
                note = self.notes[s["id"]] = ("不是图片：" if self.lang == "zh" else "not an image: ") + V.shown(f, self.project)
                V.warn_once(f"{s['id']}: {V.shown(f, self.project)} is not an image; its tile stays grey")
        im = Image.new("RGB", (w, h), (214, 211, 203)); d = ImageDraw.Draw(im)
        f_ = V.font(max(13, w // 22))
        lines = V.wrap(d, note or self.L["no_frame"], f_, w - 20, 3)
        for j, line in enumerate(lines):
            V.text(d, (w // 2, h // 2 + (j - (len(lines) - 1) / 2) * f_.size * 1.3), line, f_, V.MUTED, "mm")
        return im

    def long(self, s):
        return self.limit is not None and s["dd"] > self.limit + 1e-6

    def strip(self, d, x0, y0, w, h, shots, t0, t1, colors):
        """Proportional bar of the shots' lengths: long ones red, unsure ones outlined red with a ?."""
        span = max(t1 - t0, 1e-6); fs = V.font(18, bold=True); fsm = V.font(15)
        for s in shots:
            a = x0 + (s["start"] - t0) / span * w; b = x0 + (s["end"] - t0) / span * w
            col = V.RED if self.long(s) else V.mix(colors[s["segment"]], (255, 255, 255), 0.35)
            d.rectangle([a + 1, y0, b - 1, y0 + h], fill=col)
            if s["unsure"] is not None:
                d.rectangle([a + 1, y0, b - 1, y0 + h], outline=V.RED, width=3)
            sid = s["id"] + (" ?" if s["unsure"] is not None else "")
            lab = f"{sid}  {s['dd']:.1f}s"
            if V.tw(d, lab, fs) + 10 < b - a:
                V.text(d, (a + 6, y0 + h / 2), sid, fs, (255, 255, 255), "lm")
                V.text(d, (b - 6, y0 + h / 2), f"{s['dd']:.1f}s", fsm, (255, 255, 255), "rm")
            elif V.tw(d, s["id"], fsm) + 6 < b - a:
                V.text(d, ((a + b) / 2, y0 + h / 2), s["id"], fsm, (255, 255, 255), "mm")

    def page_cols(self, n):
        """Columns for n shots: 2 × 2 rather than 3 + 1 for four landscape frames; one row for up to 6 portrait ones."""
        if self.ar >= 1.2: return {1: 1, 2: 2, 4: 2}.get(n, 3)
        if self.ar >= 0.8: return {5: 3, 6: 3}.get(n, min(n, 4))
        return min(n, 6)

    def page(self, name, shots, k, n, colors, part=""):
        L, tw, th, cols = self.L, self.tw, self.th, self.page_cols(len(shots))
        pad, gap, label_h = 36, 24, (150 if self.ar >= 0.8 else 222)
        rows = math.ceil(len(shots) / cols)
        W = pad * 2 + cols * tw + (cols - 1) * gap
        W = max(W, 1100)
        head, strip_h = 118, 44
        H = head + strip_h + 40 + rows * (th + label_h + gap) + 70
        img = Image.new("RGB", (W, H), V.BG); d = ImageDraw.Draw(img)
        t0, t1 = shots[0]["start"], shots[-1]["end"]
        seg = name or (f"{L['shots']} {shots[0]['id']}–{shots[-1]['id']}")
        V.text(d, (pad, 30), f"{seg}{part}   {shots[0]['ds']}–{shots[-1]['de']} s", V.font(40, bold=True), colors[name])
        avg = sum(s["dur"] for s in shots) / len(shots)
        sub = f"{L['shot_1'] if len(shots) == 1 else L['shot_n'].format(n=len(shots))} · {L['avg']} {avg:.1f} s · {k}/{n}"
        if self.limit is not None:
            sub += f" · {L['limit']} {self.limit:g} s ({self.limit_src})"
        V.text(d, (pad, 84), V.fit(d, sub, V.font(24), W - 2 * pad), V.font(24), V.MUTED)
        self.strip(d, pad, head + 6, W - 2 * pad, strip_h, shots, t0, t1, colors)
        y = head + strip_h + 40
        f_id, f_read, f_uns, f_dur = V.font(30, bold=True), V.font(25), V.font(23), V.font(26)
        for i, s in enumerate(shots):
            r, c = divmod(i, cols); x = pad + c * (tw + gap); yy = y + r * (th + label_h + gap)
            img.paste(self.tile(s, tw, th), (x, yy))
            if s["unsure"] is not None:
                d.rectangle([x - 5, yy - 5, x + tw + 4, yy + th + 4], outline=V.RED, width=6)
            else:
                d.rectangle([x - 1, yy - 1, x + tw, yy + th], outline=V.RULE, width=1)
            ly = yy + th + 12
            head_s = f"{s['id']}   {s['ds']}–{s['de']} s"
            dur_s = f"({s['dd']:.1f} s)"
            if V.tw(d, head_s, f_id) + 12 + V.tw(d, dur_s, f_dur) <= tw:   # one line when it fits, else id + duration, then the times
                V.text(d, (x, ly), head_s, f_id, V.INK)
                V.text(d, (x + V.tw(d, head_s, f_id) + 12, ly + 3), dur_s, f_dur, V.RED if self.long(s) else V.MUTED)
                ly += 42
            else:
                V.text(d, (x, ly), s["id"], f_id, V.INK)
                V.text(d, (x + tw, ly + 3), f"{s['dd']:.1f} s", f_dur, V.RED if self.long(s) else V.MUTED, "ra")
                V.text(d, (x, ly + 40), f"{s['ds']}–{s['de']} s", V.font(22), V.MUTED)
                ly += 74
            reads = " / ".join(([s["label"]] if s["label"] else []) + s["reads"])
            nl = 2 if self.ar >= 0.8 else 3
            if s["unsure"] is not None: nl -= 1 if self.ar >= 0.8 else 0
            for line in V.wrap(d, reads, f_read, tw, nl):
                V.text(d, (x, ly), line, f_read, V.INK); ly += 33
            if s["unsure"] is not None:
                u = L["unsure"] + ("：" if self.lang == "zh" else ": ") + s["unsure"] if s["unsure"] else L["unsure"]
                for line in V.wrap(d, u, f_uns, tw, 2 if self.ar < 0.8 else 1):
                    V.text(d, (x, ly), line, f_uns, V.RED); ly += 30
        leg = self.legend()
        V.text(d, (pad, H - 44), V.fit(d, leg, V.font(20), W - 2 * pad), V.font(20), V.MUTED)
        return img

    def legend(self):
        zh = self.lang == "zh"
        bits = ["红框 = 没把握的镜头" if zh else "red frame = least sure"]
        if self.limit is not None:
            bits.append((f"红色时长 = 超过 {self.limit:g} s" if zh else f"red duration = longer than {self.limit:g} s"))
        bits.append(("画面：" if zh else "frames: ") + self.source_note)
        return " · ".join(bits)

    def overview(self, runs, colors):
        L = self.L
        ow = self.tw // 2; oh = int(round(ow / self.ar))
        cols = max(3, min(self.cols * 2, max(len(ss) for _, ss in runs)))   # as wide as the longest segment needs
        pad, gap, lab_w, cap_h = 32, 12, 190, 30
        rows = []
        for name, shots in runs:
            for i in range(0, len(shots), cols):
                rows.append((name, shots[i:i + cols], i == 0, shots[0]["start"], shots[-1]["end"]))
        W = pad * 2 + lab_w + cols * ow + (cols - 1) * gap
        ribbon_h, head = 40, 104
        H = head + ribbon_h + 36 + len(rows) * (oh + cap_h + gap) + 64
        img = Image.new("RGB", (W, H), V.BG); d = ImageDraw.Draw(img)
        T0, T1 = self.shots[0]["start"], self.shots[-1]["end"]
        V.text(d, (pad, 28), f"{L['overview']}   {fmt(T0)}–{fmt(T1)} s", V.font(38, bold=True), V.INK)
        nun = sum(s["unsure"] is not None for s in self.shots); nlong = sum(self.long(s) for s in self.shots)
        sub = (f"{L['shot_1'] if len(self.shots) == 1 else L['shot_n'].format(n=len(self.shots))} · {len(runs)} "
               + ("段" if self.lang == "zh" else ("segment" if len(runs) == 1 else "segments")))
        if nun: sub += f" · {nun} " + ("镜没把握" if self.lang == "zh" else "unsure")
        if self.limit is not None: sub += f" · {nlong} " + (f"镜超过 {self.limit:g} s" if self.lang == "zh" else f"over {self.limit:g} s")
        V.text(d, (pad, 76), sub, V.font(22), V.MUTED)
        # the timeline ribbon: segments in their colours, a tick at every cut
        x0, x1, y0 = pad + lab_w, W - pad, head
        span = max(T1 - T0, 1e-6)
        for name, shots in runs:
            a = x0 + (shots[0]["start"] - T0) / span * (x1 - x0); b = x0 + (shots[-1]["end"] - T0) / span * (x1 - x0)
            d.rectangle([a, y0, b, y0 + ribbon_h], fill=colors[name])
        for s in self.shots[1:]:   # a tick at every cut, under the names
            x = x0 + (s["start"] - T0) / span * (x1 - x0); d.line([(x, y0), (x, y0 + ribbon_h)], fill=V.mix(V.BG, V.INK, 0.15), width=2)
        for name, shots in runs:
            a = x0 + (shots[0]["start"] - T0) / span * (x1 - x0); b = x0 + (shots[-1]["end"] - T0) / span * (x1 - x0)
            if name and V.tw(d, name, V.font(18, bold=True)) + 8 < b - a:
                tw_ = V.tw(d, name, V.font(18, bold=True))
                d.rectangle([a + 2, y0 + 6, a + tw_ + 10, y0 + ribbon_h - 6], fill=colors[name])
                V.text(d, (a + 6, y0 + ribbon_h / 2), name, V.font(18, bold=True), (255, 255, 255), "lm")
        for s in self.shots:
            if s["unsure"] is not None:
                a = x0 + (s["start"] - T0) / span * (x1 - x0); b = x0 + (s["end"] - T0) / span * (x1 - x0)
                d.rectangle([a + 1, y0 + ribbon_h + 3, b - 1, y0 + ribbon_h + 8], fill=V.RED)
        V.text(d, (pad, y0 + ribbon_h / 2), f"{fmt(T0)}–{fmt(T1)} s", V.font(18), V.MUTED, "lm")
        y = head + ribbon_h + 36
        fcap = V.font(18, bold=True); fdur = V.font(17)
        for name, shots, first, r0, r1 in rows:
            if first:
                V.text(d, (pad, y + 4), V.fit(d, name or "—", V.font(24, bold=True), lab_w - 12), V.font(24, bold=True), colors[name])
                V.text(d, (pad, y + 36), f"{fmt(r0)}–{fmt(r1)} s", V.font(18), V.MUTED)
            for i, s in enumerate(shots):
                x = pad + lab_w + i * (ow + gap)
                img.paste(self.tile(s, ow, oh), (x, y))
                if s["unsure"] is not None:
                    d.rectangle([x - 3, y - 3, x + ow + 2, y + oh + 2], outline=V.RED, width=4)
                V.text(d, (x, y + oh + 5), s["id"], fcap, V.INK)
                V.text(d, (x + ow, y + oh + 6), f"{s['dd']:.1f}s", fdur, V.RED if self.long(s) else V.MUTED, "ra")
            y += oh + cap_h + gap
        V.text(d, (pad, H - 40), V.fit(d, self.legend(), V.font(18), W - 2 * pad), V.font(18), V.MUTED)
        return img

def main():
    ap = argparse.ArgumentParser(prog="bin/vh storyboard", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=V.SHOTS_SCHEMA)
    ap.add_argument("project")
    ap.add_argument("--shots", help="shots file (default: <project>/shots.json)")
    ap.add_argument("--video", help="take the frames from this video")
    ap.add_argument("--snapshot", action="store_true", help="capture the frames from the HyperFrames composition instead")
    ap.add_argument("--unsure", default="", help="comma-separated shot ids to mark as least sure (added to shots.json's)")
    ap.add_argument("--per", type=int, default=6, help="shots per page, 3–6 (default 6)")
    ap.add_argument("--at", type=float, default=0.6, dest="at_frac", help="where in each shot to take its frame, 0–1 (default 0.6)")
    ap.add_argument("--max", type=float, help="flag shots longer than this (default: the type's payoff interval)")
    ap.add_argument("--lang", choices=("zh", "en"), help="labels (default: zh when the shots are in Chinese)")
    ap.add_argument("--out", help="output folder (default <project>/out/check/storyboard)")
    a = ap.parse_args()
    if not 3 <= a.per <= 6: ap.error("--per must be 3–6")
    if not 0 <= a.at_frac <= 1: ap.error("--at must be 0–1")
    project = V.project_dir(a.project)
    sp = Path(a.shots) if a.shots else project / "shots.json"
    if not sp.exists():
        raise SystemExit(f"storyboard: no {V.shown(sp)}. Write one from STORYBOARD.md's shot table:\n{V.SHOTS_SCHEMA}")
    shots, meta = V.load_shots(sp)
    extra = {x.strip() for x in a.unsure.split(",") if x.strip()}
    unknown = extra - {s["id"] for s in shots}
    if unknown: raise SystemExit(f"storyboard: --unsure names unknown shots: {', '.join(sorted(unknown))}")
    for s in shots:
        if s["id"] in extra and s["unsure"] is None: s["unsure"] = ""
    out = Path(a.out) if a.out else project / "out" / "check" / "storyboard"
    fdir = out / "frames"
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob("*.png"): old.unlink()   # frames of an earlier run
    try:   # the pages an earlier run wrote (its index.json lists them): segments may have been renamed since
        for pg in json.loads((out / "index.json").read_text(encoding="utf-8")).get("pages", []):
            if (out / pg["file"]).is_file(): (out / pg["file"]).unlink()
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    names = safe_names(shots)
    frames, notes, need = {}, {}, []
    for s in shots:
        if s["frame"]:
            p = project / s["frame"]
            if p.is_file(): frames[s["id"]] = p; continue
            V.warn_once(f"{s['id']}: frame {s['frame']} not found; taking one from the video")
        t = float(s["at"]) if s["at"] is not None else s["start"] + a.at_frac * s["dur"]
        need.append((s, t))
    source, used_video = [], None
    aspect = None
    past = lambda where, dur, ids: V.warn_once(f"{V.plural(len(ids), 'shot')} past the end of {where} ({dur:.1f} s), left grey: {', '.join(ids)}")
    if need and a.snapshot:
        comp_dur = RC.composition_duration(project / "index.html") if (project / "index.html").is_file() else None
        late = [s["id"] for s, t in need if comp_dur is not None and t > comp_dur + 1e-6]
        got = snapshot(project, [(s["id"], names[s["id"]], t) for s, t in need if s["id"] not in late], fdir)
        if got:
            frames.update(got); source.append("hyperframes snapshot")
            for sid in late: notes[sid] = (f"在 index.html 的结尾（{comp_dur:.1f} s）之后" if lang_hint(shots) == "zh"
                                           else f"past the end of index.html ({comp_dur:.1f} s)")
            if late: past("index.html", comp_dur, late)
            need = []
    if need:
        video = pick_video(project, meta, a.video)
        if video:
            w, h, dur, last = probe(video)
            if w and h: aspect = w / h
            tw = 640 if (aspect or 1.78) >= 1.2 else (440 if (aspect or 1) >= 0.8 else 320)
            late = []
            for s, t in need:
                if dur and t > dur + 1e-6:   # never a clamped last frame standing in for a shot the video does not reach
                    late.append(s["id"])
                    notes[s["id"]] = (f"在 {V.shown(video, project)} 的结尾（{dur:.1f} s）之后" if lang_hint(shots) == "zh"
                                      else f"past the end of {V.shown(video, project)} ({dur:.1f} s)")
                    continue
                p = grab(video, min(max(0.0, t), last), tw, fdir / names[s["id"]])
                if p: frames[s["id"]] = p
            if late: past(V.shown(video, project), dur, late)
            used_video = video
            pct = f"{int(round(a.at_frac * 100))} %"
            source.append(f"{V.shown(video, project)} @ {pct}" if not any(s['at'] is not None for s, _ in need) else V.shown(video, project))
        else:
            V.warn_once("no video found (out/animatic.mp4, out/draft.mp4, out/final.mp4 …): tiles without a frame stay grey; "
                        "render one, pass --video, or use --snapshot")
    if any(s["frame"] and s["id"] in frames and Path(frames[s["id"]]).parent != fdir for s in shots):
        source.append("shots.json frame")
    if aspect is None:
        for s in shots:
            if s["id"] in frames and s["id"] not in notes:
                try:
                    with Image.open(frames[s["id"]]) as im: aspect = im.size[0] / im.size[1]
                    break
                except (OSError, ValueError, SyntaxError):
                    continue
    aspect = aspect or 16 / 9
    limit, limit_src = V.payoff_limit(project, a.max)
    lang = V.lang_for([s["segment"] for s in shots] + [r for s in shots for r in s["reads"]], a.lang)
    V.check_glyphs([s["segment"] for s in shots] + [r for s in shots for r in s["reads"]] + [s["label"] for s in shots]
                   + [s["unsure"] or "" for s in shots] + [s["id"] for s in shots])
    runs = V.segments_of(shots)
    colors = {}
    for i, (name, _) in enumerate(runs):
        colors.setdefault(name, V.seg_color(len(colors)))
    sheet = Sheet(a, project, shots, frames, notes, aspect, limit, limit_src, lang, " + ".join(source) or ("—" if lang == "en" else "无"))
    pages = []
    for name, ss in runs:
        chunks = pages_of(ss, a.per)
        for j, ch in enumerate(chunks):
            pages.append((name, ch, f" ({j + 1}/{len(chunks)})" if len(chunks) > 1 else ""))
    index = {"project": project.name, "shots": V.relpath(sp, project), "limit_s": limit, "overview": "overview.png", "pages": []}
    written, segs = [], []
    for k, (name, ch, part) in enumerate(pages, 1):
        img = sheet.page(name, ch, k, len(pages), colors, part)
        fn = f"{slug(name, k)}.png"
        written.append(V.save(img, out / fn))
        index["pages"].append({"file": fn, "segment": name, "start": ch[0]["start"], "end": ch[-1]["end"],
                               "shots": [s["id"] for s in ch], "unsure": [s["id"] for s in ch if s["unsure"] is not None],
                               "long": [s["id"] for s in ch if sheet.long(s)]})
        segs.append((fn[:-4], name + part, ch))
    ov = V.save(sheet.overview(runs, colors), out / "overview.png")
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    review = review_pack(project, out, shots, segs, frames, notes, sheet, lang, used_video, limit, limit_src)
    (out / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    nun = sum(s["unsure"] is not None for s in shots)
    print(f"storyboard: {V.plural(len(shots), 'shot')} · {V.plural(len(runs), 'segment')} · {V.plural(len(pages), 'page')} · "
          f"frames from {', '.join(source) or 'nowhere (grey tiles)'}")
    print(f"  {V.shown(ov)}   (+ index.json, and review.json for bin/vh review: \"include\": \"{V.relpath(out / 'review.json', project)}\")")
    for p, (name, ch, part) in zip(written, pages):
        flags = [s["id"] + ("?" if s["unsure"] is not None else "") + ("!" if sheet.long(s) else "") for s in ch if s["unsure"] is not None or sheet.long(s)]
        print(f"  {V.shown(p)}  {V.plural(len(ch), 'shot')}" + (f"  (? unsure, ! over {limit:g} s: {' '.join(flags)})" if flags else ""))
    if limit is None:
        print(f"  note: {limit_src}")
    if nun == 0:
        print("  note: no shot is marked unsure; add \"unsure\": \"why\" to the least sure ones in shots.json (or --unsure S02,S04)")

def lang_hint(shots):
    return V.lang_for([s["segment"] for s in shots] + [r for s in shots for r in s["reads"]])

def review_pack(project, out, shots, segs, frames, notes, sheet, lang, video, limit, limit_src):
    """out/check/storyboard/review.json in tools/review.py's shape, for a gate JSON to "include": one segment per page
    (id = the page's file stem), the shots with their frames, reads and the narration they sit under, the least-sure
    shots, the pages as assets and the video as the animatic. Too-long shots and grey tiles go into the segment's
    note: a shot's own note is what review.py shows as a planned change."""
    zh = lang == "zh"
    narr, _ = V.narration(project, lang if lang in ("zh", "en") else None)
    def vo(s):   # the narration lines this shot sits under (at least 0.3 s of overlap, or the whole shot)
        return " ".join(n["text"] for n in narr if min(n["end"], s["end"]) - max(n["start"], s["start"]) >= min(0.3, s["dur"] - 1e-6) and n["text"])
    rsegs, assets = [], [{"path": V.relpath(out / "overview.png", project), "caption": "分镜总览：全部镜头" if zh else "Storyboard overview: every shot"}]
    for sid, title, ch in segs:
        bits = []
        longs = [s for s in ch if sheet.long(s)]
        if longs:
            what = "、".join(f"{s['id']} {s['dd']:.1f} s" for s in longs) if zh else ", ".join(f"{s['id']} {s['dd']:.1f} s" for s in longs)
            bits.append((f"{what} 超过 {limit:g} s（{limit_src}）" if zh else f"{what} over {limit:g} s ({limit_src})"))
        greys = [s for s in ch if s["id"] in notes]
        if greys:
            bits.append(("；".join(f"{s['id']}：{notes[s['id']]}" for s in greys)) if zh else "; ".join(f"{s['id']}: {notes[s['id']]}" for s in greys))
        rsegs.append({"id": sid, "title": title, "t0": round(ch[0]["start"], 3), "t1": round(ch[-1]["end"], 3),
                      "note": ("；" if zh else "; ").join(bits),
                      "shots": [{"id": s["id"], "t0": round(s["start"], 3), "t1": round(s["end"], 3),
                                 "frame": V.relpath(frames[s["id"]], project) if s["id"] in frames and s["id"] not in notes else "",
                                 "see": " / ".join(([s["label"]] if s["label"] else []) + s["reads"]), "vo": vo(s), "note": ""} for s in ch]})
        assets.append({"path": V.relpath(out / f"{sid}.png", project), "caption": title, "for": sid})
    pack = {"lang": "zh" if zh else "en", "segments": rsegs, "assets": assets,
            "least_sure": [{"id": s["id"], "note": s["unsure"]} for s in shots if s["unsure"] is not None]}
    if video: pack["animatic"] = V.relpath(video, project)
    return pack

if __name__ == "__main__":
    main()
