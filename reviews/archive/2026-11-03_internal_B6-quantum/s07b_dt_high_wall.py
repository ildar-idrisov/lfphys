"""Q (continuation of s07): the wrapper's argument for ignoring barriers above the particle's energy ("seen only by
evanescent tails"). The double-slit preset with the wall at 3 eV (preset), 30 eV and 300 eV: the wrapper's dt does
not change (it ignores the wall); the global error ||psi - psi_ref|| at t = 12 units (reference: Richardson from dt/8
and dt/16), the companion's accumulated estimate, and the wall's phase per step V dt."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core.quantum import scene as QS
from p02_quantum import viz as P

T1 = 12.0
for V in (3.0, 30.0, 300.0):
    pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
    for o in pr["scene"]["objects"]:
        if o["type"] == "packet":
            o["values"]["bohm"] = 0
        if o["type"] == "slit_wall":
            o["values"]["V"] = V
    h = Harness("p02_quantum", None, pr)
    st0 = h.sim.qs.state_dict()
    dt_w = st0["dt"]
    res = {}
    for name, dt in (("wrapper", dt_w), ("ref8", dt_w / 8), ("ref16", dt_w / 16)):
        s = QS.Scene.from_state_dict(copy.deepcopy(st0))
        s.set_dt(dt)
        n = int(round(T1 / dt))
        step = max(1, int(round(0.25 / dt)))
        s.step_error()
        k = 0
        while k < n:
            m = min(step, n - k)
            s.advance(m)
            k += m
            s.step_error()
        res[name] = (s.wave(1), s.checks()[1]["step_error"]["accumulated"])
        g = s.grid
    ref = res["ref16"][0] + (res["ref16"][0] - res["ref8"][0]) / 3
    err = math.sqrt(g.norm(res["wrapper"][0] - ref))
    print(f"wall {V:5.0f} eV: wrapper dt {dt_w} (wall phase per step {V / P.EV * dt_w:.2f} rad): "
          f"||psi - psi_ref|| at t = {T1}: {err:.2e}; companion's estimate {res['wrapper'][1]:.2e}; "
          f"ref16 vs ref8 {math.sqrt(g.norm(res['ref16'][0] - res['ref8'][0])):.1e}")
