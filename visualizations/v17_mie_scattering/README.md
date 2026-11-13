# v17 — light scattered by a drop: the rainbow, its supernumerary bows, Alexander's dark band and the glory

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.8, on P1). One drop at one wavelength is solved exactly by the Mie
series; the same field is split by the Debye series into the light reflected by the surface and the light that
crosses the drop once, twice or three times, and compared with Descartes' rays and Airy's theory of the rainbow. A
cloud of drops of many sizes in sunlight gives the colour of the sky against the scattering angle, wavelength after
wavelength, and the sky around the antisolar point drawn from it. Small drops also show their near field, inside and
around the drop, in the volume and on slice planes of the 3-D environment.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.optics.mie` | core | the drop at the display wavelength: the coefficients a_n, b_n (and c_n, d_n inside), Q_ext, Q_sca, Q_abs, Q_back, g, the amplitudes S1(θ), S2(θ) on a grid fine enough for the drop's interference ripple (up to 20 001 angles, sent as 0.05° bin means with each bin's minimum and maximum), the phase function and the polarisation from the bins' intensities, the intensity for x- or y-polarised incident light (the polar surfaces), the Mueller elements; the scattered power over the angles by Fejér's quadrature; the self-test against Wiscombe's published values; the near field E, H (incident + scattered outside, internal inside) in a 40³ volume and on slice planes |
| `core.optics.mie_debye` | core | the Debye terms p = 0 (reflection, with diffraction), 1 (transmission), 2 (one internal reflection: the primary rainbow), 3 (two: the secondary) of the same drop, the orders where the series diverges and the terms' size against the total, and the closed-form sum against the Mie coefficients with its derived per-order tolerance |
| `core.optics.mie_poly` | core | the cloud: the average of the series over a gamma distribution of sizes (mean ⟨r⟩, relative width σ/⟨r⟩) cut at ±4σ (the probability cut off is reported), one wavelength at a time, on nodes 0.25 apart in the size parameter (at most 1600 per wavelength: beyond, coarser, flagged as an approximation), with the half-sum error estimate |
| `core.optics.radiation` | core | Planck's law for the Sun's spectrum |
| `core.data` | core | water's index n(λ, T) (IAPWS R9-97) at the density of liquid water at 0.1 MPa (IAPWS SR6-08), the Sun's nominal T_eff = 5772 K (IAU 2015 B3) |
| `theories.approx.rainbow` | approximation | ray optics (the deviation of the orders p, Descartes' angle, the ray paths drawn in 3-D) and Airy's theory (its intensity near the bow and its maxima) — for comparison with the exact series |
| `tools.colour` | tools | the CIE 1931 colour matching functions (Wyman, Sloan & Shirley 2013) and sRGB for the sky's colour (display only) |
| `core.geometry` | core | the slice planes' cut by the region (small drops only) |

## The model

* **The drop and the light.** A homogeneous sphere of water (IAPWS R9-97 at the chosen temperature and 0.1 MPa:
  dispersion included, absorption not — the release gives the real part only) or of a given index n + iκ (no
  dispersion), in a medium of index 1 (vacuum, the default — an approximation of air, stated in the header) or a given
  one; the incident plane wave travels along +z, polarised along x. Size parameter x = 2π n_medium a/λ. In the 3-D
  scene lengths are in units of the radius a.
* **One drop** (at the display wavelength, live): the phase function p(θ) = 4π (dσ/dΩ)/C_sca of unpolarised light, the
  Debye terms on the same scale, the polarisation P = (|S1|² − |S2|²)/(|S1|² + |S2|²) (and that of the term p = 2 where it
  carries light), Descartes' angles of p = 2, 3 and Airy's maxima for the drop's x; the scattered intensity as polar
  surfaces around the drop (log scale over 5 decades, 2° bins): for unpolarised light and for the incident wave
  polarised along x or y; the geometric rays of p = 0–3 in the plane y = 0 (fans and the Descartes rays).
* **The near field** (drops with x ≤ 45 at 380 nm, i.e. ⟨r⟩ ≲ 2.7 μm): |E|²/|E0|² of the total field in a 40³ volume of
  the box [−2.5a, 2.5a]³ and on up to three slice planes (121 × 121 points, computed for the plane by the series; the
  window's phase mode shows arg E_x).
* **The cloud in sunlight.** Single scattering by a dilute cloud: the intensities of the drops add. Sizes: a gamma
  distribution (σ/⟨r⟩ = 0: one size), cut at ±4σ and renormalised (the cut-off probability, ≤ 3·10⁻⁴ on the presets, is
  sent with each wavelength; its bias on ⟨dσ/dΩ⟩ was measured ≤ 2–3 times that fraction of the peak). Light: sunlight as a black body at 5772 K (the IAU nominal T_eff), 8–32 wavelengths
  from 380 to 760 nm (trapezoid weights), or one wavelength. For each wavelength the run averages ⟨dσ/dΩ⟩(θ) over the
  sizes at 551 scattering angles from 125° to 180° (0.1°), multiplies by the Sun's spectrum and the CIE functions and
  adds it to the XYZ of each angle; the colour strip (sRGB, exposure to the brightest angle) and the luminance-weighted
  polarisation are sent after each wavelength. The sky window paints that strip around the antisolar point (each
  pixel the mean of the strip over its own angular size); the dashed circles are Descartes' bows at the display
  wavelength.
* **Time.** The scene is stationary; the world's time adds one wavelength every 0.5 s (the colour "develops" as the
  spectrum is summed). A live change (the light, the display wavelength) recomputes the drop and starts the sky again;
  the drops' size, width, substance and the number of wavelengths are world parameters.

## Checks shown live

Which checks test what (review B8-mie, M3): the values of the coefficients are tested only by `debye` (a second
route to the same a_n, b_n) and `wiscombe` (published numbers). `theorem`, `energy` and `mueller` are identities of the
series' structure — true for any coefficients — and are labelled so in the run: they test the angular functions, the
quadrature and the arithmetic. `boundary` and `plane_N` test the assembly of the near fields (vector spherical
harmonics, c_n, d_n) against a_n, b_n. Each pass/fail check has a negative control in the tests (a broken engine part
it catches).

| check | what it compares | tolerance |
|---|---|---|
| `theorem` | Q_ext from the coefficients against (4/x²) Re S(0) from the angular sum — the optical theorem in the series' form, an identity (π_n(1) = τ_n(1) = n(n+1)/2): it checks the angular functions at θ = 0 | 100 N ε |
| `energy` | a transparent drop: the scattered power ∫(\|S1\|² + \|S2\|²) dΩ by Fejér's second quadrature rule in cos θ (exact for these polynomials; `mie.angular_integrals`) against Q_ext, for N ≤ 3000; above, Re a_n = \|a_n\|² and Re b_n = \|b_n\|² at every order. For a real m both are identities of the series' structure (a_n = A/(A − iB), A, B real): they check the angular functions, the sums and the quadrature, or that no imaginary part entered the arithmetic, not the coefficients' values. [error in earlier] Gauss–Legendre quadrature with numpy's weights failed this check on a correct engine for most drops of 37 ≲ x ≲ 112 (r ≈ 3–10 µm at 550 nm): those weights are off by up to 6e-9 near cos θ = ±1, where the forward peak sits; the "cause not found" of the earlier text was this | derived: u (x² Q_ext²/(2 Q_sca) + 8N + 16) (the nodes' rounding under the forward peak of width ~1/x², and the sums; measured ≤ 0.12 of it); 16 u (only the complex division's rounding remains) |
| `debye` | the Debye series summed in closed form, (1 − R²² − T²¹T¹²/(1 − R¹¹))/2, against a_n, b_n at every order (Hankel-function ratios and the Wronskian against the Mie recurrences: two routes): the check of the coefficients' values. [error in earlier] the fixed 5e-10 failed on a correct engine for m = 0.75 (an air bubble in water) at x ≥ 1.65·10⁴ | per order u (1000 N + 32 x\|da_n/dx\|/max\|a\|): the Debye route's logarithmic sums, and the conditioning near narrow resonances shared by both routes (`mie_debye.ACCURACY`; measured ≤ 0.46 of it over 281 cases) |
| `wiscombe` | the engine against Wiscombe's published MIEV1 values (1979, Appendix III: x = 100, m = 1.5 and 1.5 − 0.1i; Q_ext, Q_sca, g, S1(0°), S1(90°), S2(90°), S1(180°)): a check of the coefficients by published numbers, at those two spheres, not at the world's drop | half a unit of the last printed digit |
| `mueller` | S11² = S12² + S33² + S34² at 361 angles: an identity for any S1, S2 (a single particle's Mueller matrix is pure); it checks `mie.mueller`'s arithmetic | 1e-10 |
| `water` | the engine's IAPWS formula at 589 nm and 0 °C (density from SR6-08) against the release's Table 3 | 1e-6 (one unit of the printed digit) |
| `boundary`, `plane_N` | small drops: the tangential E (and H) just inside and outside the surface at 24 points (on each slice: 12 points where the plane cuts the drop); it checks the fields' assembly (D_n, ψ_n, χ_n enter both sides consistently) | 20 x \|m\|² × 1e-10 + 1e-11 (the field's change across the 1e-10 a gap) |
| `bow2`, `bow3` (information) | transparent drops with x ≥ 50: the maximum of the Debye term p = 2 (3) against Airy's first maximum, the difference in degrees in the note; Descartes' angle in the note | — |
| `alexander` (information) | Descartes' angles of p = 2 and 3: the dark band between them | — |
| `sky_sum` (information) | the size average's error estimate: the largest over the angles of the difference of the two interleaved half-sums, the largest over the wavelengths, in units of the maximum of ⟨dσ/dΩ⟩ — an order-of-magnitude estimate of the largest error (on the presets the actual largest error is 0.1–3 times it), not a bound and not a per-angle error; the note gives the probability the ±4σ cut removed | — |
| `sky_bow` (information) | water in white light: the brightest angle of the primary bow against Descartes' angle at 550 nm | — |

The information checks carry no tolerance ([error in earlier]: a tolerance in degrees was shown next to a relative
difference). A weakly absorbing drop with m ≈ 1 whose Debye series diverges (|R¹¹| > 1 on some orders), or whose terms
p = 0–3 exceed the total by more than ten times, gets a notice: its coloured curves are cancelling terms, not light that
took a path (the closed-form sum stays right; review B8-mie, M5).

Measured on the presets (CPU, 16 wavelengths, 2026-11-04, after review B8-mie):

* `rainbow` (0.15 mm ± 2 %, x = 1714 at 550 nm, m = 1.33540 at 10 °C, in vacuum): Descartes 138.270° (p = 2) and
  128.482° (p = 3), Alexander's band 9.79° wide; the p = 2 maximum at 138.95° against Airy's 138.959°, the p = 3 maximum
  at 127.30° against Airy's 127.251°; in white light the brightest angle of the primary bow 138.9°, supernumerary
  maxima of the luminance at 140.4°, 141.5°, 142.4°, 143.2° …, the secondary bow at 127.4°; `debye` 2.7e-12 (tolerance
  at its worst order 2.0e-10), `energy` 2.3e-11 relative (bound 3.3e-10), `theorem` 4e-16 relative, `sky_sum` 0.023;
  1589 size nodes at 380 nm; the sky takes ~0.66 s per wavelength (the schedule is 0.5 s: the run lags slightly).
* `supernumerary` (0.1 mm ± 0.5 %, x = 1142): the p = 2 maximum 139.15° (Airy 139.173°); luminance maxima in white
  light at 139.1°, 141.1°, 142.5°, 143.7°, 144.7° (Airy at 550 nm: 139.17°, 141.15°, 142.54°); `sky_sum` 0.18 (135–267
  size nodes for so narrow a distribution; with the former ±3σ cut 0.31). [error in earlier] 0.11 was quoted; it
  reproduced as 0.31.
* `fogbow` (15 μm ± 15 %, x = 171): a broad, nearly white bow at 141.2° (Airy 141.47°, Descartes 138.27°): the Airy
  offset grows as x^(−2/3); the secondary bow is lost; a glory rises at 177.8°–179°; `sky_sum` 0.036.
* `glory` (8 μm ± 10 %, x = 91): coloured glory rings with luminance maxima at 178.1°, 175.9°, 174.0°; the "bow" at
  142.5° (Airy 143.13°); `sky_sum` 0.043.
* `near` (1 μm, x = 11.4 at 550 nm): the focus of the drop just behind it on the axis (the slice y = 0); `boundary`
  2.0e-9 and `plane_1` 9.0e-10 against 4.1e-8; `debye` 1.8e-15.
* `absorbing` (2 μm, n = 1.6 + 0.05i, x = 22.9): Q_abs = 1.051; no internal rays survive (the Debye terms p ≥ 2 are
  damped), no rainbow checks.
* `big_drops` (0.3 mm ± 10 %): coarse at every wavelength (1599 nodes, dx up to 2.5 at 380 nm), stated in the header;
  ~2.7 s per wavelength.

## Approximations and limitations

* Single scattering by a dilute cloud (no multiple scattering, no extinction along the line of sight); independent
  drops (intensities add).
* Sunlight is a black body at 5772 K: no absorption lines, no atmosphere; the Sun's angular size (0.53°) is not
  folded in — real bows are smeared by about half a degree more than drawn, which dims the supernumeraries.
* Drops are spheres: large raindrops (≳ 0.5 mm) are flattened by the air, which changes their bows; water has no
  absorption here (IAPWS gives no imaginary part), so the narrow resonances of the series are narrower than real
  water's.
* The medium is vacuum by default (n = 1). In air the drop's index relative to the medium is smaller by n_air, and
  the bows move: for water at 10 °C and 550 nm, p = 2 by −0.054° and p = 3 by +0.096° for an illustrative
  n_air − 1 = 2.77·10⁻⁴ (not taken from a source; the engine has no air index yet). The quoted angles (138.270° …) are
  for vacuum. The header states this.
* The size distribution is cut at ±4σ and renormalised: the cut-off probability is reported (≤ 3·10⁻⁴ on the presets);
  its bias on ⟨dσ/dΩ⟩ was measured ≤ 2–3 times that fraction of the peak and is not part of `sky_sum`. [error in
  earlier] the cut was ±3σ and unstated (bias up to 4.6e-3 of the peak for 15 µm ± 15 %).
* The size integral is a trapezoid sum with steps ≤ 0.25 in x. Near the bows the ripple of the reflected against the
  internally reflected waves has periods 1.18–1.28 in x (4–5 nodes per period: resolved); at the antisolar point the
  strongest component has period ~0.27 (about one node per period: not resolved), and the sum there relies on the
  gamma weight being smooth over many periods (σ/⟨r⟩·x ≫ 1) to suppress the alias; the largest errors of the presets
  sit there (θ > 170°: 7e-3 – 2e-2 of the peak against 7e-4 – 4e-3 at the bow, against sums 25–50 times finer).
  [error in earlier] "the ripple (period ~1.5 in x) is resolved". The narrow resonances of the series (widths far below the step) are sampled, not resolved; the error
  is estimated, not bounded (`sky_sum`). Above 1600 nodes per wavelength the step grows ("coarse", a header
  approximation): the ripple and the supernumeraries are then aliased into noise. The nodes of one wavelength are
  also capped so that its step takes about 10 s at most on the CPU (cost ~1.4 ns × nodes × terms × angles, measured
  2026-11-05): drops of 1 mm are coarse at every wavelength; "⏭ event" goes to the next wavelength (it computed the whole
  sky at once: 20–40 s, over 2 min for 1 mm drops; review UX-params P16). A drop nearly index-matched to the medium
  (|m − 1| < 10⁻³ at the display wavelength) is refused: it scatters almost nothing, and the series' checks do not hold
  there (m = 1: Mueller NaN, Debye 1163 against 0; the Debye route fails up to |m − 1| ~ 3·10⁻⁵, the energy identity of
  large drops up to ~10⁻⁴; the cause is open, STATUS).
* The coefficients near the narrow resonances of a transparent drop are ill-conditioned problems (forward error up to
  ~x·u/Γ for a resonance of width Γ in x; the engine is backward stable), which the per-order tolerance of `debye`
  takes into account.
* The near field is computed only for x ≤ 45 (the slice grid of 121 points over 5 radii must resolve the wavelength).
* Airy's theory and Descartes' angles are approximations (`theories.approx`); the checks comparing them are
  information, not tests. For m < 1 there is no rainbow; the rays drawn are the drop's own (those that enter have
  b < m).
* Open items: `../../STATUS.md`.

## Tests

`tests/test_v17_mie_scattering.py`: every preset builds and passes its checks (the heavy `big_drops` up to its first
wavelength); the sky is revealed one wavelength per 0.5 s of world time and the summary checks come at the end; the
phase function, the polarisation and the Debye terms sent equal the engine's functions called directly; the binned
phase function of a large drop lies within its bins' minimum and maximum and integrates to 4π within the forward
peak's under-resolution; the sky's spectra are the engine's size average; the white-light colour is the sum of the
wavelengths sent (recomputed from the messages); a live change recomputes the drop and restarts the sky; the near
field's volume and slices are the engine's field and a plane placed by the view command is verified on the drop's
surface; water's index is the engine's; drops too large are refused; an absorbing drop has no rainbow checks; the
polar surfaces (the engine's polarised intensity) and the ray fans (also for m < 1). Review B8-mie added: the `energy`
check of the 5.34 µm drop that failed before passes, and fails with numpy's Gauss–Legendre weights or a wrong τ_n; the
identity beyond the quadrature fails with an imaginary part leaking into D_n; with D_n, ψ_n or χ_n wrong by 1e-3 the
identities stay at round-off while `debye` and `wiscombe` fail; `theorem`, `mueller` and `boundary` fail with a wrong
angular sum, a wrong S33 and swapped internal coefficients; an air bubble at x = 1.9·10⁴ passes `debye`; a diverging
Debye series is announced; the medium, the cut and coarse sampling are in the header; the information checks carry no
tolerance. The shared tests continue the world from a checkpoint byte for byte (`../tests/test_checkpoint.py`),
rebuild it by replay (`../tests/test_restore.py`) and compare views brought back through key frames with rebuilt ones
in a browser (`../tests/browser/keyframes.mjs`). The engine's own tests: `../../lfphys/tests/test_mie.py`,
`test_mie_debye.py`, `test_mie_water.py`, and the comparison with miepython
(`../../lfphys/tests/external/test_ext_mie_miepython.py`).
