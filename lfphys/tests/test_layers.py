# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The layering rules of LAYERS.md, checked mechanically over the whole package."""

import ast
import importlib
from pathlib import Path

import numpy as np
import pytest

from lfphys import registry

PKG = Path(__file__).resolve().parents[1] / "lfphys"
NAMES = registry.module_names()


def _imports(path: Path, modname: str) -> set[str]:
    """Absolute names of the lfphys modules a file imports (relative imports resolved)."""
    tree = ast.parse(path.read_text())
    pkg = modname.rsplit(".", 1)[0]
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names if a.name.startswith("lfphys")}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg.split(".")
                base = base[: len(base) - node.level + 1]
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            if mod.startswith("lfphys"):
                out.add(mod)
                out |= {f"{mod}.{a.name}" for a in node.names}
    return out


def _path(name):
    return PKG.joinpath(*name.split(".")[1:]).with_suffix(".py")


@pytest.mark.parametrize("name", NAMES)
def test_every_module_declares_its_layer(name):
    mod = importlib.import_module(name)
    about = getattr(mod, "ABOUT", None)
    assert about is not None, f"{name}: no ABOUT"
    for k in registry.REQUIRED:
        assert k in about, f"{name}: ABOUT lacks {k}"
    assert about["layer"] == name.split(".")[1], f"{name}: layer {about['layer']!r} but lives in {name.split('.')[1]}"
    assert about["layer"] in registry.LAYERS


@pytest.mark.parametrize("name", [n for n in NAMES if n.startswith("lfphys.core.")])
def test_core_imports_only_core(name):
    bad = {m for m in _imports(_path(name), name)
           if m.startswith(("lfphys.theories", "lfphys.laws", "lfphys.tools"))}
    assert not bad, f"{name} imports outside the core: {sorted(bad)}"


@pytest.mark.parametrize("name", [n for n in NAMES if n.startswith("lfphys.theories.")])
def test_theories_name_their_kind_and_conflicts(name):
    about = importlib.import_module(name).ABOUT
    sub = name.split(".")[2]
    expect = {"approx": "approximation", "interpretations": "interpretation", "models": "model",
              "alternatives": "alternative"}[sub]
    assert about["kind"] == expect, f"{name}: kind {about['kind']!r}, expected {expect!r}"
    assert about["conflicts"], f"{name}: a theory outside the core must name where it disagrees"


def test_catalogue_is_complete_and_ordered():
    cat = registry.catalogue()
    assert {d["id"] for d in cat} == {n[len("lfphys."):] for n in NAMES}
    desc = registry.describe(["core.relativity", "theories.approx.newton", "laws.light"])
    assert [d["layer"] for d in desc] == ["core", "theories", "laws"]


def test_refuted_kinematics_is_not_computed_in_the_core():
    """Review 2026-10-23, E8: the emission-theory front (centred on the moving source) lives outside the core; the
    core's front is that of special relativity, independent of the source's motion."""
    import inspect

    from lfphys.core.gravity import arrivals
    assert "w" not in inspect.signature(arrivals.front_arrival).parameters
    from lfphys.core import worldlines
    from lfphys.theories.alternatives import kinematics
    from lfphys.core.constants import C
    from lfphys.laws.light import Laws, flat_arrival
    wl = worldlines.Piecewise.start(Laws(gravity="none"), 0.0, 0.0, [10.0, 0.0], [0.0, 0.0])
    sr = arrivals.front_arrival(C, 0.0, np.zeros(2), wl)
    em = kinematics.emission_front_arrival(C, 0.0, np.zeros(2), np.array([0.5 * C, 0.0]), wl)
    assert sr["t"] == pytest.approx(10.0 / C, rel=1e-15) and em["t"] == pytest.approx(10.0 / (1.5 * C), rel=1e-15)
    # the law sets dispatch: SR and ether use the core's front, emission the alternative's
    for kin, t in (("SR", 10.0 / C), ("ether", 10.0 / C), ("emission", 10.0 / (1.5 * C))):
        res = flat_arrival(Laws(kinematics=kin, gravity="none"), 0.0, np.zeros(2), np.array([0.5 * C, 0.0]), wl)
        assert res["t"] == pytest.approx(t, rel=1e-15)
