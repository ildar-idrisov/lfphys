# u32 — The double-slit experiment with single particles and observers

**English** | [Русский](README.ru.md)

Particles one by one through N slits (photon with energy, frequency, polarisation; electron, neutron, He-4 atom,
C60, a custom particle), with or without an observer of the path. Owner guide: `../README.md`; rules: `../RULES.md`.

## The causal chain of one particle (all computed in the run)

1. **Emission** at a time of a Poisson stream; the particle's own wavelength (log-normal spectrum, σ of ln λ:
   temporal coherence) and its own group velocity, source point (uniform line source of width s at distance L₁:
   spatial coherence), and internal state drawn from the source's density matrix (the chosen pure state with
   probability P, otherwise uniform on the Poincaré/Bloch sphere, so ρ = P|ψ⟩⟨ψ| + (1 − P) I/2 exactly).
2. **Slit plane** (t_e + L₁/v), with the apparatus present at that moment: elements at the slits act (absorption with
   the probability their projectors give: 1 − Σ_j‖J_jχ‖²/N), the which-path qubit is coupled (Englert's model,
   rotated by θ at its slit), a probe photon of the Heisenberg microscope may scatter (direction from the dipole
   pattern (3/8π)(1 − (n·p̂)²) of a charged or polarisable particle; transverse kick κ = k_p(n_i − n_f)_x in the slit
   plane), the Aharonov–Bohm phase qΦ/ħ = 2π(q/e)Φ/(h/e) sits between slits 1 and 2. Under the GRW modification the
   hits during the flight to the screen are drawn here: number Poisson(λ·(m/u)·L₂/v), each a kick q ~ N(0, 1/(2r_C²))
   at a uniform distance z′, which moves the screen pattern exactly like a slit-plane kick q(1 − z′/L₂).
3. **Screen** (t_e + (L₁ + L₂)/v), with the apparatus present at THAT moment: the analyser in front of the screen and
   the basis in which the detector is read. Born rule P(x, r) = Σ_jl A_j A_l* G⁽ʳ⁾_jl with the closed-form paraxial
   amplitudes A_j of this particle (own k, source point, kick) and the Gram matrix of its marks; then the analyser's
   absorption, missing the finite screen (Parseval: the total flux is λL₂aΣ‖m_j‖²), the position and the reading drawn
   jointly (exactly within each grid cell for the piecewise-linear density), detector efficiency; dark counts are a
   separate Poisson stream. A particle that passed the slits before an apparatus change and reached the screen after
   it is marked transitional and not counted in the segment's statistics.

No rule "observed → no interference" exists in the code: interference between slits j and l survives only through
G_jl, the overlap of what the particle carries away from them, or is washed out by kicks it actually received.

## Live set-up (owner, 2026-10-23)

Everything an experimenter can change in a laboratory is a live parameter: the particle and its energy, the source
(distance, width, rate, polarisation or spin, spectrum), the slits (number, width, period), the screen (distance,
size, pixel), the detector (efficiency, dark counts), the which-path observer, the elements and the analyser. A
change applies at once and starts a new segment:

* particle or slits/screen changed: the beam path is rebuilt; particles in flight at that moment are lost (counted
  as `lost`), the grid, the exact reference fields and the set-up checks are recomputed;
* source changed: particles already emitted fly on and are transitional (kept out of the new segment's histogram);
* apparatus, detector or display changed: in-flight particles meet the apparatus present when they reach it;
* parts of the apparatus the new particle cannot take (a polariser for an electron, the microscope for a photon) are
  removed, with a notice; an explicit impossible request is refused and nothing changes. The forms offer only the
  choices that act on the chosen particle (option-level `show_if`: polarisation elements for photons, spin elements
  for spin ½, "Set by" = "speed (massive)" for massive particles and "frequency (photon)" for photons, the microscope
  for dipole scatterers); a choice made anyway is refused naming it by its label and what to take instead (review
  UX-params P17, 2026-11-05).

Bounds stated in the run's refusals (review UX-params P8, P18): at most 100 dark counts per emitted particle (each is
an event of the record; at 1e12 1/s one frame drew ~2e9 of them and took 31 GB), and every step of the world holds at
most ~4000 events (signal and dark); the screen's expectation is computed on the screen grid extended by the largest
shift a particle gets on its way (the microscope's recoil, GRW hits, the source's width): a set-up needing more than
1 GB for it is refused with the shift, the grid and the probe wavelength that fits. |γ₁₂| is not fitted where it is
undefined: one slit dark (crossed polarisers: it read 1.108 [error in earlier]) or the fringes not resolved by the
screen grid; the check then says why (information).

