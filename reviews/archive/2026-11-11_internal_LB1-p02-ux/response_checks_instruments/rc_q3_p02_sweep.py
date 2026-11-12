# [response] rc_q3: a sweep of p02 (double slit) through the API on the processor's PRIVATE server (port 8611): the law
# «size» (the window) 76 / 80 / 84 nm, a world-wide quantity at the end. LB1-p02-ux Q3: p02's measure() returned a
# tuple and every value failed with «AttributeError». The sweep's side now checks the contract: a world that breaks it
# is named as such and the sweep stops; once p02 returns the dict (the p02 processor's part) the values are measured.
# Host Python, stdlib only. Output: rc_q3_p02_sweep.out.
import json, time, urllib.request, urllib.error
B = "http://127.0.0.1:8611"
def post(u, b=None):
    r = urllib.request.Request(B + u, data=json.dumps(b or {}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        return json.loads(urllib.request.urlopen(r).read())
    except urllib.error.HTTPError as e:
        return {"http": e.code, **json.loads(e.read() or b"{}")}
def get(u):
    return json.loads(urllib.request.urlopen(B + u).read())
rid = post("/api/runs", {"viz": "p02_quantum", "preset": "double_slit", "seed": 3})["id"]
for _ in range(300):
    if get(f"/api/runs/{rid}")["state"] == "running": break
    time.sleep(0.3)
post(f"/api/runs/{rid}/command", {"cmd": "play"}); time.sleep(6); post(f"/api/runs/{rid}/command", {"cmd": "pause"}); time.sleep(2)
ser = post(f"/api/runs/{rid}/sweep", {"target": {"kind": "law", "id": "size"}, "values": [76, 80, 84], "duration": 1e-15,
                                      "measure": "__list__", "estimate": True})
print("measurables (from the refusal):", str(ser.get("error"))[:300])
have = str(ser.get("error", "")).split("есть: ")[1].rstrip(")").split(", ") if "есть: " in str(ser.get("error", "")) else []
mid = next((m for m in have if "." not in m), have[0] if have else None)
body = {"target": {"kind": "law", "id": "size"}, "values": [76, 80, 84], "duration": 5e-15, "measure": mid, "stat": "final"}
est = post(f"/api/runs/{rid}/sweep", {**body, "estimate": True})
print("measure", mid, "| estimate:", json.dumps(est.get("estimate", est), ensure_ascii=False)[:400])
st = post(f"/api/runs/{rid}/sweep", body)
print("start:", {k: st.get(k) for k in ("n", "state", "error", "hint")})
if "n" in st:
    for _ in range(600):
        r = get(f"/api/runs/{rid}/sweeps/{st['n']}")
        if r["state"] not in ("starting", "running") and not r["active"]: break
        time.sleep(0.5)
    print("state:", r["state"], "| message:", r.get("message"))
    print("results:", [(x["value"], x.get("measured"), (x.get("error") or "")[:120]) for x in r.get("results", [])])
    print("sampler:", r.get("sampler"))
