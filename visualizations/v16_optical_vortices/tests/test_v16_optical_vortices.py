# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v16: optical vortices. Every preset builds and passes its checks; the equiphase sheets of each phase of the slowed
optical period are revealed only as the world's time reaches it, and their vertices lie on the computed field's
surface of that phase (checked against the engine's direct route, not against a formula); the detector's samples
come as the time runs and their spectrum gives the beat 2|l| f, also after a live change of f; the spin-orbit split
of the exact tightly focused beam against the paraxial model; slices of any orientation checked at points; the fork
hologram's orders (charges and shares of the power against the thin mask's closed form); worlds without a rotating
element refuse a live change; and the regressions of review B8-beams (O1-O16): the order of the paraxial check,
labelled and refused sources, both splits of the angular momentum and the Poynting closed form as checks, the cost
guard, the plate's checks as checks, the prism's orientation, the table's reach, the flow lines' step error."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from v16_optical_vortices.viz import NB, SCHEMA  # noqa: E402

V = "v16_optical_vortices"


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_builds_and_passes_its_checks(preset):
    h = Harness(V, preset, {})
    h.run_to(0.9)  # two measurements of the detector at f = 5 Hz (128 samples each, two turns)
    assert not h.errors(), h.errors()
    assert not failed(h), failed(h)
    if h.sim.det is not None:
        assert "beat" in h.checks() and len(h.of("beat")) >= 2


def test_phases_of_the_optical_period_are_revealed_only_as_time_reaches_them():
    h = Harness(V, "lg3", {"rot": "none"})
    T = h.sim.T_show
    assert [m["bin"] for m in h.of("helix")] == [0]
    h.run_to(0.49 * T)
    assert sorted(m["bin"] for m in h.of("helix")) == list(range(8))  # bins 0..7 at t_k = k T / 16 <= 0.49 T
    assert all(m["t_bin"] <= m["t"] + 1e-12 for m in h.of("helix"))
    h.run_to(1.5 * T)
    assert sorted(m["bin"] for m in h.of("helix")) == list(range(NB))
    f = h.sim.frame()[0]
    assert f["bin"] == int(1.5 * NB) % NB and f["revealed"] == NB
    h.run_to(3.0 * T)
    assert len(h.of("helix")) == NB  # nothing new after one period: the sheets repeat


def test_sheet_vertices_lie_on_the_computed_surface_of_their_phase():
    h = Harness(V, "lg3", {"rot": "none"})
    h.run_to(h.sim.T_show * 0.4)
    bm = h.sim.beam
    rng = np.random.default_rng(2)
    for (m, b) in [(m, b) for m, b in h.msgs if m.get("type") == "helix"]:
        pos = np.asarray(b["pos"], float).reshape(-1, 3)
        idx = rng.choice(len(pos), size=min(40, len(pos)), replace=False)
        P = pos[idx].T
        psi = bm.psi(None, None, None, bm.direct(*P))  # the direct route, not the table the mesh came from
        phase = 2 * math.pi * m["bin"] / NB
        d = np.abs(np.angle(psi * np.exp(-1j * phase)))
        assert np.max(d) < 2e-2, (m["bin"], np.max(d))  # linear interpolation along phi on 192 samples
    pos0 = np.asarray([b for m, b in h.msgs if m.get("type") == "helix"][0]["pos"], float).reshape(-1, 3)
    psi = bm.psi(None, None, None, bm.direct(*pos0[:40].T))  # bin 0's vertices against the phase pi/2
    assert np.max(np.abs(np.angle(psi * np.exp(-1j * math.pi / 2)))) > 1.0  # negative control: another phase


def test_detector_samples_come_with_time_and_the_beat_follows_a_live_change():
    h = Harness(V, "lg3", {})
    l = h.sim.l
    h.run_to(0.3)
    assert all(np.max(b["ts"]) <= m["t"] + 1e-12 for m, b in h.msgs if m.get("type") == "trace")
    assert "beat" not in h.checks()  # 128 samples take two turns: 0.4 s at 5 Hz
    h.run_to(0.85)
    c = h.checks()["beat"]
    assert abs(c["value"] - 2 * abs(l) * 5.0) < 1e-3 * 2 * abs(l) * 5.0
    sh = h.checks()["shift"]
    assert abs(sh["value"] + l * 5.0) < 1e-3 * l * 5.0
    h.set(f_rot=8.0)
    t_set = h.sim.t
    h.run_to(t_set + 2.0 / 8.0 * 1.05)
    c = h.checks()["beat"]
    assert c["ref"] == 2 * abs(l) * 8.0 and abs(c["value"] - c["ref"]) < 1e-3 * c["ref"], c
    last = h.of("trace")[-1]
    assert last["seg"] == 1 and last["f_rot"] == 8.0


