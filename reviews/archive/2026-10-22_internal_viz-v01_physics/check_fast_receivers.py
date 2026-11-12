"""Arrivals at fast receivers: GR (quadrature + fixed point) and Newtonian corpuscles (Kepler + fixed point),
compared with flat SR (exact quadratic) as a sanity reference for the expected existence of an arrival.
Reviewer script (2026-10-22).

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_fast_receivers.py
"""
import argparse
import sys

sys.path.insert(0, "/lf/visualizations/tests")  # root path: the light-funnel tree mounted at /lf in the container
from harness import Harness  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__)
ap.parse_args()
for preset in ("lensing", "lensing_newton"):
    for beta, ang in ((0.5, 0.0), (0.7, 0.0), (0.9, 0.0), (0.9, 90.0), (0.9, 180.0)):
        h = Harness("v01_light_travel", preset)
        h.action("boost", obj="obs", v=beta, unit="c", angle=ang)
        h.action("flash", obj="src")
        w = h.sim.world
        n_pending = sum(1 for p in w.pending if not p.ev.get("cancelled") and p.ev["kind"] == "arrival"
                        and p.ev["obj"] == "obs")
        print(f"{preset:15s} obs boosted {beta}c at {ang:5.1f} deg, then src flashes: scheduled arrivals at obs = "
              f"{n_pending}")
