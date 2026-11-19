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
from u35_lab import SPECS, STEPS, V, VIZ, A, atlas_of, fit, point, row  # noqa: E402

from lfphys.core.optics import interfaces, materials, polarization as pol_  # noqa: E402
from lfphys.theories.models import photodetector as pd  # noqa: E402
from lfviz import headless, registry  # noqa: E402

from u35_optics_bench import screens as S  # noqa: E402

N_BK7 = materials.index("schott_n_bk7", 632.8).real
GLASS = {"bk7": "schott_n_bk7", "f2": "schott_n_f2", "sf11": "schott_n_sf11"}
TH = SPECS["explore"]["controls"][0]["values"]


# --- every grid point of every atlas ---------------------------------------------------------------------------------
def _grid(spec):
    import itertools
    names = [c["param"] for c in spec["controls"]]
    return [dict(zip(names, combo)) for combo in itertools.product(*[c["values"] for c in spec["controls"]])]


def _stop_time(spec, oc):
    st = spec["stop"]
    if "world_s" in st:
        return st["world_s"]
    return oc.stop_event_t + st.get("after_s", 0.0)


@pytest.mark.parametrize("aid", sorted(SPECS))
def test_every_grid_point_builds_with_its_checks_and_stops_by_its_rule(aid):
    spec = SPECS[aid]
    for values in _grid(spec):
        msgs, oc = A.run_point(V, spec, values)  # RunFailed on a check ending ✗ or a stop event not reached
        counts = oc.check_counts()
        assert counts["failed"] == 0 and counts["ok"] > 5, (aid, values, counts)
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
        assert sim.lab_reference("fresnel", fixed, {}, f"inv4_{g}")["value"] == pytest.approx(-1 / n ** 4, rel=1e-15)
        # θ_B: the zero of the engine's r_p, found here by bisection
        lo, hi = 0.1, 1.5
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            if interfaces.stack([1.0, n], [], 632.8, mid, "p")["r"].real * \
                    interfaces.stack([1.0, n], [], 632.8, lo, "p")["r"].real > 0:
                lo = mid
            else:
                hi = mid
        for step in ("fresnel", "reflection"):
            assert sim.lab_reference(step, fixed, {}, f"thb_{g}")["value"] == pytest.approx(math.degrees(lo), abs=1e-9)
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
        frames, header, _oc, _segs = point("lab.reflection", theta_deg=th, anaR_deg=0.0, med_out="schott_n_bk7")
        m = frames[-1]["meas"]
        Rs = interfaces.stack([1.0, N_BK7], [], 632.8, math.radians(th), "s")["R"]
        Rp = interfaces.stack([1.0, N_BK7], [], 632.8, math.radians(th), "p")["R"]
        assert 1 - 2 * m["fR_pass_ref"] == pytest.approx(pol_.degree_from_powers(Rs, Rp), abs=1e-6)


# --- the ways (design §3.4), on the built atlas's points --------------------------------------------------------------
#: the sample's outcomes (seed 1, the real detector; the report's table); a value to its printed digits
WAYS = {
    "w1": {"a": 2.3040, "a_se": 0.0156, "b": -1.006, "chi2_dof": 0.92},       # y_s, dark subtracted (ysd)
    "w1_raw": {"a": 2.3200, "a_se": 0.0156, "chi2_dof": 0.92},                 # y_s from the raw counts
    "w2": {"a": 0.43268, "a_se": 0.0040, "chi2_dof": 1.04},                    # y_p ≤ 52°, dark subtracted (ypd)
    "w2_raw": {"a": 0.43132, "a_se": 0.0038},
    "w3": {"a": 0.4917, "chi2_dof": 34.6},                                     # y_p through 62°
    "w4_50_62": {"vertex": 56.13, "vertex_se": 0.20},
    "w4_52_61": {"vertex": 56.21, "vertex_se": 0.30},
    "w8": {"a": 0.4256, "a_se": 0.0088},                                       # y_p at a fifth of the run
    "w9": {"b": 0.99928, "b_se": 0.00030},
    "w10": {"chi2_dof": 2.47e4},
    "w11_line0": {"b": 0.9016, "chi2_dof": 12.1},
    "w11_line": {"a": 0.00929, "b": 0.8897},
    "w16": {"rel": 0.00247},
}


def _close(x, want, digits_rel=2e-3, abs_=None):
    return x == pytest.approx(want, rel=digits_rel, abs=abs_)


@pytest.fixture(scope="module")
def fresnel_rows():
    return {(pol, th): row("fresnel", theta_deg=th, sample="bk7_air", pol=pol) for pol in ("s", "p") for th in TH}


