"""R-E part B: the quadratic-drag flight three ways: the engine (DOP853), its hodograph quadrature, and an independent
30-digit Taylor-series integration (mpmath.odefun) with the landing located by findroot. Also steep launches."""
import math, sys, time
import numpy as np
import mpmath as mp
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.mechanics import G_STANDARD as G, Body, fly
from lfphys.theories.models import drag_quadratic as dq

BALL = Body(0.058, 0.067, "ball67")
drag = dq.QuadraticDrag.sphere(0.067)
k = drag.k(BALL.mass)
print("k =", k)
mp.mp.dps = 30

def mp_flight(v0, th_deg, h):
    K, g = mp.mpf(repr(k)), mp.mpf(repr(G))
    th = mp.radians(mp.mpf(repr(th_deg)))
    y0 = [mp.mpf(0), mp.mpf(repr(h)), mp.mpf(repr(v0)) * mp.cos(th), mp.mpf(repr(v0)) * mp.sin(th)]
    def F(t, Y):
        x, y, vx, vy = Y
        sp = mp.sqrt(vx * vx + vy * vy)
        return [vx, vy, -K * sp * vx, -g - K * sp * vy]
    sol = mp.odefun(F, 0, y0, tol=mp.mpf(10) ** -24, degree=24)
    # landing: y(t) = 0; bracket with the engine's estimate
    return sol

for (v0, th, h) in [(25.0, 45.0, 0.0), (20.0, 40.0, 0.0), (15.0, 0.0, 1.0), (10.0, -25.0, 3.0), (25.0, 85.0, 10.0)]:
    t0 = time.time()
    vx0, vy0 = v0 * math.cos(math.radians(th)), v0 * math.sin(math.radians(th))
    f = fly(BALL, [0.0, h], [vx0, vy0], forces=[drag])
    hd = dq.hodograph(v0, math.radians(th), h, k, G)
    sol = mp_flight(v0, th, h)
    Tm = mp.findroot(lambda t: sol(t)[1], mp.mpf(repr(f.flight_time)), tol=mp.mpf(10) ** -26)
    Lm = sol(Tm)[0]
    out = {"T_engine": (f.flight_time - float(Tm)) / float(Tm), "T_hodo": (hd["T"] - float(Tm)) / float(Tm),
           "L_engine": (f.range - float(Lm)) / float(Lm), "L_hodo": (hd["L"] - float(Lm)) / float(Lm)}
    if vy0 > 0:
        ta = mp.findroot(lambda t: sol(t)[3], mp.mpf(repr(f.apex["t"])), tol=mp.mpf(10) ** -26)
        Hm = sol(ta)[1]
        out["H_engine"] = (f.apex_height - float(Hm)) / float(Hm)
        out["H_hodo"] = (hd["H"] - float(Hm)) / float(Hm)
    print(f"v0={v0} th={th} h={h}: T={float(Tm):.15g} L={float(Lm):.15g} ", {kk: f"{vv:+.1e}" for kk, vv in out.items()},
          f"({time.time()-t0:.0f} s)")

print("== steep launches: hodograph vs engine (rel), near 90 deg the horizontal speed -> 0")
for th in [80.0, 85.0, 88.0, 89.0, 89.9, 89.99]:
    v0, h = 25.0, 0.0
    vx0, vy0 = v0 * math.cos(math.radians(th)), v0 * math.sin(math.radians(th))
    f = fly(BALL, [0.0, h], [vx0, vy0], forces=[drag])
    try:
        hd = dq.hodograph(v0, math.radians(th), h, k, G)
        print(f" th={th}: T {abs(hd['T']-f.flight_time)/f.flight_time:.1e} L {abs(hd['L']-f.range)/f.range:.1e}"
              f" H {abs(hd['H']-f.apex_height)/f.apex_height:.1e}")
    except Exception as e:
        print(f" th={th}: hodograph raised {type(e).__name__}: {e}")
