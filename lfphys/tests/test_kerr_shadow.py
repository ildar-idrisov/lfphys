# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P7 / P14.3: the image of a Kerr black hole (lfphys.core.gravity.kerr_shadow) - the shadow against Bardeen's
closed-form critical curve, the photon rings against the Lyapunov demagnification of Johnson et al. 2020, the
emitters' four-velocities against the metric, the progressive image and its saved state, CPU against GPU.

Tolerances are derived in each test from the closed form's own sensitivities and the 64u-per-input budget of
test_kerr_null (module docstring there)."""

import math
import os

import numpy as np
import pytest

from lfphys.core import backend as B
from lfphys.core.gravity import kerr, kerr_geodesics as KG, kerr_null as KN, kerr_shadow as KS

U = 2.0 ** -53


@pytest.fixture(autouse=True)
def _cpu():
    B.configure(None)
    yield
    B.configure(None)


def _gpu():
    if os.environ.get("LFPHYS_NO_GPU"):
        return False
    return B.devices()["gpu"]["available"]


def _d34(al, be, th, chi):
    """-A/2 - z^2 - B/(4z) (= (r4 - r3)^2/4 where real): its sign decides the fate near the critical curve; and
    the a-priori bound of its round-off, 16 u (|A|/2 + z^2 + |B|/(4z))."""
    lam, eta = KN.screen_to_constants(np.array([al]), np.array([be]), th, chi)
    ro = KN.radial_roots(lam, eta, chi)
    A, Bc, z = ro["A"][0], ro["B"][0], ro["z"][0]
    return float(-A / 2 - z * z - Bc / (4 * z)), float(16 * U * (abs(A) / 2 + z * z + abs(Bc) / (4 * z)))


# --- the shadow: computed edge against the closed-form critical curve ----------------------------------------------
@pytest.mark.parametrize("chi,th_deg", [(0.0, 60.0), (0.5, 17.0), (0.5, 90.0), (0.94, 17.0), (0.94, 60.0),
                                        (0.998, 60.0), (0.998, 90.0), (0.9, 163.0)])
def test_shadow_edge_is_the_critical_curve(chi, th_deg):
    """Along 9 directions from the shadow's centre, the radius where the traced ray's fate changes (bisection on
    the tracer) equals the distance to Bardeen's critical curve (closed form, root along its parameter).
    Tolerance: the fate is decided by the sign of d34 = (r4 - r3)^2/4, computed with round-off e_d (a-priori
    bound), so the computed edge may be off by e_d/|d d34/d rho|; the closed-form curve point is exact to the
    gamma_12 bound of lambda, eta (test_kerr_null), mapped to the screen (<= 1e-13 here); plus the bisection's
    last bracket (2 u rho)."""
    th = math.radians(th_deg)
    cc = KN.critical_curve(chi, th, 801)
    cx = 0.5 * (cc["alpha"].max() + cc["alpha"].min())
    worst = 0.0
    for ang in np.linspace(0.1, 2 * math.pi - 0.1, 9):
        rc, _ = KN.critical_radius_at(chi, th, ang, (cx, 0.0))
        lo, hi = KS.capture_boundary(chi, th, ang, (cx, 0.0))
        ca, sa = math.cos(ang), math.sin(ang)
        h = 1e-6
        d1, e1 = _d34(cx + (rc + h) * ca, (rc + h) * sa, th, chi)
        d0, _ = _d34(cx + (rc - h) * ca, (rc - h) * sa, th, chi)
        slope = abs(d1 - d0) / (2 * h)
        tol = e1 / slope + 1e-13 * rc + 2 * U * hi + (hi - lo)
        # the engine's own bound (used by v15's live check, review B5-K1) is this one, evaluated at the edge
        tol_engine = float(KS.edge_tolerance(chi, th, [ang], [0.5 * (lo + hi)], (cx, 0.0))[0]) + (hi - lo)
        assert tol_engine == pytest.approx(tol, rel=1e-3)
        err = max(abs(lo - rc), abs(hi - rc))
        worst = max(worst, err)
        assert err <= tol, (ang, lo, hi, rc, tol)
    assert worst < 1e-12  # measured 2026-10-29: <= 1.5e-14


def test_many_directions_at_once_equal_the_single_ones():
    """``capture_boundaries`` and ``kerr_null.critical_radii`` (vectorized) against ``capture_boundary`` and
    ``critical_radius_at`` direction by direction: the same bisection, so the edges agree to the bracket; the closed
    form to the round-off of its parameter (8 u rho measured 2026-10-29: <= 1.3e-15 absolute)."""
    for chi, th_deg, center in [(0.9, 60.0, (0.0, 0.0)), (0.998, 90.0, (2.4, 0.0)), (0.3, 163.0, (0.2, 0.1)),
                                (0.0, 45.0, (0.0, 0.0))]:
        th = math.radians(th_deg)
        ang = np.linspace(0.05, 2 * math.pi - 0.05, 11)
        lo, hi = KS.capture_boundaries(chi, th, ang, center)
        rc, rb = KN.critical_radii(chi, th, ang, center)
        for k, a in enumerate(ang):
            l1, h1 = KS.capture_boundary(chi, th, a, center)
            assert abs(lo[k] - l1) <= hi[k] - lo[k] + 4 * U * h1 and abs(hi[k] - h1) <= hi[k] - lo[k] + 4 * U * h1
            r1, b1 = KN.critical_radius_at(chi, th, a, center)
            assert abs(rc[k] - r1) <= 16 * U * r1 and abs(rb[k] - b1) <= 16 * U * max(b1, 3.0)
    lo, hi = KS.capture_boundaries(0.6, 0.0, [0.3, 2.0])  # on the axis: the circle of face_on_shadow_radius
    b, _ = KN.face_on_shadow_radius(0.6)
    assert np.allclose(KN.critical_radii(0.6, 0.0, [0.3, 2.0])[0], b, rtol=0, atol=0)
    assert np.all(np.abs(0.5 * (lo + hi) - b) <= 1e-12 * b)
    with pytest.raises(ValueError, match="inside the shadow"):
        KS.capture_boundaries(0.9, 1.0, [0.0], (30.0, 0.0))


@pytest.mark.parametrize("chi,th_deg", [(0.0, 60.0), (0.5, 30.0), (0.9, 163.0), (0.998, 81.0), (0.998, 90.0)])
def test_shadow_size_on_the_traced_edge(chi, th_deg):
    """The size measured on the tracer's edge (review B5-K10) against the closed form about the same centre, within
    the stated bounds; the centre on the symmetry axis equals the extremes of the closed-form curve (the Kerr shadow
    is convex and symmetric); and the theories module's polygon measure (johannsen_metric.shadow_size, 4001 points)
    agrees to its interpolation error (measured 2026-10-29: 2.6e-7 in delta)."""
    from lfphys.theories.alternatives import johannsen_metric as JP
    th = math.radians(th_deg)
    s = KS.shadow_size(chi, th)
    assert np.all(np.abs(s["radii"] - s["radii_closed"]) <= s["radii_tol"])
    assert abs(s["delta"] - s["delta_closed"]) <= s["delta_tol"] < 1e-12
    assert abs(s["center_alpha"] - s["center_alpha_closed"]) <= s["center_tol"]
    cc = KN.critical_curve(chi, th, 4001)
    assert abs(s["center_alpha_closed"] - 0.5 * (cc["alpha"].max() + cc["alpha"].min())) <= 1e-12 * 6.0
    jp = JP.shadow_size(cc, charm=False)
    assert abs(jp["delta"] - s["delta_closed"]) <= 1e-6
    if chi == 0.0:
        assert s["delta"] == pytest.approx(0.0, abs=s["delta_tol"])


def _inside(px, py, poly_x, poly_y):
    """Even-odd rule (ray casting) for many points against a closed polygon."""
    inside = np.zeros(px.shape, bool)
    n = poly_x.size
    for i in range(n - 1):
        x0, y0, x1, y1 = poly_x[i], poly_y[i], poly_x[i + 1], poly_y[i + 1]
        cond = (y0 > py) != (y1 > py)
        with np.errstate(divide="ignore", invalid="ignore"):
            xin = x0 + (py - y0) * (x1 - x0) / (y1 - y0)
        inside ^= cond & (px < xin)
    return inside


def _dist_to_polyline(px, py, poly_x, poly_y):
    d = np.full(px.shape, np.inf)
    for i in range(poly_x.size - 1):
        x0, y0, x1, y1 = poly_x[i], poly_y[i], poly_x[i + 1], poly_y[i + 1]
        ex, ey = x1 - x0, y1 - y0
        L2 = ex * ex + ey * ey
        if L2 == 0.0:
            continue
        t = np.clip(((px - x0) * ex + (py - y0) * ey) / L2, 0.0, 1.0)
        d = np.minimum(d, np.hypot(px - x0 - t * ex, py - y0 - t * ey))
    return d


def test_pixels_against_the_critical_curve():
    """Every pixel of a 120 x 120 image farther than 1e-4 M from the critical curve (a 4001-point polygon of the
    closed form, chord error < 1e-5 M) is captured exactly when it lies inside the curve."""
    chi, th = 0.9, math.radians(60.0)
    sc = KS.Screen(120, 120, 7.5, alpha0=1.5)
    img = KS.ShadowImage(chi, th, sc, n_max=1).run(40)
    cc = KN.critical_curve(chi, th, 4001)
    px, py = np.meshgrid(sc.alpha(), sc.beta())
    al = np.append(cc["alpha"], cc["alpha"][0])
    be = np.append(cc["beta"], cc["beta"][0])
    inside = _inside(px, py, al, be)
    far = _dist_to_polyline(px, py, al, be) > 1e-4  # the 4001-point polygon's chord error is < 1e-5 M here
    assert np.mean(far) > 0.99
    assert np.array_equal(img.arrays["captured"][far].astype(bool), inside[far])


# --- the photon rings: Lyapunov demagnification ---------------------------------------------------------------------
@pytest.mark.parametrize("chi,th_deg,ang", [(0.0, 60.0, 1.0), (0.94, 17.0, 0.3), (0.94, 17.0, 3.0),
                                            (0.5, 75.0, 4.5)])
def test_photon_ring_images_approach_the_critical_curve_by_the_lyapunov_factor(chi, th_deg, ang):
    """The n-th image (n = 1..5) of the equatorial ring r = 8 M along a fixed screen direction: its distance to the
    critical curve d_n = rho_n - rho_c shrinks by the factor d_{n+1}/d_n -> e^{-gamma} (Johnson et al. 2020,
    Eqs. 7-9 and 29), gamma the Lyapunov exponent of the bound orbit seen in that direction. The approach is
    geometric (the corrections fall by a further e^{-gamma} per order), so the limit is bracketed by Aitken's
    extrapolation of the last three ratios; tolerance: twice the last change of the ratio."""
    th = math.radians(th_deg)
    cc = KN.critical_curve(chi, th, 801)
    cx = 0.5 * (cc["alpha"].max() + cc["alpha"].min())
    rho = [KS.ring_image(chi, th, 8.0, ang, n, (cx, 0.0)) for n in range(1, 6)]
    rc = rho[0][1]
    d = np.array([r[0] - rc for r in rho])
    assert np.all(d > 0) and np.all(np.diff(d) < 0)
    q = d[1:] / d[:-1]
    _, r_orbit = KN.critical_radius_at(chi, th, ang, (cx, 0.0))
    gam = float(KN.lyapunov(np.array([r_orbit]), chi)[0])
    target = math.exp(-gam)
    # Aitken's delta^2 on the ratio sequence
    q_lim = q[-1] - (q[-1] - q[-2]) ** 2 / ((q[-1] - q[-2]) - (q[-2] - q[-3]))
    tol = 2 * abs(q[-1] - q[-2]) + 1e-9
    assert abs(q[-1] - target) <= tol, (q, target)
    assert abs(q_lim - target) <= tol, (q_lim, target)


# --- emitters and the redshift --------------------------------------------------------------------------------------
@pytest.mark.parametrize("chi", [0.0, 0.5, 0.9, 0.998])
@pytest.mark.parametrize("pro", [True, False])
def test_emitter_four_velocities_are_unit_timelike(chi, pro):
    """u.u = -1 with the metric of kerr_geodesics; the Keplerian u^t equals the normalisation route
    1/sqrt(-(g_tt + 2 g_tphi Omega + g_phiphi Omega^2)); the plunge (Cunningham) has the ISCO's E, L and is
    continuous with the circular orbit at the ISCO. Tolerance: 64 u times the terms' magnitudes."""
    r_isco = kerr.isco(chi, pro)
    rs = np.concatenate((np.linspace(KN.horizon(chi) * 1.02, r_isco * 0.999, 7), np.linspace(r_isco, 40.0, 7)))
    ut, ur, up = KS.emitter_velocity(rs, chi, "cunningham", pro)
    E, L = kerr.circular_e_l(r_isco, chi, pro)
    for i, r in enumerate(rs):
        g = KG.metric(r, math.pi / 2, chi)
        u = np.array([ut[i], ur[i], 0.0, up[i]])
        norm = u @ g @ u
        mag = np.abs(u) @ np.abs(g) @ np.abs(u)
        assert abs(norm + 1.0) <= 64 * U * mag, (r, norm)
        if r < r_isco:  # the plunge keeps the ISCO's constants
            low = g @ u
            assert abs(-low[0] - E) <= 64 * U * mag and abs(low[3] - L) <= 64 * U * mag * r
            assert ur[i] < 0
        else:
            s = 1.0 if pro else -1.0
            om = s / (r ** 1.5 + s * chi)
            ut_n = 1.0 / math.sqrt(-(g[0, 0] + 2 * g[0, 3] * om + g[3, 3] * om * om))
            assert abs(ut[i] - ut_n) <= 64 * U * ut_n * (1 + abs(g[3, 3]) * om * om * ut_n ** 2)
    kep = KS.emitter_velocity(np.array([r_isco]), chi, "keplerian", pro)
    assert all(math.isnan(v[0]) for v in KS.emitter_velocity(np.array([r_isco * 0.99]), chi, "keplerian", pro))
    assert abs(kep[0][0] - ut[7]) == 0.0  # r_isco itself: the circular orbit in both models