def test_way_1_and_2_the_index_from_s_and_p_light(fresnel_rows):
    """Ways 1 and 2 (right): y_s against sin²θ (θ ≤ 80°) and y_p against sin²θ below θ_B (θ ≤ 52°), lines; with the
    real detectors the dark counts (100 s⁻¹ in each) bias R by about one error unless subtracted (columns Rd, ysd, ypd).
    """
    s_rows = [fresnel_rows[("s", t)] for t in TH if t <= 80]
    p_rows = [fresnel_rows[("p", t)] for t in TH if t <= 52]
    f1 = fit(s_rows, "x", "ysd", "line")
    a, b = f1["params"]
    assert _close(a, WAYS["w1"]["a"], 1e-4) and _close(f1["sigma"][0], WAYS["w1"]["a_se"], 0.02)
    assert _close(b, WAYS["w1"]["b"], 1e-3) and abs(f1["chi2_dof"] - WAYS["w1"]["chi2_dof"]) < 0.01
    assert abs(a - N_BK7 ** 2) < 3 * f1["sigma"][0] and abs(b + 1) < 3 * f1["sigma"][1]  # right: within its spread
    f1r = fit(s_rows, "x", "ys", "line")
    assert _close(f1r["params"][0], WAYS["w1_raw"]["a"], 1e-4)
    f2 = fit(p_rows, "x", "ypd", "line")
    assert _close(f2["params"][0], WAYS["w2"]["a"], 1e-4) and abs(f2["params"][0] - 1 / N_BK7 ** 2) < 3 * f2["sigma"][0]
    assert _close(fit(p_rows, "x", "yp", "line")["params"][0], WAYS["w2_raw"]["a"], 1e-4)


def test_way_3_p_light_past_brewster_with_the_same_formula(fresnel_rows):
    """Way 3 (wrong: a sign branch): through 62°, past θ_B, r_p < 0 and y_p needs −√R_p: the fit misses."""
    f3 = fit([fresnel_rows[("p", t)] for t in TH if t <= 62], "x", "yp", "line")
    assert _close(f3["params"][0], WAYS["w3"]["a"], 1e-3) and f3["chi2_dof"] == pytest.approx(WAYS["w3"]["chi2_dof"],
                                                                                               rel=0.01)
    assert 1 / math.sqrt(f3["params"][0]) < N_BK7 - 0.05 and f3["chi2_dof"] > 10


def test_way_4_a_parabola_through_R_p_near_brewster(fresnel_rows):
    """Way 4 (an approximation): R_p is not symmetric about θ_B: the vertex falls below it."""
    thb = math.degrees(math.atan(N_BK7))
    for lo, hi in ((50, 62), (52, 61)):
        f = fit([fresnel_rows[("p", t)] for t in TH if lo <= t <= hi], "th", "R", "quadratic")
        want = WAYS[f"w4_{lo}_{hi}"]
        assert _close(f["vertex"], want["vertex"], 2e-4) and _close(f["vertex_sigma"], want["vertex_se"], 0.05)
        assert f["vertex"] < thb


def test_way_5_6_7_8_on_the_built_points(fresnel_rows):
    # way 5: the smallest p count in 1° steps lies at 56–57° (the dark counts, ~10 per detector, are the floor)
    nr = {t: fresnel_rows[("p", t)]["NR"][0] for t in (54, 55, 56, 57, 58, 59)}
    assert min(nr, key=nr.get) in (56, 57)
    # way 6: from inside, the last angle with transmitted photons lies between 41° and 42° (θ_c = 41.30°)
    nt = {t: row("fresnel", theta_deg=t, sample="bk7_in", pol="s")["NT"][0] for t in (41.0, 42.0)}
    assert nt[41.0] > 1000 and nt[42.0] < 40  # beyond θ_c only the dark counts
    # way 7: the formula for light from air used from inside: beyond θ_c R is 1 but for the dark counts: y_s is huge
    ys = row("fresnel", theta_deg=45.0, sample="bk7_in", pol="s")["ys"]
    assert ys is not None and ys[0] > 1e5
    # way 8: the cursor at a fifth of the run: errors √5 larger
    f8 = fit([row("fresnel", 1, theta_deg=t, sample="bk7_air", pol="p") for t in TH if t <= 52], "x", "yp", "line")
    f2 = fit([fresnel_rows[("p", t)] for t in TH if t <= 52], "x", "yp", "line")
    assert _close(f8["params"][0], WAYS["w8"]["a"], 1e-3)
    assert f8["sigma"][0] / f2["sigma"][0] == pytest.approx(math.sqrt(5), rel=0.1)


