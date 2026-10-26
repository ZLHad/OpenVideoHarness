# BRIEF：footage fixture

<!-- tools/assets/fixtures/footage/project: bin/vh footage's end-to-end fixture (tools/ci.sh, footage_checks). tools/ci.sh copies it,
     gets two clips into it from tools/assets/fixtures/footage/responses (bodies made with ffmpeg), syncs them, bakes their
     frames, renders index.html (a two-cell split screen that loads those frames by film frame number), then checks the
     ledger and delivers: the CC BY clip's credit line and the NASA clip's courtesy line are printed. -->

## Spec
- Effort: quick
- Budget: none
- Assets: strict
- Output: 320x180, 30 fps, exactly 2s (60 frames)
- Language: en
