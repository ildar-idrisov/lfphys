// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// A lab's worksheet (worksheet.html?demo=<world>[&teacher=1]; /worksheet?demo=… on a server; design
// lfphys/sources/explore_2026-11-14_design.md §2.3, §10 question 2): data, not a separate document. The ФРП lab's name
// verbatim in Russian (in another language: its translation, with the Russian original); the goal and the parts from
// the lab's steps (the instruments with their divisions and errors, a blank table with one row per set-up of the step,
// the axes of each law's plot, the laws to compare with, the conclusion's lines); the equipment; the questions. «For the
// teacher» shows the answers, the teacher's notes and the laws' references (computed by the world when its atlases were
// built) on pages of their own. Every text is a T of the world's registry entry, in the viewer's language.
//
// A variant (WORKSHEET["variants"]: {id, grade, label, steps, plot: {step: {x, y, fit | null}}, goals?: {step: T},
// questions: [{q, answer}]}; S03's grade 7, review EX1-worlds F7d) is chosen on the page (&variant=<id>): only its
// steps with its own goals (else the step's), its plots (fit null: the points only, no curve), the measured columns and
// those it plots, its own questions and answers.
//
// Printed, every page is one `.sheet` (review EX1-screens F6, EX1-worlds F7): the head and part 1, then one sheet per
// part, the questions, and the teacher's sheets; each sheet is one A4 page with the attribution line at its foot (the
// licence's condition: every printed page carries it). browser test demo_screens.mjs checks that no sheet overflows its
// page and that the PDF has as many pages as sheets.
import { MODE, apiGet, getJSON, page, url } from "./api.js";
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
// a sheet: one printed page, its attribution line at its foot
const sheet = (cls, ...children) => el("section", { class: "sheet " + cls }, el("div", { class: "sheet-body" }, ...children), credit());

// the programme's name for a reader: the entry's `programme` (a T), never the raw id (review EX1-worlds F7g)
const programmeName = (f) => (f.programme ? t(f.programme) : "");
// a unit after a value («41.9°», «0.6774 m^½»)
const withUnit = (text, unit) => (!unit ? text : unit === "°" ? text + unit : `${text} ${unit}`);
const FIT_CURVE = () => ({ line0: t("the best straight line through the origin"), line: t("the best straight line"),
  quadratic: t("the best parabola"), power: t("the best power-law curve") });
const plotHow = (y, x, model) => (model ? t("Plot {y} against {x}, mark the points with their error bars and draw {curve}.", { y, x, curve: FIT_CURVE()[model] || FIT_CURVE().line })
  : t("Plot {y} against {x}: the points with their error bars, without a line.", { y, x }));

// a step's laws (the registry's `laws`: {x, y, model, quantity, label, unit, reference}; integrator D4)
const lawsOf = (st) => st.laws || [];
// the number of set-ups of a step: one blank row each (review EX1-worlds F7b)
const setups = (st) => (st.controls || []).reduce((n, c) => n * Math.max(1, (c.values || []).length), 1) || 8;

