"""Independent event-by-event re-derivation of the v01 rod apparatus measurements (SR, ether, emission; Einstein
and lab synchronisation; rod along and across the motion; external flashes from both sides; own-light round
trips) and of checks.one_way_speed / round_trip_speed / doppler_ratio.

Reviewer script (2026-10-22). The reference here is computed WITHOUT the engine: collinear (or transverse) event
geometry solved by hand (linear equations / Pythagoras), clocks by tau = t/gamma (SR) or tau = t (Galilean),
B's clock offset from a hand-computed light exchange. The engine is driven through engine.world.World.

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_apparatus.py
"""
from __future__ import annotations

import argparse
import itertools
import math

import numpy as np

from v01_light_travel.engine import checks
from v01_light_travel.engine.apparatus import Apparatus
from v01_light_travel.engine.consts import C
from v01_light_travel.engine.laws import Laws
from v01_light_travel.engine.world import Obj, World
from v01_light_travel.engine.worldlines import Piecewise


# ---------------------------------------------------------------------------------------------------------
# hand-made reference (collinear rod along x)
def ref_external_one_way(kin, sync, v, u, s, L0, D, c=C, t_flash=None):
    """Rod (A at x = v t, B ahead along +x), flash from a source at x = -s*D at lab t_f moving with u."""
    rel = kin == "SR"
    g = 1 / math.sqrt(1 - (v / c) ** 2) if rel else 1.0
    Llab = L0 / g
    xA = lambda t: v * t
    xB = lambda t: v * t + Llab
    # B's raw clock origin: B's rest-frame-simultaneous event with A's (t=0, x=0)
    tB0 = g * v * L0 / c**2 if rel else 0.0
    tauA = lambda t: t / g
    tauB_raw = lambda t: (t - tB0) / g

    # own light speed in the lab for a signal emitted by a body moving with w in direction d (+1/-1)
    def own(w, d):
        if kin == "emission":
            return d * c + w
        return d * c

    # Einstein exchange started at t1 = 0
    t1 = 0.0
    # A -> B: v t + Llab = own(v,+1) (t - t1) + xA(t1)  -> t2
    vA = own(v, +1)
    t2 = (Llab + 0.0 - vA * 0 + 0) / (vA - v)  # xA(0) = 0
    vB = own(v, -1)
    # B -> A: xB(t2) + vB (t - t2) = v t -> t3
    t3 = (xB(t2) - vB * t2) / (v - vB)
    if sync == "einstein":
        off = tauA(t1) + 0.5 * (tauA(t3) - tauA(t1)) - tauB_raw(t2)
        t_sync = t3
    else:  # equal readings at equal lab time t1
        off = tauA(t1) - tauB_raw(t1)
        t_sync = t1
    tauB = lambda t: tauB_raw(t) + off
    tf = t_flash if t_flash is not None else 1.5 * t3 + 1e-6
    # flash: source at x = -s D at tf with velocity u; light lab speed
    w = s * c + (u if kin == "emission" else 0.0)
    xs = -s * D
    # pass A: xs + w (t - tf) = v t ; pass B: xs + w (t - tf) = v t + Llab
    ta = (xs - w * tf) / (v - w)
    tb = (xs - w * tf - Llab) / (v - w)
    if s > 0:
        dtau = tauB(tb) - tauA(ta)
    else:
        dtau = tauA(ta) - tauB(tb)
    return L0 / dtau, dict(t2=t2, t3=t3, ta=ta, tb=tb, tf=tf, t_sync=t_sync)


def ref_round_trip(kin, sync, v, L0, orient, c=C, t_start=0.0):
    """Own-light round trip started at A at t_start (apparatus built at 0)."""
    rel = kin == "SR"
    g = 1 / math.sqrt(1 - (v / c) ** 2) if rel else 1.0
    if orient == "x":
        if kin == "emission":
            dt12, dt23 = L0 / c, L0 / c
        else:
            Llab = L0 / g
            dt12, dt23 = Llab / (c - v), Llab / (c + v)
        rt = 2 * L0 / ((dt12 + dt23) / g)
        return rt
    # transverse
    if kin == "emission":
        dt = L0 / c
    else:
        dt = L0 / math.sqrt(c * c - v * v)
    return 2 * L0 / (2 * dt / g)


