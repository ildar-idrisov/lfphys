"""C1 review, check 01: is a restored world the record's world going on — for EVERY message, not only the last frame?

tests/test_restore.py compares the last frame after a restore. Here, for every visualization, the original runner is
advanced in irregular frame steps (with live changes / view commands where the world has them), the server's script
of its record is taken at a "suspension" point, a second runner is rebuilt from it (Runner.restore), and then BOTH are
driven through the same continuation (the same frame advances and commands); every message each emits after the
suspension point is compared (meta without the runner's wall-clock keys, and every blob, bit for bit).

Run (engine mounted read-only at /lf):
  docker run --rm --name lf-c1rev-c01 -v <engine>:/lf:ro -v <this folder>:/rev -w /lf/visualizations \
      light-funnel-viz python3 /rev/c01_restore_all_messages.py
Output: /rev/out/c01_restore_all_messages.txt
"""
import math
import queue
import sys
import time
import traceback

import numpy as np

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from lfviz import registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402

SMALL = {  # as tests/test_restore.py
    "v08_wave_3d": {"n": 128, "zmax": 10.0},
    "v09_thomas_3d": {"ngrid": 48},
    "v11_double_slit_2d": {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse",
                           "n_bohm": 100, "n_tracks": 10},
    "v12_arrival_times_2d": {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0},
}
VOLATILE = {"cpu_ms", "speed_actual", "lag"}


class Rec:
    def __init__(self):
        self.msgs = []
        self.script = []
        self.muted = False

    def emit(self, meta, blobs=None):
        if self.muted:
            return
        meta = dict(meta)
        self.msgs.append((meta, {k: np.array(v, copy=True) for k, v in (blobs or {}).items()}))
        if meta.get("type") == "frame":
            self.script.append({"frame": meta["t"]})
        elif meta.get("type") == "command":
            self.script.append({"t": meta["t"], "cmd": meta["cmd"], "args": meta["args"]})


def build(viz_id, values=None, seed=7):
    viz = registry.load(viz_id)
    params, errors = viz["schema"].resolve(None, {**SMALL.get(viz_id, {}), **(values or {})})
    assert not errors, errors
    rec = Rec()
    sim = viz["simulation"](params, seed, rec.emit)

    def make_world(preset, vals, sd):
        p, errs = viz["schema"].resolve(preset, vals or {})
        if errs:
            raise ValueError("; ".join(errs))
        return viz["simulation"](p, seed if sd in (None, "") else int(sd), rec.emit), {"preset": preset}
    run = Runner(sim, rec.emit, queue.Queue(), make_world=make_world)
    return run, rec


def diff(a, b, path=""):
    """First difference between two messages' metas/blobs (None if equal)."""
    if isinstance(a, dict):
        ka, kb = set(a) - VOLATILE, set(b) - VOLATILE
        if ka != kb:
            return f"{path}: keys differ {sorted(ka ^ kb)}"
        for k in sorted(ka):
            d = diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if isinstance(a, np.ndarray):
        if a.shape != b.shape or a.dtype != b.dtype:
            return f"{path}: shape/dtype {a.shape}/{a.dtype} vs {b.shape}/{b.dtype}"
        if a.dtype.kind in "fc":
            same = np.array_equal(a, b, equal_nan=True)
            if not same:
                m = np.nanmax(np.abs(a.astype(complex) - b.astype(complex)))
                return f"{path}: max |diff| {m:.3g}"
            return None
        return None if np.array_equal(a, b) else f"{path}: integer arrays differ"
    if isinstance(a, float) and isinstance(b, float):
        if (math.isnan(a) and math.isnan(b)) or a == b:
            return None
        return f"{path}: {a!r} vs {b!r}"
    return None if a == b else f"{path}: {str(a)[:80]!r} vs {str(b)[:80]!r}"


