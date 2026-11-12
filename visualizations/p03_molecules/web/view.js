// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// p03 view: the particles-and-molecules playground (plan P15.4). The 3-D environment (/static/js/env3d.js) with the
// atoms as spheres (positions from the run, 16-bit over the box; radius σ/2 of their species), the molecules' bonds as
// lines, the box's walls and the piston; the charts of the run's statistics: the velocity components scaled by
// √(kT/m) against the standard Gaussian (Maxwell–Boltzmann), the radial distribution function g(r), the density along
// y (the field's axis), and the time series of the temperature, the pressure, the energy per atom, the
// bond-orientational order with the mean-square displacement and the molecules' mode temperatures; the shared
// playground panels. Drawing only: every number is the run's.
import { el, fresh2d, num, panel } from "/static/js/ui.js";
import { t, fmt } from "/static/js/i18n.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createPlayground } from "/static/js/playground.js";

function hexRgb(h) { const s = h.replace("#", ""); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) / 255); }

function chart(canvas, series, { xlabel = "", ylabel = "", xr = null, yr = null } = {}) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2), W = canvas.clientWidth, Hh = canvas.clientHeight;
  if (!W || !Hh) return;
  canvas.width = Math.round(W * dpr); canvas.height = Math.round(Hh * dpr);
  const g = fresh2d(canvas.getContext("2d"), dpr);
  g.fillStyle = "#0b0e14"; g.fillRect(0, 0, W, Hh);
  const L = 38, R = 6, T = 6, B = 20, pw = W - L - R, ph = Hh - T - B;
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const s of series) for (let i = 0; i < s.x.length; i++) {
    if (!Number.isFinite(s.x[i]) || !Number.isFinite(s.y[i])) continue;
    x0 = Math.min(x0, s.x[i]); x1 = Math.max(x1, s.x[i]); y0 = Math.min(y0, s.y[i]); y1 = Math.max(y1, s.y[i]);
  }
  if (!Number.isFinite(x0)) { x0 = 0; x1 = 1; }  // no data: an empty frame
  if (!Number.isFinite(y0)) { y0 = 0; y1 = 1; }
  if (xr) [x0, x1] = xr;
  if (yr) [y0, y1] = yr;
  if (!(x1 > x0)) { x1 = x0 + 1; }
  if (!(y1 > y0)) { y1 = y0 + 1; }
  const X = (x) => L + (x - x0) / (x1 - x0) * pw, Y = (y) => T + ph - (y - y0) / (y1 - y0) * ph;
  for (const s of series) {
    g.strokeStyle = s.color; g.fillStyle = s.color; g.lineWidth = s.width || 1.4; g.setLineDash(s.dash || []);
    if (s.bars) {
      const bw = s.x.length > 1 ? (s.x[1] - s.x[0]) : 1;
      g.globalAlpha = 0.55;
      for (let i = 0; i < s.x.length; i++) g.fillRect(X(s.x[i] - bw / 2), Y(s.y[i]), Math.max(1, bw / (x1 - x0) * pw - 1), Y(y0) - Y(s.y[i]));
      g.globalAlpha = 1;
      continue;
    }
    g.beginPath(); let pen = false;
    for (let i = 0; i < s.x.length; i++) {
      if (!Number.isFinite(s.y[i])) { pen = false; continue; }
      if (pen) g.lineTo(X(s.x[i]), Y(s.y[i])); else { g.moveTo(X(s.x[i]), Y(s.y[i])); pen = true; }
    }
    g.stroke(); g.setLineDash([]);
  }
  g.strokeStyle = "#3a4350"; g.strokeRect(L, T, pw, ph);
  g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
  g.fillText(num(y1, 3), 2, T + 9); g.fillText(num(y0, 3), 2, T + ph);
  g.fillText(num(x0, 3), L, T + ph + 12); const xt = num(x1, 3); g.fillText(xt, L + pw - g.measureText(xt).width, T + ph + 12);
  if (xlabel) g.fillText(xlabel, L + pw / 2 - g.measureText(xlabel).width / 2, T + ph + 12);
  if (ylabel) g.fillText(ylabel, L + 4, T + 10);
}

