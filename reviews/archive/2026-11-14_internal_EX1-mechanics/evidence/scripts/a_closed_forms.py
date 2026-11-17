"""R-E part A: closed forms. Vacuum; linear drag incl. the Lambert-W landing time, against mpmath (50 digits)."""
import math, sys
import numpy as np
import mpmath as mp
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.mechanics import (G_STANDARD as G, Body, fly, LinearDrag, linear_drag_landing_time,
                                   linear_drag_apex_time, linear_drag_state, vacuum_landing_time, vacuum_apex_height)
mp.mp.dps = 50

def exact_landing(h, vy0, k, g=G):
    """root s>0 of h' + c(1-e^-s) - s = 0 in 50 digits, T = tau*s (independent of the code: findroot, not Lambert W)"""
    h, vy0, k, g = (mp.mpf(repr(v)) for v in (h, vy0, k, g))
    tau = 1 / k
    c = (vy0 + g * tau) / (g * tau)
    hp = h / (g * tau * tau)
    f = lambda s: hp + c * (1 - mp.exp(-s)) - s
    # bracket: f(0)=hp>=0; start search above the vacuum estimate
    Tv = (vy0 + mp.sqrt(vy0 * vy0 + 2 * g * h)) / g
    s_hi = max(Tv / tau * 4, hp + abs(c) + 10)
    lo = mp.mpf(10) ** -40 if h == 0 else mp.mpf(0)
    s = mp.findroot(f, (lo if h > 0 else Tv / tau / 4, s_hi), solver="anderson") if False else None
    # robust: bisection
    a, b = (mp.mpf(0) if h > 0 else Tv / tau * mp.mpf("0.5")), s_hi
    assert f(a) >= 0 and f(b) < 0, (f(a), f(b))
    for _ in range(400):
        m = (a + b) / 2
        if f(m) > 0: a = m
        else: b = m
    return tau * (a + b) / 2, (a + b) / 2

print("== A1 vacuum landing time & apex (formula vs mpmath)")
for h, vy0 in [(0, 5.0), (1.25, 0.0), (5.0, -3.0), (10.0, 24.9), (1e-6, -30.0)]:
    T = vacuum_landing_time(h, vy0)
    hm, vm, g = mp.mpf(h), mp.mpf(vy0), mp.mpf(G)
    Te = (vm + mp.sqrt(vm * vm + 2 * g * hm)) / g
    print(f" h={h} vy0={vy0}: T={T!r} rel.err={float((T - Te) / Te):.2e}; H={vacuum_apex_height(h, vy0)}")

print("== A2 linear drag landing time (Lambert W) vs 50-digit bisection; s = T/tau")
rows = []
for k in [3.0, 1.0, 0.3, 0.1, 0.03, 1e-2, 1e-3, 1e-4, 1e-5]:
    for (h, vy0) in [(0.0, 10.0), (2.0, 6.0), (10.0, 0.0), (10.0, -3.0)]:
        T = linear_drag_landing_time(h, vy0, k, G)
        Te, s = exact_landing(h, vy0, k)
        rel = float((T - Te) / Te)
        rows.append((float(s), rel))
        print(f" k={k:<7g} h={h:<5} vy0={vy0:<5}: s={float(s):.3e} rel.err={rel:+.2e}  (doc ~1e-16/s={1e-16/float(s):.1e}; 1e-16/s^2={1e-16/float(s)**2:.1e})")

print("== A3 c <= 0 (launched down at or above the terminal speed): refused by the code; the formula still holds")
k, h = 1.0, 3.0
vt = G / k
for vy0 in [-vt, -1.5 * vt]:
    try:
        T = linear_drag_landing_time(h, vy0, k, G)
        print(" code:", T)
    except ValueError as e:
        print(f" vy0={vy0:.4f} (= {vy0/vt:.2f} v_t): code refuses: {e}")
    tau = 1 / k; c = (vy0 + G * tau) / (G * tau); hp = h / (G * tau * tau)
    from scipy.special import lambertw
    Tw = tau * (c + hp + lambertw(-c * math.exp(-(c + hp)), 0).real)
    Te, s = exact_landing(h, vy0, k)
    f = fly(Body(1.0), (0.0, h), (0.0, vy0), forces=[LinearDrag(k)])
    print(f"   formula T={Tw!r}  exact={float(Te)!r}  rel={float((Tw-Te)/Te):.1e}; DOP853 fly T={f.flight_time!r} rel={float((f.flight_time-Te)/Te):.1e}")

print("== A4 apex time: tau ln(1+vy0/(g tau)) vs vy(t)=0 from linear_drag_state")
for k, vy0 in [(0.3, 6.0), (1e-4, 6.0), (5.0, 0.1)]:
    ta = linear_drag_apex_time(vy0, k, G)
    _, v = linear_drag_state(ta, [0.0, 0.0], [1.0, vy0], k, G)
    print(f" k={k} vy0={vy0}: t_a={ta!r}, vy(t_a)={v[1]:.2e} (scale vy0 {vy0})")

print("== A5 linear_drag_state vs mpmath exact at a few times")
r0, v0 = [0.5, 2.0], [7.0, 3.0]
for k in [0.3, 1e-3, 1e-6]:
    for t in [1e-4, 0.5, 3.0]:
        r, v = linear_drag_state(t, r0, v0, k, G)
        K, tt, g = mp.mpf(repr(k)), mp.mpf(repr(t)), mp.mpf(G)
        tau = 1 / K; e = mp.exp(-tt / tau)
        ye = r0[1] + v0[1] * tau * (1 - e) - g * tau * (tt - tau * (1 - e))
        xe = r0[0] + v0[0] * tau * (1 - e)
        print(f" k={k:g} t={t}: rel.err x {float((r[0]-xe)/xe):+.1e} y {float((r[1]-ye)/max(abs(ye),1)):+.1e}")
