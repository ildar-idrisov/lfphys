# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Build the public site: the player in static mode, the catalogue as JSON files and the recordings (design of the start
page §4.5, §5.1; CONTRACT of steps S and P).

    python3 site/build.py --recordings DIR --out DIR [--base /lfphys/]

What it writes into ``--out`` (served at ``--base``, e.g. https://ildar-idrisov.github.io/lfphys/):

* ``index.html``, ``run.html``, ``legal.html``, ``worksheet.html`` (a lab's worksheet, once the player has it): the player's pages with ``<meta name="lf-mode" content="static">``,
  ``<meta name="lf-base" content="<base>">`` and the import map's targets made relative (``"/static/"`` ->
  ``"./static/"``, ``"/viz/"`` -> ``"./viz/"``, ``three`` -> ``./static/vendor/…``); nothing else in a page is
  rewritten (CONTRACT, Additions). A page that still lacks a meta or the import map gets one, with a warning.
  ``404.html``: a small page of its own (GitHub Pages serves it at any missing address, so its links carry the base);
* ``static/``: ``player/`` without its tests and ``legacy/``, and ``static/locales/<lang>.json`` (``lfviz.i18n
  --export``); ``viz/<id>/``: each world's ``web/``;
* ``api/viz.json``, ``api/viz/<id>.json`` (also under each old id), ``api/planned.json``, ``api/audiences.json``,
  ``api/recordings.json``, ``api/health.json`` (``{version, visualizations, cite}``): what the server's ``GET /api/…`` returns;
  ``aliases.json`` (``registry.ALIASES``);
* ``recordings/<world>/``: each world's ``index.json`` and the files it names, from ``--recordings`` (``DIR/<world>/``
  or, as the CI's artifacts land, ``DIR/rec-<world>/``), only the entries the registry asks for now (review F13); its
  atlases ``recordings/<world>/atlas/<atlas>/`` (the manifest, the base, the pool and the points it names; design of 2026-11-14
  §1.3), only those the registry asks for;
  ``api/recordings.json`` carries the public site's ``site`` and ``published`` (``site/site.json``) and ``expected``,
  the keys of every world's recordings and atlases as the code gives them (``lfviz.app.expected_keys``; integrator D11);
* ``images/<id>.jpg``: each world's poster from ``docs/images/`` (the cards' pictures); ``legal/<name>``: the full texts the licence page shows;
* ``site-manifest.json``: every file with its size and sha256, every world, recording and atlas with its key and state
  (``present`` | ``stale`` | ``missing``), checked by ``site/check.py``.

The build itself fails only when the output folder is not its own (a non-empty folder without ``site-manifest.json``);
what is missing or over budget is the check's to fail.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitelib as L  # noqa: E402

from lfviz import __version__, i18n, registry  # noqa: E402
from lfviz import app as A  # noqa: E402
from lfviz.i18n import T  # noqa: E402

PAGES = ("index.html", "run.html", "legal.html", "worksheet.html")


def pages() -> tuple:
    """The player's pages the site carries (``worksheet.html`` once the player has it)."""
    return tuple(n for n in PAGES if (A.PLAYER / n).is_file())
SKIP = {"tests", "legacy", "node_modules", "__pycache__"}
IMPORTMAP = re.compile(r'<script\s+type="importmap"\s*>(.*?)</script>', re.S)
META = '<meta name="{name}" content="{value}">'


def _warn(*a):
    print("build:", *a, file=sys.stderr, flush=True)


def _dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _set_meta(html: str, name: str, value: str, page: str) -> str:
    pat = re.compile(r'<meta\s+name="%s"\s+content="[^"]*"\s*/?>' % re.escape(name))
    tag = META.format(name=name, value=value)
    if pat.search(html):
        return pat.sub(tag, html, count=1)
    _warn(f"{page}: no <meta name=\"{name}\">: inserted")
    return re.sub(r'(<meta charset="utf-8">)', r"\1\n" + tag, html, count=1)


def _relative(target: str) -> str:
    for prefix in ("/static/", "/viz/"):
        if target.startswith(prefix):
            return "." + target
    return target


def importmap(html: str, page: str) -> str:
    """The page's import map with its targets relative to the base (one map; ``"/static/"`` and ``"/viz/"`` always)."""
    m = IMPORTMAP.search(html)
    imports = {}
    if m:
        imports = json.loads(m.group(1)).get("imports", {})
    else:
        _warn(f"{page}: no import map: inserted")
    imports.setdefault("three", "/static/vendor/three-0.185.1/three.module.min.js")
    imports.setdefault("/static/", "/static/")
    imports.setdefault("/viz/", "/viz/")
    tag = '<script type="importmap">' + json.dumps({"imports": {k: _relative(v) for k, v in imports.items()}}) + \
          "</script>"
    if m:
        return html[:m.start()] + tag + html[m.end():]
    i = html.find("<script")  # an import map comes before every module script
    i = html.find("</head>") if i < 0 else i
    return html[:i] + tag + "\n" + html[i:]


