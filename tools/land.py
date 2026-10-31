"""Landing a pull request on main: its branch brought up to date, checked and its squash queued; after GitHub merged it,
what landed checked and the branch tidied away. For the maintainer, and for an agent the maintainer told to merge
(CONTRIBUTING.md, 给 agent 的规则).

usage: python3 tools/land.py ready <PR> [--after <commit>] [--dry-run]
       python3 tools/land.py done <PR> [--clean] [--dry-run]

ready, for a PR whose review is done:
  - Brought up to date when its branch lacks main's head: main merged in, in a temporary worktree. --after <commit> names
    the last head of the PR this one was stacked on, squashed into main since. When main's tree is that commit's tree and
    this branch holds the commit, main has nothing the branch lacks: it is merged with -s ours (a plain merge would
    conflict on the squash's copy of the same lines) and the tree must come out unchanged. Otherwise a plain merge; one
    that conflicts stops here with the files named, to be resolved on the branch.
  - Checked: against main it changes only files it changed before (a merge that took in or dropped anything else stops
    it); it adds no file git ignores (.gitignore, .git/info/exclude: LOCAL.md, projects/ and the like); the lines it
    adds, its commit messages, its title and description and the squash message match no line of .git/info/land-deny
    (a regular expression a line, # for a comment). That file is in .git, so each maintainer keeps their own there:
    attribution they do not want, private names and paths. A match is named by file and line number, its text not
    repeated.
  - The merge pushed (only now), the squash message taken from the CHANGELOG.md entry the PR adds: its bold title with
    " (#N)" the subject, its lines the body. A PR adding several entries (a batch) takes its own title as the subject and
    the entries as the body; one adding none (a dependency bump) its title alone.
  - Then draft to ready, and auto-merge, squash, only while the head is the one checked: GitHub merges it when the
    required checks pass. A PR GitHub already finds mergeable is merged at once.
done, after GitHub merged the PR:
  - The squash on main has the tree of the PR's last head (what was tested is what landed), and its message matches no
    line of land-deny. A checkout on main with nothing uncommitted is moved to origin/main.
  - --clean: each worktree with the PR's branch checked out and nothing uncommitted is removed, then the local branch,
    when it holds nothing the PR's last head lacks. Other worktrees (another branch, a detached HEAD) are not touched.
--dry-run says what would be pushed, merged or removed, and does none of it.
Exit: 0 done (ready: queued or merged) · 1 a check failed or the merge conflicted (nothing pushed or queued) · 2 could not
start (no git or gh, not in a repository, the PR not open or not merged, not based on main, from a fork).
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

BASE = "main"
TITLE = re.compile(r"^\*\*(.+?)\*\*\s*$")   # a CHANGELOG entry's title line


class Stop(Exception):   # exit 2: could not start
    pass


class Fail(Exception):   # exit 1: a check failed
    pass


def git(*a):
    p = subprocess.run(["git", *a], capture_output=True, text=True)
    if p.returncode:
        raise Fail(f"git {' '.join(a[:3])}: {(p.stderr or p.stdout).strip()[:500]}")
    return p.stdout.strip()


def yes(*a):   # a git question answered by its exit status
    return subprocess.run(["git", *a], capture_output=True).returncode == 0


def has(sha):
    return yes("cat-file", "-e", f"{sha}^{{commit}}")


def tree(rev):
    return git("rev-parse", f"{rev}^{{tree}}")


def short(sha):
    return sha[:7]


def pr_view(n, fields):
    p = subprocess.run(["gh", "pr", "view", str(n), "--json", ",".join(fields)], capture_output=True, text=True)
    if p.returncode:
        raise Stop(f"gh pr view {n}: {(p.stderr or p.stdout).strip()[:300]}")
    return json.loads(p.stdout)


def deny_patterns():
    f = Path(git("rev-parse", "--git-common-dir")) / "info" / "land-deny"
    pats = []
    if f.is_file():
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip() and not line.lstrip().startswith("#"):
                try:
                    pats.append((i, re.compile(line.strip())))
                except re.error as e:
                    raise Stop(f"{f}, line {i}: not a regular expression ({e})")
    return pats


def denied(pats, where, text):
    return [f"{where} matches land-deny line {i}" for i, p in pats if p.search(text)]


def added_lines(base, head, *paths):
    """(file, hunk, line) for each line the diff from base to head adds; hunk numbers the diff's hunks."""
    out, f, h = [], None, 0
    for line in git("diff", "--unified=0", "--no-color", "--no-ext-diff", base, head, "--", *paths).splitlines():
        if line.startswith("+++ "):
            f = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            h += 1
        elif line.startswith("+") and f:
            out.append((f, h, line[1:]))
    return out


