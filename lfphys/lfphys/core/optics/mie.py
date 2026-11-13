# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Scattering of a plane electromagnetic wave by a sphere: the exact Lorenz-Mie series (plan P1, batch B8).

Conventions (Bohren & Huffman, *Absorption and Scattering of Light by Small Particles*, Wiley 1983, ch. 4): time
dependence exp(-i omega t); the sphere's refractive index relative to the (non-absorbing) medium m = n + i kappa,
kappa >= 0 absorbing; size parameter x = k a = 2 pi N_medium a / lambda; the incident wave E = E0 exp(i k z) x-hat
travels along +z; theta is the scattering angle from +z, phi the azimuth from the x axis. Riccati-Bessel functions
psi_n(z) = z j_n(z), chi_n(z) = -z y_n(z), xi_n = psi_n - i chi_n = z h_n^(1)(z), D_n(z) = psi_n'(z)/psi_n(z):

    a_n = [(D_n(mx)/m + n/x) psi_n(x) - psi_{n-1}(x)] / [(D_n(mx)/m + n/x) xi_n(x) - xi_{n-1}(x)]
    b_n = [(m D_n(mx) + n/x) psi_n(x) - psi_{n-1}(x)] / [(m D_n(mx) + n/x) xi_n(x) - xi_{n-1}(x)]
    c_n = i m / (psi_n(mx) [xi_n'(x) - m D_n(mx) xi_n(x)]),   d_n = i m / (psi_n(mx) [m xi_n'(x) - D_n(mx) xi_n(x)])

(a_n, b_n: B&H Eq. 4.88; c_n, d_n: the boundary conditions at r = a, B&H Eq. 4.53 with mu_1 = mu, and the Wronskian
psi xi' - xi psi' = i.) A perfectly conducting sphere: a_n = psi_n'(x)/xi_n'(x), b_n = psi_n(x)/xi_n(x).

    Q_ext = (2/x^2) sum (2n+1) Re(a_n + b_n),   Q_sca = (2/x^2) sum (2n+1)(|a_n|^2 + |b_n|^2),   Q_abs = Q_ext - Q_sca
    Q_back = (1/x^2) |sum (2n+1)(-1)^n (a_n - b_n)|^2,   g Q_sca = (4/x^2) sum [n(n+2)/(n+1) Re(a_n a*_{n+1} + b_n b*_{n+1})
             + (2n+1)/(n(n+1)) Re(a_n b*_n)],   Q_pr = Q_ext - g Q_sca
    S1 = sum (2n+1)/(n(n+1)) (a_n pi_n + b_n tau_n),   S2 = sum (2n+1)/(n(n+1)) (a_n tau_n + b_n pi_n)
    S11 = (|S2|^2 + |S1|^2)/2, S12 = (|S2|^2 - |S1|^2)/2, S33 = Re(S2 S1*), S34 = Im(S2 S1*);  P = -S12/S11

