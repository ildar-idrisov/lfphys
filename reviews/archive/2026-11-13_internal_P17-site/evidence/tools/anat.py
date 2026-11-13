import gzip, json, sys, collections
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
w, rid = sys.argv[1], sys.argv[2]
idx = json.load(open(f"/lf/visualizations/recordings/{w}/index.json")); e = next(x for x in idx["recordings"] if x["id"] == rid)
data = gzip.decompress(open(f"/lf/visualizations/recordings/{w}/{e['file']}", "rb").read())
c, b = collections.Counter(), collections.Counter()
ts = collections.defaultdict(list)
for _o, m in protocol.iter_stream(data, 8):
    t = protocol.peek_meta(m)["type"]; c[t] += 1; b[t] += len(m); ts[t].append(protocol.peek_meta(m).get("t"))
for t in c: print(t, c[t], round(b[t] / 1e6, 2), "MB")
fr = ts["frame"]; print("frame t range", fr[0], fr[-1])
if "wave" in ts: print("wave t first/last", ts["wave"][:3], ts["wave"][-1])
