# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Molecular dynamics (plan P8): bonds, angles and Coulomb against closed forms.

The vibration frequencies are read off the trajectory through the velocity-Verlet map itself: for a linear oscillator
the positions obey y_{n+1} + y_{n-1} = (2 - omega^2 dt^2) y_n exactly, so the least-squares coefficient
c = sum (y_{n+1} + y_{n-1}) y_n / (2 sum y_n^2) gives omega^2 = 2 (1 - c) / dt^2 - the closed-form omega^2 of the
model (k/mu for a bond) to round-off for a free diatomic, to the small-amplitude nonlinearity for a bend; and the
oscillation's own frequency (zero crossings) is the map's arccos(1 - omega^2 dt^2/2)/dt, not omega (negative control:
they differ by (omega dt)^2/24, 2.8e-4 here, far above the measurement's resolution)."""

import math

import numpy as np
import pytest

from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import CosineAngle, HarmonicAngle, HarmonicBond


def _omega2(y, dt):
    y = np.asarray(y, float)
    c = np.sum((y[2:] + y[:-2]) * y[1:-1]) / (2 * np.sum(y[1:-1] ** 2))
    return 2 * (1 - c) / dt ** 2


def _crossing_frequency(y, dt):
    s = np.flatnonzero(np.sign(y[1:]) != np.sign(y[:-1]))
    tc = (s + y[s] / (y[s] - y[s + 1])) * dt        # linear interpolation of the zero crossings
    return math.pi * (len(tc) - 1) / (tc[-1] - tc[0])


@pytest.mark.parametrize("dim", [2, 3])
def test_harmonic_bond_frequency(dim):
    """A free diatomic (m1 = 1, m2 = 3, k = 200, r0 = 1.1) vibrating along a fixed axis (no rotation): omega^2 = k/mu
    to 1e-9; the zero-crossing frequency is the Verlet map's (to 2e-6), not k/mu's (2.8e-4 apart)."""
    dt, k, r0, m1, m2 = 0.005, 200.0, 1.1, 1.0, 3.0
    md = MD(dim=dim, box=[10.0] * dim, boundary="walls", pair=None, dt=dt)
    md.add_species("A", mass=m1)
    md.add_species("B", mass=m2)
    md.set_bond_type("ab", HarmonicBond(k, r0))
    u = np.array([1.0, 2.0, 2.0][:dim])
    u /= np.linalg.norm(u)
    c = np.full(dim, 5.0)
    r = r0 + 0.01
    M = m1 + m2
    md.add_molecule(["A", "B"], [c - u * r * m2 / M, c + u * r * m1 / M], bonds=[(0, 1, "ab")])
    y = []
    for _ in range(2000):
        x = md.positions()
        y.append(np.linalg.norm(x[1] - x[0]) - r0)
        md.step()
    mu = m1 * m2 / M
    w2 = k / mu
    assert abs(_omega2(y, dt) / w2 - 1) < 1e-9
    assert HarmonicBond(k, r0).omega2(mu) == w2
    w_map = math.acos(1 - w2 * dt * dt / 2) / dt
    wc = _crossing_frequency(np.array(y), dt)
    assert abs(wc / w_map - 1) < 2e-6
    assert abs(wc / math.sqrt(w2) - 1) > 2e-4
    assert np.max(np.abs(md.momentum())) < 1e-13                # no net force


@pytest.mark.parametrize("dim", [2, 3])
@pytest.mark.parametrize("form", ["theta", "cos"])
def test_angle_bending_frequency(dim, form):
    """Two atoms (m = 1) bonded stiffly (k_b = 1000) at r0 = 1 to a frozen central atom, angle term with k = 50 at
    theta0 = 1.9: bending and stretching decouple at linear order, the bend obeys theta'' = -(2 k_eff / m r0^2)
    (theta - theta0) with k_eff = k (harmonic in theta) or k sin^2 theta0 (harmonic in cos theta). Amplitude 1e-3 rad:
    omega^2 within 1e-4 (the nonlinearity is O(amplitude^2)). Negative control: the free-atom guess k/(m r0^2)
    (without the factor 2 of the two moving arms) is rejected."""
    dt, kb, r0, k, th0, m = 0.002, 1000.0, 1.0, 50.0, 1.9, 1.0
    md = MD(dim=dim, box=[10.0] * dim, boundary="walls", pair=None, dt=dt)
    md.add_species("C", mass=math.inf)
    md.add_species("A", mass=m)
    md.set_bond_type("b", HarmonicBond(kb, r0))
    md.set_angle_type("a", HarmonicAngle(k, th0) if form == "theta" else CosineAngle(k, th0))
    c = np.full(dim, 5.0)
    d = 1e-3
    def at(phi):
        e = np.zeros(dim)
        e[0], e[1] = math.cos(phi), math.sin(phi)
        return c + r0 * e
    md.add_molecule(["A", "C", "A"], [at(-(th0 + d) / 2), c, at((th0 + d) / 2)], bonds=[(0, 1, "b"), (1, 2, "b")],
                    angles=[(0, 1, 2, "a")])
    y = []
    for _ in range(3000):
        x = md.positions()
        a, b = x[0] - x[1], x[2] - x[1]
        y.append(math.acos(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))) - th0)
        md.step()
    keff = k if form == "theta" else k * math.sin(th0) ** 2
    w2 = 2 * keff / (m * r0 * r0)
    if form == "theta":
        assert HarmonicAngle(k, th0).omega2_fixed_centre(m, r0) == w2
    assert abs(_omega2(y, dt) / w2 - 1) < 1e-4
    assert abs(_omega2(y, dt) / (keff / (m * r0 * r0)) - 1) > 0.5
    assert np.all(md.velocities()[1] == 0.0)                  # the frozen atom does not move


