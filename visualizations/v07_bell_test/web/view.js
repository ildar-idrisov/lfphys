// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v07 view: the Bell test. Left: the set-up seen from the side (source, two stations with their analyzers at the
// current angles, pairs in flight, flashes of the outcomes) and the space-time diagram of the last detected pair (its
// emission, the setting choices with their future light cones, the detections). Right: coincidence counts, E with
// errors, CHSH S against the bounds 2 and 2√2, and E(Δ) of the measured angle pairs against the laws' curves.
// Everything comes from the run: positions are interpolated along the computed straight paths (x = ±v (t − t_e)),
// outcomes, settings, choice times and space-time relations are the run's own events; the curves are computed by the
// engine (header) and are drawn only next to the measured points.
import { css, el, fresh2d, num, panel, time } from "/static/js/ui.js";

const COL_SET = ["#1c7ed6", "#ae3ec9"];      // setting 0 (a, b) and 1 (a′, b′)
const COL_PLUS = "#2b8a3e", COL_MINUS = "#e03131", COL_SRC = "#f08c00", COL_LHV = "#e8590c";
const MAXDET = 6000;
const NMIN = 30;  // pairs per cell before an estimate is compared (the same rule as the run's checks)
const F_LOC_A = 1, F_LOC_B = 2, F_FREE_A = 4, F_FREE_B = 8;

