# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The offline recorder of the public site (``site/record.py``, ``site/plan.py``; design of the start page §4.1, §4.3,
§5.1; CONTRACT of steps S and P), on the tiny test world ``tests/site_worlds/u98_site_toy``:

* the frame count is ``seconds × fps`` before thinning, the frames ``speed / fps`` of world time apart;
* the script lands at its frame (``round(at × fps)``), and the dropped messages (``command``, ``checkpoint``, …) are not
  in the file;
* thinning keeps every accumulative message, the first, the last and the poster frame;
* a budget's hard limit is reported as a problem, the target makes the recorder thin;
* the file decodes with ``lfviz.protocol`` into the same messages, and the index has the CONTRACT's fields;
* the plan's states: missing, present, stale.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys

import pytest

from lfviz import protocol, registry

VIZ = registry.ROOT
SITE_WORLDS = VIZ / "tests" / "site_worlds"


def _site(name):
    if f"lfsite_{name}" in sys.modules:
        return sys.modules[f"lfsite_{name}"]
    spec = importlib.util.spec_from_file_location(f"lfsite_{name}", VIZ / "site" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # a dataclass looks its module up there
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _extra(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(SITE_WORLDS))


@pytest.fixture
def rec():
    return _site("record")


def _spec(rid="slow"):
    viz = registry.load("u98_site_toy")
    return next(r for r in registry.recordings_of(viz) if r["id"] == rid)


def _types(raw):
    return [typ for typ, _t, _d in raw.msgs]


def test_the_frame_count_is_seconds_times_fps_on_the_recorders_own_clock(rec):
    for rid in ("slow", "fast"):
        spec = _spec(rid)
        raw = rec.record("u98_site_toy", spec)
        n = int(round(spec["seconds"] * spec["fps"]))
        assert len(raw.frames) == n
        speed = spec["speed"] or 1.0
        ts = [raw.msgs[i][1] for i in raw.frames]
        assert ts[0] == 0.0
        assert all(abs((b - a) - speed / spec["fps"]) < 1e-12 for a, b in zip(ts, ts[1:])), ts
        assert raw.poster_k == min(n - 1, round(spec["poster"] * spec["fps"]))
        types = _types(raw)
        assert types[0] == "header" and types[-1] == "end"
        assert {"command", "checkpoint", "resumed", "record_segment", "busy"}.isdisjoint(types)
        states = [protocol.decode(d)[0] for typ, _t, d in raw.msgs if typ == "state"]
        assert states[-1]["playing"] is True and states[-1]["speed"] == speed


def test_the_script_lands_at_its_frame(rec):
    spec = _spec("slow")  # kick at 1.0 s, set v = 0.5 at 2.0 s, 10 fps
    raw = rec.record("u98_site_toy", spec)
    frame_t = [raw.msgs[i][1] for i in raw.frames]
    metas = [protocol.decode(d)[0] for _typ, _t, d in raw.msgs]
    kicks = [m for m in metas if m["type"] == "event" and m.get("name") == "kick"]
    assert len(kicks) == 1 and kicks[0]["t"] == frame_t[10]
    lives = [m for m in metas if m["type"] == "live"]
    assert len(lives) == 1 and lives[0]["t"] == frame_t[20] and lives[0]["values"]["v"] == 0.5
    frames = [m for m in metas if m["type"] == "frame"]
    assert frames[9]["v"] == 1.0 and frames[10]["v"] == 2.0 and frames[20]["v"] == 0.5  # the frame shows the change
    assert not [m for m in metas if m["type"] == "command"]


def test_thinning_keeps_every_accumulative_message_and_the_poster(rec):
    raw = rec.record("u98_site_toy", _spec("slow"))
    full = rec.pack(raw, 1)
    for stride in (2, 3, 5):
        p = rec.pack(raw, stride)
        msgs = [m for _o, m in protocol.iter_stream(p.data, len(protocol.MAGIC))]
        kinds = [protocol.peek_meta(m)["type"] for m in msgs]
        others = [m for m, k in zip(msgs, kinds) if k != "frame"]
        assert others == [d for typ, _t, d in raw.msgs if typ != "frame"]  # every other message, in order, unchanged
        n = len(raw.frames)
        assert p.kept == sorted({k for k in range(n) if k % stride == 0} | {n - 1, raw.poster_k})
        assert kinds.count("frame") == len(p.kept) < n
        assert p.kept[p.poster_frame] == raw.poster_k
        assert len(p.data) < len(full.data)


def test_a_budget_over_its_target_thins_and_over_its_hard_limit_fails(rec, tmp_path, monkeypatch):
    L = rec.L
    raw = rec.record("u98_site_toy", _spec("slow"))
    assert rec.thin_to(raw, len(rec.pack(raw, 1).gz)).stride == 1  # within the target: every frame
    assert rec.thin_to(raw, len(rec.pack(raw, 2).gz)).stride == 2  # over it: the smallest stride that fits
    assert rec.thin_to(raw, 1).stride <= rec.max_stride(raw) == 5  # never below 2 frames per played second
    monkeypatch.setitem(L.BUDGET, "file", (100, 200))  # nothing fits the hard limit: a problem names it
    index, problems = rec.record_world("u98_site_toy", tmp_path / "b", only=["slow"])
    assert len(problems) == 1 and "hard limit" in problems[0] and "u98_site_toy/slow" in problems[0]
    monkeypatch.setitem(L.BUDGET, "file", (3 * L.MB, 10 * L.MB))
    monkeypatch.setitem(L.BUDGET, "world", (100, 200))  # the world's hard limit
    _index, problems = rec.record_world("u98_site_toy", tmp_path / "c")
    assert any("the world" in p and "hard limit" in p for p in problems)


def test_the_file_decodes_with_the_protocol_and_the_index_follows_the_contract(rec, tmp_path):
    index, problems = rec.record_world("u98_site_toy", tmp_path)
    assert problems == []
    assert {"world", "version", "recorder", "code_hash", "made", "recordings"} <= set(index)
    assert index["world"] == "u98_site_toy" and index["code_hash"] == registry.code_hash("u98_site_toy")
    on_disk = json.loads((tmp_path / "u98_site_toy" / "index.json").read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(index, ensure_ascii=False))
    assert [e["id"] for e in index["recordings"]] == ["slow", "fast"]
    for e in index["recordings"]:
        assert {"id", "preset", "label", "file", "seconds", "fps", "frame_stride", "frames", "bytes", "bytes_gz",
                "poster_t", "worlds", "sha256", "key"} <= set(e)
        f = tmp_path / "u98_site_toy" / e["file"]
        gz = f.read_bytes()
        assert e["file"] == f"{e['id']}.{e['sha256'][:8]}.lfrec.gz" and len(gz) == e["bytes_gz"]
        data = gzip.decompress(gz)
        assert data.startswith(protocol.MAGIC) and len(data) == e["bytes"]
        metas = [protocol.decode(m)[0] for _o, m in protocol.iter_stream(data, len(protocol.MAGIC))]
        frames = [m for m in metas if m["type"] == "frame"]
        assert len(frames) == e["frames"] and e["worlds"] == sum(m["type"] == "header" for m in metas) == 1
        assert frames[e["poster_frame"]]["t"] == e["poster_t"]
        assert metas[-1] == {**metas[-1], "type": "end", "reason": "recording"}
        assert e["label"]["$t"]  # the preset's text (a T)
    # a second recording replaces the world's files, never leaving an old one
    index2, _ = rec.record_world("u98_site_toy", tmp_path)
    names = sorted(p.name for p in (tmp_path / "u98_site_toy").glob("*.lfrec.gz"))
    assert names == sorted(e["file"] for e in index2["recordings"])


def test_the_plan_marks_missing_present_and_stale(rec, tmp_path):
    plan = _site("plan")
    L = rec.L
    p = L.planned_world("u98_site_toy")
    assert set(L.status(tmp_path, p).values()) == {"missing"}
    rec.record_world("u98_site_toy", tmp_path)
    assert set(L.status(tmp_path, p).values()) == {"present"}
    idx = json.loads((tmp_path / "u98_site_toy" / "index.json").read_text(encoding="utf-8"))
    idx["recordings"][0]["key"] = "0" * 16  # recorded for another spec or code
    (tmp_path / "u98_site_toy" / "index.json").write_text(json.dumps(idx), encoding="utf-8")
    assert L.status(tmp_path, p) == {"slow": "stale", "fast": "present"}
    # the key follows the spec and the recorder's version
    spec = _spec("slow")
    assert L.spec_key(spec, "abc") != L.spec_key({**spec, "seconds": 4}, "abc") != L.spec_key(spec, "abd")
    # the matrix: never empty; "all" forces
    worlds = plan.plan(tmp_path)
    m = plan.matrix(worlds, "all", True)
    assert {"world": "u98_site_toy", "key": p["key"], "force": True} in m["include"]
    assert plan.matrix([], "stale", True) == {"include": [{"world": "", "key": "", "force": False}]}


# --- review P17-site F1, F2, F4, F9; integrator D5, D6 --------------------------------------------------------------

def _gz(rec, viz_id, rid):
    return rec.pack(rec.record(viz_id, _spec(rid) if viz_id == "u98_site_toy" else
                               registry.recordings_of(registry.load(viz_id))[0]), 1).gz


def test_a_recording_is_byte_identical_alone_or_after_another_world(rec):
    """D6: two recordings of the same spec by the same code are the same bytes, whatever the process recorded before
    (F1: the header's kernels are this recording's own; F2: no CPU time in the frames)."""
    from lfphys.core import backend as B
    alone = _gz(rec, "u98_site_toy", "slow")
    _gz(rec, "r98_site_probe", None)  # another world first
    B._USED["fake.kernel"] = {"drawn": {"device": "cpu", "precision": "fp64", "reason": "a test", "size": 1}}
    after = _gz(rec, "u98_site_toy", "slow")
    assert after == alone
    data = gzip.decompress(after)
    metas = [protocol.decode(m)[0] for _o, m in protocol.iter_stream(data, len(protocol.MAGIC))]
    header = next(m for m in metas if m["type"] == "header")
    assert "fake.kernel" not in ((header.get("backend") or {}).get("used") or {})
    frames = [m for m in metas if m["type"] == "frame"]
    assert frames and not any(k in f for f in frames for k in rec.FRAME_TIMING)  # no wall clock, no CPU time


def _with_checks(monkeypatch, checks_at):
    """The toy world emits the given checks at its frames: {frame number: [check meta]}."""
    sim = registry.load("u98_site_toy")["simulation"]
    orig = sim.frame

    def frame(self):  # counted per world: each recording builds its own
        k = self.__dict__.setdefault("_test_k", 0)
        for c in checks_at.get(k, []):
            self.emit({"type": "check", "t": self.t, "label": "a check", "unit": "", "note": "", **c})
        self._test_k = k + 1
        return orig(self)

    monkeypatch.setattr(sim, "frame", frame)


def test_a_check_that_ends_failed_fails_the_recording(rec, monkeypatch, tmp_path):
    """D5: a check whose last state is ✗ fails the recording (no file, a problem named); a ✗ on purpose (expected) or a
    ✗ that a later version of the check turns into ✓ does not; the index counts the last states."""
    _with_checks(monkeypatch, {3: [{"id": "c1", "value": 1.0, "ref": 2.0, "rel": -0.5, "tol": 1e-9}]})
    with pytest.raises(rec.RecordingFailed, match="c1"):
        rec.record("u98_site_toy", _spec("slow"))
    index, problems = rec.record_world("u98_site_toy", tmp_path, only=["slow"])
    assert any("check(s) end failed" in p and "u98_site_toy/slow" in p for p in problems)
    assert not [e for e in index["recordings"] if e["id"] == "slow"]


def test_a_check_failed_on_purpose_or_corrected_later_does_not_fail(rec, monkeypatch, tmp_path):
    _with_checks(monkeypatch, {
        2: [{"id": "c1", "value": 1.0, "ref": 2.0, "rel": -0.5, "tol": 1e-9}],
        5: [{"id": "c1", "value": 2.0, "ref": 2.0, "rel": 0.0, "tol": 1e-9},
            {"id": "c2", "ok": False, "expected": "a what-if world"},
            {"id": "c3", "value": 1.0, "ref": None, "rel": None},
            {"id": "c4", "value": 1.0, "info": True}]})
    index, problems = rec.record_world("u98_site_toy", tmp_path, only=["slow"])
    assert problems == []
    e = next(e for e in index["recordings"] if e["id"] == "slow")
    assert e["checks"] == {"ok": 1, "failed": 0, "expected": 1, "info": 1, "na": 1}


def test_a_kept_old_entry_is_current_or_dropped(rec, tmp_path):
    """F9: a recording not made now keeps its old entry only when its key is the current one, with its own date, code
    and version; a stale one is dropped, so the index's code and date never name a file made by other code."""
    rec.record_world("u98_site_toy", tmp_path)
    folder = tmp_path / "u98_site_toy"
    idx = json.loads((folder / "index.json").read_text(encoding="utf-8"))
    fast = next(e for e in idx["recordings"] if e["id"] == "fast")
    assert {"version", "code_hash", "made"} <= set(fast) and fast["code_hash"] == idx["code_hash"]
    fast["made"] = "2000-01-01T00:00:00+00:00"
    (folder / "index.json").write_text(json.dumps(idx), encoding="utf-8")
    index, _ = rec.record_world("u98_site_toy", tmp_path, only=["slow"])
    kept = next(e for e in index["recordings"] if e["id"] == "fast")
    assert kept["made"] == "2000-01-01T00:00:00+00:00" and kept["key"] == fast["key"]
    idx = json.loads((folder / "index.json").read_text(encoding="utf-8"))
    next(e for e in idx["recordings"] if e["id"] == "fast")["key"] = "0" * 16  # made by other code
    (folder / "index.json").write_text(json.dumps(idx), encoding="utf-8")
    index, _ = rec.record_world("u98_site_toy", tmp_path, only=["slow"])
    assert [e["id"] for e in index["recordings"]] == ["slow"]
    assert sorted(p.name for p in folder.glob("*.lfrec.gz")) == [index["recordings"][0]["file"]]
