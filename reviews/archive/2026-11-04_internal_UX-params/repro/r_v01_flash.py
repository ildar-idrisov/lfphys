"""v01: the observers' flashes in the presets measure_c_lab and andromeda, as audit combinations #146 and #116 did them
(8 frames at the preset's speed, the action, 8 frames, next event, the action again, 8 frames): the events and checks
the player shows."""
import sys
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness

for preset, obj in (("measure_c_lab", "obs1"), ("measure_c", "obs1"), ("andromeda", "earth")):
    h = Harness("v01_light_travel", preset=preset)
    sp = h.runner.speed
    def frames(n):
        for _ in range(n):
            h.run_to(h.sim.t + sp / 20.0)
    frames(8); h.action("flash", obj=obj); frames(8); h.cmd("next_event"); h.action("flash", obj=obj); frames(8)
    h.run_to(h.sim.t + 20 * sp)
    print(f"== preset {preset}, flash by {obj}")
    for m in h.of("event"):
        if "измерено" in (m.get("text") or "") or m.get("kind") == "action":
            print(f"   t={m['t']:.6g} {m.get('text')}")
    for c in h.checks().values():
        bad = c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > max(c.get("tol") or 1e-9, 1e-12))
        if bad and not c.get("info"):
            print(f"   FAILED {c['id']}: {c['label']} value {c['value']!r} ref {c['ref']!r} rel {c['rel']:.3g} tol {c.get('tol')}")
