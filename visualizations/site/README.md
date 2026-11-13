# `visualizations/site/`: the recordings and the public site

Developer notes for the scripts that make the public site (GitHub Pages, `https://ildar-idrisov.github.io/lfphys/`)
and the generated parts of the root READMEs. The site is the player in static mode: it plays saved recordings of the
demonstrations and reads the catalogue from JSON files; nothing is computed there. A local server computes every
scenario live and can play the same recordings (`/run?rec=<world>/<rec>`).

All scripts run from `visualizations/` in the project's Docker image, on the CPU (`LFPHYS_NO_GPU=1`), with a memory cap.
This folder is not a Python package (`site` is a standard module's name): each script puts this folder and `server/` on
`sys.path`; `sitelib.py` holds what they share (paths, the recorder's version, the budgets, the keys).

| file | does |
|---|---|
| `record.py` | the offline recorder: `--world ID` (repeatable), `--all`, `--stale`, `--rec ID`, `--out DIR` (default `visualizations/recordings/`, git-ignored), `--worker-mem-gb N` |
| `plan.py` | every (world, recording) with its key and state (`present`, `stale`, `missing`) against a folder; `--matrix [--rerecord stale\|all]` prints the CI matrix |
| `build.py` | `--recordings DIR --out DIR --base /lfphys/`: the static site |
| `check.py` | `SITE [--base /lfphys/] [--allow-missing]`: completeness and budgets of a built site; exit 1 on a failure |
| `readme.py` | the catalogue sections of `README.md`, `README.ru.md` (every language of `LANGUAGES.md`); `--check`, `--print LANG` |
| `posters.mjs` | Playwright: `docs/images/<id>.jpg` (1200 px wide, JPEG, ≤ 150 kB) and `docs/images/posters.json` |
| `ci/pages.yml` | the draft GitHub Actions workflow; not active until the owner copies it to `.github/workflows/` |
| `site.json` | `{"published": false, "url": "https://ildar-idrisov.github.io/lfphys/"}`: whether the public site is live, and where (the owner sets `published` on his go) |

## Recordings

A world's `VIZ["recordings"]` lists what the site plays: `[{"id", "preset", "seconds", "fps"[, "speed", "seed",
"script", "poster"]}]` (`registry.RECORDING_LIMITS`; laboratories have none). `record.py` runs each spec headless with
`lfviz.sim.Runner` on a frame clock of its own:

* the world's start (header and what it emits while being built), `state` (start, then playing), then exactly
  `seconds × fps` frames: the first at the world's start, each next one `speed / fps` of world time later, with no
  wall-time budget;
* a `script` entry `{at, cmd, args}` (`set`, `action`, `view`, `new_world`) is applied at frame `round(at × fps)`: the
  world is advanced to that frame's time, the command applied, then the frame drawn;
* `end {reason: "recording"}`; `checkpoint`, `command`, `resumed`, `record_segment` (and `busy`, `scene_export`) are
  dropped;
* an error message of the world, an exception, or a check whose last state is ✗ fails the recording (a check marked
  `expected` is a ✗ on purpose and does not); the index entry counts the checks' last states (`checks`).

The same spec recorded by the same code is the same bytes (`tests/test_recorder.py`): the frames carry no `cpu_ms` and
no `speed_actual` (the CPU time of the whole recording is the index entry's `cpu_s`), and the header's kernels
(`backend.used`) are reset before each recording, so a world recorded alone or after another gives the same file. A
seeded stochastic recording is one realisation: a live run with the same seed advances on another frame clock and draws
another realisation with the same statistics.

Budgets (gzip -9, decimal MB; `sitelib.BUDGET`, design §4.3): over the target (3 MB per file, 12 MB per world) the
recorder keeps every k-th frame (the first, the last and the poster frame always; every other message always), never
fewer than 2 frames per played second, and does not thin when that saves less than 10 % (a large message that is not a
frame dominates, as u38's volume). Over the hard limit (10 MB, 25 MB) the recording fails: shorten `seconds` or lower
`fps` in the spec.

Output per world (CONTRACT S/P):

```
<out>/<world>/<rec>.<hash8>.lfrec.gz    gzip -9 of the LFVREC1 stream; hash8 = sha256 of the file (Pages caches 10 min)
<out>/<world>/index.json                {world, version, recorder, recorder_hash, code_hash, made, recordings: [{id,
                                         preset, label, file, seconds, fps, speed, seed, frame_stride, frames,
                                         frames_recorded, bytes, bytes_gz, poster, poster_t, poster_frame, t_end, worlds,
                                         script, checks, cpu_s, sha256, key, version, code_hash, made}]}
