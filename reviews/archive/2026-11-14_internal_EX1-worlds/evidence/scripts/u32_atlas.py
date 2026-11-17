"""R-W: u32 Explore atlas: per point, hits at the end, chi2, |gamma12| and its error; frames with an error < 3e-3; the
fringe-period check against lambda L / d; the share of photons that miss the ±30 mm screen."""
import glob, gzip, json, sys
sys.path.insert(0, "/lf/visualizations/server")
from lfviz.headless import read_stream
d = "/lf/visualizations/recordings/u32_double_slit/atlas/explore/"
man = json.load(open(glob.glob(d + "atlas.*.json")[0]))
ctl = man["controls"]; print([ (c["param"], c["values"]) for c in ctl]); print("points", len(man["points"]), "checks", man.get("checks"))
import itertools
combos = list(itertools.product(*[c["values"] for c in ctl]))
low = 0; out = []
for (fn, nb, state), vals in zip(man["points"], combos):
    msgs = read_stream(open(d + fn, "rb").read())
    fr = [m for m, b in msgs if m.get("type") == "frame"]
    ck = {m["id"]: m for m, b in msgs if m.get("type") == "check"}
    tiny = [(round(f["t"], 2), f["n_seg"], round(f["coh"]["hist"], 4), f["coh"]["err"]) for f in fr if isinstance(f.get("coh"), dict) and f["coh"].get("err") is not None and f["coh"]["err"] < 3e-3]
    last = fr[-1]
    fp = [c for k, c in ck.items() if "period" in k.lower() or "fringe" in str(c.get("label")).lower()]
    out.append((vals, last["n_seg"], last["counts"]["missed"], round(last["coh"]["hist"], 3) if last.get("coh") and last["coh"].get("hist") else None,
                round(last["coh"]["err"], 4) if last.get("coh") and last["coh"].get("err") else None, len(tiny), tiny[:2]))
for o in out: print(o)
print("points with a tiny-error frame:", sum(1 for o in out if o[5]))
