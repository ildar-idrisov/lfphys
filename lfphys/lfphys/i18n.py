# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Translatable texts (owner, 2026-11-12: the interface in English by default and in Russian, every user-facing text in
every supported language; ``AGENTS.md`` §3 rule 13, ``LANGUAGES.md``).

A user-facing text is never a finished string in one language: it is ``T(msgid, **args)``, where ``msgid`` is the
English source text with named placeholders and ``args`` its values (numbers stay numbers, other texts may be ``T``
too). It serialises to JSON as ``{"$t": msgid, "a": {...}}``; the player renders it in the viewer's language from the
catalogues (``locales/<lang>.json``: msgid -> translation), formatting numbers by the language's conventions, so a run's
record is language-neutral and is read in any language later.

Placeholders: ``{name}`` (a number: up to 6 significant digits; a text: as is), ``{name:.3g}``, ``{name:.2f}``,
``{name:.2e}``, ``{name:d}``, each optionally with a sign flag (``{name:+.3g}``, ``{name:+d}``); ``{name:cap}`` renders
a text argument with its first letter capitalised; ``{name:unit}`` renders only the unit a label carries after its last
comma ("Mass, M☉" gives "M☉"). A placeholder followed by a period drops that period when its text
already ends a sentence (``"{text}. What to change: {hint}"``). A list argument is rendered as its items joined by
", ". Plural forms: a catalogue entry may be an object ``{"one": ..., "few": ..., "many": ..., "other": ...}`` (CLDR
categories), chosen by the argument ``n``. ``str(T(...))`` is the English rendering (logs, tests).

Helpers: ``text_of(exc)`` (the text an exception was raised with: a ``T`` or a plain string), ``english(x)`` (the
English rendering of a text, a list or a dict of texts), ``join(items, sep)`` (a text made of several texts),
``msgids(x)`` (every msgid inside a structure, for the completeness tests).
"""

from __future__ import annotations

import re

__all__ = ["T", "render", "is_t", "text_of", "english", "join", "msgids", "plural_category"]

_PH = re.compile(r"\{(\w+)(?::([^{}]*))?\}(\.?)")
_END = re.compile(r"[.!?…]$")


class T(dict):
    """A translatable text: ``T("Slit width {w:.3g} µm", w=0.5)``.

    Also rebuilt from its own items (``T({"$t": ..., "a": ...})`` or an iterable of pairs), so that copies made by
    ``dataclasses.asdict``, ``copy`` or a JSON round trip stay ``T``."""

    def __init__(self, msgid, **args):
        if not isinstance(msgid, str):
            items = dict(msgid) if msgid is not None and not isinstance(msgid, (int, float)) else {}
            if not isinstance(items.get("$t"), str) or not items["$t"]:
                raise ValueError("T needs a non-empty English msgid")
            msgid, args = items["$t"], {**(items.get("a") or {}), **args}
        if not msgid:
            raise ValueError("T needs a non-empty English msgid")
        super().__init__()
        self["$t"] = msgid
        if args:
            self["a"] = dict(args)

    @property
    def msgid(self) -> str:
        return self["$t"]

    @property
    def args(self) -> dict:
        return self.get("a", {})

    def __str__(self) -> str:
        return render(self, {})

    def __repr__(self) -> str:
        return f"T({self.msgid!r}, **{self.args!r})"


def is_t(x) -> bool:
    """A serialised or live translatable text."""
    return isinstance(x, dict) and isinstance(x.get("$t"), str)


_UNIT = re.compile(r",\s*([^,(]+?)\s*(\(|$)")


def _fmt(v, spec: str | None, catalogue: dict | None = None, lang: str = "en") -> str:
    if spec == "unit":  # the unit a label carries after its last comma ("Mass, M☉" -> "M☉")
        m = _UNIT.search(_fmt(v, None, catalogue, lang))
        return m.group(1) if m else ""
    if spec == "cap":
        spec = None
    if is_t(v):
        return render(v, catalogue, lang)
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt(x, spec, catalogue, lang) for x in v)
    if v is None:
        return "—"
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return str(v)
    if spec:
        try:
            return format(v, spec)
        except (ValueError, TypeError):
            return str(v)
    if isinstance(v, int):
        return str(v)
    return format(v, ".6g")


def _plural_en(n) -> str:
    return "one" if n == 1 else "other"


def plural_category(n, lang: str = "en") -> str:
    """The CLDR plural category of ``n`` in a language (English and Russian rules; others: "other")."""
    try:
        x = float(n)
    except (TypeError, ValueError):
        return "other"
    if lang == "ru":
        if x != int(x):
            return "other"
        i = abs(int(x))
        if i % 10 == 1 and i % 100 != 11:
            return "one"
        if 2 <= i % 10 <= 4 and not 12 <= i % 100 <= 14:
            return "few"
        return "many"
    return "one" if x == 1 else "other"


def render(x, catalogue: dict | None = None, lang: str = "en") -> str:
    """English (or a given catalogue's) rendering of a text; plain strings pass through. The player has its own
    renderer with the language's number formats and plural rules; this one serves logs, tests and files (``lang``:
    whose plural rules choose a catalogue's plural form)."""
    if not is_t(x):
        return str(x)
    msg = x["$t"]
    args = x.get("a", {}) or {}
    tr = (catalogue or {}).get(msg, msg)
    if isinstance(tr, dict):  # plural forms
        tr = tr.get(plural_category(args.get("n", 0), lang), tr.get("other", msg))

    def sub(m):
        name, spec, dot = m.group(1), m.group(2), m.group(3)
        if name not in args:
            return m.group(0)
        s = _fmt(args[name], spec, catalogue, lang)
        if spec == "cap":
            s = s[:1].upper() + s[1:]
        return s + ("" if dot and _END.search(s) else dot)

    return _PH.sub(sub, tr)


def text_of(x):
    """The text an exception was raised with — ``ValueError(T(...))`` gives the ``T`` — or a plain string. A ``T``
    passes through; anything else is ``str(x)``."""
    if is_t(x):
        return x
    if isinstance(x, BaseException):
        v = getattr(x, "owner", None)  # an exception that keeps its composed text (lfviz.errors.Refusal)
        if is_t(v):
            return v
        if len(x.args) == 1 and is_t(x.args[0]):
            return x.args[0]
    return str(x)


def english(x):
    """The English rendering of a text, or of every text inside a list or a dict (logs, tests, API clients)."""
    if is_t(x):
        return render(x, {})
    if isinstance(x, (list, tuple)):
        return [english(v) for v in x]
    if isinstance(x, dict):
        return {k: english(v) for k, v in x.items()}
    return x


def join(items, sep: str = "; "):
    """One text made of several (``T`` or plain strings), joined by ``sep`` (punctuation, not words). A single item is
    returned as it is; none gives ""."""
    items = [i for i in items if i not in (None, "")]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return T(sep.join("{p%d}" % i for i in range(len(items))), **{f"p{i}": v for i, v in enumerate(items)})


def msgids(x, out: set | None = None) -> set:
    """Every msgid inside a structure (``T`` objects and their arguments, lists, dicts)."""
    out = set() if out is None else out
    if is_t(x):
        out.add(x["$t"])
        for v in (x.get("a") or {}).values():
            msgids(v, out)
    elif isinstance(x, dict):
        for v in x.values():
            msgids(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            msgids(v, out)
    return out
