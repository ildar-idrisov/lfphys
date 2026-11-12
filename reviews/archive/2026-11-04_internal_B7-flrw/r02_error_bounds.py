"""r02: is the error returned by ``with_error=True`` an upper bound of the actual error, and is the actual error below
the documented 2e-13 (ABOUT['validity']: "фактическая ошибка против замкнутых форм и mpmath <= 2e-13"; module
docstring: "measured against closed forms and 30-digit mpmath it is never smaller than the actual error and stays
below 1e-12 relative")?  Cases the engine's own tests do not cover with an error check:

 A. dark energy alone, constant w (CPL wa = 0, O_m = 0): the integrands in xi = sqrt(a) have an integrable power-law
    singularity at the big bang (eta: 2 xi^(1-p), t: 2 xi^(3-p), p = 1 - 3w); closed forms
    eta = a^(q-1)/(q-1), t = a^q/q (units 1/H0), q = 3(1+w)/2.
 B. closed dust (O_m = 2) next to its turnaround a_max = 2: age and conformal time against the cycloid
    (a = A(1 - cos u), H0 t = B(u - sin u), H0 eta = u/sqrt(O_m - 1)).
 C. a loitering universe (O_m = 0.3, O_L just below the critical value of an Eddington-Lemaitre double root).
 D. the same just above the critical value: a narrow forbidden band of S < 0 (no big bang) - is it detected?
 E. Planck 2018 (massive neutrino): age, conformal time, D_C, lookback time, r_s, against mpmath quadrature (50
    digits) of an integrand assembled in mpmath (polynomial part exact; the neutrino F(y) from the engine, checked to
    4.4e-16 in r01, contributing < 1e-17 to S).
Run (from engine/):
  docker run --rm --name lf-b7rc-r02 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r02_error_bounds.py
"""
import math
import sys
import warnings

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.cosmology import flrw as F  # noqa: E402
from lfphys.theories.models import dark_energy as DE  # noqa: E402

mp.mp.dps = 50
rows = []


def report(case, q, value, err, exact):
    exact = float(exact)
    actual = abs(value - exact)
    ratio = actual / err if err > 0 else math.inf
    flag = "BOUND FAILS" if actual > err and actual > 4 * 2.0 ** -53 * abs(exact) else "ok"
    rel = actual / abs(exact) if exact != 0 else actual
    flag2 = "  >2e-13" if rel > 2e-13 else ""
    rows.append((case, q, rel, err / abs(exact) if exact else err, ratio, flag))
    print(f"{case:42s} {q:22s} actual rel {rel:9.2e}  stated rel {err / abs(exact):9.2e}  actual/stated "
          f"{ratio:8.2f}  {flag}{flag2}")


# ---------------- A. dark energy alone -----------------------------------------------------------------------------
print("A. dark energy alone (O_m = 0), constant w")
for w in (-0.2, -0.3, -0.32, -0.8, -0.9, -0.95):
    bg = DE.background(70.0, 0.0, w0=w, wa=0.0)
    q = 1.5 * (1 + w)
    for z in (0.0, 1.0, 10.0):
        a = 1 / (1 + z)
        if q > 1:          # conformal time finite: eta = a^(q-1)/(q-1)
            try:
                with warnings.catch_warnings(record=True) as wl:
                    warnings.simplefilter("always")
                    v, e = bg.conformal_time(z, with_error=True)
                ex = mp.mpf(a) ** (q - 1) / (q - 1) * bg.hubble_time
                report(f"DE only w={w}", f"conformal_time z={z:g}", v, e, ex)
                for x in wl:
                    print("      warning:", str(x.message)[:90])
            except Exception as exc:  # noqa: BLE001
                print(f"DE only w={w:<36} conformal_time z={z:g}: {type(exc).__name__}: {exc}")
        try:
            with warnings.catch_warnings(record=True) as wl:
                warnings.simplefilter("always")
                v, e = bg.age(z, with_error=True)
            ex = mp.mpf(a) ** q / q * bg.hubble_time
            report(f"DE only w={w}", f"age z={z:g}", v, e, ex)
            for x in wl:
                print("      warning:", str(x.message)[:90])
        except Exception as exc:  # noqa: BLE001
            print(f"DE only w={w:<36} age z={z:g}: {type(exc).__name__}: {exc}")

