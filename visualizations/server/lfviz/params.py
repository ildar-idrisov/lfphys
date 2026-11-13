# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Parameter schema of a visualization.

Three kinds of inputs (RULES.md, section 2.4):

* world parameters (``live=False``) - laws, constants, fixed fields and initial conditions that nothing inside the
  world can change (the mass of the Sun, the Born rule). They are fixed for a world: a change starts a NEW WORLD
  inside the same run (a changed law in the middle of a history would break causality: the past would have been
  computed under other laws).
* live parameters (``live=True``) - the set-up an experimenter can change while the world runs (move the screen,
  swap the slits, insert a polarizer). A change is applied at once, at the current moment of the world (command
  ``set``); its consequences propagate from that event. The value in a preset or a new world is the initial one.
* actions - one-off events done by an agent (boost an observer, emit a flash). Declared by the simulation header,
  not here.

``standard`` marks the value of accepted physics. A run whose world parameters differ from it carries the flag
"modified physics" in its header, its record and the player's top bar, with the list of modifications.

Values are stored in the displayed unit; ``scale`` converts to SI (``si = value * scale``).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from .i18n import T, is_t, join, names_unit


JSON_MAX = 900_000  # characters of a "json" parameter: below the player socket's 1 MiB message limit (app.py), so
# that a scene file accepted from the catalogue can also be loaded in the player (review B6-F20)


@dataclass
class Param:
    id: str
    label: str
    type: str  # "float" | "int" | "select" | "bool" | "json" (structured data, e.g. a playground's initial scene)
    default: Any
    group: str = ""
    unit: str = ""
    scale: float = 1.0
    min: float | None = None
    max: float | None = None
    log: bool = False
    # [(value, label), ...] for "select"; an option may be (value, label, show_if): shown only when show_if holds (the
    # same form as the parameter's; review UX-params P17: choices a world always refuses for the particle chosen). The
    # forms hide it; the schema does not enforce it (the world refuses it in the owner's words). Labels, units, help
    # and groups are texts (lfviz.i18n.T, or a plain msgid string)
    options: list = field(default_factory=list)
    standard: Any = None  # accepted-physics value; None = not a law parameter
    help: str = ""
    show_if: dict | None = None  # {"param_id": [values]}: shown only for those values
    live: bool = False  # changeable while the world runs (command "set"); otherwise fixed for the world
    hidden: bool = False  # not shown in the parameter forms (set by the player itself, e.g. a scene loaded from a file)

    def to_json(self) -> dict:
        d = asdict(self)
        d["options"] = [{"value": o[0], "label": o[1], **({"show_if": o[2]} if len(o) > 2 and o[2] else {})}
                        for o in self.options]
        return d


class Schema:
    def __init__(self, params: list[Param], presets: dict | None = None):
        self.params = params
        self.by_id = {p.id: p for p in params}
        if len(self.by_id) != len(params):
            raise ValueError("duplicate parameter id")
        self.presets = presets or {}

    def defaults(self) -> dict:
        return {p.id: p.default for p in self.params}

    def live_ids(self) -> list[str]:
        return [p.id for p in self.params if p.live]

    def coerce_live(self, current: dict, changes: dict) -> tuple[dict, list[str]]:
        """Merge ``changes`` (live parameters only) into ``current`` and validate. Returns (merged, errors)."""
        out = dict(current)
        errors = []
        for k, v in changes.items():
            p = self.by_id.get(k)
            if p is None:
                errors.append(ParamError(T("there is no parameter “{id}”", id=k), k))
            elif not p.live:
                errors.append(ParamError(T("“{label}” cannot be changed while the world runs: it is a parameter of the "
                                           "world (a new world)", label=p.label), k))
            else:
                x, err = _coerce(p, v)
                if err:
                    errors.append(err)
                else:
                    out[k] = x
        return out, errors

    def to_json(self) -> dict:
        return {
            "params": [p.to_json() for p in self.params],
            "presets": [{"id": k, "label": v["label"], "params": v.get("params", {}), "note": v.get("note", "")}
                        for k, v in self.presets.items()],
        }

    def resolve(self, preset: str | None, values: dict | None) -> tuple[dict, list[str]]:
        """Defaults, then the preset, then explicit values; validated. Returns (params, errors)."""
        merged = self.defaults()
        errors: list[str] = []
        if preset:
            if preset not in self.presets:
                errors.append(ParamError(T("there is no scenario “{id}”; there are: {names}", id=preset,
                                           names=join([T("“{label}”", label=v.get("label", k))
                                                       for k, v in self.presets.items()], ", "))))
            else:
                merged.update(self.presets[preset].get("params", {}))
        if values:
            for k, v in values.items():
                if k not in self.by_id:
                    errors.append(ParamError(T("there is no parameter “{id}”", id=k), k))
                else:
                    merged[k] = v
        out = {}
        for p in self.params:
            v, err = _coerce(p, merged.get(p.id, p.default))
            if err:
                errors.append(err)
                v = p.default
            out[p.id] = v
        return out, errors

    def si(self, params: dict, pid: str) -> float:
        return float(params[pid]) * self.by_id[pid].scale

    def modifications(self, params: dict) -> list[dict]:
        """World parameters that differ from accepted physics, among those currently shown."""
        mods = []
        for p in self.params:
            if p.standard is None or not self.shown(p, params):
                continue
            v = params[p.id]
            std = p.standard
            if p.type in ("float", "int"):
                differs = not math.isclose(float(v), float(std), rel_tol=1e-12, abs_tol=0.0)
            else:
                differs = v != std
            if differs:
                label = v
                if p.type == "select":
                    names = {o[0]: o[1] for o in p.options}
                    label = names.get(v, v)
                    std = names.get(p.standard, p.standard)
                mods.append({"id": p.id, "label": p.label, "value": label, "standard": std})
        return mods

    def shown(self, p: Param, params: dict) -> bool:
        if not p.show_if:
            return True
        for k, allowed in p.show_if.items():
            if params.get(k) not in allowed:
                return False
        return True


