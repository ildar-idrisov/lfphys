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
import { t, fmt, lang } from "/static/js/i18n.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createImageWindow } from "/static/js/imagewin.js";

const RANGES = [["all", "0–180°", 0, 180], ["bow", t("rainbow {a}–{b}°", { a: 120, b: 150 }), 118, 152],
                ["glory", t("glory {a}–{b}°", { a: 160, b: 180 }), 160, 180], ["fwd", t("forward {a}–{b}°", { a: 0, b: 20 }), 0, 20]];
const CURVES = {
  mie: { label: t("the exact Mie series"), color: "#ffffff", width: 1.5 },
  deb0: { label: t("p = 0: reflection (with diffraction)"), color: "#b8bcc8", dash: [4, 3] },
  deb1: { label: t("p = 1: passage straight through"), color: "#5ab0ff", dash: [] },
  deb2: { label: t("p = 2: one internal reflection"), color: "#ffd23f", dash: [] },
  deb3: { label: t("p = 3: two internal reflections"), color: "#e07bff", dash: [] },
  airy2: { label: t("Airy p = 2"), color: "#ff8a1f", dash: [2, 3] },
  airy3: { label: t("Airy p = 3"), color: "#ff5c7a", dash: [2, 3] },
};
const SKY_HALF = 55;  // degrees from the antisolar point shown in the sky window (scattering angles 125-180)
const SKY_PIX = 221;

