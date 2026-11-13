"""Compare a recording (site/record.py) with a live run of the same preset and seed on a private server.

    python3 compare_live.py SERVER WORLD REC [wall_seconds]

Prints: header differences, the non-frame messages of both (type, t, name), the t=0 frame difference and, for the
frames of the live run, the nearest recording frame's difference in numbers and blobs.
"""
import gzip
import json
import sys
import time
import urllib.request

import numpy as np

sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol  # noqa: E402

SRV, WORLD, REC = sys.argv[1], sys.argv[2], sys.argv[3]
WALL = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0


def req(path, body=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(SRV + path, data=data, method=method or ("POST" if data is not None else "GET"),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=600) as f:
        return f.read()


def msgs_of(data):
    out = []
    for _o, m in protocol.iter_stream(data, len(protocol.MAGIC)):
        meta, blobs = protocol.decode(m)
        out.append((meta, blobs))
    return out


idx = json.loads(req(f"/recordings/{WORLD}/index.json"))
e = next(x for x in idx["recordings"] if x["id"] == REC)
rec = msgs_of(gzip.decompress(req(f"/recordings/{WORLD}/{e['file']}")))

run = json.loads(req("/api/runs", {"viz": WORLD, "preset": e["preset"], "seed": e.get("seed", 1)}))
rid = run["id"]
time.sleep(4)
req(f"/api/runs/{rid}/command", {"cmd": "play"})
time.sleep(WALL)
req(f"/api/runs/{rid}/command", {"cmd": "pause"})
time.sleep(2)
live = msgs_of(req(f"/api/runs/{rid}/stream"))
try:
    req(f"/api/runs/{rid}/stop", {})
except Exception:
    pass

hr = next(m for m, _ in rec if m["type"] == "header")
hl = next(m for m, _ in live if m["type"] == "header")
diff = {k: (hr.get(k), hl.get(k)) for k in set(hr) | set(hl) if hr.get(k) != hl.get(k)}
print("HEADER keys differing:", {k: (str(a)[:80], str(b)[:80]) for k, (a, b) in diff.items()})


def nonframe(ms):
    return [(m["type"], m.get("t"), m.get("name") or m.get("reason") or m.get("id") or "") for m, _ in ms
            if m["type"] not in ("frame",)]


nr, nl = nonframe(rec), nonframe(live)
print("REC non-frame types:", sorted({x[0] for x in nr}))
print("LIVE non-frame types:", sorted({x[0] for x in nl}))
tl_end = max(m["t"] for m, _ in live if m["type"] == "frame")
print("live world time reached:", tl_end, "recording t_end:", e["t_end"])
nr_cut = [x for x in nr if x[1] is None or x[1] <= tl_end]
skip = {"command", "checkpoint", "resumed", "record_segment", "busy", "state", "end", "notice"}
import os
only = set(filter(None, os.environ.get("ONLY", "").split(",")))
a = [x for x in nr_cut if x[0] not in skip and (not only or x[0] in only)]
b = [x for x in nl if x[0] not in skip and (not only or x[0] in only)]
from collections import Counter
print("  rec types", Counter(x[0] for x in a), "live types", Counter(x[0] for x in b))
print(f"non-frame (excluding {sorted(skip)}) up to t={tl_end:.6g}: rec {len(a)}, live {len(b)}")
for i, (x, y) in enumerate(zip(a, b)):
    if x[0] != y[0] or x[2] != y[2] or (x[1] is not None and y[1] is not None and abs(x[1] - y[1]) > 1e-9 * max(1, abs(x[1]))):
        print("  first difference at", i, "rec", x, "live", y)
        break
else:
    print("  same sequence of types/names" + ("" if len(a) == len(b) else f" (lengths differ: {len(a)} vs {len(b)})"))

rf = [(m, b) for m, b in rec if m["type"] == "frame"]
lf = [(m, b) for m, b in live if m["type"] == "frame"]
print("frames: rec", len(rf), "live", len(lf))
rt = np.array([m["t"] for m, _ in rf])


def cmp(m1, b1, m2, b2):
    worst = {}
    for k in set(m1) | set(m2):
        if k in ("t", "cpu_ms", "speed_actual", "lag", "type"):
            continue
        x, y = m1.get(k), m2.get(k)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            d = abs(x - y) / max(1e-300, abs(x), abs(y))
            if d > 1e-6:
                worst[k] = d
        elif x != y and not (isinstance(x, (list, dict)) and json.dumps(x, default=str) == json.dumps(y, default=str)):
            worst[k] = "differs" if (x is not None and y is not None) else f"only in {'rec' if y is None else 'live'}"
    for k in set(b1) | set(b2):
        x, y = b1.get(k), b2.get(k)
        if x is None or y is None:
            worst["blob:" + k] = f"only in {'rec' if y is None else 'live'}"
        elif x.shape != y.shape:
            worst["blob:" + k] = f"shape {x.shape} vs {y.shape}"
        elif x.size == 0:
            continue
        else:
            d = float(np.nanmax(np.abs(x.astype(float) - y.astype(float))) / max(1e-300, float(np.nanmax(np.abs(x.astype(float))))))
            if d > 1e-6:
                worst["blob:" + k] = d
    return worst


print("frame at t=0:", cmp(*rf[0], *lf[0]))
exact = 0
for m, bl in lf[1:]:
    j = int(np.argmin(np.abs(rt - m["t"])))
    if abs(rt[j] - m["t"]) <= 1e-12 * max(1.0, abs(m["t"])):
        exact += 1
        w = cmp(*rf[j], m, bl)
        if w:
            print("  same t", m["t"], "differs:", {k: v for k, v in list(w.items())[:6]})
print("live frames at exactly a recording frame's t:", exact)
# nearest frames: the relative step in t and the difference
show = [len(lf) // 4, len(lf) // 2, len(lf) - 1]
for i in show:
    m, bl = lf[i]
    j = int(np.argmin(np.abs(rt - m["t"])))
    print(f"  live frame {i} t={m['t']:.6g} vs rec frame {j} t={rt[j]:.6g}: ",
          {k: (round(v, 4) if isinstance(v, float) else v) for k, v in list(cmp(*rf[j], m, bl).items())[:8]})
print("RUN", rid)
