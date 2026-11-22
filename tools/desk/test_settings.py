"""Studio's settings page (tools/ci.sh settings_page_checks): a console of its own on a made-up machine (its own HOME, temp
folder, settings file, LOCAL.md, no window, no agent, no network), asked through its two addresses as the page asks them,
and the page's words. One line a check on stdout: "ok\t<what>" or "bad\t<what>: <why>", then "end".

  python3 tools/desk/test_settings.py <scratch folder>
"""
import http.client, json, os, re, shutil, signal, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
    sys.exit("usage: python3 tools/desk/test_settings.py <scratch folder>")
T = Path(sys.argv[1]).resolve()
for d in ("tmp", "home/films", "config", "cache", "data", "agents", "profiles"):
    (T / d).mkdir(parents=True, exist_ok=True)
FILMS = T / "home" / "films"   # a films folder in the home folder: the page shows it as ~/films
REVEAL = T / "revealed.log"
CHILD_ENV = T / "reveal-env.txt"
(T / "reveal.sh").write_text(f"#!/bin/sh\nprintf '%s\\n' \"$1\" >> '{REVEAL}'\nenv > '{CHILD_ENV}'\n")   # (what a child of the console inherits, as the column's install does)
(T / "reveal.sh").chmod(0o755)
CONF = T / "config" / "ovh" / "settings.json"
sys.path.insert(0, str(HERE))
import agents as _A   # noqa: E402  (the agents' packages: a stand-in of one is set up below)
A_INFO = _A.ADAPTERS
LOCAL = T / "LOCAL.md"
ENV = dict(os.environ, TMPDIR=str(T / "tmp"), HOME=str(T / "home"), XDG_CONFIG_HOME=str(T / "config"), XDG_CACHE_HOME=str(T / "cache"),
           XDG_DATA_HOME=str(T / "data"), OVH_LOCAL_MD=str(LOCAL), OVH_AGENTS_DIR=str(T / "agents"), OVH_STUDIO_PROFILES=str(T / "profiles"),
           OVH_STUDIO_SHELL="none", OVH_STUDIO_BROWSER="none", OVH_GATE_STUDIO="0", BROWSER="/usr/bin/false",
           OVH_PROJECTS=str(T / "no-such-folder"), OVH_REVEAL=str(T / "reveal.sh"))
for k in ("OVH_KEYSTORE", "OVH_KEYCHAIN", "OVH_KEYSTORE_SERVICE", "OVH_SECRET_TOOL"):   # (tools/ci.sh turns the store off: these checks have one of their own)
    ENV.pop(k, None)
for k in [k for k in ENV if "API_KEY" in k.upper() or k.upper().endswith(("_TOKEN", "_SECRET", "_PLAN_KEY", "_BASE_URL"))]:   # no real key of the person's reaches anything here
    del ENV[k]
FAKE = "ovhTestKey" + os.urandom(6).hex()   # a made-up key: never a real one, and never seen in anything the checks read back
MAC = sys.platform == "darwin" and shutil.which("security") is not None


def stage_store():
    """A password store of these checks' own. macOS: a keychain file in the scratch folder, made with HOME there too (so
    the person's keychain search list is not touched), named on every call, under a service name of its own; deleted at
    the end. Elsewhere: a stand-in secret-tool that keeps its secrets in a file and notes every argument it gets."""
    ENV["OVH_KEYSTORE_SERVICE"] = "ovh-test-" + os.urandom(4).hex()
    if MAC:
        kc = T / "keys" / "test.keychain-db"
        kc.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["security", "create-keychain", "-p", "made-up", str(kc)], env=ENV, check=True, capture_output=True, timeout=20)
        ENV["OVH_KEYCHAIN"] = str(kc)
        return
    tool = T / "secret-tool"
    tool.write_text(f"""#!{sys.executable}
import json, os, sys
store, log = {str(T / "secrets.json")!r}, {str(T / "secret-argv.log")!r}
open(log, "a").write(json.dumps(sys.argv[1:]) + "\\n")
d = json.load(open(store)) if os.path.exists(store) else {{}}
a = sys.argv[1:]; at = dict(zip(a[-4::2], a[-3::2])); k = at.get("service", "") + "|" + at.get("key", "")
if a[0] == "lookup":
    if k in d: print(d[k]); sys.exit(0)
    sys.exit(1)
if a[0] == "store": d[k] = sys.stdin.read()
if a[0] == "clear": d.pop(k, None)
json.dump(d, open(store, "w"))
""")
    tool.chmod(0o755)
    ENV["OVH_SECRET_TOOL"] = str(tool)


def unstage_store():
    if ENV.get("OVH_KEYCHAIN"):
        subprocess.run(["security", "delete-keychain", ENV["OVH_KEYCHAIN"]], env=ENV, capture_output=True, timeout=20)


def say(ok, what, why=""):
    print(("ok" if ok else "bad") + "\t" + what + ("" if ok else f": {why}"), flush=True)


def check(what, fn):
    try:
        r = fn()
        say(r is None, what, "" if r is None else str(r))
    except Exception as e:
        say(False, what, f"{type(e).__name__}: {e}")


