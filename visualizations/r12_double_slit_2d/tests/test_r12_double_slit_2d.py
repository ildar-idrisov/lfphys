# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""r12: the double slit in 2-D. Every preset builds; a small symmetric experiment runs to its end and passes its
checks (norm, time step, flux into the screen against the absorbed probability, Bohm hits against the computed
pattern, symmetry, no trajectory across the axis); nothing reaches the screen before the wave can; a slit closed after
the packet has passed changes almost nothing, closed before it the pattern changes; the half flux quantum gives a
symmetric pattern with the fringes moved by half a period; a path mark lets trajectories cross the axis; refusals
leave the world as it was; GPU = CPU. The geometry of these tests is small (the presets take ~1 min on GPU 0)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import backend  # noqa: E402
from lfphys.i18n import english, is_t  # noqa: E402
from r12_double_slit_2d.engine import apparatus as AP  # noqa: E402
from r12_double_slit_2d.viz import SCHEMA  # noqa: E402

V = "r12_double_slit_2d"
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 300,
         "n_tracks": 20}


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def run_out(h, tau_max=60.0):
    tu = h.sim.tunit
    while not h.sim.done and h.sim.tau < tau_max:
        h.run_to(h.sim.t + 1.0 * tu)
    return h


def screen_pattern(h):
    xs, P = h.sim._pattern(h.sim.flux)
    return xs, P


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_build(preset):
    h = Harness(V, preset)
    hd = h.of("header")[-1]
    kinds = {o["kind"] for o in hd["scene3d"]["objects"]}
    assert {"plate", "target", "panel"} <= kinds
    assert hd["scene3d"]["planes"]["max"] == 0
    assert not failed(h), failed(h)  # the static checks: grid, wall, absorbers
    assert h.of("wave"), "the initial wave is sent with the header"


def test_small_symmetric_experiment_passes_its_checks():
    h = run_out(Harness(V, "narrow", SMALL))
    assert h.sim.done
    ids = set(h.checks())
    assert {"norm", "numerics", "flux_absorbed", "bohm_born", "bohm_fraction", "bohm_accuracy", "symmetry",
            "no_crossing"} <= ids
    assert not failed(h), [(i, h.checks()[i]) for i in failed(h)]
    r = h.of("result")[-1]
    F = r["fractions"]
    assert abs(sum(F.values()) - 1) < 1e-9
    assert 0.05 < F["screen"] < 0.6 and F["back"] > 0.2
    assert r["bohm"]["crossed_axis"] == 0
    assert r["bohm"]["A"] > 0 and r["bohm"]["B"] > 0
    assert not h.errors()


