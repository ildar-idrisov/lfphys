"""P30's extreme single edits that took > 2 min (killed): plane axis in double_slit, marker edge 1e6 in which_path,
detector y = +-1e6 in aharonov_bohm; and U8's far objects. Wall time and the outcome."""
import sys, time, json
root = sys.argv[1]
sys.path[:0] = [f"{root}/visualizations", f"{root}/visualizations/server", f"{root}/lfphys", root]
from tests.harness import Harness
def oid(h, typ): return next(k for k, o in h.sim.objects.items() if o["type"] == typ)
for preset, typ, vals in [("double_slit", "plane", {"axis": "1"}), ("which_path", "marker", {"edge": 1e6}),
                          ("aharonov_bohm", "detector", {"y": 1e6}), ("aharonov_bohm", "detector", {"y": -1e6}),
                          ("double_slit", "slit_wall", {"offset": 1e6})]:
    h = Harness("p02_quantum", preset)
    n0 = len(h.msgs); t0 = time.time()
    h.cmd("scene", op="set", id=oid(h, typ), values=vals)
    errs = [m["text"][:160] for m, _ in h.msgs[n0:] if m.get("type") == "error"]
    print(json.dumps({"preset": preset, "edit": f"{typ} {vals}", "s": round(time.time() - t0, 3), "errors": errs}, ensure_ascii=False), flush=True)
