# Review B8 / P1: moving charges, vector slit diffraction and v02's vector mode

**Status: awaiting processing.**

Reviewer: an independent subagent (Claude). It did not write the code under review.
Delivered: 2026-11-04. Type: internal.

## Scope

* `lfphys/lfphys/core/em/charges.py` and `lfphys/tests/test_em_charges.py`.
* `lfphys/lfphys/core/em/slit.py` and `lfphys/tests/test_em_slit.py`.
* `lfphys/sources/verification_2026-11-04_p1_charges_slit.md`.
* `visualizations/v02_double_slit/`:
  * `viz.py`, `engine/experiment.py`, `web/view.js`;
  * `README.md`, `tests/test_v02_physics.py`;
  * against `visualizations/RULES.md`, `lfphys/LAYERS.md`, `lfphys/PLAN.md` P1 and STATUS V4.

## Environment

All runs used the Docker image `light-funnel-viz`, CPU only, with `LFPHYS_NO_GPU=1`.

* The engine was mounted read-only at `/lf`, and this folder at `/out`.
* Scripts ran as `python3 /out/<script>.py`, working directory `/lf/lfphys`.
* The engine's own tests pass: `out_engine_tests.txt`, 59 passed.

## Summary

There are **16 findings: 3 errors, 7 should-fix, 6 nits.**

Most physics claims reproduce:

* Liénard–Wiechert fields and Heaviside's field;
* Liénard's power against the integral of dP/dΩ;
* the synchrotron normalisation and σ:π = 7:1;
* the screen's optical theorem;
* the TM resonance numbers;
* Rayleigh's limits (derived again here);
* v02's `vector_narrow` numbers.

The Libelo–Bombardt disagreement is settled in the author's favour by an independent finite-difference solver (C13).

The errors are these:

* the retarded-time solver silently returns retarded times that do not exist beyond a horizon (C1);
* `FunctionWorldline` gives wrong derivatives at its default step for SI-scale motion (C2);
* v02's vector expectation omits the detector efficiency (C3).

## Findings

### C1 — error — `retarded_time` returns retarded times beyond the horizon of hyperbolic motion, and wrong ones just inside it

**Location.**
* `lfphys/lfphys/core/em/charges.py:326-337`: the bracketing loop, and its comment "beyond 2^50 light times rounding would fake a sign change".
* The claim "none beyond a horizon": `lfphys/README.md:92` and the module docstring.
* The test `lfphys/tests/test_em_charges.py:86-88`.

**Evidence.** `c02_retarded_time.py` / `.out` and `c05_horizon_sweep.py` / `.out`. The worldline is `hyperbolic(g = 3e15)`, so c²/g = 30 m; the field points are at t = 0.

* Beyond the horizon, no retarded time exists, yet one is returned:
  * at a depth of 1 m: for 56 of 60 points;
  * at 0.1 m: for 57 of 60;
  * at 1 mm: for 59 of 60;
  * at 10, 30 and 100 m the solver raises, as it should.
* On the axis, 1 m beyond the horizon, it returns t_ret = −5.8e7 s.
* Inside the horizon, on the axis, against the closed form, the relative error of t_ret is:
  * 1e-6 at a depth of 1e-4 m;
  * 2.8e-2 at 1e-6 m;
  * 100 % at 1e-9 m (it returns −2.7 s against the true −1497 s).

The test only checks a point 69 m beyond the horizon.

**Cause.** g(τ) = cτ − |x − r(t − τ)| is evaluated as the difference of two numbers of size cτ. These grow up to about 2⁵⁰ × the initial light time. The rounding error, ε·cτ, then exceeds the true asymptotic deficit, which is the distance beyond the horizon. The sign test then accepts noise.

**Fix.**
* Bound the rounding error of g, about 4ε(cτ + |x| + |r|), at every evaluation. Accept a sign change only when |g(hi)| exceeds that bound.
* Otherwise raise "undetermined: within <bound> of a horizon".
* For `hyperbolic`, give the worldline a closed-form retarded time. In η, the condition 2Za·cosh η − 2cta·sinh η = ρ² + Z² + a² − c²t² is elementary.
* Test points at depths of 1e-3…1 m on both sides of the horizon, against that closed form.

### C2 — error — `FunctionWorldline` with v, a = None: the default finite-difference step is 1e-3·max(1, |t|) seconds

