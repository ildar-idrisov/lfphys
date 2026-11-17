// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The Lab work screen (design lfphys/sources/explore_2026-11-14_design.md §2.3, §3.5): steps in order, each on its own
// atlas (lab.<step>) as Explore uses its own, so it works on the public site. The step card (part k of n, the goal, the
// step's controls, its instruments and «Measure»), the instruments drawn over the view through the view's worldToPx (an
// SVG layer), the table (kept per step in this browser; a row can be deleted, the table cleared and exported as CSV with
// the errors), the plot of any two columns with error bars and the selected fit, the fit's result, and «Check against
// the law» against the reference the world computed when the atlas was built (the manifest's "references").
//
// An instrument does not compute physics: it reads a value the run computed (a measurable at the cursor, or a set-up
// value "control:<param>" of the point shown) and rounds it to its division; the reading carries the declared error (by
// default half a division). The derived columns and the fit are arithmetic and statistics on the readings (fit.js).
//
// What keeps the bench honest (review EX1-screens F1, F3–F5; integrator D4–D6):
//  - a point's reply is applied only when it is still the one asked for (a request counter); every instrument reads
//    the shown point's own values (its header's parameters, its frames), never the slider; «Measure» is refused while
//    the slider's set-up is not the one shown (loading, refused or failed);
//  - one row per set-up: «Measure» on a set-up already in the table replaces that row and says so (the bench repeats
//    exactly: a repeat is not an independent point); the table is kept with the atlas's key and dropped when the atlas
//    was rebuilt;
//  - «Check against the law» applies only when the plot is one of the step's laws' (x, y, fit): the step's `laws`
//    (registry), each with its own reference; otherwise it is disabled with the reason, and the laws' plots are offered.
//    The bound is two errors when the errors are the instruments' declared ones, Student's t for n − p degrees of
//    freedom when they come from the scatter (fit.js verdict); a fit whose scatter exceeds its errors more than
//    BIRGE_MAX times gives no verdict;
//  - a manual stopwatch starts with the launch and runs on the wall clock until the student stops it: at real speed
//    only («slow» is refused), and while it runs the flight cannot be paused, scrubbed or stepped (it times the real
//    flight with the student's reaction, as a hand-held one does).
import { openAtlas } from "./atlas.js";
import { BIRGE_MAX, MODELS as FIT_MODELS, fit, quantity, verdict } from "./fit.js";
import { t } from "./i18n.js";
import { SLOW, controlRow, ended, localT, secs, valuesText, when } from "./explore.js";
import { frameAt, frameIndexAt, showAt } from "./record_core.js";
import { css, el, fill, fmt } from "./ui.js";