def squash_message(n, title, lines):
    """The squash's subject and body from the CHANGELOG.md lines the PR adds, (hunk, line) each. Only the hunks that add
    an entry's bold title count: an edit to an older entry further down is not this PR's entry."""
    hunks = {h for h, t in lines if TITLE.match(t)}
    entry = [t for h, t in lines if h in hunks]
    at = [i for i, t in enumerate(entry) if TITLE.match(t)]
    if not at:
        return f"{title} (#{n})", ""
    if len(at) == 1:
        return f"{TITLE.match(entry[at[0]]).group(1)} (#{n})", "\n".join(entry[at[0] + 1:]).strip("\n")
    return f"{title} (#{n})", "\n".join(TITLE.match(t).group(1) if TITLE.match(t) else t for t in entry).strip("\n")


def merge_main(n, branch, head, main, after):
    """main merged into the branch's head in a temporary worktree; the new commit, not pushed."""
    ours = False
    if after:
        if not has(after):
            subprocess.run(["git", "fetch", "-q", "origin", after], capture_output=True)
        if not has(after):
            raise Stop(f"--after {after}: no such commit here or on origin")
        after = git("rev-parse", f"{after}^{{commit}}")
        if not yes("merge-base", "--is-ancestor", after, head):
            raise Stop(f"--after {short(after)} is not in #{n}'s branch")
        ours = tree(after) == tree(main)
        print(f"main's tree is {short(after)}'s: main merged with -s ours" if ours else
              f"main has changed since {short(after)} was squashed into it: a plain merge")
    tmp = tempfile.mkdtemp(prefix="land-")
    w = os.path.join(tmp, "w")
    git("worktree", "add", "-q", "--detach", w, head)
    try:
        msg = f"Merge {BASE} into {branch}"
        if ours:
            git("-C", w, "merge", "-q", "-s", "ours", "--no-edit", "-m", msg, main)
        else:
            p = subprocess.run(["git", "-C", w, "merge", "-q", "--no-edit", "-m", msg, main], capture_output=True, text=True)
            if p.returncode:
                files = git("-C", w, "diff", "--name-only", "--diff-filter=U").split()
                subprocess.run(["git", "-C", w, "merge", "--abort"], capture_output=True)
                raise Fail(f"merging {BASE} into {branch} conflicts in {', '.join(files) or 'what git said: ' + p.stderr.strip()[:200]}"
                           f": resolve it on the branch (git merge origin/{BASE}), push, and run this again")
        new = git("-C", w, "rev-parse", "HEAD")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", w], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    if ours and tree(new) != tree(head):
        raise Fail(f"the -s ours merge changed the tree of {short(head)}")
    return new