**Location.** `charges.py:112-115` (`_step`) and `125-136`. The route is not tested anywhere.

**Evidence.** `c04_function_worldline_step.py` / `.out`. The orbit is circular, R = 1 m, β = 0.5, with a period of 42 ns. Positions only are given.

* At the default step: |v − v_true|/|v| = 1.00 and |a − a_true|/|a| = 1.00. The field error is 130 %. No warning is given; `derivative_error()` returns numbers that nobody checks.
* With h = 1e-12 s: v is good to 4e-13 and the field to 6e-9.
* `derivative_error` reports 6e6 m/s² for a at that step. The true error is about 1e8 m/s², dominated by rounding. The estimate ignores round-off.

**Fix.**
* Make `h` required when v or a is missing. Alternatively, derive it from the worldline's own time scale, for example from |r|/|v| sampled on the domain, with h ~ ε^(1/5)·T for the fourth-order rule.
* Add the rounding term ε|r|/h², and ε|r|/h for v, to `derivative_error`.
* Have `fields` refuse, or flag, a worldline whose derivative error is not small.
* Add a test against `circular` with positions only.

### C3 — error — v02 vector mode: the expected curves omit the detector efficiency, so with dark counts the run's χ² fails on a correct run

**Location.**
* `visualizations/v02_double_slit/viz.py:540-541` (`"all"`, `"kir"`) and the `vTE` / `vTM` curves.
* By contrast, the scalar curves use `ens.screen(..., eff=ex.eff)` (`viz.py:463-465`). The hits apply `eff` (`engine/experiment.py:339`).

**Evidence.** `v01_vector_narrow.py` / `.out`, part 2: `vector_narrow`, 60 000 photons.

| case | χ² p, run's curve | χ² p, eff·vector + dark |
|---|---|---|
| eff 0.2, dark 300/s | **0.0** | 0.24 |
| eff 0.2, no dark | 0.97 | 0.97 |
| eff 1.0, dark 300/s | 0.07 | 0.07 |

The orange curve drawn in the browser is visibly too high against the dark-count floor: `b01_vector_eff_dark.jpg`. The v02 tests never use eff < 1 or dark counts in vector mode.

**Fix.**
* Multiply `Jmix / unit`, `J_K / unit` and the TE/TM curves by `ex.eff` before adding `dark_per_bin`.
* Add a test with eff < 1 and dark counts in vector mode.

### C4 — should-fix — `retarded_time` raises "no convergence" far from the origin and aborts whole vectorised calls; "large t lose no digits" is misleading

**Location.**
* `charges.py:351-354`: the stopping tests `tol` and `small`.
* `charges.py:16`: the docstring "so that large t lose no digits".
* The test `test_em_charges.py:91-97`.

**Evidence.**
* `c01_charges_core.out`: uniform motion at β = 0.99, at t = 1 s, so the charge is 3e8 m from the origin. `fields()` on 200 random points within about 1 m raises `RuntimeError: retarded_time: no convergence`.
* `c03b_no_convergence_points.out`:
  * 1 of 400 such points never converges, even with 20 000 iterations, alone;
  * the others converge alone;
  * so one bad point kills the whole array.
* `c03_no_convergence.out` and `c02 A`: where it converges, the residual |cτ − R|/R grows with |r|/R, up to 3e-8 at |r| = 3e8 m.
* Digits are lost unavoidably, because t′ is quantised at ulp(t). The test at t = 1e6 s itself accepts a relative error of 8e-3, through its tolerance 1e-7·t0·c/R·1e-9.

**Fix.**
* Stop when |g| is at the level of the rounding of its terms, about 4ε(c|τ| + |x| + |r|), or when the bracket is at ulp(t). Return the root with that bound rather than raising.
* Never let one point abort a vectorised call. Return NaN with a mask, or raise listing the points.
* Reword the docstring: the delay τ is solved accurately, but the worldline is evaluated at t − τ, so positions carry |v|·ulp(t).

### C5 — should-fix — `retarded_time` refuses sampled worldlines whose retarded time lies inside the sampled domain

**Location.** `charges.py:326-329`: `bad_dom` is tested before g(hi) is evaluated, and the doubling may overshoot the domain.

**Evidence.** `c02_retarded_time.out`, part D. Uniform motion at β = 0.9 is sampled on [0, 10 ns]; the field point is behind the charge.

