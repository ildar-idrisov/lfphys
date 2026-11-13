# v15 — the shadow of a Kerr black hole and its photon rings; what if the hole is not Kerr

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.3, on P7, P10, P11). What a distant observer sees of a rotating black
hole lit by a thin equatorial disc of gas: the shadow, the lensing ring and the photon ring, computed pixel by pixel in
the 3-D environment of the player, with the horizon, the ergosphere, the disc, the equatorial photon orbits, the ISCO,
the observer's direction and sample light rays in the scene, and the observer's screen in its own window. A world with
modified physics replaces the Kerr metric by Johannsen's parametrized deviation and compares the size of its shadow
with the Event Horizon Telescope's measurements.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.gravity.kerr_shadow` | core | every pixel (α, β) of the screen a photon traced back in closed form: captured (the shadow) or come from infinity; its equatorial crossings n = 0, 1, 2 in order along the ray traced back, the radius r_n, the side of the disc and the redshift g_n of the gas there (Keplerian outside the ISCO; inside it, free fall with the ISCO's constants, after Cunningham); the progressive image `ShadowImage` (a band of rows per step, its state saved and restored exactly); the computed shadow edge `capture_boundaries` with its derived bound `edge_tolerance`, the size measured on it `shadow_size`, the images of a gas ring `ring_image`; CPU or GPU 0 (kernel `gravity.kerr_shadow`) |
| `core.gravity.kerr_null` | core | Kerr null geodesics in closed form (Gralla & Lupsasca 2020): the critical curve (Bardeen 1973) and its distance along screen directions `critical_radii`, the Lyapunov exponent of the bound photon orbits (Johnson et al. 2020), the ray paths drawn in 3-D, `cartesian` (Boyer–Lindquist to the Kerr–Schild drawing coordinates) |
| `core.gravity.kerr` | core | horizons, equatorial photon orbits, ISCO |
| `theories.alternatives.johannsen_metric` | alternative | the "what if": Johannsen's metric (α₁₂, α₁₃, α₂₂; Kerr at α = 0), refused unless regular outside the horizon (Johannsen 2013a Eqs. 72, 76–78); its shadow edge from its photon orbits, its own equatorial circular orbits and ergosphere, the size δ as EHT defines it, the EHT bounds |
| `core.data` | core | EHT M87* (2019) and Sgr A* (2022) measurements, quoted from the papers |

## The model

* **Units.** G = c = M = 1: lengths and the screen's impact parameters α, β in M; the world's time in M.
* **The observer** is at infinity at inclination θ to the spin axis (live; 163° by default, the inclination the EHT
  used for M87* with a > 0: EHT 2019 Paper V, Fig. 8, "i=17° for a* ≤ 0 and 163° for a* > 0"); the screen's α axis is
  horizontal, the spin axis projects upwards.
