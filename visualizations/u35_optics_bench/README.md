# u35 — Optical bench: boundaries, coatings, polarisation

**English** | [Русский](README.ru.md)

Single photons, one by one, on a planar structure between an incidence medium and an exit medium of real materials: a
single boundary of a SCHOTT glass, a quarter-wave antireflection layer of MgF₂, a Bragg mirror of Ta₂O₅ and SiO₂ films,
a Fabry–Pérot film, a metal film (gold, silver, aluminium), or the face of a prism (total internal reflection; with a
second prism behind a gap, frustrated total reflection). Every medium other than air is a glass block, a half-cylinder
(D-shaped, radius 25 mm) whose flat face is the structure's: a beam crosses it along a radius, leaves it through its
curved face at normal incidence (a Fresnel loss of about 4 %) and is absorbed on the way by the glass's κ; the
transmission detector can also count the incident photons with the block lifted off (the reference count N₀). An
analyser (a polarising beam splitter with a detector on each port) may stand before either detector; the detectors are
real single-photon detectors (efficiency, dark counts, dead time, jitter). Owner guide: `../README.md`; rules:
`../RULES.md`.

The visualization is a wrapper over the engine `lfphys` (`../../lfphys/LAYERS.md`): every physical number comes from
the engine; this folder holds orchestration (the set-up, the photon time line, the detectors' counting, the checks), the
screens and drawing.

| engine module | layer | used for |
|---|---|---|
| `core.optics.interfaces` | core | `stack`: r, t, R, T, A of every structure (transfer matrices); `field_intensity`, `field_profile`: \|E\|² of the source's light (s, p or any density matrix); `group_delay`: the structure's delays of reflection and transmission with each material's dispersion; `brewster`, `critical`: closed-form references |
| `core.optics.polarization` | core | the reflection and transmission Jones matrices of the structure, each beam's density matrix and ellipse, the analysers' ports (`beam_splitter` with k₁, k₂), the Born probabilities of a photon's five outcomes; closed forms for the checks (`malus`, `degree_from_powers`, `tir_phase_closed_form`) |
| `core.optics.materials` | core (data) | the complex index n + iκ and dn/dλ of N-BK7, N-F2, N-SF11 (SCHOTT), fused silica (Malitson), MgF₂ (Dodge; the film of Rodríguez-de Marcos et al.), the SiO₂ and Ta₂O₅ films (Gao et al.), gold and silver (Johnson and Christy), aluminium (Rakić); the glasses' κ gives the blocks' internal transmittance exp(−4πκL/λ) |
| `core.optics.thin_films` | core | closed forms for the checks (tested in `lfphys/tests/test_thin_films.py`), the Joule absorption for s and p |
| `theories.models.photodetector` | theories (device model) | the detectors: `DEVICES["spcm_aqrh_14_650nm"]` (Excelitas SPCM-AQRH-14, the data sheet's values), the non-paralysable dead time, `observed_rate` for the checks |
| `core.constants` | core | the speed of light c (flight times) |
| `theories.approx.ray_optics` | theories (approximation) | `snell`: ray directions for the drawing only |

## The screens: "Watch", "Boundary", "Coatings", "Polarisation" and "Lab work"

The demonstration opens as one page with five tabs (`run.html?demo=u35_optics_bench&screen=…`; EX2 design
`../../lfphys/sources/explore_EX2_2026-11-18_design.md` §3). All of them show the world's own view, cleaned: the bench
(the source, the structure to scale in depth, the beams, the analysers and the detectors, each beam's polarisation
ellipse, the field \|E\|² of the source's light in a strip on its right, the counters along its bottom) and, beside it,
the curves (R(θ), T(θ) for s and p; R(λ), T(λ); an analyser's share against its angle). The quick bar, the left form
of the parameters and the actions are left out; what the screen shows is chosen under "Show": "beams", "photons in
flight", "field \|E\|²", "curves R(θ), T(θ), R(λ), T(λ)", "polarisation ellipses". The panels "Set-up of this segment",
"Photons and detectors", "Polarisation of the beams" and "Approximations" fold into "How we know this is right", in
Lab work the same as in Explore (nothing is hidden); "Set-up of this segment" also lists the glass blocks (what each
crossing lets through) and the reference count. Below 1000 px the bench with its counters is the picture at the top
and the curves fold under it ("▸ Curves R(θ), T(θ), R(λ), T(λ) and the analyser"); the readouts follow under the bench.
On a server, "▶ Compute live" opens the full player (every parameter, the quick bar, the actions) with the screen's
set-up.

| what the live player has | on the screens | in "▶ Compute live" |
|---|---|---|
| the bench (beams, photons, analysers, detectors, the structure to scale, \|E\|²) and the curves | stay; below 1000 px the bench with its counters on top, the curves folded under it | unchanged |
| quick bar: λ, θ, polarisation, structure, "▷ photon flight", "▷▷ collect statistics" | the screen's sliders; the two speeds are the screen's "normal / slow" | unchanged |
| left form: the media, the source, the structure, the devices; actions "Emit one photon", "Reset the counters (new segment)" | hidden | unchanged |
| right: "Set-up of this segment", "Photons and detectors", "Polarisation of the beams", "Approximations" | in "How we know this is right" | unchanged |

**Watch: "One photon at a time at a surface"** (recording `story`, preset "One photon at a time at N-BK7 glass: the
Watch story": N-BK7 from air at 30°, unpolarised photons, 2·10⁵ photons per second, the real detectors; 50 s at 20
frames per second). The script's speeds are placed on the computed run: the first photon is the first draw of the
world's generator, so the waiting phase (`screens.STORY_WAIT` world seconds per played second) ends one frame step
before it leaves the source at 1.45 played s (the waiting factor ×3.6·10⁵, ×1.4·10⁶ «slow»); the flight is then shown
at 8.34·10⁻¹⁰ world s per played s (an arm of 0.30 m in 1.2 s); from 9 s, 2 000 photons per played second. The view
keeps one scale for the whole recording (the bench does not move) and leaves a band of 150 px under the pictures for
the caption on a wide screen, so no caption covers the bench, the curves or the counters. The captions (◀◀ / ▶▶ and the
ticks on the timeline), each no later than what it describes (`tests/test_u35_screens.py` measures them on the
recording):

| at, s | what changes | caption (summary) |
|---|---|---|
| 0 (held 3 s) | — | photons one at a time on N-BK7 (n = 1.515) at 30°; past the surface each photon's wave goes both ways |
| 3.5 | the first photon reaches the surface at 2.7 s, its transmission detector clicks at 3.9 s | one detector clicks; which one is random; a real detector misses about a third of the photons |
| 9 | speed 0.01 | thousands of photons; the surface reflects 4.35 %, the transmitted ones lose another 4.8 % in the glass block, so of the photons that reach a detector the shares settle at the computed 4.56 % and 95.44 % within the counts' errors |
| 17 | θ = 56.574° (Brewster's angle), an ideal analyser along p before the reflection detector | no reflected photon passes it; its pass detector clicks only in the dark (about once per played second) |
| 22 | the analyser along s | every reflected photon passes: at Brewster's angle reflection polarises light completely |
| 27 | from inside N-BK7 into air at 30°, the analyser out | about 5.85 % is reflected |
| 34 | θ = 45° | beyond θ_c = 41.3° no photon gets out; the detector in air clicks only in the dark |
| 41 | a second N-BK7 block 200 nm behind the face | nearly half the photons tunnel through the gap (47.1 %) |

"More recordings": `tir` (from inside N-BK7 at 60°: every photon reflected; the evanescent field and the elliptical
reflected light), `brewster` (unpolarised photons at Brewster's angle of N-BK7: the reflected beam's ellipse is a line
along s) and `spr` (Kretschmann: p photons through an N-BK7 prism on 50 nm of gold at 43.773°, where R_p is smallest,
0.38 %), each 30 s at 1·10⁻³ world s per played second, with two captions.

**Explore "Boundary"** (atlas `explore`, 456 points): the reflection bench at the He-Ne line, 632.8 nm, s or p light,
20 000 photons per set-up (0.1 s at 2·10⁵ s⁻¹), the real detectors. Controls: "Angle of incidence θ" (0, 10, 20, 30,
33, 34, …, 62, 66, 70, 80, 85°: 1° steps where the Brewster and the critical angles of the three glasses lie), "Glass
and
side" (N-BK7, N-F2 or N-SF11, light from air or from inside the glass: a compound control setting both media),
"Polarisation" (s (TE), p (TM)). The cursor is the count: a frame every 0.02 s, a fifth of the photons. Every set-up
has its reference count N₀ (the block removed, 0.1 s). Readouts: the reflected and the transmitted photons per incident
photon, (N_R/t)/(N₀/t₀) and (N_T/t)/(N₀/t₀), with their errors and the computed probabilities of reaching each detector
(from air the first is R itself); the reflected share of the clicks N_R/(N_R + N_T) with the computed share; the clicks
of all detectors.

**Explore "Coatings"** (atlas `coatings`, 91 points): λ 400–700 nm in 25 nm steps × seven real coatings on N-BK7 at
normal incidence (bare; λ/4 of MgF₂ crystal; a λ/4 MgF₂ film; Ta₂O₅/SiO₂ films (H L)×4 and ×8, quarter-wave at 550 nm
each with its own index there; aluminium and silver, 100 nm), 2 000 photons each (0.01 s). The curves show the spectrum
R(λ), T(λ) of the coating, every wavelength with its materials' own indices.

**Explore "Polarisation"** (atlas `polarisation`, 144 points): total internal reflection in N-BK7, the source linear at
45°, an ideal analyser before the reflection detector. Controls: θ (35, 40, 42, 45, 48, 51, 54, 57, 60, 65, 70, 80°)
and the analyser's angle α (0–165° in 15° steps). Below θ_c = 41.30° the reflected light is linear and the analyser
finds a zero (at 40°: 0.00009 of the light at 150°); beyond it the reflected light is elliptical (the phase difference
δ = arg r_s − arg r_p, largest at 51.17°, 46.29°, where the analyser's minimum is 0.1545): the curve "Share through the
analyser against its angle α" shows it at every angle at once, computed from the beam's density matrix.

**Lab work: the bench "Reflection and polarisation"** (design §3.4; four parts, a bench, not a test: the app judges
nothing; the fit prints its parameters, χ², ν, p and the Birge ratio). Instruments: the rotary table (1° marks, exact),
the counter's gate and its quartz clock (exact), the reflection and the transmission detectors (counts, error √N), the
reference count N₀ (the block removed, the transmission detector in line with the source; error √N) and its gate t₀
(exact), the source polariser's scale ψ and the analysers' scales α (exact), the analysers' pass- and reject-port
detectors (counts).

| part | atlas | grid | photons per set-up | columns |
|---|---|---|---|---|
| 1 "Dark counts" | `lab.dark` | counting time 0.1, 0.5, 1 s (the shutter closed) | none: 10, 50, 100 dark counts expected per detector | t, N_R, N_T, N/t |
| 2 "Fresnel's reflection" | the "Boundary" screen's (`explore`) | 456 | 20 000 | θ, t, N_R, N_T, N₀, t₀; R = N_R/(N_R + N_T); R_i = (N_R/t)/(N₀/t₀), R_d (its dark counts, 100 s⁻¹, subtracted), R_c (R_d with the dead time corrected); T_i = (N_T/t)/(N₀/t₀); x = sin²θ; y_s, y_p from R and from R_d |
| 3 "Malus's law" | `lab.malus` | α 0–180° (10°) × ψ 0, 30, 60° × analyser ideal or imperfect (k₁ 0.90, k₂ 0.009) | 20 000 | α, ψ, N_pass, N_reject, I, cos²(α − ψ), cos(α − ψ) |
| 4 "Polarisation by reflection" | `lab.reflection` | θ 40, 45, 50, 54–62, 66, 70° × α 0–90° (15°) × N-BK7, N-F2, N-SF11 | 100 000 | θ, α, t, N_pass, N_reject, N_pass + N_reject, f, P = 1 − 2f, f and P with the dark counts subtracted |

"Computed for this bench" (the drawer): the dark-count rate of the detectors; per glass n² and 1/n²
(the intercepts of y_s and y_p from R_d against sin²θ), N-BK7's θ_B = arctan n (the vertex of R_d near it), the slope
−1 of y_s, and for the
variant "N-BK7 from inside" sin²θ_c = 1/n² with θ_c = arcsin(1/n) (y_p's formula on s light from inside gives
1/n² − sin²θ, zero at θ_c); Malus's k₁, k₁ − k₂ and k₂ of each analyser; in part 4 per glass θ_B as the vertex of the
degree of polarisation P, with P = (R_s − R_p)/(R_s + R_p) computed at four of the grid's angles (40, 50, 57, 70°).
The task sheet follows Carnegie Mellon's 33-353
Lab 1 and the Rutgers handout (part 2, with its reference power I₀ measured before the sample is placed; the
semicircular sample is that handout's too) and Toronto's PHY293/PHY294 "Polarization of Light" (parts 3 and 4), quoted
verbatim; the teacher's variants:
N-F2 glass, N-SF11 glass, N-BK7 from inside (the critical angle), Malus's law with the imperfect analyser at ψ = 60°.

The ways the bench can be used, right and wrong, each with its outcome on the built atlas (seed 1) and its computed
reason, are listed in the design (§3.4; their outcomes on the built atlas in §3.10); `tests/test_u35_screens.py`
reproduces every one of them from the atlas's own points and compares it with the same processing of the expected counts
(the computed probabilities, the source's rate, the detector's η, dark rate and dead time): the reason is computed, not
asserted. Seeds 2–4 give every way the same status. What the glass block and the real detectors decide in part 2:

* R = N_R/(N_R + N_T) is a **wrong** way: the transmitted photons lose 4.8 % in an N-BK7 block (its curved face 4.2 %,
  25 mm of glass 0.6 %; N-F2 6.4 %, N-SF11 9.6 %), and the ratio takes the loss for reflected light. n² from y_s comes
  out 3.5 errors too high for N-BK7 (seed 1: 2.3586 ± 0.018 against n² = 2.2955), 4.7 for N-F2, 7.1 for N-SF11 (the
  expected counts' numbers); 1/n² from y_p 2.8 errors too low.
* R = (N_R/t)/(N₀/t₀), the reflected photons per incident photon against the reference count, is R itself for light
  from air (the reflected beam never enters the glass). With the dark counts left in (R_i) R is high (by about ten
  dark counts per detector in a set-up's 0.1 s: 7.4·10⁻⁴ at θ = 0, n² from y_s about one error high); with them
  subtracted (R_d) the index is right (seed 1: 2.3046 ± 0.019, n = 1.5181; 1/n² 0.43338 ± 0.0046). Without the
  dead-time correction R is 0.27 % high (the reference
  detector counts 1.3·10⁵ per second).
* From air, R + T per incident photon is 0.952, not 1: the block's loss, visible on the bench.
* From inside, the incident and the reflected beams each cross the block (their curved face and 25 mm of glass), so R
  against the reference is short by (T_c τ)² = 0.907, the level the reflected count reaches in total reflection. y_p's
  formula on s light from inside below θ_c then misses 1/n² by about six errors; divided by that plateau, it gives the
  index (seed 1: 0.43533 ± 0.0040 against 1/n² = 0.43564).
* In part 4 the analyser's pass port counts its dark counts: the degree of polarisation reaches 1 near θ_B only with
  them
  subtracted (0.976–0.986 without).

**Every set-up has its own random sample.** The world's generator is seeded by the screen's seed and the set-up's
parameters together (`engine/bench.py rng_for`): with the seed alone every point of a grid drew the same random numbers,
so the fluctuations of neighbouring set-ups moved together and a fit across them showed χ²/ν ≈ 0.2 and a shared bias.

## The causal chain of one photon (all computed in the run)

0. **The reference count** (a set-up with t₀ > 0: the reflection bench): before the world's time 0 the block is lifted
   off the table and the transmission detector, in line with the source and with the analysers out of the beam, counts
   the source's photons for t₀ (Poisson emission, the detector's efficiency, dark counts and dead time, from a random
   stream of its own): N₀, read at every frame. A later change of the source, the detector or t₀ voids it (a notice).
1. **Emission** at a time of a Poisson stream (rate: a live parameter; the shutter closed emits nothing), with a
   wavelength drawn from the source's line (a Gaussian of full width Δλ, 0.002 nm for a He-Ne laser, sampled by 33
   wavelengths over ±4σ) and the source's polarisation state: linear at ψ (s: 90°, p: 0°) or unpolarised, the density
   matrix ρ = I/2. An unpolarised photon carries no s or p label (drawn grey): labelling it would be one decomposition
   of
   ρ, not something the run measures.
2. **Flight to the structure** along the incident arm (0.30 m) at the group velocity c/n_g: in air, or, from inside a
   glass, through the block's curved face at normal incidence and 25 mm of glass along its radius (the rest in air).
3. **At the structure**, with the structure present at the moment of arrival: the run has computed, for the photon's own
   wavelength (every material's index at that wavelength), the reflection and transmission Jones matrices of the
   structure (`polarization.boundary_matrices`), the arms' density matrices ρ_R = M_R ρ M_R†, ρ_T = M_T ρ M_T†, and the
   Born probabilities of five outcomes: reflected and passed or rejected by the reflection arm's analyser, transmitted
   and passed or rejected by the transmission arm's analyser, absorbed (an arm without an analyser has one detector: its
   whole probability is "passed"), each times the share of the photons that cross the blocks (on the way in and in the
   photon's arm: the curved face's Fresnel transmission at normal incidence, s and p alike, and the glass's
   exp(−4πκL/λ) at the photon's own wavelength), and the three losses in the blocks (on the way in, in the reflection
   arm, in the transmission arm). The outcome is drawn from these eight. An absorbed photon is revealed here; a photon
   lost in a block is never seen (it leaves the flight when both arms' arrival times have passed).
4. **Flight to a detector**: 0.30 m, in a glass 25 mm through its block and the rest in air (with the radius 0, the
   whole
   arm in the medium), at the group velocity, plus the structure's group delay of reflection or transmission
   (`interfaces.group_delay` with each
   material's dn/dλ; femtoseconds). Until then a frame shows the photon as two packets on the two arms with weights
   P_R/(P_R + P_T) and P_T/(P_R + P_T), the same for every outcome; when one arm's arrival time has passed without a
   click, the other packet's weight is the conditional probability given that detector's efficiency η times the share
   of its arm's photons that cross its block (Bayes; for an ideal detector without a block the null result removes the
   packet).
5. **The detector**: the photon is detected with probability η; dark counts are a Poisson stream; a non-paralysable dead
   time follows every recorded count (a photon or a dark count arriving while the detector is dead is lost); each
   recorded count's time tag carries Gaussian jitter (`theories.models.photodetector`). The counters count the recorded
   clicks until the gate (if one is set).

The counters are the accumulation of these clicks; the computed fractions are the run's own probabilities, shown once
the segment has sent a photon (with the shutter closed the counters hold only dark counts, and there is nothing to
compare them with).

## What the run computes for every segment (set-up configuration)

* every material's index at the source's wavelength (the line's 33 wavelengths) and at the design wavelength λ₀ of a
  coating (`materials.index`): the glasses at the face by their real part (their κ ≤ 4·10⁻⁸ changes R and T by less
  than 10⁻¹⁵ below θ_c, by up to 2·10⁻⁷ in total reflection: the check `kface`), the films and metals complex;
* each block's crossings at every wavelength of the line: the curved face at normal incidence (`interfaces.stack`, s
  and p) and the internal transmittance exp(−4πκL/λ) of the radius L with the glass's κ;
* r, t, R, T, A for s and p (`stack`), the Jones matrices, the arms' density matrices and their polarisation ellipses
  (azimuth, ellipticity angle, degree), the five outcomes' Born probabilities at each wavelength of the line;
* R(θ), T(θ), A(θ) for s and p at the current λ: 360 angles from 0 to 89.9° plus points around the run's own critical
  and Brewster angles (not the set-up's own θ: the curves of one sample are then the same at every θ and the atlas's
  pool
  keeps them once); R(λ), T(λ), A(λ) at the current θ on a grid uniform in 1/λ over the materials' common range, every
  wavelength with its own indices; the curves of the source's state, ρ_pp R_p + ρ_ss R_s;
* with an analyser: the share of the arm's light through its pass port at every angle 0–180°, tr(A(α)†A(α) ρ)/tr ρ;
* the critical angle (bisection on the run's T of the bare boundary), the Brewster angle of a single boundary (the
  zero of
  r_p), the minimum of R_p of a multilayer (as before; see "Numerics");
* \|E(z)\|² of the source's light through the structure (`field_intensity`: ρ_pp \|E\|²_p + ρ_ss \|E\|²_s; the p field's
  E_z jumps at an interface, drawn as a jump: every interface is in the depth grid on both of its sides);
* the flight times at the group velocities and the structure's group delays;
* ray directions in every layer and in the exit medium for the drawing (`ray_optics.snell`, real part of the index).

## Live set-up (owner, 2026-10-23)

Every parameter is a live parameter (there are no law parameters: this world is accepted physics; the analysers and the
detectors are devices, group "Devices"). The parameters: the source (λ, Δλ, θ, polarisation s, p, linear at ψ or
unpolarised, rate, shutter), the media (air, N-BK7, N-F2, N-SF11, fused silica, MgF₂, or a model medium of a given
index), the structure (none, a boundary, a λ/4 layer, a Bragg mirror, a Fabry–Pérot film, a metal film, total internal
reflection; each layer of a real material or a model), the devices (an analyser out, ideal or imperfect before each
detector and its angle α; k₁, k₂ of the imperfect one; the detector: the SPCM-AQRH-14 or the ideal one, an idealisation;
the counters' gate). A change applies at once and starts a new segment:

* source (λ, Δλ, polarisation, ψ, rate, shutter): photons already emitted fly on with their own λ and state, meet the
  structure present when they arrive, and are **transitional** (counted separately, not in the new segment);
* structure, devices: photons not yet at the structure meet the new one (transitional); photons past it fly on and count
  in the segment they belong to; a detector kept keeps its dead-time state;
* media, the blocks' radius or the angle: the beam paths are rebuilt and photons under way are **lost** (counted, with a
  notice);
* the source's wavelength, line width, rate or shutter, the detector or t₀: the reference count N₀ no longer applies
  and is not shown (a notice; a new world counts a new one).

A change is refused (and the world left as it was) when a value is out of range, a wavelength (with the line's width)
or λ₀ lies outside a material's data, an analyser's k₂ exceeds its k₁, or the reference count would take more than
2·10⁷ photons (the rate × t₀). A change is atomic (review 2026-10-23, V5-1):
the new set-up, its segment and its checks are computed with the messages held back, and only a change that succeeds as
a whole is kept and emitted; if anything raises on the way, the world (parameters, structure, photons in flight,
counters, segments, the detectors' states, the random generator) is restored, nothing is emitted, and the error is
reported as a refused change. Actions: "Emit one photon", "Reset the counters (new segment)".

## Checks (computed ↔ reference)

Every check is emitted per segment (`<id><segment>`). `energy` covers every computed wavelength whose materials are all
lossless (a film's data may absorb in the ultraviolet only), `passive` the others; `ar` and `bragg` compare at λ₀ with
each material's index there (for an absorbing film shown for information).

| id | computed by the run | reference | tolerance |
|---|---|---|---|
| `sum` | R + T + A for the source's polarization | 1 — an identity (A is defined as 1 − R − T), group "Segment N: consistency (identities)": for information | — |
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
| `born` | the five outcomes' Born probabilities | sum 1 (tr ρ): an identity (the analysers' ports are complementary by construction), for information | — |
| `arms` | tr(M_R ρ M_R†), tr(M_T ρ M_T†) of the density matrices | ρ_pp R_p + ρ_ss R_s, ρ_pp T_p + ρ_ss T_s of the transfer matrices | 1e-12 |
| `joulep` (absorbing) | R_p + T_p + A_J for p light (E_x and E_z) | 1 | 1e-12 |
| `none` (no boundary) | R and T of the same medium on both sides | 0 and 1 | 1e-15 |
| `dop` (unpolarised source) | degree of polarisation of the reflected light from its density matrix | (R_s − R_p)/(R_s + R_p) (`polarization.degree_from_powers`) | 1e-10 |
| `malusR`, `malusT` (an analyser) | the pass port's share of the arm's photons, tr(A†A ρ)/tr ρ | for light without a circular part: (k₁ + k₂)/2 + (k₁ − k₂)/2 · P cos 2(α − ψ) with the beam's own ψ and degree P (`polarization.malus` for P = 1); elliptical light: for information | 1e-12 |
| `tirphase` (bare face beyond θ_c) | δ = arg r_s − arg r_p of the run | 2 arctan(cos θ √(sin²θ − n²)/sin²θ) (Stratton 1941, §9.7; `tir_phase_closed_form`) | 1e-11 rad plus the rounding of sin²θ − n² near θ_c |
| `line` | the largest change of an outcome's probability over the source's line (±4σ) | — (for information) | — |
| `cfacein`, `cfaceR`, `cfaceT` (a block on that path) | the curved face's T_s and T_p at normal incidence (`interfaces.stack`) | 4n/(n + 1)², s and p alike | 1e-14 |
| `bulkin`, `bulkR`, `bulkT` | the block's internal transmittance exp(−4πκL/λ) | — (for information, with κ's own uncertainty: for a SCHOTT glass half a unit of the printed τ_i) | — |
| `kface` (a glass face, no layers) | R with the glasses' complex index n + iκ minus the run's R | — (for information: what taking the real part leaves out) | — |
| `ghost` (a block on the transmission side) | the ghost the run does not follow: transmitted, reflected back by the curved face, by the face from inside, by the curved face again, out along the reflected beam (T τ⁴ R_c² R′ T′) | — (for information: 6.6·10⁻⁵ of the source's photons at θ = 0, 0.16 % of the reflected) | — |
| `ref` (segment 0, t₀ > 0) | the reference count N₀: photons, detected ones, dark counts, recorded counts | Poisson(rate·t₀), Binomial(photons, η), Poisson(d·t₀), m = n/(1 + n t_d) | Bonferroni over the four tails; fails below p = 5.7e-7 |
| `stat` | counts of the eight outcomes in the segment (the five at the face, through the blocks, and the three losses in the blocks) | their probabilities (line-averaged): exact two-sided binomial tail of each outcome with 0 < p < 1, Bonferroni over the outcomes; an outcome with p = 0 that occurred has p-value 0; z of each and Pearson's χ² in the note | fails below p = 5.7e-7 (the two-sided 5σ tail) |
| `det` | each detector's photons detected, dark counts and recorded clicks | Binomial(arrivals, η), Poisson(d·t), and m = n/(1 + n t_d) of the non-paralysable dead time (`photodetector.observed_rate`; σ² ≈ the counts lost) | Bonferroni over the tests; fails below p = 5.7e-7 |

**The Bragg closed form depends on the order of the layers.** With the order used here (incidence medium, H, L, …, H,
L, substrate) the admittance of the stack is Y = n_s (n_H/n_L)^{2N}, hence the form in the table. The often-quoted
form ((n₀n_H^{2N} − n_s n_L^{2N})/(n₀n_H^{2N} + n_s n_L^{2N}))² belongs to the opposite order, L next to the incidence
medium; both are verified against the transfer matrices in `lfphys/tests/test_thin_films.py`.

## Messages

* `segment` (accumulative): the set-up (`setup`: structure, layers with complex index, thickness and material, the media
  and their names, λ, Δλ, θ, the source's state, the analysers, the detector, the gate, the flight times and group
  delays, `block`: the radius and each crossing's index, curved face and internal transmittance, `ref`: the reference
  count), `angles`, `cur` (R, T, A for s, p and the source's state), `P` (the five outcomes at the face, at the line's
  centre), `P8` (the eight outcomes through the blocks, at the line's centre), `expected` (the eight, line-averaged),
  `arms` (P_R, P_T, P_A at the face), `ell` (each arm's polarisation ellipse), `theta_B`, `min_rp`,
  `theta_c`, `theta_c_face`, `approx`; blobs: `th`, `Rs`, `Ts`, `As`, `Rp`, `Tp`, `Ap`, `Rc`, `Tc`, `Ac` (angle curves),
  `lam`, `lR*`, `lT*`, `lA*` (spectrum), `z`, `E2` (field), with an analyser `ana_a`, `anaR_f`, `anaT_f`.
* `clicks` (accumulative): the exact counts of the step per segment, `by_seg = [[seg, c_Rpass, c_Rreject, c_Tpass,
  c_Treject, n_A], …]` (seg −1: transitional photons; the counts are recorded clicks, dark counts included), and the
  last 8 events of the step at each detector and at the structure (`t` the tag, `det` 0–3 the detectors, 4 an
  absorption, `pol` the photon's code, 9 a dark count) for the view's flashes.
* `event` `gate`: the counting time is over (the counters stop).
* `frame` (droppable): the counts of the current segment (`counts`), the measurables (`meas`: `t_c`, `n_R`, `n_T`,
  `n_Rp`, `n_Rr`, `n_Tp`, `n_Tr`, `n_clicks`, `n_emit`, `n_A`, `n_dark`, `n_L` (lost in the blocks), `n_0` (the
  reference count, from t = 0), `R_frac`, `T_frac`, `fR_pass`, `fT_pass` with their binomial errors `*_se` and computed
  references `*_ref`, `R_inc`, `T_inc` (per incident photon against N₀, with their Poisson errors and the computed
  probabilities of reaching each detector); every count None before the counting starts), totals;
  blob `fl` (n × 6): stage, polarisation code, progress to the structure or to the reflection detector, weight of the
  reflected packet, progress to the transmission detector, weight of the transmitted packet.

## Approximations

* Plane waves, infinite plane boundaries; homogeneous, isotropic, linear media. Real materials at each photon's
  wavelength (`materials`: the SCHOTT glasses relative to air at the wavelength in air, with air n = 1; the films and
  metals as the refractiveindex.info database gives them, the reference medium not verified in their papers: see the
  module's `info`); a model medium is one index for every λ, said so. Each dataset at its own temperature (the SCHOTT
  glasses at 20 °C; their dn/dT not applied: STATUS V53).
* The glasses at the structure's face by the real part of their index: their κ changes R and T there by less than
  10⁻¹⁵ below the critical angle and by up to 2·10⁻⁷ in total reflection (the engine accepts the complex index; the
  check `kface` shows the difference at the current angle).
* Every medium other than air is a half-cylinder (a D-shaped block, as the laboratory manuals' semicircular samples)
  of radius 25 mm, its flat face the structure's and its axis the table's, crossed along a radius: its curved face at
  normal incidence (Fresnel, s and p alike, so the beam keeps its polarisation; no total reflection there) and the
  glass's absorption exp(−4πκL/λ) (Beer–Lambert with SCHOTT's κ, which is itself known only to half a unit of the
  printed internal transmittance: ±50 % for N-BK7 at 632.8 nm). N-BK7 loses 4.2 % at the curved face and 0.6 % in the
  glass, N-F2 5.5 % and 1.0 %, N-SF11 7.9 % and 1.9 %. Not followed: the curved face's focusing (the detectors take the
  whole beam) and the light it reflects back, lost to both detectors except a ghost toward the reflection detector
  (the check `ghost`: 6.6·10⁻⁵ of the photons at θ = 0, 0.16 % of the reflected count). With the radius 0 the media are
  half-spaces and the detectors stand inside them (an idealisation).
* The reference count N₀ is made before the world's time 0 with the block lifted off and the analysers out of the
  beam, by the transmission detector (the same device model as the reflection detector: their efficiencies are equal).
* Single photons by the Born rule on their density matrix; an unpolarised source is ρ = I/2 (no s or p labels).
* An analyser is a linear partial polariser without retardance, k₁ and k₂ independent of the angle and the wavelength;
  its two ports are a lossless polarising beam splitter. The imperfect one (k₁ 0.90, k₂ 0.009) is a model device.
* The detectors: the SPCM-AQRH-14's data sheet values (η 0.65 at 650 nm, about 0.68 at 632.8 nm by the sheet's typical
  curve: the 650 nm value is used; 100 dark counts per second, the grade's maximum; 22 ns dead time; 350 ps timing
  resolution read as FWHM). Not modelled: afterpulsing (0.5 %), twilight events, the efficiency's dependence on the
  count rate, the timing response's slow tail; the data sheet's linearity table implies an effective dead time of
  28.2 ns at high rates (the benches' rates are far below).
* Flight at the group velocity along the arms; the structure's group delays for light with both s and p are the
  intensity-weighted mean of the two (they differ by femtoseconds, far below the 149 ps jitter).
* The source's line as 33 wavelengths over ±4σ (the probabilities change by less than 10⁻⁵ over a He-Ne line: the check
  `line`).
* The beams in the drawing are geometrical rays (Snell's law with the real part of the index); the structure is drawn
  to scale in depth, the 0.30 m arms are not. The beams' brightness is the run's √R and √T; with the shutter closed
  every beam is drawn faint (there is no light). A beam's polarisation ellipse is drawn as seen looking along the beam
  towards the source, p across the beam in the drawing's plane, s out of it.

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
    set-ups at θ_c + 10^(−14…1)° (random n₀, n_s, λ) the largest |rel|/tol was 0.53. Where the bound exceeds 1e-2
    (within ~1e-12° of θ_c)
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

N-BK7 at Brewster's angle from air (unpolarised: only s is reflected), the same with an analyser along p; total
internal reflection N-BK7 → air at 60°; frustrated total reflection through a 200 nm air gap to a second N-BK7 prism;
antireflection of N-BK7 by a λ/4 MgF₂ film (Rodríguez-de Marcos et al.) and by λ/4 of crystalline MgF₂ (Dodge),
λ₀ = 550 nm; a Bragg mirror (H L)×8 of Ta₂O₅ and SiO₂ films (Gao et al.) on N-BK7; a Fabry–Pérot model film n = 2.3,
2 µm, in air; a 30 nm gold film on N-BK7; the Kretschmann plasmon dip: N-BK7, 50 nm of gold (Johnson and Christy,
PCHIP),
air, p at 43.773° (R_p smallest, 0.0038; within gold's interpolation error between 0 and 0.014 at 43.71–43.84°); Malus's
law (linear light at ψ = 30° straight into an analyser); and the screens' set-ups (the story, the reflection bench, the
coatings, total reflection with an analyser, dark counts, Malus's bench, polarisation by reflection). All at the He-Ne
line, 2·10⁵ photons per second, with the SPCM-AQRH-14 detectors.

## Sources

Born & Wolf, *Principles of Optics*, §1.5 (Fresnel formulae), §1.6 (stratified media), §7.6 (multiple-beam
interference, Airy formulae); Byrnes, arXiv:1603.02720 (transfer-matrix formulation used by the engine); Macleod,
*Thin-Film Optical Filters*; Stratton, *Electromagnetic Theory* (1941), §9.6–9.7 (total reflection's phase); Shurcliff,
*Polarized Light* (1962) (the Jones and Stokes calculus, the partial polariser); the materials' sources as
`lfphys.core.optics.materials` cites them (SCHOTT data sheets; Dodge 1984; Malitson 1965; Rodríguez-de Marcos et al.
2017; Gao, Lemarchand, Lequime 2012, 2013; Johnson & Christy 1972; Rakić 1995); Excelitas, SPCM-AQRH data sheet, Rev
2023-1. The task sheet's quotations, checked verbatim in the downloaded texts (2026-11-19): Carnegie Mellon University,
33-353 Intermediate Optics, Lab 1 "FRESNEL RELATIONS and SNELL'S LAW" (2010); Rutgers, "Fresnel Equations and
Electromagnetic Boundary Conditions" (the semicircular sample and the reference power I₀ «before sample placement»);
University of Toronto, PHY293/PHY294, "Polarization of Light".

## Tests

`tests/test_u35_optics.py` (Docker, see `../README.md`): every preset runs without errors and without a failed check;
the first version's set-ups as model media with the ideal detector keep their closed-form checks (Brewster, total
reflection and its phase, the evanescent wave, antireflection, Bragg, Airy, tunnelling, Joule for s and p) and the
review history of 2026-10-23 (V5-1 … V5-4: the exact critical angle, the evanescent and film tolerances near grazing,
a one-nanometre skin depth, an atomic change that fails inside, the statistics of all outcomes); the real materials'
numbers (N-BK7's Brewster angle, the Bragg mirror's 99.37 %, the Kretschmann minimum 0.0038 at 43.773°); at Brewster's
angle an analyser along p passes no reflected photon; a real detector's silent arm weighs the other packet by Bayes;
live changes, refusals, transitional and lost photons, the actions; the glass blocks (the curved face against
4n/(n + 1)², 10 or 25 mm of glass against the SCHOTT sheet's printed τ_i at its own wavelengths, the eight outcomes and
the counts through 100 mm blocks against them, the silent detector's weight with its block, the identities shown for
information); the reference count against the detector model over 30 seeds, voided by a change of the source, refused
beyond 2·10⁷ photons. `tests/test_u35_screens.py`: every grid point of
every atlas builds with every check ✓ and stops by its rule; the linearisations against the engine's R at 1 000 random
(n, θ) and against Fresnel's formulae in 30 digits; the bench's computed values against the engine (θ_c and the
degree of polarisation included); every way of the bench on the atlas's points (`tests/u35_lab.py`: the readings, the
formula columns and `linear_fit` as Lab work makes them), each against the same processing of the expected counts
(`expected_row`); every select control names its values in every language; the story's captions against the
recording; the materials and the detectors' closed forms.
`tests/u35_screens.mjs` (a browser, EN and RU, 1280 × 800, 390 × 844, 390 × 700): no caption covers what the view drew;
one scale for the story; every label inside its canvas at the grids' corners; the phone's readouts under the view and
the curves' fold; at 390 px the view, the step's control, «Measure» and the time bar on the screen together; the five
tabs fit; no horizontal scroll, no page error.

Open items of this visualization go to `../../STATUS.md`, section "V. Visualizations — open items".
