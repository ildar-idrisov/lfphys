# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v11 apparatus: the double slit in the plane (x, z) as potentials on a grid, the packet, the detectors, the path
mark and the flux; references of the approximate theories for the checks. No physics of its own: the wave is evolved
by lfphys.core.quantum.schrodinger_nd, the trajectories by lfphys.theories.interpretations.bohm.

Units of the computation: lengths in de Broglie wavelengths lambda of the packet's mean momentum, hbar = m = 1. Then
k0 = 2 pi, the speed v0 = 2 pi (lambda per unit time), the energy E0 = 2 pi^2; one unit of time is m lambda^2 / hbar
of the chosen particle (``time_unit``).

The plate: a wall of height V0 (in units of E0) and thickness w across the beam at z = 0, with two slits of width a
centred at x = -+d/2 (slit A at -d/2, slit B at +d/2); edges smoothed over ``EDGE`` (one grid step: the sampled
potential stays resolved). The slits are long along y: the 2-D model is the exact reduction of that 3-D set-up
(nothing depends on y).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core.quantum import schrodinger_nd as S
from lfphys.i18n import T
from lfviz.errors import Refusal

K0 = 2 * math.pi       # the packet's mean wavenumber (lambda = 1)
V0_SPEED = K0          # its speed, hbar k0 / m
E0 = 0.5 * K0 * K0     # its energy
ABS_W = 6.0            # absorbing layers: width (lambda)
ABS_STRENGTH = 2.0     # and height (units of E0); chosen by layer_reflection (README): R < 1e-5 for the beam
SCREEN_GAP = 4.0       # free space between the screen's face z = L and its absorbing layer (lambda): the layer's W''
                       # jumps at its inner face, so the wave is only C^3 there and a difference stencil centred on it
                       # errs by ~h^4 (1.2e-4 of the flux at lambda/5, v12); the gap keeps the flux's stencil (16 samples
                       # each side, 3.2 lambda at lambda/5) in free space


def smooth_step(u, eps):
    """0 -> 1 across u = 0 over a width ~ eps (tanh)."""
    return 0.5 * (1.0 + np.tanh(np.asarray(u, float) / eps))


