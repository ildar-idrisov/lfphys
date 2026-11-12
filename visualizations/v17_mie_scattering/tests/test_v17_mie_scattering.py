# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v17: scattering of light by drops. Every preset builds and passes its checks; what the run sends is the engine's
(the phase function and the Debye terms against lfphys.core.optics.mie and mie_debye called directly, the sky's
spectra against mie_poly, the near field against mie.near_field); the sky is revealed one wavelength per T_LAM of world
time; a live change of the light recomputes the drop and restarts the sky; the near-field slices are verified on the
drop's surface; invalid drops are refused. Every pass/fail check shown has a negative control here: a broken engine
part it catches (review B8-mie, M3), and the identities of the series' structure are shown to be blind to wrong
coefficients, which only `debye` and `wiscombe` detect."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import data as D  # noqa: E402
from lfphys.core.optics import mie, mie_debye as DB, mie_poly as MP  # noqa: E402
from v17_mie_scattering.engine import drops as DR  # noqa: E402
from v17_mie_scattering.viz import DISP_DEG, MAX_NODES, N_QUAD, SCHEMA, SKY_TH, T_LAM  # noqa: E402

V = "v17_mie_scattering"
FAST = {"n_lam": 8}


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def last(h, typ):
    out = [(m, b) for m, b in h.msgs if m.get("type") == typ]
    return out[-1] if out else (None, None)


@pytest.mark.parametrize("preset", [p for p in SCHEMA.presets if p != "big_drops"])
def test_every_preset_builds_and_passes_its_checks(preset):
    h = Harness(V, preset, FAST)
    h.run_to(h.sim.sky_n * T_LAM + 0.01)
    assert not h.errors(), h.errors()
    assert not failed(h), failed(h)
    assert h.sim.sky_k == h.sim.sky_n
    ids = set(h.checks())
    assert {"theorem", "debye", "mueller", "sky_sum", "wiscombe"} <= ids
    if h.sim.near:
        assert {"boundary", "plane_1"} <= ids


def test_the_heavy_preset_builds_and_adds_its_first_wavelength():
    h = Harness(V, "big_drops", {"n_lam": 8})
    h.run_to(T_LAM + 1e-9)
    assert not h.errors() and not failed(h)
    m, _ = last(h, "sky")
    assert m["k"] == 0 and m["n_nodes"] <= MAX_NODES and m["coarse"]


def test_the_sky_is_revealed_one_wavelength_at_a_time():
    h = Harness(V, "glory", FAST)
    assert not h.of("sky")
    for k in range(1, 4):
        h.run_to(k * T_LAM + 1e-9)
        assert len(h.of("sky")) == k
    assert "sky_bow" not in h.checks()  # the summary checks come only when every wavelength is in
    h.run_to(8 * T_LAM + 1e-9)
    assert len(h.of("sky")) == 8 and "sky_bow" in h.checks()


def test_the_drop_sent_is_the_engines():
    """The phase function, the polarisation and the Debye terms sent equal the engine's functions called directly
    (near preset: x ~ 11, the display grid is the computed one, no binning)."""
    h = Harness(V, "near", FAST)
    m, b = last(h, "mono")
    lam = m["lam_nm"]
    mm = DR.index(h.params, lam)
    x = float(mie.size_parameter(1.0, lam * 1e-3, 1.0))
    assert m["x"] == pytest.approx(x, rel=1e-15) and m["n_fine"] == len(DISP_DEG)
    r = mie.scattering(mm, x, np.radians(DISP_DEG))
    norm = 4.0 / (x * x * r["Qsca"])
    assert np.allclose(b["s11"], (r["S11"] * norm).astype(np.float32), rtol=1e-6)
    assert np.allclose(b["pol"], r["P"].astype(np.float32), atol=1e-6)
    dd = DB.amplitudes(mm, x, np.radians(DISP_DEG), p_max=3)
    p2 = 0.5 * (np.abs(dd["S1"][2]) ** 2 + np.abs(dd["S2"][2]) ** 2) * norm
    assert np.allclose(b["deb2"], p2.astype(np.float32), rtol=1e-6)
    assert m["Q"]["Qext"] == pytest.approx(r["Qext"], rel=1e-14)


