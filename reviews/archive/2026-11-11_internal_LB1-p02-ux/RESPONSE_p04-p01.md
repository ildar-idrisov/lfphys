# Response (part): LB1-p02-ux — X4 (the p01 Kerr part) and X14

Processed 2026-11-11/12 by a processing agent that wrote neither the review nor the reviewed code. The rest of X4 (the
framework and p03) is answered in `RESPONSE_framework.md` and `RESPONSE_p03.md`. Rules: `../README.md`.

### X4 (p01 Kerr) — the default throw gave 2.33 c and was refused

**Reproduced** from the code: p01's Kerr bodies declared no `velocity_max`, so the player's automatic throw scale was ×1
(a flick of a few hundred pixels per second became tens of thousands of G M/c² per second).

**Decision: fixed** (`p01_gravity/viz.py`): the Kerr body's handles declare `velocity_max` as the body's hidden parameter
`tv_max`, half the speed of light in the drawing coordinates (0.5 G M/c² per G M/c³ = 0.5/T per world second), set from
the hole's mass when the body is placed and renewed when the mass changes; the throw parameters carry their unit
«(G M/c²)/с» (the readout had none). So a brisk flick gives a quarter of c. Near the hole the ZAMO-measured speed of the
same drawn velocity is larger (by 1/α); a throw at 0.99 c or more by it is still refused, with «уменьшите масштаб
броска». README states the limit.

**Verification.** `p01_gravity/tests/test_p01_lab.py::test_the_radial_period_restarts_when_the_hole_changes_and_the_throw_limit`
(the handle names `tv_max`; its value 0.5/T, renewed at M 10 → 20). Browser (private server, the manipulation check with
the preset «kerr_orbits», `../2026-11-11_internal_LB1-physics/response_checks_p04-p01/manip_kerr.mjs`, a copy of `manipulation.mjs` with that one preset; `manip_kerr.out`): the throw of «Наклонная орбита»
reads «бросок: v = (484; 200; −281) (G M/c²)/с (×0,038, авто)» and is applied (≈ 0.03 c; before: 2.33 c refused).

### X14 — p04's message after a change of the largest speed reports a 2 % mass change

**Reproduced** (the reviewer's `b7_p04_umax_api.out`; the same in a test): u_max 0.6 → 0.15 m/s booked +0.0171 kg/m of
0.895 kg/m.

**Judgement (the physics).** Not an error of the transfer and not a change of the fluid: the transfer keeps the
pressure, and the weakly compressible scheme's density for that pressure is ρ₀ + p/c_s², with c_s the scheme's sound
speed (u_max/0.1, or more where the time step is capped by τ). u_max ÷ 4 makes c_s ÷ 4 and the density deviation × 16, so
the lattice mass changes by Σ p dA (1/c_s′² − 1/c_s²). The incompressible fluid's mass ρ·S is unchanged. The running
«Перепад плотности» check keeps the scheme within its compressibility limit; a refusal is not warranted.

**Decision: fixed (the message).** `p04_fluids/viz.py` `_regrid`: the event gives the transfer's mass change in kg/m and
in %, and its parts — «из этого … кг/м — сжимаемость схемы, не жидкости: давление перенесено как было, а плотность схемы
при том же давлении ρ − ρ₀ = p/c_s², а скорость звука схемы … сменилась … м/с» (computed from the pressure integral
before the change), the fluid of a new part of the domain, the rest (interpolation, re-voxelised bodies) — and the
incompressible fluid's mass ρ·S; and it says that the balances close by construction across the transfer (review
LB1-physics P7).

**Verification.** `p04_fluids/tests/test_p04_lab.py::test_a_new_nx_states_the_new_height_and_the_scheme_compressibility`
(u_max 0.3 → 0.12 on the DFG channel: the booked mass change equals the pressure integral's prediction to 1 %, and the
event attributes it to the scheme). Browser: `../2026-11-11_internal_LB1-physics/response_checks_p04-p01/p04_event_umax.png` (the event in «События»).

**Counts (this part): 2 of 2 fixed.**