def ready(n, after, dry):
    pr = pr_view(n, ["number", "title", "body", "state", "isDraft", "baseRefName", "headRefName", "headRefOid",
                     "isCrossRepository"])
    if pr["state"] != "OPEN":
        raise Stop(f"#{n} is {pr['state'].lower()}" + (": python3 tools/land.py done" if pr["state"] == "MERGED" else ""))
    if pr["baseRefName"] != BASE:
        raise Stop(f"#{n} is based on {pr['baseRefName']}, not {BASE}: land the PR under it first")
    if pr["isCrossRepository"]:
        raise Stop(f"#{n} comes from a fork: its branch is not pushed from here")
    branch, head = pr["headRefName"], pr["headRefOid"]
    git("fetch", "-q", "origin")
    if not has(head):
        raise Stop(f"#{n}'s head {short(head)} is not on origin's {branch}")
    main = git("rev-parse", f"origin/{BASE}")
    print(f"#{n} {branch} at {short(head)}, {BASE} at {short(main)}")
    before = set(git("diff", "--name-only", f"{main}...{head}").split("\n")) - {""}
    new = head if yes("merge-base", "--is-ancestor", main, head) else merge_main(n, branch, head, main, after)

    problems = []
    now = set(git("diff", "--name-only", main, new).split("\n")) - {""}
    if now - before:
        problems.append(f"against {BASE} it now changes what the PR did not: {', '.join(sorted(now - before)[:8])}")
    adds = git("diff", "--name-only", "--diff-filter=AR", main, new)
    if adds:
        p = subprocess.run(["git", "check-ignore", "--no-index", "--stdin"], input=adds, capture_output=True, text=True)
        problems += [f"it adds {f}, which git ignores" for f in p.stdout.split("\n") if f]
    lines = added_lines(main, new)
    subject, body = squash_message(n, pr["title"], [(h, t) for f, h, t in lines if f == "CHANGELOG.md"])
    pats = deny_patterns()
    for i, p in pats:
        hits = sorted({f for f, h, t in lines if p.search(t)})
        if hits:
            problems.append(f"lines it adds to {', '.join(hits[:5])} match land-deny line {i}")
    problems += denied(pats, "a commit message on the branch", git("log", "--format=%B", f"{main}..{new}"))
    problems += denied(pats, "the PR's title", pr["title"]) + denied(pats, "the PR's description", pr["body"] or "")
    problems += denied(pats, "the squash message", f"{subject}\n{body}")
    if problems:
        raise Fail("not landed:\n  " + "\n  ".join(problems))
    print(f"checked: {len(now)} file(s) against {BASE}, all the PR's own; none ignored; land-deny: "
          + (f"{len(pats)} pattern(s), none matched" if pats else "no .git/info/land-deny here"))
    print(f"squash: {subject}" + (f" + {len(body.splitlines())} line(s)" if body else ", no body"))
    if dry:
        print(f"dry run: would push {short(new)} to {branch}, mark it ready and queue the squash" if new != head else
              f"dry run: would mark #{n} ready and queue the squash of {short(new)}")
        return
    if new != head:
        git("push", "-q", "origin", f"{new}:refs/heads/{branch}")
        print(f"pushed {short(new)} to {branch}")
    if pr["isDraft"]:
        p = subprocess.run(["gh", "pr", "ready", str(n)], capture_output=True, text=True)
        if p.returncode:
            raise Fail(f"gh pr ready {n}: {(p.stderr or p.stdout).strip()[:300]}")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(body)
    try:
        merge = ["gh", "pr", "merge", str(n), "--squash", "--match-head-commit", new, "--subject", subject, "--body-file", f.name]
        p = subprocess.run(merge + ["--auto"], capture_output=True, text=True)
        if p.returncode == 0:
            print(f"queued: GitHub squashes {short(new)} into {BASE} when the required checks pass")
        elif "clean status" in p.stderr + p.stdout:   # already mergeable: auto-merge has nothing to wait for
            p = subprocess.run(merge, capture_output=True, text=True)
            if p.returncode:
                raise Fail(f"gh pr merge {n}: {(p.stderr or p.stdout).strip()[:300]}")
            print(f"merged: #{n} was already mergeable")
        else:
            raise Fail(f"gh pr merge {n} --auto: {(p.stderr or p.stdout).strip()[:300]}")
    finally:
        os.unlink(f.name)


def worktrees():
    out, cur = [], {}
    for line in git("worktree", "list", "--porcelain").split("\n") + [""]:
        if not line:
            if cur:
                out.append(cur)
            cur = {}
        else:
            k, _, v = line.partition(" ")
            cur[k] = v
    return out


