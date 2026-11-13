# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Three-dimensional wave functions of a particle in a central field (plan P14.5, P14.9):

    psi_nlm(r, theta, phi) = R_nl(r) Y_lm(theta, phi),        R = u(r) / r,

from any radial function: a closed form (hydrogen, ``lfphys.core.quantum.hydrogen.radial``) or a table from the
radial solver (``lfphys.core.quantum.radial``), interpolated smoothly (``RadialTable``). Units are the caller's
(lengths, hbar = mu = 1 unless given).

* **Spherical harmonics** Y_lm with the Condon-Shortley phase, by the stable recurrences of the fully normalised
  associated Legendre functions (P_mm from the sectoral recurrence, then upwards in l; no factorials, any l); the real
  ("chemists'") orbitals Y_l|m| -> sqrt 2 (-1)^m Re Y_l|m| (m > 0, cos m phi) and sqrt 2 (-1)^m Im Y_l|m| (m < 0,
  sin |m| phi), so that p_x is positive along +x.
* **Superpositions** sum_k c_k psi_k exp(-i E_k t / hbar) of stationary states (a cloud that oscillates at the Bohr
  frequencies (E_j - E_k) / hbar).
* **The probability current** j = (hbar/mu) Im(psi* grad psi) by centred differences (any state), and in closed form
  for a single complex state: j = (hbar m / mu) |psi|^2 phi_hat / (r sin theta) (azimuthal rings, divergence free).
* **Matrix elements** <a| r_i |b> and moments <r^k> by quadrature: radial Gauss-Legendre panels, angular Gauss-
  Legendre in cos(theta) times the trapezoid rule in phi (exact for the band-limited angular integrands of Y_lm
  products) - a route independent of the grids the worlds draw on.
* **The energy of a wave function** <T> + <V> by the same quadrature (R' by fourth-order differences, or a radial
  table's own spline derivative): equal to the eigenvalue when R solves the radial equation - a check of a wave
  function independent of how its energy was obtained.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.interpolate import CubicSpline

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Central-field wave functions in 3-D"),
    "statement": T("ψ_nlm = R_nl(r)·Y_lm(θ, φ) from any radial function (a closed form or a table of the radial "
                   "solver with a spline); spherical harmonics by stable recurrences (complex and real orbitals), "
                   "superpositions with Bohr frequencies, the probability current, matrix elements, moments and the "
                   "energy ⟨T⟩ + ⟨V⟩ by quadrature."),
    "validity": T("a non-relativistic spinless particle in a central field; a tabulated radial function is as "
                  "accurate as the radial solver and the spline (measured)"),
    "basis": ["Schrödinger 1926", T("Condon & Shortley, The Theory of Atomic Spectra (1935): phases of Y_lm"),
              T("Holmes & Featherstone, J. Geodesy 76, 279 (2002): normalised recurrences for P_l^m")],
    "conflicts": [],
}


# --- spherical harmonics -------------------------------------------------------------------------------------------
def spherical(x, y, z):
    """(r, theta, phi) of Cartesian points (theta from +z, phi from +x towards +y); theta = 0 at the origin."""
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    rho = np.hypot(x, y)
    r = np.hypot(rho, z)
    return r, np.arctan2(rho, z), np.arctan2(y, x)


def legendre_normalised(l: int, m: int, x, s=None):
    """The fully normalised associated Legendre function with the Condon-Shortley phase, P~_lm(x) =
    sqrt((2l+1)/(4 pi) (l-m)!/(l+m)!) P_lm(x), m >= 0, so that Y_lm = P~_lm(cos theta) e^{i m phi}. Sectoral start
    P~_mm = (-1)^m sqrt((2m+1)!!/(4 pi (2m)!!)) (1 - x^2)^(m/2) built factor by factor, then
    P~_{m+1,m} = sqrt(2m+3) x P~_mm and P~_lm = a_lm (x P~_{l-1,m} - b_lm P~_{l-2,m}),
    a_lm = sqrt((4l^2 - 1)/(l^2 - m^2)), b_lm = sqrt(((l-1)^2 - m^2)/(4(l-1)^2 - 1)). ``s`` = sqrt(1 - x^2) = sin theta
    when known (near the poles 1 - x^2 loses it: x = cos 1e-9 rounds to 1)."""
    if not (0 <= m <= l):
        raise ValueError(T("need 0 ≤ m ≤ l"))
    x = np.asarray(x, float)
    s = np.sqrt(np.clip((1.0 - x) * (1.0 + x), 0.0, None)) if s is None else np.abs(np.asarray(s, float))
    p = np.full(x.shape, 1.0 / math.sqrt(4 * math.pi))
    for k in range(1, m + 1):
        p = -math.sqrt((2 * k + 1) / (2 * k)) * s * p
    if l == m:
        return p
    p_prev, p = p, math.sqrt(2 * m + 3) * x * p
    for ll in range(m + 2, l + 1):
        a = math.sqrt((4 * ll * ll - 1) / (ll * ll - m * m))
        b = math.sqrt(((ll - 1) ** 2 - m * m) / (4 * (ll - 1) ** 2 - 1))
        p_prev, p = p, a * (x * p - b * p_prev)
    return p


