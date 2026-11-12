# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v05 optical bench: every preset runs and passes its checks; the closed-form checks (Brewster, total internal
reflection, antireflection, Bragg, Airy, tunnelling, Joule heating) pass; live changes apply at once; single photons
reproduce the computed R statistically; outcomes are revealed only on arrival."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.constants import C  # noqa: E402
from lfphys.core.optics import interfaces, thin_films  # noqa: E402
from lfphys.i18n import render  # noqa: E402
from lfviz import registry  # noqa: E402
from v05_optics_bench.engine.bench import rta  # noqa: E402

V = "v05_optics_bench"
PRESETS = list(registry.load(V)["schema"].presets)


def failed(h):
    """Checks shown as failed by the player (explicit ok, else |rel| within the tolerance; info: never)."""
    out = []
    for k, c in h.checks().items():
        if c.get("info"):
            continue
        ok = c.get("ok")
        if ok is None and c.get("ref") is not None and c.get("rel") is not None:
            ok = abs(c["rel"]) <= max(c.get("tol") or 1e-9, 1e-12)
        if ok is False:
            out.append((k, c["value"], c["ref"], c.get("note")))
    return out


def clicks(h, seg=None):
    """All revealed detections (time-ordered) with the message time they came with."""
    T, D, P, S, TE, TM = [], [], [], [], [], []
    for m, b in h.msgs:
        if m.get("type") == "clicks" and len(b["t"]):
            T.append(b["t"]); D.append(b["det"]); P.append(b["pol"]); S.append(b["seg"]); TE.append(b["te"])
            TM.append(np.full(len(b["t"]), m["t"]))
    if not T:
        return {k: np.zeros(0) for k in ("t", "det", "pol", "seg", "te", "tmsg")}
    out = {"t": np.concatenate(T), "det": np.concatenate(D), "pol": np.concatenate(P), "seg": np.concatenate(S),
           "te": np.concatenate(TE), "tmsg": np.concatenate(TM)}
    if seg is not None:
        m = out["seg"] == seg
        out = {k: v[m] for k, v in out.items()}
    return out


def counts(h, seg):
    """Exact counts (R, T, A) of a segment from the record (every clicks message carries them per segment)."""
    out = np.zeros(3, int)
    for m in h.of("clicks"):
        for row in m["by_seg"]:
            if row[0] == seg:
                out += np.array(row[1:])
    return out


def run_photons(h, n):
    h.run_to(h.sim.t + n / h.sim.params["rate"])


# --- every preset ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("preset", PRESETS)
def test_preset_runs_and_passes_its_checks(preset):
    h = Harness(V, preset)
    run_photons(h, 3000)
    assert not h.errors()
    assert not failed(h), failed(h)
    seg = h.of("segment")
    assert len(seg) == 1 and seg[0]["seg"] == 0
    b = [b for m, b in h.msgs if m.get("type") == "segment"][0]
    for k in ("th", "Rs", "Ts", "Rp", "Tp", "lam", "lRc", "lTc", "z", "E2"):
        assert np.all(np.isfinite(b[k])), k
    assert sum(m["n"] for m in h.of("clicks")) > 2000
    assert {"sum0", "stat0"} <= set(h.checks())
    mods = {d["id"] for d in h.of("header")[0]["engine"]}
    assert {"core.optics.interfaces", "core.optics.thin_films", "core.constants", "theories.approx.ray_optics"} <= mods


# --- closed-form checks ---------------------------------------------------------------------------------
def test_brewster_angle_and_only_s_photons_reflect():
    h = Harness(V, "brewster")
    ch = h.checks()
    assert ch["brew0"]["value"] == pytest.approx(math.degrees(math.atan2(1.5, 1.0)), rel=1e-12)
    assert ch["brewR0"]["ok"] and ch["brewR0"]["value"] < 1e-24
    for _ in range(100):  # small steps: every detection of a step is in the record individually
        run_photons(h, 200)
    c = clicks(h, 0)
    assert len(c["t"]) == counts(h, 0).sum()
    refl = c["det"] == 0
    assert refl.sum() > 500
    assert np.all(c["pol"][refl] == 0)  # p photons do not reflect near the Brewster angle (R_p ~ 1e-11 here)


