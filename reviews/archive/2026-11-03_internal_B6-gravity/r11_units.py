# Reviewer script (B6 gravity): the playground's Newtonian unit constants (p01_gravity.viz) against their comments and
# the engine's constants; the Kerr and PN time and length units.
import math

from lfphys.core import constants as K
from p01_gravity import viz as V

print(f"G_AU = {V.G_AU!r} au^3/(Msun yr^2); 4 pi^2 = {4 * math.pi ** 2!r}; G_AU/(4 pi^2) - 1 = {V.G_AU / (4 * math.pi ** 2) - 1:.3e}"
      " (comment: 'to 6e-6')")
k = 0.01720209895  # Gauss's constant, rad/day
print(f"  check: k^2 * 365.25^2 = {k * k * 365.25 ** 2!r} (GM_sun in au^3/yr^2 with the IAU 2012 au and the Julian year, "
      f"to the 1e-10 by which k differs from today's GM_sun): ratio to 4 pi^2 - 1 = {k * k * 365.25 ** 2 / (4 * math.pi ** 2) - 1:.3e};"
      f" (Julian / Gaussian year)^2 - 1 = {(365.25 / (2 * math.pi / k)) ** 2 - 1:.3e}")
print(f"M_EARTH_SUN = {V.M_EARTH_SUN!r} from GM_E = 3.986004418e14 (comment: 'IAU 2015 nominal GM_E');"
      f" engine core.constants.GM_EARTH = {K.GM_EARTH!r} (IAU 2015 B3 nominal: 3.986 004 x 10^14, sources/1510.07674.txt"
      f" line 103); relative difference {3.986004418e14 / K.GM_EARTH - 1:.2e}")
print(f"KMS = {V.KMS!r} au/yr per km/s; Earth's circular speed sqrt(G_AU)/KMS = {math.sqrt(V.G_AU) / V.KMS:.4f} km/s")
print(f"RS_AU = {V.RS_AU!r} au (2 G Msun / c^2 = {2 * K.GM_SUN / K.C ** 2:.6g} m)")
for m in (10.0, 20.0):
    print(f"M = {m} Msun: G M/c^3 = {m * K.GM_SUN / K.C ** 3:.6e} s, G M/c^2 = {m * K.GM_SUN / K.C ** 2:.6e} m")
print(f"MPC = {V.MPC!r} m; 648000/pi au = {648000 / math.pi * K.AU!r} m")
