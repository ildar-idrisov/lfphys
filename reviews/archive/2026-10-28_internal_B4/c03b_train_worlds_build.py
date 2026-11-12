# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Review B4, check c03b: which long trains does v12 accept (its cost guard), and what does the world itself report for
# the semiclassical rule (the totals of «Итоги по правилам» come from Simulation.curves, built at construction)?
#
# Root (fix after archiving): engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this
# script in /lf/reviews/archive/2026-10-28_internal_B4/. CPU only (the GPU estimate is computed from v11's GPU rates).
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro \
#     -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-28_internal_B4/c03b_train_worlds_build.py > out/c03b_train_worlds_build.txt
import numpy as np

from harness import Harness
from v11_double_slit_2d import viz as V11

# the container has no GPU: lift the CPU limit so that the world is built, then judge it by the GPU rates and limit
V11.COST_LIMIT["cpu"] = 1e12

for params in ({"state": "train"}, {"state": "train", "n_train": 8, "sep": 60.0},
               {"state": "train", "n_train": 6, "sep": 60.0}, {"state": "train", "n_train": 4, "sep": 60.0},
               {"state": "train", "n_train": 8, "sep": 120.0}, {"state": "train", "n_train": 5, "sep": 90.0},
               {"state": "train", "n_train": 8, "sep": 30.0}, {"state": "train", "n_train": 5, "sep": 60.0},
               {"state": "train", "n_train": 3, "sep": 120.0}, {"state": "train", "n_train": 4, "sep": 90.0}):
    try:
        h = Harness("v12_arrival_times_2d", "train", {**params, "n_bohm": 300})
    except Exception as e:  # noqa: BLE001
        print(params, "REFUSED:", str(e)[:160])
        continue
    s = h.sim
    pairs = s.t_end_est / s.pair
    per_point, per_particle = V11.RATES["gpu"]
    steps = 2 + (s.geo.h / s._companion_step()) ** 2 + (2 if s.soft else 0)
    gpu_est = pairs * (s.g.size * steps * per_point + 300 * per_particle)
    c = s.curves
    w = np.gradient(c["tau"])
    w[0] *= 0.5
    w[-1] *= 0.5
    tot = float(np.sum(c["sc"] * w))
    print(params, f"built: grid {s.g.shape}, cost estimate {s.est_cost / 60:.1f} min on {s.prop.device}, "
                  f"GPU estimate {gpu_est / 60:.1f} min (limit 10: {'accepted' if gpu_est <= 600 else 'refused'} on GPU 0); semiclassical total over the window from the "
                  f"world's own curve: {tot:.4f} (exact 1.0000)")