def sph_harm(l: int, m: int, theta, phi):
    """Y_lm(theta, phi), complex, Condon-Shortley phase; Y_l,-m = (-1)^m conj(Y_lm)."""
    am = abs(m)
    y = legendre_normalised(l, am, np.cos(theta), np.sin(theta)) * np.exp(1j * am * np.asarray(phi, float))
    if m < 0:
        y = (-1) ** am * np.conj(y)
    return y


def real_harm(l: int, m: int, theta, phi):
    """The real orbital: sqrt 2 (-1)^m Re Y_l|m| = sqrt 2 (-1)^m P~_l|m| cos(|m| phi) (m > 0), Y_l0 (m = 0),
    sqrt 2 (-1)^m Im Y_l|m| = sqrt 2 (-1)^m P~_l|m| sin(|m| phi) (m < 0): normalised, and the p_x lobe along +x is
    positive (the factor (-1)^m undoes the Condon-Shortley phase)."""
    am = abs(m)
    if m == 0:
        return legendre_normalised(l, 0, np.cos(theta)) + 0.0 * np.asarray(phi, float)
    p = legendre_normalised(l, am, np.cos(theta), np.sin(theta))
    phi = np.asarray(phi, float)
    ang = np.cos(am * phi) if m > 0 else np.sin(am * phi)
    return math.sqrt(2.0) * (-1) ** am * p * ang


def orbital_name(l: int, m: int, real: bool) -> str:
    """A spectroscopic name of the angular part: s, p_z, p_x, d_xy, ... (real) or p, m = +1 ... (complex). A symbol, the
    same in every language (a plain str: worlds join and slice it): a real orbital without a Cartesian name (l >= 4) is
    named by its azimuthal factor, g, m = +4 (cos) for cos 4 phi and g, m = -4 (sin) for sin 4 phi."""
    letters = "spdfghik"
    base = letters[l] if l < len(letters) else f"l={l}"
    if not real:
        return base if l == 0 else f"{base}, m = {m:+d}"
    names = {(1, 0): "z", (1, 1): "x", (1, -1): "y", (2, 0): "z²", (2, 1): "xz", (2, -1): "yz", (2, 2): "x²−y²",
             (2, -2): "xy", (3, 0): "z³", (3, 1): "xz²", (3, -1): "yz²", (3, 2): "z(x²−y²)", (3, -2): "xyz",
             (3, 3): "x(x²−3y²)", (3, -3): "y(3x²−y²)"}
    sub = names.get((l, m))
    if l == 0:
        return base
    if sub:
        return f"{base}_{sub}"
    return f"{base}, m = {m:+d}" + ("" if m == 0 else " (cos)" if m > 0 else " (sin)")


# --- radial functions ------------------------------------------------------------------------------------------------
class RadialTable:
    """R(r) from a table of u(r) = r R(r) (the radial solver's grid, u(0) = 0, u normalised to int u^2 dr = 1). The
    smooth function f(r) = R(r) / r^l (finite at the origin) is interpolated by a cubic spline through the samples and
    r = 0, so R = r^l f(r) keeps the behaviour r^l of the true function at the origin; beyond the table R = 0 (the
    solver's box). The value f(0) is a least-squares cubic through samples 2-13, and the spline leaves out sample 1:
    the radial solver's error is largest at its first point (measured for -1/r, N = 800: 6 % in f for l = 1, against
    5e-3 at the second and < 1e-3 from the fourth), and an interpolating extrapolation would amplify the point-to-point
    error near the origin some 60-fold. Measured against the closed form (tests/test_central3d.py): hydrogen, box 40,
    N = 800, max |R_table - R| / max |R| = 4.2e-4 (1s), 3.1e-4 (2p)."""

    def __init__(self, r, u, l: int):
        r, u = np.asarray(r, float), np.asarray(u, float)
        if r[0] <= 0 or len(r) < 16:
            raise ValueError(T("the table starts at r > 0 and has at least 16 points"))
        self.l = int(l)
        self.r_max = float(r[-1])
        f = u / r ** (self.l + 1)
        f0 = float(np.polyval(np.polyfit(r[1:13], f[1:13], 3), 0.0))
        self._f = CubicSpline(np.concatenate([[0.0], r[1:]]), np.concatenate([[f0], f[1:]]))

    def __call__(self, r):
        r = np.asarray(r, float)
        out = r ** self.l * self._f(np.clip(r, 0.0, self.r_max))
        return np.where(r <= self.r_max, out, 0.0)

    def derivative(self, r):
        """dR/dr = l r^(l-1) f + r^l f' of the same spline (exact for it; zero beyond the table)."""
        r = np.asarray(r, float)
        rc = np.clip(r, 0.0, self.r_max)
        out = rc ** self.l * self._f(rc, 1)
        if self.l:
            out = out + self.l * rc ** (self.l - 1) * self._f(rc)
        return np.where(r <= self.r_max, out, 0.0)


