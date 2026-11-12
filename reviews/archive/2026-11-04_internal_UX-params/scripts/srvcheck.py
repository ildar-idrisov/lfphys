"""Confirm audit findings through the HTTP API of the private server (lf-uxc-srv, port 8563).

    python3 srvcheck.py cases.json out.json

cases: [{"name", "viz", "preset"?, "params"?, "ops": [["play", seconds] | ["set", {...}] | ["action", name, args] |
        ["scene", {...}] | ["view", {...}] | ["new_world", {...}] | ["step"] | ["next_event"] | ["wait", s]]}]
For each case: POST /api/runs (the answer: 400 with the reason, or an id), the commands, then the passport: state,
errors (what the player's toasts and the events panel show), returncode.
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8563"


def req(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    r = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=120) as f:
            return f.status, json.loads(f.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except json.JSONDecodeError:
            return e.code, None


def cmd(rid, c, args=None):
    return req("POST", f"/api/runs/{rid}/command", {"cmd": c, "args": args or {}})


def run_case(case):
    out = {"name": case["name"], "viz": case["viz"]}
    body = {"viz": case["viz"], "seed": 1}
    if case.get("preset"):
        body["preset"] = case["preset"]
    if case.get("params"):
        body["params"] = case["params"]
    st, js = req("POST", "/api/runs", body)
    out["start"] = {"status": st, "body": js}
    if st != 200:
        return out
    rid = js["id"]
    out["id"] = rid
    time.sleep(case.get("build_wait", 3))
    for op in case.get("ops", []):
        k = op[0]
        if k == "play":
            out.setdefault("cmd", []).append(cmd(rid, "play"))
            time.sleep(op[1])
            cmd(rid, "pause")
        elif k == "wait":
            time.sleep(op[1])
        elif k == "set":
            out.setdefault("cmd", []).append(cmd(rid, "set", {"values": op[1]}))
        elif k == "action":
            out.setdefault("cmd", []).append(cmd(rid, "action", {"name": op[1], "args": op[2]}))
        elif k in ("scene", "view", "new_world"):
            out.setdefault("cmd", []).append(cmd(rid, k, op[1]))
        elif k in ("step", "next_event"):
            out.setdefault("cmd", []).append(cmd(rid, k))
        time.sleep(0.5)
    time.sleep(case.get("end_wait", 2))
    st, meta = req("GET", f"/api/runs/{rid}")
    out["state"] = meta.get("state")
    out["errors"] = meta.get("errors")
    out["returncode"] = meta.get("returncode")
    out["sim_t"] = meta.get("sim_t")
    out["stop_reason"] = meta.get("stop_reason")
    out["resume_error"] = meta.get("resume_error")
    return out


def main():
    cases = json.load(open(sys.argv[1]))
    res = []
    for c in cases:
        try:
            r = run_case(c)
        except Exception as e:  # noqa: BLE001
            r = {"name": c["name"], "exc": repr(e)}
        res.append(r)
        json.dump(res, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
        print(json.dumps(r, ensure_ascii=False)[:700], flush=True)
        if r.get("id"):
            req("POST", f"/api/runs/{r['id']}/stop", {})


if __name__ == "__main__":
    main()
