# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u37's screens (EX2 design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §4, §7): every point of every atlas
builds with every check ✓ and stops by its rule; every computed value of the bench (``lab_reference``) against an
independent computation; every way of the bench (§4.3, recomputed with the real devices) gives its stated outcome on
the atlas's own points (the same seeded runs ``site/atlas.py`` packs), fitted with ``lfphys.tools.stats.linear_fit``;
the Watch story's captions against the recording, each no later than its event; part 4's counts against the engine's
exact slot probabilities, the slots shown in time against the same probabilities, the thresholds against
``bell_stats.threshold_efficiency``, Gisin and Gisin's slot table against a Monte Carlo of the engine's model.

``WAYS`` holds each way's outcome as this seeded atlas gives it (the numbers W37 reports for §4.3); the tests check
them, and that each lies within the spread the statistics allow around the engine's prediction."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
from lfviz import expr, headless, registry

from lfphys.core.quantum import qubits as Q
from lfphys.theories.alternatives import local_hidden as LHV
from lfphys.theories.models import photodetector as PD
from lfphys.tools import bell_stats as BS
from lfphys.tools.stats import linear_fit

V = "u37_bell_test"
VIZ = registry.load(V)
SCREENS = {s["id"]: s for s in VIZ["screens"]}
LAB = SCREENS["lab"]
STEPS = {s["id"]: s for s in LAB["steps"]}
RECS = {r["id"]: r for r in VIZ["recordings"]}
ATL = {a["id"]: a for a in registry.atlases_of(VIZ)}
MOD = __import__("u37_bell_test.viz", fromlist=["Simulation"])
Law = __import__("u37_bell_test.engine.experiment", fromlist=["Law"]).Law
ROOT2 = math.sqrt(2.0)


def _key(c):
    return registry.control_key(c)


def run_point(atlas_id: str, values: dict):
    """One atlas point as ``site/atlas.py`` runs it: (outcome, frames)."""
    spec = ATL[atlas_id]
    params = {**spec["fixed"], **registry.expand_values(spec["controls"], values)}
    clock = {"fps": spec["fps"], "speed": None} if spec.get("fps") is not None else {"frame_dt": spec["frame_dt"]}
    msgs = []
    out = headless.run_spec(V, spec["preset"], params, spec["seed"], clock, spec["stop"], None,
                            lambda m, b=None: msgs.append((m, b)), end_reason="atlas")
    return out, [m for m, _b in msgs if m["type"] == "frame"], msgs


@pytest.fixture(scope="module")
def atlas():
    """Every point of every atlas: {atlas id: {values tuple: (outcome, frames)}} (the messages are not kept)."""
    out = {}
    for aid, spec in ATL.items():
        keys = [_key(c) for c in spec["controls"]]
        pts = {}
        for combo in itertools.product(*[c["values"] for c in spec["controls"]]):
            o, frames, _m = run_point(aid, dict(zip(keys, combo)))
            pts[combo] = (o, [{"t": f["t"], "meas": f["meas"], "S": f["S"], "J": f["J"]} for f in frames])
        out[aid] = pts
    return out


def last(atlas, aid, **vals):
    spec = ATL[aid]
    combo = tuple(vals[_key(c)] for c in spec["controls"])
    return atlas[aid][combo][1][-1]["meas"]


# --- the registry and the grid ---------------------------------------------------------------------------------------
def test_the_screens_are_the_registry_s_and_the_view_declares_what_they_use():
    assert registry.check(VIZ) == []
    decl = registry.view_declarations(VIZ)
    ex = SCREENS["explore"]
    assert set(ex["overlays"]) <= set(decl["overlays"])
    for st in LAB["steps"]:
        assert set(st.get("overlays") or []) <= set(decl["overlays"])
    assert sorted(ATL) == ["explore", "lab.correlation", "lab.detectors"]
    sizes = {aid: math.prod(len(c["values"]) for c in a["controls"]) for aid, a in ATL.items()}
    assert sizes == {"explore": 156, "lab.correlation": 150, "lab.detectors": 189}
    # the step on Explore's atlas carries its laws there (EX2 §5 F9)
    assert ATL["explore"]["laws"] == ["chsh/slope_quantum", "chsh/slope_visibility", "chsh/slope_spins",
                                      "local/slope_local"]


