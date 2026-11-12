# lfphys source verification — plan item P15.3, the quantum scene (2026-11-03)

Purpose: every formula and number that `core.quantum.scene` takes from a source, quoted from texts fetched on
2026-11-03 (arXiv PDFs converted with `pdftotext -layout`; NIST and DLMF pages as HTML, text extracted; the Crossref
metadata API without any contact parameter; all requests with a neutral user agent and no personal identifier).
Converted equations are partly garbled; each is given as quoted fragments plus the reading used, and each reading is
checked by a test of `tests/test_quantum_scene.py` against an independent route.
Status codes as in `verification_2026-10-23.md`: VERIFIED / NOT FOUND / DIFFERS; DERIVED (not quoted: derived for the
engine, with the check that confirms it).

Sources:

* [JS] K. Jacobs, D. A. Steck, "A straightforward introduction to continuous quantum measurement", Contemp. Phys. 47,
  279 (2006) (journal reference from the arXiv API); text arXiv:quant-ph/0611067v1, https://arxiv.org/pdf/quant-ph/0611067.
* [B] A. Bassi, K. Lochan, S. Satin, T. P. Singh, H. Ulbricht, "Models of wave-function collapse, underlying
  theories, and experimental tests", Rev. Mod. Phys. 85, 471 (2013); text arXiv:1204.4325v3.
* [CDM] Y. Castin, J. Dalibard, K. Mølmer, "A wave function approach to dissipative processes", AIP Conf. Proc. 275,
  143 (1993); text arXiv:0805.4002v1 (the method of Dalibard, Castin & Mølmer, PRL 68, 580 (1992)).
* [PK] M. B. Plenio, P. L. Knight, "The quantum-jump approach to dissipative dynamics in quantum optics", Rev. Mod.
  Phys. 70, 101 (1998); text arXiv:quant-ph/9702007v1.
* [PDAC] I. L. Paiva, P. R. Dieguez, R. M. Angelo, E. Cohen, "Coherence and realism in the Aharonov-Bohm effect";
  Phys. Rev. A 107, 032213 (2023) (journal reference from the arXiv API); text arXiv:2209.00480v2 (for the two-path phase of Aharonov & Bohm, Phys. Rev. 115, 485 (1959), whose text is not
  open).
* [PCM] J. Planelles, J. I. Climente, J. L. Movilla, "Aharonov-Bohm effect for pedestrian"; text
  arXiv:cond-mat/0506691v1 (2005; authors checked against the text and the arXiv API) — the flux unit.
* [NIST] CODATA 2022 values, https://physics.nist.gov/cgi-bin/cuu/Value?muem, ?munn, ?gem, ?gamman (fetched
  2026-11-03); the same values are those of `scipy.constants` 1.17.1 in the image lfphys-viz.
* [DLMF] NIST Digital Library of Mathematical Functions, release 1.2.8 (2026-09-15): §2.10(i) eq. 2.10.1,
  https://dlmf.nist.gov/2.10; §7.2(i) eq. 7.2.2, https://dlmf.nist.gov/7.2; §6.2(i) eq. 6.2.1, https://dlmf.nist.gov/6.2.
* [Ma] P. Massart, "The tight constant in the Dvoretzky-Kiefer-Wolfowitz inequality", Ann. Probab. 18, 1269 (1990):
  the abstract, from https://api.crossref.org/works/10.1214/aop/1176990746.

---

## 1. The Gaussian position measurement (`Scene.kraus`, `Scene.measure`) — VERIFIED

