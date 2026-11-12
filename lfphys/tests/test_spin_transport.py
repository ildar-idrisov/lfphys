# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Gyroscopes and spins in special relativity (lfphys.core.spin_transport, plan P9) against closed forms and second
routes:

* the generators against core.lorentz; the 2 x 2 exponential against scipy's;
* a burn against hyperbolic motion; a manoeuvre with turns against a direct integration of dM/dtau = M Xi(tau) and
  against Thomas's precession rate (Jackson 11.119) integrated in lab time;
* the holonomy of loops in a plane against Gauss-Bonnet (triangles, regular polygons, circles; Thomas's 2 pi (gamma - 1)
  per revolution), in any plane; SU(2) against SO(3); the spinor's sign after turns by 2 pi;
* the isoperimetric inequality of the hyperbolic plane for planar loops;
* a charge in uniform fields (cyclotron motion, hyperbolic motion in E) and its spin by BMT: frozen spin at g = 2,
  omega_a = -a (q/m) B, the magic momentum, the covariant equation against the Thomas-BMT rate.

Tolerances: the pieces are products of exponentials with entries up to cosh(eta) (eta <= 3 here), so the round-off
grows like eps cosh(eta)^2 per piece: 1e-11 bounds it with margin (measured <= 1e-12 at rho = 2); integrations at
rtol 1e-12 are compared at 1e-9."""

import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from lfphys.core import lorentz as L
from lfphys.core import spin_transport as T

RNG = np.random.default_rng(271027)


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def test_generators():
    for _ in range(20):
        n, s = _unit(RNG.normal(size=3)), RNG.uniform(0.0, 3.0)
        assert np.max(np.abs(expm(s * T.gen_boost(n)) - L.boost(-math.tanh(s) * n))) < 1e-12
        assert np.max(np.abs(expm(s * T.gen_rot(n)) - L.rotation(n, s))) < 1e-14
        assert np.max(np.abs(L.lorentz_of_sl2(T.expm2(s * T.sl2_gen_boost(n))) - expm(s * T.gen_boost(n)))) < 1e-12
        assert np.max(np.abs(L.lorentz_of_sl2(T.expm2(s * T.sl2_gen_rot(n))) - expm(s * T.gen_rot(n)))) < 1e-14
        X = RNG.normal(size=(2, 2)) + 1j * RNG.normal(size=(2, 2))
        X -= 0.5 * np.trace(X) * np.eye(2)
        for scale in (1.0, 1e-4, 1e-8):
            assert np.max(np.abs(T.expm2(scale * X) - expm(scale * X))) < 1e-13


def test_burn_is_hyperbolic_motion():
    for c, a, eta in ((1.0, 1.0, 0.5), (2.0, 3.0, 2.0), (299792458.0, 9.80665, 1.2)):
        n = _unit([0.3, -0.5, 0.8])
        e = T.Manoeuvre([T.Burn(tuple(n), eta)], c=c, accel=a).end()
        L0 = c * c / a
        assert e.x[0] == pytest.approx(L0 * math.sinh(eta), rel=1e-13)
        assert np.allclose(e.x[1:], L0 * (math.cosh(eta) - 1) * n, rtol=1e-13, atol=1e-13 * L0)
        assert e.tau == pytest.approx(c * eta / a, rel=1e-15)
        beta = e.M[1:, 0] / e.M[0, 0]
        assert np.allclose(beta, math.tanh(eta) * n, atol=1e-15)
        assert T.holonomy(e)["angle"] < 1e-14  # a radial burn turns nothing


def _helix():
    return [T.Burn((1.0, 0.0, 0.0), 0.4), T.Turn((0.0, 1.0, 0.0), (0.3, 0.0, 1.0), 1.7, 2.5),
            T.Turn((0.0, 0.0, 1.0), (1.0, 1.0, 0.0), 0.6, 1.2), T.Burn((0.2, -1.0, 0.5), 0.8)]


def test_turns_against_a_direct_integration():
    """dM/dtau = M Xi(tau), Xi = K.a(tau) with the thrust direction turning in the comoving frame, integrated directly
    (DOP853, rtol 1e-13) against the exact pieces (exponentials in the turning frame)."""
    pieces = _helix()
    mv = T.Manoeuvre(pieces)
    M = np.eye(4)
    for p in pieces:
        n = _unit(p.direction)
        if isinstance(p, T.Turn):
            w, k = _unit(p.axis), p.curvature

            def rhs(s, y, n=n, w=w, k=k):
                a = L.rot3(w, k * s) @ n
                return (y.reshape(4, 4) @ T.gen_boost(a)).ravel()
        else:
            def rhs(s, y, n=n):
                return (y.reshape(4, 4) @ T.gen_boost(n)).ravel()
        sol = solve_ivp(rhs, (0, p.rapidity), M.ravel(), method="DOP853", rtol=1e-13, atol=1e-14)
        M = sol.y[:, -1].reshape(4, 4)
    e = mv.end()
    assert np.max(np.abs(M - e.M)) < 1e-9
    assert L.lorentz_defect(e.M) < 1e-12
    assert np.max(np.abs(L.lorentz_of_sl2(e.A) - e.M)) < 1e-11


def test_thomas_rate_route():
    """The gyroscopes' orientation relative to the pure-boost frame obeys dO/dt = [omega_T]x O with Jackson's
    omega_T = gamma^2/(gamma + 1) (a x v)/c^2 (lab time). Integrated piece by piece in the fuel s (dt/ds = U^0 / c for
    c = a = 1), with v and a = dv/dt taken from the exact state at each s, it reproduces the transported orientation."""
    mv = T.Manoeuvre(_helix(), c=1.0, accel=1.0)
    st = mv.start()
    O = np.eye(3)
    for p in mv.pieces:
        n = _unit(p.direction)

        def rhs(s, y, p=p, st=st, n=n):
            q = T._advance(st, p, s, 1.0, 1.0)
            a_dir = L.rot3(_unit(p.axis), p.curvature * s) @ n if isinstance(p, T.Turn) else n
            U = q.M[:, 0]
            dU = q.M @ T.gen_boost(a_dir)[:, 0]
            v = U[1:] / U[0]
            acc = (dU[1:] - v * dU[0]) / U[0] ** 2  # dv/dt
            w = T.thomas_rate(v, acc)
            return (U[0] * np.cross(w, y.reshape(3, 3).T).T).ravel()

        sol = solve_ivp(rhs, (0.0, p.rapidity), O.ravel(), method="DOP853", rtol=1e-12, atol=1e-13)
        O = sol.y[:, -1].reshape(3, 3)
        st = T._advance(st, p, p.rapidity, 1.0, 1.0)
    assert np.max(np.abs(O - mv.run(ds=0.1).O[-1])) < 1e-9


def _thomas_circle(rho, m=1):
    p = [T.Burn((1.0, 0.0, 0.0), rho), T.Turn((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), 1 / math.tanh(rho),
                                               m * 2 * math.pi * math.sinh(rho))]
    p.append(T.return_burn(T.Manoeuvre(p).end()))
    return T.Manoeuvre(p)


@pytest.mark.parametrize("rho", [0.05, 0.3, 1.0, 2.0])
def test_thomas_precession_per_revolution(rho):
    """Uniform circular motion at gamma = cosh(rho): the gyroscopes turn by 2 pi (gamma - 1) per revolution against the
    sense of the motion (Thomas; Jackson 11.120), the area of the velocity disc (Gauss-Bonnet)."""
    h = T.holonomy(_thomas_circle(rho).end())
    A = 2 * math.pi * (math.cosh(rho) - 1)
    assert h["closed"]
    assert np.max(np.abs(h["R"] - L.rot3([0, 0, 1], -A))) < 1e-11
    assert A == pytest.approx(float(T.circle_area(rho)), rel=1e-14)
    assert h["su2_angle"] == pytest.approx(A % (4 * math.pi) if A % (4 * math.pi) <= 2 * math.pi
                                           else 4 * math.pi - A % (4 * math.pi), abs=1e-10)


def test_circle_through_rest_and_the_double_cover():
    """A circle of velocity space through rest, run m times: the holonomy is m times its area, SO(3) keeps it mod
    2 pi, SU(2) mod 4 pi (the spinor changes sign at every 2 pi); one circle meets the isoperimetric bound with
    equality."""
    rho = 0.8
    A1 = float(T.circle_area(rho))
    for m in (1, 2, 3, 4):
        h = T.holonomy(T.Manoeuvre([T.Turn((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1 / math.tanh(rho),
                                           m * float(T.circle_length(rho)))]).end())
        assert h["closed"]
        assert np.max(np.abs(h["R"] - L.rot3([0, 0, 1], -m * A1))) < 1e-11
        assert np.max(np.abs(h["su2"] - L.sl2_rotation([0, 0, 1], -m * A1))) < 1e-11
    assert float(T.isoperimetric_bound(T.circle_length(rho))) == pytest.approx(A1, rel=1e-14)


def _regular_polygon_through_rest(n, rc, plane=np.eye(3)):
    cvel = math.tanh(rc) * plane[0]
    verts = []
    for k in range(n):
        ang = 2 * math.pi * k / n
        d = -math.cos(ang) * plane[0] - math.sin(ang) * plane[1]
        verts.append(L.add_velocities(cvel, math.tanh(rc) * d))
    return np.array(verts)


@pytest.mark.parametrize("n", [3, 4, 5, 9, 60])
def test_polygon_holonomy_is_its_area(n):
    """A regular geodesic n-gon through rest, flown by burns: the holonomy equals the area by the closed form for
    regular polygons and by Gauss-Bonnet from the interior angles; it tends to the circle's area; in any plane the axis
    is that plane's normal."""
    rc = 0.9
    Rm = L.rot3([0.4, -1.0, 0.7], 1.1)
    for plane in (np.eye(3), Rm.T):
        verts = _regular_polygon_through_rest(n, rc, plane)
        h = T.holonomy(T.Manoeuvre(T.polygon_burns(verts[1:])).end())
        ref = T.regular_polygon_area(n, rc)
        assert h["closed"]
        assert h["angle"] == pytest.approx(ref, abs=1e-12)
        assert T.polygon_area(verts) == pytest.approx(ref, abs=1e-12)
        nrm = np.cross(plane[0], plane[1])
        assert abs(abs(h["axis"] @ nrm) - 1) < 1e-10
        assert ref < float(T.circle_area(rc))


