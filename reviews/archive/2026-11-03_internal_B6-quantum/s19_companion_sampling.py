"""Q: the companion's accumulated error (trapezoid over local estimates taken only when the checks run) is called
"rigorous" (STATUS V39 c, README "rigorous bound"). The wrapper runs the checks every CHECK_FRAMES = 20 frames at 20
fps, i.e. once per wall second: every 2.55 units of scene time at the double-slit preset's default speed, every 25.5
at 10x speed. The double-slit preset's scene (wrapper-built, no Bohm points), the true global error at t = 12 (as
s07: Richardson reference from dt/16, dt/32 — taken from s07's run here by recomputing dt/16, dt/32) against the
accumulated estimate with estimates every 0.25, 2.55 and 25.5 units (the last: only at t = 0 and the end)."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core.quantum import scene as QS
from p02_quantum import viz as P

pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
for o in pr["scene"]["objects"]:
    if o["type"] == "packet":
        o["values"]["bohm"] = 0
h = Harness("p02_quantum", None, pr)
st0 = h.sim.qs.state_dict()
dt = st0["dt"]
T1 = 12.0
print(f"default speed: {h.sim.default_speed / P.TU:.3f} units of scene time per wall second")


def run(dt_, every):
    s = QS.Scene.from_state_dict(copy.deepcopy(st0))
    s.set_dt(dt_)
    n = int(round(T1 / dt_))
    step = max(1, int(round(every / dt_)))
    s.step_error()
    k = 0
    while k < n:
        m = min(step, n - k)
        s.advance(m)
        k += m
        s.step_error()
    return s


r16, r32 = run(dt / 16, 1e9).wave(1), run(dt / 32, 1e9).wave(1)
ref = r32 + (r32 - r16) / 3
for every in (0.25, 2.55, 25.5):
    s = run(dt, every)
    g = s.grid
    true = math.sqrt(g.norm(s.wave(1) - ref))
    print(f"estimates every {every:5.2f} units: accumulated {s.checks()[1]['step_error']['accumulated']:.2e}; "
          f"true global error {true:.2e}")
