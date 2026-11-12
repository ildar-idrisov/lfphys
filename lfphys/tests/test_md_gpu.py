# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Molecular dynamics on GPU 0 (kernel "md.pair_forces"): the pair forces equal the CPU's bit for bit (the same
elementwise IEEE operations; per-particle sums in numpy.bincount's order), so a trajectory is the same on both
devices; energy and virial sums agree to rounding. Skipped without a GPU (LFPHYS_NO_GPU or no device)."""

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.md import system
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import WCA, LennardJones

pytestmark = pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="no GPU")


@pytest.mark.parametrize("pair", [LennardJones(2.5, "energy"), LennardJones(2.5, "force"), WCA()],
                         ids=["lj-energy", "lj-force", "wca"])
def test_gpu_equals_cpu_bit_for_bit(pair):
    backend.configure({"kernels": {system.KERNEL: {"device": "gpu"}}})
    try:
        L = 16.0
        mk = []
        for dev in ("auto", "cpu"):
            md = MD(dim=3, box=(L, L, L), pair=pair, dt=0.004, seed=3, device=dev)
            md.add_species("A")
            md.add_species("B", mass=2.0, sigma=1.1, epsilon=0.8)
            md.fill("A", n=1200, T=1.0, region=([0, 0, 0], [L, L, 10]))
            md.fill("B", n=300, T=1.0, region=([0, 0, 10.5], [L, L, L]))
            mk.append(md)
        g, c = mk
        assert g.cost_estimate()["device"] == "gpu" and c.cost_estimate()["device"] == "cpu"
        assert np.array_equal(g.forces(), c.forces())
        g.step(60)
        c.step(60)
        assert np.array_equal(g.positions(True), c.positions(True))
        assert np.array_equal(g.velocities(), c.velocities())
        assert g.potential_energy()["pair"] == pytest.approx(c.potential_energy()["pair"], rel=1e-12)
        assert np.allclose(g.pressure()["tensor"], c.pressure()["tensor"], rtol=1e-12)
        assert backend.used()[system.KERNEL]["drawn"]["device"] in ("gpu", "cpu")
    finally:
        backend.configure({})


def test_kernel_is_registered():
    k = backend.kernels()
    assert system.KERNEL in k and k[system.KERNEL].gpu
