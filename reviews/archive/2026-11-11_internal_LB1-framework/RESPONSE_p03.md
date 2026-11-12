# Response (p03 part of F5): review LB1-framework, 2026-11-11

Processed 2026-11-12 by a processing subagent (prefix `lf-lpm-`), not the review's author and not the author of the
code. The framework's part of F5 (the notice, the hooks, the ids, the checkbox's title) is answered in
`RESPONSE_framework.md`. This file covers p03's part, which uses the framework's hooks of 2026-11-11 (`carry_state`,
`carry_world`, `carry_note`, `self.carrying`). Checks, scripts and screenshots:
`../2026-11-11_internal_LB1-physics/response_checks_p03/`.

## F5 (p03) — fixed [error in earlier]

**Reproduced.** `c07b_notice.out`: a 3-D gas of 12 000 atoms, carried from periodic to walls. `T` went
300.4579 → 300.2395 K at the same t, because p03's `object_state` returned None and every atom was made anew.

**Cause.**
- p03 exported no state, so the framework re-added every object from its parameters.
- **Found while processing** [error in earlier]: p03's solver started at time 0 even when the world's scene had a later
  time (a carried scene, a scene file). Its first advance therefore computed the whole interval up to the scene's time
  over the scene's atoms. In the browser check a carried gas moved by up to 0.46 σ before the new world's first frame.

**Fix** (`visualizations/p03_molecules/viz.py`):

- **`carry_state()`** (the old world) holds, per particle object (gas, crystal, atom, molecules):
  - the atoms' positions and velocities (NumPy arrays), and the space and box;
  - for molecules, per molecule, the atoms' unwrapped positions and velocities in the molecule's atom order;
  - a crystal's lattice note.

  The piston contributes its face and velocity (the piston type is declared `stateful`). The world contributes its box,
  its space, both PCG64 generators (128-bit integers as text) and whether a box change was running.
- **`on_add(obj, state)`** during a carry, when the space is the same:
  - The same atoms are placed at the same places with the same velocities (`MD.add` / `HardSpheres.add`), and molecules
    whole with their bonds and angles (`MD.add_molecules(..., keep_all=True)`, a new engine mode: every molecule as
    given, or none).
  - A molecule that crossed a periodic face which is now a wall is moved inside as a whole, by the least shift; the note
    says how many molecules and how far.
  - A box of another size keeps the atoms where they are when they fit (note).
  - The piston goes to its face with its velocity.
  - Otherwise the object is made again from its parameters, with `carry_note(..., restarted=True)` naming the reason:
    «другая размерность (плоскость ↔ объём) …», or the refusal (outside a wall, on another atom).
  - `place()` neither re-packs nor moves an object carried with its state.
- **`carry_world(state, laws)`**:
  - Both random generators continue the old world's sequence (the thermostats', the thermal walls', the hard spheres'
    draws); the note says so.
  - The note also says that the first law's balance, the momentum's reference and the mean-square displacement count
    from the new world's start, because other laws give another energy function.
  - A box change still running in the old world is said not to continue.
  - Without a world state it raises, and the framework says «состояние мира начато заново».
- **The solver starts at the scene's time** (`MD(..., t=…)`, `HardSpheres(..., t=…)`).
- **Found while processing:** a hard-sphere world given a molecule, a piston, a thermostat or a field through a file or a
  carry raised an `AttributeError`. It now gets a Russian refusal.
- **README:** the approximations' paragraph on scene files and carry-over, with the [error in earlier] tags.

**Verified.**
- `test_p03_lab.py::test_a_new_world_of_the_same_space_takes_the_atoms_as_they_are`, the review's case with 1 500 atoms:
  - positions, velocities, the kinetic energy and the generator are equal bit for bit after periodic → walls;
  - the solver's time is the scene's;
  - the notice says «с состоянием» and that the world's state was taken over;
  - the control: 3-D → 2-D makes the gas again, and the notice says «другая размерность».
- `test_molecules_and_the_piston_carry_their_state`:
  - velocities and bonds are equal;
  - positions are equal modulo the box, except whole molecules moved in from a face (said);
  - the piston's face and velocity are bit for bit, and both rows are «state».
- `test_a_smaller_box_starts_the_atoms_again_and_says_why`: the negative control. Lx 12 → 6 nm cuts the gas; it is made
  again, and the notice says why.
- Browser (`p03_lab_shots.out`, `f5_carry_notice.png`), a 3-D gas of 3 000 atoms through the real server (the carried
  file):
  - the notice «Сцена перенесена в новый мир: все объекты (1). С состоянием — «Аргон». Состояние мира перенесено: …»;
  - at the same t the temperature changes only by the degrees of freedom: 306.69098 · 8997/9000 = 306.58875 K, equal to
    1e-9. The energy per atom changes by the pairs across the former periodic faces, which the walls cut.
- `test_carryover.py`, `test_playground.py` and `test_checkpoint.py` / `test_restore.py -k p03` (twice) pass.
