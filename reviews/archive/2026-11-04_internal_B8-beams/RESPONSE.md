# Response to review B8 — optical vortices (P14.7): `core.optics.beams*`, `theories.approx.beams_paraxial`, `v16_optical_vortices`

Processed 2026-11-04 by a subagent that wrote neither the review nor the code under review (rules: `../README.md`).
The review text and the reviewer's scripts are untouched; two of them (`s05`, `s08`, which drive v16 through the test
harness) were re-run on copies in the session's scratchpad (`b8/proc_beams/revscripts/`), and the processing's own
measurements are `b8/proc_beams/exp1…exp8_*.py` with their outputs next to them. Environment: Docker image
`light-funnel-viz` (Python 3.11, NumPy 2.4.6, SciPy 1.17.1), `engine/` mounted at `/lf`, CPU only (`LFPHYS_NO_GPU=1`),
containers `lf-b8pb-*` stopped by name. Quotations were checked against texts fetched here and grepped (arXiv:0902.3214v1
Monteiro et al.; arXiv:1006.3876v3 Bliokh et al.; arXiv:1208.4523v4 Bliokh, Bekshaev & Nori, page 16 rendered; the
Lavery et al. accepted manuscript from eprints.gla.ac.uk/85025; Barnett et al. 2017's equation image `rsta20150444-e6.jpg`
from PMC5247487, read); no e-mail address or personal identifier was sent with any request.

## Summary

