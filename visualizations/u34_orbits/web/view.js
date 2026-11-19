// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u34 view: the orbit plane (trail of the body, the other theory's ghost, apsides, the special radii of the
// Schwarzschild geometry, the central body) and the plots r(t) and 1 − dτ/dt; panels "Orbit" and "Clocks".
// Everything drawn is data of the run: trail samples and apsides are messages revealed when the world's time
// reached them, the current state comes with each frame, the special radii come from the engine (header).
// The view only draws, scales and formats; it computes no physics.
//
// The screens (EX2 design lfphys/sources/explore_EX2_2026-11-18_design.md §1.3, §2.5): with ctx.screen "watch",
// "explore" or "lab" the quick bar, the toolbar and the actions are left out (a screen's points cannot be changed from
// the view); what they toggled are overlays (OVERLAYS, setOverlay: Newton's orbit, the GR radii, the periapses, the
// plots, following the body) and «⌖ orbit» stays as a button. Each picture's note is a band above it, never over it.
// Watch keeps one scale for the whole story (setStory: the extent of every trail of the recording, Newton's included)
// and leaves a fixed band under the pictures for the caption, sized to the story's longest caption at the stage's width,
// so a caption never covers what it describes. Explore draws earlier points as faded traces (setTraces), each labelled
// with what differs; Lab work draws exactly what Explore draws (nothing hidden). Below 1000 px the orbit plane is the
// picture at the top and the plots with the notes fold under it («▸ Plots r(t) and 1 − dτ/dt, and what the lines are»;
// «⌖ orbit» is in the plane's note: no wheel to zoom on a touch screen); in Watch, which has no controls,
// they stay open. Each canvas exposes what it drew where (canvas.__layout: its labels' boxes, the body, the fitted
// extent) for the browser checks (tests/u34_screens.mjs). The live player (no ctx.screen) keeps its bars and notes.
import { Plane } from "/static/js/canvas.js";
import { t } from "/static/js/i18n.js";
import { css, el, fresh2d, length, num, panel, time } from "/static/js/ui.js";

const AU_M = 149597870700;

// what the view accepts quantised (registry.view_declarations reads this literal): the trails are drawn only (the
// apsides, the measurables and the checks stay float64); 16 bits over a message's span is far below a pixel
export const QUANT_SAFE = { "trail.t": "u16", "trail.x": "u16", "trail.y": "u16", "trail.r": "u16", "trail.lag": "u16",
  "gtrail.t": "u16", "gtrail.x": "u16", "gtrail.y": "u16", "gtrail.r": "u16" };
// the overlays it can toggle on the screens (registry.view_declarations reads the ids)
export const OVERLAYS = [
  { id: "newton", label: "Newton's orbit", default: true },
  { id: "radii", label: "GR radii", default: true },
  { id: "apsides", label: "periapses and their rays", default: true },
  { id: "plots", label: "plots r(t) and 1 − dτ/dt", default: true },
  { id: "follow", label: "follow the body", default: false },
];
// i18n-msgids: "Newton's orbit" "GR radii" "periapses and their rays" "plots r(t) and 1 − dτ/dt" "follow the body"

const SCREENS = new Set(["watch", "explore", "lab"]);
// the phone's heights (below 1000 px): the orbit plane, sticky in Explore and Lab work, short enough that a control and
// «Measure» fit between it and the time bar on a 390 × 844 screen (integrator D12); the plots under it
// (Explore's plane is taller: its readouts lie over the plane's top right corner on a phone, and the orbit is fitted
// under them; Lab work's readouts are in its card)
const ORB_PX = 300, ORB_PX_EXPLORE = 340, PLOT_PX = 220;
let STYLE = false;  // the screens' layout, added once per page
function addStyle() {
  if (STYLE) return;
  STYLE = true;
  document.head.append(el("style", {}, `
.u34-c { display: flex; flex-direction: column; flex: 1; min-height: 0; box-sizing: border-box; }
.u34-panes { display: grid; flex: 1; min-height: 0; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  grid-template-rows: auto minmax(0, 1fr); grid-template-areas: "no np" "co cp"; }
.u34-c.u34-noplots .u34-panes { grid-template-columns: minmax(0, 1fr); grid-template-areas: "no" "co"; }
.u34-c.u34-noplots .u34-note-plot, .u34-c.u34-noplots .u34-plot { display: none; }
.u34-orb, .u34-plot { display: flex; flex-direction: column; min-height: 0; min-width: 0; }
.u34-orb { grid-area: co; border-right: 1px solid var(--line); }
.u34-plot { grid-area: cp; }
.u34-note { font-size: 13px; line-height: 1.35; padding: 4px 10px; background: var(--panel); color: var(--muted);
  border-bottom: 1px solid var(--line); overflow-wrap: anywhere; min-width: 0; }
.u34-note-orb { grid-area: no; border-right: 1px solid var(--line); }
.u34-note-plot { grid-area: np; }
.u34-note-orb { display: flex; gap: 8px; align-items: flex-start; }
.u34-note-orb > .u34-note-text { flex: 1; min-width: 0; }
.u34-fit { flex: none; min-height: 28px; padding: 2px 8px; font-size: 13px; }
.u34-foldbtn { grid-area: fb; display: none; align-items: center; gap: 6px; min-height: 44px; padding: 4px 10px; border: 0;
  border-top: 1px solid var(--line); background: var(--panel); color: inherit; font: inherit; font-size: 14px; text-align: left; cursor: pointer; }
@media (max-width: 999px) {
  .dm-stage:has(> .u34-c.u34-on) { aspect-ratio: auto; max-height: none; }
  .dm-stage > div.u34-c.u34-on { aspect-ratio: auto; flex: none; min-height: 0; }
  /* (every row but the plane's is auto: a folded or switched-off part takes no height in the sticky stage) */
  .u34-c.u34-on .u34-panes { flex: none; grid-template-columns: minmax(0, 1fr);
    grid-template-rows: ${ORB_PX}px auto auto auto auto; grid-template-areas: "co" "fb" "no" "np" "cp"; }
  .u34-c.u34-on .u34-plot { height: ${PLOT_PX}px; }
  .u34-c.u34-on.u34-noplots .u34-panes { grid-template-rows: ${ORB_PX}px auto auto; grid-template-areas: "co" "fb" "no"; }
  .u34-c.u34-explore .u34-panes, .u34-c.u34-explore.u34-noplots .u34-panes { grid-template-rows: ${ORB_PX_EXPLORE}px auto auto auto auto; }
  .u34-c.u34-on .u34-orb { border-right: 0; }
  .u34-c.u34-on .u34-note-orb { border-right: 0; border-top: 1px solid var(--line); }
  .u34-c.u34-fold .u34-foldbtn { display: flex; }
  .u34-c.u34-fold:not(.u34-open) .u34-note, .u34-c.u34-fold:not(.u34-open) .u34-plot { display: none; }
  /* Watch on a phone: the caption (the stage's own, after the view) right under the orbit plane, the notes and the plots
     under it, so the plane and the caption about it are read together */
  .u34-c.u34-watch, .u34-c.u34-watch .u34-panes { display: contents; }
  .u34-c.u34-watch .u34-orb { order: 1; height: ${ORB_PX}px; flex: none; }
  .dm-stage:has(> .u34-c.u34-watch) > .dm-caption { order: 2; }
  .u34-c.u34-watch .u34-note, .u34-c.u34-watch .u34-plot { order: 3; }
  .u34-c.u34-watch .u34-plot { height: ${PLOT_PX}px; flex: none; }
}`));
}