[JS] eq. (22): "A(α) = (4k∆t/π)^{1/4} ∫_{−∞}^{∞} e^{−2k∆t(x−α)²} |x⟩⟨x| dx" ("Each operator A(α) a Gaussian-weighted
sum of projectors onto the eigenstates of X. Here α is a continuous index, so that there is a continuum of
measurement results labeled by α"); eq. (24): "P(α) = Tr[A(α)† A(α)|ψ⟩⟨ψ|] = sqrt(4k∆t/π) ∫ |ψ(x)|² e^{−4k∆t(x−α)²} dx";
the post-measurement state of a general measurement, eq. (21) and before it: "After making the measurement and
obtaining the result m, the state of the system is ρf = Ω_m ρ Ω_m† / Tr[Ω_m ρ Ω_m†]"; eq. (19): the probability of a
range of results is "Tr[Σ Ω_m† Ω_m ρ]" ("positive operator-valued measure").

Reading used: with 2k∆t = 1/(4 s²), A(x) = (2π s²)^{−1/4} exp(−(r − x)²/(4 s²)) per axis, so P(x) = |ψ|² convolved
with N(0, s²) and ∫ A(x)† A(x) dx = 1. Checked: completeness by quadrature (< 1e-9), the outcomes against
N(c, s0² + s²) (Kolmogorov–Smirnov within the DKW bound, §6), the post-measurement spread (1/s0² + 1/s²)^{−1/2} and
centre (< 1e-9); a Kraus operator with exp(−(r − x)²/(2 s²)) fails both (negative control).

DERIVED: on the grid P(x) = Σ_i ρ_i dV G_s(x − r_i) is the trapezoidal rule of the convolution; by Poisson summation
its relative error for a band-limited density is of the order exp(−2π² s²/d²) (2.7e-9 at s = d), hence the
requirement s ≥ max d; sampling i with probability ρ_i dV / N and adding s ξ, ξ ~ N(0, I), draws exactly from it.
DERIVED (review B6-Q4): K_x multiplies ψ by exp(−|r − x|²/(4s²)), whose power spectrum is exp(−2 s² k²): the wave's
spectral variance grows by 1/(4s²) per axis (exact for a Gaussian packet: the post-measurement width
(1/s0² + 1/s²)^{−1/2} above is the same statement), so s must keep the widened wave within the grid's band
(`Scene.measure_min_sigma`, §8 (b)).

## 2. Localization by an environment: the GRW-form Lindblad family (`Localization`) — VERIFIED

[B] eq. (17): "Ln(x) = 1/(π r_C²)^{3/4} e^{−(qn − x)²/2r_C²}, where rC is a new parameter of the model which sets the
width of the localization process"; eq. (18): "pn(x) ≡ ‖Ln(x)ψt(x1, x2, . . . xN)‖²" ("The probability density for a
jump taking place at the position x"); "the jumps are distributed in time like a Poissonian process with frequency
λGRW"; eq. (22): "⟨x|T[ρ(t)]|y⟩ = λGRW [1 − e^{−(x−y)²/4r_C²}]⟨x|ρ(t)|y⟩" ("the effect of the spontaneous collapse is
to suppress the off-diagonal elements of the density matrix").

Reading used: L_y = sqrt(λ) (π a²)^{−d/4} exp(−|r − y|²/(2 a²)) with a = r_C (d = 3 in [B]; the normalisation
(π a²)^{−d/4} makes ∫ L_y² dy = λ in d dimensions); the coherence factor exp(−|r − r'|²/(4 a²)). The scene uses this
form for an environment (scattering decoherence has the same form, `core.quantum.decoherence`), not as a collapse
model. DERIVED: with a region χ(y), K(r, r') = ∫ χ(y) L_y(r) L_y(r') dy/λ = exp(−|r − r'|²/(4a²)) χ̃((r + r')/2) and
Γ(r) = λ χ̃(r), χ̃ = χ blurred by N(0, a²/2) (for the erf box: ε_tot² = ε² + a²), by completing the square in y.
Checked: 800 jump trajectories against the master equation with this dissipator integrated directly (DOP853), 8
z-scores below 5 everywhere and in a region (max 2.2); a reference with 0.7 λ is rejected (max |z| 9.9).

## 3. Quantum jumps (`Scene._step`, `_count`, `_jump`) — VERIFIED; the waiting-time form DERIVED

[CDM] eq. (4): "H = HS − (iħ/2) Σm Cm† Cm"; eq. (8): "δpm = δt ⟨φ(t)|Cm† Cm|φ(t)⟩ ≥ 0"; eq. (10): "with a probability
δpm |φ(t + δt)⟩ = Cm|φ(t)⟩ / ‖Cm|φ(t)⟩‖"; eq. (11): "In the no-jump case, which occurs then with a probability 1 − δp,
we take as new normalized wave function at time t + δt: |φ(1)(t + δt)⟩ / ‖|φ(1)(t + δt)⟩‖".

[PK] eq. (66): "|ψA(0)(t)⟩ = e^{−i Heff t/ħ}|ψA(0)⟩"; "In fact the square of the norm of Eq. (66) is just the delay
function", eq. (67): "P0(t) = ⟨ψA(0)(t)|ψA(0)(t)⟩"; eq. (30): "I1(τ) ≡ −dP0/dτ" ("the delay function describing the
distribution of delay times before the next emission occurs").

DERIVED for the scene: (a) the family {L_y} is a continuum of channels, the jump position drawn from ‖L_y ψ‖² as in
[B] eq. (18), which for a Gaussian L_y is |ψ|² convolved with N(0, a²/2) (sampled exactly as r_i + (a/√2) ξ, times
χ(y) by rejection). (b) The detectors' absorbing potential is part of the no-jump evolution but not of the jump
clock: the loss of each step is split per point in proportion W_k : Γ/2, the norm is restored for the Γ part (so
norm + absorbed = 1 keeps its meaning), and the jump hazard of the step is ln((n0 − ΔA)/n1). (c) Jumps are counted as
the thresholds E_1, E_1 + E_2, … (E_i ~ Exp(1)) crossed by the integrated hazard (a Poisson process in the hazard:
Poisson(λ dt) per step for a uniform rate) and placed at the step's midpoint (the midpoint rule of the Dyson term
∫ N(dt − s) J N(s) ds: second order). Checked as in §2 and: the number of jumps per trajectory 1.619 against λT =
1.571 (z = 1.1, M = 800).

