# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""S03's screens (EX2 design §1.4, §7, §10): every grid point of every atlas builds with every check ✓ and stops by its
rule; the bench is a bench (a task sheet, no questions, the teacher's variants on the grid); every way of the bench
gives its stated outcome on the built atlas (the readings as the instruments make them, fitted by
``lfphys.tools.stats.linear_fit``, the fit the player mirrors); the Watch's captions against the recording, each no
later than what it describes.

The built atlas is read from ``LFVIZ_RECORDINGS`` (or ``visualizations/recordings``) when it is there with the key the
code under test would build (``site/record.py --world s03_projectile``); otherwise its points are computed by the
atlas's own runner (``headless.run_spec``, as ``site/atlas.py`` runs them), which gives the same numbers."""

import gzip
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "site"))
import sitelib  # noqa: E402

from lfphys.core.mechanics import G_STANDARD as G  # noqa: E402
from lfphys.tools.stats import linear_fit  # noqa: E402
from lfviz import headless, registry  # noqa: E402
from s03_projectile.engine import shot as S  # noqa: E402
from s03_projectile.viz import INSTRUMENTS, STEPS, VIZ, WORKSHEET  # noqa: E402

V = "s03_projectile"
REC = Path(os.environ.get("LFVIZ_RECORDINGS") or HERE.parents[2] / "recordings")
SPECS = {s["id"]: s for s in registry.atlases_of(registry.load(V))}


def _grid(spec):
    import itertools
    return [dict(zip([c["param"] for c in spec["controls"]], v))
            for v in itertools.product(*[c["values"] for c in spec["controls"]])]


# --- the registry, the task sheet ------------------------------------------------------------------------------------------
def test_the_bench_is_a_bench_with_a_task_sheet():
    viz = registry.load(V)
    assert not registry.check_screens(viz)
    ws = WORKSHEET
    assert not {"questions", "teacher", "grading", "equipment"} & set(ws)
    assert ws["goal"] and ws["bench"] and ws["procedure"] and ws["record"] and ws["record_rows"] == 17 == len(STEPS[0]["controls"][0]["values"])
    for st in STEPS:  # nothing judged: the laws are data, the plot need not be one of them
        assert st["laws"] and "law" not in st
    # the variants are computed in the atlases: every preselected value is on its step's grid
    for v in ws["variants"]:
        for sid, vals in v.get("values", {}).items():
            st = next(s for s in STEPS if s["id"] == sid)
            for k, x in vals.items():
                assert x in next(c for c in st["controls"] if c["param"] == k)["values"]
    assert [v["id"] for v in ws["variants"]] == ["grade7", "air"]
    # the task sheet's numbers are the steps' and the engine's
    b0 = ws["bench"][0].msgid
    assert "1.5 m/s" in b0 and "0.20–1.00 m" in b0 and "5 m/s at 15–75°" in b0 and "20 m/s at 20–70°" in b0
    hs, a2, a3 = (STEPS[0]["controls"][0]["values"], STEPS[1]["controls"][0]["values"], STEPS[2]["controls"][0]["values"])
    assert (hs[0], hs[-1], a2[0], a2[-1], a3[0], a3[-1]) == (0.2, 1.0, 15, 75, 20, 70)
    assert S.Shot("steel20", 0.6, 1.5, 0.0, False).v0 == 1.5 and STEPS[1]["fixed"]["v0"] == 5.0
    assert STEPS[2]["fixed"]["v0"] == 20.0
    # «up to a tenth of a millimetre in parts 1 and 2 and millimetres in part 3» (the Earth's rotation, either way)
    def shift(s):
        return max(abs(s.x_land - (s.unrotated["L"])), abs(s.side["right"]))
    p12 = [shift(S.Shot("steel20", h, 1.5, 0.0, air)) for h in (0.2, 1.0) for air in (False, True)] + \
        [shift(S.Shot("steel20", 0.0, 5.0, float(a), air)) for a in (15, 30, 55, 75) for air in (False, True)]
    p3 = [shift(S.Shot("ball67", 0.0, 20.0, float(a), True)) for a in a3]
    assert 1e-5 <= max(p12) < 0.11e-3 and 1e-3 <= min(p3) and max(p3) < 1e-2
    assert "up to a tenth of a millimetre in parts 1 and 2 and by millimetres in part 3" in ws["bench"][2].msgid
    # the grade-7 variant compares 0.25 m and 1.00 m: both on the grid
    assert 0.25 in hs and 1.0 in hs and "0.25 m and from 1.00 m" in ws["variants"][0]["text"]["procedure"][0].msgid


