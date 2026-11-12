# lfphys source verification — 2026-10-29, plan item P7 (Kerr half: null geodesics, shadows, generic orbits)

Purpose: every formula and number used by `core.elliptic`, `core.gravity.kerr_geodesics`, `kerr_null`, `kerr_shadow`,
`kerr_orbits`, `theories.alternatives.johannsen_metric` and the EHT block of `core.data` (appended 2026-10-29),
checked against the source text. The texts were fetched from arXiv (PDF, `pdftotext`; equations whose plain-text
rendering was ambiguous were read on the rendered page, `pdftoppm`) and from NIST DLMF (HTML). Journal references and
DOIs from the arXiv API. Access date for all items: 2026-10-29. Status codes as in `verification_2026-10-23.md`:
VERIFIED (quoted) / DIFFERS (both given) / NOT FOUND.

## 1. Kerr null geodesics — Gralla & Lupsasca 2020a, "Null geodesics of the Kerr exterior"

Phys. Rev. D 101, 044032 (2020), doi 10.1103/PhysRevD.101.044032; arXiv:1910.12881v3.

* Potentials, Eqs. (7)-(8): "R(r) = (r² + a² − aλ)² − ∆(r)[η + (λ − a)²]", "Θ(θ) = η + a² cos² θ − λ² cot² θ";
  Mino time Eq. (9) "dx^µ/dτ = (Σ/E) p^µ"; λ = L/E, η = Q/E² (Eq. 5).
* Polar roots, Eq. (19): "u± = 4θ ± sqrt(4θ² + η/a²), 4θ = ½(1 − (η + λ²)/a²)" (4θ is their Δθ).
* Ordinary polar motion, Eq. (38): "cos θo / √u+ = −νθ sn(√(−u− a²)(τ + νθ Gθs) | u+/u−)", with Eq. (29)
  "Gθ = −1/√(−u− a²) F(arcsin(cos θ/√u+) | u+/u−)"; vortical, Eq. (64): "cos θo/√u− = h dn(√(u− a²)(τ + νθ Gθs) |
  1 − u+/u−)", Eq. (56) for Gθ. VERIFIED.
* Radial roots, Eqs. (79)-(95): "A = a² − η − λ²", "B = 2M[η + (λ − a)²] > 0", "C = −a²η", "P = −A²/12 − C",
  "Q = −(A/3)[(A/6)² − C] − B²/8", ξ0 the largest root of the resolvent cubic, "z = sqrt(ξ0/2)",
  "r1 = −z − sqrt(−A/2 − z² + B/(4z))", ..., "r4 = z + sqrt(−A/2 − z² − B/(4z))"; classification Sec. IV B
  (cases I-IV). VERIFIED (the engine computes ξ0 in real arithmetic: trigonometric form for three real roots,
  Cardano without cancellation otherwise, one Newton polish).
* Radial inversion: case (1) Eq. (B27), case (2) Eq. (B46) "ro(τ) = [r4 r31 − r3 r41 sn²(X2(τ)|k)]/[r31 − r41
  sn²(X2(τ)|k)]", X2 Eq. (B45), k Eq. (B13) "k = r32 r41/(r31 r42)"; case (3) Eq. (B75) with A, B, k3 of Eqs.
  (B56)-(B59); case (4) Eq. (B109) with C, D, k4, g0 of Eqs. (B84)-(B88). VERIFIED.
* Double roots (critical curve), Eqs. (107)-(109): "λ̃ = a + (r̃/a)(r̃ − 2∆(r̃)/(r̃ − M))", "η̃ = (r̃³/a²)[4M∆(r̃)/(r̃ −
  M)² − r̃]". VERIFIED; the engine evaluates them through t = (r − 3)/a (tests: equal in 30 digits).

## 2. Lensing — Gralla & Lupsasca 2020b, "Lensing by Kerr black holes"

Phys. Rev. D 101, 044031 (2020), doi 10.1103/PhysRevD.101.044031; arXiv:1910.12873v2.

