"""Parameter sweep of v01 runs through the harness: modified c, edge geometries, all law combinations.
For every run: errors emitted, checks that are shown failed (|rel| > tol), and the number of arrivals.

Reviewer script (2026-10-22).

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_sweep.py
"""
from __future__ import annotations

import argparse
import math
import sys
import traceback
import warnings

sys.path.insert(0, "/lf/visualizations/tests")  # root path: the light-funnel tree mounted at /lf in the container
from harness import Harness  # noqa: E402

from v01_light_travel.engine.consts import C  # noqa: E402

V = "v01_light_travel"

RUNS = [
    # (label, preset, params, horizon, actions)
    ("sun_earth c x 2", "sun_earth", {"c_factor": 2.0}, 400.0, []),
    ("sun_earth c x 0.5", "sun_earth", {"c_factor": 0.5}, 1200.0, []),
    ("sun_earth gravity none", "sun_earth", {"gravity": "none"}, 600.0, []),
    ("sun_earth ether", "sun_earth", {"gravity": "none", "kinematics": "ether"}, 600.0, []),
    ("sun_earth emission", "sun_earth", {"gravity": "none", "kinematics": "emission"}, 600.0, []),
    ("sun_earth emission+newton", "sun_earth", {"gravity": "newton", "kinematics": "emission"}, 600.0, []),
    ("sun_earth 1e5 Msun (rs ~ 3e8 m), R = 2 rs", "sun_earth", {"se_mass": 1e5, "se_radius_km": 2 * 2.953 * 1e5},
     700.0, []),
    ("measure_c c x 3", "measure_c", {"c_factor": 3.0}, 0.02, []),
    ("measure_c v = +-0.99c", "measure_c", {"mc_v2": 0.99, "mc_v3": -0.99}, 0.5, []),
    ("measure_c emission u=-0.9", "measure_c_emission", {"mc_src_u": -0.9}, 0.1, []),
    ("measure_c lab sync ether", "measure_c", {"kinematics": "ether", "mc_sync": "lab"}, 0.04, []),
    ("measure_c transverse SR", "measure_c", {"mc_orient": "y"}, 0.04, [("measure", {"obj": "obs2"}, 0.004)]),
    ("measure_c flash at t=0", "measure_c", {"mc_t_flash_ms": 0.0}, 0.04, []),
    ("lensing c x 2", "lensing", {"c_factor": 2.0}, 0.05, []),
    ("lensing star R = 4 rs", "lensing", {"ln_radius_km": 4 * 29.53}, 0.2, []),
    ("lensing collinear (Einstein ring)", "lensing", {"ln_src_y_rs": 0.0}, 0.2, []),
    ("lensing near obs 5 rs", "lensing", {"ln_obs_rs": 5.0, "ln_src_rs": 5.0}, 0.2, []),
    ("lensing gravity none", "lensing", {"gravity": "none"}, 0.2, []),
    ("lensing newton BH R=0", "lensing", {"kinematics": "emission", "gravity": "newton"}, 0.2, []),
    ("andromeda c x 3", "andromeda", {"c_factor": 3.0}, 1e14, []),
    ("andromeda fast", "andromeda_fast", {}, 1e14, []),
    ("andromeda 1e-9 Mly", "andromeda", {"an_dist_mly": 1e-9}, 1e6, []),
    ("andromeda 1e4 Mly", "andromeda", {"an_dist_mly": 1e4}, 4e17, []),
    ("andromeda ether", "andromeda", {"kinematics": "ether"}, 1e14, []),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    warnings.simplefilter("ignore")
    for label, preset, params, horizon, acts in RUNS:
        try:
            h = Harness(V, preset, params)
        except Exception as e:  # noqa: BLE001
            print(f"[{label}] not created: {type(e).__name__}: {e}")
            continue
        try:
            h.sim.advance(h.sim.t)
            done = []
            for k in range(1, 9):
                tk = horizon * k / 8
                for name, args, ta in acts:
                    if ta <= tk and (name, ta) not in done:
                        h.run_to(ta)
                        h.action(name, **args)
                        done.append((name, ta))
                h.run_to(tk)
                h.sim.frame()
        except Exception:  # noqa: BLE001
            print(f"[{label}] EXCEPTION at t = {h.sim.t:.6g}:\n" + "".join(traceback.format_exc().splitlines(True)[-3:]))
        bad = []
        for c in h.checks().values():
            if c["ref"] is not None and c["rel"] is not None and abs(c["rel"]) > max(c.get("tol") or 1e-9, 1e-12):
                bad.append(f"{c['label']}: {c['value']:.10g} vs {c['ref']:.10g} (rel {c['rel']:.1e}, tol {c['tol']:.0e})")
        arr = [e for e in h.of("event") if e["kind"] == "arrival"]
        mods = h.of("header")[0]["modifications"]
        print(f"[{label}] t = {h.sim.t:.4g}; mods = {[m['id'] for m in mods]}; arrivals {len(arr)}; "
              f"checks {len(h.checks())}; errors {len(h.errors())}; failed checks {len(bad)}")
        for e in h.errors()[:2]:
            print("    error:", e.strip().splitlines()[-1][:160])
        for b in bad[:4]:
            print("    failed:", b)


if __name__ == "__main__":
    main()
