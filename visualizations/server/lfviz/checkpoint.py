# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Checkpoints of a world's whole state, so that a run continues from its last state instead of recomputing its
record (owner, 2026-10-29: «для добавления записи последний кадр должен быть достаточен для полного точного
воспроизведения с последнего состояния в виде продолжения эксперимента, а не нового запуска»).

A checkpoint is the pickled simulation object with the runner's state of its world (number, preset, speed, the view
it took over). The worker's output function, which every world holds, is not data: it is written as a persistent
reference and the new worker's function is put in its place on loading. Arrays on the GPU are written as NumPy arrays
and put back on the GPU on loading, so that the world goes on on the device it ran on; a module a world keeps (its
array namespace, numpy or cupy) is written by its name and imported again, and a closure it keeps (a local function
or a lambda: a potential, a spectrum) by value — its code (``marshal``: the same Python reads it, since the run's code
hash must match), its module and the values it closes over.

The worker writes a checkpoint when its run is suspended, when it pauses and every ``sim.CHECKPOINT_EVERY`` seconds of
computation,
and records it with a ``checkpoint`` message (world, time, file, the files of the code the world runs with their hash,
the interpreter and library versions): the message's place in the record is the state's place. A resume loads the last
checkpoint of the latest world whose code files and runtime are unchanged and repeats only what the record holds after
it (``Runner.restore_from``); without one it rebuilds the world from its start (``Runner.restore``). The files are the
server's own, named ``w<world>-<ns>.pkl`` inside the run's folder (anything else is refused); the unpickler itself is not
restricted, so a checkpoint file must never come from elsewhere.
"""

from __future__ import annotations

import hashlib
import importlib
import io
import marshal
import os
import pickle
import re
import threading
import time
import types
from pathlib import Path

from .i18n import T

VERSION = 1
KEEP = 2       # checkpoint files kept per run (the newest), in case the last one was cut by a crash

_EMIT = "lfviz.emit"


_EMPTY = object()  # an unassigned closure cell


def _function(code, module, name, qualname, defaults, kwdefaults, cells, attrs):
    """A local function or a lambda rebuilt from its code, its module's globals and its closure's values."""
    fn = types.FunctionType(marshal.loads(code), importlib.import_module(module).__dict__, name, defaults,
                            tuple(types.CellType() if v is _EMPTY else types.CellType(v) for v in cells))
    fn.__qualname__ = qualname
    fn.__kwdefaults__ = kwdefaults
    if attrs:
        fn.__dict__.update(attrs)
    return fn


def _cell_value(c):
    try:
        return c.cell_contents
    except ValueError:
        return _EMPTY


def _cupy_array(a):
    """A GPU array back on the GPU, through the engine's own CuPy handle (GPU 0 pinned by its PCI id), so that the
    engine knows the arrays it meets are CuPy's (``backend.to_numpy``), as in the worker that wrote them."""
    from lfphys.core import backend
    gpu = backend.devices()["gpu"]
    if not gpu.get("available"):
        raise RuntimeError(T("there is no GPU this world ran on: {reason}", reason=gpu.get("reason")))
    import cupy
    return cupy.asarray(a)


class _Pickler(pickle.Pickler):
    def __init__(self, f, emit, cupy_mod):
        super().__init__(f, protocol=pickle.HIGHEST_PROTOCOL)
        self._emit = emit
        self._cp = cupy_mod

    def persistent_id(self, obj):
        return _EMIT if obj is self._emit else None

    def reducer_override(self, obj):
        if self._cp is not None and isinstance(obj, self._cp.ndarray):
            return _cupy_array, (self._cp.asnumpy(obj),)
        if isinstance(obj, types.ModuleType):  # an array namespace a world keeps (numpy or cupy): by its name
            return importlib.import_module, (obj.__name__,)
        if isinstance(obj, types.FunctionType) and ("<locals>" in obj.__qualname__ or obj.__name__ == "<lambda>"):
            # a closure a world keeps (a potential, a spectrum, a radial function): by value, as pickle cannot name it
            return _function, (marshal.dumps(obj.__code__), obj.__module__, obj.__name__, obj.__qualname__,
                               obj.__defaults__, obj.__kwdefaults__,
                               tuple(_cell_value(c) for c in obj.__closure__ or ()), dict(obj.__dict__) or None)
        return NotImplemented


