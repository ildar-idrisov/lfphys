# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review B5, check c05: theories.alternatives.johannsen_metric against the sources and an independent route.
#
# (a) The published bounds: Psaltis et al. 2020 "-3.6 < alpha13 < 5.9" (|delta| <= 0.17, a = 0) and Sgr A* Paper VI
#     Table 3 (Keck) "-1.1 <~ alpha12 <~ 0.5", "-3.1 <~ alpha13 <~ 1.5" with the module's allowed_range; Psaltis Eq. (8)
#     "r_sh,JP = 3 sqrt3 [1 + alpha13/27 - alpha13^2/486 + O(alpha13^3)]" against nonspinning_shadow at small alpha13;
#     the interval v15 actually uses for M87* (Paper VI 2019: -0.01 +- 0.17) against the module's (+-0.17).
# (b) The spinning shadow edge by an independent route: along screen directions from the curve's centre, bisection
#     on the fate of a ray decided from the JP radial potential itself (the largest root of R_JP(r) on r > r+ found by
#     sampling + brentq: a turning point outside the horizon = the ray came from infinity), against the closed curve
#     of shadow_curve (its polygon). Kerr (alpha = 0) and deviating metrics.
# (c) Regularity: the module checks A1 > 0 and A2 > 0 on r >= r+; Johannsen 2013a also requires (Eq. 72)
#     A1 (r^2 + a^2) - a^2 A2 sin^2 theta != 0 (the determinant, Eq. 71) and (Eq. 76) A1^2 (r^2 + a^2)^2 -
#     a^2 Delta sin^2 theta > 0 (no closed timelike curves) on and outside the horizon. Which parameters of v15's
#     ranges pass check_regular and violate (72) or (76), and what shadow_curve returns for them.
# (d) The size measure: the module centres the curve half-way between its extreme alpha; CHARM (Sgr A* Paper VI
#     Sec. 3) iterates the centre "such that the variance in the diameter along different cross sections is
#     minimized". delta with both centres; and the Kerr range "values of delta in the range [-0.075, 0] are consistent
#     with the Kerr predictions" (Paper VI Sec. 3) against the module's delta over spins and inclinations.
#
# Root: engine at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this script in
# /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/. CPU. Run as c02 (see its header).
import math

import numpy as np
from scipy.optimize import minimize, minimize_scalar

from lfphys.core.gravity import kerr_null as KN
from lfphys.theories.alternatives import johannsen_metric as JP


def fate_escapes(al, be, th, chi, dev):
    """True if the ray of screen point (al, be) has a radial turning point outside the horizon in the JP metric."""
    lam = -al * math.sin(th)
    eta = (al * al - chi * chi) * math.cos(th) ** 2 + be * be
    rp = 1 + math.sqrt(1 - chi * chi)
    r = rp * np.exp(np.linspace(1e-9, math.log(200.0 / rp), 6000))
    R = JP.radial_potential(r, lam, eta, chi, dev)
    if np.any(R < 0):
        return True  # R < 0 somewhere outside the horizon: the ray from infinity turns before it
    # refine the minimum of R near the grid's smallest value (a forbidden band narrower than the grid step)
    i = int(np.argmin(R))
    lo, hi = r[max(i - 1, 0)], r[min(i + 1, r.size - 1)]
    res = minimize_scalar(lambda x: float(JP.radial_potential(x, lam, eta, chi, dev)), bounds=(lo, hi),
                          method="bounded", options={"xatol": 1e-14 * hi})
    return res.fun < 0


def edge_along(ang, cx, th, chi, dev, rho_max=15.0):
    lo, hi = 0.0, rho_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if fate_escapes(cx + mid * math.cos(ang), mid * math.sin(ang), th, chi, dev):
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def poly_radius(curve, cx, ang):
    al, be = np.asarray(curve["alpha"]), np.asarray(curve["beta"])
    al, be = np.append(al, al[0]), np.append(be, be[0])
    return JP._radius_at(al, be, cx, ang)


