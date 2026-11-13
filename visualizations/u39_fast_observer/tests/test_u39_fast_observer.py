# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u39: what a fast observer sees. Every preset builds, renders and passes its checks (the sky against
T / (gamma (1 - beta cos theta')), stars against the aberration formula, emission times and Doppler factors against
lorentz.retarded_time, Penrose's circle, the scene at rest against plain rays, the energy density of the sky); images
use only light already emitted and the 3-D region grows only with present positions; a live boost changes the image
at once with a continuous worldline; the comparison modes are labelled; the observer inside a body is refused with a
notice; the edges of the schema (beta 0.99, the largest image, oblique velocities); the record's growth."""

import math
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402
from lfphys.i18n import english  # noqa: E402

from lfphys.core import raytrace as RT  # noqa: E402
from u39_fast_observer import viz as V10  # noqa: E402
from u39_fast_observer.viz import SCHEMA  # noqa: E402

V = "u39_fast_observer"
C = V10.C


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def run(h, t):
    """Advance to t with an image there (images are rate-limited: one per IMG_FRAMES frames)."""
    h.sim.frames_since_img = V10.IMG_FRAMES
    h.run_to(t)
    return h


def images(h):
    return [(m, b) for m, b in h.msgs if m.get("type") == "image"]


def field(meta, blobs, name):
    raw = zlib.decompress(blobs[name].tobytes())
    H, W = meta["shape"]
    if name == "rgb":
        return np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    if name == "body":
        return np.frombuffer(raw, np.int8).reshape(H, W)
    a = np.frombuffer(raw, np.uint16).reshape(H, W)
    if meta.get("filter", {}).get(name) == "sub":
        a = np.cumsum(a.astype(np.int64), axis=1) % 65536
    return a


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_build_render_and_pass(preset):
    h = Harness(V, preset, {"res": "s"})
    for f in (5, 15, 30):
        run(h, h.sim.default_speed * f)
    assert not h.errors() and not failed(h), (h.errors(), failed(h))
    ims = images(h)
    cam = h.sim.camera()
    assert len(ims) >= 4 and all(m["shape"] == [cam.height, cam.width] for m, _ in ims)
    hdr = h.of("header")[0]
    assert hdr["scene3d"]["planes"]["max"] == 0
    meshes = h.of("mesh")
    static = [b for i, b in enumerate(h.sim.scene.bodies) if i not in h.sim.moving and b.kind != "panel"]
    panels = [b for b in h.sim.scene.bodies if b.kind == "panel"]
    assert len(meshes) == 2 * len(h.sim.moving) + len(panels) + (1 if static else 0)
    ids = set(h.checks())
    if h.sim.moving:
        assert any(i.startswith("ret_") for i in ids)
        if any(h.sim.scene.bodies[i].kind == "sphere" for i in h.sim.moving):
            assert any(i.startswith("penrose_") for i in ids)
    if preset == "rest":
        assert "rest_equal" in ids
    if preset == "sky":
        assert {"sky_T", "stars", "energy"} <= ids
    if preset == "city":
        assert "stars" in ids


def test_images_use_only_light_already_emitted():
    """Every pixel's light left its body at or before the image's time (the delay field is non-negative); the retarded
    shapes are on the observer's past light cone: |x_e - x_o| = c (t - t_e) with t_e <= t."""
    h = run(Harness(V, "terrell", {"res": "s"}), 0.0)
    for f in (10, 20, 30):
        run(h, h.sim.default_speed * f)
    for meta, blobs in images(h):
        d = field(meta, blobs, "delay")
        assert np.all(d >= 0)
        if "ret_pos" in blobs:
            ob = np.asarray(meta["observer"]["x"])
            for r in meta["retarded"]:
                xe = blobs["ret_pos"][r["from"]:r["from"] + r["count"]].astype(float)
                dist = np.linalg.norm(xe - ob, axis=1)
                body = h.sim.scene.bodies[int(r["id"][3:])]
                V_, _, _ = h.sim.meshes[int(r["id"][3:])]
                te, xe2, _ = RT.retarded_points(body, V_, RT.Observer(meta["t"], tuple(ob), (0, 0, 0)), C)
                assert np.all(te <= meta["t"]) and np.allclose(xe, xe2, atol=1e-5)
                assert np.allclose(dist, C * (meta["t"] - te), rtol=1e-6)


def test_the_region_grows_only_with_present_positions():
    """The box starts from the scene at t = 0 (bodies where they are, the observer) and grows when a present position
    nears its edge: it never frames where the bodies will be."""
    h = Harness(V, "train", {"res": "s"})
    box0 = h.of("header")[0]["scene3d"]["box"]
    sim = h.sim
    T_far = 120.0 / (0.8 * C)  # the train's centre 96 m further: beyond the first box
    x_far = RT.lab_points(sim.scene.bodies[0], np.zeros(3), T_far, C)[0]
    assert x_far > box0[1][0]
    t, step = 0.0, sim.default_speed * 2
    while t < T_far:
        t += step
        h.run_to(t)
        hi = (h.of("box")[-1]["box"] if h.of("box") else box0)[1][0]
        x_now = RT.lab_points(sim.scene.bodies[0], np.zeros(3), t, C)[0]
        assert x_now <= hi
        assert hi <= max(box0[1][0], x_now) + 2 * (box0[1][0] - box0[0][0]) * 2 ** len(h.of("box"))
    assert h.of("box")


def test_a_live_boost_changes_the_image_at_once_on_a_continuous_worldline():
    h = Harness(V, "city", {"res": "s", "obs_beta": 0.0})
    sim = h.sim
    t1 = sim.default_speed * 5
    run(h, t1)
    n0 = len(images(h))
    m0, b0 = images(h)[-1]
    x_before = sim._obs_state(t1)[0].copy()
    h.set(obs_beta=0.95)
    m1, b1 = images(h)[-1]
    assert len(images(h)) == n0 + 1 and m1["t"] == m0["t"] == t1
    D0, D1 = field(m0, b0, "D"), field(m1, b1, "D")
    assert np.array_equal(D0[D0 > 0], np.full((D0 > 0).sum(), D0[D0 > 0][0]))  # at rest: D = 1 everywhere
    assert D1.max() > D0.max() + 1000  # moving: the light ahead is blue-shifted
    x_after, u, tau, g = sim._obs_state(t1)
    assert np.allclose(x_after, x_before) and g == pytest.approx(1 / math.sqrt(1 - 0.95**2))
    run(h, 2 * t1)
    x2, _, tau2, _ = sim._obs_state(2 * t1)
    assert np.allclose(x2, x_after + u * t1) and tau2 == pytest.approx(tau + t1 / g)
    assert not failed(h)


def test_comparison_modes_are_labelled_and_snapshot_shows_contraction():
    h = run(Harness(V, "snapshot", {"res": "s"}), 0.0)
    run(h, h.sim.default_speed * 18)
    m, b = images(h)[-1]
    lab = english(m["mode_label"])
    assert m["mode"] == "snapshot" and "for comparison" in lab and "not what is seen" in lab
    # the snapshot of the cube is narrower than what is seen of it (Lorentz contraction is never seen)
    body = field(m, b, "body")
    h.set(image="seen")
    m2, b2 = images(h)[-1]
    assert m2["mode"] == "seen"
    seen = field(m2, b2, "body")
    w = lambda a: np.ptp(np.nonzero(a == 0)[1]) if (a == 0).any() else 0
    if (seen == 0).any() and (body == 0).any():
        assert w(body) < w(seen)


def test_the_observer_inside_a_body_gets_a_notice_not_an_error():
    th = math.degrees(math.atan2(5.5, 15.0))
    h = Harness(V, "city", {"res": "s", "obs_beta": 0.9, "obs_theta": th, "obs_phi": 0.0})
    t_in = 16.0 / (0.9 * C)
    for f in np.linspace(0.2, 1.3, 12):
        run(h, f * t_in)
    assert not h.errors()
    # the engine's refusal with the body's name (a tower of the street), and the world's time
    assert any("tower (" in english(m["text"]) and english(m["text"]).endswith(" ns)") for m in h.of("notice"))


@pytest.mark.parametrize("params", [{"scene": "flyby", "beta": 0.99, "res": "l"},
                                    {"scene": "sky", "obs_beta": 0.99, "camera": "sky", "res": "l", "stars": 2000},
                                    {"scene": "city", "obs_beta": 0.99, "obs_theta": 37.0, "obs_phi": 211.0,
                                     "yaw": -40.0, "pitch": 25.0, "fov": 150.0, "res": "l"}])
def test_the_edges_of_the_schema(params):
    h = Harness(V, None, params)
    for f in (3, 9, 18):
        run(h, h.sim.default_speed * f)
    assert not h.errors() and not failed(h), (h.errors(), failed(h))
    assert images(h)[-1][0]["shape"] in ([240, 320], [192, 384])


def test_the_lab_bodies_are_contracted_in_the_frames():
    h = run(Harness(V, "terrell", {"res": "s"}), 0.0)
    h.cmd("step", dt=h.sim.default_speed)
    h.runner._frame(0.0)
    f = h.of("frame")[-1]
    A = np.array(f["bodies"][0]["A"]).reshape(3, 3)
    g = 1 / math.sqrt(1 - 0.9**2)
    assert np.allclose(np.linalg.eigvalsh(A), sorted([1 / g, 1.0, 1.0]))


def test_record_growth_per_minute_of_play():
    """Images are rate-limited (one per IMG_FRAMES frames while the world runs, 20 frames per second of play): bytes per
    minute of play for the default image size, measured over a stretch of each scene; the README quotes these numbers."""
    out = {}
    for preset in ("terrell", "city", "sky", "train"):
        h = Harness(V, preset)
        sizes = []
        for f in np.linspace(2, 30, 8):
            n = len(h.msgs)
            run(h, h.sim.default_speed * f)
            sizes += [sum(x.nbytes for x in b.values()) for m, b in h.msgs[n:] if m.get("type") == "image"]
        out[preset] = np.mean(sizes) * 60 * 20 / V10.IMG_FRAMES / 2**20
    print("MB per minute of play:", {k: round(v, 2) for k, v in out.items()})
    assert max(out.values()) < 12.0, out


@pytest.mark.parametrize("preset", ["city", "terrell"])
def test_the_reported_device_is_the_images(preset):
    """Every image carries the device of its own trace (pixels × bodies), not that of the small auxiliary traces of
    stars and retarded points that follow it (review B3-8); core.backend is among the world's engine modules."""
    h = run(Harness(V, preset, {"res": "s"}), 0.0)
    run(h, h.sim.default_speed * 10)
    cam = h.sim.camera()
    for meta, _ in images(h):
        assert meta["device"]["size"] == cam.height * cam.width * max(1, len(h.sim.scene.bodies))
    assert "core.backend" in h.sim.engine_modules()


# --- the record's world is the same however fast the wall clock ran (review C1-6) ----------------------------------
def _same_exactly(a, b, path=""):
    if isinstance(a, dict):
        assert set(a) == set(b), (path, set(a) ^ set(b))
        for k in a:
            if k not in ("cpu_ms", "speed_actual", "lag"):  # the runner's measurements of the wall clock
                _same_exactly(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _same_exactly(x, y, f"{path}[{i}]")
    elif isinstance(a, np.ndarray):
        assert a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b, equal_nan=a.dtype.kind in "fc"), path
    elif isinstance(a, float):
        assert a == b or (math.isnan(a) and math.isnan(b)), (path, a, b)
    else:
        assert a == b, (path, a, b)


def _messages_under_clock(monkeypatch, wall_step, frames=30):
    """Every message of a world driven through the same frames (a live change in the middle), with ``wall_step``
    seconds of wall time passing at every read of the clock (0: a frozen clock, as a world rebuilt from its record in
    a burst sees it)."""
    import time
    clock = [1e4]

    def now():
        clock[0] += wall_step
        return clock[0]
    with monkeypatch.context() as mp:
        for name in ("monotonic", "time", "perf_counter"):
            mp.setattr(time, name, now)
        h = Harness(V, "terrell", params={"res": "s"})
        step = h.sim.default_speed / 20
        for k in range(1, frames + 1):
            if k == frames // 2:
                h.set(obs_beta=0.3)
            h.run_to(k * step)
            h.runner._frame(0.0)
    return h.msgs


def test_the_images_do_not_depend_on_the_wall_clock(monkeypatch):
    """C1-6: images were rendered every 0.35 s of wall time, so a world continued from its record (its frames replayed
    in a burst) rendered other images at other times, with other numbers and heavy checks; now every IMG_FRAMES
    frames."""
    a = _messages_under_clock(monkeypatch, 0.0)
    b = _messages_under_clock(monkeypatch, 0.5)
    assert [m["type"] for m, _ in a] == [m["type"] for m, _ in b]
    imgs = [m for m, _ in a if m["type"] == "image"]
    assert len(imgs) >= 4 and len({m["seq"] for m in imgs}) == len(imgs)
    for (ma, ba), (mb, bb) in zip(a, b):
        _same_exactly(ma, mb, ma["type"])
        _same_exactly(ba or {}, bb or {}, ma["type"])
