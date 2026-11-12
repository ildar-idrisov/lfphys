"""r09: a(t) of planck2018() in the far future. Beyond a ~ 1e77, O_L a^4 overflows binary64 inside S(a); the reference
is de Sitter growth from the verified a(2000 Gyr) of r08 (the matter and radiation terms there are < 1e-140 of S):
a(t) = a(2000) exp(H0 sqrt(O_L) (t - 2000 Gyr)).
Run (from engine/):
  docker run --rm --name lf-b7rc-r09 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r09_far_future.py
"""
import math
import sys
import warnings

import mpmath as mp

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.cosmology import flrw as F  # noqa: E402

bg = F.planck2018()
a2000 = mp.mpf("3.708224032646732e49")         # r08 reference
HL = mp.mpf(bg.OL) ** 0.5 / mp.mpf(bg.hubble_time)
for t in (2000.0, 3000.0, 3080.0, 3100.0, 3200.0, 5000.0, 10000.0):
    ref = a2000 * mp.exp(HL * (t - 2000))
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        a = bg.scale_factor(t)
        try:
            a_ode = bg.scale_factor_ode(t - bg.age())
        except Exception as exc:  # noqa: BLE001
            a_ode = float("nan")
            print(f"   scale_factor_ode({t - bg.age():.1f}): {type(exc).__name__}: {exc}")
    rel = abs(a / ref - 1)
    print(f"t = {t:7.0f} Gyr: reference a = {mp.nstr(ref, 10):>12s}  scale_factor = {a:.10g} (rel err {float(rel):.2e})"
          f"  scale_factor_ode = {a_ode:.6g}  warnings: {sorted({type(w.message).__name__ for w in wl}) or 'none'}")
print("\nlargest a with O_L a^4 finite:", 1.7976931348623157e308 ** 0.25 / bg.OL ** 0.25)
print("time (age) of t(a) at a = 1e70 and 1e80 from the engine's own t(a):",
      [float(bg._time(__import__('numpy').array([x]), 'bang', 1e-13)[0] * bg.hubble_time) for x in (1e70, 1e80)])
print("reference t(a) = 2000 Gyr + ln(a / a(2000)) / (H0 sqrt(O_L)) at a = 1e70 and 1e80:",
      [float(2000 + mp.log(mp.mpf(x) / a2000) / HL) for x in (1e70, 1e80)])

# matter + dark energy of constant w = -0.99 (CPL, wa = 0), flat: beyond a1 = 1e30 the matter term is < 1e-88 of S, so
# t(a) = t(a1) + (a^q - a1^q)/(q H0 sqrt(O_L)), q = 3(1 + w)/2, with t(a1) from the engine (a1 is far below the
# overflow); here the expansion is a power law, so a Newton step in ln a is not exact
from lfphys.theories.models import dark_energy as DE  # noqa: E402
import numpy as np  # noqa: E402

w = -0.99
de = DE.background(70.0, 0.3, w0=w, wa=0.0)
q = 1.5 * (1 + w)
a1 = mp.mpf(1e30)
t1 = mp.mpf(float(de._time(np.array([1e30]), "bang", 1e-13)[0])) * mp.mpf(de.hubble_time)
cst = q * mp.sqrt(mp.mpf(de.OL)) / mp.mpf(de.hubble_time)
print(f"\nO_m = 0.3 + dark energy w = {w}: t(1e30) = {mp.nstr(t1, 12)} Gyr from the engine")
for target in (1e50, 1e70, 1e76, 1e78, 1e90, 1e120):
    t = float(t1 + (mp.mpf(target) ** q - a1 ** q) / cst)
    ref = (a1 ** q + cst * (mp.mpf(t) - t1)) ** (1 / mp.mpf(q))
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        try:
            a = de.scale_factor(t)
            sa = f"{a:.8g}, rel err {float(abs(a / ref - 1)):.2e}"
        except Exception as exc:  # noqa: BLE001
            sa = f"{type(exc).__name__}: {str(exc)[:60]}"
    print(f"   t = {t:10.6g} Gyr: reference a = {mp.nstr(ref, 8):>10s}, scale_factor = {sa}  warnings: "
          f"{sorted({type(x.message).__name__ for x in wl}) or 'none'}")
