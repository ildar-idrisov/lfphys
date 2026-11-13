# v05 — Optical bench: boundaries between media and coatings

**English** | [Русский](README.ru.md)

Single photons, one by one, on a planar structure between an incidence medium and an exit medium: a single boundary,
a quarter-wave antireflection layer, a Bragg mirror, a Fabry–Pérot film, a thin metal film, or the face of a prism
(total internal reflection; with a second prism behind a gap, frustrated total reflection). Owner guide:
`../README.md`; rules: `../RULES.md`.

The visualization is a wrapper over the engine `lfphys` (`../../lfphys/LAYERS.md`): every physical number comes from
the engine; this folder holds orchestration (the set-up, the photon time line, the checks) and drawing.

| engine module | layer | used for |
|---|---|---|
| `core.optics.interfaces` | core | `stack`: r, t, R, T, A of every structure (transfer matrices); `field_profile`: \|E\|² of s light; `brewster`, `critical`: closed-form references |
| `core.optics.thin_films` | core | closed forms for the checks (added for v05, tested in `lfphys/tests/test_thin_films.py`) |
| `core.constants` | core | the speed of light c (flight times) |
| `theories.approx.ray_optics` | theories (approximation) | `snell`: ray directions for the drawing only |

## The causal chain of one photon (all computed in the run)

1. **Emission** at a time of a Poisson stream (rate: a live parameter), with the source's wavelength and polarization
   at that moment. An unpolarized source emits s or p photons with probability ½ each (see the approximations).
2. **Flight to the structure** along the incident arm (0.30 m in the incidence medium, speed c/n₀).
3. **At the structure**, with the structure present at the moment of arrival: the run computes R, T, A for the
   photon's own wavelength, polarization and the current angle by `interfaces.stack` and draws its fate by the Born
   rule (reflected with probability R, transmitted with T, absorbed with A = 1 − R − T; an A below 1e-14, the
   round-off of 1 − R − T in a lossless structure, is set to 0 and R to 1 − T). An absorbed photon is revealed here
   (it disappears in the structure).
4. **Flight to a detector**: 0.30 m in the incidence medium (reflection detector) or in the exit medium (transmission
   detector). The fate is revealed only when the photon reaches its detector (a click). Until then a frame shows the
   photon as two packets, on the reflected and on the transmitted arm, with weights R/(R+T) and T/(R+T), the same for
   every outcome; when one detector's arrival time passes without a click, its packet disappears (Lüders update of a
   null result). The outcome itself never leaves the run before the click.

The counters are the accumulation of these events; the expected fractions are the run's own R, T, A for the segment.

## What the run computes for every segment (set-up configuration)

* r, t, R, T, A for s and p at the current λ and θ (`stack`);
* R(θ), T(θ), A(θ) for s and p at the current λ: 360 angles from 0 to 89.9° plus points around the run's own critical
  and Brewster angles; R(λ), T(λ), A(λ) at the current θ on a grid uniform in 1/λ from 300 to 1600 nm, fine enough
  for ~20 points per 2π of the round-trip phase of the whole stack (300–1600 points); the curves for the source's
  polarization (s, p or the 50/50 mixture);
* the critical angle: bisection on the run's T(θ) of the bare boundary n_in → n_out, which is exactly 0 once the exit
  wave is evanescent (Re(n_out cos θ_out) = 0); the bisection runs to adjacent binary64 angles and returns the first
  one with T = 0, so "θ ≥ θ_c" is the run's own T(θ) = 0. The layers do not move this angle (n sin θ is the same in
  every layer), and T of a thick structure can underflow to exactly 0 long before it (a film of lower index than n₀
  is evanescent beyond its grazing angle): the bisection on the whole structure reported that angle instead (found
  while fixing the review of 2026-10-23); for the prism with a gap, of the bare face;
* the Brewster angle of a single boundary: the zero of the run's r_p(θ) (Brent's method); for a multilayer the minimum
  of the run's R_p (grid, then bounded Brent minimisation between the neighbouring grid points) is shown, without a
  closed form (for a free-standing film it is exactly arctan n with R_p = 0, which the tests check);
* \|E(z)\|² of s light through the structure and ±max(0.6λ, 0.2·thickness) around it (`field_profile`);
* ray directions in every layer and in the exit medium for the drawing (`ray_optics.snell`, real part of the index).

## Live set-up (owner, 2026-10-23)

Every parameter is a live parameter (there are no law parameters: this world is accepted physics). A change applies
at once and starts a new segment:

* source (λ, polarization, rate): photons already emitted fly on with their own λ and polarization, meet the
  structure present when they arrive, and are **transitional** (counted separately, not in the new segment);
* structure (type, indices, thicknesses, number of pairs, gap): photons not yet at the structure meet the new one
  (transitional); photons past it fly on and count in the segment they belong to;
