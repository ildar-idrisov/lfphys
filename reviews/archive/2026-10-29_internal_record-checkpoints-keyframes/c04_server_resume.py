# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review 2026-10-29 (record checkpoints, key frames), check c04: the server's path, on a PRIVATE server.
# For worlds whose random draws depend on how time is split into frames (v02, v05, v07) and v04: record, change the set-up
# live, step twice (the second step and the suspension sent back to back: a checkpoint in the middle of a batch), suspend
# (POST /stop: the worker writes a checkpoint), resume with ⏺ (from the checkpoint), record, suspend again. Then, off
# line, from the run's folder: (A) the world rebuilt by replaying the whole record (Runner.restore, the fallback) and
# (B) the world loaded from the last checkpoint plus the record after it (Runner.restore_from), both advanced in the same
# frame steps: if the record holds what the checkpointed world went through, A and B emit the same bytes.
#
#   docker run --rm --name lf-rev-c04 --network host -v <engine>:/lf:ro -v <private runs dir>:/runs:ro \
#     -v <this folder>/out:/out -e LFPHYS_NO_GPU=1 -w /lf/visualizations light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-29_internal_record-checkpoints-keyframes/c04_server_resume.py 8511
import json
import queue
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from lfviz import checkpoint, protocol, registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402

PORT = sys.argv[1] if len(sys.argv) > 1 else "8511"
BASE = f"http://127.0.0.1:{PORT}"
WALL = ("cpu_ms", "speed_actual", "lag")
SET = {"v02_double_slit": {"lam_nm": 500.0}, "v05_optics_bench": {"theta_deg": 30.0},
       "v07_bell_test": {"b_deg": 30.0}, "v04_orbits": {"speed": 1.0}}


def call(path, body=None, method=None):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def cmd(rid, c, args=None):
    return call(f"/api/runs/{rid}/command", {"cmd": c, "args": args or {}})


def wait(rid, pred, timeout=120):
    t0 = time.time()
    while True:
        m = call(f"/api/runs/{rid}")
        if pred(m):
            return m
        if time.time() - t0 > timeout:
            raise TimeoutError(json.dumps(m)[:300])
        time.sleep(0.3)


def messages(path):
    data = Path(path).read_bytes()
    return [protocol.decode(m) for _, m in protocol.iter_stream(data, len(protocol.MAGIC))]


def run_offline(viz_id, folder, steps):
    msgs = messages(folder / "stream.lfrec")
    heads = [i for i, (m, _) in enumerate(msgs) if m["type"] == "header"]
    h = heads[-1]
    header = msgs[h][0]
    script, ck, ck_at, t_end = [], None, 0, float(header["t"])
    for m, _ in msgs[h + 1:]:
        if isinstance(m.get("t"), (int, float)):
            t_end = max(t_end, float(m["t"]))
        if m["type"] == "frame":
            script.append({"frame": m["t"]})
        elif m["type"] == "command":
            script.append({"t": m["t"], "cmd": m["cmd"], "args": m.get("args") or {}})
        elif m["type"] == "checkpoint" and m.get("file") and (folder / "checkpoints" / m["file"]).is_file():
            ck, ck_at = m, len(script)
    viz = registry.load(viz_id)
    params, _ = viz["schema"].resolve(None, header["params"])
    outs = {}
    for how in ("replay", "checkpoint"):
        got, muted = [], [False]

        def emit(meta, blobs=None):
            if not muted[0]:
                got.append(protocol.encode({k: v for k, v in meta.items() if k not in WALL}, blobs))
        mute = lambda on: muted.__setitem__(0, on)  # noqa: E731
        if how == "replay":
            sim = viz["simulation"](params, header["seed"], emit)
            run = Runner(sim, emit, queue.Queue())
            run.restore(header.get("world", 1), script, t_end, mute, header.get("adopted_view"))
        else:
            state = checkpoint.loads((folder / "checkpoints" / ck["file"]).read_bytes(), emit)
            run = Runner(state["sim"], emit, queue.Queue())
            run.restore_from(state, script[ck_at:], t_end, mute)
        t0 = run.sim.t
        for k, dt in enumerate(steps):
            run._advance(run.sim.t + dt * run.sim.default_speed)
            run._frame(0.0)
        outs[how] = (got, t0)
    a, b = outs["replay"][0], outs["checkpoint"][0]
    bad = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    first = None
    if bad:
        ma, mb = protocol.decode(a[bad[0]])[0], protocol.decode(b[bad[0]])[0]
        first = {"type": ma.get("type"), "keys": sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k))[:6]}
    return {"t_end": t_end, "checkpoint_t": ck and ck["t"], "checkpoint_reason": ck and ck["reason"],
            "tail_len": len(script) - ck_at, "t_after_restore": [outs["replay"][1], outs["checkpoint"][1]],
            "n": [len(a), len(b)], "n_diff": len(bad), "first_diff": first}


res = {}
for viz_id in SET:
    rid = call("/api/runs", {"viz": viz_id, "seed": 3})["id"]
    wait(rid, lambda m: m["state"] == "running")
    cmd(rid, "play")
    time.sleep(5)
    cmd(rid, "set", {"values": SET[viz_id]})
    time.sleep(4)
    cmd(rid, "pause")
    time.sleep(0.5)
    cmd(rid, "step")
    time.sleep(0.5)
    th = threading.Thread(target=lambda: cmd(rid, "step"))
    th.start()
    call(f"/api/runs/{rid}/stop", {})  # back to back with the step
    th.join()
    m1 = call(f"/api/runs/{rid}")
    cmd(rid, "play")  # resumes from the checkpoint
    wait(rid, lambda m: m["state"] == "running" and m.get("playing"))
    time.sleep(4)
    call(f"/api/runs/{rid}/stop", {})
    m2 = call(f"/api/runs/{rid}")
    folder = Path("/runs") / rid
    texts = [m.get("text", "") for m, _ in messages(folder / "stream.lfrec") if m["type"] == "notice"]
    cks = [(m["reason"], m.get("file"), m.get("error"), round(m.get("ms", 0), 1), m.get("bytes"))
           for m, _ in messages(folder / "stream.lfrec") if m["type"] == "checkpoint"]
    r = {"run": rid, "states": [m1["state"], m2["state"]], "resumes": m2.get("resumes"), "checkpoints": cks,
         "notices": [x[:110] for x in texts]}
    r["offline"] = run_offline(viz_id, folder, [0.07, 0.11, 0.05, 0.13, 0.09, 0.12, 0.06, 0.1])
    res[viz_id] = r
    print(viz_id, json.dumps(r, ensure_ascii=False, default=str), flush=True)

with open("/out/c04_server_resume.json", "w") as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
