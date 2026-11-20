# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u34's screens (EX2 design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §2, §7, §11 items 10, 13, 34): every point
of every atlas builds with every check ✓ and stops by its own rule; the bench's computed values against independent
computations; every way of the bench on the built points (the readings rounded by the instruments, the formula columns
by ``lfviz.expr``, the fit by ``lfphys.tools.stats.linear_fit``) gives its stated outcome; the Watch captions' numbers are
the recordings' own and every caption comes no later than its event; the body's clock past the horizon; Buchdahl's
refusal; Newton's ghost on the regularised integrator."""

from __future__ import annotations

import bisect
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest
from lfviz import expr, headless, registry

from lfphys.core.constants import C, GM_SUN
from lfphys.core.gravity import orbit_stream, orbits
from lfphys.theories.approx import ppn
from lfphys.tools.stats import linear_fit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "site"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
import atlas as AT  # noqa: E402
from harness import Harness  # noqa: E402

W = "u34_orbits"
VIZ = registry.load(W)
SCREENS = {s["id"]: s for s in VIZ["screens"]}
RECS = {r["id"]: r for r in VIZ["recordings"]}
ATLASES = {a["id"]: a for a in registry.atlases_of(VIZ)}
LAB = SCREENS["lab"]
INS, STEPS = LAB["instruments"], {s["id"]: s for s in LAB["steps"]}


@lru_cache(None)
def _point(aid: str, values: tuple):
    msgs, oc = AT.run_point(W, ATLASES[aid], dict(values), log=lambda *a: None)
    return msgs, oc


def _frames(aid, values):
    msgs, _oc = _point(aid, tuple(sorted(values.items())))
    return [m for m, _b in msgs if m["type"] == "frame"], next(m for m, _b in msgs if m["type"] == "header")


# --- every point of every atlas -------------------------------------------------------------------------------------
def _grid(aid):
    return [dict(zip([c["param"] for c in ATLASES[aid]["controls"]], combo))
            for combo in AT.grid(ATLASES[aid]["controls"])]


@pytest.mark.parametrize("aid", sorted(ATLASES))
def test_every_point_of_every_atlas_builds_with_every_check_ok_and_stops_by_its_rule(aid):
    spec = ATLASES[aid]
    want = registry.stop_events(spec["stop"])
    for values in _grid(aid):
        msgs, oc = _point(aid, tuple(sorted(values.items())))
        counts = oc.check_counts()
        assert counts["failed"] == 0 and counts["ok"] >= 3, (values, counts)
        assert oc.stop_event in want, (values, oc.stop_event)
        assert oc.counts[oc.stop_event] == want[oc.stop_event]
        assert oc.t_end < spec["stop"]["max_world_s"]
        seg = next(m for m, _b in msgs if m["type"] == "segment")
        # the kind of orbit decides the rule that stopped it: a circle by its turns, an ellipse by its periapses (the
        # launch's included), a plunge by the horizon
        expect = {"circular": "turn", "bound": "periapsis", "plunge": "horizon"}[seg["kind"]]
        assert oc.stop_event == expect, (values, seg["kind"], oc.stop_event)


def test_the_explore_grid_holds_what_the_design_measured():
    """EX2 §2.2: every start below the circular speed at 7 and 8 M, and at 0.9 at 10 and 12 M, falls in (Newton's ghost
    stays on an ellipse); at 10 M and 0.95 the body dips to 6.13 M and whirls 438.5° per radial period; at speed 1 a
    circle; the advance per radial period from 33.0° (30 M, 1.1) to 255.7° (7 M, 1.05)."""
    kinds = {}
    for v in _grid("explore"):
        msgs, _oc = _point("explore", tuple(sorted(v.items())))
        seg = next(m for m, _b in msgs if m["type"] == "segment")
        kinds[(v["r0"], v["speed"])] = seg
    falls = {k for k, s in kinds.items() if s["kind"] == "plunge"}
    assert falls == {(7.0, 0.9), (7.0, 0.95), (8.0, 0.9), (8.0, 0.95), (10.0, 0.9), (12.0, 0.9)}
    assert all(kinds[k]["ghost"]["kind"] == "bound" for k in falls)
    assert all(s["kind"] == "circular" for k, s in kinds.items() if k[1] == 1.0)
    zw = kinds[(10.0, 0.95)]
    assert zw["r_peri"] == pytest.approx(6.13, abs=0.005) and math.degrees(zw["adv_exact"]) == pytest.approx(438.5, abs=0.05)
    assert math.degrees(kinds[(30.0, 1.1)]["adv_exact"]) == pytest.approx(33.0, abs=0.05)
    assert math.degrees(kinds[(7.0, 1.05)]["adv_exact"]) == pytest.approx(255.7, abs=0.05)


