"""The cut page and the note box on a long film, in a real headless Chrome (tools/ci.sh's console group; not a bin/vh command).

usage: python3 tools/desk/test_cut_page.py [<chrome>]

A made-up 12:20 film is built in a temp folder from tools/desk/fixtures/demo: 60 shots in nine parts, about 180 lines, gate ③
with 67 marked places (30 the agent is unsure of, 30 to listen to, 7 the check found), gate ② cut into sheets of six as an
agent writes it ("开场（1/2）"), and the same film again cut from an edit list whose render kept the shots inside each part.
The picture is ffmpeg's test pattern, 64×36 at 5 frames a second (a few hundred KB). A desk of its own serves them (a temp
HOME and every Studio folder in the temp folder, no window, no browser, no keychain), and test_cut_page.mjs drives the
pages through the DevTools protocol with real mouse and key events. Prints nothing and exits 0 when every check holds;
else one line a failure, exit 1. Exit 3: no ffmpeg; 4: no Chrome (CHROME_PATH, the usual installs, Playwright's Chromium, as bin/vh's
chrome_path looks; the caller skips, or on CI fails).
"""
import json, os, random, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
D = 740.0
PARTS = ["开场", "两个鼓包", "转一圈", "大潮小潮", "海湾放大", "潮汐表", "历史", "今天的港口", "结尾"]
NAMES = ["PROLOGUE", "BULGES", "TURN", "SPRING", "BAY", "TABLE", "HISTORY", "PORT", "END"]


