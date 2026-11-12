# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The Debye series of the Mie coefficients: each partial wave of the sphere's field split into the wave reflected
by the surface and the waves that cross the sphere p - 1 times inside it (plan P1, batch B8).

A partial wave n meets the spherical surface as an incoming wave xi^(2) and leaves as outgoing waves xi^(1); at the
surface (radius a, size parameter x, relative index m) it is reflected and transmitted with the coefficients of a
spherical interface. With xi^(1) = xi = psi - i chi = z h_n^(1)(z), xi^(2) = psi + i chi, the boundary condition
u'/u (outside) = beta u'/u (inside) — beta = 1/m for a_n (TM), beta = m for b_n (TE), as in mie.coefficients — gives,
with L_j = xi^(j)'/xi^(j) and D = L_1(x) - beta L_2(mx):

    R22 = [xi^(2)(x)/xi^(1)(x)] (beta L_2(mx) - L_2(x)) / D        (external reflection)
    R11 = -[xi^(1)(mx)/xi^(2)(mx)] (L_1(x) - beta L_1(mx)) / D     (internal reflection)
    T21 T12 = -4 beta / (xi^(1)(x)^2 xi^(2)(mx)^2 D^2)             (in and out; Wronskian xi^(2) xi^(1)' - xi^(1) xi^(2)' = 2i)

and the plane wave's incoming part (1/2) xi^(2) is scattered into the outgoing waves (1/2)[R22 + sum_p T21 R11^(p-1)
T12] xi^(1), so (Debye 1908; van de Hulst 1957, §12.35; Hovenac & Lock, J. Opt. Soc. Am. A 9, 781 (1992), Eq. 4):

    a_n = (1/2) [1 - R22 - sum_{p>=1} T21 T12 R11^(p-1)],   a_n^(0) = (1 - R22)/2,  a_n^(p) = -T21 T12 R11^(p-1)/2.

p = 0 is diffraction with external reflection, p = 1 direct transmission, p = 2 one internal reflection (the primary
rainbow), p = 3 two (the secondary). The formulas above were derived here (sources/verification_2026-11-04_p1_mie.md)
and are checked by the sum (1 - R22 - T21 T12/(1 - R11))/2 = a_n of the Mie series computed by a different route
(tests/test_mie_debye.py).

Numerics: xi^(1)(z) by its ratio recurrence r_n = (2n-1)/z - 1/r_{n-1}, r_0 = -i (stable: xi^(1) dominates for
Im z >= 0), log xi^(1)_n = iz + sum log r_k; for real x xi^(2) = conj xi^(1). Inside, xi^(2)(mx) = 2 psi(mx) -
xi^(1)(mx) through p = psi/xi^(1) (log psi and D_n(mx) from mie: the downward recurrence of D), all in logarithms, so
that neither absorbing spheres nor high orders over- or underflow; 1 - R22 and 1 - R11 in forms without cancellation
(1 - R22 = 2 [psi(x)/xi^(1)(x)] (D_n(x) - beta L_2(mx))/D, 1 - R11 = [2 psi(mx)/xi^(2)(mx)] (L_1(x) - beta D_n(mx))/D),
which matter where the partial wave tunnels (n > x: R22, R11 -> 1). The powers R11^p of the terms and of the remainder
use R11 = 1 - (1 - R11) from that same form, so that the partial sums plus the remainder telescope to the closed form
(review B8-mie, M5: with R11 taken directly, the two disagreed by 2e-10 relative for m = 1 + 1e-6 i, which the huge
terms of a divergent series turned into a miss of 5e-4 of the largest coefficient).

Convergence. The geometric series in p converges only where |R11| < 1. For a real m, |R11| <= 1 (= 1 for the
tunnelling and totally reflected orders, where T21 T12 is tiny). For an absorbing m close to 1 the tunnelling orders
just above x have |R11| > 1 (4.8 for m = 1 + 1e-6 i at x = 100, 15 at x = 1000): there the series diverges, the closed
form is its analytic continuation, and the terms a^(p), which reach 1e6-1e8 times the largest Mie coefficient, are not
light that took a path (``coefficients`` flags these orders, "diverges_a/b", and reports the largest term relative to
the largest coefficient, "amplification"). For a real m near 1 the terms p = 0 and 1 are large too (50x for
m = 1.0001 at x = 100) and cancel: diffraction against the light passing almost unrefracted; that is physical.

