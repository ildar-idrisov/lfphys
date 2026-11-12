# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P7: Kerr null geodesics in closed form (lfphys.core.gravity.kerr_null) against independent routes.

Routes used as references:
* mpmath at 30 digits: the radial roots by ``polyroots``; the Mino-time integrals int dr/sqrt(R) and
  int dtheta/sqrt(Theta) by tanh-sinh quadrature (``mp.quad``, which integrates the square-root end points of the
  turning points exactly in the limit), their inversion by bisection. No elliptic function, no Ferrari formula.
* the Hamiltonian geodesic equations in Boyer-Lindquist coordinates (``kerr_geodesics.integrate``, DOP853): no
  separation constant except E and L; Q and H are monitored.
* closed forms of other papers: Bardeen's lambda, eta of the critical curve; Johnson et al. 2020 Eqs. 4, 6, 8, 29.

Tolerances. The closed form takes (lambda, eta) and a Mino time tau and returns r through roots, elliptic integrals
and Jacobi functions, each accurate to <= 64 u relative (test_elliptic: R_F 32 u, F 64 u, sn 128 u (1 + |X|)
absolute). The tolerance of a closed-form value v is the propagation of a 64 u relative error in each input and in v
itself with v's own sensitivities, computed by central differences of the closed form (relative step 1e-6):
tol = 64 u (|lambda dv/dlambda| + |eta dv/deta| + |tau dv/dtau| + |v|); plus 128 u (1 + |X|) |dv/dsn| for the
Jacobi function, folded in by doubling the 64 u. The mpmath references are exact to ~1e-25 in comparison.
"""

import math

import mpmath as mp
import numpy as np
import pytest

from lfphys.core.gravity import kerr, kerr_geodesics as KG, kerr_null as KN

U = 2.0 ** -53
B64 = 128 * U  # the budget per input, doubled for the Jacobi functions (module docstring)


# --- references in mpmath ------------------------------------------------------------------------------------------
def mp_roots(lam, eta, chi):
    a = mp.mpf(chi)
    lam, eta = mp.mpf(lam), mp.mpf(eta)
    A = a * a - eta - lam * lam
    B = 2 * (eta + (lam - a) ** 2)
    C = -a * a * eta
    return sorted(mp.polyroots([1, 0, A, B, C], maxsteps=200, extraprec=200), key=lambda z: (mp.re(z), mp.im(z)))


def mp_R(r, lam, eta, chi):
    a = mp.mpf(chi)
    return (r * r + a * a - a * lam) ** 2 - (r * r - 2 * r + a * a) * (eta + (lam - a) ** 2)


def mp_tau_to(r_s, lam, eta, chi, after_turn=False, r4=None):
    """Mino time from infinity down to r_s (or down to r4 and back up to r_s)."""
    lam, eta = mp.mpf(lam), mp.mpf(eta)
    a = mp.mpf(chi)
    A = a * a - eta - lam * lam
    B = 2 * (eta + (lam - a) ** 2)
    C = -a * a * eta

    def f(u):  # u^4 R(1/u) = 1 + A u^2 + B u^3 + C u^4
        return 1 / mp.sqrt(1 + A * u * u + B * u ** 3 + C * u ** 4)
    # (mp.re: rounding at the turning point u4 can leave an imaginary part ~1e-16 of the 30-digit integrand)
    if not after_turn:
        return mp.re(mp.quad(f, [0, 1 / mp.mpf(r_s)]))
    u4 = 1 / r4
    return mp.re(2 * mp.quad(f, [0, u4]) - mp.quad(f, [0, 1 / mp.mpf(r_s)]))


def mp_r_at(tau, lam, eta, chi, guess):
    """r at Mino time tau after leaving infinity: Newton's method on the mpmath integral tau(r) (dtau/dr = -+
    1/sqrt(R) before / after the turning point), started from ``guess`` and iterated until tau(r) matches to 1e-24
    (the start only decides how fast it converges, not where)."""
    rr = mp_roots(lam, eta, chi)
    rp = 1 + mp.sqrt(1 - mp.mpf(chi) ** 2)
    real = [mp.re(z) for z in rr if abs(mp.im(z)) < mp.mpf(10) ** -20]
    r4 = max(real) if real else None
    scatter = r4 is not None and r4 > rp
    tau = mp.mpf(tau)
    after = False
    if scatter:
        after = tau > mp_tau_to(r4, lam, eta, chi)
    lam_m, eta_m = mp.mpf(lam), mp.mpf(eta)
    r = mp.mpf(guess)
    for _ in range(30):
        f = mp_tau_to(r, lam, eta, chi, after, r4) - tau
        if abs(f) < mp.mpf(10) ** -24:
            return r
        d = (1 if after else -1) / mp.sqrt(mp_R(r, lam_m, eta_m, chi))
        r_new = r - f / d
        if scatter and r_new <= r4:
            r_new = (r + r4) / 2
        r = r_new
    raise AssertionError("Newton did not converge")


def mp_tau_n(lam, eta, chi, theta_o, beta, n):
    """Mino time of the n-th equatorial crossing by quadrature over the polar angle (cos theta = sqrt(u+) sin psi:
    dtheta/sqrt(Theta) = dpsi/sqrt(A_m + a^2 u_+ sin^2 psi))."""
    a = mp.mpf(chi)
    lam, eta = mp.mpf(lam), mp.mpf(eta)
    h = (eta + lam * lam - a * a) / 2
    Am = h + mp.sqrt(h * h + a * a * eta)
    up = eta / Am
    f = lambda p: 1 / mp.sqrt(Am + a * a * up * mp.sin(p) ** 2)  # noqa: E731
    psio = mp.asin(mp.cos(mp.mpf(theta_o)) / mp.sqrt(up))
    half = mp.quad(f, [-mp.pi / 2, mp.pi / 2])
    first = mp.quad(f, [0, psio]) if beta < 0 else mp.quad(f, [psio, mp.pi / 2]) + mp.quad(f, [0, mp.pi / 2])
    return first + n * half


# --- helpers -------------------------------------------------------------------------------------------------------
def closed_tol(fn, lam, eta, tau):
    """64u-per-input propagation of the closed form v = fn(lam, eta, tau) (module docstring)."""
    v = fn(lam, eta, tau)
    tot = abs(v)
    for i, x in enumerate((lam, eta, tau)):
        h = 1e-6 * max(abs(x), 1e-3)
        args_p = [lam, eta, tau]
        args_m = [lam, eta, tau]
        args_p[i] = x + h
        args_m[i] = x - h
        tot += abs(x) * abs(fn(*args_p) - fn(*args_m)) / (2 * h)
    return B64 * tot


SCREEN_POINTS = [  # (chi, theta_o deg, alpha, beta): all four radial cases, both signs of beta, n up to 2
    (0.9, 60.0, 2.0, 3.0), (0.9, 60.0, -3.0, 4.5), (0.9, 60.0, 5.5, -1.0), (0.9, 60.0, 6.2, 0.5),
    (0.9, 60.0, -4.0, -2.6), (0.9, 60.0, 7.0, -6.0), (0.5, 17.0, 5.6, 1.0), (0.5, 17.0, -5.2, -1.4),
    (0.99, 85.0, -2.5, 5.2), (0.99, 85.0, 4.1, -4.4), (0.3, 120.0, 3.0, -4.6), (0.3, 120.0, -5.4, 0.4),
    # near the axis (review B5-K13: the arcsin of 1 - O(theta_o^2) cost u/theta_o in tau_n before the atan2 form)
    (0.5, 1e-4, 5.6, 1.1), (0.5, 1e-4, -0.73, -5.6), (0.94, 0.01, -3.0, 4.2), (0.94, 179.99, 2.0, 4.8),
]


@pytest.fixture(autouse=True)
def _dps():
    with mp.workdps(30):
        yield


# --- the screen ----------------------------------------------------------------------------------------------------
def test_screen_constants_round_trip():
    rng = np.random.default_rng(1)
    for chi, th in ((0.0, 0.3), (0.7, 1.0), (0.99, 1.5)):
        al, be = rng.uniform(-8, 8, 200), rng.uniform(-8, 8, 200)
        lam, eta = KN.screen_to_constants(al, be, th, chi)
        a2, b2 = KN.constants_to_screen(lam, eta, th, chi, np.sign(be))
        assert np.allclose(a2, al, rtol=4 * U, atol=0) and np.allclose(b2, be, rtol=64 * U, atol=64 * U * 64)


# --- roots ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("chi", [0.0, 0.3, 0.9, 0.999])
def test_radial_roots_and_cases_against_mpmath(chi):
    rng = np.random.default_rng(int(chi * 1000) + 5)
    lam = rng.uniform(-8, 8, 60)
    eta = rng.uniform(-1, 40, 60)
    ok = eta >= -(np.abs(lam) - chi) ** 2 * (np.abs(lam) <= chi) - 1e-12  # the allowed region (GL-a Eq. 24)
    ok &= ~((np.abs(lam) > chi) & (eta < 0))
    lam, eta = lam[ok], eta[ok]
    ro = KN.radial_roots(lam, eta, chi)
    rp = 1 + math.sqrt(1 - chi * chi)
    seen = set()
    for i in range(lam.size):
        ref = mp_roots(lam[i], eta[i], chi)
        real = sorted(float(mp.re(z)) for z in ref if abs(mp.im(z)) < 1e-20)
        A = chi * chi - eta[i] - lam[i] ** 2
        B = 2 * (eta[i] + (lam[i] - chi) ** 2)
        C = -chi * chi * eta[i]
        case = int(ro["case"][i])
        seen.add(case)
        n_real = {1: 4, 2: 4, 3: 2, 4: 0}[case]
        assert len(real) == n_real
        if n_real == 4:
            assert (real[3] > rp) == (case == KN.CASE_I)
        for k, rt in zip(("r1", "r2", "r3", "r4")[:n_real], real):
            got = float(ro[k][i])
            # the conditioning of the root (a 64u relative perturbation of the coefficients moves it by
            # 64u S(r)/|R'(r)|) plus the absolute round-off of Ferrari's r = +-z +- sqrt(d): 64u (z + sqrt|d|)
            S = rt ** 4 + abs(A) * rt * rt + abs(B) * abs(rt) + abs(C)
            dR = abs(4 * rt ** 3 + 2 * A * rt + B)
            zz = float(ro["z"][i])
            assert abs(got - rt) <= 64 * U * S / dR + 64 * U * (zz + abs(abs(rt) - zz) + abs(rt)), (k, got, rt)
    assert {1, 3} <= seen


def test_polar_roots_satisfy_the_polar_quadratic():
    rng = np.random.default_rng(2)
    for chi in (0.0, 0.5, 0.95):
        lam, eta = rng.uniform(-6, 6, 50), rng.uniform(0.01, 30, 50)
        pol = KN.polar_roots(lam, eta, chi)
        up = pol["u_plus"]
        # (1 - u) Theta = eta + (a^2 - eta - lambda^2) u - a^2 u^2 vanishes at u+
        res = eta + (chi * chi - eta - lam * lam) * up - chi * chi * up * up
        scale = eta + np.abs(chi * chi - eta - lam * lam) * up + chi * chi * up * up
        assert np.all(np.abs(res) <= 16 * U * scale)
        assert np.all((up > 0) & (up <= 1))


# --- the closed-form ray against mpmath quadrature -------------------------------------------------------------------
@pytest.mark.parametrize("pt", SCREEN_POINTS)
def test_screen_crossings_against_quadrature(pt):
    chi, th_deg, al, be = pt
    th = math.radians(th_deg)
    res = KN.trace_back(np.array([al]), np.array([be]), th, chi, n_max=2)
    lam, eta = float(res["lam"][0]), float(res["eta"][0])
    th_n = th if th <= math.pi / 2 else math.pi - th
    be_n = be if th <= math.pi / 2 else -be
    for n in range(3):
        tn = float(res["tau_n"][n][0])
        if math.isnan(tn):
            continue
        ref_t = mp_tau_n(lam, eta, chi, th_n, be_n, n)
        tol_t = closed_tol(lambda l, e, _t, n=n: _tau_of(l, e, chi, th_n, be_n, n), lam, eta, 0.0)
        assert abs(tn - float(ref_t)) <= tol_t, (n, tn, ref_t, tol_t)
        rn = float(res["r_n"][n][0])
        ref_r = float(mp_r_at(ref_t, lam, eta, chi, rn))
        tol = closed_tol(lambda l, e, t: _r_of(l, e, t, chi), lam, eta, tn)
        assert abs(rn - ref_r) <= tol, (n, rn, ref_r, tol)


def _tau_of(lam, eta, chi, th, beta, n):
    pol = KN.polar_roots(np.array([lam]), np.array([eta]), chi)
    from lfphys.core import elliptic as EL
    up, Am, m = float(pol["u_plus"][0]), float(pol["A_m"][0]), float(pol["m"][0])
    Fo = float(EL.ellipf(math.asin(min(1.0, math.cos(th) / math.sqrt(up))), m))
    K = float(EL.ellipk(m))
    H = 1.0 if beta > 0 else 0.0
    return (2 * (n + H) * K - math.copysign(1.0, beta) * Fo) / math.sqrt(Am)


def _r_of(lam, eta, tau, chi):
    ro = KN.radial_roots(np.array([lam]), np.array([eta]), chi)
    rad = KN._Radial(ro, chi)
    I_inf = rad.antiderivative(np.array([math.inf]))
    return float(rad.r_of(rad.X_of(np.array([tau]), I_inf, -1.0))[0])


def test_total_mino_time_against_quadrature():
    for chi, th_deg, al, be in SCREEN_POINTS[:8]:
        th = math.radians(th_deg)
        res = KN.trace_back(np.array([al]), np.array([be]), th, chi)
        lam, eta = float(res["lam"][0]), float(res["eta"][0])
        rp = 1 + math.sqrt(1 - chi * chi)
        if res["captured"][0]:
            ref = mp_tau_to(rp, lam, eta, chi)
        else:
            rr = mp_roots(lam, eta, chi)
            r4 = max(mp.re(z) for z in rr if abs(mp.im(z)) < 1e-20)
            ref = 2 * mp_tau_to(r4, lam, eta, chi)
        tot = float(res["tau_total"][0])
        # an elliptic integral of the first kind (<= 64 u) of roots with backward error 64 u: 512 u covers both
        assert abs(tot - float(ref)) <= 512 * U * tot + 1e-14, (tot, ref)


# --- conservation along a ray and the Hamiltonian route ------------------------------------------------------------
RAYS = [  # chi, lam, eta, r0, theta0 (deg), nu_r, nu_theta
    (0.9, 2.0, 20.0, 12.0, 70.0, -1, 1), (0.9, -4.0, 12.0, 9.0, 70.0, -1, -1), (0.9, 1.0, 27.5, 20.0, 89.0, 1, 1),
    (0.6, 3.5, 8.0, 4.0, 60.0, 1, -1), (0.6, -6.0, 20.0, 30.0, 100.0, -1, 1), (0.95, 0.2, -0.3, 5.0, 30.0, -1, 1),
]


@pytest.mark.parametrize("ray", RAYS)
def test_closed_form_ray_keeps_its_constants_and_matches_the_hamiltonian_route(ray):
    chi, lam, eta, r0, th0, nur, nut = ray
    nr = KN.NullRay(chi, lam, eta, r0, math.radians(th0), nur, nut)
    tend = nr.tau_end()
    rp = KN.horizon(chi)
    # stop well outside the horizon (Delta -> 0 is singular in Boyer-Lindquist time and azimuth)
    taus = np.linspace(0.0, 0.9 * tend if math.isfinite(tend) else 2.0, 9)[1:]
    taus = taus[nr.r(taus) > rp + 0.05]
    path = nr.path(taus, nodes=24)
    # (1) along the closed form: (dr/dtau)^2 = R(r) and (dtheta/dtau)^2 = Theta(theta), i.e. the state (x, p)
    # reconstructed from the closed form has H = 0 and Q/E^2 = eta (E = 1 and L = lambda are its parameters).
    # The derivatives are analytic (sn' = cn dn); the tolerance propagates the 64u-per-input budget of both sides
    # (closed_tol) through the identity, plus the round-off of the potentials (16 u times their absolute terms).
    th0r = math.radians(th0)

    def ray(l, e):
        return KN.NullRay(chi, l, e, r0, th0r, nur, nut)
    a = chi
    for t in taus:
        r, th = float(nr.r(t)), float(nr.theta(t))
        drdt, dthdt = float(nr.drdtau(t)), float(nr.dthetadtau(t))
        R = KN.radial_potential(r, lam, eta, chi)
        Th = float(KN.polar_potential(th, lam, eta, chi))
        dl = r * r - 2 * r + a * a
        w = r * r + a * a - a * lam
        Rp = 4 * r * w - (2 * r - 2) * (eta + (lam - a) ** 2)
        SR = (r * r + a * a + abs(a * lam)) ** 2 + abs(dl) * (abs(eta) + (lam - a) ** 2)
        tol_r = closed_tol(lambda l, e, s: float(ray(l, e).r(s)), lam, eta, t)
        tol_d = closed_tol(lambda l, e, s: float(ray(l, e).drdtau(s)), lam, eta, t)
        assert abs(drdt ** 2 - R) <= 2 * abs(drdt) * tol_d + abs(Rp) * tol_r + 16 * U * SR, (t, drdt ** 2, R)
        c, sn = math.cos(th), math.sin(th)
        STh = abs(eta) + a * a * c * c + lam * lam * c * c / sn ** 2
        dTh = abs(2 * c * sn * (-a * a) + 2 * lam * lam * c / sn ** 3)
        tol_th = closed_tol(lambda l, e, s: float(ray(l, e).theta(s)), lam, eta, t)
        tol_dth = closed_tol(lambda l, e, s: float(ray(l, e).dthetadtau(s)), lam, eta, t)
        assert abs(dthdt ** 2 - Th) <= 2 * abs(dthdt) * tol_dth + dTh * tol_th + 16 * U * STh, (t, dthdt ** 2, Th)
    # (2) the Hamiltonian route from the same initial state; its global error estimated by a second run at a
    # 100 times tighter tolerance (the difference of the two bounds the error of the looser run, x2)
    p0 = KG.null_momentum(r0, math.radians(th0), lam, eta, chi, nur, nut)
    runs = [KG.integrate(chi, [0.0, r0, math.radians(th0), 0.0], p0, float(taus[-1]), rtol=rt, atol=rt * 1e-2,
                         dense=True) for rt in (1e-11, 1e-13)]
    y1 = np.array([runs[0].sol(t) for t in taus])
    y2 = np.array([runs[1].sol(t) for t in taus])
    err = 2 * np.abs(y1 - y2) + 1e-13
    for i, t in enumerate(taus):
        tol_r = err[i, 1] + closed_tol(lambda l, e, s: float(nr.r(s)), lam, eta, t) + 1e-12 * path["r"][i]
        assert abs(y2[i, 1] - path["r"][i]) <= tol_r, (t, y2[i, 1], path["r"][i])
        assert abs(y2[i, 2] - path["theta"][i]) <= err[i, 2] + 1e-11, (t, y2[i, 2], path["theta"][i])
        assert abs(y2[i, 3] - path["phi"][i]) <= err[i, 3] + 1e-10 * (1 + abs(path["phi"][i])), (t, y2[i, 3])
    # (3) conservation along the Hamiltonian route: E, L exactly (cyclic coordinates), Q and H to the integrator's
    # tolerance
    sol = runs[1]
    m2, Q = KG.constants(sol.y[1], sol.y[2], sol.y[4], sol.y[5], sol.E, sol.L, chi, mu2=0.0)
    assert sol.E == 1.0 and sol.L == lam
    assert np.max(np.abs(Q - eta)) <= 1e-9 * (abs(eta) + lam * lam + chi * chi)
    assert np.max(np.abs(m2)) <= 1e-9


def test_screen_rays_match_the_hamiltonian_route_from_far_away():
    """trace_back (rays from infinity) against the Hamiltonian route started at r0 = 1e7 where the ray from infinity
    passes, theta_o - beta/r0 (tests/kerr_routes.py; review B5-K12: started at theta_o the offset beta/r0 forced a
    1e-5 tolerance). Tolerance: the route's error by a second run 100 times tighter (x2), its start error
    sqrt(R(r_n)) (|Theta'(theta_o)|/(4 |beta|) + 1)/r0^2 in Mino time, and the closed form's 128 u per input (alpha,
    beta) with its sensitivities (measured agreement ~1e-11 relative)."""
    from kerr_routes import hamilton_screen_ray
    for chi, th_deg, al, be in SCREEN_POINTS[:8]:
        th = math.radians(th_deg)
        res = KN.trace_back(np.array([al]), np.array([be]), th, chi, n_max=2)
        h = 1e-6
        ra = KN.trace_back(np.array([al + h, al - h]), np.array([be, be]), th, chi, n_max=2)["r_n"]
        rb = KN.trace_back(np.array([al, al]), np.array([be + h, be - h]), th, chi, n_max=2)["r_n"]
        runs = [hamilton_screen_ray(al, be, th, chi, rtol=rt) for rt in (1e-11, 1e-13)]
        ham = runs[1]
        assert ham["captured"] == bool(res["captured"][0])
        lam, eta = ham["lam"], ham["eta"]
        c, s_ = math.cos(th), math.sin(th)
        dtau0 = (abs(-2 * chi * chi * c * s_ + 2 * lam * lam * c / s_ ** 3) / (4 * abs(be)) + 1.0) / 1e7 ** 2
        for n in range(3):
            r_e = float(res["r_n"][n, 0])
            if math.isnan(r_e):
                continue
            y, y1 = ham["cross"][n], runs[0]["cross"][n]
            sens = (abs(al) * abs(ra[n, 0] - ra[n, 1]) + abs(be) * abs(rb[n, 0] - rb[n, 1])) / (2 * h) + r_e
            tol = 2 * abs(y[1] - y1[1]) + math.sqrt(max(KN.radial_potential(r_e, lam, eta, chi), 0.0)) * dtau0 \
                + 128 * U * sens
            assert abs(r_e - y[1]) <= tol, (chi, th_deg, al, be, n, r_e, y[1], tol)


# --- photon shell and critical curve -------------------------------------------------------------------------------
@pytest.mark.parametrize("chi", [0.1, 0.5, 0.9, 0.998])
def test_critical_constants_three_forms_and_double_roots(chi):
    """lambda(r), eta(r) of the spherical photon orbits: (i) in 30-digit arithmetic the engine's form (through
    t = (r - 3)/a), GL-a Eqs. (107, 109), Bardeen's (as quoted by Johannsen 2013b App. Eqs. 3-4) and Johnson et al.
    Eq. (6) agree, and R = R' = 0 there; (ii) the float evaluation is within the a-priori bound gamma_12 times the
    formula evaluated with absolute values (Higham, Sec. 3.1) of its 30-digit value."""
    rm, rpl = KN.photon_shell(chi)
    r = np.linspace(rm, rpl, 21)
    lam, eta = KN.critical_constants(r, chi)
    a = mp.mpf(chi)
    g12 = 12 * U / (1 - 12 * U)
    for i, rf in enumerate(r):
        x = mp.mpf(rf)
        t = (x - 3) / a
        lam_e = a - x * (x * t + 2 * a) / (x - 1)
        eta_e = x ** 3 * (4 - x * t * t) / (x - 1) ** 2
        dl = x * x - 2 * x + a * a
        for lv, ev in ((a + x / a * (x - 2 * dl / (x - 1)), x ** 3 / a ** 2 * (4 * dl / (x - 1) ** 2 - x)),
                       (-(x * x * (x - 3) + a * a * (x + 1)) / (a * (x - 1)),
                        x ** 3 * (4 * a * a - x * (x - 3) ** 2) / (a * a * (x - 1) ** 2)),
                       (((x * x - a * a) - x * dl) / (a * (x - 1)), eta_e)):
            assert abs(lv - lam_e) < mp.mpf(10) ** -24 * (1 + abs(lam_e))
            assert abs(ev - eta_e) < mp.mpf(10) ** -24 * (1 + abs(eta_e)) * 10 ** 4
        R = mp_R(x, lam_e, eta_e, chi)
        Rp = 4 * x * (x * x + a * a - a * lam_e) - (2 * x - 2) * (eta_e + (lam_e - a) ** 2)
        assert abs(R) < mp.mpf(10) ** -22 and abs(Rp) < mp.mpf(10) ** -22
        tf = abs((rf - 3) / chi)
        lam_abs = chi + abs(rf) * (abs(rf) * tf + 2 * chi) / abs(rf - 1)
        eta_abs = rf ** 3 * (4 + rf * tf * tf) / (rf - 1) ** 2
        assert abs(lam[i] - float(lam_e)) <= g12 * lam_abs, (rf, lam[i], lam_e)
        assert abs(eta[i] - float(eta_e)) <= g12 * eta_abs, (rf, eta[i], eta_e)
    # the ends of the shell are the circular equatorial photon orbits (eta = 0) of kerr.photon_orbit
    for rend in (rm, rpl):
        tf = abs((rend - 3) / chi)
        assert abs(KN.critical_constants(np.array([rend]), chi)[1][0]) <= g12 * rend ** 3 * (4 + rend * tf * tf) / (
            rend - 1) ** 2 + 8 * U * rend ** 4 * 64


def test_johnson_polar_turning_points_formula():
    """Johnson et al. 2020 Eq. (4) for u_pm of the bound orbit at r, as printed (checked on the rendered page):
    u_pm = r/(a^2 (r - M)^2) [-r^3 + 3 M^2 r - 2 a^2 M pm 2 sqrt(M Delta (2 r^3 - 3 M r^2 + a^2 M))], against the
    general roots of GL-a Eq. (19) at the critical constants (an independent route through lambda(r), eta(r))."""
    for chi in (0.3, 0.9, 0.998):
        rm, rpl = KN.photon_shell(chi)
        r = np.linspace(rm + 0.02, rpl - 0.02, 9)
        sh = KN.shell_angles(r, chi)
        a = chi
        dl = r * r - 2 * r + a * a
        sq = 2 * np.sqrt(dl * (2 * r ** 3 - 3 * r * r + a * a))
        pre = r / (a * a * (r - 1) ** 2)
        up = pre * (-r ** 3 + 3 * r - 2 * a * a + sq)
        um = pre * (-r ** 3 + 3 * r - 2 * a * a - sq)
        # both sides cancel terms of size pre (r^3 + sq): 64 u of that
        tol = 64 * U * pre * (r ** 3 + 3 * r + 2 * a * a + sq)
        assert np.all(np.abs(up - sh["u_plus"]) <= tol)
        assert np.all(np.abs(um - sh["u_minus"]) <= tol + 64 * U * np.abs(sh["u_minus"]))


def test_lyapunov_exponent_two_routes_and_schwarzschild():
    for chi in (0.01, 0.5, 0.94, 0.998):
        rm, rpl = KN.photon_shell(chi)
        r = np.linspace(rm + 1e-3, rpl - 1e-3, 15)
        g1, g2 = KN.lyapunov(r, chi), KN.lyapunov_second_route(r, chi)
        # both: K (<= 64 u) and square roots of terms computed with the critical constants (cancellation as in
        # test_critical_constants: <= 64 u r^3/a^2 relative to the R'' scale)
        assert np.allclose(g1, g2, rtol=64 * U * (1 + 8 * rpl ** 3 / chi ** 2), atol=0)
    assert np.allclose(KN.lyapunov(np.array([3.0]), 0.0), math.pi)
    # a -> 0: the exponent of the shell tends to pi (Johnson et al. 2020: "For Schwarzschild, gamma = pi")
    assert abs(KN.lyapunov(np.array([3.0 + 1e-6]), 1e-6)[0] - math.pi) < 1e-6


# --- symmetry and the Schwarzschild limit ---------------------------------------------------------------------------
def test_schwarzschild_limit_and_symmetry():
    rng = np.random.default_rng(11)
    al, be = rng.uniform(-9, 9, 3000), rng.uniform(-9, 9, 3000)
    for th in (math.radians(17), math.radians(60), math.radians(90)):
        res = KN.trace_back(al, be, th, 0.0, n_max=2)
        b = np.hypot(al, be)
        away = np.abs(b - math.sqrt(27.0)) > 1e-9
        assert np.all(res["captured"][away] == (b[away] < math.sqrt(27.0)))
        # the image of the equatorial disk is mirror-symmetric under alpha -> -alpha (no rotation)
        res_m = KN.trace_back(-al, be, th, 0.0, n_max=2)
        both = ~np.isnan(res["r_n"]) & ~np.isnan(res_m["r_n"])
        assert np.array_equal(np.isnan(res["r_n"]), np.isnan(res_m["r_n"]))
        assert np.allclose(res["r_n"][both], res_m["r_n"][both], rtol=1e-12)
    cc = KN.critical_curve(0.0, 1.0)
    assert np.allclose(np.hypot(cc["alpha"], cc["beta"]), math.sqrt(27.0), rtol=8 * U)


def test_reflection_symmetry_of_the_screen():
    """theta_o -> pi - theta_o with beta -> -beta is the same set of rays (the equatorial plane is a mirror); an
    edge-on observer sees the disk symmetric in beta; the critical curve is symmetric in beta (GL-b). The two
    computations differ by the rounding of the inclination (fl(pi - fl(145 deg)) != fl(35 deg)), which changes the
    computed lambda and eta by <= 2 ulp: tolerance = closed_tol (128 u per input with the closed form's own
    sensitivities)."""
    rng = np.random.default_rng(4)
    al, be = rng.uniform(-8, 8, 120), rng.uniform(-8, 8, 120)
    for chi in (0.5, 0.95):
        th1, th2 = math.radians(35), math.radians(145)
        r1 = KN.trace_back(al, be, th1, chi, 2)
        r2 = KN.trace_back(al, -be, th2, chi, 2)
        assert np.array_equal(r1["captured"], r2["captured"])
        assert np.array_equal(np.isnan(r1["r_n"]), np.isnan(r2["r_n"]))
        for n, i in np.argwhere(~np.isnan(r1["r_n"])):
            lam, eta, b = float(r1["lam"][i]), float(r1["eta"][i]), float(be[i])
            tol = closed_tol(lambda l, e, _t: _r_of(l, e, _tau_of(l, e, chi, th1, b, n), chi), lam, eta, 0.0)
            assert abs(r1["r_n"][n, i] - r2["r_n"][n, i]) <= tol, (n, i, r1["r_n"][n, i], r2["r_n"][n, i], tol)
        # edge-on (cos theta_o taken as 0 within 1e-12): the same computation for beta and -beta
        e1 = KN.trace_back(al, be, math.pi / 2, chi, 2)
        e2 = KN.trace_back(al, -be, math.pi / 2, chi, 2)
        assert np.array_equal(e1["captured"], e2["captured"])
        assert np.array_equal(np.isnan(e1["r_n"]), np.isnan(e2["r_n"]))
        ok = ~np.isnan(e1["r_n"])
        assert np.array_equal(e1["r_n"][ok], e2["r_n"][ok])
        cc = KN.critical_curve(chi, math.radians(30))
        m = (cc["beta"].size + 1) // 2  # the lower half is the mirror image of the upper half
        assert np.array_equal(cc["beta"][m:], -cc["beta"][:m - 1][::-1])
        assert np.array_equal(cc["alpha"][m:], cc["alpha"][:m - 1][::-1])


def test_kerr_equatorial_photon_orbits_agree_with_kerr_module():
    for chi in (0.0, 0.3, 0.9, 0.999):
        assert KN.photon_shell(chi) == (kerr.photon_orbit(chi, True), kerr.photon_orbit(chi, False))


def test_screen_ray_path_for_drawing():
    """screen_ray_path: starts on r = r_out on the way in, ends at the horizon (captured) or back on r = r_out; its
    phi agrees with the Hamiltonian route started from the path's first point (DOP853, error by a second run)."""
    chi, th = 0.9, math.radians(60)
    for al, be in ((2.0, 3.0), (6.5, 0.5)):
        p = KN.screen_ray_path(al, be, th, chi, r_out=30.0, n=60)
        assert abs(p["r"][0] - 30.0) <= 1e-9 * 30
        if p["captured"]:
            assert abs(p["r"][-1] - (KN.horizon(chi) + 0.02)) <= 1e-9
        else:
            assert abs(p["r"][-1] - 30.0) <= 1e-8 * 30
        lam, eta = KN.screen_to_constants(al, be, th, chi)
        ray = KN.NullRay.from_screen(al, be, th, chi)
        nur = float(np.sign(ray.drdtau(p["tau"][0])))
        nut = float(np.sign(ray.dthetadtau(p["tau"][0])))
        # the physical photon runs the other way: p0 for the reversed tangent, integrated backwards in tau
        p0 = KG.null_momentum(p["r"][0], p["theta"][0], float(lam), float(eta), chi, -nur, -nut)
        x0 = [0.0, p["r"][0], p["theta"][0], p["phi"][0]]
        dt = p["tau"] - p["tau"][0]
        sols = [KG.integrate(chi, x0, p0, -float(dt[-1] * 0.98), rtol=rt, atol=rt * 1e-2, dense=True)
                for rt in (1e-10, 1e-12)]
        k = dt < dt[-1] * 0.98
        y1 = np.array([sols[0].sol(-v) for v in dt[k]])
        y2 = np.array([sols[1].sol(-v) for v in dt[k]])
        err = 2 * np.abs(y1 - y2) + 1e-10
        assert np.all(np.abs(y2[:, 1] - p["r"][k]) <= err[:, 1] + 1e-9 * p["r"][k])
        assert np.all(np.abs(y2[:, 3] - p["phi"][k]) <= err[:, 3] + 1e-9 * (1 + np.abs(p["phi"][k])))
