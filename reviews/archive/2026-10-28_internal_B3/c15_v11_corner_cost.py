# B3 review, check 15: the measured cost of v11 at a corner of its schema (c11 extrapolated it): a = 0.5, d = 8,
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# L = 200, sigma = (40, 20), fine grid (3369 x 3072 points), 2000 Bohm particles. The world is built, 10 pairs of steps
# warm the device up (FFT plans, kernels), and the next 20 pairs are timed on GPU 0 (seconds of load, no long run); the time to the end is the run's own number of pairs
# (t_end_est / 2 dt) times the measured time per pair.
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c15_v11_corner_cost.py > reviews/archive/2026-10-28_internal_B3/out/c15_v11_corner_cost.txt
import time

from harness import Harness

V = "v11_double_slit_2d"
for params in ({}, {"a": 0.5, "d": 8.0, "L": 200.0, "sigma_x": 40.0, "sigma_z": 20.0, "grid": "fine"}):
    t0 = time.time()
    h = Harness(V, "narrow", params, seed=1)
    s = h.sim
    t_build = time.time() - t0
    pairs_total = s.t_end_est / s.pair
    for _ in range(10):
        s._pair()
    t1 = time.time()
    for _ in range(20):
        s._pair()
    per = (time.time() - t1) / 20
    print(f"{params or 'narrow preset'}: grid {s.g.shape} on {s.prop.device}; built in {t_build:.1f} s; "
          f"{per * 1e3:.1f} ms per pair (wave, companion, 2000 Bohm particles); ~{pairs_total:.0f} pairs to the "
          f"estimated end -> ~{per * pairs_total / 60:.1f} min of computation", flush=True)
