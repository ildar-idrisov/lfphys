# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.quantum.scene and schrodinger_nd: live changes in the same world (plan P16.1, P16.2).

The grid and the window changed at the current moment (``Scene.regrid``, ``schrodinger_nd.resample``), a wave moved
(``Scene.move_particle``) or given a momentum (``Scene.boost_particle``), and the readings of the instruments
(``Scene.observables``). References: the exact free evolution of a Gaussian packet (``Grid.free_gaussian``) continued
across the change; the trigonometric interpolant evaluated term by term (a second route for the resampling); the
packet prepared afresh at the new place or with the new momentum (the identities a translation and a boost must
satisfy); ``Scene.checks`` and ``Grid.mean_x`` / ``mean_p`` for the readings. Negative controls: a naive (linear)
interpolation of the wave fails the same comparison; changes that would drop or misplace more than the stated
tolerance are refused with the measured fraction, and nothing changes.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import constants as sc

from lfphys.core import backend
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S

EPS = np.finfo(float).eps
UNIT = Q.species("atom", Q.Units(), mass_u=sc.m_e / sc.atomic_mass)  # mass 1 in the scene's units

# the base grid: 192^2 points, step 0.5 (window 96); a packet with sigma 3 and k0 = (1.5, -0.5): its amplitude beyond
# the band of the coarsest grid used (step 0.75: |k - k0| > 2.69) is exp(-sigma^2 2.69^2) ~ 1e-28 of its peak (at step
# 1 it would be 3e-11: the closed form's own samples would alias that much), its tails at the faces
# exp(-gap^2 / (4 |s_t|^2)) < 1e-20 for the times used: the exact free evolution is the reference to round-off
BASE = ((192, 192), 0.5)
C0, K0, SIG = (-4.0, 2.0), (1.5, -0.5), (3.0, 3.0)
T1, T2, DT = 2.0, 4.0, 0.25


def _free_scene(shape=BASE[0], spacing=BASE[1], edges=None):
    s = Q.Scene(shape, spacing, dt=DT, edges=edges, device="cpu")
    pid = s.add_particle(Q.Packet(UNIT, list(C0), list(K0), list(SIG)))
    return s, pid


def _ref(grid, t, center=C0, k=K0):
    return S.Grid(grid.shape, grid.d, m=1.0, center=grid.center).free_gaussian(t, center, k, SIG)


def _rel_err(a, b):
    return float(np.max(np.abs(a - b)) / np.max(np.abs(b)))


# --- the grid and the window changed in the same world ------------------------------------------------------------
@pytest.mark.parametrize("shape,spacing,route", [
    ((288, 288), 1 / 3, "same window, finer: Fourier zero padding"),
    ((128, 128), 0.75, "same window, coarser: Fourier truncation"),
    ((256, 256), 0.5, "same step, larger window: the samples, zeros beyond"),
    ((160, 160), 0.5, "same step, smaller window: the samples inside"),
    ((150, 150), 0.6, "smaller window and coarser: the interpolant evaluated"),
    ((256, 256), 0.4, "larger window and finer: the interpolant evaluated"),
])
def test_a_free_packet_continues_exactly_across_a_change_of_the_grid(shape, spacing, route):
    """A free Gaussian evolved to T1 on the base grid, the grid changed, evolved on to T2: the wave equals the exact
    free evolution on the new grid to round-off (1e-12 of its peak; the split operator is exact for free motion on the
    grid, so any error is the resampling's), the norm is kept to round-off and nothing is banked as dropped (the
    spectrum beyond a coarser band and the probability outside a smaller window are below 1e-20 here)."""
    s, pid = _free_scene()
    s.advance(int(round(T1 / DT)))
    assert _rel_err(s.wave(pid), _ref(s.grid, T1)) < 1e-12
    rep = s.regrid(shape, spacing)
    assert rep["changed"] and s.grid.shape == tuple(shape) and np.allclose(s.grid.d, spacing)
    r = rep["particles"][pid]
    assert abs(r["norm_after"] - r["norm_before"]) < 1e3 * EPS, (route, r)
    assert abs(r["dropped"]) < 1e3 * EPS and r["spectrum"] < 1e-15 and r["outside"] < 1e-15 and r["face"] < 1e-15
    assert _rel_err(s.wave(pid), _ref(s.grid, T1)) < 1e-12, route
    s.advance(int(round((T2 - T1) / DT)))
    assert _rel_err(s.wave(pid), _ref(s.grid, T2)) < 1e-12, route
    # the free energy k^2/2 + sum 1/(8 sigma^2) is the same before and after (the spectrum carried exactly)
    E = (K0[0] ** 2 + K0[1] ** 2) / 2 + sum(1 / (8 * x * x) for x in SIG)
    assert r["E_before"] == pytest.approx(E, rel=1e-12) and r["E_after"] == pytest.approx(E, rel=1e-12)
    bal = s.checks()[pid]
    assert abs(bal["balance"]) <= bal["balance_tol"]