def done(n, clean, dry):
    pr = pr_view(n, ["number", "state", "headRefName", "headRefOid", "mergeCommit"])
    if pr["state"] != "MERGED":
        raise Stop(f"#{n} is {pr['state'].lower()}, not merged" + (": python3 tools/land.py ready" if pr["state"] == "OPEN" else ""))
    branch, head, m = pr["headRefName"], pr["headRefOid"], (pr.get("mergeCommit") or {}).get("oid", "")
    git("fetch", "-q", "origin")
    if not has(head):   # its branch deleted on merge: GitHub keeps the PR's head under refs/pull
        subprocess.run(["git", "fetch", "-q", "origin", f"refs/pull/{n}/head"], capture_output=True)
    if not (m and has(m) and has(head)):
        raise Stop(f"#{n}'s squash {short(m) or '(none)'} or last head {short(head)} is not in this clone")
    problems = []
    if not yes("merge-base", "--is-ancestor", m, f"origin/{BASE}"):
        problems.append(f"{short(m)} is not on origin/{BASE}")
    if tree(m) != tree(head):
        problems.append(f"the squash {short(m)} has not the tree of the PR's last head {short(head)}: what landed is not what was tested")
    problems += denied(deny_patterns(), f"the message of {short(m)}", git("log", "-1", "--format=%B", m))
    if problems:
        raise Fail("\n  ".join([f"#{n}:"] + problems))
    print(f"#{n} landed as {short(m)}, the tree of its last head {short(head)}")
    here = os.path.realpath(git("rev-parse", "--show-toplevel"))
    on = git("rev-parse", "--abbrev-ref", "HEAD")
    if on != BASE or git("status", "--porcelain"):
        print(f"this checkout ({on}{', with changes' if on == BASE else ''}) left where it is")
    elif dry:
        print(f"dry run: would move {BASE} to origin/{BASE}")
    else:
        git("merge", "-q", "--ff-only", f"origin/{BASE}")
        print(f"{BASE} moved to {short(git('rev-parse', 'HEAD'))}")
    if not clean:
        return
    for w in worktrees():
        p = w.get("worktree", "")
        if w.get("branch") != f"refs/heads/{branch}":
            continue
        if os.path.realpath(p) == here:
            print(f"left {p}: it is this checkout")
        elif git("-C", p, "status", "--porcelain"):
            print(f"left {p}: it has uncommitted changes")
        elif not yes("merge-base", "--is-ancestor", w.get("HEAD", ""), head):
            print(f"left {p}: it has commits the PR's last head lacks")
        elif dry:
            print(f"dry run: would remove the worktree {p}")
        else:
            subprocess.run(["git", "worktree", "unlock", p], capture_output=True)   # one an agent's run locked
            git("worktree", "remove", p)
            print(f"removed the worktree {p}")
    if not yes("rev-parse", "--verify", "-q", f"refs/heads/{branch}"):
        return
    if any(w.get("branch") == f"refs/heads/{branch}" for w in worktrees()):
        print(f"left the branch {branch}: a worktree still has it checked out")
    elif not yes("merge-base", "--is-ancestor", f"refs/heads/{branch}", head):
        print(f"left the branch {branch}: it has commits the PR's last head lacks")
    elif dry:
        print(f"dry run: would delete the branch {branch}")
    else:
        git("branch", "-q", "-D", branch)
        print(f"deleted the branch {branch}")


def main():
    ap = argparse.ArgumentParser(prog="tools/land.py", description="Land a pull request on main, then check and tidy up.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("ready", help="bring the PR up to date, check it, queue its squash")
    r.add_argument("pr", type=int)
    r.add_argument("--after", metavar="COMMIT", help="the last head of the PR this one was stacked on, now squashed into main")
    r.add_argument("--dry-run", action="store_true")
    d = sub.add_parser("done", help="check what landed; move main; with --clean, remove the PR's branch and worktrees")
    d.add_argument("pr", type=int)
    d.add_argument("--clean", action="store_true")
    d.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for tool in ("git", "gh"):
        if not shutil.which(tool):
            print(f"land: no {tool} on PATH", file=sys.stderr)
            sys.exit(2)
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode:
        print("land: not in a git repository", file=sys.stderr)
        sys.exit(2)
    os.chdir(top.stdout.strip())
    try:
        if a.cmd == "ready":
            ready(a.pr, a.after, a.dry_run)
        else:
            done(a.pr, a.clean, a.dry_run)
    except Stop as e:
        print(f"land: {e}", file=sys.stderr)
        sys.exit(2)
    except Fail as e:
        print(f"land: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