def test_coulomb_pair_closed_form_and_exclusions():
    """Two point charges +-1 at r = 2 in a walled box: U = q1 q2 / r = -1/2, attraction 1/r^2 = 1/4 (d = 2 and 3:
    charges are 3-D in both). Bonded atoms (1-2) feel no Coulomb force with exclude="bonded" (only the bond's), and do
    with exclude="none". A periodic axis with charges is refused."""
    for dim in (2, 3):
        md = MD(dim=dim, box=[10.0] * dim, boundary="walls", pair=None)
        md.add_species("P", charge=1.0)
        md.add_species("N", charge=-1.0)
        md.add("P", np.full(dim, 4.0))
        md.add("N", np.r_[6.0, np.full(dim - 1, 4.0)])
        assert md.potential_energy()["coulomb"] == pytest.approx(-0.5, rel=1e-15)
        F = md.forces()
        assert F[0, 0] == pytest.approx(0.25, rel=1e-15) and F[1, 0] == pytest.approx(-0.25, rel=1e-15)
        assert md.pressure()["interaction"] * md.volume() == pytest.approx(-0.5 / dim, rel=1e-14)  # r.F = -q1q2/r
    md = MD(dim=3, box=[10.0] * 3, boundary="walls", pair=None, exclude="bonded")
    md.add_species("P", charge=1.0)
    md.add_species("N", charge=-1.0)
    md.set_bond_type("b", HarmonicBond(10.0, 2.0))
    md.add_molecule(["P", "N"], [[4, 4, 4], [6, 4, 4]], bonds=[(0, 1, "b")])
    assert md.potential_energy()["coulomb"] == 0.0 and np.all(md.forces() == 0.0)
    md.set_exclusions("none")
    assert md.potential_energy()["coulomb"] == pytest.approx(-0.5, rel=1e-15)
    p = MD(dim=3, box=[10.0] * 3, boundary=["periodic", "walls", "walls"], pair=None)
    p.add_species("P", charge=1.0)
    with pytest.raises(ValueError, match="Ewald"):
        p.add("P", [5.0, 5.0, 5.0])
    assert p.n == 0