def conf():
    try:
        return json.loads(CONF.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ---------- the module, without a console ----------

def module_check():
    sys.path.insert(0, str(ROOT / "tools"))
    keep = dict(os.environ)
    os.environ["XDG_CONFIG_HOME"] = str(T / "config-module")
    try:
        import settings as S
        S.save({"version": 1, "studio_theme": "neon", "studio_lang": "en", "someone_elses": [1]})
        bad = []
        if S.studio() != {"studio_lang": "en", "studio_theme": None, "agent_default": None}:
            bad.append(f"a value it does not know read as a setting: {S.studio()}")
        for name, value in (("studio_theme", "neon"), ("api_key", "x"), ("mirror", "cn")):
            try:
                S.set_studio(name, value)
                bad.append(f"set_studio took {name}={value}")
            except ValueError:
                pass
        S.set_studio("agent_default", "codex")
        S.set_studio("studio_lang", None)
        d = S.load()
        if d.get("agent_default") != "codex" or "studio_lang" in d or d.get("someone_elses") != [1]:
            bad.append(f"after two writes: {d}")
        return "; ".join(bad) or None
    finally:
        os.environ.clear(); os.environ.update(keep)


# ---------- a console ----------

class Desk:
    def __init__(self):
        self.log = T / "desk.log"
        self.proc = subprocess.Popen([sys.executable, str(HERE / "fixtures" / "with_tty.py"), sys.executable, str(HERE / "desk.py"),
                                      "--root", str(FILMS), "--port", "0", "--print-address"],
                                     stdout=open(self.log, "w"), stderr=subprocess.STDOUT, env=ENV, cwd=str(T))
        for _ in range(150):
            m = re.search(r"http://127\.0\.0\.1:(\d+)/\?c=([A-Za-z0-9_-]+)", self.log.read_text())
            if m:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("no address: " + self.log.read_text()[-400:])
        self.port = int(m.group(1))
        self.page = urllib.request.urlopen(f"http://127.0.0.1:{self.port}/?c={m.group(2)}").read().decode()
        st, d = self.req("POST", "/api/claim", {"c": m.group(2)}, token=False)
        self.token = d.get("token", "")

    def req(self, method, path, body=None, token=True, origin=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        h = {"Content-Type": "application/json"} if body is not None else {}
        if token:
            h["X-Desk-Token"] = self.token if token is True else token
        if origin:
            h["Origin"] = origin
        c.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = c.getresponse()
        b = r.read()
        try:
            return r.status, json.loads(b)
        except ValueError:
            return r.status, b

    def stop(self):
        self.proc.send_signal(signal.SIGTERM)
        try:
            self.proc.wait(20)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def run():
    text = (ROOT / "LOCAL.example.md").read_text(encoding="utf-8")
    text = re.sub(r"^- 默认努力程度：.*$", "- 默认努力程度：quick（不填就是 standard；规则见 CLAUDE.md）", text, flags=re.M)
    text = re.sub(r"^- 默认预算：.*$", "- 默认预算：每支片子 5 美元 <!-- 一条注释 -->", text, flags=re.M)
    text = "Effort: studio, said in a note, not a setting\n素材许可：record（也是一句话里的）\n" + text   # lines that are no list item are no setting
    LOCAL.write_text(text, encoding="utf-8")
    codex = A_INFO["codex"]   # one agent set up (a stand-in of its package, never run): the default may name it, not another
    exe = T / "agents" / "codex" / "node_modules" / ".bin" / codex["bin"]
    exe.parent.mkdir(parents=True, exist_ok=True); exe.write_text("#!/bin/sh\nexit 1\n"); exe.chmod(0o755)
    pkg = T / "agents" / "codex" / "node_modules" / codex["package"] / "package.json"
    pkg.parent.mkdir(parents=True, exist_ok=True); pkg.write_text(json.dumps({"version": codex["version"]}))
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(json.dumps({"version": 1, "mirror": "cn", "mirror_at": "2026-11-01", "kept_for_later": {"a": 1}}), encoding="utf-8")
    ENV["OVH_PROBE_OFFLINE"] = str(T / "rec")   # the page's 测一下: answered from the recording doctor_keys_check made
    out = subprocess.run([sys.executable, "-c", "import json, settings as S; print(json.dumps(S.env_changes(environ={}, mode='cn')))"],
                         cwd=str(ROOT / "tools"), env=ENV, capture_output=True, text=True, timeout=60).stdout
    CN = json.loads(out.strip().splitlines()[-1])   # Studio started under cn: what bin/vh exported for it
    ENV.update(CN)
    d = Desk()
    try:
        def page():
            bad = [f for f in ("settings.js", "settings.css") if f'/static/{f}' not in d.page]
            for f in ("settings.js", "settings.css"):
                st, _ = d.req("GET", f"/static/{f}", token=False)
                if st != 200:
                    bad.append(f"/static/{f} answers {st}")
            return "; ".join(bad) or None
        check("the page loads the settings page's script and style, and the console serves them", page)

        def read():
            st, _ = d.req("GET", "/api/settings", token=False)
            if st != 403:
                return f"without the token: {st}"
            if d.req("GET", "/api/settings", token="not-it")[0] != 403:
                return "a wrong token is let in"
            st, s = d.req("GET", "/api/settings")
            if st != 200 or s.get("version") != 1:
                return f"{st} {s}"
            bad = []
            if s["studio"] != {"studio_lang": None, "studio_theme": None, "agent_default": None}: bad.append(f"studio {s['studio']}")
            if {k: s["mirror"].get(k) for k in ("mode", "why", "at")} != {"mode": "cn", "why": None, "at": "2026-11-01"} or not isinstance(s["mirror"].get("kept_own"), list): bad.append(f"mirror {s['mirror']}")
            L = s["local"]["lines"]
            if L.get("effort") != "quick" or L.get("budget") != "每支片子 5 美元" or L.get("review") is not None or L.get("sound") is not None or L.get("assets") is not None:
                bad.append(f"LOCAL.md's lines (only list items; a template's {{…}}, its bracketed hint and a comment are no part of a value): {L}")
            if [(k["kind"], k["installed"]) for k in s["agents"]["kinds"]] != [("claude", False), ("codex", True), ("dsh", False)]:
                bad.append(f"agents {s['agents']}")
            if {"path": os.path.realpath(FILMS), "shown": "~/films"} not in s["roots"] or any("no-such-folder" in r["path"] for r in s["roots"]):
                bad.append(f"the films folders (those that exist, ~ for the home folder): {s['roots']}")
            if not s["about"].get("version") or not str(s["about"].get("url", "")).startswith("https://github.com/ZLHad/OpenVideoHarness/releases"):
                bad.append(f"about {s['about']}")
            return "; ".join(bad) or None
            return "; ".join(bad) or None
        check("GET /api/settings: only with this run's token; Studio's three settings, the mirror, LOCAL.md's list items as shown (never a template, its hint, a comment or a line in a note), the agents, the films folders that exist (~ for home), the version and its notes", read)

        def write():
            bad = []
            for body, want in (({"name": "studio_theme", "value": "prism"}, 200), ({"name": "studio_lang", "value": "en"}, 200),
                               ({"name": "agent_default", "value": "codex"}, 200)):
                st, s = d.req("POST", "/api/settings", body)
                if st != want: bad.append(f"{body}: {st} {s}")
            c = conf()
            if (c.get("studio_theme"), c.get("studio_lang"), c.get("agent_default")) != ("prism", "en", "codex"): bad.append(f"the file: {c}")
            if c.get("kept_for_later") != {"a": 1} or c.get("mirror") != "cn": bad.append(f"a key it does not change was not kept: {c}")
            page = urllib.request.urlopen(f"http://127.0.0.1:{d.port}/").read().decode()
            if '<html lang="zh-CN" data-theme="prism">' not in page or '<meta name="desk-lang" content="en">' not in page: bad.append("the page served does not carry the look and the language kept")
            st, s = d.req("POST", "/api/settings", {"name": "studio_lang", "value": None})
            if st != 200 or "studio_lang" in conf() or s["studio"]["studio_lang"] is not None: bad.append(f"null (back to Studio's default): {st} {conf()}")
            st, a = d.req("GET", "/api/space/agents")
            if st != 200 or a.get("default") != "codex": bad.append(f"the agent column is not told the default: {st} {a.get('default') if isinstance(a, dict) else a}")
            return "; ".join(bad) or None
        check("POST /api/settings: language, look and the default agent kept in this machine's settings file (other keys kept as they were; null goes back to Studio's default); the agent column is told the default", write)

        def mirror():
            bad = []
            st, s = d.req("POST", "/api/settings", {"name": "mirror", "value": "off"})
            c = conf()
            if st != 200 or c.get("mirror") != "off" or s["mirror"]["mode"] != "off" or not c.get("mirror_at"): bad.append(f"off: {st} {c}")
            d.req("POST", "/api/settings", {"name": "reveal", "value": os.path.realpath(FILMS)})   # a child of the console now (the column's install is one)
            for _ in range(50):
                if (T / "reveal-env.txt").exists():
                    break
                time.sleep(0.1)
            child = dict(x.split("=", 1) for x in (T / "reveal-env.txt").read_text().splitlines() if "=" in x)
            if not CN.get("OVH_MIRROR") or "OVH_MIRROR" in child or any(child.get(k) == v for k, v in CN.items()):
                bad.append(f"started under cn, switched to the official sources in the page: a child of the console still has the mirror {sorted(k for k, v in CN.items() if child.get(k) == v)}")
            st, s = d.req("POST", "/api/settings", {"name": "mirror", "value": "auto"})
            c = conf()
            if st != 200 or any(k in c for k in ("mirror", "mirror_at", "mirror_why")) or s["mirror"]["mode"] != "auto": bad.append(f"auto: {st} {c}")
            r = subprocess.run(["bash", str(ROOT / "bin" / "vh"), "settings", "mirror", "--get"], env=ENV, capture_output=True, text=True, timeout=60)
            if r.stdout.strip() != "auto": bad.append(f"bin/vh settings mirror --get says {r.stdout.strip()!r} {r.stderr[-200:]}")
            return "; ".join(bad) or None
        check("the download mirror from the page: off, then automatic, through tools/settings.py, and bin/vh settings sees the same; Studio started under the mirror, switched to the official sources, starts no child with the mirror's variables", mirror)

        def refusals():
            bad = []
            before = CONF.read_bytes()
            for body in ({"name": "studio_theme", "value": "neon"}, {"name": "GEMINI_API_KEY", "value": "x"}, {"name": "mirror", "value": "nope"},
                         {"name": "studio_lang", "value": 3}, {"name": "model:claude", "value": "claude-opus-5-5"},
                         {"name": "effort:nobody", "value": "high"}, {"value": "en"}, {"name": "agent_default", "value": "dsh"},
                         {"name": "reveal", "value": "/"}, {"name": "reveal", "value": str(T)}):
                st, _ = d.req("POST", "/api/settings", body)
                if st != 400: bad.append(f"{body}: {st}")
            if d.req("POST", "/api/settings", {"name": "studio_theme", "value": "bridge"}, token=False)[0] != 403: bad.append("no token")
            if d.req("POST", "/api/settings", {"name": "studio_theme", "value": "bridge"}, origin="http://evil.example")[0] != 403: bad.append("another origin")
            if CONF.read_bytes() != before: bad.append("a refused request changed the file")
            return "; ".join(bad) or None
        check("POST /api/settings refuses what is not one of its settings or values (a model no chat offered, any key's name, an agent not set up, a folder that is not one of its films folders), without the token, from another origin, and changes nothing then", refusals)

        def reveal():
            st, _ = d.req("POST", "/api/settings", {"name": "reveal", "value": os.path.realpath(FILMS)})
            for _ in range(50):
                if REVEAL.exists():
                    break
                time.sleep(0.1)
            got = REVEAL.read_text().split("\n")[:-1] if REVEAL.exists() else []
            return None if st == 200 and got and set(got) == {os.path.realpath(FILMS)} else f"{st}, opened {got}"
        check("a films folder opens in the file browser (a stand-in here), that folder and nothing else", reveal)

        def services():
            bad = []
            st, s = d.req("POST", "/api/settings", {"name": "key:GEMINI_API_KEY", "value": None})   # (the checks before saved one)
            sv = {x["module"]: x for x in s.get("services", [])}
            if list(sv) != ["gemini", "minimax", "elevenlabs", "dashscope"] or s.get("store") not in ("keychain", "secret-service"):
                return f"services {list(sv)}, store {s.get('store')}"
            if sv["gemini"]["keys"] != [{"name": "GEMINI_API_KEY", "source": None, "saved": False}] or sv["gemini"]["cost"] != "free_tier" \
                    or not sv["gemini"]["key_url"].startswith("https://") or sv["minimax"]["cost"] != "paid":
                bad.append(f"gemini before: {sv['gemini']}")
            st, s = d.req("POST", "/api/settings", {"name": "key:GEMINI_API_KEY", "value": FAKE})
            g = {x["module"]: x for x in s.get("services", [])}.get("gemini", {})
            if st != 200 or FAKE in json.dumps(s) or g.get("keys") != [{"name": "GEMINI_API_KEY", "source": "studio", "saved": True}]:
                bad.append(f"saving: {st} {g}")
            st, t = d.req("POST", "/api/settings", {"name": "test:gemini"})
            if st != 200 or (t.get("probe") or {}).get("state") != "ok": bad.append(f"测一下: {st} {t}")
            for body, why in (({"name": "key:GEMINI_API_KEY", "value": "not a key"}, "not_a_key"), ({"name": "key:PATH", "value": FAKE}, None), ({"name": "test:openverse"}, None)):
                st, e = d.req("POST", "/api/settings", body)
                if st != 400 or FAKE in json.dumps(e) or "not a key" in json.dumps(e) or e.get("reason") != why: bad.append(f"{body['name']}: {st} {e}")
            st, s = d.req("POST", "/api/settings", {"name": "key:GEMINI_API_KEY", "value": "a" * 2048})   # a key as long as the longest a provider issues
            if st != 200 or {x["module"]: x for x in s["services"]}["gemini"]["keys"][0]["source"] != "studio": bad.append(f"a 2048-character key: {st}")
            if d.req("POST", "/api/settings", {"name": "key:GEMINI_API_KEY", "value": FAKE}, token=False)[0] != 403: bad.append("saved without the token")
            st, s = d.req("POST", "/api/settings", {"name": "key:GEMINI_API_KEY", "value": None})
            if st != 200 or {x["module"]: x for x in s["services"]}["gemini"]["keys"][0]["saved"]: bad.append(f"taking it out: {st}")
            st, s = d.req("GET", "/api/settings")   # (the console remembers what it asked the store: a save or a removal is seen at once)
            if {x["module"]: x for x in s["services"]}["gemini"]["keys"][0] != {"name": "GEMINI_API_KEY", "source": None, "saved": False}: bad.append("after taking it out, the page is told it is still set")
            d.req("POST", "/api/settings", {"name": "key:GEMINI_API_KEY", "value": FAKE})   # saved again, for what follows
            if FAKE in d.log.read_text(): bad.append("the key is in the console's log")
            return "; ".join(bad) or None
        check("the services: each key's state and never the key; saved, tested at no cost (a recording here), refused when it is not a key, a key's name or a service with a key, taken out; nothing in the console's log", services)

        def local_untouched():
            return None if "默认努力程度：quick" in LOCAL.read_text(encoding="utf-8") and not list(T.glob("LOCAL.md.*")) else "LOCAL.md was written"
        check("nothing on the page writes LOCAL.md", local_untouched)
    finally:
        d.stop()


def page_check():
    """settings.js and agent.js in node: what this machine keeps wins over this browser's copy; the top bar's language and look
    buttons save; a new conversation starts with the default agent that is set up."""
    node = shutil.which("node")
    if not node:
        return None
    prog = r"""
const vm = require("vm"), fs = require("fs"), dir = process.argv[1];
const on = {}, posts = [];
const listen = (k, f) => { (on[k] = on[k] || []).push(f); };
const doc = { querySelector: () => null, querySelectorAll: () => [], documentElement: { lang: "", getAttribute: () => "darkfield" }, addEventListener: listen };
const g = vm.createContext({ console, document: doc, window: { addEventListener: listen }, navigator: { platform: "MacIntel" }, URL,
  localStorage: { getItem: () => null, setItem() {} }, setTimeout: () => 0, clearInterval() {}, setInterval: () => 0, requestAnimationFrame: () => 0,
  fetch: async (url, o) => { if (o && o.method === "POST") posts.push(JSON.parse(o.body)); return { ok: true, status: 200, json: async () => ({}) }; } });
vm.runInContext(fs.readFileSync(dir + "/core.js", "utf8"), g);
vm.runInContext("let TOKEN = 't'; function toast() {} function parse() { return { view: 'home' }; } const OVH = { theme() {} }; LANG = 'en';", g);
for (const f of ["settings.js", "agent.js"]) vm.runInContext(fs.readFileSync(dir + "/" + f, "utf8") + (f === "agent.js" ? "\nthis.AGENT = AGENT;" : "\nthis.SETTINGS = SETTINGS;"), g);
const P = g.SETTINGS._plan;
const plans = [P({ studio_theme: "prism", studio_lang: "zh" }, "bridge", "en"), P({}, "bridge", "en"), P({}, "darkfield", "zh"), P({ studio_lang: "en" }, "prism", "zh")];
const click = (sel, extra) => Promise.all(on.click.map((f) => f({ target: { closest: (s) => (s === sel ? Object.assign({ closest: () => null }, extra) : null) }, isTrusted: true })));
(async () => {
  await click("#lang");
  await click("[data-theme-set]", { dataset: { themeSet: "bridge" } });
  const K = g.AGENT._defaultKind;
  const ks = [{ kind: "claude", installed: true }, { kind: "codex", installed: true }, { kind: "dsh", installed: false }];
  const kinds = [K({ agents: ks, default: "codex" }), K({ agents: ks, default: "dsh" }), K({ agents: ks, default: null }), K({ agents: [{ kind: "claude", installed: false }], default: null })];
  console.log(JSON.stringify({ plans, posts, kinds }));
})();
"""
    out = subprocess.run([node, "-e", prog, str(HERE / "static")], capture_output=True, text=True, timeout=30)
    if out.returncode:
        return out.stderr[-400:]
    r = json.loads(out.stdout)
    want = [{"theme": "prism", "lang": "zh", "keep_theme": None, "keep_lang": None}, {"theme": "bridge", "lang": "en", "keep_theme": "bridge", "keep_lang": "en"},
            {"theme": "darkfield", "lang": "zh", "keep_theme": None, "keep_lang": None}, {"theme": "prism", "lang": "en", "keep_theme": "prism", "keep_lang": None}]
    if r["plans"] != want:
        return f"what this machine keeps does not win over the browser's copy: {r['plans']}"
    if r["posts"] != [{"name": "studio_lang", "value": "en"}, {"name": "studio_theme", "value": "bridge"}]:
        return f"the top bar's buttons did not save: {r['posts']}"
    if r["kinds"] != ["codex", "claude", "claude", "claude"]:
        return f"a new conversation's agent: {r['kinds']}"


def py(code, env=None):
    """A few lines of Python in the checks' environment (the store staged), in tools/ → (exit, stdout + stderr)."""
    r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT / "tools"), env=env or ENV, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


def keys_module_check():
    code = f"""
import os, keys as K
v = {FAKE!r}
assert K.store_kind() in ("keychain", "secret-service"), K.store_kind()
assert K.get("GEMINI_API_KEY") is None and K.source("GEMINI_API_KEY") is None
K.save("GEMINI_API_KEY", v)
assert K.stored("GEMINI_API_KEY") == v and K.get("GEMINI_API_KEY") == v and K.source("GEMINI_API_KEY") == "studio"
os.environ["GEMINI_API_KEY"] = "fromTheEnvironment1"
assert K.get("GEMINI_API_KEY") == "fromTheEnvironment1" and K.source("GEMINI_API_KEY") == "env"
del os.environ["GEMINI_API_KEY"]
for name, val in (("GEMINI_API_KEY", "has a space"), ("GEMINI_API_KEY", "-looksLikeAnOption"), ("GEMINI_API_KEY", "short"), ("HOME", v), ("SOME_API_KEY", v)):
    try:
        K.save(name, val); raise SystemExit(f"took {{name}}={{val!r}}")
    except ValueError:
        pass
K.clear("ELEVENLABS_API_KEY")   # nothing saved: nothing to do
calls, real = [], K._run
K._run = lambda *a, **k: (calls.append(a[0][:2]), real(*a, **k))[1]   # every call of the store, counted
K.forget(); K.get("GEMINI_API_KEY"); K.get("GEMINI_API_KEY"); K.source("GEMINI_API_KEY"); K.stored("GEMINI_API_KEY")
assert len(calls) == 1, f"four lookups asked the store {{len(calls)}} times"
K.clear("GEMINI_API_KEY"); n = len(calls)
assert K.get("GEMINI_API_KEY") is None and K.source("GEMINI_API_KEY") is None and len(calls) == n, "after a removal: still found, or asked again"
K.save("GEMINI_API_KEY", v); n = len(calls)
assert K.get("GEMINI_API_KEY") == v and len(calls) == n, "after a save: not found at once, or asked again"
K.forget(); K._run = lambda *a, **k: (calls.append(a[0][:2]), None)[1]; n = len(calls)   # a store that does not answer in time
assert K.get("MINIMAX_API_KEY") is None and K.get("MINIMAX_API_KEY") is None and len(calls) == n + 1, "a store with no answer asked again"
assert K.LOOKUP_S <= 3
print("ok")
"""
    rc, out = py(code)
    if rc or out.strip() != "ok":
        return out[-300:]
    if not MAC and FAKE in (T / "secret-argv.log").read_text():
        return "the key was an argument of secret-tool"
    if subprocess.run([sys.executable, str(ROOT / "tools" / "keys.py"), "has", "GEMINI_API_KEY"], env=ENV, timeout=30).returncode != 0:
        return "keys.py has: a saved key not found"


def env_reads(rel, text, names):
    """The lines of one file that read a service's key from the environment, not through tools/keys.py: a key's name
    read anywhere (os.environ, getenv, "X" in os.environ, process.env, a shell's $X); and, in a file that has anything
    to do with keys (it names one, KEY_NAMES, KEY_OF, imports keys or reads modules.json's "keys"), any read of the
    environment by a name it does not spell, which could be a key's (os.environ.get(k), os.environ[var], getenv(x))."""
    k = "|".join(map(re.escape, names))
    lit = re.compile(r"""environ(?:\.get|\.pop|\.setdefault)?\(\s*["'](?:%s)["']|environ\[\s*["'](?:%s)["']\s*\](?!\s*=[^=])|getenv\(\s*["'](?:%s)["']"""
                     r"""|["'](?:%s)["']\s+(?:not\s+)?in\s+(?:os\.)?environ\b|process\.env(?:\.(?:%s)\b|\[\s*["'](?:%s)["'])"""
                     r"""|\$\{?(?:%s)\b|printenv\s+["']?(?:%s)\b""" % ((k,) * 8))
    shell = rel.endswith(".sh") or rel.startswith("bin/")
    dyn = re.compile(r"""(?:environ\.get|getenv)\(\s*(?!["'\s)])|environ\[\s*(?!["'])(?![^\]]*\]\s*=[^=])|(?<![\w"'])\w+\s+(?:not\s+)?in\s+(?:os\.)?environ\b(?![.\[])"""
                     r"""|process\.env\[\s*(?!["'])""" + (r"""|\$\{!|printenv\s+["$]""" if shell else ""))
    keyish = re.search(r"\b(?:%s|KEY_NAMES|KEY_OF)\b|^\s*(?:import keys|from keys import)\b|\bimport keys as\b|get\(\s*[\"']keys[\"']\s*\)|\[[\"']keys[\"']\]" % k, text, re.M)
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if lit.search(line) or (keyish and dyn.search(line) and (rel, line.strip()) not in ENV_READS_OK):
            out.append(f"{rel}:{i}")
    return out


# a read of the environment by a name the line does not spell, in a file that has to do with keys, that reads no key
ENV_READS_OK = {
    ("tools/audio/tts.py", "raw = os.environ.get(key)"),   # MINIMAX_TTS_SPEED / _VOL / _PITCH (minimax_settings)
    ("tools/audio/tts.py", 'penv = {k: os.environ.get(k) for k in MINIMAX_ENV} if a.provider == "minimax" else {}'),   # MINIMAX_TTS_MODEL and the three above
    ("tools/doctor.py", 'at = os.environ.get(ck["env"]) if ck.get("env") else None'),   # where a program is (modules.json's check.env)
    ("tools/doctor.py", 'model = os.environ.get(ck["hf_model"].get("env", ""), "") or ck["hf_model"]["default"]'),   # a model's id (QWEN_TTS_MODEL)
    ("tools/doctor.py", 'if p.get("base_env") and os.environ.get(p["base_env"]):'),   # a service's base address (MINIMAX_BASE_URL)
    ("tools/doctor.py", 'b = urllib.parse.urlsplit(os.environ[p["base_env"]])'),
}


def readers_check():
    """Every place that reads one of the services' keys goes through tools/keys.py: the code under bin/, tools/, engines/,
    components/ and styles/ (tests and their fixtures left out, and showcase/: finished films' own scripts, kept as they
    were made), searched by env_reads, which is first tried on lines that read a key the ways the code once did."""
    sys.path.insert(0, str(ROOT / "tools"))
    import keys as K
    names = K.KEY_NAMES
    tries = {   # each must be found
        "tools/doctor.py": 'import keys\n        r["keys"][k] = bool(os.environ.get(k))\n',
        "tools/audio/tts.py": 'KEY_OF = {}\n    key = os.environ.get(KEY_OF[a.provider].split()[0])\n',
        "tools/audio/x.py": 'KEY_OF = {}\nfor var in ("MINIMAX_TOKEN_PLAN_KEY", "MINIMAX_API_KEY"):\n    key = os.environ.get(var)\n',
        "tools/a.py": 'if "GEMINI_API_KEY" in os.environ:\n', "tools/b.py": 'k = os.getenv("DASHSCOPE_API_KEY")\n',
        "tools/c.py": 'k = os.environ["ELEVENLABS_API_KEY"]\n', "tools/c2.py": 'if os.environ["MINIMAX_API_KEY"] == "x": pass\n', "tools/d.mjs": 'const k = process.env.GEMINI_API_KEY;\n',
        "tools/e.sh": 'curl -H "x-goog-api-key: ${GEMINI_API_KEY}"\n', "bin/f": 'v=GEMINI_API_KEY; echo "${!v}"\n',
        "tools/g.py": 'from keys import KEY_NAMES\nprint({k: os.environ.get(k) for k in KEY_NAMES})\n',
    }
    missed = [f for f, text in tries.items() if not env_reads(f, text, names)]
    if missed:
        return f"the search misses a key read the way these did: {missed}"
    try:
        files = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT), capture_output=True, text=True, timeout=30, check=True).stdout.split("\0")
    except (OSError, subprocess.SubprocessError):
        files = [str(f.relative_to(ROOT)) for f in ROOT.rglob("*") if f.is_file()]
    bad, seen = [], 0
    for rel in files:
        top = rel.split("/")[0]
        if top not in ("bin", "tools", "engines", "components", "styles") or rel == "tools/keys.py":
            continue
        name = rel.rsplit("/", 1)[-1]
        if name.startswith("test_") or "/fixtures/" in rel or "/node_modules/" in rel:
            continue
        if not (top == "bin" or re.search(r"\.(py|sh|bash|js|mjs|cjs|ts)$", name)):
            continue
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        seen += 1
        bad += env_reads(rel, text, names)
    if seen < 50:
        return f"only {seen} files searched"
    return f"reads a key without tools/keys.py: {bad}" if bad else None


