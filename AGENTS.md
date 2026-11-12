# AGENTS.md: rules for work in this repository (the lfphys engine and its visualizations)

This repository holds the physics engine `lfphys` and its interactive visualizations. It was developed inside the
owner's research tree (as `engine/`) until 2026-11-12, when it became this standalone public repository; research
projects use it only as an external library and are kept strictly apart from it (§4). Below, "`engine/`" in older text
means the root of this repository. These rules apply to every agent and session working here.

## 1. The owner's directions (verbatim, with dates)

**Visualizations (2026-10-22):**

> создай отдельную папку с визуализациями для отображения следствий по гипотезам, пропиши это в инструкциях. в ней по
> моему запросу должна создаваться подпапка и делаться визуализация в виде плеера как в проекте
> [путь к другому проекту владельца — опущен при публикации, 2026-11-12]
> с одним общим сервером для запуска разных визуализаций и вещанием в локальной сети, чтобы я мог зайти на отдельный
> порт со своего ноубтука [адрес в локальной сети]:port, выбрать одну из визуализаций и в интерактивном режиме поиграться с ней.
> плеер и сервер один в докере и единым api для всего проекта
>
> все визуализации поднимаются по запросу с браузера мною. все визуализации должны быть точно выверены и согласованы с
> общепринятой физикой, допускается только вносить изменение для исследования какого-то эффекта, например если я получил
> новое доказательство и хочу его проверить или я хочу намеренно изменить какое-нибудь известное правило/закон, чтобы
> посмотреть как все будет работать без него.
> все визуализации должны отображать результат из расчетов текущего запуска, а не из известного факта, т.е. если свет
> формирует дифракционную решетку, то она должна рисоваться как следствие запуска, а не просто появляться, потому что
> это известный факт, т.е. визуализации должны иметь четкие прифинно-следственные связи в запуске.

**Live set-up, worlds inside a run (2026-10-23):** quoted in `visualizations/RULES.md` §2.4.

**The engine (2026-10-23):** quoted in `lfphys/LAYERS.md`.

**Licence (2026-10-24):**

> по лицензии делай рекомендованный вариант:
> - Код: вариант A, плюс коммерческая лицензия по запросу.
> - Документация и визуализации: вариант B.
> - Вспомогательные файлы. Имя: Ildar Idrisov. почта: idrisov.sci@gmail.com
> укажи, что по всем вопросам или для коммерческого использования писать на почту idrisov.sci@gmail.com

**Licence review (2026-10-29):** «прочитай ревью по лицензиям и внеси правки» — the review
`reviews/archive/2026-10-29_internal_licensing/` (PolyForm Noncommercial permitted institutional use for commercial
clients and could not make citation binding), processed in its `RESPONSE.md`: the code moved to the project's own
lfphys Research Licence 1.0; the Licensor is the owner as an individual (resident in Cyprus).

**Development plan (2026-10-24):** quoted in `lfphys/PLAN.md` §0.

**Separation and 2-D slices (2026-10-24):**

> 1. Пункт 10, «моделирование в выбранном 2-D срезе» для 3-D
> оба варианта. предлагаю сделать возможность задавать как и что моделировать: либо полное 3D моделирование (может быть
> долгий и тяжелый) с возможностью исследовать любой 2D срез, либо только заданные один или несколько 2D срезов для
> ускорения, но исследовать можно только в этих срезах. помечать там, где это приближение.
> 2. проверку текстов сделаем потом, я пока не собираюсь открывать проект, он еще не готов.
> 3. lfphys - движок и визуализациями будет выделен в отдельный репозиторий, который не будет касаться базы знаний и
> прочего, текузие проекты при необходимости будут подключать lfphys как внешлюю библиотеку для исследования своей
> части вопросов. сейчас работаем вместе, т.к. для проектирования движка полезно видеть развитие исследований реальных
> проектов. но строгость разграничения нужно сохранять, чтобы код, тексты не перемешались между проектами.

**Corrections after B1: the 3-D environment (2026-10-27):** «библиотеки CUDA можно использовать. в пакету B2 не
переходи, сначала обработай мои корректировки, все реализуй и при необходимости подправь следующие запланированные
шаги.»

