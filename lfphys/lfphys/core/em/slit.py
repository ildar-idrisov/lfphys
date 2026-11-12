# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Vector diffraction of a plane wave by slits in a perfectly conducting screen (2-D: the screen and the slits infinite
along y), both polarisations, any angle of incidence; Sommerfeld's exact half-plane as the edge reference (plan P1,
batch B8; closes STATUS V4 of v02).

**Geometry and conventions.** The screen fills 0 <= z <= t (t = 0: a screen of zero thickness), slit i is the gap
|x - c_i| < w_i / 2; the plane wave comes from z < 0 at the angle theta from the normal (towards +x),
u_inc = exp(i k (x sin theta + z cos theta)), time factor exp(-i omega t). Two independent polarisations:

* **TE (s)**, E along the slits: u = E_y; Dirichlet condition u = 0 on the conductor; H_x = (i/(k Z0)) du/dz,
  H_z = -(i/(k Z0)) du/dx;
* **TM (p)**, H along the slits: u = Z0 H_y; Neumann condition du/dn = 0 on the conductor; E_x = -(i/k) du/dz,
  E_z = (i/k) du/dx.

Both have unit incident |E|; the energy flux is S = Im(u* grad u) / (2 k Z0) in either case, so the module works with
the normalised flux j = Im(u* grad u) / k (the incident wave has j_z = cos theta per unit length of x).

**The modal method** (t > 0; the waveguide-mode matching of Harrington & Auckland, RADC-TR-79-257 (1979), and of
Takakura, PRL 86, 5601 (2001), here with any number of modes and slits). Inside slit i the field is a sum of the
parallel-plate modes, sin(m pi (x - l_i)/w_i) (TE, m >= 1) or cos(m pi (x - l_i)/w_i) (TM, m >= 0), each as
A_m exp(i beta_m z) + B_m exp(i beta_m (t - z)), beta_m = sqrt(k^2 - (m pi / w_i)^2) (Im >= 0). Above and below, the
field is the incident wave, its specular reflection by the whole plane (-1 for TE, +1 for TM) and the field radiated
by the apertures, written with the half-space Green's function; matching the continuous component on the apertures
in Galerkin form gives, with the operator of a half-space between apertures

    TE:  Y_nm = 1/2 int int [k^2 phi_n(x) phi_m(x') - phi_n'(x) phi_m'(x')] H0(k |x - x'|) dx dx',
    TM:  Z_nm = 1/2 int int psi_n(x) psi_m(x') H0(k |x - x'|) dx dx'

(the TE form after two integrations by parts of (k^2 + d^2/dx^2) H0/2, possible because phi vanishes at the slit
walls), the norms N_m = int phi_m^2 and E = diag(exp(i beta t)), the decoupled systems for A +- B:

    TE:  [(Y + N beta) +- (Y - N beta) E] (A +- B) = 2 k_z0 int phi exp(i q0 x) dx,
    TM:  [(N + Z beta) +- (N - Z beta) E] (A +- B) = 2 int psi exp(i q0 x) dx.

**Zero thickness (t = 0)**: the same equations hold with E = 1, but the waveguide modes cannot represent the edge
singularity of a thin screen (TM: E_x ~ r^(-1/2)); the default for t = 0 is therefore the edge-conditioned
Chebyshev basis (the classical Galerkin method for the thin slit, e.g. Butler & Umashankar 1976): on x = c + b cos(th),
TE: u = sum c_n sin((n+1) th) (= sqrt(1 - s^2) U_n(s)), TM: du/dz = sum d_n cos(n th)/sin(th) (= T_n(s)/sqrt(1 - s^2)),
with the same operators Y, Z; it converges exponentially for narrow slits. The double integrals are done in th: the
outer by composite Gauss–Legendre, the inner graded geometrically towards the (log-)singular point x' = x.

**Outputs.** ``SlitSolution``: the field u and its gradient anywhere (below, inside the slits, in the conductor (0)
and above: the apertures' fields propagated by the exact Rayleigh–Sommerfeld integrals, Dirichlet kernel
(i k zeta/2) H1(k R)/R for TE, Neumann kernel -/+ (i/2) H0(k R) for TM), the physical components, the angular spectra
T(q) (transmitted) and R(q) (scattered back, without the specular wave), the far-field patterns f(phi) with
u ~ f exp(i k r)/sqrt(r), the transmitted and back-scattered powers, the transmission per slit width
T = P_t / (cos theta sum w_i), and the power balance by the screen's optical theorem
P_t + P_b = -4 pi r_s cos(theta) Re R(k sin theta) (r_s = -1 TE, +1 TM; derived from the flux through z = 0; for the
modal method also the power carried by the modes through the slit), and the estimated truncation error in the number
of modes (``error_estimate``, from sub-blocks of the same operator). The scalar Kirchhoff result (the incident wave in
the slits, zero on the screen), its comparison with this solution and T against the width live outside the core, in
``lfphys.theories.approx.kirchhoff`` (review B8 C10: an approximation of the law this module has in full).

**Sommerfeld's half-plane** (Math. Ann. 47, 317 (1896), §8, case (a) Z = 0 / case (b) dZ/dn = 0, time factor turned to
exp(-i omega t)): the conductor z = 0, x < 0; with polar angle phi in (0, 2 pi) measured from the screen and
phi0 = pi/2 - theta the direction the wave comes from, u = U(phi - phi0) -+ U(phi + phi0) (- TE, + TM),
U(rho, psi) = exp(-i k rho cos psi) F(-sqrt(2 k rho) cos(psi / 2)), F(a) = erfc(exp(-i pi/4) a) / 2. Its far edge wave
(Sommerfeld pp. 368–369, Keller's coefficient) is ``half_plane_edge_wave``.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field

import numpy as np
from scipy import constants as sc
from scipy import special

from ..optics.scalar import hankel1 as _hankel1_real

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Векторная дифракция на щелях в идеально проводящем экране",
    "statement": "Плоская волна под любым углом на одну или несколько щелей в идеально проводящем экране конечной "
                 "(или нулевой) толщины, обе поляризации (E вдоль щелей — TE/s, H вдоль щелей — TM/p): модовый метод "
                 "(волноводные моды в щелях, сшитые с полями полупространств), для тонкого экрана — базис с "
                 "краевыми условиями; поле в любой точке, угловой спектр, диаграмма в дальней зоне, пропускание на "
                 "ширину щели, баланс мощности (оптическая теорема экрана), оценка ошибки усечения по числу мод. "
                 "Точное решение Зоммерфельда для полуплоскости.",
    "validity": "2-D (щели бесконечно длинные), идеальный проводник (без потерь и плазмонов реальных металлов), вакуум; "
                "численная ошибка — от числа мод: базис с краевыми условиями (тонкий экран, k·w ≤ 140) сходится "
                "экспоненциально; волноводные моды — алгебраически (углы экрана, порядок 1.2–1.4), по умолчанию T "
                "занижено на 0.04–0.2 % при толщине > 0; у тонкого экрана при k·w > 140 — волноводные моды, "
                "0.2–0.5 % (измерено при k·w = 40–130); ошибка оценивается (error_estimate) и измеряется "
                "(convergence)",
    "basis": ["Harrington & Auckland, RADC-TR-79-257 (1979); IEEE TAP 28, 616 (1980)",
              "Takakura, PRL 86, 5601 (2001) (по вторичным источникам)",
              "Rayleigh, Phil. Mag. 43, 259 (1897) — пределы узкой щели",
              "Sommerfeld, Math. Ann. 47, 317 (1896) — полуплоскость"],
    "conflicts": ["lfphys.theories.approx.kirchhoff: скалярные граничные условия Кирхгофа; расходятся у щелей уже "
                  "~10 λ и по поляризации"],
}

