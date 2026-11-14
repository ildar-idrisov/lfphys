# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Quantised blobs (``lfviz.protocol``, the ``q`` descriptor; design ``lfphys/sources/explore_2026-11-14_design.md`` §1.3,
§8):

* the shared fixtures ``tests/site_worlds/quant/cases.{lfrec,json}`` decode in Python to the float32 bit patterns the
  JSON states (``player/js/api.js decode`` is held to the same file by the player's tests), and the fixture is what
  ``tests/site_worlds/make_fixture.py`` makes now;
* the decoding is the formula of the module's docstring, element by element, in double then float32 (u1 and u2, lin
  and sqrt, one range and per-column ranges, NaN codes);
* the round trip's error is within the stated ``max_err`` and within half a step of the written range; the ranges are
  written short and contain the data; an integer blob that fits is stored unchanged; ``raw`` gives the codes;
* the registry's encodings and keys.
"""

from __future__ import annotations

import importlib.util
import json
import math

import numpy as np
import pytest

from lfviz import protocol, registry

QDIR = registry.ROOT / "tests" / "site_worlds" / "quant"


def _maker():
    spec = importlib.util.spec_from_file_location("lf_make_fixture", QDIR.parent / "make_fixture.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _bits(a):
    return ["%08x" % x for x in np.ascontiguousarray(a, dtype=np.float32).view(np.uint32).ravel()]


def test_the_shared_fixture_decodes_to_its_stated_bits():
    data = (QDIR / "cases.lfrec").read_bytes()
    expect = json.loads((QDIR / "cases.json").read_text(encoding="utf-8"))
    msgs = [protocol.decode(m) for _o, m in protocol.iter_stream(data, len(protocol.MAGIC))]
    assert len(msgs) == len(expect) >= 9
    kinds = set()
    for (meta, blobs), e in zip(msgs, expect):
        assert meta["case"] == e["case"]
        for name, want in e["blobs"].items():
            got = blobs[name]
            assert list(got.shape) == want["shape"]
            if want["bits"] is not None:
                assert got.dtype == np.float32 and _bits(got) == want["bits"], (e["case"], name)
            else:
                assert [float(x) for x in got.ravel()] == want["values"]
        for d in meta.get("blobs") or []:
            if d.get("q"):
                kinds.add((d["dtype"], d["q"]["enc"], isinstance(d["q"]["lo"], list), bool(d["q"].get("nan"))))
    assert {("u2", "lin", True, False), ("u1", "lin", True, False), ("u2", "lin", False, False),
            ("u1", "sqrt", False, False), ("u2", "sqrt", False, False), ("u2", "lin", False, True),
            ("u1", "sqrt", False, True)} <= kinds


def test_the_fixture_is_what_the_maker_makes_now():
    mk = _maker()
    msgs = [protocol.encode(m, b) for m, b in mk.quant_cases()]
    assert protocol.MAGIC + b"".join(protocol.frame_stream_item(m) for m in msgs) == (QDIR / "cases.lfrec").read_bytes()


def _formula(codes, dtype, q):
    """The docstring's decoding, one element at a time in Python floats (IEEE double), then float32."""
    M = 255 if dtype == "u1" else 65535
    top = M - 1 if q.get("nan") else M
    shape = codes.shape
    flat = codes.ravel()
    ncol = shape[-1] if shape else 1
    out = np.empty(flat.size, dtype=np.float32)
    for k, v in enumerate(flat.tolist()):
        lo = q["lo"][k % ncol] if isinstance(q["lo"], list) else q["lo"]
        hi = q["hi"][k % ncol] if isinstance(q["hi"], list) else q["hi"]
        if q.get("nan") and v == M:
            out[k] = np.nan
            continue
        r = v / top
        x = lo + r * (hi - lo) if q["enc"] == "lin" else hi * (r * r)
        out[k] = np.float32(x)
    return out.reshape(shape)