def test_dove_prism_beat_and_shift():
    h = Harness(V, "dove", {})
    h.run_to(0.85)
    l = h.sim.l
    assert abs(h.checks()["beat"]["value"] - 2 * abs(l) * 5.0) < 1e-2
    assert abs(h.checks()["shift"]["value"] + 2 * l * 5.0) < 1e-2  # l_out 2 f, l_out = -l


def test_no_vortex_no_beat():
    h = Harness(V, "l0", {})
    h.run_to(0.85)
    c = h.checks()["beat"]
    assert c["ok"] and c["value"] < 1e-6


def test_spin_orbit_split_of_the_exact_tight_beam_and_the_paraxial_model():
    ex = Harness(V, "tight", {})
    am = ex.of("am")[0]
    assert abs(am["J"] - (am["l"] + am["sigma"])) < 1e-3
    # sigma = -1: |S_z| < 1 and L_z - l = sigma (1 - <cos theta>) < 0 (measured 2026-11-04: S = -0.842, L = 0.842)
    assert am["S"] > -1 + 0.05 and am["L"] < am["l"] - 0.05
    # Barnett's split of the flux moves the other way: |S_flux| > 1 (measured -1.024); J is the same (review O3)
    assert am["S_flux"] < -1 and am["L_flux"] > am["l"] and abs(am["S_flux"] + am["L_flux"] - am["J_ref"]) < 1e-3
    assert am["ez"] > 0.2  # the longitudinal field of tight focusing
    hd = ex.of("header")[0]
    # the LG_{0,1} waist at w0 = 0.6 lambda puts 0.66 % of its power beyond q = k: labelled (review O2)
    assert any("обрезан на q = k" in a for a in hd["approximations"]) and "обрезан" in hd["title"]
    assert abs(ex.checks()["kept"]["value"] - (1 - 0.0066476)) < 1e-6
    px = Harness(V, "tight_par", {})
    amp = px.of("am")[0]
    # the paraxial model's spin computed from its own field (review O9): sigma, by construction of u e_sigma
    assert abs(amp["L"] - amp["l"]) < 1e-3 and abs(amp["S"] - amp["sigma"]) < 1e-9
    assert not px.checks()["am_S"].get("info") and px.checks()["am_S"]["ok"]
    assert any("параксиальная" in a for a in px.of("header")[0]["approximations"])
    assert all(s["approximation"] for s in px.of("slice"))


def test_slices_of_any_orientation_are_computed_and_checked():
    h = Harness(V, "lg3", {"rot": "none"})
    n = np.array([0.4, -0.3, 0.866])
    h.cmd("view", op="plane", id=2, origin=list(h.sim.plane_center), normal=list(n / np.linalg.norm(n)))
    sl = [m for m in h.of("slice") if m["id"] == 2][-1]
    assert sl["verify"]["points"] == 3 and sl["verify"]["ok"]
    assert h.checks()["plane_2"]["ok"]
    h.cmd("view", op="remove", id=2)
    assert all(p["id"] != 2 for p in h.of("planes")[-1]["planes"])


def test_fork_orders_carry_charge_m_l_and_refuse_tilted_slices():
    h = Harness(V, "fork", {"l": 2})
    ch = h.checks()
    assert ch["order_1"]["value"] == 2 and ch["order_-1"]["value"] == -2 and ch["order_0"]["value"] == 0
    assert not failed(h)
    n0 = len(h.of("slice"))
    h.cmd("view", op="plane", id=2, origin=list(h.sim.plane_center), normal=[0.0, -1.0, 0.0])  # y = c: exact route
    assert len(h.of("slice")) == n0 + 1
    h.cmd("view", op="plane", id=3, origin=list(h.sim.plane_center), normal=[0.3, 0.0, 0.95])
    assert len(h.of("slice")) == n0 + 1  # refused: only planes along the axes for the hologram


def test_worlds_without_a_rotating_element_refuse_a_live_change():
    h = Harness(V, "tight", {})
    with pytest.raises(ValueError):
        h.sim.set_live({"f_rot": 3.0})


def test_detector_negative_control_measures_another_frequency_for_another_l():
    """The measured beat is a property of the field: worlds with l = 2 and l = 3 measure different beats at the same
    f (the detector does not read the closed form)."""
    out = {}
    for l in (2, 3):
        h = Harness(V, "lg3", {"l": l})
        h.run_to(0.85)
        out[l] = h.checks()["beat"]["value"]
    assert abs(out[3] - out[2] - 2 * 5.0) < 1e-2


