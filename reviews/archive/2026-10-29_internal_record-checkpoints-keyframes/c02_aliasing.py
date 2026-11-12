# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review 2026-10-29 (record checkpoints, key frames), check c02.
# Pickle copies a NumPy view as a separate array: two attributes of a world that share memory (a view and its base,
# two views of one buffer) share none after a checkpoint is loaded. A world that writes into one of them in place and
# reads the other would then go on differently. This lists, for every world after a few frames (and a live change),
# the groups of distinct arrays reachable from the world that share memory, and whether they still do after
# lfviz.checkpoint.dumps/loads.
#
#   docker run --rm --name lf-rev-c02 -v <engine>:/lf:ro -v <this folder>/out:/out -e LFPHYS_NO_GPU=1 \
#     -w /lf/visualizations light-funnel-viz python3 /lf/reviews/archive/2026-10-29_internal_record-checkpoints-keyframes/c02_aliasing.py
import json
import queue
import sys
import types

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys", "/lf/visualizations/tests"]
import numpy as np  # noqa: E402

from lfviz import checkpoint, registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
from test_restore import SMALL  # noqa: E402


def arrays(obj, path="sim", seen=None, out=None, depth=0):
    seen = set() if seen is None else seen
    out = [] if out is None else out
    if id(obj) in seen or depth > 12:
        return out
    seen.add(id(obj))
    if isinstance(obj, np.ndarray):
        out.append((path, obj))
        return out
    if isinstance(obj, (types.ModuleType, types.FunctionType, types.BuiltinFunctionType, type, str, bytes, int, float,
                        complex, bool)) or obj is None:
        return out
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:5000]:
            arrays(v, f"{path}[{k!r}]", seen, out, depth + 1)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for i, v in enumerate(list(obj)[:5000]):
            arrays(v, f"{path}[{i}]", seen, out, depth + 1)
    else:
        d = getattr(obj, "__dict__", None)
        if isinstance(d, dict):
            for k, v in d.items():
                arrays(v, f"{path}.{k}", seen, out, depth + 1)
        for k in getattr(type(obj), "__slots__", ()) or ():
            if hasattr(obj, k):
                arrays(getattr(obj, k), f"{path}.{k}", seen, out, depth + 1)
    return out


def groups(found):
    """Distinct array objects that share memory, as groups of paths."""
    by = {}
    for p, a in found:
        if a.size == 0:
            continue
        by.setdefault(id(a), (p, a))
    items = list(by.values())
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if np.may_share_memory(items[i][1], items[j][1]):
                try:
                    share = np.shares_memory(items[i][1], items[j][1], max_work=10**6)
                except Exception:  # noqa: BLE001 - too hard to decide: count as sharing
                    share = True
                if share:
                    parent[find(i)] = find(j)
    g = {}
    for i, (p, a) in enumerate(items):
        g.setdefault(find(i), []).append(p)
    return [sorted(v) for v in g.values() if len(v) > 1]


def lookup(found, path):
    for p, a in found:
        if p == path:
            return a
    return None


PLAN_SET = {"v02_double_slit": {"lam_nm": 500.0}, "v03_quantum_1d": {"energy": 1.2}, "v04_orbits": {"speed": 1.0},
            "v05_optics_bench": {"theta_deg": 30.0}, "v07_bell_test": {"b_deg": 30.0},
            "v10_fast_observer": {"obs_beta": 0.5}, "v11_double_slit_2d": {"slit_b": False},
            "v12_arrival_times_2d": {"slit_b": False}}

res = {}
for viz_id in [v for v in registry.viz_ids() if v != "v15_kerr_shadow"]:
    viz = registry.load(viz_id)
    params, _ = viz["schema"].resolve(None, SMALL.get(viz_id, {}))
    sim = viz["simulation"](params, 7, lambda m, b=None: None)
    run = Runner(sim, sim.emit, queue.Queue())
    run._start_world()
    for k in range(8):
        run._advance(sim.t + 0.3 * sim.default_speed)
        run._frame(0.0)
        if k == 3 and viz_id in PLAN_SET:
            run.handle({"cmd": "set", "args": {"values": PLAN_SET[viz_id]}})
    before = arrays(sim)
    g0 = groups(before)
    state = checkpoint.loads(checkpoint.dumps({"sim": sim}, sim.emit), sim.emit)
    after = arrays(state["sim"])
    broken = []
    for grp in g0:
        objs = [lookup(after, p) for p in grp]
        ok = all(o is not None for o in objs) and all(
            np.may_share_memory(objs[0], o) for o in objs[1:])
        if not ok:
            broken.append(grp[:6])
    res[viz_id] = {"arrays": len(before), "sharing_groups": len(g0), "broken_by_pickle": broken[:12]}
    print(viz_id, json.dumps(res[viz_id], ensure_ascii=False), flush=True)

with open("/out/c02_aliasing.json", "w") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
