// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// «Приборы» (plan P16.3; owner, 2026-11-04 and 2026-11-11): the measurable quantities of a world and of its probes as
// time plots along the record, their CSV, and parameter sweeps.
//
// The player hands every message of the run to this module (one marked line in player.js onMessage: the record replayed
// on (re)connection, then the live tail) with accessors of what it shows: `t()` the cursor's world time, `w()` the
// world shown, `n()` the number of worlds. What a world declares (`measurables` in its scene message, its header or any
// accumulative message: [{id, label, unit, of, group}]) is listed by group; every frame's `meas` is kept per world (at
// most MAX_POINTS points: beyond, every other one, uniform over the whole record as the player's history). A chosen
// quantity gets its own small plot (one axis each): the record of the world shown, solid up to the cursor and faded
// after it, the cursor as a line, its value at the cursor in the title. «CSV» downloads the record's own values at full
// resolution from the server (/api/runs/{id}/series). «Свип» (/api/runs/{id}/sweep): from the current moment of the
// latest world, the same scene for a list of values of a live law or of an object's parameter, a chosen quantity
// measured — the cost estimated before the start, the progress, then a table, a plot and a CSV. Nothing here changes a
// world: a sweep runs in its own process on a copy of the world's state.
//
// On a saved recording (/run?rec=<world>/<rec>: the public site, the server's recordings) there is no run on a server:
// the plots come from the record as always, the CSV is built in the browser from the values in memory (the frames the
// recording kept, said in its header: «from the recording, one frame in k»), and the sweeps are absent.
//
// Nothing the owner is using is rebuilt under him (review LB1-framework F8; the owner's complaint about views jumping
// back): the list of quantities, its groups (folded or not, kept per run in this browser), the plots, the sweep form
// (built once per world, what was typed kept) and a sweep's result (the table grows by rows, the plot is redrawn on the
// same canvas) are updated in place.
import { getJSON, postJSON, url } from "./api.js";
import { nice } from "./canvas.js";
import { fmtField, lang, parseNum, t } from "./i18n.js";
import { css, el, fill, fresh2d, labelHasUnit, num, panel, time, toast } from "./ui.js";

const runId = new URLSearchParams(location.search).get("id");
const REC = new URLSearchParams(location.search).get("rec");  // a saved recording "<world>/<rec>": no server behind it
const MAX_POINTS = 20000;
const MAX_PLOTS = 6;
const STAT_LABEL = { final: t("the value at the end"), mean_last: t("the mean over the last …"), max: t("the maximum"), min: t("the minimum") };
const STATE_TEXT = { starting: t("starting"), running: t("running"), done: t("done"), cancelled: t("cancelled"), failed: t("not computed"),
  over_budget: t("stopped: over budget"), interrupted: t("interrupted") };
const T_PREFIX = [[1, t("s")], [1e-3, t("ms")], [1e-6, t("µs")], [1e-9, t("ns")], [1e-12, t("ps")], [1e-15, t("fs")], [1e-18, t("as")]];
// a world time in seconds: the unit "s" (a text from the server, rendered here) or "с" of the records before the i18n
const SECONDS = new Set(["s", "\u0441", t("s")]);  // i18n-ok: «с» of the records made before the translation

const I = {
  ctx: null, worlds: [], replaying: true, histStride: 1, mounted: false,
  selected: [], dirty: true, drawnKey: "", lastDraw: 0, hover: null, listRev: 0,
  viz: null, sweeps: [], sweepShown: null, poll: null, est: null, folded: new Set(), formBuilding: false,
};

// --- the record: worlds, their declarations and series ---------------------------------------------------------
function newWorld(meta) {
  const W = { n: meta.world || I.worlds.length + 1, tUnit: tUnitOf(meta), decl: new Map(), objects: new Map(),
              palette: (meta.playground && meta.playground.palette) || [], live: { ...(meta.live || {}) },
              params: { ...(meta.params || {}) }, speed: null, at: {}, current: null,
              t: [], arr: [], v: new Map(), notes: {}, stride: 1, nArr: 0 };
  I.worlds.push(W);
  return W;
}
function tUnitOf(h) {
  const u = h && h.units, tu = u && typeof u === "object" ? u.t : null;
  if (tu && typeof tu === "object") return t(tu);  // a text (T)
  return typeof tu === "string" && tu.trim() ? t(tu.split(" (")[0].trim()) : t("s");
}
// the declarations' texts are rendered once, in the page's language (a change of language reloads the page)
function declare(W, list) {
  for (const d of list) if (d && typeof d.id === "string") W.decl.set(d.id, { id: d.id, label: t(d.label || d.id), unit: t(d.unit), of: d.of ?? null, group: t(d.group) });
}
const val = (x) => (typeof x === "number" && Number.isFinite(x) ? x : NaN);
function addFrame(W, meta) {
  const n = W.nArr;
  W.nArr += I.replaying ? I.histStride : 1;
  const L = W.t.length;
  if (L && W.arr[L - 1] % W.stride !== 0) { W.t.pop(); W.arr.pop(); for (const a of W.v.values()) a.pop(); }
  W.t.push(meta.t ?? 0); W.arr.push(n);
  const meas = meta.meas || {};
  for (const [id, a] of W.v) a.push(val(meas[id]));
  for (const id of Object.keys(meas)) {
    if (!W.v.has(id)) { const a = new Array(W.t.length - 1).fill(NaN); a.push(val(meas[id])); W.v.set(id, a); }
  }
  if (meta.meas_note) for (const [k, v] of Object.entries(meta.meas_note)) W.notes[k] = t(v);
  if (W.t.length > MAX_POINTS) {  // every other point (by arrival number), the latest kept
    W.stride *= 2;
    const keep = W.arr.map((a, i) => a % W.stride === 0 || i === W.arr.length - 1);
    const f = (arr) => arr.filter((_, i) => keep[i]);
    W.t = f(W.t); W.arr = f(W.arr);
    for (const [id, a] of W.v) W.v.set(id, f(a));
  }
}
const latestW = () => I.worlds[I.worlds.length - 1];
const shownW = () => { const w = I.ctx ? I.ctx.w() : -1; return I.worlds[w >= 0 ? w : I.worlds.length - 1]; };
function title(W, d) {
  if (d.of !== null && d.of !== undefined && W.objects.has(d.of)) {
    const ol = W.objects.get(d.of).label;
    if (ol && !d.label.includes(ol)) return `${ol}: ${d.label}`;
  }
  return d.label;
}
// "label, unit" unless the label names the unit already ("Window size, nm", "Number of slits": review LB1-p02-ux X9; the
// server's lfviz.sweep.with_unit says the same); texts are rendered first
export function hasUnit(label, unit) { return labelHasUnit(label, unit); }  // ui.js: by words, texts rendered first
export function withUnit(label, unit) { label = t(label); unit = t(unit); return !unit || hasUnit(label, unit) ? label : t("{label}, {unit}", { label, unit }); }
const shown = (p, values) => !p.show_if || Object.entries(p.show_if).every(([k, allowed]) => allowed.includes(values[k]));
function atT(W, tt) {  // the last point at or before tt
  const T = W.t;
  if (!T.length || tt < T[0]) return -1;
  let lo = 0, hi = T.length - 1;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (T[mid] <= tt + 1e-12 * Math.abs(tt)) lo = mid; else hi = mid - 1; }
  return lo;
}
const fmtT = (W, x) => (SECONDS.has(W.tUnit) ? time(x, 5) : `${num(x, 5)} ${W.tUnit}`);
const fmtV = (x, unit) => (Number.isFinite(x) ? num(x, 6) + (unit ? " " + unit : "") : "—");
// a world time in the unit of its scale: seconds with an SI prefix down to attoseconds ("50 fs"), another unit as it is
function tScale(unit, x) {
  unit = t(unit);
  if (!SECONDS.has(unit)) return { k: 1, u: unit };
  const a = Math.abs(x);
  if (!(a > 0)) return { k: 1, u: t("s") };
  for (const [k, u] of T_PREFIX) if (a >= 0.99999 * k) return { k, u };
  return { k: 1e-18, u: t("as") };
}
function fmtTime(x, unit) {
  if (typeof x !== "number" || !Number.isFinite(x)) return "—";
  const s = tScale(unit, x);
  return `${num(x / s.k, 6)} ${s.u}`;
}

