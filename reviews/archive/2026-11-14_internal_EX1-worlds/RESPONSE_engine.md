# Response to R-W (EX1-worlds): the engine part (QE, 2026-11-17)

This file covers the engine side of F2 (the integrator's decision D9) and the engine side of F8 (D10, requested by QW).
The world side of both is in `RESPONSE_worlds.md`: u32's `_coherence_err`, the readout «—», the √(n_then/n) rescaling,
and S03's `engine_modules`.

| # | summary | decision | files | verified by |
|---|---|---|---|---|
| F2 (engine) | u32's \|γ₁₂\| error is unreliable, 30× too small to 50× too large | **fixed (engine part)** [error in earlier]. Three fixes: (1) the bootstrap draws from the fitted model projected onto \|γ\| ≤ 1, with the conservative boundary rule; (2) the error is the refits' standard deviation with wild refits removed; (3) the Poisson fit no longer settles on spurious points. No error below 300 hits: None with the reason | `lfphys/lfphys/tools/stats.py` (+ ru), `lfphys/README.md` | `lfphys/tests/test_stats_coherence.py` (16 tests); the calibration study below |
| F8 (engine) | the school drawer lists PDG masses and cosmology for a thrown ball | **fixed (engine part)**: a world can name one dataset, `core.data:air` | `lfphys/lfphys/core/data.py` (`DATASETS`, + ru), `lfphys/lfphys/registry.py`, `lfphys/README.md` | `test_layers::test_a_dataset_of_a_module_is_its_own_entry` |

## F2: what was wrong, by measurement [error in earlier]

A synthetic two-slit pattern was used: 200 bins, ten fringes, G₂₂/G₁₁ = 0.8. Each bootstrap error was compared with
the true scatter of the estimate (600 histograms per row). The comparison script is
`evidence/processing_d9/study.py` (output `study1.log`).

- **The old bootstrap (60 refits, std).**
  - At |γ| = 1 its error was 0.17–47× the true scatter at 100–600 hits, and up to 2199× at 2000 hits.
  - Only 57–73 % of the histograms were within ×2.
  - **Cause.** It drew Poisson counts from the fitted model, with every negative bin clipped to 0. When the fit gave
    |γ| > 1, the clipped dark bins drew exactly 0 counts, and the refits all landed on nearly the same |γ|. This is
    the review's «1.055 ± 0.000».
  - A single wild refit inflated the std. This is the review's «± 0.431».
- **The estimate itself.** In 8 of 3000 histograms at |γ| = 1 and 2000 hits, the Fisher scoring returned |γ| from 1.4
  to 7.5, or no value.
  - **Cause.** It weighted every bin by 1/max(μ, 1e-9·max h). Where the iterate made μ < 0 in bins with counts, those
    weights became huge, and the iteration stopped on a point that is no maximum of any likelihood.

## F2: what the engine does now

1. **`_fit_beta`** (used by `coherence_ml` and the bootstrap) maximises the Poisson log-likelihood
   L = Σ_{h>0} h ln μ − Σμ.
   - L is concave in the three coefficients.
   - The method is Newton's, with the observed information and backtracking: every step keeps μ > 0 in the bins with
     counts and does not lower L. It starts from the incoherent pattern when the least-squares start is infeasible.
   - On regular data it reaches the old scoring's point to 1e-9.
   - Wild estimates: none in 1500 histograms (and none in 3000 in the study).
2. **`coherence_boot`** (with `coherence_boot_err` kept as `(err, n_ok)`) works as follows.
   - The counts are drawn from the fitted model projected onto |γ| ≤ 1. Its expectation is ≥ 0 in every bin, because
     |b₁₂|² ≤ b₁₁b₂₂ bin by bin (tested), so no bin is clipped.
   - 100 refits are made. The error is their standard deviation; refits more than 10 central half-widths from the
     median are dropped as failed.
   - **Near full coherence**, i.e. when the estimate is within two errors of 1, the draws are repeated from the
     |γ| = 1 model and the larger spread is stated.
     - The reason: at |γ| = 1 the estimate scatters widely above 1 and narrowly below. At 1000 hits with equal slits
       its 16/50/84 % points are 0.988/1.002/1.057.
     - So the scatter changes fast with the true value there, and one bootstrap at the estimate can understate it.
   - It returns `{err, why, n_ok, n_boot, hits, boundary}`. `err` is None, with a T text in `why`, in three cases:
     - below `COH_BOOT_MIN_HITS` = 300 hits;
     - when the fit fails;
     - when fewer than 90 % of the refits succeed.
   - CPU: 0.08–0.2 s per call, for 200 to 4000 bins.
3. **Texts.** The ABOUT statement says the error is given from enough hits. ru entries were added for the three
   reasons.

## F2: the calibration that sets COH_BOOT_MIN_HITS

The study is `evidence/processing_d9/study4.py` (with `study_lib.py`); its output is `study4.log`.

**Set-up.**
- Four geometries:
  - 200 bins, equal slits;
  - 200 bins, G₂₂ = 0.8;
  - 60 coarse bins, equal slits;
  - 400 bins with 5 % dark counts.
- |γ| = 1, 0.99, 0.97, 0.95, 0.9, 0.7, 0.3.
- 100 to 3000 hits.
- In each row: 40 histograms' errors against the std of 600 estimates.

The smallest share of histograms within ×2, over all geometries and |γ|:

| hits | 100 | 200 | 300 | 400 | 600 | 1000 | 3000 |
|---|---|---|---|---|---|---|---|
| share within ×2 | 0.55 | 0.875 | 1.00 | 0.975 | 1.00 | 0.95 | 1.00 |

- **From 300 hits on**, the error is within a factor 2 of the true scatter in ≥ 95 % of the histograms in every row.
  The median ratio is 0.75–1.58 (above 1 just below full coherence: the conservative rule).
- **Below 300 hits**, the error is None with the reason, and the world shows «—» (D9).
- The engine test repeats ten rows of this at 300, 1000 and 3000 hits: ≥ 18 of 20 within ×2, median 0.7–1.7. It also
  asserts:
  - the review's case: an estimate > 1 at ~650 hits now gets an error within ×2 of the scatter, not 0.0003;
  - no wild estimates;
  - equality with the old scoring on regular data;
  - the non-negative bootstrap model;
  - the refusals.

## F8, engine side (D10)

- **The new form.** `core.data.DATASETS = {"air", "water", "qcd"}`. Each entry has its own title, statement, validity
  and basis (T texts with ru) and takes the module's layer and kind.
- **Registry.** `lfphys.registry.about("core.data:air")` returns that entry with the id `core.data:air`. `describe()`
  accepts the form. The whole module "core.data" keeps working.
- **No framework change is needed.** The server calls only `registry.describe(sim.engine_modules())`
  (`visualizations/server/lfviz/sim.py`, `_engine_info`). The player renders the entries generically. `code_hash`
  covers the whole engine tree.
- **For S03**, QW names `"core.data:air"`.
- **Not split yet.** Datasets other than air, water and the QCD values (the cosmology, the pulsar, EHT, the water
  optics, the Sun) are not split. A world that reads them still names `core.data`.

## Open points for the integrator

- **u32's test** `test_coherence_error_is_calibrated_at_full_coherence` uses 100 hits, below the new threshold. It now
  gets None and fails. QW is told: raise it to ≥ 300 hits, or assert «—» at 100.
- **u32's world (QW)** should show the error only when `err` is not None, show «—» with `why` otherwise, and drop the
  √(n_then/n) rescaling between recomputations.
- **Proposed STATUS line.** Split the remaining parts of `core.data` (cosmology, pulsar, EHT, water optics, Sun) into
  `DATASETS` when a world names them.
- **Proposed RULES text (§7 or the world contract).** "`engine_modules()` names modules, or one dataset of a module as
  `module:part` (e.g. `core.data:air`), so that the panel lists only what the world uses."

## Tests run

- `lfphys/tests/test_stats_coherence.py`: 16 passed (19 s).
- The full engine suite: **2152 passed, 23 skipped**.
- `s03_projectile/tests` and `u32_double_slit/tests/test_u32_physics.py`: 114 passed, 1 failed. The failure is
  `test_coherence_error_is_calibrated_at_full_coherence` at 100 hits (open point above).
