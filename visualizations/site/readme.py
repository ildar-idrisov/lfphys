# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The catalogue sections of the root READMEs, generated from the registry in every language of ``LANGUAGES.md``
(design of the start page §5.3; ``AGENTS.md`` §3 rules 13, 14).

    python3 site/readme.py            rewrite the generated sections of README.md, README.ru.md, README.<code>.md
    python3 site/readme.py --check    exit 1 when a README differs from what the registry gives (or lacks the markers)
    python3 site/readme.py --print ru print one language's section

Between the markers ``BEGIN`` and ``END`` below (the rest of each README is written by hand and kept as it is): the four
audiences in their order, each with its one line; the school audience with the honest count of what is ready and the
planned items by section (each with its grades and the worlds of another level on the same topic); the university and
research audiences by section in teaching order with their counts, one row per world: its picture
(``docs/images/<id>.jpg``, when there is one), its title linked to its README in the language, its teaser, its anchors
(the courses; the research question with «Status: hypothesis» and the prior art), «Watch on the site» (one link per
recording, ``<site>run.html?rec=<world>/<rec>``), the count of scenarios in the player and «Same topic at other levels»;
the planned university and research items folded after their worlds, by section; the laboratories with «Runs only
with a local server» and the planned benches. Every world is in exactly one audience.
Every text is the registry's ``T`` rendered in the language (``lfviz.i18n.render_in``): the interface's own words.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitelib as L  # noqa: E402

from lfviz import i18n, registry  # noqa: E402
from lfviz.app import SITE_URL, planned_list  # noqa: E402
from lfviz.i18n import T, is_t  # noqa: E402

BEGIN = "<!-- BEGIN generated: catalogue (visualizations/site/readme.py); do not edit -->"
END = "<!-- END generated -->"

READY = T("Ready: {n} of {total}")
PLANNED_BY_SECTION = T("Planned demonstrations, by section")
GRADES = T("grades {grades}")
NEXT = T("next in the plan")
ELSEWHERE = T("Already there at another level:")
COURSES = T("Courses")
CHAPTERS = T("{book}, ch. {chapters}")
QUESTION = T("Question")
HYPOTHESIS = T("Status: hypothesis")
PRIOR_ART = T("Prior art")
WATCH = T("Watch on the site")
SAME_TOPIC = T("Same topic at other levels")
SCENARIOS = T("Scenarios in the player: {n}")
LOCAL_ONLY = T("Runs only with a local server")
QUICK_START = T("Quick start")
BENCHES = T("Planned benches")
PLANNED_AT = T("{audience}, planned")
MODIFIED = T("modified physics")
N_PLANNED = T("{n:d} planned")
HYPOTHESIS_SHORT = T("hypothesis")


def readme_files() -> dict[str, Path]:
    """{language: its root README}: README.md for the default language, README.<code>.md for the others."""
    return {lang: L.REPO / ("README.md" if lang == i18n.DEFAULT else f"README.{lang}.md") for lang in i18n.LANGS}


def _md(s: str) -> str:
    """A text for a Markdown table cell: no pipe, no tag, no line break."""
    return s.replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")


def _slug(heading: str) -> str:
    """GitHub's anchor of a heading."""
    s = re.sub(r"[^\w\- ]", "", heading.strip().lower(), flags=re.U)
    return s.replace(" ", "-")