def test_the_binned_phase_function_of_a_large_drop():
    """For x ~ 1700 the run computes a finer grid and sends bin means with the bin's minimum and maximum: the mean lies
    between them and the 4 pi normalisation of the phase function holds for the bin means (trapezoid, 0.05 deg)."""
    h = Harness(V, "rainbow", FAST)
    m, b = last(h, "mono")
    assert m["n_fine"] > len(DISP_DEG)
    assert np.all(b["lo"] <= b["s11"] * (1 + 1e-6)) and np.all(b["s11"] <= b["hi"] * (1 + 1e-6))
    th = np.radians(DISP_DEG)
    tot = 2 * math.pi * np.trapezoid(b["s11"].astype(float) * np.sin(th), th)
    # the forward peak (width ~1/x = 0.03 deg) is under-resolved by 0.05-deg bins: the trapezoid sum is a few % off
    assert abs(tot / (4 * math.pi) - 1) < 0.05


def test_the_sky_sent_is_the_engines_size_average():
    h = Harness(V, "fogbow", FAST)
    h.run_to(T_LAM + 1e-9)
    m, b = last(h, "sky")
    lam = m["lam_nm"]
    nodes = MP.size_nodes(15.0, 0.15, lam * 1e-3, 1.0, max_nodes=MAX_NODES)
    av = MP.average(DR.index(h.params, lam), lam * 1e-3, nodes, SKY_TH, 1.0)
    assert np.allclose(b["dsdo"], av["dsdo"].astype(np.float32), rtol=1e-6)
    assert m["n_nodes"] == len(nodes["w"]) and m["k"] == 0


def test_white_light_colour_is_the_sum_of_the_wavelengths():
    """The strip's colour after all wavelengths equals the XYZ of the summed spectra (sun x cloud x CMFs), recomputed
    here from the sky messages: the run adds what it sent."""
    h = Harness(V, "glory", FAST)
    h.run_to(8 * T_LAM + 1e-9)
    lams, ws = DR.wavelengths(8)
    XYZ = np.zeros((len(SKY_TH), 3))
    for (m, b), lam, w in zip([(m, b) for m, b in h.msgs if m.get("type") == "sky"], lams, ws):
        assert m["lam_nm"] == pytest.approx(lam)
        XYZ += w * float(DR.sun(lam)) * b["dsdo"].astype(float)[:, None] * DR.cmf(lam)[None, :]
    rgb = DR.strip_rgb(XYZ)
    _, b = last(h, "sky")
    # float32 transport of dsdo: a level at most
    assert np.max(np.abs(rgb.reshape(-1).astype(int) - b["rgb"].astype(int))) <= 1


def test_a_live_change_recomputes_the_drop_and_restarts_the_sky():
    h = Harness(V, "near", FAST)
    h.run_to(0.3)
    n_mono = len(h.of("mono"))
    h.set(lam_nm=450.0)
    assert len(h.of("mono")) == n_mono + 1 and h.of("mono")[-1]["lam_nm"] == 450.0
    assert h.of("sky_start")[-1]["seq"] == 2
    assert h.of("slice")[-1]["t"] == pytest.approx(0.3)
    h.set(light="white")
    assert h.of("sky_start")[-1]["n"] == 8 and h.sim.sky_k == 0
    h.run_to(0.3 + 8 * T_LAM + 1e-9)
    assert h.sim.sky_k == 8


