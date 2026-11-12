"""03: lfphys.core.gravity.orbit_stream against 50-digit references computed here without the project's code.

For bound orbits: turning points (mp roots of the cubic in u, from e^2 - 1 and l recomputed in mp from the same
float launch data), the advance per radial period (chi-integral), the radial period in t and in tau (quadrature with
r = c - d cos th, which removes the turning-point singularities), against the stream's periapsis events.
For plunges: t and tau from r0 to the stop radius r_stop = 2/(1 - 1e-6) (quadrature in r with the turning-point
substitution when the start is not a turning point), against the stream's horizon event.
Clock: 1 - dtau/dt at sample radii against mp.
"""
import math

import mpmath as mp
import numpy as np

from lfphys.core.gravity import orbit_stream as osm

mp.mp.dps = 40


def launch(r0, k, alpha_deg):
    v = k * min(math.sqrt(1.0 / (r0 - 2.0)), 1.0)
    a = math.radians(alpha_deg)
    vr, vp = v * math.sin(a), v * math.cos(a)
    if abs(vp) <= 1e-12 * v:
        vp = 0.0
    return vr, vp


def mp_consts(r0, vr, vp):
    R0, VR, VP = mp.mpf(r0), mp.mpf(vr), mp.mpf(vp)
    v2 = VR**2 + VP**2
    g2 = 1 / (1 - v2)
    return mp.sqrt(g2) * mp.sqrt(1 - 2 / R0), g2 * (v2 - 2 / R0), mp.sqrt(g2) * VP * R0


def run_stream(st, n_peri=4, max_chunks=4000):
    evs = []
    for _ in range(max_chunks):
        if st.done:
            break
        evs += st.advance(1e300, 2.0)["events"]
        if sum(e["kind"] == "peri" for e in evs) >= n_peri:
            break
    return evs


print("=== bound orbits: stream vs 40-digit references ===")
cases = [(20.0, 1.2, 0.0), (10.0, 1.12, 0.0), (7.0, 0.995, 0.0), (6.5, 1.05, 10.0), (12.0, 1.05, 25.0),
         (5.5, 1.003, 0.0), (4.6, 1.0005, 0.0), (1e3, 1.3, -20.0), (1e6, 0.5, 30.0), (1e8, 1.2, 0.0)]
for r0, k, al in cases:
    vr, vp = launch(r0, k, al)
    st = osm.OrbitStream(r0, vr, vp)
    E, EM1, L = mp_consts(r0, vr, vp)
    U = sorted([mp.re(z) for z in mp.polyroots([2, -1, 2 / L**2, EM1 / L**2], maxsteps=400, extraprec=400)
                if abs(mp.im(z)) < mp.mpf(10) ** -30])
    if len(U) != 3 or st.info["kind"] != "bound":
        print(f"r0={r0} k={k} al={al}: kind {st.info['kind']}, mp roots {[mp.nstr(u, 8) for u in U]}")
        continue
    u1, u2, u3 = U
    rp, ra, r3 = 1 / u2, 1 / u1, 1 / u3
    p, ecc = 2 / (u1 + u2), (u2 - u1) / (u2 + u1)
    mu = 1 / p
    adv = mp.quad(lambda c: 1 / mp.sqrt(1 - 2 * mu * (3 + ecc * mp.cos(c))), [0, mp.pi, 2 * mp.pi]) - 2 * mp.pi
    cc, dd = (ra + rp) / 2, (ra - rp) / 2
    w = lambda th: mp.sqrt((cc - dd * mp.cos(th)) ** 3 / (abs(EM1) * (cc - dd * mp.cos(th) - r3)))
    t_r = 2 * mp.quad(lambda th: E / (1 - 2 / (cc - dd * mp.cos(th))) * w(th), [0, mp.pi / 2, mp.pi])
    tau_r = 2 * mp.quad(w, [0, mp.pi / 2, mp.pi])
    evs = run_stream(st, 4)
    P = [e for e in evs if e["kind"] == "peri"]
    A = [e for e in evs if e["kind"] == "apo"]
    d_adv = [float((x - adv) / adv) for x in (np.diff([e["psi"] for e in P]) - 2 * math.pi)]
    d_t = [float((x - t_r) / t_r) for x in np.diff([e["t"] for e in P])]
    d_tau = [float((x - tau_r) / tau_r) for x in np.diff([e["tau"] for e in P])]
    d_rp = max(abs(float((e["r"] - rp) / rp)) for e in P)
    d_ra = max(abs(float((e["r"] - ra) / ra)) for e in A) if A else float("nan")
    d_em1 = max(abs((e["em1_state"] - st.em1) / st.em1) for e in P + A)
    print(f"r0={r0:<8g} k={k:<6g} al={al:<5g} p={float(p):.5g} ecc={float(ecc):.4f} adv={float(adv):.6e} | "
          f"rel err adv max {max(map(abs, d_adv)):.1e}, t_r {max(map(abs, d_t)):.1e}, tau_r {max(map(abs, d_tau)):.1e}, "
          f"r_peri {d_rp:.1e}, r_apo {d_ra:.1e}, em1_state {d_em1:.1e}; em1 float vs mp {float((st.em1 - EM1) / EM1):.1e}")

