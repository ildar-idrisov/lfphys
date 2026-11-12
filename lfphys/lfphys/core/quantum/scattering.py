# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Scattering of one photon by a dipole (Thomson for a free charge, Rayleigh for a polarisable particle): the
angular distribution (3/8pi)(1 - (n.p)^2) for a dipole along p, its sampling, and the coherence it leaves between two
paths a distance d apart: <exp(i k_p (n_i - n)_x d)> (Chapman et al., PRL 75, 3783 (1995)).
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Рассеяние фотона диполем",
    "statement": "Угловое распределение (3/8π)(1 − (n·p)²); передача импульса ħk_p(n_i − n); остаточная когерентность "
                 "двух путей ⟨exp(i k_p (n_i − n)_x d)⟩.",
    "validity": "один фотон, дипольное приближение (размер ≪ λ), продольная отдача не учитывается",
    "basis": ["Jackson, Classical Electrodynamics, §9.2", "Chapman et al., PRL 75, 3783 (1995)"],
    "conflicts": [],
}


def dipole_directions(rng, pdir, n):
    """Scattering directions with the dipole pattern (3/8pi)(1 - (n.p)^2), by rejection from the uniform sphere."""
    out = np.empty((0, 3))
    while len(out) < n:
        m = 2 * (n - len(out)) + 16
        v = rng.normal(size=(m, 3))
        v /= np.linalg.norm(v, axis=1)[:, None]
        acc = rng.random(m) < 1.0 - (v @ pdir) ** 2
        out = np.vstack([out, v[acc]])
    return out[:n]


def dipole_coherence(kp_d: float, ni, pdir, n_mu=400, n_phi=400) -> complex:
    """<exp(i u (n_i,x - n_x))>, u = k_p d, over the normalised dipole pattern; Gauss-Legendre in cos(theta)
    times the trapezoid rule in phi (exact for trigonometric polynomials)."""
    mu, wmu = np.polynomial.legendre.leggauss(n_mu)
    phi = 2 * math.pi * np.arange(n_phi) / n_phi
    st = np.sqrt(1 - mu**2)
    N = np.stack([st[:, None] * np.cos(phi)[None, :], st[:, None] * np.sin(phi)[None, :],
                  np.broadcast_to(mu[:, None], (n_mu, n_phi))], axis=-1)
    pat = 3.0 / (8 * math.pi) * (1 - (N @ np.asarray(pdir, float)) ** 2)
    f = np.exp(1j * kp_d * (ni[0] - N[..., 0]))
    w = wmu[:, None] * (2 * math.pi / n_phi)
    return complex(np.sum(pat * f * w))