| field point | exact t_ret | sampled worldline | formula worldline |
|---|---|---|---|
| x = −1.5 m, t = 8 ns | 1.577 ns, inside | `ValueError: the retarded time lies before the worldline's domain` | 1.5771 ns |
| x = −2.3 m, t = 9.9 ns | 1.173 ns, inside | the same error | 1.1726 ns |

**Fix.**
* Clamp `hi` to t − t_min and evaluate g there. Raise only if g(t − t_min) < 0.
* Test with a point whose present distance / c exceeds t − t_min.

### C6 — should-fix — the modal convergence that v02 shows under-reports the error 3–6×, and the documented orders disagree with measurement

**Location.**
* `viz.py:578-581`: the check `vconv`, with its tolerance of 1 %.
* `viz.py`, `_vector_screen`: M → M + max(4, ⌈M/4⌉).
* `slit.py:680-685`: the docstring of `solve`.
* `v02_double_slit/README.md:153`.

**Evidence.** `s02_slit_convergence.out`. T(M) is computed for M = M₀, 1.25 M₀, 2, 4 and 8 M₀, with the Richardson limit.

| geometry | M₀ | observed order | true error at M₀ | shown T(1.25 M₀)/T(M₀) − 1 | true/shown |
|---|---|---|---|---|---|
| `vector_narrow`, TE | 26 | 1.32 | −4.7e-4 | +1.4e-4 | 3.3 |
| `vector_narrow`, TM | 26 | 1.38 | −9.1e-4 | +2.8e-4 | 3.2 |
| test slit 1.3λ / 0.5λ, TE | 27 | 1.03–1.23 | −3.9e-4 | +7.9e-5 | 5.0 |
| test slit 1.3λ / 0.5λ, TM | 27 | 1.24–1.34 | −1.9e-3 | +4.4e-4 | 4.3 |
| thin, k a = 100, TE (modal) | 56 | 0.83–0.97 | −2.1e-3 | +3.5e-4 | 5.8 |

So a 1 % tolerance on the shown change lets true errors of about 3–6 % pass.

The docstring of `solve` says "measured ~M^-1.4 for TE through a slit of 1.3 λ in a screen of 0.5 λ, relative change 1e-3 from 32 to 64 modes". The measurement gives TE about M^-1.1 with a change of about 2e-4. TM is about M^-1.3 with a change of 1e-3, so TE and TM are swapped in the docstring.

The README's "0.2 % in T for TM and 0.03 % for TE" is about right only for the test slit. For `vector_narrow` it is 0.09 % and 0.05 %.

**Fix.**
* Show the Richardson error estimate Δ/(1 − (M/M₂)^p), with p = 1 to stay conservative. That is about 5Δ for M₂ = 1.25 M. Alternatively, solve at 2M and extrapolate.
* Label the check as an error estimate. Set its tolerance against what the display needs.
* Correct the docstring of `solve` and the README.

### C7 — should-fix — thin screens with k a > 40 go to the waveguide modes: 0.2–0.5 % error in T, as large as the vector−scalar differences v02 displays there

**Location.**
* `slit.py:699-700`, the 'auto' switch, and `_default_modes`.
* The README table row for 8 µm: `v02_double_slit/README.md:166`.

**Evidence.**
* `s04_slit_resonance_limits.out`: T jumps at k w = 40 against the exact edge basis.
  * At k w = 39.9: the edge basis, error 4e-10.
  * At k w = 40.1: the modal method, error −4.9e-3 (TE) and −3.9e-3 (TM).
  * At k w = 60: −3.6e-3 and −3.3e-3.
* `s06_readme_table_rows.out`: the README row at a = 8 µm, k a = 79.

  | | README ('auto' = modal) | edge basis |
  |---|---|---|
  | T_TE | 0.999 | 1.0021 |
  | T_TM | 0.997 | 1.0002 |

  The README's TM "0.997" and its larger difference, 0.006 at 8 µm against 0.003 at 4 µm, are the method's error, not physics.
* `s05_edge_vs_modal_cost.out`, two slits at v02's cap, k a = 129:
  * modal: 1.7–1.9 s per solve, error −2.3e-3;
  * edge basis: 6.4–10.7 s, converged to 1e-7.

**Fix.** Use the edge basis for t = 0 up to v02's cap. For the edge basis the second, convergence solve can be dropped or made cheap, because it converges exponentially. Alternatively, cap thin-screen vector mode at k a ≤ 40 and state why. Correct the README's 8 µm row.

