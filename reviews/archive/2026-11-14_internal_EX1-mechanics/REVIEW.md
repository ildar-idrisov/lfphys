# Review R-E (EX1-mechanics): the physics and statistics of engine M1's projectile part, and their use in S03

**Status: awaiting processing.** Reviewer: an internal subagent (Claude Opus). It did not write the code under review.
Delivered 2026-11-17 against commit 507c059 (clean). Per `reviews/README.md`, the reviewer does not write
`RESPONSE.md`, decide on the findings or move this folder. The brief named this path under `archive/`.
`reviews/README.md` puts new reviews at the top level of `reviews/`, so the integrator may move the folder.

| | |
|---|---|
| Scope | `lfphys/lfphys/core/mechanics/**`; `lfphys/lfphys/theories/models/drag_quadratic.py`; the air data in `core/data.py`; `lfphys/lfphys/tools/stats.py` `linear_fit`; their tests; S03's use of them (`visualizations/s03_projectile/viz.py`, `engine/shot.py`, its README, `tests/test_s03_physics.py`); `visualizations/player/js/fit.js` (and its use in `lab.js` `checkLaw`) |
| Not in scope | The atlas framework, the screens in a browser, the teaching texts as a teacher reads them (R-F, R-P, R-W) |
| Environment | Docker, CPU only. `lfphys-viz` (959a1b91570e: Python 3.11.17, NumPy 2.4.6, SciPy 1.17.1, mpmath 1.3.0) and `node:24`. The repository was mounted read-only. Containers were named `lf-rve-*`, with `--memory` 1–6 g. No server or port was used |
| Files as reviewed | `evidence/reviewed_files.sha256` (with the HEAD hash) |

## Reproduction

The scripts are in `evidence/scripts/`. Each one was run from the repository root, with its output folder mounted at
`/out`:

```
docker run --rm --name lf-rve-<x> --memory=3g --cpus=2 -e LFPHYS_NO_GPU=1 -e PYTHONDONTWRITEBYTECODE=1 --user 1000:1000 \
  -v "$PWD":/lf:ro -v <evidence>:/out -w /lf/visualizations lfphys-viz python3 /out/scripts/<script>.py
docker run --rm --name lf-rve-h --memory=1g -v "$PWD":/lf:ro -v <evidence>:/out -w /out node:24 node /out/scripts/h_fitjs.mjs
```

(`h_fitjs.mjs` reads `g_fit_cases.json`, which `g_fit.py` writes.)

| script → output | what it checks |
|---|---|
| (authors' pytest) → `authors_tests.out`, `authors_layers.out`; (authors' node tests) → `authors_fit_js.out` | `test_mechanics_air`, `test_mechanics_projectile`, `test_stats_fit`, `test_s03_physics`: 91 passed. `test_layers`: 210 passed. `fit.test.mjs` and `lab.test.mjs`: 12 passed |
| `a_closed_forms.py` → `a_closed_forms.out` | The closed forms in vacuum and with linear drag against mpmath (50 digits). The Lambert-W landing time against a 50-digit bisection of the landing condition, k from 3 to 1e-5 1/s |
| `b_hodograph.py` → `b_hodograph.out` | The quadratic-drag flight three ways: the engine, the hodograph, and an independent 30-digit Taylor-series integration (`mpmath.odefun`). Also steep launches |
| `d_energy_validity.py` → `d_energy_validity.out` | The carried drag work against a quadrature of F·v on an independent Radau solution. `validity()`'s share against a 2·10⁶-point independent computation. The drag-curve numbers. S03 with the measured curve instead of the constant. The Basset force (Maxey–Riley) against the stated estimate |
| `f_lab.py` → `f_lab.out` | S03's three lab steps as the player computes them: rounding, derived errors, the fit, and the verdict \|q − ref\| ≤ 2σ. Run on the full tables and on every subset of rows |
| `g_fit.py` → `g_fit.out` | `linear_fit` against York et al. (2004) on Pearson–York. A Monte Carlo of the effective variance with random x errors. Singular designs. The 2σ verdict at small dof |
| `h_fitjs.mjs` → `h_fitjs.out` | `fit.js` against `linear_fit` on 61 random cases and on degenerate input |
| `i_lab_more.py` → `i_lab_more.out` | On the lab tables: the effective-variance fixed point against the minimum of S. The verdict on axes other than the law's |

