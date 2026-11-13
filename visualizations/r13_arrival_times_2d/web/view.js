// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v12 view: arrival times. v11's view draws the scene (the wave, the plate if any, the detecting plane, the Bohm
// trajectories, the window of the plane y = 0 and the pattern on the screen); next to it this view draws what the run
// computed for the time of arrival: the density of each rule against time (the flux, the Bohm ensemble's first
// arrivals, ABK, semiclassical, the absorbing boundary, Wlodarz, Marchewka-Schuss, the soft detector), the joint
// distribution of place and time J(x, t) with the Bohm hits over it, and the totals. Drawing only: every curve and
// number comes from the run; everything is shown up to the time shown (the player may be scrolled back).
import { el, fill, fresh2d, panel } from "/static/js/ui.js";
import { createView as createV11View } from "/viz/v11_double_slit_2d/view.js";
import { t, fmt, lang } from "/static/js/i18n.js";

const RULES = {
  flux: { label: t("quantum flux J(t)"), color: "#ffffff", dash: [], width: 1.6 },
  bohm: { label: t("Bohm particles: first arrivals"), color: "#4fd1c5", bars: true },
  bohm_law: { label: t("Bohm's law of first arrival (from the flux)"), color: "#4fd1c5", dash: [4, 3] },
  abk: { label: t("Aharonov–Bohm–Kijowski"), color: "#ffd23f", dash: [] },
  sc: { label: t("semiclassical"), color: "#b48cff", dash: [6, 4] },
  abr: { label: t("absorbing boundary"), color: "#7bd88f", dash: [] },
  wlodarz: { label: t("Wlodarz"), color: "#ff8a1f", dash: [] },
  ms: { label: t("Marchewka–Schuss"), color: "#ff5c7a", dash: [2, 3] },
  soft: { label: t("soft detector −iW₀"), color: "#5ab0ff", dash: [] },
};
const SERIES = ["flux", "bohm_law", "wlodarz", "ms", "soft"];  // sampled at the run's steps
// the curve's colour on a dark chip, as on the chart (white and yellow vanish on the light theme)
const swatch = (k) => el("span", { style: { display: "inline-block", background: "#0b0e14", color: RULES[k].color, borderRadius: "3px",
  padding: "0 4px", marginRight: "4px", fontFamily: "monospace" } }, RULES[k].bars ? "▮" : (RULES[k].dash && RULES[k].dash.length ? "╌" : "━"));
const CURVES = ["abk", "sc", "abr"];                            // computed from the initial state at the start

