# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v15: the shadow of a Kerr black hole. Every preset builds and passes its checks; the image is revealed row by row
only as the world's time reaches the rows; the pixels sent are the engine's (captured pixels, the order n images, g^4
J); a live change of the set-up starts a new image at once; a "what if" world computes the deviating metric's shadow
edge and its size against EHT, and refuses a metric that is not regular outside the horizon."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.gravity import kerr, kerr_null as KN, kerr_shadow as KS  # noqa: E402
from lfphys.theories.alternatives import johannsen_metric as JP  # noqa: E402
from v15_kerr_shadow.viz import SCAN_M, SCHEMA  # noqa: E402

V = "v15_kerr_shadow"
SMALL = {"res": "s"}


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def rows(h, seq=None):
    """The image sent so far: captured flags and the summed brightness, decoded as the browser does."""
    out = {}
    for m, b in h.msgs:
        if m.get("type") != "rows" or (seq is not None and m["seq"] != seq):
            continue
        nx, nr, nm = m["nx"], m["i1"] - m["i0"], m["n_max"] + 1
        cap = np.asarray(b["cap"]).reshape(nr, nx)
        I = np.asarray(b["I"]).reshape(nm, nr, nx)
        for k in range(nr):
            out[m["i0"] + k] = (cap[k], I[:, k])
    return out


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_builds_and_passes_its_checks(preset):
    h = Harness(V, preset, SMALL)
    h.run_to(SCAN_M * 1.01)
    assert not h.errors(), h.errors()
    assert not failed(h), failed(h)
    if h.sim.image is not None:
        assert h.sim.image.done and "pixels" in h.checks()


def test_the_image_is_revealed_only_as_the_worlds_time_reaches_its_rows():
    h = Harness(V, "m87", SMALL)
    ny = h.sim.image.screen.ny
    assert len(rows(h)) <= 1
    h.run_to(0.5 * SCAN_M)
    n_half = len(rows(h))
    assert 0.45 * ny <= n_half <= 0.55 * ny + 1
    h.run_to(SCAN_M * 1.01)
    assert len(rows(h)) == ny


def test_the_pixels_sent_are_the_engines():
    """A row of the image against the engine's tracer called directly: the same captured pixels and brightness."""
    h = Harness(V, "ring", SMALL)
    h.run_to(SCAN_M * 1.01)
    sc = h.sim.image.screen
    j = sc.ny // 2 + 3
    a, b = sc.rows(j, j + 1)
    res = KS.trace_screen(a, b, h.sim.theta_o, h.sim.chi, 2, "cunningham", True)
    cap, I = rows(h)[j]
    assert np.array_equal(cap, res["captured"][0].astype(np.uint8))
    J = h.sim._J(res["r_n"][:, 0])
    ref = np.where(np.isfinite(res["g_n"][:, 0]), np.nan_to_num(res["g_n"][:, 0]) ** 4 * J, 0.0)
    assert np.allclose(I, ref.astype(np.float32), rtol=0, atol=0)
    # the narrow ring is seen: some pixels of the row light up through the direct image and the lensing ring
    assert (I[0] > 0).any() and (I[1] > 0).any()


def test_a_live_change_starts_a_new_image_at_once():
    h = Harness(V, "m87", SMALL)
    h.run_to(SCAN_M * 1.01)
    seq = h.sim.seq
    h.set(incl=60.0)
    assert h.sim.seq == seq + 1 and h.sim.image.next_row <= 1
    curves = h.of("curve")
    assert curves[-1]["seq"] == seq + 1
    h.run_to(h.sim.t + SCAN_M * 1.01)
    assert h.sim.image.done and not failed(h)
    assert len(rows(h, seq + 1)) == h.sim.image.screen.ny


