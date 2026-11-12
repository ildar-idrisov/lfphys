"""Latency of p03/p04 scene edits through the harness (as the worker runs them). Usage: lat.py <tag> [cases...]"""
import json, signal, sys, time
sys.path.insert(0, "/lf/visualizations/tests"); sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from harness import Harness

CAP = int(__import__("os").environ.get("CAP", "90"))

class TO(Exception):
    pass

def alarm(*a):
    raise TO()

signal.signal(signal.SIGALRM, alarm)

def oid(h, typ):
    return next(o["id"] for o in h.sim.objects.values() if o["type"] == typ)

def scene(h, **args):
    n0 = len(h.errors())
    t0 = time.perf_counter()
    signal.alarm(CAP)
    try:
        h.cmd("scene", **args)
        signal.alarm(0)
    except TO:
        return {"s": None, "note": f">{CAP} s (killed)"}
    dt = time.perf_counter() - t0
    errs = h.errors()[n0:]
    return {"s": round(dt, 3), "err": errs[-1][:200] if errs else None}

CASES = {
 # p03 molecules preset (3-D, 150 dimers)
 "mol3_shape_bent": ("p03_molecules", "molecules", None, lambda h: scene(h, op="set", id=oid(h, "molecule"), values={"shape": "bent"})),
 "mol3_shape_chain": ("p03_molecules", "molecules", None, lambda h: scene(h, op="set", id=oid(h, "molecule"), values={"shape": "chain"})),
 "mol3_start": ("p03_molecules", "molecules", None, lambda h: scene(h, op="set", id=oid(h, "molecule"), values={"start": "maxwell"})),
 "mol3_dup": ("p03_molecules", "molecules", None, lambda h: scene(h, op="duplicate", id=oid(h, "molecule"))),
 "mol3_sz": ("p03_molecules", "molecules", None, lambda h: scene(h, op="set", id=oid(h, "molecule"), values={"sz": 2.0})),
 "mol3_count2000": ("p03_molecules", "molecules", None, lambda h: scene(h, op="set", id=oid(h, "molecule"), values={"count": 2000})),
 "mol3_atoms50": ("p03_molecules", "molecules", None, lambda h: scene(h, op="set", id=oid(h, "molecule"), values={"shape": "chain", "atoms": 50})),
 # p03 2-D default world: molecules added
 "mol2_add": ("p03_molecules", None, {}, lambda h: scene(h, op="add", type="molecule", values={})),
 "mol2_add_count2000": ("p03_molecules", None, {}, lambda h: scene(h, op="add", type="molecule", values={"count": 2000})),
 "mol2_add_chain50": ("p03_molecules", None, {}, lambda h: scene(h, op="add", type="molecule", values={"shape": "chain", "atoms": 50})),
 # gas
 "gas2_add": ("p03_molecules", None, {}, lambda h: scene(h, op="add", type="gas", values={})),
 "gas3_n20000": ("p03_molecules", None, {"dim": "3d"}, lambda h: scene(h, op="add", type="gas", values={"n": 20000})),
 "gas2_n20000": ("p03_molecules", None, {}, lambda h: scene(h, op="add", type="gas", values={"n": 20000})),
 "gas3_n12000": ("p03_molecules", None, {"dim": "3d"}, lambda h: scene(h, op="add", type="gas", values={"n": 12000})),
 "mol2_add_count250": ("p03_molecules", None, {}, lambda h: scene(h, op="add", type="molecule", values={"count": 250})),
 "mol3_count600": ("p03_molecules", "molecules", None, lambda h: scene(h, op="set", id=oid(h, "molecule"), values={"count": 600})),
 "maxwell_n_set": ("p03_molecules", "maxwell", None, lambda h: scene(h, op="set", id=oid(h, "gas"), values={"n": 400})),
}

def main():
    tag = sys.argv[1]
    names = sys.argv[2:] or list(CASES)
    for name in names:
        viz, preset, params, op = CASES[name]
        t0 = time.perf_counter()
        h = Harness(viz, preset, params)
        h.run_to(h.sim.t + 1e-13)
        build = time.perf_counter() - t0
        r = op(h)
        r.update({"case": name, "tag": tag, "build_s": round(build, 2)})
        print(json.dumps(r, ensure_ascii=False), flush=True)

main()
