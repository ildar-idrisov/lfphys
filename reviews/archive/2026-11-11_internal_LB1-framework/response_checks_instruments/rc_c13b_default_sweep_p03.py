"""rc_c13b = the reviewer's c13, run against the processor's budget-20 s server (port 8619); the cancel uses the new route.
c13: the sweep form's defaults on a real section that has not computed yet (p03_molecules, preset maxwell, world
time in seconds, dt = 10 fs). The panel's defaults: «Сколько считать» = 1 (in the world's time unit, «с» for p03:
its header has no units.t), «Что взять» = the first stat (final). Against lf-lbrf-srv2 (budget 20 s, self-stop at 30 s).
What the estimate says, whether the sweep starts, and whether it has stopped after 60 s; then it is cancelled."""
import os
import sys
import time

os.environ["LBRF_BASE"] = "http://127.0.0.1:8619"  # [response] lf-lpi-srv2: LFVIZ_SWEEP_BUDGET_S=20
sys.path.insert(0, "/out")
from lbrf_client import get, post, record, req, start  # noqa: E402

rid = start("p03_molecules", "maxwell", seed=1)
h = [m for m in record(rid) if m["type"] == "header"][0]
print("header units:", h.get("units"))
body = {"target": {"kind": "law", "id": "dt_fs"}, "values": [10.0], "duration": 1, "measure": "T", "stat": "final"}
st, est = post(f"/api/runs/{rid}/sweep", {**body, "estimate": True})
print("estimate:", st, (est.get("estimate") or {}).get("known"), "|", (est.get("estimate") or {}).get("text") or est)
st, js = post(f"/api/runs/{rid}/sweep", body)
print("start:", st, js.get("n"), js.get("state"), js.get("error"))
n = js.get("n")
time.sleep(60)
st, s = get(f"/api/runs/{rid}/sweeps/{n}")
print(f"after 60 s: state {s['state']}, active {s['active']}, progress {s['progress']}")
print("   [response] its message:", s.get("message"), "| created", s.get("created"), "ended", s.get("ended"))
st, c = post(f"/api/runs/{rid}/sweeps/{n}/cancel")
print("cancel:", st, c)
