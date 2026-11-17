import json, sys, gzip
from pathlib import Path
import numpy as np
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import headless, protocol
A, B, w = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
ea = next(e for e in json.loads((A / w / "index.json").read_text())["atlases"] if e["id"] == "explore")
eb = next(e for e in json.loads((B / w / "index.json").read_text())["atlases"] if e["id"] == "explore")
ma, mb = json.loads((A / w / ea["file"]).read_text()), json.loads((B / w / eb["file"]).read_text())
da, db = (A / w / ea["file"]).parent, (B / w / eb["file"]).parent
ndiff = 0; kinds = {}; maxrel = {}
for (fa, _, _), (fb, _, _) in zip(ma["points"], mb["points"]):
    if fa.split(".")[1] == fb.split(".")[1]:
        continue
    ndiff += 1
    xa = headless.read_stream((da / fa).read_bytes(), raw=True); xb = headless.read_stream((db / fb).read_bytes(), raw=True)
    for (m1, b1), (m2, b2) in zip(xa, xb):
        t = m1.get("type")
        for k in set(m1) | set(m2):
            if k in ("blobs",): continue
            if json.dumps(protocol.clean(m1.get(k)), sort_keys=True) != json.dumps(protocol.clean(m2.get(k)), sort_keys=True):
                kinds[f"{t}.meta.{k}"] = kinds.get(f"{t}.meta.{k}", 0) + 1
        for k in set(b1) | set(b2):
            x, y = np.asarray(b1.get(k)), np.asarray(b2.get(k))
            if x.shape != y.shape or x.tobytes() != y.tobytes():
                kinds[f"{t}.blob.{k}"] = kinds.get(f"{t}.blob.{k}", 0) + 1
                if x.shape == y.shape and x.dtype.kind == "f":
                    r = float(np.nanmax(np.abs(x - y)) / (np.nanmax(np.abs(x)) or 1))
                    maxrel[f"{t}.{k}"] = max(maxrel.get(f"{t}.{k}", 0), r)
print(f"u32 explore: {ndiff} of {len(ma['points'])} point files differ between numpy's AVX2 (X86_V3) and baseline (X86_V2) paths on the same machine")
print("what differs (message.field: number of messages):", dict(sorted(kinds.items(), key=lambda kv: -kv[1])[:12]))
print("largest relative difference of float blobs:", {k: f"{v:.2g}" for k, v in maxrel.items()})