// --- messages from the player -----------------------------------------------------------------------------------
function message(meta, blobs, ctx) {
  I.ctx = ctx || I.ctx;
  mount();
  switch (meta.type) {
    case "history_start":
      I.worlds = []; I.replaying = true; I.histStride = Math.max(1, meta.frame_stride || 1); I.dirty = true;
      if (meta.recording) I.recStride = I.histStride;  // the frames the recording kept: one in recStride
      return;
    case "history_end":
      I.replaying = false; I.histStride = 1; I.dirty = true; refreshLists();
      return;
    case "header": {
      const W = newWorld(meta);
      if (Array.isArray(meta.measurables)) declare(W, meta.measurables);
      I.dirty = true; if (!I.replaying) refreshLists();
      return;
    }
    case "frame": {
      const W = latestW();
      if (W && meta.meas) { addFrame(W, meta); I.dirty = true; }
      if (W && meta.at && typeof meta.at === "object") W.at = meta.at;
      return;
    }
    default: break;
  }
  const W = latestW();
  if (!W || meta.type === "busy" || meta.type === "command" || meta.type === "checkpoint") return;
  if (meta.type === "state" && typeof meta.speed === "number") W.speed = meta.speed;
  if (meta.type === "live") W.live = { ...W.live, ...(meta.values || {}) };
  if (meta.type === "scene" && Array.isArray(meta.objects)) {
    W.objects = new Map(meta.objects.map((o) => [o.id, { label: t(o.label), type: o.type, values: o.values || {} }]));
    // what a playground measures now (a quantity of a removed object is not offered to a sweep: review F12)
    W.current = new Set((Array.isArray(meta.measurables) ? meta.measurables : []).map((d) => d && d.id));
  }
  if (Array.isArray(meta.measurables)) declare(W, meta.measurables);
  if (meta.type === "scene" || Array.isArray(meta.measurables) || meta.type === "live") {
    I.dirty = true;
    if (!I.replaying) { refreshLists(); if (UI.form) updateSweepForm(); }
  }
}

// --- the panel ----------------------------------------------------------------------------------------------------
const UI = { groups: new Map(), rows: new Map(), plotMap: new Map(), plotEls: [] };
function mount() {
  if (I.mounted) return;
  const right = document.getElementById("right");
  if (!right || !right.children.length) return;  // the player has not laid out its columns yet
  I.mounted = true;
  injectStyle();
  UI.list = el("div", { class: "in-list" });
  UI.empty = el("div", { class: "muted", style: { display: "none" } }, t("This world reports no measurable quantities."));
  UI.plots = el("div", { class: "in-plots" });
  UI.upto = el("input", { type: "checkbox", title: t("Only what was recorded up to the history's slider") });
  UI.csv = el("a", { class: "in-csv", href: "#", download: "", title: REC ? t("The values of the chosen quantities from the recording — the frames it kept, full precision; made in this browser")
    : t("The values of the chosen quantities from this world's record — every frame, full precision") }, "⤓ CSV");
  UI.csv.addEventListener("click", (e) => {
    if (REC) {  // built here from the values in memory
      const b = csvBlob();
      if (!b) { e.preventDefault(); toast(t("Tick the quantities"), "notice", 3000); return; }
      if (UI.csvUrl) URL.revokeObjectURL(UI.csvUrl);
      UI.csvUrl = URL.createObjectURL(b.blob);
      UI.csv.href = UI.csvUrl; UI.csv.download = b.name;
      return;
    }
    const h = csvHref(); if (!h) { e.preventDefault(); toast(t("Tick the quantities"), "notice", 3000); } else UI.csv.href = h;
  });
  UI.sweep = el("div", { class: "in-sweep" });
  UI.sweepBox = el("details", { class: "in-sweep-box" }, el("summary", {}, t("Parameter sweep")), UI.sweep);
  UI.sweepBox.addEventListener("toggle", () => { if (UI.sweepBox.open) { ensureSweepForm(); loadSweeps(); } });
  UI.body = el("div", {},
    el("div", { class: "help" }, t("The quantities the world measures in every frame. Tick a quantity for its plot along this world's record; the vertical line is the history's slider, after it the future of the record (faint).")),
    UI.list, UI.empty, UI.plots,
    el("div", { class: "in-row" }, UI.csv, el("label", { class: "muted" }, UI.upto, " " + t("only up to the slider"))),
    REC ? null : UI.sweepBox);  // a sweep computes: not on a recording
  UI.panel = panel(t("Instruments"), UI.body);
  UI.panel.classList.add("in-panel");
  UI.panel.style.display = "none";
  right.insertBefore(UI.panel, right.children[1] || null);
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(selKey()) || "null"); } catch (e) { saved = null; }
  I.selected = Array.isArray(saved) ? saved : [];
  I.userSelected = Array.isArray(saved);  // the owner's own choice (even none) is kept; else the first quantities
  try { I.folded = new Set(JSON.parse(localStorage.getItem(foldKey()) || "[]")); } catch (e) { I.folded = new Set(); }
  window.addEventListener("themechange", () => { I.dirty = true; drawSweepPlot(); });
  new ResizeObserver(() => { I.dirty = true; drawSweepPlot(); }).observe(UI.plots);
  requestAnimationFrame(loop);
}
const runKey = () => (REC ? "rec:" + REC : runId);
const selKey = () => "lfviz.instruments." + runKey();  // the quantities chosen, per run (kept in this browser)
const foldKey = () => "lfviz.instruments.folded." + runKey();  // the groups folded, per run
function saveSel() { try { localStorage.setItem(selKey(), JSON.stringify(I.selected)); } catch (e) { /* private mode */ } }
function saveFolded() { try { localStorage.setItem(foldKey(), JSON.stringify([...I.folded])); } catch (e) { /* private mode */ } }

function groups(W, only = null) {
  const g = new Map();
  for (const d of W.decl.values()) {
    if (only && !only.has(d.id)) continue;
    const key = d.group || (d.of !== null ? t("Objects") : t("World"));
    if (!g.has(key)) g.set(key, []);
    g.get(key).push(d);
  }
  return g;
}

// put `node` into `parent` right after `after` (first when null) — only when it is not there already: moving a node
// would take the focus from a checkbox in it
function place(parent, node, after) {
  const want = after ? after.nextSibling : parent.firstChild;
  if (node.parentNode === parent && want === node) return;
  parent.insertBefore(node, want);
}