def doctor_keys_check():
    rec = T / "rec"; rec.mkdir(exist_ok=True)
    (rec / "gemini.json").write_text(json.dumps({"models": [{"name": "models/" + n} for n in ("gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts",
                                     "gemini-3.5-transcribe", "gemini-nano-banana-2.1", "gemini-3-pro-image", "lyria-3.5")]}))
    (rec / "minimax.json").write_text(json.dumps({"base_resp": {"status_code": 0}}))
    (rec / "responses.json").write_text(json.dumps({"v": 1, "responses": [{"url": "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000",
                                                    "status": 200, "headers": {}, "body": "gemini.json"},
                                                   {"url": "https://api.minimax.io/v1/get_voice", "status": 200, "headers": {}, "body": "minimax.json"}]}))
    doc = lambda *a: subprocess.run([sys.executable, str(ROOT / "tools" / "doctor.py"), *a], env=ENV, capture_output=True, text=True, timeout=120)   # noqa: E731
    j, t, p = doc("--json"), doc(), doc("--json", "--probe", "--only", "gemini", "--offline", str(rec))
    if FAKE in j.stdout + j.stderr + t.stdout + t.stderr + p.stdout + p.stderr:
        return "doctor printed the key"
    g = next(m for m in json.loads(j.stdout)["modules"] if m["name"] == "gemini")
    if g["keys"] != {"GEMINI_API_KEY": True} or g["key_source"] != {"GEMINI_API_KEY": "studio"} or g["state"] != "ok":
        return f"doctor --json: {g['keys']} {g.get('key_source')} {g['state']}"
    if "GEMINI_API_KEY set in Studio" not in t.stdout:
        return "doctor's line does not say the key is set in Studio"
    pr = next(m for m in json.loads(p.stdout)["modules"] if m["name"] == "gemini")["probe"]
    if not pr or pr["state"] != "ok":
        return f"doctor --probe with the key saved in Studio: {pr}"
    rc, out = py(f"import keys as K\nK.save('MINIMAX_TOKEN_PLAN_KEY', {FAKE + 'Plan'!r}); K.save('MINIMAX_API_KEY', {FAKE + 'Pay'!r})")   # both of MiniMax's: each is asked
    try:
        if rc:
            return out[-300:]
        mm = doc("--json", "--probe", "--only", "minimax", "--offline", str(rec))
        pr = next(m for m in json.loads(mm.stdout)["modules"] if m["name"] == "minimax")["probe"]
        if not pr or pr["state"] != "ok" or not all(n in pr["note"] for n in ("MINIMAX_TOKEN_PLAN_KEY", "MINIMAX_API_KEY")) or FAKE in mm.stdout + mm.stderr:
            return f"doctor --probe with both MiniMax keys: {pr}"
    finally:
        py("import keys as K\nK.clear('MINIMAX_TOKEN_PLAN_KEY'); K.clear('MINIMAX_API_KEY')")