def test_total_internal_reflection_and_evanescent_wave():
    h = Harness(V, "tir")
    ch = h.checks()
    assert ch["crit0"]["value"] == pytest.approx(math.degrees(math.asin(1 / 1.5)), rel=1e-12)
    assert ch["tir0"]["ok"] and ch["tirnow0"]["ok"]
    assert ch["evan0"]["value"] == pytest.approx(thin_films.evanescent_length(1.5, 1.0, 633.0, math.radians(60.0)),
                                                 rel=1e-9)
    run_photons(h, 5000)
    R, T, A = counts(h, 0)
    assert R > 4000 and T == 0 and A == 0  # every photon reflected


def test_quarter_wave_antireflection():
    h = Harness(V, "ar_mgf2")
    ch = h.checks()
    assert ch["ar0"]["ok"]
    assert ch["ar0"]["value"] == pytest.approx(((1.5 - 1.38 ** 2) / (1.5 + 1.38 ** 2)) ** 2, rel=1e-12)
    h2 = Harness(V, "ar_ideal")
    assert h2.checks()["ar0"]["ok"] and h2.checks()["ar0"]["value"] < 1e-30


def test_bragg_mirror_peak():
    h = Harness(V, "bragg")
    c = h.checks()["bragg0"]
    q = (2.3 / 1.45) ** 16
    ref = ((1.0 - 1.52 * q) / (1.0 + 1.52 * q)) ** 2  # (H L)^8 with H next to the incidence medium
    assert c["ref"] == pytest.approx(ref, rel=1e-14)
    assert c["value"] == pytest.approx(ref, rel=1e-10)
    assert not failed(h)


def test_fabry_perot_airy():
    h = Harness(V, "fp")
    ch = h.checks()
    assert abs(ch["airy0"]["rel"]) < 1e-10 and ch["airymax0"]["ok"] and ch["film0"]["ok"]
    # oblique incidence, both polarizations, asymmetric film: still the Airy formula
    h.set(theta_deg=30.0, pol="unpol", ns=1.33)
    assert not failed(h), failed(h)
    assert abs(h.checks()["airy1"]["rel"]) < 1e-10


def test_metal_film_joule_heating_and_absorbed_photons():
    h = Harness(V, "metal")
    ch = h.checks()
    assert ch["joule0"]["ok"] and ch["passive0"]["ok"] and ch["film0"]["ok"]
    run_photons(h, 20000)
    assert counts(h, 0)[2] > 1000  # absorbed photons exist
    seg = h.of("segment")[0]
    assert seg["expected"]["A"] > 0.05


def test_frustrated_tir_tunnelling():
    h = Harness(V, "ftir")
    ch = h.checks()
    T = interfaces.stack([1.5, 1.0, 1.5], [200.0], 633.0, math.radians(45.0), "s")["T"]
    assert ch["ftir0"]["value"] == pytest.approx(T, rel=1e-14)
    assert ch["ftir0"]["ref"] == pytest.approx(thin_films.ftir_T(1.5, 1.0, 200.0, 633.0, math.radians(45.0), "s"),
                                               rel=1e-14)
    assert abs(ch["ftir0"]["rel"]) < 1e-9
    run_photons(h, 10000)
    assert counts(h, 0)[1] > 2000  # photons tunnel through the gap


def test_refined_minimum_of_Rp_of_a_free_standing_film_is_its_brewster_angle():
    """Both faces of a film in air are at their Brewster angles at arctan(n): R_p = 0 there, found by the run."""
    h = Harness(V, "fp")
    m = h.of("segment")[0]["min_rp"]
    assert m["deg"] == pytest.approx(math.degrees(math.atan(2.3)), abs=1e-6) and m["Rp"] < 1e-15


