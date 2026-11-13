// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The licence page (/legal; legal.html on the public site): a summary in the viewer's language and the full texts
// (url("legal/<name>"): the server's GET /legal/<name>, the site's copies; in English), the third-party notices among them, so a viewer of the player gets them with the code the
// browser loads (review of 2026-10-29, R4 and R8). The summary's texts carry inline markup: they are msgids whose
// translations keep the same tags.
import { apiGet, url } from "./api.js";
import { t } from "./i18n.js";
import { el, initTheme, toggleTheme } from "./ui.js";

initTheme();
document.getElementById("theme").onclick = toggleTheme;

const html = (tag, text) => { const e = el(tag); e.innerHTML = text; return e; };  // our own catalogue's markup

document.getElementById("legal").append(
  el("h2", {}, t("A research tool — without warranty")),
  el("p", {}, t("The lfphys engine and the visualizations are research tools. Their models, implementation, numerical methods and results may contain errors. The checks next to the results and the engine's tests confirm the stated cases within the stated bounds, not that any given problem is solved correctly. Before relying on a result, check the input, the model's applicability, the convergence and the result itself. The software is provided “as is”, without any warranty; support and fixes are not promised (section 8 of the licence).")),
  el("h2", {}, t("The terms in brief")),
  el("ul", {},
    html("li", t("<b>The code</b> (the engine, the server, the player, the visualizations) — lfphys Research Licence 1.0: noncommercial research, study and teaching only. The source code is open to read (source-available), but it is not open source.")),
    html("li", t("<b>Commercial use</b> by anyone — a company, a university or institute working for a company, a private person — only under a separate written agreement with the author (idrisov.sci@gmail.com).")),
    html("li", t("<b>Your results</b> (the numbers, data, figures and snapshots of your runs) are yours. If the software computed, modelled, drew or checked something your publication reports, <b>citing it is required</b>: the author (Ildar Idrisov), the name (lfphys), the version and the code of this build — <span id=\"cite\" class=\"mono\">…</span>. Snapshots of your runs and short excerpts of the code may be published anywhere, including under CC BY, with the credit “Ildar Idrisov, lfphys &lt;version&gt;”. Results may not be presented as verified or endorsed by the author. Selling data sets made mainly of the software's results requires an agreement.")),
    html("li", t("<b>The author's documentation and figures</b> — CC BY-NC-SA 4.0; figures and short quotations may be published in scholarly works, including those from commercial publishers, with the author and the version credited.")),
    html("li", t("<b>Access over a network</b>: whoever lets people use a copy of the software over a network must show them this page.")),
    html("li", t("<b>Third-party code</b>: three.js r185.1 (MIT licence) — the player's 3-D scene; the terms above do not apply to it."))),
  el("p", { class: "muted" }, t("This is a summary; the full texts below (in English) are binding.")),
  el("h2", {}, t("Full texts")),
  el("div", { id: "texts" }));

const TEXTS = [
  ["LICENSE.md", t("Licence of the code: lfphys Research Licence 1.0"), true],
  ["NOTICE", t("Notices (NOTICE), including third-party code"), true],
  ["PUBLICATIONS.md", t("Results and publications: citation, additional permissions"), false],
  ["COMMERCIAL.md", t("Commercial use: how to ask"), false],
  ["three.js-LICENSE", t("three.js r185.1 — MIT licence"), false],
  ["LICENSE-DOCS.txt", t("Licence of the documentation: CC BY-NC-SA 4.0"), false],
];

// what a publication cites: the version and this copy's code identifier (lfphys Research Licence §5)
apiGet("health").then((h) => {
  if (h.cite) document.getElementById("cite").textContent = h.cite.text;
}).catch(() => { document.getElementById("cite").textContent = t("the version is in CITATION.cff"); });

const box = document.getElementById("texts");
for (const [name, label, open] of TEXTS) {
  const pre = el("pre", {}, t("loading…"));
  box.append(el("details", open ? { open: "" } : {}, el("summary", {}, label), pre));
  fetch(url(`legal/${encodeURIComponent(name)}`))
    .then((r) => (r.ok ? r.text() : Promise.reject(new Error(r.statusText))))
    .then((text) => { pre.textContent = text; })
    .catch((e) => { pre.textContent = t("could not load: {why}", { why: e.message }); });
}
