// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// A lab's task sheet (worksheet.html?demo=<world>[&variant=<id>][&computed=1]; /worksheet?demo=… on a server; design
// lfphys/sources/explore_2026-11-14_design.md §2.3, revised by lfphys/sources/explore_EX2_2026-11-18_design.md §1.4, §5
// F8): data, not a separate document. Lab work is a narrow bench, not a test (the owner, 2026-11-18): the sheet gives the
// task — the head (name, group, date), the programme's lab (school, frp: verbatim in Russian, its translation marked)
// or the course it is based on (university, basis: quoted verbatim in its own language and marked so), the goal, the
// bench, one suggested procedure, what to record and hand in, a free field «Task from the teacher» — then one sheet per
// part with its goal, its instruments (as the step card writes them, lab.js instrumentText), its computed columns, the
// set-up the variant preselects, a blank table and the plot frame. No questions, answers, teacher's pages or grading
// (**[error in earlier]**: EX1's worksheet had them).
//
// The teacher changes the task, on the static site too: a variant (&variant=<id>, the sheet's `variants`: computed in
// the atlases) prints its own goal, procedure and record and the controls it preselects; the goal, the procedure, the
// record list and the free field are editable before printing (contenteditable; «Restore the original»; kept in this
// browser per world and variant, a convenience: nothing is sent anywhere). «Computed for this bench» (&computed=1) prints
// the world's computed values for the bench on a page of their own: what the drawer of Lab work shows to everyone.
//
// Printed, every page is one `.sheet`, one A4 page with the attribution line at its foot (the licence's condition).
// Nothing is cut off unseen (review R2-P F1, F5): printed, a part's table is full width above its plot frame (a wide table
// broke out of its half of the page and over the plot); every sheet is laid out as it prints in a hidden copy
// (`.ws-proxy`, the same rules as the print's: PRINT_RULES), and a sheet longer than its page says so on the screen,
// above it; the teacher's task moves to a sheet of its own when it does not fit on the first.
import { MODE, apiGet, getJSON, page, url } from "./api.js";
import { lang, t, withLang } from "./i18n.js";
import { controlLabel, valueUnitText } from "./explore.js";
import { computedFor, instrumentText } from "./lab.js";
import { el, fill, initTheme, toggleTheme } from "./ui.js";

// the layout of a printed sheet, for the print itself (@media print) and for the hidden copy that measures it on the
// screen (.ws.ws-proxy, 186 mm wide: A4 less the page's margins). `S` is the scope.
const PRINT_RULES = (S) => `
  ${S} { max-width: none; padding: 0; margin: 0; font-size: 10pt; line-height: 1.3; }
  ${S} h1 { font-size: 15pt; margin: 0 0 2mm; } ${S} h2 { font-size: 13pt; margin: 2mm 0 1.5mm; } ${S} h3 { font-size: 11pt; margin: 2mm 0 1mm; }
  ${S} .editable { border: 0; padding: 0; outline: none; }
  ${S} .sheet { height: 273mm; border: 0; border-radius: 0; padding: 0; margin: 0; background: none; break-before: page; page-break-before: always; break-inside: avoid; overflow: hidden; }
  ${S} .sheet.first { break-before: auto; page-break-before: auto; }
  ${S} .sheet.stack .mgrid { grid-template-columns: minmax(0, 1fr); gap: 0; }
  ${S} .tbl { overflow: visible; }
  ${S} table.blank { table-layout: auto; }
  ${S} table.blank th, ${S} table.blank td { height: var(--row-h, 5.1mm); padding: 0 1.2mm; font-size: 9.5pt; }
  ${S} table.blank th { line-height: 1.15; }
  ${S} .sheet.squeeze table.blank th { overflow-wrap: anywhere; hyphens: auto; }
  ${S} .field > b { float: left; margin-right: 0.4em; }
  ${S} .field::after { content: ""; display: block; clear: both; }
  ${S} .field .editable p:first-child, ${S} .field .bench p:first-child { margin-top: 0; }
  ${S} table.blank.wide th, ${S} table.blank.wide td { font-size: 8pt; padding: 0 0.6mm; }
  ${S} .axes { height: var(--axes-h, 48mm); margin: 2mm 0 6mm 8mm; }
  ${S} .sheet.stack .axes { max-width: 120mm; }
  ${S} .lines { height: var(--lines-h, 7mm); border-bottom-color: #888; }
  ${S} .who .fill { min-width: 38mm; }
  ${S} .note, ${S} .frp, ${S} .basis { font-size: 8.5pt; }
  ${S} .instr, ${S} .formulas { font-size: 9pt; margin: 1mm 0; }
  ${S} .basis ul { margin: 0.5mm 0; padding-left: 5mm; }
  ${S} .credit { font-size: 7.5pt; color: #444; margin-top: 2mm; }
  ${S} .sheet-warn { display: none; }
  ${S}.split .sheet.first .field.teacher-task { display: none; }
  ${S} .sheet.teacher-cont { display: none; }
  ${S}.split .sheet.teacher-cont { display: flex; }`;
