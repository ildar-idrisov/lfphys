// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// S03 view: a side view of a ball thrown from a table or from the floor (design lfphys/sources/explore_2026-11-14_design.md
// §5.2). Everything drawn is data of the run: the path is the run's samples (`traj`, every 1/60 s of world time) revealed
// as the time reaches them, the ball and the arrows come with each frame (its velocity, the drag force the engine
// computed, the energies), the top of the path and the landing are the run's events. The view scales, draws and formats;
// it computes no physics (the strobe dots are the samples whose index is a multiple of the header's `strobe_every`, i.e.
// of 0.1 s; the newest piece of the path joins the last sample sent to the ball's computed position in the frame).
//
// The screens' contract (design §2.4): `overlays` + `setOverlay`, `setTraces` (earlier points drawn faded, each from its
// own decoded world), `worldToPx` / `pxToWorld` and `anchors()` for the lab's instruments, `quantSafe`, and Watch's
// `setStory({worlds, w})` (review R-W F3, D8): one scale over all the recording's throws (the box over the worlds'
// computed scene boxes) and the earlier worlds' throws kept as faded traces with their ranges, read from the recording's
// own messages. A view's own toolbar of overlays is shown where no screen panel offers them (a live run, a recording,
// Watch). In Watch the view leaves room under the scene for the caption laid over it, so that it never covers a landing.
import { t } from "/static/js/i18n.js";
import { css, el, fmt, fresh2d, num } from "/static/js/ui.js";

// what the view accepts quantised (registry.view_declarations reads this literal): the samples' table t, x, y
export const QUANT_SAFE = { "traj.s": "u16" };
// the overlays it can toggle (registry.view_declarations reads the ids)
export const OVERLAYS = [
  { id: "path", label: "path", default: true },
  { id: "strobe", label: "dots every 0.1 s", default: false },
  { id: "v", label: "velocity", default: false },
  { id: "v_parts", label: "velocity components", default: false },
  { id: "forces", label: "forces", default: false },
  { id: "energy", label: "energy", default: false },
];
// i18n-msgids: "path" "dots every 0.1 s" "velocity" "velocity components" "forces" "energy"

const COLORS = { main: "#e8590c", drop: "#1c7ed6", vacuum: "#868e96", v: "#2f9e44", g: "#c2255c", drag: "#7048e8",
  ek: "#f08c00", ep: "#1971c2", q: "#e03131" };
const PAD = 28;           // pixels around the scene
const TOP = 18;           // pixels above it for the ball's name

function niceStep(span, n = 6) {
  const raw = span / n, p = 10 ** Math.floor(Math.log10(raw)), r = raw / p;
  return (r < 1.5 ? 1 : r < 3.5 ? 2 : r < 7.5 ? 5 : 10) * p;
}
function nice(x) {  // 1, 2 or 5 × 10^k at or below x
  if (!(x > 0)) return 1;
  const p = 10 ** Math.floor(Math.log10(x)), r = x / p;
  return (r >= 5 ? 5 : r >= 2 ? 2 : 1) * p;
}

