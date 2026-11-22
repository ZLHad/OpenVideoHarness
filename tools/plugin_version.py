"""The version of the plugin the two marketplaces install (plugins/open-video-harness), held to its skills. Stdlib only.

Claude Code takes a plugin's "version" as the thing that says a new one is out (with none, every commit to main would be
one); Codex records it too. So the version moves when, and only when, the skills the plugin carries change: skills.sha256
beside the manifests keeps the hash of plugins/open-video-harness/skills/ (every file, by its path and bytes), and
bin/vh sync-agents, after it copies skills/ in, bumps the last number of both manifests' version when that hash changed.

usage: python3 tools/plugin_version.py --write   the hash now; when it changed, the version bumped in both manifests (prints it)
       python3 tools/plugin_version.py --check   exit 1, saying why, when the hash, the two versions or their form disagree
"""
import hashlib, json, re, sys
from pathlib import Path

PLUG = Path(__file__).resolve().parent.parent / "plugins" / "open-video-harness"
MANIFESTS = (PLUG / ".claude-plugin" / "plugin.json", PLUG / ".codex-plugin" / "plugin.json")
RECORD = PLUG / "skills.sha256"


def skills_hash():
    h = hashlib.sha256()
    for f in sorted(q for q in (PLUG / "skills").rglob("*") if q.is_file()):
        h.update(f.relative_to(PLUG / "skills").as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def versions():
    return [json.loads(m.read_text(encoding="utf-8")).get("version") for m in MANIFESTS]


def set_version(v):
    for m in MANIFESTS:   # the manifests keep their own layout: the line is replaced, or added after "name"
        text = m.read_text(encoding="utf-8")
        if re.search(r'(?m)^  "version": "[^"]*",$', text):
            text = re.sub(r'(?m)^  "version": "[^"]*",$', f'  "version": "{v}",', text)
        else:
            text = re.sub(r'(?m)^(  "name": "[^"]*",)$', rf'\1\n  "version": "{v}",', text, count=1)
        m.write_text(text, encoding="utf-8")


def main(argv):
    if argv == ["--write"]:
        now, vs = skills_hash(), versions()
        v = vs[0] or "1.0.0"
        if (RECORD.read_text().strip() if RECORD.exists() else None) != now:
            if RECORD.exists():   # the skills changed since the version was set: the next one
                a, b, c = (int(x) for x in v.split("."))
                v = f"{a}.{b}.{c + 1}"
            RECORD.write_text(now + "\n")
        if vs != [v, v]:
            set_version(v)
        print(v); return 0
    if argv == ["--check"]:
        bad, vs = [], versions()
        if not RECORD.exists() or RECORD.read_text().strip() != skills_hash():
            bad.append("plugins/open-video-harness/skills.sha256 is not the hash of the plugin's skills: bin/vh sync-agents")
        if len(set(vs)) != 1 or not all(isinstance(v, str) and re.fullmatch(r"\d+\.\d+\.\d+", v) for v in vs):
            bad.append(f"the two manifests' versions are not one N.N.N: {vs}")
        print("\n".join(bad)); return 1 if bad else 0
    print(__doc__.strip(), file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