Only the laws (Born exponent, collapse model and its parameters) are fixed for a world; changing them starts a new
world inside the same run.

## What the run computes per segment (apparatus configuration), without Monte-Carlo noise

Every random transverse influence (source point, probe kick, GRW kick) shifts a particle's pattern rigidly in the
paraxial solution (`engine/ensemble.py`). The expected screen distribution is therefore the pattern of the
ensemble-averaged marks (exact for the source's density matrix) convolved with the distribution of the shift, by FFT
with the product of the characteristic functions (uniform source: sinc; microscope: the dipole pattern's marginal in
closed form; GRW: exp(−Λ_z[1 − √π erf(a)/(2a)])), and integrated over the spectrum by Gauss–Hermite nodes. The same
construction gives:
* the expected curves per detector reading and per class ("no scattered photon"), binned on the server as the
  histogram is, with the dark counts added;
* the near-field map |Ψ(x, z)|² of the ensemble (with all decoherence), z from 2a to the screen, with the marks
  *before* the analyser (the analyser stands right in front of the screen; in the eraser the map has no fringes and the
  screen has them); the region next to the slits where the paraxial field differs from the exact Rayleigh–Sommerfeld
  solution by more than 1 % is found by bisection and hatched;
* flow lines dx/dz = Im(Ψ†∂ₓΨ)/(k|Ψ|²): for a pure state without decoherence the de Broglie–Bohm trajectories (for
  photons the energy-flow lines, the average photon trajectories measured by weak measurement, Kocsis et al.,
  Science 332, 1170 (2011)); with decoherence the flow lines of the ensemble-averaged current (J gains κ|Ψ|² for a
  kick); none for GRW runs (a GRW kick at z′ is not a slit-plane kick for the current).
Only the Born-exponent modification (nonlinear in |ψ|²) uses a Monte-Carlo expectation over 1500 of the run's own
particle draws (stated in the run).

The degree of coherence |γ₁₂| of a pattern (histogram or expectation) is fitted with the slit envelopes' ratio fixed
by the marks: μ = c₀(G₁₁b₁₁ + G₂₂b₂₂) + c₃Re b₁₂ + c₄Im b₁₂ + dark, Poisson maximum likelihood for counts (`engine/stats.coherence_ml`). The error shown for the histogram is a
parametric bootstrap from the fitted model (`coherence_boot_err`, 60 refits). The Fisher error is only asymptotic:
at |γ| = 1 and 100 detections it was 14× too small. The bootstrap is recomputed when the count grows by 10 %, at
most once per 20 frames (about a second of play; counted in frames, not wall time, so a world continued from its record
shows the same errors), and scaled by √(n_then/n) in between.

## Checks emitted by the run

| check | reference |
|---|---|
| wavelength | an independent expression of the given input: hc/√(E_k² + 2E_k mc²), h√(1 − v²/c²)/(mv), hc/E, c/ν |
| screen resolution | ≥ 8 grid points per finest fringe |
| paraxial accuracy at the screen | the exact 2-D Rayleigh–Sommerfeld integral (`engine/rs.py`, composite Gauss–Legendre panels); > 1 % fails |
| fringe period (two slits, far field) | λL/d |
| degree of coherence of the expected pattern | microscope: Chapman's dipole average \|1 − p + p⟨e^{iΔk_x d}⟩\| (tolerance 0.02: the reference ignores the envelope shift by the recoil); GRW: exp(−Λ[1 − (√π r_C/d) erf(d/2r_C)]), Λ = λ(m/u)L₂/v; wide source: van Cittert–Zernike \|sinc(s d/(λL₁))\|; forced slit collapse: 0 |
| consistency (identities, labelled so) | Englert V² + D² = 1 for pure marks; \|γ₁₂\| of a coherent expectation = the marks' overlap; Sorkin's parameter 0 under the Born rule; no-signalling under the Born rule (under the Born-exponent modification its violation is reported as a computed consequence) |
| histogram vs expectation (live) | χ² p-value (dark counts included); \|γ₁₂\| of the histogram ± its error vs the expected \|γ₁₂\| |

## Vector mode: a perfectly conducting screen (B8, closes STATUS V4)

The scalar model above puts the incident wave into the slits (Kirchhoff's boundary values). For photons the screen can
instead be a perfect conductor of thickness t (live parameters "Model of the slit screen" =
"perfect conductor: vector diffraction (slits up to 20.7 λ)" and "Screen thickness, µm (0 = infinitely thin)"; t = 0
is a screen of zero thickness). The scalar model stays the default. In vector mode the run solves Maxwell's equations
for the run's own slits (`lfphys.core.em.slit`: for t = 0 and k a ≤ 140 an edge-conditioned basis, which converges
exponentially; otherwise the waveguide modes of the slits), separately for the two polarisations:

* **TE**: E along the slits (polarisation V); u = E_y, with u = 0 on the conductor;
* **TM**: E across the slits (polarisation H); u = Z0 H_y, with ∂u/∂n = 0 on the conductor.

The distance to the screen is measured from the exit face.

**Hits.** A photon of the plane wave falls on the strip W = n·d (number of slits × period) and is transmitted with
probability P_t/W, where P_t is the transmitted power per unit length in units of the incident flux. A transmitted
photon lands with the density of the energy flux through the screen plane, j_z(x)/W, where
j_z = |χ_H|² j_TM + |χ_V|² j_TE: the flux has no TE–TM cross term. Photons that are not transmitted are reflected or
scattered back by the screen; they are counted as "reflected by the conducting screen". A set-up whose transmitted power
exceeds W (a capture cross-section wider than the period) is refused. For one slit (n = 1) the strip is W = d, the
period, which the scalar model does not use for one slit: a convention. The transmitted fraction and the count of
reflected photons depend on it; the pattern on the screen does not (the run and the panel say so).

**Where the hits stay scalar.** Which-path marks, elements at the slits, the analyser and the modified laws (the
Born exponent, collapse) have no vector counterpart in the engine. With any of them the hits are drawn from the scalar
model, and the run says so in the segment, its approximations and the panel "Model of the slit screen". The vector
curve is then only a shape comparison: the flux of the vector solution for the same slits without the elements and the
analyser, scaled to the same total as the scalar expectation (their units differ: no detector efficiency, no
elements' transmission). No difference strip is drawn then [error in earlier: before review B8 (C8) the vector curve
was per particle on the open width n·a and the strip showed its difference from the scalar expectation, dominated by
that normalisation, e.g. 0.96 of the curve for a zero-phase element]. Open item: `../../STATUS.md`, u32's vector mode.

**What is shown.** The screen panel draws all curves on one scale, that of the hits' own expectation:

* orange: the expectation the hits follow (the vector solution in vector mode), times the detector efficiency, plus
  the dark counts;
* blue: the other model. When the hits are vector it is the scalar Kirchhoff result, propagated exactly
  (Rayleigh–Sommerfeld, `lfphys.theories.approx.kirchhoff.plane_wave_field`) in the same unit and with the same
  efficiency [error in earlier: before review B8 (C3) the vector curves left the efficiency out, so with dark counts
  the χ² of a correct run failed: p = 0.0 at efficiency 0.2 and 300 dark counts/s];
* green and purple dots: the TE and TM contributions;
* red, in a strip below the histogram: vector minus scalar — only when it exceeds three times the estimated error of
  the method on the screen; otherwise the screen's caption says that it is below it.

The panel "Model of the slit screen" shows:

* the transmission per slit width T_TE, T_TM and T for the Kirchhoff boundary values;
* the weights of the two polarisations;
* the power balance;
* the estimated error of the method (the truncation in the number of modes, for T and the flux on the screen);
* the fraction of photons transmitted.

The map near the slits and the flow lines stay those of the scalar paraxial model, and the run says so. There is no
vector near field or Poynting flow lines in this visualization (same open item).

**Checks of the vector screen** (per segment):

* the power balance of each polarisation by the screen's optical theorem, P_t + P_b = −4π r_s cos θ Re R(q0), to 1e-8;
* the power carried by the modes through the slit equals the transmitted power, to 1e-8;
* the estimated error of the method, relative, for T and for the flux on 201 points of the screen
  (`SlitSolution.error_estimate`, from sub-blocks of the same operator, no second solve): for the edge basis the change
  from M − max(4, M/8) to M functions, which exceeds the error at M; for the waveguide modes Richardson's
  extrapolation from M/2, M/√2 and M with the observed order clamped to [0.5, 1] — measured 1.4–3.1 times above the
  true error (the engine's tests). Tolerance 4e-3: below one pixel of the expected curve (the plot is ≈ 200 px tall)
  and below what the histogram's χ² can see before ~3·10⁶ detections. Where the waveguide modes' estimate exceeds it,
  the run solves again once with twice the modes (the preset "Vector diffraction: …": TM, 26 → 52). [error in earlier:
  before review B8 (C6) the run showed the change T(1.25 M)/T(M) − 1 with a tolerance of 1 %; that understated the
  true error 3–6 times];
* T_TE, T_TM and T_Kirchhoff, as information;
* the fraction of the transmitted power that reaches the finite screen;
* for one narrow slit (k a < 0.3) in a thin screen, Rayleigh's limits (1897).

**Limits of the vector mode** (refused otherwise, with the reason):

* photons only;
* a plane wave (L₁ = 0);
* a monochromatic source;
* slits up to 20.7 λ (k a ≤ 130), announced in the select's help and in the panel. The default geometry (a = 20 µm at
  632.8 nm, 31.6 λ) is refused in vector mode. For wider slits the solution is costly, and the scalar result differs
  from the vector one by O(1/(k a)): below 1 % from a ≈ 6 λ.

The model itself:

* a perfect conductor: no losses and no plasmons of a real metal;
* 2-D, the slits infinitely long;
* the waveguide modes (t > 0) converge algebraically, because the field is singular at the screen's corners: order
  1.2–1.4; at the engine's default number of modes T is 0.04–0.19 % low (the preset: TE 0.047 %, TM 0.091 %; with the
  run's doubled TM 0.03 %); the run shows the estimated error [error in earlier: "0.2 % in T for TM and 0.03 % for
  TE" held for the engine's test slit only]. The edge basis (t = 0, k a ≤ 140) converges exponentially (10⁻⁷ at the
  cap).
