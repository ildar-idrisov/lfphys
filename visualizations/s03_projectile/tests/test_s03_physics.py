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
from s03_projectile.engine.shot import OBJECTS, Shot, curve_flight, optimum_angle  # noqa: E402
from s03_projectile.viz import DEFAULT_LAW, SCHEMA, VIZ, WORKSHEET, Simulation  # noqa: E402

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


def _ref(sid, reference, st=None):
    st = st or _step(sid)[1]
    return Simulation.lab_reference(sid, _params(st), {c["param"]: c["values"] for c in st["controls"]}, reference)


def test_lab_reference_of_every_law_against_an_independent_computation():
    _lab, st = _step("heights")
    assert _params(st)["air"] is False  # part 1 runs without air (review R-E F4, D2)
    ref = _ref("heights", "k_horizontal")
    assert ref["value"] == pytest.approx(1.5 * math.sqrt(2 / 9.80665), rel=1e-15) and ref["kind"] == "closed form"
    assert ref["unit"].msgid == "m^½"
    # the air's effect is computed for every height and the sentence is true at every height (review R-E F4)
    hs = st["controls"][0]["values"]
    short = [Shot("steel20", h, 1.5, 0.0, False).L - Shot("steel20", h, 1.5, 0.0, True).L for h in hs]
    a = ref["how"].args
    assert a["a"] == pytest.approx(1e3 * short[0], rel=1e-12) and a["b"] == pytest.approx(1e3 * short[-1], rel=1e-12)
    assert a["h0"] == hs[0] and a["h1"] == hs[-1] and a["e"] == 0.5
    assert all(np.diff(short) > 0)  # the effect grows with the height, so «from h = … on» is exact
    over = [h for h, d in zip(hs, short) if d > 0.0005]
    assert over and a["h2"] == over[0] == 0.95 and "from h = {h2:.2f} m on" in ref["how"].msgid
    ref = _ref("angles", "v2_over_g")
    assert ref["value"] == pytest.approx(25.0 / 9.80665, rel=1e-15) and ref["unit"].msgid == "m"
    ref = _ref("angles", "theta_max_vacuum")
    assert ref["value"] == 45.0 and optimum_angle("steel20", 0.0, 5.0, False, 0.1)[0] == 45.0
    assert _ref("air", "theta_max_vacuum")["value"] == 45.0
    ref = _ref("air", "theta_max_air")
    # the second method: the hodograph quadrature's range maximised by Brent's method (no time integration)
    k = dq.QuadraticDrag.sphere(OBJECTS["ball67"]["d"]).k(OBJECTS["ball67"]["m"])
    best = optimize.minimize_scalar(lambda a: -dq.hodograph(20.0, math.radians(a), 0.0, k, G)["L"],
                                    bounds=(35.0, 48.0), method="bounded", options={"xatol": 1e-6}).x
    assert ref["kind"] == "engine" and abs(ref["value"] - best) <= 0.05 + 1e-9, (ref["value"], best)
    # the optimum depends on the drag model (review R-E F1, D1): the measured curve's optimum is stated beside it
    best_c = optimize.minimize_scalar(lambda a: -curve_flight("ball67", 0.0, 20.0, a).range, bounds=(38.0, 46.0),
                                      method="bounded", options={"xatol": 1e-4}).x
    assert ref["value"] == 41.9 and ref["how"].args["b"] == 42.3 and abs(ref["how"].args["b"] - best_c) <= 0.05 + 1e-3
    assert DEFAULT_LAW == {"heights": "k_horizontal", "angles": "v2_over_g", "air": "theta_max_air"}
    st_air = _step("air")[1]
    assert Simulation.lab_reference("air", _params(st_air), {})["value"] == ref["value"]  # no reference: the first law
    with pytest.raises(ValueError):
        Simulation.lab_reference("nothing", _params(st), {})
    with pytest.raises(ValueError):
        Simulation.lab_reference("heights", _params(st), {}, "theta_max_air")


def _reading(value, inst):
    return inst["division"] * round(value / inst["division"])


def _table(sid):
    """What a student does on the screen, done on the world's computed points: every grid value measured with the
    step's instruments (a reading rounded to the division, its error the declared one), the derived columns with
    errors propagated."""
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
                if i.get("manual"):
                    continue
                row[c["id"]] = (_reading(meas[i["reads"]], i), i["division"] / 2 if i.get("error") is None else i["error"])
            else:
                x, sx = row[c["of"]]
                if c["op"] == "sqrt":
                    row[c["id"]] = (math.sqrt(x), sx / (2 * math.sqrt(x)))
                elif c["op"] == "sin2":
                    a = math.radians(2 * x)
                    row[c["id"]] = (math.sin(a), abs(2 * math.cos(a)) * math.radians(sx))
        rows.append(row)
    return st, p, rows