* media or angle (n₀, n_s, θ: the goniometer turns the source and both detectors): the beam paths are rebuilt and
  photons under way are **lost** (counted, with a notice).

A change is refused (and the world left as it was) when a value is out of range. A change is atomic (review
2026-10-23, V5-1): the new set-up, its segment and its checks are computed with the messages held back, and only a
change that succeeds as a whole is kept and emitted; if anything raises on the way, the world (parameters,
structure, photons in flight, counters, segments, the random generator) is restored, nothing of the change is
emitted, and the error is reported as a refused change, after which the runner sends the live values in force and
the player rolls its control back. Angles at which a wave grazes inside a layer, and the critical angle itself, are
accepted (see "Numerics").

Actions: "Emit one photon" (one photon now, in addition to the stream), "Reset the counters (new segment)" (a new
segment with the same set-up).

## Checks (computed ↔ reference)

Every check is emitted per segment (`<id><segment>`).

| id | computed by the run | reference | tolerance |
|---|---|---|---|
| `sum` | R + T + A for the source's polarization | 1 — an identity (A is defined as 1 − R − T), group "Segment N: consistency (identities)" | 1e-12 |
| `energy` (lossless) | max \|1 − R − T\| over every computed angle and wavelength, s and p (R, T from r and t separately) | 0 | 1e-10 (worst seen on random stacks: 2e-13) |
| `passive` (absorbing) | min A over all computed points | ≥ 0 | −1e-12 |
| `joule` (absorbing) | R_s + T_s + A_J, A_J = k₀/Re(n₀ cos θ₀) Σ Im(n_j²)∫\|E\|²dz from the run's field (Poynting's theorem) | 1 | 1e-12: composite 16-point Gauss–Legendre, sub-intervals ≤ 4/max(2\|Im k_z\|, 2\|Re k_z\|) (remainder < 1e-25); the rest is float rounding, ≤ 1.5e-14 over 3000 random absorbing films in the ranges (before 2026-10-23: Simpson with 2001 points, +2.9e-8 for a 1.2 nm skin depth, V5-3) |
| `brew`, `brewR` (one boundary) | zero of r_p; R_p there | arctan(n_out/n₀); 0 | 1e-9; R_p < 1e-24 |
| `crit` | boundary of T = 0 of the bare boundary n_in → n_out | arcsin(n_s/n₀) | 1e-9 |
| `tir`, `tirnow` (lossless) | max \|1 − R\| at 60 angles from θ_c to 89.9°; R at the current θ > θ_c | 0; 1 | 1e-12 |
| `evan` (bare face beyond θ_c) | amplitude decay length from \|E\|² at the face and at a depth z (first z = λ/4, then z = the length so found, so that ln(I(0)/I(z)) ≈ 2) | λ/(2π√q), q = n₀² sin²θ − n_s² in 160-bit arithmetic (one rounding) | (4.5K + 9 + 15/ln)·2⁻⁵³, K = n₀² sin²θ/q (derivation below); shown for information where this exceeds 1e-2 |
| `ar` | R(λ₀, 0°) of the quarter-wave layer | ((n₀n_s − n_f²)/(n₀n_s + n_f²))², 0 for n_f = √(n₀n_s) | 1e-12 absolute |
| `bragg` | R(λ₀, 0°) of (H L)^N | ((n₀n_L^{2N} − n_s n_H^{2N})/(n₀n_L^{2N} + n_s n_H^{2N}))² | 1e-10 |
| `film` (one layer) | r, t | Airy sum of multiple reflections with complex Fresnel coefficients, with the engine's Snell cosines and layer phase | the sum of the two routes' first-order rounding bounds (`single_film` err_r/err_t ∝ 1/\|D\|, D = 1 + r₀₁r₁₂e^{2iβ}; `stack_error_single_layer`); where it exceeds 1e-9 (near grazing in the layer) or at exact grazing (0/0) also compared at θ ∓ 1e-3 rad |
| `airy`, `airymax` (Fabry–Pérot) | T at (λ, θ); max over the spectrum | T_max/(1 + F sin²(Δ/2)), F = 4ρ/(1−ρ)², ρ = √(R₁₀R₁₂), Δ = 4πn d cosθ/λ + arg r₁₀ + arg r₁₂ (= 1/(1 + F sin²(δ/2)) for n₀ = n_s), evaluated with the engine's cosines and phase | the sum of the two routes' first-order rounding bounds (airy err_T ∝ 1/(1 − ρ), F → ∞ just below grazing in the film; matrices err_T), per point; where it exceeds 1e-9 also compared at θ − 1e-3 rad (before 2026-10-23: own asin/cos of the film angle, 1e-10, failed by up to 0.1 just below grazing) |
| `ftir` (prism + gap beyond θ_c) | T | 1/(1 + ((a² + b²)/(2ab))² sinh²(κd)); s: a = k_z, b = κ; p: a = k_z/n₀², b = κ/n_s² | 1e-9 |
| `stat` | counts of all three outcomes (R, T, A) in the segment | the Born probabilities of the segment: exact two-sided binomial tail of each outcome with 0 < p < 1, Bonferroni over the outcomes; an outcome with p = 0 that occurred has p-value 0; z of each and Pearson's χ² in the note | fails below p = 5.7e-7 (the two-sided 5σ tail); before 2026-10-23 only R was tested, so a swap of T and A passed (V5-4) |