The sources were downloaded to the reviewer's scratch folder, not to the repository. The quotations, read from the
downloaded text, are in `evidence/sources_checked.txt`.

## Summary

| # | severity | finding | tag |
|---|---|---|---|
| F1 | should-fix | The check «the constant drag coefficient holds along the path» passes on every S03 flight, but it tests only the Reynolds range. On the same paths the measured curve gives C_d 0.40–0.42 against the model's 0.47. With that curve the ranges are 3–4.6 % longer, and lab part C's optimum is 42.30° instead of the reference 41.9° (2.3 σ of the student's vertex) | [weakens] |
| F2 | should-fix | The Lambert-W landing time loses accuracy as ~1e-16/s², not "~1e-16/s" as stated. With weak drag the closed form misses the engine's own 1e-9: by 8e-9 at s = 1.5e-4 and by 7e-7 at s = 2e-5, which is the Stokes regime of any real ball | [error in earlier] |
| F3 | should-fix | The core Stokes law's validity puts the Basset (history) force at "of order ρ_fluid/ρ_body (1.5e-4 for steel in air)". It scales as ~1.2·√(ρ_f/ρ_p): measured 1.4 % for steel and 4.0 % for a water droplet, as large as the Oseen error the module reports | [error in earlier] |
| F4 | should-fix | Lab part A: «the air shortens the range … less than the tape's error» is false at h = 1 m (0.544 mm against 0.5 mm). It is stated, not computed. The law «agrees» (z = −0.81) only because the ruler's declared ±5 mm, on heights the bench sets exactly, inflates σ_k fourfold; with the tape alone z = −3.07 | [weakens] |
| F5 | should-fix | `linear_fit`'s iterated effective variance is not the least-squares line (0.295 σ_b on Pearson–York, confirmed). With random x errors comparable to the x spread it is the attenuated OLS slope, with 54 % and 36 % coverage of its 95 % interval. York (2004) is as simple and consistent. S03 is not affected (≤ 0.001 σ) | [neutral] |
| F6 | nit | "The constant 0.47 errs by up to −18 % / +7 %" has the sign and base of (curve − 0.47)/0.47. The constant's error is +21 % / −7 %. The README gives "0.01" for the light ball's buoyancy ratio, which is 3.3e-3 | [neutral] |
| F7 | nit | `particle.py` states "1e-9 relative in … the range". For near-vertical throws the range's error is 1e-9 of the flight's length scale, not of L: 1.7e-8 of L at 89.9° and 1.4e-7 at 89.99° | [neutral] |
| F8 | nit | `linear_fit` on a singular design raises a raw `LinAlgError` (all x equal), or returns nonsense (a parabola on two distinct x: parameters ~1e15, σ ~1e27). `fit.js` refuses both | [neutral] |
| F9 | nit | The «Check against the law» rule \|Δ\| ≤ 2σ has three gaps: normal k = 2 when σ comes from the scatter (29.5 % false rejections at dof 1); no ceiling on the Birge scaling; no check of the plotted axes (L against h is compared with k in m^½, and the hint blames the readings) | [neutral] |
| F10 | nit | `linear_drag_landing_time` refuses c ≤ 0 (a launch downwards at or beyond the terminal speed), where its formula is exact (4e-16) | [neutral] |
| F11 | nit | The worksheet's numeric claims (air "less than 0.1 %", "about 0.5 % lower", "near 42°", "within one error") are in no test. Three are true today, and the fourth is F4 | [neutral] |

**Counts: 0 errors, 5 should-fix, 6 nits.**

What holds, by my own runs:
- **The closed forms.** The vacuum and linear-drag forms, the apex time and the Lambert-W branch choice are exact to
  1e-16 against mpmath.
- **The hodograph.** I re-derived it. It agrees to ≤ 4e-16 with a 30-digit Taylor-series integration, so it is an
  excellent second method. The engine's DOP853 is within 6e-12 of it.
- **The energy bookkeeping.** It is right: the carried work equals an independent quadrature of F·v.
- **`validity()`.** Its share agrees with an independent computation to 2e-5.
- **The sources.** Hoerner's 0.47 on p. 3-7, Morrison's eq. (1), Veysey–Goldenfeld's eq. (39) and the PDG's scale
  factor are all as quoted.
- **The lab verdicts.** Every subset of rows in all three lab steps agrees with its law. Part B with air would fail
  by 26.7 σ, as the design says.
- **`fit.js`.** It agrees with `linear_fit` to ≤ 4e-11.

---

## Findings

### F1 — should-fix — the C_d "validity" check cannot fail on S03, and the model's real error is not shown where it matters

**Where.**
- `visualizations/s03_projectile/viz.py:199–204`: the check labelled «the constant drag coefficient holds along the
  path», `ok = share ≤ VALID_SHARE`.
- `engine/shot.py:35`: `VALID_SHARE = 0.01`.
- `lfphys/lfphys/theories/models/drag_quadratic.py:145–178`: `validity`.
- `viz.py:127–133`: `lab_reference("air")`, whose «how» says only «computed by the engine … no closed form».
- `README.md:86, 98–101`.

**Evidence** (`d_energy_validity.out`).
- **S03 never leaves the Reynolds range.** The light ball is above 10³ for every v > 0.225 m/s, and its Re stays
  below 2·10⁵ up to 45 m/s (the schema stops at 40). So the check can only fail for a flight that spends > 1 % of its
  drag work below 0.225 m/s. None does: 0 to 7e-4 in every case run here.
- **On the same paths the model is not the measured curve.**
  ```
  validity at lab C (42 deg): share outside 0.0, Re 4.84e+04-8.9e+04, curve C_d 0.405-0.422 -> check 'holds' = True
  ball67 v0=20.0 th=40.0: L const 27.2222 m, L Morrison 28.2371 m (+3.73 %)
  ball67 v0=25.0 th=45.0: L const 36.2338 m, L Morrison 37.8905 m (+4.57 %)
  lab C optimum with C_d 0.47: 41.887 deg       lab C optimum with Morrison C_d(Re): 42.303 deg
  ```
- **The difference is large against the lab's precision.** The student's vertex is 42.03° ± 0.18° (`f_lab.out`).
  The model choice moves the reference by 0.42°, which is 2.3 σ. The check's note does print «the measured C_d … there
  0.41–0.42, the model's 0.47». But a ✓ under «holds» tells the student and the teacher the opposite.

**What is wrong.**
- The label claims a validity the check does not test. It tests "the path stays where the constant is *used*". It
  does not test that the constant is right there.
- The reference «θ* in air = 41.9°» is presented as the engine's result. It carries an unstated model uncertainty
  larger than the measurement's.

**Fix.**
- Rename the check, e.g. «the path stays in the Reynolds range of the constant C_d (10³–2·10⁵)».
- Add a second-model check that computes, not draws: the same flight with `cd_standard(Re)` as the drag, and the
  difference in L (and, for lab C, in θ*) reported as `info`.
- State in `lab_reference("air")`'s «how» that θ* depends on C_d: 41.9° with 0.47, 42.3° with the standard curve.
- `drag_quadratic` could expose a `QuadraticDrag` with `cd=callable(Re)` for this. The `CurveDrag` used here is 6
  lines.

### F2 — should-fix — the Lambert-W landing time is much less accurate for weak drag than stated

**Where.** `lfphys/lfphys/core/mechanics/drag.py:31–32` ("relative error ~ 1e-16 / s") and `:164–175`. The design
§4, Appendix A, quotes the same form.

**Evidence** (`a_closed_forms.out`; the reference is a 50-digit bisection of h′ + c(1 − e^{−s}) − s = 0):

```
k=0.001   h=2.0  vy0=6.0 : s=1.496e-03 rel.err=-9.95e-11  (doc ~1e-16/s=6.7e-14; 1e-16/s^2=4.5e-11)
k=0.0001  h=10.0 vy0=0.0 : s=1.428e-04 rel.err=+9.58e-09  (doc ~1e-16/s=7.0e-13; 1e-16/s^2=4.9e-09)
k=1e-05   h=0.0  vy0=10.0: s=2.039e-05 rel.err=+7.30e-07  (doc ~1e-16/s=4.9e-12; 1e-16/s^2=2.4e-07)
```

**Why the scaling is 1/s².**
- Near the branch point W ≈ −1 + √(2(1 + e z)), and 1 + e z is O(s²), formed from O(1) terms.
- A rounding of z by 1e-16 therefore moves W by ~1e-16/s, which is an absolute error in s. Relative to s it is
  1e-16/s².
- Stokes drag of the S03 steel ball (20 mm, 32.9 g) has k = 3πμd/m ≈ 1.0e-4 1/s. That gives s ≈ 1e-4, where the
  "reference" is off by ~1e-8, ten times the engine's stated 1e-9.
- Today only the tests call it, with s of order 1, so nothing fails yet.

**Fix.**
- Polish the root with one or two Newton steps on f(s) = h′ + (c − 1)(1 − e^{−s}) − (s − (1 − e^{−s})).
- In that form, c − 1 = v_y0/(gτ) is formed directly and the last bracket is `_s_minus_one_minus_exp`, so no O(s) terms
  cancel. Alternatively, form 1 + e z = −expm1(ln c + 1 − c − h′) and use W's branch-point series.
- Correct the docstring and the design, and add a test at k = 1e-4.

### F3 — should-fix — the stated size of the unsteady forces in Stokes's law is wrong by two orders of magnitude

**Where.** `lfphys/lfphys/core/mechanics/drag.py:14–15` ("they are of order rho_fluid / rho_body (1.5e-4 for steel in
air)") and the ABOUT `validity` at `:53–55` («no added mass, no Basset force, no buoyancy: of order ρ_fluid/ρ_body»).
The 50 µm droplet test, `test_mechanics_projectile.py:107–108`, cites only the Oseen error.

**Evidence** (`d_energy_validity.out`).
- **Set-up.** The Maxey–Riley equation in the Stokes regime, for a sphere released from rest, in units of τ_p and
  g·τ_p: (1 + R/2)·a = (1 − R) − v − 1.197·√R·∫₀ᵗ a(s)/√(t − s) ds, with R = ρ_f/ρ_p. It was integrated by product
  integration, converged in dt.
  ```
  steel:          R=0.000153: |dv|/v at t=tau_p 1.440%, fallen distance at 6 tau_p 1.163%   (stated 0.02 %)
  water droplet:  R=0.0012:   |dv|/v at t=tau_p 4.032%, fallen distance at 6 tau_p 3.277%   (stated 0.12 %)
  ```
- **What dominates.** Added mass and buoyancy are O(R), as stated. The Basset term is O(√R). For the droplet it is as
  large as the Oseen error 3 Re/16 the module reports (4.7 % in the test).

**Fix.**
- Write the estimate as "added mass and buoyancy ~ρ_f/ρ_p; the Basset history force ~√(ρ_f/ρ_p) while the body
  accelerates (≈ 1.4 % for steel, 4 % for water droplets in air), decaying as t^(−1/2) at terminal speed".
- Or add the history force as a declared force. The engine carries the state needed for it.

### F4 — should-fix — lab part A: the stated reason the law agrees is false, and the agreement rests on a declared error the bench does not have

**Where.**
- `viz.py:117–122`: the «how» of `lab_reference("heights")`, «… at most {d} % (computed by the engine), less than the
  tape's error».
- `viz.py:461`: the teacher's note, «… less than 0.1 %, below the tape's error, so the law without air agrees».
- `README.md:104–105`.
- The design's §5.3, row A.

**Evidence** (`f_lab.out`). The steel ball, v₀ 1.5 m/s, air on:

```
h=1.00 L_air=0.676857 L_vac=0.677401 air shortens by 0.080 % = 0.544 mm (tape error 0.5 mm, reading 0.677)
all 17 rows, line0: k=0.676871 ± 0.000654 (chi2/dof 0.0155, scaled False) vs 0.677401: z=-0.81 -> agrees
(sx=0) line0: k=0.676920 ± 0.000157 chi2/dof 0.375 scaled False: z=-3.07 -> DOES NOT AGREE
every subset of rows: {'line0': '0 of 131054 do not agree, largest |z| 0.89', 'line': '0 of 130918 do not agree ...'}
```

- **The percentage is right, the comparison is not.** «At most 0.08 %» is computed, and it is right. «Less than the
  tape's error» is a fixed phrase, and at h ≥ ~0.95 m it is false.
- **What the verdict rests on.** The verdict is robust (no subset fails), but not for the stated reason. The heights
  are set exactly on the 1 cm grid, yet each carries the ruler's declared ±5 mm. Propagated through √h, that error
  dominates σ_k: 0.00065 against 0.00016 from the tape alone. Without it the air's −0.08 % would be a 3 σ
  disagreement.
- **Part B disagrees with this reasoning.** Part B was switched to vacuum because the virtual bench would see the air
  (27 σ, confirmed: 26.7 σ).

**Fix.**
- Compute the comparison, e.g. the air's effect on k against the step's own σ_k, and phrase the «how» from the
  numbers.
- Or run part A in vacuum like part B.
- Or say plainly that the declared ruler error dominates.
- Change the teacher's note and the README to match.

### F5 — should-fix — the effective variance is neither the least-squares line nor consistent with random x errors; York (2004) would be

**Where.** `lfphys/lfphys/tools/stats.py:166–176`, `:213–228`; `fit.js:3–11`. The authors' coverage test
(`test_stats_fit.py:169–192`) uses only a benign case (x spread 4.5, σ_x = 0.1).

**Evidence** (`g_fit.out`).

```
York 2004: a=5.479910 b=-0.480533 sa=0.294971 sb=0.057985 S=11.8664      (the published benchmark, reproduced)
linear_fit (3 re-weightings): b=-0.463449 ... gap in b: +0.01708 = +0.295 York sb = +0.242 Birge-scaled sb
n=10 x in [0,1.0] sx=0.2 sy=0.05: mean b EV 1.5503, York 2.0944 (true 2); 95 % coverage EV 0.543, York 0.935
n=8  x in [0,1.0] sx=0.3 sy=0.05: mean b EV 1.2423, York 2.3176 (true 2); 95 % coverage EV 0.365, York 0.909
```

**What is wrong.**
- **The documented 0.3 σ gap is confirmed.** The module's "0.30 σ_b apart" is right, on the effective-variance σ and on
  York's σ alike.
- **The undocumented part.** With equal x errors the re-weighting leaves the weights equal, so the fixed point is the
  ordinary least-squares slope, and it is attenuated (regression dilution). The interval then badly under-covers.
- **Not S03's problem.** On S03's tables the x readings are exact, and the fixed point equals the minimum of S within
  0.001 σ (`i_lab_more.out`).
- **The tool's claim is wider than what holds.** `tools.stats` advertises «errors in x and y», and the design calls it
  the lab's general fit.

**Fix.**
- Use York's algorithm for `line`. The same weighted-mean iteration also gives the minimum of S for `line0`, and a
  Newton step on S for `quadratic`/`power`.
- Or state in `linear_fit` (and fit.js) that the effective variance is an approximation that is biased when random x
  errors are comparable to the spread of x.
- Keep fit.js in step either way. Note also that Lybanon's comment (AJP 52, 276) and Orear's erratum, cited as "not
  read", are exactly about this.

### F6 — nit — documentation numbers

- **The sign of the C_d error.** «the constant 0.47 errs by up to −18 % / +7 %» appears at `drag_quadratic.py:20` and
  `:70`, in `locales/ru.json:500`, at `README.md:100` and at `README.ru.md:102`. Those numbers are
  (curve − 0.47)/0.47. The constant's error relative to the curve (0.387–0.504) is **+21 % / −7 %**
  (`d_energy_validity.out`).
- **The buoyancy ratio.** `README.md:112` says «no buoyancy (of order ρ_air/ρ_ball: … 0.01 for the light ball)». It
  is 1.204/368 = 3.3e-3.

### F7 — nit — the stated 1e-9 "relative in the range" does not hold for steep throws

**Where.** `particle.py:46–48` and the ABOUT `validity` at `:81–82`.

**Evidence** (`b_hodograph.out`, the engine against the hodograph, 25 m/s): the range's relative error is 1.0e-9 at
88°, 1.7e-8 at 89.9° and 1.4e-7 at 89.99°. Its absolute error stays a few 1e-11 of v₀²/g.

**Fix.** S03 already compares L and H against the flight's length scale (`viz.py:180–184`, README:93–96). The engine's
own statement should say the same.

### F8 — nit — `linear_fit` does not refuse a singular design; `fit.js` does

**Evidence** (`g_fit.out`, `h_fitjs.out`):
- `linear_fit` raises `numpy.linalg.LinAlgError: Singular matrix` for all-equal x.
- For a parabola on x = 30, 30, 30, 40 it returns parameters ~1e15 and σ ~1e27 without complaint.
- `fit.js` throws `why: "singular"` in both cases.

**Fix.** Add the same |R_jj| > 1e-14·|R_00| test in `_wls`, as a translatable `ValueError`. The docstring calls the
two "the contract".

### F9 — nit — the verdict «agrees within two errors» (fit.js `agrees`, lab.js `checkLaw`)

- **(a) The normal k = 2 with σ from the scatter.** When σ comes from the scatter (unit weights, or Birge > 1 with few
  points), k = 2 of the normal distribution rejects a correct law far more often than 4.6 %. The rate is 29.5 % at
  dof 1, 18.4 % at dof 2, 13.9 % at dof 3 and 10.2 % at dof 5 (Student's t, `g_fit.out`). S03 cannot reach this, since
  every instrument declares an error above its real scatter. But fit.js is the lab's generic fit.
- **(b) No ceiling on the Birge scaling.** The PDG passage cited for the scale factor also says «If χ²/(N − 1) is very
  large, we may choose not to use the average at all». An unlimited Birge scaling turns a wrong model into a large σ
  and an «agrees». The school UI hides χ²/dof.
- **(c) The check ignores which axes are plotted.** L against h with `line0`, the grade-7 plot, gives a slope of
  0.797 ± 0.035 m/m. That is compared with k = 0.677 m^½: «✗ does not agree: measure the range from the point under
  the chute's end…» (`i_lab_more.out`). The hint blames the readings, not the axes.

**Fix.** Use a t-quantile when σ is scatter-derived. Add a χ²/dof (or p-value) ceiling with its own message. Compare
only when the plot is the step's `plot.x`/`plot.y`, or say which plot the law is for.

### F10 — nit — an unnecessary refusal in `linear_drag_landing_time`

**Where.** `drag.py:170–172`: "the body moves down faster than its terminal speed".

**Evidence** (`a_closed_forms.out`). For c ≤ 0 the argument of W₀ is ≥ 0, and the same formula is exact:
- v_y0 = −v_t: 3e-17;
- v_y0 = −1.5 v_t: 4e-16.

DOP853 agrees in both cases. The refusal also fires at c = 0 exactly, which is uniform motion at v_t.

**Fix.** Drop the refusal. The function's other conditions are enough.

### F11 — nit — the worksheet's numbers are not tested

**Where.** `viz.py:453, 461–464, 472`.

**What is in no test.** The teacher's notes state engine results as fixed text: «less than 0.1 %», «about 0.5 %
lower», «near 42°», «agrees … within one error». No test asserts them.

**What is true today** (`f_lab.out`):
- 0.080 %;
- 0.521 %;
- 41.887°;
- 0.74 σ.

The comparison with the tape in the same sentence is false (F4).

**Fix.** Assert each number in `test_s03_physics.py`, as the Watch captions already are.

---

## Checked and found fine

- **Vacuum closed forms.** T (both branches), H and r(t) are exact to ~1e-16 against mpmath. The engine is within 4e-15.
- **Linear drag.** x(t), y(t) (including the series for s < 0.1), v(t) and the apex time are exact to ~1e-16 for k from
  1e-6 to 0.3. The Lambert-W derivation and the choice of W₀ (W₋₁ is the start when h = 0) are right.
- **The hodograph.** I re-derived it: dθ/dt = −g·cos θ/v, du/dθ = k·u³/(g·cos³θ), F(p) = p√(1 + p²) + asinh p,
  dt = −u dp/g. It agrees to ≤ 4e-16 with a 30-digit Taylor-series integration in 5 cases (`b_hodograph.out`). The
  engine is within 6e-12.
- **The vertical closed forms with quadratic drag**, and `fall_time`: right.
- **The energy bookkeeping.** W = ∫F·v dt is carried and matches an independent quadrature on a Radau solution
  (8.9e-12, 1.5e-11, 1.5e-12; 8.4e-10 for the 1.2 mJ of the chute throw). E_k + E_p − W = E₀ holds with the right
  signs, and S03's Q = −W.
- **`validity()`.** The crossings found by Brent's method and the work taken from the carried state agree with an
  independent 2·10⁶-point computation to 3e-7–2e-5.
- **Sources.**
  - Hoerner (1965) p. 3-7: "a fairly constant drag coefficient (in the order of C_D = 0.47), within the R'number range
    between 10⁴ and 10⁵", and fig. 9 "ABC … R_d = 1.6·10⁵; C_D = 0.47". Both verified on the archive.org OCR.
  - Morrison's eq. (1): verified term by term on the rendered PDF. The values 0.484/0.392/0.426/0.416 are right.
  - The Clift–Grace–Weber extremes 0.387/0.504 match the reviewer's own evaluation of table 5.2.
  - Veysey & Goldenfeld eq. (39) (R = Ua/ν, so 1 + 3 Re/16): verified.
- **The air data.** The USSA-1976 constants reproduce the standard's sea-level 1.22500 kg/m³ and 1.7894e-5 Pa·s. 20 °C
  gives ρ = 1.204105 kg/m³ and μ = 1.813406e-5 Pa·s, as documented.
- **Layers.** `core.mechanics` imports only `core.data`, `codes` and `i18n`. The quadratic model is in
  `theories.models` with its conflicts. Stokes's law in the core is consistent with `LAYERS.md`, since the engine has
  no fuller law for a sphere (its LBM is 2-D). `test_layers` passes (210).
- **The lab references.**
  - v₀√(2/g) = 0.677401 m^½.
  - v₀²/g = 2.549291 m.
  - The engine's optimum 41.9° (true 41.8868°): its discretisation of 0.013° is far below σ_vertex = 0.178°.
- **The lab verdicts** (all subsets of rows, `f_lab.out`):
  - Part A: 131 054 (line0) and 130 918 (line) subsets agree.
  - Part B in vacuum: 8 178 and 8 100 agree. With air it would fail at −0.521 % (z = −26.7).
  - Part C: 163 of 163 subsets of ≥ 4 rows agree. The full table gives 42.032° ± 0.178° (z = +0.74). The parabola's
    own bias is +0.81 σ, so the README's «42.03° ± 0.18°» is confirmed.
- **The effective-variance fixed point on the lab tables** equals the minimum of S within 0.001 σ (`i_lab_more.out`).
- **`fit.js` against `linear_fit`.** On 61 random cases (all four models, with and without x or y errors, x up to 80
  for the parabola) the largest relative difference is 3.9e-11 in the parameters and 2.1e-11 in σ. The authors' JS
  tests pass. The two treat negative errors and NaN rows differently, as documented.
- **The Birge scaling.** It is as the PDG's §5.2.2 eq. (2) defines it (verified on the PDF). The authors' Monte Carlo
  coverage is reproduced: 95.03 % unscaled, 96.1 % Birge, 94.7 % with x errors.
- **S03's references and tolerances.** The vacuum, hodograph and vertical branches of `Shot.references()` are right
  for every launch the schema allows. `check_params`' refusals are consistent with `fly`'s. The length checks are
  scaled to max(h, v₀²/g).
