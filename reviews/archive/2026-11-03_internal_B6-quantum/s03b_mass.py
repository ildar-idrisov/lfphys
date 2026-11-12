"""Debug of s03: the species mass from species("atom", mass_u = m_e/u) and the packet's mean position."""
import math
import numpy as np
from lfphys.core.quantum import scene as QS, particles as PT
UNITS = QS.Units(1e-9, 9.1093837139e-31)
el = QS.species("atom", UNITS, mass_u=UNITS.mass / 1.66053906892e-27)
print("mass", repr(el.mass), "PT.U", PT.U)
import scipy.constants as sc
el2 = QS.species("atom", UNITS, mass_u=sc.m_e / sc.atomic_mass)
print("mass with scipy's u:", repr(el2.mass), sc.atomic_mass)
