# NOTICE: three.js in `engines/canvas-film/three/`

This folder is canvas-film's Three.js layer. `bin/vh new … --engine canvas-film --three` copies all of it into a project as `three/`, so the licence below travels with the code.

- `layer.js` is this repository's own (MIT, [`../../../LICENSE`](../../../LICENSE)).
- `build/` and `addons/` are files of **three.js 0.186.1** (r186), copied byte for byte from the npm package `three@0.186.1` (tarball shasum `6d50f70c2c437f844179bbb56d6f5b774e1ca38a`, integrity `sha512-blFeqb49wRCSGUGj7gtpfnSGHy2lwDk94RhUmS1c/hTby70kvChbWpkJ4Pm1390LqzzvTmzgXKHPEafJwCb8jA==`). Copyright © 2010-2026 three.js authors, MIT License: the licence, byte for byte from the package's `LICENSE`, is [`LICENSES/MIT-three.js.txt`](LICENSES/MIT-three.js.txt).

| File here | In the package | sha256 |
|---|---|---|
| `build/three.module.js` | `build/three.module.js` | `9052042d676cb0fdc1ddfefe193053f34b7ac0513a616fdac4535d49987812ea` |
| `build/three.core.js` | `build/three.core.js` | `9edde002b066a9a05676a6127f67735b62baf399bdea529f2f7e31657da769e6` |
| `addons/loaders/GLTFLoader.js` | `examples/jsm/loaders/GLTFLoader.js` | `131c0f78c01d19368ae495caa65b3adaa10487810a36a05bb5901b769a35ac16` |
| `addons/utils/BufferGeometryUtils.js` | `examples/jsm/utils/BufferGeometryUtils.js` | `9fb63427ce6641fa14fd0baff9cc4d1b5f9c3d85fd084bf2e90e803c44ec1797` |
| `addons/utils/SkeletonUtils.js` | `examples/jsm/utils/SkeletonUtils.js` | `b1632a703206c3d830de9fcbe515696770d04b71a15ee6b50afa6d2c3298c86f` |
| `addons/environments/RoomEnvironment.js` | `examples/jsm/environments/RoomEnvironment.js` | `55f466192cc84298755a424c5e040345006b2ee1455589b3b54126c2ea4123f4` |

The addons import `three` by name; the project's `film.html` maps it to `./three/build/three.module.js` (its import map), so they load unchanged. Another addon a film needs comes from the same version (`npm pack three@0.186.1`) into `three/addons/` at the path it has under `examples/jsm/`, with a row here. A new version replaces every file at once, gets new rows, and the Three.js layer's test in `tools/ci.sh` run again; `tools/modules.json` pins the version.
