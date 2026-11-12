"""r08: a(t) of planck2018() against an mpmath reference (t(a) by 40-digit quadrature, the neutrino F(y) from the
engine as in r02), at early, present and late times, since the big bang; the documented accuracy is "~1e-14
relative" (ABOUT['validity']). Late times: t H grows, so a carries the relative error of t times t H.
Run (from engine/):
  docker run --rm --name lf-b7rc-r08 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r08_scale_factor.py
"""
import sys

import mpmath as mp

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.cosmology import flrw as F  # noqa: E402

mp.mp.dps = 40
bg = F.planck2018()
Or, Om, Ok, OL, Onu = (mp.mpf(x) for x in (bg.Orad, bg.Om, bg.Ok, bg.OL, bg.Onu_per_species))
y0 = float(bg._y0[0])
tH = mp.mpf(bg.hubble_time)


def S(a):
    return Or + Om * a + Ok * a * a + OL * a ** 4 + Onu * mp.mpf(F.fermi_dirac_energy(float(a) * y0))


def t_of(a):
    pts = [mp.mpf(0)] + [mp.mpf(10) ** k for k in range(-12, 301) if 10.0 ** k < a] + [a]
    return mp.quad(lambda x: x / mp.sqrt(S(x)), pts) * tH


for t in (1e-9, 1e-3, 0.38, 13.787, 50.0, 200.0, 1000.0, 2000.0, 5000.0):
    try:
        a_eng = bg.scale_factor(t)
    except Exception as exc:  # noqa: BLE001
        print(f"t = {t:9g} Gyr: {type(exc).__name__}: {exc}")
        continue
    # refine from the engine's value by Newton on t(a) with dt/da = 1/(a H) in mpmath
    a = mp.mpf(a_eng)
    for _ in range(6):
        g = t_of(a) - t
        a = a - g * a * mp.sqrt(S(a)) / a ** 2 / tH          # dt/da = a/sqrt(S) * tH
    H_t = float(mp.sqrt(S(a)) / a ** 2 / tH * t)
    print(f"t = {t:9g} Gyr: a_engine = {a_eng:.15e}, a_ref = {mp.nstr(a, 16)}, rel err "
          f"{abs(a_eng / float(a) - 1):.2e}, t H = {H_t:.3g}")
