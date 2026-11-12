# Response to review LB1-physics (2026-11-11): index

Processed 2026-11-11/12 by two processing agents, none of whom wrote the review or the code under review
(`../README.md`). This file is only the index, written by the integrator's assistant when the folder was archived: the
decisions, the fixes and their verification are in the part files. The review text is not edited.

**Part files.**
- `RESPONSE_p03.md`: molecular dynamics and p03 — P2, P3, P4, P8, P9, P11, P13 and the molecular-dynamics parts of P12
  and P15. Its checks are in `response_checks_p03/`, which also hold the checks of LB1-framework F5 (p03) and
  LB1-p02-ux X4 (p03).
- `RESPONSE_p04-p01.md`: the lattice Boltzmann method, p04 and p01 — P1, P5, P6, P7, P10, P14 and the LBM and p01 parts
  of P12 and P15. Its checks are in `response_checks_p04-p01/`, which also hold the browser checks of LB1-framework F5
  (p04) and LB1-p02-ux X4 (p01), X14.

## Decisions

| ID | severity | one line | decision | STATUS | part file |
|---|---|---|---|---|---|
| P1 | error | the running conservation bound is not a worst case: it fails correct long runs | fixed at the cause (Kahan-compensated books on both devices, summed exactly per owner) [error in earlier] | V41 (ac) closed | p04-p01 |
| P2 | should-fix | −P dV with the virial pressure is not the first-order work with a field, soft walls or frozen atoms | fixed (the affine stress, `MD.affine_stress`) [error in earlier] | — | p03 |
| P3 | should-fix | a live box change is one jump; the slow-limit test cannot see irreversibility | fixed (`MD.ramp_box`; p03's «Время изменения размера», 50 ps by default) [error in earlier] | V42 (m) (hard spheres change the box by a wall only) | p03 |
| P4 | should-fix | soft ↔ hard: MD walls act on centres, hard-sphere walls on surfaces | fixed (`HardSpheres(walls_on="centre")`, used by `hard_from_md` and p03) [error in earlier] | — | p03 |
| P5 | should-fix | the spin/charge «what if» rule is physics in the world's code | fixed (`theories.alternatives.kn_change_whatif`, with tests and its conflicts stated) | — | p04-p01 |
| P6 | should-fix | the what-if silently clamped ZAMO speeds at 0.999 c; photons' frequency reset to 1 | fixed (no limit below c; a photon's ZAMO frequency kept) [error in earlier] | — | p04-p01 |
| P7 | should-fix | the "remap" book makes the balances blind to the transfer | fixed (stated everywhere; p04's body-force Poiseuille reference, which a wrong transfer breaks) [error in earlier] | — | p04-p01 |
| P8 | nit | the wall mode said «no work» next to a soft wall | fixed [error in earlier] | — | p03 |
| P9 | nit | «phase-space volume kept» holds only relative to the centre of mass | fixed (stated; the Jacobian tested) | — | p03 |
| P10 | nit | the «measured» radial period doubled at a mass change; stale passages survived a what-if | fixed (passages in world seconds, cleared at a change of the hole) [error in earlier] | — | p04-p01 |
| P11 | nit | p03's restore test compared only drawing positions | fixed (the whole engine state, bit for bit) | — | p03 |
| P12 | nit | tolerances not derived; a core function untested; no closed-form test of the dye transfer | fixed (MD: derived orders; LBM and p01: tests, tolerances derived or labelled; `remap_memory_estimate` fell 8–15 % short [error in earlier], corrected) | — | p03 (MD); p04-p01 (LBM, p01) |
| P13 | nit | p03's «сейчас можно до …» bisection ignored the 10 % bond limit | fixed (not reachable in p03; made consistent) | — | p03 |
| P14 | nit | a new nx silently changed Ly | fixed (stated in the event with the nx that keep both lengths; not refused) | — | p04-p01 |
| P15 | nit | docs: STATUS V42 (l) stale; Lagrava's misprinted Eq. (4.12); the Newtonian throw limits inconsistent | fixed (the citation and the throw limits in the docs; the STATUS texts, V42 (l) and V41 (ac), given to the integrator and applied 2026-11-12) | V42 (l) updated | p03 (MD part: «open → integrator»); p04-p01 |

Found while processing (recorded in `../2026-11-11_internal_LB1-framework/RESPONSE_p03.md`, F5): p03's solver started at
time 0 in a world built from a scene with a later time [error in earlier]. Changed while processing for other reviews:
`Flow2D.adopt` (LB1-framework F5), p01's Kerr throw limit and p04's u_max event (LB1-p02-ux X4, X14).

## Totals

15 findings (1 error, 6 should-fix, 8 nits):
- **15 fixed** (P15's STATUS part applied at the integration of 2026-11-12);
- **0 partly fixed, 0 rejected, 0 deferred**; P3's hard-sphere remainder recorded as V42 (m).

By part file, as each states it: p03 — 8 fixed, 1 open to the integrator (P15's molecular-dynamics part: the STATUS
text); p04-p01 — 8 of 8 fixed.

STATUS items changed by this review: V41 (ac) closed; V42 (l) (p03's and p04's parts closed), V42 (m) opened.
