# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u35 optical bench: every preset runs and passes its checks; the closed-form checks (Brewster, total internal
reflection, antireflection, Bragg, Airy, tunnelling, Joule heating) pass; live changes apply at once; single photons
reproduce the computed probabilities statistically; outcomes are revealed only on arrival. Where a test needs the
numbers of a given index (the review history of 2026-10-23), its set-up is a model medium with the ideal detector
(``OLD``): the closed forms are those of the indices, and every arrival is a click."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.optics import interfaces, materials, polarization as pol_, thin_films  # noqa: E402
from lfphys.i18n import render  # noqa: E402
from lfviz import registry  # noqa: E402
from u35_optics_bench.engine.bench import rta  # noqa: E402

V = "u35_optics_bench"
PRESETS = list(registry.load(V)["schema"].presets)
_M = {"med_in": "model", "med_out": "model", "det": "ideal", "lam_nm": 633.0, "dlam_nm": 0.0, "rate": 4e9}
#: the set-ups of the first version (constant indices), as model media with the ideal detector
OLD = {
    "brewster": {**_M, "n0": 1.0, "ns": 1.5, "theta_deg": 56.31},
    "tir": {**_M, "n0": 1.5, "ns": 1.0, "theta_deg": 60.0},
    "ftir": {**_M, "n0": 1.5, "ns": 1.0, "theta_deg": 45.0},
    "ar_mgf2": {**_M, "n0": 1.0, "ns": 1.5, "ar_mat": "model", "ar_n": 1.38, "lam_nm": 550.0},
    "bragg": {**_M, "n0": 1.0, "ns": 1.52, "bragg_mat": "model", "nH": 2.3, "nL": 1.45, "lam_nm": 550.0},
    "fp": {**_M, "n0": 1.0, "ns": 1.0},
    "metal": {**_M, "n0": 1.0, "ns": 1.5, "metal_mat": "model", "metal_n": 0.2, "metal_k": 3.3},
    "spr": {**_M, "n0": 1.5, "ns": 1.0, "metal_mat": "model", "metal_n": 0.2, "metal_k": 3.3, "theta_deg": 44.58},
}


def old(preset, **kw):
    """A world of the first version's set-up (``OLD``)."""
    return Harness(V, preset, {**OLD[preset], **kw.pop("params", {})}, **kw)


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


def clicks(h):
    """All revealed events of the clicks messages (time-ordered per step): t (the tag), det (0 reflection pass, 1
    reflection reject, 2 transmission pass, 3 transmission reject, 4 absorbed at the structure), pol (the photon's code,
    9 a dark count), tmsg (the message's time)."""
    T, D, P, TM = [], [], [], []
    for m, b in h.msgs:
        if m.get("type") == "clicks" and len(b["t"]):
            T.append(b["t"]); D.append(b["det"]); P.append(b["pol"]); TM.append(np.full(len(b["t"]), m["t"]))
    if not T:
        return {k: np.zeros(0) for k in ("t", "det", "pol", "tmsg")}
    return {"t": np.concatenate(T), "det": np.concatenate(D), "pol": np.concatenate(P), "tmsg": np.concatenate(TM)}


def counts(h, seg):
    """Exact counts of a segment from the record (every clicks message carries them per segment): (reflected, i.e.
    both reflection ports; transmitted, both transmission ports; absorbed)."""
    out = np.zeros(5, int)
    for m in h.of("clicks"):
        for row in m["by_seg"]:
            if row[0] == seg:
                out += np.array(row[1:])
    return np.array([out[0] + out[1], out[2] + out[3], out[4]])


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
    if h.sim.params["shutter"] == "open":
        assert sum(m["n"] for m in h.of("clicks")) > 1000 or seg[0]["P"]["A"] > 0.5
    assert {"sum0", "born0", "arms0"} <= set(h.checks())
    mods = {d["id"] for d in h.of("header")[0]["engine"]}
    assert {"core.optics.interfaces", "core.optics.thin_films", "core.optics.polarization", "core.optics.materials",
            "theories.models.photodetector", "theories.approx.ray_optics"} <= mods


