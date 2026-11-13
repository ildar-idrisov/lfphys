# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What the owner reads when a world refuses something or fails (reviews 2026-11-04 UX-params P4 and UX-ui U13;
RULES.md §3, «Refusals and failures»). Every text here is a ``T`` (``lfviz.i18n``), rendered by the player in the
viewer's language.

Two kinds of failure reach the owner, and they must not look alike:

* a **refusal** — the world declines a combination it cannot compute (a parameter, a change of the set-up, an object
  in the scene). It is raised as ``Refusal`` (or, as before, a ``ValueError`` raised with a ``T``) and shown as it is,
  naming what is wrong and what to change ("move the packet along x away from the wall", "reduce nx to 600");
* an **internal failure** — anything else (an English message of a library, a division by zero, a NaN, an
  allocation that failed). It is shown as a short sentence that says what failed, that the change was not applied (or
  that the world is paused) and what the owner can do; the exception's own text and its traceback are kept for the
  developer (``detail``: the record's message and the worker's log ``worker.log``), never in a toast.

``owner_text(exc, context)`` makes the owner's text and the detail for every path of the runner and the worker
(``CONTEXTS``). ``Refusal(text, hint=...)`` is the helper the worlds use for their own refusals.
"""

from __future__ import annotations

import re
import sys
import traceback

from .i18n import T, is_t, render, text_of

from lfphys.codes import code_of  # noqa: E402 - lfphys is on the path once .i18n is imported

CYRILLIC = re.compile("[\u0400-\u04ff]")  # a text written in Russian before the i18n

#: the head per path and what to do after an internal failure there; ``{label}``: an action's label, ``{t}``: the time
CONTEXTS = {
    "set": (T("Change not applied"), None),
    "action": (T("Action “{label}” not done"), None),
    "scene": (T("Scene not changed"), None),
    "view": (T("Slice not built"), None),
    "new_world": (T("New world not created"), T("The previous world continues.")),
    "build": (T("World not created"), None),
    "restore": (T("World not restored"), None),
    "advance": (T("The world's computation stopped at t = {t}"), T("The world is paused; ⏺ resumes it.")),
    "step": (T("Step not done"), None),
}
#: the integrator's wording of an internal failure (2026-11-05), and its variant where nothing was saved yet
INTERNAL = T("internal error of the world — {what} — the run is saved; you can go back or change the parameters")
INTERNAL_BUILD = T("internal error of the world — {what} — change the parameters and start again")
#: a plain (untranslated) English refusal of the engine or a library: its sentence is the detail (review i18n-code F4)
PLAIN = T("the computation refused this; its own reason (in English) is under “details”")


class Refusal(ValueError):
    """A deliberate refusal for the owner, shown as it is (a ``ValueError``, so that every refusal path keeps working).

    ``text``   what is wrong, in the owner's terms (a ``T``: the object or the parameter by its label, numbers with
               units as arguments);
    ``hint``   what to change so that it works (a ``T``, optional; shown as "What to change: …");
    ``detail`` the engine's own sentence or numbers for the developer (optional, English: shown folded, under
               "details").
    ``change`` is accepted as another name of ``hint``. ``owner`` is the composed text the player shows; ``str()`` of
    the exception is its English rendering.
    """

    def __init__(self, text, hint=None, detail: str | None = None, change=None):
        self.text = text if is_t(text) else str(text).strip()
        hint = hint if hint is not None else change
        self.hint = (hint if is_t(hint) else str(hint).strip()) if hint else None
        self.detail = detail
        if self.hint:
            text_ = self.text if is_t(self.text) else self.text.rstrip(".")
            self.owner = T("{text}. What to change: {hint}", text=text_, hint=self.hint)
        else:
            self.owner = self.text
        super().__init__(self.owner)

    def __str__(self) -> str:
        return str(self.owner)


def _size(s: str):
    """«591. GiB» (numpy) as a text with its number: the unit in the viewer's language."""
    m = re.match(r"\s*([\d.]+)\s*([KMGTPE]?i?B)", s)
    if not m:
        return s
    unit = {"KiB": "KB", "MiB": "MB", "GiB": "GB", "TiB": "TB", "PiB": "PB", "EiB": "EB"}.get(m.group(2), m.group(2))
    if unit not in ("B", "KB", "MB", "GB", "TB", "PB", "EB"):
        return s
    return T("{n:.3g} " + unit, n=float(m.group(1).rstrip(".") or 0))  # i18n-msgids: "{n:.3g} B" "{n:.3g} KB" "{n:.3g} MB" "{n:.3g} GB" "{n:.3g} TB" "{n:.3g} PB" "{n:.3g} EB"


#: English sentences of libraries and of the engine that the owner may meet anywhere, put into his terms. The worlds
#: translate the refusals of their own domain at their boundary (Refusal); this table is the framework's fallback.
KNOWN = [
    (re.compile(r"Unable to allocate ([\d.]+\s*[KMGTP]i?B)"),
     lambda m: T("out of memory: the computation asked for {size} at once", size=_size(m.group(1)))),
    (re.compile(r"array is too big|Maximum allowed dimension exceeded|maximum supported dimension"),
     lambda m: T("out of memory: an array of this size cannot be created")),
    (re.compile(r"Probabilities contain NaN|probabilities do not sum to 1"),
     lambda m: T("probabilities became not-a-number (NaN): the wave or the weights diverged")),
    (re.compile(r"float division by zero|division by zero|divide by zero"), lambda m: T("division by zero")),
    (re.compile(r"math domain error|invalid value encountered"),
     lambda m: T("an invalid value in a formula (NaN)")),
    (re.compile(r"overflow encountered|Result too large|Numerical result out of range"),
     lambda m: T("overflow: the numbers left the representable range")),
    (re.compile(r"not a finite number|must be finite|contains? (NaN|inf)"),
     lambda m: T("a value is not finite (NaN or ∞)")),
]


