# Response to UX-params (part): v03, p02 and their engine modules

Processed 2026-11-05 by a working session that did not write the review (`../README.md`). Scope of this part, as
assigned: P13, P19 (v03), P28, P29, P30 (p02), and the v03 and p02 parts of P4. The framework's part of P4 (the generic
Russian text for internal failures, tracebacks only in `worker.log`) is the framework's response. The UX-ui part of the
same worlds (latency, placement, live laws, trails): `../2026-11-04_internal_UX-ui/RESPONSE_p01-p02-v03.md`.

Evidence: `response_checks_p01-p02-v03/`. Environment: Docker image `light-funnel-viz`, CPU only, one or two threads
per process, the shared host under load 10–35 from other sessions (wall times are upper bounds).

| | fixed | partly fixed | rejected | open → STATUS |
|---|---:|---:|---:|---:|
| this part (6 findings) | 6 | 0 | 0 | 0 (two stated limits → STATUS V15 text below) |

## P13 (should-fix) — v03 «Ступенька» from the defaults: 52–88 s and two failed checks [error in earlier]

**Fixed.** Reproduced on the tree before (`v03_step.py`, `out/v03step_before.txt`): capped at the budget after
11 946 fs of world time (126 s on one loaded thread), T = 2.359·10⁻⁶ against the stationary 2.558·10⁻⁶ (−7.8 %), the
open remainder 3.2·10⁻⁸ against 3.4·10⁻⁹ allowed. Cause, found while fixing: with E = 0.8 eV below the step V₀ = 1 eV
only the fast tail of the packet passes, all of it just above the threshold and slow; the right detector ramp was chosen
for the incident spectrum and reflected 19 % of that slow transmitted part back (computed for the 15 nm ramp:
`test_a_step_above_the_energy_runs_to_its_transmission`, negative control), so T came out low and part of the wave kept
bouncing between the step and the ramp past the budget. The time estimate also ignored the slow part.

What changed (`v03_quantum_1d/viz.py`): behind a raised step the right ramp is chosen for the transmitted spectrum of
the stationary reference, w(k)·T(k): the first ramp that sends back at most 10⁻³ of the transmitted probability, else
the one that sends back least, accepted within 10⁻² (near the threshold every ramp of the set reflects: 6.8·10⁻³ at
best for this step); the reflection reported is the absolute probability returned, which the T check counts in its
tolerance. The expected time includes the slowest part of the transmitted spectrum that still carries 10⁻³ of T. The
stationary reference is computed once, before the run. Result (`out/v03k_*`): the default step ends without the budget
(t = 1441 fs, 18–24 s on one loaded thread), every check passing, T = 2.555·10⁻⁶ against 2.558·10⁻⁶; the review case
V₀ = 0.75 eV (E above the step): T within 1.2·10⁻⁴ of the reference, every check passing.

Verification: `v03_quantum_1d/tests/test_v03_quantum.py::test_a_step_above_the_energy_runs_to_its_transmission`
(not capped, every check passing, T within 2·10⁻³; **negative control**: the ramp chosen as before returns 19 % of T),
`test_review_cases_converge_to_the_stationary_reference` (unchanged, passes).

## P19 (should-fix) — v03 wide sharp barrier: T 55× off; refusals with wrong or internal wording [error in earlier]

**Fixed.** The cause of the 55× (the physics error the review asked for), found by convergence runs of the world's own
evolution with its time step and grid scaled (`v03_conv.py`, `out/v03c_*.json`, `out/v03d_*.json`; 10 nm barrier,
δ = 0.02 nm, E = 0.8 eV, V₀ = 1 eV, reference T = 1.382·10⁻⁶):

| step × | grid × | T | T / reference |
|---|---|---:|---:|
| 1 | 1 | 7.66·10⁻⁵ | 55.4 |
| 1 | 2 (dx/2) | 7.71·10⁻⁵ | 55.8 |
| 1/2 | 1 | 9.37·10⁻⁶ | 6.8 |
| 1/4 | 1 | 1.61·10⁻⁶ | 1.16 |

The grid is not the cause; the time step is. The split operator's error at an edge of width δ is set by the edge's
kinetic energy ħ²/(2mδ²) — 95 eV at 0.02 nm, against the ~3 eV the phase step counted — and it puts a spurious
~7.5·10⁻⁵ of probability above the barrier at the old step whatever the width (0.6 nm: T = 0.16 off by 2.7·10⁻⁵;
3 nm: T = 1.03·10⁻⁵ came out 8.1× too large; 10 nm: 55×). In the phase φ = dt·ħ/(2mδ²) of one step at that energy:
φ = 2.96 → 7.5·10⁻⁵, 1.48 → 8.2·10⁻⁶, 0.74 → 2.3·10⁻⁷, 0.47 → 3.5·10⁻⁷ (the floor of other errors).

What changed: where the expected transmission (the stationary reference, computed before the run) is below 0.1, the
step also keeps φ ≤ 0.25 (`PHI_EDGE`, `T_EDGE`); above, the T check's 1e-3 T holds at the phase step. The default
δ = 0.1 nm is unaffected (φ = 0.12); δ = 0.05 nm halves the step; at δ = 0.02 nm such a world costs too much and is
refused at once, saying why and the δ that would do («… края барьера резкие (δ = 0,02 нм), а прохождение мало (T ≈
1,4e-06): шаг по времени нужен в 11,9 раза меньше …; увеличьте размытие краёв δ (до ≈ 0,069 нм) или уменьшите ширину
или высоту барьера»). The refusals are scenario-aware (the trap: ħω and x₀; sharp edges: δ; a step above the energy:
the energy, the step or σ) and carry no review ids («(review V3-3)» removed). Results with the new step
(`out/v03new_*`): 3 nm, δ = 0.05: T = 1.11025·10⁻⁵ against 1.11030·10⁻⁵ (4·10⁻⁵ of T); 10 nm, δ = 0.05: within its
tolerance, but the run reaches the budget (the above-barrier part dwells in a 10 nm barrier) and the absorption check
says so — stated in the README and STATUS V15 (below).

