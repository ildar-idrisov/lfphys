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
// own decoded world), `worldToPx` / `pxToWorld` and `anchors()` for the lab's instruments, `quantSafe`. A view's own
// toolbar of overlays is shown where no screen panel offers them (a live run, a recording, Watch).
import { t } from "/static/js/i18n.js";
import { css, el, fresh2d, num } from "/static/js/ui.js";

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
  const toolbar = embedded ? null : el("div", { class: "toolbar" }, el("span", { class: "muted" }, t("Show")), boxes.map((b) => b.label));
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
    add(header);
    for (const tr of traces) add(tr.W && tr.W.header);
    let x0 = 0, x1 = 0.5, y1 = 0.3;
    for (const [[a], [b, c]] of all) { x0 = Math.min(x0, a); x1 = Math.max(x1, b); y1 = Math.max(y1, c); }
    const span = Math.max(x1 - x0, y1, 0.5);
    const table = Math.max(0.12 * span, 0.15);  // the table (or the launcher's foot) to the left of the launch point
    return { x0: x0 - table, x1: x1 + 0.04 * span, y0: -0.06 * span, y1: y1 + 0.08 * span, span };
  }
  function makeMap(W, H) {
    if (user) {
      const { k, ox, oy } = user;
      return { k, ox, oy, toPx: ([x, y]) => [ox + x * k, oy - y * k], toWorld: ([px, py]) => [(px - ox) / k, (oy - py) / k] };
    }
    const b = sceneBox();
    const k = Math.max(1e-9, Math.min((W - 2 * PAD) / (b.x1 - b.x0), (H - 2 * PAD) / (b.y1 - b.y0)));
    const ox = PAD + ((W - 2 * PAD) - (b.x1 - b.x0) * k) / 2 - b.x0 * k;
    const oy = H - PAD + b.y0 * k;  // the floor stays low in the view: the room left over is sky
    return { k, ox, oy, toPx: ([x, y]) => [ox + x * k, oy - y * k], toWorld: ([px, py]) => [(px - ox) / k, (oy - py) / k] };
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
        label(g, `${num(Math.abs(x) < 1e-12 ? 0 : x, 4)}`, px, fy + 8, { color: muted(), align: "center", base: "top" });
      }
      label(g, t("m"), W - 6, fy + 8, { color: muted(), align: "right", base: "top" });
    }
    g.restore();
  }
  function launcher(g) {
    const L = launch(), p = map.toPx([0, L.h]), [, fy] = map.toPx([0, 0]);
    g.save();
    if (L.h > 0) {  // the table
      const w = Math.max(40, 0.12 * sceneBox().span * map.k);
      g.fillStyle = css("--chip") || "#dee2e6"; g.strokeStyle = ink(); g.lineWidth = 1;
      g.fillRect(p[0] - w, p[1], w, 6); g.strokeRect(p[0] - w, p[1], w, 6);
      g.lineWidth = 3; g.strokeStyle = muted();
      line(g, [p[0] - w + 6, p[1] + 6], [p[0] - w + 6, fy]); line(g, [p[0] - 6, p[1] + 6], [p[0] - 6, fy]);
      if (ctx.screen !== "lab") label(g, t("h = {h} m", { h: num(L.h, 3) }), p[0] - w / 2, (p[1] + fy) / 2, { color: muted(), align: "center", base: "middle" });
    }
    const a = (L.angle * Math.PI) / 180;
    g.strokeStyle = ink(); g.lineCap = "round";
    if (L.angle === 0 && L.h > 0) {  // a chute: a curved ramp ending horizontally at the launch point
      const r = 26;
      g.lineWidth = 3; g.beginPath(); g.arc(p[0], p[1] - r, r, Math.PI / 2, Math.PI, false); g.stroke();
    } else {  // a launcher's barrel along the launch direction
      g.lineWidth = 7; g.globalAlpha = 0.8;
      line(g, [p[0] - 28 * Math.cos(a), p[1] + 28 * Math.sin(a)], p);
      g.globalAlpha = 1;
    }
    g.restore();
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
  function landMark(g, x, color, text) {
    const [px, py] = map.toPx([x, 0]);
    g.save(); g.strokeStyle = color; g.lineWidth = 2; line(g, [px, py - 9], [px, py + 9]); g.restore();
    if (text) {  // beside the mark, on the side that keeps the text inside the view
      g.save(); g.font = "600 13px system-ui, sans-serif"; const w = g.measureText(text).width; g.restore();
      const right = px + 5 + w > cv.clientWidth - 4;
      label(g, text, right ? px - 5 : px + 5, py - 12, { color, bold: true, align: right ? "right" : "left" });
    }
  }
  function legendArrow(g, x, y, px, text, color) {
    arrow(g, [x, y], px, 0, color, 2);
    label(g, text, x + px + 8, y + 4, { color });
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
        if (tr.label) { g.save(); g.globalAlpha = Math.min(1, (tr.alpha ?? 0.35) + 0.3); label(g, tr.label, px + 3, py + 20, { color: muted() }); g.restore(); }
      }
    }
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
    rows.forEach(([name, val, col], j) => {
      const y = 28 + j * 22;
      g.fillStyle = col; g.fillRect(x, y, Math.max(0, bw * val / e0), 12);
      g.strokeStyle = muted(); g.strokeRect(x, y, bw, 12);
      label(g, `${t(name)} ${num(val, 3)}`, x, y + 24 - 2, { color: muted() });
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
      map = makeMap(W, H);
      const tNow = frame && frame.t !== undefined ? frame.t : Infinity;
      floorAndScale(g, W);
      drawTraces(g);
      launcher(g);
      const comp = header.companion, ocol = comp === "drop" ? COLORS.drop : COLORS.vacuum;
      if (on.path) {
        pathOf(g, other, tNow, ocol, { dash: [6, 4], width: 1.5, end: oland, now: frame && frame.other ? [frame.other.x, frame.other.y] : null });
        pathOf(g, main, tNow, COLORS.main, { width: 2, end: landing, now: frame ? [frame.x, frame.y] : null });
      }
      if (on.strobe) { strobe(g, other, tNow, ocol); strobe(g, main, tNow, COLORS.main); }
      if (apex && on.path && apex.t <= tNow + 1e-9 && ctx.screen !== "lab") {
        const [px, py] = map.toPx([apex.x, apex.H]), [, fy] = map.toPx([apex.x, 0]);
        g.save(); g.strokeStyle = muted(); g.setLineDash([3, 4]); line(g, [px, py], [px, fy]); g.restore();
        label(g, t("H = {H} m", { H: num(apex.H, 3) }), px + 5, py - 6, { color: muted() });
      }
      if (oland && oland.T <= tNow + 1e-9 && comp === "vacuum") landMark(g, oland.x ?? oland.L, COLORS.vacuum, ctx.screen === "lab" ? null : t("L = {L} m", { L: num(oland.L, 4) }));
      if (landing && landing.T <= tNow + 1e-9) {
        landMark(g, landing.x ?? landing.L, COLORS.main, ctx.screen === "lab" ? null
          : t("L = {L} m, T = {T} s", { L: num(landing.L, 4), T: num(landing.T, 3) }));
      }
      if (!frame) return;
      const d = (header.ball && header.ball.d) || 0.02;
      if (frame.other) ball(g, frame.other.x, frame.other.y, ocol, d);
      const bp = ball(g, frame.x, frame.y, COLORS.main, d);
      const L = launch(), vmax = Math.max(L.v0, Math.sqrt(2 * (header.g || 9.8) * Math.max(L.h, 0)), 1);
      const sv = 70 / vmax;  // pixels per m/s
      let legendY = 18;
      const flying = !frame.landed;
      if ((on.v || on.v_parts) && flying) {
        if (on.v) arrow(g, bp, frame.vx * sv, -frame.vy * sv, COLORS.v, 2.5);
        if (on.v_parts) {
          g.save(); g.setLineDash([4, 3]);
          arrow(g, bp, frame.vx * sv, 0, COLORS.v, 1.5); arrow(g, bp, 0, -frame.vy * sv, COLORS.v, 1.5);
          g.restore();
        }
        const ref = nice(vmax / 2);
        legendArrow(g, 12, legendY, ref * sv, t("{v} m/s", { v: num(ref, 3) }), COLORS.v);
        legendY += 20;
      }
      if (on.forces && flying && header.weight) {
        const sf = 60 / header.weight;  // pixels per newton: the weight is 60 px
        arrow(g, bp, 0, header.weight * sf, COLORS.g, 2.5);
        label(g, t("mg"), bp[0] + 6, bp[1] + header.weight * sf, { color: COLORS.g });
        if (frame.F_drag) {
          arrow(g, bp, frame.F_drag[0] * sf, -frame.F_drag[1] * sf, COLORS.drag, 2.5);
          label(g, t("drag"), bp[0] + frame.F_drag[0] * sf - 8, bp[1] - frame.F_drag[1] * sf + 16, { color: COLORS.drag, align: "right" });
        }
        legendArrow(g, 12, legendY, 60, t("weight mg = {F} N", { F: num(header.weight, 3) }), COLORS.g);
        legendY += 20;
      }
      if (on.energy) energyBars(g, W, frame);
    },
  };
  return api;
}
