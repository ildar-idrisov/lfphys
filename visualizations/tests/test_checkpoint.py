# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A run continues from its last state, not from a recomputation (owner, 2026-10-29: «для добавления записи последний
кадр должен быть достаточен для полного точного воспроизведения с последнего состояния в виде продолжения
эксперимента, а не нового запуска»). For every visualization: a world advanced in irregular frame steps writes a
checkpoint (``lfviz.checkpoint``); a new process loads it and goes on in the same steps as the original, and every
message it emits is the original's, byte for byte (apart from the runner's wall-clock fields). Also: a checkpoint
followed by more record (the worker crashed later) is continued by repeating only that tail; a live change in the
tail is applied at its time."""

import json
import math
import queue
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from lfviz import checkpoint, protocol, registry
from lfviz.sim import Runner

from test_restore import SMALL

WALL = ("cpu_ms", "speed_actual", "lag")  # the runner's measurements of wall time, not the world's


def _world(viz_id, msgs):
    viz = registry.load(viz_id)
    params, errors = viz["schema"].resolve(None, SMALL.get(viz_id, {}))
    assert not errors, errors

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    sim = viz["simulation"](params, 7, emit)
    return sim, Runner(sim, emit, queue.Queue())


def _bytes(msgs):
    """The messages as the record would hold them, without the runner's wall-clock fields."""
    return [protocol.encode({k: v for k, v in m.items() if k not in WALL}, b) for m, b in msgs]


def _steps(sim, k0, n):
    """Irregular frame steps (as a frame clock under load makes them): the times of frames k0 .. k0 + n - 1."""
    rng = np.random.default_rng(1)
    dts = rng.uniform(0.02, 0.2, k0 + n) * 3.0 * sim.default_speed
    return list(np.cumsum(dts)[k0:])


def _play(run, times):
    for t in times:
        run._advance(t)
        run._frame(0.0)


CHILD = """
import json, queue, sys
sys.path[:0] = {paths}
from lfviz import checkpoint, protocol
from lfviz.sim import Runner
msgs, muted = [], [False]  # the worker's output while the tail of the record is repeated is silenced, as in a worker
def emit(meta, blobs=None):
    if not muted[0]:
        msgs.append((meta, blobs))
state = checkpoint.loads(open({file!r}, "rb").read(), emit)
run = Runner(state["sim"], emit, queue.Queue())
run.restore_from(state, json.loads({script!r}), {t_end!r}, lambda on: muted.__setitem__(0, on))
for t in json.loads({times!r}):
    run._advance(t)
    run._frame(0.0)
with open({out!r}, "wb") as f:
    for meta, blobs in msgs:
        b = protocol.encode({{k: v for k, v in meta.items() if k not in ("cpu_ms", "speed_actual", "lag")}}, blobs)
        f.write(len(b).to_bytes(8, "little") + b)
"""


def _continue_in_new_process(tmp_path, file, script, t_end, times):
    """Load the checkpoint in a new Python process (as a resumed worker does) and go on: its messages, encoded."""
    out = tmp_path / "child.bin"
    code = CHILD.format(paths=repr(list(sys.path)), file=str(file), script=json.dumps(script), t_end=float(t_end),
                        times=json.dumps([float(t) for t in times]), out=str(out))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-4000:]
    data, res, i = out.read_bytes(), [], 0
    while i < len(data):
        n = int.from_bytes(data[i:i + 8], "little")
        res.append(data[i + 8:i + 8 + n])
        i += 8 + n
    return res


def _checkpoint(run, tmp_path):
    run.ckpt_dir = tmp_path / "ck"
    run.checkpoint("test")
    run.ckpt_writer.wait()  # the file is written in the background
    files = sorted(run.ckpt_dir.glob("*.pkl"))
    assert files, "no checkpoint written"
    return files[-1]