export function createView(ctx) {
  const embedded = ctx.screen === "explore" || ctx.screen === "lab";
  const on = Object.fromEntries(OVERLAYS.map((o) => [o.id, o.default]));
  const touched = new Set();  // overlays the experimenter set (the comparison's default strobe never overrides them)
  let header = null, main = cols(), other = cols(), apex = null, landing = null, oland = null;
  let traces = [], map = null, user = null, drag = null;
  let story = null;  // Watch: {worlds, w, box, earlier: [{main, landing}]} (setStory)
  let placed = [];   // the labels drawn in this frame (their boxes): a new one moves until it overlaps none

  function cols() { return { t: [], x: [], y: [], i: [] }; }
  function push(c, meta, s) {  // s: n × 3 (t, x, y), a Float32Array (quantised) or Float64Array
    let k = meta.i0 ?? c.i.length;
    for (let j = 0; j + 2 < s.length; j += 3, k++) { c.t.push(s[j]); c.x.push(s[j + 1]); c.y.push(s[j + 2]); c.i.push(k); }
  }
  function cut(c, n) { for (const k of Object.keys(c)) c[k].length = n; }

  // --- DOM ---------------------------------------------------------------------------------------------------------
  const cv = el("canvas");
  cv.style.touchAction = "none";
  const wrap = el("div", { class: "canvas-wrap" }, cv);
  const boxes = OVERLAYS.map((o) => {
    const cb = el("input", { type: "checkbox", checked: o.default, "data-overlay": o.id,
      onchange: () => { touched.add(o.id); on[o.id] = cb.checked; redraw(); } });
    return { id: o.id, cb, label: el("label", { class: "check" }, cb, " ", t(o.label)) };
  });
  // Watch on a phone: the overlays fold under «Show», so that the scene keeps the height (review R-W F10)
  const narrow = ctx.screen === "watch" && typeof window !== "undefined" && window.innerWidth < 600;
  const toolbar = embedded ? null : narrow
    ? el("details", { class: "toolbar" }, el("summary", { class: "muted" }, t("Show")), boxes.map((b) => b.label))
    : el("div", { class: "toolbar" }, el("span", { class: "muted" }, t("Show")), boxes.map((b) => b.label));
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, toolbar, wrap);
  new ResizeObserver(() => redraw()).observe(cv);
  function redraw() { if (ctx.requestRender) ctx.requestRender(); }

  // pan (drag) and zoom (wheel) once the experimenter moves the scene; a double click fits it again
  cv.addEventListener("wheel", (e) => {
    if (!map) return;
    e.preventDefault();
    const r = cv.getBoundingClientRect(), [wx, wy] = map.toWorld([e.clientX - r.left, e.clientY - r.top]);
    const f = Math.exp(-e.deltaY * 0.0015), k = map.k * f;
    user = { k, ox: e.clientX - r.left - wx * k, oy: e.clientY - r.top + wy * k };
    redraw();
  }, { passive: false });
  cv.addEventListener("pointerdown", (e) => { if (map) { drag = { x: e.clientX, y: e.clientY, m: { k: map.k, ox: map.ox, oy: map.oy } }; cv.setPointerCapture(e.pointerId); } });
  cv.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (!user && Math.hypot(dx, dy) < 4) return;
    user = { k: drag.m.k, ox: drag.m.ox + dx, oy: drag.m.oy + dy };
    redraw();
  });
  cv.addEventListener("pointerup", () => { drag = null; });
  cv.addEventListener("dblclick", () => { user = null; redraw(); });

  // --- the scene's box and the mapping ------------------------------------------------------------------------------
  function launch() { return (header && header.launcher) || { h: 0, angle: 0, v0: 0 }; }
  function sceneBox() {
    const all = [];
    const add = (h) => { const b = h && h.scene && h.scene.box; if (b) all.push(b); };
    if (story) for (const W of story.worlds) add(W.header);  // Watch: one box for the whole recording
    else add(header);
    for (const tr of traces) add(tr.W && tr.W.header);
    let x0 = 0, x1 = 0.5, y1 = 0.3;
    for (const [[a], [b, c]] of all) { x0 = Math.min(x0, a); x1 = Math.max(x1, b); y1 = Math.max(y1, c); }
    const span = Math.max(x1 - x0, y1, 0.5);
    const table = Math.max(0.12 * span, 0.15);  // the table (or the launcher's foot) to the left of the launch point
    return { x0: x0 - table, x1: x1 + 0.04 * span, y0: -0.06 * span, y1: y1 + 0.08 * span, span };
  }
  function makeMap(W, H, minTop = 0) {
    if (user) {
      const { k, ox, oy } = user;
      return { k, ox, oy, toPx: ([x, y]) => [ox + x * k, oy - y * k], toWorld: ([px, py]) => [(px - ox) / k, (oy - py) / k] };
    }
    const b = sceneBox(), Hs = H - captionRoom();
    // (TOP: a line kept free above the scene for the ball's name; minTop: the legend's rows under a phone's readouts)
    const top = Math.max(TOP * (story && story.earlier.length && W < 600 ? 2 : 1), minTop - PAD);  // a second line: the earlier throws (phone)
    const k = Math.max(1e-9, Math.min((W - 2 * PAD) / (b.x1 - b.x0), (Hs - 2 * PAD - top) / (b.y1 - b.y0)));
    const ox = PAD + ((W - 2 * PAD) - (b.x1 - b.x0) * k) / 2 - b.x0 * k;
    const oy = Hs - PAD + b.y0 * k;  // the floor stays low in the view: the room left over is sky
    return { k, ox, oy, toPx: ([x, y]) => [ox + x * k, oy - y * k], toWorld: ([px, py]) => [(px - ox) / k, (oy - py) / k] };
  }

  // Watch lays its caption over the bottom of the stage (wide screens): the scene keeps above it a band of a fixed
  // height (its bottom offset, its padding and two lines of its text, three on a narrower stage, and the floor's
  // numbers), so that the scale does not change from caption to caption and the caption covers no landing (D8)
  function captionRoom() {
    if (ctx.screen !== "watch") return 0;
    const cap = cv.closest(".dm-stage") && cv.closest(".dm-stage").querySelector(".dm-caption");
    if (!cap) return 0;
    const cs = getComputedStyle(cap);
    if (cs.position !== "absolute") return 0;  // a caption in its own place (a phone): nothing to leave
    const fs = parseFloat(cs.fontSize) || 16, lh = parseFloat(cs.lineHeight) || 1.35 * fs;
    const lines = cv.clientWidth > 900 ? 2 : 3;
    return (parseFloat(cs.bottom) || 0) + (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0)
      + lines * lh + 26;
  }

  // a label's box kept free of the labels drawn before it in this frame: moved up (or down) by a line until it fits,
  // and kept inside the canvas
  function freeSpot(x, y, w, align, dir = -1) {
    const W = cv.clientWidth, h = 15;
    let x0 = align === "right" ? x - w : align === "center" ? x - w / 2 : x;
    x0 = Math.max(4, Math.min(x0, W - 4 - w));
    let y1 = Math.min(Math.max(y, 14), cv.clientHeight - 4);
    for (let k = 0; k < 8; k++) {
      const r = { x0, x1: x0 + w, y0: y1 - h + 3, y1: y1 + 3 };
      if (!placed.some((q) => r.x0 < q.x1 && q.x0 < r.x1 && r.y0 < q.y1 && q.y0 < r.y1)) { placed.push(r); break; }
      y1 += dir * 16;
    }
    return { x: x0, y: y1 };
  }
  function textWidth(g, text, bold) { g.save(); g.font = `${bold ? "600 " : ""}13px system-ui, sans-serif`; const w = g.measureText(text).width; g.restore(); return w; }
  // a label placed free of the others (left-aligned at the returned spot)
  function placeLabel(g, text, x, y, { color = null, align = "left", bold = false, dir = -1, alpha = 1, bg = false } = {}) {
    const w = textWidth(g, text, bold), p = freeSpot(x, y, w, align, dir);
    g.save(); g.globalAlpha = alpha;
    if (bg) { g.fillStyle = css("--canvas") || "#fff"; g.globalAlpha = 0.85 * alpha; g.fillRect(p.x - 2, p.y - 12, w + 4, 16); g.globalAlpha = alpha; }
    label(g, text, p.x, p.y, { color, bold }); g.restore();
  }

  // --- drawing parts ----------------------------------------------------------------------------------------------
  const ink = () => css("--ink") || "#222", muted = () => css("--muted") || "#888", gridc = () => css("--grid") || "#ddd";
  function line(g, a, b) { g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  function arrow(g, p, dx, dy, color, width = 2) {
    const len = Math.hypot(dx, dy);
    if (!(len > 1)) return;
    g.save(); g.strokeStyle = color; g.fillStyle = color; g.lineWidth = width;
    const q = [p[0] + dx, p[1] + dy], ux = dx / len, uy = dy / len, hw = Math.min(7, 0.4 * len);
    line(g, p, [q[0] - ux * hw * 0.8, q[1] - uy * hw * 0.8]);
    g.beginPath(); g.moveTo(q[0], q[1]); g.lineTo(q[0] - ux * hw * 1.6 - uy * hw * 0.7, q[1] - uy * hw * 1.6 + ux * hw * 0.7);
    g.lineTo(q[0] - ux * hw * 1.6 + uy * hw * 0.7, q[1] - uy * hw * 1.6 - ux * hw * 0.7); g.closePath(); g.fill();
    g.restore();
  }
  function label(g, text, x, y, { color = null, align = "left", base = "alphabetic", bold = false } = {}) {
    g.save(); g.font = `${bold ? "600 " : ""}13px system-ui, sans-serif`; g.fillStyle = color || ink();
    g.textAlign = align; g.textBaseline = base; g.fillText(text, x, y); g.restore();
  }
  function floorAndScale(g, W) {
    const [, fy] = map.toPx([0, 0]);
    g.save();
    g.fillStyle = css("--panel") || "#f1f3f5"; g.globalAlpha = 0.6; g.fillRect(0, fy, W, Math.max(0, cv.clientHeight - fy)); g.globalAlpha = 1;
    g.strokeStyle = ink(); g.lineWidth = 1.5; line(g, [0, fy], [W, fy]);
    if (ctx.screen !== "lab") {  // in the lab the instruments measure (the tape is drawn by the screen)
      const [x0] = map.toWorld([0, 0]), [x1] = map.toWorld([W, 0]);
      const step = niceStep(x1 - x0, Math.max(3, Math.round(W / 110)));
      g.strokeStyle = muted(); g.lineWidth = 1;
      for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) {
        const [px] = map.toPx([x, 0]);
        line(g, [px, fy], [px, fy + 6]);
        if (px < W - 26) label(g, `${num(Math.abs(x) < 1e-12 ? 0 : x, 4)}`, px, fy + 8, { color: muted(), align: "center", base: "top" });
      }
      label(g, t("m"), W - 6, fy + 8, { color: muted(), align: "right", base: "top" });
    }
    g.restore();
  }
  function launcher(g) {
    const L = launch(), p = map.toPx([0, L.h]), [, fy] = map.toPx([0, 0]);
    const a = (L.angle * Math.PI) / 180, chute = L.angle === 0 && L.h > 0, R = 26;
    // the launcher's shape first, as a box that the labels keep clear of (V52 (e): the barrel was drawn over «h = 1 m»):
    // a chute is a quarter circle ending horizontally at the launch point; a barrel lies along the launch direction, its
    // muzzle at the launch point, never below the floor (review R-W F16): shortened to the room above it, and from the
    // floor itself (no room) it lies forward on a mount, its breech at the launch point
    const room = a > 0 ? (fy - p[1]) / Math.sin(a) - 1 : Infinity, len = Math.min(28, room);
    const barrel = chute ? null : len >= 10 ? [[p[0] - len * Math.cos(a), p[1] + len * Math.sin(a)], p]
      : [p, [p[0] + 28 * Math.cos(a), p[1] - 28 * Math.sin(a)]];
    const box = chute ? { x0: p[0] - R - 2, x1: p[0] + 2, y0: p[1] - R - 2, y1: p[1] + 2 }
      : { x0: Math.min(barrel[0][0], barrel[1][0]) - 4, x1: Math.max(barrel[0][0], barrel[1][0]) + 4,
          y0: Math.min(barrel[0][1], barrel[1][1]) - 4, y1: Math.max(barrel[0][1], barrel[1][1]) + 4 };
    if (!chute && len < 10 && L.h <= 0) box.y1 = Math.max(box.y1, fy);  // the mount
    placed.push(box);
    const lay = { W: cv.clientWidth, H: cv.clientHeight, launcher: [box.x0, box.y0, box.x1, box.y1], hLabel: null, hWhere: null };
    g.save();
    if (L.h > 0) {  // the table
      const w = Math.max(40, 0.12 * sceneBox().span * map.k);
      g.fillStyle = css("--chip") || "#dee2e6"; g.strokeStyle = ink(); g.lineWidth = 1;
      g.fillRect(p[0] - w, p[1], w, 6); g.strokeRect(p[0] - w, p[1], w, 6);
      g.lineWidth = 3; g.strokeStyle = muted();
      line(g, [p[0] - w + 6, p[1] + 6], [p[0] - w + 6, fy]); line(g, [p[0] - 6, p[1] + 6], [p[0] - 6, fy]);
    }
    g.strokeStyle = ink(); g.lineCap = "round";
    if (chute) { g.lineWidth = 3; g.beginPath(); g.arc(p[0], p[1] - R, R, Math.PI / 2, Math.PI, false); g.stroke(); }
    else {
      g.lineWidth = 7; g.globalAlpha = 0.8;
      line(g, barrel[0], barrel[1]);
      if (len < 10 && L.h <= 0) { g.globalAlpha = 1; g.fillStyle = muted(); g.beginPath(); g.arc(p[0], fy, 9, Math.PI, 2 * Math.PI); g.fill(); }
      g.globalAlpha = 1;
    }
    g.restore();
    if (L.h > 0 && ctx.screen !== "lab") {
      const w = Math.max(40, 0.12 * sceneBox().span * map.k), r = heightLabel(g, L, p, fy, w, box);
      lay.hLabel = r && [r.x0, r.y0, r.x1, r.y1]; lay.hWhere = r && r.where;
    }
    cv.__layout = lay;  // what this frame drew where: the launcher, «h = …», the drag arrow and its legend (tests/s03_screens.mjs)
  }
  // «h = … m» beside the table, clear of the launcher and of the labels drawn before it, inside the view: left of the
  // table at the middle of its legs; else between the legs (over a backing) when they are a line high, centred or left
  // of the launcher; else over the table's top, left of the launcher, lifted line by line until it is free
  function heightLabel(g, L, p, fy, w, box) {
    const text = t("h = {h} m", { h: num(L.h, 3) }), tw = textWidth(g, text, false), W = cv.clientWidth, H = cv.clientHeight;
    const legTop = p[1] + 6, mid = Math.min((legTop + fy) / 2 + 5, fy - 5), legs = fy - legTop >= 20;
    const left = Math.min(p[0], box.x0);
    const cands = [[p[0] - w - 6 - tw, mid, false, "left of the table"]];
    if (legs) cands.push([p[0] - w / 2 - tw / 2, mid, true, "between the legs"], [left - 4 - tw, mid, true, "between the legs, left of the launcher"]);
    for (let k = 0, y = Math.min(p[1], box.y0) - 6; k < 12; k++, y -= 16) cands.push([Math.max(4, left - 6 - tw), y, false, "over the table"]);
    for (const [x, y, bg, where] of cands) {
      const r = { x0: x, x1: x + tw, y0: y - 12, y1: y + 4, where };
      if (r.x0 < 4 || r.x1 > W - 4 || r.y0 < 2 || r.y1 > H - 2) continue;
      if (placed.some((q) => r.x0 < q.x1 && q.x0 < r.x1 && r.y0 < q.y1 && q.y0 < r.y1)) continue;
      placed.push(r);
      g.save();
      if (bg) { g.fillStyle = css("--canvas") || "#fff"; g.globalAlpha = 0.85; g.fillRect(r.x0 - 2, r.y0, tw + 4, 16); g.globalAlpha = 1; }
      label(g, text, x, y, { color: muted() });
      g.restore();
      return r;
    }
    return null;  // no free place in the view (none on the computed grid: s03_screens.mjs)
  }
  function pathOf(g, c, upto, color, { alpha = 1, dash = null, width = 2, end = null, now = null } = {}) {
    if (!c.t.length) return;
    g.save(); g.globalAlpha = alpha; g.strokeStyle = color; g.lineWidth = width; if (dash) g.setLineDash(dash);
    g.beginPath();
    let n = 0;
    for (let j = 0; j < c.t.length; j++) {
      if (c.t[j] > upto + 1e-9) break;
      const [px, py] = map.toPx([c.x[j], c.y[j]]);
      if (n++) g.lineTo(px, py); else g.moveTo(px, py);
    }
    if (end && end.t <= upto + 1e-9) { const [px, py] = map.toPx([end.x, 0]); g.lineTo(px, py); }
    else if (now && n) { const [px, py] = map.toPx(now); g.lineTo(px, py); }  // up to the ball's computed position
    g.stroke(); g.restore();
  }
  function strobe(g, c, upto, color) {
    const every = (header && header.strobe_every) || 6;
    g.save(); g.fillStyle = color;
    for (let j = 0; j < c.t.length; j++) {
      if (c.t[j] > upto + 1e-9) break;
      if (c.i[j] % every) continue;
      const [px, py] = map.toPx([c.x[j], c.y[j]]);
      g.beginPath(); g.arc(px, py, 3.2, 0, 2 * Math.PI); g.fill();
    }
    g.restore();
  }
  function ball(g, x, y, color, d) {
    const [px, py] = map.toPx([x, y]), r = Math.max(5, 0.5 * d * map.k);
    g.save(); g.fillStyle = color; g.strokeStyle = ink(); g.lineWidth = 1;
    g.beginPath(); g.arc(px, py - (y <= 0 ? r : 0), r, 0, 2 * Math.PI); g.fill(); g.stroke(); g.restore();
    return [px, py];
  }
  // a landing's mark and label: its place is taken now (before the earlier throws' labels, which give way), and it
  // is painted by the returned function after the paths, so that no path crosses its text
  function landMark(g, x, color, text, short = null) {
    const [px, py] = map.toPx([x, 0]);
    let spot = null;
    if (text) {  // beside the mark, on the side that keeps the text inside the view, free of the other labels; on a
      // narrow view a label that would cross the path (left of the mark) is the short one
      let w = textWidth(g, text, true), right = px + 5 + w > cv.clientWidth - 4;
      if (right && short && cv.clientWidth < 600) { text = short; w = textWidth(g, text, true); right = px + 5 + w > cv.clientWidth - 4; }
      spot = freeSpot(right ? px - 5 : px + 5, py - 12, w, right ? "right" : "left", -1);
    }
    return () => {
      g.save(); g.strokeStyle = color; g.lineWidth = 2; line(g, [px, py - 9], [px, py + 9]); g.restore();
      if (spot) label(g, text, spot.x, spot.y, { color, bold: true });
    };
  }
  // fixed decimals for the school's numbers (review R-W F17): metres to the centimetre, seconds to the millisecond
  const m2 = (x) => fmt(x, ".2f"), s3 = (x) => fmt(x, ".3f");
  // the drag arrows' enlargement against the weight's scale (V52 (f)): the 1, 2 or 5 × 10ⁿ at or below 2 · weight /
  // drag_max (the run's computed largest drag of the flight), so that the longest drag arrow is at most twice the
  // weight's (120 px) and, when enlarged, at least 48 px: at the top of a 45° throw the drag is then a clear arrow, not a
  // tip under the ball; 1 (the weight's own scale) when that is under 2
  function dragScale() {
    const W = header && header.weight, F = header && header.drag_max, r = 2 * W / F;
    return W > 0 && F > 0 && r >= 2 ? nice(r) : 1;
  }
  function legendArrow(g, x, y, px, text, color) {
    arrow(g, [x, y], px, 0, color, 2);
    label(g, text, x + px + 8, y + 4, { color });
  }
  // the arrows' legend, a row each (the velocity's, the weight's, the drag's scale), from the overlays shown and the
  // header only, so that the scale of the scene does not change from frame to frame
  function velScale() {
    const L = launch(), vmax = Math.max(L.v0, Math.sqrt(2 * (header.g || 9.8) * Math.max(L.h, 0)), 1);
    return { vmax, sv: 70 / vmax };  // pixels per m/s
  }
  function legendRows() {
    const rows = [];
    if (on.v || on.v_parts) {
      const { vmax, sv } = velScale(), ref = nice(vmax / 2);
      rows.push({ px: ref * sv, text: t("{v} m/s", { v: num(ref, 3) }), color: COLORS.v });
    }
    if (on.forces && header.weight) {
      const sd = (60 / header.weight) * dragScale(), m = dragScale();
      rows.push({ px: 60, text: t("weight mg = {F} N", { F: num(header.weight, 3) }), color: COLORS.g });
      if (header.air && header.drag_max > 0) {  // the drag's own scale: an arrow (at most the weight's 60 px) of a round force
        const fr = nice(Math.min(header.drag_max, 60 / sd));
        rows.push({ px: fr * sd, color: COLORS.drag, drag: true, text: m > 1 ? t("drag, enlarged ×{m}: {F} N", { m: num(m, 3), F: num(fr, 3) })
          : t("drag, on the weight's scale: {F} N", { F: num(fr, 3) }) });
      }
    }
    return rows;
  }
  // where the rows go: from the top left; on a phone, where Explore lays its readouts over the view's top right corner
  // (a box whose width changes as its values appear), always under that box, with the scene kept below the rows
  // (makeMap's minTop), so that no row runs under the readouts or over the path and the scale stays put during a flight
  // (V52 (f): the drag's scale must be read)
  let roBottom = 0;  // the lowest the readouts' box has reached in this view
  function legendPlace(g, rows, y) {
    if (!rows.length) return { y, under: false, bottom: 0, rows: null, box: null };
    const ro = ctx.screen === "explore" && cv.closest(".dm-stage") ? cv.closest(".dm-stage").querySelector(":scope > .dm-readouts") : null;
    const a = ro && ro.getBoundingClientRect(), c = cv.getBoundingClientRect();
    const right = Math.max(...rows.map((r) => 12 + r.px + 8 + textWidth(g, r.text, false)));
    const box = a && a.width > 0 && a.height > 0 ? [a.left - c.left, a.top - c.top, a.right - c.left, a.bottom - c.top] : null;
    if (box) roBottom = Math.max(roBottom, box[3]);
    const under = !!box && y - 12 < roBottom;
    if (under) y = Math.max(y, roBottom + 18);
    const bottom = y + 20 * (rows.length - 1) + 5;
    return { y, under, bottom, box, rows: [12, y - 12, right, bottom] };
  }

  function drawTraces(g) {
    for (const tr of traces) {
      const v = tr.W && tr.W.view;
      if (!v || !v.samples) continue;
      const c = v.samples(), ld = v.landingData ? v.landingData() : null;
      pathOf(g, c, tr.t, ink(), { alpha: tr.alpha ?? 0.35, width: 1.5, end: ld });
      if (ld && ld.t <= tr.t + 1e-9) {
        const [px, py] = map.toPx([ld.x, 0]);
        g.save(); g.globalAlpha = Math.min(1, (tr.alpha ?? 0.35) + 0.25); g.strokeStyle = ink(); line(g, [px, py - 5], [px, py + 5]); g.restore();
        // its label above the mark, inside the canvas (right-aligned near the right edge), free of the other labels
        // (review R-W F11, R-P F8)
        if (tr.label) {
          const w = textWidth(g, tr.label, false), right = px + 3 + w > cv.clientWidth - 4;
          placeLabel(g, tr.label, right ? px - 3 : px + 3, py - 12, { color: muted(), align: right ? "right" : "left",
            alpha: Math.min(1, (tr.alpha ?? 0.35) + 0.3) });
        }
      }
    }
  }

  // Watch: the recording's earlier throws, faded, each with its landing mark and its range (setStory)
  function drawStory(g) {
    if (!story) return;
    // their ranges: beside their marks on a wide view; on a narrow one, where three labels do not fit between the
    // marks, in one line under the ball's name
    const narrow = cv.clientWidth < 600, ranges = [];
    for (const e of story.earlier) {
      pathOf(g, e.main, Infinity, COLORS.main, { alpha: 0.3, width: 1.5, end: e.landing });
      if (e.landing) {
        const [px, py] = map.toPx([e.landing.x ?? e.landing.L, 0]);
        g.save(); g.globalAlpha = 0.55; g.strokeStyle = COLORS.main; g.lineWidth = 2; line(g, [px, py - 7], [px, py + 7]); g.restore();
        const text = t("L = {L} m", { L: m2(e.landing.L) }), w = textWidth(g, text, false), right = px + 5 + w > cv.clientWidth - 4;
        if (narrow) ranges.push(text);
        else placeLabel(g, text, right ? px - 5 : px + 5, py - 12, { color: muted(), align: right ? "right" : "left" });
      }
    }
    if (ranges.length) placeLabel(g, t("earlier throws: {list}", { list: ranges.join("; ") }), 12, 36, { color: muted(), dir: 1 });
    return ranges.length > 0;
  }
  // the earlier throws of a decoded world, read from its own messages (the samples and the landing): nothing computed
  function throwOf(W) {
    const c = cols();
    let ld = null;
    for (const m of W.viewMsgs || []) {
      const meta = m.meta;
      if (meta.type === "traj" && meta.body !== "other" && m.blobs && m.blobs.s) push(c, meta, m.blobs.s);
      else if (meta.type === "event" && meta.kind === "landing") ld = { ...meta.data, T: meta.data.T ?? meta.t };
    }
    return { main: c, landing: ld };
  }

  function energyBars(g, W, f) {
    const m = f.meas || {}, ek = m.E_k, ep = m.E_p, q = m.Q || 0;
    if (ek === undefined || ep === undefined) return;
    const e0 = ek + ep + q;
    if (!(e0 > 0)) return;
    const bw = Math.min(170, W * 0.36), x = W - bw - 14, rows = [["kinetic energy", ek, COLORS.ek], ["potential energy", ep, COLORS.ep]];
    // i18n-msgids: "kinetic energy" "potential energy"
    if (header && header.air) rows.push(["heat (air)", q, COLORS.q]);  // i18n-msgids: "heat (air)"
    g.save();
    label(g, t("Energy, J"), x, 18, { bold: true });
    rows.forEach(([name, val, col], j) => {  // a row of 34 px: the bar, then its label under it (review R-W F15)
      const y = 28 + j * 34;
      g.fillStyle = col; g.fillRect(x, y, Math.max(0, bw * val / e0), 12);
      g.strokeStyle = muted(); g.strokeRect(x, y, bw, 12);
      label(g, `${t(name)} ${num(val, 3)}`, x, y + 27, { color: muted() });
    });
    g.restore();
  }

  // --- the view's API -----------------------------------------------------------------------------------------------
  const api = {
    center,
    quantSafe: QUANT_SAFE,
    overlays: OVERLAYS.map((o) => ({ ...o, label: t(o.label) })),
    setOverlay(id, v) { touched.add(id); on[id] = !!v; const b = boxes.find((x) => x.id === id); if (b) b.cb.checked = !!v; redraw(); },
    setTraces(list) { traces = list || []; redraw(); },
    // Watch (D8): the recording's worlds and the one shown; the box over all of them, the earlier ones as traces
    setStory(s) {
      if (!s || !s.worlds || !s.worlds.length) { story = null; redraw(); return; }
      const w = Math.max(0, Math.min(s.w | 0, s.worlds.length - 1));
      if (!story || story.worlds !== s.worlds) story = { worlds: s.worlds, w, all: s.worlds.map(throwOf) };
      story.w = w; story.earlier = story.all.slice(0, w);
      user = null; redraw();
    },
    worldToPx(p) { return map ? map.toPx(p) : [NaN, NaN]; },
    pxToWorld(q) { return map ? map.toWorld(q) : [NaN, NaN]; },
    // for the lab's instruments: the launch point, the floor's height, the landing point once reached
    anchors() { const L = launch(); return { launch: [0, L.h], floor: 0, angle: L.angle, landing: landing ? [landing.L, 0] : null }; },
    samples() { return main; },
    landingData() { return landing ? { t: landing.T, x: landing.x ?? landing.L } : null; },
    reset() { header = null; main = cols(); other = cols(); apex = landing = oland = null; },
    snapshot() { return { nm: main.t.length, no: other.t.length, apex, landing, oland }; },
    restore(k) { cut(main, k.nm); cut(other, k.no); apex = k.apex; landing = k.landing; oland = k.oland; },
    onHeader(h) {
      header = h; main = cols(); other = cols(); apex = landing = oland = null;
      // a comparison is told with the dots every 0.1 s unless the experimenter chose otherwise
      if (!touched.has("strobe")) { on.strobe = h.companion && h.companion !== "none" ? true : OVERLAYS[1].default; const b = boxes.find((x) => x.id === "strobe"); if (b) b.cb.checked = on.strobe; }
    },
    onMessage(meta, blobs) {
      if (meta.type === "traj" && blobs && blobs.s) push(meta.body === "other" ? other : main, meta, blobs.s);
      else if (meta.type === "event" && meta.kind === "apex") apex = meta.data;
      else if (meta.type === "event" && meta.kind === "landing") landing = { ...meta.data, T: meta.data.T ?? meta.t };
      else if (meta.type === "event" && meta.kind === "companion_landing") oland = { ...meta.data, T: meta.data.T ?? meta.t };
    },
    help() {
      return el("div", {}, el("p", {}, t("Drag the scene to move it, turn the wheel to zoom, double-click to fit it again.")),
        el("p", {}, t("The dots are the computed positions every 0.1 s; the arrows are the computed velocity and forces, drawn to the scale written next to them.")));
    },
    render(frame) {
      const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, H = cv.clientHeight;
      if (!W || !H) return;
      if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
      const g = fresh2d(cv.getContext("2d"), dpr);
      g.fillStyle = css("--canvas") || "#fff"; g.fillRect(0, 0, W, H);
      if (!header) return;
      // which ball flies (review R-W F12): its label, or its size and mass where the label does not fit; first, so
      // that the other labels keep clear of it
      // (on a phone Explore lays its readouts over the view's top right corner: about 180 px are kept for them)
      const bl = header.ball || {}, room = W - 24 - (on.energy ? Math.min(170, W * 0.36) + 14 : 0)
        - (ctx.screen === "explore" && W < 600 ? 180 : 0);
      let ballText = bl.label ? t(bl.label) : "";
      if (ballText && textWidth(g, ballText, false) > room) ballText = t("ball {d} mm, {m} g", { d: num(1000 * bl.d, 3), m: num(1000 * bl.m, 3) });
      const rows = legendRows(), lp = legendPlace(g, rows, 18 + (ballText ? 22 : 0));
      map = makeMap(W, H, lp.under ? lp.bottom + 8 : 0);
      placed = [];
      const tNow = frame && frame.t !== undefined ? frame.t : Infinity;
      if (ballText) placeLabel(g, ballText, 12, 18, { color: muted() });
      floorAndScale(g, W);
      launcher(g);  // first, so that the labels of the traces keep clear of its own
      cv.__layout.legend = { rows: lp.rows, readouts: lp.box, pathTop: map.toPx([0, sceneBox().y1 - 0.08 * sceneBox().span])[1] };
      // the landings shown now are labelled before the earlier throws, so that theirs give way
      const comp = header.companion, ocol = comp === "drop" ? COLORS.drop : COLORS.vacuum;
      const late = [];
      if (landing && landing.T <= tNow + 1e-9) {
        late.push(landMark(g, landing.x ?? landing.L, COLORS.main, ctx.screen === "lab" ? null
          : t("L = {L} m, T = {T} s", { L: m2(landing.L), T: s3(landing.T) }), t("L = {L} m", { L: m2(landing.L) })));
      }
      if (oland && oland.T <= tNow + 1e-9 && comp === "vacuum") late.push(landMark(g, oland.x ?? oland.L, COLORS.vacuum, ctx.screen === "lab" ? null : t("L = {L} m", { L: m2(oland.L) })));
      const storyLine = drawStory(g);
      drawTraces(g);
      if (on.path) {
        pathOf(g, other, tNow, ocol, { dash: [6, 4], width: 1.5, end: oland, now: frame && frame.other ? [frame.other.x, frame.other.y] : null });
        pathOf(g, main, tNow, COLORS.main, { width: 2, end: landing, now: frame ? [frame.x, frame.y] : null });
      }
      if (on.strobe) { strobe(g, other, tNow, ocol); strobe(g, main, tNow, COLORS.main); }
      if (apex && on.path && apex.t <= tNow + 1e-9 && ctx.screen !== "lab") {
        const [px, py] = map.toPx([apex.x, apex.H]), [, fy] = map.toPx([apex.x, 0]);
        g.save(); g.strokeStyle = muted(); g.setLineDash([3, 4]); line(g, [px, py], [px, fy]); g.restore();
        placeLabel(g, t("H = {H} m", { H: m2(apex.H) }), px + 5, py - 6, { color: muted() });
      }
      for (const paint of late) paint();
      if (!frame) return;
      const d = (header.ball && header.ball.d) || 0.02;
      if (frame.other) ball(g, frame.other.x, frame.other.y, ocol, d);
      const bp = ball(g, frame.x, frame.y, COLORS.main, d);
      const { sv } = velScale();
      const flying = !frame.landed;
      if ((on.v || on.v_parts) && flying) {
        if (on.v) arrow(g, bp, frame.vx * sv, -frame.vy * sv, COLORS.v, 2.5);
        if (on.v_parts) {
          g.save(); g.setLineDash([4, 3]);
          arrow(g, bp, frame.vx * sv, 0, COLORS.v, 1.5); arrow(g, bp, 0, -frame.vy * sv, COLORS.v, 1.5);
          g.restore();
        }
      }
      if (on.forces && flying && header.weight) {
        const sf = 60 / header.weight;  // pixels per newton: the weight is 60 px
        // the drag on a scale of its own (V52 (f)): enlarged ×m against the weight's scale (dragScale), so that it is seen
        // at the top of the path too; the arrow at the ball and the legend say «×m», so the two arrows' lengths are never
        // read as one scale when they are not
        const m = dragScale(), sd = sf * m;
        arrow(g, bp, 0, header.weight * sf, COLORS.g, 2.5);
        label(g, t("mg"), bp[0] + 6, bp[1] + header.weight * sf, { color: COLORS.g });
        if (frame.F_drag) {
          arrow(g, bp, frame.F_drag[0] * sd, -frame.F_drag[1] * sd, COLORS.drag, 2.5);
          if (cv.__layout) cv.__layout.drag = { m, px: Math.hypot(frame.F_drag[0], frame.F_drag[1]) * sd };
          label(g, m > 1 ? t("drag ×{m}", { m: num(m, 3) }) : t("drag"), bp[0] + frame.F_drag[0] * sd - 8, bp[1] - frame.F_drag[1] * sd + 16, { color: COLORS.drag, align: "right" });
        }
      }
      if (flying && rows.length) {  // the legend: under a phone's readouts (lp), else from the top left, under the earlier throws' line
        let y = lp.under ? lp.y : 18 + (ballText ? 22 : 0) + (storyLine ? 20 : 0);
        for (const r of rows) { legendArrow(g, 12, y, r.px, r.text, r.color); y += 20; }
        const dr = rows.find((r) => r.drag);
        if (dr) cv.__layout.dragLegend = dr.text;
      }
      if (on.energy) energyBars(g, W, frame);
    },
  };
  return api;
}
