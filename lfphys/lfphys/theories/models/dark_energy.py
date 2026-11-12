# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Dark energy with a time-varying equation of state, w(a) = w0 + wa (1 - a) (Chevallier & Polarski 2001, Eqs.
(30)-(31); Linder 2003, Eqs. (6)-(7); Planck 2018 Eq. (49)), as a component of the core's FLRW background.

The equation of state is a parametrisation, not a law: two fitted constants describe an unknown component. General
relativity then fixes its density through the continuity equation d ln rho / d ln a = -3 (1 + w(a)):

    rho(a) / rho(1) = a^(-3 (1 + w0 + wa)) exp(-3 wa (1 - a))       (Linder 2003, after Eq. (7)).

wa = 0 is a constant w ("wCDM"); w0 = -1, wa = 0 is the cosmological constant of the core (the background is then
identical to the core's Lambda universe; tests). Only the homogeneous background is modelled (no perturbations; for
w crossing -1 Planck uses the PPF description of the perturbations, Sect. 7.4.1).
"""

from __future__ import annotations

import numpy as np

from lfphys.i18n import T

from ...core.cosmology import flrw

ABOUT = {
    "layer": "theories", "kind": "model",
    "title": T("Dark energy with the w0–wa equation of state (CPL)"),
    "statement": T("A component with w(a) = w0 + wa(1 − a) and the density ρ(a)/ρ(1) = a^(−3(1+w0+wa)) exp(−3wa(1 − "
                   "a)) from the continuity equation of GR; it plugs into the core's FLRW background "
                   "(core.cosmology.flrw) in place of Λ; wa = 0 is a constant w, (w0, wa) = (−1, 0) the cosmological "
                   "constant."),
    "validity": T("homogeneous background only; a parametrisation with two fitted constants, not a law; at w < −1 "
                  "(phantom) it is not described by one canonical scalar field"),
    "basis": ["Chevallier & Polarski, Int. J. Mod. Phys. D 10, 213 (2001), Eqs. (30)-(31)",
              "Linder, Phys. Rev. Lett. 90, 091301 (2003), Eqs. (6)-(7)",
              "Planck Collaboration, A&A 641, A6 (2020), Sect. 7.4.1, Eq. (49)",
              "DESI Collaboration, Phys. Rev. D 112, 083515 (2025) (DR2 BAO), abstract"],
    "conflicts": [T("lfphys.core.cosmology.flrw: the core holds ΛCDM (w = −1, constant density); w0–wa is a "
                    "phenomenological extension beyond ΛCDM. The data disagree: Planck 2018 with BAO and supernovae "
                    "is consistent with Λ (w0 = −1.028 ± 0.031 at wa = 0), DESI DR2 BAO + CMB prefers w0 > −1, wa < "
                    "0 at 3.1σ (2.8–4.2σ with supernovae): the question is open")],
}


class CPL:
    """w(a) = w0 + wa (1 - a). ``density_ratio(a)`` = rho(a)/rho(1) and its logarithm ``log_density_ratio(a)``
    (which the core uses, so that a phantom's growth or a fast decay at a ~ 1e300 does not overflow; review B7-flrw
    C1); all vectorised and defined at a = 0 (w(0) = w0 + wa), as the core's ``Background(dark_energy=...)``
    expects."""

    def __init__(self, w0: float = -1.0, wa: float = 0.0):
        self.w0, self.wa = float(w0), float(wa)

    def w(self, a):
        return self.w0 + self.wa * (1.0 - np.asarray(a, float))

    def density_ratio(self, a):
        a = np.asarray(a, float)
        with np.errstate(divide="ignore", over="ignore"):
            return a ** (-3.0 * (1.0 + self.w0 + self.wa)) * np.exp(-3.0 * self.wa * (1.0 - a))

    def log_density_ratio(self, a):
        """ln(rho(a)/rho(1)) = -3 (1 + w0 + wa) ln a - 3 wa (1 - a)."""
        a = np.asarray(a, float)
        c = -3.0 * (1.0 + self.w0 + self.wa)
        with np.errstate(divide="ignore"):
            return (c * np.log(a) if c != 0 else np.zeros_like(a)) - 3.0 * self.wa * (1.0 - a)

    def __repr__(self):
        return f"CPL(w0={self.w0!r}, wa={self.wa!r})"


def background(H0, Om, w0=-1.0, wa=0.0, **kw) -> flrw.Background:
    """An FLRW background whose dark energy follows CPL(w0, wa); the other arguments as ``flrw.Background`` (``OL``
    is then this component's density parameter today)."""
    return flrw.Background(H0, Om, dark_energy=CPL(w0, wa), **kw)
