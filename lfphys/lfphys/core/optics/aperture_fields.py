# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Exact fields behind an aperture in the plane z = 0 for given scalar values on that plane (the Rayleigh-Sommerfeld
solution of the first kind, which is what the angular spectrum computes), by routes without FFTs: independent
references for ``lfphys.core.optics.angular_spectrum`` (review of B1, B1-2, B1-13, B1-18).

RS-I with U0 on z = 0: U(P) = (z/2pi) int U0 e^{ikR} (1 - ikR) / R^3 dS. In polar coordinates (rho, phi) around the
foot of P the radial integral is closed: with R dR = rho drho, d/dR(-e^{ikR}/R) = e^{ikR}(1 - ikR)/R^2, so a unit field
on the radial interval [t1, t2] of direction phi gives (1/2pi)(g(t1) - g(t2)) dphi, g(t) = z e^{ikR(t)}/R(t),
R(t) = sqrt(z^2 + t^2).

* ``circle_on_axis``: a unit disc of radius a, on its axis: U = e^{ikz} - (z/R) e^{ikR}, R = sqrt(z^2 + a^2) (closed;
  Osterberg & Smith, JOSA 51, 1050 (1961)).
* ``rectangles_field``: a union of disjoint unit rectangles, at any point (x0, y0, z): the remaining integral over phi
  by composite Gauss-Legendre, split at the corner directions (where the ray changes faces) and into panels of at
  most a quarter oscillation of e^{ikR}; the error is estimated by doubling the panels.
* Spectra (Fourier transforms A(q) = int U0 e^{-i q.r} d^2 r of the same sources, closed forms) for an exact source
  of the angular spectrum (``angular_spectrum.Spectral``; the arguments broadcast, so on an open grid a separable
  spectrum costs only its factors): ``rect_spectrum`` (a product of
  (e^{-i q a} - e^{-i q b}) / (i q) per axis, summed over rectangles), ``interval_spectrum`` (1-D),
  ``disc_spectrum`` (2 pi a^2 J1(q a) / (q a)), ``gaussian_spectrum`` (pi w^2 e^{-q^2 w^2 / 4}); ``rotated`` turns a
  source about the axis (A(R q) for U0(R r)).
* ``gaussian_field``: U0 = exp(-r^2/w^2), at distance r from the axis: the defining Hankel integral
  (w^2/2) int_0^inf q e^{-q^2 w^2/4} J0(q r) e^{i k_z z} dq, the propagating part written in c = cos(theta) (the phase
  k z c is linear in c) and cut into panels of a quarter oscillation, the evanescent part in s = sqrt(q^2 - k^2);
  composite Gauss-Legendre with an error estimate (review B1-13: a split [0, k/2, k] was 2.9e-6 off at k z = 1676;
  the tests compare with mpmath).
