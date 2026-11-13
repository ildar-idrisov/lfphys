# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Devices and precision of the engine's heavy kernels (plan P11; owner, 2026-10-24).

* Every heavy computation is a **kernel** (``KernelSpec``): a name, what it computes, whether it has a GPU
  implementation (and why not, if not: certified Arb references, sequential ODE integrations and mpmath stay on the
  CPU), the precisions it allows with the evidence for each, a benchmark and the problem size above which the GPU
  pays (measured on this host; ``calibrate`` measures it again).
* A kernel asks ``choose(name, size)`` for the array module (NumPy or CuPy), the device and its dtypes. The choice
  follows the settings (``configure``): per kernel "auto" (the default) | "cpu" | "gpu", and a precision. "auto" takes
  the GPU only when one is usable, the kernel has a GPU implementation and the problem is at least the kernel's
  crossover size; otherwise the CPU. A kernel moves only its heavy part to the GPU and returns NumPy arrays.
* **Precision**: fp64 always. fp32 only for kernels whose fp32 results were validated against fp64 (the bound and the
  test are in the kernel's ``precisions``), and only for what is drawn: ``choose(..., check=True)`` (references,
  checks) is always fp64. fp16 is not offered: complex FFTs in half precision lose ~1e-3, which visibly changes
  results, and the GPU of this host has no complex half-precision FFT worth the loss.
