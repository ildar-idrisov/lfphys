# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p02: the quantum playground. Every preset builds, runs and keeps norm + absorbed = 1; the wrapper's units against
closed forms (a packet's energy from its wavelength and widths, a trap's coherent state from hbar omega in meV, the
cyclotron period from the field in tesla); a position measurement as an action; Bohm points: registered by the
absorbers they enter in the proportions the absorbed probabilities give, their accuracy measured by a control, kept
across a jump of the environment (review B6-Q1, Q5); the presets that demonstrate an effect show it (which path, AB:
B6-Q9, Q10); a strong environment shortens the step (B6-Q6); a field cannot be changed under a charged packet
(B6-Q3); a refused change leaves the scene as it was; the scene file starts the same set-up (and its time: the
framework review's F14), overflowing values are refused (F15), a change of only the Bohm count keeps the wave (F16).
The engine's physics (shapes, fields, detectors, measurement, decoherence, Bohm, energy and flux checks) is tested in
``lfphys/tests/test_quantum_scene.py``; the shared tests continue every world from its checkpoint byte for byte and
rebuild it by replay (``../tests/test_checkpoint.py``, ``../tests/test_restore.py``)."""

import copy
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import backend  # noqa: E402
from lfphys.core.quantum import scene as QS  # noqa: E402
from lfphys.theories.interpretations import bohm  # noqa: E402
from p02_quantum import viz as P  # noqa: E402
from p02_quantum.viz import EV, SCHEMA, TESLA, TU  # noqa: E402
from lfphys.i18n import is_t, render  # noqa: E402

V = "p02_quantum"


def run(h, t_end, n=30):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


def failed(h):
    return [c["id"] for c in h.checks().values() if c.get("ok") is False]


def errs(h):
    """The run's error texts in English (a text travels as a T, its JSON form, or a plain string)."""
    return [render(e) for e in h.errors()]


def mean_pos(h, oid):
    return np.array([h.of("frame")[-1]["now"][oid][f"⟨{c}⟩, nm"] for c in "xyz"[:h.sim.ndim]])


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_builds_runs_and_keeps_the_balance(preset):
    h = Harness(V, preset)
    run(h, h.sim.t + (1.0 if preset == "ball_3d" else 3.0) * h.sim.default_speed, 12)
    assert not h.errors(), h.errors()
    assert not failed(h), {k: h.checks()[k] for k in failed(h)}
    bal = [c for c in h.checks().values() if c["id"].startswith("balance_")]
    assert bal and all(c["ok"] for c in bal)
    assert h.of("wave") and h.of("shapes") and h.of("scene")
    if h.sim.ndim == 3:
        assert h.of("wave3d")


def test_a_packets_energy_from_its_wavelength_and_widths():
    """The electron of the tunnel preset far from the barrier: <H> = hbar^2 (k^2 + sum_i 1/(4 sigma_i^2)) / 2m, k = 2 pi
    / lambda, in eV through the scene's unit hbar^2/(m_e nm^2)."""
    h = Harness(V, "tunnel")
    h.runner._frame(0.0)
    for _ in range(h.sim.CHECK_FRAMES):
        h.runner._frame(0.0)
    E = h.checks()["energy_o3"]["value"]
    k, sx, sy = 2 * math.pi / 2.0, 2.5, 4.0
    ref = (k * k + 1 / (4 * sx * sx) + 1 / (4 * sy * sy)) / 2 * EV
    assert E == pytest.approx(ref, rel=1e-9)
    assert EV == pytest.approx(0.0761996, rel=1e-6)  # hbar^2 / (m_e nm^2) in eV (CODATA)


def test_a_trap_holds_a_coherent_state_with_its_closed_form_energy():
    """The trap preset: the ground-state width 1/sqrt(2 m omega) displaced by (x0, y0) is a coherent state, its energy
    hbar omega (ndim/2) + m omega^2 (x0^2 + y0^2)/2 with hbar omega = 20 meV; it keeps that energy (closed) and its
    centre returns after one period 2 pi / omega."""
    h = Harness(V, "trap")
    w = 20e-3 / EV  # omega in units of 1/time
    for _ in range(h.sim.CHECK_FRAMES + 1):
        h.runner._frame(0.0)
    E0 = h.checks()["energy_o2"]["value"]
    assert E0 == pytest.approx((w * 1.0 + 0.5 * w * w * (36.0 + 4.0)) * EV, rel=2e-3)  # sigma 1.38 ~ 1/sqrt(2 w)
    T = 2 * math.pi / w * TU
    run(h, T, 40)
    assert np.allclose(mean_pos(h, "o2"), [6.0, 2.0], atol=0.02)
    assert not failed(h) and h.checks()["energy_o2"]["ok"]


def test_the_cyclotron_orbit_from_the_field_in_tesla():
    """The cyclotron preset: an electron (charge -e) in Bz = 100 T, started along +x, turns towards +y with
    omega_c = eB/m_e on the circle of radius v/omega_c = 10.3 nm (its centre follows the classical orbit exactly in a
    uniform field: Ehrenfest); compared at the scene's own time over one period."""
    h = Harness(V, "cyclotron")
    h.runner._frame(0.0)
    wc = 100.0 / TESLA  # q B / m in units of 1/time (|q| = 1, m = 1)
    assert wc / TU == pytest.approx(1.602176634e-19 * 100.0 / 9.1093837139e-31, rel=1e-9)  # rad/s, CODATA
    v = 2 * math.pi / 4.0  # k / m in nm per unit of time
    R = v / wc
    for frac in (0.25, 0.5, 1.0):
        run(h, frac * 2 * math.pi / wc * TU, 20)
        ts = h.sim.qs.t
        ref = [R * math.sin(wc * ts), -10.0 + R * (1 - math.cos(wc * ts))]
        assert np.allclose(mean_pos(h, "o2"), ref, atol=0.01), (frac, mean_pos(h, "o2"), ref)


def test_a_position_measurement_collapses_the_wave_to_its_outcome():
    h = Harness(V, "trap")
    h.runner._frame(0.0)
    # the sharpest resolution this grid holds after the measurement (review B6-Q4): 0.85 nm here; 0.5 is refused
    smin = h.sim.qs.measure_min_sigma(1)
    assert 0.8 < smin < 0.9
    h.action("measure", particle="o2", sigma=0.5)
    assert any("too small" in e for e in errs(h))
    h.action("measure", particle="o2", sigma=0.9)
    ev = [e for e in h.of("event") if e.get("kind") == "action" and e.get("name") == "measure"]
    assert ev and "found at" in render(ev[-1]["text"]), h.errors()
    x = np.array(h.of("marks")[-1]["pos"] if "pos" in h.of("marks")[-1] else [])
    h.runner._frame(0.0)
    rho = h.sim.qs.density()
    g = h.sim.qs.grid
    var = sum(float(np.sum(rho * (g.mesh()[a] - mean_pos(h, "o2")[a]) ** 2) * g.dV) for a in range(2))
    # after a measurement of resolution s the width per axis is 1/sqrt(1/s0^2 + 1/s^2) (Jacobs & Steck; engine test):
    # s0 = 1.38, s = 0.9 -> 0.754 per axis
    s = 1 / math.sqrt(1 / 1.38 ** 2 + 1 / 0.9 ** 2)
    assert var == pytest.approx(2 * s * s, rel=0.02)
    assert len(h.sim.marks) == 1 and x.size == 0


def test_bohm_points_are_registered_by_the_detectors_they_enter():
    h = Harness(V, "double_slit")
    run(h, h.sim.t + 14.0 * h.sim.default_speed, 40)
    B = h.sim.bohm["o4"]
    keys = [k for k in B["key"] if k is not None]
    assert int(B["fly"].sum()) + len(keys) == 60 and keys
    assert set(keys) <= {"edges", f"detector {h.sim.ref['o2'][1]}"}
    now = h.of("frame")[-1]["now"]["o4"]
    assert render(now["Bohm: points in flight"]) == f"{int(B['fly'].sum())} of 60"


def _double_slit_with(bohm_n, seed=3, extra=None):
    pr = copy.deepcopy(SCHEMA.presets["double_slit"]["params"])
    for o in pr["scene"]["objects"]:
        if o["type"] == "packet":
            o["values"]["bohm"] = bohm_n
    if extra:
        pr["scene"]["objects"].insert(0, extra)
    return Harness(V, None, pr, seed=seed)


def _run_until(h, T):
    sim, qs = h.sim, h.sim.qs
    t = sim.t
    while qs.t < T - 0.02:
        t = min(t + sim.max_step(), T * TU)
        h.run_to(t)
    for _ in range(sim.CHECK_FRAMES):
        h.runner._frame(0.0)


def test_bohm_registrations_follow_the_absorbed_probabilities(monkeypatch):
    """Review B6-Q1 / Q15: by equivariance a Bohm point drawn from |psi|^2 enters an absorber with the probability the
    absorber takes (points are absorbed at the rate 2 W, ``_absorb``). The double slit with 300 points until the wave
    has left: the counts per absorber (screen 67 of 300 against 55.5 expected; over ten seeds 56.8 on average) pass the
    run's binomial 5-sigma check, and the control (8 points, order-16 interpolation, 4x tighter steps) stays within
    half a grid step (median). Negative control: points moved at half their velocity are still in flight when the
    probability has been absorbed: the registration check fails."""
    h = _double_slit_with(300)
    _run_until(h, 40.0)
    c = h.checks()
    assert c["bohm_reg_o4"]["ok"] and c["bohm_acc_o4"]["ok"], (c["bohm_reg_o4"], c["bohm_acc_o4"])
    B = h.sim.bohm["o4"]
    assert not B["fly"].any() and c["bohm_acc_o4"]["value"] < 0.5 * h.sim.d
    orig = bohm.advance_ensemble

    def slow(grid, snaps, X, h_, *a, **k):
        X1, s = orig(grid, snaps, X, h_, *a, **k)
        return X + 0.5 * (X1 - X), s
    monkeypatch.setattr(P.bohm, "advance_ensemble", slow)
    h2 = _double_slit_with(300)
    _run_until(h2, 40.0)
    assert not h2.checks()["bohm_reg_o4"]["ok"]


def test_bohm_control_catches_an_inaccurate_interpolation(monkeypatch):
    """Review B6-Q1: a free electron of lambda = 1 nm on the 0.31-nm grid (k d = 1.96, admitted) with 30 Bohm points.
    The demodulated interpolation (engine default) keeps the ensemble within half a grid step of its control; the
    plain order-8 interpolation of the ensemble (the control kept) errs by its remainder at k d ~ 2 (0.13 of the
    velocity, review s04: 2 nm over 30 nm) and the run's check fails."""
    def world():
        pr = {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open",
              "scene": {"format": "lfscene", "version": 1, "objects": [
                  {"type": "packet", "label": "Electron",
                   "values": {"x": -15.0, "wavelength": 1.0, "sx": 2.5, "sy": 2.5, "bohm": 30}}]}}
        h = Harness(V, None, pr)
        _run_until(h, 4.0)
        return h
    h = world()
    assert h.checks()["bohm_acc_o1"]["ok"], h.checks()["bohm_acc_o1"]
    orig = bohm.advance_ensemble

    def plain(grid, snaps, X, h_, *a, **k):
        if "order" not in k:  # the ensemble, not its control
            k["demodulate"] = False
        return orig(grid, snaps, X, h_, *a, **k)
    monkeypatch.setattr(P.bohm, "advance_ensemble", plain)
    h2 = world()
    c = h2.checks()["bohm_acc_o1"]
    assert not c["ok"] and c["value"] > 0.5 * h2.sim.d, c


def test_a_jump_keeps_the_registered_bohm_points():
    """Review B6-Q5: an environment (20/ps) with the double slit's 300 points: at the jump the points registered so far
    stay registered and only those in flight are drawn again (their number unchanged); at the end the counts still
    follow the absorbed probabilities (the run's check, epoch by epoch)."""
    env = {"type": "env", "label": "Environment", "values": {"rate": 20.0, "length": 2.0, "region": "all"}}
    h = _double_slit_with(300, seed=4, extra=env)
    sim, qs = h.sim, h.sim.qs
    seen = []
    orig = P.Simulation._redraw_flight

    def traced(self, oid):
        B = self.bohm[oid]
        before = (list(B["key"]), int(B["fly"].sum()))
        orig(self, oid)
        seen.append((before, list(B["key"]), int(B["fly"].sum())))
    P.Simulation._redraw_flight = traced
    try:
        _run_until(h, 40.0)
    finally:
        P.Simulation._redraw_flight = orig
    assert qs.particles[1].jumps and seen
    for (keys0, fly0), keys1, fly1 in seen:
        assert keys1 == keys0 and fly1 == fly0
    assert any(k is not None for (k0, _), _, _ in seen for k in k0)
    assert len(sim.bohm["o5"]["epochs"]) == 1 + len(seen)
    assert h.checks()["bohm_reg_o5"]["ok"], h.checks()["bohm_reg_o5"]


def test_a_strong_environment_shortens_the_step():
    """Review B6-Q6: the scene refuses lambda dt > 0.05; the wrapper shortens the step in the same change. An
    environment of 1000/ps in the tunnel preset (lambda dt was 0.0675) and a change 10 -> 1000/ps are taken, with
    dt = 2^floor(log2(0.05/lambda)); a neutron's long step (16 units) is shortened for the palette's default
    environment."""
    for how in ("add", "set"):
        h = Harness(V, "tunnel")
        h.cmd("scene", op="add", type="env", values={"rate": 1000.0 if how == "add" else 10.0, "length": 2.0,
                                                     "region": "all"})
        if how == "set":
            eid = [o for o in h.sim.objects if h.sim.objects[o]["type"] == "env"][0]
            h.cmd("scene", op="set", id=eid, values={"rate": 1000.0})
        lam = 1000.0 * 1e12 * TU
        assert not h.errors(), h.errors()
        assert h.sim.qs.dt == 2.0 ** math.floor(math.log2(QS.LOC_MAX_STEP / lam)) and lam * h.sim.qs.dt <= 0.05
    h = Harness(V, None, {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open"})
    h.cmd("scene", op="add", type="packet", values={"species": "neutron", "x": -10.0, "wavelength": 2.0})
    assert h.sim.qs.dt == 16.0
    h.cmd("scene", op="add", type="env", values={})
    assert not h.errors() and 10e12 * TU * h.sim.qs.dt <= 0.05


def test_a_field_is_not_changed_under_a_charged_packet():
    """Review B6-Q3: in the cyclotron preset the inspector's change of Bz while the electron orbits is refused with the
    reason (the induced field of the switch depends on the magnet, the Landau gauge does not give it); clearing the
    scene removes the particle first, so it still works; a closed window refuses the electron next to the field
    (B6-Q2)."""
    h = Harness(V, "cyclotron")
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 5)
    fid = [o for o in h.sim.objects if h.sim.objects[o]["type"] == "bfield"][0]
    h.cmd("scene", op="set", id=fid, values={"Bz": 50.0})
    assert any("the field cannot be changed" in e for e in errs(h)), errs(h)
    assert h.sim.objects[fid]["values"]["Bz"] == 100.0
    n_err = len(h.errors())
    h.cmd("scene", op="clear")
    assert len(h.errors()) == n_err and not h.sim.objects and not h.sim.qs.objects and not h.sim.qs.particles
    pr = copy.deepcopy(SCHEMA.presets["cyclotron"]["params"])
    pr["edges"] = "closed"
    with pytest.raises(ValueError, match="closed"):
        Harness(V, None, pr)


def test_the_presets_show_their_effects():
    """Review B6-Q9, Q10. Which path: the marker fills the upper slit's 12-nm channel (c = 5.6 % of E): the screen's
    visibility near the centre falls from 0.94 to 0.18 (measured), and the transmitted wave's marker turns to
    P(1) = 0.95. Aharonov-Bohm: the tube inside the wall between the slits gives the half-fringe shift: the centre is
    a minimum (< 1e-3 of the peak) and the pattern is mirror symmetric (to 1e-3 of the peak; the earlier tube behind the
    wall gave 0.720 against 0.659 at y = -+8.1 nm)."""
    def screen(pr):
        h = Harness(V, None, pr)
        _run_until(h, 45.0)
        qs = h.sim.qs
        det = [k for k in qs.absorbed(1) if k.startswith("detector")][0]
        prof = np.sum(backend.to_numpy(qs.particles[1].acc) * qs._arr["u"][det], axis=0)
        return qs.grid.axes[1], prof
    vis = {}
    for marker in (True, False):
        pr = copy.deepcopy(SCHEMA.presets["which_path"]["params"])
        if not marker:
            pr["scene"]["objects"] = [o for o in pr["scene"]["objects"] if o["type"] != "marker"]
        y, prof = screen(pr)
        sel = np.abs(y) < 6
        vis[marker] = (prof[sel].max() - prof[sel].min()) / (prof[sel].max() + prof[sel].min())
    assert vis[True] < 0.25 and vis[False] > 0.9, vis
    y, prof = screen(copy.deepcopy(SCHEMA.presets["aharonov_bohm"]["params"]))
    pk = prof.max()
    i0 = int(np.argmin(np.abs(y)))  # y = 0 is a sample; the pattern against its mirror image y -> -y
    j = np.arange(1, int(20 / (y[1] - y[0])))
    assert prof[i0] < 1e-3 * pk
    assert np.max(np.abs(prof[i0 + j] - prof[i0 - j])) < 1e-3 * pk


def test_the_inspector_shows_a_shapes_actual_height():
    """Review B6-Q14: the tunnel preset's barrier, 1.5 nm wide with 1-nm edges, reaches 0.473 eV, not its nominal
    0.5 eV (erf(w / (2 eps)) of it)."""
    h = Harness(V, "tunnel")
    h.runner._frame(0.0)
    now = h.of("frame")[-1]["now"]["o1"]
    w = 1.05 * QS.edge_min(80 / 256)
    assert now["largest height of the potential, eV"] == pytest.approx(0.5 * math.erf(1.5 / (2 * QS.edge_eps(w))),
                                                                      rel=1e-12)
    assert now["largest height of the potential, eV"] == pytest.approx(0.4733, abs=1e-4)


def test_a_refused_change_leaves_the_scene_as_it_was():
    h = Harness(V, "tunnel")
    before = [o["id"] for o in h.of("scene")[-1]["objects"]]
    h.cmd("scene", op="add", type="packet", values={"wavelength": 0.05})  # beyond the grid wherever it is placed
    assert any("grid" in e for e in errs(h)), errs(h)
    assert [o["id"] for o in h.of("scene")[-1]["objects"]] == before
    assert set(h.sim.qs.particles) == {1}


def test_a_change_at_the_current_moment_keeps_the_balance():
    h = Harness(V, "tunnel")
    run(h, h.sim.t + 2.0 * h.sim.default_speed, 10)
    h.cmd("scene", op="set", id="o1", values={"V": 0.2})
    h.cmd("scene", op="add", type="detector", values={"x": 20.0, "sx": 4.0})
    run(h, h.sim.t + 4.0 * h.sim.default_speed, 20)
    assert not h.errors() and not failed(h)
    ab = h.of("frame")[-1]["now"]["o3"]
    assert "“Detector (absorbing)" in render(ab["absorbed"]), ab


def test_the_scene_file_starts_the_same_set_up():
    h = Harness(V, "double_slit")
    h.cmd("scene", op="export")
    sc = h.of("scene_export")[-1]["scene"]
    h2 = Harness(V, None, {**sc["laws"], "scene": sc})
    a = [(o["type"], o["label"], o["values"]) for o in h.sim.objects.values()]
    b = [(o["type"], o["label"], o["values"]) for o in h2.sim.objects.values()]
    assert a == b
    assert np.array_equal(h.sim.qs.wave(1), h2.sim.qs.wave(1))


# --- regression tests for the framework review's F14-F16 (fixes made by the integrator in viz.py) ---------------------
def test_a_scene_file_saved_later_starts_the_engines_clock_at_its_time(monkeypatch):
    """Framework review F14: a world from a scene file saved at t > 0 starts the engine's clock at the file's time, so
    the header's first advance computes nothing. Negative control: without that line the first advance integrated
    the whole span from 0 (thousands of steps)."""
    h = Harness(V, "tunnel")
    run(h, h.sim.t + 2.0 * h.sim.default_speed, 5)
    h.cmd("scene", op="export")
    sc = h.of("scene_export")[-1]["scene"]
    assert sc["t"] > 0
    h2 = Harness(V, None, {**sc["laws"], "scene": sc})
    assert h2.sim.qs.steps == 0 and h2.sim.qs.t * TU == pytest.approx(sc["t"], rel=1e-12)
    orig = P.Simulation.start_scene

    def unclocked(self):  # undo the fix: the engine's clock back at 0 before the scene is built
        self.qs.t = 0.0
        orig(self)
    monkeypatch.setattr(P.Simulation, "start_scene", unclocked)
    h3 = Harness(V, None, {**sc["laws"], "scene": sc})
    assert h3.sim.qs.steps >= int(sc["t"] / TU / h3.sim.qs.dt) - 1 > 500


def test_overflowing_values_are_refused_and_the_waves_stay_finite():
    """Framework review F15: a value that would overflow in the engine's units is refused (the schema's bound
    |V| <= 1e4 eV; an object whose values on the grid are not finite by ``_finite``) and the particle's wave stays
    finite."""
    h = Harness(V, "tunnel")
    h.cmd("scene", op="add", type="box", values={"x": 10.0, "sx": 2.0, "V": 1e308})
    assert h.errors()
    with pytest.raises(ValueError, match="not finite"):
        h.sim._finite(QS.Box([10.0, 0.0], [2.0, None], math.inf, 1.0))
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 3)
    assert np.isfinite(h.sim.qs.norm(1)) and np.all(np.isfinite(h.sim.qs.wave(1)))


def test_changing_only_the_bohm_count_keeps_the_wave():
    """Framework review F16: a change of only a particle's number of Bohm points draws the points again and keeps the
    wave (the same <x>, the same array); a change of its width replaces the packet."""
    h = Harness(V, "double_slit")
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 5)
    w0, x0 = h.sim.qs.wave(1).copy(), mean_pos(h, "o4")
    h.cmd("scene", op="set", id="o4", values={"bohm": 20})
    h.runner._frame(0.0)
    assert np.array_equal(h.sim.qs.wave(1), w0) and np.array_equal(mean_pos(h, "o4"), x0)
    assert h.sim.bohm["o4"]["n"] == 20
    h.cmd("scene", op="set", id="o4", values={"sx": 2.0})
    h.runner._frame(0.0)
    assert not h.errors() and not np.allclose(mean_pos(h, "o4"), x0, atol=1e-3)