* Screen, Eq. (55): "α = −λ/ sin θo, β = ±o sqrt(Θ(θo))", Eq. (56) "±o = sign(β)". VERIFIED.
* Eqs. (58)-(59): "λ = −α sin θo", "η = (α² − a²) cos² θo + β²". The plain-text extraction reads
  "η = α2 − a2 cos2 θ0 + β 2" (brackets lost); the rendered page shows the brackets. VERIFIED on the page.
* Equatorial sources, Eq. (81): "√(−u− a²) Ir + sign(β) Fo = 2mK", Eq. (82) "m̄ = m − H(β)"; "Even m̄ corresponds to
  emission towards the observer (i.e., from the front of an equatorial disk), while odd m̄ corresponds to emission away
  from the observer". VERIFIED (the engine's image order n = m̄).
* Eq. (29) (total radial integral) and Eq. (30) (source radius from infinity). VERIFIED.

## 3. Photon ring — Johnson et al. 2020, "Universal interferometric signatures of a black hole's photon ring"

Sci. Adv. 6, eaaz1310 (2020), doi 10.1126/sciadv.aaz1310; arXiv:1907.04329v2.

* Eq. (2b) "r±γ = 2M[1 + cos(⅔ arccos(±a/M))]"; Eq. (6) "ℓ = [M(r² − a²) − r∆]/[a(r − M)]". VERIFIED.
* Eq. (4) (read on the rendered page): "u± = r/(a²(r − M)²) [−r³ + 3M²r − 2a²M ± 2 sqrt(M∆(2r³ − 3Mr² + a²M))]".
  VERIFIED as printed: equals the general roots of GL-a Eq. (19) at the critical constants (test).
* Eq. (7) "δrn = e^{γn} δr0", Eq. (8) "γ = (4/a) sqrt(r² − M r ∆/(r − M)²) ∫₀¹ dt/sqrt((1 − t²)(u+ t² − u−))", Eq. (29)
  "γ(rγ) = sqrt(R''(rγ)/2) Gθ(rγ)"; "For Schwarzschild, γ = π (Luminet 1979)"; subring flux ratio "≈ e^{−γ}".
  VERIFIED; both forms implemented and equal to round-off; the ring images computed by the tracer approach the
  critical curve by e^{−γ} per order (test).

## 4. Generic orbits — Schmidt 2002; Fujita & Hikida 2009

* W. Schmidt, "Celestial mechanics in Kerr spacetime", CQG 19, 2743 (2002), doi 10.1088/0264-9381/19/10/314;
  arXiv:gr-qc/0202090v1, App. B (read on the rendered pages 22-23): Eq. (B.4) "Q̃ = z−²[ã²(1 − Ẽ²) + L̃z²/(1 −
  z−²)]", z− = cos θ−; Eqs. (B.6)-(B.9) f, g, h, d; (B.11)-(B.14) their derivatives; (B.17)-(B.22)
  "Ẽ±² = [κρ + 2εσ ± 2 sqrt(σ(σε² + ρεκ − ηκ²))]/(ρ² + 4ησ)"; "E^(p) = E− is the lower and E^(r) = E+ the higher
  energy". VERIFIED. Finding [useful]: the closed form loses accuracy where the determinants cancel (L, Q to 1e-9
  relative at p = 30, x = 0.05; 13 % at p = 1e6); the engine polishes by Newton steps on the defining equations.
* R. Fujita, W. Hikida, CQG 26, 135002 (2009), doi 10.1088/0264-9381/26/13/135002; arXiv:0906.1420v2: Eqs. (10)-(11)
  roots ("r1 = pM/(1 − e)", "r2 = pM/(1 + e)", "A + B = 2M/(1 − E²) − (r1 + r2)", "AB = a²C/((1 − E²) r1 r2)");
  Eq. (13) k_r, k_θ; Eq. (15) Υ_r, Υ_θ; Eq. (21) Γ and Υ_φ (read on the rendered pages 8-9, the corrected v2 with the
  footnote on the typo of v1); Eq. (26) r(λ); cos θ(λ) = √z− sn(u_θ, k_θ). VERIFIED. Table 3 (a = 0.9, p = 6,
  e = 0.7, θinc = 20°): "Ωr 1.8928532285101992 × 10⁻²", "Ωθ 2.7299110395017517 × 10⁻²", "Ωφ 3.0550463796964692 ×
  10⁻²". The 30-digit reference (tests) differs from these by 1.2e-13 .. 2.3e-13 relative; the engine is within
  1e-15 of the reference. Recorded.

