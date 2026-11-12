"""c02: the sweep's statistics at their edges, through the private server (p97_osc, preset "one", k = 4, m = 1).

(a) mean_last over the whole duration (window = duration) and over a short window, against the exact time average
    (1/W) * integral of x(t) = x0 cos wt + v0/w sin wt;
(b) max / min with few samples (n_samples = 1 and 4) against the true amplitude over the duration: what the table
    says about the sampling;
(c) undefined values: the world-wide "x_first" in an empty scene (NaN with a note) for mean_last, max, final;
(d) the request's edges: window > duration (refused), n_samples = 0 (refused), a non-numeric value, a value list of
    mixed types, a non-hashable target id (expected: 400, not 500).
"""
import json
import math
import sys
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, post, record, start, sweep_done  # noqa: E402

res = {}
rid = start("p97_osc", "one", seed=1)
for _ in range(10):
    cmd(rid, "step", {"dt": 0.05})
time.sleep(1.0)


def run(body, rid=rid):
    st, js = post(f"/api/runs/{rid}/sweep", body)
    if st != 200:
        return st, js
    return st, sweep_done(rid, js["n"])


def mean_exact(x0, v0, w, a, b):
    F = lambda t: x0 / w * math.sin(w * t) - v0 / (w * w) * math.cos(w * t)  # noqa: E731
    return (F(b) - F(a)) / (b - a)


T = 0.7
st, js = run({"target": {"kind": "law", "id": "k"}, "values": [4.0, 9.0], "duration": T, "measure": "o1.x",
              "stat": "mean_last", "window": T, "n_samples": 200})
t0 = js["base"]["t"]
x0, v0 = math.cos(2 * t0), -2 * math.sin(2 * t0)
res["a"] = []
for r in js["results"]:
    w = math.sqrt(r["value"])
    ref = mean_exact(x0, v0, w, 0.0, T)
    res["a"].append({"k": r["value"], "window": T, "measured": r["measured"], "exact": ref, "rel": (r["measured"] - ref) / abs(ref)})
    print(f"(a) mean over the whole duration, k = {r['value']}: measured {r['measured']:.10g} exact {ref:.10g} rel {(r['measured'] - ref) / abs(ref):.2e} readings {r['readings']}")
st, js = run({"target": {"kind": "law", "id": "k"}, "values": [9.0], "duration": T, "measure": "o1.x",
              "stat": "mean_last", "window": 1e-6, "n_samples": 3})
r = js["results"][0]
ref = mean_exact(x0, v0, 3.0, T - 1e-6, T)
print(f"(a) mean over a window of 1e-6: measured {r['measured']:.10g} exact {ref:.10g} readings {r['readings']} trace t0 {r['trace']['t'][0]!r}")
res["a_short"] = {"measured": r["measured"], "exact": ref}

# (b) max with few samples
res["b"] = []
for ns in (1, 4, 200):
    st, js = run({"target": {"kind": "law", "id": "k"}, "values": [4.0], "duration": 3.0, "measure": "o1.x",
                  "stat": "max", "n_samples": ns})
    r = js["results"][0]
    amp = math.hypot(x0, v0 / 2)
    print(f"(b) max of x over 3 s (1.9 periods), n_samples = {ns:3d}: measured {r['measured']:.6g}, true max {amp:.6g}; "
          f"stat_text «{js['stat_text']}», readings {r['readings']}; message «{js['message']}»")
    res["b"].append({"n_samples": ns, "measured": r["measured"], "true_max": amp, "stat_text": js["stat_text"],
                     "readings": r["readings"]})

# (c) undefined values
rid2 = start("p97_osc", "empty", seed=1)
cmd(rid2, "step", {"dt": 0.1})
time.sleep(1.0)
res["c"] = {}
for stat in ("final", "mean_last", "max"):
    body = {"target": {"kind": "law", "id": "k"}, "values": [4.0], "duration": 0.5, "measure": "x_first", "stat": stat,
            "n_samples": 5}
    if stat == "mean_last":
        body["window"] = 0.2
    st, js = run(body, rid2)
    r = js["results"][0]
    print(f"(c) x_first in an empty scene, {stat}: measured {r.get('measured')!r}, note «{r.get('note')}», error «{r.get('error')}»")
    res["c"][stat] = {"measured": r.get("measured"), "note": r.get("note"), "error": r.get("error")}

# (d) request edges
cases = {
    "window > duration": {"target": {"kind": "law", "id": "k"}, "values": [4.0], "duration": 0.5, "measure": "o1.x",
                          "stat": "mean_last", "window": 0.6},
    "n_samples 0": {"target": {"kind": "law", "id": "k"}, "values": [4.0], "duration": 0.5, "measure": "o1.x",
                    "stat": "max", "n_samples": 0},
    "value text": {"target": {"kind": "law", "id": "k"}, "values": ["abc"], "duration": 0.5, "measure": "o1.x"},
    "value dict": {"target": {"kind": "law", "id": "k"}, "values": [{"a": 1}], "duration": 0.5, "measure": "o1.x"},
    "target id a list": {"target": {"kind": "law", "id": ["k"]}, "values": [4.0], "duration": 0.5, "measure": "o1.x"},
    "obj id a list": {"target": {"kind": "object", "obj": ["o1"], "param": "x"}, "values": [1.0], "duration": 0.5,
                      "measure": "o1.x"},
    "measure a list": {"target": {"kind": "law", "id": "k"}, "values": [4.0], "duration": 0.5, "measure": ["o1.x"]},
    "body a list": [1, 2],
}
res["d"] = {}
for name, body in cases.items():
    st, js = post(f"/api/runs/{rid}/sweep", body, raw=True)
    txt = js.decode("utf-8", "replace")[:160]
    print(f"(d) {name}: HTTP {st}: {txt}")
    res["d"][name] = {"status": st, "body": txt}
json.dump(res, open("/out/c02_sweep_stats_edges.json", "w"), indent=1, ensure_ascii=False)