# --- review UX-ui U3, U4, U8, U12, U13 and UX-params P28, P29, P30 ---------------------------------------------------
def test_scene_changes_are_fast_and_retune_only_what_they_change():
    """U3/P30: in the double slit every palette click froze the world for 18 to over 30 s (the absorbers re-tuned through
    440 000 pure-Python transfer-matrix steps after every change). Now: a box far from everything, the packet moved and a
    rename take no new tuning (the strength chosen for the same waves and absorber is kept) and each well under a second;
    a new detector or a new wavelength tunes once in vectorised matrices. Negative control: the cache emptied, the same
    change computes the same strength (the cache changes the time, not the result)."""
    import time
    h = Harness(V, "double_slit")
    run(h, h.sim.t + h.sim.default_speed / 10, 2)
    pid = next(k for k, o in h.sim.objects.items() if o["type"] == "packet")
    for args in ({"op": "add", "type": "box", "values": {"x": 20.0, "y": 20.0}},
                 {"op": "set", "id": pid, "values": {"x": -19.0}},
                 {"op": "add", "type": "detector", "values": {"x": 20.0, "y": -20.0}},
                 {"op": "set", "id": pid, "values": {"wavelength": 2.2}},
                 {"op": "add", "type": "marker", "values": {"x": 2.0, "y": 5.0}}):
        t0 = time.perf_counter()
        h.cmd("scene", **args)
        assert time.perf_counter() - t0 < 1.0 and not h.errors(), (args, h.errors())
    W = float(h.sim.qs.edges.strength)
    h.sim._cache.clear()
    assert h.sim._auto_W() == pytest.approx(W, rel=0.45)  # the same choice (within the 1.4 ratio of _tune_dt)
    assert h.sim._auto_W() == h.sim._auto_W()