(B&H Eqs. 4.61, 4.62, 4.74, 4.82, 3.16 and 4.80 for g.) The near fields are the series of vector spherical harmonics
(B&H Eqs. 4.40-4.53): inside E_1 = sum E_n (c_n M_o1n - i d_n N_e1n), outside the incident wave (taken exactly) plus
E_s = sum E_n (i a_n N_e1n - b_n M_o1n), E_n = i^n (2n+1)/(n(n+1)); Z H likewise (Z the medium's impedance).

Numerics (Wiscombe, NCAR/TN-140+STR, 1979): the number of terms N = x + 4.05 x^(1/3) + 2 (his Eq. 50), plus 16 terms
of margin, the tail below 1e-20 of the largest term trimmed; D_n(z) by downward recurrence D_{n-1} = n/z -
1/(D_n + n/z), started at n = N by the continued fraction for J_{n-1/2}/J_{n+1/2} evaluated by Lentz's method
(Lentz, Appl. Opt. 15, 668 (1976); Thompson & Barnett, J. Comput. Phys. 64, 490 (1986)); psi_n by the downward
product psi_{n-1} = psi_n (D_n + n/z) (Miller's algorithm, stable for the minimal solution), normalised to whichever
of psi_0 = sin z and psi_1 = sin z/z - cos z is larger; chi_n by upward recurrence (stable for the dominant solution);
complex arguments carry the factor exp(-|Im z|) so that absorbing spheres never overflow. Measured accuracy (tests
against 40-60-digit mpmath evaluations of the same formulas, against Arb with Bessel functions, and against Wiscombe's
published tables): see ``ACCURACY``.

Accuracy is stated as a mixed forward-backward bound (review B8-mie, M1): the computation is backward stable in x —
its coefficients are the exact ones at an x moved by a few units in the last place — so the forward error is a floor
of accumulated rounding plus the conditioning of the coefficient itself,

    |a_n - a_n^exact| <= u (F N max_k |a_k| + K x |d a_n^exact / dx|)       (and b_n alike; u = 2^-53),

with F = 4, K = 8 (``ACCURACY``; measured: F <= 1 with K = 4 over 22 cases, x = 1e-3 ... 1e4, every order, and over
five resonance peaks of m = 1.333 at x ~ 1000 with widths 6e-4 ... 1.5e-11, where the forward error reaches 6.4e-3 of
the largest coefficient while staying below the change of the exact b_n under a one-ulp change of x). Near a
resonance of width Gamma in x, x |d b_n/dx| reaches ~ 2 x/Gamma, so no x-independent forward bound exists: the narrow
resonances of a transparent sphere above n = x (Gamma down to 1e-11 at x ~ 1000 for m = 1.333, narrower at larger x or
m) are ill-conditioned problems, not failures of the method. Away from them (x |d a_n/dx| ~ N) the error is a few
1e-13 of the largest coefficient at x = 1000 and ~1e-12 at x = 10^4.

Angular integrals (``angular_integrals``) use Fejér's second rule in mu = cos(theta), whose weights are a sine sum
without cancellation: numpy's and scipy's Gauss-Legendre weights of high order are off by up to 6e-9 near mu = +-1
(their formula is evaluated at the rounded node, where P_{n-1} is small and its relative sensitivity grows like n^3 u),
and the forward peak puts most of the integral there (review B8-mie, M2).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.codes import coded
from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Light scattering by a sphere: the exact Lorenz–Mie series"),
    "statement": T("The coefficients aₙ, bₙ (and the internal cₙ, dₙ) of a homogeneous sphere with a complex "
                   "refractive index m in a non-absorbing medium and of a perfectly conducting sphere; the efficiency "
                   "factors Q_ext, Q_sca, Q_abs, Q_back, Q_pr and the asymmetry parameter g; the amplitudes S₁(θ), "
                   "S₂(θ), the Mueller matrix elements S11, S12, S33, S34 and the degree of linear polarisation; the "
                   "near fields E and H inside and outside the sphere (vector spherical harmonics)."),
    "validity": T("Maxwell's equations exactly for a homogeneous isotropic sphere and a plane wave; numerically from "
                  "the Rayleigh limit (x ~ 1e-6) to x = 2·10⁴; the computation is backward stable in x: the "
                  "coefficients are exact for x shifted by a few units in the last place, error ≤ u(4N·max|aₖ| + "
                  "8x|daₙ/dx|): away from narrow resonances ~10⁻¹³–10⁻¹² of the largest coefficient, at the peak of a "
                  "resonance of width Γ in x up to ~x·u/Γ (the conditioning of the problem, e.g. 6·10⁻³ at Γ = "
                  "1.5·10⁻¹¹, x ≈ 1000); Wiscombe's tables are reproduced to all 6 digits"),
    "basis": ["Mie, Ann. Phys. 330, 377 (1908)",
              T("Bohren & Huffman, Absorption and Scattering of Light by Small Particles (Wiley 1983), ch. 4"),
              T("Wiscombe, NCAR/TN-140+STR (1979): the number of terms, test tables"),
              T("Lentz, Appl. Opt. 15, 668 (1976): the continued fraction for Dₙ")],
    "conflicts": [],
}

#: the accuracy of the coefficients that tests/test_mie.py checks over all orders (against Arb and 40-60-digit
#: references), as a mixed forward-backward bound (module docstring): |a_n - exact| <= u (F N max|a| + K x |da_n/dx|),
#: u = 2^-53, N = n_terms(x). Measured over 22 cases and 5 resonance peaks (tests/test_mie.py::BOUND_CASES, PEAKS):
#: F <= 1 with K = 4 (the worst: m = 1.33 + 1e-8 i at x = 1000), K <= 4 with F = 1; the factors below keep a margin of
#: 2-4 (the tests assert the half bound).
#: [error in earlier] a blanket 2e-11 of the largest coefficient was stated before review B8-mie (M1): it fails on
#: resonance peaks (6.4e-3 at x ~ 1000.68, m = 1.333, n = 1056).
ACCURACY = {"floor": 4.0, "conditioning": 8.0, "x_max": 2e4}
#: the largest size parameter with a tested accuracy bound (``coefficient_bound``; code "mie.size_bound" above it)
MAX_X = ACCURACY["x_max"]
#: |m x| - n beyond which D_n cannot be started (``_D_start``; code "mie.mx_too_large")
MX_START_MAX = 2e6
U = 2.0 ** -53


def coefficient_bound(x: float, sensitivity=0.0):
    """The tested bound of |a_n - a_n^exact| / max_k |a_k| (and b_n) at size parameter x: u (F N + K s), where s =
    x |d a_n^exact/dx| / max_k |a_k| is the coefficient's sensitivity (dimensionless; scalar or per order). With s = 0
    it is the floor, which holds only where the coefficient is well-conditioned (s of order N or less, i.e. away from
    resonances narrower than ~x/N in x); the caller supplies s from an exact reference (``ACCURACY``)."""
    if not x <= ACCURACY["x_max"]:
        raise coded(ValueError(T("no tested accuracy bound above the size parameter x = {xmax:.3g}", xmax=MAX_X)),
                    "mie.size_bound")
    return U * (ACCURACY["floor"] * n_terms(x) + ACCURACY["conditioning"] * np.asarray(sensitivity, float))


TINY = 1e-300
RESCALE = 1e250


# --- the number of terms ----------------------------------------------------------------------------------------
def n_wiscombe(x: float) -> int:
    """Wiscombe's number of terms (NCAR/TN-140 Eq. 50): x + 4x^(1/3) + 1 for x <= 8, x + 4.05x^(1/3) + 2 for
    8 < x < 4200, x + 4x^(1/3) + 2 above."""
    x = float(x)
    if x <= 8.0:
        v = x + 4.0 * x ** (1.0 / 3.0) + 1.0
    elif x < 4200.0:
        v = x + 4.05 * x ** (1.0 / 3.0) + 2.0
    else:
        v = x + 4.0 * x ** (1.0 / 3.0) + 2.0
    return max(int(v), 1)


def n_terms(x: float, margin: int = 16) -> int:
    """Terms computed: Wiscombe's number plus a margin (the series converges super-exponentially beyond it; the tail
    is trimmed by ``coefficients``)."""
    return n_wiscombe(x) + int(margin)


def size_parameter(radius, wavelength, n_medium: float = 1.0):
    """x = 2 pi N_medium a / lambda (radius and wavelength in the same units, lambda in vacuum)."""
    return 2.0 * math.pi * n_medium * np.asarray(radius, float) / np.asarray(wavelength, float)


# --- Riccati-Bessel functions ----------------------------------------------------------------------------------------
def _cf_D(z, n: int, tol: float = 4e-16):
    """D_n(z) = -n/z + J_{n-1/2}(z)/J_{n+1/2}(z) for an array z, the ratio by its continued fraction
    J_{nu-1}/J_nu = c_1 + 1/(c_2 + 1/(c_3 + ...)), c_k = (-1)^(k+1) 2 (nu + k - 1)/z, nu = n + 1/2, summed by the
    modified Lentz method (Thompson & Barnett 1986). Converges for every z != 0 (Pincherle: J is the minimal solution
    of the recurrence); the number of steps grows like |z| - n when n < |z|."""
    z = np.asarray(z)
    nu = n + 0.5
    f = 2.0 * nu / z
    f = np.where(f == 0, TINY, f)
    C = f.copy()
    Dd = np.zeros_like(f)
    active = np.ones(f.shape, bool)
    k = 2
    kmax = int(np.max(np.abs(z))) + 10 * n + 10000
    while active.any():
        ck = (2.0 * (nu + k - 1) / z) * (1.0 if k % 2 else -1.0)
        Dd = ck + Dd
        Dd = np.where(Dd == 0, TINY, Dd)
        C = ck + 1.0 / C
        C = np.where(C == 0, TINY, C)
        Dd = 1.0 / Dd
        delta = C * Dd
        f = np.where(active, f * delta, f)
        active &= np.abs(delta - 1.0) > tol
        k += 1
        if k > kmax:
            raise coded(RuntimeError(T("the continued fraction for D_n did not converge")), "mie.no_convergence")
    return -n / z + f


def _hankel_psi_pair(z, n: int):
    """psi_n(z), psi_{n-1}(z) times exp(-|Im z|) from Hankel's finite sums (DLMF 10.49.1, 10.49.6-7):
    xi_n^(1,2)(z) = (-+i)^(n+1) exp(+-iz) sum_k (+-i/(2z))^k (n+k)!/(k!(n-k)!), psi = (xi^(1) + xi^(2))/2; summed
    term by term, accurate where |z| > n^2 (every term smaller than the previous)."""
    z = np.asarray(z, complex)
    out = []
    ez1 = np.exp(1j * z.real - np.abs(z.imag) - z.imag)   # exp(iz) exp(-|Im z|)
    ez2 = np.exp(-1j * z.real - np.abs(z.imag) + z.imag)  # exp(-iz) exp(-|Im z|)
    for nn in (n, n - 1):
        s1, s2 = np.ones_like(z), np.ones_like(z)
        t1, t2 = np.ones_like(z), np.ones_like(z)
        for k in range(nn):
            f = (nn + k + 1) * (nn - k) / (k + 1.0)
            t1 = t1 * f * (1j / (2 * z))
            t2 = t2 * f * (-1j / (2 * z))
            s1, s2 = s1 + t1, s2 + t2
        out.append(0.5 * ((-1j) ** ((nn + 1) % 4) * ez1 * s1 + (1j) ** ((nn + 1) % 4) * ez2 * s2))
    return out[0], out[1]


def _start_D(z, N: int):
    """D_N(z): Hankel's finite sums where |z| > max(N^2, N + 50); otherwise the continued fraction (whose length
    grows like |z| - N; refused beyond 2e6 steps)."""
    z = np.asarray(z)
    out = np.empty(z.shape, z.dtype if np.iscomplexobj(z) else np.float64)
    poly = np.abs(z) > max(N * N, N + 50)
    if poly.any():
        p, p1 = _hankel_psi_pair(z[poly], N)
        d = (p1 - N / z[poly] * p) / p
        out[poly] = d if np.iscomplexobj(z) else d.real
    rest = ~poly
    if rest.any():
        if float(np.max(np.abs(z[rest]))) - N > MX_START_MAX:
            raise coded(ValueError(T("|m x| = {mx:.3g} is too large for the start of D_n at n = {n:d} (neither the "
                                     "continued fraction nor Hankel's sums are practical)",
                                     mx=float(np.max(np.abs(z[rest]))), n=int(N))), "mie.mx_too_large")
        out[rest] = _cf_D(z[rest], N)
    return out


def log_derivative(z, N: int):
    """D_n(z) = psi_n'(z)/psi_n(z) for n = 0..N (shape (N+1,) + z.shape), downward from its value at N (the continued
    fraction, or Hankel's sums for |z| > N^2); the downward recurrence is stable (Wiscombe 1979)."""
    z = np.asarray(z)
    dt = np.complex128 if np.iscomplexobj(z) else np.float64
    D = np.empty((N + 1,) + z.shape, dt)
    D[N] = _start_D(z, N)
    for n in range(N, 0, -1):
        D[n - 1] = n / z - 1.0 / (D[n] + n / z)
    return D


def _scaled_sin_cos(z):
    """sin z and cos z times exp(-|Im z|) (no overflow for strongly absorbing arguments)."""
    z = np.asarray(z)
    if not np.iscomplexobj(z):
        return np.sin(z), np.cos(z)
    a, b = z.real, z.imag
    e = np.exp(-2.0 * np.abs(b))
    ch, sh = 0.5 * (1.0 + e), np.sign(b) * 0.5 * (1.0 - e)
    return np.sin(a) * ch + 1j * np.cos(a) * sh, np.cos(a) * ch - 1j * np.sin(a) * sh


def psi(z, N: int):
    """psi_n(z) exp(-|Im z|) for n = 0..N, shape (N+1,) + z.shape. Where z is real and larger than N the whole range is
    oscillatory and the upward recurrence psi_n = (2n-1)/z psi_{n-1} - psi_{n-2} is neutrally stable; elsewhere the
    downward product psi_{n-1} = psi_n (D_n + n/z) from psi_N = 1 (Miller's algorithm, rescaled against overflow) is
    normalised to the larger of the direct psi_0 = sin z, psi_1 = sin z/z - cos z (exp(-|Im z|) = 1 for real z)."""
    z = np.atleast_1d(np.asarray(z))
    cplx = np.iscomplexobj(z)
    P = np.empty((N + 1,) + z.shape, np.complex128 if cplx else np.float64)
    s, c = _scaled_sin_cos(z)
    up = np.zeros(z.shape, bool) if cplx else (z > N + 0.5)
    if up.any():
        zu = z[up]
        P[0, up] = s[up]
        if N >= 1:
            P[1, up] = s[up] / zu - c[up]
        for n in range(2, N + 1):
            P[n, up] = (2 * n - 1) / zu * P[n - 1, up] - P[n - 2, up]
    mil = ~up
    if mil.any():
        zm = z[mil]
        D = log_derivative(zm, N)
        Q = np.empty((N + 1,) + zm.shape, P.dtype)
        Q[N] = 1.0
        for n in range(N, 0, -1):
            Q[n - 1] = Q[n] * (D[n] + n / zm)
            big = np.abs(Q[n - 1]) > RESCALE
            if np.any(big):
                Q[n - 1:, big] = Q[n - 1:, big] / RESCALE
        p0 = s[mil]
        p1 = p0 / zm - c[mil]
        use0 = np.abs(p0) >= np.abs(p1)
        with np.errstate(all="ignore"):
            if N >= 1:
                scale = np.where(use0, p0 / Q[0], p1 / np.where(use0, 1.0, Q[1]))
            else:
                scale = p0 / Q[0]
        P[:, mil] = Q * scale
    return P


def log_psi(z, N: int):
    """log psi_n(z) (complex logarithm) for n = 0..N, without under- or overflow: log psi_n = log psi_k -
    sum_{j=k+1..n} log(D_j + j/z) from the larger of psi_0 = sin z, psi_1 = sin z/z - cos z (k = 0 or 1; downward
    from k = 1 to 0 likewise); where z is real and above N, the logarithm of the upward recurrence."""
    z = np.atleast_1d(np.asarray(z))
    out = np.empty((N + 1,) + z.shape, np.complex128)
    up = np.zeros(z.shape, bool) if np.iscomplexobj(z) else (z > N + 0.5)
    if up.any():
        with np.errstate(divide="ignore"):
            out[:, up] = np.log(psi(z[up], N).astype(complex))
    mil = ~up
    if mil.any():
        zm = z[mil].astype(complex)
        D = log_derivative(z[mil], N)
        terms = np.log((D + np.arange(N + 1).reshape((-1,) + (1,) * zm.ndim) / zm).astype(complex))  # log psi_{j-1}/psi_j
        a = np.abs(zm.imag)
        s, c = _scaled_sin_cos(zm)
        p0, p1 = s, s / zm - c
        use0 = np.abs(p0) >= np.abs(p1)
        with np.errstate(divide="ignore"):
            l0 = np.log(p0) + a
            l1 = np.log(p1) + a
        L = np.empty((N + 1,) + zm.shape, complex)
        if N >= 1:
            L[0] = np.where(use0, l0, l1 + terms[1])
            L[1] = np.where(use0, l0 - terms[1], l1)
            if N >= 2:
                L[2:] = L[1] - np.cumsum(terms[2:], axis=0)
        else:
            L[0] = l0
        out[:, mil] = L
    return out


def chi(x, N: int):
    """chi_n(x) = -x y_n(x) for real x, n = -1..N (index 0 is n = -1), by upward recurrence (the dominant solution)."""
    x = np.asarray(x, float)
    X = np.empty((N + 2,) + x.shape)
    X[0] = -np.sin(x)
    X[1] = np.cos(x)
    for n in range(1, N + 1):
        X[n + 1] = (2 * n - 1) / x * X[n] - X[n - 1]
    return X


# --- coefficients ----------------------------------------------------------------------------------------------
def _check_m(m):
    m = complex(m)
    if m.imag < 0:
        raise coded(ValueError(T("the relative index is m = n + iκ with κ ≥ 0 (time dependence exp(−iωt)); an "
                                 "absorbing sphere in the exp(+iωt) convention (n − iκ) is its complex conjugate")),
                    "mie.index")
    if m == 0:
        raise coded(ValueError(T("the relative index m = 0")), "mie.index")
    return m


def _riccati_x(x, N):
    """psi_n(x), xi_n(x) for n = 0..N, real x (array): Miller's psi, upward chi."""
    P = psi(np.asarray(x, float), N)
    X = chi(x, N)[1:]  # n = 0..N
    return P, P - 1j * X


def _trim(a, b, rel=1e-20):
    s = np.abs(a) + np.abs(b)
    if not s.size:
        return a, b
    keep = np.nonzero(s > rel * s.max())[0]
    n = int(keep[-1]) + 1 if keep.size else 1
    return a[:n], b[:n]


def coefficients(m, x: float, n_max: int | None = None, trim: bool = True):
    """The external Mie coefficients (a_n, b_n), n = 1..N, of a homogeneous sphere (relative index m, size parameter
    x). ``n_max`` fixes N (no trimming); by default N = n_terms(x) with the negligible tail trimmed."""
    m = _check_m(m)
    x = float(x)
    if not x > 0:
        raise coded(ValueError(T("the size parameter x must be positive")), "mie.size")
    N = int(n_max) if n_max else n_terms(x)
    P, Xi = _riccati_x(np.array([x]), N)
    P, Xi = P[:, 0], Xi[:, 0]
    mx = np.array([m * x]) if m.imag else np.array([m.real * x])
    Dm = log_derivative(mx, N)[:, 0]
    n = np.arange(1, N + 1)
    ta = Dm[1:] / m + n / x
    tb = Dm[1:] * m + n / x
    a = (ta * P[1:] - P[:-1]) / (ta * Xi[1:] - Xi[:-1])
    b = (tb * P[1:] - P[:-1]) / (tb * Xi[1:] - Xi[:-1])
    if trim and not n_max:
        return _trim(a, b)
    return a, b


def coefficients_pec(x: float, n_max: int | None = None, trim: bool = True):
    """A perfectly conducting sphere: a_n = psi_n'(x)/xi_n'(x), b_n = psi_n(x)/xi_n(x) (the limit |m| -> infinity)."""
    x = float(x)
    N = int(n_max) if n_max else n_terms(x)
    P, Xi = _riccati_x(np.array([x]), N)
    P, Xi = P[:, 0], Xi[:, 0]
    n = np.arange(1, N + 1)
    dP = P[:-1] - n / x * P[1:]
    dXi = Xi[:-1] - n / x * Xi[1:]
    a, b = dP / dXi, P[1:] / Xi[1:]
    if trim and not n_max:
        return _trim(a, b)
    return a, b


def internal_coefficients(m, x: float, n_max: int | None = None):
    """(c_n, d_n): the internal coefficients times exp(|Im mx|) (c_n psi_n(mkr) is then evaluated with psi scaled by
    exp(-|Im mkr|), so that nothing overflows), n = 1..N. [error in earlier] the docstring promised a third value,
    "log_scale" (review B8-mie, M13): the scale is the fixed factor exp(|Im mx|)."""
    m = _check_m(m)
    x = float(x)
    N = int(n_max) if n_max else n_terms(x)
    _, Xi = _riccati_x(np.array([x]), N)
    Xi = Xi[:, 0]
    n = np.arange(1, N + 1)
    dXi = Xi[:-1] - n / x * Xi[1:]
    z = np.array([m * x]) if m.imag else np.array([m.real * x])
    Pm = psi(z, N)[1:, 0]
    Dm = log_derivative(z, N)[1:, 0]
    c = 1j * m / (Pm * (dXi - m * Dm * Xi[1:]))
    d = 1j * m / (Pm * (m * dXi - Dm * Xi[1:]))
    return c, d


def coefficients_batch(m, x, n_max: int | None = None):
    """(a, b) of shape (K, N) for K size parameters at once (m scalar or one per size), zero beyond each size's own
    n_terms; N = n_terms(max x) unless given. For polydisperse averages (the recurrences run over n, vectorised over
    the sizes)."""
    x = np.atleast_1d(np.asarray(x, float))
    mm = np.broadcast_to(np.asarray(m, complex), x.shape)
    if np.any(mm.imag < 0):
        _check_m(mm[mm.imag < 0][0])
    N = int(n_max) if n_max else n_terms(float(x.max()))
    own = np.array([n_terms(float(v)) for v in x])
    P = psi(x, N)
    X = np.empty((N + 1,) + x.shape)  # chi_0..chi_N, frozen beyond each size's own N (no overflow)
    prev, cur = -np.sin(x), np.cos(x)
    X[0] = cur
    for n in range(1, N + 1):
        nxt = (2 * n - 1) / x * cur - prev
        ok = n <= own
        nxt = np.where(ok, nxt, cur)
        prev, cur = np.where(ok, cur, prev), nxt
        X[n] = cur
    Xi = P - 1j * X
    z = mm * x if np.any(mm.imag) else (mm.real * x)
    Dm = log_derivative(z, N)
    n = np.arange(1, N + 1)[:, None]
    ta = Dm[1:] / mm + n / x
    tb = Dm[1:] * mm + n / x
    with np.errstate(all="ignore"):
        a = (ta * P[1:] - P[:-1]) / (ta * Xi[1:] - Xi[:-1])
        b = (tb * P[1:] - P[:-1]) / (tb * Xi[1:] - Xi[:-1])
    keep = n <= own
    a = np.where(keep, a, 0.0).T
    b = np.where(keep, b, 0.0).T
    return np.ascontiguousarray(a), np.ascontiguousarray(b)


# --- efficiencies ------------------------------------------------------------------------------------------------
def efficiencies_from(a, b, x: float) -> dict:
    """Q_ext, Q_sca, Q_abs, Q_back, Q_pr, g from the coefficients (B&H Eqs. 4.61, 4.62, 4.82, 4.80)."""
    a, b = np.asarray(a), np.asarray(b)
    N = a.shape[-1]
    n = np.arange(1, N + 1, dtype=float)
    f = 2.0 / x ** 2
    qext = f * np.sum((2 * n + 1) * (a.real + b.real), axis=-1)
    qsca = f * np.sum((2 * n + 1) * (np.abs(a) ** 2 + np.abs(b) ** 2), axis=-1)
    sgn = np.where(n % 2 == 0, 1.0, -1.0)
    qback = np.abs(np.sum((2 * n + 1) * sgn * (a - b), axis=-1)) ** 2 / x ** 2
    n1 = n[:-1]
    t1 = np.sum(n1 * (n1 + 2) / (n1 + 1) * (a[..., :-1] * np.conj(a[..., 1:]) + b[..., :-1] * np.conj(b[..., 1:])).real,
                axis=-1)
    t2 = np.sum((2 * n + 1) / (n * (n + 1)) * (a * np.conj(b)).real, axis=-1)
    gq = 4.0 / x ** 2 * (t1 + t2)
    with np.errstate(all="ignore"):
        g = np.where(qsca > 0, gq / np.where(qsca > 0, qsca, 1.0), 0.0)
    out = {"Qext": qext, "Qsca": qsca, "Qabs": qext - qsca, "Qback": qback, "g": g, "Qpr": qext - gq, "n_terms": N}
    return {k: (float(v) if np.ndim(v) == 0 else v) for k, v in out.items()}


def efficiencies(m, x: float) -> dict:
    """Efficiency factors and asymmetry parameter of a homogeneous sphere (``m = "pec"``: a perfect conductor)."""
    a, b = coefficients_pec(x) if isinstance(m, str) and m == "pec" else coefficients(m, x)
    return efficiencies_from(a, b, x)


# --- angular functions and amplitudes -----------------------------------------------------------------------------------
def angular(mu, N: int):
    """pi_n(mu), tau_n(mu) for n = 1..N (shape (N,) + mu.shape): pi_n = (2n-1)/(n-1) mu pi_{n-1} - n/(n-1) pi_{n-2},
    pi_0 = 0, pi_1 = 1; tau_n = n mu pi_n - (n+1) pi_{n-1} (B&H Eq. 4.47)."""
    mu = np.asarray(mu, float)
    PI = np.empty((N,) + mu.shape)
    TAU = np.empty((N,) + mu.shape)
    p0, p1 = np.zeros_like(mu), np.ones_like(mu)
    for n in range(1, N + 1):
        if n > 1:
            p0, p1 = p1, ((2 * n - 1) * mu * p1 - n * p0) / (n - 1)
        PI[n - 1] = p1
        TAU[n - 1] = n * mu * p1 - (n + 1) * p0
    return PI, TAU


def amplitudes(a, b, theta):
    """S1(theta), S2(theta) (theta in radians, any shape) from the coefficients, summed over n without storing the
    angular functions of all orders."""
    a, b = np.asarray(a), np.asarray(b)
    mu = np.cos(np.asarray(theta, float))
    S1 = np.zeros(mu.shape, complex)
    S2 = np.zeros(mu.shape, complex)
    p0, p1 = np.zeros_like(mu), np.ones_like(mu)
    for n in range(1, len(a) + 1):
        if n > 1:
            p0, p1 = p1, ((2 * n - 1) * mu * p1 - n * p0) / (n - 1)
        tau = n * mu * p1 - (n + 1) * p0
        c = (2 * n + 1) / (n * (n + 1))
        S1 += c * (a[n - 1] * p1 + b[n - 1] * tau)
        S2 += c * (a[n - 1] * tau + b[n - 1] * p1)
    return S1, S2


def amplitudes_batch(a, b, theta, chunk: int = 512):
    """S1, S2 of shape (K, A) for K coefficient rows (a, b of shape (K, N)) at A angles: matrix products with the
    angular functions, computed for chunks of angles."""
    a, b = np.atleast_2d(a), np.atleast_2d(b)
    K, N = a.shape
    theta = np.atleast_1d(np.asarray(theta, float))
    n = np.arange(1, N + 1)
    c = (2 * n + 1) / (n * (n + 1.0))
    ac, bc = a * c, b * c
    S1 = np.empty((K, len(theta)), complex)
    S2 = np.empty((K, len(theta)), complex)
    for i0 in range(0, len(theta), chunk):
        PI, TAU = angular(np.cos(theta[i0:i0 + chunk]), N)
        for out, u, v in ((S1, ac, bc), (S2, bc, ac)):  # S1 = a pi + b tau, S2 = a tau + b pi
            out[:, i0:i0 + chunk] = (u.real @ PI + v.real @ TAU) + 1j * (u.imag @ PI + v.imag @ TAU)
    return S1, S2


def mueller(S1, S2) -> dict:
    """S11, S12, S33, S34 (B&H Eq. 3.16) and the degree of linear polarisation P = -S12/S11 of scattered unpolarised
    light (positive: perpendicular to the scattering plane)."""
    i1, i2 = np.abs(S1) ** 2, np.abs(S2) ** 2
    s11, s12 = 0.5 * (i2 + i1), 0.5 * (i2 - i1)
    w = S2 * np.conj(S1)
    with np.errstate(all="ignore"):
        P = np.where(s11 > 0, -s12 / np.where(s11 > 0, s11, 1.0), 0.0)
    return {"S11": s11, "S12": s12, "S33": w.real, "S34": w.imag, "P": P}


def scattering(m, x: float, theta) -> dict:
    """Everything at once for one sphere: coefficients, efficiencies, S1, S2 and the Mueller elements at ``theta``
    (radians)."""
    a, b = coefficients_pec(x) if isinstance(m, str) and m == "pec" else coefficients(m, x)
    S1, S2 = amplitudes(a, b, theta)
    out = efficiencies_from(a, b, x)
    out.update({"a": a, "b": b, "S1": S1, "S2": S2})
    out.update(mueller(S1, S2))
    return out


def phase_function(S1, S2, x: float, Qsca: float):
    """The phase function of unpolarised light normalised to 4 pi over the sphere: 4 pi (dsigma/dOmega) / C_sca =
    2 (|S1|^2 + |S2|^2) / (x^2 Q_sca)."""
    return phase_function_from_intensities(np.abs(S1) ** 2, np.abs(S2) ** 2, x, Qsca)


def phase_function_from_intensities(I1, I2, x: float, Qsca: float):
    """The same from I1 = |S1|^2 and I2 = |S2|^2 (e.g. their means over angular bins): 2 (I1 + I2) / (x^2 Q_sca)."""
    return 2.0 * (np.asarray(I1) + np.asarray(I2)) / (x ** 2 * Qsca)


def polarisation_from_intensities(I1, I2):
    """The degree of linear polarisation of scattered unpolarised light, P = -S12/S11 = (I1 - I2)/(I1 + I2), from
    I1 = |S1|^2, I2 = |S2|^2 (0 where both vanish); the same as ``mueller(...)["P"]``."""
    I1, I2 = np.asarray(I1, float), np.asarray(I2, float)
    s = I1 + I2
    with np.errstate(all="ignore"):
        return np.where(s > 0, (I1 - I2) / np.where(s > 0, s, 1.0), 0.0)


def intensity_polarised(I1, I2, phi, along: str = "x"):
    """The scattered intensity (in units of |S|^2, i.e. k^2 r^2 |E_s|^2/|E_0|^2 far away) at azimuth phi (radians, from
    the x axis) for an incident wave along +z linearly polarised along x ("x") or y ("y"), or unpolarised ("u"):
    E_s,theta ~ cos(phi) S2, E_s,phi ~ -sin(phi) S1 (B&H Eq. 4.74, the far limit tested against ``near_field``), so
    I = I2 cos^2 phi + I1 sin^2 phi for "x", I2 sin^2 phi + I1 cos^2 phi for "y", (I1 + I2)/2 unpolarised.
    I1 = |S1|^2, I2 = |S2|^2 broadcast against phi."""
    I1, I2, phi = np.asarray(I1, float), np.asarray(I2, float), np.asarray(phi, float)
    c2, s2 = np.cos(phi) ** 2, np.sin(phi) ** 2
    if along == "x":
        return I2 * c2 + I1 * s2
    if along == "y":
        return I2 * s2 + I1 * c2
    if along == "u":
        return 0.5 * (I1 + I2) * np.ones_like(phi)
    raise ValueError("along must be 'x', 'y' or 'u'")


def dsigma_domega(S1, S2, k: float):
    """Differential scattering cross section of unpolarised light, (|S1|^2 + |S2|^2)/(2 k^2) (area per steradian)."""
    return (np.abs(S1) ** 2 + np.abs(S2) ** 2) / (2.0 * k ** 2)


# --- integrals over angles ---------------------------------------------------------------------------------------------
def _sin_pi_frac(r, n: int):
    """sin(r pi / n) for integer arrays r, with the argument reduced exactly (integers mod 2n, then to [0, pi/2]), so
    that every value is accurate to a few u relatively."""
    r = np.mod(np.asarray(r, np.int64), 2 * n)
    sign = np.where(r >= n, -1.0, 1.0)
    r = np.where(r >= n, r - n, r)
    r = np.where(2 * r > n, n - r, r)
    return sign * np.sin(r * (math.pi / n))


def fejer2(n: int):
    """Fejér's second quadrature rule on [-1, 1]: the n - 1 nodes mu_k = cos(k pi/n), k = 1..n-1, and the weights
    w_k = (4 sin t_k / n) sum_{j=1}^{[n/2]} sin((2j - 1) t_k)/(2j - 1), t_k = k pi/n (Waldvogel, "Fast construction
    of the Fejér and Clenshaw-Curtis quadrature rules", BIT Numer. Math. 46, 195 (2006), Eq. (2.3), the explicit form
    after Fejér 1933; checked against the author's copy); the interpolating polynomial has degree n - 2, so the rule
    is exact to that degree (to n - 1 for even n, by symmetry; tests). Every sine's argument (2j - 1) k pi/n is reduced
    in integers before it is rounded, and each weight is a sum without cancellation, so the weights are accurate to a
    few tens of u (measured against 30-digit sums: <= 14 u at n = 400, 22 u at 1000, 48 u at 4000), unlike the
    Gauss-Legendre weights of numpy and scipy at high order, which are off by up to 6e-9 near mu = +-1 (review B8-mie, M2)."""
    n = int(n)
    if n < 2:
        raise ValueError("n >= 2")
    k = np.arange(1, n, dtype=np.int64)
    s = np.zeros(n - 1)
    for j in range(1, n // 2 + 1):
        s += _sin_pi_frac((2 * j - 1) * k, n) / (2 * j - 1)
    mu = _sin_pi_frac(n - 2 * k, 2 * n)  # cos(k pi/n) = sin((n - 2k) pi/(2n))
    return mu, 4.0 * _sin_pi_frac(k, n) / n * s


def angular_integrals(a, b, x: float, chunk: int = 512) -> dict:
    """Q_sca = (1/x^2) int_{-1}^{1} (|S1|^2 + |S2|^2) dmu and g = int I mu dmu / int I dmu by quadrature over the
    scattering angle: a route through the angular functions independent of the series' closed sums (it checks pi_n,
    tau_n, the sums S1, S2 and the quadrature; it does not check the coefficients, which it takes as given). Fejér's
    second rule with n = 2N + 4 (exact for |S|^2 mu, a polynomial of degree 2N + 1 in mu), the angular functions
    evaluated at mu itself. Returns {"Qsca", "g", "rel_bound", "n_nodes"}: "rel_bound" bounds the relative error of
    Q_sca from rounding, u (x^2 Q_ext^2/(2 Q_sca) + 8 N + 16): the nodes are rounded cosines (|d mu| <= u), and the
    forward lobe, whose height I(0) = 2 |S(0)|^2 = x^4 Q_ext^2/8 falls off within d mu ~ 1/x^2, changes by at most its
    total variation ~ I(0) over such errors, against the integral x^2 Q_sca (4x the estimate); 8 N u for the sums S
    (N terms adding in phase in the lobe) and the sum over the nodes. The error of g is at most 2 rel_bound.
    Measured for water drops, x = 2 ... 1714: 0.02 - 0.09 x^2 u (numpy's Gauss-Legendre weights: 2 - 72 x^2 u)."""
    a, b = np.asarray(a), np.asarray(b)
    N = len(a)
    n = 2 * N + 4
    mu, w = fejer2(n)
    nn = np.arange(1, N + 1)
    c = (2 * nn + 1) / (nn * (nn + 1.0))
    ac, bc = a * c, b * c
    s0 = s1 = 0.0
    for i0 in range(0, len(mu), chunk):
        m_ = mu[i0:i0 + chunk]
        PI, TAU = angular(m_, N)
        S1 = (ac.real @ PI + bc.real @ TAU) + 1j * (ac.imag @ PI + bc.imag @ TAU)
        S2 = (ac.real @ TAU + bc.real @ PI) + 1j * (ac.imag @ TAU + bc.imag @ PI)
        I = np.abs(S1) ** 2 + np.abs(S2) ** 2
        s0 += float(w[i0:i0 + chunk] @ I)
        s1 += float(w[i0:i0 + chunk] @ (I * m_))
    q = efficiencies_from(a, b, x)
    qsca = s0 / x ** 2
    big = q["Qext"] ** 2 / (2.0 * q["Qsca"]) if q["Qsca"] > 0 else 0.0
    return {"Qsca": qsca, "g": s1 / s0 if s0 > 0 else 0.0, "rel_bound": U * (x * x * big + 8 * N + 16),
            "n_nodes": n - 1}


# --- a self-test against published values -------------------------------------------------------------------------
#: Wiscombe, NCAR/TN-140+STR (1979), Appendix III (MIEV1 results printed to 6 significant digits; read from the page
#: images, sources/verification_2026-11-04_p1_mie.md §2): x = 100, his m = 1.5 and 1.5 - 0.1i (exp(+i omega t): our m
#: and S are the complex conjugates). (x, his m, Q_ext, Q_sca, g, S1(0), S1(90), S2(90), S1(180)).
WISCOMBE_1979 = (
    (100.0, 1.5, 2.094388, 2.094388, 0.818246, 5235.97 - 367.988j, 22.4945 + 0.396468j, 16.2341 - 15.5243j,
     40.7669 + 51.7546j),
    (100.0, 1.5 - 0.1j, 2.089822, 1.132134, 0.950392, 5224.55 - 261.694j, 1.19224 + 15.3732j, -0.850854 - 4.66332j,
     -9.54952 - 3.55581j),
)


def _half_unit(v, digits=6):
    v = abs(v)
    return 0.5 * 10.0 ** (math.floor(math.log10(v)) - digits + 1) if v else 0.0


def wiscombe_self_test() -> dict:
    """The engine against Wiscombe's published MIEV1 results (``WISCOMBE_1979``): every printed quantity's deviation in
    units of half a unit of its last printed digit (Q and g printed with 6 decimals; S with 6 significant digits per
    component). {"worst": the largest such ratio (<= 1 passes), "n": the number of quantities, "rows": (name, ours,
    printed, ratio)}. A check of the coefficients' values by published numbers (independent of the engine's own
    identities); it tests the engine at these two spheres, not at the caller's."""
    rows = []
    for x, mw, qe, qs, g, s0, s90_1, s90_2, s180 in WISCOMBE_1979:
        m = complex(mw).conjugate()
        a, b = coefficients(m, x)
        q = efficiencies_from(a, b, x)
        S1, S2 = amplitudes(a, b, np.radians([0.0, 90.0, 180.0]))
        tag = f"x={x:g}, m={mw}"
        for name, ours, his in (("Q_ext", q["Qext"], qe), ("Q_sca", q["Qsca"], qs), ("g", q["g"], g)):
            rows.append((f"{name} ({tag})", ours, his, abs(ours - his) / 0.5e-6))
        for name, ours, his in (("S1(0)", S1[0], s0), ("S1(90)", S1[1], s90_1), ("S2(90)", S2[1], s90_2),
                                ("S1(180)", S1[2], s180)):
            ours = complex(ours).conjugate()
            hu = math.hypot(_half_unit(his.real), _half_unit(his.imag))
            rows.append((f"{name} ({tag})", ours, his, abs(ours - his) / hu))
    return {"worst": max(r[3] for r in rows), "n": len(rows), "rows": rows}


# --- near fields -------------------------------------------------------------------------------------------------
def _spherical(pts):
    p = np.asarray(pts, float)
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    r = np.sqrt(x * x + y * y + z * z)
    th = np.arccos(np.clip(np.where(r > 0, z / np.where(r > 0, r, 1.0), 1.0), -1.0, 1.0))
    ph = np.arctan2(y, x)
    return r, th, ph


def _to_cartesian(Er, Et, Ep, th, ph):
    st, ct, sp, cp = np.sin(th), np.cos(th), np.sin(ph), np.cos(ph)
    ex = Er * st * cp + Et * ct * cp - Ep * sp
    ey = Er * st * sp + Et * ct * sp + Ep * cp
    ez = Er * ct - Et * st
    return np.stack([ex, ey, ez], -1)


def _vsh_sum(coef_e, coef_m, R, Rp, rho, th, ph, kind):
    """The angular and radial sums shared by the four fields. R_n = z_n(rho) rho (Riccati), Rp_n its derivative,
    shape (N, P); coef_e, coef_m the coefficients multiplying the "electric" and "magnetic" families with E_n
    included. kind "E": sum (coef_e N_e1n + coef_m M_o1n); kind "H": sum (coef_e N_o1n + coef_m M_e1n).
    Returns spherical components (r, theta, phi) without the azimuthal factors' signs folded wrongly."""
    N = R.shape[0]
    mu = np.cos(th)
    st = np.sin(th)
    sr = np.zeros(th.shape, complex)
    s_te, s_tm = np.zeros(th.shape, complex), np.zeros(th.shape, complex)  # theta: tau R'/rho and pi R/rho terms
    s_pe, s_pm = np.zeros(th.shape, complex), np.zeros(th.shape, complex)  # phi: pi R'/rho and tau R/rho terms
    p0, p1 = np.zeros_like(mu), np.ones_like(mu)
    for n in range(1, N + 1):
        if n > 1:
            p0, p1 = p1, ((2 * n - 1) * mu * p1 - n * p0) / (n - 1)
        tau = n * mu * p1 - (n + 1) * p0
        ce, cm = coef_e[n - 1], coef_m[n - 1]
        Rn, Rpn = R[n - 1], Rp[n - 1]
        sr += ce * n * (n + 1) * st * p1 * Rn
        s_te += ce * tau * Rpn
        s_tm += cm * p1 * Rn
        s_pe += ce * p1 * Rpn
        s_pm += cm * tau * Rn
    sp, cp = np.sin(ph), np.cos(ph)
    if kind == "E":   # N_e1n: (cos, cos, -sin); M_o1n: (0, cos pi, -sin tau)
        Er = cp * sr / rho ** 2
        Et = cp * (s_te + s_tm) / rho
        Ep = -sp * (s_pe + s_pm) / rho
    else:             # N_o1n: (sin, sin, cos); M_e1n: (0, -sin pi, -cos tau)
        Er = sp * sr / rho ** 2
        Et = sp * (s_te - s_tm) / rho
        Ep = cp * (s_pe - s_pm) / rho
    return Er, Et, Ep


def _radial_outgoing(rho, N):
    """xi_n(rho) and xi_n'(rho), n = 1..N, real rho (array)."""
    P = psi(rho, N)
    X = chi(rho, N)[1:]
    Xi = P - 1j * X
    n = np.arange(1, N + 1)[:, None]
    return Xi[1:], Xi[:-1] - n / rho * Xi[1:]


def _radial_regular(z, N):
    """psi_n(z) exp(-|Im z|) and its derivative psi_n' = psi_{n-1} - (n/z) psi_n (same scaling), n = 1..N."""
    P = psi(z, N)
    n = np.arange(1, N + 1)[:, None]
    return P[1:], P[:-1] - n / z * P[1:]


def near_field(m, x: float, pts, *, n_max: int | None = None, parts: bool = False) -> dict:
    """The electric and magnetic fields at points ``pts`` (shape (..., 3), Cartesian, in units of the radius a): the
    incident wave E = exp(i k z) x-hat (Z H = exp(i k z) y-hat, Z the medium's impedance) plus the scattered series
    outside (r >= a), the internal series inside (r < a; zero inside a perfect conductor, ``m = "pec"``).
    Returns {"E", "H" (= Z H), "inside"}; with ``parts`` also "E_inc", "E_sca", "H_inc", "H_sca" (zero inside)."""
    pec = isinstance(m, str) and m == "pec"
    x = float(x)
    if pec:
        a, b = coefficients_pec(x, n_max=n_max or n_terms(x))
    else:
        m = _check_m(m)
        a, b = coefficients(m, x, n_max=n_max or n_terms(x))
    N = len(a)
    pts = np.asarray(pts, float)
    shape = pts.shape[:-1]
    flat = pts.reshape(-1, 3)
    r, th, ph = _spherical(flat)
    r = np.maximum(r, 1e-9)  # the centre: the regular series' limit (psi_n/rho^2 -> delta_n1 / 3)
    inside = r < 1.0
    E = np.zeros((len(r), 3), complex)
    H = np.zeros((len(r), 3), complex)
    n = np.arange(1, N + 1)
    En = (1j ** n) * (2 * n + 1) / (n * (n + 1.0))
    out = ~inside
    zi = flat[:, 2]
    Einc = np.zeros_like(E)
    Hinc = np.zeros_like(H)
    ph_in = np.exp(1j * x * zi)
    Einc[out, 0] = ph_in[out]
    Hinc[out, 1] = ph_in[out]
    Esca = np.zeros_like(E)
    Hsca = np.zeros_like(H)
    if out.any():
        rho = x * r[out]
        Xi, dXi = _radial_outgoing(rho, N)
        # E_s = sum E_n (i a_n N_e1n - b_n M_o1n);  Z H_s = sum E_n (i b_n N_o1n + a_n M_e1n)
        Er, Et, Ep = _vsh_sum(1j * En * a, -En * b, Xi, dXi, rho, th[out], ph[out], "E")
        Esca[out] = _to_cartesian(Er, Et, Ep, th[out], ph[out])
        Hr, Ht, Hp = _vsh_sum(1j * En * b, En * a, Xi, dXi, rho, th[out], ph[out], "H")
        Hsca[out] = _to_cartesian(Hr, Ht, Hp, th[out], ph[out])
    E[out] = Einc[out] + Esca[out]
    H[out] = Hinc[out] + Hsca[out]
    if inside.any() and not pec:
        c, d = internal_coefficients(m, x, n_max=N)
        z = m * x * r[inside] if m.imag else m.real * x * r[inside]
        Ps, dPs = _radial_regular(z, N)
        # the scaled psi(mkr) exp(-|Im mkr|) against c, d scaled by exp(|Im mx|): the factor exp(|Im mx| - |Im mkr|)
        # is <= 1 inside... applied explicitly
        fac = np.exp(np.abs(np.imag(m * x)) * (r[inside] - 1.0)) if m.imag else 1.0
        # E_1 = sum E_n (c_n M_o1n - i d_n N_e1n);  Z H_1 = -m sum E_n (d_n M_e1n + i c_n N_o1n)
        Er, Et, Ep = _vsh_sum(-1j * En * d, En * c, Ps, dPs, z, th[inside], ph[inside], "E")
        E[inside] = _to_cartesian(Er, Et, Ep, th[inside], ph[inside]) * np.asarray(fac)[..., None]
        Hr, Ht, Hp = _vsh_sum(1j * En * c, En * d, Ps, dPs, z, th[inside], ph[inside], "H")
        H[inside] = -m * _to_cartesian(Hr, Ht, Hp, th[inside], ph[inside]) * np.asarray(fac)[..., None]
    res = {"E": E.reshape(shape + (3,)), "H": H.reshape(shape + (3,)), "inside": inside.reshape(shape)}
    if parts:
        res.update({"E_inc": Einc.reshape(shape + (3,)), "E_sca": Esca.reshape(shape + (3,)),
                    "H_inc": Hinc.reshape(shape + (3,)), "H_sca": Hsca.reshape(shape + (3,))})
    return res
