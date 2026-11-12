# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Placing matter and changing the box at the current moment (reviews 2026-11-04 UX-ui U4–U7, UX-params P31–P33):
the vectorised random sequential insertion against the one-at-a-time algorithm it replaced (a second method: the same
points, in the same order, from the same generator), many molecules in one edit (the energy bound of every kept atom,
candidates over it left out, a refused edit leaves the state as it was), a crystal that leaves occupied sites empty, an
axis made walled or periodic at the current moment (the potential energy across the joined faces against the closed
form of the pair term; the overlap refusal), and the hard world's pressure at zero temperature."""

import math

import numpy as np
import pytest

from lfphys.core.md import hard as HD
from lfphys.core.md import system as S
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import HarmonicAngle, HarmonicBond, LennardJones


def _reference_random_sites(n, lo, hi, dmin, rng, L, periodic, others=None, others_dmin=None, max_tries=None):
    """The one-at-a-time random sequential insertion as it was before review UX-ui U5 (a dict of cells, one candidate
    per draw): the reference the vectorised version must reproduce point for point."""
    lo, hi, L = np.asarray(lo, float), np.asarray(hi, float), np.asarray(L, float)
    periodic = np.asarray(periodic, bool)
    d = len(lo)
    others = np.zeros((0, d)) if others is None else np.asarray(others, float).reshape(-1, d)
    od = np.zeros(0) if others_dmin is None else np.asarray(others_dmin, float).reshape(-1)
    g = max(float(dmin), float(od.max()) if len(od) else 0.0, 1e-12)
    nc = np.maximum(np.floor(L / g).astype(int), 1)
    nc = np.where(periodic & (nc < 3), 1, nc)
    w = L / nc
    grid = {}

    def cell_of(p):
        return tuple(int(min(max(math.floor(p[a] / w[a]), 0), nc[a] - 1)) for a in range(d))

    for p, dm in zip(others, od):
        grid.setdefault(cell_of(p), []).append((p, dm))
    offs = list(np.ndindex(*([3] * d)))
    out, tries, fails = [], 0, 0
    limit = max_tries if max_tries is not None else 200 * n + 1000
    while len(out) < n:
        tries += 1
        if tries > limit or fails > 20000:
            raise ValueError("jammed")
        p = lo + (hi - lo) * rng.random(d)
        for a in np.flatnonzero(periodic):
            p[a] -= L[a] * math.floor(p[a] / L[a])
        c = cell_of(p)
        ok, seen = True, set()
        for o in offs:
            cc, skip = [], False
            for a in range(d):
                k = c[a] + o[a] - 1
                if periodic[a]:
                    k %= nc[a]
                elif k < 0 or k >= nc[a]:
                    skip = True
                    break
                cc.append(k)
            if skip or tuple(cc) in seen:
                continue
            seen.add(tuple(cc))
            for q, dm in grid.get(tuple(cc), ()):
                dx = q - p
                for a in np.flatnonzero(periodic):
                    dx[a] -= L[a] * round(dx[a] / L[a])
                if float(dx @ dx) < dm * dm:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            out.append(p)
            grid.setdefault(cell_of(p), []).append((p, dmin))
            fails = 0
        else:
            fails += 1
    return np.array(out).reshape(-1, d)


def test_add_molecules_in_a_crowded_batch():
    """Many candidates on top of each other (600 dimers drawn at random in a 15 sigma cube): the earlier ones win, so
    a crowded batch still places a good share (it placed none when overlapping candidates were dropped together)."""
    md = _lj_box(dim=3, L=15.0)
    md.set_bond_type("b", HarmonicBond(400.0, 1.0))
    rng = np.random.default_rng(3)
    c = rng.random((600, 3)) * 15.0
    u = rng.normal(size=(600, 3))
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    X = np.stack([c - 0.5 * u, c + 0.5 * u], 1)
    kept, _, _ = md.add_molecules("A", X, bonds=[(0, 1, "b")], T=3.3, max_energy=6.7, limit=150)
    assert len(kept) == 150
    assert np.all(md._per_particle_energy() <= 6.7 + 1e-12)


