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
* ``GET /api/i18n/<lang>`` and ``GET /static/locales/<lang>.json`` serve the merged catalogue (``{lang, messages}``),
  cached until a file changes, with an ETag and gzip (``payload``, ``etag_matches``). The player loads the second
  address, relative to its own modules, so that a static copy of the player (the public site, no server) loads the same
  file written by ``export`` (``python -m lfviz.i18n --export DIR``: ``DIR/<lang>.json`` and ``.json.gz``; review
  i18n-code F9).
* HTTP errors are ``{"error": <T>, "text": <English>}`` (``error_body``; English with ``en.json``'s plural forms).
* ``render_in(text, lang)``: a text rendered on the server for a file the owner downloads (a CSV's header), with the
  language's number format.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import re
import sys
from pathlib import Path

from . import registry

registry.ensure_path()

from lfphys.i18n import (T, english, is_t, join, json_hook, mentions, msgids, plural_category, render,  # noqa: E402
                         revive, same_text, strings_of, text_of)

__all__ = ["T", "render", "is_t", "text_of", "english", "join", "msgids", "plural_category", "revive", "json_hook",
           "same_text", "mentions", "strings_of", "LANGS", "DEFAULT", "catalogue_files", "catalogue", "conflicts",
           "payload", "etag_matches", "normalise", "export", "error_body", "render_in", "names_unit", "has_unit"]

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
    val = (own, clashes, body, etag, gzip.compress(body, compresslevel=9, mtime=0))
    _CACHE[lang] = (sig, val)
    return val


def conflicts(lang: str) -> list[dict]:
    """The msgids translated differently in two catalogue files of a language."""
    return _merge(lang)[1]


def normalise(code) -> str:
    """A language code as the catalogues name it: lower case, its primary subtag ("RU", "ru-RU" -> "ru"; review
    i18n-code F13). Not checked against ``LANGS``."""
    return str(code or "").strip().replace("_", "-").split("-")[0].lower()


def payload(lang: str, gz: bool = False) -> tuple[bytes, str]:
    """The JSON body served at ``/api/i18n/<lang>`` (and ``/static/locales/<lang>.json``) and its ETag; ``gz``: the
    body gzipped, with its own ETag (a representation of its own)."""
    lang = normalise(lang)
    if lang not in LANGS:
        raise KeyError(lang)
    _, _, body, etag, zbody = _cached(lang)
    return (zbody, etag[:-1] + '-gz"') if gz else (body, etag)


def etag_matches(header: str | None, etag: str) -> bool:
    """``If-None-Match`` against an ETag by the weak comparison (RFC 9110 §13.1.2): a list, ``W/`` and ``*`` (review
    i18n-code F13). The gzip variant's tag matches its own representation only."""
    if not header:
        return False
    if header.strip() == "*":
        return True
    want = etag[2:] if etag.startswith("W/") else etag
    for tag in header.split(","):
        tag = tag.strip()
        if tag.startswith("W/"):
            tag = tag[2:]
        if tag == want:
            return True
    return False


def export(folder) -> list[Path]:
    """The merged catalogue of every language as static files ``<lang>.json`` (the body ``/api/i18n/<lang>`` serves)
    and ``<lang>.json.gz``, for a copy of the player without the server (the public site: the build copies ``player/``
    and writes these into its ``locales/``). Returns the files written."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for lang in LANGS:
        _, _, body, _, zbody = _cached(lang)
        for name, data in ((f"{lang}.json", body), (f"{lang}.json.gz", zbody)):
            (folder / name).write_bytes(data)
            out.append(folder / name)
    return out


def error_body(text, **extra) -> dict:
    """An HTTP error for an API client: the text as sent to the player (a ``T`` or a plain string) and its English
    rendering (with ``en.json``'s plural forms: "the only worker is busy", not "all 1 workers"; review i18n-code F12)."""
    return {"error": text, "text": render_in(text, DEFAULT) if is_t(text) else str(text), **extra}


def render_in(text, lang: str = DEFAULT, numbers: bool = True) -> str:
    """A text rendered on the server in a language (a file the owner downloads, e.g. a CSV's header): the catalogue of
    the language (English: its plural forms), and the numbers as the player shows them in it (``numbers``; a decimal
    comma in Russian). An unknown language gives English. A plain string passes as it is."""
    if not is_t(text):
        return "" if text is None else str(text)  # i18n-str-ok: a plain string, not a text
    lang = normalise(lang)
    try:
        cat = catalogue(lang)
    except KeyError:
        lang, cat = DEFAULT, catalogue(DEFAULT)
    return render(text, cat, lang, numbers=numbers and lang != DEFAULT)


def names_unit(label, unit) -> bool:
    """Whether a label (a text or a plain string) names a unit (a text or a plain string) already: the unit is one of
    the label's arguments, or the English msgid of the label or of one of its parts names the unit's msgid
    (``has_unit``)."""
    if not unit:
        return False
    if is_t(unit) and mentions(label, unit):
        return True
    if is_t(unit) and unit.get("a"):  # a unit with arguments: only the same text counts
        return False
    u = unit["$t"] if is_t(unit) else str(unit)
    return any(has_unit(s, u) for s in strings_of(label))


def has_unit(label: str, unit: str) -> bool:
    """Whether the label names the unit already: after a comma, in brackets, or as a word of its own (plain strings:
    English msgids or plain labels)."""
    if f", {unit}" in label or f"({unit}" in label:
        return True
    return unit in re.split(r"[^\w/·²³⁻¹°%]+", label)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="The interface's catalogues (lfviz.i18n).")
    ap.add_argument("--export", metavar="DIR", help="write <lang>.json and <lang>.json.gz of every language into DIR "
                                                    "(a static copy of the player: its locales/ folder)")
    a = ap.parse_args(argv)
    if a.export:
        for f in export(a.export):
            print(f)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
