# Review: the physics of batch LB1, plan P16.1 (laws changed at the current moment)

**Status: awaiting processing.** Reviewer: an internal subagent (Claude Opus), not the author of the code. Delivered
2026-11-11. Per `reviews/README.md`, the reviewer does not write `RESPONSE.md`, decide on the findings, or archive this
folder.

## Scope

1. Molecular dynamics: `MD.deform` (the affine mode and the wall mode), `MD.adopt`; `HardSpheres.deform`,
   `hard_from_md`, `md_from_hard`, `contact_violations`, `hard_blockers`; `lfphys/tests/test_md_deform.py`; the world
   `visualizations/p03_molecules/viz.py` (live dynamics, Lx/Ly/Lz, box_mode, handles, measurables) and its
   `tests/test_p03_lab.py`.
2. Lattice Boltzmann: `Flow2D.remap` (refinement, coarsening, the domain, a new time step), `tests/test_lbm_remap.py`,
   the world `p04_fluids/viz.py` (live nx, Lx/Ly, anchor/fill, u_max) and `tests/test_p04_lab.py`.
3. Gravity: the Kerr–Newman hole as a scene object in `p01_gravity/viz.py` (the mass as a change of units; the spin and
   charge as a declared "what if"), the binary's total mass, throws; `core.gravity.kerr_newman`
   (`rescale_proper_time`), `tests/test_p01_lab.py`.
4. The pre-existing STATUS V41 (ac): is the running conservation bound a worst case?

The files as reviewed are pinned by their SHA-256 in `reviewed_files.sha256`. None of them changed while the review
ran (checked with `find -newermt` at the end).

## Environment and reproduction

All scripts ran in Docker on the CPU, from `engine/`, one container at a time:

```
docker run --rm --name lf-lbrp-<x> --memory=8g --cpus=8 \
  -v .../light-funnel/engine:/lf:ro -v .../reviews/2026-11-11_internal_LB1-physics:/out \
  -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/<script>.py [parts]
```

The image `light-funnel-viz` (959a1b91570e) has Python 3.11.17, NumPy 2.4.6 and SciPy 1.17.1. The lab tests ran with
`--memory=10g -w /lf/visualizations`. No GPU was used, so the GPU-after-remap test was skipped.

| script | output | what it checks |
|---|---|---|
| `md_deform_checks.py` | `md_deform_checks_AD.out` (parts A, D), `md_deform_checks_CE.out` (C, E, D), `md_deform_checks_B.out` (B) | A: the ideal-gas adiabat, and an independent slow driven piston; B: W against the trapezoid, and a compress/expand cycle; C: first-order dE against −P dV with a field, soft walls and frozen atoms; D: the Jacobian of the step; E: switching to hard spheres in walled boxes |
| `lbm_remap_checks.py` | `lbm_remap_checks_PBT.out` (P, B, T), `lbm_v41ac.out` (V, O) | P: Poiseuille across a remap with three variants of the antisymmetric factor; T: Taylor–Green; B: a deliberately wrong transfer against the balance; V: STATUS V41 (ac); O: an open channel |
| `lbm_open_long.py` | `lbm_open_long.out` | the running bound on the open channel to 128 000 steps |
| `lbm_dye_check.py`, `lbm_dye_check2.py`, `lbm_dye_check3.py` | `.out` of each | the dye (D2Q5) across a remap: a Gaussian against the exact solution, and its second moment |
| `kerr_checks.py` | `kerr_checks.out` | M: the mass as a change of units, against a world never changed; W: the what-if near the horizon; R: the measured radial period across a mass change |
| `restore_checks.py` | `restore_checks.out` | p03 rebuilt by replay after the live box, the switch and drags: the whole engine state |
| `p03_softwall_wallmode.py` | `p03_softwall_wallmode.out` | p03's wall-mode event next to a soft wall |
| `verify_quotes.py` | `verify_quotes.out` | every quotation below, found in the extracted source text |
| (pytest) | `authors_engine_tests.out`, `authors_lab_tests.out` | the authors' tests: engine 26 passed, 1 skipped (GPU); lab 31 passed |

The variants of the LBM transfer were built in memory. The scripts patch one line of a copy of `lbm.py`'s source (the
factor `km` or `kgm`, or a 1 % error in the transferred velocity), and the engine files are not touched.