def test_a_packet_from_the_palette_lands_outside_the_wall():
    """U4: "+ Particle" in the double slit put the packet at (0, 0), inside the 3 eV wall, and the scene refused it (with a
    reason about a "well −3 eV" not in the scene, U13). ``place`` moves it upstream to the first point the scene takes,
    and says so; a packet that fits nowhere is refused with what to change."""
    h = Harness(V, "double_slit")
    v = h.sim.place("packet", {})
    assert v["x"] < -2.0 and abs(v["y"]) < 1e-12
    h.cmd("scene", op="add", type="packet", values=v)
    assert not h.errors(), h.errors()
    assert any(e.get("notify") and "nearest free place" in render(e["text"]) for e in h.of("event"))
    # through the framework (as the palette sends it): the same
    h.cmd("scene", op="add", type="packet", values={"species": "neutron", "wavelength": 1.5})
    assert not h.errors(), h.errors()
    # a packet inside the wall placed by hand without ``place`` (a file): refused in the scene's terms
    h2 = Harness(V, "double_slit")
    with pytest.raises(ValueError) as e:
        h2.sim._add("packet", {"x": 0.0, "y": 3.0})
    assert "inside “Wall with two slits”" in str(e.value) and "What to change" in str(e.value), str(e.value)
    assert "well" not in str(e.value)


def test_objects_wholly_outside_the_window_are_refused_and_far_packets_too():
    """U8/P29: a box, a detector, a trap at 10^6 nm were taken without a word; a packet added there made the wave NaN
    (0/0 in the normalisation) and the next Bohm change crashed in «Probabilities contain NaN»."""
    h = Harness(V, "tunnel")
    n0 = len(h.sim.objects)
    for typ, vals in (("box", {"x": 1e6}), ("detector", {"x": -1e6}), ("trap", {"x": 1e6}), ("ball", {"y": 1e6}),
                      ("flux", {"x": -1e6})):
        n_err = len(h.errors())
        h.cmd("scene", op="add", type=typ, values=vals)
        assert len(h.errors()) == n_err + 1 and "outside the window" in errs(h)[-1], (typ, errs(h)[n_err:])
    assert len(h.sim.objects) == n0
    h.cmd("scene", op="add", type="box", values={"x": 39.0, "sx": 6.0})  # partly outside: taken, with a note
    assert len(h.sim.objects) == n0 + 1 and any("partly beyond the window's edge" in render(e["text"])
                                                for e in h.of("event"))
    pid = next(k for k, o in h.sim.objects.items() if o["type"] == "packet")
    h.cmd("scene", op="set", id=pid, values={"x": 1e6})
    assert "outside the window" in errs(h)[-1]
    run(h, h.sim.t + h.sim.default_speed / 5, 3)
    assert all(np.isfinite(c["value"]) for c in h.of("check") if isinstance(c.get("value"), float))
    # the guard of _draw itself: no wave (all absorbed) or a wave that is not finite is said, not numpy's ValueError

    class FakeScene:
        grid = h.sim.qs.grid

        def density(self, pid):
            return np.zeros(self.grid.shape)

    fake = type("F", (), {})()
    fake.qs, fake.rng, fake.ndim = FakeScene(), np.random.default_rng(1), 2
    with pytest.raises(ValueError, match="the particle has no wave in the window"):
        P.Simulation._draw(fake, 1, 3)
    FakeScene.density = lambda self, pid: np.full(self.grid.shape, np.nan)
    with pytest.raises(ValueError, match="no longer finite"):
        P.Simulation._draw(fake, 1, 3)


def test_a_refused_removal_keeps_the_object_and_clear_still_works():
    """P28: removing the field of the cyclotron while its electron is in the window is refused (the engine's reason);
    before, the object had already lost its reference and every later removal or "Clear scene" failed with
    "Scene: 'o1'". Now the refusal comes before anything is touched, the field stays and works, and "Clear scene"
    removes the particle first, then the field: all of it."""
    h = Harness(V, "cyclotron")
    run(h, h.sim.t + h.sim.default_speed / 5, 3)
    fid = next(k for k, o in h.sim.objects.items() if o["type"] == "bfield")
    h.cmd("scene", op="remove", id=fid)
    assert "charged particle" in errs(h)[-1] and fid in h.sim.objects and fid in h.sim.ref
    assert "bfield" in (h.of("scene")[-1].get("palette_state") or {})  # a second field cannot be added either
    n_err = len(h.errors())
    h.cmd("scene", op="clear")
    assert len(h.errors()) == n_err and not h.sim.objects and not h.sim.ref and not h.sim.qs.objects
    run(h, h.sim.t + h.sim.default_speed / 5, 2)
    assert len(h.errors()) == n_err


