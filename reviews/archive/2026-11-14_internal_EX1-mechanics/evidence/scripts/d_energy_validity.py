"""R-E parts C, D, E: energy bookkeeping (independently), validity() share (independently), the drag curve's numbers,
the effect of the measured drag curve on S03's quantities, and the Basset force against the stated estimate."""
import math, sys
import numpy as np
from scipy import integrate, optimize
sys.path[:0] = ["/lf/lfphys", "/lf/visualizations", "/lf/visualizations/server"]
from lfphys.core.mechanics import G_STANDARD as G, Body, fly
from lfphys.core import data
from lfphys.theories.models import drag_quadratic as dq

air = data.fluid_properties("air", 20.0)
print("air 20 C:", air["rho"], air["mu"])
BALLS = {"steel20": Body(0.0329, 0.020), "ball67": Body(0.058, 0.067)}

def radau(body, drag, r0, v0, rtol=1e-12):
    """independent: Radau IIA in (x, y, vx, vy) without the work state; landing by its own event"""
    m = body.mass
    def rhs(t, Y):
        v = Y[2:]; F = drag.force(t, Y[:2], v) if drag else np.zeros(2)
        return [v[0], v[1], F[0] / m, F[1] / m - G]
    land = lambda t, Y: Y[1]; land.terminal, land.direction = True, -1
    s = integrate.solve_ivp(rhs, (0, 100), [*r0, *v0], method="Radau", rtol=rtol, atol=1e-13, dense_output=True,
                            events=land)
    return s

print("== C energy: carried W vs independent quadrature of the drag power on a Radau solution")
for name, (h, v0, th) in [("ball67", (0.0, 25.0, 45.0)), ("ball67", (10.0, 25.0, 85.0)), ("steel20", (1.0, 1.5, 0.0)),
                          ("ball67", (20.0, 40.0, -30.0))]:
    b = BALLS[name]; d = dq.QuadraticDrag.sphere(b.diameter, air)
    v = [v0 * math.cos(math.radians(th)), v0 * math.sin(math.radians(th))]
    f = fly(b, [0.0, h], v, forces=[d])
    s = radau(b, d, [0.0, h], v)
    T = s.t_events[0][0]
    P = lambda t: float(d.force(t, None, s.sol(t)[2:]) @ s.sol(t)[2:])
    W_ind, err = integrate.quad(P, 0, T, epsabs=0, epsrel=1e-13, limit=500)
    W_eng = f.landing["W"]
    vT = s.sol(T)[2:]
    E0 = 0.5 * b.mass * v0 * v0 + b.mass * G * h
    bal = 0.5 * b.mass * float(vT @ vT) + 0 - W_ind - E0
    print(f" {name} h={h} v0={v0} th={th}: W engine {W_eng:.12g}, W Radau+quad {W_ind:.12g} (rel {abs(W_eng-W_ind)/abs(W_ind):.1e});"
          f" Radau balance at landing {abs(bal)/E0:.1e}; engine energy_balance() {f.energy_balance():.1e}; T rel {abs(f.flight_time-T)/T:.1e}")

print("== D validity(): share of drag work outside 1e3<Re<2e5, engine vs independent (Radau, 2e6-point trapezoid + exact cuts)")
def share_ind(b, d, h, v0, th, lo=1e3, hi=2e5):
    v = [v0 * math.cos(math.radians(th)), v0 * math.sin(math.radians(th))]
    s = radau(b, d, [0.0, h], v)
    T = s.t_events[0][0]
    t = np.linspace(0, T, 2_000_001)
    V = s.sol(t)[2:]
    sp = np.hypot(V[0], V[1])
    re = air["rho"] * sp * b.diameter / air["mu"]
    p = 0.5 * d.rho * d.cd * d.area * sp ** 3
    out = (re < lo) | (re > hi)
    tot = integrate.trapezoid(p, t)
    o = integrate.trapezoid(np.where(out, p, 0.0), t)
    return o / tot, re.min(), re.max()
cases = [("ball67", 0.5, 0.05, 0.0), ("steel20", 0.0, 5.0, 85.0), ("steel20", 2.0, 5.0, 80.0), ("ball67", 20.0, 0.3, 0.0),
         ("steel20", 1.0, 1.5, 0.0), ("ball67", 0.0, 3.0, 89.0)]
for name, h, v0, th in cases:
    b = BALLS[name]; d = dq.QuadraticDrag.sphere(b.diameter, air)
    f = fly(b, [0.0, h], [v0 * math.cos(math.radians(th)), v0 * math.sin(math.radians(th))], forces=[d])
    val = dq.validity(f, d)
    sh, rmin, rmax = share_ind(b, d, h, v0, th)
    print(f" {name} h={h} v0={v0} th={th}: engine share {val['share_outside']:.6e}  independent {sh:.6e}"
          f"  (rel {abs(val['share_outside']-sh)/max(sh,1e-300):.1e}); Re {val['re_min']:.4g}-{val['re_max']:.4g}")

print("== drag curve: Morrison eq (1) extremes on RE_RANGE; Clift-Grace-Weber table 5.2 (as recalled by the reviewer)")
re = np.logspace(3, math.log10(2e5), 200001)
cm = dq.cd_standard(re)
print(f" Morrison: min {cm.min():.4f} at Re={re[cm.argmin()]:.4g}, max {cm.max():.4f} at Re={re[cm.argmax()]:.4g}; at 1e3 {dq.cd_standard(1e3):.4f}, 2e5 {dq.cd_standard(2e5):.4f}")
def cgw(Re):
    w = math.log10(Re)
    if Re <= 1.5e3: lg = 1.6435 - 1.1242 * w + 0.1558 * w * w
    elif Re <= 1.2e4: lg = -2.4571 + 2.5558 * w - 0.9295 * w * w + 0.1049 * w ** 3
    elif Re < 4.4e4: lg = -1.9181 + 0.6370 * w - 0.0636 * w * w
    else: lg = -4.3390 + 1.5809 * w - 0.1546 * w * w
    return 10 ** lg
