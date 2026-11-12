# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.em.slit: Sommerfeld's half-plane, the modal method and the edge basis, against closed forms, published
results and independent routes (sources: lfphys/sources/verification_2026-11-04_p1_charges_slit.md); and the scalar
Kirchhoff result of lfphys.theories.approx.kirchhoff against it. Lengths in wavelengths (k = 2 pi)."""

import math

import numpy as np
import pytest
from scipy import optimize

from lfphys.core.em import slit as S
from lfphys.theories.approx import kirchhoff as KI

K = 2 * math.pi


# --- Sommerfeld's half-plane ----------------------------------------------------------------------------------------------
def _lap(f, x, z, h):
    c = np.array([-1, 16, -30, 16, -1]) / 12.0
    acc = 0
    for o, cc in zip((-2, -1, 0, 1, 2), c):
        acc = acc + cc * (f(x + o * h, z) + f(x, z + o * h))
    return acc / (h * h)


@pytest.mark.parametrize("pol", ["TE", "TM"])
@pytest.mark.parametrize("theta", [0.0, 0.5, -0.9])
def test_half_plane_satisfies_helmholtz(pol, theta):
    rng = np.random.default_rng(1)
    r = rng.uniform(0.3, 6.0, 40)
    ph = rng.uniform(-math.pi + 0.2, math.pi - 0.2, 40)  # away from the screen (phi_c = +-pi)
    x, z = r * np.cos(ph), r * np.sin(ph)
    f = lambda xx, zz: S.half_plane(K, xx, zz, pol, theta)  # noqa: E731
    res = np.abs(_lap(f, x, z, 2e-3) + K * K * f(x, z)) / (K * K * np.maximum(np.abs(f(x, z)), 0.05))
    assert np.max(res) < 1e-7


@pytest.mark.parametrize("theta", [0.0, 0.7])
def test_half_plane_boundary_conditions(theta):
    x = -np.linspace(0.05, 5.0, 30)
    for zs in (1e-14, -1e-14):  # just above and below the screen
        assert np.max(np.abs(S.half_plane(K, x, np.full_like(x, zs), "TE", theta))) < 1e-12
    h = 1e-4
    for sgn in (1, -1):  # dU/dz on the screen by a one-sided 4th-order difference from each face
        c = np.array([-25, 48, -36, 16, -3]) / 12.0
        d = sum(cc * S.half_plane(K, x, np.full_like(x, sgn * (j * h + 1e-15)), "TM", theta)
                for j, cc in enumerate(c)) / (sgn * h)
        assert np.max(np.abs(d)) / K < 1e-6
    # negative control: the TE combination with the + sign (Neumann's) does not vanish on the screen
    phi0 = 0.5 * math.pi - theta
    rho = np.abs(x)

    def U(psi):
        return np.exp(-1j * K * rho * np.cos(psi)) * S._fresnel_F(-np.sqrt(2 * K * rho) * np.cos(0.5 * psi))
    assert np.max(np.abs(U(2 * math.pi - phi0) + U(2 * math.pi + phi0))) > 0.1


def test_half_plane_far_limits_edge_wave_and_shadow_boundary():
    theta = 0.3
    phi0 = 0.5 * math.pi - theta
    for pol in ("TE", "TM"):
        res = []
        for kr in (100.0, 1000.0):
            r = kr / K
            phis = np.array([0.5, 1.0, 2.6, 4.0, 5.5])  # Sommerfeld angles away from the shadow boundaries
            phis = phis[(np.abs(phis - (phi0 + math.pi)) > 0.4) & (np.abs(phis - (math.pi - phi0)) > 0.4)]
            x, z = -r * np.cos(phis), -r * np.sin(phis)
            u = S.half_plane(K, x, z, pol, theta)
            geo = S.half_plane_geometric(K, x, z, pol, theta)
            edge = S.half_plane_edge_wave(K, x, z, pol, theta)
            res.append(np.max(np.abs(u - geo - edge)))
            if kr == 1000.0:  # the edge wave is the leading correction to geometric optics
                assert np.all(np.abs(u - geo - edge) < 0.1 * np.abs(edge))
        assert res[1] < res[0] / 20  # O((k r)^(-3/2)): a factor 31.6 per decade
    # on the shadow boundary the incident wave is halved: |U| = |F(0)| = 1/2 (far from the edge, the image term small)
    r = 2000.0 / K
    ang = phi0 + math.pi  # Sommerfeld angle of the shadow boundary
    u = S.half_plane(K, -r * math.cos(ang), -r * math.sin(ang), "TM", theta)
    assert abs(abs(u) - 0.5) < 0.01
    assert abs(abs(S.half_plane_geometric(K, -r * math.cos(ang - 0.01), -r * math.sin(ang - 0.01), "TM", theta))
               - 0.5) > 0.4  # negative control: geometric optics jumps there


# --- the modal method: convergence, routes, balance, reciprocity -----------------------------------------------------------
def test_modal_convergence_with_modes_and_routes_agree():
    for pol in ("TE", "TM"):
        T = [S.solve(K, [0.0], [1.3], 0.5, pol, modes=M).transmission() for M in (16, 32, 64, 128)]
        d = np.abs(np.diff(T))
        # algebraic convergence (the field is singular at the screen's right-angle corners): measured factors 2.0-2.6
        # per doubling of M (~M^-1.3), relative change 8e-5 (TE) and 4e-4 (TM) from 64 to 128 modes
        assert d[0] / d[1] > 1.8 and d[1] / d[2] > 1.8 and d[2] < 5e-4 * T[-1]
        conv = S.convergence(K, [0.0], [1.3], 0.5, pol, modes=(16, 32, 64))
        assert conv[1][2] < 2e-3
    # the operator by the correlation route and by the direct graded double quadrature (independent quadratures)
    for pol in ("TE", "TM"):
        bases = [S._Basis("modal", pol, S._Slit(c, w), 10) for c, w in ((-0.9, 1.1), (0.8, 0.6))]
        A = S._operator(K, pol, bases)
        B = S._operator(K, pol, bases, route="direct")
        assert np.max(np.abs(A - B)) / np.max(np.abs(A)) < 1e-10


def test_edge_basis_converges_exponentially_and_modal_thin_limit_approaches_it():
    for pol in ("TE", "TM"):
        T = [S.solve(K, [0.0], [2.0], 0.0, pol, modes=M, method="edge").transmission() for M in (8, 16, 24)]
        assert abs(T[2] - T[1]) < 1e-10 * T[2]
        m16, m32 = (S.solve(K, [0.0], [0.7], 0.0, pol, modes=M, method="modal").transmission() for M in (16, 32))
        e = S.solve(K, [0.0], [0.7], 0.0, pol).transmission()
        assert abs(m32 - e) < abs(m16 - e) / 1.7  # ~1/M: the waveguide modes miss the thin edge's singularity
        assert abs(2 * m32 - m16 - e) < 1e-3 * e  # Richardson in 1/M


@pytest.mark.parametrize("cfg", [dict(t=0.0, theta=0.4), dict(t=0.35, theta=0.0), dict(t=0.35, theta=-0.6)])
@pytest.mark.parametrize("pol", ["TE", "TM"])
def test_power_balance_optical_theorem(cfg, pol):
    sol = S.solve(K, [-1.5, 0.1, 1.4], [0.6, 1.1, 0.3], cfg["t"], pol, theta=cfg["theta"])
    b = sol.power_balance()
    assert abs(b["rel"]) < 1e-10
    if "P_modes" in b:
        assert abs(b["rel_modes"]) < 1e-10
    assert b["P_t"] > 0 and b["P_b"] > 0


@pytest.mark.parametrize("pol", ["TE", "TM"])
@pytest.mark.parametrize("t", [0.0, 0.4])
def test_reciprocity(pol, t):
    """k_z(q2) T(-q2; q1) = k_z(q1) T(-q1; q2) (Green's theorem with the screen's mirror symmetry)."""
    c, w = [-0.9, 0.5], [0.8, 0.45]
    th1, th2 = 0.25, -0.55
    q1, q2 = K * math.sin(th1), K * math.sin(th2)
    s1 = S.solve(K, c, w, t, pol, theta=th1)
    s2 = S.solve(K, c, w, t, pol, theta=th2)
    lhs = K * math.cos(th2) * s1.spectrum(np.array([-q2]))[0]
    rhs = K * math.cos(th1) * s2.spectrum(np.array([-q1]))[0]
    assert abs(lhs - rhs) < 1e-9 * abs(lhs)
    # negative control: without the k_z factors the two differ
    assert abs(s1.spectrum(np.array([-q2]))[0] - s2.spectrum(np.array([-q1]))[0]) > 1e-3 * abs(lhs)


# --- limits ----------------------------------------------------------------------------------------------------------------
def test_wide_slit_limit_transmission_and_far_field():
    for pol in ("TE", "TM"):
        dev = []
        ff = []
        for w in (4.0, 8.0, 16.0):
            sol = S.solve(K, [0.0], [w], 0.0, pol)
            dev.append(abs(sol.transmission() - 1))
            ph = np.linspace(-0.6 / w, 0.6 / w, 41)  # the main lobe
            fv, fk = sol.far_field(ph), KI.plane_wave_far_field(K, [0.0], [w], ph)
            ff.append(np.max(np.abs(np.abs(fv) - np.abs(fk))) / np.max(np.abs(fk)))
        assert all(dv < 1 / (K * w) for dv, w in zip(dev, (4.0, 8.0, 16.0)))  # O(1/(k w)), oscillating with w
        assert ff[2] < ff[0] and ff[2] < 1e-2
    assert abs(KI.plane_wave_transmission(K, [0.0], [16.0]) - 1) < 1e-2


def test_narrow_thin_slit_rayleigh_limits():
    for pol in ("TE", "TM"):
        errs = []
        for kw in (0.05, 0.02):
            T = S.solve(K, [0.0], [kw / K], 0.0, pol).transmission()
            errs.append(abs(T / S.rayleigh_narrow_transmission(K, kw / K, pol) - 1))
        assert errs[1] < errs[0] and errs[1] < 1e-3
    # negative control: Rayleigh's TE law applied to TM is off by orders of magnitude
    assert S.solve(K, [0.0], [0.05 / K], 0.0, "TM").transmission() > 1e4 * S.rayleigh_narrow_transmission(K, 0.05 / K, "TE")


def test_te_cutoff_below_half_wavelength_in_a_thick_screen():
    w = 0.3
    T = [S.solve(K, [0.0], [w], d, "TE", modes=8).transmission() for d in (0.5, 0.75, 1.0)]
    slope = math.log(T[2] / T[1]) / 0.25
    beta1 = math.sqrt((math.pi / w) ** 2 - K * K)
    assert slope == pytest.approx(-2 * beta1, rel=1e-6)
    assert S.solve(K, [0.0], [w], 1.0, "TM", modes=8).transmission() > 1e5 * T[2]  # TM's TEM mode has no cut-off


def _peak(w, lo, hi):
    r = optimize.minimize_scalar(lambda d: -S.solve(K, [0.0], [w], d, "TM", modes=8).transmission(),
                                 bounds=(lo, hi), method="bounded", options={"xatol": 1e-6})
    return -r.fun, r.x


def _circuit(w, d):
    """Harrington & Auckland's equivalent circuit, RADC-TR-79-257 eqs. (8-4), (8-7), (8-8) (lambda0 = 1, exp(j w t))."""
    z = 1 / (w * (math.pi - 2j * math.log(1.781 * K * w / 8)))
    Z = -1 / (2 / z * math.cos(K * d) + 1j * (1 + z ** -2) * math.sin(K * d))
    return 4 * abs(Z) ** 2 * (1 / z).real