Verification: `test_sharp_edges_shorten_the_step_where_the_transmission_is_small` (3 nm, δ = 0.05 within 1e-4 of T;
3 nm and 10 nm at δ = 0.02 refused with «увеличьте размытие краёв δ», no «review»; **negative control**: without the
edges' step the 3 nm, δ = 0.02 world gives T > 3× the reference), `test_refusals_name_what_this_scenario_can_change`;
the whole v03 suite (25 tests).

## P28 (error) — p02: a refused removal left the object half-removed [error in earlier]

**Fixed.** `on_remove` called the engine after dropping the object's reference, so a removal the scene refused (the
cyclotron's field while its electron is in the window) left the object without its link and every later removal or
«Очистить сцену» failed with «Сцена: 'o1'». Now the engine first and the reference after; `can_remove` gives the
engine's own reason before anything is touched (`Scene.removal_reason`, a dry run of the same checks); «Очистить сцену»
removes the particles first and then the field (the framework asks `can_remove` for all and makes the clear all or
nothing). Verification: `p02_quantum/tests/test_p02_quantum.py::test_a_refused_removal_keeps_the_object_and_clear_still_works`
(the review's sequence: the field refused with the reason, kept and still in the engine; the palette's field button
disabled; then «Очистить сцену» removes everything, the world runs on).

## P29 (should-fix) — p02: extreme edits made the wave NaN; «Probabilities contain NaN» [error in earlier]

**Fixed at the cause.** The review's sequence (`results/p02_quantum.jsonl` #33, #70) moves the packet to x = ±10⁶ nm.
The engine's window test (`scene._prepare`) squared the distance to the window's face, which is negative for a centre
outside it, and let the packet through; its Gaussian underflowed to 0 on the grid and the normalisation made the wave
0/0 = NaN; the next Bohm change drew from NaN weights. Now a centre outside the window is refused in the scene's words
(«центр пакета вне окна по оси x: … — поставьте центр внутрь окна, не ближе … к его краю»), the add and the edit alike;
and the Bohm draw refuses in words when there is no finite wave to draw from. Verification:
`lfphys/tests/test_quantum_scene.py::test_a_packet_centred_outside_the_window_is_refused` (±10⁶, 16.5, −40 nm refused
with «вне окна» for add and replace, the particle unchanged; **negative control**: the former test alone admits the far
ones), `test_objects_wholly_outside_the_window_are_refused_and_far_packets_too` (no NaN in any check after; the `_draw`
guard's two texts).

## P30 (should-fix) — p02: tens of seconds per scene change

**Fixed** (the cause and the fix are UX-ui U3: vectorised transfer matrices and absorbers kept by what they depend on).
The review's cases: adding a detector, marker, flux plane or environment, duplicating a packet or detector 30–44 s →
0.05–0.5 s (server side, `out/latency_*.jsonl`); its extremes killed after 2 min — a plane's axis, a marker's edge 10⁶,
a detector at y = ±10⁶, a wall's offset 10⁶ — 0.04–0.16 s (`p30_extremes.py`, `out/p30_extremes_after.jsonl`).

## P4 (should-fix), the v03 and p02 parts — internal exceptions as refusal texts

**Fixed** for these worlds at their sources: p02's «Probabilities contain NaN» (P29) and «Сцена: 'o1'» (P28) no longer
occur; the engine's refusals of p02 are translated at its boundary into `Refusal` with what to change and the engine's
sentence as `detail` (a packet inside a wall, a wave finer than the grid, the band next to an object, a field under a
charged particle, an object outside the window); v03's refusals were Russian `ValueError`s and now name what the
scenario can change, without review ids (P19). Anything else falls to the framework's generic text.

## Files

`lfphys/lfphys/core/quantum/scene.py` (the window test; `_validate` and the dry runs; reflections over strengths; the
band refusal's text), `transfer.py`; `lfphys/tests/test_quantum_scene.py`, `test_transfer_chain.py`;
`visualizations/v03_quantum_1d/{viz.py, README.md, tests/test_v03_quantum.py}`;
`visualizations/p02_quantum/{viz.py, README.md, tests/test_p02_quantum.py}`.

## Changes for the integrator

**STATUS.md**, section V, row V15 (v03) — append to its text:
> Since review UX-params (2026-11-05): sharp edges shorten the time step where T < 0.1 (φ = dt ħ/(2mδ²) ≤ 0.25:
> measured, the old step put ~7.5·10⁻⁵ of spurious probability above a barrier with δ = 0.02 nm) and such worlds are
> refused when too costly; behind a raised step the right ramp is chosen for the transmitted spectrum and may still send
> back up to 1 % of T near the threshold (counted in the T check's tolerance); a 10 nm barrier with T ~ 10⁻⁶ settles
> slowly and may reach the budget (T within its tolerance, the absorption check says the run stopped early)

and to its «to close»: «longer gentle ramps for near-threshold transmission without widening the window».