def test_the_readouts_agree_with_their_references_at_every_explore_point():
    """The readouts and their references (EX2 §5 F7): the advance per orbit and the exact elliptic integral, the radial
    period and its quadrature, the clock's rate over whole periods and √(1 − 3M/r) (circles) or the quadratures'
    τ_r/t_r (ellipses), the body's clock at r = 0 and its value without the integrator; each readout either shows its
    reference or is not reached («—»)."""
    pairs = [("adv_deg", "adv_ref_deg", 1e-8), ("T_r", "T_r_ref", 1e-9), ("rate_mean", "rate_mean_ref", 1e-9),
             ("tau_centre", "tau_centre_ref", 1e-9)]
    seen = set()
    for values in _grid("explore"):
        msgs, _oc = _point("explore", tuple(sorted(values.items())))
        m = [x for x, _b in msgs if x["type"] == "frame"][-1]["meas"]
        for v, r, tol in pairs:
            if m[v] is None:
                continue
            assert m[r] is not None and abs(m[v] - m[r]) <= tol * abs(m[r]), (values, v, m[v], m[r])
            seen.add(v)
    assert seen == {p[0] for p in pairs}


# --- the bench's computed values against independent computations -----------------------------------------------------
def _ref(step, ref):
    spec = ATLASES[f"lab.{step}"]
    return AT.reference(VIZ, spec, headless.resolve(VIZ, spec["preset"], spec["fixed"]), ref)


def test_kepler_and_the_clock_law_against_a_fit_of_the_world_s_own_turns():
    """The exponent 3/2 and (τ/T)² = 1 − 3M/r: a fit of the run's own clocks at its turns (unrounded) on the circles."""
    R, T, Q = [], [], []
    for r in STEPS["periods"]["controls"][0]["values"]:
        F, _h = _frames("lab.periods", {"r0": r, "speed": 1.0})
        m = F[-1]["meas"]
        R.append(r); T.append(m["t_lap"] / m["n_lap"]); Q.append((m["tau_lap"] / m["t_lap"]) ** 2)
    f = linear_fit(R, T, 0.0, 0.0, "power")
    assert f["n_exp"] == pytest.approx(_ref("periods", "kepler")["value"], abs=1e-9)
    assert f["A"] == pytest.approx(2 * math.pi, rel=1e-9)
    g = linear_fit([1 / r for r in R], Q, 0.0, 0.0, "line")
    assert g["params"][0] == pytest.approx(_ref("periods", "clock_intercept")["value"], abs=1e-10)
    assert g["params"][1] == pytest.approx(_ref("periods", "clock_slope")["value"], abs=1e-8)


def test_six_pi_and_the_next_order_against_the_engine_s_exact_advance():
    """6π: ppn.periapsis_advance/(M/p) at any a, and the exact elliptic integral divided by M/p as M/p → 0; the next
    order 6π(18 + ε²)/4: the slope of (Δφ/(M/p) − 6π)/(M/p) of the exact integral at small M/p for these orbits' ε."""
    six_pi = _ref("advance", "leading")["value"]
    assert six_pi == pytest.approx(6 * math.pi, rel=1e-14) == _ref("advance", "intercept")["value"]
    for a in (1e3, 1e6, 1e9):
        gm = 10 * GM_SUN
        Mm = gm / C**2
        assert ppn.periapsis_advance(gm, a * Mm, 0.3) / (1 / (a * (1 - 0.09))) == pytest.approx(6 * math.pi, rel=1e-13)
    # the bench's eccentricities (speed 1.1 at each r0) and the exact advance at small M/p with the same ε
    eps = []
    for r0 in STEPS["advance"]["controls"][0]["values"]:
        c = orbit_stream.local_velocity_to_constants(r0, 0.0, 1.1 * math.sqrt(1.0 / (r0 - 2.0)))
        eps.append(orbits.elements(c["e"], abs(c["l"]), c["em1"])["ecc"])
    weak = [x for r0, x in zip(STEPS["advance"]["controls"][0]["values"], eps) if r0 >= 300]
    assert 0.2102 <= min(weak) <= max(weak) <= 0.2130 and max(eps) == pytest.approx(0.2666, abs=1e-4)  # (20 M)
    e2 = sum(x * x for x in weak) / len(weak)
    ecc = math.sqrt(e2)
    mus, ys = [], []
    for p in (2e3, 4e3, 8e3, 1.6e4):
        # e, l of the orbit with p and ε (Schwarzschild: l² = p²/(p − 3 − ε²), e² = (p − 2 − 2ε)(p − 2 + 2ε)/(p(p − 3 − ε²)))
        l2 = p * p / (p - 3 - e2)
        em1 = ((p - 2 - 2 * ecc) * (p - 2 + 2 * ecc) - p * (p - 3 - e2)) / (p * (p - 3 - e2))
        adv = orbits.periapsis_advance(math.sqrt(1 + em1), math.sqrt(l2), em1)
        mu = 1 / p
        mus.append(mu); ys.append((adv / mu - 6 * math.pi) / mu)
    f = linear_fit(mus, ys, 0.0, 0.0, "line")
    assert f["params"][0] == pytest.approx(_ref("advance", "next")["value"], rel=2e-4)
    assert _ref("advance", "next")["value"] == pytest.approx(85.03, abs=0.01)


