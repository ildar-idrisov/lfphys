"""R-W: recompute S03's key numbers against the engine (independent arithmetic around the world's Shot)."""
import math, sys
import numpy as np
from scipy.optimize import minimize_scalar
sys.path.insert(0, "/lf/visualizations")
from s03_projectile.engine.shot import Shot, optimum_angle, G, OBJECTS, medium
from lfphys.theories.models import drag_quadratic as dq

def p(*a): print(*a, flush=True)
p("g", G, "medium", medium())
for o in OBJECTS: p(o, "k =", Shot(o, 1, 5, 45, True).k, "1/m")
d, m = 0.067, 0.058; rho_b = m / (math.pi / 6 * d**3); p("light ball density", rho_b, "rho_air/rho_ball", medium()["rho"] / rho_b)
rho_s = 0.0329 / (math.pi / 6 * 0.02**3); p("steel density", rho_s, "ratio", medium()["rho"] / rho_s)
p("Re of the light ball at 45 m/s:", medium()["rho"] * 45 * d / medium()["mu"])

# --- Lab part 1: chute v0 = 1.5 m/s, steel ball, air on, h 0.20..1.00
hs = [round(0.20 + 0.05 * i, 2) for i in range(17)]
k_ref = 1.5 * math.sqrt(2 / G)
Ls, effs, Ts = [], [], []
for h in hs:
    a, v = Shot("steel20", h, 1.5, 0.0, True), Shot("steel20", h, 1.5, 0.0, False)
    Ls.append(a.L); effs.append(1 - a.L / v.L); Ts.append(a.T)
p("part1 k_ref", k_ref, "max air effect %", 100 * max(effs), "T range", min(Ts), max(Ts))
# what the virtual tape reads (1 mm) and the ruler (1 cm): a weighted line0 with effective variance, by hand
Lr = np.round(np.array(Ls) / 1e-3) * 1e-3; hr = np.round(np.array(hs) / 0.01) * 0.01
x = np.sqrt(hr); sx = 0.005 / (2 * x); sy = 0.0005
b = np.sum(x * Lr) / np.sum(x * x)
for _ in range(3):
    w = 1 / (sy**2 + (b * sx) ** 2); b = np.sum(w * x * Lr) / np.sum(w * x * x)
sb = math.sqrt(1 / np.sum(w * x * x)); chi2 = np.sum(w * (Lr - b * x) ** 2); dof = len(x) - 1
if chi2 / dof > 1: sb *= math.sqrt(chi2 / dof)
p("part1 fit line0 b =", b, "+-", sb, "chi2/dof", chi2 / dof, "v0 from slope", b * math.sqrt(G / 2), "dev/sigma", (b - k_ref) / sb)
p("part1 Q1: stopwatch 0.1 s as a share of the flight", 0.1 / max(Ts), "to", 0.1 / min(Ts))

# --- Lab part 2: steel ball 5 m/s from the floor, 15..75; vacuum vs air slope
th = np.arange(15, 76, 5.0)
Lv = np.array([Shot("steel20", 0.0, 5.0, a, False).L for a in th]); La = np.array([Shot("steel20", 0.0, 5.0, a, True).L for a in th])
s2 = np.sin(np.radians(2 * th))
bv = np.sum(s2 * Lv) / np.sum(s2 * s2); ba = np.sum(s2 * La) / np.sum(s2 * s2)
p("part2 slope vacuum", bv, "v0^2/g", 25 / G, "slope air", ba, "air lower by %", 100 * (1 - ba / bv))
cv = np.polyfit(th, Lv, 2); p("part2 vacuum parabola vertex", -cv[1] / (2 * cv[0]))

# --- Lab part 3: light ball 20 m/s, h 0, air, 25..60
best, Lb, n = optimum_angle("ball67", 0.0, 20.0, True, 0.1)
res = minimize_scalar(lambda a: -Shot("ball67", 0.0, 20.0, a, True).L, bounds=(35, 48), method="bounded", options={"xatol": 1e-4})
p("part3 engine optimum (0.1 deg)", best, Lb, n, "continuous optimum", res.x, -res.fun)
r = minimize_scalar(lambda a: -dq.hodograph(20.0, math.radians(a), 0.0, Shot("ball67", 0, 20, 45, True).k, G)["L"], bounds=(35, 48), method="bounded", options={"xatol": 1e-5})
p("part3 hodograph optimum", r.x)
t3 = np.arange(25, 61, 5.0)
L3 = np.array([Shot("ball67", 0.0, 20.0, a, True).L for a in t3]); L3v = np.array([Shot("ball67", 0.0, 20.0, a, False).L for a in t3])
c3 = np.polyfit(t3, L3, 2); c3v = np.polyfit(t3, L3v, 2)
p("part3 parabola vertex air", -c3[1] / (2 * c3[0]), "vacuum", -c3v[1] / (2 * c3v[0]))
p("part3 L(40)", Shot("ball67", 0, 20, 40, True).L, "L(45)", Shot("ball67", 0, 20, 45, True).L)
# heavy slow ball: the shift
bh, _, _ = optimum_angle("steel20", 0.0, 5.0, True, 0.1); p("steel 5 m/s optimum in air", bh)

# --- Watch
for (h, v0) in [(1.25, 2.0), (1.25, 4.0), (5.0, 4.0)]:
    s, dr = Shot("steel20", h, v0, 0.0, False), Shot("steel20", h, 0.0, 0.0, False)
    p("watch h", h, "v0", v0, "T", s.T, "L", s.L, "drop T", dr.T)
a4, v4 = Shot("ball67", 0, 20, 45, True), Shot("ball67", 0, 20, 45, False)
p("watch 4: air L", a4.L, "T", a4.T, "H", a4.H, "vacuum L", v4.L, "T", v4.T, "H", v4.H)

# --- Explore claims
p("explore 25 m/s h0 vacuum 45:", Shot("ball67", 0, 25, 45, False).L, "air 40:", Shot("ball67", 0, 25, 40, True).L, "air 45:", Shot("ball67", 0, 25, 45, True).L)
bo, Lo, _ = optimum_angle("ball67", 0.0, 25.0, True, 0.1); p("explore 25 m/s air optimum", bo, Lo)
for h in [1, 2, 5, 10]:
    for v in [5, 25]:
        bo, Lo, _ = optimum_angle("ball67", float(h), float(v), True, 1.0); bv_, Lv_, _ = optimum_angle("ball67", float(h), float(v), False, 1.0)
        p(f"explore h {h} v {v}: optimum air {bo} vacuum {bv_}")
p("default explore point (h1 v15 45 vac)", Shot("ball67", 1, 15, 45, False).L, Shot("ball67", 1, 15, 45, False).T)
