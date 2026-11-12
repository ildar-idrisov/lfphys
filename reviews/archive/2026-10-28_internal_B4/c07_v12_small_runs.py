# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Review B4, check c07: v12 on small geometries (the tests' SMALL, CPU), against closed forms the world does not use
# in its checks:
# (a) the Marchewka-Schuss input d2(t) = int |d psi/dz (x, L, t)|^2 dx (order-32 differences on the plane; no check of
#     its own) against the exact free |d phi/dz (D, t)|^2;
# (b) the Bohm first-arrival law: the world's (running maximum of the run's flux integral) against the exact law from
#     the closed-form P(z < D, t), and the Bohm hits against the exact law (KS);
# (c) what the header reveals at t = 0: the observation window (closed-form leave time) and the curves of the rules
#     computed from the initial state (sent at t = 0);
# (d) backflow (small): the flux against the closed form through the backflow, and the hits against the exact law.
#
# Root (fix after archiving): engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this
# script in /lf/reviews/archive/2026-10-28_internal_B4/. CPU only, a few minutes.
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro \
#     -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-28_internal_B4/c07_v12_small_runs.py > out/c07_v12_small_runs.txt
import math

import numpy as np

from harness import Harness

V = "v12_arrival_times_2d"
SMALL = {"grid": "coarse", "n_bohm": 300, "n_tracks": 20, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0}


def run_out(h):
    while not h.sim.done:
        h.run_to(h.sim.t + 2.0 * h.sim.tunit)
    return h


def exact_first_arrival(fg, D, tau):
    F = fg.cdf(D, tau)
    return F[0] - np.minimum.accumulate(F)


def ks(hits, tau, law):
    F = law / law[-1]
    emp = np.searchsorted(np.sort(hits), tau, side="right") / len(hits)
    return float(np.max(np.abs(emp - F)))


for name, preset, extra in (("gauss SMALL", "gauss", {"soft": False}),
                            ("backflow SMALL", "backflow", {"sigma_z": 2.0, "L": 11.0, "soft": False, "n_bohm": 400})):
    h = Harness(V, preset, {**SMALL, **extra})
    s = h.sim
    hd = h.of("header")[-1]
    ref = h.of("arrival_ref")
    print(f"\n== {name} ==")
    print(f"(c) at t = 0 the header carries arrival.tau_obs = {hd['arrival']['tau_obs']:.6g} (= {hd['arrival']['tau_obs'] / hd['arrival']['t0_units']:.4f} t0, "
          f"the closed-form leave time x 1.02); 'arrival_ref' messages at t = 0: {len(ref)} "
          f"(curves to tau = {float(h.msgs[[m for m, _ in h.msgs].index(ref[0])][1]['tau'][-1]) if ref else 0:.6g})")
    run_out(h)
    ser = s._series()
    tau = ser["tau"]
    D = s.D
    d2x = np.abs(s.fg.dpsi(D, tau)) ** 2
    d2 = np.asarray(s.rec["d2"])
    print(f"(a) d2: max|run - exact| / max exact = {float(np.max(np.abs(d2 - d2x)) / d2x.max()):.2e} "
          f"(arr_plane_psi for |psi|^2 reports {h.checks()['arr_plane_psi']['value']:.2e})")
    law_x = exact_first_arrival(s.fg, D, tau)
    C = np.cumsum(ser["flux"]) * s.dt
    law_run = np.maximum.accumulate(np.maximum(C, 0.0))
    print(f"(b) first-arrival law: max|world's - exact| = {float(np.max(np.abs(law_run - law_x))):.2e} "
          f"(exact total by the window end {law_x[-1]:.6f})")
    hits = s.hit_t[s.fate == 1] / s.tunit
    print(f"    Bohm hits ({len(hits)} of {len(s.fate)}): KS against the exact law {ks(hits, tau, law_x):.4f}, "
          f"against the world's law {ks(hits, tau, law_run):.4f}; world's check arr_bohm_times = "
          f"{h.checks()['arr_bohm_times']['value']:.4f}, critical 1.95/sqrt(n) = {1.95 / math.sqrt(len(hits)):.4f}")
    Jx = s.fg.current(D, tau)
    print(f"(d) flux: max|run - exact| / max|exact| = {float(np.max(np.abs(ser['flux'] - Jx)) / np.max(np.abs(Jx))):.2e}; "
          f"backflow run {float(np.clip(-ser['flux'], 0, None).sum() * s.dt):.5f} vs exact "
          f"{float(np.clip(-Jx, 0, None).sum() * s.dt):.5f}")
    bad = [k for k, c in h.checks().items() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]
    print(f"    failed checks: {bad}")