# --- closed-form checks ---------------------------------------------------------------------------------
def test_brewster_angle_and_only_s_light_reflects():
    h = old("brewster", params={"pol": "unpol"})
    ch = h.checks()
    assert ch["brew0"]["value"] == pytest.approx(math.degrees(math.atan2(1.5, 1.0)), rel=1e-12)
    assert ch["brewR0"]["ok"] and ch["brewR0"]["value"] < 1e-24
    assert ch["dop0"]["ok"] and ch["dop0"]["value"] > 1 - 1e-9  # the reflected light is s: fully polarised
    # at the run's own Brewster angle an analyser along p passes no reflected photon, along s every one
    thB = ch["brew0"]["value"]
    h.set(theta_deg=thB, anaR="ideal", anaR_deg=0.0)
    run_photons(h, 20000)
    c = h.sim.segc[1]
    assert c["fate"][0] == 0 and c["fate"][1] > 1000  # R_pass (along p) never, R_reject (s) always
    assert h.checks()["malusR1"]["ok"] and h.checks()["malusR1"]["value"] < 1e-20


def test_brewster_of_n_bk7_from_its_dataset():
    """The glass is N-BK7 from SCHOTT's Sellmeier formula (lfphys materials): its Brewster angle at 632.8 nm."""
    h = Harness(V, "brewster")
    n = materials.index("schott_n_bk7", 632.8).real
    assert h.of("segment")[0]["setup"]["n_out"] == n
    assert h.checks()["brew0"]["value"] == pytest.approx(math.degrees(math.atan(n)), rel=1e-12)
    assert h.checks()["brew0"]["value"] == pytest.approx(56.574, abs=5e-4)


def test_total_internal_reflection_and_evanescent_wave():
    h = old("tir")
    ch = h.checks()
    assert ch["crit0"]["value"] == pytest.approx(math.degrees(math.asin(1 / 1.5)), rel=1e-12)
    assert ch["tir0"]["ok"] and ch["tirnow0"]["ok"]
    assert ch["evan0"]["value"] == pytest.approx(thin_films.evanescent_length(1.5, 1.0, 633.0, math.radians(60.0)),
                                                 rel=1e-9)
    # the phase of total reflection: δ = arg r_s − arg r_p against Stratton's closed form
    assert ch["tirphase0"]["ok"]
    assert ch["tirphase0"]["ref"] == pytest.approx(math.degrees(pol_.tir_phase_closed_form(1 / 1.5, math.radians(60))),
                                                   rel=1e-14)
    run_photons(h, 5000)
    R, Tr, A = counts(h, 0)
    assert R > 4000 and Tr == 0 and A == 0  # every photon reflected


def test_quarter_wave_antireflection():
    h = old("ar_mgf2")
    ch = h.checks()
    assert ch["ar0"]["ok"]
    assert ch["ar0"]["value"] == pytest.approx(((1.5 - 1.38 ** 2) / (1.5 + 1.38 ** 2)) ** 2, rel=1e-12)
    h2 = old("ar_mgf2", params={"ar_n": math.sqrt(1.5)})
    assert h2.checks()["ar0"]["ok"] and h2.checks()["ar0"]["value"] < 1e-30
    # the real materials: a crystal of MgF2 (lossless) is checked, the film (κ > 0) shown for information
    h3 = Harness(V, "ar_mgf2_bulk")
    assert h3.checks()["ar0"]["ok"]
    h4 = Harness(V, "ar_mgf2")
    assert h4.checks()["ar0"].get("info") and not failed(h4)


def test_bragg_mirror_peak():
    h = old("bragg")
    c = h.checks()["bragg0"]
    q = (2.3 / 1.45) ** 16
    ref = ((1.0 - 1.52 * q) / (1.0 + 1.52 * q)) ** 2  # (H L)^8 with H next to the incidence medium
    assert c["ref"] == pytest.approx(ref, rel=1e-14)
    assert c["value"] == pytest.approx(ref, rel=1e-10)
    assert not failed(h)
    # the real films (Gao et al.) on N-BK7: the design's 99.37 % at 550 nm
    h2 = Harness(V, "bragg")
    assert h2.checks()["bragg0"]["value"] == pytest.approx(0.99368, abs=5e-5) and not failed(h2)


def test_fabry_perot_airy():
    h = old("fp")
    ch = h.checks()
    assert abs(ch["airy0"]["rel"]) < 1e-10 and ch["airymax0"]["ok"] and ch["film0"]["ok"]
    # oblique incidence, both polarizations, asymmetric film: still the Airy formula
    h.set(theta_deg=30.0, pol="unpol", ns=1.33)
    assert not failed(h), failed(h)
    assert abs(h.checks()["airy1"]["rel"]) < 1e-10