def test_newton_s_zero_against_the_ghost_on_the_bench():
    assert _ref("advance", "newton")["value"] == 0.0
    for r0 in STEPS["advance"]["controls"][0]["values"]:
        F, _h = _frames("lab.advance", {"r0": r0})
        assert abs(F[-1]["meas"]["ghost_peri_shift"]) < 1e-6  # degrees after ten Newtonian orbits


# --- the ways of the bench (EX2 §2.3; W34's numbers: two parts, the radial clock in part 2) ---------------------------
def _read(i, v):
    if i["kind"] == "counter":
        return (int(round(v)), float(i["error"]))
    d = i["division"]
    return (math.floor(v / d + 0.5) * d, i["error"] if i.get("error") is not None else d / 2)


def _row(step, values, moment=None):
    """One row of the table as the lab writes it: the instruments read at the moment (the point's end, or the first
    frame where a count reaches n: «after one turn», «after one orbit»), rounded by their divisions, the formula columns
    by the lab's grammar with the errors propagated."""
    F, hdr = _frames(f"lab.{step}", values)
    f = F[-1] if moment is None else next(x for x in F if (x["meas"].get(moment[0]) or 0) >= moment[1])
    st = STEPS[step]
    rd = {}
    for iid in st["instruments"]:
        src = INS[iid]["reads"]
        v = hdr["params"][src[8:]] if src.startswith("control:") else f["meas"][src]
        assert v is not None, (step, values, iid)  # every instrument reads on every point: «Measure» is never refused
        rd[iid] = _read(INS[iid], v)
    cols = {}
    for c in st["columns"]:
        if "from" in c:
            cols[c["id"]] = rd[c["from"]]
        else:
            try:
                cols[c["id"]] = tuple(expr.evaluate(c["expr"], {k: v for k, v in cols.items() if v is not None})[:2])
            except expr.Undefined:
                cols[c["id"]] = None
    return cols


def _fit(rows, x, y, model):
    pts = [(r[x], r[y]) for r in rows if r.get(x) and r.get(y)]
    return linear_fit([p[0][0] for p in pts], [p[1][0] for p in pts], [p[0][1] for p in pts], [p[1][1] for p in pts],
                      model)


R1 = STEPS["periods"]["controls"][0]["values"]
R2 = STEPS["advance"]["controls"][0]["values"]


def _part1(speed, moment=None):
    return [_row("periods", {"r0": r, "speed": speed}, moment) for r in R1]


def _part2(moment=None, rmin=0.0):
    return [_row("advance", {"r0": r}, moment) for r in R2 if r >= rmin]


