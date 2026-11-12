# Internal review of batch B5: the Kerr half of P7 and the visualization P14.3 (v15)

**status: awaiting processing**

Reviewer: an internal subagent that did not write the code. Delivered 2026-10-29. Another reviewer covers P5 and the
two-body half of P7. Scope (the brief of 2026-10-29): `lfphys/lfphys/core/elliptic.py`,
`core/gravity/kerr_geodesics.py`, `kerr_null.py`, `kerr_shadow.py` (CPU and GPU), `kerr_orbits.py`,
`theories/alternatives/johannsen_metric.py`, the EHT block of `core/data.py`, the tests `test_elliptic.py`,
`test_kerr_null.py`, `test_kerr_shadow.py`, `test_kerr_orbits.py`, `test_johannsen_metric.py`, the KerrGeoPy rows of
`tests/external/`, `sources/verification_2026-10-29_p7_kerr.md`; `visualizations/v15_kerr_shadow/` (viz.py,
web/view.js, README, tests) and the player additions it uses (`scene3d.js` `setLines`, `env3d.js` message `lines`,
`imagewin.js` screen axes and overlay). The tree reviewed is the working tree of 2026-10-29 14:11 (uncommitted; no file
in scope changed during the review, checked at the end).

Environment: Docker image `light-funnel-viz` (CPU, the engine mounted read-only at `/lf`, this folder mounted
read-write), the comparison image `light-funnel-ext` for KerrGeoPy, GPU 0 only through the scratchpad's `gpu_run.sh`
(one job, 2 min, 40-47 °C). Browser checks: the reviewer's own server on port 8520 (read-only engine, scratch runs
folder; stopped and removed afterwards) and `mcr.microsoft.com/playwright:v1.58.2-jammy` (swiftshader). Negative
controls were applied to copies of `lfphys` in the scratchpad, never to the repository.

Sources read (downloaded from arXiv, `pdftotext -layout`, quotes checked by grep): Gralla & Lupsasca 2020a
(arXiv:1910.12881, "GL-a"), 2020b (arXiv:1910.12873, "GL-b"); Johnson et al. 2020 (arXiv:1907.04329); Chael, Johnson &
Lupsasca 2021 (arXiv:2106.00683); Gralla, Lupsasca & Marrone 2020 (arXiv:2008.03879, "GLM"); Schmidt 2002
(gr-qc/0202090); Fujita & Hikida 2009 (arXiv:0906.1420); Johannsen 2013a (arXiv:1501.02809), 2013b (arXiv:1501.02814);
Psaltis et al. 2020 (arXiv:2010.01055); EHT M87* 2019 Papers I, V, VI (arXiv:1906.11238, 1906.11242, 1906.11243); EHT
Sgr A* 2022 Paper VI (arXiv:2311.09484). Bardeen 1973, Bardeen–Press–Teukolsky 1972 and Cunningham 1975 are not on
arXiv; their formulas were checked through GL-a/GL-b (critical curve), GLM App. B (B2-B15: Keplerian u^t, Omega, the
plunge and both redshifts) and the metric itself (c11).

## Summary of findings

