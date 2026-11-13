# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The completeness and budget check of a built site (design of the start page §4.3, §5.4). It fails (exit code 1) when

* a world or a recording of the registry is missing from ``site-manifest.json``, or its key differs from the one the
  registry gives now (stale), or its state is not ``present``;
* a file named in the manifest or in a recordings index is missing, or its size or sha256 differs;
* a page (``index.html``, ``run.html``, ``legal.html``) lacks ``lf-mode=static``, ``lf-base`` equal to the base, or the
  import map with ``"/static/"`` and ``"/viz/"`` mapped relative; ``404.html`` lacks its metas; a page has an absolute
  ``/static``, ``/api`` or ``/viz`` address outside the import map;
* a catalogue file (``api/viz.json``, ``api/viz/<id>.json``, ``api/planned.json``, ``api/audiences.json``,
  ``api/recordings.json``, ``api/health.json``, ``aliases.json``) or ``static/locales/<lang>.json`` of a language of ``LANGUAGES.md`` is missing;
* a budget's hard limit is exceeded (one recording 10 MB, one world 25 MB, one poster 400 kB, the site 900 MB); over a
  target (3 MB, 12 MB, 150 kB, 600 MB) it warns; the recordings accepted over their target (``sitelib.ACCEPTED``) are
  warned as "over target (accepted: <reason>)".

    python3 site/check.py SITE [--base /lfphys/] [--allow-missing]

``--allow-missing`` turns a missing or stale recording into a warning (a local build before everything is recorded).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitelib as L  # noqa: E402

from lfviz import registry  # noqa: E402

PAGES = ("index.html", "run.html", "legal.html")
IMPORTMAP = re.compile(r'<script\s+type="importmap"\s*>(.*?)</script>', re.S)
#: an absolute address of the server's kind in a page: an attribute value or a string literal starting with it
ABSOLUTE = re.compile(r"""(?:=|\(|\s)\s*["'`](/(?:static|api|viz)(?:/|["'`?]))""")


def languages() -> list[str]:
    """The codes of ``LANGUAGES.md``'s table."""
    text = (L.REPO / "LANGUAGES.md").read_text(encoding="utf-8")
    return re.findall(r"^\|\s*`([a-z]{2,3})`\s*\|", text, re.M)


def absolute_paths(html: str) -> list[str]:
    """The absolute ``/static``, ``/api``, ``/viz`` addresses of a page outside its import map."""
    body = IMPORTMAP.sub("", html)
    return sorted({m.group(1) for m in ABSOLUTE.finditer(body)})


class Report:
    def __init__(self):
        self.fails, self.warns = [], []

    def fail(self, msg):
        self.fails.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


def check_pages(site: Path, base: str, rep: Report):
    for name in PAGES + ("404.html",):
        f = site / name
        if not f.is_file():
            rep.fail(f"page {name} is missing")
            continue
        html = f.read_text(encoding="utf-8")
        if not re.search(r'<meta\s+name="lf-mode"\s+content="static"', html):
            rep.fail(f"{name}: no <meta name=\"lf-mode\" content=\"static\">")
        if not re.search(r'<meta\s+name="lf-base"\s+content="%s"' % re.escape(base), html):
            rep.fail(f"{name}: no <meta name=\"lf-base\" content=\"{base}\">")
        if name == "404.html":
            continue
        maps = IMPORTMAP.findall(html)
        if len(maps) != 1:
            rep.fail(f"{name}: {len(maps)} import maps (one is needed)")
        else:
            try:
                imp = json.loads(maps[0]).get("imports", {})
            except ValueError:
                imp = {}
                rep.fail(f"{name}: the import map is not JSON")
            for key, want in (("/static/", "./static/"), ("/viz/", "./viz/")):
                if imp.get(key) != want:
                    rep.fail(f"{name}: the import map maps {key!r} to {imp.get(key)!r}, not {want!r}")
            for k, v in imp.items():
                if isinstance(v, str) and v.startswith("/"):
                    rep.fail(f"{name}: the import map's {k!r} points to an absolute {v!r}")
                elif isinstance(v, str) and v.startswith("./") and not (site / v[2:]).exists() and not v.endswith("/"):
                    rep.fail(f"{name}: the import map's {k!r} -> {v!r} is not in the site")
        bad = absolute_paths(html)
        if bad:
            rep.fail(f"{name}: absolute addresses outside the import map: {bad}")


def check_files(site: Path, man: dict, rep: Report):
    for rel, info in (man.get("files") or {}).items():
        f = site / rel
        if not f.is_file():
            rep.fail(f"{rel}: in the manifest, missing")
        elif f.stat().st_size != info.get("bytes") or L.sha256_file(f) != info.get("sha256"):
            rep.fail(f"{rel}: differs from the manifest (size or sha256)")
    need = ["api/viz.json", "api/planned.json", "api/audiences.json", "api/recordings.json", "api/health.json",
            "aliases.json"]
    need += [f"api/viz/{vid}.json" for vid in registry.viz_ids()]
    need += [f"static/locales/{code}.json" for code in languages()]
    for rel in need:
        if not (site / rel).is_file():
            rep.fail(f"{rel} is missing")


