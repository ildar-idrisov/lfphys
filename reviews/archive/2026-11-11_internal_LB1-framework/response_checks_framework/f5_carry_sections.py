"""Response to review LB1-framework, F5 (framework part): what the carry-over notice says in real sections.

The reviewer's c07 / c07b / c07c showed p03 (atoms regenerated) and p04 (flow restarted from rest) carried with the
notice «все объекты (1)». After the fix the framework classifies every carried object (with its state / by its
parameters / state not carried, rebuilt from its parameters / refused), lists the values the new world changed and says
what happened to the world's own state; the section's hooks (``carry_state``, ``carry_world``, ``carry_note``) decide
what can be carried. This script prints the notice and its ``carry`` data for:
  (a) p03, preset «molecules», 0.2 ps, then a world of another space (the reviewer's c07 (a));
  (b) p04, preset «cylinder_re20», 1 s, then another fluid (the reviewer's c07c);
  (c), (d) the same two with the same laws (a new world that can take everything: the «с состоянием» path).
Against a PRIVATE server (never the shared one on 8479):
  docker run --rm --network host --name lf-lpf-f5 -v <this folder>:/out:ro light-funnel-viz \
      python3 /out/f5_carry_sections.py http://127.0.0.1:8612
"""
import json
import struct
import sys
import time
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8612"


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=300) as f:
        return f.read()


def post(path, body=None):
    return json.loads(req("POST", path, body or {}))


def record(rid):
    buf = req("GET", f"/api/runs/{rid}/stream")
    out, off = [], 8
    while off + 4 <= len(buf):
        n = struct.unpack_from("<I", buf, off)[0]
        jl = struct.unpack_from("<I", buf, off + 4)[0]
        out.append(json.loads(buf[off + 8: off + 8 + jl]))
        off += 4 + n
    return out


def wait(fn, s=180):
    t0 = time.time()
    while time.time() - t0 < s:
        v = fn()
        if v:
            return v
        time.sleep(0.5)
    return None


def run(viz, preset, dt, change):
    rid = post("/api/runs", {"viz": viz, "preset": preset, "seed": 3})["id"]
    wait(lambda: json.loads(req("GET", f"/api/runs/{rid}"))["state"] == "running")
    wait(lambda: any(m["type"] == "header" for m in record(rid)))
    post(f"/api/runs/{rid}/command", {"cmd": "step", "args": {"dt": dt}})
    wait(lambda: sum(1 for m in record(rid) if m["type"] == "frame") >= 2, 300)
    h1 = [m for m in record(rid) if m["type"] == "header"][0]
    params = {**{k: v for k, v in h1["params"].items() if k != "scene"}, **change}
    post(f"/api/runs/{rid}/command", {"cmd": "new_world", "args": {"params": params, "carry": True}})
    rec = wait(lambda: (lambda r: r if sum(1 for m in r if m["type"] in ("header",)) >= 2
                        or any(m["type"] == "error" and "Новый мир" in m.get("text", "") for m in r) else None)(record(rid)), 300)
    heads = [i for i, m in enumerate(rec) if m["type"] == "header"]
    after = rec[heads[-1]:] if len(heads) > 1 else []
    notes = [m for m in after if m["type"] == "notice" and "carry" in m]
    errs = [m["text"] for m in rec if m["type"] == "error"][-2:]
    print(f"== {viz} {preset}: worlds {len(heads)}, change {change}")
    if notes:
        n = notes[-1]
        print("notice:", n["text"])
        print("carry:", json.dumps({"objects": [{k: o[k] for k in ("id", "was", "label", "how", "notes")} for o in n["carry"]["objects"]],
                                    "world": n["carry"]["world"]}, ensure_ascii=False))
        ref = (rec[heads[-1]]["params"]["scene"] or {}).get("carry_file")
        print("carried state file:", ref)
    else:
        print("no carry notice; errors:", errs)
    post(f"/api/runs/{rid}/stop", {})
    return rid


run("p03_molecules", "molecules", 2e-13, {"dim": "2d"})
run("p04_fluids", "cylinder_re20", 1.0, {"fluid": "water"})
run("p03_molecules", "molecules", 2e-13, {})
run("p04_fluids", "cylinder_re20", 1.0, {})
