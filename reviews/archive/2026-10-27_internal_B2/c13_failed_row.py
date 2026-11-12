# B2 review, check 13: how a failed `holonomy` row of B2-1 reads in the checks panel (value, ref, rel, tol, ok).
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests light-funnel-viz python3 reviews/2026-10-27_internal_B2/c13_failed_row.py
from harness import Harness

p = {"space": "lab", "loop": "triangle", "rho": 2.6877902048795144, "turns": 3, "alpha": 57.76537981020704,
     "nth": 25.230265411303613, "nph": 123.45851349639912, "accel_g": 2.070161305081177}
h = Harness("v09_thomas_3d", None, p)
h.run_to(h.sim.T_end * 1.0001)
for cid in ("holonomy", "holonomy_su2", "closed", "roundoff"):
    c = h.checks()[cid]
    print(f"{cid:13s} value={c['value']!r} ref={c['ref']!r} rel={c['rel']!r} tol={c['tol']:.3e} ok={c.get('ok')}")
    if cid == "holonomy":
        print("   note:", c["note"])
