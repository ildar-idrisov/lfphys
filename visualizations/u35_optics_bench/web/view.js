// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u35 view: the optical bench. The bench (left): the structure to scale in depth with its materials, the beams at the
// angles the run computed by Snell's law, single photons under way (orange s, blue p, purple linear at ψ, grey
// unpolarised: an unpolarised photon carries no s or p label), the analysers (polarising beam splitters with a detector
// on each port) and the detectors with their counts, each beam's polarisation ellipse from its density matrix, the run's
// |E|² of the source's light through the structure (a strip on the right) and the counters against the run's computed
// fractions (bars along the bottom). The curves (right): the run's R(θ), T(θ) for s and p, R(λ), T(λ) at the angle (each
// wavelength with its materials' own indices), and an analyser's pass fraction against its angle for the arm's light.
// Everything drawn comes from the run: segments (curves, field, angles, the beams' states), clicks (detections with
// their times, dark counts and absorptions) and frames (photons under way as the viewer may know them, the counts).
// The view computes no physics.
//
// The screens (design lfphys/sources/explore_EX2_2026-11-18_design.md §1.3, §3.7): with ctx.screen "watch", "explore" or
// "lab" the view is the clean one — no quick set-up bar; the two pictures side by side (≥ 1000 px), Watch with a fixed
// band under them for the caption (it never covers what it describes, and the pictures keep one scale for the whole
// story); below 1000 px the bench with its counters on top and the curves folded under it. Its right panels («Set-up of
// this segment», «Photons and detectors», «Approximations») fold into «How we know this is right» (demo.js). Lab work
// draws what Explore draws (nothing hidden). Each canvas exposes what it drew where (canvas.__layout: the labels' boxes
// and the marks they describe) for tests/u35_screens.mjs.
import { fmt, t } from "/static/js/i18n.js";
import { css, el, fresh2d, num, panel, time } from "/static/js/ui.js";

// what the view accepts quantised (registry.view_declarations reads this literal): the drawn curves, the depth grid and
// |E|², the clicks' times (flashes) and the photons in flight; never a measurable
export const QUANT_SAFE = { "segment.th": "u16", "segment.Rs": "u16", "segment.Ts": "u16", "segment.As": "u16",
  "segment.Rp": "u16", "segment.Tp": "u16", "segment.Ap": "u16", "segment.Rc": "u16", "segment.Tc": "u16", "segment.Ac": "u16",
  "segment.lam": "u16", "segment.lRs": "u16", "segment.lTs": "u16", "segment.lAs": "u16", "segment.lRp": "u16",
  "segment.lTp": "u16", "segment.lAp": "u16", "segment.lRc": "u16", "segment.lTc": "u16", "segment.lAc": "u16",
  "segment.z": "u16", "segment.E2": "u16", "clicks.t": "u16", "frame.fl": "u16" };
// the overlays it can toggle on the screens (registry.view_declarations reads the ids); defaults of Explore
export const OVERLAYS = [
  { id: "beams", label: "beams", default: true },
  { id: "photons", label: "photons in flight", default: true },
  { id: "field", label: "field |E|²", default: true },
  { id: "curves", label: "curves R(θ), T(θ), R(λ), T(λ)", default: true },
  { id: "ellipse", label: "polarisation ellipses", default: true },
];
const SCREENS = new Set(["watch", "explore", "lab"]);
const WATCH_BAND = 150;  // px under the pictures in Watch on a wide screen before the story's captions are measured (D8)
const PHONE_BENCH = 280, PHONE_CURVES = 360;  // px below 1000 px: the bench on top, the curves folded under it

const S_COL = "#f76707", P_COL = "#1c7ed6", LIN_COL = "#9c36b5", UNP_COL = "#868e96", DARK_COL = "#495057", A_COL = "#c92a2a";
const POL_COLS = [S_COL, P_COL, LIN_COL, UNP_COL];
const polCol = (c) => (c === 9 ? DARK_COL : POL_COLS[c] || UNP_COL);

let STYLE = false;  // the layout, added once per page
function addStyle() {
  if (STYLE) return;
  STYLE = true;
  document.head.append(el("style", {}, `
.u35-c { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.u35-panes { display: grid; flex: 1; min-height: 0; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); }
.u35-panes > div { display: flex; flex-direction: column; min-height: 0; min-width: 0; }
.u35-bench { border-right: 1px solid var(--line); }
.u35-fold { display: none; }
.u35-fold > summary { cursor: pointer; min-height: 44px; display: flex; align-items: center; gap: 6px; padding: 0 10px;
  background: var(--panel); border-top: 1px solid var(--line); font-size: 14px; list-style: none; }
.u35-fold > summary::-webkit-details-marker { display: none; }
.u35-fold > summary::before { content: "▸"; }
.u35-fold[open] > summary::before { content: "▾"; }
.u35-c.u35-watch .u35-panes { margin-bottom: var(--u35-band, ${WATCH_BAND}px); }
@media (max-width: 999px) {
  .dm-stage:has(> .u35-c) { aspect-ratio: auto; max-height: none; }
  .dm-stage > div.u35-c.u35-on { aspect-ratio: auto; min-height: 0; flex: none; }
  .u35-c.u35-on .u35-panes { flex: none; grid-template-columns: minmax(0, 1fr); }
  .u35-c.u35-on .u35-bench { border-right: 0; height: ${PHONE_BENCH}px; }
  .u35-c.u35-on .u35-curves { display: none; }
  .u35-c.u35-on .u35-fold { display: block; }
  .u35-c.u35-on .u35-fold > .canvas-wrap { height: ${PHONE_CURVES}px; }
  .u35-c.u35-watch .u35-panes { margin-bottom: 0; }
  .dm-stage:has(> .u35-c) > .dm-readouts { position: static; border: 0; border-top: 1px solid var(--line); border-radius: 0;
    margin: 0; opacity: 1; font-size: 12.5px; line-height: 1.25; padding: 3px 10px; gap: 1px 8px; }
  .dm-stage:has(> .u35-c) > .dm-readouts .dm-ref { display: inline; margin-left: 6px; font-size: 11.5px; }
}
@media (max-width: 1000px) {
  .u35-c:not(.u35-on) .u35-panes { flex: 1 0 auto; grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(300px, 1fr) minmax(300px, 1fr); }
  .u35-c:not(.u35-on) .u35-bench { border-right: 0; border-bottom: 1px solid var(--line); }
}
/* (the five tabs, a dense grid's detents and the phone's time label: the player's demo.css) */`));
}

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
const lut = (v) => { const c = Math.min(255, Math.max(0, Math.round(v * 255))); return `rgb(${LUT[3 * c]},${LUT[3 * c + 1]},${LUT[3 * c + 2]})`; };

// approximate display colour of a wavelength (drawing only); null outside the visible range
function lamRGB(nm) {
  if (nm < 380 || nm > 780) return null;
  let r = 0, g = 0, b = 0;
  if (nm < 440) { r = (440 - nm) / 60; b = 1; }
  else if (nm < 490) { g = (nm - 440) / 50; b = 1; }
  else if (nm < 510) { g = 1; b = (510 - nm) / 20; }
  else if (nm < 580) { r = (nm - 510) / 70; g = 1; }
  else if (nm < 645) { r = 1; g = (645 - nm) / 65; }
  else r = 1;
  const f = nm < 420 ? 0.3 + 0.7 * (nm - 380) / 40 : nm > 700 ? 0.3 + 0.7 * (780 - nm) / 80 : 1;
  const q = (x) => Math.round(255 * Math.pow(x * f, 0.8));
  return `rgb(${q(r)},${q(g)},${q(b)})`;
}
const fmtN = (n) => (n[1] ? `${num(n[0], 4)} + ${num(n[1], 4)}i` : num(n[0], 5));
// the source's polarisation in words: s, p, linear at ψ, unpolarised
const polText = (su) => (su.pol === "unpol" ? t("unpolarised") : su.pol === "lin" ? t("linear, ψ = {psi:.4g}°", { psi: su.psi }) : su.pol);
const sceneText = (su) => t("{label}; λ = {lam:.4g} nm, θ = {th:.4g}°, {pol}", { label: su.label, lam: su.lam, th: su.theta, pol: polText(su) });
const MAT_SHORT = { air: "air", schott_n_bk7: "N-BK7", schott_n_f2: "N-F2", schott_n_sf11: "N-SF11", sio2_malitson: "SiO₂",
  mgf2_dodge_o: "MgF₂", mgf2_film_rodriguez: "MgF₂", sio2_film_gao: "SiO₂", ta2o5_film_gao: "Ta₂O₅", au_johnson_christy: "Au",
  ag_johnson_christy: "Ag", al_rakic: "Al" };
