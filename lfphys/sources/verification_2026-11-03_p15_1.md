# lfphys source verification — 2026-11-03, plan item P15.1 (batch B6: space and gravity)

Purpose: every formula and number used by `core.gravity.nbody`, `core.gravity.kerr_newman` and the charge added to
`core.gravity.kerr_geodesics`, checked against the source text. Texts fetched on 2026-11-03 (arXiv PDFs with
`pdftotext -layout`; NASA ADS article scans — two of them carry a text layer, two were read on the rendered pages with
`pdftoppm`; one Apache-2.0 source file from the Hipparchus project's published coverage pages). Journal references
and DOIs from the arXiv API. No contact parameter or personal identifier was sent with any request. Status codes as
in `verification_2026-10-23.md`: VERIFIED (quoted) / DIFFERS (both given) / NOT FOUND / NOT FETCHED (closed text;
what replaces it is said).

## 1. The fourth-order Hermite scheme — Kokubo, Yoshinaga & Makino 1998 ("KYM98")

"On a time-symmetric Hermite integrator for planetary N-body simulation", MNRAS 297, 1067–1072 (1998); ADS scan
1998MNRAS.297.1067K (with a text layer; the minus sign is extracted as "¹").

* Abstract: "The fourth-order implicit Hermite scheme is a time-symmetric integrator that has no secular energy error
  for the integration of periodic orbits with time-symmetric time-steps." VERIFIED.
* Predictor, Eqs. (1)-(2): "xp,j = xj + vj (t − tj) + aj/2 (t − tj)² + ȧj/6 (t − tj)³", "vp,j = vj + aj (t − tj) +
  ȧj/2 (t − tj)²". Corrector, Eqs. (3)-(6): "xc,i = xp,i + a(2)0,i/24 Δti⁴ + a(3)0,i/120 Δti⁵", "vc,i = vp,i +
  a(2)0,i/6 Δti³ + a(3)0,i/24 Δti⁴", "a(2)0,i = [−6(a0,i − a1,i) − Δti(4ȧ0,i + 2ȧ1,i)]/Δti²", "a(3)0,i =
  [12(a0,i − a1,i) + 6Δti(ȧ0,i + ȧ1,i)]/Δti³". VERIFIED (read in the extracted layout, fractions spread over lines).
* Implicit form, Eqs. (7)-(8): "x1 = x0 + ½(v1 + v0)Δt − 1/10 (a1 − a0)Δt² + 1/120 (ȧ1 + ȧ0)Δt³", "v1 = v0 +
  ½(a1 + a0)Δt − 1/12 (ȧ1 − ȧ0)Δt²"; "It is clear in this formula that the Hermite integrator is time-symmetric".
  VERIFIED. The engine corrects by (7)-(8); with the same a1, j1 they equal (3)-(6) (checked algebraically: both give
  x1 = x0 + v0 Δt + (7 a0 + 3 a1) Δt²/20 + (ȧ0/20 − ȧ1/30) Δt³), so the continuous output (the Taylor polynomial of
  (3)-(4)) ends on the committed state.
* Step, Eqs. (9)-(10), (12): the Aarseth criterion with "a(2)1,i = a(2)0,i + a(3)0,i Δti" and "The value a(3)1,i is
  the same as a(3)0,i, because we use the third-order interpolation"; start "Δtc = ηs |a|/|ȧ| ... with a sufficiently
  small value of ηs". VERIFIED.
* Iterations: "the results for n = 3 and 4 are still indistinguishable" (10^5 orbits, Fig. 2); "as the eccentricity
  increases, the necessary times of the EC iteration to achieve the time-symmetry increase". VERIFIED (default
  n_iter = 3).
* Makino & Aarseth 1992 (PASJ 44, 141), the origin of the scheme: the ADS scan 1992PASJ...44..141M has no text layer
  and was not read; the scheme is used as KYM98 states it ("the fourth-order P(EC)n Hermite scheme (Makino & Aarseth
  1992)"). NOT FETCHED as text (cited through KYM98).

## 2. Jerk and Aarseth's criterion — Nitadori & Makino 2008 ("NM08")

"Sixth- and eighth-order Hermite integrator for N-body simulations", New Astron. 13, 498 (2008),
doi 10.1016/j.newast.2008.01.010; arXiv:0708.0738v4.

* Eqs. (1), (2), (5): "Aij = mj rij/rij³", "J ij = mj vij/rij³ − 3αAij", "α = rij · vij / rij²", with "r ij = r j −
  r i , v ij = v j − v i". VERIFIED (the engine multiplies by G).