def test_kretschmann_plasmon_dip_on_the_run_curve():
    h = Harness(V, "spr")
    seg = h.of("segment")[0]
    assert seg["min_rp"] is not None and abs(seg["min_rp"]["deg"] - 44.58) < 0.3
    assert seg["cur"]["p"]["R"] < 0.01 and seg["cur"]["p"]["A"] > 0.98
    assert not failed(h)


# --- live parameters ------------------------------------------------------------------------------------
def test_live_change_applies_at_once_and_starts_a_segment():
    h = Harness(V, "brewster")
    run_photons(h, 50)
    t0 = h.sim.t
    h.set(theta_deg=30.0)
    seg = h.of("segment")
    assert len(seg) == 2 and seg[1]["seg"] == 1 and seg[1]["t"] == t0
    assert seg[1]["setup"]["theta"] == 30.0 and seg[1]["angles"]["theta"] == pytest.approx(30.0)
    assert h.of("live")[-1]["values"]["theta_deg"] == 30.0
    assert {"sum1", "energy1", "brew1"} <= set(h.checks())
    assert "brewR1" in h.checks() and not failed(h)
    # the expectation of the new segment is that of 30 degrees
    rs = interfaces.fresnel(1.0, 1.5, math.radians(30.0), "s")[2]
    rp = interfaces.fresnel(1.0, 1.5, math.radians(30.0), "p")[2]
    assert seg[1]["expected"]["R"] == pytest.approx(0.5 * (rs + rp), rel=1e-12)
    # a structure swap: a new segment with the new layers
    h.set(structure="bragg")
    seg = h.of("segment")
    assert seg[-1]["seg"] == 2 and seg[-1]["setup"]["kind"] == "bragg" and len(seg[-1]["setup"]["layers"]) == 16
    assert "bragg2" in h.checks() and not failed(h)


def test_refused_change_leaves_the_world_as_it_was():
    h = Harness(V, "brewster")
    n_seg = len(h.of("segment"))
    h.set(theta_deg=95.0)
    assert h.errors() and len(h.of("segment")) == n_seg
    assert h.of("live")[-1]["values"]["theta_deg"] == 56.31


def test_grazing_angle_of_an_inner_layer_is_accepted():
    """At the gap's critical angle the wave grazes inside the gap; the engine's characteristic matrices are regular
    there, so the set-up is accepted and the run's numbers stay finite and conserve energy."""
    h = Harness(V, "ftir")
    th = math.degrees(math.asin(1.0 / 1.5))
    h.set(theta_deg=th)
    assert not h.errors() and h.sim.params["theta_deg"] == pytest.approx(th, rel=1e-15)
    for pol in ("s", "p"):
        v = rta(h.sim.st, h.sim.params["lam_nm"], math.radians(th), pol)
        assert math.isfinite(v["R"]) and v["R"] + v["T"] == pytest.approx(1.0, abs=1e-12)
    assert not failed(h), failed(h)


def test_path_change_loses_photons_in_flight_and_source_change_makes_them_transitional():
    h = Harness(V, "brewster")
    rate = h.sim.params["rate"]
    h.run_to(30.0 / rate)
    inflight = len(h.sim.flight)
    assert inflight > 0
    h.set(theta_deg=40.0)
    assert h.sim.tot["lost"] == inflight and len(h.sim.flight) == 0
    assert any(render(m["text"]) == f"the beam paths were rebuilt (media or angle): photons in flight lost: {inflight}"
               for m in h.of("notice"))
    h.run_to(h.sim.t + 30.0 / rate)
    assert len(h.sim.flight) > 0
    h.set(lam_nm=500.0)  # the source changes: photons under way fly on with their old wavelength
    h.run_to(h.sim.t + 3 * h.sim.times["t_in"])
    assert h.sim.tot["transitional"] > 0
    c = clicks(h)
    assert np.all(c["seg"][c["te"] < h.of("segment")[-1]["t"]] != h.sim.seg)  # not counted in the new segment
    assert counts(h, -1).sum() == h.sim.tot["transitional"]


