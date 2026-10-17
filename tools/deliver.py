"""The upload copy of a finished film: re-encoded to fit a platform's file-size limit, compared with the master.

usage (via bin/vh deliver): python tools/deliver.py <master.mp4> [--for bilibili,douyin,youtube] [--max-gb N] [--crf 16]
                                  [--preset medium] [--out f.mp4] [--psnr sample|full|off] [--samples 8]

A master render is made to be cut and patched (bin/vh render: CRF 16, sometimes 14), not uploaded: a 14-minute 4K master
was 10.4 GB, over Bilibili's web upload limit, and the platform re-encodes whatever it gets. This makes the copy to upload:
  - with --for or --max-gb, a ceiling worked out from the smallest file limit asked for (95 % of it, the sound's bit rate
    taken off). A master whose own bit rate is under it is encoded at --crf (16) with the ceiling as x264's VBV cap; one
    over it, in two passes at the ceiling's average bit rate, so the whole budget goes into the picture
  - without a limit, x264 at --crf (16): the master's quality in a file with fixed keyframes, tags and the moov first
  - a keyframe every 2 s exactly, yuv420p, limited range, BT.709 with all four tags, moov first; the sound and subtitle
    tracks copied as they are (sound that is not AAC becomes AAC 320 kb/s)
  - then it prints the size against each platform's limit and the PSNR against the master: --psnr sample (default) over
    --samples 2-second stretches spread over the film, full over every frame (a full decode of both; minutes for 4K), off
The limits (PLATFORMS below; playbook/10-hooks-and-packaging.md, 交付编码, has the sources and the date they were checked)
change: the upload page has the last word. Without --for or --max-gb there is no ceiling, only the table.
Writes <master stem>.upload.mp4 beside the master (--out another), and its record beside it, <copy>.deliver.json: the
copy and the master (paths relative to the record), their sizes and times, the arguments and when (bin/vh clean keeps
the copy and its master as the film, and says when a file is no longer the one recorded). Exit: 0 written and within every limit asked for ·
1 written but over a limit asked for, without the four colour tags, or the PSNR could not be measured · 2 could not start (no ffmpeg, not a video,
not enough disk).
"""
import argparse, glob, json, math, os, re, shutil, signal, subprocess, sys, time
from pathlib import Path

# name: (label, file limit in GB (10^9 bytes), length limit in s or None, source tag). playbook/10 §交付编码 cites them.
PLATFORMS = {
    "bilibili": ("Bilibili web", 8, None, "second-hand, 2026-10-12: web upload 8 GB, 16 GB at higher creator levels"),
    "douyin": ("Douyin web", 4, 15 * 60, "second-hand, 2026-10-12: 4 GB and 15 min from a computer"),
    "youtube": ("YouTube", 256, 12 * 3600, "official, checked 2026-10-12: 256 GB or 12 hours, whichever is less"),
}


def die(msg, code=2):
    print(f"deliver: {msg}", file=sys.stderr)
    sys.exit(code)


def probe(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(f)], capture_output=True, text=True)
    if r.returncode:
        die(f"{f}: {r.stderr.strip() or 'not a video ffprobe can read'}")
    return json.loads(r.stdout)


def fps_of(v):
    for k in ("r_frame_rate", "avg_frame_rate"):
        n, _, d = v.get(k, "0/0").partition("/")
        if int(d or 0) > 0 and 0 < int(n) / int(d) <= 240:
            return int(n) / int(d)
    return 30.0


def psnr(master, upload, spans, conv=""):
    """[(start, avg dB)] over 2-second stretches (spans: [(start, seconds)]), or one for the whole film. conv: the master
    goes through the same conversion as the copy first (a full-range master against a limited-range copy otherwise
    measures the range, not the encode)."""
    out = []
    for t0, d in spans:
        cmd = ["ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-nostdin"]   # the psnr summary is an info line
        cmd += (["-ss", f"{t0:.3f}", "-t", f"{d:.3f}"] if d else []) + ["-i", str(master)]
        cmd += (["-ss", f"{t0:.3f}", "-t", f"{d:.3f}"] if d else []) + ["-i", str(upload)]
        cmd += ["-lavfi", f"[0:v]{conv.rstrip(',') or 'null'}[m];[m][1:v]psnr", "-f", "null", "-"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r"PSNR .*average:(\S+)", r.stderr)
        if r.returncode or not m:
            return None
        out.append((t0, math.inf if m.group(1) == "inf" else float(m.group(1))))
    return out