Accuracy (``ACCURACY``, ``check_against_mie``): the closed-form sum against mie.coefficients, per order, as a fraction
of the largest coefficient, within u (1000 N + 32 x |d a_n/dx| / max|a|): the floor covers the logarithmic sums of
this route (their rounding grows faster than N u — the partial sums of log r_k reach |x| — measured <= 453 N u over
281 cases: 14 m from 0.5 to 10 + 10i at x = 10 ... 19900, 150 random (m, x) and five resonance peaks; 1e-15 at x = 10,
~1e-12 at 1000, up to 1e-9 at 2e4 for m = 0.75), the second term the conditioning of the coefficients near narrow
resonances, which both routes share (mie.ACCURACY; on the peaks the routes differ by up to 5.6e-4 of the largest
coefficient).
D_n(mx) p_n = psi_n'(mx)/xi_n(mx) is formed without D_n, which has a pole at every zero of psi_n (n < |mx|) where the
downward recurrence loses relative accuracy; [error in earlier] the product with D_n lost up to 5e-9 at single orders
(m = 2.88, x = 6411: 4632 N u against a 40-digit reference, now 176 N u; review B8-mie, M4).
"""

from __future__ import annotations

import numpy as np

from lfphys.i18n import T
from . import mie

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("The Debye series for a sphere: reflection, transmission, internal reflections"),
    "statement": T("Each partial Mie coefficient is split into the wave reflected by the sphere's surface (p = 0, "
                   "together with diffraction), the wave transmitted straight through (p = 1) and those transmitted "
                   "after p − 1 internal reflections (p = 2: the primary rainbow, p = 3: the secondary); the sum of "
                   "the series (in closed form) equals the Mie coefficients."),
    "validity": T("an exact identity for a homogeneous sphere; the series in p converges only for |R¹¹| < 1: for "
                  "weakly absorbing drops with m ≈ 1, at tunnelling orders |R¹¹| > 1 (the series diverges, the closed "
                  "sum is its continuation and the terms p are not paths of light; they are flagged); numerically for "
                  "x ≤ 2·10⁴ (checked up to Im(m)·x = 10⁴); the sum of the series agrees with the Mie series within "
                  "u(1000N + 32x|daₙ/dx|) of the largest coefficient: ~10⁻¹⁵ at x = 10, ~10⁻¹² at x = 1000, up to 10⁻⁹ "
                  "at x = 2·10⁴ (m = 0.75)"),
    "basis": ["Debye, Phys. Z. 9, 775 (1908)", "van de Hulst, Light Scattering by Small Particles (1957), §12.35",
              "Hovenac & Lock, J. Opt. Soc. Am. A 9, 781 (1992)", "Nussenzveig, Diffraction Effects in Semiclassical "
              "Scattering (1992)"],
    "conflicts": [],
}


def _xi1_logs(z, N: int):
    """log xi^(1)_n(z) and L_1(z) = xi^(1)'/xi^(1) for n = 0..N, z a 1-D array (complex)."""
    z = np.asarray(z, complex)
    lg = np.empty((N + 1,) + z.shape, complex)
    L = np.empty((N + 1,) + z.shape, complex)
    r = np.full(z.shape, -1j)  # xi_0 / xi_{-1} = -i
    lg[0] = 1j * z + np.log(-1j)
    L[0] = 1.0 / r
    for n in range(1, N + 1):
        r = (2 * n - 1) / z - 1.0 / r
        lg[n] = lg[n - 1] + np.log(r)
        L[n] = 1.0 / r - n / z
    return lg, L