document.head.append(el("style", {}, `@media print {${PRINT_RULES(".ws")}\n  .ws .editable:focus { outline: none; }\n}\n${PRINT_RULES(".ws.ws-proxy")}
  .ws.ws-proxy { position: absolute; left: -10000px; top: 0; width: 186mm; visibility: hidden; pointer-events: none; }`));

initTheme();
document.getElementById("theme").onclick = toggleTheme;
const Q = new URLSearchParams(location.search);
const box = document.getElementById("ws");
// the sheet's texts are Site Materials under CC BY-NC-SA 4.0 (LICENSE.md §1 item 8, §9): every printed page carries the
// creator's line and the notices that licence asks a reuser to keep (§3(a)(1)(A))
const CREDIT_LINE = "lfphys — Ildar Idrisov — https://ildar-idrisov.github.io/lfphys/";
const CC_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/";
const credit = () => el("p", { class: "credit" }, t("{line} · © 2026 Ildar Idrisov · the texts of this task sheet: CC BY-NC-SA 4.0 ({cc}) · provided as is, without warranty · mark your changes and share changed copies under the same licence", { line: CREDIT_LINE, cc: CC_URL }));
// a sheet: one printed page, its attribution line at its foot
const sheet = (cls, ...children) => el("section", { class: "sheet " + cls }, el("div", { class: "sheet-body" }, ...children), credit());

// the programme's name for a reader: the entry's `programme` (a T), never the raw id (review EX1-worlds F7g)
const programmeName = (f) => (f.programme ? t(f.programme) : "");
// a unit after a value («41.9°», «0.6774 m^½»)
const withUnit = (text, unit) => (!unit ? text : unit === "°" ? text + unit : `${text} ${unit}`);
const FIT_CURVE = () => ({ line0: t("the best straight line through the origin"), line: t("the best straight line"),
  quadratic: t("the best parabola"), power: t("the best power-law curve") });
const plotHow = (y, x, model) => (model ? t("Plot {y} against {x}, mark the points with their error bars and draw {curve}.", { y, x, curve: FIT_CURVE()[model] || FIT_CURVE().line })
  : t("Plot {y} against {x}: the points with their error bars, without a line.", { y, x }));

// the editable texts of the sheet (F8 (b)): kept in this browser per world and variant (a convenience; try/catch:
// private windows and blocked storage)
// (and per language: an edit is a text in the language it was typed in; review R2-P nits)
const EDIT = (world, variant, code = lang()) => `lfviz.sheet.${world}.${variant || ""}.${code}`;
function loadEdits(key) { try { return JSON.parse(localStorage.getItem(key) || "{}") || {}; } catch (e) { return {}; } }
function saveEdits(key, obj) { try { localStorage.setItem(key, JSON.stringify(obj)); } catch (e) { /* the edits live in the page */ } }

