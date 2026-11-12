# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Lennard-Jones fluid (plan P8) at published state points of the NIST Standard Reference Simulation Website
(sources/verification_2026-11-04_p8_md.md):

* "LJ fluid, 3 sigma + standard long-range corrections", NVT Monte Carlo, N = 500: T = 0.85, rho = 0.776:
  U = -5.5121(4.55e-4), p = 6.7714e-3(1.77e-3) (one standard deviation). The engine integrates the energy-shifted
  potential (the forces of the truncated one) and reports the plainly truncated energy plus the tail
  U_LRC = (8/3) pi rho [(1/3) rc^-9 - rc^-3] and p = virial + p_LRC = (16/3) pi rho^2 [(2/3) rc^-9 - rc^-3].
  (NIST's NVE MD table at T = 0.851(1) gives U = -5.517(1), p = 0.030(6), five of its standard errors below its own
  MC value at T = 0.85; the engine agrees with the MC table: an open item in the engine's STATUS.md.)
* "LJ linear-force shifted at 2.5 sigma", LAMMPS NVT MD, N = 10000: T = 1.5, rho = 0.5: p = 0.8608(1.97e-4),
  U = -2.410(6.3e-5) (standard errors).

The run: N = 500 from an fcc lattice, CSVR (tau = 0.05) at T, 15 tau to equilibrate, 40 tau sampled every 10 steps.
Tolerance: 4 times the seed-to-seed standard deviation of a run of this length, measured (five / six seeds: U 0.0023
and p 0.017 at the liquid point; U 0.0033 and p 0.0079 at the supercritical one), combined with the reference's
error. g(r) of the same run is checked against the direct averages through the energy and virial routes."""

import math

import numpy as np
import pytest

from lfphys.core.md import observables as ob
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import LennardJones


def _run(rho, T, pair, rdf_every=0, r_max=3.0, n=500, seed=2):
    L = (n / rho) ** (1.0 / 3.0)
    md = MD(dim=3, box=[L] * 3, pair=pair, dt=0.005, seed=seed)
    md.add_species("A")
    md.fill("A", n=n, T=T)
    md.add_thermostat("csvr", T=T, tau=0.05)
    md.step(3000)
    U, Us, P, Pv = [], [], [], []
    hist, nh = None, 0
    for k in range(800):
        md.step(10)
        pe = md.potential_energy()
        pr = md.pressure()
        U.append((pe["pair_truncated"] + pe["tail"]) / n)
        Us.append(pe["pair"] / n)
        P.append(pr["virial_with_tail"])
        Pv.append(pr["virial"])
        if rdf_every and k % rdf_every == 0:
            r, g, _ = md.rdf(r_max, nbins=600)
            hist = g if hist is None else hist + g
            nh += 1
    out = {"U": np.mean(U), "Us": np.mean(Us), "P": np.mean(P), "Pv": np.mean(Pv), "md": md}
    if rdf_every:
        out["r"], out["g"] = r, hist / nh
    return out


def test_lj_liquid_nist_mc_3sigma():
    """T = 0.85, rho = 0.776 (liquid near coexistence). Also: the energy and virial routes through the measured g(r)
    reproduce the direct averages (0.3 % and 0.02 in p; the histogram's bin width 0.005 limits them). Negative
    control: the energy the integrator conserves (shifted, no tail) differs from the reference by 0.48."""
    rho, T, rc = 0.776, 0.85, 3.0
    res = _run(rho, T, LennardJones(rc, "energy"), rdf_every=10)
    tol_u = 4 * math.hypot(0.0023, 4.55e-4)
    tol_p = 4 * math.hypot(0.017, 1.77e-3)
    assert abs(res["U"] - (-5.5121)) < tol_u, res["U"]
    assert abs(res["P"] - 6.7714e-3) < tol_p, res["P"]
    assert abs(res["Us"] - (-5.5121)) > 50 * tol_u / 4
    # g(r) routes (r < rc, the truncated 12-6 potential; the same configurations)
    r, g = res["r"], res["g"]
    dr = r[1] - r[0]
    u = 4 * (r ** -12 - r ** -6)
    du = 4 * (-12 * r ** -13 + 6 * r ** -7)
    U_route = 2 * math.pi * rho * np.sum(r * r * u * g) * dr
    P_route = rho * T - 2 * math.pi / 3 * rho * rho * np.sum(r ** 3 * du * g) * dr
    md = res["md"]
    U_direct = res["U"] - md.potential_energy()["tail"] / md.n
    assert abs(U_route / U_direct - 1) < 3e-3, (U_route, U_direct)
    assert abs(P_route - res["Pv"]) < 0.02, (P_route, res["Pv"])


def test_lj_supercritical_nist_lfs():
    """Linear-force-shifted LJ at 2.5 sigma, T = 1.5, rho = 0.5 (supercritical gas; N = 500 against NIST's 10000:
    the finite-size difference is inside the tolerance - six seeds average to -2.4097 and 0.8556). Negative control:
    the reference of rho = 0.6 (U = -2.877, p = 1.422) is rejected."""
    res = _run(0.5, 1.5, LennardJones(2.5, "force"))
    U, P = res["Us"], res["Pv"]          # the LFS potential itself (no truncation correction, no tail)
    assert abs(U - (-2.410)) < 4 * math.hypot(0.0033, 6.3e-5), U
    assert abs(P - 0.8608) < 4 * math.hypot(0.0079, 1.97e-4), P
    assert abs(U - (-2.877)) > 0.2 and abs(P - 1.422) > 0.2
    assert res["md"].potential_energy()["tail"] == 0.0     # no tail for the force-shifted form


def test_tail_corrections_closed_form():
    """The tail of the full 12-6 potential beyond r_c with g = 1: U/N = (8/3) pi rho [(1/3) rc^-9 - rc^-3], p =
    (16/3) pi rho^2 [(2/3) rc^-9 - rc^-3] (d = 3); d = 2: U/N = pi rho [(2/5) rc^-10 - rc^-4], p = pi rho^2
    [(12/5) rc^-10 - 3 rc^-4] (sigma = epsilon = 1); a mixture adds N_a N_b / V over species pairs with the mixed
    sigma, epsilon - checked against numerical quadrature of the tail integrals."""
    from scipy.integrate import quad
    lj = LennardJones(2.5)
    t = lj.tables([1.0], [1.0])
    for d, V in ((3, 1000.0), (2, 100.0)):
        rho = 400 / V
        U, p = lj.tail(t, [400], V, d)
        x = 1 / 2.5
        if d == 3:
            Uc = 400 * (8 / 3) * math.pi * rho * (x ** 9 / 3 - x ** 3)
            pc = (16 / 3) * math.pi * rho ** 2 * (2 / 3 * x ** 9 - x ** 3)
        else:
            Uc = 400 * math.pi * rho * (2 / 5 * x ** 10 - x ** 4)
            pc = math.pi * rho ** 2 * (12 / 5 * x ** 10 - 3 * x ** 4)
        assert U == pytest.approx(Uc, rel=1e-13) and p == pytest.approx(pc, rel=1e-13)
    # mixture vs quadrature
    t2 = lj.tables([1.0, 1.3], [1.0, 0.6])
    counts, V = [300, 100], 1000.0
    U, p = lj.tail(t2, counts, V, 3)
    Uq = pq = 0.0
    for a in range(2):
        for b in range(2):
            s, e, rc = t2["sigma"][a, b], t2["epsilon"][a, b], t2["rc"][a, b]
            u = lambda r: 4 * e * ((s / r) ** 12 - (s / r) ** 6)
            du = lambda r: 4 * e * (-12 * s ** 12 / r ** 13 + 6 * s ** 6 / r ** 7)
            Uq += 2 * math.pi / V * counts[a] * counts[b] * quad(lambda r: r * r * u(r), rc, np.inf)[0]
            pq += -2 * math.pi / (3 * V * V) * counts[a] * counts[b] * quad(lambda r: r ** 3 * du(r), rc, np.inf)[0]
    assert U == pytest.approx(Uq, rel=1e-9) and p == pytest.approx(pq, rel=1e-9)
