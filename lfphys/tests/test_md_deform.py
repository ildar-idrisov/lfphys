# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The box at the current moment and the solver switch (plan P16.1, LB1): ``MD.deform`` (an affine deformation of the
box with the matter: the canonical point transformation x -> lambda x, p -> p / lambda; or a wall moved over empty
space), its work in the first law, and ``core.md.hard`` taking particles over from ``MD`` and back.

References: the adiabat of an ideal gas (T V^(2/d) = const, P V^((d+2)/d) = const; a collisionless gas compressed along
one axis keeps K_a L_a^2 - the adiabatic invariant of a particle bouncing between walls), and a slow driven piston as
its second method; the first-order work dE = -sum_a S_aa V delta_a with the affine stress (equal to -P dV with the
virial pressure only without a field, soft walls and frozen atoms: review LB1-physics P2), the trapezoid converging at
second order; the Jacobian of the map (review P9); the reversibility of a slow change against the dissipation of a jump
(review P3: ``ramp_box``); the hard-sphere walls on the centres (review P4); and negative controls: scaling the positions
only (Berendsen's barostat) misses the ideal gas's adiabat by (V0/V1)^(2/d), the virial pressure misses the first-order
work with a field, soft walls or frozen atoms, single jumps dissipate, walls on the surfaces refuse the switch."""

import math

import numpy as np
import pytest

from lfphys.core.md import hard as HD
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import WCA, HarmonicBond, LennardJones, LJWall


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


def _gas(dim, n=200, L=30.0, pair=None, T=1.0, seed=1, boundary="periodic"):
    md = MD(dim=dim, box=[L] * dim, boundary=boundary, pair=pair, dt=0.004, seed=seed)
    md.add_species("a")
    md.fill("a", n=n, T=T, arrangement="random")
    return md


# --- the ideal gas: the adiabat, exactly ------------------------------------------------------------------------------
@pytest.mark.parametrize("dim", [2, 3])
def test_ideal_gas_isotropic_deformation_is_the_adiabat(dim):
    """Isotropic compression and expansion of an ideal gas, in one step or many: P V^gamma (gamma = (d+2)/d) is kept to
    rounding, the work booked is the energy change and equals the adiabat's closed form (P1 V1 - P0 V0)/(gamma - 1),
    the first law closes exactly, the momentum is kept."""
    g = (dim + 2) / dim
    for steps in (1, 7):
        md = _gas(dim)
        P0, V0, E0 = md.pressure()["virial"], md.volume(), md.energy()
        mom0 = md.momentum()
        for k in range(steps):
            md.deform([30.0 * (1.0 - 0.3 * (k + 1) / steps)] * dim)
        P1, V1 = md.pressure()["virial"], md.volume()
        assert P1 * V1 ** g == pytest.approx(P0 * V0 ** g, rel=1e-12)
        b = md.energy_balance()
        assert b["W_box"] == pytest.approx(md.energy() - E0, rel=1e-12)
        assert b["W_box"] == pytest.approx((P1 * V1 - P0 * V0) / (g - 1.0), rel=1e-12)
        assert abs(b["residual"]) < 1e-12 * abs(b["W_box"])
        assert np.allclose(md.momentum(), mom0, atol=1e-12)
        # and back: the same adiabat
        md.deform([30.0] * dim)
        assert md.pressure()["virial"] == pytest.approx(P0, rel=1e-12)
        assert md.energy_balance()["W_box"] == pytest.approx(0.0, abs=1e-9)


def test_ideal_gas_uniaxial_keeps_the_adiabatic_invariant():
    """Along one axis of a collisionless gas between walls each particle keeps |v_a| L_a (the adiabatic invariant):
    K_aa L_a^2 is constant through compression and the dynamics between the steps, the other axes are untouched (the
    one-dimensional adiabat, gamma = 3)."""
    md = _gas(2, boundary="walls")
    Ka0 = 0.5 * np.sum(md.velocities() ** 2, axis=0)
    for k in range(10):
        md.deform([30.0, 30.0 * (1.0 - 0.05 * (k + 1))])
        md.step(20)
    Ka1 = 0.5 * np.sum(md.velocities() ** 2, axis=0)
    assert Ka1[0] == pytest.approx(Ka0[0], rel=1e-12)
    assert Ka1[1] * md.L[1] ** 2 == pytest.approx(Ka0[1] * 30.0 ** 2, rel=1e-12)
    assert abs(md.energy_balance()["residual"]) < 1e-9


@pytest.mark.parametrize("dim", [2, 3])
def test_negative_control_positions_only_misses_the_adiabat(dim):
    """The control: the same compression by scaling the positions only (Berendsen's barostat: a new box, the same
    velocities) leaves T and so misses P V^gamma by (V0/V1)^(2/d) - 1 (0.43 in 2-D, 0.27 in 3-D here), far beyond the
    1e-12 the canonical step keeps; and it books no work although -int P dV is not zero."""
    g = (dim + 2) / dim
    md = _gas(dim)
    P0, V0 = md.pressure()["virial"], md.volume()
    lam = 0.7
    ctl = MD(dim=dim, box=[30.0 * lam] * dim, pair=None, dt=0.004, seed=1)
    ctl.add_species("a")
    ctl.add("a", md.positions() * lam, v=md.velocities())
    P1, V1 = ctl.pressure()["virial"], ctl.volume()
    miss = P1 * V1 ** g / (P0 * V0 ** g) - 1.0
    assert miss == pytest.approx((V0 / V1) ** (-2.0 / dim) - 1.0, rel=1e-9)
    assert abs(miss) > 0.2
    assert ctl.energy() == pytest.approx(md.energy(), rel=1e-12)      # no work, against -int P dV != 0
    md.deform([30.0 * lam] * dim)
    assert md.pressure()["virial"] * md.volume() ** g == pytest.approx(P0 * V0 ** g, rel=1e-12)


# --- the first-order work: the affine stress (review LB1-physics P2) -----------------------------------------------------
def _periodic_lj():
    md = _gas(2, 150, 20.0, LennardJones(2.5), seed=4)
    md.step(200)
    return md


def _field_gas():
    md = _gas(2, 150, 20.0, None, seed=5, boundary="walls")
    md.set_gravity([0.0, -0.5])
    md.step(2000)
    return md


def _soft_walled():
    md = MD(dim=2, box=[20.0, 20.0], boundary=["periodic", "walls"], pair=LennardJones(2.5), dt=0.004, seed=6)
    md.add_species("a")
    md.set_wall("y", "lo", "soft", term=LJWall(2))
    md.set_wall("y", "hi", "soft", term=LJWall(2))
    md.fill("a", n=150, T=1.5, region=([0.0, 2.0], [20.0, 18.0]), arrangement="random")
    md.step(500)
    return md


def _frozen_block():
    md = MD(dim=2, box=[20.0, 20.0], boundary="walls", pair=LennardJones(2.5), dt=0.004, seed=7)
    md.add_species("w", mass=math.inf)
    md.add_species("a")
    md.fill("w", density=0.9, region=([8.0, 8.0], [12.0, 12.0]))
    md.fill("a", n=60, T=1.5, region=([0.5, 0.5], [19.5, 7.0]), arrangement="random")
    md.step(300)
    return md


@pytest.mark.parametrize("make,affine", [(_periodic_lj, True), (_field_gas, False), (_soft_walled, False),
                                         (_frozen_block, False)])
def test_first_order_work_is_minus_the_affine_stress_times_dv(make, affine):
    """dE of a uniaxial jump by delta against the trapezoid of the affine stress before and after: the trapezoid of a
    smooth path errs by O(delta^3), so (dE - pdv)/dE falls as delta^2 (x 1/100 per decade, derived; asserted within
    20 %, and below delta: the first order is exact). The virial pressure gives the same where it is the affine stress
    (the periodic control) and misses at first order where a force it omits acts (negative control: a field, soft walls,
    frozen atoms - the reviewer's -0.61, +0.19, -0.36)."""
    rel, rel_v = [], []
    for delta in (1e-3, 1e-4, 1e-5):
        md = make()
        L = md.L.copy()
        L[1] *= 1 + delta
        o = md.deform(L)
        assert o["virial_is_affine"] is affine
        rel.append((o["dE"] - o["pdv"]) / o["dE"])
        if o["pdv_virial"] is not None:
            rel_v.append((o["dE"] - o["pdv_virial"]) / o["dE"])
    for r, delta in zip(rel, (1e-3, 1e-4, 1e-5)):
        assert abs(r) < delta, rel
    assert abs(rel[0] / rel[1]) == pytest.approx(100.0, rel=0.2) and abs(rel[1] / rel[2]) == pytest.approx(100.0, rel=0.2)
    if affine:
        assert all(abs(r) < d for r, d in zip(rel_v, (1e-3, 1e-4, 1e-5)))
    else:
        assert rel_v and min(abs(r) for r in rel_v) > 0.1, rel_v


def test_trapezoid_of_a_pure_deformation_converges_at_second_order():
    """A Lennard-Jones fluid compressed along x by 15 % in N jumps with nothing between them (the path in configuration
    space is the same for every N): the summed difference of the booked work and the trapezoid of the affine stress is
    sum over steps of O(delta^3), so it falls as 1/N^2 - x4 per doubling (derived; asserted within 20 %); the work
    itself does not depend on N beyond that, and the first law closes exactly (no dynamics)."""
    diffs, Ws = [], []
    for N in (8, 16, 32):
        md = MD(dim=2, box=[16.0, 16.0], pair=LennardJones(2.5), dt=0.004, seed=3)
        md.add_species("a")
        md.fill("a", n=100, T=1.5, arrangement="random")
        md.step(100)
        md.reset_counters()
        W = PDV = 0.0
        for k in range(N):
            o = md.deform([16.0 * (1 - 0.15 * (k + 1) / N), 16.0])
            W += o["dE"]
            PDV += o["pdv"]
        b = md.energy_balance()
        assert b["W_box"] == pytest.approx(W, rel=1e-12)
        assert abs(b["residual"]) <= 1e-12 * abs(W) * N
        diffs.append(abs(W - PDV))
        Ws.append(W)
    assert diffs[0] / diffs[1] == pytest.approx(4.0, rel=0.2) and diffs[1] / diffs[2] == pytest.approx(4.0, rel=0.2)
    assert Ws[0] == Ws[1] == Ws[2] or abs(Ws[0] - Ws[2]) < 1e-9 * abs(Ws[2])   # the same path: the same work


# --- the Jacobian of the map (review LB1-physics P9) --------------------------------------------------------------------
@pytest.mark.parametrize("boundary,expect", [("periodic", 0.9 * 1.1), ("walls", 1.0)])
def test_jacobian_is_one_relative_to_the_centre_of_mass(boundary, expect):
    """The map deform makes, differentiated numerically on 3 free particles in 2-D: along an axis whose momentum is
    conserved (periodic) the centre of mass is moved by lambda with its momentum kept, so det J = lambda per such axis
    (0.9 x 1.1 here); with walls (no conserved momentum) it is the canonical point transformation, det J = 1."""
    m = np.array([1.0, 2.0, 1.5])
    x0 = np.array([[1.0, 2.0], [3.0, 1.5], [2.5, 3.5]])
    v0 = np.array([[0.3, -0.2], [0.1, 0.4], [-0.5, 0.2]])
    lam = np.array([0.9, 1.1])

    def image(z):
        md = MD(dim=2, box=[5.0, 5.0], boundary=boundary, pair=None, dt=0.01, seed=1)
        for i in range(3):
            md.add_species(f"s{i}", mass=m[i])
            md.add(f"s{i}", z[:6].reshape(3, 2)[i:i + 1], v=z[6:].reshape(3, 2)[i:i + 1])
        md.deform(5.0 * lam)
        p = md.particles()
        return np.concatenate([np.asarray(p["x"]).reshape(-1), (np.asarray(p["v"]) * m[:, None]).reshape(-1)])

    z0 = np.concatenate([x0.reshape(-1), v0.reshape(-1)])
    h = 1e-6
    J = np.zeros((12, 12))
    for k in range(12):
        dz = np.zeros(12)
        dz[k] = h
        if k >= 6:      # perturb a momentum: the velocity by h / m
            dz[k] = h / m[(k - 6) // 2]
        J[:, k] = (image(z0 + dz) - image(z0 - dz)) / (2 * h)
    assert np.linalg.det(J) == pytest.approx(expect, rel=1e-6)


def test_deformation_keeps_momentum_and_is_deterministic():
    """A gas thrown as a whole along a periodic axis: the deformation scales the peculiar velocities about the centre
    of mass, so the conserved momentum stays; the same calls give the same state bit for bit, and a saved state
    continues bit for bit."""
    def run():
        md = MD(dim=3, box=[9.0, 9.0, 9.0], pair=LennardJones(2.5), dt=0.004, seed=4)
        md.add_species("a")
        k = md.fill("a", n=150, T=1.0, arrangement="random")
        md.set(k, v=md.particles(k)["v"] + [0.5, 0.0, 0.0])
        md.step(20)
        P = md.momentum()
        md.deform([8.5, 9.2, 9.0])
        assert np.allclose(md.momentum(), P, atol=1e-11)
        return md
    a, b = run(), run()
    assert _same(a, b)
    c = MD.from_state_dict(a.state_dict())
    a.step(30)
    c.step(30)
    assert _same(a, c)


# --- refusals ---------------------------------------------------------------------------------------------------------
def test_refused_deformations_leave_the_state_bit_for_bit():
    md = MD(dim=2, box=(10.0, 12.0), boundary=["periodic", "walls"], pair=LennardJones(2.5), dt=0.004, seed=2)
    md.add_species("A")
    md.fill("A", density=0.8, T=0.5, region=([0.0, 0.5], [10.0, 6.0]))
    md.set_bond_type("b", HarmonicBond(400.0, 1.0))
    md.add_molecule("A", [[5.0, 9.0], [6.0, 9.0]], bonds=[(0, 1, "b")])
    md.set_piston("y", X=11.0, mass=50.0, p_ext=0.1)
    md.step(10)
    before = md.state_dict()
    bad = [lambda: md.deform([10.0, 13.0]),                                # the piston's axis, affine
           lambda: md.deform([10.0, 10.5], mode="wall"),                   # the stop below the piston's face
           lambda: md.deform([11.0, 12.0], mode="wall"),                   # a periodic axis has no wall
           lambda: md.deform([6.0, 12.0]),                                 # the crystal squeezed: overlap
           lambda: md.deform([11.5, 12.0], max_bond_strain=0.1),           # the bond along x stretched by 15 %
           lambda: md.deform([10.0, -1.0])]
    for f in bad:
        with pytest.raises(ValueError):
            f()
        assert _same(md, before), f
    o = md.deform([10.4, 12.0], max_bond_strain=0.1)                      # 4 %: accepted
    assert o["bond_strain"] == pytest.approx(0.04, rel=0.05)
    md.step(5)


def test_wall_mode_adds_and_removes_empty_space():
    """A wall moved over empty space does no work (specular): the energy is unchanged, W_box = 0; the gas then
    expands freely into it (Joule): its energy stays, its temperature (ideal gas) stays. Removing space where a
    particle is beyond the new wall is refused."""
    md = MD(dim=2, box=(20.0, 10.0), boundary="walls", pair=None, dt=0.004, seed=5)
    md.add_species("a")
    md.fill("a", n=40, T=1.0, region=([0.0, 0.0], [10.0, 10.0]), arrangement="random")
    E0 = md.energy()
    with pytest.raises(ValueError):
        md.deform([9.0, 10.0], mode="wall")
    md.deform([12.0, 10.0], mode="wall")        # removes empty space
    md.deform([30.0, 10.0], mode="wall")        # adds it
    assert md.energy() == E0 and md.energy_balance()["W_box"] == 0.0
    md.step(4000)
    assert md.energy() == pytest.approx(E0, rel=1e-12)
    assert np.max(md.positions()[:, 0]) > 20.0       # the gas went into the new space


# --- hard spheres ---------------------------------------------------------------------------------------------------
def test_hard_spheres_box_wall_mode_only():
    hs = HD.HardSpheres(2, (12.0, 12.0), ["periodic", "walls"], seed=1)
    hs.add_species("a")
    hs.fill("a", n=40, T=1.0, region=([0.0, 0.5], [12.0, 6.0]), arrangement="random")
    hs.advance(2.0)
    before = hs.state_dict()
    for f in (lambda: hs.deform([12.0, 14.0], mode="affine"),
              lambda: hs.deform([13.0, 12.0], mode="wall"),
              lambda: hs.deform([12.0, 3.0], mode="wall")):
        with pytest.raises(ValueError):
            f()
        sa = hs.state_dict()
        assert np.array_equal(sa["x"], before["x"]) and np.array_equal(sa["L"], before["L"])
    K = hs.kinetic_energy()
    hs.deform([12.0, 20.0], mode="wall")
    assert hs.L[1] == 20.0 and hs.kinetic_energy() == K
    hs.advance(30.0)
    assert hs.kinetic_energy() == pytest.approx(K, rel=1e-12)
    assert np.max(hs.positions()[:, 1]) > 12.0


# --- the solver switch: soft <-> hard -------------------------------------------------------------------------------
def test_switch_soft_to_hard_and_back_keeps_the_state():
    """MD -> hard -> MD at the current moment: the same keys, species, positions, velocities, time and walls; the
    kinetic energy is the same; going to forces the potential energy appears (the energy jump)."""
    md = MD(dim=2, box=(20.0, 20.0), boundary=["periodic", "walls"], pair=WCA(), dt=0.004, seed=3)
    md.add_species("a", mass=2.0, sigma=1.0)
    md.add_species("b", sigma=0.8)
    md.fill("a", n=40, T=1.0, region=([0.0, 1.0], [20.0, 19.0]), arrangement="random")
    md.fill("b", n=30, T=1.0, region=([0.0, 1.0], [20.0, 19.0]), arrangement="random")
    md.set_wall("y", "hi", "thermal", T=1.5)
    cv = HD.contact_violations(md.positions(), [1.0] * 40 + [0.8] * 30, md.L, md.periodic)
    assert cv["pairs"] == 0 and cv["walls"] == 0        # random sequential insertion: no pair inside contact
    hs = HD.hard_from_md(md, seed=9)
    assert hs.t == md.t and np.array_equal(hs.keys, md.keys)
    assert np.array_equal(hs.positions(), md.positions()) and np.array_equal(hs.velocities(), md.velocities())
    assert hs.kinetic_energy() == pytest.approx(md.kinetic_energy(), rel=1e-14)
    assert hs._walls["y-hi"]["kind"] == "thermal" and hs._walls["y-hi"]["T"] == 1.5
    hs.advance(hs.t + 1.0)
    back = HD.md_from_hard(hs, LennardJones(2.5), 0.004, seed=11, species_extra={"b": {"epsilon": 0.5}})
    assert back.t == hs.t and np.array_equal(back.keys, hs.keys)
    assert np.allclose(back.positions(), np.where(hs.periodic, hs.positions() % hs.L, hs.positions()), atol=1e-12)
    assert np.array_equal(back.velocities(), hs.velocities())
    jump = back.energy() - hs.kinetic_energy()
    assert jump == pytest.approx(back.potential_energy()["total"], rel=1e-12)
    assert [s["epsilon"] for s in back.species()] == [1.0, 0.5]
    assert back.walls()["y-hi"]["kind"] == "thermal"
    back.step(20)     # and it runs


def test_switch_to_hard_refuses_overlaps_and_what_it_has_not():
    md = MD(dim=2, box=(10.0, 10.0), pair=LennardJones(2.5), dt=0.004, seed=1)
    md.add_species("a")
    md.add("a", [[2.0, 2.0], [2.9, 2.0], [6.0, 6.0]])     # one pair at 0.9 sigma
    cv = HD.contact_violations(md.positions(), np.ones(3), md.L, md.periodic)
    assert cv["pairs"] == 1 and cv["closest"] == pytest.approx(0.9)
    with pytest.raises(ValueError, match="1 pairs"):
        HD.hard_from_md(md)
    md.remove(md.keys[1:2])
    assert HD.hard_from_md(md).n == 2
    md.set_gravity([0.0, -0.1])
    md.add_thermostat("csvr", T=1.0, tau=1.0)
    assert HD.hard_blockers(md) == ["thermostats", "field"]
    with pytest.raises(ValueError, match="thermostats, field"):
        HD.hard_from_md(md)
    w = MD(dim=2, box=(10.0, 10.0), boundary="walls", pair=LennardJones(2.5), dt=0.004, seed=1)
    w.add_species("a")
    w.add("a", [[0.2, 5.0], [5.0, 5.0]])                    # a centre 0.2 sigma from a wall
    # walls on the surfaces (the negative control) refuse it; on the centres, as MD's walls, it switches (review P4)
    assert HD.contact_violations(w.positions(), np.ones(2), w.L, w.periodic)["walls"] == 1
    assert HD.contact_violations(w.positions(), np.ones(2), w.L, w.periodic, walls_on="centre")["walls"] == 0
    with pytest.raises(ValueError, match="1 centres"):
        HD.hard_from_md(w, walls_on="surface")
    hs = HD.hard_from_md(w)
    assert hs.walls_on == "centre" and np.array_equal(hs.positions(), w.positions())


# --- a change of the box over a time: the quasi-static limit (review LB1-physics P3) ---------------------------------
def _fluid(seed):
    md = MD(dim=2, box=[16.0, 16.0], pair=LennardJones(2.5), dt=0.004, seed=seed)
    md.add_species("a")
    md.fill("a", n=100, T=1.5, arrangement="random")
    md.step(500)
    md.reset_counters()
    return md


def _cycle(seed, tau):
    """x compressed by 15 % and back: by one jump each way (tau 0, relaxing 1.6 time units after each) or by ramps of
    duration tau each way; returns (the net work of the cycle, the compression's work, the first law's residual)."""
    md = _fluid(seed)
    if tau == 0:
        md.deform([13.6, 16.0])
        Wc = md.energy_balance()["W_box"]
        md.step(400)
        md.deform([16.0, 16.0])
        md.step(400)
    else:
        md.ramp_box([13.6, 16.0], tau)
        while md.ramp_running():
            md.step(1)
        Wc = md.energy_balance()["W_box"]
        md.ramp_box([16.0, 16.0], tau)
        while md.ramp_running():
            md.step(1)
        assert md.box_ramp()["done"] and md.L[0] == 16.0
    b = md.energy_balance()
    return b["W_box"], Wc, b["residual"]


def test_a_slow_ramp_is_reversible_and_a_jump_dissipates():
    """A 2-D Lennard-Jones fluid (100 atoms, rho 0.39, T 1.5) compressed along x by 15 % and returned, NVE, four seeds.
    A quasi-static adiabatic cycle returns to its energy: the net work tends to 0 as the ramp slows. The negative
    control - single jumps (the review's +183 epsilon) - dissipates about 1 epsilon per atom; a fast ramp (tau 1, about
    one sound crossing of the box) dissipates less, a slow one (tau 8) nothing measurable. Tolerances from the
    seeds' own scatter (standard errors; the cycle's work fluctuates by about sqrt(2 kT <W_diss>))."""
    def stats(tau):
        w = np.array([_cycle(s, tau)[0] for s in (3, 4, 5, 6)])
        return w.mean(), w.std(ddof=1) / 2.0
    jm, js = stats(0)
    fm, fs = stats(1.0)
    sm, ss = stats(8.0)
    assert jm > 50.0 and jm > 3 * js                    # the jump dissipates (0.5 epsilon per atom at least)
    assert fm > 3 * fs and fm < 0.2 * jm                # a fast ramp: less, but measurably
    assert abs(sm) <= 3 * ss + 1e-9 and abs(sm) < 0.02 * jm
    assert fm - sm > 3 * math.hypot(fs, ss)              # slower is more reversible
    W, Wc, res = _cycle(3, 8.0)
    assert abs(res) < 1e-2 * abs(Wc)                     # the first law closes at the integrator's level


def test_ramp_of_an_ideal_gas_is_the_adiabat_and_agrees_with_a_slow_piston():
    """A collisionless gas compressed along y (walls) from 30 to 21: a ramp keeps K_y L_y^2 to rounding at any rate
    (each substep is the exact adiabatic step) and books W = dE; the second method - the engine's driven piston moving
    the hi wall at speed w - approaches the same as w / v_th -> 0 (the deviation falls with w), and its work tends to
    the ramp's."""
    base = _gas(2, 400, 30.0, None, seed=2, boundary=["periodic", "walls"])
    Ky0 = 0.5 * float(np.sum(base.velocities()[:, 1] ** 2))
    r = MD.from_state_dict(base.state_dict())
    E0 = r.energy()
    r.ramp_box([30.0, 21.0], 5.0)
    while r.ramp_running():
        r.step(1)
    Ky = 0.5 * float(np.sum(r.velocities()[:, 1] ** 2))
    assert Ky * 21.0 ** 2 == pytest.approx(Ky0 * 900.0, rel=1e-12)
    W_ramp = r.energy_balance()["W_box"]
    assert W_ramp == pytest.approx(r.energy() - E0, rel=1e-12)
    dev, work = [], []
    for w in (0.05, 0.01):
        p = MD.from_state_dict(base.state_dict())
        p.set_dt(0.05)
        p.set_piston("y", X=30.0, V=-w)
        while p.piston()["X"] > 21.0 + 1e-12:
            left = (p.piston()["X"] - 21.0) / w
            if left < p.dt:
                p.set_dt(left)
            p.step(1)
        Kp = 0.5 * float(np.sum(p.velocities()[:, 1] ** 2))
        dev.append(abs(Kp * p.piston()["X"] ** 2 / (Ky0 * 900.0) - 1.0))
        work.append(p.counters()["piston"]["work"])
    assert dev[1] < dev[0] and dev[1] < 2e-3, dev
    assert abs(work[1] - W_ramp) < abs(work[0] - W_ramp) and work[1] == pytest.approx(W_ramp, rel=2e-3)


def test_ramp_books_its_work_keeps_momentum_continues_bit_for_bit_and_refuses():
    md = _fluid(4)
    k = md.keys
    md.set(k, v=md.particles(k)["v"] + [0.3, 0.0])     # a moving fluid: its momentum is kept by the ramp
    P0 = md.momentum()
    rec = md.ramp_box([15.0, 16.5], 2.0)
    assert rec["running"] and rec["n"] == 1
    with pytest.raises(ValueError, match="ramp is running"):
        md.deform([15.0, 16.0])
    md.step(100)
    assert md.L[0] < 16.0 and md.L[1] > 16.0
    c = MD.from_state_dict(md.state_dict())
    md.step(400)
    c.step(400)
    assert _same(md, c)
    r = md.box_ramp()
    assert r["done"] and not r["running"] and list(md.L) == [15.0, 16.5] and r["steps"] == 500
    b = md.energy_balance()
    assert b["W_box"] == pytest.approx(r["W"], rel=1e-12)
    assert r["pdv"] == pytest.approx(r["W"], rel=2e-2)          # the work of a slow-ish change is about -int S dV
    assert np.allclose(md.momentum(), P0, atol=1e-10)
    assert md.momentum_drift()["ratio"] <= 1.0
    with pytest.raises(ValueError, match="per step"):
        md.ramp_box([10.0, 16.5], 0.1)                          # 0.1 time units: 0.14 % a step
    with pytest.raises(ValueError, match="cutoff"):
        md.ramp_box([5.0, 16.5], 100.0)
    w = MD(dim=2, box=(12.0, 12.0), boundary="walls", pair=LennardJones(2.5), dt=0.004, seed=2)
    w.add_species("a")
    w.fill("a", n=30, T=1.0, region=([0.0, 0.0], [12.0, 8.0]), arrangement="random")
    w.set_piston("y", X=10.0, mass=50.0)
    with pytest.raises(ValueError, match="piston"):
        w.ramp_box([12.0, 13.0], 5.0)
    w.ramp_box([13.0, 12.0], 5.0)
    w.step(10)
    w.stop_box_ramp("test")
    r = w.box_ramp()
    assert r["stopped"] == "test" and not r["running"] and 12.0 < w.L[0] < 13.0
    w.step(10)
    assert 12.0 < w.L[0] < 13.0                                   # stopped where it was


# --- hard spheres with walls on the centres (review LB1-physics P4) -------------------------------------------------
@pytest.mark.parametrize("walls_on", ["centre", "surface"])
def test_hard_walls_contact_plane_by_the_virial_identity(walls_on):
    """d/dt sum m x_y v_y = 2 K_y + (impulsive forces) x_y: integrated over a run of hard disks between walls on y, the
    collision virial, the kinetic integral and the walls' impulses at their contact planes balance exactly (to
    rounding): L Imp_hi with walls on the centres, (L - sigma/2) Imp_hi - sigma/2 Imp_lo with walls on the surfaces. The
    other plane misses by the impulses times sigma/2 (the negative control)."""
    hs = HD.HardSpheres(2, (20.0, 20.0), ["periodic", "walls"], seed=3, walls_on=walls_on)
    hs.add_species("a")
    hs.fill("a", n=60, T=1.0, region=([0.0, 1.0], [20.0, 19.0]), arrangement="random")
    hs.advance(1.0)
    hs.reset_counters()

    def G():
        x = hs.positions()
        return float(np.sum(x[:, 1] * hs.velocities()[:, 1]))
    G0 = G()
    hs.advance(hs.t + 50.0)
    acc = hs._acc
    hs._accumulate(hs.t)
    lhs = 2.0 * float(acc["Kadt"][1]) + float(acc["Wa"][1]) - (G() - G0)
    lo, hi = hs._walls["y-lo"]["impulse"], hs._walls["y-hi"]["impulse"]
    planes = {"centre": (0.0, 20.0), "surface": (0.5, 19.5)}
    a, b = planes[walls_on]
    other_a, other_b = planes["surface" if walls_on == "centre" else "centre"]
    right = b * hi - a * lo
    wrong = other_b * hi - other_a * lo
    assert lhs == pytest.approx(right, rel=1e-9)
    assert abs(lhs - wrong) > 1e-3 * abs(lhs)
    p = hs.pressure()
    assert p["tensor"][1] == pytest.approx(0.5 * (p["walls"]["y-lo"] + p["walls"]["y-hi"]), rel=0.1)


def test_switch_with_walls_on_centres_is_never_refused_by_the_walls():
    """An equilibrated WCA gas in a walled box (the review's case n 20, L 20: 170 of 200 moments refused by the walls):
    with the walls on the centres no moment is refused by them, and the round trip keeps every position (the same
    region of the centres, the same density); the negative control - walls on the surfaces - refuses most moments."""
    md = MD(dim=2, box=[20.0, 20.0], boundary="walls", pair=WCA(), dt=0.004, seed=8)
    md.add_species("a")
    md.fill("a", n=20, T=1.0, region=([1.0, 1.0], [19.0, 19.0]), arrangement="random")
    by_walls = {"centre": 0, "surface": 0}
    for _ in range(40):
        md.step(25)
        for won in by_walls:
            cv = HD.contact_violations(md.positions(), np.ones(md.n), md.L, md.periodic, walls_on=won)
            by_walls[won] += cv["walls"] > 0 and cv["pairs"] == 0
    assert by_walls["centre"] == 0 and by_walls["surface"] > 10, by_walls
    while HD.contact_violations(md.positions(), np.ones(md.n), md.L, md.periodic, walls_on="centre")["pairs"]:
        md.step(5)
    hs = HD.hard_from_md(md)
    back = HD.md_from_hard(hs, WCA(), 0.004)
    assert np.array_equal(back.positions(), md.positions()) and not back.centres_region_grew


def test_add_molecules_keep_all_takes_every_molecule_or_none():
    md = MD(dim=2, box=(12.0, 12.0), pair=LennardJones(2.5), dt=0.004, seed=1)
    md.add_species("a")
    md.set_bond_type("b", HarmonicBond(400.0, 1.0))
    X = np.array([[[2.0, 2.0], [3.0, 2.0]], [[3.85, 2.0], [4.85, 2.0]], [[8.0, 8.0], [9.0, 8.0]]])  # 2nd: 0.85 sigma
    kept, mk, ak = md.add_molecules("a", X, bonds=[(0, 1, "b")], keep_all=True)
    assert list(kept) == [0, 1, 2] and np.array_equal(md.positions(), X.reshape(-1, 2))
    m2 = MD(dim=2, box=(12.0, 12.0), pair=LennardJones(2.5), dt=0.004, seed=1)
    m2.add_species("a")
    m2.set_bond_type("b", HarmonicBond(400.0, 1.0))
    kept, _, _ = m2.add_molecules("a", X, bonds=[(0, 1, "b")])                 # the default leaves the 2nd out
    assert list(kept) == [0, 2]
    m3 = MD(dim=2, box=(12.0, 12.0), pair=LennardJones(2.5), dt=0.004, seed=1)
    m3.add_species("a")
    m3.set_bond_type("b", HarmonicBond(400.0, 1.0))
    X[1] = [[2.1, 2.0], [3.1, 2.0]]                                              # on top of the first: refused whole
    with pytest.raises(ValueError, match="overlap"):
        m3.add_molecules("a", X, bonds=[(0, 1, "b")], keep_all=True)
    assert m3.n == 0