@pytest.mark.parametrize("d", [2, 3])
@pytest.mark.parametrize("per", ["all", "none", "mixed"])
@pytest.mark.parametrize("n,n_others", [(1, 0), (40, 0), (300, 0), (120, 60)])
def test_random_sites_equals_one_at_a_time(d, per, n, n_others):
    """The vectorised insertion gives the reference's points exactly, in order, and leaves the generator where the
    reference leaves it (the next draw is the same)."""
    L = np.array([12.0, 10.0, 8.0][:d])
    periodic = {"all": [True] * d, "none": [False] * d, "mixed": [False] + [True] * (d - 1)}[per]
    seed = 17 * d + n + n_others + len(per)
    g0 = np.random.Generator(np.random.PCG64(seed + 1000))
    oth = g0.random((n_others, d)) * L
    od = 0.5 * (1.0 + g0.uniform(0.6, 1.4, n_others))
    r1, r2 = np.random.Generator(np.random.PCG64(seed)), np.random.Generator(np.random.PCG64(seed))
    out = []
    for f, r in ((_reference_random_sites, r1), (S.random_sites, r2)):
        try:
            out.append(f(n, np.full(d, 0.5), L - 0.5, 1.0, r, L, periodic, oth, od))
        except ValueError:
            out.append(None)                   # jammed (300 disks in 11 x 9: both refuse)
    a, b = out
    assert (a is None) == (b is None)
    if a is not None:
        assert a.shape == b.shape and np.array_equal(a, b)
        assert r1.random() == r2.random()


def test_random_sites_jams_like_the_reference():
    """An over-dense region is refused after the same number of tries (and the same error) as the reference."""
    L = np.array([6.0, 6.0])
    for f in (_reference_random_sites, S.random_sites):
        with pytest.raises(ValueError):
            f(80, np.zeros(2), L, 1.0, np.random.Generator(np.random.PCG64(4)), L, [True, True])
    # negative control: a count that fits is placed, none nearer than dmin (minimum image)
    x = S.random_sites(12, np.zeros(2), L, 1.0, np.random.Generator(np.random.PCG64(4)), L, [True, True])
    dx = x[:, None] - x[None]
    dx -= L * np.rint(dx / L)
    r = np.sqrt((dx ** 2).sum(-1)) + np.eye(len(x)) * 9
    assert len(x) == 12 and r.min() >= 1.0


def _lj_box(dim=2, L=10.0, boundary="periodic", rc=2.5):
    md = MD(dim=dim, box=[L] * dim, boundary=boundary, pair=LennardJones(rc, shift="force"), dt=0.004, seed=5)
    md.add_species("A", mass=1.0, sigma=1.0, epsilon=1.0)
    return md


def test_add_molecules_keeps_the_bound_and_leaves_out_overlaps():
    """k dimers in one edit: a candidate over an existing atom (0.3 sigma away) is left out, one at 1.3 sigma is kept,
    of two candidates on top of each other the later one is left out (as one at a time would); every kept atom's
    energy (as the insertion refusal measures it) is within the bound; bonds and molecule keys follow
    the kept candidates; the result is what add_molecule gives for each kept candidate in turn."""
    md = _lj_box()
    md.add("A", [[5.0, 5.0]])
    md.set_bond_type("b", HarmonicBond(100.0, 1.0))
    X = np.array([[[5.3, 5.0], [6.3, 5.0]],      # atom 0.3 sigma from the existing one: out
                  [[2.0, 2.0], [3.0, 2.0]],
                  [[5.0, 6.3], [5.0, 7.3]],      # 1.3 sigma: in
                  [[2.2, 2.1], [3.2, 2.1]],      # on top of candidate 1: the later one is left out
                  [[8.0, 2.0], [9.0, 2.0]]])
    kept, mks, atoms = md.add_molecules("A", X, bonds=[(0, 1, "b")], max_energy=2.0)
    assert list(kept) == [1, 2, 4]
    assert len(mks) == 3 and list(mks) == [0, 1, 2]
    assert atoms.shape == (3, 2) and md.n == 7 and len(md.topology()["bonds"]) == 3
    e = md._per_particle_energy()
    assert np.all(e <= 2.0 + 1e-12)
    # second method: the same two dimers by add_molecule into a copy of the starting state give the same energy
    ref = _lj_box()
    ref.add("A", [[5.0, 5.0]])
    ref.set_bond_type("b", HarmonicBond(100.0, 1.0))
    for c in kept:
        ref.add_molecule("A", X[c], bonds=[(0, 1, "b")], max_energy=2.0)
    assert md.energy() == pytest.approx(ref.energy(), rel=1e-12, abs=1e-12)
    assert np.allclose(md.positions(), ref.positions())
    # with a limit: the first passing candidates in order
    md3 = _lj_box()
    md3.add("A", [[5.0, 5.0]])
    md3.set_bond_type("b", HarmonicBond(100.0, 1.0))
    kept3, _, _ = md3.add_molecules("A", X, bonds=[(0, 1, "b")], max_energy=2.0, limit=2)
    assert list(kept3) == [1, 2] and md3.n == 5


