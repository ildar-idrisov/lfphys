# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Physical constants and nominal astronomical values (one source for the whole visualization).

Fundamental constants: ``scipy.constants``, CODATA 2022 (scipy >= 1.15; earlier versions ship CODATA 2018,
~1e-9 different; tests/test_experimental_bounds.py asserts the edition). c is exact in the SI.
Astronomical values:
* astronomical unit: exact by IAU 2012 Resolution B2 (149 597 870 700 m), as ``scipy.constants.au``;
* nominal solar and terrestrial values: IAU 2015 Resolution B3 (nominal conversion constants):
  (GM)_sun = 1.3271244e20 m^3 s^-2, R_sun = 6.957e8 m, (GM)_earth = 3.986004e14 m^3 s^-2,
  R_earth (equatorial) = 6.3781e6 m.
"""

from scipy import constants as sc

ABOUT = {
    "layer": "core", "kind": "data",
    "title": "Физические постоянные",
    "statement": "Фундаментальные постоянные CODATA (scipy.constants) и номинальные астрономические значения МАС.",
    "validity": "значения CODATA, поставляемые закреплённой версией scipy; МАС 2012 B2, МАС 2015 B3",
    "basis": ["CODATA (scipy.constants)", "IAU 2012 Resolution B2", "IAU 2015 Resolution B3"],
    "conflicts": [],
}

C = sc.c  # 299 792 458 m/s, exact
G = sc.G
AU = sc.au
LIGHT_YEAR = sc.light_year
DAY = 86400.0
YEAR_JULIAN = 365.25 * DAY

GM_SUN = 1.3271244e20
R_SUN = 6.957e8
GM_EARTH = 3.986004e14
R_EARTH = 6.3781e6
M_SUN = GM_SUN / G
