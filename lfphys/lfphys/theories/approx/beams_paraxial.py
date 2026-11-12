# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Paraxial beams with orbital angular momentum (plan P14.7): Laguerre-Gauss and Hermite-Gauss modes in closed form,
the Hermite-Gauss <-> Laguerre-Gauss decomposition (the astigmatic mode converter as coefficients), the Fresnel
propagation of any vortex beam given by its order-l radial spectrum, and the closed forms of the energy flow lines
and of the helical equiphase surfaces of a Laguerre-Gauss mode.

The paraxial equation is an approximation of Helmholtz's: the engine has the exact propagation (``lfphys.core.
optics.beams``: Bessel beams, exact scalar vortex beams and exact vector beams of the same spectrum;
``lfphys.core.optics.angular_spectrum``), and the tests measure the difference: of order (lambda / w0)^2 for the scalar
field and for the transverse components of the vector beam; a mode times a uniform polarisation has no longitudinal
field, which the exact vector beam has at first order, |E_z| / |E| ~ lambda / (pi w0) (review B8-beams, O1).

Conventions: time dependence exp(-i omega t); the full field E = u(x, y, z) exp(i k z) times a uniform polarisation
vector; u obeys the paraxial equation

    d2u/dx2 + d2u/dy2 + 2 i k du/dz = 0.

z_R = k w0^2 / 2, w(z) = w0 sqrt(1 + z^2/z_R^2), 1/R(z) = z / (z^2 + z_R^2) (a diverging wave front for z > 0 has
the phase + k r^2 / (2 R)), psi(z) = arctan(z / z_R) (Gouy).

* Laguerre-Gauss, normalised to int |u|^2 dx dy = 1 at every z:
      LG_{p,l} = (C_pl / w) (sqrt2 r / w)^|l| L_p^|l|(2 r^2 / w^2) exp(-r^2 / w^2) exp(i k r^2 / (2 R)) exp(i l phi)
                 exp(-i (2p + |l| + 1) psi),      C_pl = sqrt(2 p! / (pi (p + |l|)!)).
* Hermite-Gauss (physicists' Hermite polynomials):
      HG_{n,m} = (C_nm / w) H_n(sqrt2 x / w) H_m(sqrt2 y / w) exp(-r^2 / w^2) exp(i k r^2 / (2 R)) exp(-i (n+m+1) psi),
      C_nm = sqrt(2 / (pi 2^(n+m) n! m!)).
* HG <-> LG (the coefficients of Beijersbergen, Allen, van der Veen & Woerdman, Opt. Commun. 96, 123 (1993), as
  they are commonly reproduced; the paper itself was not obtained, see the sources file): with N = n + m,
      b(n, m, k) = sqrt((N - k)! k! / (2^N n! m!)) (1/k!) d^k/dt^k [(1 - t)^n (1 + t)^m] at t = 0
  (the coefficient of t^k, summed exactly in integers). In the conventions above (measured, ``tests/test_beams_paraxial``):
      sum_k b(n, m, k)       HG_{N-k,k}(x, y) = HG_{n,m}(u, v),  u = (x - y)/sqrt2, v = (x + y)/sqrt2  (turned by 45 deg)
      sum_k i^k b(n, m, k)   HG_{N-k,k}(x, y) = (-1)^min(n,m) LG_{min(n,m), m - n}(x, y)
  at every z (all terms have the same Gouy phase (N + 1) psi). The astigmatic converter multiplies the coefficient of
  HG_{N-k,k} by exp(i k delta) (its Gouy phase difference between the two axes): delta = pi/2 turns the diagonal HG
  mode into the LG mode, delta = pi turns LG_{p,l} into LG_{p,-l} (the image inversion; tested).
* Fresnel propagation of a vortex beam u(r, phi, 0) = exp(i l phi) int_0^inf A(q) J_l(q r) q dq (A: the order-l
  Hankel transform of the radial profile; ``lfphys.core.optics.beams.lg_waist_spectrum`` gives it for an LG waist):
      u(r, phi, z) = exp(i l phi) int A(q) J_l(q r) exp(-i q^2 z / (2 k)) q dq
  (the paraxial transfer function exp(i (k_z - k) z) ~ exp(-i q^2 z / (2k))); for the LG spectrum it equals the closed
  form above (a test of both).
* Energy flow of the paraxial field: j = (Im(u* grad_T u) / k, |u|^2) (the current Im(U* grad U)/k of
  ``angular_spectrum`` to leading order). For LG_{p,l} its lines keep rho = r / w(z) and turn as
      phi(z) - phi(z0) = (l / (2 rho^2)) (psi(z) - psi(z0))
  (the azimuthal current l |u|^2 / (k r); M. J. Padgett & L. Allen, Opt. Commun. 121, 36 (1995) — not obtained, the
  closed form is derived here and tested against the traced lines).
* Equiphase surfaces of LG_{p,l} at time t: arg[u exp(i (k z - omega t))] = Phi0 (mod 2 pi):
      phi_j = (Phi0 + omega t - k z - k r^2 / (2 R) + (2p + |l| + 1) psi - pi [L_p^|l| < 0] + 2 pi j) / l, j = 0..|l|-1:
  |l| intertwined helicoids of pitch |l| lambda.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import eval_genlaguerre, eval_hermite, jv

from . import gaussian_beam as GB

ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": "Параксиальные пучки с орбитальным моментом: моды Лагерра–Гаусса и Эрмита–Гаусса",
    "statement": "Решения параксиального волнового уравнения: моды LG_pl (фаза e^{ilφ}, фаза Гюи (2p+|l|+1)·arctan(z/z_R)) "
                 "и HG_nm; разложение HG ↔ LG (астигматический преобразователь мод как коэффициенты); френелевское "
                 "распространение вихревого пучка по его спектру порядка l; линии потока энергии и винтовые "
                 "поверхности равной фазы в замкнутой форме.",
    "validity": "параксиальность: малая расходимость, w0 ≫ λ; ошибка скалярного поля и поперечных компонент против "
                "точного решения порядка (λ/w0)² (измерена в тестах); поляризация однородна, продольного поля нет — "
                "у точного пучка оно первого порядка, λ/(πw0)",
    "basis": ["Allen, Beijersbergen, Spreeuw, Woerdman, Phys. Rev. A 45, 8185 (1992)",
              "Beijersbergen, Allen, van der Veen, Woerdman, Opt. Commun. 96, 123 (1993) — коэффициенты b(n,m,k)",
              "Siegman, Lasers (1986), гл. 16–17"],
    "conflicts": ["lfphys.core.optics.beams: точный векторный пучок того же спектра отличается при сильной "
                  "фокусировке (w0 ~ λ): продольное поле, спин-орбитальное расщепление L_z и S_z",
                  "lfphys.core.optics.angular_spectrum: точное распространение отличается на O((λ/w0)²)"],
}


