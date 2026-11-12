# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review B5, check c06: v15's live check `edge` (tolerance 64 eps, "round-off of the roots") over a dense scan of
# worlds: the same computation as viz.Simulation._shadow_checks (8 directions k pi/4 from the screen origin,
# capture_boundary with rho_max = 18 against critical_radius_at), for spins chi up to the slider's 0.998 and
# inclinations 1..179 deg in steps of 1 deg. Lists every world whose value exceeds 64 eps (a correct run the check
# would mark failed) and, for the worst one, the unit test's derived tolerance (test_kerr_shadow: e_d/|d d34/d rho|
# + 1e-13 rho + 2u rho + bracket) for comparison.
#
# Root: engine at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this script in
# /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/. CPU. Run as c02 (see its header).
import math
from multiprocessing import Pool

import numpy as np

from lfphys.core.gravity import kerr_null as KN, kerr_shadow as KS

EPS = np.finfo(float).eps
U = 2.0 ** -53


def edge_value(args):
    chi, incl = args
    th = math.radians(incl)
    worst, wk = 0.0, None
    for k in range(8):
        ang = 2.0 * math.pi * k / 8
        lo, hi = KS.capture_boundary(chi, th, ang, rho_max=3.0 * 6.0)
        rho_c, _ = KN.critical_radius_at(chi, th, ang)
        v = abs(0.5 * (lo + hi) - rho_c) / rho_c
        if v > worst:
            worst, wk = v, k
    return chi, incl, worst, wk


def derived_tol(chi, incl, k):
    """The unit test's tolerance for this direction, relative to rho_c."""
    th = math.radians(incl)
    ang = 2.0 * math.pi * k / 8
    rc, _ = KN.critical_radius_at(chi, th, ang)
    lo, hi = KS.capture_boundary(chi, th, ang, rho_max=18.0)
    ca, sa = math.cos(ang), math.sin(ang)

    def d34(rho):
        lam, eta = KN.screen_to_constants(np.array([rho * ca]), np.array([rho * sa]), th, chi)
        ro = KN.radial_roots(lam, eta, chi)
        A, B, z = ro["A"][0], ro["B"][0], ro["z"][0]
        return float(-A / 2 - z * z - B / (4 * z)), float(16 * U * (abs(A) / 2 + z * z + abs(B) / (4 * z)))
    h = 1e-6
    d1, e1 = d34(rc + h)
    d0, _ = d34(rc - h)
    slope = abs(d1 - d0) / (2 * h)
    return (e1 / slope + 1e-13 * rc + 2 * U * hi + (hi - lo)) / rc


def main():
    grid = [(chi, float(incl)) for chi in (0.9, 0.95, 0.98, 0.99, 0.995, 0.998) for incl in range(1, 180)]
    with Pool(12) as pool:
        res = pool.map(edge_value, grid)
    out = []
    bad = [r for r in res if r[2] > 64 * EPS]
    out.append(f"worlds {len(res)}; edge value > 64 eps ({64 * EPS:.3e}) in {len(bad)}")
    for chi, incl, v, k in sorted(bad, key=lambda r: -r[2])[:25]:
        out.append(f"  chi={chi} incl={incl}: edge = {v:.3e} (direction k = {k}); derived tolerance of the unit test "
                   f"{derived_tol(chi, incl, k):.3e}")
    top = sorted(res, key=lambda r: -r[2])[:5]
    out.append("largest values: " + "; ".join(f"chi={c} incl={i}: {v:.2e}" for c, i, v, _ in top))
    hist = np.histogram([r[2] / EPS for r in res], bins=[0, 4, 8, 16, 32, 64, 128, 256, 1e9])
    out.append("distribution of edge/eps: " + ", ".join(f"[{a:g},{b:g}): {n}" for a, b, n in
                                                       zip(hist[1][:-1], hist[1][1:], hist[0])))
    print("\n".join(out))


if __name__ == "__main__":
    main()