async function main() {
  const id = Q.get("demo");
  let viz;
  try { viz = await apiGet(`viz/${encodeURIComponent(id || "")}`); } catch (e) {  // a world that does not load says why (2026-11-18)
    fill(box, el("p", {}, e.body && e.body.detail ? e.message : t("No such demonstration"))); return;
  }
  const lab = (viz.screens || []).find((s) => s.kind === "lab");
  if (!lab) { fill(box, el("p", {}, t("This demonstration has no lab work."))); return; }
  document.title = t("Task sheet: {title}", { title: t(viz.title) });
  const ws = lab.worksheet || {};
  // the ФРП names verbatim in Russian: in another language, the Russian original next to the translation
  let ru = null;
  if (lang() !== "ru" && (ws.frp || []).length) {
    try { ru = (await getJSON(url("static/locales/ru.json"))).messages || null; } catch (e) { ru = null; }
  }
  const variants = ws.variants || [];
  const V = variants.find((v) => v.id === Q.get("variant")) || null;
  const steps = (lab.steps || []).filter((st) => !V || !V.steps || V.steps.includes(st.id));
  const showComputed = Q.get("computed") === "1";
  // the world's computed values (the laws' references), from the atlases built with the current code (the key the
  // server expects; integrator D11): here, or (a server without them) the published site's of the same world version.
  // A step on an Explore screen's atlas (F9) finds its values there as "<step>/<law>"
  const refs = {};  // atlas id -> its manifest's references
  if (showComputed) {
    try {
      const rec = await apiGet("recordings");
      const exp = ((rec.expected || {})[viz.id] || {}).atlases || {};
      const want = new Set(steps.filter((st) => (st.laws || []).length).map((st) => st.atlas));
      const fresh = (a) => want.has(a.id) && (exp[a.id] === undefined || a.key === exp[a.id]);
      const local = (rec.worlds || {})[viz.id];
      const sources = [[local, url(`recordings/${viz.id}/`)]];
      const hereOk = (aid) => ((local && local.atlases) || []).some((a) => a.id === aid && fresh(a)
        && String(a.version ?? local.version) === String(viz.version));
      if (MODE === "server" && rec.published && rec.site && ![...want].every(hereOk)) {
        const siteRec = await getJSON(`${rec.site}api/recordings.json`).catch(() => null);
        sources.push([((siteRec && siteRec.worlds) || {})[viz.id] || null, `${rec.site}recordings/${viz.id}/`]);
      }
      for (const [ix, base] of sources) {
        for (const a of ((ix && ix.atlases) || []).filter(fresh)) {
          if (refs[a.id] || String(a.version ?? ix.version) !== String(viz.version)) continue;
          try { refs[a.id] = (await getJSON(base + a.file)).references || {}; } catch (e) { /* not reachable: none */ }
        }
      }
    } catch (e) { /* no recordings: no computed values */ }
  }
  const instr = lab.instruments || {};
  const colLabel = (st, cid) => t((st.columns.find((c) => c.id === cid) || {}).label || cid);
  const editKey = EDIT(viz.id, V && V.id);
  const edits = loadEdits(editKey);
  const editables = [];
  // an editable block of paragraphs: the original kept for «Restore the original»; edits saved as the reader types
  const editable = (name, paras, cls = "") => {
    const node = el("div", { class: `editable ${cls}`, contenteditable: "true", spellcheck: "true", "data-edit": name, "aria-label": t("editable before printing") },
      ...(paras || []).map((x) => el("p", {}, x)));
    const original = node.innerHTML;
    if (typeof edits[name] === "string") node.innerHTML = edits[name];
    node.addEventListener("input", () => { edits[name] = node.innerHTML; saveEdits(editKey, edits); });
    editables.push({ node, original, name });
    return node;
  };
  const vtext = (V && V.text) || {};
  const tasks = sheet("task first",
    head(viz, ws, ru, V),
    el("h2", {}, t("The task")),
    el("div", { class: "field" }, el("b", {}, t("Goal:")), " ", editable("goal", [t(vtext.goal || ws.goal)], "inline")),
    el("div", { class: "field" }, el("b", {}, t("The bench:")), el("div", { class: "bench" }, (ws.bench || []).map((x) => el("p", {}, t(x))))),
    el("div", { class: "field" }, el("b", {}, t("A suggested procedure (one of several ways):")), editable("procedure", (vtext.procedure || ws.procedure || []).map((x) => t(x)))),
    el("div", { class: "field" }, el("b", {}, t("Record and hand in:")), editable("record", (vtext.record || ws.record || []).map((x) => t(x)))),
    el("div", { class: "field teacher-task" }, el("b", {}, t("Task from the teacher:")), editable("teacher_task", [], "free")));
  // the teacher's task on a sheet of its own, printed only when it does not fit on the first (measure(), below)
  const teacherCopy = el("div", { class: "teacher-copy" });
  const teacherSheet = sheet("teacher-cont", el("h2", {}, t("Task from the teacher:")), teacherCopy);
  const rows = ws.record_rows || 10;
  const parts = steps.map((st, k) => {
    const pre = V && V.values ? V.values[st.id] || {} : {};
    const ctl = (st.controls || []).filter((c) => c.param in pre);
    // the variant's set-up as Lab work's controls write it (review R2-P F6: raw «false», «real», «1.1» in Russian):
    // a value's own name, a number in the viewer's format with its unit, «on» / «off»
    const preText = ctl.map((c) => `${t(c.label)} ${valueUnitText(c, pre[c.param])}`).join(", ");
    // the set-up's columns of the table: the step's controls that no instrument reads (review R2-P F7), as in Lab work
    const read = new Set(st.instruments.map((iid) => String((instr[iid] || {}).reads || "")).filter((r) => r.startsWith("control:")).map((r) => r.slice(8)));
    const setup = (st.controls || []).filter((c) => !read.has(c.param));
    // a part has the step's plot frame, without a fit: which line to draw is the student's choice (EX2 §1.4)
    const cols = st.columns;
    const plot = { x: st.plot.x, y: st.plot.y, model: null };
    return sheet("part",
      el("h2", {}, t("Part {k:d} of {n:d}: {title}", { k: k + 1, n: steps.length, title: t(st.title) })),
      el("p", {}, el("b", {}, t("Goal:")), " ", t(st.goal)),
      el("p", { class: "instr" }, el("b", {}, t("Instruments:")), " ", st.instruments.filter((iid) => instr[iid]).flatMap((iid, j) => [j ? "; " : "",
        el("b", {}, t(instr[iid].label)), " — ", instrumentText(instr[iid]),
        instr[iid].error_note && instr[iid].kind !== "counter" && (instr[iid].sigma || (instr[iid].error ?? instr[iid].division / 2) > 0) ? ` (${t(instr[iid].error_note)})` : ""])),
      cols.some((c) => c.expr) ? el("p", { class: "formulas" }, el("b", {}, t("Computed columns:")), " ",
        cols.filter((c) => c.expr).flatMap((c, j) => [j ? "; " : "", t(c.label), " = ", el("code", {}, c.expr)])) : null,
      preText ? el("p", { class: "preset" }, el("b", {}, t("This variant's set-up:")), " ", preText) : null,
      el("div", { class: "mgrid" },
        el("div", {}, el("h3", {}, t("Measurements")),
          // a wide table (u34's part 2: 16 columns) scrolls in its own box on a screen, not the page; printed in full
          el("div", { class: "tbl" }, el("table", { class: "blank" + (setup.length + cols.length > 8 ? " wide" : "") }, el("tr", {}, el("th", {}, "№"),
            setup.map((c) => el("th", { class: "setup" }, controlLabel(c))), cols.map((c) => el("th", {}, t(c.label)))),
            Array.from({ length: rows }, (_, i) => el("tr", {}, el("td", {}, String(i + 1)), setup.map(() => el("td", {})), cols.map(() => el("td", {}))))))),
        el("div", {}, el("h3", {}, t("Plot")),
          el("p", { class: "plot-how" }, plotHow(colLabel(st, plot.y), colLabel(st, plot.x), plot.model)),
          el("div", { class: "axes" }, el("span", { class: "ax ay" }, colLabel(st, plot.y)), el("span", { class: "ax axx" }, colLabel(st, plot.x))))),
      el("p", { class: "concl" }, el("b", {}, t("Notes:"))), el("div", { class: "lines" }), el("div", { class: "lines" }));
  });
  // «Computed for this bench» on a page of its own (F8 (c)): the values the drawer of Lab work shows to everyone
  const computed = showComputed ? sheet("computed", el("h2", {}, t("Computed for this bench")),
    el("p", { class: "note" }, t("The world's own values for this bench, from its laws: what a measurement done the right way comes to. Everyone sees them in Lab work's drawer «How we know this is right».")),
    steps.map((st) => {
      const items = computedFor(st, refs[st.atlas] || {}, (cid) => colLabel(st, cid));
      return items.length ? [el("h3", {}, t(st.title)), el("ul", {}, items.map((x) => el("li", {}, x.text, x.how ? ` (${x.how})` : "")))] : [];
    }).flat(), steps.every((st) => !computedFor(st, refs[st.atlas] || {}).length) ? el("p", { class: "muted" }, t("No computed values found: the atlases are built with the site (site/atlas.py).")) : null) : null;
  // the tools: the variant, the computed values, «Restore the original», print
  const setParam = (k, v) => { const u = new URL(location.href); if (v) u.searchParams.set(k, v); else u.searchParams.delete(k); location.replace(u.href); };
  const varSel = variants.length ? el("label", { class: "variant-pick" }, t("Variant:") + " ", el("select", { "aria-label": t("Variant:"), onchange: (e) => setParam("variant", e.target.value) },
    el("option", { value: "", selected: !V }, t("The whole lab work")), variants.map((v) => el("option", { value: v.id, selected: V === v }, `${t(v.label)} (${v.id})`)))) : null;
  const comp = el("input", { type: "checkbox", checked: showComputed, onchange: (e) => setParam("computed", e.target.checked ? "1" : "") });
  const restore = el("button", { class: "ws-restore", onclick: () => {
    for (const x of editables) x.node.innerHTML = x.original;
    for (const k of Object.keys(edits)) delete edits[k];
    saveEdits(editKey, edits);
    later();
  } }, t("Restore the original"));
  fill(box,
    el("div", { class: "ws-tools" },
      el("a", { href: withLang(page("run", { demo: viz.id, screen: lab.id, ...(V ? { variant: V.id } : {}) })) }, t("← Back to the lab work")),
      varSel,
      el("label", { title: t("The world's computed values for this bench, on a page of their own") }, comp, t("Computed for this bench")),
      restore,
      el("button", { class: "primary", onclick: () => window.print() }, t("🖨 Print"))),
    el("p", { class: "ws-hint muted" }, t("The goal, the procedure, the record list and the teacher's task can be edited here before printing; the edits stay in this browser only.")),
    tasks, teacherSheet, parts, computed);
  // every sheet laid out as it prints, in a hidden copy: a sheet longer than its page says so above it (on the screen
  // only), and the teacher's task goes to a sheet of its own when the first does not hold it (review R2-P F5)
  const measure = () => {
    const teacher = editables.find((x) => x.name === "teacher_task").node;
    teacherCopy.innerHTML = teacher.innerHTML;
    const sheets = () => [...box.querySelectorAll(":scope > .sheet")];
    // a hidden copy of the sheets laid out as printed; f(copy of sheet i, i) for each, the proxy removed after
    const inProxy = (split, f) => {
      const proxy = el("div", { class: "ws ws-proxy" + (split ? " split" : ""), "aria-hidden": "true" });
      for (const sh of sheets()) proxy.append(sh.cloneNode(true));
      document.body.append(proxy);
      try { return [...proxy.querySelectorAll(":scope > .sheet")].map(f); } finally { proxy.remove(); }
    };
    // how far a sheet's content runs past its page box (px): past its foot (the attribution line) or its sides
    const overOf = (sh) => {
      if (getComputedStyle(sh).display === "none") return 0;
      const r = sh.getBoundingClientRect(), b = sh.querySelector(".sheet-body"), c = sh.querySelector(".credit");
      let over = Math.max(0, b.scrollHeight - b.clientHeight);
      for (const e of b.querySelectorAll("*")) {
        const q = e.getBoundingClientRect();
        if (!q.width && !q.height) continue;
        over = Math.max(over, q.bottom - (c ? c.getBoundingClientRect().top : r.bottom), q.right - r.right, r.left - q.left);
      }
      return over > 1 ? over : 0;
    };
    const mm = (px) => px * 25.4 / 96;
    // a part's layout: the table beside its plot frame when it fits in its half of the page, else full width above it
    // (review R2-P F1: u34's part 2 ran over the plot frame and off the page); a part still too long gets a lower plot
    // frame (down to 24 mm), then lower rows (down to 4.4 mm), then closer «Notes» lines (down to 5 mm)
    const parts = () => sheets().filter((sh) => sh.classList.contains("part"));
    for (const sh of parts()) { sh.classList.remove("stack"); for (const p of ["--axes-h", "--row-h", "--lines-h"]) sh.style.removeProperty(p); }
    // (a table's headers break between words; only a table wider than the page breaks them anywhere, «squeeze»)
    const fits = () => inProxy(false, (sh) => { const tb = sh.querySelector("table.blank"), tbox = sh.querySelector(".tbl"); return !tb || tb.getBoundingClientRect().width <= tbox.getBoundingClientRect().width + 1; });
    for (const sh of parts()) sh.classList.remove("squeeze");
    const narrow = fits();
    sheets().forEach((sh, i) => { if (sh.classList.contains("part") && !narrow[i]) sh.classList.add("stack"); });
    const full = fits();
    sheets().forEach((sh, i) => { if (sh.classList.contains("part") && !full[i]) sh.classList.add("squeeze"); });
    for (const [prop, from, to] of [["--axes-h", 48, 24], ["--row-h", 5.1, 4.4], ["--lines-h", 7, 5]]) {
      const over = inProxy(false, overOf);
      sheets().forEach((sh, i) => { if (sh.classList.contains("part") && over[i]) sh.style.setProperty(prop, `${Math.max(to, from - mm(over[i]) - 1).toFixed(1)}mm`); });
    }
    const hasTask = teacher.textContent.trim().length > 0;
    let over = inProxy(false, overOf);
    const split = hasTask && over[0] > 0;  // the teacher's task on a sheet of its own (review R2-P F5)
    if (split) over = inProxy(true, overOf);
    box.classList.toggle("split", split);
    box.querySelectorAll(":scope > .sheet-warn").forEach((w) => w.remove());
    sheets().forEach((sh, i) => {
      if (!over[i]) return;
      sh.before(el("p", { class: "sheet-warn", role: "status" }, t("This page is longer than an A4 sheet by {mm:d} mm: what does not fit is not printed. Shorten its texts.", { mm: Math.ceil(mm(over[i])) })));
    });
    document.body.dataset.overflow = String(over.filter(Boolean).length);
  };
  let pending = 0;
  const later = () => { clearTimeout(pending); pending = setTimeout(measure, 250); };
  for (const x of editables) x.node.addEventListener("input", later);
  window.addEventListener("beforeprint", measure);
  await (document.fonts ? document.fonts.ready : Promise.resolve());
  measure();
  window.__lfSheet = { measure };
  document.body.dataset.ready = "1";
}

