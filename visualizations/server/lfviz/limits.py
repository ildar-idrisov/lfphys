# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The memory budget of the worlds (review 2026-11-04 UX-params P8: one world grew to 31 GB on the shared host and the
kernel's OOM killer fired; RULES.md §3, «Memory budget»).

Two lines of defence, both in the framework:

* **a hard limit per worker**: the server gives every worker a budget (``--worker-mem-gb``, by default 60 % of the
  memory the server may use — its container's limit, else the host's — at most 8 GB), passed in the environment
  (``ENV``); the worker
  sets it as its own ``RLIMIT_DATA`` before it builds a world. ``RLIMIT_DATA`` counts the private writable memory (NumPy's
  arrays, Python's objects) and not the address space a GPU driver reserves, so CUDA keeps working. An allocation beyond
  it fails inside the worker (``MemoryError``), which is reported in the owner's words (``errors.owner_text``) — the host and the
  other runs are never touched;
* **estimates before allocating**: a world may say how much it will allocate — for its parameters before it is built
  (``Simulation.estimate_bytes(params) -> int``, a classmethod; the server asks it before it starts a run, the worker
  before a new world; integrator's API of 2026-11-05) and before a large allocation while it runs (``require(nbytes, what, change)``). An estimate above the
  budget is refused at once with the numbers and what to change, instead of failing after minutes or in the middle.
"""

from __future__ import annotations

import os
import sys

from .i18n import T

ENV = "LFVIZ_WORKER_MEM"  # bytes a worker may hold (set by the server for every worker; absent: no limit)
GIB = 2 ** 30
HEADROOM = 0.85  # an estimate is compared with this share of the budget: the interpreter, the libraries, the record


def fmt_bytes(n: float | None):
    """Bytes in the owner's units, a text (``T``) with its number: "6.6 GB", "591 GB", "74 TB", "120 MB" (binary
    units, as the limits); ``str()`` of it is English (the server's log)."""
    if n is None:
        return "—"
    n = float(n)
    for unit, k in (("TB", 2 ** 40), ("GB", 2 ** 30), ("MB", 2 ** 20), ("KB", 2 ** 10)):
        if n >= k:
            return T("{n:.3g} " + unit, n=n / k)  # i18n-msgids: "{n:.3g} TB" "{n:.3g} GB" "{n:.3g} MB" "{n:.3g} KB"
    return T("{n:.3g} B", n=n)


def worker_budget() -> int | None:
    """This worker's budget in bytes (None when the server set none)."""
    try:
        v = int(float(os.environ.get(ENV, "") or 0))
    except ValueError:
        return None
    return v if v > 0 else None


def apply_hard_limit(nbytes: int | None = None) -> int | None:
    """Make the budget this process's hard limit of private writable memory (RLIMIT_DATA). Returns the limit set."""
    n = worker_budget() if nbytes is None else int(nbytes)
    if not n:
        return None
    try:
        import resource  # noqa: PLC0415 - POSIX only
        soft, hard = resource.getrlimit(resource.RLIMIT_DATA)
        lim = n if hard == resource.RLIM_INFINITY else min(n, hard)
        resource.setrlimit(resource.RLIMIT_DATA, (lim, lim))
        return lim
    except (ImportError, ValueError, OSError) as e:  # a platform without it: the estimates still apply
        print(f"lfviz: memory limit not set: {e}", file=sys.stderr)
        return None


def _cgroup_limit() -> int | None:
    for path in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            s = open(path).read().strip()
        except OSError:
            continue
        if s.isdigit() and int(s) < 2 ** 60:
            return int(s)
    return None


def _mem_total() -> int | None:
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    except OSError:
        pass
    return None


def default_budget(max_workers: int) -> int:
    """A worker's budget when the server is not told one: 60 % of the memory the server may use (its container's
    limit, else the host's), at least 1 GB and at most 8 GB. One runaway world then never takes the server's or the
    host's memory (the container's own limit stays the bound of all workers together); measured peaks of every world's
    defaults and presets on the CPU are below 2 GB (v08: 1.7 GB). ``max_workers`` is kept for the signature: the share
    does not shrink with it, so that one heavy world still fits when the others are light."""
    total = _cgroup_limit() or _mem_total() or 8 * GIB
    return int(min(8 * GIB, max(1 * GIB, 0.6 * total)))


def require(nbytes: float, what, change="", budget: int | None = None) -> None:
    """Refuse (``errors.Refusal``) when ``nbytes`` — what the world is about to allocate for ``what`` (a text, e.g.
    ``T("a grid of {nx} × {ny} nodes", ...)``) — exceeds the budget (this worker's, or ``budget``); nothing when no
    budget is set or it fits."""
    budget = budget or worker_budget()
    if not budget or not (nbytes > HEADROOM * budget):
        return
    from .errors import Refusal  # noqa: PLC0415
    raise Refusal(T("{what:cap} would need about {need} of memory, while the worker is given {budget}", what=what,
                    need=fmt_bytes(nbytes), budget=fmt_bytes(budget)),
                  change or T("reduce the size of the task (the grid, the region, the number of particles)"))


def check_estimate(sim_cls, params: dict, budget: int | None = None) -> None:
    """Ask a world for the memory its parameters need before it is built (``estimate_bytes``: a classmethod, a
    staticmethod, or a method that does not use ``self``) and refuse what does not fit (``require``). It may return the
    bytes, or ``(bytes, what, change)`` with the owner's words for what takes the memory and what to change. A world
    without an estimate, or one that fails to estimate, is built as before."""
    import inspect  # noqa: PLC0415
    raw = inspect.getattr_static(sim_cls, "estimate_bytes", None)
    if raw is None:
        return
    try:
        if isinstance(raw, (classmethod, staticmethod)):
            r = getattr(sim_cls, "estimate_bytes")(params)
        else:  # a plain method: called without an instance (the world is not built yet)
            r = raw(None, params)
    except Exception as e:  # noqa: BLE001 - an estimate must never block a world that would build
        print(f"lfviz: estimate_bytes failed: {type(e).__name__}: {e}", file=sys.stderr)
        return
    if r is None:
        return
    if isinstance(r, (tuple, list)):  # (bytes, what, change)
        nbytes, what, change = (list(r) + ["", ""])[:3]
    else:
        nbytes, what, change = r, "", ""
    require(float(nbytes), what or T("a world with these parameters"), change, budget)
