"""c04: `checkpoint_now` is the server's command for the sweeps, but the REST /command route and the WebSocket forward
any command name to the worker. Can a viewer (any page or script on the LAN) make the world write checkpoints and start
record segments at will, and put arbitrary data into the record through `tag`?

p97_osc playing at 20 frames/s; 40 `checkpoint_now` commands from the REST route, 0.1 s apart, each with a fresh tag;
one with a 300 000-character tag. Counted in the record: checkpoint messages with a file (pickles written),
record_segment markers, the largest checkpoint message.
"""
import json
import sys
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, record, start  # noqa: E402

rid = start("p97_osc", "two", seed=4)
cmd(rid, "play")
time.sleep(1.5)
rec0 = record(rid)
n_ck0 = sum(1 for m in rec0 if m["type"] == "checkpoint" and m.get("file"))
n_seg0 = sum(1 for m in rec0 if m["type"] == "record_segment")
st = []
for i in range(40):
    st.append(cmd(rid, "checkpoint_now", {"tag": f"viewer-{i}"})[0])
    time.sleep(0.1)
st.append(cmd(rid, "checkpoint_now", {"tag": "x" * 300_000})[0])
time.sleep(2.0)
cmd(rid, "pause")
time.sleep(1.0)
rec = record(rid)
cks = [m for m in rec if m["type"] == "checkpoint"]
files = [m for m in cks if m.get("file")]
segs = [m for m in rec if m["type"] == "record_segment"]
big = max((len(json.dumps(m)) for m in cks), default=0)
viewer = [m for m in cks if str(m.get("tag", "")).startswith(("viewer-", "xxx"))]
out = {"run": rid, "http": sorted(set(st)), "checkpoints_with_a_file_before": n_ck0,
       "checkpoints_with_a_file_after": len(files), "answered_viewer_tags": len(viewer),
       "record_segments_before": n_seg0, "record_segments_after": len(segs),
       "largest_checkpoint_message_chars": big}
print(json.dumps(out, indent=1))
json.dump(out, open("/out/c04_checkpoint_now_from_a_viewer.json", "w"), indent=1)
