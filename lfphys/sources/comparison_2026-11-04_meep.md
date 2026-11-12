# A one-off comparison of `core.em.fdtd` with Meep 1.35.0 (2026-11-04)

**What this is.** The record of a comparison run once, during batch B8 (plan items P1, P13), of the engine's FDTD solver
with Meep 1.35.0 (MIT's FDTD code; conda-forge `pymeep`; licence GPL-2.0-or-later). Only the results and the set-up are
kept here. The comparison script and the recipe of its Docker image are not in the repository: the owner's rule of
2026-11-10 for third-party libraries under copyleft or other restrictive licences (`../../AGENTS.md` §3, rule 8):

> давай разрешим подобные тесты на любых лицензиях, но только для сравнения нашего результата со сторонними. все эти
> модули должны запускаться в одном отдельном контейнере и храниться отдельно и только временно для разового запуска. в
> репозиторий не заливать, импользовать по необходимости. например тут, если видишь что нужно запустить тест с Meep и
> сравниться, то делаешь это, сравниваешься, получаешь результаты, когда Meep перестает быть нужным, то удаляешь его.
> запускать подобный код с лицензией gpl не запрещается, главное не внедрять его в проект на постоянке.

The script (`test_ext_fdtd_meep.py`) and the image (`light-funnel-ext-meep`: `condaforge/miniforge3:26.7.2-0` pinned by
digest `sha256:569afc65b5338d35e276adf9a860025cd37a677659d19dcb71fc1d4c2063a94e`, a conda environment of 124 packages
pinned by URL and md5, numpy 2.4.6, scipy 1.17.1, mpmath 1.3.0 and pytest 9.1.1 as in the runtime image) were in the
repository from 2026-11-04 (commits a55d0fc, 85e3e41) to 2026-11-10 and were then removed; the image was deleted. Meep
was used through its documented Python interface only; no Meep code was read for or copied into the engine (one source
header was grepped for its licence statement). The licence audit of the image: `dependencies.md` §10.5.

**What it showed.**
* It exposed an inconsistency of the engine's normalisation, found by review B8-fdtd (F5,
  `../../reviews/archive/2026-11-04_internal_B8-fdtd/RESPONSE.md`): the flux monitor sees every plane wave weaker by
  cos(k dx/2) ≈ 1 − (k dx)²/8 while the engine divided by the exact intensity; "the engine nearer the exact value in 13 of
  18 rows" was an artefact of it [error in earlier]. Fixed: `FDTD.monitor_factor`, `normalisation="monitor"`.