# ---------------- B. closed dust next to the turnaround -------------------------------------------------------------
print("\nB. closed dust O_m = 2 (a_max = 2): age and conformal time at a = 2 (1 - d)")
Om = 2.0
bg = F.Background(70.0, Om, OL=0.0)
A, B = Om / (2 * (Om - 1)), Om / (2 * (Om - 1) ** 1.5)
print("   roots():", bg.roots())
for d in (1e-2, 1e-4, 1e-6, 1e-8, 1e-10, 1e-12):
    a = 2.0 * (1 - d)
    z = 1 / a - 1
    a_true = 1 / (1 + mp.mpf(z))          # the scale factor the engine actually integrates to
    u = mp.acos(1 - a_true / A)
    try:
        v, e = bg.age(z, with_error=True)
        report(f"closed dust, 1 - a/a_max = {d:g}", "age", v, e, B * (u - mp.sin(u)) * bg.hubble_time)
        v, e = bg.conformal_time(z, with_error=True)
        report(f"closed dust, 1 - a/a_max = {d:g}", "conformal_time", v, e, u / mp.sqrt(Om - 1) * bg.hubble_time)
    except Exception as exc:  # noqa: BLE001
        print(f"   d = {d:g}: {type(exc).__name__}: {exc}")

# ---------------- C/D. loitering and a narrow forbidden band ---------------------------------------------------------
print("\nC. loitering: O_m = 0.3, O_L = O_L,crit (1 - eps)")


def crit(Om):
    # double root of S = Om a + Ok a^2 + OL a^4: a_L^3 = Om/(2 OL), Ok = 1 - Om - OL = -3 OL a_L^2
    f = lambda OL: 1 - Om - OL + 3 * OL * (Om / (2 * OL)) ** (mp.mpf(2) / 3)  # noqa: E731
    OL = mp.findroot(f, 2.0)
    return OL, (Om / (2 * OL)) ** (mp.mpf(1) / 3)


OLc, aL = crit(mp.mpf("0.3"))
print(f"   O_L,crit = {mp.nstr(OLc, 17)}, a_L = {mp.nstr(aL, 17)} (z_L = {mp.nstr(1 / aL - 1, 8)})")
for eps in (1e-3, 1e-6, 1e-9):
    OL = float(OLc * (1 - eps))
    bg = F.Background(70.0, 0.3, OL=OL)
    Omp, Okp, OLp = (mp.mpf(x) for x in (bg.Om, bg.Ok, bg.OL))
    S = lambda a: Omp * a + Okp * a * a + OLp * a ** 4  # noqa: E731
    aLp = (Omp / (2 * OLp)) ** (mp.mpf(1) / 3)
    try:
        v, e = bg.age(0.0, with_error=True)
        ex = mp.quad(lambda a: a / mp.sqrt(S(a)), [0, aLp * (1 - mp.mpf(10) ** -2), aLp, aLp * (1 + mp.mpf(10) ** -2), 1])
        report(f"loitering eps={eps:g}", "age z=0", v, e, ex * bg.hubble_time)
        v, e = bg.comoving_distance(5.0, with_error=True)
        ex = mp.quad(lambda a: 1 / mp.sqrt(S(a)), [mp.mpf(1) / 6, aLp * (1 - mp.mpf(10) ** -2), aLp,
                                                     aLp * (1 + mp.mpf(10) ** -2), 1])
        report(f"loitering eps={eps:g}", "D_C z=5", v, e, ex * bg.hubble_distance)
    except Exception as exc:  # noqa: BLE001
        print(f"   eps = {eps:g}: {type(exc).__name__}: {exc}")

