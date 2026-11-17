import sys, gzip, json
sys.path.insert(0, "/s/work"); from live2 import post, show  # noqa
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import headless
S = "/api/atlas/s03_projectile/explore/point"
def frames_have_probe(body):
    return any(m.get("poisoned") for m, _b in headless.read_stream(body) if m.get("type") == "frame")
step = sys.argv[1]
for h in ([1.5] if step == "before" else [1.5, 1.7]):
    r = show(f"[{step}] h={h}", post(S, {"values": {"h_m": h}}))
    print(f"   X-LF-Key {r[1].get('X-LF-Key')}; frames carry the edited code's mark: {frames_have_probe(r[2])}")