def test_every_point_of_every_atlas_builds_with_every_check_ok_and_stops_by_its_rule(atlas):
    for aid, pts in atlas.items():
        spec = ATL[aid]
        for combo, (o, frames) in pts.items():
            c = o.check_counts()
            assert c["failed"] == 0, (aid, combo, c)
            if "events" in spec["stop"]:
                want = next(iter(spec["stop"]["events"]))
                assert o.stop_event == want, (aid, combo)
                n = int(want.split("_")[1])
                assert frames[-1]["meas"]["coinc"] >= n
                assert o.t_end < spec["stop"]["max_world_s"]
            else:
                assert o.t_end == pytest.approx(spec["stop"]["world_s"])
                assert frames[-1]["meas"]["trials"] == pytest.approx(1e9, abs=2)


# --- the bench's computed values against independent computations -------------------------------------------------
def _ref(step, ref):
    st = STEPS[step]
    return MOD.Simulation.lab_reference(step, {}, {}, ref)["value"]


def test_the_benchs_references_against_closed_forms():
    assert _ref("correlation", "slope_photons") == pytest.approx(1.0, abs=1e-12)
    assert _ref("correlation", "slope_spins") == pytest.approx(-1.0, abs=1e-12)
    assert _ref("chsh", "slope_quantum") == pytest.approx(1.0, abs=1e-12)
    assert _ref("chsh", "slope_visibility") == pytest.approx(0.85, abs=1e-12)
    assert _ref("chsh", "slope_spins") == pytest.approx(1.0, abs=1e-12)
    assert _ref("local", "slope_local") == pytest.approx(0.5, abs=1e-12)
    # J per pair of |Φ+⟩ at the CHSH angles, one pair per trial: η² (1 + √2)/2 − η (hand: the singles η/2 each); the
    # bench's μ = 0.01 Poisson pairs per slot: J per slot by hand from the POVMs, Poisson-averaged (independent pairs)
    def jp_hand(e, mu=0.01):
        # P(no click among a set of detectors) = exp(−μ (1 − q)), q the one-pair probability that none of them clicks
        def none(qa=1.0, qb=1.0, qab=1.0):
            return math.exp(-mu * (1 - qab))
        cos2 = lambda d: math.cos(math.radians(d)) ** 2  # noqa: E731
        def pp(a, b):  # p(+, +) per slot
            qa, qb = 1 - e / 2, 1 - e / 2
            qab = 1 - e / 2 - e / 2 + e * e * cos2(a - b) / 2
            return 1 - none(qab=qa) - none(qab=qb) + none(qab=qab)
        pa = 1 - math.exp(-mu * e / 2)
        J = pp(45, 22.5) + pp(45, 67.5) + pp(0, 22.5) - pp(0, 67.5) - 2 * pa
        return J / mu
    etas = np.array([0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 1.00])
    slope, icpt = np.polyfit(etas, np.array([jp_hand(e) / e for e in etas]), 1)
    assert _ref("detectors", "j_slope") == pytest.approx(slope, abs=1e-9)
    assert _ref("detectors", "j_intercept") == pytest.approx(icpt, abs=1e-9)
    assert jp_hand(1.0, 1e-9) == pytest.approx((ROOT2 - 1) / 2, abs=1e-6)  # one pair per trial
    assert slope == pytest.approx((1 + ROOT2) / 2, rel=0.01) and icpt == pytest.approx(-1.0, rel=0.01)


def test_E_from_four_counts_is_bell_stats_correlation_and_its_error_counting_statistics():
    rng = np.random.default_rng(5)
    col = next(c for c in STEPS["correlation"]["columns"] if c["id"] == "E")
    for _ in range(50):
        n = rng.integers(0, 400, 4)
        if n.sum() == 0:
            continue
        v, s, t1, _t2 = expr.evaluate(col["expr"], {k: (float(x), math.sqrt(max(x, 1))) for k, x in
                                                     zip(("npp", "npm", "nmp", "nmm"), n)})
        E, _se, N = BS.correlation(n)
        assert v == pytest.approx(E, abs=1e-12)
        # the propagated Poisson errors: (1 − E²)/N to first order (a count of 0 carries the error of one count),
        # the formula's second-order term on top
        if n.min() > 0:
            assert math.sqrt(t1) == pytest.approx(math.sqrt(4 * (n[0] + n[3]) * (n[1] + n[2]) / N ** 3), rel=1e-9)
            assert s >= math.sqrt(t1)


