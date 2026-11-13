"""Live (sweepable) parameters whose label already names their unit (with_unit must not add it again)."""
import os, sys
sys.path[:0] = ["/w/visualizations", "/w/visualizations/server", "/w/lfphys"]
os.environ.setdefault("LFVIZ_EXTRA", "/w/visualizations/tests/playgrounds:/w/visualizations/tests/instruments_worlds")
from lfviz import registry
from lfviz.sweep import has_unit
for vid in registry.viz_ids():
    viz = registry.load(vid)
    for p in viz["schema"].params:
        if p.unit and has_unit(str(p.label), str(p.unit)):
            print(vid, p.id, "live" if p.live else "-", repr(str(p.label)), repr(str(p.unit)))
    for typ, ot in (getattr(viz["simulation"], "PALETTE", None) or {}).items():
        for p in ot.schema.params:
            if p.unit and has_unit(str(p.label), str(p.unit)):
                print(vid, "palette", typ, p.id, repr(str(p.label)), repr(str(p.unit)))