def test_tm_resonance_of_a_narrow_thick_slit():
    """TM through the fundamental (TEM) mode: Fabry–Pérot-like peaks whose height approaches lambda/(pi w) (Auckland &
    Harrington, RADC-TR-79-257, p. 116: "These peaks approach a value of 1/wπ for small w"; Holley & Schnitzer 2018,
    eqs. (12), (32)-(33): eta ~ h^-1 Omega |A|^2 -> 1/(pi m h) at Omega = m pi), below m lambda/2 by the aperture end
    correction (Holley & Schnitzer eq. (34); Takakura's shift through their eq. (35) — not the height: his abstract
    reports peaks of "very low magnitude", another normalisation; review B8 C14)."""
    for w in (0.02, 0.05):
        Tp, dp = _peak(w, 0.3, 0.5)
        assert abs(Tp * math.pi * w - 1) < 0.15 * w  # measured 8e-4 (w = 0.02), 5e-3 (0.05)
        h = w / (2 * dp)  # Holley & Schnitzer eq. (34), m = 1: Delta f / f = (4h/pi)(ln h + ln 2 + gamma - 1)
        d_hs = 0.5 * (1 + 4 * h / math.pi * (math.log(h) + math.log(2) + S.EULER_GAMMA - 1))
        d_tk = 0.5 * (1 + 4 * h / math.pi * (math.log(h) + math.log(math.pi) - 1.5))  # Takakura via their eq. (35)
        if w == 0.02:
            assert abs(dp - d_hs) < 0.15 * (0.5 - d_hs) and abs(dp - d_hs) < abs(dp - d_tk)
    # the equivalent circuit (valid for k w << 1) at w = 0.02 lambda, off and on resonance
    w = 0.02
    for d in (0.1, 0.25, 0.6):
        T = S.solve(K, [0.0], [w], d, "TM", modes=8).transmission()
        assert T / _circuit(w, d) == pytest.approx(1, abs=0.015)
    # Qi et al. 2010, eq. (22): fit of PEC modal peaks T0(s) = 0.0096 + 0.3183 s, s = lambda/w, s = 55..260. At 5e-3
    # this resolves only the slope 1/pi: the constant 0.0096 is 5e-4 (s = 55) and 3e-4 (s = 100) of the peak, and the
    # slope's last digit already 1.6e-4 — a third published modal computation, adding nothing beyond Harrington &
    # Auckland and Holley & Schnitzer above (review B8 C16)
    for s in (55.0, 100.0):
        Tp, _ = _peak(1 / s, 0.42, 0.5)
        assert Tp / (0.0096 + 0.3183 * s) == pytest.approx(1, abs=5e-3)


