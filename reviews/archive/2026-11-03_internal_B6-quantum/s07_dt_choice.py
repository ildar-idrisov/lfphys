"""Q: the wrapper's time step ignores barriers above the particle's energy (viz.py _tune_dt; README: "for the double
slit's 3 eV wall that would be 8 times more steps for an error of the wave that goes from 1.0e-3 to 6e-5, measured
2026-11-03"). Reproduce: the double-slit preset's scene (built by the wrapper, Bohm points off) continued from t = 0
with the wrapper's dt, with the dt of the engine's suggest_dt (whole range of V; a power of two as the wrapper
rounds), and with references dt/16 and dt/32 of the wrapper's. Measured at t = 12 units (the packet has passed the
wall): ||psi - psi_ref|| (the reference is Richardson-extrapolated from dt/16 and dt/32), the companion's accumulated
estimate, and the difference of the screen's record at t = 40 (what the player shows)."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core import backend
from lfphys.core.quantum import scene as QS
from p02_quantum import viz as P

pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
for o in pr["scene"]["objects"]:
    if o["type"] == "packet":
        o["values"]["bohm"] = 0
h = Harness("p02_quantum", None, pr)
st0 = h.sim.qs.state_dict()
dt_w = st0["dt"]
sug = h.sim.qs.suggest_dt(P.PHASE_PER_STEP)
dt_s = 2.0 ** math.floor(math.log2(sug))
print(f"wrapper dt {dt_w}; engine suggest_dt {sug:.5f} -> power of two {dt_s}; ratio of steps {dt_w / dt_s:g}")
T1 = 12.0


def run(dt, T, every=None):
    s = QS.Scene.from_state_dict(copy.deepcopy(st0))
    s.set_dt(dt)
    n = int(round(T / dt))
    step = max(1, int(round(0.25 / dt)))  # a companion estimate every 0.25 units (the wrapper: every 20 frames)
    s.step_error()
    k = 0
    while k < n:
        m = min(step, n - k)
        s.advance(m)
        k += m
        s.step_error()
    return s


res = {}
for name, dt in (("wrapper", dt_w), ("suggest", dt_s), ("ref16", dt_w / 16), ("ref32", dt_w / 32)):
    s = run(dt, T1)
    res[name] = (s.wave(1), s.checks()[1]["step_error"]["accumulated"], s)
ref = res["ref32"][0] + (res["ref32"][0] - res["ref16"][0]) / 3
g = res["wrapper"][2].grid
for name in ("wrapper", "suggest", "ref16", "ref32"):
    err = math.sqrt(g.norm(res[name][0] - ref))
    print(f"{name:8s}: ||psi - psi_ref|| at t = {T1}: {err:.3e}; companion's accumulated estimate {res[name][1]:.3e}")
print(f"Richardson correction size |ref32 - ref16| = {math.sqrt(g.norm(res['ref32'][0] - res['ref16'][0])):.3e}")
