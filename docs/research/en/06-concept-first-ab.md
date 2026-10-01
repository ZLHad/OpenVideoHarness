# 06 · Does concept-first pay off? One request, floors only against the workflow

*Written 2026-10-02 · Status: the concept-first workflow is merged ([#44](https://github.com/ZLHad/OpenVideoHarness/pull/44), [#45](https://github.com/ZLHad/OpenVideoHarness/pull/45)); the three changes this note led to are in this note's PR; the four films and the review are the author's local files, not in the repo · [中文](../06-concept-first-ab.md)*

## Question

[#44](https://github.com/ZLHad/OpenVideoHarness/pull/44) changed the workflow to "concept first, then style" and split the taste rules into floors and defaults a concept may override. It came from the maintainer's worry that the workflow held Opus 5.5-class models too tight (`cases/oneshot-five.md`). Two questions were left unmeasured:

1. Do films made through the workflow (concept first) have more interesting ideas?
2. Against films that keep only the floors and leave the rest to the model, is the craft better or worse?

## Method

- **Requests**: two, both the one-line kind users send, both silent with no music (no sound layer, so only the picture is compared).
  - Milky Way: 「做一支 30 秒的横屏短片：为什么住在城市里看不到银河。静音也要看得懂，不用配乐。」 (a 30 s landscape short: why you can't see the Milky Way from a city; readable with the sound off, no music)
  - Bakery: 「给一家只卖一种面包的小面包店做一支 20 秒的开业短片，横屏。静音也要看得懂，不用配乐。」 (a 20 s landscape opening film for a small bakery that sells only one bread; readable with the sound off, no music)
- **Two arms**, one film per request each, four films in all. Same model (Claude Opus 5.5, as subagents), HyperFrames 0.8.82, 1920×1080, 30 fps, draft quality, about 45 minutes each.
  - **Arm A, floors only**: not allowed to open the repo's workflow docs (CLAUDE.md, type docs, playbooks, style library, recipes, cases, checklists); only the HyperFrames section of `engines/README.md`. Five floors given: every frame a pure function of t, no invented facts, minimum text size and hold, flash rate, the spec.
  - **Arm B, the workflow**: read CLAUDE.md as finalised in #44 and follow the `quick` path card (the user's words: "快速出一版，不用问我", a quick draft, don't ask me), including the concept step and `playbook/12-ideation.md`.
- **Blind review**: a fresh-context reviewer (the same model, briefed as a harsh motion director) got only the four mp4s, a 1 fps contact sheet, a phone-size contact sheet and a frame-by-frame strip of the first 2 s for each, labelled M-1, M-2, K-1, K-2, without knowing which arm made which or that this was an A/B test. It scored the eight dimensions of the scoring layer (1–10, ≥ 8 means ready to post), compared each pair (more original, better made, which one to post), and rated how similar the two films' core ideas were (0–10). It also measured static stretches by frame-differencing.

Sources: the four subagents' briefs and delivery reports, the two arm-B projects' `DECISIONS.md` and `NOTES.md`, the blind review; all the author's local files, not in the repo. The scoring dimensions are the scoring layer of [`templates/TASTE_CHECKLIST.md`](../../../templates/TASTE_CHECKLIST.md).

## Findings

![Five frames from each of the four films: Milky Way in the top two rows, bakery in the bottom two](../figs/06-four-films.jpg)

*Figure 1 · One film per row, five moments each. M-1 and K-2 are arm B (the workflow), M-2 and K-1 arm A (floors only).*

**1. The concept-first films had newer ideas and worse craft.** For both requests the reviewer found arm B's film more original, and arm A's film better made and the one to post.

| Dimension | Milky Way · B (M-1) | Milky Way · A (M-2) | Bakery · A (K-1) | Bakery · B (K-2) |
|---|---|---|---|---|
| Concept | **7** | 6 | 7 | **8** |
| Hook | 4 | 3 | 5 | 5 |
| Phone readability | 5 | **7** | 7 | **8** |
| Motion | 6 | 6 | **7** | 5 |
| Variety | 4 | 5 | **7** | 4 |
| Composition and finish | 5 | **7** | **7** | 6 |
| Accuracy | 8 | 7 | 8 | 8 |
| Silent clarity | 7 | 8 | **8** | 6 |
| Mean | 5.8 | 6.1 | 7.0 | 6.3 |

None of the four passes (each has at least one score ≤ 5). Both arm-B films score 1 higher on concept, and both score 4 on variety.

**2. Where arm B lost: the slowness its concept chose was not made up for by change inside the frame.** Milky Way B's concept was "the same sky, one knob": a locked-off shot where only the city's light-pollution level changes; its `DECISIONS.md` overrides the type's "one idea per shot, cut on phrases" to get the locked-off shot. Bakery B's concept was "a written stroke becomes a baguette, then the shop sign". By frame-differencing the reviewer found: Milky Way B is unchanged for 0–4.5 s and almost still for 8.5 s at 18.5–27 s; Bakery B spends 5.5 s at 6.5–12 s on a floating baguette while a line of text types on. Both agents mentioned stillness in their delivery reports (Milky Way B adds that `freezedetect` flagged it), but `quick` has no reviewer and no step that asks for it to be fixed, so they shipped as they were.

**3. The other one is text size.** Milky Way B's concept tells its answer through a permanent HUD (light-pollution level, two brightness bars): exactly the readout the concept card declares and that does not count as decoration. But its labels are 7–8 px at phone size, about 40 px at 1920 wide, under the 44 px floor. A concept can change taste, not floors, yet no step measures this: `bin/vh readcheck` checks hold times, not sizes.

**4. Without the workflow, the model comes up with much the same idea.** The Milky Way pair's core ideas rate 8/10 similar: the same city skyline, the lights going off to reveal the Milky Way, a "Milky Way light constant, background rising" bar, and the same paper (Falchi et al., 2016). The bakery pair rates 4/10: both make the character 一 ("one") the core, but arm A goes "a full shelf down to one loaf, whose score line becomes the 一 of the name" and arm B "a written stroke bakes into a baguette, then becomes the shop sign". Concept-first did not conjure ideas the model would not have had; it made a step the model would take anyway a required one, and left a record (each arm-B film wrote 3 concepts, reasons for rejecting 2, and 4–6 taste overrides).

**5. All four hooks are weak** (3–5). Both arms opened slowly: a static question, an empty practice grid, a full shelf slowly emptying. `quick` makes no hook cards, and nothing checks the "hook" line on the concept card.

**6. The cost is about the same.**

| | Milky Way · A | Milky Way · B | Bakery · A | Bakery · B |
|---|---|---|---|---|
| Time | 19.6 min | 19.5 min | 16.3 min | 13.1 min |
| Tokens (subagent total) | 221k | 239k | 189k | 206k |
| Tool calls | 53 | 53 | 42 | 42 |

**7. Two places in the docs were unclear.** Both arm-B agents spent some reasoning on whether the floor "no digital silence mid-film" applies to a silent film the user asked for (both concluded it does not, but the docs did not say); type 02's prompt block asks for caption weight 800, and the local PingFang's heaviest is 600.

Sources: the blind review (scores, pairs, similarity, static stretches by frame-differencing); the four subagents' delivery reports and usage records (time, tokens, tool calls); the two arm-B projects' `DECISIONS.md`. Figure 1 is frames taken from the four mp4s.

## What changed because of it

In this note's PR, all of them steps `quick` was missing, none of them limits on concepts:

- **Three more self-checks in quick** (CLAUDE.md, the quick card's step 5): a phone-size contact sheet for whether required text reads; a frame-by-frame strip of the first 2 s for whether the opening moves from frame 0; and any frozen stretch `bin/vh check` reports is fixed or explained on delivery. The commands follow `playbook/02-verification.md`.
- **A concept cannot change floors; the two most often hit are spelled out** (`playbook/12-ideation.md` §6): the part of a permanent readout that people must read keeps the size floor; a "slow" concept (locked-off shot, long holds) needs change inside the frame, one event every 2–4 s, and any stretch of 3 s or more without change needs a reason.
- **Two clarifications**: the digital-silence floor applies to films with sound; a silent film the user asked for, with no audio track, is outside it (CLAUDE.md, TASTE_CHECKLIST #18); type 02's weight reads "800, or the heaviest the local font has".

## Limitations and open questions

- **A tiny sample**: two requests, one film per cell, one run. The model makes a different film every run, and one film's scores probably move 1–2 points between runs (not measured here). The differences are a direction, not a conclusion.
- **The reviewer is a model too**: the same model briefed as a reviewer, not people. How well its judgement of "original" and "well made" matches a human's is unknown.
- **Only `quick` was compared**: `standard` and `studio` have human gates and a reviewer that should catch findings 2 and 3 in the scoring layer, but they were not run.
- **Only the picture was compared**: both requests asked for no sound, so the sound half of the workflow (score, foley, mix) is not in it.
- **Arm A is not "clean"**: the subagents may have had the repo's CLAUDE.md in their context and were only told not to follow it; they read the HyperFrames section of `engines/README.md`, which carries some habits of its own.
- **"Concept" is the thing under test**: the reviewer scored with the scoring layer, whose first dimension, concept, #44 added. Part of arm B's edge there may come from writing ideas the way the scoring layer asks for. The pairwise "more original" judgement does not depend on that dimension and agrees.