def column_check():
    """A command the agent column's agent runs (its environment has no key: acp.clean_env) finds a key saved in Studio."""
    sys.path.insert(0, str(HERE))
    import acp
    keep = dict(os.environ)
    try:
        os.environ.clear(); os.environ.update(ENV)
        env = acp.clean_env({k: ENV[k] for k in ("OVH_KEYCHAIN", "OVH_KEYSTORE_SERVICE", "OVH_SECRET_TOOL") if ENV.get(k)})
    finally:
        os.environ.clear(); os.environ.update(keep)
    if any("API_KEY" in k for k in env):
        return f"the column's environment carries a key: {[k for k in env if 'API_KEY' in k]}"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "keys.py"), "has", "GEMINI_API_KEY"], env=env, timeout=30)
    return None if r.returncode == 0 else "not found in the column's environment"


def first_run_check():
    """A film whose voice-over stopped for want of Gemini's API Key: the command says the one sentence (where to set it, where
    to get one, what works without), its record has the code no_key, and bin/vh status says the film waits on the key, with
    the way to Settings → Services; once the key is saved in Studio, it says so no more. (No call is made: the check comes
    first, and the store is these checks' own.)"""
    if not shutil.which("uv"):
        return None
    film = T / "first-run"
    shutil.rmtree(film, ignore_errors=True)
    shutil.copytree(HERE / "fixtures" / "demo", film)
    (film / "audio" / "script.txt").write_text("你好，这是一句试音。\n", encoding="utf-8")
    env = dict(ENV, OVH_ACTIVITY_AGENT="0")
    vh = lambda *a: subprocess.run(["bash", str(ROOT / "bin" / "vh"), *a], env=env, capture_output=True, text=True, timeout=180)   # noqa: E731
    rc, out = py("import keys as K\nK.clear('GEMINI_API_KEY')")
    if rc:
        return out[-300:]
    r = vh("tts", str(film), "gemini")
    if r.returncode != 1 or "Studio's Settings → Services" not in r.stderr or "GEMINI_API_KEY" not in r.stderr or "aistudio.google.com" not in r.stderr:
        return f"bin/vh tts gemini with no key: exit {r.returncode}, {r.stderr[-300:]!r}"
    if list((film / "audio").glob("voiceover*")):
        return "something was voiced"
    notes = [json.loads(x) for x in (film / ".ovh" / "activity.jsonl").read_text().splitlines() if '"note"' in x]
    if not any(n.get("level") == "error" and n.get("code") == "no_key" for n in notes):
        return f"the run's record: {notes[-1:]}"
    now = json.loads(vh("status", str(film), "--json").stdout)["now"]
    if now["code"] != "needs_key" or now["act"].get("kind") != "settings" or now["act"].get("sub") != "services" or now["facts"].get("keys") != ["GEMINI_API_KEY"]:
        return f"bin/vh status while the film waits: {now['code']} {now['act']}"
    if "now: The voice-over stopped: there's no Gemini API Key yet." not in vh("status", str(film)).stdout:
        return "bin/vh status's now: line"
    rc, out = py(f"import keys as K\nK.save('GEMINI_API_KEY', {FAKE!r})")
    try:
        if rc:
            return out[-300:]
        now = json.loads(vh("status", str(film), "--json").stdout)["now"]
        if now["code"] == "needs_key":
            return "the key saved in Studio, and the film is still said to wait on it"
    finally:
        py("import keys as K\nK.clear('GEMINI_API_KEY')")