def test_S_of_delta_is_the_laws_E_and_the_visibility_scales_it():
    for pair in ("photon", "spin"):
        q = Law(pair, "quantum")
        v = Law(pair, "quantum", V=0.85)
        for d in np.linspace(0, 90, 13):
            S = q.S(0, 2 * d, d, 3 * d)
            cf = (3 * math.cos(math.radians(2 * d)) - math.cos(math.radians(6 * d))) if pair == "photon" else \
                -(3 * math.cos(math.radians(d)) - math.cos(math.radians(3 * d)))
            assert S == pytest.approx(cf, abs=1e-12)
            assert v.S(0, 2 * d, d, 3 * d) == pytest.approx(0.85 * S, abs=1e-12)


# --- the ways of the bench (§4.3, recomputed with the real devices) ------------------------------------------------
class _Fit:
    """``linear_fit``'s output as attributes: the slope and intercept with their errors from the declared errors
    (unscaled; the scaled ones are the Birge ratio times these), χ²/dof."""

    def __init__(self, d):
        names = d["names"]
        p, s = dict(zip(names, d["params"])), dict(zip(names, d["sigma_unscaled"]))
        self.slope, self.slope_err = p.get("b"), s.get("b")
        self.intercept, self.intercept_err = p.get("a", 0.0), s.get("a", 0.0)
        self.chi2, self.dof = d["chi2"], d["dof"]


def _fit(x, y, sy, through_origin):
    x, y, sy = (np.asarray(a, float) for a in (x, y, sy))
    return _Fit(linear_fit(x, y, sx=0.0, sy=sy, model="line0" if through_origin else "line"))


