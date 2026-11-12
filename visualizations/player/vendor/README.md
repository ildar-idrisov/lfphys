# Third-party code served by the player (kept unmodified, under its own licence)

The only third-party code in `engine/` (`../../../lfphys/sources/dependencies.md` §7). Each folder holds files copied
unmodified from one published package, its licence text, and the checksums below; `lfphys/tests/test_licences.py`
checks them. The project's licence does not apply to these files; their own licence does.

## three-0.185.1 — three.js r185.1 (MIT)

Source: the npm package `three@0.185.1` (https://registry.npmjs.org/three/-/three-0.185.1.tgz, published 2026-07-01),
files `build/three.module.min.js`, `build/three.core.min.js`, `examples/jsm/controls/OrbitControls.js`,
`examples/jsm/controls/TransformControls.js`, `LICENSE`. Used by the player's 3-D environment
(`../js/scene3d.js`): WebGL rendering, the orbit camera, the move/rotate gizmo of slice planes. Loaded through the
import map of `../run.html` (`"three"` → `three.module.min.js`).

| file | sha256 |
|---|---|
| three.module.min.js | 86bcee248b64f44bcfc23c331ae74619061957d59cab040171dcb6fb5900beb6 |
| three.core.min.js | 05b2609338c76cd65daf74f3ac515bc9a5045e1b3b33edc07d8c9bd55250fa90 |
| OrbitControls.js | faabb4e8dfd9235ee4a9fd7c9a3d75f90f1689dbd4944bd6fd32117dacec5f93 |
| TransformControls.js | 151befe25bb0d68626f9a6b033625b7b0cf6848e39ba71623b7bed8e3df565d6 |
| LICENSE | 8b378ebe60e2fe500158cb0ac71cb5e8b7d92953c2abcc63a0eb90499653b5bc |