Z0 = sc.mu_0 * sc.c
EULER_GAMMA = 0.5772156649015329
_GL_X, _GL_W = np.polynomial.legendre.leggauss(16)
_SIGMA = 0.25  # geometric grading ratio towards a (near-)singular point
_PHASE = 6.0  # radians of the fastest oscillation per 16-node panel (16-node rule: error < 1e-17 for exp(i theta))


def _pol(pol: str) -> str:
    p = str(pol).upper()
    if p in ("TE", "S", "E"):
        return "TE"
    if p in ("TM", "P", "H"):
        return "TM"
    raise ValueError("pol: 'TE' (E along the slits, s) or 'TM' (H along the slits, p)")


def _kz(k, q):
    """sqrt(k^2 - q^2) with Im >= 0 (evanescent waves decay)."""
    q = np.asarray(q, float)
    return np.sqrt(k * k - q * q + 0j)


def _h0(x):
    """H0^(1)(x) for x >= 0 (real arrays); large arguments by the asymptotic series of core.optics.scalar."""
    x = np.asarray(x, float)
    out = np.empty(x.shape, complex)
    small = x < 1e4
    out[small] = special.hankel1(0, x[small])
    if np.any(~small):
        out[~small] = _hankel1_real(0, x[~small])
    return out


def _h1(x):
    x = np.asarray(x, float)
    out = np.empty(x.shape, complex)
    small = x < 1e4
    out[small] = special.hankel1(1, x[small])
    if np.any(~small):
        out[~small] = _hankel1_real(1, x[~small])
    return out


def _intexp(p, w):
    """int_0^w exp(i p u) du (elementwise, stable for small p)."""
    p = np.asarray(p, dtype=complex)
    return w * np.exp(0.5j * p * w) * np.sinc(p * w / (2 * math.pi))


def _panels(a, b, omega):
    """Breakpoints dividing [a, b] so that each panel holds at most _PHASE radians of a frequency omega."""
    n = max(1, int(math.ceil(abs(b - a) * omega / _PHASE)))
    return np.linspace(a, b, n + 1)


def _gl(breaks, omega):
    """Composite 16-node Gauss–Legendre nodes and weights on the panels between the breakpoints (each panel further
    divided for the frequency omega)."""
    xs, ws = [], []
    for a, b in zip(breaks[:-1], breaks[1:]):
        if b - a <= 0:
            continue
        e = _panels(a, b, omega)
        lo, hi = e[:-1, None], e[1:, None]
        xs.append((0.5 * (hi - lo) * _GL_X + 0.5 * (hi + lo)).ravel())
        ws.append((0.5 * (hi - lo) * _GL_W + 0 * lo).ravel())
    return np.concatenate(xs), np.concatenate(ws)


def _theta_breaks(c, b, x0, s0):
    """Breakpoints in th in [0, pi] (x = c + b cos th) for integrating against a kernel singular or peaked at the point
    x0 with length scale s0 (the distance zeta of a field point from the plane; 0 for the log kernel on the plane):
    a geometric ladder in x around x0 (inside the slit) or from the slit edge nearest to x0, mapped to th."""
    lo, hi = c - b, c + b
    xs = [lo, hi]
    if lo < x0 < hi:
        xs.append(x0)
        if s0 > 0:
            d = s0
            while d < 2 * b:
                xs.extend([x0 - d, x0 + d])
                d *= 2.0
        else:
            d = 2 * b
            while d > 1e-13 * b:
                xs.extend([x0 - d, x0 + d])
                d *= _SIGMA
    else:
        dist = lo - x0 if x0 <= lo else x0 - hi
        d = math.hypot(dist, s0)
        if d < 2 * b:
            d0 = d
            while d0 < 2 * b + d:
                xs.extend([x0 - d0, x0 + d0])
                d0 *= 2.0
    xs = np.unique(np.clip(np.asarray(xs, float), lo, hi))
    th = np.sort(np.arccos(np.clip((xs - c) / b, -1.0, 1.0)))
    return np.unique(np.concatenate([[0.0], th, [math.pi]]))


@dataclass
class _Slit:
    c: float
    w: float

    @property
    def b(self):
        return 0.5 * self.w

    @property
    def l(self):
        return self.c - 0.5 * self.w