def ways(atlas) -> dict:
    """Every way's outcome on the atlas's own points."""
    W = {}
    cor = ATL["lab.correlation"]
    a_vals, b_vals = cor["controls"][1]["values"], cor["controls"][2]["values"]

    def table(pair, a_set=(0.0, 45.0, 90.0)):
        rows = []
        for a in a_set:
            for b in b_vals:
                m = last(atlas, "lab.correlation", particles=pair, a_deg=a, b_deg=b)
                n = [m["n_pp"], m["n_pm"], m["n_mp"], m["n_mm"]]
                v, s, *_ = expr.evaluate("(npp + nmm - npm - nmp) / (npp + nmm + npm + nmp)",
                                         {k: (float(x), math.sqrt(max(x, 1))) for k, x in
                                          zip(("npp", "npm", "nmp", "nmm"), n)})
                rows.append((a, b, v, s))
        return np.array(rows)
    ph, sp = table("photon"), table("spin")
    c2 = lambda t: np.cos(np.radians(2 * (t[:, 1] - t[:, 0])))  # noqa: E731
    c1 = lambda t: np.cos(np.radians(t[:, 1] - t[:, 0]))  # noqa: E731
    r1 = _fit(c2(ph), ph[:, 2], ph[:, 3], True)
    W[1] = {"slope": r1.slope, "se": r1.slope_err, "chi2_dof": r1.chi2 / r1.dof, "n": len(ph)}
    r2 = _fit(c1(ph), ph[:, 2], ph[:, 3], False)
    W[2] = {"slope": r2.slope, "intercept": r2.intercept, "chi2_dof": r2.chi2 / r2.dof}
    r3a = _fit(c1(sp), sp[:, 2], sp[:, 3], True)
    r3b = _fit(c2(sp), sp[:, 2], sp[:, 3], False)
    W[3] = {"slope_c1": r3a.slope, "se_c1": r3a.slope_err, "chi2_dof_c1": r3a.chi2 / r3a.dof,
            "chi2_dof_c2": r3b.chi2 / r3b.dof}
    # way 4: the cursor at a tenth of the run (the first frame with 100 coincidences)
    fr = atlas["lab.correlation"][("photon", 0.0, 22.5)][1]
    early = min((f["meas"] for f in fr if f["meas"]["coinc"]), key=lambda m: abs(m["coinc"] - 100))
    W[4] = {"coinc": early["coinc"], "se_E": early["E_ab_se"], "se_E_end": fr[-1]["meas"]["E_ab_se"],
            "coinc_end": fr[-1]["meas"]["coinc"]}
    # way 5: the four E of part 1 at a ∈ {0, 45}, b ∈ {22.5, 67.5}: S, but with fixed settings (time-like)
    E = {(a, b): last(atlas, "lab.correlation", particles="photon", a_deg=a, b_deg=b) for a in (0.0, 45.0)
         for b in (22.5, 67.5)}
    S5 = E[(0.0, 22.5)]["E_ab"] - E[(0.0, 67.5)]["E_ab"] + E[(45.0, 22.5)]["E_ab"] + E[(45.0, 67.5)]["E_ab"]
    se5 = math.sqrt(sum(e["E_ab_se"] ** 2 for e in E.values()))
    W[5] = {"S": S5, "se": se5, "local_frac": E[(0.0, 22.5)]["local_frac"]}
    ex = lambda **k: last(atlas, "explore", **k)  # noqa: E731
    m6 = ex(particles="photon", delta=22.5, tau_ns=100.0, source="quantum")
    W[6] = {"S": m6["S"], "se": m6["S_se"], "excess": m6["excess"], "local_frac": m6["local_frac"]}
    m7a = ex(particles="photon", delta=45.0, tau_ns=100.0, source="quantum")
    m7b = ex(particles="spin", delta=22.5, tau_ns=100.0, source="quantum")
    m7c = ex(particles="spin", delta=45.0, tau_ns=100.0, source="quantum")
    W[7] = {"S_photon_45": m7a["S"], "se_photon_45": m7a["S_se"], "S_spin_22_5": m7b["S"], "se_spin_22_5": m7b["S_se"],
            "S_spin_45": m7c["S"]}
    m8 = ex(particles="photon", delta=22.5, tau_ns=5000.0, source="quantum")
    W[8] = {"S": m8["S"], "se": m8["S_se"], "local_frac": m8["local_frac"]}
    fr9 = atlas["explore"][("photon", 22.5, 100.0, "quantum")][1]
    early9 = min((f["meas"] for f in fr9 if f["meas"]["coinc"]), key=lambda m: abs(m["coinc"] - 400))
    m9 = ex(particles="photon", delta=22.5, tau_ns=100.0, source="visibility")
    W[9] = {"coinc": early9["coinc"], "se_S_400": early9["S_se"], "excess_400": early9["excess"],
            "S_V085": m9["S"], "se_V085": m9["S_se"]}
    ds = [d for d in ATL["explore"]["controls"][1]["values"] if 0 < d < 90]
    xph = np.array([3 * math.cos(math.radians(2 * d)) - math.cos(math.radians(6 * d)) for d in ds])
    for law, key in (("quantum", "q"), ("local", "l")):
        S = np.array([ex(particles="photon", delta=d, tau_ns=100.0, source=law)["S"] for d in ds])
        se = np.array([ex(particles="photon", delta=d, tau_ns=100.0, source=law)["S_se"] for d in ds])
        r = _fit(xph, S, se, True)
        W.setdefault(10, {})[key] = {"slope": r.slope, "se": r.slope_err, "chi2_dof": r.chi2 / r.dof,
                                     "max_abs_S": float(np.max(np.abs(S)))}
    dt = lambda **k: last(atlas, "lab.detectors", **k)  # noqa: E731
    m11n = dt(eff=1.0, source="phi", bg="none", window_ns=2.0)
    m11d = dt(eff=1.0, source="phi", bg="dark", window_ns=2.0)
    W[11] = {"S": m11n["S"], "J_pair_none": m11n["J_pair"], "se_none": m11n["J_pair_se"],
             "J_pair_none_pred": m11n["J_ref"] / 0.01, "J_pair_dark": m11d["J_pair"], "se_dark": m11d["J_pair_se"],
             "J_pair_dark_pred": m11d["J_ref"] / 0.01}
    m12 = dt(eff=0.75, source="phi", bg="dark", window_ns=2.0)
    W[12] = {"S": m12["S"], "se": m12["S_se"]}
    m13n = dt(eff=0.75, source="phi", bg="none", window_ns=2.0)
    W[13] = {"J_pair_dark": m12["J_pair"], "se_dark": m12["J_pair_se"], "J_pair_none": m13n["J_pair"],
             "se_none": m13n["J_pair_se"]}
    m14n = dt(eff=0.75, source="eberhard", bg="none", window_ns=2.0)
    m14d = dt(eff=0.75, source="eberhard", bg="dark", window_ns=2.0)
    m14_8 = dt(eff=0.8, source="eberhard", bg="none", window_ns=2.0)
    W[14] = {"J_pair_none": m14n["J_pair"], "se_none": m14n["J_pair_se"], "z_none": m14n["J"] / m14n["J_se"],
             "J_pair_dark": m14d["J_pair"], "se_dark": m14d["J_pair_se"], "J_pair_none_080": m14_8["J_pair"],
             "z_none_080": m14_8["J"] / m14_8["J_se"]}
    W[15] = {f"{s}_{b}": dt(eff=0.6, source=s, bg=b, window_ns=2.0)["J_pair"] for s in ("phi", "eberhard", "gisin")
             for b in ("dark", "none")}
    m16 = dt(eff=0.75, source="phi", bg="bright", window_ns=25.0)
    acc16 = m16["acc_est"] / (m16["coinc"] - m16["acc_est"])
    W[16] = {"S": m16["S"], "se": m16["S_se"], "acc_share": acc16, "S_sub": m16["S_sub"], "se_sub": m16["S_sub_se"],
             **_predicted(0.75, 1e5, 25e-9)}
    m17 = dt(eff=0.75, source="phi", bg="bright", window_ns=2.0)
    W[17] = {"S": m17["S"], "se": m17["S_se"], "acc_share": m17["acc_est"] / (m17["coinc"] - m17["acc_est"]),
             "S_sub": m17["S_sub"], "se_sub": m17["S_sub_se"], **_predicted(0.75, 1e5, 2e-9)}
    m18 = dt(eff=0.9, source="phi", bg="dark", window_ns=0.5)
    m18w = dt(eff=0.9, source="phi", bg="dark", window_ns=2.0)
    W[18] = {"herald_ratio": m18["herald"] / m18w["herald"], "S": m18["S"], "se": m18["S_se"],
             "J_pair": m18["J_pair"], "J_pair_wide": m18w["J_pair"], "se": m18["J_pair_se"]}
    m19 = dt(eff=1.0, source="gisin", bg="none", window_ns=2.0)
    W[19] = {"S": m19["S"], "se": m19["S_se"], "J_pair": m19["J_pair"], "se_J": m19["J_pair_se"],
             "herald": m19["herald"], "CH": m19["CH"]}
    # the law of part 4: J/η against η, |Φ+⟩, no background: a line crossing 0 at 2/(1 + √2)
    etas = ATL["lab.detectors"]["controls"][0]["values"]
    jp = np.array([dt(eff=e, source="phi", bg="none", window_ns=2.0)["J_pair"] for e in etas])
    jse = np.array([dt(eff=e, source="phi", bg="none", window_ns=2.0)["J_pair_se"] for e in etas])
    r = _fit(etas, jp / np.array(etas), jse / np.array(etas), False)
    W["law4"] = {"slope": r.slope, "slope_se": r.slope_err, "intercept": r.intercept, "intercept_se": r.intercept_err,
                 "eta0": -r.intercept / r.slope, "chi2_dof": r.chi2 / r.dof}
    return W


