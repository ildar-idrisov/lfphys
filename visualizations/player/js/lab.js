// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The Lab work screen (design lfphys/sources/explore_2026-11-14_design.md §2.3, §3.5; revised by EX2 §1.4, §5 F6, F8, F9):
// a narrow bench (the owner, 2026-11-18: «что-то вроде стенда для проведения эксперимента, который можно проводить разными
// путями»). Steps in order, each on its own atlas (lab.<step>) or on an Explore screen's (atlas: <screen>, F9), as
// Explore uses its own, so it works on the public site. The step card (part k of n, the goal, the step's controls, its
// instruments, «Measure», its overlays and readouts), the instruments drawn over the view through the view's worldToPx
// (an SVG layer), the table (kept per step in this browser; a row can be deleted, the table cleared and exported as CSV
// with the errors), the plot of any two columns with error bars and the chosen fit, and the fit's output.
//
// An instrument does not compute physics: it reads a value the run computed (a measurable at the cursor, or a set-up
// value "control:<param>" of the point shown) and rounds it to its division; the reading carries the declared error (by
// default half a division), a count its √N, a readout with the run's σ that σ. The formula columns and the fit are
// arithmetic and statistics on the readings (expr.js, fit.js).
//
// Nothing is hidden and nothing is judged (EX2 §5 F6): the drawer is Explore's, with «Computed for this bench» (the
// world's computed values for the bench: the step's laws' references, with their quantity and columns, never beside the
// student's fit); the fit prints its parameters with the σ from the declared errors, χ², dof, χ²/dof, the p-value and
// the Birge ratio, and, when χ²/dof > 1, the σ scaled by that ratio on a line of its own (at school the parameters with
// their errors only). «Check against the law» and its verdict (EX1 D4) are withdrawn. The teacher's variant
// (&variant=<id>, F8) preselects the steps' controls; nothing is locked.
//
// What keeps the bench honest (review EX1-screens F1, F4, F5; integrator D5, D6):
//  - a point's reply is applied only when it is still the one asked for (a request counter); every instrument reads
//    the shown point's own values (its header's parameters, its frames), never the slider; «Measure» is refused while
//    the slider's set-up is not the one shown (loading, refused or failed);
//  - one row per set-up: «Measure» on a set-up already in the table replaces that row and says so (the bench repeats
//    exactly: a repeat is not an independent point); the table is kept with the atlas's key and dropped when the atlas
//    was rebuilt;
//  - a manual stopwatch starts with the launch and runs on the wall clock until the student stops it: at real speed
//    only («slow» is refused), and while it runs the flight cannot be paused, scrubbed or stepped (it times the real
//    flight with the student's reaction, as a hand-held one does).
import { openAtlas } from "./atlas.js";
import { ExprError, Undefined, evaluate as evalExpr, parse as parseExpr } from "./expr.js";
import { MODELS as FIT_MODELS, fit, pValueText } from "./fit.js";
import { t } from "./i18n.js";
import { SLOW, controlLabel, controlRow, csvFormat, ended, expandValues, localT, measText, pmText, secs, speedOf, timeLabel, valueText, valuesText, when } from "./explore.js";
import { frameAt, frameIndexAt, showAt } from "./record_core.js";
import { css, el, fill, fmt } from "./ui.js";