# --- the Gaussian beam's parameters (those of lfphys.theories.approx.gaussian_beam: the same conventions) ------------
rayleigh = GB.rayleigh


def params(z, k: float, w0: float):
    """(w(z), 1/R(z), psi(z)) for arrays z: the width of ``gaussian_beam.width``, the curvature 1/R = z/(z^2 + z_R^2)
    and the two-dimensional Gouy phase arctan(z/z_R)."""
    z = np.asarray(z, float)
    zr = rayleigh(k, w0)
    return GB.width(z, k, w0), z / (z * z + zr * zr), np.arctan(z / zr)


def gouy(N: int, z, k: float, w0: float):
    """The Gouy phase lag (N + 1) arctan(z / z_R) of a mode of order N = 2p + |l| = n + m."""
    return (N + 1) * np.arctan(np.asarray(z, float) / rayleigh(k, w0))


# --- modes ---------------------------------------------------------------------------------------------------------------
def lg_norm(p: int, l: int) -> float:
    a = abs(l)
    return math.sqrt(2.0 * math.factorial(p) / (math.pi * math.factorial(p + a)))


def lg(p: int, l: int, x, y, z, k: float, w0: float):
    """LG_{p,l}(x, y, z): the envelope u (multiply by exp(i k z) for the field); arrays broadcast."""
    if p < 0:
        raise ValueError("lg: p >= 0")
    x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
    w, invR, psi = params(z, k, w0)
    r2 = x * x + y * y
    a = abs(l)
    rho2 = 2.0 * r2 / (w * w)
    amp = lg_norm(p, l) / w * rho2 ** (0.5 * a) * eval_genlaguerre(p, a, rho2) * np.exp(-r2 / (w * w))
    return amp * np.exp(1j * (0.5 * k * r2 * invR + l * np.arctan2(y, x) - (2 * p + a + 1) * psi))


def lg_gradient(p: int, l: int, x, y, z, k: float, w0: float, h: float | None = None):
    """(du/dx, du/dy) of LG_{p,l} by a fourth-order central difference of the closed form (step h, default w0 / 400):
    a numerical gradient of an analytic function, for the paraxial current."""
    h = h or w0 / 400.0
    f = lambda xx, yy: lg(p, l, xx, yy, z, k, w0)  # noqa: E731
    gx = (-f(x + 2 * h, y) + 8 * f(x + h, y) - 8 * f(x - h, y) + f(x - 2 * h, y)) / (12 * h)
    gy = (-f(x, y + 2 * h) + 8 * f(x, y + h) - 8 * f(x, y - h) + f(x, y - 2 * h)) / (12 * h)
    return gx, gy


