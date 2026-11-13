import gzip, json, sys
sys.path.insert(0, "/lf/visualizations/server")
import numpy as np
from lfviz import protocol
A, B, w, rid, typ, blob = sys.argv[1:7]
def load(D):
    i = json.load(open(f"{D}/{w}/index.json")); e = next(x for x in i["recordings"] if x["id"] == rid)
    return [protocol.decode(m) for _o, m in protocol.iter_stream(gzip.decompress(open(f"{D}/{w}/{e['file']}", "rb").read()), 8)]
ma, mb = load(A), load(B)
n = 0
for (m1, b1), (m2, b2) in zip(ma, mb):
    if m1["type"] == typ and blob in b1 and not np.array_equal(b1[blob], b2[blob]):
        x, y = b1[blob].astype(float), b2[blob].astype(float)
        if n < 4:
            print("t", m1["t"], "shape", x.shape, "max abs diff", np.nanmax(np.abs(x - y)), "max abs", np.nanmax(np.abs(x)), "nan?", np.isnan(x).sum(), np.isnan(y).sum(), x.ravel()[:6], y.ravel()[:6])
        n += 1
print("differing", n)