def test_parax_check_is_the_transverse_difference_and_of_second_order():
    """Review O1: the check «Параксиальная мода против точного поля» compares the transverse components (E_z, which the
    mode lacks, is the check «Продольное поле»): doubling w0 divides it by 4 (second order, measured 4.1), while
    E_z / |E| halves (first order). Negative control: the old all-component value (= max |E_z|) only halves."""
    out = {}
    for w0 in (1.5, 3.0):
        h = Harness(V, "lg3", {"w0": w0, "rot": "none", "zspan": 0.4})
        out[w0] = (h.checks()["parax"]["value"], h.checks()["ez"]["value"])
    rt, rz = out[1.5][0] / out[3.0][0], out[1.5][1] / out[3.0][1]
    assert 3.5 < rt < 4.6, out
    assert 1.8 < rz < 2.2, out


def test_sources_beyond_q_k_are_labelled_or_refused():
    """Review O2: an LG world whose waist lies (almost) wholly beyond q = k is refused with the reason; one that drops
    more than 1e-4 of the waist's power is labelled (header, title, check «kept»); the default world drops nothing;
    a plate world states its evanescent near field (no refusal for it: the beam is the plate's exact far field), but
    one whose incident Gaussian is itself mostly evanescent is refused."""
    with pytest.raises(ValueError, match="затухающие волны"):
        Harness(V, "lg3", {"l": 6, "p": 3, "w0": 0.3, "lam": 1.6, "rot": "none"})
    with pytest.raises(ValueError, match="затухающие волны"):
        Harness(V, "lg3", {"l": 1, "w0": 0.3, "lam": 1.0, "rot": "none"})  # 47 % beyond k
    with pytest.raises(ValueError, match="не пучок"):  # the plate's incident Gaussian: 50 % beyond k
        Harness(V, "spp", {"l": 6, "w0": 0.3, "lam": 1.6, "rot": "none"})
    h = Harness(V, "lg3", {"rot": "none"})
    assert not any("обрезан" in a for a in h.of("header")[0]["approximations"])
    assert h.checks()["kept"]["value"] > 1 - 1e-12
    sp = Harness(V, "spp", {"rot": "none"})
    hd = sp.of("header")[0]
    assert any("затухающих волн за пластинкой" in a for a in hd["approximations"])
    ev = sp.sim.beam.ev_near
    assert 0 < ev[2] < ev[1] < sp.sim.beam.dropped


def test_angular_momentum_checks_are_checks_where_the_window_holds():
    """Reviews O3, O4, O6: in the default world the canonical split, Barnett's flux split and the Poynting moment (its
    closed form J + (sigma/2) <sin^2/cos>) are checks and pass; in the plate world (window 25 lambda) the split's
    checks are checks too; its Poynting moment, whose window error falls only as R^-1/2 for a spectrum cut at q = k,
    is shown for information with that reason."""
    h = Harness(V, "lg3", {"rot": "none"})
    ch = h.checks()
    for cid in ("am_J", "am_S", "am_L", "am_flux", "am_S_flux", "am_L_flux", "am_poynting"):
        assert not ch[cid].get("info") and ch[cid]["ok"], (cid, ch[cid])
    assert ch["am_S_flux"]["value"] > 1 > ch["am_S"]["value"]
    assert abs(ch["am_poynting"]["value"] - ch["am_J"]["value"]) > 0.04  # not L_z + S_z
    sp = Harness(V, "spp", {"rot": "none"})
    cs = sp.checks()
    assert sp.of("am")[0]["miss"] < 1e-3
    for cid in ("am_J", "am_S", "am_L", "am_flux", "am_S_flux", "am_L_flux"):
        assert not cs[cid].get("info") and cs[cid]["ok"], (cid, cs[cid])
    assert cs["am_poynting"].get("info") and "R^−1/2" in cs["am_poynting"]["note"]


def test_cost_guard_refuses_with_an_estimate_before_building():
    """Review O5: the legal corner that needed an ~18 GB matrix and the plate world that took 46 s are refused at once
    with the estimate; the defaults are far inside the budget."""
    import time
    for params in ({"gen": "spp", "l": 6, "w0": 6.0, "lam": 0.4, "zspan": 3.0},
                   {"gen": "spp", "l": 2, "w0": 6.0, "lam": 1.0, "zspan": 1.5}):
        t0 = time.time()
        with pytest.raises(ValueError, match="слишком дорог"):
            Harness(V, "lg3", params)
        assert time.time() - t0 < 5.0
    from v16_optical_vortices.engine import apparatus as A
    h = Harness(V, "lg3", {"rot": "none"})
    assert h.sim.beam.cost["bessel"] < 0.1 * A.BESSEL_BUDGET