* Eq. (15): "∆t = sqrt(η (|a||a(2)| + |a(1)|²)/(|a(1)||a(3)| + |a(2)|²))"; "Usually, a value around 0.02 is used for
  η." VERIFIED (default eta = 0.02).
* "Another advantage of the fourth-order Hermite scheme is that it is time-symmetric, when used with the
  correct-to-convergence mode." VERIFIED.

## 3. Time-symmetrized steps — Hut, Makino & McMillan 1995 ("HMM95")

"Building a better leapfrog", ApJ 443, L93–L96 (1995); ADS scan 1995ApJ...443L..93H (no text layer: read on the
rendered pages L93-L95).

* Eqs. (4a)-(4b): "ξ1 = f(ξ0, δt)", "δt = ½[h(ξ0) + h(ξ1)]"; "We solve these implicit equations iteratively and
  simultaneously for all particles in the system." VERIFIED on the page. The engine's h is Aarseth's criterion at each
  end of the step from the step's own interpolant (KYM98 Eqs. 5, 6, 10), symmetric under reversal of the step.
* Eq. (5) (a truncated Hermite form, not used): "r1 = r0 + ½(v1 + v0)δt − 1/12 (a1 − a0)(δt)²". VERIFIED on the page.
* e = 0.999, 10³ steps per orbit: "For Hermite, a single iteration resulted in a drift of ∆a/a ≃ 10⁻⁶, while two
  iterations per step gave ∆a/a ≃ 2 × 10⁻¹⁰." VERIFIED on the page.

## 4. The fourth-order symplectic composition — Forest & Ruth 1990, Yoshida 1990

Forest & Ruth, Physica D 43, 105 (1990) and Yoshida, Phys. Lett. A 150, 262 (1990): NOT FETCHED (closed). Quoted from
Omelyan, Mryglod & Folk, "Optimized Forest-Ruth- and Suzuki-like algorithms for integration of motion in many-body
systems", Comput. Phys. Commun. 146, 188 (2002), doi 10.1016/S0010-4655(02)00451-4, arXiv:cond-mat/0110585:

* Eq. (8) and below: "a1 = a4 = θ/2, a2 = a3 = (1 − θ)/2, b1 = b3 = θ, b2 = (1 − 2θ), b4 = 0, and θ = 1/(2 − ∛2) ≈
  1.3512"; "For A ↔ B, Eq. (8) will represent the velocity FR counterpart (VFR), which can be derived directly from
  Eq. (5) at a1 = 0, a2 = a4 = θ, a3 = (1 − 2θ), b1 = b4 = θ/2 and b2 = b3 = (1 − θ)/2"; A the drift
  "{r + τv, v}", B the kick "{r, v + τf/m}" (Eq. 6). VERIFIED. The engine uses VFR (kicks at both ends: the
  accelerations at the step's ends serve the continuous output). The order conditions of the triple jump (2θ + (1 −
  2θ) = 1, 2θ³ + (1 − 2θ)³ = 0) hold for this θ; the tests measure fourth order.

## 5. The figure-eight orbit — Chenciner & Montgomery 2000

"A remarkable periodic solution of the three-body problem in the case of equal masses", Ann. of Math. 152, 881–901
(2000), arXiv:math/0011268.

* Fig. 1, "(Initial conditions computed by Carles Simó)": "x1 = −x2 = 0.97000436 − 0.24308753i, x3 = 0; V⃗ = ẋ3 =
  −2ẋ1 = −2ẋ2 = −0.93240737 − 0.86473146i", "T = 12T̄ = 6.32591398, I(0) = 2, m1 = m2 = m3 = 1"; "(We choose units so
  that the gravitational constant is 1.)". VERIFIED (complex numbers as plane vectors x + i y).
* Measured [useful]: with these digits the orbit closes after T to 1.8e-7 (the reference DOP853 at 1e-13); the
  effect of rounding the published digits (half a unit of the 8th decimal, propagated by the monodromy matrix) bounds
  it (tests).

## 6. Burrau's (Pythagorean) problem — Szebehely & Peters 1967

"Complete solution of a general problem of three bodies", AJ 72, 876–883 (1967); ADS scan 1967AJ.....72..876S (with an
OCR layer; Fig. 1 and Table I read on the rendered pages 876 and 881).