## 5. The emitter inside the ISCO — Cunningham 1975, as described by Chael, Johnson & Lupsasca 2021

ApJ 918, 6 (2021), doi 10.3847/1538-4357/ac09ee; arXiv:2106.00683: "While Gralla et al. (2020) follow Cunningham
(1975) and define the velocity u^µ to be on Keplerian circular orbits for r > r_ISCO and infalling for r < r_ISCO"
(Sec. 3.2); the redshift "g = −k_t/(k_µ u^µ) = 1/(u^t − λu^φ ± u^r sqrt(R)/∆)" with "the sign of the ± sqrt(R)
term is equal to the sign of the radial component of the null wavevector" — their Eq. (18) [error in earlier: cited
as Eq. 16 until review B5-K14; Eq. (16) is the intensity "I(α, β) = Σ f_n j_model(r_n) g³(r_n, α, β)"]; "f_0 = 1 and
f_n = 2/3 for n > 0"; "we use a factor of g³ to represent the redshift of the specific 230 GHz intensity (assuming a
flat emission spectrum ...) rather than the g⁴ redshift factor they use for bolometric intensity". Volume and page
from Crossref (doi 10.3847/1538-4357/ac09ee: ApJ 918, issue 1, article 6, 2021). The sign convention of p_r is the
engine's: g = 1/(-p.u), checked against the four-momentum route in the tests. Cunningham 1975 itself (ApJ 202, 788)
was not fetched: NOT FOUND (the prescription is used as quoted, with E, L of the ISCO).

Gralla, Lupsasca & Marrone 2020, "The shape of the black hole photon ring", PRD 102, 124004, doi
10.1103/PhysRevD.102.124004; arXiv:2008.03879v2 (fetched 2026-10-29 for review B5-K15): Sec. III A "We take the
matter to orbit on circular geodesics outside of the Innermost Stable Circular Orbit (ISCO), and otherwise to infall
on marginally stable geodesics"; Eq. (6) "Iobs(α, β) = Σ_{m=0}^{N} fm [g(rm, α)]⁴ Iem(rm)", Eq. (7) "fm = 1 (m = 0),
f (m > 0)", "a fudge factor to account for the effects of geometrical thickness"; "The observed intensity Iobs(α, β)
computed via Eq. (6) is to be understood as bolometric"; footnote 6 "An alternative approach would be to use g³ in
Eq. (6) in place of g⁴". VERIFIED (kerr_shadow.disk_intensity states these choices).

## 6. Non-Kerr shadow — Johannsen 2013a, 2013b; Psaltis et al. 2020

* T. Johannsen, PRD 88, 044002 (2013), doi 10.1103/PhysRevD.88.044002; arXiv:1501.02809v2 (rendered pages 5, 7, 9):
  Eq. (23) "R(r) ≡ P² − ∆{µ²[r² + f(r)] + (Lz − aE)² + Q}", Eq. (25) "P ≡ (r² + a²)A1(r)E − aA2(r)Lz"; Eqs. (51)-(56)
  the metric, "A1(r) = 1 + Σ_{n=3} α1n (M/r)^n", "A2(r) = 1 + Σ_{n=2} α2n (M/r)^n"; Eqs. (77)-(78) "α13 > −(M +
  sqrt(M² − a²))³/M³", "α22 > −(M + sqrt(M² − a²))²/M²". VERIFIED.