class _Unpickler(pickle.Unpickler):
    def __init__(self, f, emit):
        super().__init__(f)
        self._emit = emit

    def persistent_load(self, pid):
        if pid == _EMIT:
            return self._emit
        raise pickle.UnpicklingError(f"unknown persistent reference {pid!r}")


def _cupy_if_loaded():
    """CuPy only if the engine already imported it (a world that never used the GPU has no CuPy arrays)."""
    import sys
    return sys.modules.get("cupy")


def dumps(state: dict, emit) -> bytes:
    """The bytes of a checkpoint of ``state`` ({"sim": Simulation, "world": n, ...}); ``emit`` (the worker's output
    function) is written as a reference."""
    buf = io.BytesIO()
    _Pickler(buf, emit, _cupy_if_loaded()).dump({"version": VERSION, **state})
    return buf.getvalue()


def loads(data: bytes, emit) -> dict:
    state = _Unpickler(io.BytesIO(data), emit).load()
    if state.get("version") != VERSION:
        raise ValueError(f"checkpoint version {state.get('version')!r}, expected {VERSION}")
    return state


NAME = re.compile(r"^w\d+-\d+\.pkl$")  # the only file names a checkpoint may have (review CK-10)


def new_name(world: int) -> str:
    return f"w{world}-{time.time_ns()}.pkl"


def write(folder: Path, name: str, data: bytes) -> Path:
    """Write a checkpoint file atomically (a crash leaves the previous ones whole; a failed write leaves no temporary
    file) and keep the newest ``KEEP``."""
    if not NAME.match(name):
        raise ValueError(f"not a checkpoint name: {name!r}")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    old = sorted(folder.glob("w*-*.pkl"), key=lambda p: int(p.stem.split("-")[1]))[:-KEEP]
    for p in old:
        p.unlink(missing_ok=True)
    return path


class Writer:
    """Writes checkpoint files in a background thread (review CK-12: u38's 100 MB took 0.8 s in the frame loop): one
    write at a time; ``wait()`` before the worker ends; a failed write is reported once by ``take_failure()``, so the
    next trigger writes the state again (review CK-8)."""

    def __init__(self):
        self._thread = None
        self._failed = False

    def submit(self, folder: Path, name: str, data: bytes):
        self.wait()

        def run():
            try:
                write(folder, name, data)
            except Exception:  # noqa: BLE001 - reported once; the record's checkpoint message then has no file
                import traceback
                traceback.print_exc()
                self._failed = True
        self._thread = threading.Thread(target=run, name="checkpoint-writer", daemon=False)
        self._thread.start()

    def wait(self):
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def take_failure(self) -> bool:
        f, self._failed = self._failed, False
        return f


# --- what a checkpoint was made by (review CK-5): the code the world runs and the runtime ------------------------------
def code_files(root: Path) -> list[str]:
    """The source files under ``root`` (engine/) of the modules loaded in this process, as paths relative to it: the
    code the world actually runs (r13 runs r12's; an engine module the world does not import is not among them)."""
    import sys
    out = set()
    root = root.resolve()
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f or not f.endswith(".py"):
            continue
        try:
            rel = Path(f).resolve().relative_to(root)
        except ValueError:
            continue
        if "tests" not in rel.parts:
            out.add(str(rel))
    return sorted(out)


def files_hash(root: Path, files: list[str]) -> str | None:
    """sha256 of the files' paths and contents (None when one is missing)."""
    h = hashlib.sha256()
    for rel in files:
        p = root / rel
        try:
            data = p.read_bytes()
        except OSError:
            return None
        h.update(rel.encode())
        h.update(data)
    return h.hexdigest()[:16]


def runtime_env() -> dict:
    """The interpreter (closures travel as its bytecode) and the libraries whose objects a checkpoint holds."""
    import importlib.metadata as md
    import importlib.util
    import sys
    env = {"python": sys.version.split()[0], "magic": importlib.util.MAGIC_NUMBER.hex()}
    for dist in ("numpy", "scipy", "cupy-cuda12x"):
        try:
            env[dist] = md.version(dist)
        except md.PackageNotFoundError:
            env[dist] = None
    return env