def test_metal_film_joule_heating_and_absorbed_photons():
    h = old("metal")
    ch = h.checks()
    assert ch["joule0"]["ok"] and ch["joulep0"]["ok"] and ch["passive0"]["ok"] and ch["film0"]["ok"]
    run_photons(h, 20000)
    assert counts(h, 0)[2] > 1000  # absorbed photons exist
    seg = h.of("segment")[0]
    assert seg["expected"]["A"] > 0.05


def test_frustrated_tir_tunnelling():
    h = old("ftir", params={"pol": "s"})
    ch = h.checks()
    T_ = interfaces.stack([1.5, 1.0, 1.5], [200.0], 633.0, math.radians(45.0), "s")["T"]
    assert ch["ftir0"]["value"] == pytest.approx(T_, rel=1e-14)
    assert ch["ftir0"]["ref"] == pytest.approx(thin_films.ftir_T(1.5, 1.0, 200.0, 633.0, math.radians(45.0), "s"),
                                               rel=1e-14)
    assert abs(ch["ftir0"]["rel"]) < 1e-9
    run_photons(h, 10000)
    assert counts(h, 0)[1] > 2000  # photons tunnel through the gap


def test_refined_minimum_of_Rp_of_a_free_standing_film_is_its_brewster_angle():
    """Both faces of a film in air are at their Brewster angles at arctan(n): R_p = 0 there, found by the run."""
    h = old("fp")
    m = h.of("segment")[0]["min_rp"]
    assert m["deg"] == pytest.approx(math.degrees(math.atan(2.3)), abs=1e-6) and m["Rp"] < 1e-15


def test_kretschmann_plasmon_dip_on_the_run_curve():
    h = old("spr")
    seg = h.of("segment")[0]
    assert seg["min_rp"] is not None and abs(seg["min_rp"]["deg"] - 44.58) < 0.3
    assert seg["cur"]["p"]["R"] < 0.01 and seg["cur"]["p"]["A"] > 0.98
    assert not failed(h)
    # the real gold of Johnson and Christy (PCHIP), 50 nm on N-BK7: R_p smallest, 0.0038, at 43.773° (E35 part 2)
    h2 = Harness(V, "spr")
    m = h2.of("segment")[0]["min_rp"]
    assert m["deg"] == pytest.approx(43.773, abs=2e-3) and m["Rp"] == pytest.approx(0.0038, abs=2e-4)


# --- live parameters ------------------------------------------------------------------------------------
def test_live_change_applies_at_once_and_starts_a_segment():
    h = old("brewster", params={"pol": "unpol"})
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
    assert seg[1]["expected"]["R_pass"] == pytest.approx(0.5 * (rs + rp), rel=1e-12)
    # a structure swap: a new segment with the new layers
    h.set(structure="bragg", bragg_mat="model")
    seg = h.of("segment")
    assert seg[-1]["seg"] == 2 and seg[-1]["setup"]["kind"] == "bragg" and len(seg[-1]["setup"]["layers"]) == 16
    assert "bragg2" in h.checks() and not failed(h)


def test_refused_change_leaves_the_world_as_it_was():
    h = Harness(V, "brewster")
    n_seg = len(h.of("segment"))
    h.set(theta_deg=95.0)
    assert h.errors() and len(h.of("segment")) == n_seg
    assert h.of("live")[-1]["values"]["theta_deg"] == 56.574
    h.set(lam_nm=320.0, med_out="schott_n_f2")  # N-F2 has data from 365 nm: a coded refusal of the world
    assert len(h.errors()) == 2 and len(h.of("segment")) == n_seg and h.sim.params["med_out"] == "schott_n_bk7"


def test_grazing_angle_of_an_inner_layer_is_accepted():
    """At the gap's critical angle the wave grazes inside the gap; the engine's characteristic matrices are regular
    there, so the set-up is accepted and the run's numbers stay finite and conserve energy."""
    h = old("ftir")
    th = math.degrees(math.asin(1.0 / 1.5))
    h.set(theta_deg=th)
    assert not h.errors() and h.sim.params["theta_deg"] == pytest.approx(th, rel=1e-15)
    for pol in ("s", "p"):
        v = rta(h.sim.st, h.sim.params["lam_nm"], math.radians(th), pol)
        assert math.isfinite(v["R"]) and v["R"] + v["T"] == pytest.approx(1.0, abs=1e-12)
    assert not failed(h), failed(h)