* Cost of setting up the vector screen (both polarisations, once per wavelength, slits and thickness; a change of the
  source's polarisation, the efficiency or the dark counts reuses it — 0.4 s — and a change of the screen distance
  recomputes only the fluxes, 1.5–6 s): the preset ~3 s; at the cap k a = 129 ~17 s (t = 0, edge basis) and ~21 s
  (t = 0.2 µm, the waveguide modes, TM doubled) [error in earlier: "~10 s"; it was 14.4 s, and every change of the
  source or the detector solved again: 15–17 s; review B8 C9, C15].

**How much scalar and vector differ.** Thin screen, λ = 632.8 nm, two slits with d = 4a, screen in the far zone. The
measure is the maximum of |vector − scalar| / maximum of the scalar curve, in the common unit:

| a | V (TE) | H (TM) | D | T_TE | T_TM | T_Kirchhoff |
|---|---|---|---|---|---|---|
| 0.3 µm (0.47 λ) | 0.87 | 0.15 | 0.48 | 1.195 | 0.936 | 0.612 |
| 0.4 µm | 0.44 | 0.12 | 0.25 | 1.175 | 1.012 | 0.743 |
| 0.6 µm | 0.088 | 0.071 | 0.079 | 0.977 | 0.997 | 0.841 |
| 1 µm | 0.11 | 0.030 | 0.051 | 1.049 | 0.990 | 0.899 |
| 2 µm | 0.033 | 0.008 | 0.018 | 0.982 | 0.997 | 0.950 |
| 4 µm | 0.004 | 0.003 | 0.002 | 0.998 | 1.001 | 0.975 |
| 8 µm | 0.004 | 0.0007 | 0.003 | 1.002 | 1.000 | 0.987 |

