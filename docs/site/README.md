# The OpenVideoHarness homepage

`index.html` is the project's homepage, in English and Chinese, online at <https://zlhad.top/OpenVideoHarness/docs/site/>. It covers:

- the films: a full-window wall of moving shots, and the way into [the one take](reel/) (below);
- Studio: the window for the whole production, its 17-second film (loaded on play, with sound), the review workflow, a real comparison of two cuts, its three themes, and how to open it;
- getting started in Studio or the terminal, a sample request in both languages, and the review stops;
- why the project exists and what it adds, with a live f(t) demo;
- how it works, and the capability map: the tools for thinking, gathering, making, checking and delivering;
- the intro film and the four other showcase films;
- the style library: all the samples moving at once round one of them at full size, with a few recipe and component contact sheets;
- in practice: where the author publishes films made with it, the Nobel explainer's three hours, and what each showcase folder records;
- an FAQ, and contact details.

It is one HTML file with no build step; the list of shots, `reel/shots.js`, is shared with the one take.

## The one take

[`reel/index.html`](reel/index.html) is a page of its own, in its own look (<https://zlhad.top/OpenVideoHarness/docs/site/reel/>): 31 shots from the films joined into one push-in, from a galaxy to a point of light, with no cut. Where the camera is depends on how far the page is scrolled and on nothing else, so scrolling back goes back.

- **How it is joined**: each shot sits inside the one before it, at a spot picked for that pair (`dive` in `shots.js`: x, y and width as fractions of the frame, and a shape: `iris`, `line` or `door`). The last shot bursts into the wall of all 55; pointing at one lights up the other shots of its film, and a click enlarges it.
- **Moving**: scroll, the arrow keys, the ticks at the bottom, or Space (or the button) to let it run. `#<shot>` opens at a shot, `#wall` at the wall, `?lang=` as on the homepage.
- **An upright phone** keeps the world a shot came out of around it. **Reduced motion** shows the wall as a still picture; a browser that asks to save data gets the stills, not the clips.
- **What a shot may be**: 3.5–5.5 s of a finished film, silent, its end dissolved into its start, described by what is on screen. Never a film's title or a channel's name, in the picture, the words or the file name: look at the four corners and at both ends, enlarged. A film whose backdrops were generated says so.
- **To add one**: cut it (1440 × 810, H.264, about 1 MB) into `media/reel/<id>.mp4`, put its first frame in `reel/posters/<id>.webp` (1200 px wide for the dive, 720 for the wall only), add it to `shots.js`, rebuild the mosaic (below) with its tile at the end of `order`, and write each file's name and sha256 in `shots.js` (`release`) and `tools/media.txt`.

## Viewing it

GitHub's file view shows the HTML source, not the page. To see the page:

- **On GitHub Pages**: the repo publishes `main` from `/ (root)` (Settings → Pages, "Deploy from a branch"), at the custom domain zlhad.top.
  - The `index.html` at the repo root redirects to `docs/site/`, keeping `?lang=` and `#section`.
  - The old address, `…/docs/talk/`, redirects here too.
  - The empty `.nojekyll` at the repo root makes Pages serve the files as they are.
- **From a clone**: open `docs/site/index.html` in Chrome. It reads the style samples and contact sheets from `../../styles`, `../../components`, `../../recipes` and `../../showcase`.
  - With `tools/fetch_media.sh 00-promo 01-hand 02-short 03-math 04-intro` (about 320 MB, mostly the 103 s intro film), the films play from disk instead of streaming.

## What it loads

Nothing from another site loads with the page, so it opens where Google Fonts, YouTube or a CDN are blocked (the two walls fetch theirs when they scroll into view, see **Walls**):

- **Fonts**: the display face (Inter Tight) and the mono face (JetBrains Mono) are in `fonts/`, cut down to Latin and the weights the page uses (23 kB and 12 kB, WOFF2), under the SIL Open Font License 1.1 (`fonts/OFL-*.txt`). They were taken from the google/fonts repository and cut with fontTools (`varLib.instancer`, then `pyftsubset … --flavor=woff2`). Body text and every Chinese character use the system's fonts.
- **Pictures**: all from this repo. `../assets/studio/` holds the Studio pictures, which the READMEs use too: one per language (`<name>.en.webp`, `<name>.zh.webp`), each an `<img lang=…>` shown with the page's language, loaded lazily, and enlarged on a click. They show Studio's own pages on demo projects. The revision dialog is captured from the repo's Fourier explainer (`showcase/03-math-fourier`), with a note asking the first sine wave to sit half a second before the formula. Studio's film plays from `media/studio-film.mp4` in a clone that ran `tools/fetch_media.sh` (`docs/site/media/` is not in git) and from the release `media` otherwise, through `<source type="video/mp4">`; its poster is `img/studio.jpg`. `img/` also holds five poster frames of the showcase films; `img/styles/` a 384 × 216 copy of each style's poster (about 14 kB each), for the galaxy. The 5-second samples (`styles/<slug>/media/swatch.mp4`) load one at a time, for the picture in the middle of the style wall: the one whose turn it is, or the one pointed at. A spec-2 style (5–10 s, `tokens.json` `"swatch": {"spec": 2}`) has only its 2 s `preview.mp4` in git: the middle plays that, and its lightbox plays the full sample from the release `styles-media` through `<source type="video/mp4">` once `STYLES_MEDIA_UPLOADED` is set to `true` (the preview, looping, until then). `RELEASE_SAMPLES` names each one's asset as `tools/media.txt` has it; `tools/readme.py check` says when they differ.
- **Walls**: the film wall and the style wall are each one silent mosaic video (`reel-wall`, 8 × 7 tiles; `styles-wall`, 8 × 6; 320 × 180 a tile, 5 s, 30 frames a second, 4.7 and 2.7 MB) drawn tile by tile on a canvas: one video to decode, whatever is on screen. It is fetched from the release `media` when the wall scrolls into view and stops when it leaves; until then, with reduced motion, when the browser asks to save data, and where the release is out of reach, a still from this repo stands there (`reel/wall.webp`, `img/styles-wall.webp`). Each tile starts at its own point in its loop, so the wall never cuts all at once. The tiles' order is `order` in `reel/shots.js` and `STYLE_TILES` in `index.html`: a new film shot or style goes at the end, and the mosaic is made again. A shot's own clip (about 1 MB) loads when it is pointed at or clicked.
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

A count on the page is wrapped as `<span data-n="styles">33</span>`. `tools/readme.py` (run by `tools/ci.sh`) holds every one to the repo; `python3 tools/readme.py` prints the current counts, and `check` names the line of one that is wrong. It also checks:

- that every relative link, image, poster and `#anchor` is there (a film listed in `tools/media.txt` counts, since `tools/fetch_media.sh` puts it back);
- that `STYLES` lists exactly the repo's styles, each with its thumbnail in `img/styles/` and its sample, and its Chinese name as in its `STYLE.md` title;
- that there are as many `lang="en"` texts as `lang="zh"` (a `<small>` gloss, like "TikTok in China" after Douyin, may stand in one language);
- that nothing from another site loads with the page (a stylesheet, script, font, image or frame).

A new style: add its row to `STYLES` and its thumbnail, `ffmpeg -i styles/<slug>/media/poster.jpg -vf scale=384:216:flags=lanczos -q:v 4 docs/site/img/styles/<slug>.jpg`. A spec-2 style also gets its line in `RELEASE_SAMPLES` (the name `bin/vh style register` printed). Add its slug at the end of `STYLE_TILES` too, and make the `styles-wall` mosaic and its still again with its tile in that place.

## Where the other numbers come from

- **The films**: the intro film is 103 s, with a Blender opening of 1.18 million stars over 475 frames and 124 sound events; the four other films' lengths and engines; the hand-drawn short's 40 minutes of the agent's active work, three review rounds and about 20 fixes. Source: `showcase/*/README.md`.
- **Community films**: 389, with their prompts. Source: `cases/opus55-gallery.md`.
- **The FAQ's answers**: requirements, cost, times, limits and the A/B result. Source: `README.md` and `docs/research/06-concept-first-ab.md`.
- **The author's own account**: the Nobel explainer, its timing, and the Douyin and Bilibili channels.

## How it is built

- **Assets**: one HTML file with inline CSS and JS, the fonts and pictures above.
- **The galaxy**: the opening galaxy draws the style thumbnails on a canvas, with no randomness (positions come from a seeded hash); on a phone it is dimmed behind the text.
- **The f(t) panel**: it draws its frame as a pure function of `t`. Its "Render it again" button redraws that frame right after another one and compares every pixel.
- **The walls and the one take**: the clips are decoded off screen and drawn on canvases. A 30-frame video on the screen itself holds the whole page at 30 frames a second in Chrome (measured 2026-11-26).
- **Motion**: it stops when a section is off screen, and `prefers-reduced-motion` turns it off.