def test_plunging_emitter_follows_a_geodesic():
    """Cunningham's emitter inside the ISCO is a geodesic: the Hamiltonian route started just inside the ISCO with
    the model's velocity passes the model's u^r, u^phi at smaller radii (DOP853 error estimated by a second run)."""
    chi, pro = 0.9, True
    r_isco = kerr.isco(chi, pro)
    r0 = r_isco * 0.98
    ut, ur, up = (float(v[0]) for v in KS.emitter_velocity(np.array([r0]), chi, "cunningham", pro))
    g = KG.metric(r0, math.pi / 2, chi)
    p0 = g @ np.array([ut, ur, 0.0, up])

    def ev(t, y):
        return y[1] - 1.6
    ev.terminal = True
    for rt in (1e-10, 1e-12):
        sol = KG.integrate(chi, [0, r0, math.pi / 2, 0], p0, 50.0, rtol=rt, atol=rt * 1e-2, events=[ev])
    r_end = float(sol.y_events[0][0][1])
    pr = float(sol.y_events[0][0][4])
    dl = r_end ** 2 - 2 * r_end + chi ** 2
    sig = r_end ** 2
    ur_ode = dl * pr / sig  # u^r = g^rr p_r
    ur_mod = float(KS.emitter_velocity(np.array([r_end]), chi, "cunningham", pro)[1][0])
    assert abs(ur_ode - ur_mod) <= 1e-8 * abs(ur_mod)


