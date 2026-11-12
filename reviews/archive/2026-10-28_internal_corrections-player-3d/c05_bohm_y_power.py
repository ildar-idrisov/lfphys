"""C1 review, check 05: can the new check «Попадания частиц Бома по y против картины P(x, y)» (bohm_y, v11/v12) detect
a wrong y-motion of the Bohm particles?

A world is run to its end offline (CPU). Then the check's own statistic (Kolmogorov-Smirnov distance between the
hits' y and the y-marginal of the screen's flux, evaluated at the run's y bin edges, critical value 1.95/sqrt(n)) is
recomputed for the hits the run produced (the check as shipped) and for two wrong y-motions of the same particles:
  "no spreading"   y(t) = y0                (the y-factor ignored)
  "double spread"  y(t) = y0 (2 sigma_y(t)/sigma_y0 - 1)
and for the hits' y with sigma_y(t) off by 10 %. Also printed: sigma_y(t) / sigma_y0 at the mean hit time.

Run: docker run --rm --name lf-c1rev-c05 -v <engine>:/lf:ro -v <this folder>:/rev -w /lf/visualizations \
         light-funnel-viz python3 /rev/c05_bohm_y_power.py [small|default|v12]
Output: /rev/out/c05_bohm_y_power_<case>.txt
"""
import math
import sys
import time

import numpy as np

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from lfviz import registry  # noqa: E402

CASES = {
    "small": ("v11_double_slit_2d", {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0,
                                     "grid": "coarse", "n_bohm": 2000, "n_tracks": 10}),
    "default": ("v11_double_slit_2d", {}),
    "v12": ("v12_arrival_times_2d", {}),
}


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "small"
    vid, vals = CASES[case]
    viz = registry.load(vid)
    params, errs = viz["schema"].resolve(None, vals)
    assert not errs, errs
    checks = {}

    def emit(meta, blobs=None):
        if meta.get("type") == "check":
            checks[meta["id"]] = meta
    sim = viz["simulation"](params, 11, emit)
    sim.header()
    sim.after_header()  # the world buffers its messages until its header is out
    sim.advance(0.0)
    t0 = time.time()
    t = 0.0
    while not sim.done and time.time() - t0 < 3000:
        t += sim.default_speed / 4
        sim.advance(t)
    sim.advance(sim.t + sim.default_speed)  # reveal what the end computed (messages wait for the run's time)
    try:
        sim.frame()
    except Exception:  # noqa: BLE001
        pass
    out = [f"{vid} ({case}): params {vals or 'defaults'}; done {sim.done} after {time.time() - t0:.0f} s wall, "
           f"world t {sim.t:.4g} s"]
    for k in ("screen_y", "bohm_y"):
        c = checks.get(k)
        out.append(f"  shipped check {k}: " + (f"value {c['value']:.4g}, ok {c.get('ok')}; {c.get('note', '')[:160]}"
                                                 if c else "not emitted"))
    hit = sim.fate == 1
    n = int(hit.sum())
    y0 = sim.Y0[hit]
    ty = sim.hit_t[hit] / sim.tunit  # computation time of each hit
    sy = sim.sy
    st = sy * np.sqrt(1.0 + (ty / (2 * sy * sy)) ** 2)
    out.append(f"  hits n = {n}; sigma_y0 = {sy:g} lambda; sigma_y(t_hit)/sigma_y0: mean {np.mean(st / sy):.4f}, "
               f"range {np.min(st / sy):.4f}-{np.max(st / sy):.4f}")
    dy = 2 * sim.y_half / len(sim.y_screen)
    Py = np.clip(sim.flux_xy, 0, None).sum(axis=0)
    F = np.cumsum(Py) / Py.sum()
    edges = sim.y_screen + 0.5 * dy
    crit = 1.95 / math.sqrt(n)

    def D(y):
        emp = np.searchsorted(np.sort(y), edges, side="right") / len(y)
        return float(np.max(np.abs(emp - F)))
    rows = [("as shipped (hit_y)", sim.hit_y[hit]), ("no spreading: y = y0", y0),
            ("sigma_y(t) 10 % too small", y0 * (1 + 0.9 * (st / sy - 1))),
            ("sigma_y(t) 10 % too large", y0 * (1 + 1.1 * (st / sy - 1))),
            ("double spread", y0 * (2 * st / sy - 1))]
    for lab, y in rows:
        d = D(y)
        out.append(f"  KS D = {d:.4f} vs critical {crit:.4f} -> {'passes' if d < crit else 'FAILS'}: {lab}")
    with open(f"/rev/out/c05_bohm_y_power_{case}.txt", "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


main()