@pytest.mark.parametrize("enc", ["u16", "u8", "u8sqrt", "u16sqrt", "u16:all", "u8:col"])
def test_decoding_is_the_stated_formula_and_within_the_stated_error(enc):
    rng = np.random.default_rng(7)
    a = np.column_stack([rng.normal(10, 3, 200), rng.uniform(0, 1e-4, 200), np.full(200, -2.25)])
    if "sqrt" in enc:
        a = np.abs(a)
    a[5, 0] = np.nan
    qb = protocol.quantize(a, enc)
    msg = protocol.encode({"type": "x"}, {"a": qb})
    meta, blobs = protocol.decode(msg)
    d = meta["blobs"][0]
    raw = protocol.decode(msg, raw=True)[1]["a"]
    assert d["dtype"] == ("u1" if enc.startswith("u8") else "u2") and raw.dtype == np.dtype(d["dtype"])
    got = blobs["a"]
    want = _formula(raw, d["dtype"], d["q"])
    assert _bits(got) == _bits(want)
    assert np.isnan(got[5, 0]) and d["q"]["nan"] is True
    percol = enc in ("u16", "u8", "u8:col") or (enc in ("u8sqrt", "u16sqrt"))
    assert isinstance(d["q"]["lo"], list) == percol
    err = np.abs(got.astype(np.float64) - a)
    fin = np.isfinite(a)
    mx = np.where(fin, err, 0).max(axis=0)
    stated = np.broadcast_to(np.asarray(qb.max_err, dtype=np.float64), mx.shape)
    assert np.all(mx <= stated * (1 + 1e-12) + 1e-300)
    lo = np.broadcast_to(np.asarray(d["q"]["lo"], dtype=np.float64), (3,))
    hi = np.broadcast_to(np.asarray(d["q"]["hi"], dtype=np.float64), (3,))
    top = (255 if d["dtype"] == "u1" else 65535) - 1
    if d["q"]["enc"] == "lin":  # half a step of the written range, and float32's rounding
        assert np.all(mx <= (hi - lo) / top / 2 * (1 + 1e-9) + np.abs(np.nanmax(np.abs(a), axis=0)) * 2 ** -23)
        assert np.all(lo <= np.nanmin(a, axis=0)) and np.all(hi >= np.nanmax(a, axis=0))
    for v in list(lo) + list(hi):  # written short
        assert len(repr(float(v))) <= 12 or v == -2.25


def test_a_constant_range_decodes_exactly_and_an_integer_blob_is_kept():
    a = np.full((4, 2), 0.1234567890123)
    qb = protocol.quantize(a, "u16")
    _m, b = protocol.decode(protocol.encode({"type": "x"}, {"a": qb}))
    assert np.all(b["a"] == np.float32(0.1234567890123))
    flags = np.array([0, 1, 3, 255], dtype=np.uint8)
    assert protocol.quantize(flags, "u8") is flags
    assert isinstance(protocol.quantize(np.array([0, 300]), "u8"), protocol.Quantized)
    _m, b = protocol.decode(protocol.encode({"type": "x"}, {"a": protocol.quantize(np.zeros(0), "u16")}))
    assert b["a"].shape == (0,)


def test_a_range_is_widened_little_and_written_short():
    lo, hi = protocol._short_range(np.array([0.123456789, -3.1415926]), np.array([0.987654321, 2.7182818]))
    assert lo[0] <= 0.123456789 and hi[0] >= 0.987654321 and lo[1] <= -3.1415926 and hi[1] >= 2.7182818
    assert (hi[0] - lo[0]) <= (0.987654321 - 0.123456789) * (1 + 2.5e-3)
    assert all(len(repr(float(x))) <= 9 for x in (*lo, *hi))
    assert protocol._short_range(np.float64(5.0), np.float64(5.0)) == (5.0, 5.0)
    assert math.isclose(protocol.dequantize(np.array([65535], np.uint16), "u2", {"enc": "sqrt", "lo": 0, "hi": 4.0})[0], 4.0)


def test_the_registry_knows_the_encodings_and_the_keys():
    assert registry._check_quantize({"traj.s": "u16", "detections.t|x": "u16", "segment.map": "u8sqrt",
                                     "header.x": "u16:col", "a.b": "u8:all"}) == []
    bad = registry._check_quantize({"traj": "u16", "traj.s": "f16", "Traj.s": "u8", "a.b|": "u8"})
    assert len(bad) == 4
    assert registry.quantize_items({"detections.t|x": "u16"}) == [("detections", "t", "u16"), ("detections", "x", "u16")]
    assert registry._quant_safe("u16", "u8") and registry._quant_safe("u16sqrt:col", "u8sqrt")
    assert not registry._quant_safe("u8", "u16") and not registry._quant_safe("u8sqrt", "u8") \
        and not registry._quant_safe("u16", None)
