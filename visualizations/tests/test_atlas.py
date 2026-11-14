# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The atlases of the screens (``site/atlas.py``, ``site/record.py``, ``site/plan.py``, ``sitelib``; design
``lfphys/sources/explore_2026-11-14_design.md`` §1, §8), on the toy world ``tests/site_worlds/s98_atlas_toy`` (Explore:
h × angle = 2 × 3 points, one refused; Lab work: one step of five heights):

* the grid is flattened row-major (the last control fastest); the manifest names every point, the refused one with its
  state and text, its base, its checks, its quantisation's errors and the lab's law reference; the index lists the
  atlases;
* the same spec and code give the same point files twice; a point's header merged with the base is the run's header;
  the quantised path is within the manifest's ``max_err`` of the run's;
* budgets: a point over its target warns, over its hard limit fails; an atlas over its hard limit fails;
* keys and states in ``plan.py`` (missing, present, stale; the world's key covers the atlases), ``--stale``;
* a check that ends ✗ fails the atlas; a readout that is not among the header's measurables fails it; a refused default
  point fails it; an atlas not built now keeps its entry only while its key is current;
* the committed fixture of the player (``tests/site_worlds/recordings/s98_atlas_toy``) is whole and decodes.
"""

from __future__ import annotations

import gzip
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
    assert problems == [] and [e["id"] for e in entries] == ["explore", "lab.heights"]
    idx = json.loads((tmp_path / W / "index.json").read_text(encoding="utf-8"))
    assert idx["atlases"] == json.loads(json.dumps(entries)) and idx["recordings"] == []
    e = entries[0]
    assert e["points"] == 5 and e["refused"] == 1 and e["file"].startswith("atlas/explore/atlas.")
    man = _manifest(tmp_path, e)
    assert {"world", "atlas", "atlas_version", "key", "version", "code_hash", "recorder_hash", "made", "seed", "controls",
            "base", "points", "refusals", "checks", "quant", "references", "cpu_s", "bytes_gz", "frame_dt",
            "stop"} <= set(man)
    assert man["key"] == e["key"] == _site("plan").L.atlas_key(spec, registry.code_hash(W))
    assert man["controls"] == [{"param": "h_m", "values": [0.0, 1.0], "default": 1.0},
                               {"param": "angle_deg", "values": [0.0, 30.0, 60.0], "default": 0.0}]
    assert man["points"][0] == [None, 0, 1] and man["refusals"][0]["$t"] == "{text}. What to change: {hint}"
    assert all(p[0].startswith(f"p{i}.") and p[2] == 0 for i, p in enumerate(man["points"]) if i)
    assert man["checks"] == {"ok": 10, "failed": 0, "expected": 0, "info": 0, "na": 0}
    folder = tmp_path / W / "atlas" / "explore"
    names = {f.name for f in folder.iterdir()}
    assert names == {man["base"]["file"], e["file"].rsplit("/", 1)[1]} | {p[0] for p in man["points"] if p[0]}
    total = (folder / man["base"]["file"]).stat().st_size + sum(p[1] for p in man["points"])
    assert man["bytes_gz"] == e["bytes_gz"] == total
    lab = _manifest(tmp_path, entries[1])
    ref = lab["references"]["k_horizontal"]
    assert ref["value"] == pytest.approx(1.5 * (2 / 9.80665) ** 0.5, rel=1e-15) and ref["kind"] == "closed form"


def test_the_same_bytes_twice_the_header_merge_and_the_quantisation_error(A, tmp_path):
    e1, _p, _w = _build(A, tmp_path / "a", ["explore"])
    e2, _p, _w = _build(A, tmp_path / "b", ["explore"])
    m1, m2 = _manifest(tmp_path / "a", e1[0]), _manifest(tmp_path / "b", e2[0])
    assert m1["points"] == m2["points"] and m1["base"] == m2["base"] and m1["key"] == m2["key"]
    for p in [m1["base"]["file"]] + [p[0] for p in m1["points"] if p[0]]:
        assert (tmp_path / "a" / W / "atlas" / "explore" / p).read_bytes() == \
            (tmp_path / "b" / W / "atlas" / "explore" / p).read_bytes()
    spec = _spec()
    folder = tmp_path / "a" / W / "atlas" / "explore"
    base = headless.read_stream((folder / m1["base"]["file"]).read_bytes())[0]
    err = np.zeros(5)
    for i, combo in enumerate(A.grid(spec["controls"])):
        name = m1["points"][i][0]
        if name is None:
            continue
        pt = headless.read_stream((folder / name).read_bytes())
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
    assert [a["id"] for a in p["atlases"]] == ["explore", "lab.heights"] and p["atlases"][0]["points"] == 6
    assert set(L.atlas_status(tmp_path, p).values()) == {"missing"}
    _build(A, tmp_path)
    assert set(L.atlas_status(tmp_path, p).values()) == {"present"}
    idx = json.loads((tmp_path / W / "index.json").read_text(encoding="utf-8"))
    idx["atlases"][0]["key"] = "0" * 16
    (tmp_path / W / "index.json").write_text(json.dumps(idx), encoding="utf-8")
    assert L.atlas_status(tmp_path, p) == {"explore": "stale", "lab.heights": "present"}
    worlds = plan.plan(tmp_path)
    w = next(x for x in worlds if x["world"] == W)
    assert {a["id"]: a["state"] for a in w["atlases"]} == {"explore": "stale", "lab.heights": "present"}
    assert {"world": W, "key": p["key"], "force": False} in plan.matrix(worlds, "stale", True)["include"]
    # the key follows the spec: values, defaults, frame_dt, stop, quantize, drop, the law; not the labels
    spec = _spec()
    k = L.atlas_key(spec, "abc")
    for change in ({"frame_dt": 0.02}, {"stop": {"world_s": 1}}, {"quantize": {}}, {"seed": 2}, {"law": "x"},
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
    assert [x["id"] for x in entries] == ["lab.heights"]
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
    assert [a["id"] for a in index["atlases"]] == ["explore", "lab.heights"]
    story = index["recordings"][0]
    assert story["captions"] == 3 and story["quant"]["traj.s"]["enc"] == "u16"
    index2, _p = rec.record_world(W, tmp_path, only=["field"])  # only a recording: the atlases are kept as they are
    assert index2["atlases"] == index["atlases"]
    assert rec.main(["--world", W, "--out", str(tmp_path), "--no-atlases"]) == 0
    assert _site("atlas").main(["--world", W, "--out", str(tmp_path), "--atlas", "explore"]) == 0


def test_the_committed_fixture_of_the_player_is_whole():
    folder = SITE_WORLDS / "recordings" / W
    idx = json.loads((folder / "index.json").read_text(encoding="utf-8"))
    assert idx["world"] == W and [a["id"] for a in idx["atlases"]] == ["explore", "lab.heights"]
    for r in idx["recordings"]:
        data = (folder / r["file"]).read_bytes()
        assert len(data) == r["bytes_gz"] and gzip.decompress(data).startswith(protocol.MAGIC)
    for a in idx["atlases"]:
        man = json.loads((folder / a["file"]).read_text(encoding="utf-8"))
        d = (folder / a["file"]).parent
        base = headless.read_stream((d / man["base"]["file"]).read_bytes())
        assert len(base) == 1 and base[0][0]["type"] == "header"
        for name, size, state in man["points"]:
            if state:
                continue
            data = (d / name).read_bytes()
            assert len(data) == size
            msgs = headless.read_stream(data)
            assert msgs[0][0]["$delta"] and msgs[-1][0]["reason"] == "atlas"
        assert {f.name for f in d.iterdir()} == {man["base"]["file"], a["file"].rsplit("/", 1)[1]} \
            | {p[0] for p in man["points"] if p[0]}