def test_the_third_dimension_is_the_exact_product():
    """Nothing depends on y: the run sends the free y-factor eta (its width in closed form) with every image, the
    particles' y (y0 sigma_y(t)/sigma_y, starts drawn after x, z so those are unchanged by sigma_y), the screen as
    P(x, y) whose sum over y is the pattern P(x); the hits' y follow the screen's y-marginal and the guidance equation
    integrated in eta (checks screen_y, bohm_y, bohm_y_motion)."""
    h = run_out(Harness(V, "narrow", {**SMALL, "n_bohm": 400}))
    s = h.sim
    assert not failed(h), failed(h)
    assert {"screen_y", "bohm_y", "bohm_y_motion"} <= set(h.checks())
    assert h.checks()["bohm_y_motion"]["value"] < 1e-7
    w = h.of("wave")[-1]
    tau = w["tau"]
    assert abs(w["sigma_y"] - s.sy * math.sqrt(1 + (tau / (2 * s.sy ** 2)) ** 2)) < 1e-12
    eta = [b for m, b in h.msgs if m.get("type") == "wave"][-1]["eta"]
    y = np.linspace(-s.y_half, s.y_half, len(eta))
    ref = np.exp(-y ** 2 / (2 * w["sigma_y"] ** 2))
    assert np.max(np.abs(eta - ref / ref.max())) < 1e-6  # |eta|^2 of a free Gaussian, its sampled peak 1
    tr = [b for m, b in h.msgs if m.get("type") == "tracks"]
    assert all("y" in b and len(b["y"]) == s.K for b in tr)
    hits = [b for m, b in h.msgs if m.get("type") == "hits"]
    assert hits and all(np.all(np.isfinite(b["y"])) for b in hits)
    h.runner._frame(1.0)
    f, fb = [(m, b) for m, b in h.msgs if m.get("type") == "frame"][-1]
    assert "y" in fb and len(fb["y"]) == s.K
    tgt = h.of("target")[-1]
    assert tgt["shape"][1] > 2  # P(x, y), not a pattern repeated along y
    other = Harness(V, "narrow", {**SMALL, "n_bohm": 400, "sigma_y": 10.0})
    assert np.array_equal(other.sim.X, Harness(V, "narrow", {**SMALL, "n_bohm": 400}).sim.X)
    assert abs(np.std(other.sim.Y0) / 10.0 - 1) < 0.15
    # review C1-11: the Kolmogorov-Smirnov test of the hits' y cannot tell a wrong y-motion (eta spreads by a few
    # per cent over this flight); the second method fails every wrong motion: none, twice the spreading, 0.1 % more
    # of it, and every hit at the earliest one's time (the bug it found did so within each step)
    got = {}
    s._check = lambda cid, *a, **k: got.__setitem__(cid, k.get("ok"))
    _, P = screen_pattern(h)
    hit = s.fate == 1
    y_run, y0, tau = s.hit_y[hit].copy(), s.Y0[hit], s.hit_t[hit] / s.tunit
    st = s.sy * np.sqrt(1 + (tau / (2 * s.sy ** 2)) ** 2)
    wrong = {"none": y0, "double": y0 * (2 * st / s.sy - 1), "0.1 %": y0 * (1 + 1.001 * (st / s.sy - 1)),
             "earliest time": y0 * np.sqrt(1 + (tau.min() / (2 * s.sy ** 2)) ** 2)}
    for name, y in [("as run", y_run)] + list(wrong.items()):
        s.hit_y[hit] = y
        s._y_checks(P)
        assert got["bohm_y_motion"] is (name == "as run"), name


def test_nothing_reaches_the_screen_before_the_wave_can():
    """The packet's front (5 sigma ahead, at 5 standard deviations above the mean speed) needs a time to reach the
    screen; before half of it no hit and no flux."""
    h = Harness(V, "narrow", SMALL)
    geo = h.sim.geo
    vmax = AP.V0_SPEED * (1 + 5 / (2 * geo.sz * AP.K0))
    t_first = (geo.L - (geo.z_src + 5 * geo.sz)) / vmax
    h.run_to(0.5 * t_first * h.sim.tunit)
    assert not h.of("hits")
    assert abs(float(h.sim.flux.sum())) < 1e-8


def _closed_b_at(tau_close):
    h = Harness(V, "narrow", SMALL)
    tu = h.sim.tunit
    if tau_close <= 0:
        h.set(slit_b=False)
    else:
        h.run_to(tau_close * tu)
        h.set(slit_b=False)
    return run_out(h)


def test_closing_a_slit_acts_only_from_that_moment():
    """Slit B closed after the packet has left the plate (its slowest part 5 sigma behind, at 5 deviations below the
    mean speed): the pattern is that of both slits up to the small part still near the plate; closed before the
    packet arrives: a different pattern (one slit)."""
    ref = run_out(Harness(V, "narrow", SMALL))
    _, P0 = screen_pattern(ref)
    geo = ref.sim.geo
    vmin = AP.V0_SPEED * (1 - 5 / (2 * geo.sz * AP.K0))
    tau_passed = (abs(geo.z_src) + 5 * geo.sz + geo.w + 3.0) / vmin
    late = _closed_b_at(tau_passed)
    _, P1 = screen_pattern(late)
    early = _closed_b_at(0.0)
    _, P2 = screen_pattern(early)
    pk = P0.max()
    assert np.max(np.abs(P1 - P0)) / pk < 2e-3
    assert np.max(np.abs(P2 - P0)) / pk > 0.2
    assert late.of("setup"), "the change is announced with the new plate"


def test_half_flux_quantum_moves_the_fringes_by_half_a_period():
    h = run_out(Harness(V, "ab", SMALL))
    c = h.checks()
    assert not failed(h), failed(h)
    assert c["symmetry_ab"]["ok"]
    assert abs(c["ab_phase"]["value"]) < 0.2, c["ab_phase"]  # the fringe phase minus 2 pi Phi/Phi0, mod 2 pi


