"""U2: the drawn orbits' deviation from the computed trajectory (the view's Hermite tessellation, ported), points per
orbit and the largest turn between trail points, for p01 «inner» at x1 and x10; the former trail (one point per frame)
as the control."""
import sys, math, json
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf", "/lf/visualizations/p01_gravity/tests"]
import numpy as np
import test_p01_gravity as T
from tests.harness import Harness
from p01_gravity.viz import YR
for factor in (1.0, 10.0):
    h = Harness("p01_gravity", "inner")
    speed = h.sim.default_speed * factor
    frames = [h.sim.t + speed / 20.0 * k for k in range(1, 41)]
    for t in frames:
        h.run_to(t); h.runner._frame(0.0)
    for key, name, r, P in (("o2", "Меркурий", 0.387, 0.2408), ("o4", "Земля", 1.0, 1.0)):
        tr = T._trail_of(h, key)
        V_ = np.array([q[2] for q in tr])
        turns = np.degrees(np.arctan2(np.linalg.norm(np.cross(V_[:-1], V_[1:]), axis=1), np.einsum("ij,ij->i", V_[:-1], V_[1:])))
        t0, t1 = tr[0][0], tr[-1][0]
        nb = Harness("p01_gravity", "inner").sim.mode.nb
        ts = np.linspace(t0, t1, 3000)
        true = []
        for t in ts:
            nb.advance(t / YR); true.append(nb.positions()[nb.keys.index(key)].copy())
        dev = np.linalg.norm(T._drawn_at(tr, ts) - np.array(true), axis=1)
        nb3 = Harness("p01_gravity", "inner").sim.mode.nb
        fr = [t for t in frames if t0 <= t <= t1]
        per = []
        for t in fr:
            nb3.advance(t / YR); per.append(nb3.positions()[nb3.keys.index(key)].copy())
        per = np.array(per)
        ang_old = [math.degrees(math.acos(max(-1, min(1, np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b)))))
                   for a, b in zip(np.diff(per, axis=0)[:-1], np.diff(per, axis=0)[1:])]
        print(json.dumps({"speed": f"x{factor:g}", "body": name, "trail_points_per_orbit": round(len(tr) / ((t1 - t0) / (P * YR)), 1),
                          "max_turn_between_points_deg": round(float(turns.max()), 2),
                          "max_drawn_deviation_over_r": float(dev.max() / r),
                          "former_points_per_orbit": round(len(fr) / ((fr[-1] - fr[0]) / (P * YR)), 1) if len(fr) > 1 else None,
                          "former_max_turn_between_chords_deg": round(max(ang_old), 1) if ang_old else None}, ensure_ascii=False), flush=True)
