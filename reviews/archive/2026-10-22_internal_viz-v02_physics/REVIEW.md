# Physics review of `visualizations/v02_double_slit` (internal, independent lens)

**Status: awaiting processing.** Reviewer: Claude (Opus) subagent, physics lens, 2026-10-22. The reviewer does not
process this review, writes no `RESPONSE.md` and does not archive it (`reviews/README.md`).

**Object.** `visualizations/v02_double_slit/`: `engine/*.py`, `viz.py`, `web/view.js`, `tests/`, and the folder
`README.md`, which appeared during the review (16:24). Context: `visualizations/server/lfviz/`, `visualizations/RULES.md`.
Line numbers refer to the files whose SHA-256 are in `out/00_sha256_reviewed_files.txt` (snapshot 16:58; re-verified
unchanged at 19:12). The snapshot already contains the four non-physics edits of 16:28 that the main session listed:
stories sent when t_det is reached, the `flight` blob, `next_event_time` (next emission or detection), and the
incremental histogram in view.js. Findings R4 and R23 touch those places and were checked against that code.

**Environment.** Docker image `light-funnel-viz:latest` (Python 3.11, numpy 2.x, scipy, mpmath), CPU only, GPU unused.
Every script runs from the light-funnel root as

```
docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
   light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v02_physics/<script>.py [args]
```

Each script's output is in `out/`. The project's own suite passes: `out/00_pytest_v02.txt` (44 passed, 32 s).

| script | what it checks | output |
|---|---|---|
| `01_fresnel_rs.py` | Fresnel closed form and derivative vs brute-force quadrature; Parseval; RS kernel sign and magnitude; Hankel asymptotics | `out/01_fresnel_rs.txt`, `out/01b_leggauss_timing.txt` |
| `02_marks.py` | Jones and spin matrices, Stokes labels, state sampling, Englert V and D, readout completeness | `out/02_marks.txt` |
| `03_grw.py` | GRW per-hit average; GRW hits during the flight (exact kick representation) vs the engine | `out/03_grw.txt` |
| `04_particles_ab_probe.py` | kinematics vs 50-digit mpmath; Aharonov–Bohm phase for any charge; probe polarisation; GRW nucleon count; flight time | `out/04_particles_ab_probe.txt` |
| `05_statistics.py` | Monte-Carlo noise of the expectation, χ² power, check tolerances, sampler vs rebinning | `out/05_statistics.txt` (part (c) aborted on a `None` from the fit, superseded by 05b) |
| `05b_statistics_fit.py` | histogram coherence fit (bias, failures, error) vs a constrained Poisson-ML fit; dark counts; seed scatter; grid cap | `out/05b_statistics_fit.txt` (part (c)), `out/05b_statistics_fit_part2.txt` (`--skip-c`, parts (d)–(f)) |
| (note) | `out/05b_statistics_fit.txt` was written before the `--skip-c` switch and the `None`-safe print in part (d) were added; it ends in a traceback at dark 500/s (the fit returned `None`). The part (c) code is unchanged. | |
| `05c_seed_check.py`, `05d_expected_fit_stability.py` | independence of seeds; stability of the expected-curve fit and of the run's coherence check over 20 seeds | `out/05c_*.txt`, `out/05d_*.txt` |
| `06_viz_consistency.py` | map and flow lines vs the run's ensemble; browser rebinning; filter curves; apparatus change in flight; Born exponent and no-signalling; flow-line velocity | `out/06_viz_consistency.txt` |
| `07_numerics.py`, `07b_map_vs_rs.py` | grid resolution; RS quadrature cost; near-field map vs exact RS; segment cost for 12 slits | `out/07_numerics.txt`, `out/07b_map_vs_rs.txt` |

## Summary verdict