def test_the_shadow_edge_against_bardeen_and_the_schwarzschild_radius():
    h = Harness(V, "schwarzschild", SMALL)
    h.run_to(SCAN_M * 1.01)
    c = h.checks()
    assert c["edge"]["ok"] and c["edge"]["value"] <= c["edge"]["tol"]
    assert c["schw"]["ok"] and abs(c["schw"]["value"] - math.sqrt(27.0)) <= c["schw"]["tol"] * math.sqrt(27.0)
    assert c["size"]["ok"] and abs(c["size"]["value"]) <= 1e-12  # a = 0: the traced shadow is the circle sqrt 27


def test_the_checks_come_when_the_image_is_complete():
    """Review B5-K10: the run's measurements and their closed-form references are posted when the scan completes,
    not when it starts; the size is measured on the tracer's edge and agrees with the closed form."""
    h = Harness(V, "m87", SMALL)
    h.run_to(0.9 * SCAN_M)
    assert not {"edge", "lyapunov", "size", "eht", "pixels"} & set(h.checks())
    h.run_to(SCAN_M * 1.01)
    c = h.checks()
    assert {"edge", "lyapunov", "size", "eht", "pixels"} <= set(c)
    assert all(c[k]["t"] >= SCAN_M for k in ("edge", "size", "eht"))
    assert c["size"]["ok"] and abs(c["size"]["value"] - c["size"]["ref"]) <= 1e-12
    ref = KS.shadow_size(0.9, math.radians(163.0))
    assert c["size"]["value"] == ref["delta"]


def test_edge_and_pixels_are_held_to_derived_bounds():
    """Review B5-K1: a = 0.998 at 81 deg failed the old fixed 64 eps; the derived per-direction bound passes it.
    Review B5-K16: pixels are compared up to the drawn curve's sag (~1e-4 M), not sqrt 2 pixels."""
    h = Harness(V, None, {"chi": 0.998, "incl": 81.0, **SMALL})
    h.run_to(SCAN_M * 1.01)
    c = h.checks()
    assert c["edge"]["ok"] and c["edge"]["value"] <= c["edge"]["tol"] < 1e-12
    assert c["pixels"]["ok"]
    margin = float(c["pixels"]["note"].split("дальше ")[1].split(" M")[0].replace(",", "."))
    assert margin < 1e-3


def test_m87_against_eht_in_its_own_definition():
    """Review B5-K4: M87*'s 2019 delta is the deviation from Kerr (every Kerr hole has 0 there); a what-if world's
    delta - delta_Kerr is held to +-0.17 (Psaltis et al. 2020), the module's interval; Sgr A* bounds the size itself."""
    h = Harness(V, "m87", SMALL)
    h.run_to(SCAN_M * 1.01)
    e = h.checks()["eht"]
    assert e["value"] == 0.0 and e["ok"] and e["tol"] == 0.17
    w = Harness(V, None, {"metric": "jp", "a13": 5.6, "chi": 0.0, "incl": 17.0, **SMALL})
    d = JP.delta_vs_kerr(0.0, math.radians(17.0), JP.Deviation(alpha13=5.6))
    e = w.checks()["eht"]
    assert e["value"] == pytest.approx(d, abs=1e-12) and 0.15 < d < 0.17 and e["ok"]  # inside, as Psaltis's bound
    g = Harness(V, "sgra", SMALL)
    g.run_to(SCAN_M * 1.01)
    e = g.checks()["eht"]
    assert e["value"] == g.checks()["size"]["value"] and e["ok"]


