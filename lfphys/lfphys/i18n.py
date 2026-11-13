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
``msgids(x)`` (every msgid inside a structure, for the completeness tests), ``revive(x)`` / ``json_hook`` (texts read
back from JSON become ``T`` again, so that ``str()`` is their English rendering, not a dict's repr), ``same_text(a, b)``
and ``mentions(outer, inner)`` (texts compared by msgid and arguments — never by their rendering or their repr: review
i18n-code F1, F2), ``strings_of(x)`` (the msgids and plain strings a text is made of).

Numbers: ``render`` formats them as Python does (logs, tests, the API's English ``text``); ``render(..., numbers=True)``
(the server's files for the owner, e.g. a CSV's header in ``?lang=ru``) formats them as the player does in that
language: a decimal comma, the minus sign −, grouped thousands, m·10ⁿ. A plural form is chosen by the number as it is
shown (``{n:d}`` of 4.6 is "5", so the form of 5; review i18n-code F11).
"""

from __future__ import annotations

import math
import re

__all__ = ["T", "render", "is_t", "text_of", "english", "join", "msgids", "plural_category", "revive", "json_hook",
           "same_text", "mentions", "strings_of"]

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


_SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
_SPEC = re.compile(r"^(\+)?(?:\.(\d+))?([gfed%])?$")


def _group(digits: str, sep: str) -> str:
    """Thousands grouped from four digits on (as the player's Intl formats: "1 234")."""
    out = []
    while len(digits) > 3:
        out.insert(0, digits[-3:])
        digits = digits[:-3]
    return sep.join([digits] + out)


def _plain(a: float, digits: int) -> str:
    """A non-negative number with at most ``digits`` significant digits in plain notation, without trailing zeros."""
    x = float(f"{a:.{digits}g}")
    if x == int(x) and x < 1e16:
        return str(int(x))
    s = f"{x:.{max(digits - 1 - math.floor(math.log10(x)), 0)}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _local(v, spec: str | None, lang: str) -> str:
    """A number as the player shows it in ``lang`` (player/js/i18n.js ``fmt``): ru a decimal comma and narrow no-break
    spaces between thousands, en a point and commas; the minus sign −; m·10ⁿ for |x| ≥ 10⁷ or < 10⁻⁴ (g) and for e."""
    m = _SPEC.match(spec or "") or _SPEC.match("")
    plus, prec, kind = bool(m.group(1)), (int(m.group(2)) if m.group(2) else None), m.group(3) or "g"
    dec, grp = (",", " ") if lang == "ru" else (".", ",")
    x = float(v)
    if math.isnan(x):
        return "—"
    sign = "−" if x < 0 else ("+" if plus else "")
    a = abs(x)
    if math.isinf(x):
        return sign + "∞"

    def num(s: str) -> str:
        whole, _, frac = s.partition(".")
        return _group(whole, grp) + (dec + frac if frac else "")

    def sci(digits: int | None, decimals: int | None) -> str:
        e = math.floor(math.log10(a))
        mant = a / 10 ** e
        mr = round(mant, decimals) if decimals is not None else float(f"{mant:.{digits}g}")
        if mr >= 10:
            mr, e = mr / 10, e + 1
        ms = f"{mr:.{decimals}f}" if decimals is not None else _plain(mr, digits)
        return ms.replace(".", dec) + "·10" + str(e).translate(_SUP)

    if kind == "d" or (spec in (None, "") and float(a).is_integer() and a < 2 ** 53):  # whole numbers exact (F3)
        body = num(str(int(round(a))))
    elif kind == "f":
        body = num(f"{a:.{6 if prec is None else prec}f}")
    elif kind == "%":
        body = num(f"{a * 100:.{0 if prec is None else prec}f}") + " %"
    elif kind == "e":
        p = 6 if prec is None else prec
        body = num(f"{0:.{p}f}") if a == 0 else sci(None, p)
    else:
        d = min(max(6 if prec is None else prec, 1), 15)
        body = sci(d, None) if a != 0 and (a >= 1e7 or a < 1e-4) else num(_plain(a, d))
    return sign + body


def _fmt(v, spec: str | None, catalogue: dict | None = None, lang: str = "en", numbers: bool = False) -> str:
    if spec == "unit":  # the unit a label carries after its last comma ("Mass, M☉" -> "M☉")
        m = _UNIT.search(_fmt(v, None, catalogue, lang, numbers))
        return m.group(1) if m else ""
    if spec == "cap":
        spec = None
    if is_t(v):
        return render(v, catalogue, lang, numbers=numbers)
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt(x, spec, catalogue, lang, numbers) for x in v)
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "true" if v else "false"  # as the player's String(true) (review i18n-code F10)
    if not isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, float) and not math.isfinite(v):  # as the player: "—" and "∞"
        return "—" if math.isnan(v) else ("-∞" if v < 0 else ("+∞" if (spec or "").startswith("+") else "∞"))
    if numbers:
        return _local(v, spec, lang)
    if spec:
        if spec.lstrip("+") == "d" and isinstance(v, float):
            v = int(round(v))  # as the player: a float with {n:d} is rounded
        try:
            return format(v, spec)
        except (ValueError, TypeError):
            return str(v)
    if isinstance(v, int):
        return str(v)
    return format(v, ".6g")


def plural_category(n, lang: str = "en", fraction: bool = False) -> str:
    """The CLDR plural category of ``n`` in a language (English and Russian rules; others: "other"). ``fraction``: the
    number is shown with decimals ("1.00"), which is "other" in both languages. Total: a missing, non-numeric or
    non-finite ``n`` is "other" (review i18n-code F10)."""
    if isinstance(n, bool):
        return "other"
    try:
        x = float(n)
    except (TypeError, ValueError):
        return "other"
    if not math.isfinite(x) or fraction or x != int(x):
        return "other"
    i = abs(int(x))
    if lang == "ru":
        if i % 10 == 1 and i % 100 != 11:
            return "one"
        if 2 <= i % 10 <= 4 and not 12 <= i % 100 <= 14:
            return "few"
        return "many"
    if lang == "en":
        return "one" if i == 1 else "other"
    return "other"


def _shown(n, spec: str | None):
    """The value of ``n`` as its placeholder shows it, and whether decimals are shown (the plural form follows the
    shown number: review i18n-code F11)."""
    if isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n):
        return n, False
    m = _SPEC.match(spec or "")
    if not m:
        return n, False
    prec, kind = (int(m.group(2)) if m.group(2) else None), m.group(3) or "g"
    if kind == "d":
        return round(n), False
    if kind == "f":
        p = 6 if prec is None else prec
        return round(n, p), p > 0
    if kind in ("e", "%"):
        return n, True
    if spec in (None, "") and isinstance(n, int):
        return n, False
    return float(f"{n:.{min(max(6 if prec is None else prec, 1), 15)}g}"), False


