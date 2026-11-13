# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""r13 apparatus: where the particle flies (freely to a detecting plane, or through r12's double slit), the initial
states along the flight (one packet, a train of packets, a two-speed superposition with backflow) and the soft
detector's potential. No physics of its own: the wave is evolved by lfphys.core.quantum.schrodinger_nd, the
closed-form free states come from lfphys.core.quantum.schrodinger1d.FreeGaussians.

Units as in r12: lengths in de Broglie wavelengths lambda of the mean momentum hbar k0 (k0 = 2 pi), hbar = m = 1.
The flight runs along z; the initial state is separable, chi(x) phi(z - z_lead), with chi a Gaussian of width sigma_x
and phi a superposition of Gaussians whose leading packet is centred at z_lead (0 in free flight, r12's source point
before the plate).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core.quantum.schrodinger1d import FreeGaussians
from lfphys.i18n import T
from lfviz.errors import Refusal
from r12_double_slit_2d.engine import apparatus as AP11

K0, E0, V0_SPEED, ABS_W = AP11.K0, AP11.E0, AP11.V0_SPEED, AP11.ABS_W
BACKFLOW_RATIO = 0.25  # the slow packet's wavenumber in units of k0 (the fast one is k0)
BACKFLOW_AMP = 1.5     # its amplitude relative to the fast one: with both meeting at the plane 1.5 % of the probability
                       # flows back through it (sigma_z = 2-5 lambda, the slow packet 5.5 sigma_z before the plane)
OVERLAP_MAX = 1e-4     # the initial state may hold at most this much beyond the detecting plane


def packets(state: str, sigma_z: float, n_train: int = 4, sep: float = 30.0, D: float = 30.0):
    """The longitudinal state as FreeGaussians packets (c, z0, k, s) with the leading packet at z = 0 and the
    detecting plane at z = D: ``gauss`` one packet of mean wavenumber k0; ``train`` n_train equal packets at
    z = -j sep, each the translate of the first (carrier phase e^{i k0 j sep}, as in Das & Struyve 2021, eq. 18); ``backflow``
    a slow packet (k0 / 4, amplitude 1.5) at z = 0 and a fast one (k0, amplitude 1) behind it at z = -3D, timed so that
    both centres reach the plane together: there the two overlap and the current flows back for a while."""
    s = float(sigma_z)
    if state == "gauss":
        return [(1.0, 0.0, K0, s)]
    if state == "train":
        n = int(n_train)
        if sep < 6 * s:
            raise Refusal(T("the packets of the train overlap: the distance {sep} λ is less than 6σz = {m} λ", sep=float(sep),
                            m=6 * s), T("take the distance at least 6σz or narrower packets"))
        return [(complex(np.exp(1j * K0 * j * sep)), -j * float(sep), K0, s) for j in range(n)]
    if state == "backflow":
        return [(BACKFLOW_AMP, 0.0, BACKFLOW_RATIO * K0, s), (1.0, -(1 / BACKFLOW_RATIO - 1) * float(D), K0, s)]
    raise ValueError(f"unknown initial state: {state}")


def overlap(fg: FreeGaussians, D: float) -> float:
    """The initial probability beyond the plane at distance D ahead of the leading packet."""
    return float(1.0 - fg.cdf(D, 0.0)[0])


def k_range(pk, width: float = 8.0):
    """Wave numbers that carry the state: each packet's k +- ``width`` standard deviations 1/(2 s)."""
    lo = min(k - width / (2 * s) for _, _, k, s in pk)
    hi = max(k + width / (2 * s) for _, _, k, s in pk)
    return lo, hi


def rear(pk) -> float:
    """The rearmost packet's centre (<= 0)."""
    return min(z0 for _, z0, _, _ in pk)


