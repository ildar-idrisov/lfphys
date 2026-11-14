// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u32 view: the apparatus seen from above (the computed wave behind the slits, particles in flight, flow lines)
// and the screen (individual detections and their histogram against the run's own expectation).
// All data come from the run: detections are events with their computed positions and times, the map and the
// curves are computed by the run for the current apparatus segment.
//
// The screens (design lfphys/sources/explore_2026-11-14_design.md §2.4, §6): with ctx.screen "watch" or "explore" the
// view is the clean one — no quick set-up bar and no screen toolbar (the filter is «all», only the current segment is
// shown), the two pictures side by side (stacked below 1000 px), one readout line (hits, χ²/dof and p, |γ₁₂|) from the
// frame, the slits numbered; Watch adds the fold «Latest particles: the chain of causes» under the view. Its right
// panels (particle, model of the slit screen, counters, approximations) fold into «How we know this is right»
// (demo.js). Explore: the overlays below, earlier points' expectation curves as faded traces (setTraces), frames
// without their dropped `flight` blob, quantised blobs (QUANT_SAFE: the map's u8 √ steps stay under the colour map's
// 256 levels on its linear scale; the screen positions' u16 steps are below 0.03 of a detector pixel). Every count drawn
// is of the messages fed up to the time shown. The live player (no ctx.screen) is unchanged.
import { t, fmt, parseNum } from "/static/js/i18n.js";
import { css, el, fmtInput, fresh2d, num, numberInput, panel, time } from "/static/js/ui.js";

// what the view accepts quantised (registry.view_declarations reads this literal)
export const QUANT_SAFE = { "segment.map": "u8sqrt", "segment.bohm_x": "u16", "detections.t": "u16", "detections.x": "u16",
  "detections.y": "u8", "header.x": "u16" };
// the overlays it can toggle on the screens (registry.view_declarations reads the ids); defaults of Explore
export const OVERLAYS = [
  { id: "expectation", label: "expectation", default: true },
  { id: "no_interference", label: "without interference", default: false },
  { id: "wave", label: "wave", default: true },
  { id: "flow_lines", label: "flow lines", default: false },
  { id: "log_map", label: "log scale of the map", default: false },
];
// Watch shows what its captions talk about: both curves and the flow lines
const WATCH_ON = { expectation: true, no_interference: true, wave: true, flow_lines: true, log_map: false };
const OPT_OF = { expectation: "expect", no_interference: "cl", wave: "map", flow_lines: "bohm", log_map: "log" };
const SCREENS = new Set(["watch", "explore", "lab"]);

// the colour of light of a wavelength (nm) for the dots and the traces: a display convention, not physics (visible
// range only; null outside it). Piecewise-linear hues with the intensity falling off at the ends of the visible range
export function lightColour(nm) {
  if (!(nm >= 380 && nm <= 780)) return null;
  let r = 0, g = 0, b = 0;
  if (nm < 440) { r = (440 - nm) / 60; b = 1; } else if (nm < 490) { g = (nm - 440) / 50; b = 1; }
  else if (nm < 510) { g = 1; b = (510 - nm) / 20; } else if (nm < 580) { r = (nm - 510) / 70; g = 1; }
  else if (nm < 645) { r = 1; g = (645 - nm) / 65; } else r = 1;
  const f = nm < 420 ? 0.3 + 0.7 * (nm - 380) / 40 : nm > 700 ? 0.3 + 0.7 * (780 - nm) / 80 : 1;
  const c = (x) => Math.round(255 * Math.pow(x * f, 0.8));
  return `rgb(${c(r)},${c(g)},${c(b)})`;
}

let STYLE = false;  // the screens' layout, added once per page
function addStyle() {
  if (STYLE) return;
  STYLE = true;
  document.head.append(el("style", {}, `
.u32-c { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.u32-panes { display: flex; flex: 1; min-height: 0; }
.u32-panes > div { display: flex; flex-direction: column; min-height: 0; min-width: 0; }
.u32-app { flex: 1.15 1 0; border-right: 1px solid var(--line); }
.u32-scr { flex: 1 1 0; }
.u32-read { display: flex; flex-wrap: wrap; gap: 2px 16px; padding: 5px 10px; font-size: 14px; background: var(--panel); border-bottom: 1px solid var(--line); }
.u32-read b { font-variant-numeric: tabular-nums; }
.u32-stories { background: var(--panel); border-top: 1px solid var(--line); padding: 4px 10px; font-size: 13px; max-height: 30%; overflow: auto; }
.u32-stories > summary { cursor: pointer; font-weight: 600; }
.u32-c.u32-watch .u32-panes { margin-bottom: 128px; }
.u32-app .overlay, .u32-scr .overlay { right: 8px; }
@media (max-width: 999px) {
  .u32-wide { display: none; }
  .dm-stage:has(> .u32-c) { aspect-ratio: auto; max-height: none; }
  .dm-stage > .u32-c.u32-on { min-height: 460px; }
  .u32-panes { flex-direction: column; }
  .u32-app { flex: 0 0 170px; border-right: 0; border-bottom: 1px solid var(--line); }
  .u32-scr { flex: 1 0 250px; }
  .u32-c.u32-watch .u32-panes { margin-bottom: 0; }
  .u32-stories { max-height: 220px; }
}`));
}

const F_DARK = 1, F_R1 = 2, F_READ = 4, F_SCAT = 8, F_REC = 16, F_MIX = 32;
// the elements at the slits by their short names (the same msgids as the run's own texts)
const ELEM = { polarizer: "polariser", hwp: "λ/2 plate", qwp: "λ/4 plate", rot_y: "spin rotation about y",
               filter: "spin filter", phase: "phase shift", block: "shutter" };

// a perceptual colormap (magma-like), 256 entries
const LUT = (() => {
  const stops = [[0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129], [181, 54, 122], [229, 80, 100],
                 [251, 135, 97], [254, 194, 135], [252, 253, 191]];
  const out = new Uint8ClampedArray(256 * 3);
  for (let i = 0; i < 256; i++) {
    const f = i / 255 * (stops.length - 1), k = Math.min(Math.floor(f), stops.length - 2), w = f - k;
    for (let c = 0; c < 3; c++) out[3 * i + c] = stops[k][c] * (1 - w) + stops[k + 1][c] * w;
  }
  return out;
})();