def test_actions_emit_one_and_clear():
    h = Harness(V, "fp", {"rate": 1.0})
    e0 = h.sim.tot["emitted"]
    h.action("emit_one")
    assert h.sim.tot["emitted"] == e0 + 1
    h.cmd("next_event")
    h.cmd("next_event")
    h.cmd("next_event")
    assert sum(m["n"] for m in h.of("clicks")) >= 1
    h.action("clear")
    assert h.of("segment")[-1]["seg"] == 1


# --- photons: statistics and causality --------------------------------------------------------------------
@pytest.mark.parametrize("preset,params", [("brewster", {"theta_deg": 70.0, "pol": "s"}),
                                           ("metal", {}), ("ftir", {}), ("fp", {"theta_deg": 20.0, "pol": "unpol"})])
def test_photon_counts_agree_with_the_computed_probabilities(preset, params):
    h = Harness(V, preset, params, seed=7)
    run_photons(h, 40000)
    seg = h.of("segment")[0]
    p = seg["expected"]
    cnt = counts(h, 0)
    n = int(cnt.sum())
    assert n > 35000
    for j, k in enumerate(("R", "T", "A")):
        sig = math.sqrt(n * p[k] * (1 - p[k]))
        assert abs(cnt[j] - n * p[k]) <= 5 * sig + 1e-9, (k, cnt[j], n * p[k], sig)
    st = h.checks()["stat0"]
    assert st["ok"] and st["value"] > 5.7e-7  # the p-value of the counts (R, T, A) against the Born probabilities
    note = render(st["note"])
    assert f"R: {cnt[0]}" in note and f"T: {cnt[1]}" in note and f"A: {cnt[2]}" in note
    # the counters of the frame are the accumulation of the recorded clicks
    meta, _ = h.sim.frame()
    assert meta["counts"]["n"] == n and meta["counts"]["R"] == cnt[0]


def test_outcomes_are_revealed_only_on_arrival():
    h = Harness(V, "metal")  # n0 = 1 < n_s = 1.5: the transmission detector is reached later than the reflection one
    tin = h.sim.times["t_in"]
    dt = tin / 7
    for _ in range(80):
        h.run_to(h.sim.t + dt)
    c = clicks(h)
    assert len(c["t"])
    L = 0.30
    flight = {0: 2 * L * 1.0 / C, 1: L * (1.0 + 1.5) / C, 2: L * 1.0 / C}
    for j, f in flight.items():
        m = c["det"] == j
        assert np.allclose(c["t"][m] - c["te"][m], f, rtol=1e-12)
    assert np.all(c["t"] <= c["tmsg"]) and np.all(c["tmsg"] - c["t"] < dt * 1.0001)  # revealed in the step it happened


def test_frame_shows_both_packets_until_a_detector_decides():
    h = Harness(V, "metal", {"pol": "s", "rate": 5e10})
    tin, tR, tT = h.sim.times["t_in"], h.sim.times["t_R"], h.sim.times["t_T"]
    assert tT > tR
    h.run_to(tin + 0.5 * tR)  # the first photons are past the structure, no detector reached yet
    meta, b = h.sim.frame()
    fl = b["fl"].reshape(-1, 6)
    out = fl[fl[:, 0] == 1]
    assert len(out) > 0
    a = h.sim.flight.a
    R, T, _ = (h.of("segment")[0]["cur"]["s"][k] for k in ("R", "T", "A"))
    wR = R / (R + T)
    pending = out[(out[:, 2] < 1)]
    assert np.allclose(pending[:, 3], wR) and np.allclose(pending[:, 5], 1 - wR)  # the same for every outcome
    # between the two arrival times the silent reflection detector has removed the reflected packet
    h.run_to(h.sim.t + 0.5 * (tR + tT) - 0.5 * tR)
    meta, b = h.sim.frame()
    fl = b["fl"].reshape(-1, 6)
    late = fl[(fl[:, 0] == 1) & (fl[:, 2] >= 1)]
    assert len(late) and np.all(late[:, 3] == 0) and np.all(late[:, 5] == 1)
    assert np.all(a["out"][(a["stage"] == 1)] >= 0)