* Set-up: "The sides of the triangle formed by the three bodies at t=0 are 3, 4, and 5 and the masses of the
  participating bodies are also 3, 4, and 5. The particle with mass m1=3 ... is located at that apex of the triangle
  which is opposite to the side with length 3"; "The three initial speeds are zero"; Fig. 1: "P1(1,3) m1=3",
  "P2(−2,−1) m2=4", "P3(1,−1) m3=5"; "E = V = −769/60 = −12.8166... using unity for the constant of gravitation".
  VERIFIED (the OCR reads "E= F= 769/60= — 12.8166"; the page shows the minus).
* Outcome: "In the final configuration two of the three participating bodies form a permanent binary while the third
  body is rejected to infinity"; "Figure 7 shows the final formation of a binary by m2 and m3"; "The binary and the
  body with mass m1 depart with hyperbolic velocities. The period of the binary is approximately 0.9 time unit";
  Alexeev's "conditions of hyperbolic-elliptic motion are satisfied at t=69". VERIFIED.
* Table I (page 881): close approaches t1 = 1.879 (10⁻², m2 m3), t4 = 3.026 (0.6, m1 m3), t2 = 3.801 (6×10⁻²),
  t5 = 6.898 (0.1), t3 = 8.760 (8×10⁻³), t6 = 9.962 (0.5), t9 = 11.611 (0.2), t7 = 14.618 (0.2), t10 = 15.830
  (4×10⁻⁴, m2 m3), t8 = 17.001 (0.3), t11 = 19.807 (0.2), 21.791 (0.4), 22.966 (2×10⁻²), 24.537 (0.1), 27.780
  (5×10⁻²), 28.679 (0.5), 29.802 (3×10⁻³). VERIFIED on the page (pairs as printed: m2 m3 and m1 m3 alternate).
  Text: "t10=15.8299236 ... r23(t10)=4×10⁻⁴ which is the smallest distance occurring between any bodies at any time".
* DIFFERS [useful, a finding about the 1967 numbers]: t10 computed here is 15.82992027 (SciPy DOP853 at rtol 1e-13
  and the engine at eta = 6.25e-5 agree to 1e-10); the printed 15.8299236 is off by 3.3e-6 (the 1967 integration's own
  error; its energy changed by "7×10⁻⁷", Table II). The sharp minima of Table I all round to the printed times; the
  flat ones (distance 0.2-0.6) differ by up to 1.8e-3, where the distance at the printed time exceeds the minimum by
  at most 7.3e-4 (relative): a flat minimum fixes its time poorly.
* Sensitivity (Boekholt, Moerman & Portegies Zwart, PRD 104, 083020 (2021), arXiv:2109.07013): "Over the lifetime of
  the interaction, small perturbations grow by about 9 orders of magnitude". VERIFIED. Measured here [weakens the
  reach of a double-precision Cartesian integrator]: the runs agree with eta up to t = 15.83 and then sit on a floor of
  ~1e-7 that does not shrink with eta (the rounding of positions of size ~1 at a 4e-4 separation), amplified ~1e6 by
  t = 60; the outcome class (binary 2-3, body 1 escapes) was the same in six runs with eta from 1e-3 to 2.5e-5
  (eta = 5e-3 gives a wrong pair), the binary period 0.72-1.36.

## 7. DOP853 error estimate (used by `kerr_newman`)

The tableau is SciPy's (`scipy.integrate.DOP853.A, B, E3, E5`, BSD-3, used unmodified at run time; checked: the 13th
entries of E3, E5 are zero). The combination of the two embedded estimates (Hairer & Wanner's modification described in
Hairer, Nørsett & Wanner, Solving ODE I, 2nd ed. — NOT FETCHED) quoted from the Apache-2.0 Hipparchus source
`org/hipparchus/ode/nonstiff/DormandPrince853Integrator.java` (its published coverage page):
"double den = error1 + 0.01 * error2;" and "return FastMath.abs(h) * error1 / FastMath.sqrt(helper.getMainSetDimension()
* den);", with error1, error2 the sums of the squared scaled 5th- and 3rd-order estimates; class comment: "an 8(6)
method by Dormand and Prince ... modified by Hairer and Wanner to use a 5th order error estimator with 3rd order
correction". VERIFIED (the formula only; no code copied).

## 8. Kerr–Newman metric — Adamo & Newman 2014

"The Kerr-Newman metric: A Review", Scholarpedia 9, 31791 (2014), arXiv:1410.6626.