def leave_time(fg: FreeGaussians, d: float, tail: float = 1e-4) -> float:
    """Free flight: the time by which all but ``tail`` of the probability has crossed the plane at distance d ahead of
    the leading packet (bisection on P(z < d, t), which only falls for states moving forwards)."""
    lo, hi = 0.0, 1.0
    while fg.cdf(d, hi)[0] > tail:
        lo, hi = hi, 2 * hi
        if hi > 1e6:
            raise Refusal(T("the state does not move beyond the detecting plane"))
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if fg.cdf(d, mid)[0] > tail:
            lo = mid
        else:
            hi = mid
    return hi


SCREEN_LAYERS = [(6.0, 2.0), (12.0, 1.0), (24.0, 0.5), (36.0, 0.5), (48.0, 0.25)]  # (width lambda, height E0)


def screen_layer(k_lo: float, k_hi: float, R_max: float = 1e-5, T_max: float = 1e-6):
    """The narrowest absorbing layer W (s/width)^2 of SCREEN_LAYERS that reflects less than R_max and leaks less than
    T_max over the spectrum [k_lo, k_hi] (stationary transfer matrices, normal incidence): r12's layer (6 lambda,
    2 E0) is tuned for k ~ k0 and reflects 2.5 % at k0/4 (the slow packet of the backflow state)."""
    from lfphys.core.quantum import schrodinger_nd as S
    k = np.linspace(max(k_lo, 0.05 * K0), k_hi, 9)
    for w, Wf in SCREEN_LAYERS:
        R, Tr = S.layer_reflection(k, w, Wf * E0, 1.0)
        if R.max() < R_max and Tr.max() < T_max:
            return w, Wf
    raise Refusal(T("no absorber for the spectrum [{lo:.3g}, {hi:.3g}] λ⁻¹: the wave is too slow", lo=float(k_lo),
                    hi=float(k_hi)))


class FreeGeometry(AP11.Geometry):
    """Free flight along z from the leading packet's centre (z = 0) to the detecting plane z = L; no plate. The
    window: the state's rear minus 5 sigma_z, the detector layer beyond L, and across, the transverse packet at the
    end of the flight within ``screen_half`` (5 of its widths)."""

    def __init__(self, L, sigma_x, sigma_z, h, z_rear, t_end, edge=0.2, layer=(ABS_W, AP11.ABS_STRENGTH)):
        self.a = self.d = self.w = 0.0
        self.L = float(L)
        self.sx, self.sz, self.h = float(sigma_x), float(sigma_z), float(h)
        self.edge = float(edge)
        self.n_slits = 0
        self.centers = []
        sx_end = self.sx * math.sqrt(1 + (t_end / (2 * self.sx ** 2)) ** 2)  # hbar = m = 1
        self.screen_half = 5.0 * sx_end
        self.z_src = 0.0
        self.z_min = float(z_rear) - 5.0 * self.sz - ABS_W
        self.screen_w, self.screen_W = layer
        self.z_max = self.L + AP11.SCREEN_GAP + self.screen_w
        self.x_half = self.screen_half + ABS_W

    def plate(self, g, open_slits=(True, True)) -> np.ndarray:
        return np.zeros(g.shape)


class SlitGeometry(AP11.Geometry):
    """r12's double slit, the window lengthened behind the source for a train of packets."""

    def __init__(self, *args, back: float = 0.0, layer=(ABS_W, AP11.ABS_STRENGTH), **kw):
        super().__init__(*args, **kw)
        self.z_min -= float(back)
        self.screen_w, self.screen_W = layer
        self.z_max = self.L + AP11.SCREEN_GAP + self.screen_w


def soft_detector(g, L: float, W0: float, edge: float) -> np.ndarray:
    """The soft detector: an absorbing potential -i W0 that rises over ``edge`` (tanh) at the plane z = L and fills
    the half-space beyond it."""
    Z = np.broadcast_to(g.mesh()[1], g.shape)
    return W0 * AP11.smooth_step(Z - L, edge)


def soft_profile(W0: float, edge: float):
    """The same potential along z with the plane at 0, for stationary transfer matrices (complex: -i W)."""
    return lambda z: -1j * W0 * AP11.smooth_step(np.asarray(z, float), edge)