# --- the thin slit: an independent Galerkin route and a published table ----------------------------------------------------
def _hat_spectral_T(w, N):
    """TE thin slit by piecewise-linear hats and the SPECTRAL form of the operator (propagating part in the angle,
    evanescent part in q = k cosh u): an independent route to the same integral equation."""
    b = w / 2
    xs = np.linspace(-b, b, N + 2)
    h = xs[1] - xs[0]
    nodes = xs[1:-1]
    xg, wg = np.polynomial.legendre.leggauss(64)

    def gl(a, bb, n):
        e = np.linspace(a, bb, n + 1)
        lo, hi = e[:-1, None], e[1:, None]
        return (0.5 * (hi - lo) * xg + 0.5 * (hi + lo)).ravel(), (0.5 * (hi - lo) * wg + 0 * lo).ravel()

    def ft(q):
        return h * np.sinc(q[None, :] * h / (2 * np.pi)) ** 2 * np.exp(-1j * np.outer(nodes, q))
    th, wt = gl(-np.pi / 2, np.pi / 2, 40)
    F = ft(K * np.sin(th))
    Y = (F.conj() * (K * K * np.cos(th) ** 2 * wt)) @ F.T / (2 * np.pi)
    u, wu = gl(0, math.acosh(4000 / (K * h)), 4000)
    q = K * np.cosh(u)
    for sg in (1, -1):
        F = ft(sg * q)
        Y = Y + (F.conj() * (1j * K * K * np.sinh(u) ** 2 * wu)) @ F.T / (2 * np.pi)
    c = np.linalg.solve(Y, K * ft(np.array([0.0]))[:, 0].conj())
    Tq = (c @ ft(K * np.sin(th))) / (2 * np.pi)
    return 2 * np.pi * K * np.sum(wt * np.cos(th) ** 2 * np.abs(Tq) ** 2) / w


