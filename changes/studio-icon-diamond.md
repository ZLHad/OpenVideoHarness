**OVH Studio's icon is the homepage's diamond in a viewfinder**
- Why: the icon was a flat cyan square in four corners, and the homepage's mark is a diamond in a cyan-violet-pink gradient; the person found the old one plain and picked this of four directions.
- `tools/desk/icon.py` draws it, still with the standard library only: the homepage's diamond, lit from inside (its own colours blurred behind it, a violet bloom on the tile), in a viewfinder's four corners on the dark tile; at 16 and 32 px the diamond alone. The designs are now `viewfinder` (installed) and `diamond`; `docs/assets/studio-icon-designs.png` shows both.
- The console's favicon is the same diamond on a dark tile. `tools/ci.sh` checks the middle of the 16 px icon for the diamond's violet instead of the old cyan.
- An icon installed before this: `bin/vh doctor` says it is old, and `bin/vh studio --install-icon` puts the new one in.
