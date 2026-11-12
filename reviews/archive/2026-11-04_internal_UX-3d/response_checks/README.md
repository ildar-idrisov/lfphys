# Checks of the processing of review UX-3d (2026-11-05)

Before/after in one environment at one time: every script opens the same run twice, once with the code of the 3-D view
**before** the processing (`orig`: `scene3d.js`, `env3d.js`, `orbitview.js`, `imagewin.js`, `chrome.css` and the views
of p02–p04, v08–v17 as at git HEAD a55d0fc, kept in a folder mounted at `/orig` and served in the browser through
`page.route`) and once with the code on disk (`new`). Software GL (SwiftShader): frame times compare as ratios only; the
host carried other agents' work at the same time.

| file | what |
|---|---|
| `lib.mjs` | the review's `scripts/lib.mjs`, changed: `openPage(..., {variant})`; frames counted by the scene (the new code draws a frame in up to three passes) |
| `tour_ab.mjs` | the review's tour (default view, rotate, tilt, F, zoom in/out, every view button, cost, frame rate while turning), on a paused world |
| `probe_ab.mjs` | the review's probes (`volsphere`, `planevol`, `twoplanes`, `boxjump` + a step back in the history, `zfight`, `faint`, `flat`, `layerspanel`, `volcost`, `theme`) for both versions |
| `look_ab.mjs` | a volume world as opened and with its slices hidden (A1, A2, A5, A10) |
| `perf_ab.mjs` | a full-quality frame (ms), frames per second while the mouse turns the view, the script share while playing |
| `timing_ab.mjs` | a full frame timed 9 × 5 times, median and min (v10's check) |
| `lanes_ab.sh` | the runs as made: `sh lanes_ab.sh tours`, `sh lanes_ab.sh probes`, `sh lanes_ab.sh looks` (two at a time), then `sh lanes_ab.sh perf` alone |
| `summarize.py` | `SUMMARY.md` from the outputs |
| `figs.py` | the figures `figs/r*.jpg` (each under 300 KB) |

Run (a private server, never the shared one on 8479):

```
docker run -d --name lf-ux3-srv -p 8571:8479 -v <engine>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
  -e LFPHYS_NO_GPU=1 -e LFVIZ_PLAYGROUND_CKPT=6 -e PYTHONDONTWRITEBYTECODE=1 -e OMP_NUM_THREADS=2 \
  -w /lf/visualizations light-funnel-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
docker run --rm --init --name lf-ux3-pw --shm-size=2g --network host -v <these files + node_modules (playwright@1.58.2)>:/pw \
  -v <outputs>:/out -v <the files before the processing>:/orig:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
  sh /pw/lanes_ab.sh tours
python3 summarize.py <outputs> > SUMMARY.md && python3 figs.py <outputs> figs
```

The regression of the rendering contract is in the repository: `visualizations/tests/browser/scene3d_checks.mjs`.
