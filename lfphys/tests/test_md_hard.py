# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Hard disks and hard spheres by event-driven MD (plan P8) against published equations of state.

References (sources/verification_2026-11-04_p8_md.md): the virial coefficients B_k / B_2^(k-1), k = 3 ... 10, of
Clisby & McCoy (2006, Table 1) - at packing fraction eta the series Z = 1 + sum_k (B_k/B_2^(k-1)) (2^(d-1) eta)^(k-1)
converges fast at eta = 0.1 (the truncation after B10 is below 1e-8); Kolafa & Rottner (2006, Table 1, disks, the
thermodynamic limit) and Kolafa, Labik & Malijevsky (2004, the authors' data file zfinal.res, spheres) with the
ensemble correction Z_NVT = Z_inf - (rho/2N) p''/p' (Kolafa & Rottner Eq. "Zenscorr") from their equations of state.
The MD-NVE -> NVT step is in the estimator: Z = 1 + sum r_ij . Delta p_i / (d N T Delta t), T = 2<K>/(dN - d).
Tolerances: 4 standard errors from 10 blocks of the run (the blocks' Z values), plus the reference's error."""

import math

import numpy as np
import pytest

from lfphys.core.md.hard import HardSpheres

# Clisby & McCoy 2006, Table 1: B_k / B_2^(k-1), k = 3 ... 10
CM = {2: [0.782004, 0.53223180, 0.33355604, 0.1988425, 0.1148728, 0.0649930, 0.0362193, 0.0199537],
      3: [0.625, 0.2869495, 0.110252, 0.03888198, 0.01302354, 0.0041832, 0.0013094, 0.0004035]}


def z_virial(eta, d):
    x = 2 ** (d - 1) * eta          # B2 rho
    return 1 + x + sum(b * x ** (k + 2) for k, b in enumerate(CM[d]))


def z_kolafa_rottner(eta):
    """Hard disks, Kolafa & Rottner 2006, the EOS for rho_max = 0.88 (x = eta/(1 - eta))."""
    x = eta / (1 - eta)
    c = [1, 2, 1.12801775, 0.00181895291, -0.0526134737, 0.0504951668, -0.0325433846, 0.0133946531,
         0.00174265604, -0.00944632202, 0.00851111768, -0.0035963525, 0.000577345106]
    return sum(ci * x ** i for i, ci in enumerate(c)) - 1.06399127e-7 * x ** 19


def z_klm(eta):
    """Hard spheres, Kolafa, Labik & Malijevsky 2004 (the authors' code hseos.c, zB6_11348; x = eta/(1 - eta))."""
    x = eta / (1 - eta)
    return (1 + 4 * x + 6 * x ** 2 + 2.36476838 * x ** 3 - 0.869855149 * x ** 4 + 1.1062803 * x ** 5
            - 1.09504933 * x ** 6 + 0.637614043 * x ** 7 - 0.227939731 * x ** 10 + 0.109894767 * x ** 14
            - 0.00906797261 * x ** 22)


def ensemble_correction(zfun, rho, d, n):
    """(rho / 2N) p'' / p' with p = rho Z(eta(rho)) (kT = 1), by central differences."""
    v = math.pi / 4 if d == 2 else math.pi / 6

    def p(r):
        return r * zfun(v * r)
    h = 1e-4 * rho
    p1 = (p(rho + h) - p(rho - h)) / (2 * h)
    p2 = (p(rho + h) - 2 * p(rho) + p(rho - h)) / h ** 2
    return rho / (2 * n) * p2 / p1


def _run(d, n, rho, t_eq, t_block, blocks=10, seed=1):
    L = (n / rho) ** (1.0 / d)
    hs = HardSpheres(d, [L] * d, seed=seed)
    hs.add_species("S")
    hs.fill("S", n=n, T=1.0)
    hs.advance(t_eq)
    Z = []
    for _ in range(blocks):
        hs.reset_counters()
        hs.advance(hs.t + t_block)
        Z.append(hs.pressure()["Z"])
    Z = np.array(Z)
    return hs, float(Z.mean()), float(Z.std(ddof=1) / math.sqrt(blocks))


@pytest.mark.parametrize("d,n", [(2, 400), (3, 500)])
def test_low_density_virial_series(d, n):
    """eta = 0.1: Z against the virial series to B10 (Clisby & McCoy). Negative control: the second-virial truncation
    Z = 1 + B2 rho is rejected."""
    eta = 0.1
    rho = eta / (math.pi / 4 if d == 2 else math.pi / 6)
    hs, z, se = _run(d, n, rho, 5.0, 6.0)
    ref = z_virial(eta, d)
    assert abs(z - ref) < 4 * se, (z, se, ref)
    assert abs(z - (1 + 2 ** (d - 1) * eta)) > 8 * se
    assert hs.packing_fraction() == pytest.approx(eta, rel=1e-12)


def test_hard_disks_kolafa_rottner():
    """Hard disks at rho = 0.4 (eta = 0.314), N = 400: Z against Kolafa & Rottner's 2.1514393(52) (Table 1) minus
    the ensemble correction for N = 400 (from their EOS: 0.0021). Their EOS reproduces the table value to 1e-5 here.
    Negative control: the reference at a density 2 % higher (Z larger by 0.045) is rejected."""
    n, rho = 400, 0.4
    hs, z, se = _run(2, n, rho, 10.0, 8.0)
    eta = math.pi / 4 * rho
    assert abs(z_kolafa_rottner(eta) - 2.1514393) < 2e-5
    ref = 2.1514393 - ensemble_correction(z_kolafa_rottner, rho, 2, n)
    assert abs(z - ref) < 4 * se + 5.2e-6, (z, se, ref)
    ref_hi = z_kolafa_rottner(math.pi / 4 * rho * 1.02) - ensemble_correction(z_kolafa_rottner, rho * 1.02, 2, n)
    assert abs(z - ref_hi) > 4 * se


def test_hard_spheres_kolafa_labik_malijevsky():
    """Hard spheres at rho = 0.5 (eta = 0.262), N = 500: Z against 3.2693735(236) (zfinal.res, the thermodynamic limit)
    minus the ensemble correction for N = 500. Negative control: the reference at a density 2 % higher is rejected.
    Carnahan-Starling (3.2624 here, 0.2 % low) is within the run's resolution and is not used as a control. Measured
    (review B7-md M15, twelve independent runs of this test's estimator, seeds 101-112): Z = 3.2649 +- 0.0032 against
    the corrected reference 3.2673 (-0.08 %, -0.8 SE): no offset; the per-run spread 0.0111 is the scale of the
    tolerance (4 block SE = 0.038 on average, the block SE 0.0095 underestimating the spread by 14 %); the 2 % control
    lies 0.088 above the reference (8 run spreads). [error in earlier: the "+0.39 % at N = 500, a finite-size effect
    beyond 1/N" recorded here before (four runs, 3.2800 +- 0.0034) is not reproduced]"""
    n, rho = 500, 0.5
    hs, z, se = _run(3, n, rho, 5.0, 3.0)
    eta = math.pi / 6 * rho
    assert abs(z_klm(eta) - 3.2693735) < 5e-5           # the authors' EOS against their data point
    ref = 3.2693735 - ensemble_correction(z_klm, rho, 3, n)
    assert abs(z - ref) < 4 * se + 2.4e-5, (z, se, ref)
    ref_hi = z_klm(math.pi / 6 * rho * 1.02) - ensemble_correction(z_klm, rho * 1.02, 3, n)
    assert abs(z - ref_hi) > 4 * se


def test_conservation_state_and_edits():
    """Collisions conserve energy and momentum exactly (to round-off) also for unequal masses and sizes; species of
    different masses share the kinetic energy equally (equipartition: their temperatures agree within 4 standard
    errors); a saved state continues bit for bit (the event calendar is part of it); refused edits (overlap, outside
    a wall) leave the state as it was; walls: the pressure on specular walls by momentum transfer."""
    hs = HardSpheres(2, (20.0, 20.0), boundary=["periodic", "walls"], seed=5)
    hs.add_species("a", mass=1.0, sigma=1.0)
    hs.add_species("b", mass=4.0, sigma=1.4)
    from lfphys.core.md.system import lattice
    sites = lattice(180, [0.0, 0.7], [20.0, 19.3])
    hs.add("a", sites[0::3], T=1.0)
    hs.add("a", sites[1::3], T=1.0)
    hs.add("b", sites[2::3], T=1.0)       # mixed from the start: equilibration by collisions, not by conduction
    hs.advance(40.0)
    K0, P0 = hs.kinetic_energy(), hs.momentum()
    hs.reset_counters()
    ta, tb = [], []
    sel = hs._typ == 0
    for _ in range(40):
        hs.advance(hs.t + 2.0)
        v = hs.velocities()
        ta.append(np.mean(v[sel] ** 2))
        tb.append(4.0 * np.mean(v[~sel] ** 2))
    assert abs(hs.kinetic_energy() - K0) < 1e-12 * K0
    assert abs(hs.momentum()[0] - P0[0]) < 1e-12 * math.sqrt(K0)    # periodic along x: conserved
    from lfphys.core.md.observables import block_average
    (a, sa), (b, sb) = block_average(ta), block_average(tb)
    assert abs(a - b) < 4 * math.hypot(sa, sb), (a, sa, b, sb)
    p = hs.pressure()
    assert p["walls"]["y-lo"] > 0 and p["walls"]["y-hi"] > 0
    s = hs.state_dict()
    twin = HardSpheres.from_state_dict(s)
    hs.advance(hs.t + 5.0)
    twin.advance(twin.t + 5.0)
    assert np.array_equal(hs.positions(True), twin.positions(True)) and np.array_equal(hs.velocities(),
                                                                                       twin.velocities())
    before = hs.state_dict()
    x = hs.positions()
    for bad in (lambda: hs.add("a", x[0] + [0.3, 0.0]), lambda: hs.add("a", [5.0, 0.2]),
                lambda: hs.set(hs.keys[:1], x=[x[1]])):
        with pytest.raises(ValueError):
            bad()
        after = hs.state_dict()
        for k in ("x", "v", "tl", "heap_t", "heap_i", "cnt"):
            assert np.array_equal(before[k], after[k]), k


def test_thermal_wall_heats_hard_disks():
    """Hard disks between a cold specular box and one thermal wall at T_w = 2: the gas warms to T_w (the heat
    counted equals the kinetic energy gained, exactly)."""
    hs = HardSpheres(2, (15.0, 15.0), boundary="walls", seed=6)
    hs.add_species("a")
    hs.fill("a", n=80, T=0.5)
    hs.set_wall("x", "lo", "thermal", T=2.0)
    hs.reset_counters()
    hs.advance(200.0)
    Ts = []
    for _ in range(100):
        hs.advance(hs.t + 4.0)
        Ts.append(hs.temperature()["T"])
    b = hs.energy_balance()
    assert abs(b["residual"]) < 1e-10 * abs(b["Q"])
    from lfphys.core.md.observables import block_average
    m, se = block_average(Ts)
    assert abs(m - 2.0) < 4 * se, (m, se)


# --- review B7-md ------------------------------------------------------------------------------------------------------
def _pair_run(Lx, cls=HardSpheres):
    """Review B7-md r01: disks i at x = 0.1 and j at x = 1.9 (sigma = 1) in a periodic strip Lx x 10, j moving left at
    unit speed: contact at t = 0.8. Returns the smallest centre distance seen (sampled every 0.05) and the time of the
    first collision."""
    hs = cls(2, (Lx, 10.0), boundary="periodic", seed=0)
    hs.add_species("a", mass=1.0, sigma=1.0)
    hs.add("a", [[0.1, 5.0], [1.9, 5.0]], v=[[0.0, 0.0], [-1.0, 0.0]])
    dmin, t_first = 9.0, None
    for t in np.linspace(0.0, 2.0, 41)[1:]:
        hs.advance(t)
        x = hs.positions()
        d = x[1, 0] - x[0, 0]
        dmin = min(dmin, abs(d - Lx * np.rint(d / Lx)))
        if t_first is None and hs.counters()["collisions"]:
            t_first = t
    return dmin, t_first


def test_periodic_axis_needs_four_cells():
    """Review B7-md M1: with three cells on a periodic axis two disks in adjacent cells can be farther apart than L/2,
    so the minimum image taken at the prediction is not the image that collides and the collision was lost (they
    overlapped by 0.1 sigma). A periodic box shorter than four diameters is now refused; at four cells the same pair
    collides at contact. Negative control: the engine with the old rule (three cells allowed) loses the collision."""
    with pytest.raises(ValueError):
        HardSpheres(2, (3.0, 10.0), boundary="periodic")
    dmin, t1 = _pair_run(4.0)
    assert dmin >= 1.0 - 1e-12 and t1 is not None and abs(t1 - 0.8) < 0.051

    class ThreeCells(HardSpheres):
        """The cell grid of the reviewed engine: three cells allowed on a periodic axis."""
        def _grid(self):
            import itertools
            smax = max([sp["sigma"] for sp in self._species], default=1.0)
            nc = np.maximum(np.floor(self.L / smax).astype(np.int64), 1)
            assert not np.any(self.periodic & (nc < 3))
            self._nc, self._w = nc, self.L / nc
            self._sp_sig = np.array([sp["sigma"] for sp in self._species])
            self._sp_mass = np.array([sp["mass"] for sp in self._species])
            ncell = int(np.prod(nc))
            grid = np.stack(np.unravel_index(np.arange(ncell), tuple(nc)), axis=1)
            nbr = [[] for _ in range(ncell)]
            for o in itertools.product(*[(-1, 0, 1) if nc[a] > 1 else (0,) for a in range(self.dim)]):
                g = grid + np.array(o)
                for a in range(self.dim):
                    g[:, a] %= nc[a]
                flat = np.ravel_multi_index(tuple(g.T), tuple(nc))
                for c in range(ncell):
                    nbr[c].append(int(flat[c]))
            self._nbr = nbr
    dmin3, _ = _pair_run(3.0, ThreeCells)
    assert dmin3 < 0.95, dmin3


def test_no_overlap_in_a_small_periodic_box():
    """Review B7-md M1: twelve disks in a periodic 4.2 x 4.2 box (four cells per axis, the smallest allowed) for 200
    time units, sampled every 0.02: no two centres ever nearer than sigma (to rounding)."""
    hs = HardSpheres(2, (4.2, 4.2), seed=3)
    hs.add_species("a")
    hs.fill("a", n=12, T=1.0, arrangement="random")
    worst = 9.0
    for k in range(1, 10001):
        hs.advance(0.02 * k)
        x = hs.positions()
        dx = x[:, None, :] - x[None, :, :]
        dx -= hs.L * np.rint(dx / hs.L)
        r = np.sqrt((dx * dx).sum(-1)) + 9 * np.eye(len(x))
        worst = min(worst, float(r.min()))
    assert worst > 1.0 - 1e-9 and hs.counters()["collisions"] > 1000, worst


def test_walled_box_pressure_is_the_walls():
    """Review B7-md M22: in a box with walls Clausius' theorem takes the walls' impulses at their contact planes
    (sigma/2 from each wall): the collision virial gives the walls' pressure with the accessible length L - sigma per
    walled axis; it agrees with the impulse given to the walls within 4 block standard errors. Negative control: the
    periodic-box formula (2K + W)/V (7 % low here, factor (L - sigma)/L) is rejected."""
    hs = HardSpheres(2, (15.0, 15.0), boundary="walls", seed=4)
    hs.add_species("a")
    hs.fill("a", n=120, T=1.0, arrangement="random")
    hs.advance(20.0)
    diff, old = [], []
    for _ in range(12):
        hs.reset_counters()
        hs.advance(hs.t + 25.0)
        p = hs.pressure()
        pw = float(np.mean(list(p["walls"].values())))
        diff.append(p["pressure"] - pw)
        a = hs._acc
        old.append((2.0 * a["Kdt"] / 2 + a["W"] / 2) / (25.0 * hs.volume()) - pw)
    from lfphys.core.md.observables import block_average
    m, se = block_average(diff, nblocks=12)
    mo, so = block_average(old, nblocks=12)
    assert abs(m) < 4 * se + 1e-12, (m, se)
    assert abs(mo) > 4 * so and mo < 0, (mo, so)


def test_fill_by_density_counts_the_region_and_random_fill():
    """Review B7-md M5 (d), M17: a crystal block at density 0.7 in a 10 x 10 region of a 30 x 30 box gets whole
    triangular cells of that density (not the whole box's count); a random fill places n disks with no two nearer
    than sigma; a too dense random fill is refused and leaves the state as it was."""
    hs = HardSpheres(2, (30.0, 30.0), seed=2)
    hs.add_species("a")
    info = {}
    k = hs.fill("a", density=0.7, region=([10, 10], [20, 20]), T=1.0, info=info)
    assert info["density"] == pytest.approx(0.7, rel=1e-12) and len(k) == 2 * np.prod(info["cells"])
    assert 50 <= len(k) <= 70                               # 0.7 x 100 = 70 at most, whole cells
    x = hs.positions()
    assert x[:, 0].min() > 10 and x[:, 0].max() < 20
    hs.fill("a", n=200, T=1.0, arrangement="random")
    x = hs.positions()
    dx = x[:, None, :] - x[None, :, :]
    dx -= hs.L * np.rint(dx / hs.L)
    r = np.sqrt((dx * dx).sum(-1)) + 9 * np.eye(len(x))
    assert r.min() >= 1.0 - 1e-12
    before = hs.state_dict()
    with pytest.raises(ValueError):
        hs.fill("a", n=2000, T=1.0, arrangement="random")
    after = hs.state_dict()
    for key in ("x", "v", "heap_t", "cnt"):
        assert np.array_equal(before[key], after[key])
    assert before["rng"] == after["rng"]


def test_reference_eos_in_the_engine_and_pooled_ks():
    """The equations of state moved into the engine for the playground's check (z_reference, ensemble_correction)
    equal this file's; the velocity KS pools all species, each by its own mass, and returns no data for none."""
    from lfphys.core.md import hard as HD
    assert HD.z_reference(2, 0.4) == pytest.approx(z_kolafa_rottner(math.pi / 4 * 0.4), rel=1e-15)
    assert HD.z_reference(3, 0.5) == pytest.approx(z_klm(math.pi / 6 * 0.5), rel=1e-15)
    assert HD.ensemble_correction(3, 0.5, 500) == pytest.approx(ensemble_correction(z_klm, 0.5, 3, 500), rel=1e-12)
    assert HD.z_reference(2, 0.95) is None
    hs = HardSpheres(2, (20.0, 20.0), seed=1)
    hs.add_species("a", mass=1.0)
    hs.add_species("b", mass=9.0)
    hs.fill("a", n=150, T=1.0, region=([0, 0], [20, 10]))
    hs.fill("b", n=150, T=1.0, region=([0, 10], [20, 20]))
    ks = hs.velocity_ks()
    assert ks["n"] == 600 and ks["within"]
    hs.remove(hs.keys[:150])
    assert hs.velocity_ks("a")["D"] is None and hs.velocity_ks()["n"] == 300
