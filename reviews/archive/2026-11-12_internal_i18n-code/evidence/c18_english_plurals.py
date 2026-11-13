"""English plural forms live in en.json; str(T), render(T) and error_body's "text" ignore them (no catalogue)."""
import sys
sys.path[:0] = ["/w/visualizations", "/w/visualizations/server", "/w/lfphys"]
from lfviz import i18n
from lfviz.i18n import T, error_body, render_in
x = T("all {n:d} workers are busy with open runs: close the tab of one of them (it will be suspended and go on when "
      "you open it again)", n=1)
print("str(T)            :", str(x))
print("error_body text   :", error_body(x)["text"])
print("render_in(x, 'en'):", render_in(x, "en"))
y = T("{n:d} days", n=1)
print("str / render_in en:", str(y), "|", render_in(y, "en"))
