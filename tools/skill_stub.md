
# @NAME@

Harness path (set by install.sh): @HARNESS@

This installed file is a stub; the skill itself lives in the OpenVideoHarness clone, so it is current after every `git pull`
there, with nothing to reinstall. Before anything else:

1. Find the harness. Use `$OVH_DIR` if it names a checkout. Next use the OpenVideoHarness checkout containing the
   current working directory, if there is one. Otherwise try the path on the line above and then `~/OpenVideoHarness`.
   A checkout contains `bin/vh` and a `skills/` directory.
2. Read `<harness>/skills/@NAME@/SKILL.md` and follow it in place of this file.

If the harness is there but `skills/@NAME@/SKILL.md` is not, this skill was renamed or removed: say so to the user, and
run `bin/vh install-skill` in the harness, which writes the skills it has now and removes stubs like this one.

If none of those folders has `bin/vh`, the clone has been moved or removed. Ask the user where it is now; from there,
`bin/vh install-skill` points this stub at it again (or set `OVH_DIR`). With no clone at all, ask before installing one:

```bash
curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
```
