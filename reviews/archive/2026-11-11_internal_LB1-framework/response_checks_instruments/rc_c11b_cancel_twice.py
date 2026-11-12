"""rc_c11b (response to F10): «✕ отменить» twice through the new route POST /sweeps/{n}/cancel (idempotent), the
second 0.3 s after the first (a double click, two tabs): the values the first one kept stay; DELETE removes only a
sweep that is not running."""
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
st, js = post(f"/api/runs/{rid}/sweep", body)
n = js["n"]
for _ in range(200):
    s = get(f"/api/runs/{rid}/sweeps/{n}")[1]
    if s["progress"].get("done", 0) >= 2:
        break
    time.sleep(0.2)
print("before the cancel: done", s["progress"]["done"], "of", s["progress"]["total"], "state", s["state"])
print("DELETE while running:", req("DELETE", f"/api/runs/{rid}/sweeps/{n}"))
out = []
t1 = threading.Thread(target=lambda: out.append(("first", post(f"/api/runs/{rid}/sweeps/{n}/cancel"))))
t1.start()
time.sleep(0.3)
out.append(("second", post(f"/api/runs/{rid}/sweeps/{n}/cancel")))
t1.join()
for name, (st, j) in sorted(out):
    print(f"{name} cancel: HTTP {st} {j}")
st, s = get(f"/api/runs/{rid}/sweeps/{n}")
print("the sweep afterwards: HTTP", st, s.get("state"), "results kept:", len(s.get("results") or []), "|", s.get("message"))
st2, d = req("DELETE", f"/api/runs/{rid}/sweeps/{n}")
print("DELETE after: HTTP", st2, d, "| then GET:", get(f"/api/runs/{rid}/sweeps/{n}")[0])
json.dump({"run": rid, "n": n, "cancels": out, "after": {"state": s.get("state"), "results": len(s.get("results") or [])},
           "delete_after": [st2, d]}, open("/out/rc_c11b_cancel_twice.json", "w"), indent=1, ensure_ascii=False)