def test_redshift_against_the_four_momentum_route():
    """g = 1/(-p.u) with p from (lambda, eta) and the sign of p^r (kerr_geodesics.null_momentum) and u from the
    emitter: equals ``redshift`` (the closed form u^t (1 - Omega lambda) for circular orbits) to 64 u."""
    rng = np.random.default_rng(5)
    for chi, pro in ((0.0, True), (0.7, True), (0.95, False)):
        for _ in range(20):
            r = float(rng.uniform(KN.horizon(chi) * 1.05, 30.0))
            lam = float(rng.uniform(-5, 5))
            eta = float(rng.uniform(0.5, 30))
            if KN.radial_potential(r, lam, eta, chi) < 0:
                continue
            kr = float(rng.choice([-1.0, 1.0]))
            g = float(KS.redshift(np.array([r]), lam, eta, kr, chi, "cunningham", pro)[0])
            ut, ur, up = (float(v[0]) for v in KS.emitter_velocity(np.array([r]), chi, "cunningham", pro))
            p = KG.null_momentum(r, math.pi / 2, lam, eta, chi, kr, 1.0)
            u = np.array([ut, ur, 0.0, up])
            g2 = 1.0 / -(p @ u)
            assert abs(g - g2) <= 64 * U * g * (np.abs(p) @ np.abs(u)) * g, (r, lam, g, g2)


