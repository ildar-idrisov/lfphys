# Review B8-mie: the exact Mie series (P1) and v17_mie_scattering (P14.8)

**Status: awaiting processing.** This is an internal review by an independent subagent (Claude Opus), delivered on
2026-11-04. The reviewer did not write the code under review. Under `reviews/README.md` the reviewer does not
process this review: there is no RESPONSE.md, no archiving and no edits outside this folder.

## Scope

**Engine code:**
- `lfphys/lfphys/core/optics/mie.py`, `mie_debye.py` and `mie_poly.py`;
- `lfphys/lfphys/theories/approx/rainbow.py`;
- the water and Sun block of `lfphys/lfphys/core/data.py`.

**Engine tests:**
- `lfphys/tests/test_mie.py`, `test_mie_debye.py` and `test_mie_water.py`;
- `lfphys/tests/external/test_ext_mie_miepython.py`, with its rows in `make_results.py` and `RESULTS.md`.

**Sources:** `lfphys/sources/verification_2026-11-04_p1_mie.md`.

**The visualization:** `visualizations/v17_mie_scattering/` (`viz.py`, `engine/drops.py`, `web/view.js`, `README.md`,
`tests/`), read against `visualizations/RULES.md`.

**Not reviewed:** the FDTD, the beams, the charges, the slit, v02 and v16 (other agents' work).

## Environment

All runs were made in Docker from `engine/`, mounted read-only, on the CPU:

```
docker run --rm --name lf-b8rm-<x> -v .../engine:/lf:ro -v <this folder>:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/<script>
```

- **Images:** `light-funnel-viz` (numpy 2.4.6, scipy 1.17.1, mpmath 1.3.0) and `light-funnel-ext` (miepython 3.3.0)
  for `s09` and `g1`.
- **Visualization runs:** through `visualizations/tests/harness.py`, without the server.
- **Not done:** no browser check was run.
- **Containers:** every container was named `lf-b8rm-*` and was checked to have stopped (`docker ps -a` shows none).
- **Engine tests:** the three engine test files pass (103 tests, `out_engine_tests.txt`).

Each script `sNN_*.py` has its output in `sNN_*.out`, and each finding below names the scripts it rests on. Status tags
follow `AGENTS.md` §3 rule 11: [useful] / [neutral] / [weakens] / [error in earlier].

## Summary of findings

| id | severity | one line |
|---|---|---|
| M1 | error | The bound "every a_n, b_n within 2e-11 of the largest, x ≤ 2e4" fails on narrow resonances: up to 6.4e-3 at x ≈ 1000. The engine is backward stable, so the forward error is ε·x/Γ. |
| M2 | error | v17's `energy` check fails on a correct engine for most transparent drops with 37 ≲ x ≲ 112 (r ≈ 3–10 µm at 550 nm). The cause is numpy's Gauss–Legendre weights near μ = ±1, which is also the "cause not found" of the README. |
| M3 | should-fix | v17's `theorem`, `energy` and `mueller` checks (and the test docstrings behind them) are identities of the formula's structure. They stay at round-off when D_n, ψ_n or χ_n are wrong by 1e-3. Only `debye` detects such errors. |
| M4 | should-fix | v17's `debye` tolerance of 5e-10 is not derived: it fails on a correct engine for m = 0.75 (e.g. an air bubble in water) at the largest x v17 admits. mie_debye's ABOUT understates the sum's error. |
| M5 | should-fix | Debye terms for m near 1 with slight absorption: \|R11\| reaches 4.8 (the series diverges) and the terms p ≤ 3 reach 1.6e6× the largest Mie coefficient. Partial sums plus the remainder miss a_n by 5e-4. v17 draws these terms as "light of one path" without a notice. |
| M6 | should-fix | Vacuum as the medium is not listed among v17's approximations. In air the bows move by −0.054° (p = 2) and +0.096° (p = 3), more than the 0.05° and three-decimal figures quoted. |
| M7 | should-fix | Size averages: `err` is not a per-angle estimate (exceeded at 35–51 % of angles), and the ±3σ cut (up to 0.46 % of the peak) is not stated. The ripple is not "period ~1.5": it is 1.25–1.28 at 140°, and 0.27 at 180°. The README's supernumerary `sky_sum` 0.11 reproduces as 0.31. |
| M8 | nit | miepython xfails: library-side is right, but the stated cause "top orders lose accuracy" is wrong (the error is ~1.1e-9 at every order at x = 1e4). The docstring states the engine's budget as 1e-12 for x ≤ 1000, while the code uses 2e-11. |
| M9 | nit | The 40-digit references start D = 0 only 50–60 orders above \|mx\|, so they are not exact for real \|mx\| ≫ N (3.6e-5 off at m = 1e5, x = 0.5). This is harmless for the present cases. |
| M10 | nit | The Hankel-sum start (\|mx\| > N²) is tested only through the conductor limit at 1e-5 (it is accurate to 2e-16), and `log_psi` has no direct test. |
| M11 | nit | v17 texts: fixed "≈ 138°, ≈ 129°", "their sum gives the white curve" with only p ≤ 3 drawn, rays of m = 1.333 drawn for m ≤ 1, and info tolerances in degrees compared with a relative `rel`. |
| M12 | nit | Physics in the visualization: the azimuthal intensity \|S2\|²cos²φ + \|S1\|²sin²φ (`drops.polar_mesh`), plus P and the phase-function normalisation recomputed in `viz.py`. |
| M13 | nit | Small doc slips: `water_index` calls 100–110 °C at 0.1 MPa "stable" (it is metastable), and the `internal_coefficients` docstring promises a third return value. |
| M14 | nit | "One place for problems": STATUS has no B8 entry for the README's "STATUS" pointer. The "coarse" size sampling (dx up to 14.9 in x) is only a text line, not a header approximation. |

There are 2 errors, 5 should-fix findings and 7 nits. A list of what was verified and holds is at the end; it is
substantial.

---

## M1 — error — the stated coefficient bound fails on narrow resonances [error in earlier]

**Where.**
- `lfphys/lfphys/core/optics/mie.py:53-55` (ABOUT validity: «погрешность коэффициентов ≤ 2·10⁻¹¹ наибольшего (тесты по
  всем порядкам; вдали от узких резонансов ~3·10⁻¹³)»).
- `mie.py:62-73` (`ACCURACY`, `coefficient_bound`).
- `lfphys/README.md:75` ("tested bound 2e-11 of the largest coefficient … from x = 1e-6 to 2e4").
- `tests/test_mie.py:151-161`. This test checks the bound only at six fixed (m, x).
- The bound is also used as the engine's error budget in `tests/external/test_ext_mie_miepython.py:178`.

**Evidence: `s05_bound_resonances.py`, `s05b_resonance_conditioning.py`.**

For m = 1.333, the scripts locate the 17 TE resonances with x in [1000, 1001] and orders n in (x, N]. A resonance is a
zero of the real part B_n of the denominator. At each resonance peak, the engine is compared with a 40-digit evaluation
of the same series at the same binary64 x. The results, from `s05b_resonance_conditioning.out`:

```
 n     Gamma(x)   err_engine  |b(x+ulp)-b(x)| exact   eps*x/Gamma
 1023  6.30e-04   1.77e-10    3.61e-10             3.52e-10
 1028  8.80e-05   3.84e-10    2.58e-09             2.52e-09
 1037  1.02e-06   6.26e-08    2.24e-07             2.19e-07
 1046  5.72e-09   9.14e-06    3.98e-05             3.88e-05
 1056  1.47e-11   6.35e-03    1.54e-02             1.51e-02
```

The engine's error always stays below the change of the exact b_n when x moves by one ulp. So the engine is backward
stable, as one would hope, and its forward error is the conditioning of the problem, ε·x/Γ. No fixed forward bound
like 2e-11 can hold near resonances whose width in x is below ~1e-4.

The documentation saw this ("ill-conditioned … reach 2.8e-12"), but it measured the error only at x = 1000 exactly,
which is not on a peak. Away from resonances the bound holds with a wide margin, including the cases s05(b) adds:

| m | x | error (of the largest coefficient) |
|---|---|---|
| 10 + 10i | 1000 | 1.2e-14 |
| 1.5 + 1i | 3000 | 9.9e-15 |
| 4 + 0.01i | 1000 | 1.1e-14 |
| 1.5 + 1e-4i | 3000 | 3.7e-13 |
| 0.5 | 3000 | 1.1e-14 |
| 1.05 | 3000 | 2.4e-13 |

**Suggested fix.**
- State the accuracy in two parts:
  - (a) a backward error: "the computed coefficients are the exact ones of an x perturbed by ≲ 1 ulp", measured as in
    s05b;
  - (b) a forward bound that holds away from resonances narrower than a stated Γ.
- Add a test that sits on resonance peaks: the s05b construction is cheap.
- In the external comparison, either keep the cases off resonances (as now) or use (a).
- A remark for v17: water without absorption keeps resonances as narrow as 1e-11 in x. Real water's κ ~ 1e-9 in the
  visible broadens them by orders of magnitude, so such resonances are an artefact of the stated approximation "water
  without absorption" (M6 lists the approximations).

## M2 — error — v17's `energy` check fails on a correct engine for typical cloud and fog drops [error in earlier]

**Where.**
- `visualizations/v17_mie_scattering/viz.py:248-256`: Gauss–Legendre with `np.polynomial.legendre.leggauss(2N + 20)`,
  tolerance `200 N ε + 1e-12`, used when N ≤ 150.
- README row `energy` (`README.md:54`), which says the deviation's "cause not found".

**Evidence: `s12_v17_energy_check.py`, `s12b_energy_scan_small.py`, `s08_quadrature_forward_peak.py`,
`s08b_weights.py`.**

1. Water at 10 °C and 550 nm fails the check at 74 of 105 sizes with x in [60, 112] and at 33 of 233 with x in
   [2, 60]. The smallest failing x is 36.75. The worst case is rel/tol = 6.8 at x = 107.5. Through the harness, a
   world with radius 5.3396 µm and width 0 shows `energy` value 2.1647159589841585 against the reference
   2.164715958966448: rel 8.18e-12, tol 5.13e-12, so the check FAILS. The presets pass only by luck (glory x = 91.4,
   near x = 11.4).

2. The cause is numpy's weights near μ = ±1. The nodes are exact to ≤ 1 ulp.

   | x | numpy leggauss | weights refined to 40 digits (amplitudes unchanged) |
   |---|---|---|
   | 100 | 1.27e-11 | 3.6e-14 |
   | 500 | 2.03e-9 | 2.2e-12 |

   The relative errors of numpy's weights at the five nodes nearest μ = 1, for 1120 nodes, are 2.1e-10 … 6.4e-9.
   SciPy's `roots_legendre(1120)` is no better: 2.3e-10 … 7.7e-9 (`s08b_weights.out`).

   numpy's own docstring (numpy 2.4.6, grepped in the image) says: "The results have only been tested up to degree
   100, higher degrees may be problematic."

   The forward peak (|S|² ~ x⁴ over δμ ~ 1/x²) puts most of the integral on exactly these weights. This explains the
   README's "2e-9 at x = 500 and 2e-8 at x = 1700 … cause not found".

**Suggested fix.**
- Compute the weights as w = 2/((1 − μ²) P_n′(μ)²), with P_n′ from the three-term recurrence at each node. This is
  accurate to ~nε in double; s08 got 3.6e-14 at x = 100 with 40-digit weights.
- Alternatively, derive the tolerance from the measured weight error.
- `tests/test_mie.py::_angular_integrals` has the same blind spot. Its running bound adds only 2·n_gl·ε for the
  weights and passes only because its cases stop at x = 60.
- Close the README's "cause not found" (see also M14).

## M3 — should-fix — three of v17's "physics" checks cannot detect wrong coefficients [weakens]

**Where.**
- `viz.py:245-247` (`theorem`, «Оптическая теорема»).
- `viz.py:248-265` (`energy`, note «тождество верно только для точных коэффициентов (Re aₙ = |aₙ|²)»).
- `viz.py:274-277` (`mueller`).
- The same claims appear in `tests/test_mie.py:268-275` (`test_optical_theorem`, "(B&H Eq. 4.76)") and
  `test_mie.py:301-317` ("energy conservation, a property of exact coefficients").

**Evidence: `s10_check_blindness.py`.** A deliberately wrong engine was made by monkeypatching one ingredient, for
m = 1.3354 and x = 300:

```
D     : coefficients off by 5.8e-02; theorem 4.5e-16; energy 3.3e-16; debye 6.3e-02
PSI   : coefficients off by 4.3e-04; theorem 2.2e-16; energy 4.4e-16; debye 1.1e-03
CHI   : coefficients off by 5.0e-04; theorem 4.3e-16; energy 4.4e-16; debye 5.0e-04
D(mx) : coefficients off by 2.3e-03; theorem 8.7e-16; energy 3.3e-16; debye 5.7e-04
```

The reasons:
- `theorem`: (4/x²) Re S(0) equals (2/x²) Σ(2n+1) Re(a_n + b_n) identically, because π_n(1) = τ_n(1) = n(n+1)/2. The
  check tests the angular-function code at θ = 0.
- `energy`: for real m, every coefficient of the form A/(A − iB) with real A and B has Re a = |a|². That holds whatever
  D_n, ψ_n, χ_n are, so it is a property of the formula's structure, not of exactness.
- `mueller`: S11² = S12² + S33² + S34² holds for any complex S1, S2.
- `debye` is a genuine second route and catches every perturbation above. Its independence comes from the ξ^(1) ratio
  recurrence and from the Wronskian built into T21T12.

A physical optical theorem is tested in `s02_flux_optical_theorem.py`, through the power through a sphere of radius 2a
computed from `mie.near_field(parts=True)`:

| case | Q_ext: flux against the series |
|---|---|
| 7 cases (dielectric, absorbing, m < 1, conductor) | 2e-14 … 5e-14 |
| scattered H with a sign flipped (negative control) | 44 % |

Note that this route is also blind to the coefficients' values: it tests the fields and Z·H. It is still a much better
"optical theorem" than the present identity.

**Suggested fix.**
- Relabel `theorem` and `mueller` as consistency checks of the angular sums.
- Relabel `energy` honestly: the quadrature version tests the angular functions and the quadrature, and
  Re a = |a|² tests that the arithmetic stayed real.
- Present `debye` (and the Wiscombe self-test, if added as for `water`) as the check of the coefficients.
- Correct the two test docstrings.
- Optionally add the flux check for small drops (cheap at x ≤ 45, where the near field is already computed).

## M4 — should-fix — v17's `debye` tolerance fails on a correct engine for m < 1 at large x [weakens]

**Where.** `viz.py:266-273` (tol `5e-10`, note «допуск — проверенный тестами движка (до 10⁻¹⁰ при x = 10⁴)»);
`mie_debye.py:46-47` (ABOUT: «совпадает с рядом Ми в пределах ~1e-12»).

**Evidence: `s03c_debye_v17_limits.py`.** The closed-form sum against `mie.coefficients`:

| m | x | error | v17 check |
|---|---|---|---|
| 0.75 | 16535 | 8.65e-10 | FAIL |
| 0.75 | 19000 | 1.01e-9 | FAIL |
| 1.3354 | 19900 | 1.4e-10 | pass |

v17 admits x up to 2e4 at 380 nm. An example: custom n = 1.0 in a medium of 1.333 (an air bubble in water, m = 0.75),
radius 1000 µm, width 0, display wavelength 380 nm, which gives x = 16535. The engine's own test allows 1e-9 at x = 1e4
for m = 0.75 (`test_mie_debye.py:27`).

**Suggested fix.**
- Take the tolerance from the measured growth, proportional to N with a stated constant: the largest ratio measured
  here is 5.3e-14·N (m = 0.75 at x = 1.9e4), so e.g. 1e-13·N covers every case.
- Update mie_debye's ABOUT: 1e-12 at x ≤ 1000, 1e-10 … 1e-9 at 1e4 … 2e4, larger for m < 1.
- Note that `s03_debye.out` shows the Im(m)·x ≲ 700 limit in the same ABOUT to be conservative: Im(m)·x = 1000 works
  to 1e-12 and 4.6e-11.

## M5 — should-fix — Debye terms for m near 1 with slight absorption [weakens]

**Where.** `mie_debye.py:43-47` (ABOUT «сумма ряда равна коэффициентам Ми»), `mie_debye.py:133-156` (the remainder).
In v17: `viz.py:177-178` and the legend in `view.js:147` («каждый — свет одного пути через каплю; их сумма с
интерференцией даёт белую кривую»).

**Evidence: `s03c_debye_v17_limits.py` and `s03b_debye_remainder.py`.** At x = 100:

| m | max \|R11\| | largest \|a^(p)\|, \|b^(p)\| for p = 1..3 (of the largest Mie coefficient) | largest Debye/Mie intensity ratio |
|---|---|---|---|
| 1 + 1e-6i | 4.79 | 1.6e6 (b at n = 117) | 1.65e19 |
| 1 + 0.01i | 2.8 | 1.1e2 | 3.6e8 |
| 1.0001 | 1 | 50 | 1.5e11 |

For m = 1 + 1e-6i, the partial sums for p ≤ 4 plus `remainder_*` miss a_n by 5.1e-4. The closed form itself is right
to 4e-10. Where |R11| > 1 the geometric series in p diverges: the closed form is then its continuation, not its sum.

For real m → 1 the large terms are the expected cancellation of diffraction and transmission, which is physical. But
the |R11| > 1 orders of a weakly absorbing m ≈ 1 are not paths of light. v17 admits such drops (custom n = 1.0,
κ = 0.01, or a medium index close to n).

**Suggested fix.**
- Return a per-order flag where |R11| ≥ 1 or |TT/(1 − R11)| ≫ |a_n|, and say in the ABOUT that the series converges
  only where |R11| < 1.
- Compute the remainder with R11^p consistent with the cancellation-free 1 − R11.
- In v17, show a notice when the terms p ≤ 3 exceed the Mie total by orders of magnitude.

## M6 — should-fix — vacuum as the medium is not a stated approximation [weakens]

**Where.** `viz.py:550-555`: the header's `approximations` list single scattering, the black-body Sun without its disc,
spheres and water without absorption, but not the medium. The default is `n_medium = 1` (`viz.py:69`).

**Evidence: `s11_air_medium.py`.** The illustrative n_air − 1 = 2.77e-4 at 550 nm is not verified against a source;
only the size of the effect matters here.

| n_medium | m | Descartes p = 2 | Descartes p = 3 | first Airy maximum (150 µm) |
|---|---|---|---|---|
| 1 | 1.335401 | 138.270° | 128.482° | 138.959° |
| 1.000277 | 1.335031 | 138.216° | 128.578° | 138.906° |

These shifts exceed the 0.05° used by `bow2`/`bow3` and the three decimals quoted in the README and in
`sources/verification_2026-11-04_p1_mie.md` §4.

**Suggested fix.** Either list "the medium is vacuum (air would move the bows by ~0.05–0.1°)" among the approximations,
or default to air with a sourced dispersion formula (e.g. Ciddor 1996), verified like IAPWS.

## M7 — should-fix — size averages: what `err` means, the 3σ cut and the ripple [weakens]

**Where.**
- `mie_poly.py:13-17` ("the ripple … has a period ~1.5 in x … is resolved"; "err … a measured estimate").
- `mie_poly.py:35-37` (ABOUT).
- v17 `README.md:37-44, 71-73, 91-94`.
- `tests/test_mie_water.py:90-101` (tolerance `5·err + 1e-3·ref`).

**Evidence: `s06_poly_resolution.py`, `s06b_cut_and_sampling.py`, `s06c_ripple_period.py`, `s07b_v17_more.py`.** In
s06 and s07b the reference is the same sum on a 25–50× finer grid.

1. **`err` is honest only as a maximum over angles.** Per angle the actual error exceeds `err` at 35 % (glory preset),
   37 % (supernumerary), 44 % (rainbow) and 51 % (fogbow) of the 551 angles. The ratio error/err reaches 100–9e5 at
   angles where the half-sums happen to agree. As a maximum over angles, it is of the right order or pessimistic:
   - for the glory preset: 1.9e-2 actual against an `err` of 4.9e-2;
   - for supernumerary at 735 nm: 0.036 actual against 0.312 (`s07b_v17_more.out`).
   v17 shows only that maximum (`sky_sum`), so the display is honest. The module's "error estimate per angle" wording
   is not.

2. **The ±3σ cut is a bias that `err` does not contain.** On one grid (`s06b`), cutting at 3σ instead of 6σ changes
   ⟨dσ/dΩ⟩ by up to:
   - 4.7e-4 of the peak for the rainbow preset;
   - 2.6e-3 for the glory preset;
   - 4.6e-3 for the fogbow preset.
   v17's README does not mention the cut.

3. **Narrow resonances are sampled.** Fine sums with dx = 0.05, 0.031 and 0.0185 for 150 µm drops still differ by
   5.5e-3 of the peak at the glory (2.4e-3 for 8 µm). This is consistent with the docs' "sampled, not resolved"
   [neutral].

4. **The ripple's period is not "~1.5".** By FFT of |S1|² + |S2|² over x in [1000, 1060], the strongest periods are:
   - at 140°: 1.277 and 1.25;
   - at 175°: 1.176 (= 2π/4m, reflection against p = 2 on the axis);
   - at 180°: 0.273, then 0.83 and 0.39.
   At 180°, dx = 0.25 gives about one node per period. The sum survives only because the smooth gamma weight
   suppresses the alias. The claim "the ripple is resolved" does not hold at the antisolar point.

5. **The supernumerary `sky_sum` does not reproduce.** The README quotes 0.11; it reproduces as 0.312 (16 wavelengths,
   `s07_v17_presets.out`). Every other preset number checked reproduces (see "Verified").

**Suggested fix.**
- Call `err` "an order-of-magnitude estimate of the largest error over angles".
- State the cut and its measured bias in v17's README (or cut at 5–6σ: cheap).
- Correct the ripple statement (the 180° component and the reliance on the weight's smoothness).
- Update the supernumerary number.

## M8 — nit — the miepython xfail text and a docstring [neutral]

**Where.** `tests/external/test_ext_mie_miepython.py:209-212` (xfail reason «its top orders lose accuracy at large
x»); `test_ext_mie_miepython.py:21-22` («coefficient_bound: 1e-12 … for x <= 1000, 2e-11 to 2e4»), while
`mie.coefficient_bound` is 2e-11 for every x ≤ 2e4.

**Evidence: `s09_miepython_errors.out`.** miepython 3.3.0 against the suite's own 40-digit `_exact`, at x = 1e4:

| orders | miepython error (of the largest coefficient) | engine error |
|---|---|---|
| n = 1–10 | 1.2e-9 | 4.9e-13 |
| n up to 9000 | 1.2–2.1e-9 | 5–6e-13 |
| near n ≈ x | up to 3e-8 | — |

At x = 1000 miepython's error is 1e-12 at every order. The four xfailed rows are n = 1 and n = 5044 (≈ N/2), not the
top orders. Attributing them to the library is right; the stated cause is not.

**Suggested fix.** "miepython's coefficients carry a ~1e-9 error at every order at x = 1e4 (1e-12 at 1000), largest
near n ≈ x". Correct the docstring.

## M9 — nit — the 40-digit references are not exact when \|mx\| ≫ N for real m [neutral]

**Where.** `tests/test_mie.py:66-80` (`_ref_mp_recurrence`: D = 0 at N + |mx| + 50) and `test_ext_mie_miepython.py:60-76`
(`_exact`: + 60).

**Evidence: `s14_hankel_branch.py`.** For m = 1e5 and x = 0.5, this recurrence reference is 3.57e-5 off the
Bessel-function reference, while the engine is 1.6e-16 off. The first line of `s14_hankel_branch.out` is therefore
the reference's error, not the engine's. Below |z| the downward recurrence of D is neutrally stable, so a start only
60 orders above |z| has not decayed.

All present test cases have top − |mx| ≈ N ≫ |mx|^(1/3), so they are unaffected.

**Suggested fix.** Start at |mx| + c·|mx|^(1/3) + 100 or from the continued fraction, or document the condition.

## M10 — nit — branches without a direct test [neutral]

**Where.** `mie._start_D` with `_hankel_psi_pair` (`mie.py:136-172`, used where |mx| > N²) is reached only by
`test_perfect_conductor_limits` at a tolerance of 1e-5 (`test_mie.py:379-380`). `mie.log_psi` (`mie.py:238-269`) has no
direct test; it is exercised only inside `mie_debye` where ψ(mx) underflows.

**Evidence: `s14_hankel_branch.out`.** The Hankel branch is accurate to 1.6–2.0e-16 at:
- m = 1e5, x = 0.5;
- m = 300 + 300i, x = 2;
- m = 2000, x = 0.5;
- m = 50 + 1e4i, x = 0.3.

The continued-fraction start for a real |mx| well above N (178–387 oscillatory steps) is accurate to 2e-16 … 6e-14.

**Suggested fix.** Add these as tests against Bessel-function references.

## M11 — nit — v17 texts and labels [neutral]

- `view.js:217`: «основная радуга ≈ 138°, вторичная ≈ 129°» is a fixed known-fact text. It is wrong for custom drops:
  for n = 1.5, Descartes' p = 2 angle is 157.2°. Use `M.meta.bows`.
- `view.js:147`: «их сумма с интерференцией даёт белую кривую». Only p = 0…3 are drawn, so the sum needs p ≥ 4 (the
  remainder); see also M5.
- `viz.py:233-237`: for m ≤ 1 the rays of m = 1.333 are drawn. They are labelled, but the drop's own p = 0, 1 rays exist
  for b < m.
- `viz.py:290` (`bow2`/`bow3`: tol=0.05) and `viz.py:467` (`sky_bow`: tol=0.5) give the tolerance in degrees, while
  `rel` is relative. A 7° miss would read as within 0.05. These checks are info-only, so nothing is mis-scored, but the
  passport shows a misleading tol.

## M12 — nit — physics in the visualization's code [neutral]

- `engine/drops.py:61-75` computes the scattered intensity for a polarised incident wave,
  I = |S2|²cos²φ + |S1|²sin²φ. That is B&H's far field, physics that belongs in `core.optics.mie` (RULES §1, LAYERS
  rule 5).
- `viz.py:174-175` recomputes the phase-function normalisation and P, which the engine has as `mie.phase_function` and
  `mie.mueller(...)["P"]`. They agree, but the duplicates can drift.

## M13 — nit — small doc slips [neutral]

- `core/data.py:242-245`: `water_index` says "0 <= t <= 110 C here: the liquid at 0.1 MPa, the stable range of both".
  SR6-08 §2.3 (grepped): "At some temperatures within this range, the equilibrium phase at 0.1 MPa is a solid (below
  approximately 273.15 K) or a vapor (above approximately 372.76 K); at these conditions Eqs. (1)-(3) describe the
  properties of the metastable liquid phase." So 100–110 °C is metastable. v17 uses at most 40 °C, so this does not
  matter there.