def test_near_field_slices_and_volume():
    """The volume and a slice are the engine's near field; a second plane placed by the view command is verified on
    the drop's surface; removing it says so."""
    h = Harness(V, "near", FAST)
    vol, vb = last(h, "volume")
    assert vol["dims"] == [40, 40, 40] and float(np.max(vb["data"])) == pytest.approx(1.0)
    sl, sb = last(h, "slice")
    assert sl["verify"]["ok"] and sl["units"] == "a"
    # the slice's centre value against mie.near_field at that point
    i = sl["shape"][0] // 2
    j = sl["shape"][1] // 2
    s = np.linspace(*sl["s"][:2], sl["s"][2])[j]
    t = np.linspace(*sl["tt"][:2], sl["tt"][2])[i]
    P = np.asarray(sl["origin"]) + s * np.asarray(sl["u"]) + t * np.asarray(sl["v"])
    E = mie.near_field(h.sim.m, h.sim.x, P[None, :])["E"][0]
    assert float(sb["I"][i, j]) * sl["peak"] == pytest.approx(float(np.sum(np.abs(E) ** 2)), rel=1e-5)
    h.cmd("view", op="plane", id=2, origin=[0.0, 0.0, 0.3], normal=[0.0, 0.0, 1.0])
    assert h.checks()["plane_2"]["ok"]
    h.cmd("view", op="remove", id=2)
    assert h.checks()["plane_2"].get("info")


def test_the_water_index_and_the_drop_refusals():
    h = Harness(V, "rainbow", FAST)
    assert abs(h.sim.m - complex(float(D.water_index(550.0, 10.0)))) < 1e-15
    with pytest.raises(ValueError):
        Harness(V, "rainbow", {"radius_um": 1000.0, "width": 0.3})  # x > 2e4 at 380 nm
    viz_params, errs = SCHEMA.resolve("absorbing", {"n_im": -0.1})
    assert errs  # below the schema's minimum


def test_absorbing_drop_has_no_rainbow_checks():
    h = Harness(V, "absorbing", FAST)
    ids = set(h.checks())
    assert "energy" not in ids and "bow2" not in ids and "alexander" not in ids


def test_polar_surface_and_rays():
    pos, idx, rgb = DR.polar_mesh(np.linspace(0, 180, 91), np.ones(91), np.ones(91), "u")
    r = np.linalg.norm(pos, axis=-1)
    assert np.allclose(r, r[0]) and idx.max() < len(pos) and rgb.shape == (len(pos), 3)
    I2 = np.linspace(1.0, 2.0, 91)
    px, _, _ = DR.polar_mesh(np.linspace(0, 180, 91), I2, np.ones(91), "x")
    py, _, _ = DR.polar_mesh(np.linspace(0, 180, 91), I2, np.ones(91), "y")
    # x and y polarisations are the same surface turned by 90 degrees about z
    assert np.allclose(np.sort(np.linalg.norm(px, axis=-1)), np.sort(np.linalg.norm(py, axis=-1)))
    pts, col = DR.ray_fans(1.333)
    ok = np.isfinite(pts[:, 0])
    assert np.all(np.abs(pts[ok, 1]) == 0) and len(col) == len(pts)


# --- review B8-mie: the checks can fail, and they say what they test -------------------------------------------------
def _ok(c):
    """A check's verdict as the player decides it (an explicit ok, else |rel| <= tol)."""
    if c.get("ok") is not None:
        return bool(c["ok"])
    return abs(c["rel"]) <= c["tol"]


def test_energy_check_of_a_cloud_drop_with_the_new_quadrature(monkeypatch):
    """M2: a water drop of 5.3396 um at 550 nm (x = 61) failed the `energy` check on a correct engine (numpy's
    Gauss-Legendre weights near mu = +-1, rel 8.2e-12 against tol 5.1e-12); with Fejér's rule and the derived bound it
    passes. Negative controls: numpy's Gauss-Legendre weights in its place fail the derived bound; a wrong tau_n
    (the angular functions) fails it too."""
    p = {"radius_um": 5.3396, "width": 0.0, "n_lam": 8, "light": "mono"}
    h = Harness(V, "glory", p)
    c = h.checks()["energy"]
    assert c["value"] != c["ref"] and _ok(c) and c["tol"] < 1e-11
    gl = lambda n: np.polynomial.legendre.leggauss(n - 1)  # noqa: E731
    monkeypatch.setattr(mie, "fejer2", gl)
    assert not _ok(Harness(V, "glory", p).checks()["energy"])
    monkeypatch.undo()
    orig = mie.angular

    def bad_angular(mu, N):
        PI, TAU = orig(mu, N)
        return PI, TAU * (1 + 1e-6)
    monkeypatch.setattr(mie, "angular", bad_angular)
    assert not _ok(Harness(V, "glory", p).checks()["energy"])