### C8 — should-fix — when the hits stay scalar, the "vector" curve and the "vector − scalar" difference are dominated by normalisation, not physics

**Location.**
* `viz.py:546-551`: `curves["vec"]` per particle on the open width, without eff and without the elements' or the analyser's transmission.
* `web/view.js`: `othC` and `diffC` are scaled with the hits' factor.

**Evidence.** `v01_vector_narrow.out`, part 3:

| world | Σ scalar `all` | Σ vector `vec` | difference max / max(all) |
|---|---|---|---|
| eraser + conductor | 0.24 | 0.95 | — |
| zero-phase element (no physical change), eff 0.5 | 0.48 | 0.95 | 0.96 |

In the eraser screenshot `b01_eraser_pec.jpg`, the blue curve is about 3× the histogram. The red strip reads ±912 counts.

The README says only "per particle falling on the open width n·a" (without the elements). The efficiency mismatch and the effect on the difference strip are not stated.

**Fix.** Pick one:
* normalise `vec` to the same total as `all` and label it a shape comparison; or
* apply eff and the elements' and analyser's mean transmission so that the units match.

Either way, compute `diff` only when the units agree, and otherwise drop the red strip.

### C9 — should-fix — v02 re-solves the conductor on every change of the source or the detector

**Location.** `viz.py:324`: a `_build` for any `SOURCE_FIELDS` or `DETECTOR_FIELDS` change, which calls `_vector_screen` at `viz.py:284-285`.

**Evidence.** `v01_vector_narrow.out`, part 4. The world is vector, k a = 129. Each of these live changes blocks the world for the time shown:

| live change | blocking time |
|---|---|
| eff | 16.2 s |
| dark_rate | 16.9 s |
| pol_state | 14.8 s |

The TE and TM solutions depend on none of them. The first build took 14.4 s (the README says "~10 s").

**Fix.** Cache `exp.vec` keyed by (λ, slits, a, t, L2, screen grid). Rebuild it only on `SETUP_REBUILD` fields. The polarisation weights are applied per segment anyway.

### C10 — should-fix — layering: the Kirchhoff approximation is re-implemented inside the core module `core.em.slit`

**Location.**
* `slit.py:766-868`: `kirchhoff_spectrum`, `kirchhoff_far_field`, `kirchhoff_transmission`, `kirchhoff_field`, `compare_kirchhoff`, and the Kirchhoff column of `transmission_vs_width`.
* `lfphys/lfphys/theories/approx/kirchhoff.py:34-36`.

**Evidence.**
* `lfphys/LAYERS.md` §1 puts "a simplified form of a law the engine also has in fuller form, kept for comparison" in `theories/approx`. `theories.approx.kirchhoff` already exists there. `test_kirchhoff_routes_agree` shows the two copies agree to 1e-12.
* The approx module's passport still says "(нужна векторная теория)", and its `conflicts` do not name `core.em.slit`. The player shows this stale line in every vector-mode world: `b01_browser_view.json`, "Где верно: щели шире ~10 λ … (нужна векторная теория)".

**Fix.**
* Move the Kirchhoff functions to `theories.approx.kirchhoff`, which may import the core. Let v02 and `compare_kirchhoff` use them from there.
* Update the approx passport: its validity and a conflict naming `core.em.slit`.

### C11 — nit — double precision loses about γ²ε in the fields and in Liénard's power; the validity does not say so

**Location.**
* `charges.py:389-390` (`kap`, `g2`), `446-449` (`lienard_power`) and `heaviside_field`.
* ABOUT's `validity` (line 69).

**Evidence.** `c01_charges_core.out`. Uniform motion is compared with a 50-digit mpmath Heaviside field.

| γ | Liénard–Wiechert error | `heaviside_field` error |
|---|---|---|
| 1e2 | 3e-12 | 6e-15 |
| 1e4 | 4e-8 | 5e-9 |
| 1e6 | 1e-4 | 9e-5 |
| 1e7 | 8e-2 | 5e-3 |

The synchrotron spectrum against `lienard_power` is good to −5e-10 at γ = 2000 but only +1e-7 at γ = 1e4. The difference is the cancellation in `lienard_power`, 1 − β·β.

This is inherent to passing β as a float. The engine's own test, up to β = 0.9999, compares two formulas that share the cancellation.