def words_check():
    src = (HERE / "static" / "settings.js").read_text(encoding="utf-8")
    zh = src[src.index("    zh: {"):src.index("    en: {")]
    en = src[src.index("    en: {"):src.index("  };", src.index("    en: {"))]
    keys = lambda block: set(re.findall(r"(?:^|[\s,{])(\w+): \"", block))   # noqa: E731
    if keys(zh) != keys(en):
        return f"only in Chinese: {sorted(keys(zh) - keys(en))}; only in English: {sorted(keys(en) - keys(zh))}"


real_list = subprocess.run(["security", "list-keychains", "-d", "user"], capture_output=True, text=True).stdout if MAC else ""
try:
    stage_store()   # before any check: none of them can reach a store but this one
    check("tools/settings.py: Studio's three settings, a value it does not know read as not set, any other name or value refused, other keys kept", module_check)
    check("the settings page's words: every one in both languages", words_check)
    check("every command that reads a service's key does it through tools/keys.py (indirect reads too)", readers_check)
    check("the page in node: this machine's look and language win over the browser's copy (which is kept when the file has none); the top bar's two buttons save; a new conversation starts with the default agent when it is set up", page_check)
    check("tools/keys.py on a store of these checks' own: saved, found, the environment first, taken out; what is not a key or a key's name refused; the store asked once per name (a missing key and a store with no answer too), a save or removal seen at once" + ("" if MAC else "; the key never an argument"), keys_module_check)
    check("bin/vh doctor finds a key saved in Studio, says so, and probes with it (a recording), with each of MiniMax's two when both are saved, never printing one", doctor_keys_check)
    check("a command run in the agent column's environment (no key in it) finds a key saved in Studio", column_check)
    check("a voice-over with no key: the command says where to set it and where to get one (code no_key on its record); bin/vh status says the film waits on the key, with the way to Settings → Services, and no more once it is saved", first_run_check)
    run()
except Exception as e:
    say(False, "the console for the settings page", f"{type(e).__name__}: {e}")
finally:
    unstage_store()
    if MAC and subprocess.run(["security", "list-keychains", "-d", "user"], capture_output=True, text=True).stdout != real_list:
        say(False, "the person's keychain search list", "changed")
print("end", flush=True)
