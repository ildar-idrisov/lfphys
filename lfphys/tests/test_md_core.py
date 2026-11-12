# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Molecular dynamics (plan P8): neighbour search, forces as gradients, the integrator's error and symmetries, edits,
state, units, cost. Physics references: tests/test_md_thermo.py, test_md_lj.py, test_md_hard.py, test_md_bonds.py."""

import math

import numpy as np
import pytest

from lfphys.core.md import cells
from lfphys.core.md.system import MD
from lfphys.core.md.units import Units
from lfphys.theories.models.interatomic import (FENE, WCA, CosineAngle, HarmonicAngle, HarmonicBond, LennardJones,
                                                 LJWall, SoftRepulsion, argon_units)


# --- neighbour search ------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("dim,per", [(3, (1, 1, 1)), (3, (1, 0, 1)), (3, (0, 0, 0)), (2, (1, 1)), (2, (0, 1)),
                                     (2, (0, 0))])
def test_pair_list_equals_all_pairs(dim, per):
    """The cell list gives exactly the pairs of the direct O(N^2) search (each once), periodic or walled axes."""
    rng = np.random.default_rng(7)
    L = np.array([9.0, 7.6, 8.3][:dim])
    per = np.array(per, bool)
    for n, r in ((400, 2.8), (1000, 1.3), (60, 3.7)):
        x = rng.random((n, dim)) * L
        i, j = cells.pair_list(x, L, per, r)
        bi, bj = cells._brute(x, L, per, r)
        a = {tuple(p) for p in np.sort(np.stack([i, j], 1), 1)}
        b = {tuple(p) for p in np.sort(np.stack([bi, bj], 1), 1)}
        assert len(a) == len(i) and a == b
        # deterministic: the same input gives the same list
        i2, j2 = cells.pair_list(x, L, per, r)
        assert np.array_equal(i, i2) and np.array_equal(j, j2)


# --- forces are the gradient of the energy ---------------------------------------------------------------------------
def _scene(dim, pair):
    """A small mixed scene: two species with charges, a bonded triatomic and a diatomic with every bonded term, soft
    LJ walls on the lo sides, gravity; all axes walled (Coulomb by the direct sum)."""
    L = [7.0, 6.5, 6.0][:dim]
    md = MD(dim=dim, box=L, boundary="walls", pair=pair, dt=0.002, seed=3, max_insert_energy=1e9,
            gravity=[0.1, -0.2, 0.05][:dim])
    md.add_species("A", mass=1.0, sigma=1.0, epsilon=1.0, charge=0.4)
    md.add_species("B", mass=2.5, sigma=1.2, epsilon=0.7, charge=-0.3)
    md.add_species("C", mass=1.5, sigma=0.9, epsilon=1.3, charge=0.0)
    for a in range(dim):
        md.set_wall(a, "lo", "soft", term=LJWall(dim, epsilon=0.8, sigma=1.0, cutoff=2.5, mixing=True))
    md.set_bond_type("h", HarmonicBond(k=150.0, r0=1.05))
    md.set_bond_type("f", FENE(k=30.0, R0=1.6))
    md.set_angle_type("a", HarmonicAngle(k=40.0, theta0=1.9))
    md.set_angle_type("c", CosineAngle(k=25.0, theta0=2.2))
    rng = np.random.default_rng(11)
    c = np.array(L) / 2
    pts = c + np.array([[0, 0, 0], [1.0, 0.3, 0.2], [1.7, 1.1, -0.3], [-1.4, 0.9, 0.6], [-2.1, 1.5, 0.1]])[:, :dim]
    md.add_molecule(["A", "B", "C", "A", "C"], pts, bonds=[(0, 1, "h"), (1, 2, "f"), (0, 3, "h"), (3, 4, "f")],
                    angles=[(0, 1, 2, "a"), (1, 0, 3, "c"), (0, 3, 4, "a")])
    free = c + np.array([[0.4, -2.0, -1.2], [-1.0, -1.6, 1.5], [2.3, -1.2, 1.0], [-2.6, -0.4, -1.9]])[:, :dim]
    free += 0.05 * rng.standard_normal(free.shape)
    md.add("A", free[:2])
    md.add("B", free[2:3])
    md.add("C", free[3:])
    return md


@pytest.mark.parametrize("dim", [2, 3])
@pytest.mark.parametrize("pair", [LennardJones(2.5, "energy"), LennardJones(2.5, "force"), LennardJones(3.0, "none"),
                                  WCA(), SoftRepulsion(2.0), SoftRepulsion(2.5)],
                         ids=["lj-energy", "lj-force", "lj-none", "wca", "soft2", "hertz"])
def test_forces_are_minus_the_gradient(dim, pair):
    """Every force (pair, Coulomb, bonds, FENE, angles in theta and in cos theta, LJ walls 9-3 / 10-4, the field) is
    -dU/dx: central differences of the total potential energy, Richardson-extrapolated (error O(h^4) + round-off
    ~1e-16 |U| / h)."""
    md = _scene(dim, pair)
    F = md.forces()
    keys = md.keys
    x0 = md.positions(unwrapped=True)
    scale = float(np.max(np.abs(F)))

    def U(k, a, dx):
        x = x0[k].copy()
        x[a] += dx
        md.set([keys[k]], x=x)
        return md.potential_energy()["total"]

    worst = 0.0
    for k in range(md.n):
        for a in range(dim):
            h = 1e-4
            d1 = (U(k, a, h) - U(k, a, -h)) / (2 * h)
            d2 = (U(k, a, h / 2) - U(k, a, -h / 2)) / h
            fd = -(4 * d2 - d1) / 3
            md.set([keys[k]], x=x0[k])
            worst = max(worst, abs(fd - F[k, a]))
    assert worst < 1e-7 * max(scale, 1.0), (worst, scale)


def test_angle_term_regular_near_linear():
    """Harmonic angle with theta0 = pi (a linear molecule): the force is finite and correct at theta -> pi (the
    limit (theta - pi)/sin theta -> -1 is used where sin theta underflows)."""
    md = MD(dim=3, box=(8, 8, 8), boundary="walls", pair=None, dt=0.001, max_insert_energy=1e9)
    md.add_species("A")
    md.set_bond_type("b", HarmonicBond(100.0, 1.0))
    md.set_angle_type("lin", HarmonicAngle(30.0, math.pi))
    for eps in (0.0, 1e-9, 1e-3):
        mol, keys = md.add_molecule("A", [[3, 4, 4], [4, 4, 4], [5, 4 + eps, 4]], bonds=[(0, 1, "b"), (1, 2, "b")],
                                    angles=[(0, 1, 2, "lin")])
        F = md.forces()
        assert np.all(np.isfinite(F))
        # the bending force on an end atom: k (pi - theta) / r towards the line, theta = pi - eps (small)
        theta = math.pi - math.atan2(eps, 1.0)
        assert abs(F[2, 1] - (-30.0 * (math.pi - theta) / math.hypot(1.0, eps))) < 1e-6
        md.remove_molecule(mol)


# --- the integrator --------------------------------------------------------------------------------------------------
def _clear(md, pts, r):
    """Remove the particles closer than r (minimum image) to any of the points (room for an insertion)."""
    x = md.positions()
    near = np.zeros(md.n, bool)
    for p in pts:
        dx = x - p
        for a in np.flatnonzero(md.periodic):
            dx[:, a] -= md.L[a] * np.rint(dx[:, a] / md.L[a])
        near |= np.einsum("ij,ij->i", dx, dx) < r * r
    if near.any():
        md.remove(md.keys[near])


def _liquid(pair, n=256, rho=0.75, T=1.2, seed=1, dim=3):
    L = (n / rho) ** (1.0 / dim)
    md = MD(dim=dim, box=[L] * dim, pair=pair, dt=0.004, seed=seed)
    md.add_species("A")
    md.fill("A", n=n, T=T)
    md.step(600)
    return md


def _max_energy_error(base, dt, t_run=1.0):
    m = MD.from_state_dict(base.state_dict())
    m.set_dt(dt)
    E0 = m.energy()
    err = 0.0
    for _ in range(int(round(t_run / dt))):
        m.step()
        err = max(err, abs(m.energy() - E0))
    return err


def test_nve_energy_error_is_second_order():
    """Velocity Verlet: the energy error over a fixed interval scales as dt^2 for a potential with a continuous force
    (force-shifted LJ): halving dt divides it by 4 (measured 3.97-4.02; tolerance 3.6-4.4). Negative control: the
    energy-shifted LJ (force jump u'(r_c) at the cut) loses the dt^2 law at small dt (pairs crossing r_c add an error
    that does not fall as dt^2): its ratio at dt 0.002 -> 0.001 is below 3.4."""
    base = _liquid(LennardJones(2.5, "force"))
    e = [_max_energy_error(base, dt) for dt in (0.004, 0.002, 0.001)]
    for a, b in zip(e, e[1:]):
        assert 3.6 < a / b < 4.4, e
    assert e[0] / base.n < 2e-4          # per particle at dt = 0.004
    neg = _liquid(LennardJones(2.5, "energy"))
    en = [_max_energy_error(neg, dt) for dt in (0.002, 0.001)]
    assert en[0] / en[1] < 3.4, en


def test_time_reversibility():
    """v -> -v after n steps and n more steps return to the start (to round-off amplified by the dynamics' chaos over
    0.4 time units): periodic LJ, and a walled box with specular walls and a bonded molecule."""
    md = _liquid(LennardJones(2.5, "force"), n=200)
    x0 = md.positions(True)
    v0 = md.velocities()
    md.step(100)
    md.reverse()
    md.step(100)
    assert np.max(np.abs(md.positions(True) - x0)) < 1e-9
    assert np.max(np.abs(md.velocities() + v0)) < 1e-9
    w = MD(dim=2, box=(12, 10), boundary="walls", pair=WCA(), dt=0.002, seed=4)
    w.add_species("A")
    w.set_bond_type("b", HarmonicBond(80.0, 1.1))
    w.fill("A", n=60, T=1.0, region=([0, 3], [12, 10]))
    w.add_molecule("A", [[1, 1], [2.1, 1.0], [2.6, 2.0]], bonds=[(0, 1, "b"), (1, 2, "b")], T=1.0)
    x0, v0 = w.positions(), w.velocities()
    w.step(200)
    assert sum(c["hits"] for c in w.counters()["walls"].values()) > 0
    w.reverse()
    w.step(200)
    assert np.max(np.abs(w.positions() - x0)) < 1e-9 and np.max(np.abs(w.velocities() + v0)) < 1e-9


def test_momentum_is_conserved_in_a_periodic_box():
    """Pair, bond and angle forces are summed antisymmetrically: the total momentum stays at its value to round-off
    (relative to the momentum scale sum m |v|), with molecules and a CSVR bath (a global rescaling keeps P = 0)."""
    md = _liquid(LennardJones(2.5), n=200, rho=0.6)
    md.set_bond_type("b", HarmonicBond(100.0, 1.0))
    md.set_angle_type("a", HarmonicAngle(20.0, 2.0))
    L = md.L
    atoms = np.array([[0.2, 0.3, 0.4], [L[0] - 0.6, 0.3, 0.4], [L[0] - 1.1, 1.1, 0.4]])
    _clear(md, atoms, 1.6)
    md.add_molecule("A", atoms, bonds=[(0, 1, "b"), (1, 2, "b")], angles=[(0, 1, 2, "a")], T=1.0)  # across the edge
    p0 = md.momentum()
    scale = float(np.sum(np.abs(md.velocities())))
    md.add_thermostat("csvr", T=1.0, tau=0.1)
    md.set([md.keys[0]], v=md.velocities()[0] - p0)   # zero total momentum
    p0 = md.momentum()
    md.step(500)
    assert np.max(np.abs(md.momentum() - p0)) < 1e-12 * scale
    assert md.momentum_conserved() and md.dof()[0] == 3 * md.n - 3


def test_companion_step_error():
    """step_error: the dt/2 companion's estimate (4/3 of the difference) agrees with the true error of the dt run
    against a dt/16 reference within 10 % over 10 steps (second order: the estimate's own error is O(dt^3))."""
    md = _liquid(LennardJones(2.5, "force"), n=200)
    est = md.step_error(10)
    a = MD.from_state_dict(md.state_dict())
    ref = MD.from_state_dict(md.state_dict())
    ref.set_dt(md.dt / 16)
    a.step(10)
    ref.step(160)
    dx = a.positions(True) - ref.positions(True)
    true = float(np.max(np.sqrt(np.einsum("ij,ij->i", dx, dx))))
    assert abs(est["dx_max_estimate"] / true - 1) < 0.1, (est, true)
    with pytest.raises(ValueError):
        md.add_thermostat("langevin", T=1.0, gamma=1.0)
        md.step_error(5)


# --- edits and state -------------------------------------------------------------------------------------------------
def _same(a, b):
    sa, sb = a.state_dict(), b if isinstance(b, dict) else b.state_dict()
    for k in sa:
        va, vb = sa[k], sb[k]
        if isinstance(va, np.ndarray):
            if not (va.shape == vb.shape and np.array_equal(va, vb)):
                return False
        elif k == "rng":
            if va != vb:
                return False
        elif k not in ("stats",):
            if repr(va) != repr(vb):
                return False
    return True


def test_refused_edits_leave_the_state_bit_for_bit():
    md = MD(dim=2, box=(10, 10), boundary=["periodic", "walls"], pair=LennardJones(2.5), dt=0.005, seed=2)
    md.add_species("A")
    md.add_species("Q", charge=1.0)
    keys = md.fill("A", n=40, T=1.0)
    md.add_thermostat("langevin", T=1.0, gamma=0.5)
    md.step(20)
    before = md.state_dict()
    x = md.positions()
    bad = [lambda: md.add("A", x[0] + [0.05, 0.0]),                     # overlap
           lambda: md.add("A", [5.0, 10.5]),                            # outside the walls
           lambda: md.add("Q", [5.0, 5.0]),                             # charge with a periodic axis
           lambda: md.set_pair(LennardJones(5.0)),                      # cutoff + skin > L/2
           lambda: md.set(keys[:2], x=[x[3], x[3] + [0.01, 0.0]]),      # overlap by a move
           lambda: md.set_piston("x"),                                  # periodic axis
           lambda: md.set_species("A", sigma=3.5),                      # cutoff 2.5 * 3.5 > L/2
           lambda: md.add_thermostat("csvr", T=1.0)]                    # no tau
    for f in bad:
        with pytest.raises((ValueError, KeyError)):
            f()
        assert _same(md, before), f
    # an accepted edit after refusals continues normally
    _clear(md, np.array([[5.0, 9.0]]), 1.5)
    md.add("A", [5.0, 9.0])
    md.step(5)


def test_state_round_trip_is_bit_identical():
    """Save and restore mid-run: the restored copy continues bit for bit (positions, velocities, the generator, the
    counters) with molecules, a Langevin bath in a region, a CSVR bath, a thermal wall, a soft wall, a free piston,
    gravity."""
    md = MD(dim=3, box=(8, 8, 12), boundary=["periodic", "periodic", "walls"], pair=LennardJones(2.5, "force"),
            dt=0.004, seed=9, gravity=(0, 0, -0.05))
    md.add_species("A")
    md.add_species("B", mass=2.0, sigma=1.1)
    md.set_bond_type("b", HarmonicBond(100.0, 1.1))
    md.set_angle_type("a", HarmonicAngle(30.0, 2.0))
    md.fill("A", n=120, T=1.0, region=([0, 0, 0.5], [8, 8, 7]))
    md.add_molecule("B", [[1, 1, 8], [2.1, 1, 8], [2.6, 2, 8]], bonds=[(0, 1, "b"), (1, 2, "b")],
                    angles=[(0, 1, 2, "a")], T=1.0)
    md.set_wall("z", "lo", "thermal", T=1.5)
    md.set_piston("z", X=11.0, mass=20.0, p_ext=0.05)
    md.add_thermostat("langevin", T=1.0, gamma=1.0, region=([0, 0, 0], [8, 4, 12]))
    md.add_thermostat("csvr", T=1.2, tau=0.2, species="B")
    md.msd_origin()
    md.step(150)
    d = md.state_dict()
    twin = MD.from_state_dict(d)
    md.step(150)
    twin.step(150)
    assert np.array_equal(md.positions(True), twin.positions(True))
    assert np.array_equal(md.velocities(), twin.velocities())
    assert md.counters() == twin.counters() and md.energy_balance() == twin.energy_balance()
    assert md.piston()["X"] == twin.piston()["X"]
    # the plain-data part is plain: lists, numbers, str, None, dicts and NumPy arrays only
    def plain(z):
        if isinstance(z, dict):
            return all(isinstance(k, (str, int)) and plain(v) for k, v in z.items())
        if isinstance(z, (list, tuple)):
            return all(plain(v) for v in z)
        return z is None or isinstance(z, (bool, int, float, str, np.ndarray, np.integer, np.floating))
    assert plain(d)


def test_live_edits_act_at_the_current_moment():
    """add / remove / set / species / walls / baths / field mid-run; untouched particles keep their state bit for bit
    through an edit; the first-law balance carries the energy an edit changes into E0."""
    md = MD(dim=2, box=(12, 12), boundary="walls", pair=LennardJones(2.5, "force"), dt=0.004, seed=5)
    md.add_species("A")
    md.add_species("B", mass=3.0)
    k = md.fill("A", n=50, T=1.0, region=([0, 0], [12, 10]))
    md.step(50)
    x, v = md.positions(), md.velocities()
    kb = md.add("B", [[6.0, 11.5]], v=[[0.0, -1.0]])
    assert np.array_equal(md.positions()[:50], x) and np.array_equal(md.velocities()[:50], v)
    md.remove(k[:5])
    md.set(kb, v=[[0.5, -0.5]])
    md.set_species("B", mass=2.0, epsilon=1.5)
    md.set_wall("x", "lo", "thermal", T=2.0)
    md.set_gravity([0.0, -0.1])
    bath = md.add_thermostat("csvr", T=1.0, tau=0.5, region=([0, 0], [6, 12]))
    md.set_thermostat(bath, T=1.3)
    md.step(50)
    md.remove_thermostat(bath)
    md.step(10)
    assert md.n == 46 and math.isfinite(md.energy())
    bal = md.energy_balance()
    assert abs(bal["residual"]) < 1e-3 * md.n   # the integrator's error only (force-shifted LJ, dt = 0.004)


# --- units -----------------------------------------------------------------------------------------------------------
def test_units_argon():
    """Reduced units of argon (sigma = 3.405 A, eps/k = 119.8 K, m = 39.948 u): tau = sigma sqrt(m/eps) = 2.156 ps,
    pressure unit eps/sigma^3 = 419 bar, density unit m/sigma^3 = 1.68 g/cm^3, charge unit sqrt(4 pi eps0 sigma eps)
    = e / 20.2; conversions are exact inverses."""
    from scipy import constants as sc
    u = argon_units()
    eps = 119.8 * sc.k
    m = 39.948 * sc.atomic_mass
    s = 3.405e-10
    assert u.to_ps(1.0) == pytest.approx(s * math.sqrt(m / eps) / 1e-12, rel=1e-15)
    assert u.to_ps(1.0) == pytest.approx(2.156, abs=1e-3)
    assert u.to_bar(1.0) == pytest.approx(eps / s ** 3 / 1e5, rel=1e-15) and 418 < u.to_bar(1.0) < 420
    assert u.to_kg_m3(1.0) == pytest.approx(m / s ** 3, rel=1e-15)
    assert u.to_elementary_charge(1.0) == pytest.approx(math.sqrt(4 * math.pi * sc.epsilon_0 * s * eps) / sc.e,
                                                        rel=1e-15)
    for f, g in ((u.to_ps, u.from_ps), (u.to_kelvin, u.from_kelvin), (u.to_bar, u.from_bar),
                 (u.to_angstrom, u.from_angstrom), (u.to_amu, u.from_amu),
                 (u.to_elementary_charge, u.from_elementary_charge)):
        assert g(f(1.234)) == pytest.approx(1.234, rel=1e-15)
    assert u.to_kelvin(1.0) == pytest.approx(119.8, rel=1e-15)
    assert isinstance(Units.from_lj(1.0, 1.0, 1.0).table(2)["pressure_N_per_m"], float)


def test_cost_estimate_and_bench():
    from lfphys.core.md.observables import bench, md_step_model
    rows = bench(LennardJones(2.5), ns=(100,), dims=(2,), steps=5)
    assert rows and rows[0]["s_per_step"] > 0
    md = _liquid(LennardJones(2.5), n=200)
    c = md.cost_estimate()
    assert c["measured_per_step_s"] > 0 and c["per_step_s"] == md_step_model(md.n, c["pairs"], 3)


# --- review B7-md ------------------------------------------------------------------------------------------------------
def test_momentum_drift_against_its_rounding_bound():
    """Review B7-md M8: an atom launched at 5 sigma/tau into a periodic NVE liquid: P is not zero but conserved;
    momentum_drift() compares |P - P_ref| (P_ref at the last edit) with its rounding bound and passes over 600 steps.
    The bound is a worst case (rounding errors added linearly over the steps, each force sum with its full term count):
    here ~4e-10 against a measured drift below 1e-13. Negative control: a velocity changed behind the engine's back by
    1e-7 (P changes by 1e-7, 2e-11 of sum m|v|) gives a ratio far above 1; a world without conserved components gives
    no ratio."""
    md = _liquid(LennardJones(2.5, "force"), n=200, rho=0.6)
    _clear(md, np.array([[1.0, 1.0, 1.0]]), 1.2)
    md.add("A", [1.0, 1.0, 1.0], v=[5.0, 0.0, 0.0])
    assert abs(md.momentum()[0]) > 4.0
    md.step(600)
    d = md.momentum_drift()
    assert d["steps"] == 600 and d["axes"] == [True, True, True]
    assert d["ratio"] <= 1.0 and max(d["drift"]) < 1e-11, d
    md._v[0, 1] += 1e-7
    assert md.momentum_drift()["ratio"] > 10.0
    md.set_gravity([0.0, 0.0, -0.1])
    assert md.momentum_drift()["axes"] == [True, True, False]
    md.add_thermostat("langevin", T=1.0, gamma=1.0)
    assert md.momentum_drift()["ratio"] is None


def test_set_species_refuses_overlaps():
    """Review B7-md M14: sigma 1 -> 1.4 in a dense liquid (an energy of 10^4 per particle) is refused like an
    overlapping insertion and leaves the state bit for bit; sigma 1 -> 1.02 is accepted."""
    md = _liquid(LennardJones(2.5, "force"), n=500, rho=0.8)
    before = md.state_dict()
    with pytest.raises(ValueError, match="overlap"):
        md.set_species("A", sigma=1.4)
    assert _same(md, before)
    md.set_species("A", sigma=1.02)
    md.step(5)
    assert math.isfinite(md.energy())


def test_frozen_atoms_virial_is_the_walls_pressure():
    """Review B7-md M13: a block of frozen atoms in a walled 2-D box with an LJ gas. Frozen-frozen pairs are not in
    the pair list; the virial of the moving atoms (sum over them of x . F, the frozen atoms external) gives the
    pressure on the hi walls: per axis, (integral of (2K_a + W_a) dt - Delta sum m x_a v_a) / (V Delta t) equals the
    impulse the hi wall received, block by block within 4 standard errors (12 blocks of 10 tau). Negative control: the
    pair virial over all pairs with the frozen ones (the reviewed formula) is rejected. Along a periodic axis the
    virial with frozen atoms is undefined (None)."""
    md = MD(dim=2, box=(20.0, 20.0), boundary="walls", pair=LennardJones(2.5, "force"), dt=0.004, seed=21)
    md.add_species("A")
    md.add_species("W", mass=math.inf)
    g = np.arange(8.0, 12.01, 1.0)
    md.add("W", np.array([[a, b] for a in g for b in g]))
    pts = np.array([[x, y] for x in np.arange(1.0, 19.6, 1.25) for y in np.arange(1.0, 19.6, 1.25)
                    if not (6.5 < x < 13.5 and 6.5 < y < 13.5)])
    md.add("A", pts[:250], T=1.0)
    md.step(2000)
    nl = md._nl
    assert not np.any(~md._mobile[nl["i"]] & ~md._mobile[nl["j"]])
    mob = md._mobile
    pair = md.pair
    tab = md._tables

    def old_virial():
        i, j = cells.pair_list(md._x, md.L, md.periodic, 2.5)
        dx = md._x[j] - md._x[i]
        P = {k: tab[k].reshape(-1)[md._typ[i] * 2 + md._typ[j]] for k in ("s2", "eps4", "rc2", "ushift", "fshift")
             if k in tab}
        _, fr = pair.evaluate(np.einsum("ij,ij->i", dx, dx), P)
        return np.einsum("i,ij->j", fr, dx * dx)

    dev, dev_old = [], []
    for _ in range(12):
        md.reset_counters()
        G0 = np.sum(md._m[mob, None] * md._x[mob] * md._v[mob], axis=0)
        acc, acc_old, k = np.zeros(2), np.zeros(2), 0
        for _ in range(250):
            md.step(10)
            kin = md.kinetic_tensor()
            acc += kin + md._vir
            acc_old += kin + old_virial()
            k += 1
        G1 = np.sum(md._m[mob, None] * md._x[mob] * md._v[mob], axis=0)
        dt = md.t - md.counters()["t0"]
        V = md.volume()
        p = md.pressure()["walls"]
        hi = np.array([p["x-hi"], p["y-hi"]])
        dev.append((acc / k * dt - (G1 - G0)) / (V * dt) - hi)
        dev_old.append((acc_old / k * dt - (G1 - G0)) / (V * dt) - hi)
    dev, dev_old = np.array(dev), np.array(dev_old)
    for a in range(2):
        m, se = dev[:, a].mean(), dev[:, a].std(ddof=1) / math.sqrt(12)
        mo, so = dev_old[:, a].mean(), dev_old[:, a].std(ddof=1) / math.sqrt(12)
        assert abs(m) < 4 * se + 1e-3, (a, m, se)
        assert abs(mo) > 4 * so + 1e-3, (a, mo, so)
    slab = MD(dim=2, box=(20.0, 20.0), boundary=["periodic", "walls"], pair=LennardJones(2.5, "force"), seed=2)
    slab.add_species("A")
    slab.add_species("W", mass=math.inf)
    slab.add("W", [[10.0, 10.0]])
    slab.add("A", [[5.0, 5.0]], v=[1.0, 0.5])
    t = slab.pressure()["tensor"]
    assert t[0] is None and t[1] is not None and slab.pressure()["virial"] is None


def test_degrees_of_freedom_by_axis():
    """Review B7-md M21, M9: in a slab (walls in y, periodic x) without a field P_x is conserved and N_f = dN - 1;
    a field along y keeps that; a thermal wall (diffuse re-emission) breaks it (N_f = dN)."""
    md = MD(dim=2, box=(12.0, 12.0), boundary=["periodic", "walls"], pair=LennardJones(2.5, "force"), dt=0.004,
            seed=3)
    md.add_species("A")
    md.fill("A", n=100, T=1.0, region=([0, 1], [12, 11]))
    md.set(md.keys[:1], v=md.velocities()[:1] + [2.0, 0.0])
    px = md.momentum()[0]
    md.step(300)
    assert md.momentum_conserved_axes().tolist() == [True, False] and md.dof()[0] == 199
    assert abs(md.momentum()[0] - px) < 1e-12 * abs(px) + 1e-13
    md.set_gravity([0.0, -0.05])
    assert md.dof()[0] == 199
    md.set_wall("y", "lo", "thermal", T=1.0)
    assert md.dof()[0] == 200 and not md.momentum_conserved()


def test_crystal_sites_random_sites_and_probe():
    """Review B7-md M17, M18: a crystal block has the lattice of the requested density (nearest-neighbour distance
    (2/(sqrt(3) rho))^(1/2) in 2-D; fcc a/sqrt(2) in 3-D), whole cells in a region, a lattice fitted to a periodic box
    it spans (strain reported, no vacancy strip); a random fill keeps sigma between particles and is not a lattice;
    the probe counts the particles in a ball with the minimum image and the ball's volume inside the walls."""
    from lfphys.core.md.system import crystal_sites
    pts, info = crystal_sites([1.0, 2.0], [11.0, 12.0], 0.85, "hex")
    a = math.sqrt(2 / (math.sqrt(3) * 0.85))
    d = np.sqrt(((pts[:, None] - pts[None]) ** 2).sum(-1)) + 99 * np.eye(len(pts))
    assert d.min() == pytest.approx(a, rel=1e-12) and info["density"] == pytest.approx(0.85, rel=1e-12)
    assert np.all(pts > [1, 2]) and np.all(pts < [11, 12])
    p3, i3 = crystal_sites([0, 0, 0], [9, 9, 9], 1.0, "fcc", full=[True, True, True])
    assert i3["cells"] == [6, 6, 6] and i3["strain"] < 0.06 and len(p3) == 864
    md = MD(dim=2, box=(29.37, 29.37), pair=LennardJones(2.5, "force"), seed=1)
    md.add_species("A")
    inf = {}
    md.fill("A", density=0.85, T=0.1, info=inf)
    x = md.positions()
    gap = np.max(np.diff(np.sort(np.r_[x[:, 0], x[:, 0].min() + md.L[0]])))
    assert gap < 1.0 and abs(inf["density"] - 0.85) < 0.03 and md.n == 2 * np.prod(inf["cells"])
    g = MD(dim=2, box=(20.0, 20.0), pair=LennardJones(2.5, "force"), seed=2)
    g.add_species("A")
    g.fill("A", n=150, T=1.0, arrangement="random")
    x = g.positions()
    dx = x[:, None] - x[None]
    dx -= g.L * np.rint(dx / g.L)
    r = np.sqrt((dx ** 2).sum(-1)) + 99 * np.eye(150)
    assert r.min() >= 1.0 - 1e-12 and len(np.unique(np.round(x[:, 0], 9))) == 150
    c = np.array([1.0, 10.0])
    dxc = x - c
    dxc -= g.L * np.rint(dxc / g.L)
    inside = int(np.sum((dxc ** 2).sum(1) <= 9.0))
    pr = g.probe(c, 3.0)
    assert pr["n"] == inside and pr["volume"] == pytest.approx(math.pi * 9.0, rel=1e-12)
    w = MD(dim=2, box=(20.0, 20.0), boundary="walls", pair=None, seed=2)
    w.add_species("A")
    w.fill("A", n=100, T=1.0)
    assert w.probe([0.0, 10.0], 3.0)["volume"] == pytest.approx(0.5 * math.pi * 9.0, rel=0.03)


def test_bond_order_closed_forms():
    """psi_6 of a triangular lattice is 1; the global Q_6 of fcc is 0.5745 and equals the addition theorem's
    (sum over bond pairs of P_6(cos gamma)) / N_b^2, a second method; a random configuration gives ~N^-1/2."""
    from scipy.special import eval_legendre

    from lfphys.core.md.observables import bond_order
    from lfphys.core.md.system import crystal_sites
    a = math.sqrt(2 / (math.sqrt(3) * 0.9))
    p2, _ = crystal_sites([0, 0], [20 * a, 12 * a * math.sqrt(3)], 0.9, "hex", full=[True, True])
    assert bond_order(p2, [20 * a, 12 * a * math.sqrt(3)], [True, True], 1.4 * a)["psi6_global"] == pytest.approx(
        1.0, abs=1e-12)
    L = 3 * (4.0 / 1.0) ** (1 / 3)
    p3, _ = crystal_sites([0, 0, 0], [L] * 3, 1.0, "fcc", full=[True] * 3)
    q6 = bond_order(p3, [L] * 3, [True] * 3, 1.3)["Q6"]
    i, j = cells.pair_list(p3, np.full(3, L), np.ones(3, bool), 1.3)
    b = p3[j] - p3[i]
    b -= L * np.rint(b / L)
    u = b / np.linalg.norm(b, axis=1, keepdims=True)
    second = math.sqrt(np.mean(eval_legendre(6, u @ u.T)))
    assert q6 == pytest.approx(second, rel=1e-10) and q6 == pytest.approx(0.57452, abs=1e-5)
    x = np.random.default_rng(1).random((800, 3)) * 10
    assert bond_order(x, [10] * 3, [True] * 3, 1.5)["Q6"] < 4 / math.sqrt(800)


def test_hard_walls_make_the_energy_error_first_order():
    """Review B7-md M11: a hard wall's impulse inside the drift is not resolved by the Verlet splitting when the atoms
    interact (an error of order F v dt per hit): the energy error of an LJ gas (100 atoms at T = 2.5, random start, 4
    time units, the largest |E - E0| averaged over six seeds) in a walled box falls only by ~3 when dt falls by 4
    (measured 0.341 -> 0.110: first order), while in the same box made periodic it falls by ~15 (0.059 -> 0.0040:
    second order, the control). The threshold 8 lies between first (4) and second (16) order."""
    def err(bd, dt):
        e = []
        for seed in range(1, 7):
            md = MD(dim=2, box=(16.0, 16.0), boundary=bd, pair=LennardJones(2.5, "force"), dt=dt, seed=seed)
            md.add_species("A")
            md.fill("A", n=100, T=2.5, arrangement="random")
            E0 = md.energy()
            m = 0.0
            for _ in range(10):
                md.advance(md.t + 0.4)
                m = max(m, abs(md.energy() - E0))
            e.append(m)
        return float(np.mean(e))
    walls = err("walls", 0.004) / err("walls", 0.001)
    per = err("periodic", 0.004) / err("periodic", 0.001)
    assert walls < 8.0 < per, (walls, per)