# --- every grid point --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("aid", sorted(SPECS))
def test_every_grid_point_builds_with_every_check_ok_and_stops_by_its_rule(aid):
    """Every point of every atlas (Explore 950, part 1 34, part 2 26, part 3 11) runs as the site's build runs it: every
    check ✓ (or information, or no second method: a vertical flight in air), none failed; it stops at its stop event
    plus ``after_s`` (``run_spec`` fails a point whose event is not reached by ``max_world_s``). Only the launches from
    the floor at 0° are refused."""
    spec = SPECS[aid]
    n_ok = n_ref = 0
    for values in _grid(spec):
        try:
            oc = headless.run_spec(V, spec["preset"], {**spec["fixed"], **values}, spec["seed"],
                                   {"frame_dt": spec["frame_dt"]}, spec["stop"], end_reason="atlas")
        except headless.PointRefused:
            assert values.get("h_m", 1) == 0.0 and values.get("angle_deg", 1) == 0.0, values
            n_ref += 1
            continue
        c = oc.check_counts()
        assert c["failed"] == 0 and c["ok"] >= 3, (values, c)
        na = [k[1] for k, st in oc.checks.items() if st == "na"]
        assert all(x in ("main.T", "other.T") for x in na), (values, na)
        assert oc.stop_event_t is not None and oc.t_end == pytest.approx(oc.stop_event_t + spec["stop"]["after_s"],
                                                                         abs=spec["frame_dt"] + 1e-9)
        n_ok += 1
    assert n_ok and n_ref == (10 if aid == "explore" else 0)


# --- the ways of the bench, on the built atlas -------------------------------------------------------------------------
def _built(aid):
    """The built atlas's last frames' measurables by point index, when it is here with the key the code would build;
    else None."""
    try:
        want = next(a["key"] for a in sitelib.planned_world(V)["atlases"] if a["id"] == aid)
        idx = json.loads((REC / V / "index.json").read_text(encoding="utf-8"))
        entry = next(a for a in idx["atlases"] if a["id"] == aid)
        if entry["key"] != want:
            return None
        mf = REC / V / entry["file"]
        man = json.loads(mf.read_text(encoding="utf-8"))
    except (OSError, ValueError, StopIteration, KeyError):
        return None
    pool = headless.read_pool_file((mf.parent / man["pool"]["file"]).read_bytes()) if man.get("pool") else None
    out = {}
    for i, p in enumerate(man["points"]):
        if p and p[0]:
            msgs = headless.read_stream(gzip.decompress((mf.parent / p[0]).read_bytes()), pool=pool)
            out[i] = [m for m, _b in msgs if m.get("type") == "frame"][-1]["meas"]
    return out


def _computed(spec, values):
    last = {}

    def keep(meta, blobs=None):
        if meta.get("type") == "frame":
            last["meas"] = meta["meas"]
    headless.run_spec(V, spec["preset"], {**spec["fixed"], **values}, spec["seed"], {"frame_dt": spec["frame_dt"]},
                      spec["stop"], emit=keep, end_reason="atlas")
    return last["meas"]


_CACHE: dict = {}


def _points(aid):
    """{values (a tuple of the controls' values): the last frame's measurables} of an atlas: the built one when it is
    here (and then also its agreement with the runner), else the runner's."""
    if aid in _CACHE:
        return _CACHE[aid]
    spec = SPECS[aid]
    grid = _grid(spec)
    built = _built(aid)
    out = {}
    for i, values in enumerate(grid):
        key = tuple(values.values())
        if built is not None:
            out[key] = built[i]
        else:
            out[key] = _computed(spec, values)
    _CACHE[aid] = (out, built is not None)
    return _CACHE[aid]