def compare(orig, rest, label, out):
    if len(orig) != len(rest):
        ta = [m[0].get("type") for m in orig]
        tb = [m[0].get("type") for m in rest]
        out.append(f"  {label}: DIFFERENT message counts {len(orig)} vs {len(rest)}; types {summ(ta)} vs {summ(tb)}")
        return False
    for i, ((ma, ba), (mb, bb)) in enumerate(zip(orig, rest)):
        d = diff(ma, mb, f"msg[{i}] {ma.get('type')}") or diff(ba, bb, f"msg[{i}] {ma.get('type')} blobs")
        if d:
            out.append(f"  {label}: DIFFERS at {d}")
            return False
    out.append(f"  {label}: identical ({len(orig)} messages: {summ([m[0].get('type') for m in orig])})")
    return True


def summ(types):
    c = {}
    for t in types:
        c[t] = c.get(t, 0) + 1
    return ", ".join(f"{k}×{v}" for k, v in sorted(c.items()))


def drive(run, steps, cmds_at=None, sleep=0.0):
    """Advance in the given frame times, handling commands {frame index: [cmd, ...]} before that frame's advance."""
    for i, t in enumerate(steps):
        for c in (cmds_at or {}).get(i, []):
            run.handle(c)
        if t > run.sim.t:
            run._advance(t)
        run._frame(0.0)
        if sleep:
            time.sleep(sleep)


CASES = {
    "v04_orbits": {3: [{"cmd": "set", "args": {"values": {"speed": 1.1}}}]},
    "v08_wave_3d": {2: [{"cmd": "view", "args": {"op": "plane", "id": 2, "origin": [0, 0, 5], "normal": [0.3, 0.2, 0.93]}}]},
    "v11_double_slit_2d": {4: [{"cmd": "set", "args": {"values": {"slit_b": False}}}]},
    "v12_arrival_times_2d": {},
    "v10_fast_observer": {3: [{"cmd": "set", "args": {"values": {"obs_beta": 0.5}}}]},
}


def one(viz_id, out, sleep=0.0, n1=12, n2=12):
    rng = np.random.default_rng(3)
    run, rec = build(viz_id)
    run._start_world()
    span = 3.0 * run.sim.default_speed
    ts, t = [], 0.0
    for _ in range(n1 + n2):
        t += span * rng.uniform(0.02, 0.2)
        ts.append(t)
    cmds = CASES.get(viz_id, {})
    drive(run, ts[:n1], cmds, sleep=sleep)
    script = list(rec.script)
    t_end = run.sim.t
    k = len(rec.msgs)
    drive(run, ts[n1:])
    orig_after = rec.msgs[k:]

    run2, rec2 = build(viz_id)
    rec2.muted = True
    run2.restore(1, script, t_end, lambda on: setattr(rec2, "muted", bool(on)))
    rec2.muted = False
    drive(run2, ts[n1:])
    return compare(orig_after, rec2.msgs, f"{viz_id}{' (wall-clock spaced frames, %.2f s)' % sleep if sleep else ''}", out)