export function createView(ctx) {
  const base = createV11View(ctx);
  const chart = el("canvas", { style: { width: "100%", height: "240px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const joint = el("canvas", { style: { width: "100%", height: "260px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const legendBox = el("div", { class: "help" }), jointHelp = el("div", { class: "help" }), totalsBox = el("div", {}), infoBox = el("div", { class: "kv" });
  const ownPanels = [panel(t("Experiment: arrival time"), infoBox), panel(t("Distribution of the arrival time"), el("div", {}, chart, legendBox)),
                     panel(t("Place and time of arrival"), el("div", {}, joint, jointHelp)), panel(t("Totals by rule"), totalsBox)];
  const rightPanels = [...ownPanels, ...base.rightPanels];
  const hidden = new Set();
  let H = null, A = null, tu = 1, nowT = Infinity, S = null, refs = null, rows = [], hits = { x: [], t: [] }, result = null, key = "";
  let liveNow = null;  // the live values of the latest set-up message: the detectors' strengths are live (review UX-ui U12)

  function resetOwn() {
    H = null; A = null; tu = 1; nowT = Infinity; refs = null; rows = []; hits = { x: [], t: [] }; result = null; key = ""; liveNow = null;
    S = { tau: [] }; for (const k of SERIES) S[k] = [];
  }
  resetOwn();
  const pending = new Set();
  function later(name, fn) {
    if (pending.has(name)) return;
    pending.add(name);
    requestAnimationFrame(() => { pending.delete(name); fn(); });
  }
  const shownN = () => { let n = S.tau.length; while (n > 0 && S.tau[n - 1] * tu > nowT + 1e-30) n -= 1; return n; };
  const hitsN = () => { let n = hits.t.length; while (n > 0 && hits.t[n - 1] > nowT + 1e-30) n -= 1; return n; };
  const resultNow = () => (result && result.t <= nowT + 1e-30 ? result : null);

  function sizeCanvas(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, Hh = cv.clientHeight;
    if (!W || !Hh) return null;
    cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr);
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = "#0b0e14"; g.fillRect(0, 0, W, Hh);
    return { g, W, Hh };
  }

  // --- the densities of the rules against time (in units of the classical flight time t0) -----------------------------
  // the time axis: 2 t0 (a set-up scale) at first, growing with the run's time; at the end, the run's last sample. The
  // observation window's length is a consequence of the run and is shown only in the totals (review B4-5)
  const tauEnd = () => {
    const r = resultNow();
    if (r && S.tau.length) return S.tau[S.tau.length - 1];
    return Math.max(2 * A.t0_units, 1.1 * Math.min(nowT / tu, S.tau.length ? S.tau[S.tau.length - 1] : 0));
  };
  function drawChart() {
    if (!A) return;
    const c = sizeCanvas(chart); if (!c) return;
    const { g, W, Hh } = c, t0 = A.t0_units, tmax = tauEnd() / t0;
    const left = 36, right = 6, top = 8, bot = 22, pw = W - left - right, ph = Hh - top - bot;
    const n = shownN(), tauNow = Math.min(nowT / tu, tauEnd());
    const lines = [];
    for (const k of SERIES) {
      if (!A.rules.includes(k) || hidden.has(k) || !S[k].length) continue;
      const pts = []; for (let i = 0; i < n; i++) pts.push([S.tau[i] / t0, S[k][i] * t0]);
      lines.push([k, pts]);
    }
    if (refs) for (const k of CURVES) {
      if (hidden.has(k)) continue;
      const pts = []; for (let i = 0; i < refs.tau.length && refs.tau[i] <= tauNow; i++) pts.push([refs.tau[i] / t0, refs[k][i] * t0]);
      lines.push([k, pts]);
    }
    // the Bohm ensemble's first arrivals: a histogram normalised to the whole ensemble (area = fraction arrived)
    const nb = 60, bw = tmax / nb, cnt = new Float32Array(nb), N = hitsN(), Ntot = H ? H.n_bohm : 1;
    for (let i = 0; i < N; i++) { const b = Math.floor(hits.t[i] / tu / t0 / bw); if (b >= 0 && b < nb) cnt[b] += 1; }
    // the scale: every curve shown, but at most 4 times the flux's and the ensemble's peak (a narrow semiclassical
    // peak would flatten the rest; what rises above is cut at the frame, marked ▲; hide it to see it whole)
    let ymax = 0, ymin = 0, ref = 0;
    for (const [k, pts] of lines) for (const [, v] of pts) { ymax = Math.max(ymax, v); ymin = Math.min(ymin, v); if (k === "flux" || k === "bohm_law") ref = Math.max(ref, v); }
    for (let b = 0; b < nb; b++) { const h = cnt[b] / Ntot / bw; if (!hidden.has("bohm")) ymax = Math.max(ymax, h); ref = Math.max(ref, h); }
    const cut = ref > 0 && ymax > 4 * ref;
    if (cut) ymax = 4 * ref;
    ymax = ymax || 1; ymin = Math.min(ymin, 0);
    const X = (tq) => left + tq / tmax * pw, Y = (v) => top + (ymax - v) / (ymax - ymin) * ph;
    if (!hidden.has("bohm")) {
      g.fillStyle = RULES.bohm.color; g.globalAlpha = 0.35;
      for (let b = 0; b < nb; b++) { const h = cnt[b] / Ntot / bw; if (h) g.fillRect(X(b * bw), Y(h), Math.max(1, pw / nb - 0.5), Y(0) - Y(h)); }
      g.globalAlpha = 1;
    }
    g.strokeStyle = "#3a4350"; g.lineWidth = 1;
    if (ymin < 0) { g.beginPath(); g.moveTo(left, Y(0)); g.lineTo(left + pw, Y(0)); g.stroke(); }
    g.save(); g.beginPath(); g.rect(left, top, pw, ph); g.clip();
    for (const [k, pts] of lines) {
      if (pts.length < 2) continue;
      const R = RULES[k];
      g.strokeStyle = R.color; g.lineWidth = R.width || 1.2; g.setLineDash(R.dash || []);
      g.beginPath(); pts.forEach(([tq, v], i) => (i ? g.lineTo(X(tq), Y(v)) : g.moveTo(X(tq), Y(v)))); g.stroke();
      if (cut) { let m = -1, vm = ymax; pts.forEach(([, v], i) => { if (v > vm) { vm = v; m = i; } }); if (m >= 0) { g.fillStyle = R.color; g.fillText("▲", X(pts[m][0]) - 4, top + 10); } }
    }
    g.restore(); g.setLineDash([]);
    if (!resultNow() && tauNow < tauEnd()) { g.strokeStyle = "rgba(255,255,255,0.25)"; g.beginPath(); g.moveTo(X(tauNow / t0), top); g.lineTo(X(tauNow / t0), top + ph); g.stroke(); }
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    for (let q = 0; q <= 4; q++) { const tq = tmax * q / 4; g.fillText(fmt(tq, ".3g"), X(tq) - 8, top + ph + 12); }
    g.fillText("t / t₀", left + pw - 30, top + ph + 21);
    g.fillText(fmt(ymax, ".2g"), 2, top + 8); g.fillText(fmt(ymin, ".2g"), 2, top + ph);
  }
  function drawLegend() {
    if (!A) { fill(legendBox); return; }
    const items = ["flux", "bohm", ...A.rules.filter((k) => k !== "flux" && k !== "bohm")];
    fill(legendBox,
      el("div", {}, t("The density Π(t)·t₀ against t/t₀; t₀ is the flight time at the mean speed. A click on a rule hides it.")),
      ...items.map((k) => el("label", { style: { display: "inline-block", marginRight: "10px", cursor: "pointer", opacity: hidden.has(k) ? 0.45 : 1 } },
        el("input", { type: "checkbox", checked: !hidden.has(k), onchange: (e) => { if (e.target.checked) hidden.delete(k); else hidden.add(k); drawLegend(); later("chart", drawChart); } }),
        swatch(k), RULES[k].label)));
  }

  // --- the joint distribution J(x, t) with the Bohm hits over it ------------------------------------------------------
  function drawJoint() {
    if (!A) return;
    const c = sizeCanvas(joint); if (!c) return;
    const { g, W, Hh } = c, R = A.rows, t0 = A.t0_units, tmax = tauEnd() / t0;
    const left = 36, right = 6, top = 8, bot = 22, pw = W - left - right, ph = Hh - top - bot;
    const x0 = R.x0 - 0.5 * R.dx, x1 = R.x0 + (R.n - 0.5) * R.dx;
    const X = (x) => left + (x - x0) / (x1 - x0) * pw, Y = (tq) => top + tq / tmax * ph;
    let nr = rows.length; while (nr > 0 && nr * R.tbin_units * tu > nowT * (1 + 1e-12)) nr -= 1;  // whole bins in the past (B4-8)
    let pk = 0; for (let i = 0; i < nr; i++) for (const v of rows[i]) pk = Math.max(pk, Math.abs(v));
    if (nr && pk > 0) {
      const img = g.createImageData(R.n, nr);
      for (let i = 0; i < nr; i++) for (let j = 0; j < R.n; j++) {
        const v = rows[i][j] / pk, a = Math.sqrt(Math.abs(v)), o = 4 * (i * R.n + j);
        if (v >= 0) { img.data[o] = 255 * Math.min(1, 1.6 * a); img.data[o + 1] = 255 * a * a; img.data[o + 2] = 60 * a; }
        else { img.data[o] = 40 * a; img.data[o + 1] = 120 * a; img.data[o + 2] = 255 * Math.min(1, 1.6 * a); }
        img.data[o + 3] = 255;
      }
      const off = document.createElement("canvas"); off.width = R.n; off.height = nr; off.getContext("2d").putImageData(img, 0, 0);
      g.imageSmoothingEnabled = false;
      g.drawImage(off, left, top, pw, nr * R.tbin_units / t0 / tmax * ph);
    }
    g.fillStyle = "#e8f8f5";
    const N = hitsN();
    for (let i = 0; i < N; i++) { const px = X(hits.x[i]), py = Y(hits.t[i] / tu / t0); if (px >= left && px <= left + pw) g.fillRect(px - 0.75, py - 0.75, 1.5, 1.5); }
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    for (let q = 0; q <= 4; q++) { let x = x0 + (x1 - x0) * q / 4; if (Math.abs(x) < 1e-9 * (x1 - x0)) x = 0; g.fillText(fmt(x, ".3g"), X(x) - 8, top + ph + 12); }
    g.fillText("x, λ", left + pw - 22, top + ph + 21);
    for (let q = 0; q <= 4; q++) { const tq = tmax * q / 4; g.fillText(fmt(tq, ".3g"), 2, Y(tq) + 4); }
    fill(jointHelp, t("The current into the detecting plane j_z(x, t) (computed: warm colours inwards, blue back; brightness √|j|), time t/t₀ from top to bottom; the dots are the hits of the Bohm particles (the place and the time of the first arrival). The integral over x gives the flux curve, over t the pattern on the screen."));
  }

  // --- totals and the experiment -------------------------------------------------------------------------------------
  function drawInfo() {
    if (!H || !A) { fill(infoBox); return; }
    const P = H.particle, sc = A.scene === "free", D = { ...A.params, ...(liveNow || {}) }, st = { gauss: t("one packet"), train: t("a train of {n:d} packets {sep:.3g} λ apart", { n: A.params.n_train, sep: A.params.sep }), backflow: t("a slow packet (k₀/4, amplitude {amp}) ahead and a fast one (k₀) behind; they meet at the plane", { amp: 1.5 }) }[A.state];
    fill(infoBox,
      el("span", {}, t("particle")), el("span", {}, t("{particle}, λ = {lam:.4g} pm", { particle: P.label, lam: P.lambda_m * 1e12 })),
      el("span", {}, t("flight")), el("span", {}, sc ? t("free, {D:.4g} λ from the first packet to the plane", { D: A.D }) : t("through two slits, {D:.4g} λ from the first packet to the screen", { D: A.D })),
      el("span", {}, t("state")), el("span", {}, t("{state}, σz = {s:.3g} λ", { state: st, s: H.geometry.sigma_z })),
      el("span", {}, t("t₀ (flight at the mean speed)")), el("span", { class: "mono" }, t("{u:.4g} units = {s:.3g} s", { u: A.t0_units, s: A.t0_units * P.time_unit_s })),
      el("span", {}, t("detectors now")), el("span", {}, [sc ? t("κ = {k:.3g} k₀", { k: D.kappa }) : null, t("λ₀: Wlodarz {w:.3g}, Marchewka–Schuss {m:.3g}", { w: D.mu_w, m: D.mu_ms }),
        A.rules.includes("soft") ? t("W₀ = {W:.3g} E₀", { W: D.W0 }) : null].filter(Boolean).join("; ")));
  }
  function drawTotals() {
    const r = resultNow();
    if (!r) { fill(totalsBox, el("div", { class: "muted" }, t("The totals appear at the end of the observation window."))); return; }
    const t0 = r.t0_units, rows_ = [];
    const cell = (x, right) => el("td", { style: { padding: "1px 4px", textAlign: right ? "right" : "left" }, class: right ? "mono" : "" }, x);
    rows_.push(el("tr", {}, cell(el("span", { class: "muted" }, t("rule"))), cell(el("span", { class: "muted" }, t("P in the window"))),
      cell(el("span", { class: "muted" }, "⟨t⟩ / t₀")), cell(el("span", { class: "muted" }, "σ_t / t₀"))));
    for (const k of ["flux", "bohm", ...A.rules.filter((q) => q !== "flux" && q !== "bohm")]) {
      const s = r.rules[k]; if (!s) continue;
      rows_.push(el("tr", {}, cell([swatch(k), RULES[k].label]), cell(fmt(s.total, ".4g"), true), cell(s.mean === null ? "—" : fmt(s.mean / t0, ".4g"), true),
        cell(s.sd === null || s.sd === undefined ? "—" : fmt(s.sd / t0, ".3g"), true)));
    }
    const extra = [];
    extra.push(el("div", { class: "help" }, t("P is the probability of arrival within the observation window ({w:.4g} t₀), ⟨t⟩ and σ_t the mean time and the spread. Backflow through the plane: {b:.3g} of the probability.", { w: r.tau_obs / t0, b: r.backflow })));
    extra.push(el("div", { class: "help" }, t("No click within the window: Wlodarz {w:.4g}, Marchewka–Schuss {m:.4g}.", { w: r.none.wlodarz, m: r.none.ms })));
    if (r.soft) extra.push(el("div", { class: "help" }, t("Soft detector: absorbed {a:.5g}, reflected {r:.4g}.", { a: r.soft.clicks, r: r.soft.reflected })));
    if (r.abk_neg !== undefined) extra.push(el("div", { class: "help" }, t("Aharonov–Bohm–Kijowski: the weight at t < 0 is {w:.3g} (read as «not detected»); the absorbing boundary absorbs {a:.5g} in all.", { w: r.abk_neg, a: r.abr_total })));
    fill(totalsBox, el("table", { style: { borderCollapse: "collapse", width: "100%", fontSize: "12px" } }, rows_), extra);
  }

  function redrawAll() { later("chart", drawChart); later("joint", drawJoint); later("totals", drawTotals); }  // once per batch

  return {
    center: base.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, t("Particle arrival time")),
      el("p", {}, t("A particle's packet flies to a detecting plane, freely or through two slits. The run solves the Schrödinger equation on the plane (x, z) and records on the detecting plane, at every moment, the current j_z, the wave ψ and its derivative ∂ψ/∂z.")),
      el("p", {}, t("Quantum mechanics gives no single rule for the arrival time (there is no time operator). The world computes several: the quantum flux; the first arrivals of the Bohm particles (their ensemble follows the trajectories of the same wave); Aharonov–Bohm–Kijowski and the semiclassical rule (from the momenta of the initial state, free flight only); the absorbing boundary ∂ψ/∂z = iκψ (Werner, Tumulka); the exponential rules of Wlodarz and of Marchewka–Schuss, where the rate of clicks is proportional to |ψ|² or |∂ψ|² on the plane; the soft detector, a second run of the same experiment with an absorbing potential −iW₀ behind the plane (it reflects a part of the wave).")),
      el("p", {}, t("Far from the source the rules almost agree. Near the source (a narrow packet, a small L) they diverge; for a train of packets the exponential rules damp the later peaks while the semiclassical one gives a single peak; under backflow the flux is negative in places while Bohm's first arrivals are not.")),
      el("p", {}, t("Through two slits the run gives the joint distribution of the place and the time of arrival j_z(x, t) (Das, Deckert, Kellers, Krekels, Struyve, 2024). A slit can be closed on the fly while the packet is on its way; the plate (a, d, w, V₀) can be changed.")),
      el("p", {}, t("The detectors change on the fly too: the strength λ₀ of the exponential rules and the height W₀ of the soft detector. Before the change a rule is computed with the old value, after it with the new one; if the signal has not arrived by then, the experiment is as with the new value from the very start. The absorbing boundary κ is a world parameter: its rule is computed from the initial state for one κ for the whole experiment.")),
      el("p", {}, t("Checks (on the right, “Checks”): in free flight, the flux and the wave on the plane against the exact solution, the arrival times of the Bohm particles against the law of first arrival, the soft detector's reflection against the stationary theory, the identity of the absorbing boundary; plus the checks of v11 (norm, grid and step, flux, equivariance, symmetry)."))),
    reset() { base.reset(); resetOwn(); drawInfo(); drawLegend(); redrawAll(); },
    // key frames (player.js): v11's part is its own key frame; the series, rows, references and hits only grow
    snapshot() {
      return { base: base.snapshot(), S: Object.fromEntries(Object.entries(S).map(([k, v]) => [k, v.length])),
               rows: rows.length, refs: refs ? refs.tau.length : -1, hits: hits.t.length, result };
    },
    restore(k) {
      base.restore(k.base);
      for (const [name, n] of Object.entries(k.S)) S[name].length = n;
      rows.length = k.rows; hits.x.length = k.hits; hits.t.length = k.hits; result = k.result;
      liveNow = k.base.setup ? k.base.setup.live : null; drawInfo();
      if (k.refs < 0) refs = null; else if (refs) for (const name of ["tau", "abk", "sc", "abr"]) refs[name].length = k.refs;
      key = ""; redrawAll();
    },
    onHeader(meta, blobs) {
      base.onHeader(meta, blobs);
      resetOwn(); H = meta; A = meta.arrival; tu = meta.particle.time_unit_s;
      const free = A.scene === "free";
      base.rightPanels[0].style.display = "none";            // v11's state of the experiment: replaced by this world's
      base.rightPanels[2].style.display = free ? "none" : ""; // the slits' live set-up: only with the plate
      drawInfo(); drawLegend(); redrawAll();
    },
    onMessage(meta, blobs) {
      base.onMessage(meta, blobs);
      switch (meta.type) {
        case "arrival":
          for (let i = 0; i < meta.n; i++) S.tau.push(blobs.tau[i]);
          for (const k of SERIES) {
            if (!meta.keys.includes(k)) continue;
            for (let i = 0; i < meta.n; i++) S[k].push(blobs[k][i]);
          }
          if (blobs.rows && A) for (let i = 0; i < meta.row_n; i++) rows.push(blobs.rows.subarray(i * A.rows.n, (i + 1) * A.rows.n));
          if (meta.ref_n) {  // the initial state's rules, revealed with the run's time
            refs = refs || { tau: [], abk: [], sc: [], abr: [] };
            for (const k of ["tau", "abk", "sc", "abr"]) for (let i = 0; i < meta.ref_n; i++) refs[k].push(blobs["ref_" + k][i]);
          }
          redrawAll();
          break;
        case "arrival_result": result = meta; redrawAll(); break;
        case "setup": liveNow = meta.live; drawInfo(); break;
        case "hits":
          if (blobs.t) for (let i = 0; i < meta.count; i++) { hits.x.push(blobs.x[i]); hits.t.push(blobs.t[i]); }
          redrawAll();
          break;
        default: break;
      }
    },
    render(meta, tShown, blobs) {
      base.render(meta, tShown, blobs);
      if (!H || !meta) return;
      nowT = tShown;
      const k = `${shownN()}|${hitsN()}|${resultNow() ? 1 : 0}|${rows.length}`;
      if (k !== key) { key = k; redrawAll(); }
    },
  };
}
