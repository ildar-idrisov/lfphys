// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v17 view: scattering of light by a drop. The 3-D scene (the shared environment /static/js/env3d.js): the drop, the
// incident light and its polarisation, the scattered light as polar surfaces (each incident polarisation and
// unpolarised), the geometric rays of the orders p = 0..3, and for small drops the near field |E|^2 in the volume and
// on slice planes. Next to it the sky around the antisolar point (/static/js/imagewin.js), painted from the colour
// strip the run computed against the scattering angle. On the right: the drop's numbers, the phase function with the
// Debye terms, Descartes' and Airy's marks, the polarisation, and the sky's colour strip. Drawing only: every curve,
// colour and number comes from the run.
import { el, fill, fresh2d, num, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createImageWindow } from "/static/js/imagewin.js";

const RANGES = [["all", "0–180°", 0, 180], ["bow", "радуга 120–150°", 118, 152], ["glory", "глория 160–180°", 160, 180],
                ["fwd", "вперёд 0–20°", 0, 20]];
const CURVES = {
  mie: { label: "точный ряд Ми", color: "#ffffff", width: 1.5 },
  deb0: { label: "p = 0: отражение (с дифракцией)", color: "#b8bcc8", dash: [4, 3] },
  deb1: { label: "p = 1: проход насквозь", color: "#5ab0ff", dash: [] },
  deb2: { label: "p = 2: одно внутреннее отражение", color: "#ffd23f", dash: [] },
  deb3: { label: "p = 3: два внутренних отражения", color: "#e07bff", dash: [] },
  airy2: { label: "Эйри p = 2", color: "#ff8a1f", dash: [2, 3] },
  airy3: { label: "Эйри p = 3", color: "#ff5c7a", dash: [2, 3] },
};
const SKY_HALF = 55;  // degrees from the antisolar point shown in the sky window (scattering angles 125-180)
const SKY_PIX = 221;

