# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Hydrogen-like atoms: bound-state energies and wave functions.

* Schroedinger with the reduced mass mu = m_e M / (m_e + M):  E_n = -mu c^2 (Z alpha)^2 / (2 n^2);
* Dirac (point nucleus) with the leading recoil correction (Barker-Glover; Eides, Grotch & Shelyuto, Phys. Rep. 342,
  63 (2001), Eq. 2.5):  E_nj = mu c^2 (f - 1) - mu^2 c^2 (f - 1)^2 / (2 (m + M)),
  f = [1 + (Z alpha / (n - delta_j))^2]^(-1/2), delta_j = j + 1/2 - sqrt((j + 1/2)^2 - (Z alpha)^2): fine structure
  (levels depend on n and j only). M = inf gives the infinite-mass Dirac level m c^2 (f - 1).

Wave functions (plan P14.5): R_nl(r) = N_nl e^{-rho/2} rho^l L^{2l+1}_{n-l-1}(rho), rho = 2 Z r / (n a),
N_nl = sqrt((2Z/(n a))^3 (n-l-1)! / (2n (n+l)!)), a = hbar / (mu c alpha) the Bohr radius of the reduced mass;
psi_nlm = R_nl Y_lm (``lfphys.core.quantum.central3d``). The Laguerre polynomial is built by its three-term
recurrence and the whole product in logarithms (no overflow for large n); an independent route is the explicit
power series with exact binomial coefficients (``radial_series``, with its own round-off bound). Closed-form
moments <r^k> (k = -2, -1, 1, 2), energies of any reduced mass (``level``), the dipole matrix element
<1s|z|2p0> = 2^7 sqrt 2 / 3^5 a (Bethe & Salpeter) for tests.

Not included: the Lamb shift and hyperfine structure (QED and nuclear effects; 2S1/2 - 2P1/2 = 1057.8 MHz in
hydrogen) and the nuclear size. Accuracy against the measured hydrogen 1S-2S frequency (Parthey et al., PRL 107,
203001 (2011): 2 466 061 413 187 035 (10) Hz, hyperfine centroid): ``dirac_level`` with the proton mass +2.9e-6 (the
1S and 2S Lamb shifts); ``schrodinger_level`` -9.3e-6 (no fine structure); the infinite-mass Dirac level +5.5e-4
(m_e/m_p). Review of 2026-10-23, E1.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import constants as sc

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Hydrogen-like atom: Schrödinger and Dirac levels, wave functions"),
    "statement": T("Levels with the reduced mass (Schrödinger) and the fine structure (the exact Dirac formula with "
                   "the Barker–Glover nuclear recoil correction); exact wave functions R_nl·Y_lm (Laguerre "
                   "polynomials, any n), moments ⟨r^k⟩ in closed form."),
    "validity": T("no Lamb shift and no hyperfine structure (QED, the nucleus). The hydrogen 1S–2S frequency against "
                  "the measurement: Dirac with recoil +2.9·10⁻⁶ (this is the Lamb shift), Schrödinger −9.3·10⁻⁶ (no "
                  "fine structure)"),
    "basis": ["Dirac, Proc. R. Soc. A 117, 610 (1928)", "Sommerfeld 1916",
              "Barker & Glover, Phys. Rev. 99, 317 (1955); Eides, Grotch, Shelyuto, Phys. Rep. 342, 63 (2001), Eq. 2.5",
              T("Parthey et al., PRL 107, 203001 (2011): the 1S–2S frequency"), T("CODATA (α, masses)"),
              "Bethe & Salpeter, Quantum Mechanics of One- and Two-Electron Atoms (1957): R_nl, ⟨r^k⟩"],
    "conflicts": [],
}

ALPHA = sc.fine_structure
ME_C2 = sc.m_e * sc.c**2


def schrodinger_level(n: int, Z: int = 1, M: float = sc.m_p) -> float:
    mu = sc.m_e * M / (sc.m_e + M)
    return -mu * sc.c**2 * (Z * ALPHA) ** 2 / (2 * n * n)


def dirac_level(n: int, j: float, Z: int = 1, M: float = sc.m_p) -> float:
    """Binding energy (J) of level (n, j) with the leading recoil correction for a nucleus of mass M (kg); M = math.inf
    gives the infinite-mass Dirac level. j = 1/2 ... n - 1/2."""
    if not (n >= 1 and 0.5 <= j <= n - 0.5 and (j - 0.5) == int(j - 0.5)):
        raise ValueError(f"dirac_level: need n >= 1 and j in 1/2 ... n - 1/2 (got n = {n}, j = {j})")
    za = Z * ALPHA
    delta = j + 0.5 - math.sqrt((j + 0.5) ** 2 - za * za)
    x = (za / (n - delta)) ** 2
    fm1 = -x / (math.sqrt(1.0 + x) * (1.0 + math.sqrt(1.0 + x)))  # f - 1 without cancellation
    if math.isinf(M):
        return ME_C2 * fm1
    mu = sc.m_e * M / (sc.m_e + M)
    return mu * sc.c**2 * fm1 - (mu * sc.c) ** 2 * fm1 * fm1 / (2 * (sc.m_e + M))


def frequency(E1: float, E2: float) -> float:
    return abs(E2 - E1) / sc.h


# --- wave functions (plan P14.5) -------------------------------------------------------------------------------------
def bohr_radius(mu: float) -> float:
    """a = hbar / (mu c alpha) in metres (reduced mass mu in kg)."""
    return sc.hbar / (mu * sc.c * ALPHA)


