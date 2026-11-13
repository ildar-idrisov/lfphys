// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v03 view: the wave of the current particle over the potential, the detectors, the outcome in the chosen reading
// (Copenhagen collapse, Bohm trajectory, Everett branches), the space-time map of |psi|^2 with Bohm trajectories,
// and the statistics of outcomes against the run's own probabilities. Everything comes from the run.
import { t, fmt } from "/static/js/i18n.js";
import { css, el, fresh2d, num, panel, time } from "/static/js/ui.js";

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
  let H = null, segs = [], clicks = [];
  const quick = el("div", { class: "toolbar quick", title: t("Set-up: changes at once (the same as in the panel on the left)") },
    el("span", { class: "muted" }, t("Set-up:")),
    ctx.liveControl("scenario", { label: t("potential") }), ctx.liveControl("V0", { label: t("V₀, eV") }),
    ctx.liveControl("width", { label: t("a, nm") }), ctx.liveControl("energy", { label: t("E, eV") }),
    ctx.liveControl("interp", { label: t("interpretation") }));
  const cvWave = el("canvas"), cvMap = el("canvas"), cvStat = el("canvas");
  const ovWave = el("div", { class: "overlay" }), ovMap = el("div", { class: "overlay" }), ovStat = el("div", { class: "overlay" });
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick,
    el("div", { style: { flex: "1.25", minHeight: 0, display: "flex", flexDirection: "column", borderBottom: "1px solid var(--line)" } },
      el("div", { class: "canvas-wrap" }, cvWave, ovWave)),
    el("div", { class: "split", style: { flex: 1 } },
      el("div", {}, el("div", { class: "canvas-wrap" }, cvMap, ovMap)),
      el("div", {}, el("div", { class: "canvas-wrap" }, cvStat, ovStat))));
  const outBox = el("div", {}), partBox = el("div", { class: "kv" }), clickBox = el("div", { class: "events" });
  const rightPanels = [panel(t("Outcomes"), outBox), panel(t("Particle and wave"), partBox), panel(t("Latest clicks"), clickBox, { closed: true })];
  for (const cv of [cvWave, cvMap, cvStat]) new ResizeObserver(() => ctx.requestRender()).observe(cv);
  window.addEventListener("themechange", () => ctx.requestRender());
  let mapCache = null;

  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }
  const segNow = () => segs[segs.length - 1];

  // --- the wave over the potential ---------------------------------------------------------------------------
  function drawWave(frame, blobs) {
    const g = setup(cvWave), W = cvWave.clientWidth, Hh = cvWave.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const s = segNow(); if (!s) return;
    const x = s.x, V = s.V, L = s.L, n = x.length;
    const left = 40, right = 10, top = 16, bot = Hh - 24;
    const X = (xx) => left + (W - left - right) * (xx + L) / (2 * L);
    // energy axis: from min(V, 0) to max(V, E) with margins
    let vmin = 0, vmax = s.osc ? 0 : s.energy;
    for (let i = 0; i < n; i += 4) { if (Math.abs(x[i]) < L - s.det) { vmin = Math.min(vmin, V[i]); vmax = Math.max(vmax, V[i]); } }
    if (s.osc) vmax = Math.max(vmax * 0.5, 1e-6);
    const span = Math.max(vmax - vmin, 1e-6);
    const e0 = vmin - 0.15 * span, e1 = vmax + 0.35 * span;
    const Y = (e) => bot - (bot - top) * (e - e0) / (e1 - e0);
    // detectors
    g.fillStyle = "rgba(120,140,170,0.18)";
    g.fillRect(X(-L), top, X(-L + s.det) - X(-L), bot - top);
    g.fillRect(X(L - s.det), top, X(L) - X(L - s.det), bot - top);
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    g.fillText(t("detector:"), X(-L) + 4, top + 34); g.fillText(t("reflection"), X(-L) + 4, top + 47);
    g.fillText(t("detector:"), X(L - s.det) + 4, top + 34); g.fillText(t("transmission"), X(L - s.det) + 4, top + 47);
    // |psi|^2, scaled to the band above the energy line
    const rho = blobs.rho;
    if (rho) {
      let rmax = s.rmax;
      const base = s.osc ? Y(e0 + 0.02 * span) : Y(s.energy), hgt = (base - top) * 0.9;
      const collapsed = frame.clicked && frame.interp === "copenhagen";
      g.beginPath(); g.moveTo(X(x[0]), base);
      const stp = Math.max(1, Math.floor(n / 1500));
      for (let i = 0; i < n; i += stp) g.lineTo(X(x[i]), base - hgt * Math.min(rho[i] / rmax, 1.2));
      g.lineTo(X(x[n - 1]), base); g.closePath();
      g.fillStyle = collapsed ? "rgba(28,109,208,0.10)" : "rgba(28,109,208,0.35)"; g.fill();
      g.strokeStyle = collapsed ? "rgba(28,109,208,0.3)" : css("--accent"); g.lineWidth = 1.2; g.stroke();
      if (collapsed) {  // the state after the click: localised in the detector that clicked
        const xd = frame.clicked === "right" ? L - s.det / 2 : -L + s.det / 2;
        g.fillStyle = "#e8590c"; g.fillRect(X(xd) - 3, base - hgt, 6, hgt);
        g.fillText(t("collapse: the particle is in this detector"), Math.min(X(xd) - 100, W - 230), base - hgt - 6);
      }
    }
    // potential
    g.strokeStyle = css("--ink"); g.lineWidth = 1.5; g.beginPath();
    for (let i = 0; i < n; i += 2) { const yy = Y(Math.max(Math.min(V[i], e1), e0)); if (i) g.lineTo(X(x[i]), yy); else g.moveTo(X(x[i]), yy); }
    g.stroke();
    if (!s.osc) {
      g.setLineDash([5, 4]); g.strokeStyle = "#e8590c"; g.beginPath(); g.moveTo(X(-L), Y(s.energy)); g.lineTo(X(L), Y(s.energy)); g.stroke(); g.setLineDash([]);
      g.fillStyle = "#e8590c"; g.fillText(t("E = {e:.3g} eV", { e: s.energy }), X(-L) + 4, Y(s.energy) - 4);
    }
    // the Bohm particle
    if (frame.x_bohm !== undefined) {
      g.fillStyle = "#c92a2a"; g.beginPath(); g.arc(X(frame.x_bohm), s.osc ? Y(e0 + 0.02 * span) : Y(s.energy), 5, 0, 2 * Math.PI); g.fill();
    }
    // Everett branches after the click
    if (frame.branches && frame.clicked) {
      const b = frame.branches;
      g.font = "12px system-ui";
      for (const side of ["left", "right"]) {
        const ours = frame.clicked === side;
        g.fillStyle = ours ? css("--ink") : css("--muted");
        const xx = side === "right" ? X(L - s.det) - 190 : X(-L + s.det) + 6;
        const what = side === "right" ? t("the particle is transmitted") : t("the particle is reflected");
        g.fillText(ours ? t("● our branch: {what}, weight {w:.3g}", { what, w: b[side] })
          : t("○ the other branch: {what}, weight {w:.3g}", { what, w: b[side] }), xx, top + 30);
      }
    }
    // axis
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    for (let xx = -Math.floor(L / 20) * 20; xx <= L; xx += 20) { g.fillRect(X(xx), bot, 1, 4); g.fillText(fmt(xx), X(xx) - 8, bot + 15); }
    g.fillText(t("x, nm"), W - 40, bot + 15);
    for (const e of [e0, 0, vmax]) { g.fillText(t("{e:.2g} eV", { e }), 2, Y(e) + 4); }
    const interp = { copenhagen: t("the Copenhagen interpretation"), bohm: t("Bohm's interpretation"), everett: t("Everett's interpretation") }[frame.interp] || "";
    ovWave.textContent = t("Wave of particle no. {n:d} ({interp}); t after emission {t}; absorbed: left {l:.3g}, right {r:.3g}; in the window {w:.3g}",
      { n: (frame.counts || {}).emitted || 0, interp, t: time(frame.t_local * 1e-15, 4), l: frame.PL_t, r: frame.PR_t, w: frame.norm_t });
  }

  // --- space-time map with Bohm trajectories ----------------------------------------------------------------
  function drawMap(frame) {
    const g = setup(cvMap), W = cvMap.clientWidth, Hh = cvMap.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const s = segNow(); if (!s || !s.map) return;
    const [nt, nx] = s.map_shape;
    const left = 36, top = 8, bot = Hh - 20, mw = W - left - 8, mh = bot - top;
    if (!mapCache || mapCache.seg !== s.seg) {
      const img = new ImageData(nx, nt);
      for (let i = 0; i < nt; i++) for (let j = 0; j < nx; j++) {
        const v = Math.sqrt(s.map[i * nx + j]);
        const c = Math.min(255, Math.round(v * 255));
        const o = 4 * ((nt - 1 - i) * nx + j);
        img.data[o] = LUT[3 * c]; img.data[o + 1] = LUT[3 * c + 1]; img.data[o + 2] = LUT[3 * c + 2]; img.data[o + 3] = 255;
      }
      const oc = document.createElement("canvas"); oc.width = nx; oc.height = nt; oc.getContext("2d").putImageData(img, 0, 0);
      mapCache = { seg: s.seg, oc };
    }
    g.imageSmoothingEnabled = true; g.drawImage(mapCache.oc, left, top, mw, mh);
    const tmax = s.t_map[s.t_map.length - 1];
    const X = (xx) => left + mw * (xx + s.L) / (2 * s.L), Y = (tw) => bot - mh * tw / tmax;
    if (s.has_bohm && s.traj) {
      const [mt, mb] = s.traj_shape;
      g.strokeStyle = "rgba(120,220,255,0.55)"; g.lineWidth = 0.8;
      for (let k = 0; k < mb; k++) {
        g.beginPath();
        for (let i = 0; i < mt; i++) { const xx = X(s.traj[i * mb + k]), yy = Y(s.t_map[i]); if (i) g.lineTo(xx, yy); else g.moveTo(xx, yy); }
        g.stroke();
      }
    }
    // now
    const tl = Math.min(frame.t_local, tmax);
    g.strokeStyle = "#fff"; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(left, Y(tl)); g.lineTo(left + mw, Y(tl)); g.stroke(); g.setLineDash([]);
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    g.fillText("t", 4, top + 10); g.fillText(t("{v:.3g} fs", { v: tmax }), 2, top + 22); g.fillText("0", 20, bot);
    ovMap.textContent = s.has_bohm ? t("|ψ(x, t)|² of one particle (√ for contrast), time upwards; light blue: the Bohm trajectories of the ensemble (starting points distributed as |ψ|²)")
      : t("|ψ(x, t)|² of one particle (√ for contrast), time upwards");
  }

  // --- statistics: outcomes and T(E) -----------------------------------------------------------------------
  function drawStat(frame) {
    const g = setup(cvStat), W = cvStat.clientWidth, Hh = cvStat.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const s = segNow(); if (!s) return;
    if (s.osc) { ovStat.textContent = t("Trap: no detectors; the levels and the period are in “Checks”."); return; }
    const c = frame.counts || {}, n = (c.left || 0) + (c.right || 0);
    const PR = s.PR / (s.PL + s.PR);
    // bars
    const bx = 16, bw = 46, top = 24, bot = Hh * 0.55;
    const bars = [[t("reflection"), c.left || 0, 1 - PR, "#1c7ed6"], [t("transmission"), c.right || 0, PR, "#e8590c"]];
    bars.forEach(([lab, k, p, col], i) => {
      const xx = bx + i * (bw + 24), fr = n ? k / n : 0;
      g.fillStyle = col; g.globalAlpha = 0.6; g.fillRect(xx, bot - (bot - top) * fr, bw, (bot - top) * fr); g.globalAlpha = 1;
      g.strokeStyle = css("--ink"); g.setLineDash([4, 3]); g.beginPath(); g.moveTo(xx - 4, bot - (bot - top) * p); g.lineTo(xx + bw + 4, bot - (bot - top) * p); g.stroke(); g.setLineDash([]);
      g.fillStyle = css("--muted"); g.font = "11px system-ui"; g.fillText(lab, xx - 2, bot + 13); g.fillText(fmt(k, "d"), xx + 2, bot - (bot - top) * fr - 4);
    });
    // T(E) and the packet's energy distribution
    if (s.T_k) {
      const x0 = bx + 2 * (bw + 24) + 20, x1 = W - 10, y0 = top, y1 = bot;
      const E = s.E_k, T = s.T_k, wk = s.w_k, m = E.length;
      const Emin = E[0], Emax = E[m - 1];
      const XE = (e) => x0 + (x1 - x0) * (e - Emin) / (Emax - Emin), YT = (tw) => y1 - (y1 - y0) * tw;
      let wmax = 0; for (const v of wk) wmax = Math.max(wmax, v);
      g.fillStyle = "rgba(134,142,150,0.25)"; g.beginPath(); g.moveTo(XE(E[0]), y1);
      for (let i = 0; i < m; i++) g.lineTo(XE(E[i]), y1 - (y1 - y0) * 0.9 * wk[i] / wmax);
      g.lineTo(XE(E[m - 1]), y1); g.fill();
      g.strokeStyle = "#e8590c"; g.lineWidth = 1.5; g.beginPath();
      for (let i = 0; i < m; i++) { if (i) g.lineTo(XE(E[i]), YT(T[i])); else g.moveTo(XE(E[i]), YT(T[i])); }
      g.stroke();
      g.strokeStyle = css("--line"); g.strokeRect(x0, y0, x1 - x0, y1 - y0);
      g.fillStyle = css("--muted"); g.fillText(t("{e:.3g} eV", { e: Emin }), x0, y1 + 13); g.fillText(t("{e:.3g} eV", { e: Emax }), x1 - 50, y1 + 13);
      g.fillText("T(E)", x0 + 4, y0 + 12);
    }
    ovStat.textContent = t("Outcomes (particles: {n:d}); bars: fractions, dashes: probability from the wave. Right: the exact T(E) (orange) and the packet's distribution in energy, per unit energy (grey).", { n });
  }

  function drawPanels(frame) {
    const s = segNow(); if (!s) return;
    const c = frame.counts || {}, n = (c.left || 0) + (c.right || 0);
    if (!s.osc) {
      const PR = s.PR / (s.PL + s.PR);
      const fr = n ? (c.right || 0) / n : 0;
      const sd = n ? Math.sqrt(PR * (1 - PR) / n) : 0;
      outBox.replaceChildren(el("div", { class: "kv" },
        el("span", {}, t("particles")), el("span", { class: "mono" }, fmt(c.emitted || 0, "d")),
        el("span", {}, t("transmitted / reflected")), el("span", { class: "mono" }, `${fmt(c.right || 0, "d")} / ${fmt(c.left || 0, "d")}`),
        el("span", {}, t("fraction transmitted")), el("span", { class: "mono" }, n ? `${num(fr, 4)} ± ${num(sd, 2)}` : "—"),
        el("span", {}, t("probability from the wave")), el("span", { class: "mono" }, num(PR, 6)),
        el("span", {}, t("exact T(E) over the spectrum")), el("span", { class: "mono" }, s.T_expected !== undefined ? num(s.T_expected, 6) : "—")),
        el("div", { class: "help" }, t("The interpretation changes only the picture of the outcome (a collapse, a trajectory, a branch); the probabilities are the same.")));
    } else outBox.replaceChildren(el("div", { class: "help" }, t("A trap without detectors: the packet oscillates with the period 2π/ω.")));
    const lam = 2 * Math.PI / Math.max(s.k0, 1e-12);
    partBox.replaceChildren(...[[t("particle"), t("electron")], [t("energy"), s.osc ? "—" : t("{v:.4g} eV", { v: s.energy })],
      [t("de Broglie wavelength"), s.osc ? "—" : t("{v:.4g} nm", { v: lam })], [t("packet width σ"), t("{v:.4g} nm", { v: s.sigma })],
      [t("window"), t("±{v:.3g} nm", { v: s.L })], [t("grid points"), s.n_grid ? fmt(s.n_grid, "d") : ""], [t("particle cycle"), time(s.cycle * 1e-15, 4)]]
      .flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]));
  }

  return {
    center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, t("What is on the screen")),
      el("p", {}, t("At the top: the wave of the current particle |ψ(x)|² (blue) over the potential (black line) and the energy level (orange dashes). At the edges: the detectors; they absorb the wave, and the run computes what probability each of them absorbed, and when.")),
      el("p", {}, t("The particle's outcome is shown in the chosen interpretation: Copenhagen, a click at a random moment and the wave's collapse into the detector; Bohm, a red point particle moving with the probability current; Everett, after the click both branches remain with their weights. The statistics of the outcomes are the same in all three, and this is checked.")),
      el("p", {}, t("Bottom left: the map |ψ(x, t)|² of one particle (time upwards) with Bohm trajectories; bottom right: the fractions of the outcomes compared with the probability from the wave, and the exact transmission coefficient T(E) over the packet's spectrum."))),
    reset() { H = null; segs = []; clicks = []; mapCache = null; },
    // key frames (player.js): segments only grow (a length); the clicks are capped, so they are copied
    snapshot() { return { segs: segs.length, clicks: clicks.slice() }; },
    restore(k) {
      segs.length = k.segs; clicks = k.clicks.slice(); mapCache = null;
      clickBox.replaceChildren(...clicks.slice(-30).reverse().map((c) => el("div", { class: "ev" }, el("span", { class: "t mono" }, time(c.t, 6)), c.text)));
    },
    onHeader(meta) { H = meta; },
    onMessage(meta, blobs) {
      if (meta.type === "segment") {
        let rmax = 0; const mp = blobs.map;
        const s = { ...meta, x: blobs.x, V: blobs.V, W: blobs.W, map: blobs.map, t_map: blobs.t_map, traj: blobs.traj,
                    T_k: blobs.T_k, E_k: blobs.E_k, w_k: blobs.w_k, n_grid: blobs.x ? blobs.x.length : 0 };
        s.rmax = 1.0 / (Math.sqrt(2 * Math.PI) * meta.sigma);  // the initial peak of |psi|^2
        segs.push(s); mapCache = null;
        if (mp) for (const v of mp) rmax = Math.max(rmax, v);
      } else if (meta.type === "event" && meta.kind === "click") {
        clicks.push(meta); if (clicks.length > 200) clicks.shift();
        clickBox.replaceChildren(...clicks.slice(-30).reverse().map((c) => el("div", { class: "ev" }, el("span", { class: "t mono" }, time(c.t, 6)), c.text)));
      }
    },
    render(frame, tw, blobs) {
      if (!segNow()) return;
      drawWave(frame, blobs || {});
      drawMap(frame);
      drawStat(frame);
      drawPanels(frame);
    },
  };
}