The wave engine is correct where I could test it. The closed-form Fresnel amplitudes, their x-derivative, the
point-source, tilt and kick terms and Parseval agree with independent quadrature to 1e-13. The marks algebra
(Jones and spin matrices, the detector qubit, readout completeness, Englert's V and D) is right, and the per-particle
causal chain is mostly sound. The observer effect comes only from the marks, kicks and the declared modifications.

The visualization does **not yet meet** the owner's requirements ("точно выверены", "результат из расчетов текущего
запуска", "четкие причинно-следственные связи"). The **6 errors** are:

* the GRW model overestimates the decoherence (preset c60_grw: |γ₁₂| = 0.61 instead of 0.85), and its check shares the
  approximation;
* the main measured quantity, the histogram's |γ₁₂|, comes from an ill-conditioned fit: it is biased, often above 1
  and often fails, and the run's own coherence check fails on some seeds;
* the near-field map and flow lines ignore the decoherence the run computes (microscope, GRW, source width, spectral
  width);
* an analyzer inserted while particles are in flight does not act on them (contrary to RULES §2.2);
* λ from the kinetic energy loses 2–3·10⁻⁴ for slow massive particles, so the run's own λ check fails;
* the Aharonov–Bohm phase ignores |q| for custom charges.

There are **11 should-fix** findings (checks that cannot fail or are too loose, dark counts missing from the
expectation, curves in the browser that are not the run's expectation, unphysical probe input, numerical cost and
resolution limits without warnings, limitations not visible in the player) and **11 nits**.

## Findings

Severity: **error**: a wrong number or picture, or a broken owner rule. **should-fix**: misleading, unreliable or
unguarded, but not wrong in the default use. **nit**: labels, conventions, documentation.

### R1. error: GRW hits are counted over the whole flight but applied at the slit plane

* **Location.** `engine/experiment.py:228-230` (Poisson(λ N L₂/v) hits), `:326-343` (`_grw_weights`: every hit
  multiplies the slit amplitudes with the full separation d); reference `viz.py:429-433`;
  README "Approximations"; STATUS V5.
* **What is wrong.** For the Gaussian GRW map, a hit at distance z behind the slits is, on average, exactly a random
  momentum kick q ~ N(0, 1/(2r_C²)). In paraxial free flight this kick shifts the screen pattern rigidly by
  q(L₂ − z)/k (complete the square in the Fresnel kernel). So the per-hit coherence factor is
  exp(−d²(1 − z/L₂)²/(4r_C²)), not exp(−d²/(4r_C²)). Averaged over hits uniform in z:
  `|γ| = exp(−λNT [1 − (√π r_C/d) erf(d/(2 r_C))])`.
  The engine takes the hit count from the whole flight T = L₂/v and gives every hit the slit-plane separation. This
  overestimates the decoherence exponent. Point-like slits do not fix it: the model is not GRW for this geometry. The
  check's reference has the same approximation, so it passes. STATUS V5 calls this a "narrow-slit approximation". The
  real issue is the timing of the hits. The preset is also outside the stated validity: a = 0.5 r_C and d = r_C.
* **Evidence** (`out/03_grw.txt`).
  * The per-hit average of the engine's sampler is correct: E[c₁c₂*] = 0.7781, 0.6067, 0.3705 for 1, 2 and 4 hits,
    against exp(−n d²/4r_C²) = 0.7788, 0.6065, 0.3679.
  * Kick at z = 0.4 m vs the shifted pattern (two-step numerical Fresnel): agreement to 8.5·10⁻⁴.
  * Preset c60_grw (λNT = 2.25):

    | quantity | value |
    |---|---|
    | the engine's run | 0.611 |
    | its reference | 0.608 |
    | exact paraxial free flight, MC with 2·10⁵ particles, the run's own fit | 0.848 |
    | closed form above | 0.840 |
    | same kicks, all at the slit plane | 0.622 (reproduces the engine) |

* **Fix.** Draw each GRW hit as a kick κ = q(1 − z/L₂), with q ~ N(0, 1/(2r_C²)) and z ~ U(0, L₂). Sum the kicks per
  particle and pass them through the existing `kappa` path. This is exact for the ensemble in the paraxial engine,
  needs no narrow-slit assumption, and handles any slit width. Use the closed form above as the check's reference,
  then close or rewrite STATUS V5. Add a test against `03_grw.py`'s independent ensemble.

### R2. error: the slit-basis coherence fit is ill-conditioned (histogram |γ₁₂| biased, often > 1 or failing; the run's own check fails on some seeds)

* **Location.** `engine/stats.py:47-70` (`coherence_fit`: four free parameters c₁b₁₁ + c₂b₂₂ + c₃Re b₁₂ + c₄Im b₁₂,
  γ = |c₃ + ic₄|/(2√(c₁c₂)), Neyman weights 1/max(h,1)); `viz.py:411-441` (expected |γ| and the `coh` check),
  `viz.py:592` (histogram |γ|, shown in the stats panel); test `tests/test_v02_physics.py:170-178`.
* **What is wrong.** In the far field b₁₁ and b₂₂ are practically the same function. Their correlation is 0.99983 for
  the electron presets and 0.99998 for photon_young. So c₁ and c₂ are separately undetermined, and √(c₁c₂) in the
  denominator scatters. Neyman weights add a low-count bias. Whenever c₁ ≤ 0 or c₂ ≤ 0 the fit returns `None`.
* **Evidence.**
  * Histogram fits on multinomial samples of the exact expectation (`out/05b_statistics_fit.txt`), electron_weak
    (true 0.866):

    | N | fit fails | mean of the rest | fits > 1 | median reported error |
    |---|---|---|---|---|
    | 1000 | 119/200 | 1.30 | 59 % | 1.48 |
    | 5000 | 59/200 | 1.29 | 47 % | 0.38 |
    | 20 000 | — | 0.930 | 14 % | 0.07 |
    | 10⁵ | — | 0.882 | — | — |

  * photon_young (true 1): at N = 5000 the fit fails in 107/200 and the rest average 1.67, all above 1; at N = 10⁵ the
    mean is 1.058 and 98 % are above 1.
  * electron_qubit (true 0): bias +0.17 at N = 1000.
  * The same fit applied to the smooth expectation (`out/05d_expected_fit_stability.txt`, electron_microscope, 20
    seeds): c₁/c₂ ranges 0.05–4.0 where the physics gives 1. Expected |γ| = 0.170 ± 0.045, against 0.152 ± 0.022 with
    c₁ = c₂ imposed; the closed form is 0.152. The run's own `coh0` check **fails for seed 3** (0.328 vs 0.152,
    tolerance 0.123).
  * The suite's test passes only because it uses N = 20 000 and a 4σ band of a large error.