| id | severity | reproduced | one line |
|---|---|---|---|
| K1 | should-fix | yes (harness, browser) | v15's `edge` check (fixed 64 ε) fails correct worlds: χ = 0.998 at 81° and 99° give 1.83·10⁻¹⁴ (✗ in the player); the unit test's own derived tolerance there is 2.1·10⁻¹³ |
| K2 | should-fix | yes (GPU 0) | v15's `gpu` check (1e-12 absolute on g) fails a correct GPU run: χ = 0.7, 75°, retrograde: 2.0·10⁻¹²; CPU and GPU differ by up to 1.3·10⁻¹¹ in g on whole screens |
| K3 | should-fix | yes (browser) | the image's brightness scale reads rows computed after the cursor when the history goes back through a key frame: up to 71× dimmer (edge-on), all sampled pixels changed |
| K4 | should-fix | — (text against the sources) | the M87* comparison mixes two δ: the world's shadow-size δ (Sgr A* Paper VI 2022 definition) against Paper VI 2019's mass-to-distance δ = −0.01 ± 0.17, in which every Kerr hole has δ = 0; and v15's interval [−0.18, 0.16] differs from the module's and Psaltis's ±0.17 |
| K5 | should-fix | yes | δ's centre is "as CHARM" in the docstring but is the midpoint of the extreme α; CHARM's variance-minimising centre lowers Kerr δ by 0.004 (M87 preset) to 0.053 (a = 0.998, 90°), outside Paper VI's Kerr range [−0.075, 0] |
| K6 | should-fix | yes | `check_regular` (A₁ > 0, A₂ > 0) admits Johannsen metrics whose determinant (Johannsen 2013a Eq. 72) vanishes outside the horizon; v15's slider ranges reach them (a = 0.998: every α₂₂ > 1.28) and their "shadows" are drawn and compared with EHT |
| K7 | should-fix | yes (browser) | the what-if world shows Kerr's photon orbits and ISCO as the hole's own ("3 … 3 M", "6 / 6 M" for α₁₃ = 3, whose photon sphere is at 3.30 M) |
| K8 | should-fix | yes (browser) | 3-D views: «Сверху — вдоль оси вращения» shows the disk edge-on; «От наблюдателя» looks along the spin axis from −z (the hemisphere opposite the observer), not along the line of sight; the spin axis is drawn horizontal |
| K9 | should-fix | yes | n is the number of equatorial crossings (GL-b's m̄), but v15 calls n = 1 "the lensing ring, after half an orbit": for observers ≳ 75° the direct image of the disk's lower face is n = 1 below the line of sight, and the same image is n = 0 at exactly 90° |
| K10 | should-fix | yes | revealed at t = 0 and closed form as the result: Bardeen's curve is drawn and the tracer's edge and δ are posted when an image starts, before its rows; the Kerr world's δ "этого мира" is the closed-form curve's, not measured on the computed image |
| K11 | should-fix | yes (fix verified in a copy) | `ellipf` loses accuracy near φ = π/2 as m → 1 (1 − m sin²φ formed with cancellation): 3.7·10⁻⁹ relative at m = 1 − 10⁻⁹, 2.7·10⁻⁶ at 1 − 10⁻¹³ (2·10⁴ × the stated bound); one-line fix gives 2·10⁻¹⁶ |
| K12 | should-fix | yes (mutations) | the tests do not pin the redshift of crossings after the radial turning point or the screen's vertical orientation: three wrong engines pass all 113 engine tests and 12 v15 tests |
| K13 | nit | yes | accuracy of `trace_back` near the axis (~u/θ_o in τ_n: up to 7·10⁻¹⁰ at θ_o = 10⁻⁴°) and of low-order crossings far out on rays within d ≲ 10⁻⁶ of the critical curve (3.3·10⁻⁸ at d = 10⁻¹²), beyond the tests' 64u-per-input claim |
| K14 | nit | — | citations and labels: Chael et al.'s redshift is Eq. (18), not (16); α₁₂ is not in Johannsen 2013a (Paper VI Eq. 17); EHT used i = 163° for a* > 0, not 17°; the README's a = 0 ring ratio |
| K15 | nit | — | the source model: no path-length / geometric factor per crossing (GLM: f = 1.5, Chael: 2/3) and g⁴ (bolometric) vs g³ (230 GHz) — choices that set the rings' brightness, not stated |
| K16 | nit | yes | checks that cannot fail on the tracer or are coarse: `schw` is an algebraic identity of the closed form; `pixels` skips √2 pixels around the curve |
| K17 | nit | yes (browser) | player and view details: `setLines` colours not converted sRGB → linear; «готово» styled as an error in three modes; hover lists crossings off the disk; `engine_modules` omits the module whose `shadow_size` a Kerr world uses; the edge-on preset's brightness map is almost black |

What holds (status tags per item) is listed after the findings; the main engine results are [useful]: the closed-form
tracer, the redshifts and the generic orbits agree with independent routes to 10⁻¹⁰–10⁻¹⁵, and the published EHT
bounds are reproduced.

---

## K1 (should-fix; reproduced): the `edge` check fails correct worlds

**Location.** `visualizations/v15_kerr_shadow/viz.py:313-323` (tolerance `64 * EPS`); README "Checks shown live",
row `edge` ("64 ε (round-off of the roots)").

**Case.** `c06_edge_check_scan.py` repeats the check exactly (8 directions kπ/4 from the screen origin,
`capture_boundary(rho_max=18)` against `critical_radius_at`) for χ ∈ {0.9, 0.95, 0.98, 0.99, 0.995, 0.998} and
θ_o = 1…179° in steps of 1° (1074 worlds) → `out/c06_edge_check_scan.txt`:

* χ = 0.998, θ_o = 81° and 99°: edge = 1.830·10⁻¹⁴ > 64 ε = 1.421·10⁻¹⁴ (direction k = 4, the flattened prograde side);
* the distribution of edge/ε: 787 below 4, 144 in [4, 8), 87 in [8, 16), 42 in [16, 32), 12 in [32, 64), 2 above 64.

`c06b_edge_world.py` builds these worlds as the server does: `ok = False` (`out/c06b_edge_world.txt`); the player shows
✗ (`out/shots/D_chi0998_81_checks_crop.png`). The engine is right: the unit test's derived tolerance
(test_kerr_shadow.test_shadow_edge_is_the_critical_curve: e_d/|∂d₃₄/∂ρ| + 10⁻¹³ρ + 2uρ + bracket) for the same
direction is 2.06·10⁻¹³, eleven times the value.

**Effect.** A correct run is marked failed; the tolerance is a round number, not derived (and 12 more worlds are within
a factor 2 of it).

**Fix.** Use the unit test's per-direction tolerance in the live check (it costs two extra root evaluations per
direction), and state it in the README.

## K2 (should-fix; reproduced on GPU 0): the `gpu` check fails a correct GPU run

**Location.** `viz.py:389-399` (`tol=1e-12`, absolute, and the finite/NaN pattern of the middle row must be identical);
README row `gpu` ("1e-12").

**Case.** `c09_gpu.py` (GPU 0, `out/c09_gpu.txt`):

* (b) v15 worlds forced to the GPU: χ = 0.7, θ_o = 75°, retrograde disk, 192²: `gpu` = 2.04·10⁻¹², ok = False. The
  presets at 256² pass (≤ 8.5·10⁻¹⁴).
* (a) whole 256² screens, CPU against GPU: fates identical, finite patterns identical, max |Δg| = 9.3·10⁻¹³ (χ = 0.9,
  60°), 1.27·10⁻¹¹ (χ = 0.5, 17°, a pixel farther than 0.05 M from the curve), max |Δr|/r = 7.3·10⁻¹².

The engine's own GPU test (`test_gpu_equals_cpu`) derives a tolerance from the closed form's sensitivities
(128u (|α ∂r/∂α| + |β ∂r/∂β| + |r|)) and compares pixels within 0.05 M of the critical curve by fate only; the live
check does neither, and its middle row crosses the curve, where the finite pattern can also legitimately differ.

**Fix.** The same derived tolerance for g (central differences on the CPU row), fate-only near the curve.

## K3 (should-fix; reproduced in the browser): the brightness scale reads the future after going back

**Location.** `v15_kerr_shadow/web/view.js:88-90` (`Imax` = the largest `img.I` over the whole array) with
`restore(k)` at `:156-160` (a key frame cuts `im.rows` back but keeps the arrays of the rows received later); the same
`Imax` scales the "order" mode.

