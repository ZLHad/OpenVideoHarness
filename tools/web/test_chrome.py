"""Offline Chrome integration: local synthetic page, fresh profiles, no ambient credentials or Obscura.

python3 tools/web/test_chrome.py [bin/vh] — exit 3 when Chrome is missing; the test serves only local synthetic pages.
Run it from a normal shell: Chrome's own process sandbox cannot start inside another macOS sandbox (an agent's, for
one), and then the browser dies with "sandbox initialization failed"/GPU crashes instead of a test failure.
"""
import collections, hashlib, http.server, importlib.util, json, os, pathlib, shutil, struct, subprocess, sys, tempfile, threading

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("web_capture", HERE / "web.py")
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)
vh = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parents[1] / "bin" / "vh").resolve()
counts = collections.Counter()

# The browser's environment is built once here, and the captures below check the same thing end to
# end: a throwaway profile and no inherited secrets, but on macOS the real HOME (the Security
# framework finds ~/Library/Keychains through it; a fake HOME pops system keychain dialogs).
with tempfile.TemporaryDirectory(prefix="vh-web-env-") as probe:
    env_probe = web.browser_env(probe)
    assert not {"GITHUB_TOKEN", "OVH_WEB_TEST_SECRET", "OVH_OBSCURA", "NODE_OPTIONS"}.intersection(env_probe)
    if sys.platform == "darwin":
        assert env_probe["HOME"] == os.environ["HOME"] and pathlib.Path(env_probe["HOME"]).is_dir(), env_probe["HOME"]
    else:
        assert env_probe["HOME"] == probe


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
    # Ask the real CLI to choose its browser first: a cached headless shell takes precedence over the full Mac app.
    # This shim only records the selected executable and environment names; Chrome still runs through the real helper.
    node = shutil.which("node")
    assert node, "needs Node 22"
    shim = root / "shim"
    shim.mkdir()
    selected = root / "selected.json"
    (shim / "node").write_text(f'''#!{sys.executable}
import json, os, sys, tempfile
if len(sys.argv) < 2 or not sys.argv[1].endswith('/chrome.mjs'):
    os.execv({node!r}, [{node!r}] + sys.argv[1:])
payload = sys.stdin.buffer.read()
config = json.loads(payload)
with open({str(selected)!r}, 'w') as f:
    json.dump({{"browser": config["browser"], "keys": sorted(os.environ), "home": os.environ.get("HOME")}}, f)
with tempfile.TemporaryFile() as data:
    data.write(payload); data.seek(0); os.dup2(data.fileno(), 0)
    os.execv({node!r}, [{node!r}] + sys.argv[1:])
''', encoding="utf-8")
    (shim / "node").chmod(0o755)
    # Record that same binary's Chrome arguments and environment for the remaining captures.
    log = root / "launches.jsonl"
    wrapper = root / "chrome"

    def record_browser(chrome):
        wrapper.write_text(f'''#!{sys.executable}
import json, os, sys
with open({str(log)!r}, "a") as f:
    f.write(json.dumps({{"args": sys.argv[1:], "keys": sorted(os.environ), "home": os.environ.get("HOME")}}) + "\\n")
os.execv({chrome!r}, [{chrome!r}] + sys.argv[1:])
''', encoding="utf-8")
        wrapper.chmod(0o755)
        env["CHROME_PATH"] = str(wrapper)
        env["PATH"] = os.environ["PATH"]

    env = dict(os.environ, PATH=str(shim) + os.pathsep + os.environ["PATH"],
               OVH_WEB_TEST_SECRET="do-not-inherit", GITHUB_TOKEN="synthetic-secret",
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
        if code == 0 and "needs a headless Chrome" in result.stderr:
            print("needs a headless Chrome")
            sys.exit(3)
        assert result.returncode == code, f"{args!r}: exit {result.returncode}, wanted {code}: {result.stderr[-1000:]}"
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
            if dump == "html":
                first = json.loads(selected.read_text())
                assert not {"GITHUB_TOKEN", "OVH_WEB_TEST_SECRET", "OVH_OBSCURA", "NODE_OPTIONS"}.intersection(first["keys"])
                if sys.platform == "darwin":
                    assert first["home"] == os.environ["HOME"], "macOS: Chrome must keep the real HOME for the login keychain"
                else:
                    assert not pathlib.Path(first["home"]).exists()
                record_browser(first["browser"])
        before = counts["/page"]
        shot = json.loads(run("shot", proj, url + "/redirect", "--id", "shot", "--json").stdout)["capture"]
        assert 1 <= counts["/page"] - before <= shot["attempts"], "screenshot and HTML must share one navigation per attempt"
        assert shot["status"] == 200 and shot["final_url"] == url + "/page"
        directory = proj / "research/web/shot"
        png = (directory / "shot.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (1280, 720)
        assert f"load {counts['/page']}" in (directory / "page.html").read_text()
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
        assert len(launches) >= 5
        profiles = []
        for launch in launches:
            assert not {"GITHUB_TOKEN", "OVH_WEB_TEST_SECRET", "OVH_OBSCURA", "NODE_OPTIONS"}.intersection(launch["keys"])
            assert "--no-sandbox" not in launch["args"] and "--disable-setuid-sandbox" not in launch["args"]
            profile = next(a.split("=", 1)[1] for a in launch["args"] if a.startswith("--user-data-dir="))
            profiles.append(profile)
            assert not pathlib.Path(profile).exists()
            if sys.platform == "darwin":
                assert launch["home"] == os.environ["HOME"], "macOS: Chrome must keep the real HOME for the login keychain"
            else:
                assert not pathlib.Path(launch["home"]).exists()
        assert len(set(profiles)) == len(profiles), "each capture needs a new profile"
        print("Chrome offline: CLI's default browser, HTML/text/links/visible Markdown, one-load PNG+HTML, redirect/status, 404 warning, private-address refusal, legacy grep/list, clean environment and profiles (real HOME on macOS for the keychain)")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