def test_thin_te_slit_against_an_independent_hat_basis_spectral_galerkin():
    for kw in (1.6, 4.4):
        T40, T80 = _hat_spectral_T(kw / K, 40), _hat_spectral_T(kw / K, 80)
        extrap = 2 * T80 - T40  # O(1/N) in this basis (measured)
        T = S.solve(K, [0.0], [kw / K], 0.0, "TE").transmission()
        assert abs(T - extrap) < 1e-3 * T
        assert abs(T - T40) > 3 * abs(T - extrap)  # the extrapolation is what agrees


# the independent FDFD of review B8 (reviews/archive/2026-11-04_internal_B8-charges-slit/s03_fdfd_thin_slit.py: 5-point
# Helmholtz, PML, the zero-thickness screen between grid rows, exact discrete flux; nothing of the engine), reproduced
# in its processing: T at N = 8, 16, 32, 64 cells per half-width, eta = k w / 2
FDFD = {("TE", 0.8): (0.316260, 0.287396, 0.273743, 0.267104), ("TE", 1.0): (0.648003, 0.595339, 0.570029, 0.557630),
        ("TE", 1.5): (1.263089, 1.223859, 1.203563, 1.193205), ("TE", 2.0): (1.213459, 1.199500, 1.192052, 1.188199),
        ("TM", 0.8): (0.975540, 0.994925, 1.004615, 1.009461), ("TM", 1.5): (0.938038, 0.960353, 0.971482, 0.977050)}