def test_ways_1_to_5_periods_and_clocks():
    four, one = _part1(1.0), _part1(1.0, ("n_lap", 1))
    w1 = _fit(four, "r", "T", "power")   # way 1: Kepler's third law on circles in the distant observer's time
    assert w1["n_exp"] == pytest.approx(1.4999990, abs=2e-7) and w1["n_exp_sigma"] == pytest.approx(5.5e-6, rel=0.05)
    assert abs(w1["n_exp"] - 1.5) < 2 * w1["n_exp_sigma"] and w1["A"] == pytest.approx(6.28321, abs=2e-5)
    w2 = _fit(four, "r", "Tb", "power")  # way 2: the wrong clock, the body's
    assert w2["n_exp"] == pytest.approx(1.535, abs=5e-4) and w2["chi2_dof"] > 1e5 and w2["scaled"]
    w3 = _fit(four, "x", "q", "line")    # way 3: the clock law (τ/t)² = 1 − 3M/r
    assert w3["params"][0] == pytest.approx(1.0000055, abs=2e-7) and w3["params"][1] == pytest.approx(-3.00010, abs=2e-5)
    assert abs(w3["params"][1] + 3) < 2 * w3["sigma"][1] and abs(w3["params"][1]) > 100 * w3["sigma"][1]  # not Newton's 0
    w5 = _fit(one, "r", "T", "power")    # way 5: read after one turn: errors four times larger
    assert w5["n_exp"] == pytest.approx(1.500014, abs=1e-6) and w5["A"] == pytest.approx(6.2828, abs=1e-4)
    assert w5["n_exp_sigma"] / w1["n_exp_sigma"] == pytest.approx(4.0, rel=0.05)
    w5b = _fit(one, "x", "q", "line")
    assert w5b["params"][0] == pytest.approx(0.999988, abs=1e-6) and w5b["params"][1] == pytest.approx(-2.9990, abs=1e-4)
    # way 4b: eccentric orbits (1.1 of the circular speed). Not because they are ellipses: in Newton's gravity a
    # tangential launch at k of the circular speed gives a = r0/(2 − k²) ∝ r0, so T ∝ r0^{3/2} exactly (review R2-W F4).
    # Near the hole a turn in φ is not a radial period (the periapsis advances), the orbit's shape changes with r0, and
    # t/n over whole turns in φ is not a whole number of radial periods; it shows from r0 = 30 M on too
    k = 1.1
    a_newton = [r / (2.0 - k * k) for r in R1]
    assert np.polyfit(np.log(R1), np.log([2 * math.pi * a ** 1.5 for a in a_newton]), 1)[0] == pytest.approx(1.5, abs=1e-12)
    ecc = _part1(1.1)
    w4b = _fit(ecc, "r", "T", "power")
    assert w4b["n_exp"] == pytest.approx(1.410, abs=1e-3) and w4b["chi2_dof"] > 1e7
    w4c = _fit([r for r in ecc if r["r"][0] >= 30.0], "r", "T", "power")
    assert w4c["n_exp"] == pytest.approx(1.4595, abs=1e-3) and w4c["chi2_dof"] > 1e5


def test_way_4_the_radial_period_of_eccentric_orbits_is_not_kepler_s():
    ten = _part2()
    f = _fit(ten, "a", "Tr", "power")
    assert f["n_exp"] == pytest.approx(1.4975, abs=1e-4) and f["chi2_dof"] == pytest.approx(10.8, abs=0.1)
    assert abs(f["n_exp"] - 1.5) > 3 * f["n_exp_sigma"]
    g = _fit(_part2(rmin=300.0), "a", "Tr", "power")
    assert g["n_exp"] == pytest.approx(1.4981, abs=1e-4) and abs(g["n_exp"] - 1.5) > 5 * g["n_exp_sigma"]


def test_ways_6_to_12_the_advance():
    one, three, ten = _part2(("n_peri", 2)), _part2(("n_peri", 4)), _part2()
    weak = lambda rows: [r for r in rows if r["r0"][0] >= 300]  # noqa: E731
    w6 = _fit(weak(one), "x", "dphi", "line0")
    assert w6["params"][0] == pytest.approx(19.035, abs=1e-3) and w6["sigma"][0] == pytest.approx(0.24, abs=0.005)
    assert abs(w6["params"][0] - 6 * math.pi) < w6["sigma"][0]  # the leading order holds within these errors
    w7 = _fit(one, "x", "dphi", "line0")
    assert w7["params"][0] == pytest.approx(19.997, abs=1e-3) and w7["chi2_dof"] == pytest.approx(16.6, abs=0.05)
    assert w7["sigma"][0] == pytest.approx(0.27, abs=0.005) and w7["scaled"]
    w12 = _fit(weak(three), "x", "dphi", "line0")
    assert w12["params"][0] == pytest.approx(18.999, abs=1e-3) and w12["sigma"][0] == pytest.approx(0.082, abs=0.002)
    w8 = _fit(weak(ten), "x", "dphif", "line0")
    assert w8["params"][0] == pytest.approx(18.947, abs=1e-3) and w8["sigma"][0] == pytest.approx(0.023, abs=0.001)
    assert w8["chi2_dof"] == pytest.approx(14.9, abs=0.05) and w8["birge"] == pytest.approx(3.86, abs=0.01)
    w9 = _fit(weak(ten), "x", "y", "line")
    assert w9["params"][0] == pytest.approx(18.846, abs=1e-3) and w9["sigma"][0] == pytest.approx(0.012, abs=0.001)
    assert w9["params"][1] == pytest.approx(89.2, abs=0.1) and w9["sigma"][1] == pytest.approx(9.5, abs=0.1)
    w10 = _fit(ten, "x", "y", "line")
    assert w10["params"][0] == pytest.approx(18.839, abs=1e-3) and w10["sigma"][0] == pytest.approx(0.0078, abs=3e-4)
    assert w10["params"][1] == pytest.approx(94.06, abs=0.05) and w10["sigma"][1] == pytest.approx(3.7, abs=0.05)
    assert w10["chi2_dof"] == pytest.approx(0.45, abs=0.01)
    assert (w10["params"][1] - 85.03) / w10["sigma"][1] == pytest.approx(2.4, abs=0.1)  # the slope drifts, χ² small
    assert all(r["sn"][0] == 0.0 for r in one + ten)  # way 11: Newton's protractor reads 0.0° at every r0