async function main() {
  const id = Q.get("demo");
  let viz;
  try { viz = await apiGet(`viz/${encodeURIComponent(id || "")}`); } catch (e) {  // a world that does not load says why (2026-11-18)
    fill(box, el("p", {}, e.body && e.body.detail ? e.message : t("No such demonstration"))); return;
  }
  const lab = (viz.screens || []).find((s) => s.kind === "lab");
  if (!lab) { fill(box, el("p", {}, t("This demonstration has no lab work."))); return; }
  document.title = t("Worksheet: {title}", { title: t(viz.title) });
  const ws = lab.worksheet || {};
  // the ФРП names verbatim in Russian: in another language, the Russian original next to the translation
  let ru = null;
  if (lang() !== "ru" && (ws.frp || []).length) {
    try { ru = (await getJSON(url("static/locales/ru.json"))).messages || null; } catch (e) { ru = null; }
  }
  // the laws' references, from the steps' atlases when they are built with the current code (the key the server expects;
  // integrator D11): here, or (a server without them) the published site's of the same world version
  const refs = {};
  try {
    const rec = await apiGet("recordings");
    const exp = ((rec.expected || {})[viz.id] || {}).atlases || {};
    const fresh = (a) => a.step && (exp[a.id] === undefined || a.key === exp[a.id]);
    const local = (rec.worlds || {})[viz.id];
    const sources = [[local, url(`recordings/${viz.id}/`)]];
    // the published site is asked only when a step has no current atlas here (as demo.js does), and through its list of
    // every world's index (api/recordings.json, always there on a published site), not the world's own index.json,
    // which a world not yet published lacks: no 404 in the console (review EX1-worlds, QW; integrator D11)
    const hereOk = (st) => ((local && local.atlases) || []).some((a) => a.step === st.id && fresh(a)
      && String(a.version ?? local.version) === String(viz.version));
    if (MODE === "server" && rec.published && rec.site && !(lab.steps || []).every(hereOk)) {
      const siteRec = await getJSON(`${rec.site}api/recordings.json`).catch(() => null);
      sources.push([((siteRec && siteRec.worlds) || {})[viz.id] || null, `${rec.site}recordings/${viz.id}/`]);
    }
    for (const [ix, base] of sources) {
      for (const a of ((ix && ix.atlases) || []).filter(fresh)) {
        if (refs[a.step] || String(a.version ?? ix.version) !== String(viz.version)) continue;
        try { refs[a.step] = (await getJSON(base + a.file)).references || {}; } catch (e) { /* not reachable: none */ }
      }
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
  const variants = ws.variants || [];
  const V = variants.find((v) => v.id === Q.get("variant")) || null;
  const steps = (lab.steps || []).filter((st) => !V || (V.steps || []).includes(st.id));
  const questions = V ? V.questions || [] : ws.questions || [];
  const colLabel = (st, cid) => t((st.columns.find((c) => c.id === cid) || {}).label || cid);
  const parts = steps.map((st, k) => {
    // a variant's plot replaces the laws' (its fit may be none: the points only); its laws apply only when it plots one
    const vp = V && V.plot ? V.plot[st.id] : null;
    const laws = vp ? lawsOf(st).filter((L) => L.x === vp.x && L.y === vp.y && L.model === vp.fit) : lawsOf(st);
    // the plots: one pair of axes per law's (x, y), else the step's default plot
    const plots = [];
    for (const L of vp ? [{ x: vp.x, y: vp.y, model: vp.fit }] : laws.length ? laws : [{ x: st.plot.x, y: st.plot.y, model: st.plot.fit }]) {
      if (!plots.some((p) => p.x === L.x && p.y === L.y)) plots.push({ x: L.x, y: L.y, model: L.model });
    }
    // a variant's table: the measured columns and those it plots (no √h for grade 7)
    const cols = vp ? st.columns.filter((c) => c.from || c.id === vp.x || c.id === vp.y) : st.columns;
    return sheet("part" + (k === 0 ? " first" : ""),
      k === 0 ? head(viz, ws, ru, V) : null,
      el("h2", {}, t("Part {k:d} of {n:d}: {title}", { k: k + 1, n: steps.length, title: t(st.title) })),
      el("p", {}, el("b", {}, t("Goal:")), " ", t((V && V.goals && V.goals[st.id]) || st.goal)),
      el("p", { class: "instr" }, el("b", {}, t("Instruments:")), " ", st.instruments.filter((iid) => instr[iid]).flatMap((iid, j) => [j ? "; " : "",
        el("b", {}, t(instr[iid].label)), " — ", t("division {d}, error ±{e}", { d: withUnit(fmt(instr[iid].division, ".6g"), t(instr[iid].unit)),
          e: withUnit(fmt(instr[iid].error ?? instr[iid].division / 2, ".6g"), t(instr[iid].unit)) }),
        instr[iid].error_note ? ` (${t(instr[iid].error_note)})` : ""])),
      el("div", { class: "mgrid" },
        el("div", {}, el("h3", {}, t("Measurements")),
          el("table", { class: "blank" }, el("tr", {}, el("th", {}, "№"), cols.map((c) => el("th", {}, t(c.label)))),
            Array.from({ length: setups(st) }, (_, i) => el("tr", {}, el("td", {}, String(i + 1)), cols.map(() => el("td", {})))))),
        el("div", {}, el("h3", {}, t("Plot")),
          plots.flatMap((p) => [
            el("p", { class: "plot-how" }, plotHow(colLabel(st, p.y), colLabel(st, p.x), p.model)),
            el("div", { class: "axes" }, el("span", { class: "ax ay" }, colLabel(st, p.y)), el("span", { class: "ax axx" }, colLabel(st, p.x)))]),
          // the laws beside the table, under their plots (the page's room is the table's height)
          laws.length ? [el("h3", {}, laws.length > 1 ? t("The laws") : t("The law")),
            el("ul", { class: "laws" }, laws.map((L) => el("li", {}, el("b", {}, t(L.label)), ": ",
              t("from the plot of {y} against {x}; compare it with the law", { y: colLabel(st, L.y), x: colLabel(st, L.x) }))))] : null)),
      el("p", { class: "concl" }, el("b", {}, t("Conclusion:"))), el("div", { class: "lines" }), el("div", { class: "lines" }));
  });
  const qs = questions.length ? sheet("questions", el("h2", {}, t("Questions")),
    el("ol", {}, questions.map((q) => el("li", {}, t(q.q), el("div", { class: "lines" }), el("div", { class: "lines" }))))) : null;
  // «For the teacher»: the answers on a sheet, the notes and the references on another
  const lawsShown = (st) => { const vp = V && V.plot ? V.plot[st.id] : null; return vp ? lawsOf(st).filter((L) => L.x === vp.x && L.y === vp.y && L.model === vp.fit) : lawsOf(st); };
  const refItems = steps.flatMap((st) => lawsShown(st).filter((L) => refs[st.id] && refs[st.id][L.reference]).map((L) => {
    const r = refs[st.id][L.reference];
    return el("li", {}, `${t(st.title)}: ${t(L.label)} = ${withUnit(fmt(r.value, ".4g"), t(L.unit || r.unit || ""))} — ${t(r.label)} (${t(r.how)})`);
  }));
  const tAns = questions.length ? sheet("teacher", el("h2", {}, t("For the teacher")), el("h3", {}, t("Answers")),
    el("ol", {}, questions.map((q) => el("li", {}, el("div", {}, t(q.q)), el("div", { class: "answer" }, t(q.answer)))))) : null;
  const tNotes = (ws.teacher || []).length || refItems.length ? sheet("teacher", el("h2", {}, t("For the teacher")),
    (ws.teacher || []).length ? [el("h3", {}, t("Notes")), el("ul", {}, ws.teacher.map((x) => el("li", {}, t(x))))] : null,
    refItems.length ? [el("h3", {}, t("The laws' references (computed by the world when the site was built)")), el("ul", {}, refItems)] : null) : null;
  const varSel = variants.length ? el("label", { class: "variant-pick" }, t("Variant:") + " ", el("select", { "aria-label": t("Variant:"), onchange: (e) => {
    const u = new URL(location.href);
    if (e.target.value) u.searchParams.set("variant", e.target.value); else u.searchParams.delete("variant");
    location.replace(u.href);
  } }, el("option", { value: "", selected: !V }, t("The whole lab work")), variants.map((v) => el("option", { value: v.id, selected: V === v }, t(v.label))))) : null;
  fill(box,
    el("div", { class: "ws-tools" },
      el("a", { href: withLang(page("run", { demo: viz.id, screen: lab.id })) }, t("← Back to the lab work")),
      varSel,
      el("label", { title: t("The answers and the teacher's notes print on a page of their own") }, teacher, t("For the teacher")),
      el("button", { class: "primary", onclick: () => window.print() }, t("🖨 Print"))),
    parts, qs, tAns, tNotes);
  document.body.dataset.ready = "1";
}

function head(viz, ws, ru, V) {
  return [  // flat: el() flattens one level of its children
    el("h1", {}, t(viz.title)),
    V ? el("div", { class: "variant" }, t(V.label)) : null,
    el("div", { class: "who" }, [t("Name"), t("Class"), t("Date")].map((x) => el("span", {}, x + ": ", el("span", { class: "fill" })))),
    (ws.frp || []).filter((f) => !V || !V.grade || !f.grade || f.grade === V.grade).map((f) => el("div", { class: "frp" },
      [programmeName(f), f.grade ? t("grade {n:d}", { n: f.grade }) : ""].filter(Boolean).join(", ") + ": ",
      el("b", {}, t(f.name)),
      ru && f.name && f.name.$t && ru[f.name.$t] ? el("span", {}, " ", t("(our translation; the programme's own wording: «{orig}»)", { orig: ru[f.name.$t] })) : null)),
    (ws.equipment || []).length ? el("p", { class: "equip" }, el("b", {}, t("Equipment:")), " ", ws.equipment.map((x) => t(x)).join("; ")) : null,
    el("p", { class: "note" }, t("Each reading is rounded to the instrument's division; its error is the declared one (by default half a division)."),
      " ", t("The experiment is done on the computed bench of this demonstration: the engine computed every set-up in advance.")),
  ].flat(2);
}

main().catch((e) => { console.error(e); fill(box, el("p", {}, String(e.message || e))); });