* **Fix.** G₁₁ and G₂₂ are known to the run: the slit transmissions from the marks, and the same for kicks and source
  points. Fit three parameters, μ = c₀(G₁₁b₁₁ + G₂₂b₂₂) + c₃Re b₁₂ + c₄Im b₁₂, by Poisson maximum likelihood, or by
  least squares weighted by the expectation (Pearson, not Neyman). Take the error from the Fisher matrix. For |γ| near
  0, also report the signed cross-term amplitude or a bias-corrected magnitude. In the same samples this estimator has
  bias ≤ 0.03 at N = 100, about 0 for N ≥ 1000, and a scatter of 0.012 at N = 5000 (true 0.866)
  (`out/05b_statistics_fit.txt`, "constrained ML"). Use the same estimator for the expected curve.

### R3. error: the near-field map and the flow lines ignore decoherence the run computes

* **Location.** `viz.py:317-327` (map and flow lines use `Gavg` from `ensemble_marks()`, which contains elements,
  analyzer, detector qubit and Aharonov–Bohm phase only); `engine/fresnel.py:98-114`, `:117-150`; help text
  `web/view.js:373` ("рассчитанная волна этого отрезка").
* **What is wrong.** The microscope kicks, GRW, source width and spectral width never reach the left panel. The panel
  shows a fully coherent wave while the screen, computed by the same run, shows the decoherence. Under RULES §2.1 the
  drawn wave is then not the output of the run's computation for that apparatus.
* **Evidence** (`out/06_viz_consistency.txt` (a)). Fringe contrast of the map at z = L₂ next to |γ| of the run's
  expectation:

  | case | map contrast | run's \|γ\| |
  |---|---|---|
  | electron_microscope | 0.996 | 0.138 |
  | c60_grw | 0.993 | 0.611 |
  | photon_partial | 0.996 | 0.466 |
  | σλ/λ = 0.3 | 0.996 | 0.365 |

* **Fix.** Build the map as the ensemble average of |Ψ(x, z)|² over the same realizations that `ensemble()` draws
  (each with its own k, x_s, κ and weights). Build the flow lines from the averaged current Σ Im(Ψ†∂Ψ) / Σ|Ψ|² of
  those realizations (the README already calls them "flow lines of the averaged current"). For the microscope, the
  kick must act from the slit plane on. If the cost is too high, at least label the map "without microscope / GRW /
  partial coherence" whenever these are on.

### R4. error: an analyzer inserted while particles are in flight does not act on them (RULES §2.2)

