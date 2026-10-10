# The OpenVideoHarness homepage

`index.html` is the project's homepage, in English and Chinese. It covers:

- getting started;
- why the project exists;
- what it adds and how it works;
- the intro film and four showcase films;
- the 31-style library;
- how the author uses it;
- an FAQ, and contact details.

It is one HTML file with no build step.

## Viewing it

GitHub's file view shows the HTML source, not the page. To see the page:

- **On GitHub Pages**: in Settings → Pages, set Source to "Deploy from a branch", pick `main` and `/ (root)`, and save.
  - A minute later the site is at <https://zlhad.github.io/OpenVideoHarness/>. The `index.html` at the repo root redirects to <https://zlhad.github.io/OpenVideoHarness/docs/site/>.
  - The old address, `…/docs/talk/`, redirects here too.
  - The empty `.nojekyll` at the repo root makes Pages serve the files as they are.
  - Online, the films stream from the `media` release.
- **From a clone**: open `docs/site/index.html` in Chrome. It reads the style samples and contact sheets from `../../styles` and `../../showcase`.
  - With `tools/fetch_media.sh 00-promo 01-hand 02-short 03-math 04-intro` (about 320 MB, mostly the 103 s intro film), the films play from disk instead of streaming.

## Languages

The EN / 中 switch in the top bar changes the page in place.

- **First visit**: the page follows the browser's language (Chinese for any `zh-*`, English otherwise).
- **Later visits**: the choice is remembered in `localStorage` (`ovh-lang`).
- **In a link**: `?lang=en` or `?lang=zh` picks the language for that link, e.g. `…/docs/site/?lang=zh` for a Chinese audience.

To edit the text:

- **Text on the page** is written twice, side by side: `<span lang="en">…</span><span lang="zh">…</span>`. CSS shows the one that matches `<html data-lang>`; without JavaScript the page is English. Change both, and keep the same markup (`<em>`, `<strong>`, `<code>`) in each.
- **Section names** in the side rail come from each section's `data-en` / `data-zh`.
- **Labels that are attributes** (`aria-label`) come from `data-aria-en` / `data-aria-zh`.
- **Strings the script writes** are in `T` at the top of the script: the f(t) readout and check, the copy buttons, captions. The style names are in `STYLES`, as `[folder, English, Chinese]`.

## Optional material

All of it is optional. The page works without any of it.

- **WeChat QR**: save it as `docs/site/img/wechat.jpg`. The "Say hi on WeChat" card then appears next to the GitHub QR in the Contact section; without the file the card stays hidden. Committing the image makes it public with the repo.
- **Douyin and Bilibili links**: paste them into the two empty `href=""` in the "In practice" section. Left empty, the names show without a link.
- **A local film**: a file at `docs/site/media/nobel.mp4` shows up as a player in "In practice". Git ignores that folder, so the player appears only on your machine, never online.

## Where the numbers come from

- **Counts of things in the repo**: 9 video types, 13 playbook docs, 11 templates, 31 styles, 24 shot recipes. Source: `video-types/`, `playbook/`, `templates/`, `styles/`, `bin/vh recipes list`.
- **The films**:
  - the intro film: 103 s; a Blender opening of 1.18 million stars over 475 frames; 124 sound effects;
  - the four other films.

  Source: `showcase/*/README.md`.
- **Community films**: 389, with their prompts. Source: `cases/opus55-gallery.md`.
- **Checks**: the 20-point checklist and the 8 review scores. Source: `templates/TASTE_CHECKLIST.md`.
- **The FAQ's answers**: requirements, cost, times, limits and the A/B result. Source: `README.md` and `docs/research/06-concept-first-ab.md`.
- **The author's own account**: the Nobel explainer, its timing, and the Douyin and Bilibili channels.

## How it is built

- **Assets**: one HTML file with inline CSS and JS. Fonts come from Google Fonts; offline, and for Chinese, it uses the system's fonts. `img/` holds five poster frames from the showcase films (`ffmpeg -ss … -frames:v 1`).
- **The galaxy**: the opening galaxy draws the 31 style posters on a canvas, with no randomness (positions come from a seeded hash).
- **The f(t) panel**: it draws its frame as a pure function of `t`. Its "Render it again" button redraws that frame right after another one and compares every pixel.
- **Motion**: it stops when a section is off screen, and `prefers-reduced-motion` turns it off.
