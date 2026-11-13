import gzip, json, sys, glob
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
for idxf in sorted(glob.glob("/lf/visualizations/recordings/*/index.json")):
    idx = json.load(open(idxf))
    for e in idx["recordings"]:
        data = gzip.decompress(open(idxf.rsplit("/",1)[0] + "/" + e["file"], "rb").read())
        for _o, m in protocol.iter_stream(data, len(protocol.MAGIC)):
            meta = protocol.peek_meta(m)
            if meta["type"] == "header":
                b = meta.get("backend") or {}
                print(idx["world"], e["id"], "used:", sorted((b.get("used") or {}).keys()), "seed", meta.get("seed"), "preset", meta.get("preset"), "fps", meta.get("fps"))
                break