class _Basis:
    """Basis functions on one slit as densities in th (x = c + b cos th, dx = b sin th dth): values D_n(th) such that
    int f(x) basis_n(x) dx = int_0^pi D_n(th) f(x(th)) dth, and for TE the densities of the x-derivatives."""

    def __init__(self, kind: str, pol: str, slit: _Slit, M: int):
        self.kind, self.pol, self.s, self.M = kind, pol, slit, M
        if kind == "modal":
            self.m = np.arange(1, M + 1) if pol == "TE" else np.arange(0, M)
            self.alpha = self.m * math.pi / slit.w
        else:
            self.m = np.arange(M)

    def omega_theta(self, k):
        """Largest frequency in th of a basis density times the kernel's phase (for panel sizes)."""
        b = self.s.b
        if self.kind == "modal":
            return float(self.m[-1]) * math.pi / 2 + k * b + 2
        return float(self.M + 1) + k * b + 2

    def dens(self, th):
        """(M, len(th)) densities of the functions."""
        b = self.s.b
        th = np.asarray(th, float)
        st, ct = np.sin(th), np.cos(th)
        if self.kind == "modal":
            ph = np.outer(self.m * math.pi, (1 + ct) / 2)
            f = np.sin(ph) if self.pol == "TE" else np.cos(ph)
            return f * (b * st)[None, :]
        if self.pol == "TE":
            return np.sin(np.outer(self.m + 1, th)) * (b * st)[None, :]
        return b * np.cos(np.outer(self.m, th))

    def ddens(self, th):
        """(M, len(th)) densities of the x-derivatives (TE only): phi_n'(x) dx/dth."""
        b = self.s.b
        th = np.asarray(th, float)
        if self.kind == "modal":
            ph = np.outer(self.m * math.pi, (1 + np.cos(th)) / 2)
            return (self.alpha[:, None] * np.cos(ph)) * (b * np.sin(th))[None, :]
        return -(self.m + 1)[:, None] * np.cos(np.outer(self.m + 1, th))

    def ft(self, q):
        """(M, len(q)): int basis_n(x) exp(-i q x) dx (closed forms)."""
        q = np.atleast_1d(np.asarray(q, float))
        s = self.s
        if self.kind == "modal":
            ph = np.exp(-1j * q * s.l)[None, :]
            a = self.alpha[:, None]
            Ip, Im = _intexp(a - q[None, :], s.w), _intexp(-a - q[None, :], s.w)
            if self.pol == "TE":
                return ph * (Ip - Im) / 2j
            return ph * (Ip + Im) / 2
        b = s.b
        z = q * b
        ph = np.exp(-1j * q * s.c)[None, :]
        n = self.m[:, None]
        if self.pol == "TE":
            with np.errstate(invalid="ignore", divide="ignore"):
                r = np.where(np.abs(z) > 1e-8, special.jv(n + 1, z[None, :]) / np.where(z == 0, 1, z)[None, :],
                             np.where(n == 0, 0.5, 0.0))
            return ph * b * math.pi * (n + 1) * (-1j) ** n * r
        return ph * b * math.pi * (-1j) ** n * special.jv(n, z[None, :])

    def values_x(self, x):
        """(M, len(x)) basis functions at points x inside the slit (TE: u; TM: du/dz)."""
        s = self.s
        x = np.asarray(x, float)
        if self.kind == "modal":
            ph = np.outer(self.alpha, x - s.l)
            return np.sin(ph) if self.pol == "TE" else np.cos(ph)
        th = np.arccos(np.clip((x - s.c) / s.b, -1, 1))
        if self.pol == "TE":
            return np.sin(np.outer(self.m + 1, th))
        return np.cos(np.outer(self.m, th)) / np.sin(th)[None, :]

    def norms(self):
        s = self.s
        if self.kind != "modal":
            raise ValueError("norms: modal basis only")
        N = np.full(self.M, 0.5 * s.w)
        if self.pol == "TM":
            N[0] = s.w
        return N


def _ladder(a, b, s, toward_a, d0):
    """Breakpoints on [a, b] graded geometrically towards the end a (toward_a) or b where a (near-)singular point lies
    at distance d0 >= 0 outside the interval (0: at the end)."""
    L = b - a
    pts = [a, b]
    if d0 == 0:
        d = L * s
        while d > 1e-13 * L:
            pts.append(a + d if toward_a else b - d)
            d *= s
    else:
        d = d0
        while d < L:
            pts.append(a + d if toward_a else b - d)
            d *= 2.0
    return np.unique(np.clip(pts, a, b))


