import json, sys, hashlib
from pathlib import Path
A, B = Path(sys.argv[1]), Path(sys.argv[2])
for w in sys.argv[3:]:
    ia = json.loads((A / w / "index.json").read_text()); ib = json.loads((B / w / "index.json").read_text())
    ea = {e["id"]: e for e in ia["atlases"]}; eb = {e["id"]: e for e in ib["atlases"]}
    for aid in ea:
        a, b = ea[aid], eb[aid]
        ma = json.loads((A / w / a["file"]).read_text()); mb = json.loads((B / w / b["file"]).read_text())
        da, db = (A / w / a["file"]).parent, (B / w / b["file"]).parent
        same_pts = ma["points"] == mb["points"]
        nbytes_eq = sum((da / p[0]).read_bytes() == (db / p[0]).read_bytes() for p in ma["points"] if p[0])
        npts = sum(1 for p in ma["points"] if p[0])
        diffkeys = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k))
        print(f"{w}/{aid}: key {a['key']==b['key']} manifest-file {a['file']==b['file']} ({a['file'].rsplit('/',1)[1]} vs {b['file'].rsplit('/',1)[1]}) "
              f"points-list equal {same_pts}; point files byte-equal {nbytes_eq}/{npts}; base equal {ma['base']==mb['base']}; manifest keys differing: {diffkeys}")
        for k in diffkeys:
            print(f"    {k}: {str(ma.get(k))[:80]} | {str(mb.get(k))[:80]}")