function makeGroup(name) {
  const sum = el("summary", {}, name);
  const det = el("details", { class: "in-group" }, sum);
  det.open = !I.folded.has(name);
  det.addEventListener("toggle", () => { if (det.open) I.folded.delete(name); else I.folded.add(name); saveFolded(); });
  return { el: det, summary: sum };
}

function makeRow(d) {
  const cb = el("input", { type: "checkbox" });
  const name = el("span", { class: "in-name" });
  const v = el("span", { class: "in-val mono" });
  const R = { el: el("label", { class: "in-q", title: d.id }, cb, name, v), cb, name, val: v, id: d.id, text: "" };
  cb.addEventListener("change", () => {
    I.userSelected = true;
    if (cb.checked) {
      if (I.selected.length >= MAX_PLOTS) { cb.checked = false; toast(t("At most {n:d} plots at once", { n: MAX_PLOTS }), "notice", 3000); return; }
      if (!I.selected.includes(R.id)) I.selected.push(R.id);
    } else I.selected = I.selected.filter((x) => x !== R.id);
    saveSel(); syncPlots(shownW()); I.dirty = true;  // the list itself stays as it is (F8)
  });
  return R;
}

function refreshLists() {
  if (!I.mounted) return;
  const W = shownW();
  const any = I.worlds.some((x) => x.decl.size);
  UI.panel.style.display = any ? "" : "none";
  if (!W) return;
  if (!I.userSelected && !I.selected.length && W.decl.size) {  // first look: the first world-wide quantities
    I.selected = [...W.decl.values()].filter((d) => d.of === null).slice(0, 2).map((d) => d.id);
  }
  const gs = groups(W);
  for (const [g, G] of UI.groups) if (!gs.has(g)) { G.el.remove(); UI.groups.delete(g); }
  for (const [id, R] of UI.rows) if (!W.decl.has(id)) { R.el.remove(); UI.rows.delete(id); }
  let prevG = null;
  for (const [g, list] of gs) {
    let G = UI.groups.get(g);
    if (!G) { G = makeGroup(g); UI.groups.set(g, G); }
    place(UI.list, G.el, prevG); prevG = G.el;
    let prevR = G.summary;
    for (const d of list) {
      let R = UI.rows.get(d.id);
      if (!R) { R = makeRow(d); UI.rows.set(d.id, R); }
      place(G.el, R.el, prevR); prevR = R.el;
      const text = withUnit(title(W, d), d.unit);
      if (R.text !== text) { R.text = text; R.name.textContent = text; }
      R.d = d;
      const on = I.selected.includes(d.id);
      if (R.cb.checked !== on) R.cb.checked = on;
    }
  }
  UI.empty.style.display = gs.size ? "none" : "";
  syncPlots(W);
  if (UI.sweepBox && UI.sweepBox.open) ensureSweepForm();
}

function syncPlots(W) {
  const want = I.selected.filter((id) => W.decl.has(id));
  for (const [id, P] of UI.plotMap) if (!want.includes(id) || P.W !== W) { P.el.remove(); UI.plotMap.delete(id); }
  let prev = null;
  UI.plotEls = want.map((id) => {
    let P = UI.plotMap.get(id);
    const d = W.decl.get(id);
    if (!P) {
      const pt = el("span", { class: "in-pt" }), pv = el("span", { class: "in-pv mono" });
      const cv = el("canvas", { class: "in-cv" });
      P = { id, W, head: el("div", { class: "in-ph" }, pt, pv), pt, cv, val: pv };
      P.el = el("div", { class: "in-plot" }, P.head, cv);
      cv.addEventListener("mousemove", (e) => { const r = cv.getBoundingClientRect(); I.hover = { id, x: e.clientX - r.left }; I.dirty = true; });
      cv.addEventListener("mouseleave", () => { I.hover = null; I.dirty = true; });
      UI.plotMap.set(id, P);
    }
    P.d = d;
    const text = withUnit(title(W, d), d.unit);
    if (P.pt.textContent !== text) P.pt.textContent = text;
    place(UI.plots, P.el, prev); prev = P.el;
    return P;
  });
  I.listRev++; I.dirty = true;
}

function csvHref() {
  const W = shownW();
  if (!W) return "";
  const ids = I.selected.filter((id) => W.decl.has(id));
  if (!ids.length) return "";
  const q = new URLSearchParams({ ids: ids.join(","), world: String(W.n), format: "csv", lang: lang() });
  if (UI.upto.checked && I.ctx) q.set("to", String(I.ctx.t()));
  return url(`api/runs/${encodeURIComponent(runId)}/series?${q}`);
}

