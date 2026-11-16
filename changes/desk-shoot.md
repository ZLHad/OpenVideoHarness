**`tools/desk/shoot.py` takes the console's screenshots for a review from pictures alone**
- Why: the console's acceptance worked best as full-size screenshots on several projects, read page by page by a person or a reviewer that sees only the pictures. The script that took them lived in a temporary folder.
- `uv run --no-project --with playwright python3 tools/desk/shoot.py <desk url> <folder>` takes the space, each film as it opens and each module of its rail (a second picture where a column scrolls), the cut with a shot selected, its three layouts and the summary before submitting, the three themes, English, and a phone 390 wide; `index.json` says what each picture shows.
- It drives the system Chrome; Playwright is fetched by uv for the run alone. Without either it says so in a line (exit 2). It is not a `bin/vh` command and CI does not run it.
- Buttons are found by their words, Chinese or English, or their role, never by position, so a column laid out anew still works; a step whose button is gone is listed as skipped with why. Every POST to the feedback is blocked, so nothing can be submitted.
- `tools/desk/README.md` says how to use it.