def test_triangles_three_routes_and_isoperimetry():
    """Random triangles rest -> u -> w -> rest: holonomy (transport) = Wigner angle of the two boosts = L'Huilier's area
    from the sides = Gauss-Bonnet from the angles; every planar loop stays below the isoperimetric bound."""
    for _ in range(200):
        u = _unit(RNG.normal(size=3)) * RNG.uniform(0.05, 0.95)
        w = _unit(RNG.normal(size=3)) * RNG.uniform(0.05, 0.95)
        h = T.holonomy(T.Manoeuvre(T.polygon_burns([u, w])).end())
        z = np.zeros(3)
        a, b, c = float(T.distance(z, u)), float(T.distance(u, w)), float(T.distance(w, z))
        area = float(T.triangle_area(a, b, c))
        _, _, _, th = L.wigner_rotation(u, L.relative_velocity(u, w))
        assert h["angle"] == pytest.approx(area, abs=1e-11)
        assert float(th) == pytest.approx(area, abs=1e-11)
        assert T.polygon_area([z, u, w]) == pytest.approx(area, abs=1e-11)
        assert area < float(T.isoperimetric_bound(a + b + c))


def test_nonplanar_loops_two_representations():
    """Loops that leave every plane: the craft returns to rest; the Lorentz route and the SL(2, C) route give the same
    rotation; the rotation axis is not perpendicular to the loop's first plane."""
    p = _helix()
    p.append(T.return_burn(T.Manoeuvre(p).end()))
    e = T.Manoeuvre(p).end()
    h = T.holonomy(e)
    assert h["closed"] and h["unitarity"] < 1e-11
    assert np.max(np.abs(L.lorentz_of_sl2(h["su2"])[1:, 1:] - h["R"])) < 1e-11
    assert np.max(np.abs(L.rot3(h["su2_axis"], h["su2_angle"]) - h["R"])) < 1e-11
    assert abs(h["axis"][2]) < 1 - 1e-3
    # a crown (skew polygon) through rest
    verts = [L.add_velocities([0.5, 0, 0], 0.5 * np.array([math.cos(t), math.sin(t), 0.3 * (-1) ** k]))
             for k, t in enumerate(np.linspace(0, 2 * math.pi, 7)[1:-1])]
    h = T.holonomy(T.Manoeuvre(T.polygon_burns(verts)).end())
    assert h["closed"] and h["angle"] > 0