**Case.** `c08c_browser.mjs` (the player's test option `?key_every=3`, so that going back is served by a key frame as it
is in any run with ≥ 100 messages before the cursor; `out/c08c_browser.txt`): the scan paused at a quarter or so of the
rows, the canvas sampled, scanned to the end, the cursor moved back to the paused frame:

| world | rows shown | max I of the rows shown | max I held after going back | sampled pixels drawn differently |
|---|---|---|---|---|
| m87, t = 0.50 | 25 | 0.0106 | 0.0187 | 1152 of 1152, all dimmer |
| m87, t = 1.20 | 58 | 0.0158 | 0.0187 | 2644 of 2688 |
| edge_on, t = 1.19 | 58 | 0.0501 | 3.56 (×71) | 2310 of 2688 |
| ring, t = 1.19 | 58 | 1.48 | 2.16 | 551 of 2688 |

With a full rebuild (`c08b_browser.mjs`: m87 and edge_on, `full` rebuilds) the view is right, so the error depends on
how the player reached the time (key frame vs rebuild). Screenshots: `out/shots/B_live_paused.png` against
`out/shots/B3_m87_back_keyframes.png`, `B3_edge_on_back_keyframes.png`.

**Effect.** The image at the cursor is drawn with the brightness of rows the run computed later (RULES: what the cursor
shows is "exactly as it was then"; same class as B4-10).

**Fix.** Take `Imax` over the rows `j < img.rows` only (or let `restore` truncate the arrays).

## K4 (should-fix): the M87* comparison mixes two definitions of δ