def test_face_on_schwarzschild_redshift():
    """A face-on observer of a Schwarzschild disk: the direct (n = 0) image of the ring r >= 6 has lambda -> 0 and
    g = 1/u^t = sqrt(1 - 3/r) (time dilation of the circular orbit, no Doppler term); at theta_o = 1e-9 the
    Doppler term is |Omega lambda| <= 1e-8 relative."""
    sc = KS.Screen(64, 64, 12.0)
    img = KS.ShadowImage(0.0, 1e-9, sc, n_max=0, emitter="keplerian").run()
    r0, g0 = img.arrays["r_n"][0], img.arrays["g_n"][0]
    ok = ~np.isnan(g0)
    assert ok.sum() > 1000
    assert np.allclose(g0[ok], np.sqrt(1 - 3 / r0[ok]), rtol=1e-8, atol=0)


# --- progressive image, state, devices ------------------------------------------------------------------------------
def test_progressive_image_and_exact_state_restore():
    sc = KS.Screen(48, 40, 9.0, alpha0=0.5)
    full = KS.ShadowImage(0.8, math.radians(50), sc, n_max=2).run(64)
    part = KS.ShadowImage(0.8, math.radians(50), sc, n_max=2)
    part.step(7)
    part.step(9)
    st = part.state()
    import pickle
    st2 = pickle.loads(pickle.dumps(st))
    cont = KS.ShadowImage.from_state(st2)
    while cont.step(5):
        pass
    for k, v in full.arrays.items():
        assert np.array_equal(v, cont.arrays[k], equal_nan=True), k
    assert cont.done and full.done
    assert set(st["arrays"]) >= {"captured", "r_n", "g_n", "n_cross", "tau_total"}


def test_kernel_is_registered():
    ks = B.kernels()
    assert "gravity.kerr_shadow" in ks and ks["gravity.kerr_shadow"].gpu
    assert not B.import_errors(), B.import_errors()


