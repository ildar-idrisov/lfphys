# Comparison suite: lfphys against third-party libraries (plan item P13)

An optional test suite that checks the engine's accuracy against independent third-party implementations. It runs in
its own Docker image, `lfphys-ext`, and nowhere else.

## 1. The rule

The owner, 2026-10-24 (verbatim, `../../../AGENTS.md` §3 rule 8):

> сравнения со сторонними библиотеками для проверки точность движка, используй сторонние библиотеки только для тестов
> сравнения

> при разработке не используй сторонние библиотеки с лицензиями закрытыми для коммерческого применения

The owner, 2026-11-10 (verbatim), on libraries under any licence:

> давай разрешим подобные тесты на любых лицензиях, но только для сравнения нашего результата со сторонними. все эти
> модули должны запускаться в одном отдельном контейнере и храниться отдельно и только временно для разового запуска. в
> репозиторий не заливать, импользовать по необходимости. например тут, если видишь что нужно запустить тест с Meep и
> сравниться, то делаешь это, сравниваешься, получаешь результаты, когда Meep перестает быть нужным, то удаляешь его.
> запускать подобный код с лицензией gpl не запрещается, главное не внедрять его в проект на постоянке.

and (same day) that the comparisons with permissively licensed libraries stay in the repository as they are. Hence two
tiers:

* **Permissive libraries** (MIT, BSD, Apache-2.0 and the like): their comparison modules live in this folder and run in
  its image `lfphys-ext` — the suite below.
