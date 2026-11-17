import glob, json, sys
sys.path.insert(0, "/lf/visualizations/server")
from lfviz.headless import read_stream
f = glob.glob("/lf/visualizations/recordings/u32_double_slit/story.*.lfrec.gz")[0]
msgs = read_stream(open(f, "rb").read())
frames = [m for m, b in msgs if m.get("type") == "frame"]
print(json.dumps(frames[370])[:600])
small = [(i, round(fr["t"], 4), fr.get("n_seg"), fr["coh"]) for i, fr in enumerate(frames) if isinstance(fr.get("coh"), dict) and fr["coh"].get("err") is not None and fr["coh"]["err"] < 2e-3]
print("frames with err < 2e-3:", len(small)); [print(x) for x in small[:12]]
errs = [(i, fr.get("n_seg"), fr["coh"].get("hist"), fr["coh"].get("err")) for i, fr in enumerate(frames) if isinstance(fr.get("coh"), dict) and fr["coh"].get("err") is not None]
for i in range(330, 420, 6): print([e for e in errs if e[0] == i])