## 4. The Aharonov–Bohm phase and the flux unit (`FluxTube`, the AB test) — VERIFIED

[PDAC] p. 1: "The phenomenon is typically discussed in terms of a charge q traveling an interferometer with an ideal
infinitely long and thin solenoid with an associated magnetic flux ΦB at its center. In this case, the charge’s state
acquires an extra relative phase φAB = qΦB/ħ after encircling the interferometer. This effect was experimentally
verified multiple times [3–6], including the noteworthy experiment by Tonomura et al. in which the magnetic field
source was shielded by a superconductor [7]."
[PCM] p. 1: "Φ = πa²B is the magnetic flux and Φ0 = 2πħ/|e| the flux unit."

Reading used: in the scene's units (ħ = 1, charge in e, field in ħ/(e L²)) the flux quantum is 2π and the phase
difference of two paths enclosing Φ is q Φ. DERIVED: the far-field minima of a symmetric double slit then move by
δk = q Φ/(ħ D); the shift's relative error to first order equals the relative offset of the minima from (2n+1)π/D
(the slits' odd phase asymmetry, linear in k). Checked: −0.50249 and −0.25129 against −0.5, −0.25 (offset 0.0051);
measured in the gauge where A = 0 in the transmitted half-plane (the canonical momentum of the tube's symmetric gauge
gives −0.4767: a negative control).

## 5. Constants of the species (`species`) — VERIFIED

[NIST] (CODATA 2022): "electron magnetic moment Numerical value -9.284 764 6917 x 10 -24 J T -1"; "neutron magnetic
moment Numerical value -9.662 3653 x 10 -27 J T -1"; "electron g factor Numerical value -2.002 319 304 360 92";
"neutron gyromagnetic ratio Numerical value 1.832 471 74 x 10 8 s -1 T -1". `scipy.constants.physical_constants`
1.17.1 holds the same values (printed in the image on 2026-11-03: −9.2847646917e-24, −9.6623653e-27,
−2.00231930436092). Reading used: the spin Hamiltonian −μ B·σ with the signed moment μ (both negative: the moments are
antiparallel to the spins). Checked: 2|μ_n|/ħ = γ_n to 1e-8; −μ_e B equals `schrodinger_nd.pauli_coupling` with
|g_e| to 1e-9; the Larmor precession <σ_z> = cos(2bt), <σ_y> = −sin(2bt), b = −μB, to 1e-12.

## 6. Numerical formulas (DLMF, Massart) — VERIFIED

[DLMF] 2.10.1 (Euler–Maclaurin): "∑_{j=a}^{n} f(j) = ∫_a^n f(x) dx + ½ f(a) + ½ f(n) + ∑_{s=1}^{m−1} B_{2s}/(2s)!
(f^{(2s−1)}(n) − f^{(2s−1)}(a)) + ∫_a^n (B_{2m} − B̃_{2m}(x))/(2m)! f^{(2m)}(x) dx" ("This is the Euler–Maclaurin
formula"). Reading used: with B₂/2! = 1/12 and step d, ∫_{x0}^{∞} ρ = trapezoid + (d²/12) ∂ρ(x0) + O(d⁴) when ρ and
its derivatives vanish at the far end (the probability beyond a flux plane).
[DLMF] 7.2.2: "erfc z = 2/√π ∫_z^∞ e^{−t²} dt"; 6.2.1: "E₁(z) = ∫_z^∞ e^{−t}/t dt". Reading used: the edge profile
S(u) = erfc(−u/ε)/2 and its spectrum; the aliasing bound of the edge test, (2/π)∫_{k_N}^∞ e^{−k²ε²/4}/k dk =
E₁(k_N²ε²/4)/π per unit step (substitution u = k²ε²/4).
[Ma] abstract: "In particular, the two-sided inequality P(√n sup_x |F̂n(x) − F(x)| > λ) ≤ 2 exp(−2λ²) holds without any
restriction on λ." Reading used: the Kolmogorov–Smirnov acceptance bound sqrt(ln(2/α)/(2M)) of the measurement test.

## 7. Derived without a source quote (checked by tests)

* The error-function edge: ε = w/(2 erfinv 0.8) makes S rise from 0.1 to 0.9 over w (definition; test to 4 eps); the
  Gaussian blur of an interval [erfc((x − hi)/ε) − erfc((x − lo)/ε)]/2 (quadrature, 1e-13); the ramp integral
  J(u) = [u erfc(−u/ε) + ε e^{−u²/ε²}/√π]/2 (differentiation; trapezoid check); the resolution rule w ≥ 3.03 d from
  exp(−π²ε²/(4d²)) = 10⁻³.
* The Landau gauge of a field in a region, A_b = B g(x_b) F(x_a): curl A = B f_a g (central differences, 1e-8);
  the pure-gauge strip and its flux.
* Strang's local error C dt³ against two half steps C dt³/4: local error = (4/3)‖ψ_dt − ψ_dt/2‖ (against the
  Chebyshev expansion: within 3 %); a contraction's global error is at most the sum of its true local errors. The
  scene sums sampled estimates of them (trapezoid between samples): an estimate of that bound, not a bound (review
  B6-Q7 [error in earlier]: called "rigorous"; sampled only before and after a barrier crossing the sum fell below the
  true error, 1.3e-4 against 5.5e-4; sampled every 64 steps it is 8.6e-3, `test_the_companion_is_sampled_by_steps`).