def check_recordings(site: Path, man: dict, rep: Report, allow_missing: bool):
    file_t, file_l = L.BUDGET["file"]
    world_t, world_l = L.BUDGET["world"]
    mworlds = man.get("worlds") or {}
    for vid in L.demo_worlds():
        plan = L.planned_world(vid)
        mw = mworlds.get(vid)
        if mw is None:
            rep.fail(f"{vid}: not in the site's manifest")
            continue
        idx = L.read_index(site / "recordings", vid) or {}
        entries = {e.get("id"): e for e in idx.get("recordings") or []}
        total = 0
        for r in plan["recordings"]:
            m = (mw.get("recordings") or {}).get(r["id"])
            e = entries.get(r["id"])
            say = rep.warn if allow_missing else rep.fail
            if m is None or e is None:
                say(f"{vid}/{r['id']}: missing")
                continue
            if m.get("key") != r["key"] or e.get("key") != r["key"]:
                say(f"{vid}/{r['id']}: stale (key {e.get('key')}, the registry gives {r['key']})")
            f = site / "recordings" / vid / str(e.get("file"))
            if not f.is_file():
                rep.fail(f"{vid}/{r['id']}: its file {e.get('file')} is missing")
                continue
            if L.sha256_file(f) != e.get("sha256") or f.stat().st_size != e.get("bytes_gz"):
                rep.fail(f"{vid}/{r['id']}: {e.get('file')} differs from its index (sha256 or size)")
            n = f.stat().st_size
            total += n
            if n > file_l:
                rep.fail(f"{vid}/{r['id']}: {n / L.MB:.2f} MB is over the hard limit {file_l / L.MB:.0f} MB")
            elif n > file_t:
                why = L.accepted(vid, r["id"])
                rep.warn(f"{vid}/{r['id']}: {n / L.MB:.2f} MB is over the target {file_t / L.MB:.0f} MB"
                         + (f" (accepted: {why})" if why else ""))
        if total > world_l:
            rep.fail(f"{vid}: {total / L.MB:.2f} MB is over the world's hard limit {world_l / L.MB:.0f} MB")
        elif total > world_t:
            why = L.accepted(vid)
            rep.warn(f"{vid}: {total / L.MB:.2f} MB is over the world's target {world_t / L.MB:.0f} MB"
                     + (f" (accepted: {why})" if why else ""))


def check_budgets(site: Path, rep: Report):
    pic_t, pic_l = L.BUDGET["poster"]
    for f in sorted((site / "images").glob("*.jpg")) if (site / "images").is_dir() else []:
        n = f.stat().st_size
        if n > pic_l:
            rep.fail(f"images/{f.name}: {n / 1e3:.0f} kB is over the hard limit {pic_l / 1e3:.0f} kB")
        elif n > pic_t:
            rep.warn(f"images/{f.name}: {n / 1e3:.0f} kB is over the target {pic_t / 1e3:.0f} kB")
    site_t, site_l = L.BUDGET["site"]
    total = sum(f.stat().st_size for f in site.rglob("*") if f.is_file())
    if total > site_l:
        rep.fail(f"the site: {total / L.MB:.0f} MB is over the hard limit {site_l / L.MB:.0f} MB")
    elif total > site_t:
        rep.warn(f"the site: {total / L.MB:.0f} MB is over the target {site_t / L.MB:.0f} MB")
    return total


def check(site: Path, base: str = "/lfphys/", allow_missing: bool = False) -> Report:
    rep = Report()
    mf = site / "site-manifest.json"
    if not mf.is_file():
        rep.fail("site-manifest.json is missing")
        return rep
    man = json.loads(mf.read_text(encoding="utf-8"))
    if man.get("base") != base:
        rep.fail(f"the site was built for the base {man.get('base')!r}, not {base!r}")
    check_pages(site, base, rep)
    check_files(site, man, rep)
    check_recordings(site, man, rep, allow_missing)
    rep.total = check_budgets(site, rep)
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check a built site: completeness and budgets (design §5.4).")
    ap.add_argument("site", help="the site's folder")
    ap.add_argument("--base", default="/lfphys/")
    ap.add_argument("--allow-missing", action="store_true", help="a missing or stale recording only warns")
    a = ap.parse_args(argv)
    rep = check(Path(a.site), a.base, a.allow_missing)
    for w in rep.warns:
        print(f"WARN {w}")
    for f in rep.fails:
        print(f"FAIL {f}")
    print(f"# {len(rep.fails)} failures, {len(rep.warns)} warnings; the site is "
          f"{getattr(rep, 'total', 0) / L.MB:.1f} MB")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())
