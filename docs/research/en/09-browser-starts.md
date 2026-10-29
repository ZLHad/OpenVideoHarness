# 09 · How many Chromes an edit list starts: measured, and not shared for now

*Recorded 2026-10-29 · Status: numbers only, no code changed; this note's PR adds just the note · [中文](../09-browser-starts.md)*

## Question

The page tools start a headless Chrome of its own for every page they open (`openFilm` in `tools/film/host.mjs`) and close it when done. An edit list with many pages makes render, determinism and cues start many browsers. How many does each start, and how much of the time goes on those cold starts? If it is a lot, the pages of one edit list could share one browser, a tab each.

## Method

- A test edit list: 12 page entries of 1.5 s, each its own page on its own clock, 1920×1080, 18 s and 540 frames in all. Every frame of every page draws a gradient, 400 translucent circles and a line of text, all from t alone. A second copy at 160×90, the size of CI's fixtures.
- Counting: `CHROME_PATH` points to a stand-in script that notes the start and execs the real Chrome. Each command's starts and its time are recorded.
- Pricing, the median of 6 each: a) `openFilm` opens the page, draws a frame and closes, which is what every page goes through now; b) a start alone, a close alone; c) a new tab in a browser already running, in a browser context of its own, set up the same way, drawing the same frame, then closed. a − c is what each page would save with a shared browser.
- Three machines: this M3 Max with Chrome 156; GitHub's ubuntu-latest and macos-latest, in one `workflow_dispatch` on a throwaway branch, deleted after.
- The whole CI suite: one `tools/ci.sh --committed` here with the same stand-in, noting which process started each browser.

## Findings

1. **How many**: the same on all three machines (table 9.1), since the count follows the code, not the machine. For a 12-page edit list:
   - render starts 24. Reading each page's length and data takes 12, one page after another; then each worker starts another whenever it reaches a page.
   - determinism starts 50. Each of its passes A, B, C and D opens the pages one by one. B reuses A's, but that keeps at most two pages open, so walking back through the film opens them again.
   - cues starts 12, frames at 6 moments 7, a patch of one span 2, a render of one page alone 1.
2. **The price** (table 9.2): a browser of its own costs 0.37 s more per page than a tab in a running one on this machine, 0.41 s on the Linux runner and 1.67 s on the macOS runner. For the 160×90 pages it is 0.33 s and 1.33 s on the two runners.
3. **What sharing would save**: the starts saved times a − c. The data step goes one page after another, so it counts in full; while drawing, 4 workers run side by side, so divide by 4 (table 9.3).
   - render: on this 18 s test list about 5 s here, 20%. For a 3-minute film of the same 12 pages only 2–3%: the drawing grows with the film's length, the starts do not.
   - determinism: from 50 starts to 3 (one for A and B, one each for C and D, which start their own browsers by design). About 17 s here, 26%; about 79 s on the macOS runner, 30%.
   - cues: from 12 to 1, about 4 s here, 71%.
4. **The CI suite would save little**: one full run starts 321 browsers from 216 processes. 165 of the starts come from the 60 processes that started more than one, but most of those are one browser a worker already (a page's render starts as many as `--workers`), and determinism's three are by design. Only 18 starts are extra: at the macOS runner's price, about 30 s over both shards.
5. **Seen in passing**: Chrome on the macOS runner updated itself during the job, from 155.0.8059.40 to 156.0.8078.49. The chunk cache's key holds the browser's version, so the "chunk cache taking all" render after the update took no chunk and drew the whole list again, starting 24 browsers. CI's chunk cache checks would do the same if an update fell between their two renders.

Table 9.1 · The 12-page test edit list (1920×1080, 540 frames): each command's browser starts and its time

| command | starts | this M3 Max | Linux runner | macOS runner |
|---|---|---|---|---|
| render (4 workers) | 24 | 24.4 s | 79.0 s | 139.4 s |
| render --fresh --workers 1 | 24 | 45.0 s | 86.0 s | 553.4 s |
| render, the chunk cache taking all | 13 | 7.7 s | 9.8 s | 118.2 s (Chrome updated meanwhile: no chunk taken, 24 starts) |
| determinism | 50 | 66.5 s | 110.6 s | 263.3 s |
| cues | 12 | 5.7 s | 7.2 s | 28.5 s |
| frames, 6 moments | 7 | 5.0 s | 6.8 s | 26.0 s |
| patch --shot S06 | 2 | 4.4 s | 5.5 s | 10.8 s |
| one page rendered alone (4 workers) | 1 | 4.5 s | 8.6 s | 17.3 s |

Table 9.2 · Opening a page, drawing a frame, closing it (1920×1080, the median of 6)

| | this machine | Linux runner | macOS runner |
|---|---|---|---|
| a) a browser of its own (as now) | 738 ms | 1040 ms | 2953 ms |
| of it, the start alone, the close alone | 289 ms, 59 ms | 181 ms, 152 ms | 1289 ms, 379 ms |
| c) a new tab in a running browser | 371 ms | 627 ms | 1282 ms |
| a − c: what a shared browser saves a page | 367 ms | 413 ms | 1671 ms |

Table 9.3 · Estimated with a shared browser (a − c times the starts saved)

| command | starts when shared | saved here | saved on the macOS runner |
|---|---|---|---|
| render (4 workers) | 5 (1 for the data, 1 a worker) | about 5 s (20%; 2–3% for a 3-minute film) | about 22 s (16%) |
| determinism | 3 (1 for A and B, 1 each for C and D) | about 17 s (26%) | about 79 s (30%) |
| cues | 1 | about 4 s (71%) | about 18 s (64%) |
| the whole CI suite | 18 fewer (of 321) | — | about 30 s over both shards |

## What changed

- No code. The line drawn beforehand: if real films get only a few percent faster, record the numbers and leave it. A real film's render gets 2–3% faster. The bigger savings are determinism's and cues', a few seconds to a dozen or so a run on a Mac; a CI shard saves a dozen seconds or so. For that, the host every page tool shares would have to let several pages live in one browser, and every frame being a function of t alone would have to be shown again: not worth it.
- If it is done one day, the data step first (`allFacts` in `tools/film/edit.mjs`): it draws no picture, starts as many browsers as there are pages, and starts them one after another. Then `EditFilm`: a browser a worker, a tab and a browser context a page. Both need the host's event listeners split by session first: the host listens on the browser for every session's errors, so with several pages in one browser one page's errors would land on another.

## Still unclear

- Whether, with two tabs open in one browser, the one not in front is throttled. The host waits for two `requestAnimationFrame`s with every frame; if they never come, drawing stops. The old and the new headless mode may differ here; not tried.
- How the chunk cache's key would go with a shared browser: it already holds the hashes of host.mjs and browser.mjs, so changing that code redraws every chunk once. Whether it should also say that a page was drawn in a browser that had drawn others depends on whether the same page comes out byte for byte the same in a fresh browser and in a used one. Not compared.
- On the macOS runner the 160×90 copy rendered slower with 4 workers than with 1, 468.8 s against 129.3 s. Not looked into.
- The CI suite's starts were counted on this machine. The count follows the code, so the macOS runner's time was estimated from the same count, not counted again on the runner.

**Sources**: measured on this machine, 2026-10-29; one `workflow_dispatch` on GitHub's runners (run 40818048888, a throwaway branch, deleted after). The script that makes the test edit list, the stand-in Chrome and the pricing script are on the author's machine and not in the repo; browsers are started in `tools/film/host.mjs` (`openFilm`), `tools/film/edit.mjs` (`allFacts`, `EditFilm`) and `tools/film/determinism.mjs`.
