"""What a user sees when a number typed into a form is outside the schema's range, or a field is cleared.

The start form (player/js/ui.js paramForm) sends Number(input.value): an emptied field is sent as 0, and min/max of
<input type=number> are not enforced. The live control (ui.js control) refuses an empty field but sends any finite
number. Both reach Schema.resolve / Schema.coerce_live (server/lfviz/params.py _coerce)."""
import json
import sys

sys.path.insert(0, "/lf/visualizations/server")
sys.path.insert(0, "/lf/visualizations")
from lfviz import registry  # noqa: E402

registry.ensure_path()
out = []
for vid in registry.viz_ids():
    viz = registry.load(vid)
    sch = viz["schema"]
    world = [p for p in sch.params if not p.hidden and not p.live and p.type in ("float", "int")]
    live = [p for p in sch.params if not p.hidden and p.live and p.type in ("float", "int")]
    for p in world[:2]:
        for v, why in ((0, "field cleared (sent as 0)"), ((p.min or 0) - 1, "typed below min"),
                       ((p.max or 0) * 10 + 1, "typed above max")):
            params, errs = sch.resolve(None, {p.id: v})
            out.append({"world": vid, "param": p.id, "label": p.label, "value": v, "why": why, "path": "start form",
                        "shown": ("параметры: " + "; ".join(errs)) if errs else "(accepted)"})
    for p in live[:2]:
        for v, why in (((p.min or 0) - 1, "typed below min"), ((p.max or 0) * 10 + 1, "typed above max")):
            _, errs = sch.coerce_live(sch.defaults(), {p.id: v})
            out.append({"world": vid, "param": p.id, "label": p.label, "value": v, "why": why, "path": "live control",
                        "shown": ("Изменение не применено: " + "; ".join(errs)) if errs else "(accepted)"})
json.dump(out, open("/out/typed.json", "w"), ensure_ascii=False, indent=1)
for o in out:
    print(f"{o['world']:<22} {o['path']:<12} {o['param']:<12} {o['why']:<26} -> {o['shown']}")