def test_fork_shares_against_the_closed_form_of_the_thin_mask():
    """Review O8: each order's share of the propagating power, measured in the angular spectrum, against the closed
    form of the same thin mask (the orders' overlapping tails included); the ideal |c_m|^2 / sum is not what is
    measured (it is off by more than 5e-3)."""
    h = Harness(V, "fork", {})
    sh = h.sim.fork_shares
    for m in (-1, 0, 1):
        c = h.checks()[f"frac_{m}"]
        assert not c.get("info") and c["ok"], c
        assert abs(sh["ideal"][m] - sh["meas"][m]) > 5e-3


def test_dove_prism_mesh_mirrors_across_the_rotators_line():
    """Review O13: the drawn prism's base face is normal to y, so the reflection off it maps y -> -y, the mirror of
    the engine's image rotator at angle 0 (the x axis)."""
    from lfphys.core.optics import beams_rotation as ROT
    from v16_optical_vortices.engine import apparatus as A
    L, hgt = 2.0, 1.0
    pos, _, _ = A.prism_mesh(L, hgt, 0.8 * hgt)
    base = pos[np.isclose(pos[:, 1], -hgt / 2)]
    assert len(base) == 4 and np.allclose(sorted(set(np.round(np.abs(base[:, 2]), 6))), [L / 2])
    assert np.allclose(np.ptp(pos[:, 1]), hgt) and np.allclose(np.ptp(pos[:, 0]), 0.8 * hgt)
    out = ROT.image_rotator(lambda x, y, z: x + 2j * y, 0.0, vector=False)(np.array(0.3), np.array(0.7), 0.0)
    assert abs(out - (0.3 - 1.4j)) < 1e-15  # y -> -y


def test_table_reaches_every_point_the_consumers_sample():
    """Review O14: l = 6, p = 3 with a Dove prism (its square's corner was 19.29 um against a table ending at
    19.23 um): the table's radius covers the volume's and slices' corners, the angular-momentum plane, the disc's
    quadrature and the prism's square."""
    from v16_optical_vortices.engine import apparatus as A
    h = Harness(V, "lg3", {"l": 6, "p": 3, "rot": "dove"})
    bm = h.sim.beam
    r_end = float(bm.r[-1])
    assert r_end >= math.sqrt(2) * bm.half and r_end >= math.sqrt(2) * bm.am_half
    assert r_end >= math.sqrt(2) * float(np.max(np.abs(h.sim.det.X)))
    assert r_end >= A.detector_radius(bm, bm.z1)


def test_poynting_flow_lines_carry_their_step_error():
    """Review O16: the exact world's Poynting lines are re-traced with half the step on two lines; the difference is
    reported (information) and is small against w0 for the default world."""
    h = Harness(V, "lg3", {"rot": "none"})
    c = h.checks()["flow_step"]
    assert c.get("info") and 0 <= c["value"] < 1e-6
    px = Harness(V, "tight_par", {})
    assert "flow_step" not in px.checks()  # the paraxial world draws no Poynting lines


def test_fork_from_the_defaults_takes_a_waist_its_orders_separate_with():
    """Review UX-params P11: «Голограмма-вилка» alone was refused for every period (the default waist 1.5 µm, the LG
    modes', spreads faster than the orders separate: tan θ1 must exceed 9/(k w0)), and its advice could not be
    followed. Now the world takes the smallest waist with a 20 % margin (0.1 µm steps) and says so; the header carries
    it; the result is the preset's (4 µm at Λ = 2.5 µm) and its checks pass. A waist given wide enough is kept; a period
    no waist of the form can take, and Λ <= λ, are refused naming what to change. Negative control: below the bound
    (the old refusal's condition) the orders overlap."""
    import math
    import re
    h = Harness(V, None, {"gen": "fork"})
    hp = h.of("header")[-1]["params"]
    k, tan = 2 * math.pi / 1.0, (1 / 2.5) / math.sqrt(1 - (1 / 2.5) ** 2)
    assert hp["w0"] == 4.0 == math.ceil(1.2 * 9 / (k * tan) * 10) / 10
    assert any("Мир взял w0 = 4 мкм" in m["text"] for m in h.of("notice"))
    h.run_to(1.0)
    assert not failed(h)
    assert 9 / (k * 1.5) > tan  # the default waist: the orders would not separate (the old refusal)
    h = Harness(V, None, {"gen": "fork", "w0": 5.0})
    assert h.of("header")[-1]["params"]["w0"] == 5.0 and not h.of("notice")
    with pytest.raises(ValueError) as e:
        Harness(V, None, {"gen": "fork", "period": 8.0})
    p_max = float(re.search(r"до ([\d.]+) мкм или меньше", str(e.value)).group(1))
    Harness(V, None, {"gen": "fork", "period": p_max})  # the named period builds
    with pytest.raises(ValueError, match="больше 1 мкм"):
        Harness(V, None, {"gen": "fork", "period": 1.0})