def _read(value, iid):
    """A reading as the lab's instruments make it (lab.js reading): rounded to the division, with the declared error."""
    i = INSTRUMENTS[iid]
    d = i["division"]
    return round(round(value / d) * d, 10), i["error"]


def _sin2(theta, s):
    """The lab's column sin 2θ with its error σ² = f′²σ² + ½f″²σ⁴ (θ, σ in degrees; RULES.md §10)."""
    r = math.pi / 180.0
    return math.sin(2 * theta * r), math.sqrt((2 * math.cos(2 * theta * r) * r * s) ** 2
                                              + 0.5 * (4 * math.sin(2 * theta * r) * r * r * s * s) ** 2)


def _fit(x, y, sx, sy, model):
    f = linear_fit(np.asarray(x, float), np.asarray(y, float), np.asarray(sx, float), np.asarray(sy, float), model)
    if model == "quadratic":
        return f["vertex"], f["vertex_sigma"], f["chi2"] / f["dof"]
    return f["params"][-1], f["sigma"][-1], f["chi2"] / f["dof"]


K = 1.5 * math.sqrt(2.0 / G)  # the chute's k = v₀·√(2/g)
R = 25.0 / G  # the launcher's v₀²/g


def _part1(air):
    pts, built = _points("lab.heights")
    hs = SPECS["lab.heights"]["controls"][0]["values"]
    L = [_read(pts[(h, air)]["range"], "tape")[0] for h in hs]
    p = [_read(pts[(h, air)]["p_air"], "manometer")[0] for h in hs]
    return hs, L, p, built


def test_way_1_L_against_sqrt_h_without_air_gives_the_chutes_speed():
    """[right] The line through the origin of L against √h (the stand's heights exact, the tape ±0.5 mm), air off:
    k = 0.67743 ± 0.00016 m^½, 0.2 errors from k = v₀·√(2/g) = 0.67740; v₀ = k·√(g/2) = 1.5001 ± 0.0003 m/s. The
    manometer's column says 0 kPa in every row."""
    hs, L, p, _b = _part1(False)
    k, s, _c = _fit(np.sqrt(hs), L, 0.0, 0.0005, "line0")
    assert (round(k, 5), round(s, 5)) == (0.67743, 0.00016) and abs(k - K) < 2 * s
    assert round(k * math.sqrt(G / 2), 4) == 1.5001 and set(p) == {0.0}


def test_way_2_L_against_h_is_a_curve():
    """[right for grade 7, wrong as a proportion] The ranges grow with the height, but not in proportion: four times
    higher (0.25 → 1.00 m) gives 0.339 → 0.677 m, ×1.997 (2 within the readings' errors), not ×4; a line through the
    origin of L against h misses them (χ²/ν ≈ 3.5·10⁴)."""
    hs, L, _p, _b = _part1(False)
    assert all(np.diff(L) > 0)
    a, b = L[hs.index(0.25)], L[hs.index(1.0)]
    assert (a, b) == (0.339, 0.677) and abs(b / a - 2.0) < 2 * 0.0005 * math.hypot(1 / a, b / a ** 2)
    _k, _s, chi = _fit(hs, L, 0.0, 0.0005, "line0")
    assert chi > 3e4


