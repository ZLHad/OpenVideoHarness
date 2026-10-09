# A five-minute demo of OpenVideoHarness

`index.html` is a one-page site for presenting the project in about five minutes: why it exists, what it adds, the architecture, the intro film, the films it made, the style library, who wrote it, how the author uses it, and how to start. Claude wrote the page and the script below.

## Before the talk

1. Open the page from a clone of the repo: it reads the style samples and contact sheets from `../../styles` and `../../showcase`. Chrome works best; `F` goes full screen.
2. Put the films on disk so nothing streams over the venue's network:
   ```bash
   tools/fetch_media.sh 00-promo 01-hand 02-short 03-math 04-intro   # about 320 MB, mostly the 103 s intro film
   ```
   Without them the page streams from the GitHub release. Press `N` on the film section: the notes say which source it is using.
3. Your own material, all optional:
   - **WeChat QR**: save it as `docs/talk/img/wechat.jpg` and the "Say hi on WeChat" card appears next to the GitHub QR. Without the file the card stays hidden; with notes on, the page says it is missing. Committing the image makes it public with the repo.
   - **Douyin and Bilibili links**: paste them into the two empty `href=""` in the "In the wild" section.
   - **The Nobel explainer**: put the file at `docs/talk/media/nobel.mp4` (git ignores that folder) and a player shows up in the "In the wild" section.
4. Check the time once: `T` starts the timer, `R` resets it.

## Keys

| Key | Does |
|---|---|
| `→` `↓` `PgDn` (a clicker) | next section |
| `←` `↑` `PgUp` | previous section |
| `Space` | play or pause the film on the film section; next section elsewhere |
| `1`–`9`, `0` | jump to section 1–9, 10 |
| `N` | speaker notes for the current section (and the film's source) |
| `T` / `R` | start or pause the timer / reset it |
| `F` | full screen |
| `?` | the key list |

The notes panel is on the shared screen too, so turn it off before you present if the screen is mirrored.

## The script (about 4.5 minutes, the film included)

About 300 words of speech (2:20 at a relaxed pace) plus the 1:43 film. "Be done by" is when to move on.

**1 · Title** (be done by 0:15)
> Hi everyone. This is OpenVideoHarness: a video workbench for Claude Code.
> Our motto: not more tools. Know-how.

**2 · Why** (0:50)
> It started with Opus 5.5. Its video code has real taste: motion, type, pacing.
> We already have great engines, like HyperFrames and Remotion. But an engine just renders frames. It doesn't give you the idea, the storyboard, the script, or the style.
> So I talked it through with Claude, and we built that missing layer: the whole workflow, from idea to final cut.

**3 · Features** (1:15) *optional: drag the f(t) slider while you talk*
> What does it add? It starts with ideas, not code. It has nine workflows, one for each kind of video. You sign off three times: direction, storyboard, draft.
> And since Claude can't watch video, it checks its own frames and audio, and a second Claude scores the draft.

**4 · Architecture** (1:35)
> The architecture is simple. Claude Code reads CLAUDE.md, our router. It picks a video type, pulls in the playbook, styles and templates, and drives the engines through one CLI.
> And every project writes its lessons back into the docs.

**5 · The intro film** (3:25) *Space to play; the page dims while it plays*
> Here's our intro film. Claude made it with the harness itself.
>
> *(1:43 of film)*

**6 · Works** (3:45) *click "What Claude sees" on the second sentence*
> A few more films, each from one sentence: a science short, a 3Blue1Brown-style explainer, and Clawd, hand-drawn.
> And this is what Claude sees when it reviews them: not video. Contact sheets.

**7 · Styles** (3:55) *skip this line if you are short on time*
> Plus thirty-one styles to borrow from, so not every film looks the same.

**8 · Built by Claude** (4:15)
> And the code? In nine days the repo got seventy-three pull requests. Seventy came from Claude.
> I bring the taste and the decisions. Claude writes the rest.

**9 · In the wild** (4:35)
> I use it myself, too. I post films made with it on Douyin and Bilibili.
> When this year's Nobel Prize in Physics was announced, I had an explainer out about three hours later.

**10 · Get started** (4:50) *leave the QR codes up for questions*
> It's open source. One line to install, then just ask Claude Code for a video.
> Thank you!

## Where the numbers come from

- 73 pull requests, 70 from `claude/` branches and 3 from Dependabot, opened 2026-09-29 to 2026-10-07 (UTC): the repo's pull request list, read on 2026-10-09. The per-day chart and the ticker come from the same list.
- 9 video types, 13 playbook docs, 11 templates, 31 styles, 24 shot recipes: `video-types/`, `playbook/`, `templates/`, `styles/`, `bin/vh recipes list`.
- The intro film (103 s; a Blender opening of 1.18 million stars over 475 frames; 124 sound effects) and the four other films: `showcase/*/README.md`.
- 389 community films with their prompts: `cases/opus55-gallery.md`.
- Twenty checks and eight review scores: `templates/TASTE_CHECKLIST.md`. Effort levels and their times: `README.md`.
- The Nobel explainer, its timing, and the Douyin and Bilibili channels are the author's own account.

## How the page is built

One HTML file with inline CSS and JS and no build step. Fonts come from Google Fonts; offline, it falls back to system fonts. The opening galaxy draws the 31 style posters on a canvas, with no randomness (positions come from a seeded hash). The f(t) panel draws its frame as a pure function of `t`, and its "Render it again" button redraws that frame right after another one and compares every pixel. Motion stops when a section is off screen, and `prefers-reduced-motion` turns it off. `img/` holds five poster frames taken from the showcase films (`ffmpeg -ss … -frames:v 1`).
