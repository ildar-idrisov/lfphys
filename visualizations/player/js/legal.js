// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The licence page (/legal): the full texts served by the server (GET /legal/<name>), the third-party notices among
// them, so a viewer of the player gets them with the code the browser loads (review of 2026-10-29, R4 and R8).
import { el, initTheme, toggleTheme } from "./ui.js";

initTheme();
document.getElementById("theme").onclick = toggleTheme;

const TEXTS = [
  ["LICENSE.md", "Лицензия кода: lfphys Research Licence 1.0", true],
  ["NOTICE", "Уведомления (NOTICE), включая сторонний код", true],
  ["PUBLICATIONS.md", "Результаты и публикации: цитирование, дополнительные разрешения", false],
  ["COMMERCIAL.md", "Коммерческое использование: как запросить", false],
  ["three.js-LICENSE", "three.js r185.1 — лицензия MIT", false],
  ["LICENSE-DOCS.txt", "Лицензия документации: CC BY-NC-SA 4.0", false],
];

// what a publication cites: the version and this copy's code identifier (lfphys Research Licence §5)
fetch("/api/health").then((r) => r.json()).then((h) => {
  if (h.cite) document.getElementById("cite").textContent = h.cite.text;
}).catch(() => { document.getElementById("cite").textContent = "версия — в CITATION.cff"; });

const box = document.getElementById("texts");
for (const [name, label, open] of TEXTS) {
  const pre = el("pre", {}, "загрузка…");
  box.append(el("details", open ? { open: "" } : {}, el("summary", {}, label), pre));
  fetch(`/legal/${encodeURIComponent(name)}`)
    .then((r) => (r.ok ? r.text() : Promise.reject(new Error(r.statusText))))
    .then((t) => { pre.textContent = t; })
    .catch((e) => { pre.textContent = `не удалось загрузить: ${e.message}`; });
}