@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_gpu_equals_cpu():
    """The same elementwise formulas on CuPy: CUDA's sin, cos, asin, acos, atan, cbrt differ from glibc's by <= 2
    ulp, so a pixel's results differ by at most the closed form's sensitivity to a few-ulp change of its inputs:
    tolerance 16 u (|alpha dr/dalpha| + |beta dr/dbeta| + |r|) x 8, the derivatives by central differences on the
    CPU; pixels within 0.05 M of the critical curve (sensitivity unbounded) are compared by fate only."""
    chi, th = 0.9, math.radians(60)
    sc = KS.Screen(96, 96, 8.0, alpha0=1.0)
    a, b = sc.rows(0, sc.ny)
    B.configure({"kernels": {"gravity.kerr_shadow": {"device": "cpu"}}})
    cpu = KS.trace_screen(a, b, th, chi, 2)
    B.configure({"kernels": {"gravity.kerr_shadow": {"device": "gpu"}}})
    gpu = KS.trace_screen(a, b, th, chi, 2)
    assert B.used()["gravity.kerr_shadow"]["drawn"]["device"] == "gpu"
    B.configure({"kernels": {"gravity.kerr_shadow": {"device": "cpu"}}})
    h = 1e-6
    ra = KS.trace_screen(a + h, b, th, chi, 2)["r_n"]
    la = KS.trace_screen(a - h, b, th, chi, 2)["r_n"]
    rb = KS.trace_screen(a, b + h, th, chi, 2)["r_n"]
    lb = KS.trace_screen(a, b - h, th, chi, 2)["r_n"]
    sens = np.abs(a) * np.abs(ra - la) / (2 * h) + np.abs(b) * np.abs(rb - lb) / (2 * h) + np.abs(cpu["r_n"])
    cc = KN.critical_curve(chi, th, 4001)
    al, be = np.append(cc["alpha"], cc["alpha"][0]), np.append(cc["beta"], cc["beta"][0])
    far = _dist_to_polyline(a, b, al, be) > 0.05
    assert np.array_equal(cpu["captured"][far], gpu["captured"][far])
    ok = far[None] & ~np.isnan(cpu["r_n"]) & ~np.isnan(sens)
    assert np.array_equal(np.isnan(cpu["r_n"])[far[None].repeat(3, 0)], np.isnan(gpu["r_n"])[far[None].repeat(3, 0)])
    assert np.all(np.abs(cpu["r_n"][ok] - gpu["r_n"][ok]) <= 128 * U * sens[ok])
    # the redshift: that bound of r propagated, plus the formula's own rounding near the photon's turning point and
    # inside the ISCO (redshift_tolerance; review B5-kerr-v15 K2: the input sensitivity of g alone was exceeded)
    tol_g = KS.redshift_tolerance(cpu["r_n"], cpu["lam"][None], cpu["eta"][None], cpu["kr_sign_n"], chi,
                                  r_tol=128 * U * sens)
    okg = ok & ~np.isnan(cpu["g_n"]) & ~np.isnan(tol_g)
    assert np.array_equal(np.isnan(cpu["g_n"])[ok], np.isnan(gpu["g_n"])[ok])
    assert np.all(np.abs(cpu["g_n"][okg] - gpu["g_n"][okg]) <= tol_g[okg])


