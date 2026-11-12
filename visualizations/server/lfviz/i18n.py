# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The interface's languages on the server side (owner, 2026-11-12; ``AGENTS.md`` §3 rule 13, ``LANGUAGES.md``,
``RULES.md`` «Languages and i18n»).

* ``T`` and its helpers are the engine's (``lfphys.i18n``), re-exported: every user-facing text the server sends is a
  ``T`` (English msgid + arguments), rendered by the player in the viewer's language.
* The catalogues (``locales/<lang>.json``: msgid -> translation) live next to the code whose texts they translate: the
  engine's (``lfphys/lfphys/locales``), the framework's (``visualizations/locales``: server, player, catalogue,
  instruments, the test worlds) and every world's (``<world>/locales``, also the folders of ``LFVIZ_EXTRA``).
  ``catalogue(lang)`` merges them; a msgid translated differently in two files is a conflict (``conflicts``, caught by
  ``tests/test_i18n.py``; the first file in the order above wins meanwhile).
* ``GET /api/i18n/<lang>`` serves the merged catalogue (``{lang, messages}``), cached until a file changes.
* HTTP errors are ``{"error": <T>, "text": <English>}`` (``error_body``).
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from . import registry

registry.ensure_path()

from lfphys.i18n import T, english, is_t, join, msgids, plural_category, render, text_of  # noqa: E402

__all__ = ["T", "render", "is_t", "text_of", "english", "join", "msgids", "plural_category", "LANGS", "DEFAULT",
           "catalogue_files", "catalogue", "conflicts", "payload", "error_body", "render_in"]

LANGS = ("en", "ru")  # LANGUAGES.md; English is the source language and the default
DEFAULT = "en"
log = logging.getLogger("lfviz")


def catalogue_files(lang: str) -> list[Path]:
    """The catalogue files of a language, in merge order: the engine, the framework, the worlds (sorted)."""
    files = [registry.ENGINE / "lfphys" / "locales" / f"{lang}.json", registry.ROOT / "locales" / f"{lang}.json"]
    for vid in registry.viz_ids():
        try:
            files.append(registry.folder(vid) / "locales" / f"{lang}.json")
        except KeyError:
            continue
    return [f for f in files if f.is_file()]


def _read(f: Path) -> dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        log.warning("i18n: catalogue %s not read: %s", f, e)
        return {}
    if not isinstance(d, dict):
        log.warning("i18n: catalogue %s is not an object", f)
        return {}
    return {k: v for k, v in d.items() if isinstance(k, str) and isinstance(v, (str, dict))}


def _merge(lang: str) -> tuple[dict, list]:
    out: dict = {}
    origin: dict = {}
    clashes = []
    for f in catalogue_files(lang):
        for k, v in _read(f).items():
            if k in out:
                if out[k] != v:
                    clashes.append({"msgid": k, "files": [str(origin[k]), str(f)], "values": [out[k], v]})
                continue
            out[k] = v
            origin[k] = f
    return out, clashes


_CACHE: dict = {}


def _signature(lang: str) -> tuple:
    sig = []
    for f in catalogue_files(lang):
        try:
            st = f.stat()
            sig.append((str(f), st.st_mtime_ns, st.st_size))
        except OSError:
            continue
    return tuple(sig)


def catalogue(lang: str) -> dict:
    """The merged catalogue of a language (msgid -> translation). For a language other than English, English's own
    entries (its plural forms and overrides) fill what the language lacks."""
    if lang not in LANGS:
        raise KeyError(lang)
    return _cached(lang)[0]


def _cached(lang: str):
    sig = _signature(lang) + (_signature(DEFAULT) if lang != DEFAULT else ())
    hit = _CACHE.get(lang)
    if hit and hit[0] == sig:
        return hit[1]
    own, clashes = _merge(lang)
    if clashes:
        log.warning("i18n: %d msgids translated differently in two %s catalogues, e.g. %r", len(clashes), lang,
                    clashes[0]["msgid"])
    if lang != DEFAULT:
        base, _ = _merge(DEFAULT)
        own = {**base, **own}
    body = json.dumps({"lang": lang, "messages": dict(sorted(own.items()))}, ensure_ascii=False).encode("utf-8")
    etag = '"' + hashlib.sha256(body).hexdigest()[:16] + '"'
    val = (own, clashes, body, etag)
    _CACHE[lang] = (sig, val)
    return val


def conflicts(lang: str) -> list[dict]:
    """The msgids translated differently in two catalogue files of a language."""
    return _merge(lang)[1]


def payload(lang: str) -> tuple[bytes, str]:
    """The JSON body served at ``/api/i18n/<lang>`` and its ETag."""
    if lang not in LANGS:
        raise KeyError(lang)
    _, _, body, etag = _cached(lang)
    return body, etag


def error_body(text, **extra) -> dict:
    """An HTTP error for an API client: the text as sent to the player (a ``T`` or a plain string) and its English
    rendering."""
    return {"error": text, "text": render(text) if is_t(text) else str(text), **extra}


def render_in(text, lang: str = DEFAULT) -> str:
    """A text rendered on the server in a language (a file the owner downloads, e.g. a CSV's header); numbers in
    Python's format. An unknown language gives English."""
    if not is_t(text):
        return "" if text is None else str(text)
    try:
        cat = catalogue(lang)
    except KeyError:
        lang, cat = DEFAULT, catalogue(DEFAULT)
    return render(text, cat, lang)
