# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Classical molecular dynamics for the playground (plan P8, P15.4): particles and molecules in a box with walls,
pistons, heat baths and a uniform field; NVE and NVT; everything editable at the current moment.

Units: reduced (``core.md.units``: sigma0, epsilon0, m0, k_B = 1); conversions to Angstrom, ps, K, amu, bar there.

**System.** ``MD(dim, box, boundary, pair, dt, seed, ...)``: d = 2 or 3; a box [0, L_a] per axis, each axis periodic
or bounded by two walls. Species (name, mass, sigma, epsilon, charge; mass = inf: frozen particles, which act on the
others and do not move). Particles with stable integer keys (increasing; rows always in key order). Molecules: atoms
with bonds (i, j, type) and angles (i, j, k; j the vertex) whose types are bonded terms from ``theories.models``
(``set_bond_type``, ``set_angle_type``). Exclusions (``exclude``): ``"bonded"`` (default; the pairs one and two bonds
apart, 1-2 and 1-3 from the bond graph, feel no pair or Coulomb force), ``"molecule"`` (no intramolecular pair or
Coulomb force at all), ``"none"``.

**Interactions.** H = sum m v^2/2 + sum_pairs u_pair + sum Coulomb + bonds + angles + soft walls - sum m g.x.
* The short-range pair term is injected (``pair=``, e.g. ``theories.models.interatomic.LennardJones``): the core
  takes its per-species tables and evaluates it over a Verlet list (``core.md.cells``: cell lists, radius
  max r_c + ``skin``, rebuilt when a particle has moved more than skin/2 since the last build, after every edit), so
  every pair within r_c is included exactly. The pair cutoff must not exceed half a periodic box length (refused).
* Coulomb (core): u = q_i q_j / r (charges in units q0, ``units``; in d = 2 the particles are 3-D charges confined
  to a plane, 1/r). Summed directly over all pairs when every axis has walls (exact; O(N_q^2)). A periodic axis with
  charges is refused: the lattice sum is conditionally convergent and its value depends on the summation shape;
  three periodic axes in d = 3 need Ewald summation and a slab or a periodic plane need the 2-D Ewald or a slab
  correction, which this module does not have (an open item in the engine's STATUS.md).
* Bonds, angles: injected terms (energy and its derivative); the geometry (minimum image, forces on the three atoms
  of an angle from d cos(theta)/dx) is here. The forces are exactly the gradient of the energy (tests).
* Walls per side: ``"specular"`` (elastic reflection), ``"thermal"`` (diffuse re-emission at the wall temperature
  T_w: the normal speed from the flux-weighted Maxwellian p(v_n) ~ v_n exp(-m v_n^2 / 2T_w), v_n = sqrt(-2 (T_w/m)
  ln U), the tangential components Gaussian with variance T_w/m - Maxwell's diffuse wall with full accommodation: a
  heat bath; the heat is counted), ``"soft"`` (an injected wall potential, e.g. ``LJWall`` 9-3 / 10-4, with a
  specular plane behind it as a backstop, whose hits are counted). A uniform field g (``gravity``).
* A piston (``set_piston``): the "hi" wall of one walled axis replaced by a movable flat specular face at X with mass
  M (``inf``: driven at a velocity the user sets), an external pressure p_ext on its outer side (force -p_ext A) and
  the field; its collisions with particles are elastic two-body collisions along the axis (impulse exchanged
  exactly); between collisions it moves under -p_ext A + M g_a. End stops at x_min and L_a: a free piston bounces off
  them elastically, a driven piston stops there. Work done on the gas: the sum of the particles' kinetic energy
  changes at its collisions (exact bookkeeping).

**Time step** (one step dt; Strang splitting, time-reversible and measure-preserving in the NVE parts):

    O_csvr(dt/2) B(dt/2) A(dt/2) O_lang(dt) A(dt/2) [forces] B(dt/2) O_csvr(dt/2)

B: kicks v += (dt/2) F/m (and the piston's); A: free flight with the walls' and the piston's collisions found
exactly on the straight segments (several per drift, earliest first); O_lang: Langevin's Ornstein-Uhlenbeck step
v -> c v + sqrt((1 - c^2) T/m) R, c = exp(-gamma dt), for the particles inside the bath's region (BAOAB of
Leimkuhler & Matthews 2013 inside the region, velocity Verlet - Swope et al. 1982 - outside); O_csvr: the canonical
sampling through velocity rescaling of Bussi, Donadio & Parrinello (2007), their exact discrete update (Eq. A7) of
the kinetic energy of the bath's particles over dt/2 with N_f degrees of freedom and relaxation time tau; a global
bath acts on the velocities relative to the centre of mass along the axes whose momentum is conserved, so it leaves
that momentum as it is (review B7-md M9). Without baths and thermal walls the step is velocity Verlet (NVE): energy
error O(dt^2), bounded (no drift) for small dt and continuous forces; exactly time-reversible (``reverse``); the
total momentum conserved to round-off along every axis where it is a constant of the motion (pair forces are summed
antisymmetrically; ``momentum_drift`` compares its change with a bound of the rounding). Hard walls, thermal walls
and the piston act inside the drift (impulses at exact times on the straight segments): for an ideal gas the
bookkeeping is exact; with interacting atoms such an impulse is not resolved by the splitting and leaves an energy
error of order F v dt per hit that accumulates with the hits: the energy error is then first order in dt (measured,
200 LJ atoms at T = 2.5 in a walled 35 x 47 box over 9.3 tau, three seeds: largest |E - E0| 0.6 / 0.33 / 0.19 epsilon
at dt = 0.0046 / 0.0023 / 0.0012 tau, against 0.06 / 0.02 / 0.006 in the same box made periodic; the playground's
piston preset: a first-law residual of 1-14 epsilon over its first stroke at these steps, about 1.5 % of the work at
most: review B7-md M11). Baths may be restricted to a region (a local heat bath) and
to species; every O step counts the heat it gives (the change of kinetic energy), as do thermal walls:
``energy_balance`` closes the first law dE = Q + W (W: the piston's work; an edit moves E0 by the energy it
changes) up to the integrator's error. All randomness comes from one seeded generator (PCG64) whose state is saved:
runs are reproducible bit for bit.

**Measurements.** Temperature with its degrees of freedom stated: N_f = d N_mobile minus the number of momentum
components that are constants of the motion (``momentum_conserved_axes``: a periodic axis without a field component,
when no Langevin bath, no local or species-restricted CSVR bath, no thermal wall and no frozen particle acts; review
B7-md M21); then T = 2 (K - sum over those axes of P_a^2/2M)/N_f (flexible molecules: no constraints).
Pressure: the virial tensor P_aa = (2 K_aa + W_aa)/V with W = sum over pairs, bonds, angles of r_ij . F_ij (minimum
image; kinetic part in the centre-of-mass frame along the conserved axes); with walls it equals the time-averaged
force on hard walls per area (Clausius' virial theorem with the wall as the external force), with soft walls only up
to O(sigma/L) (the volume is ambiguous); with a field the virial gives the volume average, not the wall pressure.
With frozen particles (external bodies to the moving ones) W_aa = sum over the mobile particles of x_a F_a (pair,
Coulomb and bonded forces), Clausius' virial of the moving atoms, which with the origin at the lo wall equals the
pressure on the hi wall of that axis; along a periodic axis it is undefined (reported as None); frozen-frozen pairs
are not in the pair list (review B7-md M13).
The tail correction of the pair model (full potential beyond r_c with g = 1) is reported separately, only for a
fully periodic box. Wall pressure by momentum: the impulse given to each wall (hard: m |Delta v_n| per hit; soft: the
force integrated over time) per area and time since ``reset_counters``. Also: kinetic and potential energies by part,
the truncated energy of an energy-shifted pair model, momentum, g(r), mean-square displacement (unwrapped
coordinates) and the diffusion coefficient, the velocity distribution against Maxwell-Boltzmann (KS distance and
the Dvoretzky-Kiefer-Wolfowitz bound; all mobile species pooled, each component divided by sqrt(T/m) of its own
mass), heat and work counters, the time step's error by a companion (``step_error``: the same interval with dt/2;
deterministic systems only), the change of the total momentum against its rounding bound (``momentum_drift``), the
kinetic energy of molecules split into translation, rotation and vibration with the bonds' and angles' potential
energy, each as a temperature (``molecule_modes``), the number, density and temperature in a ball (``probe``).

**Building matter.** ``fill``: a crystal block of a given number density (``crystal_sites``: a perfect lattice of
that density, whole cells in the region, cells fitted to a periodic box the block spans), n particles on a lattice,
or n particles at random places none nearer than sigma_ij (``random_sites``: random sequential insertion).
``add_molecule(..., T)``: each atom's velocity Maxwellian at T - translation, rotation and vibration at T (review
B7-md M4).

**Edits** (``add``, ``remove``, ``set``, ``add_molecule``, ``add_molecules`` - many molecules in one edit, the
candidates over the energy bound left out -, ``set_species``, ``set_wall``, ``set_piston``, ``set_boundary`` - an axis
made walled or periodic -, ``set_pair``, ``set_dt``, ``add_thermostat``, ...) act at the current step time, are transactional (a refused edit - ValueError - leaves the
state bit for bit as it was) and refuse what would break the dynamics: positions outside walls or the piston, an
insertion - or a change of a species' sigma, epsilon or charge - after which a particle's interaction energy exceeds
``max_insert_energy`` or the call's ``max_energy`` (overlap), non-finite forces, a pair cutoff beyond half a periodic
box, charges with a periodic axis. ``set_piston`` on the side of a thermal wall keeps that wall's heat in the
first-law balance (review B7-md M10).

**The box at the current moment** (``deform``, plan P16.1): an affine deformation of the box with the matter in it -
the canonical point transformation x_a -> lambda_a x_a, p_a -> p_a / lambda_a (peculiar momenta; relative to the centre
of mass along conserved axes), the volume step of Andersen's and the MTK barostats - whose energy change is the work
done on the system, -S dV to first order with the affine stress (``affine_stress``; the virial pressure where no field,
soft wall or frozen atom acts); a jump is irreversible, a change over a time (``ramp_box``: a small affine step after
every step, each step's energy change booked) tends to the adiabat as it slows (exactly so for an ideal gas at any
rate: T V^(2/d) = const); or the hi wall of a walled axis moved over empty space (a free expansion; no work at hard
walls). The energy change is booked as work in the first law (``W_box``), not as an edit (review LB1-physics P2, P3).

``state_dict`` / ``from_state_dict``: plain data and NumPy arrays; a restored system continues bit for bit (the pair
list is rebuilt from the positions of its last build).

