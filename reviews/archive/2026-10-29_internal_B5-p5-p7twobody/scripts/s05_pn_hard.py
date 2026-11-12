"""P7 review, check 5: pn_binary on strong fields, high eccentricity, small mass ratios, and its helper functions.

(a) circular_speed: convergence of its fixed-point iteration at small radii (no convergence check in the code);
(b) state_from_invariants near j = 1: is the returned state the periapsis or the apoapsis?
(c) the two integration routes against each other in strong field / high e / small nu, and their cost;
(d) averaged_dissipation at high eccentricity (2.5PN, Newtonian orbit) against Peters-Mathews;
(e) PSR B1913+16: the 1PN flux check of the tests, the actual residual against the stated O(x^2);
(f) quasi-circular initial data: residual eccentricity with quasi=True and False.

Run: python3 s05_pn_hard.py
"""
import argparse
import math
import time

import numpy as np

from lfphys.core.gravity import pn_binary as P


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print("(a) circular_speed: residual of v^2 = (1 + A)/r after the return")
    for nu in (0.25, 0.01):
        for r in (20.0, 6.0, 4.0, 3.0, 2.5, 2.0):
            vt = P.circular_speed(r, nu, (1, 2))
            A, _ = P.coefficients(r, 0.0, vt * vt, nu, (1, 2))
            res = abs(vt * vt - (1 + A) / r) / (vt * vt)
            print(f"  nu={nu} r={r}: v={vt:.6f}, relative residual {res:.2e}"
                  + ("" if res < 1e-12 else "  <- NOT CONVERGED (returned silently)"))

    print("(b) state_from_invariants near j = 1: periapsis or apoapsis?")
    nu = 0.25
    for eps, j in ((0.01, 0.999), (0.01, 1.0), (0.02, 0.99), (0.01, 0.98), (0.005, 0.9995)):
        st = P.state_from_invariants(eps, j, nu)
        r0 = float(np.linalg.norm(st["x"]))
        out = P.integrate(st, 1.2 * 2 * math.pi / P.mean_motion(eps, j, nu), nu, orders=(1, 2), n_out=4000)
        r = np.linalg.norm(out["x"], axis=1)
        kind = "periapsis" if abs(r0 - r.min()) < abs(r0 - r.max()) else "APOAPSIS"
        print(f"  eps={eps} j={j}: r0={r0:.4f}, r_min={r.min():.4f}, r_max={r.max():.4f} -> {kind}")

    print("(c) cartesian vs elements, all orders, after 3 radial periods (rtol 1e-12)")
    for nu, a, e in ((0.25, 40.0, 0.8), (0.25, 16.0, 0.5), (0.001, 30.0, 0.7), (0.25, 200.0, 0.95)):
        st = P.periapsis_state(a, e)
        T = 3 * 2 * math.pi * a**1.5
        t0 = time.time()
        oc = P.integrate(st, T, nu, method="cartesian", n_out=200)
        tc = time.time() - t0
        t0 = time.time()
        try:
            oe = P.integrate(st, T, nu, method="elements", n_out=200)
            te = time.time() - t0
            dx = np.max(np.linalg.norm(oc["x"] - oe["x"], axis=1)) / (a * (1 + e))
            print(f"  nu={nu} a={a} e={e}: max |x_c - x_e| / r_apo = {dx:.2e} (cartesian {tc:.1f} s, elements "
                  f"{te:.1f} s)")
        except Exception as ex:  # noqa: BLE001
            print(f"  nu={nu} a={a} e={e}: elements route failed: {type(ex).__name__}: {ex}")
        # tighter cartesian reference
        oc2 = P.integrate(st, T, nu, method="cartesian", n_out=200, rtol=1e-13)
        print(f"      cartesian rtol 1e-12 vs 1e-13: {np.max(np.linalg.norm(oc['x'] - oc2['x'], axis=1)) / (a * (1 + e)):.2e}")

    print("(c2) a plunging orbit (a = 20, e = 0.9: r_p = 2 m) without and with r_stop = 4")
    st = P.periapsis_state(20.0, 0.9)
    for rs in (None, 4.0):
        try:
            out = P.integrate(st, 3 * 2 * math.pi * 20.0**1.5, 0.25, r_stop=rs, n_out=10)
            print(f"  r_stop={rs}: status {out['status']}, t_end {out['end']['t']:.2f}")
        except Exception as ex:  # noqa: BLE001
            print(f"  r_stop={rs}: {type(ex).__name__}: {ex}")
    st = P.state(0.0, [20.0, 0, 0], [0, 0.05, 0])  # starts at apoapsis, r_p ~ 1
    for rs in (None, 4.0):
        try:
            out = P.integrate(st, 2000.0, 0.25, r_stop=rs, n_out=10)
            print(f"  apoapsis start, r_stop={rs}: status {out['status']}, t_end {out['end']['t']:.2f}, "
                  f"r_end {np.linalg.norm(out['end']['x']):.4f}")
        except Exception as ex:  # noqa: BLE001
            print(f"  apoapsis start, r_stop={rs}: {type(ex).__name__}: {ex}")

    print("(d) averaged_dissipation (Newton + 2.5PN) at high eccentricity vs Peters-Mathews")
    nu, a = 0.2, 50.0
    for e in (0.9, 0.95, 0.99):
        t0 = time.time()
        res = P.averaged_dissipation(P.periapsis_state(a, e), nu, conservative=(), dissipative=(2.5,), order=0)
        f = (1 + 73 / 24 * e**2 + 37 / 96 * e**4) / (1 - e * e) ** 3.5
        ref = -6.4 * nu / a**5 * f
        print(f"  e={e}: dE/ref - 1 = {res['dE'] / ref - 1:.2e} ({time.time()-t0:.1f} s)")

    print("(e) PSR B1913+16: averaged reaction (2.5 + 3.5PN on the 2PN orbit) against the 1PN flux")
    from lfphys.core import data as D
    from lfphys.core.constants import C
    from lfphys.theories.approx import peters_mathews as PM
    GMS = D.PULSAR_T_SUN_S * C**3
    PB = D.PSR_B1913_PB_DAYS[0] * 86400.0
    ECC = D.PSR_B1913_ECC[0]
    om = math.radians(D.PSR_B1913_PERIASTRON_DEG_PER_YR[0]) / (365.25 * 86400.0)
    g1, g2 = PM.masses_from_pk(om, D.PSR_B1913_GAMMA_S[0], PB, ECC)
    M = g1 + g2
    nu = g1 * g2 / M**2
    a = PM.semi_major_axis(M, PB) / P.mass_units(M)["length"]
    st = P.periapsis_state(a, ECC)
    res = P.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=(2.5, 3.5), order=2, rtol=1e-13)
    gi = P.gauge_invariants(st["x"], st["v"], nu)
    x = P.x_parameter(gi["eps"], gi["j"], nu)
    et = P.time_eccentricity(gi["eps"], gi["j"], nu)
    e2 = et * et
    I0 = (1 + 73 / 24 * e2 + 37 / 96 * e2**2) / (1 - e2) ** 3.5
    I1 = (-1247 / 336 - 35 / 12 * nu + e2 * (10475 / 672 - 1081 / 36 * nu) + e2**2 * (10043 / 384 - 311 / 12 * nu)
          + e2**3 * (2179 / 1792 - 851 / 576 * nu)) / (1 - e2) ** 4.5
    ratio = res["dE"] / (-6.4 * nu * x**5 * I0)
    print(f"  x = {x:.3e}, x I1/I0 = {x * I1 / I0:.3e}, ratio - 1 - x I1/I0 = {ratio - 1 - x * I1 / I0:.2e} "
          f"(test tolerance 0.01 x I1/I0 = {0.01 * abs(x * I1 / I0):.1e}; O(x^2) = {x * x:.1e})")
    res0 = P.averaged_dissipation(st, nu, conservative=(), dissipative=(2.5,), order=0, rtol=1e-13)
    print(f"  Newtonian route for comparison: dE/(PM at the same a, e) - 1 = "
          f"{res0['dE'] / (-6.4 * nu / a**5 * I0 * (1 - e2)**3.5 / (1 - ECC**2)**3.5 * (1 + 73/24*ECC**2 + 37/96*ECC**4) / (1 + 73/24*e2 + 37/96*e2**2)) - 1:.2e}")

    print("(f) quasi-circular initial data: residual eccentricity (r_max - r_min)/(r_max + r_min) over 2 orbits")
    nu = 0.25
    for r0 in (30.0, 15.0, 10.0):
        for quasi in (False, True):
            st = P.circular_state(r0, nu, quasi=quasi)
            T = 2 * 2 * math.pi * r0**1.5
            out = P.integrate(st, T, nu, n_out=4000)
            r = np.linalg.norm(out["x"], axis=1)
            # remove the secular inspiral by a quadratic fit in t, keep the oscillation
            c = np.polyfit(out["t"], r, 2)
            osc = r - np.polyval(c, out["t"])
            print(f"  r0={r0} quasi={quasi}: radial oscillation amplitude / r0 = {np.ptp(osc) / (2 * r0):.2e}")


if __name__ == "__main__":
    main()