def test_charge_in_uniform_fields():
    """Cyclotron motion in B: angular frequency |q B|/(gamma m) in lab time, radius gamma m v/|q B|; uniform E from
    rest: hyperbolic motion with proper acceleration q E/m."""
    qm, Bz, b = -1.3, 2.0, 0.8
    g = 1 / math.sqrt(1 - b * b)
    taus = np.linspace(0, 4.0, 9)
    U, x = T.charge_motion(qm, [0, 0, 0], [0, 0, Bz], L.four_velocity([b, 0, 0]), taus)
    w = abs(qm * Bz) / g
    t = x[:, 0]
    assert np.allclose(t, g * taus, rtol=1e-14)
    ang = np.unwrap(np.arctan2(U[:, 2], U[:, 1]))
    assert np.allclose(ang, -np.sign(qm * Bz) * w * t, atol=1e-12)
    R = g * b / abs(qm * Bz)  # the velocity turns anticlockwise (q B < 0): the centre is on the +y side
    r = np.linalg.norm(x[:, 1:3] - x[:1, 1:3] - np.array([0, R]), axis=1)
    assert np.allclose(r, R, rtol=1e-12)
    U, x = T.charge_motion(0.5, [0, 0, 3.0], [0, 0, 0], [1, 0, 0, 0], taus)
    a = 1.5
    assert np.allclose(x[:, 3], (np.cosh(a * taus) - 1) / a, rtol=1e-12, atol=1e-14)
    assert np.allclose(x[:, 0], np.sinh(a * taus) / a, rtol=1e-12, atol=1e-14)


