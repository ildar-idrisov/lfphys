"""c07 (world time of p03 is in seconds: steps of 1e-13 s = 0.1 ps): carry-over in a real section (p03_molecules), through the private server.

(a) What the framework's notice says when the new world ADAPTS objects (a 3-D scene of molecules carried into a plane:
    p03's _import_values drops z, sz, vz silently) — compared with what the world's measurables show before and after.
(b) A large scene: a gas of N atoms carried into a world of the same space but another non-live law (boundary). The
    carried scene travels as the JSON parameter «scene», bounded by params.JSON_MAX = 900 000 characters.
"""
import json
import sys
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, record, start, wait  # noqa: E402

res = {}


def last_meas(rid, w=None):
    fr = [m for m in record(rid) if m["type"] == "frame" and m.get("meas")]
    return fr[-1]["meas"] if fr else {}


def new_world(rid, params, n_head):
    cmd(rid, "new_world", {"params": params, "carry": True})
    try:
        wait(lambda: sum(1 for m in record(rid) if m["type"] == "header") > n_head, 90)
    except TimeoutError:
        pass
    rec = record(rid)
    errs = [m for m in rec if m["type"] == "error"]
    notes = [m for m in rec if m["type"] == "notice"]
    return rec, errs, notes


# (a)
rid = start("p03_molecules", "molecules", seed=3)
cmd(rid, "step", {"dt": 2e-13})  # p03's world time is in seconds: 0.2 ps
time.sleep(2)
m1 = last_meas(rid)
rec, errs, notes = new_world(rid, {"dim": "2d", "Lx": 5.0, "Ly": 5.0, "boundary": "periodic", "model": "lj"}, 1)
time.sleep(1)
cmd(rid, "step", {"dt": 1e-13})
time.sleep(2)
m2 = last_meas(rid)
heads = [m for m in record(rid) if m["type"] == "header"]
print("(a) worlds:", len(heads), "| N before", m1.get("N"), "rho", m1.get("rho"), "| N after", m2.get("N"), "rho", m2.get("rho"))
print("(a) notices after the new world:", [n["text"][:300] for n in notes[-3:]])
print("(a) errors:", [e["text"][:300] for e in errs[-2:]])
res["a"] = {"N_before": m1.get("N"), "N_after": m2.get("N"), "rho_before": m1.get("rho"), "rho_after": m2.get("rho"),
            "notices": [n["text"] for n in notes[-3:]], "errors": [e["text"] for e in errs[-2:]], "worlds": len(heads)}

# (b) a large gas
for n in (4000, 12000):
    rid = start("p03_molecules", None, seed=4, params={"dim": "3d", "Lx": 30.0, "Ly": 30.0, "Lz": 30.0,
                                                        "boundary": "periodic", "scene": {"format": "lfscene", "version": 1,
                                                        "objects": [{"type": "gas", "label": "Аргон", "values": {"n": n, "T": 300.0}}]}})
    cmd(rid, "step", {"dt": 1e-13})
    time.sleep(3)
    rec, errs, notes = new_world(rid, {"dim": "3d", "Lx": 30.0, "Ly": 30.0, "Lz": 30.0, "boundary": "walls"}, 1)
    heads = [m for m in rec if m["type"] == "header"]
    print(f"(b) gas of {n} atoms: worlds {len(heads)}; last error: {errs[-1]['text'][:300] if errs else None}")
    if len(heads) > 1:
        print(f"    world 2 header: {len(json.dumps(heads[-1]))} chars")
    res[f"b_{n}"] = {"worlds": len(heads), "error": errs[-1]["text"] if errs else None,
                     "header_chars": len(json.dumps(heads[-1]))}
json.dump(res, open("/out/c07_carry_p03.json", "w"), indent=1, ensure_ascii=False)