def test_path_mark_lets_trajectories_cross_the_axis():
    """With the spin in slit B turned by 180 degrees the two parts of the wave no longer interfere and the guidance
    no longer keeps the trajectories on their side: some cross the axis; the checks still pass."""
    h = run_out(Harness(V, "mark180", {**SMALL, "n_bohm": 600}))
    assert not failed(h), failed(h)
    assert h.of("result")[-1]["bohm"]["crossed_axis"] > 0
    assert h.checks()["visibility"]["value"] < 0.5


def test_observer_at_slit_b_marks_the_path_of_a_particle_without_spin():
    """The which-path detector at slit B (Englert's two-level model) works for any particle: with theta = 180 degrees
    the fringes go (He-4 has no spin in the engine); the observer is drawn in 3-D, more opaque the more the path is
    marked, and follows a live change of theta."""
    h = run_out(Harness(V, "observer", {**SMALL, "n_bohm": 600}))
    assert not failed(h), failed(h)
    hd = h.of("header")[-1]
    obs = [o for o in hd["scene3d"]["objects"] if o["id"] == "observer"]
    assert obs and obs[0]["kind"] == "box" and obs[0]["opacity"] > 0.6
    assert hd["particle"]["mark"] == "detector"
    assert h.checks()["visibility"]["value"] < 0.5
    assert h.of("result")[-1]["bohm"]["crossed_axis"] > 0
    g = Harness(V, "narrow", {**SMALL, "particle": "c60", "mark": "detector"})
    g.set(mark_deg=90.0)
    assert g.sim.live["mark_deg"] == 90.0
    o = g.of("setup")[-1]["observer"]
    assert abs(o["opacity"] - (0.12 + 0.5 * 0.5)) < 1e-12


def test_refusals_leave_the_world_unchanged():
    h = Harness(V, "narrow", SMALL)
    before = dict(h.sim.live)
    h.set(mark_deg=90.0)  # no spin in this world
    assert h.sim.live == before
    assert any("path mark" in english(e) for e in h.errors()) or h.of("live")
    n = Harness(V, "narrow", {**SMALL, "particle": "neutron"})
    n.set(flux=0.5)  # a neutral particle
    assert n.sim.live["flux"] == 0.0
    with pytest.raises(ValueError, match="charged particles"):
        Harness(V, "narrow", {**SMALL, "particle": "neutron", "flux": 0.5})


@pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="no GPU")
def test_gpu_equals_cpu():
    from lfphys.core.quantum import schrodinger_nd as S
    h = Harness(V, "narrow", SMALL)
    assert h.sim.prop.device == "gpu"
    cpu = S.SplitOperator(h.sim.prop.H, h.sim.dt, track_absorbed=True, force_cpu=True, why="test")
    a = h.sim.prop.put(h.sim._packet(h.sim.prop.H, h.sim.g))
    b = cpu.put(h.sim._packet(h.sim.prop.H, h.sim.g))
    a = h.sim.prop.step(a, 200)
    b = cpu.step(b, 200)
    assert np.max(np.abs(h.sim.prop.get(a) - cpu.get(b))) < 1e-11



def test_a_quarter_flux_quantum_moves_the_run_and_the_curves_the_same_way():
    """Phi = +-Phi0/4: the run's fringe phase, the two-path reference 2 pi Phi/Phi0 sign(q) and the approximate theories'
    curves all move the same way (review B3-1: the curves had the opposite sign; at Phi0/2 the two signs coincide)."""
    for flux in (0.25, -0.25):
        h = run_out(Harness(V, "narrow", {**SMALL, "flux": flux}))
        xs, P = screen_pattern(h)
        geo = h.sim.geo
        period = (geo.L - 0.5 * geo.w) / geo.d
        m = h.sim.on_screen
        _, phi = AP.fringes(xs[m], P[m] / h.sim.g.d[0], period)
        ref = 2 * math.pi * flux * (-1)  # electron: sign(q) = -1
        assert abs(math.remainder(phi - ref, 2 * math.pi)) < 0.1, (flux, phi, ref)
        refs = h.of("result")[-1]["refs"]
        for k in ("paraxial", "kirchhoff"):
            R = np.asarray(refs[k])
            _, phr = AP.fringes(xs[m], R[m], period)
            assert abs(math.remainder(phr - ref, 2 * math.pi)) < 0.2, (k, flux, phr, ref)
        assert abs(h.checks()["ab_phase"]["value"]) < 0.1