def test_way_3_the_hand_stopwatch_against_the_time_from_the_tape():
    """[the stopwatch: too coarse; the tape's T = L/v₀: right] Neighbouring heights' flights differ by 0.011–0.024 s,
    a start and a stop by hand scatter by 0.10 s (Faux & Godolphin 2019, the instrument's declared error): over 4 000
    simulated classes (seed 20261118) the slope of the hand-timed T against √h is 0.452 ± 0.031 s/m^½ (7 % of √(2/g) =
    0.4516; 96 % of the classes within two of their own errors); T = L / v₀ from the tape's readings agrees with
    √(2h/g) to ±0.32 ms."""
    pts, _b = _points("lab.heights")
    hs = SPECS["lab.heights"]["controls"][0]["values"]
    T = np.array([pts[(h, False)]["flight_time"] for h in hs])
    steps = np.diff(T)
    assert (round(steps.min(), 3), round(steps.max(), 3)) == (0.011, 0.024) and steps.max() < INSTRUMENTS["stopwatch"]["error"]
    _hs, L, _p, _b = _part1(False)
    dev = [x / 1.5 - math.sqrt(2 * h / G) for x, h in zip(L, hs)]
    assert max(abs(x) for x in dev) < 0.32e-3
    rng = np.random.default_rng(20261118)
    ks, inside = [], 0
    for _ in range(4000):
        t = np.round((T + rng.normal(0.0, 0.10, T.size)) / 0.01) * 0.01
        k, s, _c = _fit(np.sqrt(hs), t, 0.0, 0.1, "line0")
        ks.append(k)
        inside += abs(k - math.sqrt(2 / G)) <= 2 * s
    assert (round(float(np.mean(ks)), 3), round(float(np.std(ks)), 3)) == (0.452, 0.031)
    assert 0.94 <= inside / 4000 <= 0.98


def test_way_4_the_air_on_part_1_misses_the_vacuum_law():
    """[wrong if read with the law of vacuum] With the air on, the ranges are 0.23–1.73 mm shorter (beyond the tape's
    ±0.5 mm from h = 0.40 m): the line through the origin gives k = 0.67629 ± 0.00016 m^½, 7.1 errors below
    v₀·√(2/g), so v₀ = 1.4975 m/s instead of 1.5000; the fit's χ²/ν (0.51) does not show it. The manometer says
    101.3 kPa."""
    hs, L, p, _b = _part1(True)
    pts, _b = _points("lab.heights")
    short = [1e3 * (pts[(h, False)]["range"] - pts[(h, True)]["range"]) for h in hs]
    assert (round(min(short), 2), round(max(short), 2)) == (0.23, 1.73)
    assert next(h for h, d in zip(hs, short) if d > 0.5) == 0.40
    k, s, chi = _fit(np.sqrt(hs), L, 0.0, 0.0005, "line0")
    assert (round(k, 5), round((k - K) / s, 1), round(k * math.sqrt(G / 2), 4)) == (0.67629, -7.1, 1.4975)
    assert chi < 1 and set(p) == {101.3}


def test_way_5_mixing_the_rows_with_and_without_air():
    """[wrong] All 34 rows in one table (the air on and off mixed): k = 0.67686 ± 0.00012 m^½, 4.4 errors below
    v₀·√(2/g), χ²/ν = 1.24: the manometer's column shows the mix."""
    hs, L0, _p0, _b = _part1(False)
    _hs, L1, _p1, _b = _part1(True)
    k, s, chi = _fit(np.sqrt(hs + hs), L0 + L1, 0.0, 0.0005, "line0")
    assert (round(k, 5), round((k - K) / s, 1), round(chi, 2)) == (0.67686, -4.4, 1.24)


def _part2(air):
    pts, built = _points("lab.angles")
    ths = SPECS["lab.angles"]["controls"][0]["values"]
    L = [_read(pts[(a, air)]["range"], "tape")[0] for a in ths]
    th = [_read(a, "protractor")[0] for a in ths]
    s2 = [_sin2(a, INSTRUMENTS["protractor"]["error"]) for a in th]
    return th, L, s2


def test_way_6_L_against_sin_2theta_without_air():
    """[right] The line through the origin of L against sin 2θ (the protractor's ±0.5° carried into sin 2θ), air off:
    2.5490 ± 0.0007 m, 0.4 errors from v₀²/g = 2.5493 m."""
    _th, L, s2 = _part2(False)
    k, s, _c = _fit([x[0] for x in s2], L, [x[1] for x in s2], 0.0005, "line0")
    assert (round(k, 4), round(s, 4)) == (2.5490, 0.0007) and abs(k - R) < 2 * s