* The far-field minima of a symmetric double slit and their offset O(D/(4σ_x²)) from the slope of the illumination
  (measured 3.7× smaller for 2× wider illumination; the model gives 4×).
* Ehrenfest's theorem for a linear potential (Stern–Gerlach) and for a uniform magnetic field (the cyclotron orbit).

## 8. Added while processing review B6-quantum (2026-11-03) — DERIVED, each checked by a test

(a) **Demodulated interpolation** (`schrodinger_nd.sample(carrier=)`, `demodulated`; `bohm.carriers`). For any
wavevector κ per point, ψ(x) ≈ e^{iκx} Σ_j w_j(x) ψ_j e^{−iκx_j} = Σ_j [w_j e^{iκ(x − x_j)}] ψ_j is exact at the
samples (w_j(x_m) = δ_jm) and its derivative's weights are (w'_j + iκ w_j) e^{iκ(x − x_j)}; the error is the
Lagrange remainder of φ = ψ e^{−iκx}, whose wavenumbers are k − κ. The plain remainder at k d (measured for a plane
wave, the maximum over the cell): 1.2e-3 of the gradient at k d = 1, 2.2e-2 at 1.5, 0.13 at 2, and higher orders
converge slowly there (order 16: 2.7e-2 at 2). κ from the phase steps of the samples around the nearest node (unique
for |k| d < π), applied where it makes the samples smoother (second differences), scaled to none where it does not
(near a node the phase winds and the plain interpolant of a locally polynomial ψ is better). Tests:
`test_demodulated_sampling_is_exact_on_the_samples_and_for_its_carrier` (plane wave at k d = 2.5 to round-off; the
samples returned exactly), `test_demodulated_interpolation_keeps_trajectories_at_any_admitted_k_d` (free packets:
3e-5, 9e-5, 2e-5 nm over 30 nm at k d = 1, 2, 2.5 against 3.3e-2, 2.2, 7.9 nm plain).