def test_no_spin_mark_for_particles_without_spin():
    """He-4 and C60 have no internal state in the engine: the spin mark is refused (review B3-7)."""
    for particle in ("he4", "c60"):
        with pytest.raises(ValueError, match="has no spin"):
            Harness(V, "mark180", {**SMALL, "particle": particle})


def test_edges_narrower_than_the_grid_are_refused():
    with pytest.raises(ValueError, match="wall's edges"):
        Harness(V, "narrow", {**SMALL, "edge": 0.1})  # the coarse grid's step is 0.2 lambda


def test_the_screen_shows_nothing_before_the_wave_can_arrive():
    """Before the packet's front can reach the screen its accumulated flux is round-off: the screen messages say
    "empty" and carry no pattern (review B3-5)."""
    h = Harness(V, "narrow", SMALL)
    geo = h.sim.geo
    vmax = AP.V0_SPEED * (1 + 5 / (2 * geo.sz * AP.K0))
    h.run_to(0.6 * (geo.L - (geo.z_src + 5 * geo.sz)) / vmax * h.sim.tunit)
    sc = h.of("screen")
    assert sc and all(m["empty"] and m["total"] == 0.0 for m in sc)


def test_the_corners_of_the_schema_are_refused_by_their_cost():
    """An experiment estimated to keep the device busy longer than its limit is refused with the estimate (review
    B3-6: ~29 min of GPU load at a corner, past the host's ~18 min hang)."""
    with pytest.raises(ValueError, match="too heavy"):
        Harness(V, "narrow", {"a": 0.5, "d": 8.0, "L": 200.0, "sigma_x": 40.0, "sigma_z": 20.0, "grid": "fine"})
    h = Harness(V, "narrow", SMALL)
    assert 0 < h.sim.est_cost < 600


def test_the_grid_changes_the_pattern_only_by_its_numerical_error():
    """With the wall's edges a physical length (0.2 lambda), the pattern on two grids (lambda/6, lambda/8) is the same
    up to the numerical error (review B3-2: edges of one grid step made the grid choice change the wall by 17 % of the
    pattern's peak in this geometry)."""
    pats = {}
    for grid in ("normal", "fine"):
        h = run_out(Harness(V, "narrow", {**SMALL, "grid": grid}))
        xs, P = screen_pattern(h)
        m = h.sim.on_screen
        pats[grid] = (xs[m], P[m] / h.sim.g.d[0])
        assert h.checks()["numerics"]["ok"]
    from scipy.interpolate import CubicSpline
    xf, Pf = pats["fine"]
    Pn = CubicSpline(*pats["normal"])(xf)
    assert np.max(np.abs(Pn - Pf)) / Pf.max() < 3e-3


# --- the plate is live (review UX-ui U12): a, d, w, V0 changed at the current moment, in the world's window ------------
def test_the_wall_height_set_at_the_start_is_the_world_built_with_it():
    """V0 set live at t = 0 builds the very Hamiltonian of a world built with that V0 (nothing else depends on it): the
    two waves agree bit for bit after 40 pairs; the event says the world had not yet computed. A different V0 changes
    the wave (negative control)."""
    live = Harness(V, "narrow", SMALL)
    live.set(V0=6.0)
    assert live.sim.live["V0"] == 6.0 and not live.errors()
    assert "has not computed yet" in english(live.of("event")[-1]["text"])
    built = Harness(V, "narrow", {**SMALL, "V0": 6.0})
    other = Harness(V, "narrow", SMALL)
    tu = live.sim.tunit
    for h in (live, built, other):
        h.run_to(40 * h.sim.pair * tu)
    a, b, c = (h.sim.prop.get(h.sim.psi) for h in (live, built, other))
    assert np.array_equal(a, b)
    assert np.max(np.abs(a - c)) > 1e-6
    note = english(live.checks()["grid_wall"]["note"])
    assert note.startswith("κ = √(2(V0 − E0)) = ") and "V0 = 6 E0" in note


