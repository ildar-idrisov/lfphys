"""Parameters whose unit is a substring of the label without being named as a unit there: the server's
playground._setting drops the unit from the log ("str(unit) in str(label)", English), the player's ui.js pName drops it
from the refusal's name ("t(lab).includes(t(u))", in the viewer's language). has_unit (sweep.with_unit / instruments.js
hasUnit) is the token-based check the code already has."""
import os, sys
sys.path[:0] = ["/w/visualizations", "/w/visualizations/server", "/w/lfphys"]
os.environ.setdefault("LFVIZ_EXTRA", "/w/visualizations/tests/playgrounds:/w/visualizations/tests/instruments_worlds")
from lfviz import i18n, registry
from lfviz.i18n import render
from lfviz.sweep import has_unit
ru = i18n.catalogue("ru")
seen = set()
def check(vid, where, p):
    if not p.unit:
        return
    for lang, cat in (("en", {}), ("ru", ru)):
        lab = render(p.label, cat, lang) if isinstance(p.label, dict) else str(cat.get(p.label, p.label) if lang == "ru" else p.label)
        u = render(p.unit, cat, lang) if isinstance(p.unit, dict) else str(cat.get(p.unit, p.unit) if lang == "ru" else p.unit)
        if u and u in lab and not has_unit(lab, u):
            key = (vid, where, p.id, lang)
            if key not in seen:
                seen.add(key)
                print(f"{lang} {vid} {where} {p.id}: label «{lab}» unit «{u}» -> unit dropped")
for vid in registry.viz_ids():
    viz = registry.load(vid)
    for p in viz["schema"].params:
        check(vid, "schema", p)
    for typ, ot in (getattr(viz["simulation"], "PALETTE", None) or {}).items():
        for p in ot.schema.params:
            check(vid, "palette:" + typ, p)
print("cases:", len(seen))
# sanity: how many (label, unit) pairs were examined, and a sample
n = 0
for vid in registry.viz_ids():
    viz = registry.load(vid)
    ps = list(viz["schema"].params) + [p for ot in (getattr(viz["simulation"], "PALETTE", None) or {}).values() for p in ot.schema.params]
    for p in ps:
        if p.unit:
            n += 1
            if n % 40 == 1:
                print("sample:", vid, p.id, repr(str(p.label)), repr(str(p.unit)), "| ru:", render(p.label, ru, "ru"), "|", render(p.unit, ru, "ru") if isinstance(p.unit, dict) else ru.get(p.unit, p.unit))
print("params with a unit:", n)
