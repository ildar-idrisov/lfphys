"""Edge case: a flash emitted exactly where (and when) other observers are (measure_c, flash by obs1 at t = 0,
when all three observers and the A ends of their rods coincide at the origin). Reviewer script (2026-10-22).

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_colocated_flash.py
"""
import argparse
import sys

sys.path.insert(0, "/lf/visualizations/tests")  # root path: the light-funnel tree mounted at /lf in the container
from harness import Harness  # noqa: E402

from v01_light_travel.engine.consts import C  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__)
ap.parse_args()
for preset in ("measure_c", "measure_c_ether", "measure_c_emission"):
    h = Harness("v01_light_travel", preset)
    h.action("flash", obj="obs1")
    h.run_to(0.05)
    print(preset)
    for e in h.of("event"):
        if e["kind"] == "arrival" and e["pulse"] == "p1":
            print(f"  arrival {e['obj']} t = {e['t']:.3g}, dir = {e['data']['dir']}")
    for c in h.checks().values():
        if "p1" in c["id"]:
            print(f"  check {c['label']}: {c['value'] / C if c['unit'] == 'м/с' else c['value']:.12g}"
                  f"{' c' if c['unit'] == 'м/с' else ''}, ref {c['ref'] if c['ref'] is None else (c['ref'] / C if c['unit'] == 'м/с' else c['ref'])}, rel {c['rel']}")
    print("  errors:", h.errors())
