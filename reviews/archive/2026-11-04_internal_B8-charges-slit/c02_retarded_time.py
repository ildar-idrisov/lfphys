"""Review B8 (charges): robustness of lfphys.core.em.charges.retarded_time.

A. Far from the origin: uniform motion, field point at distance R ~ 1 m from the charge, the charge |r| away from the
   origin. Does the solver return (with the precision the inputs allow) or raise?
B. Near light speed: circular motion at gamma = 1e3, 1e4 (the observer in the orbit plane, where g' = c (1 - n.beta)
   becomes ~ c / (2 gamma^2)); residual against a 50-digit mpmath root of the same equation.
C. Hyperbolic motion near and beyond its horizon: the exact retarded time (closed form, mpmath) against the solver.
D. A sampled worldline whose retarded time lies INSIDE its domain but whose present distance / c exceeds t - t_min
   (and a case where the doubling overshoots the domain): false refusals?
"""
import math
import sys

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import charges as ch  # noqa: E402

C = ch.C
mp.mp.dps = 50
cm = mp.mpf(C)


def tryrt(w, x, t):
    try:
        return ch.retarded_time(w, np.atleast_2d(x), np.atleast_1d(t)), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


print("== A. far from the origin (uniform motion along x) ==")
for beta in (0.5, 0.99):
    v = np.array([beta * C, 0, 0])
    w = ch.uniform([0, 0, 0], v)
    for rabs in (1.0, 10.0, 30.0, 100.0, 1e3, 1e6, 3e8 * beta):
        t = rabs / (beta * C)
        x = np.array([rabs, 1.0, 0.0])  # 1 m abeam of the present position
        tr, err = tryrt(w, x, t)
        if err:
            print(f"beta = {beta}, |r| = {rabs:9.3g} m, t = {t:.3g} s: {err}")
            continue
        # exact delay: c tau = |x - r(t - tau)| for uniform motion: solve in mpmath
        tt = mp.mpf(t)
        f = lambda tau: cm * tau - mp.sqrt((mp.mpf(rabs) - mp.mpf(beta) * cm * (tt - tau)) ** 2 + 1)  # noqa: E731
        tau_ex = mp.findroot(f, mp.mpf(1) / cm)
        tr_ex = tt - tau_ex
        print(f"beta = {beta}, |r| = {rabs:9.3g} m, t = {t:.3g} s: t_ret error {float(tr[0] - tr_ex):+.2e} s "
              f"(ulp(t) = {np.spacing(t):.1e} s; delay {float(tau_ex):.3e} s)")

print("\n-- circular motion of radius 1 m about a centre far from the origin; observer 2 m from the centre --")
for cx in (0.0, 10.0, 100.0, 1e4):
    w = ch.circular(1.0, 0.5 * C, center=(cx, 0, 0))
    xs = np.array([[cx + 2.0, 0.5, 0.3], [cx - 1.5, 1.2, -0.2], [cx, 2.0, 0.0]])
    tr, err = tryrt(w, xs, np.array([1e-9, 2e-9, 3e-9]))
    print(f"centre x = {cx:g} m: " + (err if err else "ok"))

