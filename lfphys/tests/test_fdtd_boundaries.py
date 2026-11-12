# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P1 (B8): the convolutional PML (Roden & Gedney 2000) — the reflection of a broadband cylindrical (2-D) or
spherical (3-D) pulse at normal and oblique incidence, measured the usual way: the field at probes near the layer
against a reference run in a domain so large that its own boundaries are not reached within the time window. Graded layers (m = 3, sigma at the optimum 0.8 (m + 1) / (dx eta)) against the negative
controls: a thin layer (2 cells) and an un-graded one (constant sigma, m = 0), which reflect far more.

Measured (2026-11-04, dx = 0.05, pulse 1.0 +- 0.5 (sigma_f), source 3 cells from the layer; dB of the reference's
peak at five probes, the first two at normal incidence, the others oblique up to ~70 deg): 10 cells m = 3:
-88...-95; 20 cells: -106...-113; 6 cells: -56...-79; 10 cells m = 4, kappa_max 5, alpha_max 0.2: -79...-83;
controls: 2 cells -15...-30, un-graded (m = 0, sigma_factor 0.25) -22...-28, un-graded at the full sigma -9...-15.
"""

import numpy as np
import pytest

from lfphys.core.em import fdtd as F

DX = 0.05
PROF = F.ModulatedGaussian(1.0, fwidth=0.5)
OFFS = [(0.0, -0.1), (0.0, 0.25), (0.5, -0.1), (0.9, -0.1), (0.9, 0.5)]
STEPS = 440


def _run(L, src, pml, pol):
    comp = "ez" if pol == "tm" else "hz"
    if pol == "te":  # Hz lives at cell centres: put the source on one, as in the reference
        src = (src[0] + DX / 2, src[1] + DX / 2)
    w = F.FDTD((L, L), DX, pol=pol, pml=pml)
    w.add_source(F.CurrentSource(comp, PROF, position=src))
    ids = [w.add_probe((src[0] + a, src[1] + b), [comp]) for a, b in OFFS]
    w.advance(STEPS)
    return np.array([w.probe(i)[comp] for i in ids])


@pytest.fixture(scope="module", params=["tm", "te"])
def reference(request):
    return request.param, _run(14.0, (7.0, 7.0), 10, request.param)


def _db(test, ref):
    return 20 * np.log10(np.max(np.abs(test - ref), axis=1) / np.max(np.abs(ref), axis=1))


def test_graded_cpml_reflects_below_minus_80_db(reference):
    pol, ref = reference
    db10 = _db(_run(2.0, (1.0, 0.15), F.PML(10, 3), pol), ref)
    db20 = _db(_run(2.0, (1.0, 0.15), F.PML(20, 3), pol), ref)
    assert np.all(db10 < -80), db10
    assert np.all(db20 < -100), db20
    assert np.all(db20 < db10 - 10)


def test_thin_and_ungraded_layers_reflect_far_more(reference):
    """The negative controls: the same comparison sees the reflection of a 2-cell layer and of an un-graded one."""
    pol, ref = reference
    thin = _db(_run(2.0, (1.0, 0.15), F.PML(2, 3), pol), ref)
    flat = _db(_run(2.0, (1.0, 0.15), F.PML(10, 0.0, sigma_factor=0.25), pol), ref)
    assert np.all(thin > -40) and np.all(flat > -40), (thin, flat)


def test_cfs_parameters_keep_the_layer_absorbing():
    """kappa > 1 and alpha > 0 (the complex-frequency-shifted stretch that CPML makes possible)."""
    ref = _run(14.0, (7.0, 7.0), 10, "tm")
    db = _db(_run(2.0, (1.0, 0.15), F.PML(10, 4, kappa_max=5.0, alpha_max=0.2), "tm"), ref)
    assert np.all(db < -70), db


def test_cpml_3d():
    """A 3-D dipole pulse 3 cells from the layer (dx = 0.1, 20 cells per wavelength at the centre frequency)."""
    prof = F.ModulatedGaussian(0.5, fwidth=0.25)

    def run(L, c, pml):
        w = F.FDTD((L, L, L), 0.1, pml=pml)
        w.add_source(F.CurrentSource("ez", prof, position=c))
        ids = [w.add_probe((c[0] + a, c[1] + b, c[2]), ["ez"]) for a, b in ((0.0, -0.2), (0.6, -0.2), (0.0, 0.4))]
        w.advance(170)
        return np.array([w.probe(i)["ez"] for i in ids])

    ref = run(8.0, (4.0, 4.0, 4.0), 8)
    db = _db(run(1.6, (0.8, 0.3, 0.8), F.PML(10, 3)), ref)
    thin = _db(run(1.6, (0.8, 0.3, 0.8), F.PML(2, 3)), ref)
    assert np.all(db < -70), db
    assert np.all(thin > db + 30), (thin, db)


def test_cpml_at_grazing_incidence():
    """Review B8-fdtd F10: the default layer's -88...-95 dB holds from normal incidence to ~70 deg (the geometry
    above). Along a long boundary — the source 3 cells above the lower layer, probes 2, 4, 6 units along it (image-path
    angles 81.5, 85.7, 87.1 deg) — the 10-cell layer reflects -74.5 / -57.6 / -52.4 dB (the reference: a 24 x 24
    domain whose boundaries are not reached within the window); a 20-cell layer -114...-136 dB. For grazing
    geometries 16-20 cells are needed (stated in the module's validity)."""
    far = [(2.0, 0.0), (4.0, 0.0), (6.0, 0.0), (6.0, 0.6)]
    steps = int(9.0 / (0.5 * DX))

    def run(Lx, Ly, src, pml):
        w = F.FDTD((Lx, Ly), DX, pol="tm", pml=pml)
        w.add_source(F.CurrentSource("ez", PROF, position=src))
        ids = [w.add_probe((src[0] + a, src[1] + b), ["ez"]) for a, b in far]
        w.advance(steps)
        return np.array([w.probe(i)["ez"] for i in ids])

    ref = run(24.0, 24.0, (12.0, 12.0), 10)
    db10 = _db(run(11.0, 4.0, (2.5, 0.15), F.PML(10, 3)), ref)
    db20 = _db(run(11.0, 4.0, (2.5, 0.15), F.PML(20, 3)), ref)
    assert np.all(db10[1:3] > -65) and np.all(db10 < -45), db10  # far worse than the -80 dB of the other tests
    assert np.all(db20 < -105), db20
