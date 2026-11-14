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
// value "control:<param>") and rounds it to its division; the reading carries the declared error (by default half a
// division). A manual stopwatch is started by the launch and stopped by the student: its reading is the world time at
// the press, at real speed («slow» is refused for it, so the reaction is real). The derived columns and the fit are
// arithmetic and statistics on the readings (fit.js).
import { openAtlas } from "./atlas.js";
import { MODELS as FIT_MODELS, agrees, fit, quantity } from "./fit.js";
import { t } from "./i18n.js";
import { SLOW, controlRow, ended, localT, secs, valuesText } from "./explore.js";
import { frameAt, frameIndexAt, showAt } from "./record_core.js";
import { css, el, fill, fmt } from "./ui.js";

// --- readings (pure: lab.test.mjs) ----------------------------------------------------------------------------------------
const decimals = (d) => { const s = String(d); if (s.includes("e-")) return Number(s.split("e-")[1]) + (s.split("e-")[0].split(".")[1] || "").length; return (s.split(".")[1] || "").length; };
// a value read by an instrument: division × round(value / division), its error the declared one (half a division)
export function reading(instr, value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null;
  const d = Number(instr.division);
  const v = Number((Math.round(Number(value) / d) * d).toFixed(Math.min(15, decimals(d))));
  return { v: Object.is(v, -0) ? 0 : v, e: instr.error ?? d / 2 };
}
// a derived column: its value and its error |f′(x)|·σ_x (sin2: sin 2θ with θ in degrees)
const OPS = {
  sqrt: [(x) => Math.sqrt(x), (x) => 1 / (2 * Math.sqrt(x))],
  square: [(x) => x * x, (x) => 2 * x],
  sin2: [(x) => Math.sin(2 * x * Math.PI / 180), (x) => 2 * Math.cos(2 * x * Math.PI / 180) * Math.PI / 180],
  inverse: [(x) => 1 / x, (x) => -1 / (x * x)],
  log: [(x) => Math.log(x), (x) => 1 / x],
};
export function derived(op, r) {
  if (!r || !OPS[op]) return null;
  const [f, df] = OPS[op];
  const v = f(r.v), e = Math.abs(df(r.v)) * r.e;
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

const STORE = (world, step) => `lfviz.lab.${world}.${step}`;
function loadRows(key) { try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) { return []; } }
function saveRows(key, rows) { try { localStorage.setItem(key, JSON.stringify(rows)); } catch (e) { /* private mode: the table lives in the page */ } }

const FIT_LABEL = () => ({ line0: t("line through the origin y = b·x"), line: t("line y = a + b·x"), quadratic: t("parabola y = c0 + c1·x + c2·x²"), power: t("power law y = A·x^p") });

