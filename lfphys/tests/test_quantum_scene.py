# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.quantum.scene (plan P15.3): the quantum playground's scene against closed forms and second methods.

Tolerances are derived from the error of each route (stated per test); negative controls show that each check fails
when the physics it guards is broken.
"""

from __future__ import annotations

import functools
import math

import numpy as np
import pytest
from scipy import constants as sc
from scipy import integrate, special

from lfphys.core import backend
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S
from lfphys.core.quantum import transfer

EPS = np.finfo(float).eps


def _gauss_blur_interval(x, lo, hi, w):
    """The Gaussian blur of 1_[lo, hi] at x by quadrature (an independent route): int_lo^hi G(x - y) dy with
    G = N(0, eps^2/2), eps = w / (2 erfinv 0.8)."""
    e = w / (2 * special.erfinv(0.8))
    s = e / math.sqrt(2)
    f = lambda y: math.exp(-0.5 * ((x - y) / s) ** 2) / (s * math.sqrt(2 * math.pi))  # noqa: E731
    a, b = max(lo, x - 40 * s), min(hi, x + 40 * s)
    if b <= a:
        return 0.0
    return integrate.quad(f, a, b, epsabs=1e-15, epsrel=1e-13, limit=200)[0]


# --- shapes -----------------------------------------------------------------------------------------------------------
def test_edge_profile_and_its_width():
    """S(u) = (1 + erf(u/eps))/2 rises from 0.1 to 0.9 over exactly w (erfinv(0.8) by definition); a smooth interval is
    the Gaussian blur of the sharp one (quadrature, |error| <= 1e-13); its tails keep relative accuracy (the erfc form:
    no cancellation, 1e-30 is resolved)."""
    w = 0.37
    u10 = -w / 2
    assert abs(Q.smooth_step(u10, w) - 0.1) < 4 * EPS and abs(Q.smooth_step(-u10, w) - 0.9) < 4 * EPS
    for x in (-3.0, -1.02, -0.9, 0.0, 0.33, 1.0, 1.4, 4.0):
        assert abs(Q.smooth_interval(x, -1.0, 1.2, w) - _gauss_blur_interval(x, -1.0, 1.2, w)) < 1e-13
    far = float(Q.smooth_interval(4.0, -1.0, 1.2, w))
    e = Q.edge_eps(w)
    ref = 0.5 * (special.erfc((4.0 - 1.2) / e) - special.erfc((4.0 + 1.0) / e))
    assert 0 < far and abs(far - ref) <= 1e-14 * ref
    # the ramp integral J is the antiderivative of S (trapezoid on a fine grid: error h^2/12 max|S'| L)
    u = np.linspace(-3, 3, 600001)
    J = integrate.cumulative_trapezoid(Q.smooth_step(u, w), u, initial=0.0) + float(Q.ramp_integral(-3.0, w))
    assert np.max(np.abs(J - Q.ramp_integral(u, w))) < (6 / 600000) ** 2 / 12 * 2 / (e * math.sqrt(math.pi)) * 6


def test_shapes_against_closed_forms_on_any_grid():
    """Every shape is a closed form of physical parameters: the same values at the same points on grids of different
    steps (to round-off), and the documented formula: box = product of blurred intervals (quadrature), ball = radial
    step, wall = blur(slab) (1 - sum blur(holes)) (quadrature of each factor), trap = m omega^2 r^2 / 2."""
    box = Q.Box([0.5, -0.25], [2.0, 1.5], 3.0, 0.6)
    ball = Q.Ball([0.3, 0.1], 1.1, -2.0, 0.6)
    wall = Q.SlitWall(1, 0.4, 0.8, 5.0, [[-1.5, 1.0], [1.5, 1.0]], 0.6)
    trap = Q.HarmonicTrap([0.2, -0.1], [1.3, 0.7], mass=2.0)
    g1 = S.Grid((80, 80), 0.1)
    g2 = S.Grid((40, 40), 0.2)
    for sh in (box, ball, wall, trap):
        v1, v2 = sh.V(g1), sh.V(g2)
        assert np.max(np.abs(v1[::2, ::2] - v2)) <= 8 * EPS * np.max(np.abs(v1))
    P = [(0.1, 0.2), (1.45, -0.9), (-0.6, 0.55), (2.9, 1.7)]
    gp = S.Grid((1, 1), 1.0)
    for x, y in P:
        g = S.Grid((1, 1), 1.0, center=(x, y))
        vb = box.V(g)[0, 0]
        ref = 3.0 * _gauss_blur_interval(x, -0.5, 1.5, 0.6) * _gauss_blur_interval(y, -1.0, 0.5, 0.6)
        assert abs(vb - ref) < 1e-12
        r = math.hypot(x - 0.3, y - 0.1)
        assert abs(ball.V(g)[0, 0] - (-2.0) * 0.5 * special.erfc((r - 1.1) / Q.edge_eps(0.6))) < 1e-14
        slab = _gauss_blur_interval(y, 0.0, 0.8, 0.6)
        holes = _gauss_blur_interval(x, -2.0, -1.0, 0.6) + _gauss_blur_interval(x, 1.0, 2.0, 0.6)
        assert abs(wall.V(g)[0, 0] - 5.0 * slab * (1 - holes)) < 1e-12
        assert abs(trap.V(g)[0, 0] - 0.5 * 2.0 * (1.3**2 * (x - 0.2) ** 2 + 0.7**2 * (y + 0.1) ** 2)) < 1e-13
    del gp
    # 3-D: a wall normal to z with slits along x of length 2 along y
    wall3 = Q.SlitWall(2, 0.0, 0.8, 5.0, [[-1.0, 1.0], [1.0, 0.8]], 0.6, along=0, length=[0.5, 2.0])
    for x, y, z in ((0.1, 0.2, 0.1), (-1.2, 1.6, -0.3), (1.0, -0.4, 0.5)):
        g = S.Grid((1, 1, 1), 1.0, center=(x, y, z))
        ly = _gauss_blur_interval(y, -0.5, 1.5, 0.6)
        holes = (_gauss_blur_interval(x, -1.5, -0.5, 0.6) + _gauss_blur_interval(x, 0.6, 1.4, 0.6)) * ly
        assert abs(wall3.V(g)[0, 0, 0] - 5.0 * _gauss_blur_interval(z, -0.4, 0.4, 0.6) * (1 - holes)) < 1e-12


def test_charge_coupled_shapes_act_through_q():
    """A shape with coupling "charge" is an electrostatic potential phi (energy per elementary charge): V = q phi for each
    species (an electron sees -phi, a neutron nothing), next to the energy shapes that every species sees."""
    s = Q.Scene((96, 96), 0.25, dt=0.01)
    s.add(Q.Box([0, 0], [2.0, 2.0], 1.5, 0.8, coupling="charge"))
    s.add(Q.Step(0, 3.0, 0.7, 0.8))
    el, nn = Q.species("electron"), Q.species("neutron")
    pe = s.add_particle(Q.Packet(el, [-3.0, 0.0], [1.0, 0.0], [1.0, 1.0]))
    pn = s.add_particle(Q.Packet(nn, [-3.0, 0.0], [1.0, 0.0], [1.0, 1.0]))
    g = s.grid
    phi = Q.Box([0, 0], [2.0, 2.0], 1.5, 0.8).V(g)
    step = Q.Step(0, 3.0, 0.7, 0.8).V(g)
    Ve = s.hamiltonian(s._key(s.particles[pe])).V
    Vn = s.hamiltonian(s._key(s.particles[pn])).V
    assert np.max(np.abs(Ve - (step - phi))) < 1e-15 and np.max(np.abs(Vn - step)) < 1e-15
    assert np.array_equal(s.potential(el), step - phi) and np.array_equal(s.potential(), step)


def test_unresolvable_edges_are_refused_and_why(ru):
    """An edge narrower than edge_min(d) = 3.03 d is refused with its reason. The reason: the band-limited interpolant
    of the sampled potential (the grid's own picture of it) misses the continuous one by the aliased tail of the edge's
    spectrum, at most E1(k_N^2 eps^2/4)/pi per unit step (|S^(k)| = exp(-k^2 eps^2/4)/|k|, tails beyond k_N = pi/d on
    both sides): 4.0e-5 at the minimum edge, 0.024 at half of it (measured on a 1-D box)."""
    d = 0.1
    sc_ = Q.Scene((64, 64), d, dt=0.01)
    wmin = Q.edge_min(d)
    assert abs(wmin / d - Q.EDGE_STEPS) < 1e-12 and 3.03 < Q.EDGE_STEPS < 3.04
    with pytest.raises(ValueError, match="box: the edge .* is narrower than a grid") as e:
        sc_.add(Q.Box([0, 0], [1, 1], 1.0, 0.99 * wmin))
    assert ru(e.value.args[0]).startswith("ящик: край ") and "сделайте край шире или сетку мельче" in ru(e.value.args[0])
    with pytest.raises(ValueError, match="edge"):
        sc_.add(Q.SlitWall(0, 0.0, 0.5, 1.0, [[0, 1]], 0.5 * wmin))
    sc_.add(Q.Box([0, 0], [1, 1], 1.0, wmin))

    def interp_error(w):
        g = S.Grid((256,), d)
        V = Q.Box([0.0], [3.0], 1.0, w).V(g)
        F = np.fft.fft(V)
        xs = g.axes[0][:-1] + 0.5 * d  # half-way between samples
        k = g.k[0]
        Vi = np.real(np.exp(1j * np.outer(xs - g.axes[0][0], k)) @ F) / len(V)  # sample j sits at x_0 + j d
        gx = S.Grid((len(xs),), d, center=(xs[len(xs) // 2],))
        assert np.allclose(gx.axes[0], xs)
        return float(np.max(np.abs(Vi - Q.Box([0.0], [3.0], 1.0, w).V(gx))))

    def bound(w):
        u = (math.pi / d * Q.edge_eps(w)) ** 2 / 4
        return 2 * special.exp1(u) / math.pi  # two edges
    e1, e2 = interp_error(wmin), interp_error(0.5 * wmin)
    assert e1 <= bound(wmin), (e1, bound(wmin))
    assert e2 > 10 * bound(wmin), (e2, bound(wmin))


def test_landau_gauge_of_a_confined_field():
    """A uniform field B in a rectangle (2-D, along z): curl A = B f_x f_y (central differences of the closed form,
    error h^2 |A'''|/6 ~ 1e-8 at h = 1e-4); A vanishes left of, below and above the region and is the pure gauge
    B W g(y) in the strip to its right (string +1) or left (string -1); the flux through the region is B W H."""
    fld = Q.MagneticField([0, 0, 0.8], lo=[-1.0, -0.5], hi=[1.5, 1.0], edge=0.5)
    A = fld.vector_potential(2)
    h = 1e-5
    rng = np.random.default_rng(3)
    for x, y in rng.uniform(-3, 3, (40, 2)):
        dAy = (A.fn(1, np.array(x + h), np.array(y)) - A.fn(1, np.array(x - h), np.array(y))) / (2 * h)
        dAx = (A.fn(0, np.array(x), np.array(y + h)) - A.fn(0, np.array(x), np.array(y - h))) / (2 * h)
        Bz = 0.8 * Q.smooth_interval(x, -1.0, 1.5, 0.5) * Q.smooth_interval(y, -0.5, 1.0, 0.5)
        assert abs(dAy - dAx - Bz) < 1e-8, (x, y)
    e = Q.edge_eps(0.5)
    assert abs(A.fn(1, np.array(-1.0 - 8 * e), np.array(0.2))) < 1e-15
    assert abs(A.fn(1, np.array(0.2), np.array(1.0 + 8 * e))) < 1e-14
    far = float(A.fn(1, np.array(1.5 + 8 * e), np.array(0.2)))
    assert abs(far - 0.8 * 2.5 * Q.smooth_interval(0.2, -0.5, 1.0, 0.5)) < 1e-13
    left = Q.MagneticField([0, 0, 0.8], lo=[-1.0, -0.5], hi=[1.5, 1.0], edge=0.5, string=-1).vector_potential(2)
    assert abs(left.fn(1, np.array(1.5 + 8 * e), np.array(0.2))) < 1e-13
    # charged particles are refused next to fields whose orbital coupling is not built
    sc_ = Q.Scene((64, 64), 0.25, dt=0.01, edges=Q.EdgeLayers(2.0, 3.0))
    sc_.add_particle(Q.Packet(Q.species("electron"), [0, 0], [1, 0], [1, 1]))
    with pytest.raises(ValueError, match="charged particle"):
        sc_.add(Q.MagneticField([0.3, 0, 0]))
    with pytest.raises(ValueError, match="gradient"):
        sc_.add(Q.MagneticField([0, 0, 1.0], gradient=[[0, 0, 0], [0, 0, 1.0], [0, 1.0, 0]]))
    with pytest.raises(ValueError, match="not symmetric"):
        Q.Scene((16, 16), 0.25).add(Q.MagneticField([0, 0, 1.0], gradient=[[0, 0, 0], [0, 0, 1.0], [0, 0, 0]]))
    # 3-D: a field along x confined in x has div B != 0: refused for a charge; a prism (unbounded along x) is built,
    # A_z = B g(y) F(z)... here (a, b) = (1, 2): A_2 = B g(x_2) F(x_1), curl_x A = d_1 A_2 - d_2 A_1 = B f(x_1) g(x_2)
    assert "div B" in str(Q.MagneticField([0.5, 0, 0], lo=[-1, -1, -1], hi=[1, 1, 1], edge=0.5).orbital_reason(3))
    A3 = Q.MagneticField([0.5, 0, 0], lo=[None, -1, -1], hi=[None, 1, 1], edge=0.5).vector_potential(3)
    for x0, y, z in ((0.3, 0.2, -0.4), (2.0, 1.1, 0.9)):
        a = [np.array(x0), np.array(y), np.array(z)]
        d1 = (A3.fn(2, a[0], a[1] + h, a[2]) - A3.fn(2, a[0], a[1] - h, a[2])) / (2 * h)
        d2 = (A3.fn(1, a[0], a[1], a[2] + h) - A3.fn(1, a[0], a[1], a[2] - h)) / (2 * h)
        assert abs(d1 - d2 - 0.5 * Q.smooth_interval(y, -1, 1, 0.5) * Q.smooth_interval(z, -1, 1, 0.5)) < 1e-8


# --- free motion ------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("shape,spacing,center,k,sigma,t", [
    ((160, 160), 0.15, (-2.0, 1.0), (3.0, -2.0), (1.0, 1.3), 1.2),
    ((64, 64, 64), 0.4, (-1.0, 0.0, 1.0), (1.5, 1.0, -1.0), (1.2, 1.5, 1.0), 1.0),
])
def test_free_packet_spreads_as_the_closed_form(shape, spacing, center, k, sigma, t):
    """A packet of the scene is the Gaussian of Grid.gaussian; free, it follows the exact closed form (the kinetic step is
    exact on the grid): the error is round-off (1e3 eps of the peak) plus the periodic images (the tail at the window's
    edge, computed and included)."""
    sc_ = Q.Scene(shape, spacing, dt=t / 40)
    sp = Q.species("atom", Q.Units(), mass_u=sc.m_e / sc.atomic_mass)  # mass 1 in units of m_e
    assert abs(sp.mass - 1.0) < 1e-12
    pid = sc_.add_particle(Q.Packet(sp, list(center), list(k), list(sigma)))
    g = sc_.grid
    assert np.max(np.abs(sc_.wave(pid) - g.gaussian(center, k, sigma))) < 1e-13
    sc_.advance(40)
    ref = g.free_gaussian(t, center, k, sigma)
    tail = 0.0
    for i in range(g.ndim):
        st = abs(sigma[i] ** 2 + 0.5j * t)
        gap = 0.5 * g.shape[i] * g.d[i] - abs(center[i] + k[i] * t)
        tail += math.exp(-gap**2 * sigma[i] ** 2 / (4 * st**2)) * (2 * math.pi * sigma[i] ** 2) ** -0.25
    err = float(np.max(np.abs(sc_.wave(pid) - ref)))
    assert err <= 1e3 * EPS * np.max(np.abs(ref)) + 10 * tail, (err, tail)
    # the width of |psi|^2 along axis 0: sigma sqrt(1 + (t / (2 m sigma^2))^2)
    rho = sc_.density(pid)
    x = np.broadcast_to(g.mesh()[0], g.shape)
    mx = float(np.sum(x * rho) / np.sum(rho))
    sx = math.sqrt(float(np.sum((x - mx) ** 2 * rho) / np.sum(rho)))
    assert abs(sx - sigma[0] * math.sqrt(1 + (t / (2 * sigma[0] ** 2)) ** 2)) < 1e-10


def test_packets_are_refused_when_the_grid_or_window_cannot_hold_them(ru):
    sc_ = Q.Scene((64, 64), 0.2, dt=0.01)
    sp = Q.species("electron")
    with pytest.raises(ValueError, match="the grid does not carry") as e:
        sc_.add_particle(Q.Packet(sp, [0, 0], [14.0, 0], [1.0, 1.0]))  # pi/d = 15.7 < 14 + 3
    assert "сетка не передаёт волну" in ru(e.value.args[0])
    with pytest.raises(ValueError, match="does not fit") as e:
        sc_.add_particle(Q.Packet(sp, [3.0, 0], [0, 0], [1.0, 1.0]))   # 3.4 from the edge < 7.4 sigma
    assert ru(e.value.args[0]).startswith("пакет не помещается в окно по оси x")


# --- absorbed probability ---------------------------------------------------------------------------------------------
def _absorbing_scene():
    sc_ = Q.Scene((128, 112), 0.2, dt=0.01, edges=Q.EdgeLayers(3.0, 6.0))
    d1 = sc_.add(Q.Detector([5.0, None], [None, None], 3.0, 0.8, name="screen"))
    d2 = sc_.add(Q.Detector([-2.0, 2.0], [0.0, None], 2.0, 0.8))
    sp = Q.species("electron")
    p1 = sc_.add_particle(Q.Packet(sp, [-2.0, 0.0], [5.0, 1.5], [1.0, 1.0]))
    p2 = sc_.add_particle(Q.Packet(Q.species("neutron", Q.Units(1e-9, sc.m_n)), [-1.0, -1.0], [3.0, -2.0], [1.0, 1.2]))
    return sc_, (d1, d2), (p1, p2)


def test_norm_plus_absorbed_is_one_and_detectors_share_it():
    """Per particle: norm + sum over detectors and edges of the absorbed probability = 1 to round-off (the split
    operator removes from psi exactly what it records, |psi|^2 (1 - exp(-W dt)) per half step; measured < 4 eps per step:
    the bound 32 eps per step), also across a live change of a detector (the record is banked with the old weights)."""
    sc_, (d1, d2), (p1, p2) = _absorbing_scene()
    sc_.advance(150)
    sc_.update(d2, strength=4.0, hi=[0.5, None])
    sc_.advance(150)
    ch = sc_.checks()
    for pid in (p1, p2):
        r = ch[pid]
        assert abs(r["balance"]) <= r["balance_tol"], r
        assert sum(r["absorbed"].values()) > 0.05
        assert set(r["absorbed"]) == {f"detector {d1}", f"detector {d2}", "edges"}


def test_each_detectors_share_against_its_absorption_rate():
    """The attribution W_k / W_total per point (review B6-Q15: the earlier negative control could not fail) against
    an independent route: dA_k/dt = 2 int W_k |psi|^2, integrated by the trapezoid over the steps. Two detectors that
    overlap each other and the right edge layer; the difference is the scheme's and the trapezoid's O(dt^2): measured
    1.85e-5 and 4.6e-6 for one detector at dt = 0.01, 0.005 (ratio 4.0), asserted 3 < ratio < 5 and below 1e-4 of the
    total. Negative control: attributing each point's loss to every detector whose W is non-zero there (W_k alone,
    without W_total) misses the route by 0.43 and 0.066."""
    out = []
    for dt in (0.01, 0.005):
        s = Q.Scene((128, 112), 0.2, dt=dt, edges=Q.EdgeLayers(3.0, 6.0))
        s.add(Q.Detector([5.0, None], [None, None], 3.0, 0.8))
        s.add(Q.Detector([2.0, -1.0], [7.0, None], 2.0, 0.8))
        pid = s.add_particle(Q.Packet(Q.species("electron"), [-2.0, 0.0], [5.0, 1.5], [1.0, 1.0]))
        g = s.grid
        Ws = dict(s._arr["W_parts"])
        rate = lambda: {k: 2 * float(np.sum(W * s.density(pid))) * g.dV for k, W in Ws.items()}  # noqa: E731
        I_, f0 = {k: 0.0 for k in Ws}, rate()
        for _ in range(int(round(3.0 / dt))):
            s.advance(1)
            f1 = rate()
            for k in I_:
                I_[k] += 0.5 * dt * (f0[k] + f1[k])
            f0 = f1
        A = s.absorbed(pid)
        acc = backend.to_numpy(s.particles[pid].acc) * g.dV
        wrong = {k: float(np.sum(acc * (W > 1e-12 * W.max()))) for k, W in Ws.items()}
        out.append(({k: A[k] - I_[k] for k in Ws}, {k: wrong[k] - I_[k] for k in Ws}))
    (e1, _), (e2, w2) = out
    for k in e1:
        if abs(e1[k]) > 1e-7:
            assert 3.0 < e1[k] / e2[k] < 5.0, (k, e1[k], e2[k])
        assert abs(e2[k]) < 1e-4
    assert max(abs(v) for v in w2.values()) > 1e3 * max(abs(v) for v in e2.values())


def test_detector_reflection_from_transfer_matrices_matches_a_run():
    """The reflection of a weak detector's face (transfer matrices of its profile, averaged over the packet's spectrum)
    against what a quasi-1-D run sends back (as schrodinger_nd's layer test: within 2 % of R)."""
    k0, sig, W0, w = 3.0, 4.0, 1.5, 0.5
    sc_ = Q.Scene((4096, 2), (0.05, 1.0), dt=0.005)
    sc_.add(Q.Detector([40.0, None], [None, None], W0, w))
    sp = Q.species("atom", mass_u=sc.m_e / sc.atomic_mass)
    pid = sc_.add_particle(Q.Packet(sp, [0.0, 0.0], [k0, 0.0], [sig, math.inf]))
    sc_.advance(int(round(25.0 / 0.005)))
    # at t = 25 the reflected packet is centred at 2 x 40 - 3 x 25 = 5 (width 5.1), the incident one deep in the detector
    x = sc_.grid.axes[0]
    back = float(np.sum(sc_.density(pid)[x < 30.0])) * sc_.grid.dV
    xg, wg = np.polynomial.hermite_e.hermegauss(60)
    R, T = sc_.objects[1].reflection(k0 + xg / (2 * sig), sp.mass, axis=0, slices=4000)
    ref = float(np.sum(wg * R) / np.sum(wg))
    assert ref > 1e-4 and float(np.max(T)) == 0.0
    assert abs(back - ref) < 0.02 * ref, (back, ref)


# --- spin -------------------------------------------------------------------------------------------------------------
def test_larmor_precession_of_a_neutron_is_exact():
    """A neutron (mu_n < 0) in a uniform B along x: H = -mu B sigma_x commutes with the rest, so <sigma_z> = cos(2 b t),
    <sigma_y> = -sin(2 b t), b = -mu B: the Larmor frequency 2|mu| B / hbar = gamma_n B (CODATA's gyromagnetic ratio,
    to its 1e-9 rounding); the split operator's 2 x 2 step is exact, so the error is round-off."""
    u = Q.Units(1e-9, sc.m_n)
    n = Q.species("neutron", u)
    gamma = sc.physical_constants["neutron gyromag. ratio"][0]
    assert abs(2 * abs(n.moment) * u.moment / sc.hbar - gamma) < 1e-8 * gamma
    # the electron's coupling -mu_e B is schrodinger_nd.pauli_coupling with CODATA's |g_e| (to CODATA's rounding)
    el = Q.species("electron")
    B3 = np.array([0.2, -0.1, 0.7])
    gp = S.pauli_coupling(B3, el.charge, el.mass, 1.0, abs(sc.physical_constants["electron g factor"][0]))
    assert np.max(np.abs(-el.moment * B3 - gp)) < 1e-9 * np.max(np.abs(gp))
    sc_ = Q.Scene((96, 96), 0.3, dt=0.02)
    B = 0.7
    sc_.add(Q.MagneticField([B, 0, 0]))
    pid = sc_.add_particle(Q.Packet(n, [0, 0], [1.0, 0], [1.5, 1.5]))
    assert sc_.particles[pid].kind == "spin"
    sc_.advance(50)
    b = -n.moment * B
    s = sc_.spin(pid)
    assert np.max(np.abs(s - [0.0, -math.sin(2 * b * 1.0), math.cos(2 * b * 1.0)])) < 1e-12, s


def test_spin_eigenstate_along_the_field_stays_scalar():
    """A spin that is an eigenstate of n.sigma for a field along one direction n factorizes exactly: the wave stays
    scalar with V - mu s B_n; the same run as a spinor (spin up along x, then projected) agrees to round-off."""
    u = Q.Units(1e-9, sc.m_n)
    n = Q.species("neutron", u)
    fld = Q.MagneticField([0, 0, 0.5], gradient=[[0, 0, 0], [0, 0, 0.3], [0, 0.3, 0]])
    a = Q.Scene((96, 96), 0.3, dt=0.02)
    a.add(fld)
    pa = a.add_particle(Q.Packet(n, [0, 0], [1.0, 0], [1.5, 1.5], spin=[1, 0]))
    assert a.particles[pa].kind == "scalar" and a.particles[pa].s == 1
    b = Q.Scene((96, 96), 0.3, dt=0.02)
    b.add(fld)
    pb = b.add_particle(Q.Packet(n, [0, 0], [1.0, 0], [1.5, 1.5], spin=[1, 1]))
    assert b.particles[pb].kind == "spin"
    a.advance(40)
    b.advance(40)
    up = b.wave(pb)[0] * math.sqrt(2)
    assert np.max(np.abs(up - a.wave(pa))) < 1e-12


def test_stern_gerlach_splitting_against_the_closed_form():
    """A neutral spin-1/2 particle in B = (0, 0, B0 + G y) (the field in the plane z = 0 of the vacuum field with
    dB_z/dy = dB_y/dz = G): spin up along z feels V = -mu (B0 + G y), so <y>_up = y0 + mu G t^2/(2m), <y>_down =
    y0 - mu G t^2/(2m), <x> = x0 + v t for both (Ehrenfest's theorem is exact for a linear potential); a spin along x
    splits into the two with weights 1/2. Error: round-off and the packet's tail at the window (< 1e-9)."""
    u = Q.Units(1e-9, sc.m_n)
    n = Q.species("neutron", u)
    G = 0.4
    sc_ = Q.Scene((128, 128), 0.25, dt=0.01)
    sc_.add(Q.MagneticField([0, 0, 2.0], gradient=[[0, 0, 0], [0, 0, G], [0, G, 0]]))
    pid = sc_.add_particle(Q.Packet(n, [-3.0, 0.0], [2.0, 0.0], [1.2, 1.2], spin=[1, 1]))
    sc_.advance(250)
    t = 2.5
    g = sc_.grid
    psi = sc_.wave(pid)
    for c, sgn in ((0, +1), (1, -1)):
        w = g.norm(psi[c])
        assert abs(w - 0.5) < 1e-12
        mx = g.mean_x(psi[c])
        assert abs(mx[1] - sgn * n.moment * G * t * t / (2 * n.mass)) < 1e-9, (c, mx)
        assert abs(mx[0] - (-3.0 + 2.0 * t / n.mass)) < 1e-9, (c, mx)


def test_cyclotron_orbit_and_electron_spin_in_a_uniform_field():
    """An electron in a uniform B along z (Landau gauge A_y = B (x - c), unbounded field): Ehrenfest's equations are
    exact, so <r> moves on the circle of radius v/omega_c and returns after T = 2 pi m / (|q| B); the split operator's
    alternating-direction kinetic step errs by O(dt^2) (measured: the return error falls 4x per halving of dt). Its
    spin (along x) precesses about z at 2 |mu_e| B: exactly, since a uniform b.sigma commutes with the rest."""
    el = Q.species("electron")
    B, k = 1.0, 1.5
    T = 2 * math.pi * el.mass / B
    errs = []
    for dt in (T / 400, T / 800):
        sc_ = Q.Scene((128, 128), 0.25, dt=dt, edges=Q.EdgeLayers(3.0, 4.0))
        sc_.add(Q.MagneticField([0, 0, B]))
        pid = sc_.add_particle(Q.Packet(el, [0.0, -1.5], [k, 0.0], [1.0, 1.0], spin=[1, 1]))
        assert sc_.particles[pid].kind == "spin"
        n = int(round(T / dt))
        sc_.advance(n // 4)
        g = sc_.grid
        mq = g.mean_x(sc_.wave(pid))
        # a quarter period: the electron (q < 0) turns counterclockwise for B along +z: from (0, -r) moving +x ...
        # the centre of the orbit is (0, -1.5 + r) with r = k / B (q = -1: omega = +B, counterclockwise)
        r = k / B
        assert abs(mq[0] - r) < 2e-3 and abs(mq[1] - (-1.5 + r)) < 2e-3, mq
        sc_.advance(n - n // 4)
        m1 = g.mean_x(sc_.wave(pid))
        errs.append(math.hypot(m1[0] - 0.0, m1[1] + 1.5))
        s = sc_.spin(pid)
        bz = -el.moment * B
        tt = n * dt
        assert np.max(np.abs(s - [math.cos(2 * bz * tt), math.sin(2 * bz * tt), 0.0])) < 1e-11, s
    assert 3.5 < errs[0] / errs[1] < 4.5 and errs[1] < 1e-3, errs


# --- measurement ------------------------------------------------------------------------------------------------------
def _measurement_errors(M=3000, seed=11):
    """(completeness error, worst post-measurement width error, KS distance of the outcomes, its DKW bound) of the
    Gaussian position measurement on a 2-D Gaussian packet (|psi|^2 spreads s0): the POVM's completeness
    int K_x(r)^2 d^2x = 1; the post-measurement spreads (1/s0^2 + 1/s^2)^(-1/2) and centre (x s0^2 + c s^2)/(s0^2 + s^2);
    the outcomes' marginal along x against N(c, s0^2 + s^2)."""
    sc_ = Q.Scene((96, 96), 0.2, dt=0.01)
    s0, s, c = 1.1, 0.6, (0.3, -0.2)
    pid = sc_.add_particle(Q.Packet(Q.species("electron"), list(c), [1.0, 0.5], [s0, s0]))
    psi0 = sc_.wave(pid)
    g = sc_.grid
    # completeness at a few points r, by the trapezoid over outcomes x on a grid of step 0.06 = s/10 (exponentially
    # accurate for the Gaussian K_x(r)^2: the error is far below 1e-9)
    xs = np.linspace(-6, 6, 201)
    comp = 0.0
    for r in ((0.0, 0.0), (1.0, -0.6)):
        sc_r = Q.Scene((1, 1), 1.0, center=r)
        vals = np.array([[sc_r.kraus((a, b), s)[0, 0] ** 2 for b in xs] for a in xs])
        comp = max(comp, abs(float(integrate.trapezoid(integrate.trapezoid(vals, xs), xs)) - 1.0))
    rng = np.random.default_rng(seed)
    out, werr = [], 0.0
    for i in range(M):
        sc_.set_wave(pid, psi0)
        res = sc_.measure(pid, s, rng)
        out.append(res["x"])
        if i < 5:
            rho = sc_.density(pid)
            X = g.mesh()
            for ax in range(2):
                xa = np.broadcast_to(X[ax], g.shape)
                m = float(np.sum(xa * rho) / np.sum(rho))
                sd = math.sqrt(float(np.sum((xa - m) ** 2 * rho) / np.sum(rho)))
                werr = max(werr, abs(sd - (1 / s0**2 + 1 / s**2) ** -0.5),
                           abs(m - (res["x"][ax] * s0**2 + c[ax] * s**2) / (s0**2 + s**2)))
    xo = np.sort(np.array(out)[:, 0])
    F = 0.5 * special.erfc(-(xo - c[0]) / math.sqrt(2 * (s0**2 + s**2)))
    ks = float(max(np.max(np.arange(1, M + 1) / M - F), np.max(F - np.arange(M) / M)))
    return comp, werr, ks, math.sqrt(math.log(2 / 1e-6) / (2 * M))


def test_position_measurement_probability_rule_and_post_state(monkeypatch):
    """The Gaussian POVM is complete (trapezoid over outcomes on a 0.06 grid: error < 1e-9); the outcomes follow
    p(x) = ||K_x psi||^2 = N(c, s0^2 + s^2) per axis (Kolmogorov-Smirnov distance within the DKW bound at
    alpha = 1e-6); the post-measurement state is the Gaussian of the closed form (grid quadrature: < 1e-9).
    Negative control: a Kraus operator with the wrong width (exp(-|r - x|^2 / (2 s^2)), not a POVM) fails both."""
    comp, werr, ks, dkw = _measurement_errors()
    assert comp < 1e-9 and werr < 1e-9 and ks < dkw, (comp, werr, ks, dkw)

    def wrong(self, x, sigma):
        X = self.grid.mesh()
        out = (2 * math.pi * sigma**2) ** (-self.grid.ndim / 4)
        for i in range(self.grid.ndim):
            out = out * np.exp(-((X[i] - x[i]) ** 2) / (2 * sigma**2))
        return np.broadcast_to(out, self.grid.shape)
    monkeypatch.setattr(Q.Scene, "kraus", wrong)
    comp, werr, ks, dkw = _measurement_errors(M=200)
    assert comp > 0.1 and werr > 0.05, (comp, werr)


def test_measurement_draws_the_absorbed_outcomes_with_their_probability():
    """A particle partly absorbed: the outcome "absorbed by detector k" comes with probability A_k (binomial, 5 sigma),
    the particle is then gone (norm 0, A_k = 1); a position outcome leaves norm 1 and nothing absorbed."""
    sc_ = Q.Scene((128, 80), 0.2, dt=0.01)
    det = sc_.add(Q.Detector([3.0, None], [None, None], 4.0, 0.8))
    pid = sc_.add_particle(Q.Packet(Q.species("electron"), [-2.0, 0.0], [4.0, 0.0], [1.0, 1.0]))
    sc_.advance(160)
    A = sc_.absorbed(pid)[f"detector {det}"]
    assert 0.2 < A < 0.8
    st = sc_.state_dict()
    rng = np.random.default_rng(5)
    hits, M = 0, 400
    for _ in range(M):
        s2 = Q.Scene.from_state_dict(st)
        r = s2.measure(pid, 0.6, rng)  # >= measure_min_sigma (0.52 here: review B6-Q4)
        if r["outcome"] == "absorbed":
            hits += 1
            assert s2.norm(pid) == 0.0 and s2.absorbed(pid) == {f"detector {det}": 1.0}
        else:
            assert abs(s2.norm(pid) - 1.0) < 1e-13 and sum(s2.absorbed(pid).values()) == 0.0
    assert abs(hits / M - A) < 5 * math.sqrt(A * (1 - A) / M), (hits / M, A)


# --- state ------------------------------------------------------------------------------------------------------------
def test_state_round_trip_is_bit_identical():
    """state_dict -> from_state_dict -> the same steps: every wave, absorbed record, jump and check is identical
    (a scene with shapes, detectors, a field, an environment region with jumps, a flux plane, two species; the grid
    fine enough for the waves after a jump of the environment: review B6-Q4)."""
    sc_ = Q.Scene((160, 160), 0.15, dt=0.02, edges=Q.EdgeLayers(2.5, 4.0), seed=7)
    sc_.add(Q.Box([1.0, 0.0], [0.8, 3.0], 2.0, 0.8))
    sc_.add(Q.Detector([4.0, None], [None, None], 3.0, 1.0))
    sc_.add(Q.Localization(1.0, 0.6, lo=[-1.0, None], hi=[2.0, None], edge=0.8))
    sc_.add(Q.MagneticField([0, 0, 0.5], gradient=[[0, 0, 0], [0, 0, 0.2], [0, 0.2, 0]]))
    p1 = sc_.add_particle(Q.Packet(Q.species("neutron", Q.Units(1e-9, sc.m_n)), [-2.5, 0], [2.0, 0.3], [1.0, 1.0],
                                   spin=[1, 1j]))
    p2 = sc_.add_particle(Q.Packet(Q.species("he4", Q.Units(1e-9, sc.m_n)), [-2.0, 1.0], [6.0, 0.0], [1.0, 1.0]))
    sc_.add_plane(0, 0.0)
    sc_.advance(60)
    st = sc_.state_dict()
    for v in st["particles"]:
        assert isinstance(v["psi"], np.ndarray)
    b = Q.Scene.from_state_dict(st)
    sc_.advance(80)
    b.advance(80)
    assert sum(len(p.jumps) for p in sc_.particles.values()) > 0
    for pid in (p1, p2):
        assert np.array_equal(sc_.wave(pid), b.wave(pid))
        assert np.array_equal(backend.to_numpy(sc_.particles[pid].acc), backend.to_numpy(b.particles[pid].acc))
        assert [t for t, _ in sc_.particles[pid].jumps] == [t for t, _ in b.particles[pid].jumps]
    ca, cb = sc_.checks(), b.checks()
    for pid in (p1, p2):
        assert ca[pid]["absorbed"] == cb[pid]["absorbed"] and ca[pid]["planes"] == cb[pid]["planes"]
        # the environment's Gamma/2 sits in W next to the detectors; its share is restored, not counted as absorbed
        assert abs(ca[pid]["balance"]) <= ca[pid]["balance_tol"] and sum(ca[pid]["absorbed"].values()) > 1e-3


# --- energy and the time step's error ---------------------------------------------------------------------------------
M1 = Q.species("atom", mass_u=sc.m_e / sc.atomic_mass)  # mass 1 (units of m_e)


def _closed_scene(dt):
    s = Q.Scene((96, 96), 0.25, dt=dt)
    s.add(Q.HarmonicTrap([0, 0], [1.0, 1.0]))
    s.add(Q.Box([0.5, 0.0], [1.0, 2.0], 3.0, 0.8))
    pid = s.add_particle(Q.Packet(M1, [-2.0, 0.5], [1.5, 0.5], [0.8, 0.8]))
    return s, pid


def test_energy_of_a_closed_scene_is_conserved_at_second_order():
    """A closed scene (no absorber, no measurement, fixed potentials: a trap and a smooth barrier): Strang's scheme keeps
    a modified energy, so <H> deviates by O(dt^2) without drift: the deviation at t = 4 falls 4x per halving of dt
    (measured 3.6) and stays below the rigorous bound 2 ||H psi|| e + e^2 ||H|| from the companion's error estimate e
    (loose by ~1e4: the time step's error is mostly a phase, which does not change <H>)."""
    drift = []
    for dt in (0.02, 0.01):
        s, pid = _closed_scene(dt)
        s.checks(error=True)
        for _ in range(20):
            s.advance(int(round(0.2 / dt)))
            s.step_error()
        r = s.checks()[pid]["energy"]
        assert r["closed"] and abs(r["drift"]) <= r["bound"], r
        drift.append(abs(r["drift"]))
    assert 3.0 < drift[0] / drift[1] < 5.0 and drift[1] < 1e-6, drift


def test_companion_estimates_the_step_error():
    """The companion (one step dt against two steps dt/2) gives the local error of one step: (4/3)||psi_dt - psi_dt/2||
    against the true one (the Chebyshev expansion of exp(-i H dt), exact to 1e-13), equal within the next order of
    Strang's error, O(dt) relative (measured: within 3 % at dt = 0.02 and 0.01). Accumulated over a run it bounds the
    global error (a contraction sums its local errors at most): measured 9.7x the true error at t = 4 for this
    oscillating packet (the errors partly cancel over the periods), the same ratio at both dt."""
    ratios = []
    for dt in (0.02, 0.01):
        s, pid = _closed_scene(dt)
        s.advance(37)
        psi = s.wave(pid)
        H = s.hamiltonian(s._key(s.particles[pid]))
        est = s.step_error()[pid]["local"]
        exact = S.chebyshev(H, psi, dt, tol=1e-15)
        s1 = Q.Scene.from_state_dict(s.state_dict())
        s1.advance(1)
        true = math.sqrt(s.grid.norm(s1.wave(pid) - exact))
        ratios.append(est / true)
    assert all(abs(r - 1) < 0.03 for r in ratios), ratios
    s, pid = _closed_scene(0.02)
    psi0 = s.wave(pid)
    for _ in range(20):
        s.advance(10)
        s.step_error()
    ref = S.chebyshev(s.hamiltonian(s._key(s.particles[pid])), psi0, 4.0)
    true = math.sqrt(s.grid.norm(s.wave(pid) - ref))
    acc = s.checks()[pid]["step_error"]["accumulated"]
    assert true <= acc <= 20 * true, (true, acc)


# --- flux through a plane ---------------------------------------------------------------------------------------------
def test_flux_through_a_plane_balances_the_probability_beyond_it():
    """The flux through a plane (16th-order centred differences) integrated in time (trapezoid) equals the change of the
    probability beyond the plane (trapezoid across with the Euler-Maclaurin end correction d^2/12 d rho/dn): the
    mismatch is the scheme's O(dt^2) (Strang's modified dynamics has a modified current): measured 3.6e-6 and 1.1e-6
    of 0.98 at dt = 0.01, 0.005 (ratio 3.3). Negative control: without the end correction the mismatch is the
    d^2/12 term itself, 1e3 times larger."""
    mm = []
    for dt in (0.01, 0.005):
        s = Q.Scene((128, 112), 0.2, dt=dt)
        pid = s.add_particle(Q.Packet(M1, [-3.0, 0.0], [3.0, 0.5], [1.0, 1.0]))
        pl = s.add_plane(0, 0.0)
        s.advance(int(round(2.0 / dt)))
        c = s.checks()[pid]["planes"][pl]
        assert c["valid"] and c["flux_integral"] > 0.9
        mm.append(abs(c["mismatch"]))
    assert 2.5 < mm[0] / mm[1] < 4.5 and mm[1] < 2e-6, mm
    # the uncorrected trapezoid across the plane, at the start (the packet far: 0) and now
    i = s.planes[pl]["index"]
    rho = s.density(pid)
    plain = (float(np.sum(rho[i + 1:])) + 0.5 * float(np.sum(rho[i]))) * s.grid.dV
    assert abs(plain - c["flux_integral"]) > 1e3 * mm[1]


# --- tunnelling, path marker: quasi-1-D against transfer matrices -----------------------------------------------------
def _gh(n=60):
    x, w = np.polynomial.hermite_e.hermegauss(n)
    return x, w / w.sum()


def test_tunnelling_through_a_smooth_barrier_against_transfer_matrices():
    """A packet (k0 = 2.5 below the barrier's top: E = 3.125 < 4) on a smooth box barrier (width 1, edges 0.4), uniform
    across (quasi-1-D: the transverse motion is free and exactly separable): the probability beyond the barrier is the
    1-D transmission averaged over the packet's momenta, T(k) ~ N(k0, 1/(2 sigma)) (Gauss-Hermite, 60 nodes), with T(k)
    by transfer matrices of the same profile (Richardson over 4000/8000 slices). The run's dt^2 error is removed by
    Richardson over dt, 2 dt; what remains is bounded by the edge layers' reflection (R T (1 - T)), the reference's
    Richardson residual and the next order in dt (half the dt correction). Measured: 1e-9."""
    U0, a, w, k0, sig = 4.0, 1.0, 0.4, 2.5, 3.0
    P = []
    for dt in (0.01, 0.005):
        s = Q.Scene((2048, 2), (0.05, 1.0), dt=dt, edges=Q.EdgeLayers(5.0, 6.0, axes=[0]))
        s.add(Q.Box([0.0, 0.0], [a, None], U0, w))
        pid = s.add_particle(Q.Packet(M1, [-25.0, 0.0], [k0, 0.0], [sig, math.inf]))
        s.advance(int(round((25.0 / k0 + 9.0) / dt)))
        x = s.grid.axes[0]
        beyond = (s.density(pid) * s.grid.dV + backend.to_numpy(s.particles[pid].acc) * s.grid.dV)[x > 0]
        P.append(float(np.sum(beyond)))
    xg, wg = _gh()
    ks = k0 + xg / (2 * sig)

    def V(xx):
        return U0 * Q.smooth_interval(np.asarray(xx), -a / 2, a / 2, w)
    T1 = transfer.transmission_profile(ks**2 / 2, V, -a / 2 - 3, a / 2 + 3, 4000)
    T2 = transfer.transmission_profile(ks**2 / 2, V, -a / 2 - 3, a / 2 + 3, 8000)
    ref = float(np.sum(wg * (T2 + (T2 - T1) / 3)))
    Pr = P[1] + (P[1] - P[0]) / 3
    R, _ = s.edge_reflection(np.array([k0 - 4 / (2 * sig), k0, k0 + 4 / (2 * sig)]), 1.0)
    tol = R.max() * ref * (1 - ref) + float(np.max(np.abs(T2 - T1))) / 3 + 0.5 * abs(P[1] - P[0]) / 3
    assert abs(Pr - ref) <= tol, (P, Pr, ref, tol)


def test_path_marker_turns_as_the_transfer_matrices_say():
    """A which-path marker in a slab (coupling c sigma_y on the marker inside, edges 0.5), crossed by a packet: the
    marker's eigen-components |+-y> see the potentials +-c f(x), so the transmitted marker state is
    (t_+ |+y> + t_- |-y>)/sqrt 2: P(marker 1) = E_k |t_+ - t_-|^2 / 4, P(marker 0) = E_k |t_+ + t_-|^2 / 4 (complex
    amplitudes of the staircase, Richardson over 4000/8000 slices). Bound as for the tunnelling test; measured 1e-11."""
    c, w, k0, sig = 1.0, 0.5, 3.0, 4.0
    out = []
    for dt in (0.01, 0.005):
        s = Q.Scene((4096, 2), (0.05, 1.0), dt=dt, edges=Q.EdgeLayers(6.0, 4.0, axes=[0]))
        s.add(Q.PathMarker([-1.0, None], [1.0, None], c, w))
        pid = s.add_particle(Q.Packet(M1, [-45.0, 0.0], [k0, 0.0], [sig, math.inf]))
        assert s.particles[pid].kind == "marker"
        s.advance(int(round(30.0 / dt)))  # the transmitted packet beyond x = 5, short of the edge layer at x = 96
        x = s.grid.axes[0]
        psi = s.wave(pid)
        out.append([float(np.sum(np.abs(psi[j][x > 5]) ** 2)) * s.grid.dV for j in (0, 1)])
    e = Q.edge_eps(w)
    xg, wg = _gh()
    ks = k0 + xg / (2 * sig)
    ref = []
    for n in (4000, 8000):
        z = np.linspace(-1 - 8 * e, 1 + 8 * e, n + 1)
        f = Q.smooth_interval(0.5 * (z[1:] + z[:-1]), -1, 1, w)
        tp, _ = transfer.staircase_amplitudes(ks**2 / 2, np.outer(np.ones_like(ks), c * f), z[1] - z[0])
        tm, _ = transfer.staircase_amplitudes(ks**2 / 2, np.outer(np.ones_like(ks), -c * f), z[1] - z[0])
        ref.append([float(np.sum(wg * np.abs(tp + tm) ** 2 / 4)), float(np.sum(wg * np.abs(tp - tm) ** 2 / 4))])
    for j in (0, 1):
        r = ref[1][j] + (ref[1][j] - ref[0][j]) / 3
        Pr = out[1][j] + (out[1][j] - out[0][j]) / 3
        R, _ = s.edge_reflection(np.array([k0 - 4 / (2 * sig), k0, k0 + 4 / (2 * sig)]), 1.0)
        tol = R.max() * r + abs(ref[1][j] - ref[0][j]) / 3 + 0.5 * abs(out[1][j] - out[0][j]) / 3 + 1e-12
        assert abs(Pr - r) <= tol, (j, out, r, tol)


# --- decoherence: quantum jumps against the master equation -----------------------------------------------------------
def _decoherence(region: bool, M: int = 800, lam_ref: float = 1.0):
    """M trajectories (particles of one scene) of a cat state in a 1-D trap under localization (lambda = 1, a = 0.8;
    everywhere or in x > 0), and the Lindblad master equation for the same grid operator, integrated directly
    (DOP853, rtol 1e-11) with the dissipator in closed form (module docstring). Returns the z-scores of four bounded
    observables at t = T/2 and T and the mean number of jumps."""
    N, d, lam, a = 64, 0.25, 1.0, 0.8
    T = math.pi / 2
    s = Q.Scene((N,), d, dt=T / 100, seed=3)
    s.add(Q.HarmonicTrap([0.0], [1.0]))
    s.add(Q.Localization(lam, a, lo=[0.0], hi=[None], edge=0.8) if region else Q.Localization(lam, a))
    g = s.grid
    x = g.axes[0]
    cat = np.exp(-(x - 2.5) ** 2) + np.exp(-(x + 2.5) ** 2)
    cat = cat / math.sqrt(g.norm(cat))
    pids = []
    for _ in range(M):
        pid = s.add_particle(Q.Packet(M1, [0.0], [0.0], [0.5]))
        s.set_wave(pid, cat)
        pids.append(pid)
    obs = {"P_left": (x < 0).astype(float), "x2": x**2 / 64.0, "cos": np.cos(5.0 * x)}

    def values():
        out = {k: [] for k in list(obs) + ["F_cat"]}
        for pid in pids:
            psi = s.wave(pid)
            n = g.norm(psi)
            rho = np.abs(psi) ** 2 * g.dV / n
            for k, o in obs.items():
                out[k].append(float(np.sum(rho * o)))
            out["F_cat"].append(abs(np.sum(np.conj(cat) * psi) * g.dV) ** 2 / n)
        return {k: np.array(v) for k, v in out.items()}
    traj = []
    for _ in range(2):
        s.advance(50)
        traj.append(values())
    H = s.hamiltonian(s._key(s.particles[pids[0]]))
    Hm = np.array([H.apply(e) for e in np.eye(N, dtype=complex)]).T
    lr = lam * lam_ref
    if region:
        w_tot = 2 * Q.ERF80 * math.sqrt(Q.edge_eps(0.8) ** 2 + a * a)
        chi = lambda z: Q.smooth_interval(z, 0.0, None, w_tot)  # noqa: E731
        D = (lr * np.exp(-(x[:, None] - x[None, :]) ** 2 / (4 * a * a)) * chi(0.5 * (x[:, None] + x[None, :]))
             - 0.5 * lr * (chi(x)[:, None] + chi(x)[None, :]))
    else:
        D = lr * (np.exp(-(x[:, None] - x[None, :]) ** 2 / (4 * a * a)) - 1.0)
    rho0 = (np.outer(cat, cat) * g.dV).astype(complex)

    def f(t, y):
        r = y.view(complex).reshape(N, N)
        return (-1j * (Hm @ r - r @ Hm) + D * r).ravel().view(float)
    sol = integrate.solve_ivp(f, (0, T), rho0.ravel().view(float), method="DOP853", rtol=1e-11, atol=1e-13,
                              t_eval=[T / 2, T])
    z = []
    for j in range(2):
        r = np.ascontiguousarray(sol.y[:, j]).view(complex).reshape(N, N)
        ref = {k: float(np.real(np.sum(np.diag(r) * o))) for k, o in obs.items()}
        ref["F_cat"] = float(np.real(cat @ r @ cat) * g.dV)
        for k, v in traj[j].items():
            z.append((v.mean() - ref[k]) / (v.std(ddof=1) / math.sqrt(M)))
    jumps = float(np.mean([len(s.particles[p].jumps) for p in pids]))
    return np.array(z), jumps, lam * T


@pytest.mark.parametrize("region", [False, True])
def test_decoherence_jumps_reproduce_the_master_equation(region):
    """The averages of 800 jump trajectories (the scene's unravelling) against the master equation of the same grid
    operator: every z-score of 8 comparisons below 5 (a false alarm has probability < 5e-6; measured max |z| 2.2
    everywhere, 1.0 in the region); the unitary part's time-step error on these observables is 8e-6, far below the
    statistical error ~1e-3. Everywhere, the number of jumps is Poisson(lambda T) (5 sigma)."""
    z, jumps, lt = _decoherence(region)
    assert np.max(np.abs(z)) < 5, z
    if not region:
        assert abs(jumps - lt) < 5 * math.sqrt(lt / 800), (jumps, lt)


def test_decoherence_negative_control_wrong_rate():
    """The same trajectories against a master equation with 0.7 lambda: caught (max |z| measured 9.9)."""
    z, _, _ = _decoherence(False, lam_ref=0.7)
    assert np.max(np.abs(z)) > 5, z


# --- Bohm trajectories from the scene's snapshots ---------------------------------------------------------------------
def test_bohm_trajectories_from_the_scene_follow_the_exact_free_ones():
    """The scene gives what theories.interpretations.bohm needs (snapshots at t, t + h/2, t + h; the grid, H, the array
    module): Bohm points advanced with them in a free packet follow the exact trajectories (each keeps its quantile)
    to the integrator's tolerance (rtol 1e-5 of each step's displacement, atol 1e-6 d) accumulated over 30 steps."""
    from lfphys.theories.interpretations import bohm
    s = Q.Scene((96, 96), 0.2, dt=0.01)
    c, k, sg = (-1.0, 0.5), (2.0, -1.0), (1.0, 1.2)
    pid = s.add_particle(Q.Packet(M1, list(c), list(k), list(sg)))
    X = np.random.default_rng(2).normal(c, sg, (50, 2))
    X0 = X.copy()
    for _ in range(30):
        s.advance(2, snapshots=True)
        snaps, h = s.snapshots(pid)
        grid, H, xp = s.guidance(pid)
        X, _ = bohm.advance_ensemble(grid, snaps, X, h, H, xp=xp)
    ref = bohm.gaussian_trajectory(X0, s.t, c, k, sg)
    s.advance(1)
    assert s.snapshots(pid) is None  # stale snapshots are dropped by a step without them
    disp = np.linalg.norm(ref - X0, axis=1)
    assert np.max(np.linalg.norm(X - ref, axis=1)) < 30 * (1e-6 * 0.2) + 1e-5 * float(disp.max()), \
        np.max(np.linalg.norm(X - ref, axis=1))


# --- the double slit: the far field and the Aharonov-Bohm shift -------------------------------------------------------
K0 = 2 * math.pi  # lambda = 1
E0 = 0.5 * K0**2
SLIT_D, SLIT_A, WALL = 4.0, 1.2, 1.6


@functools.lru_cache(maxsize=None)
def _double_slit(sx: float, flux: float = 0.0):
    """An electron packet (lambda = 1, sigma_z = 2) through two slits (width 1.2, centres +-2, wall 1.6 thick, 4 E0
    high, edges 0.55 = 3.3 grid steps) and, with ``flux``, an Aharonov-Bohm tube (radius 0.25) inside the wall between
    them. The far-field pattern is the transverse kinetic-momentum distribution of the transmitted wave (free motion
    beyond the wall conserves it): |FFT_x psi'|^2 summed over z beyond the wall (zero-padded 8x: the exact transform of
    the localized wave), psi' = psi exp(-i q (Phi/2pi) atan2(y, x)) the gauge in which A = 0 in the transmitted
    half-plane (``kinetic=False``: the canonical momentum of the scene's gauge, a negative control). Returns the minima
    (k at the four minima nearest -+3pi/D, -+pi/D; parabolic interpolation) for (kinetic, canonical)."""
    h = 1 / 6
    half = math.ceil(7.43 * sx + 5.0)
    nx, nz = int(round(2 * half / h)), int(round(51 / h))
    s = Q.Scene((nx, nz), h, center=(0.0, -27 + 0.5 * nz * h), dt=0.1 / E0, edges=Q.EdgeLayers(4.0, 2 * E0))
    s.add(Q.SlitWall(1, 0.0, WALL, 4 * E0, [[-SLIT_D / 2, SLIT_A], [SLIT_D / 2, SLIT_A]], 0.55))
    if flux:
        s.add(Q.FluxTube([0.0, 0.0], flux, 0.25))
    el = Q.species("electron")
    pid = s.add_particle(Q.Packet(el, [0.0, -11.0], [0.0, K0], [sx, 2.0]))
    s.advance(750)
    g = s.grid
    cut = g.axes[1] > 0.5 * WALL + 1.0
    psi = s.wave(pid)
    assert float(np.sum(np.abs(psi[:, cut]) ** 2)) * g.dV > 0.14  # the transmitted part
    out = []
    for kinetic in (True, False):
        p = psi
        if flux and kinetic:
            X, Y = g.mesh()
            p = psi * np.exp(-1j * el.charge * flux / (2 * math.pi) * np.arctan2(Y, X))
        F = np.fft.fft(p[:, cut], n=8 * nx, axis=0)
        P = np.sum(np.abs(F) ** 2, axis=1)
        k = 2 * math.pi * np.fft.fftfreq(8 * nx, h)
        o = np.argsort(k)
        k, P = k[o], P[o]
        mins = []
        for target in (-3, -1, 1, 3):
            m = np.abs(k - target * math.pi / SLIT_D) < 0.6 * math.pi / SLIT_D
            i = np.flatnonzero(m)[np.argmin(P[m])]
            y0, y1, y2 = P[i - 1], P[i], P[i + 1]
            mins.append(k[i] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (k[1] - k[0]))
        out.append(np.array(mins) * SLIT_D / math.pi)
    return tuple(out)


def test_double_slit_far_field_approaches_fraunhofer():
    """The minima of the far-field pattern sit at k = (2n+1) pi/D in the Fraunhofer limit of identical, uniformly lit
    slits. Here each slit is lit by the packet's slope across it, beta = D/(4 sigma_x^2), which tilts the phase of its
    amplitude (odd in k, first order in beta) and moves the minima by O(beta): the deviation must fall 4x when sigma_x
    doubles. Measured: D k/pi - (2n+1) = 0.0051, 0.0155 at sigma_x = 3 and 0.0014, 0.0041 at 6 (ratio 3.7; the rest, a
    sigma-independent -0.0024 of pi/D, is the slits' coupling through the wall and the near field). Asserted: the
    deviation falls at least 3x and below 0.2 % of the minimum's k at sigma_x = 6; mirror symmetry exact (round-off)."""
    d3 = _double_slit(3.0)[0] - np.array([-3, -1, 1, 3])
    d6 = _double_slit(6.0)[0] - np.array([-3, -1, 1, 3])
    assert np.max(np.abs(d3 + d3[::-1])) < 1e-9 and np.max(np.abs(d6 + d6[::-1])) < 1e-9
    rel3, rel6 = np.abs(d3) / np.array([3, 1, 1, 3]), np.abs(d6) / np.array([3, 1, 1, 3])
    assert np.all(rel3 / rel6 > 3.0) and np.all(rel6 < 2e-3), (d3, d6)


def test_aharonov_bohm_shift_of_the_fringes():
    """A flux Phi in a tube the wave cannot reach (inside the wall between the slits; its field exp(-r^2/R^2) is
    e^-10 at the wall's faces) adds the phase q Phi / hbar between the paths: the minima move by
    delta k = q Phi / (hbar D), i.e. D delta k / pi = q Phi / pi = -0.5 and -0.25 for an electron at Phi = pi/2, pi/4
    (flux quantum h/e = 2 pi). The same slit asymmetry that moves the minima (previous test, relative deviation
    eta = 0.0051 at the first minima) makes the shift's relative error eta to first order (minimum condition
    k D + dtheta(k) = pi + q Phi with dtheta odd and linear in k: shift = q Phi / (D + dtheta')); asserted 1.5 eta.
    Measured: -0.50249, -0.25129. Negative control: the canonical momentum of the scene's gauge (A ~ Phi/(2 pi r) is
    still non-zero where the transmitted wave is) gives -0.4767: caught."""
    base = _double_slit(3.0)
    eta = float(np.max(np.abs(base[0] - np.array([-3, -1, 1, 3])) / np.array([3, 1, 1, 3])))
    for flux in (math.pi / 2, math.pi / 4):
        kin, can = _double_slit(3.0, flux)
        expect = -flux / math.pi  # q = -1
        shift = kin - base[0]
        assert np.max(np.abs(shift / expect - 1)) < 1.5 * eta, (shift, expect, eta)
        assert np.max(np.abs((can - base[1]) / expect - 1)) > 3 * eta


# --- devices and cost -------------------------------------------------------------------------------------------------
def test_cost_estimate_and_measured_speed():
    s = Q.Scene((128, 128), 0.2, dt=0.01, device="cpu")
    assert s.cost_estimate()["per_step_s"] == 0.0
    s.add_particle(Q.Packet(M1, [0, 0], [1, 0], [1, 1]))
    s.add_particle(Q.Packet(Q.species("neutron"), [1, 0], [1, 0], [1, 1], spin=[1, 1]))
    s.add(Q.MagneticField([0, 0, 0.1]))  # the neutron's spin (along x) is not an eigenstate: a spinor
    c = s.cost_estimate()
    assert c["device"] == "cpu" and [p["kind"] for p in c["per_particle"]] == ["scalar", "spinor"]
    assert c["per_particle"][1]["seconds"] > c["per_particle"][0]["seconds"] > 0
    s.advance(5)
    assert s.cost_estimate()["measured_per_step_s"] > 0
    d = s.describe()
    assert [o["type"] for o in d["objects"]] == ["magnetic_field"] and [p["wave"] for p in d["particles"]] == \
        ["scalar", "spin"]


@pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="no GPU")
def test_gpu_scene_equals_cpu_scene():
    """The same scene on GPU 0 and on the CPU (cuFFT and pocketfft round differently: ~eps per step)."""
    def build(device):
        s = Q.Scene((256, 256), 0.1, dt=0.005, edges=Q.EdgeLayers(3.0, 4.0), device=device, seed=1)
        s.add(Q.Box([1.0, 0.0], [0.6, 2.0], 3.0, 0.4))
        s.add(Q.FluxTube([-1.0, 2.0], 1.0, 0.4))
        s.add(Q.Localization(2.0, 0.5, lo=[0.0, None], hi=[None, None], edge=0.5))
        s.add_particle(Q.Packet(Q.species("electron"), [-1.0, 0.0], [3.0, 0.0], [1.0, 1.0]))
        return s
    a, b = build("auto"), build("cpu")
    a.advance(100)
    b.advance(100)
    assert a.device == "gpu" and b.device == "cpu"
    assert np.max(np.abs(a.wave(1) - b.wave(1))) < 1e-12 * 100


# --- review B6: bookkeeping (Q12, Q13), shapes (Q14), closed edges and switches (Q2, Q3), resolution (Q4), the
# companion's schedule (Q7), jumps with a detector (Q15) ----------------------------------------------------------------
def test_snapshots_are_dropped_by_every_break_of_the_interval():
    """Review B6-Q12: after a measurement, a wave set by hand, a change of the set-up or a new packet, ``snapshots``
    gives None (it gave the stale pre-measurement interval)."""
    s = Q.Scene((96, 96), 0.25, dt=0.01)
    pid = s.add_particle(Q.Packet(M1, [0.0, 0.0], [1.0, 0.0], [1.5, 1.5]))
    rng = np.random.default_rng(0)
    for brk in (lambda: s.measure(pid, 0.8, rng), lambda: s.set_wave(pid, s.wave(pid)),
                lambda: s.add(Q.Box([5.0, 0.0], [1.0, 1.0], 0.1, 0.8)),
                lambda: s.replace_particle(pid, Q.Packet(M1, [0.0, 0.0], [1.0, 0.0], [1.5, 1.5]))):
        s.advance(4, snapshots=True)
        assert s.snapshots(pid) is not None
        brk()
        assert s.snapshots(pid) is None


def test_the_energy_reference_is_dated_when_it_is_taken():
    """Review B6-Q13: after a change at t = 0 the first check at t = 3 takes the reference energy; "since" is 3, not 0
    (negative control: the time of the change)."""
    s = Q.Scene((96, 96), 0.25, dt=0.01)
    s.add(Q.HarmonicTrap([0, 0], [1.0, 1.0]))
    pid = s.add_particle(Q.Packet(M1, [-2.0, 0.5], [1.5, 0.5], [0.8, 0.8]))
    s.advance(300)
    c = s.checks()[pid]["energy"]
    assert c["since"] == pytest.approx(3.0) and c["since"] != 0.0 and c["drift"] == 0.0


def test_a_shapes_peak_and_the_balls_kink():
    """Review B6-Q14: ``peak`` is the closed-form extremum (the grid's maximum on a fine grid through the centre agrees
    to 1e-12): a box 1.5 wide with a 1-wide edge reaches erf(1.5 / (2 eps)) = 0.947 of its height. A ball whose radius
    is below 1.45 edges is refused: S(R - |r|) has a kink at the centre of slope exp(-R^2/eps^2) (0.45 of the steepest
    at R = 0.5, w = 1) — the edge rule's 1e-3 sets 1.45 = sqrt(ln 1e3) / (2 erfinv 0.8)."""
    g = S.Grid((201, 201), 0.01)
    box = Q.Box([0.0, 0.0], [1.5, None], 2.0, 0.995)  # the tunnel preset's barrier (B6 s01: 0.473 of 0.5 eV)
    assert abs(box.peak(2) - float(box.V(g).max())) < 1e-12
    assert abs(box.peak(2) / 2.0 - 0.9467) < 1e-4
    ball = Q.Ball([0.0, 0.0], 1.6, -1.0, 1.0)
    assert abs(ball.peak(2) - float(ball.V(g).min())) < 1e-12
    wall = Q.SlitWall(0, 0.0, 1.0, 3.0, [[3.0, 1.0]], 0.8)
    assert abs(wall.peak(2) - float(wall.V(g).max())) < 1e-12
    sc_ = Q.Scene((64, 64), 0.25, dt=0.01)
    assert abs(Q.BALL_MIN - 1.450) < 1e-3
    with pytest.raises(ValueError, match="kink"):
        sc_.add(Q.Ball([0.0, 0.0], 0.5, 1.0, 1.0))
    sc_.add(Q.Ball([0.0, 0.0], 1.46, 1.0, 1.0))


def _sheet_run(edges, bypass=False):
    """Review B6-Q2 (s09b): a field Bz in x in [-5, 5], y in [5, 15] (1.5 h/e); an electron at (12, 10) moving along +x
    crosses the face x = 30 -> -30 without entering the field. Returns <v_y> at t = 12 (None when refused)."""
    el = Q.species("electron")
    s = Q.Scene((240, 240), 0.25, dt=0.01, edges=edges)
    if bypass:
        s._gauge_reason = lambda *a, **k: None
    s.add(Q.MagneticField([0, 0, 1.5 * 2 * math.pi / 100.0], lo=[-5.0, 5.0], hi=[5.0, 15.0], edge=1.0))
    pid = s.add_particle(Q.Packet(el, [12.0, 10.0], [2.0, 0.0], [1.5, 1.5]))
    s.advance(1200)
    psi = s.wave(pid)
    J = s.grid.current(psi, s.hamiltonian(s._key(s.particles[pid])))
    return float(np.sum(J[1])) * s.grid.dV / s.norm(pid)


def test_a_closed_window_refuses_a_charged_particle_next_to_a_field():
    """Review B6-Q2: with closed (periodic) edges the Landau gauge's strip reaches the face, where the wrap is a sheet
    of field (flux -Phi): refused for a charged particle, whichever comes first, also with edges on one axis only and
    for a flux tube; open edges take it. Negative control: with the refusal bypassed, the packet that never meets the
    field gets the sheet's kick, <v_y> = -0.75 (s09b), against -0.009 with open edges (what is left of it after the
    layer)."""
    el = Q.species("electron")
    fld = Q.MagneticField([0, 0, 0.1], lo=[-5.0, 5.0], hi=[5.0, 15.0], edge=1.0)
    for edges in (None, Q.EdgeLayers(3.0, 4.0, axes=[1])):
        s = Q.Scene((240, 240), 0.25, dt=0.01, edges=edges)
        s.add(fld)
        with pytest.raises(ValueError, match="closed"):
            s.add_particle(Q.Packet(el, [12.0, 10.0], [2.0, 0.0], [1.5, 1.5]))
        s2 = Q.Scene((240, 240), 0.25, dt=0.01, edges=edges)
        s2.add_particle(Q.Packet(el, [12.0, 10.0], [2.0, 0.0], [1.5, 1.5]))
        with pytest.raises(ValueError, match="closed"):
            s2.add(Q.FluxTube([-10.0, 0.0], math.pi, 1.0))
        s2.add_particle(Q.Packet(Q.species("neutron"), [-12.0, -10.0], [1.0, 0.0], [1.5, 1.5]))
        s2.add(Q.HarmonicTrap([0, 0], [0.01, 0.01]))  # other objects stay allowed
    s3 = Q.Scene((240, 240), 0.25, dt=0.01, edges=Q.EdgeLayers(3.0, 4.0))
    s3.add(fld)
    s3.add_particle(Q.Packet(el, [12.0, 10.0], [2.0, 0.0], [1.5, 1.5]))
    assert abs(_sheet_run(None, bypass=True) + 0.748) < 0.01
    assert abs(_sheet_run(Q.EdgeLayers(3.0, 4.0))) < 0.02


def test_a_uniform_field_is_not_changed_under_a_charged_wave():
    """Review B6-Q3: psi is kept at a change, so the kinetic momentum jumps by -q Delta A of the scene's gauge. For a
    flux tube (the Coulomb gauge of a thin solenoid: Faraday's induced field) a change is kept; for a uniform field's
    Landau gauge it is refused while the charged wave's probability is where Delta A != 0 (above the balance's
    round-off), allowed where it is not (a field far from the packet, its strip on the other side). Negative control
    (s15): with the refusal bypassed, the same field as a whole-window field (A_y = B x) and as a 76-nm box
    (A_y = B (x + 38) inside), identical in the window, give the packet kinetic momenta that differ by q Delta B 38 nm
    right after the change: 2.89/nm against k = 1.57/nm."""
    el = Q.species("electron")
    B = 100.0 / Q.Units().field
    vy = []
    for region in (None, (-38.0, 38.0)):
        s = Q.Scene((256, 256), 80 / 256, dt=2.0**-7, edges=Q.EdgeLayers(8.0, 5.0))
        lo, hi = (None, None) if region is None else ([region[0]] * 2, [region[1]] * 2)
        oid = s.add(Q.MagneticField([0, 0, B], lo=lo, hi=hi, edge=None if region is None else 1.0))
        pid = s.add_particle(Q.Packet(el, [0.0, -10.0], [2 * math.pi / 4, 0.0], [3.0, 3.0]))
        s.advance(64)
        with pytest.raises(ValueError, match="field cannot be changed"):
            s.update(oid, B=[0, 0, 0.5 * B])
        s._switch_reason = lambda *a, **k: None
        s.update(oid, B=[0, 0, 0.5 * B])
        psi = s.wave(pid)
        J = s.grid.current(psi, s.hamiltonian(s._key(s.particles[pid])))
        vy.append(float(np.sum(J[1])) * s.grid.dV / s.norm(pid))
    assert abs(abs(vy[0] - vy[1]) - 0.5 * B * 38.0) < 0.01, vy
    s = Q.Scene((256, 256), 80 / 256, dt=2.0**-7, edges=Q.EdgeLayers(8.0, 5.0))
    tube = s.add(Q.FluxTube([0.0, 10.0], math.pi, 0.6))
    far = s.add(Q.MagneticField([0, 0, 0.1 * B], lo=[-30.0, 20.0], hi=[-20.0, 30.0], edge=1.0, string=-1))
    s.add_particle(Q.Packet(el, [0.0, -10.0], [2 * math.pi / 4, 0.0], [3.0, 3.0]))
    s.update(tube, flux=0.5 * math.pi)
    s.update(far, B=[0, 0, 0.2 * B])
    s.add(Q.MagneticField([0, 0, 0.1 * B], lo=[20.0, 20.0], hi=[25.0, 25.0], edge=1.0))


def test_the_grid_must_hold_a_wave_in_a_well():
    """Review B6-Q4: next to a potential the wave's wavenumbers, |k| + 6 sigma_k raised by the energy the potential
    can convert, must stay within 2/3 of the grid's band. Quasi-1-D (exact against transfer matrices of the same
    profile, averaged over the packet's momenta): an electron (lambda = 2 nm, sigma 2.5 nm) over a -3 eV well 4 nm
    wide: on the 0.3125-nm grid (K_loc d = 3.10) the scene refuses it; with the rule bypassed (the whole band
    admitted) the probability past the well errs by 7.4e-2; on admitted grids (0.208 and 0.156 nm) by 2.4e-6 and
    2e-7 (asserted 1e-5). Measurement: s >= measure_min_sigma passes, 0.99 of it is refused."""
    k0, sig, a, w = math.pi, 2.5, 4.0, 1.0
    V0 = -3.0 / (Q.Units().energy / sc.e)
    xg, wg = np.polynomial.hermite_e.hermegauss(60)
    wg = wg / wg.sum()
    ks = k0 + xg / (2 * sig)

    def Vf(xx):
        return V0 * Q.smooth_interval(np.asarray(xx), -a / 2, a / 2, w)
    T1 = transfer.transmission_profile(ks**2 / 2, Vf, -a / 2 - 6, a / 2 + 6, 8000)
    T2 = transfer.transmission_profile(ks**2 / 2, Vf, -a / 2 - 6, a / 2 + 6, 16000)
    ref = float(np.sum(wg * (T2 + (T2 - T1) / 3)))

    def past(d, bypass=False):
        s = Q.Scene((int(round(160 / d)), 2), (d, 1.0), dt=2.0**-9, edges=Q.EdgeLayers(10.0, 30.0, axes=[0]))
        if bypass:
            s._resolution_reason = lambda *a_, **k_: None
        s.add(Q.Box([0.0, 0.0], [a, None], V0, w))
        pid = s.add_particle(Q.Packet(M1, [-25.0, 0.0], [k0, 0.0], [sig, math.inf]))
        s.advance(int(round(14.0 * 2**9)))
        x = s.grid.axes[0]
        return float(np.sum((s.density(pid) + backend.to_numpy(s.particles[pid].acc))[x > 4.0])) * s.grid.dV
    s = Q.Scene((512, 2), (80 / 256, 1.0), dt=2.0**-9, edges=Q.EdgeLayers(10.0, 30.0, axes=[0]))
    s.add(Q.Box([0.0, 0.0], [a, None], V0, w))
    with pytest.raises(ValueError, match="the grid does not carry"):
        s.add_particle(Q.Packet(M1, [-25.0, 0.0], [k0, 0.0], [sig, math.inf]))
    assert abs(past(80 / 256, bypass=True) - ref) > 0.05
    for d in (80 / 384, 80 / 512):
        assert abs(past(d) - ref) < 1e-5
    # the measurement: a free packet on the double slit's grid (review s10: s = d left an unresolved wave)
    s = Q.Scene((256, 256), 80 / 256, dt=2.0**-7)
    pid = s.add_particle(Q.Packet(M1, [-20.0, 0.0], [k0, 0.0], [2.5, 4.0]))
    sm = s.measure_min_sigma(pid)
    k_, sk = s.k_spread(pid)
    assert abs(k0 + 6 * math.sqrt(float(np.max(sk ** 2)) + 0.25 / sm ** 2) - math.pi / (80 / 256)) < 1e-9
    st = s.state_dict()
    with pytest.raises(ValueError, match="too small"):
        s.measure(pid, 0.99 * sm, np.random.default_rng(1))
    assert np.array_equal(s.wave(pid), Q.Scene.from_state_dict(st).wave(pid))  # refused: nothing changed
    s.measure(pid, sm, np.random.default_rng(1))


def test_the_companion_is_sampled_by_steps():
    """Review B6-Q7: the accumulated step-error estimate is as good as its sampling. A packet crosses a barrier
    between two free stretches (exact steps: local error ~0): estimated only at the start and the end the sum misses
    the crossing, 1.3e-4 against the true global error 5.5e-4 (Chebyshev reference) — the negative control; with an
    estimate every 64 scene steps (``error_every``) it is 8.6e-3 (an estimate of the bound: 16 x the true error here),
    within 1 % of estimates every 10 steps, whoever reads it how often."""
    def build():
        s = Q.Scene((256, 96), 0.25, dt=0.02)
        s.add(Q.Box([0.0, 0.0], [1.0, None], 6.0, 0.8))
        pid = s.add_particle(Q.Packet(M1, [-12.0, 0.0], [3.0, 0.0], [1.5, 1.5]))
        return s, pid
    s, pid = build()
    psi0 = s.wave(pid)
    s.step_error()
    for _ in range(40):
        s.advance(10)
        s.step_error()
    dense = s.checks()[pid]["step_error"]["accumulated"]
    true = math.sqrt(s.grid.norm(s.wave(pid) - S.chebyshev(s.hamiltonian(s._key(s.particles[pid])), psi0, 8.0,
                                                           tol=1e-14)))
    acc = {}
    for every in (0, 64):
        s, pid = build()
        s.error_every = every
        s.step_error()
        s.advance(400)
        s.step_error()
        acc[every] = s.checks()[pid]["step_error"]["accumulated"]
    assert acc[0] < true < acc[64] and abs(acc[64] / dense - 1) < 0.01, (acc, dense, true)
    b = Q.Scene.from_state_dict(s.state_dict())
    assert b.error_every == 64


def test_jumps_and_a_detector_together_reproduce_the_master_equation():
    """Review B6-Q15 (its s11): the localization unravelling together with a detector — each step's loss split
    W_k : Gamma/2, the detectors' part kept as absorbed probability, the hazard ln((n0 - Delta A)/n1) — against the
    master equation of the in-flight density matrix with the detector as -i W in H_eff and dA/dt = 2 sum W rho
    (DOP853): 800 trajectories, 12 z-scores (norm, P_left, x^2, cos 5x, the cat fidelity, A at T/2 and T) below 5
    (measured 1.39). Negative control: the master equation with 0.7 W is rejected (measured max |z| 18.4)."""
    def run(W_ref, M=800):
        N, d, lam, a = 64, 0.25, 1.0, 0.8
        T = math.pi / 2
        s = Q.Scene((N,), d, dt=T / 100, seed=3)
        s.add(Q.HarmonicTrap([0.0], [1.0]))
        s.add(Q.Localization(lam, a, lo=[0.0], hi=[None], edge=0.8))
        det = s.add(Q.Detector([1.5], [3.5], 0.6, 0.8))
        g = s.grid
        x = g.axes[0]
        cat = np.exp(-(x - 2.5) ** 2) + np.exp(-(x + 2.5) ** 2)
        cat = cat / math.sqrt(g.norm(cat))
        pids = []
        for _ in range(M):
            pid = s.add_particle(Q.Packet(M1, [0.0], [0.0], [0.5]))
            s.set_wave(pid, cat)
            pids.append(pid)
        obs = {"P_left": (x < 0).astype(float), "x2": x**2 / 64.0, "cos": np.cos(5.0 * x)}
        traj = []
        for _ in range(2):
            s.advance(50)
            out = {k: [] for k in list(obs) + ["norm", "F_cat", "A"]}
            for pid in pids:
                psi = s.wave(pid)
                rho = np.abs(psi) ** 2 * g.dV
                out["norm"].append(float(np.sum(rho)))
                for k, o in obs.items():
                    out[k].append(float(np.sum(rho * o)))
                out["F_cat"].append(abs(np.sum(np.conj(cat) * psi) * g.dV) ** 2)
                out["A"].append(s.absorbed(pid).get(f"detector {det}", 0.0))
            traj.append({k: np.array(v) for k, v in out.items()})
        H = s.hamiltonian(s._key(s.particles[pids[0]]))
        Hm = np.array([H.apply(e) for e in np.eye(N, dtype=complex)]).T
        W = s._arr["W_parts"][f"detector {det}"] * W_ref
        w_tot = 2 * Q.ERF80 * math.sqrt(Q.edge_eps(0.8) ** 2 + a * a)
        chi = lambda z: Q.smooth_interval(z, 0.0, None, w_tot)  # noqa: E731
        D = (lam * np.exp(-(x[:, None] - x[None, :]) ** 2 / (4 * a * a)) * chi(0.5 * (x[:, None] + x[None, :]))
             - 0.5 * lam * (chi(x)[:, None] + chi(x)[None, :]) - (W[:, None] + W[None, :]))
        rho0 = (np.outer(cat, cat) * g.dV).astype(complex)

        def f(t, y):
            r = y[:-1].view(complex).reshape(N, N)
            dr = (-1j * (Hm @ r - r @ Hm) + D * r).ravel().view(float)
            return np.concatenate([dr, [2 * float(np.sum(W * np.real(np.diag(r))))]])
        sol = integrate.solve_ivp(f, (0, T), np.concatenate([rho0.ravel().view(float), [0.0]]), method="DOP853",
                                  rtol=1e-11, atol=1e-13, t_eval=[T / 2, T])
        z = []
        for j in range(2):
            r = np.ascontiguousarray(sol.y[:-1, j]).view(complex).reshape(N, N)
            ref = {k: float(np.real(np.sum(np.diag(r) * o))) for k, o in obs.items()}
            ref["norm"] = float(np.real(np.trace(r)))
            ref["F_cat"] = float(np.real(cat @ r @ cat) * g.dV)
            ref["A"] = float(sol.y[-1, j])
            z += [(v.mean() - ref[k]) / (v.std(ddof=1) / math.sqrt(M)) for k, v in traj[j].items()]
        return np.array(z), max(abs(r["balance"]) for r in s.checks().values())
    z, bal = run(1.0)
    assert np.max(np.abs(z)) < 5 and bal < 1e-12, z
    z2, _ = run(0.7)
    assert np.max(np.abs(z2)) > 5, z2


def test_oblique_incidence_on_the_edge_layers():
    """Review B6-Q8: a layer uniform across conserves the transverse momentum, so a wave at angle theta meets it as a
    1-D wave of k cos(theta) (what the playground's angular average of the edges' reflection uses). A packet at 60
    degrees (k = 4: k_x = 2) on the layer of one axis (the other periodic): the probability sent back against
    ``edge_reflection`` at k_x over the packet's momenta, within 2 % of R (as the detector's test). The layer is strong
    enough that its leak (1e-5) is far below R (0.017): ``layer_reflection`` models the layer as a ramp that ends
    abruptly, while on the periodic grid the leak meets the opposite face's mirrored ramp; with a leak of 0.38 (W0 = 1)
    the model's R, mostly from that abrupt end, was 14 times what the run sent back — conservative, and the
    playground's strengths keep the leak below 1e-5."""
    k, th, sig = 4.0, math.radians(60), 3.0
    s = Q.Scene((512, 192), 0.2, dt=0.0125, edges=Q.EdgeLayers(3.0, 20.0, axes=[0]))
    pid = s.add_particle(Q.Packet(M1, [-28.0, 0.0], [-k * math.cos(th), k * math.sin(th)], [sig, 2.0]))
    s.advance(int(round(22.0 / 0.0125)))  # the reflected packet back near x = -24; the leak wrapped to x > 0
    x = s.grid.axes[0]
    back = float(np.sum(s.density(pid)[(x > -45.0) & (x < 0.0)])) * s.grid.dV
    xg, wg = np.polynomial.hermite_e.hermegauss(60)
    R, T = s.edge_reflection(k * math.cos(th) + xg / (2 * sig), 1.0)
    ref = float(np.sum(wg * R) / np.sum(wg))
    assert ref > 1e-4 and abs(back - ref) < 0.02 * ref, (back, ref)


def test_a_packet_centred_outside_the_window_is_refused(ru):
    """Review UX-params P29: a centre beyond the window (x = 1e6 nm in an 80 nm window) passed the window test,
    because the test squared the distance to the edge, which is then negative; the packet's Gaussian underflowed to 0
    on the grid and the normalisation made the wave NaN (the playground then showed «норма + поглощённое» = NaN and
    crashed in «Probabilities contain NaN»). Refused now, in the scene's words; a centre just inside still is refused
    only for the tail, and a fitting one is admitted."""
    sc_ = Q.Scene((64, 64), 0.5, dt=0.01)
    sp = Q.species("electron")
    s = 1.0
    need = s * math.sqrt(2 * math.log(1 / Q.PACKET_TAIL))
    for x in (1e6, -1e6, 16.5, -40.0):  # the window is [-16, 16)
        gap = 16.0 - abs(x)
        if abs(x) > 20.0:  # negative control: the former test alone, gap^2 / (2 s^2) < ln(1/tail), let these through
            assert not gap * gap / (2 * s * s) < math.log(1 / Q.PACKET_TAIL)
        with pytest.raises(ValueError, match="outside the window") as e:
            sc_.add_particle(Q.Packet(sp, [x, 0.0], [1.0, 0.0], [s, s]))
        assert ru(e.value.args[0]).startswith("центр пакета вне окна по оси x")
    with pytest.raises(ValueError, match="does not fit"):
        sc_.add_particle(Q.Packet(sp, [16.0 - 0.5 * need, 0.0], [1.0, 0.0], [s, s]))
    pid = sc_.add_particle(Q.Packet(sp, [0.0, 0.0], [1.0, 0.0], [s, s]))
    assert np.isfinite(sc_.norm(pid)) and sc_.norm(pid) == pytest.approx(1.0, abs=1e-12)
    with pytest.raises(ValueError, match="outside the window"):  # the same for a new packet of an existing particle
        sc_.replace_particle(pid, Q.Packet(sp, [1e6, 0.0], [1.0, 0.0], [s, s]))
    assert sc_.norm(pid) == pytest.approx(1.0, abs=1e-12)  # refused: the particle is as it was