@pytest.mark.parametrize("viz_id", registry.viz_ids())
def test_a_world_continued_from_its_checkpoint_emits_what_the_original_emits(viz_id, tmp_path):
    msgs = []
    sim, run = _world(viz_id, msgs)
    run._start_world()
    _play(run, _steps(sim, 0, 12))
    file = _checkpoint(run, tmp_path)
    ck = [m for m, _ in msgs if m.get("type") == "checkpoint"][-1]
    assert not ck.get("error") and ck["file"] == file.name and ck["world"] == 1 and ck["t"] == sim.t, ck
    n0 = len(msgs)
    times = _steps(sim, 12, 6)
    _play(run, times)
    original = _bytes(msgs[n0:])
    continued = _continue_in_new_process(tmp_path, file, [], ck["t"], times)
    assert len(continued) == len(original), ([m["type"] for m, _ in msgs[n0:]], len(continued))
    for i, (a, b) in enumerate(zip(original, continued)):
        assert a == b, (viz_id, i, protocol.decode(a)[0].get("type"), _diff(a, b))


def _diff(a, b):
    ma, ba = protocol.decode(a)
    mb, bb = protocol.decode(b)
    keys = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k))
    blobs = sorted(k for k in set(ba) | set(bb) if not (k in ba and k in bb and np.array_equal(ba[k], bb[k])))
    return {"meta": keys[:8], "blobs": blobs[:8]}


def test_a_checkpoint_followed_by_more_record_is_continued_by_repeating_only_the_tail(tmp_path):
    """The worker crashed after its periodic checkpoint: the record holds frames and a live change after it. The new
    worker loads the checkpoint, repeats only that tail (silently) and goes on as the original does."""
    msgs = []
    sim, run = _world("r12_double_slit_2d", msgs)
    run._start_world()
    _play(run, _steps(sim, 0, 8))
    file = _checkpoint(run, tmp_path)
    t_ck = sim.t
    n_ck = len(msgs)
    _play(run, _steps(sim, 8, 3))
    run.handle({"cmd": "set", "args": {"values": {"slit_b": False}}})
    _play(run, _steps(sim, 11, 3))
    tail = [{"frame": m["t"]} if m["type"] == "frame" else {"t": m["t"], "cmd": m["cmd"], "args": m["args"]}
            for m, _ in msgs[n_ck:] if m["type"] in ("frame", "command")]
    assert any("cmd" in c for c in tail) and sim.t > t_ck
    t_end = sim.t
    n0 = len(msgs)
    times = _steps(sim, 14, 5)
    _play(run, times)
    original = _bytes(msgs[n0:])
    continued = _continue_in_new_process(tmp_path, file, tail, t_end, times)
    assert continued == original


def test_a_world_without_changes_writes_no_new_checkpoint_and_files_are_kept_to_two(tmp_path):
    msgs = []
    sim, run = _world("u31_light_travel", msgs)
    run._start_world()
    run.ckpt_dir = tmp_path / "ck"
    for k in range(4):
        _play(run, [sim.t + sim.default_speed])
        run.checkpoint("test")
        run.ckpt_writer.wait()
    n = sum(1 for m, _ in msgs if m.get("type") == "checkpoint")
    run.checkpoint("test")  # nothing changed since the last one
    run.ckpt_writer.wait()
    assert sum(1 for m, _ in msgs if m.get("type") == "checkpoint") == n == 4
    assert len(list(run.ckpt_dir.glob("*.pkl"))) == checkpoint.KEEP


def test_a_checkpoint_of_another_version_is_refused():
    with pytest.raises(ValueError):
        checkpoint.loads(checkpoint.dumps({"sim": None}, None).replace(b"version", b"versioN"), None)
    assert math.isfinite(1.0)