// --- readings (pure: lab.test.mjs) ----------------------------------------------------------------------------------------
export const decimals = (d) => { const s = String(d); if (s.includes("e-")) return Number(s.split("e-")[1]) + (s.split("e-")[0].split(".")[1] || "").length; return (s.split(".")[1] || "").length; };
// a value read by an instrument: division × round(value / division), its error the declared one (half a division).
// A counter (EX2 §5 F4) reads a whole count N: its error √N with error "poisson" (one count for N = 0: a finite sample
// cannot exclude a rare event), or its declared number (0: an exact count). A readout with `sigma` takes the run's own
// standard error at the cursor (`sigmaValue`, the measurable it names): its division is then only the display precision.
export function reading(instr, value, sigmaValue) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null;
  if (instr.kind === "counter") {
    const n = Math.round(Number(value));
    if (n < 0) return null;
    return { v: n, e: instr.error === "poisson" ? (n > 0 ? Math.sqrt(n) : 1) : Number(instr.error ?? 0) };
  }
  const d = Number(instr.division);
  const v = Number((Math.round(Number(value) / d) * d).toFixed(Math.min(15, decimals(d))));
  if (instr.sigma) {
    if (sigmaValue === null || sigmaValue === undefined || !(Number(sigmaValue) >= 0)) return null;
    return { v: Object.is(v, -0) ? 0 : v, e: Number(sigmaValue) };
  }
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
// a formula column's parsed formula (expr.js), parsed once per text; the registry parsed it too (only earlier columns)
const PARSED = new Map();
function formula(text) {
  if (!PARSED.has(text)) PARSED.set(text, parseExpr(text));
  return PARSED.get(text);
}
// a table row from the instruments' readings ({instrument id: {v, e}}): every column of the step. A formula column
// {id, label, expr} (EX2 §5 F5) is evaluated on the row's earlier columns with its error propagated (expr.js); an
// undefined value (√ of a negative number, a division by 0, an empty input …) leaves the cell empty (null) and, when
// `why` is given, its reason there ({column id: reason code}, REASONS of expr.js)
export function rowOf(columns, readings, why = null) {
  const cols = {};
  for (const c of columns) {
    if (c.from) cols[c.id] = readings[c.from] || null;
    else if (c.of) cols[c.id] = derived(c.op, cols[c.of]);
    else if (c.expr) {
      try {
        const f = formula(c.expr);
        const r = evalExpr(f, new Map(Object.entries(cols).map(([k, x]) => [k, x])));
        // an exact result (no input carries an error) that is zero up to the rounding of its inputs is zero: 3 cos 2Δ −
        // cos 6Δ at Δ = 45° is 0, not 3.7·10⁻¹⁶ («0.000000000000»; review R2-P F13)
        const scale = Math.max(0, ...f.names.map((k) => Math.abs((cols[k] || {}).v || 0)));
        cols[c.id] = { v: r.e === 0 && Math.abs(r.v) <= 1e-12 * scale ? 0 : r.v, e: r.e };
      } catch (e) {
        cols[c.id] = null;
        if (why) why[c.id] = e instanceof Undefined ? e.reason : e instanceof ExprError ? "syntax" : "not_finite";
      }
    }
  }
  return cols;
}
// why a formula's cell is empty, in the viewer's language (expr.js REASONS)
export function whyText(reason) {
  return ({
    sqrt_negative: t("the square root of a negative number"), division_by_zero: t("a division by zero"),
    log_nonpositive: t("the logarithm of a number that is not positive"), asin_domain: t("arcsine of a number outside −1 … 1"),
    acos_domain: t("arccosine of a number outside −1 … 1"), power: t("a power of a negative number with a fractional exponent"),
    not_finite: t("the value is not a finite number"), missing: t("a column it needs is empty"),
    error_undefined: t("its error is undefined here (an infinite derivative)"), syntax: t("the formula cannot be read"),
  })[reason] || t("the value is undefined here");
}
// the CSV's format of the viewer's language (explore.js csvFormat: «;» and the decimal comma in Russian, review R2-P
// F18), and its link with the UTF-8 byte order mark (Excel reads a CSV without it in the system's 8-bit code page)
export { csvFormat };
export const csvHref = (text) => "data:text/csv;charset=utf-8," + encodeURIComponent("\ufeff" + text);
// CSV with the errors: a header of the set-up's columns (the step's controls no instrument reads: their labels with
// their units; review R2-P F7) and of the columns' labels (and «σ …»), one line per row; numbers as plain decimals in the
// format's decimal sign, a set-up value that is no number by its name; an empty cell (no reading, or a formula
// undefined there) is empty in both. setup: [{label, text(v) → string or number, param}]
export function csv(columns, rows, label = (c) => c.id, { sep = ",", dec = ".", setup = [] } = {}) {
  const q = (s) => (s.includes('"') || s.includes("\n") || s.includes(sep) ? `"${s.replace(/"/g, '""')}"` : s);
  const n = (x) => (dec === "." ? String(x) : String(x).replace(".", dec));
  const head = [...setup.map((u) => q(u.label)), ...columns.flatMap((c) => [q(label(c)), q("σ " + label(c))])];
  const lines = rows.map((r) => [...setup.map((u) => { const v = (r.values || {})[u.param]; if (v === undefined) return ""; const x = u.text(v); return typeof x === "number" ? n(x) : q(String(x)); }),
    ...columns.flatMap((c) => { const x = r.cols[c.id]; return x && x.v !== null && x.v !== undefined ? [n(x.v), n(x.e)] : ["", ""]; })].join(sep));
  return [head.join(sep), ...lines].join("\n") + "\n";
}
// a value to four significant digits, its trailing zeros kept («1.000» next to «0.4472»: V52 (y))
export function sig4(v) {
  if (!Number.isFinite(v)) return "—";
  const r = Number(v.toPrecision(4));  // rounded first: 9.9996 is «10.00», not «10.000»
  if (r === 0) return fmt(0, ".3f");
  return fmt(r, `.${Math.min(12, Math.max(0, 3 - Math.floor(Math.log10(Math.abs(r)))))}f`);
}
// a value with its error: the error to two significant digits, the value to the same decimal place; an exact value
// (error 0, e.g. √h of a height the stand sets exactly) to four significant digits, without «± 0»
export function pm(v, e) {
  if (!Number.isFinite(v)) return "—";
  if (!(e > 0) || !Number.isFinite(e)) return sig4(v);
  const [a, b] = pmText(v, e);  // the error rounded to two significant digits first (0.0996 → «0.10»; 1234 → «1200»)
  return `${a} ± ${b}`;
}
// a reading as the instrument shows it, the value and its error to the same decimals (RULES §10; review R2-P F14: the
// error was written «.2g», «0.74 ± 0.1», «−0.0349 ± 0.03»): a declared error to the decimals of its division or of the
// error, whichever is finer («0.600 ± 0.005», not «0.60 ± 0.005»; review EX1-screens F14; «0.74 ± 0.10»); the run's
// own σ (a readout with `sigma`, whose division is only the display precision) to its two significant digits
// («−0.035 ± 0.030», «1.000 ± 0.015»); an exact reading (error 0: the stand's heights) to its division's decimals,
// without «± 0» («0.20»; V52 (y))
export function readingText(instr, x) {
  if (instr.kind === "counter") return x.e > 0 ? `${fmt(x.v, "d")} ± ${fmt(x.e, ".2g")}` : fmt(x.v, "d");  // a count
  if (!(x.e > 0)) return fmt(x.v, `.${Math.min(12, decimals(instr.division))}f`);
  if (instr.sigma) { const [a, b] = pmText(x.v, x.e); return `${a} ± ${b}`; }
  const n = Math.min(12, Math.max(decimals(instr.division), decimals(x.e)));
  return `${fmt(x.v, `.${n}f`)} ± ${fmt(x.e, `.${n}f`)}`;
}
// an instrument in the step's list: its division and its error, or, for an exact one (error 0), its own reason
// («exact: the stand sets the chute's height at its marks»), never «error ±0» (V52 (y))
export function instrumentText(i) {
  if (i.kind === "counter") {  // EX2 §5 F4: a count and its error
    if (i.error === "poisson") return t("counts; error √N (a count of 0 has the error of one count)");
    return Number(i.error) > 0 ? t("counts; error ±{e}", { e: fmt(Number(i.error), ".6g") }) : t("counts; an exact count");
  }
  const d = withUnit(fmt(i.division, ".6g"), t(i.unit));
  if (i.sigma) return t("division {d}; error: the run's own standard error", { d });
  const e = i.error ?? i.division / 2;
  if (e > 0) return t("division {d}, error ±{e}", { d, e: withUnit(fmt(e, ".6g"), t(i.unit)) });
  return i.error_note ? t("division {d}; exact: {why}", { d, why: t(i.error_note) }) : t("division {d}; exact", { d });
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
// «Computed for this bench» (EX2 §5 F6 (d)): a step's laws with the world's computed values (the atlas's manifest's
// "references", by the law's id, or "<step>/<law>" on an Explore screen's atlas, F9), in words: the quantity, the columns
// it belongs to, the value with its unit, the formula or the engine's method. [{text, how, law, value}]
export function computedFor(step, references, colLabel = (id) => id) {
  const refs = references || {};
  const Q = { slope: t("slope"), intercept: t("intercept"), vertex: t("vertex"), exponent: t("exponent") };
  return (step.laws || []).map((law) => {
    const r = refs[step.shared ? `${step.id}/${law.reference}` : law.reference];
    if (!r) return null;
    const unit = t(law.unit || r.unit || "");
    return { text: t("{quantity} of {y} against {x}: {value}; {label}", { quantity: Q[law.quantity] || law.quantity,
      y: colLabel(law.y), x: colLabel(law.x), value: withUnit(fmt(r.value, ".6g"), unit), label: t(r.label) }),
      how: r.how ? t(r.how) : "", law: law.reference, value: r.value };
  }).filter(Boolean);
}
// the fit's output (EX2 §5 F6 (c)), as lines of text: the model and its parameters with the σ from the declared errors;
// at standard also χ², dof, χ²/dof, p and the Birge ratio, and, when χ²/dof > 1, the σ scaled by that ratio on a line of
// its own; without declared errors, that the σ come from the scatter. No verdict. The p is printed from ln p (EX2 §5
// F11: «3.05·10⁻²¹⁷¹³⁴» for χ² = 10⁶ on 7 degrees of freedom, never «0»).
export function fitLines(res, label, school) {
  const keys = Object.keys(res.params).filter((k) => k !== "yv");
  const name = (k) => (k === "xv" ? "x*" : k);
  const lines = [`${label}: ${keys.map((k) => `${name(k)} = ${pm(res.params[k], res.sigmaDeclared[k])}`).join(", ")}`];
  if (res.unit) { lines.push(t("(no declared errors: the σ come from the scatter of the points)")); return lines; }
  if (school) return lines;
  const ratio = res.dof > 0 ? res.chi2 / res.dof : NaN;
  lines.push(t("χ² = {chi2}, dof = {dof:d}, χ²/dof = {ratio}, p = {p}, Birge ratio √(χ²/dof) = {birge}", {
    chi2: fmt(res.chi2, ".4g"), dof: res.dof, ratio: fmt(ratio, ".3g"), p: pValueText(res.lnp), birge: fmt(res.birge, ".3g") }));
  // the σ scaled by the Birge ratio, when χ²/dof > 1 and they differ as written (a ratio of 1.0008 changes no digit:
  // review R2-P nits)
  const scaled = keys.map((k) => `${name(k)} = ${pm(res.params[k], res.sigmaScaled[k])}`).join(", ");
  if (res.birge > 1 && scaled !== keys.map((k) => `${name(k)} = ${pm(res.params[k], res.sigmaDeclared[k])}`).join(", ")) {
    lines.push(t("σ scaled by the Birge ratio: {values}", { values: scaled }));
  }
  return lines;
}

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
function saveRows(key, atlasKey, rows) { try { browserStorage().setItem(key, JSON.stringify({ key: atlasKey, rows })); } catch (e) { /* private mode: the table lives in the page */ } }
// this browser's storage, or a storage that keeps nothing when the browser refuses it: reading the global itself throws
// when site data are blocked or in a sandboxed frame (review R2-P F4: Lab work did not open, «The operation is insecure»)
export function browserStorage() {
  try { const s = window.localStorage; if (s) return s; } catch (e) { /* refused: below */ }
  return { getItem: () => null, setItem: () => {}, removeItem: () => {} };
}

// the plot's ticks on [a, b]: multiples of a round step (1, 2 or 5 × 10ⁿ), each computed from its index (not by adding
// the step, whose rounding errors made the zero tick «2.78·10⁻¹⁷»; review R2-P F12), a tick within a millionth of a step
// of zero exactly 0; at most 12 (a range a few ulps wide no longer loops: review R2-P nits)
export function plotTicks(a, b) {
  if (!(b > a) || !Number.isFinite(a) || !Number.isFinite(b)) return [];
  const st = 10 ** Math.floor(Math.log10((b - a) / 4));
  const m = [1, 2, 5, 10].find((k) => (b - a) / (k * st) <= 6) * st;
  if (!(m > 0) || !Number.isFinite(m)) return [];
  const out = [], k0 = Math.ceil(a / m - 1e-9);
  for (let j = 0; j <= 12; j++) {
    const v = (k0 + j) * m;
    if (v > b + 1e-9 * m) break;
    out.push(Math.abs(v) < 1e-6 * m ? 0 : Number(v.toPrecision(10)));
  }
  return out;
}

const FIT_LABEL = () => ({ line0: t("line through the origin y = b·x"), line: t("line y = a + b·x"), quadratic: t("parabola y = c0 + c1·x + c2·x²"), power: t("power law y = A·x^p") });

// the teacher's variant of the task (EX2 §5 F8 (b)): «&variant=<id>» in the address names one of the task sheet's
// variants; its values preselect the steps' controls (on their grids); nothing is locked
export function variantOf(worksheet, id) {
  if (!id || !worksheet) return null;
  return (worksheet.variants || []).find((v) => v.id === id) || null;
}

export async function create(host, kit, spec) {
  const steps = spec.steps || [], instruments = spec.instruments || {};
  const L = { k: 0, st: [], playing: false, wall: 0, rate: 1 };
  const V = variantOf(spec.worksheet, new URLSearchParams(location.search).get("variant"));
  // a table per step: a step on an Explore screen's atlas (F9) keeps its own, apart from another step on the same atlas
  const storeKey = (step) => STORE(kit.world, step.shared ? `${step.atlas}.${step.id}` : step.atlas);
  const view = kit.newView();
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "dm-instr");
  svg.setAttribute("aria-hidden", "true");
  const stage = el("div", { class: "dm-stage" }, view.center, svg);
  const card = el("div", { class: "dm-side dm-card" });
  // a step whose points carry modifications (a law parameter in its preset or fixed: standard only) says so on its card
  // and in the top bar, as Explore does (EX2 §5 F6)
  const modBox = el("div", { class: "dm-mod dm-lab-mod", role: "status", hidden: true });
  const work = el("div", { class: "dm-work" });
  // a step's readouts (EX2 §5 F6 (b)): the measurables it names, with their errors and references, as Explore's
  const readBox = el("div", { class: "dm-readouts dm-lab-readouts" });
  // a step's overlays (F6 (b)): the view's, those the step names (all when it names none), the view's defaults
  const overlaysOf = (step) => {
    const ovl = (view.overlays || []).filter((o) => !(step.overlays || []).length || step.overlays.includes(o.id));
    return ovl.length ? el("details", { class: "dm-overlays" }, el("summary", {}, t("Show")), ovl.map((o) => {
      const cb = el("input", { type: "checkbox", checked: o.on ?? !!o.default, "data-overlay": o.id, onchange: () => { o.on = cb.checked; if (view.setOverlay) view.setOverlay(o.id, cb.checked); } });
      return el("label", { class: "dm-check" }, cb, " ", t(o.label));
    })) : null;
  };
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
      res: null, msg: "", fromSite: !!src.fromSite };
    if (src.entry) {
      try {
        S.A = await openAtlas(kit.world, src.entry, { base: src.base });
      } catch (e) { S.why = t("This step's atlas could not be loaded: {why}", { why: e.message }); }
    }
    if (S.A) {
      S.A.controls = S.A.controls.map((c) => ({ ...((step.controls || []).find((x) => x.param === c.param) || {}), ...c }));
      S.values = { ...S.A.defaults };
      const pre = V && V.values ? V.values[step.id] || {} : {};  // the teacher's variant (F8): on the grid, unlocked
      for (const c of S.A.controls) if (c.param in pre && c.values.some((x) => x === pre[c.param])) S.values[c.param] = pre[c.param];
      const got = loadRows(browserStorage(), storeKey(step), S.A.manifest.key);
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
      // an exact instrument's reason is its error's place (instrumentText); another's note goes under it
      return el("li", {}, el("b", {}, t(i.label)), " — ", instrumentText(i),
        i.error_note && (i.error ?? i.division / 2) > 0 ? el("div", { class: "muted" }, t(i.error_note)) : null);
    }));
    const swBox = step.instruments.filter((id) => instruments[id] && instruments[id].manual).map((id) => stopwatchWidget(id, instruments[id]));
    const measure = el("button", { class: "primary dm-measure", onclick: () => measureNow() }, t("Measure"));
    const msg = el("div", { class: "dm-msg", role: "status" }, s.msg);
    fill(act, swBox, measure, msg);
    fill(card, nav, modBox,
      el("div", { class: "dm-part" }, t("Part {k:d} of {n:d}: {title}", { k: L.k + 1, n: steps.length, title: t(step.title) })),
      el("p", { class: "dm-goal" }, t(step.goal)),
      s.why ? el("p", { class: "dm-missing" }, s.why) : null,
      s.fromSite ? el("p", { class: "muted dm-from-site" }, t("This step's atlas comes from the public site: this server has no current local copy (the same version of the world).")) : null,
      el("div", { class: "dm-ctls" }, ctlRows.map((r) => r.el)),
      // «Measure» right under the controls, so that a set-up and its measurement are on the screen together at 1280×800
      // (review R2-P F11: below the list of instruments it was never on the screen with u37's or u34's controls)
      el("div", { class: "dm-act-slot" }),
      el("div", { class: "dm-sub" }, t("Instruments")), instrList,
      overlaysOf(step), readBox,
      el("p", { class: "dm-ws" }, el("a", { href: kit.worksheetHref(), target: "_blank" }, t("The task sheet (print) →"))));
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
      say(s.failed, s); if (s === S()) renderMeasure(); return;
    }
    if (seq !== s.seq) return;  // a newer choice came first: this reply is not the one asked for (D6)
    s.pending = false;
    s.A.prefetch(s.values);
    if (pt.state === "refused") { s.refused = t(pt.refusal); say(s.refused, s); if (s === S()) renderMeasure(); return; }
    say("", s);
    s.cur = { pt, launchedAt: null }; s.sw = null;
    // the reply of a step that is no longer shown (the student opened another part meanwhile) changes only that step's
    // state: not the message, the playback or the buttons of the part shown (review R2-P, suspicion on pick())
    if (s !== S()) return;
    L.playing = false;
    renderStopwatches(); renderMeasure();
    kit.dirty();
  }
  // a message of a step (by default the one shown): kept with its state, written on the card only when it is shown
  function say(text, s = S()) { s.msg = text; if (s !== S()) return; const m = act.querySelector(".dm-msg"); if (m) m.textContent = text; }

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
        const sv = i.sigma ? meas[i.sigma] : undefined;  // the run's own error at the cursor (EX2 §5 F4)
        const r = v === null || v === undefined || !eventReached(s, i, f) ? null : reading(i, v, sv);
        if (!r) {
          const m = ((c && c.pt.W && c.pt.W.header.measurables) || []).find((x) => x.id === src);
          return { refused: t("Nothing to measure yet: “{what}” has not been reached at this moment", { what: m ? t(m.label) : src }) };
        }
        readings[id] = r;
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
    const empties = {};  // a formula's cell left empty, with its reason (EX2 §5 F5)
    const row = { id: Date.now() + Math.random(), values: { ...s.cur.pt.values }, readings: r.readings, cols: rowOf(s.step.columns, r.readings, empties), why: empties };
    const placed = placeRow(s.rows, row);
    s.rows = placed.rows;
    saveRows(storeKey(s.step), s.A.manifest.key, s.rows);
    const noTime = s.step.columns.some((c) => c.from && instruments[c.from] && instruments[c.from].manual && !row.cols[c.id]);
    const text = placed.replaced
      ? t("Row {n:d} replaced: this set-up was already measured; the bench repeats exactly, so a repeat is not a new independent point", { n: placed.n })
      : t("Measured: row {n:d}", { n: placed.n });
    const empty = Object.entries(empties).map(([cid, reason]) => t("{column} is empty: {why}", { column: colLabel(colOf(s, cid) || { label: cid }), why: whyText(reason) }));
    say([noTime ? `${text}. ${t("No time in this row: the stopwatch was not stopped")}` : text, ...empty].join(". "));
    renderWork();
  }

  // --- the table, the plot, the fit, the law --------------------------------------------------------------------------------
  const colLabel = (c) => t(c.label);
  const colOf = (s, id) => s.step.columns.find((c) => c.id === id) || null;
  // a count: a counter's column, or a formula over counts only (u34's N = n − 1 of the turns counter); its whole value is
  // written as a count («10», «12 595 ± 110»), not «10.00» (review R2-P nits)
  const isCount = (c, seen = new Set()) => {
    if (!c || seen.has(c.id)) return false;
    seen.add(c.id);
    if (c.from) return (instruments[c.from] || {}).kind === "counter";
    if (!c.expr) return false;
    try { return formula(c.expr).names.every((n) => isCount(S().step.columns.find((x) => x.id === n), seen)); } catch (e) { return false; }
  };
  const cell = (c, x) => {
    if (!x) return "—";
    const i = c.from ? instruments[c.from] : null;
    if (i) return readingText(i, x);
    if (Number.isInteger(x.v) && isCount(c)) return readingText({ kind: "counter" }, x);
    return pm(x.v, x.e);
  };
  // the set-up of a row (review R2-P F7: «nothing hidden», the students hand in their own records): the step's controls
  // that no instrument reads (u35's glass and side, polarisation, analyser; u37's pairs, law and source, τ …), each a
  // column of the table and of the CSV with its label and unit, its value as the control names it
  const setupOf = (s) => {
    const read = new Set(s.step.instruments.map((id) => String((instruments[id] || {}).reads || "")).filter((r) => r.startsWith("control:")).map((r) => r.slice(8)));
    return (s.A ? s.A.controls : []).filter((c) => !read.has(c.param));
  };
  // the rows the plot and the fit use (the student's choice, review R2-P F7): those whose set-up matches the filters
  // («Polarisation: s») and that are not unticked («in the fit»); the others stay in the table and the CSV
  const inFilter = (s, r) => Object.entries(s.filter || {}).every(([p, v]) => v === undefined || JSON.stringify((r.values || {})[p]) === v);
  const inFit = (s, r) => inFilter(s, r) && !r.off;
  function renderWork() {
    const s = S(), step = s.step, cols = step.columns, setup = setupOf(s);
    const save = () => { if (s.A) saveRows(storeKey(step), s.A.manifest.key, s.rows); };
    const table = el("table", { class: "dm-table" },
      el("thead", {}, el("tr", {}, el("th", {}, "№"), setup.map((c) => el("th", { class: "dm-setup" }, controlLabel(c))), cols.map((c) => el("th", {}, colLabel(c))),
        el("th", { title: t("Use this row in the plot and the fit") }, t("in the fit")), el("th", {}, el("span", { class: "dm-sr" }, t("Delete"))))),
      el("tbody", {}, s.rows.map((r, j) => el("tr", { class: inFilter(s, r) ? "" : "dm-row-out" }, el("td", {}, String(j + 1)),
        setup.map((c) => el("td", { class: "dm-setup" }, (r.values || {})[c.param] === undefined ? "—" : valueText(c, r.values[c.param]))),
        cols.map((c) => (r.why && r.why[c.id] ? el("td", { class: "mono dm-undef", title: whyText(r.why[c.id]) }, "—", el("span", { class: "dm-why" }, whyText(r.why[c.id])))
          : el("td", { class: "mono" }, cell(c, r.cols[c.id])))),
        el("td", {}, el("input", { type: "checkbox", class: "dm-use", checked: !r.off, "aria-label": t("Row {n:d} in the plot and the fit", { n: j + 1 }),
          onchange: (e) => { r.off = !e.target.checked; save(); renderWork(); } })),
        el("td", {}, el("button", { class: "dm-del", title: t("Delete row {n:d}", { n: j + 1 }), "aria-label": t("Delete row {n:d}", { n: j + 1 }), onclick: () => {
          s.rows.splice(j, 1); save(); renderWork(); } }, "✕"))))));
    const fmtCsv = csvFormat();
    const csvText = csv(cols, s.rows, colLabel, { ...fmtCsv, setup: setup.map((c) => ({ param: c.param, label: controlLabel(c),
      text: (v) => (typeof v === "number" && !(Array.isArray(c.labels) && c.labels[c.values.indexOf(v)]) ? v : valueText(c, v)) })) });
    const csvA = el("a", { class: "button", download: `${kit.world}_${step.id}.csv`, title: t("The table with the errors, as CSV") }, "⤓ CSV");
    csvA.href = csvHref(csvText);
    const clear = el("button", { onclick: () => { if (!s.rows.length) return; s.rows = []; save(); renderWork(); } }, t("Clear the table"));
    const opt = (sel, v) => { sel.value = v; return sel; };
    const xs = opt(el("select", { "aria-label": t("x axis"), onchange: (e) => { s.x = e.target.value; renderWork(); } }, cols.map((c) => el("option", { value: c.id }, colLabel(c)))), s.x);
    const ys = opt(el("select", { "aria-label": t("y axis"), onchange: (e) => { s.y = e.target.value; renderWork(); } }, cols.map((c) => el("option", { value: c.id }, colLabel(c)))), s.y);
    const fits = (step.plot.fits || [step.plot.fit]).filter((m) => m && (m !== "power" || !kit.school));
    const fs = opt(el("select", { "aria-label": t("fit"), onchange: (e) => { s.model = e.target.value; renderWork(); } }, fits.map((m) => el("option", { value: m }, FIT_LABEL()[m] || m))), s.model);
    // a filter per set-up control whose rows differ: which set-ups the plot and the fit use
    s.filter = s.filter || {};
    const filters = setup.map((c) => {
      const seen = [...new Set(s.rows.map((r) => JSON.stringify((r.values || {})[c.param])).filter((x) => x !== undefined))];
      if (seen.length < 2 && s.filter[c.param] === undefined) return null;
      const sel = el("select", { "data-filter": c.param, "aria-label": t("Rows in the plot and the fit: {control}", { control: controlLabel(c) }),
        onchange: (e) => { s.filter = { ...s.filter, [c.param]: e.target.value || undefined }; renderWork(); } },
      el("option", { value: "" }, t("all")), seen.map((x) => el("option", { value: x }, valueText(c, JSON.parse(x)))));
      sel.value = s.filter[c.param] ?? "";
      return el("label", {}, `${controlLabel(c)} `, sel);
    }).filter(Boolean);
    const cv = el("canvas", { class: "dm-plot", role: "img", "aria-label": t("{y} against {x}", { y: colLabel(colOf(s, s.y) || { label: s.y }), x: colLabel(colOf(s, s.x) || { label: s.x }) }) });
    // the points of the rows in the plot (those filtered out are not drawn; an unticked one is drawn hollow, not fitted)
    const pts = s.rows.filter((r) => inFilter(s, r)).map((r) => [r.cols[s.x], r.cols[s.y], !r.off]).filter(([a, b]) => a && b);
    const used = pts.filter((p) => p[2]);
    const nUse = s.rows.filter((r) => inFit(s, r)).length;
    s.res = null;
    let fitText = [t("Measure at least {n:d} points to fit", { n: (FIT_MODELS[s.model] || { min: 2 }).min })];
    try {
      if (s.x === s.y) fitText = [t("Choose different columns for x and y")];
      else if (used.length) {
        s.res = fit(used.map((p) => p[0].v), used.map((p) => p[1].v), used.map((p) => p[0].e), used.map((p) => p[1].e), s.model);
        fitText = fitLines(s.res, FIT_LABEL()[s.model] || s.model, kit.school);
      }
    } catch (e) { s.res = null; fitText = [e.why === "points" || e.why === "singular" ? t("Measure more points at different set-ups to fit") : e.why === "positive" ? t("A power law needs positive values")
      : e.why === "converge" ? t("The fit with errors in x and y does not converge: look at the readings and the plot") : e.message]; }
    fill(work,
      el("div", { class: "dm-work-head" }, el("b", {}, t("Table")), el("span", { class: "grow" }), clear, csvA),
      el("div", { class: "dm-table-box" }, s.rows.length ? table : el("div", { class: "muted" }, t("No measurements yet: launch, then press «Measure»."))),
      el("div", { class: "dm-work-head" }, el("b", {}, t("Plot")), el("label", {}, "x ", xs), el("label", {}, "y ", ys), el("label", {}, t("fit") + " ", fs)),
      filters.length ? el("div", { class: "dm-work-head dm-filters" }, el("span", {}, t("Rows in the plot and the fit:")), filters) : null,
      cv,
      nUse < s.rows.length ? el("div", { class: "muted dm-fit-rows" }, t("The plot and the fit use {k:d} of {n:d} rows (the set-up chosen above, the rows ticked «in the fit»)", { k: nUse, n: s.rows.length })) : null,
      el("div", { class: "dm-fit mono", role: "status" }, fitText.map((x) => el("div", {}, x))));
    requestAnimationFrame(() => drawPlot(cv, pts, s));
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
    g.font = "11px system-ui, sans-serif";
    const xt = plotTicks(x0, x1), yt = plotTicks(y0, y1);
    // the left margin fits the longest label of the y axis (review R2-P F12: «2,78·10⁻¹⁷» was cut off at the left)
    const L0 = Math.max(48, Math.ceil(Math.max(0, ...yt.map((v) => g.measureText(fmt(v, ".3g")).width)) + 10)), R = 12, T0 = 10, B = 34;
    const px = (x) => L0 + (x - x0) / (x1 - x0) * (W - L0 - R), py = (y) => H - B - (y - y0) / (y1 - y0) * (H - T0 - B);
    g.strokeStyle = muted; g.lineWidth = 1; g.fillStyle = muted;
    g.beginPath(); g.moveTo(L0, T0); g.lineTo(L0, H - B); g.lineTo(W - R, H - B); g.stroke();
    g.textAlign = "center";
    for (const v of xt) { g.fillText(fmt(v, ".3g"), px(v), H - B + 14); g.beginPath(); g.moveTo(px(v), H - B); g.lineTo(px(v), H - B + 3); g.stroke(); }
    g.textAlign = "right";
    for (const v of yt) { g.fillText(fmt(v, ".3g"), L0 - 4, py(v) + 4); g.beginPath(); g.moveTo(L0 - 3, py(v)); g.lineTo(L0, py(v)); g.stroke(); }
    g.fillStyle = ink; g.textAlign = "right"; g.fillText(cx ? colLabel(cx) : "", W - R, H - 4);
    g.textAlign = "left"; g.fillText(cy ? colLabel(cy) : "", L0 + 4, T0 + 10);
    const used = pts.filter((p) => p[2] !== false);
    if (s.res && used.length) {  // the fitted curve over the measured range of the rows it used (a line through the origin from 0)
      const xa = Math.min(...used.map((p) => p[0].v)), xb = Math.max(...used.map((p) => p[0].v));
      const from = s.model === "line0" ? Math.min(0, xa) : xa;
      g.save(); g.beginPath(); g.rect(L0, T0, W - L0 - R, H - T0 - B); g.clip();
      g.strokeStyle = acc; g.lineWidth = 1.5; g.beginPath();
      let pen = false;
      for (let k = 0; k <= 100; k++) { const x = from + (xb - from) * k / 100, y = s.res.f(x); if (!Number.isFinite(y)) { pen = false; continue; } const X = px(x), Y = py(y); if (pen) g.lineTo(X, Y); else g.moveTo(X, Y); pen = true; }
      g.stroke(); g.restore();
    }
    g.strokeStyle = ink; g.fillStyle = ink; g.lineWidth = 1;
    for (const [a, b, use] of pts) {
      const X = px(a.v), Y = py(b.v);
      g.beginPath(); g.moveTo(px(a.v - a.e), Y); g.lineTo(px(a.v + a.e), Y); g.moveTo(X, py(b.v - b.e)); g.lineTo(X, py(b.v + b.e)); g.stroke();
      g.beginPath(); g.arc(X, Y, 3, 0, 2 * Math.PI);
      if (use === false) { g.fillStyle = css("--canvas") || "#fff"; g.fill(); g.stroke(); g.fillStyle = ink; } else g.fill();  // not in the fit: hollow
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
    c.pin = { clock: s.clock, at: c.launchedAt, t: f.t };  // that frame's own time (explore.js localT)
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
    const mods = W.header.modifications || [];
    const val = (v) => (typeof v === "number" ? fmt(v, ".6g") : t(v));
    modBox.hidden = !mods.length;
    const modText = mods.length ? t("MODIFIED PHYSICS:") + " " + mods.map((m) => t("{label}: {value} (accepted: {standard})", { label: t(m.label), value: val(m.value), standard: val(m.standard) })).join("; ") : "";
    if (modBox.textContent !== modText) modBox.textContent = modText;
    document.body.classList.toggle("dm-modified", mods.length > 0);
    const want = step().readouts || [];
    const ms = (W.header.measurables || []).filter((m) => want.includes(m.id));
    const meas = (f && f.meta.meas) || {};
    const rsig = JSON.stringify([L.k, ms.map((m) => [m.id, meas[m.id], m.sigma ? meas[m.sigma] : null, m.ref ? meas[m.ref] : null])]);
    if (rsig !== L.readSig) {
      L.readSig = rsig;
      fill(readBox, ms.map((m) => {
        const x = measText(m, meas);
        return el("div", { class: "dm-readout", "data-readout": m.id }, el("span", {}, t(m.label)),
          el("span", { class: "dm-rv" }, el("b", { class: "mono" }, x.value === null ? "—" : x.value), x.ref ? el("span", { class: "mono dm-ref" }, x.ref) : null));
      }));
    }
    const speed = speedOf(step(), c.pt);
    kit.self.rate = speed * L.rate;  // the view's ctx.speed(): world seconds per played second
    const declared = step().speed !== undefined && step().speed !== null;
    bar.update({ playing: L.playing, i: Math.max(0, i), max: Math.max(0, F.length - 1),
      text: declared ? timeLabel({ tt, tEnd: c.pt.tEnd, speed, rate: L.rate, header: W.header, school: !!kit.school }) : `${secs(tt)} / ${secs(c.pt.tEnd)}`,
      title: declared ? t("The world's own time, how much slower or faster than real time it plays, and the position in the point") : "",
      launch: c.launchedAt === null || ended(c, s.clock) });
  }
  const step = () => S().step;
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
        s.clock += dt * L.rate * speedOf(s.step, s.cur.pt);  // world seconds: the step's speed × normal or slow (EX2 §5 F1)
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
      // the events too, as Explore's (review R2-P, suspicion: an event without a new check left the drawer as it was)
      return `${L.k}|${c.pt.i}|${n}|${W.events.filter((e) => (e.t ?? 0) <= tt).length}`;
    },
    drawer() {
      const s = S(), c = s && s.cur, W = c && c.pt.W;
      const tt = W ? (frameAt(W, localT(c, s.clock)) || {}).t ?? 0 : 0;
      const m = s && s.A ? s.A.manifest : {};
      const passport = [[t("Point"), c ? valuesText(s.A.controls, c.pt.values, ((kit.viz && kit.viz.schema) || {}).params || []) : "—"], [t("Atlas"), `${m.atlas || ""} · ${t("key")} ${m.key || ""}`],
        [t("Code"), m.code_hash], [t("Random seed"), m.seed], [t("The atlas was built"), when(((s && s.A && s.A.entry) || {}).made ?? m.made)]];
      if (s && s.fromSite) passport.push([t("From"), t("the public site")]);
      // the same as Explore's: every check with its value and reference, the events with their texts and times (the
      // owner, 2026-11-18: a lab is a bench, nothing is hidden; EX1's D10 withdrawn)
      const colName = (id) => { const c = s && s.step.columns.find((x) => x.id === id); return c ? t(c.label) : id; };
      const computed = s ? computedFor(s.step, (s.A && s.A.manifest.references) || {}, colName) : [];
      return kit.howWeKnow({ W, tt, passport, computed,
        note: t("Computed by the engine when the site was built: every slider position is such a point; nothing between them is drawn.") });
    },
    liveBody() { const s = S(); return s && s.A ? { preset: s.A.manifest.preset, params: { ...(s.A.manifest.fixed || {}), ...expandValues(s.A.controls, s.values) } } : null; },
  };
  window.__lfLab = { state: L, step: () => S(), rows: () => S().rows, fit: () => S().res, variant: V };
  const first = V && V.steps ? Math.max(0, steps.findIndex((x) => x.id === V.steps[0])) : 0;
  if (steps.length) await openStep(first);
  else fill(card, el("p", { class: "muted" }, t("This lab has no steps yet.")));
  return API;
}
