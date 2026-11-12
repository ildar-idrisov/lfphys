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
  const pLabel = el("div", { class: "help" }, "Давление"), ordLabel = el("div", { class: "help" }, "Ориентационный порядок связей");
  const modeBox = el("div", {}, el("div", { class: "help" }, "Температуры мод молекул, K: поступательная (оранжевая), вращательная (зелёная), колебательная кинетическая (голубая), потенциальная связей (розовая), углов (жёлтая) — при равнораспределении равны"), cMode);
  const statBox = el("div", { class: "kv" });
  const charts = el("div", {},
    el("div", { class: "help" }, "Компоненты скорости, делённые на √(kT/m) своего вещества (столбцы), против нормального распределения — распределения Максвелла (линия)"), cVel,
    el("div", { class: "help" }, "Радиальная функция распределения g(r): строение вещества (газ ≈ 1, жидкость — затухающие пики, кристалл — острые пики)"), cRdf,
    el("div", { class: "help" }, "Плотность ρσ^d по высоте y (слои около σ): жидкость и пар — две ступени, газ в поле — плавный спад"), cRho,
    el("div", { class: "help" }, "Температура, K"), cT, pLabel, cP,
    el("div", { class: "help" }, "Энергия на атом, кДж/моль"), cE,
    ordLabel, cOrd,
    el("div", { class: "help" }, "Средний квадрат смещения атомов с последнего изменения сцены, нм² (растёт линейно — атомы диффундируют, как в жидкости; почти постоянен — колеблются у мест, как в кристалле)"), cMsd,
    modeBox, statBox);

  function describeProbe(o, r) {
    return Object.entries(r).map(([k, v]) => [k, typeof v === "number" ? num(v, 5) : String(v)]);
  }

  function lastAt(t) {
    let lo = 0, hi = stats.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (stats[m].t <= t + 1e-30) { k = m; lo = m + 1; } else hi = m - 1; }
    return k;
  }
  function drawCharts(t) {
    const k = lastAt(t);
    if (k === drawnStats) return;
    drawnStats = k;
    if (k < 0) return;
    const s = stats[k];
    if (s.vh) {
      const n = s.vh.length, x = [], y = [], gx = [], gy = [];
      for (let i = 0; i < n; i++) { x.push(-4 + (i + 0.5) * 8 / n); y.push(s.vh[i]); }
      for (let i = 0; i <= 160; i++) { const z = -4 + 8 * i / 160; gx.push(z); gy.push(Math.exp(-z * z / 2) / Math.sqrt(2 * Math.PI)); }
      chart(cVel, [{ x, y, color: "#74c0fc", bars: true }, { x: gx, y: gy, color: "#ffd43b", width: 2 }], { xlabel: "v / √(kT/m)", yr: [0, 0.5] });
    } else chart(cVel, [], { xlabel: "v / √(kT/m)" });  // every chart drawn at every cursor: a key frame and a rebuild agree
    if (s.rdf_r) chart(cRdf, [{ x: Array.from(s.rdf_r), y: Array.from(s.rdf_g), color: "#8ce99a" }, { x: [s.rdf_r[0], s.rdf_r[s.rdf_r.length - 1]], y: [1, 1], color: "#3d4450" /* solid: a dashed line was drawn differently after a key frame than after a rebuild (B7 browser check) */ }], { xlabel: "r, нм" });
    else chart(cRdf, [], { xlabel: "r, нм" });
    if (s.rho_y && s.rho_y.length) {
      const nb = s.rho_y.length, y = [], r = [];
      for (let i = 0; i < nb; i++) { y.push((i + 0.5) * s.rho_y_nm / nb); r.push(s.rho_y[i]); }
      chart(cRho, [{ x: y, y: r, color: "#74c0fc" }], { xlabel: "y, нм" });
    } else chart(cRho, [], { xlabel: "y, нм" });
    const ts = stats.slice(0, k + 1), tt = ts.map((q) => q.t * 1e12);
    chart(cT, [{ x: tt, y: ts.map((q) => q.T_K), color: "#ff922b" }], { xlabel: "t, пс" });
    pLabel.textContent = `Давление: ${s.p_kind || "вириал"}`;
    chart(cP, [{ x: tt, y: ts.map((q) => q.p), color: "#b197fc" }], { xlabel: `t, пс (${s.p_unit})` });
    chart(cE, [{ x: tt, y: ts.map((q) => q.e), color: "#e9ecef" }], { xlabel: "t, пс" });
    ordLabel.textContent = `Ориентационный порядок связей ${s.order_kind || ""} (соседи ближе 1,5σ): 1 (ψ6) или 0,575 (Q6 у ГЦК) — кристалл, ~1/√N — жидкость или газ`;
    chart(cOrd, [{ x: tt, y: ts.map((q) => (q.order === null || q.order === undefined) ? NaN : q.order), color: "#ffd43b" }], { xlabel: "t, пс", yr: [0, 1] });
    chart(cMsd, [{ x: tt, y: ts.map((q) => (q.msd === null || q.msd === undefined) ? NaN : q.msd), color: "#f783ac" }], { xlabel: "t, пс (нм²)" });
    const md = ts.filter((q) => q.modes);
    modeBox.style.display = md.length ? "" : "none";
    if (md.length) {
      const mt = md.map((q) => q.t * 1e12), col = { translation: "#ff922b", rotation: "#8ce99a", vibration: "#74c0fc", bonds: "#f783ac", angles: "#ffd43b" };
      chart(cMode, Object.keys(col).filter((p) => md.some((q) => q.modes[p] !== null && q.modes[p] !== undefined)).map((p) => ({ x: mt, y: md.map((q) => (q.modes[p] === null || q.modes[p] === undefined) ? NaN : q.modes[p]), color: col[p] })), { xlabel: "t, пс" });
    }
    statBox.replaceChildren(
      el("div", {}, el("span", {}, "температура"), el("b", {}, s.T_K === null ? "—" : `${num(s.T_K, 4)} K`)),
      el("div", {}, el("span", {}, "давление"), el("b", {}, s.p === null ? "—" : `${num(s.p, 4)} ${s.p_unit}`)),
      el("div", {}, el("span", {}, "энергия на атом"), el("b", {}, `${num(s.e, 4)} кДж/моль`)),
      el("div", {}, el("span", {}, "КС до Максвелла"), el("b", {}, s.ks && s.ks.D !== null && s.ks.D !== undefined ? `${num(s.ks.D, 3)} (граница ${num(s.ks.bound, 3)})` : "—")),
      el("div", {}, el("span", {}, `порядок ${s.order_kind || ""}`), el("b", {}, s.order === null || s.order === undefined ? "—" : num(s.order, 3))),
      el("div", {}, el("span", {}, "ср. кв. смещение"), el("b", {}, s.msd === null || s.msd === undefined ? "—" : `${num(s.msd, 3)} нм²`)));
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
    rightPanels: [panel("Статистика", charts), ...pg.rightPanels, panel("Слои сцены", env.layersPanel)],
    help: () => el("div", {},
      el("h4", {}, "Плейграунд: частицы и молекулы"),
      el("p", {}, "Добавляйте газ, кристалл, отдельные атомы и молекулы, меняйте стенки (зеркальные, мягкие, тепловые — тепловые ванны), ставьте поршень, термостаты, поле и термометры — в текущий момент. Атомы движутся по законам Ньютона с модельным взаимодействием (Леннард-Джонс, только отталкивание или твёрдые шары)."),
      el("p", {}, "«Статистика»: распределение скоростей против распределения Максвелла, радиальная функция распределения g(r), плотность по высоте, температура, давление и энергия со временем, ориентационный порядок (ψ6 / Q6) и средний квадрат смещения (кристалл или жидкость), температуры мод молекул. Проверки: баланс энергии (первое начало: теплота ванн и работа поршня), импульс (изменение с последней правки против границы округления), расстояние до распределения Максвелла, у твёрдых дисков — фактор сжимаемости против уравнения состояния.")),
    reset() { env.reset(); pg.reset(); H = null; stats = []; drawnStats = -1; shapesKey = ""; },
    snapshot() { return { env: env.snapshot(), pg: pg.snapshot(), ns: stats.length }; },
    restore(k) { env.restore(k.env); pg.restore(k.pg); stats.length = k.ns; drawnStats = -1; },
    onHeader(meta) { H = meta; env.onHeader(meta); pg.onHeader(meta); drawBox(); ctx.setScene && ctx.setScene(meta.title); },
    onMessage(meta, blobs) {
      if (pg.onMessage(meta, blobs)) return;
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "stats") stats.push({ t: meta.t, T_K: meta.T_K, p: meta.p, p_unit: meta.p_unit, p_kind: meta.p_kind, e: meta.e_kJ_mol, ks: meta.ks, rdf_r: blobs.rdf_r, rdf_g: blobs.rdf_g, vh: blobs.vh, rho_y: blobs.rho_y, rho_y_nm: meta.rho_y_nm, order: meta.order, order_kind: meta.order_kind, msd: meta.msd_nm2, modes: meta.modes });
    },
    render(frame, t, blobs) {
      if (!H || !frame) return;
      const n = frame.n || 0, d = H.md.ndim, box = frame.box_nm, q = blobs.q || new Uint16Array(0), sp = blobs.sp || new Uint8Array(0);
      const pos = new Float32Array(3 * n), rad = new Float32Array(n), rgb = new Float32Array(3 * n);
      const cols = (frame.species_colors || []).map(hexRgb), radii = frame.species_radius_nm || [];
      for (let i = 0; i < n; i++) {
        for (let a = 0; a < d; a++) pos[3 * i + a] = q[d * i + a] / 65535 * box[a];
        const s = sp[i] || 0, c = cols[s] || [0.6, 0.8, 1];
        rad[i] = radii[s] || 0.17; rgb[3 * i] = c[0]; rgb[3 * i + 1] = c[1]; rgb[3 * i + 2] = c[2];
      }
      env.scene.setSpheres("atoms", pos, rad, rgb, { label: "Атомы", minFrac: 0.0 });
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
        env.scene.setLines("bonds", new Float32Array(P), new Float32Array(C), { label: "Связи молекул" });
      }
      if (frame.piston_nm !== null && frame.piston_nm !== undefined) {  // the piston's face: a frame across its axis
        const a = frame.piston_axis || 1, o = [0, 1, 2].filter((k) => k !== a && k < Math.max(d, 2)), P = [];
        const corner = (u, v) => { const p = [0, 0, 0]; p[a] = frame.piston_nm; if (o[0] !== undefined) p[o[0]] = u; if (o[1] !== undefined) p[o[1]] = v; return p; };
        const U0 = box[o[0]] || 0, V0 = d === 3 ? (box[o[1]] || 0) : 0;
        const cs = [corner(0, 0), corner(U0, 0), corner(U0, V0), corner(0, V0), corner(0, 0)];
        for (const c of cs) P.push(...c);
        P.push(NaN, NaN, NaN);
        env.scene.setLines("piston", new Float32Array(P), new Float32Array(P.map(() => 0.85)), { label: "Поршень" });
      } else if (env.scene.removeLayer) env.scene.removeLayer("piston");  // a removed piston leaves no frame behind
      // the walled faces (an axis made walled by a «Стенка» or the piston at the current moment: review UX-ui U7)
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
        env.scene.setLines("walls", new Float32Array(P), new Float32Array(C), { label: "Стенки ящика" });
      } else if (env.scene.removeLayer) env.scene.removeLayer("walls");
      drawCharts(t);
      pg.render(frame, t);
      env.scene.requestRender();
    },
  };
}
