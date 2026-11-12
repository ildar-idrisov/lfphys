# Review B5, check c12: v15 at the ends of the screen's range (half-width 4 and 30 M, 256 x 256) and with the narrow
# ring for retrograde Keplerian gas (inner edge beyond 6 M): checks, the share of pixels the `pixels` check tests,
# lit pixels. Root and run as c02 (see its header).
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from v15_kerr_shadow.viz import SCAN_M  # noqa: E402

for preset, params in (("m87", {"res": "l", "half": 4.0}), ("m87", {"res": "l", "half": 30.0}),
                       ("edge_on", {"res": "l", "half": 30.0}),
                       ("ring", {"res": "s", "emitter": "keplerian", "retro": True, "chi": 0.9})):
    t0 = time.time()
    h = Harness("v15_kerr_shadow", preset, params)
    h.run_to(SCAN_M * 1.01)
    ch = h.checks()
    bad = [k for k, c in ch.items() if not c.get("info") and c.get("ok") is False]
    lit = 0
    tot = 0
    for m, b in h.msgs:
        if m.get("type") == "rows":
            I = np.asarray(b["I"])
            nr = m["i1"] - m["i0"]
            s = I.reshape(m["n_max"] + 1, nr, m["nx"]).sum(0)
            lit += int((s > 0).sum())
            tot += s.size
    print(f"{preset} {params}: failed {bad}; pixels note: {ch['pixels']['note'][:60]}...; lit pixels {lit}/{tot}; "
          f"lyapunov {ch.get('lyapunov', {}).get('value')}; {time.time() - t0:.1f} s")