* T. Johannsen, ApJ 777, 170 (2013), doi 10.1088/0004-637X/777/2/170; arXiv:1501.02814v1 (rendered pages 6, 12):
  Eqs. (26)-(27) "x′ = −ξ/ sin i", "y′ = ±sqrt(Θ(i))", (29) "R(r) ≡ [(r²+a²)A1(r) − aA2(r)ξ]² − ∆[(ξ − a)² + η]",
  (30) R = dR/dr = 0; Appendix Eqs. (1)-(2) ξ(r), η(r) (transcribed in tests/test_johannsen_metric.py; equal to the
  engine's derivation in 30 digits). VERIFIED.
* D. Psaltis et al. (EHT), PRL 125, 141104 (2020), doi 10.1103/PhysRevLett.125.141104; arXiv:2010.01055v1:
  Eq. (4) "rsh = rph/sqrt(−gtt(rph))"; Eq. (8) "rsh,JP = 3√3 [1 + α13/27 − α13²/486 + O(α13³)]"; "Requiring that the
  shadow size is consistent to within 17% with the 2017 EHT measurement for M87 places a bound on the deviation
  parameter −3.6 < α13 < 5.9"; "consistent (to within ∼ 17% at the 68-percentile level)". VERIFIED; reproduced
  by the engine: [−3.557, 5.888] for |δ| ≤ 0.17.

* The α12 term (review B5-K14): Johannsen 2013a's A1 starts at n = 3 (Eq. 52 "A1(r) = 1 + Σ_{n=3} α1n (M/r)^n");
  α12 is the 1PN term of Sgr A* Paper VI's non-spinning JP form, its Eq. (17) "(1 + Σ_{i=2}^∞ α1i/r_A^i)^−2". The
  module's docstring said "Johannsen 2013a" for both [error in earlier]; corrected.
* Regularity (review B5-K6): Johannsen 2013a Sec. III B (rendered page 8): Eq. (71) "det(gαβ) = −Σ̃⁴ sin²θ /
  [A5(r)(A1(r)(r²+a²) − a²A2(r) sin²θ)²]", Eq. (72) "A1(r)(r²+a²) − a²A2(r) sin²θ ≠ 0 ... which must be fulfilled
  everywhere on and outside of the event horizon", Eq. (76) "A1(r)²(r²+a²)² − a²∆ sin²θ > 0" (no closed timelike
  curves); Eqs. (77)-(78) are lowest-order forms with r = r₊. The engine's check used (77)-(78) only [error in
  earlier]; it now checks (72) and (76) on r ≥ r₊ (worst at sin²θ = 0 and 1, the conditions being linear in sin²θ).
  One test case of the engine's own suite (a = 0.9, α13 = −2, α22 = 1) was such a singular metric and was replaced.

## 7. EHT measurements (the values appended to `core.data`)

* EHT 2019 Paper I, ApJL 875, L1, doi 10.3847/2041-8213/ab0ec7; arXiv:1906.11238: abstract "an asymmetric bright
  emission ring with a diameter of 42±3 μas"; "derive a central mass of M=(6.5±0.7)×10⁹ M⊙"; Sec. 7 "we measure
  emission region diameters of 42±3 μas, angular sizes of the gravitational radius θg=3.8±0.4 μas"; "For the distance
  of 16.8±0.8 Mpc adopted here". VERIFIED → EHT_M87_RING_DIAMETER_UAS, EHT_M87_THETA_G_UAS, EHT_M87_MASS_1E9_MSUN,
  EHT_M87_DISTANCE_MPC.
* EHT 2019 Paper VI, ApJL 875, L6, doi 10.3847/2041-8213/ab1141; arXiv:1906.11243: Sec. 9.5 Eq. (31), "We ﬁnd
  δ=−0.01±0.17 (68% credible intervals) for the stellar and δ=0.78±0.3 for the gas dynamics priors"; Sec. 10
  "θg=3.8±0.4 μas"; "a mean diameter that lies in the very small range (9.6–10.4) GM/c²". VERIFIED →
  EHT_M87_DELTA_STELLAR, EHT_M87_DELTA_GAS. (δ here is θg/θdyn − 1, the mass-to-distance deviation; Psaltis et al.
  2020 use it as the 17 % shadow-size consistency.)
