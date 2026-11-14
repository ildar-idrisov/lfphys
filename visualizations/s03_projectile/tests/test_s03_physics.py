# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""S03 projectile: the run as a whole (every preset, the checks at the corners of every atlas, the events against the
engine, causality, the refusals, the companions), the laws of the lab's steps against independent computations, the
lab's measurement and fit on the computed points (design lfphys/sources/explore_2026-11-14_design.md §5, §8), and the
statements of the Watch's captions."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import optimize

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.mechanics import G_STANDARD as G  # noqa: E402
from lfphys.theories.models import drag_quadratic as dq  # noqa: E402
from lfphys.tools.stats import linear_fit  # noqa: E402
from lfviz import headless, registry  # noqa: E402
from s03_projectile.engine.shot import OBJECTS, Shot  # noqa: E402
from s03_projectile.viz import SCHEMA, VIZ, Simulation  # noqa: E402

V = "s03_projectile"


def _bad(checks):
    return [(c["id"], c.get("value"), c.get("ref"), c.get("rel"), c.get("tol")) for c in checks
            if headless.check_state(c) == "failed"]


def _run(preset=None, params=None, t=12.0):
    h = Harness(V, preset, params)
    h.run_to(t)
    h.runner._frame(0.0)
    return h


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_runs_and_all_checks_pass(preset):
    h = _run(preset)
    assert not h.errors(), h.errors()
    cs = list(h.checks().values())
    assert len(cs) >= 3 and not _bad(cs), _bad(cs)
    assert h.of("header")[0]["engine"], "the engine modules are listed"
    assert [e["kind"] for e in h.of("event")].count("landing") == 1


def _corners(spec):
    """Every combination of the first and the last value of each control."""
    out = [{}]
    for c in spec["controls"]:
        vals = c["values"]
        out = [{**o, c["param"]: v} for o in out for v in dict.fromkeys([vals[0], vals[-1]])]
    return out


@pytest.mark.parametrize("spec", registry.atlases_of(VIZ), ids=lambda s: s["id"])
def test_every_check_passes_at_the_corners_of_every_atlas(spec):
    """Each corner of each atlas runs headless as the site's build runs it (its stop rule), with every check ✓ (a
    refused corner is refused by the world, never failed)."""
    n_ok = 0
    for values in _corners(spec):
        try:
            oc = headless.run_spec(V, spec["preset"], {**spec["fixed"], **values}, spec["seed"],
                                   {"frame_dt": spec["frame_dt"]}, spec["stop"], end_reason="atlas")
        except headless.PointRefused:
            assert values.get("h_m", 1) == 0.0, values
            continue
        counts = oc.check_counts()
        assert counts["failed"] == 0 and counts["ok"] >= 3, (values, counts)
        n_ok += 1
    assert n_ok


def test_the_events_carry_the_engines_values_and_come_when_the_time_reaches_them():
    p = {"object": "ball67", "h_m": 2.0, "v0": 12.0, "angle_deg": 35.0, "air": True}
    shot = Shot("ball67", 2.0, 12.0, 35.0, True)
    h = Harness(V, None, p)
    dt = 1 / 30
    k = 0
    while h.sim.t < shot.T + 0.2:
        k += 1
        h.run_to(k * dt)
        h.runner._frame(0.0)
    ev = {e["kind"]: e for e in h.of("event")}
    assert ev["landing"]["data"]["L"] == shot.L and ev["landing"]["data"]["T"] == shot.T
    assert ev["apex"]["data"]["H"] == shot.flight.apex["y"] and ev["apex"]["t"] == shot.t_apex
    # causality: a message is emitted in the frame whose time has reached it; the samples are revealed no earlier
    t_frame = 0.0
    for m, b in h.msgs:
        if m["type"] == "frame":
            t_frame = m["t"]
        elif m["type"] in ("traj", "event", "check") and m.get("t") is not None:
            assert m["t"] <= h.sim.t + 1e-12
        if m["type"] == "traj":
            assert float(np.max(b["s"][:, 0])) <= m["t"] + 1e-12
    frames = h.of("frame")
    before = [f for f in frames if f["t"] < shot.T]
    after = [f for f in frames if f["t"] >= shot.T]
    assert all(f["meas"]["range"] is None for f in before) and all(f["meas"]["range"] == shot.L for f in after)
    assert all(f["meas"]["apex_h"] is None for f in frames if f["t"] < shot.t_apex)
    # the samples, all of them sent, are the engine's at exact multiples of 1/60 s
    s = np.vstack([b["s"] for m, b in h.msgs if m["type"] == "traj" and m["body"] == "main"])
    assert np.array_equal(s[:, 0], np.arange(len(s)) / 60.0)
    assert np.allclose(s[:, 1:], shot.flight.sample(60.0)["r"], rtol=0, atol=1e-12)


