# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The Mie series (lfphys.core.optics.mie) against closed forms and independent routes:

* the coefficients against the textbook formula with Bessel functions in ball arithmetic (Arb, python-flint) or in
  50-digit mpmath (a different formula: B&H Eq. 4.53 without the logarithmic derivative), and at x = 10^4 against
  the same recurrences in 60-digit mpmath;
* Wiscombe's published test cases (NCAR/TN-140, 1979: Appendix III and Table 3) at their printed precision;
* the coefficients' accuracy as a mixed forward-backward bound (mie.ACCURACY): every order within
  u (4 N max|a| + 8 x |da_n/dx|) of 50-digit references with their derivatives, also on narrow resonance peaks where
  the forward error reaches 6e-3 (review B8-mie, M1); the start of D_n by Hankel's sums and log_psi against Bessel
  functions (M10);
* the Rayleigh limit, Q_abs from the internal field integrated over the volume, the extinction paradox, the perfect
  conductor's limits;
* identities of the series' structure, labelled as such (review B8-mie, M3): the optical theorem in the form
  Q_ext = (4/x^2) Re S(0) holds for any coefficients (pi_n(1) = tau_n(1) = n(n+1)/2: it checks the angular functions at
  theta = 0), and Q_sca = Q_ext of a non-absorbing sphere holds for any coefficients of the form A/(A - iB) with real A,
  B (Re a_n = |a_n|^2 whatever D_n, psi_n, chi_n are): the quadrature over angles (Fejér's second rule, M2) checks the
  angular functions, the sums S1, S2 and the quadrature, not the coefficients;
* the near field: tangential E and H and normal D continuous at the surface, the scattered field's far limit equal
  to S1, S2, the series of the incident wave equal to the plane wave;
* identities of the Mueller matrix (true for any S1, S2) and the angular functions against scipy's associated
  Legendre functions; the polarised far-field intensity against the near field far away.
Negative controls show that the tolerances can fail.
"""

import math

import mpmath as mp
import numpy as np
import pytest
from scipy import special

from lfphys.core.optics import mie

EPS = np.finfo(float).eps


# --- references ---------------------------------------------------------------------------------------------------
def _ref_arb(m, x, n):
    """a_n, b_n by B&H Eq. 4.53 with j_n, y_n of Arb (python-flint) at increasing precision until the balls are
    narrower than 1e-30 relative."""
    from flint import acb, arb, ctx
    old = ctx.prec
    try:
        for prec in (200, 400, 800, 1600, 3200):
            ctx.prec = prec
            mm, xx = acb(m.real, m.imag), acb(x)

            def rb(nn, z):
                f = (acb.pi() / (2 * z)).sqrt()
                nu = arb(nn) + arb(1) / 2
                j, y = z * f * z.bessel_j(nu), z * f * z.bessel_y(nu)
                return j, j + 1j * y

            def d(nn, z):
                p, q = rb(nn, z)
                p1, q1 = rb(nn - 1, z)
                return p, p1 - nn / z * p, q, q1 - nn / z * q
            p, dp, q, dq = d(n, xx)
            pm, dpm, _, _ = d(n, mm * xx)
            a = (mm * pm * dp - p * dpm) / (mm * pm * dq - q * dpm)
            b = (pm * dp - mm * p * dpm) / (pm * dq - mm * q * dpm)
            ca = complex(float(a.real.mid()), float(a.imag.mid()))
            cb = complex(float(b.real.mid()), float(b.imag.mid()))
            rad = max(float(a.real.rad() + a.imag.rad()) / max(abs(ca), 1e-300),
                      float(b.real.rad() + b.imag.rad()) / max(abs(cb), 1e-300))
            if rad < 1e-30:
                return ca, cb
    finally:
        ctx.prec = old
    raise RuntimeError("no Arb reference")


def _ref_mp_recurrence(m, x, N, dps=60):
    """a_n, b_n, n = 1..N, by the textbook recurrences in mpmath: D_n(mx) downward from D = 0 at
    N + |mx| + 20 |mx|^(1/3) + 60, psi_n(x) downward (Miller) normalised to sin x, chi_n(x) upward; for the largest x,
    where Arb's Bessel functions of large order do not converge (a check of rounding, not of the formula, which the
    other references check). The start lies far enough above |mx| for its error to decay below 1e-40 before the
    recurrence turns oscillatory at n ~ |mx| (the decay over t |z|^(1/3) orders is ~exp(-(2/3)(2t)^(3/2)), t = 20
    gives e^-150); [error in earlier] it was N + |mx| + 50, which is not enough when |mx| >> N (3.6e-5 off at
    m = 1e5, x = 0.5; review B8-mie, M9)."""
    with mp.workdps(dps):
        a, b = _ref_mp_recurrence_mp(m, mp.mpf(x), N, dps)
        return np.array([complex(v) for v in a]), np.array([complex(v) for v in b])


def _ref_mp_recurrence_mp(m, x, N, dps):
    """As ``_ref_mp_recurrence`` for an mpmath x (not rounded to binary64), returning mpmath numbers."""
    with mp.workdps(dps):
        m = mp.mpc(m)
        mx = m * x
        top = N + int(abs(complex(mx))) + int(20 * abs(complex(mx)) ** (1.0 / 3.0)) + 60
        D, Dx = mp.mpc(0), mp.mpf(0)
        Dm, Dxs = [None] * (N + 1), [None] * (N + 2)
        for n in range(top, 0, -1):
            if n <= N:
                Dm[n] = D
            if n <= N + 1:
                Dxs[n] = Dx
            D = n / mx - 1 / (D + n / mx)
            Dx = n / x - 1 / (Dx + n / x)
        P = [mp.mpf(0)] * (N + 1)
        P[N] = mp.mpf(1)
        for n in range(N, 0, -1):
            P[n - 1] = P[n] * (Dxs[n] + n / x)
        s0, s1 = mp.sin(x), mp.sin(x) / x - mp.cos(x)
        sc = s0 / P[0] if abs(s0) >= abs(s1) else s1 / P[1]
        P = [p * sc for p in P]
        X = [mp.cos(x)]
        prev = -mp.sin(x)
        for n in range(1, N + 1):
            X.append((2 * n - 1) / x * X[-1] - prev)
            prev = X[-2]
        a, b = [], []
        for n in range(1, N + 1):
            xi, xi1 = P[n] - 1j * X[n], P[n - 1] - 1j * X[n - 1]
            ta, tb = Dm[n] / m + n / x, Dm[n] * m + n / x
            a.append((ta * P[n] - P[n - 1]) / (ta * xi - xi1))
            b.append((tb * P[n] - P[n - 1]) / (tb * xi - xi1))
        return a, b


# --- coefficients against independent references -------------------------------------------------------------------
CASES = [  # (m, x, orders checked)
    (1.33, 1e-3, [1, 2]), (1.5 + 0.1j, 1.0, [1, 3, 6]), (1.33, 50.0, [1, 25, 50, 70]),
    (1.5 + 1j, 100.0, [1, 60, 120]), (10 + 10j, 30.0, [1, 15, 40]), (0.75, 30.0, [1, 22, 40]),
    (1.33 + 1e-8j, 1000.0, [1, 700, 1000, 1040]), (1.33, 1e-6, [1, 2]),
]


@pytest.mark.parametrize("m,x,orders", CASES)
def test_coefficients_against_arb(m, x, orders):
    """Every coefficient checked within 1e-12 of the largest coefficient (measured: <= 3.2e-13 at x = 1000,
    <= 1.8e-15 at x <= 100); the largest ones (n < x) also relatively."""
    a, b = mie.coefficients(m, x)
    scale = max(np.abs(a).max(), np.abs(b).max())
    for n in orders:
        ra, rb = _ref_arb(complex(m), x, n)
        assert abs(a[n - 1] - ra) <= 1e-12 * scale, (n, a[n - 1], ra)
        assert abs(b[n - 1] - rb) <= 1e-12 * scale, (n, b[n - 1], rb)
        if n < x:
            assert abs(a[n - 1] - ra) <= 1e-10 * abs(ra) and abs(b[n - 1] - rb) <= 1e-10 * abs(rb)


def test_coefficients_small_x_relative_accuracy():
    """At x = 1e-3 a_1 is exact to round-off; b_1 ~ x^5 comes from a cancellation of O(x) terms, relative error
    ~ eps/x^2 (measured 1.6e-9), absolute 1.9e-16 of a_1: harmless for every quantity (b_1/a_1 ~ x^2)."""
    a, b = mie.coefficients(1.33, 1e-3)
    ra, rb = _ref_arb(1.33 + 0j, 1e-3, 1)
    assert abs(a[0] - ra) <= 4 * EPS * abs(ra)
    assert abs(b[0] - rb) <= 100 * EPS / 1e-6 * abs(rb)


def _ref_with_sensitivity(m, x, N, dps=50, h=1e-22):
    """The references a_n, b_n (``_ref_mp_recurrence``) and the sensitivities x |da_n/dx|, x |db_n/dx| of the exact
    coefficients, by a forward difference with relative step h in dps-digit arithmetic (truncation ~h x/Gamma relative
    for a resonance of width Gamma: 1e-8 at Gamma = 1e-11, x = 1000; rounding 10^-dps/h)."""
    with mp.workdps(dps):
        x0 = mp.mpf(x)
        a0, b0 = _ref_mp_recurrence_mp(m, x0, N, dps)
        a1, b1 = _ref_mp_recurrence_mp(m, x0 * (1 + mp.mpf(h)), N, dps)
        sa = np.array([float(abs((u - v) / h)) for u, v in zip(a1, a0)])
        sb = np.array([float(abs((u - v) / h)) for u, v in zip(b1, b0)])
        return np.array([complex(v) for v in a0]), np.array([complex(v) for v in b0]), sa, sb


def _errors_and_bound(m, x, dps=50):
    """Per order: the engine's error |a_n - exact| (max over a, b) and the stated bound, both / max|exact|."""
    a, b = mie.coefficients(m, x)
    ra, rb, sa, sb = _ref_with_sensitivity(m, x, len(a), dps=dps)
    amax = max(np.abs(ra).max(), np.abs(rb).max())
    err = np.maximum(np.abs(a - ra), np.abs(b - rb)) / amax
    sens = np.maximum(sa, sb) / amax
    return err, mie.coefficient_bound(x, sens), sens, (a, b, ra, rb, amax)