def _spin_from_rest(U, s):
    b = U[1:] / U[0]
    g = U[0]
    return np.r_[g * (b @ s), s + (g * g / (g + 1)) * (b @ s) * b]


@pytest.mark.parametrize("g_factor", [2.0, 2.00232, 2.2, 1.0, 0.0])
def test_bmt_in_a_magnetic_field(g_factor):
    """v perpendicular to B: the rest-frame spin turns relative to the velocity at omega_a = -a (q/m) B in lab time,
    a = (g - 2)/2 (frozen at g = 2): the principle of the muon g - 2 experiments; S.U = 0 and |s| = 1 kept."""
    qm, Bz, b = -1.0, 2.0, 0.8
    g = 1 / math.sqrt(1 - b * b)
    U0 = L.four_velocity([b, 0, 0])
    taus = np.linspace(0, 3.0, 61)
    U, S = T.bmt(qm, g_factor, [0, 0, 0], [0, 0, Bz], U0, _spin_from_rest(U0, np.array([1.0, 0, 0])), taus)
    s = T.rest_spin(U, S)
    dphi = np.unwrap(np.arctan2(s[:, 1], s[:, 0])) - np.unwrap(np.arctan2(U[:, 2], U[:, 1]))
    a = 0.5 * g_factor - 1
    assert np.max(np.abs(dphi - (-a * qm * Bz) * g * taus)) < 1e-9
    assert np.max(np.abs(L.mdot(S, U))) < 1e-9
    assert np.max(np.abs(np.linalg.norm(s, axis=1) - 1)) < 1e-9