`md_deform_checks.py` was edited after part A ran: the soft-wall case of part C now builds its own system. Part A did not
change. `restore_checks.py` lost one dead line after its run.

## Sources

The papers were downloaded to the session's scratch folder, outside the repository. Every quotation was checked by
`verify_quotes.py` (all found).

| source | obtained | used for |
|---|---|---|
| D. Lagrava Sandoval, *Revisiting grid refinement algorithms for the lattice Boltzmann method*, PhD thesis, Univ. Geneva 2012 (archive-ouverte unige:26414, open) | yes (PDF; pages 54–55 also read as rendered images) | the DC rescaling, Eqs. (4.1), (4.10)–(4.15) |
| A. Dupuis & B. Chopard, Phys. Rev. E 67, 066707 (2003) | **no**: the Geneva archive record unige:120658 lists the file as "Restricted" | only through Lagrava's account |
| H. C. Andersen, J. Chem. Phys. 72, 2384 (1980); G. J. Martyna, D. J. Tobias & M. L. Klein, J. Chem. Phys. 101, 4177 (1994) | **no** (paywalled) | through open secondary sources: Kolb & Dünweg, J. Chem. Phys. 111, 4453 (1999), arXiv:cond-mat/9903423 (Andersen's scaled variables, their Eqs. 12–17); Quigley & Probert, arXiv:cond-mat/0403756, Eq. (5a, b) (the MTK equations with the factor 1 + d/N_f) |
| H. J. C. Berendsen et al., J. Chem. Phys. 81, 3684 (1984) | **no**: the Groningen repository copy sits behind a bot check | not verified |
| J. M. Bardeen, W. H. Press & S. A. Teukolsky, ApJ 178, 347 (1972), the ADS scan | yes; its OCR is garbled, so Eqs. (2.3)–(2.5), (3.9) and (3.10) were read from the rendered pages 349 and 355 | the ZAMO (LNRF) quantities and velocities |
| T. Adamo & E. T. Newman, *The Kerr–Newman metric: a review*, arXiv:1410.6626 | yes | the KN horizons, Eq. (3.18) |

Quotations used:

* Lagrava on DC: "with the exception that the rescaling is applied before the collision"; "We consider that the
  convective scaling is used."; on the non-equilibrium part: "the non-equilibrium part fineq = fi − fieq is proportional
  to the gradient of the velocity, it is therefore necessary to rescale it when communi- cating it between grids"; on
  Filippova–Hänel: "The authors find that a constant relates the post–collision non–equilibrium part"; on interpolation:
  "a four-point symmetric cubic interpolation is mandatory, as it ensures that the method remains second order
  accurate".
* Kolb & Dünweg on Andersen: "The Andersen method [8] uses the box volume V = Ld and the scaled coordinates"; "however,
  the second term is deliberately omitted in order to achieve independent fluctuations of L and ~si" (their Eq. (15),
  π_i = m_i L² ṡ_i, makes the physical momentum π/L at fixed π: the 1/L scaling the engine uses).
* BPT: "the locally nonrotating frames (LNRF) for which the observers…"; "[the 3-velocity] relative to the LNRF has
  components" (Eq. 3.9), followed by v^(φ) = e^{ψ−ν}(Ω − ω) (Eq. 3.10). The functions in Eq. (2.5) are e^{2ν} = ΣΔ/A,
  e^{2ψ} = sin²θ A/Σ and ω = 2Mar/A.
* Adamo & Newman: "These surfaces are referred to as the outer (r+ ) and inner (r− ) horizons", with r± = M ± (M² − a² −
  Q²)^{1/2} (Eq. 3.18).

The engine's formulas agree with these sources. `kerr_newman.zamo` uses Eq. (2.5) with the KN replacements Δ = r² − 2r +
a² + Q² and ω = a(2r − Q²)/A. `Geodesics.zamo_velocity` and p01's `_zamo_of_throw` are BPT (3.9)–(3.10). Andersen's
scaled-variable volume step is the engine's x → λx, p → p/λ. MTK's momentum factor is (1 + d/N_f), so the engine's "MTK
up to O(1/N_f)" is right. Lagrava's DC factor is τ_f δt_f / (τ_c δt_c), applied before collision (see P15 for a misprint
in the thesis).

## Summary