**The Bragg closed form depends on the order of the layers.** With the order used here (incidence medium, H, L, …, H,
L, substrate) the admittance of the stack is Y = n_s (n_H/n_L)^{2N}, hence the form in the table. The often-quoted
form ((n₀n_H^{2N} − n_s n_L^{2N})/(n₀n_H^{2N} + n_s n_L^{2N}))² belongs to the opposite order, L next to the incidence
medium; both are verified against the transfer matrices in `lfphys/tests/test_thin_films.py`.

## Messages

* `segment` (accumulative): the set-up (`setup`: structure, layers with complex index and thickness, λ, θ,
  polarization, flight times), `angles` (θ per layer, exit θ or null), `cur` (R, T, A for s, p and the source),
  `expected` (Born probabilities), `theta_B`, `min_rp`, `theta_c`, `theta_c_face`, `approx`; blobs: `th`, `Rs`, `Ts`,
  `As`, `Rp`, `Tp`, `Ap`, `Rc`, `Tc`, `Ac` (angle curves), `lam`, `lR*`, `lT*`, `lA*` (spectrum), `z`, `E2` (field).
* `clicks` (accumulative): the exact counts of the step per segment and outcome, `by_seg = [[seg, n_R, n_T, n_A], …]`
  (seg −1: transitional photons), and the last ≤256 individual detections of the step (`t`, `det` 0/1/2 = R/T/A,
  `pol`, `seg`, `te`) for the view's flashes.
* `frame` (droppable): counts of the current segment, expectation, binomial σ, z of the reflected fraction, totals;
  blob `fl` (n × 6): stage, polarization, progress to the structure or to the reflection detector, weight of the
  reflected packet, progress to the transmission detector, weight of the transmitted packet.

## Approximations

* Plane waves, infinite plane boundaries; homogeneous, isotropic, linear media **without dispersion**: every index is
  one number (complex for absorption) for all wavelengths. The material-like values of the presets ("as MgF₂",
  "as TiO₂/SiO₂", "as gold at 633 nm") are illustrative, not tabulated dispersion data.
* Single photons by the Born rule with the computed R, T, A (the plane-wave powers are the probabilities of the three
  ports). An unpolarized source is the 50/50 proper mixture of s and p photons; an isotropic planar structure does not
  mix s and p, so every outcome probability equals that of ρ = I/2.
* Flight at c/n along the arms (no dispersion: phase and group velocities are equal); the time inside the structure
  (micrometres) is neglected; detectors are ideal (efficiency 1, no dark counts).
* The beams in the drawing are geometrical rays (Snell's law, `ray_optics.snell`, with the real part of the index in an
  absorbing layer); the structure is drawn to scale in depth, the 0.30 m arms are not. The beams' brightness is the
  run's R and T.
* \|E\|² is shown for s polarization only (`field_profile` computes s only); for a p or unpolarized source the panel
  says so.

## Numerics

