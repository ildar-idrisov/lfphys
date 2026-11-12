# Reviewer script (B6 gravity): p01's "observer on a circular orbit (free fall)" is not integrated - its clock rate and
# position are those of the circular geodesic - and it is accepted inside the ISCO, where that orbit is unstable
# (a body placed there leaves it). a = 0.9: ISCO 2.32, prograde photon orbit 1.56.
import sys

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from lfphys.core.gravity import kerr_newman as KN  # noqa: E402


def run(h, t_end, n=50):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


print(f"a = 0.9: ISCO {KN.isco(0.9, 0.0):.4f}, prograde photon orbit {KN.photon_orbit(0.9, 0.0):.4f}")
h = Harness("p01_gravity", None, {"laws": "kerr", "m_hole": 10.0, "spin": 0.9, "charge": 0.0, "scene": {
    "format": "lfscene", "version": 1, "objects": [
        {"type": "observer", "label": "obs r=2", "values": {"kind": "circular", "r": 2.0, "phi": 0.0}},
        {"type": "body", "label": "body r=2", "values": {"r": 2.0, "vmode": "circular"}}]}})
run(h, 300 * h.sim.mode.T, 60)
pr = h.of("frame")[-1]["probes"]
g = h.sim.mode.geo
print("observer accepted at r = 2 (inside the ISCO): clock rate", pr["o1"]["ход dτ/dt"])
print("the body started on the same circular orbit after 300 M:", g.status(), "r =", g.bl()[:, 0].tolist(),
      "events", [e["text"][:50] for e in h.of("event")])