def test_add_molecules_refused_edit_leaves_the_state():
    md = _lj_box()
    md.add("A", [[5.0, 5.0]], v=[[0.3, -0.1]])
    md.set_bond_type("b", HarmonicBond(100.0, 1.0))
    before = md.state_dict()
    with pytest.raises(KeyError):
        md.add_molecules("A", np.zeros((3, 2, 2)) + [[1.0, 1.0], [2.0, 1.0]], bonds=[(0, 1, "nope")])
    after = md.state_dict()
    assert np.array_equal(before["x"], after["x"]) and np.array_equal(before["v"], after["v"])
    # outside the walls: left out, not refused
    w = _lj_box(boundary="walls")
    w.set_bond_type("b", HarmonicBond(100.0, 1.0))
    kept, _, _ = w.add_molecules("A", np.array([[[-0.5, 1.0], [0.5, 1.0]], [[3.0, 3.0], [4.0, 3.0]]]),
                                 bonds=[(0, 1, "b")], T=1.0)
    assert list(kept) == [1] and w.n == 2


def test_add_molecules_angles_and_temperature():
    """Triatomic candidates at T: velocities Maxwellian per atom from the system's generator (deterministic), angles
    attached to the kept molecules only."""
    md = _lj_box(dim=3, L=8.0)
    md.set_bond_type("b", HarmonicBond(100.0, 1.0))
    md.set_angle_type("a", HarmonicAngle(30.0, 1.9))
    tpl = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.3, 0.95, 0.0]])
    X = np.stack([tpl + [1.5 + 2.2 * (i % 3), 1.5 + 2.2 * (i // 3), 4.0] for i in range(9)])
    kept, mks, atoms = md.add_molecules("A", X, bonds=[(0, 1, "b"), (1, 2, "b")], angles=[(0, 1, 2, "a")], T=1.0)
    assert len(kept) == 9 and len(md.topology()["angles"]) == 9 and len(md.molecules()) == 9
    md2 = _lj_box(dim=3, L=8.0)
    md2.set_bond_type("b", HarmonicBond(100.0, 1.0))
    md2.set_angle_type("a", HarmonicAngle(30.0, 1.9))
    md2.add_molecules("A", X, bonds=[(0, 1, "b"), (1, 2, "b")], angles=[(0, 1, 2, "a")], T=1.0)
    assert np.array_equal(md.velocities(), md2.velocities())


def test_set_boundary_energy_across_the_faces_closed_form():
    """Two atoms 0.6 sigma from opposite faces of x: walled, they do not interact (U = 0); made periodic they are 1.2
    sigma apart across the joined faces, U = u_LJ(1.2) of the force-shifted pair term (its own closed form); the edit
    is booked (the first-law residual stays 0); made walled again, U = 0. Negative control: 0.3 sigma from the faces
    (0.6 sigma apart) is refused as an overlap and leaves the state as it was."""
    L = 10.0
    md = _lj_box(L=L, boundary="walls")
    md.add("A", [[0.6, 5.0], [L - 0.6, 5.0]])
    assert md.potential_energy()["pair"] == 0.0
    md.set_boundary("x", "periodic")
    assert bool(md.periodic[0]) and "x-lo" not in md.walls()
    lj = LennardJones(2.5, shift="force")
    T = lj.tables(np.array([1.0]), np.array([1.0]))
    u, _ = lj.evaluate(np.array([1.2 ** 2]), {k: float(T[k][0, 0]) for k in T if k in ("s2", "eps4", "rc2", "ushift", "fshift", "sig", "eps")})
    assert md.potential_energy()["pair"] == pytest.approx(float(u[0]), rel=1e-12)
    assert md.energy_balance()["residual"] == pytest.approx(0.0, abs=1e-12)
    md.set_boundary("x", "walls")
    assert md.potential_energy()["pair"] == 0.0 and set(md.walls()) >= {"x-lo", "x-hi"}
    bad = _lj_box(L=L, boundary="walls")
    bad.add("A", [[0.3, 5.0], [L - 0.3, 5.0]])
    s0 = bad.state_dict()
    with pytest.raises(ValueError):
        bad.set_boundary("x", "periodic")
    assert not bad.periodic[0] and np.array_equal(bad.state_dict()["x"], s0["x"])


def test_set_boundary_walls_keep_the_particles_and_refuse_the_pistons_axis():
    md = _lj_box(L=10.0)
    md.fill("A", n=30, arrangement="random", T=1.0)
    x0 = md.positions().copy()
    md.set_boundary("y", "walls")
    assert np.array_equal(md.positions(), x0) and not md.periodic[1]
    md.set_piston("y", X=10.0, mass=50.0)
    with pytest.raises(ValueError):
        md.set_boundary("y", "periodic")
    md.step(20)
    assert np.all(md.positions()[:, 1] <= md.piston()["X"] + 1e-12)


def test_fill_skips_occupied_sites():
    """A crystal filled over an atom leaves out exactly the sites nearer than sigma_ij to it (counted by brute
    force); the remaining sites are the lattice's; with every site occupied the block is refused."""
    md = _lj_box(L=12.0)
    md.add("A", [[6.1, 6.05]])
    info = {}
    md.fill("A", density=0.8, T=0.0, info=info, skip_occupied=True)
    pos, _ = S.crystal_sites(np.zeros(2), np.full(2, 12.0), 0.8, "auto", np.array([True, True]))
    dx = pos - [6.1, 6.05]
    dx -= 12.0 * np.rint(dx / 12.0)
    near = np.sqrt((dx ** 2).sum(1)) < 1.0
    assert info["skipped"] == int(near.sum()) >= 1
    assert md.n == 1 + len(pos) - int(near.sum())
    with pytest.raises(ValueError):
        md.fill("A", density=0.8, skip_occupied=True)        # the same block again: no free site
    # negative control: without skip_occupied the overlap is refused as before
    md2 = _lj_box(L=12.0)
    md2.add("A", [[6.1, 6.05]])
    with pytest.raises(ValueError):
        md2.fill("A", density=0.8, T=0.0)


def test_hard_pressure_at_zero_temperature():
    """One disk at rest (T = 0): the pressure is 0 and Z has no value (it was a division by zero, review UX-ui U6);
    negative control: two moving disks give a finite Z."""
    hs = HD.HardSpheres(2, (10.0, 10.0), "periodic", seed=1)
    hs.add_species("A", mass=1.0, sigma=1.0)
    hs.add("A", [[5.0, 5.0]])
    hs.advance(1.0)
    p = hs.pressure()
    assert p["Z"] is None and p["pressure"] == 0.0
    hs.add("A", [[2.0, 2.0]], v=[[1.0, 0.3]])
    hs.reset_counters()
    hs.advance(5.0)
    assert hs.pressure()["Z"] is not None and math.isfinite(hs.pressure()["Z"])


def test_hard_set_boundary():
    """Hard disks: a periodic axis made walled when no disk is within sigma/2 of its faces (else refused, state kept);
    walls made periodic again; the dynamics goes on (no overlap)."""
    hs = HD.HardSpheres(2, (10.0, 10.0), "periodic", seed=2)
    hs.add_species("A", mass=1.0, sigma=1.0)
    hs.add("A", [[0.3, 5.0]])
    with pytest.raises(ValueError):
        hs.set_boundary("x", "walls")
    assert hs.periodic[0]
    hs2 = HD.HardSpheres(2, (10.0, 10.0), "periodic", seed=2)
    hs2.add_species("A", mass=1.0, sigma=1.0)
    hs2.fill("A", density=0.3, region=([1.0, 1.0], [9.0, 9.0]), T=1.0)
    hs2.set_boundary("x", "walls")
    assert not hs2.periodic[0] and "x-lo" in hs2._walls
    hs2.advance(3.0)
    x = hs2.positions()
    assert np.all(x[:, 0] >= 0.5 - 1e-9) and np.all(x[:, 0] <= 9.5 + 1e-9)
    hs2.set_boundary("x", "periodic")
    assert hs2.periodic[0] and "x-lo" not in hs2._walls
    hs2.advance(5.0)