const medName = (id, n) => (id === "air" ? t("air") : id === "model" ? t("model medium") : MAT_SHORT[id] || id) + ` n = ${num(n, 5)}`;

export function createView(ctx) {
  let H = null, segs = [], clk = null, flashes = [], lastT = null, inFlight = [0, 0];
  let story = null, band = 0;  // Watch: the recording's captions (setStory) and the band they need under the pictures
  const SCR = SCREENS.has(ctx.screen);
  const on = Object.fromEntries(OVERLAYS.map((o) => [o.id, o.default]));
  let LAY = null;  // the layout being recorded for the canvas drawn now (canvas.__layout)

  // --- DOM --------------------------------------------------------------------------------------------
  addStyle();
  const cvGeo = el("canvas", { "data-u35": "bench" }), cvCur = el("canvas", { "data-u35": "curves" });
  const btnFly = el("button", { title: t("A speed at which the flight of one photon is seen (an arm in ≈ {s} s)", { s: 1.2 }) },
    t("▷ photon flight"));
  const btnStat = el("button", { title: t("A speed for collecting statistics (≈ {n:d} photons per second)", { n: 2000 }) },
    t("▷▷ collect statistics"));
  // the curves: their own pane on a wide screen; on a phone's screens folded under the bench (design §3.7)
  const curvesWrap = el("div", { class: "canvas-wrap" }, cvCur);
  const curvesBox = el("div", { class: "u35-curves" }, curvesWrap);
  const fold = el("details", { class: "u35-fold", "data-u35": "fold" },
    el("summary", {}, t("Curves R(θ), T(θ), R(λ), T(λ) and the analyser")));
  const narrowMQ = matchMedia("(max-width: 999px)");
  const placeCurves = () => {
    if (SCR && narrowMQ.matches) { if (curvesWrap.parentNode !== fold) fold.append(curvesWrap); } else if (curvesWrap.parentNode !== curvesBox) curvesBox.append(curvesWrap);
    ctx.requestRender();
  };
  narrowMQ.addEventListener("change", placeCurves);
  fold.addEventListener("toggle", () => ctx.requestRender());
  const curvesShown = () => curvesWrap.parentNode === curvesBox || fold.open;
  const panes = el("div", { class: "u35-panes" }, el("div", { class: "u35-bench" }, el("div", { class: "canvas-wrap" }, cvGeo)),
    curvesBox, fold);
  placeCurves();
  let center;
  if (!SCR) {
    const quick = el("div", { class: "toolbar quick", title: t("Set-up: changes at once (the same as in the panel on the left)") },
      el("span", { class: "muted" }, t("Set-up:")),
      ctx.liveControl ? [ctx.liveControl("lam_nm", { label: t("λ, nm") }), ctx.liveControl("theta_deg", { label: "θ, °" }),
        ctx.liveControl("pol", { label: t("polarisation") }), ctx.liveControl("structure", { label: t("structure") })] : null,
      btnFly, btnStat);
    center = el("div", { class: "u35-c" }, quick, panes);
  } else center = el("div", { class: `u35-c u35-on u35-${ctx.screen}` }, panes);
  const infoBox = el("div", {}), statBox = el("div", {}), polBox = el("div", {}), approxBox = el("div", { class: "help" });
  const rightPanels = [panel(t("Set-up of this segment"), infoBox), panel(t("Photons and detectors"), statBox),
    panel(t("Polarisation of the beams"), polBox), panel(t("Approximations"), approxBox)];
  btnFly.onclick = () => { const s = now(); if (s) ctx.send("speed", { value: s.t_in / 1.2 }); };
  btnStat.onclick = () => { const s = now(); if (s) ctx.send("speed", { value: 2000 / s.rate }); };
  for (const cv of [cvGeo, cvCur]) new ResizeObserver(() => ctx.requestRender()).observe(cv);

  // --- data ---------------------------------------------------------------------------------------------
  function newClicks() { return { n: 0, cap: 0, t: null, det: null, pol: null }; }
  function pushClicks(b) {
    const m = b.t.length;
    if (!m) return;
    if (clk.n + m > clk.cap) {
      const cap = Math.max(1024, 2 * (clk.n + m));
      const grow = (old, T) => { const a = new T(cap); if (old) a.set(old.subarray(0, clk.n)); return a; };
      clk.t = grow(clk.t, Float64Array); clk.det = grow(clk.det, Uint8Array); clk.pol = grow(clk.pol, Uint8Array);
      clk.cap = cap;
    }
    clk.t.set(b.t, clk.n); clk.det.set(b.det, clk.n); clk.pol.set(b.pol, clk.n);
    clk.n += m;
  }
  function firstAfter(tw) {  // index of the first click with time > t (each step's clicks are in time order)
    let lo = 0, hi = clk.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (clk.t[m] <= tw) lo = m + 1; else hi = m; }
    return lo;
  }
  function segAt(tw) { let s = segs[0]; for (const g of segs) if (g.t <= tw) s = g; return s; }
  function now() { const s = segs[segs.length - 1]; return (s && s.setup) || H; }

  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    return fresh2d(cv.getContext("2d"), dpr);
  }
  // a label: kept inside its canvas (moved in, never cut), with a background, recorded in the canvas's layout
  // s: a text, or its alternatives from the longest to the shortest: the first that fits the canvas's width is drawn;
  // if none fits, the last is drawn in a smaller font (not below 8 px)
  function text(g, s, x, y, { color = css("--ink"), align = "left", bg = true, font = "11px system-ui", mark = null } = {}) {
    g.font = font;
    const Wc = LAY ? LAY.w : 1e9, Hc = LAY ? LAY.h : 1e9;
    const alts = Array.isArray(s) ? s : [s];
    s = alts.find((a) => g.measureText(a).width <= Wc - 6) ?? alts[alts.length - 1];
    let w = g.measureText(s).width, size = parseFloat(font.match(/(\d+(?:\.\d+)?)px/)[1]);
    if (w > Wc - 6) {
      size = Math.max(8, Math.floor(size * (Wc - 6) / w * 10) / 10);
      g.font = font.replace(/(\d+(?:\.\d+)?)px/, size + "px");
      w = g.measureText(s).width;
    }
    let x0 = align === "left" ? x : align === "right" ? x - w : x - w / 2;
    x0 = Math.max(2, Math.min(x0, Wc - w - 2));
    const yy = Math.max(size, Math.min(y, Hc - 3));
    if (bg) { g.fillStyle = hexA(css("--canvas"), 0.8); g.fillRect(x0 - 2, yy - size + 1, w + 4, size + 3); }
    g.textAlign = "left"; g.fillStyle = color; g.fillText(s, x0, yy);
    if (LAY) LAY.labels.push({ text: s, x: x0 - 2, y: yy - size + 1, w: w + 4, h: size + 3, mark });
    return { x: x0, w };
  }
  const markBox = (kind, x, y, w, h) => { if (LAY) LAY.marks.push({ kind, x, y, w, h }); };
  function hexA(c, a) {  // "#rrggbb" -> rgba with alpha (theme tokens are hex)
    const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(c.trim());
    return m ? `rgba(${parseInt(m[1], 16)},${parseInt(m[2], 16)},${parseInt(m[3], 16)},${a})` : c;
  }
  const medium = (n) => `rgba(110,165,235,${0.05 + 0.25 * Math.min(1, Math.max(0, (n - 1) / 2))})`;
  function layerFill(L) {
    if (L.role === "metal") return L.mat === "ag_johnson_christy" || L.mat === "al_rakic" ? "rgba(173,181,189,0.9)" : "rgba(242,183,5,0.85)";
    if (L.role === "gap") return medium(L.n[0]);
    if (L.role === "H") return "rgba(76,110,245,0.75)";
    if (L.role === "L") return "rgba(102,217,232,0.55)";
    return `rgba(116,192,252,${0.35 + 0.3 * Math.min(1, (L.n[0] - 1) / 2)})`;
  }
  const lerp = (a, b, f) => [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
  const clamp01 = (f) => Math.min(1, Math.max(0, f));

  // --- the bench ------------------------------------------------------------------------------------------------
  function drawGeometry(frame, tw, blobs) {
    const cv = cvGeo, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    LAY = { w: W, h: Hh, labels: [], marks: [] };
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(tw);
    if (!seg || !W || !Hh) { cv.__layout = LAY; LAY = null; return; }
    const su = seg.setup, ang = seg.angles, b = seg.b || {};
    const narrow = W < 600;
    const fieldOn = on.field && b.z && b.E2;
    const pw = fieldOn ? Math.max(76, Math.min(210, W * 0.24)) : 0, W1 = W - pw;
    // the counters' strip along the bottom: a row per fraction shown
    const c = frame.counts || {}, here = c.here || [true, false, true, false];
    const rows = 2 + (here[1] ? 1 : 0) + (here[3] ? 1 : 0) + (narrow ? 1 : 0);
    const rowH = narrow ? 15 : 17, ch = 20 + rows * rowH;
    const Hg = Hh - ch;  // the geometry's height
    const z = b.z, E2 = b.E2, nz = z ? z.length : 0;
    const zmin = nz ? z[0] : -1, zmax = nz ? z[nz - 1] : 1;
    const y0 = Hg * (narrow ? 0.47 : 0.40), y1 = Hg * (narrow ? 0.63 : 0.62), k = (y1 - y0) / (zmax - zmin);
    const yz = (zz) => y0 + (zz - zmin) * k;
    const none = su.kind === "none";
    const D = su.thickness, yTop = none ? (y0 + y1) / 2 : yz(0), yBot = none ? yTop : yz(D);
    // media and layers (to scale in depth)
    g.fillStyle = medium(su.n_in); g.fillRect(0, 0, W1, yTop);
    g.fillStyle = medium(su.n_out); g.fillRect(0, yBot, W1, Hg - yBot);
    let zc = 0;
    const thin = su.layers.some((L) => L.d * k < 12);
    for (const L of su.layers) {
      const ya = yz(zc), yb = yz(zc + L.d);
      g.fillStyle = layerFill(L); g.fillRect(0, ya, W1, Math.max(yb - ya, 0.6));
      zc += L.d;
    }
    if (!none) {
      g.strokeStyle = hexA(css("--ink"), 0.55); g.lineWidth = 1;
      zc = 0;
      for (const e of [0, ...su.layers.map((L) => (zc += L.d))]) { const y = yz(e); g.beginPath(); g.moveTo(0, y); g.lineTo(W1, y); g.stroke(); }
      markBox("structure", 0, yTop - 2, W1, yBot - yTop + 4);
    }
    const muted = css("--muted");
    const mIn = medName(su.med_in, su.n_in), mOut = medName(su.kind === "tir" && su.layers.length ? su.med_in : su.med_out, su.n_out);
    text(g, narrow ? mIn : t("incidence medium: {m}", { m: mIn }), 6, yTop - 8, { color: muted });
    if (!none) text(g, narrow ? mOut : t("{name:cap}: {m}", { name: su.out_name, m: mOut }), 6, Math.min(Hg - 4, yBot + 15), { color: muted });
    if (su.layers.length && !thin) {
      zc = 0;
      for (const L of su.layers) {
        const ya = yz(zc), yb = yz(zc + L.d); zc += L.d;
        text(g, t("{name}: {mat} n = {n}, d = {d:.4g} nm", { name: L.name, mat: L.mat ? MAT_SHORT[L.mat] || "" : "", n: fmtN(L.n), d: L.d }), W1 - 22, (ya + yb) / 2 + 4, { align: "right" });
      }
    } else if (su.layers.length) {
      const uniq = new Map();
      for (const L of su.layers) uniq.set(t(L.name), L);
      const parts = [...uniq.values()].map((L) => t("{name}: {mat} n = {n}, {d:.4g} nm", { name: L.name, mat: L.mat ? MAT_SHORT[L.mat] || "" : "", n: fmtN(L.n), d: L.d }));
      const head = su.kind === "bragg" ? `(H L)×${su.layers.length / 2}` : t(su.label);
      text(g, narrow ? head : `${head}; ${parts.join("; ")}`, W1 - 22, (yTop + yBot) / 2 + 4, { align: "right" });
    }
    // the scale: one wavelength in depth
    if (!none && nz) {
      const lamPx = su.lam * k;
      g.strokeStyle = css("--ink"); g.lineWidth = 2;
      const xs = W1 - 10, ys = Math.max(4, Math.min(yz(zmin) + 4, Hg - lamPx - 4));
      g.beginPath(); g.moveTo(xs, ys); g.lineTo(xs, ys + lamPx); g.moveTo(xs - 4, ys); g.lineTo(xs + 4, ys); g.moveTo(xs - 4, ys + lamPx); g.lineTo(xs + 4, ys + lamPx); g.stroke();
    }
    // beams: directions from the run (Snell's law of the engine, approximate ray picture)
    const m = 16, xc = W1 * (narrow ? 0.40 : 0.42), th = ang.theta * Math.PI / 180;
    const dx = Math.sin(th), dy = Math.cos(th);
    const reach = (x, y, ux, uy, xmin, xmax, ymin, ymax) => {
      let s = 1e5;
      if (ux > 1e-9) s = Math.min(s, (xmax - x) / ux); if (ux < -1e-9) s = Math.min(s, (xmin - x) / ux);
      if (uy > 1e-9) s = Math.min(s, (ymax - y) / uy); if (uy < -1e-9) s = Math.min(s, (ymin - y) / uy);
      return Math.max(s, 0);
    };
    const P = [xc, yTop];
    const top = 22;
    const sIn = reach(xc, yTop, -dx, -dy, m + 8, W1 - m, top + 8, Hg);
    const Sp = [xc - dx * sIn, yTop - dy * sIn];
    const normal = ang.theta < 3;  // the reflected beam goes back to the source: drawn shifted aside
    const off = normal ? 26 : 0;
    const PR = [xc + off, yTop];
    const sR = reach(PR[0], yTop, dx, -dy, m, W1 - m - 8, top + 8, Hg);
    const DR = [PR[0] + dx * sR, yTop - dy * sR];
    let x = xc; zc = 0;
    const inner = [];
    su.layers.forEach((L, j) => {
      const a = ang.layers[j], ya = yz(zc), yb = yz(zc + L.d); zc += L.d;
      if (a === null || a === undefined) { inner.push([x, ya, x, yb, true]); return; }
      let x1 = x + Math.tan(a * Math.PI / 180) * (yb - ya);
      x1 = Math.min(x1, W1 - m);
      inner.push([x, ya, x1, yb, false]); x = x1;
    });
    const Q = [x, yBot];
    const prop = ang.out !== null && ang.out !== undefined;
    const tho = (prop ? ang.out : ang.theta) * Math.PI / 180;
    const sT = reach(Q[0], yBot, Math.sin(tho), Math.cos(tho), m, W1 - m - 8, 0, Hg - m - 2);
    const DT = [Q[0] + Math.sin(tho) * sT, yBot + Math.cos(tho) * sT];
    const arms = seg.arms || { R: seg.cur.mix.R, T: seg.cur.mix.T }, beamC = lamRGB(su.lam) || "#adb5bd";
    const beam = (a, bb, alpha, w, dash) => {
      if (!on.beams) return;
      g.save(); g.globalAlpha = alpha; g.strokeStyle = beamC; g.lineWidth = w; g.setLineDash(dash || []);
      g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(bb[0], bb[1]); g.stroke(); g.restore();
    };
    const closed = su.shutter === "closed", dark = 0.08;  // the shutter closed: no light anywhere, every path faint
    beam(Sp, P, closed ? dark : 0.9, 4);
    if (!none) beam(PR, DR, closed ? dark : 0.12 + 0.88 * Math.sqrt(arms.R), 4);
    for (const [xa, ya, xb, yb, ev] of inner) beam([xa, ya], [xb, yb], closed ? dark : ev ? 0.5 : 0.8, ev ? 1.5 : 3, ev ? [2, 3] : null);
    if (prop) beam(Q, DT, closed ? dark : 0.12 + 0.88 * Math.sqrt(arms.T), 4);
    else if (on.beams && !closed) {  // evanescent: no transmitted beam; the field strip shows the decay computed by the run
      const gr = g.createLinearGradient(0, yBot, 0, yBot + 26);
      gr.addColorStop(0, hexA("#ffa94d", 0.55)); gr.addColorStop(1, hexA("#ffa94d", 0));
      g.fillStyle = gr; g.fillRect(Q[0] - 10, yBot, Math.min(150, W1 - Q[0] - 4), 26);
      text(g, t("evanescent wave"), Q[0] + 4, yBot + 38, { color: muted });
    }
    // the normal
    if (!none) {
      g.save(); g.setLineDash([4, 4]); g.strokeStyle = hexA(css("--ink"), 0.35); g.lineWidth = 1;
      g.beginPath(); g.moveTo(xc, Math.max(top, yTop - 70)); g.lineTo(xc, Math.min(Hg, yBot + 70)); g.stroke(); g.restore();
    }
    // the source (a shutter across it when closed)
    g.fillStyle = beamC; g.beginPath(); g.arc(Sp[0], Sp[1], 7, 0, 2 * Math.PI); g.fill();
    g.strokeStyle = css("--ink"); g.lineWidth = 1; g.stroke();
    markBox("source", Sp[0] - 8, Sp[1] - 8, 16, 16);
    if (closed) { g.save(); g.strokeStyle = css("--ink"); g.lineWidth = 4; const n = [-dy, dx]; const c0 = lerp(Sp, P, 0.12); g.beginPath(); g.moveTo(c0[0] - 10 * n[0], c0[1] + 10 * n[1]); g.lineTo(c0[0] + 10 * n[0], c0[1] - 10 * n[1]); g.stroke(); g.restore(); }
    const lamS = lamRGB(su.lam) ? "" : su.lam < 380 ? " (UV)" : " (IR)";
    const srcLab = closed ? t("source {lam:.4g} nm{band}: shutter closed", { lam: su.lam, band: lamS })
      : t("source {lam:.4g} nm{band}, {pol}", { lam: su.lam, band: lamS, pol: polText(su) });
    text(g, srcLab, Sp[0] + (normal ? -12 : 10), Math.max(12, Sp[1] - 10), { align: normal ? "right" : "left", mark: "source" });
    // the detectors, with an analyser where one stands: its pass port straight on, its reject port to the side
    const det = {};  // detector index -> its position (flashes)
    const armDraw = (arm, from, to, show, dim) => {
      const ana = su.ana && su.ana[arm];
      const u = [to[0] - from[0], to[1] - from[1]], L = Math.hypot(u[0], u[1]) || 1;
      const ux = u[0] / L, uy = u[1] / L;
      const i0 = arm === "R" ? 0 : 2;
      if (!ana) {
        det[i0] = to;
        detector(g, to, [ux, uy], arm === "R" ? t("R: {k}", { k: cnt(c, "Rp") }) : t("T: {k}", { k: cnt(c, "Tp") }), show, dim);
        return;
      }
      // a phone's bench: the ports' labels short (the counts are in the counters' strip too), no angle label
      const portLabel = (port) => (narrow ? `${arm}${port === "p" ? "+" : "−"} ${cnt(c, arm + port)}`
        : port === "p" ? t("{arm} pass: {k}", { arm, k: cnt(c, arm + "p") }) : t("{arm} reject: {k}", { arm, k: cnt(c, arm + "r") }));
      const C = lerp(from, to, 0.62);
      // the reject port leaves at a right angle, towards the middle of the bench
      let v = [-uy, ux];
      if ((C[0] + v[0] * 30 - W1 / 2) ** 2 + (C[1] + v[1] * 30 - Hg / 2) ** 2 > (C[0] - v[0] * 30 - W1 / 2) ** 2 + (C[1] - v[1] * 30 - Hg / 2) ** 2) v = [-v[0], -v[1]];
      const rj = [C[0] + v[0] * Math.min(56, 0.35 * L), C[1] + v[1] * Math.min(56, 0.35 * L)];
      if (on.beams) { g.save(); g.globalAlpha = 0.5; g.strokeStyle = beamC; g.lineWidth = 2; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(C[0], C[1]); g.lineTo(rj[0], rj[1]); g.stroke(); g.restore(); }
      // the cube with its axis (α drawn across the beam: the cube is seen from the side)
      g.save(); g.translate(C[0], C[1]); g.rotate(Math.atan2(uy, ux));
      g.fillStyle = hexA(css("--panel"), 0.95); g.strokeStyle = css("--ink"); g.lineWidth = 1.2;
      g.fillRect(-8, -8, 16, 16); g.strokeRect(-8, -8, 16, 16);
      g.beginPath(); g.moveTo(-8, 8); g.lineTo(8, -8); g.stroke();
      g.restore();
      markBox("analyser", C[0] - 9, C[1] - 9, 18, 18);
      if (!narrow) text(g, t("α = {a:.4g}°", { a: ana.alpha }) + (ana.dev === "real" ? " *" : ""), C[0] - 12 * (v[0] < 0 ? -1 : 1), C[1] - 12, { align: v[0] < 0 ? "left" : "right", color: muted });
      det[i0] = to; det[i0 + 1] = rj;
      detector(g, to, [ux, uy], portLabel("p"), show, dim);
      detector(g, rj, v, portLabel("r"), show, dim);
    };
    if (!none) armDraw("R", PR, DR, !normal || true, false);
    armDraw("T", prop ? Q : Q, DT, true, !prop);
    if (!prop && !su.ana.T && !narrow) text(g, t("no light goes here"), DT[0] - 14, DT[1] - 40, { align: "right", color: muted });
    // the polarisation ellipses of the beams (overlay "ellipse"): the source's state and each arm's, from the run
    if (on.ellipse) {
      const srcE = su.pol === "unpol" ? { degree: 0 } : { degree: 1, azimuth: su.psi, chi: 0, hand: 0 };
      glyph(g, lerp(Sp, P, 0.5), [dx, dy], srcE, polText(su));
      if (!none && seg.ell && seg.ell.R) glyph(g, lerp(PR, DR, su.ana && su.ana.R ? 0.32 : 0.5), [dx, -dy], seg.ell.R, null);
      if (prop && seg.ell && seg.ell.T) glyph(g, lerp(Q, DT, su.ana && su.ana.T ? 0.32 : 0.5), [Math.sin(tho), Math.cos(tho)], seg.ell.T, null);
    }
    // photons under way: on the way in a dot; after the structure the two packets with their weights
    const fl = (blobs && blobs.fl) || [];
    let nin = 0, nout = 0;
    for (let i = 0; i + 5 < fl.length; i += 6) {
      const col = polCol(Math.round(fl[i + 1]));
      if (fl[i] < 0.5) { nin++; if (on.photons) dot(g, lerp(Sp, P, clamp01(fl[i + 2])), col, 1); continue; }
      nout++;
      if (!on.photons) continue;
      if (fl[i + 3] > 0 && !none) dot(g, lerp(PR, DR, clamp01(fl[i + 2])), col, fl[i + 3]);
      if (fl[i + 5] > 0 && prop) dot(g, lerp(Q, DT, clamp01(fl[i + 4])), col, fl[i + 5]);
    }
    // clicks since the previous frame flash at their detector (absorptions at the structure, dark counts grey)
    if (lastT !== null && tw > lastT && clk.n) {
      const i0 = firstAfter(lastT), i1 = firstAfter(tw);
      const seen = new Set();
      for (let i = i1 - 1; i >= i0 && seen.size < 5; i--) {
        if (seen.has(clk.det[i])) continue;
        seen.add(clk.det[i]);
        flashes = flashes.filter((f) => f.det !== clk.det[i]);
        flashes.push({ det: clk.det[i], pol: clk.pol[i], w: performance.now() });
      }
    }
    lastT = tw;
    const wall = performance.now();
    flashes = flashes.filter((f) => wall - f.w < 450);
    for (const f of flashes) {
      const a = 1 - (wall - f.w) / 450, pos = f.det === 4 ? P : det[f.det];
      if (!pos) continue;
      g.save(); g.globalAlpha = 0.8 * a; g.strokeStyle = f.det === 4 ? A_COL : polCol(f.pol); g.lineWidth = 1.6;
      g.beginPath(); g.arc(pos[0], pos[1], 8 + 12 * (1 - a), 0, 2 * Math.PI); g.stroke(); g.restore();
    }
    // the field strip: |E|² of the source's light through the structure, same depth scale
    if (fieldOn) {
      const xS = W1;
      g.fillStyle = css("--canvas"); g.fillRect(xS, 0, pw, Hg);
      g.strokeStyle = css("--line"); g.beginPath(); g.moveTo(xS, 0); g.lineTo(xS, Hg); g.stroke();
      zc = 0;
      for (const L of su.layers) { const ya = yz(zc), yb = yz(zc + L.d); zc += L.d; g.fillStyle = layerFill(L); g.globalAlpha = 0.35; g.fillRect(xS + 28, ya, pw - 32, Math.max(yb - ya, 0.6)); g.globalAlpha = 1; }
      let emax = 0; for (let i = 0; i < nz; i++) emax = Math.max(emax, E2[i]);
      emax = emax || 1;
      for (let i = 0; i + 1 < nz; i++) { g.fillStyle = lut(E2[i] / emax); g.fillRect(xS + 6, yz(z[i]), 14, Math.max(yz(z[i + 1]) - yz(z[i]), 0.7)); }
      g.strokeStyle = hexA(css("--ink"), 0.5); g.lineWidth = 1;
      if (!none) for (const e of [0, D]) { g.beginPath(); g.moveTo(xS + 4, yz(e)); g.lineTo(W - 4, yz(e)); g.stroke(); }
      const xl = (v) => xS + 28 + (v / emax) * (pw - 34);
      g.strokeStyle = css("--accent"); g.lineWidth = 1.4; g.beginPath();
      for (let i = 0; i < nz; i++) { const X = xl(E2[i]), Y = yz(z[i]); if (i) g.lineTo(X, Y); else g.moveTo(X, Y); }  // a jump at an interface stays a jump (p light's E_z)
      g.stroke();
      text(g, t("|E|², the run"), xS + 5, Math.max(14, y0 - 22), { bg: false });
      text(g, t("max {e:.3g}", { e: emax }), xS + 5, Math.max(28, y0 - 8), { color: muted, bg: false });
    }
    if (!narrow) text(g, t("the structure is to scale, the {arm:.3g} cm arms are not", { arm: (su.arm_m ?? 0.3) * 100 }), 6, 14, { color: muted });
    drawCounters(g, { x: 8, y: Hg + 4, w: W - 16, h: ch - 6, rowH, counts: narrow }, frame, seg, su);
    inFlight = [nin, nout];
    cv.__layout = LAY;
    LAY = null;
  }
  const cnt = (c, key) => (c && c[key] !== undefined ? fmt(c[key], "d") : "0");
  function detector(g, pos, dir, label, show = true, dim = false) {
    const nx = -dir[1], ny = dir[0];
    g.save(); g.globalAlpha = dim ? 0.35 : 1;
    g.strokeStyle = css("--ink"); g.lineWidth = 5;
    g.beginPath(); g.moveTo(pos[0] - 10 * nx, pos[1] - 10 * ny); g.lineTo(pos[0] + 10 * nx, pos[1] + 10 * ny); g.stroke();
    g.restore();
    markBox("detector", pos[0] - 11, pos[1] - 11, 22, 22);
    if (!show) return;
    const W = cvGeo.clientWidth, right = pos[0] > W * 0.4;
    text(g, label, pos[0] + (right ? -14 : 14), pos[1] + (pos[1] < 40 ? 24 : -12), { align: right ? "right" : "left", mark: "detector" });
  }
  function dot(g, p, col, w) {
    g.save(); g.globalAlpha = 0.2 + 0.8 * w; g.fillStyle = col;
    g.beginPath(); g.arc(p[0], p[1], 4.2, 0, 2 * Math.PI); g.fill();
    if (w < 0.999) { g.globalAlpha = 0.9; g.strokeStyle = col; g.lineWidth = 1; g.beginPath(); g.arc(p[0], p[1], 6.5, 0, 2 * Math.PI); g.stroke(); }
    g.restore();
  }
  // a beam's polarisation as seen looking along it (towards the source): p across the beam in the drawing's plane
  // (horizontal in the glyph), s out of the plane (vertical); the ellipse of its polarised part from the run's density
  // matrix (azimuth from p towards s, ellipticity angle χ, handedness), its degree as the line's strength; unpolarised
  // light a dashed circle
  function glyph(g, at, dir, e, label) {
    const small = cvGeo.clientWidth < 600;
    const r = small ? 9 : 13, nx = -dir[1], ny = dir[0];
    const cx = at[0] + nx * (small ? 17 : 26), cy = at[1] + ny * (small ? 17 : 26);
    g.save();
    g.fillStyle = hexA(css("--panel"), 0.9); g.strokeStyle = hexA(css("--ink"), 0.35); g.lineWidth = 1;
    g.beginPath(); g.arc(cx, cy, r + 4, 0, 2 * Math.PI); g.fill(); g.stroke();
    g.strokeStyle = hexA(css("--ink"), 0.2);
    g.beginPath(); g.moveTo(cx - r - 3, cy); g.lineTo(cx + r + 3, cy); g.moveTo(cx, cy - r - 3); g.lineTo(cx, cy + r + 3); g.stroke();
    const deg = e && e.degree !== undefined ? e.degree : 0;
    if (deg < 0.999) { g.setLineDash([2, 2]); g.strokeStyle = UNP_COL; g.lineWidth = 1.2; g.beginPath(); g.arc(cx, cy, r * Math.sqrt(1 - Math.min(1, deg)), 0, 2 * Math.PI); g.stroke(); g.setLineDash([]); }
    if (deg > 1e-6 && e.azimuth !== null && e.azimuth !== undefined) {
      const az = e.azimuth * Math.PI / 180, chi = (e.chi || 0) * Math.PI / 180;
      const a = r * Math.cos(chi), bb = Math.max(r * Math.abs(Math.sin(chi)), 0.6);
      g.translate(cx, cy); g.rotate(-az);
      g.strokeStyle = LIN_COL; g.globalAlpha = 0.25 + 0.75 * deg; g.lineWidth = 2;
      g.beginPath(); g.ellipse(0, 0, a, bb, 0, 0, 2 * Math.PI); g.stroke();
      if (Math.abs(chi) > 0.01) {  // the sense of rotation: right-handed (χ > 0) clockwise as the beam comes towards us
        const sgn = chi > 0 ? 1 : -1;
        g.fillStyle = LIN_COL; g.beginPath(); g.moveTo(0, -bb * sgn); g.lineTo(-5 * sgn, -bb * sgn - 3); g.lineTo(-5 * sgn, -bb * sgn + 3); g.fill();
      }
    }
    g.restore();
    markBox("ellipse", cx - r - 4, cy - r - 4, 2 * r + 8, 2 * r + 8);
    text(g, "p", cx + r + 4, cy + 4, { color: muted0(), bg: false, font: "9px system-ui" });
    text(g, "s", cx - 3, cy - r - 5, { color: muted0(), bg: false, font: "9px system-ui" });
    if (label && cvGeo.clientWidth >= 600) text(g, label, cx + r + 10, cy + 4, { color: muted0(), font: "10px system-ui" });
  }
  const muted0 = () => css("--muted");

  // the counters against the run's computed fractions: a bar each, its tick the expectation, its whisker ±2σ
  function drawCounters(g, bx, frame, seg, su) {
    const c = frame.counts || {}, me = frame.meas || {}, here = c.here || [true, false, true, false];
    const ink = css("--ink"), muted = css("--muted");
    g.strokeStyle = css("--line"); g.beginPath(); g.moveTo(0, bx.y - 2); g.lineTo(cvGeo.clientWidth, bx.y - 2); g.stroke();
    const n = (me.n_clicks ?? 0);
    const gate = frame.gated ? " · " + t("gate closed") : "";
    const head = me.t_c === null || me.t_c === undefined ? t("Counters: the counting has not started")
      : [t("Counters, {t}: {n:d} clicks ({d:d} of them dark counts)", { t: time(me.t_c, 3), n, d: me.n_dark ?? 0 }) + gate,
         t("{t}: {n:d} clicks, {d:d} dark", { t: time(me.t_c, 3), n, d: me.n_dark ?? 0 }) + gate];
    text(g, head, bx.x, bx.y + 11, { bg: false, font: "600 11.5px system-ui" });
    if (bx.counts) {  // a phone: the detectors' counts in a line of their own (their labels on the bench are short)
      const parts = [];
      for (const [arm, i0] of [["R", 0], ["T", 2]]) {
        if (here[i0 + 1]) parts.push(`${arm}+ ${cnt(c, arm + "p")} · ${arm}− ${cnt(c, arm + "r")}`);
        else parts.push(`${arm} ${cnt(c, arm + "p")}`);
      }
      text(g, parts.join("   "), bx.x, bx.y + 11 + bx.rowH, { bg: false, color: muted });
    }
    const rows = [[t("reflected"), me.R_frac, me.R_frac_se, me.R_frac_ref, "#ae3ec9"], [t("transmitted"), me.T_frac, me.T_frac_se, me.T_frac_ref, "#2b8a3e"]];
    if (here[1]) rows.push([t("R arm through the analyser"), me.fR_pass, me.fR_pass_se, me.fR_pass_ref, LIN_COL]);
    if (here[3]) rows.push([t("T arm through the analyser"), me.fT_pass, me.fT_pass_se, me.fT_pass_ref, LIN_COL]);
    g.font = "11px system-ui";
    const labW = Math.min(170, Math.max(...rows.map((r) => g.measureText(r[0]).width)) + 8);
    const valueText = (f, se, ref, long) => {
      const v = f === null || f === undefined ? "—" : se ? `${fmt(f, ".4g")} ± ${fmt(se, ".2g")}` : fmt(f, ".4g");
      return long && ref !== null && ref !== undefined ? `${v} (${t("computed {p:.4g}", { p: ref })})` : v;
    };
    // the bar takes what the label and the value leave; the value drops its «computed» part when the strip is narrow
    // (the tick shows the computed value)
    let long = true;
    let textW = Math.max(...rows.map((r) => g.measureText(valueText(r[1], r[2], r[3], true)).width));
    if (bx.w - labW - textW - 10 < 70) { long = false; textW = Math.max(...rows.map((r) => g.measureText(valueText(r[1], r[2], r[3], false)).width)); }
    const barW = Math.max(40, Math.min(bx.w * 0.45, bx.w - labW - textW - 10));
    rows.forEach(([lab, f, se, ref, col], i) => {
      const y = bx.y + 16 + (i + (bx.counts ? 1 : 0)) * bx.rowH;
      text(g, lab, bx.x, y + 11, { bg: false, color: muted });
      const x0 = bx.x + labW;
      g.fillStyle = css("--chip"); g.fillRect(x0, y + 2, barW, 11);
      if (f !== null && f !== undefined) { g.fillStyle = col; g.fillRect(x0, y + 2, barW * clamp01(f), 11); }
      if (se && ref !== null && ref !== undefined) {
        g.strokeStyle = ink; g.lineWidth = 1;
        const a = clamp01(ref - 2 * se), b = clamp01(ref + 2 * se);
        g.beginPath(); g.moveTo(x0 + barW * a, y + 7.5); g.lineTo(x0 + barW * b, y + 7.5); g.stroke();
      }
      if (ref !== null && ref !== undefined) { g.fillStyle = ink; g.fillRect(x0 + barW * clamp01(ref) - 1, y, 2.5, 15); }
      text(g, valueText(f, se, ref, long), x0 + barW + 6, y + 11, { bg: false });
    });
    markBox("counters", bx.x, bx.y, bx.w, bx.h);
  }

  // --- the curves ------------------------------------------------------------------------------------------------
  function axes(g, bx, xmin, xmax, xticks, xfmt, title) {
    g.strokeStyle = css("--grid"); g.lineWidth = 1;
    for (const v of [0, 0.25, 0.5, 0.75, 1]) { const y = bx.y + (1 - v) * bx.h; g.beginPath(); g.moveTo(bx.x, y); g.lineTo(bx.x + bx.w, y); g.stroke(); }
    g.strokeStyle = css("--line"); g.strokeRect(bx.x, bx.y, bx.w, bx.h);
    const muted = css("--muted");
    for (const v of [0, 0.5, 1]) text(g, fmt(v), bx.x - 4, bx.y + (1 - v) * bx.h + 4, { align: "right", color: muted, bg: false });
    for (const v of xticks) {
      const X = bx.x + (v - xmin) / (xmax - xmin) * bx.w;
      g.fillStyle = muted; g.fillRect(X, bx.y + bx.h, 1, 4);
      text(g, xfmt(v), X, bx.y + bx.h + 14, { align: "center", color: muted, bg: false });
    }
    text(g, title, bx.x, bx.titleY ?? bx.y - 6, { bg: false, font: "600 12px system-ui" });
  }
  function curve(g, bx, xs, ys, xmin, xmax, col, w, dash, alpha = 1) {
    g.save(); g.strokeStyle = col; g.lineWidth = w; g.setLineDash(dash || []); g.globalAlpha = alpha;
    g.beginPath();
    for (let i = 0; i < xs.length; i++) {
      const X = bx.x + (xs[i] - xmin) / (xmax - xmin) * bx.w, Y = bx.y + (1 - Math.min(1, Math.max(0, ys[i]))) * bx.h;
      if (i) g.lineTo(X, Y); else g.moveTo(X, Y);
    }
    g.stroke(); g.restore();
  }
  function vline(g, bx, X, col, dash, label, frac = 0.92) {  // frac: height of the label (0 top .. 1 bottom)
    g.save(); g.strokeStyle = col; g.lineWidth = 1.2; g.setLineDash(dash || []);
    g.beginPath(); g.moveTo(X, bx.y); g.lineTo(X, bx.y + bx.h); g.stroke(); g.restore();
    if (label) {
      g.font = "11px system-ui";
      const w = g.measureText(label).width, right = X + 3 + w > bx.x + bx.w;
      text(g, label, right ? X - 3 : X + 3, bx.y + frac * bx.h + 4, { color: col, align: right ? "right" : "left" });
    }
  }
  function drawCurves(frame, tw) {
    const cv = cvCur, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    LAY = { w: W, h: Hh, labels: [], marks: [] };
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(tw);
    if (!seg || !W || !Hh || !on.curves) {
      if (seg && !on.curves && W && Hh) text(g, t("curves hidden (overlay “curves”)"), 10, 20, { color: css("--muted") });
      cv.__layout = LAY; LAY = null; return;
    }
    const su = seg.setup, b = seg.b || {}, pm = su.pol;
    const ink = css("--ink"), muted = css("--muted"), accent = css("--accent");
    const panels = [];
    if (b.th && b.Rs) panels.push("th");
    if (b.lam && b.lRs) panels.push("lam");
    if (b.ana_a && (b.anaR_f || b.anaT_f)) panels.push("ana");
    const weights = { th: 1.25, lam: 1, ana: 0.9 };
    const tot = panels.reduce((s, p) => s + weights[p], 0) || 1;
    let yAt = 0;
    const curC = pm === "s" ? S_COL : pm === "p" ? P_COL : pm === "lin" ? LIN_COL : ink;
    const cm = seg.cur.mix;
    for (const p of panels) {
      const h = Hh * weights[p] / tot;
      const bx = { x: 40, y: yAt + 40, w: W - 52, h: Math.max(30, h - 66), titleY: yAt + 16 };
      if (p === "th") {
        axes(g, bx, 0, 90, [0, 15, 30, 45, 60, 75, 90], (v) => v + "°", t("R(θ), T(θ) at λ = {lam:.4g} nm", { lam: su.lam }));
        if (seg.theta_c !== null && seg.theta_c !== undefined) {
          const X = bx.x + seg.theta_c / 90 * bx.w;
          g.fillStyle = hexA(accent.startsWith("#") ? accent : "#1c6dd0", 0.07); g.fillRect(X, bx.y, bx.x + bx.w - X, bx.h);
        }
        const lossy = !su.lossless;
        const thick = (q) => (pm === q ? 2.4 : 1.3);
        for (const [q, col] of [["s", S_COL], ["p", P_COL]]) {
          curve(g, bx, b.th, b["R" + q], 0, 90, col, thick(q));
          curve(g, bx, b.th, b["T" + q], 0, 90, col, thick(q), [6, 4]);
          if (lossy) curve(g, bx, b.th, b["A" + q], 0, 90, col, thick(q), [1.5, 3]);
        }
        if ((pm === "unpol" || pm === "lin") && b.Rc) { curve(g, bx, b.th, b.Rc, 0, 90, ink, 2.2); curve(g, bx, b.th, b.Tc, 0, 90, ink, 2.2, [6, 4]); }
        if (seg.theta_c !== null && seg.theta_c !== undefined) {
          const lab = su.kind === "tir" && su.layers.length ? t("θ_c of the face = {a:.5g}°", { a: seg.theta_c }) : `θ_c = ${fmt(seg.theta_c, ".5g")}°`;
          vline(g, bx, bx.x + seg.theta_c / 90 * bx.w, accent, [3, 3], lab, 0.62);
        } else if (seg.theta_c_face !== null && seg.theta_c_face !== undefined) {
          vline(g, bx, bx.x + seg.theta_c_face / 90 * bx.w, accent, [3, 3], t("θ_c of the face = {a:.5g}°", { a: seg.theta_c_face }), 0.62);
        }
        if (seg.theta_B) vline(g, bx, bx.x + seg.theta_B.deg / 90 * bx.w, P_COL, [3, 3], `θ_B = ${fmt(seg.theta_B.deg, ".5g")}°`, 0.86);
        else if (seg.min_rp) vline(g, bx, bx.x + seg.min_rp.deg / 90 * bx.w, P_COL, [2, 4], t("min. R_p = {r:.3g} at {a:.4g}°", { r: seg.min_rp.Rp, a: seg.min_rp.deg }), 0.86);
        const Xc = bx.x + su.theta / 90 * bx.w;
        vline(g, bx, Xc, curC, null, null);
        for (const v of [cm.R, cm.T]) { g.fillStyle = curC; g.beginPath(); g.arc(Xc, bx.y + (1 - v) * bx.h, 4, 0, 2 * Math.PI); g.fill(); }
        text(g, `θ = ${fmt(su.theta, ".5g")}°: R = ${fmt(cm.R, ".5g")}, T = ${fmt(cm.T, ".5g")}` + (lossy ? `, A = ${fmt(cm.A, ".4g")}` : ""),
          Math.min(Xc + 6, bx.x + bx.w - 230), bx.y + 14, { color: curC });
        legend(g, bx.x + bx.w, bx.titleY + 16, lossy, pm);
      } else if (p === "lam") {
        const l0 = b.lam[0], l1 = b.lam[b.lam.length - 1];
        const ticks = [400, 500, 600, 700, 800, 1000, 1200, 1400, 1600].filter((v) => v >= l0 && v <= l1);
        axes(g, bx, l0, l1, ticks, (v) => String(v), t("R(λ), T(λ) at θ = {th:.5g}°, polarisation {pol}; λ, nm", { th: su.theta, pol: polText(su) }));
        for (let L = Math.max(380, Math.ceil(l0)); L < Math.min(780, l1); L += 2) {
          const X = bx.x + (L - l0) / (l1 - l0) * bx.w; g.fillStyle = lamRGB(L); g.fillRect(X, bx.y + bx.h - 4, Math.ceil(bx.w * 2 / (l1 - l0)) + 1, 4);
        }
        if (pm !== "s" && pm !== "p") for (const [q, col] of [["s", S_COL], ["p", P_COL]]) curve(g, bx, b.lam, b["lR" + q], l0, l1, col, 1, null, 0.35);
        curve(g, bx, b.lam, b.lRc, l0, l1, curC, 2);
        curve(g, bx, b.lam, b.lTc, l0, l1, curC, 2, [6, 4]);
        if (!su.lossless) curve(g, bx, b.lam, b.lAc, l0, l1, curC, 1.6, [1.5, 3]);
        if (su.lam0) vline(g, bx, bx.x + (su.lam0 - l0) / (l1 - l0) * bx.w, muted, [3, 3], `λ₀ = ${fmt(su.lam0, ".4g")}`, 0.5);
        const Xl = bx.x + (su.lam - l0) / (l1 - l0) * bx.w;
        vline(g, bx, Xl, curC, null, null);
        for (const v of [cm.R, cm.T]) { g.fillStyle = curC; g.beginPath(); g.arc(Xl, bx.y + (1 - v) * bx.h, 4, 0, 2 * Math.PI); g.fill(); }
        text(g, `λ = ${fmt(su.lam, ".4g")} nm: R = ${fmt(cm.R, ".4g")}, T = ${fmt(cm.T, ".4g")}`, Math.min(Xl + 6, bx.x + bx.w - 200), bx.y + 14, { color: curC });
      } else {
        axes(g, bx, 0, 180, [0, 30, 60, 90, 120, 150, 180], (v) => v + "°", [t("Share through the analyser against its angle α (the arm's light)"),
          t("Share through the analyser against α")]);
        for (const [arm, key, col] of [["R", "anaR_f", "#ae3ec9"], ["T", "anaT_f", "#2b8a3e"]]) {
          if (!b[key] || !su.ana[arm]) continue;
          curve(g, bx, b.ana_a, b[key], 0, 180, col, 2);
          const a = ((su.ana[arm].alpha % 180) + 180) % 180, X = bx.x + a / 180 * bx.w;
          vline(g, bx, X, col, [3, 3], `${arm}: α = ${fmt(su.ana[arm].alpha, ".4g")}°`, arm === "R" ? 0.15 : 0.35);
        }
      }
      yAt += h;
    }
    cv.__layout = LAY;
    LAY = null;
  }
  function legend(g, xr, y, lossy, pm) {
    const items = [["R_s", S_COL, null], ["T_s", S_COL, [6, 4]], ["R_p", P_COL, null], ["T_p", P_COL, [6, 4]]];
    if (pm === "unpol" || pm === "lin") items.push([t("R, T of the source's light"), css("--ink"), null]);
    if (lossy) items.push(["A", css("--muted"), [1.5, 3]]);
    g.font = "11px system-ui";
    let x = xr;
    for (const [lab, col, dash] of items.reverse()) {
      const w = g.measureText(lab).width + 26; x -= w;
      if (x < 40) break;
      g.save(); g.strokeStyle = col; g.lineWidth = 2; g.setLineDash(dash || []); g.beginPath(); g.moveTo(x, y - 4); g.lineTo(x + 16, y - 4); g.stroke(); g.restore();
      text(g, lab, x + 19, y, { bg: false });
    }
  }

  // --- Watch: the caption's band (desktop: the caption lies over the stage's bottom) -------------------------------------
  function captionBand() {
    if (ctx.screen !== "watch" || !story || !story.captions.length) return 0;
    const stage = center.closest(".dm-stage"), cap = stage && stage.querySelector(".dm-caption");
    if (!cap || getComputedStyle(cap).position !== "absolute") return 0;  // a phone: the caption has its own place
    const probe = cap.cloneNode(false);
    probe.removeAttribute("hidden"); probe.removeAttribute("aria-live"); probe.setAttribute("aria-hidden", "true");
    probe.style.visibility = "hidden";
    stage.append(probe);
    let hMax = 0;
    for (const text of story.captions) { probe.textContent = t(text); hMax = Math.max(hMax, probe.getBoundingClientRect().height); }
    probe.remove();
    return Math.ceil(hMax + (parseFloat(getComputedStyle(cap).bottom) || 0) + 10);
  }
  function syncBand() {
    const b = captionBand();
    if (b && b !== band) { band = b; center.style.setProperty("--u35-band", `${b}px`); ctx.requestRender(); }
  }
  if (ctx.screen === "watch") new ResizeObserver(() => syncBand()).observe(center);

  // --- panels ---------------------------------------------------------------------------------------------
  function drawInfo() {
    const su = now();
    if (!su || !su.label) return;
    const rows = [[t("Structure"), t(su.label)], [t("Incidence medium"), t(su.med_in_name)], [t("{name:cap}", { name: su.out_name }), t(su.med_out_name)],
      [t("Wavelength λ"), t("{v:.6g} nm, line width {w:.3g} nm", { v: su.lam, w: su.dlam })], [t("Angle of incidence θ"), num(su.theta, 6) + "°"],
      [t("Polarisation"), t(su.pol_label) + (su.pol === "lin" ? ` (ψ = ${num(su.psi, 4)}°)` : "")],
      [t("Source rate"), t("{v:.4g} photons/s", { v: su.rate })], [t("Shutter"), su.shutter === "closed" ? t("closed") : t("open")],
      [t("Flight to the structure"), time(su.t_in, 4)],
      [t("Group delay: reflection, transmission"), `${time(su.tau_r, 3)}, ${time(su.tau_t, 3)}`],
      [t("Layers"), su.layers.length ? t("{k:d}, total thickness {d:.5g} nm", { k: su.layers.length, d: su.thickness }) : "0"]];
    if (su.lam0) rows.push([t("Design λ₀"), t("{v:.5g} nm", { v: su.lam0 })]);
    for (const arm of ["R", "T"]) {
      const a = su.ana && su.ana[arm];
      rows.push([arm === "R" ? t("Analyser before the reflection detector") : t("Analyser before the transmission detector"),
        a ? t("α = {a:.4g}°, k₁ = {k1}, k₂ = {k2}", { a: a.alpha, k1: a.k1, k2: a.k2 }) : t("out")]);
    }
    if (su.det) rows.push([t("Detectors"), t(su.det.title)], [t("Efficiency, dark counts, dead time, jitter σ"),
      `${num(su.det.eta, 3)}, ${t("{v:.4g} s⁻¹", { v: su.det.dark })}, ${time(su.det.dead, 3)}, ${time(su.det.jitter, 3)}`]);
    if (su.gate) rows.push([t("Counting time (gate)"), time(su.gate, 4)]);
    const items = [el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]))];
    if (su.layers.length && su.layers.length <= 8) {
      items.push(el("table", { style: { fontSize: "12px", marginTop: "6px" } },
        el("tr", {}, el("th", {}, t("layer")), el("th", {}, "n"), el("th", {}, t("d, nm"))),
        su.layers.map((L) => el("tr", {}, el("td", {}, t(L.name) + (L.mat ? ` (${MAT_SHORT[L.mat] || ""})` : "")), el("td", { class: "mono" }, fmtN(L.n)), el("td", { class: "mono" }, num(L.d, 5))))));
    }
    infoBox.replaceChildren(...items);
    const seg = segs[segs.length - 1];
    const ell = (e) => (!e ? "—" : e.degree < 1e-6 ? t("unpolarised")
      : t("azimuth {a:.4g}° from p, ellipticity angle χ = {c:.3g}°, degree of polarisation {d:.6g}", { a: e.azimuth ?? 0, c: e.chi ?? 0, d: e.degree }));
    polBox.replaceChildren(el("div", { class: "kv" },
      el("span", {}, t("Reflected beam")), el("span", { class: "mono" }, ell(seg && seg.ell && seg.ell.R)),
      el("span", {}, t("Transmitted beam")), el("span", { class: "mono" }, ell(seg && seg.ell && seg.ell.T))),
      el("div", { class: "help" }, t("Each beam's state is its density matrix computed by the run from the Jones matrices of the structure; the ellipse is that of its polarised part (p in the plane of incidence, s across it).")));
  }
  function drawStats(frame) {
    const tt = frame.totals || {}, c = frame.counts || {};
    const rows = [[t("emitted in all"), tt.emitted], [t("in flight: to the structure / after it"), `${inFlight[0]} / ${inFlight[1]}`],
      [t("reflected (in all)"), tt.R], [t("transmitted (in all)"), tt.T], [t("absorbed (in all)"), tt.A],
      [t("missed by the detectors (efficiency, dead time)"), tt.missed], [t("dark counts (in all)"), tt.dark],
      [t("transitional (emitted before a change)"), tt.transitional], [t("lost at a rebuild"), tt.lost],
      [t("clicks counted in this segment"), c.n]];
    statBox.replaceChildren(el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, String(v ?? 0))])),
      el("div", { class: "help" }, t("A real detector clicks for only part of the photons that reach it, clicks now and then in the dark, and is dead for a while after each click. Which clicks were dark counts is known only in a simulation (grey flashes).")),
      frame.lag ? el("p", { class: "st-bad" }, t("The computation cannot keep up with the chosen speed: the world runs slower.")) : "");
  }

  return {
    center, rightPanels,
    quantSafe: QUANT_SAFE,
    overlays: OVERLAYS.map((o) => ({ ...o, default: on[o.id], label: t(o.label) })),  // i18n-msgids: "beams" "photons in flight" "field |E|²" "curves R(θ), T(θ), R(λ), T(λ)" "polarisation ellipses"
    setOverlay(id, v) { if (id in on) { on[id] = !!v; ctx.requestRender(); } },
    // Watch: the bench does not move (one scale for the whole story); the band under the pictures is the height of the
    // story's longest caption at the stage's width, the same for the whole recording, so no caption covers the bench,
    // the curves or the counters (as u34's view does)
    setStory({ worlds } = {}) {
      const caps = [];
      for (const W of worlds || []) for (const c of W.captions || []) caps.push(c.text);
      story = { captions: caps };
      syncBand();
    },
    help: () => el("div", {},
      el("h4", {}, t("What is on the screen")),
      el("p", {}, t("On the left, the bench: the source, the planar structure (to scale in depth: the layers are coloured bands of their materials, the bar on the right of it is one wavelength), the incident, reflected and transmitted beams at the angles the run computed by Snell's law, the detectors and, where one stands, an analyser: a polarising beam splitter with a detector on each port. The brightness of the beams is the computed R and T. The small circles show each beam's polarisation as seen along it (p across the beam in the drawing's plane, s out of it): a line for linear light, an ellipse for elliptical light, a dashed circle for the unpolarised part. On the right of the bench, the field |E|² of the source's light in and near the structure; along the bottom, the counters.")),
      el("p", {}, t("Photons fly one by one (orange: s, blue: p, purple: linear at the angle ψ, grey: unpolarised). When a photon reaches the structure, its outcome is drawn by the Born rule from its density matrix. While no detector has clicked, two packets (rings) are shown after the structure, their brightness by the probabilities; a click (a flash) is the outcome; a real detector misses some photons and clicks in the dark (grey flashes). An absorbed photon vanishes in the structure (a red flash).")),
      el("p", {}, t("The curves: R(θ), T(θ) for s and p at the current λ (θ_B: where the run's r_p vanishes, θ_c: where the run's transmission vanishes), the spectrum R(λ), T(λ) at the current angle, each wavelength with its materials' own indices, and, with an analyser, the share of the arm's light through it against its angle.")),
      el("p", {}, t("Any change of the set-up applies at once and starts a new segment. Photons emitted before a change of the source or the structure fly on and are counted as transitional; when the angle or the media change, the beam paths are rebuilt and the photons in flight are lost (this is counted)."))),
    reset() { H = null; segs = []; clk = newClicks(); flashes = []; lastT = null; },
    // key frames (player.js): segments and clicks only grow (lengths); the panels follow the last segment
    snapshot() { return { segs: segs.length, clk: clk.n }; },
    restore(k) {
      segs.length = k.segs; clk.n = k.clk; lastT = null; flashes = [];
      const last = segs[segs.length - 1];
      approxBox.replaceChildren(...((last && last.approx) || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• " + t(a))));
      if (last) ctx.setScene && ctx.setScene(sceneText(last.setup));
      drawInfo();
    },
    onHeader(meta) { H = meta; },
    onMessage(meta, blobs) {
      if (meta.type === "segment") {
        segs.push({ ...meta, b: blobs || {} });
        approxBox.replaceChildren(...(meta.approx || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• " + t(a))));
        ctx.setScene && ctx.setScene(sceneText(meta.setup));
        drawInfo();
        lastT = null;
      } else if (meta.type === "clicks" && blobs && blobs.t) {
        pushClicks(blobs);
      }
    },
    render(frame, tw, blobs) {
      if (!H) return;
      if (lastT !== null && tw < lastT) { lastT = null; flashes = []; }
      drawGeometry(frame || {}, tw, blobs);
      if (curvesShown()) drawCurves(frame || {}, tw);
      drawStats(frame || {});
    },
  };
}