| # | severity | finding | tag |
|---|---|---|---|
| P1 | **error** | STATUS V41 (ac) confirmed: the running conservation bound is not a worst case. It fails correct runs: a closed channel after 9 537 steps, an open channel after 64 000 | [error in earlier] |
| P2 | should-fix | "dE = −P dV to first order with the virial" is false with a field (−61 %), soft walls (+19 %) or frozen atoms (−36 %). p03's event shows the mismatching number | [weakens] |
| P3 | should-fix | A live box change is one instantaneous jump of any size. The "slow → adiabatic" claim is not what the owner gets, and the test of the slow limit is fast and cannot see irreversibility | [weakens] |
| P4 | should-fix | Soft ↔ hard: MD walls act on centres, hard-sphere walls on surfaces. The switch is refused almost always in walled boxes, and the accessible volume jumps 7–11 % unstated | [weakens] |
| P5 | should-fix | The spin/charge "what if" rule is physics in the world's code, not in `theories.alternatives` (LAYERS). It has no engine test and no ABOUT/conflicts, and its coordinate dependence is not stated | [neutral] |
| P6 | should-fix | The what-if silently clamps ZAMO speeds above 0.999 c, so "the velocity is kept" is false near the horizon. Photons' local frequency is reset to 1 | [weakens] |
| P7 | should-fix | The "remap" book closes the balances by construction: a 1 % error in the transferred velocity passes every running check, yet p04's test and README cite those checks | [weakens] |
| P8 | nit | The wall-mode event says "no work" next to a soft wall, where W_box = +1.15 ε | [error in earlier] |
| P9 | nit | "Canonical, phase-space volume kept" is exact only relative to the centre of mass (det J = λ per conserved axis) | [neutral] |
| P10 | nit | The "measured" radial period Tr doubles at a mass change without a new passage, and stale passages survive a what-if | [neutral] |
| P11 | nit | p03's restore test compares only 16-bit drawing positions. The whole state does match (checked here) | [useful] |
| P12 | nit | Tolerances are not derived. A core function has no engine test. There is no closed-form test of the dye transfer | [neutral] |
| P13 | nit | p03's "сейчас можно до …" bisection ignores the 10 % bond limit | [neutral] |
| P14 | nit | p04: a new nx silently changes Ly (2.2 × 0.41 m, nx 333 gives Ly 0.40961 m) | [neutral] |
| P15 | nit | Docs: STATUS V42 (l) is stale. The cited Lagrava range contains a misprinted Eq. (4.12). The Newtonian throw limits are inconsistent | [neutral] |

**Counts: 1 error, 6 should-fix, 8 nits.**