**Location.** `viz.py:349-362` (the `eht` check: label "δ = d/(6√3 M) − 1 этого мира против EHT −0.01 ± 0.17", note
"δ по определению EHT (Paper VI 2022: отклонение диаметра тени от шварцшильдовского); масса по звёздам (Paper VI): δ =
−0.01 ± 0.17"); README row `eht`; `core/data.py:109-113`.

**The sources.** M87* Paper VI (2019), Sec. 9.5: "we can, therefore, measure the fractional difference δ between the
predicted and measured mass-to-distance ratio", Eq. (31) δ ≡ θ_g/θ_dyn − 1, "We find δ=−0.01±0.17 (68% credible
intervals) for the stellar and δ=0.78±0.3 for the gas dynamics priors". θ_g was inferred from the ring with the Kerr
GRMHD calibration, so a Kerr hole of any spin has δ = 0 in this definition. Sgr A* Paper VI (2022), Sec. 3: "The
quantity δ ≡ (dsh/dsh,Sch) − 1 ... dsh,Sch = 6√3 θg", "values of δ in the range [−0.075, 0] are consistent with the
Kerr predictions", and "We also note the small differences in the definitions of these quantities with respect to
earlier work (see, e.g., Event Horizon Telescope Collaboration et al. 2019c ...), which simply scaled the image diameter
to θg". Psaltis et al. 2020 use the 2019 result only as "consistent to within 17%" (no centre value) — the module's
`eht_delta_bounds` takes ±0.17.

**Case.** The M87 preset shows δ = −0.0523 (the 2022 definition, a Kerr shadow 5 % smaller than Schwarzschild's)
"against −0.01 ± 0.17" (the 2019 definition, where this hole is δ = 0). The interval also differs from the module's:
with v15's [−0.18, 0.16], α₁₃ ∈ [−3.711, 5.463]; with ±0.17, [−3.557, 5.888] (Psaltis: "−3.6 < α13 < 5.9";
`out/c05_johannsen.txt`). A what-if world with α₁₃ = 5.6 (δ = 0.163) is shown outside the M87* interval although it is
inside the published bound. STATUS V35 (g) records the data-level caveat; the visualization's label states the opposite
("по определению EHT (Paper VI 2022)").

**Fix.** For M87*, show the deviation of the world's shadow from the Kerr shadow of the same spin and inclination
(δ − δ_Kerr) against ±0.17 (Psaltis's use), with the definition named; use one interval in the module and the view.

## K5 (should-fix): δ's centre is not CHARM's

**Location.** `theories/alternatives/johannsen_metric.py:213-232` (`shadow_size`: "the centre (half-way between the
extreme alpha ...), the median diameter (twice the median radius over n_angles equally spaced directions, as CHARM, EHT
2022 Paper VI Sec. 3)").

**The source.** Sgr A* Paper VI Sec. 3: CHARM "(i) chooses a trial center ... (iii) ... identifies the ring diameter as
two times the median value of this distance; (iv) iterates the location of the trial center and steps (i)−(iii) such
that the variance in the diameter along different cross sections is minimized"; Sec. 5.1: "As was done in Section 3 we
define the size of a shadow as its median radius"; Eq. (14) "δmetric = d̃metric/(6√3) − 1, where d̃metric is the median
shadow diameter".

**Case.** `c05_johannsen.py` (d): the critical curve's δ with the module's centre and with the centre that minimises the
variance of the 64 chord lengths through it (Nelder–Mead; the minimum is sharp: for a = 0.5, 30° the variance is
6.6·10⁻⁸ at α = 0.974 against 2.2·10⁻⁴ at the module's centre 0.514, `c05b_charm_variance.py`):

| Kerr | δ (module) | centre | δ (CHARM centre) | centre | difference |
|---|---|---|---|---|---|
| a = 0.5, 30° | −0.0128 | 0.514 | −0.0148 | 0.974 | −0.002 |
| a = 0.9, 17° (M87 preset) | −0.0523 | 0.600 | −0.0563 | 1.225 | −0.004 |
| a = 0.9, 60° | −0.0380 | 1.747 | −0.0656 | 3.212 | −0.028 |
| a = 0.998, 60° | −0.0590 | 2.157 | −0.1057 | 3.842 | −0.047 |
| a = 0.998, 90° | −0.0530 | 2.443 | −0.1057 | 4.214 | −0.053 |

The module's centre reproduces Paper VI's Kerr range (its δ over a ≤ 0.998, 1–90°: [−0.0704, 0.0000]) and the
non-spinning bounds (circles, where the centre does not matter); with CHARM's centre high-spin Kerr shadows fall to
−0.106. The effect is of the size of the Sgr A* error bars (±0.09).

**Fix.** Name the convention (midpoint of the extreme α) and that it reproduces Paper VI's Kerr range; drop "as CHARM",
or report both.

## K6 (should-fix): `check_regular` admits singular Johannsen metrics

**Location.** `johannsen_metric.py:91-98` (A₁ > 0 and A₂ > 0 on r ≥ r₊), `:54` (validity "метрика регулярна вне
горизонта при A₁ > 0, A₂ > 0 для r ≥ r₊ (Johannsen 2013a, ур. 77–78)"); v15's ranges `viz.py:52-57` (α₁₃ ∈ [−10, 10],
α₂₂ ∈ [−3, 10], α₁₂ ∈ [−3, 10] at any spin up to 0.998).

**The source.** Johannsen 2013a Sec. B: the determinant (Eq. 71) "det(gαβ) = −Σ̃⁴ sin²θ / [A5(r)(A1(r)(r²+a²) −
a²A2(r) sin²θ)²]"; "I impose the requirement A1(r)(r²+a²) − a²A2(r) sin²θ ≠ 0, (72) ... which must be fulfilled
everywhere on and outside of the event horizon"; and (76) "A1(r)²(r²+a²)² − a²∆ sin²θ > 0". Eqs. (77)-(78) are these
conditions "at lowest order" with r = r₊ inserted.

**Case.** `c05_johannsen.py` (c) (`out/c05_johannsen.txt`): `check_regular` passes and Eq. (72) fails (sin²θ = 1) for
a = 0.998 with α₂₂ = 1.5, 2, 5, 10 (the condition with α₁₂ = α₁₃ = 0 is α₂₂ < r₊⁴/a² = 1.283), a = 0.9 with α₂₂ = 10
(limit 5.25), and α₁₃ = −0.95 r₊³ or α₁₂ = −0.95 r₊² at a = 0.6, 0.9, 0.998. For each, `shadow_curve` returns a curve
and δ (e.g. a = 0.998, α₂₂ = 2: δ = −0.117), which v15 would draw and compare with EHT as a regular "what if".

**Fix.** Check (72) and (76) numerically on r ≥ r₊ at sin²θ = 1 (both are worst there for A₂ > 0) in `check_regular`;
state the domain in the validity text and in v15's parameter help.

## K7 (should-fix; seen in the browser): the what-if world shows Kerr's orbits as the hole's own

**Location.** `viz.py:482-484` (header `hole`: `kerr.isco`, `kerr.photon_orbit`), `:285-286` (the 3-D rings),
`view.js:126-131` (panel «Чёрная дыра»).

**Case.** The what-if preset (a = 0, α₁₃ = 3): the panel shows «фотонные орбиты в экваторе 3 … 3 M», «ISCO 6 / 6 M»
(`out/shots/D_whatif_page.png`) and the 3-D scene draws the r = 3 M photon orbit; this metric's photon sphere is
r_ph = 3.300 M (`JP.nonspinning_shadow`: b_c = 5.697 M), and its circular orbits differ too (g_tt = −(1 − 2/r)/A₁²).

**Fix.** In a modified world show the deviating metric's photon orbits (`JP.photon_shell` / `nonspinning_shadow`) or
label the Kerr values as "Kerr, for comparison"; omit the ISCO if the module does not compute it.

## K8 (should-fix; seen in the browser): the 3-D views do not show what their names say

**Location.** `viz.py:462-463` (header views: «Сбоку — диск с ребра», «Сверху — вдоль оси вращения», «От наблюдателя —
вдоль оси z»); `player/js/scene3d.js:15` (`P2T`: physics (x, y, z) → three (z, y, −x)) and `:853` (fixed camera
directions in three's frame: top [0.001, 1, 0], beam [−1, 0, 0], side [0, 0, 1]).

**Case.** Physics z is the spin axis. "top" looks along physics +y: the disk edge-on (`out/shots/C_view_top.png`).
"beam" (named «От наблюдателя») looks along physics z from −z (`out/shots/C_view_beam.png`: x to the left, y up, so z
points away from the viewer): the face of the disk from below, the hemisphere opposite an observer at θ_o < 90°, i.e. a
mirror image of what the observer sees, and not at the observer's inclination. Three's up is physics y, so in every view
the spin axis lies horizontal (`out/shots/A_m87_page.png`: the disk stands vertical).

**Fix.** Let a world give its view directions (or an "up" axis); for v15 a view along n = (sin θ_o, 0, cos θ_o) with
the spin's projection up, which then matches the screen window.

## K9 (should-fix): n is the crossing count, not half-orbits

**Location.** `kerr_shadow.py:9-10` ("n counts half-orbits: n = 0 the direct image of the disk, n = 1 the lensing ring,
n >= 2 the photon ring; Johnson et al. 2020; GL-b Eqs. 81-82"); `viz.py:7-10`, header text, `view.js:12, 136-137`
(«после пол-оборота вокруг дыры (кольцо линзирования, n = 1)»), README.

**The source.** GL-b after Eq. (82): m̄ labels equatorial crossings; "Even m̄ corresponds to emission towards the
observer (i.e., from the front of an equatorial disk), while odd m̄ corresponds to emission away from the observer
(i.e., from the back of a disk)"; footnote 15: "If θo = π/2 exactly, then Fo vanishes and this jump does not occur. We
have excluded this degenerate case". Johnson et al.'s n counts half-orbits.

**Case.** `c13_order_labels_edge_on.py` (a = 0.99, `out/c13_order_labels_edge_on.txt`): for rays below the line of
sight the first crossing lies at r ≈ |β|/cos θ_o, beyond the disk (20 M) once θ_o ≳ 75°; the near-hole image (the
disk's lower face seen directly, less than half an orbit) is then n = 1:

| pixel (α, β) | 75° | 89° | 89.9° | 90° |
|---|---|---|---|---|
| (0.5, −6) | n0 r = 23.2, n1 r = 5.48 | n0 343.8, n1 4.99 | n0 3438, n1 4.97 | n0 4.97 |
| (3, −4) | n0 15.7, n1 1.50 | n0 229, n1 1.80 | n0 2292, n1 1.82 | n0 1.82 |

The brightness is the same, but the "order" map colours this image as «кольцо линзирования» and the hover text says
"после пол-оборота"; at exactly 90° (the edge-on preset) the same image is n = 0, so the map jumps between 89.9° and
90°.

**Fix.** Describe n as GL-b's m̄ (crossings; odd = the disk's far / lower face) or count half-orbits (polar turning
points) for the labels; say that n = 1 is a thin ring only for moderate inclinations.

## K10 (should-fix): revealed at t = 0; the closed form shown as the result

**Location.** `viz.py:150-173` (`_new_image`: the `curve` message with Bardeen's curve, and `_shadow_checks` — the
tracer's edge, the ring images, δ against EHT — at t = img_t0), `view.js:47-59` (the curve drawn over the screen as
soon as it arrives), `viz.py:346` (δ from `self.curve`, the closed form).

**Case.** In every image the dashed critical curve and the δ comparison appear at the image's first instant, while the
image itself is revealed over 4 M (`out/shots/B_live_paused.png`: 51 of 192 rows computed, the whole curve drawn). The
Kerr world's δ «этого мира» is computed from the closed-form curve, not from the run's ray-traced shadow; the run
computes the shadow edge (`capture_boundary`) only in 8 directions, for the `edge` check. AGENTS.md §3 rules 2–3:
"Closed forms of the known theory appear only as references in the run's checks, next to the computed value";
"Consequences are revealed when the run's time reaches them". (The B4 review's B4-5 was the same kind.)

**Fix.** Post the curve, `edge`, `lyapunov` and `eht` when the scan completes (or the curve's parts as the rows reach
them); measure the Kerr world's δ on the tracer's edge (128 directions of `capture_boundary`) with the closed-form δ as
its reference.

## K11 (should-fix; fix verified in a copy): `ellipf` near φ = π/2 as m → 1

**Location.** `core/elliptic.py:96`: `f = s * rf(c * c, 1.0 - m * s * s, ...)`. DLMF 19.25.5 has R_F(cos²φ,
1 − k² sin²φ, 1); for m → 1 and φ → π/2 the second argument is formed by cancelling m sin²φ against 1, with absolute
error ~u against a value ~(1 − m) + cos²φ.

**Case.** `c01b_ellipf_corner.py` (`out/c01b_ellipf_corner.txt`), mpmath at 40 digits, same binary64 inputs:

| m | φ | relative error | error / stated bound (test_elliptic) |
|---|---|---|---|
| 1 − 10⁻⁶ | π/2 − 10⁻⁴ | 1.1·10⁻¹² | 12 |
| 1 − 10⁻⁹ | π/2 − 10⁻⁶ | 3.7·10⁻⁹ | 1.9·10³ |
| 1 − 10⁻¹² | π/2 − 10⁻⁶ | 9.1·10⁻⁷ | 1.9·10⁴ |
| 1 − 10⁻¹³ | π/2 − 3·10⁻⁹ | 2.7·10⁻⁶ | 2.0·10⁴ |

The test draws m ≤ 0.999999 only. This is the regime of the radial antiderivative of near-critical rays (k → 1, phase
→ π/2). With `c * c + (1.0 - m) * s * s` (a copy of the engine, `out/c01b_ellipf_corner_with_fixed_copy.txt`) the
errors are ≤ 2.2·10⁻¹⁶ and `c01_elliptic_stress.py` passes everywhere (`out/c01_elliptic_stress_with_fixed_ellipf_copy.txt`,
against `out/c01_elliptic_stress.txt`: 1.2·10³ and 1.1·10⁵ × the bound at m = 1 − 10⁻⁹, 1 − 10⁻¹³). The tracer's r_n
did not change measurably with the fix (`out/c02_table_with_fixed_ellipf_copy.txt`): K13 (b) dominates there.

**Fix.** The one-line change and test points with m ∈ [1 − 10⁻¹⁴, 1 − 10⁻⁶] and φ near π/2.

## K12 (should-fix; reproduced): the tests do not pin two things the image depends on

**Case.** `c10_mutations.py` applies each change to a copy of `lfphys` and runs `test_kerr_null`, `test_kerr_shadow`,
`test_johannsen_metric`, `test_kerr_orbits` and v15's tests (`out/c10_mutations.txt`, `out/c10b_which_tests.txt`):

| mutation | engine tests | v15 tests |
|---|---|---|
| M1: p^r of every crossing outward (`kr = +1`) | 113 passed | 12 passed |
| M10: the radial turning time 10 % early (`tau_turn = 0.9 I∞`) | 113 passed | 12 passed |
| M6: the screen's rows reversed (image upside down) | 113 passed | 12 passed |
| M2 (no H(β)), M3 (radial redshift sign), M4 (γ × 2), M5 (screen mirrored left–right), M7 (Keplerian gas inside the ISCO), M8 (JP: sign of A₂′), M9 (plunge constants of 1.05 r_isco) | caught | M4 caught, the rest pass |

M1 and M10 change g only where the gas moves radially (Cunningham's plunge) and the crossing follows the turning point;
M6 swaps the lensed far side of the disk to below the shadow. The present code is right on all three: `c03` (below)
reproduces g_n and r_n of 98 pixels from an independent route to 4.7·10⁻¹² and 7.8·10⁻¹¹, and the browser check
finds the approaching side on the left (`c08`). Also, `test_screen_rays_match_the_hamiltonian_route_from_far_away`
allows 10⁻⁵ because it starts the comparison ray at θ_o instead of θ_o − β/r₀; started there (c03) the two routes agree to
8·10⁻¹¹.

**Fix.** A test like c03 (Hamiltonian route with crossing events, g from p·u with the emitter built from the metric),
covering crossings after the turning point inside the ISCO; an orientation test (e.g. at θ_o = 60° the far side of the
disk is imaged above the shadow, β > 0, and the approaching side at α < 0); tighten the far-start test.

## K13 (nit; reproduced): accuracy beyond the tests' range

`c02_hard_rays.py` compares `trace_back` with a 40-digit route that uses no elliptic function and no Ferrari formula
(polar Mino time by quadrature; the radial Mino time to the engine's r_n by quadrature with the substitutions r = r₄ + s²
and u = 1/r; the r error is Δτ·√R), at the engine's own binary64 (λ, η), so input rounding is not counted
(`out/c02_hard_rays.txt`, tables `out/c02_table.txt`, `out/c02_table_regular_observers.txt`).

* (a) Near the axis. θ_o = 10⁻⁴°: every τ_n is off by 10⁻¹¹–7·10⁻¹⁰ relative (r_n up to 1.8·10⁻⁹), independent of d.
  Cause `kerr_null.py:380`: F_o = F(arcsin(cos θ_o/√u₊)) with cos θ_o/√u₊ = 1 − O(θ_o²) for every ray of a near-axis
  observer; the arcsin turns its rounding into ~u/θ_o. At v15's 1° that estimate is ~6·10⁻¹⁵ (no effect). Fix: ψ_o =
  atan2(cos θ_o/√u₊, sin θ_o |β| / √(u₊ (A_m + a² cos²θ_o))), which follows from (1 − u)Θ = a²(u₊ − u)(u − u₋) with
  Θ(θ_o) = β².
* (b) Grazing rays. For θ_o ≥ 17° and |d| ≥ 10⁻³ every r_n (n ≤ 3) is within 3.4·10⁻¹² (n = 1: 1.4·10⁻¹³). The growth with n at
  d ≤ 10⁻⁹ (n = 8: 1.7·10⁻⁴ at d = −10⁻¹²) is the problem's conditioning. But the n = 0 crossing far out on a grazing ray
  is well conditioned and still loses accuracy: χ = 0.9999, 89.9°, r₀ = 2893 M: 9·10⁻¹¹ (d = 10⁻⁶), 2.7·10⁻⁹ (10⁻⁹),
  3.3·10⁻⁸ (10⁻¹²). Cause: the phase arcsin(√(r₃₁/r₄₁)) at r = ∞ is computed from a ratio → 1 as r₃ → r₄
  (`kerr_null.py:260`), then subtracted in X = rate·(τ − I∞) (`:329`) with τ ~ 1/r small. No pixel comes within 10⁻⁶ of the
  curve except by chance, so the images are not affected. Fix (optional): phase = atan2(√r₃₁, √r₄₃) with r₄₃ = 2 s₃₄
  taken from the root solver, and state the tests' "64u per input" as valid for d ≳ 10⁻⁶.

## K14 (nit): citations and labels

* `kerr_shadow.py:22` and `sources/verification_2026-10-29_p7_kerr.md:76` cite the redshift as Chael et al. 2021
  Eq. (16); in arXiv:2106.00683 it is Eq. (18) ("g = −k_t/(k_μ u^μ) = 1/(u^t − λu^φ ± u^r √R/Δ)"); Eq. (16) is the
  intensity sum "I(α, β) = Σ f_n j_model(r_n) g³(r_n, α, β)".
* `johannsen_metric.py` docstring: "The metric (Johannsen 2013a Eqs. 51-56): ... A1(r) = 1 + alpha12/r^2 + alpha13/r^3".
  Johannsen 2013a Eq. (52) starts A₁'s series at n = 3 ("A1(r) = 1 + Σ_{n=3} α1n (M/r)^n"); α₁₂ is the 1PN term of Sgr A*
  Paper VI Eq. (17) ("Σ_{i=2}"). Cite that for α₁₂ (its regularity conditions are the analogues, not Johannsen's).
* v15's inclination help «17° — наклон джета M87* (так EHT сравнивал свои снимки)» and the M87 preset (a = 0.9, 17°):
  EHT M87* Paper V used "i=17° for a* ≤ 0 and 163° for a* > 0" (Fig. 8 caption; the ≤ is a glyph in the PDF text),
  and Chael et al. 2021 "θo = 163 deg" for a* = 0.9375.
  δ is the same; the image is flipped top–bottom relative to the spin's projection.
* README "Measured on the presets": "0.04317 against e^(−π) = 0.04321 (a = 0.99 edge-on, the equatorial orbit; a = 0)"
  — the a = 0 preset gives 0.042968 (`out/c04_viz_checks_grid.txt`); worth adding that γ = π holds for the circular
  equatorial photon orbits at every spin (the a = 0.99 reference is e^(−π) exactly), which is why both share the reference.

## K15 (nit): the source model's choices that set the rings' brightness

`viz.py:9-11`, README "The model": the pixel brightness is Σ_n g_n⁴ J(r_n). GLM 2020 (Eq. 6–7) use "Iobs = Σ fm [g]⁴
Iem(rm)" with "fm = 1 (m = 0), f (m > 0)", a fudge factor for the geometric thickness (their fiducial f = 1.5); Chael et
al. 2021 use g³ (230 GHz specific intensity, flat spectrum) and f_n = 2/3 for n > 0. The model here is f = 1 with g⁴, i.e. a
surface brightness per crossing independent of the photon's angle to the disk. That is a legitimate choice, but it sets
the n ≥ 1 rings' brightness relative to the direct image; the README should state it (and that a thin optically thin
layer would weight each crossing by its path length).

## K16 (nit): checks that cannot fail on the tracer, coarse margins

* `schw` (`viz.py:342-345`): the median of √(α² + β²) of the closed-form curve against √27. At a = 0, α² + β² = λ² + η
  = 27 identically for `critical_constants_t`; the tracer is not involved.
* `pixels` (`viz.py:383`): pixels within √2 pixel sizes of the curve are skipped (2.5 % of a 192² image); the edge is
  point-sampled, so 10⁻⁴ M (the unit test's margin) suffices and would also test an error in the shadow's size below
  1.4 pixels.

## K17 (nit): player and view details

* `scene3d.js:1002-1017` `setLines` passes the 0..1 colours as linear vertex colours; `setMesh` (`:457`) converts
  sRGB → linear. The rays' red/yellow/blue (`viz.py:261`) render visibly paler than the legend names
  (`out/shots/A_m87_page.png`).
* `imagewin.js:93`: the status span gets class `st-bad` (the error style) whenever the mode is not "seen": «готово: 192 ×
  192» appears red in the order, redshift and fate modes (`out/shots/A_m87_order.png`).
* `view.js:25-28` (hover): every crossing is listed as «диск при r = …», also beyond the disk (r > 20 M, e.g. r = 1146 at
  89.9°) and inside the ISCO of a Keplerian disk (shown with g = 0).
* `viz.py:452-456`: a Kerr world's `engine_modules()` omits `theories.alternatives.johannsen_metric`, whose
  `shadow_size` produces its δ (`viz.py:346`); a core world's measure then lives in an alternatives module (it is
  geometry; `core` or `tools` would fit).
* The edge-on preset (a = 0.99, 90°) in the brightness mode: the scale is set by one Doppler-boosted pixel, and the rest
  of the image is near black (`out/shots/D_edge_on_page.png`); the flattened shadow named in the preset's label is
  visible only through the dashed curve.

---

## What holds (checked)

* **Formulas against the sources** [useful]. GL-b Eqs. (55)-(59) (screen; "λ = −α sin θo, η = (α² − a²) cos² θo + β²",
  brackets confirmed), (56) "±o = sign(β)", (81) "√(−u− a²) Ir + sign(β)Fo = 2mK", (82) "m̄ = m − H(β)", (38)-(39) the
  critical constants, (43)-(44) γ = 4r̃√χ̃ K̃/(a√−ũ−) per half-orbit (footnote 9) — all as implemented. Johnson et al.
  2020 Eqs. (4), (8), (29) and "For Schwarzschild, γ = π". The projected rotation is "counterclockwise as seen by the
  observer" (GL-b) and the approaching side is at α < 0: the image agrees (`c08`: brightness left/right 198/98 in the
  data, 1.58 drawn; mean g of the direct image 0.77 vs 0.65). Schmidt and Fujita–Hikida: through c07's independent
  quadratures. Johannsen 2013a Eqs. (23)-(25) (R(r), and Θ reduces to Kerr's with A₃ = A₄ = 1, so Bardeen's screen
  coordinates hold), (77)-(78) as quoted (but see K6). The EHT block of `core/data.py`: every number checked against
  the text — M87* "42±3 μas", "M=(6.5±0.7)×10⁹", "θg=3.8±0.4 μas", "16.8±0.8 Mpc", "δ=−0.01±0.17 ... δ=0.78±0.3"; Sgr
  A* Table 2 eht-imaging/GRMHD "VLT(I) −0.08 +0.09/−0.09", "Keck −0.04 +0.09/−0.10", Eqs. (12)-(13) "3√3(1 − 0.14)M ≲
  r̃sh ≲ 3√3(1 + 0.05)M", "3√3(1 − 0.17)M ≲ r̃sh ≲ 3√3(1 + 0.01)M", Sec. 2.1 θ_g values, Table 3 "−1.1 ≲ α12 ≲ 0.5",
  "−3.1 ≲ α13 ≲ 1.5"; Psaltis "−3.6 < α13 < 5.9", Eq. (8).
* **The image pipeline end to end** [useful] (`c03_redshift_end_to_end.py`, `out/c03_redshift_end_to_end.txt`): 98
  pixels (a = 0.3–0.998; 17°, 45°, 60°, 75°, 89°, 163°; Keplerian and Cunningham; prograde and retrograde) against the
  reviewer's own route — Hamilton's equations with the reviewer's inverse metric and complex-step derivatives, started
  at r₀ = 10⁷, θ_o − β/r₀; the gas from Ω = ±1/(r^1.5 ± a) and the metric's normalisation, the plunge from the ISCO's
  u_t, u_φ raised by the metric (r_isco found as the minimum of E(r)); g = 1/(−p·u): fates identical, r_n within
  7.8·10⁻¹¹, g_n within 4.7·10⁻¹². GLM App. B (B9)-(B14) agree with the reviewer's plunge to 6·10⁻¹⁰ (limited by the
  reviewer's r_isco), (B7) with the engine's Keplerian g to 7.6·10⁻¹⁵, and Ω from the metric's derivatives with the
  engine's to 4·10⁻¹⁶ (`c11`).
* **Grazing rays and turning points** [useful] (`c02`): see K13 for the limits; for θ_o ≥ 17° and |d| ≥ 10⁻³ every
  r_n (n ≤ 3) within 3.4·10⁻¹², through the turning points (crossings after the turn included).
* **The shadow's edge** [useful]: the tracer's edge equals Bardeen's curve to ≤ 1.8·10⁻¹⁴ relative in all 1074 worlds of
  c06 (well within the derived tolerance; K1 is about the live check's constant only). The Johannsen edge from
  R = R′ = 0 against an independent bisection on the fate decided by R_JP itself (largest root outside the horizon):
  2–4·10⁻⁶ (the reviewer's grid and the 1441-point polygon), for six deviating metrics at a = 0.3–0.95 (`c05` (b)).
* **The published bounds reproduced** [useful] (`c05` (a)): α₁₃ ∈ [−3.557, 5.888] (|δ| ≤ 0.17), α₁₃ ∈ [−3.063, 1.455],
  α₁₂ ∈ [−1.144, 0.465] (Keck); Psaltis Eq. (8) to 9·10⁻¹³ at α₁₃ = ±10⁻³. Kerr δ over a ≤ 0.998, 1–90°: [−0.0704, 0]
  (Paper VI: [−0.075, 0]).
* **Generic orbits** [useful] (`c07_kerr_orbits_hard.py`, comparison image): 14 harder orbits (near the separatrix at
  a = 0.998 and 0.99, e = 0.9 retrograde, nearly polar and polar, circular inclined, a = 10⁻⁴, p = 10³ and 10⁵, e = 0.95,
  equatorial): constants within 2·10⁻¹⁵ except at large p (p = 10³: 1.4·10⁻¹³; p = 10⁵: L, Q 4–9·10⁻¹², as
  conditioned), the four Mino frequencies of both routes within 4·10⁻¹² of 40-digit quadratures near the separatrix,
  10⁻¹¹ at p = 10⁵ (KerrGeoPy: the same), ≤ 10⁻¹² elsewhere, including the polar orbits KerrGeoPy refuses. The KerrGeoPy suite: 1057 passed (`out/t01_ext_kerrgeopy.txt`).
* **Elliptic functions** [useful] apart from K11: sn, cn, dn within 0.11 of their stated bound for |u| ≤ 1000, m up to
  1 − 10⁻¹⁵ and down to −10⁶; R_F over 10⁻²⁰⁰…10²⁰⁰ within 0.16 of 32u (`c01`).
* **v15 on a grid** [useful] (`c04`): 240 worlds (a = 0…0.998 × 10 inclinations × both gases × both directions) and the 6
  presets built, scanned and checked: no failed check except K1's worlds (found by the denser c06); screens 4–30 M and
  256² (`c12`); the README's preset numbers reproduced (edge 1.7·10⁻¹⁶–7.9·10⁻¹⁶, ratio 0.0601/0.0607 and
  0.04317/0.04321, δ = −0.0523, what-if δ = 0.0963). Tests: in-scope engine tests 128 passed, 1 skipped (CPU); v15 and its
  checkpoint/restore tests 14 passed (`out/t00`, `out/t02`).
* **GPU** [useful] (`c09`): whole 256² screens identical in fate and crossings, r within 7.3·10⁻¹² (K2 is about the live
  check's tolerance only); 49 ms per 256² screen after the first call.

## Scripts and outputs

All scripts name their root and how to run them in their header (engine at `/lf`, this folder mounted read-write at
the same path). Outputs in `out/`, screenshots in `out/shots/`.

| script | what | output |
|---|---|---|
| `c01_elliptic_stress.py`, `c01b_ellipf_corner.py` | elliptic functions beyond the tests' ranges; the F corner (K11) | `out/c01_*.txt` (also against the patched copy) |
| `c02_hard_rays.py`, `c02_table.py` | grazing, near-axis, edge-on, large-screen rays against a 40-digit quadrature route (K13) | `out/c02_*.txt` |
| `c03_redshift_end_to_end.py` | r_n, g_n against an independent Hamiltonian route and emitter | `out/c03_redshift_end_to_end.txt` |
| `c04_viz_checks_grid.py` | v15 presets and a 240-world grid through the harness | `out/c04_viz_checks_grid.txt` |
| `c05_johannsen.py`, `c05b_charm_variance.py` | published bounds, independent JP edge, regularity (K6), δ centre (K5) | `out/c05_johannsen.txt`, `out/c05b_charm_variance.txt` |
| `c06_edge_check_scan.py`, `c06b_edge_world.py` | the `edge` check over 1074 worlds; the failing worlds built (K1) | `out/c06*.txt` |
| `c07_kerr_orbits_hard.py` | generic orbits against 40-digit quadratures and KerrGeoPy | `out/c07_kerr_orbits_hard.txt` |
| `c08_browser.mjs`, `c08b_browser.mjs`, `c08c_browser.mjs` | the player: orientation, modes, views (K8), history and key frames (K3), what-if (K7), failing edge (K1) | `out/c08*.txt`, `out/shots/` |
| `c09_gpu.py` | GPU 0 against CPU; the `gpu` check (K2) | `out/c09_gpu.txt` |
| `c10_mutations.py` | negative controls in copies (K12) | `out/c10_mutations.txt`, `out/c10b_which_tests.txt` |
| `c11_keplerian_sources.py` | Ω from the metric; GLM (B7) | `out/c11_keplerian_sources.txt` |
| `c12_screen_sizes.py` | v15 at 4 and 30 M, 256² | `out/c12_screen_sizes.txt` |
| `c13_order_labels_edge_on.py` | crossing order near edge-on (K9) | `out/c13_order_labels_edge_on.txt` |
