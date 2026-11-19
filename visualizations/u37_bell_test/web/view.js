// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u37 view: the Bell test with real detectors. Three pictures: the set-up line (the source, the two stations with
// their analysers at the setting of the current slot, two detectors each with their clicks, the pairs in flight, and
// under each station the strip of its latest slots with their settings and outcomes «+», «−», «0», «±»); the spacetime
// of the last coincidence (its emission, the setting choices with their future light cones, the clicks); the
// statistics (the coincidence counts of the four setting pairs, E with errors, S under fair sampling against the bounds
// 2 and 2√2, S with the accidentals subtracted, CH and J of all the slots, the curves E(Δ) and S(Δ), or in the counting
// by slots the curve J(η)). Everything comes from the run: positions are interpolated along the computed straight paths
// (x = ±v (t − t_e)), clicks, settings, choice times and space-time relations are the run's own; the curves are
// computed by the engine (header) and are drawn only next to the measured points.
//
// The screens (EX2 design lfphys/sources/explore_EX2_2026-11-18_design.md §1.3, §4): with ctx.screen "watch",
// "explore" or "lab" the view has no quick set-up bar and no toolbar (the overlays below replace its check boxes, the
// screen's «normal / slow» its speeds); its right panels fold into «How we know this is right»; Lab work draws what
// Explore draws. Watch keeps a fixed band under the pictures for the caption (wide screens; on a phone the caption has
// its own place), so a caption never covers what it describes. Below 1000 px the statistics are on top, the set-up line
// a strip under them, the spacetime diagram folded. Each canvas exposes what it drew where (canvas.__layout: the boxes
// of its texts and parts) for tests/u37_screens.mjs.
import { fmt, t } from "/static/js/i18n.js";
import { css, el, fresh2d, num, panel, time } from "/static/js/ui.js";

// what the view accepts quantised (registry.view_declarations reads this literal): the drawn arrays only
export const QUANT_SAFE = { "header.cq": "u16", "header.ch": "u16", "header.sq": "u16", "header.sh": "u16", "header.sw": "u16" };
// the overlays it can toggle on the screens (registry.view_declarations reads the ids); defaults of Explore
export const OVERLAYS = [
  { id: "spacetime", label: "spacetime of the last coincidence", default: true },
  { id: "cones", label: "light cones", default: true },
  { id: "slots", label: "slot strips", default: true },
  { id: "e_delta", label: "E(Δ)", default: true },
  { id: "s_delta", label: "S(Δ)", default: true },
  { id: "other_law", label: "the other law's curves", default: true },
];
const SCREENS = new Set(["watch", "explore", "lab"]);

const COL_SET = ["#1c7ed6", "#ae3ec9"];      // setting 0 (a, b) and 1 (a′, b′)
const COL_PLUS = "#2b8a3e", COL_MINUS = "#e03131", COL_SRC = "#f08c00", COL_LHV = "#e8590c", COL_BOTH = "#f59f00";
const MAXDET = 20000, MAXCLK = 20000;  // above a story's details (1 000 frames × 6 coincidences, × 8 clicks): key frames restore
const NMIN = 30;  // coincidences per cell before an estimate is compared (the same rule as the run's checks)
const F_LOC_A = 1, F_LOC_B = 2, F_FREE_A = 4, F_FREE_B = 8, F_TRUE = 16;
const OUT_GLYPH = ["+", "−", "0", "±"];
const OUT_COL = [COL_PLUS, COL_MINUS, "#868e96", COL_BOTH];
const STAT_PX = 380, SET_PX = 104;  // a phone's heights of the statistics and of the set-up strip

let STYLE = false;
function addStyle() {
  if (STYLE) return;
  STYLE = true;
  document.head.append(el("style", {}, `
.u37-c { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.u37-panes { display: grid; flex: 1; min-height: 0; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  grid-template-rows: minmax(0, 0.9fr) minmax(0, 1.1fr); grid-template-areas: "set stat" "st stat"; }
.u37-panes > div { min-height: 0; min-width: 0; display: flex; flex-direction: column; }
.u37-set { grid-area: set; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.u37-st { grid-area: st; border-right: 1px solid var(--line); }
.u37-st > .u37-st-tg { display: none; }
.u37-stat { grid-area: stat; }
.u37-panes .canvas-wrap { flex: 1; min-height: 0; }
/* Watch: a fixed band for the caption laid over the stage's bottom (up to five lines of its text at 16 px, its padding
   and its 14 px offset), the same for every caption, so the pictures never move and no caption covers them */
.u37-c.u37-watch .u37-panes { margin-bottom: 184px; }
.u37-c.u37-noST .u37-panes { grid-template-areas: "set stat" "set stat"; }
.u37-c.u37-noST .u37-st { display: none; }
@media (max-width: 999px) {
  .dm-stage:has(> .u37-c) { aspect-ratio: auto; max-height: none; }
  .dm-stage > div.u37-c.u37-on { aspect-ratio: auto; min-height: 0; flex: none; }
  .u37-c.u37-on .u37-panes { flex: none; grid-template-columns: minmax(0, 1fr);
    grid-template-rows: ${STAT_PX}px ${SET_PX}px auto; grid-template-areas: "stat" "set" "st"; }
  .u37-c.u37-on .u37-set { border-right: 0; border-top: 1px solid var(--line); }
  .u37-c.u37-on .u37-st { border-right: 0; display: block; }
  .u37-c.u37-on .u37-st > .u37-st-tg { display: flex; width: 100%; min-height: 44px; align-items: center; gap: 6px; border: 0;
    border-radius: 0; padding: 0 10px; font-size: 13px; color: var(--muted); background: var(--panel); border-bottom: 1px solid var(--line);
    text-align: left; cursor: pointer; }
  .u37-c.u37-on .u37-st > .u37-st-tg::before { content: "▸"; }
  .u37-c.u37-on .u37-st.open > .u37-st-tg::before { content: "▾"; }
  .u37-c.u37-on .u37-st .canvas-wrap { display: none; height: 260px; }
  .u37-c.u37-on .u37-st.open .canvas-wrap { display: block; }
  .u37-c.u37-on.u37-noST .u37-st { display: none; }
  .u37-c.u37-watch .u37-panes { margin-bottom: 0; }
}
@media (max-width: 1000px) {
  .u37-c:not(.u37-on) .u37-panes { flex: 1 0 auto; grid-template-columns: minmax(0, 1fr);
    grid-template-rows: minmax(300px, 1fr) minmax(240px, 1fr) minmax(360px, 1.2fr); grid-template-areas: "set" "st" "stat"; }
  .u37-c:not(.u37-on) .u37-set, .u37-c:not(.u37-on) .u37-st { border-right: 0; }
}`));
}