def test_engine_modules_and_header():
    h = Harness(V)
    head = h.of("header")[0]
    assert head["title"]["$t"] == "Optical bench: {structure}" and head["modifications"] == []
    assert {a["name"] for a in head["actions"]} == {"emit_one", "clear"}
    assert h.sim.engine_modules() == ["core.optics.interfaces", "core.optics.thin_films", "core.constants",
                                      "theories.approx.ray_optics"]


# --- review 2026-10-23 ------------------------------------------------------------------------------------------
THC = math.degrees(math.asin(1.0 / 1.5))  # glass 1.5 -> air


def test_exact_critical_angle_is_accepted_and_every_check_holds():
    """V5-1/V5-2: at theta_c as the float asin gives it (and a few ulp around it) the evanescent decay constant is 0 or
    lost in rounding: the change raised ZeroDivisionError inside `set` (world half-changed) or the `evan` check failed
    (18 of 39 values above theta_c). Now the change is accepted and the check is decided only where the numbers
    determine the decay length (its tolerance follows the condition number), else shown for information."""
    for th in [THC, float(f"{THC:.12g}")] + [THC + k * 1e-14 for k in range(-20, 41)]:
        h = Harness(V, "tir")
        h.set(theta_deg=th)
        assert not h.errors(), (th, h.errors())
        assert h.sim.params["theta_deg"] == th and h.sim.seg == 1
        assert not failed(h), (th, failed(h))
        if h.sim.st.n_in * math.sin(math.radians(th)) > 1.0 and "evan1" in h.checks():
            assert h.checks()["evan1"].get("info") or h.checks()["evan1"]["ok"]


@pytest.mark.parametrize("dth", [1e-7, 1e-9, 1e-12, 1e-5, 18.0])
def test_evanescent_check_tolerance_follows_the_condition_number(dth):
    """V5-2: theta_c + 1e-7 deg gave rel 2.8e-8 > 1e-8 (fail); the tolerance is now (4.5 K + 9 + 15/ln) u with
    K = n0^2 sin^2 / (n0^2 sin^2 - n_s^2) (README, derivation), and the reference is exact to one rounding."""
    h = Harness(V, "tir")
    h.set(theta_deg=THC + dth)
    c = h.checks()["evan1"]
    th = math.radians(THC + dth)
    q = 1.5 ** 2 * math.sin(th) ** 2 - 1.0
    K = 1.5 ** 2 * math.sin(th) ** 2 / q
    if 4.5 * K * 2.0 ** -53 > 1e-2:
        assert c.get("info")
        return
    assert c["ok"] is True and abs(c["rel"]) <= c["tol"]
    assert c["tol"] == pytest.approx((4.5 * K + 9) * 2.0 ** -53, rel=0.1, abs=10 * 2.0 ** -53)
    assert c["ref"] == pytest.approx(thin_films.evanescent_length(1.5, 1.0, 633.0, th), rel=1e-15)