def test_the_window_edges_change_at_the_current_moment():
    """U12: open (absorbing) and closed (periodic) edges are live: the world goes on, what the layers absorbed stays
    absorbed (norm + absorbed = 1 throughout), the scene file takes the edges in force. With a charged particle next to a
    field closing them is refused (a closed window cannot hold the field's gauge) and nothing changes."""
    h = Harness(V, "tunnel")
    run(h, h.sim.t + 3 * h.sim.default_speed, 12)
    h.set(edges="closed")
    assert not h.errors(), h.errors()
    assert h.sim.qs.edges is None and h.of("live")[-1]["values"]["edges"] == "closed"
    run(h, h.sim.t + 3 * h.sim.default_speed, 12)
    h.set(edges="open")
    run(h, h.sim.t + 3 * h.sim.default_speed, 12)
    assert not h.errors() and h.sim.qs.edges is not None
    bal = [c for c in h.of("check") if c["id"].startswith("balance_")]
    assert bal and all(c["ok"] for c in bal)
    h.cmd("scene", op="export")
    assert h.of("scene_export")[-1]["scene"]["laws"]["edges"] == "open"
    h2 = Harness(V, "cyclotron")
    h2.set(edges="closed")
    assert "the window's edges were not changed" in errs(h2)[-1] and h2.sim.qs.edges is not None


# --- plan P16.1: the grid and the window change in the same world (LB1) -------------------------------------------
def _ev(h):
    return [render(e["text"]) for e in h.of("event")]


def test_the_grid_and_the_window_change_live_in_the_same_world():
    """The grid (points per axis) and the window's size are live: the double slit run, refined 256 -> 384, the window
    enlarged 80 -> 100 nm (both changed: the interpolant evaluated; 256 points there are refused: the wall keeps its
    0.995-nm edge), back to 80 nm and 256 points — one world throughout, the wave resampled exactly (the refined wave
    equals ``schrodinger_nd.resample`` of the old one; each event states the norm before and after — unchanged to
    round-off by the refinement — and <H> before and after), the absorbers and the time step re-tuned, the grid and the
    box sent to the view, the live values in force; the run goes on with every check passing (norm + absorbed = 1
    among them)."""
    h = Harness(V, "double_slit")
    run(h, h.sim.t + 2.0 * h.sim.default_speed, 8)
    w0 = h.sim.qs.wave(1).copy()
    h.set(n2="384")
    assert not h.errors(), h.errors()
    assert len(h.of("header")) == 1 and h.sim.qs.grid.shape == (384, 384) and h.sim.d == pytest.approx(80 / 384)
    text = _ev(h)[-1]
    assert "resampled exactly (by padding the spectrum with zeros)" in text and "(unchanged to within round-off)" in text, text
    from lfphys.core.quantum import schrodinger_nd as S
    old = S.Grid((256, 256), 80 / 256)
    assert np.max(np.abs(h.sim.qs.wave(1) - S.resample(w0, old, h.sim.qs.grid))) < 1e-14
    assert h.of("grid")[-1]["grid"]["n"] == [384, 384] and h.of("box")
    assert h.of("live")[-1]["values"]["n2"] == "384"
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 6)
    h.set(size=100.0)
    assert not h.errors(), h.errors()
    assert h.sim.size == 100.0 and h.sim.d == pytest.approx(100 / 384) and h.sim.edge_w == pytest.approx(10.0)
    assert "zeros beyond the former window" in _ev(h)[-1]
    n_err = len(h.errors())
    h.set(n2="256")  # the wall's 0.995-nm edge on a 0.39-nm grid: refused (its physical edge is kept)
    assert len(h.errors()) == n_err + 1 and "“Wall with two slits”" in errs(h)[-1]
    n_err += 1
    h.set(size=80.0)
    h.set(n2="256")
    assert len(h.errors()) == n_err, h.errors()
    assert h.sim.qs.grid.shape == (256, 256) and h.sim.size == 80.0
    run(h, h.sim.t + 6.0 * h.sim.default_speed, 30)
    assert len(h.errors()) == n_err and not failed(h), {k: h.checks()[k] for k in failed(h)}
    bal = [c for c in h.of("check") if c["id"] == "balance_o4"]
    assert bal[-1]["ok"] and len(h.of("header")) == 1


def test_a_live_grid_change_is_refused_with_the_measured_fraction():
    """A coarser grid under the wave's spectrum (the tunnel's electron, lambda = 2 nm: a window of 200 nm on 256 points
    leaves 4.4 sigma_k of its band — more than 1e-6 of its norm beyond), a window that would cut the packet off (30 nm),
    and an object's edge the coarser grid cannot resolve (the double slit's wall, resolved at 0.995 nm on the 0.31-nm
    grid): each refused in the owner's terms with the number and what to change, and nothing changes (the grid, the
    wave, the live values)."""
    h = Harness(V, "tunnel")
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
    w0 = h.sim.qs.wave(1).copy()
    for vals, what in (({"size": 200.0}, "beyond the new grid's band"), ({"size": 30.0}, "outside the new window")):
        n = len(h.errors())
        h.set(**vals)
        assert len(h.errors()) == n + 1 and "Grid not changed" in errs(h)[-1] and what in errs(h)[-1], \
            errs(h)[-1]
        assert h.sim.qs.grid.shape == (256, 256) and np.array_equal(h.sim.qs.wave(1), w0)
        assert h.of("live")[-1]["values"]["size"] == 80.0
    h2 = Harness(V, "double_slit")
    h2.set(n2="192")
    assert "“Wall with two slits”" in errs(h2)[-1] and "edge" in errs(h2)[-1], errs(h2)[-1]
    assert h2.sim.qs.grid.shape == (256, 256)


def test_objects_keep_their_physical_edges_across_a_live_grid_change():
    """An edge set to 0 is «the sharpest the grid resolves» when the object gets it; a live change of the grid keeps
    the object as it is (the potential must not change with the numerics): after a refinement the double slit's wall
    keeps its 0.995-nm edge, also when it is moved later; a new object takes the sharper edge of the finer grid."""
    h = Harness(V, "double_slit")
    qid = h.sim.ref["o1"][1]
    e0 = h.sim.qs.objects[qid].edge
    assert e0 == pytest.approx(1.05 * QS.edge_min(80 / 256))
    h.set(n2="512")
    assert not h.errors(), h.errors()
    assert h.sim.qs.objects[qid].edge == e0
    h.cmd("scene", op="edit", id="o1", values={"position": 1.0})
    assert not h.errors(), h.errors()
    assert h.sim.qs.objects[h.sim.ref["o1"][1]].edge == e0 and h.sim.qs.objects[h.sim.ref["o1"][1]].position == 1.0
    h.cmd("scene", op="add", type="box", values={"x": 20.0, "y": 25.0})
    new = [o for o in h.sim.objects.values() if o["type"] == "box"][0]
    assert h.sim.qs.objects[h.sim.ref[new["id"]][1]].edge == pytest.approx(1.05 * QS.edge_min(80 / 512))


# --- plan P16.2: handles, positions, a packet's drag and throw, objects moved -------------------------------------
def test_every_type_declares_its_handles_and_every_positioned_object_is_reported():
    """The palette's handles (sent in the header), and ``at`` in every frame: a packet at its wave's mean position, a
    wall, a step and a flux plane at their place on their axis, the others at their centre (world units, 3 numbers)."""
    h = Harness(V, "double_slit")
    pal = {o["type"]: o.get("handles") for o in h.of("header")[0]["playground"]["palette"]}
    assert pal["packet"] == {"position": ["x", "y"], "velocity": ["vx", "vy"], "size": "sx", "velocity_max": "v_max"}
    for t in ("slit_wall", "step", "plane"):
        assert pal[t]["position"] == {"param": "position", "axis_param": "axis"}
    assert all(pal[t] and pal[t].get("position") for t in pal)
    h.cmd("scene", op="add", type="flux", values={"x": 10.0, "y": 20.0})
    run(h, h.sim.t + 0.5 * h.sim.default_speed, 3)
    at = h.of("frame")[-1]["at"]
    assert at["o1"] == [0.0, 0.0, 0.0] and at["o2"] == [30.0, 0.0, 0.0] and at["o5"] == [10.0, 20.0, 0.0]
    assert at["o3"][0] == pytest.approx(h.sim.qs.planes[h.sim.ref["o3"][1]]["position"])
    assert np.allclose(at["o4"][:2], mean_pos(h, "o4"), atol=1e-12) and at["o4"][2] == 0.0
    h3 = Harness(V, "ball_3d")
    h3.runner._frame(0.0)
    at = h3.of("frame")[-1]["at"]
    assert at["o1"] == [4.0, 0.0, 0.0] and len(at["o2"]) == 3