def charm_delta(curve, n_angles=128):
    """Median diameter with the centre chosen to minimise the variance of the diameters (CHARM step iv)."""
    al, be = np.asarray(curve["alpha"], float), np.asarray(curve["beta"], float)
    al, be = np.append(al, al[0]), np.append(be, be[0])
    ang = 2 * math.pi * np.arange(n_angles) / n_angles

    def radii(c):
        cx, cy = c
        return np.array([JP._radius_at(al, be - cy, cx, t) for t in ang])

    def var(c):
        r = radii(c)
        d = r[:n_angles // 2] + r[n_angles // 2:]
        return float(np.var(d))
    c0 = (0.5 * (al.max() + al.min()), 0.0)
    res = minimize(var, c0, method="Nelder-Mead", options={"xatol": 1e-7, "fatol": 1e-14})
    r = radii(res.x)
    return 2 * float(np.median(r)) / JP.SCHWARZSCHILD_DIAMETER - 1, res.x


def main():
    out = []
    out.append("== (a) published bounds ==")
    b = JP.allowed_range("alpha13", (-0.17, 0.17))
    out.append(f"M87* |delta| <= 0.17, a = 0: alpha13 in [{b['low']:.4f}, {b['high']:.4f}]  (Psaltis 2020: -3.6 < a13 < 5.9)")
    b = JP.allowed_range("alpha13", (-0.18, 0.16))
    out.append(f"M87* as v15 compares it (-0.01 +- 0.17 -> [-0.18, 0.16]): alpha13 in [{b['low']:.4f}, {b['high']:.4f}]")
    k = JP.eht_delta_bounds()
    kb = k["Sgr A* Keck (Paper VI Eq. 12)"]
    for p in ("alpha13", "alpha12"):
        b = JP.allowed_range(p, kb)
        out.append(f"Sgr A* Keck {kb}: {p} in [{b['low']:.4f}, {b['high']:.4f}]")
    out.append(f"module's bounds: {k}")
    for a13 in (1e-3, -1e-3, 0.3):
        bc, _ = JP.nonspinning_shadow(JP.Deviation(alpha13=a13))
        ser = 3 * math.sqrt(3) * (1 + a13 / 27 - a13 ** 2 / 486)
        out.append(f"Psaltis Eq. 8 at alpha13 = {a13}: module {bc:.12f}, series {ser:.12f}, diff {bc - ser:.2e} "
                   f"(O(a^3) ~ {abs(a13) ** 3 * 3 * math.sqrt(3) * 1e-3:.1e})")
    out.append("")
    out.append("== (b) spinning shadow edge: independent fate bisection vs shadow_curve ==")
    for chi, thd, kw in ((0.9, 60.0, {}), (0.9, 60.0, {"alpha13": 2.0}), (0.6, 30.0, {"alpha22": 1.5}),
                         (0.6, 80.0, {"alpha12": -0.5, "alpha13": 1.0}), (0.95, 89.0, {"alpha13": -1.0}),
                         (0.3, 17.0, {"alpha22": -1.0, "alpha13": 3.0})):
        th = math.radians(thd)
        dev = JP.Deviation(**kw)
        try:
            cur = JP.shadow_curve(chi, th, dev, 1441)
        except ValueError as e:
            out.append(f"chi={chi} th={thd} {kw}: shadow_curve refused: {e}")
            continue
        cx = 0.5 * (np.max(cur["alpha"]) + np.min(cur["alpha"]))
        worst = 0.0
        for ang in np.linspace(0.05, 2 * math.pi - 0.05, 12):
            e1 = edge_along(ang, cx, th, chi, dev)
            e2 = poly_radius(cur, cx, ang)
            worst = max(worst, abs(e1 - e2) / e2)
        out.append(f"chi={chi} th={thd} {kw}: max rel |edge(fate) - edge(curve)| over 12 directions = {worst:.2e} "
                   f"(fate: grid + refined minimum of R; polygon of 1441 points)")
    out.append("")
    out.append("== (c) regularity: check_regular vs Johannsen 2013a Eqs. 72 and 76 ==")
    for chi in (0.0, 0.6, 0.9, 0.998):
        rp = 1 + math.sqrt(1 - chi * chi)
        r = rp * np.exp(np.linspace(0.0, math.log(1e3), 40001))
        for kw in ({"alpha22": 10.0}, {"alpha22": 5.0}, {"alpha22": 2.0}, {"alpha22": 1.5}, {"alpha12": 10.0},
                   {"alpha13": 10.0}, {"alpha13": -0.95 * rp ** 3}, {"alpha12": -0.95 * rp ** 2}):
            dev = JP.Deviation(**kw)
            try:
                JP.check_regular(chi, dev)
                reg = "passes"
            except ValueError:
                reg = "refuses"
            det = dev.A1(r) * (r * r + chi * chi) - chi * chi * dev.A2(r)  # Eq. 72 at sin^2 = 1
            dl = r * r - 2 * r + chi * chi
            ctc = dev.A1(r) ** 2 * (r * r + chi * chi) ** 2 - chi * chi * dl  # Eq. 76 at sin^2 = 1
            v72 = bool(np.any(det <= 0))
            v76 = bool(np.any(ctc <= 0))
            if reg == "passes" and (v72 or v76):
                try:
                    cur = JP.shadow_curve(chi, math.radians(60), dev, 721)
                    d = JP.shadow_size(cur)["delta"]
                    sh = f"shadow_curve returns a curve, delta = {d:.4f}"
                except Exception as e:  # noqa: BLE001
                    sh = f"shadow_curve: {type(e).__name__}: {e}"
                out.append(f"chi={chi} {kw}: check_regular {reg}; Eq.72 violated: {v72} (min {det.min():.3g} at r = "
                           f"{r[np.argmin(det)]:.4g}); Eq.76 violated: {v76}; {sh}")
            else:
                out.append(f"chi={chi} {kw}: check_regular {reg}; Eq.72 violated: {v72}; Eq.76 violated: {v76}")
        out.append(f"   chi={chi}: Eq. 72 at alpha12 = alpha13 = 0 needs alpha22 < r+^4/a^2 = "
                   f"{(rp ** 4 / chi ** 2) if chi else float('inf'):.4g}")
    out.append("")
    out.append("== (d) the size measure: module centre vs CHARM centre; Kerr delta range ==")
    for chi, thd in ((0.5, 30.0), (0.9, 17.0), (0.9, 60.0), (0.998, 60.0), (0.998, 90.0), (0.9999, 90.0)):
        cur = KN.critical_curve(chi, math.radians(thd), 1441)
        s = JP.shadow_size(cur)
        dc, c = charm_delta(cur)
        out.append(f"Kerr chi={chi} th={thd}: delta module {s['delta']:+.5f} (centre {s['center_alpha']:.4f}); CHARM "
                   f"centre ({c[0]:.4f}, {c[1]:.1e}) delta {dc:+.5f}; diff {dc - s['delta']:+.1e}")
    lo, hi = 1.0, -1.0
    for chi in (0.0, 0.2, 0.5, 0.8, 0.9, 0.95, 0.99, 0.998):
        for thd in (1.0, 17.0, 30.0, 45.0, 60.0, 75.0, 90.0):
            d = JP.delta(chi, math.radians(thd))
            lo, hi = min(lo, d), max(hi, d)
    out.append(f"Kerr delta over chi in [0, 0.998], theta in [1, 90] deg: [{lo:+.4f}, {hi:+.4f}] "
               f"(Paper VI: 'values of delta in the range [-0.075, 0] are consistent with the Kerr predictions')")
    print("\n".join(out))


if __name__ == "__main__":
    main()