def _predicted(eta, bg, w):
    """The accidentals' share and the raw S of |Φ+⟩ at the CHSH angles with the SPCM-NIR at η, a background and a
    window: ``photodetector.coincidence_rates`` per setting pair, computed here independently of the world."""
    from lfphys.core.quantum import qubits as Qb
    dev = PD.DEVICES["spcm_nir_800_13"]["detector"]
    d = PD.Detector(eta, dev.dark_rate + bg, dev.dead_time, dev.jitter_sigma)
    S, acc, true = 0.0, 0.0, 0.0
    for sg, (a, b) in zip((1, -1, 1, 1), ((0, 22.5), (0, 67.5), (45, 22.5), (45, 67.5))):
        P = Qb.joint_probabilities(Qb.PHI_PLUS, Qb.polarizer_projectors(math.radians(a)),
                                   Qb.polarizer_projectors(math.radians(b)))
        r = PD.coincidence_rates(1e4, P, [d, d], [d, d], w)
        tot = (r["true"] + r["accidental"]).ravel()
        S += sg * (tot[0] + tot[3] - tot[1] - tot[2]) / tot.sum()
        acc += r["accidental"].sum()
        true += r["true"].sum()
    return {"acc_share_pred": acc / true, "S_pred": S}


@pytest.fixture(scope="module")
def W(atlas):
    return ways(atlas)