def test_dragging_a_packet_moves_its_wave_and_keeps_the_norm():
    """A drag (scene op «edit» with the packet's position handles) prepares the same wave in the new place: its mean
    position becomes the point dropped, the wave is the old one translated exactly (``schrodinger_nd.translate``), the
    norm and what was absorbed are kept, its Bohm points move with it; the edit is cheap (no other object is
    evaluated again: well under a second); the event states the preparation."""
    import time
    from lfphys.core.quantum import schrodinger_nd as S
    h = _double_slit_with(20)
    run(h, h.sim.t + 3.0 * h.sim.default_speed, 10)
    qs = h.sim.qs
    w0, n0, A0 = qs.wave(1).copy(), qs.norm(1), qs.absorbed(1)
    r0 = mean_pos(h, "o4")
    X0 = h.sim.bohm["o4"]["X"].copy()
    fly = h.sim.bohm["o4"]["fly"].copy()
    target = np.array([-22.0, 6.0])
    t0 = time.perf_counter()
    h.cmd("scene", op="edit", id="o4", values={"x": float(target[0]), "y": float(target[1])})
    dt = time.perf_counter() - t0
    assert not h.errors() and dt < 1.0, (h.errors(), dt)
    h.runner._frame(0.0)
    assert np.allclose(mean_pos(h, "o4"), target, atol=1e-9)
    assert np.max(np.abs(qs.wave(1) - S.translate(w0, qs.grid, target - r0))) < 1e-13
    assert qs.norm(1) == pytest.approx(n0, rel=1e-13) and qs.absorbed(1) == pytest.approx(A0, rel=1e-13)
    assert np.allclose(h.sim.bohm["o4"]["X"][fly], X0[fly] + (target - r0), atol=1e-12)
    assert "the same wave moved by" in _ev(h)[-2], _ev(h)[-3:]
    run(h, h.sim.t + 2.0 * h.sim.default_speed, 10)
    assert not h.errors() and not failed(h), {k: h.checks()[k] for k in failed(h)}


def test_throwing_a_packet_gives_it_the_momentum_of_the_drag_velocity():
    """A throw (positions and velocity handles together): the velocity v (nm per second of the world's time, the
    player's unit) becomes k0 = m v / hbar — the wave's mean kinetic wavenumber after the change — and the packet's
    wavelength and direction follow (lambda = 2 pi / |k0|); the event says so. For a neutron (mass m_n) the same velocity
    is a 1838.7 times larger k0. Negative control: a velocity the grid cannot carry, typed in the inspector, is refused
    and nothing changes (a throw beyond the limit is clamped to v_max by the framework: next test)."""
    h = Harness(V, "tunnel")
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
    r = list(mean_pos(h, "o3"))
    v = (2.0e14, -1.0e14)
    h.cmd("scene", op="edit", id="o3", values={"x": r[0], "y": r[1], "vx": v[0], "vy": v[1]})
    assert not h.errors(), h.errors()
    k0 = np.array(v) * TU * 1.0  # m = m_e = 1 in the scene's units
    o = h.sim.qs.observables(1)
    assert np.allclose(o["k"], k0, atol=1e-9)
    vals = h.sim.objects["o3"]["values"]
    assert vals["wavelength"] == pytest.approx(2 * math.pi / np.linalg.norm(k0), rel=1e-9)
    assert vals["theta"] == pytest.approx(math.degrees(math.atan2(k0[1], k0[0])), rel=1e-9)
    assert "k₀ = m v/ħ" in _ev(h)[-2]
    w = h.sim.qs.wave(1).copy()
    h.cmd("scene", op="set", id="o3", values={"vx": 1e16})  # typed: not clamped by the player's throw limit
    assert "grid" in errs(h)[-1] and np.array_equal(h.sim.qs.wave(1), w)
    assert h.sim.objects["o3"]["values"]["vx"] == pytest.approx(v[0])
    hn = Harness(V, "tunnel")
    hn.cmd("scene", op="set", id="o3", values={"species": "neutron", "wavelength": 0.0})
    hn.cmd("scene", op="edit", id="o3", values={"vx": 300.0 * 1e9, "vy": 0.0})  # 300 m/s
    assert not hn.errors(), hn.errors()
    kn = hn.sim.qs.observables(1)["k"][0]
    assert kn == pytest.approx(300.0 * 1e9 * TU * hn.sim.qs.particles[1].species.mass, rel=1e-9)
    assert hn.sim.qs.particles[1].species.mass == pytest.approx(1838.68366, rel=1e-6)


def test_the_throws_limit_is_the_speed_the_grid_carries_here():
    """``handles.velocity_max`` names the packet's hidden parameter v_max: the speed a throw is taken at in every
    direction now, from the wave itself (``Scene.kick_reach``, VMAX_MARGIN inside it; for a fresh packet the rule
    sqrt((k + 6 sigma_k)^2 + 2 m dV) = 2/3 pi/d, here to a grid wavenumber step), in nm/s; a throw just below it is
    taken as asked (no clamp by the world), a throw above it is clamped to it (the framework), the same speed typed in
    the inspector is refused by the scene with the limit in that direction; it follows a live change of the grid (a
    finer grid carries faster packets); every parameter carries its unit."""
    h = Harness(V, "tunnel")
    pal = {o["type"]: o for o in h.of("header")[0]["playground"]["palette"]}
    assert pal["packet"]["handles"].get("velocity_max") == "v_max"
    units = {q["id"]: q["unit"] for q in pal["packet"]["params"]}
    assert render(units["vx"]) == "nm/s" and render(units["x"]) == "nm" and render(units["wavelength"]) == "nm" \
        and units["theta"] == "°"
    assert all(q["unit"] for t in pal.values() for q in t["params"] if q["type"] in ("float", "int")), \
        [(t["type"], q["id"]) for t in pal.values() for q in t["params"] if q["type"] in ("float", "int") and not q["unit"]]
    v = h.sim.objects["o3"]["values"]
    k = P.VMAX_MARGIN * ((2 / 3) * math.pi / h.sim.d - 6 / (2 * 2.5))  # dV = 0 at the packet (the barrier ahead)
    dkg = 2 * math.pi / 80.0
    assert abs(v["v_max"] * TU - k) < dkg
    h.cmd("scene", op="edit", id="o3", values={"vx": 0.9 * v["v_max"], "vy": 0.0})
    assert not h.errors(), h.errors()
    assert "limited" not in _ev(h)[-2] and h.sim.qs.observables(1)["k"][0] == pytest.approx(0.9 * v["v_max"] * TU,
                                                                                                rel=1e-6)
    vm0 = h.sim.objects["o3"]["values"]["v_max"]
    h.cmd("scene", op="edit", id="o3", values={"vx": 3.0 * vm0, "vy": 0.0})  # a throw: clamped to v_max, said
    assert not h.errors(), h.errors()
    assert h.sim.qs.observables(1)["k"][0] == pytest.approx(vm0 * TU, rel=1e-6)
    h.cmd("scene", op="set", id="o3", values={"vx": 3.0 * vm0})  # typed: refused by the scene, with the limit
    assert "grid" in errs(h)[-1] and "no faster than" in errs(h)[-1], errs(h)[-1]
    vm = h.sim.objects["o3"]["values"]["v_max"]
    h.set(n2="384")
    assert h.sim.objects["o3"]["values"]["v_max"] > 1.4 * vm
    ht = Harness(V, "trap")  # in the trap the displaced packet can turn its potential energy into motion: a lower limit
    vt = ht.sim.objects["o2"]["values"]["v_max"]
    kt = (2 / 3) * math.pi / ht.sim.d - 6 / (2 * 1.38)
    assert 0 < vt < 0.95 * kt / TU


def test_moving_a_wall_or_a_detector_moves_its_potential_now():
    """Dragging the double slit's wall (its axis handle) and the screen moves their potentials at the current moment:
    the wave is not prepared again (it goes on as it was), the absorbed probability stays, the run's checks pass; a
    registered (absorbed) particle dragged back is prepared afresh and said so."""
    h = Harness(V, "double_slit")
    run(h, h.sim.t + 2.0 * h.sim.default_speed, 8)
    w = h.sim.qs.wave(1).copy()
    h.cmd("scene", op="edit", id="o1", values={"position": 2.0})
    h.cmd("scene", op="edit", id="o2", values={"x": 25.0, "y": 0.0})
    assert not h.errors(), h.errors()
    assert np.array_equal(h.sim.qs.wave(1), w)
    assert h.sim.qs.objects[h.sim.ref["o1"][1]].position == 2.0
    assert h.sim.qs.objects[h.sim.ref["o2"][1]].lo[0] == pytest.approx(23.0)
    run(h, h.sim.t + 4.0 * h.sim.default_speed, 20)
    assert not h.errors() and not failed(h)
    h2 = Harness(V, "trap")
    h2.runner._frame(0.0)
    h2.sim.qs.particles[1].active, h2.sim.qs.particles[1].psi = False, None  # as if a detector had taken it
    h2.cmd("scene", op="edit", id="o2", values={"x": 3.0, "y": 0.0})
    assert not h2.errors() and h2.sim.qs.particles[1].active and "a new packet was prepared" in _ev(h2)[-2]