def test_negative_control_a_state_without_its_random_generator_continues_differently(tmp_path):
    """The comparison above can fail: the same checkpoint with the world's random generator re-seeded (a state that
    lost one piece) goes on differently (u32: the particles drawn after it)."""
    msgs = []
    sim, run = _world("u32_double_slit", msgs)
    run._start_world()
    _play(run, _steps(sim, 0, 12))
    file = _checkpoint(run, tmp_path)
    n0 = len(msgs)
    times = _steps(sim, 12, 6)
    _play(run, times)
    original = _bytes(msgs[n0:])
    msgs2 = []
    state = checkpoint.loads(file.read_bytes(), lambda m, b=None: msgs2.append((m, b)))
    state["sim"].rng = np.random.default_rng(7)
    run2 = Runner(state["sim"], state["sim"].emit, queue.Queue())
    run2.restore_from(state, [], state["sim"].t, lambda on: None)
    _play(run2, times)
    assert _bytes(msgs2) != original


# --- the review's scenario (2026-10-29, record-checkpoints-keyframes, CK-6): what a session does around a checkpoint ---
# per visualization: (a live change before the checkpoint, one after, an action or None, a slice plane added before and
# removed after); then step and next_event, and a new world on each side of the checkpoint (its header carries its
# number)
PLAN = {
    "s03_projectile": (None, None, None, False),  # no live parameters and no actions (EX1, 2026-11-14)
    "u31_light_travel": (None, None, ("flash", {"obj": "earth"}), False),
    # u32: the change after the checkpoint turns on the vector screen (a perfectly conducting screen, B8): the continued
    # world computes it in the new process (a checkpoint of a vector world: u32's own tests)
    "u32_double_slit": ({"lam_nm": 500.0}, {"screen_model": "pec", "screen_t_um": 0.2, "a_um": 1.0, "d_um": 5.0,
                                            "L2_m": 0.02}, ("clear", {}), False),
    "u33_quantum_1d": ({"energy": 1.2}, {"sigma": 6.0}, ("clear", {}), False),
    "u34_orbits": ({"speed": 1.0}, {"angle": 10.0}, ("boost", {"dv": 0.05}), False),
    "u35_optics_bench": ({"theta_deg": 30.0}, {"pol": "s"}, ("emit_one", {}), False),
    "u36_qcd": ({"mu": 100.0}, {"kappa": 0.4}, None, False),
    "u37_bell_test": ({"b_deg": 30.0}, {"switch": "fixed"}, ("clear", {}), False),
    "u38_wave_3d": (None, None, None, True),
    "r11_thomas_3d": (None, None, None, True),
    "u39_fast_observer": ({"obs_beta": 0.5}, {"yaw": 30.0}, None, False),
    "r12_double_slit_2d": ({"slit_b": False}, {"mark_deg": 90.0}, None, False),
    "r13_arrival_times_2d": ({"slit_b": False}, {"slit_a": False}, None, False),
    "u40_hydrogen_3d": (None, None, None, True),
    "u41_quarkonium_3d": (None, None, None, True),
    "u42_kerr_shadow": ({"incl": 40.0}, {"retro": True}, None, False),
    "u43_optical_vortices": ({"f_rot": 6.0}, {"f_rot": 3.0}, None, True),
    "u44_mie_scattering": ({"lam_nm": 480.0}, {"light": "mono"}, None, True),
    "p01_gravity": (None, None, None, False),
    "p02_quantum": (None, None, ("measure", {"particle": "o3", "sigma": 2.5}), False),
    "p04_fluids": (None, None, None, False),
    "p03_molecules": (None, None, None, False),
}


