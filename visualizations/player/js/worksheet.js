// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// A lab's worksheet (worksheet.html?demo=<world>[&teacher=1]; /worksheet?demo=… on a server; design
// lfphys/sources/explore_2026-11-14_design.md §2.3, §10 question 2): data, not a separate document. The ФРП lab's name
// verbatim in Russian (in another language: its translation, marked so, with the Russian original); the goal and the
// parts from the lab's steps (the instruments with their divisions and errors, a blank table of the step's columns, the
// axes of its plot, the law to compare with); the equipment; the questions. «For the teacher» shows the answers, the
// teacher's notes and the laws' references (computed by the world when its atlases were built) on a page of their own.
// Printable: one A4 page per part. Every text is a T of the world's registry entry, in the viewer's language.
import { apiGet, getJSON, page, url } from "./api.js";
import { lang, t, withLang } from "./i18n.js";
import { el, fill, fmt, initTheme, toggleTheme } from "./ui.js";

initTheme();
document.getElementById("theme").onclick = toggleTheme;
const Q = new URLSearchParams(location.search);
const box = document.getElementById("ws");
// the worksheet's texts are Site Materials under CC BY-NC-SA 4.0 (LICENSE.md §1 item 8, §9): every printed page carries
// the creator's line and the notices that licence asks a reuser to keep (§3(a)(1)(A))
const CREDIT_LINE = "lfphys — Ildar Idrisov — https://ildar-idrisov.github.io/lfphys/";
const CC_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/";
const credit = () => el("p", { class: "credit" }, t("{line} · © 2026 Ildar Idrisov · the texts of this worksheet: CC BY-NC-SA 4.0 ({cc}) · provided as is, without warranty · mark your changes and share changed copies under the same licence", { line: CREDIT_LINE, cc: CC_URL }));

