"""Independent check of the observer 'now' (World._now_at) and 'seen' (World._seen) at Andromeda distances,
against closed forms derived here:
  now (SR):  t_q = t + v (x_q - x_o(t)) / c^2      (static q at x_q, observer at x_o(t) with velocity v along x)
  now (Galilean): t_q = t
  seen (static q): t_e = t - |x_o(t) - x_q| / c   (SR, ether);  emission: same for a static source.
The 'now' offsets are also compared with checks.simultaneity_offset and the frame matrix row.

Reviewer script (2026-10-22).

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_simultaneity.py
"""
from __future__ import annotations

import argparse
import sys

sys.path.insert(0, "/lf/visualizations/tests")  # root path: the light-funnel tree mounted at /lf in the container
from harness import Harness  # noqa: E402

from v01_light_travel.engine.consts import C, DAY, LIGHT_YEAR  # noqa: E402

V = "v01_light_travel"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    for preset, params in (("andromeda", {}), ("andromeda_fast", {}), ("andromeda", {"kinematics": "ether"}),
                           ("andromeda", {"kinematics": "emission"})):
        h = Harness(V, preset, params)
        c = h.sim.laws.c
        D = h.params["an_dist_mly"] * 1e6 * LIGHT_YEAR
        worst_now = worst_seen = 0.0
        for t in (0.0, 1e9, 3.3e13, 7.0e13):
            h.run_to(t)
            meta, _ = h.sim.frame()
            for oid in ("walk_to", "walk_from", "stay"):
                o = h.sim.world.objects[oid]
                xo = o.wl.pos(t)[0]
                v = o.wl.vel(t)[0]
                ref_now = t + (v * (D - xo) / c**2 if h.sim.laws.kinematics == "SR" else 0.0)
                got = meta["now_at"][oid]["andromeda"]
                worst_now = max(worst_now, abs(got - ref_now))
                s = meta["seen"][oid]["andromeda"]
                ref_seen = t - abs(xo - D) / c
                worst_seen = max(worst_seen, abs(s[0] - ref_seen))
        print(f"{preset} {params}: max |now_at - closed form| = {worst_now:.3e} s "
              f"({worst_now / DAY:.2e} d); max |seen t_e - closed form| = {worst_seen:.3e} s")


if __name__ == "__main__":
    main()