def test_ways_9_10_11_malus():
    al = SPECS["lab.malus"]["controls"][0]["values"]
    ideal = [row("malus", anaT_deg=a, psi_deg=30.0, anaT="ideal") for a in al]
    f9 = fit(ideal, "c2", "I", "line0")
    assert _close(f9["params"][0], WAYS["w9"]["b"], 1e-5) and abs(f9["params"][0] - 1) < 3 * f9["sigma"][0] + 1e-3
    f10 = fit(ideal, "c1", "I", "line0")
    assert f10["chi2_dof"] > 1e4  # a wrong angle law: the points lie on x², not on a line
    real = [row("malus", anaT_deg=a, psi_deg=30.0, anaT="real") for a in al]
    f11 = fit(real, "c2", "I", "line0")
    assert _close(f11["params"][0], WAYS["w11_line0"]["b"], 1e-3) and f11["chi2_dof"] > 5
    f11b = fit(real, "c2", "I", "line")
    a, b = f11b["params"]
    assert _close(a, WAYS["w11_line"]["a"], 2e-3) and _close(b, WAYS["w11_line"]["b"], 1e-4)
    assert abs(a - 0.009) < 3 * f11b["sigma"][0] + 1e-3 and abs(b - 0.891) < 3 * f11b["sigma"][1] + 1e-3


def test_ways_12_to_15_polarisation_by_reflection():
    """Way 12 (right, coarse): with the analyser along p the reflected light is completely polarised near θ_B, P ≈ 1
    once the dark counts are subtracted (way 15); way 14: left in, the dark counts hold P at about 0.97–0.98 with no
    clear maximum; way 13: both ports added, the reflection only grows with the angle."""
    rr = {t: row("reflection", theta_deg=t, anaR_deg=0.0, med_out="schott_n_bk7")
          for t in SPECS["lab.reflection"]["controls"][0]["values"]}
    raw = {t: r["P"][0] for t, r in rr.items()}
    dark = {t: r["Pd"][0] for t, r in rr.items()}
    for t in (55.0, 56.0, 57.0, 58.0):
        assert 0.965 < raw[t] < 0.985 and abs(dark[t] - 1) < 3 * rr[t]["Pd"][1]
    assert max(dark, key=dark.get) in (56.0, 57.0, 58.0)
    ns = [rr[t]["Ns"][0] for t in sorted(rr)]
    assert all(b > a for a, b in zip(ns, ns[1:]))  # way 13: no minimum near θ_B


def test_way_16_the_dead_time_at_normal_incidence():
    r = row("fresnel", theta_deg=0.0, sample="bk7_air", pol="s")
    rel = (r["R"][0] - r["Rc"][0]) / r["Rc"][0]
    assert _close(rel, WAYS["w16"]["rel"], 0.02)
    # the closed form of the bias: the transmission detector loses m·t_d of its counts, the reflection one ~nothing
    m_T = r["NT"][0] / r["tc"][0]
    assert rel == pytest.approx((1 - r["R"][0]) * m_T * S.DEAD_TIME, rel=0.05)


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
    assert a[9]["r"] == pytest.approx(100 * segs[0]["P"]["R_pass"], abs=5e-4)  # 4.350 %
    assert a[9]["t"] == pytest.approx(100 * segs[0]["P"]["T_pass"], abs=5e-4)
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
        _frames, header, _oc, segs = point("explore", theta_deg=30.0, sample=sample, pol="s")
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
    frames, header, oc, segs = point("explore", theta_deg=0.0, sample="bk7_air", pol="s")
    msgs = []
    out = headless.run_spec(V, "boundary", {"theta_deg": 0.0}, 1, {"frame_dt": 0.02}, {"world_s": 0.1}, None,
                            lambda m, b=None: msgs.append((m, b)), end_reason="test")
    chk = [m for m, _b in msgs if m["type"] == "check" and m["id"] == "det0"][-1]
    assert chk["ok"] is True
    d = pd.DEVICES["spcm_aqrh_14_650nm"]["detector"]
    n_in = segs[0]["P"]["T_pass"] * 2e5 * d.eta + d.dark_rate
    m_expected = float(pd.observed_rate(n_in, d.dead_time))
    m_seen = frames[-1]["meas"]["n_T"] / 0.1
    assert m_seen == pytest.approx(m_expected, rel=4 * math.sqrt(m_expected * 0.1) / (m_expected * 0.1))