export async function create(host, kit, spec) {
  const steps = spec.steps || [], instruments = spec.instruments || {};
  const L = { k: 0, st: [], playing: false, wall: 0, rate: 1 };
  const index = kit.index || {};
  const view = kit.newView();
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "dm-instr");
  const stage = el("div", { class: "dm-stage" }, view.center, svg);
  const card = el("div", { class: "dm-side dm-card" });
  const work = el("div", { class: "dm-work" });
  const bar = kit.transport({ launchLabel: t("▶ Launch"), play: () => playPressed(), reset: () => resetPressed(),
    scrub: (i) => scrub(i), rate: (r) => { L.rate = r === 1 ? 1 : SLOW; kit.self.rate = L.rate; } });
  fill(host, el("div", { class: "dm-main" }, stage, card), bar.el, work);

  // --- a step's state, made when the step is first opened -------------------------------------------------------------
  async function stepState(k) {
    if (L.st[k]) return L.st[k];
    const step = steps[k];
    const entry = (index.atlases || []).find((a) => a.id === step.atlas);
    const S = { step, A: null, values: {}, cur: null, clock: 0, rows: loadRows(STORE(kit.world, step.atlas)), sw: null,
      x: step.plot.x, y: step.plot.y, model: step.plot.fit || (step.plot.fits || [])[0] || "line", res: null, check: null, msg: "" };
    if (entry) {
      S.A = await openAtlas(kit.world, entry);
      S.A.controls = S.A.controls.map((c) => ({ ...((step.controls || []).find((x) => x.param === c.param) || {}), ...c }));
      S.values = { ...S.A.defaults };
      const pt = await S.A.point(S.values);
      if (pt.state === "computed") S.cur = { pt, launchedAt: null };
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
    const nav = steps.length > 1 ? el("div", { class: "dm-seg dm-steps" }, steps.map((x, j) => el("button", { class: j === L.k ? "on" : "",
      title: t(x.title), onclick: () => openStep(j) }, String(j + 1)))) : null;
    ctlRows = s.A ? s.A.controls.map((c) => {
      const r = controlRow(c, s.values[c.param], (v) => pick(c, v), { server: false });
      r.set(s.values[c.param]);
      return r;
    }) : [];
    const instrList = el("ul", { class: "dm-instr-list" }, step.instruments.map((id) => {
      const i = instruments[id];
      if (!i) return null;
      return el("li", {}, el("b", {}, t(i.label)), " — ", t("division {d} {unit}, error ±{e} {unit}", { d: fmt(i.division, ".6g"), e: fmt(i.error, ".6g"), unit: t(i.unit) }),
        i.error_note ? el("div", { class: "muted" }, t(i.error_note)) : null);
    }));
    const swBox = step.instruments.filter((id) => instruments[id] && instruments[id].manual).map((id) => stopwatchWidget(id, instruments[id]));
    const measure = el("button", { class: "primary dm-measure", onclick: () => measureNow() }, t("Measure"));
    const msg = el("div", { class: "dm-msg", role: "status" }, s.msg);
    fill(card, nav,
      el("div", { class: "dm-part" }, t("Part {k:d} of {n:d}: {title}", { k: L.k + 1, n: steps.length, title: t(step.title) })),
      el("p", { class: "dm-goal" }, t(step.goal)),
      s.A ? null : el("p", { class: "dm-missing" }, t("No atlas of this step yet: it is built with the site (site/atlas.py).")),
      el("div", { class: "dm-ctls" }, ctlRows.map((r) => r.el)),
      el("div", { class: "dm-sub" }, t("Instruments")), instrList, swBox, measure, msg,
      el("p", { class: "dm-ws" }, el("a", { href: kit.worksheetHref(), target: "_blank" }, t("The worksheet (print) →"))));
  }
  async function pick(c, v) {
    const s = S();
    s.values = { ...s.values, [c.param]: v };
    for (const [j, r] of ctlRows.entries()) r.set(s.values[s.A.controls[j].param]);
    const pt = await s.A.point(s.values);
    s.A.prefetch(s.values);
    if (pt.state === "refused") { say(t(pt.refusal)); return; }
    say("");
    s.cur = { pt, launchedAt: null }; s.sw = null; L.playing = false;
    renderStopwatches();
    kit.dirty();
  }
  function say(text) { S().msg = text; const m = card.querySelector(".dm-msg"); if (m) m.textContent = text; }

  // --- the manual stopwatch ------------------------------------------------------------------------------------------------
  function stopwatchWidget(id, instr) {
    const out = el("output", { class: "mono dm-sw-read" }, "—");
    const btn = el("button", { class: "dm-sw-btn", onclick: () => {
      const s = S();
      if (!s.sw || !s.sw.running) { say(t("The stopwatch starts with the launch: press ▶ Launch first")); return; }
      s.sw.running = false; s.sw.stopped = true;
      renderStopwatches();
    } }, t("⏱ Stop"));
    return el("div", { class: "dm-sw", "data-instr": id }, el("span", {}, t(instr.label)), btn, out);
  }
  function renderStopwatches() {
    const s = S();
    for (const w of card.querySelectorAll(".dm-sw")) {
      const instr = instruments[w.dataset.instr];
      const running = !!(s.sw && s.sw.running);
      const tt = s.sw ? s.sw.t : null;
      const r = tt === null ? null : reading(instr, tt);
      w.querySelector("output").textContent = r ? `${fmt(r.v, `.${decimals(instr.division)}f`)} ${t(instr.unit)}` : "—";
      w.querySelector("button").disabled = !running;
    }
  }

  // --- measuring ---------------------------------------------------------------------------------------------------------
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
      if (src.startsWith("control:")) {
        const p = src.slice(8);
        readings[id] = reading(i, p in s.values ? s.values[p] : (s.A.manifest.fixed || {})[p]);
      } else {
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
    if (!s.cur) { say(t("Choose a set-up first")); return; }
    const r = readAll();
    if (r.refused) { say(r.refused); return; }
    const row = { id: Date.now() + Math.random(), values: { ...s.values }, readings: r.readings, cols: rowOf(s.step.columns, r.readings) };
    s.rows.push(row);
    saveRows(STORE(kit.world, s.step.atlas), s.rows);
    say(t("Measured: row {n:d}", { n: s.rows.length }));
    s.check = null;
    renderWork();
  }

  // --- the table, the plot, the fit, the law --------------------------------------------------------------------------------
  const colLabel = (c) => t(c.label);
  // a reading as the instrument shows it (its division's decimals) with its declared error; a derived value to its error
  const cell = (c, x) => {
    if (!x) return "—";
    const i = c.from ? instruments[c.from] : null;
    return i ? `${fmt(x.v, `.${decimals(i.division)}f`)} ± ${fmt(x.e, ".2g")}` : pm(x.v, x.e);
  };
  function renderWork() {
    const s = S(), step = s.step, cols = step.columns;
    const table = el("table", { class: "dm-table" },
      el("thead", {}, el("tr", {}, el("th", {}, "№"), cols.map((c) => el("th", {}, colLabel(c))), el("th", {}, ""))),
      el("tbody", {}, s.rows.map((r, j) => el("tr", {}, el("td", {}, String(j + 1)),
        cols.map((c) => el("td", { class: "mono" }, cell(c, r.cols[c.id]))),
        el("td", {}, el("button", { class: "dm-del", title: t("Delete this row"), onclick: () => { s.rows.splice(j, 1); saveRows(STORE(kit.world, step.atlas), s.rows); s.check = null; renderWork(); } }, "✕"))))));
    const csvA = el("a", { class: "button", download: `${kit.world}_${step.id}.csv`, title: t("The table with the errors, as CSV") }, "⤓ CSV");
    csvA.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv(cols, s.rows, colLabel));
    const clear = el("button", { onclick: () => { if (!s.rows.length) return; s.rows = []; saveRows(STORE(kit.world, step.atlas), s.rows); s.check = null; renderWork(); } }, t("Clear the table"));
    const opt = (sel, v) => { sel.value = v; return sel; };
    const xs = opt(el("select", { "aria-label": t("x axis"), onchange: (e) => { s.x = e.target.value; s.check = null; renderWork(); } }, cols.map((c) => el("option", { value: c.id }, colLabel(c)))), s.x);
    const ys = opt(el("select", { "aria-label": t("y axis"), onchange: (e) => { s.y = e.target.value; s.check = null; renderWork(); } }, cols.map((c) => el("option", { value: c.id }, colLabel(c)))), s.y);
    const fits = (step.plot.fits || [step.plot.fit]).filter((m) => m && (m !== "power" || !kit.school));
    const fs = opt(el("select", { "aria-label": t("fit"), onchange: (e) => { s.model = e.target.value; s.check = null; renderWork(); } }, fits.map((m) => el("option", { value: m }, FIT_LABEL()[m] || m))), s.model);
    const cv = el("canvas", { class: "dm-plot" });
    // the fit on the rows that have both columns
    const pts = s.rows.map((r) => [r.cols[s.x], r.cols[s.y]]).filter(([a, b]) => a && b);
    s.res = null;
    let fitText = t("Measure at least {n:d} points to fit", { n: (FIT_MODELS[s.model] || { min: 2 }).min });
    try {
      if (pts.length) {
        s.res = fit(pts.map((p) => p[0].v), pts.map((p) => p[1].v), pts.map((p) => p[0].e), pts.map((p) => p[1].e), s.model);
        fitText = [FIT_LABEL()[s.model] + ":", ...Object.keys(s.res.params).filter((k) => k !== "yv").map((k) =>
          `${k === "xv" ? "x*" : k} = ${pm(s.res.params[k], s.res.sigma[k])}`),
        kit.school ? "" : Number.isFinite(s.res.chi2) && s.res.dof > 0 ? `χ²/dof = ${fmt(s.res.chi2 / s.res.dof, ".3g")}` : ""].filter(Boolean).join("  ");
      }
    } catch (e) { s.res = null; fitText = e.why === "points" || e.why === "singular" ? t("Measure more points at different set-ups to fit") : e.why === "positive" ? t("A power law needs positive values") : e.message; }
    const law = step.law;
    const checkBtn = law ? el("button", { class: "primary dm-check-law", disabled: !s.res, onclick: () => { checkLaw(); renderWork(); } }, t("Check against the law")) : null;
    const checkOut = el("div", { class: "dm-law " + (s.check ? (s.check.ok ? "st-ok" : "st-bad") : ""), role: "status" }, s.check ? s.check.text : "");
    fill(work,
      el("div", { class: "dm-work-head" }, el("b", {}, t("Table")), el("span", { class: "grow" }), clear, csvA),
      el("div", { class: "dm-table-box" }, s.rows.length ? table : el("div", { class: "muted" }, t("No measurements yet: launch, then press «Measure»."))),
      el("div", { class: "dm-work-head" }, el("b", {}, t("Plot")), el("label", {}, "x ", xs), el("label", {}, "y ", ys), el("label", {}, t("fit") + " ", fs)),
      cv, el("div", { class: "dm-fit mono" }, fitText), checkBtn, checkOut);
    requestAnimationFrame(() => drawPlot(cv, pts, s));
  }
  function checkLaw() {
    const s = S(), law = s.step.law, refs = (s.A && s.A.manifest.references) || {};
    const ref = refs[law.reference];
    const q = s.res ? quantity(s.res, law.quantity) : null;
    if (!ref || !q) { s.check = { ok: false, text: t("This fit gives no “{q}”: choose the step's fit", { q: law.quantity }) }; return; }
    const a = agrees(q.value, q.sigma, ref.value);
    const unit = law.unit || ref.unit || "";
    const how = ref.kind === "engine" ? t("computed by the engine; there is no closed form") : t("closed form {law}", { law: t(ref.label) });
    const measured = t("{label} = {value} {unit}", { label: t(law.label), value: pm(q.value, q.sigma), unit });
    const lawText = t("law: {value} {unit} ({how})", { value: fmt(ref.value, ".4g"), unit, how });
    s.check = { ok: a.agrees, text: `${measured} — ${lawText} ` + (a.agrees ? t("✓ agrees within two errors")
      : s.step.hint ? t("✗ does not agree: {hint}", { hint: t(s.step.hint) }) : t("✗ does not agree: look at the readings and the plot")) };
  }
  function drawPlot(cv, pts, s) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth || 300, H = cv.clientHeight || 220;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    const g = cv.getContext("2d");
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.fillStyle = css("--canvas") || "#fff"; g.fillRect(0, 0, W, H);
    const ink = css("--ink") || "#222", muted = css("--muted") || "#888", acc = css("--accent") || "#1c5fb8";
    const cols = s.step.columns, cx = cols.find((c) => c.id === s.x), cy = cols.find((c) => c.id === s.y);
    const xsV = pts.flatMap((p) => [p[0].v - p[0].e, p[0].v + p[0].e]), ysV = pts.flatMap((p) => [p[1].v - p[1].e, p[1].v + p[1].e]);
    let [x0, x1] = [Math.min(0, ...xsV), Math.max(...xsV, 1e-9)], [y0, y1] = [Math.min(0, ...ysV), Math.max(...ysV, 1e-9)];
    if (!pts.length) { x0 = 0; x1 = 1; y0 = 0; y1 = 1; }
    x1 += 0.06 * (x1 - x0); y1 += 0.08 * (y1 - y0);
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
    if (s.res) {  // the fitted curve over the plotted range
      g.save(); g.beginPath(); g.rect(L0, T0, W - L0 - R, H - T0 - B); g.clip();
      g.strokeStyle = acc; g.lineWidth = 1.5; g.beginPath();
      let pen = false;
      for (let k = 0; k <= 100; k++) { const x = x0 + (x1 - x0) * k / 100, y = s.res.f(x); if (!Number.isFinite(y)) { pen = false; continue; } const X = px(x), Y = py(y); if (pen) g.lineTo(X, Y); else g.moveTo(X, Y); pen = true; }
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
    if (L.playing) { L.playing = false; L.paused = true; kit.dirty(); return; }
    if (c.launchedAt === null || ended(c, s.clock)) {
      c.launchedAt = s.clock;
      // the manual stopwatch starts with the launch and runs in real time (× the speed) until it is pressed
      s.sw = s.step.instruments.some((id) => (instruments[id] || {}).manual) ? { running: true, stopped: false, t: 0 } : null;
    }
    L.playing = true; L.paused = false; L.wall = performance.now(); kit.dirty();
  }
  function resetPressed() { const s = S(); L.playing = false; if (s.cur) s.cur.launchedAt = null; s.sw = null; kit.dirty(); }
  function scrub(i) {
    const s = S(), c = s.cur;
    if (!c || !c.pt.W) return;
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
      if (s && s.sw && s.sw.running && !L.paused) { s.sw.t += dt * L.rate; renderStopwatches(); }
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
        [t("Code"), m.code_hash], [t("Random seed"), m.seed], [t("Made"), String(m.made || "").replace("T", " ").slice(0, 19)]];
      return kit.howWeKnow({ W, tt, passport, note: t("Computed by the engine when the site was built: every slider position is such a point; nothing between them is drawn.") });
    },
    liveBody() { const s = S(); return s && s.A ? { preset: s.A.manifest.preset, params: { ...(s.A.manifest.fixed || {}), ...s.values } } : null; },
  };
  window.__lfLab = { state: L, step: () => S(), rows: () => S().rows, check: () => S().check, fit: () => S().res };
  if (steps.length) await openStep(0);
  else fill(card, el("p", { class: "muted" }, t("This lab has no steps yet.")));
  return API;
}