@dataclass
class Orbital:
    """A stationary state R(r) Y_lm (complex) or R(r) Y_l,m^real (real orbital), its energy and a label."""
    R: Callable
    l: int
    m: int
    real: bool = False
    energy: float = 0.0
    label: str = ""

    def angular(self, theta, phi):
        return real_harm(self.l, self.m, theta, phi) if self.real else sph_harm(self.l, self.m, theta, phi)

    def psi(self, x, y, z):
        r, th, ph = spherical(x, y, z)
        return self.R(r) * self.angular(th, ph)


@dataclass
class Superposition:
    """sum_k c_k psi_k exp(-i E_k t / hbar); the coefficients are normalised on construction (the states are taken
    orthonormal: distinct (n, l, m))."""
    orbitals: list
    coefs: list = field(default_factory=list)
    hbar: float = 1.0

    def __post_init__(self):
        c = np.asarray(self.coefs if self.coefs else [1.0] * len(self.orbitals), complex)
        self.c = c / np.linalg.norm(c)

    def psi(self, x, y, z, t: float = 0.0):
        out = 0.0
        for ck, o in zip(self.c, self.orbitals):
            out = out + ck * np.exp(-1j * o.energy * t / self.hbar) * o.psi(x, y, z)
        return out

    def frequencies(self):
        """The Bohr frequencies |E_j - E_k| / hbar (rad per unit time) of the pairs present."""
        E = [o.energy for o in self.orbitals]
        return sorted({abs(a - b) / self.hbar for i, a in enumerate(E) for b in E[i + 1:] if abs(a - b) > 0})


# --- the current -----------------------------------------------------------------------------------------------------
def current(state, x, y, z, t: float = 0.0, mu: float = 1.0, hbar: float = 1.0, h: float = 1e-5):
    """j = (hbar/mu) Im(psi* grad psi) at points, the gradient by centred differences of step h (relative error
    ~ (h k)^2 / 6 for wavenumbers k of the state). ``state``: an Orbital or a Superposition. Returns (3, ...)."""
    def f(a, b, c):
        return state.psi(a, b, c, t) if isinstance(state, Superposition) else state.psi(a, b, c)
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    p = f(x, y, z)
    g = [(f(x + h, y, z) - f(x - h, y, z)) / (2 * h), (f(x, y + h, z) - f(x, y - h, z)) / (2 * h),
         (f(x, y, z + h) - f(x, y, z - h)) / (2 * h)]
    return np.stack([hbar / mu * np.imag(np.conj(p) * gi) for gi in g])


def azimuthal_current(orbital: Orbital, x, y, z, mu: float = 1.0, hbar: float = 1.0):
    """The closed form for a complex state R Y_lm: j = (hbar m / mu) |psi|^2 phi_hat / (r sin theta) = (hbar m / mu)
    |psi|^2 (-y, x, 0) / (x^2 + y^2); zero for real orbitals (a real wave carries no current)."""
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    if orbital.real or orbital.m == 0:
        return np.zeros((3,) + np.broadcast(x, y, z).shape)
    rho2 = x * x + y * y
    w = np.where(rho2 > 0, hbar * orbital.m / mu * np.abs(orbital.psi(x, y, z)) ** 2 / np.where(rho2 > 0, rho2, 1.0),
                 0.0)
    return np.stack([-y * w, x * w, 0.0 * w])


