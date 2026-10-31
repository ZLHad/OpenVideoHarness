# The OpenVideoHarness homepage

`index.html` is the project's homepage, in English and Chinese, online at <https://zlhad.top/OpenVideoHarness/docs/site/>. It covers:

- getting started, and what happens at the three stops;
- why the project exists and what it adds, with a live f(t) demo;
- how it works, and the capability map: the tools for thinking, gathering, making, checking and delivering;
- the intro film and the four other showcase films;
- the style library, with a few recipe and component contact sheets;
- in practice: where the author publishes films made with it, the Nobel explainer's three hours, and what each showcase folder records;
- an FAQ, and contact details.

It is one HTML file with no build step.

## Viewing it

GitHub's file view shows the HTML source, not the page. To see the page:

- **On GitHub Pages**: the repo publishes `main` from `/ (root)` (Settings → Pages, "Deploy from a branch"), at the custom domain zlhad.top.
  - The `index.html` at the repo root redirects to `docs/site/`, keeping `?lang=` and `#section`.
  - The old address, `…/docs/talk/`, redirects here too.
  - The empty `.nojekyll` at the repo root makes Pages serve the files as they are.
- **From a clone**: open `docs/site/index.html` in Chrome. It reads the style samples and contact sheets from `../../styles`, `../../components`, `../../recipes` and `../../showcase`.
  - With `tools/fetch_media.sh 00-promo 01-hand 02-short 03-math 04-intro` (about 320 MB, mostly the 103 s intro film), the films play from disk instead of streaming.

## What it loads

Nothing from another site loads with the page, so it opens where Google Fonts, YouTube or a CDN are blocked:

- **Fonts**: the display face (Inter Tight) and the mono face (JetBrains Mono) are in `fonts/`, cut down to Latin and the weights the page uses (23 kB and 12 kB, WOFF2), under the SIL Open Font License 1.1 (`fonts/OFL-*.txt`). They were taken from the google/fonts repository and cut with fontTools (`varLib.instancer`, then `pyftsubset … --flavor=woff2`). Body text and every Chinese character use the system's fonts.
- **Pictures**: all from this repo. `img/` holds five poster frames of the showcase films; `img/styles/` a 384 × 216 copy of each style's poster (about 14 kB each), for the galaxy and the style wall. The 5-second samples (`styles/<slug>/media/swatch.mp4`) load when a tile is hovered or clicked.
- **Films**: the showcase films stream from the `media` release, and only when one is played (`preload="none"`); the contact sheets behind "What Claude sees" load when it is turned on. From mainland China the release can be slow; each film's folder and file are linked.

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

## Channel links

The Douyin and Bilibili entries in the "In practice" section have an empty `href=""`; paste the channel links there. Left empty, the names show without a link.

## Counts, and what checks them

A count on the page is wrapped as `<span data-n="styles">32</span>`. `tools/readme.py` (run by `tools/ci.sh`) holds every one to the repo; `python3 tools/readme.py` prints the current counts, and `check` names the line of one that is wrong. It also checks:

- that every relative link, image, poster and `#anchor` is there (a film listed in `tools/media.txt` counts, since `tools/fetch_media.sh` puts it back);
- that `STYLES` lists exactly the repo's styles, each with its thumbnail in `img/styles/` and its sample, and its Chinese name as in its `STYLE.md` title;
- that there are as many `lang="en"` texts as `lang="zh"` (a `<small>` gloss, like "TikTok in China" after Douyin, may stand in one language);
- that nothing from another site loads with the page (a stylesheet, script, font, image or frame).

A new style: add its row to `STYLES` and its thumbnail, `ffmpeg -i styles/<slug>/media/poster.jpg -vf scale=384:216:flags=lanczos -q:v 4 docs/site/img/styles/<slug>.jpg`.

## Where the other numbers come from

- **The films**: the intro film is 103 s, with a Blender opening of 1.18 million stars over 475 frames and 124 sound events; the four other films' lengths and engines; the hand-drawn short's 40 minutes of the agent's active work, three review rounds and about 20 fixes. Source: `showcase/*/README.md`.
- **Community films**: 389, with their prompts. Source: `cases/opus55-gallery.md`.
- **The FAQ's answers**: requirements, cost, times, limits and the A/B result. Source: `README.md` and `docs/research/06-concept-first-ab.md`.
- **The author's own account**: the Nobel explainer, its timing, and the Douyin and Bilibili channels.

## How it is built

- **Assets**: one HTML file with inline CSS and JS, the fonts and pictures above.
- **The galaxy**: the opening galaxy draws the style thumbnails on a canvas, with no randomness (positions come from a seeded hash); on a phone it is dimmed behind the text.
- **The f(t) panel**: it draws its frame as a pure function of `t`. Its "Render it again" button redraws that frame right after another one and compares every pixel.
- **Motion**: it stops when a section is off screen, and `prefers-reduced-motion` turns it off.