```

`frames` counts the frames in the file, `frames_recorded` those recorded (`seconds × fps`); `frame_stride` is what the
player counts each frame as (it opens the file with its own `history_start`); `poster_t` is the world time of the
poster frame and `poster_frame` its index among the frames in the file. Each entry carries its own `version`,
`code_hash` and `made`; a recording not made now (`--rec`, or one that failed) keeps its old entry only when its key is
still the current one, else the entry and its file are dropped.

The key of a recording is `sha256(spec + RECORDER_VERSION + recorder_hash + registry.code_hash(world))[:16]`.
`sitelib.recorder_hash()` covers `record.py`, the image's `docker/requirements.lock` and `docker/Dockerfile`, and the
budgets that decide the thinning (`BUDGET` of a file and a world, `MIN_KEPT_FPS`), so a change of the recorder or of a
locked library makes every recording stale (`tests/test_code_hash.py`). `code_hash` covers the
world's folder, `lfviz` and the engine, so a change there makes recordings stale; the server process's own modules
(`registry.SERVER_ONLY`: `app.py`, `runs.py`, which no worker imports) are left out, so an edit of a route re-records
nothing. `RECORDER_VERSION` is raised when the recorder writes something different. The catalogue's entries carry the
server's `code_hash` of each world (`registry.code_hash_cached`, once per process), and the player's recording badge
names both codes when the recording's differs (design §4.6).

Locally, in Docker (at most 12 GB, a few containers at a time on a shared host; create `visualizations/recordings/`
first, or Docker creates the mount point as root):

```
docker run --rm --name lf-rec --memory=12g -e LFPHYS_NO_GPU=1 --user "$(id -u):$(id -g)" \
  -v "$PWD:/lf:ro" -v "$PWD/visualizations/recordings:/lf/visualizations/recordings" -w /lf/visualizations \
  lfphys-viz python3 site/record.py --stale
