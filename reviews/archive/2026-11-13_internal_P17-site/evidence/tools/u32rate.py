import gzip, json, sys
sys.path.insert(0, "/lf/visualizations/server")
import numpy as np
from lfviz import protocol
live = [protocol.decode(m) for _o, m in protocol.iter_stream(open(sys.argv[1], "rb").read(), 8)]
idx = json.load(open("/lf/visualizations/recordings/u32_double_slit/index.json")); e = next(x for x in idx["recordings"] if x["id"] == "young")
rec = [protocol.decode(m) for _o, m in protocol.iter_stream(gzip.decompress(open("/lf/visualizations/recordings/u32_double_slit/" + e["file"], "rb").read()), 8)]
def at(ms, T):
    fr = [(m, b) for m, b in ms if m["type"] == "frame" and m["t"] <= T][-1]
    m, b = fr
    c = b.get("counts")
    return m["t"], (None if c is None else int(np.sum(c))), {k: m[k] for k in ("n_seg", "chi2", "coh") if k in m}
T = max(m["t"] for m, _ in live if m["type"] == "frame")
print("live", at(live, T)); print("rec ", at(rec, T))
nd = lambda ms: sum(len(b.get("x", b.get("pos", []))) if b else 0 for m, b in ms if m["type"] == "detections" and m["t"] <= T)
print("detections blobs keys", [list(b.keys()) for m, b in live if m["type"] == "detections"][:1])
