"""Independent check of v01 engine/kepler.py (exact Newtonian corpuscle hyperbolae, modified physics "newton").

Reviewer script (2026-10-22). Reference: scipy solve_ivp DOP853 (rtol 1e-12) of x'' = -mu x/|x|^3 with events
at |x| = rT and |x| = r_abs; compared with kepler.crossings (time and position of every crossing) for
random unbound orbits of both senses of rotation, starting before and after periapsis, with and without
absorption; and connect_newton images re-shot with the same integrator.

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_kepler.py
"""
from __future__ import annotations

import argparse
import math

import numpy as np
from scipy.integrate import solve_ivp

from v01_light_travel.engine import kepler


def reference_crossings(r0, v0, mu, rT, r_abs, t_max):
    def rhs(t, y):
        x = y[:2]
        r3 = (x @ x) ** 1.5
        return [y[2], y[3], -mu * x[0] / r3, -mu * x[1] / r3]

    def ev_T(t, y):
        return math.hypot(y[0], y[1]) - rT

    def ev_abs(t, y):
        return math.hypot(y[0], y[1]) - r_abs

    ev_abs.terminal = True
    sol = solve_ivp(rhs, (0, t_max), [*r0, *v0], method="DOP853", rtol=1e-12, atol=1e-12 * np.linalg.norm(r0),
                    events=[ev_T, ev_abs])
    return [(t, y[:2]) for t, y in zip(sol.t_events[0], sol.y_events[0]) if t > 1e-12 * t_max]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    rng = np.random.default_rng(7)
    mu = 1.0
    worst_t = worst_x = 0.0
    n_ok = n_bad = 0
    for k in range(300):
        r0 = rng.uniform(-10, 10, 2)
        r = np.linalg.norm(r0)
        if r < 2:
            continue
        vesc = math.sqrt(2 * mu / r)
        v0 = rng.normal(size=2)
        v0 = v0 / np.linalg.norm(v0) * vesc * rng.uniform(1.05, 4.0)
        rT = rng.uniform(1.5, 20)
        r_abs = rng.uniform(0.05, 1.0)
        eng = kepler.crossings(r0, v0, mu, rT, r_abs)
        ref = reference_crossings(r0, v0, mu, rT, r_abs, t_max=200.0)
        if len(eng) != len(ref):
            n_bad += 1
            if n_bad <= 5:
                print(f"  count mismatch: r0={r0}, v0={v0}, rT={rT:.3f}, r_abs={r_abs:.3f}: engine {len(eng)}, "
                      f"reference {len(ref)}")
            continue
        for (te, xe, _), (tr, xr) in zip(eng, ref):
            worst_t = max(worst_t, abs(te - tr) / tr)
            worst_x = max(worst_x, np.linalg.norm(xe - xr) / rT)
        n_ok += 1
    print(f"crossings: {n_ok} random orbits agree in count; max rel time err {worst_t:.1e}, "
          f"max position err / rT {worst_x:.1e}; count mismatches: {n_bad}")

    # connect_newton images re-shot
    mu = 1.0
    o = np.array([-30.0, 1.5])
    sp = 1.0
    worst = 0.0
    for tgt in (np.array([30.0, 0.0]), np.array([10.0, 12.0]), np.array([-5.0, -20.0])):
        imgs = kepler.connect_newton(o, tgt, sp, np.zeros(2), mu, 0.3)
        for im in imgs:
            v0 = sp * np.array([math.cos(im["angle"]), math.sin(im["angle"])])
            ref = reference_crossings(o, v0, mu, np.linalg.norm(tgt), 0.3, t_max=10 * im["dt"])
            best = min(ref, key=lambda z: abs(z[0] - im["dt"]))
            worst = max(worst, np.linalg.norm(best[1] - tgt) / np.linalg.norm(tgt))
        print(f"  target {tgt}: {len(imgs)} image(s), dt = {[round(i['dt'], 9) for i in imgs]}")
    print(f"connect_newton: re-shot images hit the target to max rel {worst:.1e}")


if __name__ == "__main__":
    main()
