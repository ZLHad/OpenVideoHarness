"""Stage the stand-in agents as if bin/vh desk agents install had put them there: <home>/<kind>/node_modules/.bin/<bin>
runs fake_acp.py, and the package's package.json carries the pinned version. Point OVH_AGENTS_DIR at <home>.

  python3 stage.py <home> [--speed S] [--only claude,codex]
"""
import json, shlex, stat, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
import agents as A   # noqa: E402


def stage(home, speed=0.05, only=None, log=None, args=None):
    """log: a file the stand-ins append each prompt to (the adapter's environment is clean, so it is written into the
    wrapper, not passed through the desk's environment). args: {kind: [more arguments]} (--signed-out)."""
    home = Path(home)
    for kind, a in A.ADAPTERS.items():
        if only and kind not in only:
            continue
        nm = home / kind / "node_modules"
        exe = nm / ".bin" / a["bin"]
        exe.parent.mkdir(parents=True, exist_ok=True)
        env = f"FAKE_ACP_LOG={shlex.quote(str(log))} " if log else ""
        exe.write_text("#!/bin/sh\n" + env + "exec " + shlex.quote(sys.executable) + " " + shlex.quote(str(HERE / "fake_acp.py"))
                       + f" {kind} --speed {speed}" + "".join(" " + shlex.quote(x) for x in (args or {}).get(kind, [])) + "\n")
        exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        pj = nm / a["package"] / "package.json"
        pj.parent.mkdir(parents=True, exist_ok=True)
        pj.write_text(json.dumps({"name": a["package"], "version": a["version"]}))
    return home


if __name__ == "__main__":
    args = sys.argv[1:]
    speed = float(args[args.index("--speed") + 1]) if "--speed" in args else 0.05
    only = args[args.index("--only") + 1].split(",") if "--only" in args else None
    print(stage(args[0], speed, only))