function head(viz, ws, ru, V) {
  return [  // flat: el() flattens one level of its children
    el("h1", {}, t(viz.title)),
    V ? el("div", { class: "variant" }, t("Variant: {label}", { label: t(V.label) })) : null,  // its name, not its raw id (review R2-P F6)
    el("div", { class: "who" }, [t("Name"), viz.ui === "school" ? t("Class") : t("Group"), t("Date")].map((x) => el("span", {}, x + ": ", el("span", { class: "fill" })))),
    (ws.frp || []).filter((f) => !V || !V.grade || !f.grade || f.grade === V.grade).map((f) => el("div", { class: "frp" },
      [programmeName(f), f.grade ? t("grade {n:d}", { n: f.grade }) : ""].filter(Boolean).join(", ") + ": ",
      el("b", {}, t(f.name)),
      ru && f.name && f.name.$t && ru[f.name.$t] ? el("span", {}, " ", t("(our translation; the programme's own wording: «{orig}»)", { orig: ru[f.name.$t] })) : null)),
    // a university sheet's basis (EX2 §1.4, §5 F8): the course or the manual it follows, its words quoted verbatim in
    // their own language and marked as a quotation
    (ws.basis || []).length ? el("div", { class: "basis" }, el("b", {}, t("Basis:")), el("ul", {}, ws.basis.map((b) => el("li", {},
      t(b.text), " — ", el("span", { class: "source" }, t(b.source)),
      b.quote ? el("div", { class: "quote-box" }, el("span", { class: "quote-mark" }, t("quoted verbatim:")), " ",
        el("q", { class: "quote", lang: b.quote_lang || "en" }, b.quote)) : null)))) : null,
    el("p", { class: "note" }, t("Each reading is rounded to the instrument's division; its error is the declared one (by default half a division)."),
      " ", t("The experiment is done on the computed bench of this demonstration: the engine computed every set-up in advance.")),
  ].flat(2);
}

main().catch((e) => { console.error(e); fill(box, el("p", {}, String(e.message || e))); });