@pytest.mark.parametrize("preset,params", [
    ("ftir", {"theta_deg": 41.8103149}), ("ftir", {"theta_deg": THC + 1e-9}), ("ftir", {"theta_deg": THC - 1e-9}),
    ("ftir", {"theta_deg": THC}),
    ("fp", {"n0": 4.0, "fp_n": 2.3, "fp_d_nm": 20000.0, "lam_nm": 300.0,
            "theta_deg": math.degrees(math.asin(2.3 / 4.0) - 1e-4)}),
    ("fp", {"n0": 4.0, "fp_n": 2.3, "fp_d_nm": 20000.0, "lam_nm": 300.0,
            "theta_deg": math.degrees(math.asin(2.3 / 4.0) + 1e-6)}),
])
def test_single_film_check_near_grazing(preset, params):
    """V5-2: 41.8103149 deg (theta_c + 4.2e-9 deg) gave film = 4.1e-12 > 1e-12; a 20 um film at n0 = 4 near grazing
    gave 2.4e-12 (the two routes rounded sin^2 differently: phase error ~ k u / cos theta1). Now both routes use the
    engine's cosines and the tolerance is the sum of their first-order rounding bounds; where that exceeds 1e-9 the
    routes are also compared at theta -/+ 1e-3 rad."""
    h = Harness(V, preset)
    h.set(**params)
    assert not h.errors()
    c = h.checks()["film1"]
    assert c["ok"] is True, c
    assert not failed(h), failed(h)


def test_joule_check_resolves_a_one_nanometre_skin_depth():
    """V5-3: n0 = 4, metal 0.2 + 20i, 500 nm, 300 nm, 70.24 deg: R + T + A_J - 1 = +2.9e-8 with 2001 Simpson points
    (tolerance 1e-8: failed); the quadrature now follows the skin depth (1.2 nm) and the standing-wave period."""
    h = Harness(V, "metal", {"n0": 4.0, "metal_n": 0.2, "metal_k": 20.0, "metal_d_nm": 500.0, "lam_nm": 300.0,
                             "theta_deg": 70.24})
    c = h.checks()["joule0"]
    assert c["ok"] is True and abs(c["value"] - 1.0) < 1e-13 and c["tol"] <= 1e-12
    h.set(theta_deg=0.0, n0=1.0)
    assert h.checks()["joule1"]["ok"] is True and abs(h.checks()["joule1"]["value"] - 1.0) < 1e-13


def test_a_change_that_fails_inside_leaves_the_world_as_it_was(monkeypatch):
    """V5-1: an exception after the new segment had been built (the reviewer's ZeroDivisionError in the checks) left
    the new parameters, structure and segment in place and escaped the runner (no rollback of the player's control).
    Now a live change is atomic: nothing of it is kept or emitted unless it succeeds as a whole, and any exception
    is reported as a refused change followed by the live values in force."""
    import v05_optics_bench.viz as vz
    h = Harness(V, "tir")
    run_photons(h, 200)
    before = dict(params=dict(h.sim.params), seg=h.sim.seg, tot=dict(h.sim.tot), segc=dict(h.sim.segc),
                  nflight=len(h.sim.flight), rng=h.sim.rng.bit_generator.state, nmsg=len(h.msgs))
    orig = vz.Simulation._segment_checks

    def failing(self, *a, **k):
        orig(self, *a, **k)
        raise ZeroDivisionError("injected after the new segment was built")

    monkeypatch.setattr(vz.Simulation, "_segment_checks", failing)
    h.set(theta_deg=70.0, rate=1e9)
    new = [(m, b) for m, b in h.msgs[before["nmsg"]:] if m["type"] != "command"]  # the record's log of the command
    assert [m["type"] for m, _ in new] == ["error", "live"], [m["type"] for m, _ in new]
    assert [m["type"] for m, _ in h.msgs[before["nmsg"]:]][0] == "command"  # logged with its time (a resume replays it)
    assert "ZeroDivisionError" in render(new[0][0]["text"])  # the framework's prefix: lfviz.errors.CONTEXTS["set"]
    assert new[1][0]["values"]["theta_deg"] == 60.0 and new[1][0]["values"]["rate"] == before["params"]["rate"]
    assert h.sim.params == before["params"] and h.sim.seg == before["seg"] and h.sim.tot == before["tot"]
    assert h.sim.segc == before["segc"] and len(h.sim.flight) == before["nflight"]
    assert h.sim.rng.bit_generator.state == before["rng"]
    h.cmd("new_world", preset="ftir")  # a world that fails while being built is refused, not a crash
    assert len(h.errors()) == 2 and len(h.of("header")) == 1 and h.sim.params == before["params"]
    monkeypatch.undo()
    h.set(theta_deg=70.0)  # the same change now goes through
    assert len(h.errors()) == 2 and h.sim.seg == before["seg"] + 1 and h.sim.params["theta_deg"] == 70.0
    assert "ZeroDivisionError" in render(h.errors()[-1])  # the world that failed to be built: why, in its text