def test_every_instrument_reads_on_every_point_of_its_step():
    """lab.js refuses the whole «Measure» when one instrument of the step has nothing to read: so every instrument of
    a step reads on every point of its atlas at its end (a circle has no periapsis: the radial clock and the radius
    scales are part 2's, on eccentric orbits only)."""
    for step in STEPS:
        for values in _grid(f"lab.{step}"):
            _row(step, values)


# --- Watch: the captions against the recordings ---------------------------------------------------------------------
@lru_cache(None)
def _recording(rid):
    r = RECS[rid]
    msgs = []
    out = headless.run_spec(W, r["preset"], None, r.get("seed", 1), {"fps": r["fps"], "speed": r.get("speed")},
                            {"seconds": r["seconds"]}, r.get("script") or [], lambda m, b=None: msgs.append((m, b)),
                            captions=r.get("captions") or [], end_reason="test")
    frames = [m for m, _b in msgs if m["type"] == "frame"]
    ft = [f["t"] for f in frames]
    played = lambda t: bisect.bisect_left(ft, t - 1e-15) / r["fps"]  # noqa: E731 - the first frame at or after t
    return out, msgs, frames, played


def _cap(rid, k):
    c = RECS[rid]["captions"][k]
    return c["at"], c["text"].args


def _apsides(msgs, kind, seg=None):
    return [m for m, _b in msgs if m["type"] == "apsis" and m["kind"] == kind and (seg is None or m["seg"] == seg)]


def test_the_story_s_captions_say_what_the_run_shows_no_later_than_it_shows_it():
    out, msgs, frames, played = _recording("story")
    assert out.frames == 800 and out.check_counts()["failed"] == 0
    caps = [m for m, _b in msgs if m["type"] == "caption"]
    assert [c["at"] for c in caps] == [c["at"] for c in RECS["story"]["captions"]]
    hdr = next(m for m, _b in msgs if m["type"] == "header")
    # 0: the launch from 20 M at 1.1, M ≈ 14.8 km for 10 M☉
    at, a = _cap("story", 0)
    seg = [m for m, _b in msgs if m["type"] == "segment"]
    assert at == 0 and seg[0]["init"]["r0"] == a["r0"] and seg[0]["init"]["k"] == pytest.approx(a["k"])
    assert hdr["units"]["M_m"] / 1e3 == pytest.approx(a["mkm"], abs=0.05) and hdr["body"]["mass_msun"] == a["m"]
    # 1: Newton's ellipse back at its periapsis after one turn (6.30 s)
    gp = [m for m, _b in msgs if m["type"] == "gapsis" and m["seg"] == 0]
    assert _cap("story", 1)[0] <= played(gp[1]["t"]) == pytest.approx(6.30)
    assert math.atan2(gp[1]["y"], gp[1]["x"]) == pytest.approx(0.0, abs=1e-9)  # closed on itself
    # 2: GR's periapsis 2 about 52° further on (6.00 s)
    p0 = _apsides(msgs, "peri", 0)
    at, a = _cap("story", 2)
    assert at <= played(p0[1]["t"]) == pytest.approx(6.0) and round(math.degrees(p0[1]["adv"])) == a["a"]
    # 3: the clock lags by 8.4 % at the periapsis (the plot, from 0 s), shown before periapsis 3 (12.0 s)
    at, a = _cap("story", 3)
    k = bisect.bisect_left([f["t"] for f in frames], p0[1]["t"])
    assert round(100 * frames[k]["deficit"], 1) == a["p"] and at < played(p0[2]["t"])
    # 4: after three turns about 156° (periapsis 4 at 18.0 s)
    at, a = _cap("story", 4)
    assert at <= played(p0[3]["t"]) == pytest.approx(18.0) and round(math.degrees(p0[3]["shift"])) == a["a"]
    # 5: launched again from 10 M at 1.1 (19.0 s): about 120° per turn (periapsis 2 at 22.05 s), the clock lags 17.6 %
    at, a = _cap("story", 5)
    assert at == pytest.approx(played(seg[1]["t"])) and seg[1]["init"]["r0"] == a["r0"]
    p1 = _apsides(msgs, "peri", 1)
    assert at <= played(p1[1]["t"]) == pytest.approx(22.05) and round(math.degrees(p1[1]["adv"])) == a["a"]
    k = bisect.bisect_left([f["t"] for f in frames], p1[1]["t"])
    assert round(100 * frames[k]["deficit"], 1) == a["p"]
    # 6: from 7 M with 5 % less, six times slower; a plunge, Newton's body keeps orbiting
    at, a = _cap("story", 6)
    assert at == pytest.approx(played(seg[2]["t"])) and seg[2]["kind"] == "plunge" and seg[2]["ghost"]["kind"] == "bound"
    assert seg[2]["init"]["r0"] == a["r0"] and seg[2]["init"]["k"] == pytest.approx(1 - a["dv"] / 100)
    speeds = [c["args"]["value"] for c in RECS["story"]["script"] if c["cmd"] == "speed"]
    assert round(speeds[0] / speeds[1]) == a["f"]
    # 7: the stop 2·10⁻⁶ M above the horizon (32.75 s): 2.59 ms of the body's clock from 7 M, 36 µs more to r = 0
    at, a = _cap("story", 7)
    hz = next(m for m, _b in msgs if m["type"] == "event" and m["kind"] == "horizon")
    assert at <= played(hz["t"]) == pytest.approx(32.75)
    last = frames[-1]["meas"]
    T_s = hdr["units"]["T_s"]
    tau_stop = (frames[-1]["tau"]) * 1e3  # ms: the body's clock since this launch, frozen at the stop
    assert round(tau_stop, 2) == a["ts"]
    assert round(last["dtau_inside"] * T_s * 1e6) == a["tin"]
    # the trails reach 41.0 M (Newton's ellipse from 20 M): Watch's one scale for the whole story (setStory)
    R = max(float(abs(b[k]).max()) for m, b in msgs if m["type"] in ("trail", "gtrail") and b for k in ("x", "y"))
    assert R == pytest.approx(41.0, abs=0.05)