* **Location.** `viz.py:509-523` (each particle's whole fate is decided at slit passage); `engine/experiment.py:158-162`
  and `:197-245` (the analyzer `Pa` enters the marks at that moment); `viz.py:604-621` (an action does not withdraw
  pending detections). Also the detector's readout basis.
* **What is wrong.** The analyzer stands in front of the screen. A particle that passed the slits before the analyzer
  was inserted (or removed, or rotated) reaches it afterwards, yet it is detected with the old analyzer. The detection
  is drawn at t_det, so a consequence is revealed under a configuration that no longer exists. RULES §2.2 requires
  pending consequences that depend on a change to be withdrawn and recomputed. With the "▷ полёт" speed (one flight
  ≈ 2 s of wall time) this is exactly what the user watches. Elements at the slits are handled correctly.
* **Evidence** (`out/06_viz_consistency.txt` (d)). Neutron preset at 20 000/s, flight 25.3 ms, spin filter along x
  inserted at t₀ (it should pass ½ of up_z):

  | window | detections | rate | analyzer acting? |
  |---|---|---|---|
  | (t₀, t₀ + flight] | 511, all tagged with the old segment | 20 215/s | no |
  | the following two flights | — | 8 545/s | yes |

* **Fix.** Split the fate. Keep the slit-plane state of every in-flight particle (marks without `Pa`, plus k, x_s, κ,
  GRW weights). Draw its screen outcome when it reaches the analyzer plane (≈ t_det), using the apparatus present
  then. Alternatively, on an apparatus change, withdraw the pending detections of in-flight particles and redraw
  them. The detector reading can be drawn at the reading time in the same way (a delayed choice). The screen marginal
  is unaffected by no-signalling.

### R5. error: λ from the kinetic energy loses up to 3·10⁻⁴ for slow massive particles; the run's own λ check fails

* **Location.** `engine/particles.py:96-97`: `E = value*EV + mc2; p = sqrt(E*E - mc2*mc2)/c`. The relative resolution
  of mc² in float64 (10⁻¹⁶·mc²) is comparable with E_k; the reverse direction (`:111`) was already fixed.
* **Evidence** (`out/04_particles_ab_probe.txt` §1–2; reference: mpmath at 50 digits).

  | particle and energy | relative error of λ |
  |---|---|
  | neutron at 0.2045 meV (λ ≈ 2 nm) | −3.0·10⁻⁴ |
  | C60 at 0.15 eV | +1.75·10⁻⁴ |
  | He-4 at 20 meV | −4.9·10⁻⁶ |
  | electron at 50 keV | 5·10⁻¹⁶ |

  The run's check `lam` for the neutron shows rel = −3.03·10⁻⁴ against tol 10⁻⁹, i.e. failed. Presets set slow
  particles by λ or speed, so the suite does not see it.
* **Fix.** `p = sqrt(Ek² + 2·Ek·mc²)/c` and `E = Ek + mc²` for display only. Add a test with slow massive particles
  given by E_k.

### R6. error: the Aharonov–Bohm phase ignores |q|

* **Location.** `engine/experiment.py:147`: `ph = 2π·ab_flux·sign(q)`.
* **What is wrong.** The phase is qΦ/ħ = 2π(q/e)(Φ/(h/e)). Custom particles accept a charge from −100 e to 100 e.
* **Evidence** (`out/04_particles_ab_probe.txt` §3).

  | q | Φ (h/e) | engine | qΦ/ħ |
  |---|---|---|---|
  | +2e | 1/4 | +π/2 | π |
  | −3e | 1/6 | −π/3 | π (mod 2π) |
  | +0.5e | 1 | 0 | π |

  q = ±e is correct.
* **Fix.** `ph = 2π·ab_flux·charge/E_CHARGE`. Add a test for |q| ≠ e.

### R7. should-fix: with a modified Born exponent, reading the detector changes the screen distribution, but the no-signalling check reports ok

* **Location.** `engine/experiment.py:247-248, 257` (the exponent is applied to each readout component I_r);
  `viz.py:459-475` (the check compares Σ_r I_r with the unread |ψ|², not the distribution actually sampled).
* **Evidence** (`out/06_viz_consistency.txt` (e)). electron_eraser with p = 2.4: the sampled screen marginal with
  reading differs from the one without reading by 7.4 % (max/max). The check shows 1.6·10⁻¹⁶, ok.
* **Fix.** Compute the check from `born(I)` as sampled. Under a modification, report signalling as a computed
  consequence (a failed check with a note), not as "ok".

### R8. should-fix: dark counts are in the histogram but not in the expectation

* **Location.** `viz.py:569-576` (dark counts are added to the segment histogram), `:588` (the expectation is `Pens`
  only), `:592` (the coherence fit has no constant term); `web/view.js:270-283` (curves).
* **Evidence** (`out/05b_statistics_fit_part2.txt` (d)), photon_young, 30 s:

  | dark counts | χ² | p | histogram \|γ\| |
  |---|---|---|---|
  | none | 197.9 / 173 dof | 0.094 | 1.004 ± 0.014 |
  | 50/s (5 %) | 376.5 / 177 dof | 1.8·10⁻¹⁶ | 0.991 ± 0.062 |
  | 500/s | 24 491 / 189 dof | — | `None` (the fit fails), shown as "—" |

* **Fix.** Add the dark density (dark_rate / emission rate / screen width, per emitted particle) to the expectation
  sent and used for χ². Add a constant column to the coherence fit.

### R9. should-fix: the expected curve in the browser is rebinned differently from the run and shows a sawtooth

* **Location.** `web/view.js:304-310` (`rebin`: each grid point's P·dx is put into one bin, so bins with 2 and 3 grid
  points alternate). The server's `_rebin` (`viz.py:649-652`) integrates correctly.
* **Evidence** (`out/06_viz_consistency.txt` (b)). Browser/server ratio per bin (bins above 20 % of the maximum):

  | preset | ratio range |
  |---|---|
  | c60 | 0.835–1.363 |
  | electron | 0.954–1.129 |
  | photon_young | 0.986–1.028 |

  The orange "expectation of the run" is not the run's expectation per bin.
* **Fix.** Send the server's binned expectation per readout and per class, or port the cumulative trapezoid.

### R10. should-fix: the filter "без рассеянного фотона" draws the whole ensemble's curve

* **Location.** `web/view.js:270-278` (for `noscat` the curve is Σ_r Pens, i.e. scattered and unscattered particles
  together).
* **Evidence** (`out/06_viz_consistency.txt` (c)). Microscope with p = 0.5: the subset's histogram gives
  |γ| = 1.016 ± 0.037, while the drawn curve has |γ| = 0.504. The correct expectation for the subset has |γ| = 1.
* **Fix.** Compute the expectation per class on the server (as per readout row), or draw no curve for this filter.

### R11. should-fix: a probe photon polarised along its own direction is accepted

* **Location.** `viz.py:239-258` (`_apparatus` has no check), schema `viz.py:102-105`;
  `engine/experiment.py:216-219`.
* **What is wrong.** A transverse wave cannot be polarised along its propagation direction, yet the dipole pattern
  is then drawn about that axis.
* **Evidence** (`out/04_particles_ab_probe.txt` §4). mic_dir = mic_pol = x, y and z are all accepted without an error.
* **Fix.** Reject mic_pol == mic_dir, or derive the dipole axis from a polarisation angle in the plane transverse to
  the probe.

### R12. should-fix: Monte-Carlo expectations with M = 600/1500 and check tolerances that cannot fail

* **Location.** `viz.py:309-314` (M), `:426, :432, :437` (tolerance 4/√M + c).
* **Evidence.**
  * Seed-to-seed scatter of the expected |γ| against the tolerance (`out/05_statistics.txt`, `05b` (e), `05d`):

    | case | scatter (std) | tolerance |
    |---|---|---|
    | photon_partial | 0.017 | 0.113 |
    | c60_grw | 0.008 | 0.103 |
    | microscope | 0.022 (constrained fit), 0.045 (run's fit) | 0.123 |
    | microscope, p = 0.5 | 0.033 | 0.123 |

    For p = 0.5, seed 1 gives 0.504 against the near-exact 0.432, and the check accepts it. Deviations of up to 4–12σ
    pass. R1 shows that a wrong model can still pass because its reference is wrong as well.
  * The noise in the expectation itself makes χ² reject a perfect detector beyond N* = dof/δ detections: about
    1.8·10⁶ (photon_partial), 3.4·10⁶ (microscope), 1.05·10⁶ (microscope p = 0.5), 3·10⁷ (c60_grw). At the "набор
    картины" speed this is hours; at a high speed it is minutes.
* **Fix.** Replace the Monte-Carlo ensemble by quadrature, each part exact or with controlled error:
  * source points: Gauss–Legendre in x_s;
  * spectrum: Gauss–Hermite in λ;
  * dipole directions: the product rule already in `stats.dipole_coherence`;
  * GRW: the kick convolution of R1;
  * internal states: exact through ρ.

  Then set the tolerances from the quadrature error, and add the expectation's own variance to χ² while any Monte
  Carlo remains.

### R13. should-fix: the near-field part of the map is paraxial where the paraxial approximation fails, and nothing says so

* **Location.** `engine/fresnel.py:98-114` (the map starts at z₀ = 2a, log scale); `viz.py:322`. The RS check
  (`viz.py:371-378`) covers the screen plane only.
* **Evidence** (`out/07b_map_vs_rs.txt`; the map's own grid, per-column normalisation as drawn).

  | geometry | part of the map width | max deviation from exact RS |
  |---|---|---|
  | photon_young | first 30 % (z ≲ 40a) | 3–12 % |
  | photon_young | z ≥ 120a | ≤ 0.5 % |
  | a = 3 µm photons | first 20 % | 8–29 % |

* **Fix.** Run the RS comparison on a few map columns and report it. Start the map at the first z where it passes, or
  hatch the region where it fails.

### R14. should-fix: the RS check's quadrature is O(n³) in time and O(n²) in memory, with n up to 20 000

* **Location.** `engine/rs.py:54-55` (`np.polynomial.legendre.leggauss(n)` builds a dense n × n companion matrix).
* **Evidence** (`out/01b_leggauss_timing.txt`, `out/07_numerics.txt` §2). numpy leggauss takes 0.42 s at n = 2000 and
  4.7 s at n = 4000; `scipy.special.roots_legendre` takes 0.09 and 0.37 s. Node counts from the same formula:

  | geometry | nodes | estimated time | memory |
  |---|---|---|---|
  | photons a = 1 mm, screen 1 m | 20 000 | ≈ 590 s per slit | 3.2 GB |
  | photons a = 1 mm, L₂ = 1 mm (near field) | 20 000 | ≈ 590 s per slit | 3.2 GB |
  | electrons, screen 1 cm | 4 513 | 6.7 s per slit | — |

  This is repeated at every apparatus change. My first script stalled the same way in this call.
* **Fix.** Use composite fixed-order Gauss–Legendre panels (as in `01_fresnel_rs.py`), or `scipy.special.roots_legendre`.

### R15. should-fix: the 16 384-point cap undersamples paraxial patterns without any warning

* **Location.** `viz.py:209-213` (`ns = min(..., 16384)`, `pixel = max(fine/8, dx)`), `_nbins` cap 4000 (`:342-344`).
* **What is wrong.** When the cap binds, detections are drawn from the coarse grid, so the histogram and the
  expectation agree with each other (χ² passes) but not with the physical pattern. The RS check passes because it
  compares the two methods pointwise.
* **Evidence** (`out/05b_statistics_fit_part2.txt` (f), `out/07_numerics.txt` §1; electrons 50 keV, all RS checks pass
  at 3·10⁻⁵, no notice):

  | geometry | points per finest fringe | bin-probability error | central contrast, run vs exact |
  |---|---|---|---|
  | 12 slits, a = 0.1 µm, d = 10 µm | 1.85 | up to 48 % | 0.600 vs 0.701 |
  | 2 slits, d = 150 µm | 1.24 | up to 27 % | — |

  All presets are fine (≥ 17.9 points per fringe).
* **Fix.** Warn (or fail a check) when the points per finest fringe drop below ~8. Better, sample positions inside a
  bin from the analytic amplitude instead of grid points.

### R16. should-fix: 10–12 slits with any Monte-Carlo ensemble make the run unusable in real time

* **Location.** `viz.py:309-314`; `engine/experiment.py:197-245` (a Python loop over particles for marks and Gram
  matrices; a three-operand `einsum` over (b, j, l, x)).
* **Evidence** (`out/07_numerics.txt` §4).

  | geometry | grid points | first segment | 500 particles | peak memory |
  |---|---|---|---|---|
  | 12-slit microscope, electrons | 9 646 | 100 s | 15 s | 0.44 GB |
  | 12 slits, partial coherence, photons | 16 384 | 167 s | 27 s | 0.44 GB |

  Every apparatus change blocks the run for minutes.
* **Fix.** Quadrature ensembles (R12). Vectorise marks and Gram matrices over particles. Contract with
  `np.einsum(..., optimize=True)` or two matrix products.

### R17. should-fix: the stated limitations are not visible where the user works

* **Location.** The README is not served by the player (`server/lfviz`, `player/` have no reference to it); the help
  is `web/view.js:371-375`, the header text `viz.py:633-638`. The only notice is the Kirchhoff one (`viz.py:379-381`).
* **What is wrong.** RULES §2.6 asks the run to say where an approximation can fail. The player shows nothing about:
  * the 2-D geometry;
  * paraxial optics in the near-field map (R13);
  * GRW at the slit plane (R1);
  * the microscope acting only at the slit plane with a dipole pattern for every species;
  * the analyzer acting at slit passage (R4);
  * conventions (R19);
  * the grid cap (R15).

  The help still calls the flow lines "траектории Бома", including for mixed sources. The README lacks the analyzer
  timing, the single flight time under spectral width (R21) and the Born-exponent normalisation (R28).
* **Fix.** Add an "approximations" panel generated from the README or from the run (per segment, listing the active
  ones). Emit notices when an active feature leaves its validity (a ≲ r_C for GRW, points per fringe, paraxial map
  columns).

### R18. nit: the RS-I kernel has the wrong overall sign

* **Location.** `engine/rs.py:4` (docstring) and `:69`: −(ikz/2)H₁⁽¹⁾(kR)/R.
* **What is wrong.** From ∫H₁⁽¹⁾(k√(x² + z²)) z/√(x² + z²) dx = −2i e^{ikz}/k, the first-kind RS kernel for
  G = (i/4)H₀⁽¹⁾ is +(ikz/2)H₁⁽¹⁾/R.
* **Evidence** (`out/01_fresnel_rs.txt` §4). U_RS / (√(k/2πiz) e^{ikz} A_Fresnel) = −1.0000 at x = 0 and 1 mm. A wide
  aperture gives U ≈ −e^{ikz}. Intensities are unaffected, and the docstring's "common constants included" holds up to
  this sign.
* **Fix.** Flip the sign.

### R19. nit: polarisation conventions are not stated, and two labels contradict the engine's own R/L

* **Location.** `engine/experiment.py:389-394` (S₃ = −2 Im(a b*)), `engine/marks.py:100-104` (custom ellipticity χ),
  `engine/marks.py:20-22` (conventions text).
* **What is wrong.** The engine's time convention is e^{i(kz−ωt)}, from the Fresnel kernel e^{+ik(x−x')²/2z} and the
  outgoing H⁽¹⁾. Its R = (1, −i)/√2 rotates clockwise for the receiver, i.e. right-circular in the usual optics
  convention, and the QWP at 45° turns H into R with the angle being the fast axis. All of that is consistent.
  However:
  * the Stokes label gives R → S₃ = −1, while S₃ = I_R − I_L with the engine's own R and L gives +1;
  * the custom state with χ = +45° is the engine's L.
* **Evidence.** `out/02_marks.txt` §1.
* **Fix.** Flip the S₃ sign and the χ sign, or define both explicitly. State the time convention and "angle = fast
  axis" in the README and the help.

### R20. nit: several checks are algebraic identities, not physics tests

* **Location.** Englert V² + D² for pure marks (`viz.py:404-410`); no-signalling (`:459-475`, completeness of an
  orthonormal basis); Sorkin at p = 2 (`:443-457`, bilinearity); `coh` against the marks at tol 10⁻⁶ (`:416-419`,
  Pens is built from the same Gram matrix).
* **What is wrong.** They can fail only by round-off. That is useful as regression, but the panel presents them as
  agreement with physics.
* **Evidence.** `out/02_marks.txt` §4: identity to 10⁻¹²; readout completeness to 4·10⁻¹⁶ over 200 random cases.
* **Fix.** Label them "consistency (identity)". Keep the independent checks (RS, VCZ, Chapman, period) separate.

### R21. nit: under a spectral width every particle has its own λ but the same flight time; λ is reflected at 0

* **Location.** `engine/experiment.py:203` (|λ(1 + σN)|), `:279` (central v); `viz.py:233`.
* **What is wrong.** For massive particles σλ/λ is a velocity spread: 20 % for the neutron example
  (`out/04_particles_ab_probe.txt` §6), while every particle uses 25.3 ms. For σ up to 0.5 the reflected Gaussian is
  not a physical spectrum.
* **Fix.** Per-particle v_g in t_det (and in the GRW hit count). Use a log-normal spectrum or limit σ.

### R22. nit: GRW silently has no effect on electrons and light custom particles

* **Location.** `engine/particles.py:75` (`nuc = round(mass_u)`, 0 below 0.5 u), `engine/experiment.py:228`.
* **What is wrong.** Mass-proportional GRW and CSL give electrons m_e/m_N ≈ 5.5·10⁻⁴ nucleon equivalents.
* **Evidence.** `out/04_particles_ab_probe.txt` §5.
* **Fix.** Use mass/m_N as the rate factor, or emit a notice that GRW does not act on this species.

### R23. nit: with "текущий отрезок" off, the curve is the current segment's expectation over a multi-segment histogram

* **Location.** `web/view.js:98, 270` (incremental histogram, version of 16:28).
* **Fix.** Draw the count-weighted mix of the segments' expectations, or hide the curve.

### R24. nit: the meaning of the "cone" recording and the dipole pattern for neutral species

* **Location.** `engine/experiment.py:212-224`; filter "phase" in `web/view.js:101-105`.
* **What is wrong.** Sorting by the exact Δk·d means the photon's direction is measured (a detector in the back focal
  plane), not an image of the slits. A neutron's photon scattering is not a dipole (Thomson or Rayleigh) pattern.