# --- plan P16.3: measurables ------------------------------------------------------------------------------------------
def test_measurables_are_declared_and_every_frame_carries_their_values():
    """``measurables`` in every scene message (labels and units as texts; the world's totals, each particle's, each
    plane's and detector's); every frame's ``meas`` holds a value for each, in the units declared, the same as the
    scene's own readings: the probability in the window and absorbed, <H> (eV, as the energy check), <x> (nm, as
    ``now``), the detector's absorbed probability, a plane's flux now (1/fs); a quantity without a value is NaN with its
    reason (no Bohm points)."""
    h = Harness(V, "double_slit")
    run(h, h.sim.t + 6.0 * h.sim.default_speed, 20)
    ms = h.of("scene")[-1]["measurables"]
    ids = {m["id"] for m in ms}
    assert {"norm", "absorbed", "regrid", "o4.norm", "o4.E", "o4.x", "o4.kx", "o4.v", "o2.P", "o2.in", "o2.n", "o3.J",
            "o3.F", "o3.J.o4"} <= ids
    assert all(is_t(m["label"]) and (is_t(m["unit"]) or m["unit"] in ("", "σ")) for m in ms)
    assert render(next(m for m in ms if m["id"] == "o4.E")["unit"]) == "eV"
    f = h.of("frame")[-1]
    meas = f["meas"]
    assert set(meas) == ids
    qs = h.sim.qs
    assert meas["o4.norm"] == pytest.approx(qs.norm(1), rel=1e-12)
    assert meas["o4.x"] == pytest.approx(f["now"]["o4"]["⟨x⟩, nm"], rel=1e-12)
    assert meas["o2.P"] == pytest.approx(qs.absorbed(1).get(f"detector {h.sim.ref['o2'][1]}", 0.0), rel=1e-12)
    assert meas["norm"] + meas["absorbed"] + meas["regrid"] == pytest.approx(1.0, abs=1e-12) and meas["regrid"] == 0.0
    assert meas["o3.J"] == pytest.approx(qs.particles[1].planes[h.sim.ref["o3"][1]]["J"] * P.FS, rel=1e-12)
    E = h.sim.qs.checks()[1]["energy"]["E"] * EV
    assert meas["o4.E"] == pytest.approx(E, rel=1e-10)
    B = h.sim.bohm["o4"]
    assert meas["o2.n"] == sum(1 for k in B["key"] if k == f"detector {h.sim.ref['o2'][1]}")
    h2 = Harness(V, "which_path")  # no Bohm points: the count is NaN with its reason (NaN travels as null)
    h2.runner._frame(0.0)
    f2 = h2.of("frame")[-1]
    assert f2["meas"]["o3.n"] is None and "Bohm" in render(f2["meas_note"]["o3.n"])
    assert f2["meas"]["o4.coh"] == pytest.approx(f2["now"]["o4"]["marker: ⟨0|ρ|1⟩ (coherence)"], abs=1e-15)


def test_measurables_are_cheap():
    """The readings every frame costs (``measure``: one FFT per wave and a few sums) against the frame's own stepping:
    in the double slit at its default speed (about 6 scene steps per frame) below 25 % of the steps' time on this CPU
    — measured here, stated in the README; the sweeps call ``measure`` alone."""
    import time
    h = Harness(V, "double_slit")
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
    qs = h.sim.qs
    t0 = time.perf_counter()
    for _ in range(20):
        qs.advance(1)
    step = (time.perf_counter() - t0) / 20
    t0 = time.perf_counter()
    for _ in range(20):
        h.sim.measure()
    meas = (time.perf_counter() - t0) / 20
    per_frame = h.sim.default_speed / 20 / (qs.dt * TU)
    print(f"measure {meas * 1e3:.2f} ms, step {step * 1e3:.2f} ms, steps per frame {per_frame:.1f}")
    assert meas < 0.25 * per_frame * step


# --- plan P16.1: "New world" of the other dimension takes the scene over -------------------------------------------
def test_a_new_world_of_the_other_dimension_takes_over_what_makes_sense():
    """The plane's set-up is the section z = 0 of one that does not change along z: into space its box, detector and
    disk go as a prism, a slab and a cylinder along z (unbounded in z); out of space only what crosses the plane, as its
    section (a sphere of radius 4.5 at z = 1 as the disk of radius sqrt(4.5^2 - 1)); a box above the plane, a wall
    across z and a packet moving out of the plane are refused in the owner's terms and listed in the notice; the world's time
    goes on."""
    pr = {"dim": "2d", "n2": "128", "size": 40.0, "edges": "open", "scene": {"format": "lfscene", "version": 1,
          "objects": [{"type": "box", "values": {"x": 5.0, "sx": 2.0, "sy": 6.0, "V": 0.5}},
                      {"type": "ball", "values": {"x": -6.0, "y": 8.0, "radius": 5.0, "V": 0.4}},
                      {"type": "detector", "values": {"x": 15.0, "sx": 3.0}}]}}
    h = Harness(V, None, pr)
    run(h, h.sim.t + 0.2e-15, 2)
    t0 = h.sim.t
    h.cmd("new_world", params={"dim": "3d", "n3": "48", "size": 40.0}, carry=True)
    assert not h.errors(), h.errors()
    s3 = h.sim
    assert s3.ndim == 3 and s3.t == pytest.approx(t0) and len(s3.objects) == 3
    vals = {o["type"]: o["values"] for o in s3.objects.values()}
    assert vals["box"]["sz"] == 0.0 and vals["ball"]["shape"] == "cylinder" and vals["detector"]["sz"] == 0.0
    assert any("cylinder" in render(n["text"]) for n in h.of("notice"))
    # into space and back: the section z = 0
    s3_scene = {"format": "lfscene", "version": 1, "objects": [
        {"type": "ball", "label": "Ball", "values": {"x": 10.0, "y": 10.0, "z": 1.0, "radius": 4.5, "V": 0.3}},
        {"type": "box", "label": "High", "values": {"x": 0.0, "z": 10.0, "sz": 2.0, "V": 0.3}},
        {"type": "slit_wall", "label": "Across z", "values": {"axis": "2", "position": 14.0}},
        {"type": "packet", "label": "Upward", "values": {"x": -5.0, "phi": 30.0, "wavelength": 8.0, "sx": 2.0,
                                                        "sy": 2.0, "sz": 2.0}}]}
    h3 = Harness(V, None, {"dim": "3d", "n3": "48", "size": 40.0, "edges": "open", "scene": s3_scene})
    h3.cmd("new_world", params={"dim": "2d", "n2": "128", "size": 40.0}, carry=True)
    assert len(h3.sim.objects) == 1
    ball = list(h3.sim.objects.values())[0]["values"]
    assert ball["radius"] == pytest.approx(math.sqrt(4.5 ** 2 - 1.0))
    note = [n for n in h3.of("notice") if n.get("carry")][-1]
    refused = {render(o["label"]): " ".join(render(x) for x in o["notes"]).lower() for o in note["carry"]["objects"]
               if o["how"] == "refused"}
    assert "does not cross the plane" in refused["High"] and "across the z axis" in refused["Across z"]
    assert "out of the (x, y) plane" in refused["Upward"]


# --- the record: live changes are continued from a checkpoint and repeated by a replay -----------------------------
def _live_session(run, sim, play, steps):
    play(run, steps(sim, 0, 6))
    run.handle({"cmd": "set", "args": {"values": {"n2": "256"}}})
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o3", "values": {"x": -15.0, "y": 1.0}}})
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o3", "values": {"x": -15.0, "y": 1.0, "vx": 3.0e14,
                                                                             "vy": 0.5e14}}})
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o1", "values": {"x": 1.0, "y": 0.0}}})
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o2", "values": {"position": 8.0}}})
    run.handle({"cmd": "set", "args": {"values": {"size": 84.0}}})
    play(run, steps(sim, 6, 4))


def test_a_world_with_live_changes_continues_from_its_checkpoint_byte_for_byte(tmp_path):
    """The shared checkpoint test (``../tests/test_checkpoint.py``) with p02's live changes before the checkpoint: a
    refinement, a drag and a throw of the packet, the barrier and the flux plane moved, a larger window; a new process
    loads the checkpoint and goes on in the same frame steps: every message it emits is the original's, byte for byte
    (the resampled waves, the banked records, the objects' kept edges and the engine's array cache — dropped from the
    checkpoint and rebuilt — give the same world)."""
    import queue
    from test_checkpoint import _bytes, _checkpoint, _continue_in_new_process, _play, _steps
    from lfviz import registry
    from lfviz.sim import Runner
    viz = registry.load(V)
    params, errors = viz["schema"].resolve("tunnel", {"n2": "192"})
    assert not errors
    msgs = []

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    sim = viz["simulation"](params, 7, emit)
    run = Runner(sim, emit, queue.Queue())
    run._start_world()
    _live_session(run, sim, _play, _steps)
    assert not [m for m, _ in msgs if m.get("type") == "error"], [m["text"] for m, _ in msgs if m.get("type") == "error"]
    assert sim.qs.grid.shape == (256, 256) and sim.size == 84.0
    file = _checkpoint(run, tmp_path)
    ck = [m for m, _ in msgs if m.get("type") == "checkpoint"][-1]
    n0 = len(msgs)
    times = _steps(sim, 10, 6)
    _play(run, times)
    original = _bytes(msgs[n0:])
    continued = _continue_in_new_process(tmp_path, file, [], ck["t"], times)
    assert len(continued) == len(original)
    assert all(a == b for a, b in zip(original, continued))


def test_live_changes_are_deterministic_for_a_replay():
    """A replay repeats the recorded commands at their times (``Runner.restore``): the same session twice gives the same
    messages, byte for byte (no wall clock, no unseeded draw in a regrid, a move or a throw)."""
    import queue
    from test_checkpoint import _bytes, _play, _steps
    from lfviz import registry
    from lfviz.sim import Runner

    def session():
        viz = registry.load(V)
        params, _ = viz["schema"].resolve("tunnel", {"n2": "192"})
        msgs = []

        def emit(meta, blobs=None):
            msgs.append((meta, blobs))
        sim = viz["simulation"](params, 7, emit)
        run = Runner(sim, emit, queue.Queue())
        run._start_world()
        _live_session(run, sim, _play, _steps)
        _play(run, _steps(sim, 10, 4))
        return _bytes(msgs)
    a, b = session(), session()
    assert len(a) == len(b) and all(x == y for x, y in zip(a, b))


# --- review LB1-p02-ux ---------------------------------------------------------------------------------------------
def _free_world(x=-15.0, lam=2.5, extra=(), sig=2.5):
    return {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open", "scene": {"format": "lfscene", "version": 1,
            "objects": [{"type": "packet", "label": "Electron", "values": {"x": x, "wavelength": lam, "sx": sig,
                                                                         "sy": sig}}, *extra]}}


