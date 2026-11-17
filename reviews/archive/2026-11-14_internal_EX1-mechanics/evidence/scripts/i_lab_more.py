"""R-E part I: on S03's lab tables, the iterated effective variance against the minimum of S (b-dependent weights);
the verdict on axes other than the law's (L against h); the parabola's bias with the lab's weights."""
import math, sys
import numpy as np
from scipy import optimize
sys.path[:0] = ["/lf/lfphys", "/lf/visualizations", "/lf/visualizations/server"]
from lfphys.tools.stats import linear_fit
from s03_projectile.engine.shot import Shot, G
from s03_projectile import viz

def rd(v, d): return round(round(v / d) * d, 6)
# A heights
hs = viz.STEPS[0]["controls"][0]["values"]
L = np.array([rd(Shot("steel20", h, 1.5, 0.0, True).L, 0.001) for h in hs]); H = np.array(hs)
X, SX = np.sqrt(H), 0.005 / (2 * np.sqrt(H))
# B angles (vacuum)
ths = np.array(viz.STEPS[1]["controls"][0]["values"], float)
LB = np.array([rd(Shot("steel20", 0.0, 5.0, t, False).L, 0.001) for t in ths]); XB = np.sin(2 * np.radians(ths)); SXB = np.abs(2 * np.cos(2 * np.radians(ths))) * math.pi / 180 * 0.5
# C air
tc = np.array(viz.STEPS[2]["controls"][0]["values"], float)
LC_exact = np.array([Shot("ball67", 0.0, 20.0, t, True).L for t in tc]); LC = np.array([rd(v, 0.001) for v in LC_exact])

def minS(x, y, sx, sy, model, p0):
    def f(p, x):
        return p[0] * x if model == "line0" else p[0] + p[1] * x + p[2] * x * x
    def df(p, x):
        return p[0] + 0 * x if model == "line0" else p[1] + 2 * p[2] * x
    S = lambda p: float(np.sum((y - f(p, x)) ** 2 / (sy ** 2 + (df(p, x) * sx) ** 2)))
    r = optimize.minimize(S, p0, method="Nelder-Mead", options={"xatol": 1e-14, "fatol": 1e-16, "maxiter": 40000, "maxfev": 80000})
    r = optimize.minimize(S, r.x, method="Nelder-Mead", options={"xatol": 1e-14, "fatol": 1e-16, "maxiter": 40000, "maxfev": 80000})
    return r.x
for nm, (x, y, sx, model) in {"A heights line0": (X, L, SX, "line0"), "B angles line0": (XB, LB, SXB, "line0"),
                              "C air quadratic": (tc, LC, np.full(tc.size, 0.5), "quadratic")}.items():
    fv = linear_fit(x, y, sx, 0.0005, model)
    p = minS(x, y, sx, 0.0005, model, np.array(fv["params"]))
    if model == "quadratic":
        v_ev, s_ev = fv["vertex"], fv["vertex_sigma"]; v_m = -p[1] / (2 * p[2])
        print(f" {nm}: EV vertex {v_ev:.5f} ± {s_ev:.5f}; min S vertex {v_m:.5f}: gap {(v_ev-v_m)/s_ev:+.3f} σ")
    else:
        print(f" {nm}: EV slope {fv['params'][0]:.7f} ± {fv['sigma'][0]:.7f}; min S {p[0]:.7f}: gap {(fv['params'][0]-p[0])/fv['sigma'][0]:+.4f} σ")
# the parabola's bias with the lab's weights on exact (unrounded) ranges
fe = linear_fit(tc, LC_exact, 0.5, 0.0005, "quadratic")
print(f" C with exact ranges and the lab's errors: vertex {fe['vertex']:.4f} ± {fe['vertex_sigma']:.4f}; true optimum 41.8868: z {(fe['vertex']-41.8868)/fe['vertex_sigma']:+.2f}")
# a verdict on other axes: L against h (the grade-7 plot) with the step's default fit, then «Check against the law»
ref = 1.5 * math.sqrt(2 / G)
for xname, x, sx in [("h", H, np.full(H.size, 0.005)), ("sqrt h", X, SX)]:
    for model in ("line0", "line"):
        f = linear_fit(x, L, sx, 0.0005, model)
        b, s = f["params"][-1], f["sigma"][-1]
        print(f" heights, x = {xname}, {model}: slope {b:.5f} ± {s:.5f} vs k {ref:.5f} m^1/2: z {(b-ref)/s:+.1f} -> {'agrees' if abs(b-ref)<=2*s else 'does not agree'}")
