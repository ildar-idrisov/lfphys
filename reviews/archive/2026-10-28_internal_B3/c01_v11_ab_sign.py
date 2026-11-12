# B3 review, check 1: the sign of the Aharonov-Bohm fringe shift in v11 — the run, the `ab_phase` reference and the
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# approximate theories' patterns (`ref_paraxial`, `ref_kirchhoff`), at a flux that is not a half quantum (at Phi0/2 a
# shift of +pi and -pi are the same, so the tests' `ab` preset cannot tell the sign).
# The small geometry of v11's own tests (a = 1.5, d = 4, w = 1, L = 12, coarse grid), electron (q < 0).
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c01_v11_ab_sign.py > reviews/archive/2026-10-28_internal_B3/out/c01_v11_ab_sign.txt
import math
import time

import numpy as np
from harness import Harness

from v11_double_slit_2d.engine import apparatus as AP

V = "v11_double_slit_2d"
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 300,
         "n_tracks": 20}


def run_out(h, tau_max=60.0):
    tu = h.sim.tunit
    while not h.sim.done and h.sim.tau < tau_max:
        h.run_to(h.sim.t + 1.0 * tu)
    return h


def phase_of(xs, P, period):
    m = np.abs(xs) <= 1e9
    Pn = P / np.trapezoid(P, xs)
    return AP.fringes(xs, Pn, period)


rows = []
for flux in (0.0, 0.25, -0.25, 0.5):
    t0 = time.time()
    h = run_out(Harness(V, "narrow", {**SMALL, "flux": flux}))
    sim = h.sim
    xs, P = sim._pattern(sim.flux)
    m = sim.on_screen
    period = (sim.geo.L - 0.5 * sim.geo.w) / sim.geo.d
    V_run, ph_run = phase_of(xs[m], P[m], period)
    refs = h.of("result")[-1].get("refs", {})
    out = {"flux": flux, "device": sim.prop.device, "wall_s": round(time.time() - t0, 1),
           "run": (V_run, ph_run)}
    for k in ("paraxial", "kirchhoff"):
        if k in refs:
            R = np.asarray(refs[k])
            out[k] = phase_of(xs[m], R[m], period)
    c = h.checks()
    out["check_ab_phase"] = (c.get("ab_phase", {}).get("value"), c.get("ab_phase", {}).get("ref"))
    out["check_ref_paraxial"] = c.get("ref_paraxial", {}).get("value")
    out["check_ref_kirchhoff"] = c.get("ref_kirchhoff", {}).get("value")
    out["charge_sign"] = int(np.sign(sim.part.charge))
    rows.append(out)
    print(out, flush=True)

print()
print("fringe phase phi (P ~ 1 + V cos(q x - phi)), radians; electron: physical phase phi_B - phi_A = q Phi / hbar")
print(f"{'flux/Phi0':>9} {'run':>9} {'ab_phase ref':>13} {'paraxial ref':>13} {'kirchhoff ref':>14}  "
      f"{'ref_paraxial dev':>16} {'ref_kirchhoff dev':>17}")
base = rows[0]
for r in rows:
    d = lambda a: math.remainder(a - (base["run"][1] if r is not base else 0.0), 2 * math.pi)
    print(f"{r['flux']:>9.2f} {r['run'][1]:>9.4f} {str(r['check_ab_phase'][1]):>13.13} "
          f"{r.get('paraxial', (0, float('nan')))[1]:>13.4f} {r.get('kirchhoff', (0, float('nan')))[1]:>14.4f}  "
          f"{str(r['check_ref_paraxial']):>16.16} {str(r['check_ref_kirchhoff']):>17.17}")