def _pair_modal(k, pol, bi, bj):
    """Block of the half-space operator between the waveguide modes of slits i and j by the correlation route:
    int int f(x) g(x') K(x - x') dx dx' = int K(xi) Gamma(xi) dxi with the closed-form correlation Gamma of two
    trigonometric functions over the overlap of the slits shifted by xi; K = H0(k |xi|) (log-singular at xi = 0),
    composite Gauss–Legendre graded towards the singular point and split where Gamma has kinks."""
    si, sj = bi.s, bj.s
    wi, wj = si.w, sj.w
    dl = si.l - sj.l
    sing = -dl  # eta of xi = 0
    br = sorted({-wj, 0.0, wi - wj, wi} | ({sing} if -wj < sing < wi else set()))
    br = [v for v in br if -wj <= v <= wi]
    a_, b_ = bi.alpha, bj.alpha
    om = float(a_[-1] + b_[-1]) + k + 1.0
    nodes, weights = [], []
    for a, b in zip(br[:-1], br[1:]):
        if b - a <= 1e-15 * (wi + wj):
            continue
        if abs(a - sing) <= 1e-15 * (wi + wj) or abs(b - sing) <= 1e-15 * (wi + wj):
            pts = _ladder(a, b, _SIGMA, abs(a - sing) < abs(b - sing), 0.0)
        else:
            dist = min(abs(a - sing), abs(b - sing))
            pts = _ladder(a, b, _SIGMA, abs(a - sing) < abs(b - sing), dist) if dist < (b - a) else np.array([a, b])
        x, w = _gl(np.asarray(pts), om)
        nodes.append(x)
        weights.append(w)
    eta = np.concatenate(nodes)
    wq = np.concatenate(weights) * _h0(np.maximum(k * np.abs(eta + dl), 1e-300))
    A = a_[:, None, None]
    Bf = b_[None, :, None]
    out = np.zeros((bi.M, bj.M), complex)
    chunk = max(1, int(3e6 // (bi.M * bj.M)))
    for e0 in range(0, len(eta), chunk):
        et = eta[e0:e0 + chunk][None, None, :]
        u1 = np.maximum(0.0, et)
        u2 = np.minimum(wi, wj + et)
        Lh = np.maximum(u2 - u1, 0.0)
        um = 0.5 * (u1 + u2)

        def I(g, d):
            return Lh * np.cos(g * um + d) * np.sinc(g * Lh / (2 * math.pi))

        Im_ = I(A - Bf, Bf * et)
        Ip_ = I(A + Bf, -Bf * et)
        cc = 0.5 * (Im_ + Ip_)
        ww = wq[e0:e0 + chunk]
        if pol == "TE":
            ss = 0.5 * (Im_ - Ip_)
            out += np.tensordot(k * k * ss - (A * Bf) * cc, ww, axes=([2], [0]))
        else:
            out += np.tensordot(cc, ww, axes=([2], [0]))
    return 0.5 * out


def _operator(k, pol, bases, route: str = "auto"):
    """The half-space operator (Y for TE, Z for TM) between all basis functions of all slits: (sum M) square.
    route 'auto': the correlation route for waveguide modes, the direct double quadrature (outer Gauss–Legendre in th,
    inner graded towards x' = x) for the edge basis; 'direct': the direct route for both (an independent check of the
    correlation route). A block depends only on the two slits' widths, mode counts and offset (the kernel depends on
    x - x'), so identical pairs (the diagonal blocks of equal slits, equally spaced pairs) are computed once."""
    cache = {}
    sizes = [bs.M for bs in bases]
    off = np.concatenate([[0], np.cumsum(sizes)])
    Mtot = off[-1]
    out = np.zeros((Mtot, Mtot), complex)
    for i, bi in enumerate(bases):
        si = bi.s
        th_o, w_o = _gl(np.array([0.0, math.pi]), bi.omega_theta(k))
        X_o = si.c + si.b * np.cos(th_o)
        D_o = bi.dens(th_o) * w_o[None, :]
        dD_o = bi.ddens(th_o) * w_o[None, :] if pol == "TE" else None
        for j, bj in enumerate(bases):
            if j < i:
                continue
            sj = bj.s
            om = bj.omega_theta(k)
            acc = np.zeros((bi.M, bj.M), complex)
            accd = np.zeros((bi.M, bj.M), complex) if pol == "TE" else None
            gap = abs(si.c - sj.c) - si.b - sj.b
            key = (bi.kind, route, bi.M, bj.M, round(si.w, 14), round(sj.w, 14), round(si.l - sj.l, 12))
            if key in cache:
                blk = cache[key]
                out[off[i]:off[i + 1], off[j]:off[j + 1]] = blk
                if j != i:
                    out[off[j]:off[j + 1], off[i]:off[i + 1]] = blk.T
                continue
            if bi.kind == "modal" and route == "auto":
                blk = cache[key] = _pair_modal(k, pol, bi, bj)
                out[off[i]:off[i + 1], off[j]:off[j + 1]] = blk
                if j != i:
                    out[off[j]:off[j + 1], off[i]:off[i + 1]] = blk.T
                continue
            if i != j and gap > 0.5 * max(si.w, sj.w):
                # well separated: one tensor rule
                th_i, w_i = _gl(np.array([0.0, math.pi]), om)
                X_i = sj.c + sj.b * np.cos(th_i)
                K = _h0(k * np.abs(X_o[:, None] - X_i[None, :]))
                Dj = bj.dens(th_i) * w_i[None, :]
                acc = D_o @ K @ Dj.T
                if pol == "TE":
                    accd = dD_o @ K @ (bj.ddens(th_i) * w_i[None, :]).T
            else:
                rows = np.zeros((len(th_o), bj.M), complex)
                rowsd = np.zeros((len(th_o), bj.M), complex) if pol == "TE" else None
                for o, x0 in enumerate(X_o):
                    th_i, w_i = _gl(_theta_breaks(sj.c, sj.b, x0, 0.0), om)
                    X_i = sj.c + sj.b * np.cos(th_i)
                    K = _h0(np.maximum(k * np.abs(x0 - X_i), 1e-300)) * w_i
                    rows[o] = bj.dens(th_i) @ K
                    if pol == "TE":
                        rowsd[o] = bj.ddens(th_i) @ K
                acc = D_o @ rows
                if pol == "TE":
                    accd = dD_o @ rowsd
            blk = cache[key] = 0.5 * (k * k * acc - accd) if pol == "TE" else 0.5 * acc
            out[off[i]:off[i + 1], off[j]:off[j + 1]] = blk
            if j != i:
                out[off[j]:off[j + 1], off[i]:off[i + 1]] = blk.T
    return out


@dataclass
class SlitSolution:
    """The solved problem (see the module's docstring); build it with ``solve``."""
    k: float
    pol: str
    theta: float
    thickness: float
    slits: list
    method: str
    modes: list
    bases: list = field(repr=False)
    coef: dict = field(repr=False)
    info: dict = field(default_factory=dict)
    system: tuple = field(default=None, repr=False)  # (operator, excitation): truncated() solves its sub-blocks

    # --- the error of the truncation in the number of modes (review B8 C6) ---
    def truncated(self, modes) -> "SlitSolution":
        """The solution with the first ``modes`` basis functions of each slit (an int or one per slit, at most the
        solved number), from the sub-blocks of the solved operator: no new quadrature, only a smaller linear system (the
        basis functions of fewer modes are the first ones of more, and the operator's rule integrates both)."""
        modes = [int(m) for m in np.broadcast_to(np.atleast_1d(np.asarray(modes, int)), (len(self.slits),))]
        if any(m < 1 or m > M for m, M in zip(modes, self.modes)):
            raise ValueError("truncated: 1 <= modes <= the solved number per slit")
        L, exc = self.system
        off = np.concatenate([[0], np.cumsum(self.modes)])
        idx = np.concatenate([off[i] + np.arange(m) for i, m in enumerate(modes)])
        bases = [_Basis(self.method, self.pol, s, m) for s, m in zip(self.slits, modes)]
        coef, info = _solve_system(self.k, self.pol, self.method, self.thickness, self.theta, bases,
                                   L[np.ix_(idx, idx)], exc[idx])
        return SlitSolution(self.k, self.pol, self.theta, self.thickness, self.slits, self.method, modes, bases, coef,
                            info, (L[np.ix_(idx, idx)], exc[idx]))

    def error_levels(self):
        """The mode counts of the coarser solutions the error estimate uses (per slit): edge basis M - max(4, M/8); waveguide
        modes M / 2 and M / sqrt 2."""
        if self.method == "edge":
            return [[max(2, m - max(4, m // 8)) for m in self.modes], list(self.modes)]
        r = math.sqrt(2.0)
        return [[max(2, int(round(m / (r * r)))) for m in self.modes], [max(3, int(round(m / r))) for m in self.modes],
                list(self.modes)]

    def error_estimate(self, quantity=None, parts=("T", "pattern")) -> dict:
        """Estimated error of this solution's truncation in the number of modes, relative: of T, of the far-field pattern
        |f(phi)| on 181 angles (max over phi / max |f|), and of ``quantity(sol)`` (an array, e.g. the flux on a screen;
        max |change| / max |value|) when given. From the sub-block solutions (``truncated``, ``error_levels``):

        * edge basis (exponential convergence): the change from M - max(4, M/8) modes to M, which exceeds the error at M;
        * waveguide modes (algebraic, X(M) = X_inf + c M^-p): Richardson from M/2, M/sqrt 2, M: the order p observed from
          the two changes, clamped to [0.5, 1] (conservative: the asymptotic orders are 1.2-1.4 with corners; a lower p
          gives a larger estimate), error = |X(M) - X(M/sqrt 2)| / ((M / (M/sqrt 2))^p - 1); a change of sign between
          the levels (not yet asymptotic), and a zero-thickness screen (the edge singularity: order <= 1 and irregular
          at these counts), take p = 0.5. Measured against Richardson limits from 2M, 4M, 8M: 1.4-3.1 times the true
          error of T for six thick geometries, 1.2-1.9 times for the thin screen at k w = 60 and 100.

        Returns {'kind', 'levels', 'T', 'pattern' (those of ``parts`` asked for), 'quantity' (if given), 'order' (of
        T, or of the first quantity estimated), 'T_levels'}."""
        levels = self.error_levels()
        sols = [self.truncated(m) for m in levels[:-1]] + [self]
        ph = np.linspace(-0.5 * math.pi, 0.5 * math.pi, 183)[1:-1]
        # the basis transforms of this solution serve the truncated ones (their first rows): computed once
        Ts = pats = None
        if "T" in parts:
            rule, _ = self._phi_rule()
            F_rule = [bs.ft(self.k * np.sin(rule)) for bs in self.bases]
            norm = math.cos(self.theta) * sum(sl.w for sl in self.slits)
            Ts = [self.power("t", F_rule, s_._side("t")) / norm for s_ in sols]
        if "pattern" in parts:
            F_pat = [bs.ft(self.k * np.sin(ph)) for bs in self.bases]
            pats = [np.abs(self._far(ph, F_pat, "t", s_._side("t"))) for s_ in sols]
        quants = [np.atleast_1d(np.asarray(quantity(s_), float)) for s_ in sols] if quantity is not None else None
        out = {"kind": "exponential" if self.method == "edge" else "richardson", "levels": levels, "T_levels": Ts,
               "order": None}

        def rel(a, b, scale):
            return float(np.max(np.abs(a - b)) / max(float(np.max(np.abs(scale))), 1e-300))
        if self.method == "edge":
            if Ts is not None:
                out["T"] = abs(Ts[1] - Ts[0]) / abs(Ts[1])
            if pats is not None:
                out["pattern"] = rel(pats[1], pats[0], pats[1])
            if quants is not None:
                out["quantity"] = rel(quants[1], quants[0], quants[1])
            return out
        M = [float(sum(m)) for m in levels]

        def richardson(x0, x1, x2, scale):
            d1, d2 = x1 - x0, x2 - x1
            n1, n2 = float(np.max(np.abs(d1))), float(np.max(np.abs(d2)))
            same = float(np.sum(d1 * d2)) > 0
            if n2 == 0:
                return 0.0, None
            p = 0.5
            if same and n1 > n2:
                # solve (M0^-p - M1^-p) / (M1^-p - M2^-p) = n1 / n2 for p by bisection
                def f(q):
                    return (M[0] ** -q - M[1] ** -q) / (M[1] ** -q - M[2] ** -q) - n1 / n2
                lo, hi = 1e-3, 8.0
                if f(lo) < 0 < f(hi):
                    for _ in range(80):
                        mid = 0.5 * (lo + hi)
                        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
                    p = 0.5 * (lo + hi)
            pu = 0.5 if self.thickness == 0 else min(max(p, 0.5), 1.0)
            return n2 / ((M[2] / M[1]) ** pu - 1) / max(float(np.max(np.abs(scale))), 1e-300), p
        if Ts is not None:
            out["T"], out["order"] = richardson(np.array([Ts[0]]), np.array([Ts[1]]), np.array([Ts[2]]),
                                                np.array([Ts[2]]))
        if pats is not None:
            out["pattern"] = richardson(pats[0], pats[1], pats[2], pats[2])[0]
        if quants is not None:
            out["quantity"], pq = richardson(quants[0], quants[1], quants[2], quants[2])
            if out["order"] is None:
                out["order"] = pq
        return out

    # --- incidence ---
    @property
    def q0(self):
        return self.k * math.sin(self.theta)

    @property
    def kz0(self):
        return self.k * math.cos(self.theta)

    @property
    def r_spec(self):
        return -1.0 if self.pol == "TE" else 1.0

    def _split(self, vec):
        off = np.concatenate([[0], np.cumsum(self.modes)])
        return [vec[off[i]:off[i + 1]] for i in range(len(self.modes))]

    # --- angular spectra ---
    def _side(self, side):
        """Aperture data per slit for the side: TE: u (Dirichlet data); TM: du/dz (Neumann data)."""
        key = {"t": "exit", "r": "entrance"}[side]
        return self._split(self.coef[key])

    def spectrum(self, q, side: str = "t"):
        """Angular spectrum of the scattered field: side 't' transmitted, u = int T(q) exp(i (q x + k_z (z - t))) dq
        (z > t); side 'r' back-scattered, u_s = int R(q) exp(i (q x - k_z z)) dq (z < 0; the incident and specular
        waves not included)."""
        q = np.atleast_1d(np.asarray(q, float))
        acc = np.zeros(q.shape, complex)
        for bs, cf in zip(self.bases, self._side(side)):
            acc += cf @ bs.ft(q)
        acc /= 2 * math.pi
        if self.pol == "TM":
            kz = _kz(self.k, q)
            acc = acc / (1j * kz) if side == "t" else acc * 1j / kz
        return acc

    def far_field(self, phi, side: str = "t"):
        """f(phi) with u_s ~ f exp(i k r)/sqrt(r) far from the screen; phi from the normal (z for 't', -z for 'r'),
        positive towards +x; dP/dphi = |f|^2 (normalised flux units)."""
        phi = np.atleast_1d(np.asarray(phi, float))
        q = self.k * np.sin(phi)
        return self._far(phi, [bs.ft(q) for bs in self.bases], side)

    def _far(self, phi, F, side, coefs=None):
        """The far field from the basis transforms F (per slit, at q = k sin phi; their first rows serve a truncated
        solution's coefficients ``coefs``): TM cos(phi) T (the 1/k_z cancels exactly), TE cos(phi) T."""
        cfs = self._side(side) if coefs is None else coefs
        acc = np.zeros(np.shape(phi), complex)
        for cf, Fi in zip(cfs, F):
            acc += cf @ Fi[:len(cf)]
        acc /= 2 * math.pi
        if self.pol == "TM":
            cT = acc / (1j * self.k) if side == "t" else acc * 1j / self.k
        else:
            cT = np.cos(phi) * acc
        return math.sqrt(2 * math.pi * self.k) * cT * cmath.exp(-0.25j * math.pi)

    def _phi_rule(self):
        span = max(s.c + s.b for s in self.slits) - min(s.c - s.b for s in self.slits)
        om = self.k * span + 2 + max(self.modes)
        return _gl(np.array([-0.5 * math.pi, 0.5 * math.pi]), om)

    def power(self, side: str = "t", _F=None, _coefs=None) -> float:
        """Transmitted ('t') or back-scattered ('r') power per unit length in y, normalised flux units (the incident
        wave carries cos(theta) per unit length of x)."""
        ph, w = self._phi_rule()
        F = _F if _F is not None else [bs.ft(self.k * np.sin(ph)) for bs in self.bases]
        return float(np.sum(w * np.abs(self._far(ph, F, side, _coefs)) ** 2))

    def transmission(self) -> float:
        """Transmission per slit width: P_t / (cos theta sum w_i) (1 for a wide slit in geometric optics)."""
        return self.power("t") / (math.cos(self.theta) * sum(s.w for s in self.slits))

    def power_balance(self) -> dict:
        """P_t, P_b, the extinction of the specular wave -4 pi r_s cos(theta) Re R(q0) (optical theorem of the screen),
        their relative mismatch, and (modal method) the power carried by the modes through the exit."""
        ph, _ = self._phi_rule()
        F = [bs.ft(self.k * np.sin(ph)) for bs in self.bases]  # one set of transforms for both sides
        Pt, Pb = self.power("t", F), self.power("r", F)
        R0 = complex(self.spectrum(np.array([self.q0]), "r")[0])
        ext = -4 * math.pi * self.r_spec * math.cos(self.theta) * R0.real
        out = {"P_t": Pt, "P_b": Pb, "extinction": ext, "rel": (Pt + Pb - ext) / max(abs(ext), 1e-300),
               "T": Pt / (math.cos(self.theta) * sum(s.w for s in self.slits))}
        if self.method == "modal":
            out["P_modes"] = self.info["P_modes"]
            out["rel_modes"] = (Pt - self.info["P_modes"]) / max(abs(Pt), 1e-300)
        return out

    # --- fields ---
    def _aperture_sum(self, x, zeta, side, deriv=False):
        """Field radiated by the apertures of one side at points (x, zeta) (zeta = distance from the face, > 0),
        with d/dx and d/dzeta: Dirichlet kernel (TE) or Neumann kernel (TM, without the -/+ i/2)."""
        k = self.k
        x = np.asarray(x, float)
        zeta = np.asarray(zeta, float)
        u = np.zeros(x.shape, complex)
        ux = np.zeros(x.shape, complex)
        uz = np.zeros(x.shape, complex)
        for bs, cf in zip(self.bases, self._side(side)):
            s = bs.s
            om = bs.omega_theta(k)
            far = zeta >= 2 * s.w
            groups = []
            if np.any(far):
                th, w = _gl(np.array([0.0, math.pi]), om + k * s.b)
                groups.append((np.nonzero(far)[0], th, w))
            for i in np.nonzero(~far)[0]:
                th, w = _gl(_theta_breaks(s.c, s.b, float(x[i]), float(zeta[i])), om)
                groups.append((np.array([i]), th, w))
            for idx, th, w in groups:
                D = (cf @ bs.dens(th)) * w
                Xs = s.c + s.b * np.cos(th)
                for i0 in range(0, len(idx), 2048):
                    ii = idx[i0:i0 + 2048]
                    xi = (x[ii, None] - Xs[None, :])
                    zt = zeta[ii, None]
                    R = np.hypot(xi, zt)
                    if self.pol == "TE":
                        H0, H1 = _h0(k * R), _h1(k * R)
                        h = H1 / R
                        u[ii] += np.sum(0.5j * k * zt * h * D, axis=1)
                        if deriv:
                            hp = k * H0 / R - 2 * H1 / (R * R)
                            ux[ii] += np.sum(0.5j * k * zt * hp * xi / R * D, axis=1)
                            uz[ii] += np.sum(0.5j * k * (h + zt * zt * hp / R) * D, axis=1)
                    else:
                        H0 = _h0(k * R)
                        u[ii] += np.sum(H0 * D, axis=1)
                        if deriv:
                            H1 = _h1(k * R)
                            ux[ii] += np.sum(-k * H1 * xi / R * D, axis=1)
                            uz[ii] += np.sum(-k * H1 * zt / R * D, axis=1)
        return u, ux, uz

    def field(self, x, z, deriv: bool = True):
        """u and its gradient (du/dx, du/dz) at points (x, z) (arrays, broadcast), unit incident amplitude: u = E_y
        (TE) or Z0 H_y (TM). Regions: z < 0 (incident + specular + back-scattered), 0 <= z <= t (modal fields in the
        slits, 0 in the conductor), z > t (transmitted). Returns (u, ux, uz)."""
        x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
        shp = x.shape
        x, z = x.ravel(), z.ravel()
        t = self.thickness
        u = np.zeros(x.shape, complex)
        ux = np.zeros(x.shape, complex)
        uz = np.zeros(x.shape, complex)
        below = z < 0
        above = (z > t) | ((z == t) & (t == 0) & (self.pol == "TM"))
        inside = ~below & ~above
        sgn = 1.0 if self.pol == "TE" else 0.5j  # TE: Dirichlet kernel; TM: (i/2) H0 below, -(i/2) H0 above
        if np.any(below):
            i = np.nonzero(below)[0]
            a, ax, az = self._aperture_sum(x[i], -z[i], "r", deriv)
            ein = np.exp(1j * (self.q0 * x[i] + self.kz0 * z[i]))
            esp = self.r_spec * np.exp(1j * (self.q0 * x[i] - self.kz0 * z[i]))
            u[i] = ein + esp + sgn * a
            ux[i] = 1j * self.q0 * (ein + esp) + sgn * ax
            uz[i] = 1j * self.kz0 * (ein - esp) - sgn * az
        if np.any(above):
            i = np.nonzero(above)[0]
            sg = 1.0 if self.pol == "TE" else -0.5j
            a, ax, az = self._aperture_sum(x[i], z[i] - t, "t", deriv)
            u[i], ux[i], uz[i] = sg * a, sg * ax, sg * az
        if np.any(inside):
            i = np.nonzero(inside)[0]
            if self.method == "modal":
                A, B = self._split(self.coef["A"]), self._split(self.coef["B"])
                for bs, a_, b_ in zip(self.bases, A, B):
                    s = bs.s
                    sel = (x[i] > s.c - s.b) & (x[i] < s.c + s.b)
                    if not np.any(sel):
                        continue
                    ii = i[sel]
                    beta = bs.beta[:, None]
                    ef = np.exp(1j * beta * z[ii][None, :])
                    eb = np.exp(1j * beta * (t - z[ii])[None, :])
                    zf = a_[:, None] * ef + b_[:, None] * eb
                    zb = 1j * beta * (a_[:, None] * ef - b_[:, None] * eb)
                    ph = np.outer(bs.alpha, x[ii] - s.l)
                    f, fp = (np.sin(ph), bs.alpha[:, None] * np.cos(ph)) if self.pol == "TE" else \
                        (np.cos(ph), -bs.alpha[:, None] * np.sin(ph))
                    u[ii] = np.sum(f * zf, axis=0)
                    ux[ii] = np.sum(fp * zf, axis=0)
                    uz[ii] = np.sum(f * zb, axis=0)
            else:  # zero thickness, TE on the plane: the aperture field
                for bs, cf in zip(self.bases, self._side("t")):
                    s = bs.s
                    sel = (x[i] > s.c - s.b) & (x[i] < s.c + s.b)
                    if np.any(sel):
                        u[i[sel]] = cf @ bs.values_x(x[i[sel]])
                ux[i] = np.nan
                uz[i] = np.nan
        return u.reshape(shp), ux.reshape(shp), uz.reshape(shp)

    def components(self, x, z) -> dict:
        """Physical fields (SI, for an incident |E| of 1 V/m): TE: E_y, H_x, H_z; TM: H_y, E_x, E_z; and the energy
        flux S_x, S_z (W/m^2)."""
        u, ux, uz = self.field(x, z)
        k = self.k
        if self.pol == "TE":
            out = {"E_y": u, "H_x": 1j / (k * Z0) * uz, "H_z": -1j / (k * Z0) * ux}
        else:
            out = {"H_y": u / Z0, "E_x": -1j / k * uz, "E_z": 1j / k * ux}
        out["S_x"] = np.imag(np.conj(u) * ux) / (2 * k * Z0)
        out["S_z"] = np.imag(np.conj(u) * uz) / (2 * k * Z0)
        return out

    def intensity(self, x, z):
        """|E|^2 / |E_inc|^2 at points (x, z): TE |u|^2; TM (|du/dz|^2 + |du/dx|^2)/k^2."""
        u, ux, uz = self.field(x, z, deriv=self.pol == "TM")
        if self.pol == "TE":
            return np.abs(u) ** 2
        return (np.abs(ux) ** 2 + np.abs(uz) ** 2) / self.k ** 2

    def flux_z(self, x, z):
        """Normalised energy flux j_z = Im(u* du/dz)/k (the incident wave: cos theta)."""
        u, _, uz = self.field(x, z)
        return np.imag(np.conj(u) * uz) / self.k

    def per_slit(self, x, z, side: str = "t"):
        """(n_slits, ...) contributions of each slit's aperture to u at points (x, z) of the side (z measured from that
        face, > 0), without incident and specular waves: the decomposition of the scattered field by slit."""
        x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
        out = []
        sg = (1.0 if self.pol == "TE" else (-0.5j if side == "t" else 0.5j))
        full = self.coef["exit" if side == "t" else "entrance"]
        off = np.concatenate([[0], np.cumsum(self.modes)])
        for i in range(len(self.slits)):
            keep = np.zeros_like(full)
            keep[off[i]:off[i + 1]] = full[off[i]:off[i + 1]]
            saved = self.coef["exit" if side == "t" else "entrance"]
            self.coef["exit" if side == "t" else "entrance"] = keep
            try:
                a, _, _ = self._aperture_sum(x.ravel(), z.ravel(), side, deriv=False)
            finally:
                self.coef["exit" if side == "t" else "entrance"] = saved
            out.append((sg * a).reshape(x.shape))
        return np.stack(out)


EDGE_KW_MAX = 140.0  # 'auto' uses the edge basis for a zero-thickness screen up to this k w (review B8 C7)


def _default_modes(k, w, method):
    if method == "edge":
        return int(min(90, max(8, math.ceil(k * w / 2) + 10)))
    return int(min(400, max(16, math.ceil(k * w / math.pi) + 24)))


def _solve_system(k, pol, method, thickness, theta, bases, L, exc):
    """Coefficients of the solution from the operator L and the excitation exc (int basis exp(i q0 x) dx)."""
    kz0 = k * math.cos(theta)
    coef, info = {}, {"method": method}
    if method == "edge":
        if pol == "TE":
            c = np.linalg.solve(L, kz0 * exc)  # aperture u
        else:
            c = np.linalg.solve(L, 1j * exc)  # aperture du/dz
        coef["exit"] = coef["entrance"] = c
        info["cond"] = float(np.linalg.cond(L))
        return coef, info
    t = thickness
    N = np.concatenate([bs.norms() for bs in bases])
    for bs in bases:
        bb = np.sqrt(k * k - bs.alpha.astype(complex) ** 2)
        # a mode exactly at cut-off (beta = 0: field a + b z) is not representable by A exp(i beta z) + B ...;
        # beta is moved to 1e-6 k i there (the solution is continuous in beta: change O(1e-12 (k t)^2), about
        # six digits lost in the cancellation of A and B)
        bs.beta = np.where(np.abs(bb) < 1e-6 * k, 1e-6j * k, bb)
    beta = np.concatenate([bs.beta for bs in bases])
    E = np.exp(1j * beta * t)
    if pol == "TE":
        P_ = L + np.diag(N * beta)
        M_ = (L - np.diag(N * beta)) * E[None, :]
        rhs = 2 * kz0 * exc
    else:
        Zb = L * beta[None, :]
        P_ = np.diag(N) + Zb
        M_ = (np.diag(N) - Zb) * E[None, :]
        rhs = 2 * exc
    S = np.linalg.solve(P_ + M_, rhs)  # A + B
    D = np.linalg.solve(P_ - M_, rhs)  # A - B
    A, B = 0.5 * (S + D), 0.5 * (S - D)
    u0, u1 = A + E * B, E * A + B
    g0, g1 = 1j * beta * (A - E * B), 1j * beta * (E * A - B)
    coef.update(A=A, B=B, u0=u0, u1=u1, g0=g0, g1=g1)
    if pol == "TE":
        coef["entrance"], coef["exit"] = u0, u1
    else:
        coef["entrance"], coef["exit"] = g0, g1
    info["P_modes"] = float(np.imag(np.sum(N * np.conj(u1) * g1)) / k)
    info["cond"] = float(max(np.linalg.cond(P_ + M_), np.linalg.cond(P_ - M_)))
    return coef, info


def solve(k: float, centers, widths, thickness: float = 0.0, pol: str = "TE", theta: float = 0.0,
          modes=None, method: str = "auto") -> SlitSolution:
    """Solve the diffraction of the plane wave (wavenumber k, angle theta from the normal) by slits of the given
    centres and widths (same length unit as 1/k) in a perfectly conducting screen of the given thickness (0: zero
    thickness), polarisation 'TE' (E along the slits) or 'TM' (H along the slits). method: 'modal' (waveguide modes;
    t >= 0), 'edge' (edge-conditioned basis; t = 0 only), 'auto' (edge for t = 0 and k w <= EDGE_KW_MAX = 140, modal
    otherwise). modes: per slit (an int or a list); the default grows with the slit width (all propagating modes plus
    24 for the waveguide modes; k w/2 + 10, at most 90, for the edge basis).

    Convergence (measured; review B8 C6, C7): the edge basis converges exponentially (k w = 129: T unchanged to 1e-7
    from 75 to 95 functions); it costs about (k w)^2 in the operator's quadrature (a few seconds per polarisation at
    k w = 130 for two slits). The waveguide modes converge algebraically, because the field is singular at the screen's
    corners: orders 1.2-1.4 measured between 2, 4 and 8 times the default count (six geometries, w = 0.3-2 lambda,
    t = 0.2-0.6 lambda: TE 1.23-1.33, TM 1.34-1.36), and at the default count T is 0.04-0.19 % low (the slit of
    1.3 lambda in a screen of 0.5 lambda: TE -0.039 %, TM -0.19 %) [error in earlier: this docstring said ~M^-1.4 for
    TE there; review B8 C6]. At zero thickness they miss the edge singularity: order 0.8-1.0, irregular at the default
    count, and T is 0.2-0.5 % low for k w = 40-130 — which is why 'auto' keeps the edge basis up to k w = 140. ``SlitSolution.error_estimate``
    estimates the truncation error from sub-blocks of the same operator (no new quadrature), ``convergence`` measures it
    by solving again."""
    pol = _pol(pol)
    centers = np.atleast_1d(np.asarray(centers, float))
    widths = np.broadcast_to(np.atleast_1d(np.asarray(widths, float)), centers.shape).copy()
    if np.any(widths <= 0):
        raise ValueError("solve: slit widths > 0")
    order = np.argsort(centers)
    centers, widths = centers[order], widths[order]
    if np.any(centers[1:] - widths[1:] / 2 <= centers[:-1] + widths[:-1] / 2):
        raise ValueError("solve: the slits overlap")
    if thickness < 0:
        raise ValueError("solve: thickness >= 0")
    if not abs(theta) < 0.5 * math.pi:
        raise ValueError("solve: |theta| < pi/2")
    if method == "auto":
        method = "edge" if thickness == 0 and k * float(np.max(widths)) <= EDGE_KW_MAX else "modal"
    if method == "edge" and thickness != 0:
        raise ValueError("solve: the edge basis is for a zero-thickness screen")
    slits = [_Slit(float(c), float(w)) for c, w in zip(centers, widths)]
    if modes is None:
        modes = [_default_modes(k, s.w, method) for s in slits]
    else:
        modes = list(np.broadcast_to(np.atleast_1d(np.asarray(modes, int)), centers.shape))
    bases = [_Basis(method, pol, s, int(M)) for s, M in zip(slits, modes)]
    q0 = k * math.sin(theta)
    L = _operator(k, pol, bases)
    exc = np.concatenate([bs.ft(np.array([-q0]))[:, 0] for bs in bases])  # int basis exp(i q0 x) dx
    coef, info = _solve_system(k, pol, method, thickness, theta, bases, L, exc)
    return SlitSolution(k, pol, float(theta), float(thickness), slits, method, [int(m) for m in modes], bases, coef,
                        info, (L, exc))


def convergence(k, centers, widths, thickness=0.0, pol="TE", theta=0.0, modes=(8, 16, 32), method="auto") -> list:
    """Transmission per slit width and the transmitted far field for increasing numbers of modes: [(M, T,
    max |f_M - f_last| / max |f_last|)] (a measured convergence, for runs and tests)."""
    sols = [solve(k, centers, widths, thickness, pol, theta, M, method) for M in modes]
    ph = np.linspace(-1.4, 1.4, 201)
    fl = sols[-1].far_field(ph)
    return [(int(M), s.transmission(), float(np.max(np.abs(s.far_field(ph) - fl)) / np.max(np.abs(fl))))
            for M, s in zip(modes, sols)]


# --- narrow-slit limits (Rayleigh 1897, transmitted power derived from his far fields) ---------------------------------
def rayleigh_narrow_transmission(k: float, w: float, pol: str) -> float:
    """Leading low-frequency transmission per slit width of a narrow slit (k w << 1) in a screen of zero thickness at
    normal incidence, from Rayleigh's far fields (Phil. Mag. 43, 259 (1897), eqs. 46 and 53): TE (E along the slit)
    (pi^2/256)(k w)^3; TM (H along the slit) pi^2 / (4 k b [(gamma + ln(k b/4))^2 + pi^2/4]), b = w/2."""
    pol = _pol(pol)
    b = 0.5 * w
    if pol == "TE":
        return math.pi ** 2 / 256 * (k * w) ** 3
    return math.pi ** 2 / (4 * k * b * ((EULER_GAMMA + math.log(k * b / 4)) ** 2 + math.pi ** 2 / 4))


# --- Sommerfeld's half-plane ------------------------------------------------------------------------------------------
def _fresnel_F(a):
    """F(a) = exp(-i pi/4)/sqrt(pi) int_a^inf exp(i tau^2) dtau = erfc(exp(-i pi/4) a)/2."""
    return 0.5 * special.erfc(cmath.exp(-0.25j * math.pi) * np.asarray(a, float))


def half_plane(k: float, x, z, pol: str = "TE", theta: float = 0.0):
    """Sommerfeld's exact field u (E_y for TE, Z0 H_y for TM; unit incident amplitude) of the plane wave
    exp(i k (x sin theta + z cos theta)) on the perfectly conducting half-plane z = 0, x < 0 (edge on the y axis)."""
    pol = _pol(pol)
    x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
    rho = np.hypot(x, z)
    phi = np.arctan2(z, x) + math.pi  # in (0, 2 pi]: 0 just below the screen, 2 pi just above it
    phi0 = 0.5 * math.pi - theta
    s = -1.0 if pol == "TE" else 1.0

    def U(psi):
        return np.exp(-1j * k * rho * np.cos(psi)) * _fresnel_F(-np.sqrt(2 * k * rho) * np.cos(0.5 * psi))

    return U(phi - phi0) + s * U(phi + phi0)


def half_plane_edge_wave(k: float, x, z, pol: str = "TE", theta: float = 0.0):
    """The edge-diffracted cylindrical wave of the half-plane far from the edge and from the shadow boundaries
    (Sommerfeld 1896 pp. 368–369; Keller's coefficient): D(phi, phi0) exp(i k rho)/sqrt(rho),
    D = -exp(i pi/4) / (2 sqrt(2 pi k)) [sec((phi - phi0)/2) -+ sec((phi + phi0)/2)] (- TE, + TM)."""
    pol = _pol(pol)
    x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
    rho = np.hypot(x, z)
    phi = np.arctan2(z, x) + math.pi
    phi0 = 0.5 * math.pi - theta
    s = -1.0 if pol == "TE" else 1.0
    D = -cmath.exp(0.25j * math.pi) / (2 * math.sqrt(2 * math.pi * k)) * (
        1 / np.cos(0.5 * (phi - phi0)) + s / np.cos(0.5 * (phi + phi0)))
    return D * np.exp(1j * k * rho) / np.sqrt(rho)


def half_plane_geometric(k: float, x, z, pol: str = "TE", theta: float = 0.0):
    """Geometric optics of the half-plane: the incident wave where it is not shadowed, the specularly reflected wave
    where the screen reflects it (the limits the exact solution tends to away from the edge)."""
    pol = _pol(pol)
    x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
    phi = np.arctan2(z, x) + math.pi
    phi0 = 0.5 * math.pi - theta
    inc = np.exp(1j * k * (x * math.sin(theta) + z * math.cos(theta)))
    refl = np.exp(1j * k * (x * math.sin(theta) - z * math.cos(theta)))
    lit = np.abs(phi - phi0) < math.pi
    refl_region = phi + phi0 < math.pi
    s = -1.0 if pol == "TE" else 1.0
    return np.where(lit, inc, 0.0) + np.where(refl_region, s * refl, 0.0)


__all__ = ["SlitSolution", "solve", "convergence", "EDGE_KW_MAX",
           "rayleigh_narrow_transmission", "half_plane", "half_plane_edge_wave", "half_plane_geometric", "Z0"]