def film(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=s=64x36:r=5:d={D:g}", "-f", "lavfi",
                        "-i", f"sine=f=330:sample_rate=8000:d={D:g}", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "40", "-g", "5",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "16k", "-shortest", str(path)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg: {r.stderr.strip()[:300]}")


def long_film(root, mp4):
    p = root / "2026-11-20-long-tide"
    shutil.copytree(HERE / "fixtures/demo", p)
    R = random.Random(7)
    cuts = sorted(R.uniform(3, D - 3) for _ in range(59))
    bounds = [0.0] + [round(c, 2) for c in cuts] + [D]
    shots = [{"id": f"S{i + 1}", "segment": PARTS[min(8, i * 9 // 60)], "start": bounds[i], "end": bounds[i + 1], "label": f"第 {i + 1} 镜",
              "frame": f"out/frames/S{i % 6 + 1}.svg", "reads": [f"读点 {i + 1}"]} for i in range(60)]
    rows = []
    for k, seg in enumerate(PARTS):
        ss = [x for x in shots if x["segment"] == seg]
        rows.append(f"| {k + 1} | {seg} | {ss[0]['start']:.0f}–{ss[-1]['end']:.0f} s | 看懂{seg} | {seg}的画面 |")
    b = (p / "BRIEF.md").read_text(encoding="utf-8").replace("- Output: 1920x1080, 30 fps, about 32 s", "- Output: 320x180, 30 fps, 12:20")
    b = re.sub(r"(\|---\|---\|---\|---\|---\|\n)(?:\|.*\n)+", lambda m: m.group(1) + "\n".join(rows) + "\n", b)
    (p / "BRIEF.md").write_text(b, encoding="utf-8")
    (p / "shots.json").write_text(json.dumps({"shots": shots}, ensure_ascii=False), encoding="utf-8")
    segs, t, n = [], 0.4, 0
    while t < D - 4:
        n += 1
        d = R.uniform(2.0, 5.0)
        segs.append({"id": f"L{n}", "start": round(t, 2), "end": round(t + d, 2), "text": f"第 {n} 句旁白。"})
        t += d + R.uniform(0.3, 0.9)
    (p / "audio/timeline.zh.json").write_text(json.dumps({"version": 1, "lang": "zh", "provider": "fixture", "segments": segs}, ensure_ascii=False), encoding="utf-8")
    g = json.loads((p / "out/review/gate-3.json").read_text(encoding="utf-8"))
    g.update(film="out/draft.mp4", least_sure=[{"id": shots[k]["id"], "t": round(shots[k]["start"] + 0.5, 1), "note": f"没把握 {k}"} for k in range(0, 60, 2)],
             listen=[{"t": round(10 + j * 24.1, 1), "note": f"请听 {j}"} for j in range(30)])
    (p / "out/review/gate-3.json").write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    c = json.loads((p / "out/check/draft.check.json").read_text(encoding="utf-8"))
    c["findings"] = [{"kind": "textcheck", "severity": "warn", "message": f"字压在亮处 {j}", "t": round(30 + j * 97.3, 1), "t1": round(32 + j * 97.3, 1)} for j in range(7)]
    (p / "out/check/draft.check.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    g2 = json.loads((p / "out/review/gate-2.json").read_text(encoding="utf-8"))
    sheets = []
    for k, seg in enumerate(PARTS):
        ss = [x for x in shots if x["segment"] == seg]
        ch = [ss[i:i + 6] for i in range(0, len(ss), 6)]
        sheets += [{"id": f"P{k + 1}-{j + 1}", "title": seg + (f"（{j + 1}/{len(ch)}）" if len(ch) > 1 else ""), "t0": c0[0]["start"], "t1": c0[-1]["end"],
                    "shots": [{"id": x["id"], "t0": x["start"], "t1": x["end"], "frame": x["frame"], "see": x["label"]} for x in c0]} for j, c0 in enumerate(ch)]
    g2["segments"] = sheets
    (p / "out/review/gate-2.json").write_text(json.dumps(g2, ensure_ascii=False), encoding="utf-8")
    shutil.copy(mp4, p / "out/draft.mp4")
    return p, shots, len(sheets)


def edit_film(root, src, shots):
    """The same film from an edit list of nine parts; its render record keeps each part's shots (<part>.<shot>), as render.mjs writes them."""
    import hashlib
    p = root / "2026-11-21-long-tide-edit"
    shutil.copytree(src, p)
    (p / "shots.json").unlink()
    parts = [[x for x in shots if x["segment"] == seg] for seg in PARTS]
    entries = [{"id": NAMES[k], "src": "black", "end": ss[-1]["end"], "segment": PARTS[k], "label": PARTS[k]} for k, ss in enumerate(parts)]
    entries[-1].pop("end")
    entries[-1]["dur"] = round(D - parts[-1][0]["start"], 3)
    (p / "edit.json").write_text(json.dumps({"v": 1, "fps": 30, "size": [320, 180], "sources": {"black": {"color": "#000000"}},
                                             "tracks": [{"id": "V1", "entries": entries}]}, ensure_ascii=False), encoding="utf-8")
    sha = hashlib.sha256((p / "edit.json").read_bytes()).hexdigest()
    rec = [{"id": NAMES[k], "start": ss[0]["start"], "end": ss[-1]["end"], "kind": "color"} for k, ss in enumerate(parts)]
    rec += [{"id": f"{NAMES[k]}.S{k + 1}_{j + 1}", "start": x["start"], "end": x["end"], "kind": "shot"} for k, ss in enumerate(parts) for j, x in enumerate(ss)]
    (p / "out/draft.mp4.render.json").write_text(json.dumps({"fps": 30, "frames": int(D * 30), "first_frame": 0, "edit": {"path": "edit.json", "sha256": sha}, "shots": rec}), encoding="utf-8")
    return p


def find_chrome():
    """The Chrome bin/vh's chrome_path would take: CHROME_PATH, the system installs, then Playwright's Chromium builds, newest first."""
    for p in (os.environ.get("CHROME_PATH", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/usr/bin/google-chrome",
              "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    for d in (os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""), str(Path.home() / ".cache/ms-playwright")):
        if d and os.path.isdir(d):
            for n in sorted((int(m.group(1)) for m in (re.fullmatch(r"chromium-(\d+)", x) for x in os.listdir(d)) if m), reverse=True):
                for p in (f"{d}/chromium-{n}/chrome-linux64/chrome", f"{d}/chromium-{n}/chrome-linux/chrome"):
                    if os.access(p, os.X_OK):
                        return p
    return None


def main(argv):
    if len(argv) > 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    chrome = argv[0] if argv else find_chrome()
    if not chrome:
        return 4
    if not shutil.which("ffmpeg"):
        return 3
    t = Path(tempfile.mkdtemp(prefix="vh-cut-page."))
    desk = None
    try:
        env = dict(os.environ)
        for k in ("HOME", "TMPDIR", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "OVH_STUDIO_PROFILES", "OVH_STUDIO_SHELL_PROFILE", "OVH_STUDIO_SHELL_CACHE", "OVH_AGENTS_DIR"):
            (t / k.lower()).mkdir()
            env[k] = str(t / k.lower())
        root = t / "root"
        root.mkdir()
        env.update(OVH_PROJECTS=str(root), OVH_LOCAL_MD="/dev/null/LOCAL.md", OVH_STUDIO_SHELL="none", OVH_STUDIO_BROWSER="none", OVH_GATE_STUDIO="0",
                   OVH_KEYSTORE="none", BROWSER="/usr/bin/true")
        film(t / "film.mp4")
        p, shots, sheets = long_film(root, t / "film.mp4")
        for g in ("1", "2", "3"):
            r = subprocess.run([str(ROOT / "bin/vh"), "gate", str(p), g], env=env, capture_output=True, text=True)
            if r.returncode:
                print(f"bin/vh gate {g}: {r.stderr.strip()[:300]}")
                return 1
        edit_film(root, p, shots)
        log = t / "desk.log"
        desk = subprocess.Popen([sys.executable, str(HERE / "fixtures/with_tty.py"), str(ROOT / "bin/vh"), "desk", "--root", str(root), "--port", "0", "--idle", "0",
                                 "--no-open", "--print-address"], env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT)
        url = None
        for _ in range(150):
            m = re.search(r"(http://127\.0\.0\.1:\d+/)\?c=([A-Za-z0-9_-]+)", log.read_text(errors="replace"))
            if m:
                url = m.group(0)
                break
            if desk.poll() is not None:
                break
            time.sleep(0.2)
        if not url:
            print("the desk gave no address: " + log.read_text(errors="replace")[:400].replace("\n", " "))
            return 1
        r = subprocess.run(["node", str(HERE / "test_cut_page.mjs")], input=json.dumps({"chrome": chrome, "url": url, "sheets": sheets, "parts": len(PARTS)}),
                           capture_output=True, text=True, timeout=600)
        out = (r.stdout + r.stderr).strip()
        if out:
            print(out)
        return 0 if r.returncode == 0 and not r.stdout.strip() else 1
    finally:
        if desk and desk.poll() is None:
            desk.terminate()
            try:
                desk.wait(10)
            except subprocess.TimeoutExpired:
                desk.kill()
        shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
