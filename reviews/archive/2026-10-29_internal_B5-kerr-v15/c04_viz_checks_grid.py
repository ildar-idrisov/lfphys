# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review B5, check c04: v15's live checks over a grid of worlds (do they fail correct runs? do they hold what the
# README says?), and the README's measured numbers on the presets.
#
# (a) Every preset at res "s": the checks' values (edge, lyapunov, pixels, schw, eht, eht_kerr) as the player gets
#     them, against the README's "Measured on the presets".
# (b) A grid chi x incl x emitter x retro (res "s", half 9 M): each world built by the harness (as the server does)
#     and scanned to the end; every non-info check with ok == False is listed with its value and tolerance.
#     The engine is the same for all of them, so a failure is a check that fails a correct run (or an engine error
#     that c02/c03 did not see; the listing says which).
#
# Root: engine at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this script in
# /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/. CPU (LFPHYS_NO_GPU=1). Run as c02 (see its header).
import itertools
import math
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

V = "v15_kerr_shadow"


def failed(h):
    return [c for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def world(args):
    preset, params = args
    t0 = time.time()
    try:
        h = Harness(V, preset, params)
        from v15_kerr_shadow.viz import SCAN_M
        h.run_to(SCAN_M * 1.01)
    except Exception as e:  # noqa: BLE001
        return (preset, params, None, f"{type(e).__name__}: {e}", time.time() - t0)
    ch = {k: {kk: v.get(kk) for kk in ("value", "ref", "tol", "ok", "info", "note")} for k, v in h.checks().items()}
    bad = [c["id"] for c in failed(h)]
    return (preset, params, ch, bad, time.time() - t0)


def main():
    out = []
    from v15_kerr_shadow.viz import SCHEMA
    out.append("== (a) presets (res s) ==")
    with Pool(8) as pool:
        res = pool.map(world, [(p, {"res": "s"}) for p in SCHEMA.presets])
    for preset, params, ch, bad, dt in res:
        out.append(f"-- {preset} ({dt:.1f} s): failed {bad}")
        if ch is None:
            continue
        for k, c in ch.items():
            out.append(f"   {k}: value={c['value']!r} ref={c['ref']!r} tol={c['tol']!r} ok={c['ok']} info={c['info']}")
            if k in ("lyapunov", "eht", "eht_kerr"):
                out.append(f"      note: {c['note']}")
    out.append("")
    out.append("== (b) grid (res s, half 9) ==")
    grid = []
    for chi, incl, em, retro in itertools.product((0.0, 0.3, 0.6, 0.9, 0.99, 0.998),
                                                   (1.0, 5.0, 17.0, 45.0, 75.0, 89.0, 90.0, 120.0, 163.0, 179.0),
                                                   ("cunningham", "keplerian"), (False, True)):
        grid.append((None, {"res": "s", "chi": chi, "incl": incl, "emitter": em, "retro": retro}))
    t0 = time.time()
    with Pool(12) as pool:
        res = pool.map(world, grid)
    nfail = 0
    worst_edge = (0.0, None)
    for preset, params, ch, bad, dt in res:
        if ch is None:
            out.append(f"ERROR {params}: {bad}")
            nfail += 1
            continue
        e = ch.get("edge", {}).get("value")
        if e is not None and e > worst_edge[0]:
            worst_edge = (e, params)
        if bad:
            nfail += 1
            det = "; ".join(f"{b}: value={ch[b]['value']!r} ref={ch[b]['ref']!r} tol={ch[b]['tol']!r}" for b in bad)
            out.append(f"FAILED {params}: {det}")
    out.append(f"worlds {len(grid)}; with a failed check or an error: {nfail}; worst edge value {worst_edge[0]:.3e} at "
               f"{worst_edge[1]} (tolerance 64 eps = {64 * 2.220446049250313e-16:.3e}); wall {time.time() - t0:.0f} s")
    print("\n".join(out))


if __name__ == "__main__":
    main()
