import json, sys, gzip, hashlib
from pathlib import Path
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
A, B, C = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])  # prev, new, local (the committed run's recordings)
def msgs(p):
    d = gzip.decompress(p.read_bytes())
    return [bytes(m) for _o, m in protocol.iter_stream(d, len(protocol.MAGIC))]
tot = same_file = same_local = 0
for ia in sorted(A.glob("*/index.json")):
    w = ia.parent.name
    xa = json.loads(ia.read_text()); xb = json.loads((B / w / "index.json").read_text()); xc = json.loads((C / w / "index.json").read_text())
    eb = {e["id"]: e for e in xb["recordings"]}; ec = {e["id"]: e for e in xc["recordings"]}
    for e in xa["recordings"]:
        tot += 1
        fa, fb, fc = A / w / e["file"], B / w / eb[e["id"]]["file"], C / w / ec[e["id"]]["file"]
        eq = fa.read_bytes() == fb.read_bytes(); eql = fb.read_bytes() == fc.read_bytes()
        same_file += eq; same_local += eql
        note = ""
        if not eq:
            ma, mb = msgs(fa), msgs(fb)
            nd = sum(1 for x, y in zip(ma, mb) if x != y) + abs(len(ma) - len(mb))
            first = next((i for i, (x, y) in enumerate(zip(ma, mb)) if x != y), None)
            note = f" DIFF: {nd} of {len(ma)}/{len(mb)} messages differ, first at {first}"
            if first is not None:
                a0, b0 = protocol.decode(ma[first])[0], protocol.decode(mb[first])[0]
                note += f" type {a0.get('type')}; keys differing {sorted(k for k in set(a0)|set(b0) if a0.get(k)!=b0.get(k))[:6]}"
        print(f"{w}/{e['id']}: prev==new {eq}; new==local {eql}; key prev {e['key']} new {eb[e['id']]['key']} local {ec[e['id']]['key']}{note}")
print(f"# {tot} recordings: {same_file} byte-identical between ee6da3f and 507c059; {same_local} new == the local (committed run's) files")
