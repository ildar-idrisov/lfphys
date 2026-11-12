// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v01 view: the space map (lab "now", an observer's "now", or what an observer sees) and the spacetime diagram.
// Everything drawn is data of the run: ray polylines traced by the server, worldlines (segments the server
// sends after every change of motion), events with their computed times, frame matrices of the laws.
// The browser only interpolates along those polylines and applies the given matrices.
import { Plane } from "/static/js/canvas.js";
import { css, el, length, num, panel, time } from "/static/js/ui.js";

const C_SI = 299792458;

export function createView(ctx) {
  let H = null;                 // header
  let units = {};
  let objs = new Map();         // id -> header object (+ wl)
  let wls = new Map();          // id -> worldline json (latest)
  let apps = new Map();         // owner -> [{t, wl}]  apparatus end B worldlines by generation
  let pulses = [];              // {id, t0, kind, n, src, off, T, X, Y, st}
  let signals = [];             // apparatus light: {owner, gen, kind, pts: [[t, x, y], ...], cut}
  let events = [];
  let lastFrame = null, lastT = 0;
  let setUpFor = null;          // the header the controls and the zoom were set up for
  const opt = { frame: "lab", mode: "now", trails: true, labels: true, follow: "", cones: true, simul: true };

  // --- DOM ----------------------------------------------------------------------------------------
  const selFrame = el("select", { title: "Чья система отсчёта: что считается «сейчас» и какие координаты" });
  const selMode = el("select", { title: "«Сейчас» — срез одновременности; «видимое» — где были объекты, когда ушёл свет, который приходит к наблюдателю сейчас" },
    el("option", { value: "now" }, "сейчас (одновременность)"), el("option", { value: "seen" }, "видимое (прошлый конус)"));
  const selFollow = el("select", { title: "Держать объект в центре карты" }, el("option", { value: "" }, "камера свободна"));
  const cbTrails = el("input", { type: "checkbox", checked: true });
  const cbLabels = el("input", { type: "checkbox", checked: true });
  const cbCones = el("input", { type: "checkbox", checked: true });
  const cbSimul = el("input", { type: "checkbox", checked: true });
  const btnFitSpace = el("button", { title: "Вписать сцену" }, "⌖ карта");
  const btnFitDiag = el("button", { title: "Вписать диаграмму" }, "⌖ диаграмма");
  const btn45 = el("button", { title: "Свет под 45° на диаграмме" }, "45°");
  const zoomBox = el("span");
  const cvSpace = el("canvas");
  const cvDiag = el("canvas");
  const ovSpace = el("div", { class: "overlay" });
  const ovDiag = el("div", { class: "overlay" });
  const toolbar = el("div", { class: "toolbar" },
    el("span", { class: "muted" }, "Система:"), selFrame, selMode, selFollow,
    el("label", {}, cbTrails, " лучи"), el("label", {}, cbLabels, " подписи"),
    el("label", { title: "Локальный световой конус наблюдателей на диаграмме" }, cbCones, " конусы"),
    el("label", { title: "Линии одновременности наблюдателей на диаграмме" }, cbSimul, " одновременность"),
    btnFitSpace, btnFitDiag, btn45, zoomBox);
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } },
    toolbar,
    el("div", { class: "split" },
      el("div", {}, el("div", { class: "canvas-wrap" }, cvSpace, ovSpace)),
      el("div", {}, el("div", { class: "canvas-wrap" }, cvDiag, ovDiag))));
  const objTable = el("div", { class: "checks" });
  const rightPanels = [panel("Объекты и часы", objTable)];

  const space = new Plane(cvSpace, { onChange: () => ctx.requestRender() });
  const diag = new Plane(cvDiag, { onChange: () => ctx.requestRender(), lockAspect: false });

  for (const [cb, key] of [[cbTrails, "trails"], [cbLabels, "labels"], [cbCones, "cones"], [cbSimul, "simul"]])
    cb.onchange = () => { opt[key] = cb.checked; ctx.requestRender(); };
  selFrame.onchange = () => { opt.frame = selFrame.value; fitDiagram(); ctx.requestRender(); };
  selMode.onchange = () => { opt.mode = selMode.value; ctx.requestRender(); };
  selFollow.onchange = () => { opt.follow = selFollow.value; ctx.requestRender(); };
  btnFitSpace.onclick = () => fitSpace();
  btnFitDiag.onclick = () => fitDiagram();
  btn45.onclick = () => { diag.sy = diag.sx * c(); ctx.requestRender(); };

  // --- helpers ------------------------------------------------------------------------------------
  const c = () => (H ? H.laws.c : C_SI);

  function wlPos(wl, t) {
    if (!wl) return [NaN, NaN];
    if (wl.kind === "orbit") {
      const a = wl.phase0 + wl.omega * t;
      return [wl.radius * Math.cos(a), wl.radius * Math.sin(a)];
    }
    let s = wl.segments[0];
    for (const g of wl.segments) { if (g.t0 <= t) s = g; else break; }
    return [s.x0[0] + s.v[0] * (t - s.t0), s.x0[1] + s.v[1] * (t - s.t0)];
  }
  function bWl(owner, t) {  // apparatus end B worldline valid at lab time t
    const list = apps.get(owner);
    if (!list) return null;
    let w = null;
    for (const g of list) if (g.t <= t + 1e-15 * Math.abs(t)) w = g.wl;
    return w;
  }

  // the observer frame: row 0 of M gives c t'; rows 1, 2 give x', y'
  function frameM(frame) {
    if (opt.frame === "lab" || !frame || !frame.frames || !frame.frames[opt.frame]) return null;
    return frame.frames[opt.frame];
  }
  const tr = (M, t, x, y) => M ? [ (M[3] * c() * t + M[4] * x + M[5] * y), (M[6] * c() * t + M[7] * x + M[8] * y), (M[0] * c() * t + M[1] * x + M[2] * y) / c() ] : [x, y, t];

  // slice: events with c t' = K, i.e. g(t,x,y) = M0 c t + M1 x + M2 y - K = 0 (lab: t = t_now)
  function sliceK(frame, M) {
    if (!M) return null;
    const o = frame.objects.find((q) => q.id === opt.frame);
    return M[0] * c() * frame.t + M[1] * o.x + M[2] * o.y;
  }
  function onSliceRay(T, X, Y, a, b, M, K, t) {
    // vertices a..b-1 ordered in time; returns [x, y, t] at the slice or null
    const g = M ? (i) => M[0] * c() * T[i] + M[1] * X[i] + M[2] * Y[i] - K : (i) => T[i] - t;
    if (g(a) > 0) return null;
    if (g(b - 1) < 0) return { end: true, p: [X[b - 1], Y[b - 1], T[b - 1]] };
    let lo = a, hi = b - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (g(m) <= 0) lo = m; else hi = m; }
    const g0 = g(lo), g1 = g(hi);
    const w = g1 === g0 ? 0 : -g0 / (g1 - g0);
    return { end: false, p: [X[lo] + w * (X[hi] - X[lo]), Y[lo] + w * (Y[hi] - Y[lo]), T[lo] + w * (T[hi] - T[lo])], k: lo };
  }
  function onSliceWl(wl, M, K, t) {
    if (!M) { const p = wlPos(wl, t); return [p[0], p[1], t]; }
    if (wl.kind === "orbit") {  // bisection on the slice function (monotone along a timelike worldline)
      const g = (tt) => { const p = wlPos(wl, tt); return M[0] * c() * tt + M[1] * p[0] + M[2] * p[1] - K; };
      let lo = t - 1, hi = t + 1, k = 0;
      while (g(lo) > 0 && k++ < 200) lo = t - 2 * (t - lo);
      k = 0; while (g(hi) < 0 && k++ < 200) hi = t + 2 * (hi - t);
      for (let i = 0; i < 100; i++) { const m = 0.5 * (lo + hi); if (g(m) <= 0) lo = m; else hi = m; }
      const p = wlPos(wl, lo); return [p[0], p[1], lo];
    }
    const segs = wl.segments;
    for (let i = segs.length - 1; i >= 0; i--) {
      const s = segs[i];
      // M0 c t + M1 (x0 + v (t - t0)) + M2 (y0 + v (t - t0)) = K  ->  t
      const A = M[0] * c() + M[1] * s.v[0] + M[2] * s.v[1];
      const B = M[1] * (s.x0[0] - s.v[0] * s.t0) + M[2] * (s.x0[1] - s.v[1] * s.t0);
      const tt = (K - B) / A;
      if (tt >= s.t0 || i === 0) { const p = wlPos(wl, tt); return [p[0], p[1], tt]; }
    }
    return null;
  }

  // --- space map ----------------------------------------------------------------------------------
  function fitSpace() {
    if (!H) return;
    const v = H.view;
    space.fit(v.center[0] - v.half, v.center[0] + v.half, v.center[1] - v.half, v.center[1] + v.half, 0.02);
  }
  function fitDiagram() {
    if (!H) return;
    const d = H.diagram;
    diag.fit(d.x0, d.x1, d.t0, d.t1, 0.04);
  }

  function lenLabel(v) {
    const u = H.view.unit;
    if (u === "rs" && units.rs) return num(v / units.rs, 4) + " rs";
    if (u === "au") return length(v, { au: units.au }, 4);
    if (u === "ly") return length(v, { ly: units.ly }, 4);
    return length(v, {}, 4);
  }

  function drawSpace(frame) {
    const g = space.ctx;
    space.clear();
    const M = frameM(frame);
    const K = sliceK(frame, M);
    const t = frame.t;
    const flat = H.flat;
    if (opt.follow) {
      const wl = wls.get(opt.follow);
      if (wl) {
        let q;
        if (M) { const ev = onSliceWl(wl, M, K, t); q = tr(M, ev[2], ev[0], ev[1]); } else q = wlPos(wl, t);
        space.cx = q[0]; space.cy = q[1];
      }
    }
    space.grid({ labelX: lenLabel, labelY: lenLabel });
    // body (and its photon sphere) in the lab frame
    if (H.body && opt.frame === "lab") {
      const b = H.body;
      g.save();
      g.fillStyle = b.radius > b.rs * 1.0001 ? "#f5b700" : "#000";
      g.strokeStyle = css("--ink");
      circle(g, space.X(0), space.Y(0), Math.max(b.r_abs * space.sx, 2)); g.fill(); g.stroke();
      g.restore();
    }
    // light
    const showSeen = opt.mode === "seen" && M;
    if (!showSeen) for (const p of pulses) {  // "seen": only retarded positions, no fronts on another slice
      if (p.t0 > t + 1e-15 * Math.abs(t)) continue;
      drawPulse(g, p, M, K, t);
    }
    // objects
    for (const o of frame.objects) {
      const h = objs.get(o.id);
      if (!h) continue;
      let pos;
      if (showSeen) {
        const s = frame.seen && frame.seen[opt.frame] && frame.seen[opt.frame][o.id];
        if (o.id === opt.frame) pos = tr(M, t, o.x, o.y);
        else if (s) pos = tr(M, s[0], s[1], s[2]);
        else continue;
      } else if (M) {
        const ev = onSliceWl(wls.get(o.id), M, K, t);
        pos = tr(M, ev[2], ev[0], ev[1]);
        pos.future = ev[2] > t * (1 + 1e-15) + 1e-300;
      } else pos = [o.x, o.y];
      drawObject(g, h, o, pos, M, K, t, frame);
    }
    ovSpace.textContent = (opt.frame === "lab" ? "Лабораторная система (покоится относительно " + (H.body ? H.body.name || "тела" : "сцены") + ")"
      : `Система «${objs.get(opt.frame).name}»`) + " · " + (opt.mode === "seen" && M ? "видимое: где были объекты, когда ушёл приходящий сейчас свет"
      : "срез «сейчас»") + (H.gr ? " · координаты Шварцшильда" : "");
  }

  function drawPulse(g, p, M, K, t) {
    const pts = new Array(p.n);
    const col = p.kind === "plane" ? "#1c7ed6" : p.kind === "train" ? "#ae3ec9" : "#f08c00";
    g.save();
    // trails
    if (opt.trails) {
      g.strokeStyle = col; g.globalAlpha = p.kind === "plane" ? 0.35 : 0.18; g.lineWidth = 1;
      for (let i = 0; i < p.n; i++) {
        const a = p.off[i], b = p.off[i + 1];
        const s = onSliceRay(p.T, p.X, p.Y, a, b, M, K, t);
        if (!s) continue;
        g.beginPath();
        let q = tr(M, p.T[a], p.X[a], p.Y[a]); g.moveTo(space.X(q[0]), space.Y(q[1]));
        const kmax = s.end ? b - 1 : s.k;
        for (let k = a + 1; k <= kmax; k++) { q = tr(M, p.T[k], p.X[k], p.Y[k]); g.lineTo(space.X(q[0]), space.Y(q[1])); }
        q = tr(M, s.p[2], s.p[0], s.p[1]); g.lineTo(space.X(q[0]), space.Y(q[1]));
        g.stroke();
      }
    }
    // front
    for (let i = 0; i < p.n; i++) {
      const s = onSliceRay(p.T, p.X, p.Y, p.off[i], p.off[i + 1], M, K, t);
      if (!s) { pts[i] = null; continue; }
      if (s.end && p.st[i] !== 2) { pts[i] = null; continue; }  // left the scene or absorbed
      const q = tr(M, s.p[2], s.p[0], s.p[1]);
      pts[i] = [space.X(q[0]), space.Y(q[1]), s.end];
    }
    g.globalAlpha = 1; g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 2;
    const gap = p.kind === "plane" ? 60 : 40;
    g.beginPath();
    let pen = false;
    const N = p.n, closed = p.kind !== "plane";
    for (let j = 0; j <= (closed ? N : N - 1); j++) {
      const q = pts[j % N];
      if (!q || q[2]) { pen = false; continue; }
      if (pen) {
        const prev = pts[(j - 1 + N) % N];
        if (prev && Math.hypot(q[0] - prev[0], q[1] - prev[1]) > gap) pen = false;
      }
      if (!pen) { g.moveTo(q[0], q[1]); pen = true; } else g.lineTo(q[0], q[1]);
    }
    g.stroke();
    for (const q of pts) if (q && !q[2]) { g.fillRect(q[0] - 1, q[1] - 1, 2, 2); }
    for (const q of pts) if (q && q[2]) { g.globalAlpha = 0.5; g.fillRect(q[0] - 1, q[1] - 1, 2, 2); }
    g.restore();
  }

  function drawObject(g, h, o, pos, M, K, t, frame) {
    const X = space.X(pos[0]), Y = space.Y(pos[1]);
    g.save();
    if (pos.future) g.globalAlpha = 0.35;  // on the observer's slice but in the lab future: extrapolated
    g.fillStyle = h.color; g.strokeStyle = css("--ink");
    const rpx = Math.max((h.radius || 0) * space.sx, h.kind === "galaxy" ? 6 : 4);
    if (h.kind === "star" && H.body && opt.frame === "lab") { g.restore(); return; }  // drawn as the body
    // apparatus rod A-B
    if (o.bx !== undefined && opt.mode === "now") {
      let qb;
      if (M) { const wb = bWl(o.id, t); const ev = wb ? onSliceWl(wb, M, K, t) : null; qb = ev ? tr(M, ev[2], ev[0], ev[1]) : null; }
      else qb = [o.bx, o.by];
      if (qb) {
        g.strokeStyle = h.color; g.lineWidth = 3; g.globalAlpha = o.synced ? 1 : 0.4;
        g.beginPath(); g.moveTo(X, Y); g.lineTo(space.X(qb[0]), space.Y(qb[1])); g.stroke();
        g.globalAlpha = 1; g.fillStyle = css("--canvas"); g.strokeStyle = h.color; g.lineWidth = 2;
        circle(g, space.X(qb[0]), space.Y(qb[1]), 4); g.fill(); g.stroke();
        if (opt.labels) { g.fillStyle = css("--muted"); g.font = "11px system-ui";
          g.fillText("B " + (!o.synced || o.tau_b === null || o.tau_b === undefined ? "(часы ещё не синхронизированы)" : "τ=" + time(o.tau_b, 9)), space.X(qb[0]) + 6, space.Y(qb[1]) + 14); }
      }
    }
    g.fillStyle = h.color; g.strokeStyle = css("--ink"); g.lineWidth = 1;
    circle(g, X, Y, rpx); g.fill(); g.stroke();
    // velocity arrow (lab only: in other frames the run would have to transform velocities)
    if (!M && (o.vx || o.vy)) {
      const v = Math.hypot(o.vx, o.vy), L = 18 + 22 * Math.min(1, v / c());
      g.strokeStyle = h.color; g.lineWidth = 2;
      g.beginPath(); g.moveTo(X, Y); g.lineTo(X + L * o.vx / v, Y - L * o.vy / v); g.stroke();
    }
    if (opt.labels) {
      g.fillStyle = css("--ink"); g.font = "12px system-ui";
      g.fillText(h.name + (pos.future ? " (лаб. будущее: экстраполяция)" : ""), X + rpx + 4, Y - 4);
      g.fillStyle = css("--muted"); g.font = "11px system-ui";
      g.fillText("τ = " + time(o.tau, 9), X + rpx + 4, Y + 10);
    }
    g.restore();
  }

  // --- spacetime diagram ----------------------------------------------------------------------------
  function drawDiagram(frame) {
    const g = diag.ctx;
    diag.clear();
    const M = frameM(frame);
    const K = sliceK(frame, M);
    const t = frame.t;
    const P = (tt, x, y) => { const q = tr(M, tt, x, y); return [diag.X(q[0]), diag.Y(q[2])]; };
    const past = (tt, x, y) => M ? M[0] * c() * tt + M[1] * x + M[2] * y <= K * (1 + 1e-15) : tt <= t;
    diag.grid({ labelX: lenLabel, labelY: (v) => time(v, 4) });
    g.save();
    // light: projection of every ray on (x, t), up to the current slice
    for (const p of pulses) {
      if (!past(p.t0, p.origin[0], p.origin[1])) continue;
      const col = p.kind === "plane" ? "#1c7ed6" : p.kind === "train" ? "#ae3ec9" : "#f08c00";
      g.strokeStyle = col; g.globalAlpha = p.kind === "flash" ? 0.25 : 0.2; g.lineWidth = 1;
      const step = p.n > 180 ? Math.ceil(p.n / 180) : 1;
      for (let i = 0; i < p.n; i += step) {
        const a = p.off[i], b = p.off[i + 1];
        const s = onSliceRay(p.T, p.X, p.Y, a, b, M, K, t);
        if (!s) continue;
        g.beginPath();
        let q = P(p.T[a], p.X[a], p.Y[a]); g.moveTo(q[0], q[1]);
        const kmax = s.end ? b - 1 : s.k;
        for (let k = a + 1; k <= kmax; k++) { q = P(p.T[k], p.X[k], p.Y[k]); g.lineTo(q[0], q[1]); }
        if (!s.end) { q = P(s.p[2], s.p[0], s.p[1]); g.lineTo(q[0], q[1]); }
        g.stroke();
      }
    }
    g.globalAlpha = 1;
    // worldlines up to their event on the current slice
    const b = diag.bounds();
    const tLow = Math.min(b.y0, t) - Math.abs(b.y1 - b.y0);
    for (const [id, h] of objs) {
      const wl = wls.get(id);
      if (!wl) continue;
      const now = onSliceWl(wl, M, K, t);
      if (!now) continue;
      const tEnd = now[2];
      g.strokeStyle = h.color; g.lineWidth = h.kind === "observer" ? 2.2 : 1.6;
      const pts = [];
      if (wl.kind === "orbit") {
        const n = 240, t0 = Math.max(tLow, tEnd - 50 * Math.abs(b.y1 - b.y0));
        for (let i = 0; i <= n; i++) { const tt = t0 + (tEnd - t0) * i / n; const p = wlPos(wl, tt); pts.push(P(tt, p[0], p[1])); }
      } else {
        const t0 = Math.min(wl.segments[0].t0, tLow);
        let p = wlPos(wl, t0); pts.push(P(t0, p[0], p[1]));
        for (const sg of wl.segments) if (sg.t0 > t0 && sg.t0 < tEnd) { p = wlPos(wl, sg.t0); pts.push(P(sg.t0, p[0], p[1])); }
        pts.push(P(tEnd, now[0], now[1]));
      }
      g.beginPath(); pts.forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); g.stroke();
      if (M && tEnd > t) {  // the observer's slice reaches into the lab future: extrapolated, not computed yet
        const pNow = wlPos(wl, t), A2 = P(t, pNow[0], pNow[1]), B2 = pts[pts.length - 1];
        g.save(); g.strokeStyle = css("--canvas"); g.lineWidth = 3; g.setLineDash([2, 4]); line(g, A2, B2); g.restore();
      }
      const last = pts[pts.length - 1];
      g.fillStyle = h.color; circle(g, last[0], last[1], 3.5); g.fill();
      if (opt.labels) { g.font = "11px system-ui"; g.fillText(h.name, last[0] + 5, last[1] - 5); }
    }
    // apparatus end B (one dashed worldline per assembled apparatus)
    for (const [owner, list] of apps) {
      const h = objs.get(owner);
      for (let i = 0; i < list.length; i++) {
        const ta = list[i].t;
        const nb = onSliceWl(list[i].wl, M, K, t);
        if (!nb) continue;
        let tEndGen = i + 1 < list.length ? list[i + 1].t : Infinity;
        for (const sg of signals) if (sg.owner === owner && sg.gen === list[i].gen) tEndGen = Math.max(tEndGen, sg.pts[sg.pts.length - 1][0]);
        const tb = Math.min(tEndGen, nb[2]);
        if (ta > tb) continue;
        const pa = wlPos(list[i].wl, ta), pb = wlPos(list[i].wl, tb);
        g.strokeStyle = h.color; g.setLineDash([3, 3]); g.lineWidth = 1.2;
        line(g, P(ta, pa[0], pa[1]), P(tb, pb[0], pb[1])); g.setLineDash([]);
      }
    }
    // apparatus light signals (synchronisation and measurements), up to the slice
    for (const sg of signals) {
      const h = objs.get(sg.owner);
      const pts = sg.pts.filter((q) => sg.cut === undefined || q[0] <= sg.cut);
      if (sg.cut !== undefined && pts.length < sg.pts.length) {  // truncate the leg crossing the cut
        const a = sg.pts[pts.length - 1], b2 = sg.pts[pts.length], w = (sg.cut - a[0]) / (b2[0] - a[0]);
        pts.push([sg.cut, a[1] + w * (b2[1] - a[1]), a[2] + w * (b2[2] - a[2])]);
      }
      g.strokeStyle = h ? h.color : css("--muted"); g.lineWidth = 1.4; g.globalAlpha = 0.95;
      g.setLineDash(sg.kind === "sync" ? [2, 2] : []);
      g.beginPath();
      let started = false;
      for (let i = 0; i < pts.length; i++) {
        const q = pts[i];
        if (!past(q[0], q[1], q[2])) {
          if (i > 0) {  // interpolate to the slice
            const a = pts[i - 1];
            let lo = 0, hi = 1;
            for (let k = 0; k < 60; k++) { const m = 0.5 * (lo + hi);
              if (past(a[0] + m * (q[0] - a[0]), a[1] + m * (q[1] - a[1]), a[2] + m * (q[2] - a[2]))) lo = m; else hi = m; }
            const r = P(a[0] + lo * (q[0] - a[0]), a[1] + lo * (q[1] - a[1]), a[2] + lo * (q[2] - a[2]));
            g.lineTo(r[0], r[1]);
          }
          break;
        }
        const r = P(q[0], q[1], q[2]);
        if (!started) { g.moveTo(r[0], r[1]); started = true; } else g.lineTo(r[0], r[1]);
      }
      g.stroke(); g.setLineDash([]); g.globalAlpha = 1;
    }
    // events on the past side of the slice
    for (const e of events) {
      if (!e.obj || !wls.get(e.obj)) continue;
      const p = e.pos || wlPos(wls.get(e.obj), e.t);  // events at B carry their own position
      if (!past(e.t, p[0], p[1])) continue;
      const q = P(e.t, p[0], p[1]);
      g.fillStyle = e.kind === "arrival" ? "#f08c00" : e.kind === "measure" ? "#2b8a3e" : e.kind === "emit" ? "#c92a2a" : css("--muted");
      g.fillRect(q[0] - 3, q[1] - 3, 6, 6);
    }
    // planned events of the initial data (known in advance, review R14): hollow markers
    for (const pe of H.planned || []) {
      if (!past(pe.t, pe.x, pe.y)) continue;
      const q = P(pe.t, pe.x, pe.y);
      g.strokeStyle = "#c92a2a"; g.lineWidth = 1.5; g.strokeRect(q[0] - 4, q[1] - 4, 8, 8);
      if (opt.labels) { g.fillStyle = "#c92a2a"; g.font = "11px system-ui"; g.fillText(pe.text, q[0] + 6, q[1] + 12); }
    }
    // simultaneity lines (flat runs: each observer's c t' = const) and local light cones
    for (const o of frame.objects) {
      const h = objs.get(o.id);
      if (!h || (h.kind !== "observer" && h.kind !== "station")) continue;
      const Mo = frame.frames && frame.frames[o.id];
      if (opt.simul && Mo) {
        const K0 = Mo[0] * c() * t + Mo[1] * o.x + Mo[2] * o.y;
        const tAt = (x) => (K0 - Mo[1] * x - Mo[2] * o.y) / (Mo[0] * c());
        const w = b.x1 - b.x0, xs = [b.x0 - 3 * w, b.x1 + 3 * w];
        g.strokeStyle = h.color; g.globalAlpha = 0.65; g.setLineDash([8, 5]); g.lineWidth = 1.3;
        line(g, P(tAt(xs[0]), xs[0], o.y), P(tAt(xs[1]), xs[1], o.y)); g.setLineDash([]); g.globalAlpha = 1;
      }
      if (opt.cones && frame.cones && frame.cones[o.id]) {
        const cn = frame.cones[o.id];
        const span = Math.abs(b.y1 - b.y0) * 0.25;
        g.strokeStyle = h.color; g.lineWidth = 1;
        g.globalAlpha = 0.9;
        for (const u of cn.fut) line(g, P(t, o.x, o.y), P(t + span, o.x + u * span, o.y));
        g.globalAlpha = 0.5;
        for (const u of cn.past) line(g, P(t, o.x, o.y), P(t - span, o.x - u * span, o.y));
        g.globalAlpha = 1;
      }
    }
    // the current slice of the chosen frame: horizontal in its own coordinates
    g.strokeStyle = css("--ink"); g.globalAlpha = 0.5; g.lineWidth = 1;
    const tNow = M ? K / c() : t;
    line(g, [0, diag.Y(tNow)], [diag.w, diag.Y(tNow)]);
    g.restore();
    ovDiag.textContent = "Пространство-время: x вправо, t вверх; " + (M ? `координаты «${objs.get(opt.frame).name}» (x′, t′); пунктир поверх линии — лабораторное будущее (ещё не вычислено: действия могут его изменить)` : "лабораторные координаты")
      + (H.gr ? " (Шварцшильд)" : "") + " · колесо — масштаб, Shift — только t, Alt — только x";
  }

  // --- readouts ---------------------------------------------------------------------------------------
  function drawTable(frame) {
    const rows = [];
    const t = frame.t;
    for (const o of frame.objects) {
      const h = objs.get(o.id);
      if (!h || h.kind === "star") continue;
      const beta = Math.hypot(o.vx, o.vy) / c();
      const cells = [el("td", {}, el("span", { style: { color: h.color } }, "● "), h.name),
        el("td", { class: "mono" }, "τ " + time(o.tau, 10), el("div", { class: "muted" }, "t − τ = " + time(t - o.tau, 4))),
        el("td", { class: "mono" }, beta ? num(beta, 4) + " c" : "покой")];
      rows.push(el("tr", {}, cells));
      const na = frame.now_at && frame.now_at[o.id];
      if (na) {
        for (const [qid, tq] of Object.entries(na)) {
          const q = objs.get(qid);
          if (!q || q.kind !== "galaxy" || tq === null) continue;
          const evA = events.find((e) => e.kind === "emit" && e.obj === qid) || (H.planned || []).find((e) => e.obj === qid);
          let txt = `«сейчас» на ${q.name}: t = ${time(tq, 6)}` + (tq > t ? " (лаб. будущее)" : "");
          if (evA) txt += tq >= evA.t ? ` — событие уже произошло (${time(tq - evA.t, 4)} назад)` : ` — событие ещё впереди (через ${time(evA.t - tq, 4)})`;
          rows.push(el("tr", {}, el("td", { colspan: 3, class: "muted" }, txt)));
        }
      }
    }
    objTable.replaceChildren(el("table", {}, rows));
  }

  // --- contract ---------------------------------------------------------------------------------------
  return {
    center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, "Что на экране"),
      el("p", {}, "Слева — пространство на срезе «сейчас» выбранной системы отсчёта (или то, что видит наблюдатель: где были объекты, когда ушёл приходящий к нему свет). Справа — диаграмма Минковского: мировые линии, лучи вспышек (проекция на ось x), события, линии одновременности и локальные конусы наблюдателей."),
      el("p", {}, "Фронт вспышки — это положения посчитанных лучей в текущий момент; задержка у массы, тень и петли у фотонной сферы — результат интегрирования геодезических. Часы (τ) — собственное время по метрике законов запуска. Скорость света, частоты, одновременность — в «Проверках», рядом с эталоном.")),
    reset() { H = null; objs = new Map(); wls = new Map(); apps = new Map(); pulses = []; signals = []; events = []; },  // setUpFor stays
    // key frames (player.js): the accumulated lists only grow, so a key frame is their lengths and the latest worldlines
    snapshot() {
      return { pulses: pulses.length, signals: signals.length, events: events.length, wls: new Map(wls),
               apps: new Map([...apps].map(([k, v]) => [k, v.length])) };
    },
    restore(k) {
      pulses.length = k.pulses; signals.length = k.signals; events.length = k.events; wls = new Map(k.wls);
      for (const [owner, list] of [...apps]) {
        if (k.apps.has(owner)) list.length = k.apps.get(owner); else apps.delete(owner);
      }
    },
    onHeader(meta) {
      H = meta; units = meta.units || {};
      for (const o of meta.objects) { objs.set(o.id, o); wls.set(o.id, o.wl); }
      // the same world rebuilt from the record (the player going back) keeps the chosen frame, the camera and the
      // zoom: only a new world sets them up again (found by the key frames' browser check, STATUS V32 f)
      if (setUpFor === meta) return;
      setUpFor = meta;
      selFrame.replaceChildren(el("option", { value: "lab" }, "лабораторная"));
      if (meta.flat) for (const o of meta.objects) if (o.kind === "observer") selFrame.append(el("option", { value: o.id }, o.name));
      selFrame.value = "lab"; opt.frame = "lab";
      selMode.disabled = !meta.flat;
      selFollow.replaceChildren(el("option", { value: "" }, "камера свободна"), ...meta.objects.map((o) => el("option", { value: o.id }, "следить: " + o.name)));
      zoomBox.replaceChildren(...(meta.diagram.zooms || []).map((z) => el("button", { title: "Приблизить диаграмму",
        onclick: () => { diag.fit(z.x0, z.x1, z.t0, z.t1, 0.04); } }, "⌖ " + z.label)));
      fitSpace(); fitDiagram();
    },
    onMessage(meta, blobs) {
      if (meta.type === "pulse") {
        pulses.push({ ...meta, off: blobs.off, T: blobs.T, X: blobs.X, Y: blobs.Y, st: blobs.st });
      } else if (meta.type === "worldline") {
        if (meta.owner) {
          if (!apps.has(meta.owner)) apps.set(meta.owner, []);
          apps.get(meta.owner).push({ t: meta.t, wl: meta.wl, gen: meta.gen });
          // a rebuilt apparatus does not erase light already on its way: old signals run to their ends
        } else wls.set(meta.id, meta.wl);
      } else if (meta.type === "signal") {
        signals.push({ ...meta });
      } else if (meta.type === "event") {
        events.push(meta);
      }
    },
    render(frame, t) {
      if (!H) return;
      lastFrame = frame; lastT = t;
      drawSpace(frame);
      drawDiagram(frame);
      drawTable(frame);
    },
  };
}

function circle(g, x, y, r) { g.beginPath(); g.arc(x, y, r, 0, 2 * Math.PI); }
function line(g, A, B) { g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(B[0], B[1]); g.stroke(); }
