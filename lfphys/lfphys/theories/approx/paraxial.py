# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Paraxial (Fresnel) wave behind the slits, in closed form.

The stationary wave of every particle species satisfies the Helmholtz equation in free space (Schroedinger,
Klein-Gordon and Maxwell alike) with k = p / hbar. In the paraxial regime the field at distance z behind the slit
plane is the Fresnel integral of the field in the slits (Kirchhoff boundary values: the incident wave inside a
slit, zero on the screen). For slit j = [e1, e2], a point source at transverse position x_s and distance L1
(L1 = inf: plane wave at incidence angle theta) and a transverse momentum kick kappa (from a scattered photon):

    A_j(x; z) = int_{e1}^{e2} exp(i [alpha x'^2 + beta x' + gamma0]) dx',
    alpha = k/2 (1/z + 1/L1),  beta = beta_src - k x / z + kappa,  gamma0 = k x_s^2/(2 L1) + k x^2/(2 z),
    beta_src = -k x_s / L1   (or k sin(theta) for a plane wave),

    A_j = exp(i Gamma) sqrt(pi/(2 alpha)) [ (C(u2) - C(u1)) + i (S(u2) - S(u1)) ],
    u = sqrt(2 alpha/pi) (e - x0),  x0 = -beta/(2 alpha),  Gamma = gamma0 - beta^2/(4 alpha)

with the Fresnel integrals C, S (scipy.special.fresnel). The x-derivative (for the probability current /
Bohmian velocity) is closed-form too:

    dA_j/dx = i (k/z) [ (x - x0) A_j - exp(i Gamma) (E2 - E1) / (2 i alpha) ],  E = exp(i alpha (e - x0)^2).

A common factor sqrt(k / (2 pi i z)) is omitted: it is the same for all slits and drops out of normalised
distributions; it does not depend on x, so it does not enter velocities either.
The paraxial result is compared with the exact propagation of the same boundary values (kirchhoff.py).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

from lfphys.i18n import T

ABOUT = {
    "layer": 'theories', "kind": 'approximation',
    "title": T("Paraxial (Fresnel) diffraction by slits"),
    "statement": T("The field behind the slits is the Fresnel integral of the field in the slits (Kirchhoff's "
                   "boundary conditions), in closed form through the Fresnel integrals; the x derivative for the "
                   "probability current."),
    "validity": T("z ≫ (x − x′)⁴ k / 8 (paraxiality) and slits wider than ~10 λ (Kirchhoff); the accuracy is checked "
                  "against exact propagation (kirchhoff.py)"),
    "basis": [T("Born & Wolf, Principles of Optics, ch. 8")],
    "conflicts": [T("lfphys.core.optics.scalar: exact propagation differs at large angles and near the slits")],
}


def slit_amplitudes(x, z, k, slits, a, L1=math.inf, src=0.0, kappa=0.0, deriv=False):
    """x: (..., Nx) points; z: scalar or broadcastable to x[..., :1]; k, src, kappa: broadcastable likewise.
    slits: (n,) centres; a: width. Returns A (..., n, Nx) [and dA/dx]."""
    x = np.asarray(x, float)
    z = np.asarray(z, float)
    k = np.asarray(k, float)
    src = np.asarray(src, float)
    kappa = np.asarray(kappa, float)
    if math.isinf(L1):
        alpha = 0.5 * k / z
        beta_src = k * np.sin(src)  # src = incidence angle
    else:
        alpha = 0.5 * k * (1.0 / z + 1.0 / L1)
        beta_src = -k * src / L1
    beta = beta_src - k * x / z + kappa
    x0 = -beta / (2.0 * alpha)
    # Gamma = gamma0 - beta^2/(4 alpha) cancels two large terms; the algebraically equal stable form is used
    Gam = _stable_gamma(x, z, k, L1, src, kappa)
    s = np.sqrt(2.0 * alpha / math.pi)
    pref = np.sqrt(math.pi / (2.0 * alpha)) * np.exp(1j * Gam)
    A = []
    dA = []
    for c in np.asarray(slits, float):
        e1, e2 = c - 0.5 * a, c + 0.5 * a
        S1, C1 = special.fresnel(s * (e1 - x0))
        S2, C2 = special.fresnel(s * (e2 - x0))
        Aj = pref * ((C2 - C1) + 1j * (S2 - S1))
        A.append(Aj)
        if deriv:
            E1 = np.exp(1j * alpha * (e1 - x0) ** 2)
            E2 = np.exp(1j * alpha * (e2 - x0) ** 2)
            dA.append(1j * (k / z) * ((x - x0) * Aj - np.exp(1j * Gam) * (E2 - E1) / (2j * alpha)))
    A = np.stack(A, axis=-2)
    if deriv:
        return A, np.stack(dA, axis=-2)
    return A


def _stable_gamma(x, z, k, L1, src, kappa):
    """Gamma = gamma0 - beta^2/(4 alpha), written without the cancellation of two large terms.
    Plane wave (L1 = inf), b0 = k sin(theta) + kappa:  Gamma = (b0 x) - b0^2 z/(2k)  [exact].
    Point source: alpha = k (L1 + z)/(2 z L1); with q = (-k x_s/L1 + kappa), beta = q - k x/z:
        Gamma = k x_s^2/(2 L1) + k x^2/(2 z) - (q - k x/z)^2 z L1/(2 k (L1 + z))."""
    if math.isinf(L1):
        b0 = k * np.sin(src) + kappa
        return b0 * x - b0**2 * z / (2.0 * k)
    q = -k * src / L1 + kappa
    D = L1 + z
    # expand and collect: k x^2/(2z) [1 - L1/D] = k x^2 / (2 D);  cross term: q x L1 / D;  rest: -q^2 z L1/(2kD)
    return k * src**2 / (2.0 * L1) + k * x**2 / (2.0 * D) + q * x * L1 / D - q**2 * z * L1 / (2.0 * k * D)


def intensity(A, G):
    """P(x) = sum_jl A_j A_l^* G_jl  for A (..., n, Nx), G (n, n) -> (..., Nx) real."""
    return np.einsum("...jx,...lx,jl->...x", A, A.conj(), G).real


def current(A, dA, G):
    """Im(Psi^dagger dPsi) = Im sum_jl A_l^* dA_j G_jl  and |Psi|^2."""
    num = np.einsum("...jx,...lx,jl->...x", dA, A.conj(), G).imag
    den = np.einsum("...jx,...lx,jl->...x", A, A.conj(), G).real
    return num, den
