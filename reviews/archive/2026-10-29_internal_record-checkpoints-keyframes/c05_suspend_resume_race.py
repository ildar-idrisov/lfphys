# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review 2026-10-29 (record checkpoints, key frames), check c05: ⏺ pressed while the run is being suspended.
# Run._stop holds the run's lock until the worker PROCESS has exited (proc.wait()); the worker's last messages — the
# suspension's checkpoint and "end" — may still be unread by the run's reader task (read_worker). A resume waiting on
# the lock then reads the record (Run._latest_world) without that checkpoint and opens a new record file handle that the
# old reader, when it finishes, closes (self.file.close()) and whose state it overwrites. This repeats [suspend, ⏺] sent
# together and checks after each round: did the resume use the checkpoint the suspension wrote, is the checkpoint
# message before the resume's notice in the record, is the run recording afterwards.
#
#   docker run --rm --name lf-rev-c05 --network host -v <engine>:/lf:ro -v <private runs dir>:/runs:ro \
#     -v <this folder>/out:/out -w /lf/visualizations light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-29_internal_record-checkpoints-keyframes/c05_suspend_resume_race.py 8511 v07_bell_test 20
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path[:0] = ["/lf/visualizations/server"]
from lfviz import protocol  # noqa: E402

PORT, VIZ, ROUNDS = sys.argv[1], sys.argv[2], int(sys.argv[3])
BASE = f"http://127.0.0.1:{PORT}"


def call(path, body=None):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"http": e.code, "body": e.read().decode()[:200]}


def records(rid):
    data = (Path("/runs") / rid / "stream.lfrec").read_bytes()
    return [protocol.peek_meta(m) for _, m in protocol.iter_stream(data, len(protocol.MAGIC))]


rid = call("/api/runs", {"viz": VIZ, "seed": 3})["id"]
time.sleep(2)
call(f"/api/runs/{rid}/command", {"cmd": "play"})
time.sleep(2)
out = []
DELAYS = [0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.2]  # ⏺ this long after the suspension began
for k in range(ROUNDS):
    res = {}
    n0 = len(records(rid))
    n_res0 = len(call(f"/api/runs/{rid}").get("resumes") or [])
    d = DELAYS[k % len(DELAYS)]
    t1 = threading.Thread(target=lambda: res.__setitem__("stop", call(f"/api/runs/{rid}/stop", {})))
    t1.start()
    time.sleep(d)
    res["play"] = call(f"/api/runs/{rid}/command", {"cmd": "play"})
    t1.join()
    time.sleep(2.0)
    m = call(f"/api/runs/{rid}")
    recs = records(rid)[n0:]  # what this round added to the record
    i_ck = next((i for i, r in enumerate(recs) if r["type"] == "checkpoint" and r.get("reason") == "suspend"), -1)
    i_res = next((i for i, r in enumerate(recs) if r["type"] == "notice" and "Продолжение" in r.get("text", "")), -1)
    i_end = next((i for i, r in enumerate(recs) if r["type"] == "end"), -1)
    resumed = len(m.get("resumes") or []) > n_res0
    row = {"round": k, "delay_s": d, "resumed": resumed, "state": m.get("state"), "playing": m.get("playing"),
           "resumed_from": (m.get("resumes") or [{}])[-1].get("from") if resumed else None,
           "order": [r["type"] + (":" + r.get("reason", "") if r["type"] == "checkpoint" else "")
                     + (":resume" if r["type"] == "notice" and "Продолжение" in r.get("text", "") else "")
                     for r in recs if r["type"] in ("checkpoint", "notice", "end", "header")],
           "checkpoint_after_resume_notice": resumed and i_ck > i_res >= 0,
           "end_after_resume_notice": resumed and i_end > i_res >= 0,
           "frames_after_resume": sum(1 for r in recs[i_res + 1:] if r["type"] == "frame") if i_res >= 0 else 0,
           "stop": res.get("stop"), "play": res.get("play")}
    out.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
    if m.get("state") != "running":
        call(f"/api/runs/{rid}/command", {"cmd": "play"})
        time.sleep(2)
lost = [r for r in out if not r["resumed"]]
bad = [r for r in out if r["resumed"] and (r["checkpoint_after_resume_notice"] or r["end_after_resume_notice"]
                                           or r["state"] != "running" or r["resumed_from"] != "checkpoint"
                                           or not r["frames_after_resume"])]
print("rounds", len(out), "play acknowledged but lost (run left suspended)", len(lost), "resumed wrongly", len(bad))
with open("/out/c05_suspend_resume_race.json", "w") as f:
    json.dump({"run": rid, "rounds": out, "lost": len(lost), "resumed_wrongly": len(bad)}, f, ensure_ascii=False, indent=1)
