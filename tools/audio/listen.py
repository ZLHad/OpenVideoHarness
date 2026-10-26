"""bin/vh qa … --listen [N] and --picture: where a person should put headphones on, and the sound as one picture. A
machine finds silence, clicks and pumping (bin/vh qa); whether the weakest line can still be heard over the music, or
the loudest hit is too much, takes a person, and these are the places to send one. Numpy (bin/vh adds it), and ffmpeg;
--picture also needs pillow.

usage: bin/vh qa <mix> [beats.json] [events.json] --listen [N] [--stems DIR] [--timeline t.json] [--out DIR] [--gate G]
                  [--picture f.png] [--cuts film.mp4.render.json|shots.json] [--json]
<mix>: anything ffmpeg decodes (the muxed mp4 too). --stems DIR: the buses bin/vh mix … stems=DIR wrote (voice.wav,
music.wav, sfx.wav); --timeline: the narration's lines (default the project's audio/timeline.<lang>.json beside the mix).

  --listen N (default 5): N places, each a 6 s excerpt in --out (default out/listen/ of the mix's project, else beside
  it) as NN-<why>.wav, and listen.json ({"version": 1, "mix", "points": [{"n", "t", "why", "note", "file", "detail"}]}):
    weakest-line   the narration line with the lowest voice-to-music ratio (needs --stems and a timeline)
    loudest-hit    the loudest 400 ms of the effects bus (--stems), else of the whole mix
    biggest-turn   the section boundary (beats.json's sections) the level changes most across, else the biggest 3 s jump
    ending         the last 6 s
    aac-risk       the highest sample peak of the mix: where an AAC encode overshoots first, and clips on a phone
  past 5, more of the weakest lines. Two places within 3 s of each other are one (the next candidate is taken).
  --gate G: put them into out/review/gate-G.json: "listen" (the points, which the review desk lists) and the excerpts
  as "assets" (the review page plays them); what was there under listen and those paths is replaced.
  --picture f.png: the whole mix on one time axis, in the manner of earshot: a spectrogram (log frequency), the
  narration's lines and the events (events.json) as labels, the momentary loudness (400 ms) against −14 LUFS, and the
  cuts (a film's .render.json shots, or shots.json) as lines, with the listen points marked when given.
Exit: 0 · 2 usage: no mix, a file named that is not there, a gate JSON that cannot be read.
"""
import argparse, json, math, os, subprocess, sys
from pathlib import Path

import numpy as np

SR = 48000
CLIP = 6.0


def decode(path, sr=SR, mono=True):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1" if mono else "2", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype="<f4").astype(np.float64)
    return x if mono else x.reshape(-1, 2)


def db(x):
    return 20 * math.log10(max(float(x), 1e-9))


def rms(x):
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def windows(x, win, hop):
    """RMS (dB) of windows of win s every hop s → (times of their centres, levels)."""
    w, h = int(win * SR), int(hop * SR)
    if len(x) < w:
        return np.array([len(x) / SR / 2]), np.array([db(rms(x))])
    n = 1 + (len(x) - w) // h
    c = np.cumsum(np.concatenate([[0.0], x ** 2]))
    e = (c[w + np.arange(n) * h] - c[np.arange(n) * h]) / w
    return (np.arange(n) * h + w / 2) / SR, 10 * np.log10(np.maximum(e, 1e-18))