def test_way_7_the_law_of_vacuum_applied_in_air():
    """[wrong: a law of vacuum applied in air] The same with the air on: 2.5380 ± 0.0007 m, 15.4 errors below v₀²/g
    (the design's 18 came from exact angles: the protractor's error enters the fit here); the fit's χ²/ν (0.006) does
    not show it."""
    _th, L, s2 = _part2(True)
    k, s, chi = _fit([x[0] for x in s2], L, [x[1] for x in s2], 0.0005, "line0")
    assert (round(k, 4), round((k - R) / s, 1)) == (2.5380, -15.4) and chi < 0.01


def test_way_8_the_angle_of_the_largest_range():
    """[right, within the steps] By eye on 5° steps: 45° with the air off and on; the parabola through L against θ:
    45.00 ± 0.14° without air, 44.97 ± 0.14° in air (the engine's optimum in air: 45.0°)."""
    for air, want in ((False, 45.00), (True, 44.97)):
        th, L, _s2 = _part2(air)
        assert th[int(np.argmax(L))] == 45
        v, s, _c = _fit(th, L, 0.5, 0.0005, "quadratic")
        assert (round(v, 2), round(s, 2)) == (want, 0.14)


def _part3():
    pts, _b = _points("lab.air")
    ths = SPECS["lab.air"]["controls"][0]["values"]
    L = np.array([_read(pts[(a,)]["range"], "tape")[0] for a in ths])
    Lv = np.array([_read(pts[(a,)]["range_vacuum"], "tape_grey")[0] for a in ths])
    return np.array(ths, float), L, Lv


def test_way_9_a_parabola_near_the_top():
    """[right] The parabola through the six points 30–55°: 42.36 ± 0.20°, 0.3 errors from the engine's optimum 42.3°
    (with the measured drag curve; 41.9° with the constant C_d)."""
    th, L, _Lv = _part3()
    m = (th >= 30) & (th <= 55)
    v, s, _c = _fit(th[m], L[m], 0.5, 0.0005, "quadratic")
    assert (round(v, 2), round(s, 2), round((v - 42.3) / s, 1)) == (42.36, 0.20, 0.3)


def test_way_10_a_parabola_over_the_whole_range():
    """[wrong: a parabola too far from the top] Over all eleven points 20–70°: 42.52 ± 0.15°, 1.5 errors above the
    engine's 42.3° (EX1's 25–60°: 42.41 ± 0.18°, 0.6 errors); the bias is systematic but, at this tape's resolution,
    under two errors [weakens the design's 1.8σ]."""
    th, L, _Lv = _part3()
    v, s, _c = _fit(th, L, 0.5, 0.0005, "quadratic")
    assert (round(v, 2), round(s, 2), round((v - 42.3) / s, 1)) == (42.52, 0.15, 1.5)
    m = (th >= 25) & (th <= 60)
    v, s, _c = _fit(th[m], L[m], 0.5, 0.0005, "quadratic")
    assert (round(v, 2), round(s, 2)) == (42.41, 0.18)


def test_way_11_the_largest_range_by_eye_and_the_grey_ball():
    """[coarse] By eye on 5° steps the largest range in air is at 40° (28.352 m against 28.323 m at 45°); the grey
    ball's parabola peaks at 45.00 ± 0.16°."""
    th, L, Lv = _part3()
    assert th[int(np.argmax(L))] == 40.0 and (L[4], L[5]) == (28.352, 28.323)
    v, s, _c = _fit(th, Lv, 0.5, 0.0005, "quadratic")
    assert (round(v, 2), round(s, 2)) == (45.00, 0.16)


