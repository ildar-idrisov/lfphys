# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The Debye series (lfphys.core.optics.mie_debye) and the rainbow of ray optics and Airy's theory
(lfphys.theories.approx.rainbow):

* the Debye series summed in closed form equals the Mie coefficients computed by a different route (mie: D_n(mx)
  downward, Miller's psi, upward chi; here: Hankel-function ratios, logarithms), for transparent, absorbing, m < 1
  and large spheres, within the derived u (1000 N + 32 x |da_n/dx|) (mie_debye.check_against_mie; review B8-mie, M4),
  also on narrow resonance peaks; negative controls: a wrong D_n, psi_n or chi_n of the engine fails the check;
  partial sums plus the closed-form remainder too, also where the series diverges (|R11| > 1, absorbing m near 1,
  flagged; M5); the p = 2 term's peak converges to Airy's maximum for large x, beyond Descartes' angle by Airy's
  offset ~ x^(-2/3);
* ray optics: Descartes' angle is the extremum of the deviation (numerically), the ray paths leave at the deviation
  angle, Airy's intensity averages to the two classical rays on the bright side, Alexander's band.
"""

import math

import numpy as np
import pytest
from scipy.signal import argrelmax

from lfphys.core.optics import mie, mie_debye as dbe
from lfphys.theories.approx import rainbow as rb


DEBYE_CASES = [(1.333, 10.0), (1.333, 500.0), (1.333 + 1e-9j, 3000.0), (1.5 + 0.1j, 100.0), (1.5 + 0.01j, 1000.0),
               (0.75, 50.0), (0.75, 1000.0), (2.0 + 1.0j, 30.0), (10 + 10j, 100.0), (1.5, 1.0), (1.333, 1e4),
               (0.75, 1e4), (0.75, 16535.0), (2.0, 100.0), (2.879237407580798, 6410.882296), (3.0, 19900.0),
               (1.5 + 0.5j, 2000.0), (2 + 2j, 5000.0), (1.333, 1000.6795370463041), (1.333, 1000.4647488523628)]


@pytest.mark.parametrize("m,x", DEBYE_CASES)
def test_debye_sum_equals_mie(m, x):
    """(1 - R22 - T21 T12/(1 - R11))/2 = a_n (and b_n) for every order within u (1000 N + 32 s) of the largest
    coefficient, s = x |da_n/dx|/max|a| (mie_debye.ACCURACY: the floor measured <= 453 N u over 281 cases — 14 m from
    0.5 to 10 + 10i at x = 10 ... 19900, 150 random (m, x) and the resonance peaks; the conditioning term covers the
    peaks, where the two routes differ by up to 5.6e-4 (the last case, Gamma = 1.5e-11)). [error in earlier] v17's
    fixed 5e-10 failed for m = 0.75 at x >= 16535 (8.6e-10), and the Debye route lost up to 5e-9 at single orders where
    D_n has a pole (m = 2 at x = 100: 206 N u; m = 2.88 at x = 6411: 4632 N u; now 5 and 176 N u, D_n p_n formed without
    D_n). Partial sums p = 0..4 plus the closed-form remainder within the same tolerance times the series'
    amplification. Negative control: dropping the internal waves (p >= 1) misses a_n by far more."""
    r = dbe.check_against_mie(m, x)
    assert r["ok"], (r["worst"], int(np.argmax(r["err"] / r["tol"])) + 1)
    c = dbe.coefficients(m, x, p_max=4)
    a, b = mie.coefficients(m, x, n_max=c["N"])
    s = max(np.abs(a).max(), np.abs(b).max())
    assert c["underflow"] == 0
    amp = max(1.0, c["amplification"])
    for key, ref in (("a", a), ("b", b)):
        assert np.all(np.abs(c[key].sum(0) + c["remainder_" + key] - ref) <= r["tol"] * amp * s)
    if complex(m).imag < 0.5:
        assert np.any(np.abs(c["a"][0] - a) > 1e3 * r["tol"] * s)


@pytest.mark.parametrize("part", ["D", "psi", "chi", "D(mx)"])
def test_debye_check_detects_a_wrong_engine(monkeypatch, part):
    """The check's purpose (v17 shows it as the check of the coefficients): an engine whose D_n, psi_n or chi_n is
    wrong by 1e-3 (D(mx): D_n wrong only at the argument m x) fails it, at m = 1.3354, x = 300 (review B8-mie s10: the
    optical theorem and the energy identity stay at round-off for all four)."""
    m, x = 1.3354, 300.0
    assert dbe.check_against_mie(m, x)["ok"]
    if part == "D":
        orig = mie.log_derivative
        monkeypatch.setattr(mie, "log_derivative", lambda z, N: orig(z, N) * (1 + 1e-3))
    elif part == "D(mx)":
        orig = mie.log_derivative
        monkeypatch.setattr(mie, "log_derivative", lambda z, N: orig(z, N) * (
            1.0 if np.allclose(np.atleast_1d(np.asarray(z)), x) else 1 + 1e-3))
    elif part == "psi":
        orig = mie.psi
        monkeypatch.setattr(mie, "psi", lambda z, N: orig(z, N) * (1 + 1e-3 * np.arange(N + 1) / N).reshape(
            (-1,) + (1,) * np.ndim(np.atleast_1d(z))))
    else:
        orig = mie.chi
        monkeypatch.setattr(mie, "chi", lambda xx, N: orig(xx, N) * (1 + 1e-3))
    r = dbe.check_against_mie(m, x)
    assert not r["ok"] and r["worst"] > 1e3


def test_debye_terms_where_the_series_diverges():
    """Absorbing m near 1 (review B8-mie, M5): m = 1 + 1e-6 i at x = 100 has |R11| up to 4.8 on 21 tunnelling
    orders: they are flagged ("diverges"), the terms reach ~1e7 times the largest Mie coefficient ("amplification"),
    and the partial sums plus the remainder still equal the closed form within round-off of the terms (R11^p taken
    from the cancellation-free 1 - R11). Negative control: with R11 taken directly (as before), they missed b_117 by
    5e-4 of the largest coefficient. A real m near 1 does not diverge but its terms p = 0, 1 cancel (amplification
    ~50 for m = 1.0001); a water drop has neither."""
    m, x = 1.0 + 1e-6j, 100.0
    c = dbe.coefficients(m, x, p_max=4)
    it = dbe.interface_terms(m, x)
    a, b = mie.coefficients(m, x, n_max=c["N"])
    s = max(np.abs(a).max(), np.abs(b).max())
    div = c["diverges_a"] | c["diverges_b"]
    assert 15 <= div.sum() <= 30 and np.all(np.flatnonzero(div) + 1 > x)
    assert c["amplification"] > 1e6
    tol = 64 * c["N"] * mie.U * c["amplification"] * s
    miss = 0.0
    for key, ref in (("a", a), ("b", b)):
        assert np.all(np.abs(c[key].sum(0) + c["remainder_" + key] - ref) <= tol)
        R11 = it[key]["R11"]  # the direct form: the old remainder
        TT = it[key]["TT"]
        old = 0.5 * it[key]["one_minus_R22"] - 0.5 * TT * (1 + R11 + R11 ** 2 + R11 ** 3) \
            - 0.5 * TT / it[key]["one_minus_R11"] * R11 ** 4
        miss = max(miss, float(np.abs(old - ref).max()))
    assert miss > 1e-5 * s > tol
    c2 = dbe.coefficients(1.0001, 100.0, p_max=3)
    assert not (c2["diverges_a"].any() or c2["diverges_b"].any()) and 10 < c2["amplification"] < 1e3
    c3 = dbe.coefficients(1.3354, 1714.0, p_max=3)
    assert not (c3["diverges_a"].any() or c3["diverges_b"].any()) and c3["amplification"] < 2.0


def test_debye_route_at_the_poles_of_D_against_40_digits():
    """The Debye route itself at m = 2, x = 100 against the 40-digit Mie reference: every order within 16 N u of the
    largest coefficient (measured 4.7 N u; before review B8-mie M4, 206 N u at n = 59, a pole of D_59(mx)). Negative
    control: an error of 100 N u at that order exceeds the tolerance."""
    from test_mie import _ref_mp_recurrence
    m, x = 2.0, 100.0
    c = dbe.coefficients(m, x, p_max=0)
    N = c["N"]
    ra, rb = _ref_mp_recurrence(m, x, N, dps=40)
    s = max(np.abs(ra).max(), np.abs(rb).max())
    e = np.maximum(np.abs(c["sum_a"] - ra), np.abs(c["sum_b"] - rb)) / s
    tol = 16 * N * mie.U
    assert np.all(e <= tol), (e.max() / (N * mie.U), int(np.argmax(e)) + 1)
    e2 = e.copy()
    e2[58] += 100 * N * mie.U
    assert e2.max() > tol


def test_debye_series_converges_where_internal_reflection_is_weak():
    """Where |R11| <= 0.5 the partial sums converge geometrically: up to p = 60 they reach a_n within 1e-12 there
    (the remainder <= |T21 T12| 0.5^60 / 0.5)."""
    m, x = 1.333, 30.0
    c = dbe.coefficients(m, x, p_max=60)
    it = dbe.interface_terms(m, x)
    a, _ = mie.coefficients(m, x, n_max=c["N"])
    weak = np.abs(it["a"]["R11"]) <= 0.5
    assert weak.sum() > 10
    assert np.abs(c["a"].sum(0)[weak] - a[weak]).max() <= 1e-12 * np.abs(a).max()


def test_debye_reflection_limits():
    """Far beyond the sphere (n >> x) the partial wave is reflected whole (R22 -> 1) and nothing enters; for an
    opaque metal-like sphere (|m| large) R22 -> 1 too while the p >= 1 terms vanish; |R22| <= 1 always."""
    it = dbe.interface_terms(1.333, 50.0)
    R22 = it["a"]["R22"]
    assert abs(abs(R22[-1]) - 1.0) < 1e-12 and np.all(np.abs(R22) <= 1 + 1e-12)
    it2 = dbe.interface_terms(3.0 + 5.0j, 50.0)
    assert np.abs(it2["a"]["TT"]).max() < 1e-30


@pytest.mark.parametrize("x", [1000.0, 3000.0, 10000.0])
def test_p2_peak_approaches_descartes_with_airys_offset(x):
    """The main maximum of |S1^(2)|^2 (Debye p = 2, perpendicular polarisation, m = 1.333) lies beyond Descartes'
    angle by Airy's offset a'_1 (h/2)^(1/3) x^(-2/3): measured offsets 0.977, 0.4735, 0.2131 deg against Airy's
    0.9914, 0.4766, 0.2136 deg; the remaining difference falls faster than the offset (~x^(-4/3)): within 2 % of the
    offset at x = 1000, 1 % at 3000 and 0.5 % at 10^4 (measured 1.5 %, 0.65 %, 0.24 %). The supernumerary maxima
    follow Airy's within 5 % of their offsets. Negative control: Descartes' angle itself is off by the whole offset."""
    m = 1.333
    d = rb.descartes(m, 2)
    am = rb.airy_maxima(m, 2, x, 3)
    off = am[0] - d["theta"]
    th = d["theta"] + np.linspace(-0.5, 6.0, 13001) * off
    c = dbe.coefficients(m, x, p_max=2)
    S1, _ = mie.amplitudes(c["a"][2], c["b"][2], th)
    I1 = np.abs(S1) ** 2
    k = int(np.argmax(I1))
    tol = {1000.0: 0.02, 3000.0: 0.01, 10000.0: 0.005}[x]
    assert abs(th[k] - am[0]) <= tol * off + (th[1] - th[0])
    assert abs(th[k] - d["theta"]) > 10 * tol * off  # negative control
    mx = argrelmax(I1, order=40)[0]
    for j in (1, 2):
        assert abs(th[mx[j]] - am[j]) <= 0.05 * (am[j] - d["theta"])
    # Airy's peak value within 2.5 % (measured: Debye/Airy = 0.981, 0.991, 0.996)
    A = rb.airy(m, 2, x, th, "s")
    assert abs(I1[k] / A.max() - 1.0) <= 0.025


def test_airy_averages_to_classical_rays():
    """Far from the rainbow on its bright side Airy's Ai^2(-z) averaged over a period equals the classical intensity
    of the two rays near the rainbow ray (the normalisation 2 pi |eps|^2 (b/sin theta) x^(7/3) (2/h)^(2/3)): checked
    where the quadratic expansion of theta(b) still holds (z ~ 20-40), within the size of the cubic term."""
    m, x = 1.333, 1e5
    d = rb.descartes(m, 2)
    h = d["h"]
    zs = np.linspace(20.0, 40.0, 40001)
    th = d["theta"] + zs / ((2.0 / h) ** (1.0 / 3.0) * x ** (2.0 / 3.0))
    A = rb.airy(m, 2, x, th, "s")
    # the classical intensity of the two rays of the same quadratic model: x^2 eps^2 b/(sin theta) * 2/sqrt(2 h dth)
    dth = th - d["theta"]
    C = x * x * float(rb.eps2(m, 2, d["b"], "s")) * d["b"] / math.sin(d["theta"]) * 2.0 / np.sqrt(2.0 * h * dth)
    ratio = np.trapezoid(A, zs) / np.trapezoid(C, zs)
    assert abs(ratio - 1.0) <= 0.01, ratio
    # and the exact ray optics there (both rays, Fresnel factors at their own b) within the model's error ~ dth
    tc = th[len(th) // 2]
    cl = rb.classical(m, 2, x, np.array([tc]), "s")[0]
    assert abs(C[len(th) // 2] / cl - 1.0) <= 0.05


def test_descartes_angle_is_the_extremum_of_the_deviation():
    for m in (1.333, 4 / 3, 1.5):
        for p in (2, 3, 4):
            d = rb.descartes(m, p)
            # the extremum near b_R (elsewhere theta folds at 0 or pi where D crosses a multiple of pi)
            bs = np.linspace(max(1e-6, d["b"] - 0.05), min(1 - 1e-9, d["b"] + 0.05), 200001)
            th = rb.scattering_angle(rb.deviation(m, p, bs))
            k = int(np.argmin(th)) if d["h"] > 0 else int(np.argmax(th))
            assert abs(bs[k] - d["b"]) <= 2e-6
            assert abs(th[k] - d["theta"]) <= 1e-9
            # h by finite differences
            e = 1e-4
            f = [float(rb.scattering_angle(rb.deviation(m, p, d["b"] + s * e))) for s in (-1, 0, 1)]
            assert abs((f[0] - 2 * f[1] + f[2]) / e ** 2 - d["h"]) <= 1e-4 * abs(d["h"])
    assert math.degrees(rb.descartes(4 / 3, 2)["theta"]) == pytest.approx(137.97, abs=0.005)
    with pytest.raises(ValueError):
        rb.descartes(2.5, 2)  # no primary rainbow for m >= 2


def test_alexander_band_and_ray_paths():
    m = 1.333
    t3, t2 = rb.alexander_band(m)
    assert t3 < t2  # the secondary bow at smaller scattering angle: outside the primary around the antisolar point
    for p in (2, 3):
        bs = np.linspace(1e-6, 1 - 1e-9, 20001)
        th = rb.scattering_angle(rb.deviation(m, p, bs))
        assert not np.any((th > t3 + 1e-12) & (th < t2 - 1e-12))  # no rays of p = 2, 3 inside the band
    for p in (0, 1, 2, 3, 4):
        for b in (0.1, 0.5, 0.86, 0.95):
            path = rb.ray_path(m, p, b)
            assert np.allclose(np.hypot(path[1:-1, 0], path[1:-1, 1]), 1.0)  # the vertices on the sphere
            t = path[-1] - path[-2]
            t /= np.linalg.norm(t)
            assert abs(math.acos(np.clip(t[1], -1, 1)) - float(rb.scattering_angle(rb.deviation(m, p, b)))) < 1e-12


def test_fresnel_energy_of_the_rays():
    """|eps|^2 of all orders sums to 1 for a non-absorbing sphere (ray energy is conserved)."""
    for b in (0.0, 0.3, 0.86, 0.99):
        for pol in ("s", "p"):
            tot = sum(float(rb.eps2(1.333, p, b, pol)) for p in range(0, 400))
            assert abs(tot - 1.0) < 1e-12


def test_ray_paths_for_m_below_1():
    """A sphere of m < 1 (an air bubble in water, m = 0.75): the rays of p >= 1 enter only for b < m (v17 draws the
    drop's own rays; review B8-mie, M11) and leave at the deviation angle; b >= m is refused for p >= 1, while the
    reflection p = 0 exists for every b."""
    m = 0.75
    for p in (0, 1, 2, 3):
        for b in (0.1, 0.4, 0.7):
            path = rb.ray_path(m, p, b)
            assert np.allclose(np.hypot(path[1:-1, 0], path[1:-1, 1]), 1.0)
            t = path[-1] - path[-2]
            t /= np.linalg.norm(t)
            assert abs(math.acos(np.clip(t[1], -1, 1)) - float(rb.scattering_angle(rb.deviation(m, p, b)))) < 1e-12
    rb.ray_path(m, 0, 0.9)
    with pytest.raises(ValueError):
        rb.ray_path(m, 1, 0.8)