def kweight(x):
    """BS.1770's K-weighting (its two biquads at 48 kHz, the coefficients pyloudnorm derives), for --picture's momentary
    loudness. Without scipy, unweighted (said)."""
    try:
        from scipy.signal import lfilter
    except ImportError:
        print("  (no scipy: the loudness curve is unweighted RMS)", file=sys.stderr)
        return x
    f0, g, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = math.tan(math.pi * f0 / SR)
    vh = 10 ** (g / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    b1, a1 = [(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0], [1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    f0, q = 38.13547087602444, 0.5003270373238773
    k = math.tan(math.pi * f0 / SR)
    a0 = 1 + k / q + k * k
    b2, a2 = [1.0, -2.0, 1.0], [1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    return lfilter(b2, a2, lfilter(b1, a1, x))


def timeline_of(mix, arg):
    if arg:
        return Path(arg)
    for d in [Path(mix).resolve().parent] + list(Path(mix).resolve().parents)[:3]:
        hits = sorted(d.glob("audio/timeline.*.json")) + sorted(d.glob("timeline.*.json"))
        if hits:
            return hits[0]
    return None


def lines_of(tl):
    try:
        d = json.loads(Path(tl).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = d.get("lines", d) if isinstance(d, dict) else d
    out = []
    for i, r in enumerate(rows if isinstance(rows, list) else []):
        if isinstance(r, dict) and isinstance(r.get("start"), (int, float)) and isinstance(r.get("end"), (int, float)) and r["end"] > r["start"]:
            out.append({"id": str(r.get("id", i + 1)), "start": float(r["start"]), "end": float(r["end"]), "text": str(r.get("text") or r.get("zh") or r.get("en") or "")})
    return out


def project_of(p):
    for d in [Path(p).resolve().parent] + list(Path(p).resolve().parents):
        if (d / "BRIEF.md").is_file():
            return d
    return None


def candidates(mix, x, beats, stems, lines):
    """{why: [(t, note, detail), …]} best first."""
    dur = len(x) / SR
    out = {}
    if stems and lines:
        v, m = decode(stems / "voice.wav"), decode(stems / "music.wav")
        rows = []
        for ln in lines:
            a, b = int(ln["start"] * SR), int(ln["end"] * SR)
            vr, mr = rms(v[a:b]), rms(m[a:b])
            if vr > 0:
                rows.append((db(vr) - db(mr), ln))
        rows.sort(key=lambda r: r[0])
        out["weakest-line"] = [((ln["start"] + ln["end"]) / 2, f"line {ln['id']}: the voice {vmr:.1f} dB over the music: can every word be heard?",
                                {"line": ln["id"], "vmr_db": round(vmr, 1), "text": ln["text"][:80]}) for vmr, ln in rows]
    src = decode(stems / "sfx.wav") if stems and (stems / "sfx.wav").is_file() else x
    t, lv = windows(src, 0.4, 0.1)
    out["loudest-hit"] = [(float(t[i]), f"the loudest 400 ms of {'the effects' if src is not x else 'the mix'} ({lv[i]:.1f} dBFS RMS): too much?",
                           {"rms_db": round(float(lv[i]), 1)}) for i in apart(t, lv) if lv[i] > lv.max() - 12 and lv[i] > -80]
    secs = [s for s in (beats or {}).get("sections") or [] if isinstance(s, dict) and isinstance(s.get("start"), (int, float)) and s["start"] > 1]
    rows = []
    if secs:
        for s in secs:
            a = int(s["start"] * SR)
            before, after = db(rms(x[max(0, a - 2 * SR):a])), db(rms(x[a:a + 2 * SR]))
            rows.append((abs(after - before), float(s["start"]), f"into {s.get('name', 'a section')}: {after - before:+.1f} dB across the turn"))
    else:
        t3, l3 = windows(x, 3.0, 0.5)
        for i in range(len(l3) - 6):
            rows.append((abs(l3[i + 6] - l3[i]), float(t3[i] + 1.5), f"{l3[i + 6] - l3[i]:+.1f} dB within 3 s"))
    rows.sort(key=lambda r: -r[0])
    out["biggest-turn"] = [(tt, f"the biggest change in level ({note}): does it feel meant?", {"delta_db": round(d, 1)}) for d, tt, note in rows[:20]]
    out["ending"] = [(max(0.0, dur - CLIP / 2), "the ending: does the music land, and the last word stay clear?", {"duration": round(dur, 3)})]
    w = int(0.01 * SR)
    n10 = max(1, len(x) // w)
    peaks = np.abs(x[:n10 * w]).reshape(n10, w).max(axis=1) if len(x) >= w else np.array([float(np.max(np.abs(x))) if len(x) else 0.0])
    t2 = (np.arange(len(peaks)) + 0.5) * 0.01
    out["aac-risk"] = [(float(t2[i]), f"the highest peak ({db(peaks[i]):.1f} dBFS): an AAC encode overshoots here first; listen on the upload too",
                        {"peak_dbfs": round(db(peaks[i]), 1)}) for i in apart(t2, peaks) if peaks[i] > 0.5 * peaks.max() > 0]
    return out


def apart(t, v, gap=3.0, n=20):
    """The indices of the highest values, at least gap s apart (one per event, not twenty of the same hit)."""
    out = []
    for i in np.argsort(-np.asarray(v)):
        if all(abs(t[i] - t[j]) >= gap for j in out):
            out.append(int(i))
            if len(out) >= n:
                break
    return out


def choose(cands, n, dur, gap=2.0):
    """One place of each kind (the ending first: it is where it is), then more of the weakest lines, up to n. A kind whose
    best place falls within gap s of one chosen already is said on that one, not swapped for a worse place."""
    order = ["ending", "weakest-line", "loudest-hit", "biggest-turn", "aac-risk"]
    picked = []
    def near(t):
        return next((p for p in picked if abs(t - p["t"]) < gap), None)
    for why in order:
        cs = cands.get(why, [])
        if not cs:
            continue
        t, note, detail = cs[0]
        hit = near(t)
        if hit is None:
            picked.append({"t": round(min(max(t, 0.0), dur), 3), "why": why, "note": note, "detail": detail})
        else:
            hit["note"] += f"; and {why}: {note}"
            hit.setdefault("also", []).append({"why": why, "t": round(t, 3), "detail": detail})
    for t, note, detail in cands.get("weakest-line", [])[1:]:
        if len(picked) >= n:
            break
        if near(t) is None:
            picked.append({"t": round(t, 3), "why": "weakest-line", "note": note, "detail": detail})
    return sorted(picked[:n], key=lambda p: p["t"])


def excerpt(mix, t, dest):
    a = max(0.0, t - CLIP / 2)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{CLIP:.3f}", "-i", str(mix), "-vn", "-af",
                    f"afade=t=in:d=0.02,afade=t=out:st={CLIP - 0.02:.3f}:d=0.02", "-c:a", "pcm_s16le", str(dest)], check=True)


def cuts_of(arg):
    if not arg:
        return []
    try:
        d = json.loads(Path(arg).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    shots = d.get("shots") if isinstance(d, dict) else d
    return sorted({float(s["start"]) for s in shots or [] if isinstance(s, dict) and isinstance(s.get("start"), (int, float)) and s["start"] > 0})


def events_of(arg):
    if not arg:
        return []
    try:
        d = json.loads(Path(arg).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    ev = d.get("events") if isinstance(d, dict) else d
    return [(float(e["t"]), str(e.get("sfx", "?"))) for e in ev or [] if isinstance(e, dict) and isinstance(e.get("t"), (int, float))]


def picture(x, dest, lines, events, cuts, points):
    from PIL import Image, ImageDraw
    dur = len(x) / SR
    W, Hs, Hl, Hm = 1600, 300, 90, 160
    img = Image.new("RGB", (W, Hs + Hl + Hm + 30), (250, 250, 248))
    d = ImageDraw.Draw(img)
    sr2 = 16000
    y = x[::SR // sr2] if SR % sr2 == 0 else x
    nfft, hop = 1024, max(1, int(len(y) / W))
    if len(y) > nfft:
        frames = np.lib.stride_tricks.sliding_window_view(y, nfft)[::hop] * np.hanning(nfft)
        spec = 20 * np.log10(np.abs(np.fft.rfft(frames, axis=1)) + 1e-9)
        freqs = np.fft.rfftfreq(nfft, 1 / sr2)
        rows = np.geomspace(40, sr2 / 2, Hs)
        idx = np.clip(np.searchsorted(freqs, rows), 0, len(freqs) - 1)
        s = spec[:, idx].T[::-1]
        top = np.percentile(s, 99.5)
        s = np.clip((s - (top - 70)) / 70, 0, 1)
        col = (255 * (1 - s)).astype(np.uint8)
        im = Image.fromarray(col, "L").resize((W, Hs))
        img.paste(Image.merge("RGB", (im, im, im)), (0, 0))
    xt = lambda t: int(t / max(dur, 1e-9) * (W - 1))   # noqa: E731
    yl = Hs
    for ln in lines:
        d.rectangle([xt(ln["start"]), yl + 8, max(xt(ln["start"]) + 1, xt(ln["end"])), yl + 26], fill=(70, 110, 180))
    for t, name in events:
        d.line([xt(t), yl + 32, xt(t), yl + Hl - 6], fill=(200, 90, 30), width=1)
        d.text((xt(t) + 2, yl + 34 + (hash(name) % 3) * 16), name[:14], fill=(160, 70, 20))
    ym = Hs + Hl
    t4, l4 = windows(kweight(x), 0.4, max(0.05, dur / W))
    lufs = l4 - 0.691
    to_y = lambda v: int(ym + Hm - 10 - (min(max(v, -40), 0) + 40) / 40 * (Hm - 20))   # noqa: E731
    d.line([0, to_y(-14), W, to_y(-14)], fill=(160, 160, 160), width=1)
    d.text((4, to_y(-14) - 14), "-14 LUFS", fill=(120, 120, 120))
    pts = [(xt(t), to_y(v)) for t, v in zip(t4, lufs)]
    if len(pts) > 1:
        d.line(pts, fill=(30, 30, 30), width=1)
    for c in cuts:
        d.line([xt(c), 0, xt(c), Hs + Hl + Hm], fill=(40, 160, 80), width=1)
    for p in points or []:
        d.line([xt(p["t"]), ym, xt(p["t"]), ym + Hm], fill=(220, 30, 60), width=2)
        d.text((xt(p["t"]) + 3, ym + 2), p["why"], fill=(220, 30, 60))
    for k in range(0, int(dur) + 1, max(1, int(dur // 12) or 1)):
        d.text((xt(k), Hs + Hl + Hm + 8), f"{k // 60}:{k % 60:02d}", fill=(80, 80, 80))
    img.save(dest)


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh qa … --listen", description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", help="<mix> [beats.json] [events.json]")
    ap.add_argument("--listen", nargs="?", type=int, const=5)
    ap.add_argument("--stems")
    ap.add_argument("--timeline")
    ap.add_argument("--out")
    ap.add_argument("--gate")
    ap.add_argument("--picture")
    ap.add_argument("--cuts")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    mix = Path(a.files[0])
    if not mix.is_file():
        print(f"bin/vh qa: no such mix: {mix}", file=sys.stderr)
        return 2
    beats = events = None
    for f in a.files[1:]:
        if not Path(f).is_file():
            print(f"bin/vh qa: no such file: {f}", file=sys.stderr)
            return 2
        try:
            j = json.loads(Path(f).read_text(encoding="utf-8"))
        except ValueError as e:
            print(f"bin/vh qa: {f}: not JSON ({e})", file=sys.stderr)
            return 2
        if isinstance(j, dict) and ("beats" in j or "sections" in j):
            beats = j
        else:
            events = f
    stems = Path(a.stems) if a.stems else None
    if stems and not (stems / "voice.wav").is_file():
        print(f"bin/vh qa: --stems {stems}: no voice.wav there (bin/vh mix … stems=DIR writes it)", file=sys.stderr)
        return 2
    tl = timeline_of(mix, a.timeline)
    lines = lines_of(tl) if tl else []
    x = decode(mix)
    if not len(x):
        print(f"bin/vh qa: {mix}: no sound ffmpeg can read", file=sys.stderr)
        return 2
    dur = len(x) / SR
    out = {"version": 1, "tool": "bin/vh qa --listen", "mix": str(mix), "duration": round(dur, 3), "points": []}
    log = sys.stderr if a.json else sys.stdout
    if a.listen:
        cands = candidates(mix, x, beats, stems, lines)
        pts = choose(cands, a.listen, dur)
        proj = project_of(mix)
        od = Path(a.out) if a.out else (proj / "out" / "listen" if proj else mix.with_name(mix.stem + ".listen"))
        od.mkdir(parents=True, exist_ok=True)
        for k, p in enumerate(pts, 1):
            f = od / f"{k:02d}-{p['why']}.wav"
            excerpt(mix, p["t"], f)
            p["n"], p["file"] = k, (os.path.relpath(f, proj) if proj else str(f))
        out["points"] = pts
        (od / "listen.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"qa --listen: {len(pts)} place(s) to hear with headphones, {CLIP:g} s each → {od}" + ("" if stems else " (no --stems: the weakest line is not chosen)"), file=log)
        for p in pts:
            print(f"  {p['n']}. {p['t']:7.2f} s  {p['why']:<13} {p['note']}", file=log)
        if a.gate:
            if not proj:
                print("bin/vh qa: --gate: the mix is not in a project", file=sys.stderr)
                return 2
            g = proj / "out" / "review" / f"gate-{a.gate}.json"
            try:
                gj = json.loads(g.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                print(f"bin/vh qa: --gate {a.gate}: {g} cannot be read ({e})", file=sys.stderr)
                return 2
            files = {p["file"] for p in pts}
            gj["listen"] = [{"t": p["t"], "note": f"{p['why']}: {p['note']}"} for p in pts]
            gj["assets"] = [x_ for x_ in gj.get("assets") or [] if not (isinstance(x_, dict) and str(x_.get("path", "")).startswith(os.path.relpath(od, proj)))] \
                + [{"path": p["file"], "caption": f"{p['n']}. {p['t']:.1f} s · {p['why']}: {p['note']}"} for p in pts if p["file"] in files]
            tmp = g.with_name(f".{g.name}.{os.getpid()}")
            tmp.write_text(json.dumps(gj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            os.replace(tmp, g)
            print(f"  into {os.path.relpath(g, proj)}: listen ({len(pts)}) and the excerpts as assets (bin/vh review {proj.name} {a.gate})", file=log)
    if a.picture:
        try:
            picture(x, a.picture, lines, [] if not events else events_of(events), cuts_of(a.cuts), out["points"])
        except ImportError:
            print("bin/vh qa --picture needs pillow (bin/vh adds it)", file=sys.stderr)
            return 2
        out["picture"] = a.picture
        print(f"qa --picture: {a.picture} (spectrogram, lines and events, momentary loudness against −14 LUFS, cuts)", file=log)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
