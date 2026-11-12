"""01: which CODATA edition the pinned scipy ships, and the constants/nominal values of lfphys.core.constants.

Reference values typed from CODATA 2022 (Mohr, Tiesinga, Newell, Taylor; NIST SP 961 / physics.nist.gov/cuu, 2024
release) and CODATA 2018 for comparison; IAU 2015 Resolution B3 nominal values. Usage: python3 01_constants.py
"""
import argparse
import sys

argparse.ArgumentParser(description=__doc__).parse_args()

import numpy as np
import scipy
from scipy import constants as sc

from lfphys.core import constants as K

print("python", sys.version.split()[0], "numpy", np.__version__, "scipy", scipy.__version__)
try:
    import flint, mpmath
    print("python-flint", flint.__version__, "mpmath", mpmath.__version__)
except Exception as e:  # noqa: BLE001
    print("flint/mpmath:", e)

# (name in scipy, CODATA 2018, CODATA 2022)
ref = [
    ("fine-structure constant", 7.2973525693e-3, 7.2973525643e-3),
    ("electron mass", 9.1093837015e-31, 9.1093837139e-31),
    ("proton mass", 1.67262192369e-27, 1.67262192595e-27),
    ("neutron mass", 1.67492749804e-27, 1.67492750056e-27),
    ("atomic mass constant", 1.66053906660e-27, 1.66053906892e-27),
    ("classical electron radius", 2.8179403262e-15, 2.8179403205e-15),
    ("Rydberg constant", 10973731.568160, 10973731.568157),
    ("Newtonian constant of gravitation", 6.67430e-11, 6.67430e-11),
    ("Thomson cross section", 6.6524587321e-29, 6.6524587051e-29),
]
print("\nconstant | scipy | rel. diff vs CODATA 2018 | rel. diff vs CODATA 2022")
for name, v18, v22 in ref:
    v = sc.physical_constants[name][0]
    print(f"{name:36s} {v:.12e}  {abs(v / v18 - 1):.2e}  {abs(v / v22 - 1):.2e}")

print("\nlfphys.core.constants:")
for n in ("C", "G", "AU", "GM_SUN", "R_SUN", "GM_EARTH", "R_EARTH", "M_SUN", "LIGHT_YEAR", "YEAR_JULIAN"):
    print(f"  {n:12s} {getattr(K, n)!r}")
iau = {"GM_SUN": 1.3271244e20, "R_SUN": 6.957e8, "GM_EARTH": 3.986004e14, "R_EARTH": 6.3781e6}
for n, v in iau.items():
    assert getattr(K, n) == v, n
print("IAU 2015 B3 nominal values: match")
print("AU exact (IAU 2012 B2):", K.AU == 149597870700.0)