**Fix.**
* State "relative error about 1e-16·γ²" in `validity`.
* Optionally, let worldlines provide 1/γ², and compute `lienard_power` for perpendicular motion as γ⁴|β̇|² directly.

### C12 — nit — layering of the synchrotron F/G spectrum

**Location.** `charges.py:37-43`, `514-553`, and ABOUT, where `"conflicts": []`.

**Evidence.** The F/G spectrum and the angular-spectral form are the γ ≫ 1 limit of Schott's exact harmonics. Those harmonics are in the same core module. LAYERS §1 puts such simplified forms in `theories/approx`, or at least requires the relation to be named.

The `critical_frequency` docstring says ω_c "divides the radiated power into halves". The fraction below it is 0.5000052565: `c01`, which agrees with mpmath and with the sources file.

**Fix.**
* Move the F-based functions to `theories.approx.synchrotron`, or name the relation in `conflicts` / `validity`.
* Say "nominally (0.5000053)" in the docstring.

### C13 — nit — Libelo–Bombardt: the author is right, and an independent route now shows it; tighten the record

**Evidence.** `s03_fdfd_thin_slit.py` / `.out`. This is an independent FDFD solver written for this review. It does not use the engine:

* the 5-point Helmholtz equation with a stretched-coordinate PML;
* the zero-thickness screen between two grid rows;
* exact discrete flux;
* four grids, N = 8…64, with an observed order of 0.95–1.04, extrapolated.

| polarisation | η | FDFD | engine | engine − FDFD | Libelo–Bombardt table | table − FDFD |
|---|---|---|---|---|---|---|
| TE | 0.8 | 0.2608 | 0.2606 | −0.09 % | 0.2923 | **+12.1 %** |
| TE | 1.0 | 0.5457 | 0.5454 | −0.06 % | 0.6012 | **+10.2 %** |
| TE | 1.5 | 1.1824 | 1.1827 | +0.03 % | 1.2307 | +4.1 % |
| TE | 2.0 | 1.1841 | 1.1843 | +0.02 % | 1.2061 | +1.9 % |
| TM | 0.8 | 1.0143 | 1.0143 | 0.00 % | — | — |
| TM | 1.5 | 0.9826 | 0.9826 | 0.00 % | — | — |

The TM rows are the first independent check of the thin-screen TM case. So the claim "the table lies 10–12 % high at small η" is **justified**.

Three points of the record need tightening.

(a) **The quotation is elided.** The sources file (line 163) quotes L&B's "accuracy … about 3%". L&B's text (NOLTR 70-58, p. 29, rendered page) reads:

> However, the higher order approximation indicates about 3% difference from the other results and this is not terribly significant

That is a difference from Skavlem and Seshadri near the first resonance, not a stated accuracy. Quote it exactly.

(b) **L&B's printed long-wave formulas are half the true limit.**
* Their (130) prints T(η) = ¼ η Σ|a_n|². The table uses ½: 0.5 × 0.8 × 0.7307 = 0.2923.
* Consistently with the ¼, their (131)–(133) give σ_t ≈ ρ₀π²η³/32, that is T → π²(kw)³/512. This is half the correct limit π²(kw)³/256, which the engine uses.
* I derived that limit independently: the static aperture field −ik√(b² − x²) gives P = π²k³b⁴/16. I also derived the TM limit, which agrees with the engine and with Harrington & Auckland's (8-7) at d = 0.

This supports the engine and could go in the sources file.

(c) **The test is fragile.** `test_thin_te_slit_against_libelo_bombardt_table` (`test_em_slit.py:251-257`) passes at η = 1.5 with a margin of 0.1 %, against a reference that is itself 4.1 % high.

**Fix.** Pin the FDFD numbers above, or the hat route, as the reference values with a derived tolerance. Keep L&B as documentation of a known-high table.

### C14 — nit — the peak height λ/(πw) is attributed to Takakura

**Location.** `test_em_slit.py:191-192`: "peaks of T = lambda/(pi w) (Harrington & Auckland 1980; Takakura 2001; …)".

**Evidence.** Takakura's abstract (OpenAlex, fetched) says:

> The resonance peaks, however, have very low magnitude and a systematic shift towards longer wavelengths is observed.

His normalisation evidently differs, and the paper itself was not fetched.

**Fix.** Attribute the peak height to Harrington & Auckland:

> These peaks approach a value of 1/wπ for small w

That is RADC-TR-79-257, p. 116; the OCR reads "l/w7r", checked on the rendered page. Also attribute it to Holley & Schnitzer, where η ≈ h⁻¹Ω̄|A|² at resonance gives 1/(πmh). Keep Takakura only for the shift, via Holley & Schnitzer's eq. (35).

### C15 — nit — v02 UI and documentation details of the vector mode

* **The refusal of the default geometry is acceptable, but the limit is not announced in advance.**
  * The default slit is 20 µm, k a = 199. The scalar and vector results differ there by well under 1 %, and the cost is high.
  * The refusal text is explicit, and the control rolls back: `v01 part 4`, `b01_browser_view.json`.
  * However, neither the select's help (`viz.py:96-102`) nor the scalar panel's text in `view.js` (`drawVector`) mentions the width limit.
  * The message says "шире 21 λ" (`viz.py:1148`, 130/2π = 20.7), while the README says "up to 20 λ".
* **For n = 1 the strip W = n·d uses the otherwise unused period d.** So `p_trans` and the "reflected" count depend on a parameter without meaning; README "Hits".
* **"χ² p = 0.52 for 30 000 emitted photons" (README:171) is a single seed.** Five seeds give vector p = 0.43, 0.91, 0.73, 0.48, 0.09 and Kirchhoff p from 1e-12 to 1e-6.
* **The first build at k a = 129 takes 14.4 s, not "~10 s".**

**Fix.**
* Add "щели до ~20 λ" to the select's help and to the scalar panel. Use one number.
* State the n = 1 convention.
* Give the seed spread.

### C16 — nit — the source record and test naming

* **The Fitzpatrick quotation** in the sources file (line 41) has "dt′". The text layer reads:

  > This quantity is actually the amount of energy lost by the charge in a retarded time interval dt during the emission of the signal

  The prime is lost in extraction. This is fine, but say the quote was checked on the rendered page.
* **`test_large_times_lose_no_digits_and_domain_is_respected`.** The name contradicts its own tolerance (C4). Rename it, or assert the |v|·ulp(t) bound.
* **The Qi et al. comparison** (`test_em_slit.py:206-209`) cannot resolve their constant 0.0096 at a tolerance of 5e-3. It re-tests only the slope 1/π, so it adds nothing beyond Harrington & Auckland and Holley & Schnitzer. Say so, or drop it.

## Reproduced claims (status per item)