def _fit(rows, law):
    x = np.array([r[law["x"]][0] for r in rows])
    sx = np.array([r[law["x"]][1] for r in rows])
    y = np.array([r[law["y"]][0] for r in rows])
    sy = np.array([r[law["y"]][1] for r in rows])
    fit = linear_fit(x, y, sx, sy, law["model"])
    return (fit["vertex"], fit["vertex_sigma"]) if law["quantity"] == "vertex" else (fit["params"][-1], fit["sigma"][-1])


@pytest.mark.parametrize("sid", ["heights", "angles", "air"])
def test_the_lab_measurement_and_fit_on_the_computed_points_agree_with_every_law(sid):
    """Each law of the step (its x, y and model, review D4) fitted on the student's table (lfphys.tools.stats.linear_fit,
    the player's fit.js contract): «Check against the law», the fitted quantity within two errors of the reference."""
    st, p, rows = _table(sid)
    assert (st["plot"]["x"], st["plot"]["y"], st["plot"]["fit"]) == \
        (st["laws"][0]["x"], st["laws"][0]["y"], st["laws"][0]["model"])
    for law in st["laws"]:
        ref = _ref(sid, law["reference"], st)["value"]
        got, sig = _fit(rows, law)
        assert abs(got - ref) <= 2 * sig, (sid, law["reference"], got, sig, ref)
    if sid == "heights":  # the stand sets the heights exactly (D2)
        assert all(r["h"][1] == 0.0 and r["sqrt_h"][1] == 0.0 for r in rows)
    if sid == "air":  # the maximum in air is measurably lower than the grey ball's 45°
        got, sig = _fit(rows, st["laws"][0])
        assert got < 45.0 - 2 * sig


def test_part_1_with_air_would_be_seen_by_the_exact_bench():
    """Why part 1 runs without air (review R-E F4, D2): with the heights exact, the tape resolves the air's −0.08 %."""
    st, p, _rows = _table("heights")
    hs = st["controls"][0]["values"]
    L = np.array([_reading(Shot("steel20", h, 1.5, 0.0, True).L, {"division": 0.001}) for h in hs])
    fit = linear_fit(np.sqrt(hs), L, 0.0, 0.0005, "line0")
    z = (fit["params"][-1] - 1.5 * math.sqrt(2 / G)) / fit["sigma"][-1]
    assert z < -2.5, z


# --- the worksheet's numbers (review R-E F11, R-W F7a) -------------------------------------------------------------------
def _text(msgid_start, items):
    hits = [x for x in items if x.msgid.startswith(msgid_start)]
    assert len(hits) == 1, msgid_start
    return hits[0].msgid


