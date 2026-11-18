// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The tests' thrown ball (tests/site_worlds/s98_atlas_toy; the fixture of the screens, design
// lfphys/sources/explore_2026-11-14_design.md §2.4): a side view drawn from the run's `traj` chunks (computed samples),
// the ball at the latest frame, the landing mark when the time reaches it. Drawing only: it computes no physics.
// The screens' optional contract: `ctx.screen`, `overlays` + `setOverlay`, `setTraces`, `worldToPx` / `pxToWorld`,
// `anchors()`, `quantSafe`; it copes with a frame without its `ghost` blob (dropped by the Explore screen) and a header
// without its `ticks` blob (dropped by the screen «Throws»).
import { t } from "/static/js/i18n.js";
import { css, el, fresh2d } from "/static/js/ui.js";

// what the view accepts quantised (registry.view_declarations reads this literal)
export const QUANT_SAFE = { "traj.s": "u16", "header.ticks": "u16" };
// the overlays it can toggle (registry.view_declarations reads the ids)
export const OVERLAYS = [
  { id: "path", label: "path", default: true },
  { id: "strobe", label: "strobe", default: false },
  { id: "v", label: "velocity", default: false },
];

export function createView(ctx) {
  const cv = el("canvas");
  const center = el("div", { class: "canvas-wrap", style: { flex: 1 } }, cv);
  new ResizeObserver(() => ctx.requestRender && ctx.requestRender()).observe(cv);
  const on = Object.fromEntries(OVERLAYS.map((o) => [o.id, o.default]));
  let header = null, rows = [], landing = null, traces = [], map = null;

  function samples() { return rows; }
  function push(s) {  // s: a Float32Array or Float64Array of n × 5 (t, x, y, vx, vy)
    for (let i = 0; i + 4 < s.length; i += 5) rows.push([s[i], s[i + 1], s[i + 2], s[i + 3], s[i + 4]]);
  }
  function box() {
    const b = (header && header.scene && header.scene.box) || [[-0.2, -0.05], [1, 1]];
    return b;
  }
  function makeMap(W, H) {
    const [[x0, y0], [x1, y1]] = box();
    const k = Math.min((W - 40) / (x1 - x0), (H - 40) / (y1 - y0));
    const ox = 20 - x0 * k, oy = H - 20 + y0 * k;
    return { k, toPx: ([x, y]) => [ox + x * k, oy - y * k], toWorld: ([px, py]) => [(px - ox) / k, (oy - py) / k] };
  }
  function drawPath(g, pts, tMax, alpha) {
    g.save(); g.globalAlpha = alpha; g.strokeStyle = css("--ink") || "#333"; g.beginPath();
    let pen = false;
    for (const r of pts) { if (r[0] > tMax) break; const [px, py] = map.toPx([r[1], r[2]]); if (pen) g.lineTo(px, py); else { g.moveTo(px, py); pen = true; } }
    g.stroke(); g.restore();
  }

  return {
    center,
    quantSafe: QUANT_SAFE,
    overlays: OVERLAYS.map((o) => ({ ...o, label: t(o.label) })),  // i18n-msgids: "path" "strobe" "velocity"
    setOverlay(id, v) { on[id] = !!v; ctx.requestRender && ctx.requestRender(); },
    setTraces(list) { traces = list || []; ctx.requestRender && ctx.requestRender(); },
    worldToPx(p) { return map ? map.toPx(p) : [NaN, NaN]; },
    pxToWorld(q) { return map ? map.toWorld(q) : [NaN, NaN]; },
    // where the lab's tape, ruler and protractor sit (a lab step with a ruler needs it: registry, EX2 §5 F8)
    anchors() {
      const L = (header && header.launcher) || { h: 0, angle: 0 };
      return { launch: [0, Number(L.h) || 0], floor: 0, angle: Number(L.angle) || 0, landing: landing ? [landing.L, 0] : null };
    },
    samples,
    reset() { header = null; rows = []; landing = null; },
    snapshot() { return { n: rows.length, landing }; },
    restore(k) { rows.length = k.n; landing = k.landing; },
    onHeader(h) { header = h; rows = []; landing = null; },
    onMessage(meta, blobs) {
      if (meta.type === "traj" && blobs && blobs.s) push(blobs.s);
      else if (meta.type === "event" && meta.kind === "landing") landing = meta.data;
    },
    render(frame, tt) {
      const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, H = cv.clientHeight;
      if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
      const g = fresh2d(cv.getContext("2d"), dpr);
      g.fillStyle = css("--canvas") || "#fff"; g.fillRect(0, 0, W, H);
      map = makeMap(W, H);
      g.strokeStyle = css("--grid") || "#ccc"; g.beginPath();
      const [gx0, gy] = map.toPx([box()[0][0], 0]), [gx1] = map.toPx([box()[1][0], 0]);
      g.moveTo(gx0, gy); g.lineTo(gx1, gy); g.stroke();
      for (const tr of traces) if (tr.W && tr.W.view && tr.W.view.samples) drawPath(g, tr.W.view.samples(), tr.t, tr.alpha ?? 0.3);
      const tNow = frame ? frame.t ?? tt : tt;
      if (on.path) drawPath(g, rows, tNow ?? Infinity, 1);
      if (on.strobe) { g.fillStyle = "#1c7ed6"; for (const r of rows) if (Math.abs(r[0] / 0.1 - Math.round(r[0] / 0.1)) < 1e-6) { const [px, py] = map.toPx([r[1], r[2]]); g.beginPath(); g.arc(px, py, 2.5, 0, 2 * Math.PI); g.fill(); } }
      if (frame) {
        const [px, py] = map.toPx([frame.x, frame.y]);
        g.fillStyle = "#e8590c"; g.beginPath(); g.arc(px, py, 6, 0, 2 * Math.PI); g.fill();
        if (frame.drop_y !== undefined) { const [qx, qy] = map.toPx([0, frame.drop_y]); g.fillStyle = "#868e96"; g.beginPath(); g.arc(qx, qy, 6, 0, 2 * Math.PI); g.fill(); }
      }
      if (landing) { const [lx, ly] = map.toPx([landing.L, 0]); g.strokeStyle = "#c92a2a"; g.beginPath(); g.moveTo(lx, ly - 8); g.lineTo(lx, ly + 8); g.stroke(); }
    },
  };
}