def test_the_built_atlases_are_the_runners():
    """When the built atlases are here, their points' measurables are the runner's, bit for bit (a sample per atlas)."""
    for aid in ("lab.heights", "lab.angles", "lab.air", "explore"):
        built = _built(aid)
        if built is None:
            pytest.skip("the atlases are not built here with the current key (site/record.py --world s03_projectile)")
        spec = SPECS[aid]
        grid = _grid(spec)
        for i in sorted(built)[:: max(1, len(built) // 7)]:
            assert built[i] == _computed(spec, grid[i]), (aid, grid[i])


# --- Watch -------------------------------------------------------------------------------------------------------------
def _story(rid):
    rec = next(r for r in VIZ["recordings"] if r["id"] == rid)
    msgs = []
    headless.run_spec(V, rec["preset"], None, rec["seed"], {"fps": rec["fps"], "speed": rec["speed"]},
                      {"seconds": rec["seconds"]}, rec.get("script"), emit=lambda m, b=None: msgs.append((m, b)),
                      captions=rec.get("captions"))
    return rec, msgs


def test_the_independence_story_s_captions_against_the_recording():
    """The captions' statements are the recording's: «at the same height, to 0.03 mm» (the thrown ball at most
    0.026 mm higher, the Eötvös effect); «twice as far, at the same moment» (×2.0000, the landings 10 µs apart);
    «four times higher: twice as long, the range doubles» (×2.0000 each). Each caption comes no later than what it
    describes: the second while the balls fall, the third and the fourth at their worlds' starts."""
    rec, msgs = _story("independence")
    fps, speed = rec["fps"], rec["speed"]
    caps = [m for m, _b in msgs if m["type"] == "caption"]
    assert [c["at"] for c in caps] == [c["at"] for c in rec["captions"]]
    worlds, w = [], -1
    for m, b in msgs:
        if m["type"] == "header":
            worlds.append({"events": [], "dy": [], "start_frame": None})
            w += 1
        elif m["type"] == "event":
            worlds[w]["events"].append(m)
        elif m["type"] == "check" and m["id"] == "other.same_height":
            worlds[w]["dy"].append(m["value"])
    land = [{e["kind"]: e for e in W["events"]} for W in worlds]
    assert len(worlds) == 3
    dy = worlds[0]["dy"][-1]
    assert 0 < dy <= 0.03e-3 and round(1e3 * dy, 2) == rec["captions"][1]["text"].args["d"] == 0.03
    assert caps[1]["t"] < land[0]["landing"]["t"]  # while the balls fall
    L = [x["landing"]["data"]["L"] for x in land]
    T = [x["landing"]["data"]["T"] for x in land]
    Td = [x["companion_landing"]["data"]["T"] for x in land]
    assert abs(L[1] / L[0] - 2) < 1e-4 and abs(T[1] - Td[1]) < 2e-5 and abs(T[0] - Td[0]) < 1e-5
    assert abs(T[2] / T[1] - 2) < 1e-4 and abs(L[2] / L[1] - 2) < 1e-4
    # each world's flight ends before the next world starts (a caption of a world comes at its start)
    starts = [0.0] + [c["at"] for c in rec["script"] if c["cmd"] == "new_world"] + [rec["seconds"]]
    for k in range(3):
        assert starts[k] + T[k] / speed < starts[k + 1] - 0.5
    assert [c["at"] for c in rec["captions"]][2:] == starts[1:3] and rec["captions"][0].get("hold")
    assert fps == 20


def test_the_air_story_s_captions_against_the_recording():
    """«the ball in air rises lower and falls short of the grey one»: computed so, the caption before the top."""
    rec, msgs = _story("air")
    ev = {m["kind"]: m for m, _b in msgs if m["type"] == "event"}
    a = S.Shot("ball67", 0.0, 20.0, 40.0, True)
    v = S.Shot("ball67", 0.0, 20.0, 40.0, False)
    assert ev["landing"]["data"]["L"] == a.L < 0.8 * v.L == 0.8 * ev["companion_landing"]["data"]["L"] and a.H < v.H
    caps = [m for m, _b in msgs if m["type"] == "caption"]
    assert caps[1]["t"] < ev["apex"]["t"] and v.T / rec["speed"] < rec["seconds"] - 0.5
    assert rec["captions"][0]["text"].args == {"v": 20.0, "a": 40.0}