#: the engine's refusals by their machine code (lfphys.codes; PR-B, 2026-11-13: the wording may change, the code stays),
#: where the framework says it in the owner's terms itself (an internal failure's "what", a plain text)
BY_CODE = {
    "gr.not_timelike": T("the worldline is not timelike: the speed is not below this world's speed of light"),
}


def _memory_text(exc: BaseException):
    from . import limits  # noqa: PLC0415 - avoids an import cycle at module load
    m = KNOWN[0][0].search(_english(exc))
    budget = limits.worker_budget()
    if m and budget:
        body = T("out of memory (asked for {size}), while the worker is given {budget}", size=_size(m.group(1)),
                 budget=limits.fmt_bytes(budget))
    elif m:
        body = T("out of memory (asked for {size})", size=_size(m.group(1)))
    elif budget:
        body = T("out of memory, while the worker is given {budget}", budget=limits.fmt_bytes(budget))
    else:
        body = T("out of memory")
    return T("{text}. What to change: {hint}", text=body,
             hint=T("reduce the grid, the region, the number of particles or the rate of events"))


def owner_text(exc: BaseException, context: str = "", **fmt):
    """The owner's text (a ``T``) for ``exc`` on the path ``context`` (a key of ``CONTEXTS``) and a one-line detail for
    the developer (the exception's type and own text in English, never a traceback: the traceback goes to the worker's
    log only). ``fmt``: ``label`` (an action's label, a text), ``t`` (the world time: a number of seconds, or a text)."""
    head, tail = CONTEXTS.get(context, (None, None))
    if head is not None:
        t = fmt.get("t", "?")
        head = T(head.msgid, **({"label": fmt.get("label", "")} if "{label}" in head.msgid else {}),
                 **({"t": T("{t} s", t=t) if isinstance(t, (int, float)) else t} if "{t}" in head.msgid else {}))
    detail = None
    own = text_of(exc)
    if isinstance(exc, Refusal):
        body, detail, tail = exc.owner, exc.detail, None
    elif isinstance(exc, MemoryError) or (isinstance(exc, ValueError) and KNOWN[1][0].search(_english(exc))) \
            or KNOWN[0][0].search(_english(exc)):
        body, detail = _memory_text(exc), _detail(exc)
    elif isinstance(exc, ValueError) and not isinstance(exc, UnicodeError):
        # a ValueError raised with a text: shown as it is (integrator, 2026-11-05); a known English sentence of a
        # library is put into the owner's terms; any other plain English sentence (an engine's or a library's that no
        # world translated) is not put in front of the owner in English: a translated head says so and the sentence
        # goes to the detail, under "details" (review i18n-code F4). A plain Russian text is a record's from before the
        # i18n: shown as it is.
        body, tail = own, None
        if not is_t(own) and code_of(exc) in BY_CODE:
            body, detail = BY_CODE[code_of(exc)], _detail(exc)
        elif not is_t(own) and not CYRILLIC.search(own):
            body, detail = PLAIN, _detail(exc)
            for rx, fn in KNOWN:
                m = rx.search(own)
                if m:
                    body = fn(m)
                    break
    else:
        detail = _detail(exc)
        body = T((INTERNAL_BUILD if context in ("build", "restore") else INTERNAL).msgid, what=_what(exc))
    text = T("{head}: {body}", head=head, body=body) if head is not None else T("{body:cap}", body=body)
    if tail is not None:
        text = T("{text}. {tail}", text=text, tail=tail)
    return text, detail


def _english(exc: BaseException) -> str:
    """The exception's own text in English: a text (also one read back from JSON) by its English rendering, never a
    dict's repr (review i18n-code F2)."""
    own = text_of(exc)
    return render(own) if is_t(own) else str(own or "")


def _what(exc: BaseException):
    """What failed, in a few words of the owner, with the exception's type."""
    s = _english(exc)
    own = text_of(exc)
    name = type(exc).__name__
    if code_of(exc) in BY_CODE:
        return T("{what} ({type})", what=BY_CODE[code_of(exc)], type=name)
    if (is_t(own) or CYRILLIC.search(s)) and isinstance(exc, (RuntimeError, ArithmeticError)):
        return T("{what} ({type})", what=own, type=name)
    for rx, fn in KNOWN:
        m = rx.search(s)
        if m:
            return T("{what} ({type})", what=fn(m), type=name)
    if isinstance(exc, ZeroDivisionError):
        return T("{what} ({type})", what=T("division by zero"), type=name)
    if isinstance(exc, (FloatingPointError, OverflowError)):
        return T("{what} ({type})", what=T("a numerical error"), type=name)
    return name


def _detail(exc: BaseException) -> str:
    """The traceback to the worker's log (stderr: the server keeps it as the run's ``worker.log``); the exception's
    type and own text in English, one line, for the record (shown folded under "details"; never a traceback)."""
    print("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), file=sys.stderr, flush=True)
    line = f"{type(exc).__name__}: {exc}".splitlines()[0] if str(exc) else type(exc).__name__
    return line[:500]
