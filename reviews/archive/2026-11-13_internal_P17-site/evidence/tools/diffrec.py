import gzip, json, sys
sys.path.insert(0, "/lf/visualizations/server")
import numpy as np
from lfviz import protocol
A, B = sys.argv[1], sys.argv[2]
for w in sys.argv[3:]:
    ia, ib = json.load(open(f"{A}/{w}/index.json")), json.load(open(f"{B}/{w}/index.json"))
    for ea in ia["recordings"]:
        eb = next(x for x in ib["recordings"] if x["id"] == ea["id"])
        ma = [protocol.decode(m) for _o, m in protocol.iter_stream(gzip.decompress(open(f"{A}/{w}/{ea['file']}", "rb").read()), 8)]
        mb = [protocol.decode(m) for _o, m in protocol.iter_stream(gzip.decompress(open(f"{B}/{w}/{eb['file']}", "rb").read()), 8)]
        diffs = []
        for i, ((m1, b1), (m2, b2)) in enumerate(zip(ma, mb)):
            ks = [k for k in set(m1) | set(m2) if k != "cpu_ms" and json.dumps(m1.get(k), sort_keys=True, default=str) != json.dumps(m2.get(k), sort_keys=True, default=str)]
            bs = [k for k in set(b1) | set(b2) if k not in b1 or k not in b2 or not np.array_equal(b1[k], b2[k])]
            if ks or bs:
                diffs.append((i, m1["type"], ks, bs))
        kinds = {}
        for d in diffs:
            kinds.setdefault((d[1], tuple(sorted(d[2])), tuple(d[3])), 0)
            kinds[(d[1], tuple(sorted(d[2])), tuple(d[3]))] += 1
        print(w, ea["id"], "same file" if ea["sha256"] == eb["sha256"] else "files differ", "msgs", len(ma), len(mb), "diff kinds:", kinds)