def test_path_change_loses_photons_in_flight_and_source_change_makes_them_transitional():
    h = old("brewster", params={"rate": 4e9})
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
    assert counts(h, -1).sum() == h.sim.tot["transitional"]  # counted apart, not in the new segment


def test_actions_emit_one_and_clear():
    h = old("fp", params={"rate": 1.0})
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
    h = old(preset, params=params, seed=7)
    run_photons(h, 40000)
    seg = h.of("segment")[0]
    p = seg["arms"]
    cnt = counts(h, 0)
    n = int(cnt.sum())
    assert n > 35000
    for j, k in enumerate(("R", "T", "A")):
        sig = math.sqrt(n * p[k] * (1 - p[k]))
        assert abs(cnt[j] - n * p[k]) <= 5 * sig + 1e-9, (k, cnt[j], n * p[k], sig)
    st = h.checks()["stat0"]
    assert st["ok"] and st["value"] > 5.7e-7  # the p-value of the outcomes against the Born probabilities
    # the counters of the frame are the accumulation of the recorded clicks (an ideal detector: every arrival)
    meta, _ = h.sim.frame()
    assert meta["counts"]["n"] == int(cnt[0] + cnt[1]) and meta["counts"]["Rp"] == cnt[0]
    assert meta["meas"]["n_R"] == cnt[0] and meta["meas"]["n_T"] == cnt[1] and meta["meas"]["n_A"] == cnt[2]


def test_outcomes_are_revealed_only_on_arrival():
    h = old("metal")  # n0 = 1 < n_s = 1.5: the transmission detector is reached later than the reflection one
    tin = h.sim.times["t_in"]
    dt = tin / 7
    for _ in range(80):
        h.run_to(h.sim.t + dt)
    c = clicks(h)
    assert len(c["t"])
    a = h.sim.flight.a
    # every event is revealed in the step in which it happens (an ideal detector: no jitter, the tag is the arrival)
    assert np.all(c["t"] <= c["tmsg"] * (1 + 1e-15)) and np.all(c["tmsg"] - c["t"] < dt * 1.0001)
    tR, tT = h.sim.times["t_R"], h.sim.times["t_T"]
    assert tT > tR and tR == pytest.approx(tin, rel=1e-12)  # model media: the group index is n (no dispersion)
    assert np.all(a["stage"][a["tdet"] <= h.sim.t] == 0)  # nothing past its arrival time is still in flight


def test_frame_shows_both_packets_until_a_detector_decides():
    h = old("metal", params={"pol": "s", "rate": 5e10})
    tin, tR, tT = h.sim.times["t_in"], h.sim.times["t_R"], h.sim.times["t_T"]
    assert tT > tR
    h.run_to(tin + 0.5 * tR)  # the first photons are past the structure, no detector reached yet
    meta, b = h.sim.frame()
    fl = b["fl"].reshape(-1, 6)
    out = fl[fl[:, 0] == 1]
    assert len(out) > 0
    R, T_, _ = (h.of("segment")[0]["cur"]["s"][k] for k in ("R", "T", "A"))
    wR = R / (R + T_)
    pending = out[(out[:, 2] < 1)]
    assert np.allclose(pending[:, 3], wR) and np.allclose(pending[:, 5], 1 - wR)  # the same for every outcome
    # between the two arrival times the silent reflection detector (ideal) has removed the reflected packet
    h.run_to(h.sim.t + 0.5 * (tR + tT) - 0.5 * tR)
    meta, b = h.sim.frame()
    fl = b["fl"].reshape(-1, 6)
    late = fl[(fl[:, 0] == 1) & (fl[:, 2] >= 1)]
    assert len(late) and np.all(late[:, 3] == 0) and np.all(late[:, 5] == 1)