> в визуализации v08, и для всех остальных визуализаций, при моделировании в 3d при запуске срез по двум осям постоянно
> смещается, этого не нужно делать, он должен быть зафикварован. если мне нужно сместить срез, то я место среза задаю
> руками. автосмещение можно сделать как доп. опцию (по умолчанию выключено).
> так же при 3d моделировании я должен видеть полное 3D. на примере v08 я должен в 3d видеть заслонку с целями, проходящие
> пучки света и мишень. а при выборе среза, рядом должно появляться окно с проекцией среза. срез должен задаваться на 3D,
> не 3 строго вертикальные прокции, а заданная плоскость среза в 3D под любыми углами. плоскость среза добавляется на 3D
> с сразу появляетсяко окно с проекцией, я должен уметь поворачивать плоскость среза в 3D руками как в 3D движках
> (unreal, 3d max) и с помощью параметров. должна быть возможность добавлять до 3х плоскостей со своими окнами. при
> выделении окна на 3D подсвечивается эта плоскость, чтобы было понятно какой это срез. должны быть возможность
> включать/отключать части визуализации, например при 3D моделировании непрозрачной области, где показаны вероятности
> нахождения частиц или потоки энергии, силы взаимодействия, причем каждый элемент нужно выключать отдельно, чтобы можно
> было видеть оставшиеся части визуализации. срезы автоматически располагай в середине визуализации под углами 90
> градусов. по интерфейсу можешь смотреть на схожие продукты и перенисать опыт, но не копируй то что может быть
> запрещено (по лицензии, правам), только перенимай опыт. работать с визуализациями должно быть удобно, информативно и
> это должна быть полноценная 3D среда для исследователей на основе физического движка с разными визуализациями

## 2. Layout

| path | content |
|---|---|
| `lfphys/` | the physics engine (Python package `lfphys`): layers `LAYERS.md`, catalogue `README.md`, plan `PLAN.md`, sources `sources/`, tests `tests/` |
| `visualizations/` | one server and one player in Docker (port 8479) and one folder `vNN_<slug>/` per visualization; rules and API `RULES.md`, owner guide (Russian) `README.md`; the player's 3-D environment `player/js/scene3d.js`, `player/js/slices.js`; third-party code only in `player/vendor/` (three.js, MIT, unmodified) |
| `reviews/` | independent reviews of the engine and the visualizations, rules and registry `reviews/README.md` |
| `STATUS.md` | the one place for open problems and plans of the engine and the visualizations |
| `LICENSE.md`, `LICENSE-DOCS.txt`, `NOTICE`, `COMMERCIAL.md`, `CITATION.cff`, `CONTRIBUTING.md`, `CLA.md`, `PUBLICATIONS.md` | licence (code: the lfphys Research Licence 1.0, `LicenseRef-lfphys-Research-1.0` — noncommercial research only, citation required; documentation: CC BY-NC-SA 4.0 with additional permissions for scholarly publications; commercial use only by a separate written agreement), citation, contribution terms and the contributor agreement; copies in `lfphys/` and `visualizations/` |

## 3. Rules

1. **Visualizations live in `visualizations/`.** A new visualization is a new subfolder `vNN_<slug>/` made on the
   owner's request; the one server and the one player serve all of them through one API (`visualizations/RULES.md`).
   Runs start only from the owner's browser.
2. **Computed, not drawn.** Every visible consequence is computed by the current run from its inputs. Closed forms of
   the known theory appear only as references in the run's checks, next to the computed value.
3. **Causality.** Consequences are revealed when the run's time reaches them; actions act at the current event and
   pending consequences are recomputed; the past is not rewritten.
4. **Accepted physics unless explicitly modified.** A changed law is a named world parameter with a `standard` value;
   such a world is flagged "modified physics" everywhere. Laws and initial conditions are fixed per world (a new
   world starts inside the same run), except a playground's laws that the engine can change at the current moment:
   those are live (owner, 2026-11-04; `visualizations/RULES.md` §2.4, §6); the set-up an experimenter can change is live and applies at once
   (`visualizations/RULES.md` §2.4).
5. **Physics in the engine, verified before use.** A visualization is a wrapper over `lfphys`. The engine's core holds
   only established physics; theories that disagree with it or with each other sit outside the core
   (`lfphys/LAYERS.md`). Every function is tested against a closed form or a second method; approximations are stated
   in the visualization's README.
6. **Reviews.** New physics gets a review by a different agent in `reviews/`. The author of a review never processes
   it (owner, 2026-10-15: «тот кто пишет ревью - не обрабатывает его»); processing is finding by finding in
   `RESPONSE.md`, then the folder moves to `reviews/archive/` (`reviews/README.md`).