// a recording's CSV, made here: the header as the server's (the time with its unit, then each quantity's label with its
// unit and id), the values as JavaScript writes them (shortest round trip, "." as the decimal point), the frames the
// recording kept (one in k of the run: said in the time column's header)
const csvCell = (x) => { const s = String(x); return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
function csvBlob() {
  const W = shownW();
  if (!W) return null;
  const ids = I.selected.filter((id) => W.decl.has(id));
  if (!ids.length) return null;
  const k = Math.max(1, (I.recStride || 1) * W.stride);
  const head = [k > 1 ? t("t, {unit} (from the recording: one frame in {k:d} of the run)", { unit: W.tUnit, k })
    : t("t, {unit} (from the recording: every frame)", { unit: W.tUnit })];
  for (const id of ids) {
    const d = W.decl.get(id), label = title(W, d);
    head.push(d.unit ? t("{label}, {unit} [{id}]", { label, unit: d.unit, id }) : t("{label} [{id}]", { label, id }));
  }
  const upto = UI.upto.checked && I.ctx ? I.ctx.t() : Infinity;
  const rows = [head.map(csvCell).join(",")];
  for (let i = 0; i < W.t.length; i++) {
    if (W.t[i] > upto) break;
    rows.push([String(W.t[i]), ...ids.map((id) => { const v = (W.v.get(id) || [])[i]; return Number.isFinite(v) ? String(v) : ""; })].join(","));
  }
  const name = `${String(REC).replace(/[^\w.-]+/g, "-")}-w${W.n}-series.csv`;
  return { blob: new Blob([rows.join("\r\n") + "\r\n"], { type: "text/csv;charset=utf-8" }), name };
}

// --- drawing ----------------------------------------------------------------------------------------------------
function loop() {
  requestAnimationFrame(loop);
  if (I.replaying || !I.ctx || !UI.plotEls) return;
  const W = shownW();
  if (!W) return;
  const tt = I.ctx.t();
  const key = `${I.ctx.w()}|${tt}|${W.t.length}|${W.t[W.t.length - 1]}|${I.listRev}|${I.hover ? I.hover.id + I.hover.x : ""}`;
  if (!I.dirty && key === I.drawnKey) return;
  const now = performance.now();
  // the cursor or the world moved: at once; new points of a recording only: at most ~12 times a second
  const moved = key.split("|").slice(0, 2).join("|") !== I.drawnKey.split("|").slice(0, 2).join("|") || !!I.hover;
  if (!moved && now - I.lastDraw < 80) return;
  if (W !== I.lastWorld) { I.lastWorld = W; refreshLists(); }
  I.drawnKey = key; I.dirty = false; I.lastDraw = now;
  const i = atT(W, tt);
  for (const [id, R] of UI.rows) {
    const a = W.v.get(id), d = W.decl.get(id);
    const x = a && i >= 0 ? a[i] : NaN;
    const text = fmtV(x, d && d.unit);
    if (R.val.textContent !== text) R.val.textContent = text;
    const tip = Number.isFinite(x) ? "" : (W.notes[id] || t("no value at this moment"));
    if (R.val.title !== tip) R.val.title = tip;
  }
  for (const P of UI.plotEls) drawPlot(W, P, tt, i);
  const h = REC ? (UI.csvUrl || "#") : csvHref() || "#";
  if (UI.csv.getAttribute("href") !== h) UI.csv.setAttribute("href", h);
}

function sizeCanvas(cv) {
  const r = cv.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.max(1, Math.round(r.width * dpr)), h = Math.max(1, Math.round(r.height * dpr));
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  return { w: r.width, h: r.height, dpr };
}

function range(a, from = 0, to = a.length) {
  let lo = Infinity, hi = -Infinity;
  for (let k = from; k < to; k++) { const x = a[k]; if (Number.isFinite(x)) { if (x < lo) lo = x; if (x > hi) hi = x; } }
  return lo <= hi ? [lo, hi] : null;
}

function axes(g, w, h, x0, x1, y0, y1, X, Y, fx, fy) {
  g.strokeStyle = css("--grid"); g.fillStyle = css("--muted"); g.font = "10px system-ui"; g.lineWidth = 1;
  const sy = nice((y1 - y0) / 3), sx = nice((x1 - x0) / Math.max(2, w / 90));
  for (let y = Math.ceil(y0 / sy) * sy; y <= y1 + 1e-12 * Math.abs(y1); y += sy) {
    const py = Math.round(Y(y)) + 0.5;
    g.beginPath(); g.moveTo(0, py); g.lineTo(w, py); g.stroke();
    g.fillText(fy(Math.abs(y) < 1e-12 * sy ? 0 : y), 3, py - 2);
  }
  for (let x = Math.ceil(x0 / sx) * sx; x <= x1; x += sx) {
    const px = Math.round(X(x)) + 0.5;
    g.beginPath(); g.moveTo(px, 0); g.lineTo(px, h - 12); g.stroke();
    g.fillText(fx(x), px + 2, h - 2);
  }
}

function polyline(g, T, A, X, Y, from, to) {  // NaN breaks the line; dense stretches drawn as per-pixel min/max
  let open = false, col = null, mn = 0, mx = 0, last = 0;
  const flush = () => { if (col !== null) { g.lineTo(col, Y(mn)); g.lineTo(col, Y(mx)); g.lineTo(col, Y(last)); } };
  g.beginPath();
  for (let k = from; k < to; k++) {
    const y = A[k];
    if (!Number.isFinite(y)) { flush(); col = null; open = false; continue; }
    const px = Math.round(X(T[k]));
    if (open && px === col) { if (y < mn) mn = y; if (y > mx) mx = y; last = y; continue; }
    flush();
    if (!open) { g.moveTo(px, Y(y)); open = true; } else g.lineTo(px, Y(y));
    col = px; mn = mx = last = y;
  }
  flush();
  g.stroke();
}

function drawPlot(W, P, tt, iCur) {
  const { w, h, dpr } = sizeCanvas(P.cv);
  const g = fresh2d(P.cv.getContext("2d"), dpr);
  g.fillStyle = css("--canvas"); g.fillRect(0, 0, P.cv.width / dpr, P.cv.height / dpr);
  const A = W.v.get(P.id) || [], T = W.t;
  const d = P.d;
  const cur = iCur >= 0 && A.length ? A[iCur] : NaN;
  if (!T.length || !A.length) { if (P.val.textContent !== "—") P.val.textContent = "—"; g.fillStyle = css("--muted"); g.font = "11px system-ui"; g.fillText(t("no recorded values"), 8, h / 2); return; }
  const yr = range(A);
  let [y0, y1] = yr || [0, 1];
  if (y1 - y0 <= 1e-12 * Math.max(Math.abs(y0), Math.abs(y1))) { const p = Math.max(Math.abs(y0) * 1e-3, 1e-12); y0 -= p; y1 += p; }
  const pad = 0.08 * (y1 - y0); y0 -= pad; y1 += pad;
  let x0 = T[0], x1 = T[T.length - 1];
  if (!(x1 > x0)) x1 = x0 + 1;
  const L = 2, R = w - 4, TOP = 4, BOT = h - 14;
  const X = (x) => L + (x - x0) / (x1 - x0) * (R - L), Y = (y) => BOT - (y - y0) / (y1 - y0) * (BOT - TOP);
  axes(g, w, h, x0, x1, y0, y1, X, Y, (x) => fmtT(W, x), (y) => num(y, 4));
  const xc = Math.max(L, Math.min(R, X(tt)));
  const accent = css("--accent");
  g.lineWidth = 2; g.lineJoin = "round"; g.strokeStyle = accent;
  g.save(); g.beginPath(); g.rect(0, 0, xc + 1, h); g.clip(); polyline(g, T, A, X, Y, 0, T.length); g.restore();
  g.save(); g.globalAlpha = 0.28; g.beginPath(); g.rect(xc + 1, 0, w, h); g.clip(); polyline(g, T, A, X, Y, 0, T.length); g.restore();
  g.strokeStyle = css("--muted"); g.lineWidth = 1;
  g.beginPath(); g.moveTo(Math.round(xc) + 0.5, 0); g.lineTo(Math.round(xc) + 0.5, BOT); g.stroke();
  if (Number.isFinite(cur)) { g.fillStyle = accent; g.beginPath(); g.arc(X(T[iCur]), Y(cur), 3.5, 0, 2 * Math.PI); g.fill(); }
  let text = `${fmtV(cur, d.unit)} · ${fmtT(W, tt)}`;
  if (!Number.isFinite(cur) && W.notes[P.id]) text = `— (${W.notes[P.id]})`;
  if (I.hover && I.hover.id === P.id) {  // a crosshair and the value under the pointer
    const th = x0 + (I.hover.x - L) / (R - L) * (x1 - x0), k = atT(W, th);
    if (k >= 0) {
      g.setLineDash([3, 3]); g.strokeStyle = css("--muted");
      g.beginPath(); g.moveTo(Math.round(X(T[k])) + 0.5, 0); g.lineTo(Math.round(X(T[k])) + 0.5, BOT); g.stroke(); g.setLineDash([]);
      if (Number.isFinite(A[k])) { g.strokeStyle = accent; g.lineWidth = 2; g.beginPath(); g.arc(X(T[k]), Y(A[k]), 4, 0, 2 * Math.PI); g.stroke(); }
      text = t("under the pointer: {v} · {t}", { v: fmtV(A[k], d.unit), t: fmtT(W, T[k]) });
    }
  }
  if (P.val.textContent !== text) P.val.textContent = text;
}

// --- sweeps -------------------------------------------------------------------------------------------------------
async function vizSchema() {
  if (I.viz) return I.viz;
  const meta = await getJSON(url(`api/runs/${encodeURIComponent(runId)}`));
  I.viz = await getJSON(url(`api/viz/${encodeURIComponent(meta.viz)}`));
  return I.viz;
}

// a palette type's handles (API §1): the parameters a drag changes — the position's (a list, or {param, axis_param})
// and the velocity's
function handleOf(ot, pid) {
  const h = (ot && ot.handles) || {};
  const pos = h.position;
  if (Array.isArray(pos) && pos.includes(pid)) return { kind: "position", index: pos.indexOf(pid) };
  if (pos && typeof pos === "object" && !Array.isArray(pos) && pos.param === pid) return { kind: "position", axisParam: pos.axis_param };
  if (Array.isArray(h.velocity) && h.velocity.includes(pid)) return { kind: "velocity" };
  return null;
}
const AXES = ["x", "y", "z"];
const axisIndex = (v) => (AXES.includes(v) ? AXES.indexOf(v) : [0, 1, 2, "0", "1", "2"].includes(v) ? Number(v) : -1);

function targets(W) {  // what a sweep can change: the live laws in force here, every object's parameters shown for it
  const out = [];
  const lawValues = { ...W.params, ...W.live };
  for (const p of (I.viz ? I.viz.schema.params : []).filter((q) => q.live && !q.hidden && q.type !== "json" && shown(q, lawValues))) {
    out.push({ key: "law:" + p.id, target: { kind: "law", id: p.id }, label: t("Law: {label}", { label: withUnit(p.label, p.unit) }), p, current: W.live[p.id] });
  }
  for (const [oid, o] of W.objects) {
    const ot = W.palette.find((x) => x.type === o.type);
    for (const p of (ot ? ot.params : []).filter((q) => q.type !== "json" && !q.hidden && shown(q, o.values))) {
      out.push({ key: `obj:${oid}:${p.id}`, target: { kind: "object", obj: oid, param: p.id }, label: t("“{object}”: {label}", { object: o.label, label: withUnit(p.label, p.unit) }),
                 p, current: o.values[p.id], oid, handle: handleOf(ot, p.id) });
    }
  }
  return out;
}

// values typed by the owner: separated by ";", spaces or ", " (a comma between digits is a decimal comma)
export function parseValues(text, p) {
  const toks = String(text).split(/;|\s+|,(?!\d)/).map((s) => s.trim()).filter(Boolean);
  const out = [];
  for (const s of toks) {
    if (p.type === "float" || p.type === "int") {
      const r = parseNum(s), x = r.value;  // a decimal comma or point (review i18n-browser F1)
      if (r.err === "ambiguous") throw new Error(t("in “{value}” the comma may separate thousands or decimals — type {a} or {b}", { value: s, a: r.a, b: r.b }));
      if (r.err) throw new Error(t("“{value}” is not a number", { value: s }));
      out.push(p.type === "int" ? Math.round(x) : x);
    } else if (p.type === "bool") out.push(/^(1|true|yes|on)$/i.test(s) || s.toLowerCase() === t("yes").toLowerCase());
    else {
      const o = (p.options || []).find((q) => String(q.value) === s || t(q.label) === s);
      if (!o) throw new Error(t("“{value}” — there is no such option; allowed: {options}", { value: s, options: (p.options || []).map((q) => q.value).join(", ") }));
      out.push(o.value);
    }
  }
  return out;
}

function inp(attrs) { return el("input", { type: "text", ...attrs }); }
// a number in a field of the form, in the viewer's format without thousands separators (the values are separated by
// spaces and ";"), and read back with either decimal separator (review i18n-browser F1, F2)
const fmtIn = (x) => fmtField(Number(x.toPrecision(6))).replace(/[\s\u00a0\u202f]/g, "");
const readIn = (s) => { const r = parseNum(s); return r.err ? NaN : r.value; };
const numIn = (e, what) => { const v = readIn(e.value); if (!Number.isFinite(v)) throw new Error(t("{what}: a number is needed", { what })); return v; };

// the world time a sweep computes by default (review F2, X7: "1" in the world's unit asked p03 for 1 s of molecular
// dynamics and p02 for 10¹³ of its spans): five wall seconds of the world at the speed chosen, else a tenth of what the
// record covers, else one unit
function defaultDuration(W) {
  if (W.speed > 0) return 5 * W.speed;
  const T = W.t;
  if (T.length > 1 && T[T.length - 1] > T[0]) return (T[T.length - 1] - T[0]) / 10;
  return 1;
}

function ensureSweepForm() {
  const W = latestW();
  if (!W || !UI.sweep) return;
  if (UI.form && UI.form.W === W) { updateSweepForm(); return; }  // built once per world: what was typed stays (F8)
  drawSweepForm();
}

async function drawSweepForm() {
  const W = latestW();
  if (!W || !UI.sweep || I.formBuilding) return;
  I.formBuilding = true;
  try { await vizSchema(); } catch (e) { I.formBuilding = false; fill(UI.sweep, el("div", { class: "muted" }, t("The world's schema did not load: {why}", { why: e.message }))); return; }
  I.formBuilding = false;
  if (UI.form && UI.form.W === W) { updateSweepForm(); return; }
  const F = UI.form = { W, tgKeys: "", msKeys: "" };
  F.none = el("div", { class: "muted" });
  F.target = el("select", {});
  F.values = inp({ placeholder: t("for example: 1; 2; 4; 8"), style: { width: "100%" } });
  F.cur = el("div", { class: "help in-cur" });
  F.rFrom = inp({ placeholder: t("from"), style: { width: "4.5em" } }); F.rTo = inp({ placeholder: t("to"), style: { width: "4.5em" } });
  F.rN = inp({ value: "8", style: { width: "2.5em" }, title: t("How many values (2–50)") });
  F.rLog = el("select", {}, el("option", { value: "lin" }, t("evenly")), el("option", { value: "log" }, t("logarithmically")));
  const fillRange = () => {
    const a = readIn(F.rFrom.value), b = readIn(F.rTo.value), n = Math.round(readIn(F.rN.value));
    if (!Number.isFinite(a) || !Number.isFinite(b) || !(n >= 2 && n <= 50)) { toast(t("A series: “from” and “to” are numbers, from 2 to 50 values"), "notice", 4000); return; }
    if (F.rLog.value === "log" && !(a > 0 && b > 0)) { toast(t("A logarithmic series is only for positive numbers"), "notice", 4000); return; }
    const vals = [];
    for (let i = 0; i < n; i++) {
      const s = i / (n - 1);
      vals.push(F.rLog.value === "log" ? a * (b / a) ** s : a + (b - a) * s);
    }
    F.values.value = vals.map((x) => fmtIn(x)).join("; ");
    invalidate();
  };
  const dur = defaultDuration(W);
  F.ts = tScale(W.tUnit, dur);  // the form's time unit: of the world's scale (X7)
  F.duration = inp({ size: 7, value: fmtIn(dur / F.ts.k) });
  F.measure = el("select", {});
  F.stat = el("select", {}, Object.entries(STAT_LABEL).map(([k, v]) => el("option", { value: k }, v)));
  F.window = inp({ size: 6, value: fmtIn(dur / 2 / F.ts.k) });
  F.winRow = el("div", { class: "ctl" }, el("label", {}, t("window, {unit}", { unit: F.ts.u })), F.window);
  F.samples = inp({ size: 5, value: "200" });
  F.dt = el("span", { class: "muted in-dt" });
  F.est = el("div", { class: "help in-est" });
  F.go = el("button", { class: "primary", disabled: true }, t("▶ Start the sweep"));
  F.estBtn = el("button", {}, t("Estimate"));
  const invalidate = F.invalidate = () => { F.go.disabled = true; I.est = null; F.est.classList.remove("in-bad"); F.est.textContent = t("First “Estimate”: the cost of computing from this world's step time."); showDt(); };
  const showDt = () => {  // the readings' spacing, next to their number (F7)
    try {
      const n = Math.round(numIn(F.samples, t("Readings"))), span = (F.stat.value === "mean_last" ? numIn(F.window, t("Window")) : numIn(F.duration, t("How long to compute"))) * F.ts.k;
      F.dt.textContent = F.stat.value === "final" ? t("one reading at the end") : n >= 1 ? t("{n:d} readings {dt} apart", { n: n + 1, dt: fmtTime(span / n, W.tUnit) }) : "";
    } catch (e) { F.dt.textContent = ""; }
  };
  F.target.onchange = () => { showCur(); invalidate(); };
  F.stat.onchange = () => { F.winRow.style.display = F.stat.value === "mean_last" ? "" : "none"; F.samples.disabled = F.stat.value === "final"; invalidate(); };
  for (const x of [F.values, F.duration, F.measure, F.window, F.samples]) x.addEventListener("input", invalidate);
  F.measure.addEventListener("change", invalidate);
  F.estBtn.onclick = () => submit(true);
  F.go.onclick = () => submit(false);
  F.stat.onchange();
  UI.sweepRes = UI.sweepRes || el("div", { class: "in-sres" });
  UI.sweepList = UI.sweepList || el("div", { class: "in-slist" });
  F.body = el("div", {},
    el("div", { class: "ctl" }, el("label", {}, t("What to change")), F.target), F.cur,
    el("div", { class: "ctl" }, el("label", {}, t("Values")), F.values),
    el("div", { class: "in-row" }, el("span", { class: "muted" }, t("series:")), F.rFrom, F.rTo, F.rN, F.rLog, el("button", { onclick: fillRange, title: t("Fill “Values” with this series") }, "→")),
    el("div", { class: "ctl" }, el("label", {}, t("How long to compute, {unit}", { unit: F.ts.u })), F.duration),
    el("div", { class: "ctl" }, el("label", {}, t("What to measure")), F.measure),
    el("div", { class: "ctl" }, el("label", {}, t("What to take")), F.stat), F.winRow,
    el("div", { class: "ctl" }, el("label", { title: t("Readings over the computed time (one for “at the end”)") }, t("Readings")), F.samples, F.dt),
    el("div", { class: "in-row" }, F.estBtn, F.go), F.est);
  fill(UI.sweep,
    el("div", { class: "help" }, t("The same experiment from the current moment of the latest world — for each value of the parameter separately, in a separate process; the running world does not change. The chosen quantity is measured.")),
    F.none, F.body, UI.sweepRes, UI.sweepList);
  updateSweepForm();
  invalidate();
}

// the form's lists follow the world (objects added or removed, laws in force, what it measures now) in place: the choice
// and everything typed stay (F8)
function updateSweepForm() {
  const F = UI.form, W = latestW();
  if (!F || F.W !== W) return;
  const tg = targets(W);
  const now = W.current || new Set(W.decl.keys());
  const empty = !tg.length || !now.size;
  F.none.textContent = !now.size ? t("The world reports no measurable quantities: there is nothing to measure.") : !tg.length ? t("There is nothing to sweep in this world: no laws that change on the go and no objects in the scene.") : "";
  F.none.style.display = empty ? "" : "none";
  F.body.style.display = empty ? "none" : "";
  const tKeys = tg.map((x) => x.key + "=" + x.label).join("|");
  if (tKeys !== F.tgKeys) {
    F.tgKeys = tKeys;
    const was = F.target.value;
    fill(F.target, tg.map((x) => el("option", { value: x.key }, x.label)));
    if (tg.some((x) => x.key === was)) F.target.value = was;
  }
  const ms = groups(W, now);
  const mKeys = [...ms].map(([g, l]) => g + ":" + l.map((d) => d.id + "=" + title(W, d)).join(",")).join("|");
  if (mKeys !== F.msKeys) {
    F.msKeys = mKeys;
    const was = F.measure.value;
    fill(F.measure, [...ms].map(([g, list]) => el("optgroup", { label: g }, list.map((d) => el("option", { value: d.id }, withUnit(title(W, d), d.unit))))));
    if ([...F.measure.options].some((o) => o.value === was)) F.measure.value = was;
  }
  showCur();
}

// what the chosen parameter is now (F1): a law's value in force; an object's stored value — for a position also where
// the object is in the latest frame, for a velocity that it was the last throw's
function showCur() {
  const F = UI.form, W = latestW();
  if (!F) return;
  const x = targets(W).find((q) => q.key === F.target.value);
  if (!x) { F.cur.textContent = ""; return; }
  const p = x.p, unit = p.unit && !hasUnit(t(p.label), t(p.unit)) ? t(p.unit) : "";
  const v = (y) => (typeof y === "number" ? num(y, 6) + (unit ? " " + unit : "") : y === undefined ? "—" : String(y) + (unit ? " " + unit : ""));
  const range = (p.min !== null && p.min !== undefined ? " · " + t("at least {lo:.6g}", { lo: p.min }) : "") + (p.max !== null && p.max !== undefined ? " · " + t("at most {hi:.6g}", { hi: p.max }) : "");
  let text;
  if (x.target.kind === "law") text = t("Now: {v}", { v: v(x.current) });
  else if (x.handle && x.handle.kind === "position") {
    const o = W.objects.get(x.oid), at = (W.at || {})[x.oid];
    const i = x.handle.index !== undefined ? x.handle.index : axisIndex(o && o.values[x.handle.axisParam]);
    text = Array.isArray(at) && i >= 0 && typeof at[i] === "number"
      ? t("Set: {v} — where the object was put; the object is now at {at} (the last frame). Each value puts it there at the moment of the sweep, including one equal to the set value", { v: v(x.current), at: v(at[i]) })
      : t("Set: {v} — where the object was put. Each value puts it there at the moment of the sweep, including one equal to the set value", { v: v(x.current) });
  } else if (x.handle && x.handle.kind === "velocity") {
    text = t("Set: {v} — the velocity of the last throw; it may be different now. Each value is a throw with this velocity at the moment of the sweep", { v: v(x.current) });
  } else text = t("Set: {v} — the value of the object's parameter, not necessarily its state now. Each value is applied at the moment of the sweep, including one equal to the set value", { v: v(x.current) });
  F.cur.textContent = text + range;
}

function request(estimate) {
  const F = UI.form, W = latestW();
  const x = targets(W).find((q) => q.key === F.target.value);
  if (!x) throw new Error(t("Choose what to change"));
  const values = parseValues(F.values.value, x.p);
  if (!values.length) throw new Error(t("Type the values (separated by “;” or a space)"));
  const body = { target: x.target, values, duration: numIn(F.duration, t("How long to compute")) * F.ts.k, measure: F.measure.value, stat: F.stat.value };
  if (F.stat.value === "mean_last") body.window = numIn(F.window, t("Window")) * F.ts.k;
  if (F.stat.value !== "final") body.n_samples = Math.round(numIn(F.samples, t("Readings")));
  if (estimate) body.estimate = true;
  return body;
}

async function submit(estimate) {
  const F = UI.form;
  let body;
  try { body = request(estimate); } catch (e) { F.est.textContent = e.message; F.est.classList.add("in-bad"); return; }
  F.est.classList.remove("in-bad");
  const sweepUrl = url(`api/runs/${encodeURIComponent(runId)}/sweep`);
  F.estBtn.disabled = F.go.disabled = true;
  try {
    const r = await fetch(sweepUrl, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      const text = j.error !== undefined ? (j.hint ? t("{text}. What to change: {hint}", { text: t(j.error), hint: t(j.hint) }) : t(j.error)) : r.statusText;
      F.est.textContent = text + (j.estimate ? ` (${t(j.estimate.text)})` : "");
      F.est.classList.add("in-bad");
      return;
    }
    if (estimate) {
      I.est = JSON.stringify({ ...body, estimate: undefined });
      F.est.textContent = t(j.estimate.text);
      F.go.disabled = false;
      return;
    }
    F.invalidate();  // the estimate was this sweep's: the next one is estimated anew (X7)
    toast(t("Sweep no. {n:d} started", { n: j.n }), "notice", 3000);
    I.sweepShown = j.n;
    pollSweep(j.n);
  } catch (e) {
    F.est.textContent = t("The server did not answer: {why}", { why: e.message }); F.est.classList.add("in-bad");
  } finally {
    F.estBtn.disabled = false;
    if (!estimate) F.go.disabled = true;
  }
}

async function loadSweeps() {
  try { I.sweeps = await getJSON(url(`api/runs/${encodeURIComponent(runId)}/sweeps`)); } catch (e) { I.sweeps = []; }
  drawSweepList();
  const act = I.sweeps.find((s) => s.active);
  if (act) { I.sweepShown = act.n; pollSweep(act.n); } else if (I.sweepShown === null && I.sweeps.length) showSweep(I.sweeps[I.sweeps.length - 1].n);
}

let listText = "";
function drawSweepList() {
  if (!UI.sweepList) return;
  const key = JSON.stringify(I.sweeps.map((s) => [s.n, s.state, s.n === I.sweepShown]));
  if (key === listText) return;  // unchanged: nothing rebuilt
  listText = key;
  if (!I.sweeps.length) { fill(UI.sweepList); return; }
  fill(UI.sweepList, el("div", { class: "muted" }, t("Sweeps of this run:")),
    I.sweeps.slice().reverse().map((s) => el("div", { class: "in-si" + (s.n === I.sweepShown ? " on" : ""), onclick: () => showSweep(s.n), title: t("Show the results") },
      t("no. {n:d} · {target} · {k:d} values → {measure} · {state}", { n: s.n, target: t(s.target_label), k: (s.request || {}).values ? s.request.values.length : 0, measure: t(s.measure_label), state: STATE_TEXT[s.state] || s.state }))));
}

async function showSweep(n) {
  I.sweepShown = n;
  try { renderSweep(await getJSON(url(`api/runs/${encodeURIComponent(runId)}/sweeps/${n}`))); } catch (e) { fill(UI.sweepRes, el("div", { class: "muted" }, e.message)); UI.res = null; }
  drawSweepList();
}

function pollSweep(n) {
  clearTimeout(I.poll);
  const tick = async () => {
    let s;
    try { s = await getJSON(url(`api/runs/${encodeURIComponent(runId)}/sweeps/${n}`)); } catch (e) { return; }
    if (I.sweepShown === n) renderSweep(s);
    if (s.active || s.state === "starting" || s.state === "running") I.poll = setTimeout(tick, 700);
    else { loadSweeps(); if (s.state !== "done") toast(s.message ? t(s.message) : STATE_TEXT[s.state], "notice", 6000); }
  };
  tick();
}

// a sweep's result block, built once per sweep and then updated in place (F8): the state, the progress, new table rows
function buildRes(s) {
  const R = { n: s.n, rows: 0 };
  R.state = el("span", {});
  R.cancel = el("button", { class: "cancel" }, t("✕ cancel"));
  R.cancel.onclick = async () => {
    R.cancel.disabled = true; R.cancel.textContent = t("cancelling…");  // one click is enough (F10)
    try { await postJSON(url(`api/runs/${encodeURIComponent(runId)}/sweeps/${R.n}/cancel`)); } catch (e) { toast(e.message); }
  };
  R.remove = el("button", { title: t("Remove this sweep and its results") }, t("remove"));
  R.remove.onclick = async () => {
    R.remove.disabled = true;
    try { await postJSON(url(`api/runs/${encodeURIComponent(runId)}/sweeps/${R.n}`), undefined, "DELETE"); I.sweepShown = null; fill(UI.sweepRes); UI.res = null; loadSweeps(); } catch (e) { toast(e.message); R.remove.disabled = false; }
  };
  R.what = el("div", { class: "help in-what" });
  R.base = el("div", { class: "help in-warn" });
  R.bar = el("div", {});
  R.prog = el("div", { class: "help" });
  R.progBox = el("div", {}, el("div", { class: "in-bar" }, R.bar), R.prog);
  R.msg = el("div", { class: "help in-msg" });
  R.cv = el("canvas", { class: "in-cv in-scv" });
  R.th1 = el("th", {}); R.th2 = el("th", {});
  R.tbody = el("tbody", {});
  R.table = el("table", { class: "in-tab" }, el("thead", {}, el("tr", {}, R.th1, R.th2)), R.tbody);
  R.csv = el("a", { href: url(`api/runs/${encodeURIComponent(runId)}/sweeps/${s.n}?format=csv&lang=${lang()}`), class: "in-csv" }, t("⤓ CSV of the table"));
  R.el = el("div", {}, el("div", { class: "in-sh" }, el("b", {}, t("Sweep no. {n:d}: ", { n: s.n })), R.state, " ", R.cancel, R.remove),
    R.what, R.base, R.progBox, R.msg, R.cv, R.table, R.csv);
  return R;
}

const setText = (e, s) => { if (e.textContent !== s) e.textContent = s; };
const show = (e, on) => { const d = on ? "" : "none"; if (e.style.display !== d) e.style.display = d; };

function renderSweep(s) {
  I.sweepData = s;
  let R = UI.res;
  if (!R || R.n !== s.n || !R.el.isConnected) { R = UI.res = buildRes(s); fill(UI.sweepRes, R.el); }
  const res = s.results || [], req = s.request || {}, prog = s.progress || {};
  const running = s.active || s.state === "starting" || s.state === "running";
  setText(R.state, STATE_TEXT[s.state] || s.state);
  show(R.cancel, running); show(R.remove, !running);
  const tu = s.t_unit || "s";
  setText(R.what, t("{target} → {measure}, {stat}; each value — {duration} of the world from t = {t}", { target: t(s.target_text), measure: t(s.measure_label), stat: t(s.stat_text), duration: fmtTime(req.duration, tu), t: fmtTime((s.base || {}).t, tu) }));
  setText(R.base, t((s.base || {}).note)); show(R.base, !!(s.base || {}).note);
  show(R.progBox, running);
  const w = `${Math.round(100 * (prog.frac || 0))}%`;
  if (R.bar.style.width !== w) R.bar.style.width = w;
  setText(R.prog, t("{k:d} of {n:d} values", { k: prog.done || 0, n: prog.total || 0 }) + (prog.elapsed_s ? " · " + t("{t:d} s", { t: Math.round(prog.elapsed_s) }) : "") + (prog.eta_s ? " · " + t("≈ {t:d} s left", { t: Math.round(prog.eta_s) }) : ""));
  setText(R.msg, t(s.message)); show(R.msg, !!s.message);
  R.msg.classList.toggle("in-warn", s.state !== "done");
  setText(R.th1, withUnit(s.target_label || t("value"), s.target_unit || ""));
  setText(R.th2, withUnit(t("{label} ({stat})", { label: s.measure_label, stat: s.stat_text }), s.measure_unit || ""));
  const fmtX = (v) => (typeof v === "number" ? num(v, 6) : String(v));
  for (; R.rows < res.length; R.rows++) {  // the table grows by rows: what is there stays (F8)
    const r = res[R.rows];
    R.tbody.append(el("tr", { title: t(r.error || r.note) }, el("td", { class: "mono" }, fmtX(r.value)),
      el("td", { class: "mono" + (r.error ? " in-bad" : "") }, r.error ? "✗ " + t(r.error) : (r.measured === null || r.measured === undefined ? "— " + t(r.note) : num(r.measured, 8) + (r.note ? " ⚠" : "")))));
  }
  show(R.cv, res.length > 0); show(R.table, res.length > 0); show(R.csv, res.length > 0);
  drawSweepPlot();
}

function drawSweepPlot() {
  const s = I.sweepData, cv = UI.res && UI.res.cv;
  if (!s || !cv || !cv.isConnected || cv.style.display === "none") return;
  const { w, h, dpr } = sizeCanvas(cv);
  const g = fresh2d(cv.getContext("2d"), dpr);
  g.fillStyle = css("--canvas"); g.fillRect(0, 0, cv.width / dpr, cv.height / dpr);
  const pts = (s.results || []).filter((r) => typeof r.value === "number");
  const ok = pts.filter((r) => typeof r.measured === "number" && Number.isFinite(r.measured)).sort((a, b) => a.value - b.value);
  if (!pts.length) { g.fillStyle = css("--muted"); g.font = "11px system-ui"; g.fillText(t("the values are not numbers: see the table"), 8, h / 2); return; }
  const xs = pts.map((r) => r.value);
  let x0 = Math.min(...xs), x1 = Math.max(...xs);
  const log = x0 > 0 && x1 / x0 >= 100;
  const fx = (x) => (log ? Math.log10(x) : x);
  let a0 = fx(x0), a1 = fx(x1);
  if (!(a1 > a0)) { a0 -= 0.5; a1 += 0.5; }
  const pa = 0.06 * (a1 - a0); a0 -= pa; a1 += pa;
  const yr = range(ok.map((r) => r.measured)) || [0, 1];
  let [y0, y1] = yr;
  if (y1 - y0 <= 1e-12 * Math.max(Math.abs(y0), Math.abs(y1))) { const p = Math.max(Math.abs(y0) * 1e-3, 1e-12); y0 -= p; y1 += p; }
  const pad = 0.1 * (y1 - y0); y0 -= pad; y1 += pad;
  const L = 2, R = w - 6, TOP = 6, BOT = h - 14;
  const X = (a) => L + (a - a0) / (a1 - a0) * (R - L), Y = (y) => BOT - (y - y0) / (y1 - y0) * (BOT - TOP);
  axes(g, w, h, a0, a1, y0, y1, X, Y, (a) => num(log ? 10 ** a : a, 3), (y) => num(y, 4));
  const accent = css("--accent");
  g.strokeStyle = accent; g.lineWidth = 2; g.lineJoin = "round";
  g.beginPath(); ok.forEach((r, k) => { const px = X(fx(r.value)), py = Y(r.measured); if (k) g.lineTo(px, py); else g.moveTo(px, py); }); g.stroke();
  for (const r of ok) { g.fillStyle = css("--canvas"); g.beginPath(); g.arc(X(fx(r.value)), Y(r.measured), 5, 0, 2 * Math.PI); g.fill(); g.fillStyle = accent; g.beginPath(); g.arc(X(fx(r.value)), Y(r.measured), 4, 0, 2 * Math.PI); g.fill(); }
  g.strokeStyle = css("--bad"); g.lineWidth = 2;  // values without a number: × on the axis
  for (const r of pts) {
    if (ok.includes(r)) continue;
    const px = X(fx(r.value)), py = BOT - 4;
    g.beginPath(); g.moveTo(px - 4, py - 4); g.lineTo(px + 4, py + 4); g.moveTo(px + 4, py - 4); g.lineTo(px - 4, py + 4); g.stroke();
  }
  if (log) { g.fillStyle = css("--muted"); g.font = "10px system-ui"; g.fillText(t("a logarithmic scale of the values"), R - 170, TOP + 10); }
}

function injectStyle() {
  if (document.getElementById("lf-instruments-style")) return;
  document.head.append(el("style", { id: "lf-instruments-style" }, `
.in-panel .in-group > summary { cursor: pointer; color: var(--muted); font-size: 12px; margin-top: 4px; }
.in-q { display: grid; grid-template-columns: auto 1fr auto; gap: 4px; align-items: baseline; font-size: 12px; padding: 1px 0; cursor: pointer; }
.in-q .in-val { color: var(--muted); font-size: 11px; white-space: nowrap; }
.in-plots { display: flex; flex-direction: column; gap: 6px; margin-top: 6px; }
.in-plot { border: 1px solid var(--line); border-radius: 6px; padding: 3px 4px 2px; }
.in-ph { display: flex; justify-content: space-between; gap: 6px; font-size: 11px; }
.in-ph .in-pt { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.in-ph .in-pv { color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.in-cv { display: block; width: 100%; height: 110px; }
.in-scv { height: 150px; margin: 6px 0; border: 1px solid var(--line); border-radius: 6px; }
.in-row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 6px; }
.in-csv { font-size: 12px; }
.in-sweep-box { margin-top: 10px; }
.in-sweep-box > summary { cursor: pointer; font-weight: 600; font-size: 12px; }
.in-sweep .ctl { margin-top: 4px; }
.in-sweep .in-dt { font-size: 11px; margin-left: 6px; }
.in-bad { color: var(--bad); } .in-warn { color: var(--warn); }
.in-bar { height: 6px; background: var(--grid); border-radius: 3px; overflow: hidden; margin: 4px 0; }
.in-bar > div { height: 100%; background: var(--accent); }
.in-tab { width: 100%; border-collapse: collapse; font-size: 11px; }
.in-tab th { text-align: left; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--line); }
.in-tab td { border-bottom: 1px solid var(--grid); overflow-wrap: anywhere; }
.in-si { font-size: 11px; cursor: pointer; padding: 2px 0; } .in-si.on { color: var(--accent); }
.in-sh { margin-top: 8px; font-size: 12px; }
.in-sh button { font-size: 11px; padding: 1px 6px; margin-left: 4px; }
.in-sh button.cancel { border-color: var(--bad); color: var(--bad); }
`));
}

// the player's one entry point (player.js onMessage) and the tests' view of the panel
window.lfInstruments = {
  message,
  state: () => ({ worlds: I.worlds.map((W) => ({ n: W.n, points: W.t.length, decl: [...W.decl.keys()] })), selected: [...I.selected] }),
};