def test_a_what_if_world_shows_its_own_orbits_and_ergosphere():
    """Review B5-K7: the deviating metric's photon orbits and ISCO (johannsen_metric.circular_orbits), Kerr's for
    comparison; its ergosphere from g_tt = 0."""
    h = Harness(V, "whatif", SMALL)
    hole = h.of("header")[-1]["hole"]
    o = JP.circular_orbits(0.0, JP.Deviation(alpha13=3.0))
    assert hole["ph_pro"] == o["photon_pro"] and hole["isco_pro"] == o["isco_pro"]
    assert abs(hole["ph_pro"] - 3.3005) < 1e-4 and abs(hole["isco_pro"] - 7.1646) < 1e-4
    assert hole["kerr"]["ph_pro"] == 3.0 and hole["kerr"]["isco_pro"] == pytest.approx(6.0, abs=1e-12)
    rings = [b for m, b in h.msgs if m.get("type") == "lines" and m["id"] == "orbits"][-1]["pts"].reshape(-1, 3)
    r = np.hypot(rings[:, 0], rings[:, 1])
    assert np.nanmax(np.abs(r[np.isfinite(r)][:181] - o["photon_pro"])) < 1e-5  # float32 drawing coordinates
    k = Harness(V, "m87", SMALL).of("header")[-1]["hole"]
    assert k["kerr"] is None and k["ph_pro"] == kerr.photon_orbit(0.9, True)


def test_the_views_look_from_the_directions_they_name():
    """Review B5-K8: the spin axis up; the observer's view along the observer's arrow."""
    sc = Harness(V, "m87", SMALL).of("header")[-1]["scene3d"]
    assert sc["up"] == [0.0, 0.0, 1.0]
    views = {v[0]: v for v in sc["views"]}
    assert views["obs"][3] == {"along": "observer"} and views["pole"][3] == [0.0, 0.0, 1.0]
    assert views["side"][3][2] == 0.0  # perpendicular to the spin: the disk edge-on


def test_a_what_if_world_computes_the_edge_and_refuses_an_irregular_metric():
    h = Harness(V, "whatif", SMALL)
    assert h.sim.image is None and "eht" in h.checks()
    header = h.of("header")[-1]
    assert [m["id"] for m in header["modifications"]] == ["metric", "a13"]  # flagged as modified physics
    assert Harness(V, "m87", SMALL).of("header")[-1]["modifications"] == []
    d_dev, d_kerr = h.checks()["eht"]["value"], h.checks()["eht_kerr"]["value"]
    assert abs(d_kerr) <= 1e-15 and d_dev > 0.05  # alpha13 = 3 makes the shadow larger than Kerr's
    with pytest.raises(ValueError, match="не регулярна"):
        Harness(V, None, {"metric": "jp", "a13": -10.0, "chi": 0.0, **SMALL})


def test_rays_and_scene():
    h = Harness(V, "edge_on", SMALL)
    lines = {m["id"]: (m, b) for m, b in h.msgs if m.get("type") == "lines"}
    assert "rays" in lines and "orbits" in lines
    pts = lines["rays"][1]["pts"].reshape(-1, 3)
    assert np.isfinite(pts).sum() > 3 * 100
    meshes = {m["id"] for m in h.of("mesh")}
    assert {"horizon", "ergo", "disk"} <= meshes
    # the horizon's points lie on r = r+ (kerr_null.cartesian of the Boyer-Lindquist sphere)
    hz = [b for m, b in h.msgs if m.get("type") == "mesh" and m["id"] == "horizon"][0]["pos"].reshape(-1, 3)
    rp = h.sim.r_plus
    x, y, z = hz.T.astype(float)
    rho2 = x * x + y * y
    # r^4 - r^2 (rho^2 + z^2 - a^2) - a^2 z^2 = 0 for the oblate coordinates of kerr_null.cartesian
    a2 = h.sim.chi ** 2
    resid = rp ** 4 - rp ** 2 * (rho2 + z * z - a2) - a2 * z * z
    assert np.max(np.abs(resid)) < 1e-4 * rp ** 4