const swatch = (c, dash) => el("span", { style: { display: "inline-block", background: "#0b0e14", color: c, borderRadius: "3px", padding: "0 4px", marginRight: "4px", fontFamily: "monospace" } }, dash && dash.length ? "╌" : "━");

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  let H = null, monos = [], skyStarts = [], skies = [], nowFrame = null, drawnKey = "", range = "all";
  const hidden = new Set(["airy3"]);
  const skyWin = createImageWindow({ title: t("The sky around the antisolar point: the computed colour (the Sun behind you)"), describe: describeSky, overlay: skyOverlay });
  const skyPanelBody = el("div", {});
  const cvPhase = el("canvas", { style: { width: "100%", height: "250px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const cvPol = el("canvas", { style: { width: "100%", height: "150px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const cvSky = el("canvas", { style: { width: "100%", height: "170px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const rangeSel = el("select", { title: t("Range of scattering angles") }, RANGES.map(([v, label]) => el("option", { value: v }, label)));
  rangeSel.onchange = () => { range = rangeSel.value; drawnKey = ""; draw(); };
  const dropBox = el("div", { class: "kv" }), legendBox = el("div", { class: "help" }), phaseHelp = el("div", { class: "help" }),
        polHelp = el("div", { class: "help" }), skyBox = el("div", { class: "help" });
  const rightPanels = [panel(t("Drop and light"), dropBox),
                       panel(t("Phase function and the Debye series"), el("div", {}, el("div", { class: "row" }, rangeSel), cvPhase, legendBox, phaseHelp)),
                       panel(t("Polarisation"), el("div", {}, cvPol, polHelp)),
                       panel(t("Sky: colour against the scattering angle"), el("div", {}, cvSky, skyBox)),
                       panel(t("Sky around the antisolar point"), skyPanelBody),
                       panel(t("Scene layers"), env.layersPanel), panel(t("Slice: position and tilt"), env.planePanel)];

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
        g.fillStyle = col; g.font = "10px system-ui"; g.fillText(t("Descartes p={p}", { p }), X(bw.theta) + 3, top + 10 + (p === "3" ? 12 : 0));
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
    g.fillText(t("scattering angle θ"), left + pw - 92, top + ph + 21);
  }
  function drawLegend(M) {
    if (!M) { fill(legendBox); fill(phaseHelp); return; }
    const keys = ["mie", "deb0", "deb1", "deb2", "deb3"].concat(M.blobs.airy2 ? ["airy2"] : [], M.blobs.airy3 ? ["airy3"] : []);
    fill(legendBox, keys.map((k) => el("label", { style: { display: "inline-block", marginRight: "10px", cursor: "pointer", opacity: hidden.has(k) ? 0.45 : 1 } },
      el("input", { type: "checkbox", checked: !hidden.has(k), onchange: (e) => { if (e.target.checked) hidden.delete(k); else hidden.add(k); drawnKey = ""; drawLegend(M); draw(); } }),
      swatch(CURVES[k].color, CURVES[k].dash), CURVES[k].label)));
    const b = M.meta.bows || {};
    const parts = [M.meta.n_fine > M.blobs.theta.length
      ? t("The phase function p(θ) = 4π (dσ/dΩ)/C_sca of unpolarised light (the integral over the sphere is 4π), a logarithmic scale. White: the exact Mie series, the mean over cells of {c}° of {n} points; the grey band is the fine interference ripple inside a cell (its minimum and maximum).", { c: 0.05, n: M.meta.n_fine })
      : t("The phase function p(θ) = 4π (dσ/dΩ)/C_sca of unpolarised light (the integral over the sphere is 4π), a logarithmic scale. White: the exact Mie series.")];
    const dbg = M.meta.debye || {};
    if (dbg.diverging_orders) parts.push(t("Coloured: the terms p = 0–3 of the Debye series of the same drop. For this drop the series diverges at {n} orders (|R¹¹| > 1) and the terms are up to {a:.2g} times larger than the full answer: these are not paths of light but cancelling terms; the white curve is their sum in closed form.", { n: dbg.diverging_orders, a: dbg.amplification }));
    else if (dbg.amplification > 10) parts.push(t("Coloured: the terms p = 0–3 of the Debye series of the same drop: here they are up to {a:.2g} times larger than the full answer and nearly cancel each other (m close to 1), so one by one they do not look like the white curve.", { a: dbg.amplification }));
    else parts.push(t("Coloured: the terms of the Debye series (of the same drop): each is the light of one path through the drop (p = 0–3 shown; p ≥ 4 is the rest of the series); the sum of all p with their interference gives the white curve."));
    if (b["2"]) parts.push(b["3"]
      ? t("Dashed: Descartes' angles (rays): p = 2, {a:.5g}°; p = 3, {b:.5g}°; the ticks below are the maxima of Airy's theory (the main and the supernumerary ones), the triangle the maximum of the term p by the Debye series. Between the bows, Alexander's band (shaded).", { a: b["2"].theta, b: b["3"].theta })
      : t("Dashed: Descartes' angle (rays): p = 2, {a:.5g}°; the ticks below are the maxima of Airy's theory (the main and the supernumerary ones), the triangle the maximum of the term p by the Debye series.", { a: b["2"].theta }));
    else parts.push(t("This drop has no ray rainbow (p = 2 needs 1 < m < 2)."));
    fill(phaseHelp, parts.map((x) => el("div", {}, x)));
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
    fill(polHelp, el("div", {}, t("The degree of linear polarisation P = (|S₁|² − |S₂|²)/(|S₁|² + |S₂|²) of scattered unpolarised light: + across the scattering plane. White: one drop (the Mie series); yellow dashed: the term p = 2 only (the rainbow's light is polarised almost completely); green: the cloud of drops in the chosen light, weighted by the brightness Y.")));
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
    } else { g.fillStyle = "#9aa3ad"; g.font = "11px system-ui"; g.fillText(t("waiting for the first wavelength…"), left + 8, top + 24); }
    if (M) for (const [p, bw] of Object.entries(M.meta.bows || {})) {
      if (bw.theta < d0 || bw.theta > d1) continue;
      g.strokeStyle = p === "2" ? "#ffd23f" : "#e07bff"; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(X(bw.theta), top + band); g.lineTo(X(bw.theta), top + ph); g.stroke(); g.setLineDash([]);
    }
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    for (let a = 130; a <= 180; a += 10) g.fillText(`${a}°`, X(a) - 9, top + ph + 12);
    g.fillText("Y", 4, top + band + 18);
    const done = S ? S.meta.k + 1 : 0;
    const lines = [st ? (st.mode === "white"
      ? (S ? t("Sunlight: wavelengths added {k} of {n} (the last {lam:.4g} nm).", { k: done, n: st.n, lam: S.meta.lam_nm }) : t("Sunlight: wavelengths added {k} of {n}.", { k: done, n: st.n }))
      : (S ? t("One wavelength {lam:.4g} nm: the colour is its spectral colour.", { lam: S.meta.lam_nm }) : t("One wavelength: the colour is its spectral colour."))) : ""];
    if (S) {
      const bw = (M && M.meta.bows) || {};
      const bowTxt = bw["2"] ? (bw["3"]
        ? t("the bows by Descartes at {lam:.4g} nm: primary {a:.5g}°, secondary {b:.5g}°", { lam: M.meta.lam_nm, a: bw["2"].theta, b: bw["3"].theta })
        : t("the bows by Descartes at {lam:.4g} nm: primary {a:.5g}°", { lam: M.meta.lam_nm, a: bw["2"].theta }))
        : t("this drop has no ray rainbow");
      const parts = [t("Above: the colour of the light scattered by the cloud of drops at the angle θ (the antisolar point is 180°; {bows}); below: the brightness Y (square root). Size nodes {n}, the step in x {dx:.3g}", { bows: bowTxt, n: S.meta.n_nodes, dx: S.meta.dx })];
      if (S.meta.coarse) parts.push(t("coarse: too few nodes, the ripple and the supernumerary bows are washed into noise"));
      parts.push(t("the error estimate of the sum over the sizes ~{e:.2g} of the maximum (by the order of magnitude)", { e: S.meta.rel_err }));
      if (S.meta.tail) parts.push(t("the cut of the distribution at ±4σ dropped {f:.2g} of it", { f: S.meta.tail }));
      lines.push(parts.join("; ") + ".");
      lines.push(t("The colour is the sum of the spectra with the CIE 1931 functions (the approximation of Wyman et al.), the exposure set by the brightest angle, the brightness compressed for the screen."));
    }
    fill(skyBox, lines.map((x) => el("div", {}, x)));
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
    const meta = { shape: [n, n], mode: "seen", camera: { kind: "screen", alpha: [-SKY_HALF, SKY_HALF], beta: [-SKY_HALF, SKY_HALF], axis_label: t("angle from the antisolar point, °") } };
    const white = startNow() && startNow().mode === "white";
    skyWin.setImage(meta, rgb, { S, deg: H.sky.deg }, S ? (white
      ? t("a cloud of drops {r:.4g} µm ± {w:.3g} %; sunlight", { r: H.drop.r_um, w: 100 * H.drop.width })
      : t("a cloud of drops {r:.4g} µm ± {w:.3g} %; one wavelength", { r: H.drop.r_um, w: 100 * H.drop.width })) : t("waiting for the first wavelength…"));
  }
  function describeSky(meta, f, i, j) {
    const n = meta.shape[0], a = -SKY_HALF + (i + 0.5) / n * 2 * SKY_HALF, b = SKY_HALF - (j + 0.5) / n * 2 * SKY_HALF;
    const rho = Math.hypot(a, b), th = 180 - rho, parts = [t("{r:.4g}° from the antisolar point, scattering angle θ = {th:.5g}°", { r: rho, th })];
    if (f.S && f.deg) {
      const [d0, d1, nd] = f.deg, k = Math.round((th - d0) / (d1 - d0) * (nd - 1));
      if (k >= 0 && k < nd) parts.push(t("brightness Y = {y:.3g} of the maximum", { y: f.S.blobs.Y[k] }), t("polarisation P = {p:.3g}", { p: f.S.blobs.pol[k] }));
      else parts.push(t("outside the computed angles"));
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
    const rows = [[t("drops"), t("⟨r⟩ = {r:.5g} µm, spread {w:.3g} %", { r: d.r_um, w: 100 * d.width })],
                  [t("substance"), d.index === "water" ? t("water at {tc:.3g} °C (IAPWS)", { tc: d.t_c }) : t("a given index")],
                  [t("surrounding medium"), `n = ${num(d.n_medium, 5)}`]];
    if (M) rows.push([t("λ (one drop)"), t("{lam:.4g} nm", { lam: M.meta.lam_nm })], [t("m relative to the medium"), `${num(M.meta.m[0], 7)}${M.meta.m[1] ? ` + ${num(M.meta.m[1], 3)}i` : ""}`],
                     ["x = 2πa/λ", num(M.meta.x, 6)], [t("terms of the series"), fmt(M.meta.n_terms, "d")],
                     ["Q_ext, Q_sca", `${num(q.Qext, 7)}, ${num(q.Qsca, 7)}`], ["Q_abs, Q_back", `${num(q.Qabs, 4)}, ${num(q.Qback, 4)}`],
                     [t("g (asymmetry)"), num(q.g, 6)]);
    rows.push([t("near field"), d.near ? t("computed (slices and volume)") : t("not computed: x up to {x:.4g} > {lim}", { x: d.x_max, lim: 45 })]);
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
      el("h4", {}, t("Light scattered by a drop")),
      el("p", {}, t("A plane wave of light (from left to right, along z; polarised along x) falls on a drop. The engine solves Maxwell's equations for a sphere exactly, by the Mie series: the coefficients aₙ, bₙ of every partial wave, and from them the amplitudes S₁(θ), S₂(θ), the cross sections, the polarisation, and for small drops the field inside and around the drop (the layer “Field |E|²” and slices at any angle).")),
      el("p", {}, t("The Debye series splits the same answer by the paths of light: p = 0 is the reflection by the surface (together with diffraction), p = 1 the passage straight through, p = 2 one reflection inside (the primary rainbow), p = 3 two (the secondary). Ray optics (the rays in 3-D, Descartes' angle) gives the rainbow as a crowding of rays; Airy's theory gives the main and the supernumerary bows; the exact series shows where both are wrong and where the glory near 180° comes from.")),
      el("p", {}, t("The sky: a cloud of drops of different sizes (a gamma distribution) in sunlight. With every step of the world's time one wavelength is added: the light of drops of all sizes at it, multiplied by the spectrum of the Sun (a black body at {T} K), is turned into a colour; the sky window paints this colour around the antisolar point (the Sun behind the observer). The supernumerary bows are seen for equal drops and blur when the sizes spread; for small drops the rainbow turns white (a fogbow), and the rings of the glory appear around the antisolar point.", { T: 5772 })),
      el("p", {}, t("On the left: “Light” and “Wavelength” change at once (the drop is recomputed, the sky builds up anew); the size, the spread, the substance are in “New world”. The checks are on the right. The coefficients' values are tested by “Debye series” (a second route to the same aₙ, bₙ) and “Wiscombe” (the engine against published numbers). “Angular sum at θ = 0”, “Energy” and “Mueller matrix” are identities of the series' form: they test the angular functions, the quadrature and the arithmetic, but hold also for wrong coefficients. Also: the index of water by IAPWS, the boundary conditions of the near field (the assembly of the fields); the comparisons with Airy's theory and Descartes are for information (≈)."))),
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
