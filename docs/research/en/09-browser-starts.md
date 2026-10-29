# 09 · How many Chromes an edit list starts: measured, and not shared for now

*Recorded 2026-10-29 · Status: numbers only, no code changed · [中文](../09-browser-starts.md)*

## Question

The page tools start a headless Chrome of its own for every page they open (`openFilm` in `tools/film/host.mjs`) and close it when done. An edit list with many pages makes render, determinism and cues start many browsers. How many does each start, and how much of the time goes on those cold starts? If it is a lot, the pages of one edit list could share one browser, a tab each.

## Method

- Test edit lists: 12 page entries, each its own page on its own clock, 1920×1080. The short one has entries of 1.5 s, 18 s and 540 frames in all; the long one entries of 15 s, 180 s and 5400 frames. Every frame of every page draws a gradient, 400 translucent circles and a line of text, all from t alone. A copy of the short one at 160×90, the size of CI's fixtures. None of this repo's films is made with an edit list, so synthetic lists are all there is to measure.
- Counting: `CHROME_PATH` points to a stand-in script that notes the start and execs the real Chrome. Each command's starts and its time are recorded, one run a row of table 9.1. For the long list, the time of each start and render's own lines split that run into its steps.
- Pricing, the median of 6 each (table 9.2): a) `openFilm` opens the page, draws a frame and closes, which is what every page goes through now; b) a start alone, a close alone; c) a new tab in a browser already running, in a browser context of its own, set up the same way, drawing the same frame, then closed. a − c is what each page would save with a shared browser.
- Three machines: this M3 Max with Chrome 156.0.8078.49; GitHub's ubuntu-latest (ubuntu-24.04, Chrome 156.0.8078.47) and macos-latest (macos-26-arm64), in one `workflow_dispatch` on a throwaway branch, deleted after. GitHub gives them 4 cores (Linux) and 3 (macOS); not measured here.
- The whole CI suite: one `tools/ci.sh --committed` here with the same stand-in, noting which process started each browser and when, then putting each start in the group whose time it fell in.

## Findings

1. **How many**: the same on all three machines (table 9.1), since the count follows the code, not the machine. For the short 12-page list:
   - render starts 24. Reading each page's length and data takes 12, one page after another; then each worker starts another whenever it reaches a page. A page longer than one GOP (60 frames) is cut into chunks, and each worker that draws one of them opens it; and with more than 600 frames to draw, a few chunks are drawn first for an estimate. The long list, 12 pages of 15 s, is cut into 96 chunks and starts 54: 12 for the data, 7 for the first page and the estimate, 35 while drawing.
   - determinism starts 50. Each of its passes A, B, C and D opens the pages one by one. B reuses A's, but that keeps at most two pages open, so walking back through the film opens them again.
   - cues starts 12, frames at 6 moments 7, a patch of one span 2, a render of one page alone 1.
2. **The price** (table 9.2): a browser of its own costs 0.37 s more per page than a tab in a running one on this machine, 0.41 s on the Linux runner and about 1.7 s on the macOS runner. For the 160×90 pages it is 0.33 s and about 1.3 s on the two runners.
3. **What sharing would save**: the starts saved times a − c. The data step goes one page after another, so it counts in full; while drawing, 4 workers run side by side, so divide by 4 (table 9.3).
   - render: on the short 18 s list about 5 s here, about 20% of that command's 24.4 s. On the 3-minute long list sharing leaves 5 starts (1 for the data, 1 a worker). The data, the first page and the estimate go one page after another, so the 17 starts they save count in full, about 6.2 s; the 32 saved while drawing are spread over 4 workers, about 2.9 s; about 9 s in all. render took about 122 s from its start to printing "done" (about 13 s before drawing, 109 s drawing and joining), so that is about 7.5%. It was measured with another check running on the machine.
   - determinism: from 50 starts to 3 (one for A and B, one each for C and D, which start their own browsers by design). About 17 s here, 26%; about 80 s on the macOS runner, around 30%.
   - cues: from 12 to 1, about 4 s here, 71%.