@pytest.mark.filterwarnings("ignore:Casting complex values")  # the negative control's complex D_n meets real psi
def test_energy_identity_beyond_the_quadrature(monkeypatch):
    """Above N_QUAD terms the `energy` check is Re a_n = |a_n|^2, labelled an identity (it holds for any real A, B of
    a_n = A/(A - iB)): within 16 u on a correct engine (the denominator's real part is the numerator bit for bit);
    negative control: an imaginary part leaking into D_n (an absorbing drop computed as transparent) fails it."""
    p = {"radius_um": 300.0, "width": 0.0, "n_lam": 8, "light": "mono", "lam_nm": 550.0}
    h = Harness(V, "rainbow", p)
    assert h.sim.x > 2900 and len(h.sim.coef[0]) > N_QUAD
    c = h.checks()["energy"]
    assert _ok(c) and "тождество" in c["note"].lower()
    orig = mie.log_derivative
    monkeypatch.setattr(mie, "log_derivative", lambda z, N: orig(z, N) * (1 + 1e-9j))
    assert not _ok(Harness(V, "rainbow", p).checks()["energy"])


@pytest.mark.parametrize("part", ["D", "psi", "chi"])
def test_only_debye_and_wiscombe_catch_wrong_coefficients(monkeypatch, part):
    """M3: an engine whose D_n, psi_n or chi_n is wrong by 1e-3 (review s10) leaves `theorem`, `energy` and `mueller` at
    round-off — identities of the series' structure, labelled so — while `debye` (a second route) and `wiscombe` (the
    published numbers) fail. A drop of x ~ 23 (1 um at 380 nm... the near preset at 450 nm)."""
    p = {"n_lam": 8, "lam_nm": 450.0}
    h = Harness(V, "near", p)
    for cid in ("theorem", "energy", "mueller", "debye", "wiscombe"):
        assert _ok(h.checks()[cid]), cid
    if part == "D":
        orig = mie.log_derivative
        monkeypatch.setattr(mie, "log_derivative", lambda z, N: orig(z, N) * (1 + 1e-3))
    elif part == "psi":
        orig = mie.psi
        monkeypatch.setattr(mie, "psi", lambda z, N: orig(z, N) * (1 + 1e-3 * np.arange(N + 1) / N).reshape(
            (-1,) + (1,) * np.ndim(np.atleast_1d(z))))
    else:
        orig = mie.chi
        monkeypatch.setattr(mie, "chi", lambda xx, N: orig(xx, N) * (1 + 1e-3))
    ch = Harness(V, "near", p).checks()
    assert _ok(ch["theorem"]) and _ok(ch["energy"]) and _ok(ch["mueller"])  # blind: identities
    assert "тождество" in ch["theorem"]["note"].lower() and "тождество" in ch["energy"]["note"].lower()
    assert not _ok(ch["debye"]) and not _ok(ch["wiscombe"])


def test_the_identity_checks_catch_what_they_test(monkeypatch):
    """The identities are not empty: `theorem` fails with a wrong tau_n in the angular sum, `mueller` with a wrong S33
    (no conjugate), and the near field's `boundary` with the internal coefficients swapped (the field's assembly)."""
    p = {"n_lam": 8}
    orig_amp = mie.amplitudes

    def bad_amp(a, b, theta):
        S1, S2 = orig_amp(a, b, theta)
        return S1 * (1 + 1e-6), S2
    monkeypatch.setattr(mie, "amplitudes", bad_amp)
    assert not _ok(Harness(V, "near", p).checks()["theorem"])
    monkeypatch.undo()
    orig_m = mie.mueller

    def bad_mueller(S1, S2):
        r = orig_m(S1, S2)
        r["S33"] = (S2 * S1).real
        return r
    monkeypatch.setattr(mie, "mueller", bad_mueller)
    assert not _ok(Harness(V, "near", p).checks()["mueller"])
    monkeypatch.undo()
    orig_ic = mie.internal_coefficients
    monkeypatch.setattr(mie, "internal_coefficients", lambda *a, **k: orig_ic(*a, **k)[::-1])
    assert not _ok(Harness(V, "near", p).checks()["boundary"])