* **Fix.** State both, or restrict the microscope to charged and polarisable species.

### R25. nit: absorption by the analyzer is reported as "поглощена элементом на щелях"

* **Location.** `engine/experiment.py:346-347`. The total, via Parseval including the analyzer's cross terms, is
  correct; only the label is wrong.

### R26. nit: the detector sampler (grid point plus uniform jitter) and the trapezoid rebinning differ slightly

* **Location.** `engine/experiment.py:271`, `viz.py:649-652`.
* **Evidence** (`out/05_statistics.txt` (b)). χ² would notice the difference only after 3·10⁶ (c60) to 1.6·10⁸
  (photon_young) detections. Fold into the fix of R15.

### R27. nit: minor code and labels

* `engine/stats.py:22` `visibility()` is unused.
* For massive particles the "Частота" panel shows E_total/h (the de Broglie frequency including the rest energy);
  label it.
* `src_width` is silently ignored for a plane wave (`engine/experiment.py:206`).
* `viz.py:3` points to README.md, which now exists; README links `../RULES.md`, which exists.

### R28. nit: conventions of the Born-exponent modification are not stated

* **Location.** `engine/experiment.py:247-248, 243, 314-316`; Sorkin `viz.py:449-455`.
* **What is wrong.** The position is drawn from |ψ|^p normalised over the finite screen. The probability of reaching
  the screen uses |ψ|². The Sorkin parameter uses unnormalised I^{p/2} of the sub-configurations. The values reported
  under the modification depend on these choices.