# --- quadratures -----------------------------------------------------------------------------------------------------
def radial_quadrature(r_max: float, panels: int = 200, nodes: int = 16):
    """Gauss-Legendre panels on [0, r_max] (nodes, weights)."""
    xg, wg = np.polynomial.legendre.leggauss(nodes)
    edges = np.linspace(0.0, r_max, panels + 1)
    mid, half = 0.5 * (edges[1:] + edges[:-1]), 0.5 * np.diff(edges)
    return (mid[:, None] + half[:, None] * xg).ravel(), (half[:, None] * wg).ravel()


def angular_quadrature(l_max: int):
    """Product rule exact for polynomials of degree <= 2 l_max + 4 in (x, y, z) on the sphere: Gauss-Legendre in
    cos(theta), the trapezoid in phi. Returns (theta, phi, weights) on a mesh (flat)."""
    nt = l_max + 4
    nphi = 2 * l_max + 6
    ct, wt = np.polynomial.legendre.leggauss(nt)
    ph = 2 * math.pi * np.arange(nphi) / nphi
    T, P = np.meshgrid(np.arccos(ct), ph, indexing="ij")
    W = np.broadcast_to(wt[:, None] * (2 * math.pi / nphi), T.shape)
    return T.ravel(), P.ravel(), W.ravel()


def moment(R: Callable, k: float, r_max: float, panels: int = 400) -> float:
    """<r^k> = int R^2 r^(k+2) dr over [0, r_max] by Gauss-Legendre panels."""
    r, w = radial_quadrature(r_max, panels)
    return float(np.sum(w * R(r) ** 2 * r ** (k + 2)))


def dipole(a: Orbital, b: Orbital, r_max: float, panels: int = 400) -> np.ndarray:
    """<a| (x, y, z) |b> (complex 3-vector): the radial integral int R_a R_b r^3 dr by panels, the angular integral of
    conj(Y_a) n Y_b by the exact product rule."""
    r, w = radial_quadrature(r_max, panels)
    rad = float(np.sum(w * a.R(r) * b.R(r) * r**3))
    th, ph, wa = angular_quadrature(max(a.l, b.l) + 1)
    ya, yb = a.angular(th, ph), b.angular(th, ph)
    n = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
    return rad * np.sum(wa * np.conj(ya) * n * yb, axis=1)


def box_radius(R: Callable, frac: float, r_max: float, panels: int = 400) -> float:
    """The radius inside which the probability int R^2 r^2 dr reaches 1 - frac."""
    r, w = radial_quadrature(r_max, panels)
    order = np.argsort(r)
    c = np.cumsum((w * R(r) ** 2 * r**2)[order])
    return float(r[order][min(len(r) - 1, int(np.searchsorted(c, (1.0 - frac) * c[-1])))])


def derivative_fd(R: Callable, scale: float) -> Callable:
    """dR/dr by the fourth-order centred difference [R(r-2h) - 8R(r-h) + 8R(r+h) - R(r+2h)] / 12h with
    h = 1e-3 min(r, scale) (``scale``: the length over which R changes, e.g. n a / Z): truncation ~ (h/scale)^4 / 30
    ~ 1e-13 relatively, round-off ~ 1.5 eps |R| / h; the step shrinks towards the origin so that no point crosses it
    (the weight r^2 of the energy integrals makes the larger relative round-off there harmless)."""
    def dR(r):
        r = np.asarray(r, float)
        h = 1e-3 * np.minimum(np.abs(r), scale) + 1e-300
        return (R(r - 2 * h) - 8 * R(r - h) + 8 * R(r + h) - R(r + 2 * h)) / (12 * h)
    return dR


def energy_terms(R: Callable, dR: Callable, l: int, V: Callable, r_max: float, mu: float = 1.0, hbar: float = 1.0,
                 panels: int = 400):
    """(<T>, <V>) of R(r) Y_lm by Gauss-Legendre panels: <T> = hbar^2/(2 mu) int (R'^2 r^2 + l(l+1) R^2) dr (the
    kinetic energy after an integration by parts; R'^2 from ``dR``), <V> = int V R^2 r^2 dr. Their sum is the energy
    when R solves the radial equation: a check of a wave function independent of how its energy was obtained."""
    r, w = radial_quadrature(r_max, panels)
    Rv, dRv = R(r), dR(r)
    T = hbar * hbar / (2 * mu) * float(np.sum(w * (dRv * dRv * r * r + l * (l + 1) * Rv * Rv)))
    return T, float(np.sum(w * V(r) * Rv * Rv * r * r))