All rows are now solved by the edge basis (estimated error ≤ 1.3e-6) and recomputed in the processing of review B8
(screen at 50 (5a)²/λ; at four times that distance the same digits). [error in earlier: the 8 µm row (k a = 79) was
solved by the waveguide modes, 0.2–0.3 % low in T; its T_TE 0.999, T_TM 0.997 and the TM difference 0.006 — larger than
at 4 µm — were the method's error, not physics (review B8 C7)]

In a thick screen TE is cut off below a = λ/2: its transmission falls as exp(−2|β₁|t), while TM passes through the TEM
mode with Fabry–Pérot resonances of height λ/(πa). The preset
"Vector diffraction: 0.5 µm slits in a 0.2 µm conducting screen, polarisation D" (a = 0.5 µm, d = 3 µm, t = 0.2 µm,
L₂ = 1 cm, polarisation D) gives T_TE = 1.056, T_TM = 0.974 (with 52 modes; 0.973 with the default 26) and Kirchhoff
0.805. Its histogram follows the vector curve: for 30 000 emitted photons (≈ 5 000 detected) seeds 1–5 give χ² p =
0.33, 0.006, 0.67, 0.44, 0.10, while the scalar Kirchhoff curve is rejected at p ≤ 5e-7 in all five [error in earlier:
"χ² p = 0.52" was one seed; review B8 C15]. Over 40 seeds the median p is 0.33 and 15 % lie below 0.05: Pearson's χ²
with ~120 bins, 46 of them expecting only 5–10 counts, is mildly anti-conservative at this count (10 % without the TM
doubling); with 300 000 photons (≈ 50 000 detected) p = 0.62, 0.39, 0.76 — no systematic mismatch between the hits and
the curve.

## Conventions

Time dependence e^{i(kz−ωt)}; H = polarisation along x (across the slits), V along y; R = (1, −i)/√2 is right-handed
(S₃ = +1), L = (1, i)/√2; the custom state R(ψ)(cos χ, −i sin χ) has S₃ = sin 2χ; wave plates: the angle is the fast
axis, symmetric retardance, no overall phase; spin rotation about y: exp(−iaσ_y/2); spin filter along
n = (sin t, 0, cos t). Born-exponent modification: the position is drawn from |ψ|^p normalised on the finite screen,
the probability of reaching the screen uses |ψ|², Sorkin's parameter uses the unnormalised I^{p/2}.

## Approximations and limits (also shown in the player, panel "Approximations of this segment")

* Paraxial Fresnel optics with Kirchhoff boundary values (the field in a slit is the incident field); the exact
  Rayleigh–Sommerfeld check covers the paraxial step only. Its quadrature: 32-node Gauss–Legendre panels with at
  most 32 rad of phase each (measured accuracy 1e-15 up to ~56 rad per panel), no cap on the panel count; a column
  whose exact integral would need more than 2·10⁷ kernel evaluations is not computed and is reported as not verified
  (hatched with its own label; the screen check is then shown as not computed). The exact fields of the map columns
  and of the screen are computed once per run and reused by every segment. For slits
  narrower than ~10 λ the boundary condition itself fails; the run warns and, for photons, points to the vector
  mode (above), which solves the conducting screen exactly. For wide multi-slit
  geometries the map column next to the slits does not resolve the individual slits (stated in the run).
* 2-D geometry (slits infinitely long along y); the y position of a dot on the screen is only for display.
* Polarisation enters through the marks; in the paraxial regime both polarisations propagate identically.
* GRW hits between the source and the slits are not modelled.
* The microscope: one scattered photon in the slit plane, a dipole pattern (Thomson for charged, Rayleigh for
  polarisable particles; not available for photons and neutrons), the longitudinal recoil is neglected; recording "the
  direction" means a detector in the back focal plane of a lens (a direction, not an image of the slits).
* Gravity on slow particles is neglected.
* Presets for electrons, neutrons and C60 are illustrative geometries, not reproductions of the original experiments.

Open items: `../../STATUS.md`, "V. Visualizations — open items".

## Tests

`tests/test_u32_physics.py` (85 tests): kinematics (50 keV electron; slow neutron by E_k against 50-digit mpmath);
Fresnel → Fraunhofer; Fresnel vs Rayleigh–Sommerfeld; the exact integral for a wide slit in the near field (incident
wave inside the projection); the exact fields reused across segments; unaffordable columns reported as not verified; closed-form derivative; Parseval; polariser marks and the
eraser; λ/2 plate; spin flip; Englert duality; readout completeness; dipole coherence vs closed forms; every preset
runs and its checks agree; the Born-exponent modification is flagged, breaks Sorkin and is reported as signalling; a
20 000-particle histogram agrees with the expectation; the eraser restores fringes in sorted subsets; absorption at
the slits and at the analyser; an analyser inserted while particles fly acts on them; apparatus changes start
segments; the exact ensemble against a direct Monte-Carlo with shifts; GRW coherence against the closed form; the
coherence estimator is unbiased on multinomial samples and its shown error is calibrated at |γ| = 1; the map shows the decoherence; the map shows the wave before the analyser (eraser); the Aharonov–Bohm phase for
|q| ≠ e; dark counts in the expectation; probe rules; per-particle flight times; GRW on electrons; circular-state
conventions.

Vector mode (13 of them):

* the scalar mode stays the default with no vector part;
* the hits follow the vector flux (χ² p > 1e-4), while the scalar Kirchhoff curve in the same unit is rejected by the
  same histogram (p < 1e-8);
* the transmitted fraction equals P_t/W within 5σ;
* the balance, mode and error-estimate checks pass;
* with efficiency 0.2 and 300 dark counts/s the run's curve passes χ², the curve without the efficiency fails it
  (review B8 C3);
* with scalar hits the vector curve is a shape with the same total and no difference is drawn (C8);
* a change of the efficiency, the dark counts, the polarisation or the screen distance does not solve again (C9);
* the estimated error lies above the true error of the preset against Richardson limits from 52–208 modes (C6);
* the width limit is announced with one number, 20.7 λ, in the help and the refusal (C15);
* TE is cut off below λ/2 in a thick screen while TM passes;
* vector and scalar approach each other for wide slits (0.25 → 0.003 from a = 0.4 to 8 µm), and at 8 µm the edge
  basis's error is far below the difference (C7);
* refusals: electrons, a finite source distance, a spectrum, slits over 20.7 λ;
* marks keep scalar hits, labelled;
* a live switch to the conductor and back;
* a checkpoint of a vector world, continued in a new process, emits what the original emits.

The engine's own tests of the solver: `../../lfphys/tests/test_em_slit.py`.

## Sources

Englert, PRL 77, 2154 (1996), doi:10.1103/PhysRevLett.77.2154 (duality); Chapman et al., PRL 75, 3783 (1995),
doi:10.1103/PhysRevLett.75.3783 (photon scattering in an atom interferometer); Kocsis et al., Science 332, 1170
(2011), doi:10.1126/science.1202218 (average photon trajectories); Sorkin, Mod. Phys. Lett. A 9, 3119 (1994),
doi:10.1142/S021773239400294X and Sinha et al., Science 329, 418 (2010), doi:10.1126/science.1190545 (three-slit test
of the Born rule); Aharonov & Bohm, Phys. Rev. 115, 485 (1959), doi:10.1103/PhysRev.115.485; Ghirardi, Rimini &
Weber, Phys. Rev. D 34, 470 (1986), doi:10.1103/PhysRevD.34.470 (GRW); CODATA via scipy.constants. The vector mode:
the sources of `lfphys.core.em.slit` (Harrington & Auckland, RADC-TR-79-257 and IEEE TAP 28, 616 (1980),
doi:10.1109/TAP.1980.1142382; Takakura, PRL 86, 5601 (2001), via Holley & Schnitzer, arXiv:1812.06753; Rayleigh, Phil.
Mag. 43, 259 (1897)), checked in `../../lfphys/sources/verification_2026-11-04_p1_charges_slit.md`. Bibliographic
data checked on Crossref 2026-10-22 (the formulas themselves are checked numerically in the tests, not quoted).