| claim | result | evidence | status |
|---|---|---|---|
| Heaviside's field = Liénard–Wiechert at β = 0.99 | 1e-13 in E and in c·B, two directions, t = 0 and 3 ns | `c01` | [useful] |
| ∮dP/dΩ (retarded) = Liénard | adaptive quadrature about β: ≤ 3e-13 for β = 0.9, 0.99, 0.999, collinear, circular and general | `c01` | [useful] |
| observer-time pattern | ∮ observer / ∮ retarded = the closed form ∫(1−μ²)(1−βμ)⁻⁶ / ∫(1−μ²)(1−βμ)⁻⁵ to 12 digits; 60.1015 at β = 0.99 | `c01` | [useful] |
| synchrotron spectrum | ∫ = Liénard to −5e-10 (γ = 2000); σ/π = 7.0000000000; fraction below ω_c 0.5000052565, which equals mpmath | `c01` | [useful] |
| retarded time near light speed | circular orbit, γ = 1e2…1e4: residual ≤ 4e-16; t_ret phase against 50-digit mpmath ≤ 9e-12 rad | `c02 B` | [useful] |
| retarded time beyond a horizon | fake roots | C1 | [error in earlier] |
| `FunctionWorldline` with finite differences | wrong at the default step | C2 | [error in earlier] |
| screen optical theorem and P_t | two slits (0.8, 0.5 λ), t = 0.4 λ, θ = 0.3, default modes. TE: P_t = 0.8906441164, extinction balance −1.1e-11. TM: P_t = 1.186848005, 7e-16. The **field's** flux through upper and lower half circles (r₀ = 1.5, 4 λ) equals P_t to 3e-11 / 1e-13 | `s01` | [useful] |
| the theorem as stated | derived here from the flux through z = z₁ < 0: P_t + P_b = −4π r_s cos θ Re R(q₀), with u_s = ∫R e^{i(qx − k_z z)} dq | REVIEW | [useful] |
| TE Galerkin form (two integrations by parts, Maue) | checked analytically. φ vanishes at the walls, so the boundary terms drop | — | [neutral] |
| thin-slit TE and TM against an independent FDFD | ≤ 0.1 % (TE), 0.00 % (TM) | `s03` | [useful] |
| Rayleigh's limits (π²/256)(kw)³ and π²/(4kb[(γ + ln kb/4)² + π²/4]) | re-derived; engine/Rayleigh − 1 = 3e-4 (TE) and 3e-5 (TM) at kw = 0.02; 3.8 % (TE) at v02's threshold k a = 0.3, against its tolerance of 5 % | `s04` | [useful] |
| TM resonance at w = 0.02 λ | peak 15.928 = λ/(πw)(1 + 8e-4), stable from M = 8 to 64; resonant thickness 0.4538 against H–S (34) 0.4503 and Takakura (35) 0.4415 | `s04` | [useful] |
| TM resonance at w = 0.05 λ | 6.398 (+5e-3); the shift is 12 % below H–S | `s04` | [neutral] |
| Harrington & Auckland circuit | within 1.0 % off resonance, 1.8 % at d = 0.45 | `s04` | [neutral] |
| Qi et al. | within 1.4e-4 at s = 55 and 100 | `s04` | [neutral] |
| `vector_narrow` | T_TE = 1.05602, T_TM = 0.97332, T_K = 0.80546, as the README says | `v01` | [useful] |
| `vector_narrow` checks | balance ≤ 2e-16; mode power ≤ 4e-16; the shown conv understates (C6) | `v01` | [useful] |
| `vector_narrow` transmitted fraction | equals P_t/W within 2.5σ over 5 seeds | `v01` | [useful] |
| `vector_narrow` χ² | vector p 0.09–0.91; Kirchhoff rejected at p ≤ 1e-6 with 30 000 photons | `v01` | [useful] |
| scalar default unchanged | v02 at HEAD against the current v02, six presets with a live change: detections, curves and checks bit-identical | `v02_scalar_unchanged_*.out` | [useful] |
| hits labelled scalar | with marks, elements, analyser or modified laws: in the segment's approximations, the overlay and the panel; the near-field map and flow lines are labelled scalar | `b01_*`, `v01` | [useful] |

## Answers to the focus questions (short)

**Retarded time.**
* It is unique for subluminal motion, and robust near light speed.
* It is **not** reliable near a horizon (C1) or far from the origin (C4).
* It falsely refuses sampled worldlines (C5).

**The field split and the time convention.** E_vel, E_acc and B = n×E/c are correct. The parts were checked term by term against Fitzpatrick (12.293)–(12.297), the fetched source; Jackson was not fetched. The κ⁵ (retarded) and κ⁶ (observer) patterns are correct and tested both ways.

**Synchrotron.** The normalisation (PDG's F has unit integral; the engine's S = (9√3/8π)F) is right. The σ/π split (F ± G) and the 7:1 ratio are right.

**The modal method.**
* The TE and TM Galerkin forms and the decoupled A ± B systems are consistent: the energy holds independently on finite contours (`s01`).
* The edge singularity of thin screens is built into the Chebyshev basis, and that basis converges exponentially.
* The corners of thick screens are not built in. Convergence is algebraic, order 1.0–1.4. The defaults are adequate at about 0.05–0.2 %, but the run understates the error (C6).
* Thin screens beyond k a = 40 should not use the modal method (C7).

**The optical theorem** is stated correctly.

**v02.**
* The hit sampling from the flux is correct: TM/TE weights |χ_H|²/|χ_V|², no cross term, P_t/W, the reflected photons. The exception is the efficiency in the expectation (C3).
* The scalar fallbacks are clearly labelled.
* The comparison curve in the fallback is misleading (C8).
* The scalar default is unchanged.
* The refusal of the default geometry is acceptable but should be announced in the UI (C15).

## Sources

All fetched sources are in the session scratchpad (`…/scratchpad/b8/rev_charges_src/`), not here. Requests carried a generic user-agent and no contact parameter.

**Verified by grep of the text layer or on a rendered page:**

* Fitzpatrick's notes: (12.293)–(12.299), (12.309), (12.327), (12.337)–(12.338). Quoted:

  > represents the energy flux per unit actual time, t

