# STYLE

## Canvas
- 1920x1080, 24 fps, 12.0 s. No captions, so no caption band. Keep Clawd's face and the leaf inside x 150–1770, y 90–990 (the viewfinder inset used in the last shot).

## Palette
| token | hex | use |
|---|---|---|
| paper | PAL.paper #F3EBDC | ground of everything |
| sky | #F5DDB6 → #EBD3C4 (B, windier, a touch lilac) → #F7D59A (D, golden) | colour arc: soft morning gold → breezy → warm amber |
| hillFar | #C9A7A0 | far hills (paler, cooler = farther) |
| hillMid | #B98F6A | mid hills |
| ground | #B7A05A / fill #8E7A3C | olive-ochre meadow |
| trunk | #6E4A3A | maple trunk and branch |
| foliage | #C4553A, #D9773E, #A8452F | rust / orange maple crown (NOT gold, so the hero leaf pops) |
| LEAF (accent) | #F2B632 wash, #E58A2A fill, ink outline | the hero leaf — the only saturated yellow in the film |
| pumpkin | #D9692E / ribs #B24E22 | shot B perch |
| camera | walnut #7B4B33, dark #4A3036, brass #D9A441, lens glass PAL.ink | the prop |
| wind | PAL.cream dry-brush + #9C8FA8 fine ink curls | gust streaks |
| rec dot | #D8394E + glow | viewfinder "recording" mark (painted, not text) |
| ink | PAL.ink #2B2233 | outlines, viewfinder border, iris |

## Motion tokens (cartoon register, per ANIMATION_GUIDE)
- Acting: emotions() for every face change; take() / backOut for reactions; jump()-style crouch before the dash.
- Leaf fall: pendulum rock (sway ±90 px, rotation follows sway), slow descent — light things flutter.
- Gusts: 0.15 s anticipation (grass and twigs lean first), then the snatch in ~0.35 s along an arc; streaks trail it.
- Camera (cinematic): always drifting or pushing slightly; handheld wobble only in the POV shot.
- Beat: bpm 120; hits on beats (leaf lets go 0.5, gust 2.5, cut 4.0, gust 6.0, stomp 6.5, leaf lands 10.0, delight 10.5).

## Transitions (3 kinds, reused)
- Viewfinder iris (rounded rect + corner brackets): opens the film on the leaf; closes the film on Clawd. The rhyme.
- Cut on action: A → B (Clawd launches right, arrives running right).
- Push into the lens: B → D (camera pushes to the lens, its dark glass fills the frame, the viewfinder opens out of it).
- Dominant direction: left → right (the wind, the leaf, Clawd's chase).

## Banned
Lettering of any kind, plain p5 shapes, gradients/digital glows other than glow(), pure black/white, 3D rotation (the camera prop turns through drawn key views), the demo's night/star imagery.