print("\n=== plunges: horizon event vs 40-digit quadrature to the radius of the event ===")
RS = mp.mpf(2) / (1 - mp.mpf(osm.HORIZON_GAP))
for r0, k, al in [(5.5, 0.995, 0.0), (8.0, 0.9, 20.0), (30.0, 0.3, -40.0), (20.0, 0.0, 0.0), (1e4, 0.0005, 0.0),
                  (1e6, 0.0, 0.0), (1e8, 1e-6, 0.0), (3.5, 0.5, 60.0), (2.1, 0.5, -30.0), (1e8, 0.0, 0.0)]:
    vr, vp = launch(r0, k, al)
    st = osm.OrbitStream(r0, vr, vp)
    E, EM1, L = mp_consts(r0, vr, vp)
    Rf = lambda r: EM1 + 2 / r - L**2 / r**2 + 2 * L**2 / r**3
    r_apo = st.info.get("r_apo")
    evs = run_stream(st, 10**9, max_chunks=20000)
    stop = evs[-1] if evs else None
    if stop is None or stop["kind"] != "horizon":
        print(f"r0={r0} k={k} al={al}: no horizon event ({st.done}, kind {st.info['kind']})")
        continue

    def legs(fn):
        # integral of fn(r) dr / sqrt(R) over the path r0 -> (apoapsis if outward) -> r_stop
        def seg(a, b):  # a < b, turning point possible at b (or a)
            h = (b - a) / 2
            g = lambda th: fn(a + h * (1 - mp.cos(th))) * h * mp.sin(th) / mp.sqrt(abs(Rf(a + h * (1 - mp.cos(th)))))
            return mp.quad(g, [0, mp.pi / 2, mp.pi])
        if vr > 0:
            ra = mp.mpf(r_apo) if r_apo else None
            # refine the apoapsis in mp
            ra = mp.findroot(Rf, ra)
            return seg(mp.mpf(r0), ra) + seg(RS, ra)
        return seg(RS, mp.mpf(r0))

    if stop["r"] <= 2.0:
        print(f"r0={r0:<8g} k={k:<6g} al={al:<5g} kind={st.info['kind']:<12} STOP EVENT INSIDE THE HORIZON: "
              f"r = {stop['r']!r}, v_r = {stop['v_r']!r}")
        continue
    RS = mp.mpf(stop["r"])  # quadrature to the radius where the stream actually stopped
    tau = legs(lambda r: 1)
    t = legs(lambda r: E / (1 - 2 / r))
    RS = mp.mpf(2) / (1 - mp.mpf(osm.HORIZON_GAP))
    print(f"r0={r0:<8g} k={k:<6g} al={al:<5g} kind={st.info['kind']:<12} r_event-2 = {stop['r'] - 2:.6e} "
          f"(nominal {float(RS - 2):.6e}) | "
          f"rel err tau {float((stop['tau'] - tau) / tau):+.1e}, t {float((stop['t'] - t) / t):+.1e} "
          f"(t = {float(t):.6e} M)")

print("\n=== clock: 1 - dtau/dt = (e - 1 + 2/r)/e vs mp ===")
for r0, k, al in [(3.1152981116278067e7, 1.0980121538489453, 0.0), (20.0, 1.2, 0.0), (1e8, 1.0, 0.0), (2.1, 0.5, 0.0)]:
    vr, vp = launch(r0, k, al)
    st = osm.OrbitStream(r0, vr, vp)
    E, EM1, L = mp_consts(r0, vr, vp)
    worst = 0.0
    for r in np.geomspace(2.000002, 10 * r0, 50):
        ref = 1 - (1 - 2 / mp.mpf(r)) / E
        worst = max(worst, abs(float((st.clock_lag(r) - ref) / ref)))
    print(f"r0={r0:.6g}: max rel err of clock_lag over r in [2.000002, 10 r0]: {worst:.1e}")
