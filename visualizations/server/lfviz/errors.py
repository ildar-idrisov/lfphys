# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What the owner reads when a world refuses something or fails (reviews 2026-11-04 UX-params P4 and UX-ui U13;
RULES.md §3, «Refusals and failures»).

Two kinds of failure reach the owner, and they must not look alike:

* a **refusal** — the world declines a combination it cannot compute (a parameter, a change of the set-up, an object
  in the scene). It is raised as ``Refusal`` (or, as before, a ``ValueError`` whose text is Russian) and shown as it
  is: in Russian, naming what is wrong and what to change ("сдвиньте пакет по x вне стенки", "уменьшите nx до 600");
* an **internal failure** — anything else (an English message of a library, a division by zero, a NaN, an
  allocation that failed). It is shown as a short Russian sentence that says what failed, that the change was not
  applied (or that the world is paused) and what the owner can do; the exception's own text and its traceback are kept
  for the developer (``detail``: the record's message and the worker's log ``worker.log``), never in a toast.

``owner_text(exc, context)`` makes the owner's text and the detail for every path of the runner and the worker
(``CONTEXTS``). ``Refusal(text, change=...)`` is the helper the worlds use for their own refusals.
"""

from __future__ import annotations

import re
import sys
import traceback

CYRILLIC = re.compile("[А-Яа-яЁё]")

#: the prefix per path and what to do after an internal failure there; ``{label}``: an action's label, ``{t}``: the time
CONTEXTS = {
    "set": ("Изменение не применено", ""),
    "action": ("Действие «{label}» не выполнено", ""),
    "scene": ("Сцена не изменена", ""),
    "view": ("Срез не построен", ""),
    "new_world": ("Новый мир не создан", " Прежний мир продолжается."),
    "build": ("Мир не создан", ""),
    "restore": ("Мир не восстановлен", ""),
    "advance": ("Расчёт мира остановился на t = {t}", " Мир на паузе; ⏺ продолжит."),
    "step": ("Шаг не сделан", ""),
}
#: the integrator's wording of an internal failure (2026-11-05), and its variant where nothing was saved yet
INTERNAL = "внутренняя ошибка мира — {what} — запуск сохранён, можно вернуться назад или изменить параметры"
INTERNAL_BUILD = "внутренняя ошибка мира — {what} — измените параметры и запустите снова"


class Refusal(ValueError):
    """A deliberate refusal for the owner, shown as it is (a ``ValueError``, so that every refusal path keeps working).

    ``text``   what is wrong, in the owner's terms (Russian; the object or the parameter by its label, numbers with
               units);
    ``hint``   what to change so that it works (Russian, optional; shown as «что изменить: …»);
    ``detail`` the engine's own sentence or numbers for the developer (optional: shown folded, under «подробности»).
    ``change`` is accepted as another name of ``hint``.
    """

    def __init__(self, text: str, hint: str | None = None, detail: str | None = None, change: str | None = None):
        self.text = str(text).strip()
        hint = hint if hint is not None else change
        self.hint = str(hint).strip() if hint else None
        self.detail = detail
        msg = self.text
        if self.hint:
            msg = msg.rstrip(".") + ". Что изменить: " + self.hint
        super().__init__(msg)


#: English sentences of libraries and of the engine that the owner may meet anywhere, put into his terms. The worlds
#: translate the refusals of their own domain at their boundary (Refusal); this table is the framework's fallback.
KNOWN = [
    (re.compile(r"Unable to allocate ([\d.]+\s*[KMGTP]i?B)"),
     lambda m: f"не хватает памяти: расчёт запросил {_units(m.group(1))} сразу"),
    (re.compile(r"array is too big|Maximum allowed dimension exceeded|maximum supported dimension"),
     lambda m: "не хватает памяти: массив такого размера создать нельзя"),
    (re.compile(r"Probabilities contain NaN|probabilities do not sum to 1"),
     lambda m: "вероятности стали не числами (NaN): волна или веса разошлись"),
    (re.compile(r"float division by zero|division by zero|divide by zero"), lambda m: "деление на ноль"),
    (re.compile(r"math domain error|invalid value encountered"), lambda m: "недопустимое значение в формуле (NaN)"),
    (re.compile(r"overflow encountered|Result too large|Numerical result out of range"),
     lambda m: "переполнение: числа вышли за пределы представимых"),
    (re.compile(r"worldline is not timelike"),
     lambda m: "мировая линия не времениподобна: скорость не меньше скорости света этого мира"),
    (re.compile(r"not a finite number|must be finite|contains? (NaN|inf)"), lambda m: "значение не конечно (NaN или ∞)"),
]


def _units(s: str) -> str:
    s = re.sub(r"\.(?=\s)", "", s)  # numpy writes «591. GiB»
    return s.replace("GiB", "ГиБ").replace("MiB", "МиБ").replace("TiB", "ТиБ").replace("KiB", "КиБ")


def _memory_text(exc: BaseException) -> str:
    from . import limits  # noqa: PLC0415 - avoids an import cycle at module load
    m = KNOWN[0][0].search(str(exc))
    asked = f" (запрошено {_units(m.group(1))})" if m else ""
    budget = limits.worker_budget()
    lim = f", а вычислителю отведено {limits.fmt_bytes(budget)}" if budget else ""
    return (f"не хватает памяти{asked}{lim}. Что изменить: уменьшите сетку, область, число частиц или темп событий")


def owner_text(exc: BaseException, context: str = "", **fmt) -> tuple[str, str | None]:
    """The owner's text for ``exc`` on the path ``context`` (a key of ``CONTEXTS``) and a one-line detail for the
    developer (the exception's type and own text, never a traceback: the traceback goes to the worker's log only).
    ``fmt``: ``label`` (an action's label), ``t`` (the world time, formatted)."""
    head, tail = CONTEXTS.get(context, ("", ""))
    try:
        head = head.format(label=fmt.get("label", ""), t=fmt.get("t", "?"))
    except (KeyError, IndexError):
        pass
    detail = None
    if isinstance(exc, Refusal):
        body, detail, tail = str(exc), exc.detail, ""
    elif isinstance(exc, MemoryError) or (isinstance(exc, ValueError) and KNOWN[1][0].search(str(exc))) \
            or KNOWN[0][0].search(str(exc) or ""):
        body, detail = _memory_text(exc), _detail(exc)
    elif isinstance(exc, ValueError) and not isinstance(exc, UnicodeError):
        # a plain ValueError of a world: its own text, as before (integrator, 2026-11-05); a known English sentence of a
        # library is put into the owner's terms, its own text kept as the detail
        body, tail = str(exc), ""
        if not CYRILLIC.search(body):
            for rx, fn in KNOWN:
                m = rx.search(body)
                if m:
                    body, detail = fn(m), _detail(exc)
                    break
    else:
        detail = _detail(exc)
        what = _what(exc)
        body = (INTERNAL_BUILD if context in ("build", "restore") else INTERNAL).format(what=what)
    text = f"{head}: {body}" if head else body[:1].upper() + body[1:]
    if tail:
        text = text.rstrip(".") + "." + tail
    return text, detail


def _what(exc: BaseException) -> str:
    """What failed, in a few Russian words, with the exception's type."""
    s = str(exc)
    if CYRILLIC.search(s) and isinstance(exc, (RuntimeError, ArithmeticError)):
        return f"{s} ({type(exc).__name__})"
    for rx, fn in KNOWN:
        m = rx.search(s)
        if m:
            return f"{fn(m)} ({type(exc).__name__})"
    if isinstance(exc, ZeroDivisionError):
        return f"деление на ноль ({type(exc).__name__})"
    if isinstance(exc, (FloatingPointError, OverflowError)):
        return f"численная ошибка ({type(exc).__name__})"
    return type(exc).__name__


def _detail(exc: BaseException) -> str:
    """The traceback to the worker's log (stderr: the server keeps it as the run's ``worker.log``); the exception's
    type and own text, one line, for the record (shown folded under «подробности»; never a traceback)."""
    print("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), file=sys.stderr, flush=True)
    line = f"{type(exc).__name__}: {exc}".splitlines()[0] if str(exc) else type(exc).__name__
    return line[:500]