export function createView(ctx) {
  let H = null, X = null, segs = [], stories = [];
  let det = null;  // growing columns
  const SCR = SCREENS.has(ctx.screen);  // a demonstration's screen (Watch, Explore), not the live player
  const opt = { filter: "all", phase0: 0, phaseW: 60, segOnly: true, expect: true, cl: true, map: true, bohm: true, log: false };
  const ovOn = Object.fromEntries(OVERLAYS.map((o) => [o.id, ctx.screen === "watch" ? WATCH_ON[o.id] : o.default]));
  if (SCR) for (const [id, on] of Object.entries(ovOn)) opt[OPT_OF[id]] = on;
  let traces = [];  // earlier points (Explore): [{key, label, W, t, alpha}], W.view an instance of this view fed up to t

  // --- DOM --------------------------------------------------------------------------------------------
  const selFilter = el("select", { title: t("Which particles to show on the screen") },
    el("option", { value: "all" }, t("all particles")),
    el("option", { value: "r0" }, t("the which-path detector showed {r:d}", { r: 0 })),
    el("option", { value: "r1" }, t("the which-path detector showed {r:d}", { r: 1 })),
    el("option", { value: "noscat" }, t("no scattered photon")),
    el("option", { value: "phase" }, t("scattered photon recorded: phase Δk·d in the window")),
    el("option", { value: "dark" }, t("dark counts only (known only in a simulation)")));
  // number fields that take a decimal comma (review i18n-browser F1): a text that is not a number is refused, and the
  // field shows the value in use again
  const inPhase = numberInput(0, { style: { width: "5em" }, title: t("centre of the phase window, °") }, { step: 15 });
  const inPhaseW = numberInput(60, { style: { width: "5em" }, title: t("width of the window, °") }, { step: 15, min: 0 });
  const phaseBox = el("span", { style: { display: "none" } }, " φ₀ ", inPhase, "° ± ", inPhaseW, "°/2");
  const cbSeg = el("input", { type: "checkbox", checked: true });
  const cbCurves = el("input", { type: "checkbox", checked: true });
  const cbMap = el("input", { type: "checkbox", checked: true });
  const cbBohm = el("input", { type: "checkbox", checked: true });
  const cbLog = el("input", { type: "checkbox" });
  const btnFly = el("button", { title: t("A speed at which the flight of one particle is visible (≈{s:d} s per flight)", { s: 2 }) }, t("▷ flight"));
  const btnBuild = el("button", { title: t("The speed at which the pattern builds up (≈{n:d} particles per second)", { n: 40 }) }, t("▷▷ build-up"));
  const cvApp = el("canvas"), cvScr = el("canvas");
  const ovApp = el("div", { class: "overlay" }), ovScr = el("div", { class: "overlay" });
  const toolbar = el("div", { class: "toolbar" }, el("span", { class: "muted" }, t("Screen:")), selFilter, phaseBox,
    el("label", { title: t("Show only the current segment (after the last change of the set-up)") }, cbSeg, " ", t("current segment")),
    el("label", {}, cbCurves, " ", t("expectation")), el("label", {}, cbLog, " ", t("log scale of the map")),
    el("label", {}, cbMap, " ", t("wave")), el("label", {}, cbBohm, " ", t("flow lines")), btnFly, btnBuild);
  const quick = el("div", { class: "toolbar quick", title: t("Set-up: changes at once (the same as in the panel on the left)") },
    el("span", { class: "muted" }, t("Set-up:")),
    ctx.liveControl ? [ctx.liveControl("wp_mode", { label: t("observer") }), ctx.liveControl("wp_theta", { label: t("coupling θ, °") }),
      ctx.liveControl("L2_m", { label: t("screen, m") }), ctx.liveControl("a_um", { label: t("slit, µm") }),
      ctx.liveControl("d_um", { label: t("period, µm") })] : null);
  const infoBox = el("div", { class: "kv" });
  const statBox = el("div", {});
  const storyBox = el("div", { class: "events" });
  const approxBox = el("div", { class: "help" });
  const vecBox = el("div", {});
  const readBox = el("div", { class: "u32-read", "data-u32": "readouts" });  // the screens' readout line
  let center, rightPanels;
  if (!SCR) {
    center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick, toolbar,
      el("div", { class: "split" },
        el("div", {}, el("div", { class: "canvas-wrap" }, cvApp, ovApp)),
        el("div", {}, el("div", { class: "canvas-wrap" }, cvScr, ovScr))));
    rightPanels = [panel(t("Particle"), infoBox), panel(t("Model of the slit screen"), vecBox), panel(t("Counters and statistics"), statBox),
      panel(t("Approximations of this segment"), approxBox), panel(t("Latest particles: the chain of causes"), storyBox)];
  } else {
    addStyle();
    // Watch: the chain of causes of the latest particles folds under the view (design §6.3); Explore drops the stories
    const storyFold = ctx.screen === "watch" ? el("details", { class: "u32-stories" }, el("summary", {}, t("Latest particles: the chain of causes")), storyBox) : null;
    center = el("div", { class: `u32-c u32-on u32-${ctx.screen}` }, readBox,
      el("div", { class: "u32-panes" },
        el("div", { class: "u32-app" }, el("div", { class: "canvas-wrap" }, cvApp, ovApp)),
        el("div", { class: "u32-scr" }, el("div", { class: "canvas-wrap" }, cvScr, ovScr))), storyFold);
    rightPanels = [panel(t("Particle"), infoBox), panel(t("Model of the slit screen"), vecBox), panel(t("Counters and statistics"), statBox),
      panel(t("Approximations of this segment"), approxBox)];
  }

  selFilter.onchange = () => { opt.filter = selFilter.value; phaseBox.style.display = opt.filter === "phase" ? "" : "none"; full(); };
  const readNum = (inp, key) => {
    const r = parseNum(inp.value);
    if (r.err) { inp.value = fmtInput(opt[key]); return; }
    opt[key] = r.value; inp.value = fmtInput(r.value); full();
  };
  inPhase.onchange = () => readNum(inPhase, "phase0");
  inPhaseW.onchange = () => readNum(inPhaseW, "phaseW");
  for (const [cb, k] of [[cbSeg, "segOnly"], [cbMap, "map"], [cbBohm, "bohm"], [cbLog, "log"]])
    cb.onchange = () => { opt[k] = cb.checked; full(); };
  cbCurves.onchange = () => { opt.expect = opt.cl = cbCurves.checked; full(); };  // the live player: both curves at once
  btnFly.onclick = () => H && ctx.send("speed", { value: now().t_flight / 2 });
  btnBuild.onclick = () => H && ctx.send("speed", { value: 40 / now().rate });

  const offDots = document.createElement("canvas");
  let dotsState = null;  // {n, w, h, key}
  let histState = null;  // {key, n, counts, tot}
  let mapCache = null;   // {seg, log, img}
  let lastFrame = null, curBlobs = {};
  const flightOf = () => curBlobs.flight || [];
  for (const cv of [cvApp, cvScr]) new ResizeObserver(() => { dotsState = null; mapCache = null; ctx.requestRender(); }).observe(cv);
  window.addEventListener("themechange", () => { dotsState = null; });
  function full() { dotsState = null; mapCache = null; ctx.requestRender(); }

  // --- data -------------------------------------------------------------------------------------------
  function newCols() { return { n: 0, cap: 0, t: null, x: null, y: null, f: null, k: null, s: null }; }
  function push(b) {
    const m = b.t.length;
    if (det.n + m > det.cap) {
      const cap = Math.max(1024, 2 * (det.n + m));
      const grow = (old, T) => { const a = new T(cap); if (old) a.set(old.subarray(0, det.n)); return a; };
      det.t = grow(det.t, Float64Array); det.x = grow(det.x, Float64Array); det.y = grow(det.y, Float32Array);
      det.f = grow(det.f, Uint8Array); det.k = grow(det.k, Float32Array); det.s = grow(det.s, Uint16Array);
      det.cap = cap;
    }
    det.t.set(b.t, det.n); det.x.set(b.x, det.n); det.y.set(b.y, det.n); det.f.set(b.f, det.n); det.k.set(b.k, det.n); det.s.set(b.s, det.n);
    det.n += m;
  }
  function countUpTo(tw) {  // detections are in time order
    let lo = 0, hi = det.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (det.t[m] <= tw) lo = m + 1; else hi = m; }
    return lo;
  }
  function segAt(tw) { let s = segs[0]; for (const g of segs) if (g.t <= tw) s = g; return s; }
  function now() { const s = segs[segs.length - 1]; return (s && s.setup) || H; }
  function pass(i, seg) {
    const f = det.f[i];
    if (opt.segOnly && seg && (det.s[i] !== seg.seg || (f & F_MIX))) return false;  // transitional: other segment's slits
    switch (opt.filter) {
      case "r0": return (f & F_READ) && !(f & F_R1) && !(f & F_DARK);
      case "r1": return (f & F_R1) && !(f & F_DARK);
      case "noscat": return !(f & F_SCAT);
      case "phase": {
        if (!(f & F_SCAT) || !(f & F_REC)) return false;
        let d = (det.k[i] * 180 / Math.PI - opt.phase0) % 360; if (d > 180) d -= 360; if (d < -180) d += 360;
        return Math.abs(d) <= opt.phaseW / 2;
      }
      case "dark": return !!(f & F_DARK);
      default: return true;
    }
  }
  function dotColor(i) {
    const f = det.f[i];
    if (f & F_DARK) return "#868e96";
    if (f & F_READ) return f & F_R1 ? "#e8590c" : "#1c7ed6";
    return (SCR && lightOf(now())) || css("--ink");
  }
  // the colour of a photon's light on the screens (a massive particle or invisible light: the ink colour)
  function lightOf(G) { const p = G && G.particle; return p && !p.mass_kg && p.lambda_m ? lightColour(p.lambda_m * 1e9) : null; }
  // the detections shown at the time tw: on the screens the view holds exactly the messages up to the frame shown, so
  // all of them (a quantised time may lie a rounding after its frame's); the live player counts by time
  function shownUpTo(tw) { return SCR ? det.n : countUpTo(tw); }

  // --- apparatus view -----------------------------------------------------------------------------------
  function drawApparatus(frame, tw) {
    const cv = cvApp, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(tw);
    if (!seg) return;
    const geo = (seg.setup || H).geometry;
    const left = Math.round(W * 0.16), top = 18, bot = Hh - 22, mh = bot - top;
    const z0 = seg.map_z[0], zL = seg.map_z[seg.map_z.length - 1];
    const uOf = (z) => left + (W - left - 8) * Math.log(z / z0) / Math.log(zL / z0);
    const w0 = seg.map_w[0];
    const yOf = (xi) => top + mh * (1 - xi) / 2;
    // map
    if (opt.map) {
      if (!mapCache || mapCache.seg !== seg.seg || mapCache.log !== opt.log || mapCache.W !== W || mapCache.H !== Hh) {
        const nz = seg.map_z.length, nxi = seg.map.length / nz;
        const img = new ImageData(nz, nxi);
        for (let i = 0; i < nz; i++) for (let j = 0; j < nxi; j++) {
          let v = seg.map[i * nxi + j];
          if (opt.log) v = Math.max(0, 1 + Math.log10(Math.max(v, 1e-4)) / 4);
          const c = Math.min(255, Math.max(0, Math.round(v * 255)));
          const o = 4 * ((nxi - 1 - j) * nz + i);
          img.data[o] = LUT[3 * c]; img.data[o + 1] = LUT[3 * c + 1]; img.data[o + 2] = LUT[3 * c + 2]; img.data[o + 3] = 255;
        }
        const oc = document.createElement("canvas"); oc.width = nz; oc.height = nxi; oc.getContext("2d").putImageData(img, 0, 0);
        mapCache = { seg: seg.seg, log: opt.log, W, H: Hh, oc };
      }
      g.imageSmoothingEnabled = true;
      g.drawImage(mapCache.oc, left, top, W - left - 8, mh);
    }
    // the part of the map next to the slits where the paraxial field deviates from the exact solution by > 1 %
    if (opt.map && seg.z_paraxial && seg.z_paraxial > z0 * 1.001) {
      const Xp = uOf(Math.min(seg.z_paraxial, zL));
      g.save(); g.strokeStyle = "rgba(255,255,255,0.35)"; g.lineWidth = 1;
      for (let xx = left - mh; xx < Xp; xx += 8) { g.beginPath(); g.moveTo(Math.max(xx, left), top + Math.max(0, left - xx)); g.lineTo(Math.min(xx + mh, Xp), top + Math.min(mh, Xp - xx)); g.stroke(); }
      // label near the bottom edge, clear of the overlay text at the top and of the probe label at the bottom
      const lab = seg.z_paraxial_why === "cost" ? t("not verified against the exact solution") : t("paraxially inaccurate (> {p:d} %)", { p: 1 });
      g.font = "11px system-ui";
      const tw = g.measureText(lab).width;
      g.fillStyle = "rgba(0,0,0,0.6)"; g.fillRect(left + 2, top + mh - 38, tw + 6, 15);
      g.fillStyle = "#fff"; g.fillText(lab, left + 5, top + mh - 27);
      g.restore();
    }
    // flow lines
    if (opt.bohm && seg.bohm_z) {
      const nz = seg.bohm_z.length, M = seg.bohm_x.length / nz;
      g.strokeStyle = "rgba(120,220,255,0.55)"; g.lineWidth = 0.8;
      for (let m = 0; m < M; m++) {
        g.beginPath();
        for (let i = 0; i < nz; i += 3) {
          const z = seg.bohm_z[i], xx = seg.bohm_x[i * M + m];
          const w = Math.hypot(seg.map_half0, seg.map_theta * z);
          const X = uOf(z), Y = yOf(xx / w);
          if (i === 0) g.moveTo(X, Y); else g.lineTo(X, Y);
        }
        g.stroke();
      }
    }
    // source side: the source's dot and, under it along the left margin, its name (at the top-left it lay under the
    // view's caption: integrator's D8 screenshots, 2026-11-13)
    g.fillStyle = "#f08c00";
    g.beginPath(); g.arc(10, top + mh / 2, 4, 0, 2 * Math.PI); g.fill();
    g.save(); g.fillStyle = css("--muted"); g.font = "11px system-ui"; g.textAlign = "left";
    g.translate(5, top + mh / 2 + 10); g.rotate(Math.PI / 2);
    g.fillText(geo.L1 ? t("source, L₁ = {L:.4g} m", { L: geo.L1 }) : t("plane wave"), 0, 0, Math.max(20, mh / 2 - 14));
    g.restore();
    // slit plate at z0 (scale w0)
    g.fillStyle = css("--ink");
    const xs = geo.slits, a = geo.a;
    const edges = [];
    for (const c of xs) edges.push([c - a / 2, c + a / 2]);
    let yPrev = top;
    const plateX = left - 4;
    for (const [e1, e2] of edges.slice().reverse()) {
      const y1 = yOf(e2 / w0), y2 = yOf(e1 / w0);
      g.fillRect(plateX, yPrev, 4, Math.max(0, y1 - yPrev));
      yPrev = y2;
    }
    g.fillRect(plateX, yPrev, 4, Math.max(0, bot - yPrev));
    // elements, detector, microscope, flux
    const app = seg.app || {};
    g.font = "11px system-ui";
    if (SCR && xs.length <= 4) {  // the slits' numbers (the captions and the elements name them), right of the plate
      g.save(); g.font = "bold 12px system-ui"; g.fillStyle = "#fff"; g.textAlign = "left";
      xs.forEach((c, j) => g.fillText(String(j + 1), plateX + 7, yOf(c / w0) + 4));
      g.restore();
    }
    const els = [[app.el1, app.el1_angle], [app.el2, app.el2_angle]];
    els.forEach(([k, ang], j) => {
      if (!k || k === "none" || j >= xs.length) return;
      const Y = yOf(xs[j] / w0);
      g.fillStyle = "#ae3ec9"; g.fillRect(plateX - 10, Y - 6, 6, 12);
      g.fillText(t("{elem} {a:g}°", { elem: ELEM[k] ? t(ELEM[k]) : k, a: ang }), 18, Y + 4);
    });
    if (app.wp_mode === "qubit") {
      const Y = yOf(xs[app.wp_slit - 1] / w0);
      g.strokeStyle = "#e8590c"; g.lineWidth = 2; g.beginPath(); g.arc(plateX - 16, Y, 6, 0, 2 * Math.PI); g.stroke();
      g.fillStyle = "#e8590c"; g.fillText(t("detector θ = {th:g}°", { th: app.wp_theta }), 18, Y - 9);
    }
    if (app.wp_mode === "microscope") {
      g.strokeStyle = "#2b8a3e"; g.lineWidth = 1.5; g.beginPath();
      for (let k = 0; k <= 40; k++) { const Y = top + mh * k / 40; g.lineTo(plateX - 18 + 4 * Math.sin(k * 1.3), Y); }
      g.stroke(); g.fillStyle = "#2b8a3e"; g.fillText(t("probe λ = {lam:.3g} nm", { lam: app.mic_lambda_nm }), 18, bot - 4);
    }
    if (app.ab_flux && xs.length >= 2) {
      const Y = yOf((xs[0] + xs[1]) / 2 / w0); g.fillStyle = "#1c7ed6"; g.fillText("⊗ Φ = " + fmt(app.ab_flux, ".4g") + " h/e", plateX - 60, Y + 4);
    }
    if (app.analyzer === "on") { g.fillStyle = "#ae3ec9"; g.fillRect(W - 14, top, 4, mh); g.fillText(t("analyser {a:g}°", { a: app.analyzer_angle }), W - 120, top - 4); }
    // screen
    g.fillStyle = css("--ink"); g.fillRect(W - 8, top, 3, mh);
    // particles in flight
    const L1 = geo.L1 || 0;
    let nfl = 0;
    const fl = flightOf(frame);
    for (let q = 0; q + 1 < fl.length; q += 2) {
      const te = fl[q], v = fl[q + 1];  // each particle flies at its own group velocity
      if (te > tw) continue;
      const z = v * (tw - te) - L1;
      if (z > zL) continue;
      nfl++;
      g.fillStyle = "rgba(255,255,255,0.75)";
      if (z < z0) {
        const X = L1 ? 10 + (left - 30) * Math.min(1, (z + L1) / L1) : left - 10;
        g.beginPath(); g.arc(X, top + mh / 2, 3, 0, 2 * Math.PI); g.fill();
      } else { g.fillRect(uOf(z) - 1, top, 2.5, mh); }
    }
    // z axis ticks (log)
    g.fillStyle = css("--muted");
    for (let e = Math.ceil(Math.log10(z0)); e <= Math.floor(Math.log10(zL)); e++) {
      const z = 10 ** e, X = uOf(z);
      g.fillRect(X, bot, 1, 4); g.fillText(lenFmt(z), X + 2, bot + 14);
    }
    if (SCR) {  // the screens: what is drawn, in a few words, and the set-up of this segment
      const txt = [t("View from above: the computed wave behind the slits, brighter where a hit is more probable."),
        t("The distance is on a log scale and the width is rescaled at each distance, so the beams seem to bend."),
        t("Set-up: {app}", { app: seg.apparatus })];
      if (ovApp.dataset.txt !== txt.join("|")) {
        ovApp.dataset.txt = txt.join("|");
        ovApp.replaceChildren(txt[0] + " ", el("span", { class: "u32-wide" }, txt[1] + " "), txt[2]);
      }
      return;
    }
    ovApp.textContent = t("View from above: the wave behind the slits (|ψ|², normalised in each cross-section), z on a log scale from 2a to the screen; x relative to the beam's width. In flight: {n:d}. Segment {s:d}: {app}",
      { n: nfl, s: seg.seg, app: seg.apparatus }) + (seg.vector ? " " + t("The screen is a perfect conductor; the map and the flow lines are the scalar model (Kirchhoff, paraxial).") : "");
  }

  // --- screen -------------------------------------------------------------------------------------------
  function drawScreen(frame, tw) {
    const cv = cvScr, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(tw);
    const SU = (seg && seg.setup) || H;
    const half = SU.geometry.half;
    // the screens: the dots start under the overlay's line, and few hits are drawn larger (one photon is one visible dot)
    const dotsTop = SCR ? (W < 420 ? 40 : 26) : 0;
    const dotsH = Math.round(Hh * 0.55) - dotsTop, histTop = dotsTop + dotsH + 10;
    let histH = Hh - histTop - 20;
    const xOf = (x) => 8 + (W - 16) * (x + half) / (2 * half);
    const n = shownUpTo(tw);
    const big = SCR && ((frame && frame.n_seg) || 0) < 400;
    // dots: incremental offscreen drawing
    const key = [opt.filter, opt.phase0, opt.phaseW, opt.segOnly, seg ? seg.seg : -1, W, dotsH, document.documentElement.dataset.theme, big].join("|");
    if (!dotsState || dotsState.key !== key || n < dotsState.n) {
      offDots.width = W * 2; offDots.height = dotsH * 2;
      dotsState = { key, n: 0, last: -1 };
    }
    const og = offDots.getContext("2d");
    const ds = big ? 5 : 2;
    for (let i = dotsState.n; i < n; i++) {
      if (!pass(i, seg)) continue;
      og.fillStyle = dotColor(i);
      og.fillRect(2 * xOf(det.x[i]) - ds / 2, 2 * (dotsH / 2 + det.y[i] * (dotsH - 10)) - ds / 2, ds, ds);
      dotsState.last = i;
    }
    dotsState.n = n;
    g.drawImage(offDots, 0, dotsTop, W, dotsH);
    if (big && dotsState.last >= 0) {  // the latest hit ringed: where the last photon landed
      const i = dotsState.last;
      g.strokeStyle = css("--warn") || "#e8590c"; g.lineWidth = 1.5;
      g.beginPath(); g.arc(xOf(det.x[i]), dotsTop + dotsH / 2 + det.y[i] * (dotsH - 10), 7, 0, 2 * Math.PI); g.stroke();
    }
    // histogram: incremental like the dots (full recount only when the selection changes or time goes back)
    const nb = SU.geometry.nbins;
    const hkey = [opt.filter, opt.phase0, opt.phaseW, opt.segOnly, seg ? seg.seg : -1].join("|");
    if (!histState || histState.key !== hkey || n < histState.n) histState = { key: hkey, n: 0, counts: new Float64Array(nb), tot: 0 };
    for (let i = histState.n; i < n; i++) {
      if (!pass(i, seg)) continue;
      const b = Math.min(nb - 1, Math.max(0, Math.floor((det.x[i] + half) / (2 * half) * nb)));
      histState.counts[b]++; histState.tot++;
    }
    histState.n = n;
    const counts = histState.counts, tot = histState.tot;
    let cmax = 1; for (const c of counts) cmax = Math.max(cmax, c);
    // expected curves for the shown subset: the run's own binned curves (server), scaled to the shown count
    let expC = null, clC = null, curveNote = "", othC = null, teC = null, tmC = null, diffC = null;
    const vec = seg && seg.vector;
    if ((opt.expect || opt.cl) && seg && tot > 0) {
      const name = { all: ["all", "cl"], r0: ["r0", "cl0"], r1: ["r1", "cl1"], noscat: ["noscat", null] }[opt.filter];
      if (!opt.segOnly) curveNote = " " + t("The expected curves are shown only for the current segment.");
      else if (!name) curveNote = " " + t("No expectation is computed for this selection.");
      else {
        const pick = (nm) => (nm && seg.curves && seg.curves[nm]) ? Float64Array.from(seg.curves[nm]) : null;
        expC = pick(name[0]); clC = pick(name[1]);
        if (vec && opt.filter === "all") {  // the other model, the polarisations and the difference: one common scale
          othC = pick(vec.hits === "vector" ? "kir" : "vec"); teC = pick("vTE"); tmC = pick("vTM"); diffC = pick("diff");
        }
        let s2 = 0; if (expC) for (const v of expC) s2 += v;
        const f = tot / Math.max(s2, 1e-300);
        for (const arr of [expC, othC, teC, tmC, diffC]) if (arr) for (let i = 0; i < nb; i++) arr[i] *= f;
        if (clC) { let s3 = 0; for (const v of clC) s3 += v; for (let i = 0; i < nb; i++) clC[i] *= tot / Math.max(s3, 1e-300); }
        if (!opt.expect) expC = othC = teC = tmC = diffC = null;
        if (!opt.cl) clC = null;
        for (const arr of [expC, clC, othC, teC, tmC]) if (arr) for (const v of arr) cmax = Math.max(cmax, v);
      }
    }
    // earlier points (Explore's traces): their own expectation, as expected counts per bin of this histogram, for the
    // number of hits each had at its time (equal counts at equal times: the cursor is kept)
    const bw = (W - 16) / nb;
    const tr = SCR && opt.expect ? traceCurves(half, nb) : [];
    for (const c of tr) for (const v of c.y) cmax = Math.max(cmax, v);
    const fullH = histH;
    if (diffC) histH = Math.round(fullH * 0.72);
    const yOfC = (c) => histTop + histH * (1 - c / cmax);
    g.fillStyle = css("--accent"); g.globalAlpha = 0.55;
    for (let b = 0; b < nb; b++) if (counts[b]) g.fillRect(8 + b * bw, yOfC(counts[b]), Math.max(bw, 1), histTop + histH - yOfC(counts[b]));
    g.globalAlpha = 1;
    const curve = (arr, col, dash) => {
      if (!arr) return;
      g.strokeStyle = col; g.lineWidth = 1.6; g.setLineDash(dash || []);
      g.beginPath(); for (let b = 0; b < nb; b++) { const X2 = 8 + (b + 0.5) * bw, Y = yOfC(arr[b]); if (b) g.lineTo(X2, Y); else g.moveTo(X2, Y); }
      g.stroke(); g.setLineDash([]);
    };
    g.save(); g.beginPath(); g.rect(8, histTop, W - 16, histH); g.clip();
    for (const c of tr) {
      g.globalAlpha = c.alpha; g.strokeStyle = c.colour; g.lineWidth = 1.6; g.setLineDash([6, 3]);
      g.beginPath(); c.x.forEach((x, k) => { const X2 = xOf(x), Y = yOfC(c.y[k]); if (k) g.lineTo(X2, Y); else g.moveTo(X2, Y); });
      g.stroke();
    }
    g.restore(); g.globalAlpha = 1; g.setLineDash([]);
    if (!SCR) curve(clC, "#868e96", [5, 4]);
    curve(teC, "#2f9e44", [2, 3]);
    curve(tmC, "#ae3ec9", [2, 3]);
    curve(othC, "#1c7ed6");
    curve(expC, "#e8590c");
    if (SCR) curve(clC, "#5c636a", [5, 4]);  // the screens: over the orange, visible where the two coincide (no interference)
    g.strokeStyle = css("--line"); g.strokeRect(8, histTop, W - 16, histH);
    if (tr.length) {  // the traces' legend: each earlier point's set-up, from its own header
      g.save(); g.font = "11px system-ui"; g.textAlign = "left";
      tr.forEach((c, k) => {
        const y = histTop + 13 + 13 * k;
        g.globalAlpha = Math.min(1, c.alpha + 0.3); g.strokeStyle = c.colour; g.setLineDash([6, 3]); g.lineWidth = 1.6;
        g.beginPath(); g.moveTo(14, y - 4); g.lineTo(32, y - 4); g.stroke();
        g.fillStyle = css("--muted"); g.fillText(c.label, 36, y);
      });
      g.restore(); g.setLineDash([]);
    }
    if (diffC) {  // the difference vector − scalar in a strip of its own (symmetric scale)
      const top = histTop + histH + 6, sh = fullH - histH - 6, mid = top + sh / 2;
      let dm = 1e-300; for (const v of diffC) dm = Math.max(dm, Math.abs(v));
      g.strokeStyle = css("--line"); g.strokeRect(8, top, W - 16, sh);
      g.setLineDash([3, 3]); g.beginPath(); g.moveTo(8, mid); g.lineTo(W - 8, mid); g.stroke(); g.setLineDash([]);
      g.strokeStyle = "#c92a2a"; g.lineWidth = 1.4; g.beginPath();
      for (let b = 0; b < nb; b++) { const X2 = 8 + (b + 0.5) * bw, Y = mid - (sh / 2 - 2) * diffC[b] / dm; if (b) g.lineTo(X2, Y); else g.moveTo(X2, Y); }
      g.stroke();
      g.fillStyle = css("--muted"); g.font = "10px system-ui";
      g.fillText(t("difference vector − scalar (±{d:.3g} counts)", { d: dm }), 12, top + 11);
    }
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    g.fillText(lenFmt(-half), 8, Hh - 5); g.fillText("0", W / 2 - 3, Hh - 5); g.fillText(lenFmt(half), W - 60, Hh - 5);
    if (SCR) {  // the screens: what the dots are; the curves' legend in the histogram's corner, only those shown
      ovScr.textContent = t("The screen: each dot is one hit. Below: their histogram.");
      const leg = [expC ? [t("expectation"), "#e8590c", []] : null, clC ? [t("without interference"), "#868e96", [5, 4]] : null].filter(Boolean);
      g.save(); g.font = "11px system-ui"; g.textAlign = "right"; g.lineWidth = 1.6;
      leg.forEach(([lab, col, dash], k) => {
        const y = histTop + 13 + 13 * k;
        g.fillStyle = css("--muted"); g.fillText(lab, W - 36, y);
        g.strokeStyle = col; g.setLineDash(dash); g.beginPath(); g.moveTo(W - 32, y - 4); g.lineTo(W - 14, y - 4); g.stroke();
      });
      g.restore(); g.setLineDash([]);
      return;
    }
    const vecNote = !vec ? "" : vec.hits === "vector"
      ? " " + (vec.diff_note
        ? t("Conducting screen: the hits and the orange line are the vector solution (energy flux), the blue one the scalar Kirchhoff solution in the same units (with the same detector efficiency), the green and purple dots the TE and TM contributions; {note}.", { note: vec.diff_note })
        : t("Conducting screen: the hits and the orange line are the vector solution (energy flux), the blue one the scalar Kirchhoff solution in the same units (with the same detector efficiency), the green and purple dots the TE and TM contributions, the red one the difference vector − scalar."))
      : " " + t("Conducting screen, but the hits and the orange line are the scalar model ({why}); the blue one is only the shape of the vector solution for the same slits without elements and analyser, normalised to the same sum (their units differ; the difference is not shown).", { why: vec.why || "" });
    ovScr.textContent = t("Screen: {shown:d} counts shown (of {n:d} in all). Histogram; the orange line is the run's expectation (with the dark counts), the grey dashed one the sum of the slits without interference.", { shown: tot, n })
      + vecNote + curveNote;
  }

  // Explore's traces: each earlier point's own expectation (its segment's curve "all"), as expected counts per bin of
  // the histogram shown (its density × this bin's width, for the hits it had at its time), at its own screen positions
  function traceCurves(half, nb) {
    const out = [];
    for (const tr of traces) {
      const v = tr.W && tr.W.view;
      const d = v && v.expectation ? v.expectation() : null;
      if (!d || !d.n) continue;
      let s = 0; for (const c of d.curve) s += c;
      const k = d.n / Math.max(s, 1e-300) * (2 * half / nb) / (2 * d.half / d.curve.length);
      const x = Array.from(d.curve, (_, b) => -d.half + (b + 0.5) * 2 * d.half / d.curve.length);
      out.push({ x, y: Array.from(d.curve, (c) => c * k), alpha: Math.max(0.35, tr.alpha ?? 0.4), colour: d.colour || "#868e96",
        label: t("λ {lam:.4g} nm, d {d:.4g} µm, a {a:.4g} µm", { lam: d.lam * 1e9, d: d.d * 1e6, a: d.a * 1e6 }) });
    }
    return out;
  }
  // what a trace needs of this view (an instance fed an earlier point up to its time): the expectation of its latest
  // segment, its screen's half-width, the hits of that segment fed so far, its set-up
  function expectation() {
    const seg = segs[segs.length - 1];
    if (!seg || !seg.curves || !seg.curves.all || !det) return null;
    let n = 0;
    for (let i = 0; i < det.n; i++) if (pass(i, seg)) n++;
    const G = (seg.setup || H), p = G.particle || {};
    return { curve: seg.curves.all, half: G.geometry.half, n, lam: p.lambda_m, d: G.geometry.d, a: G.geometry.a, colour: lightOf(G) };
  }

  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }

  function lenFmt(x) {
    const a = Math.abs(x);
    if (a >= 1) return t("{v:.3g} m", { v: x });
    if (a >= 1e-3) return t("{v:.3g} mm", { v: x * 1e3 });
    if (a >= 1e-6) return t("{v:.3g} µm", { v: x * 1e6 });
    if (a >= 1e-9) return t("{v:.3g} nm", { v: x * 1e9 });
    return t("{v:.3g} pm", { v: x * 1e12 });
  }

  // --- panels ---------------------------------------------------------------------------------------------
  function drawInfo() {
    const G = now(), p = G.particle;
    const rows = [[t("Particle"), t(p.label)], [t("Wavelength λ"), lenFmt(p.lambda_m)],
      [t("Energy"), p.mass_kg ? t("{e} eV (kinetic {k} eV)", { e: num(p.E_eV, 8), k: num(p.Ekin_eV, 6) }) : t("{e} eV", { e: num(p.E_eV, 8) })],
      [p.mass_kg ? t("de Broglie frequency E/h (with the rest energy)") : t("Frequency"), t("{f} Hz", { f: num(p.nu_Hz, 6) })],
      [t("Momentum"), t("{p} kg·m/s", { p: num(p.p, 6) })], [t("Speed"), t("{v} m/s ({b} c)", { v: num(p.v, 8), b: num(p.beta, 6) })],
      [t("Internal state"), p.internal === "pol" ? t("polarisation (2 states)") : p.internal === "spin" ? t("spin ½") : t("none")],
      [t("Slits"), t("{n:d} × {a}, period {d}", { n: G.geometry.n, a: lenFmt(G.geometry.a), d: lenFmt(G.geometry.d) })],
      [t("To the screen"), lenFmt(G.geometry.L2)],
      [t("Flight to the screen"), time(G.t_flight, 6)], [t("Source rate"), t("{r} 1/s", { r: num(G.rate, 4) })]];
    infoBox.replaceChildren(...rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]));
  }
  function drawStats(frame) {
    const c = frame.counts || {};
    const rows = [[t("emitted"), c.emitted], [t("absorbed at the slits"), c.absorbed_slits], [t("absorbed by the analyser"), c.absorbed_an],
      [t("past the screen"), c.missed], [t("not registered"), c.undetected], [t("registered"), c.detected], [t("dark counts"), c.dark],
      [t("scattered a photon"), c.scattered], [t("GRW hits"), c.grw_hits], [t("transitional (slits and screen in different segments)"), c.mixed],
      [t("in the current segment"), frame.n_seg]];
    const items = [el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, fmt(v ?? 0, "d"))]))];
    if (c.reflected) items[0].append(el("span", {}, t("reflected by the conducting screen")), el("span", { class: "mono" }, fmt(c.reflected, "d")));
    if (frame.coh && frame.coh.why) {
      items.push(el("p", {}, t("The degree of coherence of the slits |γ₁₂| is undefined: {why}", { why: frame.coh.why })));
    } else if (frame.coh) {
      const h = frame.coh;
      items.push(el("p", {}, t("Degree of coherence of the slits |γ₁₂|: from the histogram") + " ",
        el("b", { class: "mono" }, h.hist === null ? "—" : num(h.hist, 4)), h.err ? ` ± ${num(h.err, 2)}` : "",
        "; " + t("the run's expectation") + " ", el("b", { class: "mono" }, h.expected === null ? "—" : num(h.expected, 4)),
        el("div", { class: "help" }, t("A fit of the histogram to the computed slit functions |A₁|², |A₂|², A₁A₂*: 1 is full interference, 0 none."))));
    }
    if (frame.chi2 && frame.chi2.x2 !== null) {
      const ch = frame.chi2;
      items.push(el("p", {}, t("Agreement of the histogram with the expectation: χ² = {x2:.4g} for {dof:d} degrees of freedom, p = {p:.3g}", { x2: ch.x2, dof: ch.dof, p: ch.p }),
        el("span", { class: ch.p > 1e-3 ? "st-ok" : "st-bad" }, ch.p > 1e-3 ? " ✓" : " ✗")));
    }
    if (frame.lag) items.push(el("p", { class: "st-bad" }, t("The computation cannot keep up with the chosen speed: the world runs slower.")));
    statBox.replaceChildren(...items);
  }
  function drawVector(tw) {
    const seg = segAt(tw), v = seg && seg.vector;
    if (!v) { vecBox.replaceChildren(el("p", { class: "help" }, t("Scalar model: the field in a slit equals the incident one (Kirchhoff boundary conditions). For photons with a plane monochromatic wave and slits no wider than {w:.1f} λ (k·a ≤ {ka:d}) a perfect conductor (vector diffraction) can be chosen in the settings “Slits and screen”.", { w: 130 / (2 * Math.PI), ka: 130 }))); return; }
    const rows = [[t("Screen"), v.t === 0 ? t("perfect conductor, infinitely thin") : t("perfect conductor, {t} thick", { t: lenFmt(v.t) })],
      [t("Hits"), v.hits === "vector" ? t("from the vector solution (energy flux)") : t("from the scalar model")],
      [t("Transmission per slit width T_TE (E along the slits)"), num(v.T_TE, 5)], [t("T_TM (H along the slits)"), num(v.T_TM, 5)],
      [t("T by Kirchhoff (scalar)"), num(v.T_K, 5)], [t("Polarisation weights H(TM) / V(TE)"), `${num(v.wH, 3)} / ${num(v.wV, 3)}`],
      [t("Power balance TE / TM (rel.)"), `${num(v.rel_TE, 2)} / ${num(v.rel_TM, 2)}`],
      [t("Estimated error of the method TE / TM (T and the flux on the screen)"), `${num(v.err_TE, 2)} / ${num(v.err_TM, 2)}`],
      [t("Method"), t("{method}, {n:d} modes per slit", { method: v.method === "edge" ? t("a basis with edge conditions") : t("waveguide modes"), n: v.modes })]];
    if (v.hits === "vector") rows.push([v.n === 1 ? t("Share of transmitted photons (strip n·d = {w}; one slit: a nominal width, the period d)", { w: lenFmt(v.W) })
      : t("Share of transmitted photons (strip n·d = {w})", { w: lenFmt(v.W) }), num(v.p_trans, 4)]);
    const items = [el("div", { class: "kv" }, rows.flatMap(([k, x]) => [el("span", {}, k), el("span", { class: "mono" }, x)]))];
    if (v.hits !== "vector") items.push(el("p", { class: "help" }, t("Hits come from the scalar model: {why}.", { why: v.why || "" })));
    vecBox.replaceChildren(...items);
  }
  function drawStories(frame, tw) {
    const st = stories.filter((s) => s.t_det <= tw).slice(-10);
    storyBox.replaceChildren(...st.slice().reverse().map((s) => el("div", { class: "ev" },
      el("b", {}, `#${s.id}`), " " + t("emitted at {t}; λ = {lam}", { t: time(s.t_emit, 6), lam: lenFmt(s.lambda) }),
      s.x_src ? "; " + t("source point {x}", { x: lenFmt(s.x_src) }) : "",
      "; " + t("state {s}", { s: s.state }),
      s.scattered ? "; " + (s.recorded ? t("scattered a photon (phase Δk·d = {ph:.3g} rad, the photon recorded)", { ph: s.kick_phase })
        : t("scattered a photon (phase Δk·d = {ph:.3g} rad)", { ph: s.kick_phase })) : "",
      s.grw_hits ? "; " + t("GRW hits: {n:d}", { n: s.grw_hits }) : "",
      s.overlap12 !== null && s.overlap12 !== undefined ? "; " + t("overlap of the marks |⟨m₂|m₁⟩| = {o:.4g}", { o: s.overlap12 }) : "",
      el("div", {}, "→ " + t(s.fate) + ` (${time(s.t_det, 6)})`))));
  }

  // the screens' readout line (design §6.3): the hits of the current segment, the agreement of their histogram with the
  // run's expectation (χ²/dof, p) and the degree of coherence fitted to it, all computed by the run for this frame
  function drawReadouts(frame) {
    const items = [el("span", { "data-r": "hits" }, t("Hits in this segment:") + " ", el("b", { class: "mono" }, fmt(frame.n_seg ?? 0, "d")))];
    const ch = frame.chi2;
    items.push(ch && ch.x2 !== null && ch.dof
      ? el("span", { "data-r": "chi2", title: t("Agreement of the histogram with the expectation: χ² = {x2:.4g} for {dof:d} degrees of freedom, p = {p:.3g}", { x2: ch.x2, dof: ch.dof, p: ch.p }) },
        "χ²/dof ", el("b", { class: "mono" }, fmt(ch.x2 / ch.dof, ".3g")), ", p ", el("b", { class: "mono" }, fmt(ch.p, ".2g")),
        el("span", { class: ch.p > 1e-3 ? "st-ok" : "st-bad" }, ch.p > 1e-3 ? " ✓" : " ✗"))
      : el("span", { "data-r": "chi2", class: "muted" }, t("χ²: from {n:d} hits on", { n: 50 })));
    const c = frame.coh;
    if (c && !c.why && c.hist !== null && c.hist !== undefined)
      items.push(el("span", { "data-r": "coh", title: t("A fit of the histogram to the computed slit functions |A₁|², |A₂|², A₁A₂*: 1 is full interference, 0 none.") },
        "|γ₁₂| ", el("b", { class: "mono" }, fmt(c.hist, ".3f")), c.err ? ` ± ${fmt(c.err, ".3f")}` : "",
        c.expected !== null && c.expected !== undefined ? " " + t("(the run's expectation {g})", { g: fmt(c.expected, ".3f") }) : ""));
    readBox.replaceChildren(...items);
  }

  return {
    center, rightPanels,
    // the screens' contract (design §2.4)
    quantSafe: QUANT_SAFE,
    overlays: OVERLAYS.map((o) => ({ ...o, default: ovOn[o.id], label: t(o.label) })),  // i18n-msgids: "expectation" "without interference" "wave" "flow lines" "log scale of the map"
    setOverlay(id, on) {
      if (!(id in OPT_OF)) return;
      ovOn[id] = !!on; opt[OPT_OF[id]] = !!on; full();
    },
    setTraces(list) { traces = list || []; ctx.requestRender(); },
    expectation,
    help: () => el("div", {},
      el("h4", {}, t("What is on the screen")),
      el("p", {}, t("Left: the set-up from above: the slits, the elements at the slits, the which-path detector, the microscope's probe; behind the slits the computed wave of this segment (|ψ|² by cross-sections), white bars are particles in flight (their wave fills the whole cross-section), light-blue lines are flow lines: for a pure state without decoherence de Broglie–Bohm trajectories (for a photon, lines of energy flow), with decoherence lines of the ensemble's averaged current, with GRW not shown. The map is the expected wave of the run's ensemble (with decoherence).")),
      el("p", {}, t("Right: the screen, each dot one registered particle; below it the histogram. The orange curve is this run's expectation (the mean over its own particles), the grey one without interference. Sorting by the detector's reading or by the direction of the scattered photon shows how interference comes back in the subsets (the eraser).")),
      el("p", {}, t("The observer does not switch interference off by a rule: each particle carries marks away from the slits (polarisation, spin, the detector's state, the photon's recoil), and the pattern is computed by the Born rule with their overlap."))),
    reset() { H = null; X = null; segs = []; stories = []; det = newCols(); dotsState = null; histState = null; mapCache = null; },
    // key frames (player.js): segments and detections only grow (lengths); the stories are capped, so they are copied
    snapshot() { return { segs: segs.length, det: det.n, stories: stories.slice() }; },
    restore(k) {
      segs.length = k.segs; det.n = k.det; stories = k.stories.slice();
      dotsState = null; histState = null; mapCache = null;
      const last = segs[segs.length - 1];
      approxBox.replaceChildren(...((last && last.approx) || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• ", a)));
      const set = [...segs].reverse().find((g) => g.setup);
      if (set) { ctx.setScene && ctx.setScene(set.setup.title); }
      drawInfo();
    },
    onHeader(meta, blobs) { H = meta; X = blobs.x; drawInfo(); },
    onMessage(meta, blobs) {
      if (meta.type === "segment") {
        const curves = {};
        for (const nm of meta.curves || []) curves[nm] = blobs["c_" + nm];
        segs.push({ ...meta, curves, map: blobs.map, map_z: blobs.map_z, map_w: blobs.map_w,
                    bohm_z: blobs.bohm_z, bohm_x: blobs.bohm_x });
        approxBox.replaceChildren(...(meta.approx || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• ", a)));
        dotsState = null; histState = null;
        if (meta.setup) { ctx.setScene && ctx.setScene(meta.setup.title); drawInfo(); }
      } else if (meta.type === "detections") {
        push(blobs);
      } else if (meta.type === "stories") {
        for (const st of meta.stories) stories.push(st);
        if (stories.length > 2000) stories.splice(0, stories.length - 2000);
      }
    },
    render(frame, tw, blobs) {
      if (!H) return;
      curBlobs = blobs || {};
      lastFrame = frame;
      drawApparatus(frame, tw);
      drawScreen(frame, tw);
      drawStats(frame);
      if (SCR) drawReadouts(frame);
      drawVector(tw);
      drawStories(frame, tw);
    },
  };
}
