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


def words_check():
    src = (HERE / "static" / "settings.js").read_text(encoding="utf-8")
    zh = src[src.index("    zh: {"):src.index("    en: {")]
    en = src[src.index("    en: {"):src.index("  };", src.index("    en: {"))]
    keys = lambda block: set(re.findall(r"(?:^|[\s,{])(\w+): \"", block))   # noqa: E731
    if keys(zh) != keys(en):
        return f"only in Chinese: {sorted(keys(zh) - keys(en))}; only in English: {sorted(keys(en) - keys(zh))}"


check("tools/settings.py: Studio's three settings, a value it does not know read as not set, any other name or value refused, other keys kept", module_check)
check("the settings page's words: every one in both languages", words_check)
check("the page in node: this machine's look and language win over the browser's copy (which is kept when the file has none); the top bar's two buttons save; a new conversation starts with the default agent when it is set up", page_check)
try:
    run()
except Exception as e:
    say(False, "the console for the settings page", f"{type(e).__name__}: {e}")
print("end", flush=True)