(b) **The grid's band next to a potential** (`Scene._resolution_reason`). On the grid the product V ψ of two
band-limited fields carries the sum of their wavenumbers; what passes π/d reappears at k − 2π/d (aliasing). Free
motion is exact for |k_i| ≤ π/d_i; with a potential the wave's largest wavenumber must leave room for the potential's
own spectrum, the classical 2/3 bound of pseudo-spectral products (K ≤ (2/3) π/d keeps the aliased sum K + K_V − 2π/d
out of |k| ≤ K when K_V ≤ K). The wave's K is its packet's |k| + 6σ_k (the packet rule's e^{−18} level), widened in
quadrature by measurements (1/(4s²)) and jumps (1/(2a²): L_y ∝ exp(−|r − y|²/(2a²)) has the power spectrum
exp(−a²k²)), raised by energy conservation to sqrt(K² + 2m ΔV) with ΔV the potential energy it can convert; along the
axes where nothing acts the momentum is conserved and the free rule stays. Measured (a 4-nm well, transmission against
transfer matrices): 6e-7 at K_loc d = 1.78, 1.5e-4 at 2.11, 4e-3 at 2.65, 7.4e-2 at 3.10 (2/3 π = 2.09). Test:
`test_the_grid_must_hold_a_wave_in_a_well`.

(c) **A ball's centre** (`Ball.check`): S(R − |r|) has the radial slope S'(R) = exp(−R²/ε²)/(ε√π) at r = 0, a cone;
relative to the edge's steepest slope 1/(ε√π) it is exp(−R²/ε²) ≤ EDGE_TOL (the edge rule's level) for
R ≥ ε sqrt(ln 1/EDGE_TOL) = 1.45 w. A shape's extremum in closed form: a box height × Π_i erf(s_i/(2ε)), a ball
height × erfc(−R/ε)/2, a wall height × erf(t/(2ε)). Test: `test_a_shapes_peak_and_the_balls_kink`.

(d) **Closed edges and a vector potential** (`Scene._gauge_reason`). The split operator applies A through the gauge
phases e^{−iqχ_i}, χ_i = ∫ A_i dx_i from the window's first sample, on a periodic grid: across a closed face A must be
periodic (else the wrap is a sheet of field, flux −Φ for the Landau strip) and q∮A_i dx_i a multiple of 2π (else a
wave crossing the face gains an Aharonov–Bohm phase of a flux that is not there). Test (review B6 s09b):
`test_a_closed_window_refuses_a_charged_particle_next_to_a_field` (bypassed: ⟨v_y⟩ = −0.75 for a packet that never
meets the field).

(e) **The switch of a field** (`Scene._switch_reason`). Keeping ψ through an instantaneous change of A changes the
kinetic momentum by −qΔA(r): Faraday's law fixes only curl E = −∂B/∂t; for a z-invariant field with E → 0 far away
the induced field is −∂A_C/∂t of the Coulomb gauge (div A = 0, A → 0), which a thin solenoid's symmetric gauge is
(Φ/(2πr) outside: the flux tube) and the Landau gauge is not. Test (review B6 s15):
`test_a_uniform_field_is_not_changed_under_a_charged_wave` (bypassed: two set-ups identical in the window get kinetic
momenta q ΔB · 38 nm = 2.89/nm apart).

(f) **Bohm points in an absorbing wave** (p02 `_absorb`). With −iW in H, ∂ρ/∂t + ∇·(ρ v) = −2Wρ, v = j/ρ. Points that
move with v and are removed at the rate 2W(x) keep the density of the survivors equal to ρ (the same equation for the
points' density), so a point drawn from ρ/N is absorbed by detector k with probability ΔA_k/N, A_k = ∫∫ 2W_k ρ;
removed in an interval h with the hazard h (W(X_0) + W(X_1)) (trapezoid) against an Exp(1) threshold, credited to k
with probability W_k/W. The run's check compares the counts with Σ_epochs m ΔA_k/N (binomial); p02 test
`test_bohm_registrations_follow_the_absorbed_probabilities` (negative control: half the velocity).

(g) **Oblique incidence on an absorbing layer** uniform across: the transverse momentum is conserved, so a wave at
angle θ meets it as a 1-D wave of k cos θ. Test: `test_oblique_incidence_on_the_edge_layers` (60°: within 2 % of R).
`layer_reflection` models the layer as a ramp that ends abruptly; on the periodic grid a wave that passes it meets the
opposite face's mirrored ramp, so with a leak comparable to R the model's R is larger than what the run returns (×14 at
a leak of 0.38) — conservative; the playground's strengths keep the leak below 1e-5.
