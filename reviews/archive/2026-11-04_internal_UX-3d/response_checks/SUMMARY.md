# Before/after numbers of the processing (software GL, private server; compare ratios only)

## Tours (`tour_ab.mjs`): box corners on screen as opened, a full frame, frames while turning

| tour | corners before → after | ms per frame before → after | scene frames/s while turning before → after | triangles before → after | errors |
|---|---|---|---|---|---|
| p01_sun_earth | 8 → 8 | 9.7 → 13.8 | 30 → 29.9 | 1064 → 834 |   |
| p02_dslit | 4 → 8 | 44.8 → 11.5 | 25 → 30 | 31348 → 272 |   |
| p03_maxwell | 8 → 8 | 91.1 → 25.8 | 16.4 → 29.9 | 156024 → 620 |   |
| p04_cyl | 6 → 8 | 8.9 → 10 | 30 → 30 | 412 → 218 |   |
| v08_double | 6 → 8 | 207.6 → 88.5 | 7.7 → 30 | 152 → 300 |   |
| v09_lab | 8 → 8 | 27.3 → 14.6 | 30 → 30 | 780 → 5512 |   |
| v10_terrell | 8 → 8 | 22.2 → 64.4 | 30 → 25.6 | 17080 → 17432 |   |
| v11_narrow | 4 → 8 | 83.4 → 41 | 20 → 29.9 | 86 → 3206 |   |
| v12_gauss | 2 → 8 | 86.4 → 90.2 | 19.4 → 23.8 | 38 → 1838 |   |
| v15_m87 | 8 → 8 | 23.3 → 25.4 | 30.2 → 30 | 25092 → 32940 |   |
| v17_rainbow | 4 → 8 | 21.8 → 19.8 | 28.7 → 30 | 28176 → 33236 |   |

## Performance (`perf_ab.mjs`, each world twice, orig and new interleaved)

| world | full frame, ms (runs) before | after | scene frames/s while turning before | after | script share playing before | after |
|---|---|---|---|---|---|---|
| p03_lv | 99.3 / 153.1 | 49.2 / 32.7 | 18 / 15.7 | 30 / 29.7 | — | — |
| v11_narrow | 199.5 / 222.5 | 30.9 / 46.5 | 10.5 / 10.4 | 29.8 / 29.8 | — | — |
| v13_1s | 375.8 / 479.6 | 79.1 / 88 | 8.4 / 9.1 | 30 / 29.7 | — | — |
| v13_super | 396.5 / 301.2 | 72.7 / 85.6 | 8.4 / 9.2 | 29.5 / 28.7 | 0.944 / 0.983 | 0.078 / 0.1 |
| v16_lg3 | 496 / 343.9 | 306.3 / 153.6 | 8.4 / 8.8 | 22.3 / 22.3 | — | — |
| v17_near | 381.1 / 342.2 | 85.3 / 103 | 9.9 / 8.8 | 24.5 / 26.6 | — | — |

## Probes (`probe_ab.mjs`)

