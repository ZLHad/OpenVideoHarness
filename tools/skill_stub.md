
# @NAME@

Harness path (set by install.sh): @HARNESS@

This installed file is a stub; the skill itself lives in the OpenVideoHarness clone, so it is current after every `git pull`
there, with nothing to reinstall. Before anything else:

1. Find the harness: the first of `$OVH_DIR`, the path on the line above, `~/OpenVideoHarness` and the current working
   directory that has `bin/vh` in it.
2. Read `<harness>/skills/@NAME@/SKILL.md` and follow it in place of this file.

If none of those folders has it, the clone has been moved or removed. Ask the user where it is now; from there,
`bin/vh install-skill` points this stub at it again (or set `OVH_DIR`). With no clone at all, ask before installing one:

```bash
curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
```
