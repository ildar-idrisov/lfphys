# v16 — optical vortices: Laguerre–Gauss beams, orbital angular momentum, the rotational Doppler effect

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.7, batch B8). A beam whose phase winds as e^{ilφ} around its axis:
its surfaces of equal phase are l intertwined helices, its energy flow spirals around the axis, and every photon
carries the orbital angular momentum lħ. A rotating element shifts the light's frequency by an amount proportional to
l; a detector records samples as the world's time runs, and their spectrum gives the measured beat.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.optics.beams` | core | the exact vector beam of the world (`VortexBeam`: plane waves of helicity σ with the azimuthal factor e^{i(l+σ)φ_k}, an exact solution of Maxwell's equations; the share of the source's power it keeps, `propagating_fraction`, and what its evanescent part still carries at a distance, `evanescent_fraction`; its cost before it is built, `table_cost`) and its radial table (`RadialTable`); the densities of Berry and of Bliokh, Bekshaev & Nori (energy, Poynting vector, spin, canonical momentum), the angular momentum per photon and its flux, with Barnett's split of the flux (`angular_momentum`), and their closed forms from the spectrum (`moments`: both splits, the Poynting moment, the energy per unit length); the topological charge (`charge_on_circle`, `charge_in_disc`); the flow lines (`trace_lines`); the surfaces of equal phase (`isophase_sheets`) |
| `core.optics.beams_rotation` | core | the image rotator (`image_rotator`), the spectrum of a sampled series and its peak (`spectrum`, `peak_frequency`); the closed forms of the shifts (references in the checks: `superposition_beat`, `scattered_on_axis_shift`, `rotated_beam_frequency`) |
| `theories.approx.beams_thin_masks` | approx | the thin masks (moved from the core after review B8-beams, O7): the spiral phase plate (its thickness for drawing), the fork hologram (the binary mask as its Fourier series up to the grid's band), its orders' shares of the power and their closed form, the spinning rough surface (`SpinningSurface`, `on_axis_amplitude`) |
| `core.optics.angular_spectrum` | core | the field behind the fork hologram: the volume, the transverse planes, the longitudinal planes (exact routes) |
| `theories.approx.beams_paraxial` | approx | the paraxial model (Laguerre–Gauss modes, the Fresnel integral of the plate's spectrum and its current) and the paraxial closed forms used as references (Gouy phase, the spiral of the flow lines); the Gaussian beam's parameters (z_R, w(z)) of every world |
| `core.geometry` | core | slice planes (`Plane.horizontal`, `plane_cut`) |

The apparatus (`engine/apparatus.py`, no physics of its own): the beam of a world as a table of the engine's
fields, the grids the scene samples it on, the devices' meshes (geometry, not consequences), the detectors.

## The model

* **The beam** (world parameters): a Laguerre–Gauss mode LG_pl with its waist w0 at z = 0, or a Gaussian of waist w0
  behind a spiral phase plate at z = 0 (charge l), or a Gaussian on a fork hologram (below). Wavelength λ, polarisation
  σ = +1, −1 or linear (x).
* **Exact model** (default): the vector beam whose plane-wave spectrum is the source's order-l Hankel transform A(q)
  (closed form for the LG waist; for the plate a Gaussian times e^{ilφ}, whose spectrum falls only as q⁻²), propagating
  waves only (q ≤ k), each with the helicity polarisation (θ̂ + iσφ̂)/√2. Each plane wave is transverse, so the field is
  exact Maxwell; H = −iσE. In the paraxial limit it is LG × e_σ. For linear polarisation, the sum of the two
  helicities. J_z = l + σ per photon is a property of this construction (an eigenstate of J_z, Bliokh et al. 2010),
  not of every nonparaxial beam with a phase e^{ilφ}.
* **What the exact beam keeps of the named source** (review B8-beams, O2). The evanescent part of the source's
  spectrum (q > k) is not in the beam. The run computes the share of the source's power it keeps (check "Fraction of the
  source's power the beam carries"; Hankel–Parseval). For an LG waist narrower than about a wavelength w0 is then the width of the spectrum,
  not the measured waist: a world that drops more than 10⁻⁴ of the waist's power (its field on z = 0 differs from the
  named mode by more than 1 % in L2 norm) is labelled in the header and the title ("the spectrum cut at q = k"; the
  `tight` preset drops 0.66 %), and one that drops more than 10 % (32 % in L2 norm) is refused with the reason (e.g.
  LG₃⁶ at w0 = 0.3 µm, λ = 1.6 µm: 99.96 %). Behind a spiral plate the dropped part is the plate's evanescent near field
  (the singular centre): real, but decaying away from the plate; the beam is the plate's exact far field, and the header
  states the share at z = 0, λ and 2λ (default plate world: 9 %, 0.11 %, 0.028 %). A plate world whose incident Gaussian
  is itself more than 10 % evanescent is refused.
* **Cost** (review B8-beams, O5). The radial table is sized before it is built (`VortexBeam.table_cost`, the Fresnel
  table's node count): a world needing more than 6·10⁷ Bessel evaluations (~20 s at the measured 3·10⁶/s in the image)
  or a dense matrix above 0.5 GB is refused with the estimate (the worst legal corner needed ~10¹⁰ evaluations and an
  18 GB matrix; a plate world with w0 = 6 µm, λ = 1 µm took 46 s). The defaults need 10⁶–10⁷.
* **Paraxial model** (flagged "approximation"): the LG closed form (or the Fresnel integral of the plate's spectrum,
  cut at q = k) times a uniform polarisation vector. It has no longitudinal field; its spin is σ by construction (the
  run computes it from the model's field, check "Spin S_z per photon per unit length (from the model's field on the
  same plane)"; review O9).
* **The table.** The world tabulates the radial functions F0, F2, F1 (exact) or u (paraxial) on at least 320 radii
  (λ/16 apart) × 200 depths, out to the largest radius any part of the run samples (the volume's and the slices'
  corners, the angular-momentum plane, the disc's quadrature, the prism's square; review O14); every drawn value is the
  bicubic interpolation of the envelopes F e^{−ikz} (each extended to negative r by its parity, so that the spline has
  no boundary at the axis) with the carrier put back exactly. Its error is measured against the direct route at 24
  seeded points and 18 on the brightest ring (check "Field table against the direct calculation"): 5.9·10⁻⁸ of the peak for the default world.
* **The rotating element** (world parameter; its frequency f is live): a spinning rough disc at 90 % of the depth
  (a thin phase screen of 60 seeded Gaussian bumps, turned exactly) — the detector takes the scattered light through a
  mode filter of the +l and −l superposition (the mode filter of Lavery et al., Science 341, 537 (2013), their second
  configuration; here the illumination is the world's beam l): the part that keeps +l is not shifted, the part the
  surface's harmonic −2l scatters into −l is shifted by −2lf, so the intensity beats at 2|l|f — the frequency of their
  Eq. (4) (illumination ±l, shifts ±lf); the light scattered onto the axis (q = 0) is shifted by −lf (their Eq. (3));
  or a Dove prism in one arm of a
  Mach–Zehnder interferometer (the other arm's prism at rest; Courtial et al., Phys. Rev. Lett. 80, 3217 (1998)):
  the prism turning at f turns the image at 2f and mirrors it (l → −l), so the turned arm is shifted by −2lf and the
  power of the two arms beats at 2|l|f. The detector samples 64 times per turn; every 128 samples (two turns) the
  spectrum of the series is computed, its peak is the measured beat, and the check compares it with the closed form.
  A live change of f starts a new series at once.
* **The fork hologram**: a Gaussian on a thin mask with the phase function lφ − 2πx/Λ (amplitude, binary or blazed),
  propagated by the angular spectrum on 512 × 512 points; the depth is chosen so that the orders −1, 0, +1 separate
  (4.5 w(z) apart); that needs tan θ₁ > 9/(k w0): the default waist of the LG modes (1.5 µm) is too narrow for every
  period of the form, so the world takes the smallest waist with a 20 % margin over that bound whose region fits the
  grid, in steps of 0.1 µm, and says so (4 µm at Λ = 2.5 µm, the preset's value; review UX-params P11); a period no
  waist up to 6 µm can take is refused naming the largest period that works; order m leaves at sin θ = −mλ/Λ (order +1 towards negative x). The charge of each order is
  measured in a disc of 1.3 w(z) around it. The binary mask is sampled as its Fourier series up to the grid's band
  (|m| ≤ 4 here): point samples of its sharp edges would alias the higher orders back (the sampled duty cycle was 0.526,
  c₀ 5 % too large; review O8); the fork's centre is sampled by the mask's mean around it. Each order's share of the
  propagating power is measured in the angular spectrum (the cell |k_x + mK| < K/2) and compared with the closed form
  of the same thin mask on the same k grid: each order m is a Gaussian behind a plate of charge m·l, shifted by −mK, and
  their q⁻² tails overlap, so the share is not |c_m|²/Σ|c_j|².

## The scene

* **Equiphase surfaces** (layer "Surfaces of equal phase"): the sheets arg ψ = ωt of the field's component along the
  input polarisation, extracted by the engine from the field sampled on a cylinder grid (r follows w(z), 192
  azimuths), over at most 36 λ of depth around the waist. The optical phase is shown slowed: one period of e^{−iωt}
  takes `t_show` of world time (400 ms by default; the real period of 1 µm light is 3.3 fs). The 16 phases of the
  period are sent as the world's time reaches them; frames name the phase they show; after one period nothing new is
  computed (the sheets repeat). The helices therefore turn on screen; in fact the wave front runs along z at c. The
  rotating element, by contrast, turns in real world time: the relative rotation of the helices and the element on
  the screen is not the measured shift, which is counted from the true optical frequency (review O11; said in the
  panel "Time and phase").
* **Intensity** (volume, 56³, |E|²/peak); zero beyond the rotating element (the light there is not computed).
* **Flow lines**: the Poynting vector (yellow; exact model) and the canonical (orbital) current p_o (cyan), traced by
  RK4 (220 steps) from 16 points on two rings of the first plane; two Poynting lines are traced again with half the
  step, and their difference is the lines' error shown in the checks (review O16). In the paraxial model the Poynting
  vector of u·e_σ has no transverse part (it lacks E_z), so only the orbital current Im(u*∇u)/k is drawn.
* **Slice planes** (up to three, any orientation): |E|² and the phase of the envelope arg(ψ e^{−ikz}) (the window's
  "phase" mode shows it on a colour wheel); computed from the table for the plane's points and checked at three points
  of the plane against the direct route. For the fork hologram only planes along the axes (exact angular-spectrum
  routes).
* **Devices**: the spiral phase plate (its thickness h(φ) = lλφ/(2π(n−1)), exaggerated), the hologram's pattern, the
  rotating disc or prism (turned each frame by the matrix the run sends), the detector. The prism is drawn with its
  base face normal to y, so that the reflection off it mirrors y → −y, the mirror line of the computed rotator at the
  same angle (the x axis at 0; it was drawn turned by 90°, review O13).

## Checks (computed value against the reference)

| check | reference | default world (LG₀³, σ = +1, w0 = 1.5 λ, exact) |
|---|---|---|
| table against the direct route (24 seeded points + 18 on the brightest ring) | 0 (tolerance 10⁻⁴ of the peak) | 5.9·10⁻⁸ |
| share of the source's power the beam keeps (q ≤ k; information) | 1 | 1 − 9·10⁻¹⁶ (`tight`: 0.99335) |
| J_z = L_z + S_z per photon **per unit length**, measured on the waist plane (LG) or 2 λ behind the plate (Berry's densities, spectral derivatives on up to 192² points; window ±25 λ behind the plate, ±10 λ for a cut LG spectrum; shown for information when more than 10⁻³ of the energy lies outside the window) | l + σ | 4.0000000 (4) |
| S_z per photon per unit length — **the canonical split** (Bliokh et al. 2010) | σ⟨cos θ⟩ from the spectrum | 0.9536057 (0.9536057) |
| L_z per photon per unit length (canonical) | l + σ(1 − ⟨cos θ⟩) | 3.0463943 (3.0463943) |
| angular-momentum flux / energy flux × ω (Maxwell stress) [error in earlier: the README printed 4.000000015, which did not reproduce] | l + σ | 4.000000058 (4) |
| spin flux per photon crossing the plane — **Barnett's split** (Monteiro et al. 2009, Eq. 33; review O3) | σ⟨(1 + cos²θ)/2⟩/⟨cos θ⟩ (\|S\| > 1: moves from σ the other way) | 1.0014290 (1.0014290) |
| orbital flux per photon (Barnett's split) | l + σ − the above | 2.9985711 (2.9985710) |
| Poynting angular momentum per unit length ∫(r × P)_z dA — a check since review O4 (information where the spectrum is cut at q = k: its window error falls only as R^−1/2) | l + σ + (σ/2)⟨sin²θ/cos θ⟩, the same on every plane | 4.0478636 (4.0478636) |
| power through three planes | equal (tolerance 3 × the energy outside the window; information when that exceeds 10⁻³) | 9.2·10⁻⁸ |
| topological charge: phase winding on the brightest ring at z_c (720 points) | l | 3 |
| Gouy phase on the ring r = w/√2 at z = z_R | ρ²z/z_R − (2p+\|l\|+1) arctan(z/z_R) (paraxial; information for the exact field) | −2.64376 (−2.64159) |
| number of helical sheets (mean crossings per bright cell) | \|l\| | 3.000 |
| orbital flow lines against the paraxial spiral φ − φ0 = l/(2ρ²)(ψ − ψ0) | 0 (paraxial worlds; information for the exact field) | 0.339 w0 |
| Poynting flow lines: RK4 step error (two lines with half the step; information) | — | 2.1·10⁻¹⁰ w0 |
| longitudinal field max\|E_z\|/max\|E\| (information) | — (first order, ~λ/(πw0)) | 0.200 |
| paraxial mode against the exact field on z_c: **the transverse components** (information) [error in earlier: the check compared all three components, so its value was max\|E_z\| (0.280, first order), while its note said it grows as (λ/w0)²; review O1] | — (second order: ×4 when w0 doubles) | 0.047 of the peak |
| each slice: \|E\|² at three points against the direct route | 0 (tolerance 4 × the table's error) | 1.6·10⁻⁷ (tolerance 2.4·10⁻⁷) |
| detector: beat from the spectrum of 128 samples | 2\|l\|f | 30.0001 Hz (30 Hz) |
| detector: shift of the on-axis light (disc) / of the turned arm against the arm at rest (prism) | −lf / −2lf | −15.000 Hz (−15 Hz) |
| no vortex (l = 0) or f = 0: modulation depth | 0 | < 10⁻⁶ |
| fork hologram: charge of the orders −1, 0, +1 | −l, 0, l | −1, 0, 1 (l = 1) |
| fork hologram: each order's share of the propagating power, in the angular spectrum (review O8) [error in earlier: the README compared the power in discs of 2.5 w(z), 0.190, 0.591, 0.190, with \|c_m\|²/Σ_{\|j\|≤40}\|c_j\|² = 0.204, 0.503, 0.204, which counted evanescent orders and described neither the discs nor the sampled mask] | the closed form of the thin mask on the same k grid (tolerance 2 × the grid's aliasing, estimated by the closed form with the grid's periodic images) | 0.2135, 0.5590, 0.2135 against 0.2135, 0.5584, 0.2135 (tolerance 1.1·10⁻³; without the overlap of the tails it would be 0.224, 0.552, 0.224) |

In the plate world (`spp`) the angular-momentum comparisons are checks (window ±25 λ: 6.7·10⁻⁴ of the energy outside; it
was 1.3·10⁻³ with the former ±16.6 λ, and they were shown for information — review O6). Its S_z = 0.87243 (0.87190) and
L_z = 2.12758 (2.12810) per photon per unit length: the plate's lħ per photon is the scalar field's orbital angular momentum
(measured for l = 3 in `lfphys/tests/test_beams_thin_masks.py`); in the vector field ⟨cos θ⟩ = 0.87190 is set by the light that the singular
centre of the ideal thin plate sends to wide angles (the q⁻² spectrum cut at q = k) — a property of the idealised plate,
not of a real one.

## Approximations (stated in the header where a world uses them)

* The paraxial model (a world's choice): the transverse field errs at second order, (λ/w0)², and the longitudinal
  field, first order (~λ/(πw0)), is missing; both are measured by the information checks of an exact world, and the
  header gives both numbers.
* The spiral phase plate, the fork hologram and the rough disc are thin masks in one plane (the engine's
  `theories.approx.beams_thin_masks`: the Kirchhoff boundary condition; the engine's fuller models of structured
  plates are `core.em.fdtd` and `core.em.slit`).
* The exact beam holds propagating waves only (above: labelled or refused where the named source is not represented).
* The split of the angular momentum into spin and orbit depends on the definition: the panel shows the canonical split
  per unit length (Bliokh et al. 2010) and Barnett's split of the flux (Monteiro et al. 2009); only J_z = l + σ does
  not depend on it.
* The disc scatters scalarly (Lavery et al.: "there is no dependence upon polarisation"); the Dove prism is an ideal
  image rotator that leaves the polarisation alone (so the shift is l, not l + σ, as in Courtial et al. 1998, PRL 80;
  the engine also has the mirror-like rotator that adds σ, tested in `lfphys/tests/test_beams.py`).
* Behind the rotating element the light is not propagated: the detector's samples are computed from the field on the
  element's plane (the mode filter's overlap, the interferometer's power).
* The flow lines are traced from 16 starting points; the equiphase sheets cover at most 36 λ of depth.

## Tests

`tests/test_v16_optical_vortices.py`: every preset builds and passes its checks (with two detector measurements);
the regressions of review B8-beams — the paraxial check is the transverse difference and falls by 4 when w0 doubles
(E_z by 2), sources beyond q = k are labelled or refused, both splits and the Poynting moment are checks where the
window holds (the plate world's too), the cost guard refuses at once with the estimate, the fork's shares against the
closed form (the ideal |c_m|² share off by more than 5·10⁻³), the drawn Dove prism mirrors y → −y like the computed
rotator, the table reaches every sampled point (l = 6, p = 3 with the prism), the Poynting lines carry their step error;
the phases of the optical period are revealed only as the time reaches them and repeat after one period; the sheets'
vertices lie on the surface of their phase of the field computed by the direct route (a negative control at another
phase); the detector's samples never run ahead of the world's time, the beat follows a live change of f; the Dove
prism's beat and shift; no beat without a vortex; the spin–orbit split of the exact tight beam (σ = −1, w0 = 0.6 λ:
S_z = −0.842, L_z = 0.842, J_z = 0; Barnett's flux split −1.024, 1.024) against the paraxial model (L_z = l, S_z = σ
computed from its field); slices of any orientation checked
at points; the fork's orders carry ±2 for l = 2 and tilted slices are refused; a world without a rotating element
refuses a live change; the measured beat differs by 2f between l = 2 and l = 3 (the detector reads the field, not the
formula). The engine's own tests: `lfphys/tests/test_beams.py`, `lfphys/tests/test_beams_thin_masks.py`,
`lfphys/tests/test_beams_paraxial.py`. Open items: `../../STATUS.md` V44.