class Geometry:
    """Lengths in lambda. ``screen_half``: half-width of the detecting screen; the window adds the absorbers."""

    def __init__(self, a, d, w, L, sigma_x, sigma_z, h, screen_half=None, slits=2, edge=0.2):
        self.a, self.d, self.w, self.L = float(a), float(d), float(w), float(L)
        self.sx, self.sz, self.h = float(sigma_x), float(sigma_z), float(h)
        self.edge = float(edge)  # the width of the wall's and the mark's edges: physics, the same on every grid
        self.n_slits = int(slits)
        self.centers = [-0.5 * self.d, 0.5 * self.d] if self.n_slits == 2 else [0.0]
        if self.a >= self.d and self.n_slits == 2:
            raise Refusal(T("the slits overlap: the slit width must be smaller than the distance between them"))
        if self.L <= self.w:
            raise Refusal(T("the screen must stand behind the plate"))
        # the screen: wide enough for the single-slit envelope to its 3rd zero (or 45 degrees), at least the
        # illuminated width
        th = math.asin(min(0.999, 3.0 / self.a)) if self.a > 3.0 else math.radians(45.0)
        th = min(th, math.radians(45.0))
        self.screen_half = float(screen_half) if screen_half else max(
            0.5 * self.d + self.a + self.L * math.tan(th), 3.0 * self.sx)
        self.z_src = -(4.5 * self.sz + 0.5 * self.w + 1.0)   # the packet's centre: its tail at the plate < 1e-4
        self.z_min = self.z_src - 4.0 * self.sz - ABS_W
        self.screen_w, self.screen_W = ABS_W, ABS_STRENGTH  # the screen's layer: width (lambda), height (E0)
        self.z_max = self.L + SCREEN_GAP + self.screen_w
        self.x_half = self.screen_half + ABS_W

    def grid(self, h: float | None = None) -> S.Grid:
        """The grid of step h (default the geometry's): x symmetric with x = 0 a sample (odd count), the screen's face
        z = L a sample (so that grids of different steps measure the flux through the same plane)."""
        h = float(h or self.h)
        nx = int(math.ceil(2 * self.x_half / h)) | 1          # odd: x = 0 is a sample, the grid is symmetric
        nb = int(math.ceil((self.L - self.z_min) / h))         # samples below the screen's face
        na = int(math.ceil((self.z_max - self.L) / h))
        nz = nb + na + 1
        zc = self.L - (nb - nz // 2) * h                       # sample nb sits at z = L
        return S.Grid((nx, nz), h, m=1.0, hbar=1.0, center=(0.0, zc))

    def plate(self, g: S.Grid, open_slits=(True, True)) -> np.ndarray:
        """The solid part of the plate (0..1); its edges rise over ``edge`` (tanh), the same on every grid (review B3-2:
        edges of one grid step made the grid choice change the wall)."""
        X, Z = g.mesh()
        eps = self.edge
        sz = smooth_step(Z + 0.5 * self.w, eps) * smooth_step(0.5 * self.w - Z, eps)
        holes = 0.0
        for c, op in zip(self.centers, open_slits):
            if op:
                holes = holes + smooth_step(X - (c - 0.5 * self.a), eps) * smooth_step((c + 0.5 * self.a) - X, eps)
        return np.broadcast_to(sz * (1.0 - holes), g.shape)

    def slit_channel(self, g: S.Grid, j: int) -> np.ndarray:
        """Slit j's channel inside the plate (0..1): where the path mark acts (edges of width ``edge``)."""
        X, Z = g.mesh()
        eps = self.edge
        c = self.centers[j]
        return np.broadcast_to(smooth_step(Z + 0.5 * self.w, eps) * smooth_step(0.5 * self.w - Z, eps)
                               * smooth_step(X - (c - 0.5 * self.a), eps) * smooth_step((c + 0.5 * self.a) - X, eps),
                               g.shape)

    def absorbers(self, g: S.Grid) -> np.ndarray:
        """Absorbing layers: the screen (the detector: from SCREEN_GAP behind its face z = L on), the source side
        (z < z_min + ABS_W) and both sides (|x| > screen_half)."""
        W0 = ABS_STRENGTH * E0
        W = S.absorbing_layer(g, 1, "high", g.axes[1][-1] - (self.L + SCREEN_GAP), self.screen_W * E0)
        W = W + S.absorbing_layer(g, 1, "low", ABS_W, W0)
        for side in ("low", "high"):
            W = W + S.absorbing_layer(g, 0, side, ABS_W, W0)
        return W

    def regions(self, g: S.Grid, zL: float) -> dict:
        """Masks of the detectors (where the absorbed probability counts): beyond the screen's front zL (all x: what
        flows through the front, also at an angle into the corners), the source side, the two sides before the
        screen, and everything before the plate's middle (z < 0: what the plate reflected)."""
        X, Z = g.mesh()
        X = np.broadcast_to(X, g.shape)
        Z = np.broadcast_to(Z, g.shape)
        beyond = Z > zL
        back = Z < self.z_min + ABS_W
        side = (np.abs(X) > self.screen_half) & ~back & ~beyond
        # reflected by the plate: whatever is absorbed on its source side, by the back layer or by the side layers
        # (counted by the side of the plate, not by which layer took it: review B3-13)
        before = Z < 0
        return {"beyond": beyond, "back": back, "side": side, "before": before}


def marker_angle_to_coupling(theta: float, w: float) -> float:
    """The first-order coupling b0 (b = b0 e_y in slit B's channel, units of hbar = m = lambda = 1): theta =
    2 b0 w / (hbar v0) for a free particle at the mean speed v0 crossing a length w. Used until B4; it ignores the
    channel's transverse mode and the edges, and turned the mark by ~1.2 theta (review B4-3)."""
    return theta * V0_SPEED / (2.0 * w)


class MarkCalibration:
    """The coupling b0 that turns the mark (the spin, or the detector's state) of the wave crossing slit B by theta,
    calibrated on the channel itself: the lowest transverse mode of slit B (the plate's profile across x at its middle
    plane, sinc-DVR: ``lfphys.core.quantum.schrodinger1d``) carries the energy E_perp; along z the two eigenstates of
    b.sigma (sigma_y = +-1) see (E_perp +- b0 c_x) s(z), with s the plate's profile along z and c_x the mode's weight
    inside the coupling's opening; their complex transmission amplitudes at the mean energy E0 (exact for the
    staircase, ``lfphys.core.quantum.transfer.staircase_amplitudes``) differ by the phase arg(t_- / t_+) = the
    rotation of the mark. b0(theta) by interpolating that rotation over 121 strengths (computed once per geometry).
    What it leaves out: higher transverse modes (they turn more), the speed spread, coupling between modes."""

    def __init__(self, geo: Geometry, V0: float):
        from lfphys.core.quantum import schrodinger1d as S1
        from lfphys.core.quantum import transfer
        a, e, c = geo.a, geo.edge, geo.centers[1]
        m = min(3.0, 0.5 * (geo.d - geo.a))
        x = np.linspace(c - 0.5 * a - m, c + 0.5 * a + m, 1201)
        hole = smooth_step(x - (c - 0.5 * a), e) * smooth_step((c + 0.5 * a) - x, e)
        E, vec = S1.Grid(x, 1.0).eigenstates(V0 * (1.0 - hole), 1)
        chi2 = vec[:, 0] ** 2 * (x[1] - x[0])
        self.E_perp, self.c_x = float(E[0]), float(np.sum(chi2 * hole) / np.sum(chi2))
        n = 600
        z = np.linspace(-0.5 * geo.w - 8 * e, 0.5 * geo.w + 8 * e, n + 1)
        zm = 0.5 * (z[1:] + z[:-1])
        s_z = smooth_step(zm + 0.5 * geo.w, e) * smooth_step(0.5 * geo.w - zm, e)
        b_max = 0.95 * (E0 - self.E_perp) / self.c_x
        self.b = np.linspace(0.0, b_max, 121)
        U = (self.E_perp + np.outer(np.concatenate([self.b, -self.b]), np.full(n, self.c_x))) * s_z[None, :]
        t, _ = transfer.staircase_amplitudes(E0, U, z[1] - z[0])
        tp, tm = t[:len(self.b)], t[len(self.b):]
        self.rotation = np.unwrap(np.angle(tm / tp))
        self.rotation -= self.rotation[0]
        self.transmission = (np.abs(tp) ** 2, np.abs(tm) ** 2)

    def coupling(self, theta: float) -> float:
        if theta <= 0:
            return 0.0
        if theta > self.rotation[-1]:
            raise Refusal(T("a turn of the mark by {a:.0f}° cannot be reached in this channel (at most {m:.0f}°: beyond "
                            "it one of the components does not pass the slit)", a=math.degrees(theta),
                            m=math.degrees(self.rotation[-1])))
        return float(np.interp(theta, self.rotation, self.b))


def time_unit(mass: float, lam: float) -> float:
    """Seconds per unit of time of the computation: m lambda^2 / hbar."""
    from scipy import constants as sc
    return mass * lam * lam / sc.hbar


# --- references of the approximate theories (checks; info) ------------------------------------------------------------
def k_nodes(sigma_z: float, n: int = 9):
    """Gauss-Hermite nodes and weights of the packet's wavenumbers along z, k ~ N(k0, 1/(2 sigma_z))."""
    x, w = np.polynomial.hermite_e.hermegauss(n)
    return K0 + x / (2.0 * sigma_z), w / w.sum()


def _coherence_matrix(geo, open_slits, phases, coherence):
    c = np.array([cc for cc, op in zip(geo.centers, open_slits) if op])
    amp = np.exp(-(c**2) / (4 * geo.sx**2))
    ph = np.zeros(len(c)) if phases is None else np.asarray([p for p, op in zip(phases, open_slits) if op])
    v = amp * np.exp(1j * ph)
    G = np.outer(v, v.conj())
    if len(c) == 2:  # the marks' overlap <m_B|m_A> damps the cross terms (two-path model)
        G[0, 1] *= coherence
        G[1, 0] *= np.conj(coherence)
    return c, v, G


def paraxial_pattern(xs, geo: Geometry, open_slits=(True, True), phases=None, coherence=1.0):
    """The screen pattern of the paraxial (Fresnel) theory with Kirchhoff boundary values (v02's engine,
    lfphys.theories.approx.paraxial): plane-wave incidence on slits weighted by the packet's transverse amplitude at
    their centres, summed over the packet's wavenumbers (time-integrated flux = sum over energies), distance from the
    plate's exit face; ``phases`` per slit (Aharonov-Bohm), ``coherence`` the marks' overlap <m_B|m_A>. Normalised to
    unit integral over xs."""
    from lfphys.theories.approx import paraxial
    ks, ws = k_nodes(geo.sz)
    c, v, G = _coherence_matrix(geo, open_slits, phases, coherence)
    z = geo.L - 0.5 * geo.w
    P = np.zeros(len(xs))
    for k, w in zip(ks, ws):
        A = paraxial.slit_amplitudes(xs[None, :], z, k, c, geo.a)[0]
        P += w * paraxial.intensity(A, G) * (k / (2 * math.pi * z))  # |U|^2 with the dropped factor k/(2 pi z)
    return P / np.trapezoid(P, xs)


def kirchhoff_pattern(xs, geo: Geometry, open_slits=(True, True), phases=None, coherence=1.0):
    """The same boundary values propagated exactly (2-D Rayleigh-Sommerfeld, lfphys.theories.approx.kirchhoff): no
    paraxial approximation, Kirchhoff's boundary values kept; the flux j_z = Im(U* dU/dz)/k by a centred difference
    of the field at z +- lambda/200. Normalised like ``paraxial_pattern``."""
    from lfphys.theories.approx import kirchhoff
    ks, ws = k_nodes(geo.sz, 7)
    c, v, G = _coherence_matrix(geo, open_slits, phases, coherence)
    z = geo.L - 0.5 * geo.w
    dz = 1.0 / 200
    P = np.zeros(len(xs))
    for k, w in zip(ks, ws):
        Up = kirchhoff.slit_fields(xs, z + dz, k, c, geo.a)  # per slit, unit amplitude
        Um = kirchhoff.slit_fields(xs, z - dz, k, c, geo.a)
        U0, dU = 0.5 * (Up + Um), (Up - Um) / (2 * dz)
        # j_z = Im sum_jl G_jl U_l^* dU_j / k (marks through G, as in the Born rule of v02)
        P += w * np.einsum("jx,lx,jl->x", dU, U0.conj(), G).imag / k
    return P / np.trapezoid(P, xs)


def fringes(xs, P, period: float, n_periods: float = 2.0):
    """The fringes near the axis as a windowed Fourier component at their spatial frequency q = 2 pi / period:
    with P = A (1 + V cos(q x - phi)) under a Hann window over |x| <= n_periods * period, returns (V, phi) =
    (2 |sum w P e^{-iqx}| / sum w P, -arg of that sum). The envelope's slow variation leaks in only weakly (unlike
    (max - min)/(max + min), which counts it as contrast)."""
    X = n_periods * period
    m = np.abs(xs) <= X
    if m.sum() < 8:
        return float("nan"), float("nan")
    x, p = xs[m], P[m]
    w = 0.5 * (1 + np.cos(np.pi * x / X))
    q = 2 * np.pi / period
    F = np.sum(w * p * np.exp(-1j * q * x))
    S0 = np.sum(w * p)
    return float(2 * abs(F) / S0), float(-np.angle(F))