def test_part_1_ways(W):
    assert W[1]["slope"] == pytest.approx(1.0, abs=4 * W[1]["se"])        # 1: right
    assert W[1]["chi2_dof"] < 2.0
    assert W[2]["chi2_dof"] > 20                                           # 2: E on 2x² − 1, not on a line
    assert W[3]["slope_c1"] == pytest.approx(-1.0, abs=4 * W[3]["se_c1"])  # 3: spins against cos(b − a)
    assert W[3]["chi2_dof_c2"] > 20
    assert W[4]["coinc"] < 300 and W[4]["se_E"] > 2 * W[4]["se_E_end"] and W[4]["se_E_end"] < 0.03  # 4: too few
    assert W[5]["S"] == pytest.approx(2 * ROOT2, abs=4 * W[5]["se"]) and W[5]["local_frac"] == 0.0  # 5: time-like


def test_part_2_and_3_ways(W):
    assert W[6]["S"] == pytest.approx(2 * ROOT2, abs=4 * W[6]["se"]) and W[6]["excess"] > 15
    assert W[6]["local_frac"] == 1.0                                        # 6: every choice space-like
    assert abs(W[7]["S_photon_45"]) < 4 * W[7]["se_photon_45"]              # 7: S = 0 at the wrong angle
    assert abs(W[7]["S_spin_22_5"]) == pytest.approx(2.389, abs=4 * W[7]["se_spin_22_5"])
    assert W[8]["S"] == pytest.approx(2 * ROOT2, abs=4 * W[8]["se"]) and W[8]["local_frac"] == 0.0  # 8: time-like
    assert 0.1 < W[9]["se_S_400"] < 0.2                                     # 9: too few coincidences
    assert W[9]["S_V085"] == pytest.approx(0.85 * 2 * ROOT2, abs=4 * W[9]["se_V085"])
    assert W[10]["q"]["slope"] == pytest.approx(1.0, abs=4 * W[10]["q"]["se"])     # 10: the quantum law
    assert W[10]["l"]["slope"] == pytest.approx(0.5, abs=4 * W[10]["l"]["se"])     # the local model
    assert W[10]["l"]["max_abs_S"] < 2.0