class ParamError(T):
    """A refused value, in the owner's terms (review 2026-11-04 UX-params P2): the parameter by its label and unit,
    the value and what is allowed. A text (``T``; a list of them is joined by ``lfviz.i18n.join``) that also carries
    the parameter's id (``pid``), so that a form can mark the field."""

    def __init__(self, text, pid: str | None = None):
        super().__init__(text if is_t(text) else str(text))
        self.pid = pid


def _num(x) -> str:
    """A number as the owner typed it before the i18n («1600», «0,001», «2·10⁻⁵»). Kept for the worlds' older texts;
    a text passes its numbers as arguments of a ``T`` instead."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    if x != 0 and (abs(x) >= 1e7 or abs(x) < 1e-4):
        m, e = f"{x:.4g}".split("e")
        sup = str(int(e)).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
        return f"{m}·10{sup}".replace(".", ",")
    s = f"{x:.10g}"
    return s.replace(".", ",")


def _name(p: Param):
    """The parameter as the form shows it: its label, with the unit when the label does not carry one."""
    lab = p.label or p.id
    unit = p.unit
    if unit and not names_unit(lab, unit):  # by msgid and arguments (review i18n-code F2, F14)
        return T("“{label}, {unit}”", label=lab, unit=unit)
    return T("“{label}”", label=lab)


def _range(p: Param):
    if p.min is not None and p.max is not None:
        return T("from {lo:.10g} to {hi:.10g}", lo=p.min, hi=p.max)
    if p.min is not None:
        return T("at least {lo:.10g}", lo=p.min)
    if p.max is not None:
        return T("at most {hi:.10g}", hi=p.max)
    return T("any finite number")


def _coerce(p: Param, v: Any) -> tuple[Any, str | None]:
    E = lambda text: ParamError(text, p.id)  # noqa: E731
    name = _name(p)
    try:
        if p.type == "float":
            if v is None or (isinstance(v, str) and not v.strip()):
                return None, E(T("{name}: the field is empty — enter a number {range}", name=name, range=_range(p)))
            x = float(v)
            if not math.isfinite(x):
                return None, E(T("{name}: enter a finite number {range}", name=name, range=_range(p)))
        elif p.type == "int":
            if v is None or (isinstance(v, str) and not v.strip()):
                return None, E(T("{name}: the field is empty — enter a whole number {range}", name=name,
                                 range=_range(p)))
            x = int(round(float(v)))
        elif p.type == "bool":
            if isinstance(v, str):
                x = v.lower() in ("1", "true", "yes", "on")
            else:
                x = bool(v)
            return x, None
        elif p.type == "select":
            values = [o[0] for o in p.options]
            if v not in values and isinstance(v, str):
                # a form sends a numeric option's value as text («256», «1» for 1.0): take the option itself (UX-ui L2)
                try:
                    num = float(v.strip())
                except ValueError:
                    num = None
                match = [o for o in values if not isinstance(o, (str, bool)) and isinstance(o, (int, float))
                         and num is not None and float(o) == num]
                if match:
                    return match[0], None
            if v not in values:
                labels = join([T("“{label}”", label=o[1]) for o in p.options], ", ")
                return None, E(T("{name}: there is no option “{value}”; allowed: {options}", name=name, value=str(v),
                                 options=labels))
            return v, None
        elif p.type == "json":  # plain JSON data (dicts, lists, numbers, strings), bounded in size
            import json
            text = json.dumps(v, ensure_ascii=False, allow_nan=False)
            if len(text) > JSON_MAX:
                return None, E(T("{name}: {n:d} characters — more than the limit of {max:d}", name=name, n=len(text),
                                 max=JSON_MAX))
            return json.loads(text), None
        else:
            return None, E(T("{name}: unknown parameter type {type}", name=name, type=p.type))
    except (TypeError, ValueError, OverflowError):
        if p.type == "int":
            return None, E(T("{name}: “{value}” is not a whole number; allowed: {range}", name=name, value=str(v),
                             range=_range(p)))
        if p.type == "float":
            return None, E(T("{name}: “{value}” is not a number; allowed: {range}", name=name, value=str(v),
                             range=_range(p)))
        return None, E(T("{name}: “{value}” is not a valid value", name=name, value=str(v)))
    if p.min is not None and x < p.min:
        return None, E(T("{name}: {x:.10g} is below the minimum {lo:.10g}; allowed: {range}", name=name, x=x, lo=p.min,
                         range=_range(p)))
    if p.max is not None and x > p.max:
        return None, E(T("{name}: {x:.10g} is above the maximum {hi:.10g}; allowed: {range}", name=name, x=x, hi=p.max,
                         range=_range(p)))
    return x, None
