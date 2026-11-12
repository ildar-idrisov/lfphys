# Review B8-mie, script s11: the medium. v17's default medium is vacuum (n_medium = 1); a rainbow forms in air,
# n_air - 1 ~ 2.7e-4 in the visible (an illustrative value: ~2.77e-4 at 550 nm for dry air at 15 C, 101.325 kPa; not
# verified against a source here, only the size of the effect matters). The relative index m = n_water/n_air and
# the Descartes and Airy angles shift; compared with the precision the README quotes (138.270 deg, 138.959 deg).
import math, sys
sys.path.insert(0, "/lf/lfphys")
from lfphys.core import data as D  # noqa: E402
from lfphys.theories.approx import rainbow as rb  # noqa: E402
nw = float(D.water_index(550.0, 10.0))
for n_air in (1.0, 1.000277):
    m = nw / n_air
    d2, d3 = rb.descartes(m, 2), rb.descartes(m, 3)
    x = 2 * math.pi * n_air * 150.0 / 0.55
    am = rb.airy_maxima(m, 2, x, 1)[0]
    print(f"n_medium = {n_air}: m = {m:.6f}, Descartes p=2 {math.degrees(d2['theta']):.3f} deg, p=3 {math.degrees(d3['theta']):.3f} deg, "
          f"Airy first max (150 um) {math.degrees(am):.3f} deg")
print("water_index at 105 C (0.1 MPa; boiling 372.76 K per SR6-08):", float(D.water_index(589.0, 105.0)))
