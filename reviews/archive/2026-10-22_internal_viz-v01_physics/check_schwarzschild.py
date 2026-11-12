"""Independent check of v01 engine/schwarzschild.py (connect, integrals, turning point, local directions).

Reviewer script (2026-10-22). Independent routes:
* mpmath tanh-sinh quadrature (30 digits) of the ORIGINAL integrands dphi/dr = b/(r^2 sqrt(g)),
  c dt/dr = 1/(f sqrt(g)) (no substitution), split at the turning point;
* shooting with scipy solve_ivp (DOP853, rtol 1e-12) of the second-order polar geodesic equations
  r'' = b^2/r^3 - 1.5 rs b^2/r^4, phi' = b/r^2, (ct)' = 1/f, started from the engine's emit_dir converted to
  (dr/dlam, b) in the local static frame, stopped at the target radius;
* turning point from numpy.roots of the cubic.

Run (from the light-funnel root):
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_schwarzschild.py
"""
from __future__ import annotations

import argparse
import math
import warnings

import mpmath as mp
import numpy as np
from scipy.integrate import solve_ivp

from v01_light_travel.engine import checks, schwarzschild as S

mp.mp.dps = 30


def mp_integrals(b, ra, rb, rs, rtp=None):
    """(dphi, c dt) from ra to rb (ra < rb) along a monotonic stretch, original integrands, tanh-sinh."""
    b, ra, rb, rs = (mp.mpf(x) for x in (b, ra, rb, rs))

    def g(r):
        return 1 - (1 - rs / r) * b * b / (r * r)

    fphi = lambda r: b / (r * r * mp.sqrt(g(r)))
    ft = lambda r: 1 / ((1 - rs / r) * mp.sqrt(g(r)))
    # geometric split points so that tanh-sinh sees moderate ranges
    pts = [ra]
    while pts[-1] * 4 < rb:
        pts.append(pts[-1] * 4)
    pts.append(rb)
    qp, qt = mp.quad(fphi, pts), mp.quad(ft, pts)
    # rounding at the turning point can give g = -1e-30: keep the real part, check the imaginary part is noise
    assert abs(mp.im(qp)) < mp.mpf(10) ** -12 * abs(qp) + mp.mpf(10) ** -20 and abs(mp.im(qt)) < mp.mpf(10) ** -12 * abs(qt)
    return mp.re(qp), mp.re(qt)


def mp_connection(b, r1, r2, rs, branch):
    if branch == "out":
        p, t = mp_integrals(b, r1, r2, rs)
    elif branch == "in":
        p, t = mp_integrals(b, r2, r1, rs)
    else:
        rtp = S.turning_point(b, rs)
        # refine the root in mpmath
        rtp = mp.findroot(lambda r: r**3 - mp.mpf(b) ** 2 * r + mp.mpf(b) ** 2 * rs, mp.mpf(rtp))
        p1, t1 = mp_integrals(b, rtp, r1, rs)
        p2, t2 = mp_integrals(b, rtp, r2, rs)
        p, t = p1 + p2, t1 + t2
    return float(p), float(t)