* Like-normalised, both codes give the same discrete reflectance to 1e-6 (slab) and 6e-6 (Drude, whose update differs
  from Meep's at second order); for the cylinder both lie within their own convergence bounds of the exact series, Meep
  nearer to it (its full-tensor sub-pixel averaging against the engine's diagonal one: STATUS V43 (b)).
* The engine's accuracy itself rests on its exact references (the grid's discrete reflectance, Fresnel/Airy, the
  cylinder and Mie series, cavity modes, the dipole's power: `../tests/test_fdtd_*.py`), not on this comparison.

## The set-up and the tolerances (from the script's docstring)

``lfphys.core.em.fdtd`` against Meep 1.35.0 (MIT's FDTD solver, pymeep from conda-forge; GPL-2.0-or-later) — plan
items P1 and P13. Runs only in the test-only image light-funnel-ext-meep (``docker/meep/Dockerfile``; never
distributed). Meep is used here as a library through its documented Python interface; none of its code was read for or
copied into the engine.

Reworked after review B8-fdtd (F5, F8). Both codes are like-normalised: Meep divides the reflected (scattered) flux by
the incident flux its own monitor measures in a normalisation run; the engine divides by
``incident_intensity(normalisation="monitor")``, the incident wave as its flux monitor measures it (a closed form,
``FDTD.monitor_factor``). Before the review the engine divided by the exact intensity, which its monitor sees weaker by
cos(k dx/2) = 1 - (k dx)^2/8 + ...: that bias alone made the 1-D rows differ by 6e-4 ... 6e-3, and "the engine nearer
the exact value in 13 of 18 rows" was an artefact of it [error in earlier].

**1-D rows** (normal-incidence R of a dielectric slab n = 2, d = 0.5, and of a Drude half-space fp = 2, gamma = 0.1;
Meep's DrudeSusceptibility(frequency=fp, gamma, sigma=1) is the same function; f = 0.6 ... 1.4, off the slab's
Fabry-Perot zeros at f = 0.5, 1, 1.5, where R = 0 tested nothing; 40 cells per unit). Both codes solve the same discrete
problem — the Yee grid at S = 0.5, the interface on an E node (the slab's with the arithmetic mean of eps, Meep's
averaging and the engine's alike; the half-space's node wholly Drude in both, checked: an averaged node would move R by
3e-3) — whose exact reflectance R_d is computed here by the discrete transfer recursion
E_{i-1} = (2 - (Omega dx)^2 eps_i) E_i - E_{i+1} over the engine's node profile, with the scheme's own eps_d(f). R_d is
the exact reference of these rows (eng_err, lib_err). Tolerance "one discrete problem" (slab): each side's R differs
from R_d only through (a) its absorbing layer, whose reflection amplitude A returns into the reflected wave once:
|dR| <= 2 |r| (|r|^2 + |t|^2) A <= 2A (lossless), and (b) the end of its DFT window, W; tol = 2 (A_eng + A_meep) +
W_eng + W_meep, with A measured in this module by a control (a source three cells from the layer, probed three cells
from it, against a run ten times longer: engine CPML 20 cells -110 dB, Meep PML 1.5 units -130 dB at 40 cells) and W
as the change of R when the run is extended (engine: 16 -> 48 time units after the pulse; Meep: field decay 1e-11 ->
1e-13). Tolerance "one discrete problem + Meep's Drude scheme" (Drude rows): Meep's Drude update is not the engine's
to the last digit (Meep's own distance to R_d falls as dx^2: 2.4e-5 at 20 cells, 5.4e-6 at 40); its 20-cell distance
bounds its 40-cell one when that difference converges, which ``test_meep_drude_difference_converges`` checks; tol =
the slab's form + |R_meep,20 - R_d,20|.

**Cylinder rows** (Q_sca of a dielectric cylinder m = 1.5, a = 0.5, TM and TE, f = 0.4 ... 1.0, 40 cells per unit).
The codes discretise the surface differently (Meep's anisotropic averaging with the full tensor, the engine's diagonal
VP-EP form, F6), so they do not solve the same discrete problem. Exact reference: the series (``core.optics.cylinder``).
Tolerance "coarser-grid errors, monotone": each side's error at 40 cells is bounded by its error at 20 cells,
provided its error decreases monotonically over 20, 40 and 80 cells, which ``test_cylinder_convergence_is_monotone``
checks for both codes (no order is assumed; review B8-fdtd F8: the Richardson bound assumed second order, which the
engine's TE row at f = 0.4 violated); tol = |v20_eng - exact| + |v20_meep - exact|.

## Results (generated 2026-11-04 in light-funnel-ext-meep, Python 3.11.18)

### Summary

| library | comparisons | pass | xfail (known) | FAIL | max diff/tol (passing) | engine closer to exact | library closer | equal |
|---|---|---|---|---|---|---|---|---|
| Meep 1.35.0 (FDTD; conda-forge pymeep, own image light-funnel-ext-meep) | 20 | 20 | 0 | 0 | 0.318 | 3 | 17 | 0 |

*engine closer / library closer / equal*: among the rows with an exact reference, which side is nearer to it.

### Known disagreements

None.

### Tolerance bases

| basis | meaning (details in the module docstrings) |
|---|---|
| coarser-grid errors, monotone | different surface discretisations: each side's error at 40 cells bounded by its error at 20 cells against the exact series, valid where the error falls monotonically over 20, 40, 80 cells (checked per side); tol = the sum |
| one discrete problem | both FDTD codes solve the same discrete problem (exact: the grid's discrete R by the transfer recursion); each side differs from it only by its absorbing layer (2A, A its reflection amplitude measured by a control run) and its DFT window (W, the change of R when the run is extended); tol = 2(A_eng + A_meep) + W_eng + W_meep |
| one discrete problem + Meep's Drude scheme | as 'one discrete problem', plus \|R_meep - R_d\| at 20 cells: Meep's Drude update differs from the engine's at second order, so its 20-cell distance bounds its 40-cell one (checked) |

### Meep 1.35.0 (FDTD; conda-forge pymeep, own image light-funnel-ext-meep) (`test_ext_fdtd_meep.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| R (slab n=2 d=0.5) | f = 0.6, 40 cells per unit | 0.163151169382501 | 0.163151982337412 | 8.13e-07 | 7.12e-06 | pass | one discrete problem | 1.76e-06 | 9.49e-07 |
| R (slab n=2 d=0.5) | f = 0.75, 40 cells per unit | 0.355942229349395 | 0.355942421084543 | 1.92e-07 | 7.12e-06 | pass | one discrete problem | 1.16e-06 | 9.66e-07 |
| R (slab n=2 d=0.5) | f = 0.9, 40 cells per unit | 0.152707874588994 | 0.152707715002231 | 1.60e-07 | 7.12e-06 | pass | one discrete problem | 1.15e-06 | 9.92e-07 |
| R (slab n=2 d=0.5) | f = 1.1, 40 cells per unit | 0.169464396708937 | 0.169463670222773 | 7.26e-07 | 7.12e-06 | pass | one discrete problem | 1.00e-06 | 2.75e-07 |
| R (slab n=2 d=0.5) | f = 1.25, 40 cells per unit | 0.348093673178966 | 0.348094334644697 | 6.61e-07 | 7.12e-06 | pass | one discrete problem | 1.32e-06 | 6.62e-07 |
| R (slab n=2 d=0.5) | f = 1.4, 40 cells per unit | 0.129837731786709 | 0.129838840092566 | 1.11e-06 | 7.12e-06 | pass | one discrete problem | 1.59e-06 | 4.84e-07 |
| R (Drude half-space fp=2 gamma=0.1) | f = 0.6, 40 cells per unit | 0.901937932109637 | 0.901939831314351 | 1.90e-06 | 1.08e-05 | pass | one discrete problem + Meep's Drude scheme | 2.06e-06 | 1.56e-07 |
| R (Drude half-space fp=2 gamma=0.1) | f = 0.75, 40 cells per unit | 0.899143768163957 | 0.899145911382066 | 2.14e-06 | 1.52e-05 | pass | one discrete problem + Meep's Drude scheme | 4.63e-06 | 2.49e-06 |
| R (Drude half-space fp=2 gamma=0.1) | f = 0.9, 40 cells per unit | 0.895474352839415 | 0.895480599236438 | 6.25e-06 | 1.96e-05 | pass | one discrete problem + Meep's Drude scheme | 5.05e-06 | 1.20e-06 |
| R (Drude half-space fp=2 gamma=0.1) | f = 1.1, 40 cells per unit | 0.888656095835644 | 0.888655328868006 | 7.67e-07 | 1.44e-05 | pass | one discrete problem + Meep's Drude scheme | 2.46e-07 | 5.21e-07 |
| R (Drude half-space fp=2 gamma=0.1) | f = 1.25, 40 cells per unit | 0.881387068445123 | 0.881387223380999 | 1.55e-07 | 2.50e-05 | pass | one discrete problem + Meep's Drude scheme | 2.25e-06 | 2.09e-06 |
| R (Drude half-space fp=2 gamma=0.1) | f = 1.4, 40 cells per unit | 0.871159603714331 | 0.871164629568311 | 5.03e-06 | 2.47e-05 | pass | one discrete problem + Meep's Drude scheme | 3.26e-06 | 1.76e-06 |
| Q_sca (cylinder m=1.5, a=0.5, TM) | f = 0.4, 40 cells per unit | 1.21256104374581 | 1.21236350290307 | 1.98e-04 | 8.15e-03 | pass | coarser-grid errors, monotone | 1.20e-03 | 1.00e-03 |
| Q_sca (cylinder m=1.5, a=0.5, TM) | f = 0.6, 40 cells per unit | 2.3952074399394 | 2.39457680686791 | 6.31e-04 | 2.46e-02 | pass | coarser-grid errors, monotone | 3.35e-03 | 2.72e-03 |
| Q_sca (cylinder m=1.5, a=0.5, TM) | f = 0.8, 40 cells per unit | 3.51212948151159 | 3.5110579785376 | 1.07e-03 | 6.75e-02 | pass | coarser-grid errors, monotone | 8.95e-03 | 7.87e-03 |
| Q_sca (cylinder m=1.5, a=0.5, TM) | f = 1, 40 cells per unit | 4.09394337296832 | 4.09248457581065 | 1.46e-03 | 1.15e-01 | pass | coarser-grid errors, monotone | 1.52e-02 | 1.38e-02 |
| Q_sca (cylinder m=1.5, a=0.5, TE) | f = 0.4, 40 cells per unit | 0.55263066902794 | 0.553866250300754 | 1.24e-03 | 4.03e-03 | pass | coarser-grid errors, monotone | 3.70e-04 | 8.65e-04 |
| Q_sca (cylinder m=1.5, a=0.5, TE) | f = 0.6, 40 cells per unit | 1.67996659392642 | 1.68024452752874 | 2.78e-04 | 2.87e-02 | pass | coarser-grid errors, monotone | 3.41e-03 | 3.68e-03 |
| Q_sca (cylinder m=1.5, a=0.5, TE) | f = 0.8, 40 cells per unit | 2.83670049647868 | 2.83389847736018 | 2.80e-03 | 8.79e-02 | pass | coarser-grid errors, monotone | 1.28e-02 | 9.95e-03 |
| Q_sca (cylinder m=1.5, a=0.5, TE) | f = 1, 40 cells per unit | 3.56595639073787 | 3.55952255519899 | 6.43e-03 | 1.36e-01 | pass | coarser-grid errors, monotone | 2.13e-02 | 1.49e-02 |