- `boxjump` new: `{"case": "boxjump", "variant": "new", "before": {"pos": [-2.975, -3.406, 6.59], "target": [-0.774, -0.529, -0.036], "dist": 7.551, "box": "[[-4,-4,-2],[4,4,2]]", "lastView": "iso"}, "after": {"pos": [-2.975, -3.406, 6.59], "target": [-0.774, -0.529, -0.036], "dist": 7.551, "box": "[[-16,-16,-8],[16,16,8]]", "lastView": "iso"}, "afterScrub": {"pos": [-2.975, -3.406, 6.59], "target": [-0.774, -0.529, -0.036], "dist": 7.551, "box": "[[-4,-4,-2],[4,4,2]]", "lastView": "iso"}, "errors": []}`
- `boxjump` orig: `{"case": "boxjump", "variant": "orig", "before": {"pos": [-3.991, -5.216, 12.016], "target": [0, 0, 0], "dist": 13.694, "box": "[[-4,-4,-2],[4,4,2]]", "lastView": "iso"}, "after": {"pos": [41.49, -58.086, -41.49], "target": [0, 0, 0], "dist": 82.563, "box": "[[-16,-16,-8],[16,16,8]]", "lastView": "iso"}, "afterScrub": {"pos": [10.372, -14.521, -10.372], "target": [0, 0, 0], "dist": 20.641, "box": "[[-4,-4,-2],[4,4,2]]", "lastView": "iso"}, "errors": []}`
- `faint` new: `{"case": "faint", "variant": "new", "failed": "page.waitForFunction: Timeout 240000ms exceeded.\n    at openPage (/pw/lib.mjs:81:14)\n    at async file:///pw/probe_ab.mjs:219:18", "errors": ["pageerror: Cannot set properties of null (setting 'onclick')"]}`
- `faint` orig: `{"case": "faint", "variant": "orig", "look": {"look": {"density": 0.9, "threshold": 0.01}, "diag": 10.29403133513567, "dt": 0.06433769584459795}, "errors": []}`
- `flat` new: `{"case": "flat", "variant": "new", "layers": [["atoms", "spheres"]], "errors": []}`
- `flat` orig: `{"case": "flat", "variant": "orig", "layers": [["atoms", "spheres"]], "errors": []}`
- `layerspanel` new: `{"case": "layerspanel", "variant": "new", "worlds": {"p01_gravity": {"secs": 10.001700000286103, "childListMutations": 0, "firstInputReplaced": false, "hasRange": false}, "p02_quantum": {"secs": 10.000400000095368, "childListMutations": 1, "firstInputReplaced": true, "hasRange": true}, "v16_optical_vortices": {"secs": 10.000199999809265, "childListMutations": 0, "firstInputReplaced": false, "hasRange": true}}, "errors": []}`
- `layerspanel` orig: `{"case": "layerspanel", "variant": "orig", "worlds": {"p01_gravity": {"secs": 10.000199999809265, "childListMutations": 188, "firstInputReplaced": true, "hasRange": false}, "p02_quantum": {"secs": 10.000200000286103, "childListMutations": 2, "firstInputReplaced": true, "hasRange": true}, "v16_optical_vortices": {"secs": 10.000199999809265, "childListMutations": 18, "firstInputReplaced": true, "hasRange": true}}, "errors": []}`
- `planevol` new: `{"case": "planevol", "variant": "new", "planes": [{"id": 1, "label": "y = 0", "data": true}], "errors": []}`
- `planevol` orig: `{"case": "planevol", "variant": "orig", "planes": [{"id": 1, "label": "y = 0", "data": true}], "errors": []}`
- `twoplanes` new: `{"case": "twoplanes", "variant": "new", "planes": [{"id": 1, "label": "y = 0", "n": [0, -1, 0]}, {"id": 2, "label": "x = 0", "n": [1, 0, 0]}], "current": [{"p": [0, -1.7829785287161064, 0.8914892643580532], "plane2InFront": false, "rgb": [0, 255, 0]}, {"p": [0, 1.7829785287161064, 0.8914892643580532], "plane2InFront": true, "rgb": [0, 255, 0]}], "fix": [{"p": [0, -1.7829785287161064, 0.8914892643580532], "plane2InFront": false, "rgb": [0, 255, 0]}, {"p": [0, 1.7829785287161064, 0.8914892643580532], "plane2InFront": true, "rgb": [0, 255, 0]}], "errors": []}`
- `twoplanes` orig: `{"case": "twoplanes", "variant": "orig", "planes": [{"id": 1, "label": "y = 0", "n": [0, -1, 0]}, {"id": 2, "label": "x = 0", "n": [1, 0, 0]}], "current": [{"p": [0, -1.7829785287161064, 0.8914892643580532], "plane2InFront": false, "rgb": [0, 255, 0]}, {"p": [0, 1.7829785287161064, 0.8914892643580532], "plane2InFront": true, "rgb": [0, 255, 0]}], "fix": [{"p": [0, -1.7829785287161064, 0.8914892643580532], "plane2InFront": false, "rgb": [0, 255, 0]}, {"p": [0, 1.7829785287161064, 0.8914892643580532], "plane2InFront": true, "rgb": [0, 255, 0]}], "errors": []}`
- `volsphere` new: `{"case": "volsphere", "variant": "new", "cloudAtFront": [198, 110, 121], "cloudAtBack": [175, 83, 115], "withFront": [81, 254, 98], "withBack": [176, 86, 116], "sphereAloneFront": [81, 255, 98], "sphereAloneBack": [81, 255, 98], "errors": []}`
- `volsphere` orig: `{"case": "volsphere", "variant": "orig", "cloudAtFront": [127, 41, 110], "cloudAtBack": [92, 28, 104], "withFront": [51, 255, 77], "withBack": [51, 255, 77], "sphereAloneFront": [51, 255, 77], "sphereAloneBack": [51, 255, 77], "errors": []}`
- `zfight` new: `{"case": "zfight", "variant": "new", "errors": []}`
- `zfight` orig: `{"case": "zfight", "variant": "orig", "errors": []}`