* **Fix.** State them in the README.

## Checked and found correct

* **Fresnel closed form** (`engine/fresnel.py:34-83`), compared with brute-force composite Gauss–Legendre quadrature of
  the defining integral (`out/01_fresnel_rs.txt` §1–2):
  * signs, the incidence angle, the point source, the kick, and the derivative to 1e-13;
  * the near field z = 2a and picometre wavelengths (electron, C60) to 1e-12.
* The "stable Γ" is algebraically equal to γ₀ − β²/4α. It is common to all slits, so it cancels in every intensity and
  current.
* **Parseval** ∫|A|²dx = λza, also with a point source and a kick: 0.99578 on a ±0.6 m screen, where the remainder is
  the sinc² tail. Cross terms of disjoint slits integrate to 2·10⁻⁹. The absorbed and missed fractions built on it are
  right, including the analyzer's cross terms.
* **RS check:** magnitude and agreement with Fresnel (up to R18); the Hankel asymptotic branch to 4·10⁻¹²;
  preset deviations 3·10⁻⁷ to 3·10⁻³ (`out/07_numerics.txt` §1).
* **Jones matrices** (`out/02_marks.txt`): polarizer projector and Malus law; the HWP as a mirror about its axis; QWP
  at 45° turns H into R; R and L consistent with e^{i(kz−ωt)}.
