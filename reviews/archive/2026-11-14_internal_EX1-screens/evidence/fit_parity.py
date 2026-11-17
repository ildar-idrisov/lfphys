import json, sys
sys.path.insert(0, "/lf/lfphys")
from lfphys.tools.stats import linear_fit
cases = json.load(open("/q/fit_cases.json"))
worst = 0.0
for c in cases:
    r = linear_fit(c["x"], c["y"], c["sx"], c["sy"], c["model"])
    py = dict(zip(r["names"], r["params"])) if isinstance(r["params"], (list, tuple)) or hasattr(r["params"], "__len__") else r["params"]
    ps = dict(zip(r["names"], r["sigma"]))
    if c["model"] == "power":
        py = {"A": r["A"], "p": r["n_exp"]}; ps = {"A": r["A_sigma"], "p": r["n_exp_sigma"]}
    if c["model"] == "quadratic":
        py["xv"] = r["vertex"]; ps["xv"] = r["vertex_sigma"]
    js = c["js"]
    names = {"line0": ["b"], "line": ["a", "b"], "quadratic": ["c0", "c1", "c2", "xv"], "power": ["A", "p"]}[c["model"]]
    pyn = list(py.values())
    rels = []
    for k_js, k_py in zip(names, list(py.keys())):
        a, b = js["params"][k_js], py[k_py]
        sa, sb = js["sigma"][k_js], ps[k_py]
        rels.append(max(abs(a - b) / max(abs(b), 1e-300), abs(sa - sb) / max(abs(sb), 1e-300)))
    worst = max(worst, max(rels))
    print(f"{c['name']:22s} js {[round(js['params'][k], 8) for k in names]} py {[round(float(py[k]), 8) for k in py]} max rel diff {max(rels):.1e} scaled js {js['scaled']} py {r['scaled']}")
print("worst", worst)
