"""Rhythm map: shots, words and music on one time axis, with the problems in red.

usage: bin/vh rhythm <project> [--max S] [--segment NAME | --from S --to S] [--lang zh|en] [--beats map.json] [--out PNG]

Lanes, all aligned to the same seconds:
  shots       one bar per shot from shots.json (bin/vh storyboard -h has the schema); taller = longer. Red when it runs
              longer than the type's "new payoff every N s" (dashed line): BRIEF.md's "payoff every A–B s", else the
              type the project was made from (01: 15 s, 02: 5 s, 04: 4 s, 08: 1.5 s), else --max.
  narration   the lines of audio/timeline.json (or timeline.<lang>.json) from bin/vh tts
  captions    the cues of audio/captions.json: red when bin/vh readcheck --mode subtitle fails (under 1.8 s, or faster
              than 9 CJK / 20 Latin characters a second)
  on-screen   texts.json or out/check/texts.json, else the timed text in index.html (bin/vh readcheck --export): red when
              the on-screen rule fails (max(2.5 s, CJK/4.5 + other/15 + 1.5 s))
  music       sections, beats (downbeats taller) and hits of audio/music.beats.json (bin/vh music), or --beats
  issues      every red thing again, with its reason, so it can be read without hunting
Missing inputs just leave their lane out. --segment (a shots.json segment) or --from/--to zooms in: shot boxes then
carry their ids and lengths, and the words are written out.

Writes <project>/out/check/rhythm.png (rhythm-<segment>.png when zoomed) and prints the issues. Exit 0 even with
issues: this is a picture to decide from, not a gate (bin/vh readcheck is the gate).
"""
import argparse, os, re, sys
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vhdraw as V
import readcheck as RC

ONSCREEN = SimpleNamespace(min=2.5, cjk_cps=4.5, latin_cps=15.0, pad=1.5)   # readcheck's defaults
NARR, NARR_EDGE, CAP, CAP_EDGE = (190, 204, 226), (120, 140, 180), (214, 224, 206), (140, 160, 130)
SEC_A, SEC_B, SEC_EDGE = (216, 214, 206), (230, 228, 220), (170, 168, 160)

def narration(project, lang):
    audio = project / "audio"
    cands = ([audio / "timeline.json"] + ([audio / f"timeline.{lang}.json"] if lang else []) +
             sorted(audio.glob("timeline*.json")) if audio.is_dir() else [])
    for p in cands:
        if p.exists():
            d = V.load_json(p)
            segs = d.get("segments", d) if isinstance(d, dict) else d
            out = []
            for i, s in enumerate(segs if isinstance(segs, list) else []):
                if not isinstance(s, dict) or s.get("start") is None or s.get("end") is None: continue
                txt = s.get("text") or (s.get(lang) if lang else None) or s.get("zh") or s.get("en") or ""
                out.append({"id": str(s.get("id", i + 1)), "start": float(s["start"]), "end": float(s["end"]), "text": str(txt)})
            if out:
                return out, p
    return [], None

def captions(project, lang):
    p = project / "audio" / "captions.json"
    if not p.exists():
        return [], None
    _, items = RC.load_items(p)
    langs = [lang] if lang else [k for k in ("zh", "en") if any(it.get(k) for it in items if isinstance(it, dict))] or [None]
    use = langs[0]   # one language per lane: zh when there is Chinese, --lang otherwise
    out = []
    for label, t0, t1, text in RC.pieces(items, use):
        dur = t1 - t0
        need, rate, limit = RC.subtitle_check(text, dur)
        ok = dur >= need - 1e-6
        why = "" if ok else (f"{dur:.1f} s < {RC.SUB_FLOOR:g} s" if dur < RC.SUB_FLOOR - 1e-6 else f"{rate:.1f}/s > {limit:g}/s")
        out.append({"id": label, "start": t0, "end": t1, "text": text, "ok": ok, "why": why})
    return out, p

