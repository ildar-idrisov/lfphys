// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v02 view: the apparatus seen from above (the computed wave behind the slits, particles in flight, flow lines)
// and the screen (individual detections and their histogram against the run's own expectation).
// All data come from the run: detections are events with their computed positions and times, the map and the
// curves are computed by the run for the current apparatus segment.
import { css, el, fresh2d, num, panel, time } from "/static/js/ui.js";

const F_DARK = 1, F_R1 = 2, F_READ = 4, F_SCAT = 8, F_REC = 16, F_MIX = 32;

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
  const opt = { filter: "all", phase0: 0, phaseW: 60, segOnly: true, curves: true, map: true, bohm: true, log: false };

  // --- DOM --------------------------------------------------------------------------------------------
  const selFilter = el("select", { title: "Какие частицы показывать на экране" },
    el("option", { value: "all" }, "все частицы"),
    el("option", { value: "r0" }, "детектор пути показал 0"), el("option", { value: "r1" }, "детектор пути показал 1"),
    el("option", { value: "noscat" }, "без рассеянного фотона"),
    el("option", { value: "phase" }, "рассеянный фотон зарегистрирован: фаза Δk·d в окне"),
    el("option", { value: "dark" }, "только темновые (известно лишь в симуляции)"));
  const inPhase = el("input", { type: "number", value: 0, step: 15, style: { width: "5em" }, title: "центр окна фазы, °" });
  const inPhaseW = el("input", { type: "number", value: 60, step: 15, style: { width: "5em" }, title: "ширина окна, °" });
  const phaseBox = el("span", { style: { display: "none" } }, " φ₀ ", inPhase, "° ± ", inPhaseW, "°/2");
  const cbSeg = el("input", { type: "checkbox", checked: true });
  const cbCurves = el("input", { type: "checkbox", checked: true });
  const cbMap = el("input", { type: "checkbox", checked: true });
  const cbBohm = el("input", { type: "checkbox", checked: true });
  const cbLog = el("input", { type: "checkbox" });
  const btnFly = el("button", { title: "Скорость, при которой виден полёт одной частицы (≈2 с на пролёт)" }, "▷ полёт");
  const btnBuild = el("button", { title: "Скорость набора картины (≈40 частиц в секунду)" }, "▷▷ набор картины");
  const cvApp = el("canvas"), cvScr = el("canvas");
  const ovApp = el("div", { class: "overlay" }), ovScr = el("div", { class: "overlay" });
  const toolbar = el("div", { class: "toolbar" }, el("span", { class: "muted" }, "Экран:"), selFilter, phaseBox,
    el("label", { title: "Показывать только текущий отрезок (после последнего изменения установки)" }, cbSeg, " текущий отрезок"),
    el("label", {}, cbCurves, " ожидание"), el("label", {}, cbLog, " лог. шкала карты"),
    el("label", {}, cbMap, " волна"), el("label", {}, cbBohm, " линии тока"), btnFly, btnBuild);
  const quick = el("div", { class: "toolbar quick", title: "Установка: меняется сразу (то же, что в панели слева)" },
    el("span", { class: "muted" }, "Установка:"),
    ctx.liveControl ? [ctx.liveControl("wp_mode", { label: "наблюдатель" }), ctx.liveControl("wp_theta", { label: "связь θ, °" }),
      ctx.liveControl("L2_m", { label: "экран, м" }), ctx.liveControl("a_um", { label: "щель, мкм" }),
      ctx.liveControl("d_um", { label: "период, мкм" })] : null);
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick, toolbar,
    el("div", { class: "split" },
      el("div", {}, el("div", { class: "canvas-wrap" }, cvApp, ovApp)),
      el("div", {}, el("div", { class: "canvas-wrap" }, cvScr, ovScr))));
  const infoBox = el("div", { class: "kv" });
  const statBox = el("div", {});
  const storyBox = el("div", { class: "events" });
  const approxBox = el("div", { class: "help" });
  const vecBox = el("div", {});
  const rightPanels = [panel("Частица", infoBox), panel("Модель экрана со щелями", vecBox), panel("Счётчики и статистика", statBox),
    panel("Приближения этого отрезка", approxBox), panel("Последние частицы: цепочка причин", storyBox)];

  selFilter.onchange = () => { opt.filter = selFilter.value; phaseBox.style.display = opt.filter === "phase" ? "" : "none"; full(); };
  inPhase.onchange = () => { opt.phase0 = Number(inPhase.value); full(); };
  inPhaseW.onchange = () => { opt.phaseW = Number(inPhaseW.value); full(); };
  for (const [cb, k] of [[cbSeg, "segOnly"], [cbCurves, "curves"], [cbMap, "map"], [cbBohm, "bohm"], [cbLog, "log"]])
    cb.onchange = () => { opt[k] = cb.checked; full(); };
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
  function countUpTo(t) {  // detections are in time order
    let lo = 0, hi = det.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (det.t[m] <= t) lo = m + 1; else hi = m; }
    return lo;
  }
  function segAt(t) { let s = segs[0]; for (const g of segs) if (g.t <= t) s = g; return s; }
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
    return css("--ink");
  }

  // --- apparatus view -----------------------------------------------------------------------------------
  function drawApparatus(frame, t) {
    const cv = cvApp, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(t);
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
      const lab = seg.z_paraxial_why === "cost" ? "не сверено с точным решением" : "параксиально неточно (>1 %)";
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
    // source side
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    g.fillText(geo.L1 ? `источник, L₁ = ${num(geo.L1, 4)} м` : "плоская волна", 4, 12);
    g.fillStyle = "#f08c00";
    g.beginPath(); g.arc(10, top + mh / 2, 4, 0, 2 * Math.PI); g.fill();
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
    const els = [[app.el1, app.el1_angle], [app.el2, app.el2_angle]];
    els.forEach(([k, ang], j) => {
      if (!k || k === "none" || j >= xs.length) return;
      const Y = yOf(xs[j] / w0);
      g.fillStyle = "#ae3ec9"; g.fillRect(plateX - 10, Y - 6, 6, 12);
      g.fillText(`${k} ${ang}°`, 18, Y + 4);
    });
    if (app.wp_mode === "qubit") {
      const Y = yOf(xs[app.wp_slit - 1] / w0);
      g.strokeStyle = "#e8590c"; g.lineWidth = 2; g.beginPath(); g.arc(plateX - 16, Y, 6, 0, 2 * Math.PI); g.stroke();
      g.fillStyle = "#e8590c"; g.fillText(`детектор θ=${app.wp_theta}°`, 18, Y - 9);
    }
    if (app.wp_mode === "microscope") {
      g.strokeStyle = "#2b8a3e"; g.lineWidth = 1.5; g.beginPath();
      for (let k = 0; k <= 40; k++) { const Y = top + mh * k / 40; g.lineTo(plateX - 18 + 4 * Math.sin(k * 1.3), Y); }
      g.stroke(); g.fillStyle = "#2b8a3e"; g.fillText(`зонд λ=${num(app.mic_lambda_nm, 3)} нм`, 18, bot - 4);
    }
    if (app.ab_flux && xs.length >= 2) {
      const Y = yOf((xs[0] + xs[1]) / 2 / w0); g.fillStyle = "#1c7ed6"; g.fillText("⊗ Φ=" + app.ab_flux + " h/e", plateX - 60, Y + 4);
    }
    if (app.analyzer === "on") { g.fillStyle = "#ae3ec9"; g.fillRect(W - 14, top, 4, mh); g.fillText(`анализатор ${app.analyzer_angle}°`, W - 120, top - 4); }
    // screen
    g.fillStyle = css("--ink"); g.fillRect(W - 8, top, 3, mh);
    // particles in flight
    const L1 = geo.L1 || 0;
    let nfl = 0;
    const fl = flightOf(frame);
    for (let q = 0; q + 1 < fl.length; q += 2) {
      const te = fl[q], v = fl[q + 1];  // each particle flies at its own group velocity
      if (te > t) continue;
      const z = v * (t - te) - L1;
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
    ovApp.textContent = `Вид сверху: волна за щелями (|ψ|², нормирована в каждом сечении), z — логарифм. шкала от 2a до экрана; x отнесён к ширине пучка. В полёте: ${nfl}. Отрезок ${seg.seg}: ${seg.apparatus}` + (seg.vector ? ". Экран — идеальный проводник; карта и линии тока — скалярная модель (Кирхгоф, параксиально)." : "");
  }

  // --- screen -------------------------------------------------------------------------------------------
  function drawScreen(frame, t) {
    const cv = cvScr, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(t);
    const SU = (seg && seg.setup) || H;
    const half = SU.geometry.half;
    const dotsH = Math.round(Hh * 0.55), histTop = dotsH + 10;
    let histH = Hh - histTop - 20;
    const xOf = (x) => 8 + (W - 16) * (x + half) / (2 * half);
    const n = countUpTo(t);
    // dots: incremental offscreen drawing
    const key = [opt.filter, opt.phase0, opt.phaseW, opt.segOnly, seg ? seg.seg : -1, W, dotsH, document.documentElement.dataset.theme].join("|");
    if (!dotsState || dotsState.key !== key || n < dotsState.n) {
      offDots.width = W * 2; offDots.height = dotsH * 2;
      dotsState = { key, n: 0 };
    }
    const og = offDots.getContext("2d");
    for (let i = dotsState.n; i < n; i++) {
      if (!pass(i, seg)) continue;
      og.fillStyle = dotColor(i);
      og.fillRect(2 * xOf(det.x[i]) - 1, 2 * (dotsH / 2 + det.y[i] * (dotsH - 10)) - 1, 2, 2);
    }
    dotsState.n = n;
    g.drawImage(offDots, 0, 0, W, dotsH);
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
    if (opt.curves && seg && tot > 0) {
      const name = { all: ["all", "cl"], r0: ["r0", "cl0"], r1: ["r1", "cl1"], noscat: ["noscat", null] }[opt.filter];
      if (!opt.segOnly) curveNote = " Кривые ожидания показываются только для текущего отрезка.";
      else if (!name) curveNote = " Для этого отбора ожидание не считается.";
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
        for (const arr of [expC, clC, othC, teC, tmC]) if (arr) for (const v of arr) cmax = Math.max(cmax, v);
      }
    }
    const fullH = histH;
    if (diffC) histH = Math.round(fullH * 0.72);
    const yOfC = (c) => histTop + histH * (1 - c / cmax);
    g.fillStyle = css("--accent"); g.globalAlpha = 0.55;
    const bw = (W - 16) / nb;
    for (let b = 0; b < nb; b++) if (counts[b]) g.fillRect(8 + b * bw, yOfC(counts[b]), Math.max(bw, 1), histTop + histH - yOfC(counts[b]));
    g.globalAlpha = 1;
    const curve = (arr, col, dash) => {
      if (!arr) return;
      g.strokeStyle = col; g.lineWidth = 1.6; g.setLineDash(dash || []);
      g.beginPath(); for (let b = 0; b < nb; b++) { const X2 = 8 + (b + 0.5) * bw, Y = yOfC(arr[b]); if (b) g.lineTo(X2, Y); else g.moveTo(X2, Y); }
      g.stroke(); g.setLineDash([]);
    };
    curve(clC, "#868e96", [5, 4]);
    curve(teC, "#2f9e44", [2, 3]);
    curve(tmC, "#ae3ec9", [2, 3]);
    curve(othC, "#1c7ed6");
    curve(expC, "#e8590c");
    g.strokeStyle = css("--line"); g.strokeRect(8, histTop, W - 16, histH);
    if (diffC) {  // the difference vector − scalar in a strip of its own (symmetric scale)
      const top = histTop + histH + 6, sh = fullH - histH - 6, mid = top + sh / 2;
      let dm = 1e-300; for (const v of diffC) dm = Math.max(dm, Math.abs(v));
      g.strokeStyle = css("--line"); g.strokeRect(8, top, W - 16, sh);
      g.setLineDash([3, 3]); g.beginPath(); g.moveTo(8, mid); g.lineTo(W - 8, mid); g.stroke(); g.setLineDash([]);
      g.strokeStyle = "#c92a2a"; g.lineWidth = 1.4; g.beginPath();
      for (let b = 0; b < nb; b++) { const X2 = 8 + (b + 0.5) * bw, Y = mid - (sh / 2 - 2) * diffC[b] / dm; if (b) g.lineTo(X2, Y); else g.moveTo(X2, Y); }
      g.stroke();
      g.fillStyle = css("--muted"); g.font = "10px system-ui";
      g.fillText(`разность вектор − скаляр (±${num(dm, 3)} отсчётов)`, 12, top + 11);
    }
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    g.fillText(lenFmt(-half), 8, Hh - 5); g.fillText("0", W / 2 - 3, Hh - 5); g.fillText(lenFmt(half), W - 60, Hh - 5);
    const vecNote = !vec ? "" : vec.hits === "vector"
      ? " Экран-проводник: попадания и оранжевая линия — векторное решение (поток энергии), синяя — скалярное решение Кирхгофа в тех же единицах (с той же эффективностью детектора), зелёная/фиолетовая точки — вклады TE/TM" + (vec.diff_note ? "; " + vec.diff_note + "." : ", красная — разность вектор − скаляр.")
      : " Экран-проводник, но попадания и оранжевая линия — скалярная модель (" + (vec.why || "") + "); синяя — только форма векторного решения тех же щелей без элементов и анализатора, нормированная на ту же сумму (единицы у них разные; разность не показывается).";
    ovScr.textContent = `Экран: ${tot} отсчётов показано (из ${n} всего). Гистограмма; оранжевая линия — ожидание запуска (с темновыми отсчётами), серая пунктирная — сумма щелей без интерференции.` + vecNote + curveNote;
  }

  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }

  function lenFmt(x) {
    const a = Math.abs(x);
    if (a >= 1) return num(x, 3) + " м";
    if (a >= 1e-3) return num(x * 1e3, 3) + " мм";
    if (a >= 1e-6) return num(x * 1e6, 3) + " мкм";
    if (a >= 1e-9) return num(x * 1e9, 3) + " нм";
    return num(x * 1e12, 3) + " пм";
  }

  // --- panels ---------------------------------------------------------------------------------------------
  function drawInfo() {
    const G = now(), p = G.particle;
    const rows = [["Частица", p.label], ["Длина волны λ", lenFmt(p.lambda_m)], ["Энергия", num(p.E_eV, 8) + " эВ" + (p.mass_kg ? ` (кинетическая ${num(p.Ekin_eV, 6)} эВ)` : "")],
      [p.mass_kg ? "Частота де Бройля E/h (с энергией покоя)" : "Частота", num(p.nu_Hz, 6) + " Гц"], ["Импульс", num(p.p, 6) + " кг·м/с"], ["Скорость", num(p.v, 8) + " м/с" + ` (${num(p.beta, 6)} c)`],
      ["Внутреннее состояние", p.internal === "pol" ? "поляризация (2 состояния)" : p.internal === "spin" ? "спин ½" : "нет"],
      ["Щели", `${G.geometry.n} × ${lenFmt(G.geometry.a)}, период ${lenFmt(G.geometry.d)}`], ["До экрана", lenFmt(G.geometry.L2)],
      ["Полёт до экрана", time(G.t_flight, 6)], ["Темп источника", num(G.rate, 4) + " 1/с"]];
    infoBox.replaceChildren(...rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]));
  }
  function drawStats(frame) {
    const c = frame.counts || {};
    const rows = [["выпущено", c.emitted], ["поглощено у щелей", c.absorbed_slits], ["поглощено анализатором", c.absorbed_an], ["мимо экрана", c.missed],
      ["не зарегистрировано", c.undetected], ["зарегистрировано", c.detected], ["темновых", c.dark],
      ["рассеяли фотон", c.scattered], ["ударов GRW", c.grw_hits], ["переходных (щели и экран в разных отрезках)", c.mixed],
      ["в текущем отрезке", frame.n_seg]];
    const items = [el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v ?? 0)]))];
    if (c.reflected) items[0].append(el("span", {}, "отражено экраном-проводником"), el("span", { class: "mono" }, c.reflected));
    if (frame.coh && frame.coh.why) {
      items.push(el("p", {}, "Степень когерентности щелей |γ₁₂| не определена: " + frame.coh.why));
    } else if (frame.coh) {
      const h = frame.coh;
      items.push(el("p", {}, "Степень когерентности щелей |γ₁₂|: по гистограмме ",
        el("b", { class: "mono" }, h.hist === null ? "—" : num(h.hist, 4)), h.err ? ` ± ${num(h.err, 2)}` : "",
        "; ожидание запуска ", el("b", { class: "mono" }, h.expected === null ? "—" : num(h.expected, 4)),
        el("div", { class: "help" }, "Фит гистограммы по рассчитанным функциям щелей |A₁|², |A₂|², A₁A₂*: 1 — полная интерференция, 0 — её нет.")));
    }
    if (frame.chi2 && frame.chi2.x2 !== null) {
      const ch = frame.chi2;
      items.push(el("p", {}, `Согласие гистограммы с ожиданием: χ² = ${num(ch.x2, 4)} на ${ch.dof} ст. св., p = ${num(ch.p, 3)}`,
        el("span", { class: ch.p > 1e-3 ? "st-ok" : "st-bad" }, ch.p > 1e-3 ? " ✓" : " ✗")));
    }
    if (frame.lag) items.push(el("p", { class: "st-bad" }, "Вычисление не успевает за выбранной скоростью: мир идёт медленнее."));
    statBox.replaceChildren(...items);
  }
  function drawVector(t) {
    const seg = segAt(t), v = seg && seg.vector;
    if (!v) { vecBox.replaceChildren(el("p", { class: "help" }, "Скалярная модель: поле в щели равно падающему (граничные условия Кирхгофа). Для фотонов с плоской монохроматической волной и щелями не шире 20.7 λ (k·a ≤ 130) можно выбрать идеальный проводник (векторная дифракция) в настройках «Щели и экран».")); return; }
    const rows = [["Экран", `идеальный проводник, толщина ${lenFmt(v.t)}` + (v.t === 0 ? " (тонкий)" : "")],
      ["Попадания", v.hits === "vector" ? "по векторному решению (поток энергии)" : "по скалярной модели"],
      ["Пропускание на ширину щели T_TE (E вдоль щелей)", num(v.T_TE, 5)], ["T_TM (H вдоль щелей)", num(v.T_TM, 5)],
      ["T по Кирхгофу (скаляр)", num(v.T_K, 5)], ["Веса поляризаций H(TM) / V(TE)", `${num(v.wH, 3)} / ${num(v.wV, 3)}`],
      ["Баланс мощности TE / TM (отн.)", `${num(v.rel_TE, 2)} / ${num(v.rel_TM, 2)}`],
      ["Оценка ошибки метода TE / TM (T и поток на экране)", `${num(v.err_TE, 2)} / ${num(v.err_TM, 2)}`],
      ["Метод", (v.method === "edge" ? "базис с краевыми условиями" : "волноводные моды") + `, ${v.modes} мод на щель`]];
    if (v.hits === "vector") rows.push(["Доля прошедших фотонов (полоса n·d = " + lenFmt(v.W) + (v.n === 1 ? "; одна щель: условная ширина — период d" : "") + ")", num(v.p_trans, 4)]);
    const items = [el("div", { class: "kv" }, rows.flatMap(([k, x]) => [el("span", {}, k), el("span", { class: "mono" }, x)]))];
    if (v.hits !== "vector") items.push(el("p", { class: "help" }, "Попадания — по скалярной модели: " + (v.why || "") + "."));
    vecBox.replaceChildren(...items);
  }
  function drawStories(frame, t) {
    const st = stories.filter((s) => s.t_det <= t).slice(-10);
    storyBox.replaceChildren(...st.slice().reverse().map((s) => el("div", { class: "ev" },
      el("b", {}, `#${s.id}`), ` вылет ${time(s.t_emit, 6)}; λ = ${lenFmt(s.lambda)}`, s.x_src ? `; точка источника ${lenFmt(s.x_src)}` : "",
      `; состояние ${s.state}`, s.scattered ? `; рассеяла фотон (фаза Δk·d = ${num(s.kick_phase, 3)} рад${s.recorded ? ", фотон зарегистрирован" : ""})` : "",
      s.grw_hits ? `; ударов GRW: ${s.grw_hits}` : "",
      s.overlap12 !== null && s.overlap12 !== undefined ? `; перекрытие меток |⟨m₂|m₁⟩| = ${num(s.overlap12, 4)}` : "",
      el("div", {}, "→ " + s.fate + ` (${time(s.t_det, 6)})`))));
  }

  return {
    center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, "Что на экране"),
      el("p", {}, "Слева — установка сверху: щели, элементы у щелей, детектор пути, зонд микроскопа; за щелями — рассчитанная волна этого отрезка (|ψ|² по сечениям), белые полосы — частицы в полёте (их волна занимает всё сечение), голубые линии — линии тока: для чистого состояния без декогеренции — траектории де Бройля–Бома (для фотона — линии потока энергии), при декогеренции — линии усреднённого тока ансамбля, при GRW не показываются. Карта — ожидаемая волна ансамбля запуска (с декогеренцией)."),
      el("p", {}, "Справа — экран: каждая точка — одна зарегистрированная частица; ниже — гистограмма. Оранжевая кривая — ожидание этого запуска (среднее по его же частицам), серая — без интерференции. Сортировка по показанию детектора или по направлению рассеянного фотона показывает, как интерференция возвращается в подвыборках (ластик)."),
      el("p", {}, "Наблюдатель не выключает интерференцию правилом: каждая частица уносит от щелей метки (поляризацию, спин, состояние детектора, отдачу фотона), и картина считается правилом Борна с их перекрытием.")),
    reset() { H = null; X = null; segs = []; stories = []; det = newCols(); dotsState = null; histState = null; mapCache = null; },
    // key frames (player.js): segments and detections only grow (lengths); the stories are capped, so they are copied
    snapshot() { return { segs: segs.length, det: det.n, stories: stories.slice() }; },
    restore(k) {
      segs.length = k.segs; det.n = k.det; stories = k.stories.slice();
      dotsState = null; histState = null; mapCache = null;
      const last = segs[segs.length - 1];
      approxBox.replaceChildren(...((last && last.approx) || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• " + a)));
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
        approxBox.replaceChildren(...(meta.approx || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• " + a)));
        dotsState = null; histState = null;
        if (meta.setup) { ctx.setScene && ctx.setScene(meta.setup.title); drawInfo(); }
      } else if (meta.type === "detections") {
        push(blobs);
      } else if (meta.type === "stories") {
        for (const st of meta.stories) stories.push(st);
        if (stories.length > 2000) stories.splice(0, stories.length - 2000);
      }
    },
    render(frame, t, blobs) {
      if (!H) return;
      curBlobs = blobs || {};
      lastFrame = frame;
      drawApparatus(frame, t);
      drawScreen(frame, t);
      drawStats(frame);
      drawVector(t);
      drawStories(frame, t);
    },
  };
}
