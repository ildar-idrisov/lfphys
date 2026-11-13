# Response to review i18n-code: worlds v01–v09 (PR-C1)

Processed 2026-11-13 by the worlds-1 agent of the integration (not the review's author). The part covers the findings
located in `visualizations/v01_light_travel … v09_thomas_3d` (`viz.py`, `engine/`, `web/view.js`, `tests/`). The
engine's machine codes (`lfphys.codes`: `code_of`, `data_of`; PR-B, `lfphys/tests/test_codes.py`) are what the worlds now
match.

| # | finding (v01–v09 part) | decision | verification |
|---|---|---|---|
| F4 / F5 | v05 recognised `thin_films.airy`'s refusals by English substrings ("total reflection", "grazes", "real positive") | fixed: `_airy_reason` maps the codes `airy.total_reflection`, `airy.grazing`, `airy.lossy_index` to the world's own sentences (`_AIRY_REASONS`); an uncoded exception keeps its own `T`, or is wrapped as "the engine's reason: {err}". Two more engine refusals of the v05 checks are now handled by code instead of crashing the check: `film.too_many_nodes` (the Joule check becomes informational with the engine's numbers `n`, `lim`) and `film.below_critical` (no reference decay length at a rounding neighbour of θ_c) | `v05_optics_bench/tests/test_v05_optics.py`: one test per mapping (`test_airy_refusals_map_to_the_worlds_words_by_code` ×3, `test_airy_grazing_is_coded_by_the_engine`, `test_airy_reason_without_a_code_keeps_the_engines_text`, `test_film_below_critical_maps_to_no_reference`, `test_joule_quadrature_limit_maps_to_an_informational_check`) |
| F5 (same kind, found in this pass) | v06 caught `running.LandauPole` by class and every other `ValueError` as an RG failure; v01 took *any* `ValueError` of `clock_rate` for "faster than light" | fixed: v06 matches `qcd.landau_pole` (α_s is NaN below the pole; the one-loop check informational with the pole's μ from `data_of`) and `qcd.rg_failed` (the world's refusal, the solver's message in the details); v01 maps only `gr.not_timelike` and `kinematics.superluminal` to its refusal and lets another code (e.g. `gr.inside_horizon`) through | `v06_qcd/tests/test_v06_qcd.py`: `test_landau_pole_code_gives_nan_in_the_world`, `test_rg_failure_code_becomes_the_worlds_refusal`; `v01_light_travel/tests/test_v01_physics.py`: `test_superluminal_path_codes_become_the_worlds_refusal` ×2, `test_other_clock_rate_codes_are_not_taken_for_superluminal` |
| F8 | `T` bound as a local in `v05_optics_bench/viz.py` (`_at_structure`) and `v05_optics_bench/engine/bench.py` (`born_probs`) | fixed: the locals renamed `Tr` (the dict key `res["T"]` unchanged) | PR-A's new shadowing test; v05 tests |
| F15 | v06 `alpha_mz`: the label "α_s(M_Z), the coupling constant" yields a phrase as its `{label:unit}` in English, nothing in Russian | fixed by rewording: "Coupling constant α_s(M_Z)" / «Константа связи α_s(M_Z)» (no comma, so no false unit); the use was latent (playgrounds only) | v06 tests |
| F3, F6, F7, F9–F14 | framework code | not in this part (PR-A) | — |
| other | the remaining `except ValueError` in v01–v09 catch by type, not by text (v02 apparatus fitting, v04 ghost and turning points, v05 Brent refinement) | no change needed | read of every `except` in these worlds |

Browser F1 (same root cause, in a world): v02's two phase-window fields (`web/view.js`) were `type=number`; they are now
the framework's `numberInput` read by `parseNum` (a decimal comma accepted; a text that is not a number is refused and
the field shows the value in use again). No other `type: "number"` field in v01–v09.

## Tests (2026-11-13, Docker `lfphys-viz`, CPU, `--memory=7g`; private server on port 8674)

- The worlds' own tests: v01–v07 and v09, **392 passed**; v08, **24 passed, 1 skipped** (the GPU test). The new tests of the code review's F5 mappings (v01 3, v05 7, v06 2) are among them.
- `tests/test_checkpoint.py` and `tests/test_restore.py` with `-k` for v01–v09: **all passed** (27).
- `tests/test_i18n.py`: **87 passed**. The first run reported one conflict, "View along the x axis" («Вид» in v09,
  «Взгляд» in v10); PR-C2 aligned v10 and the rerun passed.
- Browser (Playwright 1.58.2 Chromium): `i18n_checks.mjs` for v01–v09 in EN and RU, **62 checks, all passed**;
  `keyframes.mjs` for v01–v09, **all equal** in EN and in RU.