def hg_norm(n: int, m: int) -> float:
    return math.sqrt(2.0 / (math.pi * 2 ** (n + m) * math.factorial(n) * math.factorial(m)))


def hg(n: int, m: int, x, y, z, k: float, w0: float):
    """HG_{n,m}(x, y, z): the envelope u; arrays broadcast."""
    if n < 0 or m < 0:
        raise ValueError("hg: n, m >= 0")
    x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
    w, invR, psi = params(z, k, w0)
    s = math.sqrt(2.0)
    r2 = x * x + y * y
    amp = hg_norm(n, m) / w * eval_hermite(n, s * x / w) * eval_hermite(m, s * y / w) * np.exp(-r2 / (w * w))
    return amp * np.exp(1j * (0.5 * k * r2 * invR - (n + m + 1) * psi))


# --- HG <-> LG -------------------------------------------------------------------------------------------------------------
def b_coeff(n: int, m: int, kk: int) -> float:
    """b(n, m, k) = sqrt((N-k)! k! / (2^N n! m!)) * [t^k] (1 - t)^n (1 + t)^m  (exact integer coefficient)."""
    N = n + m
    if not 0 <= kk <= N:
        raise ValueError("b_coeff: 0 <= k <= n + m")
    c = sum(math.comb(n, j) * (-1) ** j * math.comb(m, kk - j) for j in range(0, kk + 1) if kk - j <= m)
    return math.sqrt(math.factorial(N - kk) * math.factorial(kk) / (2 ** N * math.factorial(n) * math.factorial(m))) * c


def diagonal_hg_coefficients(n: int, m: int) -> np.ndarray:
    """c_k such that HG_{n,m}((x - y)/sqrt2, (x + y)/sqrt2) = sum_k c_k HG_{N-k,k}(x, y) (real)."""
    return np.array([b_coeff(n, m, kk) for kk in range(n + m + 1)])


def lg_hg_coefficients(p: int, l: int) -> np.ndarray:
    """c_k (complex) such that LG_{p,l} = sum_k c_k HG_{N-k,k}, N = 2p + |l| (in this module's conventions):
    n = p + max(-l, 0), m = p + max(l, 0) (so that m - n = l), c_k = (-1)^p i^k b(n, m, k)."""
    n, m = p + max(-l, 0), p + max(l, 0)
    return np.array([(-1) ** p * (1j ** kk) * b_coeff(n, m, kk) for kk in range(n + m + 1)])


def mode_converter(coeffs, delta: float = math.pi / 2) -> np.ndarray:
    """The astigmatic mode converter in the HG basis of its axes: the coefficient of HG_{N-k,k} is multiplied by
    exp(i k delta) (delta: the converter's Gouy phase difference between its two axes; pi/2 or pi)."""
    c = np.asarray(coeffs, complex)
    return c * np.exp(1j * delta * np.arange(len(c)))


def hg_sum(coeffs, x, y, z, k: float, w0: float):
    """sum_k c_k HG_{N-k,k}(x, y, z), N = len(coeffs) - 1."""
    N = len(coeffs) - 1
    return sum(c * hg(N - kk, kk, x, y, z, k, w0) for kk, c in enumerate(coeffs) if c != 0)


# --- Fresnel propagation of a vortex beam given by its order-l spectrum ---------------------------------------------
_GL_X, _GL_W = np.polynomial.legendre.leggauss(16)


def fresnel_vortex(spectrum, l: int, k: float, r, z: float, q_max: float, panels: int | None = None):
    """u(r, z) exp(-i l phi) of the paraxial beam whose waist-plane field is exp(i l phi) int A(q) J_l(q r) q dq:
    int_0^q_max A(q) J_l(q r) exp(-i q^2 z / (2k)) q dq by composite Gauss-Legendre (panels of at most a quarter
    oscillation of J_l and of the Fresnel phase; error estimated by doubling). Returns (values, error estimate)."""
    r = np.atleast_1d(np.asarray(r, float))
    rmax = float(np.max(np.abs(r))) if r.size else 0.0
    osc = q_max * rmax + q_max * q_max * abs(z) / (2 * k)
    n0 = panels or int(math.ceil(4 * osc / (2 * math.pi))) + 16

    def integ(npan):
        e = np.linspace(0.0, q_max, npan + 1)
        lo, hi = e[:-1, None], e[1:, None]
        q = (0.5 * (hi - lo) * _GL_X[None, :] + 0.5 * (hi + lo)).ravel()
        wq = (0.5 * (hi - lo) * _GL_W[None, :]).ravel()
        f = wq * np.asarray(spectrum(q), complex) * q * np.exp(-1j * q * q * z / (2 * k))
        return jv(l, np.outer(r, q)) @ f
    v1, v2 = integ(n0), integ(2 * n0)
    return v2, float(np.max(np.abs(v2 - v1))) if r.size else 0.0