What holds (confirmed by my own runs; details at the end): the ideal-gas adiabat, which an independent slow-piston run
also confirms; first-order −P dV in periodic matter; the TRT antisymmetric factor, which the author derived and which
discriminates (Dupuis–Chopard's single factor is about 10⁸ times worse on Poiseuille); a consistent dye transfer; the mass as an
exactly physics-neutral change of units; the ZAMO formulas; and bit-identical restores.

---

## Findings

### P1 — error — the running conservation bound is not a worst case (STATUS V41 (ac) confirmed)

**Location.**
* `lfphys/lfphys/core/fluids/lbm.py:3187–3200`: the bound in `checks()`, `lim = max(1e-12, 2 eps · steps)`.
* `lbm.py:113` and `:3194`: "a worst-case bound".
* `lbm.py:1786–1789`: the per-link accumulators `acc_m`, `acc_p` grow by the gross exchange every step.
* `STATUS.md:52`, V41 (ac).
* `p04_fluids/viz.py:1426–1442`: the check is shown to the owner with its ok flag.

**Evidence** (`lbm_v41ac.out`, `lbm_open_long.out`). The test helper's 4 × 16 channel (τ = 0.8, g = 1e-5, 9 537 steps)
has a momentum residual of **1.698e-11 against the limit 4.235e-12: failed**, exactly as the author reported.

Continuing the run from a fresh baseline:

| steps | engine residual | limit 2 eps n | the same books summed exactly (`math.fsum` of every step's per-link records) | max \|acc_p\| of a link |
|---|---|---|---|---|
| 1 000 | 1.3e-13 | 1.0e-12 | 1.2e-15 | 2.2e2 |
| 8 000 | 1.3e-11 | 3.6e-12 | 8.4e-15 | 1.8e3 |
| 32 000 | 5.4e-11 | 1.4e-11 | 3.4e-14 | 7.1e3 |
| 64 000 | 6.1e-10 | 2.8e-11 | 6.8e-14 | 1.4e4 |

With exact books the residual grows linearly and stays about 400 times inside the bound, so there is no leak. The excess
is the rounding of the per-link accumulators: each one collects the gross exchange of its link, about 0.22 per step, so
its magnitude grows like n. The rounding of each addition is therefore about eps·n, and the total like n² (worst case)
or n^1.5. The STATUS note's reason ("round the same way step after step") is not why the bound fails; the growth of the
accumulators is.

The problem is not confined to the closed channel. The remap test's own open channel (inlet, outlet, interpolated disk;
120 × 24) **fails after 64 000 steps (61.6 s of world time)**: 3.17e-11 against 2.84e-11, then 2.6e-10 against 5.7e-11
at 128 000. Its mass residual approaches its limit too (2.9e-11 against 5.7e-11).

p04 shows this as a failed «Импульс жидкости» on a correct run. LB1 makes worlds that never restart, so such long runs
are the normal use.

**Fix.** Use compensated (Neumaier/Kahan) accumulation of the per-link records on both devices; STATUS already plans
this. Or periodically fold the accumulators into an exactly summed bank (`math.fsum`, or double-double) every K steps,
which keeps their magnitude bounded. Or let the bound grow with the books' gross size: Σ over steps of eps·Σ|acc|, about
eps·n²·(gross per step)/2. Then mark V41 (ac)'s "worst case" as [error in earlier] and add a test: the 4 × 16 channel to
64 000 steps with the check passing.

### P2 — should-fix — "dE = −P dV to first order with the virial pressure" fails where the virial misses a force

**Location.**
* `system.py:1326–1329`: the deform docstring, "i.e. −P dV".
* `system.py:105–110`: the module docstring.
* `system.py:1405–1413`: the returned `pdv`.
* `system.py:1745–1755`: the virial omits the soft walls and the field, and with frozen atoms it is Σ over mobile atoms
  of x·F, while `deform` also moves the frozen atoms.
* p03 `viz.py:1633–1635`: the event shows "−P·ΔV по вириалу до и после".
* p03 `README.md:28`: "to first order it is −P_aa ΔV with the virial pressure".

**Evidence** (`md_deform_checks_CE.out`, part C). The table gives the first-order ratio (dE − pdv)/dE for a uniaxial
δ → 0. A periodic LJ control converges as δ.

| system | δ = 1e-3 | 1e-4 | 1e-5 |
|---|---|---|---|
| periodic LJ (control) | −2.8e-5 | −2.8e-7 | −2.8e-9 |
| walled ideal gas, field g_y = −0.5 | −0.609 | −0.608 | −0.608 |
| walled LJ, soft 9-3 walls on y | +0.189 | +0.188 | +0.188 |
| walled LJ gas around a frozen block | −0.362 | −0.359 | — |

The booked work (ΔE, `W_box`) is correct in all of these cases: the first law closes. What is wrong is the claim that it
equals −P dV with the virial pressure. The comparison number the owner sees is then off at first order, which suggests a
non-quasi-static step where there is none.

**Fix.** Add the missing terms to an "affine virial" used for `pdv`: the field's −Σ m g_a x_a, the soft walls' x_a
F_wall,a (the hi wall moves with the box), and all atoms' x·F when frozen atoms are scaled. Alternatively, return
`pdv = None` and omit the comparison in those cases. In either case, restrict the docstring and README claims and add
first-order tests with a field, soft walls and frozen atoms (the ratio → 0 as δ → 0).

### P3 — should-fix — a live box change is one jump; the "slow compression" claim and its test

**Location.**
* p03 `viz.py:1596–1640` (`_set_box`: one `MD.deform` per change, any size up to the per-atom overlap limit of 50 ε).
* The help texts at `viz.py:103–108` (BOX_HELP: «при медленном сжатии она равна −∫P dV») and `viz.py:184`
  («медленное сжатие — адиабатическое»).
* `README.md:28`.
* `system.py:1327–1328` ("a slow deformation in small steps is the adiabatic (isentropic) work").
* `tests/test_md_deform.py:107–130`: two MD steps (0.008 τ) between the deformation steps.

**Evidence** (`md_deform_checks_B.out`; 2-D LJ, 100 atoms, ρ = 0.39, T = 1.5; 15 % compression of x, then back). For an
adiabatic quasi-static process the net work of the cycle tends to 0.

| N steps | MD steps between | W of the compression | net work of the cycle | Σ(W − PDV) over the cycle |
|---|---|---|---|---|
| 1 | 400 | 218.7 | **+182.6** | −77.9 |
| 4 | 100 | 61.7 | +21.5 | −0.59 |
| 16 | 2 | 91.2 | +35.6 | −5.4e-2 |
| 64 | 2 (the test's spacing) | 57.1 | +17.6 | −9.5e-4 |
| 256 | 2 | 46.1 | +5.75 | −3.6e-4 |
| 16 | 25 | 47.9 | +12.4 (seed 3); seeds 3–6: 12.4, 2.1, 3.8, 7.5 (mean 6.4) | −1.8e-2 |
| 64 | 6 | 45.3 | +1.53 | 6.7e-4 |
| 64 | 25 | — | seeds 3–6: 0.40, −1.27, 1.61, 1.13 (mean 0.47) | — |
| 64 | 50 | 39.0 | −3.2 (one seed: noise of the integrator and the statistics) | 4.5e-4 |

Σ(W − PDV) falls as 1/N² (the trapezoid uses the instantaneous virial right after each jump). The dissipation falls far
more slowly: at the test's spacing, N 16 → 64 → 256 only reduces it by ×2.0 and ×3.1, while Σ(W − PDV) drops by ×57 and
×2.6 from an already tiny value. So the test's convergence of W − PDV holds for a strongly irreversible process (+17.6 ε
per cycle at its own spacing) and cannot confirm the adiabat for interacting matter.

In p03 itself (`restore_checks.out`, second scenario), three live changes 12 × 12 → 11 × 12 → 11 × 11 → 12 × 12 nm leave
W_box = +13.2 ε for 120 atoms. That is about +0.11 ε/k, or about 13 K of heating from compress-and-return.

The independent check does hold (`md_deform_checks_AD.out`, part A). A collisionless gas compressed 30 → 21 along y by a
slow driven piston (the engine's own piston, an independent second method) keeps K_y L_y² to 0.99999 at w/v_th = 0.002.
The work is 218.042 against the affine step's 218.044. The ideal-gas adiabat therefore holds by an independent route,
not only algebraically as in the tests.

**Fix.**
1. Offer a ramp: the asked size reached over a chosen time in small affine steps between MD steps, like a barostat or a
   driven piston. Keep the instantaneous jump as an explicit option, and say in the event which one happened (|λ − 1|,
   and that a jump is not quasi-static).
2. Replace the "slow" test by a reversibility test: the net work of a compress/expand cycle → 0 as the rate → 0, with
   several seeds and derived tolerances.
3. Add the slow-piston comparison as the ideal gas's second method.

### P4 — should-fix — soft ↔ hard: the two solvers' walls are different walls

**Location.**
* `system.py:1560–1566`: MD's hard walls act on centres, x ∈ [0, L].
* `hard.py` docstring: hard-sphere centres stay in [σ/2, L − σ/2].
* `hard.py:984–1008` (`contact_violations`) and `:1033–1058` (`hard_from_md`).
* p03 `viz.py:1550–1561`.
* p03 `README.md:24`.

**Evidence** (`md_deform_checks_CE.out`, part E: an equilibrated WCA gas in a walled 2-D box, 200 sampled moments).

| case | switch possible | refused only by the walls |
|---|---|---|
| n = 20, L = 20 | 18/200 | 170/200 |
| n = 60, L = 30 | 7/200 | 156/200 |
| n = 200, L = 30 | 0/200 | 34/200 |

The rest are refused by pairs. The probability that no centre lies within σ/2 of a wall is about (1 − σ/L)^{2n}.

When a switch does happen, the area accessible to the centres jumps from L² to (L − σ)²: 10.8 % denser at L = 20, 7.0 %
at L = 30. Going back to forces it expands into the σ/2 layers. Neither the README nor the event states this pressure and
density jump; only the energy jump is stated.

**Fix.** Make the walls the same physical walls. One way: build the hard world with the wall planes at −σ/2 and L + σ/2
(a box L + σ shifted by σ/2 along walled axes); for mixtures, use σ_max and state the residual for the smaller species.
Another: give `HardSpheres` walls that act on centres. Either way, state the change of the accessible volume in the event
and the README.

### P5 — should-fix — the "what if" rule is physics in the world, outside the engine's layers

**Location.** p01 `viz.py:1573–1633` (`_what_if_metric`); `README.md:26–32` ("The rule is the world's (a model,
orchestration …), not the engine core's"); `engine_modules()` of the Kerr mode returns only `core.gravity.kerr_newman`.

**Why.** LAYERS §1 puts "modified or refuted laws for declared 'what if' studies" in `theories.alternatives`. §2 rule 5
says a visualization's own code is orchestration (time line, events, apparatus logic) and drawing, and that its physics
comes from the engine.

The rule is a physical matching condition at a metric jump. It keeps the Boyer–Lindquist place, the proper time and the
ZAMO velocity; it recomputes E, L and K; it moves captured bodies to the new r₊; it re-anchors observers.
`theories.models` (phenomenology with fitted parameters) does not fit it; `alternatives` does.

Outside the engine the rule has:
* no ABOUT and no conflicts;
* no engine test;
* no entry in `engine_modules()`, so the player's «Физика этого мира» cannot show its layer.

Its main caveat is not stated anywhere: BL coordinates of different (a, Q) do not label the same physical places. Keeping
the circumferential radius, or keeping E and L, are equally defensible rules that give different worlds.

**Fix.**
1. Move the rule to `lfphys/theories/alternatives/` (e.g. `metric_jump.py`): a function taking a `Geodesics` and the new
   (a, Q) and returning the new `Geodesics`, or a refusal with the reason.
2. Give it an ABOUT with layer `alternatives` and conflicts: no established dynamics, and dependence on the coordinates.
3. Give it tests: an unchanged (a, Q) gives back the state bit for bit; the ZAMO velocity is kept to rounding; the
   refusals work.
4. List it in the world's `engine_modules()`.

### P6 — should-fix — the what-if silently clamps speeds above 0.999 c

**Location.** p01 `viz.py:1593`: `vv = vz[i] * min(1.0, 0.999 / |vz|)`. The event at `:1630–1633` and the README say
that each body keeps its ZAMO-measured velocity.

**Evidence** (`kerr_checks.out`, part W). A body falling radially into an a = 0.9 hole was at r = 1.4363025, with
r₊ = 1.4358898, |v| = 0.9990030 and γ = 22.40. After a → 0.95 it had |v| = 0.9990000 and γ = 22.37. The event says
«каждое тело сохранило … скорость», and nothing mentions the clamp.

Here the change is small. But γ = E/α near the horizon with α ∝ (r − r₊)^{1/2}, so at the capture radius
(r₊ + 1e-4) the same body has γ ≈ 45 by this scaling (an estimate). The clamp to γ = 22.4 would then halve its energy.

For photons, `momentum_from_zamo(…, n=…)` uses its default ν = 1. The direction is kept, but the photon's local frequency
(its E) is reset.

**Fix.** `momentum_from_zamo` accepts any |v| < 1, so keep v as it is. If a cap is wanted, refuse or flag the change
with the body named and its change of E stated. For photons, pass the ZAMO-measured frequency as ν.

### P7 — should-fix — the "remap" book makes the balances blind to the transfer

**Location.**
* `lbm.py:2326–2331` (the docstring: "booked as 'remap', so the balances' residuals stay round-off") and `:2662–2669`.
* p04 `README.md:34` ("booked as «remap», so the running balances still close to round-off").
* `test_p04_lab.py::test_the_grid_changed_live_continues_the_flow` ("every running check passes").

**Evidence** (`lbm_remap_checks_PBT.out`, part B). I injected a deliberately wrong transfer: the transferred u_x × 1.01
on the Poiseuille channel, refined. The momentum check still says ok = True, with a residual of 6.4e-13, identical to the
correct transfer. The error went into the "remap" book (1.9e-4 instead of 2.0e-5), and the flow is 1.0e-2 off the
parabola.

The engine's own tests check the transfer against closed forms, so the engine is covered. But the running checks and the
p04 test that cites them cannot fail for a wrong transfer.

**Fix.** Say in the docstring and README that the balances close by construction across a remap. Add a check of the
transfer itself. For example, compare the booked transfer with an a-priori bound (the interpolation error estimated from
the fields' fourth differences, or a second interpolation of another order). Alternatively, show the transfer in the
event as unchecked. In the p04 test, assert something that a wrong transfer would break, e.g. Poiseuille in a p04 world.

### P8 — nit — the wall-mode event says "no work" next to a soft wall

**Location.** p03 `viz.py:1627–1628`; `README.md:28` ("a free expansion (Joule) with no work").

**Evidence** (`p03_softwall_wallmode.out`). In a walled 6 × 6 nm box with a soft upper wall, Ly 6 → 6.15 nm in «стенка»
mode books **W_box = +1.153 ε**: the engine is right, because the wall's potential under nearby atoms changed. The event
nevertheless reads «… сдвинута стенка …, работы над системой нет». The engine's docstring is correct ("a soft wall's
energy change is work").

**Fix.** State W when it is not 0.

### P9 — nit — "the canonical point transformation (phase-space volume kept)"

**Location.** `system.py:1319–1323`; p03 `README.md:28`; `BOX_HELP`.

With the centre-of-mass velocity kept along conserved axes, the map moves the centre of mass by λ and keeps its momentum.
The Jacobian determinant is then λ per conserved axis; it is 0.9 for λ = 0.9 (part D). This is physically right (the
momentum is conserved), but the statement is exact only for the motion relative to the centre of mass.

**Fix.** Say so.

### P10 — nit — the "measured" radial period across a change of the hole

**Location.** p01 `viz.py:1999–2001`.

`Tr = clk.sec(pp[1]) − clk.sec(pp[0])` converts passages recorded before a mass change with the new seconds per M. It
jumps from 0.04373 s to 0.08746 s at the change, without a new periapsis (`kerr_checks.out`, part R). After a what-if,
`self.peri` keeps the old orbit's passages.

**Fix.** Store the passage times in seconds, and clear them on a what-if.

### P11 — nit — p03's restore test compares only drawing positions

**Location.** `test_p03_lab.py:435`.

The test compares `q`, the 16-bit positions sent for drawing (STATUS V42 b), plus `box_nm` and `at`. My check
(`restore_checks.out`) compares the whole `md.state_dict()`: positions, velocities, generator, energies and books, after
hard → wall box → forces → drag → affine box, and after an LJ box cycle. Every key is equal and the balances are equal,
so the claim holds [useful].

**Fix.** Assert the whole state, as p01 and p04 already do.

### P12 — nit — tolerances and coverage

* `test_md_deform.py:126, 128, 130` (0.02|W|, 0.05|W|, 2e-3|W|), the TG bounds in `test_lbm_remap.py` (2e-4, 1.2×, 0.5×)
  and the p01 lab test's rtol 1e-7 are measured margins, not derived ones.
* `Geodesics.rescale_proper_time` is a core function tested only through the world (LAYERS admission (c)).
* `remap_memory_estimate` is tested only as larger than `memory_estimate`.
* The dye's transfer has no closed-form test. A sharp one is its second moment (`lbm_dye_check3.out`): the engine keeps
  the coarse history's variance offset unchanged across a refinement (0.16420 → 0.16385, tracking the coarse-alone
  curve). The variants change it at once: −0.041 with kgm = 1, and +0.020 with kgm = kgp.

  The first, absolute-error comparison (`lbm_dye_check*.out`) is misleading taken alone. There, kgm = 1 looks more
  accurate only because its error cancels part of the coarse grid's own variance offset, which diffusion never removes.
  Add the moment test.

### P13 — nit — the size p03 says fits may itself be refused

**Location.** p03 `viz.py:1659`.

The bisection behind «сейчас можно до …» calls `deform(...)` without `max_bond_strain`. With molecules, the size it names
can exceed the 10 % bond limit, and the owner's next try is then refused for another reason.

**Fix.** Pass `MAX_BOND_STRAIN`.

### P14 — nit — a new nx silently changes the domain

**Location.** p04 `viz.py:1061–1066`.

dx = Lx/nx, and ny = round(Ly/dx). For the DFG channel 2.2 × 0.41 m and nx = 333: dx = 6.607 mm, ny = round(62.06) = 62,
so Ly = 0.40961 m. The channel is 0.39 mm lower, and the set-up is no longer the DFG one the «Эталоны» recognise. The
event names the nodes, not the new height.

**Fix.** Keep both lengths (refuse, or pick the nearest nx that divides both), or state the new Ly in the event.

### P15 — nit — documents

* `STATUS.md:53`, V42 (l) still lists "p03 the box sizes …, p04 the grid and domain … and the largest expected speed" as
  "not possible with the engine as it is". STATUS was not touched in LB1 (perhaps pending).
* `lbm.py:2303` cites Lagrava "Eqs. (4.1), (4.10)-(4.15)". On page 54, the thesis's Eq. (4.12) reads
  α = (δt_c/δt_f)(τ_f/τ_c), and the middle member of (4.13), (δt_f τ_c)/(δt_c τ_f), agrees with it but not with the
  right-hand side 2τ_c/τ_f (for δt_f = δt_c/2). Only the right-hand side and (4.14)–(4.15) correspond to f^neq ∝ τ δt.
  The engine uses the correct τ′dt′/(τ dt), which my Poiseuille controls confirm. Cite (4.13)–(4.15) and note the
  misprint, so that nobody copies (4.12).
* The Newtonian throw: the client's handle clamps at 0.05 c (`viz.py:666`), the server refuses only from 0.1 c
  (`viz.py:960`), and the hidden parameters allow ±1 au/s (≈ 500 c). The README's "up to 0.05 c" is the client's rule.
  Say that 0.05–0.1 c is accepted (as Newtonian, about 1 % off).

---

## What holds (my own runs)

* **The ideal-gas adiabat** [useful] (`md_deform_checks_AD.out`). T V^{2/d} is kept to 4.4e-16 in 2-D and 3-D over ten
  steps. An independent slow driven piston (w/v_th = 0.002) gives K_y L² = 0.99999 of its start and work 218.042, against
  the affine step's 218.044. This is the second method the engine's tests lack.
* **−P dV to first order in periodic matter** [useful]: (dE − pdv)/dE = −2.8e-9 at δ = 1e-5, scaling as δ.
* **The refusals** [neutral]:
  * The bond strain (10 %), the overlap (50 ε per atom), the piston's axis, the periodic axis in wall mode and the time
    step: all in the authors' tests, and all bit-for-bit transactional.
  * Hard spheres refuse the affine mode. This is right: the hard-sphere adiabat needs the collisional pressure
    (dT/T = −(2/d) Z dV/V), which an affine jump does not give.
* **The TRT antisymmetric factor (the author's derivation)** [useful] (`lbm_remap_checks_PBT.out`, part P). With the
  engine's km, the steady TRT channel stays on its own steady state to 1.6e-13…5.9e-12 after refinement (diffusive and
  acoustic), coarsening and a new dt, at τ = 0.8 and 1.0. Dupuis–Chopard's single factor (km = kp) gives 8.8e-5…2.0e-3,
  and no rescale gives 9.3e-4…5.0e-3.

  The derivation stands: every term of the momentum balance, the viscous one included, scales in lattice units as
  dt²/dx. The existing Poiseuille test does discriminate it.
* **BGK across a remap** [neutral]: 0.4–1.7 % off the target grid's steady state. This is BGK's τ-dependent wall slip,
  not the transfer: (16Λ − 3)/(3H²) of the peak changes by 6.1e-3 against 6.9e-3 measured for the diffusive refinement
  at τ = 0.8.
* **Taylor–Green** [neutral]: the transfer adds nothing beyond the coarse history. Its km variants agree within 1.5e-5
  of the amplitude, because the vortex has no significant odd part.
* **The dye** [useful]: its second moment is carried exactly through a refinement (P12).
* **The hole's mass as a change of units** [useful] (`kerr_checks.out`, part M). The geometric time is equal to all
  digits, and the positions agree to 5.8e-15 with a world that never changed, run for half the seconds. Proper times and
  clocks in seconds are continuous, as are rates, E and ZAMO speeds. r_km doubles by design, and no running check fails.
  The binary's mass (h ∝ m, f ∝ 1/m) is covered by the authors' test.
* **Kerr throws** [neutral]: `_zamo_of_throw` is BPT (3.9)–(3.10). The authors' round-trip test is a genuine check,
  because the forward route goes through the engine's geodesic right-hand side.
* **Restore** [useful]: bit-identical in the whole state for p03 (here), and for p01 and p04 (their tests compare the
  full `geo.state_dict()` and the populations).
* **The authors' tests** pass in this environment (26 + 31; the GPU test was skipped).