def test_the_refusals_say_why():
    for p in ({"h_m": 0.0, "angle_deg": 0.0}, {"h_m": 0.0, "angle_deg": -10.0}, {"h_m": 0.0, "v0": 0.0},
              {"h_m": 0.0, "companion": "drop"}, {"companion": "vacuum", "air": False}):
        params, errs = SCHEMA.resolve("field", p)
        assert not errs
        with pytest.raises(ValueError):
            Simulation.check_params(params)
    params, _ = SCHEMA.resolve("field", {"h_m": 1.0, "angle_deg": -30.0, "v0": 0.0})
    Simulation.check_params(params)  # a drop from 1 m: a flight


@pytest.mark.parametrize("air", [False, True])
def test_the_dropped_ball_and_the_independence_of_the_motions(air):
    h = _run("story", {"air": air})
    cs = h.checks()
    tf = cs["other.T"]
    ref = math.sqrt(2 * 1.25 / G) if not air else dq.fall_time(1.25, Shot("steel20", 1.25, 0, 0, True).k, G)
    assert tf["ref"] == pytest.approx(ref, rel=1e-15) and abs(tf["rel"]) < 1e-9
    same = cs["other.same_height"]
    if air:  # the thrown ball's drag has an upward part growing with its whole speed: it lands a little later
        assert same.get("info") and same["value"] > 0
        assert h.sim.main.T > h.sim.other.T
    else:
        assert same["ok"] and same["value"] < 1e-12
        assert h.sim.main.T == pytest.approx(h.sim.other.T, rel=1e-12)


def test_vertical_throws_against_the_closed_forms_of_vertical_motion():
    for v0, ang in ((10.0, 90.0), (0.0, 0.0)):
        h = _run(None, {"object": "ball67", "h_m": 3.0, "v0": v0, "angle_deg": ang, "air": True})
        cs = h.checks()
        assert not _bad(cs.values())
        assert cs["main.L"]["ok"] and abs(cs["main.T"]["rel"]) < 1e-9


def test_the_constant_drag_coefficient_holds_on_the_whole_explore_grid_corners():
    """The light ball's Reynolds numbers on the Explore grid stay in the model's range except near a slow top, where
    the drag does almost no work (the check's share stays far under 1 %)."""
    for v0 in (5.0, 25.0):
        for ang in (5.0, 90.0):
            s = Shot("ball67", 10.0, v0, ang, True)
            val = s.validity()
            assert val["share_outside"] < 1e-3 and val["re_max"] < dq.RE_RANGE[1], (v0, ang, val)


def test_air_moves_the_maximum_visibly_on_the_explore_grid():
    """Design §5.3: in vacuum the range from the floor peaks at 45°, in air below it, visible on the 5° grid."""
    angles = list(range(5, 90, 5))
    vac = [Shot("ball67", 0.0, 25.0, a, False).L for a in angles]
    air = [Shot("ball67", 0.0, 25.0, a, True).L for a in angles]
    assert angles[int(np.argmax(vac))] == 45 and angles[int(np.argmax(air))] < 45
    assert max(vac) == pytest.approx(25.0 ** 2 / G, rel=1e-12)


# --- the lab ---------------------------------------------------------------------------------------------------------
def _step(sid):
    lab = next(s for s in VIZ["screens"] if s["kind"] == "lab")
    return lab, next(s for s in lab["steps"] if s["id"] == sid)


def _params(step):
    return headless.resolve(registry.load(V), step["preset"], step["fixed"])


def test_lab_reference_of_every_step_against_an_independent_computation():
    _lab, st = _step("heights")
    ref = Simulation.lab_reference("heights", _params(st), {"h_m": st["controls"][0]["values"]})
    assert ref["value"] == pytest.approx(1.5 * math.sqrt(2 / 9.80665), rel=1e-15) and ref["kind"] == "closed form"
    _lab, st = _step("angles")
    ref = Simulation.lab_reference("angles", _params(st), {})
    assert ref["value"] == pytest.approx(25.0 / 9.80665, rel=1e-15)
    _lab, st = _step("air")
    ref = Simulation.lab_reference("air", _params(st), {})
    # the second method: the hodograph quadrature's range maximised by Brent's method (no time integration)
    k = dq.QuadraticDrag.sphere(OBJECTS["ball67"]["d"]).k(OBJECTS["ball67"]["m"])
    best = optimize.minimize_scalar(lambda a: -dq.hodograph(20.0, math.radians(a), 0.0, k, G)["L"],
                                    bounds=(35.0, 48.0), method="bounded", options={"xatol": 1e-6}).x
    assert ref["kind"] == "engine" and abs(ref["value"] - best) <= 0.05 + 1e-9, (ref["value"], best)
    with pytest.raises(ValueError):
        Simulation.lab_reference("nothing", _params(st), {})


