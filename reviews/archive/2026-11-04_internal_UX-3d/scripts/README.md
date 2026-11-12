# Scripts of the UX-3d review (as run on 2026-11-04)

All of them drive the player in Chromium against a **private** server, never the shared one on 8479.

1. The server (from `engine/`, a scratch folder for the runs):

   ```
   docker run -d --name lf-uxa-srv -p 8561:8479 -v <engine>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
     -e LFPHYS_NO_GPU=1 -e PYTHONDONTWRITEBYTECODE=1 -e OMP_NUM_THREADS=2 -w /lf/visualizations light-funnel-viz \
     python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
   ```

2. Put these files next to a `node_modules` with `playwright@1.58.2` (ES modules resolve packages from the script's
   folder) and run them in Playwright's image:

   ```
   docker run --rm --init --name lf-uxa-pw --shm-size=2g --network host -v <that folder>:/pw -w /pw \
     mcr.microsoft.com/playwright:v1.58.2-jammy node /pw/tour.mjs 8561 v08_wave_3d double v08_double 10000 - /pw/out
   docker run ... node /pw/probe.mjs 8561 twoplanes /pw/out
   ```

| file | what it does |
|---|---|
| `lib.mjs` | start a run (`POST /api/runs`, `play`), open its page (patching the served `scene3d.js` **in the browser only** so that the scene's api also exposes `camera`, `orbit`, `renderer`, `scene`), mouse drags, wheel, screenshots, `diag()` (camera, near/far, box corners on screen, every layer's object and material types), `perf()` (draw calls, triangles, ms per frame), `fpsWhileRotating()` (rAF count and scene draws per second while the mouse keeps turning the view, CDP script time) |
| `tour.mjs <port> <viz> <preset> <tag> [playMs] [params] [out]` | the user's tour of one world: default view, turn 300 px, tilt 220 px, over the pole 700 px, F, zoom in (2500 px of wheel), F, zoom out (6000 px of wheel), pan with the right button, every view button; writes `tour.json` and the screenshots |
| `probe.mjs <port> <case> [out]` | `volsphere` (A1), `planevol`, `twoplanes` (A2), `flat` (A5), `boxjump` (A7), `faint` (A10), `volcost` (A11), `layerspanel` (A17), `zfight` (A19), `theme` |
| `lanes.sh` | every tour run (each world's default preset first, then one or two more) |
| `shiftpan.mjs <port>` | Shift + left drag (pan) and one wheel notch, measured on the camera (A6) |
| `montage.py` | the figures `fNN_*.jpg` of this folder from the screenshots (JPEG, each under 300 KB) |
| `table.py` | the tables of the review from the tours' `tour.json` |
| `outputs.json` | the measured outputs as delivered: per tour the canvas, the box, the box's corners on screen, the camera as opened / after F / after zooming out, every layer's object and material types, the render cost and the frame rate; per probe its result (`boxjump` keeps the number of samples only) |

Software GL (swiftshader): frame times are only comparable with each other on the same machine and load.
