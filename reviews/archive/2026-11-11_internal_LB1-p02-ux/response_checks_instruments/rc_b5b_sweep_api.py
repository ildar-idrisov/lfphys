# [response] rc_b5b = the reviewer's b5 against the processor's server, object sweeps also RUN (X1).
# Review LB1-p02-ux, b5: the sweep through its HTTP API on the PRIVATE server (port 8603, never 8479): an object
# parameter in p03 and p04 (the panel offers them), a law in p04 (estimate, then a real run). Host Python, stdlib only,
# talks to the server over HTTP. Output: b5_sweep_api.out.
import json, time, urllib.request
B = "http://127.0.0.1:8611"  # [response] the processor's private server lf-lpi-srv
def post(u, b):
    r = urllib.request.Request(B + u, data=json.dumps(b).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        return json.loads(urllib.request.urlopen(r).read())
    except urllib.error.HTTPError as e:
        return {"http": e.code, **json.loads(e.read() or b"{}")}
def get(u):
    return json.loads(urllib.request.urlopen(B + u).read())
def run(viz, preset, secs=4):
    rid = post("/api/runs", {"viz": viz, "preset": preset, "seed": 3})["id"]
    for _ in range(200):
        if get(f"/api/runs/{rid}")["state"] == "running": break
        time.sleep(0.3)
    post(f"/api/runs/{rid}/command", {"cmd": "play"}); time.sleep(secs); post(f"/api/runs/{rid}/command", {"cmd": "pause"}); time.sleep(2)
    return rid
for viz, preset, target, values, dur, meas in (
        ("p03_molecules", "maxwell", {"kind": "object", "obj": "o1", "param": "T"}, [100, 200], 1e-12, None),
        ("p04_fluids", "cylinder_re20", {"kind": "object", "obj": "o3", "param": "radius"}, [0.04, 0.05], 0.5, None),
        ("p04_fluids", "cylinder_re20", {"kind": "law", "id": "nu"}, [0.001, 0.002], 0.5, None)):
    rid = run(viz, preset)
    est = post(f"/api/runs/{rid}/sweep", {"target": target, "values": values, "duration": dur, "measure": meas or "x", "estimate": True})
    if "нет измеряемой величины" in str(est):
        m = str(est).split("есть: ")[1].split(",")[0].strip(") '\"}")
        est = post(f"/api/runs/{rid}/sweep", {"target": target, "values": values, "duration": dur, "measure": m, "estimate": True})
    else:
        m = meas or "x"
    print(viz, preset, json.dumps(target, ensure_ascii=False), "measure", m, "->", json.dumps(est, ensure_ascii=False)[:500])
    if est.get("estimate"):  # [response] the object parameters run too
        s = post(f"/api/runs/{rid}/sweep", {"target": target, "values": values, "duration": dur, "measure": m})
        for _ in range(240):
            r = get(f"/api/runs/{rid}/sweeps/{s['n']}")
            if r["state"] in ("done", "failed", "cancelled"): break
            time.sleep(1)
        print("   run:", r["state"], [(x["value"], x.get("measured"), x.get("error")) for x in r.get("results", [])])