def test_redshift_tolerance_covers_the_rounding_of_its_square_roots():
    """The bound of ``redshift_tolerance`` against the formula evaluated in 40-digit arithmetic at crossings near the
    places where it loses digits: just inside the ISCO (the plunge's sqrt(R_timelike) -> 0) and near a photon's radial
    turning point (sqrt(R) -> 0); the CPU's own error stays within it, and the bound grows there as 1/sqrt."""
    import mpmath as mp
    mp.mp.dps = 40
    chi, pro = 0.9, True
    r_isco = kerr.isco(chi, pro)
    E, L = kerr.circular_e_l(r_isco, chi, pro)
    lam = 1.0
    cases = []
    for r in (r_isco * (1 - 1e-6), r_isco * (1 - 1e-3), 0.8 * r_isco, 5.5, 9.0):
        for gap in (1e-9, 1e-4, 0.3):  # the photon's radial turning point just below r, or farther
            rt = r * (1 - gap)
            eta = (rt * rt + chi * chi - chi * lam) ** 2 / (rt * rt - 2 * rt + chi * chi) - (lam - chi) ** 2
            dl = r * r - 2 * r + chi * chi
            if eta > 0 and (r * r + chi * chi - chi * lam) ** 2 - dl * (eta + (lam - chi) ** 2) > 0:
                cases.append((r, eta))  # a photon that can be at r (R(r) > 0)
    assert len(cases) >= 10
    for r, eta in cases:
        for kr in (1.0, -1.0):
            g = float(KS.redshift(np.array([r]), lam, eta, np.array([kr]), chi)[0])
            R_, a = mp.mpf(r), mp.mpf(chi)
            dl = R_ * R_ - 2 * R_ + a * a
            Rp = (R_ * R_ + a * a - a * lam) ** 2 - dl * (eta + (lam - a) ** 2)
            pr = kr * mp.sqrt(Rp) / dl
            if r >= r_isco:
                sr = mp.sqrt(R_)
                ut = (R_ * sr + a) / (R_ ** mp.mpf(0.75) * mp.sqrt(R_ * sr - 3 * sr + 2 * a))
                ur, up = 0, ut / (R_ * sr + a)
            else:
                Em, Lm = mp.mpf(E), mp.mpf(L)
                P = Em * (R_ * R_ + a * a) - a * Lm
                ut = ((R_ * R_ + a * a) * P / dl - a * (a * Em - Lm)) / (R_ * R_)
                up = (a * P / dl - (a * Em - Lm)) / (R_ * R_)
                # clamped at 0 as the engine does: with E, L rounded to doubles the triple root at the ISCO moves
                ur = -mp.sqrt(max(P * P - dl * (R_ * R_ + (Lm - a * Em) ** 2), 0)) / (R_ * R_)
            exact = 1 / (ut - lam * up - pr * ur)
            tol = float(KS.redshift_tolerance(np.array([r]), lam, eta, np.array([kr]), chi)[0])
            assert abs(g - float(exact)) <= tol, (r, kr, g, float(exact), tol)
    # the plunge's part grows as 1/sqrt(R_timelike) towards the ISCO: a photon turning at 0.998 r_isco seen there
    rt = 0.998 * r_isco
    eta = (rt * rt + chi * chi - chi * lam) ** 2 / (rt * rt - 2 * rt + chi * chi) - (lam - chi) ** 2
    near = KS.redshift_tolerance(np.array([r_isco * (1 - 1e-12)]), lam, eta, np.array([1.0]), chi)[0]
    far = KS.redshift_tolerance(np.array([r_isco * (1 - 1e-3)]), lam, eta, np.array([1.0]), chi)[0]
    assert near > 100 * far


def test_face_on_observer():
    """On the axis (theta_o = 0 or pi): the shadow is the circle b = sqrt(eta + a^2) of the bound orbit with
    lambda = 0 (GL-b Eq. 61); the traced edge is there in every direction; theta_o = 0 and pi give the same image;
    a nearly face-on observer (1e-7 rad) differs from it by O(a theta_o)."""
    for chi in (0.0, 0.6, 0.99):
        b, r0 = KN.face_on_shadow_radius(chi)
        lam, eta = KN.critical_constants_t(np.array([(r0 - 3) / chi]), chi)[:2] if chi else (0.0, 27.0)
        assert abs(float(np.asarray(lam).ravel()[0])) <= 1e-12 * max(1.0, b)
        for ang in (0.3, 2.0, 4.0):
            lo, hi = KS.capture_boundary(chi, 0.0, ang)
            d1, e1 = _d34((b + 1e-6) * math.cos(ang), (b + 1e-6) * math.sin(ang), 0.0, chi)
            d0, _ = _d34((b - 1e-6) * math.cos(ang), (b - 1e-6) * math.sin(ang), 0.0, chi)
            tol = e1 / (abs(d1 - d0) / 2e-6) + 1e-13 * b
            assert abs(lo - b) <= tol and abs(hi - b) <= tol
        a_, b_ = KS.Screen(24, 24, 7.0).rows(0, 24)
        i0 = KS.trace_screen(a_, b_, 0.0, chi)
        ipi = KS.trace_screen(a_, -b_, math.pi, chi)  # the mirror image through the equatorial plane
        for k in ("captured", "r_n", "g_n"):
            assert np.array_equal(i0[k], ipi[k], equal_nan=True)
        near = KN.critical_curve(chi, 1e-7, 401)
        assert np.max(np.abs(np.hypot(near["alpha"], near["beta"]) - b)) <= 10 * chi * 1e-7 + 1e-9


# --- review B5-K12: the whole image pipeline against an independent route ---------------------------------------
def _pipeline_pixels(chi, th):
    """Pixels just outside the critical curve on the prograde (left) side, whose later crossings follow the radial
    turning point at r < r_isco (the plunging gas), plus generic pixels."""
    cc = KN.critical_curve(chi, th, 801)
    cx = 0.5 * (cc["alpha"].max() + cc["alpha"].min())
    pix = []
    for ang in (math.pi - 0.3, math.pi, math.pi + 0.3, 0.5 * math.pi, 1.5 * math.pi):
        rc, _ = KN.critical_radius_at(chi, th, ang, (cx, 0.0))
        for f in (1e-3, 1e-2, 0.05, 0.3):
            pix.append((cx + rc * (1 + f) * math.cos(ang), rc * (1 + f) * math.sin(ang)))
    pix += [(2.0, 3.0), (-3.0, -4.5), (0.5, -6.5), (7.5, 1.0)]
    return pix