def test_a_real_detector_weighs_the_silent_arm_by_its_efficiency():
    """With efficiency η a silent detector does not rule its arm out: the other packet's weight is Bayes's
    P_T/(P_T + P_R(1 − η)), not 1."""
    h = old("metal", params={"pol": "s", "rate": 5e10, "det": "spcm_aqrh_14_650nm"})
    tin, tR, tT = h.sim.times["t_in"], h.sim.times["t_R"], h.sim.times["t_T"]
    h.run_to(tin + 0.5 * tR)
    h.run_to(h.sim.t + 0.5 * (tR + tT) - 0.5 * tR)
    meta, b = h.sim.frame()
    fl = b["fl"].reshape(-1, 6)
    late = fl[(fl[:, 0] == 1) & (fl[:, 2] >= 1)]
    R, T_ = (h.of("segment")[0]["cur"]["s"][k] for k in ("R", "T"))
    wR, eta = R / (R + T_), 0.65
    assert len(late) and np.allclose(late[:, 5], (1 - wR) / ((1 - wR) + wR * (1 - eta)))


def test_engine_modules_and_header():
    h = Harness(V)
    head = h.of("header")[0]
    assert head["title"]["$t"] == "Optical bench: {structure}" and head["modifications"] == []
    assert {a["name"] for a in head["actions"]} == {"emit_one", "clear"}
    assert h.sim.engine_modules() == ["core.optics.interfaces", "core.optics.thin_films", "core.optics.polarization",
                                      "core.optics.materials", "core.constants", "theories.models.photodetector",
                                      "theories.approx.ray_optics"]
    assert {m["id"] for m in head["measurables"]} >= {"n_R", "n_T", "n_Rp", "n_Rr", "n_Tp", "n_Tr", "R_frac", "t_c"}


# --- review 2026-10-23 ------------------------------------------------------------------------------------------
THC = math.degrees(math.asin(1.0 / 1.5))  # glass 1.5 -> air


def test_exact_critical_angle_is_accepted_and_every_check_holds():
    """V5-1/V5-2: at theta_c as the float asin gives it (and a few ulp around it) the evanescent decay constant is 0 or
    lost in rounding: the change raised ZeroDivisionError inside `set` (world half-changed) or the `evan` check failed
    (18 of 39 values above theta_c). Now the change is accepted and the check is decided only where the numbers
    determine the decay length (its tolerance follows the condition number), else shown for information."""
    for th in [THC, float(f"{THC:.12g}")] + [THC + k * 1e-14 for k in range(-20, 41)]:
        h = old("tir")
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
    h = old("tir")
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
    h = old(preset)
    h.set(**params)
    assert not h.errors()
    c = h.checks()["film1"]
    assert c["ok"] is True, c
    assert not failed(h), failed(h)


