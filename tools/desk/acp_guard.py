"""Runs an agent's adapter for the desk and outlives it by no more than a second or two.

  python3 acp_guard.py <desk pid> -- <adapter argv…>

The desk starts this as the leader of a new process group; the adapter is its child in that group and talks to the desk
over the same stdin and stdout (this process never reads or writes them). When the desk goes away without stopping the
adapter (a kill -9, a crash: no chance to clean up), this process notices that its parent changed and stops the whole
group: TERM, then KILL. DeepSeek Harness does not end when its input closes, so without this it would be left running.
When the adapter ends by itself, this ends with its exit status.
"""
import os, signal, subprocess, sys, time


def main():
    desk = int(sys.argv[1])
    argv = sys.argv[sys.argv.index("--") + 1:]
    child = subprocess.Popen(argv)   # inherits stdin, stdout and stderr: the desk talks to the adapter directly
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1):   # this process holds no end of the conversation: the desk sees the adapter's EOF, not ours
        os.dup2(devnull, fd)

    def stop(signum, _frame):   # the desk's own stop: TERM to the group, which reached the adapter too
        try:
            child.wait(timeout=8)
        except subprocess.TimeoutExpired:
            pass
        sys.exit(128 + signum)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    while child.poll() is None:
        if os.getppid() != desk:   # the desk is gone: take the adapter (and whatever it started) with it
            signal.signal(signal.SIGTERM, signal.SIG_IGN)   # the group's TERM is for the others; this one stays to KILL
            try:
                os.killpg(0, signal.SIGTERM)
            except OSError:
                pass
            for _ in range(30):
                if child.poll() is not None:
                    break
                time.sleep(0.1)
            try:
                os.killpg(0, signal.SIGKILL)
            except OSError:
                pass
            return 1
        time.sleep(0.5)
    return child.returncode or 0


if __name__ == "__main__":
    sys.exit(main())
