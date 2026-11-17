# per lab-step point of s03: the grid values and the last frame's meas (what the instruments read after landing)
import gzip, json, sys, struct
from pathlib import Path
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
root = Path("/rec/s03_projectile/atlas")
out = {}
for a in sorted(root.iterdir()):
    if not a.name.startswith("lab."): continue
    man = json.loads(next(a.glob("atlas.*.json")).read_text())
    ctl = man["controls"]
    rows = []
    for i, (fn, size, state) in enumerate(man["points"]):
        data = gzip.decompress((a / fn).read_bytes())
        pos, last, events = 8, None, []
        while pos + 4 <= len(data):
            (ln,) = struct.unpack_from("<I", data, pos)
            m = protocol.peek_meta(data[pos + 4: pos + 4 + ln])
            if m["type"] == "frame": last = m
            if m["type"] == "event": events.append((m.get("kind"), m.get("t")))
            pos += 4 + ln
        # flat index -> values (single control)
        c = ctl[0]
        rows.append({"v": c["values"][i], "meas": last.get("meas"), "t_last": last["t"], "events": events})
    out[man["step"]] = {"controls": ctl, "references": man.get("references"), "rows": rows}
json.dump(out, open("/q/lab_points.json", "w"), indent=0, default=str)
for k, v in out.items():
    print(k, [ (r["v"], round(r["meas"].get("range") or -1, 6), r["meas"].get("range_vacuum")) for r in v["rows"]][:20])
