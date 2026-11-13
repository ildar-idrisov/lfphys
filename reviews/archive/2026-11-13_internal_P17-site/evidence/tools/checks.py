import gzip, json, sys, glob, collections
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
first = True
for idxf in sorted(glob.glob("/lf/visualizations/recordings/*/index.json")):
    idx = json.load(open(idxf))
    for e in idx["recordings"]:
        data = gzip.decompress(open(idxf.rsplit("/", 1)[0] + "/" + e["file"], "rb").read())
        st = collections.Counter(); bad = []
        for _o, m in protocol.iter_stream(data, 8):
            meta = protocol.peek_meta(m)
            if meta["type"] == "check":
                if first: print("example check meta keys:", sorted(meta)); first = False
                s = meta.get("status", meta.get("ok"))
                st[str(s)] += 1
                if s not in ("ok", True, "pass", None, "info"):
                    bad.append((meta.get("id") or meta.get("name"), s, str(meta.get("value"))[:30], str(meta.get("ref"))[:30]))
        print(idx["world"], e["id"], dict(st), bad[:3])
