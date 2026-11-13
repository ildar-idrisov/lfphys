"""What the i18n tests' tools see in constructed files (they live in the review folder, the tools are the repo's)."""
import sys
from pathlib import Path
sys.path[:0] = ["/w/visualizations/tests", "/w/visualizations/server", "/w/lfphys", "/w/visualizations"]
import i18n_tools as tools
F = Path(__file__).resolve().parent / "c05_fixtures"
print("shadowed_t(shadow.js) lines:", tools.shadowed_t(F / "shadow.js"), "(cases on lines 3,4,6,7,8; control line 9)")
print("cyrillic_lines(cyr.js):", tools.cyrillic_lines(F / "cyr.js"), "(Cyrillic data on lines 2,3,4)")
print("cyrillic_lines(cyr.py):", tools.cyrillic_lines(F / "cyr.py"), "(Cyrillic data on lines 1,2,3)")
print("cyrillic_lines(cyr.css):", tools.cyrillic_lines(F / "cyr.css"), "(.css is not a code file the guard reads)")
print("code_files() suffixes:", sorted({f.suffix for f in tools.code_files()}))
print("msgids_py(msgids.py):", tools.msgids_py(F / "msgids.py"))
print("msgids_js(msgids.js):", tools.msgids_js(F / "msgids.js"))
from lfviz.i18n import msgids, T
print("msgids() of a schema-like dict with a plain label:", msgids({"label": "Plain string label nobody translated", "unit": T("nm")}))
# needs_translation: msgids without Latin letters are exempt -- a Greek/symbol-only label with Cyrillic-free text
print("needs_translation('{n} µs') =", tools.needs_translation("{n} µs"), "; ('°C') =", tools.needs_translation("°C"))
