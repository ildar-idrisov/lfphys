# Review LB1-p02-ux, b7: p04's largest speed u_max changed live through the command API (PRIVATE server 8603). Host
# Python, stdlib only. Output: b7_p04_umax_api.out.
import json, time, struct, urllib.request
B = "http://127.0.0.1:8603"
def post(u, b):
    r = urllib.request.Request(B + u, data=json.dumps(b).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(r).read())
def get(u): return json.loads(urllib.request.urlopen(B + u).read())
def record(rid):
    buf = urllib.request.urlopen(f"{B}/api/runs/{rid}/stream").read(); off = 8; out = []
    while off + 4 <= len(buf):
        n = struct.unpack_from("<I", buf, off)[0]; m = off + 4; jl = struct.unpack_from("<I", buf, m)[0]
        out.append(json.loads(buf[m+4:m+4+jl])); off = m + n
    return out
rid = post("/api/runs", {"viz": "p04_fluids", "preset": "cylinder_re20", "seed": 3})["id"]
for _ in range(200):
    if get(f"/api/runs/{rid}")["state"] == "running": break
    time.sleep(0.3)
post(f"/api/runs/{rid}/command", {"cmd": "play"}); time.sleep(4); post(f"/api/runs/{rid}/command", {"cmd": "pause"}); time.sleep(2)
for v in (0.6, 0.15):
    n0 = len(record(rid)); t0 = time.time()
    post(f"/api/runs/{rid}/command", {"cmd": "set", "args": {"values": {"u_max": v}}})
    for _ in range(300):
        rec = record(rid)[n0:]
        if any(m.get("type") in ("event", "error") for m in rec): break
        time.sleep(0.3)
    print(f"u_max -> {v}: {time.time() - t0:.1f} s;", [m.get("text") for m in rec if m.get("type") in ("event", "error", "notice")])
