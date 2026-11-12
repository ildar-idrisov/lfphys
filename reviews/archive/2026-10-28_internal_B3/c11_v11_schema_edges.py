# B3 review, check 11: v11 at the edges of its schema.
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
#  (a) a spin-1/2 path mark for particles the engine itself records without an internal state (lfphys.core.quantum.
#      particles: He-4 and C60 have internal = None): does the world build, and is it flagged as modified physics?
#  (b) the size of the computation at the corners of the schema: grid points, pairs of steps to the end (the run's own
#      estimate t_end_est), and an extrapolated wall time from the measured rate of the "narrow" preset on GPU 0
#      (745 x 640 points, ~1100 pairs in ~35 s with 100 Bohm particles: c03), against the README's "50-95 s on GPU 0;
#      many minutes on the CPU".
# CPU only, nothing is stepped.
# Run (from engine/):
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c11_v11_schema_edges.py > reviews/archive/2026-10-28_internal_B3/out/c11_v11_schema_edges.txt
import itertools
import math

from harness import Harness

from lfphys.core.quantum import particles
from v11_double_slit_2d.engine import apparatus as AP
from v11_double_slit_2d.viz import DT_E0, H_OF, SCHEMA

V = "v11_double_slit_2d"
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 100,
         "n_tracks": 10}
print("(a) a spin-1/2 mark for every particle of the schema")
for part in ("electron", "neutron", "he4", "c60"):
    p = particles.make(part, "lambda", 100e-12)
    try:
        h = Harness(V, "mark180", {**SMALL, "particle": part})
        hd = h.of("header")[-1]
        print(f"  {part:8s}: engine internal state = {p.internal!r}; world built: yes; modifications = "
              f"{hd.get('modifications')}; header particle.spin = {hd['particle']['spin']}; errors {h.errors()}")
    except Exception as e:  # noqa: BLE001
        print(f"  {part:8s}: engine internal state = {p.internal!r}; refused: {e}")

print("\n(b) the size of the computation at corners of the schema (normal grid unless stated)")
ref_pts, ref_pairs, ref_s = 745 * 640, None, 35.0
geo = AP.Geometry(2.0, 8.0, 2.0, 50.0, 8.0, 5.0, H_OF["normal"])
pair = 2 * DT_E0 / AP.E0
t_end = (abs(geo.z_src) + geo.L + 4 * geo.sz + 2 * geo.screen_half) / AP.V0_SPEED
ref_pairs = t_end / pair
rate = ref_s / (ref_pts * ref_pairs)
print(f"  narrow preset: grid {geo.grid().shape}, ~{ref_pairs:.0f} pairs (t_end_est / 2dt); measured ~{ref_s:.0f} s on GPU 0")
rows = []
for a, L, sx, sz, grid in itertools.product((0.5, 20.0), (5.0, 200.0), (1.0, 40.0), (2.0, 20.0), ("normal", "fine")):
    d = max(a + 1.0, 8.0) if a < 20 else 60.0
    try:
        g = AP.Geometry(a, d, 2.0, L, sx, sz, H_OF[grid])
    except ValueError as e:
        continue
    shape = g.grid().shape
    t_end = (abs(g.z_src) + g.L + 4 * g.sz + 2 * g.screen_half) / AP.V0_SPEED
    pairs = t_end / pair
    est = rate * shape[0] * shape[1] * pairs
    rows.append((est, a, d, L, sx, sz, grid, shape, pairs))
rows.sort(reverse=True)
for est, a, d, L, sx, sz, grid, shape, pairs in rows[:8]:
    mem = 16 * shape[0] * shape[1] * 8 / 2**30
    print(f"  a = {a:g}, d = {d:g}, L = {L:g}, sigma = ({sx:g}, {sz:g}), {grid}: grid {shape} = "
          f"{shape[0] * shape[1] / 1e6:.1f} M points, ~{pairs:.0f} pairs; extrapolated ~{est / 60:.0f} min on GPU 0 "
          f"(the wave and its companion), ~{mem:.1f} GB for 8 complex arrays")
print("  (schema limits: " + ", ".join(f"{k} {SCHEMA.by_id[k].min}..{SCHEMA.by_id[k].max}" for k in ("a", "d", "L", "sigma_x", "sigma_z")) + ")")
