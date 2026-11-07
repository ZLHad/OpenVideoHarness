"""Offline Chrome integration: local synthetic page, fresh profiles, no ambient credentials or Obscura.

python3 tools/web/test_chrome.py [bin/vh] — exit 3 when Chrome is missing; the test serves only local synthetic pages.
"""
import collections, hashlib, http.server, importlib.util, json, os, pathlib, shutil, struct, subprocess, sys, tempfile, threading

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("web_capture", HERE / "web.py")
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)
try:
    chrome = web.chrome()
except web.Failed:
    print("needs a headless Chrome")
    sys.exit(3)
vh = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parents[1] / "bin" / "vh").resolve()
counts = collections.Counter()


class Page(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        counts[self.path] += 1
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/page")
            self.end_headers()
            return
        status = 404 if self.path == "/missing" else 200
        html = f'''<!doctype html><html><head><title>Saved &amp; checked</title><style>.stale{{display:none}}</style></head><body>
<h1>Evidence</h1><p id="fact">initial</p><a href="https://docs.example/fact">Source link</a>
<p class="stale">Old limit: 999 GB</p>
<p>load {counts[self.path]}</p><script>document.getElementById('fact').textContent = 'The limit is 2 GB.';</script>
</body></html>'''.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, *_):
        pass


with tempfile.TemporaryDirectory(prefix="vh-web-test-") as tmp:
    root = pathlib.Path(tmp)
    proj = root / "project"
    proj.mkdir()
    (proj / "BRIEF.md").write_text("# isolated web test\n", encoding="utf-8")
    # Record only the names of environment variables, plus non-secret launch configuration, before exec'ing Chrome.
    log = root / "launches.jsonl"
    wrapper = root / "chrome"
    wrapper.write_text(f'''#!{sys.executable}
import json, os, sys
with open({str(log)!r}, "a") as f:
    f.write(json.dumps({{"args": sys.argv[1:], "keys": sorted(os.environ), "home": os.environ.get("HOME")}}) + "\\n")
os.execv({chrome!r}, [{chrome!r}] + sys.argv[1:])
''', encoding="utf-8")
    wrapper.chmod(0o755)
    env = dict(os.environ, CHROME_PATH=str(wrapper), OVH_WEB_TEST_SECRET="do-not-inherit", GITHUB_TOKEN="synthetic-secret",
               OVH_OBSCURA="/no/obscura/should/run")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Page)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"

    def run(*args, private=True, code=0):
        argv = [os.environ.get("VH_BASH", "bash"), str(vh), "web", *map(str, args)]
        if args[0] in ("fetch", "shot"):
            argv += ["--wait", "0", "--timeout", "10"]
            if private:
                argv += ["--allow-private-network"]
        result = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=160)
        assert result.returncode == code, f"{args[0]}: exit {result.returncode}, wanted {code}: {result.stderr[-1000:]}"
        return result

    try:
        for dump in ("html", "text", "links", "markdown"):
            got = json.loads(run("fetch", proj, url + "/page", "--dump", dump, "--id", dump, "--json").stdout)["capture"]
            assert got["provider"] == "chrome" and got["obscura"] is None and got["status"] == 200 and got["browser"]
            assert got["title"] == "Saved & checked" and got["final_url"] == url + "/page"
            page = proj / "research/web" / dump / web.DUMPS[dump]
            data = page.read_bytes()
            assert got["files"][page.name]["sha256"] == hashlib.sha256(data).hexdigest()
            assert (b"https://docs.example/fact" if dump == "links" else b"The limit is 2 GB.") in data
            if dump in ("text", "markdown"):
                assert b"999 GB" not in data, "hidden old facts must not appear as rendered text/markdown"
        before = counts["/page"]
        shot = json.loads(run("shot", proj, url + "/redirect", "--id", "shot", "--json").stdout)["capture"]
        assert counts["/page"] == before + 1, "screenshot and HTML must share one navigation"
        assert shot["status"] == 200 and shot["final_url"] == url + "/page"
        directory = proj / "research/web/shot"
        png = (directory / "shot.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (1280, 720)
        assert f"load {before + 1}" in (directory / "page.html").read_text()
        missing = json.loads(run("fetch", proj, url + "/missing", "--id", "missing", "--json").stdout)["capture"]
        assert missing["status"] == 404 and any("HTTP 404" in s for s in missing["warnings"])
        result = run("fetch", proj, url + "/page", "--id", "blocked", private=False, code=1)
        assert "private/local address blocked" in result.stderr
        assert not (proj / "research/web/blocked").exists()
        listed = json.loads(run("list", proj, "--json").stdout)["captures"]
        assert len(listed) == 6 and len({r["id"] for r in listed}) == 6
        legacy = {k: v for k, v in listed[0].items() if k not in ("provider", "browser", "status")}
        legacy.update(id="legacy", obscura="0.2.5")
        shutil.copytree(proj / "research/web/html", proj / "research/web/legacy")
        (proj / "research/web/legacy/meta.json").write_text(json.dumps(legacy))
        with open(proj / "research/web.jsonl", "a") as index:
            index.write(json.dumps(legacy) + "\n")
        assert json.loads(run("list", proj, "--json").stdout)["captures"][-1] == legacy
        found = json.loads(run("grep", proj, "all", "2 GB", "--json").stdout)["hits"]
        assert any(h["hits"] for h in found)
        launches = [json.loads(line) for line in log.read_text().splitlines()]
        assert len(launches) >= 6
        profiles = []
        for launch in launches:
            assert not {"GITHUB_TOKEN", "OVH_WEB_TEST_SECRET", "OVH_OBSCURA", "NODE_OPTIONS"}.intersection(launch["keys"])
            assert "--no-sandbox" not in launch["args"] and "--disable-setuid-sandbox" not in launch["args"]
            profile = next(a.split("=", 1)[1] for a in launch["args"] if a.startswith("--user-data-dir="))
            profiles.append(profile)
            assert not pathlib.Path(profile).exists() and not pathlib.Path(launch["home"]).exists()
        assert len(set(profiles)) == len(profiles), "each capture needs a new profile"
        print("Chrome offline: HTML, text, links, markdown, one-load PNG+HTML, redirect/status, 404 warning, private-address refusal, legacy grep/list, clean environment and profiles")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
