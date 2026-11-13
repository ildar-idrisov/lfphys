// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v06 view: the running coupling alpha_s(mu) computed by the run (1-4 loops, thresholds, the PDG band), the probe
// sweeping the scales, and quarkonium in the Cornell model (levels against PDG, the potential and the radial waves).
import { t, fmt } from "/static/js/i18n.js";
import { css, el, fresh2d, num, panel } from "/static/js/ui.js";

export function createView(ctx) {
  let seg = null;
  const quick = el("div", { class: "toolbar quick", title: t("Changes apply at once") }, el("span", { class: "muted" }, t("Set-up:")),
    ctx.liveControl("mu", { label: t("μ, GeV") }), ctx.liveControl("loops", { label: t("loops") }),
    ctx.liveControl("system", { label: t("quarkonium") }), ctx.liveControl("kappa", { label: "κ" }), ctx.liveControl("a_conf", { label: t("a, GeV⁻¹") }));
  const cvRun = el("canvas"), cvSpec = el("canvas"), cvPot = el("canvas");
  const ovRun = el("div", { class: "overlay" }), ovSpec = el("div", { class: "overlay" }), ovPot = el("div", { class: "overlay" });
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick,
    el("div", { class: "split", style: { flex: 1 } },
      el("div", {}, el("div", { class: "canvas-wrap" }, cvRun, ovRun)),
      el("div", { style: { display: "flex", flexDirection: "column" } },
        el("div", { class: "canvas-wrap", style: { flex: 1.1 } }, cvSpec, ovSpec),
        el("div", { class: "canvas-wrap", style: { flex: 1, borderTop: "1px solid var(--line)" } }, cvPot, ovPot))));
  const runBox = el("div", { class: "kv" }), specBox = el("div", {});
  const rightPanels = [panel(t("Coupling constant"), runBox), panel(t("Quarkonium: levels"), specBox)];
  for (const cv of [cvRun, cvSpec, cvPot]) new ResizeObserver(() => ctx.requestRender()).observe(cv);

  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }

  function drawRun(frame) {
    const g = setup(cvRun), W = cvRun.clientWidth, H = cvRun.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, H);
    if (!seg) return;
    const left = 52, right = 14, top = 26, bot = H - 30;
    const lmin = 0, lmax = 4;  // log10 mu from 1 GeV to 10 TeV
    const amax = 0.5;
    const X = (mu) => left + (W - left - right) * (Math.log10(mu) - lmin) / (lmax - lmin);
    const Y = (a) => bot - (bot - top) * a / amax;  // not clamped: curves are clipped at the frame (review V6-6)
    // grid
    g.strokeStyle = css("--grid"); g.fillStyle = css("--muted"); g.font = "11px system-ui";
    const ticks = [t("{x} GeV", { x: 1 }), fmt(10, "d"), fmt(100, "d"), t("{x} TeV", { x: 1 }), t("{x} TeV", { x: 10 })];
    for (let e = 0; e <= 4; e++) {
      g.beginPath(); g.moveTo(X(10 ** e), top); g.lineTo(X(10 ** e), bot); g.stroke();
      // centred on its tick, kept inside the canvas (the last one, "10 TeV", sits at the right edge: browser review F13)
      const wl = g.measureText(ticks[e]).width;
      g.fillText(ticks[e], Math.max(2, Math.min(X(10 ** e) - wl / 2, W - 2 - wl)), bot + 15);
    }
    for (let a = 0; a <= amax + 1e-9; a += 0.1) { g.beginPath(); g.moveTo(left, Y(a)); g.lineTo(W - right, Y(a)); g.stroke(); g.fillText(num(a, 2), 8, Y(a) + 4); }
    // thresholds
    for (const [q, m] of Object.entries(seg.thresholds)) {
      g.strokeStyle = "rgba(134,142,150,0.7)"; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(X(m), top); g.lineTo(X(m), bot); g.stroke(); g.setLineDash([]);
      g.fillStyle = css("--muted"); g.fillText(`m_${q}`, X(m) + 3, top + 12);
    }
    // curves and the band are clipped at the frame; values above amax leave it (towards the Landau pole)
    g.save(); g.beginPath(); g.rect(left, top, W - left - right, bot - top); g.clip();
    // uncertainty band of alpha_s(M_Z)
    const mus = seg.mus, n = mus.length;
    g.fillStyle = "rgba(232,89,12,0.18)"; g.beginPath();
    const ok = (i) => Number.isFinite(seg.hi[i]) && Number.isFinite(seg.lo[i]);
    for (let i = 0; i < n; i++) if (ok(i)) g.lineTo(X(mus[i]), Y(seg.hi[i]));
    for (let i = n - 1; i >= 0; i--) if (ok(i)) g.lineTo(X(mus[i]), Y(seg.lo[i]));
    g.closePath(); g.fill();
    // loop orders
    const cols = { L1: "#adb5bd", L2: "#74c0fc", L3: "#4dabf7", L4: "#1c7ed6" };
    for (const L of ["L1", "L2", "L3", "L4"]) {
      const arr = seg[L]; if (!arr) continue;
      const sel = L === `L${seg.loops}`;
      g.strokeStyle = sel ? "#e8590c" : cols[L]; g.lineWidth = sel ? 2.4 : 1;
      g.beginPath(); let pen = false;
      for (let i = 0; i < n; i++) { if (!Number.isFinite(arr[i])) { pen = false; continue; } const y = Y(arr[i]); if (pen) g.lineTo(X(mus[i]), y); else { g.moveTo(X(mus[i]), y); pen = true; } }
      g.stroke();
    }
    g.restore(); g.lineWidth = 1;
    const off = (seg[`L${seg.loops}`] || []).some((v) => Number.isFinite(v) && v > amax);
    if (off) {  // inside the frame, right-aligned under the top edge: the legend line above the frame stays readable
      g.save(); g.fillStyle = "#e8590c"; g.textAlign = "right";
      g.fillText(t("↑ α_s > {a:.2g}: the curve leaves the scale (towards the Landau pole)", { a: amax }), W - right - 6, top + 26);
      g.restore();
    }
    // input point alpha_s(M_Z)
    const [a0, da] = seg.alpha_mz_pdg;
    g.strokeStyle = css("--ink"); g.fillStyle = css("--ink"); g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(X(seg.mz), Y(a0 - da)); g.lineTo(X(seg.mz), Y(a0 + da)); g.stroke();
    g.beginPath(); g.arc(X(seg.mz), Y(seg.alpha_mz), 3.5, 0, 2 * Math.PI); g.fill();
    g.fillText(`M_Z: α_s = ${num(seg.alpha_mz, 4)}`, X(seg.mz) + 6, Y(seg.alpha_mz) - 8);
    // the probe
    const mu = frame.mu, a = frame.alpha ?? NaN;
    if (Number.isFinite(a)) {
      const yp = Math.max(Y(a), top);
      g.fillStyle = "#c92a2a"; g.beginPath();
      if (a > amax) { g.moveTo(X(mu), top - 2); g.lineTo(X(mu) - 6, top + 9); g.lineTo(X(mu) + 6, top + 9); g.closePath(); }
      else g.arc(X(mu), yp, 6, 0, 2 * Math.PI);
      g.fill();
      const args = { mu, a, nf: frame.nf };
      g.fillText(a > amax ? t("μ = {mu:.3g} GeV: α_s = {a:.4g} (off the scale), n_f = {nf:d}", args) : t("μ = {mu:.3g} GeV: α_s = {a:.4g}, n_f = {nf:d}", args),
        Math.min(X(mu) + 8, W - 230), Math.max(yp - 10, top + 24));
    } else {
      g.fillStyle = "#c92a2a"; g.fillRect(X(mu) - 1, top, 2, bot - top);
      g.fillText(t("μ = {mu:.3g} GeV: below the Landau pole, α_s is undefined", { mu }), Math.min(X(mu) + 8, W - 260), top + 24);
    }
    // legend
    g.fillStyle = css("--muted");
    g.fillText(t("loops: 1 (grey), 2–4 (blue); the chosen one orange; the band: α_s(M_Z) ± {da}", { da: seg.alpha_mz_pdg[1] }), left, top - 8);
    ovRun.textContent = "";
  }

  function drawSpec() {
    const g = setup(cvSpec), W = cvSpec.clientWidth, H = cvSpec.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, H);
    if (!seg) return;
    const lv = seg.levels;
    let lo = Infinity, hi = -Infinity;
    for (const l of lv) { lo = Math.min(lo, l.model, l.measured ?? Infinity); hi = Math.max(hi, l.model, l.measured ?? -Infinity); }
    const top = 30, bot = H - 22, left = 60;
    const Y = (m) => bot - (bot - top) * (m - lo) / Math.max(hi - lo, 1);
    const colW = (W - left - 10) / 3;
    g.font = "11px system-ui";
    for (let L = 0; L < 3; L++) {
      const x0 = left + L * colW;
      g.fillStyle = css("--muted"); g.fillText(["S (L = 0)", "P (L = 1)", "D (L = 2)"][L], x0 + 8, top - 12);
      for (const l of lv.filter((q) => q.L === L)) {
        g.strokeStyle = "#1c7ed6"; g.lineWidth = 2; g.beginPath(); g.moveTo(x0 + 6, Y(l.model)); g.lineTo(x0 + colW * 0.45, Y(l.model)); g.stroke();
        g.fillStyle = "#1c7ed6"; g.fillText(`${l.n}${"SPD"[L]} ${num(l.model, 4)}`, x0 + 6, Y(l.model) - 3);
        if (l.measured) {
          g.strokeStyle = "#e8590c"; g.beginPath(); g.moveTo(x0 + colW * 0.5, Y(l.measured)); g.lineTo(x0 + colW * 0.92, Y(l.measured)); g.stroke();
          g.fillStyle = "#e8590c"; g.fillText(num(l.measured, 5), x0 + colW * 0.5, Y(l.measured) + 12);
        }
      }
    }
    g.fillStyle = css("--muted");
    for (const m of [lo, (lo + hi) / 2, hi]) g.fillText(t("{m:d} MeV", { m: Math.round(m) }), 2, Y(m) + 4);
    ovSpec.textContent = t("{system}: blue, the Cornell model (1S anchored to experiment, the model gives the splittings); orange, PDG 2024 (spin-averaged)",
      { system: seg.system === "charm" ? t("Charmonium") : t("Bottomonium") });
  }

  function drawPot() {
    const g = setup(cvPot), W = cvPot.clientWidth, H = cvPot.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, H);
    if (!seg || !seg.r) return;
    const r = seg.r, V = seg.V, n = r.length, rmax = 10;
    const left = 40, top = 20, bot = H - 24;
    const X = (x) => left + (W - left - 10) * x / rmax;
    const vmin = -1.0, vmax = 2.0;
    const Yv = (v) => bot - (bot - top) * (v - vmin) / (vmax - vmin);
    g.strokeStyle = css("--grid"); g.beginPath(); g.moveTo(left, Yv(0)); g.lineTo(W - 10, Yv(0)); g.stroke();
    g.strokeStyle = css("--ink"); g.lineWidth = 1.5; g.beginPath();
    let started = false;
    for (let i = 0; i < n; i++) { if (r[i] > rmax) break; const y = Yv(Math.max(V[i], vmin)); if (started) g.lineTo(X(r[i]), y); else { g.moveTo(X(r[i]), y); started = true; } }
    g.stroke();
    const cols = ["#1c7ed6", "#2b8a3e", "#ae3ec9"], labs = ["1S", "2S", "1P"];
    for (let k = 0; k < 3; k++) {
      let um = 0; for (let i = 0; i < n; i++) um = Math.max(um, seg.u[k * n + i] ** 2);
      g.strokeStyle = cols[k]; g.lineWidth = 1.2; g.beginPath();
      for (let i = 0; i < n; i++) { if (r[i] > rmax) break; const y = bot - (bot - top) * 0.45 * seg.u[k * n + i] ** 2 / um; if (i) g.lineTo(X(r[i]), y); else g.moveTo(X(r[i]), y); }
      g.stroke(); g.fillStyle = cols[k]; g.fillText(labs[k], W - 60 + k * 18, top + 10);
    }
    g.strokeStyle = "#e8590c"; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(X(seg.r_mean), top); g.lineTo(X(seg.r_mean), bot); g.stroke(); g.setLineDash([]);
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    for (let x = 0; x <= rmax; x += 2) g.fillText(`${x}`, X(x) - 3, bot + 14);
    g.fillText(t("r, GeV⁻¹ (1 GeV⁻¹ ≈ {fm} fm)", { fm: 0.197 }), W - 200, bot + 14);
    ovPot.textContent = t("V(r) = −κ/r + r/a² (κ = {k:.3g}, a = {a:.3g} GeV⁻¹) and |u(r)|² of the levels; dashed: ⟨r⟩ of 1S", { k: seg.kappa, a: seg.a_conf });
  }

  function drawPanels(frame) {
    if (!seg) return;
    runBox.replaceChildren(...[[t("probe μ"), t("{mu:.4g} GeV", { mu: frame.mu })], ["α_s(μ)", frame.alpha === null || frame.alpha === undefined ? t("— (below the Landau pole)") : num(frame.alpha, 5)], [t("active flavours n_f"), String(frame.nf)],
      [t("input α_s(M_Z)"), t("{a:.4g} (PDG 2024: {p} ± {dp})", { a: seg.alpha_mz, p: seg.alpha_mz_pdg[0], dp: seg.alpha_mz_pdg[1] })], [t("order of the β function"), t("loops: {l:d}", { l: seg.loops })],
      [t("⟨r⟩ of the 1S state"), t("{r:.3g} GeV⁻¹ = {fm:.3g} fm", { r: seg.r_mean, fm: seg.r_mean * 0.1973 })],
      [t("4/3·α_s(1/⟨r⟩) against κ"), seg.a_bs ? t("{a:.3g} against {k:.3g}", { a: 4 / 3 * seg.a_bs, k: seg.kappa }) : "—"]]
      .flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]));
    specBox.replaceChildren(el("table", { class: "runs" }, el("tr", {}, [t("level"), t("model, MeV"), t("PDG, MeV"), t("states")].map((h) => el("th", {}, h))),
      seg.levels.map((l) => el("tr", {}, el("td", {}, `${l.n}${"SPD"[l.L]}`), el("td", { class: "mono" }, num(l.model, 5)),
        el("td", { class: "mono" }, l.measured ? num(l.measured, 5) : "—"), el("td", { class: "muted" }, (l.states || []).join(", "))))));
  }

  return {
    center, rightPanels,
    help: () => el("div", {}, el("h4", {}, t("What is on the screen")),
      el("p", {}, t("On the left: α_s(μ) computed by the run from α_s(M_Z) (PDG 2024) by solving the renormalisation-group equation with the QCD β function at 1–4 loops; dashed: the heavy-quark thresholds (the number of flavours changes). The red dot is the probe: “Play” sweeps it over the scales. The shorter the distance (the larger μ), the weaker the coupling: asymptotic freedom.")),
      el("p", {}, t("On the right: quarkonium in the Cornell potential (a model outside the core of QCD, fitted parameters): the levels from the radial Schrödinger equation against the measured ones; below, the potential and the radial wave functions."))),
    reset() { seg = null; },
    // key frames (player.js): the latest segment is the whole state (it is replaced, never changed)
    snapshot() { return { seg }; },
    restore(k) { seg = k.seg; },
    onHeader() {},
    onMessage(meta, blobs) {
      if (meta.type === "segment") seg = { ...meta, ...blobs };
    },
    render(frame) { drawRun(frame); drawSpec(); drawPot(); drawPanels(frame); },
  };
}