print("\nD. just above the critical value: O_L = O_L,crit (1 + eps) has S < 0 on a band around a_L (no big bang)")
for eps in (1e-2, 1e-4, 1e-6, 1e-8, 1e-10):
    OL = float(OLc * (1 + eps))
    bg = F.Background(70.0, 0.3, OL=OL)
    Omp, Okp, OLp = (mp.mpf(x) for x in (bg.Om, bg.Ok, bg.OL))
    S = lambda a: Omp * a + Okp * a * a + OLp * a ** 4  # noqa: E731
    # the true band: roots of S/a = Om + Ok a + OL a^3 near a_L
    g = lambda a: Omp + Okp * a + OLp * a ** 3  # noqa: E731
    aLp = (Omp / (2 * OLp)) ** (mp.mpf(1) / 3)
    try:
        lo = mp.findroot(g, aLp * (1 - 2 * mp.sqrt(eps)))
        hi = mp.findroot(g, aLp * (1 + 2 * mp.sqrt(eps)))
        band = f"S<0 on [{mp.nstr(lo, 10)}, {mp.nstr(hi, 10)}] (width {mp.nstr((hi - lo) / aLp, 3)} a_L)"
    except Exception:  # noqa: BLE001
        band = "band not resolved"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            r = bg.roots()
            msg = f"roots() = {r}"
            try:
                age = bg.age()
                msg += f"; age() returned {age!r} Gyr  <-- a universe without a big bang"
            except Exception as exc:  # noqa: BLE001
                msg += f"; age() -> {type(exc).__name__}: {str(exc)[:80]}"
        except Exception as exc:  # noqa: BLE001
            msg = f"{type(exc).__name__}: {exc}"
    print(f"   eps = {eps:7.0e}: {band}; {msg}")

# ---------------- E. Planck 2018 with the massive neutrino ----------------------------------------------------------
print("\nE. Planck 2018 (planck2018()), mpmath reference with exact polynomial part")
bg = F.planck2018()
Or, Om, Ok, OL, Onu = (mp.mpf(x) for x in (bg.Orad, bg.Om, bg.Ok, bg.OL, bg.Onu_per_species))
y0 = float(bg._y0[0])
R0 = mp.mpf(3) * mp.mpf(bg.Ob) / (4 * mp.mpf(bg.Ogamma))


def S(a):
    return Or + Om * a + Ok * a * a + OL * a ** 4 + Onu * mp.mpf(F.fermi_dirac_energy(float(a) * y0))


def mpint(f, lo, hi):
    pts = [mp.mpf(lo)] + [mp.mpf(10) ** k for k in range(-12, 1) if lo < 10.0 ** k < hi] + [mp.mpf(hi)]
    return mp.quad(f, pts)


zs = 1089.80
cases = [
    ("age z=0", lambda: bg.age(0.0, with_error=True), lambda: mpint(lambda a: a / mp.sqrt(S(a)), 0, 1),
     bg.hubble_time),
    ("age z=1089.8", lambda: bg.age(zs, with_error=True),
     lambda: mpint(lambda a: a / mp.sqrt(S(a)), 0, 1 / (1 + mp.mpf(zs))), bg.hubble_time),
    ("conformal_time z=0", lambda: bg.conformal_time(0.0, with_error=True),
     lambda: mpint(lambda a: 1 / mp.sqrt(S(a)), 0, 1), bg.hubble_time),
    ("D_C z=1089.8", lambda: bg.comoving_distance(zs, with_error=True),
     lambda: mpint(lambda a: 1 / mp.sqrt(S(a)), 1 / (1 + mp.mpf(zs)), 1), bg.hubble_distance),
    ("D_C z=0.5", lambda: bg.comoving_distance(0.5, with_error=True),
     lambda: mpint(lambda a: 1 / mp.sqrt(S(a)), 1 / mp.mpf(1.5), 1), bg.hubble_distance),
    ("lookback z=2", lambda: bg.lookback_time(2.0, with_error=True),
     lambda: mpint(lambda a: a / mp.sqrt(S(a)), mp.mpf(1) / 3, 1), bg.hubble_time),
    ("r_s z=1089.8", lambda: bg.sound_horizon(zs, with_error=True),
     lambda: mpint(lambda a: 1 / mp.sqrt(S(a)) / mp.sqrt(3 * (1 + R0 * a)), 0, 1 / (1 + mp.mpf(zs))),
     bg.hubble_distance),
]
for q, eng, ref, unit in cases:
    v, e = eng()
    report("Planck 2018", q, float(v), float(e), ref() * unit)

print("\nsummary: worst actual/stated per case")
fails = [r for r in rows if r[5] != "ok"]
print(f"   {len(rows)} checks, {len(fails)} where the stated error is below the actual error:")
for r in fails:
    print(f"   {r[0]:42s} {r[1]:22s} actual rel {r[2]:.2e} stated rel {r[3]:.2e} ratio {r[4]:.1f}")
big = [r for r in rows if r[2] > 2e-13]
print(f"   {len(big)} checks with actual relative error above the documented 2e-13:")
for r in big:
    print(f"   {r[0]:42s} {r[1]:22s} actual rel {r[2]:.2e} stated rel {r[3]:.2e}")
