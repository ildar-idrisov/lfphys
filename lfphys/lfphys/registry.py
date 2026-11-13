# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Catalogue of the engine: every module declares ``ABOUT`` (layer, kind, title, statement, validity, basis,
conflicts). The catalogue is what a visualization shows as "the physics of this world" and what the layering tests
check (LAYERS.md).
"""

from __future__ import annotations

import importlib
import pkgutil

from lfphys.i18n import T

# the user-facing fields of ABOUT (title, statement, validity, conflicts and the descriptive basis entries) and the
# texts below are translatable texts (lfphys.i18n.T; Russian in lfphys/locales/ru.json)
LAYERS = {
    "core": T("Core: established physics confirmed by experiment and its exact consequences (with the numerical "
              "error controlled)."),
    "theories": T("Outside the core: widely used theories that disagree with the core or with each other somewhere "
                  "(approximations, interpretations, models) and alternatives for “what if” studies."),
    "laws": T("Law sets: which core modules and which theories a world uses."),
    "tools": T("Tools, not physics: statistics of simulated data."),
}
THEORY_KINDS = {
    "approximation": T("approximation"),
    "interpretation": T("interpretation"),
    "model": T("phenomenological model"),
    "alternative": T("alternative (modified laws)"),
}
NOT_MODULES = ("lfphys.registry", "lfphys.i18n", "lfphys.codes")  # the catalogue itself, the text mechanism and the
#                                                                   refusal codes: no physics, no ABOUT
REQUIRED = ("layer", "kind", "title", "statement", "validity", "basis", "conflicts")


def module_names() -> list[str]:
    import lfphys
    return sorted(m.name for m in pkgutil.walk_packages(lfphys.__path__, "lfphys.")
                  if not m.ispkg and m.name not in NOT_MODULES)


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
