# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v08: the 3-D scene (owner, 2026-10-27), slice planes of any orientation placed by view commands (they stay where
they are put; moving by themselves is an option), the modelling modes, the flagged approximation, the measured
accuracy (the window and every slice against the exact field), the energy current, fp32 drawing, the devices."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import backend  # noqa: E402
from v08_wave_3d.engine import apparatus as A  # noqa: E402
from v08_wave_3d.viz import SCHEMA, Simulation  # noqa: E402

V = "v08_wave_3d"
SMALL = {"n": 128, "zmax": 10.0}  # a world that builds in seconds on one CPU thread


@pytest.fixture(autouse=True)
def _defaults():
    backend.configure(None)
    yield
    backend.configure(None)


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def plane(h, pid, **kw):
    h.cmd("view", op="plane", id=pid, **kw)
    return h.of("slice")[-1]


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_build_and_checks_pass(preset):
    h = Harness(V, preset)
    assert not h.errors() and not failed(h), (h.errors(), failed(h))
    hdr = h.of("header")[0]
    sc = hdr["scene3d"]
    kinds = {o["kind"] for o in sc["objects"]}
    assert {"incident", "target"} <= kinds and kinds & {"plate", "disk"}
    assert h.of("target") and h.of("planes") and h.of("slice")
    assert (len(h.of("volume")) == 1) == (hdr["modelling"]["mode"] == "full3d")
    used = hdr["backend"]["used"]["optics.angular_spectrum"]
    assert hdr["accuracy"]["window"] <= A.TOL and used["check"]["precision"] == "fp64"
    # a world whose only slice is the reduced model (fp64) has drawn nothing by the kernel yet
    assert ("drawn" in used) == (preset != "double_slices")
    ids = set(h.checks())
    assert "window" in ids and any(i.startswith("exact_") for i in ids) and "slice_route" in ids


def test_planes_stay_where_they_are_put_and_auto_is_an_option():
    """Owner, 2026-10-27: a slice does not move by itself; automatic shifting is an option, off by default."""
    h = Harness(V, "double", SMALL)
    n0 = len(h.of("slice"))
    h.cmd("play")
    h.run_to(5.0)
    assert len(h.of("slice")) == n0 and h.of("planes")[-1]["planes"][0]["auto"] is False
    plane(h, 1, auto=True, speed=1.0)
    o0 = h.of("planes")[-1]["planes"][0]["origin"]
    h.run_to(8.0)
    o1 = h.of("planes")[-1]["planes"][0]["origin"]
    assert len(h.of("slice")) > n0 + 1 and o1 != o0 and abs(o1[1] - o0[1]) > 0  # moved along its normal (y)
    assert o1[0] == pytest.approx(o0[0]) and o1[2] == pytest.approx(o0[2])


def test_planes_of_any_orientation_up_to_three_each_checked_against_the_exact_field():
    h = Harness(V, "double", SMALL)
    s = plane(h, 2, origin=[0.3, -0.4, 4.0], normal=[0.4, 0.3, 0.86])
    assert s["id"] == 2 and s["exact"] and s["verify"]["points"] == 3 and s["verify"]["ok"]
    assert s["label"] == "произвольная плоскость" and len(h.of("planes")[-1]["planes"]) == 2
    s = plane(h, 3, normal=[0.0, 0.0, 1.0], origin=[0.0, 0.0, 6.0])
    assert s["label"] == "z = 6" and s["verify"]["ok"]
    n_err = len(h.errors())
    h.cmd("view", op="plane", id=4, normal=[1, 0, 0])
    assert len(h.errors()) == n_err + 1 and "трёх" in h.errors()[-1]
    h.cmd("view", op="remove", id=2)
    assert [p["id"] for p in h.of("planes")[-1]["planes"]] == [1, 3]
    # a plane through the axis at azimuth 30 degrees: labelled and exact
    s = plane(h, 2, origin=[0.0, 0.0, 5.0], normal=[-math.sin(math.radians(30)), math.cos(math.radians(30)), 0.0])
    assert s["label"] == "через ось z, φ = 30°"
    # every grid point of the slice lies on its plane and inside the computed region (else NaN)
    sl = h.sim.slices[2]
    P = A.slice_points(sl["plane"], sl["s"], sl["t"])
    assert np.allclose((P - np.asarray(sl["plane"].origin)) @ sl["plane"].normal, 0.0, atol=1e-12)
    inside = A.inside_box(P, h.sim.box)
    assert np.all(np.isfinite(sl["U"][inside])) and np.all(np.isnan(sl["U"][~inside]))
    assert not failed(h)