@pytest.mark.parametrize("g_factor,field", [(2.0, "E"), (2.6, "E"), (2.3, "E"), (2.6, "B"), (0.0, "B")])
def test_bmt_longitudinal_polarisation_rate(g_factor, field):
    """The rate of the longitudinal polarisation (Jackson 11.171, SI):
    d(bhat.s)/dt = -(q/m) s_perp.[ (g/2 - 1) bhat x B + (g beta/2 - 1/beta) E/c ], measured at tau = 0 from the BMT
    solution (Richardson difference). For E alone it vanishes at beta^2 = 2/g, i.e. a = 1/(gamma^2 - 1) (g = 2.6 at
    gamma^2 = 1 + 1/0.3 here): the magic momentum of storage rings; the other cases at beta = 0.6 (review B2-9: g = 2.3
    in E at a general momentum instead of a duplicate of the magic case)."""
    qm = 0.7
    a = 0.5 * g_factor - 1
    b = math.sqrt(1 - a / (1 + a)) if (g_factor, field) == (2.6, "E") else 0.6
    E, B = ([0, 0.8, 0], [0, 0, 0]) if field == "E" else ([0, 0, 0], [0.3, 0.2, 1.1])
    U0 = L.four_velocity([b, 0, 0])
    s0 = _unit([0.3, 0.8, -0.5])
    h = 1e-4
    U, S = T.bmt(qm, g_factor, E, B, U0, _spin_from_rest(U0, s0), [0.0, h, 2 * h], rtol=3e-14)
    s = T.rest_spin(U, S)
    lon = np.array([(U[i, 1:] / np.linalg.norm(U[i, 1:])) @ s[i] for i in range(3)])
    g = U0[0]
    rate = (4 * lon[1] - lon[2] - 3 * lon[0]) / (2 * h) / g  # per lab time
    bh = np.array([1.0, 0, 0])
    sp = s0 - (s0 @ bh) * bh
    ref = -qm * sp @ ((g_factor / 2 - 1) * np.cross(bh, B) + (g_factor * b / 2 - 1 / b) * np.asarray(E, float))
    assert rate == pytest.approx(ref, abs=1e-6 * max(1.0, abs(ref)))
    if (g_factor, field) == (2.6, "E"):
        assert abs(ref) < 1e-12  # the magic momentum: the spin follows the velocity


def test_bmt_covariant_against_thomas_bmt():
    """General fields: the covariant BMT spin against the Thomas-BMT precession of the rest-frame spin, ds/dtau =
    gamma Omega x s, integrated in proper time with the exact velocity (two independent formulas)."""
    E, B, gf, qm = np.array([0.3, -0.2, 0.5]), np.array([0.4, 1.1, -0.7]), 2.4, 0.7
    U0 = L.four_velocity([0.5, 0.3, -0.4])
    s0 = _unit([0.2, 0.9, -0.3])
    taus = np.linspace(0, 2.0, 41)
    U, S = T.bmt(qm, gf, E, B, U0, _spin_from_rest(U0, s0), taus)
    s_cov = T.rest_spin(U, S)

    def rhs(tau, y):
        Uu = T.charge_motion(qm, E, B, U0, [tau])[0][0]
        return Uu[0] * np.cross(T.thomas_bmt_rate(qm, gf, E, B, Uu[1:] / Uu[0]), y)

    sol = solve_ivp(rhs, (0, taus[-1]), s0, t_eval=taus, method="DOP853", rtol=1e-12, atol=1e-14)
    assert np.max(np.abs(sol.y.T - s_cov)) < 1e-9
