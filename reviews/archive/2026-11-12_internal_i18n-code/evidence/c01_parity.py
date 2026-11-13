"""Python renderer on the shared cases; also NaN/inf and plural crashes (not representable in JSON)."""
import json, sys, math
sys.path.insert(0, "/w/lfphys"); sys.path.insert(0, "/w/visualizations/server")
from lfphys.i18n import T, render, plural_category
EN = json.load(open("/w/visualizations/locales/en.json"))
EN.update(json.load(open("/w/visualizations/p01_gravity/locales/en.json")))
cases = json.load(open(sys.argv[1]))
out = {}
for name, x in cases:
    try:
        out[name] = render(x, EN, "en")
    except Exception as e:
        out[name] = f"EXC {type(e).__name__}: {e}"
print(json.dumps(out, ensure_ascii=False, indent=0))
print("--- non-JSON values")
for v in (float("nan"), float("inf"), -float("inf")):
    print(repr(v), "default:", render(T("x = {x}", x=v)), "| .3g:", render(T("{x:.3g}", x=v)))
cat = {"{n:d} days": {"one": "{n:d} день", "few": "{n:d} дня", "many": "{n:d} дней", "other": "{n:d} дня"}}
for v in (float("nan"), float("inf"), 1e300, 2.5):
    try:
        print("ru plural n=", v, "->", render(T("{n:d} days", n=v), cat, "ru"))
    except Exception as e:
        print("ru plural n=", v, "-> EXC", type(e).__name__, e)
import numpy as np
print("np.float32 .2f:", render(T("{x:.2f}", x=np.float32(0.123456))), "| np.int64 .3g:", render(T("{x:.3g}", x=np.int64(123456))))
print("np.bool_:", render(T("{b}", b=np.bool_(True))))
try:
    print("json np.float32:", json.dumps(T("{x}", x=np.float32(1.5))))
except Exception as e:
    print("json np.float32: EXC", type(e).__name__, e)