def test_a_slice_equals_the_volume_on_its_grid_points():
    """In full 3-D the slice route and the volume give the same field where the slice's points are grid nodes of the
    volume (the plane y = c through a grid row, at the volume's z planes)."""
    h = Harness(V, "double", SMALL)
    sim = h.sim
    j = sim.n // 2 + 5
    zs = sim.zs
    pl = A.plane_box((0.0, float(sim.x[j]), zs[48]), (0.0, -1.0, 0.0), sim.box)[0]
    from lfphys.core.optics import angular_spectrum as AS
    s, U = AS.propagate_plane(sim.src, sim.dx, sim.k, pl, (float(sim.x[0]), float(sim.x[-1])),
                              np.asarray(zs) - zs[48], **sim.kw)
    idx = np.rint(s / sim.dx).astype(int) + sim.n // 2
    assert np.max(np.abs(U - sim.vol[:, idx, j])) < 1e-12 * np.max(np.abs(sim.vol))


def test_slices_mode_computes_only_the_planes_and_flags_the_approximate_one():
    h = Harness(V, "double_slices", SMALL)
    hdr = h.of("header")[0]
    assert not h.of("volume") and hdr["modelling"]["mode"] == "slices"
    assert hdr["approximations"] and hdr["approximations"][0].startswith("срез y = 0:")
    s = h.of("slice")[-1]
    assert s["approximation"] and s["route"] == "reduced" and "ПРИБЛИЖЕНИЕ" in s["route_label"]
    assert h.checks()["reduced"].get("info")
    s = plane(h, 2, normal=[1.0, 0.0, 0.0])
    assert s["exact"] and not s["approximation"]
    m = h.of("modelling")[-1]
    assert [p["exact"] for p in m["modelling"]["planes"]] == [False, True] and len(m["approximations"]) == 1
    h.cmd("view", op="remove", id=1)
    assert h.of("modelling")[-1]["approximations"] == []


def test_reduced_model_error_is_measured_and_shrinks_with_the_slit_length():
    errs = []
    for L in (4.0, 12.0, 24.0):
        h = Harness(V, "double_slices", {"L": L, "a": 0.5, "zmax": 12.0, "n": 128})
        c = h.checks()["reduced"]
        assert c.get("info") and "ПРИБЛИЖЕНИЕ" in c["label"]
        errs.append(c["value"])
    assert errs[0] > errs[1] > errs[2] > 0


def test_energy_current_is_sent_with_its_checks():
    h = Harness(V, "double", SMALL)
    v = h.of("vectors")[0]
    assert v["count"] > 0 and h.checks()["flux_exact"]["ok"] and h.checks()["flux"].get("info")