def _log_2p_minus_1(lp):
    """log(2p - 1) from lp = log p, without overflow."""
    big = lp.real > 0
    out = np.empty_like(lp)
    with np.errstate(all="ignore"):
        out[big] = lp[big] + np.log(2.0 - np.exp(-lp[big]))
        out[~big] = np.log(2.0 * np.exp(lp[~big]) - 1.0)
    return out


def interface_terms(m, x: float, n_max: int | None = None) -> dict:
    """R22, R11, T21 T12 of the spherical interface for both polarisations, n = 1..N: dict with keys "a" and "b",
    each {"R22", "R11", "TT", "one_minus_R22", "one_minus_R11"} (arrays), "N" and "underflow" (the number of orders
    where psi(mx) underflowed: n >> |mx| for m < 1 at large x; there the p >= 1 waves are dropped)."""
    m = complex(m)
    if m.imag < 0:
        raise ValueError("m = n + i kappa with kappa >= 0 (exp(-i omega t))")
    x = float(x)
    N = int(n_max) if n_max else mie.n_terms(x)
    lx, L1x = _xi1_logs(np.array([x + 0j]), N)
    lx, L1x = lx[1:, 0], L1x[1:, 0]
    l2x, L2x = np.conj(lx), np.conj(L1x)            # real x: xi^(2) = conj xi^(1)
    z = np.array([m * x])
    lm_all, L1m_all = _xi1_logs(z, N)                # n = 0..N
    lm, L1m = lm_all[1:, 0], L1m_all[1:, 0]
    zz = z if m.imag else z.real
    Dm = mie.log_derivative(zz, N)[1:, 0]
    P_all = mie.psi(zz, N)[:, 0]                     # psi(mx) exp(-|Im mx|), n = 0..N; its logarithm where it is tiny
    with np.errstate(divide="ignore"):
        lpsi_all = np.log(P_all.astype(complex)) + abs(z[0].imag)
    tiny = np.abs(P_all) < 1e-250  # near or below the subnormal range: its logarithm by the sum of log(D + n/z)
    if np.any(tiny):
        lpsi_all = np.where(tiny, mie.log_psi(zz, N)[:, 0], lpsi_all)
    lp_all = lpsi_all - lm_all[:, 0]                 # log(psi / xi^(1)) at mx, n = 0..N
    lp = lp_all[1:]
    big = lp.real > 0
    p = np.where(big, 0.0, np.exp(np.where(big, 0.0, lp)))
    ip = np.where(big, np.exp(-np.where(big, lp, 0.0)), 0.0)
    # D_n(mx) p_n = psi_n'(mx)/xi_n(mx) without D_n, which has a pole at each zero of psi_n (n < |mx|) where the
    # downward recurrence loses its relative accuracy (the product stays finite): psi_n' = psi_{n-1} - (n/z) psi_n, so
    # D p = p_{n-1} xi_{n-1}/xi_n - (n/z) p_n, xi_{n-1}/xi_n = L_1 + n/z (review B8-mie, M4: before, single orders at
    # these poles missed a_n by up to 5e-9 of the largest coefficient)
    nn = np.arange(1, N + 1)
    zn = nn / z[0]
    p_prev = np.where(lp_all[:-1].real > 0, 0.0, np.exp(np.where(lp_all[:-1].real > 0, 0.0, lp_all[:-1])))
    usable = (~big) & (lp.real > -30.0) & (lp_all[:-1].real <= 0)  # p, p_{n-1} of moderate size: no underflow
    Dp = np.where(usable, p_prev * (L1m + zn) - zn * p, Dm * p)
    # L_2(mx) = (2 D p - L1) / (2 p - 1), written with 1/p where p is large
    L2m = np.where(big, (2 * Dm - L1m * ip) / (2.0 - ip), (2 * Dp - L1m) / (2 * p - 1.0))
    l2p1 = _log_2p_minus_1(lp)
    l2m = lm + l2p1                                  # log xi^(2)(mx)
    ratio12_m = np.exp(-l2p1)                        # xi^(1)(mx) / xi^(2)(mx)
    # the differences 1 - R22 and 1 - R11 without cancellation (both -> 0 where the partial wave misses the sphere):
    # 1 - R22 = 2 [psi(x)/xi^(1)(x)] (D(x) - beta L_2(mx)) / D,
    # 1 - R11 = [2 psi(mx)/xi^(2)(mx)] (L_1(x) - beta D(mx)) / D, with psi D = psi' formed directly (no pole of D_n)
    Px = mie.psi(np.array([x]), N)[:, 0]
    ex = np.exp(-lx)
    px = Px[1:] * ex
    pDx = (Px[:-1] - nn / x * Px[1:]) * ex                   # psi_n'(x)/xi_n(x)
    f = np.where(big, 2.0 / (2.0 - ip), 2 * p / (2 * p - 1.0))   # 2 psi(mx)/xi^(2)(mx)
    with np.errstate(all="ignore"):
        lf = np.log(2.0) + lp - l2p1                              # its logarithm (-inf where psi(mx) underflowed)
    out = {"N": N, "underflow": int(np.sum(~np.isfinite(lf.real)))}
    for key, beta in (("a", 1.0 / m), ("b", m)):
        den = L1x - beta * L2m
        R22 = np.exp(l2x - lx) * (beta * L2m - L2x) / den
        R11 = -ratio12_m * (L1x - beta * L1m) / den
        lTT = np.log(-4.0 * beta + 0j) - 2 * lx - 2 * l2m - 2 * np.log(den)
        TT = np.exp(lTT)
        # 1 - R11 = 2 (p L1(x) - beta D p) / ((2p - 1) D) on the small-p side (D p without the pole of D)
        small = np.where(usable, 2.0 * (p * L1x - beta * Dp) / (2 * p - 1.0), f * (L1x - beta * Dm))
        omr11 = small / den
        with np.errstate(all="ignore"):
            l_omr11 = np.where(usable, np.log(2.0 * (p * L1x - beta * Dp)) - l2p1,
                               lf + np.log(L1x - beta * Dm)) - np.log(den)
        out[key] = {"R22": R22, "R11": R11, "TT": TT, "one_minus_R22": 2 * (pDx - beta * px * L2m) / den,
                    "one_minus_R11": omr11, "log_TT": lTT, "log_one_minus_R11": l_omr11}
    return out


