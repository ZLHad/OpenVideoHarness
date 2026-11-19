"""The words a person reads, both languages: Studio's three word tables (core.js, modules.js, agent.js, read in node), bin/vh
status's lines as Studio says them in Chinese, where a film stands (tools/standing.py), the review page's words and the
lines bin/vh gate prints for the person. Each key in both languages; none of the names retired for plainer ones
(tools/desk/README.md). Prints a line and exits 0 when they hold, the problems and 1 when not; 0 and a note without node."""
import json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gate as G, review as RV, standing as SD   # noqa: E402

# the words a person reads in Studio, the review pages and gate's lines, retired for plainer ones (tools/desk/README.md, 页面上的字):
# a stop is 一站 by its name, a note 意见, Studio is Studio; codes, files and commands stay out of the words
RETIRED_ZH = re.compile(r"审阅台|控制台|关卡|检查点|这一轮|这一关|点评|反馈|评论|要你定|待你定|点头|待批准|等你点|默认通过|上下文|推理|代理|"
                        r"硬规则|写成意见|记成点评|提交|锁时|样板章|项目|BRIEF|\.md\b|bin/vh")
RETIRED_EN = re.compile(r"(?i)\bdesk\b|\bconsole\b|\bgate\b|checkpoint|\bround\b|\bcomments?\b|feedback|submission|\bsubmit|\(s\)|untouched|"
                        r"to allow|\bcontext\b|\bproxy\b|hard rule|conversation|bin/vh|\.md\b|timing lock|sample chapter")
WORDS_KEEP = {"proj_ph"}   # the film's folder inside a command, in that command's tooltip (<项目> / <project>)


def wording_check():
    """Every string a person reads, both languages: each key in both tables (a key missing in one language fails), none of the
    retired words in any of them: Studio's three tables, bin/vh status's lines as Studio says them in Chinese, where a film
    stands (tools/standing.py), the review page's words and the lines bin/vh gate prints for the person."""
    node = shutil.which("node")
    if not node:
        return None
    prog = r"""
const vm = require("vm"), fs = require("fs");
const doc = { querySelector: () => null, querySelectorAll: () => [], documentElement: { lang: "" }, addEventListener() {} };
const g = vm.createContext({ console, document: doc, window: {}, localStorage: { getItem: () => null, setItem() {} }, setTimeout, clearInterval, setInterval,
  requestAnimationFrame: () => 0, matchMedia: () => ({ matches: false }) });
for (const f of ["core.js", "modules.js", "agent.js"]) vm.runInContext(fs.readFileSync(process.argv[1] + "/" + f, "utf8"), g);
vm.runInContext("this.__T = { STR, MSTR, ASTR };", g);
console.log(JSON.stringify(g.__T));
"""
    out = subprocess.run([node, "-e", prog, str(HERE / "static")], capture_output=True, text=True, timeout=30)
    if out.returncode:
        return out.stderr[-300:]
    bad = []
    for name, tb in json.loads(out.stdout).items():
        flat = {}
        for lang in ("zh", "en"):
            for k, v in tb[lang].items():
                for kk, vv in (v.items() if isinstance(v, dict) else [(None, v)]):
                    flat.setdefault((k, kk), {})[lang] = vv
        for (k, kk), v in flat.items():
            key = k + ("." + kk if kk else "")
            if set(v) != {"zh", "en"}:
                bad.append(f"{name}.{key} only in {'/'.join(v)}")
                continue
            if k in WORDS_KEEP:
                continue
            for lang, rx in (("zh", RETIRED_ZH), ("en", RETIRED_EN)):
                m = rx.search(str(v[lang]))
                if m:
                    bad.append(f"{name}.{key} ({lang}) says {m.group(0)!r}")
    core = (HERE / "static" / "core.js").read_text(encoding="utf-8")
    zh = core.split("const STATUS_ZH = [", 1)[1].split("const STATUS_EN", 1)[0]
    for m in re.finditer(r'=>\s*(["`])(.*?)\1', zh):
        w = RETIRED_ZH.search(re.sub(r"\$\{[^}]*\}", "", m.group(2)))
        if w:
            bad.append(f"STATUS_ZH says {w.group(0)!r}: {m.group(2)[:60]}")
    for k, v in SD.WORDS.items():
        if k.startswith("say."):   # the words a button sends to the agent, as the person's own message: they name bin/vh status for it
            continue
        for lang, x, rx in (("zh", v[0], RETIRED_ZH), ("en", v[1], RETIRED_EN)):
            m = rx.search(x)
            if m:
                bad.append(f"standing {k} ({lang}) says {m.group(0)!r}")
    for lang, rx in (("zh", RETIRED_ZH), ("en", RETIRED_EN)):
        for k, v in list(RV.T[lang].items()) + list(G.SAY[lang].items()):
            if k == "warn":   # the page's own rule breaks, for the agent: a page with any goes to nobody
                continue
            for x in (v if isinstance(v, tuple) else (v,)):
                m = rx.search(re.sub(r"<[^>]+>", "", str(x)))
                if m:
                    bad.append(f"review/gate {k} ({lang}) says {m.group(0)!r}")
    if set(RV.T["zh"]) != set(RV.T["en"]) or set(G.SAY["zh"]) != set(G.SAY["en"]):
        bad.append(f"review/gate keys differ: {sorted(set(RV.T['zh']) ^ set(RV.T['en']))} {sorted(set(G.SAY['zh']) ^ set(G.SAY['en']))}")
    return "; ".join(bad[:20]) + (f" … ({len(bad)} in all)" if len(bad) > 20 else "") if bad else None


if __name__ == "__main__":
    r = wording_check()
    if r is None and not shutil.which("node"):
        print("no node: the word tables were not read")
    elif r:
        print(r)
        sys.exit(1)
    else:
        print("every key in both languages, none of the retired names")
