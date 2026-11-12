# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P1 (B8): the FDTD solver as a tool — edits at a running moment (all or nothing), the saved state's
bit-identical continuation, GPU = CPU (through the backend's guard), the cell-fill fraction behind sub-pixel
averaging, the shapes, the display helpers and the refusals."""

import math

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.em import fdtd as F
from lfphys.core.em import fdtd_geometry as geo


def _gpu():
    return backend.devices()["gpu"]["available"]


def _busy(device="cpu", pol="tm", bloch=None):
    """A world with every kind of part: PML, a Drude + Debye body, a dielectric (averaged), a PEC box, a conductor,
    a plane wave (or a Bloch sheet source), a point source, a probe, a flux box, a DFT and a near-to-far box."""
    bc = {"x": "pml", "y": "periodic"} if bloch else "pml"
    w = F.FDTD((3.0, 2.5), 0.05, pol=pol, pml=8, device=device, bloch=bloch, boundary=bc)
    if bloch:
        w.add_source(F.PlaneWave(F.ModulatedGaussian(1.0, fwidth=0.1), ((0.6, -math.inf), (math.inf, math.inf))))
    else:
        w.add_source(F.PlaneWave(F.ModulatedGaussian(1.0, fwidth=0.3), ((0.6, 0.6), (2.4, 1.9)), direction=0.4))
    w.add_body(F.Cylinder((1.5, 1.2), 0.3), F.Medium(eps=1.0, poles=[F.Drude(1.5, 0.1), F.Debye(2.0, 0.3)]))
    w.add_body(F.Cylinder((0.9, 1.2), 0.2), F.Medium(eps=3.0))
    w.add_body(F.Box((2.0, 0.3), (2.3, 0.6)), F.Medium.pec())
    w.add_body(F.Polygon([(0.3, 2.0), (0.7, 2.0), (0.5, 2.3)]), F.Medium(eps=2.0, sigma=0.5))
    comp = "ez" if pol != "te" else "hz"
    w.add_source(F.CurrentSource(comp, F.GaussianPulse(0.3), position=(1.0, 0.5)))
    w.add_probe((1.7, 1.3))
    w.add_flux(((0.3, 0.3), (2.7, 2.2)), freqs=[0.8, 1.0])
    w.add_dft(((1.0, 1.0), (2.0, 1.5)), [1.0])
    if not bloch:
        w.add_near2far(((0.4, 0.4), (2.6, 2.1)), [1.0])
    return w


def _same(a, b, exact=True):
    for c in a.comps:
        fa, fb = a.field(c), b.field(c)
        if exact:
            assert np.array_equal(fa, fb), c
        else:
            assert np.allclose(fa, fb, rtol=0, atol=1e-13 * max(1.0, np.abs(fa).max())), c


# --- state --------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("pol,bloch", [("tm", None), ("te", None), ("tm", (0.0, 2.0))])
def test_state_round_trip_is_bit_identical(pol, bloch):
    a = _busy(pol=pol, bloch=bloch)
    a.advance(120)
    d = a.state_dict()
    b = F.FDTD.from_state_dict(d, device="cpu")
    a.advance(150)
    b.advance(150)
    _same(a, b)
    for (k, pa), (_, pb) in zip(sorted(a.psi.items()), sorted(b.psi.items())):
        assert np.array_equal(pa, pb), k
    for c in a.disp:
        for key in ("P", "Pm", "PD"):
            assert np.array_equal(a.disp[c][key], b.disp[c][key])
    for mid, m in a._monitors.items():
        if m["kind"] == "probe":
            pa, pb = a.probe(mid), b.probe(mid)
            assert all(np.array_equal(pa[k], pb[k]) for k in pa)
        elif m["kind"] == "flux":
            fa, fb = a.flux(mid), b.flux(mid)
            assert np.array_equal(fa["spectrum"], fb["spectrum"]) and np.array_equal(fa["power"], fb["power"])
        elif m["kind"] == "dft":
            da, db = a.dft(mid), b.dft(mid)
            assert all(np.array_equal(da[c], db[c]) for c in a.comps)
    assert b.steps == a.steps and b.t == a.t


def test_state_refuses_what_cannot_be_saved(ru):
    w = F.FDTD((1.0, 1.0), 0.05)
    w.add_source(F.CurrentSource("ez", lambda t: np.sin(t), position=(0.5, 0.5)))
    with pytest.raises(ValueError, match="is not saved in the state") as e:
        w.state_dict()
    assert "не сохраняется в состоянии" in ru(e.value.args[0])


# --- edits ------------------------------------------------------------------------------------------------------------
def test_edits_at_a_running_moment():
    w = _busy()
    w.advance(100)
    n_bodies = len(w.bodies())
    disp_before = {k: w.disp["ez"][k].copy() for k in ("idx", "P", "PD")}
    # a refused edit (an unstable Lorentz pole) leaves the world as it was: compare with an untouched twin
    twin = _busy()
    twin.advance(100)
    with pytest.raises(F.Unstable):
        w.add_body(F.Cylinder((0.5, 0.5), 0.1), F.Medium(poles=[F.Lorentz(1.0, 2.5 / (2 * math.pi * w.dt))]))
    assert len(w.bodies()) == n_bodies
    w.advance(30)
    twin.advance(30)
    _same(w, twin)
    # a new PEC body: E = 0 at its nodes at once; the dispersive body's polarization is kept
    bid = w.add_body(F.Box((0.4, 1.6), (0.6, 1.9)), F.Medium.pec())
    pec = w.coef["ez"]["cb"] == 0.0
    assert np.all(w.F["ez"][pec] == 0.0)
    assert np.array_equal(w.disp["ez"]["idx"], disp_before["idx"])
    assert not np.array_equal(w.disp["ez"]["P"], disp_before["P"])  # it has evolved, and was not reset
    P_now = w.disp["ez"]["P"].copy()
    w.update_body(bid, shape=F.Box((0.4, 1.6), (0.7, 1.9)))
    assert np.array_equal(w.disp["ez"]["P"], P_now)
    # removing the dispersive body drops its polarization; the run goes on
    w.remove_body(1)
    assert len(w.disp.get("ez", {"idx": []})["idx"]) == 0
    w.advance(20)
    assert w.checks()["finite"]
    # sources and monitors come and go
    sid = w.add_source(F.CurrentSource("ez", F.ContinuousWave(1.0, ramp=2.0), position=(2.5, 2.0)))
    mid = w.add_probe((2.4, 2.0), ["ez"])
    w.advance(10)
    assert len(w.probe(mid)["ez"]) == 10
    w.remove_source(sid)
    w.remove_monitor(mid)
    with pytest.raises(KeyError):
        w.remove_body(99)


def test_an_added_dielectric_changes_the_energy_by_half_delta_eps_e2():
    w = F.FDTD((1.0, 1.0), 0.05, pol="tm", boundary="pec")
    w.set_field("ez", lambda x, y: np.sin(math.pi * x) * np.sin(math.pi * y))
    w.advance(7)
    e0 = w.energy()["electric"]
    E = w.field("ez")
    w.add_body(F.Box((0.2, 0.2), (0.6, 0.6)), F.Medium(eps=3.0), averaging="staircase")
    eps = w.material_map("eps", interior=False)
    assert w.energy()["electric"] == pytest.approx(e0 + 0.5 * np.sum((eps - 1.0) * E ** 2) * w.dV, rel=1e-12)


# --- devices -----------------------------------------------------------------------------------------------------------
@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_gpu_equals_cpu():
    """Real fields: bit for bit (the kernel performs the CPU's operations in the same order, --fmad=false); complex
    (Bloch) fields: to round-off (complex products may differ in their rounding), measured 2.3e-15 of fields of
    order 1."""
    backend.configure({"kernels": {F.KERNEL: {"device": "gpu"}}})
    try:
        for pol, bloch, exact in (("tm", None, True), ("te", None, True), ("both", None, True), ("tm", (0.0, 2.0), False)):
            c, g = _busy("cpu", pol, bloch), _busy("auto", pol, bloch)
            assert c.device == "cpu" and g.device == "gpu"
            c.advance(150)
            g.advance(150)
            _same(c, g, exact)
            fid = next(k for k, m in c._monitors.items() if m["kind"] == "flux")
            fc, fg = c.flux(fid), g.flux(fid)
            assert np.allclose(fc["spectrum"], fg["spectrum"], rtol=1e-12)
        w3c, w3g = (F.FDTD((1.2, 1.0, 0.9), 0.05, pml=6, device=d) for d in ("cpu", "auto"))
        for w in (w3c, w3g):
            w.add_body(F.Sphere((0.6, 0.5, 0.45), 0.2), F.Medium(eps=2.0, sigma=0.5))
            w.add_body(F.Box((0.2, 0.2, 0.2), (0.3, 0.4, 0.3)), F.Medium(poles=[F.Lorentz(2.0, 1.2, 0.2)]))
            w.add_source(F.CurrentSource("ey", F.ModulatedGaussian(1.0, fwidth=0.4), position=(0.4, 0.5, 0.45)))
            w.advance(100)
        _same(w3c, w3g)
        assert backend.used()[F.KERNEL]["drawn"]["device"] in ("gpu", "cpu")
    finally:
        backend.configure({})


def test_kernel_is_registered_and_cost_is_estimated():
    k = backend.kernels()
    assert F.KERNEL in k and k[F.KERNEL].gpu and k[F.KERNEL].crossover == 128 * 128
    w = F.FDTD((2.0, 2.0), 0.02)
    c = w.cost_estimate()
    assert c["per_step_s"] > 0 and c["device"] == "cpu"
    w.advance(3)
    assert w.cost_estimate()["measured_per_step_s"] > 0


# --- geometry -----------------------------------------------------------------------------------------------------------
def test_cut_fraction_against_quadrature():
    rng = np.random.default_rng(3)
    for D, nq in ((2, 1000), (3, 160)):
        g = (np.arange(nq) + 0.5) / nq - 0.5
        pts = np.stack(np.meshgrid(*([g] * D), indexing="ij"), axis=-1).reshape(-1, D)
        for _ in range(12):
            n = rng.standard_normal(D)
            if rng.random() < 0.3:
                n[rng.integers(D)] = 1e-6  # nearly axis-aligned planes take the folded branch
            n /= np.linalg.norm(n)
            off = rng.uniform(-0.8, 0.8)
            exact_q = np.mean(pts @ n <= off)
            got = float(geo.cut_fraction(n[None], np.array([off]))[0])
            assert abs(got - exact_q) < (3e-3 if D == 3 else 2e-3), (D, n, off, got, exact_q)
    # exact cases: an axis-aligned plane, the diagonal through the centre, and full / empty cells
    assert geo.cut_fraction(np.array([[1.0, 0, 0]]), np.array([0.25]))[0] == pytest.approx(0.75)
    assert geo.cut_fraction(np.array([[1, 1, 1]]) / math.sqrt(3), np.array([0.0]))[0] == pytest.approx(0.5)
    assert geo.cut_fraction(np.array([[0.6, 0.8]]), np.array([2.0]))[0] == 1.0
    assert geo.cut_fraction(np.array([[0.6, 0.8]]), np.array([-2.0]))[0] == 0.0


def test_shapes_signed_distance():
    P = (np.array([0.0, 1.0, 2.0, 0.5]), np.array([0.0, 0.0, 0.0, 0.5]))
    d, n = F.Cylinder((0.0, 0.0), 1.0).sdf(P)
    assert np.allclose(d, [-1, 0, 1, math.sqrt(0.5) - 1]) and np.allclose(n[0][1:3], 1)
    d, _ = F.Box((-1, -1), (1, 1)).sdf(P)
    assert np.allclose(d, [-1, 0, 1, -0.5])
    d, _ = F.Polygon([(-1, -1), (1, -1), (1, 1), (-1, 1)]).sdf(P)
    assert np.allclose(d, [-1, 0, 1, -0.5])
    d, n = F.HalfSpace((1.0, 0.0), (1.0, 0.0)).sdf(P)
    assert np.allclose(d, [-1, 0, 1, -0.5])
    d, _ = F.Sphere((0, 0, 0), 1.0).sdf((np.array([0.0, 3.0]), np.array([0.0, 0.0]), np.array([0.0, 4.0])))
    assert np.allclose(d, [-1, 4])
    d, _ = F.Cylinder((0, 0, 0), 1.0, axis="x", height=2.0).sdf((np.array([0.0, 3.0]), np.array([0.0, 0.0]),
                                                                 np.array([0.5, 0.0])))
    assert np.allclose(d, [-0.5, 2.0])
    with pytest.raises(ValueError):
        F.FDTD((1.0, 1.0), 0.1).add_body(F.Sphere((0.5, 0.5, 0.5), 0.2), F.Medium(eps=2))


def test_mask_body_is_a_staircase_of_its_samples():
    """A mask given as a boolean array (saved in the state) takes the same nodes as the box it samples, staircase."""
    arr = np.zeros((40, 40), bool)
    arr[10:30, 12:20] = True  # cells of 0.025 over [0, 1]^2: x in [0.25, 0.75), y in [0.3, 0.5)
    a = F.FDTD((1.0, 1.0), 0.05, pml=4)
    a.add_body(F.Mask(array=arr, lo=(0.0, 0.0), hi=(1.0, 1.0)), F.Medium(eps=3.0))
    b = F.FDTD((1.0, 1.0), 0.05, pml=4, averaging="staircase")
    b.add_body(F.Box((0.25, 0.3), (0.7499, 0.4999)), F.Medium(eps=3.0))
    assert np.array_equal(a.material_map("eps"), b.material_map("eps"))
    c = F.FDTD.from_state_dict(a.state_dict())
    assert np.array_equal(c.material_map("eps"), a.material_map("eps"))
    with pytest.raises(ValueError, match="is not saved in the state"):
        w = F.FDTD((1.0, 1.0), 0.05)
        w.add_body(F.Mask(inside=lambda x, y: x < 0.5, dims=2), F.Medium(eps=2.0))
        w.state_dict()


# --- display and refusals ---------------------------------------------------------------------------------------------
def test_snapshots_and_material_map():
    w = _busy()
    w.advance(60)
    s = w.snapshot("ez")
    assert s["values"].shape == (60, 50) and len(s["x"]) == 60
    assert np.all(w.snapshot("|E|^2")["values"] >= 0)
    assert w.snapshot("Sx")["values"].shape == (60, 50)
    m = w.material_map("eps")
    assert m.shape == (60, 50) and m.max() == pytest.approx(3.0) and m.min() == pytest.approx(1.0)
    assert w.material_map("pec").sum() > 0
    w3 = F.FDTD((1.0, 0.8, 0.6), 0.05, pml=4)
    w3.add_body(F.Sphere((0.5, 0.4, 0.3), 0.2), F.Medium(eps=4.0))
    sl = w3.snapshot("ex", plane=("z", 0.3))
    assert sl["values"].shape == (20, 16) and sl["axes"] == ["x", "y"]
    assert w3.material_map("eps").shape == (20, 16, 12)


def test_refusals(ru):
    w = F.FDTD((2.0, 2.0), 0.05, pml=10)
    with pytest.raises(ValueError, match="absorbing layer") as e:
        w.add_source(F.PlaneWave(F.GaussianPulse(0.3), ((-0.2, 0.5), (1.5, 1.5))))
    assert "в поглощающем слое" in ru(e.value.args[0])
    with pytest.raises(ValueError, match="Bloch phase") as e:
        w.add_source(F.CurrentSource("ez", F.GaussianPulse(0.3), position=(1, 1), amplitude=1j))
    assert "фазой Блоха" in ru(e.value.args[0])
    with pytest.raises(ValueError, match="no component hz") as e:
        w.add_source(F.CurrentSource("hz", F.GaussianPulse(0.3), position=(1, 1)))
    assert ru(e.value.args[0]) == "компоненты hz нет в этом мире (поляризация tm)"
    wb = F.FDTD((2.0, 0.05), 0.05, boundary={"x": "pml", "y": "periodic"}, bloch=(0.0, 2 * math.pi * 0.8))
    with pytest.raises(ValueError, match="of its energy"):  # half the pulse lies below the Bloch wave's cut-off
        wb.add_source(F.PlaneWave(F.ModulatedGaussian(0.8, fwidth=0.2), ((0.5, -math.inf), (math.inf, math.inf))))
    with pytest.raises(ValueError):
        F.FDTD((1.0, 1.0), 0.05, boundary={"x": ("periodic", "pec")})
    with pytest.raises(ValueError):
        F.FDTD((1.0, 1.0), 0.05, bloch=(1.0, 0.0))  # Bloch only on periodic axes


def test_units():
    u = F.Units(1e-6)
    assert float(u.frequency(1.0)) == pytest.approx(299792458.0 / 1e-6)
    assert float(u.time(1.0)) == pytest.approx(1e-6 / 299792458.0)
    assert float(u.H(1.0)) == pytest.approx(1 / 376.730313412, rel=1e-9)


# --- regressions of review B8-fdtd -----------------------------------------------------------------------------------
def test_stability_cache_is_by_value_not_by_id():
    """F1: the check's cache was keyed by id(Medium); a freed medium's id reused by a new, unstable one skipped the
    check (9 of 200 trials of this edit pattern accepted eps = 0.3 at S = 0.6, where n = 0.55 needs S <= 0.39, and the
    run blew up). Now 0 of 200; equal media share one cache entry."""
    accepted = 0
    for _ in range(200):
        w = F.FDTD((1.0, 1.0), 0.05, courant=0.6)
        bid = w.add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=2.0))
        w.update_body(bid, medium=F.Medium(eps=1.5))
        try:
            w.update_body(bid, medium=F.Medium(eps=0.3))
            accepted += 1
        except F.Unstable:
            pass
    assert accepted == 0
    w = F.FDTD((1.0, 1.0), 0.05)
    n0 = len(w._media_check_cache)
    w.add_body(F.Cylinder((0.3, 0.3), 0.1), F.Medium(eps=2.0, label="a"))
    w.add_body(F.Cylinder((0.7, 0.7), 0.1), F.Medium(eps=2.0, label="b"))
    assert len(w._media_check_cache) == n0 + 1


def test_polarization_is_kept_by_medium_not_by_position():
    """F3: (1) a body changed from a Lorentz to a Drude medium starts the Drude polarization from 0 (it carried the
    Lorentz P into the Drude update); (2) removing an earlier dispersive body keeps a later, unchanged body's P (it was
    zeroed because its index in the media list shifted); (3) a new Medium object equal in value keeps P."""
    def world():
        w = F.FDTD((2.0, 2.0), 0.05, pol="tm", pml=8)
        w.add_source(F.CurrentSource("ez", F.ModulatedGaussian(1.0, fwidth=0.3), position=(1.0, 1.0)))
        return w

    w = world()
    bid = w.add_body(F.Box((1.2, 0.6), (1.6, 1.4)), F.Medium(poles=[F.Lorentz(2.0, 1.0, 0.1)]))
    w.advance(120)
    assert np.abs(w.disp["ez"]["P"]).max() > 0.1
    w.update_body(bid, medium=F.Medium(poles=[F.Drude(3.0, 0.5)]))
    assert np.all(w.disp["ez"]["P"] == 0.0) and np.all(w.disp["ez"]["Pm"] == 0.0)

    w = world()
    b1 = w.add_body(F.Box((0.2, 0.2), (0.4, 0.4)), F.Medium(poles=[F.Debye(2.0, 0.3)]))
    D = F.Medium(poles=[F.Lorentz(2.0, 1.0, 0.1)])
    b2 = w.add_body(F.Box((1.2, 0.6), (1.6, 1.4)), D)
    w.advance(120)
    sel = w.disp["ez"]["mid"] == 2
    idx_D, P_D = w.disp["ez"]["idx"][sel].copy(), w.disp["ez"]["P"][sel].copy()
    assert np.abs(P_D).max() > 0.1
    w.remove_body(b1)
    keep = np.isin(w.disp["ez"]["idx"], idx_D)
    assert np.array_equal(w.disp["ez"]["idx"][keep], idx_D) and np.array_equal(w.disp["ez"]["P"][keep], P_D)
    w.update_body(b2, medium=F.Medium(poles=[F.Lorentz(2.0, 1.0, 0.1)], label="the same, a new object"))
    assert np.array_equal(w.disp["ez"]["P"][keep], P_D)


def _cylinder_with_late_wave(delay_steps, res=20, save_at=None):
    a = 0.5
    fs = np.array([0.4, 0.6, 0.8])
    w = F.FDTD((4.0, 4.0), 1.0 / res, pol="tm", pml=16)
    w.add_body(F.Cylinder((2.0, 2.0), a), F.Medium(eps=2.25))
    width = 1.0 / (2 * math.pi * 0.25)
    w.advance(delay_steps)
    prof = F.ModulatedGaussian(0.7, fwidth=0.25, t0=w.t + 6 * width)
    w.add_source(F.PlaneWave(prof, ((0.8, 0.8), (3.2, 3.2)), direction=0.0))
    sca = w.add_flux(((0.5, 0.5), (3.5, 3.5)), freqs=fs)
    n = int((12 * width + 25) / w.dt)
    if save_at is not None:
        w.advance(save_at)
        w = F.FDTD.from_state_dict(w.state_dict())
        n -= save_at
    w.advance(n)
    return w.cross_sections(sca)["sigma_sca"] / (2 * a)


def test_plane_wave_added_during_the_run():
    """F4: the incident series is numbered from the step at which the wave was added (it was numbered from step 1, so
    monitors started later dropped the pulse: Q_sca off by 4 % when added at step 100 and by 1e23 at step 400). The
    same pulse added at step 0, 100 or 400 gives the same cross sections (measured 9.4e-10: the two runs' incident
    series come from FFT windows of different lengths), also through a saved and restored state."""
    q0 = _cylinder_with_late_wave(0)
    for d in (100, 400):
        assert np.allclose(_cylinder_with_late_wave(d) / q0, 1.0, rtol=1e-8, atol=0), d
    assert np.allclose(_cylinder_with_late_wave(400, save_at=300) / q0, 1.0, rtol=1e-8, atol=0)


def test_bodies_at_the_plane_wave_faces_and_misplaced_monitors(ru):
    """F12: a body crossing a TF/SF face (also one added later) is flagged in ``checks()`` with the count of correction
    nodes not in the background; a cross-section box crossing the total-field box is refused, and so is a near-to-far
    box that is not wholly in the scattered-field region."""
    w = F.FDTD((5.0, 5.0), 0.05, pol="tm", pml=12)
    w.add_source(F.PlaneWave(F.ModulatedGaussian(1.0, fwidth=0.3), ((1.5, 1.5), (3.5, 3.5)), direction=0.0))
    assert w.checks()["tfsf_1"]["ok"] and w.checks()["tfsf_1"]["foreign_nodes_at_faces"] == 0
    bid = w.add_body(F.Cylinder((2.5, 2.5), 0.4), F.Medium(eps=2.25))
    assert w.checks()["tfsf_1"]["ok"]
    w.update_body(bid, shape=F.Box((1.0, 2.2), (4.0, 2.8)))
    c = w.checks()["tfsf_1"]
    assert not c["ok"] and c["foreign_nodes_at_faces"] > 0 and "faces" in str(c["note"])
    assert f"не в фоновой среде: {c['foreign_nodes_at_faces']}" in ru(c["note"])
    w.remove_body(bid)
    assert w.checks()["tfsf_1"]["ok"]
    good = w.add_flux(((1.0, 1.0), (4.0, 4.0)), freqs=[1.0])
    inside = w.add_flux(((2.0, 2.0), (3.0, 3.0)), freqs=[1.0])
    crossing = w.add_flux(((1.0, 1.0), (3.0, 3.0)), freqs=[1.0])
    n2f_bad = w.add_near2far(((1.6, 1.6), (3.6, 3.6)), freqs=[1.0])
    w.advance(20)
    ch = w.checks()
    assert ch[f"monitor_{good}"]["region"] == "sf" and ch[f"monitor_{inside}"]["region"] == "tf"
    assert not ch[f"monitor_{crossing}"]["ok"] and not ch[f"monitor_{n2f_bad}"]["ok"]
    w.cross_sections(good, inside)
    with pytest.raises(ValueError, match="F12") as e:
        w.cross_sections(crossing)
    assert "across the boundary of the total-field region" in str(e.value)
    assert "а он лежит поперёк границы области полного поля" in ru(e.value.args[0])
    with pytest.raises(ValueError, match="F12"):
        w.cross_sections(good, crossing)
    with pytest.raises(ValueError, match="F12"):
        w.far_field(n2f_bad, [0.0])


def test_3d_polarization_along_the_direction_is_refused():
    """F16: a 3-D plane wave polarized along its own direction gave a silent zero wave."""
    w = F.FDTD((1.0, 1.0, 1.0), 0.1, pml=6)
    with pytest.raises(ValueError, match="polarization"):
        w.add_source(F.PlaneWave(F.ModulatedGaussian(0.8, fwidth=0.3), ((0.3,) * 3, (0.7,) * 3),
                                 direction=(0, 0, 1), polarization=(0, 0, 1)))
    with pytest.raises(ValueError, match="polarization"):
        w.add_source(F.PlaneWave(F.ContinuousWave(0.8, ramp=2.0), ((0.3,) * 3, (0.7,) * 3),
                                 direction=(1, 1, 0), polarization=(2, 2, 0)))
    assert not w._sources
    w.add_source(F.PlaneWave(F.ModulatedGaussian(0.8, fwidth=0.3), ((0.3,) * 3, (0.7,) * 3), direction=(0, 0, 1),
                             polarization=(1, 0, 0.5)))  # the part along k is projected out


def test_cost_estimate_and_footprint():
    """F18: the other device's estimate carries the complex factor; the device footprint counts the plane wave's
    tables, the DFT accumulators and the dispersive nodes."""
    w = F.FDTD((3.0, 0.05), 0.05, pol="tm", boundary={"x": "pml", "y": "periodic"}, bloch=(0.0, 1.0))
    c = w.cost_estimate()
    other = F._interp_rate("2d", "gpu", w.N)
    assert c["other_device_per_step_s"] == pytest.approx(2.0 * other)
    w = F.FDTD((3.0, 3.0), 0.05)
    b0 = w._footprint()
    w.add_source(F.PlaneWave(F.ModulatedGaussian(1.0, fwidth=0.3), ((0.6, 0.6), (2.4, 2.4)), direction=0.4))
    b1 = w._footprint()
    table = w._sources[1]["table"].nbytes
    assert b1 - b0 >= 1.3 * table
    w.add_dft(((0.5, 0.5), (2.5, 2.5)), np.linspace(0.5, 1.5, 11))
    b2 = w._footprint()
    assert b2 - b1 >= 1.3 * 11 * 40 * 40 * 16 * len(w.comps)
    w.add_body(F.Box((1.0, 1.0), (2.0, 2.0)), F.Medium(poles=[F.Lorentz(1.0, 1.0, 0.1)]))
    assert w._footprint() > b2


def test_labels_are_translatable_texts(ru):
    """A medium's or a body's label may be a translatable text (``lfphys.i18n.T``, owner 2026-11-12: the interface in
    English and Russian); it survives a state saved as JSON."""
    import json

    from lfphys.i18n import T
    m = F.Medium(eps=2.0, label=T("vacuum"))
    back = F.Medium.from_params(json.loads(json.dumps(m.params())))
    assert isinstance(back.label, T) and str(back.label) == "vacuum" and ru(back.label) == "вакуум"
    assert ru(F.VACUUM.label) == "вакуум" and F.Medium(label="glass").label == "glass"
    w = F.FDTD((1.0, 1.0), 0.05)
    w.add_body(F.Box((0.2, 0.2), (0.4, 0.4)), F.Medium(eps=2.0), label=T("vacuum"))
    c = F.FDTD.from_state_dict(json.loads(json.dumps(w.state_dict(), default=lambda a: a.tolist())))
    assert c.bodies()[0]["label"] == T("vacuum") and isinstance(c.bodies()[0]["label"], T)