def _session(viz_id, sim, before):
    """The operations of a session before (or after) the checkpoint: frames in irregular steps between commands."""
    first, second, act, planes = PLAN[viz_id]
    d = 3.0 * sim.default_speed
    rng = np.random.default_rng(1 if before else 2)
    adv = lambda n: [{"adv": float(x)} for x in rng.uniform(0.02, 0.2, n) * d]  # noqa: E731
    ops = adv(5)
    change = first if before else second
    if change:
        ops.append({"cmd": "set", "args": {"values": change}})
    ops += adv(3)
    if act:
        ops.append({"cmd": "action", "args": {"name": act[0], "args": act[1]}})
    if planes:
        ops.append({"cmd": "view", "args": {"op": "plane", "id": 2, "normal": [1.0, 0.0, 0.0]} if before
                    else {"op": "remove", "id": 2}})
    ops.append({"cmd": "step", "args": {"dt": 0.05 * d}})
    ops.append({"cmd": "next_event", "args": {}})
    ops += adv(3)
    # a new world on each side: the checkpoint is of world 2, the world after it must be number 3
    ops.append({"cmd": "new_world", "args": {"params": {}, "seed": 5 if before else 11}})
    ops += adv(3)
    return ops


SESSION_CHILD = """
import json, queue, sys
sys.path[:0] = {paths}
from lfviz import checkpoint, protocol, registry
from lfviz.sim import Runner
from test_checkpoint import _apply, _maker
msgs, muted = [], [False]
def emit(meta, blobs=None):
    if not muted[0]:
        msgs.append((meta, blobs))
state = checkpoint.loads(open({file!r}, "rb").read(), emit)
run = Runner(state["sim"], emit, queue.Queue(), make_world=_maker({viz!r}, emit))
run.restore_from(state, [], state["sim"].t, lambda on: muted.__setitem__(0, on))
_apply(run, json.loads({ops!r}))
with open({out!r}, "wb") as f:
    for meta, blobs in msgs:
        b = protocol.encode({{k: v for k, v in meta.items() if k not in ("cpu_ms", "speed_actual", "lag")}}, blobs)
        f.write(len(b).to_bytes(8, "little") + b)
"""


def _maker(viz_id, emit):
    viz = registry.load(viz_id)

    def make_world(preset, values, seed):
        p, errs = viz["schema"].resolve(preset, {**SMALL.get(viz_id, {}), **(values or {})})
        if errs:
            raise ValueError("; ".join(errs))
        return viz["simulation"](p, 7 if seed in (None, "") else int(seed), emit), {"preset": preset}
    return make_world


def _apply(run, ops):
    for o in ops:
        if "adv" in o:
            run._advance(run.sim.t + o["adv"])
            run._frame(0.0)
        else:
            args = dict(o["args"])
            if args.get("op") == "plane":
                args["origin"] = run.sim.header()[0]["scene3d"]["planes"]["center"]
            run.handle({"cmd": o["cmd"], "args": args})


@pytest.mark.parametrize("viz_id", registry.viz_ids())
def test_a_session_around_a_checkpoint_continues_as_the_original(viz_id, tmp_path):
    """Live changes, an action, a slice plane, step, next_event and a new world before the checkpoint (so it is of
    world 2); the same kinds after it, with a new world 3: the world continued from the checkpoint in a new process
    emits the original's bytes (review CK-6; a checkpoint that lost the world's number would give the new world the
    wrong one: the negative control "world": 1 fails here)."""
    msgs = []

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    make_world = _maker(viz_id, emit)
    sim, _ = make_world(None, {}, 7)
    run = Runner(sim, emit, queue.Queue(), make_world=make_world)
    run._start_world()
    _apply(run, _session(viz_id, sim, True))
    file = _checkpoint(run, tmp_path)
    n0 = len(msgs)
    after = _session(viz_id, sim, False)
    _apply(run, after)
    original = _bytes(msgs[n0:])
    assert any(m.get("type") == "header" and m.get("world") == 3 for m, _ in msgs[n0:])
    out = tmp_path / "session.bin"
    code = SESSION_CHILD.format(paths=repr(list(sys.path)), file=str(file), viz=viz_id, ops=json.dumps(after),
                                out=str(out))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=900,
                       cwd=str(Path(__file__).parent))
    assert r.returncode == 0, r.stderr[-4000:]
    data, cont, i = out.read_bytes(), [], 0
    while i < len(data):
        n = int.from_bytes(data[i:i + 8], "little")
        cont.append(data[i + 8:i + 8 + n])
        i += 8 + n
    assert len(cont) == len(original)
    for k, (a, b) in enumerate(zip(original, cont)):
        assert a == b, (viz_id, k, protocol.decode(a)[0].get("type"), _diff(a, b))


