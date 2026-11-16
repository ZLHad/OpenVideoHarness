"""Run a command with a terminal of its own, for the checks: --print-address (bin/vh studio, desk, desk link, gate) writes
its address to the terminal alone, and a check's shell has none. What the command writes to its terminal (/dev/tty) comes
out on this one's stdout (--to FILE: in that file, so a check tells the two apart). The command takes this process's place
(its pid is this one's), so a check stops it as before.

  python3 tools/desk/fixtures/with_tty.py [--to FILE] <command> [args…]
"""
import fcntl, os, sys, termios


def main(argv):
    out = 1
    if argv[:1] == ["--to"] and len(argv) > 1:
        out, argv = os.open(argv[1], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), argv[2:]
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        os.setsid()   # a session of its own, to take a terminal; a process-group leader cannot: one level down
    except OSError:
        pid = os.fork()
        if pid:
            _, st = os.waitpid(pid, 0)
            return os.waitstatus_to_exitcode(st)
        os.setsid()
    master, slave = os.openpty()
    t = termios.tcgetattr(slave)
    t[1] &= ~termios.OPOST   # its lines as written (no \r added)
    termios.tcsetattr(slave, termios.TCSANOW, t)
    if os.fork() == 0:   # the copier: the terminal's output to stdout, until the command and all it started let go of it
        os.close(slave)
        while True:
            try:
                data = os.read(master, 4096)
            except OSError:
                break
            if not data:
                break
            os.write(out, data)
        os._exit(0)
    os.close(master)
    if out != 1:
        os.close(out)
    try:
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
    except OSError:
        pass
    os.set_inheritable(slave, True)   # held open by the command: the terminal lives as long as it does
    os.execvp(argv[0], argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
