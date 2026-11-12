# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review 2026-10-29 (record checkpoints, key frames), check c01.
# A world continued from its checkpoint against the uninterrupted world, with what the shipped test leaves out:
# live changes, actions, slice planes, step / next_event BEFORE the checkpoint, and after it the same commands plus a
# new world (its header), in irregular frame steps. Two fresh processes load the same checkpoint (a control: if they
# differ between themselves the difference is the world's own non-determinism, not the checkpoint).
#
# Run (engine read-only, outputs to ./out):
#   docker run --rm --name lf-rev-c01 -v <engine>:/lf:ro -v <this folder>/out:/out -e PYTHONDONTWRITEBYTECODE=1 \
#     -e LFPHYS_NO_GPU=1 -w /lf/visualizations light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-29_internal_record-checkpoints-keyframes/c01_checkpoint_scenarios.py [viz ...]
import json
import os
import queue
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys", "/lf/visualizations/tests"]
import numpy as np  # noqa: E402

from lfviz import checkpoint, protocol, registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
from test_restore import SMALL  # noqa: E402

WALL = ("cpu_ms", "speed_actual", "lag")
HERE = Path(__file__).resolve().parent


def gpu_settings():
    """LF_GPU=1: every kernel with a GPU implementation on the GPU (as a run whose settings ask for it)."""
    if os.environ.get("LF_GPU") != "1":
        return
    from lfphys.core import backend
    notes = backend.configure({"kernels": {n: {"device": "gpu"} for n, k in backend.kernels().items() if k.gpu}})
    print("gpu settings:", backend.settings(), notes, file=sys.stderr)

# per visualization: (first live change, second live change, an action or None, slice planes?)
PLAN = {
    "v01_light_travel": (None, None, ("flash", {"obj": "earth"}), False),
    "v02_double_slit": ({"lam_nm": 500.0}, {"lam_nm": 700.0}, ("clear", {}), False),
    "v03_quantum_1d": ({"energy": 1.2}, {"sigma": 6.0}, ("clear", {}), False),
    "v04_orbits": ({"speed": 1.0}, {"angle": 10.0}, ("boost", {"dv": 0.05}), False),
    "v05_optics_bench": ({"theta_deg": 30.0}, {"pol": "s"}, ("emit_one", {}), False),
    "v06_qcd": ({"mu": 100.0}, {"kappa": 0.4}, None, False),
    "v07_bell_test": ({"b_deg": 30.0}, {"switch": "fixed"}, ("clear", {}), False),
    "v08_wave_3d": (None, None, None, True),
    "v09_thomas_3d": (None, None, None, True),
    "v10_fast_observer": ({"obs_beta": 0.5}, {"yaw": 30.0}, None, False),
    "v11_double_slit_2d": ({"slit_b": False}, {"mark_deg": 90.0}, None, False),
    "v12_arrival_times_2d": ({"slit_b": False}, {"slit_a": False}, None, False),
    "v13_hydrogen_3d": (None, None, None, True),
    "v14_quarkonium_3d": (None, None, None, True),
}


def make(viz_id, emit):
    viz = registry.load(viz_id)
    small = SMALL.get(viz_id, {})

    def make_world(preset, values, seed):
        p, errs = viz["schema"].resolve(preset, {**small, **(values or {})})
        if errs:
            raise ValueError("; ".join(errs))
        return viz["simulation"](p, 7 if seed in (None, "") else int(seed), emit), {"preset": preset}
    return viz, make_world


def ops_before(viz_id, sim):
    first, _, act, planes = PLAN[viz_id]
    d = 3.0 * sim.default_speed
    rng = np.random.default_rng(1)
    adv = lambda n: [{"adv": float(x)} for x in rng.uniform(0.02, 0.2, n) * d]  # noqa: E731
    ops = adv(6)
    if first:
        ops.append({"cmd": "set", "args": {"values": first}})
    ops += adv(4)
    if act:
        ops.append({"cmd": "action", "args": {"name": act[0], "args": act[1]}})
    ops += adv(3)
    if planes:
        ops.append({"cmd": "view", "args": {"op": "plane", "id": 2, "origin": None, "normal": [1.0, 0.0, 0.0]}})
    ops.append({"cmd": "step", "args": {"dt": 0.05 * d}})
    ops.append({"cmd": "next_event", "args": {}})
    ops += adv(2)
    return ops


def ops_after(viz_id, sim):
    _, second, act, planes = PLAN[viz_id]
    d = 3.0 * sim.default_speed
    rng = np.random.default_rng(2)
    adv = lambda n: [{"adv": float(x)} for x in rng.uniform(0.02, 0.2, n) * d]  # noqa: E731
    ops = adv(6)
    if second:
        ops.append({"cmd": "set", "args": {"values": second}})
    ops += adv(6)
    if planes:
        ops.append({"cmd": "view", "args": {"op": "remove", "id": 2}})
    ops.append({"cmd": "step", "args": {"dt": 0.05 * d}})
    ops.append({"cmd": "next_event", "args": {}})
    ops += adv(4)
    ops.append({"cmd": "new_world", "args": {"params": {}, "seed": 11}})
    ops += adv(4)
    return ops


