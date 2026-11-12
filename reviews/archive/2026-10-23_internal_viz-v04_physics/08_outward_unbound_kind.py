"""08: kind of an orbit launched outward on an unbound path with no periapsis ahead (no turning point at smaller r).

OrbitStream._classify: r_peri is None -> 'plunge' before 'escape' is considered, regardless of the direction of
motion; NewtonTrack: r_peri <= r_stop -> 'plunge' regardless of the direction. A body moving outward with e >= 1
(Newton: E >= 0) and no apoapsis never comes back: it escapes. Shown: the run's kind, its text, and what actually
happens (the end event of the run).
"""
from harness import Harness

cases = [("GR", 5.0, 1.6, 30.0), ("GR", 3.5, 0.95, 45.0), ("GR", 2.5, 0.9, 10.0), ("GR", 20.0, 1.6, 89.0),
         ("newton", 20.0, 1.6, 89.9999), ("newton", 20.0, 1.5, 89.99999), ("newton", 20.0, 1.6, 30.0)]
for law, r0, k, ang in cases:
    h = Harness("v04_orbits", "default", {"gravity": law, "r0": r0, "speed": k, "angle": ang, "ghost": False})
    info = h.sim.info
    te = h.sim.track.next_event_after(0.0, {"horizon", "escape", "center", "surface"})
    h.run_to(1.0001 * te * h.sim.T_s if te else 10 * h.sim.track.dyn * h.sim.T_s)
    end = [e for e in h.of("event") if e.get("kind") in ("horizon", "escape", "center", "surface")]
    seg = h.of("event")[0]["text"]
    print(f"{law:6s} r0={r0:<5g} k={k:<5g} angle={ang:<9g}: kind = {info['kind']!r:10s} ({info['kind_text']}); "
          f"e^2-1 = {info.get('em1')}; end of the run: {end[0]['kind'] if end else None} at r = "
          f"{h.sim.track.end_event['r'] if h.sim.track.end_event else None}")
    print(f"      segment text: {seg[:160]}")