def render(x, catalogue: dict | None = None, lang: str = "en", numbers: bool = False) -> str:
    """English (or a given catalogue's) rendering of a text; plain strings pass through. The player has its own
    renderer; this one serves logs, tests and files (``lang``: whose plural rules choose a catalogue's plural form;
    ``numbers``: the numbers formatted as the player formats them in ``lang``, for a file the owner reads)."""
    if not is_t(x):
        return str(x)
    msg = x["$t"]
    args = x.get("a", {}) or {}
    tr = (catalogue or {}).get(msg, msg)
    if isinstance(tr, dict):  # plural forms, chosen by n as it is shown
        spec = next((m.group(2) for m in _PH.finditer(msg) if m.group(1) == "n"), None)
        n, frac = _shown(args.get("n"), spec)
        tr = tr.get(plural_category(n, lang, frac), tr.get("other", msg))

    def sub(m):
        name, spec, dot = m.group(1), m.group(2), m.group(3)
        if name not in args:
            return m.group(0)
        s = _fmt(args[name], spec, catalogue, lang, numbers)
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
    return T(sep.join("{p%d}" % i for i in range(len(items))),  # i18n-msgids: (placeholders and punctuation only)
             **{f"p{i}": v for i, v in enumerate(items)})


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

def revive(x):
    """A structure read back from JSON with its texts as ``T`` again (a decoded text is a plain dict, whose ``str()`` is
    a repr: review i18n-code F2)."""
    if isinstance(x, dict):
        if isinstance(x, T):
            return x
        if is_t(x):
            try:
                return T(x["$t"], **{str(k): revive(v) for k, v in (x.get("a") or {}).items()})
            except (ValueError, TypeError):
                return x
        return {k: revive(v) for k, v in x.items()}
    if isinstance(x, list):
        return [revive(v) for v in x]
    return x


def json_hook(d: dict):
    """``json.loads(..., object_hook=json_hook)``: every serialised text comes back as a ``T``."""
    if isinstance(d.get("$t"), str) and d["$t"] and set(d) <= {"$t", "a"} and isinstance(d.get("a") or {}, dict):
        return T(d["$t"], **(d.get("a") or {}))
    return d


def _key(x):
    if is_t(x):
        return ("$t", x["$t"], tuple(sorted((str(k), _key(v)) for k, v in (x.get("a") or {}).items())))
    if isinstance(x, dict):
        return ("{}", tuple(sorted((str(k), _key(v)) for k, v in x.items())))
    if isinstance(x, (list, tuple)):
        return ("[]", tuple(_key(v) for v in x))
    return ("=", x)


def same_text(a, b) -> bool:
    """Whether two texts are the same: the same msgid with the same arguments (live ``T`` or decoded dicts alike), or
    equal plain values."""
    try:
        return _key(a) == _key(b)
    except TypeError:
        return False


def mentions(outer, inner) -> bool:
    """Whether ``inner`` is ``outer`` itself or one of its arguments at any depth, compared by msgid and arguments (a
    plain string also inside a plain string). E.g. a probe's quantity ``T("“{label}”: to the nearest particle",
    label=probe_label)`` mentions ``probe_label`` (review i18n-code F1)."""
    if inner is None or inner == "":
        return False
    if same_text(outer, inner):
        return True
    if isinstance(outer, str) and isinstance(inner, str):
        return inner in outer
    if is_t(outer):
        return any(mentions(v, inner) for v in (outer.get("a") or {}).values())
    if isinstance(outer, (list, tuple)):
        return any(mentions(v, inner) for v in outer)
    return False


def strings_of(x) -> list[str]:
    """The English pieces a text is made of: its msgid, those of its arguments, and its plain-string arguments (for
    structural checks such as "does this label name its unit already", never on a rendering)."""
    out: list[str] = []
    if is_t(x):
        out.append(x["$t"])
        for v in (x.get("a") or {}).values():
            out += strings_of(v)
    elif isinstance(x, str):
        out.append(x)
    elif isinstance(x, (list, tuple)):
        for v in x:
            out += strings_of(v)
    return out