def test_a_live_plate_is_the_apparatus_plate_in_the_same_window():
    """a, d, w changed live: the run's and the companion's potential are the apparatus's plate for the new a, d, w in
    the window the world was built with (screen, source, grid unchanged); the set-up message carries the plate in force
    for the view; the event says how much of the wave was where the wall changed."""
    h = Harness(V, "narrow", SMALL)
    g0 = h.sim.geo
    window = (g0.screen_half, g0.x_half, g0.z_src, g0.z_min, g0.z_max, h.sim.g.shape)
    h.run_to(h.sim.t + 3 * h.sim.tunit)
    h.set(a=2.0, d=5.0, w=1.5)
    assert not h.errors(), h.errors()
    s = h.sim
    assert (s.geo.screen_half, s.geo.x_half, s.geo.z_src, s.geo.z_min, s.geo.z_max, s.g.shape) == window
    ref = AP.Geometry(2.0, 5.0, 1.5, g0.L, g0.sx, g0.sz, g0.h, screen_half=g0.screen_half, edge=g0.edge)
    for prop, g in ((s.prop, s.g), (s.comp, s.g_c)):
        assert np.array_equal(np.asarray(prop.H.V), s.live["V0"] * AP.E0 * ref.plate(g))
    su = h.of("setup")[-1]
    assert su["geometry"] == {"a": 2.0, "d": 5.0, "w": 1.5, "V0": 4.0, "centers": [-2.5, 2.5]}
    assert [hole["rect"][:2] for hole in su["plate"]["holes"]] == [[-3.5, -1.5], [1.5, 3.5]]
    ev = english(h.of("event")[-1]["text"])
    assert "of the probability" in ev and "acts from this moment on" in ev


def test_a_plate_that_does_not_fit_the_window_is_refused_and_the_world_unchanged():
    """Slits beyond the screen, a plate thicker than the room between the source and the screen, merged slits: each is
    refused in the owner's terms and leaves the plate, the potential and the live values as they were."""
    h = Harness(V, "narrow", {**SMALL, "L": 5.0})  # a short flight: the screen 5 λ behind the plate
    V0 = np.array(h.sim.prop.H.V)
    live, geo = dict(h.sim.live), h.sim.geo
    for change, why in (({"d": 30.0}, "a slit goes beyond the screen"), ({"w": 10.0}, "does not fit into the "
                        "experiment's window"), ({"a": 4.5}, "the slits merge")):
        n = len(h.errors())
        h.set(**change)
        assert len(h.errors()) == n + 1 and why in english(h.errors()[-1]), (change, h.errors()[-1:])
        assert "What to change" in english(h.errors()[-1])
        assert h.sim.live == live and h.sim.geo is geo and np.array_equal(np.asarray(h.sim.prop.H.V), V0)
        assert h.of("live")[-1]["values"] == h.sim.live_values()


def share_in(text):
    """The probability an event names: the argument of its sentence «where the wall changed there was {p} of the
    probability» (the text is language-neutral: the number is an argument, not a formatted string)."""
    if is_t(text):
        if text["$t"].startswith("where the wall changed there was"):
            return text["a"]["p"]
        for v in (text.get("a") or {}).values():
            p = share_in(v)
            if p is not None:
                return p
    return None


def _plate_widened_at(tau):
    h = Harness(V, "narrow", SMALL)
    if tau > 0:
        h.run_to(tau * h.sim.tunit)
    h.set(a=2.5)
    return run_out(h)


def test_a_plate_changed_after_the_packet_passed_changes_almost_nothing():
    """Slit width widened after the packet has left the plate (its slowest part 5 sigma behind, at 5 deviations below
    the mean speed): the pattern is that of the plate it crossed, within 2·10⁻³ of its peak, and the run's checks pass
    (norm, numerics, flux, Bohm); widened before the packet arrives (at t = 0): another pattern (negative control). After
    a change at t > 0 the comparisons that assume one set-up for the whole run are not made."""
    ref = run_out(Harness(V, "narrow", SMALL))
    _, P0 = screen_pattern(ref)
    geo = ref.sim.geo
    vmin = AP.V0_SPEED * (1 - 5 / (2 * geo.sz * AP.K0))
    late = _plate_widened_at((abs(geo.z_src) + 5 * geo.sz + geo.w + 3.0) / vmin)
    _, P1 = screen_pattern(late)
    early = _plate_widened_at(0.0)
    _, P2 = screen_pattern(early)
    pk = P0.max()
    assert np.max(np.abs(P1 - P0)) / pk < 2e-3
    assert np.max(np.abs(P2 - P0)) / pk > 0.05
    assert not failed(late), failed(late)
    ids = set(late.checks())
    assert {"norm", "numerics", "flux_absorbed", "bohm_born"} <= ids
    assert not ({"symmetry", "no_crossing", "visibility", "ref_paraxial"} & ids)
    assert [m for m in late.of("event") if "Slit width a, λ: 1.5 λ → 2.5 λ" in english(m["text"])]


