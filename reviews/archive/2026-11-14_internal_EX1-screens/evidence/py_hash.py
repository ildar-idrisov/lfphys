# sha256 of every quantised blob's dequantised float32 bytes, per file/message/blob (Python's protocol.decode)
import gzip, hashlib, json, sys, struct
from pathlib import Path
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
root = Path(sys.argv[1])
out = {}
files = sorted(list(root.glob("*/atlas/*/*.lfpt.gz")) + list(root.glob("*/*.lfrec.gz")))
nq = 0
for f in files:
    data = gzip.decompress(f.read_bytes())
    assert data[:8] == b"LFVREC1\n"
    pos, k = 8, 0
    while pos + 4 <= len(data):
        (ln,) = struct.unpack_from("<I", data, pos)
        msg = data[pos + 4: pos + 4 + ln]
        meta = protocol.peek_meta(msg)
        if any(d.get("q") for d in meta.get("blobs", [])):
            m, blobs = protocol.decode(msg)
            for d in meta["blobs"]:
                if d.get("q"):
                    a = blobs[d["name"]]
                    assert a.dtype.name == "float32"
                    out[f"{f.relative_to(root)}|{k}|{d['name']}"] = hashlib.sha256(a.tobytes()).hexdigest()[:16]
                    nq += 1
        pos += 4 + ln; k += 1
json.dump(out, open(sys.argv[2], "w"), sort_keys=True)
print(len(files), "files", nq, "quantised blobs")