- `mie.py:348-349`: the `internal_coefficients` docstring says it returns "(c_n, d_n, log_scale)"; it returns two
  arrays.

## M14 — nit — the open items are not recorded in one place [neutral]

- The v17 README says "cause not found, STATUS" (`README.md:54`) and "Open items: ../../STATUS.md" (`README.md:98`).
  `STATUS.md` has no entry for B8, Mie or v17: `grep -i "mie\|v17\|quadrature" STATUS.md` finds nothing relevant.
- The "coarse" size sampling is shown only as a line of text in the sky panel (`view.js:217`); it is not among the
  header's approximations and gets no notice. Two examples:
  - `big_drops`: dx = 2.2–2.5 in x, 1199 nodes (s07b);
  - radius 600 µm ±30 %: dx = 14.9, 1.05 GB peak RSS, about 5 s per wavelength, 24 wavelengths, ~2 min, with no label
    (s13).
  At these steps both the ripple and the supernumeraries are aliased into noise (M7.4).
- **Suggested fix:** one STATUS entry for B8 (M1–M7 residuals, the quadrature cause) and the coarse sampling in
  `approximations`.

---

## Verified and holding

**Wiscombe's test cases, by an independent route** [useful] (`s01_wiscombe_independent.py`). The route was written
here from B&H 4.53 with mpmath's half-integer Bessel functions: no recurrence and no logarithmic derivative.
- Against the engine, all orders agree to 7e-16 … 3.7e-15 of the largest coefficient.
- The printed values at x = 10 and 100 (m = 1.5 and 1.5 − 0.1i) are reproduced within half a unit of the last printed
  digit: Q_ext, Q_sca, g, S1(0), S1(90), S2(90), S1(180).