def _reading(value, inst):
    return inst["division"] * round(value / inst["division"])


@pytest.mark.parametrize("sid", ["heights", "angles", "air"])
def test_the_lab_measurement_and_fit_on_the_computed_points_agree_with_the_law(sid):
    """What a student does on the screen, done here on the world's computed points: every grid value measured with
    the step's instruments (a reading rounded to the division, its error the declared one), the derived columns with
    errors propagated, the default plot fitted with the step's default model (lfphys.tools.stats.linear_fit, the
    player's fit.js contract), and «Check against the law»: the fitted quantity within two errors of the reference."""
    lab, st = _step(sid)
    inst = lab["instruments"]
    p = _params(st)
    ctl = st["controls"][0]
    rows = []
    for v in ctl["values"]:
        q = {**p, ctl["param"]: v}
        s = Shot(q["object"], q["h_m"], q["v0"], q["angle_deg"], q["air"])
        meas = {"range": s.L, "range_vacuum": Shot(q["object"], q["h_m"], q["v0"], q["angle_deg"], False).L,
                "control:h_m": q["h_m"], "control:angle_deg": q["angle_deg"]}
        row = {}
        for c in st["columns"]:
            if "from" in c:
                i = inst[c["from"]]
                row[c["id"]] = (_reading(meas[i["reads"]], i), i["error"])
            else:
                x, sx = row[c["of"]]
                if c["op"] == "sqrt":
                    row[c["id"]] = (math.sqrt(x), sx / (2 * math.sqrt(x)))
                elif c["op"] == "sin2":
                    a = math.radians(2 * x)
                    row[c["id"]] = (math.sin(a), abs(2 * math.cos(a)) * math.radians(sx))
        rows.append(row)
    px, py = st["plot"]["x"], st["plot"]["y"]
    x = np.array([r[px][0] for r in rows])
    sx = np.array([r[px][1] for r in rows])
    y = np.array([r[py][0] for r in rows])
    sy = np.array([r[py][1] for r in rows])
    fit = linear_fit(x, y, sx, sy, st["plot"]["fit"])
    law = st["law"]
    ref = Simulation.lab_reference(sid, p, {c["param"]: c["values"] for c in st["controls"]})["value"]
    got, sig = (fit["vertex"], fit["vertex_sigma"]) if law["quantity"] == "vertex" else (fit["params"][-1], fit["sigma"][-1])
    assert abs(got - ref) <= 2 * sig, (sid, got, sig, ref)
    if sid == "air":  # the grey ball (vacuum) peaks at 45° within its error
        fv = linear_fit(x, np.array([r["L_vac"][0] for r in rows]), sx, 0.0005, "quadratic")
        assert abs(fv["vertex"] - 45.0) <= 2 * fv["vertex_sigma"]
        assert got < 45.0 - 2 * sig  # and the maximum in air is measurably lower


# --- the Watch's story ------------------------------------------------------------------------------------------------
def test_the_watch_story_says_what_the_run_computes():
    rec = VIZ["recordings"][0]
    assert rec["id"] == "independence" and len(rec["captions"]) == 5
    base = SCHEMA.presets["story"]["params"]
    w1 = (Shot("steel20", 1.25, 2.0, 0.0, False), Shot("steel20", 1.25, 0.0, 0.0, False))
    w2 = (Shot("steel20", 1.25, 4.0, 0.0, False), Shot("steel20", 1.25, 0.0, 0.0, False))
    w3 = Shot("steel20", 5.0, 4.0, 0.0, False)
    assert base["h_m"] == 1.25 and base["v0"] == 2.0 and not base["air"]
    assert w1[0].T == pytest.approx(w1[1].T, rel=1e-12) and w2[0].T == pytest.approx(w2[1].T, rel=1e-12)
    assert w2[0].L == pytest.approx(2 * w1[0].L, rel=1e-12)  # twice the speed: twice as far, the same moment
    assert w3.T == pytest.approx(2 * w2[0].T, rel=1e-12) and w3.L == pytest.approx(2 * w2[0].L, rel=1e-12)
    air, vac = Shot("ball67", 0.0, 20.0, 45.0, True), Shot("ball67", 0.0, 20.0, 45.0, False)
    assert air.L < 0.8 * vac.L
    # each flight ends before the next world starts, and the last one before the recording ends
    starts = [0.0] + [c["at"] for c in rec["script"] if c["cmd"] == "new_world"] + [rec["seconds"]]
    speeds = [rec["speed"], 0.1, 0.1, 0.5]
    flights = [w1[0].T, w2[0].T, w3.T, vac.T]
    for k in range(4):
        assert starts[k] + flights[k] / speeds[k] < starts[k + 1] - 0.5, (k, starts, flights)
    assert [c["at"] for c in rec["captions"]][2:] == starts[1:4]
