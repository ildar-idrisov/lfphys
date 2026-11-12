# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Slit diffraction: the exact 2-D Rayleigh-Sommerfeld propagation (first kind) of Kirchhoff boundary values
(the incident field inside the slits); used as the independent check of the paraxial engine. For an aperture
field U0(x') in the plane z = 0 the field at (x, z) is

    U(x, z) = (i k z / 2) int U0(x') H1^(1)(k R) / R dx',   R = sqrt((x - x')^2 + z^2),

the exact solution of the 2-D Helmholtz equation for the given aperture values (2-D Green's function
(i/4) H0^(1)). Incident wave: H0^(1)(k r_s) from a line source at (x_s, -L1), or a plane wave. Hankel functions
of large argument use their asymptotic expansion (three terms; relative error < 1e-10 for kR > 1e4).
Quadrature: composite 32-node Gauss-Legendre per slit, at most PHASE_PER_PANEL radians of phase per panel
(a 32-node panel integrates exp(i phi) to 1e-15 up to about 56 rad, 3e-11 at 72 rad: measured, review
response); no cap on the panel count, so the reference stays exact for wide slits in the near field.

What it checks: the paraxial (Fresnel) approximation of fresnel.py for the run's geometry. It does not lift the
Kirchhoff boundary condition (the field inside a slit = the incident field), which fails for slits of a few
wavelengths; the run warns about that separately.

**The plane wave on slits, against the vector solution** (moved here from ``lfphys.core.em.slit``, review B8 C10: the
core keeps the exact law, the approximation lives here). For the plane wave exp(i k (x sin theta + z cos theta)) the
Kirchhoff boundary values u = exp(i q0 x) in the slits, 0 on the screen, have the angular spectrum
T_K(q) = (1/2 pi) sum_i int_slit_i exp(i (q0 - q) x) dx (``plane_wave_spectrum``), the far field
f_K(phi) = sqrt(2 pi k) cos(phi) T_K(k sin phi) exp(-i pi/4) (u ~ f exp(i k r)/sqrt(r); ``plane_wave_far_field``), the
transmission per slit width P_K / (cos theta sum w) (``plane_wave_transmission``) and the field anywhere above the slits by
the exact Rayleigh–Sommerfeld integral with the quadrature of the core's ``SlitSolution`` fields
(``plane_wave_field``). ``compare_vector`` puts the vector solution of ``lfphys.core.em.slit`` and this result side by
side on a screen; ``transmission_vs_width`` gives T of one slit against its width for TE, TM and Kirchhoff.
"""

from __future__ import annotations

import cmath
import math

import numpy as np
from scipy import special

from lfphys.i18n import T
from ...core.em import slit as _vslit
from ...core.optics.scalar import hankel1

ABOUT = {
    "layer": 'theories', "kind": 'approximation',
    "title": T("Diffraction by slits: exact propagation of Kirchhoff's boundary values"),
    "statement": T("The field on the screen is the exact two-dimensional Rayleigh–Sommerfeld integral (its kernel is "
                   "in core.optics.scalar) of the field in the slits, taken equal to the incident field (Kirchhoff's "
                   "boundary conditions)."),
    "validity": T("slits wider than ~10 λ: in narrow slits the field is not equal to the incident one; the exact "
                  "vector solution for a perfectly conducting screen is lfphys.core.em.slit (the difference from it is "
                  "of order 1/(k·a), several times for slits narrower than λ, and depends on the polarisation)"),
    "basis": [T("Born & Wolf, Principles of Optics, ch. 8.11")],
    "conflicts": [T("lfphys.theories.approx.paraxial: differs at large angles"),
                  T("lfphys.core.em.slit: the vector solution for a conducting screen (both polarisations); "
                    "Kirchhoff's boundary values depart from it for slits narrower than ~10 λ (T and the pattern) and "
                    "know nothing of polarisation")],
}


PHASE_PER_PANEL = 32.0
_GL32 = np.polynomial.legendre.leggauss(32)


def _panels(x, z, k, c, a, L1, src, kappa):
    """Panel count for slit c: a bound on the phase variation across the slit. |d(kR)/dx'| = k|x - x'|/R grows with
    |x - x'|, so its maximum is at the farthest pair (screen point, slit edge); plus the incident wave's phase
    gradient. Composite Gauss-Legendre with 32-node panels (review R14: an n-point rule costs O(n^3) to build); the
    former cap of 2000 panels left > 56 rad per panel for k a > 1.1e5 near the slits (response check)."""
    xm = float(np.max(np.abs(x - c))) + 0.5 * a
    ph = k * a * xm / math.hypot(xm, z)
    if math.isinf(L1):
        ph += a * abs(k * math.sin(src) + kappa)
    else:
        xs_ = abs(c - src) + 0.5 * a
        ph += k * a * xs_ / math.hypot(xs_, L1) + abs(kappa) * a
    return int(math.ceil(ph / PHASE_PER_PANEL)) + 1


def cost(x, z, k, slits, a, L1=math.inf, src=0.0, kappa=0.0):
    """Number of kernel evaluations slit_fields would need (to decide whether the exact check is affordable)."""
    x = np.asarray(x, float)
    return sum(32 * _panels(x, z, k, c, a, L1, src, kappa) for c in np.asarray(slits, float)) * x.size


def slit_fields(x, z, k, slits, a, L1=math.inf, src=0.0, kappa=0.0):
    """Per-slit exact fields U_j(x, z) (n, Nx) for unit incident amplitude (common constants included)."""
    x = np.asarray(x, float)
    out = []
    for c in np.asarray(slits, float):
        e1, e2 = c - 0.5 * a, c + 0.5 * a
        panels = _panels(x, z, k, c, a, L1, src, kappa)
        t32, w32 = _GL32
        edges = np.linspace(e1, e2, panels + 1)
        h = 0.5 * (edges[1:] - edges[:-1])
        mid = 0.5 * (edges[1:] + edges[:-1])
        xp = (mid[:, None] + h[:, None] * t32[None, :]).ravel()
        wp = (h[:, None] * w32[None, :]).ravel()
        n = len(xp)
        if math.isinf(L1):
            U0 = np.exp(1j * (k * math.sin(src) + kappa) * xp)
        else:
            rs = np.hypot(xp - src, L1)
            U0 = hankel1(0, k * rs) * np.exp(1j * kappa * xp)
        acc = np.zeros(x.shape, complex)
        # chunk over screen points and nodes to bound memory (about 4e6 kernel values at a time)
        nc = min(n, 4_000_000)
        step = max(1, int(4e6 // nc))
        Uw = U0 * wp
        for i in range(0, len(x), step):
            xs = x[i:i + step]
            for j0 in range(0, n, nc):
                R = np.hypot(xs[:, None] - xp[None, j0:j0 + nc], z)
                K = (0.5j * k * z) * hankel1(1, k * R) / R  # sign: review R18 (a wide aperture gives U -> e^{ikz})
                acc[i:i + step] += K @ Uw[j0:j0 + nc]
        out.append(acc)
    return np.stack(out)


def paraxial_deviation(x, z, k, slits, a, L1, G, A_fresnel, src=0.0, kappa=0.0):
    """Max |P_RS - P_F| / max P_F with both distributions normalised to unit sum on the same points."""
    U = slit_fields(x, z, k, slits, a, L1, src, kappa)
    return deviation(U, A_fresnel, G)


def deviation(U, A_fresnel, G):
    """The same comparison for per-slit fields already computed (exact U, paraxial A) and the marks' Gram G."""
    P_rs = np.einsum("jx,lx,jl->x", U, U.conj(), G).real
    P_f = np.einsum("jx,lx,jl->x", A_fresnel, A_fresnel.conj(), G).real
    P_rs = P_rs / P_rs.sum()
    P_f = P_f / P_f.sum()
    return float(np.max(np.abs(P_rs - P_f)) / np.max(P_f)), P_rs


# --- the plane wave on slits, against the vector solution (moved from lfphys.core.em.slit; review B8 C10) -----------
def plane_wave_spectrum(k, centers, widths, q, theta=0.0):
    """T_K(q) = (1/2 pi) sum_i int_slit_i exp(i q0 x) exp(-i q x) dx: Kirchhoff's boundary values (the incident wave in
    the slits, zero on the screen) in the plane of the screen; the transmitted field is u = int T_K(q) exp(i (q x +
    k_z z)) dq."""
    q = np.atleast_1d(np.asarray(q, float))
    q0 = k * math.sin(theta)
    acc = np.zeros(q.shape, complex)
    for c, w in zip(np.atleast_1d(centers), np.broadcast_to(np.atleast_1d(widths), np.shape(np.atleast_1d(centers)))):
        l = c - w / 2
        acc += np.exp(1j * (q0 - q) * l) * _vslit._intexp(q0 - q, w)
    return acc / (2 * math.pi)


def plane_wave_far_field(k, centers, widths, phi, theta=0.0):
    """f_K(phi) of the Kirchhoff boundary values propagated exactly (Rayleigh–Sommerfeld, first kind), u ~ f exp(i k r) /
    sqrt(r); dP/dphi = |f|^2 in the flux units of ``lfphys.core.em.slit``."""
    phi = np.atleast_1d(np.asarray(phi, float))
    return math.sqrt(2 * math.pi * k) * np.cos(phi) * plane_wave_spectrum(k, centers, widths, k * np.sin(phi), theta) \
        * cmath.exp(-0.25j * math.pi)


def plane_wave_transmission(k, centers, widths, theta=0.0) -> float:
    """Transmitted power of the Kirchhoff boundary values (exact propagation) per slit width and cos theta (1 for a wide
    slit)."""
    centers = np.atleast_1d(np.asarray(centers, float))
    widths = np.broadcast_to(np.atleast_1d(np.asarray(widths, float)), centers.shape)
    span = float(np.max(centers + widths / 2) - np.min(centers - widths / 2))
    ph, w = _vslit._gl(np.array([-0.5 * math.pi, 0.5 * math.pi]), k * span + 2)
    P = float(np.sum(w * np.abs(plane_wave_far_field(k, centers, widths, ph, theta)) ** 2))
    return P / (math.cos(theta) * float(np.sum(widths)))


def plane_wave_field(k, centers, widths, x, z, theta=0.0, deriv: bool = False):
    """u_K(x, z), z > 0 from the plane of the slits: the exact Rayleigh–Sommerfeld integral (first kind) of the incident
    wave inside the slits (Kirchhoff's boundary values), with the quadrature of the core's ``SlitSolution`` fields;
    deriv=True returns (u, du/dx, du/dz) (the kernel's exact derivatives)."""
    x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
    centers = np.atleast_1d(np.asarray(centers, float))
    widths = np.broadcast_to(np.atleast_1d(np.asarray(widths, float)), centers.shape)
    xr, zr = x.ravel(), z.ravel()
    out = np.zeros(xr.shape, complex)
    ox = np.zeros(xr.shape, complex)
    oz = np.zeros(xr.shape, complex)
    q0 = k * math.sin(theta)
    for c, w in zip(centers, widths):
        s = _vslit._Slit(float(c), float(w))
        om = k * s.b + 4
        far = zr >= 2 * s.w
        groups = []
        if np.any(far):
            groups.append((np.nonzero(far)[0],) + _vslit._gl(np.array([0.0, math.pi]), om + k * s.b))
        for i in np.nonzero(~far)[0]:
            groups.append((np.array([i]),) + _vslit._gl(_vslit._theta_breaks(s.c, s.b, float(xr[i]), float(zr[i])), om))
        for idx, th, wq in groups:
            Xs = s.c + s.b * np.cos(th)
            D = np.exp(1j * q0 * Xs) * s.b * np.sin(th) * wq
            for i0 in range(0, len(idx), 2048):
                ii = idx[i0:i0 + 2048]
                xi = xr[ii, None] - Xs[None, :]
                zt = zr[ii, None]
                R = np.hypot(xi, zt)
                H1 = _vslit._h1(k * R)
                h = H1 / R
                out[ii] += np.sum(0.5j * k * zt * h * D, axis=1)
                if deriv:
                    hp = k * _vslit._h0(k * R) / R - 2 * H1 / (R * R)
                    ox[ii] += np.sum(0.5j * k * zt * hp * xi / R * D, axis=1)
                    oz[ii] += np.sum(0.5j * k * (h + zt * zt * hp / R) * D, axis=1)
    if deriv:
        return out.reshape(x.shape), ox.reshape(x.shape), oz.reshape(x.shape)
    return out.reshape(x.shape)


def compare_vector(k, centers, widths, thickness, pol, x, z, theta=0.0, modes=None, solution=None) -> dict:
    """The vector solution (``lfphys.core.em.slit``) and the scalar Kirchhoff result side by side on a screen at distance
    z (> 0) behind the exit face of the slits (the Kirchhoff aperture taken in the exit plane), at the points x:

    * ``I_vector`` |E|^2 of the vector solution, ``I_scalar`` |u_K|^2 (unit incident |E|), their difference;
    * ``j_vector``, ``j_scalar``: the normalised energy flux through the screen plane (incident: cos theta);
    * ``T_vector``, ``T_scalar``: transmission per slit width; ``balance``: the vector solution's power balance.
    """
    sol = solution or _vslit.solve(k, centers, widths, thickness, pol, theta, modes)
    x = np.asarray(x, float)
    zz = np.full(x.shape, float(z))
    u, ux, uz = sol.field(x, sol.thickness + zz)
    Iv = np.abs(u) ** 2 if sol.pol == "TE" else (np.abs(ux) ** 2 + np.abs(uz) ** 2) / k ** 2
    jv = np.imag(np.conj(u) * uz) / k
    uk, _, ukz = plane_wave_field(k, centers, widths, x, zz, theta, deriv=True)
    jk = np.imag(np.conj(uk) * ukz) / k
    Is = np.abs(uk) ** 2
    return {"I_vector": Iv, "I_scalar": Is, "difference": Iv - Is, "j_vector": jv, "j_scalar": jk,
            "T_vector": sol.transmission(), "T_scalar": plane_wave_transmission(k, centers, widths, theta),
            "balance": sol.power_balance(), "solution": sol}


def transmission_vs_width(k, widths, thickness=0.0, theta=0.0, modes=None) -> dict:
    """T (per slit width) of one slit against its width for TE, TM (``lfphys.core.em.slit``) and the scalar Kirchhoff
    result: {'w_over_lambda', 'TE', 'TM', 'kirchhoff'}."""
    widths = np.atleast_1d(np.asarray(widths, float))
    out = {"w_over_lambda": widths * k / (2 * math.pi), "TE": [], "TM": [], "kirchhoff": []}
    for w in widths:
        for p in ("TE", "TM"):
            out[p].append(_vslit.solve(k, [0.0], [w], thickness, p, theta, modes).transmission())
        out["kirchhoff"].append(plane_wave_transmission(k, [0.0], [w], theta))
    return {kk: np.asarray(v) for kk, v in out.items()}
