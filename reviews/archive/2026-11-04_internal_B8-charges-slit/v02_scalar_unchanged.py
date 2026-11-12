"""Review B8 (v02): is the scalar model's behaviour unchanged? The same presets and seeds run through the harness with
the current v02 (/lf/visualizations) and with v02 at git HEAD (the committed version before B8; a scratch copy mounted
at /old/visualizations, the same current lfphys). Compared: every detection (time, x, y, flags), every segment's
curves, every check value. Usage: python3 v02_scalar_unchanged.py new|old  (prints a digest per preset).
"""
import hashlib
import json
import sys

import numpy as np

root = "/lf/visualizations" if sys.argv[1] == "new" else "/old/visualizations"
for p in (root, root + "/server", "/lf/lfphys", root + "/tests"):
    sys.path.insert(0, p)
from harness import Harness  # noqa: E402

V = "v02_double_slit"
for preset in ("photon_young", "photon_eraser", "photon_partial", "electron_microscope", "triple_mod", "c60_grw"):
    h = Harness(V, preset, seed=4)
    h.run_to(min(3.0, 3000.0 / h.of("header")[0]["rate"]))
    h.set(a_um=h.sim.params["a_um"] * 1.1)  # a live change: a new segment
    h.run_to(h.sim.t + min(1.0, 1000.0 / h.sim.app.rate))
    det = hashlib.sha256()
    ndet = 0
    for m, b in h.msgs:
        if m.get("type") == "detections" and b:
            for k in sorted(b):
                det.update(k.encode())
                det.update(np.ascontiguousarray(b[k]).tobytes())
            ndet += m.get("n", 0)
    seg = hashlib.sha256()
    for m, b in h.msgs:
        if m.get("type") == "segment":
            for k in sorted(b or {}):
                if k.startswith("c_"):
                    seg.update(k.encode())
                    seg.update(np.ascontiguousarray(b[k]).tobytes())
    chk = hashlib.sha256(json.dumps(sorted((c["id"], repr(c["value"])) for c in h.of("check"))).encode())
    counts = {k: v for k, v in h.sim.counts.items() if k != "reflected"}
    print(f"{preset}: detections {ndet} {det.hexdigest()[:16]}; curves {seg.hexdigest()[:16]}; checks "
          f"{chk.hexdigest()[:16]}; counts {json.dumps(counts, sort_keys=True)}")