* EHT 2022 Sgr A* Paper VI, ApJL 930, L17, doi 10.3847/2041-8213/ac6756; arXiv:2311.09484v1: Sec. 2.1 "θg =
  (5.125 ± 0.009 ± 0.020) µas (VLTI) and θg = (4.92 ± 0.03 ± 0.01) µas (Keck)"; Sec. 3 "The quantity δ ≡ (dsh
  /dsh,Sch ) − 1 ... dsh,Sch = 6√3θg"; "values of δ in the range [−0.075, 0] are consistent with the Kerr
  predictions"; Table 2 (eht-imaging, GRMHD): "VLT(I) −0.08+0.09 −0.09", "Keck −0.04+0.09 −0.10"; Sec. 5.1 Eqs.
  (12)-(13): "3√3(1 − 0.14)M ≲ r̃sh ≲ 3√3(1 + 0.05)M" (Keck), "3√3(1 − 0.17)M ≲ r̃sh ≲ 3√3(1 + 0.01)M" (VLTI); Eq.
  (14) "δmetric = d̃metric/(6√3) − 1" with "d̃metric is the median shadow diameter"; Eq. (17) the non-spinning JP g_tt;
  Table 3 "JP −1.1 ≲ α12 ≲ 0.5, −3.1 ≲ α13 ≲ 1.5, −7.8 ≲ α14 ≲ 4.6". VERIFIED → EHT_SGRA_*; reproduced by the
  engine: α13 ∈ [−3.063, 1.455], α12 ∈ [−1.144, 0.465] (Keck bounds, a = 0). The median diameter's centre (review
  B5-K5): Sec. 3 describes CHARM as "(iv) iterates the location of the trial center and steps (i)−(iii) such that the
  variance in the diameter along different cross sections is minimized"; for the GRMHD images "the median diameter
  Dim of the bright ring of emission, with respect to the analytically calculated center of the black hole shadow".
  The engine's default centre (half-way between the extreme α) reproduces the Kerr range [−0.075, 0]; the
  variance-minimising centre is reported as a second measure (it has two local minima for spinning, inclined
  shadows; up to 0.07 lower δ). The engine's docstring had said "as CHARM" for the default [error in earlier].
* EHT 2019 M87* Paper V, ApJL 875, L5, doi 10.3847/2041-8213/ab0f43; arXiv:1906.11242: Fig. 8 caption "(i=17° for
  a* ≤ 0 and 163° for a* > 0)" (the ≤ is a glyph "£" in the text extraction). VERIFIED → EHT_M87_INCLINATION_DEG.

## 8. Numerics — NIST DLMF; Abramowitz & Stegun

* DLMF 19.36.1 (https://dlmf.nist.gov/19.36): "1 − (1/10)E2 + (1/14)E3 + (1/24)E2² − (3/44)E2E3 − (5/208)E2³ +
  (3/104)E3² + (1/16)E2²E3" and "If (19.36.1) is used instead of its first five terms, then the factor (3r)^(−1/6) in
  Carlson (1995, (2.2)) is changed to (3r)^(−1/8)". VERIFIED.
* DLMF 22.17.5-8 (https://dlmf.nist.gov/22.17): "k1 = k/sqrt(1 + k²)", "sn(z, ik) = k1′ sd(z/k1′, k1)", "cn(z, ik) =
  cd(z/k1′, k1)", "dn(z, ik) = nd(z/k1′, k1)". VERIFIED.
* The AGM algorithm for sn, cn, dn: Abramowitz & Stegun 16.4 (not fetched; implemented from the description and
  tested against mpmath at 30 digits). Finding [useful]: SciPy's and CuPy's Cephes ``ellipj`` stop after eight AGM
  steps and switch to a first-order expansion in 1 − m above m = 1 − 1e-10, whose error grows with u: measured
  1.8e-7 in sn at m = 1 − 1e-11, u = 20 (tests/test_elliptic.py); the engine runs the AGM to convergence.