* Below Eq. (2.19): "R² ≡ r² + a² cos² θ, ∆ ≡ r² + a² − 2Mr + Q²". VERIFIED (their R² is our Σ).
* Eq. (3.3): "C = p²θ + cos² θ [a²(µ² − E²) + (L/ sin θ)²]" (Carter's constant). VERIFIED.
* Eq. (3.18): "r = r± = M ± sqrt(M² − a² − Q²)". Eq. (3.23): "r = rE+(θ) = M + sqrt(M² − a² cos² θ − Q²)". VERIFIED.

## 9. Separated geodesic equations with charge — Hackmann & Xu 2013

"Charged particle motion in Kerr-Newmann space-times", Phys. Rev. D 87, 124030 (2013), doi 10.1103/PhysRevD.87.124030,
arXiv:1304.2142.

* Eqs. (11)-(16): "(dθ/dγ)² = K̄ − ǫā² cos² θ − T²(θ)/sin² θ =: Θ(θ)", "(dr̄/dγ)² = R²(r̄) − (ǫr̄² + K̄)∆(r̄) =: R(r̄)",
  "dφ/dγ = āR(r̄)/∆(r̄) − T(θ)/sin² θ", "dt/dγ = (r̄² + ā²)R(r̄)/∆(r̄) − āT(θ)", "R(r̄) = (r̄² + ā²)E − āL̄ − eQ̄r̄",
  "T(θ) = āE sin² θ − L̄ + eP̄ cos θ", "∆(r̄) = r̄² − 2r̄ + ā² + Q̄² + P̄²"; "the alternative form C̄ = K̄ − (āE − L̄)²".
  VERIFIED. The engine: particle charge e = 0, magnetic charge P = 0; its W = L − aE sin² θ = −T.

## 10. Reissner–Nordström closed forms (tests)

* Photon sphere — Pugliese, Quevedo & Ruffini, "Motion of charged test particles in Reissner-Nordström spacetime",
  Phys. Rev. D 83, 104052 (2011), arXiv:1103.1807, Eq. (36): "rγ+ ≡ ½ (3M + sqrt(9M² − 8Q²))". VERIFIED. Circular
  orbits, Eqs. (11)-(12) at ǫ = 0: L²/µ² = r²(Mr − Q²)/Σ, E/µ = ∆/(r sqrt(Σ)), "Σ ≡ r² − 3Mr + 2Q²" (read in the
  extracted layout). VERIFIED; hence u^t = E/f = r/sqrt(Σ), dτ/dt = sqrt(1 − 3/r + 2q²/r²) (M = 1).
* ISCO — Morales-Herrera, Ortega-Ruiz, Momennia & Herrera-Aguilar, Eur. Phys. J. C 84, 525 (2024),
  doi 10.1140/epjc/s10052-024-12880-w, arXiv:2401.07112, Eq. (20): "M r³ − 6M² r² + 9M Q² r − 4Q⁴ = 0". VERIFIED
  (the tests take its largest real root; at Q = M it gives 4M).
* Weak deflection — Keeton & Petters, Phys. Rev. D 72, 104006 (2005), arXiv:gr-qc/0511019: Eq. (2) "α̂(b) = A1 (m•/b)
  + A2 (m•/b)² + A3 (m•/b)³ + O((m•/b)⁴)", Eq. (51) "A(r) = B(r)⁻¹ = 1 − 2m•/r + q²m•²/r²", Eq. (53) "A1 = 4,
  A2 = (5 − q²) 3π/4, A3 = 128/3 − 16q²". VERIFIED. Consistent with Sereno, Phys. Rev. D 69, 023002 (2004),
  arXiv:gr-qc/0310063, Eq. (14) "α̂(ξ) ≃ 4M ξ/ξ² + 3π/4 (5 − a²) M² ξ/ξ³", "a ≡ Q/M". VERIFIED.

## 11. Derived here (no source quoted; each tested by an independent route)

* Equatorial circular geodesics of Kerr–Newman: Ω± = ±s/(r² ± a s), s = sqrt(r − q²), from g_tt' + 2 g_tφ' Ω +
  g_φφ' Ω² = 0 with the metric of §8; E, L, dτ/dt from the metric. Tests: R = R' = 0 of the radial potential (§9);
  Kerr limit = Bardeen–Press–Teukolsky (`kerr.circular_e_l`, Ω = 1/(r^{3/2} + a)); RN limit = §10.
* ZAMO lapse, frame dragging and tetrad (α² = ΣΔ/A, ω = a(2r − q²)/A, ϖ² = A sin²θ/Σ): from the metric; tests:
  −1/g^tt, −g_tφ/g_φφ, g_φφ and the orthonormality of the tetrad with `kerr_geodesics.metric`.
* Equatorial photon orbits from R = R' = 0 at η = 0: r² − 3r + 2a² + 2q² = ∓2a sqrt(Δ) (independent route in the
  tests); the photon orbit and the ISCO are computed as numerical roots (Brent; SciPy needs rtol ≥ 4u = 8.9e-16 — a
  bug of the first version, found by the playground's wrapper and fixed before the tests were run).
* Radial Kepler time (merger test): t(r) = sqrt(D³/(2GM)) [sqrt(x(1 − x)) + arccos sqrt(x)], x = r/D, from energy
  conservation of the radial two-body problem; the Schwarzschild infall cycloid τ = sqrt(r0³/8)(η + sin η),
  r = r0(1 + cos η)/2 (textbook; the RN case of the same test uses the quadrature of dτ = dr/sqrt(E² − f)); the RN
  tortoise coordinate
  r* = r + r+²/(r+ − r−) ln(r − r+) − r−²/(r+ − r−) ln(r − r−) (dr*/dr = 1/f); Kepler's equation.
* Camera (`trace_sky`): a photon seen by a ZAMO at angle psi from the inward radial has L = varpi nu sin psi and
  E = alpha nu + omega L (§8 metric), so at a = 0 its impact parameter is b = r_o sin psi / sqrt(f(r_o)) (Synge's
  relation for the shadow's angular radius, sin psi_sh = b_c sqrt(f(r_o)) / r_o); the RN critical impact parameter
  b_c² = r_ph⁴ / Δ(r_ph) from R = R' = 0 at a = 0 with r_ph of §10 (q = 0: b_c = sqrt 27). The distant observer's screen
  (α = −λ / sin θ_o, β = ± sqrt(Θ(θ_o))) is Gralla & Lupsasca 2020b Eq. (55), verified in
  `verification_2026-10-29_p7_kerr.md` §2; Bardeen's curve is `kerr_null.critical_radius_at` (same file, §1). The
  boost of the camera uses `core.lorentz.aberrate` (B2).

## 12. Review B6-gravity (2026-11-03): sources and measurements added while processing it

Texts: the reviewer's downloads in `../../reviews/archive/2026-11-03_internal_B6-gravity/sources/` (fetched 2026-11-03 without
any contact parameter), re-read here by grep; nothing new fetched.

* KYM98 (§1), the two ingredients of time symmetry (review G9): abstract "... no secular energy error for the
  integration of periodic orbits with time-symmetric time-steps"; Sect. 3 "a result of the time-symmetry of the scheme
  achieved by the iteration of EC steps". VERIFIED (text layer lines 20 and 197). Since the review `max_passes = 1`
  honours `n_iter` (it silently meant P(EC)¹), and the tests have one control for each ingredient.
* The residual secular drift left by the symmetrization tolerance (review G8) — measured here, e = 0.999, eta = 0.02,
  386 steps per orbit, 300 orbits, the energy error's own level dE/E = 4.5e-4 at apoapsis; slope per orbit / force
  evaluations per orbit: dt_rtol 1e-3: −2.05e-6 / 1633; 1e-4: −7.1e-8 / 1988; 1e-5: −1.57e-8 / 3098; 1e-6:
  −7.5e-10 / 3419; e = 0.9: −8.4e-9 (1e-3), −1.3e-10 (1e-5). [useful] The default became 1e-4 (29 times less drift
  for 22 % more force evaluations); HMM95's numbers (§3) were not compared (its text is a scan, read on the pages).
* Aarseth's step is proportional to sqrt(eta) (§2, Eq. 15), so eta/2 divides a fourth-order error by 4 (review G10:
  the playground said 16); measured 4.05–4.11 (`test_halving_eta_quarters_the_error`).
