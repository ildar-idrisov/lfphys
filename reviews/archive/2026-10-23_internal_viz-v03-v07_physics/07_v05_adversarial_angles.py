"""v05 through the harness: angles near the critical / grazing angle (where the closed forms of the checks are
ill-conditioned), including the critical angle as the player displays it (12 significant digits, player.js fmtVal),
and the world's state after a refused or failed change.
Output: out/07_v05_adversarial_angles.txt
"""
import math
import sys
import traceback

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

OUT = open("out/07_v05_adversarial_angles.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


def failed(h):
    out = []
    for c in h.checks().values():
        if c.get("ok") is False:
            out.append((c["id"], c["value"], c["ref"]))
        elif c.get("ok") is None and c.get("rel") is not None and c.get("ref") is not None \
                and abs(c["rel"]) > max(c.get("tol") or 1e-9, 1e-12):  # the player's rule (player.js checkRows)
            out.append((c["id"], c["value"], c["ref"], c["rel"]))
    return out


thc = math.degrees(math.asin(1 / 1.5))
say(f"face critical angle glass 1.5 -> air: {thc!r} deg; as the player shows it (12 digits): {float(f'{thc:.12g}')!r}")

say("\nA. prism + 200 nm gap (preset ftir): theta set live near the face critical angle = grazing angle in the gap")
for th in [float(f"{thc:.12g}"), float(f"{thc:.10g}"), thc, thc + 1e-12, thc - 1e-12, thc + 1e-9, thc - 1e-9,
           thc + 1e-7, thc - 1e-7, thc + 1e-5]:
    h = Harness("v05_optics_bench", "ftir")
    h.set(theta_deg=th)
    f = [x for x in failed(h) if x[0].endswith("1")]
    seg = h.of("segment")[-1]
    say(f"  theta = {th!r} (offset {th - thc:+.2e} deg): errors {h.errors()}, failed checks of the new segment: {f}")
    if f:
        say(f"     film check note: {h.checks()['film1']['note'][:160]}")

say("\nB. bare face (preset tir, no gap): theta near the critical angle")
for th in [float(f"{thc:.12g}"), thc, thc + 1e-13, thc + 3e-13, thc + 1e-12, thc + 1e-11, thc + 1e-9, thc + 1e-7]:
    h = Harness("v05_optics_bench", "tir")
    try:
        h.set(theta_deg=th)
    except Exception as e:  # noqa: BLE001  (an exception the runner does not catch would crash the worker)
        say(f"  theta = {th!r}: UNCAUGHT {type(e).__name__}: {e}")
        say("     world state after it: params theta =", h.sim.params["theta_deg"], ", seg =", h.sim.seg,
            ", segments emitted =", len(h.of("segment")))
        continue
    f = [x for x in failed(h) if str(x[0]).endswith("1")]
    say(f"  theta = {th!r} (offset {th - thc:+.2e} deg): errors {h.errors()}, failed: {f}")

say("\nC. scan of theta = theta_c + k ulp-ish steps (1e-14 deg) for the bare face: which checks fail / crash")
bad = {}
for k in range(-20, 41):
    th = thc + k * 1e-14
    h = Harness("v05_optics_bench", "tir")
    try:
        h.set(theta_deg=th)
        f = tuple(sorted({x[0] for x in failed(h)}))
        e = tuple(h.errors())
    except Exception as ex:  # noqa: BLE001
        f, e = ("UNCAUGHT " + type(ex).__name__,), ()
    if f or e:
        bad[k] = (f, e)
for k, v in bad.items():
    say(f"  k = {k:+d}: failed {v[0]}, errors {[x[:90] for x in v[1]]}")
if not bad:
    say("  none")
