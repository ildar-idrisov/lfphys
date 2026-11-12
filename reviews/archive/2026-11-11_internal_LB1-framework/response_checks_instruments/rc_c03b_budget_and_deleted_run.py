"""rc_c03b = the reviewer's c03, run against the processor's budget-20 s server (port 8619); unchanged otherwise.
c03: is the sweep budget enforced, and what happens to a sweep whose run is deleted?

Against a second private server (lf-lbrf-srv2, port 8602) started like the first but with LFVIZ_SWEEP_BUDGET_S=20,
so that the self-stop (1.5 x budget = 30 s) is quick to observe.

(a) A run of p97_osc that has not computed (no frames with a time step: the estimate is «unknown»), a sweep with stat
    "final" and a long duration: one reading, i.e. one call of Runner._advance for the whole duration. The budget check
    sits between readings. Expected by the docs: «свип начнётся и остановится сам, если первое значение покажет, что он
    дороже предела». Observed: state and the process after 45 s.
(b) The run is deleted while its sweep runs: is the process ended, can the sweep still be cancelled, does it still hold
    one of the server's two sweep places?
The processes are listed by the caller with `docker exec lf-lbrf-srv2 ps` (see c03 .out).
"""
import json
import os
import sys
import time

os.environ["LBRF_BASE"] = "http://127.0.0.1:8619"  # [response] lf-lpi-srv2: LFVIZ_SWEEP_BUDGET_S=20
sys.path.insert(0, "/out")
from lbrf_client import get, post, req, start  # noqa: E402

res = {}
rid = start("p97_osc", "one", seed=1)
body = {"target": {"kind": "law", "id": "k"}, "values": [4.0, 9.0], "duration": 1e7, "measure": "o1.x", "stat": "final"}
st, est = post(f"/api/runs/{rid}/sweep", {**body, "estimate": True})
print("estimate:", st, est.get("estimate", {}).get("known"), "|", est.get("estimate", {}).get("text"))
st, js = post(f"/api/runs/{rid}/sweep", body)
print("start:", st, js.get("n"), js.get("state"))
n = js["n"]
t_start = time.monotonic()
time.sleep(45)
st, s = get(f"/api/runs/{rid}/sweeps/{n}")
print(f"after {time.monotonic() - t_start:.0f} s (budget 20 s, self-stop at 30 s): state={s['state']} active={s['active']} "
      f"progress={s['progress']}")
print("   [response] its message:", s.get("message"), "| ended", s.get("ended"), "created", s.get("created"))
res["a"] = {"estimate_known": est.get("estimate", {}).get("known"), "after_s": 45, "state": s["state"],
            "active": s["active"], "progress": s["progress"]}
pass
# (b) delete the run while its sweep runs. [response] (a)'s sweep now stops by itself within seconds, so (b) needs a
# sweep that is still running: a second run, a sweep within the budget (2 values of ~8 s), deleted after 3 s
req("DELETE", f"/api/runs/{rid}")
rid = start("p97_osc", "one", seed=4)
st, js = post(f"/api/runs/{rid}/sweep", {**body, "duration": 2.5e4})
n = js["n"]
time.sleep(3)
print("[response] (b) the sweep before the delete:", get(f"/api/runs/{rid}/sweeps/{n}")[1]["state"])
t_del = time.monotonic()
st, d = req("DELETE", f"/api/runs/{rid}")
print("DELETE run:", st, d)
time.sleep(3)
st, c = post(f"/api/runs/{rid}/sweeps/{n}/cancel")  # [response] the new cancel route
print("cancel the deleted run's sweep:", st, c)
st, h = get("/api/health")
print("health: running workers", h.get("running"), "runs", h.get("runs"))
# two other runs: one sweep each; the second must find a free place if the deleted run's sweep had ended
r2 = start("p97_osc", "one", seed=2)
r3 = start("p97_osc", "one", seed=3)
st2, j2 = post(f"/api/runs/{r2}/sweep", body)
st3, j3 = post(f"/api/runs/{r3}/sweep", body)
print("another run's sweep:", st2, j2.get("n") or j2)
print("a third run's sweep:", st3, j3)
res["b"] = {"delete_run": st, "cancel_after_delete": c, "second": st2, "third": [st3, j3]}
json.dump(res, open("/out/rc_c03b_budget_and_deleted_run.json", "w"), indent=1, ensure_ascii=False)
for r in (r2,):
    if st2 == 200:
        post(f"/api/runs/{r}/sweeps/{j2['n']}/cancel")  # [response] the new cancel route