def test_the_worksheets_numbers_are_the_engines():
    qs = WORKSHEET["questions"]
    hs = _step("heights")[1]["controls"][0]["values"]
    ts = [Shot("steel20", h, 1.5, 0.0, False).T for h in hs]
    # Q1: «the flight lasts 0.2–0.45 s»; «0.1 s: from a fifth to a half of the whole flight»
    assert "0.2–0.45 s" in qs[0]["q"].msgid and round(min(ts), 1) == 0.2 and round(max(ts), 2) == 0.45
    assert "from a fifth to a half" in qs[0]["answer"].msgid
    assert 0.19 <= 0.1 / max(ts) <= 0.25 and 0.45 <= 0.1 / min(ts) <= 0.55
    # the stopwatch question (review R-W F6): «0.1 s … 0.2–0.45 s … neighbouring heights 5 cm apart differ by only
    # 0.01–0.02 s … averaging 10 runs … about 0.03 s»
    sw = next(q for q in qs if "hand stopwatch. Compare" in q["q"].msgid)["answer"].msgid
    steps = np.diff(ts)
    assert np.allclose(np.diff(hs), 0.05) and round(min(steps), 2) == 0.01 and round(max(steps), 2) == 0.02
    assert "0.01–0.02 s" in sw and "0.2–0.45 s" in sw and "about 0.03 s" in sw and round(0.1 / math.sqrt(10), 2) == 0.03
    lab = _step("heights")[0]
    assert lab["instruments"]["stopwatch"]["error"] == 0.1 and "about 0.1 s" in sw
    assert [c["id"] for c in _step("heights")[1]["columns"]] == ["h", "L", "sqrt_h", "T"]
    # the grey ball's tape reads at its own landing (review R-P F18), the event the world emits for it
    assert lab["instruments"]["tape_grey"]["event"] == "companion_landing"
    h = _run("air_max")
    assert [e["kind"] for e in h.of("event")].count("companion_landing") == 1
    # «near 42°»
    best = optimum_angle("ball67", 0.0, 20.0, True, 0.1)[0]
    assert "near 42°" in next(q for q in qs if q["q"].msgid.startswith("Part 3: why does the maximum"))["answer"].msgid
    assert round(best) == 42
    notes = WORKSHEET["teacher"]
    # part 1: the chute's speed and k
    assert notes[0].args == {"v": 1.5, "k": 1.5 * math.sqrt(2 / G)}
    # «in part 1 it would shorten the range by up to 0.54 mm (0.08 %, at 1 m), more than the tape's error of 0.5 mm at
    # the largest heights; in part 2 the slope would be about 0.5 % lower»
    m = _text("Parts 1 and 2 are computed without air", notes)
    vac1, air1 = Shot("steel20", 1.0, 1.5, 0.0, False).L, Shot("steel20", 1.0, 1.5, 0.0, True).L
    assert "up to 0.54 mm (0.08 %, at 1 m)" in m and round(1e3 * (vac1 - air1), 2) == 0.54
    assert round(100 * (1 - air1 / vac1), 2) == 0.08 and max(hs) == 1.0
    assert vac1 - air1 > 0.0005 > Shot("steel20", 0.2, 1.5, 0.0, False).L - Shot("steel20", 0.2, 1.5, 0.0, True).L
    angles = _step("angles")[1]["controls"][0]["values"]
    s2 = np.sin(np.radians(2 * np.array(angles, float)))
    sl = [linear_fit(s2, np.array([Shot("steel20", 0.0, 5.0, a, air).L for a in angles]), 0.0, 0.0005, "line0")["params"][-1]
          for air in (False, True)]
    assert "about 0.5 % lower" in m and 0.45 <= 100 * (1 - sl[1] / sl[0]) <= 0.55
    # part 3: «41.9° … 42.3° … its vertex agrees with the world's optimum within one error … peaks at 45°»
    m = _text("Part 3: the best angle in air depends on the drag model", notes)
    ref = _ref("air", "theta_max_air")
    assert "gives 41.9°" in m and ref["value"] == 41.9 and "gives 42.3°" in m and ref["how"].args["b"] == 42.3
    st, _p, rows = _table("air")
    got, sig = _fit(rows, st["laws"][0])
    assert "within one error" in m and abs(got - ref["value"]) <= sig, (got, sig)
    got_v, sig_v = _fit(rows, st["laws"][1])
    assert "peaks at 45°" in m and abs(got_v - 45.0) <= 2 * sig_v
    # grade 7: «four times higher (0.25 m → 1.00 m) gives twice the range»; «from 0.339 m to 0.677 m»
    L25, L100 = Shot("steel20", 0.25, 1.5, 0.0, False).L, Shot("steel20", 1.0, 1.5, 0.0, False).L
    assert L100 / L25 == pytest.approx(2.0, rel=1e-12) and 0.25 in hs and 1.0 in hs
    g7 = WORKSHEET["variants"][0]
    assert g7["id"] == "grade7" and g7["steps"] == ["heights"] and g7["plot"]["heights"] == {"x": "h", "y": "L", "fit": None}
    assert "√h" not in g7["goals"]["heights"].msgid and "air is switched off" in g7["goals"]["heights"].msgid
    ans = g7["questions"][1]["answer"].msgid
    assert f"from {L25:.3f} m to {L100:.3f} m" in ans and "only doubles" in ans
    assert "0.25 m → 1.00 m" in _text("Grade 7", notes)