@pytest.mark.parametrize("chi,th_deg,pro", [(0.9, 60.0, True), (0.95, 75.0, False), (0.7, 163.0, True)])
def test_crossings_redshifts_and_turning_points_against_an_independent_route(chi, th_deg, pro):
    """Review B5-K12. For each pixel: the fate, every crossing's radius r_n, the sign of the photon's p^r there,
    the face of the disk it left (``face_n``), the redshift g_n of the (Cunningham) emitter, and the Mino time of the
    radial turning point, against ``tests/kerr_routes.py``: Hamilton's equations from r0 = 1e7 at theta_o - beta/r0
    with crossing and turning events, the emitter from the metric, g = 1/(-p.u). The sample contains crossings after
    the turning point inside the ISCO (radially moving gas), where a wrong sign of p^r or a wrong turning time changes
    g. Tolerances: the route's error by a second run at a 100 times tighter tolerance (x2), its start error
    sqrt(R(r_n)) dtau with dtau = (|Theta'(theta_o)|/(4 |beta|) + 1)/r0^2, and the closed form's 128 u per input
    (alpha, beta) with its own sensitivities; for g the r tolerance times |dg/dr| plus 64 u of the products."""
    from kerr_routes import emitter_four_velocity, hamilton_screen_ray
    th = math.radians(th_deg)
    r_isco = kerr.isco(chi, pro)
    after_turn_inside_isco = 0
    for al, be in _pipeline_pixels(chi, th):
        res = KS.trace_screen(np.array([al]), np.array([be]), th, chi, 3, "cunningham", pro)
        h = 1e-6
        rA = KS.trace_screen(np.array([al + h, al - h]), np.array([be, be]), th, chi, 3, "cunningham", pro)
        rB = KS.trace_screen(np.array([al, al]), np.array([be + h, be - h]), th, chi, 3, "cunningham", pro)
        ra, rb = rA["r_n"], rB["r_n"]
        routes = [hamilton_screen_ray(al, be, th, chi, rtol=rt) for rt in (1e-11, 1e-13)]
        ham = routes[1]
        assert ham["captured"] == bool(res["captured"][0])
        lam, eta = ham["lam"], ham["eta"]
        c, s = math.cos(th), math.sin(th)
        dTh = abs(-2 * chi * chi * c * s + 2 * lam * lam * c / s ** 3)
        dtau0 = (dTh / (4 * abs(be)) + 1.0) / 1e7 ** 2
        if not math.isnan(res["tau_turn"][0]):
            err_t = 2 * abs(routes[0]["tau_turn"] - ham["tau_turn"]) + dtau0
            sens_t = (abs(al) * abs(rA["tau_turn"][0] - rA["tau_turn"][1]) + abs(be) * abs(rB["tau_turn"][0]
                      - rB["tau_turn"][1])) / (2 * h) + res["tau_turn"][0]
            assert abs(res["tau_turn"][0] - ham["tau_turn"]) <= err_t + 128 * U * sens_t
        else:
            assert math.isnan(ham["tau_turn"])
        n_eng = int(np.sum(~np.isnan(res["r_n"][:, 0])))
        assert ham["cross"].shape[0] >= n_eng
        for n in range(n_eng):
            y, y1 = ham["cross"][n], routes[0]["cross"][n]
            r_e = float(res["r_n"][n, 0])
            Rn = max(KN.radial_potential(r_e, lam, eta, chi), 0.0)
            sens = (abs(al) * abs(ra[n, 0] - ra[n, 1]) + abs(be) * abs(rb[n, 0] - rb[n, 1])) / (2 * h) + r_e
            tol_r = 2 * abs(y[1] - y1[1]) + math.sqrt(Rn) * dtau0 + 128 * U * sens
            assert abs(r_e - y[1]) <= tol_r, (al, be, n, r_e, y[1], tol_r)
            assert res["kr_sign_n"][n, 0] == math.copysign(1.0, y[4]), (al, be, n)
            assert res["face_n"][n, 0] == -math.copysign(1.0, y[5]), (al, be, n)  # p^theta < 0: towards +z
            u = emitter_four_velocity(y[1], chi, pro)
            p = np.array([-1.0, y[4], y[5], lam])
            g_ref = 1.0 / -(p @ u)
            dr = 1e-7 * r_e
            gp = KS.redshift(np.array([r_e + dr]), lam, eta, res["kr_sign_n"][n, 0], chi, "cunningham", pro)[0]
            gm = KS.redshift(np.array([r_e - dr]), lam, eta, res["kr_sign_n"][n, 0], chi, "cunningham", pro)[0]
            tol_g = abs(gp - gm) / (2 * dr) * tol_r + 64 * U * g_ref * g_ref * float(np.abs(p) @ np.abs(u)) \
                + 2 * abs(1.0 / -(np.array([-1.0, y1[4], y1[5], lam]) @ emitter_four_velocity(y1[1], chi, pro))
                          - g_ref)
            assert abs(res["g_n"][n, 0] - g_ref) <= tol_g, (al, be, n, res["g_n"][n, 0], g_ref, tol_g)
            if res["kr_sign_n"][n, 0] < 0 and r_e < r_isco:
                after_turn_inside_isco += 1
    if pro and chi >= 0.9:
        assert after_turn_inside_isco >= 2  # the sample does exercise the radial redshift after the turn