* **The order n** is the number of the crossing of the equatorial plane along the ray traced back (Gralla & Lupsasca
  2020b's m̄; the polar half-periods of the ray). For moderate inclinations n = 0 is the direct image of the disc,
  n = 1 the thin lensing ring, n = 2 the photon ring. Near edge-on (θ ≳ 75° for a disc of 20 M) a ray below the line
  of sight first crosses the plane far beyond the disc, so the direct image of the disc's lower face is n = 1; at
  exactly 90° that crossing does not exist and the same image is n = 0. The hover names the side of the disc (+z, the
  spin's, or −z) and marks crossings beyond the disc or inside its inner edge.
* **The disc** (a model of the source, stated, not a law): a thin equatorial disc from its inner edge (the horizon for
  Cunningham's gas, the ISCO for Keplerian gas only) to 20 M, prograde or retrograde (live), with emissivity
  J(r) ∝ r⁻² or a narrow ring at 6 M (live). A pixel's brightness is Σ_n g_n⁴ J(r_n): the bolometric intensity of an
  emitter moving with the gas (I/ν³ invariant along the ray), each crossing counted once (f_n = 1), no absorption, no
  scattering, no time dependence. These choices set the rings' brightness against the direct image: Gralla, Lupsasca
  & Marrone 2020 weight the crossings n ≥ 1 by a fudge factor f = 1.5 for the disc's thickness, Chael, Johnson &
  Lupsasca 2021 use g³ (a flat spectrum at 230 GHz) and 2/3; a thin optically thin layer would weight each crossing
  by its path length through it (`kerr_shadow.disk_intensity` takes p and f). The brightness scale of the screen is
  percentile 99.5 of the pixels computed so far.
* **The scene is stationary.** The image does not change in time; the run reveals it row by row as the world's time
  goes on (one image in 4 M at the default speed of 1 M/s), and a live change starts a new image at once.
* **What if.** In the Johannsen world the engine computes the edge of the shadow (from the metric's photon orbits,
  the conditions R = R′ = 0 as Bardeen's) and its size, and the metric's own circular equatorial orbits (photon orbits,
  ISCO; numerically, Johannsen 2013a Eq. 83) and ergosphere (g_tt = 0, his Eq. 69), shown in the scene and the panel
  with Kerr's for comparison; it does not ray-trace the disc in that metric, and the screen shows only the two edges
  (the deviating one and Kerr's with the same spin).
* **The 3-D scene** has the spin axis up. Views: "Iso"; "Observer" — from the observer's direction (the arrow), as
  on the screen; "Edge-on" — the disc edge-on; "From the pole" — along the spin axis.

## Checks shown live

In a Kerr world the checks come when an image is complete: they measure the run's own tracer, and the closed forms
are references next to the measured values, not before them (the dashed critical curve too is drawn only over the
rows already computed). In a what-if world the shadow's edge is the world's computed result and is compared at once.

| check | what it compares | tolerance |
|---|---|---|
| `edge` | the shadow's edge found by bisection on the tracer's own fate of each ray, in 8 directions, against Bardeen's closed-form critical curve | derived per direction (`kerr_shadow.edge_tolerance`): the round-off of d₃₄ = (r₄ − r₃)²/4, whose sign decides the fate, over its slope, plus the curve formula's error and the last bisection step |
| `schw` | at a = 0: the traced edge in the 8 directions against √27 M | the same derived bound |
| `lyapunov` | the images n = 1, 2, 3 of a gas ring approach the curve by e^(−γ) per polar half-period; the ratio n = 2 → 3 against e^(−γ) of the bound orbit behind | 4 e^(−γ) × the deviation of the ratio n = 1 → 2 (corrections fall by e^(−γ) per order) |
| `size` | the shadow's size δ = d/(6√3 M) − 1 (EHT 2022 Sgr A* Paper VI Eq. 14: d the median diameter over 128 directions from the point half-way between the extreme α) measured on the traced edge, against the closed-form curve | twice the largest derived edge bound over the diameters |
| `pixels` | the image's captured pixels against the inside of the critical curve, for every pixel farther from the curve than the drawn 721-point curve can be from the true one (its chords' sag, measured against 8001 points: ~10⁻⁴ M) | 0 mismatches |
| `gpu` | when the image ran on GPU 0: the redshift of its middle row against the same code on the CPU | the engine's GPU test: 128 u × (|α ∂g/∂α| + |β ∂g/∂β| + |g|) by central differences on the CPU; values compared farther than 0.05 M from the curve, the fate everywhere |
| `eht` (information) | M87*: the deviation of the shadow's size from the Kerr hole of the same spin and inclination (EHT 2019 Paper VI Sec. 9.5 measured δ = θg(ring)/θg(stars) − 1 = −0.01 ± 0.17 with the ring calibrated with Kerr models, so every Kerr hole is 0 there; ±0.17 as Psaltis et al. 2020 use it); Sgr A*: δ itself against the VLTI interval [−0.17, +0.01] (Paper VI 2022 Eq. 13; −0.08 +0.09/−0.09) | the 68 % interval |
| `eht_kerr` (information, what-if) | δ of Kerr with the same spin and inclination | — |

Measured on the presets (CPU, 128 × 128, 2026-10-29): `edge` 1.7·10⁻¹⁶ – 7.9·10⁻¹⁶ against bounds of ~10⁻¹³; `size`
traced = closed form to round-off; `pixels` 0 mismatches over all 16 384 pixels farther than 6·10⁻⁵ – 9·10⁻⁵ M from
the curve; the ring ratio n = 2 → 3 0.0601 against e^(−γ) = 0.0607 (a = 0.9, θ = 163°), 0.04317 against
e^(−γ) = 0.04321 (a = 0.99 edge-on: the equatorial orbit, where γ = π at every spin), 0.04297 against e^(−π) = 0.04321
(a = 0); δ = −0.0523 for M87* at a = 0.9 (the same at 17° and 163°); the what-if α₁₃ = 3 at a = 0: δ − δ_Kerr = 0.096,
its photon sphere at 3.3005 M and ISCO at 7.1646 M (Kerr: 3, 6).

## Limitations

* The source is a thin disc with a chosen emissivity, not a computed accretion flow; no time variability (an orbiting
  hot spot and the time delays of the rings are not modelled).
* The what-if world draws no image of the disc: the engine traces rays only in the Kerr metric.
* EHT's ring diameter (42 ± 3 μas for M87*) is the diameter of the emission ring, not of the shadow; the comparison
  uses δ, the shadow-size deviation EHT derives with its calibration.
* Open items: `../../STATUS.md`.

## Tests

`tests/test_v15_kerr_shadow.py`: every preset builds and passes its checks; the image is revealed only as the world's
time reaches its rows; the pixels sent equal the engine's tracer called directly; a live change starts a new image; the
checks come when the image is complete and the size measured on the traced edge equals the engine's; the edge against
Bardeen and √27 M, and a = 0.998 at 81° (which failed a fixed tolerance) within the derived bound; the pixels compared
up to ~10⁻⁴ M of the curve; M87* in its own definition of δ and a what-if world inside ±0.17; a what-if world computes
its edge, its own orbits and ergosphere and refuses a metric not regular outside the horizon, or without a single
band of photon orbits, in the viewer's language, naming for each deviation the values it takes with the others as they are
(`johannsen_metric.admissible_intervals`; review UX-params P6 — the refusals were the engine's English); a metric with
a band without circular geodesics (Ω² < 0) builds, its ISCO the band's outer edge (against a 40-digit root); the views and the
spin axis up; the rays, the orbits and the horizon's surface. The shared tests continue the world from a checkpoint byte for byte
(`../tests/test_checkpoint.py`) and rebuild it by replay (`../tests/test_restore.py`).