* **Spin:** the rotation equals exp(−iaσ_y/2); the filter is the projector onto |+n⟩; the spin labels are right.
* **State sampling:** unpolarised sampling is Haar (ρ = I/2 within MC; moments ⟨S_i²⟩ = 1/3, ⟨S_i⁴⟩ = 1/5); partial
  polarisation gives ρ = P|ψ⟩⟨ψ| + (1 − P)I/2.
* **Englert and readout:** D is the trace norm of (w_aρ_a − w_bρ_b) and V = 2|⟨m_b|m_a⟩|/(n_a + n_b), also with
  unequal weights (D ≥ predictability). The readout projections are complete; no-signalling holds at p = 2.
* **GRW:** the per-hit sampling distribution and its renormalisation give exactly exp(−d²/4r_C²) per hit (point
  slits).
* **Microscope:** momentum transfer ħk_p(n_i − n_f) with the x component entering. Rejection sampling of the dipole
  pattern is correct. Recording the photon or not does not change the particle's distribution, as it should.
* **Chapman reference:** against a near-exact ensemble (M = 10⁵), 0.147 vs 0.152; the remaining 0.005 is the envelope
  shift.
* **Van Cittert–Zernike reference:** |sinc(sd/λL₁)| = 0.4608 vs the near-exact 0.4603.
* **Flow lines:** dx/dz = Im(Ψ†∂ₓΨ)/(k|Ψ|²) matches the phase gradient (5·10⁻⁴, finite differences). The
  multi-component form Im Σ dA_j A_l* G_jl is correct, and there is no crossing for a pure state.
