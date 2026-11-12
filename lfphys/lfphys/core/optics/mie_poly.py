# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Light scattered by a cloud of spheres of many sizes (a polydisperse average of the exact Mie series), for one
wavelength at a time; the building block of white-light scattering (plan P1/P14.8, batch B8).

Single scattering by a dilute cloud: drops scatter independently and their intensities add, so the cloud's
differential cross section per drop is the average over the size distribution n(r):

    <dsigma/dOmega>(theta) = int n(r) (|S1|^2 + |S2|^2)/(2 k^2) dr,   <C_sca> = int n(r) pi r^2 Q_sca dr

(and likewise (|S2|^2 - |S1|^2)/(2 k^2) for the polarisation, k = 2 pi N_medium / lambda). The distribution is a
gamma distribution of mean r_mean and relative standard deviation w (shape 1/w^2, scale r_mean w^2; w = 0: one size),
cut at +-n_sigma standard deviations (default 4) and renormalised on the cut: the probability mass cut off is returned
("tail", from the gamma distribution's CDF); the cut's bias on <dsigma/dOmega> was measured <= 2-3 tail of its peak
(3 sigma: tail 2.7e-3 - 3.8e-3, bias up to 4.6e-3 of the peak for 15 um +- 15 %; 4 sigma: tail <= 2.8e-4, bias
<= 5.5e-4; review B8-mie, M7) and is not part of "err". [error in earlier] the cut was +-3 sigma and not stated.

The integral over r is a trapezoid sum on nodes uniform in the size parameter x with spacing at most dx_max (0.25).
What that resolves, measured by FFT of |S1|^2 + |S2|^2 over x in [1000, 1060] for water (review B8-mie, s06c): near
the bows the ripple of the reflected against the internally reflected waves has periods 1.25-1.28 in x (140 deg) and
1.18 (175 deg, = 2 pi/4m, reflection against p = 2 on the axis): 4-5 nodes per period, resolved. At the antisolar
point the strongest component has period ~0.27 (and 0.39, 0.83): about one node per period, NOT resolved; there the
sum at dx_max relies on the gamma weight being smooth over many periods (sigma_x = w x >> 1, so that the weight's
Fourier transform at the alias frequency is small) rather than on sampling the ripple, and its error is larger: in the
v17 presets the largest actual errors sit at theta > 170 deg (7e-3 - 2e-2 of the peak, against 7e-4 - 4e-3 at the
bow; review B8-mie, s06). [error in earlier] "the ripple (period ~1.5 in x) is resolved". The narrow resonances of the
series (widths far below dx_max) are sampled, not resolved.

The error of the sum is estimated by the difference of the two interleaved half-sums (even and odd nodes), "err"
per angle. Per angle it is not an error estimate (in the v17 presets the actual error exceeds it at 35-51 % of the
angles, by up to 1e2-1e6 where the half-sums happen to agree); its maximum over the angles is an order-of-magnitude
estimate of the largest error over the angles (measured: the largest actual error is 0.1-3x that maximum against
sums 25-50x finer). It contains neither the cut's bias nor the resonances' sampling beyond what the half-sums see.
[error in earlier] "err ... per angle".
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

from lfphys.i18n import T
from . import mie

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Scattering by a cloud of spheres of different sizes (the Mie series averaged)"),
    "statement": T("The scattering and extinction cross-sections averaged over a gamma distribution of sizes and the "
                   "differential cross-section ⟨dσ/dΩ⟩(θ) of unpolarised light (and its polarised part) at one "
                   "wavelength; single scattering by a dilute cloud, the intensities of the drops add."),
    "validity": T("single scattering (an optically thin cloud), independent drops; the distribution is cut at ±4σ "
                  "(the probability cut off is returned; the bias of the cut ≲ 3 times that fraction of the peak); the "
                  "integral over sizes is a sum over nodes with a step ≤ dx_max = 0.25 in x: the ripple of the "
                  "rainbows (period 1.2–1.3 in x) is resolved, at the antisolar point (period ~0.27) it is not and the "
                  "sum converges thanks to the smoothness of the distribution; narrow resonances are sampled; the "
                  "error is an order-of-magnitude estimate (the largest difference over the angles between two "
                  "alternating half sums)"),
    "basis": [T("Bohren & Huffman (1983), §4.4 and ch. 13 (size distributions)"), T("Hansen & Travis, Space Sci. Rev. "
                                                                                   "16, 527 (1974): averages over size "
                                                                                   "distributions")],
    "conflicts": [],
}


def gamma_pdf(r, r_mean: float, w: float):
    """The gamma distribution of mean r_mean and relative standard deviation w (shape k = 1/w^2, scale r_mean w^2)."""
    r = np.asarray(r, float)
    k = 1.0 / (w * w)
    th = r_mean * w * w
    with np.errstate(divide="ignore"):
        lg = (k - 1.0) * np.log(r) - r / th - special.gammaln(k) - k * math.log(th)
    return np.where(r > 0, np.exp(lg), 0.0)


def gamma_tail(lo: float, hi: float, r_mean: float, w: float) -> float:
    """The probability mass of the gamma distribution outside [lo, hi] (regularised incomplete gamma functions)."""
    k = 1.0 / (w * w)
    th = r_mean * w * w
    return float(special.gammainc(k, lo / th) + special.gammaincc(k, hi / th))