export function createView(ctx) {
  const SCR = SCREENS.has(ctx.screen);
  const WATCH = ctx.screen === "watch", FOLD = ctx.screen === "explore" || ctx.screen === "lab";
  let H = null, units = null, liveVals = {};
  let segs = [];                 // segment messages, in time order
  let trails = new Map();        // seg -> columns {n, t, x, y, r, lag}
  let gtrails = new Map();       // seg -> columns {n, t, x, y, r}
  let apsides = new Map();       // seg -> [apsis]
  let gapsides = new Map();      // seg -> [ghost periapsis]
  let ghostInfo = new Map();     // seg -> ghost info (or null)
  // the plane is fitted to a new launch once, when it first appears; scrubbing back and forth, a rebuild or a key frame
  // keep the owner's pan and zoom (review UX-ui U1: a step back refitted the plane); a new world fits again
  let lastT = 0, fittedSeg = -1, fittedWorld = null;
  const opt = { allSegs: true, radii: true, apsides: true, follow: false, history: false, ghost: true, plots: true };
  let traces = [];               // Explore: earlier points [{W, t, label, alpha, live}] (setTraces)
  let story = null;              // Watch: {R, worlds} (setStory): one scale for the whole recording
  let fitKey = "", userMoved = false, capBand = 0, watchedReadouts = null;
  // a screen asks to render at every animation frame, while the point's frames change 8 times per played second: the
  // drawing is skipped when neither the frame shown nor anything the view holds has changed (under a loaded CPU the
  // redraws slowed the playback 3-fold); every change of what the view holds asks for a drawing (want)
  let changed = true, lastFrame = null;
  const want = () => { changed = true; ctx.requestRender(); };
  const traceCols = new WeakMap();  // a trace's world -> its trail columns (from its own messages)
  if (SCR) addStyle();

  // --- DOM -----------------------------------------------------------------------------------------------
  const live = (id, label) => (ctx.liveControl ? ctx.liveControl(id, { label }) : null);
  const cvOrb = el("canvas"), cvPlot = el("canvas");
  const ovOrb = el(SCR ? "span" : "div", { class: SCR ? "u34-note-text" : "overlay" });
  const ovPlot = el("div", { class: SCR ? "u34-note u34-note-plot" : "overlay" });
  const btnFit = el("button", { class: SCR ? "u34-fit" : "", title: t("Fit the orbit of the current segment") }, t("⌖ orbit"));
  let center, quick = null, toolbar = null, btnPlus = null, btnMinus = null, btnRelaunch = null, foldBtn = null;
  const cbs = {};
  if (!SCR) {
    btnPlus = el("button", { title: t("Push: +{p} % of the speed along the motion (at the current moment)", { p: 5 }) }, t("push +{p} %", { p: 5 }));
    btnMinus = el("button", { title: t("Brake: −{p} % of the speed along the motion", { p: 5 }) }, t("−{p} %", { p: 5 }));
    btnRelaunch = el("button", { title: t("Launch the body again from the initial data (r₀, speed, angle)") }, t("↻ launch"));
    quick = el("div", { class: "toolbar quick", title: t("Launch of the body: changes apply at once (the same as in the panel on the left)") },
      el("span", { class: "muted" }, t("Launch:")), live("r0", "r₀, M"), live("speed", t("speed, × circular")),
      live("angle", t("angle, °")), live("ghost", t("ghost")), btnPlus, btnMinus, btnRelaunch);
    for (const k of ["allSegs", "radii", "apsides", "follow", "history"]) cbs[k] = el("input", { type: "checkbox", checked: opt[k] });
    const btnCenter = el("button", { title: t("Fit the region near the centre (up to {r}M)", { r: 12 }) }, t("⌖ centre"));
    btnCenter.onclick = () => { const R = Math.max(12, (H && H.body.R) ? 1.5 * H.body.R : 0); plane.fit(-R, R, -R, R); };
    toolbar = el("div", { class: "toolbar" },
      el("label", { title: t("Show the traces of earlier segments (faded)") }, cbs.allSegs, " ", t("earlier segments")),
      el("label", { title: t("Horizon 2M, photon sphere 3M, marginally bound orbit 4M, ISCO 6M") }, cbs.radii, " ", t("GR radii")),
      el("label", {}, cbs.apsides, " ", t("periapses")),
      el("label", { title: t("Keep the body in the centre of the view") }, cbs.follow, " ", t("follow the body")),
      el("label", { title: t("Plots: the whole history of the segment instead of the last orbits") }, cbs.history, " ", t("plots: whole segment")),
      btnFit, btnCenter);
    center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick, toolbar,
      el("div", { class: "split", style: { gridTemplateColumns: "1.5fr 1fr" } },
        el("div", {}, el("div", { class: "canvas-wrap" }, cvOrb, ovOrb)),
        el("div", {}, el("div", { class: "canvas-wrap" }, cvPlot, ovPlot))));
  } else {
    const foldText = () => `${center && center.classList.contains("u34-open") ? "▾" : "▸"} ${t("Plots r(t) and 1 − dτ/dt, and what the lines are")}`;
    foldBtn = FOLD ? el("button", { class: "u34-foldbtn", "aria-expanded": "false", onclick: () => {
      const open = !center.classList.contains("u34-open");
      center.classList.toggle("u34-open", open); foldBtn.setAttribute("aria-expanded", String(open)); foldBtn.textContent = foldText();
      want();
    } }) : null;
    center = el("div", { class: `u34-c u34-on u34-${ctx.screen}${FOLD ? " u34-fold" : ""}` },
      el("div", { class: "u34-panes" }, el("div", { class: "u34-note u34-note-orb" }, ovOrb, btnFit), ovPlot,
        el("div", { class: "u34-orb" }, el("div", { class: "canvas-wrap" }, cvOrb)), foldBtn,
        el("div", { class: "u34-plot" }, el("div", { class: "canvas-wrap" }, cvPlot))));
    if (foldBtn) foldBtn.textContent = foldText();
  }
  const orbBox = el("div", {});
  const clockBox = el("div", {});
  // the panels fold into the drawer on the screens: built only while they are shown, and again when they are opened
  const shownBox = (b) => !SCR || b.offsetParent !== null;
  for (const b of [orbBox, clockBox]) new ResizeObserver(() => want()).observe(b);
  if (SCR && typeof MutationObserver !== "undefined")  // the theme's colours (data-theme on the page)
    new MutationObserver(() => want()).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] });
  const rightPanels = [panel(t("Orbit"), orbBox), panel(t("Clocks"), clockBox)];

  const plane = new Plane(cvOrb, { onChange: () => want() });
  new ResizeObserver(() => want()).observe(cvPlot);
  // the experimenter's pan and zoom are kept until the set-up changes (the screens refit only a new point)
  cvOrb.addEventListener("wheel", () => { userMoved = true; }, { passive: true });
  cvOrb.addEventListener("mousedown", () => { userMoved = true; });
  if (!SCR) {
    for (const k of Object.keys(cbs)) cbs[k].onchange = () => { opt[k] = cbs[k].checked; want(); };
    btnPlus.onclick = () => ctx.action("boost", { dv: 0.05 });
    btnMinus.onclick = () => ctx.action("boost", { dv: -0.05 });
    btnRelaunch.onclick = () => ctx.action("relaunch", {});
    // the actions act at the end of a live run's record: on a recording, in the past or on an earlier world they are
    // off, with the reason as their tooltip (start-page review F2, STATUS V51 (f); as the slice planes, ctx.readOnly())
    const actBtns = [btnPlus, btnMinus, btnRelaunch].map((b) => [b, b.title]);
    const syncActions = () => {
      const why = ctx.readOnly ? ctx.readOnly() : "";
      for (const [b, title] of actBtns) { b.disabled = !!why; b.title = why || title; }
    };
    window.addEventListener("editablechange", syncActions);
    syncActions();
  }
  btnFit.onclick = () => { userMoved = false; fitKey = ""; const s = segAt(lastT); if (s) { if (SCR) fitScreen(s, true); else fitSeg(s); } };

  // --- data helpers -----------------------------------------------------------------------------------------
  function cols(withLag) { return { n: 0, cap: 0, t: null, x: null, y: null, r: null, lag: withLag ? null : undefined }; }
  function push(map, seg, b, withLag) {
    let c = map.get(seg);
    if (!c) { c = cols(withLag); map.set(seg, c); }
    const m = b.t.length;
    if (c.n + m > c.cap) {
      const cap = Math.max(1024, 2 * (c.n + m));
      const grow = (old, T) => { const a = new T(cap); if (old) a.set(old.subarray(0, c.n)); return a; };
      c.t = grow(c.t, Float64Array); c.x = grow(c.x, Float64Array); c.y = grow(c.y, Float64Array); c.r = grow(c.r, Float64Array);
      if (withLag) c.lag = grow(c.lag, Float64Array);
      c.cap = cap;
    }
    c.t.set(b.t, c.n); c.x.set(b.x, c.n); c.y.set(b.y, c.n); c.r.set(b.r, c.n);
    if (withLag) c.lag.set(b.lag, c.n);
    c.n += m;
  }
  function upTo(c, tw) {  // number of samples with time <= t (samples are in time order)
    if (!c) return 0;
    let lo = 0, hi = c.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (c.t[m] <= tw) lo = m + 1; else hi = m; }
    return lo;
  }
  function segAt(tw) { let s = null; for (const g of segs) if (g.t <= tw) s = g; return s || segs[0] || null; }
  const M = () => (units ? units.M_m : 1);
  function lenM(rM) { return `${num(rM, 7)} M (${length(rM * M(), { au: AU_M }, 6)})`; }
  function tfmt(s, d = 7) {
    if (s === null || s === undefined) return "—";
    return liveVals.time_units === "geo" && units ? `${num(s / units.T_s, d)} GM/c³` : time(s, d);
  }
  const geo = (x, d = 7) => (x === null || x === undefined ? "—" : tfmt(x * (units ? units.T_s : 1), d));  // a time in GM/c³ (the measurables')
  function angFmt(rad) {
    if (rad === null || rad === undefined) return "—";
    const a = Math.abs(rad);
    if (a < Math.PI / 180) return num(rad * 180 / Math.PI * 3600, 7) + "″";
    return num(rad * 180 / Math.PI, 7) + "°";
  }
  // the radius a segment's orbit reaches (its apoapsis, its start, the ghost's apoapsis within 20 r₀): the box to fit
  function extentOf(s, gi) {
    const i = s.init || {}, r0 = i.r0 || 10;
    let R = r0;
    if (s.kind === "bound" && s.r_apo) R = s.r_apo;
    else if (s.kind === "escape" || s.kind === "radial_escape") R = 4 * r0;
    else if (s.r_apo && Number.isFinite(s.r_apo)) R = Math.max(r0, s.r_apo);
    if (opt.ghost && gi && gi.r_apo && Number.isFinite(gi.r_apo)) R = Math.max(R, Math.min(gi.r_apo, 20 * r0));
    return R;
  }
  const extent = (s) => 1.12 * extentOf(s, ghostInfo.get(s.seg));
  function fitSeg(s) { const R = extent(s); plane.fit(-R, R, -R, R); }

  // --- the screens' fit: one box, kept clear of what the screen lays over the picture -------------------------------
  // On a phone Explore lays its readouts over the stage's top right corner: the box is fitted into the part of the plane
  // under them (and under «⌖ orbit»), so the readouts never cover the orbit they describe.
  function topReserve() {
    if (!SCR) return 0;
    const stage = cvOrb.closest(".dm-stage");
    const rd = stage && stage.querySelector(":scope > .dm-readouts");
    const cr = cvOrb.getBoundingClientRect();
    // the readouts are filled after the view draws (and grow when their values come): their size change draws again
    if (rd && rd !== watchedReadouts) { watchedReadouts = rd; new ResizeObserver(() => want()).observe(rd); }
    let top = 0;
    if (rd && getComputedStyle(rd).position === "absolute" && rd.offsetParent) {
      const b = rd.getBoundingClientRect();
      if (b.bottom > cr.top && b.top < cr.bottom && b.left < cr.right && b.right > cr.left) top = Math.max(top, b.bottom - cr.top + 4);
    }
    return Math.min(top, 0.5 * cr.height);
  }
  function fitInto(R, top) {
    const w = plane.w, h = plane.h, m = 0.04;
    const s = Math.min(w * (1 - 2 * m), (h - top) * (1 - 2 * m) - 22) / (2 * R);  // (22 px: the scale bar's row)
    if (!(s > 0) || !(w > 1) || !(h > 1)) { plane.fit(-R, R, -R, R); return; }
    plane.sx = plane.sy = s; plane.cx = 0; plane.cy = (top - 22) / (2 * s);
  }
  function screenR(s) {
    if (WATCH && story) return 1.06 * story.R;
    let R = extentOf(s, ghostInfo.get(s.seg));
    for (const tr of traces) { const g = traceSeg(tr.W); if (g) R = Math.max(R, extentOf(g, opt.ghost ? g.ghost : null)); }
    return 1.08 * R;
  }
  function fitScreen(s, force = false) {
    const R = screenR(s), top = topReserve();
    const key = JSON.stringify([H && H.params, R, Math.round(plane.w), Math.round(plane.h), Math.round(top)]);
    const pkey = JSON.stringify([H && H.params, R]);
    if (pkey !== (fitScreen.pkey || "")) { userMoved = false; fitScreen.pkey = pkey; }  // a new set-up is shown whole
    if (!force && (key === fitKey || userMoved)) return;
    fitKey = key;
    fitInto(R, top);
  }

  // --- labels: inside the canvas, clear of each other; their boxes kept for the browser checks ------------------------
  let placed = [];
  function label(g, text, x, y, { color = null, align = "left", font = "11px system-ui", kind = "", bg = false, dir = -1 } = {}) {
    const W = g.canvas.clientWidth || plane.w, Hh = g.canvas.clientHeight || plane.h;
    g.save(); g.font = font;
    const w = g.measureText(text).width, hgt = parseFloat(font) || 11;
    let x0 = align === "right" ? x - w : align === "center" ? x - w / 2 : x;
    x0 = Math.max(3, Math.min(x0, W - 3 - w));
    let yb = Math.max(hgt + 2, Math.min(y, Hh - 3));
    const list = placed.filter((q) => q.cv === g.canvas);
    for (let k = 0; k < 10; k++) {
      const r = { x0, x1: x0 + w, y0: yb - hgt, y1: yb + 3 };
      if (!list.some((q) => r.x0 < q.x1 && q.x0 < r.x1 && r.y0 < q.y1 && q.y0 < r.y1)) break;
      const ny = yb + dir * (hgt + 3);
      if (ny < hgt + 2 || ny > Hh - 3) { dir = -dir; yb = Math.max(hgt + 2, Math.min(yb + dir * (hgt + 3), Hh - 3)); } else yb = ny;
    }
    if (bg) { g.fillStyle = css("--canvas"); g.globalAlpha = 0.85; g.fillRect(x0 - 2, yb - hgt, w + 4, hgt + 4); g.globalAlpha = 1; }
    g.fillStyle = color || css("--muted"); g.textBaseline = "alphabetic"; g.fillText(text, x0, yb);
    g.restore();
    const box = { cv: g.canvas, text, kind, x0, x1: x0 + w, y0: yb - hgt, y1: yb + 3 };
    placed.push(box);
    return box;
  }
  const layOf = (cv) => placed.filter((q) => q.cv === cv).map(({ cv: _c, ...b }) => b);

  // --- orbit plane -------------------------------------------------------------------------------------------
  function polyline(g, c, n, color, width, dash, alpha) {
    if (!c || n < 2) return;
    g.save(); g.strokeStyle = color; g.lineWidth = width; g.globalAlpha = alpha; g.setLineDash(dash || []);
    g.beginPath();
    let px = plane.X(c.x[0]), py = plane.Y(c.y[0]);
    g.moveTo(px, py);
    for (let i = 1; i < n; i++) {
      const X = plane.X(c.x[i]), Y = plane.Y(c.y[i]);
      if (Math.abs(X - px) + Math.abs(Y - py) < 0.7 && i < n - 1) continue;  // sub-pixel: skip (drawing only)
      g.lineTo(X, Y); px = X; py = Y;
    }
    g.stroke(); g.restore();
  }
  // Newton's dashed orbit, one piece per orbit from each of its periapses: the dash pattern starts again at each, so a
  // closed ellipse traced three times keeps its dashes (one continuous pattern would fill the gaps on the second turn)
  function ghostLine(g, c, n, gper) {
    const cuts = [0];
    for (const a of gper) { const k = upTo(c, a.t); if (k > cuts[cuts.length - 1] + 1 && k < n) cuts.push(k); }
    cuts.push(n);
    for (let j = 0; j + 1 < cuts.length; j++) {
      const a = Math.max(0, cuts[j] - (j ? 1 : 0)), b = cuts[j + 1];
      polyline(g, { x: c.x.subarray(a, b), y: c.y.subarray(a, b) }, b - a, "#f08c00", 1.3, [6, 5], 0.95);
    }
  }
  function circle(g, r, stroke, dash, text, fill, angDeg = -45) {
    const R = r * plane.sx;
    if (R < 2) return;
    g.save(); g.beginPath(); g.arc(plane.X(0), plane.Y(0), R, 0, 2 * Math.PI);
    if (fill) { g.fillStyle = fill; g.fill(); }
    if (stroke) { g.strokeStyle = stroke; g.lineWidth = 1; g.setLineDash(dash || []); g.stroke(); }
    g.restore();
    if (text && R > 22) {
      const a = angDeg * Math.PI / 180;
      label(g, text, plane.X(r * Math.cos(a)) + 3, plane.Y(r * Math.sin(a)) + 4, { color: stroke || css("--muted"), kind: "radius" });
    }
  }
  // an earlier point (Explore): its own segment and trail, from the trace's decoded world
  function traceSeg(W) {
    const m = W && W.viewMsgs ? W.viewMsgs.find((x) => x.meta.type === "segment") : null;
    return m ? m.meta : null;
  }
  function traceTrail(W) {
    let c = traceCols.get(W);
    if (!c) {
      c = cols(false);
      for (const m of W.viewMsgs || []) if (m.meta.type === "trail" && m.meta.seg === 0 && m.blobs) push(new Map([[0, c]]), 0, m.blobs, false);
      traceCols.set(W, c);
    }
    return c;
  }
  function drawTraces(g) {
    for (const tr of traces) {
      const c = traceTrail(tr.W), n = upTo(c, tr.t);
      polyline(g, c, n, css("--muted"), 1.4, null, Math.max(0.25, tr.alpha || 0.4));
      const s = traceSeg(tr.W);
      if (s && s.init && tr.label) {
        const x0 = s.init.r0 * Math.cos(s.init.phi0), y0 = s.init.r0 * Math.sin(s.init.phi0);
        label(g, tr.label, plane.X(x0) + 8, plane.Y(y0) + 16, { color: css("--muted"), kind: "trace", bg: true, dir: 1 });
      }
    }
  }
  function drawOrbit(frame, tw) {
    const g = plane.ctx;
    plane.clear();
    placed = placed.filter((q) => q.cv !== cvOrb);
    if (!H) return;
    const s = segAt(tw);
    if (SCR && s) fitScreen(s);
    else if (s && s.seg > fittedSeg && s.launch !== false) { fittedSeg = s.seg; fitSeg(s); }
    if (opt.follow && frame) { plane.cx = frame.x; plane.cy = frame.y; }
    plane.grid({ labelX: (v) => num(v, 4) + " M", labelY: (v) => num(v, 4) + " M" });
    const gi0 = s ? ghostInfo.get(s.seg) : null;
    const gr = H.law === "GR" || (gi0 && gi0.law === "GR" && opt.ghost);
    const body = H.body;
    // central body
    if (body.R > 0) circle(g, body.R, css("--warn"), null, null, "rgba(240,140,0,0.35)");
    if (H.law === "GR" && !(body.R > 0)) circle(g, H.special.horizon, "#000", null, null, "#000");
    if (!(body.R > 0)) {  // a point mass / a black hole too small to see: a marker of fixed size
      g.save(); g.fillStyle = H.law === "GR" ? "#000" : css("--warn"); g.strokeStyle = css("--muted");
      g.beginPath(); g.arc(plane.X(0), plane.Y(0), 3, 0, 2 * Math.PI); g.fill(); g.stroke(); g.restore();
    }
    // special radii (from the engine: lfphys.core.gravity.kerr at zero spin)
    if (opt.radii && gr) {  // only outside the body: inside it the exterior (Schwarzschild) metric does not apply
      const sp = H.special, out = (r) => !(body.R > 0) || r > body.R;
      if (out(sp.horizon)) circle(g, sp.horizon, "#868e96", null, t("{r:.3g}M horizon", { r: sp.horizon }), null, -100);
      if (out(sp.photon)) circle(g, sp.photon, "#ae3ec9", [4, 3], t("{r:.3g}M photon sphere", { r: sp.photon }), null, -75);
      if (out(sp.mb)) circle(g, sp.mb, "#1c7ed6", [1, 3], `${num(sp.mb, 3)}M`, null, -45);
      if (out(sp.isco)) circle(g, sp.isco, "#e8590c", [6, 4], `${num(sp.isco, 3)}M ISCO`, null, -20);
    }
    if (SCR && !WATCH) drawTraces(g);
    // trails: earlier segments faded
    const accent = css("--accent");
    if (opt.allSegs) for (const [sg, c] of trails) if (!s || sg !== s.seg) polyline(g, c, upTo(c, tw), css("--muted"), 1, null, 0.45);
    let bodyAt = null;
    if (s) {
      const gc = gtrails.get(s.seg);
      if (gc && opt.ghost) ghostLine(g, gc, upTo(gc, tw), (gapsides.get(s.seg) || []).filter((a) => a.t <= tw));
      const c = trails.get(s.seg);
      const n = upTo(c, tw);
      polyline(g, c, n, accent, 1.6, null, 1);
      // from the last revealed sample to the body's current position
      if (c && n && frame && frame.seg === s.seg) {
        g.save(); g.strokeStyle = accent; g.lineWidth = 1.6; g.beginPath();
        g.moveTo(plane.X(c.x[n - 1]), plane.Y(c.y[n - 1])); g.lineTo(plane.X(frame.x), plane.Y(frame.y)); g.stroke(); g.restore();
      }
      // launch point and the direction of the initial velocity
      const i = s.init;
      if (i) {
        const x0 = i.r0 * Math.cos(i.phi0), y0 = i.r0 * Math.sin(i.phi0);
        const vx = i.v_r * Math.cos(i.phi0) - i.v_phi * Math.sin(i.phi0), vy = i.v_r * Math.sin(i.phi0) + i.v_phi * Math.cos(i.phi0);
        const vn = Math.hypot(vx, vy);
        g.save(); g.strokeStyle = css("--ok"); g.fillStyle = css("--ok"); g.lineWidth = 1.5;
        const X0 = plane.X(x0), Y0 = plane.Y(y0);
        g.beginPath(); g.arc(X0, Y0, 3.5, 0, 2 * Math.PI); g.stroke();
        if (vn > 0) {
          const L = 34, ux = vx / vn, uy = -vy / vn;
          g.beginPath(); g.moveTo(X0, Y0); g.lineTo(X0 + L * ux, Y0 + L * uy); g.stroke();
          g.beginPath(); g.moveTo(X0 + L * ux, Y0 + L * uy);
          g.lineTo(X0 + (L - 7) * ux - 4 * uy, Y0 + (L - 7) * uy + 4 * ux); g.lineTo(X0 + (L - 7) * ux + 4 * uy, Y0 + (L - 7) * uy - 4 * ux); g.fill();
        }
        g.restore();
      }
      if (opt.apsides) drawApsides(g, s, tw);
    }
    // the body and the ghost
    if (frame && s && frame.seg === s.seg) {
      if (frame.ghost && opt.ghost) {
        g.save(); g.strokeStyle = "#f08c00"; g.lineWidth = 2; g.beginPath();
        g.arc(plane.X(frame.ghost.x), plane.Y(frame.ghost.y), 6, 0, 2 * Math.PI); g.stroke(); g.restore();
      }
      g.save();
      const X = plane.X(frame.x), Y = plane.Y(frame.y);
      bodyAt = { x: X, y: Y };
      if (frame.alive) {
        g.fillStyle = accent; g.strokeStyle = css("--canvas"); g.lineWidth = 1.5;
        g.beginPath(); g.arc(X, Y, 6, 0, 2 * Math.PI); g.fill(); g.stroke();
        g.restore();
      } else {
        g.strokeStyle = css("--bad"); g.lineWidth = 2;
        g.beginPath(); g.moveTo(X - 6, Y - 6); g.lineTo(X + 6, Y + 6); g.moveTo(X - 6, Y + 6); g.lineTo(X + 6, Y - 6); g.stroke();
        g.restore();
        const b1 = label(g, END_TEXT[frame.status] || frame.status, X + 9, Y - 8, { color: css("--bad"), font: "12px system-ui", kind: "end", bg: SCR });
        // past the stop at the horizon the body's own clock goes on to r = 0 (EX2 §11 item 34): said where it stopped
        const ms = frame.meas || {};
        if (frame.status === "horizon" && ms.tau_centre !== null && ms.tau_centre !== undefined)
          label(g, t("the body's clock reaches r = 0 at τ = {tau}", { tau: geo(ms.tau_centre, 5) }), b1.x0, b1.y1 + 13,
            { color: css("--bad"), font: "12px system-ui", kind: "end", bg: SCR, dir: 1 });
      }
    }
    // scale bar: at the bottom right, its label above it, clear of the axes' numbers (STATUS V51 (h))
    const bw = 100, wM = bw / plane.sx;
    const yb = plane.h - 22, xr = plane.w - 12;
    g.save(); g.strokeStyle = css("--ink"); g.lineWidth = 2;
    g.beginPath(); g.moveTo(xr - bw, yb); g.lineTo(xr, yb); g.stroke(); g.restore();
    label(g, `${num(wM, 3)} M = ${length(wM * M(), { au: AU_M }, 3)}`, xr, yb - 5, { color: css("--ink"), align: "right", kind: "scale" });
    const gi = s ? ghostInfo.get(s.seg) : null;
    const note = gi && opt.ghost
      ? t("The orbit plane from above. Solid: the orbit of this world ({law}), dashed: the ghost ({ghost}) from the same initial data. The green arrow is the initial velocity. Wheel: zoom, drag: pan.",
        { law: lawShort(H.law), ghost: lawShort(gi.law) })
      : t("The orbit plane from above. Solid: the orbit of this world ({law}). The green arrow is the initial velocity. Wheel: zoom, drag: pan.",
        { law: lawShort(H.law) });
    const note2 = SCR && traces.length ? `${note} ${t("Faded: earlier points, labelled with what differs.")}` : note;
    if (ovOrb.textContent !== note2) ovOrb.textContent = note2;
    cvOrb.__layout = { w: plane.w, h: plane.h, labels: layOf(cvOrb), body: bodyAt, R: SCR && s ? screenR(s) : null,
      centre: { x: plane.X(0), y: plane.Y(0) }, scale: plane.sx, capBand, screen: ctx.screen || "live" };
  }
  function drawApsides(g, s, tw) {
    const list = (apsides.get(s.seg) || []).filter((a) => a.t <= tw);
    const peri = list.filter((a) => a.kind === "peri"), apo = list.filter((a) => a.kind === "apo");
    g.save();
    g.fillStyle = css("--muted");
    for (const a of apo.slice(-40)) { const X = plane.X(a.x), Y = plane.Y(a.y); g.fillRect(X - 2.5, Y - 2.5, 5, 5); }
    const show = peri.slice(-8);
    if (peri.length) {  // apsidal lines: the first and the latest periapsis
      const f = peri[0], l = peri[peri.length - 1];
      g.strokeStyle = css("--muted"); g.lineWidth = 1; g.setLineDash([3, 4]);
      g.beginPath(); g.moveTo(plane.X(0), plane.Y(0)); g.lineTo(plane.X(f.x), plane.Y(f.y)); g.stroke();
      g.setLineDash([]); g.strokeStyle = "#c2255c";
      g.beginPath(); g.moveTo(plane.X(0), plane.Y(0)); g.lineTo(plane.X(l.x), plane.Y(l.y)); g.stroke();
    }
    for (const a of show) {
      const X = plane.X(a.x), Y = plane.Y(a.y);
      g.fillStyle = "#c2255c";
      g.beginPath(); g.moveTo(X, Y - 5); g.lineTo(X + 5, Y); g.lineTo(X, Y + 5); g.lineTo(X - 5, Y); g.closePath(); g.fill();
    }
    if (opt.ghost) for (const a of (gapsides.get(s.seg) || []).filter((q) => q.t <= tw).slice(-8)) {
      const X = plane.X(a.x), Y = plane.Y(a.y);
      g.strokeStyle = "#f08c00"; g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(X, Y - 5); g.lineTo(X + 5, Y); g.lineTo(X, Y + 5); g.lineTo(X - 5, Y); g.closePath(); g.stroke();
    }
    g.restore();
    // labels: the newest periapsis of each cluster closer than 14 px (Mercury: all of them at one point)
    let lastXY = null;
    for (let k = show.length - 1; k >= 0; k--) {
      const a = show[k], X = plane.X(a.x), Y = plane.Y(a.y);
      if (lastXY && Math.hypot(X - lastXY[0], Y - lastXY[1]) < 14) continue;
      if (k < show.length - (SCR ? 2 : 4)) continue;
      let deg = (a.phi * 180 / Math.PI) % 360;
      if (deg > 180) deg -= 360; else if (deg <= -180) deg += 360;
      if (Math.abs(deg) < 5e-7) deg = 0;  // below the display precision of the angle (the shift is shown separately)
      let txt = t("p{n:d}: φ = {phi:.7g}°", { n: a.n, phi: deg });
      if (a.n > 1 && peri.length && k === show.length - 1) txt = t("{a}, shift from p{k:d}: {s}", { a: txt, k: peri[0].n, s: angFmt(a.shift) });
      g.save(); g.font = "11px system-ui"; const w = g.measureText(txt).width; g.restore();
      label(g, txt, X + 7 + w > plane.w - 4 ? X - 7 - w : X + 7, Y - 6, { color: "#c2255c", kind: "apsis", bg: SCR });
      lastXY = [X, Y];
    }
  }

  // --- plots: r(t) and 1 − dτ/dt ------------------------------------------------------------------------
  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }
  function drawPlots(frame, tw) {
    placed = placed.filter((q) => q.cv !== cvPlot);
    if (SCR && !opt.plots) { cvPlot.__layout = { w: 0, h: 0, labels: [], hidden: true }; return; }
    const g = setup(cvPlot), W = cvPlot.clientWidth, Hh = cvPlot.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const s = segAt(tw);
    if (!H || !s || W < 2 || Hh < 2) { cvPlot.__layout = { w: W, h: Hh, labels: [] }; return; }
    const c = trails.get(s.seg), gc = opt.ghost ? gtrails.get(s.seg) : null;
    const n = upTo(c, tw), ng = upTo(gc, tw);
    const t1 = tw, t0 = opt.history ? s.t : Math.max(s.t, tw - (s.t_window || (tw - s.t)));
    // (the live player's note lies over the canvas's top: the plots start under it; a screen's note is a band above)
    const right = 10, top1 = SCR ? 22 : 74, gap = SCR ? 30 : 36;
    const h1 = Math.max(30, (Hh - top1 - gap - 22) / 2), top2 = top1 + h1 + gap, h2 = Math.max(30, Hh - top2 - 22);
    let left = 66;  // widened below to the widest number of the axes (Mercury's r is «3.1152981·10⁷»)
    const span = Math.max(t1 - t0, 1e-300);
    const X = (tt) => left + (W - left - right) * (tt - t0) / span;
    const i0 = c ? Math.max(0, upTo(c, t0) - 1) : 0;
    // r(t)
    let lo = Infinity, hi = -Infinity;
    for (let i = i0; i < n; i++) { lo = Math.min(lo, c.r[i]); hi = Math.max(hi, c.r[i]); }
    if (frame && frame.seg === s.seg) { lo = Math.min(lo, frame.r); hi = Math.max(hi, frame.r); }
    const gi0 = gc ? Math.max(0, upTo(gc, t0) - 1) : 0;
    for (let i = gi0; i < ng; i++) { lo = Math.min(lo, gc.r[i]); hi = Math.max(hi, gc.r[i]); }
    if (!Number.isFinite(lo)) { lo = 0; hi = 1; }
    if (hi - lo < 1e-9 * Math.max(Math.abs(hi), 1)) { const m = 0.5 * (hi + lo); lo = m * (1 - 1e-6) - 1e-9; hi = m * (1 + 1e-6) + 1e-9; }
    const pad = 0.08 * (hi - lo); lo -= pad; hi += pad;
    const Y1 = (r) => top1 + h1 * (1 - (r - lo) / (hi - lo));
    const dig = Math.min(12, Math.max(5, Math.ceil(Math.log10(Math.abs(hi) / Math.max(hi - lo, 1e-300))) + 2));
    g.save(); g.font = "10px system-ui";
    for (let k = 0; k <= 4; k++) left = Math.max(left, g.measureText(num(lo + (hi - lo) * k / 4, dig)).width + 8);
    g.restore();
    axes(g, left, top1, W - left - right, h1, lo, hi, (v) => num(v, dig), "r, M");
    if (H.law === "GR" || (gc && ghostInfo.get(s.seg) && ghostInfo.get(s.seg).law === "GR")) {
      for (const [r, lab, col] of [[H.special.isco, "ISCO", "#e8590c"], [H.special.horizon, "2M", "#868e96"], [H.special.photon, "3M", "#ae3ec9"]]) {
        if (r > lo && r < hi) { g.save(); g.strokeStyle = col; g.setLineDash([5, 4]); g.beginPath(); g.moveTo(left, Y1(r)); g.lineTo(W - right, Y1(r)); g.stroke(); g.restore();
          label(g, lab, W - right - 4, Y1(r) - 3, { color: col, align: "right", font: "10px system-ui", kind: "radius" }); }
      }
    }
    series(g, gc, gi0, ng, X, (i) => Y1(gc.r[i]), "#f08c00", [6, 5]);
    series(g, c, i0, n, X, (i) => Y1(c.r[i]), css("--accent"), null);
    if (frame && frame.seg === s.seg) dot(g, X(tw), Y1(frame.r), css("--accent"));
    // 1 − dτ/dt
    if (H.law === "GR") {
      let lo2 = Infinity, hi2 = -Infinity;
      for (let i = i0; i < n; i++) { const v = c.lag[i]; lo2 = Math.min(lo2, v); hi2 = Math.max(hi2, v); }
      if (frame && frame.seg === s.seg) { lo2 = Math.min(lo2, frame.deficit); hi2 = Math.max(hi2, frame.deficit); }
      if (!Number.isFinite(lo2)) { lo2 = 0; hi2 = 1; }
      if (hi2 - lo2 < 1e-6 * Math.max(Math.abs(hi2), 1e-300)) { const m = 0.5 * (hi2 + lo2); lo2 = m * 0.999; hi2 = m * 1.001 + 1e-300; }
      const pad2 = 0.08 * (hi2 - lo2); lo2 -= pad2; hi2 += pad2;
      const Y2 = (v) => top2 + h2 * (1 - (v - lo2) / (hi2 - lo2));
      axes(g, left, top2, W - left - right, h2, lo2, hi2, (v) => num(v, 4), "1 − dτ/dt");
      series(g, c, i0, n, X, (i) => Y2(c.lag[i]), "#2b8a3e", null);
      if (frame && frame.seg === s.seg) dot(g, X(tw), Y2(frame.deficit), "#2b8a3e");
    } else {
      label(g, t("Newton: time is absolute:"), left, top2 + 20, { font: "12px system-ui", kind: "note" });
      label(g, t("the body's clock runs like the distant observer's clock (dτ/dt = 1)."), left, top2 + 38, { font: "12px system-ui", kind: "note" });
    }
    // time axis
    label(g, tfmt(t0, 5), left, Hh - 6, { kind: "time" });
    label(g, tfmt(t1, 5), W - right, Hh - 6, { align: "right", kind: "time" });
    const pn = opt.history
      ? t("r(t) of the body (dashed: the ghost) and the lag of its clock 1 − dτ/dt; the axis is the world's time t (the whole segment).")
      : t("r(t) of the body (dashed: the ghost) and the lag of its clock 1 − dτ/dt; the axis is the world's time t (the last orbits).");
    if (ovPlot.textContent !== pn) ovPlot.textContent = pn;
    cvPlot.__layout = { w: W, h: Hh, labels: layOf(cvPlot) };
  }
  function axes(g, x, y, w, h, lo, hi, fmt, title) {
    g.save(); g.strokeStyle = css("--line"); g.strokeRect(x, y, w, h); g.restore();
    for (let k = 0; k <= 4; k++) {
      const v = lo + (hi - lo) * k / 4, Y = y + h * (1 - k / 4);
      g.save(); g.strokeStyle = css("--grid"); g.beginPath(); g.moveTo(x, Y); g.lineTo(x + w, Y); g.stroke(); g.restore();
      if (k === 0 || k === 4 || h >= 70 || k === 2) label(g, fmt(v), 2, Y + 3, { font: "10px system-ui", kind: "tick" });
    }
    label(g, title, x + 4, y - 6, { color: css("--ink"), kind: "title" });
  }
  function series(g, c, i0, n, X, Y, col, dash) {
    if (!c || n - i0 < 1) return;
    g.save(); g.strokeStyle = col; g.lineWidth = 1.4; g.setLineDash(dash || []); g.beginPath();
    let px = -1e9;
    for (let i = i0; i < n; i++) {
      const x = X(c.t[i]);
      if (i === i0) g.moveTo(x, Y(i)); else if (x - px >= 0.5 || i === n - 1) g.lineTo(x, Y(i)); else continue;
      px = x;
    }
    g.stroke(); g.restore();
  }
  function dot(g, x, y, col) { g.save(); g.fillStyle = col; g.beginPath(); g.arc(x, y, 4, 0, 2 * Math.PI); g.fill(); g.restore(); }

  // --- Watch: the caption's band under the pictures (desktop: the caption lies over the stage's bottom) ----------------
  // The band is the height of the story's longest caption at the stage's present width, the same for the whole story,
  // so the scale does not change from caption to caption and no caption covers the orbit, the plots or their axes.
  function captionBand() {
    if (!WATCH || !story) return 0;
    const stage = cvOrb.closest(".dm-stage"), cap = stage && stage.querySelector(".dm-caption");
    if (!cap || getComputedStyle(cap).position !== "absolute") return 0;  // a phone: the caption has its own place
    const probe = cap.cloneNode(false);
    probe.removeAttribute("hidden"); probe.removeAttribute("aria-live"); probe.setAttribute("aria-hidden", "true");
    probe.style.visibility = "hidden";
    stage.append(probe);
    let hMax = 0;
    for (const text of story.captions) { probe.textContent = t(text); hMax = Math.max(hMax, probe.getBoundingClientRect().height); }
    probe.remove();
    const cs = getComputedStyle(cap);
    return Math.ceil(hMax + (parseFloat(cs.bottom) || 0) + 10);
  }
  function syncBand() {
    if (!WATCH) return;
    const b = captionBand();
    if (b !== capBand) { capBand = b; center.style.paddingBottom = b ? `${b}px` : ""; fitKey = ""; }
  }
  if (WATCH) new ResizeObserver(() => { const b = captionBand(); if (b !== capBand) { syncBand(); want(); } }).observe(center);

  // --- panels -----------------------------------------------------------------------------------------------
  function kv(rows) { return el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)])); }
  function drawOrbPanel(frame, tw) {
    const s = segAt(tw);
    if (!H || !s) { orbBox.replaceChildren(); return; }
    const i = s.init, el2 = s.elements;
    const peri = (apsides.get(s.seg) || []).filter((a) => a.kind === "peri" && a.t <= tw);
    const last = peri.length ? peri[peri.length - 1] : null;
    const mean = peri.length >= 2 ? (peri[peri.length - 1].shift / (peri.length - 1)) : null;
    const rows = [[t("Law"), H.law === "GR" ? t("GR (Schwarzschild)") : t("Newton (approximation)")],
      [t("Central body"), H.body.R > 0
        ? t("{m:.6g} M☉, R = {R:.6g} M ({km:.6g} km)", { m: H.body.mass_msun, R: H.body.R, km: H.body.R_km })
        : t("{m:.6g} M☉, {body}", { m: H.body.mass_msun, body: H.law === "GR" ? t("a black hole") : t("a point mass") })],
      ["1 M = GM/c²", length(M(), { au: AU_M }, 6)], [t("Segment"), t("{seg:d}: {reason}", { seg: s.seg, reason: s.reason })], [t("Orbit"), t(s.kind_text)],
      [t("Start"), `r = ${lenM(i.r0)}`], [t("Speed"), t("{v:.7g} c = {k:.6g} × circular, angle {a:.5g}°", { v: i.v, k: i.k, a: i.alpha })]];
    if (H.law === "GR") rows.push([t("e (energy per mc²)"), num(s.e, 12)], ["e² − 1", num(s.em1, 8)], [t("l (angular momentum, M·c)"), num(s.l, 10)]);
    else rows.push([t("E (per c²)"), num(s.E, 10)], ["h (M·c)", num(s.h, 10)]);
    if (s.r_peri && s.kind !== "plunge") rows.push([t("Periapsis"), lenM(s.r_peri)]);
    if (s.r_apo) rows.push([t("Apoapsis"), lenM(s.r_apo)]);
    if (el2) rows.push([t("Eccentricity ε"), num(el2.ecc, 8)], [t("p (parameter)"), lenM(el2.p)], ["a = p/(1 − ε²)", lenM(el2.a)]);
    rows.push([t("Periapses passed"), String(peri.length)]);
    if (last && last.adv !== null) rows.push([t("Advance over the last orbit"), angFmt(last.adv)]);
    if (mean !== null) rows.push([t("Advance, mean"), angFmt(mean)]);
    if (s.adv_exact !== null && s.adv_exact !== undefined) rows.push([t("Exact formula (reference)"), angFmt(s.adv_exact)]);
    if (last && last.dt) rows.push([t("Radial period (t)"), tfmt(last.dt)]);
    if (frame && frame.n_lap) rows.push([t("Turns in φ"), String(frame.n_lap)]);
    const items = [kv(rows)];
    const gi = ghostInfo.get(s.seg);
    if (gi) {
      const grow = [[t("Law"), lawShort(gi.law)], [t("Orbit"), t(gi.kind_text)]];
      if (gi.r_peri && gi.kind !== "plunge") grow.push([t("Periapsis"), lenM(gi.r_peri)]);
      if (gi.r_apo) grow.push([t("Apoapsis"), lenM(gi.r_apo)]);
      const gp = (gapsides.get(s.seg) || []).filter((a) => a.t <= tw);
      grow.push([t("Periapses passed"), String(gp.length)]);
      items.push(el("h5", { style: { margin: "10px 0 4px" } }, t("Ghost (dashed)")), kv(grow));
    }
    orbBox.replaceChildren(...items);
  }
  function drawClockPanel(frame, tw) {
    if (!H || !frame) { clockBox.replaceChildren(); return; }
    const since = tw - frame.t_launch;
    const rows = [[t("t, the world's time (a distant observer)"), tfmt(tw, 10)], [t("t since the launch of the body"), tfmt(since, 10)],
      [t("τ, the body's clock since the launch"), tfmt(frame.tau, 10)],
      [t("τ / t (mean since the launch)"), since > 0 ? num(frame.tau / since, 12) : "—"],
      [t("dτ/dt now"), num(frame.rate, 12)], ["1 − dτ/dt", num(frame.deficit, 10)]];
    if (H.law === "GR") {
      rows.push(["   " + t("gravity √(1 − 2M/r)"), num(frame.grav, 12)], ["   " + t("motion √(1 − v²/c²)"), num(frame.kin, 12)]);
    }
    rows.push([t("r now"), lenM(frame.r)], [t("Speed (a static observer)"), frame.v === null || frame.v === undefined ? "—" : num(frame.v, 8) + " c"]);
    if (frame.ghost) rows.push([t("Ghost's clock τ"), tfmt(frame.ghost.tau, 10)]);
    // past the horizon's stop: the body's own clock on to r = 0 (EX2 §11 item 34; the distant picture ends at the stop)
    const ms = frame.meas || {};
    if (ms.tau_centre !== null && ms.tau_centre !== undefined) {
      rows.push([t("τ at r = 0 (the body's clock, past the stop)"), geo(ms.tau_centre, 10)],
        [t("τ inside the horizon, from r = 2M to r = 0"), geo(ms.dtau_inside, 8)]);
    }
    const items = [kv(rows)];
    if (H.law === "GR") items.push(el("div", { class: "help" },
      t("dτ/dt = (1 − 2M/r)/e along the geodesic: the product of the gravitational factor (the clock of a static observer at this r) and the factor of the speed relative to that observer.")));
    if (!frame.alive) items.push(el("div", { class: "st-bad" }, END_TEXT[frame.status] || frame.status));
    if (frame.lag === true) items.push(el("div", { class: "st-bad" }, t("The computation cannot keep up with the chosen speed: the world runs slower.")));
    clockBox.replaceChildren(...items);
  }

  const END_TEXT = { horizon: t("at the horizon (r − 2M = 2·10⁻⁶ M; beyond it t → ∞)"), surface: t("fell onto the surface"),
    center: t("fell into the centre"), escape: t("gone to infinity") };
  const lawShort = (law) => (law === "GR" ? t("GR") : t("Newton"));

  return {
    center, rightPanels,
    quantSafe: QUANT_SAFE,
    overlays: OVERLAYS.map((o) => ({ ...o, label: t(o.label) })),
    setOverlay(id, on) {
      const k = { newton: "ghost", radii: "radii", apsides: "apsides", plots: "plots", follow: "follow" }[id];
      if (!k) return;
      opt[k] = !!on;
      if (k === "plots") center.classList.toggle("u34-noplots", !on);
      if (k === "ghost") fitKey = "";  // the box may have been the ghost's
      want();
    },
    // Explore: earlier points, each a decoded world drawn up to its own time, labelled with what differs
    setTraces(list) { traces = list || []; want(); },
    // Watch: the story's worlds; one box for all of them (every trail and Newton's, as recorded), never refitted
    setStory({ worlds }) {
      let R = 0;
      const caps = [];
      for (const W of worlds || []) {
        for (const m of W.viewMsgs || []) {
          if ((m.meta.type === "trail" || m.meta.type === "gtrail") && m.blobs && m.blobs.x) {
            const { x, y } = m.blobs;
            for (let i = 0; i < x.length; i++) R = Math.max(R, Math.abs(x[i]), Math.abs(y[i]));
          }
        }
        for (const c of W.captions || []) caps.push(c.text);
      }
      story = { R: R || 10, captions: caps };
      fitKey = ""; userMoved = false;
      syncBand();
      want();
    },
    help: () => el("div", {},
      el("h4", {}, t("What is on the screen")),
      el("p", {}, t("On the left: the orbit plane from above. The solid line is the orbit computed in this run by the world's laws; it appears as the world's time t (the clock of a distant static observer) reaches it. Diamonds are periapses (the numbers are their angle φ), squares apoapses; the solid ray from the centre is the latest periapsis, the dashed one the first: the angle between them is the accumulated periapsis advance. The orange dashed line is the “ghost”: the orbit under the other theory (GR ↔ Newton) from the same initial data; it does not affect the world.")),
      el("p", {}, t("Circles (GR): the horizon 2M, the photon sphere 3M (the circular orbit of light), the marginally bound circular orbit 4M, the ISCO 6M (innermost stable circular orbit); the radii come from the engine (lfphys.core.gravity.kerr at zero spin).")),
      el("p", {}, t("On the right: r(t) and the lag of the body's clock 1 − dτ/dt: the body's clock runs slower because of gravity (√(1 − 2M/r)) and because of its speed relative to the static observer (√(1 − v²/c²)).")),
      el("p", {}, t("The launch of the body (r₀, the speed as a fraction of the circular one, the angle to the tangent) changes apply at once: the body is launched again at the world's current moment from its current direction to the centre. “Push” changes the speed along the motion instantly; the body's clock keeps running. The law of gravitation and the mass and radius of the central body are the world's laws: changing them is a new world in the same run.")),
      el("p", {}, t("A fall through the horizon: for a distant observer the body only approaches r = 2M asymptotically (the time t grows logarithmically), while the body's proper time to the horizon is finite; the computation stops at r − 2M = 2·10⁻⁶ M.")),
      el("p", {}, t("Past that stop the body's own clock goes on: the proper time through the horizon to r = 0 is the quadrature ∫dr/√R(r), which the panel “Clocks” and the readout show; inside the horizon it is at most πM. The distant observer's picture ends at the stop, as it should."))),
    reset() {
      H = null; units = null; liveVals = {}; segs = []; trails = new Map(); gtrails = new Map(); apsides = new Map();
      gapsides = new Map(); ghostInfo = new Map(); lastT = 0; changed = true;  // fittedSeg kept: the same world keeps its view
    },
    // key frames (player.js): the columns and lists only grow (their objects and lengths are kept, so a ghost orbit
    // switched off later comes back); the small maps and the live values are copied
    snapshot() {
      const lens = (m) => new Map([...m].map(([k, v]) => [k, { o: v, n: Array.isArray(v) ? v.length : v.n }]));
      return { segs: segs.length, trails: lens(trails), gtrails: lens(gtrails), apsides: lens(apsides),
               gapsides: lens(gapsides), ghostInfo: new Map(ghostInfo), liveVals: { ...liveVals } };
    },
    restore(k) {
      const back = (m) => new Map([...m].map(([key, { o, n }]) => { if (Array.isArray(o)) o.length = n; else o.n = n; return [key, o]; }));
      segs.length = k.segs; trails = back(k.trails); gtrails = back(k.gtrails); apsides = back(k.apsides);
      gapsides = back(k.gapsides); ghostInfo = new Map(k.ghostInfo); liveVals = { ...k.liveVals }; changed = true;
    },
    onHeader(meta) {
      H = meta; units = meta.units; liveVals = { ...(meta.live || {}) }; changed = true;
      if (meta.world !== fittedWorld) { fittedWorld = meta.world; fittedSeg = -1; }  // a new world is framed anew
    },
    onMessage(meta, blobs) {
      switch (meta.type) {
        case "segment": segs.push(meta); ghostInfo.set(meta.seg, meta.ghost || null); break;
        case "trail": if (blobs && blobs.t) push(trails, meta.seg, blobs, true); break;
        case "gtrail": if (blobs && blobs.t) push(gtrails, meta.seg, blobs, false); break;
        case "apsis": { if (!apsides.has(meta.seg)) apsides.set(meta.seg, []); apsides.get(meta.seg).push(meta); break; }
        case "gapsis": { if (!gapsides.has(meta.seg)) gapsides.set(meta.seg, []); gapsides.get(meta.seg).push(meta); break; }
        case "ghost": {
          ghostInfo.set(meta.seg, meta.info || null);
          if (!meta.info) { gtrails.delete(meta.seg); gapsides.delete(meta.seg); }
          break;
        }
        case "event":
          if (meta.kind === "action" && meta.name === "set" && meta.args) Object.assign(liveVals, meta.args);
          break;
        default: break;
      }
      want();
    },
    render(frame, tw) {
      if (!H) return;
      if (SCR && !changed && frame === lastFrame && tw === lastT) return;
      changed = false; lastFrame = frame;
      lastT = tw;
      if (WATCH && story && !capBand) syncBand();
      drawOrbit(frame, tw);
      drawPlots(frame, tw);
      if (shownBox(orbBox)) drawOrbPanel(frame, tw);
      if (shownBox(clockBox)) drawClockPanel(frame, tw);
    },
  };
}
