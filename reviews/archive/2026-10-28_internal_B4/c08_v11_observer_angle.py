# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Review B4, check c08: v11's observer (the which-path detector at slit B) — is the residual visibility at
# theta = 180 deg (README: 0.25 on the presets, "not understood", STATUS V26) a miscalibrated angle? The coupling b0 is
# set from theta = 2 b0 w / (hbar v0), the first-order rotation for the FREE mean speed v0; inside a narrow channel the
# longitudinal wavenumber is lower (the transverse mode's energy) and b0 = 0.25 E0 at 180 deg (w = 2) is not small, so
# the actual rotation differs. Scan theta and see where the visibility is smallest.
#
# Root (fix after archiving): engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this
# script in /lf/reviews/archive/2026-10-28_internal_B4/. CPU only, small geometry of the v11 tests, ~1-2 min per run.
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro \
#     -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-28_internal_B4/c08_v11_observer_angle.py [theta ...] > out/c08_v11_observer_angle.txt
#   (out/c08_v11_observer_angle.txt: 180 165 150; out/c08b_v11_observer_angle.txt: 155 145 140 130)
import math
import sys

from harness import Harness

V = "v11_double_slit_2d"
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 200,
         "n_tracks": 10}
E0 = 2 * math.pi ** 2
k0 = 2 * math.pi


def run(theta, extra=None):
    h = Harness(V, "observer", {**SMALL, "mark_deg": theta, **(extra or {})})
    while not h.sim.done:
        h.run_to(h.sim.t + 2.0 * h.sim.tunit)
    c = h.checks()["visibility"]
    return c["value"], c.get("ref")


a, w = SMALL["a"], SMALL["w"]
b0 = math.pi * k0 / (2 * w)
Eperp = 0.5 * (math.pi / a) ** 2
kp, km = math.sqrt(2 * (E0 - Eperp - b0)), math.sqrt(2 * (E0 - Eperp + b0))
print(f"a = {a} λ, w = {w} λ: b0(180°) = {b0:.3f} = {b0 / E0:.3f} E0; lowest transverse mode E_perp = {Eperp:.3f} "
      f"= {Eperp / E0:.3f} E0; in the channel k± = {kp:.3f}, {km:.3f}: (k− − k+) w = {(km - kp) * w:.4f} rad "
      f"(first-order design: π) -> |cos(θ_eff/2)| = {abs(math.cos((km - kp) * w / 2)):.3f}")
print(f"theta for a rotation of π in the lowest mode (same b0 scaling): ≈ {180 * math.pi / ((km - kp) * w):.1f}°")
sys.stdout.flush()
THETAS = [float(a) for a in sys.argv[1:]] or [180.0, 165.0, 150.0]
for th in THETAS:
    v, ref = run(th)
    print(f"theta = {th:5.1f}°: visibility {v:.4f} (two-path model |cos(θ/2)| = {ref if ref is not None else abs(math.cos(math.radians(th) / 2)):.4f})")
    sys.stdout.flush()
