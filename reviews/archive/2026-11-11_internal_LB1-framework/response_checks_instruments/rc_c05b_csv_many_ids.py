"""rc_c05b (response to F11): a CSV of many DISTINCT quantities while /api/health is asked every 20 ms. The reviewer's c05
asked for 100 copies of one id; those now count once, so its CSV is small (after/c05_series_load.out). Here: p97_osc with
40 oscillators (82 measurables), played until the record holds ~4800 frames (as the reviewer's 4793), then the CSV of
all 82 ids. Before the fix one batch of 4000 rows was formatted in the event loop (0.36 s stall for 100 columns)."""
import json
import sys
import threading
import time
import urllib.request

sys.path.insert(0, "/out")
from lbrf_client import BASE, cmd, get, start  # noqa: E402

rid = start("p97_osc", "one", seed=7)
for i in range(39):
    cmd(rid, "scene", {"op": "add", "type": "osc", "values": {"x": 0.02 * i, "v": 0.1}})
time.sleep(1.0)
cmd(rid, "play")
t0 = time.monotonic()
while True:
    time.sleep(10)
    n = get(f"/api/runs/{rid}/series?ids=E&max_points=2")[1]["n_frames"]
    if n >= 4800 or time.monotonic() - t0 > 400:
        break
cmd(rid, "pause")
time.sleep(1.0)
st, js = get(f"/api/runs/{rid}/series?ids=E&max_points=2")
ids = [d for d in json.loads(urllib.request.urlopen(BASE + f"/api/runs/{rid}/series?ids=E").read())["measurables"]]
sc = get(f"/api/runs/{rid}/series?ids=E")[1]
allids = None
# every declared id: ask for an unknown one, the refusal lists them
try:
    urllib.request.urlopen(BASE + f"/api/runs/{rid}/series?ids=__none__")
except urllib.error.HTTPError as e:
    allids = json.loads(e.read())["error"].split("есть: ")[1].rstrip(")").split(", ")
lat, stop = [], [False]


def poll():
    while not stop[0]:
        a = time.monotonic()
        urllib.request.urlopen(BASE + "/api/health").read()
        lat.append(time.monotonic() - a)
        time.sleep(0.02)


base = []
for _ in range(20):
    a = time.monotonic(); urllib.request.urlopen(BASE + "/api/health").read(); base.append(time.monotonic() - a)
th = threading.Thread(target=poll)
th.start()
a = time.monotonic()
body = urllib.request.urlopen(BASE + f"/api/runs/{rid}/series?ids={','.join(allids)}&format=csv").read()
dt = time.monotonic() - a
time.sleep(0.3)
stop[0] = True
th.join()
out = {"run": rid, "frames": js["n_frames"], "ids": len(allids), "csv_bytes": len(body), "csv_seconds": round(dt, 3),
       "health_latency_before_s": round(max(base), 4), "health_max_latency_during_s": round(max(lat), 4),
       "health_polls_during": len(lat)}
print(json.dumps(out, indent=1))
json.dump(out, open("/out/rc_c05b_csv_many_ids.json", "w"), indent=1)
