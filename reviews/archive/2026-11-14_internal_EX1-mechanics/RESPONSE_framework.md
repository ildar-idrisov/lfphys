# Response to review R-E (EX1-mechanics): the framework's part

**Responder:** QF, the processing agent for the framework and the site (containers `lf-qf-*`). It wrote neither the
review nor the code under review. **Date:** 2026-11-17.

**Scope.** The registry side of F9, under the integrator's decision D4. The fit's statistics (Student-t k, the Birge
cap) are QE's and QP's; the worlds' law declarations are QW's.

| # | finding | outcome (this part) | where | test |
|---|---|---|---|---|
| F9 | the verdict «agrees within two errors» | **fixed, registry side** (D4): «Check against the law» can apply only when the plotted columns and the fit are a law's own. A lab step declares `laws: [{x, y, model, quantity, label, unit, reference}, …]` (several per step), validated by `registry._check_laws`: two columns of the step, a model among the plot's fits, a quantity the model gives (`registry.LAW_MODELS`), a reference id unique in the step and answered by `Simulation.lab_reference(step_id, fixed, values, reference)`, the step's own plot among its laws; the old `law` is refused. The catalogue gives every step `laws` as a list; each law's reference is computed when the step's atlas is built (`site/atlas.py`, the manifest's `references`) | `server/lfviz/registry.py`, `site/sitelib.py`, `site/atlas.py` | `test_site_registry.py::test_a_steps_laws_name_their_columns_model_and_reference`; `test_atlas.py::test_the_grid_the_manifest_and_the_index` |