#: the closed-form sum against mie.coefficients (module docstring): |sum_n - a_n| <= u (F N max|a| + K x |da_n/dx|);
#: F measured <= 453 (m = 0.75, x = 16535; 281 cases of m and x, a random scan among them; tests/test_mie_debye.py),
#: K covers the conditioning both routes share at narrow resonances (the Mie route's own K is 8, mie.ACCURACY).
ACCURACY = {"floor": 1000.0, "conditioning": 32.0}
DIVERGES = 1.0 + 1e-9  # |R11| above this: the series in p diverges at that order (rounding of |R11| = 1 excluded)


def coefficients(m, x: float, p_max: int = 3, n_max: int | None = None) -> dict:
    """The Debye terms a_n^(p), b_n^(p) for p = 0..p_max (arrays of shape (p_max + 1, N)), with "remainder_a",
    "remainder_b" (the terms p > p_max summed in closed form: -T21 T12 R11^p_max / (2 (1 - R11))), so that
    sum_p a^(p) + remainder = a_n; "sum_a", "sum_b" = (1 - R22 - T21 T12/(1 - R11))/2 (the whole series);
    "diverges_a", "diverges_b": the orders where |R11| > 1 (the series in p diverges there: its terms are not paths
    of light, the closed form is its continuation); "amplification": the largest |a^(p)|, |b^(p)| (p = 0..p_max)
    and remainder over the largest |sum| — of order 1 where the terms are paths of light, >> 1 where they cancel
    (m near 1) or diverge."""
    it = interface_terms(m, x, n_max)
    out = {"N": it["N"], "underflow": it["underflow"]}
    big = 0.0
    for key in ("a", "b"):
        TT = it[key]["TT"]
        omr22, omr11 = it[key]["one_minus_R22"], it[key]["one_minus_R11"]
        R11 = 1.0 - omr11  # consistent with the cancellation-free 1 - R11 of the remainder (M5)
        terms = [0.5 * omr22]
        pw = np.ones_like(R11)
        for _ in range(1, p_max + 1):
            terms.append(-0.5 * TT * pw)
            pw = pw * R11
        # T21 T12 / (1 - R11) in logarithms (both factors tiny where the wave tunnels); dropped (and counted in
        # "underflow") only where psi(mx) itself underflowed
        ok = np.isfinite(it[key]["log_one_minus_R11"].real)
        lq = np.where(ok, it[key]["log_TT"] - np.where(ok, it[key]["log_one_minus_R11"], 0.0), -np.inf)
        with np.errstate(all="ignore"):
            q = np.where(ok, np.exp(lq), 0.0)
        out[key] = np.array(terms)
        out["remainder_" + key] = -0.5 * q * pw
        out["sum_" + key] = 0.5 * omr22 - 0.5 * q
        out["diverges_" + key] = np.abs(R11) > DIVERGES
        big = max(big, float(np.abs(out[key]).max()), float(np.abs(out["remainder_" + key]).max()))
    total = max(float(np.abs(out["sum_a"]).max()), float(np.abs(out["sum_b"]).max()))
    out["amplification"] = big / total if total > 0 else 0.0
    return out