# ---------------------------------------------------------------------------------------------------------
def engine_external(kin, sync, v, u, s, L0, D):
    laws = Laws(kin, "none")
    msgs = []
    w = World(laws, None, [0.0, 0.0], 4 * D, 36, lambda m, b=None: msgs.append(m))
    w.add(Obj("src", "src", "beacon", "#000", Piecewise.start(laws, 0.0, 0.0, [-s * D, 0.0], [u, 0.0]),
              receiver=False))
    wl = Piecewise.start(laws, 0.0, 0.0, [0.0, 0.0], [v, 0.0])
    o = Obj("obs", "obs", "observer", "#000", wl, movable=True)
    o.apparatus = Apparatus(laws, "obs", wl, L0, "x", sync)
    w.add(o)
    w.build_apparatus(o, 0.0)
    _, info = ref_external_one_way(kin, sync, v, u, s, L0, D)
    tf = info["tf"]
    # the source is at -s D at t = 0 and moves with u: place it so that it is at -s D at tf
    w.objects["src"].wl = Piecewise.start(laws, 0.0, tf, [-s * D, 0.0], [u, 0.0])
    w.advance(tf)
    w.flash("src", tf)
    w.advance(tf + 100 * (D + L0) / C)
    out = [m for m in msgs if m.get("type") == "check" and "внешний свет" in m.get("label", "")]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    L0, D = 3e5, 1e8
    worst_eng = worst_chk = 0.0
    rows = 0
    print("A. external flash, rod along x: engine value vs hand-made events vs checks.one_way_speed")
    for kin, sync, v, u, s in itertools.product(["SR", "ether", "emission"], ["einstein", "lab"],
                                                [0.0, 0.5 * C, -0.5 * C, 0.9 * C], [0.0, 0.3 * C, -0.3 * C],
                                                [+1, -1]):
        if kin == "emission" and abs(u - v) >= C:
            continue
        ref, info = ref_external_one_way(kin, sync, v, u, s, L0, D)
        chk_ref = checks.one_way_speed(kin, sync, C, v, s, u)
        e = engine_external(kin, sync, v, u, s, L0, D)
        if not e:
            print(f"  {kin:8s} {sync:8s} v={v / C:+.1f}c u={u / C:+.1f}c s={s:+d}: NO ENGINE RESULT")
            continue
        val = e[0]["value"]
        d1 = abs(val / ref - 1)
        d2 = abs(chk_ref / ref - 1)
        worst_eng, worst_chk = max(worst_eng, d1), max(worst_chk, d2)
        rows += 1
        if d1 > 1e-9 or d2 > 1e-9:
            print(f"  MISMATCH {kin} {sync} v={v / C:+.1f} u={u / C:+.1f} s={s:+d}: engine {val:.10g} hand {ref:.10g} "
                  f"checks.py {chk_ref:.10g}")
    print(f"  {rows} configurations; max rel |engine/hand - 1| = {worst_eng:.1e}; "
          f"max rel |checks.py/hand - 1| = {worst_chk:.1e}")

    print("B. own-light round trip: checks.round_trip_speed vs hand-made")
    worst = 0.0
    for kin, v, orient in itertools.product(["SR", "ether", "emission"], [0.0, 0.5 * C, -0.8 * C],
                                            ["x", "y"]):
        ref = ref_round_trip(kin, "einstein", v, L0, orient)
        chk = checks.round_trip_speed(kin, C, abs(v), transverse=(orient == "y"))
        worst = max(worst, abs(chk / ref - 1))
    print(f"  max rel |checks.py/hand - 1| = {worst:.1e}")

    print("C. Doppler closed forms (checks.doppler_ratio) vs hand-made pulse arrival intervals")
    worst = 0.0
    for kin, bs, br, s in itertools.product(["SR", "ether", "emission"], [0.0, 0.4, -0.3], [0.0, 0.5, -0.6],
                                            [+1, -1]):
        c = C
        gs = 1 / math.sqrt(1 - bs * bs) if kin == "SR" else 1.0
        gr = 1 / math.sqrt(1 - br * br) if kin == "SR" else 1.0
        T0 = 1e-3  # proper period of the source
        # pulses k = 0, 1 emitted at lab times k*T0*gs from x_s = bs c t (source passes x=0 at t=0);
        # receiver at x_r = -s*1e6... receiver placed on the side the light travels to: x_r0 = s * 1e6 + br c t
        w = s * c + (bs * c if kin == "emission" else 0.0)
        arr = []
        for k in range(2):
            te = k * T0 * gs
            xe = bs * c * te
            # xe + w (t - te) = s*1e6 + br c t
            t = (s * 1e6 - xe + w * te) / (w - br * c)
            arr.append(t / gr)
        ratio = T0 / (arr[1] - arr[0])
        if abs(w - br * c) < 1e-9 * c:
            continue  # the light never reaches a receiver moving with it (degenerate, emission theory)
        worst = max(worst, abs(checks.doppler_ratio(kin, s, bs, br) / ratio - 1))
    print(f"  max rel |checks.py/hand - 1| = {worst:.1e}")


if __name__ == "__main__":
    main()