def test_the_other_recordings_captions():
    out, msgs, frames, played = _recording("rosette")
    assert out.check_counts()["failed"] == 0
    at, a = _cap("rosette", 0)
    ap = _apsides(msgs, "apo")
    assert at <= played(ap[0]["t"]) and round(ap[0]["r"], 1) == a["ra"]
    p = _apsides(msgs, "peri")
    at, a = _cap("rosette", 1)
    assert at <= played(p[1]["t"]) and round(math.degrees(p[1]["adv"]), 1) == a["a"]
    at, a = _cap("rosette", 2)
    assert at <= played(p[5]["t"]) and round(math.degrees(p[5]["shift"]), 1) == a["a"] and p[5]["n"] == 6
    out, msgs, frames, played = _recording("mercury")
    p = _apsides(msgs, "peri")
    at, a = _cap("mercury", 1)
    assert at <= played(p[1]["t"]) and round(math.degrees(p[1]["adv"]) * 3600, 4) == a["a"]
    cent = [m for m, _b in msgs if m["type"] == "check" and m["id"].endswith(".century")]
    assert at <= played(cent[0]["t"]) and round(cent[0]["value"], 2) == round(cent[-1]["value"], 2) == a["c"]
    at, a = _cap("mercury", 2)
    assert at <= played(p[4]["t"]) and p[4]["n"] == 5 and round(math.degrees(p[4]["shift"]) * 3600, 3) == a["a"]
    out, msgs, frames, played = _recording("plunge")
    at, a = _cap("plunge", 1)
    hz = next(m for m, _b in msgs if m["type"] == "event" and m["kind"] == "horizon")
    hdr = next(m for m, _b in msgs if m["type"] == "header")
    assert at <= played(hz["t"]) and round(frames[-1]["tau"] * 1e3, 2) == a["ts"]
    assert round(frames[-1]["meas"]["tau_centre"] * hdr["units"]["T_s"] * 1e3, 2) == a["t0"]


