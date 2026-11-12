# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Response to B4-3: the observer at slit B after the channel calibration, on the reviewer's small geometry (He-4, a = 1.5, w = 1,
# edges 0.2): visibility and the down share of the flux behind slit B against the nominal theta.
# Root: engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine). CPU, ~1-2 min per angle.
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-28_internal_B4/response_checks/r03_observer_angle.py 180 165 150 200
import sys, math
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 200, "n_tracks": 10}
for th in [float(x) for x in sys.argv[1:]]:
    h = Harness("v11_double_slit_2d", "observer", {**SMALL, "mark_deg": th})
    cal = h.sim.mark_cal
    while not h.sim.done:
        h.run_to(h.sim.t + 2.0 * h.sim.tunit)
    c = h.checks()["visibility"]; r = h.of("result")[-1]
    bad = [k for k, v in h.checks().items() if not v.get("info") and v.get("ok") is False]
    print(f"theta {th}: b0 {h.sim.mark_cal.coupling(math.radians(th)):.3f} (first order {th*math.pi/180*2*math.pi/(2*1.0):.3f}) E_perp {cal.E_perp/19.7392:.3f} c_x {cal.c_x:.3f}; visibility {c['value']:.4f} ref {c['ref']:.4f}; down share behind slit B {r['mark']['down_fraction']:.3f}; failed {bad}", flush=True)