def check_against_mie(m, x: float, c: dict | None = None, rel_step: float = 2.0 ** -46) -> dict:
    """The closed-form Debye sum against the Mie coefficients of mie.coefficients (a second route: Hankel-function
    ratios in logarithms and the Wronskian in T21 T12, against D_n downward, Miller's psi and upward chi), per order:
    {"err": max over a, b of |sum - mie| / max|mie| (per order), "tol": u (F N + K s) per order (``ACCURACY``), s the
    coefficient's sensitivity x |da_n/dx| / max|a| estimated by a central difference of mie.coefficients with relative
    step rel_step = 2^-46 (~64 units in the last place of x: it resolves resonances down to widths ~1e-14 x, while the
    coefficients' own rounding, u (4N + 8s), adds at most u/rel_step (4N + 8s) = (0.03 N + 0.06 s) to the estimate),
    "worst" (the largest err/tol), "ok", "N", "max_err"}. ``c``: the result of ``coefficients`` if already computed."""
    c = c if c is not None else coefficients(m, x, p_max=0)
    N = c["N"]
    a, b = mie.coefficients(m, x, n_max=N)
    amax = max(float(np.abs(a).max()), float(np.abs(b).max()))
    err = np.maximum(np.abs(c["sum_a"] - a), np.abs(c["sum_b"] - b)) / amax
    xp, xm = x * (1.0 + rel_step), x * (1.0 - rel_step)
    ap, bp = mie.coefficients(m, xp, n_max=N)
    am, bm = mie.coefficients(m, xm, n_max=N)
    s = x * np.maximum(np.abs(ap - am), np.abs(bp - bm)) / (xp - xm) / amax  # xp - xm exact (Sterbenz)
    tol = mie.U * (ACCURACY["floor"] * N + ACCURACY["conditioning"] * s)
    ratio = err / tol
    return {"err": err, "tol": tol, "sensitivity": s, "worst": float(ratio.max()), "ok": bool(np.all(err <= tol)),
            "N": N, "max_err": float(err.max())}


def amplitudes(m, x: float, theta, p_max: int = 3, n_max: int | None = None) -> dict:
    """S1^(p), S2^(p) at theta for p = 0..p_max (lists of arrays), and the coefficients."""
    c = coefficients(m, x, p_max, n_max)
    S1, S2 = [], []
    for p in range(p_max + 1):
        s1, s2 = mie.amplitudes(c["a"][p], c["b"][p], theta)
        S1.append(s1)
        S2.append(s2)
    c.update({"S1": S1, "S2": S2})
    return c