7. **One place for problems.** A problem found is fixed, or recorded once in `STATUS.md` here. READMEs point to it.
8. **Licence-clean code (owner, 2026-10-24).** The owner's words (verbatim): «при разработке не используй сторонние
   библиотеки с лицензиями закрытыми для коммерческого применения, если такие нужны, то пиши свою релизацию так чтобы
   код был лицензионно чист для установки любой своей лицензии» and «сравнения со сторонними библиотеками для проверки
   точность движка, используй сторонние библиотеки только для тестов сравнения». So: no third-party code is copied in
   unless permissive (MIT, BSD, Apache-2.0, ISC, PSF, zlib, public domain); runtime dependencies are permissive or weak
   copyleft used unmodified as separate libraries; libraries under strong copyleft, noncommercial or proprietary
   licences appear only in comparison tests, and only where their own licences allow that use; anything else is reimplemented from published descriptions.
   The owner, 2026-11-10 (verbatim): «давай разрешим подобные тесты на любых лицензиях, но только для сравнения нашего
   результата со сторонними. все эти модули должны запускаться в одном отдельном контейнере и храниться отдельно и только
   временно для разового запуска. в репозиторий не заливать, импользовать по необходимости. … когда Meep перестает быть
   нужным, то удаляешь его. запускать подобный код с лицензией gpl не запрещается, главное не внедрять его в проект на
   постоянке», and the same day: comparisons with permissively licensed libraries stay in the repository. So two tiers:
   permissive libraries (MIT, BSD, Apache-2.0, …) are compared in `lfphys/tests/external` and its image
   `lfphys-ext`; copyleft, restricted or unclear licences only in a one-off run — the script kept outside the
   repository, a throwaway image of its own, the licence's terms of use (not only of distribution) checked first, a dated
   record of the set-up and results committed as `lfphys/sources/comparison_<date>_<library>.md`, the script and the image
   deleted when the library is no longer needed (`lfphys/tests/external/README.md` §1). Every source
   file keeps its SPDX lines; `NOTICE` travels with every copy (`CONTRIBUTING.md`). One category is admitted as a
   platform runtime: the NVIDIA CUDA libraries for the optional GPU backend (NVIDIA EULA: commercial use permitted,
   redistribution only of the listed files, unmodified, inside an application); the engine imports CuPy only inside a
   function and runs entirely without them. The owner confirmed this category on 2026-10-27: «библиотеки CUDA можно
   использовать». The audit and its test: `lfphys/sources/dependencies.md`,
   `lfphys/tests/test_licences.py`.
9. **Docker only.** Build, run and test in Docker (`visualizations/docker/`, commands in `visualizations/README.md`),
   from the repository root. On the owner's development host GPU work (plan item P11) runs only on GPU 0 (its GPU 1 is
   faulty; pinned by `LFPHYS_GPU_PCI` in the git-ignored `visualizations/docker/.env`), with a lowered power limit for
   long runs (that host overheats under full load). Never touch the host's CUDA or git config.
   Run records stay in `visualizations/runs/` (git-ignored).
10. **Working mode for the plan.** `lfphys/PLAN.md` is done in batches of three items: implementation with tests, an
    independent review and its processing, a report to the owner and a discussion; the next batch starts only on the
    owner's go.
11. **Practice.** Verify quotations and numbers against the source before building on them. Unreproduced claims are
    hypotheses. Give every reported result a status tag: [useful] / [neutral] / [weakens] / [error in earlier].
    Persist background work to files. Stop processes by PID or container name, never with `pkill -f`. Never put the
    owner's e-mail or any personal identifier into requests to external services (only into this project's own
    licence and citation files, as the owner asked). Code and documentation in English; the owner guide and reports
    to the owner in Russian; a question from the owner is answered first, implied work is not started without a go.

## 4. Boundary with the research projects (owner, 2026-10-24)

The engine is a library that research projects use; it is not part of their research record, and their texts are not
part of it.

1. **Nothing from the research projects enters `engine/`.** No file here imports, reads or links research code, notes,
   knowledge-base items, research status items or drafts. A research result reaches the engine only as a published
   reference, or as a hypothesis the owner states for a visualization (its formula and parameters written here, with
   its status: hypothesis). `lfphys/tests/test_boundary.py` checks the obvious markers.
2. **Research projects use the engine only as an external library**: `import lfphys` with `engine/lfphys` on the path
   (or installed from it), never by copying engine code into their folders and never by writing their notes into
   `engine/`. A change the research needs is made here, under these rules (tests, review), and used from there.
3. **Separate records.** Open items, plans and reviews of the engine live here (`STATUS.md`, `lfphys/PLAN.md`,
   `reviews/`); the research project keeps only pointers to `engine/`. Commits keep engine changes and research changes
   apart.
4. The owner's log of how AI work is steered is part of the owner's methodology, kept outside `engine/`; engine files
   do not refer to it.