def size_nodes(r_mean: float, w: float, lam: float, n_medium: float = 1.0, *, dx_max: float = 0.25,
               n_sigma: float = 4.0, max_nodes: int = 4000) -> dict:
    """Nodes and weights (summing to 1) of the size average at wavelength lam (same length unit as r_mean):
    {"r", "w", "x", "dx", "coarse", "tail", "n_sigma"}; dx = dx_max unless that would need more than max_nodes nodes
    (then larger: "coarse"); "tail" the probability mass cut off by the +-n_sigma cut."""
    if w <= 0:
        x = float(mie.size_parameter(r_mean, lam, n_medium))
        return {"r": np.array([float(r_mean)]), "w": np.array([1.0]), "x": np.array([x]), "dx": 0.0, "coarse": False,
                "tail": 0.0, "n_sigma": 0.0}
    lo = max(r_mean * (1.0 - n_sigma * w), r_mean * 1e-3)
    hi = r_mean * (1.0 + n_sigma * w)
    kx = 2.0 * math.pi * n_medium / lam
    span = (hi - lo) * kx
    n = int(math.ceil(span / dx_max)) + 1
    coarse = n > max_nodes
    n = min(max(n, 9), max_nodes)
    if n % 2 == 0:  # odd: the two interleaved half-sums cover the same interval (and n <= max_nodes)
        n = n + 1 if n + 1 <= max_nodes else n - 1
    r = np.linspace(lo, hi, n)
    tw = np.full(n, r[1] - r[0])
    tw[0] = tw[-1] = 0.5 * (r[1] - r[0])
    wt = tw * gamma_pdf(r, r_mean, w)
    wt = wt / wt.sum()
    return {"r": r, "w": wt, "x": r * kx, "dx": float((r[1] - r[0]) * kx), "coarse": coarse,
            "tail": gamma_tail(lo, hi, r_mean, w), "n_sigma": float(n_sigma)}


def average(m, lam: float, nodes: dict, theta, n_medium: float = 1.0, chunk: int = 256, angular=None) -> dict:
    """The size average at one wavelength (lam, vacuum; lengths in the unit of the radii): "dsdo" =
    <(|S1|^2 + |S2|^2)/(2k^2)> (area per sr), "dsdo_pol" = <(|S2|^2 - |S1|^2)/(2k^2)>, "dsdo_1", "dsdo_2" (each
    polarisation), "C_sca", "C_ext" (mean cross sections), "err" (the half-sum difference of dsdo at each angle: only
    its maximum over the angles is meaningful, as an order-of-magnitude estimate of the largest error; module
    docstring), "err_C_sca", "tail" (the probability mass the cut removed, from ``nodes``). ``angular``: (PI, TAU) of
    mie.angular at theta for at least the needed orders (reused across wavelengths)."""
    theta = np.atleast_1d(np.asarray(theta, float))
    k = 2.0 * math.pi * n_medium / lam
    x = nodes["x"]
    wts = nodes["w"]
    N = mie.n_terms(float(x.max()))
    if angular is None or angular[0].shape[0] < N:
        angular = mie.angular(np.cos(theta), N)
    PI, TAU = angular[0][:N], angular[1][:N]
    n = np.arange(1, N + 1)
    c = (2 * n + 1) / (n * (n + 1.0))
    acc = {key: np.zeros(len(theta)) for key in ("I1", "I2")}
    half = {key: np.zeros(len(theta)) for key in ("I1e", "I2e")}
    csca = cext = csca_e = 0.0
    order = np.argsort(x)
    for i0 in range(0, len(x), chunk):
        idx = order[i0:i0 + chunk]
        xs = x[idx]
        Nk = mie.n_terms(float(xs.max()))
        a, b = mie.coefficients_batch(m, xs, n_max=Nk)
        q = mie.efficiencies_from(a, b, xs)
        ac, bc = a * c[:Nk], b * c[:Nk]
        P, T = PI[:Nk], TAU[:Nk]
        S1 = (ac.real @ P + bc.real @ T) + 1j * (ac.imag @ P + bc.imag @ T)
        S2 = (ac.real @ T + bc.real @ P) + 1j * (ac.imag @ T + bc.imag @ P)
        w = wts[idx]
        even = (idx % 2 == 0)
        i1, i2 = np.abs(S1) ** 2, np.abs(S2) ** 2
        acc["I1"] += w @ i1
        acc["I2"] += w @ i2
        half["I1e"] += (w * even) @ i1
        half["I2e"] += (w * even) @ i2
        area = math.pi * (xs / k) ** 2
        csca += float(np.sum(w * area * np.asarray(q["Qsca"])))
        cext += float(np.sum(w * area * np.asarray(q["Qext"])))
        csca_e += float(np.sum(w * even * area * np.asarray(q["Qsca"])))
    f = 1.0 / (2.0 * k * k)
    out = {"dsdo_1": 2 * f * acc["I1"], "dsdo_2": 2 * f * acc["I2"], "C_sca": csca, "C_ext": cext,
           "k": k, "n_nodes": len(x), "dx": nodes["dx"], "coarse": nodes["coarse"], "angular": angular,
           "tail": float(nodes.get("tail", 0.0))}
    out["dsdo"] = f * (acc["I1"] + acc["I2"])
    out["dsdo_pol"] = f * (acc["I2"] - acc["I1"])
    if len(x) > 2:
        # half-sums: the even nodes and the odd nodes, each renormalised to the total weight
        we = float(np.sum(wts[::2]))
        wo = 1.0 - we
        ie = f * (half["I1e"] + half["I2e"]) / we
        io = f * ((acc["I1"] - half["I1e"]) + (acc["I2"] - half["I2e"])) / wo
        out["err"] = 0.5 * np.abs(ie - io)
        out["err_C_sca"] = 0.5 * abs(csca_e / we - (csca - csca_e) / wo)
    else:
        out["err"] = np.zeros(len(theta))
        out["err_C_sca"] = 0.0
    return out