def test_a_wall_grown_under_the_wave_is_a_sudden_change_and_said():
    """The plate thickened while the packet is at it: the probability where the wall changed is computed from the wave
    and said in the event (here > 10⁻³); norm + absorbed stays 1 (the split steps are unitary for any potential)."""
    h = Harness(V, "narrow", SMALL)
    geo = h.sim.geo
    h.run_to(abs(geo.z_src) / AP.V0_SPEED * h.sim.tunit)  # the packet's centre at the plate
    h.set(w=2.0)
    ev = [m["text"] for m in h.of("event") if "Plate thickness" in english(m["text"])][-1]
    assert share_in(ev) > 1e-3, ev
    run_out(h)
    assert h.checks()["norm"]["ok"]


def test_a_live_plate_is_continued_from_a_checkpoint_and_replayed_by_a_restore(tmp_path):
    """A plate change before a checkpoint and another after it: the world continued from the checkpoint in a new process
    emits the original's bytes (as tests/test_checkpoint.py for the shared session); a world rebuilt from its record's
    script (Runner.restore) has the same plate and frames."""
    import json
    import queue
    import subprocess
    import test_checkpoint as TC
    import test_restore as TR
    from lfviz.sim import Runner
    msgs = []

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    make_world = TC._maker(V, emit)
    sim, _ = make_world(None, {}, 7)
    run = Runner(sim, emit, queue.Queue(), make_world=make_world)
    run._start_world()
    sp = sim.default_speed
    TC._apply(run, [{"adv": 0.5 * sp}, {"adv": 0.7 * sp}, {"cmd": "set", "args": {"values": {"a": 2.0, "V0": 5.0}}},
                    {"adv": 0.4 * sp}])
    file = TC._checkpoint(run, tmp_path)
    n0 = len(msgs)
    after = [{"adv": 0.3 * sp}, {"cmd": "set", "args": {"values": {"w": 1.5}}}, {"adv": 0.6 * sp}, {"adv": 0.5 * sp}]
    TC._apply(run, after)
    original = TC._bytes(msgs[n0:])
    assert any(m.get("type") == "setup" and m["geometry"]["w"] == 1.5 for m, _ in msgs[n0:])
    out = tmp_path / "session.bin"
    code = TC.SESSION_CHILD.format(paths=repr(list(sys.path)), file=str(file), viz=V, ops=json.dumps(after),
                                   out=str(out))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=900,
                       cwd=str(Path(TC.__file__).parent))
    assert r.returncode == 0, r.stderr[-4000:]
    data, cont, i = out.read_bytes(), [], 0
    while i < len(data):
        n = int.from_bytes(data[i:i + 8], "little")
        cont.append(data[i + 8:i + 8 + n])
        i += 8 + n
    assert cont == original
    # the restore by replay of the record's script
    sim1, run1, frames1, script1 = TR._world(V)
    run1._start_world()
    run1._advance(0.6 * sp)
    run1._frame(0.0)
    run1.handle({"cmd": "set", "args": {"values": {"d": 5.0, "w": 1.5}}})
    run1._advance(1.5 * sp)
    run1._frame(0.0)
    sim2, run2, frames2, _ = TR._world(V)
    run2.restore(1, list(script1)[:-1], sim1.t, lambda on: None)
    assert (sim2.geo.d, sim2.geo.w) == (5.0, 1.5)
    run2._frame(0.0)
    TR._same(frames1[-1][0], frames2[-1][0])
    TR._same(frames1[-1][1] or {}, frames2[-1][1] or {})


def test_every_length_and_the_wall_height_carry_their_unit_in_the_label():
    """Review UX-ui U19: the player shows a parameter's label, not its unit field: every parameter with a unit names it
    in the label («Slit width a, λ», «de Broglie wavelength λ, pm», «Wall height V₀, in E₀»)."""
    for p in SCHEMA.params:
        if p.unit:
            assert english(p.unit) in english(p.label), (p.id, p.label, p.unit)
    assert english(SCHEMA.by_id["lam_pm"].label).endswith(", pm") and english(SCHEMA.by_id["V0"].label).endswith("in E₀")