def main():
    out = [f"C1 check 01 — restore compared on every message after the suspension point ({time.strftime('%Y-%m-%d %H:%M')})"]
    ids = registry.viz_ids()
    out.append("\n[A] every visualization: frames in irregular steps (+ a live change / view command where listed), "
               "restore, the same continuation for both")
    for vid in ids:
        try:
            one(vid, out)
        except Exception as e:  # noqa: BLE001
            out.append(f"  {vid}: ERROR {e!r}\n" + traceback.format_exc(limit=3))
        print(out[-1], flush=True)

    out.append("\n[B] the original advanced with wall time between its frames (as a live run), the restore without")
    for vid, sl in (("v10_fast_observer", 0.4), ("v02_double_slit", 1.05), ("v04_orbits", 0.0)):
        try:
            one(vid, out, sleep=sl, n1=6, n2=6)
        except Exception as e:  # noqa: BLE001
            out.append(f"  {vid}: ERROR {e!r}")
        print(out[-1], flush=True)

    # [C] a command handled after a step in the same batch (no frame between them)
    out.append("\n[C] a `step` and a `set` handled in one batch (paused world): the set's recorded t is after the step")
    try:
        run, rec = build("v11_double_slit_2d")
        run._start_world()
        drive(run, [0.3, 0.6])
        run.handle({"cmd": "step", "args": {"dt": 0.5}})
        run.handle({"cmd": "set", "args": {"values": {"slit_b": False}}})
        run._frame(0.0)
        script = list(rec.script)
        t_end = run.sim.t
        cmd = [c for c in script if "cmd" in c][-1]
        out.append(f"  recorded: set at t = {cmd['t']:.6g}; frames before it: {[c['frame'] for c in script if 'frame' in c]}")
        k = len(rec.msgs)
        drive(run, [t_end + 0.5, t_end + 1.0, t_end + 1.5, t_end + 2.0])
        orig_after = rec.msgs[k:]
        run2, rec2 = build("v11_double_slit_2d")
        run2.restore(1, script, t_end, lambda on: setattr(rec2, "muted", bool(on)))
        rec2.muted = False
        drive(run2, [t_end + 0.5, t_end + 1.0, t_end + 1.5, t_end + 2.0])
        compare(orig_after, rec2.msgs, "v11 after step+set", out)
    except Exception as e:  # noqa: BLE001
        out.append(f"  ERROR {e!r}\n" + traceback.format_exc(limit=4))
    print(out[-1], flush=True)

    # [D] a restored world n >= 2: the planes the previous world handed over (adopt_view)
    out.append("\n[D] v08: a plane placed in world 1, then new_world (the planes carry over), then the latest world restored")
    try:
        run, rec = build("v08_wave_3d")
        run._start_world()
        drive(run, [0.5, 1.0])
        run.handle({"cmd": "view", "args": {"op": "plane", "id": 1, "origin": [0, 0, 5], "normal": [0.5, 0.0, 0.866]}})
        run.handle({"cmd": "view", "args": {"op": "plane", "id": 2, "origin": [0, 0, 5], "normal": [0.0, 1.0, 0.0]}})
        drive(run, [1.5])
        run.handle({"cmd": "new_world", "args": {"params": {**SMALL["v08_wave_3d"]}}})
        hidx = max(i for i, (m, _) in enumerate(rec.msgs) if m.get("type") == "header")
        header2 = rec.msgs[hidx][0]
        # the server's script of the latest world: what follows its header
        script, seen = [], False
        for m, _ in rec.msgs[hidx + 1:]:
            if m.get("type") == "frame":
                script.append({"frame": m["t"]})
            elif m.get("type") == "command":
                script.append({"t": m["t"], "cmd": m["cmd"], "args": m["args"]})
        drive(run, [0.4, 0.8])
        script = []
        for m, _ in rec.msgs[hidx + 1:]:
            if m.get("type") == "frame":
                script.append({"frame": m["t"]})
            elif m.get("type") == "command":
                script.append({"t": m["t"], "cmd": m["cmd"], "args": m["args"]})
        planes_orig = [p["normal"] for p in run.sim.planes.values()]
        out.append(f"  world 2 (live run): planes {sorted(run.sim.planes)} normals {planes_orig}; header2 planes "
                   f"defaults {header2['scene3d']['planes'].get('defaults')}")
        # rebuild as the worker does: the world from the header's params and seed, then restore(world=2, script)
        viz = registry.load("v08_wave_3d")
        rec2 = Rec()
        sim2 = viz["simulation"](header2["params"], header2["seed"], rec2.emit)
        run2 = Runner(sim2, rec2.emit, queue.Queue())
        run2.restore(2, script, run.sim.t, lambda on: setattr(rec2, "muted", bool(on)))
        planes_rest = [p["normal"] for p in run2.sim.planes.values()]
        out.append(f"  world 2 (restored): planes {sorted(run2.sim.planes)} normals {planes_rest}")
        out.append("  -> " + ("SAME" if planes_orig == planes_rest else "DIFFERENT: the restored world lost the planes "
                                                                          "the previous world handed over"))
    except Exception as e:  # noqa: BLE001
        out.append(f"  ERROR {e!r}\n" + traceback.format_exc(limit=4))
    print(out[-1], flush=True)

    with open("/rev/out/c01_restore_all_messages.txt", "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