def test_refusals_of_the_what_if_metric_name_the_values_it_takes():
    """Review UX-params P6 / UX-ui U13: an irregular metric or one without a single photon shell was refused in English
    («the metric is not regular…», «the photon shell is not a single band…»). Now the refusal is Russian, names what
    fails and, for each deviation (the others as they are), the values the world takes; a value inside the named
    interval builds, one just outside is refused (the interval's end is the edge, within the bisection's 1e-4)."""
    import re
    cases = [({"metric": "jp", "a13": -10.0}, "не регулярна", "α₁₃ — от "),
             ({"metric": "jp", "a22": 10.0}, "det g обращается в нуль", "α₂₂ — от "),
             ({"metric": "jp", "a13": 10.0, "chi": 0.998}, "не образуют одну полосу", "α₁₃ — от ")]
    for vals, what, tip in cases:
        with pytest.raises(ValueError) as e:
            Harness(V, None, {**vals, **SMALL})
        text = str(e.value)
        assert what in text and tip in text and not re.search(r"[A-Za-z]{4,}", text.replace("Johannsen", "")), text
        pid = {"α₁₃": "a13", "α₂₂": "a22"}[tip[:3]]
        lo, hi = (float(x.replace("−", "-")) for x in re.search(tip + r"(\S+) до (\S+?)[;,]", text).groups())
        inside = 0.5 * (lo + hi)
        Harness(V, None, {**vals, pid: inside, **SMALL})  # builds
        edge = hi if abs(vals[pid] - hi) < abs(vals[pid] - lo) else lo
        beyond = edge + (2e-3 if edge == hi else -2e-3) * max(1.0, abs(edge))
        if SCHEMA.by_id[pid].min <= beyond <= SCHEMA.by_id[pid].max:
            with pytest.raises(ValueError):
                Harness(V, None, {**vals, pid: beyond, **SMALL})
    # the help's numbers next to the sliders are the engine's intervals (a = 0.9, the other deviations zero)
    for pid, key, ref in (("a13", "alpha13", (-2.11, 10.0)), ("a22", "alpha22", (-2.06, 5.13)),
                          ("a12", "alpha12", (-1.47, 10.0))):
        (a, b), = JP.admissible_intervals(0.9, key, {}, SCHEMA.by_id[pid].min, SCHEMA.by_id[pid].max)
        assert a == pytest.approx(ref[0], abs=6e-3) and b == pytest.approx(ref[1], abs=6e-3)
        h = SCHEMA.by_id[pid].help.replace(",", ".").replace("−", "-")
        assert f"{ref[0]:.2f}" in h


def test_a_what_if_metric_with_a_band_without_circular_orbits_builds():
    """Review UX-params P6: alpha12 = -3, alpha13 = -1.399, alpha22 = 3.612 at a = 0 (the preset «whatif» edited) has
    no circular geodesics between 2.1 M and 4.6 M (Omega^2 < 0); the ISCO search took a complex E and float() crashed
    the world (TypeError). Now the world builds; its ISCO is the outer edge of that band, where g_tt' = 0 (a static
    orbit): checked against a 40-digit root of g_tt'(r) = 0 and E = sqrt(-g_tt) there (a second route)."""
    import mpmath as mp
    h = Harness(V, "whatif", {"a13": -1.399, "a22": 3.612, "a12": -3.0, **SMALL})
    assert not h.errors()
    hole = h.of("header")[-1]["hole"]
    assert hole["isco_kind"] == "existence"
    with mp.workdps(40):
        gtt = lambda r: -(1 - 2 / r) / (1 + mp.mpf(-3) / r ** 2 + mp.mpf("-1.399") / r ** 3) ** 2  # noqa: E731
        r0 = mp.findroot(lambda r: mp.diff(gtt, r), 4.6)
        e0 = mp.sqrt(-gtt(r0))
    assert hole["isco_pro"] == pytest.approx(float(r0), rel=1e-12)
    co = JP.circular_orbits(0.0, JP.Deviation(-3.0, -1.399, 3.612))
    assert co["E_isco_pro"] == pytest.approx(float(e0), rel=1e-12) and co["L_isco_pro"] == 0.0
    assert "края области" in " ".join(m.get("label", "") for m in h.of("lines")) or \
        "край области" in " ".join(m.get("label", "") for m in h.of("lines"))