const swatch = (c, dash) => el("span", { style: { display: "inline-block", background: "#0b0e14", color: c, borderRadius: "3px", padding: "0 4px", marginRight: "4px", fontFamily: "monospace" } }, dash && dash.length ? "╌" : "━");

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  let H = null, monos = [], skyStarts = [], skies = [], nowFrame = null, drawnKey = "", range = "all";
  const hidden = new Set(["airy3"]);
  const skyWin = createImageWindow({ title: "Небо вокруг антисолнечной точки: посчитанный цвет (Солнце за спиной)", describe: describeSky, overlay: skyOverlay });
  const skyPanelBody = el("div", {});
  const cvPhase = el("canvas", { style: { width: "100%", height: "250px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const cvPol = el("canvas", { style: { width: "100%", height: "150px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const cvSky = el("canvas", { style: { width: "100%", height: "170px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const rangeSel = el("select", { title: "Диапазон углов рассеяния" }, RANGES.map(([v, t]) => el("option", { value: v }, t)));
  rangeSel.onchange = () => { range = rangeSel.value; drawnKey = ""; draw(); };
  const dropBox = el("div", { class: "kv" }), legendBox = el("div", { class: "help" }), phaseHelp = el("div", { class: "help" }),
        polHelp = el("div", { class: "help" }), skyBox = el("div", { class: "help" });
  const rightPanels = [panel("Капля и свет", dropBox),
                       panel("Фазовая функция и ряд Дебая", el("div", {}, el("div", { class: "row" }, rangeSel), cvPhase, legendBox, phaseHelp)),
                       panel("Поляризация", el("div", {}, cvPol, polHelp)),
                       panel("Небо: цвет против угла рассеяния", el("div", {}, cvSky, skyBox)),
                       panel("Небо вокруг антисолнечной точки", skyPanelBody),
                       panel("Слои сцены", env.layersPanel), panel("Срез: положение и наклон", env.planePanel)];

  // --- what the cursor's time shows ----------------------------------------------------------------------------------
  const monoNow = () => { const s = nowFrame ? nowFrame.seq : Infinity; for (let k = monos.length - 1; k >= 0; k--) if (monos[k].meta.seq <= s) return monos[k]; return null; };
  const startNow = () => { const s = nowFrame ? nowFrame.sky_seq : Infinity; for (let k = skyStarts.length - 1; k >= 0; k--) if (skyStarts[k].seq <= s) return skyStarts[k]; return null; };
  function skyNow() {
    const st = startNow();
    if (!st) return null;
    const kmax = nowFrame ? nowFrame.k : Infinity;
    let last = null;
    for (const s of skies) if (s.meta.seq === st.seq && s.meta.k < kmax) last = s;
    return last;
  }

  function sizeCanvas(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, Hh = cv.clientHeight;
    if (!W || !Hh) return null;
    cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr);
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = "#0b0e14"; g.fillRect(0, 0, W, Hh);
    return { g, W, Hh };
  }

  // --- the phase function -----------------------------------------------------------------------------------------------
  function drawPhase(M) {
    const c = sizeCanvas(cvPhase); if (!c || !M) return;
    const { g, W, Hh } = c, [, , a0, a1] = RANGES.find((r) => r[0] === range);
    const left = 40, right = 6, top = 8, bot = 22, pw = W - left - right, ph = Hh - top - bot;
    const th = M.blobs.theta, n = th.length;
    const i0 = Math.max(0, Math.floor(a0 / 0.05)), i1 = Math.min(n - 1, Math.ceil(a1 / 0.05));
    const series = { mie: M.blobs.s11, deb0: M.blobs.deb0, deb1: M.blobs.deb1, deb2: M.blobs.deb2, deb3: M.blobs.deb3, airy2: M.blobs.airy2, airy3: M.blobs.airy3 };
    let ymax = -Infinity;
    for (let i = i0; i <= i1; i++) { const v = M.blobs.hi[i]; if (v > 0) ymax = Math.max(ymax, Math.log10(v)); }
    for (const k of ["deb0", "deb1", "deb2", "deb3"]) if (!hidden.has(k)) for (let i = i0; i <= i1; i++) { const v = series[k][i]; if (v > 0) ymax = Math.max(ymax, Math.log10(v)); }
    if (!Number.isFinite(ymax)) return;
    // the lower end: the 1st percentile of the exact curve in the range (at most 12 decades below the top)
    const lv = [];
    for (let i = i0; i <= i1; i++) { const v = series.mie[i]; if (v > 0) lv.push(Math.log10(v)); }
    lv.sort((u, w) => u - w);
    ymax = Math.ceil(ymax + 0.2);
    const ymin = Math.max(ymax - 12, Math.floor((lv.length ? lv[Math.floor(0.01 * (lv.length - 1))] : ymax - 7) - 0.3));
    const X = (a) => left + (a - a0) / (a1 - a0) * pw, Y = (lg) => top + (ymax - lg) / (ymax - ymin) * ph;
    // Alexander's dark band (Descartes' angles of p = 3 and p = 2)
    if (M.meta.alexander) {
      const [b3, b2] = M.meta.alexander;
      if (b2 > a0 && b3 < a1) { g.fillStyle = "rgba(120,120,160,0.16)"; g.fillRect(X(Math.max(a0, b3)), top, X(Math.min(a1, b2)) - X(Math.max(a0, b3)), ph); }
    }
    g.save(); g.beginPath(); g.rect(left, top, pw, ph); g.clip();
    // the envelope of the fine structure inside each 0.05-deg bin (when the run binned a finer grid)
    if (M.meta.n_fine > n) {
      g.fillStyle = "rgba(255,255,255,0.13)";
      g.beginPath();
      for (let i = i0; i <= i1; i++) { const v = M.blobs.hi[i]; const yy = Y(Math.log10(Math.max(v, 1e-300))); if (i === i0) g.moveTo(X(th[i]), yy); else g.lineTo(X(th[i]), yy); }
      for (let i = i1; i >= i0; i--) { const v = M.blobs.lo[i]; g.lineTo(X(th[i]), Y(Math.log10(Math.max(v, 10 ** (ymin - 1))))); }
      g.closePath(); g.fill();
    }
    for (const k of ["deb0", "deb1", "deb3", "deb2", "airy3", "airy2", "mie"]) {
      const s = series[k];
      if (!s || hidden.has(k)) continue;
      const C = CURVES[k];
      g.strokeStyle = C.color; g.lineWidth = C.width || 1.1; g.setLineDash(C.dash || []);
      g.beginPath(); let on = false;
      for (let i = i0; i <= i1; i++) {
        const v = s[i];
        if (!(v > 0)) { on = false; continue; }
        const xx = X(th[i]), yy = Y(Math.log10(v));
        if (on) g.lineTo(xx, yy); else { g.moveTo(xx, yy); on = true; }
      }
      g.stroke();
    }
    g.setLineDash([]);
    // Descartes (dashed), Airy's maxima (ticks), the measured maximum of the p = 2, 3 terms (triangles)
    for (const [p, bw] of Object.entries(M.meta.bows || {})) {
      const col = p === "2" ? "#ffd23f" : "#e07bff";
      if (bw.theta >= a0 && bw.theta <= a1) {
        g.strokeStyle = col; g.setLineDash([5, 4]); g.beginPath(); g.moveTo(X(bw.theta), top); g.lineTo(X(bw.theta), top + ph); g.stroke(); g.setLineDash([]);
        g.fillStyle = col; g.font = "10px system-ui"; g.fillText(`Декарт p=${p}`, X(bw.theta) + 3, top + 10 + (p === "3" ? 12 : 0));
      }
      g.strokeStyle = "#ff8a1f";
      for (const a of bw.airy) if (a >= a0 && a <= a1) { g.beginPath(); g.moveTo(X(a), top + ph); g.lineTo(X(a), top + ph - 8); g.stroke(); }
      const mm = (M.meta.measured || {})[p];
      if (mm !== undefined && mm >= a0 && mm <= a1) { g.fillStyle = col; g.beginPath(); g.moveTo(X(mm), top + ph - 10); g.lineTo(X(mm) - 4, top + ph - 2); g.lineTo(X(mm) + 4, top + ph - 2); g.fill(); }
    }
    g.restore();
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    for (let q = 0; q <= 4; q++) { const a = a0 + (a1 - a0) * q / 4; g.fillText(`${num(a, 4)}°`, X(a) - 10, top + ph + 12); }
    for (let lg = ymin; lg <= ymax; lg += (ymax - ymin > 8 ? 3 : 2)) g.fillText(`10${lg < 0 ? "⁻" : ""}${String(Math.abs(lg)).replace(/\d/g, (d) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d])}`, 2, Y(lg) + 3);
    g.fillText("угол рассеяния θ", left + pw - 92, top + ph + 21);
  }
  function drawLegend(M) {
    if (!M) { fill(legendBox); fill(phaseHelp); return; }
    const keys = ["mie", "deb0", "deb1", "deb2", "deb3"].concat(M.blobs.airy2 ? ["airy2"] : [], M.blobs.airy3 ? ["airy3"] : []);
    fill(legendBox, keys.map((k) => el("label", { style: { display: "inline-block", marginRight: "10px", cursor: "pointer", opacity: hidden.has(k) ? 0.45 : 1 } },
      el("input", { type: "checkbox", checked: !hidden.has(k), onchange: (e) => { if (e.target.checked) hidden.delete(k); else hidden.add(k); drawnKey = ""; drawLegend(M); draw(); } }),
      swatch(CURVES[k].color, CURVES[k].dash), CURVES[k].label)));
    const b = M.meta.bows || {};
    const parts = ["Фазовая функция p(θ) = 4π (dσ/dΩ)/C_sca неполяризованного света (интеграл по сфере 4π), логарифмическая шкала. Белая — точный ряд Ми"
                   + (M.meta.n_fine > M.blobs.theta.length ? `: среднее по ячейкам 0,05° из ${M.meta.n_fine} точек, серая полоса — мелкая интерференционная рябь внутри ячейки (её минимум и максимум)` : "") + "."];
    const dbg = M.meta.debye || {};
    if (dbg.diverging_orders) parts.push(`Цветные — члены ряда Дебая p = 0–3 той же капли. Для этой капли ряд расходится на ${dbg.diverging_orders} порядках (|R¹¹| > 1) и члены до ${num(dbg.amplification, 2)} раз больше полного ответа: это не пути света, а сокращающиеся слагаемые; белую кривую даёт их сумма в замкнутом виде.`);
    else if (dbg.amplification > 10) parts.push(`Цветные — члены ряда Дебая p = 0–3 той же капли: здесь они до ${num(dbg.amplification, 2)} раз больше полного ответа и почти гасят друг друга (m близко к 1), поэтому по отдельности не похожи на белую кривую.`);
    else parts.push("Цветные — члены ряда Дебая (той же капли): каждый — свет одного пути через каплю (p = 0–3 показаны; p ≥ 4 — остаток ряда); сумма всех p с интерференцией даёт белую кривую.");
    if (b["2"]) parts.push(`Штрих — углы Декарта (лучи): p = 2 — ${num(b["2"].theta, 5)}°` + (b["3"] ? `, p = 3 — ${num(b["3"].theta, 5)}°` : "") + "; засечки снизу — максимумы теории Эйри (главный и дополнительные), треугольник — максимум члена p по ряду Дебая. Между дугами — полоса Александра (затенена).");
    else parts.push("Для этой капли лучевой радуги нет (нужно 1 < m < 2 для p = 2).");
    fill(phaseHelp, parts.map((t) => el("div", {}, t)));
  }

  // --- polarisation --------------------------------------------------------------------------------------------------
  function drawPol(M) {
    const c = sizeCanvas(cvPol); if (!c || !M) return;
    const { g, W, Hh } = c, [, , a0, a1] = RANGES.find((r) => r[0] === range);
    const left = 40, right = 6, top = 6, bot = 18, pw = W - left - right, ph = Hh - top - bot;
    const th = M.blobs.theta, n = th.length;
    const i0 = Math.max(0, Math.floor(a0 / 0.05)), i1 = Math.min(n - 1, Math.ceil(a1 / 0.05));
    const X = (a) => left + (a - a0) / (a1 - a0) * pw, Y = (p) => top + (1 - p) / 2 * ph;
    g.strokeStyle = "#3a4350"; g.beginPath(); g.moveTo(left, Y(0)); g.lineTo(left + pw, Y(0)); g.stroke();
    const S = skyNow();
    // the p = 2 term's polarisation only where that term carries light (above 1e-3 of its peak in the range)
    let p2max = 0;
    for (let i = i0; i <= i1; i++) p2max = Math.max(p2max, M.blobs.deb2[i] || 0);
    const lines = [[M.blobs.pol, "#ffffff", [], () => true], [M.blobs.pol_p2, "#ffd23f", [3, 3], (i) => M.blobs.deb2[i] > 1e-3 * p2max]];
    g.save(); g.beginPath(); g.rect(left, top, pw, ph); g.clip();
    for (const [s, col, dash, show] of lines) {
      g.strokeStyle = col; g.setLineDash(dash); g.lineWidth = 1.1; g.beginPath(); let on = false;
      for (let i = i0; i <= i1; i++) {
        if (!show(i)) { on = false; continue; }
        const xx = X(th[i]), yy = Y(s[i]);
        if (on) g.lineTo(xx, yy); else { g.moveTo(xx, yy); on = true; }
      }
      g.stroke();
    }
    if (S && H) {  // the cloud in the chosen light: luminance-weighted polarisation over the sky window
      const [d0, d1, nd] = H.sky.deg;
      g.strokeStyle = "#7bd88f"; g.setLineDash([]); g.beginPath(); let on = false;
      for (let i = 0; i < nd; i++) { const a = d0 + (d1 - d0) * i / (nd - 1); if (a < a0 || a > a1) continue; const xx = X(a), yy = Y(S.blobs.pol[i]); if (on) g.lineTo(xx, yy); else { g.moveTo(xx, yy); on = true; } }
      g.stroke();
    }
    g.restore(); g.setLineDash([]);
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    g.fillText("+1", 2, Y(1) + 8); g.fillText("0", 2, Y(0) + 3); g.fillText("−1", 2, Y(-1));
    for (let q = 0; q <= 4; q++) { const a = a0 + (a1 - a0) * q / 4; g.fillText(`${num(a, 4)}°`, X(a) - 10, top + ph + 12); }
    fill(polHelp, el("div", {}, "Степень линейной поляризации P = (|S₁|² − |S₂|²)/(|S₁|² + |S₂|²) рассеянного неполяризованного света: + — поперёк плоскости рассеяния. Белая — одна капля (ряд Ми), жёлтый пунктир — только член p = 2 (свет радуги поляризован почти полностью), зелёная — облако капель в выбранном свете, взвешенная по яркости Y."));
  }

  // --- the sky ------------------------------------------------------------------------------------------------------
  function drawSkyStrip(M) {
    const c = sizeCanvas(cvSky); if (!c || !H) return;
    const { g, W, Hh } = c, S = skyNow(), st = startNow();
    const left = 30, right = 6, top = 6, bot = 18, pw = W - left - right, band = 46, ph = Hh - top - bot;
    const [d0, d1, nd] = H.sky.deg;
    const X = (a) => left + (a - d0) / (d1 - d0) * pw;
    if (S) {
      const rgb = S.blobs.rgb;
      for (let i = 0; i < nd; i++) { const x0 = X(d0 + (d1 - d0) * (i - 0.5) / (nd - 1)), x1 = X(d0 + (d1 - d0) * (i + 0.5) / (nd - 1)); g.fillStyle = `rgb(${rgb[3 * i]},${rgb[3 * i + 1]},${rgb[3 * i + 2]})`; g.fillRect(x0, top, Math.max(1, x1 - x0 + 0.5), band); }
      const Yv = S.blobs.Y, y0 = top + band + 6, hh = ph - band - 6;
      g.strokeStyle = "#e8e8e8"; g.lineWidth = 1; g.beginPath();
      for (let i = 0; i < nd; i++) { const xx = X(d0 + (d1 - d0) * i / (nd - 1)), yy = y0 + hh * (1 - Math.sqrt(Math.max(0, Yv[i]))); if (i) g.lineTo(xx, yy); else g.moveTo(xx, yy); }
      g.stroke();
    } else { g.fillStyle = "#9aa3ad"; g.font = "11px system-ui"; g.fillText("ждём первую длину волны…", left + 8, top + 24); }
    if (M) for (const [p, bw] of Object.entries(M.meta.bows || {})) {
      if (bw.theta < d0 || bw.theta > d1) continue;
      g.strokeStyle = p === "2" ? "#ffd23f" : "#e07bff"; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(X(bw.theta), top + band); g.lineTo(X(bw.theta), top + ph); g.stroke(); g.setLineDash([]);
    }
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    for (let a = 130; a <= 180; a += 10) g.fillText(`${a}°`, X(a) - 9, top + ph + 12);
    g.fillText("Y", 4, top + band + 18);
    const prog = st ? (S ? `${S.meta.k + 1} из ${st.n}` : `0 из ${st.n}`) : "—";
    const lines = [st ? (st.mode === "white" ? `Солнечный свет: сложено длин волн — ${prog}` + (S ? ` (последняя ${num(S.meta.lam_nm, 4)} нм).` : ".") : `Одна длина волны ${S ? num(S.meta.lam_nm, 4) + " нм" : ""}: цвет — её спектральный цвет.`) : ""];
    if (S) {
      const bw = (M && M.meta.bows) || {}, bowTxt = bw["2"] ? `; дуги по Декарту при ${num(M.meta.lam_nm, 4)} нм: основная ${num(bw["2"].theta, 5)}°` + (bw["3"] ? `, вторичная ${num(bw["3"].theta, 5)}°` : "") : "; лучевой радуги у этой капли нет";
      lines.push(`Сверху — цвет света, рассеянного облаком капель под углом θ (антисолнечная точка — 180°${bowTxt}); снизу — яркость Y (корень). Узлов размера ${S.meta.n_nodes}, шаг по x ${num(S.meta.dx, 3)}` + (S.meta.coarse ? " (грубый: узлов не хватило — рябь и дополнительные дуги размыты в шум)" : "") + `; оценка ошибки суммы по размерам ~${num(S.meta.rel_err, 2)} максимума (по порядку величины)` + (S.meta.tail ? `, обрезка распределения на ±4σ отбросила ${num(S.meta.tail, 2)} его доли` : "") + ".");
      lines.push("Цвет — сумма спектров с функциями CIE 1931 (аппроксимация Уаймена и др.), экспозиция по самому яркому углу, сжатие яркости для экрана.");
    }
    fill(skyBox, lines.map((t) => el("div", {}, t)));
  }
  function drawSkyImage() {
    if (!H) return;
    const S = skyNow(), n = SKY_PIX, rgb = new Uint8Array(3 * n * n);
    const [d0, d1, nd] = H.sky.deg;
    if (S) {
      // each pixel shows the mean colour of the strip over its own angular size (a box filter of the run's strip, so
      // that ripples finer than a pixel are averaged, not aliased into moire)
      const cum = new Float64Array(3 * (nd + 1)), step = (d1 - d0) / (nd - 1), half = SKY_HALF / n;
      for (let k = 0; k < nd; k++) for (let c = 0; c < 3; c++) cum[3 * (k + 1) + c] = cum[3 * k + c] + S.blobs.rgb[3 * k + c];
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
        const a = -SKY_HALF + (i + 0.5) / n * 2 * SKY_HALF, b = SKY_HALF - (j + 0.5) / n * 2 * SKY_HALF;
        const th = 180 - Math.hypot(a, b);
        let k0 = Math.round((th - half - d0) / step), k1 = Math.round((th + half - d0) / step);
        if (k1 < 0 || k0 >= nd) continue;
        k0 = Math.max(0, k0); k1 = Math.min(nd - 1, Math.max(k0, k1));
        const o = 3 * (j * n + i), cnt = k1 - k0 + 1;
        for (let c = 0; c < 3; c++) rgb[o + c] = Math.round((cum[3 * (k1 + 1) + c] - cum[3 * k0 + c]) / cnt);
      }
    }
    const meta = { shape: [n, n], mode: "seen", camera: { kind: "screen", alpha: [-SKY_HALF, SKY_HALF], beta: [-SKY_HALF, SKY_HALF], axis_label: "угол от антисолнечной точки, °" } };
    skyWin.setImage(meta, rgb, { S, deg: H.sky.deg }, S ? `облако капель ${num(H.drop.r_um, 4)} мкм ± ${num(100 * H.drop.width, 3)} %; ${startNow() && startNow().mode === "white" ? "солнечный свет" : "одна длина волны"}` : "ждём первую длину волны…");
  }
  function describeSky(meta, f, i, j) {
    const n = meta.shape[0], a = -SKY_HALF + (i + 0.5) / n * 2 * SKY_HALF, b = SKY_HALF - (j + 0.5) / n * 2 * SKY_HALF;
    const rho = Math.hypot(a, b), th = 180 - rho, parts = [`от антисолнечной точки ${num(rho, 4)}°, угол рассеяния θ = ${num(th, 5)}°`];
    if (f.S && f.deg) {
      const [d0, d1, nd] = f.deg, k = Math.round((th - d0) / (d1 - d0) * (nd - 1));
      if (k >= 0 && k < nd) parts.push(`яркость Y = ${num(f.S.blobs.Y[k], 3)} максимума`, `поляризация P = ${num(f.S.blobs.pol[k], 3)}`);
      else parts.push("вне посчитанных углов");
    }
    return parts.join(" · ");
  }
  function skyOverlay(g, geom) {
    const M = monoNow();
    if (!M) return;
    const cx = geom.left + geom.pw / 2, cy = geom.top + geom.ph / 2, s = geom.pw / (2 * SKY_HALF);
    for (const [p, bw] of Object.entries(M.meta.bows || {})) {
      const r = (180 - bw.theta) * s;
      if (r <= 0 || r > geom.pw / 2) continue;
      g.strokeStyle = p === "2" ? "rgba(255,210,63,0.55)" : "rgba(224,123,255,0.55)"; g.setLineDash([3, 4]); g.lineWidth = 1;
      g.beginPath(); g.arc(cx, cy, r, 0, 2 * Math.PI); g.stroke(); g.setLineDash([]);
    }
    g.fillStyle = "rgba(255,255,255,0.7)"; g.beginPath(); g.arc(cx, cy, 2, 0, 2 * Math.PI); g.fill();
  }

  function drawDrop(M) {
    if (!H) { fill(dropBox); return; }
    const d = H.drop, q = M ? M.meta.Q : null;
    const rows = [["капли", `⟨r⟩ = ${num(d.r_um, 5)} мкм, разброс ${num(100 * d.width, 3)} %`],
                  ["вещество", d.index === "water" ? `вода при ${num(d.t_c, 3)} °C (IAPWS)` : "заданный показатель"],
                  ["среда", `n = ${num(d.n_medium, 5)}`]];
    if (M) rows.push(["λ (одна капля)", `${num(M.meta.lam_nm, 4)} нм`], ["m относительно среды", `${num(M.meta.m[0], 7)}${M.meta.m[1] ? ` + ${num(M.meta.m[1], 3)}i` : ""}`],
                     ["x = 2πa/λ", num(M.meta.x, 6)], ["членов ряда", String(M.meta.n_terms)],
                     ["Q_ext, Q_sca", `${num(q.Qext, 7)}, ${num(q.Qsca, 7)}`], ["Q_abs, Q_back", `${num(q.Qabs, 4)}, ${num(q.Qback, 4)}`],
                     ["g (асимметрия)", num(q.g, 6)]);
    rows.push(["ближнее поле", d.near ? "считается (срезы и объём)" : `не считается: x до ${num(d.x_max, 4)} > 45`]);
    fill(dropBox, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]));
  }

  function draw() {
    const M = monoNow(), S = skyNow();
    const key = `${M ? M.meta.seq : -1}|${S ? S.meta.seq + ":" + S.meta.k : -1}|${range}|${[...hidden].join(",")}`;
    if (key === drawnKey) return;
    drawnKey = key;
    drawPhase(M); drawLegend(M); drawPol(M); drawSkyStrip(M); drawSkyImage(); drawDrop(M);
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, "Рассеяние света каплей"),
      el("p", {}, "Плоская волна света (слева направо, вдоль z; поляризация вдоль x) падает на каплю. Движок решает уравнения Максвелла для шара точно — рядом Ми: коэффициенты aₙ, bₙ каждой парциальной волны, из них — амплитуды S₁(θ), S₂(θ), сечения, поляризация, а для малых капель — поле внутри и вокруг капли (слой «Поле |E|²» и срезы под любым углом)."),
      el("p", {}, "Ряд Дебая раскладывает тот же ответ по путям света: p = 0 — отражение поверхностью (вместе с дифракцией), p = 1 — проход насквозь, p = 2 — одно отражение внутри (первичная радуга), p = 3 — два (вторичная). Лучевая оптика (лучи в 3D, угол Декарта) даёт радугу как сгущение лучей; теория Эйри — главную и дополнительные дуги; точный ряд показывает, где обе ошибаются и откуда глория у 180°."),
      el("p", {}, "Небо: облако капель разного размера (гамма-распределение) в солнечном свете. С каждым шагом времени мира прибавляется одна длина волны: свет капель всех размеров при ней, умноженный на спектр Солнца (чёрное тело 5772 K), переводится в цвет; окно неба рисует этот цвет вокруг антисолнечной точки (Солнце за спиной наблюдателя). Дополнительные дуги видны у одинаковых капель и размываются при разбросе размеров; у мелких капель радуга белеет (туманная радуга), а у антисолнечной точки появляются кольца глории."),
      el("p", {}, "Слева: «Свет» и «Длина волны» меняются сразу (капля пересчитывается, небо складывается заново); размер, разброс, вещество — в «Новый мир». Проверки справа. Значения коэффициентов проверяют «Ряд Дебая» (второй путь счёта тех же aₙ, bₙ) и «Уискомб» (движок против опубликованных чисел). «Угловая сумма при θ = 0», «Энергия» и «Матрица Мюллера» — тождества формы ряда: они проверяют угловые функции, квадратуру и арифметику, но верны и при неверных коэффициентах. Ещё: показатель воды IAPWS, граничные условия ближнего поля (сборка полей); сравнения с теорией Эйри и Декартом — для информации (≈).")),
    reset() { env.reset(); H = null; monos = []; skyStarts = []; skies = []; nowFrame = null; drawnKey = ""; },
    // key frames (player.js): the environment's own, and the lengths of the lists that only grow
    snapshot() { return { env: env.snapshot(), monos: monos.length, starts: skyStarts.length, skies: skies.length }; },
    restore(k) { env.restore(k.env); monos.length = k.monos; skyStarts.length = k.starts; skies.length = k.skies; drawnKey = ""; },
    onHeader(meta) {
      H = meta; env.onHeader(meta); drawnKey = "";
      // the sky next to the 3-D scene, or (when slice windows share the centre: small drops) in its own panel
      const host = H.drop.near ? skyPanelBody : env.center;
      if (skyWin.el.parentNode !== host) host.append(skyWin.el);
      skyPanelBody.parentNode.parentNode.style.display = H.drop.near ? "" : "none";
    },
    onMessage(meta, blobs) {
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "mono") monos.push({ meta, blobs });
      else if (meta.type === "sky_start") skyStarts.push(meta);
      else if (meta.type === "sky") skies.push({ meta, blobs });
    },
    render(frame) {
      if (!H) return;
      nowFrame = frame || null;
      draw();
      env.scene.requestRender();
    },
  };
}
