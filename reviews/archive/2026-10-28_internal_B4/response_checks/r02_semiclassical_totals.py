# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Response to B4-2: the semiclassical rule of v12 through its CDF in k. The reviewer's four train worlds (accepted by
# the cost guard on GPU 0) and the preset: the total within the window, the curve's bin averages integrated, against
# the exact F_SC(t_obs); the mean against quadrature in k. Builds the worlds only (no run).
# Root: engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine). GPU 0 (one world exceeds the CPU cost limit).
#   add --gpus device=0 to the command below
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests \
#     light-funnel-viz python3 /lf/reviews/archive/2026-10-28_internal_B4/response_checks/r02_semiclassical_totals.py
import numpy as np
from harness import Harness

for n, sep in ((4, 30.0), (4, 60.0), (8, 30.0), (4, 90.0), (5, 60.0)):
    try:
        h = Harness("v12_arrival_times_2d", "train", {"n_train": n, "sep": sep})
    except ValueError as e:  # refused by the cost guard (an estimate at the limit)
        print(f"N = {n}, sep = {sep:g} λ: refused — {e}")
        continue
    c, sc = h.sim.curves, h.sim.sc_rule
    tau = c["tau"]
    dt = tau[1] - tau[0]
    area = float(np.sum(c["sc"]) * dt)  # bin averages over [tau_i - dt/2, tau_i + dt/2]
    exact = float(sc.cdf(tau[-1] + 0.5 * dt)[0])
    tot, mean, sd = sc.moments(float(tau[-1]))
    print(f"N = {n}, sep = {sep:g} λ: curve area {area:.6f}, exact F_SC {exact:.6f}, total in the window {tot:.6f}, "
          f"mean {mean / h.sim.t0:.4f} t0, sd {sd / h.sim.t0:.4f} t0, k samples {len(sc.k)}")