def test_naive_interpolation_fails_the_same_comparison():
    """Negative control: the wave at T1 put on the finer grid by linear interpolation of its samples (per axis, real
    and imaginary parts) and evolved on to T2 differs from the exact free evolution by more than 1e-3 of its peak,
    9 orders above the exact resampling; the norm is not kept either."""
    s, pid = _free_scene()
    s.advance(int(round(T1 / DT)))
    old = s.grid
    psi = s.wave(pid)
    new = S.Grid((288, 288), 1 / 3, center=old.center)
    lin = psi
    for a in range(2):
        lin = np.apply_along_axis(lambda f: np.interp(new.axes[a], old.axes[a], f.real)
                                  + 1j * np.interp(new.axes[a], old.axes[a], f.imag), a, lin)
    n_lin = float(np.sum(np.abs(lin) ** 2) * new.dV)
    s2 = Q.Scene(new.shape, new.d, dt=DT, device="cpu")
    pid2 = s2.add_particle(Q.Packet(UNIT, list(C0), list(K0), list(SIG)))
    s2.set_wave(pid2, lin)
    s2.t = T1
    s2.advance(int(round((T2 - T1) / DT)))
    err = _rel_err(s2.wave(pid2), _ref(new, T2))
    assert err > 1e-3, err
    assert abs(n_lin - 1.0) > 1e-4
    # the exact route on the same data: 1e-12
    exact = S.resample(psi, old, new)
    assert _rel_err(exact, _ref(new, T1)) < 1e-12