def test_debye_check_of_an_air_bubble_at_large_x():
    """M4: m = 0.75 (n = 1 in a medium of 1.333, an air bubble in water) at x = 1.9e4 (380 nm, 860 um): the
    Debye-route error 1.0e-9 exceeded v17's fixed 5e-10 on a correct engine; the derived per-order tolerance
    u (1000 N + 32 s) holds it (measured err/tol <= 0.46 over 281 cases)."""
    p = {"radius_um": 860.0, "width": 0.0, "index": "custom", "n_re": 1.0, "n_im": 0.0, "n_medium": 1.333,
         "light": "mono", "lam_nm": 380.0, "n_lam": 8}
    h = Harness(V, "rainbow", p)
    assert h.sim.x > 1.8e4
    c = h.checks()["debye"]
    assert c["value"] > 5e-10 and _ok(c)


def test_a_diverging_debye_series_is_announced():
    """M5: a weakly absorbing drop with m ~ 1 (n = 1 + 0.01i in vacuum, 30 um) has orders with |R11| > 1: the run
    sends a notice that its Debye terms are not paths of light, with the series' amplification; a water drop sends
    none."""
    h = Harness(V, "glory", {"index": "custom", "n_re": 1.0, "n_im": 0.01, "radius_um": 30.0, "width": 0.0,
                             "n_lam": 8})
    m, _ = last(h, "mono")
    assert m["debye"]["diverging_orders"] > 0
    assert any("расходится" in n.get("text", "") for n in h.of("notice"))
    assert _ok(h.checks()["debye"])
    h2 = Harness(V, "glory", FAST)
    assert not any("Дебая" in n.get("text", "") for n in h2.of("notice"))


def test_the_medium_cut_and_coarse_sampling_are_stated():
    """M6, M7, M14: vacuum as the medium is an approximation of the header (with the size of the shift in air); a
    medium of index != 1 is named; the size distribution's +-4 sigma cut is stated and its tail sent with each
    wavelength; coarse size sampling is a header approximation (big_drops), not only a text line; the rainbow preset
    is not coarse at 380 nm with the 1600-node cap."""
    h = Harness(V, "rainbow", FAST)
    hdr = h.of("header")[-1]
    ap = " ".join(hdr["approximations"])
    assert "вакуум" in ap and "±4σ" in ap and "грубая" not in ap
    assert MP.size_nodes(150.0, 0.02, 0.38, max_nodes=MAX_NODES)["coarse"] is False
    h.run_to(T_LAM + 1e-9)
    m, _ = last(h, "sky")
    assert 0 < m["tail"] < 1e-3 and not m["coarse"]
    hb = Harness(V, "big_drops", {"n_lam": 8})
    assert any("грубая" in a for a in hb.of("header")[-1]["approximations"])
    ha = Harness(V, "rainbow", {"n_medium": 1.0003, "n_lam": 8})
    ap2 = " ".join(ha.of("header")[-1]["approximations"])
    assert "вакуум" not in ap2 and "1.0003" in ap2


def test_info_checks_carry_no_misleading_tolerance_and_rays_for_m_below_1():
    """M11: the information checks in degrees (bow2, bow3, alexander, sky_bow) carry no tolerance (a degree tolerance
    against a relative difference was shown before) and state the difference in degrees; for m < 1 the drop's own
    rays are drawn (those of p >= 1 with b < m), not those of m = 1.333."""
    h = Harness(V, "rainbow", FAST)
    h.run_to(8 * T_LAM + 1e-9)
    for cid in ("bow2", "bow3", "alexander", "sky_bow"):
        c = h.checks()[cid]
        assert c.get("info") and c.get("tol") is None, cid
    assert "°" in h.checks()["bow2"]["note"]
    hb = Harness(V, "glory", {"index": "custom", "n_re": 1.0, "n_im": 0.0, "n_medium": 1.333, "radius_um": 3.0,
                              "width": 0.0, "n_lam": 8})
    m = hb.sim.m.real
    pts, col = DR.ray_fans(m)
    ok = np.isfinite(pts[:, 0])
    assert m < 1 and np.all(np.abs(pts[ok, 1]) == 0)
    lines = [ms for ms in hb.of("lines") if ms["id"] == "rays"][-1]
    assert "1,333" not in lines["label"] and "b < m" in lines["label"]


