# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A run can always be continued (owner, 2026-10-28): a suspended world is rebuilt from its parameters and seed by
repeating its record — every frame's advance and every command, in order (``Runner.restore``). For every
visualization: a world advanced in irregular frame steps, against the same world rebuilt from the script of its
record — the frames at the end of the record agree (also for the particle sources, whose random draws depend on how
time is split into frames: the script repeats the very same advances), and so do they after both go on in the same
steps; a world with a live change is restored through it."""

import math
import queue

import numpy as np
import pytest

from lfviz import registry
from lfviz.sim import Runner

SMALL = {  # worlds that are heavy at their defaults: the geometries of their own tests
    "v08_wave_3d": {"n": 128, "zmax": 10.0},
    "v09_thomas_3d": {"ngrid": 48},
    "v11_double_slit_2d": {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse",
                           "n_bohm": 100, "n_tracks": 10},
    "v12_arrival_times_2d": {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0},
    "v17_mie_scattering": {"radius_um": 1.0, "width": 0.05, "n_lam": 8},
    # playgrounds start empty: a scene with something in it (a preset's)
    "p01_gravity": dict(registry.load("p01_gravity")["schema"].presets["hole_stars"]["params"]),
    "p02_quantum": {**registry.load("p02_quantum")["schema"].presets["tunnel"]["params"], "n2": "192"},
    "p04_fluids": dict(registry.load("p04_fluids")["schema"].presets["cavity"]["params"], nx="128"),
    "p03_molecules": dict(registry.load("p03_molecules")["schema"].presets["piston"]["params"]),
}


def _world(viz_id, values=None):
    viz = registry.load(viz_id)
    params, errors = viz["schema"].resolve(None, {**SMALL.get(viz_id, {}), **(values or {})})
    assert not errors, errors
    frames, script = [], []  # the frames drawn; the record's script (frame times and commands, as the server keeps)

    def emit(meta, blobs=None):
        if meta.get("type") == "frame":
            frames.append((meta, blobs))
            script.append({"frame": meta["t"]})
        elif meta.get("type") == "command":
            script.append({"t": meta["t"], "cmd": meta["cmd"], "args": meta["args"]})
    sim = viz["simulation"](params, 7, emit)
    return sim, Runner(sim, emit, queue.Queue()), frames, script


def _same(a, b, path=""):
    if isinstance(a, dict):
        assert set(a) == set(b), (path, set(a) ^ set(b))
        for k in a:
            if k in ("cpu_ms", "speed_actual", "lag"):
                continue
            _same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _same(x, y, f"{path}[{i}]")
    elif isinstance(a, np.ndarray):
        assert a.shape == b.shape, path
        if a.dtype.kind in "fc":
            assert np.allclose(a, b, rtol=1e-9, atol=1e-12, equal_nan=True), (path, np.nanmax(np.abs(a - b)))
        else:
            assert np.array_equal(a, b), path
    elif isinstance(a, float):
        assert (math.isnan(a) and math.isnan(b)) or abs(a - b) <= 1e-9 * max(1.0, abs(a)), (path, a, b)
    else:
        assert a == b, (path, a, b)


@pytest.mark.parametrize("viz_id", registry.viz_ids())
def test_a_world_restored_by_replay_continues_as_the_original(viz_id):
    sim, run, frames, script = _world(viz_id)
    run._start_world()
    span = 3.0 * sim.default_speed  # three wall seconds of the default speed
    rng = np.random.default_rng(1)
    t = 0.0
    while t < span:  # irregular frame steps, as a frame clock under load would make them
        t = min(span, t + span * rng.uniform(0.02, 0.2))
        run._advance(t)
        run._frame(0.0)
    sim2, run2, frames2, _ = _world(viz_id)
    muted = [False]
    run2.restore(1, list(script), sim.t, lambda on: muted.__setitem__(0, on))
    run2._frame(0.0)
    _same(frames[-1][0], frames2[-1][0])
    _same(frames[-1][1] or {}, frames2[-1][1] or {})
    for k in range(3):  # both go on in the same steps (a continued run is the record's world going on)
        run._advance(span + (k + 1) * span / 3)
        run2._advance(span + (k + 1) * span / 3)
    run._frame(0.0)
    run2._frame(0.0)
    _same(frames[-1][0], frames2[-1][0])
    _same(frames[-1][1] or {}, frames2[-1][1] or {})


def test_restore_replays_live_changes_at_their_times():
    """v11: slit B closed while the packet flies, then the world rebuilt: the same frames after the change."""
    sim, run, frames, script = _world("v11_double_slit_2d")
    run._start_world()
    span = 3.0 * sim.default_speed
    run._advance(0.4 * span)
    run._frame(0.0)
    run.handle({"cmd": "set", "args": {"values": {"slit_b": False}}})
    run._advance(span)
    run._frame(0.0)
    assert any(c.get("cmd") == "set" for c in script)
    sim2, run2, frames2, _ = _world("v11_double_slit_2d")
    run2.restore(1, list(script)[:-1], sim.t, lambda on: None)
    assert sim2.live["slit_b"] is False
    run2._frame(0.0)
    _same(frames[-1][0], frames2[-1][0])
    _same(frames[-1][1] or {}, frames2[-1][1] or {})


def test_a_command_after_a_step_in_one_batch_is_replayed_at_its_time():
    """Review C1-4: a paused world handles a ``step`` and a queued ``set`` in one batch: the ``set`` is recorded at the
    time after the step with no frame between them; the restore advances to the command's recorded time first."""
    sim, run, frames, script = _world("v11_double_slit_2d")
    run._start_world()
    sp = sim.default_speed
    for t in (2 * sp, 4 * sp):
        run._advance(t)
        run._frame(0.0)
    run.handle({"cmd": "step", "args": {"dt": 3 * sp}})
    run.handle({"cmd": "set", "args": {"values": {"slit_b": False}}})
    run._frame(0.0)
    t_end = sim.t
    assert [c for c in script if "cmd" in c][-1]["t"] == t_end
    sim2, run2, frames2, _ = _world("v11_double_slit_2d")
    run2.restore(1, list(script), t_end, lambda on: None)
    for k in (1, 2, 3):
        run._advance(t_end + k * sp)
        run2._advance(t_end + k * sp)
    run._frame(0.0)
    run2._frame(0.0)
    _same(frames[-1][0], frames2[-1][0])
    _same(frames[-1][1] or {}, frames2[-1][1] or {})