LIBELO_BOMBARDT = {0.8: 0.2923, 1.0: 0.6012, 1.5: 1.2307, 2.0: 1.2061, 3.0: 1.0001, 3.6: 0.9490, 4.8: 1.0699,
                   5.6: 1.0363}  # NOLTR 70-58, Table I (E along the slot)


def test_thin_slit_against_an_independent_fdfd_and_the_libelo_bombardt_table():
    """Review B8 C13: the reference is the independent FDFD, extrapolated by Richardson with its observed order p
    (0.95-1.04, first order: the grid does not resolve the edge singularity); its uncertainty is taken as the spread
    between the order-p and the order-1 extrapolations (the true order lies between, about 1), times 1.5, plus 3e-5 for
    the six printed digits of the levels. The Libelo–Bombardt table is kept as a known-high reference: it lies 10-12 %
    above at eta <= 1, more than its 'about 3% difference from the other results' (their p. 29), and its printed
    eq. (130)-(132) carry a factor 1/2 (sources file)."""
    for (pol, eta), lv in FDFD.items():
        d1, d2 = lv[2] - lv[1], lv[3] - lv[2]
        p = math.log(d1 / d2) / math.log(2)
        Tp, T1 = lv[3] + d2 / (2 ** p - 1), lv[3] + d2
        tol = 1.5 * abs(Tp - T1) + 3e-5 * Tp
        T = S.solve(K, [0.0], [2 * eta / K], 0.0, pol).transmission()
        assert abs(T - Tp) < tol, (pol, eta, T, Tp, tol)
        assert tol < 3e-3 * Tp  # informative: ten times below the table's own "about 3%" and its 10-12 % deviations
        if pol == "TE" and eta <= 1.0:
            assert LIBELO_BOMBARDT[eta] / Tp - 1 > 0.09  # negative control: the table would fail by 10-12 %
    for eta, ref in LIBELO_BOMBARDT.items():  # documentation of the table: high everywhere (+1.5 % to +12.2 %)
        T = S.solve(K, [0.0], [2 * eta / K], 0.0, "TE").transmission()
        assert 0.01 < ref / T - 1 < 0.13, (eta, ref, T)


# --- the truncation error in the number of modes (review B8 C6, C7) ---------------------------------------------------
# Richardson limits from 2, 4 and 8 times the default count (processing of review B8, p02_slit_convergence; the same
# digits as the review's s02): the slit of 1.3 lambda in a screen of 0.5 lambda
T_LIMIT = {"TE": 0.85812062, "TM": 0.98232870}


def test_truncated_solution_is_a_fresh_solve_with_fewer_modes():
    for pol in ("TE", "TM"):
        for t, meth in ((0.5, "modal"), (0.0, "edge")):
            s = S.solve(K, [-1.0, 1.2], [1.3, 0.9], t, pol, modes=24, method=meth)
            a = s.truncated(17)
            b = S.solve(K, [-1.0, 1.2], [1.3, 0.9], t, pol, modes=17, method=meth)
            ph = np.linspace(-1.4, 1.4, 101)
            assert abs(a.transmission() / b.transmission() - 1) < 1e-12
            assert np.max(np.abs(a.far_field(ph) - b.far_field(ph))) < 1e-12 * np.max(np.abs(b.far_field(ph)))
            assert abs(a.power_balance()["rel"]) < 1e-10