# (m, x): absorbing, transparent, m < 1, large |m|, x = 1e-3 ... 1e4 (review B8-mie, M1; measured F <= 1 with K = 4)
BOUND_CASES = [(1.33, 1e-3), (1.5 + 0.1j, 1.0), (1.33, 50.0), (1.5 + 1j, 100.0), (10 + 10j, 30.0), (0.75, 30.0),
               (1.33 + 1e-8j, 1000.0), (1.333, 1000.0), (1.5, 1000.0), (1.5 + 0.1j, 1000.0), (0.75, 1000.0),
               (1.333, 3000.0), (10 + 10j, 1000.0), (4 + 0.01j, 1000.0), (1.05, 3000.0), (0.5, 3000.0),
               (1.5 + 1e-4j, 3000.0), (1.3354, 300.0), (2.0, 500.0), (3.0, 200.0), (1.33 + 0.01j, 1e4), (1.333, 1e4)]


@pytest.mark.parametrize("m,x", BOUND_CASES)
def test_every_coefficient_within_the_stated_bound(m, x):
    """All orders against 50-digit recurrences: |a_n - exact| <= u (4 N max|a| + 8 x |da_n/dx|) (mie.ACCURACY);
    measured: within half the bound with F = 1, K = 4."""
    err, bound, sens, _ = _errors_and_bound(m, x)
    half = mie.U * (1.0 * mie.n_terms(x) + 4.0 * sens)
    assert np.all(err <= bound), (np.max(err / bound), int(np.argmax(err / bound)) + 1)
    assert np.all(err <= half)


