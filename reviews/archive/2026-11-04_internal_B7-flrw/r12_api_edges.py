"""r12: small API edges (each line: call -> result).
Run (from engine/):
  docker run --rm --name lf-b7rc-r12 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r12_api_edges.py
"""
import sys

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.cosmology import flrw as F  # noqa: E402


def show(label, f):
    try:
        r = f()
    except Exception as exc:  # noqa: BLE001
        r = f"{type(exc).__name__}: {exc}"
    print(f"{label:60s} -> {r}")


show("Background(70, -0.1)  (negative dust density)", lambda: F.Background(70, -0.1))
show("from_physical(0.7, 0.022, 0.12, T_cmb=2.7255, N_eff=3.046, OL=0.7)",
     lambda: F.from_physical(0.7, 0.022, 0.12, T_cmb=2.7255, N_eff=3.046, OL=0.7).Ok)
bg = F.planck2018()
show("angular_diameter_distance_z1z2(2.0, 0.5)  (z1 > z2)", lambda: bg.angular_diameter_distance_z1z2(2.0, 0.5))
d = bg.densities(1.0)
show("sum of densities(1.0) over all keys (docstring: 'they sum to one')", lambda: sum(d.values()))
show("sum without 'baryons'", lambda: sum(v for k, v in d.items() if k != "baryons"))