* **Copyleft or restricted libraries** (GPL, AGPL, LGPL used beyond linking, licences that restrict use or the
  publication of results, unclear licences): a comparison is run once, when it is needed, from a script kept outside
  the repository, in a throwaway image of its own; nothing of it is committed except a dated record of the set-up and
  the results in `../../sources/comparison_<date>_<library>.md`; the script and the image are deleted when the library
  is no longer needed. Before a run, the licence's terms of use are checked, not only those of distribution (some
  restrict use or forbid publishing benchmarks). Running GPL code is not restricted (GPL-2 §0: "The act of running the
  Program is not restricted"); only distributing it binds. Done so far: Meep 1.35.0 (FDTD, GPL-2.0-or-later),
  2026-11-04, `../../sources/comparison_2026-11-04_meep.md`.
* Third-party physics libraries appear only in this folder, its image, or such a one-off run.
* They are never imported by engine code (`lfphys/`), never added to the runtime image `lfphys-viz` or its
  `visualizations/docker/requirements.lock`, and never listed in `ALLOWED` of `../test_licences.py`.
* The image is **for local testing only and is never distributed**: it is not pushed to a registry, exported or
  shared. At the pinned versions no package in it is under a strong-copyleft licence (§5). The image is nevertheless
  kept test-only, because a library's licence may change with its version.
* The main suite does not collect this folder. `../conftest.py` sets `collect_ignore = ["external"]` unless
  `LFPHYS_EXTERNAL=1`, and only the image sets that variable. `pytest -q` in the runtime image therefore never
  imports these libraries.
* Naming the folder explicitly without the variable collects nothing either. This folder's `conftest.py` ignores its
  test modules and says why in the session header.

## 2. What is compared

Each test module computes a list of rows (quantity, inputs, the engine's value, the library's value, the tolerance and
how it was derived). The tests assert them one by one, and `make_results.py` writes the same rows to `RESULTS.md`.

| engine | library | module | rows | what |
|---|---|---|---|---|
| `core.qcd.running` | CRunDec 3.1 (Python bindings `rundec` 0.7) | `test_ext_qcd_rundec.py` | 216 | alpha_s(mu) at 1-4 loops, fixed n_f = 3...6 from M_Z to 1.5-3000 GeV (80 rows); across the c, b, t thresholds with MS-bar decoupling at m_h(m_h), as in the engine (40); the decoupling relations alone (96) |
| `core.gravity.kerr`, `core.gravity.kerr_orbits` | KerrGeoPy 0.9.3 | `test_ext_kerr_kerrgeopy.py` | 1056 | ISCO and marginally bound orbit, pro- and retrograde, chi from 0 to 1 - 1e-12 (40); E and L of circular orbits from r_isco(1 + 1e-6) to 1e4 r_isco (168); horizons (14); the engine's radial potential at the turning points of eccentric orbits, using KerrGeoPy's E and L (72); generic orbits (P7): E, L_z, Q of 120 eccentric inclined orbits, chi 0.3-0.99, e 0.1-0.8, x = cos(inclination) from -0.9 to 0.9, p = 1.3 x separatrix and 25 (360), polar orbits against KerrGeoPy's separate closed forms (24); the Mino frequencies Upsilon_r, Upsilon_theta, Upsilon_phi, Gamma and Omega_r, Omega_theta, Omega_phi of 54 of them (378) |
| `core.optics.interfaces`, `core.optics.thin_films` | tmm 0.2.0 | `test_ext_optics_tmm.py` | 476 | Fresnel coefficients up to 89.999 deg, the critical angle, TIR and metals; multilayers (AR coating, a 20-layer Bragg mirror, Kretschmann SPR, frustrated TIR across 0.1-20 um, an absorbing 4-layer stack, an opaque 2 um metal); r, t, R, T for s and p; the Airy sum, Airy T, quarter-wave R, FTIR T, evanescent decay length, absorption per layer and \|E\|^2 inside the layers |
| `core.quantum.qubits` | QuTiP 5.3.1 | `test_ext_qubits_qutip.py` | 110 | singlet correlations and CHSH, \|Phi+> polarizer correlations, Born probabilities, Lueders states, partial trace, Bloch vector, entropy, concurrence, precession exp(-i omega t n.sigma/2) up to omega t = 1000 |
| `core.quantum.open_systems`, `two_level`, `jumps` | QuTiP 5.3.1 | `test_ext_open_qutip.py` | 91 | the Lindblad superoperator of five systems (two two-level atoms with T1, T2; a Lambda system; a driven thermal oscillator; two qubits with collective decay) (5); rho(t) of these systems against QuTiP's diagonalising `mesolve` at t = 0-6 (20); a circularly driven atom in the lab frame (time-dependent H) against QuTiP's Verner 9(8) `mesolve`, with the exact rotating-frame solution as reference (7); steady states against `steadystate(method="direct")`, with closed forms (Bloch equations, the Lambda dark state, the thermal ladder) (5); quantum-jump trajectory means of P_e, sigma_x, sigma_y against `mcsolve` (51); the waiting-time distribution of fluorescence photons, two-sample against `mcsolve`'s collapse times, with the closed form (3) |
| `core.constants`, plus the constants of `quantum.particles`, `hydrogen`, `compton`, `optics.radiation` | Astropy 8.0.2 | `test_ext_constants_astropy.py` | 25 | every constant the engine takes from scipy.constants or IAU resolutions; the CODATA and IAU editions of both sides |
| `core.cosmology.flrw`, `theories.models.dark_energy` (P8, B7) | Astropy 8.0.2 (`astropy.cosmology`) | `test_ext_flrw_astropy.py` | 661 | six universes (flat LCDM without radiation, where Astropy uses closed forms; flat, open and closed LCDM and flat w0-wa with photons and massless neutrinos; Planck 2018 with a 0.06 eV neutrino in Astropy's convention, the engine given m (N_eff/3)^(1/4)) at z = 0.001-1000: D_C, D_M, D_A, D_L, mu, lookback time, age, H, Omega_m, Omega_de, Omega_k, rho_crit; Omega_gamma0, Omega_nu0, T_nu0, rho_crit0, c/H0, 1/H0; D_A(z1, z2); the neutrino density through Komatsu et al. 2011's fit. One known library-side error kept as a strict xfail (Astropy's age at z = 1000 of the closed universe: QUADPACK 1.4 % off, beyond its own estimate) |
| `core.optics.mie` (P1, B8) | miepython 3.3.0 (with numba 0.68.0, llvmlite 0.50.0) | `test_ext_mie_miepython.py` | 326 | 15 spheres (m = 1.333 from x = 0.1 to 10⁴, 1.333 + 1e-8i, 1.5 + 0.1i to x = 3000, 0.75, 2 + i, 10 + 10i): Q_ext, Q_sca, Q_back, g (60); S1, S2 at 0°, 30°, 90°, 137.9°, 170°, 180° (180); a_n, b_n at n = 1, N/2, N (86). Six known library-side disagreements kept as strict xfails: miepython's coefficients carry an error of about the same size at every order, 3.7e-13 – 4.2e-13 of the largest at x = 100 and 7e-10 – 1.2e-9 at x = 10⁴ (up to 3e-8 near n ≈ x), beyond the 16 N u allowance (the x = 100 rows were covered before review B8-mie by the engine's blanket 2e-11 budget, replaced by its bound u (4N + 8 x\|da_n/dx\|/max\|a\|) with the exact coefficients' sensitivity); miepython stops at Wiscombe's N without margin, and its omitted tail (up to 2e-6 of the largest coefficient at x = 10⁴) is part of its budget |

Besides these 2961 rows in `RESULTS.md`, 25 tests support them (the one-off Meep comparison of 2026-11-04 is recorded in
`../../sources/comparison_2026-11-04_meep.md`):

* a re-implementation of CRunDec's step-size control (it reproduces CRunDec bit for bit) and attribution tests;
* checks that the mpmath references are what they claim to be;
* checks of conventions and editions;
* a check that QuTiP's quantum-jump sampler has the waiting-time form the engine uses (exponential collapse times of a
  pure decay), and of the stage count of QuTiP's Verner 9(8) behind the step bound of the time-dependent rows.
* the conventions behind the FLRW rows (Astropy's Om0 without massive neutrinos, its neutrino temperature and density
  convention, scipy's quad defaults), and the cause of the one FLRW xfail (Astropy's integration, not its integrand).

The result is in `RESULTS.md`: per library, the counts and, where an exact reference exists, which side is closer to
it; the known disagreements with their numbers; every row.

**Not compared yet, and why:**

* KerrGeoPy has no circular-photon-orbit routine. It refuses an orbit exactly at the separatrix, so the radiative
  efficiency at the ISCO cannot be compared. It does not support chi = 1, nor the frequencies of polar orbits.
* `lfphys.core.data` holds PDG, NASA and experiment values, which Astropy does not have.
* QuTiP's ODE solvers (`sesolve`, `mesolve`) control only the local error. For the qubit precession no global tolerance
  is derived from them, and `Qobj.expm` calls the same scipy routine as the engine, so it would not be an independent
  check: the precession is compared with QuTiP's closed-form rotation gates instead. For open systems (P5) a global
  tolerance does follow from the local control: the Lindblad flow is completely positive and trace preserving, hence a
  contraction in the trace norm, and the equation is linear, so the global error is at most the sum of the local
  errors; the steps are bounded by the counted calls of a coefficient function divided by the 16 stages of QuTiP's
  Verner 9(8) (basis "engine estimate + Verner control" in `test_ext_open_qutip.py`). Constant generators are compared with QuTiP's diagonalising integrator, whose
  decomposition is checked a posteriori in mpmath.
* CRunDec's `AlL2AlH` and `AlH2AlL` decouple at pole masses, a different physics input. The engine's MS-bar
  convention is rebuilt from CRunDec's `AlphasExact` and `DecAsDownMS` / `DecAsUpMS`.

## 3. How the tolerances are derived

The tolerance of every row is the sum of the two sides' error bounds. A bound comes from one of three sources: the
side's stated error control, a rounding analysis of its actual operations, or the conditioning of the problem. Each
module's docstring gives the full derivation, and the column *basis* of `RESULTS.md` names it.

* **Integrators** (alpha_s):
  * CRunDec accepts a Runge-Kutta step when its error estimate is below 1e-10 in alpha_s/pi.
  * The engine's DOP853 accepts a step when its error estimate is below rtol 1e-12 (plus atol 1e-16).
  * The accepted steps are counted for both sides: for CRunDec by a re-implementation of its controller, for the
    engine by wrapping scipy's `solve_ivp`.
  * Each step's error is propagated to the end with the exact factor f(a_end)/f(a_k).
* **Running error bounds** (Kerr closed forms, the quarter-wave and FTIR formulas): `_common.Fe` evaluates each
  side's own code with first-order error tracking. The tracked value must equal the float result bit for bit.
* **Conditioning** (generic Kerr orbits, P7): the engine polishes E, L, Q by Newton steps on their defining
  equations, so its error is bounded by |J^-1| times the round-off of the equations' evaluation (J their Jacobian);
  KerrGeoPy's unpolished closed form by its running error bound. The frequencies: 256 u per input, per constant and on
  the result, propagated with the engine's own sensitivities (central differences), plus KerrGeoPy's constants'
  running bounds propagated the same way. Exact references: the defining equations solved by mpmath's findroot at
  40 digits, the frequencies by 30-digit quadratures of the periods and averages.
* **Root finding** (KerrGeoPy's separatrix): brentq's xtol and rtol, plus the width of the region where the
  separatrix polynomial cannot be told from zero within its evaluation error. Near chi = 1 the polynomial has a triple
  root, and this term dominates.
* **Transfer matrices** (tmm). Three contributions:
  * a backward error of 16u in every input, admittance and phase, weighted by sensitivities computed in mpmath;
  * tmm's absolute error in cos(arcsin x);
  * the rounding of the chain of 2x2 products, bounded by the product of the moduli.
* **Linear algebra** (QuTiP):
  * contractions: gamma_n times the sum of the moduli of the terms;
  * eigenvalues: LAPACK's p(n) u ||A|| with p(n) = 10n (LAPACK Users' Guide), carried through h(x) = -x log2 x for
    the entropy and through sqrt for the concurrence;
  * scipy's expm: backward error u||A||, and exp is 1-Lipschitz on skew-Hermitian matrices.
* **Open systems** (QuTiP, `test_ext_open_qutip.py`):
  * Liouvillians: gamma_k times the moduli of the kron terms of every entry, per side;
  * propagation by a constant generator: the engine's stated expm bound (`open_systems.expm_error_bound`); QuTiP's
    eigendecomposition checked a posteriori in mpmath (the residuals L U - U Lambda and U Uinv - I), plus the
    roundings of its application; both carried by the trace-norm contraction of the Lindblad flow;
  * a time-dependent drive: each side's stated local error control (the engine's step doubling of Radau IIA, QuTiP's
    Verner 9(8) pair) summed over the steps, which is a global bound because the flow contracts the trace norm and the
    equation is linear;
  * steady states: Wedin's bound for the engine's SVD null vector, cond(A) p(n) u for QuTiP's LAPACK solve;
  * Monte Carlo: 5 standard errors of the two trajectory means; the Dvoretzky-Kiefer-Wolfowitz bound (alpha = 1e-6
    per sample) for the two waiting-time distributions; QuTiP's collapse-time tolerances as a bias.
* **Mie** (miepython): coefficient budgets + truncation — the engine's tested coefficient bound and miepython's
  measured coefficient error, each propagated with the moduli of the row's partial derivatives, plus miepython's
  omitted tail (exact, mpmath) and gamma_{8N} of the moduli of the sums; the exact reference is the series in 40-digit
  mpmath.

* **Constants**: a value that both sides parse from the same published decimal must be the same binary64 number
  (tolerance 0). A value computed from such numbers may differ by its roundings.

No tolerance is loosened to make a row pass. A measured disagreement beyond the derived tolerance is kept as
`xfail(strict=True)`, with the measured numbers in its reason. A dedicated test pins its cause. If the disagreement
disappears, the strict xfail fails and the record has to be revisited.

**Exact references.** Wherever the solution is known exactly, it is evaluated in 30-50-digit mpmath for the same
binary64 inputs, and RESULTS.md gives each side's distance to it (*eng err*, *lib err*). The references are:

* the closed forms of Kerr, Fresnel, quarter-wave, alpha_s at one loop, and the qubit formulas;
* the renormalisation-group equation, solved by quadrature;
* the transfer matrices, evaluated in mpmath;
* the Lindblad equations: the Liouvillian and its exponential in mpmath, the lab-frame drive through the exact rotating
  frame, the closed-form steady states (Bloch equations, the Lambda dark state, the thermal ladder) and the closed-form
  waiting-time distribution of fluorescence photons.

A disagreement is attributed to one side only on this evidence.

## 4. Build and run

The commands run from `engine/`, the repository root, and the image `lfphys-viz:latest` must exist. Build it
with `docker compose -f visualizations/docker/docker-compose.yml build`. The suite needs no GPU and must be run
without `--gpus`.

```sh
# build the comparison image (needs PyPI access; installs requirements-external.lock with --no-deps, then pip check)
docker build -f lfphys/tests/external/docker/Dockerfile -t lfphys-ext:latest .

# run the comparison suite (about 25 s)
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/lfphys -e LFPHYS_EXTERNAL=1 \
    lfphys-ext:latest python3 -m pytest -q -p no:cacheprovider tests/external

# regenerate RESULTS.md (exit status 1 if a row fails or a recorded disagreement has disappeared)
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/lfphys -e LFPHYS_EXTERNAL=1 \
    lfphys-ext:latest python3 tests/external/make_results.py

# the main suite stays in the runtime image and does not collect tests/external
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/lfphys lfphys-viz:latest \
    python3 -m pytest -q -p no:cacheprovider
```

Run only `tests/external` in `lfphys-ext`. The licence audit `../test_licences.py` belongs to the runtime image.
In this image it would rightly report the comparison libraries as unpinned, unaudited packages.

The pins are in `docker/requirements-external.lock`: every package that the six libraries add to the runtime image,
as name==version. They were found by installing the libraries, constrained to the runtime image's versions, in a
throwaway container, then running `pip freeze`. numpy, scipy, mpmath and pytest stay at the runtime image's versions.
Changing a pin means:

1. re-running the suite and `make_results.py`;
2. re-auditing the licence;
3. updating `../../sources/dependencies.md` §10.

## 5. Licences

The full audit is in `../../sources/dependencies.md`, §10 "Comparison-only libraries (plan P13)". It covers the
installed metadata, each repository's LICENSE file, the 16 packages the libraries pull in (numba and llvmlite added with miepython in B8), and the libraries bundled
inside the wheels.

| library | version | licence (metadata) | licence (repository LICENSE file) |
|---|---|---|---|
| rundec (CRunDec bindings) | 0.7 | MIT | MIT. The CRunDec 3.1 source compiled into the wheel is MIT: "Jan 2019: Changed license from GPLv3 to MIT" (CRunDec.cpp, v3.1) |
| kerrgeopy | 0.9.3 | MIT (classifier) | MIT |
| tmm | 0.2.0 | MIT | MIT |
| qutip | 5.3.1 | BSD-3-Clause | BSD-3-Clause |
| astropy | 8.0.2 | BSD-3-Clause | BSD-3-Clause |
| miepython | 3.3.0 | MIT | MIT (LICENSE.txt, "Copyright 2017-2021 Scott Prahl"); it pulls in numba 0.68.0 (BSD-2-Clause) and llvmlite 0.50.0 (BSD-2-Clause AND Apache-2.0 WITH LLVM-exception) |

The plan (`../../PLAN.md`, P13) listed rundec/CRunDec as "GPL-3". That was true of CRunDec up to version 3.0; the
version in use is MIT (the plan was corrected on 2026-10-27).

## 6. Files

| file | content |
|---|---|
| `_common.py` | the result row, the running error bound `Fe` and the bounded `math` |
| `test_ext_*.py` | the eight comparisons and their derivations |
| `conftest.py` | collects the test modules only with `LFPHYS_EXTERNAL=1`; filters a packaging DeprecationWarning of the SWIG bindings |
| `make_results.py` | writes `RESULTS.md` (`--help`) |
| `RESULTS.md` | the generated table (kept in the repository) |
| `docker/Dockerfile`, `docker/requirements-external.lock` | the image `lfphys-ext` and its pins |
