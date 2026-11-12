# Response (part): LB1-framework F5 — the p04 part (and p01)

Processed 2026-11-11/12 by a processing agent that wrote neither the review nor the reviewed code. The framework part of
F5 (the hooks `carry_state`, `carry_world`, `carry_note`, the notice, the dialog's title) is answered in
`RESPONSE_framework.md`; the p03 part in `RESPONSE_p03.md`. This file: p04's flow and p01's bodies across a carry-over.
Rules: `../README.md`.

### F5 (p04) — «перенести сцену» restarted p04's flow from rest

**Not re-run before the change**: the reviewer's `c07c_carry_p04.out` shows it (q_net 0.0178 → 0.0, the notice naming
only the refused objects); the negative control below (no flow given) is the former behaviour, now said.

**Decision: fixed** with the framework's hooks (spec of 2026-11-11, landed in `server/lfviz/playground.py`):
* `p04_fluids/viz.py` `carry_state()`: the engine's whole flow state (`Flow2D.state_dict()`, the force record left out:
  the new world records its own) as the world's state.
* `carry_world(state, laws)`: rebuilds the old flow and continues it in the new world with the engine's new
  `Flow2D.adopt` (`lfphys/lfphys/core/fluids/lbm.py`): on the same grid and time step the populations are copied bit for
  bit; on another grid, domain or time step the old flow is first moved there by the engine's transfer (`Flow2D.remap`,
  the same as a live change of the grid; the domain grows or is cut on the right and the top, where the objects keep
  their coordinates). The new world's own geometry, sides, fluid, dye and force apply from then on: nodes that were a
  body start at rest, an inlet with the same velocity continues its ramp, the balances count from the carried state.
  Every adaptation is a `carry_note` (the transfer and its grids, another viscosity or density, the dye started at zero
  or dropped, an inlet's ramp started anew); what cannot be taken (no flow given, a state that does not read, a transfer
  the new grid refuses) is `carry_note("течение начато заново из покоя: <reason>", restarted=True)`.

**Verification.**
* Engine: `lfphys/tests/test_lbm_remap.py::test_adopt_continues_another_flow_bit_for_bit` — a channel adopted half-way
  through its inlet's ramp follows the original bit for bit for 300 more steps (populations and dye); refusals of
  another grid or time step; a body only in the adopting flow (rest weights), a body only in the other (its nodes start
  at rest), the dye zero / dropped.
* World: `p04_fluids/tests/test_p04_lab.py::test_a_new_world_keeps_the_flow` — through the runner's `new_world` with
  `carry`: another fluid law on the same grid takes the populations bit for bit and its balances pass; another grid
  (nx 256 → 192) takes the developed flow (not at rest) and the notice says «переносом движка»; the notice's world entry
  is «state»; negative control: `carry_state` None → «течение начато заново из покоя», world «restarted», the flow at rest.
* Browser (private server): `../2026-11-11_internal_LB1-physics/response_checks_p04-p01/p04_new_world_keeps_flow.png` — the notice «Состояние мира перенесено: течение перенесено с
  сетки 32 × 32 … на 24 × 24 … переносом движка …; вязкость 0,001 → 0,0012 …; балансы считаются от перенесённого
  состояния», the developed profile on the screen.

### F5 (p01) — the bodies' state across compatible laws

**Found while processing:** a new Kerr–Newman world of another spin or charge refused every carried body («momentum off
the mass shell»: a state of another metric), and one of another mass carried the state but kept the proper times in the
old unit of M without a word.

**Decision: fixed** (`p01_gravity/viz.py`): Kerr bodies' and rays' `object_state` holds the metric and unit it is in
(a, Q, M), observers' the unit (M). In the new world (`KerrMode._state_here`): the same metric — as it is; another mass
only — the same state in units of M, proper times and clocks kept in seconds (noted); another spin or charge — the body
starts where it was with the momentum its local ZAMO measured (the core's `zamo_frame_momentum` / `momentum_from_frame`;
the new world's initial condition, noted per object); a state under the new horizon — anew from the body's parameters
(`restarted`, noted), or refused when those lie there too (named). Newtonian bodies and the binary carried their state
already.

**Verification.** `p01_gravity/tests/test_p01_lab.py::test_a_new_kerr_world_keeps_the_bodies_states` (another mass:
positions bit for bit, proper times in seconds to 1e-14; another spin: positions bit for bit, ZAMO velocities to 1e-9,
every body «state» with the note; a body falling under the new horizon «restarted», one whose set-up lies there too
«refused»).

**Counts (this part): 1 of 1 fixed** (p04 and p01).
