"""c11: «✕ отменить» twice. The same request (DELETE /api/runs/{id}/sweeps/{n}) cancels a running sweep (its computed
values kept) and removes a finished one with its results. A second click on «✕ отменить» (the button stays until the
next poll, 700 ms), or two tabs cancelling, sends a second DELETE: are the values the first one kept removed?

A sweep of 6 values, each ~1 s, cancelled after ~2.5 s with two DELETEs 0.3 s apart."""
import json
import sys
import threading
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, get, post, req, start  # noqa: E402

rid = start("p97_osc", "two", seed=5)
cmd(rid, "play")
time.sleep(3)
cmd(rid, "pause")
time.sleep(1)
body = {"target": {"kind": "law", "id": "k"}, "values": [1, 2, 3, 4, 5, 6], "duration": 3000.0, "measure": "E",
        "stat": "final"}
st, est = post(f"/api/runs/{rid}/sweep", {**body, "estimate": True})
print("estimate:", st, (est.get("estimate") or {}).get("text") or est)
st, js = post(f"/api/runs/{rid}/sweep", body)
n = js["n"]
for _ in range(100):
    s = get(f"/api/runs/{rid}/sweeps/{n}")[1]
    if s["progress"].get("done", 0) >= 2:
        break
    time.sleep(0.2)
print("before the cancel: done", s["progress"]["done"], "of", s["progress"]["total"], "state", s["state"])
out = []
t1 = threading.Thread(target=lambda: out.append(("first", req("DELETE", f"/api/runs/{rid}/sweeps/{n}"))))
t1.start()
time.sleep(0.3)
out.append(("second", req("DELETE", f"/api/runs/{rid}/sweeps/{n}")))
t1.join()
for name, (st, j) in sorted(out):
    print(f"{name} DELETE: HTTP {st} {j}")
st, s = get(f"/api/runs/{rid}/sweeps/{n}")
print("the sweep afterwards: HTTP", st, (s.get("state"), len(s.get("results") or [])) if st == 200 else s)
json.dump({"run": rid, "n": n, "deletes": out, "after": [st, s if st != 200 else {"state": s["state"], "results": len(s["results"])}]},
          open("/out/c11_cancel_twice.json", "w"), indent=1, ensure_ascii=False)