```

The server serves that folder at `/recordings/<world>/<file>` and lists it at `GET /api/recordings`
(`{worlds: {<world>: index.json}, site: the address of site.json or LFVIZ_SITE_URL, published: site.json's}`);
`LFVIZ_RECORDINGS` points it elsewhere. The player falls back to the public site's recording only when `published` is
true and the site's index has the same world version.
`/images/<file>` serves `docs/images/`.

## The site

`build.py` writes `index.html`, `run.html`, `legal.html` (the player's pages with `<meta name="lf-mode"
content="static">`, `<meta name="lf-base" content="<base>">` and the import map's `/static/`, `/viz/` and `three` made
relative; nothing else in a page is rewritten), `404.html` (its own, links with the base), `static/` (the player without
its tests and `legacy/`, and `static/locales/<lang>.json`), `viz/<id>/` (each world's `web/`), `api/viz.json`,
`api/viz/<id>.json` (also under each old id), `api/audiences.json` (`GET /api/audiences`: the audiences and the sections
with their labels), `api/planned.json`, `api/recordings.json`, `api/health.json` (the citation),
`aliases.json`, `recordings/`, `images/<id>.jpg`, `legal/<name>` (the licence page's full texts) and
`site-manifest.json` (every file's size and sha256; every world and recording with its key and state).

`check.py` fails on: a registry world or recording missing from the manifest or the site, or stale; a file that differs
from the manifest or its index; a recording whose index entry counts a check that ends failed; a page without its metas
or import map, or with an absolute `/static`, `/api`, `/viz` outside the import map; a script (`static/**/*.js`,
`viz/**/*.js`) with an absolute server address (`"/api…"`, `"/run…"`, `"/runs…"`, `"/settings…"`, `"/legal…"`,
`"/recordings…"`, `"/images…"`, `"/ws…"`) in a string literal; a catalogue world without `viz/<id>/view.js`, or a named
picture without `images/<id>.jpg`; a missing catalogue, audiences or i18n file; `api/recordings.json` that disagrees with
`site.json`; a hard limit exceeded (file 10 MB, world 25 MB, poster 400 kB, site 900 MB). Over a target it warns, and on
an index entry or a file the registry does not ask for (`build.py` copies only the entries it asks for).

Locally:

```
python3 site/build.py --recordings recordings --out /tmp/site --base /lfphys/
python3 site/check.py /tmp/site --base /lfphys/
cd /tmp && mkdir -p srv && ln -s /tmp/site srv/lfphys && cd srv && python3 -m http.server 8000   # http://127.0.0.1:8000/lfphys/
```

## The READMEs and the pictures

`readme.py` regenerates the section between `<!-- BEGIN generated: catalogue (visualizations/site/readme.py); do not
edit -->` and `<!-- END generated -->` in every language's README; everything outside the markers is written by hand.
Per audience: its worlds by section in teaching order; the school's planned items by section; the university's and the
research's planned items folded (`<details>`) after their worlds; the laboratories and the planned benches. The links to
the public site follow `site.json`: while `published` is false each world names its recordings without links and one
line at the top says, in the README's language, that the site is being prepared and the recordings play on a local
server; with `published` true every recording is linked (`<url>run.html?rec=<world>/<rec>`, plus `&lang=<code>` in a
README of a language other than the default, since the player does not follow the browser's language). To publish:
set `"published": true`, run `readme.py`, commit both.
The texts are the registry's `T` rendered with `lfviz.i18n.render_in`, so a new text needs its translation in the
catalogues (`tests/test_i18n.py`). `tests/test_site_registry.py` fails when a README is out of date or a world has no
picture.

`posters.mjs` takes each demonstration's picture at the poster frame of its first recording, played on a private server
with the local recordings; a laboratory's from a live run of its scenario (`LAB_PRESET`) after a few seconds of computing,
or, when its phenomenon needs world time, once the run reaches `LAB_T` (p04: the Kármán street at t = 6 s, about
20 minutes on the CPU); `--run <lab>:<run id>` takes it from a run already computed on that server. A picture is remade
only when its recording's key changed (`docs/images/posters.json`) or with `--force`. Its header has the Docker command.

## CI

`ci/pages.yml` (design §5.2): `check` (the image, the completeness, site and key tests, the matrix), in parallel with
`viz-tests` (the whole visualizations suite, three shards) and `engine-tests` (the engine's suite); `record` (after all
three: one job per world, restored from the cache by the world's key, recorded on a miss on the CPU with
`--memory=12g`, saved under the key also after a forced re-record), `build` (`build.py`, `check.py`, the smoke test
`tests/browser/site_smoke.mjs` in EN and RU on the site served under `/lfphys/` by `python -m http.server`, every
recording played), `deploy`. **Deployment is the owner's go:** a push to `main` checks, records and builds only; the
`deploy` job runs only when the workflow is started by hand (Actions → pages → Run workflow) with `deploy: true`. Every
action is pinned to a commit SHA, its tag in a comment, and the container images by digest. Enabling Pages and copying
the workflow to `.github/workflows/` are the owner's actions, on his go; until the first deployment `site.json` says
`"published": false` and the README carries no links to the site.

The smoke test checks that no request leaves `/lfphys/` and none goes to `/api/`, that the start page and an audience
page render in EN and RU, that a recording plays (the timeline moves, the checks appear, the canvas is drawn), that
every recording loads with the index's frame count and lands on `poster_t` at `poster_frame` (an old id too), that an
unknown recording id is said with a link to the start page, that `run.html?id=…` says the site plays recordings only,
that the laboratories are greyed with their note, that the school banner is honest, and that `legal.html` shows the
texts. `ALL_RECS=0` plays only one recording.