def test_a_sweep_of_p02_measures_the_free_packets_closed_form(tmp_path, monkeypatch):
    """Review Q3: a sweep (``sweep.run_value``: the checkpoint restored in a fresh world, the change, the advance, the
    world's ``measure()``) over a free packet's wavelength measures <x> after T, the closed form x0 + (h/(m lambda)) T
    (Ehrenfest, exact for the free split step) for every value. ``measure()`` returns the dict of the API; negative
    control: the earlier (values, notes) tuple fails every value (AttributeError, as the owner saw; or the sweep's
    own contract check)."""
    import queue
    import time
    from test_checkpoint import _checkpoint
    from lfviz import registry, sweep
    from lfviz.sim import Runner
    viz = registry.load(V)
    params, errors = viz["schema"].resolve(None, _free_world())
    assert not errors
    sim = viz["simulation"](params, 3, lambda m, b=None: None)
    run = Runner(sim, lambda m, b=None: None, queue.Queue())
    run._start_world()
    run._advance(sim.t + 0.05 * sim.default_speed)
    run._frame(0.0)
    assert isinstance(sim.measure(), dict) and "o1.x" in sim.measure()
    x0 = sim.qs.observables(1)["r"][0]
    data = _checkpoint(run, tmp_path).read_bytes()
    T = 3.0 * TU

    def clock():  # the sweep process's clock (the instruments' ``Clock``; a dict before review LB1-F2)
        return sweep.Clock() if hasattr(sweep, "Clock") else {"w0": time.monotonic(), "budget": 1e9,
                                                               "tick": lambda f: None}
    req = {"target": {"kind": "object", "obj": "o1", "param": "wavelength"}, "duration": T, "n_samples": 1,
           "stat": "final", "measure": "o1.x", "window": T}
    for lam in (2.2, 3.1):
        r = sweep.run_value(data, req, lam, clock())
        assert r.get("measured") is not None, r
        assert r["measured"] == pytest.approx(x0 + 2 * math.pi / lam * (r["t1"] - r["t0"]) / TU, abs=1e-8)
    monkeypatch.setattr(P.Simulation, "measure", lambda self: (self._measure()[0], {}))
    try:  # the sweep says so (its contract check) or fails the value (AttributeError: what the owner saw)
        r = sweep.run_value(data, req, 2.2, clock())
        said = r.get("measured") is None and "AttributeError" in (r.get("error", "") + r.get("detail", ""))
    except Exception as e:  # noqa: BLE001
        said = "tuple" in str(e) or "AttributeError" in type(e).__name__
    assert said


def test_a_drag_in_the_aharonov_bohm_preset_keeps_the_wave_or_is_refused():
    """Review Q1: the electron dragged after it passed the wall, along it by (0, 4) — the tube's path relative to the
    wave stays inside the wall: the same wave (its kinetic momentum and kinetic energy unchanged, the event says the
    magnetic translation; the earlier factor cut lines of phase into it: the outer third of the spectrum 4.4e-9 ->
    6.6e-6, <k - qA> changed); while the wave is in the slits a drag by (0, 6) moves the tube's path across the lower
    slit: refused, naming the tube, nothing changed."""
    h = Harness(V, "aharonov_bohm")
    run(h, h.sim.t + 5.0 * h.sim.default_speed, 20)
    qs = h.sim.qs
    o = qs.observables(1)
    T0 = qs.kinetic_energy(1)
    h.cmd("scene", op="edit", id="o4", values={"x": o["r"][0], "y": o["r"][1] + 4.0})
    assert not h.errors(), h.errors()
    o1 = qs.observables(1)
    assert np.allclose(o1["k"], o["k"], atol=1e-6) and qs.kinetic_energy(1) == pytest.approx(T0, rel=1e-6)
    assert "magnetic translation" in _ev(h)[-2] and "the same wave moved by" in _ev(h)[-2]
    h2 = Harness(V, "aharonov_bohm")
    t0 = h2.sim.t
    while True:  # until the wave is in the slits (|psi|^2 at the lower slit)
        run(h2, h2.sim.t + 0.25 * h2.sim.default_speed, 2)
        rho, g = h2.sim.qs.density(), h2.sim.qs.grid
        X = g.mesh()
        slit = np.broadcast_to((np.abs(X[0]) < 1.5) & (np.abs(X[1] + 5.0) < 1.0), rho.shape)
        if rho[slit].sum() / rho.sum() > 1e-3 or h2.sim.t > t0 + 8 * h2.sim.default_speed:
            break
    w = h2.sim.qs.wave(1).copy()
    r = h2.sim.qs.observables(1)["r"]
    h2.cmd("scene", op="edit", id="o4", values={"x": r[0], "y": r[1] + 6.0})
    assert h2.errors() and "the tube “Flux tube”" in errs(h2)[-1], errs(h2)
    assert np.array_equal(h2.sim.qs.wave(1), w)


def test_a_throw_after_the_wall_is_clamped_by_the_world_not_refused():
    """Review Q5, X5: after the double slit's wall the wave is split (reflected and transmitted); its throw limit
    follows it (checked every 20 frames, the scene message sent again: far below the fresh packet's), a throw at it in
    each axis direction is taken as asked, and a throw beyond it — at the stale fresh packet's limit, as the player had
    clamped before — is clamped by the world to the fastest the scene takes in that direction and said so (the earlier
    world refused both, "0.113 of the spectrum would lie beyond its band"); a typed one is refused with that limit."""
    h = Harness(V, "double_slit")
    v0 = h.sim.objects["o4"]["values"]["v_max"]
    run(h, h.sim.t + 4.5 * h.sim.default_speed, 45)
    vm = h.sim.objects["o4"]["values"]["v_max"]
    assert 0 < vm < 0.5 * v0
    assert h.of("scene")[-1]["objects"][3]["values"]["v_max"] == vm
    for u in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # the scene's own test of a throw (what the edit applies)
        assert h.sim.qs.kick_limit(1, [0.999 * vm * TU * c for c in u]) == 1.0, u
    r = h.sim.qs.observables(1)["r"]
    h.cmd("scene", op="edit", id="o4", values={"x": r[0], "y": r[1], "vx": -0.999 * vm, "vy": 0.0})
    assert not h.errors(), h.errors()
    assert "limited" not in _ev(h)[-2], _ev(h)[-2]
    h = Harness(V, "double_slit")
    run(h, h.sim.t + 4.5 * h.sim.default_speed, 15)
    r = h.sim.qs.observables(1)["r"]
    h.sim.objects["o4"]["values"]["v_max"] = v0  # the player's limit from before the wall (stale)
    h.cmd("scene", op="edit", id="o4", values={"x": r[0], "y": r[1], "vx": 0.999 * v0, "vy": 0.0})
    assert not h.errors(), h.errors()
    k = h.sim.qs.observables(1)["k"][0]
    assert 0 < k < 0.999 * v0 * TU and "the throw was limited" in _ev(h)[-2], _ev(h)[-2:]
    h.cmd("scene", op="set", id="o4", values={"vx": 0.999 * v0})
    assert "no faster than" in errs(h)[-1], errs(h)[-1]


def test_a_new_world_carries_walls_tubes_planes_into_space_and_waves_in_the_same_space():
    """Review Q4 (+ the framework's carry hooks, LB1-F5): a plane's wall with slits, flux tube, flux plane, detector and
    packet into space: all carried (the earlier world refused the wall and the plane with "No parameter “z”" and
    carried 0 of the double slit's 4), the wall unbounded along z, the tube along z, the packet said to be prepared
    afresh (another dimension), one notice and no change noted for an object not carried. In the same space with a
    finer grid the wave itself goes (``carry_state``, ``Scene.adopt_wave``): the exact resampling of the old wave, its
    norm and absorbed records kept (norm + absorbed = 1), the checks pass after."""
    from lfphys.core.quantum import schrodinger_nd as S
    pr = {"dim": "2d", "n2": "128", "size": 40.0, "edges": "open", "scene": {"format": "lfscene", "version": 1,
          "objects": [{"type": "slit_wall", "label": "Wall", "values": {"position": 0.0, "thickness": 3.0, "V": 3.0,
                                                                       "n_slits": 2, "width": 2.0, "spacing": 8.0}},
                      {"type": "flux", "label": "Tube", "values": {"x": 0.0, "y": 0.0, "flux": 0.5, "radius": 1.0}},
                      {"type": "plane", "label": "Flux", "values": {"position": 8.0}},
                      {"type": "detector", "label": "Screen", "values": {"x": 15.0, "sx": 3.0, "edge": 3.0}},
                      {"type": "packet", "label": "Electron", "values": {"x": -5.0, "wavelength": 4.0, "sx": 1.5,
                                                                         "sy": 1.5}}]}}
    h = Harness(V, None, pr)
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 3)
    h.cmd("new_world", params={"dim": "3d", "n3": "96", "size": 40.0}, carry=True)
    assert not h.errors(), h.errors()
    assert [o["type"] for o in h.sim.objects.values()] == ["slit_wall", "flux", "plane", "detector", "packet"]
    note = [n for n in h.of("notice") if n.get("carry")][-1]
    how = {render(o["label"]): o for o in note["carry"]["objects"]}
    assert how["Electron"]["how"] == "restarted" and any("another dimension" in render(x)
                                                         for x in how["Electron"]["notes"])
    assert any("along z" in render(x) for x in how["Wall"]["notes"]) \
        and any("along z" in render(x) for x in how["Tube"]["notes"])
    assert "No parameter" not in render(note["text"])
    h2 = Harness(V, "tunnel")
    run(h2, h2.sim.t + 3.0 * h2.sim.default_speed, 10)
    w, A, g0 = h2.sim.qs.wave(1).copy(), h2.sim.qs.absorbed(1), h2.sim.qs.grid
    h2.cmd("new_world", params={"dim": "2d", "n2": "384", "size": 80.0}, carry=True)
    assert not h2.errors(), h2.errors()
    s2 = h2.sim
    pid = [q for k, q in s2.ref.values() if k == "particle"][0]
    assert np.max(np.abs(s2.qs.wave(pid) - S.resample(w, g0, s2.qs.grid))) < 1e-15
    assert sum(s2.qs.absorbed(pid).values()) == pytest.approx(sum(A.values()), rel=1e-12, abs=1e-15)
    note = [n for n in h2.of("notice") if n.get("carry")][-1]
    assert {render(o["label"]): o["how"] for o in note["carry"]["objects"]}["Electron"] == "state"
    run(h2, h2.sim.t + 1.0 * h2.sim.default_speed, 6)
    assert not failed(h2), {k: h2.checks()[k] for k in failed(h2)}


