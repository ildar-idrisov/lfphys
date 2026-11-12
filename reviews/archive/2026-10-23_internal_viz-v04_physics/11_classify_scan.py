"""11: OrbitStream._classify against 40-digit truth on a grid of tangential launches (v_r = 0 exactly) near the circular
speed, and on boosts of circular orbits (v_r ~ 1e-17 from the dense output).

Truth: roots of F(y) = 2 u_s y^3 - y^2 + 2 A y + B at 40 digits from the same float launch data; y = 1 is the start;
the allowed interval is the one containing y = 1 (F >= 0 there); kind: 'circular' if the interval collapses to a
point within 1e-6 (the code's own criterion), 'bound' if both ends are turning points with y > 0 and the inner one
below y_stop, 'plunge' if no inner turning point, 'escape' if no outer one. The direction of motion is not needed for a
start at a turning point.
"""
import math

import mpmath as mp

from lfphys.core.gravity import orbit_stream as osm

mp.mp.dps = 40


def truth(r0, vr, vp):
    R0, VR, VP = mp.mpf(r0), mp.mpf(vr), mp.mpf(vp)
    v2 = VR**2 + VP**2
    g2 = 1 / (1 - v2)
    EM1, L = g2 * (v2 - 2 / R0), mp.sqrt(g2) * VP * R0
    us = 1 / R0
    A, B = 1 / (L**2 * us), EM1 / (L**2 * us**2)
    F = lambda y: 2 * us * y**3 - y**2 + 2 * A * y + B
    ys = sorted([mp.re(z) for z in mp.polyroots([2 * us, -1, 2 * A, B], maxsteps=400, extraprec=400)
                 if abs(mp.im(z)) < mp.mpf(10) ** -25])
    # the allowed interval containing 1: nearest roots on both sides, using F's sign just inside
    eps = mp.mpf(10) ** -30
    lo = max([y for y in ys if y < 1 - eps] + [y for y in ys if abs(y - 1) <= eps and F(1 - mp.mpf(10) ** -20) < 0],
             default=None)
    hi = min([y for y in ys if y > 1 + eps] + [y for y in ys if abs(y - 1) <= eps and F(1 + mp.mpf(10) ** -20) < 0],
             default=None)
    y_stop = R0 / (2 / (1 - mp.mpf(osm.HORIZON_GAP)))
    r_peri = R0 / hi if hi is not None and hi < y_stop else None
    r_apo = R0 / lo if lo is not None and lo > 0 else None
    if r_peri is not None and r_apo is not None and r_apo - r_peri <= mp.mpf(10) ** -6 * r_peri:
        k = "circular"
    elif r_peri is not None and r_apo is not None:
        k = "bound"
    elif r_peri is None:
        k = "plunge"
    else:
        k = "escape"
    return k, r_peri, r_apo


wrong = 0
total = 0
print("tangential launches at r0 with speed k x circular (v_r = 0 exactly):")
for r0 in (6.01, 6.1, 6.5, 7.0, 10.0, 20.0, 100.0, 1e4):
    row = []
    for dk in (-1e-3, -1e-4, -1e-5, -1e-6, 1e-6, 1e-5, 1e-4, 1e-3):
        k = 1 + dk
        vp = k * math.sqrt(1 / (r0 - 2))
        st = osm.OrbitStream(r0, 0.0, vp)
        kt, rp, ra = truth(r0, 0.0, vp)
        total += 1
        bad = st.info["kind"] != kt
        wrong += bad
        row.append(f"{dk:+.0e}:{st.info['kind'][:4]}{'!=' + kt[:4] if bad else ''}")
    print(f"  r0={r0:<7g} " + " ".join(row))
print(f"  -> {wrong} of {total} kinds wrong")

print("\nexamples (run vs truth):")
for r0, dk in ((6.01, 1e-5), (6.5, 1e-4), (7.0, 1e-5), (10.0, -1e-5)):
    vp = (1 + dk) * math.sqrt(1 / (r0 - 2))
    st = osm.OrbitStream(r0, 0.0, vp)
    kt, rp, ra = truth(r0, 0.0, vp)
    print(f"  r0={r0} k=1{dk:+.0e}: run {st.info['kind']} r_peri={st.info['r_peri']!r} r_apo={st.info['r_apo']!r} | "
          f"truth {kt} r_peri={mp.nstr(rp, 12) if rp else None} r_apo={mp.nstr(ra, 12) if ra else None}")

print("\nboosts of a circular orbit: state (r, v_r ~ 1e-17, v_phi) then v -> v (1 + dv):")
wrong = total = 0
for r0 in (6.2, 8.0, 20.0, 1e3):
    row = []
    vc = math.sqrt(1 / (r0 - 2))
    for dv in (-0.3, -0.05, -1e-3, 1e-3, 0.05, 0.3):
        for vr in (3e-17, -3e-17):
            vp = vc * (1 + dv)
            st = osm.OrbitStream(r0, vr * (1 + dv), vp)
            kt, rp, ra = truth(r0, vr * (1 + dv), vp)
            total += 1
            bad = st.info["kind"] != kt or (kt == "bound" and (abs(st.info["r_peri"] - float(rp)) > 1e-6 * float(rp)
                                                               or abs(st.info["r_apo"] - float(ra)) > 1e-6 * float(ra)))
            wrong += bad
            row.append(f"{dv:+.0e}/{'+' if vr > 0 else '-'}:{st.info['kind'][:4]}{'!=' + kt[:4] if bad else ''}")
    print(f"  r0={r0:<6g} " + " ".join(row))
print(f"  -> {wrong} of {total} wrong (kind, or bound with wrong turning points)")
