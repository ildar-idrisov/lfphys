# lfphys: physics engine and interactive visualizations

* `lfphys/` — a Python physics engine. Its core holds established physics only, each function tested against a closed
  form or an independent method (with certified Arb references for key quantities); outside the core, layered
  approximations, interpretations, phenomenological models and declared alternatives, each stating where it disagrees
  with the core. Catalogue: `lfphys/README.md`; layers: `lfphys/LAYERS.md`; development plan: `lfphys/PLAN.md`.
* `visualizations/` — one server and one browser player (Docker, port 8479) with interactive worlds built on the engine:
  every visible consequence is computed in the run, with live checks against independent references. Owner guide
  (Russian): `visualizations/README.md`; rules and API: `visualizations/RULES.md`.
* `reviews/` — independent reviews and their responses; `STATUS.md` — open items and plans; `AGENTS.md` — rules for
  work here, including the boundary with the research projects that use the engine.

## Running

From this folder (`engine/`):

```
docker compose -f visualizations/docker/docker-compose.yml build
docker compose -f visualizations/docker/docker-compose.yml up -d viz        # the server, http://<host>:8479/
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/lfphys lfphys-viz \
    python3 -m pytest -q -p no:cacheprovider                                # engine tests
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/visualizations lfphys-viz \
    python3 -m pytest -q -p no:cacheprovider                                # visualization and server tests
```

A research project uses the engine as an external library: `import lfphys` with `engine/lfphys` on `PYTHONPATH`.

## A research tool: no warranty

The engine and the visualizations are research tools. Their models, implementation, numerical methods and results
may contain errors. The tests check the stated cases within the stated ranges (closed forms, independent methods, and
certified Arb references for the specific quantities named in `lfphys/README.md`); they do not certify every model or
the result of any other problem. Before relying on a result, check the inputs, whether the model applies, the
convergence and the result yourself. No support, corrections or fitness for a particular use are promised without a
separate agreement (`LICENSE.md` §8). The player shows this notice and the licences at `/legal`.

## Licence, citation, contact

The software is **source-available, not open source**: it may be used for noncommercial research, study and teaching;
any commercial use needs a separate written agreement.

| what | licence |
|---|---|
| code: every source file, script and configuration (`*.py`, `*.js`, `*.mjs`, `*.html`, `*.css`, Docker and lock files), including the visualizations' code and the texts and images the program shows when it runs (its interface and help) | lfphys Research Licence 1.0 (`LICENSE.md`, SPDX `LicenseRef-lfphys-Research-1.0`): noncommercial research only; commercial use by anyone, including institutions working for a business, needs an agreement (`COMMERCIAL.md`) |
| documentation: the texts of guides and READMEs, `sources/`, and the figures and images the author made for them | CC BY-NC-SA 4.0 (`LICENSE-DOCS.txt`), with additional permissions for scholarly publications (`PUBLICATIONS.md`) |
| your results: numbers, data, figures and images of your runs | yours; publications of results obtained substantially with lfphys (it computed, simulated or rendered, or checked, something the publication reports) must cite it with its version; screenshots of your runs may be published with attribution, also by the publisher; selling data sets that consist substantially of its output needs an agreement (`LICENSE.md` §5, §6; `PUBLICATIONS.md`) |
| third-party components (`visualizations/player/vendor/`) | their own licences (three.js: MIT), listed in `NOTICE` |

* **Notices**: `NOTICE`, the licence texts and the copyright notices in the files accompany every copy; every source
  file carries its SPDX lines.
* **Citation**: required in publications (`LICENSE.md` §5), as in `CITATION.cff`. **Contributions**: `CONTRIBUTING.md`
  and the contributor agreement `CLA.md`.
* **Licensor**: Ildar Idrisov, an individual.

Copyright (c) 2026 Ildar Idrisov. **For commercial use and for all other questions: idrisov.sci@gmail.com**