def test_photon_statistics_check_covers_all_three_outcomes():
    """V5-4: only the reflected fraction was tested, so a swap of the T and A expectations passed; now every outcome
    is tested (exact binomial tail of each, Bonferroni over the outcomes, failure below the two-sided 5 sigma tail)."""
    h = Harness(V, "metal", seed=3)
    run_photons(h, 20000)
    assert h.checks()["stat0"]["ok"] is True
    c = h.sim.segc[0]
    assert c["T"] > 500 and c["A"] > 500 and abs(c["pT"] - c["pA"]) > 0.05
    c["pT"], c["pA"] = c["pA"], c["pT"]  # the expectation of T and A swapped
    h.sim._stat_check(0)
    assert h.checks()["stat0"]["ok"] is False
    c["pT"], c["pA"] = c["pA"], c["pT"]
    h.sim._stat_check(0)
    assert h.checks()["stat0"]["ok"] is True


def test_critical_angle_is_not_confused_with_an_opaque_structure():
    """Found while fuzzing the V5-2 fix: a thick film of lower index than n0 is evanescent beyond its grazing angle and
    its T underflows to exactly 0 long before the exit critical angle; the bisection on the structure's T then
    reported that angle (22-25 deg instead of arcsin(3/4) = 48.6 deg here) and the `crit` check failed. The critical
    angle is now found on the bare boundary n_in -> n_out (n sin theta is the same in every layer)."""
    h = Harness(V, "fp", {"n0": 4.0, "ns": 3.0, "fp_n": 1.5, "fp_d_nm": 20000.0, "lam_nm": 300.0, "theta_deg": 10.0})
    c = h.checks()["crit0"]
    assert c["value"] == pytest.approx(math.degrees(math.asin(0.75)), rel=1e-12)
    assert not failed(h), failed(h)


@pytest.mark.parametrize("ns,d,lam,dth", [(3.0, 20000.0, 300.0, -1e-7), (3.0, 20000.0, 300.0, -1e-12),
                                          (3.17, 2000.0, 894.8, -1e-14), (2.5, 121.6, 826.2, -5e-9),
                                          (3.0, 20000.0, 300.0, -1e-4)])
def test_airy_checks_just_below_grazing_in_the_film(ns, d, lam, dth):
    """Found while fuzzing the V5-2 fix: just below the angle at which the wave grazes inside a film of lower index
    than n0, F -> infinity and the Airy intensity formula (own asin / cos of the film angle) disagreed with the
    matrices by up to 0.1 (airy, airymax with tolerances 1e-10, 1e-9). Now the formula uses the engine's Snell
    cosines and the shared phase, and the tolerance is the sum of both routes' first-order rounding bounds; where it
    exceeds 1e-9 the routes are also compared 1e-3 rad further from grazing."""
    th = math.degrees(math.asin(2.3 / 4.0) + dth)
    h = Harness(V, "fp", {"n0": 4.0, "ns": ns, "fp_n": 2.3, "fp_d_nm": d, "lam_nm": lam, "theta_deg": th,
                          "pol": "unpol"})
    assert not failed(h), failed(h)
    ch = h.checks()
    assert ch["airy0"]["ok"] is True and ch["airymax0"]["ok"] is True, (ch["airy0"], ch["airymax0"])