def page(src: Path, base: str) -> str:
    html = src.read_text(encoding="utf-8")
    html = _set_meta(html, "lf-mode", "static", src.name)
    html = _set_meta(html, "lf-base", base, src.name)
    return importmap(html, src.name)


NOT_FOUND = T("This page does not exist on the lfphys site.")
TO_START = T("Go to the start page")


def page_404(base: str) -> str:
    """A page of its own for any missing address (GitHub Pages serves ``404.html`` there): its links carry the base,
    its text is in every language (the catalogue's)."""
    paras = "\n".join(
        f'<p lang="{lang}"{"" if lang == i18n.DEFAULT else " class=other"}>{escape(i18n.render_in(NOT_FOUND, lang))} '
        f'<a href="{base}">{escape(i18n.render_in(TO_START, lang))}</a>.</p>' for lang in i18n.LANGS)
    return f"""<!doctype html>
<!-- SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
     SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0 -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="lf-mode" content="static">
<meta name="lf-base" content="{base}">
<title>lfphys · 404</title>
<style>
body {{ font: 15px/1.5 system-ui, sans-serif; margin: 0; padding: 48px 24px; background: #fafaf7; color: #222; }}
main {{ max-width: 36em; margin: 0 auto; }} a {{ color: #1c5fb8; }} p.other {{ color: #555; }}
@media (prefers-color-scheme: dark) {{ body {{ background: #16181b; color: #ddd; }} a {{ color: #7fb0ff; }} p.other {{ color: #aaa; }} }}
</style>
</head>
<body>
<main>
<h1>404</h1>
{paras}
</main>
</body>
</html>
"""


def _copy_tree(src: Path, dst: Path, pages: bool = True):
    """Copy a folder without ``SKIP``; ``pages=False``: without its top-level HTML pages (the player's pages are the
    site's own, at its root)."""
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src)
        if set(rel.parts) & SKIP or not f.is_file() or (not pages and len(rel.parts) == 1 and f.suffix == ".html"):
            continue
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst / rel)


def _rec_source(folder: Path, vid: str) -> Path | None:
    for d in (folder / vid, folder / f"rec-{vid}", folder / f"rec-{vid}" / vid):
        if (d / "index.json").is_file():
            return d
    return None


def copy_recordings(src: Path | None, out: Path, worlds: list[str]) -> dict:
    """Copy each world's index and the files it names; {world: index} of what was copied."""
    got = {}
    if src is None or not src.is_dir():
        _warn(f"no recordings folder {src}: the site has no recordings")
        return got
    for vid in worlds:
        d = _rec_source(src, vid)
        if d is None:
            continue
        idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
        planned = {r["id"] for r in registry.recordings_of(registry.load(vid))}
        keep = []
        for e in idx.get("recordings") or []:
            if e.get("id") not in planned:  # a recording the registry no longer asks for stays off the site (F13)
                _warn(f"{vid}: {e.get('id')} is in its index but not asked for by the registry: left out")
                continue
            f = d / str(e.get("file", ""))
            if not f.is_file():
                _warn(f"{vid}: {e.get('file')} is named in its index but missing")
                continue
            (out / "recordings" / vid).mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out / "recordings" / vid / f.name)
            keep.append(e)
        idx["recordings"] = keep
        idx["atlases"] = copy_atlases(d, out / "recordings" / vid, vid, idx.get("atlases") or [])
        _dump(out / "recordings" / vid / "index.json", idx)
        got[vid] = idx
    return got