export function createView(ctx) {
  // a 2-D world (the plane z = 0, y up) opens looking at its plane (review UX-3d A3)
  const env = createEnv3D(ctx, { scale: "lin", plane2d: (H) => (H.md && H.md.ndim === 2 ? 2 : null) });
  let H = null, stats = [], drawnStats = -1, shapesKey = "";
  const pg = createPlayground(ctx, { onSelect: () => env.scene.requestRender(), describeProbe });
  const cv = () => el("canvas", { style: { width: "100%", height: "150px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const cVel = cv(), cRdf = cv(), cRho = cv(), cT = cv(), cP = cv(), cE = cv(), cOrd = cv(), cMsd = cv(), cMode = cv();
  const pLabel = el("div", { class: "help" }, t("Pressure")), ordLabel = el("div", { class: "help" }, t("Bond-orientational order"));
  const modeBox = el("div", {}, el("div", { class: "help" }, t("Mode temperatures of the molecules, K: translational (orange), rotational (green), vibrational kinetic (blue), potential of the bonds (pink), of the angles (yellow); equal at equipartition")), cMode);
  const statBox = el("div", { class: "kv" });
  const charts = el("div", {},
    el("div", { class: "help" }, t("Velocity components divided by √(kT/m) of their substance (bars) against the normal distribution, the Maxwell distribution (line)")), cVel,
    el("div", { class: "help" }, t("Radial distribution function g(r): the structure of the matter (gas ≈ 1, liquid: damped peaks, crystal: sharp peaks)")), cRdf,
    el("div", { class: "help" }, t("Density ρσ^d along the height y (layers of about σ): liquid and vapour show two steps, a gas in a field a smooth decline")), cRho,
    el("div", { class: "help" }, t("Temperature, K")), cT, pLabel, cP,
    el("div", { class: "help" }, t("Energy per atom, kJ/mol")), cE,
    ordLabel, cOrd,
    el("div", { class: "help" }, t("Mean-square displacement of the atoms since the last change of the scene, nm² (grows linearly: the atoms diffuse, as in a liquid; nearly constant: they vibrate about their places, as in a crystal)")), cMsd,
    modeBox, statBox);

  function describeProbe(o, r) {
    return Object.entries(r).map(([k, v]) => [t(k), typeof v === "number" ? fmt(v, ".5g") : t(v)]);
  }

  function lastAt(tNow) {
    let lo = 0, hi = stats.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (stats[m].t <= tNow + 1e-30) { k = m; lo = m + 1; } else hi = m - 1; }
    return k;
  }
  function drawCharts(tNow) {
    const k = lastAt(tNow);
    if (k === drawnStats) return;
    drawnStats = k;
    if (k < 0) return;
    const s = stats[k];
    if (s.vh) {
      const n = s.vh.length, x = [], y = [], gx = [], gy = [];
      for (let i = 0; i < n; i++) { x.push(-4 + (i + 0.5) * 8 / n); y.push(s.vh[i]); }
      for (let i = 0; i <= 160; i++) { const z = -4 + 8 * i / 160; gx.push(z); gy.push(Math.exp(-z * z / 2) / Math.sqrt(2 * Math.PI)); }
      chart(cVel, [{ x, y, color: "#74c0fc", bars: true }, { x: gx, y: gy, color: "#ffd43b", width: 2 }], { xlabel: "v / √(kT/m)", yr: [0, 0.5] });  // symbols only
    } else chart(cVel, [], { xlabel: "v / √(kT/m)" });  // every chart drawn at every cursor: a key frame and a rebuild agree
    if (s.rdf_r) chart(cRdf, [{ x: Array.from(s.rdf_r), y: Array.from(s.rdf_g), color: "#8ce99a" }, { x: [s.rdf_r[0], s.rdf_r[s.rdf_r.length - 1]], y: [1, 1], color: "#3d4450" /* solid: a dashed line was drawn differently after a key frame than after a rebuild (B7 browser check) */ }], { xlabel: t("r, nm") });
    else chart(cRdf, [], { xlabel: t("r, nm") });
    if (s.rho_y && s.rho_y.length) {
      const nb = s.rho_y.length, y = [], r = [];
      for (let i = 0; i < nb; i++) { y.push((i + 0.5) * s.rho_y_nm / nb); r.push(s.rho_y[i]); }
      chart(cRho, [{ x: y, y: r, color: "#74c0fc" }], { xlabel: t("y, nm") });
    } else chart(cRho, [], { xlabel: t("y, nm") });
    const ts = stats.slice(0, k + 1), tt = ts.map((q) => q.t * 1e12);
    chart(cT, [{ x: tt, y: ts.map((q) => q.T_K), color: "#ff922b" }], { xlabel: t("t, ps") });
    pLabel.textContent = t("Pressure: {kind}", { kind: s.p_kind ? t(s.p_kind) : t("virial") });
    chart(cP, [{ x: tt, y: ts.map((q) => q.p), color: "#b197fc" }], { xlabel: t("t, ps ({unit})", { unit: t(s.p_unit) }) });
    chart(cE, [{ x: tt, y: ts.map((q) => q.e), color: "#e9ecef" }], { xlabel: t("t, ps") });
    ordLabel.textContent = t("Bond-orientational order {kind} (neighbours closer than {rc}σ): 1 (ψ6) or {q6} (Q6 of fcc) for a crystal, ~1/√N for a liquid or a gas", { kind: s.order_kind || "", rc: 1.5, q6: 0.575 });
    chart(cOrd, [{ x: tt, y: ts.map((q) => (q.order === null || q.order === undefined) ? NaN : q.order), color: "#ffd43b" }], { xlabel: t("t, ps"), yr: [0, 1] });
    chart(cMsd, [{ x: tt, y: ts.map((q) => (q.msd === null || q.msd === undefined) ? NaN : q.msd), color: "#f783ac" }], { xlabel: t("t, ps (nm²)") });
    const md = ts.filter((q) => q.modes);
    modeBox.style.display = md.length ? "" : "none";
    if (md.length) {
      const mt = md.map((q) => q.t * 1e12), col = { translation: "#ff922b", rotation: "#8ce99a", vibration: "#74c0fc", bonds: "#f783ac", angles: "#ffd43b" };
      chart(cMode, Object.keys(col).filter((p) => md.some((q) => q.modes[p] !== null && q.modes[p] !== undefined)).map((p) => ({ x: mt, y: md.map((q) => (q.modes[p] === null || q.modes[p] === undefined) ? NaN : q.modes[p]), color: col[p] })), { xlabel: t("t, ps") });
    }
    statBox.replaceChildren(
      el("div", {}, el("span", {}, t("temperature")), el("b", {}, s.T_K === null ? "—" : t("{v:.4g} K", { v: s.T_K }))),
      el("div", {}, el("span", {}, t("pressure")), el("b", {}, s.p === null ? "—" : t("{v:.4g} {unit}", { v: s.p, unit: t(s.p_unit) }))),
      el("div", {}, el("span", {}, t("energy per atom")), el("b", {}, t("{v:.4g} kJ/mol", { v: s.e }))),
      el("div", {}, el("span", {}, t("KS to Maxwell")), el("b", {}, s.ks && s.ks.D !== null && s.ks.D !== undefined ? t("{d:.3g} (bound {b:.3g})", { d: s.ks.D, b: s.ks.bound }) : "—")),
      el("div", {}, el("span", {}, t("order {kind}", { kind: s.order_kind || "" })), el("b", {}, s.order === null || s.order === undefined ? "—" : fmt(s.order, ".3g"))),
      el("div", {}, el("span", {}, t("mean-square displacement")), el("b", {}, s.msd === null || s.msd === undefined ? "—" : t("{v:.3g} nm²", { v: s.msd }))));
  }

  function drawBox() {
    if (!H) return;
    const key = JSON.stringify(H.md.box_nm);
    if (key === shapesKey) return;
    shapesKey = key;
  }

  return {
    center: env.center,
    leftPanels: pg.leftPanels,
    rightPanels: [panel(t("Statistics"), charts), ...pg.rightPanels, panel(t("Scene layers"), env.layersPanel)],
    help: () => el("div", {},
      el("h4", {}, t("Playground: particles and molecules")),
      el("p", {}, t("Add a gas, a crystal, single atoms and molecules, change the walls (specular, soft, thermal: heat baths), put a piston, thermostats, a field and thermometers, all at the current moment. The atoms move by Newton's laws with a model interaction (Lennard-Jones, repulsion only, or hard spheres).")),
      el("p", {}, t("“Statistics”: the velocity distribution against the Maxwell distribution, the radial distribution function g(r), the density along the height, the temperature, the pressure and the energy over time, the orientational order (ψ6 / Q6) and the mean-square displacement (crystal or liquid), the molecules' mode temperatures. Checks: the energy balance (the first law: the baths' heat and the piston's work), the momentum (its change since the last edit against the rounding bound), the distance to the Maxwell distribution, for hard disks the compressibility factor against the equation of state."))),
    reset() { env.reset(); pg.reset(); H = null; stats = []; drawnStats = -1; shapesKey = ""; },
    snapshot() { return { env: env.snapshot(), pg: pg.snapshot(), ns: stats.length }; },
    restore(k) { env.restore(k.env); pg.restore(k.pg); stats.length = k.ns; drawnStats = -1; },
    onHeader(meta) { H = meta; env.onHeader(meta); pg.onHeader(meta); drawBox(); ctx.setScene && ctx.setScene(meta.title); },
    onMessage(meta, blobs) {
      if (pg.onMessage(meta, blobs)) return;
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "stats") stats.push({ t: meta.t, T_K: meta.T_K, p: meta.p, p_unit: meta.p_unit, p_kind: meta.p_kind, e: meta.e_kJ_mol, ks: meta.ks, rdf_r: blobs.rdf_r, rdf_g: blobs.rdf_g, vh: blobs.vh, rho_y: blobs.rho_y, rho_y_nm: meta.rho_y_nm, order: meta.order, order_kind: meta.order_kind, msd: meta.msd_nm2, modes: meta.modes });
    },
    render(frame, tNow, blobs) {
      if (!H || !frame) return;
      const n = frame.n || 0, d = H.md.ndim, box = frame.box_nm, q = blobs.q || new Uint16Array(0), sp = blobs.sp || new Uint8Array(0);
      const pos = new Float32Array(3 * n), rad = new Float32Array(n), rgb = new Float32Array(3 * n);
      const cols = (frame.species_colors || []).map(hexRgb), radii = frame.species_radius_nm || [];
      for (let i = 0; i < n; i++) {
        for (let a = 0; a < d; a++) pos[3 * i + a] = q[d * i + a] / 65535 * box[a];
        const s = sp[i] || 0, c = cols[s] || [0.6, 0.8, 1];
        rad[i] = radii[s] || 0.17; rgb[3 * i] = c[0]; rgb[3 * i + 1] = c[1]; rgb[3 * i + 2] = c[2];
      }
      env.scene.setSpheres("atoms", pos, rad, rgb, { label: t("Atoms"), minFrac: 0.0 });
      if (blobs.bonds && blobs.bonds.length) {
        const b = blobs.bonds, P = [], C = [];
        for (let k = 0; k + 1 < b.length; k += 2) {
          const i = b[k], j = b[k + 1];
          let far = false;
          for (let a = 0; a < d; a++) if (Math.abs(pos[3 * i + a] - pos[3 * j + a]) > 0.5 * box[a]) far = true;  // across a periodic face
          if (far) continue;
          P.push(pos[3 * i], pos[3 * i + 1], pos[3 * i + 2], pos[3 * j], pos[3 * j + 1], pos[3 * j + 2], NaN, NaN, NaN);
          C.push(0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0, 0, 0);
        }
        env.scene.setLines("bonds", new Float32Array(P), new Float32Array(C), { label: t("Bonds of the molecules") });
      }
      if (frame.piston_nm !== null && frame.piston_nm !== undefined) {  // the piston's face: a frame across its axis
        const a = frame.piston_axis || 1, o = [0, 1, 2].filter((k) => k !== a && k < Math.max(d, 2)), P = [];
        const corner = (u, v) => { const p = [0, 0, 0]; p[a] = frame.piston_nm; if (o[0] !== undefined) p[o[0]] = u; if (o[1] !== undefined) p[o[1]] = v; return p; };
        const U0 = box[o[0]] || 0, V0 = d === 3 ? (box[o[1]] || 0) : 0;
        const cs = [corner(0, 0), corner(U0, 0), corner(U0, V0), corner(0, V0), corner(0, 0)];
        for (const c of cs) P.push(...c);
        P.push(NaN, NaN, NaN);
        env.scene.setLines("piston", new Float32Array(P), new Float32Array(P.map(() => 0.85)), { label: t("Piston") });
      } else if (env.scene.removeLayer) env.scene.removeLayer("piston");  // a removed piston leaves no frame behind
      // the walled faces (an axis made walled by a "Wall" or the piston at the current moment: review UX-ui U7)
      const walled = frame.walled || [];
      if (walled.length) {
        const P = [], C = [];
        for (const a of walled) {
          const o = [0, 1, 2].filter((k) => k !== a && k < Math.max(d, 2));
          const U0 = box[o[0]] || 0, V0 = d === 3 ? (box[o[1]] || 0) : 0;
          for (const at of [0, box[a]]) {
            const corner = (u, v) => { const p = [0, 0, 0]; p[a] = at; if (o[0] !== undefined) p[o[0]] = u; if (o[1] !== undefined) p[o[1]] = v; return p; };
            for (const c of (d === 3 ? [corner(0, 0), corner(U0, 0), corner(U0, V0), corner(0, V0), corner(0, 0)] : [corner(0, 0), corner(U0, 0)])) { P.push(...c); C.push(0.95, 0.85, 0.55); }
            P.push(NaN, NaN, NaN); C.push(0, 0, 0);
          }
        }
        env.scene.setLines("walls", new Float32Array(P), new Float32Array(C), { label: t("Walls of the box") });
      } else if (env.scene.removeLayer) env.scene.removeLayer("walls");
      drawCharts(tNow);
      pg.render(frame, tNow);
      env.scene.requestRender();
    },
  };
}