* Kerr–Newman drift budgets (review G7): the analytic gradient of Carter's K (§8, Eq. 3.3 with W = L − aE sin²θ) and of
  μ² = −N/Σ (§9) agrees with central differences to 1e-9 relative; a body's K and μ² changed by at most its budget at
  every sampled time of the falls of review r05c (worst 5e-6 of the budget) and of an inclined orbit over 3000 M
  (1.2e-3); a relative error of 1e-7 in dp_r/dλ or dp_θ/dλ exceeds it within 300 M (×1.45, ×6.7).
* IAU 2015 Resolution B3 (Prša et al., AJ 152, 41 (2016), arXiv:1510.07674), the nominal terrestrial mass parameter:
  "(GM)NE = 3.986 004 × 10¹⁴ m³ s⁻²" (line 103 of the extracted text). VERIFIED; `core.constants.GM_EARTH` has it, p01
  used 3.986004418e14 (review G15).

Used by the gravity playground's binary (p01, review G1; Blanchet, Living Rev. Relativ. 17, 2 (2014), arXiv:1310.1528v4
— the current arXiv version renumbers the equations):

* Eq. (314): "F = 32c⁵/5G ν² x⁵ {1 + (−1247/336 − 35/12 ν) x + 4πx^{3/2} + (−44711/9072 + 9271/504 ν + 65/18 ν²) x² +
  (−8191/672 − 583/24 ν) πx^{5/2} + [6643739519/69854400 + 16/3 π² − 1712/105 γE − 856/105 ln(16x) + (−134543/7776 +
  41/48 π²) ν − 94403/3024 ν² − 775/324 ν³] x³ + (−16285/504 + 214745/1728 ν + 193385/3024 ν²) πx^{7/2}}". VERIFIED
  (lines 8023–8045, fractions spread over lines). Eq. (232), the circular energy to 3PN, "E = −µc²x/2 {1 + (−3/4 −
  ν/12) x + (−27/8 + 19/8 ν − ν²/24) x² + (−675/64 + (34445/576 − 205/96 π²) ν − 155/96 ν² − 35/5184 ν³) x³}".
  VERIFIED (lines 6097–6103). Both used only as a reference in the processing's comparison of inspiral times.
