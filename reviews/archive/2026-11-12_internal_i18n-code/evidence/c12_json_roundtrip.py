"""A T after a JSON round trip (a sweep's spec file, a record's message) is a plain dict: str() of it is the dict's repr,
not English. sweep.with_unit compares str(label) and str(unit) — so a label that already names its unit gets the unit
twice once the spec has been read back from disk (table_csv reads the spec file)."""
import json, sys
sys.path[:0] = ["/w/visualizations", "/w/visualizations/server", "/w/lfphys"]
from lfviz.i18n import T, render
from lfviz.sweep import with_unit
lab, unit = T("Window size, nm"), T("nm")
live = with_unit(lab, unit)
disk = with_unit(json.loads(json.dumps(lab)), json.loads(json.dumps(unit)))
print("live :", render(live))
print("disk :", render(disk))
print("str(T) live:", str(lab), "| str(after JSON):", str(json.loads(json.dumps(lab))))