def shoot(P1, emit_dir, rs, r2, b_expected, lam_max):
    """Integrate the polar second-order geodesic equations from P1 along emit_dir (local static frame)."""
    r1 = math.hypot(*P1)
    ph1 = math.atan2(P1[1], P1[0])
    rhat = np.array(P1) / r1
    phat = np.array([-rhat[1], rhat[0]])
    nr, nphi = float(emit_dir @ rhat), float(emit_dir @ phat)
    f1 = 1 - rs / r1
    L = r1 * nphi / math.sqrt(f1)  # r^2 dphi/dlam with E = 1
    y0 = [r1, nr, ph1, 0.0]

    def rhs(lam, y):
        r, rd, ph, ct = y
        return [rd, L * L / r**3 - 1.5 * rs * L * L / r**4, L / r**2, 1.0 / (1.0 - rs / r)]

    def hit(lam, y):
        return y[0] - r2

    hit.terminal = False
    sol = solve_ivp(rhs, (0, lam_max), y0, method="DOP853", rtol=1e-13, atol=1e-12 * r1, events=hit,
                    dense_output=True)
    return L, sol


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    rs, c = 1.0, 1.0
    cases = [
        ("lens 60/60 offset", (-60.0, 0.5), (60.0, 0.0)),
        ("outward 10 -> 1000, 90 deg", (10.0, 0.0), (0.0, 1000.0)),
        ("inward 1000 -> 10, 90 deg", (0.0, 1000.0), (10.0, 0.0)),
        ("inward 50 -> 4, 170 deg", (50.0, 0.0), (4 * math.cos(math.radians(170)), 4 * math.sin(math.radians(170)))),
        ("near photon sphere 1.6 -> 1.6, 20 deg", (1.6, 0.0), (1.6 * math.cos(0.35), 1.6 * math.sin(0.35))),
        ("same radius 5 -> 5, 179.9 deg", (5.0, 0.0), (5 * math.cos(math.radians(179.9)), 5 * math.sin(math.radians(179.9)))),
        ("radial 5 -> 500", (5.0, 0.0), (500.0, 0.0)),
        ("radial in 500 -> 5", (500.0, 0.0), (5.0, 0.0)),
        ("far 1e6 <-> 1e6, 180 deg - 1e-6", (-1e6, 0.0), (1e6 * math.cos(1e-6), 1e6 * math.sin(1e-6))),
    ]
    worst = {"phi": 0.0, "t": 0.0, "shoot_phi": 0.0, "shoot_t": 0.0}
    print(f"{'case':40s} {'side':>4s} {'branch':>7s} {'b':>14s} {'dphi err':>10s} {'dt rel err':>11s} "
          f"{'shoot dphi':>10s} {'shoot dt':>10s}")
    for name, P1, P2 in cases:
        imgs = S.connect(P1, P2, rs, c, rs)
        r1, r2 = math.hypot(*P1), math.hypot(*P2)
        delta = (math.atan2(P2[1], P2[0]) - math.atan2(P1[1], P1[0])) % (2 * math.pi)
        for im in imgs:
            theta = delta if im["side"] > 0 else 2 * math.pi - delta
            if im["b"] == 0.0:
                ref_t = checks.radial_light_time(r1, r2, rs, c)
                p_mp, t_mp = 0.0, ref_t
            else:
                p_mp, t_mp = mp_connection(im["b"], r1, r2, rs, im["branch"])
            e_phi = abs(p_mp - theta)
            e_t = abs(t_mp - im["dt"]) / im["dt"] if im["dt"] else 0.0
            # shooting
            L, sol = shoot(P1, im["emit_dir"], rs, r2, im["b"], lam_max=4 * (r1 + r2) + 200)
            sp, st = math.nan, math.nan
            if sol.t_events[0].size:
                # choose the crossing whose time is closest to the engine's (first crossing for direct rays)
                best = None
                for lam_e, y_e in zip(sol.t_events[0], sol.y_events[0]):
                    dphi = abs(y_e[2] - math.atan2(P1[1], P1[0]))
                    cand = (abs(y_e[3] - im["dt"] * c), dphi, y_e[3])
                    if best is None or cand[0] < best[0]:
                        best = cand
                sp = abs(best[1] - theta)
                st = abs(best[2] - im["dt"] * c) / (im["dt"] * c)
            worst["phi"] = max(worst["phi"], e_phi)
            worst["t"] = max(worst["t"], e_t)
            if not math.isnan(sp):
                worst["shoot_phi"] = max(worst["shoot_phi"], sp)
                worst["shoot_t"] = max(worst["shoot_t"], st)
            print(f"{name:40s} {im['side']:4d} {im['branch']:>7s} {im['b']:14.9g} {e_phi:10.2e} {e_t:11.2e} "
                  f"{sp:10.2e} {st:10.2e}  (L/b-1 = {abs(L) / im['b'] - 1 if im['b'] else 0:.1e})")
        if not imgs:
            print(f"{name:40s}  NO IMAGES returned (r1={r1}, r2={r2}, 1.5 rs = {1.5 * rs})")
    print("worst:", worst)

    # --- turning point vs numpy roots ---------------------------------------------------------------------
    print("\nturning point vs numpy.roots (relative):")
    for b in [S.b_crit(rs) * (1 + 1e-12), S.b_crit(rs) * (1 + 1e-6), 3.0, 10.0, 1e3, 1e8]:
        rt = S.turning_point(b, rs)
        roots = np.roots([1, 0, -b * b, b * b * rs])
        rr = max(x.real for x in roots if abs(x.imag) < 1e-6 * abs(x))
        mp_rt = mp.findroot(lambda r: r**3 - mp.mpf(b) ** 2 * r + mp.mpf(b) ** 2 * rs, mp.mpf(rt))
        print(f"  b = {b:.12g}: engine {rt:.16g}  numpy {rr:.16g}  mpmath {mp.nstr(mp_rt, 18)}  "
              f"rel(engine-mp) = {float((rt - mp_rt) / mp_rt):.2e}")

    # --- integrals() near b_c ---------------------------------------------------------------------------
    # engine integrals with (a) its own turning point, (b) the turning point refined in 40-digit arithmetic and
    # rounded to double; reference: 40-digit tanh-sinh of the original integrand from the 40-digit root
    print("\nintegrals(b, rtp -> 100) near b_c: engine (own rtp), engine (mp-refined rtp), vs 40-digit mpmath:")
    for eps in [1e-3, 1e-6, 1e-9, 1e-11]:
        b = S.b_crit(rs) * (1 + eps)
        rtp = S.turning_point(b, rs)
        with mp.workdps(40):
            mp_rtp = mp.findroot(lambda r: r**3 - mp.mpf(b) ** 2 * r + mp.mpf(b) ** 2 * rs, mp.mpf(rtp))
            p_m, t_m = mp_integrals(b, mp_rtp * (1 + mp.mpf(10) ** -38), 100.0, rs)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            p_e, t_e = S.integrals(b, rtp, 100.0, rs, c, rtp)
            p_f, t_f = S.integrals(b, float(mp_rtp), 100.0, rs, c, float(mp_rtp))
        print(f"  eps = {eps:.0e}: rtp rel err {float((rtp - mp_rtp) / mp_rtp):+.2e};"
              f" dphi rel err own-rtp {abs(p_e / float(p_m) - 1):.2e}, refined-rtp {abs(p_f / float(p_m) - 1):.2e};"
              f" dt rel err own-rtp {abs(t_e / float(t_m) - 1):.2e}; quad warnings: {len(w)}")

if __name__ == "__main__":
    main()