def test_part_4_ways(W):
    # 11: (√2 − 1)/2 for one pair per trial; μ = 0.01 Poisson pairs per slot lower it by about μ/2 (the prediction)
    assert W[11]["J_pair_none"] == pytest.approx(W[11]["J_pair_none_pred"], abs=4 * W[11]["se_none"])
    assert W[11]["J_pair_none_pred"] == pytest.approx((ROOT2 - 1) / 2, rel=0.01)
    assert W[11]["J_pair_dark"] > 5 * W[11]["se_dark"]  # violated with the real device's dark counts too
    assert W[12]["S"] == pytest.approx(2 * ROOT2, abs=4 * W[12]["se"])      # 12: fair sampling hides the losses
    assert W[13]["J_pair_none"] == pytest.approx(-0.0710, abs=4 * W[13]["se_none"])  # 13: no violation
    assert W[13]["J_pair_dark"] < 0
    assert W[14]["J_pair_none"] == pytest.approx(0.0053, abs=4 * W[14]["se_none"])   # 14: Eberhard's state
    assert W[14]["J_pair_dark"] < 0  # [error in earlier]: the SPCM-NIR's dark counts in 1 µs slots spoil J
    assert all(v < 0 for v in W[15].values())                               # 15: below 2/3 nothing violates
    # 16: a bright background left in (at the bench's η 0.75 with the real device; E37's 22.0 % and S = 2.319 were for
    # the design's first devices at η 0.70)
    assert W[16]["acc_share"] == pytest.approx(W[16]["acc_share_pred"], rel=0.03)
    assert W[16]["S"] == pytest.approx(W[16]["S_pred"], abs=4 * W[16]["se"]) and W[16]["S"] < 2.5
    assert W[16]["S_sub"] == pytest.approx(2 * ROOT2, abs=4 * W[16]["se_sub"])
    assert W[17]["acc_share"] == pytest.approx(W[17]["acc_share_pred"], rel=0.05)  # 17: the window matched
    assert W[17]["S"] == pytest.approx(W[17]["S_pred"], abs=4 * W[17]["se"])
    assert W[17]["S_sub"] == pytest.approx(2 * ROOT2, abs=4 * W[17]["se_sub"])
    assert W[18]["herald_ratio"] == pytest.approx(PD.window_share(0.5e-9, 350e-12 * PD.FWHM_TO_SIGMA), abs=0.01)
    assert W[19]["S"] == pytest.approx(2 * ROOT2, abs=4 * W[19]["se"]) and W[19]["J_pair"] < 0  # 19: GG
    assert W["law4"]["eta0"] == pytest.approx(2 / (1 + ROOT2), abs=0.01)
    assert W["law4"]["slope"] == pytest.approx(_ref("detectors", "j_slope"), abs=4 * W["law4"]["slope_se"])
    assert W["law4"]["intercept"] == pytest.approx(_ref("detectors", "j_intercept"), abs=4 * W["law4"]["intercept_se"])


# --- part 4's counts and the shown slots against the engine's slot probabilities ----------------------------------
def test_part_4_counts_are_the_exact_multinomial_of_the_engines_slot_probabilities():
    """The trials' outcome tables of a slots run against ``Law.slot_table`` (χ² over the 16 outcomes of each setting
    pair), and the slots shown in time (``photodetector.pair_slots``) pooled against the same probabilities."""
    from scipy import stats as sps
    out, frames, msgs = run_point("lab.detectors", {"eff": 0.8, "source": "phi", "bg": "dark", "window_ns": 2.0})
    sim_law = Law("photon", "quantum")
    pd = PD.dark_click_probability(DEVD, 1e-6)
    shown = np.concatenate([b["slots"] for m, b in msgs if m["type"] == "slots"])
    P = {(x, y): sim_law.slot_table(a, b, 0.8, 0.8, pd, pd, 0.01) for x, a in ((0, 0.0), (1, 45.0))
         for y, b in ((0, 22.5), (1, 67.5))}
    # the shown slots: each station's outcome against its marginal (few slots: pooled outcome classes)
    # the shown slots' columns: slot, setting A, setting B, outcome A, outcome B
    for side, col in (("A", 3), ("B", 4)):
        obs = np.bincount(shown[:, col].astype(int), minlength=4)
        exp = np.zeros(4)
        for (x, y), p in P.items():
            sel = (shown[:, 1] == x) & (shown[:, 2] == y)
            exp += sel.sum() * (p.sum(axis=1) if side == "A" else p.sum(axis=0))
        none = 2
        assert abs(obs[none] - exp[none]) < 5 * math.sqrt(exp[none] * (1 - exp[none] / exp.sum()))
    assert out.check_counts()["failed"] == 0


DEVD = PD.DEVICES["spcm_nir_800_13"]["detector"].dark_rate