* **GPU 0 only** (GPU 1 of this host computes wrongly): the container is given only GPU 0; on a bare host the
  backend sets CUDA_DEVICE_ORDER=PCI_BUS_ID (CUDA's default order is "fastest first", not the PCI order) and
  CUDA_VISIBLE_DEVICES=0 if they are unset, before CuPy is imported; with LFPHYS_GPU_PCI set (e.g. 0000:01:00.0) a
  device with another PCI bus id is refused (review B1-8).
* **Memory**: "auto" takes the GPU only if the kernel's estimated footprint fits in 80 % of the free GPU memory; a
  kernel that still runs out of GPU memory frees the pool and redoes the call on the CPU; after every GPU call the
  pool's free blocks are returned, so an idle run holds no GPU memory beyond the CUDA context (review B1-7).
* ``used()`` reports, per kernel, what its drawn results and its checks last ran on (device, precision, reason),
  for a run's header (review B1-4: one record per kernel hid the precision of what is drawn).
* **Temperature** (STATUS V23 c: the host hung once after ~18 min of full GPU load; a playground session runs for
  hours): before a kernel takes the GPU its temperature is read (NVML, read only; at most every ``THERMAL["period_s"]``
  seconds); from ``pause_c`` on, kernels run on the CPU until the GPU has cooled to ``resume_c`` (hysteresis), and the
  reason says so. Results then come from the CPU (equal within the kernel's GPU = CPU tolerance, not bit for bit).

Command line (the server calls it in a subprocess, so the server process itself never holds the GPU):
``python -m lfphys.core.backend --devices`` | ``--kernels`` | ``--calibrate`` | ``--configure -`` (settings JSON on
stdin; exit status 2 with {"error": ...} when they are malformed).
"""

from __future__ import annotations

import json
import os
import platform
import time
from dataclasses import dataclass, field

import numpy as np

from lfphys.i18n import T, text_of

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": T("Devices and precision of computation (CPU / GPU)"),
    "statement": T("The engine's heavy kernels run on the CPU or on GPU 0: by default where it is faster (measured), "
                   "or as chosen; precision fp64, fp32 only where validated and only for what is drawn; references and "
                   "checks always in fp64."),
    "validity": T("the GPU through CuPy (CUDA 12); without a GPU everything runs on the CPU (NumPy) by the same "
                  "formulas"),
    "basis": ["CuPy (MIT)", "NVIDIA CUDA runtime, cuFFT"],
    "conflicts": [],
}

DEVICES = ("auto", "cpu", "gpu")
PRECISIONS = ("fp64", "fp32")
_DTYPES = {"fp64": (np.float64, np.complex128), "fp32": (np.float32, np.complex64)}


@dataclass
class KernelSpec:
    name: str
    title: T  # for the settings page (a translatable text, lfphys.i18n)
    what: T  # what it computes, where it is used (a translatable text)
    gpu: bool  # has a GPU implementation
    cpu_reason: T | str = ""  # why it stays on the CPU (when gpu is False; a translatable text)
    precisions: dict = field(default_factory=lambda: {"fp64": {"allowed": True}})
    crossover: int | None = None  # problem size (points) from which "auto" takes the GPU; None: never
    crossover_note: T | str = ""  # how the crossover was measured (a translatable text)
    bench: object = None  # callable(size, xp, complex_dtype) -> None, runs the kernel once at that size
    bench_sizes: tuple = ()

    def public(self) -> dict:
        return {"name": self.name, "title": self.title, "what": self.what, "gpu": self.gpu,
                "cpu_reason": self.cpu_reason, "precisions": self.precisions, "crossover": self.crossover,
                "crossover_note": self.crossover_note}


_KERNELS: dict[str, KernelSpec] = {}
_SETTINGS: dict = {"kernels": {}, "crossover": {}}
_USED: dict = {}
_GPU: dict | None = None
_CP = None

# kernels that stay on the CPU, listed so that the settings page can say why
_CPU_ONLY = [
    KernelSpec("certified.arb", T("Rigorous bounds (Arb)"), T("ball arithmetic for references and tests"), False,
               T("Arb (python-flint) exists only for the CPU; these are references, not bulk computation")),
    KernelSpec("gravity.geodesics", T("Geodesics and orbits"), T("integration of the equations of motion (u31, u34)"),
               False, T("sequential integration of one ODE: nothing to parallelise on a GPU")),
    KernelSpec("quantum.transfer", T("Transfer matrices"), T("stationary transmission through barriers (u33, u35)"),
               False, T("a loop over layers of small 2×2 matrices: the GPU overhead exceeds the gain")),
    KernelSpec("quantum.schrodinger1d", T("Schrödinger equation in 1-D"), T("a wave packet (u33)"), False,
               T("a grid of ≤ 32768 points and absorption applied at every step: slower on a GPU (2-D and 3-D: the "
                 "quantum.split_operator kernel, with a GPU)")),
]


def register(spec: KernelSpec) -> KernelSpec:
    _KERNELS[spec.name] = spec
    return spec


_KERNEL_MODULES = (("optics.angular_spectrum", "optics.angular_spectrum"),
                   ("quantum.split_operator", "quantum.schrodinger_nd"),
                   ("relativity.raytrace", "raytrace"),
                   ("gravity.kerr_shadow", "gravity.kerr_shadow"),
                   ("fluids.lbm", "fluids.lbm"),
                   ("md.pair_forces", "md.system"),
                   ("em.fdtd", "em.fdtd"))
_IMPORT_ERRORS: dict = {}


def kernels() -> dict[str, KernelSpec]:
    """All kernels (importing the modules that register GPU kernels). A kernel module that fails to import is left
    out and its error kept in ``import_errors()`` (shown with the devices): one broken module must not take every
    other kernel down with it (it did once, B3, while a module was being edited); the tests import each module
    directly and fail loudly."""
    import importlib
    for kname, mod in _KERNEL_MODULES:
        if kname in _KERNELS:
            continue
        try:
            importlib.import_module(f"{__package__}.{mod}")
            _IMPORT_ERRORS.pop(kname, None)
        except Exception as e:  # noqa: BLE001
            _IMPORT_ERRORS[kname] = f"{type(e).__name__}: {e}"[:300]
    out = {k.name: k for k in _CPU_ONLY}
    out.update(_KERNELS)
    return out


def import_errors() -> dict:
    """{kernel: error} of the kernel modules that failed to import (normally empty)."""
    return dict(_IMPORT_ERRORS)


# --- the GPU -------------------------------------------------------------------------------------------------------
def _cupy():
    """CuPy and a description of GPU 0, or (None, reason)."""
    global _GPU, _CP
    if _GPU is not None:
        return _CP, _GPU
    os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")  # the nvidia-smi numbering
    if "CUDA_VISIBLE_DEVICES" not in os.environ:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # GPU 0 only (GPU 1 of this host is faulty)
    if os.environ.get("LFPHYS_NO_GPU"):
        _GPU = {"available": False, "reason": T("disabled by the variable LFPHYS_NO_GPU")}
        return None, _GPU
    try:
        import cupy as cp
        n = cp.cuda.runtime.getDeviceCount()
        if n < 1:
            raise RuntimeError("CUDA sees no device")
        with cp.cuda.Device(0):
            props = cp.cuda.runtime.getDeviceProperties(0)
            pci = cp.cuda.Device(0).pci_bus_id
            want = os.environ.get("LFPHYS_GPU_PCI", "").strip()
            if want and pci_key(want) != pci_key(pci):
                raise RuntimeError(f"device 0 is on bus {pci}, but only {want} is allowed (LFPHYS_GPU_PCI)")
            free, total = cp.cuda.runtime.memGetInfo()
            # a trivial kernel and an FFT: the runtime, NVRTC and cuFFT really work with this driver
            x = cp.arange(8, dtype=cp.complex128)
            float(cp.abs(cp.fft.fft(x)).sum())
        _CP = cp
        _GPU = {"available": True, "name": props["name"].decode() if isinstance(props["name"], bytes) else str(props["name"]),
                "memory_total": int(total), "memory_free": int(free), "cupy": cp.__version__,
                "cuda_runtime": int(cp.cuda.runtime.runtimeGetVersion()),
                "driver": int(cp.cuda.runtime.driverGetVersion()), "pci_bus_id": pci,
                "visible": os.environ.get("CUDA_VISIBLE_DEVICES", "")}
    except Exception as e:  # no CuPy, no driver, no device: everything runs on the CPU
        _GPU = {"available": False, "reason": f"{type(e).__name__}: {e}"[:300]}
        _CP = None
    return _CP, _GPU


def devices() -> dict:
    _, gpu = _cupy()
    out = {"cpu": {"available": True, "name": platform.processor() or platform.machine(),
                   "threads": os.cpu_count(), "numpy": np.__version__},
           "gpu": gpu}
    kernels()
    if _IMPORT_ERRORS:
        out["kernel_import_errors"] = import_errors()
    return out


# --- settings ------------------------------------------------------------------------------------------------------
def configure(settings: dict | None) -> list[str]:
    """Apply settings {"kernels": {name: {"device": ..., "precision": ...}}, "crossover": {name: size}}. Returns notes
    about what was adjusted (an unknown kernel, a GPU asked for but not usable, a precision not validated)."""
    global _SETTINGS
    notes = []
    ks = kernels()
    clean = {"kernels": {}, "crossover": {}}
    settings = settings or {}
    if not isinstance(settings, dict):
        raise ValueError(T("settings: a JSON object"))
    for key in ("kernels", "crossover"):
        if settings.get(key) is not None and not isinstance(settings[key], dict):
            raise ValueError(T("settings: {key} must be a JSON object (kernel → value)", key=repr(key)))
    for name, s in (settings.get("kernels") or {}).items():
        if name not in ks:
            notes.append(T("unknown kernel {name}: skipped", name=repr(name)))
            continue
        if not isinstance(s, dict) or not all(isinstance(s.get(f, ""), str) for f in ("device", "precision")):
            raise ValueError(T('settings of kernel {name}: an object {"device": string, "precision": string}',
                               name=repr(name)))
        spec = ks[name]
        dev = s.get("device", "auto")
        prec = s.get("precision", "fp64")
        if dev not in DEVICES:
            notes.append(T("{name}: unknown device {dev} → auto", name=name, dev=repr(dev)))
            dev = "auto"
        if dev == "gpu" and not spec.gpu:
            notes.append(T("{name}: the kernel has no GPU implementation ({why}) → CPU", name=name,
                           why=spec.cpu_reason))
            dev = "cpu"
        if prec not in PRECISIONS or not spec.precisions.get(prec, {}).get("allowed"):
            if prec != "fp64":
                notes.append(T("{name}: precision {prec} is not validated for this kernel → fp64", name=name,
                               prec=str(prec)))
            prec = "fp64"
        if dev == "gpu":
            _, gpu = _cupy()
            if not gpu["available"]:
                notes.append(T("{name}: the GPU is chosen but not available ({why}) → runs on the CPU", name=name,
                               why=gpu.get("reason", "")))
        clean["kernels"][name] = {"device": dev, "precision": prec}
    for name, size in (settings.get("crossover") or {}).items():
        if name in ks and (size is None or (isinstance(size, int) and not isinstance(size, bool) and size > 0)):
            clean["crossover"][name] = size
        else:
            notes.append(T("threshold {name} = {size} not accepted (an integer > 0 or null is needed)",
                           name=repr(name), size=repr(size)))
    _SETTINGS = clean
    return notes


def settings() -> dict:
    return json.loads(json.dumps(_SETTINGS))


@dataclass
class Choice:
    xp: object
    device: str
    precision: str
    real: object
    complex: object
    reason: str

    def asarray(self, a):
        return self.xp.asarray(a)


# --- the GPU's temperature (STATUS V23 c) -------------------------------------------------------------------------
THERMAL = {"pause_c": 82.0, "resume_c": 70.0, "period_s": 2.0}
_THERMAL = {"hot": False, "temp": None, "last_temp": None, "read_at": float("-inf"), "error": ""}


def pci_key(bus_id: str) -> tuple | None:
    """A PCI bus id as numbers (domain, bus, device, function), so the forms of different tools compare equal:
    CuPy's ``0000:01:00.0`` and nvidia-smi's ``00000000:01:00.0`` (hex fields; an omitted domain is 0). None when the
    text is not a bus id."""
    t = (bus_id or "").strip().lower()
    try:
        head, fn = t.rsplit(".", 1)
        parts = head.split(":")
        if len(parts) == 2:
            parts = ["0"] + parts
        dom, bus, dev = (int(x, 16) for x in parts)
        return dom, bus, dev, int(fn, 16)
    except ValueError:
        return None


def _nvml_temperature() -> float | None:
    """GPU 0's temperature in °C through NVML (read only): the device on the bus LFPHYS_GPU_PCI if set, else NVML's
    index 0 (in the container the only GPU given). None when NVML is not there."""
    import ctypes
    try:
        lib = ctypes.CDLL("libnvidia-ml.so.1")
    except OSError:
        return None
    if lib.nvmlInit_v2() != 0:
        return None
    try:
        h = ctypes.c_void_p()
        key = pci_key(os.environ.get("LFPHYS_GPU_PCI", ""))
        pci = f"{key[0]:08x}:{key[1]:02x}:{key[2]:02x}.{key[3]:x}" if key else ""  # NVML's own form
        rc = (lib.nvmlDeviceGetHandleByPciBusId_v2(pci.encode(), ctypes.byref(h)) if pci
              else lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(h)))
        if rc != 0:
            return None
        t = ctypes.c_uint()
        if lib.nvmlDeviceGetTemperature(h, 0, ctypes.byref(t)) != 0:  # 0: NVML_TEMPERATURE_GPU
            return None
        return float(t.value)
    finally:
        lib.nvmlShutdown()


_TEMPERATURE = _nvml_temperature  # replaceable (tests)


def set_temperature_reader(fn) -> None:
    """Replace the temperature reader (tests); None restores NVML."""
    global _TEMPERATURE
    _TEMPERATURE = fn or _nvml_temperature
    _THERMAL.update(hot=False, temp=None, last_temp=None, read_at=float("-inf"), error="")


def thermal() -> dict:
    """The GPU's temperature as last read and whether kernels are kept off it (``hot``), with the thresholds."""
    return {**THERMAL, "hot": _THERMAL["hot"], "temp": _THERMAL["temp"], "last_temp": _THERMAL["last_temp"],
            "error": _THERMAL["error"]}


def _gpu_hot() -> bool:
    now = time.monotonic()
    if now - _THERMAL["read_at"] >= THERMAL["period_s"]:
        _THERMAL["read_at"] = now
        try:
            t = _TEMPERATURE()
        except Exception as e:  # noqa: BLE001 - an unreadable sensor never blocks the GPU, but is reported
            t, _THERMAL["error"] = None, f"{type(e).__name__}: {e}"
        _THERMAL["temp"] = t
        if t is not None:
            _THERMAL["last_temp"] = t  # the last valid reading: an unreadable sensor while hot keeps it (review B6-F7)
            if t >= THERMAL["pause_c"]:
                _THERMAL["hot"] = True
            elif t <= THERMAL["resume_c"]:
                _THERMAL["hot"] = False
    return _THERMAL["hot"]


def choose(name: str, size: int, check: bool = False, footprint: int | None = None, force: str | None = None,
           why: T | str = "", aux: bool = False) -> Choice:
    """The array module, device and dtypes for kernel ``name`` on a problem of ``size`` points. ``check=True``
    (references and checks) forces fp64. ``footprint``: the bytes the call needs on the device (compared with the free
    GPU memory before the GPU is taken). ``force="cpu"`` with ``why``: a fallback decided by the kernel. ``aux``: a small
    auxiliary call of a kernel whose main call draws the result (recorded apart, so that ``used()`` keeps the main call's
    device; review B3-8: v10's report showed the last small trace instead of the image's)."""
    spec = kernels()[name]
    s = _SETTINGS["kernels"].get(name, {})
    want = s.get("device", "auto")
    prec = "fp64" if check else s.get("precision", "fp64")
    cross = _SETTINGS["crossover"].get(name, spec.crossover)
    device, reason = "cpu", ""
    if force == "cpu":
        reason = why
    elif spec.gpu and want in ("auto", "gpu"):
        cp, gpu = _cupy()
        if not gpu["available"]:
            reason = T("GPU not available: {why}", why=gpu.get("reason", ""))
        elif want == "gpu" or (cross is not None and size >= cross):
            device = "gpu"
            reason = (T("chosen in the settings") if want == "gpu"
                      else T("auto: problem size {size:d} ≥ threshold {cross:d}", size=int(size), cross=int(cross)))
            if footprint:
                free = int(cp.cuda.runtime.memGetInfo()[0]) + int(cp.get_default_memory_pool().free_bytes())
                if footprint > 0.8 * free:
                    device = "cpu"
                    reason = T("GPU: needs ~{need:.2g} GB, {free:.2g} GB free → CPU", need=footprint / 2**30,
                               free=free / 2**30)
            if device == "gpu" and _gpu_hot():
                device = "cpu"
                t = _THERMAL["temp"]
                seen = (T("{t:.0f} °C", t=float(t)) if t is not None else
                        T("the temperature cannot be read, last {t:.0f} °C", t=float(_THERMAL["last_temp"]))
                        if _THERMAL["last_temp"] is not None else T("the temperature cannot be read"))
                reason = T("GPU cooling down: {seen} (threshold {pause:.0f} °C): runs on the CPU until it has "
                           "cooled to {resume:.0f} °C", seen=seen, pause=float(THERMAL["pause_c"]),
                           resume=float(THERMAL["resume_c"]))
        else:
            reason = (T("auto: problem size {size:d} below threshold {cross:d}", size=int(size), cross=int(cross))
                      if cross else T("auto: the GPU does not pay off here"))
    elif not spec.gpu:
        reason = spec.cpu_reason or T("CPU only")
    else:
        reason = T("chosen in the settings")
    xp = _CP if device == "gpu" else np
    real, cplx = _DTYPES[prec]
    if device == "gpu":
        real, cplx = getattr(_CP, np.dtype(real).name), getattr(_CP, np.dtype(cplx).name)
    _USED.setdefault(name, {})["check" if check else ("aux" if aux else "drawn")] = {
        "device": device, "precision": prec, "reason": reason, "size": int(size)}
    return Choice(xp, device, prec, real, cplx, reason)


def is_out_of_memory(e: Exception) -> bool:
    return _CP is not None and isinstance(e, _CP.cuda.memory.OutOfMemoryError)


def release() -> None:
    """Return the GPU memory pool's free blocks (an idle run then holds only its CUDA context)."""
    if _CP is not None:
        _CP.get_default_memory_pool().free_all_blocks()
        _CP.get_default_pinned_memory_pool().free_all_blocks()


def to_numpy(a):
    if _CP is not None and isinstance(a, _CP.ndarray):
        return _CP.asnumpy(a)
    return np.asarray(a)


def used() -> dict:
    """{kernel: {"drawn": {device, precision, reason, size}, "check": {...}, "aux": {...}}} for the kernels called in
    this process: the last main call for drawn results, the last call for references and checks, the last auxiliary
    call."""
    return json.loads(json.dumps(_USED))


def reset_used() -> None:
    _USED.clear()


def set_used(record: dict) -> None:
    """Take over a record of ``used()`` (a run continued in a new process from a saved state reports the kernels as the
    process that saved it did)."""
    _USED.clear()
    _USED.update(json.loads(json.dumps(record)))


# --- calibration ---------------------------------------------------------------------------------------------------
def _time(fn, repeat=3):
    best = float("inf")
    for _ in range(repeat):
        t = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t)
    return best


def calibrate(names=None) -> dict:
    """Time every GPU kernel's benchmark on the CPU and on the GPU over its sizes; the crossover is the smallest size
    from which the GPU is faster at every larger size. Short runs (seconds): no thermal concern."""
    cp, gpu = _cupy()
    out = {}
    for name, spec in kernels().items():
        if names and name not in names:
            continue
        if not spec.gpu or spec.bench is None:
            continue
        rows = []
        for n in spec.bench_sizes:
            t_cpu = _time(lambda: spec.bench(n, np, np.complex128))
            t_gpu = None
            if gpu["available"]:
                spec.bench(n, cp, cp.complex128)  # warm-up (plans, kernels)
                cp.cuda.Device(0).synchronize()

                def run():
                    spec.bench(n, cp, cp.complex128)
                    cp.cuda.Device(0).synchronize()
                t_gpu = _time(run)
            rows.append({"size": int(n), "cpu_s": t_cpu, "gpu_s": t_gpu})
        cross = None
        if gpu["available"]:
            for i, r in enumerate(rows):
                if all(rr["gpu_s"] < rr["cpu_s"] for rr in rows[i:]):
                    cross = r["size"]
                    break
        out[name] = {"rows": rows, "crossover": cross, "measured": time.strftime("%Y-%m-%d %H:%M"),
                     "gpu": gpu.get("name") if gpu["available"] else None}
    return out


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="lfphys devices and kernels (JSON on stdout).")
    ap.add_argument("--devices", action="store_true", help="the CPU and GPU 0 as the engine sees them")
    ap.add_argument("--kernels", action="store_true", help="the registered kernels and their options")
    ap.add_argument("--calibrate", action="store_true", help="time the GPU kernels on CPU and GPU, report crossovers")
    ap.add_argument("--configure", metavar="JSON", help="validate settings (JSON, or - to read it from stdin): print "
                                                        "the settings in force and the notes")
    a = ap.parse_args(argv)
    out = {}
    if a.configure is not None:
        import sys
        try:
            out["notes"] = configure(json.loads(sys.stdin.read() if a.configure == "-" else a.configure))
        except ValueError as e:  # malformed JSON or shape: a message, not a traceback (review B1-10)
            print(json.dumps({"error": text_of(e)}, ensure_ascii=False))
            raise SystemExit(2)
        out["settings"] = settings()
    if a.devices:
        out["devices"] = devices()
    if a.kernels:
        out["kernels"] = [k.public() for k in kernels().values()]
    if a.calibrate:
        out["calibration"] = calibrate()
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    # run in the canonical module object: the kernel modules register into lfphys.core.backend, not into __main__
    from lfphys.core import backend as _canonical
    _canonical._main()