class Gen:
    def __init__(self, lang: str):
        self.lang = lang
        self.ids = registry.viz_ids()
        self.viz = {vid: registry.load(vid) for vid in self.ids}
        self.planned = {p["id"]: p for p in planned_list()}

    def r(self, text, **kw) -> str:
        """A text in the language (a ``T``, a plain English string of the registry, or a msgid with arguments)."""
        if kw:
            text = T(text["$t"], **{**(text.get("a") or {}), **kw}) if is_t(text) else T(text, **kw)
        elif isinstance(text, str):
            text = T(text)
        return i18n.render_in(text, self.lang)

    def readme_of(self, vid: str) -> str:
        own = registry.folder(vid) / f"README.{self.lang}.md"
        name = own.name if self.lang != i18n.DEFAULT and own.is_file() else "README.md"
        return f"visualizations/{vid}/{name}"

    def short(self, vid: str) -> str:
        return vid.split("_", 1)[0]

    def link(self, vid: str) -> str:
        return f"[{self.short(vid)} · {_md(self.r(self.viz[vid]['title']))}]({self.readme_of(vid)})"

    def aud_label(self, aud: str) -> str:
        return self.r(registry.AUDIENCE[aud]["label"])

    def related(self, ids) -> list[str]:
        out = []
        for x in ids:
            if x in self.viz:
                out.append(f"{self.link(x)} ({self.aud_label(self.viz[x]['audience'])})")
            elif x in self.planned:
                p = self.planned[x]
                out.append(f"{x} · {_md(self.r(p['title']))} "
                           f"({_md(self.r(PLANNED_AT, audience=registry.AUDIENCE[p['audience']]['label']))})")
        return out

    def modified(self, vid: str, preset: str) -> bool:
        schema = self.viz[vid]["schema"]
        params, _ = schema.resolve(preset, {})
        try:
            return bool(schema.modifications(params))
        except Exception:  # noqa: BLE001 - a schema without the method: no flag
            return False

    def picture(self, vid: str) -> str:
        pic = registry.picture(vid)
        if not pic:
            return ""
        alt = _md(f"{self.short(vid)}: {self.r(self.viz[vid]['title'])}").replace('"', "&quot;")
        return f'<a href="{pic}"><img src="{pic}" width="300" alt="{alt}"></a>'

    def row(self, vid: str) -> str:
        v = self.viz[vid]
        lines = [f"**{self.link(vid)}**", _md(self.r(v["teaser"]))]
        aud = v["audience"]
        if aud == "university" and v.get("courses"):
            books = []
            for c in v["courses"]:
                book = self.r(c["text"])
                books.append(self.r(CHAPTERS, book=book, chapters=c["chapters"]) if c.get("chapters") else book)
            lines.append(f"*{self.r(COURSES)}:* {_md('; '.join(books))}")
        if aud == "research":
            lines.append(f"*{self.r(QUESTION)}:* {_md(self.r(v['question']))} · **{self.r(HYPOTHESIS)}**")
            refs = [f"[{_md(p['ref'])}]({p['url']})" if p.get("url") else _md(p["ref"]) for p in v.get("prior_art") or []]
            if refs:
                lines.append(f"*{self.r(PRIOR_ART)}:* " + "; ".join(refs))
        recs = registry.recordings_of(v)
        if recs:
            links = []
            for rec in recs:
                label = _md(self.r(rec["label"]))
                if self.modified(vid, rec["preset"]):
                    label += f" *({self.r(MODIFIED)})*"
                links.append(f"[{label}]({SITE_URL}run.html?rec={vid}/{rec['id']})")
            lines.append(f"▷ {self.r(WATCH)}: " + " · ".join(links))
        n = len(getattr(v["schema"], "presets", {}) or {})
        if n:
            lines.append(_md(self.r(SCENARIOS, n=n)))
        rel = self.related(v.get("related") or [])
        if rel:
            lines.append(f"{self.r(SAME_TOPIC)}: " + "; ".join(rel))
        return f"| {self.picture(vid)} | " + "<br>".join(lines) + " |"

    def sections(self, aud: str) -> list[str]:
        out = []
        worlds = [vid for vid in self.ids if self.viz[vid]["audience"] == aud]
        for sec in registry.SECTIONS:
            here = [vid for vid in worlds if self.viz[vid]["section"] == sec["id"]]
            if not here:
                continue
            out += [f"**{self.r(sec['label'])}** · {len(here)}", "", "| | |", "|---|---|"]
            out += [self.row(vid) for vid in here] + [""]
        return out

    def school(self) -> list[str]:
        worlds = [vid for vid in self.ids if self.viz[vid]["audience"] == "school"]
        items = [p for p in json.loads((L.VIZ / "planned.json").read_text(encoding="utf-8"))
                 if p["audience"] == "school"]
        out = [f"**{self.r(READY, n=len(worlds), total=len(items))}**", ""]
        out += self.sections("school")
        todo = [p for p in items if p["id"] in self.planned]
        if not todo:
            return out
        out += [f"*{self.r(PLANNED_BY_SECTION)}:*", ""]
        return out + self.planned_by_section(todo)

    def planned_by_section(self, todo: list[dict]) -> list[str]:
        """The planned items by section in teaching order: one line each with its grades (school), «hypothesis»
        (research), «next in the plan», and the worlds of another level on the same topic."""
        back = {}  # planned id -> worlds of another level that name it
        for vid, v in self.viz.items():
            for x in v.get("related") or []:
                back.setdefault(x, []).append(vid)
        out = []
        for sec in registry.SECTIONS:
            here = [p for p in todo if p["section"] == sec["id"]]
            if not here:
                continue
            out += [f"**{self.r(sec['label'])}** · {len(here)}", ""]
            for p in here:
                s = f"* {p['id']} · {_md(self.r(p['title']))}"
                if p.get("grades"):
                    s += f" ({self.r(GRADES, grades=', '.join(str(g) for g in p['grades']))})"
                if p.get("status") == "hypothesis":
                    s += f" · *{self.r(HYPOTHESIS_SHORT)}*"
                if p.get("state") == "next":
                    s += f" · *{self.r(NEXT)}*"
                there = [x for x in dict.fromkeys(list(p.get("related") or []) + back.get(p["id"], []))
                         if x in self.viz]
                if there:
                    s += f". {self.r(ELSEWHERE)} " + "; ".join(self.related(there))
                out.append(s)
            out.append("")
        return out

    def planned_folded(self, aud: str) -> list[str]:
        """University and research: their planned items after the worlds, folded (as the site folds them)."""
        todo = [p for p in self.planned.values() if p["audience"] == aud]
        if not todo:
            return []
        return (["<details>", f"<summary>{_md(self.r(N_PLANNED, n=len(todo)))}</summary>", ""]
                + self.planned_by_section(todo) + ["</details>", ""])

    def labs(self) -> list[str]:
        anchor = _slug(self.r(QUICK_START))
        out = [f"*{self.r(LOCAL_ONLY)}* ([{self.r(QUICK_START)}](#{anchor})).", ""]
        out += self.sections("playground")
        benches = [p for p in self.planned.values() if p["audience"] == "playground"]
        if benches:
            out += [f"*{self.r(BENCHES)}:*", ""]
            for p in benches:
                s = f"* {p['id']} · {_md(self.r(p['title']))}"
                if p.get("text"):
                    s += f": {_md(self.r(p['text']))}"
                out.append(s)
            out.append("")
        return out

    def block(self) -> str:
        out = [BEGIN, ""]
        for a in registry.AUDIENCES:
            out += [f"### {self.r(a['label'])}", "", self.r(a["text"]) + ".", ""]
            if a["id"] == "school":
                out += self.school()
            elif a["id"] == "playground":
                out += self.labs()
            else:
                out += self.sections(a["id"]) + self.planned_folded(a["id"])
        while out and out[-1] == "":
            out.pop()
        return "\n".join(out + ["", END])


