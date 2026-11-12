# B2 review, check 8: v09 (a) what the header reveals at t = 0 about the manoeuvre's outcome; (b) the factor by which a
# drag preview's readout is off: env3d.js previews from the volume (normalised by the field's global peak) but the
# window reads values as I * quantity.peak of the last slice (normalised by that slice's own peak); (c) whether the
# shown "accumulated angle" of planar loops is computed by the run or is the closed form.
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests light-funnel-viz python3 reviews/2026-10-27_internal_B2/c08_v09_reveal_and_preview.py
import math

import numpy as np
from harness import Harness

V = "v09_thomas_3d"
h = Harness(V, "thomas", {"ngrid": 48})
hdr = h.of("header")[0]
L = hdr["loop"]
print("(a) header at t = 0 (before anything ran):")
print(f"    loop.T_end  = {L['T_end']:.6g} yr (lab duration of the whole manoeuvre)")
print(f"    loop.tau_end = {L['tau_end']:.6g} yr (the craft's proper time at the end)")
print(f"    loop.eta_max = {L['eta_max']:.6g} (largest gamma {math.cosh(L['eta_max']):.6g})")
print(f"    scene3d.box (lab space only: the extent of the whole future trajectory) -> see lab below")
hl = Harness(V, "lab", {})
print(f"    lab preset: scene3d.box = {hl.of('header')[0]['scene3d']['box']} at t = {hl.sim.t}")
print(f"    view.js drawLoop() shows T_end, tau_end and cosh(eta_max) in the panel «Манёвр и голономия» on the header")

print("(b) drag preview readout in v09 (theta field): global volume peak vs each slice's own peak")
sim = h.sim
for pid, n, o in ((1, None, None), (2, (1.0, 0.0, 0.0), [0, 0, 0]), (3, (0.0, 0.0, 1.0), [0, 0, 0.6]),
                  (2, (1.0, 0.0, 0.0), [-0.6, 0, 0])):
    if n is not None:
        h.cmd("view", op="plane", id=pid, origin=o, normal=list(n))
    sl = [m for m in h.of("slice") if m["id"] == pid and not m.get("preview")][-1]
    qpk = sl["quantity"]["peak"]
    print(f"    slice {pid} ({sl['label']}): its peak theta = {qpk:.4f} rad; volume peak theta = "
          f"{sim.field_peak * math.pi:.4f} rad -> preview readout off by x{qpk / (sim.field_peak * math.pi):.3f}")

print("(c) planar loop: the shown accumulated angle vs what the run computes")
hp = Harness(V, None, {"loop": "circle", "rho": 1.5, "turns": 2, "ngrid": 48})
hp.run_to(hp.sim.T_end * 1.0001)
r = hp.of("holonomy")[0]
print(f"    holonomy message: angle (SO(3), computed) = {r['angle']:.6f}, su2_angle (computed) = {r['su2_angle']:.6f}, "
      f"reference (closed form) = {r['reference']:.6f} shown as «накопленный угол = площадь»; per_bound = "
      f"reference / bound = {r['per_bound']:.6f}")