# --- the body's clock past the horizon (EX2 §11 item 34; E34's numbers) -----------------------------------------------
def test_the_story_s_fall_by_the_body_s_own_clock_to_r_zero():
    """E34 (WORLD_NOTES): the story's fall from 7 M at 0.95 of the circular speed, 10 M☉: the stop at 52.588 GM/c³
    (2.590 ms), r = 0 at 53.316 GM/c³ (2.626 ms), 0.727 GM/c³ (35.8 µs) inside the horizon; τ at r = 0 against the
    quadrature of the whole fall without the integrator; dτ_inside ≤ πM."""
    h = Harness(W, "default", {"r0": 7.0, "speed": 0.95, "ghost": False})
    h.run_to(1.0)
    F = [h.sim.frame()[0]]
    m = F[-1]["meas"]
    T_s = h.sim.T_s
    assert F[-1]["status"] == "horizon"
    assert F[-1]["tau"] / T_s == pytest.approx(52.588, abs=5e-4) and F[-1]["tau"] * 1e3 == pytest.approx(2.590, abs=5e-4)
    assert m["tau_centre"] == pytest.approx(53.316, abs=5e-4) and m["tau_centre"] * T_s * 1e3 == pytest.approx(2.626, abs=5e-4)
    assert m["dtau_inside"] == pytest.approx(0.727, abs=5e-4) and m["dtau_inside"] * T_s * 1e6 == pytest.approx(35.8, abs=0.05)
    assert m["tau_centre"] == pytest.approx(m["tau_centre_ref"], rel=1e-9)
    ref = orbit_stream.plunge_proper_time(h.sim.track.em1, h.sim.track.l, 7.0, h.sim.init["v_r"], 0.0, h.sim.info["r_apo"])
    assert m["tau_centre"] == pytest.approx(ref, rel=1e-9)
    c = {x["id"].split(".")[1]: x for x in h.checks().values()}
    assert abs(c["fall_r0"]["rel"]) < 1e-9 and c["inside"]["ok"] and m["dtau_inside"] <= math.pi


def test_a_radial_fall_from_rest_reaches_r_zero_at_the_cycloid_s_time():
    h = Harness(W, "radial")
    h.run_to(10 * 2 * math.pi * 20**1.5 * h.sim.T_s)
    m = h.sim.frame()[0]["meas"]
    assert m["tau_centre"] == pytest.approx(orbit_stream.cycloid_proper_time(20.0), rel=1e-9)
    assert m["tau_centre"] == pytest.approx(math.pi * math.sqrt(20.0**3 / 8), rel=1e-9)
    assert m["dtau_inside"] < math.pi  # from rest at 20 M: less than from rest at the horizon
    c = {x["id"].split(".")[1]: x for x in h.checks().values()}
    assert abs(c["fall_r0"]["rel"]) < 1e-9 and c["inside"]["ok"]


def test_the_interior_is_not_claimed_for_a_star_or_an_escape():
    h = Harness(W, "neutron_star", {"speed": 0.5})
    h.run_to(5 * h.sim.track.dyn * h.sim.T_s)
    assert h.sim.track.end_event["kind"] == "surface" and h.sim.frame()[0]["meas"]["tau_centre"] is None


# --- Buchdahl, Newton's ghost, the declarations ------------------------------------------------------------------------
def test_a_star_more_compact_than_buchdahl_s_limit_is_refused_with_its_reason():
    from lfviz.errors import Refusal
    sim = VIZ["simulation"]
    Mkm = 1.4 * GM_SUN / C**2 / 1e3
    with pytest.raises(Refusal) as e:
        sim.check_params({"gravity": "GR", "mass_msun": 1.4, "radius_km": 2.2 * Mkm})
    assert "9M/4" in str(e.value.text) and "Buchdahl" in str(e.value.text)
    with pytest.raises(Refusal) as e:
        sim.check_params({"gravity": "GR", "mass_msun": 1.4, "radius_km": 1.9 * Mkm})
    assert "black hole" in str(e.value.text)
    sim.check_params({"gravity": "GR", "mass_msun": 1.4, "radius_km": 2.26 * Mkm})  # just outside: allowed
    sim.check_params({"gravity": "newton", "mass_msun": 1.4, "radius_km": 2.0 * Mkm})  # Newton has no such bound
    with pytest.raises(headless.PointRefused):
        headless.run_spec(W, "neutron_star", {"radius_km": 2.2 * Mkm}, 1, {"frame_dt": 1e-4}, {"world_s": 1e-3})