export function createView(ctx) {
  let H = null, HB = null, det = newDet(), clk = newClk(), shownSlots = [];
  const SCR = SCREENS.has(ctx.screen);
  const on = Object.fromEntries(OVERLAYS.map((o) => [o.id, o.default]));
  let traces = [];
  addStyle();

  // --- DOM --------------------------------------------------------------------------------------------
  const live = (id, label) => (ctx.liveControl ? ctx.liveControl(id, { label }) : null);
  const cvSet = el("canvas"), cvST = el("canvas"), cvStat = el("canvas");
  // the spacetime pane: always shown on a wide screen; on a phone folded under a toggle (a <details> would not lay its
  // canvas out as a flex item)
  const stToggle = el("button", { class: "u37-st-tg", type: "button", "aria-expanded": "false" }, t("Spacetime of the last coincidence"));
  const stFold = el("div", { class: "u37-st", "data-u37": "st" }, stToggle, el("div", { class: "canvas-wrap" }, cvST));
  stToggle.onclick = () => { const o = !stFold.classList.contains("open"); stFold.classList.toggle("open", o); stToggle.setAttribute("aria-expanded", String(o)); redraw(); };
  const panes = el("div", { class: "u37-panes" },
    el("div", { class: "u37-set" }, el("div", { class: "canvas-wrap" }, cvSet)), stFold,
    el("div", { class: "u37-stat" }, el("div", { class: "canvas-wrap" }, cvStat)));
  let center;
  const infoBox = el("div", { class: "kv" }), countBox = el("div", {}), lastBox = el("div", { class: "events" });
  const rightPanels = [panel(t("Set-up and spacetime"), infoBox), panel(t("Counters"), countBox),
    panel(t("Last coincidences"), lastBox)];
  let btnClear = null;
  if (!SCR) {
    const quick = el("div", { class: "toolbar quick", title: t("Set-up: changes at once (the same as in the panel on the left)") },
      el("span", { class: "muted" }, t("Settings:")), live("a_deg", "a, °"), live("a2_deg", "a′, °"), live("b_deg", "b, °"),
      live("b2_deg", "b′, °"), live("switch", t("choice")), live("tau_ns", t("τ, ns")), live("rate", t("pairs/s")));
    const btnFly = el("button", { title: t("A speed at which the flight of one pair is seen (≈{s} s per flight)", { s: 2 }) }, t("▷ flight"));
    const btnStat = el("button", { title: t("A speed for collecting statistics (≈{n:d} pairs per second)", { n: 2000 }) }, t("▷▷ collect statistics"));
    btnClear = el("button", { title: t("The counts start anew (the action “Reset the statistics”)") }, t("⟲ reset the statistics"));
    const boxes = OVERLAYS.map((o) => {
      const cb = el("input", { type: "checkbox", checked: o.default, onchange: () => { on[o.id] = cb.checked; redraw(); } });
      return el("label", {}, cb, " ", t(o.label));
    });
    const toolbar = el("div", { class: "toolbar" }, btnFly, btnStat, btnClear, ...boxes);
    btnFly.onclick = () => lastF && ctx.send("speed", { value: Math.max(lastF.flight[0], lastF.flight[1]) / 2 });
    btnStat.onclick = () => lastF && ctx.send("speed", { value: 2000 / lastF.settings.rate });
    btnClear.onclick = () => ctx.action && ctx.action("clear", {});
    // an action acts at the end of a live run's record: on a recording, in the past or on an earlier world it is off,
    // with the reason as its tooltip (start-page review F2, STATUS V51 (f))
    const clearTitle = btnClear.title;
    const syncActions = () => { const why = ctx.readOnly ? ctx.readOnly() : ""; btnClear.disabled = !!why; btnClear.title = why || clearTitle; };
    window.addEventListener("editablechange", syncActions);
    syncActions();
    center = el("div", { class: "u37-c" }, quick, toolbar, panes);
  } else {
    center = el("div", { class: `u37-c u37-on u37-${ctx.screen}` }, panes);
  }
  for (const cv of [cvSet, cvST, cvStat]) new ResizeObserver(() => redraw()).observe(cv);
  function redraw() { if (ctx.requestRender) ctx.requestRender(); }

  let lastF = null, lastBlobs = {}, lastT = 0;

  // --- the run's details (coincidences and clicks) --------------------------------------------------------------
  function newDet() {
    return { n: 0, off: 0, tA: [], tB: [], te: [], id: [], sA: [], sB: [], oA: [], oB: [], alA: [], alB: [], tcA: [], tcB: [], fl: [] };
  }
  function newClk() { return { A: { t: [], d: [], s: [] }, B: { t: [], d: [], s: [] }, off: 0 }; }
  // a "pairs" message: its coincidences (times relative to the click at A, float32) and the stations' clicks (times
  // relative to the message's time)
  function pushDet(b, t0) {
    const m = b.c_tA ? b.c_tA.length : 0;
    for (let i = 0; i < m; i++) {
      const tA = b.c_tA[i];
      det.tA.push(tA); det.tB.push(tA + b.c_dtB[i]); det.te.push(tA + b.c_dte[i]);
      det.tcA.push(tA + b.c_dtcA[i]); det.tcB.push(tA + b.c_dtcB[i]);
      for (const k of ["id", "sA", "sB", "oA", "oB", "alA", "alB", "fl"]) det[k].push(b["c_" + k][i]);
    }
    det.n += m;
    if (det.n > MAXDET) {
      const cut = det.n - MAXDET;
      for (const k of Object.keys(det)) if (Array.isArray(det[k])) det[k].splice(0, cut);
      det.n = MAXDET; det.off += cut;
    }
    for (const s of ["A", "B"]) {
      const T = b[`k${s}_dt`];
      if (!T) continue;
      const c = clk[s];
      for (let i = 0; i < T.length; i++) { c.t.push(t0 + T[i]); c.d.push(b[`k${s}_d`][i]); c.s.push(b[`k${s}_s`][i]); }
      if (c.t.length > MAXCLK) { const cut = c.t.length - MAXCLK; for (const k of ["t", "d", "s"]) c[k].splice(0, cut); clk.off += cut; }
    }
  }
  function lastUpTo(tw) {  // index of the last coincidence completed at time t (-1: none)
    let lo = 0, hi = det.n;
    const done = (i) => Math.max(det.tA[i], det.tB[i]);
    while (lo < hi) { const m = (lo + hi) >> 1; if (done(m) <= tw) lo = m + 1; else hi = m; }
    return lo - 1;
  }

  // --- drawing helpers: every text's box is kept in the canvas's layout ------------------------------------------
  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr);
    cv.__layout = { w, h, texts: [], parts: {} };
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, w, h);
    return g;
  }
  // a text drawn and recorded (its box in CSS px): with maxW the font shrinks to 9 px, then the text wraps at spaces
  // into as many lines as it needs (each line fs + 2 px below the previous one); the box covers every line
  // (bottom: the last line at y, the lines above it: a footnote at a canvas's bottom wraps upwards)
  function text(g, cv, s, x, y, { align = "left", color = null, size = 12, bold = false, maxW = null, part = null, bottom = false } = {}) {
    let fs = size;
    const font = () => { g.font = `${bold ? "600 " : ""}${fs}px system-ui, sans-serif`; };
    font();
    if (maxW) while (g.measureText(s).width > maxW && fs > 9) { fs -= 0.5; font(); }
    let lines = [s];
    if (maxW && g.measureText(s).width > maxW) {
      lines = [];
      let cur = "";
      for (const w of s.split(" ")) {
        const tryS = cur ? `${cur} ${w}` : w;
        if (cur && g.measureText(tryS).width > maxW) { lines.push(cur); cur = w; } else cur = tryS;
      }
      if (cur) lines.push(cur);
    }
    if (color) g.fillStyle = color;
    g.textAlign = "left";
    if (bottom) y -= (lines.length - 1) * (fs + 2);
    let x0m = Infinity, x1m = -Infinity;
    lines.forEach((ln, i) => {
      const w = g.measureText(ln).width;
      const x0 = align === "right" ? x - w : align === "center" ? x - w / 2 : x;
      g.fillText(ln, x0, y + i * (fs + 2));
      x0m = Math.min(x0m, x0); x1m = Math.max(x1m, x0 + w);
    });
    const box = { s, x0: x0m, x1: x1m, y0: y - fs * 0.85, y1: y + (lines.length - 1) * (fs + 2) + fs * 0.25, part };
    cv.__layout.texts.push(box);
    return box;
  }
  // a trace's label at the top right of a plot, stacked under the previous one: the next label starts below this one's
  // box (a label wrapped into two or three lines included), and none is drawn past the plot's bottom
  function traceLabel(g, cv, s, x, y, fs, maxW, yMax) {
    if (y > yMax) return y;
    const b = text(g, cv, s, x, y, { align: "right", color: muted(), size: fs - 2, maxW, part: "trace" });
    return b.y1 + (fs - 2) * 0.85 + 3;
  }
  const ink = () => css("--ink") || "#222", muted = () => css("--muted") || "#888", lineC = () => css("--line") || "#ccc";
  const sign = (o) => (o > 0 ? "+" : "−");
  const oCol = (o) => (o > 0 ? COL_PLUS : COL_MINUS);
  const isPhoton = () => H && H.pair === "photon";
  function lenFmt(x) {
    const a = Math.abs(x);
    if (a >= 1e3) return t("{v:.4g} km", { v: x / 1e3 });
    if (a >= 1) return t("{v:.4g} m", { v: x });
    if (a >= 1e-3) return t("{v:.4g} mm", { v: x * 1e3 });
    return t("{v:.4g} µm", { v: x * 1e6 });
  }
  function setLabel(side, s) { return side === "A" ? (s ? "a′" : "a") : (s ? "b′" : "b"); }
  const slotsMode = () => H && H.counting === "slots";

  // the setting of a station at time tw: the run's choice for the current slot (sent with the frame), else the last
  // click's slot
  function activeSetting(f, side) {
    if (f.settings.switch === "fixed") return { s: 0, why: t("set by the mode “fixed”") };
    const ns = (f.now_slots || {})[side];
    if (ns && ns.length) return { s: ns[1], why: t("chosen for the current slot") };
    return { s: null, why: "" };
  }

  // --- the set-up line ----------------------------------------------------------------------------------------
  function drawSet(f, tw, blobs) {
    const cv = cvSet, g = setup(cv), W = cv.clientWidth, Hh = cv.clientHeight;
    if (W < 10 || Hh < 10) return;
    const S = f.settings, LA = S.LA, LB = S.LB, v = H.v;
    const narrow = W < 520;
    const mx = Math.min(narrow ? 70 : 120, W * 0.2);
    const X = (x) => mx + (W - 2 * mx) * (x + LA) / (LA + LB);
    const stripH = on.slots ? (narrow ? 34 : 44) : 0;
    const yc = Math.max(narrow ? 38 : 48, Math.min(Hh * 0.42, Hh - stripH - 46));
    const lay = cv.__layout.parts;
    g.strokeStyle = lineC(); g.lineWidth = 1; g.setLineDash([4, 4]);
    g.beginPath(); g.moveTo(X(-LA), yc); g.lineTo(X(LB), yc); g.stroke(); g.setLineDash([]);
    if (!narrow) {
      text(g, cv, `L_A = ${lenFmt(LA)}`, (X(0) + X(-LA)) / 2, yc - 9, { align: "center", color: muted(), size: 11 });
      text(g, cv, `L_B = ${lenFmt(LB)}`, (X(0) + X(LB)) / 2, yc - 9, { align: "center", color: muted(), size: 11 });
    }
    g.fillStyle = COL_SRC; g.beginPath(); g.arc(X(0), yc, 7, 0, 2 * Math.PI); g.fill();
    text(g, cv, t("source"), X(0), yc - (narrow ? 12 : 22), { align: "center", color: ink(), size: narrow ? 11 : 12 });
    lay.source = { x: X(0), y: yc };
    // particles in flight (computed emission times; straight paths at the speed v)
    const fl = blobs.flight || [];
    let nfl = 0;
    for (let q = 0; q < fl.length; q++) {
      const te = fl[q], tA = te + f.flight[0], tB = te + f.flight[1];
      if (te > tw) continue;
      const r = v * (tw - te);
      nfl++;
      g.strokeStyle = "rgba(240,140,0,0.18)"; g.lineWidth = 1;
      const xa = tw < tA ? -r : null, xb = tw < tB ? r : null;
      g.beginPath(); g.moveTo(X(xa ?? -LA), yc); g.lineTo(X(xb ?? LB), yc); g.stroke();
      for (const xx of [xa, xb]) if (xx !== null) { g.fillStyle = COL_SRC; g.beginPath(); g.arc(X(xx), yc, 4, 0, 2 * Math.PI); g.fill(); }
    }
    // the stations, their analysers and detectors with the latest clicks
    const sp = ctx.speed ? ctx.speed() : null;
    const flash = sp ? 0.3 * sp : 0.6 * Math.max(f.flight[0], f.flight[1]);
    for (const side of ["A", "B"]) {
      const x0 = side === "A" ? X(-LA) : X(LB), dir = side === "A" ? -1 : 1;
      const angs = side === "A" ? [S.a, S.a2] : [S.b, S.b2];
      const act = activeSetting(f, side);
      drawStation(g, cv, x0, yc, side, angs, act, narrow);
      // two detectors behind the analyser: "+" (transmitted / up) and "−"
      const c = clk[side];
      for (let d = 0; d < 2; d++) {
        const dx = x0 + dir * (narrow ? 34 : 46), dy = yc + (d ? 14 : -14);
        let age = Infinity;
        for (let i = c.t.length - 1; i >= 0; i--) if (c.d[i] === d && c.t[i] <= tw) { age = tw - c.t[i]; break; }
        const a = age < flash ? 1 - age / flash : 0;
        g.fillStyle = a > 0 ? (d ? COL_MINUS : COL_PLUS) : css("--panel"); g.globalAlpha = a > 0 ? 0.35 + 0.65 * a : 1;
        g.strokeStyle = d ? COL_MINUS : COL_PLUS; g.lineWidth = 1.5;
        g.beginPath(); g.rect(dx - 9, dy - 7, 18, 14); g.fill(); g.stroke(); g.globalAlpha = 1;
        text(g, cv, d ? "−" : "+", dx, dy + 4, { align: "center", color: a > 0.5 ? "#fff" : (d ? COL_MINUS : COL_PLUS), size: 12, bold: true });
      }
      lay[side] = { x: x0, y: yc };
      if (on.slots) drawStrip(g, cv, side, x0, yc + (narrow ? 42 : 54), f, tw, blobs, narrow);
    }
    // the note: what this picture shows now
    const fl0 = f.flight;
    const note = slotsMode()
      ? (narrow ? t("{k} slots; {n:d} of them shown in time", { k: fmt(f.meas.trials ?? 0, ".3g"), n: shownCount(blobs) })
        : t("Counting by slots: {k} slots; the strips show {n:d} slots simulated in time.", { k: fmt(f.meas.trials ?? 0, ".3g"), n: shownCount(blobs) }))
      : narrow ? t("Flight L/v = {tf}; pairs in flight: {k:d}", { tf: time(Math.max(fl0[0], fl0[1]), 4), k: nfl })
        : t("Flight L/v = {tf}. Pairs in flight: {k:d}. A click: + or −; a coincidence: a click at each station within the window.",
          { tf: time(Math.max(fl0[0], fl0[1]), 4), k: nfl });
    text(g, cv, note, 8, Hh - 8, { color: muted(), size: narrow ? 10 : 11, maxW: W - 16, part: "note", bottom: true });
  }
  function shownCount(blobs) { const s = blobs.slots || []; return Math.floor(s.length / 4); }

  function drawStation(g, cv, x0, y0, side, angles, act, narrow) {
    const R = narrow ? 17 : 22;
    g.strokeStyle = ink(); g.lineWidth = 1.5; g.fillStyle = css("--panel");
    g.beginPath(); g.arc(x0, y0, R, 0, 2 * Math.PI); g.fill(); g.stroke();
    for (let s = 0; s < 2; s++) {
      const al = angles[s] * Math.PI / 180, cur = act.s === s;
      const dx = Math.sin(isPhoton() ? al : al), dy = -Math.cos(al);
      g.strokeStyle = COL_SET[s]; g.globalAlpha = cur ? 1 : 0.35; g.lineWidth = cur ? 3.5 : 1.5;
      g.setLineDash(cur ? [] : [3, 3]);
      g.beginPath();
      if (isPhoton()) { g.moveTo(x0 - dx * R, y0 - dy * R); g.lineTo(x0 + dx * R, y0 + dy * R); }
      else {
        g.moveTo(x0 - dx * R * 0.6, y0 - dy * R * 0.6); g.lineTo(x0 + dx * R, y0 + dy * R);
        g.stroke(); g.beginPath();
        const hx = x0 + dx * R, hy = y0 + dy * R, px = -dy, py = dx;
        g.moveTo(hx, hy); g.lineTo(hx - dx * 8 + px * 4, hy - dy * 8 + py * 4); g.moveTo(hx, hy); g.lineTo(hx - dx * 8 - px * 4, hy - dy * 8 - py * 4);
      }
      g.stroke(); g.setLineDash([]); g.globalAlpha = 1;
    }
    const name = side === "A" ? t("Alice") : t("Bob");
    text(g, cv, `${name} (${side})`, x0, y0 - R - 6, { align: "center", color: ink(), size: narrow ? 11 : 12 });
    if (!narrow) {
      const l0 = setLabel(side, 0), l1 = setLabel(side, 1);
      const xt = side === "A" ? x0 - R - 6 : x0 + R + 6, al = side === "A" ? "right" : "left";
      text(g, cv, `${l0} = ${num(angles[0], 4)}°`, xt, y0 - 4, { align: al, color: COL_SET[0], size: 11 });
      text(g, cv, `${l1} = ${num(angles[1], 4)}°`, xt, y0 + 10, { align: al, color: COL_SET[1], size: 11 });
    }
  }

  // a station's latest slots: one box per slot, its colour the setting, its glyph the outcome
  function drawStrip(g, cv, side, x0, y, f, tw, blobs, narrow) {
    const sl = blobs.slots || [];
    const n = Math.floor(sl.length / 4);
    const W = cv.clientWidth;
    const room = side === "A" ? x0 - 6 + (W / 2 - x0) * 0.9 : (W - x0 - 6) + (x0 - W / 2) * 0.9;
    const bw = narrow ? 9 : 12, gap = 2;
    const kmax = Math.max(1, Math.min(n, Math.floor(Math.max(room, 60) / (bw + gap)), 24));
    const xs = side === "A" ? Math.max(4, x0 - kmax * (bw + gap) / 2) : Math.min(W - 4 - kmax * (bw + gap), x0 - kmax * (bw + gap) / 2);
    for (let q = 0; q < kmax; q++) {
      const i = n - kmax + q;
      if (i < 0) continue;
      const s = sl[4 * i + (side === "A" ? 0 : 1)], o = sl[4 * i + (side === "A" ? 2 : 3)];
      const x = xs + q * (bw + gap);
      g.fillStyle = COL_SET[s | 0]; g.globalAlpha = 0.22; g.fillRect(x, y - 10, bw, 16); g.globalAlpha = 1;
      g.font = `${narrow ? 10 : 11}px system-ui`; g.fillStyle = OUT_COL[o | 0]; g.textAlign = "center";
      g.fillText(OUT_GLYPH[o | 0], x + bw / 2, y + 2); g.textAlign = "left";
    }
    cv.__layout.parts["strip" + side] = { x0: xs, x1: xs + kmax * (bw + gap), y0: y - 10, y1: y + 6 };
    if (!narrow) text(g, cv, t("slots of {side}: setting (colour) and outcome", { side }), side === "A" ? xs : xs + kmax * (bw + gap),
      y + 18, { align: side === "A" ? "left" : "right", color: muted(), size: 10, maxW: Math.max(80, kmax * (bw + gap)) });
  }

  // --- the spacetime of the last coincidence ---------------------------------------------------------------------
  function drawSpacetime(f, tw) {
    const cv = cvST, g = setup(cv), W = cv.clientWidth, Hh = cv.clientHeight;
    if (W < 10 || Hh < 10) return;
    const x0 = 40, x1 = W - 14, y0 = 40, y1 = Hh - 48;
    const narrow = W < 520;
    text(g, cv, t("Spacetime of the last coincidence (x to the right, t upwards)"), 8, 16, { color: ink(), size: 12, maxW: W - 16 });
    if (slotsMode()) { text(g, cv, t("the counting by slots follows no single pair in time"), 8, 34, { color: muted(), size: 11, maxW: W - 16 }); return; }
    const i = lastUpTo(tw);
    if (i < 0) { text(g, cv, t("no coincidence yet"), 8, 34, { color: muted(), size: 11 }); return; }
    const c = H.c, tdA = det.tA[i], tdB = det.tB[i], te = det.te[i], td = Math.max(tdA, tdB);
    const S = f.settings, LA = S.LA, LB = S.LB, Lr = Math.max(LA, LB);
    const Xd = (x) => (x0 + x1) / 2 + (x1 - x0) / 2 * 0.92 * x / Lr;
    const isTrue = (det.fl[i] & F_TRUE) && Number.isFinite(te);
    let tlo = Math.min(isTrue ? te : td, det.tcA[i], det.tcB[i]);
    const span0 = td - (isTrue ? te : td - 2 * Lr / c);
    const clipped = tlo < td - 4 * Math.max(span0, 2 * Lr / c);
    if (clipped) tlo = td - 1.15 * Math.max(span0, 2 * Lr / c);
    const span = Math.max(td - tlo, 1e-30);
    const Teq = (y1 - y0) / (x1 - x0) * (2 * Lr / 0.92) / c;
    let thi = td + 0.12 * span, tl = tlo - 0.08 * span;
    if (Teq >= 1.2 * span) { thi = td + 0.1 * Teq; tl = thi - Teq; }
    const Y = (tt) => y1 - (y1 - y0) * (tt - tl) / (thi - tl);
    g.strokeStyle = lineC(); g.lineWidth = 1;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x0, y1); g.lineTo(x1, y1); g.stroke();
    for (const [xx, lab] of [[-LA, "−L_A (A)"], [0, "0"], [LB, "+L_B (B)"]]) {
      g.fillStyle = muted(); g.fillRect(Xd(xx), y1, 1, 4);
      text(g, cv, lab, Xd(xx), y1 + 14, { align: "center", color: muted(), size: 11 });
    }
    text(g, cv, "t", x0 - 12, y0 + 4, { color: muted(), size: 11 });
    g.save(); g.beginPath(); g.rect(x0, y0 - 6, x1 - x0, y1 - y0 + 6); g.clip();
    const cone = (tc, xc, col) => {
      if (!on.cones || !(tc <= thi)) return;
      const tcd = Math.max(tc, tl), dxe = c * (thi - tc), dx0 = c * (tcd - tc);
      g.fillStyle = col; g.globalAlpha = 0.10;
      g.beginPath(); g.moveTo(Xd(xc - dx0), Y(tcd)); g.lineTo(Xd(xc - dxe), Y(thi)); g.lineTo(Xd(xc + dxe), Y(thi)); g.lineTo(Xd(xc + dx0), Y(tcd)); g.closePath(); g.fill();
      g.globalAlpha = 0.75; g.strokeStyle = col; g.lineWidth = 1; g.setLineDash([5, 3]);
      g.beginPath(); g.moveTo(Xd(xc - dx0), Y(tcd)); g.lineTo(Xd(xc - dxe), Y(thi)); g.moveTo(Xd(xc + dx0), Y(tcd)); g.lineTo(Xd(xc + dxe), Y(thi)); g.stroke();
      g.setLineDash([]); g.globalAlpha = 1;
    };
    cone(det.tcA[i], -LA, COL_SET[det.sA[i]]);
    cone(det.tcB[i], LB, COL_SET[det.sB[i]]);
    if (isTrue) {
      g.strokeStyle = COL_SRC; g.lineWidth = 2;
      g.beginPath(); g.moveTo(Xd(0), Y(te)); g.lineTo(Xd(-LA), Y(tdA)); g.moveTo(Xd(0), Y(te)); g.lineTo(Xd(LB), Y(tdB)); g.stroke();
    }
    g.restore();
    const dot = (x, y, col, r = 5) => { g.fillStyle = col; g.beginPath(); g.arc(x, y, r, 0, 2 * Math.PI); g.fill(); };
    const diamond = (x, y, col) => { g.fillStyle = col; g.beginPath(); g.moveTo(x, y - 7); g.lineTo(x + 7, y); g.lineTo(x, y + 7); g.lineTo(x - 7, y); g.closePath(); g.fill(); };
    if (isTrue && te >= tl) { dot(Xd(0), Y(te), COL_SRC); text(g, cv, t("emission"), Xd(0), Y(te) + 16, { align: "center", color: ink(), size: 11 }); }
    for (const [side, tc, xc, s] of [["A", det.tcA[i], -LA, det.sA[i]], ["B", det.tcB[i], LB, det.sB[i]]]) {
      const yy = tc >= tl ? Y(tc) : y1 - 4;
      diamond(Xd(xc), yy, COL_SET[s]);
      const lab = tc >= tl ? t("choice {s}", { s: setLabel(side, s) }) : t("choice {s}: {dt} before ↓", { s: setLabel(side, s), dt: time(td - tc, 3) });
      text(g, cv, lab, Xd(xc) + (side === "A" ? 10 : -10), Math.min(y1 - 4, Math.max(yy + 4, Y(td) + 22)), { align: side === "A" ? "left" : "right", color: COL_SET[s], size: 11 });
    }
    for (const [side, x, o, tdd] of [["A", -LA, det.oA[i], tdA], ["B", LB, det.oB[i], tdB]]) {
      dot(Xd(x), Y(tdd), oCol(o), 7);
      g.fillStyle = "#fff"; g.font = "bold 12px system-ui"; g.textAlign = "center"; g.fillText(sign(o), Xd(x), Y(tdd) + 4); g.textAlign = "left";
      text(g, cv, t("click {side}", { side }), Xd(x) + (side === "A" ? 10 : -10), Y(tdd) - 10, { align: side === "A" ? "left" : "right", color: ink(), size: 11 });
    }
    const fl = det.fl[i];
    const okA = fl & F_LOC_A, okB = fl & F_LOC_B;
    const txt = (ok, a, b) => ok ? t("the choice at {a} is outside the cone of the click at {b}: space-like", { a, b })
      : t("the choice at {a} is inside the cone of the click at {b}: the locality loophole", { a, b });
    text(g, cv, (okA ? "✓ " : "✗ ") + txt(okA, "A", "B"), 8, Hh - 20, { color: okA ? css("--ok") : css("--bad"), size: narrow ? 10 : 11, maxW: W - 16 });
    text(g, cv, (okB ? "✓ " : "✗ ") + txt(okB, "B", "A"), 8, Hh - 6, { color: okB ? css("--ok") : css("--bad"), size: narrow ? 10 : 11, maxW: W - 16 });
    const ratio = (c * (thi - tl)) / (2 * Lr / 0.92) * (x1 - x0) / (y1 - y0);
    let win = Math.abs(ratio - 1) > 0.05
      ? t("window in t: {dt}; the scales of x and ct differ: the world lines of light are not at 45°", { dt: time(thi - tl, 3) })
      : t("window in t: {dt}; the scales of x and ct are equal: the world lines of light are at 45°", { dt: time(thi - tl, 3) });
    if (clipped) win = t("{text}; the bottom of the window is cut", { text: win });
    if (!isTrue) win = t("an accidental coincidence: the clicks come from different pairs or a dark count (known only in a simulation)");
    text(g, cv, win, 8, 32, { color: muted(), size: 10.5, maxW: W - 16 });
  }

  // --- the statistics ------------------------------------------------------------------------------------------
  function drawStat(f) {
    const cv = cvStat, g = setup(cv), W = cv.clientWidth, Hh = cv.clientHeight;
    if (W < 10 || Hh < 10) return;
    const narrow = W < 520, fs = narrow ? 10 : 12;
    const ro = cv.closest(".dm-stage") ? cv.closest(".dm-stage").querySelector(":scope > .dm-readouts") : null;
    let top = 0;
    if (ro && getComputedStyle(ro).position === "absolute" && ro.offsetHeight) {
      const rb = ro.getBoundingClientRect(), cb = cv.getBoundingClientRect();
      if (rb.bottom > cb.top && rb.left < cb.right) top = Math.max(0, rb.bottom - cb.top + 4);
    }
    cv.__layout.parts.top = top;
    const cols = narrow ? [0, 0.12, 0.22, 0.32, 0.42, 0.53, 0.88, 1] : [0, 0.11, 0.27, 0.35, 0.43, 0.51, 0.59, 0.80, 0.90];
    const heads = narrow ? [t("pair"), "N++", "N+−", "N−+", "N−−", "E ± σ", "z"]
      : [t("pair"), "α_A, α_B", "N++", "N+−", "N−+", "N−−", "E ± σ", t("predicted"), "z"];
    const xc = (k) => 8 + (W - 16) * cols[k];
    let y = 16 + top;
    heads.forEach((h, k) => h && text(g, cv, h, xc(k), y, { color: muted(), size: fs }));
    g.strokeStyle = lineC(); g.beginPath(); g.moveTo(8, y + 5); g.lineTo(W - 8, y + 5); g.stroke();
    for (const c of f.cells) {
      y += fs + 6;
      const sA = c.x === "a" ? 0 : 1, sB = c.y === "b" ? 0 : 1;
      const b1 = text(g, cv, `(${c.x},`, xc(0), y, { color: COL_SET[sA], size: fs });
      text(g, cv, ` ${c.y})`, b1.x1, y, { color: COL_SET[sB], size: fs });
      let k = 1;
      if (!narrow) { text(g, cv, `${fmt(c.alA, ".4g")}°, ${fmt(c.alB, ".4g")}°`, xc(1), y, { color: ink(), size: fs }); k = 2; }
      c.n.forEach((q, j) => text(g, cv, fmt(q, "d"), xc(k + j), y, { color: ink(), size: fs, maxW: xc(k + j + 1) - xc(k + j) - 2 }));
      k += 4;
      text(g, cv, c.E === null ? "—" : `${fmt(c.E, ".3f")} ± ${fmt(c.se, ".3f")}`, xc(k), y, { color: c.N >= NMIN ? ink() : muted(), size: fs, maxW: xc(k + 1) - xc(k) - 2 });
      if (!narrow) { text(g, cv, fmt(c.Eexp, ".3f"), xc(k + 1), y, { color: muted(), size: fs }); k++; }
      const zw = W - 8 - xc(k + 1);
      if (c.z !== null && c.N >= NMIN) text(g, cv, fmt(c.z, "+.1f"), xc(k + 1), y, { color: Math.abs(c.z) < 5 ? css("--ok") : css("--bad"), size: fs, maxW: zw });
      else text(g, cv, "—", xc(k + 1), y, { color: muted(), size: fs });
    }
    y += 8;
    y = drawGauge(g, cv, f, y, W, fs, narrow);
    y = drawJ(g, cv, f, y, W, fs, narrow);
    const rest = Hh - y - 6;
    if (slotsMode()) { drawJeta(g, cv, f, 8, y, W - 8, Hh - 6, fs); return; }
    const wantE = on.e_delta, wantS = on.s_delta;
    if (!wantE && !wantS) return;
    if (wantE && wantS && W >= 560) {
      drawCurve(g, cv, f, 8, y, W / 2 - 4, Hh - 6, fs);
      drawSdelta(g, cv, f, W / 2 + 4, y, W - 8, Hh - 6, fs);
    } else if (wantE && wantS && narrow && rest < 300) {
      if (f.settings.switch === "fixed") drawCurve(g, cv, f, 8, y, W - 8, Hh - 6, fs);
      else drawSdelta(g, cv, f, 8, y, W - 8, Hh - 6, fs);
    } else if (wantE && wantS && rest > 300) {
      drawCurve(g, cv, f, 8, y, W - 8, y + rest / 2, fs);
      drawSdelta(g, cv, f, 8, y + rest / 2 + 4, W - 8, Hh - 6, fs);
    } else if (wantS) drawSdelta(g, cv, f, 8, y, W - 8, Hh - 6, fs);
    else drawCurve(g, cv, f, 8, y, W - 8, Hh - 6, fs);
  }

  // |S| on [0, 3] with the bounds 2 and 2√2: the law's, the measured raw S and S with the accidentals subtracted
  function drawGauge(g, cv, f, y, W, fs, narrow) {
    const S = f.S, gx0 = 24, gx1 = W - 20, gy = y + (narrow ? 30 : 36);
    const Xs = (s) => gx0 + (gx1 - gx0) * Math.min(3, Math.max(0, s)) / 3;
    const Tz = 2 * Math.SQRT2;
    text(g, cv, t("CHSH from the coincidences (fair sampling): |S| and the bounds"), 8, y + 10, { color: muted(), size: fs, maxW: W - 16 });
    const band = (s0, s1, col) => { g.fillStyle = col; g.globalAlpha = 0.16; g.fillRect(Xs(s0), gy - 9, Xs(s1) - Xs(s0), 18); g.globalAlpha = 1; };
    band(0, 2, "#868e96"); band(2, Tz, "#1c7ed6"); band(Tz, 3, "#e03131");
    g.strokeStyle = ink(); g.lineWidth = 1;
    for (const [s, lab] of [[0, "0"], [1, "1"], [2, "2"], [Tz, "2√2"], [3, "3"]]) {
      g.beginPath(); g.moveTo(Xs(s), gy - 11); g.lineTo(Xs(s), gy + 9); g.stroke();
      text(g, cv, lab, Xs(s), gy - 13, { align: "center", color: ink(), size: fs - 1 });
    }
    const Sl = Math.abs(f.S_law);
    g.fillStyle = muted(); g.beginPath(); g.moveTo(Xs(Sl), gy + 9); g.lineTo(Xs(Sl) - 6, gy + 17); g.lineTo(Xs(Sl) + 6, gy + 17); g.closePath(); g.fill();
    let stxt = t("S: accumulating; ≥ {nmin:d} coincidences are needed in each of the four cells (now the minimum is {k:d})", { nmin: NMIN, k: S.Nmin });
    if (S.S !== null && S.Nmin >= NMIN) {
      const a = Math.abs(S.S), e = S.se;
      g.strokeStyle = ink(); g.lineWidth = 2;
      g.beginPath(); g.moveTo(Xs(a - 2 * e), gy); g.lineTo(Xs(a + 2 * e), gy); g.stroke();
      g.fillStyle = a > 2 + 5 * e ? "#1c7ed6" : ink(); g.beginPath(); g.arc(Xs(a), gy, 5, 0, 2 * Math.PI); g.fill();
      const sub = f.S_sub && f.S_sub[0] !== null ? f.S_sub : null;
      if (sub) { g.strokeStyle = COL_BOTH; g.lineWidth = 2; g.beginPath(); g.arc(Xs(Math.abs(sub[0])), gy, 7, 0, 2 * Math.PI); g.stroke(); }
      stxt = t("S = {S:.4f} ± {se:.4f} (the law: {law:.4f}); (|S| − 2)/σ = {x:.1f}", { S: S.S, se: e, law: f.S_law, x: S.excess });
      cv.__layout.parts.S = { x: Xs(a), y: gy };
    }
    const b = text(g, cv, stxt, 8, gy + 30, { color: ink(), size: fs, maxW: W - 16, part: "S" });
    if (narrow) return b.y1 + 8;
    const b2 = text(g, cv, t("● measured (bar ± 2σ)  ○ accidentals subtracted  ▲ the world's law"), 8, b.y1 + fs + 2, { color: muted(), size: fs - 1, maxW: W - 16 });
    return b2.y1 + 8;
  }

  // CH and J of all the slots against 0 (no fair sampling)
  function drawJ(g, cv, f, y, W, fs, narrow) {
    const J = f.J || {};
    if (J.J === null || J.J === undefined) {
      const b = text(g, cv, t("J and CH of all the slots: accumulating"), 8, y + 4, { color: muted(), size: fs, maxW: W - 16 });
      return b.y1 + 8;
    }
    const z = J.se ? J.J / J.se : 0;
    const col = z > 5 ? "#1c7ed6" : ink();
    if (narrow) {
      const bn = text(g, cv, t("All the slots: J/σ = {z:+.1f}; J per pair {jp} (a local model: ≤ 0)", { z, jp: fmt(J.J / J.mu, ".3g") }),
        8, y + 4, { color: col, size: fs, maxW: W - 16, part: "J" });
      return bn.y1 + 8;
    }
    const b = text(g, cv, t("All the slots (no fair sampling): J = {J} ± {se} per slot, J/σ = {z:+.1f}; per pair {jp}; CH = {CH} ± {cse}",
      { J: fmt(J.J, ".3g"), se: fmt(J.se, ".2g"), z, jp: fmt(J.J / J.mu, ".3g"), CH: fmt(J.CH, ".3g"), cse: fmt(J.CHse, ".2g") }),
      8, y + 4, { color: col, size: fs, maxW: W - 16, part: "J" });
    const b2 = text(g, cv, t("predicted by the engine: J = {J} per slot ({k} slots); a local model: J ≤ 0",
      { J: fmt(J.Jexp, ".3g"), k: fmt(J.trials, ".3g") }), 8, b.y1 + fs + 2, { color: muted(), size: fs - 1, maxW: W - 16 });
    return b2.y1 + 8;
  }

  function plotFrame(g, cv, X0, Y0, X1, Y1, title, fs) {
    text(g, cv, title, X0, Y0 + 10, { color: ink(), size: fs, maxW: X1 - X0 });
    const px0 = X0 + 34, px1 = X1 - 6, py0 = Y0 + 20, py1 = Y1 - 18 - fs;
    g.strokeStyle = lineC(); g.lineWidth = 1; g.strokeRect(px0, py0, px1 - px0, py1 - py0);
    return { px0, px1, py0, py1 };
  }

  function drawCurve(g, cv, f, X0, Y0, X1, Y1, fs) {
    if (Y1 - Y0 < 90) return;
    const P = H.period;
    const { px0, px1, py0, py1 } = plotFrame(g, cv, X0, Y0, X1, Y1 - 2 * fs - 2, t("E(Δ), Δ = α_A − α_B (modulo {p}°)", { p: P }), fs);
    const Xd = (d) => px0 + (px1 - px0) * (d + P / 2) / P;
    const Ye = (e) => py0 + (py1 - py0) * (1 - e) / 2;
    for (const e of [-1, 0, 1]) { text(g, cv, fmt(e), px0 - 4, Ye(e) + 4, { align: "right", color: muted(), size: fs - 1 }); g.strokeStyle = lineC(); g.globalAlpha = e === 0 ? 0.9 : 0.35; g.beginPath(); g.moveTo(px0, Ye(e)); g.lineTo(px1, Ye(e)); g.stroke(); g.globalAlpha = 1; }
    const step = P === 180 ? 90 : 180;
    for (let d = -P / 2; d <= P / 2 + 1e-9; d += step) text(g, cv, `${fmt(d, "d")}°`, Xd(d), py1 + 13, { align: "center", color: muted(), size: fs - 1 });
    const quantumWorld = H.law === "quantum";
    const curve = (arr, col, dash, lw) => {
      g.strokeStyle = col; g.lineWidth = lw; g.setLineDash(dash);
      g.beginPath(); for (let k = 0; k < HB.cd.length; k++) { const X = Xd(HB.cd[k]), Yy = Ye(arr[k]); if (k) g.lineTo(X, Yy); else g.moveTo(X, Yy); }
      g.stroke(); g.setLineDash([]);
    };
    if (H.law !== "lhv" || on.other_law) curve(HB.cq, "#1c7ed6", H.law !== "lhv" ? [] : [6, 4], H.law !== "lhv" ? 2 : 1.2);
    if (H.law === "lhv" || on.other_law) curve(HB.ch, COL_LHV, H.law === "lhv" ? [] : [6, 4], H.law === "lhv" ? 2 : 1.2);
    const pts = lastBlobs.pts || [];
    for (let k = 0; k + 4 < pts.length; k += 5) {
      const d = pts[k], E = pts[k + 1], se = pts[k + 2], N = pts[k + 3];
      const X = Xd(d);
      g.globalAlpha = N >= NMIN ? 1 : 0.3; g.strokeStyle = ink(); g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(X, Ye(Math.min(1, E + se))); g.lineTo(X, Ye(Math.max(-1, E - se))); g.stroke();
      g.fillStyle = ink(); g.beginPath(); g.arc(X, Ye(E), 3, 0, 2 * Math.PI); g.fill(); g.globalAlpha = 1;
    }
    const lx = px0;
    const leg = (col, dash, s, yy) => { g.strokeStyle = col; g.lineWidth = 2; g.setLineDash(dash); g.beginPath(); g.moveTo(lx, yy - 4); g.lineTo(lx + 18, yy - 4); g.stroke(); g.setLineDash([]); text(g, cv, s, lx + 22, yy, { color: ink(), size: fs - 1, maxW: px1 - lx - 22 }); };
    leg("#1c7ed6", quantumWorld ? [] : [6, 4], quantumWorld ? t("quantum mechanics: the world's law") : t("quantum mechanics: for comparison"), Y1 - 14);
    if (on.other_law || H.law === "lhv") leg(COL_LHV, H.law === "lhv" ? [] : [6, 4], H.law === "lhv" ? t("the local model: the world's law") : t("a local model: for comparison"), Y1 - 2);
  }

  // S(Δ) in the CHSH geometry a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ: the laws' curves, this point's S and the traces' S
  function drawSdelta(g, cv, f, X0, Y0, X1, Y1, fs) {
    if (Y1 - Y0 < 90 || !HB.sd) return;
    const top = HB.sd[HB.sd.length - 1];
    const { px0, px1, py0, py1 } = plotFrame(g, cv, X0, Y0, X1, Y1, t("S(Δ): a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ"), fs);
    const Xd = (d) => px0 + (px1 - px0) * d / top;
    const Ys = (s) => py0 + (py1 - py0) * (3 - s) / 6;
    for (const s of [-2 * Math.SQRT2, -2, 0, 2, 2 * Math.SQRT2]) {
      g.strokeStyle = Math.abs(Math.abs(s) - 2) < 1e-9 ? "#868e96" : lineC(); g.setLineDash(Math.abs(s) > 2.1 ? [2, 3] : []);
      g.globalAlpha = s === 0 ? 0.9 : 0.6; g.beginPath(); g.moveTo(px0, Ys(s)); g.lineTo(px1, Ys(s)); g.stroke(); g.globalAlpha = 1; g.setLineDash([]);
    }
    for (const [s, lab] of [[2, "2"], [0, "0"], [-2, "−2"]]) text(g, cv, lab, px0 - 4, Ys(s) + 4, { align: "right", color: muted(), size: fs - 1 });
    for (const d of [0, top / 2, top]) text(g, cv, `${fmt(d, "d")}°`, Xd(d), py1 + 13, { align: "center", color: muted(), size: fs - 1 });
    const line = (arr, col, dash, lw) => {
      g.strokeStyle = col; g.lineWidth = lw; g.setLineDash(dash);
      g.beginPath(); for (let k = 0; k < HB.sd.length; k++) { const X = Xd(HB.sd[k]), Yy = Ys(arr[k]); if (k) g.lineTo(X, Yy); else g.moveTo(X, Yy); }
      g.stroke(); g.setLineDash([]);
    };
    if (H.law !== "lhv" || on.other_law) line(HB.sq, "#1c7ed6", H.law !== "lhv" ? [] : [6, 4], H.law !== "lhv" ? 2 : 1.2);
    if (H.law === "lhv" || on.other_law) line(HB.sh, COL_LHV, H.law === "lhv" ? [] : [6, 4], H.law === "lhv" ? 2 : 1.2);
    // the traces: earlier points' measured S at their Δ (faded), with their labels
    let ly = py0 + 12;
    for (const tr of traces) {
      const fr = frameOf(tr.W, tr.t);
      if (!fr || !fr.meta || !fr.meta.settings) continue;
      const d = fr.meta.settings.delta, Sx = fr.meta.S;
      if (d === null || d === undefined || !Sx || Sx.S === null) continue;
      g.globalAlpha = Math.max(0.3, tr.alpha ?? 0.4);
      g.strokeStyle = ink(); g.lineWidth = 1; g.beginPath(); g.moveTo(Xd(d), Ys(Sx.S + Sx.se)); g.lineTo(Xd(d), Ys(Sx.S - Sx.se)); g.stroke();
      g.fillStyle = muted(); g.beginPath(); g.arc(Xd(d), Ys(Sx.S), 3.5, 0, 2 * Math.PI); g.fill();
      if (tr.label) ly = traceLabel(g, cv, tr.label, px1 - 4, ly, fs, (px1 - px0) * 0.6, py1);
      g.globalAlpha = 1;
    }
    const d = f.settings.delta, S = f.S;
    if (d !== null && d !== undefined && S.S !== null) {
      g.strokeStyle = ink(); g.lineWidth = 1.5; g.beginPath(); g.moveTo(Xd(d), Ys(S.S + S.se)); g.lineTo(Xd(d), Ys(S.S - S.se)); g.stroke();
      g.fillStyle = ink(); g.beginPath(); g.arc(Xd(d), Ys(S.S), 4.5, 0, 2 * Math.PI); g.fill();
      cv.__layout.parts.Sdelta = { x: Xd(d), y: Ys(S.S) };
    }
    if (cv.clientWidth >= 520) text(g, cv, t("●: S of this point; grey: earlier points"), px0, Y1 - 2, { color: muted(), size: fs - 1, maxW: px1 - px0, bottom: true });
  }
  function frameOf(W, tt) {
    const F = W && W.frames;
    if (!F || !F.length) return null;
    let lo = 0, hi = F.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (F[m].t <= tt) lo = m + 1; else hi = m; }
    return F[Math.max(0, lo - 1)];
  }

  // the counting by slots: J per pair against the efficiency, the engine's curve for this source and background, this
  // point and the traces
  function drawJeta(g, cv, f, X0, Y0, X1, Y1, fs) {
    if (Y1 - Y0 < 90 || !HB.je) return;
    // (one line more under the axis: the footnote may take two lines)
    const { px0, px1, py0, py1 } = plotFrame(g, cv, X0, Y0, X1, Y1 - (cv.clientWidth >= 520 ? fs + 2 : 0), t("J per pair against the efficiency η (all the slots)"), fs);
    const e0 = 0.5, e1 = 1.0;
    let jmin = -0.15, jmax = 0.25;
    for (const j of HB.jq) { jmin = Math.min(jmin, j); jmax = Math.max(jmax, j); }
    for (const tr of traces) { const fr = frameOf(tr.W, tr.t), m = fr && fr.meta && fr.meta.meas; if (m && m.J_pair != null) { jmin = Math.min(jmin, m.J_pair); jmax = Math.max(jmax, m.J_pair); } }
    if (f.meas && f.meas.J_pair != null) { jmin = Math.min(jmin, f.meas.J_pair - 2 * (f.meas.J_pair_se || 0)); jmax = Math.max(jmax, f.meas.J_pair + 2 * (f.meas.J_pair_se || 0)); }
    const pad = 0.05 * (jmax - jmin); jmin -= pad; jmax += pad;
    const Xe = (e) => px0 + (px1 - px0) * (e - e0) / (e1 - e0);
    const Yj = (j) => py0 + (py1 - py0) * (jmax - Math.min(jmax, Math.max(jmin, j))) / (jmax - jmin);
    g.strokeStyle = "#868e96"; g.beginPath(); g.moveTo(px0, Yj(0)); g.lineTo(px1, Yj(0)); g.stroke();
    for (const [e, lab] of [[2 / 3, "2/3"], [2 / (1 + Math.SQRT2), "82.8 %"]]) {
      g.setLineDash([2, 3]); g.beginPath(); g.moveTo(Xe(e), py0); g.lineTo(Xe(e), py1); g.stroke(); g.setLineDash([]);
      text(g, cv, lab, Xe(e), py1 + 13, { align: "center", color: muted(), size: fs - 1 });
    }
    const jstep = jmax - jmin > 0.6 ? 0.2 : 0.1;
    for (let j = Math.ceil(jmin / jstep) * jstep; j <= jmax + 1e-9; j += jstep) text(g, cv, fmt(Math.round(j * 10) / 10), px0 - 4, Yj(j) + 4, { align: "right", color: muted(), size: fs - 1 });
    text(g, cv, "η = 1", Xe(1), py1 + 13, { align: "right", color: muted(), size: fs - 1 });
    g.strokeStyle = "#1c7ed6"; g.lineWidth = 2; g.beginPath();
    for (let k = 0; k < HB.je.length; k++) { const X = Xe(HB.je[k]), Yy = Yj(HB.jq[k]); if (k) g.lineTo(X, Yy); else g.moveTo(X, Yy); }
    g.stroke();
    let ly = py0 + 12;
    for (const tr of traces) {
      const fr = frameOf(tr.W, tr.t);
      const m = fr && fr.meta && fr.meta.meas;
      if (!m || m.J_pair === null || m.J_pair === undefined) continue;
      const e = fr.meta.settings.etaA;
      g.globalAlpha = Math.max(0.3, tr.alpha ?? 0.4); g.fillStyle = muted();
      g.beginPath(); g.arc(Xe(e), Yj(m.J_pair), 3.5, 0, 2 * Math.PI); g.fill();
      if (tr.label) ly = traceLabel(g, cv, tr.label, px1 - 4, ly, fs, (px1 - px0) * 0.6, py1);
      g.globalAlpha = 1;
    }
    const m = f.meas || {};
    if (m.J_pair !== null && m.J_pair !== undefined) {
      const e = f.settings.etaA, X = Xe(e);
      g.strokeStyle = ink(); g.lineWidth = 1.5; g.beginPath(); g.moveTo(X, Yj(m.J_pair + 2 * m.J_pair_se)); g.lineTo(X, Yj(m.J_pair - 2 * m.J_pair_se)); g.stroke();
      g.fillStyle = m.J_pair > 5 * m.J_pair_se ? "#1c7ed6" : ink(); g.beginPath(); g.arc(X, Yj(m.J_pair), 4.5, 0, 2 * Math.PI); g.fill();
      cv.__layout.parts.Jeta = { x: X, y: Yj(m.J_pair) };
    }
    if (cv.clientWidth >= 520) text(g, cv, t("line: the engine's J per pair for this source and background; ●: this point (± 2σ)"), px0, Y1 - 2, { color: muted(), size: fs - 1, maxW: px1 - px0, bottom: true });
  }

  // --- panels ---------------------------------------------------------------------------------------------
  function drawInfo(f) {
    const S = f.settings, c = H.c;
    const rows = [[t("Pairs"), t(H.pair_label)],
      [t("Law"), H.law === "quantum" ? t("quantum mechanics (the Born rule)") : t("{model}: a modification", { model: t(H.model_label) })],
      [t("Detectors"), t(H.device)],
      [t("Speed of the particles"), H.pair === "photon" ? "c" : `${fmt(H.v / c, ".4g")} c`],
      ["L_A, L_B", `${lenFmt(S.LA)}, ${lenFmt(S.LB)}`], [t("Light between the stations"), time((S.LA + S.LB) / c, 5)],
      [t("Slot T_s"), time(S.Ts, 4)], [t("Window w"), time(S.w, 4)], [t("Pairs per slot μ"), fmt(S.rate * S.Ts, ".3g")],
      [t("Choice of the settings"), S.switch === "random" ? t("random per slot, τ before it") : t("fixed (a, b)")]];
    if (S.switch === "random") {
      const ct = c * (S.tau + S.Ts);
      rows.push(["τ", time(S.tau, 4)], [t("c(τ + T_s) against L_A + L_B"), `${lenFmt(ct)} ${ct < S.LA + S.LB ? "<" : "≥"} ${lenFmt(S.LA + S.LB)}`]);
    }
    infoBox.replaceChildren(...rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]));
  }
  function drawCounts(f) {
    const c = f.counts, m = f.meas || {};
    const n = c.coinc || 0;
    const pct = (k) => (n ? t("{p:.4g} %", { p: 100 * k / n }) : "—");
    const rows = [[t("pairs emitted"), fmt(c.emitted || 0, "d")], [t("in flight"), fmt(c.in_flight || 0, "d")],
      [t("coincidences (after the reset)"), fmt(n, "d")], [t("of them true (known only in a simulation)"), fmt(c.true || 0, "d")],
      [t("singles A / B"), `${fmt(m.singles_A ?? 0, "d")} / ${fmt(m.singles_B ?? 0, "d")}`],
      [t("accidentals, estimate w·N_A·N_B/T"), m.acc_est === null || m.acc_est === undefined ? "—" : fmt(m.acc_est, ".4g")],
      [t("trials (slots)"), m.trials === null || m.trials === undefined ? "—" : fmt(m.trials, ".4g")],
      [t("choice outside the other side's cone"), pct(c.loc)]];
    countBox.replaceChildren(el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, String(v))])),
      el("div", { class: "help" }, t("The fractions come from the events of each coincidence: the choice of a setting, the emission, the clicks (the interval s² = c²Δt² − Δx²).")));
  }
  function drawLast(tw) {
    const i = lastUpTo(tw);
    const items = [];
    for (let k = i; k >= 0 && k > i - 10; k--) {
      const fl = det.fl[k];
      items.push(el("div", { class: "ev" }, el("b", {}, (fl & F_TRUE) ? `#${fmt(det.id[k], "d")}` : t("accidental")), ` ${time(Math.max(det.tA[k], det.tB[k]), 6)}: `,
        el("span", { style: { color: oCol(det.oA[k]) } }, `A ${sign(det.oA[k])}`), ` (${setLabel("A", det.sA[k])} = ${fmt(det.alA[k], ".4g")}°), `,
        el("span", { style: { color: oCol(det.oB[k]) } }, `B ${sign(det.oB[k])}`), ` (${setLabel("B", det.sB[k])} = ${fmt(det.alB[k], ".4g")}°)`,
        el("div", { class: "muted" }, (fl & (F_LOC_A | F_LOC_B)) === (F_LOC_A | F_LOC_B)
          ? t("both choices outside the other side's cone") : t("a choice inside the other side's cone"))));
    }
    lastBox.replaceChildren(...(items.length ? items : [el("div", { class: "muted" }, t("None yet"))]));
  }

  function layoutClass() {
    center.classList.toggle("u37-noST", !on.spacetime || slotsMode());
  }

  return {
    center, rightPanels,
    quantSafe: QUANT_SAFE,
    overlays: OVERLAYS.map((o) => ({ ...o, label: t(o.label) })),  // i18n-msgids: "spacetime of the last coincidence" "light cones" "slot strips" "E(Δ)" "S(Δ)" "the other law's curves"
    setOverlay(id, v) { if (id in on) { on[id] = !!v; layoutClass(); redraw(); } },
    setTraces(list) { traces = list || []; redraw(); },
    help: () => el("div", {},
      el("h4", {}, t("What is on the screen")),
      el("p", {}, t("The set-up line: the source in the middle, the stations of Alice (A) and Bob (B) at L_A and L_B. Each station has two settings of its analyser: for photons the transmission axis of the polariser (a line), for spin ½ the direction of the Stern–Gerlach magnet (an arrow); blue: a/b, violet: a′/b′, bold: the one chosen for the current time slot. Behind each analyser two detectors, + and −, flash when they click. Under each station the strip of its latest slots: the colour is the setting, the sign the outcome (+, −, 0 for no click, ± for both).")),
      el("p", {}, t("The spacetime of the last coincidence: the emission, the particles' world lines, the events of the setting choices (diamonds) with their future light cones, and the clicks. If the click on the other side lies outside the cone of a choice, no signal about the choice could have reached it.")),
      el("p", {}, t("The statistics: the coincidence counts of the four pairs of settings, E with its error and the engine's prediction for these detectors, S under fair sampling on a scale with the bounds 2 (any local model) and 2√2 (Tsirelson), CH and J of all the slots (no fair sampling: a local model keeps them ≤ 0), and the curves E(Δ) and S(Δ); in the counting by slots the curve J(η)."))),
    reset() { H = null; HB = null; det = newDet(); clk = newClk(); shownSlots = []; lastF = null; lastBlobs = {}; },
    snapshot() { return { n: det.n, off: det.off, cA: clk.A.t.length, cB: clk.B.t.length, coff: clk.off }; },
    restore(k) {
      if (det.off !== k.off || clk.off !== k.coff) throw new Error("the oldest coincidences were dropped since this key frame");
      for (const key of Object.keys(det)) if (Array.isArray(det[key])) det[key].length = k.n;
      det.n = k.n;
      for (const [s, n] of [["A", k.cA], ["B", k.cB]]) for (const key of ["t", "d", "s"]) clk[s][key].length = n;
      lastF = null;
    },
    onHeader(meta, blobs) {
      H = meta; HB = { cd: blobs.cd, cq: blobs.cq, ch: blobs.ch, sd: blobs.sd, sq: blobs.sq, sh: blobs.sh, sw: blobs.sw, je: blobs.je, jq: blobs.jq };
      layoutClass();
      ctx.setScene && ctx.setScene(t(meta.title));
    },
    onMessage(meta, blobs) {
      if (meta.type === "pairs") pushDet(blobs || {}, meta.t);
    },
    render(frame, tw, blobs) {
      if (!H || !frame || !frame.settings) return;
      lastF = frame; lastBlobs = blobs || {}; lastT = tw;
      drawSet(frame, tw, lastBlobs);
      const stShown = !SCR || window.innerWidth >= 1000 || stFold.classList.contains("open");
      if (on.spacetime && !slotsMode() && stShown) drawSpacetime(frame, tw);
      drawStat(frame);
      drawInfo(frame);
      drawCounts(frame);
      drawLast(tw);
    },
  };
}
