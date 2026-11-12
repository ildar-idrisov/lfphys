import sys, json, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
out = {}
for vid in registry.viz_ids():
    t0 = time.time()
    try:
        viz = registry.load(vid)
        sch = viz["schema"].to_json()
        d = {"kind": viz.get("kind"), "title": viz.get("title"), "schema": sch, "load_s": round(time.time()-t0, 2)}
        sim = viz["simulation"]
        pal = getattr(sim, "PALETTE", None)
        if pal:
            d["palette"] = {}
            for k, ot in pal.items():
                try:
                    d["palette"][k] = {"label": ot.label, "kind": getattr(ot, "kind", None),
                                       "schema": ot.schema.to_json() if hasattr(ot.schema, "to_json") else str(ot.schema)}
                except Exception as e:
                    d["palette"][k] = {"err": repr(e)}
        out[vid] = d
    except Exception as e:
        out[vid] = {"err": repr(e)}
json.dump(out, open("/out/schemas.json", "w"), ensure_ascii=False, indent=1, default=str)
print("ok", len(out))