def onscreen(project):
    """texts.json (written or edited by hand) wins; else the timed text of index.html, read the way readcheck does."""
    p = project / "texts.json"
    if p.exists():
        _, items = RC.load_items(p)
        todo, src = list(RC.pieces(items, None)), p
    else:
        html = project / "index.html"
        if not html.exists():
            return [], None
        items = RC.export_html(html)
        todo, src = [(it["id"], it["start"], it["end"], it["text"]) for it in items], html
    clips = {str(it.get("id")): it["clip"] for it in items if isinstance(it, dict) and it.get("clip")}
    out = []
    for label, t0, t1, text in todo:
        need = RC.onscreen_need(text, ONSCREEN)
        ok = t1 - t0 >= need - 1e-6
        out.append({"id": label, "start": t0, "end": t1, "text": text, "ok": ok, "why": "" if ok else f"{t1 - t0:.1f} s < {need:.1f} s"})
        if label in clips: out[-1]["clip"] = clips[label]
    return out, src if out else None

def beatmap(project, arg):
    if arg:
        p = Path(arg)
        return V.load_json(p), p
    audio = project / "audio"
    for p in [audio / "music.beats.json"] + (sorted(audio.glob("*.beats.json")) if audio.is_dir() else []):
        if p.exists():
            return V.load_json(p), p
    return None, None

class Plot:
    def __init__(self, t0, t1, x0, x1):
        self.t0, self.t1, self.x0, self.x1 = t0, t1, x0, x1
    def x(self, t):
        return self.x0 + (min(max(t, self.t0), self.t1) - self.t0) / max(self.t1 - self.t0, 1e-9) * (self.x1 - self.x0)
    def visible(self, a, b):
        return b > self.t0 and a < self.t1

def pack(items, maxrows=3):
    """Rows for overlapping spans: each item gets the first row where it does not overlap (the last row takes the rest).
    Items with their own timing go first, so a long scene span lands below them."""
    ends, rows = [], {}
    for it in sorted(items, key=lambda i: ("clip" in i, i["start"], i["end"])):
        r = next((k for k, e in enumerate(ends) if e <= it["start"] + 1e-6), None)
        if r is None:
            if len(ends) < maxrows: ends.append(0.0); r = len(ends) - 1
            else: r = maxrows - 1
        ends[r] = max(ends[r], it["end"]); rows[id(it)] = r
    return rows, max(1, len(ends))

def block(d, P, a, b, y0, y1, fill, edge, label=None, f=None, color=V.INK):
    if not P.visible(a, b): return
    xa, xb = P.x(a), P.x(b)
    d.rectangle([xa + 1, y0, max(xa + 2, xb - 1), y1], fill=fill, outline=edge)
    if label and f is not None and xb - xa > 26:
        V.text(d, (xa + 6, (y0 + y1) / 2), V.fit(d, label, f, xb - xa - 10), f, color, "lm")