def record(out, master):
    """<copy>.deliver.json beside the copy: what bin/vh clean keeps as the film. Sizes and times, not hashes: enough to see
    that a file was replaced, without reading gigabytes on every clean."""
    st, ms = out.stat(), master.stat()
    rec = {"tool": "bin/vh deliver", "output": out.name, "size": st.st_size, "mtime": round(st.st_mtime, 3),
           "master": os.path.relpath(master, out.parent), "master_size": ms.st_size, "master_mtime": round(ms.st_mtime, 3),
           "args": sys.argv[1:], "time": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    f = out.with_name(out.name + ".deliver.json"); tmp = f.with_name(f".{f.name}.{os.getpid()}")
    try:
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"); os.replace(tmp, f)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        print(f"deliver: could not write {f.name} ({e.strerror or e}): bin/vh clean will not know the copy is the film (--final it)", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(prog="bin/vh deliver", usage=__doc__.split("\n\n")[1].split("\n", 1)[0].replace("usage (via bin/vh deliver): python tools/deliver.py", "bin/vh deliver"))
    ap.add_argument("master")
    ap.add_argument("--for", dest="plat", default="", help="platforms whose limits the copy must fit: " + ", ".join(PLATFORMS) + " (comma-separated)")
    ap.add_argument("--max-gb", type=float, help="a file-size limit of your own, in GB (10^9 bytes)")
    ap.add_argument("--crf", type=float, default=16, help="the quality when the master fits the ceiling (default 16, bin/vh render's)")
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--out")
    ap.add_argument("--psnr", choices=["sample", "full", "off"], default="sample")
    ap.add_argument("--samples", type=int, default=8)
    a = ap.parse_args()
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"{tool} is not installed")
    master = Path(a.master).resolve()
    if not master.is_file():
        die(f"no such file: {a.master}")
    plats = [p.strip().lower() for p in a.plat.split(",") if p.strip()]
    if "all" in plats:
        plats = list(PLATFORMS)
    bad = [p for p in plats if p not in PLATFORMS]
    if bad:
        die(f"unknown platform {', '.join(bad)} (" + ", ".join(PLATFORMS) + ", or --max-gb)")
    info = probe(master)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if not v:
        die(f"{master.name} has no video")
    dur = float(info["format"].get("duration") or v.get("duration") or 0)
    if dur <= 0:
        die(f"{master.name}: no duration")
    fps, gop = fps_of(v), max(1, round(2 * fps_of(v)))
    audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
    # the sound's share of the budget: an AAC track as it is, anything else as the AAC 320 kb/s it becomes
    abps = sum((int(s.get("bit_rate") or 0) or 192000) if s.get("codec_name") == "aac" else 320000 for s in audio)
    for p in plats:   # a length limit cannot be met by encoding: say it before the encode
        secs = PLATFORMS[p][2]
        if secs and dur > secs:
            print(f"deliver: {dur / 60:.1f} min is over {PLATFORMS[p][0]}'s {secs // 60:g} min ({PLATFORMS[p][3]}): the copy will not upload there", file=sys.stderr)
    limits = [(p, PLATFORMS[p][1]) for p in plats] + ([("--max-gb", a.max_gb)] if a.max_gb else [])
    cap_gb = min((g for _, g in limits), default=None)
    maxrate = None
    if cap_gb:
        maxrate = int(cap_gb * 1e9 * 0.95 * 8 / dur - abps)
        if maxrate < 500_000:
            die(f"{cap_gb:g} GB for {dur / 60:.1f} min leaves {max(0, maxrate) / 1e6:.2f} Mb/s for the picture: too little; cut the film or allow more")
    out = Path(a.out).resolve() if a.out else master.with_name(master.stem + ".upload.mp4")
    if out == master:
        die("--out is the master itself")
    if not out.parent.is_dir():
        die(f"no folder {out.parent} for --out")
    # the disk: the copy is at most the ceiling, else about the master's size
    need = min(master.stat().st_size, cap_gb * 1e9 if cap_gb else math.inf) * 1.1
    free = shutil.disk_usage(out.parent).free
    if need > free:
        die(f"about {need / 1e9:.1f} GB needed for {out.name}, {free / 1e9:.1f} GB free on that disk")
    col = (v.get("pix_fmt"), v.get("color_range"), v.get("color_space"))
    # the four tags are set on the frames (setparams), as bin/vh render does: the encoder's own options lose to what the
    # decoded frames carry. A master that is not limited-range BT.709 yuv420p (a JPEG pipe's yuvj420p) is converted first
    tags = "setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv"
    conv = ""
    if col != ("yuv420p", "tv", "bt709"):
        # the matrix as tagged; untagged full-range video (yuvj420p from a JPEG pipe) is BT.601, as JPEG is
        jpeg = v.get("color_range") == "pc" or str(v.get("pix_fmt", "")).startswith("yuvj")
        bt601 = v.get("color_space") in ("bt470bg", "smpte170m") or (jpeg and v.get("color_space") in (None, "", "unknown"))
        conv = (f"scale=in_color_matrix={'bt601' if bt601 else 'bt709'}:in_range="
                f"{'pc' if v.get('color_range') == 'pc' or str(v.get('pix_fmt', '')).startswith('yuvj') else 'tv'}:out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,")
    vf = ["-vf", conv + tags]
    subs = [s for s in info["streams"] if s["codec_type"] == "subtitle"]
    scodec = ["-c:s", "copy"] if all(s.get("codec_name") == "mov_text" for s in subs) else ["-c:s", "mov_text"]   # SRT/ASS from an MKV: as MP4 text
    acodec = [] if not audio else (["-c:a", "copy"] if all(s.get("codec_name") == "aac" for s in audio) else ["-c:a", "aac", "-b:a", "320k"])
    # rate: the master's own bit rate fits under the ceiling (or there is none): CRF, with the ceiling as a VBV cap. It does
    # not: two passes at the ceiling's average, which spends the whole budget where the pictures need it (one pass under a
    # VBV cap leaves part of it unused: 64 of 72 Mb/s on a 4K test, 1 dB lower)
    vbps = int(v.get("bit_rate") or 0) or int(master.stat().st_size * 8 / dur - abps)
    two = bool(maxrate) and vbps > maxrate
    if maxrate and not two and maxrate > 2 * vbps:
        maxrate = None   # the master's rate is far under the ceiling: CRF alone fits (and x264 takes no VBV over 2^31 b/s)
    elif maxrate:
        maxrate = min(maxrate, 600_000_000)   # VBV numbers stay inside x264's int range (bufsize up to 3x this)
    head = ["ffmpeg", "-v", "error", "-stats", "-nostdin", "-y", "-i", str(master)]
    venc = ["-c:v", "libx264", "-preset", a.preset, "-g", str(gop), "-keyint_min", str(gop), "-sc_threshold", "0", *vf, "-pix_fmt", "yuv420p",
            "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    rate = (["-b:v", str(maxrate), "-maxrate", str(int(maxrate * 1.5)), "-bufsize", str(3 * maxrate)] if two
            else ["-crf", f"{a.crf:g}", *(["-maxrate", str(maxrate), "-bufsize", str(2 * maxrate)] if maxrate else [])])
    part = out.with_name(f".{out.name}.{os.getpid()}.part.mp4")   # this run's own: two delivers never share a file
    log = str(out.with_name(f".{out.name}.{os.getpid()}.x264"))
    final = [*head, "-map", "0:v:0", "-map", "0:a?", "-map", "0:s?", *venc, *rate, *(["-pass", "2", "-passlogfile", log] if two else []),
             *acodec, *scodec, "-map_metadata", "0", "-movflags", "+faststart", str(part)]
    how = (f"two passes at {maxrate / 1e6:.1f} Mb/s for the picture (the master's {vbps / 1e6:.1f} does not fit {cap_gb:g} GB)" if two else
           f"crf {a.crf:g}" + (f", at most {maxrate / 1e6:.1f} Mb/s for the picture (to fit {cap_gb:g} GB)" if maxrate
                                else f" (the master's {vbps / 1e6:.1f} Mb/s fits {cap_gb:g} GB with room)" if cap_gb else ", no size ceiling"))
    print(f"deliver: {master.name} · {v['width']}x{v['height']} · {fps:g} fps · {dur / 60:.1f} min · {master.stat().st_size / 1e9:.2f} GB"
          f" → x264 {a.preset}, {how}, keyframe every {gop}")
    r = None
    def stop(sig, _frame):   # SIGTERM (a timeout) as Ctrl-C: subprocess.run then stops ffmpeg, and the files below go
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        if two:
            r = subprocess.run([*head, "-map", "0:v:0", *venc, *rate, "-pass", "1", "-passlogfile", log, "-an", "-f", "null", "-"])
        if not (r and r.returncode):
            r = subprocess.run(final)
    except KeyboardInterrupt:
        r = None
    finally:   # this run's pass logs and part file, whatever happened (Ctrl-C too)
        for f in out.parent.glob(glob.escape(f".{out.name}.{os.getpid()}.") + "*"):
            if f != part or r is None or r.returncode: f.unlink(missing_ok=True)
    if r is None:
        die("stopped; the part file is deleted", 130)
    if r.returncode:
        die(f"ffmpeg failed (exit {r.returncode})", 1)
    os.replace(part, out)
    size = out.stat().st_size
    record(out, master)
    print(f"  {out.name}: {size / 1e9:.2f} GB, {size * 8 / dur / 1e6:.1f} Mb/s on average (the master: {master.stat().st_size * 8 / dur / 1e6:.1f})")
    u = next((s for s in probe(out)["streams"] if s["codec_type"] == "video"), {})
    tags = tuple(u.get(k) for k in ("pix_fmt", "color_range", "color_space", "color_transfer", "color_primaries"))
    over = tags != ("yuv420p", "tv", "bt709", "bt709", "bt709")
    print(f"  {'✗' if over else '✓'} colour: {', '.join(str(x) for x in tags)}")
    for p, (label, gb, secs, src) in PLATFORMS.items():
        fits = size <= gb * 1e9 and (secs is None or dur <= secs)
        asked = p in plats
        over = over or (asked and not fits)
        mark = ("✓" if fits else "✗") if asked else ("·" if fits else "!")
        print(f"  {mark} {label:<13} {gb:>4g} GB{f', {secs // 60:g} min' if secs else '':<9} {'fits' if fits else 'too big' if size > gb * 1e9 else 'too long'}   ({src})")
    if a.max_gb:
        fits = size <= a.max_gb * 1e9
        over = over or not fits
        print(f"  {'✓' if fits else '✗'} --max-gb      {a.max_gb:>4g} GB          {'fits' if fits else 'too big'}")
    bad_psnr = False
    if a.psnr != "off":
        if a.psnr == "full":
            spans = [(0.0, 0)]
        else:
            n = max(1, a.samples)
            spans = [((dur - 2) * (k + 0.5) / n, 2.0) for k in range(n)] if dur > 4 else [(0.0, 0)]
        got = psnr(master, out, spans, conv)
        if got is None:
            bad_psnr = True
            print("  PSNR against the master: could not be measured (ffmpeg's psnr filter failed)")
        else:
            vals = [x for _, x in got]
            worst = min(got, key=lambda x: x[1])
            what = "every frame" if a.psnr == "full" or len(spans) == 1 else f"{len(spans)} stretches of 2 s"
            fin = [x for x in vals if x != math.inf]
            if not fin:
                print(f"  PSNR against the master ({what}): the same pictures (infinite)")
            else:
                print(f"  PSNR against the master ({what}): {sum(fin) / len(fin):.1f} dB on average" + (f", the lowest stretch {worst[1]:.1f} dB (at {worst[0]:.0f} s)" if len(got) > 1 else ""))
    if over:
        print("deliver: over a limit asked for: lower --crf's quality (a higher number) or allow more, and check the upload page")
    sys.exit(1 if over or bad_psnr else 0)


if __name__ == "__main__":
    main()