def test_a_smaller_window_is_refused_where_its_layers_would_cover_the_wave():
    """Review Q6: the tunnel's window 80 -> 56 nm while the wave is mid-window put 2.7e-5 of it under the new 5.6-nm
    layers, said as "3.6e-10 dropped": now refused in the owner's terms (the layers would absorb it), nothing
    changed; a window enlarged says what was inside the old layers."""
    h = Harness(V, "tunnel")
    run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
    w = h.sim.qs.wave(1).copy()
    h.set(size=56.0)
    assert h.errors() and "the new window's absorbing layers" in errs(h)[-1], errs(h)
    assert np.array_equal(h.sim.qs.wave(1), w) and h.sim.size == 80.0
    h.set(n2="384", size=100.0)
    assert len(h.errors()) == 1 and h.sim.size == 100.0, h.errors()


def test_a_late_drag_with_open_edges_is_taken_and_says_what_was_in_the_layers():
    """Review Q8: at 1.32e-13 s 17 % of the double slit's wave is inside the open edges' layers; a drag by (-3, 0) was
    refused for 1.9e-4 «crossing the face» — all of it landing in the far layer: now taken, the event saying the share in
    the layers and what went into the far layer."""
    h = Harness(V, "double_slit")
    while h.sim.t < 1.32e-13:
        h.run_to(min(1.32e-13, h.sim.t + 0.5 * h.sim.default_speed))
        h.runner._frame(0.0)
    r = h.sim.qs.observables(1)["r"]
    h.cmd("scene", op="edit", id="o4", values={"x": r[0] - 3.0, "y": r[1]})
    assert not h.errors(), h.errors()
    assert "the edges' absorbing layers held" in _ev(h)[-2] and "absorbing layer on the other side" in _ev(h)[-2]


def test_prepare_where_the_wave_is_and_coarsen_with_the_edges():
    """Review X11: "Prepare the packet anew" "where the wave is now" puts the fresh packet at <r> with <k> (the parameters
    written; from the parameters it went back to the centre of preparation, 6.6 nm behind). Review X10: the double slit
    cannot go 256 -> 192 (the wall's edge 0 was frozen at 0.995 nm; the refusal names it and the action); the action
    "Coarsen the grid with edges to match" widens it to 1.05 x the new grid's narrowest edge and coarsens, the live values
    sent; the run's checks pass after."""
    h = Harness(V, "tunnel")
    run(h, h.sim.t + 2.0 * h.sim.default_speed, 6)
    o = h.sim.qs.observables(1)
    h.action("prepare", particle="o3", where="now")
    assert not h.errors(), h.errors()
    o1 = h.sim.qs.observables(1)
    assert np.allclose(o1["r"], o["r"], atol=1e-8) and np.allclose(o1["k"], o["k"], atol=1e-8)
    assert h.sim.objects["o3"]["values"]["x"] == pytest.approx(o["r"][0], rel=1e-9)
    h2 = Harness(V, "double_slit")
    h2.set(n2="192")
    assert "Coarsen the grid with edges to match" in errs(h2)[-1]
    h2.action("coarsen", n="192")
    assert len(h2.errors()) == 1, h2.errors()
    qid = h2.sim.ref["o1"][1]
    assert h2.sim.qs.grid.shape == (192, 192) and h2.sim.qs.objects[qid].edge == pytest.approx(1.05 * QS.edge_min(80 / 192))
    assert h2.of("live")[-1]["values"]["n2"] == "192" and "the edges of width 0 widened" in _ev(h2)[-1]
    run(h2, h2.sim.t + 2.0 * h2.sim.default_speed, 10)
    assert not failed(h2), {k: h2.checks()[k] for k in failed(h2)}


def test_refusal_and_label_texts_say_which_rule():
    """Review Q7: a free packet's coarsening refused by the resolution rule says the wave is finer than the grid holds
    (not "next to what acts on it"); Q10: the regrid bank's label says a minus is a gain; X12: no doubled
    parentheses and no "resampled" without waves."""
    h = Harness(V, None, _free_world(x=-10.0, lam=0.952, sig=3.0))  # k0 + 5 sigma_k < pi/d(192) < k0 + 6 sigma_k
    h.set(n2="192")
    e = errs(h)[-1]
    assert "is finer than the new grid" in e and "next to what acts" not in e, e
    ms = {m["id"]: m["label"] for m in h.of("scene")[-1]["measurables"]}
    assert "a minus: added" in render(ms["regrid"])
    h.set(n2="384")
    assert "(unchanged to within round-off)" in _ev(h)[-1] and "((" not in _ev(h)[-1]
    he = Harness(V, None, {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open"})
    he.set(n2="384")
    assert "no waves in the window" in _ev(he)[-1] and "resampled" not in _ev(he)[-1]


def test_engine_refusals_are_said_in_the_worlds_terms(monkeypatch):
    """Code review 2026-11-12 i18n-code F5: every engine refusal the world puts in its own terms is matched by the
    engine's machine code (``lfphys.codes``), not by its wording. Each place the world matches is triggered here, and
    both the engine's code and the world's own text are asserted: ``_refusal`` (resolution, field under a charge),
    ``_packet_refusal`` (resolution and the packet's band), ``palette_state``, ``can_remove`` and the window's edges."""
    from lfphys.codes import code_of
    seen = []

    def spy(name):
        orig = getattr(P.Simulation, name)

        def f(self, obj, *a):
            seen.append((name, code_of(a[-1])))
            return orig(self, obj, *a)
        monkeypatch.setattr(P.Simulation, name, f)
    spy("_refusal")
    spy("_packet_refusal")
    # _refusal, qscene.resolution: a deep well next to a fast packet
    h = Harness(V, None, _free_world(lam=1.2))
    n = len(h.errors())
    h.cmd("scene", op="add", type="box", values={"x": 10.0, "V": -30.0})
    assert seen[-1] == ("_refusal", "qscene.resolution"), seen
    assert len(h.errors()) == n + 1 and "the grid (step 0.312 nm) does not resolve the particle's wave: next to it" \
        in errs(h)[-1], errs(h)[n:]
    # palette_state, qscene.resolution (Scene.addition_check): a default trap next to the same packet
    ot = h.sim.PALETTE["trap"]
    obj = {"type": "trap", "values": ot.schema.resolve(None, h.sim.place("trap", {}))[0], "label": ot.label}
    assert code_of(h.sim.qs.addition_check(h.sim._object(obj))) == "qscene.resolution"
    ps = h.of("scene")[-1].get("palette_state") or {}
    assert ps.get("trap") and render(ps["trap"]).startswith("with it the grid would not resolve the wave of a particle"), ps
    # _packet_refusal, qscene.resolution: a packet inside the double slit's wall, said in the scene's terms
    h2 = Harness(V, "double_slit")
    with pytest.raises(ValueError) as e:
        h2.sim._add("packet", {"x": 0.0, "y": 3.0})
    assert seen[-1] == ("_packet_refusal", "qscene.resolution"), seen
    assert "the packet's centre" in str(e.value) and "inside “Wall with two slits”" in str(e.value), str(e.value)
    # _packet_refusal, qscene.packet_band: a packet faster than the grid holds anywhere
    with pytest.raises(ValueError) as e:
        h2.sim._add("packet", {"x": -10.0, "wavelength": 0.2})
    assert seen[-1] == ("_packet_refusal", "qscene.packet_band"), seen
    assert "the particle's wave is finer than the grid" in str(e.value), str(e.value)
    # _refusal, qscene.field_with_charge: the cyclotron's field changed under its electron
    h3 = Harness(V, "cyclotron")
    run(h3, h3.sim.t + h3.sim.default_speed / 5, 3)
    fid = next(k for k, o in h3.sim.objects.items() if o["type"] == "bfield")
    h3.cmd("scene", op="set", id=fid, values={"Bz": 50.0})
    assert seen[-1] == ("_refusal", "qscene.field_with_charge"), seen
    assert "while a charged particle is in the window: the impulse of the induced field" in errs(h3)[-1], errs(h3)[-1]
    # can_remove, qscene.field_with_charge: the same field removed
    assert code_of(h3.sim._removal_check(h3.sim.ref[fid][1])) == "qscene.field_with_charge"
    h3.cmd("scene", op="remove", id=fid)
    assert "the field cannot be switched off" in errs(h3)[-1] and fid in h3.sim.objects, errs(h3)[-1]
    # the edges, qscene.gauge: closing the window with the electron next to the field
    assert code_of(h3.sim._edges_check(None)) == "qscene.gauge"
    h3.set(edges="closed")
    assert "a charged particle next to a field is allowed only with open edges" in errs(h3)[-1], errs(h3)[-1]