@pytest.mark.parametrize("params", [
    {"source": "double", "lam": 0.5, "a": 0.4, "d": 3.0, "L": 6.0, "zmax": 8.0},
    {"source": "square", "lam": 1.0, "a": 1.0, "zmax": 30.0},
    {"source": "slit", "lam": 0.6, "a": 1.5, "L": 10.0, "zmax": 15.0},
])
def test_window_estimate_bounds_the_true_error(params):
    """The calibration of apparatus.SAFETY over depth (reviews B1-1, C1): with the chosen window, the field on z_max
    and on the central planes y = 0, x = 0 at the measured depths differs from the exact field (no FFTs) by less than
    the estimate."""
    p = {**SCHEMA.defaults(), **params, "n": 128}
    k, n = 2 * math.pi / p["lam"], 128
    dx = p["lam"] / 4
    x = (np.arange(n) - n // 2) * dx
    src = A.source(p, n)
    win = A.choose_window(src, dx, k, p["zmax"])
    zs = A.check_depths(dx, k, p["zmax"])
    plane, sy, sx = A._measured(src, dx, k, p["zmax"], zs, win.pad, win.band_limit)
    pk = [float(np.max(np.abs(c))) for c in (plane, sy, sx)]  # each plane against its own peak (review C1)
    for i in (n // 2, n // 2 + 9, n // 2 + 30, n - 1, 5):
        for j in (n // 2, n // 2 + 17, n - 3):
            ref = A.reference(p, k, p["zmax"], x[i], x[j])[0]
            assert abs(plane[i, j] - ref) <= win.est * pk[0] and abs(plane[i, j] - ref) <= win.abs_err, (i, j)
        for iz in range(0, len(zs), 3):
            assert abs(sy[iz, i] - A.reference(p, k, zs[iz], x[i], 0.0)[0]) <= win.est * pk[1], ("y0", iz, i)
            assert abs(sx[iz, i] - A.reference(p, k, zs[iz], 0.0, x[i])[0]) <= win.est * pk[2], ("x0", iz, i)


def test_the_circle_preset_is_within_its_estimate_at_every_depth():
    """Review C1: the circle preset picked the band-limited sum, exact on z_max but 3.8e-3 off at mid-depth; the
    estimate over depth now picks a window whose error on the axis stays within it at all depths."""
    h = Harness(V, "circle")
    sim = h.sim
    zs = np.linspace(sim.z_near * 2, sim.zmax, 40)
    from lfphys.core.optics import angular_spectrum as AS
    U = AS.propagate_slice(sim.src, sim.dx, sim.k, zs, axis=1, at=0.0, check=True, **sim.kw)[:, sim.n // 2]
    ref = np.array([A.reference(sim.params, sim.k, z, 0.0, 0.0)[0] for z in zs])
    assert np.max(np.abs(U - ref)) <= sim.win.abs_err and sim.win.est <= A.TOL


def test_a_world_whose_window_is_not_enough_is_refused():
    p = SCHEMA.resolve(None, {"source": "double", "lam": 1.5, "a": 0.2, "zmax": 80.0, "n": 128})[0]
    with pytest.raises(ValueError, match="окно расчёта мало"):
        Simulation(p, 1, lambda *a: None)


def test_fp32_drawing_keeps_every_check_passing():
    backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu", "precision": "fp32"}}})
    for preset in ("double", "double_slices"):
        h = Harness(V, preset, SMALL)
        assert not failed(h), failed(h)
        if preset == "double":
            assert h.checks()["fp32"]["ok"] and h.checks()["fp32"]["value"] > 1e-9
        if preset == "double_slices":
            plane(h, 2, normal=[1.0, 0.0, 0.0])  # an exact slice: drawn by the kernel in fp32
            assert not failed(h), failed(h)
            continue
        used = h.of("header")[0]["backend"]["used"]["optics.angular_spectrum"]
        assert used["drawn"]["precision"] == "fp32" and used["check"]["precision"] == "fp64"


@pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="no GPU given to this container")
def test_the_gpu_gives_the_same_world():
    backend.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
    hg = Harness(V, "double", SMALL)
    sg = plane(hg, 2, origin=[0.3, -0.4, 4.0], normal=[0.4, 0.3, 0.86])
    assert hg.of("header")[0]["backend"]["used"]["optics.angular_spectrum"]["drawn"]["device"] == "gpu"
    assert not failed(hg)
    backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
    hc = Harness(V, "double", SMALL)
    plane(hc, 2, origin=[0.3, -0.4, 4.0], normal=[0.4, 0.3, 0.86])
    assert np.max(np.abs(hg.sim.vol - hc.sim.vol)) < 1e-12 * np.max(np.abs(hc.sim.vol))
    a, b = hg.sim.slices[2]["U"], hc.sim.slices[2]["U"]
    assert np.nanmax(np.abs(a - b)) < 1e-12 * np.nanmax(np.abs(b)) and sg["verify"]["ok"]


def test_a_dragged_plane_in_slices_mode_gets_a_coarse_preview_that_changes_nothing():
    h = Harness(V, "double_slices", SMALL)
    n_planes = len(h.of("planes"))
    before = dict(h.sim.planes[1])
    h.cmd("view", op="preview", id=1, origin=[0.0, 1.0, 5.0], normal=[0.0, -1.0, 0.2])
    s = h.of("slice")[-1]
    assert s["preview"] and s["shape"][0] == 48 and "verify" not in s
    assert len(h.of("planes")) == n_planes and h.sim.planes[1]["origin"] == before["origin"]


def test_a_tilted_plane_moves_uniformly_with_auto_and_an_outside_centre_keeps_its_plane():
    """Review C3: the plane's point is the one closest to (0, 0, z_max/2), never clipped off the plane."""
    h = Harness(V, "double", SMALL)
    n = np.array([1.0, 0.0, 1.0]) / math.sqrt(2)
    plane(h, 2, origin=[6.0, 0.0, 5.0], normal=list(n))  # o.n = 7.78: inside the box's range; the point is outside
    p2 = h.sim.planes[2]
    assert float(np.asarray(p2["origin"]) @ n) == pytest.approx((6.0 + 5.0) / math.sqrt(2))
    plane(h, 2, auto=True, speed=1.0)
    d = [float(np.asarray(h.sim.planes[2]["origin"]) @ n)]
    t = 0.0
    for _ in range(12):
        t += 1.0
        h.run_to(t)
        d.append(float(np.asarray(h.sim.planes[2]["origin"]) @ n))
    steps = np.diff(d)
    steps = steps[steps > 0]  # wraps excluded
    assert len(steps) >= 6 and np.allclose(steps, steps[0], rtol=0.35), steps


def test_auto_moving_slices_are_coarse_and_rate_limited_and_the_full_slice_returns():
    """Review C6: the record of an auto-moving plane."""
    h = Harness(V, "double", SMALL)
    plane(h, 1, auto=True, speed=2.0)
    n0 = len(h.of("slice"))
    for t in np.arange(0.25, 10.01, 0.25):
        h.run_to(float(t))
    moving = h.of("slice")[n0:]
    assert moving and all(m["coarse"] and m["shape"][0] == 64 for m in moving)
    assert len(moving) <= 21  # at most twice per world second
    s = plane(h, 1, auto=False)
    assert not s["coarse"] and s["shape"][0] == A.NT and s["verify"]["ok"]


def test_planes_carry_over_to_a_new_world_and_reset_restores_the_default():
    """Review C7: the planes the experimenter placed survive a new world of the run."""
    h = Harness(V, "double", SMALL)
    plane(h, 2, origin=[0.0, 0.0, 4.0], normal=[0.3, 0.2, 0.93])
    h.cmd("new_world", params={**SMALL, "lam": 0.6})
    planes = h.of("planes")[-1]["planes"]
    assert [p["id"] for p in planes] == [1, 2] and h.sim.lam == pytest.approx(0.6)
    assert planes[1]["normal"] == pytest.approx(list(np.array([0.3, 0.2, 0.93]) / np.linalg.norm([0.3, 0.2, 0.93])))
    h.cmd("view", op="reset")
    assert [p["id"] for p in h.of("planes")[-1]["planes"]] == [1]


def test_each_plane_has_its_own_check_and_labels_follow_the_normal():
    """Reviews C8, C11."""
    h = Harness(V, "double", SMALL)
    plane(h, 2, normal=[0.0, 1.0, 0.0], origin=[0.0, 1.0, 5.0])
    assert h.sim.planes[2]["label"] == "y = 1"  # the normal +y (not only -y) names the coordinate plane
    plane(h, 3, normal=[0.2, 0.1, 0.97], origin=[0.0, 0.0, 6.0])
    ids = set(h.checks())
    assert {"plane_exact_1", "plane_exact_2", "plane_exact_3"} <= ids
    h.cmd("view", op="remove", id=3)
    c = h.checks()["plane_exact_3"]
    assert c.get("info") and "убран" in c["label"]


def test_the_current_is_checked_against_the_exact_current():
    """Review C4: the current at the reference points of z_max against the exact field's derivatives; the power
    identity is information."""
    for preset in ("double", "circle", "gauss"):
        h = Harness(V, preset, SMALL)
        c = h.checks()
        assert c["flux_exact"]["ok"] and c["flux"].get("info"), preset



def test_a_refused_window_says_what_to_change_with_a_working_example(monkeypatch):
    """Review UX-params P26 (partly): «Круглое отверстие» with the other defaults is refused after the window search
    (11 s on GPU 0, 90 s on the CPU; response_checks_v-worlds/v08_gpu.out). The refusal now says what to change and
    names the scenario that works for that source; the search itself is unchanged (an early refusal by extrapolating
    the measured errors was tried and rejected: one doubling of the window cut the plain sum's error 10-fold at
    z_max = 80 µm, so no extrapolation is safe)."""
    def refuse(*a, **k):
        raise ValueError("окно расчёта мало для глубины z_max = 30 мкм: …, а нужно ≤ 2e-03. Уменьшите z_max или "
                         "возьмите источник шире (свет уходит под меньшими углами)")
    monkeypatch.setattr(A, "choose_window", refuse)
    p = SCHEMA.resolve(None, {"source": "circle"})[0]
    with pytest.raises(ValueError) as e:
        Simulation(p, 1, lambda *a: None)
    text = str(e.value)
    assert "Что изменить: уменьшите z_max" in text and "«Круглое отверстие» (a = 3 мкм, z_max = 40 мкм)" in text