def test_joule_check_resolves_a_one_nanometre_skin_depth():
    """V5-3: n0 = 4, metal 0.2 + 20i, 500 nm, 300 nm, 70.24 deg: R + T + A_J - 1 = +2.9e-8 with 2001 Simpson points
    (tolerance 1e-8: failed); the quadrature now follows the skin depth (1.2 nm) and the standing-wave period."""
    h = old("metal", params={"n0": 4.0, "metal_n": 0.2, "metal_k": 20.0, "metal_d_nm": 500.0, "lam_nm": 300.0,
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
    import u35_optics_bench.viz as vz
    h = old("tir")
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
    h = old("metal", seed=3)
    run_photons(h, 20000)
    assert h.checks()["stat0"]["ok"] is True
    c = h.sim.segc[0]
    iT, iA = 2, 4  # T_pass (the sole transmission detector) and A among the five outcomes
    assert c["fate"][iT] > 500 and c["fate"][iA] > 500 and abs(c["probs"][iT] - c["probs"][iA]) > 0.05
    c["probs"][iT], c["probs"][iA] = c["probs"][iA], c["probs"][iT]  # the expectation of T and A swapped
    h.sim._stat_check(0)
    assert h.checks()["stat0"]["ok"] is False
    c["probs"][iT], c["probs"][iA] = c["probs"][iA], c["probs"][iT]
    h.sim._stat_check(0)
    assert h.checks()["stat0"]["ok"] is True


def test_critical_angle_is_not_confused_with_an_opaque_structure():
    """Found while fuzzing the V5-2 fix: a thick film of lower index than n0 is evanescent beyond its grazing angle and
    its T underflows to exactly 0 long before the exit critical angle; the bisection on the structure's T then
    reported that angle (22-25 deg instead of arcsin(3/4) = 48.6 deg here) and the `crit` check failed. The critical
    angle is now found on the bare boundary n_in -> n_out (n sin theta is the same in every layer)."""
    h = old("fp", params={"n0": 4.0, "ns": 3.0, "fp_n": 1.5, "fp_d_nm": 20000.0, "lam_nm": 300.0, "theta_deg": 10.0})
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
    h = old("fp", params={"n0": 4.0, "ns": ns, "fp_n": 2.3, "fp_d_nm": d, "lam_nm": lam, "theta_deg": th,
                          "pol": "unpol"})
    assert not failed(h), failed(h)
    ch = h.checks()
    assert ch["airy0"]["ok"] is True and ch["airymax0"]["ok"] is True, (ch["airy0"], ch["airymax0"])


# --- the engine's refusals matched by their machine codes (review 2026-11-12 i18n-code F5) ------------------------
def _raised(f, *a):
    with pytest.raises(ValueError) as e:
        f(*a)
    return e.value


@pytest.mark.parametrize("code,call", [
    ("airy.total_reflection", lambda: thin_films.airy(1.5, 1.0, 1.5, 200.0, 600.0, math.radians(60.0), "s")),
    ("airy.lossy_index", lambda: thin_films.airy(1.0, 1.5 + 0.1j, 1.5, 200.0, 600.0, 0.3, "s")),
    ("airy.grazing", None),
])
def test_airy_refusals_map_to_the_worlds_words_by_code(code, call):
    """`_airy_reason` reads the engine's code, not its English: every Airy refusal gets the world's own sentence."""
    from lfphys.codes import code_of, coded
    from lfphys.i18n import T
    from u35_optics_bench.viz import _AIRY_REASONS, _airy_reason
    e = _raised(call) if call else coded(ValueError(T("airy: reworded by the engine")), code)
    assert code_of(e) == code
    assert _airy_reason(e) == _AIRY_REASONS[code] and _airy_reason(e)["$t"] != e.args[0]["$t"]


def test_airy_grazing_is_coded_by_the_engine():
    """The grazing case for real: n₀ sin θ equal to the film's index, cos θ₁ = 0 (single_film / airy)."""
    from lfphys.codes import code_of
    th = math.asin(1.2 / 1.5)
    codes = set()
    for f in (thin_films.airy, thin_films.single_film):
        try:
            f(1.5, 1.2, 1.0, 200.0, 600.0, th, "s")
        except ValueError as e:
            codes.add(code_of(e))
    assert codes and codes <= {"airy.grazing", "airy.total_reflection"}


def test_airy_reason_without_a_code_keeps_the_engines_text():
    from lfphys.i18n import T
    from u35_optics_bench.viz import _airy_reason
    assert _airy_reason(ValueError(T("some new refusal"))) == T("some new refusal")
    assert _airy_reason(ValueError("plain"))["$t"] == "the engine's reason: {err}"


def test_film_below_critical_maps_to_no_reference():
    from lfphys.codes import code_of
    from u35_optics_bench.viz import _evanescent_ref
    th = math.radians(20.0)  # below the critical angle of glass 1.5 -> air
    assert code_of(_raised(thin_films.evanescent_length, 1.5, 1.0, 600.0, th)) == "film.below_critical"
    assert _evanescent_ref(1.5, 1.0, 600.0, th) is None
    assert _evanescent_ref(1.5, 1.0, 600.0, math.radians(60.0)) > 0


def test_joule_quadrature_limit_maps_to_an_informational_check(monkeypatch):
    """film.too_many_nodes: the Joule check becomes informational with the engine's numbers, never a crash."""
    from lfphys.codes import coded
    from lfphys.i18n import T
    from u35_optics_bench import viz as VZ

    def refuse(*a, **k):
        raise coded(ValueError(T("Joule absorption: {n:d} quadrature nodes needed in one layer (the limit is {lim:d})",
                                 n=99999, lim=4096)), "film.too_many_nodes")

    monkeypatch.setattr(VZ.thin_films, "joule_absorption_s", refuse)
    h = old("metal")
    c = h.checks()["joule0"]
    assert c.get("info") and c["note"]["$t"].startswith("not checked here: the Joule integral")
    assert c["note"]["a"] == {"n": 99999, "lim": 4096}
    assert not h.errors()