// --- readings (pure: lab.test.mjs) ----------------------------------------------------------------------------------------
export const decimals = (d) => { const s = String(d); if (s.includes("e-")) return Number(s.split("e-")[1]) + (s.split("e-")[0].split(".")[1] || "").length; return (s.split(".")[1] || "").length; };
// a value read by an instrument: division × round(value / division), its error the declared one (half a division)
export function reading(instr, value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null;
  const d = Number(instr.division);
  const v = Number((Math.round(Number(value) / d) * d).toFixed(Math.min(15, decimals(d))));
  return { v: Object.is(v, -0) ? 0 : v, e: instr.error ?? d / 2 };
}
// a derived column: its value and its error σ_f² = f′(x)²·σ² + ½·f″(x)²·σ⁴ (the second-order term keeps an error at a
// stationary point: sin 2θ at 45° is 1.0000 ± 0.0002, not ± 0; review EX1-screens F14). sin2: sin 2θ with θ in degrees
const RAD = Math.PI / 180;
const OPS = {
  sqrt: [(x) => Math.sqrt(x), (x) => 1 / (2 * Math.sqrt(x)), (x) => -1 / (4 * x * Math.sqrt(x))],
  square: [(x) => x * x, (x) => 2 * x, () => 2],
  sin2: [(x) => Math.sin(2 * x * RAD), (x) => 2 * Math.cos(2 * x * RAD) * RAD, (x) => -4 * Math.sin(2 * x * RAD) * RAD * RAD],
  inverse: [(x) => 1 / x, (x) => -1 / (x * x), (x) => 2 / (x * x * x)],
  log: [(x) => Math.log(x), (x) => 1 / x, (x) => -1 / (x * x)],
};
export function derived(op, r) {
  if (!r || !OPS[op]) return null;
  const [f, d1, d2] = OPS[op];
  const v = f(r.v), a = d1(r.v) * r.e, b = d2(r.v) * r.e * r.e;
  const e = Math.sqrt(a * a + 0.5 * b * b);
  return Number.isFinite(v) ? { v, e: Number.isFinite(e) ? e : NaN } : null;
}
// a table row from the instruments' readings ({instrument id: {v, e}}): every column of the step
export function rowOf(columns, readings) {
  const cols = {};
  for (const c of columns) {
    if (c.from) cols[c.id] = readings[c.from] || null;
    else if (c.of) cols[c.id] = derived(c.op, cols[c.of]);
  }
  return cols;
}
// CSV with the errors: a header of the columns' labels (and «σ …»), one line per row; numbers as plain decimals
export function csv(columns, rows, label = (c) => c.id) {
  const q = (s) => (/[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
  const head = columns.flatMap((c) => [q(label(c)), q("σ " + label(c))]);
  const lines = rows.map((r) => columns.flatMap((c) => { const x = r.cols[c.id]; return x ? [String(x.v), String(x.e)] : ["", ""]; }).join(","));
  return [head.join(","), ...lines].join("\n") + "\n";
}
// a value with its error: the error to two significant digits, the value to the same decimal place
export function pm(v, e) {
  if (!Number.isFinite(v)) return "—";
  if (!(e > 0) || !Number.isFinite(e)) return fmt(v, ".4g");
  const k = Math.max(0, 1 - Math.floor(Math.log10(e)));
  return `${fmt(v, `.${Math.min(12, k)}f`)} ± ${fmt(e, `.${Math.min(12, k)}f`)}`;
}
// a reading as the instrument shows it, to the decimals of its division or of its error, whichever is finer
// («0.600 ± 0.005», not «0.60 ± 0.005»; review EX1-screens F14)
export function readingText(instr, x) {
  const n = Math.max(decimals(instr.division), decimals(Number(x.e.toPrecision(2))));
  return `${fmt(x.v, `.${Math.min(12, n)}f`)} ± ${fmt(x.e, ".2g")}`;
}
// a unit after a value: «45°» with no space before the degree sign, «0.677 m^½» with one (review EX1-screens F16)
export const withUnit = (text, unit) => (!unit ? text : unit === "°" ? text + unit : `${text}\u00a0${unit}`);
// a set-up's identity: its control values (the grid values of the point; D5)
export const setupKey = (values) => JSON.stringify(Object.keys(values || {}).sort().map((k) => [k, values[k]]));
// a measured row into the table: a set-up already there is replaced (D5). Returns {rows, n (1-based), replaced}
export function placeRow(rows, row) {
  const j = rows.findIndex((r) => setupKey(r.values) === setupKey(row.values));
  if (j < 0) return { rows: [...rows, row], n: rows.length + 1, replaced: false };
  const out = rows.slice(); out[j] = row;
  return { rows: out, n: j + 1, replaced: true };
}
// the law of the plot shown: the step's law whose (x, y, model) is the plot's, or null (D4)
export const lawOf = (laws, x, y, model) => (laws || []).find((L) => L.x === x && L.y === y && L.model === model) || null;

// the table of a step, kept in this browser with the atlas's key: rows of another key (an older bench) are dropped
const STORE = (world, atlas) => `lfviz.lab.${world}.${atlas}`;
export function loadRows(storage, key, atlasKey) {
  try {
    const j = JSON.parse(storage.getItem(key) || "null");
    if (j && !Array.isArray(j) && j.key === atlasKey && Array.isArray(j.rows)) return { rows: j.rows, dropped: 0 };
    const n = Array.isArray(j) ? j.length : j && Array.isArray(j.rows) ? j.rows.length : 0;
    if (n) storage.removeItem(key);
    return { rows: [], dropped: n };
  } catch (e) { return { rows: [], dropped: 0 }; }
}
function saveRows(key, atlasKey, rows) { try { localStorage.setItem(key, JSON.stringify({ key: atlasKey, rows })); } catch (e) { /* private mode: the table lives in the page */ } }

const FIT_LABEL = () => ({ line0: t("line through the origin y = b·x"), line: t("line y = a + b·x"), quadratic: t("parabola y = c0 + c1·x + c2·x²"), power: t("power law y = A·x^p") });

export async function create(host, kit, spec) {
  const steps = spec.steps || [], instruments = spec.instruments || {};
  const L = { k: 0, st: [], playing: false, wall: 0, rate: 1 };
  const view = kit.newView();
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "dm-instr");
  svg.setAttribute("aria-hidden", "true");
  const stage = el("div", { class: "dm-stage" }, view.center, svg);
  const card = el("div", { class: "dm-side dm-card" });
  const work = el("div", { class: "dm-work" });
  const bar = kit.transport({ launchLabel: t("▶ Launch"), play: () => playPressed(), reset: () => resetPressed(),
    scrub: (i) => scrub(i), rate: (r) => { L.rate = r === 1 ? 1 : SLOW; kit.self.rate = L.rate; } });
  // «Measure», the stopwatch and the messages: in the step card on a desktop; on a phone in the dock above the time bar,
  // sticky, so that they are within reach while the ball is in view (integrator D12)
  const act = el("div", { class: "dm-act" });
  const dock = el("div", { class: "dm-dock" }, bar.el);
  fill(host, el("div", { class: "dm-main" }, stage, card), dock, work);
  const narrow = matchMedia("(max-width: 999px)");
  const placeAct = () => {
    if (narrow.matches) { if (act.parentNode !== dock) dock.prepend(act); }
    else { const slot = card.querySelector(".dm-act-slot"); if (slot && act.parentNode !== slot) slot.append(act); }
  };
  narrow.addEventListener("change", placeAct);

  // --- a step's state, made when the step is first opened -------------------------------------------------------------
  async function stepState(k) {
    if (L.st[k]) return L.st[k];
    const step = steps[k];
    const src = kit.atlasSource ? kit.atlasSource(step.atlas) : { why: t("No atlas of this step yet: it is built with the site (site/atlas.py).") };
    const laws = step.laws || [];
    const S = { step, laws, A: null, why: src.why || null, values: {}, cur: null, clock: 0, rows: [], sw: null, seq: 0, pending: false,
      refused: null, failed: null, x: step.plot.x, y: step.plot.y, model: step.plot.fit || (step.plot.fits || [])[0] || "line",
      res: null, check: null, msg: "", fromSite: !!src.fromSite };
    if (src.entry) {
      try {
        S.A = await openAtlas(kit.world, src.entry, { base: src.base });
      } catch (e) { S.why = t("This step's atlas could not be loaded: {why}", { why: e.message }); }
    }
    if (S.A) {
      S.A.controls = S.A.controls.map((c) => ({ ...((step.controls || []).find((x) => x.param === c.param) || {}), ...c }));
      S.values = { ...S.A.defaults };
      const got = loadRows(localStorage, STORE(kit.world, step.atlas), S.A.manifest.key);
      S.rows = got.rows;
      if (got.dropped) S.msg = t("The table of an earlier build of this bench was cleared: its atlas has been rebuilt");
      try {
        const pt = await S.A.point(S.values);
        if (pt.state === "computed") S.cur = { pt, launchedAt: null };
        else S.refused = t(pt.refusal);
      } catch (e) { S.failed = t("This point could not be loaded: {why}", { why: e.message }); }
      S.A.prefetch(S.values);
    }
    L.st[k] = S;
    return S;
  }
  const S = () => L.st[L.k];

  async function openStep(k) {
    L.k = k; L.playing = false;
    await stepState(k);
    renderCard(); renderWork();
    // a manual stopwatch measures the student's reaction: real speed only
    const manual = S().step.instruments.some((id) => instruments[id] && instruments[id].manual);
    bar.setSlowAllowed(!manual, t("A manual stopwatch measures your own reaction: it works at real speed only"));
    kit.dirty();
  }

  // --- the step card -----------------------------------------------------------------------------------------------------
  let ctlRows = [];
  function renderCard() {
    const s = S(), step = s.step;
    const nav = steps.length > 1 ? el("div", { class: "dm-seg dm-steps", role: "group", "aria-label": t("Parts of the lab work") }, steps.map((x, j) => el("button", {
      class: j === L.k ? "on" : "", "aria-current": j === L.k ? "step" : null, title: t(x.title),
      "aria-label": t("Part {k:d} of {n:d}: {title}", { k: j + 1, n: steps.length, title: t(x.title) }), onclick: () => openStep(j) }, String(j + 1)))) : null;
    ctlRows = s.A ? s.A.controls.map((c) => {
      const r = controlRow(c, s.values[c.param], (v) => pick(c, v), { server: false });
      r.set(s.values[c.param]);
      return r;
    }) : [];
    const instrList = el("ul", { class: "dm-instr-list" }, step.instruments.map((id) => {
      const i = instruments[id];
      if (!i) return null;
      return el("li", {}, el("b", {}, t(i.label)), " — ", t("division {d}, error ±{e}", { d: withUnit(fmt(i.division, ".6g"), t(i.unit)), e: withUnit(fmt(i.error ?? i.division / 2, ".6g"), t(i.unit)) }),
        i.error_note ? el("div", { class: "muted" }, t(i.error_note)) : null);
    }));
    const swBox = step.instruments.filter((id) => instruments[id] && instruments[id].manual).map((id) => stopwatchWidget(id, instruments[id]));
    const measure = el("button", { class: "primary dm-measure", onclick: () => measureNow() }, t("Measure"));
    const msg = el("div", { class: "dm-msg", role: "status" }, s.msg);
    fill(act, swBox, measure, msg);
    fill(card, nav,
      el("div", { class: "dm-part" }, t("Part {k:d} of {n:d}: {title}", { k: L.k + 1, n: steps.length, title: t(step.title) })),
      el("p", { class: "dm-goal" }, t(step.goal)),
      s.why ? el("p", { class: "dm-missing" }, s.why) : null,
      s.fromSite ? el("p", { class: "muted dm-from-site" }, t("This step's atlas comes from the public site: this server has no current local copy (the same version of the world).")) : null,
      el("div", { class: "dm-ctls" }, ctlRows.map((r) => r.el)),
      el("div", { class: "dm-sub" }, t("Instruments")), instrList,
      el("div", { class: "dm-act-slot" }),
      el("p", { class: "dm-ws" }, el("a", { href: kit.worksheetHref(), target: "_blank" }, t("The worksheet (print) →"))));
    placeAct();
    renderMeasure();
  }
  // «Measure» is offered only when the set-up shown is the slider's (D6)
  function measureBlock(s) {
    if (!s.A) return s.why || t("Choose a set-up first");
    if (s.pending) return t("The set-up is loading: measure when it is shown");
    if (s.failed) return s.failed;
    if (s.refused) return s.refused;
    if (!s.cur || setupKey(shownValues(s)) !== setupKey(pickValues(s))) return t("The set-up is loading: measure when it is shown");
    return null;
  }
  function renderMeasure() {
    const s = S(), b = act.querySelector(".dm-measure");
    if (!b) return;
    const why = measureBlock(s);
    b.disabled = !!why;
    b.title = why || "";
  }
  // the controls' values as the slider says, and as the point shown was computed with
  const pickValues = (s) => Object.fromEntries((s.A ? s.A.controls : []).map((c) => [c.param, s.values[c.param]]));
  const shownValues = (s) => Object.fromEntries((s.A ? s.A.controls : []).map((c) => [c.param, s.cur ? s.cur.pt.values[c.param] : undefined]));
  async function pick(c, v) {
    const s = S(), seq = ++s.seq;
    s.values = { ...s.values, [c.param]: v };
    for (const [j, r] of ctlRows.entries()) r.set(s.values[s.A.controls[j].param]);
    s.pending = true; s.refused = null; s.failed = null;
    renderMeasure();
    let pt = null;
    try { pt = await s.A.point(s.values); } catch (e) {
      if (seq !== s.seq) return;
      s.pending = false; s.failed = t("This point could not be loaded: {why}", { why: e.message });
      say(s.failed); renderMeasure(); return;
    }
    if (seq !== s.seq) return;  // a newer choice came first: this reply is not the one asked for (D6)
    s.pending = false;
    s.A.prefetch(s.values);
    if (pt.state === "refused") { s.refused = t(pt.refusal); say(s.refused); renderMeasure(); return; }
    say("");
    s.cur = { pt, launchedAt: null }; s.sw = null; L.playing = false;
    renderStopwatches(); renderMeasure();
    kit.dirty();
  }
  function say(text) { const s = S(); s.msg = text; const m = act.querySelector(".dm-msg"); if (m) m.textContent = text; }

  // --- the manual stopwatch (wall clock: review EX1-screens F5) ------------------------------------------------------------
  const swNow = (sw) => (sw.running ? (performance.now() - sw.t0) / 1000 : sw.t);
  function stopwatchWidget(id, instr) {
    const out = el("output", { class: "mono dm-sw-read", "aria-live": "off" }, "—");
    const btn = el("button", { class: "dm-sw-btn", onclick: () => {
      const s = S();
      if (!s.sw || !s.sw.running) { say(t("The stopwatch starts with the launch: press ▶ Launch first")); return; }
      s.sw.t = swNow(s.sw); s.sw.running = false; s.sw.stopped = true;
      say(t("Stopwatch stopped: {t}", { t: withUnit(fmt(reading(instr, s.sw.t).v, `.${decimals(instr.division)}f`), t(instr.unit)) }));
      renderStopwatches();
    } }, t("⏱ Stop"));
    return el("div", { class: "dm-sw", "data-instr": id }, el("span", {}, t(instr.label)), btn, out);
  }
  function renderStopwatches() {
    const s = S();
    for (const w of act.querySelectorAll(".dm-sw")) {
      const instr = instruments[w.dataset.instr];
      const running = !!(s.sw && s.sw.running);
      const tt = s.sw ? swNow(s.sw) : null;
      const r = tt === null ? null : reading(instr, tt);
      const text = r ? withUnit(fmt(r.v, `.${decimals(instr.division)}f`), t(instr.unit)) : "—";
      const out = w.querySelector("output");
      if (out.textContent !== text) out.textContent = text;
      w.querySelector("button").disabled = !running;
    }
  }
  const swRunning = () => { const s = S(); return !!(s && s.sw && s.sw.running); };
  const swRefuse = () => say(t("The stopwatch is running: stop it first (⏱ Stop); a hand stopwatch times the real flight, which cannot be paused"));

  // --- measuring ---------------------------------------------------------------------------------------------------------
  // a set-up value of the point shown: its header's parameters (what the run was made with), its grid values, the fixed
  // ones of the atlas (D6: never the slider)
  function setupValue(s, p) {
    const c = s.cur, h = c && c.pt.W ? c.pt.W.header.params || {} : {};
    if (p in h) return h[p];
    if (c && p in (c.pt.values || {})) return c.pt.values[p];
    return (s.A.manifest.fixed || {})[p];
  }
  function readAll() {
    const s = S(), step = s.step, c = s.cur;
    const f = c && c.pt.W ? frameAt(c.pt.W, localT(c, s.clock)) : null;
    const meas = (f && f.meta.meas) || {};
    const readings = {};
    for (const id of step.instruments) {
      const i = instruments[id];
      if (!i) continue;
      if (i.manual) { readings[id] = s.sw && s.sw.stopped ? reading(i, s.sw.t) : null; continue; }
      const src = String(i.reads || "");
      if (src.startsWith("control:")) readings[id] = reading(i, setupValue(s, src.slice(8)));
      else {
        const v = meas[src];
        if (v === null || v === undefined || !eventReached(s, i, f)) {
          const m = ((c && c.pt.W && c.pt.W.header.measurables) || []).find((x) => x.id === src);
          return { refused: t("Nothing to measure yet: “{what}” has not been reached at this moment", { what: m ? t(m.label) : src }) };
        }
        readings[id] = reading(i, v);
      }
    }
    return { readings, f };
  }
  function measureNow() {
    const s = S();
    const why = measureBlock(s);
    if (why) { say(why); return; }
    const r = readAll();
    if (r.refused) { say(r.refused); return; }
    const row = { id: Date.now() + Math.random(), values: { ...s.cur.pt.values }, readings: r.readings, cols: rowOf(s.step.columns, r.readings) };
    const placed = placeRow(s.rows, row);
    s.rows = placed.rows;
    saveRows(STORE(kit.world, s.step.atlas), s.A.manifest.key, s.rows);
    const noTime = s.step.columns.some((c) => c.from && instruments[c.from] && instruments[c.from].manual && !row.cols[c.id]);
    const text = placed.replaced
      ? t("Row {n:d} replaced: this set-up was already measured; the bench repeats exactly, so a repeat is not a new independent point", { n: placed.n })
      : t("Measured: row {n:d}", { n: placed.n });
    say(noTime ? `${text}. ${t("No time in this row: the stopwatch was not stopped")}` : text);
    s.check = null;
    renderWork();
  }

  // --- the table, the plot, the fit, the law --------------------------------------------------------------------------------
  const colLabel = (c) => t(c.label);
  const colOf = (s, id) => s.step.columns.find((c) => c.id === id) || null;
  const cell = (c, x) => {
    if (!x) return "—";
    const i = c.from ? instruments[c.from] : null;
    return i ? readingText(i, x) : pm(x.v, x.e);
  };
  // a law's plot in words: «L, m against √h, m^½ — line through the origin y = b·x»
  const lawPlot = (s, law) => t("{y} against {x} — {fit}", { y: colLabel(colOf(s, law.y) || { label: law.y }), x: colLabel(colOf(s, law.x) || { label: law.x }), fit: FIT_LABEL()[law.model] || law.model });
  function renderWork() {
    const s = S(), step = s.step, cols = step.columns;
    const table = el("table", { class: "dm-table" },
      el("thead", {}, el("tr", {}, el("th", {}, "№"), cols.map((c) => el("th", {}, colLabel(c))), el("th", {}, ""))),
      el("tbody", {}, s.rows.map((r, j) => el("tr", {}, el("td", {}, String(j + 1)),
        cols.map((c) => el("td", { class: "mono" }, cell(c, r.cols[c.id]))),
        el("td", {}, el("button", { class: "dm-del", title: t("Delete this row"), "aria-label": t("Delete this row"), onclick: () => {
          s.rows.splice(j, 1); if (s.A) saveRows(STORE(kit.world, step.atlas), s.A.manifest.key, s.rows); s.check = null; renderWork(); } }, "✕"))))));
    const csvA = el("a", { class: "button", download: `${kit.world}_${step.id}.csv`, title: t("The table with the errors, as CSV") }, "⤓ CSV");
    csvA.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv(cols, s.rows, colLabel));
    const clear = el("button", { onclick: () => { if (!s.rows.length) return; s.rows = []; if (s.A) saveRows(STORE(kit.world, step.atlas), s.A.manifest.key, s.rows); s.check = null; renderWork(); } }, t("Clear the table"));
    const opt = (sel, v) => { sel.value = v; return sel; };
    const xs = opt(el("select", { "aria-label": t("x axis"), onchange: (e) => { s.x = e.target.value; s.check = null; renderWork(); } }, cols.map((c) => el("option", { value: c.id }, colLabel(c)))), s.x);
    const ys = opt(el("select", { "aria-label": t("y axis"), onchange: (e) => { s.y = e.target.value; s.check = null; renderWork(); } }, cols.map((c) => el("option", { value: c.id }, colLabel(c)))), s.y);
    const fits = (step.plot.fits || [step.plot.fit]).filter((m) => m && (m !== "power" || !kit.school));
    const fs = opt(el("select", { "aria-label": t("fit"), onchange: (e) => { s.model = e.target.value; s.check = null; renderWork(); } }, fits.map((m) => el("option", { value: m }, FIT_LABEL()[m] || m))), s.model);
    const cv = el("canvas", { class: "dm-plot", role: "img", "aria-label": t("{y} against {x}", { y: colLabel(colOf(s, s.y) || { label: s.y }), x: colLabel(colOf(s, s.x) || { label: s.x }) }) });
    // the fit on the rows that have both columns
    const pts = s.rows.map((r) => [r.cols[s.x], r.cols[s.y]]).filter(([a, b]) => a && b);
    s.res = null;
    let fitText = t("Measure at least {n:d} points to fit", { n: (FIT_MODELS[s.model] || { min: 2 }).min });
    try {
      if (s.x === s.y) fitText = t("Choose different columns for x and y");
      else if (pts.length) {
        s.res = fit(pts.map((p) => p[0].v), pts.map((p) => p[1].v), pts.map((p) => p[0].e), pts.map((p) => p[1].e), s.model);
        fitText = [FIT_LABEL()[s.model] + ":", ...Object.keys(s.res.params).filter((k) => k !== "yv").map((k) =>
          `${k === "xv" ? "x*" : k} = ${pm(s.res.params[k], s.res.sigma[k])}`),
        kit.school ? "" : Number.isFinite(s.res.chi2) && s.res.dof > 0 ? `χ²/dof = ${fmt(s.res.chi2 / s.res.dof, ".3g")}` : "",
        // the Birge scaling is shown, at school too (D4)
        s.res.scaled && Number.isFinite(s.res.birge) ? t("(errors enlarged ×{b}: the points scatter more than the instruments' errors)", { b: fmt(s.res.birge, ".2g") }) : "",
        ].filter(Boolean).join("  ");
      }
    } catch (e) { s.res = null; fitText = e.why === "points" || e.why === "singular" ? t("Measure more points at different set-ups to fit") : e.why === "positive" ? t("A power law needs positive values")
      : e.why === "converge" ? t("The fit with errors in x and y does not converge: look at the readings and the plot") : e.message; }
    // «Check against the law»: only on the plot of one of the step's laws (D4)
    const law = lawOf(s.laws, s.x, s.y, s.model);
    let lawBox = null;
    if (s.laws.length) {
      const why = !law ? t("The law is checked on its own plot: choose it below") : !s.res ? t("Measure more points at different set-ups to fit") : "";
      const checkBtn = el("button", { class: "primary dm-check-law", disabled: !!why, title: why, onclick: () => { checkLaw(law); renderWork(); } }, t("Check against the law"));
      const list = el("ul", { class: "dm-laws" }, s.laws.map((Lw) => {
        const on = Lw === law;
        return el("li", { class: on ? "on" : "" }, el("b", {}, t(Lw.label)), " — ", lawPlot(s, Lw), " ",
          on ? el("span", { class: "muted" }, t("(plotted)")) : el("button", { class: "link dm-law-plot", onclick: () => { s.x = Lw.x; s.y = Lw.y; s.model = Lw.model; s.check = null; renderWork(); } }, t("plot it")));
      }));
      lawBox = el("div", { class: "dm-law-box" }, el("div", { class: "dm-sub" }, t("The laws of this part")), list, checkBtn,
        !law ? el("div", { class: "muted dm-law-why" }, why) : null);
    }
    const checkOut = el("div", { class: "dm-law " + (s.check ? (s.check.ok ? "st-ok" : "st-bad") : ""), role: "status" }, s.check ? s.check.text : "");
    fill(work,
      el("div", { class: "dm-work-head" }, el("b", {}, t("Table")), el("span", { class: "grow" }), clear, csvA),
      el("div", { class: "dm-table-box" }, s.rows.length ? table : el("div", { class: "muted" }, t("No measurements yet: launch, then press «Measure»."))),
      el("div", { class: "dm-work-head" }, el("b", {}, t("Plot")), el("label", {}, "x ", xs), el("label", {}, "y ", ys), el("label", {}, t("fit") + " ", fs)),
      cv, el("div", { class: "dm-fit mono" }, fitText), lawBox, checkOut);
    requestAnimationFrame(() => drawPlot(cv, pts, s));
  }
  function checkLaw(law) {
    const s = S(), refs = (s.A && s.A.manifest.references) || {};
    const ref = law ? refs[law.reference] : null;
    const q = s.res && law ? quantity(s.res, law.quantity) : null;
    if (!law || !ref || !q) { s.check = { ok: false, text: t("No reference of this law in the step's atlas: it is built with the site (site/atlas.py).") }; return; }
    const v = verdict(s.res, q.value, q.sigma, ref.value);
    const unit = t(law.unit || ref.unit || "");
    const how = ref.kind === "engine" ? t("computed by the engine; there is no closed form") : t("closed form {law}", { law: t(ref.label) });
    const measured = t("{label} = {value}", { label: t(law.label), value: withUnit(pm(q.value, q.sigma), unit) });
    const lawText = t("law: {value} ({how})", { value: withUnit(fmt(ref.value, ".4g"), unit), how });
    let tail;
    if (v.refused === "birge") {
      tail = t("✗ no verdict: the points scatter {b} times more than their errors (more than {max:d} times), so this curve does not describe them; look at the readings, the axes and the fit",
        { b: fmt(s.res.birge, ".2g"), max: BIRGE_MAX });
    } else if (v.refused === "dof") tail = t("Measure more points at different set-ups to fit");
    else if (v.agrees) {
      tail = v.kind === "t" ? t("✓ agrees within {k} errors: the errors come from the scatter of the points, so the bound is Student's t for n − p = {n:d}", { k: fmt(v.k, ".3g"), n: v.dof })
        : t("✓ agrees within two errors");
    } else {
      tail = s.step.hint ? t("✗ does not agree: {hint}", { hint: t(s.step.hint) }) : t("✗ does not agree: look at the readings and the plot");
      if (v.kind === "t") tail += " " + t("(the bound: {k} errors, Student's t for n − p = {n:d})", { k: fmt(v.k, ".3g"), n: v.dof });
    }
    s.check = { ok: !!v.agrees, law: law.reference, k: v.k, kind: v.kind, text: `${measured} — ${lawText} ${tail}` };
  }
  function drawPlot(cv, pts, s) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth || 300, H = cv.clientHeight || 220;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    const g = cv.getContext("2d");
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.fillStyle = css("--canvas") || "#fff"; g.fillRect(0, 0, W, H);
    const ink = css("--ink") || "#222", muted = css("--muted") || "#888", acc = css("--accent") || "#1c5fb8";
    const cx = colOf(s, s.x), cy = colOf(s, s.y);
    const xsV = pts.flatMap((p) => [p[0].v - p[0].e, p[0].v + p[0].e]), ysV = pts.flatMap((p) => [p[1].v - p[1].e, p[1].v + p[1].e]);
    // the axes: the data's range, with the origin when it is near (or the fit passes through it); review EX1-screens F11
    const span = (vals, origin) => {
      let a = Math.min(...vals), b = Math.max(...vals);
      if (origin || (a >= 0 && a <= 0.35 * b) || (b <= 0 && b >= 0.35 * a)) { a = Math.min(a, 0); b = Math.max(b, 0); }
      const pad = 0.06 * ((b - a) || Math.abs(b) || 1);
      return [a === 0 ? 0 : a - pad, b === 0 ? 0 : b + pad];
    };
    let [x0, x1] = pts.length ? span(xsV, s.model === "line0") : [0, 1];
    let [y0, y1] = pts.length ? span(ysV, s.model === "line0") : [0, 1];
    if (!(x1 > x0)) { x0 -= 1; x1 += 1; }
    if (!(y1 > y0)) { y0 -= 1; y1 += 1; }
    const L0 = 48, R = 12, T0 = 10, B = 34;
    const px = (x) => L0 + (x - x0) / (x1 - x0) * (W - L0 - R), py = (y) => H - B - (y - y0) / (y1 - y0) * (H - T0 - B);
    g.strokeStyle = muted; g.lineWidth = 1; g.font = "11px system-ui, sans-serif"; g.fillStyle = muted;
    g.beginPath(); g.moveTo(L0, T0); g.lineTo(L0, H - B); g.lineTo(W - R, H - B); g.stroke();
    const ticks = (a, b) => { const st = 10 ** Math.floor(Math.log10((b - a) / 4)); const m = [1, 2, 5, 10].find((k) => (b - a) / (k * st) <= 6) * st; const out = []; for (let v = Math.ceil(a / m) * m; v <= b + 1e-12; v += m) out.push(Number(v.toPrecision(10))); return out; };
    g.textAlign = "center";
    for (const v of ticks(x0, x1)) { g.fillText(fmt(v, ".3g"), px(v), H - B + 14); g.beginPath(); g.moveTo(px(v), H - B); g.lineTo(px(v), H - B + 3); g.stroke(); }
    g.textAlign = "right";
    for (const v of ticks(y0, y1)) { g.fillText(fmt(v, ".3g"), L0 - 4, py(v) + 4); g.beginPath(); g.moveTo(L0 - 3, py(v)); g.lineTo(L0, py(v)); g.stroke(); }
    g.fillStyle = ink; g.textAlign = "right"; g.fillText(cx ? colLabel(cx) : "", W - R, H - 4);
    g.textAlign = "left"; g.fillText(cy ? colLabel(cy) : "", L0 + 4, T0 + 10);
    if (s.res && pts.length) {  // the fitted curve over the measured range only (a line through the origin from 0)
      const xa = Math.min(...pts.map((p) => p[0].v)), xb = Math.max(...pts.map((p) => p[0].v));
      const from = s.model === "line0" ? Math.min(0, xa) : xa;
      g.save(); g.beginPath(); g.rect(L0, T0, W - L0 - R, H - T0 - B); g.clip();
      g.strokeStyle = acc; g.lineWidth = 1.5; g.beginPath();
      let pen = false;
      for (let k = 0; k <= 100; k++) { const x = from + (xb - from) * k / 100, y = s.res.f(x); if (!Number.isFinite(y)) { pen = false; continue; } const X = px(x), Y = py(y); if (pen) g.lineTo(X, Y); else g.moveTo(X, Y); pen = true; }
      g.stroke(); g.restore();
    }
    g.strokeStyle = ink; g.fillStyle = ink; g.lineWidth = 1;
    for (const [a, b] of pts) {
      const X = px(a.v), Y = py(b.v);
      g.beginPath(); g.moveTo(px(a.v - a.e), Y); g.lineTo(px(a.v + a.e), Y); g.moveTo(X, py(b.v - b.e)); g.lineTo(X, py(b.v + b.e)); g.stroke();
      g.beginPath(); g.arc(X, Y, 3, 0, 2 * Math.PI); g.fill();
    }
  }

  // --- time (one shot at a time; ▶ Launch starts it at t = 0) -----------------------------------------------------------------
  function playPressed() {
    const s = S(), c = s.cur;
    if (!c || !c.pt.W) return;
    if (swRunning()) { swRefuse(); return; }
    if (L.playing) { L.playing = false; kit.dirty(); return; }
    if (c.launchedAt === null || ended(c, s.clock)) {
      c.launchedAt = s.clock;
      // the manual stopwatch starts with the launch and runs on the wall clock until it is pressed
      s.sw = s.step.instruments.some((id) => (instruments[id] || {}).manual) ? { running: true, stopped: false, t0: performance.now(), t: 0 } : null;
    }
    L.playing = true; L.wall = performance.now(); kit.dirty();
  }
  function resetPressed() { const s = S(); L.playing = false; if (s.cur) s.cur.launchedAt = null; s.sw = null; kit.dirty(); }
  function scrub(i) {
    const s = S(), c = s.cur;
    if (!c || !c.pt.W) return;
    if (swRunning()) { swRefuse(); kit.dirty(); return; }  // the time bar goes back to the time shown at the next frame
    const F = c.pt.W.frames, f = F[Math.max(0, Math.min(i, F.length - 1))];
    if (c.launchedAt === null) c.launchedAt = s.clock;
    s.clock = c.launchedAt + f.t;
    L.playing = false; kit.dirty();
  }

  // --- drawing: the view at the frame shown, the instruments over it ----------------------------------------------------------
  function render() {
    const s = S();
    if (!s || !s.cur || !s.cur.pt.W) return;
    const c = s.cur, W = c.pt.W, F = W.frames;
    const i = frameIndexAt(F, localT(c, s.clock)), f = F[i] || null, tt = f ? f.t : 0;
    showAt(view, W, tt);
    kit.self.frame = f;
    if (f) { try { view.render(f.meta, f.t, f.blobs); } catch (e) { console.error(e); } }
    drawInstruments(s, f);
    renderStopwatches();
    bar.update({ playing: L.playing, i: Math.max(0, i), max: Math.max(0, F.length - 1), text: `${secs(tt)} / ${secs(c.pt.tEnd)}`,
      launch: c.launchedAt === null || ended(c, s.clock) });
  }
  // the tape along the ground from the launch point, the ruler up to the launch height, the protractor at the launcher:
  // placed by the view's own mapping (worldToPx); without one, nothing is drawn over the view
  function drawInstruments(s, f) {
    while (svg.firstChild) svg.firstChild.remove();
    const cv = view.center.querySelector("canvas");
    if (!view.worldToPx || !cv) return;
    const sr = stage.getBoundingClientRect(), cr = cv.getBoundingClientRect();
    const ox = cr.left - sr.left, oy = cr.top - sr.top;
    const P = (x, y) => { const [a, b] = view.worldToPx([x, y]); return [a + ox, b + oy]; };
    const NS = "http://www.w3.org/2000/svg";
    const add = (tag, attrs, text) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v)); if (text) e.textContent = text; svg.append(e); return e; };
    const head = s.cur.pt.W.header, box = (head.scene && head.scene.box) || [[0, 0], [1, 1]];
    // where the instruments go: the view's own anchors (design §2.4; S03: {launch: [x, y], floor: y, angle, landing}),
    // else the launch point at x = 0 on the ground y = 0 at the header's launcher
    let an = null;
    try { an = view.anchors ? view.anchors() : null; } catch (e) { an = null; }
    const floor = an && Number.isFinite(an.floor) ? an.floor : 0;
    const launch = an && an.launch ? an.launch : [0, head.launcher ? Number(head.launcher.h) || 0 : 0];
    const angle = an && Number.isFinite(an.angle) ? an.angle : head.launcher ? Number(head.launcher.angle) || 0 : 0;
    const x0 = launch[0], x1 = box[1][0];
    let nTape = 0;
    for (const id of s.step.instruments) {
      const i = instruments[id];
      if (!i || i.manual) continue;
      const src = String(i.reads || "");
      if (i.kind === "ruler" && !src.startsWith("control:")) {  // a tape on the floor from the launch point
        const off = 6 + 16 * nTape++;  // a second tape (S03 part 3: the grey ball's range) on its own line
        const [a, b] = P(x0, floor), [c] = P(x1, floor);
        add("line", { x1: a, y1: b + off, x2: c, y2: b + off, class: "tape" });
        const step = niceStep(Math.max(1e-9, x1 - x0) / 10);
        const [p1] = P(x0 + step, floor), every = Math.max(1, Math.ceil(30 / Math.max(1, Math.abs(p1 - a))));  // labels ≥ 30 px apart
        let k = 0;
        for (let x = 0; x0 + x <= x1 + 1e-9; x += step, k++) {
          const [u] = P(x0 + x, floor);
          add("line", { x1: u, y1: b + off - 4, x2: u, y2: b + off + 4, class: "tick" });
          if (nTape === 1 && k % every === 0) add("text", { x: u, y: b + off + 16, class: "lbl" }, fmt(Number(x.toPrecision(6)), ".3g"));
        }
        const v = f && f.meta.meas ? f.meta.meas[src] : null;
        if (v !== null && v !== undefined && eventReached(s, i, f)) { const [u] = P(x0 + v, floor); add("line", { x1: u, y1: b + off - 12, x2: u, y2: b + off + 6, class: "mark" }); }
      } else if (i.kind === "ruler") {  // a set-up height: the ruler upright at the launch point, from the floor
        const [a, b] = P(x0, floor), [, c] = P(x0, launch[1]);
        add("line", { x1: a - 8, y1: b, x2: a - 8, y2: c, class: "tape" });
        const hgt = launch[1] - floor, step = niceStep(Math.max(hgt, 0.1) / 5);
        for (let y = 0; y <= hgt + 1e-9; y += step) { const [, v] = P(x0, floor + y); add("line", { x1: a - 12, y1: v, x2: a - 4, y2: v, class: "tick" }); }
      } else if (i.kind === "protractor") {
        const [a, b] = P(launch[0], launch[1]), r = 34;
        add("path", { d: `M ${a + r} ${b} A ${r} ${r} 0 0 0 ${a} ${b - r}`, class: "tape" });
        add("line", { x1: a, y1: b, x2: a + r * Math.cos(angle * Math.PI / 180), y2: b - r * Math.sin(angle * Math.PI / 180), class: "mark" });
      }
    }
  }
  // an instrument bound to an event (S03 part 3: the tape of the grey ball reads only after "companion_landing"): has the
  // event (by kind or name, as a stop rule matches it) happened by the frame shown?
  function eventReached(s, i, f) {
    if (!i.event) return true;
    const tt = f ? f.t : 0, eps = 1e-12 * Math.abs(tt);
    return s.cur.pt.W.events.some((e) => (e.kind === i.event || e.name === i.event) && (e.t ?? 0) <= tt + eps);
  }
  const niceStep = (x) => { const p = 10 ** Math.floor(Math.log10(x)); return [1, 2, 5, 10].find((k) => k * p >= x) * p; };

  const API = {
    tick(now) {
      const s = S();
      const dt = Math.min(0.25, (now - L.wall) / 1000);
      if (s && s.sw && s.sw.running) renderStopwatches();
      if (L.playing && s && s.cur) {
        L.wall = now;
        s.clock += dt * L.rate;
        if (s.cur.launchedAt === null || ended(s.cur, s.clock)) L.playing = false;
        this.dirty = true;
      } else L.wall = now;
      if (this.dirty) { this.dirty = false; render(); }
    },
    show() { this.dirty = true; },
    hide() { L.playing = false; },
    key(e) {
      if (e.key === " ") { e.preventDefault(); playPressed(); }
      else if (e.key === "Home") { e.preventDefault(); resetPressed(); }
      else if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        const s = S(); if (!s.cur || !s.cur.pt.W) return;
        scrub(frameIndexAt(s.cur.pt.W.frames, localT(s.cur, s.clock)) + (e.key === "ArrowRight" ? 1 : -1));
      }
    },
    drawerKey() {
      const s = S(), c = s && s.cur, W = c && c.pt.W;
      if (!W) return "none";
      const tt = (frameAt(W, localT(c, s.clock)) || {}).t ?? 0;
      let n = 0;
      for (const vs of W.checks.values()) for (const x of vs) if ((x.t ?? 0) <= tt) n++;
      return `${L.k}|${c.pt.i}|${n}`;
    },
    drawer() {
      const s = S(), c = s && s.cur, W = c && c.pt.W;
      const tt = W ? (frameAt(W, localT(c, s.clock)) || {}).t ?? 0 : 0;
      const m = s && s.A ? s.A.manifest : {};
      const passport = [[t("Point"), c ? valuesText(s.A.controls, c.pt.values) : "—"], [t("Atlas"), `${m.atlas || ""} · ${t("key")} ${m.key || ""}`],
        [t("Code"), m.code_hash], [t("Random seed"), m.seed], [t("The atlas was built"), when(((s && s.A && s.A.entry) || {}).made ?? m.made)]];
      if (s && s.fromSite) passport.push([t("From"), t("the public site")]);
      return kit.howWeKnow({ W, tt, passport, eventTimes: false,
        note: t("Computed by the engine when the site was built: every slider position is such a point; nothing between them is drawn.") });
    },
    liveBody() { const s = S(); return s && s.A ? { preset: s.A.manifest.preset, params: { ...(s.A.manifest.fixed || {}), ...s.values } } : null; },
  };
  window.__lfLab = { state: L, step: () => S(), rows: () => S().rows, check: () => S().check, fit: () => S().res };
  if (steps.length) await openStep(0);
  else fill(card, el("p", { class: "muted" }, t("This lab has no steps yet.")));
  return API;
}