FILES_CHILD = """
import json, queue, sys
sys.path[:0] = {paths}
from lfviz import checkpoint
from test_checkpoint import _play, _steps, _world, _checkpoint
from pathlib import Path
msgs = []
sim, run = _world("r13_arrival_times_2d", msgs)
run._start_world()
_play(run, _steps(sim, 0, 3))
_checkpoint(run, Path({tmp!r}))
ck = [m for m, _ in msgs if m.get("type") == "checkpoint"][-1]
print(json.dumps({{"files": ck["files"], "code": ck["code"], "env": ck["env"]}}))
"""


def test_a_checkpoint_records_the_code_it_ran_and_its_runtime(tmp_path):
    """Review CK-5: the files of the modules a world's worker runs (r13's include r12's; not an engine module it never
    imports, not the view's JS), their hash and the runtime; an edit of one of them changes the hash. Run in a fresh
    process, as a worker is."""
    r = subprocess.run([sys.executable, "-c", FILES_CHILD.format(paths=repr(list(sys.path)), tmp=str(tmp_path))],
                       capture_output=True, text=True, timeout=600, cwd=str(Path(__file__).parent))
    assert r.returncode == 0, r.stderr[-4000:]
    ck = json.loads(r.stdout.strip().splitlines()[-1])
    files = ck["files"]
    assert "visualizations/r12_double_slit_2d/viz.py" in files and "visualizations/server/lfviz/sim.py" in files
    assert not any(f.endswith(".js") for f in files) and "lfphys/lfphys/core/quantum/open_systems.py" not in files
    assert ck["env"] == checkpoint.runtime_env() and ck["env"]["magic"]
    root = Path(__file__).resolve().parents[2]
    assert checkpoint.files_hash(root, files) == ck["code"]
    copy = tmp_path / "root"
    for f in files:
        (copy / f).parent.mkdir(parents=True, exist_ok=True)
        (copy / f).write_bytes((root / f).read_bytes())
    assert checkpoint.files_hash(copy, files) == ck["code"]
    (copy / "visualizations/r12_double_slit_2d/viz.py").write_text("# edited\\n")
    assert checkpoint.files_hash(copy, files) != ck["code"]
    (copy / "visualizations/r12_double_slit_2d/viz.py").unlink()
    assert checkpoint.files_hash(copy, files) is None
    with pytest.raises(ValueError):
        checkpoint.write(tmp_path, "../escape.pkl", b"x")


def test_shared_buffers_in_a_worlds_state_are_known():
    """Review CK-15: pickling makes two attributes that view one buffer two arrays. No world writes into such a pair in
    place today (the continuation tests above); this lists the pairs, so that a new one is looked at."""
    known = {"r12_double_slit_2d", "r13_arrival_times_2d"}
    for viz_id in registry.viz_ids():
        sim, run = _world(viz_id, [])
        arrays = []

        def walk(o, depth=0, seen=set()):
            if id(o) in seen or depth > 4:
                return
            seen.add(id(o))
            if isinstance(o, np.ndarray):
                arrays.append(o)
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v, depth + 1, seen)
            elif isinstance(o, (list, tuple)):
                for v in o[:50]:
                    walk(v, depth + 1, seen)
            elif hasattr(o, "__dict__") and not isinstance(o, type):
                for v in vars(o).values():
                    walk(v, depth + 1, seen)
        walk(sim)
        shared = any(a is not b and a.size and b.size and np.shares_memory(a, b)
                     for k, a in enumerate(arrays[:400]) for b in arrays[k + 1:400])
        assert not shared or viz_id in known, f"{viz_id}: arrays sharing memory in its state (RULES §3)"
