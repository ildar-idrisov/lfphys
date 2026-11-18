# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The atlases of the screens (``site/atlas.py``, ``site/record.py``, ``site/plan.py``, ``sitelib``; design
``lfphys/sources/explore_2026-11-14_design.md`` §1, §8), on the toy world ``tests/site_worlds/s98_atlas_toy`` (Explore:
h × angle = 2 × 3 points, one refused; «Throws»: a compound control × h, 3 × 2; Lab work: a step of five heights and a
step of four, «ticks»):

* the grid is flattened row-major (the last control fastest); the manifest names every point, the refused one with its
  state and text, its base, its checks, its quantisation's errors and the references of the lab step's laws (one per
  law: integrator D4); the index lists the atlases with the build's time and CPU, the manifest has neither (review R-F
  F7);
* the same spec and code give the same point files and the same manifest twice; a point's header names its base
  (``$base``: the base file's sha256) and merged with the base is the run's header; the quantised path is within the
  manifest's ``max_err`` of the run's;
* budgets: a point over its target warns, over its hard limit fails; an atlas over its hard limit fails;
* keys and states in ``plan.py`` (missing, present, stale; the world's key covers the atlases), ``--stale``; an atlas
  with a missing point or base is stale (review R-F F6);
* a check that ends ✗ fails the atlas; a readout that is not among the header's measurables fails it; a refused default
  point fails it; an atlas not built now keeps its entry only while its key is current; a world that refuses in its
  constructor gives refused points, not a failed atlas (integrator D14; review R-F F4);
* the committed fixture of the player (``tests/site_worlds/recordings/s98_atlas_toy``) is whole, decodes, and is what
  the builder makes now (review R-F F14);
* EX2 (design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §5): the toy's screen «Throws» (a compound control,
  frames per played second, a stop by counted events, ``drop.blobs``) and its lab step «ticks» (a counter, a readout with
  the run's own error, formula columns): the manifest records a compound control's sets, every point runs with the
  parameters its value sets, the key covers the sets and the clock; a counter's measurable is a whole number in every
  frame; a measurable's ``sigma`` and ``ref`` and a readout's ``sigma`` name declared measurables.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import sys

import numpy as np
import pytest

from lfviz import headless, protocol, registry

VIZ = registry.ROOT
SITE_WORLDS = VIZ / "tests" / "site_worlds"
W = "s98_atlas_toy"


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


@pytest.fixture
def A():
    return _site("atlas")


def _spec(aid="explore"):
    return next(a for a in registry.atlases_of(registry.load(W)) if a["id"] == aid)


def _manifest(out, entry):
    return json.loads((out / W / entry["file"]).read_text(encoding="utf-8"))


def _build(A, out, only=None):
    entries, problems, warns = A.build_world(W, out, only)
    A.write_atlases(out, W, entries)
    return entries, problems, warns


def test_the_grid_the_manifest_and_the_index(A, tmp_path):
    spec = _spec()
    assert A.grid(spec["controls"]) == [(0.0, 0.0), (0.0, 30.0), (0.0, 60.0), (1.0, 0.0), (1.0, 30.0), (1.0, 60.0)]
    assert A.flat_index(spec["controls"], {"h_m": 1.0, "angle_deg": 30.0}) == 4
    assert A.flat_index(spec["controls"], {}) == 3  # the defaults
    with pytest.raises(ValueError):
        A.flat_index(spec["controls"], {"h_m": 0.5})
    entries, problems, _w = _build(A, tmp_path)
    assert problems == [] and [e["id"] for e in entries] == ["explore", "throws", "lab.heights", "lab.ticks"]
    idx = json.loads((tmp_path / W / "index.json").read_text(encoding="utf-8"))
    assert idx["atlases"] == json.loads(json.dumps(entries)) and idx["recordings"] == []
    e = entries[0]
    assert e["points"] == 5 and e["refused"] == 1 and e["file"].startswith("atlas/explore/atlas.")
    man = _manifest(tmp_path, e)
    assert {"world", "atlas", "atlas_version", "key", "version", "code_hash", "recorder_hash", "seed", "controls",
            "base", "points", "refusals", "checks", "quant", "references", "bytes_gz", "frame_dt", "stop"} <= set(man)
    assert "made" not in man and "cpu_s" not in man and e["made"] and e["cpu_s"] >= 0  # F7: in the index only
    assert man["key"] == e["key"] == _site("plan").L.atlas_key(spec, registry.code_hash(W))
    assert man["controls"] == [{"param": "h_m", "values": [0.0, 1.0], "default": 1.0},
                               {"param": "angle_deg", "values": [0.0, 30.0, 60.0], "default": 0.0}]
    assert man["points"][0] == [None, 0, 1] and man["refusals"][0]["$t"] == "{text}. What to change: {hint}"
    assert all(p[0].startswith(f"p{i}.") and p[2] == 0 for i, p in enumerate(man["points"]) if i)
    assert man["checks"] == {"ok": 10, "failed": 0, "expected": 0, "info": 0, "na": 0}
    folder = tmp_path / W / "atlas" / "explore"
    names = {f.name for f in folder.iterdir()}
    assert names == {man["base"]["file"], e["file"].rsplit("/", 1)[1], man["pool"]["file"]} \
        | {p[0] for p in man["points"] if p[0]}  # the pool of the blobs the points share (EX2 §5 F10)
    total = (folder / man["base"]["file"]).stat().st_size + sum(p[1] for p in man["points"]) + man["pool"]["bytes_gz"]
    assert man["bytes_gz"] == e["bytes_gz"] == total
    lab = _manifest(tmp_path, entries[2])
    assert set(lab["references"]) == {"k_horizontal", "zero_intercept"}  # one per law of the step (D4)
    ref = lab["references"]["k_horizontal"]
    assert ref["value"] == pytest.approx(1.5 * (2 / 9.80665) ** 0.5, rel=1e-15) and ref["kind"] == "closed form"
    assert lab["references"]["zero_intercept"]["value"] == 0.0 and _spec("lab.heights")["laws"] == \
        ["k_horizontal", "zero_intercept"]
    pool = headless.read_pool_file((folder / man["pool"]["file"]).read_bytes())
    for p in man["points"]:  # every point names its base (D13)
        if p[0]:
            head = headless.read_stream((folder / p[0]).read_bytes(), pool=pool)[0][0]
            assert head["$delta"] is True and head["$base"] == man["base"]["sha256"]


def test_the_same_bytes_twice_the_header_merge_and_the_quantisation_error(A, tmp_path):
    e1, _p, _w = _build(A, tmp_path / "a", ["explore"])
    e2, _p, _w = _build(A, tmp_path / "b", ["explore"])
    m1, m2 = _manifest(tmp_path / "a", e1[0]), _manifest(tmp_path / "b", e2[0])
    assert m1["points"] == m2["points"] and m1["base"] == m2["base"] and m1["key"] == m2["key"]
    assert e1[0]["file"] == e2[0]["file"]  # F7: the manifest too is the same bytes, so its hashed name is the same
    assert (tmp_path / "a" / W / e1[0]["file"]).read_bytes() == (tmp_path / "b" / W / e2[0]["file"]).read_bytes()
    for p in [m1["base"]["file"], m1["pool"]["file"]] + [p[0] for p in m1["points"] if p[0]]:  # the pool too (F10)
        assert (tmp_path / "a" / W / "atlas" / "explore" / p).read_bytes() == \
            (tmp_path / "b" / W / "atlas" / "explore" / p).read_bytes()
    spec = _spec()
    folder = tmp_path / "a" / W / "atlas" / "explore"
    base = headless.read_stream((folder / m1["base"]["file"]).read_bytes())[0]
    pool = headless.read_pool_file((folder / m1["pool"]["file"]).read_bytes())
    err = np.zeros(5)
    for i, combo in enumerate(A.grid(spec["controls"])):
        name = m1["points"][i][0]
        if name is None:
            continue
        pt = headless.read_stream((folder / name).read_bytes(), pool=pool)
        msgs, _oc = A.run_point(W, spec, dict(zip(["h_m", "angle_deg"], combo)))
        run_h = next(m for m, _b in msgs if m["type"] == "header")
        meta, blobs = headless.merge_header(base, pt[0])
        want = protocol.decode(protocol.encode(run_h, {}))[0]
        assert {k: v for k, v in meta.items() if k != "blobs"} == {k: v for k, v in want.items() if k != "blobs"}
        got = np.concatenate([b["s"] for m, b in pt if m["type"] == "traj"])
        ref = np.concatenate([b["s"] for m, b in msgs if m["type"] == "traj"])
        assert got.shape == ref.shape and got.dtype == np.float32
        err = np.maximum(err, np.abs(got - ref).max(axis=0))
        assert [m["type"] for m, _b in pt if m["type"] != "story"] == [m["type"] for m, _b in msgs if m["type"] != "story"]
    assert np.all(err <= np.asarray(m1["quant"]["traj.s"]["max_err"]) * (1 + 1e-9))
    assert m1["quant"]["traj.s"]["enc"] == "u16" and max(m1["quant"]["traj.s"]["max_rel"]) < 1e-4


def test_budgets(A, tmp_path, monkeypatch):
    L = A.L
    monkeypatch.setitem(L.BUDGET, "point", (1000, 1_000_000))
    _e, problems, warns = A.build_world(W, tmp_path / "a", ["explore"])
    assert problems == [] and any("over the target" in w and "point p" in w for w in warns)
    monkeypatch.setitem(L.BUDGET, "point", (1000, 2000))
    e, problems, _w = A.build_world(W, tmp_path / "b", ["explore"])
    assert any("over the hard limit" in p for p in problems) and e == []
    assert not (tmp_path / "b" / W / "atlas" / "explore").exists()  # a failed atlas leaves no files
    monkeypatch.setitem(L.BUDGET, "point", (150_000, 400_000))
    monkeypatch.setitem(L.BUDGET, "atlas", (5_000, 10_000))
    e, problems, _w = A.build_world(W, tmp_path / "c", ["explore"])
    assert any("for the atlas is over the hard limit" in p for p in problems)
    monkeypatch.setitem(L.BUDGET, "atlas", (6 * L.MB, 12 * L.MB))
    monkeypatch.setitem(L.BUDGET, "world", (100, 1000))  # the world's budget counts the atlases
    rec = _site("record")
    _idx, problems = rec.record_world(W, tmp_path / "d")
    assert any(f"{W}:" in p and "the world is over the hard limit" in p for p in problems)


def test_keys_states_and_the_stale_rule(A, tmp_path):
    L, plan = A.L, _site("plan")
    p = L.planned_world(W)
    assert [a["id"] for a in p["atlases"]] == ["explore", "throws", "lab.heights", "lab.ticks"] and p["atlases"][0]["points"] == 6
    assert set(L.atlas_status(tmp_path, p).values()) == {"missing"}
    _build(A, tmp_path)
    assert set(L.atlas_status(tmp_path, p).values()) == {"present"}
    idx = json.loads((tmp_path / W / "index.json").read_text(encoding="utf-8"))
    idx["atlases"][0]["key"] = "0" * 16
    (tmp_path / W / "index.json").write_text(json.dumps(idx), encoding="utf-8")
    rest = {"throws": "present", "lab.heights": "present", "lab.ticks": "present"}
    assert L.atlas_status(tmp_path, p) == {"explore": "stale", **rest}
    worlds = plan.plan(tmp_path)
    w = next(x for x in worlds if x["world"] == W)
    assert {a["id"]: a["state"] for a in w["atlases"]} == {"explore": "stale", **rest}
    assert {"world": W, "key": p["key"], "force": False} in plan.matrix(worlds, "stale", True)["include"]
    # the key follows the spec: values, defaults, frame_dt, stop, quantize, drop, the law; not the labels
    spec = _spec()
    k = L.atlas_key(spec, "abc")
    for change in ({"frame_dt": 0.02}, {"stop": {"world_s": 1}}, {"quantize": {}}, {"seed": 2}, {"laws": ["x"]},
                   {"drop": {"types": [], "frame_blobs": []}}, {"fixed": {"v0": 3}},
                   {"controls": [{**spec["controls"][0], "default": 0.0}, spec["controls"][1]]},
                   {"controls": [{**spec["controls"][0], "values": [0.0, 2.0]}, spec["controls"][1]]}):
        assert L.atlas_key({**spec, **change}, "abc") != k, change
    assert L.atlas_key({**spec, "controls": [{**c, "label": "x"} for c in spec["controls"]]}, "abc") == k
    assert L.atlas_key(spec, "abd") != k
    nogrid = L.atlas_key(spec, "abc", grid=False)
    assert L.atlas_key({**spec, "controls": [{**spec["controls"][0], "values": [0.0, 2.0]}, spec["controls"][1]]},
                       "abc", grid=False) == nogrid
    # the world's key covers the atlases
    assert p["key"] == L.world_key([r["key"] for r in p["recordings"]] +
                                   [f"atlas:{a['id']}:{a['key']}" for a in p["atlases"]])
    # an atlas not built now: its entry kept while current, dropped when stale
    entries, _pr, _w = A.build_world(W, tmp_path, ["lab.heights"])
    assert [x["id"] for x in entries] == ["throws", "lab.heights", "lab.ticks"]  # the current ones kept
    assert not (tmp_path / W / "atlas" / "explore").exists()  # the stale atlas's files went with it


def test_a_failing_check_a_missing_readout_or_a_refused_default_fails_the_atlas(A, tmp_path, monkeypatch):
    sim = registry.load(W)["simulation"]
    orig = sim.frame

    def frame(self):
        if self.landed and self.params["angle_deg"] == 60.0:
            self.emit({"type": "check", "t": self.t, "id": "bad", "label": "bad", "value": 1, "ref": 2, "rel": -0.5,
                       "tol": 1e-9, "unit": "", "group": "", "note": ""})
        return orig(self)
    monkeypatch.setattr(sim, "frame", frame)
    e, problems, _w = A.build_world(W, tmp_path / "a", ["explore"])
    assert e == [] and any("p2" in p and "check(s) end failed" in p for p in problems)
    monkeypatch.setattr(sim, "frame", orig)
    viz = registry.load(W)
    screens = [dict(s) for s in viz["screens"]]
    screens[1] = {**screens[1], "readouts": ["range", "nowhere"]}
    monkeypatch.setitem(sys.modules[f"{W}.viz"].VIZ, "screens", screens)
    e, problems, _w = A.build_world(W, tmp_path / "b", ["explore"])
    assert any("readout 'nowhere'" in p for p in problems)
    screens[1] = {**screens[1], "readouts": [], "controls": [{"param": "h_m", "values": [0.0, 1.0], "default": 0.0},
                                                            {"param": "angle_deg", "values": [0.0], "default": 0.0}]}
    e, problems, _w = A.build_world(W, tmp_path / "c", ["explore"])
    assert any("default point" in p and "refused" in p for p in problems)


def test_record_world_builds_the_atlases_after_the_recordings(tmp_path):
    rec = _site("record")
    index, problems = rec.record_world(W, tmp_path)
    assert problems == [] and [e["id"] for e in index["recordings"]] == ["story", "field"]
    assert [a["id"] for a in index["atlases"]] == ["explore", "throws", "lab.heights", "lab.ticks"]
    story = index["recordings"][0]
    assert story["captions"] == 3 and story["quant"]["traj.s"]["enc"] == "u16"
    index2, _p = rec.record_world(W, tmp_path, only=["field"])  # only a recording: the atlases are kept as they are
    assert index2["atlases"] == index["atlases"]
    assert rec.main(["--world", W, "--out", str(tmp_path), "--no-atlases"]) == 0
    assert _site("atlas").main(["--world", W, "--out", str(tmp_path), "--atlas", "explore"]) == 0


def test_the_committed_fixture_of_the_player_is_whole():
    """The committed fixture (the player's Node tests read it; its keys may be stale: they compare none) is whole,
    decodes, and is of the builder's format versions."""
    folder = SITE_WORLDS / "recordings" / W
    idx = json.loads((folder / "index.json").read_text(encoding="utf-8"))
    assert idx["world"] == W and [a["id"] for a in idx["atlases"]] == ["explore", "throws", "lab.heights", "lab.ticks"]
    L = _site("atlas").L
    assert idx["recorder"] == L.RECORDER_VERSION, "remake the fixture: tests/site_worlds/make_fixture.py"
    for a in idx["atlases"]:
        assert json.loads((folder / a["file"]).read_text(encoding="utf-8"))["atlas_version"] == L.ATLAS_VERSION
    for r in idx["recordings"]:
        data = (folder / r["file"]).read_bytes()
        assert len(data) == r["bytes_gz"] and gzip.decompress(data).startswith(protocol.MAGIC)
    for a in idx["atlases"]:
        man = json.loads((folder / a["file"]).read_text(encoding="utf-8"))
        d = (folder / a["file"]).parent
        base = headless.read_stream((d / man["base"]["file"]).read_bytes())
        assert len(base) == 1 and base[0][0]["type"] == "header"
        pool = headless.read_pool_file((d / man["pool"]["file"]).read_bytes()) if man.get("pool") else None
        for name, size, state in man["points"]:
            if state:
                continue
            data = (d / name).read_bytes()
            assert len(data) == size
            msgs = headless.read_stream(data, pool=pool)
            assert msgs[0][0]["$delta"] and msgs[-1][0]["reason"] == "atlas"
        assert {f.name for f in d.iterdir()} == {man["base"]["file"], a["file"].rsplit("/", 1)[1]} \
            | {p[0] for p in man["points"] if p[0]} | ({man["pool"]["file"]} if man.get("pool") else set())
    # the pooled point the Node test decodes with the pool, and its bytes without the pool (EX2 §5 F10, §7)
    case = json.loads((SITE_WORLDS / "quant" / "pool_point.json").read_text(encoding="utf-8"))
    a = next(x for x in idx["atlases"] if x["id"] == case["atlas"])
    man = json.loads((folder / a["file"]).read_text(encoding="utf-8"))
    d = (folder / a["file"]).parent
    data = (d / man["points"][case["point"]][0]).read_bytes()
    plain = headless.unpool(data, (d / man["pool"]["file"]).read_bytes())
    assert plain != data and plain == (SITE_WORLDS / "quant" / "pool_point.lfpt.gz").read_bytes(), \
        "remake the fixture: tests/site_worlds/make_fixture.py"


def test_a_missing_point_or_base_makes_the_atlas_stale(A, tmp_path):
    """Review R-F F6: ``atlas_status`` (and so ``plan.py`` and ``record.py --stale``) checks the base and every point the
    manifest names, with their sizes, not only the manifest."""
    L = A.L
    p = L.planned_world(W)
    entries, _pr, _w = _build(A, tmp_path)
    assert set(L.atlas_status(tmp_path, p).values()) == {"present"}
    man = _manifest(tmp_path, entries[0])
    folder = tmp_path / W / "atlas" / "explore"
    victim = folder / man["points"][4][0]
    data = victim.read_bytes()
    victim.unlink()
    assert L.atlas_status(tmp_path, p) == {"explore": "stale", "throws": "present", "lab.heights": "present",
                                           "lab.ticks": "present"}
    victim.write_bytes(data + b"x")  # another size
    assert L.atlas_status(tmp_path, p)["explore"] == "stale"
    victim.write_bytes(data)
    assert L.atlas_status(tmp_path, p)["explore"] == "present"
    (folder / man["base"]["file"]).unlink()
    assert L.atlas_status(tmp_path, p)["explore"] == "stale"
    stale = [w for w in [W] if set(L.atlas_status(tmp_path, L.planned_world(w)).values()) - {"present"}]
    assert stale == [W]  # what record.py --stale and atlas.py --stale take


def test_a_refusal_of_the_worlds_constructor_is_a_refused_point(A, tmp_path):
    """Integrator D14, review R-F F4: u32 refuses d ≤ a in its constructor; a toy world does so for ``mode: refuse``.
    Such a grid point is refused, with the world's text and hint, and the atlas is built."""
    spec = next(a for a in registry.atlases_of(registry.load("u97_atlas_hog")) if a["id"] == "faults")
    with pytest.raises(headless.PointRefused) as ex:
        A.run_point("u97_atlas_hog", spec, {"h_m": 1.0, "mode": "refuse"})
    assert ex.value.text["$t"].startswith("This test world refuses") and ex.value.hint["$t"] == "choose another mode"
    entries, problems, _w = A.build_world("u97_atlas_hog", tmp_path, ["faults"])
    assert problems == [] and [e["id"] for e in entries] == ["faults"]
    assert entries[0]["points"] == 2 and entries[0]["refused"] == 2
    man = json.loads((tmp_path / "u97_atlas_hog" / entries[0]["file"]).read_text(encoding="utf-8"))
    assert [p[2] for p in man["points"]] == [0, 1, 0, 1]
    assert man["refusals"][0]["a"]["text"]["$t"].startswith("This test world refuses")


def test_the_committed_fixture_is_what_the_builder_makes_now(tmp_path):
    """Review R-F F14: the player's Node tests and browser tests read the committed fixture; a change of the packing,
    the header's delta or the recorder would leave them testing an old format. A fresh build of the toy world gives
    the same recording, base and point files (by name and bytes) and the same manifests but for the code's keys
    (``tests/site_worlds/make_fixture.py`` remakes it)."""
    rec = _site("record")
    index, problems = rec.record_world(W, tmp_path)
    assert problems == []
    folder = SITE_WORLDS / "recordings" / W
    old = json.loads((folder / "index.json").read_text(encoding="utf-8"))
    remake = "the fixture is stale: remake it with tests/site_worlds/make_fixture.py"
    assert [(r["id"], r["file"], r["bytes_gz"]) for r in index["recordings"]] == \
        [(r["id"], r["file"], r["bytes_gz"]) for r in old["recordings"]], remake
    for r in index["recordings"]:
        assert (tmp_path / W / r["file"]).read_bytes() == (folder / r["file"]).read_bytes(), remake
    assert [a["id"] for a in index["atlases"]] == [a["id"] for a in old["atlases"]], remake
    code_keys = ("key", "code_hash", "recorder_hash")
    for new_e, old_e in zip(index["atlases"], old["atlases"]):
        new_m = json.loads((tmp_path / W / new_e["file"]).read_text(encoding="utf-8"))
        old_m = json.loads((folder / old_e["file"]).read_text(encoding="utf-8"))
        assert {k: v for k, v in new_m.items() if k not in code_keys} == \
            {k: v for k, v in old_m.items() if k not in code_keys}, remake
        d_new, d_old = (tmp_path / W / new_e["file"]).parent, (folder / old_e["file"]).parent
        for name in [new_m["base"]["file"]] + [p[0] for p in new_m["points"] if p[0]] \
                + ([new_m["pool"]["file"]] if new_m.get("pool") else []):
            assert (d_new / name).read_bytes() == (d_old / name).read_bytes(), (name, remake)


def test_the_browser_tests_fixtures_are_built_current(tmp_path, monkeypatch):
    """``site/fixtures.py`` (integrator, 2026-11-17): what a browser test serves is built now, so every key is the
    expected one (a server's player refuses a stale atlas: D11); it finds the test worlds by itself."""
    monkeypatch.delenv("LFVIZ_EXTRA", raising=False)
    fx = _site("fixtures")
    assert fx.main(["--out", str(tmp_path)]) == 0
    monkeypatch.setenv("LFVIZ_EXTRA", str(SITE_WORLDS))
    plan = _site("atlas").L.planned_world(W)
    assert set(_site("atlas").L.atlas_status(tmp_path, plan).values()) == {"present"}
    assert set(_site("atlas").L.status(tmp_path, plan).values()) == {"present"}


# --- EX2 (design lfphys/sources/explore_EX2_2026-11-18_design.md §5 F1–F5, F7, F8) ---------------------------------------
def test_a_compound_control_the_fps_clock_and_a_stop_by_counted_events(A, tmp_path):
    """The toy's screen «Throws»: a compound control ``throw`` (the speed and the angle together) × h; frames per played
    second (``fps``, no ``frame_dt``); six ticks or the landing stop a point; ``drop.blobs``. The manifest records the
    sets; every point is run with the parameters its value sets; the key covers the sets and the clock."""
    spec = _spec("throws")
    c0 = spec["controls"][0]
    assert c0["param"] == c0["id"] == "throw" and c0["compound"] and c0["sets"]["angle_deg"] == [0.0, 30.0, 60.0]
    assert spec["fps"] == 20.0 and spec["frame_dt"] is None and spec["speed"] == 0.5
    entries, problems, _w = A.build_world(W, tmp_path, ["throws"])
    assert problems == []
    man = _manifest(tmp_path, entries[0])
    assert man["controls"][0] == {"param": "throw", "values": ["flat", "lob", "steep"], "default": "lob",
                                  "compound": True, "sets": {"v0": [2.0, 3.0, 2.5], "angle_deg": [0.0, 30.0, 60.0]}}
    assert man["fps"] == 20.0 and man["frame_dt"] is None and man["stop"]["events"] == {"tick": 6, "landing": 1}
    folder = tmp_path / W / "atlas" / "throws"
    pool = headless.read_pool_file((folder / man["pool"]["file"]).read_bytes()) if man.get("pool") else None
    for i, combo in enumerate(A.grid(spec["controls"])):
        pt = headless.read_stream((folder / man["points"][i][0]).read_bytes(), pool=pool)
        head = headless.merge_header(headless.read_stream((folder / man["base"]["file"]).read_bytes())[0], pt[0])[0]
        k = c0["values"].index(combo[0])
        assert head["params"]["v0"] == c0["sets"]["v0"][k] and head["params"]["angle_deg"] == c0["sets"]["angle_deg"][k]
        assert head["params"]["h_m"] == combo[1] and "ticks" not in pt[0][1]
        frames = [m for m, _b in pt if m["type"] == "frame"]
        assert all("ghost" not in b for m, b in pt if m["type"] == "frame")
        ticks = [m["t"] for m, _b in pt if m["type"] == "event" and m["kind"] == "tick"]
        land = [m["t"] for m, _b in pt if m["type"] == "event" and m["kind"] == "landing"]
        first = min(x for x in ([ticks[5]] if len(ticks) >= 6 else []) + land[:1])
        assert frames[-1]["t"] == pytest.approx(first + 0.1, abs=1e-12)  # 0.1 s after the first count reached
        assert frames[1]["t"] - frames[0]["t"] == pytest.approx(0.05, abs=1e-12)  # 1 / fps at the toy's speed 1
    L = A.L
    k = L.atlas_key(spec, "abc")
    other = {**spec, "controls": [{**c0, "sets": {**c0["sets"], "v0": [2.0, 3.0, 2.6]}}, spec["controls"][1]]}
    assert L.atlas_key(other, "abc") != k and L.atlas_key(other, "abc", grid=False) != L.atlas_key(spec, "abc", grid=False)
    assert L.atlas_key({**spec, "fps": 10.0}, "abc") != k
    assert L.atlas_key({**spec, "speed": 1.0}, "abc") == k  # the playback speed changes no byte
    with pytest.raises(ValueError):
        A.params_of(spec, {"throw": "sideways", "h_m": 1.0})


def test_the_lab_step_with_a_counter_a_runs_error_and_formula_columns(A, tmp_path):
    """The toy's lab step «ticks»: the counter's measurable is a whole number in every frame, the readout's σ and the
    measurables' sigma and ref are declared measurables (``check_declarations``); its stop is by counted events."""
    entries, problems, _w = A.build_world(W, tmp_path, ["lab.ticks"])
    assert problems == [] and entries[0]["points"] == 4
    man = _manifest(tmp_path, entries[0])
    assert man["references"]["fall_coefficient"]["value"] == pytest.approx((2 / 9.80665) ** 0.5, rel=1e-15)
    spec = _spec("lab.ticks")
    assert A.counted(registry.load(W), spec) == {"n_ticks"}
    msgs, _oc = A.run_point(W, spec, {"h_m": 0.8})
    assert A.not_counts(msgs, {"n_ticks"}) == []
    assert [m["meas"]["n_ticks"] for m, _b in msgs if m["type"] == "frame"][-1] == 4  # T = 0.404 s: ticks 0.1 … 0.4
    bad = [({**m, "meas": {**m["meas"], "n_ticks": 2.5}}, b) if m["type"] == "frame" else (m, b) for m, b in msgs]
    assert A.not_counts(bad, {"n_ticks"}) == ["n_ticks"]
    viz = registry.load(W)
    head = next(m for m, _b in msgs if m["type"] == "header")
    assert A.check_declarations(viz, spec, head) == []
    broken = {**head, "measurables": [*head["measurables"][:4], {"id": "v_mean", "label": "x", "sigma": "nowhere"},
                                      *head["measurables"][5:]]}
    assert any("sigma 'nowhere'" in x for x in A.check_declarations(viz, spec, broken))
    noref = {**head, "measurables": [{**head["measurables"][0], "ref": "range"}, *head["measurables"][1:]]}
    assert any("its ref 'range'" in x for x in A.check_declarations(viz, spec, noref))  # not itself
    nosig = {**head, "measurables": [m for m in head["measurables"] if m["id"] != "v_mean_se"]}
    probs = A.check_declarations(viz, spec, nosig)
    assert any("instrument speedo: its sigma 'v_mean_se'" in x for x in probs)


def test_a_counter_that_reads_no_whole_number_fails_the_atlas(A, tmp_path, monkeypatch):
    sim = registry.load(W)["simulation"]
    orig = sim.frame

    def frame(self):
        meta, blobs = orig(self)
        return {**meta, "meas": {**meta["meas"], "n_ticks": meta["meas"]["n_ticks"] + 0.5}}, blobs
    monkeypatch.setattr(sim, "frame", frame)
    e, problems, _w = A.build_world(W, tmp_path, ["lab.ticks"])
    assert e == [] and any("a counter reads ['n_ticks'], not whole numbers" in p for p in problems)



def test_the_pool_of_shared_blobs(A, tmp_path):
    """EX2 §5 F10: a blob stored by two or more points (the toy's aim line: the same for every point of one angle) is kept
    once in the atlas's pool and named by the points; a point decoded with the pool equals the same point packed without
    it; unpooled, its bytes are those of the packing without a pool (what a live point is); a pool missing or of another
    size makes the atlas stale; ``ATLAS_VERSION`` is 3."""
    assert A.L.ATLAS_VERSION == "3"
    entries, problems, _w = _build(A, tmp_path, ["explore"])
    assert problems == []
    man = _manifest(tmp_path, entries[0])
    folder = tmp_path / W / "atlas" / "explore"
    pool_bytes = (folder / man["pool"]["file"]).read_bytes()
    assert len(pool_bytes) == man["pool"]["bytes_gz"] and hashlib.sha256(pool_bytes).hexdigest() == man["pool"]["sha256"]
    pool = headless.read_pool_file(pool_bytes)
    assert len(pool) == 2  # the aim lines of 30° and 60°: each stored by the points of h 0 and 1
    spec = _spec()
    m0, _oc = A.run_point(W, spec, A.defaults(spec))
    base = A.base_header(spec, m0)
    bsha = man["base"]["sha256"]
    pooled_points = 0
    for i, combo in enumerate(A.grid(spec["controls"])):
        name = man["points"][i][0]
        if name is None:
            continue
        data = (folder / name).read_bytes()
        msgs, _oc = A.run_point(W, spec, dict(zip(["h_m", "angle_deg"], combo)))
        plain, _pk = A.pack_point(spec, msgs, base, bsha)
        assert headless.unpool(data, pool_bytes) == plain  # a live point's bytes
        if b'"pool"' in gzip.decompress(data):
            pooled_points += 1
            with pytest.raises(KeyError):
                headless.read_stream(data)  # without the pool it cannot be read
        a, b = headless.read_stream(data, pool=pool), headless.read_stream(plain)
        nob = lambda msgs: [{k: v for k, v in m.items() if k != "blobs"} for m, _x in msgs]  # noqa: E731
        assert nob(a) == nob(b)
        for (_m1, x1), (_m2, x2) in zip(a, b):
            assert set(x1) == set(x2) and all(np.array_equal(x1[k], x2[k], equal_nan=True) for k in x1)
    assert pooled_points == 4
    L = A.L
    p = L.planned_world(W)
    assert L.atlas_status(tmp_path, p)["explore"] == "present"
    (folder / man["pool"]["file"]).write_bytes(pool_bytes + b"x")
    assert L.atlas_status(tmp_path, p)["explore"] == "stale"
    (folder / man["pool"]["file"]).unlink()
    assert L.atlas_status(tmp_path, p)["explore"] == "stale"