async function main() {
  const id = Q.get("demo");
  let viz;
  try { viz = await apiGet(`viz/${encodeURIComponent(id || "")}`); } catch (e) { fill(box, el("p", {}, t("No such demonstration"))); return; }
  const lab = (viz.screens || []).find((s) => s.kind === "lab");
  if (!lab) { fill(box, el("p", {}, t("This demonstration has no lab work."))); return; }
  document.title = t("Worksheet: {title}", { title: t(viz.title) });
  const ws = lab.worksheet || {};
  // the ФРП names verbatim in Russian: in another language, the Russian original next to the translation
  let ru = null;
  if (lang() !== "ru" && (ws.frp || []).length) {
    try { ru = (await getJSON(url("static/locales/ru.json"))).messages || null; } catch (e) { ru = null; }
  }
  // the laws' references, from the steps' atlases (when they are built)
  const refs = {};
  try {
    const rec = await apiGet("recordings");
    const ix = (rec.worlds || {})[viz.id];
    for (const a of (ix && ix.atlases) || []) {
      if (!a.step) continue;
      try { Object.assign(refs, (await getJSON(url(`recordings/${viz.id}/${a.file}`))).references || {}); } catch (e) { /* not built: none */ }
    }
  } catch (e) { /* no recordings: no references */ }
  const teacher = el("input", { type: "checkbox", checked: Q.get("teacher") === "1", onchange: () => setTeacher(teacher.checked) });
  const setTeacher = (on) => {
    document.body.classList.toggle("teacher-on", on);
    const u = new URL(location.href);
    if (on) u.searchParams.set("teacher", "1"); else u.searchParams.delete("teacher");
    history.replaceState(null, "", u.href);
  };
  setTeacher(teacher.checked);
  const instr = lab.instruments || {};
  const parts = (lab.steps || []).map((st, k) => el("section", { class: "part" + (k === 0 ? " first" : "") },
    k === 0 ? head(viz, ws, ru) : null,
    el("h2", {}, t("Part {k:d} of {n:d}: {title}", { k: k + 1, n: lab.steps.length, title: t(st.title) })),
    el("p", {}, el("b", {}, t("Goal:")), " ", t(st.goal)),
    el("h3", {}, t("Instruments")),
    el("ul", {}, st.instruments.map((iid) => instr[iid] ? el("li", {}, el("b", {}, t(instr[iid].label)), " — ",
      t("division {d} {unit}, error ±{e} {unit}", { d: fmt(instr[iid].division, ".6g"), e: fmt(instr[iid].error, ".6g"), unit: t(instr[iid].unit) }),
      instr[iid].error_note ? ` (${t(instr[iid].error_note)})` : "") : null)),
    el("h3", {}, t("Measurements")),
    el("table", { class: "blank" }, el("tr", {}, el("th", {}, "№"), st.columns.map((c) => el("th", {}, t(c.label)))),
      Array.from({ length: 8 }, (_, i) => el("tr", {}, el("td", {}, String(i + 1)), st.columns.map(() => el("td", {}))))),
    el("h3", {}, t("Plot")),
    el("p", {}, t("Plot {y} against {x} and draw the best line through the points with their error bars.", {
      y: t((st.columns.find((c) => c.id === st.plot.y) || {}).label || st.plot.y), x: t((st.columns.find((c) => c.id === st.plot.x) || {}).label || st.plot.x) })),
    el("div", { class: "axes" }),
    st.law ? el("p", {}, el("b", {}, t("The law:")), " ", t("find {label} from the plot and compare it with the law.", { label: t(st.law.label) })) : null,
    k === lab.steps.length - 1 ? questions(ws) : null,
    credit()));
  const tAns = el("section", { class: "teacher" },
    el("h2", {}, t("For the teacher")),
    (ws.questions || []).length ? el("ol", {}, ws.questions.map((q) => el("li", {}, el("div", {}, t(q.q)), el("div", { class: "answer" }, t(q.answer))))) : null,
    (ws.teacher || []).length ? [el("h3", {}, t("Notes")), el("ul", {}, ws.teacher.map((x) => el("li", {}, t(x))))] : null,
    Object.keys(refs).length ? [el("h3", {}, t("The laws' references (computed by the world when the site was built)")),
      el("ul", {}, (lab.steps || []).filter((st) => st.law && refs[st.law.reference]).map((st) => {
        const r = refs[st.law.reference];
        return el("li", {}, `${t(st.title)}: ${t(st.law.label)} = ${fmt(r.value, ".4g")} ${r.unit || st.law.unit || ""} — ${t(r.label)} (${t(r.how)})`);
      }))] : null,
    credit());
  fill(box,
    el("div", { class: "ws-tools" },
      el("a", { href: withLang(page("run", { demo: viz.id, screen: lab.id })) }, t("← Back to the lab work")),
      el("label", { title: t("The answers and the teacher's notes print on a page of their own") }, teacher, t("For the teacher")),
      el("button", { class: "primary", onclick: () => window.print() }, t("🖨 Print"))),
    parts, tAns);
  document.body.dataset.ready = "1";
}

function head(viz, ws, ru) {
  return [  // flat: el() flattens one level of its children
    el("h1", {}, t(viz.title)),
    (ws.frp || []).map((f) => el("div", { class: "frp" }, `${f.system}${f.grade ? ", " + t("grade {n:d}", { n: f.grade }) : ""}: `,
      el("b", {}, t(f.name)),
      ru && f.name && f.name.$t && ru[f.name.$t] ? el("span", {}, " ", t("(translated; the programme's own wording: «{orig}»)", { orig: ru[f.name.$t] })) : null)),
    (ws.equipment || []).length ? [el("h3", {}, t("Equipment")), el("ul", {}, ws.equipment.map((x) => el("li", {}, t(x))))] : null,
    el("p", { class: "note" }, t("Each reading is rounded to the instrument's division; its error is the declared one (by default half a division).")),
    el("p", { class: "note" }, t("The experiment is done on the computed bench of this demonstration: the engine computed every set-up in advance.")),
  ].flat(2);
}
function questions(ws) {
  if (!(ws.questions || []).length) return null;
  return [el("h2", {}, t("Questions")), el("ol", {}, ws.questions.map((q) => el("li", {}, t(q.q), el("div", { class: "lines" }), el("div", { class: "lines" }))))];
}

main().catch((e) => { console.error(e); fill(box, el("p", {}, String(e.message || e))); });
