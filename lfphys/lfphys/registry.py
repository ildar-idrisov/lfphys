# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Catalogue of the engine: every module declares ``ABOUT`` (layer, kind, title, statement, validity, basis,
conflicts). The catalogue is what a visualization shows as "the physics of this world" and what the layering tests
check (LAYERS.md).
"""

from __future__ import annotations

import importlib
import pkgutil

LAYERS = {
    "core": "Ядро: установленная и подтверждённая опытом физика и её точные следствия (с контролем численной ошибки).",
    "theories": "Вне ядра: широко используемые теории, расходящиеся с ядром или друг с другом в какой-то области "
                "(приближения, интерпретации, модели) и альтернативы для исследований «что если».",
    "laws": "Наборы законов: какие модули ядра и какие теории использует мир.",
    "tools": "Инструменты, не физика: статистика смоделированных данных.",
}
THEORY_KINDS = {
    "approximation": "приближение",
    "interpretation": "интерпретация",
    "model": "феноменологическая модель",
    "alternative": "альтернатива (модификация законов)",
}
REQUIRED = ("layer", "kind", "title", "statement", "validity", "basis", "conflicts")


def module_names() -> list[str]:
    import lfphys
    return sorted(m.name for m in pkgutil.walk_packages(lfphys.__path__, "lfphys.")
                  if not m.ispkg and m.name not in ("lfphys.registry",))


def about(name: str) -> dict:
    """ABOUT of a module, with its id (the module path without the package prefix)."""
    if not name.startswith("lfphys."):
        name = "lfphys." + name
    mod = importlib.import_module(name)
    d = dict(getattr(mod, "ABOUT", {}))
    d["id"] = name[len("lfphys."):]
    return d


def catalogue() -> list[dict]:
    return [about(n) for n in module_names()]


def describe(names) -> list[dict]:
    """The entries a world uses, for display: core first, then theories by kind, then the rest."""
    order = {"core": 0, "theories": 1, "laws": 2, "tools": 3}
    out = [about(n) for n in names]
    return sorted(out, key=lambda d: (order.get(d.get("layer"), 9), d.get("kind", ""), d["id"]))
