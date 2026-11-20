# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u35's screens (design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §3, §7 «The worlds»):

* every grid point of every atlas builds with all its checks ✓ and stops by its own rule (``site/atlas.py``'s runner);
* the bench's computed values (``lab_reference``) against independent computations: the linearisations of Fresnel's
  reflection against the engine's R at 1 000 random (n, θ) to 1e-12 and against Fresnel's formulae in 30-digit
  arithmetic; Malus's values and the reflected polarisation's against ``core.optics.polarization``; the dark rate
  against the detector model;
* every way of the bench gives its stated outcome on the built atlas (the readings of the atlas's points processed as
  the way says, fitted by ``tools.stats.linear_fit``): the sample's values (seed 1) as recorded in ``WAYS`` and in the
  report, and each within its own statistical spread of the computed value where the way is a right one;
* the Watch story: its captions' numbers are the run's, and every caption comes no later than its event;
* the bench's materials are the engine's (``materials.index`` in every segment's set-up); the detectors' dark counts and
  dead time against the closed forms of ``theories.models.photodetector``.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from u35_lab import SPECS, STEPS, V, VIZ, A, atlas_of, expected_row, fit, point, row  # noqa: E402

from lfphys.core.optics import interfaces, materials, polarization as pol_  # noqa: E402
from lfphys.theories.models import photodetector as pd  # noqa: E402
from lfviz import headless, registry  # noqa: E402

from u35_optics_bench import screens as S  # noqa: E402
from u35_optics_bench import viz as VIZ_MOD  # noqa: E402

N_BK7 = materials.index("schott_n_bk7", 632.8).real
GLASS = {"bk7": "schott_n_bk7", "f2": "schott_n_f2", "sf11": "schott_n_sf11"}
TH = SPECS["explore"]["controls"][0]["values"]


# --- every grid point of every atlas ---------------------------------------------------------------------------------
def _grid(spec):
    import itertools
    names = [c["param"] for c in spec["controls"]]
    return [dict(zip(names, combo)) for combo in itertools.product(*[c["values"] for c in spec["controls"]])]


def _stop_time(spec, oc):
    """The world time of a point's last frame by its stop rule (``headless.run_spec``): a world time, or the stop
    event + after_s; when that falls within the stop event's own frame (a frame_dt clock), one more full frame step
    after it (review R2-F F3: the stop event's frame is never the last)."""
    st = spec["stop"]
    if "world_s" in st:
        return st["world_s"]
    t = oc.stop_event_t + st.get("after_s", 0.0)
    dt = spec.get("frame_dt")
    if dt:
        k_ev = math.ceil(oc.stop_event_t / dt * (1 - 1e-12))  # the event's own frame: the first at or after it
        if t <= k_ev * dt * (1 + 1e-12):
            return (k_ev + 1) * dt
    return t


@pytest.mark.parametrize("aid", sorted(SPECS))
def test_every_grid_point_builds_with_its_checks_and_stops_by_its_rule(aid):
    spec = SPECS[aid]
    for values in _grid(spec):
        msgs, oc = A.run_point(V, spec, values)  # RunFailed on a check ending ✗ or a stop event not reached
        counts = oc.check_counts()
        # the checks shown: passes and information rows (review R2-W F3 moved the identities `sum`, `born` from the
        # passes to information; the dark-count bench then has 5 passes: arms, energy, brew, brewR, cfaceT)
        assert counts["failed"] == 0 and counts["ok"] >= 5 and counts["ok"] + counts["info"] > 7, (aid, values, counts)
        assert oc.t_end == pytest.approx(_stop_time(spec, oc), rel=1e-12), (aid, values, oc.t_end)
        frames = [m for m, _b in msgs if m["type"] == "frame"]
        assert frames[0]["meas"]["n_R"] is None  # nothing counted at t = 0 («Measure» says so before a launch)
        last = frames[-1]["meas"]
        for k in ("n_R", "n_T", "n_clicks"):  # the counters' readings: whole numbers ≥ 0
            assert isinstance(last[k], int) and last[k] >= 0, (aid, values, k, last[k])


def test_the_atlases_grids_are_the_designs():
    """Design §3.2–§3.5, §6: the grids and their sizes."""
    n = {aid: math.prod(len(c["values"]) for c in s["controls"]) for aid, s in SPECS.items()}
    assert n == {"explore": 456, "coatings": 91, "polarisation": 144, "lab.dark": 3, "lab.malus": 114,
                 "lab.reflection": 294}
    assert 40.0 in SPECS["polarisation"]["controls"][0]["values"]  # E35: a grid point below θ_c (linear light)
    assert len(TH) == 38 and {56.0, 57.0, 41.0, 42.0, 58.0, 60.0, 61.0, 38.0, 34.0, 35.0} <= set(TH)


def test_every_select_control_names_its_values_in_every_language():
    """Review R2-P F9: a control over a select's raw values (u35's polarisation "s" | "p", the analyser "ideal" |
    "real") names them with ``labels``, one text per value, each translated into Russian: shown raw, "s" became «с»
    (the msgid of seconds) and "real" stayed English."""
    from lfviz import i18n
    ru = i18n._merge("ru")[0]
    ctrls = [c for sc in VIZ["screens"] for c in sc.get("controls", [])]
    ctrls += [c for st in STEPS.values() for c in st.get("controls", [])]
    seen = 0
    for c in ctrls:
        if any(isinstance(v, str) for v in c["values"]):
            labels = c.get("labels")
            assert labels and len(labels) == len(c["values"]), c.get("param") or c.get("id")
            assert all(lb["$t"] in ru for lb in labels), [lb["$t"] for lb in labels]
            seen += 1
    assert seen >= 4  # the glass and side, the polarisation, the analyser, the glass of part 4


# --- the bench's computed values against independent computations -----------------------------------------------------
def test_the_linearisations_against_the_engines_R_at_random_n_and_theta():
    """y_s = (cos θ (1 + √R_s)/(1 − √R_s))² = n² − sin²θ for light from air, and below θ_B y_p = (cos θ (1 − √R_p)/(1 +
    √R_p))² = 1/n² − sin²θ/n⁴: the formula columns of part 1 against the engine's transfer matrices at 1 000 random
    (n, θ), to 1e-12 (relative)."""
    rng = random.Random(1)
    worst_s = worst_p = 0.0
    for _ in range(1000):
        n = rng.uniform(1.3, 2.0)
        th = math.radians(rng.uniform(0.0, 80.0))
        Rs = interfaces.stack([1.0, n], [], 600.0, th, "s")["R"]
        ys = (math.cos(th) * (1 + math.sqrt(Rs)) / (1 - math.sqrt(Rs))) ** 2
        worst_s = max(worst_s, abs(ys - (n * n - math.sin(th) ** 2)) / (n * n))
        thb = math.atan(n)
        th_p = rng.uniform(0.0, 0.98) * thb
        Rp = interfaces.stack([1.0, n], [], 600.0, th_p, "p")["R"]
        yp = (math.cos(th_p) * (1 - math.sqrt(Rp)) / (1 + math.sqrt(Rp))) ** 2
        worst_p = max(worst_p, abs(yp - (1 / n ** 2 - math.sin(th_p) ** 2 / n ** 4)) / (1 / n ** 2))
    assert worst_s < 1e-12 and worst_p < 1e-12, (worst_s, worst_p)


def test_the_linearisations_against_fresnels_formulae_in_30_digits():
    mp = pytest.importorskip("mpmath")
    mp.mp.dps = 30
    for n in (N_BK7, materials.index("schott_n_sf11", 632.8).real):
        N = mp.mpf(n)
        for deg in (0, 10, 30, 45, 52, 70, 80):
            th = mp.radians(deg)
            ct = mp.sqrt(1 - (mp.sin(th) / N) ** 2)
            rs = (mp.cos(th) - N * ct) / (mp.cos(th) + N * ct)
            ys = (mp.cos(th) * (1 + abs(rs)) / (1 - abs(rs))) ** 2
            assert abs(ys - (N ** 2 - mp.sin(th) ** 2)) < mp.mpf("1e-25")
            Rs = interfaces.stack([1.0, n], [], 632.8, math.radians(deg), "s")["R"]
            assert Rs == pytest.approx(float(rs ** 2), rel=1e-12, abs=1e-15)
            if math.radians(deg) < math.atan(n):
                rp = (N * mp.cos(th) - ct) / (N * mp.cos(th) + ct)
                yp = (mp.cos(th) * (1 - rp) / (1 + rp)) ** 2
                assert abs(yp - (1 / N ** 2 - mp.sin(th) ** 2 / N ** 4)) < mp.mpf("1e-25")


def test_the_lab_references_against_the_engine():
    sim = VIZ["simulation"]
    for g, gid in GLASS.items():
        n = materials.index(gid, 632.8).real
        fixed = registry.load(V)["schema"].resolve("boundary", {})[0]
        assert sim.lab_reference("fresnel", fixed, {}, f"ns2_{g}")["value"] == pytest.approx(n * n, rel=1e-15)
        assert sim.lab_reference("fresnel", fixed, {}, f"inv2_{g}")["value"] == pytest.approx(1 / n ** 2, rel=1e-15)
        # θ_c from inside: sin²θ_c = 1/n², the zero of the engine's transmission found by bisection
        lo, hi = 0.1, 1.5
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if interfaces.stack([n, 1.0], [], 632.8, mid, "s")["T"] > 0 else (lo, mid)
        assert sim.lab_reference("fresnel", fixed, {}, f"thc_{g}")["value"] == pytest.approx(math.sin(hi) ** 2,
                                                                                            rel=1e-12)
        # θ_B: the zero of the engine's r_p, found here by bisection
        lo, hi = 0.1, 1.5
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            if interfaces.stack([1.0, n], [], 632.8, mid, "p")["r"].real * \
                    interfaces.stack([1.0, n], [], 632.8, lo, "p")["r"].real > 0:
                lo = mid
            else:
                hi = mid
        assert sim.lab_reference("fresnel", fixed, {}, f"thb_{g}")["value"] == pytest.approx(math.degrees(lo), abs=1e-9)
        # the degree of polarisation (R_s − R_p)/(R_s + R_p): 1 at θ_B, its values listed at the grid's angles
        ths = SPECS["lab.reflection"]["controls"][0]["values"]
        ref = sim.lab_reference("reflection", fixed, {"theta_deg": ths}, f"dop_{g}")
        assert ref["value"] == pytest.approx(math.degrees(lo), abs=1e-9)
        items = ref["how"]["a"]["list"]["a"]  # join(): {p0: T("{th:g}°: {P:.4f}"), p1: …}
        shown = [x for x in ths if x in VIZ_MOD.DOP_SHOWN]
        assert len(items) == len(shown) == 4
        for i, th in enumerate(shown):
            Rs, Rp = (interfaces.stack([1.0, n], [], 632.8, math.radians(th), q)["R"] for q in ("s", "p"))
            assert items[f"p{i}"]["a"]["th"] == th
            assert items[f"p{i}"]["a"]["P"] == pytest.approx((Rs - Rp) / (Rs + Rp), rel=1e-12)
    fixed = registry.load(V)["schema"].resolve("lab_malus", {})[0]
    assert sim.lab_reference("malus", fixed, {}, "slope0_ideal")["value"] == pol_.malus(0.0, 0.0)
    from u35_optics_bench.schema import IMPERFECT
    k1, k2 = IMPERFECT
    assert sim.lab_reference("malus", fixed, {}, "slope_real")["value"] == pytest.approx(
        pol_.malus(0.0, 0.0, k1, k2) - pol_.malus(0.0, math.pi / 2, k1, k2), rel=1e-15)
    assert sim.lab_reference("malus", fixed, {}, "icept_real")["value"] == pol_.malus(0.0, math.pi / 2, k1, k2)
    fixed = registry.load(V)["schema"].resolve("lab_dark", {})[0]
    assert sim.lab_reference("dark", fixed, {}, "rate_r")["value"] == \
        pd.DEVICES["spcm_aqrh_14_650nm"]["detector"].dark_rate == 100.0


def test_the_reflected_degree_of_polarisation_on_the_bench_against_the_engine():
    """Part 3's P = 1 − 2f with the analyser along p is (R_s − R_p)/(R_s + R_p) of the reflected light: the run's
    probabilities against ``polarization.degree_from_powers``."""
    for th in (40.0, 56.0, 62.0):
        frames, header, _oc, _segs = point("lab.reflection", theta_deg=th, anaR_deg=0.0, glass="bk7")
        m = frames[-1]["meas"]
        Rs = interfaces.stack([1.0, N_BK7], [], 632.8, math.radians(th), "s")["R"]
        Rp = interfaces.stack([1.0, N_BK7], [], 632.8, math.radians(th), "p")["R"]
        assert 1 - 2 * m["fR_pass_ref"] == pytest.approx(pol_.degree_from_powers(Rs, Rp), abs=1e-6)


# --- the ways (design §3.4), on the built atlas's points --------------------------------------------------------------
#: the sample's outcomes (seed 1, the real detector, the 25 mm glass blocks and the reference count; numbers in the
#: report). Part 2: «_R» the ratio N_R/(N_R + N_T), «_d» R = (N_R/t)/(N₀/t₀) with the dark counts subtracted (R_d).
#: The other seeds (2–4) reproduce every way's status (review R2-W F1, the processor's numbers)
WAYS = {
    "w1_R": {"a": 2.3586, "a_se": 0.018},                                      # y_s from N_R/(N_R + N_T)
    "w1_d": {"a": 2.3046, "a_se": 0.019, "b": -1.0244},                         # y_s from R_d: right
    "w2_R": {"a": 0.42215},
    "w2_d": {"a": 0.43338, "a_se": 0.0046},
    "w3": {"a": 0.48545, "chi2_dof": 38.9},                                    # y_p through 62°
    "w4_50_62": {"vertex": 55.881, "vertex_se": 0.239},
    "w4_52_61": {"vertex": 56.336, "vertex_se": 0.190},
    "w8": {"a": 0.43257, "a_se": 0.0090},                                      # y_p (R_d) at a fifth of the run
    "w9": {"b": 0.99949, "b_se": 0.00027},
    "w10": {"chi2_dof": 2.48e4},
    "w11_line0": {"b": 0.9031, "chi2_dof": 13.8},
    "w11_line": {"a": 0.0097116, "b": 0.89069},
    "w16": {"rel": 0.00271},
    "w18_d": {"a": 0.45849},                                                   # from inside, y_p's formula, R_d
    "w18_norm": {"a": 0.43533},                                                # the same normalised by the TIR plateau
}


def _close(x, want, digits_rel=2e-3, abs_=None):
    return x == pytest.approx(want, rel=digits_rel, abs=abs_)


@pytest.fixture(scope="module")
def fresnel_rows():
    return {(pol, th): row("fresnel", theta_deg=th, sample="bk7_air", light=pol) for pol in ("s", "p") for th in TH}


@pytest.fixture(scope="module")
def fresnel_expected():
    return {(pol, th): expected_row("fresnel", theta_deg=th, sample="bk7_air", light=pol) for pol in ("s", "p")
            for th in TH}


def _fits(rows, exp, x, y, model):
    """The sample's fit and the same fit on the expected counts (the way's computed outcome)."""
    return fit(rows, x, y, model), fit(exp, x, y, model)


def test_way_1_and_2_the_index_from_s_and_p_light(fresnel_rows, fresnel_expected):
    """Ways 1 and 2: y_s against sin²θ (θ ≤ 80°) and y_p below θ_B (θ ≤ 52°), lines. With R = (N_R/t)/(N₀/t₀) and the
    dark counts subtracted (y from R_d) the index is right; with N_R/(N_R + N_T) wrong: the transmitted photons lose
    4.8 % in the glass block (its curved face 4.2 %, the glass 0.6 %), which the ratio counts as reflected light;
    against the reference with the dark counts left in (R_i), R is high by d(1 − R)/(rate·η + d). Each sample's line
    lies within 3σ of the same fit on the expected counts, which carries the computed reason."""
    for way, pol, top, ycols, truth in (("w1", "s", 80, ("ys", "ysd"), N_BK7 ** 2),
                                        ("w2", "p", 52, ("yp", "ypd"), 1 / N_BK7 ** 2)):
        rows = [fresnel_rows[(pol, t)] for t in TH if t <= top]
        exp = [fresnel_expected[(pol, t)] for t in TH if t <= top]
        out = {}
        for tag, y in zip(("R", "d"), ycols):
            f, e = _fits(rows, exp, "x", y, "line")
            out[tag] = (f, e)
            assert _close(f["params"][0], WAYS[f"{way}_{tag}"]["a"], 1e-4), (way, tag, f["params"])
            assert abs(f["params"][0] - e["params"][0]) < 3 * f["sigma"][0], (way, tag)
        f, e = out["d"]  # right: the expectation is the truth within a fifth of an error; the sample within 3σ
        assert abs(e["params"][0] - truth) < 0.2 * e["sigma"][0] and abs(f["params"][0] - truth) < 3 * f["sigma"][0]
        f, e = out["R"]  # wrong: the block's loss moves the expectation by more than 2.5σ
        assert abs(e["params"][0] - truth) > 2.5 * e["sigma"][0], (way, e["params"][0], truth)
    f1 = fit([fresnel_rows[("s", t)] for t in TH if t <= 80], "x", "ysd", "line")
    assert _close(f1["sigma"][0], WAYS["w1_d"]["a_se"], 0.05) and _close(f1["params"][1], WAYS["w1_d"]["b"], 1e-3)
    assert abs(f1["params"][1] + 1) < 3 * f1["sigma"][1]
    # R_i keeps the dark counts: at θ = 0 it exceeds R_d by d(1 − R)/(rate·η + d) (the dead time aside)
    from lfphys.theories.models import photodetector as pd
    det = pd.DEVICES["spcm_aqrh_14_650nm"]["detector"]
    e0 = fresnel_expected[("s", 0.0)]
    R0 = ((N_BK7 - 1) / (N_BK7 + 1)) ** 2
    assert e0["Ri"][0] - e0["Rid"][0] == pytest.approx(det.dark_rate * (1 - R0) / (2e5 * det.eta + det.dark_rate),
                                                       rel=0.02)


def test_way_3_p_light_past_brewster_with_the_same_formula(fresnel_rows, fresnel_expected):
    """Way 3 (wrong: a sign branch): through 62°, past θ_B, r_p < 0 and y_p needs −√R_p: the fit misses."""
    f3, e3 = _fits([fresnel_rows[("p", t)] for t in TH if t <= 62], [fresnel_expected[("p", t)] for t in TH if t <= 62],
                   "x", "yp", "line")
    assert _close(f3["params"][0], WAYS["w3"]["a"], 1e-3) and f3["chi2_dof"] == pytest.approx(WAYS["w3"]["chi2_dof"],
                                                                                               rel=0.01)
    assert 1 / math.sqrt(f3["params"][0]) < N_BK7 - 0.05 and f3["chi2_dof"] > 10 and e3["chi2_dof"] > 10


def test_way_4_a_parabola_through_R_p_near_brewster(fresnel_rows, fresnel_expected):
    """Way 4 (an approximation): R_p is not symmetric about θ_B: the vertex falls below it, on the expected counts too
    (by 0.47° over 50–62°, 0.29° over 52–61°)."""
    thb = math.degrees(math.atan(N_BK7))
    for lo, hi in ((50, 62), (52, 61)):
        f, e = _fits([fresnel_rows[("p", t)] for t in TH if lo <= t <= hi],
                     [fresnel_expected[("p", t)] for t in TH if lo <= t <= hi], "th", "Ri", "quadratic")
        want = WAYS[f"w4_{lo}_{hi}"]
        assert _close(f["vertex"], want["vertex"], 2e-4) and _close(f["vertex_sigma"], want["vertex_se"], 0.05)
        assert f["vertex"] < thb and abs(f["vertex"] - e["vertex"]) < 3 * f["vertex_sigma"]
        assert thb - e["vertex"] > 0.25


def test_way_5_6_7_8_on_the_built_points(fresnel_rows, fresnel_expected):
    # way 5: the smallest p count in 1° steps lies at 55–57° (the dark counts, ~10 per detector, are the floor)
    nr = {t: fresnel_rows[("p", t)]["NR"][0] for t in (54, 55, 56, 57, 58, 59)}
    assert min(nr.values()) == min(nr[t] for t in (55, 56, 57)) and min(nr.values()) < 20
    # way 6: from inside, the last angle with transmitted photons lies between 41° and 42° (θ_c = 41.30°)
    nt = {t: row("fresnel", theta_deg=t, sample="bk7_in", light="s")["NT"][0] for t in (41.0, 42.0)}
    assert nt[41.0] > 1000 and nt[42.0] < 40  # beyond θ_c only the dark counts
    # way 7: the formula for light from air used from inside: beyond θ_c R is 1 but for the dark counts: y_s is huge
    ys = row("fresnel", theta_deg=45.0, sample="bk7_in", light="s")["ys"]
    assert ys is not None and ys[0] > 1e5
    # way 8: the cursor at a fifth of the run: the errors of the line about √5 larger (the expected counts: 2.225; a
    # sample's errors come from its own counts, a few at 45–52° in 0.02 s: 0.87–1.16 of that on seeds 1–4), the same
    # index
    f8 = fit([row("fresnel", 1, theta_deg=t, sample="bk7_air", light="p") for t in TH if t <= 52], "x", "ypd", "line")
    f2 = fit([fresnel_rows[("p", t)] for t in TH if t <= 52], "x", "ypd", "line")
    e8 = fit([expected_row("fresnel", 1, theta_deg=t, sample="bk7_air", light="p") for t in TH if t <= 52], "x", "ypd",
             "line")
    e2 = fit([fresnel_expected[("p", t)] for t in TH if t <= 52], "x", "ypd", "line")
    assert _close(f8["params"][0], WAYS["w8"]["a"], 1e-3) and _close(f8["sigma"][0], WAYS["w8"]["a_se"], 0.05)
    assert e8["sigma"][0] / e2["sigma"][0] == pytest.approx(math.sqrt(5), rel=0.01)
    assert f8["sigma"][0] / f2["sigma"][0] == pytest.approx(e8["sigma"][0] / e2["sigma"][0], rel=0.2)
    assert abs(f8["params"][0] - 1 / N_BK7 ** 2) < 3 * f8["sigma"][0]


def test_ways_9_10_11_malus():
    al = SPECS["lab.malus"]["controls"][0]["values"]
    ideal = [row("malus", anaT_deg=a, psi_deg=30.0, analyser="ideal") for a in al]
    f9 = fit(ideal, "c2", "I", "line0")
    assert _close(f9["params"][0], WAYS["w9"]["b"], 1e-5) and abs(f9["params"][0] - 1) < 3 * f9["sigma"][0] + 1e-3
    f10 = fit(ideal, "c1", "I", "line0")
    assert f10["chi2_dof"] > 1e4  # a wrong angle law: the points lie on x², not on a line
    real = [row("malus", anaT_deg=a, psi_deg=30.0, analyser="real") for a in al]
    f11 = fit(real, "c2", "I", "line0")
    assert _close(f11["params"][0], WAYS["w11_line0"]["b"], 1e-3) and f11["chi2_dof"] > 5
    f11b = fit(real, "c2", "I", "line")
    a, b = f11b["params"]
    assert _close(a, WAYS["w11_line"]["a"], 2e-3) and _close(b, WAYS["w11_line"]["b"], 1e-4)
    assert abs(a - 0.009) < 3 * f11b["sigma"][0] + 1e-3 and abs(b - 0.891) < 3 * f11b["sigma"][1] + 1e-3


def test_ways_12_to_15_polarisation_by_reflection():
    """Way 12 (right, coarse): with the analyser along p the reflected light is completely polarised near θ_B, P ≈ 1
    once the dark counts are subtracted (way 15); way 14: left in, the pass port's dark counts hold P below 1 by many
    errors; way 13: both ports added, the reflection only grows with the angle. The vertex of a parabola through f, or
    through P (the law «P = (R_s − R_p)/(R_s + R_p) largest»), lies at θ_B within its errors."""
    rr = {t: row("reflection", theta_deg=t, anaR_deg=0.0, glass="bk7")
          for t in SPECS["lab.reflection"]["controls"][0]["values"]}
    for t in (55.0, 56.0, 57.0, 58.0):
        assert 1 - rr[t]["P"][0] > 3 * rr[t]["P"][1] and abs(rr[t]["Pd"][0] - 1) < 3 * rr[t]["Pd"][1]
    dark = {t: r["Pd"][0] for t, r in rr.items()}
    assert max(dark, key=dark.get) in (56.0, 57.0, 58.0)
    ns = [rr[t]["Ns"][0] for t in sorted(rr)]
    assert all(b > a for a, b in zip(ns, ns[1:]))  # way 13: no minimum near θ_B
    thb = math.degrees(math.atan(N_BK7))
    ff, fp = fit(list(rr.values()), "th", "f", "quadratic"), fit(list(rr.values()), "th", "P", "quadratic")
    assert ff["vertex"] == pytest.approx(fp["vertex"], rel=1e-9)  # P = 1 − 2f: the same vertex
    assert abs(ff["vertex"] - thb) < 3 * ff["vertex_sigma"] * max(1.0, math.sqrt(ff["chi2_dof"]))


def test_way_16_the_dead_time_at_normal_incidence():
    """R = (N_R/t)/(N₀/t₀) with the dark counts subtracted, without the dead-time correction: the reference detector
    (1.3·10⁵ counts per second) loses m₀·t_d of its counts, the reflection detector almost nothing: R too high by
    (m₀ − m_R)·t_d ≈ 0.27 %."""
    r = row("fresnel", theta_deg=0.0, sample="bk7_air", light="s")
    rel = (r["Rid"][0] - r["Ric"][0]) / r["Ric"][0]
    assert _close(rel, WAYS["w16"]["rel"], 0.02)
    m_0, m_R = r["N0"][0] / r["t0"][0], r["NR"][0] / r["tc"][0]
    assert rel == pytest.approx((m_0 - m_R) * S.DEAD_TIME, rel=0.05)


def test_way_17_reflected_and_transmitted_do_not_add_to_one(fresnel_expected):
    """At θ = 0: R + T per incident photon falls short of 1 by the block's loss (the transmitted beam crosses 25 mm of
    glass and its curved face): T = (1 − R) T_c τ, where the face's own R + T = 1."""
    r = row("fresnel", theta_deg=0.0, sample="bk7_air", light="s")
    e = fresnel_expected[("s", 0.0)]
    tot, se = r["Rid"][0] + r["Ti"][0], math.hypot(r["Rid"][1], r["Ti"][1])
    assert 1 - tot > 2.5 * se and abs(r["Ti"][0] - e["Ti"][0]) < 3 * r["Ti"][1]
    n = N_BK7
    R = ((n - 1) / (n + 1)) ** 2
    tau = math.exp(-4 * math.pi * materials.index("schott_n_bk7", 632.8).imag * 25e6 / 632.8)
    assert e["Ti"][0] == pytest.approx((1 - R) * (1 - R) * tau, rel=3e-3)  # dead time and dark counts aside


def test_way_18_the_critical_angle_from_inside():
    """From inside, s light below θ_c: y_p's formula gives 1/n² − sin²θ, zero at θ_c (the law sin²θ_c = 1/n²). Against
    the reference count (the block removed) R is short by the block's round trip (T_c τ)² = 0.907, seen as the plateau
    of total reflection: the line misses 1/n² by about six errors; divided by that plateau, the right index."""
    ins = {t: row("fresnel", theta_deg=t, sample="bk7_in", light="s") for t in TH}
    below = [ins[t] for t in TH if t <= 40]
    fd = fit(below, "x", "ypd", "line")
    assert _close(fd["params"][0], WAYS["w18_d"]["a"], 1e-4) and fd["params"][0] - 1 / N_BK7 ** 2 > 3 * fd["sigma"][0]
    tir = [ins[t]["Rid"] for t in TH if t >= 42]
    w = [1 / s_ ** 2 for _v, s_ in tir]
    plat, plat_se = sum(v * wi for (v, _s), wi in zip(tir, w)) / sum(w), sum(w) ** -0.5
    k = math.exp(-4 * math.pi * materials.index("schott_n_bk7", 632.8).imag * 25e6 / 632.8)
    roundtrip = (4 * N_BK7 / (N_BK7 + 1) ** 2 * k) ** 2
    assert abs(plat - roundtrip) < 3 * plat_se
    rows = []
    from lfviz import expr
    for r in below:
        v, s_ = r["Rid"]
        Rn = v / plat
        yv, ys_, *_ = expr.evaluate("(cosd(th) * (1 - sqrt(Rn)) / (1 + sqrt(Rn)))^2",
                                    {"th": r["th"], "Rn": (Rn, Rn * math.hypot(s_ / v, plat_se / plat))})
        rows.append({"x": r["x"], "yn": (yv, ys_)})
    fn = fit(rows, "x", "yn", "line")
    assert _close(fn["params"][0], WAYS["w18_norm"]["a"], 1e-4) and abs(fn["params"][0] - 1 / N_BK7 ** 2) < 3 * fn[
        "sigma"][0]


def test_way_19_the_denser_glasses():
    """N-F2 and N-SF11 from air, s light: the ratio N_R/(N_R + N_T) misses n² by more (their blocks lose 6.4 % and
    9.6 %), R against the reference with the dark counts subtracted gives it."""
    for g, gid in (("f2", "schott_n_f2"), ("sf11", "schott_n_sf11")):
        n = materials.index(gid, 632.8).real
        rows = [row("fresnel", theta_deg=t, sample=f"{g}_air", light="s") for t in TH if t <= 80]
        fR, fd = fit(rows, "x", "ys", "line"), fit(rows, "x", "ysd", "line")
        assert fR["params"][0] - n * n > 3 * fR["sigma"][0] and abs(fd["params"][0] - n * n) < 3 * fd["sigma"][0]


# --- the Watch story --------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def story():
    rec = next(r for r in VIZ["recordings"] if r["id"] == "story")
    msgs = []
    out = headless.run_spec(V, rec["preset"], {}, rec["seed"], {"fps": rec["fps"], "speed": rec.get("speed")},
                            {"seconds": rec["seconds"]}, rec["script"], lambda m, b=None: msgs.append((m, b)),
                            captions=rec["captions"], end_reason="test")
    return rec, out, msgs


def test_the_story_runs_with_every_check_and_its_segments(story):
    rec, out, msgs = story
    assert out.frames == rec["seconds"] * rec["fps"] and out.check_counts()["failed"] == 0
    segs = [m for m, _b in msgs if m["type"] == "segment"]
    kinds = [(s["setup"]["med_in"], s["setup"]["theta"], s["setup"]["kind"],
              (s["setup"]["ana"]["R"] or {}).get("alpha"),
              s["setup"]["layers"] and s["setup"]["layers"][0]["d"]) for s in segs]
    assert kinds == [("air", 30.0, "interface", None, []), ("air", round(S.THETA_B, 3), "interface", 0.0, []),
                     ("air", round(S.THETA_B, 3), "interface", 90.0, []), ("schott_n_bk7", 30.0, "tir", None, []),
                     ("schott_n_bk7", 45.0, "tir", None, []), ("schott_n_bk7", 45.0, "tir", None, 200.0)]


def test_every_caption_comes_no_later_than_its_event(story):
    rec, _out, msgs = story
    fps = rec["fps"]
    frames = [m for m, _b in msgs if m["type"] == "frame"]
    ft = np.array([f["t"] for f in frames])
    played = lambda tw: int(np.searchsorted(ft, tw - 1e-18)) / fps  # noqa: E731 - the first frame showing time tw
    caps = {c["at"]: c for c in rec["captions"]}
    # the first photon: emitted after STORY_SLOW_AT, at the surface after caption 0, detected after caption 1 and
    # before the speed-up at 9 s (a photon, not a dark count)
    flights = [k / fps for k, f in enumerate(frames) if f["in_flight"]]
    assert flights and flights[0] >= S.STORY_SLOW_AT and flights[0] > caps[0]["at"]
    first = next((m["t"], b) for m, b in msgs
                 if m["type"] == "clicks" and len(b["t"]) and any(p != 9 for p in b["pol"]))
    assert caps[3.5]["at"] <= played(first[0]) < 9.0
    # each set-up change comes at its caption's frame
    for s in [m for m, _b in msgs if m["type"] == "segment"][1:]:
        assert played(s["t"]) in caps and caps[played(s["t"])]["at"] == played(s["t"])


def test_the_captions_numbers_are_the_runs(story):
    rec, _out, msgs = story
    segs = [m for m, _b in msgs if m["type"] == "segment"]
    frames = [m for m, _b in msgs if m["type"] == "frame"]
    fps = rec["fps"]
    a = {c["at"]: c["text"]["a"] for c in rec["captions"] if c["text"].get("a")}
    assert a[0]["n"] == segs[0]["setup"]["n_out"] == N_BK7
    P8 = segs[0]["P8"]
    assert a[9]["R"] == pytest.approx(100 * segs[0]["P"]["R_pass"], abs=5e-4)  # the surface: 4.350 %
    assert a[9]["l"] == pytest.approx(100 * (1 - P8["T_pass"] / segs[0]["P"]["T_pass"]), abs=5e-4)  # the block: 4.775 %
    assert a[9]["r"] == pytest.approx(100 * P8["R_pass"] / (P8["R_pass"] + P8["T_pass"]), abs=5e-4)  # 4.558 %
    assert a[9]["t"] == pytest.approx(100 * P8["T_pass"] / (P8["R_pass"] + P8["T_pass"]), abs=5e-3)  # 95.44 %
    m17 = frames[17 * fps - 1]["meas"]  # the counts by the caption at 17 s: within 3σ of the computed fraction
    assert abs(m17["R_frac"] - m17["R_frac_ref"]) < 3 * m17["R_frac_se"]
    assert a[17]["b"] == pytest.approx(math.degrees(math.atan(N_BK7)), abs=1e-9) and segs[1]["P"]["R_pass"] < 1e-12
    m22 = frames[22 * fps - 1]["meas"]  # the pass detector clicked only in the dark: about once per played second
    assert m22["n_Rp"] <= 15 and segs[1]["P"]["R_reject"] > 0.07
    assert a[27]["r"] == pytest.approx(100 * segs[3]["P"]["R_pass"], abs=5e-3)  # 5.85 %
    assert a[34]["c"] == pytest.approx(math.degrees(math.asin(1 / N_BK7)), abs=1e-9)
    assert segs[4]["P"]["R_pass"] == pytest.approx(1.0, abs=1e-12)
    assert 0.4 < segs[5]["P"]["T_pass"] < 0.5  # «nearly half» tunnel through the 200 nm gap


def test_the_other_recordings_numbers():
    rec = {r["id"]: r for r in VIZ["recordings"]}
    a = rec["brewster"]["captions"][0]["text"]["a"]
    Rs = interfaces.stack([1.0, N_BK7], [], 632.8, math.atan(N_BK7), "s")["R"]
    assert a["b"] == pytest.approx(math.degrees(math.atan(N_BK7)), abs=1e-9)
    assert a["r"] == pytest.approx(50 * Rs, abs=5e-4)
    assert rec["tir"]["captions"][0]["text"]["a"]["c"] == pytest.approx(math.degrees(math.asin(1 / N_BK7)), abs=1e-9)
    au = materials.index("au_johnson_christy", 632.8)
    rp = [interfaces.stack([N_BK7, au, 1.0], [50.0], 632.8, math.radians(x), "p")["R"] for x in (43.773,)]
    assert rec["spr"]["captions"][1]["text"]["a"]["r"] == pytest.approx(100 * rp[0], abs=0.01)


# --- materials and detectors ----------------------------------------------------------------------------------------
def test_the_benchs_materials_are_the_engines():
    for sample in S.SAMPLES:
        _frames, header, _oc, segs = point("explore", theta_deg=30.0, sample=sample, light="s")
        p = header["params"]
        for side, key in (("med_in", "n_in"), ("med_out", "n_out")):
            m = p[side]
            want = 1.0 if m == "air" else materials.index(m, 632.8).real
            assert segs[0]["setup"][key] == want and segs[0]["setup"][side] == m
    from u35_optics_bench.engine.bench import build_structure
    params = registry.load(V)["schema"].resolve("coatings", {"structure": "bragg", "pairs": 8})[0]
    st = build_structure(params, 550.0)
    assert complex(st.layers[0][0]) == materials.index("ta2o5_film_gao", 550.0)
    assert complex(st.layers[1][0]) == materials.index("sio2_film_gao", 550.0)
    assert st.n_out == materials.index("schott_n_bk7", 550.0).real


def test_the_dark_counts_against_the_detector_model():
    """Part 0: the shutter closed, the counts are the detectors' dark counts: Poisson of mean d·t (100 s⁻¹)."""
    from scipy import stats as sps
    d = pd.DEVICES["spcm_aqrh_14_650nm"]["detector"]
    tot, mu = 0, 0.0
    for g in (0.1, 0.5, 1.0):
        r = row("dark", gate_s=g)
        for k in ("NR", "NT"):
            tot += int(r[k][0])
            mu += d.dark_rate * g
    assert sps.poisson.cdf(tot, mu) > 1e-4 and sps.poisson.sf(tot - 1, mu) > 1e-4, (tot, mu)
    # no photon was sent: the fractions of dark counts are shown without a computed value to compare with
    frames, _h, _oc, _segs = point(atlas_of("dark"), gate_s=0.5)
    m = frames[-1]["meas"]
    assert m["n_emit"] == 0 and m["R_frac"] is not None
    assert m["R_frac_ref"] is None and m["T_frac_ref"] is None


def test_the_dead_time_against_the_closed_form():
    """At normal incidence the transmission detector counts ~1.2·10⁵ s⁻¹: its recorded rate is the non-paralysable
    m = n/(1 + n t_d) of its input (``photodetector.observed_rate``), within the counts' spread."""
    frames, header, oc, segs = point("explore", theta_deg=0.0, sample="bk7_air", light="s")
    msgs = []
    out = headless.run_spec(V, "boundary", {"theta_deg": 0.0}, 1, {"frame_dt": 0.02}, {"world_s": 0.1}, None,
                            lambda m, b=None: msgs.append((m, b)), end_reason="test")
    chk = [m for m, _b in msgs if m["type"] == "check" and m["id"] == "det0"][-1]
    assert chk["ok"] is True
    d = pd.DEVICES["spcm_aqrh_14_650nm"]["detector"]
    n_in = segs[0]["P8"]["T_pass"] * 2e5 * d.eta + d.dark_rate  # the photons that cross the block to the detector
    m_expected = float(pd.observed_rate(n_in, d.dead_time))
    m_seen = frames[-1]["meas"]["n_T"] / 0.1
    assert m_seen == pytest.approx(m_expected, rel=4 * math.sqrt(m_expected * 0.1) / (m_expected * 0.1))
