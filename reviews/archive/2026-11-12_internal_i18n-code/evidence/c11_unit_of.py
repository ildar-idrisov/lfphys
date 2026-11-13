"""playground.unit_of for every parameter without a unit whose label is a T: the unit the {label:unit} placeholder
extracts from the English label and from its Russian translation. Flags pairs where the two disagree in kind (one
empty, or a phrase of words rather than a unit)."""
import os, re, sys
sys.path[:0] = ["/w/visualizations", "/w/visualizations/server", "/w/lfphys"]
os.environ.setdefault("LFVIZ_EXTRA", "/w/visualizations/tests/playgrounds:/w/visualizations/tests/instruments_worlds")
from lfviz import i18n, registry
from lfviz.i18n import render, is_t
from lfviz.playground import unit_of
ru = i18n.catalogue("ru")
n = bad = 0
for vid in registry.viz_ids():
    viz = registry.load(vid)
    ps = [("schema", p) for p in viz["schema"].params]
    ps += [(typ, p) for typ, ot in (getattr(viz["simulation"], "PALETTE", None) or {}).items() for p in ot.schema.params]
    for where, p in ps:
        if p.unit or not is_t(p.label):
            continue
        u = unit_of(p)
        if not u:
            continue
        n += 1
        en, r = render(u, {}, "en"), render(u, ru, "ru")
        words = lambda s: len(re.findall(r"[^\W\d_]{4,}", s)) >= 2
        if (not en) != (not r) or words(en) or words(r):
            bad += 1
            print(f"{vid} {where}.{p.id}: label en «{render(p.label)}» -> unit «{en}»; ru «{render(p.label, ru, 'ru')}» -> unit «{r}»")
print(f"params whose unit comes from the label: {n}; suspicious: {bad}")
