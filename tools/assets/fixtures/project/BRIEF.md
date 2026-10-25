# BRIEF：assets fixture

<!-- tools/assets/fixtures/project: the asset ledger's fixture (tools/ci.sh, assets_checks). Synthetic files; example.org sources.
     tools/ci.sh copies it and writes assets/genclips/gc-0001/clip.mp4 (a video may not be in git): here, check misses that clip.
     index.html loads two pictures on record and assets/img/stray.png, which is not. -->

## Spec
- Effort: quick
- Budget: $1  <!-- the fixture's: $0.04 in spend.jsonl, $0.50 from the clip's ledger before v1 -->
- Assets: record  <!-- the NC loop is taken and listed; --policy strict fails on it -->
- Output: 320x180, 30 fps, exactly 1s (30 frames)
- Language: en