def test_a_later_world_restored_keeps_the_planes_it_took_over():
    """Review C1-5: world 2 of a run took over the slice planes placed in world 1 (``adopt_view``); its header carries
    them and its restore takes them over again, so the rebuilt world 2 has the planes it had and goes on the same."""
    viz = registry.load("v08_wave_3d")
    params, _ = viz["schema"].resolve(None, SMALL["v08_wave_3d"])
    msgs = []

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))

    sim = viz["simulation"](params, 7, emit)
    run = Runner(sim, emit, queue.Queue(),
                 make_world=lambda preset, values, seed: (viz["simulation"](
                     viz["schema"].resolve(preset, values or {})[0], 7 if seed is None else seed, emit), {}))
    run._start_world()
    sp = sim.default_speed
    run._advance(sp)
    run._frame(0.0)
    run.handle({"cmd": "view", "args": {"op": "plane", "id": 1, "origin": [0, 0, 5], "normal": [0.5, 0.0, 0.866]}})
    run.handle({"cmd": "view", "args": {"op": "plane", "id": 2, "origin": [0, 0, 5], "normal": [0.0, 1.0, 0.0]}})
    run._advance(2 * sp)
    run._frame(0.0)
    run.handle({"cmd": "new_world", "args": {"params": dict(SMALL["v08_wave_3d"])}})
    head = max(i for i, (m, _) in enumerate(msgs) if m.get("type") == "header")
    header = msgs[head][0]
    assert header["world"] == 2 and len(header["adopted_view"]) == 2
    for t in (sp, 2 * sp):
        run._advance(t)
        run._frame(0.0)
    script = [{"frame": m["t"]} if m["type"] == "frame" else {"t": m["t"], "cmd": m["cmd"], "args": m["args"]}
              for m, _ in msgs[head + 1:] if m["type"] in ("frame", "command")]
    planes = {k: (list(v["origin"]), list(v["normal"])) for k, v in run.sim.planes.items()}
    msgs2 = []
    sim2 = viz["simulation"](viz["schema"].resolve(None, header["params"])[0], header["seed"],
                             lambda m, b=None: msgs2.append((m, b)))
    run2 = Runner(sim2, sim2.emit, queue.Queue())
    run2.restore(2, script, run.sim.t, lambda on: None, header.get("adopted_view"))
    assert {k: (list(v["origin"]), list(v["normal"])) for k, v in sim2.planes.items()} == planes
    n0 = len(msgs)
    run._advance(3 * sp)
    run._frame(0.0)
    run2._advance(3 * sp)
    run2._frame(0.0)
    a, b = msgs[n0:], msgs2[-(len(msgs) - n0):]
    assert [m["type"] for m, _ in a] == [m["type"] for m, _ in b]
    for (ma, ba), (mb, bb) in zip(a, b):
        _same(ma, mb)
        _same(ba or {}, bb or {})