# Resonance peaks of m = 1.333 near x = 1000 (TE orders n; located by bisection of the real part of b_n's
# denominator, review B8-mie s05b): widths Gamma in x from 6.3e-4 down to 1.5e-11
PEAKS = [(1023, 1000.1056989418499, 6.3e-4), (1037, 1000.4288438876538, 1.0e-6), (1046, 1000.2155243892129, 5.7e-9),
         (1051, 1000.4647488523628, 3.2e-10), (1056, 1000.6795370463041, 1.5e-11)]


@pytest.mark.parametrize("n,x,gamma", PEAKS)
def test_the_bound_holds_on_resonance_peaks(n, x, gamma):
    """On the peak of a narrow resonance the forward error is the problem's conditioning, ~u x/Gamma (6.4e-3 at
    Gamma = 1.5e-11), and the bound with the coefficient's own sensitivity still holds: the engine is backward
    stable in x. Negative controls: [error in earlier] the blanket bound 2e-11 stated before review B8-mie (M1) fails
    on the three narrowest peaks; the floor alone (the bound without the sensitivity) fails on all but the widest;
    and an engine whose x is off by 256 units in the last place fails the bound at the peak (K = 8 is not loose)."""
    m = 1.333
    err, bound, sens, (a, b, ra, rb, amax) = _errors_and_bound(m, x)
    k = n - 1
    assert abs(abs(rb[k]) - 1.0) < 0.01  # on the peak: |b_n| = 1 (b_n = A/(A - iB), B = 0)
    assert np.all(err <= bound)
    assert err[k] > 0.05 * mie.U * x / gamma  # the forward error is the conditioning, not round-off
    if gamma < 1e-8:
        assert err[k] > 2e-11  # the old blanket bound fails here
    if gamma < 1e-5:
        assert err[k] > mie.coefficient_bound(x)  # the floor alone fails
    xs = x
    for _ in range(256):
        xs = math.nextafter(xs, 2e3)
    a2, b2 = mie.coefficients(m, xs, n_max=len(a))
    assert abs(b2[k] - rb[k]) / amax > bound[k]


def test_coefficients_batch_equal_single():
    xs = np.array([3.0, 3.5, 7.0, 20.0, 21.0])
    A, B = mie.coefficients_batch(1.33 + 0.001j, xs)
    for k, x in enumerate(xs):
        a, b = mie.coefficients(1.33 + 0.001j, x, n_max=mie.n_terms(x))
        n = len(a)
        assert np.allclose(A[k, :n], a, rtol=1e-13, atol=1e-15 * np.abs(a).max())
        assert np.allclose(B[k, :n], b, rtol=1e-13, atol=1e-15 * np.abs(b).max())
        assert np.all(A[k, n:] == 0) and np.all(B[k, n:] == 0)


def test_absorbing_sign_convention_is_enforced():
    with pytest.raises(ValueError):
        mie.coefficients(1.5 - 0.1j, 10.0)


# --- Wiscombe's published tables (NCAR/TN-140+STR, 1979) ----------------------------------------------------------
# Appendix III (MIEV1 results printed to 6 significant digits), his m = n - i kappa (exp(+i omega t)): our m is its
# complex conjugate and our S its complex conjugate (sources/verification_2026-11-04_p1_mie.md).
WISCOMBE = [  # x, m (his), Qext, Qsca, g, S1(0), S1(90), S2(90), S1(180)
    (10, 1.5, 2.881999, 2.881999, 0.742913, 72.0500 + 4.16662j, 0.0785066 + 3.06855j, -1.87329 + 2.32789j,
     4.32164 + 4.86827j),
    (100, 1.5, 2.094388, 2.094388, 0.818246, 5235.97 - 367.988j, 22.4945 + 0.396468j, 16.2341 - 15.5243j,
     40.7669 + 51.7546j),
    (1000, 1.5, 2.013945, 2.013945, 0.827882, 503486 - 8361.82j, 4.25817 - 156.554j, -157.646 - 17.4914j,
     565.233 + 1502.09j),
    (5000, 1.5, 2.008650, 2.008650, 0.829592, 1.25541e7 - 67229.4j, 762.792 + 466.846j, 384.561 - 433.204j,
     -14562.5 - 5071.55j),
    (10, 1.5 - 0.1j, 2.459791, 1.235144, 0.922350, 61.4948 - 3.17799j, 1.35105 + 0.417250j, -1.02255 + 0.791253j,
     1.49343 + 0.296366j),
    (100, 1.5 - 0.1j, 2.089822, 1.132134, 0.950392, 5224.55 - 261.694j, 1.19224 + 15.3732j, -0.850854 - 4.66332j,
     -9.54952 - 3.55581j),
    (1000, 1.5 - 0.1j, 2.019703, 1.106932, 0.950880, 504926 - 7214.99j, 55.8595 - 143.671j, -11.6307 + 46.0706j,
     99.4571 + 22.1736j),
    (5000, 1.5 - 0.1j, 2.006775, 1.099193, 0.950650, 1.25423e7 - 66647.2j, 543.810 + 546.205j,
     -187.405 - 146.093j, -77.7833 + 503.522j),
]


def _printed(v, digits=6):
    """Half a unit of the last printed digit of a value printed with ``digits`` significant digits."""
    v = abs(v)
    return 0.5 * 10.0 ** (math.floor(math.log10(v)) - digits + 1) if v else 0.0


def _six(z):
    return math.hypot(_printed(z.real), _printed(z.imag))


@pytest.mark.parametrize("row", WISCOMBE, ids=[f"x{r[0]}_m{r[1]}" for r in WISCOMBE])
def test_wiscombe_appendix_iii(row):
    x, mw, qe, qs, g, s0, s90_1, s90_2, s180 = row
    m = complex(mw).conjugate()
    a, b = mie.coefficients(m, x)
    q = mie.efficiencies_from(a, b, x)
    S1, S2 = mie.amplitudes(a, b, np.radians([0.0, 90.0, 180.0]))
    # efficiencies: printed with 6 decimals (F14.6), g with 6 decimals (F9.6)
    assert abs(q["Qext"] - qe) <= 0.5e-6 and abs(q["Qsca"] - qs) <= 0.5e-6 and abs(q["g"] - g) <= 0.5e-6
    for ours, his in ((S1[0], s0), (S1[1], s90_1), (S2[1], s90_2), (S1[2], s180)):
        assert abs(np.conj(ours) - his) <= _six(his) * 1.0001, (ours, his)
    assert abs(S2[2] + S1[2]) <= 1e-9 * abs(S1[2])  # S2(180) = -S1(180)