4. **The CI suite would save little**: one full run starts 321 browsers from 216 processes. 165 of the starts come from the 60 processes that started more than one, but most of those are one browser a worker already (a page's render starts as many as `--workers`), and determinism's three are by design. Only 18 are extra: 14 in edit_checks, 3 in edit_footage_checks, 1 in film_engine_checks, all in the second macOS shard. At the macOS runner's price for small pages (1.33 s each), even with none of them overlapping, that is about 24 s.
5. **Seen in passing**:
   - Chrome's version on the macOS runner changed during the job: 155.0.8059.40 at the start, 156.0.8078.49 by the pricing; the log does not say what changed it. The chunk cache's key holds the browser's version, so the "chunk cache taking all" render in table 9.1's third row took no chunk, drew the whole list again and started 24 browsers.
   - Rendering the long list here with Google Chrome, render waited about 4 minutes after printing "done": of its 376.8 s, about 122 s came before "done" and the other 255 s or so were this wait. The crashpad and GoogleUpdater processes Chrome starts held the pipe render reads Chrome's errors from, outlived Chrome, and node waited for that pipe to close. On this machine bin/vh uses HyperFrames' chrome-headless-shell, which starts neither; GitHub's macOS runner has only Google Chrome.

Table 9.1 · The short 12-page test list (1920×1080, 540 frames): each command's browser starts and its time, one run a row

| command | starts | this M3 Max | Linux runner | macOS runner |
|---|---|---|---|---|
| render (4 workers) | 24 | 24.4 s | 79.0 s | 139.4 s |
| render --fresh --workers 1 | 24 | 45.0 s | 86.0 s | 553.4 s |
| render, the chunk cache taking all | 13 | 7.7 s | 9.8 s | 118.2 s (Chrome's version changed before this row: no chunk taken, 24 starts) |
| determinism | 50 | 66.5 s | 110.6 s | 263.3 s |
| cues | 12 | 5.7 s | 7.2 s | 28.5 s |
| frames, 6 moments | 7 | 5.0 s | 6.8 s | 26.0 s |
| patch --shot S06 | 2 | 4.4 s | 5.5 s | 10.8 s |
| one page rendered alone (4 workers) | 1 | 4.5 s | 8.6 s | 17.3 s |

Table 9.2 · Opening a page, drawing a frame, closing it (1920×1080, the median of 6; the macOS column with Chrome 156.0.8078.49)

| | this machine | Linux runner | macOS runner |
|---|---|---|---|
| a) a browser of its own (as now) | 738 ms | 1040 ms | 2953 ms |
| of it, the start alone, the close alone | 289 ms, 59 ms | 181 ms, 152 ms | 1289 ms, 379 ms |
| c) a new tab in a running browser | 371 ms | 627 ms | 1282 ms |
| a − c: what a shared browser saves a page | 367 ms | 413 ms | 1671 ms |

Table 9.3 · Estimated with a shared browser (a − c times the starts saved)

| command | starts when shared | saved here | saved on the macOS runner |
|---|---|---|---|
| render (4 workers) | 5 (1 for the data, 1 a worker) | short list about 5 s (about 20%); long list about 9 s (about 7.5% of its time to "done") | short list about 22 s (about 16%) |
| determinism | 3 (1 for A and B, 1 each for C and D) | about 17 s (26%) | about 80 s (around 30%) |
| cues | 1 | about 4 s (71%) | about 18 s (over 60%) |
| the whole CI suite | 18 fewer (of 321) | — | at most about 24 s, all in the second shard |

## What changed

- No code. The line drawn beforehand: if it gets only a few percent faster, record the numbers and leave it. The 3-minute long list's render gets about 7.5% faster. The bigger savings are determinism's and cues', a few seconds to a dozen or so a run on a Mac; the second CI shard saves at most twenty-odd seconds. For that, the host every page tool shares would have to let several pages live in one browser, and every frame being a function of t alone would have to be shown again: not worth it.
- To save some of it, try a cheaper step first: the data step (`allFacts` in `tools/film/edit.mjs`) starts its browsers one page after another; reading four pages at a time would take most of it away without touching the host. This is reasoned, not measured.
- If a shared browser is ever done, the data step first there too: it draws no picture and starts as many browsers as there are pages. Then `EditFilm`: a browser a worker, a tab and a browser context a page. Both need the host's event listeners split by session first: the host listens on the browser for every session's errors, so with several pages in one browser one page's errors would land on another.

## Still unclear

- Whether, with two tabs open in one browser, the one not in front is throttled. The host waits for two `requestAnimationFrame`s with every frame; if they never come, drawing stops. The old and the new headless mode may differ here; not tried.
- How the chunk cache's key would go with a shared browser: it already holds the hashes of host.mjs and browser.mjs, so changing that code redraws every chunk once. Whether it should also say that a page was drawn in a browser that had drawn others depends on whether the same page comes out byte for byte the same in a fresh browser and in a used one. Not compared.
- CI's chunk cache checks would take no chunk either, as in table 9.1's third row, if Chrome's version changed between their two renders. Not seen in a CI log yet; left as a follow-up, not fixed here.
- How long crashpad and GoogleUpdater holding that pipe make each command wait on the macOS runner was not measured; the fix would be to close the pipe when the browser is closed instead of waiting for it.
- On the macOS runner the 160×90 copy rendered slower with 4 workers than with 1, 468.8 s against 129.3 s. Not looked into.
- The CI suite's starts were counted on this machine. The count follows the code, so the macOS runner's time was estimated from the same count, not counted again on the runner.

**Sources**: measured on this machine, 2026-10-29; one `workflow_dispatch` on GitHub's runners, https://github.com/ZLHad/OpenVideoHarness/actions/runs/40818048888 (a throwaway branch, deleted after). The long list's render was a separate run on this machine. The script that makes the test edit lists, the stand-in Chrome and the pricing script are on the author's machine and not in the repo; browsers are started in `tools/film/host.mjs` (`openFilm`), `tools/film/edit.mjs` (`allFacts`, `EditFilm`), `tools/film/render.mjs` (the chunks dealt to workers) and `tools/film/determinism.mjs`.
