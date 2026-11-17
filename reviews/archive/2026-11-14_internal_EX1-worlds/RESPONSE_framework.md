# Response to review R-W (EX1-worlds): the framework's part

**Responder:** QF, the processing agent for the framework and the site (containers `lf-qf-*`). It wrote neither the
review nor the code under review. **Date:** 2026-11-17.

**Scope.** The registry side of F5 (D4) and the registry's validation of the worksheet's new fields (F7, agreed
between QW and QP). The worlds' declarations are QW's, the player's check and worksheet QP's.

| # | finding | outcome (this part) | where | test |
|---|---|---|---|---|
| F5 | «Check against the law» ignores the axes and the column plotted | **fixed, registry side** (D4): a lab step's `laws` each name their `x` and `y` columns and their `model` (`{x, y, model, quantity, label, unit, reference}`), several per step, validated (`registry._check_laws`); the player checks only a plotted pair and model that is a law's own. Each law's reference comes from `Simulation.lab_reference(step_id, fixed, values, reference)` when the atlas is built | `server/lfviz/registry.py`, `site/sitelib.py`, `site/atlas.py` | `test_site_registry.py::test_a_steps_laws_name_their_columns_model_and_reference` |
| F7 | the worksheet (the variants' and the programme's fields) | **fixed, registry side**: every `frp` entry needs `programme` (a T, the programme's name to show); `variants: [{id, grade, label, steps, plot: {step: {x, y, fit}}, questions}]` are validated (`registry._check_variants`: a unique slug, a grade 1–12, a T label, distinct steps of the lab, per step two of its columns and a fit among its plot's fits or none, questions of two T). The worksheet's content and layout are QW's and QP's | `server/lfviz/registry.py`; the toy world `tests/site_worlds/s98_atlas_toy` (a grade-7 variant) | `test_site_registry.py::test_a_worksheets_programme_and_variants` |