| id | severity | one line | decision | files |
|---|---|---|---|---|
| O1 | error | the check «Параксиальная мода против точного поля» claimed (λ/w0)², but its value was max\|E_z\| (first order) | fixed [error in earlier]: the check compares the transverse components (second order, measured ×4.1 when w0 doubles); E_z stays its own check; the paraxial module's validity says both orders | `viz.py`, `beams_paraxial.py`, v16 `README.md`, tests |
| O2 | error | exact worlds whose LG waist lies beyond q = k were built and titled as that mode | fixed: the engine gives the kept share (`propagating_fraction`) and the evanescent share at a distance (`evanescent_fraction`); LG worlds are labelled above 10⁻⁴ and refused above 10 %; plate worlds state their evanescent near field (no refusal: argued below), a plate on a sub-wavelength Gaussian is refused | `beams.py`, `apparatus.py`, `viz.py`, `view.js`, README, tests |
| O3 | should-fix | the spin–orbit split shown as unique | fixed [error in earlier]: labelled "per unit length, canonical (Bliokh et al. 2010)"; Barnett's split of the flux (Monteiro et al. 2009, Eq. 33) implemented, measured and shown next to it; help and README say only J_z is definition-independent | `beams.py`, `viz.py`, `view.js`, README, sources, tests |
| O4 | should-fix | the Poynting AM has a closed form; "converges or diverges" misleads; the test checked an inequality | fixed [error in earlier]: J_P = l + σ̄ + (σ̄/2)⟨sin²θ/cos θ⟩ in the docstring and `moments()`, tested on planes at z = 0, 0.3–0.5 and z_R for both helicities and a mixture; a check in v16 (information, with the measured reason, where the spectrum is cut at q = k) | `beams.py`, `viz.py`, tests |
| O5 | should-fix | no cost guard (a legal world needed an ~18 GB matrix) | fixed: the table is sized before it is built; > 6·10⁷ Bessel evaluations (~20 s) or a 0.5 GB matrix is refused with the estimate; `VortexBeam` refuses any dense intermediate above `max_elements` | `beams.py`, `beams_paraxial.py`, `apparatus.py`, tests |
| O6 | should-fix | the plate preset's AM checks were information only; its label promised 2ħ | fixed [error in earlier]: a ±25 λ window (6.7·10⁻⁴ missed) makes them checks; relabelled (the 2ħ is the scalar field's) and the README explains ⟨cos θ⟩ | `apparatus.py`, `viz.py`, `view.js`, README, tests |
| O7 | should-fix | thin-mask models in the core | fixed: `core.optics.beams_generation` and the rough surface of `beams_rotation` moved to `theories.approx.beams_thin_masks` (conflicts: `core.em.fdtd`, `core.em.slit`) | new `beams_thin_masks.py`, `beams_rotation.py`, `beams_generation.py` removed, tests, v16 |
| O8 | should-fix | the fork's power-fraction reference did not describe the measurement; the sampled binary mask was not the declared one | fixed [error in earlier]: shares measured in the angular spectrum against the closed form of the same thin mask on the same k grid (a check, tolerance from the grid's aliasing); the binary mask band-limited; the fork's centre sampled by its mean | `beams_thin_masks.py`, `apparatus.py`, `viz.py`, README, tests |
| O9 | nit | the paraxial S_z assigned, shown as measured | fixed: computed from the model's field (`spin_density`), a real check | `viz.py`, `view.js`, tests |
| O10 | nit | labels: «на фотон», z_c, «ħω⁻¹·ω», the detector's shift | fixed | `viz.py`, `view.js` |
| O11 | nit | two clocks on one screen | fixed: one line in «Время и фаза», the help and the README | `view.js`, README |
| O12 | nit | the wrapper re-derived engine physics | fixed: `energy_per_length`, `ROT.superposition_beat`/`scattered_on_axis_shift`/`rotated_beam_frequency`, `PX.gouy`, `PX.field_current`; `engine_modules()` complete; `beams_paraxial` takes z_R and w(z) from `gaussian_beam` | `beams.py`, `beams_paraxial.py`, `viz.py`, tests |
| O13 | nit | the drawn Dove prism turned 90° from the computed one | fixed [error in earlier]: base normal to y (mirror y → −y, the rotator's line at 0) | `apparatus.py`, tests |
| O14 | nit | a detector sampled outside the table | fixed [error in earlier]: the table's radius is the largest any consumer samples | `apparatus.py`, tests |
| O15 | nit | `VortexBeam.scalar`'s panel count unbounded as z_min → 0⁺ | fixed: sized first, refused beyond `max_elements` with the estimate | `beams.py`, tests |
| O16 | nit | the Poynting lines carried no error measure | fixed: step doubling on two lines, an information check | `viz.py`, README, tests |
| O17 | nit | the sources file could be sharpened | fixed [error in earlier for §1's "NOT FOUND"]: §1 (Eq. 22 + A7), §4 (Monteiro et al.; Barnett–Allen's beam not a J_z eigenstate, also in `beams.ABOUT`), §5 (Lavery's sign), §6 (Eq. 3.5 of the published text) | sources file, `beams.py`, `beams_rotation.py` |
| O18 | nit | the README's flux number; the fork panel's sign | fixed [error in earlier] | README, `view.js` |
| +1 | found | SciPy's `ive` returns NaN near x = 1e10 | fixed: asymptotic branch in `gaussian_vortex_spectrum` | `beams.py`, sources, tests |
| +2 | found | the slice check's tolerance came from mostly dim points; the table's spline had a boundary at the axis | fixed: the table's error measured also on the brightest ring and next to the axis; `RadialTable` extends each function to r < 0 by its parity | `beams.py`, `viz.py`, tests |
| +3 | found | the singular centre of a sampled plate or fork took a point value of an undefined phase | fixed: the mask's mean there | `beams_thin_masks.py`, tests |
| +4 | found | the binary mask's even coefficients were 1e-17, not 0 | fixed | `beams_thin_masks.py` |

Counts: 18 of 18 fixed (O4 with its stated limit for spectra cut at q = k, O2 with a deliberate difference for the plate
from the reviewer's suggestion — both argued below), 0 partly, 0 rejected, 0 deferred; 4 more found while processing,
fixed. Remainders that are limits of the method, not of the fixes, go to STATUS V44 (f) through the integrator.

## Findings

### O1 (error) — the paraxial check's order

*Reproduced.* `reviews/…/out/s03`: all components 0.280, 0.140, 0.070 (ratio 2.00) = max|E_z|/peak; transverse only
0.047, 0.0114, 0.0028 (ratios 4.13, 4.03).

*Fix.* `viz.py` (`_checks_beam`, check `parax`): the difference is taken over E_x, E_y only; the label says «поперечные
компоненты», the note says second order with the number (λ/w0)², and points to the E_z check (first order, its note
now says so). `beams_paraxial.py`: the docstring and `ABOUT["validity"]` said the error against the exact solution is
(λ/w0)²; they now say: scalar field and transverse components (λ/w0)², the missing longitudinal field first order,
λ/(πw0). The paraxial world's header line gives both numbers. README row tagged [error in earlier].

*Verified.* `test_parax_check_is_the_transverse_difference_and_of_second_order` (v16): w0 = 1.5 and 3.0 λ give a ratio
in (3.5, 4.6) for the check (measured 4.13: 0.04696, 0.01137) and in (1.8, 2.2) for E_z (measured 2.02) — the
negative control: the old quantity only halves (`exp9_parax.py`). Default world: 0.047 (was 0.280).

### O2 (error) — sources beyond q = k

*Reproduced.* `exp1_moments.out`: the dropped share of LG_{0,1} at w0 = 0.6, 0.3 λ: 0.00665, 0.470; LG_{0,3} at 0.3 λ:
0.895; LG₃⁶ at 0.3 µm, λ = 1.6 µm: 0.99959; LG_{0,1} at 0.3 µm, 1.6 µm: 0.846 (the reviewer's 0.007, 0.470, 0.895,
1.000, 0.846).

*Fix.* Engine (`beams.py`): `VortexBeam.spectrum_power(q_lo, q_hi, weight)` (Hankel–Parseval, an unbounded band mapped
to [0, 1)), `propagating_fraction()` (the share kept; the L2 distance between the named source and the beam's field on
z = 0 is √(1 − share)), `evanescent_fraction(z)` (the share still carried by evanescent waves at a distance z,
integrated in t = √(q² − k²), where the integrand is smooth). v16 (`apparatus.py`, `viz.py`, `view.js`): a check
«Доля мощности источника» (information); an LG world that drops ≥ 10⁻⁴ (1 % in L2 norm) is labelled in the header
(«спектр обрезан на q = k … w0 — ширина спектра, а не измеренная перетяжка») and in the title; above 10 % (32 % in L2
norm: the name no longer describes the beam) it is refused with the reason. The schema's help for w0 says so.

*A deliberate difference for the spiral plate.* The reviewer suggested refusing above ~10 % for every world. Behind a
plate the dropped part is the plate's own evanescent near field (the singular centre): it is real, and it decays away
from the plate; the vector beam is then the exact far field of the thin plate, not a different beam. The default plate
world drops 9.0 % at z = 0, but only 0.107 % at λ and 0.028 % at 2 λ (`evanescent_fraction`); refusing it would refuse
a faithful far field. So a plate world is labelled with those three numbers («у пучка нет затухающих волн за
пластинкой …»), and refused only when its *incident* Gaussian is itself not a beam (> 10 % evanescent without the plate,
e.g. w0 = 0.3 µm at λ = 1.6 µm: 50 %).

*Verified.* Engine: `test_propagating_fraction_of_an_lg_waist` against the closed form 1 − Q(|l| + 1, (k w0)²/2) (to
1e-12; negative control: Q(|l| + 2, ·) is off by > 5 %), `test_spectrum_power_without_cut_off_is_parseval` (the
plate's total w²/4 to 1e-10), `test_evanescent_fraction_by_an_independent_quadrature` (SciPy's adaptive `quad`, to
1e-9). v16: `test_sources_beyond_q_k_are_labelled_or_refused` (two LG corners and the sub-wavelength plate refused; the
default unlabelled; the plate labelled, its near field falling with distance); `test_spin_orbit_split_…` (the `tight`
preset labelled, kept 0.99335). The reviewer's `s08` on a copy (`revscripts/s08_after.txt`): the four LG corners and
the plate on w0 = 0.3 µm at 1.6 µm are refused with the reason; the plate on w0 = 0.6 µm is built and labelled (19.4 %
at z = 0).

### O3 (should-fix) — the spin–orbit split depends on the definition

*Reproduced* (`exp1_moments.out`, own closed form and plane measurement): Barnett's flux split for l = 2, σ = ±1,
w0 = 1.2 λ: spin ±1.0021648; canonical S = ±0.9451824 — opposite directions of the change from σ (the reviewer's
+0.0022 against −0.0548).

*Source checked.* Monteiro, Maia Neto & Nussenzveig, Phys. Rev. A 79, 033830 (2009), arXiv:0902.3214v1 (journal
reference from the arXiv page): Eq. (33), read on the rendered page 8, M^spin = (σ/2ω)√(ε/μ0)∫dρρ∫dφ(|Ex|² + |Ey|²); the
quotes "we conclude that r is positive and does not depend on the sign of ℓ nor on the value of σ" and "To our
knowledge, a consistent identification of spin and orbital contributions to the local angular momentum or flux densities
of nonparaxial beams is not available" grepped. Barnett 2002's full text is still not fetched (bot check); the form of
the split is taken from Monteiro et al. and said so.

*Fix.* Engine: `moments()` gives `S_flux` = σ̄⟨(1 + cos²θ)/2⟩/⟨cos θ⟩ and `L_flux` = J − S_flux (derived from Eq. 33 by
Hankel–Parseval); `angular_momentum()` measures `M_spin` = −∫Im(E⊥*·H⊥) dA/(2ω) (Eq. 33 for each helicity in natural
units; no cross terms between helicities — derived in the docstring) and `flux_S`, `flux_L`. The docstring and
`ABOUT` name both definitions and say only J_z = l + σ is independent of them. v16: S_z and L_z are labelled «на фотон
на единицу длины (каноническое разделение, Блиох и др. 2010)»; two new checks «Спин/Орбита по потоку через плоскость на
фотон (разделение Барнетта)»; the panel shows both splits under their names, and its help, the header help and the
README say the split depends on the definition (Barnett's spin > 1 in magnitude, the change the other way).

*Verified.* `test_barnett_flux_split_against_the_canonical_split`: measured on planes against the closed form to 1e-9
(1e-6 at z_R), for σ = ±1 and a mixture; independent of z; |S_flux| > 1 > |S| and the changes of opposite sign;
negative control: the canonical S as the reference is off by > 4·10⁻²σ̄; both tend to σ in the paraxial limit. v16:
`tight` shows S_flux = −1.02406 (closed form −1.02426, tolerance 4.6·10⁻³), default 1.0014290 (1.0014290).

### O4 (should-fix) — the Poynting angular momentum

*Reproduced.* `exp1_moments.out`: the closed form l + σ̄ + (σ̄/2)⟨sin²θ/cos θ⟩ = 3.0570859516 (l = 2, σ = +1, w0 = 1.2)
against the plane: −8.5e-10 at z = 0, −9.3e-10 at 0.4, −1.2e-7 at z_R; −5e-15 for l = 3, w0 = 1.5; a mixture (σ̄ = −0.28)
to 2e-11. The term is the same at the waist, where the beam neither converges nor diverges.

*Fix.* `beams.py`: the docstring derives the closed form (S = σP/ω for one helicity, Bliokh, Bekshaev & Nori 2013 Eq.
3.50, re-read on the rendered page 16; ∇·P = 0; the quadratic z-dependence of ∫r²|U|² in k-space) and replaces "not
zero for a beam that converges or diverges" [error in earlier] — including the remark on the ideal Bessel beam
(r·S_T = 0, not normalisable; a finite beam narrowing to one cone keeps the term). `moments()["J_poynting"]` (σ̄ for a
mixture). The test's inequality is replaced by the closed form on six planes (the identity test kept). v16: `am_poynting`
is a check with that reference and the window's tolerance.

*Its limit, measured.* For a spectrum cut at q = k with a non-zero value there (the `tight` and plate worlds), the
Poynting moment in a window converges far more slowly than the densities: `exp5_window.out`, `tight`, its error
5.6e-3, 4.6e-3, 4.0e-3, 3.2e-3 at R = 10, 15, 20, 30 λ (~R^−1/2), while S errs 3e-4 → 1e-4 and the window tolerance is
4.6e-3 → 1.5e-3. There the comparison is information, and its note says why; making it a check needs a tail route —
STATUS V44 (f) through the integrator.

*Verified.* `test_poynting_angular_momentum_closed_form_on_every_plane` (tolerances 1e-8, 1e-6 at z_R; negative
control: l + σ̄ is off by > 4·10⁻²σ̄; also the energy per length against Parseval); v16
`test_angular_momentum_checks_are_checks_where_the_window_holds` (default: a passing check, 4.04786362 against
4.04786356; plate: information with "R^−1/2" in the note).

### O5 (should-fix) — cost guard

*Reproduced* (sizing): the corner (plate, l = 6, w0 = 6 µm, λ = 0.4 µm, zspan 3) needs 9266 radii × 242688 nodes,
~1.0·10¹⁰ Bessel evaluations (the reviewer's 17.9 GB matrix); the plate world l = 2, w0 = 6, λ = 1 (46 s measured by the
reviewer) needs 1.5·10⁸. Bessel rate measured in the image: 2.8–3.8·10⁶/s (orders 0–8; `rate.py`).

*Fix.* Engine: `VortexBeam.nodes`, `table_cost` (nodes, the largest matrix in elements and bytes, Bessel evaluations)
and a guard in `scalar`, `radial`, `table`: any dense intermediate above `max_elements` (default 10⁸) is refused with
the estimate before it is allocated; `beams_paraxial.fresnel_table_nodes` for the paraxial plate table. v16
(`apparatus.Beam`): the cost is computed before the table; > 6·10⁷ Bessel evaluations (~20 s at 3·10⁶/s) or a matrix
> 0.5 GB is refused with the numbers («мир слишком дорог: таблица поля … ~X млн вычислений … (~Y с) …»). Map of the
estimate (`exp8_costmap.py`, zspan 1.5, l = 1/6): the guard refuses plate worlds with w0/λ ≳ 4–5 (they need all angles
to 90° over the whole depth) and LG worlds at λ = 0.4 µm with w0 = 6 µm; the defaults need 0.8–2.8 s.

*Verified.* `test_cost_is_sized_before_the_matrices_are_built` (the count equals the table's nodes; a budget of half
refuses); v16 `test_cost_guard_refuses_with_an_estimate_before_building` (both reviewer's worlds refused in < 5 s; the
default below a tenth of the budget).

### O6 (should-fix) — the plate preset

*Reproduced.* Before: miss 1.26e-3 > 1e-3, every AM comparison information. Window sweep (`exp5_window.out`): miss
3.1e-3, 1.5e-3, 9.3e-4, 5.0e-4 at ±10, 15, 20, 30 λ (∝ 1/R, the r^−3/2 tails); the errors of J, S, L, flux_J,
S_flux stay well inside 4(|l| + 2)·miss.

*Fix.* The AM window behind a plate is ±25 λ (`AM_HALF_LAMS_SPP`): the default plate world misses 6.7·10⁻⁴, and its
J, S, L, flux, both flux-split checks are checks (they pass: S 0.87243 against 0.87190, tolerance 1.1·10⁻²). The label
«l = 2: заряд 2, не одна мода LG; орбитальный момент скалярного поля 2ħ на фотон, у векторного L_z = l + σ(1 − ⟨cos θ⟩)»
[error in earlier: "2ħ на фотон"]; README and help: ⟨cos θ⟩ = 0.872 is set by the light the singular centre of the
ideal thin plate sends to wide angles. The power check stays information (light does leave the window between planes).

*Verified.* v16 `test_angular_momentum_checks_are_checks_where_the_window_holds` (miss < 1e-3; six checks real and
passing); the reviewer's `s05` on a copy (`revscripts/s05_after_spp_fork.txt`).

### O7 (should-fix) — thin masks in the core

*Fix.* New `theories/approx/beams_thin_masks.py` (layer theories, kind approximation; the thin-element = Kirchhoff
boundary condition stated; conflicts: `core.em.fdtd` (a plate or hologram of finite thickness with a vector response),
`core.em.slit` (vector slits against thin-mask boundary values)): the spiral plate, its thickness, the fork hologram
and its coefficients, order directions and positions, `propagate`, and the rough surface (`SpinningSurface`,
`polar_grid`, `on_axis_amplitude`). `core/optics/beams_generation.py` is removed (nothing else used it); `beams_rotation`
keeps the closed forms, the observer, the image rotator and the spectra, and says where the surface model went.
`gaussian_vortex_spectrum` stays in the core (the order-l Hankel transform of a Gaussian times e^{ilφ}: exact; its
docstring names the thin plate as the model that imposes it). v16 imports and `engine_modules()` follow (the plate, the
disc and the fork list `theories.approx.beams_thin_masks`). LAYERS.md needs no change: the move follows its §1.

*Verified.* `test_layers.py` (every module declares its layer; the core imports nothing from theories; the new module
names its conflicts), `test_beams_thin_masks.py` (the moved tests), the v16 tests.

### O8 (should-fix) — the fork's power fractions

*Reproduced.* `exp2_fork.out`: point-sampled binary mask, shares in the angular spectrum 0.200, 0.579, 0.200 against
the ideal 0.224, 0.552, 0.224; even a blazed fork (one order) has only 0.959 of the propagating power in its cell — the
orders' q^−2 tails (each order m is a Gaussian behind a plate of charge m·l) overlap: no |c_m|²-type reference describes
the cells.

*Fix.* `beams_thin_masks`: `fork_band(dx, period)` and `fork_hologram(..., m_max)` (the binary mask as its Fourier
series up to the grid's band: its c_m exact, nothing aliased); the fork's centre sampled by the mask's mean c₀ (+3);
`order_powers` (the share of the propagating power in each order's cell |k_x + mK| < K/2); `fork_spectrum` and
`order_powers_closed_form` (the thin mask's closed form on the same k grid, from `gaussian_vortex_spectrum`, the
overlapping tails included; with `images` the grid's periodic images); `order_power_reference` (the ideal
|c_m|²/Σ_prop|c_j|²), `order_leakage`. v16 (`apparatus.Fork.shares`, `viz._checks_fork`): «Порядок m: доля
распространяющейся мощности» is a check: measured against the closed form, tolerance 2 × the aliasing estimated by the
closed form with the grid's images (|p| ≤ 1), the ideal share in the note. README row [error in earlier].

*Verified.* Over five forks and three kinds (`exp4_images.out`): |measured − closed form| / |closed form with images −
closed form| = 0.87–1.71, so 2× is a tolerance with margin; default fork 0.21347, 0.55905, 0.21347 against 0.21348,
0.55838, 0.21348 (tolerance 1.1·10⁻³). Tests: `test_fork_order_powers_against_the_closed_form_of_the_thin_mask` (three
kinds; negative controls: the point-sampled binary mask exceeds the tolerance, the ideal share is off by > 5·10⁻³),
`test_band_limited_binary_mask_keeps_the_declared_coefficients` (c_m to 1e-12; point samples off by > 0.01), v16
`test_fork_shares_against_the_closed_form_of_the_thin_mask`.

### O9 (nit) — the paraxial spin

*Fix.* The paraxial world computes S_z = ω∫S_z dA/∫w dA from its own field u·e_pol (H = −iσE per helicity) with
`spin_density`, a check against σ̄ (tolerance: round-off); J = L + S measured; the panel row says «по полю модели» and
the help says it equals σ̄ by construction. *Verified:* `test_spin_orbit_split_…` (|S − σ| < 1e-9, a real passing
check); `tight_par` shows −0.9999999999999999.

### O10 (nit) — labels

*Fix.* J, S, L «на фотон на единицу длины» (checks and panel); the panel names the plane «z = … мкм» from the `am`
message (the plate's 2 λ); the flux row's unit ħ; the detector panel «сдвиг частоты света, рассеянного на ось» (disc) /
«сдвиг частоты повёрнутого плеча (против плеча в покое)» (prism). *Verified:* the panels' text in the browser
(`b8/proc_beams/shots/s10_*_text.txt`).

### O11 (nit) — two clocks

*Fix.* «Время и фаза» has a line «два хода времени»: the element turns in real world time, the optical phase is slowed,
so their relative rotation on the screen is not the measured shift (counted from the true frequency); the same in the
help and the README's scene section. *Verified:* browser text (`s10_spp_text.txt`).

### O12 (nit) — physics in the wrapper

*Fix.* `VortexBeam.energy_per_length()` (and `moments()["W"]`) replaces v16's own Parseval sum over the private
`B._nodes`; `_beat_ref`/`_shift_ref` call `ROT.superposition_beat`, `scattered_on_axis_shift`,
`rotated_beam_frequency`; the Gouy reference uses `PX.gouy`; the Fresnel field's current is
`PX.field_current` (any field, fourth-order differences); `engine_modules()` lists `beams_paraxial` for every beam
world (its z_R and w(z) set the region and the helix grid) and `beams_thin_masks` where a mask is used;
`beams_paraxial.rayleigh` is `gaussian_beam.rayleigh` and `params` takes w(z) from `gaussian_beam.width`.
*Verified:* `test_field_current_of_any_field_and_the_shared_gaussian_parameters` (against `current` to 1e-9 with and
without the carrier; a wrong k off; one definition of z_R and w), `test_poynting_…` (W against the plane), the v16
detector tests (unchanged values).

### O13 (nit) — the Dove prism's drawing

*Fix.* `prism_mesh`: the trapezoid profile lies in (z, y), the base face normal to y; the reflection off it maps
y → −y, the mirror line of `image_rotator` at angle 0 (the x axis); the winding is reversed with the axes so that the
faces still face outwards. [error in earlier: it was drawn turned by 90°.] *Verified:*
`test_dove_prism_mesh_mirrors_across_the_rotators_line` (the base's vertices at y = −h/2 with |z| = L/2; the computed
rotator maps y → −y).

### O14 (nit) — the table's reach

*Fix.* `Beam.r_need` = max(√2·half, √2·am_half, the disc's quadrature radius, √2 × the prism's half-side) at the widest
plane the element can sit on (z1), through the shared `detector_radius` and `prism_half` that the detectors use; the
table ends 2 % beyond. [error in earlier: the prism's corner at 19.29 µm against a table ending at 19.23 µm.]
*Verified:* `test_table_reaches_every_point_the_consumers_sample` (l = 6, p = 3 with the prism).

### O15 (nit) — `VortexBeam.scalar` near z = 0⁺

*Fix.* The node count of both parts is computed before anything is allocated and refused beyond `max_elements` with the
estimate (elements and GB). *Verified:* `test_cost_is_sized_before_the_matrices_are_built` (the plate's spectrum at
z = 1e-4 over 100 radii refused; at z = 0.5 computed).

### O16 (nit) — the flow lines' error

*Fix.* Two Poynting lines are re-traced with 440 steps; the largest distance from the 220-step lines, as a fraction of
w0, is the information check «Линии потока энергии (Пойнтинг): ошибка интегрирования» (default 2.1·10⁻¹⁰, plate
9·10⁻⁷, tight 1.2·10⁻⁷). *Verified:* `test_poynting_flow_lines_carry_their_step_error`.

### O17 (nit) — sources

*Fix* (`lfphys/sources/verification_2026-11-04_p14_7_beams.md`, all quotes re-fetched and grepped here):
§1 the general S_z = σ⟨cos θ⟩ from Bliokh et al.'s Eq. (22) with κ = k/k and the normalisation (A7) "the energy per unit
z-length" — VERIFIED [error in earlier: "NOT FOUND as printed"]; §3 Eq. (3.50) re-read and used for O4; §4 rewritten:
Monteiro et al. 2009 (the secondary account of Barnett & Allen 1994, quoted; Eq. 33 for O3), and `beams.py`'s docstring
and `ABOUT` say J = l + σ is a property of the J_z-eigenstate construction (Bliokh et al. 2010), which Barnett–Allen's
beam is not; §5 Lavery's Fig. 2 caption quoted and mapped: in this engine's conventions the on-axis light is red-shifted
when the disc turns with the beam's orbital angular momentum (the light does work on it: "Doing work against this
force is the energy input required to shift the frequency of the light"), blue-shifted when it turns against it — the
same sentence in `beams_rotation`'s docstring; §6 Barnett et al. 2017: the formula is Eq. (3.5) in the published text,
read from its equation image, with the same printed sign; §6a the SciPy `ive` NaN (+1).

### O18 (nit) — small inconsistencies

*Fix.* README flux row: the value the run shows now, 4.000000058 [error in earlier: 4.000000015 did not reproduce; the
reviewer saw 4.0000000488, and the table's new radius changed it again — within the tolerance 2·10⁻⁴]; the fork panel:
«sin θ = −mλ/Λ (порядок +1 — к отрицательным x)», as `order_direction` and the check's x = −39.4 µm.

### Found while processing

* **+1** SciPy 1.17.1's `ive(0, 1e10)` (and `ive(1, 1e10)`, `ive(0, 1e12)`) returns NaN without a warning; the
  integral of the plate's q⁻² spectrum to infinity reached it (every `spectrum_power` of the plate was NaN). Fixed:
  beyond x = 1e6 `gaussian_vortex_spectrum` sums the asymptotic series of the difference (the k = 0 terms cancel
  analytically). `test_gaussian_vortex_spectrum_far_tail_and_the_asymptotic_branch`: equal to `ive` on x = 1e4…1e6 for
  orders up to 42 within the reference's own cancellation bound (4ε·ive), finite and ∝ q⁻² far out.
* **+2** After O14 changed the table's radius by 0.5 %, the l = 0 world's slice check failed (1.9e-8 against 1.7e-8):
  its tolerance, 4 × the table's error, came from 24 seeded points that mostly sit in dim light, and the table's
  largest error is next to the axis (4.4e-8 at r = 1.4 dr against 3.6e-9 on the axis), where the not-a-knot spline has
  a boundary. Fixed twice over: `RadialTable` extends each radial function to negative r by its exact parity
  (F_n(−r) = (−1)^n F_n(r)), so the spline has no boundary at the axis; v16 measures the table's error also at 18
  points on the brightest ring (at least 1.4 radial steps off the axis) at six depths. All slice checks pass, at 0.42–0.78 of their
  tolerance (`exp7_numbers.out`); `test_radial_table_interpolates_…` (fourth order) still passes.
* **+3** The centre of a sampled spiral plate or fork (x = y = 0) took exp(i·0) — a point value of an undefined phase,
  a spurious flat spectrum of one cell; now the mask's mean around the centre (0 for a continuous plate, c₀ for a fork).
  `exp3_origin.out`: the fork's share error falls from 1.2e-3 to 2.2e-4 (amplitude, default fork).
* **+4** `fork_order_coefficient("binary", 2)` was sin(π)/(2π) ≈ 1e-17, so even orders counted as "propagating"
  orders; now exactly 0.

## Tests run (all pass)

* Engine (`lfphys/`): `tests/test_beams.py`, `tests/test_beams_paraxial.py`, `tests/test_beams_thin_masks.py`,
  `tests/test_layers.py`, `tests/test_boundary.py`, `tests/test_licences.py`: 330 passed (112 s).
* v16: `visualizations/v16_optical_vortices/tests`: 27 passed (8 new; 183 s, was 86 s).
* Shared, for v16: `tests/test_checkpoint.py -k v16` and `test_shared_buffers_in_a_worlds_state_are_known`,
  `tests/test_restore.py -k v16`, `tests/test_server.py::test_registry_lists_visualizations`: 5 passed; the browser key-frame
  check `tests/browser/keyframes.mjs v16_optical_vortices` on a private server (port 8542): "all equal" (292 frames,
  106 key frames, 6 cursors); screenshots and panel texts of six presets (`b8/proc_beams/shots/`).
* The shared test files' v16 entries needed no change.

## Changes for the integrator

The processing may not edit these files; the exact text to put in them:

**1. `engine/STATUS.md`, row V44.** In the problem column replace the text of item (f), from "(f) spiral-plate and
tightly focused worlds" up to "CPU only." (keep everything before and after), with:

> (f) worlds whose angular-momentum window misses more than 1e-3 of the energy show those comparisons as information
> (the default plate world checks them in a ±25 λ window since review B8-beams O6; a plate on w0 = 0.6 µm at λ = 1 µm
> still misses 2.1e-3); the Poynting angular momentum of a spectrum cut at q = k converges in the window only as R^−1/2
> and is information there (O4); the exact vector beam holds propagating waves only — LG worlds that drop more than 1e-4
> of the waist's power are labelled, more than 10 % refused; plate worlds state their evanescent near field at 0, λ and
> 2λ, which the beam lacks within a few λ of the plate (O2); the cost guard refuses worlds above ~20 s of Bessel
> evaluations or a 0.5 GB matrix, in practice plate worlds with w0/λ ≳ 4–5 and LG worlds with w0 = 6 µm at λ = 0.4 µm
> (O5); Barnett's split of the angular-momentum flux is implemented in the form of Monteiro et al. 2009 (O3), Barnett
> 2002's full text not fetched; Beijersbergen 1993 and the other primary texts not fetched (Allen 1992, Barnett & Allen
> 1994, Garetz 1981, Durnin 1987, PRL 80 full text); CPU only.

In the "what would close it" column replace "(f) a radial route with an integrated or extrapolated tail, an evanescent
part in `VortexBeam.radial`, Barnett's split, the texts; a GPU kernel if needed;" with:

> (f) a radial route with an integrated or extrapolated tail (would make the cut spectra's Poynting moment and the
> wider plate worlds' comparisons checks), an evanescent part in `VortexBeam.radial` (the plate's near field), a cheaper
> table for wide or long plate worlds (an angular cut per depth with its error measured, or a GPU kernel), the texts;

In the state column replace "open (independent reviews of B8: `reviews/2026-11-04_internal_B8-*`)" — only if the other
B8 reviews are archived too — by the archive paths; for this review: `reviews/archive/2026-11-04_internal_B8-beams/`.

**2. `engine/lfphys/README.md`, "Light and optics".** Replace the three rows `core.optics.beams`,
`core.optics.beams_rotation`, `core.optics.beams_generation` and the row `theories.approx.beams_paraxial` with:

| `core.optics.beams` | core | (P14.7, B8) exact beams with orbital angular momentum: scalar and vector Bessel beams; the vortex beam of order l from its order-l Hankel spectrum (closed forms for an LG waist and a Gaussian times e^{ilφ}) — exact scalar (Rayleigh–Sommerfeld with the evanescent part) and exact vector of helicity σ (plane waves (θ̂ + iσφ̂)/√2: a J_z eigenstate, J_z = l + σ per photon; propagating waves only — the share of the source's power it keeps and what the evanescent part carries at a distance); radial tables (splines without a boundary at the axis); Berry's dual-symmetric densities (energy, Poynting, canonical momentum, spin); angular momentum per photon per unit length (the canonical split, Bliokh et al. 2010) and its flux through a plane with Barnett's split (in the form of Monteiro et al. 2009), measured and in closed form, and the Poynting angular momentum in closed form; costs sized before the matrices are built; topological charge (winding, plaquettes); flow lines; equiphase surfaces as meshes |
| `core.optics.beams_rotation` | core | (P14.7, B8) the rotational Doppler effect: rotating observer, turned beam (image rotator, scalar or mirror-like), the light a spinning surface scatters onto the axis (Lavery et al. 2013) — closed forms and measurables from sampled series (spectrum, peak) |

and, after the row `theories.approx.gaussian_beam`, `ray_optics`:

| `theories.approx.beams_paraxial` | approx | (P14.7, B8) Laguerre–Gauss and Hermite–Gauss modes, HG ↔ LG coefficients and the astigmatic converter, Fresnel propagation of a vortex spectrum (its cost sized first), the paraxial current of any field, closed forms of the flow spirals and of the helical equiphase surfaces; z_R and w(z) those of `gaussian_beam` |
| `theories.approx.beams_thin_masks` | approx | (P14.7, B8; moved from the core after review B8-beams) thin masks on z = 0 (the Kirchhoff boundary condition): spiral phase plate (continuous or stepped), fork hologram (amplitude, binary — band-limited on a grid —, blazed; orders m with charge m·l), the orders' shares of the propagating power measured and in closed form, the spinning rough surface as a thin phase screen |

In "Who uses it" replace the v16 row's modules by: `optics.beams, optics.beams_rotation, optics.angular_spectrum
(fork), geometry, approx.beams_paraxial, approx.beams_thin_masks`.

**3. Owner guide `engine/visualizations/README.md`, the v16 row.** Replace «орбитальный и спиновый момент на фотон,
измеренные по полю, — точное векторное решение уравнений Максвелла или параксиальная модель (при острой фокусировке
видны продольное поле и спин-орбитальное расщепление)» with:

> орбитальный и спиновый момент на фотон, измеренные по полю, — точное векторное решение уравнений Максвелла или
> параксиальная модель (при острой фокусировке видны продольное поле и то, что деление момента на спин и орбиту зависит
> от определения: каноническое на единицу длины и по потоку Барнетта расходятся в разные стороны, а полный момент l + σ —
> один); пучок, перетяжка которого уже длины волны, помечается или не строится (у точного пучка только распространяющиеся
> волны)

**4. `engine/reviews/README.md`.** Move this folder to `reviews/archive/2026-11-04_internal_B8-beams/` and add the
registry row:

| `archive/2026-11-04_internal_B8-beams/` | internal (Claude Opus subagent) | batch B8, P14.7: `core.optics.beams`, `beams_rotation`, `beams_generation`, `theories.approx.beams_paraxial`, `v16_optical_vortices`; 12 scripts, sources quoted, browser checks | 2026-11-04 | `RESPONSE.md` (processed 2026-11-04: 18 of 18 fixed — the paraxial check reported E_z under a (λ/w0)² note [error in earlier], LG worlds beyond q = k built and titled as the mode (now labelled or refused; the plate's near field stated), the spin–orbit split shown as unique (now both published definitions, Barnett's flux split implemented) [error in earlier], the Poynting moment's closed form, a cost guard, the plate preset's checks and label [error in earlier], thin masks moved to `theories.approx.beams_thin_masks`, the fork's shares against the thin mask's closed form [error in earlier]; +4 found: SciPy's `ive` NaN at large x, the table's spline boundary at the axis and the slice tolerance from dim points, the masks' singular centre, binary even orders; remainders in STATUS V44 (f)) |

No change is needed in `lfphys/LAYERS.md`, `PLAN.md`, `backend.py` or `core/data.py`.
