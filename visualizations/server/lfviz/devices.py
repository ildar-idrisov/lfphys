# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Device and precision settings of the engine's kernels (plan P11), for the settings page and the runs.

* The owner's defaults live in ``settings.local.json`` next to the visualizations (git-ignored, per machine).
* Devices, kernels, validation and calibration come from the engine itself (``python -m lfphys.core.backend``) in a
  subprocess: the server process never initialises CUDA or holds the GPU; each run's worker does, if a kernel of its
  world asks for the GPU.
* A run takes the settings in force when it starts, or those with the start form's overrides for that run (plan
  P11: "global defaults and per-run overrides"); they are recorded in its passport and its header.
* Input is checked here before it reaches the engine (a malformed body gets 400 with the reason, never a traceback);
  the engine gets the JSON on stdin; writes of the settings file are serialised (review B1-10, B1-11).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

from . import registry

SETTINGS_FILE = registry.ROOT / "settings.local.json"
MAX_BYTES = 64 * 1024  # a settings body or an override larger than this is refused
_CACHE: dict = {}
_LOCKS: dict = {}
log = logging.getLogger("lfviz.devices")


def _lock() -> asyncio.Lock:
    """One lock per event loop around load -> validate -> save (tests run several loops in one process)."""
    loop = asyncio.get_running_loop()
    if loop not in _LOCKS:
        _LOCKS.clear()
        _LOCKS[loop] = asyncio.Lock()
    return _LOCKS[loop]


def shape_error(s, allow=("kernels", "crossover")) -> str | None:
    """Why ``s`` is not a settings object (None if it is): {"kernels": {name: {"device": str, "precision": str}},
    "crossover": {name: int > 0 | null}}."""
    if not isinstance(s, dict):
        return "настройки — объект JSON"
    extra = sorted(set(s) - set(allow))
    if extra:
        return f"неизвестные поля: {', '.join(map(str, extra))}"
    if len(json.dumps(s)) > MAX_BYTES:
        return f"настройки длиннее {MAX_BYTES // 1024} КБ"
    ks = s.get("kernels")
    if ks is not None:
        if not isinstance(ks, dict):
            return "kernels — объект: ядро → {device, precision}"
        for name, v in ks.items():
            if (not isinstance(v, dict) or set(v) - {"device", "precision"}
                    or not all(isinstance(x, str) for x in v.values())):
                return f"kernels[{name!r}] — объект {{device: строка, precision: строка}}"
    cs = s.get("crossover")
    if cs is not None:
        if not isinstance(cs, dict):
            return "crossover — объект: ядро → целое > 0 или null"
        for name, v in cs.items():
            if v is not None and (isinstance(v, bool) or not isinstance(v, int) or not 0 < v <= 10**12):
                return f"crossover[{name!r}] = {v!r}: нужно целое > 0 или null"
    return None


def load() -> dict:
    try:
        d = json.loads(SETTINGS_FILE.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(d: dict) -> None:
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    os.replace(tmp, SETTINGS_FILE)


def _env() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(registry.ENGINE), env.get("PYTHONPATH", "")])
    return env


async def _backend(*args: str, stdin: str | None = None, timeout: float = 60.0) -> dict:
    """Run ``python -m lfphys.core.backend`` with ``args`` (``stdin``: text for ``--configure -``). Raises ValueError
    with the engine's message for malformed settings, RuntimeError otherwise; the engine's traceback goes to the
    server log only."""
    proc = await asyncio.create_subprocess_exec(sys.executable, "-m", "lfphys.core.backend", *args,
                                                stdin=asyncio.subprocess.PIPE if stdin is not None else None,
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                                                env=_env(), cwd=str(registry.ENGINE))
    try:
        out, err = await asyncio.wait_for(proc.communicate(None if stdin is None else stdin.encode()), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError("движок не ответил вовремя")
    if proc.returncode == 2:  # malformed settings: the engine's message (argparse errors also exit 2, without it)
        try:
            msg = json.loads(out.decode())["error"]
        except (ValueError, KeyError, TypeError):
            msg = None
        if msg:
            raise ValueError(msg)
    if proc.returncode != 0:
        log.warning("lfphys.core.backend %s: exit %s\n%s", " ".join(args), proc.returncode,
                    err.decode(errors="replace")[-4000:])
        raise RuntimeError(f"движок завершился с кодом {proc.returncode} (подробности — в журнале сервера)")
    return json.loads(out.decode())


async def probe(max_age: float = 60.0) -> dict:
    """{"devices": ..., "kernels": [...]} as the engine sees them (cached for ``max_age`` seconds)."""
    now = time.monotonic()
    if _CACHE.get("t") and now - _CACHE["t"] < max_age:
        return _CACHE["v"]
    v = await _backend("--devices", "--kernels")
    _CACHE.update(t=now, v=v)
    return v


async def validate(settings: dict) -> tuple[dict, list]:
    """The settings the engine accepts (unknown kernels dropped, impossible choices adjusted) and its notes."""
    err = shape_error({k: settings.get(k) for k in ("kernels", "crossover")})
    if err:
        raise ValueError(err)
    out = await _backend("--configure", "-", stdin=json.dumps({"kernels": settings.get("kernels") or {},
                                                               "crossover": settings.get("crossover") or {}}))
    clean = dict(settings)
    clean["kernels"] = out["settings"]["kernels"]
    clean["crossover"] = out["settings"]["crossover"]
    return clean, out["notes"]


async def update(body: dict) -> tuple[dict, list]:
    """Apply a PUT body ({"kernels": ...} replaces the kernel choices, {"crossover": ...} the thresholds) to the
    settings file, one writer at a time. ValueError: a malformed body."""
    err = shape_error(body)
    if err:
        raise ValueError(err)
    async with _lock():
        cur = load()
        if "kernels" in body:
            cur["kernels"] = body["kernels"] or {}
        if "crossover" in body:
            cur["crossover"] = body["crossover"] or {}
        clean, notes = await validate(cur)
        save(clean)
    return clean, notes


async def for_run(override: dict | None) -> tuple[dict, list]:
    """The settings a new run takes: the file's, with ``override`` ({"kernels": {...}} from the start form) applied
    on top for this run only. ValueError: a malformed override."""
    base = load()
    if not override:
        return base, []
    err = shape_error(override, allow=("kernels",))
    if err:
        raise ValueError(err)
    merged = dict(base)
    merged["kernels"] = {**(base.get("kernels") or {}), **(override.get("kernels") or {})}
    clean, notes = await validate(merged)
    clean["override"] = override
    return clean, notes


async def calibrate() -> dict:
    """Time the GPU kernels on CPU and GPU (a few seconds); the measured crossovers become the "auto" thresholds."""
    cal = (await _backend("--calibrate", timeout=300.0))["calibration"]
    async with _lock():  # measured outside the lock (seconds); merged into the file as it is now
        s = load()
        s.setdefault("crossover", {})
        for name, c in cal.items():
            if c.get("gpu"):
                s["crossover"][name] = c["crossover"]
        s["calibration"] = cal
        save(s)
    _CACHE.clear()
    return s
