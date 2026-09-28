# STORYBOARD — OpenVideoHarness launch film

<!-- Gate 2 skipped by the user for this showcase; written before any scene code and used as the review contract. Timings below are the FINAL ones (re-timed after snapshot/draft review, see NOTES.md). -->

Logline: A coding agent can now make videos but can't watch them; OpenVideoHarness gives it one command, a routing table and a review loop — so it checks its own frames.
World: one near-black blueprint desk (#0A0A0B, 120px grid at 6%). Real UI panes sit on it in 1px hairlines. One amber accent (#FFB224) marks "what the harness is acting on now". No colour shift across the film — the accent migrates: focus ring → routed row → FAIL flag → playhead of the wordmark.
Motif: the lower-left timecode `t 00.00 · f 000` — every frame prints the t it is a pure function of. It never stops; on the last frame it reads `t 19.97 · f 599`.
Arc: promise → doubt ("it can't watch video") → three proofs of competence → scale → name.
Audio: none (silent by brief). No BPM; timing comes from the reads below.

Seams (vector ledger, all LEFT unless noted): A→B waterfall cut · B→C, C→D, D→E, E→F cut-the-curve LEFT (230px, power4.in/out, cut mid-motion) · F→G inverse zoom-through (ARRIVAL, the one reserved vector). Cursor = carrier across C→D→E.

## Shots

| # | 时间 | 旁白 | 画面：看到什么 · 发生的事件 · 反应 · 镜头运动 | 焦点 | 转场出 |
|---|---|---|---|---|---|
| A | 0.00–2.50 | — | Hook. Two lines assemble word by word from below, left-aligned on the grid: "Your coding agent," (muted 400) / "now a video studio." (fg 600, 136px). | "video studio" | waterfall cut LEFT |
| B | 2.50–4.70 | — | Problem. "One catch: it can't watch video." cascades in mid-flight from the right and holds still. | "can't watch video" | cut-the-curve LEFT |
| C | 4.70–8.00 | — | Feature 1 · label "01  Scaffold a project in one command". Terminal pane (left) + file-tree pane (right). Cursor enters from below, clicks the prompt → `bin/vh new promo launch-film` types → the real stdout of that command (run 2026-09-29 01:38, `assets/vh-new-stdout.txt`): the hf-init scaffolding lines, `✓ created projects/2026-09-29-launch-film`, type doc, next → the tree cascades the 14 entries that project really had (`assets/vh-new-tree.txt`). Camera pushes in 1.0→1.18× on the ✓ lines + tree (1.9s), stops. Label + hairline stay fixed; the camera works in a clipped viewport below them. | the `✓ created` line | cut-the-curve LEFT, cursor carries |
| D | 8.00–11.30 | — | Feature 2 · label "02  CLAUDE.md routes the request". One wide pane: request pill "a 15–20 s launch film for OpenVideoHarness" + CLAUDE.md routing table rows 01–05 verbatim. Cursor clicks ↵ → an amber scan box steps down the rows → 0.33s comma → row 03 locks: `video-types/03-product-promo.md` · HyperFrames; other rows dim. Camera pushes 1.0→1.15× on row 03 with the request pill still in view (1.5s), stops. *(Draft v1 pushed 1.4× and cropped the row — NOTES #3; `tools/draft-v1.sh` rebuilds that state for beat E.)* | row 03 path | cut-the-curve LEFT, cursor carries |
| E | 11.30–15.00 | — | Feature 3 · label "03  It reviews its own frames". The timestamped `bin/vh sheet` of this film's draft v1 + a NOTES.md line. A scan passes the tiles; tile "0:10.50" (f 315) gets an amber box and the real `#3 FAIL` line types in. Camera pushes 3× into that tile (sheet → crop, 960×540 overlay with the same tile label). Cursor clicks → rack-focus swap to the current frame 315, `#3 FAIL` → `✓ #3 PASS`. Cursor leaves the frame downward. Sheet greyscaled; only the flagged tile keeps colour. | flagged tile + FAIL line | cut-the-curve LEFT |
| F | 15.00–17.00 | — | Proof. Four hairline-separated stats count up: 8 video types · 10 stages · 3 review gates · 20 taste checks. Then 0.5s of stillness. | the numbers | inverse zoom-through (exit shrinks 1→0.8) |
| G | 17.00–20.00 | — | Lockup, centred: "OpenVideoHarness" (168px, ~1330px wide) arrives oversized and settles (1.25→1, blur 10→0); an amber playhead bar draws to its left; tagline "Video as code, for coding agents." rises word by word under it. Holds to the end; timecode ends at `t 19.97 · f 599`. | wordmark | end (hold) |

### A 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 0.25–1.00 | "Your coding agent," | first motion at 0.25s, not t=0; waterfall from below pulls the eye to the left third |
| 0.85–2.50 | "now a video studio." — the promise | overlaps line 1's settle by 0.15s (a wave, not a queue); ~0.8s of pure hold before the peel |

### B 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 2.50–4.50 | "One catch: it can't watch video." | enters mid-flight in the same direction the hook left; ~1.6s still hold = the doubt sinks in |

### C 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 4.70–5.22 | "01 Scaffold…" + a terminal | label and pane arrive together; cursor enters from below and lands on the prompt |
| 5.22–6.08 | the command types itself | click at 5.22 ignites typing same-frame (28 ms/char); cursor drifts aside so it doesn't cover the text |
| 6.18–7.70 | `✓ created projects/…` + the tree fills | Return at 6.18; "scaffolding" line at once, the rest 0.22s later (hf-init "runs"); `✓ created` from 6.49; tree 30 ms/item; push-in ends 7.22 |

### D 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 8.00–8.50 | a request + a routing table | cursor already in flight from C lands on ↵ |
| 8.50–9.22 | the harness scans rows | click ignites the scan; scan box moves slow-fast-slow |
| 9.55–11.00 | row 03 → `video-types/03-product-promo.md` · HyperFrames | 0.33s comma before the lock; other rows dim at the same frame the row locks |

### E 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 11.30–12.15 | "03 It reviews its own frames" + a contact sheet | scan line sweeps the sheet so the eye reads it as "being checked" |
| 12.15–13.40 | one tile flagged + the FAIL line; camera lands the tile at 3× | box and the line's first char appear on the same frame (cause = effect) |
| 13.70–14.70 | click → fixed frame, ✓ PASS | 0.3s comma before the click (13.40–13.70); swap under a rack-focus blur spike |

### F 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 15.00–16.30 | 8 video types · 10 stages · 3 review gates · 20 taste checks | column 1 on screen at the cut frame, 60ms stagger, counts finish by 15.95 |
| 16.30–16.80 | (stillness) | brief: 0.5s stillness before the lockup |

### G 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 17.00–17.50 | OpenVideoHarness | arrival (inverse zoom) = the one reserved vector, spent on the name |
| 17.65–20.00 | "Video as code, for coding agents." | rises after the name settles; 2.0s+ hold for the GIF loop and the poster frame |

## 对照检查
- [x] 每个镜头都有事件（首帧和末帧之间有东西变了）
- [x] 每条 read 在下一条开始前有时间落地
- [x] 每个接缝都有转场，开头和结尾也有（open: first motion at 0.25s from the bare grid; end: hold）
- [x] 文字用量符合类型文档的规则（≤ 8 words of copy per frame; UI text is real UI)
- [x] 结尾与开头呼应：the hook's left-aligned type returns as a left-aligned lockup block (centred on the frame for the longer name); the timecode motif lands
- [x] 全片只用 3 种转场、一个主运动方向（LEFT）