def test_wiscombe_negative_control_too_few_terms():
    """With 20 terms fewer than Wiscombe's count the x = 100 case misses its printed Q_ext."""
    x = 100
    a, b = mie.coefficients(1.5, x, n_max=mie.n_wiscombe(x) - 20)
    assert abs(mie.efficiencies_from(a, b, x)["Qext"] - 2.094388) > 0.5e-6


TABLE3 = [  # Wiscombe 1979, Table 3, column "Exact": x, his m, Q_ext (6 significant digits)
    (0.02, 1.5 - 1e-6j, 7.67805e-8), (0.02, 1.95 - 1e-6j, 1.27355e-7), (0.02, 1.95 - 1e-5j, 3.77659e-7),
    (0.04, 1.05 - 1e-6j, 1.12179e-7), (0.04, 1.5 - 1e-6j, 6.70403e-7), (0.04, 1.5 - 1e-4j, 8.57008e-6),
    (0.04, 1.95 - 1e-4j, 7.16259e-6), (0.08, 1.05 - 1e-6j, 3.28478e-7), (0.08, 1.5 - 1e-6j, 9.61292e-6),
    (0.08, 1.5 - 1e-4j, 2.54547e-5), (0.08, 1.95 - 1e-4j, 3.67336e-5), (0.20, 1.05 - 0.01j, 5.25263e-3),
    (0.20, 1.05 - 1j, 5.78539e-1), (0.20, 1.95 - 0.01j, 3.90548e-3), (0.20, 1.95 - 1j, 2.58637e-1),
]


@pytest.mark.parametrize("x,mw,qext", TABLE3)
def test_wiscombe_table3_small_particles(x, mw, qext):
    q = mie.efficiencies(complex(mw).conjugate(), x)
    assert abs(q["Qext"] - qext) <= _printed(qext) * 1.0001, (q["Qext"], qext)


# --- closed forms and identities ------------------------------------------------------------------------------------
@pytest.mark.parametrize("m", [1.33, 1.5 + 0.1j, 2.0 + 1.0j, 0.75])
def test_rayleigh_limit(m):
    """x -> 0: Q_sca = (8/3) x^4 |K|^2, Q_abs = 4 x Im K, K = (m^2 - 1)/(m^2 + 2), with relative corrections O(x^2):
    the bound 3 |m|^2 x^2 + 1e-14 (measured: at x = 1e-3 the deviation is ~2e-6, ~1e-6 x^-2... below it); and the
    negative control: Q_sca with (8/3) replaced by 2.6 fails."""
    for x in (1e-3, 1e-2):
        q = mie.efficiencies(m, x)
        K = (m * m - 1) / (m * m + 2)
        qs = 8.0 / 3.0 * x ** 4 * abs(K) ** 2
        tol = 3 * abs(m) ** 2 * x ** 2 + 1e-12
        assert abs(q["Qsca"] - qs) <= tol * qs
        if complex(m).imag:
            qa = 4 * x * K.imag
            assert abs(q["Qabs"] - qa) <= tol * qa
        assert abs(q["Qsca"] - 2.6 * x ** 4 * abs(K) ** 2) > tol * qs  # negative control
        assert abs(q["g"]) <= 5 * x ** 2  # Rayleigh scattering is symmetric front-back to O(x^2)


@pytest.mark.parametrize("m,x", [(1.33, 3.0), (1.5 + 0.1j, 20.0), (0.75, 50.0), (1.33 + 0.01j, 400.0), ("pec", 7.0)])
def test_optical_theorem(m, x):
    """Q_ext from the coefficients against (4/x^2) Re S(0) from the angular sum (B&H Eq. 4.76). An identity of the
    series' structure (pi_n(1) = tau_n(1) = n(n+1)/2, so S(0) = sum (2n+1)(a_n + b_n)/2 for any coefficients): it
    checks the angular functions and the sum at theta = 0, not the coefficients (review B8-mie, M3). Negative
    control: tau_n built with the wrong sign of its second term fails."""
    a, b = mie.coefficients_pec(x) if m == "pec" else mie.coefficients(m, x)
    q = mie.efficiencies_from(a, b, x)
    S1, S2 = mie.amplitudes(a, b, np.array([0.0]))
    assert abs(S1[0] - S2[0]) <= 1e-13 * abs(S1[0])
    assert abs(4.0 / x ** 2 * S1[0].real - q["Qext"]) <= 50 * len(a) * EPS * q["Qext"]
    if m == 1.33:  # negative control: tau_n = n mu pi_n + (n + 1) pi_{n-1} (a wrong sign)
        def bad(a_, b_, th):
            mu = np.cos(np.asarray(th, float))
            s1 = np.zeros(mu.shape, complex)
            p0, p1 = np.zeros_like(mu), np.ones_like(mu)
            for n in range(1, len(a_) + 1):
                if n > 1:
                    p0, p1 = p1, ((2 * n - 1) * mu * p1 - n * p0) / (n - 1)
                tau = n * mu * p1 + (n + 1) * p0
                s1 += (2 * n + 1) / (n * (n + 1)) * (a_[n - 1] * p1 + b_[n - 1] * tau)
            return s1
        assert abs(4.0 / x ** 2 * bad(a, b, [0.0])[0].real - q["Qext"]) > 50 * len(a) * EPS * q["Qext"]


def _gauss_legendre_integrals(a, b, x):
    """Q_sca and g by numpy's Gauss-Legendre rule of order 2N + 20 (the route used before review B8-mie, M2): kept
    as the negative control of the quadrature's tolerance."""
    N = len(a)
    mu, w = np.polynomial.legendre.leggauss(2 * N + 20)
    S1, S2 = mie.amplitudes(a, b, np.arccos(mu))
    I = np.abs(S1) ** 2 + np.abs(S2) ** 2
    return (w @ I) / x ** 2, (w @ (I * mu)) / (w @ I)