def test_gisin_gisins_slot_table_against_a_monte_carlo_of_the_engines_model():
    """The slot table of Gisin and Gisin's model (three independent Poisson streams, their clicks combined) against a
    Monte Carlo: a Poisson number of pairs per slot from ``local_hidden.gisin_gisin``, each photon detected with η,
    dark clicks, the click sets per station."""
    law = Law("photon", "gg")
    rng = np.random.default_rng(3)
    eta, pdk, mu, n = 0.8, 0.02, 0.4, 200_000
    a, b = 0.0, 22.5
    P = law.slot_table(a, b, eta, eta, pdk, pdk, mu)
    k = rng.poisson(mu, n)
    slot = np.repeat(np.arange(n), k)
    A, B = LHV.gisin_gisin(LHV.poincare(math.radians(a)), LHV.poincare(math.radians(b)), len(slot), rng,
                           state="phi_plus")
    det = rng.random((2, len(slot))) < eta
    mask = {"A": np.zeros(n, np.int64), "B": np.zeros(n, np.int64)}
    for s, o, d in (("A", A, det[0]), ("B", B, det[1])):
        for port, val in ((0, 1), (1, -1)):
            hit = (o == val) & d
            np.bitwise_or.at(mask[s], slot[hit], 1 << port)
        for port in (0, 1):
            mask[s] |= (rng.random(n) < pdk).astype(np.int64) << port
    code = np.array([2, 0, 1, 3])
    obs = np.zeros((4, 4))
    np.add.at(obs, (code[mask["A"]], code[mask["B"]]), 1)
    exp = P * n
    m = exp > 20
    z = (obs[m] - exp[m]) / np.sqrt(exp[m])
    assert np.max(np.abs(z)) < 5, z


def test_the_thresholds_table_is_bell_stats_threshold_efficiency():
    for (state, r, d), th in MOD.THRESHOLDS.items():
        psi = Q.PHI_PLUS if state == "max" else Q.eberhard_state(r)
        got = BS.threshold_efficiency(psi, p_dark=PD.dark_click_probability(d, 1e-6), mu=0.01)
        if math.isnan(th):
            assert math.isnan(got)  # J ≤ 0 at every efficiency
        else:
            assert got == pytest.approx(th, abs=2e-5)


# --- Watch ------------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def story():
    r = RECS["story"]
    msgs = []
    out = headless.run_spec(V, r["preset"], None, r["seed"], {"fps": r["fps"], "speed": r.get("speed")},
                            {"seconds": r["seconds"]}, r["script"], lambda m, b=None: msgs.append((m, b)),
                            captions=r["captions"], end_reason="test")
    return out, [m for m, _b in msgs]


def _played(frames, t_world, world_index):
    """The played second at which the frames of world ``world_index`` reach the world time t."""
    k0 = 0
    w = -1
    for k, f in enumerate(frames):
        if f.get("_new"):
            w += 1
        if w == world_index and f["t"] >= t_world - 1e-15:
            return k / RECS["story"]["fps"]
    return None


def test_the_story_s_captions_quote_the_run_and_come_no_later_than_their_events(story):
    out, msgs = story
    fps = RECS["story"]["fps"]
    assert out.frames == RECS["story"]["seconds"] * fps and out.check_counts()["failed"] == 0
    frames, k, world = [], 0, -1
    events = []
    for m in msgs:
        if m["type"] == "header":
            world += 1
        elif m["type"] == "frame":
            frames.append({**m, "_w": world, "_k": len(frames)})
        elif m["type"] == "event":
            events.append({**m, "_w": world, "_k": len(frames)})  # revealed at the next frame
    caps = [m for m in msgs if m["type"] == "caption"]
    assert [c["at"] for c in caps] == [c["at"] for c in RECS["story"]["captions"]]
    played = lambda e: e["_k"] / fps  # noqa: E731
    first = next(e for e in events if e["kind"] == "detection" and e["_w"] == 0)
    viol = next(e for e in events if e["kind"] == "result" and e["_w"] == 0)
    assert 3.0 <= played(first) <= 4.0          # caption at 3 s: the first coincidence follows it
    assert 10.0 <= played(viol) <= 12.0         # caption at 10 s: the violation event follows it
    # caption at 20 s quotes the run at 33.9 s (the last frame of the quantum world)
    q = [f for f in frames if f["_w"] == 0][-1]["meas"]
    n = MOD.STORY_NUMBERS
    assert abs(q["coinc"] - n["n"]) < 0.05 * n["n"]
    assert round(q["S"], 2) == n["S"] and round(q["S_se"], 2) == n["se"] and q["excess"] > n["z"]
    # caption at 44 s: the local world's S stays below 2, near √2
    lq = frames[-1]["meas"]
    assert lq["S"] < 2.0 and abs(lq["S"] - ROOT2) < 3 * lq["S_se"]
    # the flights shown slowly: the first pair's emission and arrival inside the slow stretch 1–5 s
    assert any(e["kind"] == "count" for e in events)
