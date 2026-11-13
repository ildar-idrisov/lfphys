# Response (worlds-2 part) to the review i18n-code, 2026-11-12

**Responder:** PR-C2, the agent processing worlds v10–v17 and p01–p04 (container prefix `lf-pc2-`). It did not write the
review. **Date:** 2026-11-13.

**Scope.** The findings that touch the code of p01_gravity, p02_quantum, p03_molecules, p04_fluids and v10–v17 (each
world's `viz.py`, `engine/`, `web/view.js`, `tests/`):
- F5 on the worlds' side;
- the integrator's follow-ups from PR-A on code F8 (local `T`) and F12 (count msgids);
- F14-type operations on rendered text.

The engine side of F5 (the codes in `lfphys/lfphys/codes.py`) is PR-B's (`RESPONSE_engine.md`). The framework findings
are PR-A's (`RESPONSE_framework.md`).

| Finding | Outcome in these worlds |
|---|---|
| F5 text matching | fixed: p01, p02, p03, p04, v14, v15, v17 now match `lfphys.codes` codes; a test for every mapping. Two narrow fallbacks remain where the engine gives no code (below) |
| F8 local `T` (PR-A's follow-up) | fixed: p01 (`unit_s`, `th`), p03 (`T_K`); none in the other worlds |
| F12 count msgids (PR-A's / PR-D's follow-up) | fixed: p03 `{n:d} atoms`, `{n:d} atoms, {e:d} events`; en one/other files for p02, p03, p04, v10, v12, v13, v16, v17 |
| F14 operations on rendered text | one instance, fixed (v16); none in the other worlds |
| Number fields (PR-A's `numberInput`) | nothing to do: no `type: "number"` input in these worlds' views (only checkboxes) |

## F5 — the worlds recognise engine refusals by code

Every mapping now goes through `from lfphys.codes import code_of, data_of`. The numbers come from `data_of`, never from
parsing the text. Each test below triggers the real engine condition and asserts both the engine's code and the
world's own msgid, so a renamed code or a reworded world text fails in CI.

| World | Place | Engine code(s) | World text (start) | Test |
|---|---|---|---|---|
| p01 | `NewtonMode._engine_edit` | `nbody.refused`, `nbody.collision` | "the body would be at exactly the same point as another…" | `test_the_engines_coincidence_refusal_is_said_in_the_worlds_terms` |
| p02 | `_refusal` branch 1 | `qscene.resolution` | "with “{label}” the grid … does not resolve the particle's wave…" | `test_engine_refusals_are_said_in_the_worlds_terms` (6 cases) |
| p02 | `_refusal` branch 2 | `qscene.field_with_charge` | "the field cannot be changed while a charged particle is in the window…" | same |
| p02 | `_packet_refusal` | `qscene.resolution`, `qscene.packet_band` (both "the grid cannot hold the packet") | "the particle's wave is finer than the grid…" etc. | same (`packet_band` was unmapped before) |
| p02 | `palette_state` | `code_of(qs.addition_check(obj)) == "qscene.resolution"` | "with it the grid would not resolve the wave…" | same |
| p02 | `can_remove` | `qscene.field_with_charge` | "while a charged particle is in the window, the field cannot be switched off…" | same |
| p02 | window edges | `qscene.gauge` | "the window's edges were not changed: …" | same |
| p03 | `_MD` (replaces `_EN`'s 21 regexes, `_BOX_FRAGMENTS`, the ramp regex, the matches at ~2024/2044) | md.jammed, md.overlap, md.same_point, md.hard_overlap, md.region, md.outside_walls, md.cutoff, md.ewald, md.hard_box, md.piston, md.periodic_axis, md.bond_strain, md.no_free_site, md.lattice_cell, md.non_finite, md.thermal_wall, md.ramp; md.refused resolved through `data["cause"]` | the world's text and hint per code | `test_each_engine_code_maps_to_the_worlds_text` (19 cases), `test_every_md_mapping_has_a_test` |
| p04 | `_LBM_CODES` / `_lbm_refusal` | lbm.mach, lbm.tau, lbm.cell_reynolds, lbm.rest_density, lbm.interp_moving | "a velocity above what the weakly compressible scheme…", "the viscosity ν = … is too small for this grid and time step…", … | `test_each_engine_refusal_maps_to_the_worlds_text[mach\|tau\|recell\|density\|interp]`, `test_every_lbm_code_mapping_has_a_test` (English text alone maps to nothing) |
| v14 | `engine/pair.py` `solve` (repeats the engine's box enlargement) | `cornell.box` (now raised coded by the world too) | "the states with L = {L} do not fit into the box of radius …" | `test_a_box_too_small_for_the_states_is_refused_with_the_engines_code` |
| v15 | `_ORBIT_REFUSALS` / `orbits_refusal` | jp.no_photon_orbit, jp.no_stable_orbit, jp.no_isco | "there is no circular photon orbit…", "there are no stable circular orbits…", "the inner edge of the stable circular orbits (ISCO) is not found…" | `test_each_refusal_of_the_circular_orbits_gets_the_worlds_own_text[photon\|stable\|isco]`, `test_a_refused_orbit_search_becomes_the_worlds_notice` |
| v15 | `_new_image` (shadow_curve) | jp.no_bound_orbit | "at the inclination θ = …° no spherical photon orbit of this metric is visible…" | `test_no_visible_bound_orbit_is_refused_in_the_worlds_words` |
| v17 | `__init__` size bound | mie.size_bound; the literal 2e4 replaced by `mie.MAX_X` (and 380 by `DR.LAM_MIN`) | "the drops are too large: x > {xmax} at {lam} nm…" | `test_drops_beyond_the_engines_size_bound_are_refused_in_the_worlds_words` |

**What the review asked, item by item.**
- **p04's five mappings had no test.** Each now has one, checking the code too.
- **p02's two `_refusal` branches had no test.** Both are covered.
- **`p04._lbm_refusal` could give "Mach number nan".** No text is parsed any more; the numbers come from `exc.data`.

**Bugs found on the way:**
- **v15, ISCO reported as a photon orbit.** The old matching tested `"photon orbit" in s` first, and the ISCO refusal
  also contains "the photon orbit". A missing ISCO was therefore reported as a missing photon orbit.
- **v15, any error became a refusal.** Every `ValueError` of `shadow_curve` became the "no visible bound orbit" refusal.
  Now only `jp.no_bound_orbit` does; other failures keep the engine's own coded text.
- **p04, viscosity value.** A refused viscosity named the value in force, not the value asked for.

**Codes checked and needing no mapping:**
- p04 `lbm.unstable`, `lbm.rebuild_unstable` and `lbm.adopt_unstable` are caught by type (`L.Unstable`) and shown with
  the engine's translated text.
- p04 `lbm.cut_by_edge` and `lbm.dye_has_sources` are checked by the world before the engine is called.
- v15 `kerr.spin` and `kerr.axis_view` are excluded by the schema (a/M ≤ 0.998, θ ∈ [1°, 179°]). `kerr.image` is shown
  with the engine's own text.
- v16 `beams.memory` and `beams.z` cannot reach the user: the world checks its own stricter budget first, using the
  engine's `table_cost` and the same budget passed as `max_elements`.
- v16 `angular_spectrum.*`: z is clamped to ≥ 0.
- v17 `mie.mx_too_large` cannot occur in the schema's range. `mie.index`, `mie.size` and `mie.no_convergence` are not
  matched.
- v13 `hydrogen.level` (Dirac levels) is never called.
- p01 `kn.*`, `kerr.*`, `pn.*`, `orbit.*` and `gr.*` pass through with their translated T. `WHATIF.Refused` is matched
  by its type.

**Fallbacks that remain (open points for PR-B):**
1. **p02 `_uncoded()`.** `Scene.removal_reason` and `Scene.edges_reason` return a T without a code, and the engine has
   no `removal_check` or `edges_check`. p02 matches two msgid fragments of those two texts ("the field cannot be changed
   while the charged particle", "a charged particle next to a field or a flux tube is"). It already calls
   `removal_check`/`edges_check` through `getattr` once they exist, and `_uncoded` can then be deleted.
2. **p03 `md.piston`.** One code covers five engine sentences without numbers. The two the world words itself ("the hi
   side of this axis is the piston", "0 < x_min <= X <= L, …") are told apart by exact msgid equality, not a fragment,
   and each has a test. Sub-codes or a `data["what"]` would remove this.
3. **p03 box ramp.** `box_ramp()["stopped"]` is an engine status string (`"refused: …"`) without a code; the world tests
   `startswith("refused")`. A `stopped_code` in the ramp record would remove it.

## F8 follow-up — locals named `T`
The `test_no_function_of_the_visualizations_makes_T_a_local` check now passes for these worlds:
- **p01:** the `T` locals became `Clock(unit_s)`, `rescale(…, unit_s)` and `lambda th`.
- **p03:** `debye_cv_fraction`, `einstein_cv_fraction`, `_gas`, `_mol_candidates` and `_T_kelvin` now use `T_K`.

## F12 follow-up — count msgids
- **p03 plurals.** `T("{n} atoms")` now uses the plural msgid `{n:d} atoms`. `T("{n} atoms, {e} events")` became
  `{n:d} atoms, {e:d} events`, with ru one/few/many/other and en one/other.
- **English one/other files.** New or extended `en.json` for:
  - p02: `every {n:d} steps`
  - p03
  - p04: `St = f D / U ({n:d} periods of C_L)`, `{n:d} nodes …`
  - v10
  - v12
  - v13, v16, v17 (the language review's F12.3/F12.4)

## F14 — operations on rendered text
- **v16, fixed.** `web/view.js` glued `${b.l}, ${kind}` from a raw JS number, which showed a hyphen-minus for a negative
  l. It is now `t("{l:d}, {kind}", …)`, a symbols-only msgid formatted by `fmt`.
- **No other instance.** Searched for in p01–p04 and v10–v17: `.includes(t(…))`, `.replace` on rendered titles, glued
  phrases with fixed word order. The view.js joins that remain are separator lists (`" · "`, `"; "`, `${lab}: ${n}`) or
  data (`${w} × ${h}`).
- **p03, fixed.** The Verlet failure inserted the engine's English reason into a Russian sentence; it now uses the
  world's own text through the md codes.

## Tests (Docker `lfphys-viz`, CPU, `--memory` ≤ 6g)

| Run | Result |
|---|---|
| p01 | 42 passed, 1 skipped |
| p02 | 52 passed |
| p03 + p04 | 145 passed; the one test that fed `_box_refusal` a plain English string was switched to a coded `md.overlap` exception and passes |
| v10 | 20 passed |
| v11 | 28 passed, 1 skipped |
| v12 | 18 passed, 1 skipped |
| v13–v17 | 133 passed |
| `test_checkpoint`, `test_restore`, `test_carryover`, `test_manipulation`, `-k` v10–v12 | 9 passed |
| the same, `-k` v13–v17, p01, p02 | 21 passed |
| the same, `-k` p03, p04 | 6 passed |

`tests/test_i18n.py` and the browser checks are reported in `../2026-11-12_internal_i18n-browser/RESPONSE_worlds-2.md`.