def test_resampling_against_the_interpolant_term_by_term():
    """Second route: the trigonometric interpolant (1/n) sum_m F_m exp(i k_m (x - x_0)) summed mode by mode in plain
    Python at the new points, against every route of ``resample_axis`` (odd and even n, the same window, the same step,
    both changed; a coarser grid keeps the modes -pi/d2 <= k < pi/d2)."""
    rng = np.random.default_rng(3)
    for n, d, n2, d2 in ((16, 0.5, 24, 1 / 3), (17, 0.5, 34, 0.25), (16, 0.5, 8, 1.0), (16, 0.5, 22, 0.5),
                         (16, 0.5, 12, 0.5), (16, 0.5, 13, 0.55), (15, 0.4, 20, 0.35)):
        f = rng.normal(size=n) + 1j * rng.normal(size=n)
        c = 0.3
        x0 = c - (n // 2) * d
        F = np.fft.fft(f)
        m = np.rint(np.fft.fftfreq(n) * n).astype(int)
        xn = c + (np.arange(n2) - n2 // 2) * d2
        lo, hi = x0 - 0.5 * d, x0 - 0.5 * d + n * d
        ref = np.zeros(n2, complex)
        r = n * d / (2 * d2)
        for j, x in enumerate(xn):
            if not (lo - 1e-12 <= x < hi - 1e-12):
                continue
            for i in range(n):
                if d2 > d * (1 + 1e-12) and not (-r - 1e-9 <= m[i] < r - 1e-9):
                    continue
                ref[j] += F[i] * np.exp(1j * 2 * math.pi * m[i] / (n * d) * (x - x0)) / n
        got = S.resample_axis(f, 0, n, d, c, n2, d2)
        assert np.max(np.abs(got - ref)) < 1e-12 * np.max(np.abs(f)), (n, d, n2, d2)


def test_the_norm_and_kinetic_energy_are_kept_to_round_off_by_refinement():
    """Refinement on the same window carries the spectrum exactly (Parseval): the norm and every moment of the
    momentum are the same to round-off for any band-limited wave (here a random one, not smooth at all); refining and
    then coarsening back returns the samples."""
    rng = np.random.default_rng(5)
    g = S.Grid((32, 24), (0.5, 0.7))
    psi = rng.normal(size=g.shape) + 1j * rng.normal(size=g.shape)
    g2 = S.Grid((64, 40), (0.25, 0.42))
    p2 = S.resample(psi, g, g2)
    assert abs(g2.norm(p2) - g.norm(psi)) < 64 * EPS * g.norm(psi)
    assert np.allclose(g2.mean_p(p2), g.mean_p(psi), rtol=0, atol=1e-13)
    back = S.resample(p2, g2, g)
    assert np.max(np.abs(back - psi)) < 1e-13 * np.max(np.abs(psi))
    assert S.regrid_losses(p2, g2, g)["spectrum"] < 1e-28


def test_changes_that_drop_or_misplace_the_wave_are_refused_with_the_number():
    """Coarser than the wave's spectrum, smaller than where it is, larger while it crosses the periodic face: each is
    refused with the measured fraction (above the stated tolerance REGRID_TOL), and nothing changes."""
    s, pid = _free_scene()
    s.advance(int(round(T1 / DT)))
    w0, g0 = s.wave(pid), s.grid
    for shape, spacing, what in (((48, 48), 2.0, "за полосой новой сетки"), ((40, 40), 0.5, "вне нового окна")):
        with pytest.raises(ValueError, match=what) as e:
            s.regrid(shape, spacing)
        assert e.value.pid == pid and e.value.value > Q.REGRID_TOL
        assert s.grid is g0 and np.array_equal(s.wave(pid), w0)
    # a packet across the periodic face: a larger window would cut it in two
    s2 = Q.Scene((64, 64), 0.5, dt=DT, device="cpu")
    p2 = s2.add_particle(Q.Packet(UNIT, [0.0, 0.0], [0.0, 0.0], [1.5, 1.5]))
    s2.set_wave(p2, np.roll(s2.wave(p2), 32, axis=0))
    with pytest.raises(ValueError, match="у граней прежнего окна") as e:
        s2.regrid((96, 96), 0.5)
    assert e.value.what == "face" and e.value.value > 0.1
    # an object whose edge (a physical length) the coarser grid cannot resolve: refused, named by its id
    s3, p3 = _free_scene()
    oid = s3.add(Q.Box([20.0, 0.0], [2.0, None], 0.05, 1.6))
    with pytest.raises(ValueError, match="край") as e:
        s3.regrid((96, 96), 1.0)
    assert e.value.oid == oid and s3.grid.shape == (192, 192)


def test_a_finer_or_coarser_grid_carries_a_wave_across_the_periodic_face():
    """The same window keeps the periodic function whole: a packet straddling the face of a closed (periodic) window is
    refined 64 -> 96 and coarsened back exactly, nothing refused (the new grid's cell starts half a step elsewhere — the
    sample n//2 sits at the centre — which is not a face; review of LB1 [error in earlier]: the browser check refused
    the 3-D preset's refinement for 3.5e-6 of its probability "at the faces"), and it then evolves as the exact free
    packet across the face (the periodic images summed)."""
    s = Q.Scene((64, 64), 0.5, dt=DT, device="cpu")
    pid = s.add_particle(Q.Packet(UNIT, [0.0, 0.0], list(K0), [1.5, 1.5]))
    shift = np.array([16.0, 0.0])  # the centre on the face x = +16 (the window is [-16.25, 15.75))
    s.set_wave(pid, S.translate(s.wave(pid), s.grid, shift))
    assert S.regrid_losses(s.wave(pid), s.grid, S.Grid((96, 96), 1 / 3))["face"] == 0.0
    rep = s.regrid((96, 96), 1 / 3)
    assert abs(rep["particles"][pid]["dropped"]) < 1e3 * EPS
    s.advance(8)
    g = s.grid
    # the periodic function: its images at (16 + 32 m, 32 n), each the packet moved there, exp(-i k0 . (16 + 32 m,
    # 32 n)) relative to the closed form's phase exp(i k0 . r)
    ref = sum(np.exp(-1j * (K0[0] * (16.0 + m * 32.0) + K0[1] * n * 32.0))
              * S.Grid(g.shape, g.d, m=1.0).free_gaussian(8 * DT, (16.0 + m * 32.0, n * 32.0), K0, (1.5, 1.5))
              for m in (-2, -1, 0, 1) for n in (-1, 0, 1))
    ph = np.vdot(ref, s.wave(pid)) / abs(np.vdot(ref, s.wave(pid)))
    assert _rel_err(s.wave(pid), ph * ref) < 1e-11
    s.regrid((64, 64), 0.5)
    assert s.grid.shape == (64, 64)


def test_absorbed_records_and_the_dropped_probability_keep_the_balance():
    """With open edges and a detector: a run, then a smaller window that drops a measured probability (tolerance raised
    for the test) — what the absorbed records held is attributed to the detector and the edges first, the dropped part
    is banked as "regrid", so norm + absorbed = 1 to round-off, and the run goes on with the balance kept."""
    edges = Q.EdgeLayers(6.0, 2.0)
    s = Q.Scene((192, 192), 0.5, dt=0.05, edges=edges, device="cpu")
    did = s.add(Q.Detector([15.0, None], [25.0, None], 0.8, 2.0))
    pid = s.add_particle(Q.Packet(UNIT, [0.0, 0.0], [2.0, 0.0], [3.0, 3.0]))
    s.advance(200)
    A0 = s.absorbed(pid)
    assert A0[f"detector {did}"] > 0.05
    with pytest.raises(ValueError):
        s.regrid((120, 120), 0.5, edges=Q.EdgeLayers(4.0, 2.0))
    rep = s.regrid((120, 120), 0.5, edges=Q.EdgeLayers(4.0, 2.0), tol=0.5)
    r = rep["particles"][pid]
    assert r["dropped"] > Q.REGRID_TOL and r["dropped"] == pytest.approx(r["outside"] * r["norm_before"], rel=1e-9)
    A1 = s.absorbed(pid)
    assert A1["regrid"] == pytest.approx(r["dropped"], rel=1e-12)
    assert A1[f"detector {did}"] == pytest.approx(A0[f"detector {did}"], rel=1e-12)
    c = s.checks()[pid]
    assert abs(c["balance"]) <= c["balance_tol"]
    s.advance(100)
    c = s.checks()[pid]
    assert abs(c["balance"]) <= c["balance_tol"]


def test_flux_planes_follow_the_grid_and_are_refused_outside_it():
    """A flux plane keeps the position it was asked for (the nearest sample of the new grid; no drift over repeated
    changes) and restarts its integral at the change: after a refinement and back, its balance (flux integrated in time
    against the probability gained beyond it; the scheme's own O(dt^2) mismatch) equals that of the same plane added
    afresh at that moment without a change, to round-off. A window that leaves it outside is refused, naming it."""
    def run(change):
        s, pid = _free_scene()
        pl = s.add_plane(0, 10.1)
        s.advance(4)
        t_change = s.t
        if change:
            s.regrid((288, 288), 1 / 3)
            assert s.planes[pl]["position"] == pytest.approx(
                s.grid.axes[0][np.argmin(np.abs(s.grid.axes[0] - 10.1))])
            s.regrid((192, 192), 0.5)
            assert s.planes[pl]["position"] == pytest.approx(10.0) and s.planes[pl]["requested"] == 10.1
        else:
            s.remove_plane(pl)
            pl = s.add_plane(0, 10.1)
        s.advance(8)
        f = s.checks()[pid]["planes"][pl]
        assert f["since"] == pytest.approx(t_change)
        return s, pl, f
    s, pl, f = run(True)
    _, _, f0 = run(False)
    assert f["flux_integral"] == pytest.approx(f0["flux_integral"], rel=1e-12, abs=1e-15)
    assert f["mismatch"] == pytest.approx(f0["mismatch"], rel=1e-9, abs=1e-15)
    with pytest.raises(ValueError, match="плоскость потока") as e:
        s.regrid((40, 40), 0.5, tol=1.0)
    assert e.value.plane == pl


# --- a wave moved, a momentum given (handles of the playground) ----------------------------------------------------
def test_a_moved_packet_is_the_same_wave_in_the_new_place():
    """A translation of the evolved free packet by s: the wave equals the exact free evolution of the packet started at
    C0 + s (up to the constant phase exp(-i k0 . s)), before and after evolving on; the norm is kept to round-off."""
    s, pid = _free_scene()
    s.advance(int(round(T1 / DT)))
    sh = np.array([7.25, -3.5])
    rep = s.move_particle(pid, sh)
    assert abs(rep["norm_after"] - rep["norm_before"]) < 1e3 * EPS
    assert np.allclose(rep["r_after"], np.array(rep["r_before"]) + sh, atol=1e-10)
    ph = np.exp(-1j * float(np.dot(K0, sh)))
    c1 = tuple(np.array(C0) + sh)
    assert _rel_err(s.wave(pid), ph * _ref(s.grid, T1, center=c1)) < 1e-12
    s.advance(int(round((T2 - T1) / DT)))
    assert _rel_err(s.wave(pid), ph * _ref(s.grid, T2, center=c1)) < 1e-12
    # too near a face: refused with the probability that would cross it, nothing changed
    w = s.wave(pid)
    with pytest.raises(ValueError, match="через грань окна") as e:
        s.move_particle(pid, [40.0, 0.0])
    assert e.value.value > Q.REGRID_TOL and np.array_equal(s.wave(pid), w)


def test_a_moved_charged_packet_keeps_its_kinetic_momentum_in_a_field():
    """In a uniform field (Landau gauge) and next to a flux tube, the translation carries the gauge factor: a packet
    moved by s right after it is prepared equals, up to a constant phase, the packet prepared at the new place (in the
    field the identity exp(i q [Lambda_{c+s}(r) - Lambda_c(r - s)]) psi(r - s) = exp(-i k . s) psi_{c+s}(r); past the
    tube, whose path relative to the packet misses it, the magnetic translation of ``flux_tube_segment`` — equal up to the
    packet's own tail at the tube, where a prepared packet carries its convention's cut: the tube here 12.7 nm from the
    packet, 1.7e-8 of its peak; at 7 nm, 4e-3 of the peak, they differ by 2.3e-4 of it); without the factor (negative
    control) the kinetic momentum would jump by q (A(r) - A(r - s))."""
    el = Q.species("electron")
    for field in (Q.MagneticField([0, 0, 0.6]), Q.FluxTube([10.0, 10.0], 2 * math.pi * 0.5, 1.0)):
        s = Q.Scene((128, 128), 0.25, dt=0.01, edges=Q.EdgeLayers(3.0, 4.0), device="cpu")
        s.add(field)
        pid = s.add_particle(Q.Packet(el, [-2.0, -1.5], [1.5, 0.5], [1.5, 1.5]))
        k0 = s.observables(pid)["k"]
        sh = np.array([3.0, 2.5])
        s.move_particle(pid, sh)
        s2 = Q.Scene((128, 128), 0.25, dt=0.01, edges=Q.EdgeLayers(3.0, 4.0), device="cpu")
        s2.add(field)
        p2 = s2.add_particle(Q.Packet(el, [1.0, 1.0], [1.5, 0.5], [1.5, 1.5]))
        a, b = s.wave(pid), s2.wave(p2)
        ph = np.vdot(b, a) / abs(np.vdot(b, a))
        assert _rel_err(a, ph * b) < (1e-9 if isinstance(field, Q.MagneticField) else 1e-7), type(field).__name__
        assert np.allclose(s.observables(pid)["k"], k0, atol=1e-6)
        # negative control: the plain translation (no gauge factor) changes the kinetic momentum in the uniform field
        if isinstance(field, Q.MagneticField):
            s3 = Q.Scene((128, 128), 0.25, dt=0.01, edges=Q.EdgeLayers(3.0, 4.0), device="cpu")
            s3.add(field)
            p3 = s3.add_particle(Q.Packet(el, [-2.0, -1.5], [1.5, 0.5], [1.5, 1.5]))
            s3.set_wave(p3, S.translate(s3.wave(p3), s3.grid, sh))
            assert np.max(np.abs(np.array(s3.observables(p3)["k"]) - k0)) > 0.5


def test_a_boost_gives_the_packet_the_new_momentum():
    """exp(i dk . r) psi: the evolved free packet continues as the exact free evolution with k0 + dk from that moment
    (the closed form shifted in time: a packet with k0 + dk whose centre at T1 is where the old one was); the mean
    kinetic wavenumber gains dk exactly, the norm is kept; a boost past the grid's band is refused."""
    s, pid = _free_scene()
    s.advance(int(round(T1 / DT)))
    dk = np.array([-2.5, 1.0])
    rep = s.boost_particle(pid, dk)
    assert np.allclose(rep["k_after"], np.array(K0) + dk, atol=1e-12)
    assert abs(rep["norm_after"] - rep["norm_before"]) < 1e3 * EPS
    g = s.grid
    X = g.mesh()
    ref1 = _ref(g, T1) * np.exp(1j * (dk[0] * X[0] + dk[1] * X[1]))
    assert _rel_err(s.wave(pid), ref1) < 1e-12
    # continued: the free propagator applied to ref1 (exact on the grid: the kinetic factor in Fourier space)
    t = T2 - T1
    K2 = g.k2()
    ref2 = np.fft.ifftn(np.exp(-0.5j * K2 * t) * np.fft.fftn(ref1))
    s.advance(int(round(t / DT)))
    assert _rel_err(s.wave(pid), ref2) < 1e-12
    E = float(np.sum((np.array(K0) + dk) ** 2)) / 2 + sum(1 / (8 * x * x) for x in SIG)
    assert s.observables(pid)["E"] == pytest.approx(E, rel=1e-9)
    w = s.wave(pid)
    with pytest.raises(ValueError, match="за полосу сетки") as e:
        s.boost_particle(pid, [7.0, 0.0])
    assert e.value.what == "alias" and np.array_equal(s.wave(pid), w)


def test_the_model_of_a_boosted_wave_is_its_spectrum():
    """After a boost the resolution rule sees the wave's measured spectrum (``_spec_model``): for a Gaussian the mean
    and sigma_k = 1/(2 sigma) (to the grid's wavenumber step over z = 3.09), so the rule's |k| + 6 sigma_k is the
    packet's own; for a wave split into two packets at -k0 and +k0 its outer part. A packet at rest in a harmonic trap,
    accelerated by it, thrown back at rest: taken (the model of the shifted packet k, 0 plus the current -<k>, would
    have been refused)."""
    s, pid = _free_scene()
    from scipy import special
    z = float(special.ndtri(1 - Q.SPECTRUM_TAIL))
    mean, sk = s._spec_model(s.wave(pid))
    dkg = 2 * math.pi / (192 * 0.5)
    assert np.allclose(mean, K0, atol=1e-12)
    assert np.allclose(sk, [1 / 6, 1 / 6], atol=dkg / z + 1e-3)
    g = s.grid
    two = g.gaussian((-10.0, 0.0), (3.0, 0.0), (3.0, 3.0)) + g.gaussian((10.0, 0.0), (-3.0, 0.0), (3.0, 3.0))
    mean, sk = s._spec_model(two)  # the outer part: the two outer tails (half the norm each) beyond 3 + z sigma_k
    assert abs(mean[0]) < 1e-9 and abs(sk[0] - (3.0 + z / 6) / z) < dkg / z + 1e-3
    t = Q.Scene((128, 128), 0.3, dt=0.02, edges=Q.EdgeLayers(4.0, 2.0), device="cpu")
    w = 0.6
    t.add(Q.HarmonicTrap([0.0, 0.0], [w, w], mass=1.0))
    p = t.add_particle(Q.Packet(UNIT, [6.0, 0.0], [0.0, 0.0], [1 / math.sqrt(2 * w)] * 2))
    t.advance(int(round(0.5 * math.pi / w / 0.02)))  # a quarter period: through the centre at full speed
    k = np.array(t.observables(p)["k"])
    assert k[0] < -3.0
    # negative control: the model shifted by dk (the packet's k = 0 plus -<k>) fails the same rule
    import copy
    import dataclasses
    sh = copy.copy(t.particles[p])
    sh.packet = dataclasses.replace(sh.packet, k=list(-k))
    assert "сетка не передаёт" in (t._resolution_reason(t._arr, [sh]) or "")
    rep = t.boost_particle(p, -k)
    assert np.allclose(rep["k_after"], 0.0, atol=1e-9)
    # with the packet's own spread s0 (what a boost uses: review LB1-p02-ux Q5) the model's |mean| + 6 sigma_k is the
    # reach plus (6 - z) s0: the Gaussian's own sigma_k, and for the two packets the outer one's |k| + 6 sigma_k = 4
    # (without s0, 6 K / z = 6.8: a wave reflected and transmitted at a wall was judged twice its reach)
    mean, sk = s._spec_model(s.wave(pid), np.array([1 / 6, 1 / 6]))
    assert np.allclose(sk, [1 / 6, 1 / 6], atol=dkg / 6 + 1e-3)
    mean, sk = s._spec_model(two, np.array([1 / 6, 1 / 6]))
    assert abs(abs(mean[0]) + 6 * sk[0] - 4.0) < dkg + 1e-3


def test_observables_against_checks_and_the_grid():
    """``observables``: E equals ``checks``' <H> (H applied) to 1e-12, also with a potential, a spin in a field and a
    charged particle in a vector potential; <r> equals ``Grid.mean_x``; <k> equals ``Grid.mean_p`` without a vector
    potential and <p - qA> with one."""
    el = Q.species("electron")
    s = Q.Scene((128, 128), 0.25, dt=0.01, edges=Q.EdgeLayers(3.0, 4.0), device="cpu")
    s.add(Q.Box([5.0, 0.0], [2.0, None], 0.3, 1.0))
    s.add(Q.MagneticField([0.0, 0.0, 0.5]))
    p1 = s.add_particle(Q.Packet(el, [-3.0, 1.0], [1.0, 0.5], [1.5, 1.5], spin=[1, 1j]))
    p2 = s.add_particle(Q.Packet(Q.species("neutron"), [-3.0, -2.0], [2.0, 0.0], [1.5, 1.5], spin=[1, 0]))
    s.advance(30)
    ch = s.checks()
    for pid in (p1, p2):
        o = s.observables(pid)
        assert o["E"] == pytest.approx(ch[pid]["energy"]["E"], rel=1e-12)
        g = s._grid_for(s.particles[pid].species.mass)
        assert np.allclose(o["r"], g.mean_x(s.wave(pid)), atol=1e-12)
        assert o["norm"] == pytest.approx(s.norm(pid), rel=1e-14)
    p = s.particles[p2]
    assert np.allclose(s.observables(p2)["k"], s._grid_for(p.species.mass).mean_p(s.wave(p2)), atol=1e-12)
    A = s.hamiltonian(s._key(s.particles[p1])).A_arrays()
    rho = s.density(p1)
    kin = np.array(s._grid_for(el.mass).mean_p(s.wave(p1))) - el.charge * np.array(
        [float(np.sum(a * rho) / np.sum(rho)) for a in A])
    assert np.allclose(s.observables(p1)["k"], kin, atol=1e-12)


@pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="no GPU")
def test_live_changes_on_gpu_equal_the_cpu():
    """The resampling, the move and the boost run on the host for both devices: the same scene on GPU 0 and on the CPU
    after a regrid, a move and a boost and steps on either side differs by the FFTs' rounding only."""
    def build(device):
        s = Q.Scene((256, 256), 0.2, dt=0.01, edges=Q.EdgeLayers(4.0, 4.0), device=device)
        s.add(Q.Box([4.0, 0.0], [1.0, None], 0.3, 0.8))
        pid = s.add_particle(Q.Packet(Q.species("electron"), [-6.0, 0.0], [2.0, 0.0], [1.5, 1.5]))
        s.advance(50)
        s.regrid((384, 384), 0.2 * 256 / 384)
        s.move_particle(pid, [1.0, 0.5])
        s.boost_particle(pid, [0.5, 0.0])
        s.advance(50)
        return s, pid
    (a, pa), (b, pb) = build("auto"), build("cpu")
    assert a.device == "gpu" and b.device == "cpu"
    assert np.max(np.abs(a.wave(pa) - b.wave(pb))) < 1e-12 * 100


# --- review LB1-p02-ux: the magnetic translation (Q1, Q2), the throw's limit (Q5), the layers (Q6, Q8), a carried wave --
def test_flux_tube_segment_is_the_line_integral_of_the_tubes_potential():
    """``flux_tube_segment`` (closed form with Owen's T) against Gauss-Legendre quadrature (400 nodes) of the tube's A
    along r - s -> r, at every point whose segment keeps 0.4 R from the axis (nearer, the quadrature itself fails); its
    gradient is A(r) - A(r - s) away from the tube's path [c, c + s] (the magnetic translation); negative control: the
    straight-line integrals from one reference point (the earlier factor) differ by the flux on a ray."""
    g = S.Grid((64, 64), 0.37, center=(0.3, -0.2))
    for flux, c, R, sh in ((math.pi, (1.1, -0.7), 0.8, (3.0, 1.5)), (-2.0, (-2.0, 3.0), 1.5, (-1.2, 4.0))):
        A = S.flux_tube(flux, c, R)
        chi = S.flux_tube_segment(g, flux, sh, c, R)
        X = g.mesh(sparse=False)
        s_ = np.array(sh)
        xg, wg = np.polynomial.legendre.leggauss(400)
        ref = np.zeros(g.shape)
        for t, w in zip(0.5 * (xg + 1), 0.5 * wg):
            ref += w * sum(A.fn(i, *[X[j] - s_[j] + t * s_[j] for j in range(2)]) * s_[i] for i in range(2))
        ra, rb = X[0] - c[0], X[1] - c[1]
        tt = np.clip((ra * s_[0] + rb * s_[1]) / (s_ @ s_), 0, 1)
        dist = np.hypot(ra - tt * s_[0], rb - tt * s_[1])
        assert np.max(np.abs(chi - ref)[dist > 0.4 * R]) < 1e-12
        # the gradient (centred differences of chi) against A(r) - A(r - s), away from the path (5 R)
        h = 1e-5
        for i in range(2):
            Xp, Xm = list(X), list(X)
            Xp[i], Xm[i] = X[i] + h, X[i] - h
            gp = S.Grid(g.shape, g.d, center=np.array(g.center) + h * np.eye(2)[i])
            gm = S.Grid(g.shape, g.d, center=np.array(g.center) - h * np.eye(2)[i])
            d_chi = (S.flux_tube_segment(gp, flux, sh, c, R) - S.flux_tube_segment(gm, flux, sh, c, R)) / (2 * h)
            dA = A.fn(i, *X) - A.fn(i, *[X[j] - s_[j] for j in range(2)])
            far = dist > 5 * R
            assert np.max(np.abs(d_chi - dA)[far]) < 1e-6
        old = A.gauge(g, np.array([-3.0, -3.0]) + s_) - A.gauge(S.Grid(g.shape, g.d, center=np.array(g.center) - s_),
                                                                np.array([-3.0, -3.0]))
        v = np.exp(1j * (old - chi))[dist > 5 * R]  # the magnetic translation's factor differs by a constant only
        assert np.max(np.abs(v - v[0])) > 0.1


def _ab_world(flux, post_V=5.0, post_R=1.6, n=192, d=0.25):
    el = Q.species("electron")
    s = Q.Scene((n, n), d, dt=0.01, edges=Q.EdgeLayers(0.1 * n * d, 4.0), device="cpu")
    s.add(Q.FluxTube([0.0, 0.0], 2 * math.pi * flux, 0.5))
    s.add(Q.Ball([0.0, 0.0], post_R, post_V, 1.0))
    pid = s.add_particle(Q.Packet(el, [-8.0, 0.0], [2.0, 0.0], [2.0, 3.0]))
    s.advance(500)
    return s, pid


def test_a_move_whose_tube_path_crosses_the_wave_is_refused():
    """A wave that has gone round an Aharonov-Bohm tube on both sides (a soft post around it), moved by (0, 6): the
    path [c0, c0 + s] the tube takes relative to the wave crosses it, so no translation keeps the wave (the flux its
    parts enclose would change; the earlier factor cut lines of phase q Phi into it, its kinetic energy +3 %): refused
    with what="gauge", the tube's probability on that path named, nothing changed. Control: flux 0, the same move taken
    and exact (eps 0, the kinetic energy unchanged)."""
    s, pid = _ab_world(0.5)
    w0 = s.wave(pid).copy()
    with pytest.raises(ValueError) as e:
        s.move_particle(pid, [0.0, 6.0])
    assert e.value.what == "gauge" and e.value.value > 1e-3 and e.value.tubes[1] > 1e-3
    assert np.array_equal(s.wave(pid), w0)
    s0, p0 = _ab_world(0.0)
    r = s0.move_particle(p0, [0.0, 6.0])
    assert r["gauge"] < 1e-20 and r["T_after"] == pytest.approx(r["T_before"], rel=1e-13)


def test_a_move_past_a_shielded_tube_is_the_magnetic_translation():
    """The wave has gone round a tube shielded by a hard post (radius 3, 60 units); a move by (0, 0.6) keeps the tube's
    path inside the post: taken, its kinetic field carried within 1e-8 (eps) and its kinetic energy to 1e-8. Second
    method: the same packet evolved in a scene whose tube stands at c0 - s, translated by s, equals the moved wave up to
    one phase within 1e-3 — the floor of that comparison is the two scenes' own evolution (2.7e-4 at no move: the
    singular gauge between them puts a phase step on rows across the post, which the spectral kinetic step couples);
    negative control: the earlier factor (integrals from <r>) is off by 3e-2."""
    def world(tube_at):
        s = Q.Scene((192, 192), 0.25, dt=0.005, edges=Q.EdgeLayers(4.8, 6.0), device="cpu")
        s.add(Q.Ball([0.0, 0.0], 3.0, 60.0, 1.0))
        s.add(Q.FluxTube(list(tube_at), 2 * math.pi * 0.37, 0.5))
        pid = s.add_particle(Q.Packet(Q.species("electron"), [-9.0, 0.6], [2.2, 0.0], [1.6, 2.6]))
        s.advance(1200)
        return s, pid
    sh = np.array([0.0, 0.6])
    sB, pB = world([0.0, 0.0])
    w0 = sB.wave(pB).copy()
    c = np.array(sB.observables(pB)["r"])
    r = sB.move_particle(pB, sh)
    assert r["gauge"] < 1e-8 and r["T_after"] == pytest.approx(r["T_before"], rel=1e-8)
    sA, pA = world(list(-sh))
    ref = S.translate(sA.wave(pA), sA.grid, sh)

    def off(x):
        ph = np.vdot(ref, x) / abs(np.vdot(ref, x))
        return float(np.sqrt(np.sum(np.abs(x - ph * ref) ** 2) / np.sum(np.abs(ref) ** 2)))
    assert off(sB.wave(pB)) < 1e-3
    g, A = sB.grid, sB._arr["A"]
    old = S.translate(w0, g, sh) * np.exp(-1j * (A.gauge(g, c + sh) - A.gauge(S.Grid(g.shape, g.d, center=-sh), c)))
    assert off(old) > 1e-2


def test_a_move_across_a_fields_edge_is_refused_and_inside_it_exact():
    """A charged wave evolved inside a field region (x in [-6, 6], B = 0.5): moved out by (12, 0) there is no same
    wave (grad chi = A(r) - A(r - s) is impossible where B(r) != B(r - s); the earlier factor changed its kinetic energy by
    -9.7 %): refused with the field named and the kinetic change; moved by (0, 3) along the strip: exact. Control B = 0:
    both taken, exact."""
    for B in (0.5, 0.0):
        s = Q.Scene((256, 256), 0.25, dt=0.01, edges=Q.EdgeLayers(6.0, 4.0), device="cpu")
        s.add(Q.MagneticField([0.0, 0.0, B], lo=[-6.0, None], hi=[6.0, None], edge=1.5))
        pid = s.add_particle(Q.Packet(Q.species("electron"), [0.0, -2.0], [1.5, 0.0], [1.5, 1.5]))
        s.advance(150)
        if B:
            with pytest.raises(ValueError) as e:
                s.move_particle(pid, [12.0, 0.0])
            assert e.value.what == "gauge" and e.value.fields == [1] and e.value.dT == pytest.approx(-0.0966, abs=2e-3)
        else:
            assert s.move_particle(pid, [12.0, 0.0])["gauge"] == 0.0
            s.move_particle(pid, [-12.0, 0.0])
        r = s.move_particle(pid, [0.0, 3.0])
        assert r["gauge"] < 1e-20 and r["T_after"] == pytest.approx(r["T_before"], rel=1e-13)


def test_the_throws_limit_is_the_scenes_and_a_split_wave_can_be_thrown():
    """A packet met a barrier and split (reflected and transmitted): ``kick_limit`` finds the largest throw the boost's
    tests take (bisection on them), the throw at that limit is taken and a little beyond it refused; stopping the wave is
    possible (the earlier model read the split wave as one Gaussian about its mean ~0, twice its reach, and refused even
    that — negative control with s0 = None); ``kick_reach`` (the limit shown) is a bound: a throw at 0.98 of it (p02's
    VMAX_MARGIN: the bound and the model read the reach with different interpolation, within a wavenumber step of the
    grid; measured here up to 1.2 % over) in each of the four axis directions is taken."""
    s = Q.Scene((192, 192), 0.3, dt=0.01, edges=Q.EdgeLayers(5.76, 4.0), device="cpu")
    s.add(Q.Box([0.0, 0.0], [1.0, None], 5.4, 1.0))
    pid = s.add_particle(Q.Packet(UNIT, [-12.0, 0.0], [3.0, 0.0], [2.0, 2.0]))
    s.advance(500)
    o = s.observables(pid)
    p = s.particles[pid]
    assert -1.0 < o["k"][0] < 2.0  # in parts: the mean between -3 and +3
    import copy as cp
    import dataclasses
    sh = cp.copy(p)
    b = s.wave(pid) * np.exp(-1j * o["k"][0] * s.grid.mesh()[0])
    sh.psi, sh.kspec, sh.sk_extra2 = b, s._spec_model(b), 0.0
    sh.packet = dataclasses.replace(p.packet, k=[0.0, 0.0])
    assert s._resolution_info(s._arr, [sh]) is not None  # negative control: the earlier model refuses the stop
    a = s.kick_limit(pid, [6.0, 0.0])
    assert a is not None and 0.0 < a < 1.0
    with pytest.raises(ValueError):
        s.transform_particle(pid, dk=np.array([(a + 0.01) * 6.0, 0.0]) - np.array(o["k"]))
    reach = s.kick_reach(pid)
    assert reach > 0
    for u in ([1, 0], [-1, 0], [0, 1], [0, -1]):
        assert s.kick_limit(pid, list(0.98 * reach * np.array(u, float))) == 1.0, u
    r = s.transform_particle(pid, dk=np.array([a * 6.0, 0.0]) - np.array(o["k"]))
    assert r["k_after"][0] == pytest.approx(a * 6.0, abs=1e-5)  # the boost of a tail at the band (<= 1e-6 of it)


def test_a_smaller_window_does_not_move_the_absorbing_layers_over_the_wave():
    """Open edges: a smaller window whose new layers (the edges' width) would cover more than 1e-6 of the wave that is
    outside the old layers now is refused (what="layers", nothing changed: the layers would absorb it); a smaller one
    whose layers stay clear is taken, the report giving the shares inside the old and the new layers. Negative control:
    closed edges, the same window taken (no layers)."""
    s = Q.Scene((192, 192), 0.5, dt=0.05, edges=Q.EdgeLayers(9.6, 2.0), device="cpu")
    pid = s.add_particle(Q.Packet(UNIT, [-18.0, 0.0], [0.0, 0.0], [2.0, 2.0]))
    w = s.wave(pid).copy()
    with pytest.raises(ValueError) as e:
        s.regrid((120, 120), 0.5, edges=Q.EdgeLayers(6.0, 2.0))  # window 60: layers from |x| > 24
    assert e.value.what == "layers" and e.value.value > 1e-6 and np.array_equal(s.wave(pid), w)
    rep = s.regrid((160, 160), 0.5, edges=Q.EdgeLayers(8.0, 2.0))  # window 80: layers from |x| > 32
    r = rep["particles"][pid]
    assert r["exposed"] < 1e-6 and r["in_new_layers"] >= r["exposed"] and r["in_layers"] < 1e-6
    c = Q.Scene((192, 192), 0.5, dt=0.05, edges=None, device="cpu")
    pc = c.add_particle(Q.Packet(UNIT, [-18.0, 0.0], [0.0, 0.0], [2.0, 2.0]))
    assert c.regrid((120, 120), 0.5)["particles"][pc]["exposed"] == 0.0


def test_a_move_with_open_edges_counts_only_what_wraps_into_the_window():
    """With open edges a wave's part that a move carries across a face lands in the far side's absorbing layer when the
    move is shorter than the layer: it is absorbed there (reported as ``far_layer``), not refused; what lands beyond the
    layer, inside the window, is refused as before (``wrap``). ``wrap_fraction`` with the margin against without."""
    s = Q.Scene((128, 128), 0.5, dt=0.05, edges=Q.EdgeLayers(6.4, 2.0), device="cpu")
    pid = s.add_particle(Q.Packet(UNIT, [22.0, 0.0], [0.0, 0.0], [1.2, 1.2]))
    psi = s.wave(pid)
    assert S.wrap_fraction(psi, s.grid, [5.0, 0.0]) > 1e-6 and S.wrap_fraction(psi, s.grid, [5.0, 0.0], 6.4) == 0.0
    r = s.move_particle(pid, [5.0, 0.0])
    assert r["wrap"] == 0.0 and r["far_layer"] > 1e-6
    with pytest.raises(ValueError) as e:
        s.move_particle(pid, [12.0, 0.0])
    assert e.value.what == "wrap"


def test_a_wave_carried_into_another_scene_is_the_same_wave():
    """``adopt_wave`` (a new world of the same dimension, plan P16.1): the wave on a finer grid is the exact resampling
    of the old one, its norm and records kept; a wave this grid cannot hold, or a spinor where the particle is a scalar,
    is refused and nothing changes."""
    a, pa = _free_scene()
    a.advance(8)
    psi, n0 = a.wave(pa).copy(), a.norm(pa)
    b = Q.Scene((288, 288), 1 / 3, dt=DT, device="cpu")
    pb = b.add_particle(Q.Packet(UNIT, list(C0), list(K0), list(SIG)))
    rep = b.adopt_wave(pb, psi, (192, 192), 0.5, banked={"edges": 0.25})
    assert np.max(np.abs(b.wave(pb) - S.resample(psi, a.grid, b.grid))) == 0.0
    assert rep["norm_after"] == pytest.approx(n0, rel=1e-13) and b.absorbed(pb) == {"edges": 0.25}
    c = Q.Scene((48, 48), 2.0, dt=DT, device="cpu")
    pc = c.add_particle(Q.Packet(UNIT, list(C0), [0.0, 0.0], list(SIG)))
    w = c.wave(pc).copy()
    with pytest.raises(ValueError) as e:
        c.adopt_wave(pc, psi, (192, 192), 0.5)  # K0 = (1.5, -0.5) and its spread beyond the band pi/2 of this grid
    assert e.value.what == "spectrum"
    with pytest.raises(ValueError):
        c.adopt_wave(pc, np.stack([w, 0 * w]), (48, 48), 2.0)
    assert np.array_equal(c.wave(pc), w)