* **Kinematics:** photon relations; massive particles given by λ or by speed; group velocity pc²/E; 50 keV electron to
  5·10⁻¹⁶.
* **Aharonov–Bohm** for q = ±e: sign and magnitude.
* **Segments and stories:** particles reaching the slit plane after a change get the new apparatus; detections of
  earlier particles keep their segment; stories are revealed at t_det (version of 16:28); dark counts are uniform
  over the screen.
* **Modifications** (Born exponent, GRW, forced slit) are flagged in the header. The observer effect comes only from
  marks, kicks and the declared modifications; there is no "observed → no fringes" rule.
* **Grid resolution of all presets** is at least 17.9 points per finest fringe.

## Could not check

* The pages in a browser: I read view.js and ported its `rebin` to Python, but rendered nothing.
* Vector diffraction for narrow slits (Kirchhoff validity, STATUS V4): there is no vector solver.
* The primary papers (Englert 1996, Chapman et al. 1995, GRW 1986): I quote nothing from them. The formulas used
  (Englert D, the dipole coherence closed forms, the GRW map and its kick representation) were derived and checked
  numerically here. The statement that S₃ = I_R − I_L and (1, −i)/√2 is right-circular in the usual optics convention
  (Hecht, Born & Wolf) is from memory; R19 rests on internal consistency alone.
* χ² false rejection at N ≳ 10⁶ is computed from the non-centrality, not simulated by a run of 10⁶ detections.
* The illustrative presets against the original experiments (STATUS V7).