## Volume looks (`look_ab.mjs`): the start look (τ after, the old density before), corners as opened

- lookF/p02_ball3d new: look {'density': 15.171013064682484, 'threshold': 0.01}, corners 8, errors []
- lookF/p02_ball3d orig: look {'density': 3, 'threshold': 0.01}, corners 4, errors []
- lookF/v08_double new: look {'density': 4.742561101913452, 'threshold': 0.02}, corners 8, errors []
- lookF/v08_double orig: look {'density': 0.6, 'threshold': 0.02}, corners 6, errors []
- lookF/v09_thomas new: look {'density': 0.3, 'threshold': 0.05}, corners 8, errors []
- lookF/v09_thomas orig: look {'density': 0.35, 'threshold': 0.05}, corners 6, errors []
- lookF/v11_narrow new: look {'density': 40, 'threshold': 0.01}, corners 8, errors []
- lookF/v11_narrow orig: look {'density': 3, 'threshold': 0.01}, corners 4, errors []
- lookF/v13_1s new: look {'density': 4, 'threshold': 0.01}, corners 8, errors []
- lookF/v13_1s orig: look {'density': 0.9, 'threshold': 0.01}, corners 6, errors []
- lookF/v13_3dm2 new: look {'density': 4, 'threshold': 0.01}, corners 8, errors []
- lookF/v13_3dm2 orig: look {'density': 0.9, 'threshold': 0.01}, corners 6, errors []
- lookF/v14_cc1S new: look {'density': 4, 'threshold': 0.01}, corners 8, errors []
- lookF/v14_cc1S orig: look {'density': 0.9, 'threshold': 0.01}, corners 7, errors []
- lookF/v16_lg3 new: look {'density': 10.02179705857265, 'threshold': 0.03}, corners 8, errors []
- lookF/v16_lg3 orig: look {'density': 0.9, 'threshold': 0.03}, corners 6, errors []
- lookF/v17_near new: look {'density': 0.32338178157806396, 'threshold': 0.05}, corners 8, errors []
- lookF/v17_near orig: look {'density': 0.6, 'threshold': 0.05}, corners 5, errors []

## Repeated timing of v10 «Террелл» (a tour's single sample looked slower; host shared, 9 × 5 frames, ms per frame)

After the change that draws a flat translucent surface's depth-only twin only in the volume's split pass:

| run | before: median (min) | after: median (min) |
|---|---|---|
| 1 | 39.0 (27.8) | 22.7 (18.3) |
| 2 | 88.7 (60.4) | 24.8 (20.6) |

## Repository checks on the final code

- `visualizations/tests/browser/keyframes.mjs` (private server, `LFVIZ_PLAYGROUND_CKPT=6`, all worlds): all equal, 23 jobs.
- `visualizations/tests/browser/scene3d_checks.mjs`: all passed, 12 of 12.
- `visualizations/tests/test_server.py` 29 passed; `node --test visualizations/player/js/tests/*.mjs` 1 passed;
  `lfphys/tests/test_licences.py` + `test_boundary.py` 42 passed.

## Notes

- The tours of v15 «M87» (after) and v17 «Радуга» (before) and the probe `flat` (before) were run again: the first
  attempts met a page error of the player page itself ("Cannot set properties of null (setting 'onclick')") in both
  versions while other agents were editing `player.js` / `run.html`; the repeats ran clean.
- The tours' and probes' ms are single samples on a shared host; `perf_ab.mjs` repeats each world twice.
