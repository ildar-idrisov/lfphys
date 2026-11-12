# Review B6-framework, script s08: what a playground's record holds, by message type (the runs of b01_browser.mjs in
# runs_browser/): every message but "frame" is accumulative, so a viewer's tab keeps all of them for the session.
# Usage: python3 /out/s08_record_by_type.py /out/runs_browser/<run id>
import json
import sys
from pathlib import Path

from lfviz import protocol

d = Path(sys.argv[1])
meta = json.loads((d / "meta.json").read_text())
by, n = {}, {}
for f in sorted(d.glob("stream*.lfrec")):
    data = f.read_bytes()
    for _, m in protocol.iter_stream(data, len(protocol.MAGIC)):
        t = protocol.peek_meta(m).get("type")
        by[t] = by.get(t, 0) + len(m)
        n[t] = n.get(t, 0) + 1
wall = meta.get("buffer", {}).get("segs", [{}])
print("run", meta["id"], "world time", meta.get("sim_t"))
for t in sorted(by, key=lambda k: -by[k]):
    print(f"  {t:16s} {n[t]:6d} messages {by[t] / 1e6:8.2f} MB" + ("" if t == "frame" else "   (accumulative: kept by the tab)"))
acc = sum(v for k, v in by.items() if k != "frame")
print(f"accumulative total {acc / 1e6:.1f} MB; checkpoint files:",
      [(p.name, round(p.stat().st_size / 1e6, 1)) for p in (d / "checkpoints").glob("*.pkl")])
