# Reviewer's check: is p03's restore after the live box, the solver switch and drags bit-identical in the WHOLE engine
# state (positions, velocities, generator, energies, books), not only in the 16-bit drawing positions the lab test
# compares? Run in Docker from engine/ (REVIEW.md).
import queue
import sys

import numpy as np

sys.path[:0] = ["/lf/visualizations/tests", "/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys"]
from lfviz import registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402

V = "p03_molecules"


def world(params):
    viz = registry.load(V)
    p, errors = viz["schema"].resolve(None, params)
    assert not errors
    frames, script = [], []

    def emit(meta, blobs=None):
        if meta.get("type") == "frame":
            frames.append((meta, blobs))
            script.append({"frame": meta["t"]})
        elif meta.get("type") == "command":
            script.append({"t": meta["t"], "cmd": meta["cmd"], "args": meta["args"]})
    sim = viz["simulation"](p, 7, emit)
    return sim, Runner(sim, emit, queue.Queue()), frames, script


def diff_state(a, b):
    out = []
    for k in a:
        va, vb = a[k], b.get(k)
        if isinstance(va, np.ndarray):
            if not (isinstance(vb, np.ndarray) and va.shape == vb.shape and np.array_equal(va, vb)):
                out.append(k)
        elif k == "stats":
            continue
        elif repr(va) != repr(vb):
            out.append(k)
    return out


def scenario(label, params, cmds):
    sim, run_, frames, script = world(params)
    run_._start_world()
    t = 0.0
    for c in cmds:
        if isinstance(c, float):
            t += c
            run_._advance(t)
            run_._frame(0.0)
        else:
            if c.get("args", {}).get("id") == "GID":
                c = {**c, "args": {**c["args"], "id": next(iter(sim.objects))}}
            run_.handle(c)
    sim2, run2, frames2, _ = world(params)
    run2.restore(1, list(script)[:-1], sim.t, lambda on: None)
    run2._frame(0.0)
    d = diff_state(sim.md.state_dict(), sim2.md.state_dict())
    ba, bb = sim.md.energy_balance(), sim2.md.energy_balance()
    q_same = np.array_equal(frames[-1][1]["q"], frames2[-1][1]["q"])
    print(f"  {label}: world now: solver {type(sim.md).__name__}, box {np.round(sim.md.L, 6).tolist()}, live "
          f"{ {k: sim.live[k] for k in ('dynamics', 'model', 'box_mode', 'Lx', 'Ly')} }, W_box "
          f"{sim.md.energy_balance().get('W_box')}")
    print(f"  {label}: frame q equal {q_same}; engine state keys that differ: {d or 'none'}; "
          f"balance equal {ba == bb}; t {sim.t!r} vs {sim2.t!r}")


if __name__ == "__main__":
    print("== restore of p03 after the LB1 live changes: whole engine state ==")
    scenario("hard -> wall box -> forces (WCA) -> drag -> affine box",
             {"dim": "2d", "dynamics": "hard", "Lx": 30.0, "Ly": 30.0, "boundary": "walls"},
             [{"cmd": "scene", "args": {"op": "add", "type": "gas", "values": {"n": 40, "x": 10.0, "y": 10.0,
                                                                               "sx": 8.0, "sy": 8.0}}},
              0.5e-12,
              {"cmd": "set", "args": {"values": {"box_mode": "wall", "Lx": 34.0}}},
              {"cmd": "set", "args": {"values": {"dynamics": "forces", "model": "wca"}}},
              1.0e-12,
              {"cmd": "scene", "args": {"op": "edit", "id": "GID", "values": {"x": 20.0, "y": 15.0}}},
              {"cmd": "set", "args": {"values": {"box_mode": "affine", "Ly": 28.0}}},
              1.5e-12])
    scenario("LJ periodic: affine Lx, Ly in steps, then back",
             {"dim": "2d", "Lx": 12.0, "Ly": 12.0},
             [{"cmd": "scene", "args": {"op": "add", "type": "gas", "values": {"n": 120, "T": 150.0}}},
              0.5e-12,
              {"cmd": "set", "args": {"values": {"Lx": 11.0}}}, 0.3e-12,
              {"cmd": "set", "args": {"values": {"Ly": 11.0}}}, 0.3e-12,
              {"cmd": "set", "args": {"values": {"Lx": 12.0, "Ly": 12.0}}}, 0.5e-12])
