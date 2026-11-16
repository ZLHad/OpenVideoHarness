**A change is noted in its own file under `changes/`, so two PRs no longer collide on CHANGELOG.md**
- Why: in two days eight PRs from parallel sessions landed, and nearly every one conflicted at the top of `CHANGELOG.md`, because each added its entry on the first line under `## Unreleased`. Each conflict meant merging main again and running CI again.
- A PR adds `changes/<name>.md`: one entry written as before, its bold title on the first line and its lines below. `changes/README.md` shows one.
- `python3 tools/changes.py show` prints what changed since the last release, newest first (`--titles` for a list); `show vX.Y.Z` prints one release's section; `check` holds each note to one entry with a title and lines (`tools/ci.sh` runs it).
- `python3 tools/changes.py release vX.Y.Z [--date …] [--dry-run]` gathers the notes into `## vX.Y.Z — <date>` at the top of `CHANGELOG.md`, deletes them, and writes the version and the date into `CITATION.cff`. A note's age is the commit that added it.
- `tools/land.py ready` takes the squash message from the note the PR adds. A note it only edits, or `changes/README.md`, is not its own.
- Until the PRs written the old way have landed, both ways count: an entry added under `## Unreleased` still gives the squash message, and a release takes those entries too, after the notes. `CHANGELOG.md` itself is not touched in this change, so open PRs do not conflict with it.
- `CONTRIBUTING.md` (rule 5, landing, the release steps) and the PR template say so.