def generate(lang: str) -> str:
    return Gen(lang).block()


def apply(text: str, block: str, name: str = "README") -> str:
    """The README with its generated section replaced (ValueError when the markers are not there once each)."""
    if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(BEGIN) > text.index(END):
        raise ValueError(f"{name}: the markers {BEGIN!r} … {END!r} must appear once each, in this order")
    i, j = text.index(BEGIN), text.index(END) + len(END)
    return text[:i] + block + text[j:]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="The READMEs' catalogue sections from the registry (design §5.3).")
    ap.add_argument("--check", action="store_true", help="fail when a README differs from the registry")
    ap.add_argument("--print", metavar="LANG", help="print one language's generated section")
    a = ap.parse_args(argv)
    if a.print:
        print(generate(a.print))
        return 0
    bad = []
    for lang, f in readme_files().items():
        if not f.is_file():
            bad.append(f"{f.name}: missing (LANGUAGES.md lists {lang})")
            continue
        text = f.read_text(encoding="utf-8")
        try:
            new = apply(text, generate(lang), f.name)
        except ValueError as e:
            bad.append(str(e))
            continue
        if new != text:
            if a.check:
                bad.append(f"{f.name}: the generated section differs from the registry (run site/readme.py)")
            else:
                f.write_text(new, encoding="utf-8")
                print(f"{f.name}: written")
    for b in bad:
        print(b, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
