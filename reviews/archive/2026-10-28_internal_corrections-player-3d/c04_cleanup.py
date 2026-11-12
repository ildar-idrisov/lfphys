"""C1 review, check 04: removal of old runs (owner, 2026-10-28: «автоудаление старых экспериментов по времени последнего
действия, которые позднее N дней, по дефолту 3 дня») — RunManager.cleanup on fake records in a temporary folder (no
workers are started).

Q1  over the quota: which run goes first — the one created first, or the one whose last action is oldest?
Q2  a run someone is looking at right now (a viewer connected, the run suspended): can it be removed?
Q3  a viewer's visit to a suspended run (touch): does it survive a server restart?
Q4  records made before last_action existed: when are they removed?

Run: docker run --rm --name lf-c1rev-c04 -v <engine>:/lf:ro -v <this folder>:/rev -w /lf/visualizations \
         light-funnel-viz python3 /rev/c04_cleanup.py
Output: /rev/out/c04_cleanup.txt
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from lfviz import protocol  # noqa: E402
from lfviz.runs import RunManager  # noqa: E402

OUT = []


def log(s):
    OUT.append(s)
    print(s)


def fake(d: Path, rid, created, last_action=None, size=1000, state="suspended", restorable=True):
    r = d / rid
    r.mkdir()
    msg = protocol.encode({"type": "notice", "t": 0.0, "text": "fake"}, {"pad": np.zeros(size, np.uint8)})
    (r / "stream.lfrec").write_bytes(protocol.MAGIC + protocol.frame_stream_item(msg))
    m = {"id": rid, "viz": "v01_light_travel", "created": created, "state": state, "keep": False,
         "restorable": restorable}
    if last_action is not None:
        m["last_action"] = last_action
        m["last_action_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(last_action))
    (r / "meta.json").write_text(json.dumps(m))
    return r


now = time.time()
DAY = 86400.0

with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    # Q1: quota 2.5 kB, three runs of 1 kB each: A created first but used a minute ago, B and C created later and not
    # touched for two days
    fake(d, "20261020-000000-v01-aaaa", "2026-10-20T00:00:00", last_action=now - 60)
    fake(d, "20261026-000000-v01-bbbb", "2026-10-26T00:00:00", last_action=now - 2 * DAY)
    fake(d, "20261026-000001-v01-cccc", "2026-10-26T00:00:01", last_action=now - 2 * DAY)
    mgr = RunManager(d, keep_days=3.0, quota_gb=2.5e-6)
    removed = mgr.cleanup()
    log(f"Q1 over the quota: removed {removed} (A was used a minute ago; B and C untouched for 2 days)")

with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    # Q2: a suspended run with a viewer connected, the folder over the quota
    fake(d, "20261027-000000-v01-dddd", "2026-10-27T00:00:00", last_action=now - 10)
    fake(d, "20261028-000000-v01-eeee", "2026-10-28T00:00:00", last_action=now - 10)
    mgr = RunManager(d, keep_days=3.0, quota_gb=1.5e-6)
    r = mgr.get("20261027-000000-v01-dddd")
    r.viewers.add(object())  # a viewer's tab is open on it (the run is suspended: not running)
    removed = mgr.cleanup()
    log(f"Q2 a viewer is looking at dddd (suspended), quota exceeded: removed {removed}; folder still there: "
        f"{(d / '20261027-000000-v01-dddd').exists()}")

with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    # Q3: the owner opens a suspended run two days after its last action; the server restarts the next day
    fake(d, "20261026-000000-v01-ffff", "2026-10-26T00:00:00", last_action=now - 2 * DAY)
    mgr = RunManager(d, keep_days=3.0, quota_gb=5.0)
    r = mgr.get("20261026-000000-v01-ffff")

    class WS:
        pass
    v = r.add_viewer(WS())
    r.remove_viewer(v)
    in_mem = r.meta["last_action"]
    on_disk = json.loads((d / "20261026-000000-v01-ffff" / "meta.json").read_text())["last_action"]
    mgr2 = RunManager(d, keep_days=3.0, quota_gb=5.0)  # a server restart
    after = mgr2.get("20261026-000000-v01-ffff").meta["last_action"]
    log(f"Q3 a viewer came and left: last action in memory {(now - in_mem) / DAY:.3f} d ago, on disk "
        f"{(now - on_disk) / DAY:.3f} d ago, after a restart {(now - after) / DAY:.3f} d ago")
    mgr2.keep_days = 1.9  # (equivalently: ~1 day after the restart with the default 3 days) older than the limit
    log(f"    removed by the next cleanup with the restart's value: {mgr2.cleanup()}")

with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    # Q4: a record from before this version (no last_action), its folder untouched for 10 days
    r = fake(d, "20261018-000000-v01-gggg", "2026-10-18T00:00:00", state="stopped", restorable=False)
    old = now - 10 * DAY
    os.utime(r / "meta.json", (old, old))
    os.utime(r / "stream.lfrec", (old, old))
    mgr = RunManager(d, keep_days=3.0, quota_gb=5.0)  # the server starts (and saves every record's meta)
    mt = (r / "meta.json").stat().st_mtime
    log(f"Q4 a record without last_action, meta.json 10 days old: after the server's start its mtime is "
        f"{(now - mt):.0f} s old; cleanup removes {mgr.cleanup()} (it would go only after {mgr.keep_days} days of "
        f"uninterrupted uptime)")

Path("/rev/out").mkdir(exist_ok=True)
Path("/rev/out/c04_cleanup.txt").write_text("\n".join(OUT) + "\n")
