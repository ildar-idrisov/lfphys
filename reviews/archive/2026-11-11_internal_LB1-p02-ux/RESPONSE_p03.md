# Response (p03 part of X4): review LB1-p02-ux, 2026-11-11

Processed 2026-11-12 by a processing subagent (prefix `lf-lpm-`), not the review's author and not the author of the
code. p01's part of X4 is in `RESPONSE_p04-p01.md`; the framework's (units in the readout, the scale) is in
`RESPONSE_framework.md`. Checks and screenshots: `../2026-11-11_internal_LB1-physics/response_checks_p03/`.

## X4 (p03) — fixed [error in earlier]

**Reproduced, and the cause is larger than the review says.** The player computes a throw in the world's units, length
per world time: here nm per second of world time, the units of the frames' `at` and `t`. p03's handles named its
velocity parameters vx, vy, vz, which are in m/s. A flick of 1.9·10¹² nm/s (1 900 m/s) was therefore taken for
1.9·10¹² m/s and refused by the schema («больше наибольшего 100000»). Even a correct `velocity_max` in m/s would have
been off by 10⁹.

**Fix** (`visualizations/p03_molecules/viz.py`):
- The handles' velocity is now hidden parameters `throw_vx`, `throw_vy`, `throw_vz`, in nm/s. Their label is «Бросок:
  скорость центра масс v…, нм/с», so the player's readout carries the unit.
- `_set_obj` turns a throw into the object's vx, vy, vz in m/s (÷10⁹), applied even when the value equals the stored
  one.
- A 3-D scene carried into a plane drops `throw_vz`.
- `handles["velocity_display"] = {"unit": "м/с", "factor": 1e-9}` on every type with a throw (gas, crystal, atom,
  molecules; the framework's display handle of 2026-11-12). The player's readout and the edit's log line show the throw
  in m/s; the edit, the world and `velocity_max` stay in world units (nm/s).
- `handles["velocity_max"] = 5·10¹¹` nm/s, that is 500 m/s, stated in the README and in the code. It is about the
  speed of sound of argon gas at room temperature and above its thermal speed.
- The default step (10 fs) resolves a 300 K argon group thrown at it: q = 12 v dt / r_t = 0.34 in a plane and 0.37 in a
  volume, against Q_MAX = 0.4.
- A hotter, lighter or faster group is refused by the step, with what to change («скорость центра масс не больше … или
  «Шаг по времени» не больше …»). The refusal names the step, not the schema's range.
- README: the handles' paragraph.

**Verified.**
- `test_p03_lab.py::test_the_largest_throw_is_resolved_by_the_default_step[2d|3d]`:
  - q = 0.34 / 0.37 as stated;
  - a throw at `velocity_max` is taken, and the object's vx is 500 m/s with the group's centre-of-mass velocity
    500 m/s to 1e-9;
  - the control: 1 500 m/s is refused by the step, in Russian, naming «Шаг по времени».
- `test_palette_declares_handles`, `test_drag_moves_…_a_throw_gives_its_centre_a_velocity` and
  `test_atom_drag_keeps_its_velocity_and_a_throw_keeps_its_place` now send the throw in nm/s. The palette test checks
  `velocity_display` on the four types; the drag test checks that the log line reads «м/с» (300) and not «нм/с».
- In the browser (`p03_lab_shots.out`, `x4_throw_readout_m_s.png`, `x4_throw_after.png`), a real Shift+drag on a gas:
  - the ghost's readout «бросок: v = (60,7; −24,1) м/с (×0,0206, авто)» during the gesture;
  - sent (6.07·10¹⁰, −2.42·10¹⁰) nm/s;
  - the log line «бросок: v = (60,69; −24,15) м/с»;
  - the object's vx, vy = (60.69, −24.15) m/s, no refusal.
- In the run before the display handle, the same gesture read «(5,95·10¹⁰; −2,37·10¹⁰) нм/с» and gave vx = 47.96 m/s.
  The system's momentum Px = 60 × 39.948 u × 47.96 m/s = 114 954 u·m/s, as the instruments showed.
- `manipulation.mjs` for p03: 4/4 (rerun after the display handle).

**Display unit.** The framework added `handles["velocity_display"]` on this processing's suggestion; p03 declares it (above).
