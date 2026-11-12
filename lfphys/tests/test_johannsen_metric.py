# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The what-if shadow of the Johannsen (2013) Kerr-like metric (theories.alternatives.johannsen_metric): its
closed forms against the paper's Appendix (transcribed from the rendered page of arXiv:1501.02814, Eqs. A1-A2), the
double-root conditions in 30-digit arithmetic, the Kerr limit, the non-spinning closed form against the series of
Psaltis et al. 2020 (Eq. 8), and the published EHT bounds on alpha13 and alpha12 reproduced."""

import math

import mpmath as mp
import numpy as np
import pytest

from lfphys.core import data as D
from lfphys.core.gravity import kerr, kerr_null as KN
from lfphys.theories.alternatives import johannsen_metric as JM

U = 2.0 ** -53


@pytest.fixture(autouse=True)
def _dps():
    with mp.workdps(30):
        yield


def xi_appendix(r, a, a13, a22):
    """Johannsen 2013b App. Eq. (1), M = 1."""
    num = (-3 * a ** 4 * a13 + a * a * r * (7 * a13 - 5 * r * a13 + r ** 3 + r ** 4)
           + r ** 3 * (3 * a13 - 2 * r * a13 - 3 * r ** 3 + r ** 4))
    den = a * r * (a22 * (2 * a * a + 3 * r * r) - 5 * r * a22 - r ** 3 + r ** 4)
    return -num / den


def eta_appendix(r, a, b, c):
    """Johannsen 2013b App. Eq. (2), M = 1, b = alpha13, c = alpha22."""
    den = a * a * r ** 6 * (c * (2 * a * a + 3 * r * r) - 5 * r * c - r ** 3 + r ** 4) ** 2
    t8 = a ** 8 * b * c * (b * c + 6 * r * r * b - 4 * r ** 3 * c)
    t6 = -a ** 6 * r * (2 * b * b * c * c + r * b * b * c * c + 12 * r * r * b * b * c
                        - 2 * r ** 3 * b * c * (b + 4 * c) + 8 * r ** 4 * b * (c * c - 3 * b) + r ** 5 * b * (15 * b + 34 * c)
                        + 6 * r ** 6 * c * (b - 2 * c) - 8 * r ** 7 * c * c)
    t4 = a ** 4 * r ** 3 * (4 * b * b * c * c - r * b * b * c * c + 8 * r * r * b * b * c
                            + r ** 3 * b * (8 * c * c - b * (6 * c + 49)) + 2 * r ** 4 * b * (38 * b + c * (2 * c + 35))
                            - 5 * r ** 5 * (6 * b * b + 8 * b * c + 5 * c * c) + 2 * r ** 6 * c * (b - c)
                            + r ** 7 * (23 * c * c - 22 * b) + 2 * r ** 8 * (5 * b + 8 * c) + 8 * r ** 9 * c)
    t2 = a * a * r ** 5 * (-2 * b * b * c * c + r * b * b * c * c + 4 * r * r * b * b * c
                           - 2 * r ** 3 * b * (b * (c + 21) + 8 * c * c) + 2 * r ** 4 * b * (28 * b + c * (4 * c + 15))
                           - r ** 5 * b * (19 * b + 30 * c) + 2 * r ** 6 * (b * (4 * c + 21) - 16 * c * c)
                           - 2 * r ** 7 * (24 * b + (15 - 8 * c) * c) + 2 * r ** 8 * (7 * b - 2 * c) + 10 * r ** 9 * c
                           + 4 * r ** 10)
    t0 = -r ** 10 * (3 * b - 2 * r * b - 3 * r ** 3 + r ** 4) ** 2
    return (t8 + t6 + t4 + t2 + t0) / den


class _MpDev:
    def __init__(self, a12, a13, a22):
        self.a12, self.a13, self.a22 = mp.mpf(a12), mp.mpf(a13), mp.mpf(a22)

    def A1(self, r):
        return 1 + self.a12 / r ** 2 + self.a13 / r ** 3

    def dA1(self, r):
        return -2 * self.a12 / r ** 3 - 3 * self.a13 / r ** 4

    def A2(self, r):
        return 1 + self.a22 / r ** 2

    def dA2(self, r):
        return -2 * self.a22 / r ** 3


# (0.9, alpha13 = -2, alpha22 = 1) was here until the review B5-K6 check: its determinant (Johannsen 2013a Eq. 72)
# vanishes outside the horizon, so it is refused now; replaced by alpha13 = -1
CASES = [(0.5, 0.0, 1.5, 0.0), (0.9, 0.0, -1.0, 1.0), (0.94, 0.0, 3.0, -1.5), (0.3, 0.0, 0.7, 2.0),
         (0.7, 0.4, -1.0, 0.5)]


@pytest.mark.parametrize("chi,a12,a13,a22", CASES)
def test_photon_orbits_against_the_appendix_and_the_double_root(chi, a12, a13, a22):
    """In 30 digits: the engine's lambda(r), eta(r) (derived from R = R' = 0) equal Johannsen's Appendix Eqs. (1)-(2)
    (alpha12 = 0, where the Appendix applies) and satisfy R = R' = 0; in floats they are within the propagated
    round-off of their sub-expressions (32 u per sub-expression, first order)."""
    dev = JM.Deviation(a12, a13, a22)
    JM.check_regular(chi, dev)
    lo, hi = JM.photon_shell(chi, dev)
    rs = np.linspace(lo + 0.01 * (hi - lo), hi - 0.01 * (hi - lo), 9)
    lam_f, eta_f = JM.photon_orbit_constants(rs, chi, dev)
    md = _MpDev(a12, a13, a22)
    a = mp.mpf(chi)
    for i, rf in enumerate(rs):
        r = mp.mpf(rf)
        dl, dlp = r * r - 2 * r + a * a, 2 * r - 2
        w = (r * r + a * a) * md.A1(r)
        wp = 2 * r * md.A1(r) + (r * r + a * a) * md.dA1(r)
        D_ = a * (dlp * md.A2(r) - 2 * dl * md.dA2(r))
        lam = (dlp * w - 2 * dl * wp) / D_
        P = w - a * md.A2(r) * lam
        eta = P * P / dl - (lam - a) ** 2
        R = P * P - dl * ((lam - a) ** 2 + eta)
        Pp = wp - a * md.dA2(r) * lam
        Rp = 2 * P * Pp - dlp * ((lam - a) ** 2 + eta)
        assert abs(R) < mp.mpf(10) ** -24 and abs(Rp) < mp.mpf(10) ** -24
        if a12 == 0.0:
            assert abs(lam - xi_appendix(r, a, md.a13, md.a22)) < mp.mpf(10) ** -24 * (1 + abs(lam))
            assert abs(eta - eta_appendix(r, a, md.a13, md.a22)) < mp.mpf(10) ** -22 * (1 + abs(eta))
        tol_lam = 32 * U * (abs(dlp * w) + abs(2 * dl * wp)) / abs(D_) \
            + 32 * U * abs(lam) * (abs(dlp * md.A2(r)) + abs(2 * dl * md.dA2(r))) * abs(a) / abs(D_)
        dP = abs(a * md.A2(r)) * tol_lam + 32 * U * (abs(w) + abs(a * md.A2(r) * lam))
        tol_eta = 2 * abs(P) * dP / abs(dl) + 2 * abs(lam - a) * tol_lam + 32 * U * (P * P / abs(dl) + (lam - a) ** 2)
        assert abs(lam_f[i] - float(lam)) <= float(tol_lam), (rf, lam_f[i], lam)
        assert abs(eta_f[i] - float(eta)) <= float(tol_eta), (rf, eta_f[i], eta)


def test_kerr_limit():
    dev = JM.Deviation()
    for chi, th in ((0.5, 0.6), (0.94, 1.2)):
        assert JM.photon_shell(chi, dev) == pytest.approx(KN.photon_shell(chi), rel=1e-14)
        c1 = JM.shadow_curve(chi, th, dev)
        c2 = KN.critical_curve(chi, th)
        assert np.array_equal(c1["alpha"], c2["alpha"]) and np.array_equal(c1["beta"], c2["beta"])
        r = np.linspace(*KN.photon_shell(chi), 7)[1:-1]
        lj, ej = JM.photon_orbit_constants(r, chi, dev)
        lk, ek = KN.critical_constants(r, chi)
        assert np.allclose(lj, lk, rtol=0, atol=1e-12) and np.allclose(ej, ek, rtol=0, atol=1e-11)
    assert JM.delta(0.0, 1.0, dev) == pytest.approx(0.0, abs=4 * U)
    assert JM.nonspinning_shadow(dev) == pytest.approx((3 * math.sqrt(3), 3.0), rel=1e-12)


def test_nonspinning_shadow_against_the_series_of_psaltis_et_al():
    """Psaltis et al. 2020 Eq. (8): r_sh = 3 sqrt 3 (1 + alpha13/27 - alpha13^2/486 + O(alpha13^3)). The residual
    divided by alpha13^3 tends to a constant: its ratio for alpha13 halved stays within 1 +- 4 alpha13 (the next
    order)."""
    res = []
    for al in (0.08, 0.04, 0.02):
        b, _ = JM.nonspinning_shadow(JM.Deviation(alpha13=al))
        series = 3 * math.sqrt(3) * (1 + al / 27 - al * al / 486)
        res.append((b - series) / al ** 3)
    assert abs(res[1] / res[0] - 1) <= 4 * 0.08 and abs(res[2] / res[1] - 1) <= 4 * 0.04
    # the photon sphere: d/dr [r A1/sqrt(1 - 2/r)] = 0, an independent check by central differences
    dev = JM.Deviation(alpha13=2.0)
    b, rph = JM.nonspinning_shadow(dev)
    f = lambda r: r * dev.A1(r) / math.sqrt(1 - 2 / r)  # noqa: E731
    assert abs(f(rph * (1 + 1e-4)) - b) <= 1e-7 * b and abs(f(rph * (1 - 1e-4)) - b) <= 1e-7 * b
    assert f(rph * 1.01) > b and f(rph * 0.99) > b


def test_small_spin_tends_to_the_nonspinning_shadow():
    dev = JM.Deviation(alpha13=2.0, alpha22=0.5)
    d0 = JM.delta(0.0, 1.0, dev)
    d1 = JM.delta(1e-3, 1.0, dev)
    assert abs(d1 - d0) < 1e-5  # O(a^2) plus the median of a sampled curve (~1e-8 here)


def test_published_eht_bounds_are_reproduced():
    """M87*: |delta| <= 0.17 gives -3.6 < alpha13 < 5.9 (Psaltis et al. 2020, non-spinning); Sgr A* Keck bounds
    (Paper VI Eq. 12) give -3.1 <~ alpha13 <~ 1.5 and -1.1 <~ alpha12 <~ 0.5 (Paper VI Table 3). The published
    numbers carry two significant figures: agreement within half a unit of their last digit (0.05)."""
    bounds = JM.eht_delta_bounds()
    m87 = JM.allowed_range("alpha13", bounds["M87* (|delta| <= 0.17, Psaltis et al. 2020)"])
    assert abs(m87["low"] - D.JP_ALPHA13_M87_PSALTIS2020[0]) <= 0.05
    assert abs(m87["high"] - D.JP_ALPHA13_M87_PSALTIS2020[1]) <= 0.05
    keck = bounds["Sgr A* Keck (Paper VI Eq. 12)"]
    r13 = JM.allowed_range("alpha13", keck)
    r12 = JM.allowed_range("alpha12", keck)
    assert abs(r13["low"] - D.JP_ALPHA13_SGRA_KECK[0]) <= 0.05 and abs(r13["high"] - D.JP_ALPHA13_SGRA_KECK[1]) <= 0.05
    assert abs(r12["low"] - D.JP_ALPHA12_SGRA_KECK[0]) <= 0.05 and abs(r12["high"] - D.JP_ALPHA12_SGRA_KECK[1]) <= 0.05
    assert not any(v for k, v in {**m87, **r13, **r12}.items() if k.endswith("_limited"))


def test_kerr_shadows_are_within_the_quoted_range():
    """EHT 2022 Paper VI (Sec. 3): Kerr shadows are smaller than Schwarzschild's by up to ~7.5 % (Takahashi 2004;
    Chan et al. 2013): delta in [-0.075, 0] for every spin and inclination (with the median diameter: >= -0.08)."""
    worst = 0.0
    for chi in (0.0, 0.5, 0.9, 0.998):
        for th in (math.radians(5), math.radians(17), math.radians(60), math.pi / 2):
            if chi == 0.0:
                d = JM.delta(0.0, th)
            else:
                d = JM.shadow_size(KN.critical_curve(chi, th, 2001), charm=False)["delta"]
            assert -0.08 <= d <= 1e-12, (chi, th, d)
            worst = min(worst, d)
    assert worst < -0.05  # the large-spin, edge-on shadows are visibly smaller


def test_shape_of_a_deformed_spinning_shadow():
    """A deformation changes the size (alpha13) and makes the shadow less circular at large spin (alpha22): the
    descriptors are computed and the circle of equal area lies between the extreme radii."""
    chi, th = 0.9, math.radians(60)
    base = JM.shadow_size(JM.shadow_curve(chi, th, JM.Deviation(), 2001))
    big = JM.shadow_size(JM.shadow_curve(chi, th, JM.Deviation(alpha13=3.0), 2001))
    assert big["median_diameter"] > base["median_diameter"]
    for s in (base, big):
        assert 0.5 * s["height_beta"] >= s["area_radius"] * 0.9 and s["diameter_spread"] < 0.1


def test_regularity_check():
    with pytest.raises(ValueError):
        JM.check_regular(0.0, JM.Deviation(alpha13=-8.5))  # A1 vanishes outside r+ = 2 (alpha13 > -r+^3 = -8)
    with pytest.raises(ValueError):
        JM.check_regular(0.5, JM.Deviation(alpha22=-3.6))  # alpha22 > -r+^2 = -3.48
    JM.check_regular(0.5, JM.Deviation(alpha13=-6.0, alpha22=-3.0))


@pytest.mark.parametrize("chi,kw", [(0.998, {"alpha22": 1.29}), (0.998, {"alpha22": 1.5}), (0.998, {"alpha22": 2.0}),
                                    (0.998, {"alpha22": 5.0}), (0.998, {"alpha22": 10.0}), (0.9, {"alpha22": 5.3}),
                                    (0.9, {"alpha22": 10.0}), (0.6, {"alpha13": -0.95}), (0.9, {"alpha13": -0.95}),
                                    (0.998, {"alpha13": -0.95}), (0.6, {"alpha12": -0.95}), (0.9, {"alpha12": -0.95}),
                                    (0.998, {"alpha12": -0.95})])
def test_singular_metrics_are_refused(chi, kw):
    """Review B5-K6: metrics whose determinant vanishes outside the horizon (Johannsen 2013a Eqs. 71-72:
    A1 (r^2 + a^2) - a^2 A2 sin^2 theta = 0 somewhere at r >= r+) are refused, at the reviewer's cases: every
    alpha22 > r+^4/a^2 with alpha12 = alpha13 = 0 (1.283 at a = 0.998, 5.248 at a = 0.9), alpha13 = -0.95 r+^3 and
    alpha12 = -0.95 r+^2 at a = 0.6, 0.9, 0.998 (the scale factors given as fractions of r+^3, r+^2)."""
    rp = KN.horizon(chi)
    kw = dict(kw)
    if "alpha13" in kw:
        kw["alpha13"] *= rp ** 3
    if "alpha12" in kw:
        kw["alpha12"] *= rp ** 2
    m = JM.regularity_margins(chi, JM.Deviation(**kw))
    assert m["det_eq72"] < 0 and m["A1"] > 0 and m["A2"] > 0  # the old check (A1, A2 > 0) passed them
    with pytest.raises(ValueError):
        JM.check_regular(chi, JM.Deviation(**kw))
    with pytest.raises(ValueError):
        JM.shadow_curve(chi, 1.0, JM.Deviation(**kw))


def test_the_alpha22_limit_of_equation_72():
    """With alpha12 = alpha13 = 0, Eq. (72) at sin theta = 1 is r^2 - a^2 alpha22/r^2 > 0, smallest at r+: the
    limit alpha22 < r+^4/a^2 (the check accepts 0.999 of it and refuses 1.001 of it)."""
    for chi in (0.6, 0.9, 0.998):
        lim = KN.horizon(chi) ** 4 / chi ** 2
        JM.check_regular(chi, JM.Deviation(alpha22=0.999 * lim))
        with pytest.raises(ValueError):
            JM.check_regular(chi, JM.Deviation(alpha22=1.001 * lim))


def test_shadow_size_both_centres():
    """Review B5-K5: the median diameter about the midpoint of the extreme alpha (default) and about CHARM's
    variance-minimising centre. For a circle (a = 0) they agree; for spinning shadows the CHARM centre has a smaller
    variance of the diameters and gives a smaller delta (measured values in shadow_size's docstring); the default
    reproduces Paper VI's Kerr range (test_kerr_shadows_are_within_the_quoted_range), the CHARM measure does not."""
    sz0 = JM.shadow_size(JM.shadow_curve(0.0, 1.0, JM.Deviation(alpha13=2.0)))
    # a circle sampled by 721 points: the chord lengths carry the polygon's error ~ (pi/720)^2 R/2 = 5e-5 M, so the
    # variance is flat to that level within ~1e-2 M of the centre and the median radius moves by the square of
    # that offset over R: |delta_charm - delta| <~ 1e-5
    assert abs(sz0["delta_charm"] - sz0["delta"]) <= 1e-5
    expected = {(0.9, 17.0): (-0.0523, -0.0565), (0.998, 90.0): (-0.0530, -0.1238)}
    for (chi, th), (d_ext, d_charm) in expected.items():
        cur = KN.critical_curve(chi, math.radians(th), 1441)
        sz = JM.shadow_size(cur)
        assert abs(sz["delta"] - d_ext) <= 5e-4 and abs(sz["delta_charm"] - d_charm) <= 5e-4
        ang = 2 * math.pi * np.arange(128) / 128
        al, be = np.append(cur["alpha"], cur["alpha"][0]), np.append(cur["beta"], cur["beta"][0])

        def var(cx):
            r = JM._radii(al, be, cx, ang)
            return float(np.var(r[:64] + r[64:]))
        assert var(sz["center_alpha_charm"]) < var(sz["center_alpha"])
        assert len(sz["charm_minima"]) >= 2  # the variance has a minimum on each side (stated in the docstring)
        assert JM.delta(chi, math.radians(th), centre="charm") == pytest.approx(sz["delta_charm"], abs=1e-12)
        assert JM.delta_vs_kerr(chi, math.radians(th), JM.Deviation()) == 0.0


def _mp_equatorial_isco(chi, a12, a13, a22, guess):
    """ISCO of the Johannsen metric by an independent route in 30 digits: the equatorial metric of Johannsen 2013a
    Eq. (51) written out here, the timelike radial function V(r) = -1 - (g^tt E^2 - 2 g^tphi E L + g^phiphi L^2) (the
    t-phi block inverted), and V = V' = V'' = 0 solved for (r, E, L) by findroot."""
    with mp.workdps(30):
        a = mp.mpf(chi)

        def V(r, E, L):
            A1 = 1 + a12 / r ** 2 + a13 / r ** 3
            A2 = 1 + a22 / r ** 2
            dl = r * r - 2 * r + a * a
            W = (r * r + a * a) * A1 - a * a * A2
            gtt = -r * r * (dl - a * a * A2 ** 2) / W ** 2
            gtp = -a * r * r * ((r * r + a * a) * A1 * A2 - dl) / W ** 2
            gpp = r * r * ((r * r + a * a) ** 2 * A1 ** 2 - a * a * dl) / W ** 2
            det = gtt * gpp - gtp ** 2
            itt, itp, ipp = gpp / det, -gtp / det, gtt / det
            return -1 - (itt * E * E - 2 * itp * E * L + ipp * L * L)
        sol = mp.findroot(lambda r, E, L: [V(r, E, L), mp.diff(lambda x: V(x, E, L), r),
                                           mp.diff(lambda x: V(x, E, L), r, 2)], [mp.mpf(g) for g in guess])
        return [float(sol[i]) for i in range(3)]


def test_circular_orbits_of_the_deviating_metric():
    """Review B5-K7: the deviating metric's own equatorial photon orbits and ISCO. Zero deviation: Kerr's closed
    forms (Bardeen, Press & Teukolsky 1972, kerr.photon_orbit and kerr.isco) to 1e-12; deviating metrics: the
    photon orbits equal the ends of the photon shell from R = R' = 0 (an independent route), at a = 0 the photon
    sphere of nonspinning_shadow; the ISCO, E and L against a 30-digit solution of V = V' = V'' = 0 (a second
    route through the inverse metric instead of Eq. 83's Omega): 1e-9 relative (the 1e-14 brentq tolerance in r
    enters E, L only at second order; r itself is conditioned by V'' ~ 0: about sqrt of the round-off)."""
    for chi in (0.0, 0.5, 0.9, 0.998):
        co = JM.circular_orbits(chi)
        for pro, nm in ((True, "pro"), (False, "retro")):
            assert abs(co[f"photon_{nm}"] - kerr.photon_orbit(chi, pro)) <= 1e-12 * kerr.photon_orbit(chi, pro)
            assert abs(co[f"isco_{nm}"] - kerr.isco(chi, pro)) <= 1e-12 * kerr.isco(chi, pro)
            e, l_ = kerr.circular_e_l(kerr.isco(chi, pro), chi, pro)
            assert abs(co[f"E_isco_{nm}"] - e) <= 1e-13 and abs(co[f"L_isco_{nm}"] - l_) <= 1e-12 * abs(l_)
    dev = JM.Deviation(alpha13=3.0)
    co = JM.circular_orbits(0.0, dev)
    assert abs(co["photon_pro"] - JM.nonspinning_shadow(dev)[1]) <= 1e-12 * co["photon_pro"]
    for chi, kw in ((0.9, dict(alpha13=2.0, alpha22=1.0)), (0.5, dict(alpha13=-1.5)), (0.7, dict(alpha12=0.4))):
        dev = JM.Deviation(**kw)
        co = JM.circular_orbits(chi, dev)
        lo, hi = JM.photon_shell(chi, dev)
        assert abs(co["photon_pro"] - lo) <= 1e-12 * lo and abs(co["photon_retro"] - hi) <= 1e-12 * hi
        for nm in ("pro", "retro"):
            r, E, L = _mp_equatorial_isco(chi, dev.a12, dev.a13, dev.a22,
                                          (co[f"isco_{nm}"], co[f"E_isco_{nm}"], co[f"L_isco_{nm}"]))
            assert abs(co[f"isco_{nm}"] - r) <= 1e-9 * r
            assert abs(co[f"E_isco_{nm}"] - E) <= 1e-12 and abs(co[f"L_isco_{nm}"] - L) <= 1e-12 * abs(L)


def test_ergosurface():
    """g_tt = 0 (Johannsen 2013a Eq. 69, Delta = a^2 A2^2 sin^2 theta): Kerr's 1 + sqrt(1 - a^2 cos^2 theta) at zero
    deviation (measured 2026-10-29: <= 3.1e-16 relative); at the poles it meets the horizon whatever alpha22 is; it
    grows with alpha22 at 0 < theta < pi (his Fig. 1) and does not depend on alpha13 (A1 does not enter); each value
    is a root of Eq. 69 to round-off."""
    th = np.linspace(0.0, math.pi, 13)
    for chi in (0.0, 0.5, 0.9, 0.998):
        r = JM.ergosurface(chi, JM.Deviation(), th)
        ref = 1.0 + np.sqrt(1.0 - chi ** 2 * np.cos(th) ** 2)
        assert np.all(np.abs(r - ref) <= 4 * 2.0 ** -53 * ref)
    rp = 1.0 + math.sqrt(1.0 - 0.81)
    r1, r2 = JM.ergosurface(0.9, JM.Deviation(alpha22=1.0), th), JM.ergosurface(0.9, JM.Deviation(alpha22=2.0), th)
    assert abs(r1[0] - rp) <= 1e-15 and abs(r2[-1] - rp) <= 1e-15
    assert np.all(r2[1:-1] > r1[1:-1]) and np.all(r1[1:-1] > JM.ergosurface(0.9, JM.Deviation(), th)[1:-1])
    assert np.array_equal(JM.ergosurface(0.9, JM.Deviation(alpha13=2.0), th), JM.ergosurface(0.9, JM.Deviation(), th))
    a, A2 = 0.9, JM.Deviation(alpha22=2.0).A2
    f = r2 * r2 - 2 * r2 + a * a - a * a * A2(r2) ** 2 * np.sin(th) ** 2
    scale = r2 * r2 + 2 * r2 + a * a + a * a * A2(r2) ** 2
    assert np.all(np.abs(f) <= 16 * 2.0 ** -53 * scale)
    assert isinstance(JM.ergosurface(0.9, JM.Deviation(), 1.0), float)


def test_circular_orbits_where_omega_squared_is_negative():
    """Review UX-params P6: a band without circular geodesics (Omega^2 < 0, e.g. a = 0, alpha12 = -3, alpha13 = -1.399,
    alpha22 = 3.612 between 2.1 M and 4.6 M) gave a complex Omega for a real r, and the ISCO search returned a complex
    E (float() crashed v15). Now the band reads NaN, and the ISCO is the outer edge of the band (kind "existence"),
    against a 40-digit route (g_tt' = 0 at a = 0: Omega = 0, E = sqrt(-g_tt)). Negative control: Kerr and the
    existing deviations keep kind "stability" and their values (test above)."""
    dev = JM.Deviation(-3.0, -1.399, 3.612)
    assert all(math.isnan(x) for x in JM._circular(3.0, 0.0, dev, True))
    co = JM.circular_orbits(0.0, dev)
    with mp.workdps(40):
        gtt = lambda r: -(1 - 2 / r) / (1 + mp.mpf(-3) / r ** 2 + mp.mpf("-1.399") / r ** 3) ** 2  # noqa: E731
        r0 = mp.findroot(lambda r: mp.diff(gtt, r), 4.6)
        e0 = mp.sqrt(-gtt(r0))
    for nm in ("pro", "retro"):
        assert co[f"isco_kind_{nm}"] == "existence"
        assert co[f"isco_{nm}"] == pytest.approx(float(r0), rel=1e-13)
        assert co[f"E_isco_{nm}"] == pytest.approx(float(e0), rel=1e-13)
    assert co["photon_pro"] == pytest.approx(JM.nonspinning_shadow(dev)[1], rel=1e-12)
    for chi in (0.0, 0.9):
        assert JM.circular_orbits(chi)["isco_kind_pro"] == "stability"
    assert JM.circular_orbits(0.9, JM.Deviation(alpha13=2.0, alpha22=1.0))["isco_kind_retro"] == "stability"


def test_admissible_intervals():
    """The values one deviation may take, the others fixed (review UX-params P6: what v15's refusal names): at a = 0
    alpha13 > -r+^3 = -8 exactly (A1 > 0 at the horizon decides), within the bisection's tolerance; each end is the edge
    of ``shadow_computable`` (inside builds, 1e-3 outside does not)."""
    (lo, hi), = JM.admissible_intervals(0.0, "alpha13", {}, -10.0, 10.0)
    assert lo == pytest.approx(-8.0, abs=1.5e-4) and hi == 10.0
    for chi, key in ((0.9, "alpha13"), (0.9, "alpha22"), (0.998, "alpha13")):
        for a, b in JM.admissible_intervals(chi, key, {}, -10.0, 10.0):
            for end, out in ((a, a - 1e-3), (b, b + 1e-3)):
                assert JM.shadow_computable(chi, JM.Deviation(**{key: end})) is None
                if -10.0 < out < 10.0:
                    assert JM.shadow_computable(chi, JM.Deviation(**{key: out})) is not None