def test_error_estimate_bounds_the_true_truncation_error():
    """The estimate from sub-blocks (M/2, M/sqrt 2, M, Richardson with the observed order clamped to [0.5, 1]) lies
    above the true error of T against the Richardson limit from 2M-8M, by 1.4-1.7 times here (measured); negative
    control: the change T(1.25 M)/T(M) - 1 that v02 showed before understates it 4-5 times (review B8 C6)."""
    for pol in ("TE", "TM"):
        sol = S.solve(K, [0.0], [1.3], 0.5, pol)
        true = abs(sol.transmission() / T_LIMIT[pol] - 1)
        est = sol.error_estimate()
        assert est["kind"] == "richardson" and true < est["T"] < 4 * true, (pol, true, est)
        M = sol.modes[0]
        shown = abs(S.solve(K, [0.0], [1.3], 0.5, pol, modes=M + max(4, math.ceil(M / 4))).transmission()
                    / sol.transmission() - 1)
        assert shown < true / 3
        # a quantity of the caller's (the flux on a few screen points) is estimated the same way
        xs = np.linspace(-3, 3, 7)
        q = sol.error_estimate(quantity=lambda s_: s_.flux_z(xs, np.full(7, 0.5 + 20.0)))["quantity"]
        assert 0 < q < 0.05


def test_thin_screen_uses_the_edge_basis_up_to_kw_140():
    """Review B8 C7: beyond k w = 40 'auto' took the waveguide modes for a thin screen, 0.2-0.5 % low — as large as
    the vector-scalar differences v02 shows there. Now the edge basis up to k w = 140; its estimate is tiny, while the
    waveguide modes at the same k w (negative control) are off by more than 2e-3 and their estimate says so."""
    for pol in ("TE", "TM"):
        e = S.solve(K, [0.0], [60.0 / K], 0.0, pol)
        assert e.method == "edge" and S.solve(K, [0.0], [141.0 / K], 0.0, pol, modes=4).method == "modal"
        assert e.error_estimate()["T"] < 1e-5
        m = S.solve(K, [0.0], [60.0 / K], 0.0, pol, method="modal")
        true = abs(m.transmission() / e.transmission() - 1)
        assert true > 2e-3 and m.error_estimate()["T"] > true


# --- fields --------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("pol", ["TE", "TM"])
def test_fields_continuity_conductor_and_helmholtz(pol):
    sol = S.solve(K, [-0.6, 0.7], [0.8, 0.5], 0.4, pol, theta=0.3, modes=20)
    xs = np.array([-0.6, -0.45, 0.7, 0.8])
    eps = 1e-7
    for z0, z1 in ((0.4, 0.4 + eps), (0.0, -eps)):
        a, b = sol.field(xs, np.full(4, z0)), sol.field(xs, np.full(4, z1))
        i = 0 if pol == "TE" else 2  # the component the method matches exactly: E_y (TE), E_x ~ du/dz (TM)
        assert np.max(np.abs(a[i] - b[i])) < 1e-4 * np.max(np.abs(a[i]))
    xc = np.array([-1.5, 0.1, 2.0])
    for z in (0.4 + 1e-9, -1e-9):
        u, ux, uz = sol.field(xc, np.full(3, z))
        assert np.max(np.abs(u if pol == "TE" else uz)) < 1e-6 * K
    # Helmholtz above and below (the Rayleigh–Sommerfeld kernels)
    x = np.array([-1.0, 0.3, 2.2])
    for z in (1.3, -0.8):
        f = lambda xx, zz: sol.field(xx, zz, deriv=False)[0]  # noqa: E731
        res = np.abs(_lap(f, x, np.full(3, z), 3e-3) + K * K * f(x, np.full(3, z))) / (K * K * np.abs(f(x, np.full(3, z))))
        assert np.max(res) < 1e-6