- The conjugation mapping (his m and S are the conjugates of B&H's) is confirmed.

From the report (OCR of the archive.org copy, grepped): "Sample results from MIEV1, rounded to 6 significant digits,
are presented in Appendix III. Users should reproduce these results before attempting to apply MIEVO or MIEV1." (OCR
spells MIEV0 as "MIEVO".) Eq. (50) appears in the OCR as "x + 4.05x + 2 8 < x < 4200 (50)", consistent with
`n_wiscombe`. Most of the Appendix III numbers are present verbatim in the OCR text; for example "2.881999" and
"0.742913" were found, and "EFFICIENCY FACTORS 2.006775 1.0 99193 0.937582" is an OCR misreading of 0.907582. The
engine's test reproduces all eight cases.

**The optical theorem and energy balance through the fields** [useful] (`s02`). Q_ext from the interference flux
equals the series to 2e-14 … 5e-14 in seven cases, including absorbing spheres, m < 1 and the conductor. Q_abs from the
total flux equals the series (abs. diff/Q_ext ≤ 3e-13). The negative control misses by 44 %. The conventions of the near
fields (exp(−iωt), outgoing ξ = ψ − iχ = z h⁽¹⁾, Z·H, the internal fields' scaling) are consistent with the series.

**The Debye series against Hovenac & Lock** [useful] (`s03`, page images of NASA CR-187191). Hovenac and Lock's 1991
report, the report version of JOSA A 9, 781 (1992), is open on NASA NTRS. Its Appendix A was read from page images:
- the time dependence: "The time dependence of the waves is taken to be e^{-iωt}";
- (A18)–(A22): α = 1 for TE and n1/n2 for TM; β = n1/n2 for TE and 1 for TM;
- (A29): a_ℓ, b_ℓ = ½[1 − R22 − Σ_{p≥1} T21 (R11)^{p−1} T12].

The engine's R22, R11 and T21T12 equal these expressions algebraically, with β_engine = m for b_n (TE) and 1/m for a_n
(TM). The verification record's "their printed equations were not compared" can now be closed.

By localization ("When x >> 1, these fractions are approximated by the Fresnel coefficients for oblique incidence on a
flat interface with either the TE or TM polarization", grepped), the engine's |R22|, |R11| and |T21T12| at x = 2000
equal Fresnel's |r_s|, |r_p| and 1 − r² to 5 digits at incidence angles of 10–70°, including the Brewster dip of TM.
The TE↔s and TM↔p assignment is therefore right.

The sum identity holds for m = 0.5, 0.75, 1.001, 1.333, 3, 10, 1.5 + 0.5i and 1.5 + 1i, x up to 2e4 (1e-13 … 1e-9),
apart from M4 and M5.

**Rainbow: Descartes, Alexander and Airy** [useful] (`s04`).
- Descartes' angles: 137.9703° and 129.0219° for m = 4/3; 138.2698° and 128.4819° for water (m = 1.335401).
- Alexander's band: 9.788°.
- The engine's |h|/2 equals Hovenac & Lock's Eq. (11), h = (p²−1)²(p²−n²)^{1/2}/(p²(n²−1)^{3/2}), to all printed
  digits for p = 2 and 3. So Airy's argument x^{2/3}Δ/h^{1/3} agrees with the report.
- The p = 2 Debye peak in s polarisation lies beyond Descartes by 0.9775° at x = 1000 (Airy 0.9914°) and 0.4736° at
  x = 3000 (Airy 0.4766°), as claimed.
- The supernumerary maxima are within 0.5–1.7 % of Airy's offsets.
- The peak Debye/Airy ratio is 0.981 and 0.991.

In p polarisation Airy fails completely: the strongest p-polarised maximum lies 4.3 Airy offsets beyond Airy's first
maximum, because of the Brewster angle of the internal reflection. The module's ABOUT says so [neutral].

**Coefficients in hard regimes** [useful] (`s05`(b), `s14`). Absorbing and large |m| at x = 1000–3000 are accurate to
1e-14 … 4e-13, with the downward D_n stable throughout. The Hankel and continued-fraction starts are accurate to
2e-16 … 6e-14.

**Data** [useful]. These were fetched and grepped:
- IAPWS R9-97, from iapws.org: Table 1 a0–a7, λ_UV and λ_IR equal `IAPWS97_RINDEX_A` digit for digit; the range and
  the Table 3 values match.
- IAPWS SR6-08: Table 1 rows 5–10 (a_i, b_i, n_i, m_i), R, T_R, T_a, T_b and the Table 8 densities match `IAPWS08_*`.
- IAU 2015 B3 (Prša et al., arXiv:1605.09788v1): "T⊙N = 5772 K" and "yielding T ⊙ = 5772.0 ± 0.8 K".
- The terms of IAPWS publication: "Publication in whole or in part is allowed in all countries provided that
  attribution is given to the International Association for the Properties of Water and Steam".

**v17 presets** [useful] (`s07`, `s07b`, 16 wavelengths): the README's numbers reproduce.

- **rainbow:** x = 1713.6; p = 2 maximum at 138.95° (Airy 138.959°); p = 3 maximum at 127.30° (Airy 127.251°). In
  white light the brightest angle is 138.9°, the supernumerary luminance maxima are at 140.4°, 141.5°, 142.4° and
  143.2°, and the secondary bow is at 127.4°. The checks give `debye` 4.3e-12, `energy` 4.4e-16 and `sky_sum` 0.036.
- **supernumerary:** maxima at 139.1°, 141.1°, 142.5°, 143.7° and 144.7°; p = 2 at 139.15° (Airy 139.173°). The one
  number that does not reproduce is its `sky_sum` (M7).
- **glory:** maxima at 178.1°, 175.9° and 174.0°; bow at 142.5° (Airy 143.13°).
- **fogbow:** bow at 141.2°; glory maxima at 177.8° and 179.0°; no secondary bow.
- **near:** `boundary` 2.0e-9 and `plane_1` 9.0e-10 against 4.1e-8; `debye` 1.7e-15.
- **absorbing:** Q_abs = 1.051.

Every non-info check passes on the presets. M2 and M4 are failures off the presets.

**The colour pipeline** [neutral].
- XYZ = Σ w_λ·B_λ(5772 K)·⟨dσ/dΩ⟩·cmf(λ), with trapezoid weights in nm.
- The exposure puts Y = 2 at the brightest angle, then `tools.colour.to_display` applies L/(1+L) at constant
  chromaticity (a scale of XYZ), clips negative components and scales out-of-gamut colours. This changes the luminance
  of saturated spectral colours slightly, which is acceptable for display.
- The luminance-weighted polarisation is computed correctly (−Σ Y·S12/Σ Y·S11).
- The hover text gives θ, Y/Y_max and P at the pixel's angle.

**Costs** [neutral]. The times come from s07, s07b and s13:

| world | build | sky |
|---|---|---|
| rainbow (16 wavelengths) | 1.0 s | 7.2 s |
| big_drops (16 wavelengths) | 1.9 s | ~2 s per wavelength, ~35 s in all (the label says "~минута") |
| largest admitted, radius 600 µm ±30 % (24 wavelengths) | 4 s | 5 s per wavelength, ~2 min, 1.05 GB peak RSS, unlabelled (M14) |

**The comparison suite** [neutral]. Its conventions are handled correctly:
- miepython takes m = n − ik; its a_n, b_n equal B&H's; its S are the conjugates.
- The quotations are verified against the installed docstrings (`g1_miepython_docstrings.out`): "Complex refractive
  index of the sphere, defined as m = n - ik", "automatically corrected to its conjugate value to ensure a valid
  input", "The normalization is controlled by `norm` and should be one of".

On the library's side, the tolerance is built from the library's own measured coefficient error plus its truncation
tail. Its Q and S rows therefore test the library's sums, as its docstring says. That is fair, but those rows can
hardly fail for the library. The four xfails are rightly library-side (M8 is about their wording).

**Licence cleanliness** [useful]. `mie.py` does not follow MIEV0/MIEV1 or BHMIE beyond the textbook formulas. The MIEV1
listing in Wiscombe's report (OCR) shows:
- `BIGA` with an up-or-down recurrence choice (`... WHETHER TO USE UP- OR DOWN-RECURRENCE FOR BIGA`);
- upward ψ/χ in the combined complex `ZETN`;
- the S+/S− sums (`SP(J)`, `SM(J)`);
- Wiscombe's own π_n recurrence.

BHMIE (as widely published) recurs ψ and χ upward from n = 0 and starts D = 0 at max(xstop, |mx|) + 15. The engine
instead uses:
- D_n always downward, started by a vectorised modified-Lentz continued fraction (Thompson & Barnett) or by Hankel's
  finite sums (DLMF 10.49);
- ψ by Miller's normalised downward product;
- χ upward as a separate array;
- the direct S1/S2 sums with B&H's π_n recurrence;
- log-space Debye terms and NumPy batching.

What is shared is only the textbook form a_n = [(D/m + n/x)ψ_n − ψ_{n−1}]/[…] (B&H 4.88; MIEV1 line 144 has the same
textbook form), the standard initial values χ_{−1} = −sin x, χ_0 = cos x, and Wiscombe's published N. No copied
expression was found.

## Sources that could not be obtained

- Bohren & Huffman (a book).
- Lentz (1976) and Thompson & Barnett (1986), both paywalled.
- Hovenac & Lock, JOSA A 9, 781 (1992): the CORE link returned HTML. The NASA report version was used instead.
- Laven's papers: only an abstract was seen.
- Nussenzveig.
- Airy (1838).

The Ciddor/Edlén air index was not fetched (M6 uses an illustrative value).

## Index of scripts

| script | what |
|---|---|
| `s01_wiscombe_independent.py` | Wiscombe x = 10 and 100 by mpmath Bessel functions against the printed values and the engine |
| `s02_flux_optical_theorem.py` | Q_ext, Q_sca, Q_abs from the Poynting flux of the near fields, with a negative control |
| `s03_debye.py`, `s03b_debye_remainder.py`, `s03c_debye_v17_limits.py` | the Debye sum, the localization against Fresnel, the remainder, the v17 tolerance, m ≈ 1 |
| `s04_airy_p2.py` | Descartes, h against Hovenac & Lock, the p = 2 peak against Airy at x = 1000 and 3000 (s and p) |
| `s05_bound_resonances.py`, `s05b_resonance_conditioning.py` | the coefficient bound on resonance peaks and hard regimes; backward stability |
| `s06_poly_resolution.py`, `s06b_cut_and_sampling.py`, `s06c_ripple_period.py` | the size average's actual error against `err`, the 3σ cut, resonance sampling, the ripple periods |
| `s07_v17_presets.py`, `s07b_v17_more.py` | v17 presets through the harness: checks, maxima, sky_sum, costs |
| `s08_quadrature_forward_peak.py`, `s08b_weights.py` | the cause of the Gauss–Legendre deviation (numpy and scipy weights) |
| `s09_miepython_errors.py` | miepython's coefficient error per order (image light-funnel-ext) |
| `s10_check_blindness.py` | what `theorem`, `energy` and `debye` detect (perturbed D, ψ, χ) |
| `s11_air_medium.py` | the bows in air against vacuum |
| `s12_v17_energy_check.py`, `s12b_energy_scan_small.py` | the v17 `energy` check failing on a correct engine |
| `s13_v17_cost_extreme.py` | the cost of the largest admitted world |
| `s14_hankel_branch.py` | the Hankel and continued-fraction starts against Bessel references; the recurrence reference's limit |
| `g1_miepython_docstrings.out` | grep of miepython 3.3.0's docstrings and licence metadata |
| `out_engine_tests.txt` | the three engine test files in Docker: 103 passed |