"""

from __future__ import annotations

import cmath
import math

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Exact fields behind an aperture (references without FFTs)"),
    "statement": T("The Rayleigh–Sommerfeld field behind an aperture in the plane z = 0: a disc on the axis (closed "
                   "form), a union of rectangles at any point (a one-dimensional integral over the angle), a Gaussian "
                   "field (a Hankel integral), with an error estimate; independent references for the angular-spectrum "
                   "computation."),
    "validity": T("a scalar field given on the plane z = 0 (Rayleigh–Sommerfeld boundary values), z > 0"),
    "basis": [T("Goodman, Introduction to Fourier Optics, ch. 3"), "Osterberg & Smith, JOSA 51, 1050 (1961)"],
    "conflicts": [],
}

_GL_X, _GL_W = np.polynomial.legendre.leggauss(16)


def circle_on_axis(k: float, a: float, z: float) -> complex:
    """U(0, 0, z) behind a unit disc of radius a: e^{ikz} - (z/R) e^{ikR}, R = sqrt(z^2 + a^2)."""
    if z <= 0:
        raise ValueError("circle_on_axis: z > 0")
    R = math.hypot(z, a)
    return cmath.exp(1j * k * z) - z / R * cmath.exp(1j * k * R)


def _ray_box(c, s, xa, xb, ya, yb):
    """Parameters t_in, t_out (arrays) where the rays t (c, s), t >= 0 cross the box; t_out <= t_in: no crossing."""
    big = np.inf
    with np.errstate(divide="ignore", invalid="ignore"):
        tx1, tx2 = xa / c, xb / c
        ty1, ty2 = ya / s, yb / s
    lo_x = np.where(c != 0, np.minimum(tx1, tx2), np.where((xa <= 0) & (0 <= xb), -big, big))
    hi_x = np.where(c != 0, np.maximum(tx1, tx2), np.where((xa <= 0) & (0 <= xb), big, -big))
    lo_y = np.where(s != 0, np.minimum(ty1, ty2), np.where((ya <= 0) & (0 <= yb), -big, big))
    hi_y = np.where(s != 0, np.maximum(ty1, ty2), np.where((ya <= 0) & (0 <= yb), big, -big))
    return np.maximum(np.maximum(lo_x, lo_y), 0.0), np.minimum(hi_x, hi_y)


def _g(k, z, t):
    R = np.sqrt(z * z + t * t)
    return np.where(np.isfinite(t), z * np.exp(1j * k * np.where(np.isfinite(R), R, 0.0)) / R, 0.0)


def _rect_integrand(k, z, boxes, phi):
    c, s = np.cos(phi), np.sin(phi)
    total = np.zeros(phi.shape, complex)
    for xa, xb, ya, yb in boxes:
        t1, t2 = _ray_box(c, s, xa, xb, ya, yb)
        hit = t2 > t1
        total += np.where(hit, _g(k, z, np.where(hit, t1, 0.0)) - _g(k, z, np.where(hit, t2, 0.0)), 0.0)
    return total / (2 * math.pi)


def rectangles_field(k: float, rects, z: float, x0: float = 0.0, y0: float = 0.0, panels: int | None = None):
    """(U(x0, y0, z), error estimate) behind a union of disjoint unit rectangles (xa, xb, ya, yb) on z = 0."""
    if z <= 0:
        raise ValueError("rectangles_field: z > 0")
    boxes = [(xa - x0, xb - x0, ya - y0, yb - y0) for xa, xb, ya, yb in rects]
    cuts = {0.0, 2 * math.pi}
    for xa, xb, ya, yb in boxes:
        for cx in (xa, xb):
            for cy in (ya, yb):
                if cx or cy:
                    cuts.add(math.atan2(cy, cx) % (2 * math.pi))
        for ang in (0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi):  # axis directions (a ray along a face's line)
            cuts.add(ang)
    edges = sorted(cuts)
    rmax = max(math.hypot(max(abs(xa), abs(xb)), max(abs(ya), abs(yb))) for xa, xb, ya, yb in boxes)
    swing = k * (math.hypot(z, rmax) - z)  # the largest phase change of e^{ikR} along a face

    def integrate(npan):
        val = 0.0 + 0.0j
        for a, b in zip(edges[:-1], edges[1:]):
            if b - a < 1e-15:
                continue
            nodes = np.linspace(a, b, npan + 1)
            lo, hi = nodes[:-1, None], nodes[1:, None]
            phi = 0.5 * (hi - lo) * _GL_X[None, :] + 0.5 * (hi + lo)
            f = _rect_integrand(k, z, boxes, phi.ravel()).reshape(phi.shape)
            val += np.sum(0.5 * (hi - lo) * _GL_W[None, :] * f)
        return complex(val)

    n1 = panels or int(math.ceil(4 * swing / (2 * math.pi))) + 8
    v1, v2 = integrate(n1), integrate(2 * n1)
    return v2, abs(v2 - v1)


def gaussian_field(k: float, w: float, z: float, r: float = 0.0, deriv: str | None = None) -> tuple[complex, float]:
    """(U(r, z), error estimate) for the field exp(-r^2/w^2) given on z = 0 (exact, by quadrature): composite
    Gauss-Legendre, 16 nodes per panel of at most a quarter oscillation (of e^{ikzc} J0(q r) in c; of J0 and the decay
    in s), the error estimated by doubling the panels. ``deriv`` = "z" or "r": the derivative dU/dz or dU/dr of the
    same integral (the integrand times i k_z, or J0(q r) replaced by -q J1(q r))."""
    from scipy.special import j0, j1
    if z < 0:
        raise ValueError("gaussian_field: z >= 0")
    if deriv not in (None, "z", "r"):
        raise ValueError("gaussian_field: deriv None, 'z' or 'r'")
    # evanescent part: exp(-s^2 w^2/4 - z s) below 1e-18 beyond s_max
    s_max = 2.0 * (-z + math.sqrt(z * z + 41.5 * w * w)) / (w * w)

    def panels(a, b, npan, f):
        e = np.linspace(a, b, npan + 1)
        lo, hi = e[:-1, None], e[1:, None]
        t = 0.5 * (hi - lo) * _GL_X[None, :] + 0.5 * (hi + lo)
        return complex(np.sum(0.5 * (hi - lo) * _GL_W[None, :] * f(t)))

    def radial(q):
        if deriv == "r":
            return -q * j1(q * r)
        return j0(q * r) if r else 1.0

    def prop(c):
        q = k * np.sqrt(np.clip(1 - c * c, 0.0, None))
        f = c * np.exp(-q * q * w * w / 4) * np.exp(1j * k * z * c) * radial(q)
        return f * (1j * k * c) if deriv == "z" else f

    def evan(s):
        q = np.sqrt(k * k + s * s)
        f = s * np.exp(-q * q * w * w / 4 - z * s) * radial(q)
        return f * (-s) if deriv == "z" else f

    n_prop = int(math.ceil(4 * k * (z + r) / (2 * math.pi))) + 8
    n_evan = int(math.ceil(4 * s_max * (r + w) / (2 * math.pi))) + 8

    def total(f):
        return w * w / 2 * (k * k * panels(0.0, 1.0, f * n_prop, prop) + panels(0.0, s_max, f * n_evan, evan))
    v1, v2 = total(1), total(2)
    return v2, abs(v2 - v1) + 1e-15 * abs(v2)


def gaussian_on_axis(k: float, w: float, z: float) -> tuple[complex, float]:
    """(U(0, 0, z), error estimate) for the field exp(-r^2/w^2) given on z = 0."""
    return gaussian_field(k, w, z, 0.0)


# --- spectra of the sources (closed forms) ---------------------------------------------------------------------------
def _xp(*arrays):
    """The array module of the arguments: NumPy, or CuPy when the engine evaluates a spectrum on GPU 0."""
    for a in arrays:
        if type(a).__module__.split(".")[0] == "cupy":
            import cupy
            return cupy
    return np


def _ft_interval(q, a, b):
    """int_a^b e^{-i q x} dx, elementwise (b - a at q = 0); NumPy or CuPy arrays."""
    xp = _xp(q)
    q = xp.asarray(q, dtype=float)
    small = xp.abs(q) * max(abs(a), abs(b), b - a) < 1e-8
    qs = xp.where(small, 1.0, q)
    out = (xp.exp(-1j * qs * a) - xp.exp(-1j * qs * b)) / (1j * qs)
    return xp.where(small, (b - a) * xp.exp(-1j * q * 0.5 * (a + b)), out)


def interval_spectrum(intervals):
    """1-D: unit field on the intervals (a, b); returns fn(q)."""
    return lambda q: sum(_ft_interval(q, a, b) for a, b in intervals)


def rect_spectrum(rects):
    """Unit field on disjoint rectangles (xa, xb, ya, yb); returns fn(qx, qy)."""
    return lambda qx, qy: sum(_ft_interval(qx, xa, xb) * _ft_interval(qy, ya, yb) for xa, xb, ya, yb in rects)


def disc_spectrum(a: float):
    """Unit field on the disc of radius a centred on the axis; returns fn(qx, qy) = 2 pi a^2 J1(q a) / (q a)."""
    def fn(qx, qy):
        xp = _xp(qx, qy)
        if xp is np:
            from scipy.special import j1
        else:
            from cupyx.scipy.special import j1
        qa = xp.hypot(qx, qy) * a
        safe = xp.where(qa > 1e-8, qa, 1.0)
        return xp.where(qa > 1e-8, 2 * math.pi * a * a * j1(safe) / safe, math.pi * a * a).astype(complex)
    return fn


def gaussian_spectrum(w: float, ndim: int = 2):
    """exp(-r^2/w^2) on z = 0; returns fn(q...) = (sqrt(pi) w)^d e^{-q^2 w^2 / 4} (separable: a product over axes)."""
    c = math.sqrt(math.pi) * w

    def fn(*q):
        xp = _xp(*q)
        out = 1.0
        for qi in q:
            out = out * (c * xp.exp(-xp.asarray(qi) ** 2 * w * w / 4))
        return xp.asarray(out, dtype=complex)
    return fn


def rotated(fn, angle: float):
    """The source turned by ``angle`` (rad, counter-clockwise) about the axis: U0'(r) = U0(R_{-angle} r), whose
    spectrum is A(R_{-angle} q). With angle = -phi, the plane y = 0 of the turned source is the plane through the axis
    at azimuth phi of the original."""
    c, s = math.cos(angle), math.sin(angle)
    return lambda qx, qy: fn(c * qx + s * qy, -s * qx + c * qy)
