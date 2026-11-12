# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P11: the device and precision policy of lfphys.core.backend, and the GPU kernel (the angular spectrum) against
its CPU version. The GPU tests run when the container is given GPU 0 (docker run --gpus '"device=0"'); otherwise they
are skipped, and everything else still runs."""

import json
import math
import os
import subprocess
import sys

import numpy as np
import pytest

from lfphys.core import backend as B
from lfphys.core.optics import angular_spectrum as AS
from lfphys.i18n import T

K = 2 * math.pi


@pytest.fixture(autouse=True)
def _defaults():
    B.configure(None)
    B.reset_used()
    yield
    B.configure(None)


def _gpu():
    return B.devices()["gpu"]["available"]


def _field(n=128, dx=1 / 6):
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    return np.exp(-((X - 0.4) ** 2 + (Y + 0.3) ** 2) / 2.0) * np.exp(1j * (0.9 * X - 0.4 * Y)), dx


def test_settings_are_validated_with_notes(ru):
    notes = B.configure({"kernels": {
        "optics.angular_spectrum": {"device": "gpu", "precision": "fp32"},
        "gravity.geodesics": {"device": "gpu", "precision": "fp32"},
        "no.such": {"device": "cpu"}}})
    s = B.settings()["kernels"]
    assert s["optics.angular_spectrum"] == {"device": "gpu", "precision": "fp32"}  # fp32 validated for it
    assert s["gravity.geodesics"] == {"device": "cpu", "precision": "fp64"}  # no GPU code, fp32 not validated
    assert any("unknown kernel" in str(n) for n in notes) and any("no GPU implementation" in str(n) for n in notes)
    assert any("not validated" in str(n) for n in notes)
    assert any("неизвестное ядро" in ru(n) for n in notes) and any("нет GPU-реализации" in ru(n) for n in notes)


def test_auto_takes_the_cpu_for_small_problems_and_checks_are_fp64():
    ch = B.choose("optics.angular_spectrum", 16)
    assert ch.device == "cpu" and ch.precision == "fp64"
    B.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu", "precision": "fp32"}}})
    assert B.choose("optics.angular_spectrum", 10**6, check=True).precision == "fp64"
    assert B.choose("optics.angular_spectrum", 10**6).precision == "fp32"
    u = B.used()["optics.angular_spectrum"]  # what is drawn and what is checked, recorded apart (review B1-4)
    assert u["drawn"]["device"] == "cpu" and u["drawn"]["precision"] == "fp32"
    assert u["check"]["precision"] == "fp64" and u["check"]["size"] == 10**6


def test_malformed_settings_are_refused_and_unusable_gpu_is_noted(ru):
    for bad in ({"kernels": []}, {"kernels": {"optics.angular_spectrum": "gpu"}}, {"crossover": [1]},
                {"kernels": {"optics.angular_spectrum": {"device": 1}}}):
        with pytest.raises(ValueError):
            B.configure(bad)
    notes = B.configure({"crossover": {"optics.angular_spectrum": True}})
    assert notes and B.settings()["crossover"] == {}  # a bool is not a size
    r = subprocess.run([sys.executable, "-m", "lfphys.core.backend", "--configure", "-"], input='{"kernels": []}',
                       capture_output=True, text=True)
    err = json.loads(r.stdout)["error"]
    assert r.returncode == 2 and str(T(err)) == "settings: 'kernels' must be a JSON object (kernel → value)"
    assert ru(err) == "настройки: 'kernels' — объект JSON (ядро → значение)"  # a translatable text (lfphys.i18n)
    env = dict(os.environ, LFPHYS_NO_GPU="1")
    code = ("import json; from lfphys.core import backend as B; "
            "print(json.dumps(B.configure({'kernels': {'optics.angular_spectrum': {'device': 'gpu'}}})))")
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
    notes = [T(n) for n in json.loads(out.stdout)]  # review B1-17
    assert any("not available" in str(n) for n in notes) and any("недоступен" in ru(n) for n in notes)


def test_kernel_catalogue_states_why_cpu_only_kernels_stay_on_the_cpu():
    ks = B.kernels()
    assert ks["optics.angular_spectrum"].gpu
    for name in ("certified.arb", "gravity.geodesics", "quantum.transfer", "quantum.schrodinger1d"):
        assert not ks[name].gpu and ks[name].cpu_reason


def test_command_line_reports_devices_and_kernels():
    r = subprocess.run([sys.executable, "-m", "lfphys.core.backend", "--devices", "--kernels"], capture_output=True,
                       text=True, check=True)
    d = json.loads(r.stdout)
    assert d["devices"]["cpu"]["available"] and "gpu" in d["devices"]
    assert any(k["name"] == "optics.angular_spectrum" for k in d["kernels"])
    assert subprocess.run([sys.executable, "-m", "lfphys.core.backend", "--help"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_gpu_equals_cpu_in_fp64():
    U0, dx = _field()
    zs = [0.5, 3.0]
    B.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
    cpu = AS.propagate_field(U0, dx, K, zs)
    cpu_sl = AS.propagate_slice(U0, dx, K, zs, axis=1, at=0.123)
    B.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
    gpu = AS.propagate_field(U0, dx, K, zs)
    gpu_sl = AS.propagate_slice(U0, dx, K, zs, axis=1, at=0.123)
    assert B.used()["optics.angular_spectrum"]["drawn"]["device"] == "gpu"
    assert isinstance(gpu, np.ndarray) and gpu.dtype == np.complex128
    scale = np.max(np.abs(cpu))
    assert np.max(np.abs(gpu - cpu)) < 1e-13 * scale and np.max(np.abs(gpu_sl - cpu_sl)) < 1e-13 * scale
    # a source given by its spectrum (evaluated on the device on the GPU) and a tilted plane (the source turned)
    from lfphys.core import geometry as G
    from lfphys.core.optics import aperture_fields as AF
    src = AS.Spectral((128, 128), AF.rect_spectrum([(-1.0, 0.4, -0.7, 1.3)]))
    pl = G.Plane.horizontal((0.3, -0.8, 0.5), origin=(0.1, 0.2, 3.0))
    out = {}
    for dev in ("cpu", "gpu"):
        B.configure({"kernels": {"optics.angular_spectrum": {"device": dev}}})
        out[dev] = AS.propagate_plane(src, 0.25, K, pl, (-3.0, 3.0), np.linspace(-2.0, 2.0, 9), pad=4)[1]
        assert B.used()["optics.angular_spectrum"]["drawn"]["device"] == dev
    assert np.nanmax(np.abs(out["gpu"] - out["cpu"])) < 1e-12 * np.nanmax(np.abs(out["cpu"]))


@pytest.mark.parametrize("device", ["cpu", "gpu"])
def test_angular_spectrum_fp32_within_its_bound(device):
    """The fp32 bound declared for the kernel (max |U32 - U64| / max |U64| <= 1e-5) over its declared domain,
    k z up to 2000 rad (review B1-6: with the phase formed in fp32 the error grew to 1.2e-5 at k z = 1676), on a 3-D
    field and a 2-D one, and for the slice route."""
    if device == "gpu" and not _gpu():
        pytest.skip("no GPU given to this container")
    spec = B.kernels()["optics.angular_spectrum"].precisions["fp32"]
    bound = spec["bound"]
    assert "2000" in str(spec["domain"])
    U0, dx = _field(256)
    zs = [0.0, 2.0, 8.0, 100.0, 2000.0 / K]
    B.configure({"kernels": {"optics.angular_spectrum": {"device": device, "precision": "fp64"}}})
    ref = AS.propagate_field(U0, dx, K, zs)
    ref1 = AS.propagate_field(U0[:, 128], dx, K, zs)
    refs = AS.propagate_slice(U0, dx, K, zs, axis=1, at=0.123)
    B.configure({"kernels": {"optics.angular_spectrum": {"device": device, "precision": "fp32"}}})
    u32 = AS.propagate_field(U0, dx, K, zs)
    u321 = AS.propagate_field(U0[:, 128], dx, K, zs)
    u32s = AS.propagate_slice(U0, dx, K, zs, axis=1, at=0.123)
    assert u32.dtype == np.complex64 and B.used()["optics.angular_spectrum"]["drawn"]["precision"] == "fp32"
    errs = [np.max(np.abs(a - b)) / np.max(np.abs(b)) for a, b in ((u32, ref), (u321, ref1), (u32s, refs))]
    assert max(errs) <= bound, errs
    assert min(errs) > 1e-9  # it really ran in single precision


@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_gpu_out_of_memory_falls_back_to_the_cpu_and_the_pool_is_released():
    """Review B1-7: GPU memory shared with other services. A call that does not fit is redone on the CPU (the reason
    recorded); "auto" does not take the GPU for a footprint above the free memory; the pool is empty after a call."""
    import cupy as cp
    U0, dx = _field(256)
    B.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
    ref = AS.propagate_field(U0, dx, K, [1.0, 3.0])
    B.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
    pool = cp.get_default_memory_pool()
    pool.set_limit(size=1 << 20)  # 1 MiB: the 512 x 512 padded field does not fit
    try:
        out = AS.propagate_field(U0, dx, K, [1.0, 3.0])
    finally:
        pool.set_limit(size=0)
    u = B.used()["optics.angular_spectrum"]["drawn"]
    assert u["device"] == "cpu" and "memory" in str(T(u["reason"]))
    assert np.max(np.abs(out - ref)) < 1e-13 * np.max(np.abs(ref))
    AS.propagate_field(U0, dx, K, [1.0])
    assert B.used()["optics.angular_spectrum"]["drawn"]["device"] == "gpu" and pool.used_bytes() == 0
    assert pool.total_bytes() == 0
    B.configure(None)
    ch = B.choose("optics.angular_spectrum", 10**8, footprint=1 << 50)  # a petabyte: never on the GPU
    assert ch.device == "cpu" and "free" in str(ch.reason)


@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_calibration_measures_a_crossover():
    out = B.calibrate(["optics.angular_spectrum"])["optics.angular_spectrum"]
    assert len(out["rows"]) == len(B.kernels()["optics.angular_spectrum"].bench_sizes)
    assert all(r["gpu_s"] is not None and r["cpu_s"] > 0 for r in out["rows"])
    assert out["crossover"] is not None  # the GPU wins for the large FFTs on this host


@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_gpu_is_pinned_by_its_pci_bus_id():
    """Review B1-8: with LFPHYS_GPU_PCI set, a device 0 on another bus is refused (everything runs on the CPU), and the
    PCI order is the default."""
    code = "import json; from lfphys.core import backend as B; import os; d = B.devices()['gpu']; " \
           "print(json.dumps({'gpu': d, 'order': os.environ.get('CUDA_DEVICE_ORDER')}))"
    pci = B.devices()["gpu"]["pci_bus_id"]
    ok = json.loads(subprocess.run([sys.executable, "-c", code], env=dict(os.environ, LFPHYS_GPU_PCI=pci),
                                   capture_output=True, text=True, check=True).stdout)
    assert ok["gpu"]["available"] and ok["order"] == "PCI_BUS_ID"
    bad = json.loads(subprocess.run([sys.executable, "-c", code], env=dict(os.environ, LFPHYS_GPU_PCI="0000:99:00.0"),
                                    capture_output=True, text=True, check=True).stdout)
    assert not bad["gpu"]["available"] and "LFPHYS_GPU_PCI" in bad["gpu"]["reason"]


def test_every_kernel_module_imports():
    """The kernel modules import (a broken one would only be left out at run time, with its error shown)."""
    ks = B.kernels()
    assert not B.import_errors(), B.import_errors()
    for name in ("optics.angular_spectrum", "quantum.split_operator", "relativity.raytrace"):
        assert name in ks and ks[name].gpu


def test_a_hot_gpu_sends_kernels_to_the_cpu_until_it_cools(monkeypatch):
    """STATUS V23 c: from pause_c on the kernels stay off the GPU until it has cooled to resume_c (hysteresis); the
    reading is cached for period_s; an unreadable sensor never blocks the GPU."""
    monkeypatch.setitem(B.THERMAL, "period_s", 0.0)
    temps = iter([60.0, 83.0, 75.0, 71.0, 69.0, 80.0])
    B.set_temperature_reader(lambda: next(temps))
    try:
        assert [B._gpu_hot() for _ in range(6)] == [False, True, True, True, False, False]
        B.set_temperature_reader(lambda: None)
        assert B._gpu_hot() is False and B.thermal()["temp"] is None
        B.set_temperature_reader(lambda: 1 / 0)
        assert B._gpu_hot() is False and "ZeroDivisionError" in B.thermal()["error"]
        monkeypatch.setitem(B.THERMAL, "period_s", 3600.0)  # cached: no new reading within the period
        calls = []
        B.set_temperature_reader(lambda: calls.append(1) or 90.0)
        B._gpu_hot(); B._gpu_hot()
        assert len(calls) == 1
    finally:
        B.set_temperature_reader(None)


@pytest.mark.parametrize("unreadable", [lambda: None, lambda: 1 / 0])
def test_a_sensor_that_fails_while_hot_keeps_the_kernels_on_the_cpu(monkeypatch, unreadable, ru):
    """Review B6-F7: after a hot reading an unreadable sensor (None or an exception) keeps the GPU off with a reason
    that names the last valid temperature; choose() must not fail (it formatted None). The GPU is stubbed as
    available (no CuPy needed: the choice ends on the CPU)."""
    monkeypatch.setitem(B.THERMAL, "period_s", 0.0)
    monkeypatch.setattr(B, "_cupy", lambda: (None, {"available": True}))
    B.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
    try:
        B.set_temperature_reader(lambda: 90.0)
        assert B.choose("optics.angular_spectrum", 10 ** 6).device == "cpu"
        monkeypatch.setattr(B, "_TEMPERATURE", unreadable)  # the reader fails; the state stays hot
        ch = B.choose("optics.angular_spectrum", 10 ** 6)
        assert ch.device == "cpu" and "cannot be read, last 90 °C" in str(ch.reason), ch.reason
        assert "не читается, последняя 90 °C" in ru(ch.reason)
        assert B.thermal()["hot"] is True and B.thermal()["last_temp"] == 90.0
    finally:
        B.set_temperature_reader(None)
        B.configure(None)


@pytest.mark.skipif(not _gpu(), reason="needs GPU 0")
def test_a_hot_gpu_is_not_chosen(monkeypatch):
    monkeypatch.setitem(B.THERMAL, "period_s", 0.0)
    B.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
    try:
        B.set_temperature_reader(lambda: 90.0)
        ch = B.choose("optics.angular_spectrum", 10 ** 6)
        assert ch.device == "cpu" and "cooling down" in str(ch.reason)
        B.set_temperature_reader(lambda: 50.0)
        assert B.choose("optics.angular_spectrum", 10 ** 6).device == "gpu"
    finally:
        B.set_temperature_reader(None)
        B.configure(None)


def test_pci_bus_ids_of_different_tools_compare_equal():
    """LFPHYS_GPU_PCI may be written as nvidia-smi prints it (8-digit domain) or as CuPy reports it (4-digit): both are
    the same device; another bus is not (negative control); text that is no bus id gives None."""
    assert B.pci_key("00000000:01:00.0") == B.pci_key("0000:01:00.0") == B.pci_key("01:00.0") == (0, 1, 0, 0)
    assert B.pci_key("0000:02:00.0") != B.pci_key("0000:01:00.0")
    assert B.pci_key("") is None and B.pci_key("gpu0") is None