* Eq. (220b), the 3.5PN coefficient of v: "(1/c⁷)(Gm/r)[−626/35 νv⁴ − 12/5 ν²v⁴ + 678/5 νv²ṙ² + 12/5 ν²v²ṙ² − 120νṙ⁴]
  + (G²m²/r²)[164/21 νv² + 148/5 ν²v² − 82/3 νṙ² − 848/15 ν²ṙ²] + (G³m³/r³)[−1060/21 ν − 104/5 ν²]". VERIFIED (lines
  5820–5836; equal to `pn_binary.coefficients`). Eq. (226), the reaction on circular orbits, "−(32/5)(G³m³ν/c⁵r⁴)[1 +
  γ(−743/336 − 11/4 ν)] v". VERIFIED (line 6027); its 1PN bracket includes the conservative 1PN term B ṙ v with the
  inspiral's ṙ, which does not change the energy: on a circular state (ṙ = 0) the 3.5PN term alone is
  −νγ³(60.55 − 6.4ν) against the 2.5PN term's 6.4νγ² (measured ratio −0.46 at r = 20, −1.01 at r = 9).
* "gravitational radiation reaction is inherently gauge-dependent, so the expression of the force depends on the
  coordinate system which is used" (line 476); "The 3.5PN terms in the equations of motion correspond to the 1PN
  relative corrections in the radiation reaction force. They were derived by Iyer & Will [258, 259] for point-particle
  binaries in a general gauge, relying on energy and angular momentum balance equations and the known expressions of
  the 1PN fluxes. The latter works have been extended to 2PN order [226]" (lines 793–797); [226] = Gopakumar, Iyer &
  Iyer, "Second post-Newtonian gravitational radiation reaction for two-body systems: Nonspinning bodies", Phys. Rev.
  D 55, 6030 (1997), arXiv:gr-qc/9703075 (NOT FETCHED: the 4.5PN reaction that would remove the residual below).
  VERIFIED.
* Measured on the engine's equations (circular states, D = −ν dE_2PN/dt along them): D/F_1PN = 0.973 (r = 40), 0.870
  (20), 0.535 (12), 0.236 (10), 0 at r = 9.10–9.12 for every q in [0.05, 1], −0.480 (8); without the 3.5PN term 1.26,
  1.60, 2.22 (never zero down to the 2PN binding peak); (D/F_1PN − 1)/x² → −35.5 as x → 0 (review r06d). The
  remainder equals the 1PN correction |c1| x F_N at r = 10.59 (q = 1), 10.94 (0.5), 11.69 (0.25), 12.58 (0.1), 13.01
  (0.05): p01 stops the binary there. Inspiral time from x = 0.05 to 0.08, q = 1 (units G m/c³): the equations with all
  orders 15787, without 3.5PN 6677, energy balance with Eqs. (232) and (314) 10349 (with the 1PN flux only 12644).
  [weakens: no local PN equations of motion in the engine reach the last orbits; the gap is STATUS V34]