* X-ray Data Booklet §2.1:

  > ωc = critical frequency, defined as the frequency that divides the emitted power into equal halves

  > The first and second terms in the last bracket of Eq. (1) correspond, respectively, to the intensity of the horizontally and vertically polarized radiation.

* PDG 2024, "Electromagnetic relations": (7.12)–(7.14), and

  > Note that earlier editions of Ref. [2] had ωc twice as large as Eq. (7.13).

* Holley & Schnitzer, arXiv:1812.06753v2: (32)–(35), and

  > Takakura’s approximation is seen to be in poor agreement with the numerical data

* Qi et al. 2010, author copy: eq. (22), "T0(s) = 0.0096 + 0.3183 × s". This was read on rendered page 3661. Note their T is defined through the exit field, eq. (19).
* Auckland & Harrington, RADC-TR-79-257 (DTIC ADA078477, archive.org):
  * (8-4), (8-7) and (8-8), on the rendered page 115;
  * "These peaks approach a value of 1/wπ for small w", p. 116.
* Libelo & Bombardt, NOLTR 70-58 (UNM Interaction Note 106):
  * Table I, every digit used, on the rendered page 35;
  * their (130)–(133), p. 29;
  * the sentence quoted in C13(a).
* OpenAlex abstracts:
  * Takakura, PRL 86, 5601, quoted in C14;
  * Harrington & Auckland 1980, doi:10.1109/TAP.1980.1142382:

    > the transmission width at resonance becomes 1/\pi wavelengths regardless of the actual slot width

* Crossref confirms that doi:10.1109/TAP.1980.1142397 is a different paper (Ghobrial, "Axial cross polarization in reflector antennas…").

**Not fetched or not re-verified:**

* R. P. Walker, CAS CERN 94-01: CDS served an HTML page, not the PDF. The booklet and the PDG replace it.
* Jackson.
* Schott 1912 and Rayleigh 1897 were not re-read from the scans. Instead:
  * Rayleigh's two limits were derived here;
  * Schott's SI forms were checked against the formulas the sources file quotes;
  * Schott is also checked by the engine's independent FFT test.
* Sommerfeld 1896: not fetched. Its implementation is covered by the tests: Helmholtz, the boundary conditions, Keller's edge wave and |u| = ½ on the shadow boundary.
* Takakura's full text.
* Born & Wolf.

## Files in this folder

| file | what |
|---|---|
| `out_engine_tests.txt` | the engine's tests for both modules (59 passed) |
| `c01_charges_core.py` / `.out` | Heaviside, Liénard against ∮, high-γ precision, synchrotron |
| `c02_retarded_time.py` / `.out` | retarded time: far from the origin, near light speed, the horizon, sampled domains |
| `c03_no_convergence.py`, `c03b_no_convergence_points.py` / `.out` | the non-converging point (C4) |
| `c04_function_worldline_step.py` / `.out` | the finite-difference default step (C2) |
| `c05_horizon_sweep.py` / `.out` | fake-root rate beyond the horizon (C1) |
| `s01_slit_balance.py` / `.out` | the optical theorem and independent contour fluxes |
| `s02_slit_convergence.py` / `.out` | convergence in M (stopped by the reviewer at 11 min, at the k a = 100 TM part; the lines shown are complete) |
| `s03_fdfd_thin_slit.py` / `.out` | the independent FDFD solver (C13) |
| `s04_slit_resonance_limits.py` / `.out` | TM resonance, H&A, Qi, Rayleigh at k a ≤ 0.3, the auto switch at k w = 40 |
| `s05_edge_vs_modal_cost.py` / `.out`, `s06_readme_table_rows.py` / `.out` | C7 |
| `v01_vector_narrow.py` / `.out` | v02 through the harness: the preset, eff/dark, the scalar fallback, refusals and costs |
| `v02_scalar_unchanged.py`, `v02_scalar_unchanged_new.out` / `_old.out` | v02 at HEAD against current, bit for bit |
| `b01_browser_view.mjs` / `.json`, `b01_*.jpg` | private server (port 8533) and Playwright: panel texts and screenshots |

**To re-run the old-v02 comparison:**

```
git show HEAD:engine/visualizations/v02_double_slit/{viz.py,engine/experiment.py,web/view.js,README.md}
```

Put those files into a copy of `visualizations/`, mount it at `/old`, and run `python3 /out/v02_scalar_unchanged.py old`.
