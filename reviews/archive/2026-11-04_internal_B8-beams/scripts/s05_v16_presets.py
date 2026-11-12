"""s05: v16 presets through visualizations/tests/harness.py (no server): every check as emitted (value, ref, tol, ok,
info), the 'am' message, the build time, for the presets named on the command line (default: all)."""
import json
import math
import sys
import time

for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from harness import Harness  # noqa: E402
from v16_optical_vortices.viz import SCHEMA  # noqa: E402


def show(preset, params, t_end):
    t0 = time.time()
    h = Harness("v16_optical_vortices", preset, params)
    t1 = time.time()
    h.run_to(t_end)
    t2 = time.time()
    print(f"=== preset {preset} {params or ''}: build {t1 - t0:.1f} s, run to {t_end} s world: {t2 - t1:.1f} s;"
          f" errors {h.errors()}")
    hd = h.of("header")[0]
    print("  approximations:", hd["approximations"])
    print("  engine:", [m.get("name", m) if isinstance(m, dict) else m for m in hd.get("engine", [])][:8])
    for cid, c in h.checks().items():
        st = "info" if c.get("info") else ("ok" if c.get("ok") else ("FAIL" if c.get("ok") is False else
              ("ok(rel)" if c.get("rel") is not None and abs(c["rel"]) <= c["tol"] else "FAIL(rel)" if c.get("rel") is not None else "-")))
        v, r = c["value"], c["ref"]
        print(f"  [{st:8s}] {cid:12s} value={v!r:>24} ref={r!r:>22} tol={c['tol']:.3g}  | {c['label'][:70]}")
    am = h.of("am")
    if am:
        print("  am:", json.dumps({k: (round(v, 10) if isinstance(v, float) else v) for k, v in am[0].items()
                                   if k not in ("type",)}, ensure_ascii=False))
    if h.sim.beam is not None:
        bm = h.sim.beam
        print(f"  table: r {len(bm.r)} pts to {bm.r[-1]:.3g}, z {len(bm.z)} pts {bm.z0:.3g}..{bm.z1:.3g}; half {bm.half:.3g},"
              f" am_half {bm.am_half:.3g}, edge {bm.edge:.3g}, table_err {h.sim.table_err:.3g}")
    beats = h.of("beat")
    if beats:
        b = beats[-1]
        print(f"  last beat: f_meas {b['f_meas']:.7g} (ref {b['f_ref']}), shift {b['shift_meas']:.7g} (ref {b['shift_ref']}),"
              f" depth {b['depth']:.3g}")
    return h


if __name__ == "__main__":
    names = sys.argv[1:] or list(SCHEMA.presets)
    for nm in names:
        if "=" in nm:  # preset:key=value,key=value
            pr, kv = nm.split(":", 1)
            params = {}
            for it in kv.split(","):
                k, v = it.split("=")
                try:
                    params[k] = int(v)
                except ValueError:
                    try:
                        params[k] = float(v)
                    except ValueError:
                        params[k] = v
            show(pr, params, 0.9)
        else:
            show(nm, {}, 0.9)
