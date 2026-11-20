# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The bench's readings as Lab work takes them (``player/js/lab.js``), in Python, for the tests of the ways
(``test_u35_screens.py``): a point of an atlas is run as ``site/atlas.py`` runs it (``run_point``: the screen's preset,
fixed values, grid values, seed, clock and stop), its frame at the cursor is read by the step's instruments (a counter
N ± √N, one count for N = 0; a set-up value or the counter's clock exact), the step's columns are evaluated with
``lfviz.expr`` (the same grammar and error propagation as ``player/js/expr.js``) and fitted by
``lfphys.tools.stats.linear_fit`` (York for lines, the effective variance for the parabola, as ``fit.js``)."""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

from lfviz import expr, registry

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "site"))
import atlas as A  # noqa: E402

V = "u35_optics_bench"
VIZ = registry.load(V)
SPECS = {a["id"]: a for a in registry.atlases_of(VIZ)}
LAB = next(s for s in VIZ["screens"] if s["kind"] == "lab")
STEPS = {s["id"]: s for s in LAB["steps"]}


def atlas_of(step_id: str) -> str:
    st = STEPS[step_id]
    return st.get("atlas") or f"lab.{step_id}"


@lru_cache(maxsize=None)
def _run(aid: str, key: tuple):
    msgs, oc = A.run_point(V, SPECS[aid], dict(key))
    frames = [m for m, _b in msgs if m["type"] == "frame"]
    header = next(m for m, _b in msgs if m["type"] == "header")
    segs = [m for m, _b in msgs if m["type"] == "segment"]
    return frames, header, oc, segs


def point(aid: str, **values):
    """(frames, header, outcome, segments) of an atlas's point at these grid values (the others at their
    defaults)."""
    spec = SPECS[aid]
    full = {c["param"]: c.get("default", c["values"][0]) for c in spec["controls"]}
    full.update(values)
    return _run(aid, tuple(sorted(full.items())))


def reading(instr: dict, header: dict, frame: dict, values: dict):
    """(value, error) of an instrument at a frame, as lab.js reads it; None when it reads nothing."""
    src = str(instr.get("reads") or "")
    if src.startswith("control:"):
        p = src[8:]
        v = header["params"].get(p, values.get(p))
        d = float(instr["division"])
        return (round(float(v) / d) * d, 0.0 if instr.get("error") == 0 else float(instr.get("error", d / 2)))
    v = (frame.get("meas") or {}).get(src)
    if v is None:
        return None
    if instr["kind"] == "counter":
        n = int(round(v))
        return (float(n), math.sqrt(n) if n > 0 else 1.0)
    d = float(instr["division"])
    return (round(float(v) / d) * d, 0.0 if instr.get("error") == 0 else float(instr.get("error", d / 2)))


def row(step_id: str, frame_index: int = -1, **values) -> dict:
    """The step's table row at a set-up (its columns {id: (value, sigma) or None}) read at a frame (the last: the
    point's end)."""
    st = STEPS[step_id]
    frames, header, _oc, _segs = point(atlas_of(step_id), **values)
    f = frames[frame_index]
    rd = {iid: reading(LAB["instruments"][iid], header, f, values) for iid in st["instruments"]}
    cols: dict = {}
    for c in st["columns"]:
        if "from" in c:
            cols[c["id"]] = rd[c["from"]]
        elif "expr" in c:
            try:
                v, s, _t1, _t2 = expr.evaluate(c["expr"], {k: x for k, x in cols.items() if x is not None})
                cols[c["id"]] = (v, s)
            except (expr.Undefined, expr.ExprError):
                cols[c["id"]] = None
    return cols


def fit(rows: list, x: str, y: str, model: str) -> dict:
    """``linear_fit`` of the rows' columns x, y with their errors (rows with an empty cell are skipped, as lab.js)."""
    from lfphys.tools.stats import linear_fit
    pts = [(r[x], r[y]) for r in rows if r.get(x) is not None and r.get(y) is not None]
    xs = [p[0][0] for p in pts]
    ys = [p[1][0] for p in pts]
    sx = [p[0][1] for p in pts]
    sy = [p[1][1] for p in pts]
    return linear_fit(xs, ys, sx, sy, model=model)


def expected_row(step_id: str, frame_index: int = -1, **values) -> dict:
    """The step's table row on the noise-free expected counts of a set-up (a way's computed outcome, review R2-W F1):
    each detector's input rate is the source's rate × η × the computed probability that a photon reaches it (the
    frame's R_inc_ref, T_inc_ref; 1 for the reference count with the block removed) + the dark rate, thinned by the
    non-paralysable dead time (``photodetector.observed_rate``); the counts are those rates × the counting times, with
    the errors √N, and the formula columns are evaluated on them as on a measured row."""
    from lfphys.theories.models import photodetector as pd
    st = STEPS[step_id]
    frames, header, _oc, _segs = point(atlas_of(step_id), **values)
    p = header["params"]
    m = frames[frame_index]["meas"]
    det = pd.DEVICES[p["det"]]["detector"]
    t, t0 = m["t_c"], float(p["ref_s"])

    def count(prob, tt):
        n = float(p["rate"]) * det.eta * prob + det.dark_rate
        c = float(pd.observed_rate(n, det.dead_time)) * tt
        return (c, math.sqrt(c))
    cols = {"th": (float(p["theta_deg"]), 0.0), "tc": (t, 0.0), "NR": count(m["R_inc_ref"], t),
            "NT": count(m["T_inc_ref"], t), "N0": count(1.0, t0), "t0": (t0, 0.0)}
    for c in st["columns"]:
        if "expr" in c:
            try:
                v, s, _t1, _t2 = expr.evaluate(c["expr"], {k: x for k, x in cols.items() if x is not None})
                cols[c["id"]] = (v, s)
            except (expr.Undefined, expr.ExprError):
                cols[c["id"]] = None
    return cols
