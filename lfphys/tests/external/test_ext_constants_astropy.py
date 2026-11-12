# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The engine's constants against Astropy (plan item P13): ``lfphys.core.constants`` and the constants the engine's
modules take from ``scipy.constants`` (``core.quantum.particles``, ``hydrogen``, ``compton``, ``core.optics.radiation``)
against ``astropy.constants`` / ``astropy.units``.

Editions. The engine: CODATA 2022 through scipy.constants (scipy >= 1.15; tests/test_experimental_bounds.py asserts
the edition), the astronomical unit of IAU 2012 Resolution B2, the nominal solar and terrestrial values of IAU 2015
Resolution B3. Astropy 8.0.2: science state ``physical_constants`` = codata2022 and ``astronomical_constants`` =
iau2015 by default (asserted below). Both sides therefore carry the same decimal values.

Tolerances (derived, no allowance for a difference of editions):
* "same decimal": a value that both sides parse from the same published decimal string (c, G, h, e, k_B, m_e, ...,
  GM_sun, R_sun, au) is the same binary64 number: tolerance 0.
* "n roundings": a value that each side computes from such numbers with n correctly rounded operations (hbar = h/(2 pi),
  M_sun = GM_sun/G, m_e c^2, h/(m_e c)) differs from the exact value of the same expression by at most gamma_n |x| on
  each side: tolerance 2 gamma_n |x|.
A difference between CODATA editions is about 1e-10 relative for m_e, alpha, m_p (test_edition_shift_is_detected), far
above these tolerances, so an edition mismatch on either side fails here instead of being absorbed.
``lfphys.core.data`` holds PDG, NASA and experiment values (alpha_s(M_Z), quark and quarkonium masses, Mercury's orbit,
tests of GR); Astropy has none of them, so it is not compared (README.md).
"""

from __future__ import annotations

import functools

import astropy
import astropy.constants as ac
import astropy.units as u
import pytest
from astropy import astronomical_constants, physical_constants
from scipy import constants as sc

from lfphys.core import constants as lc
from lfphys.core.optics import radiation
from lfphys.core.quantum import compton, hydrogen, particles

from _common import Row, check, gamma, params

GROUP = "constants (astropy)"


@functools.lru_cache(maxsize=None)
def rows() -> list[Row]:
    out = []

    def same(name, eng, lib):
        out.append(Row(GROUP, name, "SI", float(eng), float(lib), 0.0, "same decimal"))

    def derived(name, eng, lib, n):
        out.append(Row(GROUP, name, "SI", float(eng), float(lib), 2 * gamma(n) * abs(float(lib)), f"{n} roundings"))

    si = lambda q: q.si.value  # noqa: E731
    # lfphys.core.constants
    same("constants.C", lc.C, si(ac.c))
    same("constants.G", lc.G, si(ac.G))
    same("constants.AU", lc.AU, si(ac.au))
    same("constants.DAY", lc.DAY, (1 * u.day).to_value(u.s))
    same("constants.YEAR_JULIAN", lc.YEAR_JULIAN, (1 * u.yr).to_value(u.s))
    derived("constants.LIGHT_YEAR", lc.LIGHT_YEAR, (1 * u.lyr).to_value(u.m), 2)
    same("constants.GM_SUN", lc.GM_SUN, si(ac.GM_sun))
    same("constants.R_SUN", lc.R_SUN, si(ac.R_sun))
    same("constants.GM_EARTH", lc.GM_EARTH, si(ac.GM_earth))
    same("constants.R_EARTH", lc.R_EARTH, si(ac.R_earth))
    derived("constants.M_SUN = GM_SUN/G", lc.M_SUN, si(ac.M_sun), 1)
    # constants the engine's modules take from scipy.constants
    same("particles.H", particles.H, si(ac.h))
    derived("particles.HBAR = h/(2 pi)", particles.HBAR, si(ac.hbar), 1)
    same("particles.C", particles.C, si(ac.c))
    same("particles.E_CHARGE", particles.E_CHARGE, si(ac.e))
    same("particles.EV", particles.EV, (1 * u.eV).to_value(u.J))
    same("particles.U (atomic mass constant)", particles.U, si(ac.u))
    same("particles: m_e", particles.SPECIES["electron"][1], si(ac.m_e))
    same("particles: m_n", particles.SPECIES["neutron"][1], si(ac.m_n))
    same("hydrogen: m_p (default nucleus)", sc.m_p, si(ac.m_p))
    same("hydrogen.ALPHA", hydrogen.ALPHA, si(ac.alpha))
    derived("hydrogen.ME_C2 = m_e c^2", hydrogen.ME_C2, si(ac.m_e * ac.c ** 2), 2)
    derived("compton.LAMBDA_C = h/(m_e c)", compton.LAMBDA_C, si(ac.h / (ac.m_e * ac.c)), 2)
    same("radiation.H", radiation.H, si(ac.h))
    same("radiation.K (Boltzmann)", radiation.K, si(ac.k_B))
    return out


@pytest.mark.parametrize("row", params(rows()))
def test_constant(row):
    check(row)


def test_editions():
    """Which editions the two sides use (stated in RESULTS.md): Astropy's defaults and scipy's CODATA 2022 values."""
    assert physical_constants.get() == "codata2022" and astronomical_constants.get() == "iau2015", (
        physical_constants.get(), astronomical_constants.get())
    assert "CODATA 2022" in ac.m_e.reference and "IAU 2015" in ac.GM_sun.reference
    # CODATA 2022 values (scipy >= 1.15): m_e = 9.1093837139(28)e-31 kg, alpha^-1 = 137.035999177(21)
    assert sc.m_e == 9.1093837139e-31 and sc.physical_constants["inverse fine-structure constant"][0] == 137.035999177


def test_edition_shift_is_detected():
    """CODATA 2018 and 2022 differ by ~1e-10 relative in m_e and alpha: an edition change on either side would fail
    the rows above (tolerance 0 or a few ulp), it is not absorbed."""
    from astropy.constants import codata2018
    for name in ("m_e", "alpha", "m_p"):
        new, old = getattr(ac, name).si.value, getattr(codata2018, name).si.value
        assert abs(new / old - 1) > 1e3 * gamma(2), name


def edition_notes() -> list[str]:
    """Lines for RESULTS.md: versions and editions of both sides."""
    from astropy.constants import codata2018
    shifts = []
    for name in ("m_e", "m_p", "alpha", "u", "G"):
        new, old = getattr(ac, name), getattr(codata2018, name)
        shifts.append(f"{name}: {(new.si.value / old.si.value - 1):+.2e} relative "
                      f"({(new.si.value - old.si.value) / new.si.uncertainty if new.si.uncertainty else 0:+.2f} "
                      f"standard uncertainties of 2022)" if new.si.uncertainty else
                      f"{name}: {(new.si.value / old.si.value - 1):+.2e} relative")
    return [f"engine: CODATA 2022 via scipy {__import__('scipy').__version__}, IAU 2012 B2 (au), IAU 2015 B3 (nominal "
            f"solar and terrestrial values)",
            f"astropy {astropy.__version__}: physical_constants = {physical_constants.get()}, "
            f"astronomical_constants = {astronomical_constants.get()}",
            "CODATA 2018 -> 2022 shifts (astropy.constants.codata2018 vs codata2022), for scale: " + "; ".join(shifts)]