def copy_atlases(src: Path, dst: Path, vid: str, entries: list) -> list:
    """Copy a world's atlases that the registry asks for (design of 2026-11-14 §1.3): each manifest with its base, its
    pool (EX2 §5 F10) and the point files it names; an atlas whose files are not all there is left out (the check says
    it is missing)."""
    planned = {a["id"] for a in registry.atlases_of(registry.load(vid))}
    keep = []
    for e in entries:
        if e.get("id") not in planned:
            _warn(f"{vid}: atlas {e.get('id')} is in its index but not asked for by the registry: left out")
            continue
        man_f = src / str(e.get("file", ""))
        try:
            man = json.loads(man_f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _warn(f"{vid}: atlas {e.get('id')}: its manifest {e.get('file')} is missing or unreadable")
            continue
        names = [man["base"]["file"]] + [p[0] for p in man.get("points") or [] if p and p[0]] \
            + ([man["pool"]["file"]] if man.get("pool") else [])  # the blobs the points share (EX2 §5 F10)
        missing = [n for n in names if not (man_f.parent / n).is_file()]
        if missing:
            _warn(f"{vid}: atlas {e.get('id')}: {len(missing)} files named in its manifest are missing")
            continue
        to = dst / Path(e["file"]).parent
        to.mkdir(parents=True, exist_ok=True)
        for n in names + [man_f.name]:
            shutil.copy2(man_f.parent / n, to / n)
        keep.append(e)
    return keep


def build(recordings: Path | None, out: Path, base: str) -> dict:
    if not base.startswith("/") or not base.endswith("/"):
        raise SystemExit(f"--base {base!r}: an absolute path ending in /, e.g. /lfphys/")
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        if not (out / "site-manifest.json").is_file():
            raise SystemExit(f"{out} is not empty and holds no site-manifest.json: not a site of this build")
        for p in out.iterdir():  # the folder may be a mount point: its contents go, not the folder
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    out.mkdir(parents=True, exist_ok=True)

    # the player and the worlds' browser modules
    _copy_tree(A.PLAYER, out / "static", pages=False)
    i18n.export(out / "static" / "locales")
    ids = registry.viz_ids()
    catalogue = []
    for vid in ids:
        web = registry.folder(vid) / "web"
        if web.is_dir():
            _copy_tree(web, out / "viz" / vid)
        d = registry.describe(vid)
        catalogue.append(d)
        _dump(out / "api" / "viz" / f"{vid}.json", d)
        for old in d.get("aliases") or []:
            _dump(out / "api" / "viz" / f"{old}.json", d)
    _dump(out / "api" / "viz.json", catalogue)
    _dump(out / "api" / "planned.json", A.planned_list())
    _dump(out / "api" / "audiences.json", A.audiences_list())
    _dump(out / "aliases.json", registry.ALIASES)
    _dump(out / "api" / "health.json", {"ok": True, "version": __version__, "visualizations": ids,
                                        "cite": registry.citation(), "static": True})

    # the recordings and their list
    demos = [d["id"] for d in catalogue if d.get("kind") != "playground" and d.get("recordings")]
    copy_recordings(Path(recordings) if recordings else None, out, demos)
    rec_list = A.recordings_list(out / "recordings")
    _dump(out / "api" / "recordings.json", rec_list)

    # pictures and the licence texts
    for vid in ids:  # the cards' pictures: each world's poster (docs/images/<id>.jpg, site/posters.mjs)
        f = L.IMAGES / f"{vid}.jpg"
        if f.is_file():
            (out / "images").mkdir(exist_ok=True)
            shutil.copy2(f, out / "images" / f.name)
    for name, src in A.LEGAL.items():
        if src.is_file():
            (out / "legal").mkdir(exist_ok=True)
            shutil.copy2(src, out / "legal" / name)

    # the pages
    for name in pages():
        (out / name).write_text(page(A.PLAYER / name, base), encoding="utf-8")
    (out / "404.html").write_text(page_404(base), encoding="utf-8")

    # the manifest
    worlds = {}
    for vid in demos:
        p = L.planned_world(vid)
        st = L.status(out / "recordings", p)
        idx = rec_list["worlds"].get(vid) or {}
        files = {e["id"]: e.get("file") for e in idx.get("recordings") or []}
        ast = L.atlas_status(out / "recordings", p)
        afiles = {e["id"]: e.get("file") for e in idx.get("atlases") or []}
        worlds[vid] = {"version": p["version"], "code_hash": p["code_hash"], "key": p["key"],
                       "recordings": {r["id"]: {"key": r["key"], "state": st[r["id"]], "file": files.get(r["id"])}
                                      for r in p["recordings"]},
                       "atlases": {a["id"]: {"key": a["key"], "state": ast[a["id"]], "file": afiles.get(a["id"])}
                                   for a in p["atlases"]}}
    for vid in ids:
        if vid not in worlds:
            worlds[vid] = {"version": registry.load(vid).get("version", ""), "recordings": {}}
    files = {}
    for f in sorted(out.rglob("*")):
        if f.is_file():
            rel = f.relative_to(out).as_posix()
            files[rel] = {"bytes": f.stat().st_size, "sha256": L.sha256_file(f)}
    manifest = {"base": base, "built": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                "version": __version__, "recorder": L.RECORDER_VERSION, "cite": registry.citation(),
                "languages": list(i18n.LANGS), "pages": list(pages()) + ["404.html"], "worlds": worlds,
                "files": files}
    _dump(out / "site-manifest.json", manifest)
    total = sum(v["bytes"] for v in files.values())
    n_rec = sum(1 for w in worlds.values() for r in w["recordings"].values() if r["state"] == "present")
    n_all = sum(len(w["recordings"]) for w in worlds.values())
    n_at = sum(1 for w in worlds.values() for a in (w.get("atlases") or {}).values() if a["state"] == "present")
    n_at_all = sum(len(w.get("atlases") or {}) for w in worlds.values())
    print(f"site: {len(files)} files, {total / L.MB:.1f} MB, {n_rec} of {n_all} recordings and {n_at} of {n_at_all} "
          f"atlases present, base {base}")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the static public site (design §5.1).")
    ap.add_argument("--recordings", default=None, help="the recordings folder (DIR/<world>/ or DIR/rec-<world>/)")
    ap.add_argument("--out", required=True, help="the site's folder (created; emptied when it is a site already)")
    ap.add_argument("--base", default="/lfphys/", help="the path the site is served at (default /lfphys/)")
    a = ap.parse_args(argv)
    build(Path(a.recordings) if a.recordings else None, Path(a.out), a.base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