print("\n== B. near light speed: circular motion, observer far in the orbit plane ==")
for gam in (1e2, 1e3, 1e4):
    beta = math.sqrt(1 - 1 / gam ** 2)
    rho = 1.0
    w0 = beta * C / rho
    w = ch.circular(rho, w0)
    Rf = 100.0
    x = np.array([0.0, Rf, 0.0])  # far along +y: the charge's velocity points at it near phase 0 (velocity +y)
    T0 = 2 * math.pi / w0
    ts = Rf / C + np.linspace(-0.01, 0.01, 2001) * T0  # observer times around the pulse
    tr, err = tryrt(w, np.broadcast_to(x, (len(ts), 3)), ts)
    if err:
        print(f"gamma = {gam:g}: {err}")
        continue
    r = w.position(tr)
    res = np.abs(C * (ts - tr) - np.linalg.norm(x - r, axis=1)) / Rf
    # mpmath reference at the 5 points with the largest kappa^-1
    n = (x - r) / np.linalg.norm(x - r, axis=1)[:, None]
    kap = 1 - np.einsum("ij,ij->i", n, w.state(tr)[1] / C)
    worst = np.argsort(kap)[:5]
    errs = []
    for i in worst:
        tt = mp.mpf(ts[i])

        def f(tp):
            ph = mp.mpf(w0) * tp
            return cm * (tt - tp) - mp.sqrt((0 - rho * mp.cos(ph)) ** 2 + (Rf - rho * mp.sin(ph)) ** 2)
        tp = mp.findroot(f, mp.mpf(tr[i]))
        errs.append(abs(float(tp - mp.mpf(tr[i]))) * w0)  # orbit phase error (rad)
    print(f"gamma = {gam:g}: max |c tau - R|/R = {res.max():.1e}; min kappa = {kap.min():.2e} "
          f"(1/(2 gamma^2) = {0.5 / gam ** 2:.1e}); phase error of t_ret at the 5 smallest kappa: {max(errs):.1e} rad "
          f"(pulse width ~ 1/gamma^3 = {1 / gam ** 3:.1e} rad)")

print("\n== C. hyperbolic motion near its horizon (g = 3e15 m/s^2, c^2/g = 30 m, along +x; point at t = 0) ==")
g = 3e15
a = C * C / g
w = ch.hyperbolic(g, direction=(1, 0, 0))
# horizon at t = 0: x + a > -c t = 0 i.e. x > -a (for points on the axis); exact t_ret by mpmath
for dx in (1.0, 1e-3, 1e-6, 1e-9, 0.0, -1e-9, -1e-6, -1e-3, -1.0):
    X = -a + dx
    x = np.array([X, 0.0, 0.0])
    tr, err = tryrt(w, x, 0.0)
    am = mp.mpf(a)

    def f(tp):  # c (0 - tp) - |X - xq(tp)|, xq = a (sqrt(1 + (g tp/c)^2) - 1)
        xq = am * (mp.sqrt(1 + (mp.mpf(g) * tp / cm) ** 2) - 1)
        return cm * (0 - tp) - abs(mp.mpf(X) - xq)
    exact = None
    if dx > 0:
        # on the axis behind the charge: c(-tp) = xq - X  ->  closed form: -c tp = a cosh(eta) - a - X, c tp = a sinh(eta)
        # -> a sinh + a cosh = a + X  -> e^eta = (a + X)/a ... eta = ln((a+X)/a) <= 0
        eta = mp.log((am + mp.mpf(X)) / am)
        exact = am * mp.sinh(eta) / cm
    line = f"x = -c^2/g {dx:+.0e} m: "
    if err:
        line += err
    else:
        line += f"t_ret = {tr[0]:.6e} s"
        if exact is not None:
            line += f", exact {float(exact):.6e} s, rel err {abs(float((mp.mpf(tr[0]) - exact) / exact)):.1e}"
        else:
            line += "  <-- a root reported where none exists"
    if exact is None and not err:
        pass
    print(line)

print("\n== D. sampled worldline: retarded time inside the domain, present distance / c beyond it ==")
beta = 0.9
v = np.array([beta * C, 0, 0])
ts = np.linspace(0, 1e-8, 201)
uw = ch.uniform([0, 0, 0], v)
sw = ch.SampledWorldline(ts, uw.position(ts), *uw.state(ts)[1:])
for X, t in ((-1.5, 8e-9), (-0.2, 9e-9), (-2.3, 9.9e-9)):
    x = np.array([X, 0.0, 0.0])
    tau_ex = (beta * C * t - X) / (C * (1 + beta))  # behind the charge moving away: c tau = v (t - tau) - X
    tr_ex = t - tau_ex
    tr, err = tryrt(sw, x, t)
    tr_f, _ = tryrt(uw, x, t)
    print(f"x = ({X}, 0, 0) m, t = {t:.2e} s: exact t_ret = {tr_ex:.4e} s (inside [0, 1e-8]); "
          f"sampled: {err if err else f'{tr[0]:.4e} s'}; formula worldline: {tr_f[0]:.4e} s")