export function createView(ctx) {
  let H = null, HB = null, det = newDet();
  const opt = { cones: true, other: true };

  // --- DOM --------------------------------------------------------------------------------------------
  const live = (id, label) => (ctx.liveControl ? ctx.liveControl(id, { label }) : null);
  const quick = el("div", { class: "toolbar quick", title: "Установка: меняется сразу (то же, что в панели слева)" },
    el("span", { class: "muted" }, "Настройки:"), live("a_deg", "a, °"), live("a2_deg", "a′, °"), live("b_deg", "b, °"),
    live("b2_deg", "b′, °"), live("switch", "выбор"), live("tau_ns", "τ, нс"), live("L_m", "L, м"));
  const btnFly = el("button", { title: "Скорость, при которой виден полёт одной пары (≈2 с на пролёт)" }, "▷ полёт");
  const btnStat = el("button", { title: "Скорость набора статистики (≈2000 пар в секунду)" }, "▷▷ набор статистики");
  const btnClear = el("button", { title: "Счёты совпадений начинаются заново (действие «Сбросить статистику»)" }, "⟲ сбросить статистику");
  const cbCones = el("input", { type: "checkbox", checked: true });
  const cbOther = el("input", { type: "checkbox", checked: true });
  const toolbar = el("div", { class: "toolbar" }, btnFly, btnStat, btnClear,
    el("label", { title: "Будущие световые конусы событий выбора на диаграмме пространства-времени" }, cbCones, " световые конусы"),
    el("label", { title: "Кривая другого закона на графике E(Δ) (для сравнения)" }, cbOther, " кривая другого закона"));
  const cvGeo = el("canvas"), cvStat = el("canvas");
  const ovGeo = el("div", { class: "overlay" }), ovStat = el("div", { class: "overlay" });
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick, toolbar,
    el("div", { class: "split" },
      el("div", {}, el("div", { class: "canvas-wrap" }, cvGeo, ovGeo)),
      el("div", {}, el("div", { class: "canvas-wrap" }, cvStat, ovStat))));
  const infoBox = el("div", { class: "kv" });
  const countBox = el("div", {});
  const lastBox = el("div", { class: "events" });
  const rightPanels = [panel("Установка и пространство-время", infoBox), panel("Счётчики", countBox),
    panel("Последние пары", lastBox)];

  btnFly.onclick = () => lastF && ctx.send("speed", { value: lastF.flight / 2 });
  btnStat.onclick = () => lastF && ctx.send("speed", { value: 2000 / lastF.settings.rate });
  btnClear.onclick = () => ctx.action && ctx.action("clear", {});
  cbCones.onchange = () => { opt.cones = cbCones.checked; ctx.requestRender(); };
  cbOther.onchange = () => { opt.other = cbOther.checked; ctx.requestRender(); };
  for (const cv of [cvGeo, cvStat]) new ResizeObserver(() => ctx.requestRender()).observe(cv);

  let lastF = null;

  // --- detections (per-pair detail of the run) ---------------------------------------------------------------
  function newDet() {
    return { n: 0, off: 0, t: [], te: [], id: [], sA: [], sB: [], oA: [], oB: [], alA: [], alB: [], tcA: [], tcB: [], xcA: [], xcB: [], L: [], fl: [] };
  }
  function pushDet(b) {
    const m = b.t.length;
    for (const k of ["t", "te", "id", "sA", "sB", "oA", "oB", "alA", "alB", "tcA", "tcB", "xcA", "xcB", "L", "fl"])
      for (let i = 0; i < m; i++) det[k].push(b[k][i]);
    det.n += m;
    if (det.n > MAXDET) {
      const cut = det.n - MAXDET;
      for (const k of Object.keys(det)) if (Array.isArray(det[k])) det[k].splice(0, cut);
      det.n = MAXDET;
      det.off += cut;  // detections dropped from the front (a key frame from before cannot be restored any more)
    }
  }
  function lastUpTo(t) {  // index of the last detection revealed at time t (-1: none)
    let lo = 0, hi = det.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (det.t[m] <= t) lo = m + 1; else hi = m; }
    return lo - 1;
  }

  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }
  const isPhoton = () => H && H.pair === "photon";
  const sign = (o) => (o > 0 ? "+" : "−");
  const oCol = (o) => (o > 0 ? COL_PLUS : COL_MINUS);
  function lenFmt(x) {
    const a = Math.abs(x);
    if (a >= 1e3) return num(x / 1e3, 4) + " км";
    if (a >= 1) return num(x, 4) + " м";
    if (a >= 1e-3) return num(x * 1e3, 4) + " мм";
    return num(x * 1e6, 4) + " мкм";
  }
  function setLabel(side, s) { return side === "A" ? (s ? "a′" : "a") : (s ? "b′" : "b"); }

  // which setting is in force at a station: the choice already made for the next particle, else the last one used
  function activeSetting(f, fl, t, side) {
    if (f.settings.switch === "fixed") return { s: 0, why: "фиксированная" };
    const k = fl.length / 6;
    let best = null;
    for (let q = 0; q < k; q++) {
      const tarr = fl[6 * q + 1], s = fl[6 * q + (side === "A" ? 2 : 3)], tc = fl[6 * q + (side === "A" ? 4 : 5)];
      if (s >= 0 && tc <= t && (best === null || tarr < best.tarr)) best = { tarr, s };
    }
    if (best) return { s: best.s, why: "выбрана для следующей частицы" };
    const i = lastUpTo(t);
    if (i >= 0) return { s: side === "A" ? det.sA[i] : det.sB[i], why: "последняя использованная" };
    return { s: 0, why: "" };
  }

  // --- the set-up and the space-time diagram -------------------------------------------------------------
  function drawGeo(f, t, blobs) {
    const cv = cvGeo, g = setup(cv), W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const S = f.settings, L = S.L, v = H.v;
    const mx = Math.min(125, W * 0.2);
    const X = (x) => W / 2 + (W / 2 - mx) * x / L;
    const topH = Math.round(Hh * 0.46);
    const yc = 30 + (topH - 30) * 0.48;
    const ink = css("--ink"), muted = css("--muted");
    g.font = "12px system-ui";
    // beam line and the distance
    g.strokeStyle = css("--line"); g.lineWidth = 1; g.setLineDash([4, 4]);
    g.beginPath(); g.moveTo(X(-L), yc); g.lineTo(X(L), yc); g.stroke(); g.setLineDash([]);
    g.fillStyle = muted; g.textAlign = "center";
    for (const s of [-1, 1]) g.fillText(`L = ${lenFmt(L)}`, (X(0) + X(s * L)) / 2, yc - 9);
    // source
    g.fillStyle = COL_SRC; g.beginPath(); g.arc(X(0), yc, 7, 0, 2 * Math.PI); g.fill();
    g.fillStyle = ink; g.fillText("источник", X(0), yc - 14);
    // particles in flight (computed emission times; straight paths at the speed v)
    const fl = blobs.flight || [];
    let nfl = 0;
    for (let q = 0; q + 5 < fl.length; q += 6) {
      const te = fl[q];
      if (te > t) continue;
      const r = v * (t - te);
      if (r > L * 1.0001) continue;
      nfl++;
      g.strokeStyle = "rgba(240,140,0,0.18)"; g.lineWidth = 1;
      g.beginPath(); g.moveTo(X(-r), yc); g.lineTo(X(r), yc); g.stroke();
      for (const xx of [-r, r]) { g.fillStyle = COL_SRC; g.beginPath(); g.arc(X(xx), yc, 4, 0, 2 * Math.PI); g.fill(); }
    }
    // stations with analyzers at the current angles
    const actA = activeSetting(f, fl, t, "A"), actB = activeSetting(f, fl, t, "B");
    drawStation(g, X(-L), yc, "A", "Алиса", [S.a, S.a2], actA, ink, muted);
    drawStation(g, X(L), yc, "B", "Боб", [S.b, S.b2], actB, ink, muted);
    // flashes of the last outcomes (revealed at the arrival)
    const i = lastUpTo(t);
    if (i >= 0) {
      const age = t - det.t[i], w = 0.6 * f.flight;
      const a = age < w ? 1 - age / w : 0;
      for (const [side, x0, o] of [["A", X(-L), det.oA[i]], ["B", X(L), det.oB[i]]]) {
        if (a > 0) {
          const gr = g.createRadialGradient(x0, yc, 2, x0, yc, 40);
          gr.addColorStop(0, oCol(o)); gr.addColorStop(1, "rgba(0,0,0,0)");
          g.globalAlpha = 0.85 * a; g.fillStyle = gr; g.beginPath(); g.arc(x0, yc, 40, 0, 2 * Math.PI); g.fill(); g.globalAlpha = 1;
        }
        g.fillStyle = oCol(o); g.font = `bold ${a > 0 ? 22 : 15}px system-ui`; g.textAlign = "center";
        g.fillText(sign(o), x0 + (side === "A" ? 38 : -38), yc - 22);
      }
      g.font = "12px system-ui";
    }
    g.textAlign = "left";
    drawSpacetime(g, W, Hh, topH, t, f);
    const cnt = f.counts;
    ovGeo.textContent = `Полёт L/v = ${time(f.flight, 4)}. В полёте пар: ${cnt.in_flight} (показано ${nfl}). Исход + или − — в момент прихода частицы.`;
  }

  function drawStation(g, x0, y0, side, name, angles, act, ink, muted) {
    const R = 24;
    g.strokeStyle = ink; g.lineWidth = 1.5; g.fillStyle = css("--panel");
    g.beginPath(); g.arc(x0, y0, R, 0, 2 * Math.PI); g.fill(); g.stroke();
    for (let s = 0; s < 2; s++) {
      const al = angles[s] * Math.PI / 180, on = act.s === s;
      // photons: transmission axis of the polarizer (a line); spin: the Stern-Gerlach direction (an arrow)
      const dx = Math.sin(al), dy = -Math.cos(al);
      g.strokeStyle = COL_SET[s]; g.globalAlpha = on ? 1 : 0.35; g.lineWidth = on ? 3.5 : 1.5;
      g.setLineDash(on ? [] : [3, 3]);
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
    g.font = "12px system-ui"; g.textAlign = "center"; g.fillStyle = ink;
    g.fillText(`${name} (${side})`, x0, y0 - R - 8);
    const l0 = setLabel(side, 0), l1 = setLabel(side, 1);
    g.fillStyle = COL_SET[0]; g.fillText(`${l0} = ${num(angles[0], 4)}°`, x0, y0 + R + 16);
    g.fillStyle = COL_SET[1]; g.fillText(`${l1} = ${num(angles[1], 4)}°`, x0, y0 + R + 30);
    g.fillStyle = muted; g.font = "11px system-ui";
    if (act.why) g.fillText(`${setLabel(side, act.s)}: ${act.why}`, x0, y0 + R + 44);
    g.textAlign = "left";
  }

  function drawSpacetime(g, W, Hh, topH, t, f) {
    const x0 = 46, x1 = W - 14, y0 = topH + 40, y1 = Hh - 54;
    const ink = css("--ink"), muted = css("--muted");
    g.strokeStyle = css("--line"); g.beginPath(); g.moveTo(0, topH + 4); g.lineTo(W, topH + 4); g.stroke();
    g.fillStyle = ink; g.font = "12px system-ui";
    g.fillText("Пространство-время последней пары (x — вправо, t — вверх)", 8, topH + 20);
    const i = lastUpTo(t);
    if (i < 0) { g.fillStyle = muted; g.fillText("пока ни одна пара не дошла до станций", 8, topH + 40); return; }
    const c = H.c, td = det.t[i], te = det.te[i], Ld = det.L[i];
    const Lr = Math.max(Ld, Math.abs(det.xcA[i]), Math.abs(det.xcB[i]));
    const Xd = (x) => (x0 + x1) / 2 + (x1 - x0) / 2 * 0.92 * x / Lr;
    let tlo = Math.min(te, det.tcA[i], det.tcB[i]);
    const clipped = tlo < td - 4 * Math.max(td - te, 2 * Ld / c);
    if (clipped) tlo = td - 1.15 * (td - te);  // a choice far in the past: show the pair, mark the choice below
    const span = Math.max(td - tlo, 1e-30);
    // equal scales of x and ct (light lines at 45°) whenever the events fit into that window
    const Teq = (y1 - y0) / (x1 - x0) * (2 * Lr / 0.92) / c;
    let thi = td + 0.12 * span, tl = tlo - 0.08 * span;
    if (Teq >= 1.2 * span) { thi = td + 0.1 * Teq; tl = thi - Teq; }
    const Y = (tt) => y1 - (y1 - y0) * (tt - tl) / (thi - tl);
    // axes
    g.strokeStyle = css("--line"); g.lineWidth = 1;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x0, y1); g.lineTo(x1, y1); g.stroke();
    g.fillStyle = muted; g.font = "11px system-ui";
    g.fillText("t", x0 - 12, y0 + 4);
    for (const [xx, lab] of [[-Ld, "−L (A)"], [0, "0"], [Ld, "+L (B)"]]) { g.fillRect(Xd(xx), y1, 1, 4); g.textAlign = "center"; g.fillText(lab, Xd(xx), y1 + 14); }
    g.textAlign = "left";
    g.save(); g.beginPath(); g.rect(x0, y0 - 6, x1 - x0, y1 - y0 + 6); g.clip();
    // future light cones of the two choices
    const cone = (tc, xc, col) => {
      if (!opt.cones || !(tc <= thi)) return;
      const tcd = Math.max(tc, tl), dxe = c * (thi - tc), dx0 = c * (tcd - tc);
      g.fillStyle = col; g.globalAlpha = 0.10;
      g.beginPath(); g.moveTo(Xd(xc - dx0), Y(tcd)); g.lineTo(Xd(xc - dxe), Y(thi)); g.lineTo(Xd(xc + dxe), Y(thi)); g.lineTo(Xd(xc + dx0), Y(tcd)); g.closePath(); g.fill();
      g.globalAlpha = 0.75; g.strokeStyle = col; g.lineWidth = 1; g.setLineDash([5, 3]);
      g.beginPath(); g.moveTo(Xd(xc - dx0), Y(tcd)); g.lineTo(Xd(xc - dxe), Y(thi)); g.moveTo(Xd(xc + dx0), Y(tcd)); g.lineTo(Xd(xc + dxe), Y(thi)); g.stroke();
      g.setLineDash([]); g.globalAlpha = 1;
    };
    cone(det.tcA[i], det.xcA[i], COL_SET[det.sA[i]]);
    cone(det.tcB[i], det.xcB[i], COL_SET[det.sB[i]]);
    // world lines of the two particles
    g.strokeStyle = COL_SRC; g.lineWidth = 2;
    g.beginPath(); g.moveTo(Xd(0), Y(te)); g.lineTo(Xd(-Ld), Y(td)); g.moveTo(Xd(0), Y(te)); g.lineTo(Xd(Ld), Y(td)); g.stroke();
    g.restore();
    // events
    const dot = (x, y, col, r = 5) => { g.fillStyle = col; g.beginPath(); g.arc(x, y, r, 0, 2 * Math.PI); g.fill(); };
    const diamond = (x, y, col) => { g.fillStyle = col; g.beginPath(); g.moveTo(x, y - 7); g.lineTo(x + 7, y); g.lineTo(x, y + 7); g.lineTo(x - 7, y); g.closePath(); g.fill(); };
    if (te >= tl) { dot(Xd(0), Y(te), COL_SRC); g.fillStyle = ink; g.textAlign = "center"; g.fillText("вылет", Xd(0), Y(te) + 16); }
    for (const [side, tc, xc, s] of [["A", det.tcA[i], det.xcA[i], det.sA[i]], ["B", det.tcB[i], det.xcB[i], det.sB[i]]]) {
      const yy = tc >= tl ? Y(tc) : y1 - 4;
      diamond(Xd(xc), yy, COL_SET[s]);
      g.fillStyle = COL_SET[s]; g.textAlign = side === "A" ? "left" : "right";
      const lab = `выбор ${setLabel(side, s)}` + (tc >= tl ? "" : `: за ${time(td - tc, 3)} ↓`);
      g.fillText(lab, Xd(xc) + (side === "A" ? 10 : -10), Math.max(yy + 4, Y(td) + 22));
    }
    for (const [side, x, o] of [["A", -Ld, det.oA[i]], ["B", Ld, det.oB[i]]]) {
      dot(Xd(x), Y(td), oCol(o), 7);
      g.fillStyle = "#fff"; g.textAlign = "center"; g.font = "bold 12px system-ui"; g.fillText(sign(o), Xd(x), Y(td) + 4);
      g.font = "11px system-ui"; g.fillStyle = ink;
      g.textAlign = side === "A" ? "left" : "right";
      g.fillText(`регистрация ${side}`, Xd(x) + (side === "A" ? 10 : -10), Y(td) - 10);
    }
    g.textAlign = "left";
    // verdicts from the run's own space-time relations of this pair
    const fl = det.fl[i];
    const okA = fl & F_LOC_A, okB = fl & F_LOC_B;
    const txt = (ok, a, b) => ok ? `выбор у ${a} вне конуса регистрации у ${b}: пространственноподобно` : `выбор у ${a} в конусе регистрации у ${b}: лазейка локальности`;
    g.font = "11px system-ui";
    g.fillStyle = okA ? css("--ok") : css("--bad"); g.fillText((okA ? "✓ " : "✗ ") + txt(okA, "A", "B"), 8, Hh - 18);
    g.fillStyle = okB ? css("--ok") : css("--bad"); g.fillText((okB ? "✓ " : "✗ ") + txt(okB, "B", "A"), 8, Hh - 5);
    g.fillStyle = muted;
    const ratio = (c * (thi - tl)) / (2 * Lr / 0.92) * (x1 - x0) / (y1 - y0);
    g.fillText(`окно по t: ${time(thi - tl, 3)}${Math.abs(ratio - 1) > 0.05 ? "; масштабы x и ct различны: световые линии не под 45°" : "; масштабы x и ct равны: световые линии под 45°"}${clipped ? "; низ окна обрезан" : ""}`, 8, topH + 34);
    g.textAlign = "left";
  }

  // --- statistics ---------------------------------------------------------------------------------------------
  function drawStat(f) {
    const cv = cvStat, g = setup(cv), W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const ink = css("--ink"), muted = css("--muted"), line = css("--line");
    const fs = W < 520 ? 10 : 12;
    g.font = `${fs}px system-ui`;
    // table of the four setting pairs
    const cols = [0, 0.11, 0.27, 0.35, 0.43, 0.51, 0.59, 0.80, 0.90];
    const heads = ["пара", "α_A, α_B", "N++", "N+−", "N−+", "N−−", "E ± σ", "закон", "z"];
    const xc = (k) => 8 + (W - 16) * cols[k];
    let y = 34;
    g.fillStyle = muted; heads.forEach((h, k) => g.fillText(h, xc(k), y));
    g.strokeStyle = line; g.beginPath(); g.moveTo(8, y + 5); g.lineTo(W - 8, y + 5); g.stroke();
    for (const c of f.cells) {
      y += fs + 7;
      const sA = c.x === "a" ? 0 : 1, sB = c.y === "b" ? 0 : 1;
      g.fillStyle = COL_SET[sA]; g.fillText(`(${c.x},`, xc(0), y);
      g.fillStyle = COL_SET[sB]; g.fillText(` ${c.y})`, xc(0) + g.measureText(`(${c.x},`).width, y);
      g.fillStyle = ink;
      g.fillText(`${num(c.alA, 4)}°, ${num(c.alB, 4)}°`, xc(1), y);
      c.n.forEach((q, k) => g.fillText(String(q), xc(2 + k), y));
      g.fillStyle = c.N >= NMIN ? ink : muted;  // fewer than NMIN pairs: the estimate is not compared yet
      g.fillText(c.E === null ? "—" : `${c.E.toFixed(3)} ± ${c.se.toFixed(3)}`, xc(6), y);
      g.fillStyle = muted; g.fillText(c.Eref.toFixed(3), xc(7), y);
      if (c.z !== null && c.N >= 30) { g.fillStyle = Math.abs(c.z) < 5 ? css("--ok") : css("--bad"); g.fillText((c.z >= 0 ? "+" : "") + c.z.toFixed(2), xc(8), y); }
      else { g.fillStyle = muted; g.fillText("—", xc(8), y); }
    }
    y += 10;
    // CHSH gauge: |S| on [0, 3] with the bounds 2 and 2√2
    const S = f.S, gx0 = 30, gx1 = W - 24, gy = y + 46;
    const Xs = (s) => gx0 + (gx1 - gx0) * s / 3;
    const T = 2 * Math.SQRT2;
    g.fillStyle = muted; g.fillText("CHSH: S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′); шкала |S|", 8, y + 12);
    const band = (s0, s1, col, lab) => { g.fillStyle = col; g.globalAlpha = 0.18; g.fillRect(Xs(s0), gy - 12, Xs(s1) - Xs(s0), 24); g.globalAlpha = 1; g.fillStyle = muted; g.textAlign = "center"; g.fillText(lab, (Xs(s0) + Xs(s1)) / 2, gy + 34); g.textAlign = "left"; };
    band(0, 2, "#868e96", "локальные модели: |S| ≤ 2");
    band(2, T, "#1c7ed6", "только квантовая");
    band(T, 3, "#e03131", "нет");
    g.strokeStyle = ink; g.lineWidth = 1;
    for (const [s, lab] of [[0, "0"], [1, "1"], [2, "2"], [T, "2√2"], [3, "3"]]) { g.beginPath(); g.moveTo(Xs(s), gy - 14); g.lineTo(Xs(s), gy + 12); g.stroke(); g.fillStyle = ink; g.textAlign = "center"; g.fillText(lab, Xs(s), gy - 18); }
    g.textAlign = "left";
    // the law's exact expectation (engine) and the measured value
    const Sl = Math.abs(f.S_law);
    g.fillStyle = muted; g.beginPath(); g.moveTo(Xs(Sl), gy + 12); g.lineTo(Xs(Sl) - 6, gy + 20); g.lineTo(Xs(Sl) + 6, gy + 20); g.closePath(); g.fill();
    let stxt = `S: набирается — нужно ≥ ${NMIN} пар в каждой из четырёх ячеек (сейчас минимум ${S.Nmin})`;
    if (S.S !== null && S.Nmin >= NMIN) {
      const a = Math.abs(S.S), e = S.se;
      g.strokeStyle = ink; g.lineWidth = 2;
      g.beginPath(); g.moveTo(Xs(Math.max(0, a - 2 * e)), gy); g.lineTo(Xs(Math.min(3, a + 2 * e)), gy); g.stroke();
      g.fillStyle = a > 2 + 5 * e ? "#1c7ed6" : ink; g.beginPath(); g.arc(Xs(a), gy, 6, 0, 2 * Math.PI); g.fill();
      stxt = `S = ${S.S.toFixed(4)} ± ${e.toFixed(4)}  (закон мира: ${f.S_law.toFixed(4)});  (|S| − 2)/σ = ${S.excess === null ? "—" : S.excess.toFixed(1)}`;
    }
    g.fillStyle = ink; g.fillText(stxt, 8, gy + 54);
    g.fillStyle = muted; g.fillText("● измерено (черта ± 2σ)   ▲ точное ожидание закона мира", 8, gy + 54 + fs + 4);
    drawCurve(g, f, 8, gy + 80 + fs, W - 8, Hh - 8, ink, muted, line, fs);
    ovStat.textContent = `Пар в статистике: ${f.counts.seg_detected}${f.counts.seg ? ` (после сброса №${f.counts.seg})` : ""}`;
  }

  function drawCurve(g, f, X0, Y0, X1, Y1, ink, muted, line, fs) {
    if (Y1 - Y0 < 60) return;
    const P = H.period, px0 = X0 + 34, px1 = X1 - 6, py0 = Y0 + 18, py1 = Y1 - 22 - 3 * (fs + 4);
    const Xd = (d) => px0 + (px1 - px0) * (d + P / 2) / P;
    const Ye = (e) => py0 + (py1 - py0) * (1 - e) / 2;
    g.fillStyle = ink; g.fillText("Корреляция E(Δ), Δ = α_A − α_B (по модулю периода " + P + "°)", X0, Y0 + 6);
    g.strokeStyle = line; g.lineWidth = 1; g.strokeRect(px0, py0, px1 - px0, py1 - py0);
    g.fillStyle = muted; g.textAlign = "right";
    for (const e of [-1, -0.5, 0, 0.5, 1]) { g.fillText(String(e), px0 - 4, Ye(e) + 4); g.beginPath(); g.moveTo(px0, Ye(e)); g.lineTo(px1, Ye(e)); g.globalAlpha = e === 0 ? 0.9 : 0.35; g.stroke(); g.globalAlpha = 1; }
    g.textAlign = "center";
    const step = P === 180 ? 45 : 90;
    for (let d = -P / 2; d <= P / 2 + 1e-9; d += step) { g.fillText(`${d}°`, Xd(d), py1 + 14); }
    g.textAlign = "left";
    const quantumWorld = H.law === "quantum";
    const curve = (arr, col, dash, lw) => {
      g.strokeStyle = col; g.lineWidth = lw; g.setLineDash(dash);
      g.beginPath(); for (let k = 0; k < HB.cd.length; k++) { const X = Xd(HB.cd[k]), Yy = Ye(arr[k]); if (k) g.lineTo(X, Yy); else g.moveTo(X, Yy); }
      g.stroke(); g.setLineDash([]);
    };
    const qCol = "#1c7ed6";
    if (quantumWorld || opt.other) curve(HB.cq, qCol, quantumWorld ? [] : [6, 4], quantumWorld ? 2.2 : 1.2);
    if (!quantumWorld || opt.other) curve(HB.ch, COL_LHV, quantumWorld ? [6, 4] : [], quantumWorld ? 1.2 : 2.2);
    // measured points (each angle pair actually used) with ± σ
    const pts = lastBlobs.pts || [];
    for (let k = 0; k + 4 < pts.length; k += 5) {
      const d = pts[k], E = pts[k + 1], se = pts[k + 2], N = pts[k + 3];
      const X = Xd(d);
      g.globalAlpha = N >= NMIN ? 1 : 0.3;
      g.strokeStyle = ink; g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(X, Ye(Math.min(1, E + se))); g.lineTo(X, Ye(Math.max(-1, E - se))); g.stroke();
      g.fillStyle = ink; g.beginPath(); g.arc(X, Ye(E), 3.2, 0, 2 * Math.PI); g.fill();
      g.globalAlpha = 1;
    }
    // the four current setting pairs
    const P2 = P / 2, seen = new Map();
    for (const c of f.cells) {
      const d = ((c.alA - c.alB + P2) % P + P) % P - P2;
      const X = Xd(d), Yy = Ye(c.E === null || c.N < NMIN ? c.Eref : c.E);
      const key = d.toFixed(6), k = seen.get(key) || 0;  // cells with the same delta: labels stacked
      seen.set(key, k + 1);
      g.strokeStyle = COL_SET[c.x === "a" ? 0 : 1]; g.lineWidth = 1.5; g.beginPath(); g.arc(X, Yy, 7 + 3 * k, 0, 2 * Math.PI); g.stroke();
      g.fillStyle = muted; g.font = `${fs - 1}px system-ui`; g.fillText(`${c.x}${c.y}`, X + 9, Yy - 6 - 12 * k); g.font = `${fs}px system-ui`;
    }
    // legend
    const lx = px0; let ly = py1 + 34;
    const leg = (col, dash, txt) => { g.strokeStyle = col; g.lineWidth = 2; g.setLineDash(dash); g.beginPath(); g.moveTo(lx, ly - 4); g.lineTo(lx + 22, ly - 4); g.stroke(); g.setLineDash([]); g.fillStyle = ink; g.fillText(txt, lx + 28, ly); ly += fs + 4; };
    leg(qCol, quantumWorld ? [] : [6, 4], "квантовая механика (движок)" + (quantumWorld ? " — закон мира" : " — для сравнения"));
    leg(COL_LHV, quantumWorld ? [6, 4] : [], (H.model_label || (isPhoton() ? "поляризационная модель ЛСП" : "знаковая модель Белла")) + (quantumWorld ? " — для сравнения" : " — закон мира"));
    g.fillStyle = ink; g.beginPath(); g.arc(lx + 11, ly - 4, 3.2, 0, 2 * Math.PI); g.fill(); g.fillText(`измерено в этом запуске (± σ; бледные — меньше ${NMIN} пар)`, lx + 28, ly);
  }

  // --- panels ---------------------------------------------------------------------------------------------
  function drawInfo(f) {
    const S = f.settings, c = H.c, L = S.L;
    const rows = [["Пары", H.pair_label], ["Закон", H.law === "quantum" ? "квантовая механика (правило Борна)" : `${H.model_label} — модификация`],
      ["Скорость частиц", H.pair === "photon" ? "c" : `${num(H.v / c, 4)} c`], ["Источник — станция L", lenFmt(L)],
      ["Между станциями 2L", lenFmt(2 * L)], ["Полёт L/v", time(f.flight, 5)], ["Свет между станциями 2L/c", time(2 * L / c, 5)],
      ["Выбор настроек", S.switch === "random" ? "случайный, за τ до прихода" : "фиксированный (a, b)"]];
    if (S.switch === "random") {
      const ct = c * S.tau;
      rows.push(["τ", time(S.tau, 4)], ["cτ против 2L", `${lenFmt(ct)} ${ct < 2 * L ? "<" : "≥"} ${lenFmt(2 * L)}`],
        ["Локальность", ct < 2 * L ? "выбор вне светового конуса другой стороны" : "выбор внутри конуса: лазейка открыта"]);
    } else rows.push(["Локальность", "настройки известны заранее: лазейка открыта"]);
    infoBox.replaceChildren(...rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]));
  }
  function drawCounts(f) {
    const c = f.counts, n = c.seg_detected || 0;
    const pct = (k) => (n ? `${num(100 * k / n, 4)} %` : "—");
    const rows = [["выпущено пар", c.emitted], ["зарегистрировано", c.detected], ["потеряно (станции передвинуты)", c.lost],
      ["в полёте", c.in_flight], ["в статистике (после сброса)", n],
      ["выбор вне конуса другой стороны", pct(c.loc)], ["выбор пространственноподобен вылету", pct(c.free)]];
    countBox.replaceChildren(el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, String(v ?? 0))])),
      el("div", { class: "help" }, "Доли — по событиям каждой пары: выбор настройки, вылет, регистрация (интервал s² = c²Δt² − Δx²)."));
  }
  function drawLast(t) {
    const i = lastUpTo(t);
    const items = [];
    for (let k = i; k >= 0 && k > i - 10; k--) {
      const fl = det.fl[k];
      items.push(el("div", { class: "ev" }, el("b", {}, `#${det.id[k]}`), ` ${time(det.t[k], 6)}: `,
        el("span", { style: { color: oCol(det.oA[k]) } }, `A ${sign(det.oA[k])}`), ` (${setLabel("A", det.sA[k])} = ${num(det.alA[k], 4)}°), `,
        el("span", { style: { color: oCol(det.oB[k]) } }, `B ${sign(det.oB[k])}`), ` (${setLabel("B", det.sB[k])} = ${num(det.alB[k], 4)}°)`,
        el("div", { class: "muted" }, `выбор за ${time(det.t[k] - det.tcA[k], 3)} / ${time(det.t[k] - det.tcB[k], 3)} до прихода; `
          + ((fl & (F_LOC_A | F_LOC_B)) === (F_LOC_A | F_LOC_B) ? "оба выбора вне конуса другой стороны" : "выбор в конусе другой стороны")
          + ((fl & (F_FREE_A | F_FREE_B)) === (F_FREE_A | F_FREE_B) ? "; независим от вылета" : ""))));
    }
    lastBox.replaceChildren(...(items.length ? items : [el("div", { class: "muted" }, "Пока нет")]));
  }

  let lastBlobs = {};
  return {
    center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, "Что на экране"),
      el("p", {}, "Слева вверху — установка: источник в центре, станции Алисы (A) и Боба (B) на расстоянии L. У каждой станции две настройки анализатора: для фотонов — ось пропускания поляризатора (линия), для спина ½ — направление магнита Штерна–Герлаха (стрелка); синяя — a/b, фиолетовая — a′/b′, жирная — действующая. Оранжевые точки — частицы пар в полёте; вспышка и знак + или − — исход в момент прихода частицы."),
      el("p", {}, "Слева внизу — пространство-время последней пары: её вылет, мировые линии частиц, события выбора настроек (ромбы) с их будущими световыми конусами и регистрации. Если регистрация на другой стороне лежит вне конуса выбора, никакой сигнал о выборе не мог до неё дойти: это условие закрытия лазейки локальности."),
      el("p", {}, "Справа — счёты совпадений N(±,±) для четырёх пар настроек, корреляции E с ошибкой и ожиданием закона мира, параметр S на шкале с границами 2 (любая локальная модель) и 2√2 (Цирельсон), и кривая E(Δ): точки — измерения этого запуска по всем использованным парам углов (двигайте b в режиме «фиксированный»), линии — законы, посчитанные движком."),
      el("p", {}, "«Выбор настройки: случайный» — генератор станции выбирает a или a′ для каждой частицы за τ до её прихода. «▷ полёт» — скорость, при которой видна одна пара; «▷▷ набор статистики» — быстро набрать пары.")),
    reset() { H = null; HB = null; det = newDet(); lastF = null; lastBlobs = {}; },
    // key frames (player.js): the columns only grow until the cap drops their oldest entries; a key frame is the count
    // and the number dropped, and it is restorable while no more were dropped since (else the player rebuilds)
    snapshot() { return { n: det.n, off: det.off }; },
    restore(k) {
      if (det.off !== k.off) throw new Error("the oldest detections were dropped since this key frame");
      for (const key of Object.keys(det)) if (Array.isArray(det[key])) det[key].length = k.n;
      det.n = k.n; lastF = null;
    },
    onHeader(meta, blobs) { H = meta; HB = { cd: blobs.cd, cq: blobs.cq, ch: blobs.ch }; ctx.setScene && ctx.setScene(meta.title); },
    onMessage(meta, blobs) {
      if (meta.type === "pairs") pushDet(blobs);
    },
    render(frame, t, blobs) {
      if (!H || !frame || !frame.settings) return;
      lastF = frame; lastBlobs = blobs || {};
      drawGeo(frame, t, lastBlobs);
      drawStat(frame);
      drawInfo(frame);
      drawCounts(frame);
      drawLast(t);
    },
  };
}