def test_screen_orientation_and_the_approaching_side():
    """Review B5-K12 (an image upside down passed every test). The screen's row 0 is the top, beta > 0 (the
    projected spin axis up), column 0 the left, alpha < 0; at theta_o = 60 deg the top centre pixel's direct image is
    the far side of the disk (its crossing behind the hole, cos(phi) < 0 with the observer at phi = 0, from the
    independent Hamiltonian route) and the bottom one the near side; the approaching side of a prograde disk is at
    alpha < 0 (GL-b: the projected rotation is counter-clockwise), where g of the direct image is larger."""
    from kerr_routes import hamilton_screen_ray
    sc = KS.Screen(64, 64, 9.0)
    p = 18.0 / 64
    assert np.array_equal(sc.beta(), (31.5 - np.arange(64)) * p)
    assert np.array_equal(sc.alpha(), -9.0 + p * (np.arange(64) + 0.5))
    chi, th = 0.9, math.radians(60)
    img = KS.ShadowImage(chi, th, sc, n_max=0).run()
    j = 32
    for i, sign in ((2, 1.0), (61, -1.0)):
        al, be = float(sc.alpha()[j]), float((31.5 - i) * p)
        ham = hamilton_screen_ray(al, be, th, chi)
        assert sign * math.cos(ham["cross"][0][3]) < 0  # top: behind the hole; bottom: in front of it
        assert abs(img.arrays["r_n"][0, i, j] - ham["cross"][0][1]) <= 1e-8 * ham["cross"][0][1]
    g0 = img.arrays["g_n"][0]
    assert np.nanmax(g0[:, :32]) > np.nanmax(g0[:, 32:]) and np.nanmean(g0[:, :32]) > np.nanmean(g0[:, 32:])


def test_crossing_order_and_face_near_edge_on():
    """Review B5-K9: n counts crossings, not turns around the hole. a = 0.99, rays below the line of sight: at 89.9 deg
    the first crossing (n = 0, the northern face) lies far out (r ~ |beta|/cos theta_o > 2000 M) and the direct image
    of the southern face is n = 1; at exactly 90 deg (the observer's own crossing dropped) that image is n = 0. The
    face of the disk (``face_n``) labels it the same on both sides of 90 deg, and its radius is continuous (to the
    O(cos theta_o) change of the ray: 1e-2 relative between 89.9 and 90 deg)."""
    chi = 0.99
    for al, be in ((0.5, -6.0), (3.0, -4.0)):
        r899 = KS.trace_screen(np.array([al]), np.array([be]), math.radians(89.9), chi, 2)
        r90 = KS.trace_screen(np.array([al]), np.array([be]), math.pi / 2, chi, 2)
        assert r899["face_n"][0, 0] == 1.0 and r899["r_n"][0, 0] > 1000.0
        assert r899["face_n"][1, 0] == -1.0 and r90["face_n"][0, 0] == -1.0
        assert abs(r899["r_n"][1, 0] - r90["r_n"][0, 0]) <= 1e-2 * r90["r_n"][0, 0]
    # away from edge-on the faces alternate, starting with the near face: northern for an observer above the plane,
    # southern below it
    a_, b_ = KS.Screen(40, 40, 8.0).rows(0, 40)
    for th, first in ((math.radians(60.0), 1.0), (math.radians(120.0), -1.0)):
        r = KS.trace_screen(a_, b_, th, 0.5, 2)
        for n in range(3):
            ok = ~np.isnan(r["face_n"][n])
            assert ok.sum() > 10 and np.all(r["face_n"][n][ok] == first * (-1.0) ** n)


def test_disk_intensity_states_its_choices():
    """Review B5-K15: I = sum_n f_n g_n^p J(r_n) with f_0 = 1, f_n = f for n > 0; crossings beyond r_out and missing
    ones are skipped."""
    r_n = np.array([[6.0, 30.0], [4.0, np.nan], [3.1, 2.9]])
    g_n = np.array([[0.8, 0.9], [0.6, np.nan], [0.5, 0.4]])
    J = lambda r: r ** -2.0  # noqa: E731
    got = KS.disk_intensity(r_n, g_n, J, power=3.0, f_higher=1.5, r_out=20.0)
    want = np.array([0.8 ** 3 / 36 + 1.5 * 0.6 ** 3 / 16 + 1.5 * 0.5 ** 3 / 3.1 ** 2,
                     1.5 * 0.4 ** 3 / 2.9 ** 2])
    assert np.allclose(got, want, rtol=4 * U)
