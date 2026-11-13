# Response to review i18n-code: the engine part (PR-B)

Processed 2026-11-13 by the engine agent of the integration (not the review's author). The part covers the files
`lfphys/lfphys/**` (except `i18n.py`, which PR-A owns), `lfphys/tests/**` and the engine catalogue
`lfphys/lfphys/locales/ru.json`. Findings of this review in these files: **F4** and the engine side of **F5**, plus the
plain f-string ValueError at `core/qcd/running.py:106` named in the integrator's brief. The world side of F5 (switching
the worlds from English fragments to codes) belongs to PR-C1/PR-C2. The `owner_text` part of F4 (`errors.py`) belongs to
PR-A.

Summary: **F4 fixed (engine part), F5 fixed (engine part), running.py:106 fixed.** No finding rejected.

| # | finding | decision | where | verification |
|---|---|---|---|---|
| F4 | plain-English engine messages reach the owner; the «programming errors» claim does not hold for optics | fixed: every engine raise that a world's owner can trigger is now `ValueError(T(...))` (or `RuntimeError`/`FloatingPointError` with a `T`, the type kept) with a machine code (F5). 194 raises converted; 456 → 262 plain-string raises remain, all classified below. The reviewer's examples: `thin_films.airy`'s three raises (and `single_film`'s two 0/0 cases), `mie.coefficient_bound`, `mie._D_start`, the continued fraction of `D_n`, `VortexBeam._guard` and its two z limits, `thin_films.joule_absorption_s`'s node limit, `angular_spectrum`'s `z ≥ 0`. The thresholds are exported, so worlds need not copy numbers: `mie.MAX_X` (= 2·10⁴), `mie.MX_START_MAX`, `VortexBeam.max_elements`, `thin_films.GL_MAX_NODES`; a coded exception also carries its numbers in `exc.data` | `lfphys/lfphys/core/**`, `theories/**` (list below); catalogue: 267 entries added (with the language renames), 67 removed (renamed or no longer used) | `lfphys/tests/test_codes.py` (each world-matched condition raises its code with a `T`), `test_i18n_engine.py` (every new msgid has a Russian entry with the same placeholders), the full suite |
| F5 (engine side) | worlds recognise engine messages by their English text | fixed: `lfphys/lfphys/codes.py` — `coded(exc, code, **extra)` sets `exc.code` (a stable string) and `exc.data` (the `T`'s arguments plus extras), keeps the exception's type, survives pickling; `code_of`, `data_of`; `CODES` lists 127 codes with their meaning. Exception classes carry their code: `lbm.Unstable` sites (`lbm.unstable`, `lbm.rebuild_unstable`, `lbm.adopt_unstable`), `fdtd.Unstable` sites, `running.LandauPole` (`qcd.landau_pole`), `pn_binary.NoOrbit` (`"pn." + reason`), `kn_change_whatif.Refused` (`kn_change.refused`). The quantum scene: `Scene._refusal` codes by `what` (`qscene.resolution`, `qscene.regrid_loss`, …), `_validate` codes its three reasons (`qscene.gauge`, `qscene.field_with_charge`, `qscene.resolution`), the packet's band check is `qscene.packet_band`; new `Scene.addition_check(obj)` / `particle_check(packet)` return the coded refusal (the `*_reason` methods still return the text). NoOrbit and LandauPole now pickle (they did not: custom `__init__` signatures). The codes were sent to the integrator in two messages (first the ones the worlds match, then the rest) | `lfphys/lfphys/codes.py`; the raise sites below | `lfphys/tests/test_codes.py`: the list is frozen (`FROZEN`: a code is never renamed or removed); every code in `CODES` is raised somewhere and every raised code is in `CODES` (AST scan); `coded` keeps type, text and numbers through pickle; one trigger per world-matched family (lbm Mach/τ/cell Reynolds, airy lossy/total reflection, Mie size bound/index/size, md jammed/periodic axis, scene packet band/resolution and `particle_check`, Landau pole + pickle, NoOrbit + pickle, `kn_change.refused`, superluminal, rainbow order) |
| — | `core/qcd/running.py:106`: a plain f-string ValueError | fixed: `T("the integration of the renormalisation-group equation failed at μ = {mu:.4g} GeV")`, code `qcd.rg_failed`; scipy's own message moved to `exc.data["solver"]` (English, for the developer) | `core/qcd/running.py` | `test_codes.py::test_every_code_is_raised_somewhere…` |

## F4: how each remaining plain raise was classified

The rule: a raise is **user-reachable** when its module is loaded by a world (checked by importing every world's
`viz.py` in the container and listing `sys.modules`, plus the worlds' lazy imports such as `core.md.hard`) **and** its
condition depends on a value or a combination the owner sets (a parameter, a scene object, a live change), or on what the
computation does with them (non-convergence, instability, a resource limit). Such raises are now `T` with a code. A
raise is a **programming error** (stays English, no code) when it checks what only code supplies.

User-reachable, made `T` + code (by area; the codes are in `codes.py`):
- **fluids** `lbm`: codes on the already-translated refusals (τ, Mach, cell Reynolds, rest density, interpolated walls,
  the three `Unstable` sites, the edge cut, the dye with sources).
- **molecular dynamics** `md/system.py`, `md/hard.py`, `md/observables.py`, `md/units.py`, `theories/models/interatomic.py`
  (77 raises): placement (jammed, lattice cell, no free site, ball, region), overlaps and insertion, same point,
  non-finite forces/velocities/positions, outside the walls, periodic axes, the piston, box ramps, bond strain, cutoff vs
  box, Ewald, thermal walls, thermostats, hard-sphere limits, potential parameters, FENE break. **The English rendering of
  each message is unchanged**, because p03 still recognises them by regular expressions until PR-C2 switches to the codes.
- **optics** `thin_films`, `mie`, `mie_debye`, `beams`, `angular_spectrum`, `aperture_fields`, `theories/approx/rainbow`,
  `beams_paraxial` (mode indices, helix l ≠ 0), `core/data.py` (water's IAPWS ranges: v05/v17 set temperature and λ).
- **gravity and relativity** `kerr_newman` (no horizon, no photon orbit/ISCO, on the axis, inside the horizon, |v| < 1,
  zero direction, capture radius, step underflow, the observer), `kerr`/`kerr_null` (spin range, axis view),
  `kerr_shadow` (source ring, n-th image, centre), `nbody` (collisions, body values, the refused edit), `orbits`,
  `orbit_stream`, `pn_binary` (NoOrbit's invalid/no_circular/above_circular/plunge/pn_breakdown texts, the start below
  `r_stop`, the plunging integration, orbit averages), `relativity`/`lorentz`/`causality`/`spin_transport` (|v| ≥ c: one
  msgid), `worldlines` (boost order), `raytrace` (camera up ∥ look), `geometry` (zero normal of a slice plane),
  `johannsen_metric` (regularity, photon sphere/shell, photon orbit/stable orbit/ISCO — prograde and retrograde as
  separate msgids, bound orbit, bounds), `theories/approx/newton` (unbound corpuscle).
- **quantum** `scene` (codes on the refusals; device memory; localisation jump), `qubits` (negative probability beyond
  round-off), `hydrogen` (Dirac level), `theories/models/cornell` (box), `core/em/slit` (slit widths, overlap, thickness,
  angle, edge basis).
- **QCD** `running.py:106` (above).

Programming errors, left English (262 plain raises; `KeyError`/`TypeError` included):
- **an unknown identifier or a wrong type/shape from code**: `KeyError` for a missing body/species/obstacle/monitor/source
  key; `pol must be 's' or 'p'`, `dim must be 2 or 3`, `mode: 'affine' or 'wall'`, `emitter must be one of …`,
  `integrator/collisions must be one of …`, `kind one of …`, `unknown camera/mode/piece`, `Plane.preset`, `positions
  (n, d)`, `events must be (t, x[, y[, z]])`, `U0 is 1-D or 2-D`, `need one thickness per inner layer`, `along must be
  'x', 'y' or 'u'`, `a scene object expected`, `device: 'auto' or 'cpu'`, `PN orders must be among …`, `order 0, 1 or 2`.
- **call order and API combinations**: `call msd_origin() first`, `time runs forward`, `give n or density`, `give
  either v (a body) or n (a photon)`, `radial orbits: use integrate_radial`, `free motion has no step of its own`,
  `static_render: bodies at rest only`, `propagate_plane` preconditions.
- **state restore and internal invariants**: `not an … state`, `adopt: …`, `a saved state outside the horizon`,
  `momentum off the mass shell`, `unexpected DOP853 tableau layout in this SciPy`, NoOrbit "unresolved" (a numerical
  self-check of the PN solver), `reaction_validity_radius: no crossing…`, `R(r0) < 0`/`Theta(theta0) < 0` of a null
  geodesic's constants, TF/SF repeated nodes, `lfphys.codes.coded` with an unknown code.
- **environment**: `backend.py` (`CUDA sees no device`, `LFPHYS_GPU_PCI`), `SystemExit` of the CLI.
- **modules no world loads** (developer API only; translated when a world uses them): `core/cosmology/flrw.py` (21),
  `core/em/charges.py` (18), `core/quantum/open_systems.py` (11), `core/gravity/kerr_orbits.py` (6),
  `core/em/fdtd*.py` (7 left; the FDTD refusals that were already `T` got codes), `core/quantum/two_level.py`,
  `jumps.py`, `theories/approx/peters_mathews.py`, `core/certified.py`.

Not changed here, for PR-A (F4's framework part): `server/lfviz/errors.py` `KNOWN` still recognises "worldline is not
timelike"; that engine text is now a `T` (`gr.not_timelike`), so the entry no longer applies to the engine.

## Related changes made while processing

- `T` shadowing: functions with a local `T` (a temperature: `md/system.py`, `md/hard.py`, `thin_films.airy`/
  `single_film`, `core/data.py` water functions, `kerr_newman` state check) call `i18n.T(...)`. The full suite found one
  case the guard test missed: a closure (`MD.add_molecules`' transaction `apply`) that calls `T(...)` while the enclosing
  method has a parameter `T`. Fixed, and `test_i18n_engine.py::test_no_function_shadows_T` now also follows closures
  (a gap of the kind code F8 describes for the framework's guard).
- `registry.NOT_MODULES` includes `lfphys.codes` (a mechanism, no physics, no ABOUT; `test_layers.py`).
- F11 of the language review (engine side), since it is code: the scene's events name the object kind with a
  translatable `NAME` per class ("a box", "a potential step", "a wall with slits", "a flux tube", …) instead of `TYPE`
  ids; "added particle {pid} ({species})" passes the species' label; the regrid loss passes "beyond the grid's band" /
  "outside the window" / "at the window's faces"; FDTD shapes have `NAME` ("a sphere", "a rectangular box", …) and the
  label "a body of shape {kind}" became "a body ({kind})".
- Engine tests updated where they asserted reworded text (`test_quantum_scene*.py`, `test_fdtd_api.py`, `test_beams.py`,
  `test_fdtd_scattering.py`, `test_hydrogen_wavefunctions.py`, `test_lbm_remap.py`), with code assertions added.

## Tests

See the section «Tests» of `../2026-11-12_internal_i18n-language/RESPONSE_engine.md` (one run covers both parts).
