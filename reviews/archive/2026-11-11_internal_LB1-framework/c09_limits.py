"""c09: the memory limits and OOM priority of the sweep process and of the workers (private server lf-lbrf-srv2,
container limit 6 GB, 3 workers). Starts one long sweep, then the caller lists /proc/<pid>/limits and oom_score_adj of
every process in the container (see c09_limits.out), then cancels it."""
import os, sys, json
os.environ["LBRF_BASE"] = "http://127.0.0.1:8602"
sys.path.insert(0, "/out")
from lbrf_client import post, start
rid = start("p97_osc", "one", seed=1)
st, js = post(f"/api/runs/{rid}/sweep", {"target": {"kind": "law", "id": "k"}, "values": [4.0], "duration": 1e6,
                                        "measure": "o1.x", "stat": "final"})
print(st, rid, js.get("n"))
open("/out/c09_run", "w").write(f"{rid} {js.get('n')}")