def test_the_polar_surface_uses_the_engine_intensity():
    """M12: the polar surface's radius follows mie.intensity_polarised (the B&H far field for x-polarised light)."""
    th = np.linspace(0, 180, 91)
    I1, I2 = np.linspace(1.0, 3.0, 91), np.linspace(2.0, 0.5, 91)
    pos, _, _ = DR.polar_mesh(th, I2, I1, "x")
    ph = np.linspace(0.0, 2 * math.pi, 72, endpoint=False)
    I = mie.intensity_polarised(I1[:, None], I2[:, None], ph[None, :], "x")
    f = np.clip(1.0 + np.log10(I / I.max()) / 5.0, 0.0, 1.0)
    assert np.allclose(np.linalg.norm(pos, axis=-1), (1.15 + 1.25 * f).reshape(-1), rtol=1e-6)


def test_index_matched_drop_is_refused_and_next_event_is_one_wavelength():
    """Review UX-params P16: an index-matched drop (n = 1, κ = 0 in a medium of 1) scatters nothing: its Mueller check
    was NaN and the Debye check failed (1163 against 0); up to |m - 1| = 1e-6 the Debye route still fails
    and the energy identity of large drops up to ~1e-4 (response_checks_v-worlds/v17_m1*.out). Now |m - 1| < 1e-3 is
    refused at the start (check_params too) and as a live change of the wavelength, saying what to change; m = 1.001
    builds and passes (negative control, at 1.0015). «⏭ событие» computed every
    wavelength of the sky at once (20-40 s, > 2 min for 1 mm drops): now one wavelength per press, and the size nodes
    of a wavelength are capped by a time budget (coarse, flagged)."""
    import time
    from v17_mie_scattering.viz import STEP_BUDGET_S, SKY_S_PER_UNIT, Simulation
    vals = {"index": "custom", "n_re": 1.0, "n_im": 0.0, "n_medium": 1.0}
    with pytest.raises(ValueError, match="капля почти неотличима от среды"):
        Simulation.check_params({**SCHEMA.defaults(), **vals})
    with pytest.raises(ValueError, match=r"\|m − 1\| < 10⁻³"):
        Simulation.check_params({**SCHEMA.defaults(), **vals, "n_re": 1.0001})
    with pytest.raises(ValueError, match="Показатель среды вокруг"):
        Harness(V, None, {**vals, "n_lam": 8})
    h = Harness(V, None, {**vals, "n_re": 1.0015, "n_lam": 8, "radius_um": 1.0})
    assert not [c["id"] for c in h.checks().values() if c.get("ok") is False]
    h = Harness(V, None, {"n_lam": 8})
    t_next = h.sim.next_event_time()
    assert t_next == pytest.approx(T_LAM)
    h.cmd("next_event")
    assert h.sim.sky_k == 1 and len(h.of("sky")) == 1
    # 1 mm drops: the nodes of one wavelength within the budget (coarse), so that a step is bounded
    big = Harness(V, None, {"radius_um": 1000.0, "n_lam": 8})
    cap = big.sim._max_nodes(380.0)
    N = mie.n_terms(float(mie.size_parameter(1000.0 * 1.08, 0.38, 1.0)))
    assert cap < MAX_NODES and cap * N * len(SKY_TH) * SKY_S_PER_UNIT <= STEP_BUDGET_S
    t0 = time.monotonic()
    big.cmd("next_event")
    assert big.sim.sky_k == 1 and time.monotonic() - t0 < 6 * STEP_BUDGET_S  # host-dependent; the old path > 120 s
    assert big.of("sky")[-1]["coarse"]