def fresnel_table_nodes(l: int, k: float, r_max: float, z_max: float, q_max: float) -> int:
    """The number of quadrature nodes ``fresnel_table`` uses (for sizing it before it is built; review B8-beams, O5)."""
    osc = q_max * r_max + q_max * q_max * abs(z_max) / (2 * k)
    return 16 * (int(math.ceil(osc / (2 * math.pi))) + 16)


def fresnel_table(spectrum, l: int, k: float, r, z, q_max: float):
    """The same Fresnel integral on a grid r (nr) x z (nz): array (nz, nr) of u(r, z) exp(-i l phi); the Bessel
    matrix is computed once (nodes for the largest r and |z|; one panel of 16 nodes per oscillation, plus 16:
    ``fresnel_table_nodes``)."""
    r = np.asarray(r, float)
    z = np.asarray(z, float)
    npan = fresnel_table_nodes(l, k, float(np.max(r)), float(np.max(np.abs(z))), q_max) // 16
    e = np.linspace(0.0, q_max, npan + 1)
    lo, hi = e[:-1, None], e[1:, None]
    q = (0.5 * (hi - lo) * _GL_X[None, :] + 0.5 * (hi + lo)).ravel()
    wq = (0.5 * (hi - lo) * _GL_W[None, :]).ravel() * np.asarray(spectrum(q), complex) * q
    ph = np.exp(-1j * np.outer(z, q * q) / (2 * k)) * wq
    return ph @ jv(l, np.outer(r, q)).T


# --- closed forms of the flow and of the phase surfaces -----------------------------------------------------------------
def current(p: int, l: int, x, y, z, k: float, w0: float):
    """The paraxial energy current (j_x, j_y, j_z) = (Im(u* du/dx)/k, Im(u* du/dy)/k, |u|^2) of LG_{p,l} (gradient by
    ``lg_gradient``)."""
    u = lg(p, l, x, y, z, k, w0)
    gx, gy = lg_gradient(p, l, x, y, z, k, w0)
    return np.stack([np.imag(np.conj(u) * gx) / k, np.imag(np.conj(u) * gy) / k, np.abs(u) ** 2])


def field_current(u_fn, x, y, z, k: float, h: float):
    """The same paraxial current of any field ``u_fn(x, y, z)`` (the envelope u, or u exp(i k z): the carrier drops out
    of Im(u* grad_T u)), with the transverse gradient by fourth-order central differences of step h."""
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    u = u_fn(x, y, z)
    d = lambda f: (-f(2) + 8 * f(1) - 8 * f(-1) + f(-2)) / (12 * h)  # noqa: E731
    gx = d(lambda s: u_fn(x + s * h, y, z))
    gy = d(lambda s: u_fn(x, y + s * h, z))
    return np.stack([np.imag(np.conj(u) * gx) / k, np.imag(np.conj(u) * gy) / k, np.abs(u) ** 2])


def flow_line(l: int, r0: float, phi0: float, z0: float, z, k: float, w0: float):
    """The closed-form energy flow line of LG_{p,l} through (r0, phi0, z0): rho = r / w(z) is kept and
    phi(z) = phi0 + l / (2 rho^2) (psi(z) - psi(z0)). Returns (x, y) at the z values (any p)."""
    z = np.asarray(z, float)
    w, _, psi = params(z, k, w0)
    w_0, _, psi0 = params(z0, k, w0)
    rho = r0 / float(w_0)
    phi = phi0 + l / (2 * rho * rho) * (psi - float(psi0))
    r = rho * w
    return r * np.cos(phi), r * np.sin(phi)


def helix_phi(p: int, l: int, r, z, k: float, w0: float, phase0: float = 0.0, omega_t: float = 0.0):
    """Closed form of the equiphase surfaces arg[u exp(i (k z - omega t))] = phase0 of LG_{p,l} (l != 0): the
    azimuths phi_j(r, z), j = 0..|l|-1, in [0, 2 pi): array (|l|, *shape)."""
    if l == 0:
        raise ValueError("helix_phi: l != 0 (for l = 0 the surfaces are not helicoids)")
    r, z = np.broadcast_arrays(np.asarray(r, float), np.asarray(z, float))
    w, invR, psi = params(z, k, w0)
    sign = np.where(eval_genlaguerre(p, abs(l), 2 * r * r / (w * w)) < 0, math.pi, 0.0)
    base = phase0 + omega_t - k * z - 0.5 * k * r * r * invR + (2 * p + abs(l) + 1) * psi - sign
    j = np.arange(abs(l)).reshape((-1,) + (1,) * r.ndim)
    return np.mod((base[None] + 2 * math.pi * j) / l, 2 * math.pi)
