# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The headless runner (``lfviz.headless.run_spec``; design ``lfphys/sources/explore_2026-11-14_design.md`` §1.2, §8):

* the site's recorder, now built on it, gives byte for byte what the recorder before it gave (``_legacy_record`` below
  is a frozen copy of ``site/record.py``'s ``record()`` of 2026-11-13) for the specs of ``tests/test_recorder.py``'s
  worlds, with and without a script;
* the stop rules: ``world_s`` (the last frame at that time), ``event`` with ``after_s`` (the last frame that long after
  the event), ``max_world_s`` reached first fails; frames at the multiples of ``frame_dt``;
* a refusal of ``check_params`` is ``PointRefused`` (not a failure), a schema's refusal a ``ValueError``; an error
  message or a check ending ✗ fails;
* captions land at their frames with the frame's world time, and a script's ``speed`` changes the frames' spacing;
* the packer: dropped types and frame blobs, the header delta merged back equals the full header.
"""

from __future__ import annotations

import gzip
import importlib.util
import queue
import sys
import time

import numpy as np
import pytest

from lfviz import headless, limits, protocol, registry
from lfviz.i18n import join, render_in
from lfviz.sim import Runner

VIZ = registry.ROOT
SITE_WORLDS = VIZ / "tests" / "site_worlds"


def _site(name):
    if f"lfsite_{name}" in sys.modules:
        return sys.modules[f"lfsite_{name}"]
    spec = importlib.util.spec_from_file_location(f"lfsite_{name}", VIZ / "site" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _extra(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(SITE_WORLDS))


# --- the recorder before run_spec (site/record.py, 2026-11-13), frozen: the reference of the bytes ------------------
_DROP = {"checkpoint", "command", "resumed", "record_segment", "busy", "scene_export"}
_TIMING = ("cpu_ms", "speed_actual")


def _legacy_record(viz_id: str, spec: dict) -> list:
    viz = registry.load(viz_id)
    fps = int(spec["fps"])
    n = int(round(float(spec["seconds"]) * fps))
    seed = int(spec.get("seed") if spec.get("seed") is not None else 1)
    msgs = []

    def emit(meta, blobs=None):
        typ = meta.get("type")
        if typ in _DROP:
            return
        if typ == "frame":
            meta = {k: v for k, v in meta.items() if k not in _TIMING}
        msgs.append((typ, protocol.encode(meta, blobs)))

    from lfphys.core import backend as _backend
    _backend.reset_used()
    notes = _backend.configure({})

    def make_world(pr, values, sd):
        p, errs = viz["schema"].resolve(pr, values or {})
        if errs:
            raise ValueError(join(errs, "; "))
        limits.check_estimate(viz["simulation"], p)
        return viz["simulation"](p, seed if sd in (None, "") else int(sd), emit), {"preset": pr}

    params, errs = viz["schema"].resolve(spec["preset"], {})
    assert not errs, [render_in(e) for e in errs]
    limits.check_estimate(viz["simulation"], params)
    sim = viz["simulation"](params, seed, emit)
    runner = Runner(sim, emit, queue.Queue(), fps=float(fps), make_world=make_world,
                    world_info={"preset": spec["preset"], "backend_notes": notes})
    assert runner.start()
    runner._state("start")
    if spec.get("speed") is not None:
        runner.handle({"cmd": "speed", "args": {"value": float(spec["speed"])}})
    runner.handle({"cmd": "play"})
    script = {}
    for c in spec.get("script") or []:
        script.setdefault(min(n - 1, int(round(float(c["at"]) * fps))), []).append(c)
    for k in range(n):
        if k:
            runner._advance(runner.sim.t + runner.speed / fps)
        for c in script.get(k, []):
            runner.handle({"cmd": c["cmd"], "args": dict(c.get("args") or {})})
        runner._frame(0.0)
    emit({"type": "end", "t": runner.sim.t, "reason": "recording"})
    return msgs


SPECS = [("u98_site_toy", "slow"), ("u98_site_toy", "fast"), ("r98_site_probe", "only"), ("s98_atlas_toy", "field")]


@pytest.mark.parametrize("vid,rid", SPECS)
def test_the_recorder_on_run_spec_gives_the_bytes_of_the_recorder_before_it(vid, rid):
    rec = _site("record")
    spec = next(r for r in registry.recordings_of(registry.load(vid)) if r["id"] == rid)
    raw = rec.record(vid, spec)
    legacy_msgs = _legacy_record(vid, spec)
    assert [(t, d) for t, _tt, d in raw.msgs] == legacy_msgs
    full = rec.pack(raw, 1)
    legacy = protocol.MAGIC + b"".join(protocol.frame_stream_item(d) for _t, d in legacy_msgs)
    assert full.data == legacy and full.gz == gzip.compress(legacy, compresslevel=9, mtime=0)


def _run(vid, values, stop, clock=None, **kw):
    msgs = []
    oc = headless.run_spec(vid, kw.pop("base", "field"), values, 1, clock or {"frame_dt": 0.05}, stop,
                           emit=lambda m, b=None: msgs.append((m, b)), end_reason="atlas", **kw)
    return msgs, oc


def _frames_t(msgs):
    return [m["t"] for m, _b in msgs if m["type"] == "frame"]


def test_the_stop_rules():
    msgs, oc = _run("s98_atlas_toy", {}, {"world_s": 0.33})
    ts = _frames_t(msgs)
    assert ts[0] == 0.0 and ts[-1] == pytest.approx(0.33, abs=1e-12) and oc.frames == len(ts) == 8
    assert all(abs(b - k * 0.05) < 1e-12 for k, b in enumerate(ts[:-1]))
    assert msgs[-1][0] == {**msgs[-1][0], "type": "end", "reason": "atlas"}
    T = (2 * 1.0 / 9.80665) ** 0.5  # the toy's landing time from 1 m, thrown horizontally
    msgs, oc = _run("s98_atlas_toy", {}, {"event": "landing", "after_s": 0.12, "max_world_s": 5})
    ts = _frames_t(msgs)
    assert oc.stop_event_t == pytest.approx(T, rel=1e-12)
    assert ts[-1] == pytest.approx(T + 0.12, abs=1e-12) and ts[-2] < T + 0.12
    assert [m["t"] for m, _b in msgs if m["type"] == "event" and m["kind"] == "landing"] == [pytest.approx(T)]
    with pytest.raises(headless.RunFailed, match="max_world_s"):
        _run("s98_atlas_toy", {}, {"event": "landing", "after_s": 0.1, "max_world_s": 0.2})
    with pytest.raises(headless.RunFailed, match="max_world_s"):
        _run("s98_atlas_toy", {}, {"event": "nothing", "after_s": 0.1, "max_world_s": 1.0})


def test_refusals_and_failures():
    with pytest.raises(headless.PointRefused) as e:
        _run("s98_atlas_toy", {"h_m": 0.0, "angle_deg": 0.0}, {"world_s": 1})
    assert e.value.text["$t"].startswith("The ball starts on the ground") and e.value.hint["$t"]
    with pytest.raises(ValueError):
        _run("s98_atlas_toy", {"h_m": 99.0}, {"world_s": 1})
    sim = registry.load("s98_atlas_toy")["simulation"]
    orig = sim.frame

    def bad_check(self):
        self.emit({"type": "check", "t": self.t, "id": "c", "label": "c", "value": 1, "ref": 2, "rel": -0.5,
                   "tol": 1e-9, "unit": "", "group": "", "note": ""})
        return orig(self)
    sim.frame = bad_check
    try:
        with pytest.raises(headless.RunFailed, match="check"):
            _run("s98_atlas_toy", {}, {"world_s": 0.1})
    finally:
        sim.frame = orig

    def error(self):
        self.emit({"type": "error", "t": self.t, "text": "broken"})
        return orig(self)
    sim.frame = error
    try:
        with pytest.raises(headless.RunFailed, match="error"):
            _run("s98_atlas_toy", {}, {"world_s": 0.1})
    finally:
        sim.frame = orig


def test_captions_and_the_scripts_speed():
    spec = next(r for r in registry.recordings_of(registry.load("s98_atlas_toy")) if r["id"] == "story")
    msgs, oc = _run("s98_atlas_toy", {}, {"seconds": spec["seconds"]}, clock={"fps": spec["fps"], "speed": spec["speed"]},
                    base=spec["preset"], script=spec["script"], captions=spec["captions"])
    assert oc.frames == 60 and oc.worlds == 2
    caps = [m for m, _b in msgs if m["type"] == "caption"]
    assert [c["n"] for c in caps] == [0, 1, 2] and [c["at"] for c in caps] == [0.0, 1.5, 3.0]
    assert caps[1]["hold"] == 1.0 and "hold" not in caps[0]
    frames = [m for m, _b in msgs if m["type"] in ("frame", "caption", "header")]
    for c in caps:  # each caption comes right before the frame of its time
        i = frames.index(c)
        assert frames[i + 1]["type"] == "frame" and frames[i + 1]["t"] == c["t"]
    ts = _frames_t(msgs)  # 0.25 / 10 s per frame, a new world at 3 s (its default speed), 0.5 / 10 s from 4.5 s
    assert ts[1] - ts[0] == pytest.approx(0.025) and ts[-1] - ts[-2] == pytest.approx(0.05)


def test_the_packer_drops_quantises_and_the_header_delta_merges_back():
    spec = next(a for a in registry.atlases_of(registry.load("s98_atlas_toy")) if a["id"] == "explore")
    atlas = _site("atlas")
    m0, _oc = atlas.run_point("s98_atlas_toy", spec, atlas.defaults(spec))
    base = atlas.base_header(spec, m0)
    msgs, _oc = atlas.run_point("s98_atlas_toy", spec, {"h_m": 1.0, "angle_deg": 60.0})
    data, pk = atlas.pack_point(spec, msgs, base)
    out = headless.read_stream(data)
    assert not [m for m, _b in out if m["type"] == "story"] and [m for m, _b in msgs if m["type"] == "story"]
    assert all("ghost" not in b for m, b in out if m["type"] == "frame")
    assert set(pk.quant) == {"traj.s", "header.ticks"} and len(pk.quant["traj.s"]["max_err"]) == 5
    full_meta, full_blobs = next((m, b) for m, b in msgs if m["type"] == "header")
    bmeta, bblobs = headless.read_stream(atlas.pack_base_file(base))[0]
    meta, blobs = headless.merge_header((bmeta, bblobs), out[0])
    want = protocol.decode(protocol.encode(full_meta, {}))[0]
    assert {k: v for k, v in meta.items() if k != "blobs"} == {k: v for k, v in want.items() if k != "blobs"}
    assert set(blobs) == set(full_blobs) and np.abs(blobs["ticks"] - full_blobs["ticks"]).max() < 1e-4
    assert "ticks" not in out[0][1]  # the same as the base's: not repeated
    assert out[0][0]["$delta"] and "params" in out[0][0] and "title" not in out[0][0]
    # a key the point lacks and a blob it lacks are dropped from the merged header
    dm, db = headless.Packer(base=({**bmeta, "extra": 1}, {**bblobs, "more": np.zeros(2)})).delta(
        {k: v for k, v in full_meta.items()}, {"ticks": bblobs["ticks"]})
    assert dm["$drop"] == ["extra"] and dm["$drop_blobs"] == ["more"]
    mm, bb = headless.merge_header(({**bmeta, "extra": 1}, {**bblobs, "more": np.zeros(2)}), (dm, db))
    assert "extra" not in mm and "more" not in bb and "$drop" not in mm


def test_the_same_spec_gives_the_same_bytes_twice():
    spec = next(a for a in registry.atlases_of(registry.load("s98_atlas_toy")) if a["id"] == "explore")
    atlas = _site("atlas")
    m0, _ = atlas.run_point("s98_atlas_toy", spec, atlas.defaults(spec))
    base = atlas.base_header(spec, m0)
    one = atlas.pack_point(spec, atlas.run_point("s98_atlas_toy", spec, {"h_m": 0.0, "angle_deg": 30.0})[0], base)[0]
    time.sleep(0.01)
    two = atlas.pack_point(spec, atlas.run_point("s98_atlas_toy", spec, {"h_m": 0.0, "angle_deg": 30.0})[0], base)[0]
    assert one == two


def test_a_refusal_while_the_world_is_built_is_a_refused_point():
    """Integrator D14, review R-F F4: a ``Refusal`` from the world's constructor (u32: d ≤ a) is ``PointRefused`` with its
    text and hint, as one from ``check_params``; checks that end ✗ fail the run naming their labels."""
    with pytest.raises(headless.PointRefused) as e:
        headless.run_spec("u97_atlas_hog", "field", {"mode": "refuse"}, 1, {"frame_dt": 0.05}, {"world_s": 0.1})
    assert e.value.text["$t"].startswith("This test world refuses") and e.value.hint["$t"] == "choose another mode"
    with pytest.raises(headless.RunFailed) as f:
        headless.run_spec("u97_atlas_hog", "field", {"mode": "fail"}, 1, {"frame_dt": 0.05},
                          {"event": "landing", "after_s": 0.0, "max_world_s": 5.0})
    assert [c["$t"] for c in f.value.checks] == ["a check that fails on purpose"]


def test_a_delta_names_its_base_and_the_merge_drops_the_name():
    spec = next(a for a in registry.atlases_of(registry.load("s98_atlas_toy")) if a["id"] == "explore")
    atlas = _site("atlas")
    m0, _oc = atlas.run_point("s98_atlas_toy", spec, atlas.defaults(spec))
    base = atlas.base_header(spec, m0)
    msgs, _oc = atlas.run_point("s98_atlas_toy", spec, {"h_m": 1.0, "angle_deg": 60.0})
    data, _pk = atlas.pack_point(spec, msgs, base, "ab" * 32)
    head = headless.read_stream(data)[0]
    assert head[0]["$base"] == "ab" * 32
    meta, _b = headless.merge_header(headless.read_stream(atlas.pack_base_file(base))[0], head)
    assert not [k for k in meta if k.startswith("$")]
    full, _pk = atlas.pack_point(spec, msgs, None)  # no base: a full header
    assert "$delta" not in headless.read_stream(full)[0][0]
