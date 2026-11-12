# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Two-dimensional incompressible flow by the lattice Boltzmann method (plan P8; playground P15.7).

The law is the incompressible Navier-Stokes equation (with a uniform body force g)

    du/dt + (u . grad) u = -grad p / rho + nu lap u + g,      div u = 0,

with a passive scalar C ("dye") carried by the flow, dC/dt + u . grad C = D lap C. The lattice Boltzmann equation
solves the weakly compressible (isothermal) equations instead; their difference from the incompressible ones is the
compressibility error O(Ma^2), Ma = |u| / c_s, c_s = (dx/dt) / sqrt(3), plus the discretisation error O(dx^2) in the
diffusive scaling (dt proportional to dx^2 at fixed tau). Both are measured in every run (``numbers``, ``checks``: the
largest Mach number, the density range ~ Ma^2) and in the tests (second order: Poiseuille, Couette's start-up and the
Taylor-Green decay; the benchmarks below).

* **Lattice.** D2Q9 (Qian, d'Humieres & Lallemand 1992): velocities e_i = (0,0), (1,0), (0,1), (-1,0), (0,-1), (1,1),
  (-1,1), (-1,-1), (1,-1), weights 4/9, 1/9 (x4), 1/36 (x4), c_s^2 = 1/3 (lattice units dx = dt = 1). Equilibrium
  f_i^eq = w_i rho (1 + 3 e.u + 9/2 (e.u)^2 - 3/2 u^2). Node (i, j) sits at ((i + 1/2) dx, (j + 1/2) dx) in the domain
  [0, Lx] x [0, Ly]; arrays are indexed [i, j] (axis 0 = x). The stored state is the post-collision populations.
* **Collision: TRT** (two relaxation times; Ginzburg, Verhaeghe & d'Humieres 2008) by default: the symmetric part
  f_i^+ = (f_i + f_-i)/2 relaxes with omega+ = 1/tau+, tau+ = 3 nu + 1/2 (the viscosity), the antisymmetric part with
  omega- from the "magic" parameter Lambda = (tau+ - 1/2)(tau- - 1/2). With half-way bounce-back the steady
  Poiseuille solution is the exact parabola plus a uniform slip (16 Lambda - 3) g dx^2 / (24 nu) (found here to
  round-off for TRT at six Lambda and BGK at four tau, tests; the published Heff^2 - H^2 = (16/3) Lambda - 1 of
  Ginzburg, Verhaeghe & d'Humieres 2008b, Table 4): zero at Lambda = 3/16 (default), a function
  of Lambda alone, so for TRT independent of the viscosity; BGK (one relaxation time, tau- = tau+, Lambda =
  (tau - 1/2)^2) is the option, whose wall moves with the viscosity. The rest population is set last to the node's
  density minus the other eight (the TRT value up to one rounding): the collision then conserves mass with an
  unbiased rounding (the formula's own rounding drifted by -8e-17 per node and step: 1.2e-13 of the mass in 1500 steps).
* **Forcing:** Guo, Zheng & Shi (2002): u = (sum e f + F/2) / rho and the source
  F_i = (1 - omega-/2) 3 w_i e_i.F + (1 - omega+/2) w_i [9 (e_i.u)(e_i.F) - 3 u.F] (Guo's term split into its
  antisymmetric and symmetric parts, each with its own rate; BGK: Guo's term exactly). A uniform force density
  F = rho0 g (gravity, or a pressure gradient G = -rho0 g). Every collision adds exactly F to each fluid node's
  momentum and nothing to its mass (to round-off: the momentum balance checks it). Along a non-periodic axis a fluid
  at rest in the force has the hydrostatic density c_s^2 grad rho = rho0 g (linear, the force density being uniform):
  the flow starts in it, and a change of the force adds the change of that density and the half-step momentum
  (F_new - F_old)/2 of the stored state at once (an incompressible fluid's pressure follows the force instantly; the
  scheme would set it by sound waves that overshoot; booked "body_force_change"); the hydrostatic part is zero at the
  outlet of an axis with one outlet, else in the middle (review B7 L6).
* **Walls: half-way bounce-back** f_i(x_f, t+1) = f*_-i(x_f, t): the wall lies half-way between a fluid node and a
  solid one, second order for walls along the lattice; curved walls are staircases (first order in the geometry: the
  cylinder's drag 1 % high at 20 cells per diameter), or, per obstacle, **interpolated** (Bouzidi, Firdaouss &
  Lallemand 2001, linear: q is the exact fraction of the link in the fluid; links with q < 1/2 whose next node is not
  fluid fall back to half-way). Interpolated bounce-back does not conserve mass (-5e-5 of the mass in 1500 steps of a
  test cavity): the exchange is booked per link (``balance``). **Moving walls** (Ladd 1994): f_i = f*_-i + 6 w_i
  rho0 e_i.u_w, u_w the wall velocity at the link's wall point: a side wall moving along itself (a driven lid), or an
  obstacle's surface velocity (a uniform velocity and/or a rotation about its centre) on a fixed geometry - the body
  itself does not move.
* **Velocity inlet** (a side; uniform, parabolic or any profile): link-wise, the moving-wall rule with the inlet
  velocity at the link's wall point (a velocity bounce-back; its mass flux per step is exactly rho0 times the profile
  sampled at the links' wall points). It leaves a transverse velocity in its column that grows with the grid Reynolds
  number (a plain channel started from the exact parabola: max |u_y| / U = 0.0040 at u dx / nu = 1, 0.038 at 10;
  0.0020 twenty columns in; tests), and the stability edge of open domains is the inlet's (review B7 L12: a plain
  channel with TRT blows up from about 12, a periodic channel driven by a force is stable at 60; see
  ``RE_CELL_MAX_OPEN``). A ramp (``Inlet(ramp=...)``) is per side: it starts when that side's velocity is set and
  blends from the velocity the side had (zero after a wall) to the new one, link by link c1 (1 - s) + val s; an edit
  that keeps the velocity (the dye, the ramp time) does not restart it (review B7 L1). **Pressure outlet** (a side):
  anti-bounce-back (Ginzburg 2005; Krueger et al. 2017) f_i = -f*_-i + 2 w_i rho_out [1 + 9/2 (e_i.u_w)^2 - 3/2 u_w^2]
  (Ginzburg et al. 2008a, Eq. 6.2 with Table 9: "PAB", without its optional correction term; there the non-linear
  term takes rho0), u_w extrapolated to the wall point along the link, u_w = u(x_f) + (u(x_f) - u(x_f + e_i)) / 2;
  rho_out is the outlet's pressure at the middle of its side plus, with a body force along the side, the hydrostatic
  part g_s (s - s_mid) / c_s^2 (a uniform rho_out drove a fluid at rest into a circulation of 0.13 m/s: review B7
  L6). Chosen over Zou-He (node-based): link-wise rules keep every boundary half-way, so inlet, outlet, walls and
  obstacles meet at corners without special cases.
  **Periodic** sides in pairs. Where two sides meet, a diagonal link from outside both takes the rule of the side in
  the order wall > inlet > outlet (left/right before bottom/top among equals).
* **Sound.** The scheme carries sound at c_s; the inlet (a closed end for sound) and the outlet (an open end) reflect
  it, so a channel rings at the period 4 L / c_s (2.93 s in the cylinder benchmark at Ma = 0.1; ``acoustic_period``,
  checked against the measured ringing to 5e-4), with an amplitude O(Ma^2) that the viscosity damps only as
  nu (pi / 2L)^2: after a 3-s smooth start +-1.5 % of the drag at Ma = 0.1 and +-0.4 % at 0.05; after an impulsive
  start far more (+-13 % of the drag between 8 and 12 s at Ma 0.067, review B7 L4). Forces averaged over whole periods
  are unaffected (benchmarks; ``record_forces``); pressure fields show the wave. ``Inlet(ramp=...)`` starts the inflow
  smoothly (sin^2) and excites less of it.
* **Dye** (passive scalar): D2Q5 (the first five D2Q9 velocities; w = 1/3, 1/6, c_s^2 = 1/3) advection-diffusion
  TRT, g_i^eq = w_i C (1 + 3 e_i.u), diffusivity D = (tau_g- - 1/2)/3, Lambda_g = 1/4. The linear equilibrium adds a
  numerical diffusion along the flow: D_ab = D delta_ab - (tau_g- - 1/2) u_a u_b (lattice units; measured to 1e-6,
  tests), i.e. a relative error 3 u_lat^2 (0.0075 at u_lat = 0.05) along the flow. Walls and obstacles reflect the dye
  (zero flux), an inlet sets its concentration (anti-bounce-back), an outlet lets it out (the outside node taken equal
  to the boundary node), sources hold a concentration in a region (the dye they add is booked). The diffusivity has a
  floor (``DYE_TAU_MIN``: tau_g- >= 0.505); the run reports the diffusivity used and the cell Peclet number.
* **Time.** t = t0 + steps dt (``t0``: a flow started at a time, e.g. from a scene file; review B7 L2); the inlet
  ramps count steps.
* **Geometry at any moment.** Obstacles (disks, rectangles, polygons, masks) are added, changed and removed between
  steps (all or nothing: a refused change leaves the flow as it was). A node that becomes solid loses its populations:
  their mass, momentum and dye are booked ("geometry"); with ``displaced="spread"`` the mass is instead returned to the
  remaining fluid by scaling its populations uniformly (total mass conserved to round-off; the pressure level rises). A
  node that becomes fluid starts at equilibrium with the mean density of its fluid neighbours (the domain's mean where
  it has none) and the surface velocity of the moving body that left it.
* **Laws at any moment** (review 2026-11-04 UX-ui U12). ``set_viscosity`` (tau changes, the time step stays; the
  populations are kept: mass and momentum do not jump, the viscous stress in the non-equilibrium part adapts within a
  few steps), ``set_density`` (the lattice state is kept: only the physical scale of mass, momentum, pressure and force
  changes), ``set_collision`` (TRT or BGK: the same equilibrium and viscosity, the odd moments' rate changes),
  ``enable_dye`` / ``disable_dye`` (off: the dye's amount booked as removed, "dye_off") / ``set_dye_diffusivity``; each
  restarts the force record. ``gravity_limit`` gives the largest body force the rest state carries (the refusal's edge),
  ``memory_estimate`` the peak memory of a grid before it is built (measured per node).
* **The grid, the domain and the time step at any moment** (plan P16.1): ``remap`` continues the flow on another
  spacing, a larger or smaller (or shifted) domain, or another time step (the largest expected speed): the pre-collision
  populations of the next step are split into equilibrium and non-equilibrium parts, the pressure, the velocity and the
  non-equilibrium part interpolated (four-point cubic where the stencil is fluid) and the latter rescaled with the
  relaxation times and the time step (Dupuis & Chopard 2003, the grid-refinement transfer); a new part of the domain
  starts at rest or with the inflow; a domain that would cut an obstacle or a dye source is refused; the change of the
  totals is booked ("remap"), so the balances close by construction across a remap and cannot check the transfer
  (review LB1-physics P7): the tests do — Poiseuille's parabola is transferred and continued exactly, a Taylor-Green
  vortex at the scheme's own accuracy, the dye's second moment carried through a refinement. ``adopt`` continues another
  flow's fluid on the same grid and time step with this flow's own geometry and laws (a new world that keeps the flow:
  ``remap`` the old one first).
* **Measurements.** Density, pressure p - p_ref = c_s^2 (rho - rho0) (dx/dt)^2 rho_phys, velocity, vorticity (centred
  differences; one-sided next to solids), the dye. Forces and torques on each obstacle by momentum exchange (Ladd
  1994; per link e_i (f_in + f_out), also on interpolated links), of the last step or averaged since
  ``reset_force_mean``, and their drag and lift coefficients; the force record (``record_forces``): the means over
  consecutive blocks of whole steps, aligned to the step count however ``advance`` is called and restarted when the
  flow's set-up changes, to average over whole sound periods (``acoustic_period``) or to sample a periodic flow. The
  **balance** of mass, momentum and dye: the totals against their start values plus everything booked at the
  boundaries (per link, accumulated every step: inlets,
  outlets, walls, obstacles), by the body force and by geometry changes; the residual is round-off (4e-16 of the mass
  in 1500 steps, 5e-14 of the momentum in 15 000: ``checks`` allows 2 ulps per step, at least 1e-12 — not a proven
  worst case [error in earlier: "a worst-case bound"]: the per-link records, the dye sources' and the body force's
  books are Kahan-compensated sums (a plain running sum's rounding grew like n^2 and failed correct runs after 10^4
  steps, review LB1-physics P1), so what remains is the nodes' unbiased rounding; it does not see a leak below about
  2 eps of the total per step, review B7 L18; the tests use a tighter bound where no accumulator carries the
  quantity). Mach and Reynolds numbers, tau, the grid Reynolds number u dx / nu (a stability limit, not a measure of
  accuracy), the density range (compressibility).
* **Benchmarks (tests; data ``GHIA_*``, ``DFG_*``).** The driven cavity at Re = 100 against Ghia, Ghia & Shin (1982):
  0.005 (u) and 0.008 (v) of the lid speed on 64^2 to 256^2 alike (asserted below 0.008 and 0.012); the DFG cylinder
  (Schaefer & Turek 1996) 2D-1 with interpolated walls at 40 cells per diameter: cD 5.5790, cL 0.010752 (bounds
  5.5700-5.5900, 0.0104-0.0110; 20 cells: 5.5893, 0.010483; staircase at 20: 5.6367, 0.011252, outside); 2D-2 at 20
  cells: St 0.2990 (0.2950-0.3050) inside, but cLmax 0.979 (0.980 at 40 cells; bounds 0.99-1.01) and cDmax 3.330
  (3.248 at 40; bounds 3.22-3.24) outside — the lift's mean offset -0.018 is the same at Ma 0.1 and 0.05, so not the
  scheme's sound (review B7 L9; cause open). Accuracy away from them: the cavity at Re 1000 on 64^2 (grid Reynolds
  number 15.6, accepted) is 0.017 of the lid speed off Ghia's Re 1000 columns, on 128^2 0.011 (review B7 L13).
* **Stability** (refused with the reason): Ma of the declared largest velocity (and of every wall, inlet and surface
  speed) <= ``MACH_MAX`` = 0.3; tau+ - 1/2 >= ``TAU_MIN_EXCESS``; the grid Reynolds number u_max dx / nu <=
  ``RE_CELL_MAX`` (25, closed or periodic domains) or ``RE_CELL_MAX_OPEN`` (10, with an inlet or an outlet), both
  measured stability edges (see the constants), not limits of accuracy; the rest state the outlets' pressures and the
  body force's hydrostatic part impose may deviate from rho0 by at most ``RHO_DEV_MAX`` (reviews B7 L6, L7).
  ``advance`` checks every chunk of up to 64 steps (a population non-finite or beyond ``F_GUARD``): on a blow-up it restores the state of the call and raises ``Unstable`` with the numbers of the last
  healthy state.

Precision fp64 only (fp32 is not offered: the deviations from rest equilibrium are O(Ma^2) ~ 1e-3 of the populations,
so fp32 keeps ~4 digits of them). The heavy part (the fused stream-collide step) runs on the CPU (NumPy, vectorised,
the collision on ``LBM_THREADS`` threads by row blocks) or on GPU 0 (a CuPy kernel, ``lfphys.core.backend`` kernel
"fluids.lbm"): the kernel performs the same floating-point operations in the same order without fused multiply-adds
(--fmad=false), so the GPU state equals the CPU state bit for bit (tests), and a threaded CPU step equals a single
thread's. Reductions for diagnostics (totals) differ between devices by round-off only. Measured speeds: ``RATES``.

Units: SI (2-D quantities per metre of depth: forces N/m, masses kg/m); ``Units`` converts. Fluid data with their
sources: ``fluid_properties`` (water: IAPWS values from the NIST WebBook; air: the U.S. Standard Atmosphere 1976).
"""

from __future__ import annotations

import copy
import math
import os
import time

import numpy as np

from .. import backend

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": "Несжимаемая жидкость в 2-D: решёточный метод Больцмана (D2Q9)",
    "statement": "Уравнения Навье–Стокса несжимаемой жидкости (с однородной объёмной силой) и перенос пассивной "
                 "примеси решаются решёточным уравнением Больцмана D2Q9 (столкновения TRT с «магическим» параметром "
                 "3/16 или BGK, сила по Гуо); стенки — отражение на полпути (подвижные — по Ладду), криволинейные "
                 "препятствия — ступеньками или с интерполяцией Бузиди; вход со скоростью, выход с давлением "
                 "(анти-отражение), периодические стороны; препятствия добавляются и убираются в любой момент с "
                 "учётом массы; вязкость, плотность, оператор столкновений и краска меняются в текущий момент; сетка, область и шаг "
                 "по времени тоже: популяции переносятся на новую сетку (неравновесная часть — с пересчётом по "
                 "временам релаксации, как при измельчении сеток у Дюпюи и Шопара), новая часть области — в покое "
                 "или с входящим потоком; силы на препятствия обменом импульса (сопротивление и подъёмная сила), баланс массы, "
                 "импульса и краски с потоками через границы.",
    "validity": "течение несжимаемой жидкости: ошибка сжимаемости O(Ma²) (Ma ≤ 0.3, проверяется; звуковые волны "
                "схемы отражаются входом и выходом, амплитуда O(Ma²)), второй порядок по сетке в диффузионном "
                "масштабе; ламинарные течения; пределы устойчивости по числу Рейнольдса ячейки u·dx/ν: ≤ 25, с входом "
                "или выходом ≤ 10 (измерено; это не мера точности: каверна Re 1000 на 64² при 15,6 отличается от Ghia "
                "на 0,017 скорости крышки); плотность покоя от давления выхода и силы — в пределах ±0,045; 2-D, однородная плотность, однородная объёмная сила; препятствия "
                "неподвижны (их поверхность может двигаться); криволинейные стенки — ступеньками (1-й порядок по "
                "геометрии) или с интерполяцией; примесь пассивна, её диффузия не меньше порога схемы, вдоль потока "
                "добавлена численная диффузия −(τ−½)u²",
    "basis": ["Qian, d'Humières, Lallemand, Europhys. Lett. 17, 479 (1992) — D2Q9",
              "Ginzburg, Verhaeghe, d'Humières, Commun. Comput. Phys. 3, 427 и 519 (2008) — TRT, магический "
              "параметр, анти-отражение для давления",
              "Guo, Zheng, Shi, Phys. Rev. E 65, 046308 (2002) — объёмная сила",
              "Ladd, J. Fluid Mech. 271, 285 (1994) — подвижные стенки, обмен импульсом",
              "Bouzidi, Firdaouss, Lallemand, Phys. Fluids 13, 3452 (2001) — интерполяция отражения",
              "Krüger et al., The Lattice Boltzmann Method (Springer 2017)",
              "Schäfer & Turek (1996), Ghia, Ghia & Shin (1982) — эталонные задачи (тесты)",
              "Dupuis & Chopard, Phys. Rev. E 67, 066707 (2003); Filippova & Hänel, J. Comput. Phys. 147, 219 (1998); "
              "Lagrava, диссертация, Женевский университет (2012), ур. (4.1), (4.10), (4.11), правая часть (4.13), "
              "(4.14)–(4.15) (в (4.12) и в средней части (4.13) отношение перевёрнуто — опечатка) — перенос неравновесной "
              "части между сетками (смена сетки, области и шага)"],
    "conflicts": [],
}

KERNEL = "fluids.lbm"
FORMAT = "lfphys.lbm2d/2"  # /2: the time origin, per-side inlet ramps, the force record (/1 still read)
# the per-link records (``_L``): the cumulative exchanges of mass, momentum (v + f, summed with e_i into the momentum)
# and dye with their compensation terms, and the last step's. The cumulative ones are summed with Kahan's compensation
# (the true sum is acc - cmp to the rounding of acc; review LB1-physics P1, STATUS V41 (ac)): a plain running sum grows
# by the gross exchange every step (~0.2 per wall link), so its rounding per step grows with its size and the books'
# error like n^2 (a 4 x 16 channel failed the running check after 9537 steps); compensated, it stays at the rounding of
# the final sum (Higham, Accuracy and Stability of Numerical Algorithms, 2nd ed., section 4.3: |error| <= 2u sum |x_i|
# + O(n u^2) sum |x_i|). Older states without "cmp_*" restart them at zero.
LINK_ACC = ("acc_m", "acc_p", "last_m", "last_p", "acc_d", "cmp_m", "cmp_p", "cmp_d")

# --- the lattice ------------------------------------------------------------------------------------------------------
EX = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1])
EY = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1])
OPP = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])
W = (4 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 36, 1 / 36, 1 / 36, 1 / 36)
WA = np.array(W)
PAIRS = ((1, 3), (2, 4), (5, 7), (6, 8))  # (i, -i): i's velocity . u is ux, uy, ux + uy, uy - ux
CS2 = 1 / 3
CS = math.sqrt(CS2)
WG = (1 / 3, 1 / 6, 1 / 6, 1 / 6, 1 / 6)  # D2Q5 (the dye): directions 0..4 of D2Q9
OPP5 = np.array([0, 3, 4, 1, 2])

# --- stability and accuracy limits (refusals) -------------------------------------------------------------------------
MACH_MAX = 0.3          # declared largest velocity / c_s: the compressibility error O(Ma^2) <~ 0.1 at the limit
# imposed densities (review B7, L6 and L7): the running check allows |rho - rho0| <= MACH_MAX^2; the rest state an outlet's
# pressure and a body force's hydrostatic part impose may deviate from rho0 by at most half of it: a step of the
# outlet's pressure is reflected by closed ends with twice its height (measured at the limit: 0.089), and the flow's own
# O(Ma^2) needs the rest
RHO_DEV_MAX = MACH_MAX**2 / 2
TAU_MIN_EXCESS = 1e-3   # tau+ - 1/2 (lattice viscosity >= 3.3e-4)
# the grid Reynolds number u_max dx / nu (measured 2026-11-04, TRT 3/16, Ma 0.1, GPU runs of 6-20 s): a closed
# cavity (no inlet or outlet) was stable at 25 (Re 3200 on 128^2) and blew up at 31; with an inlet and an outlet
# (the cylinder channel of Schaefer & Turek, D = 20 and 40 cells) stable at 10 and 11, unstable from 12 on (the growth
# starts at the velocity inlet; in these cylinder runs BGK, Lambda = 1/4 or 1/12, a local density in the inlet rule, a
# 3-s ramp or Ma 0.05 did not move the edge); a plate blocking half the channel blew up at 8 of the declared speed (its
# jets run 2-3 times faster: the run's own grid Reynolds number is reported by ``numbers`` and ``checks``). The edge
# is the inlet's (review B7 L12, the reviewer's runs r07, r09, reproduced): a plain channel (no obstacle) with the
# velocity inlet and the outlet runs 1e5 steps at 10 and 11 but blows up at 12 with TRT (after 8320 steps; a uniform
# inlet after 1408), while BGK survives 12 for 3e4 steps and fails at 20; the same channel driven by a body force with
# periodic ends is stable at 20 and 60. The inlet's column keeps a transverse velocity growing with this number (0.4 %
# of U at 1, 3.8 % at 10). These are stability edges, not limits of accuracy (review B7 L13). The remedy, a regularised
# or characteristic inlet, is open (STATUS V41 m).
RE_CELL_MAX = 25.0      # closed or periodic domains
RE_CELL_MAX_OPEN = 10.0  # with an inlet or an outlet
F_GUARD = 1.5           # |f*| above this (healthy populations stay within about -0.05..0.6) is a blow-up
DYE_TAU_MIN = 0.505     # the dye's tau_g- floor: D_lat >= 0.005/3
DYE_LAMBDA = 0.25
MAGIC = 3 / 16

# link types (fluid) and dye link types
T_BB, T_IN, T_BZN, T_BZF, T_ABB = 1, 2, 3, 4, 5
D_BB, D_IN, D_OUT = 1, 2, 3
SIDES = ("left", "right", "bottom", "top")
SIDE_CODE = {"left": -1, "right": -2, "bottom": -3, "top": -4}
SIDE_OF_CODE = {v: k for k, v in SIDE_CODE.items()}
PRIORITY = {"wall": 0, "inlet": 1, "outlet": 2, "periodic": 3}


# --- fluids: cited data ------------------------------------------------------------------------------------------------
# Water at 0.101325 MPa: NIST Chemistry WebBook, SRD 69, "Isobaric Properties for Water" at 0.101325 MPa, fetched
# 2026-11-04, computed there from IAPWS-95 (Wagner & Pruss, J. Phys. Chem. Ref. Data 31, 387 (2002); IAPWS R6-95(2016))
# for the density and the IAPWS 2008 viscosity formulation (Huber et al., J. Phys. Chem. Ref. Data 38, 101 (2009));
# the WebBook states the uncertainty of the density "0.0001% at 1 atm in the liquid phase"; IAPWS R12-08 states the
# viscosity's "uncertainty of 0.17 % at 293.15 K" (the releases themselves tabulate neither value at 20 C).
# (T in deg C, density kg/m^3, dynamic viscosity Pa s), 7 digits as printed.
WATER_1ATM = (
    (0.01, 999.8438, 0.001791132),
    (1, 999.9018, 0.001731021),
    (2, 999.9430, 0.001673515),
    (3, 999.9672, 0.001619009),
    (4, 999.9749, 0.001567292),
    (5, 999.9666, 0.001518173),
    (6, 999.9429, 0.001471477),
    (7, 999.9043, 0.001427043),
    (8, 999.8510, 0.001384724),
    (9, 999.7836, 0.001344385),
    (10, 999.7025, 0.001305900),
    (11, 999.6079, 0.001269155),
    (12, 999.5003, 0.001234043),
    (13, 999.3801, 0.001200468),
    (14, 999.2474, 0.001168337),
    (15, 999.1026, 0.001137568),
    (16, 998.9461, 0.001108081),
    (17, 998.7780, 0.001079806),
    (18, 998.5986, 0.001052674),
    (19, 998.4083, 0.001026624),
    (20, 998.2072, 0.001001596),
    (21, 997.9955, 0.0009775372),
    (22, 997.7735, 0.0009543962),
    (23, 997.5414, 0.0009321258),
    (24, 997.2994, 0.0009106817),
    (25, 997.0476, 0.0008900225),
    (26, 996.7864, 0.0008701093),
    (27, 996.5158, 0.0008509058),
    (28, 996.2360, 0.0008323778),
    (29, 995.9471, 0.0008144932),
    (30, 995.6495, 0.0007972218),
    (31, 995.3431, 0.0007805353),
    (32, 995.0281, 0.0007644068),
    (33, 994.7048, 0.0007488114),
    (34, 994.3731, 0.0007337251),
    (35, 994.0333, 0.0007191256),
    (36, 993.6855, 0.0007049918),
    (37, 993.3298, 0.0006913036),
    (38, 992.9663, 0.0006780421),
    (39, 992.5951, 0.0006651895),
    (40, 992.2164, 0.0006527287))
WATER_SOURCE = ("NIST Chemistry WebBook SRD 69 (изобара 0.101325 МПа, загружено 2026-11-04): IAPWS-95 (Wagner & Pruß 2002) "
                "и вязкость IAPWS 2008 (Huber et al. 2009)")
# Air: U.S. Standard Atmosphere 1976 (NOAA/NASA/USAF, NASA-TM-X-74335, NTRS 19770009539): ideal gas
# rho = P M0 / (R* T) with M0 = 28.9644 kg/kmol (p. 9), R* = 8.31432e3 N m/(kmol K) (p. 3; table 2 on p. 2 prints the
# exponent wrongly), P0 = 1.013250e5 Pa (table 2); dynamic viscosity eq. (51), p. 19: mu = beta T^(3/2) / (T + S),
# beta = 1.458e-6 kg/(s m K^(1/2)), S = 110.4 K ("basically from kinetic theory, but with constants derived from
# experiment"; table 2 prints S = 110 K, the text 110.4 K). Checked against the standard's table I (p. 52): sea level
# 288.150 K, 1.01325e3 mb, 1.2250 kg/m^3.
AIR_M0, AIR_RSTAR, AIR_BETA, AIR_S, P_ATM = 28.9644, 8.31432e3, 1.458e-6, 110.4, 1.013250e5
AIR_SOURCE = ("U.S. Standard Atmosphere 1976 (NASA-TM-X-74335): идеальный газ с M0 = 28.9644 кг/кмоль, R* = 8.31432·10³ "
              "Дж/(кмоль·К) (с. 3, 9); вязкость по формуле (51) с β = 1.458·10⁻⁶, S = 110.4 К (с. 19)")


def fluid_properties(name: str, T_C: float = 20.0, p: float = P_ATM) -> dict:
    """Density (kg/m^3), dynamic viscosity mu (Pa s) and kinematic viscosity nu (m^2/s) of "water" (at 1 atm, 0.01-40 C:
    the WebBook's IAPWS values at whole degrees, density interpolated linearly and log(mu) linearly in T; on every
    second row the interpolation errs by at most 3.4e-4 in mu and 8.5e-6 in rho, so on the whole-degree table by about
    a quarter of that: ~1e-4 and ~2e-6, tests) or "air" (dry air, any T from -50 to 100 C and pressure ``p`` in Pa:
    the U.S. Standard Atmosphere 1976 formulas), with the source."""
    if name == "water":
        if p != P_ATM:
            raise ValueError("вода: только при 1 атм (101325 Па)")
        tab = np.array(WATER_1ATM)
        if not (tab[0, 0] <= T_C <= tab[-1, 0]):
            raise ValueError(f"вода: таблица от {tab[0, 0]} до {tab[-1, 0]} °C")
        at = np.flatnonzero(tab[:, 0] == T_C)
        if len(at):  # a tabulated temperature: the value as printed
            rho, mu = float(tab[at[0], 1]), float(tab[at[0], 2])
        else:
            rho = float(np.interp(T_C, tab[:, 0], tab[:, 1]))
            mu = float(np.exp(np.interp(T_C, tab[:, 0], np.log(tab[:, 2]))))
        src = WATER_SOURCE
    elif name == "air":
        if not (-50.0 <= T_C <= 100.0) or not p > 0:
            raise ValueError("воздух: от −50 до 100 °C, давление > 0")
        T = T_C + 273.15
        rho = p * AIR_M0 / (AIR_RSTAR * T)
        mu = AIR_BETA * T**1.5 / (T + AIR_S)
        src = AIR_SOURCE
    else:
        raise ValueError(f"жидкость {name!r}: 'water' или 'air'")
    return {"name": name, "T_C": float(T_C), "p": float(p), "rho": rho, "mu": mu, "nu": mu / rho, "source": src}


FLUIDS = {"water_20C": fluid_properties("water", 20.0), "air_20C": fluid_properties("air", 20.0)}

# --- reference data of the benchmarks (the tests and the playground's comparisons; sources/verification_2026-11-04_p8_lbm.md)
# Ghia, Ghia & Shin, J. Comput. Phys. 48, 387 (1982), the driven cavity: Table I (u on the vertical centre line) and Table
# II (v on the horizontal one), the Re = 100 columns, from two transcriptions that agree (the paper not obtained), in units
# of the lid speed and the cavity's side
GHIA_Y = (1.0, .9766, .9688, .9609, .9531, .8516, .7344, .6172, .5, .4531, .2813, .1719, .1016, .0703, .0625, .0547, 0.0)
GHIA_U100 = (1.0, .84123, .78871, .73722, .68717, .23151, .00332, -.13641, -.20581, -.21090, -.15662, -.10150, -.06434,
             -.04775, -.04192, -.03717, 0.0)
GHIA_X = (1.0, .9688, .9609, .9531, .9453, .9063, .8594, .8047, .5, .2344, .2266, .1563, .0938, .0781, .0703, .0625, 0.0)
GHIA_V100 = (0.0, -.05906, -.07391, -.08864, -.10313, -.16914, -.22445, -.24533, .05454, .17527, .17507, .16077, .12317,
             .10890, .10091, .09233, 0.0)
# Schaefer & Turek (1996), "Benchmark computations of laminar flow around a cylinder": channel 2.2 x 0.41 m, cylinder
# D = 0.1 m at (0.2, 0.2), nu = 1e-3 m^2/s, rho = 1 kg/m^3, inflow 4 Um y (H - y) / H^2, U = 2 Um / 3; the lower and upper
# bounds of Table 3 (2D-1, Um = 0.3 m/s, Re 20: cD, cL) and Table 4 (2D-2, Um = 1.5 m/s, Re 100: "maximum drag
# coefficient cDmax, maximum lift coefficient cLmax, Strouhal number St")
DFG_GEOMETRY = {"Lx": 2.2, "H": 0.41, "center": (0.2, 0.2), "D": 0.1, "nu": 1e-3, "rho": 1.0}
DFG_2D1 = {"Um": 0.3, "cD": (5.5700, 5.5900), "cL": (0.0104, 0.0110)}
DFG_2D2 = {"Um": 1.5, "cDmax": (3.2200, 3.2400), "cLmax": (0.9900, 1.0100), "St": (0.2950, 0.3050)}


class Unstable(RuntimeError):
    """A step produced a non-finite value; the state was restored to the start of the call."""


# --- units --------------------------------------------------------------------------------------------------------------
class Units:
    """Lattice <-> physical units: ``dx`` (m), ``dt`` (s) and ``rho`` (kg/m^3, the physical density of lattice density
    1). Velocities scale with dx/dt, viscosities and diffusivities with dx^2/dt, pressures with rho (dx/dt)^2,
    forces per unit depth with rho dx^3/dt^2 (2-D: per metre of depth)."""

    def __init__(self, dx: float, dt: float, rho: float = 1000.0):
        if not (dx > 0 and dt > 0 and rho > 0):
            raise ValueError("единицы: dx, dt и плотность должны быть положительными")
        self.dx, self.dt, self.rho = float(dx), float(dt), float(rho)

    @classmethod
    def from_flow(cls, dx: float, nu: float, u_max: float, mach: float = 0.1, rho: float = 1000.0,
                  tau_max: float | None = 1.0) -> "Units":
        """dt from the Mach number of the largest expected velocity u_max: dt = Ma c_s dx / u_max; if that makes
        tau+ = 3 nu dt/dx^2 + 1/2 larger than ``tau_max``, dt is lowered to tau_max (Ma then smaller)."""
        if not (u_max > 0 and nu > 0 and mach > 0):
            raise ValueError("единицы: нужны u_max > 0, ν > 0, Ma > 0")
        dt = mach * CS * dx / u_max
        if tau_max is not None and 3 * nu * dt / dx**2 + 0.5 > tau_max:
            dt = (tau_max - 0.5) * dx**2 / (3 * nu)
        return cls(dx, dt, rho)

    @property
    def c(self) -> float:
        return self.dx / self.dt

    def velocity(self, u_lat):
        return np.asarray(u_lat) * self.c

    def to_velocity(self, u):
        return np.asarray(u, float) / self.c

    def viscosity(self, nu: float) -> float:
        """Lattice viscosity of nu (m^2/s)."""
        return nu * self.dt / self.dx**2

    def pressure(self, rho_lat):
        return CS2 * (np.asarray(rho_lat) - 1.0) * self.rho * self.c**2

    def density_of_pressure(self, p):
        return 1.0 + np.asarray(p, float) / (CS2 * self.rho * self.c**2)

    def acceleration(self, a) -> np.ndarray:
        return np.asarray(a, float) * self.dt**2 / self.dx

    @property
    def force(self) -> float:
        """Newtons per metre of depth per lattice momentum per step."""
        return self.rho * self.dx**3 / self.dt**2

    @property
    def mass(self) -> float:
        return self.rho * self.dx**2

    @property
    def momentum(self) -> float:
        return self.rho * self.dx**2 * self.c

    def params(self) -> dict:
        return {"dx": self.dx, "dt": self.dt, "rho": self.rho}


# --- shapes -------------------------------------------------------------------------------------------------------------
class Shape:
    """A solid region in physical coordinates (m). ``contains`` decides which nodes are solid; ``hit`` gives the
    fraction t in (0, 1] of a segment P0 -> P0 + D (P0 outside) at which it enters the shape (inf: none), for the
    interpolated walls."""
    TYPE = ""

    def contains(self, X, Y) -> np.ndarray:
        raise NotImplementedError

    def hit(self, X0, Y0, DX, DY) -> np.ndarray:
        return np.full(np.shape(X0), np.inf)

    def center(self) -> tuple:
        raise NotImplementedError

    def span(self, direction=(1.0, 0.0)) -> float:
        """The width across ``direction`` (the reference length of drag and lift coefficients)."""
        raise NotImplementedError

    def params(self) -> dict:
        raise NotImplementedError

    @property
    def analytic(self) -> bool:
        return True

    def shifted(self, sx: float, sy: float) -> "Shape":
        """The same shape moved by (sx, sy) m (the domain's origin moved: ``Flow2D.remap``)."""
        raise NotImplementedError


class Disk(Shape):
    TYPE = "disk"

    def __init__(self, center, radius: float):
        self.c = (float(center[0]), float(center[1]))
        self.r = float(radius)
        if not self.r > 0:
            raise ValueError("диск: радиус должен быть положительным")

    def contains(self, X, Y):
        return (X - self.c[0]) ** 2 + (Y - self.c[1]) ** 2 <= self.r**2

    def hit(self, X0, Y0, DX, DY):
        px, py = X0 - self.c[0], Y0 - self.c[1]
        a = DX * DX + DY * DY
        b = 2 * (px * DX + py * DY)
        c0 = px * px + py * py - self.r**2
        disc = b * b - 4 * a * c0
        with np.errstate(invalid="ignore"):
            t = (-b - np.sqrt(disc)) / (2 * a)
        return np.where((disc >= 0) & (t > 0) & (t <= 1 + 1e-12), t, np.inf)

    def center(self):
        return self.c

    def span(self, direction=(1.0, 0.0)):
        return 2 * self.r

    def params(self):
        return {"type": self.TYPE, "center": list(self.c), "radius": self.r}

    def shifted(self, sx, sy):
        return Disk((self.c[0] + sx, self.c[1] + sy), self.r)


class Rect(Shape):
    """A rectangle of ``size`` (w, h) about ``center``, turned by ``angle`` (rad, counter-clockwise)."""
    TYPE = "rect"

    def __init__(self, center, size, angle: float = 0.0):
        self.c = (float(center[0]), float(center[1]))
        self.w, self.h = float(size[0]), float(size[1])
        self.a = float(angle)
        if not (self.w > 0 and self.h > 0):
            raise ValueError("прямоугольник: размеры должны быть положительными")
        self._cs, self._sn = math.cos(self.a), math.sin(self.a)

    def _local(self, X, Y):
        dx, dy = X - self.c[0], Y - self.c[1]
        return dx * self._cs + dy * self._sn, -dx * self._sn + dy * self._cs

    def contains(self, X, Y):
        u, v = self._local(X, Y)
        return (np.abs(u) <= self.w / 2) & (np.abs(v) <= self.h / 2)

    def hit(self, X0, Y0, DX, DY):
        u0, v0 = self._local(X0, Y0)
        du = DX * self._cs + DY * self._sn
        dv = -DX * self._sn + DY * self._cs
        tin = np.zeros(np.shape(u0))
        tout = np.ones(np.shape(u0))
        ok = np.ones(np.shape(u0), bool)
        for p, d, half in ((u0, du, self.w / 2), (v0, dv, self.h / 2)):
            par = np.abs(d) < 1e-300
            ok &= ~(par & (np.abs(p) > half))
            with np.errstate(divide="ignore", invalid="ignore"):
                t1 = (-half - p) / d
                t2 = (half - p) / d
            lo = np.where(par, -np.inf, np.minimum(t1, t2))
            hi = np.where(par, np.inf, np.maximum(t1, t2))
            tin = np.maximum(tin, lo)
            tout = np.minimum(tout, hi)
        good = ok & (tin <= tout) & (tin > 0) & (tin <= 1 + 1e-12)
        return np.where(good, tin, np.inf)

    def center(self):
        return self.c

    def span(self, direction=(1.0, 0.0)):
        d = np.asarray(direction, float) / np.hypot(*direction)
        n = np.array([-d[1], d[0]])
        ax_u = np.array([self._cs, self._sn]) * self.w
        ax_v = np.array([-self._sn, self._cs]) * self.h
        return float(abs(ax_u @ n) + abs(ax_v @ n))

    def params(self):
        return {"type": self.TYPE, "center": list(self.c), "size": [self.w, self.h], "angle": self.a}

    def shifted(self, sx, sy):
        return Rect((self.c[0] + sx, self.c[1] + sy), (self.w, self.h), self.a)


class Polygon(Shape):
    """A simple polygon (vertices in order, either orientation); inside by the even-odd rule."""
    TYPE = "polygon"

    def __init__(self, points):
        p = np.asarray(points, float)
        if p.ndim != 2 or p.shape[1] != 2 or p.shape[0] < 3 or not np.all(np.isfinite(p)):
            raise ValueError("многоугольник: не меньше трёх конечных вершин (x, y)")
        self.p = p

    def contains(self, X, Y):
        X, Y = np.asarray(X, float), np.asarray(Y, float)
        inside = np.zeros(np.broadcast(X, Y).shape, bool)
        q = self.p
        for k in range(len(q)):
            x1, y1 = q[k]
            x2, y2 = q[(k + 1) % len(q)]
            if y1 == y2:
                continue
            cond = (y1 > Y) != (y2 > Y)
            xint = x1 + (Y - y1) * (x2 - x1) / (y2 - y1)
            inside ^= cond & (X < xint)
        return inside

    def hit(self, X0, Y0, DX, DY):
        best = np.full(np.shape(X0), np.inf)
        q = self.p
        for k in range(len(q)):
            ax, ay = q[k]
            bx, by = q[(k + 1) % len(q)]
            ex_, ey_ = bx - ax, by - ay
            den = DX * ey_ - DY * ex_
            with np.errstate(divide="ignore", invalid="ignore"):
                t = ((ax - X0) * ey_ - (ay - Y0) * ex_) / den
                s = ((ax - X0) * DY - (ay - Y0) * DX) / den
            good = (np.abs(den) > 1e-300) & (t > 0) & (t <= 1 + 1e-12) & (s >= -1e-12) & (s <= 1 + 1e-12)
            best = np.where(good & (t < best), t, best)
        return best

    def center(self):
        return tuple(float(v) for v in self.p.mean(axis=0))

    def span(self, direction=(1.0, 0.0)):
        d = np.asarray(direction, float) / np.hypot(*direction)
        proj = self.p @ np.array([-d[1], d[0]])
        return float(proj.max() - proj.min())

    def params(self):
        return {"type": self.TYPE, "points": self.p.tolist()}

    def shifted(self, sx, sy):
        return Polygon(self.p + np.array([sx, sy]))


class Mask(Shape):
    """Solid nodes given directly: a boolean array of the grid's shape (nx, ny), or a function f(X, Y) -> bool of
    the node coordinates (evaluated once, when the obstacle is added). No analytic boundary: walls half-way."""
    TYPE = "mask"

    def __init__(self, mask):
        self.fn = mask if callable(mask) else None
        self.m = None if callable(mask) else np.asarray(mask, bool).copy()

    @property
    def analytic(self) -> bool:
        return False

    def resolve(self, X, Y):
        if self.m is None:
            self.m = np.asarray(self.fn(X, Y), bool).reshape(X.shape).copy()
            self.fn = None
        if self.m.shape != X.shape:
            raise ValueError(f"маска: форма {self.m.shape}, а сетка {X.shape}")
        return self

    def contains(self, X, Y):
        if self.m is None or self.m.shape != np.shape(X):
            raise ValueError("маска задаётся на узлах сетки")
        return self.m

    def center(self):
        idx = np.argwhere(self.m)
        return tuple(float(v) for v in idx.mean(axis=0)) if len(idx) else (0.0, 0.0)  # in nodes; replaced by Flow2D

    def span(self, direction=(1.0, 0.0)):
        return float("nan")  # in nodes; Flow2D computes it in metres

    def params(self):
        return {"type": self.TYPE, "mask": None if self.m is None else self.m.copy()}

    def shifted(self, sx, sy):
        raise ValueError("маска задана на узлах сетки: её нельзя перенести на другую сетку или сдвинуть")


SHAPES = {"disk": lambda d: Disk(d["center"], d["radius"]),
          "rect": lambda d: Rect(d["center"], d["size"], d.get("angle", 0.0)),
          "polygon": lambda d: Polygon(d["points"]),
          "mask": lambda d: Mask(np.asarray(d["mask"], bool))}


def shape_from_params(d: dict) -> Shape:
    if d.get("type") not in SHAPES:
        raise ValueError(f"неизвестная форма {d.get('type')!r}")
    return SHAPES[d["type"]](d)


# --- sides --------------------------------------------------------------------------------------------------------------
class Side:
    KIND = ""

    def params(self) -> dict:
        raise NotImplementedError


class Wall(Side):
    """A no-slip wall (half-way bounce-back), moving along itself with ``velocity`` (m/s; along +x for bottom/top,
    along +y for left/right): a driven lid."""
    KIND = "wall"

    def __init__(self, velocity: float = 0.0):
        self.velocity = float(velocity)

    def params(self):
        return {"kind": self.KIND, "velocity": self.velocity}


class Inlet(Side):
    """A velocity inlet: ``velocity`` (m/s, into the domain; the maximum of a parabolic profile), ``profile``
    "uniform" | "parabolic" | f(s) -> m/s of the coordinate s (m) along the side; ``tangential`` (m/s, along +x or +y);
    ``ramp`` (s): the inflow grows from zero as sin^2(pi t / 2 ramp) over this time after the inlet is set (a smooth
    start excites less sound: the weakly compressible flow carries sound waves, which the inlet and outlet reflect);
    ``dye``: the concentration of the inflowing dye (a number or f(s))."""
    KIND = "inlet"

    def __init__(self, velocity: float = 0.0, profile="uniform", tangential: float = 0.0, ramp: float = 0.0,
                 dye=0.0):
        self.velocity, self.profile, self.tangential = float(velocity), profile, float(tangential)
        self.ramp, self.dye = float(ramp), dye
        if not (isinstance(profile, str) and profile in ("uniform", "parabolic") or callable(profile)):
            raise ValueError("вход: профиль 'uniform', 'parabolic' или функция")
        if self.ramp < 0:
            raise ValueError("вход: время разгона ≥ 0")

    def normal_velocity(self, s, length):
        s = np.asarray(s, float)
        if callable(self.profile):
            return np.asarray(self.profile(s), float) * np.ones_like(s)
        if self.profile == "parabolic":
            return 4 * self.velocity * s * (length - s) / length**2
        return np.full_like(s, self.velocity)

    def dye_at(self, s):
        s = np.asarray(s, float)
        return np.asarray(self.dye(s), float) * np.ones_like(s) if callable(self.dye) else np.full_like(s, float(self.dye))

    def params(self):
        if callable(self.profile) or callable(self.dye):
            raise ValueError("вход с профилем-функцией не сохраняется как данные: задайте 'uniform'/'parabolic' и "
                             "число для краски")
        return {"kind": self.KIND, "velocity": self.velocity, "profile": self.profile,
                "tangential": self.tangential, "ramp": self.ramp, "dye": float(self.dye)}


class Outlet(Side):
    """A pressure outlet (anti-bounce-back): ``pressure`` (Pa, relative to the reference pressure of rho0)."""
    KIND = "outlet"

    def __init__(self, pressure: float = 0.0):
        self.pressure = float(pressure)

    def params(self):
        return {"kind": self.KIND, "pressure": self.pressure}


class Periodic(Side):
    KIND = "periodic"

    def params(self):
        return {"kind": self.KIND}


def side_from_params(d: dict) -> Side:
    k = d.get("kind")
    if k == "wall":
        return Wall(d.get("velocity", 0.0))
    if k == "inlet":
        return Inlet(d["velocity"], d.get("profile", "uniform"), d.get("tangential", 0.0), d.get("ramp", 0.0),
                     d.get("dye", 0.0))
    if k == "outlet":
        return Outlet(d.get("pressure", 0.0))
    if k == "periodic":
        return Periodic()
    raise ValueError(f"неизвестная сторона {k!r}")


def _as_side(s) -> Side:
    if isinstance(s, Side):
        return s
    if isinstance(s, str):
        return side_from_params({"kind": s, "velocity": 0.0})
    if isinstance(s, dict):
        return side_from_params(s)
    raise ValueError(f"сторона: {s!r}")


# --- the CUDA kernel ----------------------------------------------------------------------------------------------------
def _r(v: float) -> str:
    return repr(float(v))


_EU = {1: "ux", 2: "uy", 5: "(ux + uy)", 6: "(uy - ux)"}


def _cuda_source() -> str:
    """The fused step for GPU 0: one thread per node; the same operations, in the same order, as ``_step_cpu``."""
    L = []
    a = L.append
    a('extern "C" __global__ void lbm_step(')
    a("  const double* __restrict__ fs, double* __restrict__ fn, const double* __restrict__ gs, double* __restrict__ gn,")
    a("  const unsigned char* __restrict__ flags, const int* __restrict__ slot,")
    a("  const signed char* __restrict__ ltype, const signed char* __restrict__ dtype, const signed char* __restrict__ lsd,")
    a("  const double* __restrict__ lc1, const double* __restrict__ lc2, const double* __restrict__ lval,")
    a("  const double* __restrict__ dval, const int* __restrict__ lnb,")
    a("  double* __restrict__ acc_m, double* __restrict__ acc_p, double* __restrict__ last_m, double* __restrict__ last_p,")
    a("  double* __restrict__ acc_d, const double* __restrict__ csrc, double* __restrict__ src_acc,")
    a("  double* __restrict__ cmp_m, double* __restrict__ cmp_p, double* __restrict__ cmp_d,")
    a("  const double* __restrict__ prm, const int nx, const int ny, const int dye_on, const int force_on)")
    a("{")
    a("  const int n = blockDim.x * blockIdx.x + threadIdx.x;")
    a("  const int N = nx * ny;")
    a("  if (n >= N) return;")
    a("  const unsigned char fl = flags[n];")
    a("  if (fl & 1) {")
    for i in range(9):
        a(f"    fn[{i} * N + n] = {_r(W[i])};")
    a("    if (dye_on) {")
    for i in range(5):
        a(f"      gn[{i} * N + n] = 0.0;")
    a("    }")
    a("    return;")
    a("  }")
    a("  const int x = n / ny;")
    a("  const int y = n - x * ny;")
    a("  const double hFx = prm[2], hFy = prm[3];")
    a("  double f[9];")
    a("  int sl[9];")
    a("  f[0] = fs[n];")
    a("  sl[0] = -1;")
    for i in range(1, 9):
        o = int(OPP[i])
        a("  {")
        a("    int l = -1;")
        a(f"    if (fl & 2) l = slot[{i - 1} * N + n];")
        a(f"    sl[{i}] = l;")
        a("    if (l < 0) {")
        a(f"      int xs = x - ({int(EX[i])}); if (xs < 0) xs += nx; else if (xs >= nx) xs -= nx;")
        a(f"      int ys = y - ({int(EY[i])}); if (ys < 0) ys += ny; else if (ys >= ny) ys -= ny;")
        a(f"      f[{i}] = fs[{i} * N + xs * ny + ys];")
        a("    } else {")
        a(f"      const double fo = fs[{o} * N + n];")
        a("      const int t = ltype[l];")
        a("      double v;")
        a("      if (t == 1) v = fo + lval[l];")
        a("      else if (t == 2) { const double s = prm[40 + lsd[l]]; v = fo + ((lc1[l] * (1.0 - s)) + (lval[l] * s)); }")
        a(f"      else if (t == 3) v = lc1[l] * fo + lc2[l] * fs[{o} * N + lnb[l]];")
        a(f"      else if (t == 4) v = lc1[l] * fo + lc2[l] * fs[{i} * N + n];")
        a("      else {")
        a("        double ux, uy;")
        a("        {")
        a("          const double* p = fs + n;")
        a("          const double r = (((((((p[0] + p[N]) + p[2*N]) + p[3*N]) + p[4*N]) + p[5*N]) + p[6*N]) + p[7*N]) + p[8*N];")
        a("          const double jx = ((p[N] + p[5*N]) + p[8*N]) - ((p[3*N] + p[6*N]) + p[7*N]);")
        a("          const double jy = ((p[2*N] + p[5*N]) + p[6*N]) - ((p[4*N] + p[7*N]) + p[8*N]);")
        a("          ux = (jx - hFx) / r; uy = (jy - hFy) / r;")
        a("        }")
        a("        double uwx = ux, uwy = uy;")
        a("        const int nb = lnb[l];")
        a("        if (nb >= 0) {")
        a("          const double* p = fs + nb;")
        a("          const double r = (((((((p[0] + p[N]) + p[2*N]) + p[3*N]) + p[4*N]) + p[5*N]) + p[6*N]) + p[7*N]) + p[8*N];")
        a("          const double jx = ((p[N] + p[5*N]) + p[8*N]) - ((p[3*N] + p[6*N]) + p[7*N]);")
        a("          const double jy = ((p[2*N] + p[5*N]) + p[6*N]) - ((p[4*N] + p[7*N]) + p[8*N]);")
        a("          const double ux2 = (jx - hFx) / r, uy2 = (jy - hFy) / r;")
        a("          uwx = ux + 0.5 * (ux - ux2); uwy = uy + 0.5 * (uy - uy2);")
        a("        }")
        a(f"        const double eu = {_r(EX[i])} * uwx + {_r(EY[i])} * uwy;")
        a("        v = (-fo) + lval[l] * ((1.0 + (4.5 * eu) * eu) - 1.5 * (uwx * uwx + uwy * uwy));")
        a("      }")
        # Kahan's compensated sums (``_kahan``: the same four operations)
        a("      { const double y_ = (v - fo) - cmp_m[l]; const double t_ = acc_m[l] + y_; cmp_m[l] = (t_ - acc_m[l]) - y_; acc_m[l] = t_; }")
        a("      { const double y_ = (v + fo) - cmp_p[l]; const double t_ = acc_p[l] + y_; cmp_p[l] = (t_ - acc_p[l]) - y_; acc_p[l] = t_; }")
        a("      last_m[l] = v - fo;")
        a("      last_p[l] = v + fo;")
        a(f"      f[{i}] = v;")
        a("    }")
        a("  }")
    # collision
    a("  const double rho = (((((((f[0] + f[1]) + f[2]) + f[3]) + f[4]) + f[5]) + f[6]) + f[7]) + f[8];")
    a("  const double jx = ((f[1] + f[5]) + f[8]) - ((f[3] + f[6]) + f[7]);")
    a("  const double jy = ((f[2] + f[5]) + f[6]) - ((f[4] + f[7]) + f[8]);")
    a("  const double ux = (jx + hFx) / rho;")
    a("  const double uy = (jy + hFy) / rho;")
    a("  const double usq = ux * ux + uy * uy;")
    a("  const double omp = prm[0], omm = prm[1];")
    a("  const double uF3 = 3.0 * (ux * prm[7] + uy * prm[8]);")
    a("  double h9[9];")
    for i, o in PAIRS:
        a("  {")
        a(f"    const double eu = {_EU[i]};")
        a(f"    const double wr = {_r(W[i])} * rho;")
        a("    const double feqp = wr * ((1.0 + (4.5 * eu) * eu) - 1.5 * usq);")
        a("    const double feqm = wr * (3.0 * eu);")
        a(f"    const double dp = omp * (0.5 * (f[{i}] + f[{o}]) - feqp);")
        a(f"    const double dm = omm * (0.5 * (f[{i}] - f[{o}]) - feqm);")
        a(f"    double ni = (f[{i}] - dp) - dm;")
        a(f"    double no = (f[{o}] - dp) + dm;")
        a("    if (force_on) {")
        a(f"      const double Fp = prm[{10 + i}] * ((9.0 * eu) * prm[{30 + i}] - uF3);")
        a(f"      ni = ni + (Fp + prm[{20 + i}]);")
        a(f"      no = no + (Fp - prm[{20 + i}]);")
        a("    }")
        a(f"    h9[{i}] = ni;")
        a(f"    h9[{o}] = no;")
        a("  }")
    a("  h9[0] = rho - (((((((h9[1] + h9[2]) + h9[3]) + h9[4]) + h9[5]) + h9[6]) + h9[7]) + h9[8]);")
    for i in range(9):
        a(f"  fn[{i} * N + n] = h9[{i}];")
    # dye
    a("  if (dye_on) {")
    a("    double g[5];")
    a("    g[0] = gs[n];")
    for i in range(1, 5):
        o = int(OPP[i])
        a("    {")
        a(f"      const int l = sl[{i}];")
        a("      if (l < 0) {")
        a(f"        int xs = x - ({int(EX[i])}); if (xs < 0) xs += nx; else if (xs >= nx) xs -= nx;")
        a(f"        int ys = y - ({int(EY[i])}); if (ys < 0) ys += ny; else if (ys >= ny) ys -= ny;")
        a(f"        g[{i}] = gs[{i} * N + xs * ny + ys];")
        a("      } else {")
        a(f"        const double go = gs[{o} * N + n];")
        a("        const int t = dtype[l];")
        a("        double v;")
        a("        if (t == 2) v = (-go) + dval[l];")
        a(f"        else if (t == 3) v = gs[{i} * N + n];")
        a("        else v = go;")
        a("        { const double y_ = (v - go) - cmp_d[l]; const double t_ = acc_d[l] + y_; cmp_d[l] = (t_ - acc_d[l]) - y_; acc_d[l] = t_; }")
        a(f"        g[{i}] = v;")
        a("      }")
        a("    }")
    a("    const double C = (((g[0] + g[1]) + g[2]) + g[3]) + g[4];")
    a("    const double ogp = prm[5], ogm = prm[6];")
    a("    double h[5];")
    for i, o, eu in ((1, 3, "ux"), (2, 4, "uy")):
        a("    {")
        a(f"      const double wc = {_r(WG[i])} * C;")
        a(f"      const double geqm = wc * (3.0 * {eu});")
        a(f"      const double dp = ogp * (0.5 * (g[{i}] + g[{o}]) - wc);")
        a(f"      const double dm = ogm * (0.5 * (g[{i}] - g[{o}]) - geqm);")
        a(f"      h[{i}] = (g[{i}] - dp) - dm;")
        a(f"      h[{o}] = (g[{o}] - dp) + dm;")
        a("    }")
    a("    h[0] = C - (((h[1] + h[2]) + h[3]) + h[4]);")
    a("    if (fl & 4) {")
    a("      const double Cs = csrc[n];")
    a(f"      double e[5];")
    a(f"      e[0] = {_r(WG[0])} * Cs;")
    a(f"      e[1] = ({_r(WG[1])} * Cs) * (1.0 + 3.0 * ux);")
    a(f"      e[2] = ({_r(WG[2])} * Cs) * (1.0 + 3.0 * uy);")
    a(f"      e[3] = ({_r(WG[3])} * Cs) * (1.0 - 3.0 * ux);")
    a(f"      e[4] = ({_r(WG[4])} * Cs) * (1.0 - 3.0 * uy);")
    a("      { const double y_ = (((((e[0] - h[0]) + (e[1] - h[1])) + (e[2] - h[2])) + (e[3] - h[3])) + (e[4] - h[4])) - src_acc[N + n];")
    a("        const double t_ = src_acc[n] + y_; src_acc[N + n] = (t_ - src_acc[n]) - y_; src_acc[n] = t_; }")
    a("      h[0] = e[0]; h[1] = e[1]; h[2] = e[2]; h[3] = e[3]; h[4] = e[4];")
    a("    }")
    for i in range(5):
        a(f"    gn[{i} * N + n] = h[{i}];")
    a("  }")
    a("}")
    a('extern "C" __global__ void lbm_moments(const double* __restrict__ fs, const unsigned char* __restrict__ flags,')
    a("  const double hFx, const double hFy, double* __restrict__ out, const int N)")
    a("{")
    a("  const int n = blockDim.x * blockIdx.x + threadIdx.x;")
    a("  if (n >= N) return;")
    a("  const double* p = fs + n;")
    a("  const double r = (((((((p[0] + p[N]) + p[2*N]) + p[3*N]) + p[4*N]) + p[5*N]) + p[6*N]) + p[7*N]) + p[8*N];")
    a("  const double jx = ((p[N] + p[5*N]) + p[8*N]) - ((p[3*N] + p[6*N]) + p[7*N]);")
    a("  const double jy = ((p[2*N] + p[5*N]) + p[6*N]) - ((p[4*N] + p[7*N]) + p[8*N]);")
    a("  out[n] = r; out[N + n] = (jx - hFx) / r; out[2 * N + n] = (jy - hFy) / r;")
    a("}")
    return "\n".join(L)


_GPU_MODULE = {}


def _gpu_kernels(cp):
    if "mod" not in _GPU_MODULE:
        _GPU_MODULE["mod"] = cp.RawModule(code=_cuda_source(), options=("--fmad=false", "-std=c++11"))
    m = _GPU_MODULE["mod"]
    return m.get_function("lbm_step"), m.get_function("lbm_moments")


# --- NumPy pieces shared by both devices ------------------------------------------------------------------------------
def _ksum(acc, cmp) -> float:
    """sum(acc - cmp) of Kahan-compensated records (``LINK_ACC``), summed exactly (``math.fsum``) and rounded once."""
    return math.fsum(np.concatenate([np.ravel(acc), -np.ravel(cmp)]).tolist())


def _kahan(acc, cmp, x):
    """One compensated addition of ``x`` to the running sums ``acc`` with their compensations ``cmp`` (arrays or floats;
    the true sum is acc - cmp): the same four operations as the GPU kernel's (no fused multiply-adds)."""
    y = x - cmp
    t = acc + y
    return t, (t - acc) - y


def _moments_post(f, hFx, hFy):
    """Density and velocity from post-collision populations (the stored state): u = (sum e f* - F/2) / rho."""
    r = f[0] + f[1] + f[2] + f[3] + f[4] + f[5] + f[6] + f[7] + f[8]
    jx = ((f[1] + f[5]) + f[8]) - ((f[3] + f[6]) + f[7])
    jy = ((f[2] + f[5]) + f[6]) - ((f[4] + f[7]) + f[8])
    return r, (jx - hFx) / r, (jy - hFy) / r


def _equilibrium(rho, ux, uy):
    usq = ux * ux + uy * uy
    out = []
    for i in range(9):
        eu = EX[i] * ux + EY[i] * uy
        out.append(W[i] * rho * ((1.0 + (4.5 * eu) * eu) - 1.5 * usq) + W[i] * rho * (3.0 * eu))
    return np.stack(out)


def _pull(dst, src, ex, ey):
    """dst[x, y] = src[(x - ex) % nx, (y - ey) % ny] (streaming with periodic wrap)."""
    nx, ny = src.shape
    if ex == 0 and ey == 0:
        dst[...] = src
        return
    xs = [(slice(None), slice(None))] if ex == 0 else (
        [(slice(1, None), slice(0, nx - 1)), (slice(0, 1), slice(nx - 1, nx))] if ex == 1 else
        [(slice(0, nx - 1), slice(1, None)), (slice(nx - 1, nx), slice(0, 1))])
    ys = [(slice(None), slice(None))] if ey == 0 else (
        [(slice(1, None), slice(0, ny - 1)), (slice(0, 1), slice(ny - 1, ny))] if ey == 1 else
        [(slice(0, ny - 1), slice(1, None)), (slice(ny - 1, ny), slice(0, 1))])
    for dxs, sxs in xs:
        for dys, sys_ in ys:
            dst[dxs, dys] = src[sxs, sys_]


def _sums(f, g, idx):
    """Mass, momentum (x, y) and dye of the nodes ``idx`` (lattice units) of host arrays."""
    ff = f.reshape(9, -1)[:, idx]
    M = float(np.sum(ff))
    Px = float(np.sum(((ff[1] + ff[5]) + ff[8]) - ((ff[3] + ff[6]) + ff[7])))
    Py = float(np.sum(((ff[2] + ff[5]) + ff[6]) - ((ff[4] + ff[7]) + ff[8])))
    D = 0.0 if g is None else float(np.sum(g.reshape(5, -1)[:, idx]))
    return M, Px, Py, D


_POOL = {}
LBM_THREADS = int(os.environ.get("LFPHYS_LBM_THREADS", "0")) or min(4, os.cpu_count() or 1)
MIN_BLOCK_NODES = 16384  # below this a block's NumPy calls cost more than threads gain


def _pool():
    if "p" not in _POOL:
        from concurrent.futures import ThreadPoolExecutor
        _POOL["p"] = ThreadPoolExecutor(max_workers=LBM_THREADS, thread_name_prefix="lfphys-lbm")
    return _POOL["p"]


def _blocks(nx: int, ny: int) -> list:
    """Row blocks for the threaded collision (``LBM_THREADS``, env LFPHYS_LBM_THREADS)."""
    k = max(1, min(LBM_THREADS, (nx * ny) // MIN_BLOCK_NODES, nx))
    edges = [round(nx * q / k) for q in range(k + 1)]
    return [(edges[q], edges[q + 1]) for q in range(k)]


class _Obstacle:
    def __init__(self, oid, shape, velocity=(0.0, 0.0), omega=0.0, interpolated=False, label="", ref_length=None):
        self.id, self.shape = int(oid), shape
        self.velocity = (float(velocity[0]), float(velocity[1]))
        self.omega, self.interpolated, self.label = float(omega), bool(interpolated), str(label)
        if ref_length is not None and not float(ref_length) >= 0.0:
            raise ValueError("длина для коэффициентов: ≥ 0 (0 — ширина тела поперёк потока)")
        # 0 means the default (the width across the flow): review B7 L10, a length set back to 0 is cleared
        self.ref_length = None if ref_length is None or float(ref_length) == 0.0 else float(ref_length)

    @property
    def moving(self) -> bool:
        return self.velocity != (0.0, 0.0) or self.omega != 0.0

    def surface_velocity(self, X, Y, c):
        return (self.velocity[0] - self.omega * (Y - c[1]), self.velocity[1] + self.omega * (X - c[0]))

    def params(self):
        return {"id": self.id, "shape": self.shape.params(), "velocity": list(self.velocity), "omega": self.omega,
                "interpolated": self.interpolated, "label": self.label, "ref_length": self.ref_length}


class _Source:
    def __init__(self, sid, shape, concentration, label=""):
        self.id, self.shape, self.concentration, self.label = int(sid), shape, float(concentration), str(label)

    def params(self):
        return {"id": self.id, "shape": self.shape.params(), "concentration": self.concentration,
                "label": self.label}


# --- measured speeds (cost_estimate) ----------------------------------------------------------------------------------
# (nodes, seconds per step) measured 2026-11-04 by ``bench`` (a periodic square with one disk, a body force and the dye;
# best of three): CPU = the image's NumPy, collision on 4 threads (LBM_THREADS), in a container with 16 CPUs of an
# i9-9900K; GPU = RTX 2080 Ti (GPU 0), the state on the device. GPU / CPU: x8 at 32^2, x14 at 64^2, x47 at 128^2, x45 at
# 256^2, x96 at 512^2, x155 at 1024^2 (965 Mnode/s against 6.2 on the CPU); below 128^2 the GPU's step is the ~34 us
# of a kernel launch from Python.
RATES = {
    "cpu": [(32**2, 2.76e-4), (64**2, 5.00e-4), (128**2, 1.59e-3), (256**2, 4.81e-3), (512**2, 2.74e-2),
            (1024**2, 1.68e-1)],
    "gpu": [(32**2, 3.38e-5), (64**2, 3.47e-5), (128**2, 3.40e-5), (256**2, 1.08e-4), (512**2, 2.85e-4),
            (1024**2, 1.09e-3)],
}
RATES_NOTE = ("измерено 2026-11-04: CPU (NumPy, столкновения в 4 потоках) 6–14 млн узлов/с; GPU 0 (RTX 2080 Ti) до "
              "965 млн узлов/с, быстрее CPU при любом размере от 32² (×8) до 1024² (×155)")


def _interp_rate(dev: str, nodes: int) -> float:
    pts = RATES[dev]
    x = np.log([q for q, _ in pts])
    y = np.log([s for _, s in pts])
    n = math.log(max(nodes, 1))
    if x[0] <= n <= x[-1]:
        return float(np.exp(np.interp(n, x, y)))
    q, t = pts[0] if n < x[0] else pts[-1]
    return float(t * nodes / q) if n > x[-1] else float(t)


def _same_velocity(a: "Inlet", b: "Inlet") -> bool:
    """Two inlets impose the same velocity (profile, size, tangential part); their dye or ramp may differ."""
    pa, pb = a.profile, b.profile
    same = (pa == pb) if isinstance(pa, str) and isinstance(pb, str) else (pa is pb)
    return same and a.velocity == b.velocity and a.tangential == b.tangential


def _rec_copy(rec):
    if rec is None:
        return None
    return {**rec, "prev": dict(rec["prev"]), "t": list(rec["t"]), "F": {k: list(v) for k, v in rec["F"].items()}}


# --- the solver -------------------------------------------------------------------------------------------------------
class Flow2D:
    """A 2-D incompressible flow on a D2Q9 lattice in the domain [0, Lx] x [0, Ly] (m).

    Parameters: ``size`` (Lx, Ly) in m (rounded to whole cells of ``dx``); ``dx`` (m); the fluid: kinematic viscosity
    ``nu`` (m^2/s) or dynamic ``mu`` (Pa s), density ``rho`` (kg/m^3); the time step: ``dt`` (s), or from the Mach
    number ``mach`` of the largest expected velocity ``u_max`` (m/s), capped so that tau+ <= ``tau_max``
    (``Units.from_flow``); ``sides``: {"left"|"right"|"bottom"|"top": Wall | Inlet | Outlet | Periodic | "wall" |
    "periodic" | ...} (default walls); ``collision`` "trt" | "bgk", ``magic`` (TRT's Lambda, default 3/16);
    ``gravity`` (m/s^2, a uniform body force per unit mass); ``dye``: the dye's diffusivity (m^2/s) or None (no dye);
    ``device`` "auto" | "cpu" | "gpu" (``lfphys.core.backend``); ``displaced`` "remove" | "spread" (what happens to
    the fluid in nodes that become solid, see the module's docstring).
    """

    def __init__(self, size, dx: float, nu: float | None = None, rho: float = 1000.0, mu: float | None = None,
                 u_max: float | None = None, mach: float = 0.1, dt: float | None = None, tau_max: float | None = 1.0,
                 sides=None, collision: str = "trt", magic: float = MAGIC, gravity=(0.0, 0.0), dye=None,
                 device: str = "auto", displaced: str = "remove", u_ref: float | None = None,
                 length_ref: float | None = None, t0: float = 0.0):
        if nu is None and mu is None:
            raise ValueError("жидкость: задайте ν (м²/с) или μ (Па·с)")
        nu = float(mu) / float(rho) if nu is None else float(nu)
        if not (nu > 0 and dx > 0):
            raise ValueError("жидкость: ν > 0, dx > 0")
        Lx, Ly = float(size[0]), float(size[1])
        self.nx, self.ny = int(round(Lx / dx)), int(round(Ly / dx))
        if self.nx < 2 or self.ny < 2:
            raise ValueError("область: не меньше 2 × 2 узлов")
        if dt is None:
            if u_max is None:
                raise ValueError("шаг по времени: задайте dt или u_max (с числом Маха)")
            self.units = Units.from_flow(dx, nu, u_max, mach, rho, tau_max)
        else:
            self.units = Units(dx, dt, rho)
        self.u_max = None if u_max is None else float(u_max)
        self.mach_target = float(mach)
        self.tau_max = tau_max
        if collision not in ("trt", "bgk"):
            raise ValueError("столкновения: 'trt' или 'bgk'")
        if displaced not in ("remove", "spread"):
            raise ValueError("вытесненная жидкость: 'remove' или 'spread'")
        self.collision, self.magic, self.displaced = collision, float(magic), displaced
        self.nu = nu
        self.device_mode = device
        self.u_ref, self.length_ref = u_ref, length_ref
        self.N = self.nx * self.ny
        u = self.units
        self.x = (np.arange(self.nx) + 0.5) * u.dx
        self.y = (np.arange(self.ny) + 0.5) * u.dx
        self._X, self._Y = np.meshgrid(self.x, self.y, indexing="ij")
        self.size = (self.nx * u.dx, self.ny * u.dx)
        self._sides = {s: Wall() for s in SIDES}
        if sides:
            for k, v in sides.items():
                if k not in SIDES:
                    raise ValueError(f"сторона {k!r}: одна из {SIDES}")
                self._sides[k] = _as_side(v)
        self._check_sides(self._sides)
        if not math.isfinite(float(t0)):
            raise ValueError("время начала: конечное число")
        self._t0 = float(t0)  # the time of step 0: t = t0 + steps dt (a world started from a scene file at its time)
        # the ramps of the inlets, per side: {"s0": the step it starts at, "ramp": duration (s), "from": [(Inlet,
        # weight), ...] (the velocity the side had when the inlet's velocity was set: empty after a wall)}; counted in
        # steps, so a flow started at a time t0 ramps exactly as one started at 0
        self._ramps = {k: {"s0": 0, "ramp": v.ramp, "from": []} for k, v in self._sides.items()
                       if isinstance(v, Inlet)}
        self.gravity = (float(gravity[0]), float(gravity[1]))
        self._obstacles: dict[int, _Obstacle] = {}
        self._sources: dict[int, _Source] = {}
        self._next_id = 0
        self._next_src = 0
        self.t, self.steps = self._t0, 0
        self.dye_D = None if dye is None else float(dye)
        self._check_numbers(self.nu, self.u_max)
        self._relax()
        # state on the host first
        self._f = np.empty((9, self.nx, self.ny))
        g0 = self._g_lattice()
        if self.gravity == (0.0, 0.0):
            for i in range(9):
                self._f[i] = W[i]
        else:  # at rest in the body force: the hydrostatic density and the half-step momentum F/2 (review B7 L6)
            xr, yr = self._hydro_refs()
            rho_s = 1.0 + (g0[0] * (self._X - xr) + g0[1] * (self._Y - yr)) / self.units.dx / CS2
            F = self.units.acceleration(self.gravity)
            self._f[...] = _equilibrium(rho_s, 0.5 * float(F[0]) / rho_s, 0.5 * float(F[1]) / rho_s)
        self._g = np.zeros((5, self.nx, self.ny)) if self.dye_D is not None else None
        self._src_acc = np.zeros((2, self.N))  # the dye injected by the sources per node and its compensation (Kahan)
        self._banked = {}
        self._banked_tq = {}  # obstacle key -> the torque's momentum-exchange sum folded at edits (lattice)
        self._body_imp = [0.0, 0.0, 0.0, 0.0]  # the body force's impulse (x, y) and its compensation (Kahan)
        self._timing = {"steps": 0, "seconds": 0.0}
        self._force_ref = None
        self._rec = None  # the force record (``record_forces``)
        self._xp, self.device = np, "cpu"
        self._dev = None
        self._build(reset_acc=True)
        self._baseline()
        self._choose()

    # --- parameters, numbers and refusals ---------------------------------------------------------------------------
    def _relax(self):
        nu_l = self.units.viscosity(self.nu)
        self.tau_p = 3 * nu_l + 0.5
        if self.collision == "bgk":
            self.tau_m = self.tau_p
        else:
            self.tau_m = 0.5 + self.magic / (self.tau_p - 0.5)
        self.om_p, self.om_m = 1 / self.tau_p, 1 / self.tau_m
        F = self.units.acceleration(self.gravity)  # force density with rho0 = 1
        self._F = (float(F[0]), float(F[1]))
        if self.dye_D is not None:
            d_l = self.units.viscosity(self.dye_D)
            self.tau_gm = max(3 * d_l + 0.5, DYE_TAU_MIN)
            self.tau_gp = 0.5 + DYE_LAMBDA / (self.tau_gm - 0.5)
            self.dye_D_used = (self.tau_gm - 0.5) / 3 * self.units.dx**2 / self.units.dt
        else:
            self.tau_gm = self.tau_gp = 1.0
            self.dye_D_used = None
        self._prm_host = self._params_vector()

    def _params_vector(self) -> np.ndarray:
        p = np.zeros(44)
        Fx, Fy = self._F
        p[0], p[1] = self.om_p, self.om_m
        p[2], p[3] = 0.5 * Fx, 0.5 * Fy
        p[40:44] = 1.0  # the inlets' ramp scales per side (left, right, bottom, top), set per step
        p[5], p[6] = 1 / self.tau_gp, 1 / self.tau_gm
        p[7], p[8] = Fx, Fy
        cp_, cm_ = 1.0 - 0.5 * self.om_p, 1.0 - 0.5 * self.om_m
        eF = {0: 0.0, 1: Fx, 2: Fy, 5: Fx + Fy, 6: Fy - Fx}
        p[10] = cp_ * W[0]
        for i, _ in PAIRS:
            p[10 + i] = cp_ * W[i]
            p[20 + i] = (cm_ * W[i]) * (3.0 * eF[i])
            p[30 + i] = eF[i]
        return p

    def _check_numbers(self, nu, u_max, sides=None, gravity=None):
        u = self.units
        sides = sides or self._sides
        self._check_densities(sides, self.gravity if gravity is None else gravity)
        nu_l = u.viscosity(nu)
        if nu_l < TAU_MIN_EXCESS / 3:
            raise ValueError(f"неустойчиво: τ = {3 * nu_l + 0.5:.5g} слишком близко к 1/2 (нужно τ − 1/2 ≥ "
                             f"{TAU_MIN_EXCESS}); увеличьте вязкость или уменьшите dx, или увеличьте dt")
        vmax = 0.0 if u_max is None else float(u_max)
        for s in (sides or self._sides).values():
            if isinstance(s, Wall):
                vmax = max(vmax, abs(s.velocity))
            elif isinstance(s, Inlet):
                if callable(s.profile):
                    ss = np.linspace(0, max(self.size), 257)
                    vn = float(np.max(np.abs(s.normal_velocity(ss, max(self.size)))))
                else:
                    vn = abs(s.velocity)
                vmax = max(vmax, math.hypot(vn, s.tangential))
        for ob in self._obstacles.values():
            vmax = max(vmax, self._surface_speed_max(ob))
        ma = vmax / u.c / CS
        if ma > MACH_MAX:
            raise ValueError(f"число Маха {ma:.3g} > {MACH_MAX}: ошибка сжимаемости O(Ma²) слишком велика (и схема "
                             f"неустойчива); уменьшите dt (или скорость)")
        rec = vmax * u.dx / nu if nu > 0 else math.inf
        lim = self.re_cell_limit(sides)
        if rec > lim:
            raise ValueError(f"число Рейнольдса ячейки u·dx/ν = {rec:.3g} > {lim:g}: сетка не разрешает течение "
                             f"(неустойчиво); уменьшите dx или скорость, или увеличьте вязкость")
        return ma, rec

    def _g_lattice(self, gravity=None, sides=None) -> tuple:
        """The body force in lattice units with its components along periodic axes left out (there it drives the
        flow: no hydrostatic part)."""
        g = self.units.acceleration(self.gravity if gravity is None else gravity)
        sides = sides or self._sides
        px, py = isinstance(sides["left"], Periodic), isinstance(sides["bottom"], Periodic)
        return (0.0 if px else float(g[0]), 0.0 if py else float(g[1]))

    def _hydro_refs(self, sides=None) -> tuple:
        """(x_ref, y_ref) in m where the hydrostatic part of the rest state vanishes: along an axis with an outlet at one
        end only, at that outlet (its pressure is the pressure there); otherwise the middle."""
        sides = sides or self._sides

        def ref(a, b, L):
            oa, ob = isinstance(sides[a], Outlet), isinstance(sides[b], Outlet)
            return 0.0 if (oa and not ob) else L if (ob and not oa) else 0.5 * L
        return ref("left", "right", self.size[0]), ref("bottom", "top", self.size[1])

    def hydrostatic_spread(self, gravity=None, sides=None) -> float:
        """The relative density difference across the domain that a body force g sustains at rest, |g| . L / c_s^2 in
        lattice units (the force density rho0 g is uniform, so the rest state's density is linear: c_s^2 grad rho =
        rho0 g); none along a periodic axis."""
        g = self._g_lattice(gravity, sides)
        return (abs(g[0]) * self.nx + abs(g[1]) * self.ny) / CS2

    def _check_densities(self, sides, gravity):
        """Refuse a rest state the weakly compressible scheme cannot carry (review B7 L6, L7): the density that the
        outlets' pressures and the body force's hydrostatic part impose, rho = rho_out + g . (x - x_ref) / c_s^2
        (lattice), may deviate from rho0 by at most ``RHO_DEV_MAX`` anywhere in the domain (a linear field: at the
        corners), for each outlet's level (1 without outlets: the mass is conserved)."""
        u = self.units
        g = self._g_lattice(gravity, sides)
        xr, yr = self._hydro_refs(sides)
        levels = [(name, s.pressure, float(u.density_of_pressure(s.pressure))) for name, s in sides.items()
                  if isinstance(s, Outlet)] or [(None, 0.0, 1.0)]
        worst = (0.0, None)
        for name, p, lev in levels:
            for X in (0.0, self.size[0]):
                for Y in (0.0, self.size[1]):
                    r = lev + (g[0] * (X - xr) + g[1] * (Y - yr)) / u.dx / CS2
                    if abs(r - 1.0) > abs(worst[0]):
                        worst = (r - 1.0, (name, p, X, Y))
        dev = abs(worst[0])
        if dev <= RHO_DEV_MAX:
            return
        name, p, X, Y = worst[1]
        what = []
        if name is not None and p != 0.0:
            what.append(f"давление выхода ({name}) {p:g} Па")
        if g != (0.0, 0.0):
            what.append(f"объёмная сила ({gravity[0]:g}, {gravity[1]:g}) м/с² (гидростатический перепад g·L/c_s² = "
                        f"{self.hydrostatic_spread(gravity, sides):.3g})")
        at = f"в точке ({X:g}, {Y:g}) м; " if g != (0.0, 0.0) else ""
        raise ValueError(f"{' и '.join(what)}: плотность покоя схемы отклонилась бы от ρ0 на {dev:.3g} > "
                         f"{RHO_DEV_MAX:g} ({at}масштаб давления схемы c_s²ρ(dx/dt)² = "
                         f"{CS2 * u.rho * u.c**2:.4g} Па, её скорость звука c_s = {u.c * CS:.4g} м/с — свойство счёта, "
                         f"не жидкости): ошибка сжимаемости слишком велика; уменьшите давление или силу, или увеличьте "
                         f"«наибольшую ожидаемую скорость» (шаг по времени меньше, c_s больше)")

    def _hydrostatic_shift(self, g_old, g_new):
        """A body force changed now: add the change of its hydrostatic pressure at once (an incompressible fluid's
        pressure follows a body force instantly; the weakly compressible scheme would set it by sound waves that
        overshoot it, review B7 L6) — every fluid node's density changes by (g_new - g_old) . (x - x_ref) / c_s^2
        (lattice), added as rest equilibrium w_i d rho —, and the half-step momentum (F_new - F_old) / 2 of the stored
        post-collision state (its momentum is rho u + F / 2): the velocity read stays continuous and a fluid at rest stays
        at rest. What this adds is booked ("body_force_change")."""
        a, b = self._g_lattice(g_old), self._g_lattice(g_new)
        dg = (b[0] - a[0], b[1] - a[1])
        Fa, Fb = self.units.acceleration(g_old), self.units.acceleration(g_new)
        hx, hy = 0.5 * (float(Fb[0]) - float(Fa[0])), 0.5 * (float(Fb[1]) - float(Fa[1]))
        if dg == (0.0, 0.0) and (hx, hy) == (0.0, 0.0):
            return
        xr, yr = self._hydro_refs()
        d = ((dg[0] * (self._X - xr) + dg[1] * (self._Y - yr)) / self.units.dx / CS2).ravel()[self._fluid_idx]
        f, g = self._host_state()
        k = self._fluid_idx
        before = _sums(f, g, k)
        ff = f.reshape(9, -1)
        for i in range(9):
            ff[i, k] = ff[i, k] + (W[i] * d + W[i] * (3.0 * (EX[i] * hx + EY[i] * hy)))
        after = _sums(f, g, k)
        bk = self._banked.setdefault("body_force_change", [0.0, 0.0, 0.0, 0.0])
        for q in range(4):
            bk[q] += after[q] - before[q]
        self._drop_dev()
        self._put_state(f, g)

    def _outlet_density(self, name, side, s, gravity=None, sides=None):
        """The lattice density an outlet imposes at the points ``s`` (m) along its side: its pressure, plus, with a body
        force along the side, the hydrostatic part g_s (s - s_mid) / c_s^2 (lattice units, rho0 = 1): a fluid at rest
        in the force stays at rest (a uniform-pressure outlet is not in hydrostatic balance with a force along it);
        none along a periodic axis (there the force drives the flow)."""
        g = self.gravity if gravity is None else gravity
        sides = sides or self._sides
        vertical = name in ("left", "right")
        length = self.size[1] if vertical else self.size[0]
        base = float(self.units.density_of_pressure(side.pressure))
        s = np.asarray(s, float)
        g_s = self._g_lattice(g, sides)[1 if vertical else 0]
        if g_s == 0.0:
            return np.full_like(s, base)
        return base + g_s * ((s - 0.5 * length) / self.units.dx) / CS2

    def _inlet_wall_velocity(self, side, name, s):
        """An inlet's velocity (lattice units) at the points ``s`` (m) along its side: (ux, uy)."""
        vertical = name in ("left", "right")  # the side's coordinate s is y
        length = self.size[1] if vertical else self.size[0]
        un = side.normal_velocity(s, length) / self.units.c
        ut = side.tangential / self.units.c
        sign = {"left": 1.0, "right": -1.0, "bottom": 1.0, "top": -1.0}[name]
        return (sign * un, np.full_like(un, ut)) if vertical else (np.full_like(un, ut), sign * un)

    def re_cell_limit(self, sides=None) -> float:
        """The largest grid Reynolds number u_max dx / nu accepted (measured, see ``RE_CELL_MAX_OPEN``)."""
        open_ = any(isinstance(v, (Inlet, Outlet)) for v in (sides or self._sides).values())
        return RE_CELL_MAX_OPEN if open_ else RE_CELL_MAX

    def _surface_speed_max(self, ob):
        if not ob.moving:
            return 0.0
        c = self._center(ob)
        r = 0.0
        if isinstance(ob.shape, Disk):
            r = ob.shape.r
        else:
            m = self._shape_mask(ob.shape)
            if m.any():
                r = float(np.max(np.hypot(self._X[m] - c[0], self._Y[m] - c[1]))) + self.units.dx
        return math.hypot(*ob.velocity) + abs(ob.omega) * r

    def _check_sides(self, sides):
        for a, b in (("left", "right"), ("bottom", "top")):
            pa, pb = isinstance(sides[a], Periodic), isinstance(sides[b], Periodic)
            if pa != pb:
                raise ValueError(f"периодичность: стороны {a} и {b} — обе периодические или ни одна")

    @property
    def periodic(self) -> tuple[bool, bool]:
        return isinstance(self._sides["left"], Periodic), isinstance(self._sides["bottom"], Periodic)

    # --- geometry ---------------------------------------------------------------------------------------------------
    def _images(self):
        px, py = self.periodic
        Lx, Ly = self.size
        return [(ax * Lx, ay * Ly) for ax in ((-1, 0, 1) if px else (0,)) for ay in ((-1, 0, 1) if py else (0,))]

    def _shape_mask(self, shape) -> np.ndarray:
        if isinstance(shape, Mask):
            return shape.resolve(self._X, self._Y).m
        m = np.zeros((self.nx, self.ny), bool)
        for ox, oy in self._images():
            m |= shape.contains(self._X - ox, self._Y - oy)
        return m

    def _center(self, ob) -> tuple:
        if isinstance(ob.shape, Mask):
            m = ob.shape.m
            if not m.any():
                return (0.0, 0.0)
            return (float(self._X[m].mean()), float(self._Y[m].mean()))
        return ob.shape.center()

    def _span(self, ob, direction=(1.0, 0.0)) -> float:
        if ob.ref_length is not None:
            return ob.ref_length
        if isinstance(ob.shape, Mask):
            m = ob.shape.m
            d = np.asarray(direction, float) / np.hypot(*direction)
            proj = self._X[m] * -d[1] + self._Y[m] * d[0]
            return float(proj.max() - proj.min() + self.units.dx) if m.any() else 0.0
        return ob.shape.span(direction)

    def _hit(self, shape, X0, Y0, DX, DY):
        t = np.full(np.shape(X0), np.inf)
        for ox, oy in self._images():
            t = np.minimum(t, shape.hit(X0 - ox, Y0 - oy, DX, DY))
        return t

    def _build(self, reset_acc: bool):
        """Solid nodes and the boundary links from the sides and the obstacles (host)."""
        nx, ny, N = self.nx, self.ny, self.N
        dx = self.units.dx
        solid = np.zeros((nx, ny), bool)
        owner = np.full((nx, ny), -1, np.int64)
        for oid, ob in self._obstacles.items():
            m = self._shape_mask(ob.shape)
            owner[m & ~solid] = oid
            solid |= m
        self._solid = solid
        self._owner_node = owner
        px, py = self.periodic
        I, J = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
        fluid = ~solid
        recs = {k: [] for k in ("dir", "node", "type", "c1", "c2", "val", "nb", "owner", "dtype", "dval", "wx", "wy",
                                "lsd")}
        rho0 = 1.0
        for i in range(1, 9):
            ex, ey = int(EX[i]), int(EY[i])
            sx, sy = I - ex, J - ey
            outl, outr = (sx < 0), (sx >= nx)
            outb, outt = (sy < 0), (sy >= ny)
            if px:
                outl[:] = False
                outr[:] = False
            if py:
                outb[:] = False
                outt[:] = False
            outside = outl | outr | outb | outt
            sxw, syw = sx % nx, sy % ny
            src_solid = np.zeros((nx, ny), bool)
            src_solid[~outside] = solid[sxw[~outside], syw[~outside]]
            sel = fluid & (outside | src_solid)
            if not sel.any():
                continue
            ii, jj = I[sel], J[sel]
            node = ii * ny + jj
            n_l = len(node)
            # the next node along e_i (for interpolation and extrapolation): fluid and inside
            nxn, nyn = ii + ex, jj + ey
            inside_n = np.ones(n_l, bool)
            if not px:
                inside_n &= (nxn >= 0) & (nxn < nx)
            if not py:
                inside_n &= (nyn >= 0) & (nyn < ny)
            nxn, nyn = nxn % nx, nyn % ny
            nb_ok = inside_n & ~solid[nxn, nyn]
            nb = np.where(nb_ok, nxn * ny + nyn, -1)
            # wall point of the link (half-way)
            wx = (ii + 0.5 - 0.5 * ex) * dx
            wy = (jj + 0.5 - 0.5 * ey) * dx
            typ = np.zeros(n_l, np.int64)
            c1 = np.zeros(n_l)
            c2 = np.zeros(n_l)
            val = np.zeros(n_l)
            own = np.zeros(n_l, np.int64)
            dtyp = np.zeros(n_l, np.int64)
            dval = np.zeros(n_l)
            lsd = np.zeros(n_l, np.int64)
            o_side = outside[sel]
            # sides
            if o_side.any():
                cand = []
                for name, m_out in (("left", outl), ("right", outr), ("bottom", outb), ("top", outt)):
                    cand.append((name, m_out[sel]))
                best = np.full(n_l, 99)
                bname = np.full(n_l, -1)
                for k, (name, mo) in enumerate(cand):
                    pr = PRIORITY[self._sides[name].KIND]
                    take = mo & (pr < best)
                    best[take] = pr
                    bname[take] = k
                for k, (name, _) in enumerate(cand):
                    m = o_side & (bname == k)
                    if not m.any():
                        continue
                    side = self._sides[name]
                    own[m] = SIDE_CODE[name]
                    vertical = name in ("left", "right")  # the side's coordinate s is y
                    s = wy[m] if vertical else wx[m]
                    length = self.size[1] if vertical else self.size[0]
                    if isinstance(side, Wall):
                        typ[m] = T_BB
                        ut = side.velocity / self.units.c
                        uwx, uwy = (0.0, ut) if vertical else (ut, 0.0)
                        val[m] = 6 * W[i] * rho0 * (ex * uwx + ey * uwy)
                        dtyp[m] = D_BB
                    elif isinstance(side, Inlet):
                        typ[m] = T_IN
                        uwx, uwy = self._inlet_wall_velocity(side, name, s)
                        val[m] = 6 * W[i] * rho0 * (ex * uwx + ey * uwy)
                        # the ramp starts from the velocity the side had when this inlet was set (zero after a
                        # wall; a blend of the earlier inlets otherwise): the link's value then is c1 (1 - s) + val s
                        frm = 0.0
                        for old, wgt in self._ramps.get(name, {}).get("from", ()):
                            ox, oy = self._inlet_wall_velocity(old, name, s)
                            frm = frm + wgt * (6 * W[i] * rho0 * (ex * ox + ey * oy))
                        c1[m] = frm
                        lsd[m] = SIDES.index(name)
                        dtyp[m] = D_IN
                        dval[m] = 2 * WG[i] * side.dye_at(s) if i <= 4 else 0.0
                    elif isinstance(side, Outlet):
                        typ[m] = T_ABB
                        val[m] = 2 * W[i] * self._outlet_density(name, side, s)
                        dtyp[m] = D_OUT
            # obstacles
            ob_l = ~o_side
            if ob_l.any():
                si, sj = sxw[sel][ob_l], syw[sel][ob_l]
                own[ob_l] = owner[si, sj]
                typ[ob_l] = T_BB
                dtyp[ob_l] = D_BB
                idx = np.flatnonzero(ob_l)
                for oid in np.unique(own[ob_l]):
                    ob = self._obstacles[int(oid)]
                    k = idx[own[idx] == oid]
                    if ob.moving:
                        c = self._center(ob)
                        uwx, uwy = ob.surface_velocity(wx[k], wy[k], c)
                        val[k] = 6 * W[i] * rho0 * (ex * np.asarray(uwx) + ey * np.asarray(uwy)) / self.units.c
                    elif ob.interpolated and ob.shape.analytic:
                        X0 = (ii[k] + 0.5) * dx
                        Y0 = (jj[k] + 0.5) * dx
                        q = self._hit(ob.shape, X0, Y0, -ex * dx * np.ones(len(k)), -ey * dx * np.ones(len(k)))
                        q = np.where(np.isfinite(q) & (q > 0) & (q <= 1.0), q, 0.5)
                        near = (q < 0.5) & (nb[k] >= 0)
                        far = q >= 0.5
                        kn, kf = k[near], k[far]
                        typ[kn] = T_BZN
                        c1[kn] = 2 * q[near]
                        c2[kn] = 1 - 2 * q[near]
                        typ[kf] = T_BZF
                        c1[kf] = 1 / (2 * q[far])
                        c2[kf] = (2 * q[far] - 1) / (2 * q[far])
                        wx[k] = X0 - q * ex * dx
                        wy[k] = Y0 - q * ey * dx
            for key, arr in (("dir", np.full(n_l, i)), ("node", node), ("type", typ), ("c1", c1), ("c2", c2),
                             ("val", val), ("nb", nb), ("owner", own), ("dtype", dtyp), ("dval", dval),
                             ("wx", wx), ("wy", wy), ("lsd", lsd)):
                recs[key].append(arr)
        L = {k: (np.concatenate(v) if v else np.zeros(0, np.int64 if k in ("dir", "node", "type", "nb", "owner",
                                                                           "dtype", "lsd") else float))
             for k, v in recs.items()}
        L["n"] = len(L["node"])
        L["opp"] = OPP[L["dir"]]
        L["groups"] = {t: np.flatnonzero(L["type"] == t) for t in (T_BB, T_IN, T_BZN, T_BZF, T_ABB)}
        L["dgroups"] = {t: np.flatnonzero((L["dtype"] == t) & (L["dir"] <= 4)) for t in (D_BB, D_IN, D_OUT)}
        L["nb_safe"] = np.where(L["nb"] >= 0, L["nb"], L["node"])
        if reset_acc or not hasattr(self, "_L"):
            for k in LINK_ACC:
                L[k] = np.zeros(L["n"])
        self._L = L
        flags = np.zeros(N, np.uint8)
        flags[solid.ravel()] |= 1
        flags[L["node"]] |= 2
        src = np.zeros((nx, ny), bool)
        csrc = np.zeros(N)
        for so in self._sources.values():
            m = self._shape_mask(so.shape) & ~solid
            src |= m
            csrc[m.ravel()] = so.concentration
        self._src_mask = src.ravel()
        self._src_idx = np.flatnonzero(self._src_mask)
        flags[self._src_idx] |= 4
        self._flags = flags
        self._csrc_host = csrc
        self._fluid_idx = np.flatnonzero(~solid.ravel())
        self._solid_idx = np.flatnonzero(solid.ravel())
        self._n_fluid = int(len(self._fluid_idx))
        slot = np.full((8, N), -1, np.int32)
        if L["n"]:
            slot[L["dir"] - 1, L["node"]] = np.arange(L["n"], dtype=np.int32)
        self._slot = slot
        self._dev = None  # device copies are rebuilt on demand

    def _bank(self):
        """Fold the per-link accumulators into the per-owner totals (before the links are rebuilt); the last step's
        sums are kept for ``forces`` until the next step."""
        L = self._L
        self._last_kept = (self._owner_sums("last"), self.steps)
        if not L["n"]:
            return
        for key, v in self._owner_sums("cum").items():
            if key.startswith("obstacle:"):
                self._banked_tq[key] = self._banked_tq.get(key, 0.0) + v[4]
            b = self._banked.setdefault(key, [0.0, 0.0, 0.0, 0.0])
            for q in range(4):
                b[q] += v[q]
        for k in LINK_ACC:
            self._L[k] = np.zeros(L["n"])
        if self._dev is not None:
            for k in LINK_ACC:
                self._dev[k].fill(0)

    def _owner_key(self, own: int) -> str:
        return SIDE_OF_CODE[own] if own < 0 else f"obstacle:{own}"

    # --- device -----------------------------------------------------------------------------------------------------
    def _footprint(self) -> int:
        return int(self.N * (2 * 9 * 8 + (2 * 5 * 8 if self._g is not None else 0) + 8 * 4 + 1 + 24) + self._L["n"] * 104)

    def _choose(self):
        """The device for the next steps (``backend.choose``: settings, crossover, free memory, the GPU's
        temperature); "gpu" takes GPU 0 whenever it is usable, below the crossover too."""
        force = "cpu" if self.device_mode == "cpu" else None
        size = self.N
        if self.device_mode == "gpu":
            cross = backend.settings()["crossover"].get(KERNEL, backend.kernels()[KERNEL].crossover)
            size = max(self.N, cross or 0)
        ch = backend.choose(KERNEL, size, footprint=self._footprint(), force=force,
                            why="выбрано для этого течения" if force else "")
        self._reason = ch.reason
        if ch.device != self.device:
            self._move(ch.device, ch.xp)

    def _drop_dev(self):
        """Copy the per-link accumulators from the device to the host and forget the device's copies of the tables
        (rebuilt at the next step)."""
        if self._dev is not None:
            n = self._L["n"]
            for k in LINK_ACC:
                self._L[k] = backend.to_numpy(self._dev[k])[:n].copy()
        self._dev = None

    def _move(self, device, xp):
        f, g = backend.to_numpy(self._f), None if self._g is None else backend.to_numpy(self._g)
        sacc = backend.to_numpy(self._src_acc)
        self._drop_dev()
        self.device, self._xp = device, xp
        if device == "gpu":
            self._f = xp.asarray(f)
            self._g = None if g is None else xp.asarray(g)
            self._src_acc = xp.asarray(sacc)
        else:
            self._f, self._g, self._src_acc = f, g, sacc
            backend.release()

    def _device_arrays(self):
        if self._dev is not None:
            return self._dev
        cp = self._xp
        L = self._L
        d = {"flags": cp.asarray(self._flags), "slot": cp.asarray(self._slot),
             "ltype": cp.asarray(L["type"].astype(np.int8)), "dtype": cp.asarray(L["dtype"].astype(np.int8)),
             "lsd": cp.asarray(L["lsd"].astype(np.int8)), "lc1": cp.asarray(L["c1"]), "lc2": cp.asarray(L["c2"]), "lval": cp.asarray(L["val"]),
             "dval": cp.asarray(L["dval"]), "lnb": cp.asarray(L["nb"].astype(np.int32)),
             "csrc": cp.asarray(self._csrc_host), "prm": cp.asarray(self._prm_host)}
        for k in LINK_ACC:
            d[k] = cp.asarray(L[k])
        if L["n"] == 0:  # CUDA wants valid pointers
            for k in ("ltype", "dtype", "lsd"):
                d[k] = cp.zeros(1, cp.int8)
            for k in ("lc1", "lc2", "lval", "dval", *LINK_ACC):
                d[k] = cp.zeros(1)
            d["lnb"] = cp.zeros(1, cp.int32)
        d["fn"] = cp.empty_like(self._f)
        d["gn"] = cp.empty_like(self._g) if self._g is not None else cp.zeros(1)
        d["g_dummy"] = cp.zeros(1)
        self._dev = d
        return d

    def _link_acc(self) -> dict:
        if self._dev is not None and self.device == "gpu":
            n = self._L["n"]
            return {k: backend.to_numpy(self._dev[k])[:n] for k in LINK_ACC}
        return {k: self._L[k] for k in LINK_ACC}

    # --- stepping ---------------------------------------------------------------------------------------------------
    def _inlet_scales(self, step: int) -> tuple:
        """The ramp of every side's inlet at the end of step ``step`` (left, right, bottom, top): sin^2(pi x / 2) of the
        fraction x of its own ramp elapsed since its velocity was set (1 after it, and for a side without a ramp)."""
        out = [1.0, 1.0, 1.0, 1.0]
        for k, name in enumerate(SIDES):
            rec = self._ramps.get(name)
            if rec is not None and rec["ramp"] > 0:
                x = (step - rec["s0"]) * self.units.dt / rec["ramp"]
                out[k] = 1.0 if x >= 1.0 else float(math.sin(0.5 * math.pi * max(x, 0.0)) ** 2)
        return tuple(out)

    def inlet_scales(self) -> dict:
        """{side: the ramp's value now (0 ... 1)} for every side with an inlet."""
        sc = self._inlet_scales(self.steps)
        return {name: sc[k] for k, name in enumerate(SIDES) if isinstance(self._sides[name], Inlet)}

    def _ramp_after(self, name: str, old: Side, new: Side):
        """The ramp record of side ``name`` after its condition changes from ``old`` to ``new`` now: none for a side
        that is not an inlet; unchanged when the inlet's velocity is unchanged (an edit of its dye or of its ramp time
        does not restart the inflow, review B7 L1); else a new ramp of the new inlet's duration that starts from the
        velocity the side has now (zero after a wall; the old inlet at its present ramp, which may itself blend)."""
        if not isinstance(new, Inlet):
            return None
        rec = self._ramps.get(name)
        if isinstance(old, Inlet) and rec is not None and _same_velocity(old, new):
            return rec
        frm = []
        if isinstance(old, Inlet) and new.ramp > 0:
            s = self._inlet_scales(self.steps)[SIDES.index(name)]
            if rec is None or s >= 1.0:
                frm = [(old, 1.0)]
            else:
                frm = [(i, w * (1.0 - s)) for i, w in rec["from"] if w * (1.0 - s) != 0.0]
                if s > 0.0:
                    frm.append((old, s))
        return {"s0": self.steps, "ramp": new.ramp, "from": frm}

    def _step_cpu(self, s_in: tuple):
        fin, gin = self._stream_cpu(s_in)
        self._collide_cpu(fin, gin)

    def _stream_cpu(self, s_in: tuple):
        """The streaming half of a step on the host: the populations pulled along their links and the boundary
        links' rules applied (their exchanges booked); returns the pre-collision populations (and the dye's)."""
        f = self._f
        fin = np.empty_like(f, order="C")  # C order: the link rules write through reshape views
        for i in range(9):
            _pull(fin[i], f[i], int(EX[i]), int(EY[i]))
        L = self._L
        hFx, hFy = 0.5 * self._F[0], 0.5 * self._F[1]
        if L["n"]:
            ff, fs = fin.reshape(9, -1), f.reshape(9, -1)
            d, nd, o = L["dir"], L["node"], L["opp"]
            fo = fs[o, nd]
            v = np.empty_like(fo)
            g = L["groups"]
            k = g[T_BB]
            v[k] = fo[k] + L["val"][k]
            k = g[T_IN]
            if len(k):  # the ramp of each side blends from the velocity the side had (c1) to the inlet's (val)
                s = np.asarray(s_in, float)[L["lsd"][k]]
                v[k] = fo[k] + ((L["c1"][k] * (1.0 - s)) + (L["val"][k] * s))
            k = g[T_BZN]
            v[k] = L["c1"][k] * fo[k] + L["c2"][k] * fs[o[k], L["nb_safe"][k]]
            k = g[T_BZF]
            v[k] = L["c1"][k] * fo[k] + L["c2"][k] * fs[d[k], nd[k]]
            k = g[T_ABB]
            if len(k):
                p = fs[:, nd[k]]
                _, ux, uy = _moments_post(p, hFx, hFy)
                uwx, uwy = ux.copy(), uy.copy()
                hasn = L["nb"][k] >= 0
                if hasn.any():
                    q = fs[:, L["nb"][k][hasn]]
                    _, ux2, uy2 = _moments_post(q, hFx, hFy)
                    uwx[hasn] = ux[hasn] + 0.5 * (ux[hasn] - ux2)
                    uwy[hasn] = uy[hasn] + 0.5 * (uy[hasn] - uy2)
                eu = EX[d[k]].astype(float) * uwx + EY[d[k]].astype(float) * uwy
                v[k] = (-fo[k]) + L["val"][k] * ((1.0 + (4.5 * eu) * eu) - 1.5 * (uwx * uwx + uwy * uwy))
            ff[d, nd] = v
            dm = v - fo
            dpp = v + fo
            L["acc_m"], L["cmp_m"] = _kahan(L["acc_m"], L["cmp_m"], dm)
            L["acc_p"], L["cmp_p"] = _kahan(L["acc_p"], L["cmp_p"], dpp)
            L["last_m"] = dm
            L["last_p"] = dpp
        # the dye's streaming and its boundary links
        gin = None
        if self._g is not None:
            gs = self._g
            gin = np.empty_like(gs, order="C")
            for i in range(5):
                _pull(gin[i], gs[i], int(EX[i]), int(EY[i]))
            if L["n"]:
                gf, gsf = gin.reshape(5, -1), gs.reshape(5, -1)
                dg = L["dgroups"]
                allk = np.concatenate([dg[D_BB], dg[D_IN], dg[D_OUT]])
                if len(allk):
                    d, nd, o = L["dir"][allk], L["node"][allk], L["opp"][allk]
                    go = gsf[o, nd]
                    v = go.copy()
                    nb_in = len(dg[D_BB])
                    n_in = len(dg[D_IN])
                    sl_in = slice(nb_in, nb_in + n_in)
                    v[sl_in] = (-go[sl_in]) + L["dval"][dg[D_IN]]
                    sl_out = slice(nb_in + n_in, None)
                    v[sl_out] = gsf[d[sl_out], nd[sl_out]]
                    gf[d, nd] = v
                    L["acc_d"][allk], L["cmp_d"][allk] = _kahan(L["acc_d"][allk], L["cmp_d"][allk], v - go)
        return fin, gin

    def _collide_cpu(self, fin, gin):
        """The collision half of a step on the host (the grid's own relaxation rates, force and sources): the
        post-collision state from the pre-collision populations ``fin`` (and the dye's ``gin``)."""
        nx, ny = self.nx, self.ny
        # collision (and the dye's), by blocks of rows on threads: elementwise, so the same numbers in any split
        fnew = np.empty_like(fin, order="C")
        gnew = None if gin is None else np.empty_like(gin, order="C")
        ux = np.empty((nx, ny))
        uy = np.empty((nx, ny))
        blocks = _blocks(nx, ny)
        if len(blocks) == 1:
            self._collide(fin, fnew, gin, gnew, ux, uy, 0, nx)
        else:
            list(_pool().map(lambda ab: self._collide(fin, fnew, gin, gnew, ux, uy, ab[0], ab[1]), blocks))
        fnf = fnew.reshape(9, -1)
        if len(self._solid_idx):
            fnf[:, self._solid_idx] = WA[:, None]
        # dye
        if gin is not None:
            gnf = gnew.reshape(5, -1)
            if len(self._src_idx):
                k = self._src_idx
                Cs = self._csrc_host[k]
                uxs, uys = ux.reshape(-1)[k], uy.reshape(-1)[k]
                e = [WG[0] * Cs, (WG[1] * Cs) * (1.0 + 3.0 * uxs), (WG[2] * Cs) * (1.0 + 3.0 * uys),
                     (WG[3] * Cs) * (1.0 - 3.0 * uxs), (WG[4] * Cs) * (1.0 - 3.0 * uys)]
                h = gnf[:, k]
                self._src_acc[0, k], self._src_acc[1, k] = _kahan(
                    self._src_acc[0, k], self._src_acc[1, k],
                    ((((e[0] - h[0]) + (e[1] - h[1])) + (e[2] - h[2])) + (e[3] - h[3])) + (e[4] - h[4]))
                for i in range(5):
                    gnf[i, k] = e[i]
            if len(self._solid_idx):
                gnf[:, self._solid_idx] = 0.0
            self._g = gnew
        self._f = fnew

    def _collide(self, fin, fnew, gin, gnew, uxo, uyo, a, b):
        """TRT/BGK collision with Guo's force (and the dye's TRT) on the rows a:b; the same operations, in the same
        order, as the GPU kernel."""
        hFx, hFy = 0.5 * self._F[0], 0.5 * self._F[1]
        fi = fin[:, a:b]
        fo_ = fnew[:, a:b]
        with np.errstate(all="ignore"):
            rho = fi[0] + fi[1] + fi[2] + fi[3] + fi[4] + fi[5] + fi[6] + fi[7] + fi[8]
            jx = ((fi[1] + fi[5]) + fi[8]) - ((fi[3] + fi[6]) + fi[7])
            jy = ((fi[2] + fi[5]) + fi[6]) - ((fi[4] + fi[7]) + fi[8])
            ux = (jx + hFx) / rho
            uy = (jy + hFy) / rho
            usq = ux * ux + uy * uy
            omp, omm = self.om_p, self.om_m
            prm = self._prm_host
            force_on = self._F != (0.0, 0.0)
            if force_on:
                uF3 = 3.0 * (ux * prm[7] + uy * prm[8])
            for i, o in PAIRS:
                eu = ux if i == 1 else uy if i == 2 else (ux + uy) if i == 5 else (uy - ux)
                wr = W[i] * rho
                feqp = wr * ((1.0 + (4.5 * eu) * eu) - 1.5 * usq)
                feqm = wr * (3.0 * eu)
                dp = omp * (0.5 * (fi[i] + fi[o]) - feqp)
                dmm = omm * (0.5 * (fi[i] - fi[o]) - feqm)
                ni = (fi[i] - dp) - dmm
                no = (fi[o] - dp) + dmm
                if force_on:
                    Fp = prm[10 + i] * ((9.0 * eu) * prm[30 + i] - uF3)
                    ni = ni + (Fp + prm[20 + i])
                    no = no + (Fp - prm[20 + i])
                fo_[i] = ni
                fo_[o] = no
            # the rest population closes the node's mass (the TRT value up to rounding; an unbiased rounding instead
            # of the formula's systematic one: 1e-13 of the mass per 1500 steps before)
            fo_[0] = rho - (((((((fo_[1] + fo_[2]) + fo_[3]) + fo_[4]) + fo_[5]) + fo_[6]) + fo_[7]) + fo_[8])
            uxo[a:b] = ux
            uyo[a:b] = uy
            if gin is not None:
                gi = gin[:, a:b]
                gn = gnew[:, a:b]
                C = (((gi[0] + gi[1]) + gi[2]) + gi[3]) + gi[4]
                ogp, ogm = 1 / self.tau_gp, 1 / self.tau_gm
                for i, o, eu in ((1, 3, ux), (2, 4, uy)):
                    wc = WG[i] * C
                    geqm = wc * (3.0 * eu)
                    dp = ogp * (0.5 * (gi[i] + gi[o]) - wc)
                    dmm = ogm * (0.5 * (gi[i] - gi[o]) - geqm)
                    gn[i] = (gi[i] - dp) - dmm
                    gn[o] = (gi[o] - dp) + dmm
                gn[0] = C - (((gn[1] + gn[2]) + gn[3]) + gn[4])

    def _step_gpu(self, s_in: list, n: int):
        cp = self._xp
        step, _ = _gpu_kernels(cp)
        d = self._device_arrays()
        prm = self._prm_host.copy()
        dye_on = np.int32(1 if self._g is not None else 0)
        force_on = np.int32(1 if self._F != (0.0, 0.0) else 0)
        block = 256
        grid = ((self.N + block - 1) // block,)
        for k in range(n):
            s = s_in[k]
            if tuple(prm[40:44]) != s:
                prm[40:44] = s
                d["prm"].set(prm)
            g_in = self._g if self._g is not None else d["g_dummy"]
            step(grid, (block,), (self._f, d["fn"], g_in, d["gn"], d["flags"], d["slot"], d["ltype"], d["dtype"],
                                  d["lsd"], d["lc1"], d["lc2"], d["lval"], d["dval"], d["lnb"], d["acc_m"], d["acc_p"],
                                  d["last_m"], d["last_p"], d["acc_d"], d["csrc"], self._src_acc,
                                  d["cmp_m"], d["cmp_p"], d["cmp_d"], d["prm"],
                                  np.int32(self.nx), np.int32(self.ny), dye_on, force_on))
            self._f, d["fn"] = d["fn"], self._f
            if self._g is not None:
                self._g, d["gn"] = d["gn"], self._g

    def advance(self, n: int = 1):
        """n steps of dt. Every chunk of steps is checked (a non-finite population or one beyond ``F_GUARD``: a
        blow-up); then the state at the call is restored and ``Unstable`` raised with the numbers of the last state
        that passed the check."""
        n = int(n)
        if n <= 0:
            return self
        self._choose()
        t0 = time.perf_counter()
        backup = self._snapshot()
        chunk = max(1, min(n, 64))
        done = 0
        last_good = None
        while done < n:
            m = min(chunk, n - done)
            if self._rec is not None:  # a block of the force record ends at its step exactly
                m = min(m, self._rec["next"] - self.steps)
            # each step's ramp from its number alone (the same however the steps are split into calls)
            s_in = [self._inlet_scales(self.steps + k + 1) for k in range(m)]
            try:
                if self.device == "gpu":
                    self._step_gpu(s_in, m)
                else:
                    for k in range(m):
                        self._step_cpu(s_in[k])
            except Exception as e:
                if self.device == "gpu" and backend.is_out_of_memory(e):
                    self._restore(backup)
                    self._move("cpu", np)
                    self.device_mode = "cpu"
                    return self.advance(n)
                raise
            self._add_impulse(m)
            self.steps += m
            self.t = self._t0 + self.steps * self.units.dt
            done += m
            if not self._healthy():
                bad_t = self.t
                if last_good is not None:
                    self._restore(last_good)
                else:
                    self._restore(backup)
                nums = self.numbers()
                at = self.t
                self._restore(backup)
                imposed = self._imposed_note()
                raise Unstable(f"счёт неустойчив к t = {bad_t:.6g} с (популяции нечисловые или вне |f| < {F_GUARD}); "
                               f"последнее здоровое состояние (t = {at:.6g} с): Ma_max = {nums['mach_max']:.3g}, τ+ = "
                               f"{self.tau_p:.4g}, Re ячейки = {nums['re_cell']:.3g} (предел {self.re_cell_limit():g})"
                               + (f"; заданы {imposed}" if imposed else "")
                               + f"; состояние восстановлено на начало вызова (t = {self.t:.6g} с). Уменьшите скорость "
                               f"или dx, увеличьте вязкость" + (", уменьшите заданное давление или силу" if imposed
                                                                else ""))
            if self._rec is not None and self.steps == self._rec["next"]:
                self._rec_sample()
            if done < n:
                last_good = self._snapshot()
        if self.device == "gpu":
            self._xp.cuda.Device(0).synchronize()
        self._timing["steps"] += n
        self._timing["seconds"] += time.perf_counter() - t0
        return self

    def _add_impulse(self, m: int):
        """Book the body force's impulse of ``m`` steps (compensated: a plain running sum's rounding grows with it)."""
        nf = self._n_fluid
        b = self._body_imp
        b[0], b[2] = _kahan(b[0], b[2], self._F[0] * nf * m)
        b[1], b[3] = _kahan(b[1], b[3], self._F[1] * nf * m)

    def _healthy(self) -> bool:
        xp = self._xp
        ok = bool(xp.abs(self._f).max() < F_GUARD)  # NaN compares False
        if ok and self._g is not None:
            ok = bool(xp.isfinite(self._g).all())
        return ok

    def _snapshot(self):
        return (self._f.copy(), None if self._g is None else self._g.copy(), self._src_acc.copy(),
                {k: v.copy() for k, v in self._link_acc().items()}, self.t, self.steps, list(self._body_imp),
                _rec_copy(self._rec))

    def _restore(self, b):
        f, g, sacc, acc, t, steps, imp, rec = b
        self._f, self._g, self._src_acc = f, g, sacc
        if self._dev is not None:
            for k, v in acc.items():
                self._dev[k][: len(v)] = self._xp.asarray(v)
        else:
            for k, v in acc.items():
                self._L[k] = v
        self.t, self.steps, self._body_imp = t, steps, list(imp)
        self._rec = _rec_copy(rec)

    def _imposed_note(self) -> str:
        """The imposed outlet pressures and body force, for the blow-up message (review B7 L7)."""
        out = []
        for name, s in self._sides.items():
            if isinstance(s, Outlet) and s.pressure != 0.0:
                out.append(f"давление на выходе ({name}) {s.pressure:g} Па — плотность решётки "
                           f"{float(self.units.density_of_pressure(s.pressure)):.4g}")
        if self.gravity != (0.0, 0.0):
            out.append(f"объёмная сила ({self.gravity[0]:g}, {self.gravity[1]:g}) м/с² — гидростатический перепад "
                       f"плотности {self.hydrostatic_spread():.3g}")
        return "; ".join(out)

    def advance_to(self, t: float):
        """Advance to the step nearest to time t (s)."""
        n = int(round((t - self.t) / self.units.dt))
        return self.advance(n)

    # --- edits ------------------------------------------------------------------------------------------------------
    def _host_state(self):
        return backend.to_numpy(self._f).copy(), None if self._g is None else backend.to_numpy(self._g).copy()

    def _put_state(self, f, g):
        xp = self._xp
        self._f = xp.asarray(f) if self.device == "gpu" else f
        if g is not None:
            self._g = xp.asarray(g) if self.device == "gpu" else g

    def _regeometry(self, change):
        """Apply a geometry change (a callable editing obstacles, dye sources or sides) with the bookkeeping of mass,
        momentum and dye; all or nothing (a refused change leaves the flow as it was)."""
        saved = (dict(self._obstacles), dict(self._sources), dict(self._sides), self._next_id, self._next_src,
                 dict(self._ramps), self.gravity)
        sig = self._flow_signature()
        old_solid = self._solid.copy()
        old_fluid = self._fluid_idx
        self._drop_dev()
        self._bank()  # with the links as they are (a refused change loses nothing: the totals are kept)
        try:
            change()
            self._check_sides(self._sides)
            self._check_numbers(self.nu, self.u_max)
        except Exception:
            (self._obstacles, self._sources, self._sides, self._next_id, self._next_src, self._ramps,
             self.gravity) = saved
            raise
        self._relax()
        f, g = self._host_state()
        sacc = backend.to_numpy(self._src_acc).copy()
        before = _sums(f, g, old_fluid)
        self._build(reset_acc=True)
        new_solid = self._solid
        became_solid = np.flatnonzero((new_solid & ~old_solid).ravel())
        became_fluid_m = (~new_solid & old_solid)
        became_fluid = np.flatnonzero(became_fluid_m.ravel())
        ff = f.reshape(9, -1)
        if len(became_solid):
            ff[:, became_solid] = WA[:, None]
            if g is not None:
                g.reshape(5, -1)[:, became_solid] = 0.0
        if len(became_fluid):
            k = became_fluid
            rho_all = (ff[0] + ff[1] + ff[2] + ff[3] + ff[4] + ff[5] + ff[6] + ff[7] + ff[8]).reshape(self.nx, self.ny)
            fl = ~new_solid & ~became_fluid_m
            I, J = np.unravel_index(k, (self.nx, self.ny))
            acc_r = np.zeros(len(k))
            cnt = np.zeros(len(k))
            px, py = self.periodic
            for a in (-1, 0, 1):
                for c in (-1, 0, 1):
                    if a == 0 and c == 0:
                        continue
                    ii, jj = I + a, J + c
                    ok = np.ones(len(k), bool)
                    if not px:
                        ok &= (ii >= 0) & (ii < self.nx)
                    if not py:
                        ok &= (jj >= 0) & (jj < self.ny)
                    ii, jj = ii % self.nx, jj % self.ny
                    use = ok & fl[ii, jj]
                    acc_r[use] += rho_all[ii[use], jj[use]]
                    cnt[use] += 1
            mean_all = float(np.mean(rho_all[fl])) if fl.any() else 1.0
            r = np.where(cnt > 0, acc_r / np.maximum(cnt, 1), mean_all)
            ux = np.zeros(len(k))
            uy = np.zeros(len(k))
            for oid, ob in saved[0].items():  # the moving surfaces that left these nodes: their velocity
                if ob.moving and (oid not in self._obstacles or self._obstacles[oid].shape is not ob.shape):
                    m = self._shape_mask(ob.shape).ravel()[k]
                    vx, vy = ob.surface_velocity(self._X.ravel()[k], self._Y.ravel()[k], self._center(ob))
                    ux = np.where(m, np.asarray(vx) / self.units.c, ux)
                    uy = np.where(m, np.asarray(vy) / self.units.c, uy)
            ff[:, k] = _equilibrium(r, ux, uy)
        if self.displaced == "spread" and (len(became_solid) or len(became_fluid)):
            fl_idx = self._fluid_idx
            mid = _sums(f, None, fl_idx)
            ff[:, fl_idx] *= before[0] / mid[0]
        after = _sums(f, g, self._fluid_idx)
        b = self._banked.setdefault("geometry", [0.0, 0.0, 0.0, 0.0])
        for q in range(4):
            b[q] += after[q] - before[q]
        self._put_state(f, g)
        self._src_acc = self._xp.asarray(sacc) if self.device == "gpu" else sacc
        if self._rec is not None and self._flow_signature() != sig:
            self._rec_restart()

    def _flow_signature(self):
        """What the flow depends on among the editable things: the obstacles' shapes, surface motions and wall kinds,
        the sides (an inlet by its velocity and its ramp), the body force; not labels, coefficient lengths, the dye."""
        def shape_sig(sh):
            return ("mask", id(sh)) if isinstance(sh, Mask) else repr(sh.params())

        def side_sig(name, sd):
            if isinstance(sd, Inlet):
                prof = sd.profile if isinstance(sd.profile, str) else id(sd.profile)
                rec = self._ramps.get(name) or {}
                return ("inlet", sd.velocity, prof, sd.tangential, rec.get("s0"), rec.get("ramp"))
            return repr(sd.params())
        return (tuple((oid, shape_sig(ob.shape), ob.velocity, ob.omega, ob.interpolated)
                      for oid, ob in sorted(self._obstacles.items())),
                tuple(side_sig(k, self._sides[k]) for k in SIDES), self.gravity)

    def add_obstacle(self, shape: Shape, velocity=(0.0, 0.0), omega: float = 0.0, interpolated: bool = False,
                     label: str = "", ref_length: float | None = None) -> int:
        """Add a solid obstacle now; returns its id. ``velocity`` (m/s) and ``omega`` (rad/s, about the shape's
        centre, counter-clockwise): the surface velocity on the fixed geometry (Ladd); ``interpolated``: Bouzidi's
        interpolated bounce-back on its links (analytic shapes, static surface only); ``ref_length``: the length of
        its drag and lift coefficients (default: its width across the flow)."""
        if not isinstance(shape, Shape):
            raise ValueError("препятствие: форма Disk, Rect, Polygon или Mask")
        oid = self._next_id

        def change():
            if isinstance(shape, Mask):
                shape.resolve(self._X, self._Y)
            ob = _Obstacle(oid, shape, velocity, omega, interpolated, label, ref_length)
            if ob.interpolated and ob.moving:
                raise ValueError("интерполированные стенки — только у неподвижной поверхности (подвижная — по Ладду)")
            self._obstacles[oid] = ob
            self._next_id = oid + 1
        self._regeometry(change)
        return oid

    def remove_obstacle(self, oid: int):
        if oid not in self._obstacles:
            raise KeyError(f"нет препятствия {oid}")
        self._regeometry(lambda: self._obstacles.pop(oid))

    def update_obstacle(self, oid: int, shape: Shape | None = None, velocity=None, omega=None, interpolated=None,
                        label=None, ref_length=None):
        """Change an obstacle now (a new shape moves it: nodes it leaves become fluid, nodes it covers solid). None
        keeps a value; ``ref_length=0`` returns the coefficients' length to the default (the width across the flow)."""
        if oid not in self._obstacles:
            raise KeyError(f"нет препятствия {oid}")
        old = self._obstacles[oid]

        def change():
            sh = old.shape if shape is None else shape
            if isinstance(sh, Mask):
                sh.resolve(self._X, self._Y)
            ob = _Obstacle(oid, sh, old.velocity if velocity is None else velocity,
                           old.omega if omega is None else omega,
                           old.interpolated if interpolated is None else interpolated,
                           old.label if label is None else label,
                           old.ref_length if ref_length is None else ref_length)
            if ob.interpolated and ob.moving:
                raise ValueError("интерполированные стенки — только у неподвижной поверхности (подвижная — по Ладду)")
            self._obstacles[oid] = ob
        self._regeometry(change)

    def obstacles(self) -> list[dict]:
        out = []
        for ob in self._obstacles.values():
            d = ob.params()
            d["nodes"] = int(np.sum(self._owner_node == ob.id))
            d["center"] = list(self._center(ob))
            d["span"] = self._span(ob)
            out.append(d)
        return out

    def set_side(self, name: str, side):
        """Change a side now: Wall(velocity), Inlet(...), Outlet(pressure), Periodic() (with its opposite side)."""
        if name not in SIDES:
            raise ValueError(f"сторона {name!r}: одна из {SIDES}")
        side = _as_side(side)

        def change():
            self._set_side_now(name, side)
        self._regeometry(change)

    def _set_side_now(self, name: str, side: Side):
        rec = self._ramp_after(name, self._sides[name], side)
        self._sides[name] = side
        ramps = dict(self._ramps)
        if rec is None:
            ramps.pop(name, None)
        else:
            ramps[name] = rec
        self._ramps = ramps

    def set_sides(self, sides: dict):
        """Change several sides at once (e.g. both of a periodic pair)."""
        new = {k: _as_side(v) for k, v in sides.items()}
        for k in new:
            if k not in SIDES:
                raise ValueError(f"сторона {k!r}: одна из {SIDES}")

        def change():
            for k, v in new.items():
                self._set_side_now(k, v)
        self._regeometry(change)

    def sides(self) -> dict:
        return {k: (v.params() if not (isinstance(v, Inlet) and (callable(v.profile) or callable(v.dye)))
                    else {"kind": "inlet", "velocity": v.velocity, "profile": "function"})
                for k, v in self._sides.items()}

    def set_gravity(self, gravity):
        """The uniform body force per unit mass (m/s^2), e.g. gravity or a pressure gradient G as -G/rho. Refused when
        the rest state it imposes deviates from rho0 by more than ``RHO_DEV_MAX`` (review B7 L6); the fluid takes the
        change of the hydrostatic pressure at once (``_hydrostatic_shift``) and the outlets its part along their sides
        (``_outlet_density``)."""
        g = (float(gravity[0]), float(gravity[1]))
        if not all(math.isfinite(v) for v in g):
            raise ValueError("объёмная сила: конечные числа")

        old = self.gravity

        def change():
            self.gravity = g
        self._regeometry(change)
        self._hydrostatic_shift(old, g)

    def set_viscosity(self, nu: float):
        """Change the viscosity now (tau changes; the time step stays)."""
        self._check_numbers(float(nu), self.u_max)
        self.nu = float(nu)
        self._relax()
        if self._dev is not None:
            self._dev["prm"].set(self._prm_host)
        if self._rec is not None:
            self._rec_restart()

    def set_density(self, rho: float):
        """Change the fluid's density now (review UX-ui U12): in the incompressible scheme the lattice state (density
        ratio, velocity) stays as it is and only the physical scale of mass, momentum, pressure and force changes with
        rho (``Units``): the flow goes on as before; the reported pressures and forces scale by rho_new / rho_old, the
        balances' relative residuals do not change; the force record restarts (its blocks would mix the two scales)."""
        rho = float(rho)
        if not (rho > 0 and math.isfinite(rho)):
            raise ValueError("плотность: конечное число > 0")
        self.units = Units(self.units.dx, self.units.dt, rho)
        if self._rec is not None:
            self._rec_restart()

    def set_collision(self, collision: str):
        """Switch the collision operator now, "trt" or "bgk" (review UX-ui U12): both relax towards the same
        equilibrium with the same tau+ (the viscosity), they differ in the odd moments' rate tau- (TRT: the magic
        Lambda; BGK: tau- = tau+); the populations are kept, the next step uses the new rates; the force record
        restarts."""
        if collision not in ("trt", "bgk"):
            raise ValueError("столкновения: 'trt' или 'bgk'")
        self.collision = collision
        self._relax()
        if self._dev is not None:
            self._dev["prm"].set(self._prm_host)
        if self._rec is not None:
            self._rec_restart()

    # --- the grid, the domain and the time step changed at the current moment (plan P16.1) -----------------------------
    def remap(self, dx: float | None = None, size=None, shift=(0.0, 0.0), u_max: float | None = None,
              dt: float | None = None, fill: str = "rest") -> dict:
        """Continue the flow on another grid, domain or time step from now (plan P16.1: "the populations regridded,
        the time step rescaled"); all or nothing (a refused or failed remap leaves the flow as it was).

        ``dx`` the new spacing (m); ``size`` (Lx, Ly) the new domain (m, rounded to whole cells of dx); ``shift``
        (sx, sy) where the present domain's origin lands in the new one (new coordinates = old + shift: a domain grown
        on the left by a has shift (a, 0)); the obstacles and dye sources move with the fluid (their coordinates
        change by the shift); ``u_max`` the largest expected speed, which sets the time step as when a flow is built
        (``Units.from_flow``: the lattice Mach number of u_max, capped at tau+ <= tau_max) — or ``dt`` explicitly; by
        default the flow's u_max (or, for a flow built with dt, the same tau: dt (dx'/dx)^2). ``fill``: the fluid of a
        part of the new domain that lies outside the present one — "rest" (at rest, the pressure of the nearest node
        of the present domain with the body force's hydrostatic part) or "inflow" (moving with the first inlet's
        velocity at its coordinate along the inlet's side; at rest without an inlet).

        The transfer (Dupuis & Chopard, Phys. Rev. E 67, 066707 (2003), as used for grid refinement: the rescaling of
        the non-equilibrium part applied to the PRE-collision populations, which avoids the singularity at tau = 1 of
        the post-collision rescaling of Filippova & Haenel, J. Comput. Phys. 147, 219 (1998); described in Lagrava's
        thesis, Univ. Geneva 2012, Eqs. (4.1), (4.10), (4.11), the right-hand side of (4.13), (4.14)-(4.15) — not
        (4.12) and the middle member of (4.13), where the ratio is printed inverted, alpha = dt_c tau_f / (dt_f tau_c),
        against (4.14)'s tau_f / (2 tau_c) at dt_f = dt_c / 2: a misprint, review LB1-physics P15; f^neq ~ tau dt as
        here, confirmed by the Poiseuille tests): the next step's streaming is done on the present grid
        (its boundary exchanges booked as in any step); its pre-collision populations are split into the equilibrium of
        their density and velocity and the non-equilibrium rest; the density (as the PHYSICAL pressure: the incompressible
        flow's pressure is kept, the lattice density deviation scales by (c/c')^2), the physical velocity and the
        non-equilibrium part are interpolated to the new nodes and the non-equilibrium part rescaled; the new grid's
        collision completes the step. The rescaling at first order of the Chapman-Enskog expansion: the symmetric part
        f+(1) = -tau+ (Q : grad u) w rho / c_s^2 ~ tau+ dt S (lattice gradients are dt times physical ones) is multiplied
        by tau+' dt' / (tau+ dt) (Dupuis & Chopard's tau_f dt_f / (tau_c dt_c)); the antisymmetric part of TRT, whose
        first order is -tau- [3 w e . d_t(rho u) + e . grad f+eq] ~ tau- dt^2/dx d(rho u u) (the pressure gradient
        cancels against d_t of the momentum), by tau-' dt'^2/dx' / (tau- dt^2/dx) — the same factor when dt ~ dx (their
        convective scaling), different in general (derived here, not in the sources); the force's half-step
        momentum -F/2 is taken out of the non-equilibrium part and put back in the new units. The dye (D2Q5): its
        antisymmetric non-equilibrium part, -tau_g- w e . grad C ~ tau_g- dx, by tau_g-' dx' / (tau_g- dx); the symmetric
        one ~ tau_g+ dt by tau_g+' dt' / (tau_g+ dt).

        Interpolation: the four-point (cubic Lagrange) interpolation in each axis where its whole 4 x 4 stencil is
        fluid (Lagrava's thesis, ch. 7, Conclusion: "a four-point symmetric cubic interpolation is mandatory, as it
        ensures that the method remains second order"; a second order one lost mass), bilinear elsewhere; beyond a non-periodic side two ghost layers: the velocity of a
        wall or inlet and the pressure of an outlet by a parabola through the wall's value half-way and the first two
        nodes, the other fields by the parabola through the first three nodes (a dye's at a wall or outlet by a mirror):
        a Poiseuille flow is transferred exactly; inside an obstacle the solid nodes next to the fluid take 2 u_w - the
        mean of their fluid neighbours (the wall half-way: linear; first order near curved or interpolated walls), the
        deeper ones the nearest such value. A grid shifted by whole cells at the same spacing is copied exactly (the
        cubic weights are 0 and 1). The obstacles and dye sources are re-voxelised on the new grid; nodes that become
        solid take the rest equilibrium.

        Books: everything booked so far is put into the new lattice units; the change of the totals by the transfer
        (interpolation, re-voxelisation, the density deviation of the kept pressure — p / c_s^2 changes with the
        scheme's sound speed when the time step does) is booked as "remap", so the balances' residuals stay round-off
        BY CONSTRUCTION: the running checks cannot see an error of the transfer itself (a velocity transferred 1 % wrong
        passes them; review LB1-physics P7). The transfer is checked against closed forms by the tests (Poiseuille
        exact across a refinement, a coarsening and a new time step, with negative controls; Taylor-Green at the
        scheme's accuracy; the dye's second moment) and, in a world, by a reference flow a wrong transfer breaks
        (p04's «Эталоны»). The step: the remap advances the flow by one step of the present grid
        (t + dt); the time origin, the inlets' ramps (a ramp's start may be a fraction of a step) and the force record
        are re-based on the new time step. Returns what changed: the mass, momentum and dye before and after (physical),
        the booked transfer, the grids, the time steps, the relaxation times.

        Refused: a domain that would cut an obstacle or a dye source, an obstacle or source given as a mask of nodes (on
        another grid or shifted), a new grid or time step outside the scheme's limits (the same refusals as a new flow:
        Mach, tau, the grid Reynolds number, the imposed densities)."""
        u0 = self.units
        dx1 = u0.dx if dx is None else float(dx)
        if not (math.isfinite(dx1) and dx1 > 0):
            raise ValueError("сетка: шаг dx — конечное число > 0")
        L1 = self.size if size is None else (float(size[0]), float(size[1]))
        if not all(math.isfinite(v) and v > 0 for v in L1):
            raise ValueError("область: длина и высота — конечные числа > 0")
        nx1, ny1 = int(round(L1[0] / dx1)), int(round(L1[1] / dx1))
        if nx1 < 2 or ny1 < 2:
            raise ValueError("область: не меньше 2 × 2 узлов")
        sx, sy = float(shift[0]), float(shift[1])
        if not (math.isfinite(sx) and math.isfinite(sy)):
            raise ValueError("сдвиг области: конечные числа")
        if fill not in ("rest", "inflow"):
            raise ValueError("новая часть области: 'rest' или 'inflow'")
        if u_max is not None and not (math.isfinite(float(u_max)) and float(u_max) > 0):
            raise ValueError("наибольшая ожидаемая скорость: конечное число > 0")
        um = self.u_max if u_max is None else float(u_max)
        if dt is not None:
            dt1 = float(dt)
            if not (math.isfinite(dt1) and dt1 > 0):
                raise ValueError("шаг по времени: конечное число > 0")
        elif um is not None:
            dt1 = Units.from_flow(dx1, self.nu, um, self.mach_target, u0.rho, self.tau_max).dt
        else:
            dt1 = u0.dt * (dx1 / u0.dx) ** 2
        same = (nx1, ny1) == (self.nx, self.ny) and dx1 == u0.dx and sx == 0.0 and sy == 0.0
        if not same:
            masks = [f"«{o.label}»" if o.label else f"№ {o.id}" for o in [*self._obstacles.values(),
                                                                          *self._sources.values()]
                     if isinstance(o.shape, Mask)]
            if masks:
                raise ValueError("тела или источники, заданные маской узлов, нельзя перенести на другую сетку или "
                                 "сдвинуть: " + ", ".join(masks))
            self._check_cut(nx1 * dx1, ny1 * dx1, sx, sy)
        saved = copy.deepcopy(self.__getstate__())
        try:
            return self._remap(nx1, ny1, Units(dx1, dt1, u0.rho), sx, sy, um, fill, same)
        except BaseException:
            self.__dict__.clear()
            self.__dict__.update(saved)
            self._xp, self._dev, self.device = np, None, "cpu"
            self._choose()
            raise

    def remap_memory_estimate(self, nx: int, ny: int) -> int:
        """Bytes a remap to an nx x ny grid holds at its peak: the new flow's (``memory_estimate``), the present state
        kept for all-or-nothing, the pre-collision populations and the interpolated fields of both grids. Per node of
        the present grid 1000 B with the dye (800 without), per node of the new one 1000 + 400 (800 + 300): the NumPy
        buffers' peak measured with tracemalloc (a channel with an inlet, an outlet, an interpolated disk and a dye
        source, 200 x 40 <-> 400 x 80) fits a N_old + b N_new with a = 723 / 603 B and b = 783 / 588 B (review
        LB1-physics P12: the former 500 / 380 B per present node fell short of a coarsening by 8-15 % [error in
        earlier]); the test holds the measured peak within 0.3-1 of this estimate."""
        dye = self._g is not None
        return int(self.memory_estimate(nx, ny, dye) + (1000 if dye else 800) * self.N
                   + (400 if dye else 300) * int(nx) * int(ny))

    def _check_cut(self, Lx1, Ly1, sx, sy):
        """A smaller or shifted domain must not cut an obstacle or a dye source: every cell of one inside the present
        domain stays inside the new one."""
        h = 0.5 * self.units.dx
        tol = 1e-9 * max(Lx1, Ly1, *self.size)
        for what, items in (("тело", self._obstacles.values()), ("источник красителя", self._sources.values())):
            for it in items:
                m = np.asarray(it.shape.contains(self._X, self._Y), bool)
                if not m.any():
                    continue
                X, Y = self._X[m] + sx, self._Y[m] + sy
                if X.min() - h < -tol or X.max() + h > Lx1 + tol or Y.min() - h < -tol or Y.max() + h > Ly1 + tol:
                    lab = f"«{it.label}»" if it.label else f"№ {it.id}"
                    raise ValueError(f"{what} {lab} оказалось бы срезано краем новой области: уменьшать область можно "
                                     f"только там, где нет тел и источников красителя")

    def _inlet_now(self, name: str, s, step: int):
        """The velocity (lattice units, the present ones) an inlet imposes at the points ``s`` (m) of its side at step
        ``step``: its own, blended with the side's former velocity while its ramp runs (as its links do)."""
        side = self._sides[name]
        ux, uy = self._inlet_wall_velocity(side, name, s)
        sk = self._inlet_scales(step)[SIDES.index(name)]
        if sk < 1.0:
            fx, fy = np.zeros_like(ux), np.zeros_like(uy)
            for old, wgt in self._ramps.get(name, {}).get("from", ()):
                ox, oy = self._inlet_wall_velocity(old, name, s)
                fx, fy = fx + wgt * ox, fy + wgt * oy
            ux, uy = fx * (1.0 - sk) + ux * sk, fy * (1.0 - sk) + uy * sk
        return np.asarray(ux, float), np.asarray(uy, float)

    def _ghost_rules(self, step):
        """For each side: the rule and the wall's values of every field group at the points along it (``_pad``)."""
        c, dx = self.units.c, self.units.dx
        px = (np.arange(self.nx + 2 * REMAP_PAD) - REMAP_PAD + 0.5) * dx  # the x of the columns padded first

        def rules(name):
            side = self._sides[name]
            s = self.y if name in ("left", "right") else px
            if isinstance(side, Periodic):
                return None
            r = {"p": ("E", None), "neq": ("E", None), "gneq": ("E", None), "C": ("N", None)}
            if isinstance(side, Wall):
                v = np.full_like(s, side.velocity)
                z = np.zeros_like(s)
                r["u"] = ("D", np.stack([z, v]) if name in ("left", "right") else np.stack([v, z]))
            elif isinstance(side, Inlet):
                ux, uy = self._inlet_now(name, s, step)
                r["u"] = ("D", np.stack([ux * c, uy * c]))
                r["C"] = ("D", side.dye_at(s)[None])
            else:  # an outlet: its pressure (with the body force's hydrostatic part along it)
                r["u"] = ("E", None)
                r["p"] = ("D", np.asarray(self.units.pressure(self._outlet_density(name, side, s)), float)[None])
            return r
        return {name: rules(name) for name in SIDES}

    def _remap_fields(self, fields: dict, xq, yq, exact_q, step):
        """The fields of the present grid (``fields``: group -> (k, nx, ny), values at the fluid nodes) at the new nodes
        (old-frame coordinates ``xq`` x ``yq``, m): solid nodes filled (``_fill_solid``), two ghost layers beyond the
        sides (``_pad``), the four-point interpolation where its stencil is fluid and bilinear elsewhere. ``exact_q``:
        the fractional indices of the new nodes when they are old nodes exactly (a shift by whole cells), else None.
        Returns (group -> (k, mx, my), the nearest old node (i, j) of every new node)."""
        from scipy import sparse
        P = REMAP_PAD
        fluid = ~self._solid
        px, py = self.periodic
        wall = np.zeros((2, self.nx, self.ny))
        for ob in self._obstacles.values():
            if ob.moving:
                m = self._owner_node == ob.id
                vx, vy = ob.surface_velocity(self._X[m], self._Y[m], self._center(ob))
                wall[0][m], wall[1][m] = vx, vy
        rules = self._ghost_rules(step)
        good = self._pad(fluid.astype(float)[None], rules, "good")[0]
        if exact_q is not None:
            qx, qy = exact_q
        else:
            qx = xq / self.units.dx - 0.5 + P
            qy = yq / self.units.dx - 0.5 + P

        def mats(q, n):
            m = len(q)
            fl = np.floor(q)
            t = q - fl
            fl = fl.astype(np.int64)
            rows4 = np.repeat(np.arange(m), 4)
            cols4 = np.clip(fl[:, None] + np.arange(-1, 3)[None, :], 0, n - 1).ravel()
            wc = np.stack([-t * (t - 1) * (t - 2) / 6, (t + 1) * (t - 1) * (t - 2) / 2, -(t + 1) * t * (t - 2) / 2,
                           (t + 1) * t * (t - 1) / 6], 1).ravel()
            A = sparse.csr_matrix((wc, (rows4, cols4)), shape=(m, n))
            S = sparse.csr_matrix((np.ones(4 * m), (rows4, cols4)), shape=(m, n))
            rows2 = np.repeat(np.arange(m), 2)
            cols2 = np.clip(fl[:, None] + np.arange(0, 2)[None, :], 0, n - 1).ravel()
            B = sparse.csr_matrix((np.stack([1 - t, t], 1).ravel(), (rows2, cols2)), shape=(m, n))
            return A, B, S
        Ax, Bx, Sx = mats(qx, self.nx + 2 * P)
        Ay, By, Sy = mats(qy, self.ny + 2 * P)

        def apply(Mx, My, F):
            return np.ascontiguousarray(np.asarray(My @ np.asarray(Mx @ F).T).T)
        cubic = apply(Sx, Sy, 1.0 - good) < 0.5
        out = {}
        for g, V in fields.items():
            V = _fill_solid(V, fluid, px, py, wall if g == "u" else None)
            Vp = self._pad(V, rules, g)
            out[g] = np.stack([np.where(cubic, apply(Ax, Ay, Vp[k]), apply(Bx, By, Vp[k])) for k in range(len(Vp))])
        near = (np.clip(np.rint(qx - 0.5 - P + 0.5).astype(np.int64), 0, self.nx - 1),
                np.clip(np.rint(qy - 0.5 - P + 0.5).astype(np.int64), 0, self.ny - 1))
        return out, near

    def _pad(self, V, rules, group):
        """V (k, nx, ny) with ``REMAP_PAD`` layers beyond every side: wrapped along a periodic axis, else the ghosts
        of the side's rule for ``group`` (``_ghosts``; "good": a ghost counts as fluid when the three layers it is made
        from are). Along x first (the sides' values at the nodes' y), then along y (at the padded columns' x)."""
        P = REMAP_PAD
        for axis, (lo, hi) in ((1, ("left", "right")), (2, ("bottom", "top"))):
            n = V.shape[axis]
            shape = list(V.shape)
            shape[axis] = n + 2 * P
            out = np.empty(shape)

            def ix(i):
                idx = [slice(None)] * 3
                idx[axis] = i
                return tuple(idx)
            out[ix(slice(P, P + n))] = V
            if rules[lo] is None:  # periodic
                out[ix(slice(0, P))] = V[ix(slice(n - P, n))]
                out[ix(slice(n + P, n + 2 * P))] = V[ix(slice(0, P))]
            else:
                for name, layers, dest in ((lo, (0, 1, 2), (P - 1, P - 2)), (hi, (n - 1, n - 2, n - 3), (n + P, n + P + 1))):
                    v = [V[ix(k)] if 0 <= k < n and (k != layers[2] or n >= 3) else None for k in layers]
                    if group == "good":
                        gv = v[0] * v[1] * (v[2] if v[2] is not None else 1.0)
                        g1 = g2 = gv
                    else:
                        rule, w = rules[name][group]
                        if w is not None and axis == 1:
                            w = w[:, :] if w.ndim == 2 else w
                        g1, g2 = _ghosts(v[0], v[1], v[2], rule, w)
                    out[ix(dest[0])], out[ix(dest[1])] = g1, g2
            V = out
        return V

    def _remap(self, nx1, ny1, u1, sx, sy, um, fill, same):
        u0 = self.units
        if self.device != "cpu":
            self._move("cpu", np)
        self._drop_dev()
        M0, P0x, P0y, D0 = self._totals()
        dye = self._g is not None
        before = {"mass": M0 * u0.mass, "momentum": [P0x * u0.momentum, P0y * u0.momentum],
                  "dye": D0 * u0.dx ** 2 if dye else None, "nodes": [self.nx, self.ny], "dx": u0.dx, "dt": u0.dt,
                  "size": list(self.size), "tau_plus": self.tau_p, "t": self.t}
        step1 = self.steps + 1
        t1 = self._t0 + step1 * u0.dt
        tp0, tm0, tgp0, tgm0 = self.tau_p, self.tau_m, self.tau_gp, self.tau_gm
        hF0 = (0.5 * self._F[0], 0.5 * self._F[1])
        # 1. the next step's streaming on the present grid (its boundary exchanges booked as in any step)
        fin, gin = self._stream_cpu(self._inlet_scales(step1))
        Min = _sums(fin, gin, self._fluid_idx)
        # 2. its pre-collision state: density (as the pressure), velocity (physical), the non-equilibrium part with the
        # force's half-step momentum taken out (lattice units of the present grid)
        rho = fin.sum(axis=0)
        jx = ((fin[1] + fin[5]) + fin[8]) - ((fin[3] + fin[6]) + fin[7])
        jy = ((fin[2] + fin[5]) + fin[6]) - ((fin[4] + fin[7]) + fin[8])
        rho = np.where(self._solid, 1.0, rho)
        ux, uy = (jx + hF0[0]) / rho, (jy + hF0[1]) / rho
        neq = fin - _equilibrium(rho, ux, uy)
        for i in range(1, 9):
            neq[i] += 3.0 * W[i] * (EX[i] * hF0[0] + EY[i] * hF0[1])
        fields = {"p": np.asarray(u0.pressure(rho), float)[None], "u": np.stack([ux * u0.c, uy * u0.c]), "neq": neq}
        if dye:
            C = gin.sum(axis=0)
            geq = np.stack([WG[i] * C * (1.0 + 3.0 * (EX[i] * ux + EY[i] * uy)) for i in range(5)])
            fields["C"], fields["gneq"] = C[None], gin - geq
        # 3. to the new nodes (old-frame coordinates); which of them lie in the present domain
        x1 = (np.arange(nx1) + 0.5) * u1.dx
        y1 = (np.arange(ny1) + 0.5) * u1.dx
        xq, yq = x1 - sx, y1 - sy
        tol = 1e-9 * u0.dx
        inside = ((xq >= -tol) & (xq <= self.size[0] + tol))[:, None] & ((yq >= -tol) & (yq <= self.size[1] + tol))[None, :]
        if same:
            R = fields
            near = (np.arange(self.nx), np.arange(self.ny))
        else:
            kx, ky = sx / u0.dx, sy / u0.dx
            exact = None
            if u1.dx == u0.dx and kx == round(kx) and ky == round(ky):  # whole cells: the old nodes themselves
                exact = (np.arange(nx1) - round(kx) + float(REMAP_PAD), np.arange(ny1) - round(ky) + float(REMAP_PAD))
            R, near = self._remap_fields(fields, xq, yq, exact, step1)
        # the rest state of a new part: the pressure of the nearest node of the present domain and the body force's
        # hydrostatic part from it (along non-periodic axes)
        pf = _fill_solid(fields["p"], ~self._solid, *self.periodic)[0]
        p_near = pf[np.ix_(near[0], near[1])]
        xn = (near[0] + 0.5) * u0.dx + sx
        yn = (near[1] + 0.5) * u0.dx + sy
        gl = self._g_lattice()
        gphys = (0.0 if gl[0] == 0.0 else self.gravity[0], 0.0 if gl[1] == 0.0 else self.gravity[1])
        p_rest = p_near + u0.rho * (gphys[0] * (x1 - xn)[:, None] + gphys[1] * (y1 - yn)[None, :])
        # 4. the books so far, in the new units
        self._bank()
        last = self._last_kept[0]
        if dye:
            b = self._banked.setdefault("dye_sources", [0.0, 0.0, 0.0, 0.0])
            sa = backend.to_numpy(self._src_acc)
            b[3] += _ksum(sa[0], sa[1])
        self._rescale_books(u0, u1)
        kf, kr = u0.force / u1.force, (u0.mass / u0.dt) / (u1.mass / u1.dt)
        self._last_kept = ({k: (v[0] * kr, v[1] * kf, v[2] * kf, v[3] * (u0.dx / u1.dx) ** 2,
                                v[4] * kf * u0.dx / u1.dx) for k, v in last.items()}, step1)
        # 5. the new grid: units, nodes, the obstacles and sources moved with the fluid, the ramps and the time re-based
        dt_ratio = u0.dt / u1.dt
        self.units = u1
        if um is not None:
            self.u_max = float(um)
        self.nx, self.ny = nx1, ny1
        self.N = nx1 * ny1
        self.x, self.y = x1, y1
        self._X, self._Y = np.meshgrid(self.x, self.y, indexing="ij")
        self.size = (nx1 * u1.dx, ny1 * u1.dx)
        if sx != 0.0 or sy != 0.0:
            for o in [*self._obstacles.values(), *self._sources.values()]:
                o.shape = o.shape.shifted(sx, sy)
        if dt_ratio != 1.0:
            for rec in self._ramps.values():
                rec["s0"] = _step_number(step1 - (step1 - rec["s0"]) * dt_ratio)
        self._relax()
        self._check_numbers(self.nu, self.u_max)
        self._build(reset_acc=True)
        fluid1 = ~self._solid
        # 6. the pre-collision populations of the new grid
        rho1 = 1.0 + R["p"][0] / (CS2 * u1.rho * u1.c ** 2)
        ux1, uy1 = R["u"][0] / u1.c, R["u"][1] / u1.c
        kp = (self.tau_p * u1.dt) / (tp0 * u0.dt) if REMAP_NEQ_RESCALE else 1.0
        km = (self.tau_m * u1.dt ** 2 / u1.dx) / (tm0 * u0.dt ** 2 / u0.dx) if REMAP_NEQ_RESCALE else 1.0
        neq1 = np.empty_like(R["neq"])
        neq1[0] = kp * R["neq"][0]
        for i, o in PAIRS:
            sp, am = 0.5 * (R["neq"][i] + R["neq"][o]), 0.5 * (R["neq"][i] - R["neq"][o])
            neq1[i], neq1[o] = kp * sp + km * am, kp * sp - km * am
        out = ~inside
        filled = "rest"
        if out.any():
            rho1[out] = (1.0 + p_rest / (CS2 * u1.rho * u1.c ** 2))[out]
            neq1[:, out] = 0.0
            vx, vy = np.zeros((nx1, ny1)), np.zeros((nx1, ny1))
            if fill == "inflow":
                for name in SIDES:
                    if isinstance(self._sides[name], Inlet):
                        s = self._Y if name in ("left", "right") else self._X
                        vx, vy = self._inlet_now(name, s, step1)
                        filled = "inflow"
                        break
            ux1[out], uy1[out] = vx[out], vy[out]
        hF1 = (0.5 * self._F[0], 0.5 * self._F[1])
        fin1 = np.ascontiguousarray(_equilibrium(rho1, ux1, uy1) + neq1)
        for i in range(1, 9):
            fin1[i] -= 3.0 * W[i] * (EX[i] * hF1[0] + EY[i] * hF1[1])
        fin1[:, self._solid] = WA[:, None]
        gin1 = None
        if dye:
            C1 = np.where(out, 0.0, R["C"][0])
            kgp = (self.tau_gp * u1.dt) / (tgp0 * u0.dt) if REMAP_NEQ_RESCALE else 1.0
            kgm = (self.tau_gm * u1.dx) / (tgm0 * u0.dx) if REMAP_NEQ_RESCALE else 1.0
            gn = R["gneq"]
            gin1 = np.empty((5, nx1, ny1))
            gin1[0] = WG[0] * C1 + kgp * gn[0]
            for i, o in ((1, 3), (2, 4)):
                sp, am = 0.5 * (gn[i] + gn[o]), 0.5 * (gn[i] - gn[o])
                gin1[i] = WG[i] * C1 * (1.0 + 3.0 * (EX[i] * ux1 + EY[i] * uy1)) + kgp * sp + kgm * am
                gin1[o] = WG[o] * C1 * (1.0 + 3.0 * (EX[o] * ux1 + EY[o] * uy1)) + kgp * sp - kgm * am
            gin1[:, out] = np.where(out, 0.0, gin1)[:, out]
            gin1[:, self._solid] = 0.0
        # 7. the transfer's change of the totals, booked; the new grid's collision completes the step
        Mn = _sums(fin1, gin1, self._fluid_idx)
        k = (u0.mass / u1.mass, u0.momentum / u1.momentum, u0.momentum / u1.momentum, (u0.dx / u1.dx) ** 2)
        bk = self._banked.setdefault("remap", [0.0, 0.0, 0.0, 0.0])
        moved = [Mn[q] - Min[q] * k[q] for q in range(4)]
        for q in range(4):
            bk[q] += moved[q]
        self._src_acc = np.zeros((2, self.N))
        self._collide_cpu(fin1, gin1)
        self._add_impulse(1)
        self.steps = step1
        self.t = t1
        self._t0 = t1 - step1 * u1.dt
        self._timing = {"steps": 0, "seconds": 0.0}
        if self._rec is not None:
            self._rec_restart()
        if self._force_ref is not None:
            self.reset_force_mean()
        if not self._healthy():
            raise Unstable("после перестройки сетки популяции вышли за пределы здоровых: перестройка отменена")
        self._choose()
        M1, P1x, P1y, D1 = self._totals()
        return {"before": before,
                "after": {"mass": M1 * u1.mass, "momentum": [P1x * u1.momentum, P1y * u1.momentum],
                          "dye": D1 * u1.dx ** 2 if dye else None, "nodes": [nx1, ny1], "dx": u1.dx, "dt": u1.dt,
                          "size": list(self.size), "tau_plus": self.tau_p, "t": self.t},
                "transfer": {"mass": moved[0] * u1.mass, "momentum": [moved[1] * u1.momentum, moved[2] * u1.momentum],
                             "dye": moved[3] * u1.dx ** 2 if dye else None},
                "shift": [sx, sy], "fill": filled if out.any() else None, "new_part": float(np.mean(out)),
                "factors": {"neq_plus": kp, "neq_minus": km}}

    def _rescale_books(self, u0: Units, u1: Units):
        """Everything booked (the start's totals, the boundaries' and edits' books, the body force's impulse, the folded
        torques) from the lattice units ``u0`` into ``u1`` (the physical amounts unchanged)."""
        km, kp, kd = u0.mass / u1.mass, u0.momentum / u1.momentum, (u0.dx / u1.dx) ** 2
        M, Px, Py, D = self._ref
        self._ref = (M * km, Px * kp, Py * kp, D * kd)
        self._banked = {k: [v[0] * km, v[1] * kp, v[2] * kp, v[3] * kd] for k, v in self._banked.items()}
        self._banked_tq = {k: v * kp * u0.dx / u1.dx for k, v in self._banked_tq.items()}
        bi = self._body_imp
        self._body_imp = [(bi[0] - bi[2]) * kp, (bi[1] - bi[3]) * kp, 0.0, 0.0]

    def gravity_limit(self, direction=(0.0, -1.0), sides=None) -> float:
        """The largest |g| (m/s^2) along ``direction`` that the rest state can carry now (``_check_densities``: the
        hydrostatic density of the weakly compressible scheme within RHO_DEV_MAX of rho0, with the outlets' pressures),
        by bisection on the same test the refusal makes; inf when the direction lies along periodic axes only."""
        d = np.asarray(direction, float)
        d = d / np.hypot(*d)
        sides = sides or self._sides

        def ok(g):
            try:
                self._check_densities(sides, (float(g * d[0]), float(g * d[1])))
                return True
            except ValueError:
                return False
        if not ok(0.0):
            return 0.0
        hi = 1.0
        while ok(hi):
            hi *= 4.0
            if hi > 1e12:
                return math.inf
        lo = 0.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
        return lo

    def shape_mask(self, shape: Shape) -> np.ndarray:
        """The nodes (nx, ny) inside ``shape`` (its periodic images included): what it would make solid."""
        return self._shape_mask(shape)

    def solid(self) -> np.ndarray:
        """The solid nodes now (nx, ny)."""
        return np.array(self._solid, bool)

    @staticmethod
    def memory_estimate(nx: int, ny: int, dye: bool = True) -> int:
        """Bytes a flow of nx x ny nodes takes at its peak on the CPU (state, link tables, the step's temporaries and the
        fields read for a picture): measured 840 B per node with the dye and 632 without (1e6 nodes, a channel with an
        inlet, an outlet, a disk and a dye source; VmHWM after 5 steps, 2026-11-05), rounded up to 1000 / 800."""
        return int(int(nx) * int(ny) * (1000 if dye else 800))

    # --- dye --------------------------------------------------------------------------------------------------------
    def disable_dye(self):
        """Switch the dye off now (review UX-ui U12): its field goes; the amount in the domain is booked as removed
        ("dye_off"), so that the dye's balance closes again when it is switched on (``enable_dye``: zero dye). Refused
        while dye sources exist (remove them first)."""
        if self._g is None:
            return
        if self._sources:
            raise ValueError(f"краситель нельзя выключить, пока есть его источники ({len(self._sources)}): "
                             f"сначала уберите их")
        f, g = self._host_state()
        D = float(g.reshape(5, -1)[:, self._fluid_idx].sum())
        b = self._banked.setdefault("dye_off", [0.0, 0.0, 0.0, 0.0])
        b[3] -= D
        self._g = None
        self.dye_D = None
        self._drop_dev()
        self._relax()
        self._put_state(f, None)

    def enable_dye(self, diffusivity: float):
        """Switch the dye on (all zero) with ``diffusivity`` (m^2/s; raised to the scheme's floor if lower)."""
        self.dye_D = float(diffusivity)
        if self._g is None:
            g = np.zeros((5, self.nx, self.ny))
            self._g = self._xp.asarray(g) if self.device == "gpu" else g
        self._relax()
        self._drop_dev()

    def set_dye_diffusivity(self, diffusivity: float):
        if self._g is None:
            return self.enable_dye(diffusivity)
        self.dye_D = float(diffusivity)
        self._relax()
        if self._dev is not None:
            self._dev["prm"].set(self._prm_host)

    def add_dye(self, shape: Shape, concentration: float = 1.0, mode: str = "set"):
        """Put dye in a region now: ``mode`` "set" (the concentration becomes ``concentration``) or "add". The dye
        added is booked ("injected")."""
        if self._g is None:
            raise ValueError("краска выключена: enable_dye(диффузия)")
        m = (self._shape_mask(shape) & ~self._solid).ravel()
        f, g = self._host_state()
        gf = g.reshape(5, -1)
        k = np.flatnonzero(m)
        before = float(np.sum(gf[:, k]))
        r, ux, uy = _moments_post(f.reshape(9, -1)[:, k], 0.5 * self._F[0], 0.5 * self._F[1])
        C = gf[:, k].sum(axis=0)
        Cn = np.full(len(k), float(concentration)) if mode == "set" else C + float(concentration)
        for i in range(5):
            eu = EX[i] * ux + EY[i] * uy
            gf[i, k] = WG[i] * Cn * (1.0 + 3.0 * eu)
        b = self._banked.setdefault("injected", [0.0, 0.0, 0.0, 0.0])
        b[3] += float(np.sum(gf[:, k])) - before
        self._put_state(f, g)

    def clear_dye(self):
        if self._g is None:
            return
        f, g = self._host_state()
        b = self._banked.setdefault("injected", [0.0, 0.0, 0.0, 0.0])
        b[3] -= float(np.sum(g.reshape(5, -1)[:, self._fluid_idx]))
        g[...] = 0.0
        self._put_state(f, g)

    def add_dye_source(self, shape: Shape, concentration: float = 1.0, label: str = "") -> int:
        """A region where the dye is held at ``concentration`` (an ink pen); returns its id."""
        if self._g is None:
            raise ValueError("краска выключена: enable_dye(диффузия)")
        sid = self._next_src

        def change():
            if isinstance(shape, Mask):
                shape.resolve(self._X, self._Y)
            self._sources[sid] = _Source(sid, shape, concentration, label)
            self._next_src = sid + 1
        self._regeometry(change)
        return sid

    def remove_dye_source(self, sid: int):
        if sid not in self._sources:
            raise KeyError(f"нет источника {sid}")
        self._regeometry(lambda: self._sources.pop(sid))

    def dye_sources(self) -> list[dict]:
        return [s.params() for s in self._sources.values()]

    # --- the flow ---------------------------------------------------------------------------------------------------
    def set_flow(self, velocity=None, pressure=None):
        """Set the fluid to equilibrium with ``velocity`` ((ux, uy) in m/s: a pair of numbers, of arrays (nx, ny) or
        a function f(X, Y) -> (ux, uy)) and ``pressure`` (Pa relative to the reference; number, array or f(X, Y)).
        The balance starts again from this state."""
        X, Y = self._X, self._Y

        def ev(v, default):
            if v is None:
                return default
            if callable(v):
                return v(X, Y)
            return v
        uxy = ev(velocity, (0.0, 0.0))
        ux = np.broadcast_to(np.asarray(uxy[0], float), X.shape) / self.units.c
        uy = np.broadcast_to(np.asarray(uxy[1], float), X.shape) / self.units.c
        p = np.broadcast_to(np.asarray(ev(pressure, 0.0), float), X.shape)
        rho = np.asarray(self.units.density_of_pressure(p), float)
        # the stored state is post-collision, whose momentum is rho u + F/2: the equilibrium of u + F/(2 rho)
        f = _equilibrium(rho, ux + 0.5 * self._F[0] / rho, uy + 0.5 * self._F[1] / rho)
        f = np.array(f, float)
        f.reshape(9, -1)[:, self._solid_idx] = WA[:, None]
        g = None if self._g is None else backend.to_numpy(self._g).copy()
        self._drop_dev()
        self._put_state(f, g)
        self._L.update({k: np.zeros(self._L["n"]) for k in LINK_ACC})
        self._banked = {}
        self._src_acc = self._xp.zeros((2, self.N)) if self.device == "gpu" else np.zeros((2, self.N))
        self._body_imp = [0.0, 0.0, 0.0, 0.0]
        self._baseline()

    def adopt(self, other: "Flow2D") -> dict:
        """Continue ``other``'s fluid in this flow (a new world that keeps the flow of the previous one: plan P16.1,
        review LB1-framework F5): the same nodes, spacing and time step are required (``remap`` ``other`` first; refused
        otherwise with ValueError); the viscosity, the density scale, the sides, the obstacles, the dye sources and the
        body force are this flow's (a change of them acts as a change at this moment would: the lattice state is kept).
        The stored populations are copied where both flows are fluid; a node fluid here but solid there starts at rest
        at the mean density of the copied fluid; a solid node here takes the rest weights. The dye: copied when both
        carry it (zero here when only this one does). An inlet of this flow on a side where ``other`` has an inlet of the
        same velocity continues its ramp where it was (a ramp otherwise starts as an inlet added now does). This flow's
        time and step count stay; its books start here (the balance's start is the adopted state; the force record
        restarts). Returns {"copied": nodes copied, "rest": nodes started at rest, "dye": "copied" | "zero" | "none" |
        "dropped", "ramps": [sides whose ramp was continued]}."""
        if (other.nx, other.ny) != (self.nx, self.ny) or other.units.dx != self.units.dx \
                or not math.isclose(other.units.dt, self.units.dt, rel_tol=1e-12):
            raise ValueError(f"перенять течение можно только на той же сетке и с тем же шагом по времени: "
                             f"{other.nx} × {other.ny} (dx {other.units.dx:g} м, dt {other.units.dt:g} с) против "
                             f"{self.nx} × {self.ny} (dx {self.units.dx:g} м, dt {self.units.dt:g} с) — сначала remap")
        fo, go = other._host_state()
        both = ~self._solid & ~other.solid()
        fresh = ~self._solid & other.solid()
        f = np.empty_like(fo)
        f[:, both] = fo[:, both]
        rho_mean = float(fo[:, both].sum(axis=0).mean()) if both.any() else 1.0
        if fresh.any():
            r = np.full(int(fresh.sum()), rho_mean)
            z = np.zeros_like(r)
            f[:, fresh] = _equilibrium(r, z + 0.5 * self._F[0] / r, z + 0.5 * self._F[1] / r)
        f[:, self._solid] = WA[:, None]
        g, dye = None, "none"
        if self._g is not None:
            g = np.zeros((5, self.nx, self.ny))
            if go is not None:
                g[:, both] = go[:, both]
                dye = "copied"
            else:
                dye = "zero"
        elif go is not None:
            dye = "dropped"
        self._drop_dev()
        self._put_state(np.ascontiguousarray(f), None if g is None else np.ascontiguousarray(g))
        ramps = []
        for name, side in self._sides.items():
            old, rec = other._sides.get(name), other._ramps.get(name)
            if isinstance(side, Inlet) and isinstance(old, Inlet) and rec is not None and _same_velocity(old, side):
                self._ramps[name] = {"s0": _step_number(self.steps - (other.steps - rec["s0"])), "ramp": rec["ramp"],
                                     "from": list(rec["from"])}
                ramps.append(name)
        self._L.update({k: np.zeros(self._L["n"]) for k in LINK_ACC})
        self._banked = {}
        self._banked_tq = {}
        self._src_acc = self._xp.zeros((2, self.N)) if self.device == "gpu" else np.zeros((2, self.N))
        self._body_imp = [0.0, 0.0, 0.0, 0.0]
        if self._rec is not None:
            self._rec_restart()
        if self._force_ref is not None:
            self.reset_force_mean()
        self._baseline()
        if not self._healthy():
            raise Unstable("перенятое течение вне здоровых популяций")
        return {"copied": int(both.sum()), "rest": int(fresh.sum()), "dye": dye, "ramps": ramps}

    def _totals(self):
        """Mass, momentum (lattice) of the fluid and the dye's amount, from the stored state."""
        xp = self._xp
        f = self._f.reshape(9, -1)
        fl = self._fluid_idx if self.device == "cpu" else xp.asarray(self._fluid_idx)
        fs = f[:, fl]
        M = float(fs.sum())
        Px = float((fs[1] + fs[5] + fs[8] - fs[3] - fs[6] - fs[7]).sum())
        Py = float((fs[2] + fs[5] + fs[6] - fs[4] - fs[7] - fs[8]).sum())
        D = float(self._g.reshape(5, -1)[:, fl].sum()) if self._g is not None else 0.0
        return M, Px, Py, D

    def _baseline(self):
        self._ref = self._totals()
        self._ref_steps = self.steps

    # --- fields -----------------------------------------------------------------------------------------------------
    def _moments(self):
        xp = self._xp
        hFx, hFy = 0.5 * self._F[0], 0.5 * self._F[1]
        r, ux, uy = _moments_post(self._f, hFx, hFy)
        return r, ux, uy

    def fields(self) -> dict:
        """Density (kg/m^3), pressure (Pa, relative), velocity (m/s), as NumPy arrays (nx, ny); solid nodes NaN."""
        r, ux, uy = (backend.to_numpy(a) for a in self._moments())
        s = self._solid
        u = self.units
        out = {"rho": r * u.rho, "p": u.pressure(r), "ux": ux * u.c, "uy": uy * u.c}
        for k in out:
            out[k] = np.where(s, np.nan, out[k])
        return out

    def velocity(self):
        f = self.fields()
        return f["ux"], f["uy"]

    def pressure(self):
        return self.fields()["p"]

    def speed(self):
        ux, uy = self.velocity()
        return np.hypot(ux, uy)

    def vorticity(self) -> np.ndarray:
        """dv/dx - du/dy (1/s): centred differences; next to a solid node or a non-periodic edge one-sided."""
        ux, uy = self.velocity()
        dx = self.units.dx
        return _ddx(uy, self._solid, 0, self.periodic[0], dx) - _ddx(ux, self._solid, 1, self.periodic[1], dx)

    def dye(self) -> np.ndarray | None:
        if self._g is None:
            return None
        g = self._g
        C = backend.to_numpy((((g[0] + g[1]) + g[2]) + g[3]) + g[4])
        return np.where(self._solid, np.nan, C)

    def solid(self) -> np.ndarray:
        return self._solid.copy()

    def populations(self) -> np.ndarray:
        """The stored post-collision populations (9, nx, ny), lattice units (for tests and checks)."""
        return backend.to_numpy(self._f).copy()

    # --- forces -----------------------------------------------------------------------------------------------------
    def _owner_sums(self, which="last"):
        """{owner key: (mass, px, py, dye, torque)} of the per-link records: the last step or cumulative."""
        L = self._L
        acc = self._link_acc()
        out = {}
        if not L["n"]:
            return out
        ex, ey = EX[L["dir"]].astype(float), EY[L["dir"]].astype(float)
        last = which == "last"
        m = acc["last_m"] if last else acc["acc_m"]
        p = acc["last_p"] if last else acc["acc_p"]
        for own in np.unique(L["owner"]):
            k = L["owner"] == own
            key = self._owner_key(int(own))
            tq = 0.0
            if own >= 0:
                c = np.asarray(self._center(self._obstacles[int(own)])) / self.units.dx
                rx, ry = L["wx"][k] / self.units.dx - c[0], L["wy"][k] / self.units.dx - c[1]
                pk = p[k] if last else p[k] - acc["cmp_p"][k]
                tq = float(np.sum((rx * ey[k] - ry * ex[k]) * pk))
            if last:
                out[key] = (float(np.sum(m[k])), float(np.sum(ex[k] * p[k])), float(np.sum(ey[k] * p[k])), 0.0, tq)
            else:  # the compensated books summed exactly (e = -1, 0, 1: the products are exact), rounded once
                cp = acc["cmp_p"][k]
                out[key] = (_ksum(m[k], acc["cmp_m"][k]), _ksum(ex[k] * p[k], ex[k] * cp),
                            _ksum(ey[k] * p[k], ey[k] * cp), _ksum(acc["acc_d"][k], acc["cmp_d"][k]), tq)
        return out

    def forces(self, u_ref: float | None = None, direction=(1.0, 0.0)) -> dict:
        """Per obstacle {id: {"force": (Fx, Fy) N/m, "torque": N (per m of depth, about its centre), "drag", "lift"
        (N/m, along ``direction`` and 90 degrees counter-clockwise from it), "cd", "cl", "length", "mean": the same
        averaged since ``reset_force_mean``}}, by momentum exchange over the last step. cd = 2 drag / (rho u_ref^2 L),
        L the obstacle's width across ``direction`` (or its ref_length)."""
        u = self.units
        uref = u_ref if u_ref is not None else (self.u_ref if self.u_ref is not None else self._default_uref())
        d = np.asarray(direction, float) / np.hypot(*direction)
        nrm = np.array([-d[1], d[0]])
        last = self._owner_sums("last")
        kept = getattr(self, "_last_kept", None)
        if kept is not None and kept[1] == self.steps:  # edited since the last step: that step's record
            last = kept[0]
        cum = self._owner_sums("cum")
        out = {}
        for oid, ob in self._obstacles.items():
            key = f"obstacle:{oid}"
            Lr = self._span(ob, direction)

            def pack(v, steps):
                if v is None or steps <= 0:
                    return None
                F = -np.array([v[0], v[1]]) / steps * u.force
                tq = -v[2] / steps * u.force * u.dx
                drag, lift = float(F @ d), float(F @ nrm)
                q = 0.5 * u.rho * uref**2 * Lr if uref and Lr else float("nan")
                return {"force": F.tolist(), "torque": tq, "drag": drag, "lift": lift, "cd": drag / q, "cl": lift / q}
            lv = last.get(key)
            res = pack(None if lv is None else (lv[1], lv[2], lv[4]), 1) or {
                "force": [0.0, 0.0], "torque": 0.0, "drag": 0.0, "lift": 0.0, "cd": 0.0, "cl": 0.0}
            mean = None
            if self._force_ref is not None:
                ref, st = self._force_ref
                cv = cum.get(key, (0, 0, 0, 0, 0))
                rv = ref.get(key, (0, 0, 0, 0, 0))
                bk = self._banked.get(key, [0.0] * 4)
                rb = ref.get("_banked:" + key, [0.0] * 4)
                mean = pack((cv[1] - rv[1] + bk[1] - rb[1], cv[2] - rv[2] + bk[2] - rb[2], 0.0), self.steps - st)
                if mean is not None:
                    mean.pop("torque")
            res.update({"length": Lr, "u_ref": uref, "mean": mean})
            out[oid] = res
        return out

    def reset_force_mean(self):
        """Start averaging the forces from now (``forces()[id]["mean"]``)."""
        ref = dict(self._owner_sums("cum"))
        for k, v in self._banked.items():
            ref["_banked:" + k] = list(v)
        self._force_ref = (ref, self.steps)

    # --- the force record and the acoustic period ----------------------------------------------------------------------
    def record_forces(self, every: int | None, keep: int = 4096):
        """Record the force and torque on every obstacle as means over consecutive blocks of ``every`` steps (the
        blocks end at whole steps counted from now, however ``advance`` is called; None stops), keeping the last
        ``keep`` blocks (``force_record``). A change of what the flow depends on (obstacles' shapes, surface motions
        and wall kinds, the sides, the body force, the viscosity) restarts the record at that step: a block across the
        change would mix two flows. The means are momentum-exchange sums over whole blocks, so a mean over whole
        periods of a ringing (the scheme's sound, ``acoustic_period``) does not carry it."""
        if every is None:
            self._rec = None
            return
        every, keep = int(every), int(keep)
        if every < 1 or keep < 1:
            raise ValueError("запись сил: блок ≥ 1 шага, хранить ≥ 1 блока")
        self._rec = {"every": every, "keep": keep, "next": 0, "prev": {}, "since_step": 0, "t": [], "F": {}}
        self._rec_restart()

    def _rec_cum(self) -> dict:
        """{obstacle id: (px, py, torque)}: the momentum-exchange sums since the flow started (lattice; with what the
        edits folded)."""
        cum = self._owner_sums("cum")
        out = {}
        for oid in self._obstacles:
            key = f"obstacle:{oid}"
            c = cum.get(key, (0.0, 0.0, 0.0, 0.0, 0.0))
            b = self._banked.get(key, (0.0, 0.0, 0.0, 0.0))
            out[oid] = (c[1] + b[1], c[2] + b[2], c[4] + self._banked_tq.get(key, 0.0))
        return out

    def _rec_restart(self):
        r = self._rec
        r["prev"] = self._rec_cum()
        r["next"] = self.steps + r["every"]
        r["since_step"] = self.steps
        r["t"], r["F"] = [], {}

    def _rec_sample(self):
        r = self._rec
        now = self._rec_cum()
        u, k = self.units, r["every"]
        r["t"].append(self.t)
        for oid, (px, py, tq) in now.items():
            p = r["prev"].get(oid, (px, py, tq))
            r["F"].setdefault(oid, []).append((-(px - p[0]) / k * u.force, -(py - p[1]) / k * u.force,
                                               -(tq - p[2]) / k * u.force * u.dx))
        r["prev"] = now
        r["next"] = self.steps + k
        drop = len(r["t"]) - r["keep"]
        if drop > 0:
            del r["t"][:drop]
            for v in r["F"].values():
                del v[:drop]

    def force_record(self) -> dict | None:
        """The force record (``record_forces``): {"every": steps per block, "block": its duration (s), "since": the
        time the record (re)started, "t_end": the blocks' end times (s), "obstacles": {id: {"force": (n, 2) N/m,
        "torque": (n,) N}}} — each row the mean over its block; None when not recording."""
        r = self._rec
        if r is None:
            return None
        obs = {}
        for oid, v in r["F"].items():
            a = np.array(v, float).reshape(-1, 3)
            obs[oid] = {"force": a[:, :2], "torque": a[:, 2]}
        return {"every": r["every"], "block": r["every"] * self.units.dt,
                "since": self._t0 + r["since_step"] * self.units.dt, "t_end": np.array(r["t"], float),
                "obstacles": obs}

    def acoustic_period(self) -> dict:
        """The periods of the slowest standing sound waves of the domain (the scheme carries sound at c_s = (dx/dt) /
        sqrt(3)): along each axis of length L, ends that hold the velocity (walls, velocity inlets: closed for sound)
        or the pressure (outlets: open) give 2 L / c_s for two alike ends, 4 L / c_s for a closed and an open one; a
        periodic axis L / c_s. {"period": the longest, "axis", "c_s" (m/s), "x", "y": {"period", "kind", "length"}}.
        Obstacles are ignored (they shorten the paths: the longest period is the one to average over)."""
        c_s = self.units.c * CS
        out = {"c_s": c_s}
        for axis, (a, b), L in (("x", ("left", "right"), self.size[0]), ("y", ("bottom", "top"), self.size[1])):
            sa, sb = self._sides[a], self._sides[b]
            if isinstance(sa, Periodic):
                T, kind = L / c_s, "periodic"
            else:
                oa, ob = isinstance(sa, Outlet), isinstance(sb, Outlet)
                if oa != ob:
                    T, kind = 4 * L / c_s, "closed-open"
                else:
                    T, kind = 2 * L / c_s, ("open-open" if oa else "closed-closed")
            out[axis] = {"period": T, "kind": kind, "length": L}
        out["axis"] = "x" if out["x"]["period"] >= out["y"]["period"] else "y"
        out["period"] = out[out["axis"]]["period"]
        return out

    def _default_uref(self) -> float:
        for s in self._sides.values():
            if isinstance(s, Inlet):
                if s.profile == "parabolic":
                    return 2 * s.velocity / 3
                if not callable(s.profile):
                    return s.velocity
        if self.u_max is not None:
            return self.u_max
        return 1.0

    # --- balance, numbers, checks ------------------------------------------------------------------------------------
    def balance(self) -> dict:
        """Mass (kg/m), momentum (kg m/s per m) and dye (concentration x m^2) of the domain: now, at the start, and
        what crossed each boundary since (per side and obstacle, the geometry changes, dye sources and injections,
        the body force); "residual" = now - start - booked: round-off when everything is accounted for."""
        u = self.units
        M, Px, Py, D = self._totals()
        M0, Px0, Py0, D0 = self._ref
        cum = self._owner_sums("cum")
        books = {}
        for k, v in self._banked.items():
            books[k] = list(v)
        for k, v in cum.items():
            b = books.setdefault(k, [0.0, 0.0, 0.0, 0.0])
            b[0] += v[0]
            b[1] += v[1]
            b[2] += v[2]
            b[3] += v[3]
        if self._g is not None:
            b = books.setdefault("dye_sources", [0.0, 0.0, 0.0, 0.0])
            sa = backend.to_numpy(self._src_acc)
            b[3] += _ksum(sa[0], sa[1])
        bi = self._body_imp
        books["body_force"] = [0.0, bi[0] - bi[2], bi[1] - bi[3], 0.0]
        tot = [sum(v[i] for v in books.values()) for i in range(4)]
        res = [M - M0 - tot[0], Px - Px0 - tot[1], Py - Py0 - tot[2], D - D0 - tot[3]]
        out = {
            "mass": {"now": M * u.mass, "start": M0 * u.mass, "residual": res[0] * u.mass,
                     "relative_residual": res[0] / M0,
                     "booked": {k: v[0] * u.mass for k, v in books.items() if v[0] != 0.0}},
            "momentum": {"now": [Px * u.momentum, Py * u.momentum], "start": [Px0 * u.momentum, Py0 * u.momentum],
                         "residual": [res[1] * u.momentum, res[2] * u.momentum],
                         "relative_residual": max(abs(res[1]), abs(res[2])) / M0,
                         "booked": {k: [v[1] * u.momentum, v[2] * u.momentum] for k, v in books.items()
                                    if v[1] != 0.0 or v[2] != 0.0}},
            "steps": self.steps - self._ref_steps,
        }
        if self._g is not None:
            out["dye"] = {"now": D * u.dx**2, "start": D0 * u.dx**2, "residual": res[3] * u.dx**2,
                          "relative_residual": res[3] / max(abs(D0), abs(D), 1e-300),
                          "booked": {k: v[3] * u.dx**2 for k, v in books.items() if v[3] != 0.0}}
        out["lattice"] = {"mass": [M, M0, res[0]], "momentum": [Px, Py, Px0, Py0, res[1], res[2]],
                          "dye": [D, D0, res[3]], "books": books}
        return out

    def flow_rates(self) -> dict:
        """Mass flow (kg/s per m of depth) into the domain through each side over the last step (also right after an
        edit, before the next step: that step's record, as in ``forces``; review B7 L14)."""
        last = self._owner_sums("last")
        kept = getattr(self, "_last_kept", None)
        if kept is not None and kept[1] == self.steps:
            last = kept[0]
        u = self.units
        return {k: last[k][0] * u.mass / u.dt for k in SIDES if k in last}

    def numbers(self, u_ref: float | None = None, length: float | None = None) -> dict:
        """Mach and Reynolds numbers, relaxation times, resolution: Ma_max (the largest speed now / c_s), Re =
        u_ref L / nu (u_ref: the inlet's mean velocity or u_max; L: ``length``, the largest obstacle's width, or the
        domain height), the grid Reynolds number u_max dx / nu, the density range (compressibility, ~Ma^2)."""
        r, ux, uy = (backend.to_numpy(a) for a in self._moments())
        fl = ~self._solid
        sp = np.sqrt(ux**2 + uy**2)[fl] if fl.any() else np.zeros(1)
        umax = float(sp.max())
        nu_l = self.units.viscosity(self.nu)
        uref = u_ref if u_ref is not None else (self.u_ref if self.u_ref is not None else self._default_uref())
        if length is None:
            length = self.length_ref
        if length is None:
            spans = [self._span(ob) for ob in self._obstacles.values()]
            length = max(spans) if spans else self.size[1]
        out = {"mach_max": umax / CS, "u_max": umax * self.units.c, "re": uref * length / self.nu, "u_ref": uref,
               "length": length, "re_cell": umax / nu_l, "tau_plus": self.tau_p, "tau_minus": self.tau_m,
               "magic": (self.tau_p - 0.5) * (self.tau_m - 0.5), "collision": self.collision,
               "nu_lattice": nu_l, "dx": self.units.dx, "dt": self.units.dt,
               "density_range": [float(r[fl].min()), float(r[fl].max())] if fl.any() else [1.0, 1.0],
               "mach_declared": (self.u_max / self.units.c / CS) if self.u_max else None}
        if self._g is not None:
            D_l = (self.tau_gm - 0.5) / 3
            out.update({"dye_diffusivity": self.dye_D_used, "dye_diffusivity_asked": self.dye_D,
                        "dye_peclet_cell": umax / D_l})
        return out

    def checks(self) -> dict:
        """Running checks: the balances' residuals, the largest Mach number, the grid Reynolds number, the density
        range; each with its limit and whether it holds."""
        b = self.balance()
        n = self.numbers()
        # round-off accumulates with the steps: the limit is 2 ulps of the total per step, at least 1e-12 (the
        # rounding of the sums over all nodes). Not a proven worst case [error in earlier: "a worst-case bound", review
        # LB1-physics P1]. Its two sources: (1) the books — the per-link records grow by the gross exchange every
        # step (~0.2 per wall link), so a plain running sum's rounding grew like n^2 and failed correct runs (a 4 x 16
        # channel after 9537 steps, an open channel after 64 000); they are now Kahan-compensated on both devices
        # (``LINK_ACC``, the dye sources, the body force's impulse) and summed exactly per owner, which leaves the
        # rounding of their final sums, ~eps times the gross exchange (Higham 2002, section 4.3: at most 2 eps sum
        # |x_i| per record); (2) the nodes' own rounding in the collision: in a steady flow it repeats every step, so it
        # grows linearly, but its sign varies from node to node (the rest population closes each node's mass:
        # unbiased); measured after the fix: the momentum residual at most 2.3e-3 of this limit, the mass's 4e-4 (a
        # closed 4 x 16 body-force channel over 256 000 steps, an open channel with an interpolated disk and dye over
        # 128 000; before: 22 and 4.6 times over it; review LB1-physics P1). So it does
        # not see a leak below about 2 eps of the total per step (7.5e-13 per step at one link of the test cavity:
        # review B7 L18); the tests check closed domains with a bound ~100 times tighter, and a mutation (an unbooked
        # 1e-13 per step at one link) that this one passes
        lim = max(1e-12, 2 * float(np.finfo(float).eps) * b["steps"])
        out = {"mass": {"relative_residual": b["mass"]["relative_residual"], "limit": lim,
                        "ok": abs(b["mass"]["relative_residual"]) < lim},
               "momentum": {"relative_residual": b["momentum"]["relative_residual"], "limit": lim,
                            "ok": abs(b["momentum"]["relative_residual"]) < lim},
               "mach": {"value": n["mach_max"], "limit": MACH_MAX, "ok": n["mach_max"] <= MACH_MAX},
               "re_cell": {"value": n["re_cell"], "limit": self.re_cell_limit(),
                           "ok": n["re_cell"] <= self.re_cell_limit()},
               "compressibility": {"density_range": n["density_range"],
                                   "value": max(abs(n["density_range"][0] - 1), abs(n["density_range"][1] - 1)),
                                   "limit": MACH_MAX**2, "ok": max(abs(n["density_range"][0] - 1),
                                                                   abs(n["density_range"][1] - 1)) <= MACH_MAX**2,
                                   "note": "относительное отклонение плотности ~ Ma² (и перепад давления): мера "
                                           "ошибки сжимаемости; предел — Ma² при Ma = 0.3"}}
        if "dye" in b:
            out["dye"] = {"relative_residual": b["dye"]["relative_residual"], "limit": lim,
                          "ok": abs(b["dye"]["relative_residual"]) < lim}
        return out

    # --- cost -------------------------------------------------------------------------------------------------------
    def cost_estimate(self) -> dict:
        """Seconds per step on the device in use, from the measured ``RATES`` (log-log interpolation in the number of
        nodes), and this run's measured speed."""
        dev = self.device
        est = _interp_rate(dev, self.N)
        meas = self._timing["seconds"] / self._timing["steps"] if self._timing["steps"] else None
        return {"device": dev, "nodes": self.N, "per_step_s": est, "steps_per_s": 1 / est,
                "measured_per_step_s": meas, "sim_seconds_per_s": self.units.dt / (meas or est),
                "note": RATES_NOTE, "other_device_per_step_s": _interp_rate("gpu" if dev == "cpu" else "cpu", self.N)}

    def describe(self) -> dict:
        return {"size": list(self.size), "nx": self.nx, "ny": self.ny, "units": self.units.params(), "nu": self.nu,
                "t": self.t, "t0": self._t0, "steps": self.steps, "device": self.device, "device_reason": getattr(self, "_reason", ""),
                "collision": self.collision, "sides": self.sides(), "obstacles": self.obstacles(),
                "dye": self.dye_D is not None, "gravity": list(self.gravity), "displaced": self.displaced}

    # --- pickling -------------------------------------------------------------------------------------------------
    def __getstate__(self):
        """Picklable as a whole: the arrays come to the host and the array module is left out; the unpickled flow
        continues bit-identically (on the device ``backend`` chooses at its next step). Inlet profiles given as
        functions are pickled as whatever the pickler does with functions."""
        d = dict(self.__dict__)
        acc = self._link_acc()
        L = dict(self._L)
        L.update({k: np.array(v) for k, v in acc.items()})
        d["_L"] = L
        d["_f"] = backend.to_numpy(self._f).copy()
        d["_g"] = None if self._g is None else backend.to_numpy(self._g).copy()
        d["_src_acc"] = backend.to_numpy(self._src_acc).copy()
        d["_xp"], d["_dev"], d["device"] = None, None, "cpu"
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self._xp = np

    # --- state ------------------------------------------------------------------------------------------------------
    def state_dict(self) -> dict:
        """Plain data (dicts, lists, floats, NumPy arrays): ``Flow2D.from_state_dict`` continues bit-identically."""
        acc = self._link_acc()
        return {
            "format": FORMAT, "size": list(self.size), "dx": self.units.dx, "dt": self.units.dt,
            "rho": self.units.rho, "nu": self.nu, "u_max": self.u_max, "mach": self.mach_target,
            "tau_max": self.tau_max, "collision": self.collision, "magic": self.magic, "gravity": list(self.gravity),
            "dye": self.dye_D, "device": self.device_mode, "displaced": self.displaced, "u_ref": self.u_ref,
            "length_ref": self.length_ref, "t0": self._t0,
            "sides": {k: v.params() for k, v in self._sides.items()},
            "ramps": {k: {"s0": r["s0"], "ramp": r["ramp"], "from": [[i.params(), w] for i, w in r["from"]]}
                      for k, r in self._ramps.items()},
            "obstacles": [ob.params() for ob in self._obstacles.values()],
            "sources": [s.params() for s in self._sources.values()],
            "next": [self._next_id, self._next_src], "t": self.t, "steps": self.steps,
            "f": backend.to_numpy(self._f).copy(), "g": None if self._g is None else backend.to_numpy(self._g).copy(),
            "src_acc": backend.to_numpy(self._src_acc).copy(),
            "acc": {k: np.array(v) for k, v in acc.items()},
            "banked": {k: list(v) for k, v in self._banked.items()}, "body_imp": list(self._body_imp),
            "banked_tq": dict(self._banked_tq), "rec": _rec_copy(self._rec),
            "ref": list(self._ref), "ref_steps": self._ref_steps,
            "force_ref": None if self._force_ref is None else [dict(self._force_ref[0]), self._force_ref[1]],
            "timing": dict(self._timing),
        }

    @classmethod
    def from_state_dict(cls, d: dict, device: str | None = None) -> "Flow2D":
        if d.get("format") not in (FORMAT, "lfphys.lbm2d/1"):
            raise ValueError(f"не состояние {FORMAT}")
        o = cls(d["size"], d["dx"], nu=d["nu"], rho=d["rho"], u_max=d["u_max"], mach=d["mach"], dt=d["dt"],
                tau_max=d["tau_max"], sides={k: side_from_params(v) for k, v in d["sides"].items()},
                collision=d["collision"], magic=d["magic"], gravity=d["gravity"], dye=d["dye"],
                device="cpu", displaced=d["displaced"], u_ref=d["u_ref"], length_ref=d["length_ref"],
                t0=d.get("t0", 0.0))
        if "ramps" in d:
            o._ramps = {k: {"s0": _step_number(r["s0"]), "ramp": float(r["ramp"]),
                            "from": [(side_from_params(p), float(w)) for p, w in r["from"]]}
                        for k, r in d["ramps"].items()}
        else:  # format /1: one start time for all inlets
            s0 = int(round(float(d["inlet_t0"]) / float(d["dt"])))
            o._ramps = {k: {"s0": s0, "ramp": v.ramp, "from": []} for k, v in o._sides.items()
                        if isinstance(v, Inlet)}
        for p in d["obstacles"]:
            o._obstacles[int(p["id"])] = _Obstacle(p["id"], shape_from_params(p["shape"]), p["velocity"], p["omega"],
                                                   p["interpolated"], p["label"], p["ref_length"])
        for p in d["sources"]:
            o._sources[int(p["id"])] = _Source(p["id"], shape_from_params(p["shape"]), p["concentration"], p["label"])
        o._next_id, o._next_src = d["next"]
        o._build(reset_acc=True)
        for k, v in d["acc"].items():
            o._L[k] = np.array(v, float)
        o._f = np.array(d["f"], float)
        o._g = None if d["g"] is None else np.array(d["g"], float)
        sa = np.array(d["src_acc"], float)
        o._src_acc = sa if sa.ndim == 2 else np.stack([sa, np.zeros_like(sa)])  # older states: no compensation
        o.t, o.steps = float(d["t"]), int(d["steps"])
        o._banked = {k: list(v) for k, v in d["banked"].items()}
        o._body_imp = [*map(float, d["body_imp"]), 0.0, 0.0][:4]  # older states: [x, y] without compensation
        o._ref = tuple(d["ref"])
        o._ref_steps = int(d["ref_steps"])
        o._force_ref = None if d["force_ref"] is None else (dict(d["force_ref"][0]), int(d["force_ref"][1]))
        o._banked_tq = dict(d.get("banked_tq", {}))
        o._rec = _rec_copy(d.get("rec"))
        o._timing = dict(d["timing"])
        o.device_mode = d["device"] if device is None else device
        o._xp, o.device, o._dev = np, "cpu", None
        o._choose()
        return o


# --- the remap's pieces (plan P16.1) -------------------------------------------------------------------------------------
REMAP_PAD = 2  # ghost layers beyond a non-periodic side: the four-point stencil reaches two cells
# the non-equilibrium part rescaled by a remap (``Flow2D.remap``); False only in the tests' negative control (the part
# carried over as it is: the viscous stress of the old grid's units in the new one)
REMAP_NEQ_RESCALE = True


def _step_number(v):
    """A ramp's start step: an integer as stored, or a fraction of a step after a change of the time step (remap)."""
    v = float(v)
    return int(v) if v.is_integer() else v


def _ghosts(v1, v2, v3, rule, w=None):
    """The two ghost layers beyond a side (half a cell and one and a half cells outside; the wall half-way between the
    side's node layer and the first ghost) from the layers v1, v2, v3 inside (v1 next to the wall; v2, v3 None in a
    domain too thin): "D" the wall's value w and the parabola through it and v1, v2 (exact for quadratics; linear with
    v1 alone); "E" the parabola through v1, v2, v3 (no condition at the wall); "N" a mirror (no normal derivative)."""
    if rule == "D":
        if v2 is None:
            return 2.0 * w - v1, 4.0 * w - 3.0 * v1
        return (8.0 / 3.0) * w - 2.0 * v1 + v2 / 3.0, 8.0 * w - 9.0 * v1 + 2.0 * v2
    if rule == "E" and v2 is not None and v3 is not None:
        return 3.0 * v1 - 3.0 * v2 + v3, 6.0 * v1 - 8.0 * v2 + 3.0 * v3
    return v1, (v2 if v2 is not None else v1)


def _nb(A, a, b, px, py):
    """A at the node (i + a, j + b) of every node (i, j), and where that node exists (wrapped along periodic axes)."""
    R = np.roll(A, (-a, -b), axis=(-2, -1))
    nx, ny = A.shape[-2:]
    ok = np.ones((nx, ny), bool)
    if not px and a:
        ok[slice(nx - a, None) if a > 0 else slice(0, -a), :] = False
    if not py and b:
        ok[:, slice(ny - b, None) if b > 0 else slice(0, -b)] = False
    return R, ok


def _fill_solid(V, fluid, px, py, wall=None):
    """V (k, nx, ny), meaningful at the fluid nodes, with values at the solid ones: a solid node next to the fluid takes
    the mean of its fluid neighbours (the four along the axes, else the four diagonal ones) — with ``wall`` (k, nx, ny),
    the wall's value there, 2 wall - that mean (linear through the wall half-way) —, a deeper one the value of the
    nearest such node."""
    out = np.array(V, float)
    solid = ~fluid
    if not solid.any() or not fluid.any():
        return out
    known = fluid.copy()
    for offs in (((1, 0), (-1, 0), (0, 1), (0, -1)), ((1, 1), (1, -1), (-1, 1), (-1, -1))):
        S = np.zeros_like(out)
        n = np.zeros(fluid.shape)
        for a, b in offs:
            Vr, ok = _nb(np.asarray(V, float), a, b, px, py)
            Fr, _ = _nb(fluid, a, b, px, py)
            w = ok & Fr
            S += np.where(w, Vr, 0.0)
            n += w
        sel = solid & ~known & (n > 0)
        if sel.any():
            mean = S[:, sel] / n[sel]
            out[:, sel] = (2.0 * wall[:, sel] - mean) if wall is not None else mean
            known |= sel
    if not known.all():
        from scipy import ndimage
        _, (ii, jj) = ndimage.distance_transform_edt(~known, return_indices=True)
        miss = ~known
        out[:, miss] = out[:, ii[miss], jj[miss]]
    return out


def _ddx(a, solid, axis, periodic, dx):
    """d a / d axis with centred differences where both neighbours are fluid, one-sided where one is, 0 where none."""
    n = a.shape[axis]
    fl = ~solid
    if periodic:
        ap, am = np.roll(a, -1, axis), np.roll(a, 1, axis)
        fp, fm = np.roll(fl, -1, axis), np.roll(fl, 1, axis)
    else:
        ap, am = np.roll(a, -1, axis), np.roll(a, 1, axis)
        fp, fm = np.roll(fl, -1, axis), np.roll(fl, 1, axis)
        idx = [slice(None)] * 2
        idx[axis] = n - 1
        fp = fp.copy()
        fp[tuple(idx)] = False
        idx[axis] = 0
        fm = fm.copy()
        fm[tuple(idx)] = False
    with np.errstate(invalid="ignore"):
        c = np.where(fp & fm, (ap - am) / (2 * dx),
                     np.where(fp, (ap - a) / dx, np.where(fm, (a - am) / dx, 0.0)))
    return np.where(solid, np.nan, c)


# --- the benchmark and the kernel's registration ------------------------------------------------------------------------
def bench(size: int, device: str = "cpu", steps: int = 10) -> float:
    """Seconds per step of a periodic square of ``size`` nodes with a disk and the dye on, after a warm-up."""
    n = max(8, int(round(math.sqrt(size))))
    fl = Flow2D((n * 1e-3, n * 1e-3), 1e-3, nu=1e-4, rho=1000.0, dt=5e-3, sides={s: "periodic" for s in SIDES},
                gravity=(1e-3, 0.0), dye=1e-4, device=device)
    fl.add_obstacle(Disk((n * 0.5e-3, n * 0.5e-3), n * 0.1e-3))
    fl.advance(2)
    t = time.perf_counter()
    fl.advance(steps)
    fl.velocity()
    return (time.perf_counter() - t) / steps


_BENCH = {}


def _bench(size: int, xp, cplx):
    """For ``backend.calibrate``: ten steps on the device of ``xp`` and the velocity back (the flow is built once per
    size and device and kept for the repeated timings)."""
    dev = "gpu" if xp is not np else "cpu"
    key = (size, dev)
    if key not in _BENCH:
        _BENCH.clear()
        n = max(8, int(round(math.sqrt(size))))
        fl = Flow2D((n * 1e-3, n * 1e-3), 1e-3, nu=1e-4, rho=1000.0, dt=5e-3, sides={s: "periodic" for s in SIDES},
                    gravity=(1e-3, 0.0), dye=1e-4, device=dev)
        fl.add_obstacle(Disk((n * 0.5e-3, n * 0.5e-3), n * 0.1e-3))
        _BENCH[key] = fl
    fl = _BENCH[key]
    fl.advance(10)
    fl.velocity()


backend.register(backend.KernelSpec(
    KERNEL, "Жидкость в 2-D (решёточный метод Больцмана)",
    "шаг течения D2Q9 с краской: перенос, граничные условия, столкновения (плейграунд «Жидкости»)",
    gpu=True,
    precisions={"fp64": {"allowed": True},
                "fp32": {"allowed": False,
                         "why": "отклонения популяций от равновесия ~Ma² ~ 1e-3: в fp32 от них остаётся ~4 знака "
                                "(не проверено — не предлагается)"}},
    crossover=32 * 32,
    crossover_note=("измерено 2026-11-04 на RTX 2080 Ti против CPU контейнера (NumPy, столкновения в 4 потоках), fp64, "
                    "шаги на устройстве: GPU быстрее при любом размере от 32² (×8; ×47 на 128², ×155 на 1024²); "
                    "«Измерить заново» уточняет"),
    bench=_bench, bench_sizes=(32 * 32, 64 * 64, 128 * 128, 256 * 256, 512 * 512, 1024 * 1024)))