def apply(run, ops):
    for o in ops:
        if "adv" in o:
            run._advance(run.sim.t + o["adv"])
            run._frame(0.0)
        else:
            args = dict(o["args"])
            if args.get("op") == "plane" and args.get("origin") is None:
                h = run.sim.header()[0]
                args["origin"] = h["scene3d"]["planes"]["center"]
            run.handle({"cmd": o["cmd"], "args": args})


def encode(msgs):
    return [protocol.encode({k: v for k, v in m.items() if k not in WALL}, b) for m, b in msgs]


def child(viz_id, file, ops_file, out):
    gpu_settings()
    msgs = []

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    viz, make_world = make(viz_id, emit)
    state = checkpoint.loads(Path(file).read_bytes(), emit)
    run = Runner(state["sim"], emit, queue.Queue(), make_world=make_world)
    run.restore_from(state, [], state["sim"].t, lambda on: None)
    apply(run, json.loads(Path(ops_file).read_text()))
    with open(out, "wb") as f:
        for b in encode(msgs):
            f.write(len(b).to_bytes(8, "little") + b)


def read(out):
    data, res, i = Path(out).read_bytes(), [], 0
    while i < len(data):
        n = int.from_bytes(data[i:i + 8], "little")
        res.append(data[i + 8:i + 8 + n])
        i += 8 + n
    return res


def describe(a, b):
    ma, ba = protocol.decode(a)
    mb, bb = protocol.decode(b)
    keys = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k))
    blobs = sorted(k for k in set(ba) | set(bb) if not (k in ba and k in bb and np.array_equal(ba[k], bb[k])))
    out = {"type": ma.get("type"), "id": ma.get("id"), "t": ma.get("t"), "meta_keys": keys[:8], "blobs": blobs[:8]}
    for k in keys[:3]:
        out[f"orig.{k}"] = json.dumps(ma.get(k), ensure_ascii=False, default=str)[:300]
        out[f"cont.{k}"] = json.dumps(mb.get(k), ensure_ascii=False, default=str)[:300]
    return out


def compare(x, y):
    if len(x) != len(y):
        n = min(len(x), len(y))
        first = next((i for i in range(n) if x[i] != y[i]), n)
        return {"same": False, "len": [len(x), len(y)], "first_diff": first,
                "at": describe(x[first], y[first]) if first < n else None}
    bad = [i for i in range(len(x)) if x[i] != y[i]]
    return {"same": not bad, "n": len(x), "n_diff": len(bad),
            "first": describe(x[bad[0]], y[bad[0]]) if bad else None}


def main(ids):
    gpu_settings()
    res = {}
    for viz_id in ids:
        msgs = []

        def emit(meta, blobs=None):
            msgs.append((meta, blobs))
        try:
            viz, make_world = make(viz_id, emit)
            sim, _ = make_world(None, {}, 7)
            run = Runner(sim, emit, queue.Queue(), make_world=make_world)
            run._start_world()
            apply(run, ops_before(viz_id, sim))
            tmp = Path(tempfile.mkdtemp())
            run.ckpt_dir, run.code = tmp / "ck", "c01"
            run.ckpt_dirty = True
            run.checkpoint("c01")
            ck = [m for m, _ in msgs if m.get("type") == "checkpoint"][-1]
            if ck.get("error"):
                res[viz_id] = {"checkpoint_error": ck["error"]}
                print(viz_id, res[viz_id], flush=True)
                continue
            file = tmp / "ck" / ck["file"]
            n0 = len(msgs)
            after = ops_after(viz_id, sim)
            apply(run, after)
            orig = encode(msgs[n0:])
            (tmp / "ops.json").write_text(json.dumps(after))
            conts = []
            for k in range(2):
                out = tmp / f"cont{k}.bin"
                r = subprocess.run([sys.executable, __file__, "--child", viz_id, str(file), str(tmp / "ops.json"),
                                    str(out)], capture_output=True, text=True, timeout=1800)
                if r.returncode:
                    raise RuntimeError(r.stderr[-2000:])
                conts.append(read(out))
            from lfphys.core import backend
            res[viz_id] = {"used": {k: (v.get("drawn") or {}).get("device") for k, v in backend.used().items()},
                           "checkpoint_bytes": ck["bytes"], "checkpoint_ms": ck["ms"],
                           "orig_vs_cont": compare(orig, conts[0]), "cont_vs_cont": compare(conts[0], conts[1]),
                           "types_after": sorted({m.get("type") for m, _ in msgs[n0:]})}
        except Exception as e:  # noqa: BLE001
            res[viz_id] = {"failed": f"{type(e).__name__}: {e}"[:3000]}
        print(viz_id, json.dumps(res[viz_id], ensure_ascii=False, default=str), flush=True)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(*sys.argv[2:6])
        sys.exit(0)
    ids = sys.argv[1:] or list(PLAN)
    r = main(ids)
    os.makedirs("/out", exist_ok=True)
    with open("/out/c01_checkpoint_scenarios%s.json" % ("_gpu" if os.environ.get("LF_GPU") == "1" else ""), "a") as f:
        f.write(json.dumps(r, ensure_ascii=False, default=str, indent=1) + "\n")