def main():
    ap = argparse.ArgumentParser(prog="bin/vh rhythm", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--max", type=float, help="shots longer than this are red (default: the type's payoff interval)")
    ap.add_argument("--segment", help="zoom to one segment of shots.json")
    ap.add_argument("--from", dest="t_from", type=float); ap.add_argument("--to", dest="t_to", type=float)
    ap.add_argument("--lang", choices=("zh", "en"), help="caption / narration language and labels")
    ap.add_argument("--beats", help="beat map (default audio/music.beats.json)")
    ap.add_argument("--out", help="output PNG (default <project>/out/check/rhythm.png)")
    a = ap.parse_args()
    project = V.project_dir(a.project)
    shots, _ = V.load_shots(project / "shots.json") if (project / "shots.json").exists() else ([], {})
    narr, narr_src = narration(project, a.lang)
    caps, cap_src = captions(project, a.lang)
    ons, on_src = onscreen(project)
    bm, bm_src = beatmap(project, a.beats)
    if not (shots or narr or caps or ons or bm):
        raise SystemExit("rhythm: nothing to draw: no shots.json, audio/timeline*.json, audio/captions.json, texts.json or audio/*.beats.json")
    limit, limit_src = V.payoff_limit(project, a.max)
    texts = [s["segment"] for s in shots] + [s for sh in shots for s in sh["reads"]] + [n["text"] for n in narr] + [c["text"] for c in caps]
    lang = V.lang_for(texts, a.lang); L = V.LABELS[lang]; zh = lang == "zh"
    V.check_cjk_font(texts)
    ends = [s["end"] for s in shots] + [n["end"] for n in narr] + [c["end"] for c in caps] + [o["end"] for o in ons]
    if bm: ends += [s["end"] for s in bm.get("sections", [])] or [float(bm.get("duration", 0))]
    T0, T1 = 0.0, max(ends)
    runs = V.segments_of(shots)
    if a.segment:
        run = next((ss for n, ss in runs if n == a.segment), None)
        if not run: raise SystemExit(f"rhythm: no segment {a.segment!r} in shots.json ({', '.join(n for n, _ in runs)})")
        T0, T1 = run[0]["start"], run[-1]["end"]
    if a.t_from is not None: T0 = a.t_from
    if a.t_to is not None: T1 = a.t_to
    if T1 <= T0: raise SystemExit("rhythm: --to must come after --from")
    zoom = (T1 - T0) < 0.999 * max(ends)
    colors = {}
    for n, _ in runs: colors.setdefault(n, V.seg_color(len(colors)))
    long = lambda s: limit is not None and s["dur"] > limit + 1e-6

    # issues, in time order
    issues = []
    for s in shots:
        if long(s): issues.append((s["start"], f"{s['id']} {s['dur']:.1f} s > {limit:g} s", "shot"))
    for c in caps:
        if not c["ok"]: issues.append((c["start"], f"{L['captions']} {c['id']}: {c['why']}", "cap"))
    for o in ons:
        if not o["ok"]: issues.append((o["start"], f"{L['onscreen']} {o['id']}: {o['why']}", "on"))
    issues.sort()
    vis = [i for i in issues if T0 - 1e-6 <= i[0] <= T1 + 1e-6]

    # layout
    W, lab_w, pad = 2000, 170, 36
    P = Plot(T0, T1, pad + lab_w, W - pad)
    lanes = []
    if shots: lanes.append(("shots", 250 if not zoom else 170))
    if narr: lanes.append(("narration", 64))
    cap_rows, ncap = pack(caps)
    on_rows, non = pack(ons)
    if caps: lanes.append(("captions", 20 + 44 * ncap))
    if ons: lanes.append(("onscreen", 20 + 44 * non))
    if bm: lanes.append(("music", 96))
    if vis: lanes.append(("issues", 34 + 32 * min(4, len(vis))))
    head = 158 if runs else 110
    H = head + sum(h + 22 for _, h in lanes) + 96
    img = Image.new("RGB", (W, H), V.BG); d = ImageDraw.Draw(img)
    f_lane, f_small, f_tiny = V.font(28, bold=True), V.font(20), V.font(17)

    # title
    title = ("剪辑节奏" if zh else "Rhythm") + f"   {T0:.1f}–{T1:.1f} s"
    V.text(d, (pad, 26), title, V.font(36, bold=True), V.INK)
    sub = []
    ins = [s for s in shots if P.visible(s["start"], s["end"])]
    if ins:
        avg = sum(s["dur"] for s in ins) / len(ins)
        sub.append((f"{len(ins)} 镜，平均 {avg:.1f} s" if zh else f"{len(ins)} shots, avg {avg:.1f} s"))
    if limit is not None:
        sub.append((f"虚线 = {limit:g} s（{limit_src}）" if zh else f"dashed = {limit:g} s ({limit_src})"))
    elif shots:
        sub.append("类型文档没有写回报间隔：用 --max N 标出过长的镜头" if zh else limit_src)
    if vis: sub.append((f"{len(vis)} 处问题" if zh else f"{len(vis)} issue(s)"))
    V.text(d, (pad, 76), V.fit(d, " · ".join(sub), V.font(22), W - 2 * pad), V.font(22), V.MUTED)

    # vertical grid
    y_top = head; y_bot = H - 86
    step = next(s for s in (0.5, 1, 2, 5, 10, 15, 30, 60, 120) if (T1 - T0) / s <= 20)
    t = (int(T0 / step) + (1 if T0 % step else 0)) * step
    while t <= T1 + 1e-9:
        x = P.x(t); d.line([(x, y_top), (x, y_bot)], fill=V.FAINT, width=1)
        V.text(d, (x, y_bot + 8), f"{t:g}", f_small, V.MUTED, "ma"); t += step

    y = head
    for name, h in lanes:
        V.text(d, (pad, y + (22 if name != "shots" else h - 60)), L[name], f_lane, V.INK)
        if name == "shots":
            if runs:   # segment ribbon on top
                for n, ss in runs:
                    if not P.visible(ss[0]["start"], ss[-1]["end"]): continue
                    xa, xb = P.x(ss[0]["start"]), P.x(ss[-1]["end"])
                    d.rectangle([xa, y - 12, xb - 1, y - 6], fill=colors[n])
                    if n and xb - xa > 30:
                        V.text(d, (xa + 2, y - 16), V.fit(d, n, V.font(24, bold=True), xb - xa - 4), V.font(24, bold=True), colors[n], "ld")
            base = y + h - 30; top = y + 36   # room for the length labels above the tallest bars
            cap_s = max([s["dur"] for s in ins] + [limit * 1.6 if limit else 0]) or 1
            scale = (base - top) / cap_s
            if limit is not None:
                V.dashed_hline(d, P.x0, P.x1, base - limit * scale, V.MUTED)
            for s in shots:
                if not P.visible(s["start"], s["end"]): continue
                xa, xb = P.x(s["start"]), P.x(s["end"])
                hh = min(s["dur"], cap_s) * scale
                col = V.RED if long(s) else colors[s["segment"]]
                d.rectangle([xa + 1, base - hh, max(xa + 2, xb - 1), base], fill=col)
                if long(s) or zoom:
                    V.text(d, ((xa + xb) / 2, base - hh - 4), f"{s['dur']:.1f}s", f_small, V.RED if long(s) else V.MUTED, "md")
                sid = s["id"] if s["unsure"] is None else s["id"] + "?"
                if zoom and xb - xa > V.tw(d, sid, f_small) + 6:
                    V.text(d, ((xa + xb) / 2, base + 6), sid, f_small, V.INK, "ma")
                elif xb - xa > V.tw(d, re.sub(r"^\D+", "", sid), f_tiny) + 2:
                    V.text(d, ((xa + xb) / 2, base + 6), re.sub(r"^\D+", "", sid), f_tiny, V.MUTED, "ma")
            d.line([(P.x0, base), (P.x1, base)], fill=V.RULE, width=1)
        elif name == "narration":
            for n in narr:
                block(d, P, n["start"], n["end"], y + 8, y + h - 8, NARR, NARR_EDGE, n["text"], f_small if zoom else f_tiny)
        elif name in ("captions", "onscreen"):
            items, rows = (caps, cap_rows) if name == "captions" else (ons, on_rows)
            for it in sorted(items, key=lambda i: i["ok"], reverse=True):   # the failing ones last, on top
                ry = y + 10 + 44 * rows[id(it)]
                block(d, P, it["start"], it["end"], ry, ry + 38, V.RED_SOFT if not it["ok"] else CAP,
                      V.RED if not it["ok"] else CAP_EDGE, it["text"], f_small if zoom else f_tiny, V.INK)
        elif name == "music":
            for i, s in enumerate(bm.get("sections", [])):
                block(d, P, float(s["start"]), float(s["end"]), y + 6, y + h - 34, SEC_A if i % 2 == 0 else SEC_B, SEC_EDGE,
                      s.get("name"), f_small if zoom else f_tiny)
            by = y + h - 30
            for b in bm.get("beats", []):
                if T0 <= b <= T1: x = P.x(b); d.line([(x, by), (x, by + 7)], fill=V.MUTED, width=1)
            for b in bm.get("downbeats", []):
                if T0 <= b <= T1: x = P.x(b); d.line([(x, by - 4), (x, by + 12)], fill=V.INK, width=2)
            label_end = -1e9
            for hit in sorted(bm.get("hits", []), key=lambda h: float(h.get("t", 0))):
                t = float(hit.get("t", 0))
                if not T0 <= t <= T1: continue
                x = P.x(t); kind = str(hit.get("kind", ""))
                col = V.MUTED if "no transient" in kind else V.AMBER
                d.polygon([(x - 7, by + 22), (x + 7, by + 22), (x, by + 12)], fill=col)
                if zoom and hit.get("what") and x + 9 > label_end:   # names only where they do not run into the last one
                    lab = V.fit(d, str(hit["what"]), f_tiny, 200)
                    V.text(d, (x + 9, by + 17), lab, f_tiny, V.MUTED, "lm"); label_end = x + 9 + V.tw(d, lab, f_tiny) + 8
            nh = sum(1 for hit in bm.get("hits", []) if T0 <= float(hit.get("t", 0)) <= T1)
            V.text(d, (pad, y + 58), f"{bm.get('bpm', '?'):g} bpm · {nh} {L['hits']}" if isinstance(bm.get("bpm"), (int, float)) else "", f_tiny, V.MUTED)
        elif name == "issues":
            rows_end, hidden = [-1e9] * 4, 0
            for t, msg, kind in vis:
                x = P.x(t); w = V.tw(d, msg, f_small)
                left = x + 16 + w > W - pad   # near the right edge: the label goes to the left of its mark
                x0 = x - 6 - w if left else x
                r = next((i for i in range(4) if rows_end[i] < x0 - 4), None)
                if r is None:
                    hidden += 1; continue
                yy = y + 8 + r * 32
                d.rectangle([x, yy + 4, x + 10, yy + 22], fill=V.RED)
                V.text(d, (x - 6, yy + 13) if left else (x + 16, yy + 13), msg, f_small, V.RED, "rm" if left else "lm")
                rows_end[r] = (x + 12) if left else (x + 16 + w + 12)
            if hidden:
                V.text(d, (W - pad, y + h - 4), (f"另有 {hidden} 处，见命令行输出" if zh else f"+{hidden} more: see the command output"),
                       f_tiny, V.RED, "rs")
        y += h + 22
    # footer: where each lane came from
    src = [f"{L['shots']}: shots.json" if shots else None,
           f"{L['narration']}: {V.shown(narr_src, project)}" if narr_src else None,
           f"{L['captions']}: {V.shown(cap_src, project)}" if cap_src else None,
           f"{L['onscreen']}: {V.shown(on_src, project)}" if on_src else None,
           f"{L['music']}: {V.shown(bm_src, project)}" if bm_src else None]
    V.text(d, (pad, H - 18), V.fit(d, " · ".join(x for x in src if x), V.font(17), W - 2 * pad), V.font(17), V.MUTED, "ls")
    if a.out:
        out = Path(a.out)
    else:
        tag = ("-" + "".join(c if c.isalnum() or V.is_cjk(c) else "-" for c in a.segment).strip("-")) if a.segment \
            else (f"-{T0:g}-{T1:g}s" if zoom else "")
        out = project / "out" / "check" / f"rhythm{tag}.png"
    V.save(img, out)
    print(f"rhythm: {V.shown(out)}  ({T0:.1f}–{T1:.1f} s; lanes: {', '.join(n for n, _ in lanes if n != 'issues')})")
    if limit is None and shots:
        print(f"  note: {limit_src}")
    for t, msg, _ in vis:
        print(f"  {t:7.2f}s  {msg}")
    if not vis:
        print("  no issues in this span")

if __name__ == "__main__":
    main()
