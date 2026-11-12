"""r06: a bounce whose forbidden band (S < 0) is narrower than roots()'s scan step (4000 points in xi): what the public
functions return. O_m = 0.3, O_L = O_L,crit (1 + eps) (Eddington-Lemaitre double root at a_L = 0.444 when eps = 0):
the universe today (a = 1) came from a bounce at the upper edge of the band; there is no big bang.
Run (from engine/):
  docker run --rm --name lf-b7rc-r06 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r06_missed_bounce.py
"""
import sys
import warnings

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.cosmology import flrw as F  # noqa: E402

mp.mp.dps = 40
Om = mp.mpf("0.3")
OLc = mp.findroot(lambda OL: 1 - Om - OL + 3 * OL * (Om / (2 * OL)) ** (mp.mpf(2) / 3), 2.0)


def call(f, *a, **k):
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        try:
            r = f(*a, **k)
            r = np.asarray(r)
            s = np.array2string(r, precision=10) if r.size > 1 else f"{float(r):.10g}"
        except Exception as exc:  # noqa: BLE001
            s = f"{type(exc).__name__}: {str(exc)[:70]}"
    if wl:
        s += f"  [warning: {str(wl[0].message)[:60]}]"
    return s


for eps in (1e-4, 1e-6, 1e-8):
    bg = F.Background(70.0, 0.3, OL=float(OLc * (1 + eps)))
    Omp, Okp, OLp = (mp.mpf(x) for x in (bg.Om, bg.Ok, bg.OL))
    g = lambda a: Omp + Okp * a + OLp * a ** 3  # noqa: E731
    aL = (Omp / (2 * OLp)) ** (mp.mpf(1) / 3)
    hi = mp.findroot(g, aL * (1 + 2 * mp.sqrt(eps)))
    lo = mp.findroot(g, aL * (1 - 2 * mp.sqrt(eps)))
    print(f"eps = {eps:g}: true bounce at a = {mp.nstr(hi, 12)} (z = {mp.nstr(1 / hi - 1, 8)}); band [{mp.nstr(lo, 8)}, "
          f"{mp.nstr(hi, 8)}]")
    print(f"   roots()                         : {bg.roots()}")
    print(f"   _has_big_bang()                 : {bg._has_big_bang()}")
    print(f"   comoving_distance(z=1.2)        : {call(bg.comoving_distance, 1.2)}  (z_bounce above)")
    zb = float(1 / hi - 1)
    print(f"   comoving_distance(z=3)          : {call(bg.comoving_distance, 3.0)}  (beyond the bounce: never seen)")
    print(f"   E(z=1/a_L - 1)                  : {call(bg.E, float(1 / aL - 1))}")
    print(f"   age()                           : {call(bg.age)}")
    print(f"   scale_factor(-30, 'today')      : {call(bg.scale_factor, -30.0, since='today')}")
    print(f"   scale_factor_ode(-30)           : {call(bg.scale_factor_ode, -30.0)}")
    print(f"   scale_factor(5, 'big_bang')     : {call(bg.scale_factor, 5.0)}")