def hartree(mu: float) -> float:
    """E_h = mu c^2 alpha^2 in joules: the energy unit in which E_n = -Z^2 / (2 n^2)."""
    return mu * sc.c**2 * ALPHA**2


def reduced_mass(m1: float, m2: float) -> float:
    return m1 * m2 / (m1 + m2) if math.isfinite(m2) else m1


def level(n: int, Z: int = 1, mu: float = sc.m_e) -> float:
    """E_n = -mu c^2 (Z alpha)^2 / (2 n^2) in joules for any reduced mass (``schrodinger_level`` for an electron)."""
    return -hartree(mu) * Z * Z / (2.0 * n * n)


def _check_nl(n, l):
    if not (n >= 1 and 0 <= l < n):
        raise ValueError(T("need n ≥ 1 and 0 ≤ l < n (n = {n}, l = {l})", n=float(n), l=float(l)))


def radial(n: int, l: int, r, Z: float = 1.0, a: float = 1.0):
    """R_nl(r) (units a^(-3/2)): the generalised Laguerre polynomial by its recurrence
    (k+1) L_{k+1} = (2k + 1 + alpha - rho) L_k - (k + alpha) L_{k-1}, kept as mantissa and exponent (rescaled when
    large), and the product N e^{-rho/2} rho^l L formed in logarithms: no overflow or underflow for any n."""
    _check_nl(n, l)
    r = np.asarray(r, float)
    rho = 2.0 * Z * r / (n * a)
    k, alpha = n - l - 1, 2 * l + 1
    Lm, L = np.zeros_like(rho), np.ones_like(rho)
    expo = np.zeros_like(rho)  # L = mantissa * e^expo
    if k >= 1:
        Lm, L = L, 1.0 + alpha - rho
        for j in range(1, k):
            Lm, L = L, ((2 * j + 1 + alpha - rho) * L - (j + alpha) * Lm) / (j + 1)
            big = np.abs(L) > 1e150
            if np.any(big):
                L = np.where(big, L * 1e-150, L)
                Lm = np.where(big, Lm * 1e-150, Lm)
                expo = expo + np.where(big, 150 * math.log(10.0), 0.0)
    lognorm = 0.5 * (3 * math.log(2.0 * Z / (n * a)) + math.lgamma(n - l) - math.log(2.0 * n) - math.lgamma(n + l + 1))
    lterm = l * np.log(np.where(rho > 0, rho, 1.0)) if l > 0 else 0.0
    absL = np.abs(L)
    val = np.exp(lognorm - 0.5 * rho + lterm + expo + np.log(np.where(absL > 0, absL, 1.0)))
    return np.where((absL > 0) & ((rho > 0) | (l == 0)), np.sign(L) * val, 0.0)


def radial_series(n: int, l: int, r, Z: float = 1.0, a: float = 1.0):
    """The same R_nl by the explicit series L^alpha_k(rho) = sum_j (-1)^j C(k + alpha, k - j) rho^j / j! (exact
    integer coefficients): an independent route. Returns (R, bound), bound = 64 eps N e^{-rho/2} rho^l sum_j |term_j|,
    a bound on its round-off (the series cancels for large rho and k)."""
    _check_nl(n, l)
    r = np.asarray(r, float)
    rho = 2.0 * Z * r / (n * a)
    k, alpha = n - l - 1, 2 * l + 1
    tot, mag = np.zeros_like(rho), np.zeros_like(rho)
    for j in range(k + 1):
        term = (-1) ** j * math.comb(k + alpha, k - j) / math.factorial(j) * rho**j
        tot = tot + term
        mag = mag + np.abs(term)
    norm = math.sqrt((2.0 * Z / (n * a)) ** 3 * math.factorial(n - l - 1) / (2.0 * n * math.factorial(n + l)))
    pref = norm * np.exp(-0.5 * rho) * rho**l
    return pref * tot, 64 * np.finfo(float).eps * pref * mag


def expectation(n: int, l: int, k: int, Z: float = 1.0, a: float = 1.0) -> float:
    """<r^k> in closed form (Bethe & Salpeter, eq. 3.24-3.26): k = 1: a/(2Z) (3n^2 - l(l+1)); k = 2: a^2 n^2/(2Z^2)
    (5n^2 + 1 - 3l(l+1)); k = -1: Z/(a n^2); k = -2: Z^2/(a^2 n^3 (l + 1/2))."""
    _check_nl(n, l)
    if k == 1:
        return a / (2.0 * Z) * (3 * n * n - l * (l + 1))
    if k == 2:
        return a * a * n * n / (2.0 * Z * Z) * (5 * n * n + 1 - 3 * l * (l + 1))
    if k == -1:
        return Z / (a * n * n)
    if k == -2:
        return Z * Z / (a * a * n**3 * (l + 0.5))
    raise ValueError(T("closed forms exist only for k = −2, −1, 1, 2"))


def orbital(n: int, l: int, m: int, Z: float = 1.0, a: float = 1.0, real: bool = False):
    """psi_nlm as a ``central3d.Orbital`` (energy -Z^2/(2n^2) in units of the reduced-mass Hartree, a = 1)."""
    from .central3d import Orbital, orbital_name
    _check_nl(n, l)
    if abs(m) > l:
        raise ValueError(T("need |m| ≤ l (m = {m}, l = {l})", m=float(m), l=float(l)))
    return Orbital(lambda r: radial(n, l, r, Z, a), l, m, real, -Z * Z / (2.0 * n * n),
                   f"{n}{orbital_name(l, m, real)}")


DIPOLE_1S_2P0 = 2**7 * math.sqrt(2.0) / 3**5  # <100|z|210> in units of a (Bethe & Salpeter): 0.7449...
