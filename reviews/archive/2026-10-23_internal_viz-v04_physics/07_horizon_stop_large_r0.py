"""07: the horizon stop of a radial fall from a large start radius.

The radial scheme integrates rho = r/r0 in s = tau/r0^{3/2}. The last stretch of the fall, from r = 2M + a few 1e-4 M
to the stop at 2M + 2e-6 M, lasts ~1e-4 M of proper time, i.e. Delta s ~ 1e-4 / r0^{3/2}; once this is below the
spacing of doubles near s ~ 1 (2.2e-16), the stop cannot be resolved: expected from r0^{3/2} ~ 1e-4/2e-16 ~ 5e8,
r0 ~ 6e5 ... 5e6 M. Shown: the radius of the stop event in the engine, and what the run (Harness) shows after it
(r, the static observer's speed v, dtau/dt, 1 - dtau/dt), and whether any check notices.
"""
import math

import numpy as np

from harness import Harness
from lfphys.core.gravity import orbit_stream as osm

print("engine: radial fall from rest, stop event radius (nominal r - 2M = 2.000002e-06 M)")
for r0 in (1e3, 1e4, 1e5, 1e6, 3e6, 1e7, 3e7, 1e8):
    st = osm.OrbitStream(r0, 0.0, 0.0)
    evs = []
    while not st.done:
        evs += st.advance(1e300, 2.0)["events"]
    e = evs[-1]
    print(f"  r0 = {r0:8.0e}: {e['kind']:8s} r - 2M = {e['r'] - 2:+.6e} M, v_r = {e['v_r']:+.12f} c")

print("\nengine: the same in chunks ended by a coordinate-time event (as the run calls it)")
for r0 in (1e6, 1e7, 1e8):
    st = osm.OrbitStream(r0, 0.0, 0.0)
    t, evs = 0.0, []
    step = 2 * math.pi * r0**1.5 / 8
    while not st.done:
        t += step
        evs += st.advance(t, 2.0)["events"]
    e = evs[-1]
    print(f"  r0 = {r0:8.0e}: {e['kind']:8s} r - 2M = {e['r'] - 2:+.6e} M, v_r = {e['v_r']:+.12f} c")

print("\nthe run (Harness, preset 'radial' with r0 changed): what the frame shows after the stop")
for r0 in (20.0, 1e6, 1e7, 1e8):
    h = Harness("v04_orbits", "radial", {"r0": r0})
    te = h.sim.track.next_event_after(0.0, {"horizon"})
    h.run_to(1.001 * te * h.sim.T_s)
    h.runner._frame(1.0)
    f = h.of("frame")[-1]
    ev = [m for m in h.of("event") if m.get("kind") == "horizon"]
    ch = {m["id"].split(".")[1]: m for m in h.checks().values()}
    print(f"  r0 = {r0:8.0e}: frame r = {f['r']!r}, v = {f['v']!r} c, dtau/dt = {f['rate']!r}, 1 - dtau/dt = "
          f"{f['deficit']!r}, grav = {f['grav']!r}, kin = {f['kin']!r}")
    print(f"      event text: {ev[0]['text'][:90] if ev else None}")
    print(f"      checks: " + ", ".join(f"{k}: rel={c['rel']!r} ok={c.get('ok')}" for k, c in ch.items()))
    lag = np.concatenate([b["lag"] for m, b in h.msgs if m.get("type") == "trail"])
    rr = np.concatenate([b["r"] for m, b in h.msgs if m.get("type") == "trail"])
    print(f"      trail: min r = {rr.min()!r}, max 1 - dtau/dt = {lag.max()!r}")