**Devices and cost.** The pair forces (the heavy part) run on GPU 0 when ``core.backend`` chooses it (kernel
"md.pair_forces"; "auto" from 2·10^4 pairs in the list; ``device="cpu"`` keeps a system on the CPU): the elementwise
part is the same IEEE arithmetic as NumPy's and the per-particle sums are made in numpy.bincount's order by a small
CUDA kernel, so the forces - and the trajectory - equal the CPU's bit for bit (energy and virial sums: to rounding).
The list rebuild, the walls, the piston, the baths, Coulomb and the bonded terms stay on the CPU. Measured per step
(i9-9900K; RTX 2080 Ti): see ``core.md.observables`` (_STEP_MODEL) and ``cost_estimate``.
"""

from __future__ import annotations

import copy
import importlib
import math
import time

import numpy as np

from lfphys.i18n import T

from .. import backend
from . import cells

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": T("Molecular dynamics: particles and molecules, walls, piston, thermostats"),
    "statement": T("Classical MD in 2-D and 3-D: particle species (mass, charge, σ, ε), molecules with bonds and "
                   "angles, a short-range pair potential (from theories.models) by Verlet lists, the Coulomb "
                   "interaction (a direct sum in a box with walls), walls (specular, thermal with diffuse re-emission "
                   "— a heat bath, soft), a movable piston (mass, external pressure, work), a uniform field; velocity "
                   "Verlet (NVE), the CSVR (Bussi–Donadio–Parrinello) and Langevin (BAOAB) thermostats, also in a "
                   "region of space; changes at the current moment (transactional): among them the pair model, the "
                   "time step, an axis periodic or with walls, many molecules in one edit, the box size (an affine "
                   "deformation at once or over a given time in small steps, the work on the system accounted for "
                   "exactly, to first order in the affine stress; or a wall shift); temperature, pressure from the "
                   "virial and from the momentum given to the walls, energies, momentum, g(r), MSD, the velocity "
                   "distribution, heat and work counters, the step error from a companion run with dt/2; the state "
                   "is plain data, continued bit for bit."),
    "validity": T("classical mechanics (quantum corrections at ħω ≳ kT, for light atoms and low T, are not "
                  "included); the interactions are models (theories.models.interatomic), except the Coulomb one; "
                  "step error O(dt²) for continuous forces (Verlet: energy without drift at small dt; CSVR and BAOAB: "
                  "the stationary distribution with an error O(dt²)); with hard walls and the piston and interacting "
                  "atoms the energy error is first order in dt (an impact inside a step); Coulomb only in a box with "
                  "walls on every axis (periodic: refused, no Ewald sum); the piston is a flat specular face only on "
                  "the hi side of one axis"),
    "basis": [T("Swope, Andersen, Berens & Wilson, J. Chem. Phys. 76, 637 (1982): velocity Verlet"),
              "Bussi, Donadio & Parrinello, J. Chem. Phys. 126, 014101 (2007), arXiv:0803.4060, Eqs. (7), (A7)",
              "Leimkuhler & Matthews, Appl. Math. Res. Express 2013, 34, arXiv:1203.5428: BAOAB",
              T("Allen & Tildesley, Computer Simulation of Liquids (2nd ed., 2017): virial, tail corrections, lists"),
              T("Maxwell (1879): diffuse wall; Tehver, Toigo, Koplik & Banavar, PRE 57, R17 (1998): thermal walls"),
              T("checks: NIST SRS (LJ, 3σ + tail; linear force shift 2.5σ), closed forms (ideal gas, bond and "
                "angle frequencies by the Verlet map, heat exchange of a Knudsen gas), the Γ(N_f/2) distribution of "
                "the kinetic energy")],
    "conflicts": [],
}

_FORMAT = "lfphys.md/1"
KERNEL = "md.pair_forces"
_SEG_SRC = r'''
extern "C" __global__ void md_seg(const double* w, const int* oj, const long long* sj, const int* oi,
                                  const long long* si, double* f, const int n) {
    int p = blockIdx.x * blockDim.x + threadIdx.x;
    if (p >= n) return;
    double a = 0.0;
    for (long long e = sj[p]; e < sj[p + 1]; ++e) a += w[oj[e]];
    double b = 0.0;
    for (long long e = si[p]; e < si[p + 1]; ++e) b += w[oi[e]];
    f[p] = a - b;
}
'''
_SEG = {}


def _seg_kernel():
    """Per-particle sums of the pair contributions in increasing pair order (as numpy.bincount adds them)."""
    if "k" not in _SEG:
        _SEG["k"] = backend._CP.RawKernel(_SEG_SRC, "md_seg")
    return _SEG["k"]


_BENCH: dict = {}


def _bench(size, xp, cdtype=None):
    """One pair-force evaluation (12-6 terms, minimum image, per-particle sums) for ``size`` pairs among size/20
    particles in a periodic cube at density 0.8 (backend.calibrate)."""
    key = (size, xp.__name__)
    if key not in _BENCH:
        rng = np.random.default_rng(0)
        n = max(size // 20, 16)
        L = (n / 0.8) ** (1.0 / 3.0)
        x = rng.random((n, 3)) * L
        i = rng.integers(0, n, size)
        j = (i + 1 + rng.integers(0, n - 1, size)) % n
        d = {"x": x, "i": xp.asarray(i), "j": xp.asarray(j), "L": L, "n": n}
        if xp is not np:
            for side, idx in (("i", i), ("j", j)):
                d["o" + side] = xp.asarray(np.argsort(idx, kind="stable").astype(np.int32))
                d["s" + side] = xp.asarray(np.concatenate([[0], np.cumsum(np.bincount(idx, minlength=n))]))
        _BENCH[key] = d
    d = _BENCH[key]
    x = xp.asarray(d["x"])
    dx = x[d["j"]] - x[d["i"]]
    dx -= d["L"] * xp.rint(dx / d["L"])
    r2 = dx[:, 0] * dx[:, 0] + dx[:, 1] * dx[:, 1] + dx[:, 2] * dx[:, 2]
    q = 1.0 / r2
    q6 = q * q * q
    fr = 4.0 * (12.0 * q6 * q6 - 6.0 * q6) * q
    for a in range(3):
        w = fr * dx[:, a]
        if xp is np:
            np.bincount(d["j"], weights=w, minlength=d["n"]) - np.bincount(d["i"], weights=w, minlength=d["n"])
        else:
            out = xp.empty(d["n"], dtype=xp.float64)
            _seg_kernel()(((d["n"] + 127) // 128,), (128,), (xp.ascontiguousarray(w), d["oj"], d["sj"], d["oi"],
                                                             d["si"], out, np.int32(d["n"])))
            backend.to_numpy(out)


backend.register(backend.KernelSpec(
    KERNEL, T("Molecular dynamics: pair forces"),
    T("forces, energy and virial of a short-range pair potential by the Verlet list (core.md.system; the playground "
      "of particles and molecules P15.4): element by element as on the CPU, sums over particles in the order of "
      "numpy.bincount — the forces equal the CPU's bit for bit"),
    gpu=True,
    precisions={"fp64": {"allowed": True},
                "fp32": {"allowed": False,
                         "why": T("MD trajectories are chaotic: the fp32 error of the forces grows exponentially "
                                  "and changes the trajectory within tens of steps; the NVE energy drifts (not "
                                  "checked — not offered)")}},
    crossover=20000,
    crossover_note=T("pairs in the Verlet list; measured 2026-11-04 on an RTX 2080 Ti against the container's CPU "
                     "(i9-9900K): the force kernel is faster on the GPU from 2·10^4 pairs (0.46 against 0.76 ms), ×12 "
                     "at 10^5, ×28 at 3·10^5; the whole step (list rebuilds and the rest on the CPU): 3-D ×1.1 / 2.0 "
                     "/ 2.7 / 2.0 at N = 10^3 / 3·10^3 / 10^4 / 3·10^4, 2-D ×1.0 / 1.7 / 2.2 at N = 3·10^3 / 10^4 / "
                     "3·10^4; “Measure again” refines this"),
    bench=_bench, bench_sizes=(2000, 5000, 10000, 20000, 50000, 100000, 300000, 1000000)))
_EXCLUDE = ("bonded", "molecule", "none")
_WALL_KINDS = ("specular", "thermal", "soft")
_BATHS = ("csvr", "langevin")
_AX = "xyz"


def _trapezoid(S0, S1, V0, lam, changed):
    """-sum over the changed axes of (S0_a + S1_a)/2 dV_a, the axes deformed one after the other (dV_a = V0 (lambda_a
    - 1) prod of the earlier lambdas): the trapezoid estimate of -int S dV of one affine step; None where S is
    undefined."""
    out = 0.0
    for a in changed:
        if S0[a] is None or S1[a] is None:
            return None
        out -= 0.5 * (S0[a] + S1[a]) * V0 * (lam[a] - 1.0) * float(np.prod(lam[:a]))
    return out


def _ramp_data(r):
    return None if r is None else {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in r.items()}


def _ramp_from(d):
    if d is None:
        return None
    return {k: (np.array(v, float) if k in ("L0", "L1") else v) for k, v in d.items()}


def _term_data(term):
    if term is None:
        return None
    cls = type(term)
    return {"module": cls.__module__, "class": cls.__name__, "params": term.params()}


def _term_from(d):
    """Rebuild an injected term from its plain data (only lfphys modules are imported)."""
    if d is None:
        return None
    mod = d["module"]
    if not mod.startswith("lfphys."):
        raise ValueError(f"a term from outside lfphys: {mod!r}")
    cls = getattr(importlib.import_module(mod), d["class"])
    return cls.from_params(d["params"])


def lattice(n, lo, hi, kind="auto"):
    """n lattice sites filling the box [lo, hi] (d = 2: square or triangular "hex"; d = 3: simple cubic or "fcc"),
    the first n sites of the smallest lattice with at least n sites, centred in their cells."""
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    d = len(lo)
    ext = hi - lo
    if kind == "auto":
        kind = "fcc" if d == 3 else "hex"
    if kind in ("sc", "square"):
        basis = np.zeros((1, d))
    elif kind == "fcc" and d == 3:
        basis = np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])
    elif kind == "hex" and d == 2:
        basis = np.array([[0, 0], [0.5, 0.5]])   # centred rectangular; triangular when the cell is 1 x sqrt(3)
    else:
        raise ValueError(f"lattice kind {kind!r} for d = {d}")
    nb = basis.shape[0]
    aspect = ext / ext.max()
    if kind == "hex":
        aspect = aspect / np.array([1.0, math.sqrt(3.0)])
    m = 1
    while True:
        cellsn = np.maximum(np.round(m * aspect).astype(int), 1)
        if np.prod(cellsn) * nb >= n:
            break
        m += 1
    idx = np.stack(np.meshgrid(*[np.arange(c) for c in cellsn], indexing="ij"), -1).reshape(-1, d)
    pts = (idx[:, None, :] + basis[None, :, :] + 0.25).reshape(-1, d) / cellsn
    return lo + pts[:n] * ext


def _basis(kind, d):
    if kind == "auto":
        kind = "fcc" if d == 3 else "hex"
    if kind in ("sc", "square"):
        return kind, np.zeros((1, d)), np.ones(d)
    if kind == "fcc" and d == 3:
        return kind, np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]], float), np.ones(3)
    if kind == "hex" and d == 2:
        return kind, np.array([[0, 0], [0.5, 0.5]], float), np.array([1.0, math.sqrt(3.0)])
    raise ValueError(f"lattice kind {kind!r} for d = {d}")


def crystal_sites(lo, hi, density, kind="auto", full=None):
    """The sites of a perfect lattice of number density ``density`` in the box [lo, hi] (review B7-md M17): d = 2
    triangular ("hex": a rectangular cell a x a sqrt(3) with two sites, a = (2/(sqrt(3) rho))^(1/2)) or square; d = 3
    "fcc" (cubic cell a = (4/rho)^(1/3), four sites) or simple cubic. Along an axis that is ``full`` (a periodic axis
    the block spans) the number of cells is rounded so that the lattice is periodic with the box, and the cell is
    stretched or compressed to fit (the density then differs from the requested one: reported); along any other axis
    only whole cells of the requested size are placed, centred in the region (the margins stay empty). Returns
    (positions (n, d), info) with info = {"density": sites per volume of the cells, "requested", "cells", "cell",
    "strain": the largest relative change of a cell side}."""
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    d = len(lo)
    if not (density > 0 and math.isfinite(density)):
        raise ValueError("density > 0")
    kind, basis, shape = _basis(kind, d)
    nb = basis.shape[0]
    a = (nb / (density * float(np.prod(shape)))) ** (1.0 / d)
    cell = a * shape
    ext = hi - lo
    full = np.zeros(d, bool) if full is None else np.asarray(full, bool)
    ncell = np.where(full, np.maximum(np.round(ext / cell), 1), np.floor(ext / cell * (1 + 1e-12))).astype(int)
    if np.any(ncell < 1):
        raise ValueError(f"the region is smaller than one lattice cell ({' x '.join(f'{c:.3g}' for c in cell)}) "
                         f"at density {density:g}")
    used = np.where(full, ext / ncell, cell)
    offset = np.where(full, 0.0, 0.5 * (ext - ncell * cell))
    idx = np.stack(np.meshgrid(*[np.arange(c) for c in ncell], indexing="ij"), -1).reshape(-1, d)
    pts = lo + offset + (idx[:, None, :] + basis[None, :, :] + 0.25).reshape(-1, d) * used
    info = {"density": nb / float(np.prod(used)), "requested": float(density), "cells": ncell.tolist(),
            "cell": used.tolist(), "strain": float(np.max(np.abs(used / cell - 1.0)))}
    return pts, info


class _SiteIndex:
    """Points with their own exclusion distances ``dms``, sorted into cells of width >= every distance (review UX-ui U5:
    the placement is vectorised): ``hits(P)`` says which candidate points come nearer to a stored point than that
    point's distance (minimum image on periodic axes). The cells are those of ``random_sites`` (``nc`` per axis,
    clamped at the walls), so the test is exact: every point within the largest distance is in a neighbouring cell."""

    def __init__(self, pts, dms, L, periodic, nc):
        self.L = np.asarray(L, float)
        self.periodic = np.asarray(periodic, bool)
        self.nc = np.asarray(nc, np.int64)
        self.d = len(self.L)
        self.w = self.L / self.nc
        self.strides = np.cumprod(np.concatenate([[1], self.nc[::-1][:-1]]))[::-1]
        pts = np.asarray(pts, float).reshape(-1, self.d)
        cell = self._cells(pts) @ self.strides
        order = np.argsort(cell, kind="stable")
        self.order = order
        self.pts = pts[order]
        self.dm2 = np.asarray(dms, float).reshape(-1)[order] ** 2
        ncell = int(np.prod(self.nc))
        self.count = np.bincount(cell[order], minlength=ncell)
        self.start = np.concatenate([[0], np.cumsum(self.count)[:-1]])
        self.offs = [np.array(o) - 1 for o in np.ndindex(*([3] * self.d))]

    def __len__(self):
        return len(self.pts)

    def _cells(self, P):
        return np.clip(np.floor(P / self.w).astype(np.int64), 0, self.nc - 1)

    def pairs(self, P):
        """(I, J): candidate I is nearer than the distance of the stored point J (J: the index in the order the points
        were given)."""
        P = np.asarray(P, float).reshape(-1, self.d)
        k = len(P)
        z = np.zeros(0, np.int64)
        if k == 0 or len(self.pts) == 0:
            return z, z.copy()
        cidx = self._cells(P)
        per = np.flatnonzero(self.periodic)
        hi = self.nc - 1
        out_i, out_j = [], []
        for o in self.offs:
            g = cidx + o
            valid = np.ones(k, bool)
            for a in range(self.d):
                if self.periodic[a]:
                    g[:, a] %= self.nc[a]
                else:
                    valid &= (g[:, a] >= 0) & (g[:, a] <= hi[a])
                    g[:, a] = np.minimum(np.maximum(g[:, a], 0), hi[a])
            c = g @ self.strides
            cnt = np.where(valid, self.count[c], 0)
            tot = int(cnt.sum())
            if tot == 0:
                continue
            I = np.repeat(np.arange(k), cnt)
            off = np.repeat(np.cumsum(cnt) - cnt, cnt)
            J = np.repeat(self.start[c], cnt) + (np.arange(tot) - off)
            dx = self.pts[J] - P[I]
            for a in per:
                dx[:, a] -= self.L[a] * np.rint(dx[:, a] / self.L[a])
            r2 = dx[:, 0] * dx[:, 0]
            for a in range(1, self.d):
                r2 = r2 + dx[:, a] * dx[:, a]
            sel = r2 < self.dm2[J]
            out_i.append(I[sel])
            out_j.append(J[sel])
        if not out_i:
            return z, z.copy()
        return np.concatenate(out_i), self.order[np.concatenate(out_j)]

    def hits(self, P):
        P = np.asarray(P, float).reshape(-1, self.d)
        out = np.zeros(len(P), bool)
        out[self.pairs(P)[0]] = True
        return out


def _site_cells(L, periodic, g):
    nc = np.maximum(np.floor(np.asarray(L, float) / g).astype(int), 1)
    return np.where(np.asarray(periodic, bool) & (nc < 3), 1, nc)


def random_sites(n, lo, hi, dmin, rng, L, periodic, others=None, others_dmin=None, max_tries=None):
    """n points placed uniformly at random in [lo, hi] one after another, each refused while nearer than ``dmin``
    to an earlier point or than ``others_dmin[k]`` to the existing point ``others[k]`` (random sequential insertion;
    minimum image on periodic axes). Raises ValueError when the region is too dense (the insertion jams near packing
    fraction 0.55 in 2-D and 0.38 in 3-D for equal disks / spheres): after 200 n + 1000 tries or 20000 failures in a
    row.

    Vectorised (review UX-ui U5, UX-params P33: 20 000 atoms took minutes one by one): the candidates still needed are
    drawn at once - the same numbers, in the same order, as one at a time (``rng.random((k, d))``) - tested together
    against the points already placed (``_SiteIndex``), then accepted in their order against each other; the result is
    the same as the one-by-one insertion, point for point (tests)."""
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    L = np.asarray(L, float)
    periodic = np.asarray(periodic, bool)
    d = len(lo)
    others = np.zeros((0, d)) if others is None else np.asarray(others, float).reshape(-1, d)
    od = np.zeros(0) if others_dmin is None else np.asarray(others_dmin, float).reshape(-1)
    dmin = float(dmin)
    g = max(dmin, float(od.max()) if len(od) else 0.0, 1e-12)
    nc = _site_cells(L, periodic, g)
    per = np.flatnonzero(periodic)
    index = _SiteIndex(others, od, L, periodic, nc)
    base_pts, base_dm = others, od
    recent = np.zeros((0, d))          # placed here, not yet in the index (each with dmin)
    out = []
    tries = fails = 0
    limit = max_tries if max_tries is not None else 200 * n + 1000
    span = hi - lo
    # a generator that can step back (PCG64: ``advance`` modulo 2^128) lets a batch draw more candidates than are still
    # needed (fewer, larger batches near jamming) and give back the ones not used: the stream stays the one-by-one one
    bg = getattr(rng, "bit_generator", None)
    rewind = type(bg).__name__ in ("PCG64", "PCG64DXSM") and hasattr(bg, "advance")
    while len(out) < n:
        need = n - len(out)
        k = max(need, min(8192, 8 * need + 1024)) if rewind else need
        P = lo + span * rng.random((k, d))
        for a in per:
            P[:, a] -= L[a] * np.floor(P[:, a] / L[a])
        bad = index.hits(P)
        if len(recent):
            bad |= _SiteIndex(recent, np.full(len(recent), dmin), L, periodic, nc).hits(P)
        # pairs of candidates nearer than dmin: the later one is refused when the earlier one was placed
        earlier = {}
        if k > 1 and dmin > 0:
            ci, cj = _SiteIndex(P, np.full(k, dmin), L, periodic, nc).pairs(P)
            sel = cj < ci
            for x_, y_ in zip(cj[sel].tolist(), ci[sel].tolist()):
                earlier.setdefault(y_, []).append(x_)
        acc = np.zeros(k, bool)
        for c in range(k):
            tries += 1
            if tries > limit or fails > 20000:
                raise ValueError(f"random placement jammed: {len(out)} of {n} placed without overlaps; fewer "
                                 f"particles, a larger region or a lattice")
            ok = not bad[c] and not any(acc[e] for e in earlier.get(c, ()))
            if ok:
                acc[c] = True
                out.append(P[c])
                fails = 0
                if len(out) == n:
                    unused = k - c - 1
                    if unused:          # the draws not used go back (rewind only: else k == need)
                        bg.advance((1 << 128) - unused * d)
                    break
            else:
                fails += 1
        if acc.any():
            recent = np.vstack([recent, P[acc]])
            if len(recent) > max(256, len(index) // 4):
                base_pts = np.vstack([base_pts, recent])
                base_dm = np.concatenate([base_dm, np.full(len(recent), dmin)])
                index = _SiteIndex(base_pts, base_dm, L, periodic, nc)
                recent = np.zeros((0, d))
    return np.array(out).reshape(-1, d)


def free_sites(pos, sigma, others, others_sigma, L, periodic):
    """A mask of the sites ``pos`` (n, d) that are not nearer than sigma_ij = (sigma + others_sigma[k]) / 2 to any
    existing particle ``others[k]`` (minimum image on periodic axes): where a new particle of diameter ``sigma`` fits
    without overlapping (used to leave occupied sites of a lattice empty)."""
    pos = np.asarray(pos, float)
    d = pos.shape[1]
    others = np.asarray(others, float).reshape(-1, d)
    if len(others) == 0 or len(pos) == 0:
        return np.ones(len(pos), bool)
    od = 0.5 * (float(sigma) + np.asarray(others_sigma, float).reshape(-1))
    nc = _site_cells(L, periodic, max(float(od.max()), 1e-12))
    return ~_SiteIndex(others, od, L, periodic, nc).hits(pos)


def _probe(x, v, m, L, periodic, center, radius, hi=None):
    """Shared by ``MD.probe`` and ``HardSpheres.probe``."""
    c = np.asarray(center, float).reshape(-1)
    r = float(radius)
    L = np.asarray(L, float)
    periodic = np.asarray(periodic, bool)
    d = len(L)
    if c.shape != (d,) or not (r > 0) or np.any(periodic & (r > 0.5 * L)):
        raise ValueError("a ball: a d-vector centre and 0 < radius <= L/2 on periodic axes")
    dx = np.asarray(x, float) - c
    for a in np.flatnonzero(periodic):
        dx[:, a] -= L[a] * np.rint(dx[:, a] / L[a])
    inside = np.einsum("ij,ij->i", dx, dx) <= r * r if len(dx) else np.zeros(0, bool)
    n = int(np.sum(inside))
    hi = L if hi is None else np.asarray(hi, float)
    g = (np.arange(48) + 0.5) / 48 * 2 * r - r
    pts = np.stack(np.meshgrid(*([g] * d), indexing="ij"), -1).reshape(-1, d)
    pts = pts[np.einsum("ij,ij->i", pts, pts) <= r * r] + c
    box = np.all(periodic | ((pts >= 0.0) & (pts <= hi)), axis=1)
    vol = (math.pi * r * r if d == 2 else 4.0 / 3.0 * math.pi * r ** 3) * float(np.mean(box)) if len(pts) else 0.0
    vv = np.asarray(v, float)[inside]
    K = 0.5 * float(np.sum(np.asarray(m, float)[inside] * np.einsum("ij,ij->i", vv, vv))) if n else 0.0
    return {"n": n, "density": n / vol if vol > 0 else None, "T": 2.0 * K / (d * n) if n else None,
            "volume": vol}


class MD:
    """Molecular dynamics of particles and molecules (see the module docstring).

    MD(dim=3, box=(10, 10, 10), boundary="periodic", pair=None, dt=0.005, seed=0, skin=0.3, exclude="bonded",
       gravity=None, max_insert_energy=50.0)
    """

    def __init__(self, dim=3, box=(10.0, 10.0, 10.0), boundary="periodic", pair=None, dt=0.005, seed=0, skin=0.3,
                 exclude="bonded", gravity=None, max_insert_energy=50.0, t=0.0, device="auto"):
        if dim not in (2, 3):
            raise ValueError("dim must be 2 or 3")
        self.dim = int(dim)
        L = np.asarray(box, float).reshape(-1)
        if L.shape != (self.dim,) or not np.all((L > 0) & np.isfinite(L)):
            raise ValueError("box: dim positive finite lengths")
        if isinstance(boundary, str):
            boundary = [boundary] * self.dim
        if len(boundary) != self.dim or any(b not in ("periodic", "walls") for b in boundary):
            raise ValueError("boundary: 'periodic' or 'walls' per axis")
        if exclude not in _EXCLUDE:
            raise ValueError(f"exclude must be one of {_EXCLUDE}")
        if not (dt > 0 and math.isfinite(dt) and skin >= 0 and max_insert_energy > 0):
            raise ValueError("dt > 0, skin >= 0, max_insert_energy > 0")
        if device not in ("auto", "cpu"):
            raise ValueError("device: 'auto' (the backend's choice for the pair forces) or 'cpu'")
        self.device_mode = device
        self._force_cpu = T("set: CPU") if device == "cpu" else None
        self._device = "cpu"
        self.L = L
        self.periodic = np.array([b == "periodic" for b in boundary])
        self.pair = pair
        self.skin = float(skin)
        self.exclude = exclude
        self.max_insert_energy = float(max_insert_energy)
        self._dt = float(dt)
        self._t_base = float(t)
        self._n_since = 0
        self.nstep = 0
        self.g = np.zeros(self.dim) if gravity is None else self._vec(gravity)
        self.rng = np.random.Generator(np.random.PCG64(seed))
        self._seed = seed
        self._species: list = []
        self._bond_types: dict = {}
        self._angle_types: dict = {}
        d = self.dim
        self._key = np.zeros(0, np.int64)
        self._typ = np.zeros(0, np.int64)
        self._mol = np.zeros(0, np.int64)
        self._x = np.zeros((0, d))
        self._img = np.zeros((0, d), np.int64)
        self._v = np.zeros((0, d))
        self._f = np.zeros((0, d))
        self._next_key = 0
        self._next_mol = 0
        self._bonds = np.zeros((0, 2), np.int64)    # particle keys
        self._bond_t = np.zeros(0, np.int64)
        self._angles = np.zeros((0, 3), np.int64)
        self._angle_t = np.zeros(0, np.int64)
        self._walls: dict = {}
        for a in range(d):
            if not self.periodic[a]:
                for s in ("lo", "hi"):
                    self._walls[f"{_AX[a]}-{s}"] = self._new_wall("specular")
        self._piston = None
        self._baths: dict = {}
        self._next_bath = 0
        self._energy = {}
        self._vir = np.zeros(d)
        self._vir_aff = np.zeros(d)
        self._ramp = None          # a change of the box over a time (``ramp_box``)
        self._ramp_steps = 0       # its substeps so far (the momentum check's rounding bound)
        self._wallf = {}
        self._balance = {"t0": float(t), "E0": None, "Q": 0.0, "W": 0.0, "Wd": 0.0}
        self._msd_ref = None
        self._msd_t0 = None
        self._nl = None
        self._stats = {"rebuilds": 0, "steps_since_build": 0, "seconds": 0.0, "timed_steps": 0,
                       "backstop_hits": 0, "pairs": 0}
        self._derived()
        self._compute_forces()
        self._balance["E0"] = self.energy()
        self._p_ref = self.momentum()
        self._p_ref_step = 0
        self._p_ref_ramp = 0

    # --- small helpers ------------------------------------------------------------------------------------------
    def _vec(self, z):
        z = np.asarray(z, float).reshape(-1)
        if z.shape != (self.dim,) or not np.all(np.isfinite(z)):
            raise ValueError(f"a {self.dim}-vector of finite numbers")
        return z

    @staticmethod
    def _new_wall(kind, T=None, term=None):
        return {"kind": kind, "T": None if T is None else float(T), "term": term,
                "impulse": 0.0, "heat": 0.0, "hits": 0, "t0": None}

    @property
    def t(self) -> float:
        return self._t_base + self._n_since * self._dt

    @property
    def dt(self) -> float:
        return self._dt

    @property
    def n(self) -> int:
        return int(self._key.shape[0])

    @property
    def keys(self) -> np.ndarray:
        return self._key.copy()

    def _rows(self, keys):
        keys = np.atleast_1d(np.asarray(keys, np.int64))
        if self.n == 0:
            if len(keys):
                raise KeyError(f"no particle with key(s) {keys.tolist()}")
            return np.zeros(0, np.int64)
        r = np.searchsorted(self._key, keys)
        bad = (r >= self.n) | (self._key[np.minimum(r, self.n - 1)] != keys)
        if np.any(bad):
            raise KeyError(f"no particle with key(s) {keys[bad].tolist()}")
        return r

    def _species_index(self, name):
        for i, s in enumerate(self._species):
            if s["name"] == name:
                return i
        raise KeyError(f"no species {name!r}")

    # --- species --------------------------------------------------------------------------------------------------
    def add_species(self, name, mass=1.0, sigma=1.0, epsilon=1.0, charge=0.0):
        """A species: mass (inf: frozen), sigma (size), epsilon (energy) for the pair model, charge (units q0)."""
        if not isinstance(name, str) or not name:
            raise ValueError("a species name is a non-empty str")
        if any(s["name"] == name for s in self._species):
            raise KeyError(f"species {name!r} exists")
        sp = self._check_species({"name": name, "mass": mass, "sigma": sigma, "epsilon": epsilon, "charge": charge})

        def apply():
            self._species.append(sp)
        self._transaction(apply)
        return name

    @staticmethod
    def _check_species(sp):
        sp = dict(sp)
        for k in ("mass", "sigma", "epsilon", "charge"):
            sp[k] = float(sp[k])
        if not (sp["mass"] > 0 and sp["sigma"] > 0 and sp["epsilon"] >= 0 and math.isfinite(sp["sigma"])
                and math.isfinite(sp["epsilon"]) and math.isfinite(sp["charge"])):
            raise ValueError("mass > 0 (inf: frozen), sigma > 0, epsilon >= 0, finite charge")
        return sp

    def set_species(self, name, max_energy=None, **changes):
        """Change a species' mass, sigma, epsilon or charge at the current time (velocities kept: a mass change
        changes the kinetic energy). A change of sigma, epsilon or charge is refused, like an insertion, when a particle
        of the species then has a potential energy above ``max_energy`` (default ``max_insert_energy``; review
        B7-md M14)."""
        i = self._species_index(name)
        bad = set(changes) - {"mass", "sigma", "epsilon", "charge"}
        if bad:
            raise ValueError(f"unknown species fields {sorted(bad)}")
        sp = self._check_species({**self._species[i], **{k: v for k, v in changes.items() if v is not None}})
        moved = any(sp[k] != self._species[i][k] for k in ("sigma", "epsilon", "charge"))
        keys = self._key[self._typ == i] if moved else None

        def apply():
            self._species[i] = sp
        self._transaction(apply, new_keys=keys, max_energy=max_energy)

    def species(self) -> list:
        return [dict(s) for s in self._species]

    # --- particles ------------------------------------------------------------------------------------------------
    def add(self, species, x, v=None, T=None, zero_momentum=False, max_energy=None):
        """Add particles of one species at positions x (n, d) (or one, (d,)); velocities v, or Maxwell velocities
        at temperature T from the system's generator, or zero. Returns their keys. Refused where a position is
        outside the walls or the piston, or a new particle's interaction energy exceeds ``max_energy`` (default the
        system's ``max_insert_energy``)."""
        ti = self._species_index(species)
        x = np.atleast_2d(np.asarray(x, float))
        if x.shape[1] != self.dim or not np.all(np.isfinite(x)):
            raise ValueError(f"positions: (n, {self.dim}) finite")
        n = x.shape[0]
        m = self._species[ti]["mass"]
        if v is not None:
            v = np.broadcast_to(np.asarray(v, float), (n, self.dim)).copy()
            if not np.all(np.isfinite(v)):
                raise ValueError("non-finite velocities")
        if not math.isfinite(m):
            v = np.zeros((n, self.dim))

        def apply():
            vv = v
            if vv is None:
                vv = np.zeros((n, self.dim)) if T is None else self._maxwell(n, m, T, zero_momentum)
            self._append(x, vv, np.full(n, ti), np.full(n, -1))
        keys = np.arange(self._next_key, self._next_key + n, dtype=np.int64)
        self._transaction(apply, new_keys=keys, max_energy=max_energy)
        return keys

    def _maxwell(self, n, m, T, zero_momentum):
        if not (T >= 0 and math.isfinite(T)):
            raise ValueError("T must be finite and >= 0")
        if not math.isfinite(m):
            return np.zeros((n, self.dim))
        v = self.rng.standard_normal((n, self.dim)) * math.sqrt(T / m)
        if zero_momentum and n > 1:
            v -= v.mean(axis=0)
        return v

    def _append(self, x, v, typ, mol):
        n = x.shape[0]
        keys = np.arange(self._next_key, self._next_key + n, dtype=np.int64)
        self._next_key += n
        xw, img = self._wrap(x, np.zeros((n, self.dim), np.int64))
        self._key = np.concatenate([self._key, keys])
        self._typ = np.concatenate([self._typ, typ.astype(np.int64)])
        self._mol = np.concatenate([self._mol, mol.astype(np.int64)])
        self._x = np.vstack([self._x, xw])
        self._img = np.vstack([self._img, img])
        self._v = np.vstack([self._v, v])
        self._f = np.vstack([self._f, np.zeros((n, self.dim))])
        if self._msd_ref is not None:
            self._msd_ref = np.vstack([self._msd_ref, xw + img * self.L])
        return keys

    def fill(self, species, n=None, density=None, region=None, lattice_kind="auto", T=None, zero_momentum=True,
             arrangement="lattice", info=None, max_energy=None, skip_occupied=False):
        """Add particles of one species in ``region`` = (lo, hi) (default: the whole box, or the gas side of the
        piston) with Maxwell velocities at T (their common momentum removed with ``zero_momentum``). Returns their keys.

        * ``density`` (a crystal): a perfect lattice of that number density (``crystal_sites``: whole cells of the
          lattice spacing of the density, centred in the region; along a periodic axis the block spans, the cells are
          fitted to the box and the density reported in ``info``, a dict filled when given).
        * ``n`` with ``arrangement="lattice"``: the first n sites of the smallest lattice of ``lattice_kind`` with at
          least n sites filling the region (its spacing set by the region, not by a density).
        * ``n`` with ``arrangement="random"``: random places, none nearer than the pair's sigma_ij = (sigma_i +
          sigma_j)/2 to another particle (random sequential insertion from the system's generator; refused when the
          region is too dense).

        ``skip_occupied`` (a crystal): the sites nearer than sigma_ij to a particle already present are left empty (the
        block fills the free space around what is there; review UX-ui U4); ``info["skipped"]`` counts them, and a block
        with no free site is refused."""
        lo, hi = self._region(region)
        ti = self._species_index(species)
        if n is None and density is None:
            raise ValueError("give n or density")
        if arrangement not in ("lattice", "random"):
            raise ValueError("arrangement: 'lattice' or 'random'")
        if n is None:
            full = self.periodic & (lo <= 0.0) & (hi >= self.L)
            pos, inf = crystal_sites(np.where(full, 0.0, lo), np.where(full, self.L, hi), float(density),
                                     lattice_kind, full)
            inf["skipped"] = 0
            if skip_occupied and self.n:
                pw, _ = self._wrap(pos, np.zeros(pos.shape, np.int64))
                sig = np.array([sp["sigma"] for sp in self._species])
                keep = free_sites(pw, self._species[ti]["sigma"], self._x, sig[self._typ], self.L, self.periodic)
                inf["skipped"] = int(np.sum(~keep))
                if not keep.any():
                    raise ValueError(f"no free lattice site: all {len(pos)} sites of the block are occupied")
                pos = pos[keep]
            if info is not None:
                info.update(inf)
            return self.add(species, pos, T=T, zero_momentum=zero_momentum, max_energy=max_energy)
        n = int(n)
        if arrangement == "lattice" or n == 0:
            return self.add(species, lattice(n, lo, hi, lattice_kind), T=T, zero_momentum=zero_momentum,
                            max_energy=max_energy)
        s_new = self._species[ti]["sigma"]
        m = self._species[ti]["mass"]

        def apply():
            sig = np.array([sp["sigma"] for sp in self._species])
            od = 0.5 * (s_new + sig[self._typ]) if self.n else np.zeros(0)
            x = random_sites(n, lo, hi, s_new, self.rng, self.L, self.periodic, self._x, od)
            vv = np.zeros((n, self.dim)) if T is None else self._maxwell(n, m, T, zero_momentum)
            self._append(x, vv, np.full(n, ti), np.full(n, -1))
        keys = np.arange(self._next_key, self._next_key + n, dtype=np.int64)
        self._transaction(apply, new_keys=keys, max_energy=max_energy)
        return keys

    def _region(self, region):
        if region is None:
            lo, hi = np.zeros(self.dim), self.L.copy()
            if self._piston is not None:
                hi[self._piston["axis"]] = self._piston["X"]
            return lo, hi
        lo, hi = self._vec(region[0]), self._vec(region[1])
        if not np.all(hi > lo):
            raise ValueError("region: hi > lo on every axis")
        return lo, hi

    def adopt(self, keys, species_index, x, v, next_key=None, max_energy=None):
        """Particles taken over from another solver at the current time (``hard.md_from_hard``: hard spheres become
        particles with continuous forces): their keys (increasing), species indices, positions and velocities, kept as
        they are, into an empty system, in one edit (refused as an insertion: overlap above ``max_energy``, outside
        the walls). The keys continue from ``next_key``."""
        if self.n:
            raise ValueError("adopt: the system must be empty")
        keys = np.asarray(keys, np.int64).reshape(-1)
        n = len(keys)
        if n > 1 and np.any(np.diff(keys) <= 0):
            raise ValueError("adopt: keys must increase")
        typ = np.asarray(species_index, np.int64).reshape(-1)
        if typ.shape != (n,) or (n and (typ.min() < 0 or typ.max() >= len(self._species))):
            raise ValueError("adopt: a species index per particle")
        x = np.asarray(x, float).reshape(n, self.dim)
        v = np.asarray(v, float).reshape(n, self.dim)
        if not (np.all(np.isfinite(x)) and np.all(np.isfinite(v))):
            raise ValueError("adopt: finite positions and velocities")

        def apply():
            xw, img = self._wrap(x, np.zeros((n, self.dim), np.int64))
            mass = np.array([sp["mass"] for sp in self._species])[typ] if n else np.zeros(0)
            self._key, self._typ, self._mol = keys.copy(), typ.copy(), np.full(n, -1, np.int64)
            self._x, self._img = xw, img
            self._v = np.where(np.isfinite(mass)[:, None], v, 0.0)
            self._f = np.zeros((n, self.dim))
            self._next_key = max(int(next_key) if next_key is not None else 0, int(keys[-1]) + 1 if n else 0)
        self._transaction(apply, new_keys=keys if n else None, max_energy=max_energy)

    def remove(self, keys):
        """Remove particles (and the bonds and angles that involve them) at the current time."""
        rows = self._rows(keys)
        kset = self._key[rows]

        def apply():
            keep = np.ones(self.n, bool)
            keep[rows] = False
            self._drop(keep)
            if len(self._bonds):
                kb = ~np.any(np.isin(self._bonds, kset), axis=1)
                self._bonds, self._bond_t = self._bonds[kb], self._bond_t[kb]
            if len(self._angles):
                ka = ~np.any(np.isin(self._angles, kset), axis=1)
                self._angles, self._angle_t = self._angles[ka], self._angle_t[ka]
        self._transaction(apply)

    def _drop(self, keep):
        self._key, self._typ, self._mol = self._key[keep], self._typ[keep], self._mol[keep]
        self._x, self._img, self._v, self._f = self._x[keep], self._img[keep], self._v[keep], self._f[keep]
        if self._msd_ref is not None:
            self._msd_ref = self._msd_ref[keep]

    def set(self, keys, x=None, v=None, species=None):
        """Change positions (unwrapped allowed on periodic axes), velocities or species of particles at the current
        time; refused as ``add``."""
        rows = self._rows(keys)
        n = len(rows)
        if x is not None:
            x = np.broadcast_to(np.asarray(x, float), (n, self.dim)).copy()
        if v is not None:
            v = np.broadcast_to(np.asarray(v, float), (n, self.dim)).copy()
        ti = None if species is None else self._species_index(species)
        for z in (x, v):
            if z is not None and not np.all(np.isfinite(z)):
                raise ValueError("non-finite values")

        def apply():
            if x is not None:
                xw, img = self._wrap(x, np.zeros((n, self.dim), np.int64))
                self._x[rows] = xw
                self._img[rows] = img
                if self._msd_ref is not None:
                    self._msd_ref[rows] = xw + img * self.L
            if v is not None:
                self._v[rows] = v
            if ti is not None:
                self._typ[rows] = ti
                if not math.isfinite(self._species[ti]["mass"]):
                    self._v[rows] = 0.0
        self._transaction(apply, new_keys=self._key[rows] if x is not None else None)

    def particles(self, keys=None) -> dict:
        """Positions (wrapped), unwrapped positions, velocities, species names, molecule keys of the particles."""
        rows = np.arange(self.n) if keys is None else self._rows(keys)
        names = [self._species[t]["name"] for t in self._typ[rows]]
        return {"keys": self._key[rows].copy(), "x": self._x[rows].copy(),
                "x_unwrapped": self._x[rows] + self._img[rows] * self.L, "v": self._v[rows].copy(),
                "species": names, "molecule": self._mol[rows].copy()}

    def positions(self, unwrapped=False) -> np.ndarray:
        return (self._x + self._img * self.L) if unwrapped else self._x.copy()

    def velocities(self) -> np.ndarray:
        return self._v.copy()

    def forces(self) -> np.ndarray:
        return self._f.copy()

    # --- molecules ------------------------------------------------------------------------------------------------
    def set_bond_type(self, name, term):
        """Define or change a bond type (a term with ``evaluate(r) -> (u, -u'(r))``)."""
        if not callable(getattr(term, "evaluate", None)):
            raise ValueError("a bond term needs evaluate(r)")

        def apply():
            self._bond_types[str(name)] = term
        self._transaction(apply)

    def set_angle_type(self, name, term):
        """Define or change an angle type (a term with ``evaluate(theta, cos) -> (u, du/dcos)``)."""
        if not callable(getattr(term, "evaluate", None)):
            raise ValueError("an angle term needs evaluate(theta, cos)")

        def apply():
            self._angle_types[str(name)] = term
        self._transaction(apply)

    def add_molecule(self, species, x, bonds=(), angles=(), v=None, T=None, zero_momentum=False, max_energy=None):
        """Add a molecule: atoms of the given species (a list, one per atom) at positions x (n, d) (unwrapped,
        a connected geometry), bonds [(a, b, type)], angles [(a, b, c, type)] (b the vertex) by atom index in the
        molecule. Velocities v, or zero, or at temperature T each atom's Maxwell velocity N(0, T/m): for a flexible
        molecule (no constraints) the canonical distribution of its momenta, i.e. translation, rotation and the
        vibrations' kinetic energy all at T (review B7-md M4; ``zero_momentum`` removes the molecule's own momentum,
        which leaves it no translation). The bonds and angles keep the given geometry (their potential energy is
        whatever it gives). Refused as ``add`` (``max_energy``). Returns (molecule key, atom keys)."""
        x = np.atleast_2d(np.asarray(x, float))
        n = x.shape[0]
        if isinstance(species, str):
            species = [species] * n
        if len(species) != n or x.shape[1] != self.dim or not np.all(np.isfinite(x)):
            raise ValueError("one species per atom, positions (n, d) finite")
        typ = np.array([self._species_index(s) for s in species], np.int64)
        bt = list(self._bond_types)
        at = list(self._angle_types)
        B, BT, A, AT = [], [], [], []
        for b in bonds:
            a1, a2, ty = int(b[0]), int(b[1]), str(b[2])
            if ty not in self._bond_types:
                raise KeyError(f"no bond type {ty!r}")
            if not (0 <= a1 < n and 0 <= a2 < n and a1 != a2):
                raise ValueError("bond atoms: two distinct atoms of the molecule")
            B.append((a1, a2))
            BT.append(bt.index(ty))
        for g in angles:
            a1, a2, a3, ty = int(g[0]), int(g[1]), int(g[2]), str(g[3])
            if ty not in self._angle_types:
                raise KeyError(f"no angle type {ty!r}")
            if not (len({a1, a2, a3}) == 3 and all(0 <= z < n for z in (a1, a2, a3))):
                raise ValueError("angle atoms: three distinct atoms of the molecule")
            A.append((a1, a2, a3))
            AT.append(at.index(ty))
        if v is not None:
            v = np.broadcast_to(np.asarray(v, float), (n, self.dim)).copy()
        mk = self._next_mol

        def apply():
            vv = v
            if vv is None:
                if T is None:
                    vv = np.zeros((n, self.dim))
                else:
                    m = np.array([self._species[t]["mass"] for t in typ])
                    fin = np.isfinite(m)
                    vv = np.zeros((n, self.dim))
                    vv[fin] = self.rng.standard_normal((int(fin.sum()), self.dim)) * np.sqrt(T / m[fin])[:, None]
                    if zero_momentum and fin.sum() > 1:
                        vv[fin] -= (m[fin, None] * vv[fin]).sum(0) / m[fin].sum()
            keys = self._append(x, vv, typ, np.full(n, mk))
            self._next_mol += 1
            if B:
                self._bonds = np.vstack([self._bonds, keys[np.array(B)]])
                self._bond_t = np.concatenate([self._bond_t, np.array(BT, np.int64)])
            if A:
                self._angles = np.vstack([self._angles, keys[np.array(A)]])
                self._angle_t = np.concatenate([self._angle_t, np.array(AT, np.int64)])
        keys = np.arange(self._next_key, self._next_key + n, dtype=np.int64)
        self._transaction(apply, new_keys=keys, max_energy=max_energy)
        return mk, keys

    def add_molecules(self, species, X, bonds=(), angles=(), v=None, T=None, max_energy=None, limit=None,
                      keep_all=False):
        """Add many molecules of one shape in one edit (review UX-ui U5: one transaction instead of one per molecule):
        candidates X (k, n, d) - atoms of the given species (a name, or one per atom), bonds and angles by atom index
        in the molecule as in ``add_molecule``; velocities v (k, n, d), or each atom's Maxwell velocity at T, or zero.
        A candidate is left out when one of its atoms lies outside the walls or the piston, or comes nearer than
        0.9 sigma_ij to an atom of an earlier candidate kept so far (the earlier one wins, as in one-at-a-time insertion),
        or when, with the particles present and the other candidates kept, one of its atoms' potential energy (as ``add`` measures it: half of each
        pair and Coulomb term, half of each bond, a third of each angle, walls) exceeds ``max_energy`` (default
        ``max_insert_energy``): every candidate over the bound is dropped at once and the energies measured again until
        none is (dropping only lowers what the others feel by the dropped pairs' terms). With ``limit`` at most that
        many are kept: the first ones in order that pass (the later ones are dropped and the bound checked again). The
        kept candidates get consecutive molecule keys in their order. ``keep_all``: every candidate is kept as given - no
        candidate is left out - or the whole edit is refused (ValueError) where an atom lies outside the walls or the
        piston or an atom's energy exceeds the bound (molecules taken over as they were, e.g. by a new world). Returns
        (indices of the candidates kept, molecule keys, atom keys per kept molecule)."""
        X = np.asarray(X, float)
        if X.ndim == 2:
            X = X[None]
        if X.ndim != 3 or X.shape[2] != self.dim or not np.all(np.isfinite(X)):
            raise ValueError("candidates: (k, n, d) finite positions")
        k, n, d = X.shape
        sp = [species] * n if isinstance(species, str) else list(species)
        if len(sp) != n:
            raise ValueError("one species per atom of the molecule")
        typ = np.array([self._species_index(q) for q in sp], np.int64)
        bt, at = list(self._bond_types), list(self._angle_types)
        B, BT, A, AT = [], [], [], []
        for b in bonds:
            a1, a2, ty = int(b[0]), int(b[1]), str(b[2])
            if ty not in self._bond_types:
                raise KeyError(f"no bond type {ty!r}")
            if not (0 <= a1 < n and 0 <= a2 < n and a1 != a2):
                raise ValueError("bond atoms: two distinct atoms of the molecule")
            B.append((a1, a2))
            BT.append(bt.index(ty))
        for g in angles:
            a1, a2, a3, ty = int(g[0]), int(g[1]), int(g[2]), str(g[3])
            if ty not in self._angle_types:
                raise KeyError(f"no angle type {ty!r}")
            if not (len({a1, a2, a3}) == 3 and all(0 <= z < n for z in (a1, a2, a3))):
                raise ValueError("angle atoms: three distinct atoms of the molecule")
            A.append((a1, a2, a3))
            AT.append(at.index(ty))
        B, A = np.array(B, np.int64).reshape(-1, 2), np.array(A, np.int64).reshape(-1, 3)
        if v is not None:
            v = np.broadcast_to(np.asarray(v, float), (k, n, d)).copy()
            if not np.all(np.isfinite(v)):
                raise ValueError("non-finite velocities")
        lim = self.max_insert_energy if max_energy is None else float(max_energy)
        m_at = np.array([self._species[t]["mass"] for t in typ])
        # outside the walls or the piston: left out before anything is built
        inside = np.ones(k, bool)
        for a in range(d):
            if self.periodic[a]:
                continue
            top = self._piston["X"] if (self._piston is not None and self._piston["axis"] == a) else self.L[a]
            inside &= np.all((X[:, :, a] >= 0.0) & (X[:, :, a] <= top), axis=1)
        result = {}
        # candidates closer than 0.9 sigma_ij to an earlier candidate are left out first, the earlier one kept (as one
        # at a time would): otherwise in a crowded batch every candidate would be over the bound with another one
        sig_at = np.array([self._species[t]["sigma"] for t in typ])
        P = X.reshape(-1, d).copy()
        for a in np.flatnonzero(self.periodic):
            P[:, a] -= self.L[a] * np.floor(P[:, a] / self.L[a])
        smax = float(sig_at.max())
        dm = 0.45 * (np.tile(sig_at, k) + smax)
        own = np.repeat(np.arange(k), n)
        pi, pj = _SiteIndex(P, dm, self.L, self.periodic, _site_cells(self.L, self.periodic, float(dm.max()))).pairs(P)
        sel = own[pi] > own[pj]
        earlier = {}
        for a_, b_ in zip(own[pi[sel]].tolist(), own[pj[sel]].tolist()):
            earlier.setdefault(a_, set()).add(b_)
        first = np.zeros(k, bool)
        for c in range(k):
            first[c] = inside[c] and not any(first[e] for e in earlier.get(c, ()))
        if keep_all:
            if not np.all(inside):
                raise ValueError(f"{int(np.sum(~inside))} molecules have an atom outside the walls or the piston")
            first = np.ones(k, bool)

        def apply():
            cand = np.flatnonzero(first)
            if v is None and T is not None:
                vv_all = np.zeros((k, n, d))
                fin = np.isfinite(m_at)
                if not (T >= 0 and math.isfinite(T)):
                    raise ValueError("T must be finite and >= 0")
                vv_all[:, fin] = self.rng.standard_normal((k, int(fin.sum()), d)) * np.sqrt(T / m_at[fin])[None, :, None]
            else:
                vv_all = np.zeros((k, n, d)) if v is None else v
            n0, key0, mol0 = self.n, self._next_key, self._next_mol
            base = {q: copy.deepcopy(getattr(self, q)) for q in ("_key", "_typ", "_mol", "_x", "_img", "_v", "_f",
                                                                  "_msd_ref", "_bonds", "_bond_t", "_angles",
                                                                  "_angle_t", "_next_key", "_next_mol")}
            for _ in range(64):
                for q, val in base.items():
                    setattr(self, q, copy.deepcopy(val))
                if len(cand) == 0:
                    break
                kk = len(cand)
                keys = self._append(X[cand].reshape(-1, d), vv_all[cand].reshape(-1, d), np.tile(typ, kk),
                                    np.repeat(mol0 + np.arange(kk), n))
                kr = keys.reshape(kk, n)
                if len(B):
                    self._bonds = np.vstack([self._bonds, kr[:, B].reshape(-1, 2)])
                    self._bond_t = np.concatenate([self._bond_t, np.tile(np.array(BT, np.int64), kk)])
                if len(A):
                    self._angles = np.vstack([self._angles, kr[:, A].reshape(-1, 3)])
                    self._angle_t = np.concatenate([self._angle_t, np.tile(np.array(AT, np.int64), kk)])
                self._derived()
                rows = np.arange(n0, self.n)
                # coincident points (no energy can be measured): the later candidate goes
                bad = np.zeros(kk, bool)
                same = _SiteIndex(self._x, np.full(self.n, 1e-9), self.L, self.periodic,
                                  _site_cells(self.L, self.periodic, 1.0))
                pi, qj = same.pairs(self._x[n0:])
                pi = pi + n0
                for p_, q_ in zip(pi.tolist(), qj.tolist()):
                    if p_ != q_:
                        bad[(max(p_, q_) - n0) // n] = True
                if not bad.any():
                    try:
                        e = self._per_particle_energy()[rows]
                    except FloatingPointError:
                        e = np.full(len(rows), np.inf)
                    bad = ~np.all(np.isfinite(e.reshape(kk, n)) & (e.reshape(kk, n) <= lim), axis=1)
                if bad.any() and keep_all:
                    emax = float(np.max(e)) if "e" in locals() and np.all(np.isfinite(e)) else math.inf
                    raise ValueError(f"overlap: an inserted particle's potential energy {emax:.4g} exceeds the bound "
                                     f"{lim:g} ({int(bad.sum())} molecules)")
                if not bad.any():
                    if limit is not None and len(cand) > int(limit):
                        cand = cand[:int(limit)]
                        continue
                    break
                cand = cand[~bad]
            else:
                raise ValueError("molecules: the insertion did not settle")
            self._next_mol = mol0 + len(cand)
            result["kept"] = cand
            result["keys"] = (np.arange(n0, self.n) if len(cand) else np.zeros(0, np.int64))
            result["atom_keys"] = self._key[n0:].reshape(len(cand), n) if len(cand) else np.zeros((0, n), np.int64)
        self._transaction(apply)
        kept = result["kept"]
        return kept, np.arange(self._next_mol - len(kept), self._next_mol), result["atom_keys"]

    def remove_molecule(self, mol):
        rows = np.flatnonzero(self._mol == int(mol))
        if len(rows) == 0:
            raise KeyError(f"no molecule {mol!r}")
        self.remove(self._key[rows])

    def molecules(self) -> dict:
        """{molecule key: atom keys}."""
        out = {}
        for mk in np.unique(self._mol[self._mol >= 0]):
            out[int(mk)] = self._key[self._mol == mk].copy()
        return out

    def topology(self) -> dict:
        """Bonds and angles by particle keys with their type names."""
        bt, at = list(self._bond_types), list(self._angle_types)
        return {"bonds": [(int(a), int(b), bt[t]) for (a, b), t in zip(self._bonds, self._bond_t)],
                "angles": [(int(a), int(b), int(c), at[t]) for (a, b, c), t in zip(self._angles, self._angle_t)]}

    # --- box, walls, piston, field, pair model --------------------------------------------------------------------
    def set_wall(self, axis, side, kind, T=None, term=None):
        """Set the wall on side "lo" or "hi" of a walled axis: "specular", "thermal" (temperature T) or "soft" (a
        wall term with ``tables`` and ``evaluate(z, P)``, a specular backstop behind it). Its counters restart."""
        a = self._axis(axis)
        if self.periodic[a]:
            raise ValueError(f"axis {_AX[a]} is periodic")
        if side not in ("lo", "hi"):
            raise ValueError("side: 'lo' or 'hi'")
        if kind not in _WALL_KINDS:
            raise ValueError(f"wall kind must be one of {_WALL_KINDS}")
        if kind == "thermal" and not (T is not None and T > 0 and math.isfinite(T)):
            raise ValueError("a thermal wall needs a temperature T > 0")
        if kind == "soft" and not callable(getattr(term, "evaluate", None)):
            raise ValueError("a soft wall needs a wall term")
        if self._piston is not None and self._piston["axis"] == a and side == "hi":
            raise ValueError("the hi side of this axis is the piston")

        def apply():
            old = self._walls.get(f"{_AX[a]}-{side}")
            if old is not None:
                self._balance["Q"] += old["heat"]
            w = self._new_wall(kind, T, term if kind == "soft" else None)
            w["t0"] = self.t
            self._walls[f"{_AX[a]}-{side}"] = w
        self._transaction(apply)

    def walls(self) -> dict:
        return {k: {"kind": w["kind"], "T": w["T"], "term": _term_data(w["term"])} for k, w in self._walls.items()}

    def set_boundary(self, axis, kind):
        """Make one axis periodic or bounded by walls at the current moment (review UX-ui U7: a wall or a piston placed
        on a periodic axis). ``"walls"``: specular walls at 0 and L_a; the pairs that interacted across the faces stop
        interacting (the potential energy changes by their terms: an edit, booked in the first-law balance as every
        edit). ``"periodic"``: the axis's walls go (their heat stays in the balance), the faces are joined and the
        positions wrapped; refused with the piston on this axis, and, as an insertion, when a particle near a face would
        overlap one across it (its energy above ``max_insert_energy``); the pair cutoff and charges are checked as at
        the start."""
        a = self._axis(axis)
        if kind not in ("periodic", "walls"):
            raise ValueError("boundary: 'periodic' or 'walls'")
        if (kind == "periodic") == bool(self.periodic[a]):
            return
        if kind == "periodic" and self._piston is not None and self._piston["axis"] == a:
            raise ValueError("the piston's axis cannot be made periodic (remove the piston first)")
        near = None
        if kind == "periodic" and self.n:
            reach = (float(np.max(self._tables["rc"])) if self._tables is not None else 0.0) + self.skin
            xa = self._x[:, a]
            near = self._key[(xa < reach) | (xa > self.L[a] - reach)]

        def apply():
            per = self.periodic.copy()
            per[a] = kind == "periodic"
            self.periodic = per
            for side in ("lo", "hi"):
                key = f"{_AX[a]}-{side}"
                if kind == "walls":
                    w = self._new_wall("specular")
                    w["t0"] = self.t
                    self._walls[key] = w
                else:
                    old = self._walls.pop(key, None)
                    if old is not None:
                        self._balance["Q"] += old["heat"]
            if kind == "periodic" and self.n:
                self._x, self._img = self._wrap(self._x, self._img)
        self._transaction(apply, new_keys=near)

    def _axis(self, axis):
        a = _AX.index(axis) if isinstance(axis, str) else int(axis)
        if not 0 <= a < self.dim:
            raise ValueError("no such axis")
        return a

    def set_piston(self, axis, X=None, mass=math.inf, p_ext=0.0, V=None, x_min=None):
        """Put a piston on the hi side of a walled axis (or change it): face at X, mass M (inf: driven with the
        velocity V the user sets), external pressure p_ext on its outer side, end stops x_min and L_a."""
        a = self._axis(axis)
        if self.periodic[a]:
            raise ValueError("a piston needs a walled axis")
        old = self._piston if (self._piston is not None and self._piston["axis"] == a) else None
        X = (old["X"] if old else self.L[a]) if X is None else float(X)
        V = (old["V"] if old else 0.0) if V is None else float(V)
        x_min = (old["x_min"] if old else 1e-3 * self.L[a]) if x_min is None else float(x_min)
        mass, p_ext = float(mass), float(p_ext)
        if not (0 < x_min <= X <= self.L[a] and mass > 0 and math.isfinite(p_ext) and math.isfinite(V)):
            raise ValueError("0 < x_min <= X <= L, mass > 0, finite p_ext and V")
        if self._piston is not None and self._piston["axis"] != a:
            raise ValueError("one piston per system (remove the other first)")
        if self.ramp_running() and self._ramp["L1"][a] != self._ramp["L0"][a]:
            raise ValueError(f"the box is being changed along axis {_AX[a]} (a ramp): stop it first")

        def apply():
            p = old or {"axis": a, "work": 0.0, "impulse": 0.0, "hits": 0, "t0": self.t, "stops": 0}
            p.update({"X": X, "V": V, "M": mass, "p_ext": p_ext, "x_min": x_min})
            self._piston = p
            gone = self._walls.pop(f"{_AX[a]}-hi", None)
            if gone is not None:   # its heat stays in the first-law balance (review B7-md M10)
                self._balance["Q"] += gone["heat"]
        self._transaction(apply)

    def remove_piston(self):
        """Replace the piston by a specular wall at L_a (its work so far stays in the first-law balance)."""
        if self._piston is None:
            return
        a = self._piston["axis"]

        def apply():
            self._balance["W"] += self._piston["work"]
            self._piston = None
            w = self._new_wall("specular")
            w["t0"] = self.t
            self._walls[f"{_AX[a]}-hi"] = w
        self._transaction(apply)

    def piston(self) -> dict | None:
        if self._piston is None:
            return None
        p = dict(self._piston)
        p["axis"] = _AX[p["axis"]]
        p["area"] = self._area(self._piston["axis"])
        return p

    def set_gravity(self, g):
        g = self._vec(g)

        def apply():
            self.g = g
        self._transaction(apply)

    def set_pair(self, term):
        """Change the pair model (any object with ``tables``, ``evaluate``; None: no pair forces)."""
        def apply():
            self.pair = term
        self._transaction(apply)

    def set_dt(self, dt):
        if not (dt > 0 and math.isfinite(dt)):
            raise ValueError("dt > 0")
        self._t_base = self.t
        self._n_since = 0
        self._dt = float(dt)

    def deform(self, L, mode="affine", max_bond_strain=None) -> dict:
        """Change the box lengths to ``L`` at the current time, in one jump (plan P16.1: a bench that never restarts;
        over a time: ``ramp_box``).

        ``"affine"``: the box and the matter in it are deformed together, axis by axis with lambda_a = L'_a / L_a: the
        positions x_a -> lambda_a x_a of every atom (frozen ones too; the lo face stays at 0) and the peculiar velocities
        v_a -> u_a + (v_a - u_a) / lambda_a (u: the centre-of-mass velocity along the axes whose momentum is conserved,
        else 0: that momentum is kept). For the motion relative to the centre of mass this is the canonical point
        transformation x -> lambda x, p -> p / lambda (phase-space volume kept); along an axis whose momentum is
        conserved the centre of mass itself is moved by lambda with its momentum kept, so the Jacobian of the whole map
        is lambda_a per such axis (review LB1-physics P9; tested). It is the volume step of Andersen's barostat in its
        scaled variables (rho = x / L and pi fixed while L changes, so the peculiar velocity goes as 1/L) and of the MTK
        barostat (Martyna, Tobias & Klein 1994, up to their O(1/N_f) factor); scaling the positions only (Berendsen's
        barostat) is not canonical and does no work on an ideal gas.

        Its energy change, to first order in delta_a = lambda_a - 1, is dE = -sum_a (2 K_aa + W^aff_aa) delta_a
        = -sum_a S_aa V delta_a (``affine_stress``: K the peculiar kinetic tensor, W^aff the virial of every force the
        deformation moves: pairs, Coulomb, bonds and angles over all their pairs, the soft walls' z F_z, the field's
        m g_a x_a). S equals the virial pressure of ``pressure`` - so that dE = -P dV - only where no field component
        along a changed axis, no soft wall across it and no frozen atom acts (``"virial_is_affine"``); otherwise they
        differ at first order (review LB1-physics P2: a field, soft walls, frozen atoms). A jump is not quasi-static:
        the matter is out of equilibrium after it and relaxes irreversibly (a 15 % compression and back of a
        Lennard-Jones fluid in single jumps leaves about 1.8 epsilon per atom as heat; the review's table); the
        quasi-static adiabatic work -int S dV is approached by a slow change, ``ramp_box``. For an ideal gas each jump
        is exactly adiabatic (K_aa L_a^2 kept; isotropic: T V^(2/d) = const, P V^((d+2)/d) = const). Refused along the
        piston's axis (move the piston, or use "wall"), while a ramp runs, where a bond's length would change by more
        than ``max_bond_strain`` (relative; atoms are scaled one by one, so bonds stretch with the box), and, as an
        insertion, where a particle's potential energy would exceed ``max_insert_energy`` (overlap), the pair cutoff
        would exceed half a periodic length, or a particle would leave a wall.

        ``"wall"``: on walled axes only, the hi wall (the piston's end stop on its axis) moves to L'_a; nothing else
        moves: empty space is added (a free expansion follows, irreversible by nature) or removed (refused where a
        particle would be beyond it). Specular and thermal walls do no work so; a soft wall's energy change is work.

        The energy change of either is booked as work done on the system (``energy_balance``: ``W_box``), not as an
        edit; the walls' and the piston's impulse counters (their pressures) restart, their heat and work stay.
        Returns {"mode", "lambda", "V0", "V1", "dE" (the work), "dK", "P0" (the virial tensor before), "P1" (after),
        "S0", "S1" (the affine stress before and after), "pdv" (affine: -(S0 + S1)/2 . dV_a per axis, summed: the
        trapezoid estimate of -int S dV, equal to dE to second order; None for "wall"), "pdv_virial" (the same with
        the virial pressure; None where undefined), "virial_is_affine", "bond_strain" (the largest relative change of
        a bond's length)}."""
        L_new = np.asarray(L, float).reshape(-1)
        if L_new.shape != (self.dim,) or not np.all((L_new > 0) & np.isfinite(L_new)):
            raise ValueError("box: dim positive finite lengths")
        if mode not in ("affine", "wall"):
            raise ValueError("mode: 'affine' or 'wall'")
        if self.ramp_running():
            raise ValueError("a box ramp is running: stop it first (stop_box_ramp)")
        lam = L_new / self.L
        changed = np.flatnonzero(L_new != self.L)
        p = self._piston
        if p is not None and p["axis"] in changed:
            if mode == "affine":
                raise ValueError(f"the piston's axis {_AX[p['axis']]}: move the piston (or mode 'wall': its end stop)")
            if L_new[p["axis"]] < p["X"]:
                raise ValueError(f"the piston's face {p['X']:.6g} lies beyond the new length {L_new[p['axis']]:.6g}")
        if mode == "wall":
            per = [_AX[a] for a in changed if self.periodic[a]]
            if per:
                raise ValueError(f"axis {', '.join(per)} is periodic: it has no wall to move")
        strain = 0.0
        if mode == "affine" and len(self._bonds) and len(changed):
            r = self._rows(self._bonds.reshape(-1)).reshape(-1, 2)
            dx = self._min_image(self._x[r[:, 1]] - self._x[r[:, 0]])
            b0 = np.sqrt(np.einsum("ij,ij->i", dx, dx))
            b1 = np.sqrt(np.einsum("ij,ij->i", dx * lam, dx * lam))
            strain = float(np.max(np.abs(b1 / np.where(b0 > 0, b0, 1.0) - 1.0)))
            if max_bond_strain is not None and strain > float(max_bond_strain):
                raise ValueError(f"a bond would change its length by {strain:.4g} (limit {float(max_bond_strain):g})")
        V0 = self.volume()
        P0 = self.pressure()["tensor"] if self.n else [0.0] * self.dim
        S0 = self.affine_stress() if self.n else [0.0] * self.dim
        K0 = self.kinetic_energy()
        out = {"mode": mode, "lambda": lam.tolist(), "V0": V0, "V1": V0, "dE": 0.0, "dK": 0.0, "P0": P0, "P1": P0,
               "S0": S0, "S1": S0, "pdv": 0.0, "pdv_virial": 0.0, "virial_is_affine": self.virial_is_affine(changed),
               "bond_strain": strain}
        if not len(changed):
            return out
        E_before = self.energy() if self._energy else 0.0
        # the soft walls' energy and an affine change move particles: checked as an insertion (overlap)
        moved = mode == "affine" or any(w["kind"] == "soft" for w in self._walls.values())

        def apply():
            if mode == "affine" and self.n:
                self._affine_map(lam)
            self.L = L_new.copy()
            for w in self._walls.values():
                w.update(impulse=0.0, t0=self.t)
            if self._piston is not None:
                self._piston.update(impulse=0.0, t0=self.t)
        self._transaction(apply, new_keys=self._key if (moved and self.n) else None)
        dE = (self.energy() - E_before) if self._energy else 0.0
        # the transaction booked dE as an edit (E0 += dE): it is work done on the system
        self._balance["E0"] -= dE
        self._balance["Wd"] = self._balance.get("Wd", 0.0) + dE
        V1 = self.volume()
        P1 = self.pressure()["tensor"] if self.n else [0.0] * self.dim
        S1 = self.affine_stress() if self.n else [0.0] * self.dim
        pdv = pdv_v = None   # a wall moved over empty space feels no force: no -P dV
        if mode == "affine":
            pdv, pdv_v = _trapezoid(S0, S1, V0, lam, changed), _trapezoid(P0, P1, V0, lam, changed)
        out.update(V1=V1, dE=dE, dK=self.kinetic_energy() - K0, P1=P1, S1=S1, pdv=pdv, pdv_virial=pdv_v)
        return out

    def _affine_map(self, lam):
        """x -> lambda x for every atom, the peculiar velocities of the mobile ones -> u + (v - u) / lambda (u: the
        centre-of-mass velocity along the conserved axes); the mean-square displacement's reference with them."""
        cons = self.momentum_conserved_axes()
        self._x = self._x * lam
        mob = self._mobile
        if np.any(mob):
            m = self._m[mob]
            v = self._v[mob]
            u = np.where(cons, (m[:, None] * v).sum(0) / m.sum(), 0.0)
            self._v[mob] = u + (v - u) / lam
        if self._msd_ref is not None:
            self._msd_ref = self._msd_ref * lam

    def affine_stress(self) -> list:
        """S_aa = (2 K_aa + W^aff_aa) / V per axis: minus the derivative of the energy along the affine deformation of
        ``deform`` per volume, -(1/V) dH/d(delta_a) (K: the peculiar kinetic tensor of ``kinetic_tensor``; W^aff: the
        virial of every force that deformation moves - pairs, Coulomb, bonds and angles over all their pairs, the soft
        walls' sum z F_z, the field's sum m g_a x_a). It is the virial pressure tensor where ``virial_is_affine``."""
        if self._vir_aff is None:   # a state saved before the affine virial existed: computed now, the state untouched
            keep = {k: getattr(self, k) for k in ("_f", "_vir", "_energy", "_wallf", "_nl")}
            keep_stats = dict(self._stats)
            self._compute_forces()
            va = self._vir_aff
            for k, v in keep.items():
                setattr(self, k, v)
            self._stats = keep_stats
            self._vir_aff = va
        return [float(z) for z in (self.kinetic_tensor() + np.asarray(self._vir_aff, float)) / self.volume()]

    def virial_is_affine(self, axes=None) -> bool:
        """Is the virial pressure (``pressure``) the affine stress (``affine_stress``) along ``axes`` (default all):
        no frozen atom, no field component along them, no soft wall across them."""
        axes = range(self.dim) if axes is None else [int(a) for a in axes]
        if self.n and not np.all(self._mobile):
            return False
        for a in axes:
            if self.g[a] != 0.0:
                return False
            if any(w["kind"] == "soft" for k, w in self._walls.items() if k[0] == _AX[a]):
                return False
        return True

    # --- a change of the box over a time (review LB1-physics P3) -------------------------------------------------
    RAMP_MAX_STRAIN = 1e-3   # the largest relative change of a length in one step of a ramp

    def ramp_box(self, L, duration) -> dict:
        """Change the box lengths to ``L`` over the world time ``duration`` from now, linearly in time (review
        LB1-physics P3: a quasi-static change at a rate the experimenter sets). After every step the box and the
        matter are deformed affinely from L(t) to L(t + dt), exactly as ``deform``'s "affine" (``_affine_map``), the
        forces and energies are computed at once at the new positions, and the energy change of that substep is booked
        as the work W_box: the work is the exact energy change, summed over the substeps (the record's "W"; "pdv" sums
        the trapezoid -(S + S')/2 dV of the affine stress, ``affine_stress``, the quasi-static work's estimate). As
        duration -> infinity the change tends to the quasi-static adiabat (the net work of a compress-and-return cycle
        tends to 0; tested against single jumps and, for the ideal gas, against a slow driven piston); a finite rate
        dissipates (the matter cannot follow), the more the faster. Refused as ``deform``'s affine mode along the
        piston's axis and where the pair cutoff would exceed half a periodic length at the end, and when one step
        would change a length by more than ``RAMP_MAX_STRAIN`` (then ``deform`` is the jump); a ramp already running
        is stopped first (its work so far stays). While it runs, ``deform`` and a piston on a changing axis are
        refused; the walls' impulse counters run on (their pressure: the average over the changing box). A substep
        that would make a force non-finite, or the cutoff exceed half a periodic length, is not made: the ramp stops
        there (``box_ramp()["stopped"]``). Returns the ramp's record (``box_ramp``)."""
        L1 = np.asarray(L, float).reshape(-1)
        if L1.shape != (self.dim,) or not np.all((L1 > 0) & np.isfinite(L1)):
            raise ValueError("box: dim positive finite lengths")
        duration = float(duration)
        if not (duration > 0 and math.isfinite(duration)):
            raise ValueError("a ramp needs a finite duration > 0 (a jump: deform)")
        if self.ramp_running():
            self.stop_box_ramp("replaced")
        L0 = self.L.copy()
        changed = np.flatnonzero(L1 != L0)
        p = self._piston
        if p is not None and p["axis"] in changed:
            raise ValueError(f"the piston's axis {_AX[p['axis']]}: move the piston (or mode 'wall': its end stop)")
        per_step = float(np.max(np.abs(L1 - L0) / np.minimum(L0, L1))) * self._dt / duration if len(changed) else 0.0
        if per_step > self.RAMP_MAX_STRAIN:
            raise ValueError(f"a ramp of {duration:.4g} changes a length by {per_step:.3g} per step (limit "
                             f"{self.RAMP_MAX_STRAIN:g}): longer duration, or a jump (deform)")
        if self._tables is not None and np.any(self.periodic):
            rc = float(np.max(self._tables["rc"])) + self.skin
            low = float(np.min(np.minimum(L0, L1)[self.periodic]))
            if rc > 0.5 * low:
                raise ValueError(f"the pair cutoff + skin {rc:.4g} exceeds half a periodic box length {0.5 * low:.4g}")
        n_prev = self._ramp["n"] if self._ramp is not None else 0
        self._ramp = {"n": n_prev + 1, "L0": L0, "L1": L1.copy(), "t0": self.t, "t1": self.t + duration,
                      "W": 0.0, "pdv": 0.0, "steps": 0, "running": bool(len(changed)), "done": not len(changed),
                      "t_end": None if len(changed) else self.t, "stopped": None, "V0": self.volume(),
                      "K0": self.kinetic_energy(), "virial_is_affine": self.virial_is_affine(changed)}
        return self.box_ramp()

    def ramp_running(self) -> bool:
        return self._ramp is not None and bool(self._ramp["running"])

    def box_ramp(self) -> dict | None:
        """The latest ramp's record (a copy; None if there was none): "n" (its number), "L0", "L1", "t0", "t1", "L" (the
        box now), "W" (the work booked so far), "pdv" (the trapezoid of -int S dV), "steps", "running", "done", "t_end"
        (when it ended), "stopped" (why it stopped early, or None), "V0", "K0", "virial_is_affine"."""
        if self._ramp is None:
            return None
        out = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in self._ramp.items()}
        out["L"] = self.L.tolist()
        return out

    def stop_box_ramp(self, reason="stopped"):
        """Stop a running ramp where the box is now (its work so far stays booked)."""
        if self.ramp_running():
            self._ramp.update(running=False, stopped=str(reason), t_end=self.t)

    def _ramp_substep(self):
        r = self._ramp
        t = self.t
        f = (t - r["t0"]) / (r["t1"] - r["t0"])
        last = f >= 1.0 - 1e-12
        L_new = r["L1"].copy() if last else r["L0"] + (r["L1"] - r["L0"]) * f
        if self._tables is not None and np.any(self.periodic):
            rc = float(np.max(self._tables["rc"])) + self.skin
            if rc > 0.5 * float(np.min(L_new[self.periodic])):
                self.stop_box_ramp("cutoff")
                return
        lam = L_new / self.L
        keep = {k: getattr(self, k) for k in ("_x", "_v", "L", "_msd_ref", "_f", "_vir", "_vir_aff", "_energy",
                                               "_wallf", "_nl")}
        keep_stats = dict(self._stats)
        E0 = self.energy()
        S0 = self.affine_stress()
        V0 = self.volume()
        changed = np.flatnonzero(lam != 1.0)
        self._v = self._v.copy()
        self._affine_map(lam)
        self.L = L_new
        try:
            self._compute_forces()
            if not np.all(np.isfinite(self._f)):
                raise FloatingPointError("non-finite forces")
        except FloatingPointError as e:
            for k, v in keep.items():
                setattr(self, k, v)
            self._stats = keep_stats
            self.stop_box_ramp(f"refused: {e}")
            return
        dE = self.energy() - E0
        self._balance["Wd"] = self._balance.get("Wd", 0.0) + dE
        r["W"] += dE
        r["pdv"] += _trapezoid(S0, self.affine_stress(), V0, lam, changed)
        r["steps"] += 1
        self._ramp_steps += 1
        if last:
            r.update(running=False, done=True, t_end=t)

    def set_exclusions(self, exclude):
        if exclude not in _EXCLUDE:
            raise ValueError(f"exclude must be one of {_EXCLUDE}")

        def apply():
            self.exclude = exclude
        self._transaction(apply)

    # --- thermostats ----------------------------------------------------------------------------------------------
    def add_thermostat(self, kind, T, tau=None, gamma=None, region=None, species=None):
        """A heat bath: "csvr" (relaxation time tau) or "langevin" (friction gamma), at temperature T, acting on the
        particles inside ``region`` = (lo, hi) (default everywhere) and of the given species (default all).
        Returns its key."""
        b = self._check_bath({"kind": kind, "T": T, "tau": tau, "gamma": gamma, "region": region,
                              "species": species})
        key = self._next_bath

        def apply():
            b.update({"heat": 0.0})
            self._baths[key] = b
            self._next_bath += 1
        self._transaction(apply)
        return key

    def _check_bath(self, b):
        if b["kind"] not in _BATHS:
            raise ValueError(f"thermostat kind must be one of {_BATHS}")
        T = float(b["T"])
        if not (T >= 0 and math.isfinite(T)):
            raise ValueError("T must be finite and >= 0")
        out = {"kind": b["kind"], "T": T, "tau": None, "gamma": None, "region": None, "species": None}
        if b["kind"] == "csvr":
            if not (b.get("tau") is not None and float(b["tau"]) > 0):
                raise ValueError("a CSVR bath needs tau > 0")
            out["tau"] = float(b["tau"])
        else:
            if not (b.get("gamma") is not None and float(b["gamma"]) > 0):
                raise ValueError("a Langevin bath needs gamma > 0")
            out["gamma"] = float(b["gamma"])
        if b.get("region") is not None:
            lo, hi = self._vec(b["region"][0]), self._vec(b["region"][1])
            if not np.all(hi > lo):
                raise ValueError("region: hi > lo")
            out["region"] = [lo.tolist(), hi.tolist()]
        if b.get("species") is not None:
            sp = [b["species"]] if isinstance(b["species"], str) else list(b["species"])
            for s in sp:
                self._species_index(s)
            out["species"] = sp
        return out

    def set_thermostat(self, key, **changes):
        if key not in self._baths:
            raise KeyError(f"no thermostat {key!r}")
        old = self._baths[key]
        b = self._check_bath({**old, **changes})

        def apply():
            b["heat"] = old["heat"]
            self._baths[key] = b
        self._transaction(apply)

    def remove_thermostat(self, key):
        if key not in self._baths:
            raise KeyError(f"no thermostat {key!r}")

        def apply():
            self._balance["Q"] += self._baths[key]["heat"]
            del self._baths[key]
        self._transaction(apply)

    def thermostats(self) -> dict:
        return {k: dict(b) for k, b in self._baths.items()}

    # --- transactions ---------------------------------------------------------------------------------------------
    _STATE = ("L", "periodic", "pair", "exclude", "g", "rng", "_species", "_bond_types", "_angle_types", "_key", "_typ",
              "_mol", "_x", "_img", "_v", "_f", "_next_key", "_next_mol", "_bonds", "_bond_t", "_angles", "_angle_t",
              "_walls", "_piston", "_baths", "_next_bath", "_energy", "_vir", "_vir_aff", "_wallf", "_balance",
              "_msd_ref", "_nl", "_stats", "_m", "_invm", "_mobile", "_tables", "_excl", "_wtables", "_p_ref",
              "_p_ref_step", "_p_ref_ramp", "_ramp", "_ramp_steps")

    def _transaction(self, apply, new_keys=None, max_energy=None):
        if self._nl is not None and self._nl.pop("dev", None) is not None:
            backend.release()
        snap = {k: copy.deepcopy(getattr(self, k, None)) for k in self._STATE}
        E_before = self.energy() if self._energy else 0.0
        try:
            apply()
            self._derived()
            self._check_inside()
            self._compute_forces()
            if not np.all(np.isfinite(self._f)):
                raise FloatingPointError("non-finite forces")
            if new_keys is not None and len(new_keys):
                rows = self._rows(new_keys)
                e = self._insert_energy(rows)
                lim = self.max_insert_energy if max_energy is None else float(max_energy)
                if e > lim:
                    raise ValueError(f"overlap: an inserted particle's potential energy {e:.4g} exceeds "
                                     f"{'max_insert_energy' if max_energy is None else 'the limit'} = {lim:g}")
            # an edit changes the Hamiltonian or the state: the first-law balance continues from here
            self._balance["E0"] += self.energy() - E_before
            self._p_ref = self.momentum()      # and the momentum's conservation is checked from here
            self._p_ref_step = self.nstep
            self._p_ref_ramp = self._ramp_steps
        except FloatingPointError as e:
            for k, val in snap.items():
                setattr(self, k, val)
            raise ValueError(f"refused: {e}") from e
        except BaseException:
            for k, val in snap.items():
                setattr(self, k, val)
            raise

    def _derived(self):
        """Per-particle masses, the pair model's tables, exclusion codes, wall tables."""
        ns = len(self._species)
        mass = np.array([s["mass"] for s in self._species]) if ns else np.zeros(0)
        self._m = mass[self._typ] if self.n else np.zeros(0)
        self._mobile = np.isfinite(self._m)
        self._invm = np.where(self._mobile, 1.0 / np.where(self._mobile, self._m, 1.0), 0.0)
        if ns and self.pair is not None:
            sig = np.array([s["sigma"] for s in self._species])
            eps = np.array([s["epsilon"] for s in self._species])
            self._tables = self.pair.tables(sig, eps)
            rcmax = float(np.max(self._tables["rc"]))
            if np.any(self.periodic) and rcmax + self.skin > 0.5 * float(np.min(self.L[self.periodic])):
                raise ValueError(f"the pair cutoff + skin {rcmax + self.skin:.4g} exceeds half a periodic box "
                                 f"length {0.5 * float(np.min(self.L[self.periodic])):.4g}")
        else:
            self._tables = None
        self._wtables = {}
        if ns:
            sig = np.array([s["sigma"] for s in self._species])
            eps = np.array([s["epsilon"] for s in self._species])
            for k, w in self._walls.items():
                if w["kind"] == "soft":
                    self._wtables[k] = w["term"].tables(sig, eps)
        q = np.array([s["charge"] for s in self._species]) if ns else np.zeros(0)
        if self.n and np.any(q[self._typ] != 0.0) and np.any(self.periodic):
            raise ValueError("charges in a box with a periodic axis: the Coulomb lattice sum (Ewald) is not "
                             "implemented; use walls on every axis")
        self._excl = self._exclusions()
        self._nl = None

    def _check_inside(self):
        for a in range(self.dim):
            if self.periodic[a]:
                continue
            hi = self._piston["X"] if (self._piston is not None and self._piston["axis"] == a) else self.L[a]
            if np.any(self._x[:, a] < 0.0) or np.any(self._x[:, a] > hi):
                raise ValueError(f"a particle outside the walls on axis {_AX[a]}")

    def _exclusions(self):
        """Sorted int64 codes (min key << 32 | max key) of the excluded pairs (mode "bonded"), or None."""
        if self.exclude != "bonded" or len(self._bonds) == 0:
            return None
        b = self._bonds
        pairs = [np.sort(b, axis=1)]
        # 1-3: two bonds sharing an atom
        e = np.vstack([b, b[:, ::-1]])           # directed edges (u, w)
        order = np.argsort(e[:, 0], kind="stable")
        e = e[order]
        u = e[:, 0]
        starts = np.flatnonzero(np.r_[True, u[1:] != u[:-1]])
        ends = np.r_[starts[1:], len(u)]
        thr = []
        for s0, s1 in zip(starts, ends):
            if s1 - s0 > 1:
                nbrs = e[s0:s1, 1]
                ii, jj = np.triu_indices(len(nbrs), 1)
                thr.append(np.stack([nbrs[ii], nbrs[jj]], 1))
        if thr:
            pairs.append(np.sort(np.vstack(thr), axis=1))
        P = np.vstack(pairs)
        codes = (P[:, 0] << 32) | P[:, 1]
        return np.unique(codes)

    def _insert_energy(self, rows):
        """The largest potential energy of one of the particles ``rows`` (half of each pair and Coulomb term, a
        third of each angle, half of each bond, walls), for the overlap refusal."""
        e = self._per_particle_energy()
        return float(np.max(e[rows]))

    # --- the forces -----------------------------------------------------------------------------------------------
    def _build_list(self):
        had_dev = self._nl is not None and self._nl.pop("dev", None) is not None
        if had_dev:
            backend.release()   # the device copies of the old list go back to the driver
        rc = float(np.max(self._tables["rc"]))
        rl = rc + self.skin
        i, j = cells.pair_list(self._x, self.L, self.periodic, rl)
        if not np.all(self._mobile):   # frozen-frozen pairs move nothing (their energy is a constant): not listed
            keep = self._mobile[i] | self._mobile[j]
            i, j = i[keep], j[keep]
        if self.exclude == "molecule":
            keep = ~((self._mol[i] == self._mol[j]) & (self._mol[i] >= 0))
            i, j = i[keep], j[keep]
        elif self._excl is not None:
            ki, kj = self._key[i], self._key[j]
            codes = (np.minimum(ki, kj) << 32) | np.maximum(ki, kj)
            keep = ~np.isin(codes, self._excl)
            i, j = i[keep], j[keep]
        ns = len(self._species)
        T = self._tables
        names = [k for k in ("s2", "eps4", "rc2", "ushift", "fshift", "sig", "eps") if k in T]
        if ns == 1:
            P = {k: float(T[k][0, 0]) for k in names}
        else:
            tp = self._typ[i] * ns + self._typ[j]
            P = {k: T[k].reshape(-1)[tp] for k in names}
        self._nl = {"i": i, "j": j, "P": P, "x_ref": self._x + self._img * self.L, "x_build": self._x.copy(),
                    "rlist": rl}
        self._stats["rebuilds"] += 1
        self._stats["steps_since_build"] = 0
        self._stats["pairs"] = int(len(i))

    def _list_valid(self) -> bool:
        if self._nl is None:
            return False
        dx = (self._x + self._img * self.L) - self._nl["x_ref"]
        if dx.shape[0] == 0:
            return True
        return float(np.max(np.einsum("ij,ij->i", dx, dx))) <= (0.5 * self.skin) ** 2

    def _min_image(self, dx):
        for a in np.flatnonzero(self.periodic):
            dx[:, a] -= self.L[a] * np.rint(dx[:, a] / self.L[a])
        return dx

    def _pair_terms(self, x, xp=np, nl_arrays=None):
        """Pair term over the Verlet list: (i, j, fr, dx, u, r2) for the pairs (u, fr zero beyond r_c). The same
        elementwise operations on NumPy or CuPy arrays (``xp``): IEEE results identical on both."""
        i, j, P = nl_arrays if nl_arrays is not None else (self._nl["i"], self._nl["j"], self._nl["P"])
        dx = x[j] - x[i]
        for a in np.flatnonzero(self.periodic):
            dx[:, a] -= self.L[a] * xp.rint(dx[:, a] / self.L[a])
        r2 = dx[:, 0] * dx[:, 0]
        for a in range(1, self.dim):
            r2 = r2 + dx[:, a] * dx[:, a]
        if bool(xp.any(r2 == 0.0)):
            raise FloatingPointError("two interacting particles at the same point")
        u, fr = self.pair.evaluate(r2, P)
        return i, j, fr, dx, u, r2

    def _pair_device(self):
        """The device the pair forces run on (kernel "md.pair_forces": auto by the number of pairs)."""
        npairs = len(self._nl["i"])
        foot = npairs * 8 * (2 * self.dim + 12) + self.n * 8 * 3 * self.dim
        ch = backend.choose(KERNEL, npairs, footprint=foot,
                            force="cpu" if self._force_cpu else None, why=self._force_cpu or "")
        return ch

    def _pair_gpu(self, x, f, vir, E):
        """The pair forces on GPU 0: the elementwise part as on the CPU, the per-particle sums by a kernel that adds
        each particle's pair contributions in increasing pair order from 0.0 - the order of numpy.bincount - so the
        forces equal the CPU's bit for bit (energy and virial sums: within rounding)."""
        cp = backend._CP
        nl = self._nl
        dev = nl.get("dev")
        if dev is None:
            dev = {"i": cp.asarray(nl["i"]), "j": cp.asarray(nl["j"]),
                   "P": {k: (v if np.isscalar(v) else cp.asarray(v)) for k, v in nl["P"].items()}}
            for side in ("i", "j"):
                idx = nl[side]
                order = np.argsort(idx, kind="stable").astype(np.int32)
                off = np.concatenate([[0], np.cumsum(np.bincount(idx, minlength=self.n))]).astype(np.int64)
                dev["o" + side], dev["s" + side] = cp.asarray(order), cp.asarray(off)
            nl["dev"] = dev
        xg = cp.asarray(x)
        i, j, fr, dx, u, r2 = self._pair_terms(xg, cp, (dev["i"], dev["j"], dev["P"]))
        n = self.n
        out = cp.empty(n, dtype=cp.float64)
        threads = 128
        blocks = (n + threads - 1) // threads
        for a in range(self.dim):
            w = cp.ascontiguousarray(fr * dx[:, a])
            _seg_kernel()((blocks,), (threads,), (w, dev["oj"], dev["sj"], dev["oi"], dev["si"], out, np.int32(n)))
            f[:, a] += cp.asnumpy(out)
        vir += cp.asnumpy(cp.stack([cp.sum(fr * dx[:, a] * dx[:, a]) for a in range(self.dim)]))
        E["pair"] = float(cp.sum(u))
        us = nl["P"]["ushift"]
        if np.any(np.asarray(us) != 0.0):
            E["pair_shift"] = float(cp.sum(cp.where(r2 < dev["P"]["rc2"], dev["P"]["ushift"], 0.0)))

    def _compute_forces(self, per_particle=False):
        """Forces at the current positions; energies by part and the virial (diagonal). With ``per_particle``,
        returns the potential energy of each particle (pair and Coulomb halves, bonded terms split equally, walls,
        no field) instead of storing anything."""
        n, d = self.n, self.dim
        x = self._x
        f = np.zeros((n, d))
        vir = np.zeros(d)
        E = {"pair": 0.0, "pair_shift": 0.0, "coulomb": 0.0, "bond": 0.0, "angle": 0.0, "wall": 0.0, "field": 0.0}
        pe = np.zeros(n) if per_particle else None
        wallf = {}
        if n >= 2 and self.pair is not None and self._tables is not None:
            if not self._list_valid():
                self._build_list()
            ch = None if per_particle else self._pair_device()
            if ch is not None:
                self._device = ch.device
            if ch is not None and ch.device == "gpu":
                try:
                    self._pair_gpu(x, f, vir, E)
                    ch = "done"
                except Exception as e:  # noqa: BLE001 - out of GPU memory or a driver error: redo on the CPU
                    if not backend.is_out_of_memory(e):
                        raise
                    backend.release()
                    backend.choose(KERNEL, len(self._nl["i"]), force="cpu", why=T("GPU: out of memory → CPU"))
                    f[:] = 0.0
                    vir[:] = 0.0
                    self._device = "cpu"
            if ch != "done":
                i, j, fr, dx, u, r2 = self._pair_terms(x)
                for a in range(d):
                    w = fr * dx[:, a]
                    f[:, a] += np.bincount(j, weights=w, minlength=n) - np.bincount(i, weights=w, minlength=n)
                vir += np.array([np.sum(fr * dx[:, a] * dx[:, a]) for a in range(d)])
                E["pair"] = float(np.sum(u))
                us = self._nl["P"]["ushift"]
                if np.any(np.asarray(us) != 0.0):
                    inside = r2 < self._nl["P"]["rc2"]
                    E["pair_shift"] = float(np.sum(np.where(inside, us, 0.0)))
                if per_particle:
                    pe += 0.5 * (np.bincount(i, weights=u, minlength=n) + np.bincount(j, weights=u, minlength=n))
        self._coulomb(x, f, vir, E, pe)
        self._bonded(x, f, vir, E, pe)
        # the affine virial (review LB1-physics P2): -dU/d(delta_a) of the deformation x_a -> (1 + delta_a) x_a of every
        # atom (frozen ones too, as ``deform`` moves them) with the box: the pair, Coulomb and bonded terms over all
        # their pairs (minimum image), the soft walls' sum z F_z (the hi wall moves with the box) and the field's
        # sum m g_a x_a (unwrapped); with the kinetic tensor it gives deform's first-order work exactly
        vir_aff = vir.copy()
        if not per_particle and n and not np.all(self._mobile):
            # frozen atoms are external bodies to the moving ones (review B7-md M13): Clausius' virial of the mobile
            # atoms is sum_mobile x_i . F_i (pair, Coulomb and bonded forces; the walls' and the field's apart), which
            # is defined along walled axes only (origin at the lo wall); along a periodic axis it is undefined (NaN)
            mob = self._mobile
            vir = np.where(self.periodic, np.nan, np.einsum("ij,ij->j", x[mob], f[mob]))
        self._soft_walls(x, f, E, pe, wallf, vir_aff)
        if np.any(self.g != 0.0) and n:
            mob = self._mobile
            f[mob] += self._m[mob, None] * self.g[None, :]
            xu = x + self._img * self.L
            E["field"] = float(-np.sum(self._m[mob] * (xu[mob] @ self.g)))
            vir_aff += self.g * np.einsum("i,ij->j", self._m[mob], xu[mob])
        if per_particle:
            return pe
        self._f = f
        self._vir = vir
        self._vir_aff = vir_aff
        self._energy = E
        self._wallf = wallf

    def _per_particle_energy(self):
        return self._compute_forces(per_particle=True)

    def _coulomb(self, x, f, vir, E, pe):
        if not self._species or self.n < 2:
            return
        q = np.array([s["charge"] for s in self._species])[self._typ]
        c = np.flatnonzero(q != 0.0)
        if len(c) < 2:
            return
        n = self.n
        ii, jj = np.triu_indices(len(c), 1)
        i, j = c[ii], c[jj]
        if self.exclude == "molecule":
            keep = ~((self._mol[i] == self._mol[j]) & (self._mol[i] >= 0))
            i, j = i[keep], j[keep]
        elif self._excl is not None:
            ki, kj = self._key[i], self._key[j]
            keep = ~np.isin((np.minimum(ki, kj) << 32) | np.maximum(ki, kj), self._excl)
            i, j = i[keep], j[keep]
        dx = x[j] - x[i]
        r2 = np.einsum("ij,ij->i", dx, dx)
        if np.any(r2 == 0.0):
            raise FloatingPointError("two charges at the same point")
        r = np.sqrt(r2)
        qq = q[i] * q[j]
        u = qq / r
        fr = u / r2
        w = fr[:, None] * dx
        for a in range(self.dim):
            f[:, a] += np.bincount(j, weights=w[:, a], minlength=n) - np.bincount(i, weights=w[:, a], minlength=n)
        vir += np.einsum("i,ij->j", fr, dx * dx)
        E["coulomb"] = float(np.sum(u))
        if pe is not None:
            pe += 0.5 * (np.bincount(i, weights=u, minlength=n) + np.bincount(j, weights=u, minlength=n))

    def _bonded(self, x, f, vir, E, pe):
        n = self.n
        if len(self._bonds):
            rows = self._rows(self._bonds.reshape(-1)).reshape(-1, 2)
            bt = list(self._bond_types.values())
            for t in np.unique(self._bond_t):
                sel = self._bond_t == t
                i, j = rows[sel, 0], rows[sel, 1]
                dx = self._min_image(x[j] - x[i])
                r = np.sqrt(np.einsum("ij,ij->i", dx, dx))
                if np.any(r == 0.0):
                    raise FloatingPointError("two bonded atoms at the same point")
                u, mdu = bt[t].evaluate(r)
                u = np.broadcast_to(u, r.shape)
                fr = mdu / r
                w = fr[:, None] * dx
                for a in range(self.dim):
                    f[:, a] += np.bincount(j, weights=w[:, a], minlength=n) - np.bincount(i, weights=w[:, a],
                                                                                         minlength=n)
                vir += np.einsum("i,ij->j", fr, dx * dx)
                E["bond"] += float(np.sum(u))
                if pe is not None:
                    pe += 0.5 * (np.bincount(i, weights=u, minlength=n) + np.bincount(j, weights=u, minlength=n))
        if len(self._angles):
            rows = self._rows(self._angles.reshape(-1)).reshape(-1, 3)
            at = list(self._angle_types.values())
            for t in np.unique(self._angle_t):
                sel = self._angle_t == t
                i, j, k = rows[sel, 0], rows[sel, 1], rows[sel, 2]
                a_ = self._min_image(x[i] - x[j])
                b_ = self._min_image(x[k] - x[j])
                la = np.sqrt(np.einsum("ij,ij->i", a_, a_))
                lb = np.sqrt(np.einsum("ij,ij->i", b_, b_))
                if np.any(la == 0.0) or np.any(lb == 0.0):
                    raise FloatingPointError("an angle with coincident atoms")
                cos = np.clip(np.einsum("ij,ij->i", a_, b_) / (la * lb), -1.0, 1.0)
                theta = np.arccos(cos)
                u, dudc = at[t].evaluate(theta, cos)
                u = np.broadcast_to(u, la.shape)
                dci = b_ / (la * lb)[:, None] - (cos / (la * la))[:, None] * a_
                dck = a_ / (la * lb)[:, None] - (cos / (lb * lb))[:, None] * b_
                Fi = -dudc[:, None] * dci
                Fk = -dudc[:, None] * dck
                Fj = -(Fi + Fk)
                for a in range(self.dim):
                    f[:, a] += (np.bincount(i, weights=Fi[:, a], minlength=n)
                                + np.bincount(j, weights=Fj[:, a], minlength=n)
                                + np.bincount(k, weights=Fk[:, a], minlength=n))
                vir += np.einsum("ij,ij->j", a_, Fi) + np.einsum("ij,ij->j", b_, Fk)
                E["angle"] += float(np.sum(u))
                if pe is not None:
                    for r_ in (i, j, k):
                        pe += np.bincount(r_, weights=u / 3.0, minlength=n)

    def _soft_walls(self, x, f, E, pe, wallf, vir_aff=None):
        n = self.n
        for key, w in self._walls.items():
            if w["kind"] != "soft" or n == 0:
                continue
            a = _AX.index(key[0])
            z = x[:, a] if key.endswith("lo") else self.L[a] - x[:, a]
            T = self._wtables[key]
            P = {k: T[k][self._typ] for k in ("zc", "sw", "ew", "uc")}
            zz = np.maximum(z, 1e-300)
            u, fz = w["term"].evaluate(zz, P)
            if not np.all(np.isfinite(fz)):
                raise FloatingPointError("a particle on a soft wall's plane")
            sgn = 1.0 if key.endswith("lo") else -1.0
            f[:, a] += sgn * fz
            E["wall"] += float(np.sum(u))
            wallf[key] = float(np.sum(fz[self._mobile])) if n else 0.0   # outward force on the wall
            if vir_aff is not None:
                vir_aff[a] += float(np.sum(fz * z))    # u(z) with z -> (1 + delta) z: -dU/d(delta) = sum z F_z
            if pe is not None:
                pe += u

    # --- time -----------------------------------------------------------------------------------------------------
    def step(self, n: int = 1):
        """n steps of dt."""
        for _ in range(int(n)):
            self._step()

    def advance(self, t_target) -> int:
        """Steps until the world time is the last step time <= t_target (+ a rounding allowance); returns the number
        of steps taken."""
        k = int(math.floor((float(t_target) - self.t) / self._dt + 1e-9))
        if k < 0:
            raise ValueError("time runs forward")
        self.step(k)
        return k

    def _step(self):
        t0 = time.perf_counter()
        h = self._dt
        self._o_csvr(0.5 * h)
        self._kick(0.5 * h)
        self._drift(0.5 * h)
        self._o_langevin(h)
        self._drift(0.5 * h)
        self._compute_forces()
        if not np.all(np.isfinite(self._f)):
            raise FloatingPointError("non-finite forces: the time step is too large or particles overlap")
        self._kick(0.5 * h)
        self._o_csvr(0.5 * h)
        self._n_since += 1
        self.nstep += 1
        if self._ramp is not None and self._ramp["running"]:
            self._ramp_substep()
        self._stats["steps_since_build"] += 1
        self._stats["seconds"] += time.perf_counter() - t0
        self._stats["timed_steps"] += 1

    def _kick(self, h):
        if self.n:
            self._v += h * self._f * self._invm[:, None]
        for key, fw in self._wallf.items():
            self._walls[key]["impulse"] += fw * h
        p = self._piston
        if p is not None and math.isfinite(p["M"]):
            a = p["axis"]
            p["V"] += h * (-p["p_ext"] * self._area(a) + p["M"] * self.g[a]) / p["M"]

    def _area(self, a):
        return float(np.prod(np.delete(self.L, a))) if self.dim > 1 else 1.0

    def _drift(self, h):
        if self.n == 0:
            if self._piston is not None:
                self._piston_free(h)
            return
        x = self._x + h * self._v
        mob = self._mobile
        x[~mob] = self._x[~mob]
        self._x = x
        if np.any(~self.periodic):
            self._walls_drift(h, np.flatnonzero(mob))
        if self._piston is not None:
            self._piston_drift(h)
            if np.any(~self.periodic):
                self._walls_drift(h, np.flatnonzero(mob))
        per = np.flatnonzero(self.periodic)
        if len(per):
            xs = self._x[:, per]
            k = np.floor(xs / self.L[per]).astype(np.int64)
            if np.any(k):
                xs = xs - k * self.L[per]
                xs = np.where(xs >= self.L[per], xs - self.L[per], xs)
                xs = np.where(xs < 0.0, 0.0, xs)
                self._x[:, per] = xs
                self._img[:, per] += k

    def _plane(self, key):
        a = _AX.index(key[0])
        return a, (0.0 if key.endswith("lo") else self.L[a])

    def _walls_drift(self, h, rows):
        """Collisions with the fixed walls during the drift just made (straight segments of length h): earliest
        first per particle, repeated until no particle is beyond a wall."""
        keys = list(self._walls)
        for _ in range(64):
            x = self._x[rows]
            v = self._v[rows]
            tau = np.full((len(rows), len(keys)), -np.inf)   # time since crossing the plane (on the last segment)
            for c, key in enumerate(keys):
                a, pl = self._plane(key)
                if key.endswith("lo"):
                    beyond = x[:, a] < pl
                else:
                    beyond = x[:, a] > pl
                if np.any(beyond):
                    with np.errstate(divide="ignore", invalid="ignore"):
                        tc = (x[:, a] - pl) / v[:, a]
                    tau[:, c] = np.where(beyond & (v[:, a] != 0.0), np.minimum(tc, h), -np.inf)
            if not np.any(np.isfinite(tau)):
                return
            c_best = np.argmax(tau, axis=1)
            t_best = tau[np.arange(len(rows)), c_best]
            for c, key in enumerate(keys):
                sel = np.flatnonzero((c_best == c) & np.isfinite(t_best))
                if len(sel):
                    self._wall_event(key, rows[sel], t_best[sel])
        raise FloatingPointError("a particle crossed the walls more than 64 times in one drift (dt too large)")

    def _wall_event(self, key, r, s):
        """Particles r crossed the wall ``key`` a time s ago (on their straight segment): reflect or re-emit."""
        w = self._walls[key]
        a, pl = self._plane(key)
        lo = key.endswith("lo")
        v_old = self._v[r].copy()
        m = self._m[r]
        if w["kind"] in ("specular", "soft"):
            self._v[r, a] = -v_old[:, a]
            self._x[r, a] = 2.0 * pl - self._x[r, a]
            if w["kind"] == "soft":
                self._stats["backstop_hits"] += len(r)
        else:
            T = w["T"]
            sd = np.sqrt(T / m)
            vn = sd * np.sqrt(-2.0 * np.log1p(-self.rng.random(len(r))))
            vt = self.rng.standard_normal((len(r), self.dim)) * sd[:, None]
            vt[:, a] = vn if lo else -vn
            x_hit = self._x[r] - v_old * s[:, None]
            x_hit[:, a] = pl
            self._v[r] = vt
            self._x[r] = x_hit + vt * s[:, None]
            w["heat"] += float(0.5 * np.sum(m * (np.einsum("ij,ij->i", vt, vt) - np.einsum("ij,ij->i", v_old, v_old))))
        dv = self._v[r, a] - v_old[:, a]
        w["impulse"] += float(np.sum(m * (dv if lo else -dv)))
        w["hits"] += len(r)

    def _piston_free(self, h):
        p = self._piston
        p["X"] += p["V"] * h
        self._piston_stops()

    def _piston_stops(self):
        p = self._piston
        a = p["axis"]
        if p["X"] > self.L[a] or p["X"] < p["x_min"]:
            edge = self.L[a] if p["X"] > self.L[a] else p["x_min"]
            p["X"] = 2.0 * edge - p["X"] if math.isfinite(p["M"]) else edge
            p["V"] = -p["V"] if math.isfinite(p["M"]) else 0.0
            p["X"] = min(max(p["X"], p["x_min"]), self.L[a])
            p["stops"] += 1

    def _piston_drift(self, h):
        """The piston face moves X(s) = X0 + V s during the drift; particles that crossed it (on their last straight
        segment) collide with it elastically, earliest first (each collision changes V when M is finite)."""
        p = self._piston
        a = p["axis"]
        M = p["M"]
        X0, V, s_last = p["X"], p["V"], 0.0      # the face's path: X(s) = X0 + V (s - s_last) from s_last
        mob = self._mobile
        for _ in range(100000):
            X_end = X0 + V * (h - s_last)
            beyond = np.flatnonzero(mob & (self._x[:, a] > X_end))
            if len(beyond) == 0:
                break
            xe = self._x[beyond, a]
            va = self._v[beyond, a]
            # the particle's segment: x(s) = xe - va (h - s); meets the face where xe - va (h - s) = X0 + V (s - s_last)
            den = va - V
            with np.errstate(divide="ignore", invalid="ignore"):
                s = (X0 - V * s_last - xe + va * h) / den
            s = np.where(den > 0.0, np.clip(s, s_last, h), s_last)
            if not math.isfinite(M):
                # driven: every crossing particle is reflected in the moving face at once
                Xs = X0 + V * (s - s_last)
                v_new = 2.0 * V - va
                m = self._m[beyond]
                p["work"] += float(0.5 * np.sum(m * (v_new ** 2 - va ** 2)))
                p["impulse"] += float(np.sum(m * (va - v_new)))
                p["hits"] += len(beyond)
                self._v[beyond, a] = v_new
                self._x[beyond, a] = np.minimum(Xs + v_new * (h - s), X_end)
                break
            k = int(np.argmin(s))
            r, sk = beyond[k], float(s[k])
            m = float(self._m[r])
            vi = float(va[k])
            Xs = X0 + V * (sk - s_last)
            vi_new = ((m - M) * vi + 2.0 * M * V) / (m + M)
            V_new = ((M - m) * V + 2.0 * m * vi) / (m + M)
            p["work"] += 0.5 * m * (vi_new ** 2 - vi ** 2)
            p["impulse"] += m * (vi - vi_new)
            p["hits"] += 1
            self._v[r, a] = vi_new
            self._x[r, a] = Xs + vi_new * (h - sk)
            X0, V, s_last = Xs, V_new, sk
        p["X"] = X0 + V * (h - s_last)
        p["V"] = V
        self._piston_stops()
        X = p["X"]
        over = mob & (self._x[:, a] > X)
        if np.any(over):   # only after a stop: reflect in the face at rest
            self._x[over, a] = np.maximum(2.0 * X - self._x[over, a], 0.0)
            vo = self._v[over, a]
            p["impulse"] += float(np.sum(self._m[over] * 2.0 * np.maximum(vo, 0.0)))   # no work: the face is at rest
            self._v[over, a] = -np.abs(vo)

    def _bath_rows(self, b):
        sel = self._mobile.copy()
        if b["species"] is not None:
            ti = [self._species_index(s) for s in b["species"]]
            sel &= np.isin(self._typ, ti)
        if b["region"] is not None:
            lo, hi = np.asarray(b["region"][0]), np.asarray(b["region"][1])
            sel &= np.all((self._x >= lo) & (self._x < hi), axis=1)
        return np.flatnonzero(sel)

    def momentum_conserved_axes(self) -> np.ndarray:
        """Per axis: is that component of the total momentum a constant of the motion? Yes along a periodic axis
        without a field component, when no Langevin bath, no local or species-restricted CSVR bath, no thermal wall
        (diffuse re-emission draws new tangential velocities) and no frozen particle acts. Specular and soft walls and
        the piston push only along their own (walled) axis; a global CSVR bath rescales only the velocities relative
        to the centre of mass along these axes (review B7-md M9, M21)."""
        ok = self.periodic & (self.g == 0.0)
        if not np.all(self._mobile) or any(w["kind"] == "thermal" for w in self._walls.values()):
            return np.zeros(self.dim, bool)
        for b in self._baths.values():
            if b["kind"] == "langevin" or b["region"] is not None or b["species"] is not None:
                return np.zeros(self.dim, bool)
        return ok

    def momentum_conserved(self) -> bool:
        """Is the whole total momentum a constant of the motion (every axis, ``momentum_conserved_axes``)?"""
        return bool(np.all(self.momentum_conserved_axes()))

    def _o_csvr(self, h):
        for b in self._baths.values():
            if b["kind"] != "csvr":
                continue
            r = self._bath_rows(b)
            if len(r) == 0:
                continue
            m = self._m[r]
            v = self._v[r]
            glob = b["region"] is None and b["species"] is None and len(r) == self.n
            cons = self.momentum_conserved_axes() if glob else np.zeros(self.dim, bool)
            if np.any(cons) and len(r) > 1:
                # the global bath acts on the motion relative to the centre of mass along the axes whose momentum is
                # conserved: P stays as it is and N_f counts d N - (those axes) (review B7-md M9)
                vc = np.where(cons, (m[:, None] * v).sum(0) / m.sum(), 0.0)
                v = v - vc
            else:
                vc = None
            K = 0.5 * float(np.sum(m * np.einsum("ij,ij->i", v, v)))
            nf = self.dim * len(r) - int(np.sum(cons))
            if nf <= 0:
                continue
            Kbar = 0.5 * nf * b["T"]
            if K <= 0.0:
                vn = self.rng.standard_normal(v.shape) * np.sqrt(b["T"] / m)[:, None]
                if vc is not None:
                    vn -= np.where(cons, (m[:, None] * vn).sum(0) / m.sum(), 0.0)
                Kn = 0.5 * float(np.sum(m * np.einsum("ij,ij->i", vn, vn)))
                self._v[r] = vn if vc is None else vn + vc
                b["heat"] += Kn
                continue
            c = math.exp(-h / b["tau"])
            R1 = float(self.rng.standard_normal())
            S = float(self.rng.chisquare(nf - 1)) if nf > 1 else 0.0
            Knew = (c * K + (1.0 - c) * Kbar * (S + R1 * R1) / nf
                    + 2.0 * R1 * math.sqrt(c * (1.0 - c) * K * Kbar / nf))
            alpha = math.sqrt(max(Knew, 0.0) / K)
            self._v[r] = v * alpha if vc is None else vc + v * alpha
            b["heat"] += Knew - K

    def _o_langevin(self, h):
        for b in self._baths.values():
            if b["kind"] != "langevin":
                continue
            r = self._bath_rows(b)
            if len(r) == 0:
                continue
            m = self._m[r]
            v = self._v[r]
            c = math.exp(-b["gamma"] * h)
            vn = c * v + math.sqrt(1.0 - c * c) * np.sqrt(b["T"] / m)[:, None] * self.rng.standard_normal(v.shape)
            self._v[r] = vn
            b["heat"] += 0.5 * float(np.sum(m * (np.einsum("ij,ij->i", vn, vn) - np.einsum("ij,ij->i", v, v))))

    def reverse(self):
        """Time reversal at the current time: v -> -v (and the piston's V); velocity Verlet retraces its steps."""
        self._v = -self._v
        if self._piston is not None:
            self._piston["V"] = -self._piston["V"]
        self._p_ref = -self._p_ref

    # --- measurements ---------------------------------------------------------------------------------------------
    def kinetic_energy(self, rows=None) -> float:
        r = np.flatnonzero(self._mobile) if rows is None else rows
        v = self._v[r]
        return 0.5 * float(np.sum(self._m[r] * np.einsum("ij,ij->i", v, v)))

    def potential_energy(self) -> dict:
        """Potential energy by part (pair as integrated, i.e. shifted; Coulomb, bond, angle, wall, field), the total,
        the plainly truncated pair energy (pair + the shifts of the pairs inside r_c) and the pair model's tail
        correction (fully periodic boxes)."""
        E = dict(self._energy)
        tot = E["pair"] + E["coulomb"] + E["bond"] + E["angle"] + E["wall"] + E["field"]
        out = {k: E[k] for k in ("pair", "coulomb", "bond", "angle", "wall", "field")}
        out["total"] = tot
        out["pair_truncated"] = E["pair"] + E["pair_shift"]
        out["tail"] = self._tail()[0]
        return out

    def _tail(self):
        if self.pair is None or self._tables is None or not np.all(self.periodic) or not hasattr(self.pair, "tail"):
            return 0.0, 0.0
        counts = np.bincount(self._typ, minlength=len(self._species))
        return self.pair.tail(self._tables, counts, self.volume(), self.dim)

    def energy(self) -> float:
        """Total energy of the particles (kinetic + potential) at the current time."""
        if not self._energy:
            return 0.0
        E = self._energy
        return self.kinetic_energy() + E["pair"] + E["coulomb"] + E["bond"] + E["angle"] + E["wall"] + E["field"]

    def piston_energy(self) -> float:
        """The piston's mechanical energy: (M/2) V^2 + p_ext A X - M g_a X (0 without a free piston)."""
        p = self._piston
        if p is None or not math.isfinite(p["M"]):
            return 0.0
        a = p["axis"]
        return 0.5 * p["M"] * p["V"] ** 2 + p["p_ext"] * self._area(a) * p["X"] - p["M"] * self.g[a] * p["X"]

    def momentum(self) -> np.ndarray:
        mob = self._mobile
        return np.sum(self._m[mob, None] * self._v[mob], axis=0)

    def volume(self) -> float:
        L = self.L.copy()
        if self._piston is not None:
            L[self._piston["axis"]] = self._piston["X"]
        return float(np.prod(L))

    def dof(self) -> tuple:
        """(N_f, reason): the degrees of freedom of the temperature: d N_mobile minus the number of conserved
        momentum components (``momentum_conserved_axes``)."""
        nm = int(np.sum(self._mobile))
        nc = int(np.sum(self.momentum_conserved_axes())) if nm > 1 else 0
        if nc == self.dim:
            return self.dim * nm - nc, T("d·N − d: the total momentum is conserved (all axes periodic)")
        if nc:
            ax = ", ".join(_AX[a] for a in np.flatnonzero(self.momentum_conserved_axes()))
            return self.dim * nm - nc, T("d·N − {nc:d}: the momentum along {axes} is conserved", nc=nc, axes=ax)
        return self.dim * nm, T("d·N: the momentum is not conserved (walls, a field, a Langevin or a local "
                                "thermostat)")

    def temperature(self, species=None, region=None) -> dict:
        """Kinetic temperature. Whole system: 2 K_int / N_f (K_int: in the centre-of-mass frame along the axes whose
        momentum is conserved; N_f from ``dof``). A species or a region (lo, hi): 2 K / (d n) (no momentum
        constraint)."""
        if species is None and region is None:
            nf, why = self.dof()
            K = self.kinetic_energy()
            cons = self.momentum_conserved_axes()
            if np.any(cons) and nf > 0 and int(np.sum(self._mobile)) > 1:
                P = np.where(cons, self.momentum(), 0.0)
                K -= 0.5 * float(P @ P) / float(np.sum(self._m[self._mobile]))
            return {"T": 2.0 * K / nf if nf > 0 else float("nan"), "dof": nf, "K": K, "reason": why}
        sel = self._mobile.copy()
        if species is not None:
            sel &= self._typ == self._species_index(species)
        if region is not None:
            lo, hi = self._region(region)
            sel &= np.all((self._x >= lo) & (self._x < hi), axis=1)
        r = np.flatnonzero(sel)
        K = self.kinetic_energy(r)
        nf = self.dim * len(r)
        return {"T": 2.0 * K / nf if nf else float("nan"), "dof": nf, "K": K, "reason": T("d·n of the selected particles")}

    def kinetic_tensor(self) -> np.ndarray:
        """2 K_aa = sum m v_a^2 (centre-of-mass frame along the axes whose momentum is conserved)."""
        mob = self._mobile
        v = self._v[mob]
        m = self._m[mob]
        cons = self.momentum_conserved_axes()
        if np.any(cons) and len(m):
            v = v - np.where(cons, (m[:, None] * v).sum(0) / m.sum(), 0.0)
        return np.einsum("i,ij->j", m, v * v)

    def pressure(self) -> dict:
        """Virial pressure (tensor diagonal and its mean), its kinetic and interaction parts, the tail correction
        (fully periodic boxes) and the pressure on each wall and on the piston by the momentum given to them
        since the counters were reset (see the module docstring)."""
        V = self.volume()
        kin = self.kinetic_tensor()
        tens = (kin + self._vir) / V
        ok = bool(np.all(np.isfinite(tens)))
        Pv = float(np.mean(tens)) if ok else None
        tail = self._tail()[1]
        out = {"virial": Pv, "tensor": [float(z) if math.isfinite(z) else None for z in tens],
               "kinetic": float(np.mean(kin)) / V, "interaction": float(np.mean(self._vir)) / V if ok else None,
               "tail": tail, "virial_with_tail": Pv + tail if ok else None,
               "volume": V, "walls": {}, "piston": None}
        for k, w in self._walls.items():
            a = _AX.index(k[0])
            dt = self.t - (w["t0"] if w["t0"] is not None else self._balance["t0"])
            out["walls"][k] = w["impulse"] / (self._area(a) * dt) if dt > 0 else None
        p = self._piston
        if p is not None:
            dt = self.t - p["t0"]
            out["piston"] = p["impulse"] / (self._area(p["axis"]) * dt) if dt > 0 else None
        return out

    def counters(self) -> dict:
        """Heat and work counters since the last reset: walls (impulse, heat, hits), baths (heat), the piston
        (work on the gas, impulse, hits, stops)."""
        return {"t0": self._balance["t0"], "t": self.t,
                "walls": {k: {"kind": w["kind"], "impulse": w["impulse"], "heat": w["heat"], "hits": w["hits"]}
                          for k, w in self._walls.items()},
                "baths": {k: b["heat"] for k, b in self._baths.items()},
                "piston": None if self._piston is None else {k: self._piston[k] for k in
                                                             ("work", "impulse", "hits", "stops", "X", "V")}}

    def heat(self) -> float:
        """Heat given to the particles since the counters' reset (walls and baths, also those removed since)."""
        return float(sum(w["heat"] for w in self._walls.values()) + sum(b["heat"] for b in self._baths.values())
                     + self._balance["Q"])

    def work(self) -> float:
        """Work done on the particles since the counters' reset: by the piston (also pistons removed since) and by the
        changes of the box (``deform``)."""
        return float(self._balance["W"] + self._balance.get("Wd", 0.0)
                     + (0.0 if self._piston is None else self._piston["work"]))

    def energy_balance(self) -> dict:
        """First law since the counters' reset: E - E0 = Q + W + residual (the residual is the integrator's error;
        edits move E0 by the energy they change; a change of the box is work, ``W_box``, not an edit)."""
        E = self.energy()
        Q, W = self.heat(), self.work()
        dE = E - self._balance["E0"]
        Wd = float(self._balance.get("Wd", 0.0))
        return {"E": E, "E0": self._balance["E0"], "dE": dE, "Q": Q, "W": W, "W_box": Wd, "W_piston": W - Wd,
                "residual": dE - Q - W, "t0": self._balance["t0"], "t": self.t}

    def reset_counters(self):
        """Restart the heat, work and impulse counters and the first-law balance at the current time."""
        for w in self._walls.values():
            w.update(impulse=0.0, heat=0.0, hits=0, t0=self.t)
        for b in self._baths.values():
            b["heat"] = 0.0
        if self._piston is not None:
            self._piston.update(work=0.0, impulse=0.0, hits=0, t0=self.t, stops=0)
        self._balance = {"t0": self.t, "E0": self.energy(), "Q": 0.0, "W": 0.0, "Wd": 0.0}
        self._p_ref = self.momentum()
        self._p_ref_step = self.nstep
        self._p_ref_ramp = self._ramp_steps

    def momentum_drift(self) -> dict:
        """The change of the total momentum since the last edit or counter reset, per axis, against a bound of its
        rounding (review B7-md M8). Where a component is conserved (``momentum_conserved_axes``) the forces cancel
        pairwise in exact arithmetic; in floating point each step changes P_a by at most

            eps [ h (k + 3) S_w,a + h S_f,a + 4 S_v,a ]

        (eps = 2^-52; two kicks of h/2: the rounded per-particle force sums leave sum_i f_ia off zero by at most
        (k + 2) eps/2 times the twice-counted gross sum S_w,a = sum over force terms |w_a| (k: the most terms one
        particle's force sums, the +2 for adding the force kinds), the product (h/2) f/m and the addition to v round
        at eps/2 |h f/(2m)| and eps/2 |v|, i.e. S_f,a = sum |f_ia|, S_v,a = sum m |v_ia|; a global CSVR's
        rescaling about the centre of mass adds 2 x 3 eps/2 S_v,a per step), and measuring P adds (log2 N + 2) eps
        S_v,a at each end. The bound is the per-step bound times the steps (rounding errors add at most linearly; in
        practice like a random walk), evaluated with the current magnitudes doubled for their fluctuation. Returns
        {"P", "P_ref", "drift" (|P - P_ref| per axis), "steps", "bound" (per axis), "axes" (conserved), "ratio": the
        largest drift / bound over the conserved axes (None if none)}."""
        P = self.momentum()
        steps = self.nstep - self._p_ref_step
        cons = self.momentum_conserved_axes()
        eps = float(np.finfo(float).eps)
        mob = self._mobile
        Sv = np.sum(self._m[mob, None] * np.abs(self._v[mob]), axis=0) if np.any(mob) else np.zeros(self.dim)
        Sf = np.sum(np.abs(self._f[mob]), axis=0) if np.any(mob) else np.zeros(self.dim)
        Sw, k = self._gross_forces()
        h = self._dt
        per = eps * (h * (k + 3) * Sw + h * Sf + 4.0 * Sv)
        nmob = max(int(np.sum(mob)), 1)
        # a box ramp's substep (``ramp_box``) maps v -> u + (v - u)/lambda about the centre of mass: u's sum and the
        # three operations round at most (log2 N + 4) eps S_v,a per substep
        ramp = (self._ramp_steps - self._p_ref_ramp) * (math.log2(nmob) + 4.0) * eps * Sv
        bound = 2.0 * (steps * per + ramp + 2.0 * (math.log2(nmob) + 2.0) * eps * Sv)
        drift = np.abs(P - self._p_ref)
        ratio = None
        if np.any(cons):
            with np.errstate(divide="ignore", invalid="ignore"):
                rr = np.where(bound[cons] > 0, drift[cons] / bound[cons], np.where(drift[cons] > 0, np.inf, 0.0))
            ratio = float(np.max(rr))
        return {"P": P.tolist(), "P_ref": np.asarray(self._p_ref).tolist(), "drift": drift.tolist(), "steps": steps,
                "bound": bound.tolist(), "axes": cons.tolist(), "ratio": ratio}

    def _gross_forces(self):
        """(S_w per axis, k): the sum over every force term (pair, Coulomb, bond, angle) of the absolute value of its
        contribution, counted once per particle it acts on, and the largest number of terms of one particle."""
        n, d = self.n, self.dim
        Sw = np.zeros(d)
        cnt = np.zeros(n, np.int64)
        if n < 2:
            return Sw, 0
        x = self._x
        if self.pair is not None and self._tables is not None and self._nl is not None:
            i, j, fr, dx, u, r2 = self._pair_terms(x)
            Sw += 2.0 * np.abs(fr[:, None] * dx).sum(0)
            cnt += np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
        q = np.array([sp["charge"] for sp in self._species])[self._typ]
        c = np.flatnonzero(q != 0.0)
        if len(c) >= 2:
            ii, jj = np.triu_indices(len(c), 1)
            i, j = c[ii], c[jj]
            dx = x[j] - x[i]
            r2 = np.einsum("ij,ij->i", dx, dx)
            Sw += 2.0 * np.abs((q[i] * q[j] / (r2 * np.sqrt(r2)))[:, None] * dx).sum(0)
            cnt[c] += len(c) - 1
        if len(self._bonds):
            rows = self._rows(self._bonds.reshape(-1)).reshape(-1, 2)
            bt = list(self._bond_types.values())
            for t in np.unique(self._bond_t):
                sel = self._bond_t == t
                i, j = rows[sel, 0], rows[sel, 1]
                dx = self._min_image(x[j] - x[i])
                r = np.sqrt(np.einsum("ij,ij->i", dx, dx))
                _, mdu = bt[t].evaluate(r)
                Sw += 2.0 * np.abs((np.broadcast_to(mdu, r.shape) / r)[:, None] * dx).sum(0)
                cnt += np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
        if len(self._angles):
            rows = self._rows(self._angles.reshape(-1)).reshape(-1, 3)
            at = list(self._angle_types.values())
            for t in np.unique(self._angle_t):
                sel = self._angle_t == t
                i, j, k = rows[sel, 0], rows[sel, 1], rows[sel, 2]
                a_ = self._min_image(x[i] - x[j])
                b_ = self._min_image(x[k] - x[j])
                la = np.sqrt(np.einsum("ij,ij->i", a_, a_))
                lb = np.sqrt(np.einsum("ij,ij->i", b_, b_))
                cos = np.clip(np.einsum("ij,ij->i", a_, b_) / (la * lb), -1.0, 1.0)
                _, dudc = at[t].evaluate(np.arccos(cos), cos)
                dudc = np.broadcast_to(dudc, la.shape)
                Fi = -dudc[:, None] * (b_ / (la * lb)[:, None] - (cos / (la * la))[:, None] * a_)
                Fk = -dudc[:, None] * (a_ / (la * lb)[:, None] - (cos / (lb * lb))[:, None] * b_)
                Sw += 2.0 * (np.abs(Fi).sum(0) + np.abs(Fk).sum(0))
                for r_ in (i, j, k):
                    cnt += np.bincount(r_, minlength=n)
        return Sw, int(cnt.max()) if n else 0

    def rdf(self, r_max, nbins=100, species_a=None, species_b=None):
        """g(r) of the current configuration (minimum image on periodic axes) between species a and b (default
        all), normalised by the ideal-gas pair count in the box volume (exact for a periodic box; with walls the
        missing neighbours near the walls lower g at large r: an approximation)."""
        from .observables import rdf as _rdf
        sa = None if species_a is None else self._typ == self._species_index(species_a)
        sb = None if species_b is None else self._typ == self._species_index(species_b)
        return _rdf(self._x, self.L, self.periodic, r_max, nbins, sa, sb, volume=self.volume())

    def msd_origin(self):
        """Set the origin of the mean-square displacement at the current time."""
        self._msd_ref = self._x + self._img * self.L
        self._msd_t0 = self.t

    def msd(self, species=None) -> dict:
        """Mean-square displacement since ``msd_origin`` (unwrapped coordinates), mobile particles."""
        if self._msd_ref is None:
            raise RuntimeError("call msd_origin() first")
        sel = self._mobile.copy()
        if species is not None:
            sel &= self._typ == self._species_index(species)
        dx = (self._x + self._img * self.L)[sel] - self._msd_ref[sel]
        return {"t": self.t - self._msd_t0, "msd": float(np.mean(np.einsum("ij,ij->i", dx, dx))) if sel.any()
                else float("nan"), "n": int(sel.sum())}

    def velocity_ks(self, species=None, T=None, alpha=0.01) -> dict:
        """Velocity components against the Maxwell-Boltzmann Gaussian: each component of each mobile particle of
        ``species`` (a name, a list of names, or None: every species) divided by sqrt(T/m) of its own mass, pooled,
        against N(0, 1) - the KS distance and its DKW bound at level alpha. T: given, or the temperature of the
        pooled sample 2K/(d n) (the species share one temperature in equilibrium; review B7-md M7). No particles:
        {"D": None, "n": 0, ...}."""
        from .observables import ks_gaussian
        sel = self._mobile.copy()
        if species is not None:
            names = [species] if isinstance(species, str) else list(species)
            sel &= np.isin(self._typ, [self._species_index(nm) for nm in names])
        r = np.flatnonzero(sel)
        if T is None:
            T = 2.0 * self.kinetic_energy(r) / (self.dim * len(r)) if len(r) else float("nan")
        if not len(r) or not (T > 0):
            return ks_gaussian(np.zeros(0), 1.0, alpha=alpha)
        z = self._v[r] * np.sqrt(self._m[r] / T)[:, None]
        return ks_gaussian(z.reshape(-1), 1.0, alpha=alpha)

    def molecule_modes(self, molecules=None) -> dict | None:
        """The kinetic energy of molecules split into translation (centre of mass), rotation (L . omega / 2 with
        omega = I^-1 L about the centre of mass, I the instantaneous inertia tensor) and the rest (vibration), and
        the bonds' and angles' potential energy, each with its number of quadratic terms and as a temperature
        2 E / (terms) (review B7-md M4): equipartition gives every one the same T (harmonic bonds and angles: stiff
        limit). Rotations: d = 2 one per molecule; d = 3 two for a linear molecule (the inertia about its axis below
        1e-9 of the largest), three otherwise. ``molecules``: molecule keys (default all). None without molecules."""
        mk = np.unique(self._mol[self._mol >= 0]) if molecules is None else np.unique(np.asarray(molecules, np.int64))
        if len(mk) == 0:
            return None
        rows = np.flatnonzero(np.isin(self._mol, mk) & self._mobile)
        if len(rows) == 0:
            return None
        d = self.dim
        gid = np.searchsorted(mk, self._mol[rows])
        nmol = len(mk)
        m = self._m[rows]
        x = self._x[rows] + self._img[rows] * self.L
        v = self._v[rows]
        M = np.bincount(gid, weights=m, minlength=nmol)
        X = np.stack([np.bincount(gid, weights=m * x[:, a], minlength=nmol) for a in range(d)], 1) / M[:, None]
        V = np.stack([np.bincount(gid, weights=m * v[:, a], minlength=nmol) for a in range(d)], 1) / M[:, None]
        r = x - X[gid]
        u = v - V[gid]
        K_tr = 0.5 * float(np.sum(M * np.einsum("ij,ij->i", V, V)))
        K_int = 0.5 * float(np.sum(m * np.einsum("ij,ij->i", u, u)))
        natoms = np.bincount(gid, minlength=nmol)
        if d == 2:
            Lz = np.bincount(gid, weights=m * (r[:, 0] * u[:, 1] - r[:, 1] * u[:, 0]), minlength=nmol)
            Iz = np.bincount(gid, weights=m * np.einsum("ij,ij->i", r, r), minlength=nmol)
            K_rot = 0.5 * float(np.sum(np.where(Iz > 0, Lz * Lz / np.where(Iz > 0, Iz, 1.0), 0.0)))
            nrot = int(np.sum(natoms >= 2))
        else:
            Lv = np.stack([np.bincount(gid, weights=w, minlength=nmol) for w in (m[:, None] * np.cross(r, u)).T], 1)
            rr = np.einsum("ij,ij->i", r, r)
            I = np.zeros((nmol, 3, 3))
            for a in range(3):
                for b in range(3):
                    I[:, a, b] = np.bincount(gid, weights=m * ((rr if a == b else 0.0) - r[:, a] * r[:, b]),
                                             minlength=nmol)
            w, Q = np.linalg.eigh(I)
            top = w[:, -1:]
            good = w > 1e-9 * np.maximum(top, 1e-300)
            Lb = np.einsum("nji,nj->ni", Q, Lv)              # L in the principal axes
            K_rot = 0.5 * float(np.sum(np.where(good, Lb * Lb / np.where(good, w, 1.0), 0.0)))
            nrot = int(np.sum(np.where(natoms >= 2, np.sum(good, axis=1), 0)))
        K_vib = K_int - K_rot
        n_tr = d * nmol
        n_vib = int(d * len(rows) - n_tr - nrot)
        out = {"molecules": nmol, "atoms": int(len(rows)),
               "translation": {"K": K_tr, "terms": n_tr}, "rotation": {"K": K_rot, "terms": nrot},
               "vibration": {"K": K_vib, "terms": n_vib}}
        keyset = self._key[rows]
        for part, arr, typ, types, nat in (("bonds", self._bonds, self._bond_t, self._bond_types, 2),
                                          ("angles", self._angles, self._angle_t, self._angle_types, 3)):
            sel = np.all(np.isin(arr, keyset), axis=1) if len(arr) else np.zeros(0, bool)
            E = 0.0
            if np.any(sel):
                rw = self._rows(arr[sel].reshape(-1)).reshape(-1, nat)
                tl = list(types.values())
                for t in np.unique(typ[sel]):
                    q = typ[sel] == t
                    if nat == 2:
                        dx = self._min_image(self._x[rw[q, 1]] - self._x[rw[q, 0]])
                        E += float(np.sum(np.broadcast_to(tl[t].evaluate(np.sqrt(np.einsum("ij,ij->i", dx, dx)))[0],
                                                          (int(q.sum()),))))
                    else:
                        a_ = self._min_image(self._x[rw[q, 0]] - self._x[rw[q, 1]])
                        b_ = self._min_image(self._x[rw[q, 2]] - self._x[rw[q, 1]])
                        cos = np.clip(np.einsum("ij,ij->i", a_, b_) / np.sqrt(np.einsum("ij,ij->i", a_, a_)
                                                                              * np.einsum("ij,ij->i", b_, b_)), -1, 1)
                        E += float(np.sum(np.broadcast_to(tl[t].evaluate(np.arccos(cos), cos)[0], (int(q.sum()),))))
            out[part] = {"U": E, "terms": int(np.sum(sel))}
        for part in ("translation", "rotation", "vibration"):
            o = out[part]
            o["T"] = 2.0 * o["K"] / o["terms"] if o["terms"] > 0 else None
        for part in ("bonds", "angles"):
            o = out[part]
            o["T"] = 2.0 * o["U"] / o["terms"] if o["terms"] > 0 else None
        return out

    def probe(self, center, radius) -> dict:
        """The particles whose centres lie within ``radius`` of ``center`` (minimum image on periodic axes; radius
        <= L/2 there): their number, the number density over the part of the ball inside the box (by a 48^d grid of
        the ball's bounding cube: about 1 % on the volume where the ball crosses a wall) and their kinetic temperature
        2K/(d n) (review B7-md M18)."""
        return _probe(self._x[self._mobile], self._v[self._mobile], self._m[self._mobile], self.L, self.periodic,
                      center, radius, hi=self._region(None)[1])

    def step_error(self, n_steps=10) -> dict:
        """The time step's error by a companion: the same interval n_steps dt from the current state with dt and
        with dt/2 (copies; this system is not advanced). Second order: the error of the dt run is ~ 4/3 of the
        difference. Deterministic systems only (no baths, no thermal walls)."""
        if self._baths or any(w["kind"] == "thermal" for w in self._walls.values()):
            raise ValueError("the companion needs a deterministic system (no thermostats, no thermal walls)")
        a = MD.from_state_dict(self.state_dict())
        b = MD.from_state_dict(self.state_dict())
        b.set_dt(self._dt / 2)
        a.step(n_steps)
        b.step(2 * n_steps)
        dx = a.positions(True) - b.positions(True)
        err = float(np.max(np.sqrt(np.einsum("ij,ij->i", dx, dx)))) if self.n else 0.0
        return {"interval": n_steps * self._dt, "dt": self._dt, "dx_max": err, "dx_max_estimate": 4.0 / 3.0 * err,
                "dE": a.energy() - b.energy(), "dE_estimate": 4.0 / 3.0 * (a.energy() - b.energy())}

    def cost_estimate(self) -> dict:
        """Seconds per step: measured on this run so far and modelled from the bench of this host (``bench``)."""
        from .observables import md_step_model
        meas = self._stats["seconds"] / self._stats["timed_steps"] if self._stats["timed_steps"] else None
        model = md_step_model(self.n, self._stats["pairs"], self.dim)
        return {"per_step_s": model, "measured_per_step_s": meas, "n": self.n, "pairs": self._stats["pairs"],
                "rebuilds": self._stats["rebuilds"], "device": self._device,
                "note": T("model: CPU; on GPU 0 the pair forces are faster from ~2·10^4 pairs (README)")}

    def diagnostics(self) -> dict:
        T = self.temperature()
        return {"t": self.t, "nstep": self.nstep, "n": self.n, "T": T["T"], "dof": T["dof"],
                "energy": self.energy(), "potential": self.potential_energy(), "momentum": self.momentum().tolist(),
                "balance": self.energy_balance(), "pairs": self._stats["pairs"], "rebuilds": self._stats["rebuilds"],
                "backstop_hits": self._stats["backstop_hits"]}

    # --- state ----------------------------------------------------------------------------------------------------
    def state_dict(self) -> dict:
        """Plain data and NumPy arrays of the whole state; ``from_state_dict`` continues bit for bit."""
        nl_ref = None if self._nl is None else [self._nl["x_build"].copy(), self._nl["x_ref"].copy()]
        walls = {k: {**{kk: vv for kk, vv in w.items() if kk != "term"}, "term": _term_data(w["term"])}
                 for k, w in self._walls.items()}
        return {
            "format": _FORMAT, "dim": self.dim, "L": self.L.copy(), "periodic": self.periodic.copy(),
            "pair": _term_data(self.pair), "skin": self.skin, "exclude": self.exclude,
            "max_insert_energy": self.max_insert_energy, "dt": self._dt, "t_base": self._t_base,
            "n_since": self._n_since, "nstep": self.nstep, "g": self.g.copy(), "rng": self.rng.bit_generator.state,
            "species": [dict(s) for s in self._species],
            "bond_types": {k: _term_data(v) for k, v in self._bond_types.items()},
            "angle_types": {k: _term_data(v) for k, v in self._angle_types.items()},
            "key": self._key.copy(), "typ": self._typ.copy(), "mol": self._mol.copy(), "x": self._x.copy(),
            "img": self._img.copy(), "v": self._v.copy(), "f": self._f.copy(), "next_key": self._next_key,
            "next_mol": self._next_mol, "bonds": self._bonds.copy(), "bond_t": self._bond_t.copy(),
            "angles": self._angles.copy(), "angle_t": self._angle_t.copy(), "walls": walls,
            "piston": None if self._piston is None else dict(self._piston),
            "baths": {int(k): dict(b) for k, b in self._baths.items()}, "next_bath": self._next_bath,
            "energy": dict(self._energy), "vir": self._vir.copy(), "wallf": dict(self._wallf),
            "vir_aff": None if self._vir_aff is None else np.asarray(self._vir_aff, float).copy(),
            "ramp": _ramp_data(self._ramp), "ramp_steps": int(self._ramp_steps),
            "balance": dict(self._balance), "msd_ref": None if self._msd_ref is None else self._msd_ref.copy(),
            "msd_t0": self._msd_t0, "nl_ref": nl_ref, "stats": dict(self._stats), "device_mode": self.device_mode,
            "p_ref": np.asarray(self._p_ref, float).copy(), "p_ref_step": int(self._p_ref_step),
            "p_ref_ramp": int(self._p_ref_ramp),
        }

    @classmethod
    def from_state_dict(cls, d: dict) -> "MD":
        if d.get("format") != _FORMAT:
            raise ValueError(f"not an {_FORMAT} state")
        o = cls.__new__(cls)
        o.dim = int(d["dim"])
        o.L = np.array(d["L"], float)
        o.periodic = np.array(d["periodic"], bool)
        o.pair = _term_from(d["pair"])
        o.device_mode = d.get("device_mode", "auto")
        o._force_cpu = T("set: CPU") if o.device_mode == "cpu" else None
        o._device = "cpu"
        o.skin, o.exclude = float(d["skin"]), d["exclude"]
        o.max_insert_energy = float(d["max_insert_energy"])
        o._dt, o._t_base, o._n_since, o.nstep = float(d["dt"]), float(d["t_base"]), int(d["n_since"]), int(d["nstep"])
        o.g = np.array(d["g"], float)
        o.rng = np.random.Generator(np.random.PCG64())
        o.rng.bit_generator.state = copy.deepcopy(d["rng"])
        o._seed = None
        o._species = [dict(s) for s in d["species"]]
        o._bond_types = {k: _term_from(v) for k, v in d["bond_types"].items()}
        o._angle_types = {k: _term_from(v) for k, v in d["angle_types"].items()}
        dd = o.dim
        o._key = np.array(d["key"], np.int64)
        o._typ = np.array(d["typ"], np.int64)
        o._mol = np.array(d["mol"], np.int64)
        n = len(o._key)
        o._x = np.array(d["x"], float).reshape(n, dd)
        o._img = np.array(d["img"], np.int64).reshape(n, dd)
        o._v = np.array(d["v"], float).reshape(n, dd)
        o._f = np.array(d["f"], float).reshape(n, dd)
        o._next_key, o._next_mol = int(d["next_key"]), int(d["next_mol"])
        o._bonds = np.array(d["bonds"], np.int64).reshape(-1, 2)
        o._bond_t = np.array(d["bond_t"], np.int64)
        o._angles = np.array(d["angles"], np.int64).reshape(-1, 3)
        o._angle_t = np.array(d["angle_t"], np.int64)
        o._walls = {k: {**{kk: vv for kk, vv in w.items() if kk != "term"}, "term": _term_from(w["term"])}
                    for k, w in d["walls"].items()}
        o._piston = None if d["piston"] is None else dict(d["piston"])
        o._baths = {int(k): dict(b) for k, b in d["baths"].items()}
        o._next_bath = int(d["next_bath"])
        o._balance = dict(d["balance"])
        o._msd_ref = None if d["msd_ref"] is None else np.array(d["msd_ref"], float).reshape(n, dd)
        o._msd_t0 = d["msd_t0"]
        o._stats = dict(d["stats"])
        o._derived()
        o._energy = dict(d["energy"])
        o._vir = np.array(d["vir"], float)
        o._vir_aff = None if d.get("vir_aff") is None else np.array(d["vir_aff"], float)   # older states: on demand
        o._ramp = _ramp_from(d.get("ramp"))
        o._ramp_steps = int(d.get("ramp_steps", 0))
        o._wallf = dict(d["wallf"])
        o._p_ref = np.array(d["p_ref"], float) if d.get("p_ref") is not None else o.momentum()
        o._p_ref_step = int(d.get("p_ref_step", o.nstep))
        o._p_ref_ramp = int(d.get("p_ref_ramp", o._ramp_steps))
        if d["nl_ref"] is not None and o.pair is not None and o._tables is not None and n >= 2:
            # rebuild the pair list exactly as it was built: from the positions of its last build
            x_now = o._x
            o._x = np.array(d["nl_ref"][0], float).reshape(n, dd)
            rebuilds, ssb, pairs = o._stats["rebuilds"], o._stats["steps_since_build"], o._stats["pairs"]
            o._build_list()
            o._nl["x_ref"] = np.array(d["nl_ref"][1], float).reshape(n, dd)
            o._stats.update(rebuilds=rebuilds, steps_since_build=ssb, pairs=pairs)
            o._x = x_now
        return o

    def clone(self) -> "MD":
        return MD.from_state_dict(self.state_dict())

    def _wrap(self, x, img):
        x = np.array(x, float)
        img = np.array(img, np.int64)
        per = np.flatnonzero(self.periodic)
        if len(per):
            k = np.floor(x[:, per] / self.L[per]).astype(np.int64)
            x[:, per] -= k * self.L[per]
            x[:, per] = np.where(x[:, per] >= self.L[per], x[:, per] - self.L[per], x[:, per])
            x[:, per] = np.where(x[:, per] < 0.0, 0.0, x[:, per])
            img[:, per] += k
        return x, img
