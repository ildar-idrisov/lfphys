# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Rotating black hole (Kerr): closed forms for the equatorial plane.

Units: G = c = 1, lengths in M, spin chi = a/M in [0, 1]. Upper sign (prograde, co-rotating) / lower (retrograde):

* horizons r_pm = 1 pm sqrt(1 - chi^2); ergosphere r_E(theta) = 1 + sqrt(1 - chi^2 cos^2 theta);
* circular photon orbit  r_ph = 2 [1 + cos(2/3 arccos(-+ chi))];
* marginally bound orbit r_mb = 2 -+ chi + 2 sqrt(1 -+ chi);
* innermost stable circular orbit (Bardeen, Press & Teukolsky 1972):
      Z1 = 1 + (1 - chi^2)^(1/3) [(1 + chi)^(1/3) + (1 - chi)^(1/3)],  Z2 = sqrt(3 chi^2 + Z1^2),
      r_isco = 3 + Z2 -+ sqrt((3 - Z1)(3 + Z1 + 2 Z2));
* energy and angular momentum per unit mass of a circular orbit:
      e = (r^{3/2} - 2 r^{1/2} pm chi) / (r^{3/4} sqrt(r^{3/2} - 3 r^{1/2} pm 2 chi)),
      l = pm (r^2 -+ 2 chi r^{1/2} + chi^2) / (r^{3/4} sqrt(r^{3/2} - 3 r^{1/2} pm 2 chi)).

The tests check every closed form against the equatorial radial potential
R(r) = [e (r^2 + chi^2) - chi l]^2 - Delta [r^2 + (l - chi e)^2], Delta = r^2 - 2r + chi^2
(circular: R = R' = 0; ISCO: also R'' = 0), an independent route.
"""

from __future__ import annotations

import math

from lfphys.i18n import T
from lfphys.codes import coded

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Rotating black hole (Kerr): equatorial orbits"),
    "statement": T("Horizons, ergosphere, circular photon orbit, marginally bound orbit, ISCO "
                   "(Bardeen–Press–Teukolsky), energy and angular momentum of circular orbits; accretion efficiency 1 "
                   "− e_ISCO."),
    "validity": T("vacuum solution of GR, |a| ≤ M; equatorial plane"),
    "basis": ["Kerr, PRL 11, 237 (1963)", "Bardeen, Press, Teukolsky, ApJ 178, 347 (1972)",
              T("the shadows of M87* and Sgr A* (EHT 2019, 2022) agree with Kerr")],
    "conflicts": [],
}


def _chk(chi):
    if not 0.0 <= chi <= 1.0:
        raise coded(ValueError(T("the spin χ = a/M must be in [0, 1]")), "kerr.spin")


def horizons(chi: float) -> tuple[float, float]:
    _chk(chi)
    s = math.sqrt(1.0 - chi * chi)
    return 1.0 + s, 1.0 - s


def ergosphere(chi: float, theta: float) -> float:
    _chk(chi)
    return 1.0 + math.sqrt(1.0 - (chi * math.cos(theta)) ** 2)


def photon_orbit(chi: float, prograde: bool = True) -> float:
    _chk(chi)
    return 2.0 * (1.0 + math.cos(2.0 / 3.0 * math.acos(-chi if prograde else chi)))


def marginally_bound(chi: float, prograde: bool = True) -> float:
    _chk(chi)
    s = 1.0 if prograde else -1.0
    return 2.0 - s * chi + 2.0 * math.sqrt(1.0 - s * chi)


def isco(chi: float, prograde: bool = True) -> float:
    _chk(chi)
    z1 = 1.0 + (1.0 - chi * chi) ** (1.0 / 3.0) * ((1.0 + chi) ** (1.0 / 3.0) + (1.0 - chi) ** (1.0 / 3.0))
    z2 = math.sqrt(3.0 * chi * chi + z1 * z1)
    s = 1.0 if prograde else -1.0
    return 3.0 + z2 - s * math.sqrt((3.0 - z1) * (3.0 + z1 + 2.0 * z2))


def circular_e_l(r: float, chi: float, prograde: bool = True) -> tuple[float, float]:
    _chk(chi)
    s = 1.0 if prograde else -1.0
    sr = math.sqrt(r)
    den = r ** 0.75 * math.sqrt(r * sr - 3.0 * sr + s * 2.0 * chi)
    e = (r * sr - 2.0 * sr + s * chi) / den
    l = s * (r * r - s * 2.0 * chi * sr + chi * chi) / den
    return e, l


def efficiency(chi: float, prograde: bool = True) -> float:
    """Radiative efficiency of thin-disc accretion: 1 - e(r_isco)."""
    return 1.0 - circular_e_l(isco(chi, prograde), chi, prograde)[0]


def radial_potential(r: float, e: float, l: float, chi: float) -> float:
    """R(r) for equatorial geodesics (r^4 (dr/dtau)^2 = R)."""
    delta = r * r - 2.0 * r + chi * chi
    return (e * (r * r + chi * chi) - chi * l) ** 2 - delta * (r * r + (l - chi * e) ** 2)