@pytest.mark.parametrize("pol", ["TE", "TM"])
def test_field_by_quadrature_agrees_with_the_far_field_of_the_spectrum(pol):
    sol = S.solve(K, [-0.6, 0.7], [0.8, 0.5], 0.4, pol, theta=0.2)
    errs = []
    for kr in (2e3, 2e4):
        r = kr / K
        ph = np.array([-0.8, 0.0, 0.5])
        xx, zz = r * np.sin(ph), sol.thickness + r * np.cos(ph)
        u = sol.field(xx, zz, deriv=False)[0]
        f = sol.far_field(ph) * np.exp(1j * K * r) / math.sqrt(r)
        errs.append(np.max(np.abs(u - f)) / np.max(np.abs(f)))
    assert errs[1] < errs[0] / 5 and errs[1] < 2e-3  # O(1/(k r)) and the slits' extent
    # the per-slit decomposition adds up to the scattered field
    x = np.linspace(-3, 3, 7)
    parts = sol.per_slit(x, np.full(7, 2.0))
    assert np.max(np.abs(parts.sum(axis=0) - sol.field(x, sol.thickness + 2.0, deriv=False)[0])) < 1e-12 * \
        np.max(np.abs(parts))


# --- the scalar Kirchhoff result (lfphys.theories.approx.kirchhoff; moved out of the core, review B8 C10) --------------
def test_kirchhoff_routes_agree():
    x = np.linspace(-3, 3, 9)
    uk = KI.plane_wave_field(K, [0.0], [0.8], x, np.full(9, 2.0))
    ref = KI.slit_fields(x, 2.0, K, [0.0], 0.8)[0]
    assert np.max(np.abs(uk - ref)) < 1e-12 * np.max(np.abs(ref))
    u, ux, uz = KI.plane_wave_field(K, [0.0], [0.8], x, np.full(9, 2.0), deriv=True)
    h = 1e-4
    fd = (KI.plane_wave_field(K, [0.0], [0.8], x, np.full(9, 2.0 + h)) -
          KI.plane_wave_field(K, [0.0], [0.8], x, np.full(9, 2.0 - h))) / (2 * h)
    assert np.max(np.abs(uz - fd)) < 1e-6 * np.max(np.abs(uz))
    # the far field and the transmission against the field at a large distance and the flux through a line
    r = 2e4 / K
    ph = np.array([-0.5, 0.0, 0.3])
    f = KI.plane_wave_far_field(K, [0.0], [0.8], ph) * np.exp(1j * K * r) / math.sqrt(r)
    u = KI.plane_wave_field(K, [0.0], [0.8], r * np.sin(ph), r * np.cos(ph))
    assert np.max(np.abs(u - f)) < 3e-3 * np.max(np.abs(f))
    xs = np.linspace(-60, 60, 24001)
    u, _, uz = KI.plane_wave_field(K, [-0.7, 0.9], [0.8, 0.5], xs, np.full(xs.size, 3.0), deriv=True)
    flux = np.sum(np.imag(np.conj(u) * uz)) / K * (xs[1] - xs[0]) / 1.3
    assert flux == pytest.approx(KI.plane_wave_transmission(K, [-0.7, 0.9], [0.8, 0.5]), rel=2e-2)


def test_comparison_with_kirchhoff_for_v02():
    x = np.linspace(-40, 40, 161)
    c_narrow = KI.compare_vector(K, [-1.5, 1.5], [0.4, 0.4], 0.3, "TE", x, 100.0)
    assert c_narrow["T_vector"] < 0.2 * c_narrow["T_scalar"]  # below the TE cut-off (w < lambda/2) in a thick screen
    c_wide = KI.compare_vector(K, [-10, 10], [6.0, 6.0], 0.0, "TM", x, 400.0)
    assert abs(c_wide["T_vector"] / c_wide["T_scalar"] - 1) < 0.03
    assert np.max(np.abs(c_wide["difference"])) < 0.05 * np.max(c_wide["I_scalar"])
    tw = KI.transmission_vs_width(K, [0.25, 1.0, 4.0], thickness=0.3)
    assert tw["TE"][0] < 0.1 < tw["TM"][0] and abs(tw["TE"][2] - 1) < 0.05 and abs(tw["TM"][2] - 1) < 0.05


def test_the_approximation_lives_outside_the_core():
    """Review B8 C10: the core module keeps the exact law only; the approximation names it as its conflict."""
    assert not [n for n in dir(S) if n.startswith("kirchhoff") or n in ("compare_kirchhoff", "transmission_vs_width")]
    assert any("lfphys.core.em.slit" in c for c in KI.ABOUT["conflicts"])
    assert "нужна векторная теория" not in KI.ABOUT["validity"] and "core.em.slit" in KI.ABOUT["validity"]