def test_fejer_rule_is_exact_and_its_weights_accurate():
    """Fejér's second rule with n - 1 nodes integrates mu^k exactly for k <= n - 1 (n even), its weights sum to 2, and
    they agree with 40-digit evaluations of the same sine sum within 64 u relatively at n = 4000 (measured 48 u: the
    rounding of a sum of n/2 terms; every sine's argument is reduced exactly). Negative control: the Chebyshev
    polynomial T_2n, equal to 1 at every node (aliasing), is integrated as 2 instead of -2/(4n^2 - 1)."""
    for n in (40, 400, 4000):
        mu, w = mie.fejer2(n)
        assert len(mu) == n - 1 and np.all(w > 0)
        assert abs(w.sum() - 2.0) <= 8 * n * mie.U
        for k in (2, n // 2, n - 2):
            assert abs(w @ mu ** k - 2.0 / (k + 1)) <= 16 * n * mie.U
        t = np.arccos(mu)
        assert abs(w @ np.cos(2 * n * t) + 2.0 / (4 * n * n - 1)) > 1.0  # negative control
    n = 4000
    mu, w = mie.fejer2(n)
    with mp.workdps(40):
        for k in (1, 2, 18, 50, n // 2, n - 1):
            t = k * mp.pi / n
            ref = 4 * mp.sin(t) / n * mp.fsum(mp.sin((2 * j - 1) * t) / (2 * j - 1) for j in range(1, n // 2 + 1))
            assert abs(w[k - 1] / float(ref) - 1) <= 64 * mie.U


ANGULAR_CASES = [(1.33, 5.0), (1.5, 30.0), (1.33 + 0.05j, 60.0), (0.75, 15.0), ("pec", 10.0), (1.3354, 36.75),
                 (1.3354, 61.0), (1.3354, 107.5), (1.3354, 500.0), (1.3354, 1714.0), (1.5 + 0.1j, 300.0)]


@pytest.mark.parametrize("m,x", ANGULAR_CASES)
def test_angular_integrals_equal_series(m, x):
    """Q_sca and g by quadrature over the angles (mie.angular_integrals: Fejér's second rule, exact for these
    polynomials in mu) equal the series within the derived rounding bound u (x^2 Q_ext^2/(2 Q_sca) + 8N + 16)
    (measured 0.02-0.09 x^2 u). For a non-absorbing sphere (and the conductor) the scattered power equals Q_ext: an
    identity of the series' structure (Re a_n = |a_n|^2 for any a_n = A/(A - iB) with real A, B), so this checks the
    angular functions, the sums and the quadrature, not the coefficients (review B8-mie, M3). Negative controls: numpy's
    Gauss-Legendre weights (the route before review B8-mie, M2) fail the bound for x >= 36 (2-72 x^2 u; at x = 61 a
    world of v17 failed its energy check on a correct engine); all a_n scaled by 1 + 1e-6 break the comparison."""
    a, b = mie.coefficients_pec(x) if m == "pec" else mie.coefficients(m, x)
    q = mie.efficiencies_from(a, b, x)
    r = mie.angular_integrals(a, b, x)
    tol = r["rel_bound"] * q["Qsca"]
    assert abs(r["Qsca"] - q["Qsca"]) <= tol and abs(r["g"] - q["g"]) <= 2 * r["rel_bound"]
    transparent = m == "pec" or complex(m).imag == 0
    if transparent:
        assert abs(r["Qsca"] - q["Qext"]) <= tol
        a2 = a * (1 + 1e-6)
        q2 = mie.efficiencies_from(a2, b, x)
        assert abs(mie.angular_integrals(a2, b, x)["Qsca"] - q2["Qext"]) > tol
    if transparent and m != "pec" and 36.0 <= x <= 500.0:
        qs_gl, _ = _gauss_legendre_integrals(a, b, x)
        assert abs(qs_gl - q["Qext"]) > tol  # the old weights fail


def test_backscatter_efficiency_equals_angular_sum():
    for m, x in [(1.33, 12.0), (1.5 + 0.1j, 80.0)]:
        a, b = mie.coefficients(m, x)
        q = mie.efficiencies_from(a, b, x)
        S1, S2 = mie.amplitudes(a, b, np.array([math.pi]))
        assert abs(4 * abs(S1[0]) ** 2 / x ** 2 - q["Qback"]) <= 1e-12 * q["Qback"]


def _ball_absorption(m, x, nr=40, nt=40, nphi=8):
    """Q_abs = (x/pi) Im(m^2) int_{r<a} |E|^2 dV (in units of a, |E0| = 1): Gauss-Legendre in r and cos(theta),
    the trapezoid rule in phi (exact for |E|^2, a trigonometric polynomial of degree 2 in phi)."""
    r, wr = np.polynomial.legendre.leggauss(nr)
    r, wr = 0.5 * (r + 1), 0.5 * wr
    mu, wm = np.polynomial.legendre.leggauss(nt)
    ph = np.arange(nphi) * 2 * math.pi / nphi
    R, MU, PH = np.meshgrid(r, mu, ph, indexing="ij")
    st = np.sqrt(1 - MU ** 2)
    pts = np.stack([R * st * np.cos(PH), R * st * np.sin(PH), R * MU], -1)
    E = mie.near_field(m, x, pts)["E"]
    I = np.sum(np.abs(E) ** 2, -1)
    W = (wr * r ** 2)[:, None, None] * wm[None, :, None] * (2 * math.pi / nphi)
    return x / math.pi * (m * m).imag * np.sum(W * I)


@pytest.mark.parametrize("m,x", [(1.5 + 0.1j, 2.0), (1.33 + 0.3j, 5.0), (2.0 + 1.0j, 1.0)])
def test_absorption_from_the_internal_field(m, x):
    """Q_abs = Q_ext - Q_sca (the series) against the Joule heat of the internal field integrated over the ball: an
    independent route through c_n, d_n, the vector spherical harmonics and a quadrature (converged: the same with
    twice the nodes)."""
    q = mie.efficiencies(m, x)
    qa = _ball_absorption(m, x)
    qa2 = _ball_absorption(m, x, nr=60, nt=60)
    assert abs(qa - qa2) <= 1e-9 * qa
    assert abs(qa - q["Qabs"]) <= 1e-9 * q["Qabs"], (qa, q["Qabs"])


def test_extinction_paradox():
    """Q_ext -> 2 for x -> infinity (twice the geometric cross section: the diffracted part); the approach is by the
    edge term ~ x^(-2/3): |Q_ext - 2| <= 2 x^(-2/3) for an absorbing sphere (no ripple), and it shrinks with x.
    Negative control: the geometric value 1 is far outside."""
    vals = [mie.efficiencies(1.5 + 0.1j, x)["Qext"] for x in (100.0, 1000.0, 10000.0)]
    for x, q in zip((100.0, 1000.0, 10000.0), vals):
        assert abs(q - 2.0) <= 2.0 * x ** (-2.0 / 3.0)
        assert abs(q - 1.0) > 2.0 * x ** (-2.0 / 3.0)
    assert abs(vals[2] - 2) < abs(vals[1] - 2) < abs(vals[0] - 2)


def test_perfect_conductor_limits():
    """Rayleigh: Q_sca = (10/3) x^4 (Jackson, Eq. 10.71: sigma = 10 pi k^4 a^6 / 3) to O(x^2); no absorption at any x;
    the limit |m| -> infinity of the dielectric series; large x: Q_ext -> 2 and the backscatter -> the geometric
    pi a^2 (Q_back -> 1)."""
    for x in (1e-3, 1e-2):
        q = mie.efficiencies("pec", x)
        assert abs(q["Qsca"] - 10.0 / 3.0 * x ** 4) <= 3 * x ** 2 * 10.0 / 3.0 * x ** 4
        assert abs(q["Qsca"] - 3.0 * x ** 4) > 3 * x ** 2 * 10.0 / 3.0 * x ** 4  # negative control
    for x in (0.5, 5.0, 50.0):
        q = mie.efficiencies("pec", x)
        assert abs(q["Qabs"]) <= 100 * q["n_terms"] * EPS * q["Qext"]
        ap, bp = mie.coefficients_pec(x)
        am, bm = mie.coefficients(1e7 + 1e7j, x, n_max=len(ap))
        assert np.abs(am - ap).max() <= 1e-5 and np.abs(bm - bp).max() <= 1e-5
    q = mie.efficiencies("pec", 2000.0)
    assert abs(q["Qext"] - 2.0) <= 2.0 * 2000.0 ** (-2.0 / 3.0)
    assert abs(q["Qback"] - 1.0) <= 0.05


def test_mueller_identities():
    """A single sphere's Mueller matrix is pure: S11^2 = S12^2 + S33^2 + S34^2 — an identity for ANY complex S1, S2
    (it checks mie.mueller's arithmetic, not the physics; review B8-mie, M3); P(0) = P(180) = 0 (S1 = S2 forward and
    S1 = -S2 backward: the symmetry of the angular functions); |P| <= 1; P from the intensities equals P from
    mie.mueller (the route v17 uses for bin means, M12)."""
    th = np.radians(np.linspace(0, 180, 361))
    for m, x in [(1.33, 30.0), (1.5 + 0.1j, 8.0)]:
        r = mie.scattering(m, x, th)
        lhs, rhs = r["S11"] ** 2, r["S12"] ** 2 + r["S33"] ** 2 + r["S34"] ** 2
        assert np.all(np.abs(lhs - rhs) <= 1e-12 * lhs)
        assert abs(r["P"][0]) < 1e-12 and abs(r["P"][-1]) < 1e-9 and np.all(np.abs(r["P"]) <= 1 + 1e-12)
        P2 = mie.polarisation_from_intensities(np.abs(r["S1"]) ** 2, np.abs(r["S2"]) ** 2)
        assert np.allclose(P2, r["P"], rtol=1e-12, atol=1e-14)
        pf = mie.phase_function(r["S1"], r["S2"], x, r["Qsca"])
        assert np.allclose(pf, 4 * r["S11"] / (x * x * r["Qsca"]), rtol=1e-13)


def test_angular_functions_against_legendre():
    """pi_n = P_n^1(mu)/sin(theta), tau_n = d P_n^1(cos theta)/d theta (B&H Eq. 4.46; scipy's lpmv carries the
    Condon-Shortley phase (-1)^m)."""
    th = np.radians(np.array([1.0, 17.0, 60.0, 90.0, 133.0, 179.0]))
    mu = np.cos(th)
    PI, TAU = mie.angular(mu, 40)
    for n in range(1, 41):
        pn1 = -special.lpmv(1, n, mu)
        assert np.allclose(PI[n - 1], pn1 / np.sin(th), rtol=1e-11, atol=1e-11 * n * n)
        h = 1e-6
        d = -(special.lpmv(1, n, np.cos(th + h)) - special.lpmv(1, n, np.cos(th - h))) / (2 * h)
        assert np.allclose(TAU[n - 1], d, rtol=1e-6, atol=1e-6 * n * n)


def test_amplitudes_batch_equal_loop():
    xs = np.array([10.0, 11.0])
    A, B = mie.coefficients_batch(1.33, xs)
    th = np.radians(np.linspace(0, 180, 37))
    S1, S2 = mie.amplitudes_batch(A, B, th, chunk=10)
    for k in range(2):
        s1, s2 = mie.amplitudes(A[k], B[k], th)
        assert np.allclose(S1[k], s1, rtol=1e-12, atol=1e-12) and np.allclose(S2[k], s2, rtol=1e-12, atol=1e-12)


# --- near fields ----------------------------------------------------------------------------------------------------
def _sphere_points(r, n, seed=1):
    rng = np.random.default_rng(seed)
    th = np.arccos(rng.uniform(-1, 1, n))
    ph = rng.uniform(0, 2 * np.pi, n)
    return np.stack([r * np.sin(th) * np.cos(ph), r * np.sin(th) * np.sin(ph), r * np.cos(th)], -1), th, ph


def _components(F, th, ph):
    er = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
    et = np.stack([np.cos(th) * np.cos(ph), np.cos(th) * np.sin(ph), -np.sin(th)], -1)
    ep = np.stack([-np.sin(ph), np.cos(ph), 0 * ph], -1)
    return (F * er).sum(-1), (F * et).sum(-1), (F * ep).sum(-1)


@pytest.mark.parametrize("m,x", [(1.33, 5.0), (1.5 + 0.1j, 10.0), (1.33, 30.0), (2.0 + 1.0j, 3.0), (0.75, 8.0)])
def test_near_field_boundary_conditions(m, x):
    """At r = a the tangential E and H (Z H) are continuous and so is the normal D (m^2 E_r inside = E_r outside):
    points 1e-12 a inside and outside, so the field's own change across that gap (~ |grad E| 1e-12 a, |grad E| ~ x
    |m|^2) bounds the mismatch: tol = 20 x |m|^2 1e-12 + 1e-12 (measured 4e-12 - 4e-11). Negative control: the
    internal field with c_n, d_n swapped fails."""
    p, th, ph = _sphere_points(1.0, 200)
    d = 1e-12
    fo, fi = mie.near_field(m, x, p * (1 + d)), mie.near_field(m, x, p * (1 - d))
    assert fi["inside"].all() and not fo["inside"].any()
    s = np.abs(fo["E"]).max()
    tol = (20 * x * abs(m) ** 2 * d + 1e-12) * s
    Eo, Ei = _components(fo["E"], th, ph), _components(fi["E"], th, ph)
    Ho, Hi = _components(fo["H"], th, ph), _components(fi["H"], th, ph)
    for k in (1, 2):
        assert np.abs(Eo[k] - Ei[k]).max() <= tol
        assert np.abs(Ho[k] - Hi[k]).max() <= tol * abs(m)
    assert np.abs(Eo[0] - m * m * Ei[0]).max() <= tol * abs(m) ** 2


def test_near_field_negative_control_swapped_internal_coefficients(monkeypatch):
    m, x = 1.33, 5.0
    p, th, ph = _sphere_points(1.0, 50)
    orig = mie.internal_coefficients
    monkeypatch.setattr(mie, "internal_coefficients", lambda *a, **k: orig(*a, **k)[::-1])
    fo, fi = mie.near_field(m, x, p * (1 + 1e-12)), mie.near_field(m, x, p * (1 - 1e-12))
    Eo, Ei = _components(fo["E"], th, ph), _components(fi["E"], th, ph)
    assert np.abs(Eo[1] - Ei[1]).max() > 1e-3


def test_perfect_conductor_tangential_field_vanishes():
    p, th, ph = _sphere_points(1.0, 100)
    f = mie.near_field("pec", 6.0, p * (1 + 1e-12))
    _, Et, Ep = _components(f["E"], th, ph)
    s = np.abs(f["E"]).max()
    assert max(np.abs(Et).max(), np.abs(Ep).max()) <= 1e-10 * s
    assert np.all(mie.near_field("pec", 6.0, 0.5 * p)["E"] == 0)


@pytest.mark.parametrize("m,x", [(1.33, 5.0), (1.5 + 0.1j, 10.0)])
def test_far_field_limit_equals_amplitudes(m, x):
    """E_s,theta -> exp(ikr)/(-ikr) cos(phi) S2, E_s,phi -> -exp(ikr)/(-ikr) sin(phi) S1, E_s,r = O(1/r^2) (B&H Eq.
    4.74): the relative deviation falls as 1/(kr) (measured ~1e-6 at kr = 5e6 and ~1e-7 at 5e7) and is below
    N^2/(kr)."""
    a, b = mie.coefficients(m, x)
    N = len(a)
    errs = []
    for R in (1e6, 1e7):
        p, th, ph = _sphere_points(R, 40)
        f = mie.near_field(m, x, p, parts=True)
        Er, Et, Ep = _components(f["E_sca"], th, ph)
        S1, S2 = mie.amplitudes(a, b, th)
        kr = x * R
        g = np.exp(1j * kr) / (-1j * kr)
        e = max(np.abs(Et - g * np.cos(ph) * S2).max(), np.abs(Ep + g * np.sin(ph) * S1).max()) / np.abs(g * S1).max()
        assert e <= N * N / kr
        assert np.abs(Er).max() <= N * N / kr * np.abs(g * S1).max()
        errs.append(e)
    assert errs[1] < 0.2 * errs[0]


def test_incident_series_equals_plane_wave():
    """The regular-wave series E_i = sum E_n (M_o1n - i N_e1n), Z H_i = -sum E_n (M_e1n + i N_o1n) (B&H Eqs. 4.37,
    4.43), with the engine's radial and angular functions, reproduce exp(ikz) x-hat and exp(ikz) y-hat inside
    r <= 1.5 a: checks the vector spherical harmonics that the scattered and internal fields share."""
    x, N = 6.0, 60
    rng = np.random.default_rng(3)
    pts = rng.uniform(-1.0, 1.0, (300, 3)) * 1.5
    r, th, ph = mie._spherical(pts)
    rho = x * r
    n = np.arange(1, N + 1)
    En = (1j ** n) * (2 * n + 1) / (n * (n + 1.0))
    Ps, dPs = mie._radial_regular(rho, N)
    E = mie._to_cartesian(*mie._vsh_sum(-1j * En, En, Ps, dPs, rho, th, ph, "E"), th, ph)
    H = -mie._to_cartesian(*mie._vsh_sum(1j * En, En, Ps, dPs, rho, th, ph, "H"), th, ph)
    w = np.exp(1j * x * pts[:, 2])
    assert np.abs(E - np.stack([w, 0 * w, 0 * w], -1)).max() <= 1e-12
    assert np.abs(H - np.stack([0 * w, w, 0 * w], -1)).max() <= 1e-12


def test_polarised_far_intensity_against_the_near_field():
    """mie.intensity_polarised (the scattered intensity for x- and y-polarised incident light, M12) against
    (k r)^2 |E_s|^2 of the near-field series far away (kr = 5e6), for the field polarised along x; the "y" form is
    the same field turned by 90 deg about z. Deviation below N^2/(kr) (the far field's 1/(kr) corrections). Negative
    control: exchanging I1 and I2 fails."""
    m, x = 1.33, 5.0
    a, b = mie.coefficients(m, x)
    N = len(a)
    p, th, ph = _sphere_points(1e6, 60, seed=4)
    f = mie.near_field(m, x, p, parts=True)
    kr = x * 1e6
    I = kr ** 2 * np.sum(np.abs(f["E_sca"]) ** 2, -1)
    S1, S2 = mie.amplitudes(a, b, th)
    I1, I2 = np.abs(S1) ** 2, np.abs(S2) ** 2
    ref = mie.intensity_polarised(I1, I2, ph, "x")
    tol = N * N / kr * np.max(ref)
    assert np.max(np.abs(I - ref)) <= tol
    assert np.max(np.abs(I - mie.intensity_polarised(I2, I1, ph, "x"))) > 100 * tol  # negative control
    assert np.allclose(mie.intensity_polarised(I1, I2, ph + np.pi / 2, "y"), ref, rtol=1e-12)
    assert np.allclose(mie.intensity_polarised(I1, I2, ph, "u"), 0.5 * (I1 + I2), rtol=1e-15)


def _bessel_coefficients(m, x, N, dps=40):
    """a_n, b_n with D_n(mx) and psi_n, chi_n(x) from mpmath's Bessel functions of half-integer order directly (no
    recurrence, no logarithmic derivative): psi_n(z) = z sqrt(pi/(2z)) J_{n+1/2}(z), chi_n = -z sqrt(pi/(2z))
    Y_{n+1/2}(z), D_n = psi_{n-1}/psi_n - n/z."""
    with mp.workdps(dps):
        m, x = mp.mpc(m), mp.mpf(x)
        z = m * x

        def ps(n, w):
            return w * mp.sqrt(mp.pi / (2 * w)) * mp.besselj(n + mp.mpf(1) / 2, w)

        def ch(n, w):
            return -w * mp.sqrt(mp.pi / (2 * w)) * mp.bessely(n + mp.mpf(1) / 2, w)
        a, b = [], []
        for n in range(1, N + 1):
            Dm = ps(n - 1, z) / ps(n, z) - n / z
            p, p1 = ps(n, x), ps(n - 1, x)
            xi, xi1 = p - 1j * ch(n, x), p1 - 1j * ch(n - 1, x)
            ta, tb = Dm / m + n / x, Dm * m + n / x
            a.append(complex((ta * p - p1) / (ta * xi - xi1)))
            b.append(complex((tb * p - p1) / (tb * xi - xi1)))
        return np.array(a), np.array(b)


@pytest.mark.parametrize("m,x", [(1e5, 0.5), (300 + 300j, 2.0), (2000.0, 0.5), (50 + 1e4j, 0.3), (200.0, 1.0),
                                 (30.0, 10.0)])
def test_start_of_D_by_hankel_sums_and_continued_fraction(m, x):
    """The start of D_n(mx): Hankel's finite sums where |mx| > max(N^2, N + 50) (the first four cases; before, reached
    only through the conductor limit at 1e-5, review B8-mie, M10) and the continued fraction summed through its
    oscillatory part (|mx| - N up to 264 steps), against Bessel-function references: every order within
    u (4N + 8 s) of the largest coefficient with s <= 4N here (measured 1.6e-16 - 6e-14). Negative control for
    the reference: the recurrence reference started only 50 orders above |mx| (as before M9) misses m = 1e5, x = 0.5 by
    more than 1e-6."""
    N = mie.n_terms(x)
    hankel = abs(m * x) > max(N * N, N + 50)
    assert hankel == (abs(m * x) > 500)
    a, b = mie.coefficients(m, x, n_max=N)
    ra, rb = _bessel_coefficients(m, x, N)
    s = max(np.abs(ra).max(), np.abs(rb).max())
    e = max(np.abs(a - ra).max(), np.abs(b - rb).max()) / s
    assert e <= mie.coefficient_bound(x, 4 * N), e
    if m == 1e5:
        r2a, _ = _ref_mp_recurrence(m, x, N, dps=40)  # the corrected start agrees with the Bessel functions
        assert np.abs(r2a - ra).max() <= 1e-15 * s
        with mp.workdps(40):  # the start of the old reference: D = 0 at N + |mx| + 50
            mx = mp.mpf(m) * x
            D = mp.mpf(0)
            for n in range(N + int(m * x) + 50, N, -1):
                D = n / mx - 1 / (D + n / mx)
            Dbes = (mp.besselj(N - mp.mpf(1) / 2, mx) / mp.besselj(N + mp.mpf(1) / 2, mx)) - N / mx
            assert abs(D - Dbes) > 1e-6 * abs(Dbes)


def test_log_psi_against_bessel_functions():
    """mie.log_psi (log psi_n(z) without under- or overflow; used by mie_debye where psi(mx) underflows; review B8-mie,
    M10) against mpmath's Bessel functions, for real and complex z, orders where psi_n is ~1e-300 or below and where
    it oscillates: |log psi - exact| <= 64 N u (1 + |log psi|) (the sum of N logarithms). Negative control: the
    logarithm of the double-precision psi underflows to -inf at the top orders."""
    for z, N in ((0.5 + 0j, 200), (3.0, 400), (2.0 + 1.5j, 300), (40.0, 60), (25.0 + 0.3j, 120)):
        L = mie.log_psi(np.array([z]), N)[:, 0]
        with mp.workdps(40):
            zz = mp.mpc(z)
            for n in (1, 2, N // 3, N // 2, N):
                ref = mp.log(zz * mp.sqrt(mp.pi / (2 * zz)) * mp.besselj(n + mp.mpf(1) / 2, zz))
                d = complex(L[n] - complex(ref))
                d = complex(d.real, (d.imag + math.pi) % (2 * math.pi) - math.pi)  # the branch of the logarithm
                assert abs(d) <= 64 * N * mie.U * (1 + abs(complex(ref))), (z, n, d)
    with np.errstate(divide="ignore"):
        assert not np.isfinite(np.log(np.abs(mie.psi(np.array([0.5]), 200)[-1, 0])))