* `interfaces.stack` multiplies the layers' characteristic (Abelès) matrices, written without dividing by the tilted
  admittance (a sinc form). A wave grazing inside a lossless layer (n₀ sin θ = n_j: the gap of the prism set-up at the
  face's critical angle, a low-index layer seen from a denser incidence medium) is therefore a regular point, and the
  angle curves sample those angles exactly. (The first version multiplied interface matrices (1/t_j)[[1, r_j],
  [r_j, 1]], which divide by t_j = 0 there; the run had to refuse such angles. Replaced in the engine on 2026-10-23.)
* The spectrum grid is capped at 1600 points; a very thick stack can then be under-resolved at short wavelengths, and
  the run says so in the approximations.
* **Checks near the critical and grazing angles (review 2026-10-23, V5-2).** There the numbers are ill-conditioned
  for any binary64 evaluation, and a fixed tolerance fails on angles one can type (θ_c + 1e-7°, 41.8103149°). The
  tolerances are therefore first-order rounding bounds, computed for the case at hand:
  * `evan`: the engine's cos θ_t = √(1 − x²), x = n₀ sin θ/n_s, carries 9u in x² (sin ≤ 1 ulp, ×n₀, /n_s, the
    square), i.e. 9uK in 1 − x² (the subtraction is exact near x = 1), K = n₀² sin²θ/q; the root halves it, and
    2π, n_s, the product and λ add ≤ 5u: the decay constant to (4.5K + 5)u. Each \|E\|² value carries ≤ (11 + ln)u,
    their ratio and logarithm 1u each: ln to (15 + ln)u absolutely; the division and the reference (q in 160-bit
    arithmetic, `thin_films.evanescent_q`) add 3u. Tolerance (4.5K + 9 + 15/ln)u, u = 2⁻⁵³. Over 3100 random
    set-ups at θ_c + 10^(−14…1)° (random n₀, n_s, λ) the largest |rel|/tol was 0.53. Where the bound exceeds 1e-2 (within ~1e-12° of θ_c)
    the angle fixes the decay length only to ~K u and the line is shown for information (`info`); at θ = θ_c as
    asin gives it the run's decay constant is exactly 0 (a grazing exit wave): before the fix this raised
    ZeroDivisionError inside `set` (V5-1).
  * `film`: the Airy sum is a ratio N/D, D = 1 + r₀₁r₁₂e^{2iβ} → 0 when the wave grazes inside the layer, so its
    rounding grows as 1/\|D\|; and the two routes used to compute the Snell cosines with different float formulas,
    which shifts β = 2πn₁d cos θ₁/λ by ~(2πn₁d/λ)u/\|cos θ₁\| near grazing (2.4e-12 for a 20 µm film at n₀ = 4,
    1.4e-7 near an exit critical angle). Both routes now use the engine's cosines and layer phase, and the tolerance
    is the sum of the two first-order bounds (`thin_films.single_film` err_r, err_t: each Fresnel coefficient ≤ 6u
    times the condition number of its denominator, e^{2iβ} ≤ 2u, then N and D divided by \|D\|;
    `thin_films.stack_error_single_layer`: entries of the scaled characteristic matrix ≤ 8u, B and C ≤ 12u of their
    terms, then the denominator). Over 120 000 random comparisons the largest ratio was 0.25.
  * `airy`, `airymax`: the same construction for the intensity formula, written as T = T₀₁T₁₂/((1 − ρ)² + 4ρ sin²(Δ/2))
    (a sum of two non-negative terms; sin²(Δ/2) is sin²β or cos²β exactly, the Fresnel coefficients being real).

## Presets

Brewster angle of glass n = 1.5 in air (unpolarized: only s photons reflect); total internal reflection glass → air
at 60°; frustrated total reflection through a 200 nm gap; antireflection layer n_f = 1.38 (as MgF₂) and the ideal
n_f = √1.5; Bragg mirror (H L)×8, n_H = 2.3, n_L = 1.45 on glass 1.52; Fabry–Pérot film n = 2.3, 2 µm in air; metal
film 30 nm, n = 0.2 + 3.3i, on glass; Kretschmann surface-plasmon dip (prism 1.5, the same metal 50 nm, air, p, at the
run's minimum of R_p, 44.58°). All material values illustrative.

## Sources

Born & Wolf, *Principles of Optics*, §1.5 (Fresnel formulae), §1.6 (stratified media), §7.6 (multiple-beam
interference, Airy formulae); Byrnes, arXiv:1603.02720 (transfer-matrix formulation used by the engine); Macleod,
*Thin-Film Optical Filters* (quarter-wave layers and stacks).

## Tests

`tests/test_v05_optics.py` (Docker, see `../README.md`): every preset runs without errors and without a failed check;
the exact critical angle and 60 angles a few ulp around it are accepted with no failed check (V5-1/V5-2); a change
that fails inside (an injected exception after the new segment was built) leaves the world, the counters and the
random generator exactly as they were and emits only the refusal and the live values in force (V5-1); the `evan`
tolerance follows the condition number; the `film` check at 41.8103149°, θ_c ± 1e-9° and a 20 µm film near grazing;
the `joule` check for a 1.2 nm skin depth (V5-3); a swap of the T and A expectations fails the `stat` check (V5-4);
the critical angle of a structure whose T underflows; the Airy checks just below grazing in the film;
the Brewster, total-reflection, evanescent, antireflection, Bragg, Airy, tunnelling and Joule checks; a live change
applies at once (a new segment with its own expectation and checks), a refused change leaves the world unchanged, a
grazing angle inside the gap is accepted and conserves energy; path changes lose photons, source changes make them transitional; photon counts agree with
R, T, A within 5σ for four structures; detections are revealed in the step in which they happen, after exactly the
flight time; a frame shows both packets with the same weights for every outcome until a detector decides.

Open items of this visualization go to `../../STATUS.md`, section "V. Visualizations — open items".