@pytest.mark.parametrize("angle", [-89.9, -89.99])
def test_newton_s_ghost_on_the_regularised_integrator_keeps_its_energy_at_a_deep_periapsis(angle, monkeypatch):
    """EX2 §11 item 10 (STATUS V19 (e)): in coordinate time a periapsis at ~1e-6 r₀ cost ~1e-5 of |E|; the Levi-Civita
    regularised integration (restarted at every chunk) keeps it to a few 1e-9 over three orbits: the same orbit with the
    coordinate-time integrator measured beside it, here, for the comparison."""
    from lfphys.theories.approx import newton
    from u34_orbits.engine import body
    h = Harness(W, "newton_ellipse", {"angle": angle, "speed": 1.0, "ghost": False})
    h.run_to(3.3 * h.sim.info["period_ref"])
    reg = h.sim.track.drift["E"]
    assert reg < 1e-8
    ap = [m for m in h.of("apsis") if m["kind"] == "peri"]
    if h.sim.info["kind"] == "bound":
        assert len(ap) >= 3 and all(abs(a["adv"]) < 1e-6 for a in ap[1:])
    monkeypatch.setattr(body.NewtonTrack, "_fine", lambda self, X, dt, n, r_stop: newton.integrate_body(
        (X[0], X[1]), (X[2], X[3]), 1.0, dt, n_out=n, r_stop=r_stop))
    old = Harness(W, "newton_ellipse", {"angle": angle, "speed": 1.0, "ghost": False})
    old.run_to(3.3 * old.sim.info["period_ref"])
    assert old.sim.track.drift["E"] > 100 * reg


def test_the_screens_are_the_registry_s_and_the_view_declares_what_they_use():
    assert registry.check(VIZ) == []
    decl = registry.view_declarations(VIZ)
    for sc in [SCREENS["explore"], *LAB["steps"]]:
        assert set(sc.get("overlays") or []) <= set(decl["overlays"])
        assert all(decl["quantSafe"].get(f"{t}.{b}") for t, b, _e in registry.quantize_items(sc.get("quantize") or {}))
    assert {a: len(AT.grid(s["controls"])) for a, s in ATLASES.items()} == {"explore": 35, "lab.periods": 18,
                                                                           "lab.advance": 13}
    assert VIZ["version"] == "1.1"


# --- CI 2026-11-19 (run 44536842139): results that hung on the last bits of a CPU ------------------------------------
@pytest.mark.parametrize("r0b, j", [(20.0, 24), (50.0, 7), (50.0, 18), (7.0, 24), (100.0, 8), (30.0, 4), (30.0, 5),
                                    (12.0, 0), (15.0, 3)])
def test_a_circle_stepped_by_the_atlas_frame_clock_counts_every_turn_once(r0b, j):
    """Lab part 1's circles advance a frame every T/32 and compute 1/8 of a period ahead, so a chunk of the geodesic
    ends within a rounding of a turn; the engine's turn counting then lost a turn on some CPUs (CI's AVX-512 runner:
    «s0.period» failed). These starts, perturbed by ulps, lost one before the fix (laps [1, 2, 4]: a period 4/3 of
    Kepler's); every turn now comes once and the period check holds."""
    h = Harness(W, "default", {"ghost": False, "angle": 0.0, "time_units": "geo", "r0": r0b * (1 + j * 2.2e-16),
                               "speed": 1.0})
    step = h.sim.default_speed / 4.0
    for k in range(1, 4 * 32 + 3):
        h.run_to(k * step)
    assert [e["n"] for e in h.sim.S["laps"]] == [1, 2, 3, 4]
    per = [c for c in h.checks().values() if c["id"].endswith(".period")][-1]
    assert abs(per["rel"]) <= per["tol"]


def test_newton_s_nearly_circular_apsis_is_stable_to_the_last_bits_of_its_start():
    """Test V4-5's orbit (r0 50 M, speed 1.0000004, spread 1.6e-6): its apses lie where r·v changes sign, which the
    tiny eccentricity makes ill-conditioned. On the regularised integrator's output the measured advance scattered by up
    to 0.69″ under ulp changes of the start (CI: 0.265″ against the tolerance 0.026″); a smooth orbit is now integrated
    in coordinate time (0.0009″) and only a deep one (r_p < 2e-3 a) regularised."""
    vals = []
    for j in range(12):
        h = Harness(W, "newton_ellipse", {"r0": 50.0 * (1 + j * 2.2e-16), "speed": 1.0000004 + (j % 3) * 2.2e-16,
                                          "ghost": False})
        assert not h.sim.track.regularised
        h.run_to(h.sim.t + 3.3 * 2 * math.pi * 50.0**1.5 * h.sim.T_s)
        c = [m for m in h.checks().values() if m["id"].endswith(".adv")][-1]
        assert c["ok"], (j, c["value"], c["tol"])
        vals.append(abs(c["value"]))
    assert max(vals) < 0.1 * c["tol"]
    deep = Harness(W, "newton_ellipse", {"angle": -89.9, "speed": 1.0, "ghost": False})
    radial = Harness(W, "newton_ellipse", {"speed": 0.0, "ghost": False})
    assert deep.sim.track.regularised and radial.sim.track.regularised
