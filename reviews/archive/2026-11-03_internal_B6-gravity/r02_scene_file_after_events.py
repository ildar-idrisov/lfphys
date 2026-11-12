# Reviewer script (B6 gravity): the scene file and edits after a merger (Newton) and after a capture (Kerr), and the
# observers' clocks across a scene file.  p01_gravity.viz: NewtonMode.object_state / on_add / on_set,
# KerrMode.object_state / on_add (observers).
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from p01_gravity.viz import YR  # noqa: E402


def run(h, t_end, n=200):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


print("=== Newton: a star at rest and a test body (total energy exactly 0): the running checks ===")
h = Harness("p01_gravity", None, {"laws": "newton", "scene": {"format": "lfscene", "version": 1, "objects": [
    {"type": "star", "label": "S", "values": {"mass": 1.0}},
    {"type": "test", "label": "T", "values": {"x": 2.0}}]}})
try:
    run(h, 0.5 * YR, 50)
    print("ran without error; checks:", {k: c.get("ok") for k, c in h.checks().items()})
except Exception as exc:  # noqa: BLE001
    print("the frame raised:", type(exc).__name__, exc)
print()
print("=== Newton: two stars merge, then the scene is exported and loaded again ===")
params = {"laws": "newton", "collisions": "merge", "scene": {"format": "lfscene", "version": 1, "objects": [
    {"type": "star", "label": "A", "values": {"mass": 1.0, "radius": 1.0}},
    {"type": "star", "label": "B", "values": {"mass": 0.5, "radius": 1.0, "x": 0.2}},
    {"type": "star", "label": "C (far, keeps E != 0)", "values": {"mass": 0.1, "radius": 1.0, "x": 30.0}}]}}
h = Harness("p01_gravity", None, params)
nb = h.sim.mode.nb
M0, P0 = nb.total_mass(), nb.momentum().copy()
run(h, 0.2 * YR, 100)
print("merges:", [e["text"] for e in h.of("event") if e.get("kind") == "merge"])
print(f"after the merger: keys {nb.keys}, engine mass {nb.total_mass():.6g} Msun (before {M0:.6g}), "
      f"radius {nb.radii()[0]:.6g} au")
h.cmd("scene", op="export")
sc = h.of("scene_export")[-1]["scene"]
print("exported objects:", [(o["label"], o["values"]["mass"], o.get("state")) for o in sc["objects"]])
h2 = Harness("p01_gravity", None, {**sc["laws"], "scene": sc})
nb2 = h2.sim.mode.nb
print(f"reloaded: keys {nb2.keys}, engine mass {nb2.total_mass():.6g} Msun (should be {nb.total_mass():.6g}), "
      f"radius {nb2.radii()[0]:.6g} au (was {nb.radii()[0]:.6g})")
# an edit of the colour of the merged body
r_before = nb.radii()[0]
h.cmd("scene", op="set", id=nb.keys[0], values={"color": "#ff6b6b"})
print(f"colour changed: radius {r_before:.6g} -> {h.sim.mode.nb.radii()[0]:.6g} au; "
      f"mass {h.sim.mode.nb.total_mass():.6g}")
# duplicate the merged body
h.cmd("scene", op="duplicate", id=nb.keys[0], values={"x": 3.0})
print("duplicate of the merged body: masses", h.sim.mode.nb.masses().tolist())

print()
print("=== Kerr: a body captured, then the scene exported and loaded again ===")
h = Harness("p01_gravity", "kerr_orbits")
run(h, 200 * h.sim.mode.T, 100)
geo = h.sim.mode.geo
caps = [e for e in h.of("event") if e.get("kind") == "captured"]
print("captured:", [e["text"][:60] for e in caps])
print("status:", dict(zip(geo.keys, geo.status())))
h.cmd("scene", op="export")
sc = h.of("scene_export")[-1]["scene"]
for o in sc["objects"]:
    if o.get("state") and o["type"] == "body":
        print(f"  {o['label']}: state r = {o['state']['r']!r}, r_+ + capture_eps = "
              f"{geo.r_plus + geo.capture_eps!r}")
try:
    h2 = Harness("p01_gravity", None, {**sc["laws"], "scene": sc})
    g2 = h2.sim.mode.geo
    print("reloaded: status", dict(zip(g2.keys, g2.status())))
    run(h2, h2.sim.t + 1 * h2.sim.mode.T, 5)
    print("after 1 M: status", dict(zip(g2.keys, g2.status())), "events",
          [e["text"][:50] for e in h2.of("event")])
except Exception as exc:  # noqa: BLE001
    print("reloading the scene FAILED:", type(exc).__name__, exc)

print()
print("=== Kerr: an observer's clock across a scene file ===")
h = Harness("p01_gravity", "kerr_orbits")
run(h, 300 * h.sim.mode.T, 30)
pr = h.of("frame")[-1]["probes"]
print("before export: o6 clock tau =", pr["o6"]["часы наблюдателя τ, с"], "s; distant t =", pr["o6"]["часы далёкого t, с"])
h.cmd("scene", op="export")
sc = h.of("scene_export")[-1]["scene"]
print("observer entries in the file:", [(o["label"], o.get("state")) for o in sc["objects"] if o["type"] == "observer"])
# drop the captured body (its reload may fail, see above) to isolate the clocks
sc2 = dict(sc)
sc2["objects"] = [o for o in sc["objects"] if not (o["type"] == "body" and o["label"] == "Падает")]
h2 = Harness("p01_gravity", None, {**sc["laws"], "scene": sc2})
run(h2, h2.sim.t + 1e-9, 1)
pr2 = h2.of("frame")[-1]["probes"]
k6 = [o["id"] for o in h2.sim.objects.values() if o["label"].startswith("Неподвижный")][0]
print("after reload: clock tau =", pr2[k6]["часы наблюдателя τ, с"], "s; distant t =", pr2[k6]["часы далёкого t, с"])

print()
print("=== Kerr: an observer added at t > 0 is drawn where? ===")
h = Harness("p01_gravity", None, {"laws": "kerr", "m_hole": 10.0, "spin": 0.9, "charge": 0.0, "scene": {
    "format": "lfscene", "version": 1, "objects": []}})
run(h, 500 * h.sim.mode.T, 10)
h.cmd("scene", op="add", type="observer", values={"kind": "circular", "r": 6.0, "phi": 0.0})
run(h, h.sim.t + 1e-6 * h.sim.mode.T, 1)
fr = h.of("frame")[-1]
fb = [m for m, b in h.msgs if m.get("type") == "frame"][-1]
blobs = [b for m, b in h.msgs if m.get("type") == "frame"][-1]
pos = np.asarray(blobs["pos"]).reshape(-1, 3)
i = fr["ids"].index("o1")
ph = math.degrees(math.atan2(pos[i, 1], pos[i, 0]))
from lfphys.core.gravity import kerr_newman as KN  # noqa: E402
Om = float(KN.circular_orbit(6.0, 0.9, 0.0, True)["Omega"])
tm = h.sim.mode.t_m()
print(f"observer added at t = {tm:.6g} M with phi = 0 deg is drawn at phi = {ph:.2f} deg; "
      f"Omega t = {math.degrees(Om * tm) % 360:.2f} deg (mod 360), Omega = {Om:.6f}: it is drawn where it would be "
      f"had it been placed at t = 0, not at the phi it was given")
