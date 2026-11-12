# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P9 / P14.2: light-time ray tracing (lfphys.core.raytrace) against closed forms and independent routes.

Tolerances: every quantity passes through a few 4 x 4 boosts whose entries reach gamma, and through products of two
of them, so its round-off is a small multiple of eps gamma^2 (per boost involved); the bounds below are 16 to 64 eps
times those factors, with the measured values (2026-10-28) quoted where they matter."""

import math

import numpy as np
import pytest

from lfphys.core import backend as B
from lfphys.core import lorentz as LZ
from lfphys.core import raytrace as RT

EPS = np.finfo(float).eps


def g2(*vs):
    out = 1.0
    for v in vs:
        out *= float(LZ.gamma_of(np.asarray(v, float))) ** 2
    return out


def ang(a, b):
    return np.arctan2(np.linalg.norm(np.cross(a, b), axis=-1), np.sum(a * b, -1))


@pytest.fixture(autouse=True)
def _cpu():
    B.configure(None)
    yield
    B.configure(None)


def unit(v, beta):
    v = np.asarray(v, float)
    return tuple(beta * v / np.linalg.norm(v))


def test_at_rest_the_tracer_is_plain_ray_casting():
    """Velocities zero: no aberration, no light-time difference — the same image and distances as plain rays."""
    sc = RT.Scene([RT.Sphere((0, 0, 6), 1.0), RT.Box((2.5, 0.3, 7), (0.5, 0.6, 0.7)),
                   RT.Panel((0, -1.5, 0), half=(10, 10))], sky=3000.0)
    cam = RT.Camera(160, 120, fov=100)
    r = RT.render(sc, RT.Observer(2.0, (0, 0, 0)), cam)
    who, s = RT.static_render(sc, (0, 0, 0), cam.directions())
    assert np.array_equal(np.where(r["body"] >= 0, r["body"], -1), who)
    f = np.isfinite(s)
    assert f.sum() > 3000 and set(np.unique(who)) == {-1, 0, 1, 2}
    assert np.max(np.abs(r["s"][f] - s[f]) / s[f]) <= 4 * EPS
    assert np.allclose(r["D"][f], 1.0, rtol=0, atol=4 * EPS) and np.all(r["t_emit"][f] == 2.0 - r["s"][f])


@pytest.mark.parametrize("beta", [1e-9, 0.3, 0.9, 0.99, 0.999])
def test_the_sky_is_a_black_body_at_D_T_in_every_direction(beta):
    """A uniform black-body sky at rest in the lab seen by a moving observer: T / (gamma (1 - beta cos theta')) in every
    pixel (the dipole of the cosmic background). Measured: <= 2.7 eps gamma^2."""
    u = unit((0.3, 0.5, 0.81), beta)
    cam = RT.Camera(128, 64, kind="sky", forward=(0.2, 0.1, 1.0))
    r = RT.render(RT.Scene([], sky=2.725), RT.Observer(0.0, (0, 0, 0), u), cam)
    ref = RT.ref_sky_temperature(2.725, u, cam.directions())
    assert np.all(r["body"] == -1) and np.all(np.isinf(r["s"]))
    assert np.max(np.abs(r["T_obs"] / ref - 1)) <= 16 * EPS * g2(u)


@pytest.mark.parametrize("beta", [0.3, 0.9, 0.99])
def test_the_energy_density_seen_moving_is_gamma2_1_plus_beta2_over_3(beta):
    """(1/4 pi) int (T'/T)^4 dOmega' = gamma^2 (1 + beta^2/3) (the searchlight integrated): the sky camera's pixels
    have exact solid angles; the midpoint quadrature's error, O(h^2), is estimated by Richardson from the half
    resolution and bounds the difference (measured 2e-6 .. 3e-5)."""
    u = unit((0.0, 0.6, 0.8), beta)

    def integral(w):
        cam = RT.Camera(w, w // 2, kind="sky")
        r = RT.render(RT.Scene([], sky=1.0), RT.Observer(0.0, (0, 0, 0), u), cam)
        return float(np.sum(r["T_obs"] ** 4 * cam.solid_angles()) / (4 * math.pi))

    Ih, I2h = integral(256), integral(128)
    ref = RT.ref_energy_density_factor(beta)
    assert abs(Ih - ref) <= abs(Ih - I2h) and abs(Ih - ref) / ref < 1e-4


def test_the_quadrature_estimate_flags_an_unresolved_peak():
    """At beta = 0.999999 the forward peak (width 1/gamma ~ 1.4e-3 rad) is far below a pixel: the Richardson
    estimate must not pretend the integral is right (the visualization reports such a check as failed)."""
    u = unit((0, 0, 1), 0.999999)
    vals = []
    for w in (256, 128):
        cam = RT.Camera(w, w // 2, kind="sky")
        r = RT.render(RT.Scene([], sky=1.0), RT.Observer(0.0, (0, 0, 0), u), cam)
        vals.append(float(np.sum(r["T_obs"] ** 4 * cam.solid_angles()) / (4 * math.pi)))
    ref = RT.ref_energy_density_factor(0.999999)
    assert abs(vals[0] - ref) > abs(vals[0] - vals[1])


@pytest.mark.parametrize("beta", [0.5, 0.95, 0.999])
def test_stars_are_aberrated_as_the_closed_form_says(beta):
    """cos theta' = (cos theta + beta) / (1 + beta cos theta) and D = gamma (1 + beta cos theta) for stars at rest in the
    lab; the matrices of lorentz.aberrate agree too."""
    rng = np.random.default_rng(1)
    s = rng.normal(size=(60, 3))
    s /= np.linalg.norm(s, axis=1, keepdims=True)
    u = np.asarray(unit((0.6, 0, 0.8), beta))
    st = RT.star_images(RT.Scene([], stars=[(tuple(x), 5000.0) for x in s]), RT.Observer(0, (0, 0, 0), u))
    tol = 16 * EPS * g2(u)
    assert np.max(ang(st["d"], RT.ref_aberration(s, u))) <= tol
    g = float(LZ.gamma_of(u))
    assert np.max(np.abs(st["D"] / (g * (1 + s @ u)) - 1)) <= tol
    nl, D = LZ.aberrate(-s, -u)
    assert np.max(ang(st["d"], -nl)) <= tol and np.max(np.abs(st["D"] / D - 1)) <= tol
    assert not st["hidden"].any()


@pytest.mark.parametrize("beta", [0.3, 0.5, 0.99])
def test_aberration_reference_near_the_line_of_motion(beta):
    """Stars within a few degrees of +-u (review B3-3: the reference lost precision there and a correct run failed):
    the tracer and the reference agree within the stated tolerance, also over 20 000 random stars."""
    rng = np.random.default_rng(7)
    u = np.asarray(unit((0.6, 0, 0.8), beta))
    e = u / np.linalg.norm(u)
    small = rng.uniform(1e-4, 0.08, 400)
    phi = rng.uniform(0, 2 * math.pi, 400)
    a = np.cross(e, [1.0, 0, 0])
    a /= np.linalg.norm(a)
    b2 = np.cross(e, a)
    near = []
    for sg in (1.0, -1.0):
        near.append(sg * np.cos(small)[:, None] * e + np.sin(small)[:, None] * (np.cos(phi)[:, None] * a + np.sin(phi)[:, None] * b2))
    s = np.concatenate(near + [rng.normal(size=(20000, 3))])
    s /= np.linalg.norm(s, axis=1, keepdims=True)
    st = RT.star_images(RT.Scene([], stars=[(tuple(x), 5000.0) for x in s]), RT.Observer(0, (0, 0, 0), u))
    assert np.max(ang(st["d"], RT.ref_aberration(s, u))) <= 16 * EPS * g2(u)


@pytest.mark.parametrize("v", [(0.9, 0, 0), (0.5, 0.3, -0.2), (0.99, 0, 0)])
@pytest.mark.parametrize("u", [(0, 0, 0), (0, 0.3, 0.6)])
@pytest.mark.parametrize("kind", ["box", "sphere", "panel"])
def test_emission_events_and_doppler_factors_agree_with_retarded_time(kind, v, u):
    """For every pixel that sees a body: the tracer's emission time against lorentz.retarded_time of the rest-frame
    point it found, the look direction of that emission event, and D against gamma_o (1 - u.n)/(gamma_b (1 - v.n))
    (measured: <= 4 eps gamma^2)."""
    body = {"box": RT.Box((-1.0, 0.0, 3.0), (1.5, 1.0, 1.2), v), "sphere": RT.Sphere((-1.0, 0.5, 3.0), 1.5, v),
            "panel": RT.Panel((0, -1, 3), half=(30, 30), velocity=v, cell=0.5)}[kind]
    ob = RT.Observer(0.0, (0.2, 0, 0), u)
    # rays aimed at the retarded images of points of the body (an approaching body at 0.99 c looks tiny and far)
    rng = np.random.default_rng(3)
    q = rng.normal(size=(400, 3))
    if kind == "sphere":
        q = 1.5 * q / np.linalg.norm(q, axis=1, keepdims=True)
    elif kind == "box":
        k = rng.integers(0, 3, len(q))
        q = np.clip(q, -1, 1) * np.array([1.5, 1.0, 1.2])
        q[np.arange(len(q)), k] = np.sign(q[np.arange(len(q)), k]) * np.array([1.5, 1.0, 1.2])[k]
    else:
        q = 10 * q[:, 0, None] * np.array([1.0, 0, 0]) + 10 * q[:, 1, None] * np.array([0, 0, 1.0])
    _, xe0, _ = RT.retarded_points(body, q, ob)
    dirs = RT.look_direction(ob, xe0)
    r = RT.trace_directions(RT.Scene([body]), ob, dirs)
    m = r["body"] == 0
    assert m.sum() >= 40  # the points facing the observer
    te, xe, D = RT.retarded_points(body, r["q"][m], ob)
    tol = 64 * EPS * g2(v, u)
    assert np.all(r["t_emit"][m] <= ob.t)
    assert np.max(np.abs(te - r["t_emit"][m]) / (ob.t - te)) <= tol
    assert np.max(np.abs(D / r["D"][m] - 1)) <= tol
    assert np.max(ang(RT.look_direction(ob, xe), dirs[m])) <= tol
    # and the camera's pixels that see the body
    cam = RT.Camera(256, 128, kind="sky")
    rc = RT.render(RT.Scene([body]), ob, cam)
    mc = rc["body"] == 0
    if mc.any():
        te, _, D = RT.retarded_points(body, rc["q"][mc], ob)
        assert np.max(np.abs(te - rc["t_emit"][mc]) / (ob.t - te)) <= tol
        assert np.max(np.abs(D / rc["D"][mc] - 1)) <= tol


@pytest.mark.parametrize("beta,u", [(0.9, (0, 0, 0)), (0.99, (0, 0, 0)), (0.9, (0.5, 0.1, -0.3)), (0.999, (0, 0.4, 0))])
def test_a_moving_sphere_is_seen_with_a_circular_outline(beta, u):
    """Penrose (1959): the outline found by bisection along the tracer's rays is a circle on the observer's sky and is
    the circle of lorentz.sphere_outline (carried into the observer's frame). Measured: deviations <= 1e-13 rad."""
    v = unit((1.0, 0.2, 0.1), beta)
    sp = RT.Sphere((-3.0, 0.5, 5.0), 1.0, v)
    ob = RT.Observer(0.0, (0, 0, 0), u)
    dirs, bracket = RT.outline(RT.Scene([sp]), ob, 0)
    m, rho, dev = RT.circle_fit(dirs)
    mr, rr, devr = RT.circle_fit(RT.penrose_reference(sp, ob))
    P = np.linalg.norm(lab_rest_distance(sp, ob))
    tol = 64 * EPS * g2(v, u) * (1 + P / sp.radius)
    assert bracket < tol and dev <= tol and devr <= tol
    # every outline point of the tracer lies on the reference circle (axis mr, angular radius rr)
    assert np.max(np.abs(ang(dirs, mr) - rr)) <= tol


def lab_rest_distance(body, ob):
    return (LZ.boost(np.asarray(body.velocity, float)) @ np.r_[ob.t, np.asarray(ob.x) - np.asarray(body.center)])[1:]


def test_snapshot_shows_the_lorentz_contraction_that_light_never_shows():
    """For comparison only: the snapshot intersects the observer's simultaneity. Its emission events are simultaneous
    in the observer's frame and lie on the contracted body (an ellipse of aspect 1/gamma on a distant sky), while what
    is seen is a circle (Penrose)."""
    v = (0.9, 0.0, 0.0)
    sp = RT.Sphere((0.0, 0.0, 40.0), 1.0, v)
    ob = RT.Observer(0.0, (0, 0, 0), (0.0, 0.0, 0.0))
    snap = RT.render(RT.Scene([sp]), ob, RT.Camera(301, 301, fov=4), mode="snapshot")
    m = snap["body"] == 0
    assert np.allclose(snap["event"][m][:, 0], 0.0, atol=1e-12)
    x = snap["event"][m][:, 1:]
    g = float(LZ.gamma_of(v))
    # the lab-simultaneous body is the ellipsoid g^2 x^2 + y^2 + (z - 40)^2 = 1
    assert np.max(np.abs(g * g * x[:, 0] ** 2 + x[:, 1] ** 2 + (x[:, 2] - 40) ** 2 - 1)) < 1e-10
    aspect = lambda mm: (np.ptp(np.nonzero(mm)[1]) + 1) / (np.ptp(np.nonzero(mm)[0]) + 1)
    assert aspect(m) == pytest.approx(1 / g, abs=0.03)
    assert np.all(snap["D"][m] == 1.0) and "t_emit" not in snap
    _, xe, _ = RT.retarded_points(sp, np.zeros((1, 3)), ob)
    seen = RT.render(RT.Scene([sp]), ob, RT.Camera(301, 301, fov=4, forward=tuple(RT.look_direction(ob, xe)[0])))
    assert aspect(seen["body"] == 0) == pytest.approx(1.0, abs=0.03)


def test_lab_points_are_lorentz_contracted_along_the_velocity():
    v = np.array([0.6, 0.0, 0.8]) * 0.95
    q = np.array([[0.0, 0.0, 0.0], v / np.linalg.norm(v), [0.0, 1.0, 0.0]])
    x = RT.lab_points(RT.Sphere((1, 2, 3), 1.0, tuple(v)), q, 2.0)
    g = float(LZ.gamma_of(v))
    assert np.allclose(x[0], np.array([1, 2, 3]) + 2.0 * v)
    assert np.linalg.norm(x[1] - x[0]) == pytest.approx(1 / g, rel=1e-14)
    assert np.allclose(x[2] - x[0], [0, 1, 0], atol=1e-15)


def test_the_observer_inside_a_body_is_refused_with_a_reason():
    ob = RT.Observer(0.0, (0.0, 0.0, 0.0))
    cam = RT.Camera(8, 8)
    for body in (RT.Sphere((0.2, 0, 0), 1.0), RT.Box((0, 0.3, 0), (0.5, 0.5, 0.5))):
        with pytest.raises(ValueError, match="наблюдатель внутри тела"):
            RT.render(RT.Scene([body]), ob, cam)
    # a moving box whose world tube contains the observation event (in the box's own frame)
    with pytest.raises(ValueError, match="внутри"):
        RT.render(RT.Scene([RT.Box((-0.9 * 2.0, 0, 0), (0.5, 0.5, 0.5), (0.9, 0, 0))]), RT.Observer(2.0, (0, 0, 0)), cam)


def test_bodies_and_stars_behind_a_pinhole_camera_are_not_in_its_image():
    sc = RT.Scene([RT.Sphere((0, 0, -5), 1.0)], stars=[((0, 0, -1), 5000.0), ((0, 0, 1), 5000.0)])
    ob = RT.Observer(0.0, (0, 0, 0))
    cam = RT.Camera(64, 48, fov=90)
    r = RT.render(sc, ob, cam)
    assert np.all(r["body"] == -2)
    st = RT.star_images(sc, ob)
    ci, rj = cam.pixel_of(st["d"])
    assert np.isnan(ci[0]) and np.isnan(rj[0]) and abs(ci[1] - 31.5) < 1e-9 and abs(rj[1] - 23.5) < 1e-9
    assert st["hidden"].tolist() == [True, False]


def test_grazing_rays_meet_the_sphere_consistently():
    """Rays on a cone just inside and just outside the static sphere's outline (angle arcsin(r/d) +- 1e-12): every
    inside ray meets it with s near sqrt(d^2 - r^2), every outside ray misses."""
    d, r = 5.0, 1.0
    a = math.asin(r / d)
    psi = np.linspace(0, 2 * math.pi, 50, endpoint=False)
    for da, expect in ((-1e-12, True), (1e-12, False)):
        al = a + da
        dirs = np.stack([np.sin(al) * np.cos(psi), np.sin(al) * np.sin(psi), np.full_like(psi, np.cos(al))], -1)
        out = RT.trace_directions(RT.Scene([RT.Sphere((0, 0, d), r)]), RT.Observer(0.0, (0, 0, 0)), dirs)
        assert np.all(np.isfinite(out["s"]) == expect)
        if expect:
            assert np.allclose(out["s"], math.sqrt(d * d - r * r), rtol=1e-5)


def test_patterns_are_rest_frame_temperatures():
    """A box shows its six face temperatures (or their alternate squares); a panel its two; light from each pixel is
    a black body at D T_rest."""
    temps = (6000.0, 5000.0, 4000.0, 3000.0, 7000.0, 8000.0)
    bx = RT.Box((0, 0, 0), (1, 1, 1), temps=temps, alt=0.5, cells=2)
    for k, dirn in enumerate([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]):
        eye = 5 * np.asarray(dirn, float)
        f = -np.asarray(dirn, float)
        up = (0, 0, 1) if abs(f[2]) < 0.9 else (0, 1, 0)
        r = RT.render(RT.Scene([bx]), RT.Observer(0.0, tuple(eye)), RT.Camera(40, 40, fov=20, forward=tuple(f), up=up))
        vals = set(np.unique(r["T_rest"][r["body"] == 0]).tolist())
        assert vals == {temps[k], 0.5 * temps[k]}
    v = (0.0, 0.0, 0.8)
    r = RT.render(RT.Scene([RT.Panel((0, -1, 0), half=(50, 50), velocity=v, cell=0.7)]), RT.Observer(0.0, (0, 0, 0)),
                  RT.Camera(128, 64, kind="sky"))
    m = r["body"] == 0
    assert set(np.unique(r["T_rest"][m]).tolist()) == {5500.0, 3000.0}
    assert np.allclose(r["T_obs"][m], r["D"][m] * r["T_rest"][m])
    assert r["D"][m].min() < 0.5 and r["D"][m].max() > 1.5  # receding and approaching parts of the moving floor


@pytest.mark.skipif(not B.devices()["gpu"]["available"], reason="no GPU given to this container")
def test_gpu_equals_cpu():
    """The same formulas on GPU 0 (CuPy) and on the CPU: equal to round-off (measured: identical)."""
    sc = RT._bench_scene()
    ob = RT.Observer(0.0, (0, 0, 0), (0, 0.1, 0.6))
    cam = RT.Camera(256, 192, fov=110)
    B.configure({"kernels": {RT.KERNEL: {"device": "cpu"}}})
    rc = RT.render(sc, ob, cam)
    B.configure({"kernels": {RT.KERNEL: {"device": "gpu"}}})
    rg = RT.render(sc, ob, cam)
    assert B.used()[RT.KERNEL]["drawn"]["device"] == "gpu"
    assert np.array_equal(rc["body"], rg["body"])
    for k in ("s", "D", "T_obs", "t_emit"):
        f = np.isfinite(rc[k])
        assert np.array_equal(f, np.isfinite(rg[k]))
        assert np.max(np.abs(rc[k][f] - rg[k][f]) / np.maximum(np.abs(rc[k][f]), 1e-300)) <= 16 * EPS * g2(ob.u)


def test_the_kernel_is_registered_with_a_measured_crossover():
    k = B.kernels()[RT.KERNEL]
    assert k.gpu and k.crossover and "измерено" in k.crossover_note and k.bench is not None
    assert list(k.precisions) == ["fp64"]