cg = np.array([cgw(r) for r in re[::100]])
print(f" CGW: min {cg.min():.4f} at Re={re[::100][cg.argmin()]:.4g}, max {cg.max():.4f} at Re={re[::100][cg.argmax()]:.4g}")
print(f" constant 0.47 relative to the curve: (0.47-0.387)/0.387 = {100*(0.47-0.387)/0.387:+.1f} %, (0.47-0.504)/0.504 = {100*(0.47-0.504)/0.504:+.1f} %;"
      f" the code's -18 %/+7 % = (curve-0.47)/0.47: {100*(0.387-0.47)/0.47:+.1f} / {100*(0.504-0.47)/0.47:+.1f}")

print("== the measured curve (Morrison) instead of the constant: S03's ranges and the optimum of lab part C")
class CurveDrag(dq.QuadraticDrag):
    def force(self, t, r, v):
        v = np.asarray(v, float); sp = math.sqrt(float(v @ v))
        if sp == 0: return np.zeros_like(v)
        cd = float(dq.cd_standard(self.rho * sp * self.diameter / self.mu))
        return -0.5 * self.rho * cd * self.area * sp * v
b = BALLS["ball67"]; dconst = dq.QuadraticDrag.sphere(b.diameter, air); dcurve = CurveDrag(0.47, dconst.area, air["rho"], mu=air["mu"], diameter=b.diameter)
def L(drag, v0, th, h=0.0):
    return fly(b, [0.0, h], [v0 * math.cos(math.radians(th)), v0 * math.sin(math.radians(th))], forces=[drag]).range
for v0, th in [(20.0, 40.0), (25.0, 45.0), (15.0, 45.0)]:
    a, c = L(dconst, v0, th), L(dcurve, v0, th)
    print(f" ball67 v0={v0} th={th}: L const {a:.4f} m, L Morrison {c:.4f} m ({100*(c/a-1):+.2f} %)")
for drag, nm in [(dconst, "C_d 0.47"), (dcurve, "Morrison C_d(Re)")]:
    m = optimize.minimize_scalar(lambda a: -L(drag, 20.0, a), bracket=(40, 42, 44), tol=1e-8)
    print(f" lab C optimum with {nm}: {m.x:.3f} deg, L {-m.fun:.4f} m")
fv = fly(b, [0, 0], [20 * math.cos(math.radians(42)), 20 * math.sin(math.radians(42))], forces=[dconst])
val = dq.validity(fv, dconst)
print(f" validity at lab C (42 deg): share outside {val['share_outside']}, Re {val['re_min']:.3g}-{val['re_max']:.3g}, curve C_d {val['cd_curve_min']:.3f}-{val['cd_curve_max']:.3f} -> check 'holds' = {val['share_outside']<=0.01}")

print("== E Basset history force (Maxey-Riley, Stokes regime) for a sphere falling from rest; R = rho_f/rho_p")
def mr(R, T=6.0, dt=1e-3, basset=True, am=True):
    # (1 + R/2) a = (1 - R) - v - B * int_0^t a(s)/sqrt(t-s) ds, B = 9/sqrt(18 pi) sqrt(R); units tau_p, g tau_p
    B = 9.0 / math.sqrt(18 * math.pi) * math.sqrt(R) if basset else 0.0
    ma = 1 + (R / 2 if am else 0.0); buo = (1 - R) if am else 1.0
    n = int(round(T / dt)); a = np.zeros(n); v = np.zeros(n + 1); x = np.zeros(n + 1)
    tn = dt * np.arange(n + 1)
    for i in range(n):  # a on (t_i, t_{i+1}) constant; history at t_{i+1}
        tt = tn[i + 1]
        wts = 2 * (np.sqrt(tt - tn[:i + 1]) - np.sqrt(np.maximum(tt - tn[1:i + 2], 0)))
        hist = float(a[:i] @ wts[:i]) if i else 0.0
        # implicit in a_i: ma a_i = buo - (v_i + a_i dt) - B (hist + a_i wts[i])
        a[i] = (buo - v[i] - B * hist) / (ma + dt + B * wts[i])
        v[i + 1] = v[i] + a[i] * dt; x[i + 1] = x[i] + v[i] * dt + 0.5 * a[i] * dt * dt
    return tn, v, x
for nm, rp in [("steel", 7850.0), ("water droplet", 1000.0), ("light ball 67 mm (368 kg/m3)", 368.0)]:
    R = air["rho"] / rp
    t, v0_, x0_ = mr(R, basset=False, am=False)
    for dt in (2e-3, 1e-3):
        t, v1, x1 = mr(R, dt=dt)
        t0, v0_, x0_ = mr(R, dt=dt, basset=False, am=False)
        i1 = int(round(1.0 / dt))
        print(f" {nm}: R={R:.3g}, dt={dt}: |dv|/v at t=tau_p {abs(v1[i1]-v0_[i1])/v0_[i1]:.3%}, max over [0.2,6]tau_p "
              f"{np.max(np.abs(v1-v0_)[int(0.2/dt):]/v0_[int(0.2/dt):]):.3%}, fallen distance at 6 tau_p {abs(x1[-1]-x0_[-1])/x0_[-1]:.3%};"
              f" the stated estimate rho_f/rho_p = {R:.2%}, sqrt = {math.sqrt(R):.2%}")