# --- the world's own messages (reviews R-E F1, R-W F8; D1, D10) -------------------------------------------------------------
def test_the_drag_model_is_checked_where_it_is_used_and_compared_with_the_measured_curve():
    h = _run(None, {"object": "ball67", "h_m": 0.0, "v0": 20.0, "angle_deg": 40.0, "air": True})
    cs = h.checks()
    assert cs["main.cd"]["label"]["$t"] == "the drag model's range of validity (Re)" and cs["main.cd"]["ok"]
    cc = cs["main.cd_curve"]
    assert cc.get("info") and cc["ref"] == h.sim.main.L
    # the review's own number (R-E F1, d_energy_validity.out): 28.2371 m with the measured curve against 27.2222 m
    assert cc["value"] == pytest.approx(28.2371, abs=5e-5) and h.sim.main.L == pytest.approx(27.2222, abs=5e-5)
    assert cc["note"]["a"]["d"] == pytest.approx(100 * (cc["value"] / cc["ref"] - 1), rel=1e-12)
    # a vertical throw compares the flight time
    h = _run(None, {"object": "ball67", "h_m": 3.0, "v0": 10.0, "angle_deg": 90.0, "air": True})
    cc = h.checks()["main.cd_curve"]
    assert cc["unit"] == "s" and cc["ref"] == h.sim.main.T and cc["value"] > 0


def test_the_engine_modules_and_the_events_reveal_no_lab_value():
    h = _run("chute", {"air": False})
    assert h.sim.engine_modules() == ["core.mechanics.particle", "theories.models.drag_quadratic", "core.data:air"]
    eng = h.of("header")[0]["engine"]
    assert [d["id"] for d in eng if d["id"].startswith("core.data")] == ["core.data:air"]
    # an event's text carries no measured value: the lab's instruments measure them (D10)
    for e in h.of("event"):
        assert not e["text"].get("a"), e["text"]
    h = _run("story")
    assert {e["text"]["$t"] for e in h.of("event")} == {"the ball lands", "the dropped ball lands"}


# --- the Watch's story ------------------------------------------------------------------------------------------------
def test_the_watch_story_says_what_the_run_computes():
    recs = {r["id"]: r for r in VIZ["recordings"]}
    watch = next(s for s in VIZ["screens"] if s["kind"] == "watch")
    assert watch["recording"] == "independence" and watch["more"] == ["air"]
    rec = recs["independence"]
    base = SCHEMA.presets["story"]["params"]
    w1 = (Shot("steel20", 1.25, 2.0, 0.0, False), Shot("steel20", 1.25, 0.0, 0.0, False))
    w2 = (Shot("steel20", 1.25, 4.0, 0.0, False), Shot("steel20", 1.25, 0.0, 0.0, False))
    w3 = Shot("steel20", 5.0, 4.0, 0.0, False)
    assert base["h_m"] == 1.25 and base["v0"] == 2.0 and not base["air"]
    assert w1[0].T == pytest.approx(w1[1].T, rel=1e-12) and w2[0].T == pytest.approx(w2[1].T, rel=1e-12)
    assert w2[0].L == pytest.approx(2 * w1[0].L, rel=1e-12)  # twice the speed: twice as far, the same moment
    assert w3.T == pytest.approx(2 * w2[0].T, rel=1e-12) and w3.L == pytest.approx(2 * w2[0].L, rel=1e-12)
    # one box for the three throws (D8): from a table, h ≤ 5 m, L ≤ 4.1 m
    assert max(w.L for w in (w1[0], w2[0], w3)) < 4.1
    # each flight ends before the next world starts, and the last one before the recording ends
    starts = [0.0] + [c["at"] for c in rec["script"] if c["cmd"] == "new_world"] + [rec["seconds"]]
    flights = [w1[0].T, w2[0].T, w3.T]
    for k in range(3):
        assert starts[k] + flights[k] / rec["speed"] < starts[k + 1] - 0.5, (k, starts, flights)
    caps = rec["captions"]
    assert [c["at"] for c in caps][2:] == starts[1:3]
    # a caption comes no later than what it describes (review R-W F4): «at every moment both balls are at the same
    # height» while they fall, long before the landing
    assert caps[1]["at"] * rec["speed"] < 0.25 * w1[0].T and caps[0].get("hold")
    air = recs["air"]
    pa = SCHEMA.presets[air["preset"]]["params"]
    a, v = Shot("ball67", 0.0, pa["v0"], pa["angle_deg"], True), Shot("ball67", 0.0, pa["v0"], pa["angle_deg"], False)
    assert a.L < 0.8 * v.L and a.H < v.H  # «rises lower and falls short of the grey one»
    assert air["captions"][0]["text"].args == {"v": pa["v0"], "a": pa["angle_deg"]}
    assert air["captions"][1]["at"] * air["speed"] < a.t_apex and v.T / air["speed"] < air["seconds"] - 0.5
