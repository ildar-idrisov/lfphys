// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v11 view: the 2-D double slit in the shared 3-D environment (/static/js/env3d.js). The scene: the plate with its two
// long slits, the screen with the pattern accumulated so far, the wave |psi|^2 on the plane of the experiment (y = 0),
// the Bohm trajectories and the particles now; next to it the window of that plane (|psi|^2, amplitude, log or
// phase, with the trajectories over it); on the right the state of the experiment and the screen: the computed
// pattern, the Bohm hits by slit, and at the end the approximate theories for comparison. Drawing only: every number
// comes from the run (the view decodes the run's images and draws its polylines).
import { el, fill, fresh2d, num, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";

const COLORS = { 0: [0.78, 0.82, 0.86], 1: [0.31, 0.82, 0.77], 2: [1.0, 0.54, 0.12] };  // not yet through, A, B
const CSS = { 0: "#c8d0da", 1: "#4fd1c5", 2: "#ff8a1f" };
const FATE = { 1: "на экране", 2: "отражены пластиной", 3: "ушли вбок", 0: "в полёте" };

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "sqrt", logFloor: () => 1e-6 });
  env.windows.el.classList.add("wide");  // the plane's window is this world's main picture
  const stateBox = el("div", { class: "kv" }), setupBox = el("div", { class: "kv" }), resBox = el("div", {});
  const chart = el("canvas", { style: { width: "100%", height: "220px", display: "block", background: "#0b0e14", borderRadius: "4px" } });
  const chartHelp = el("div", { class: "help" });
  const legend = el("div", { class: "help" },
    el("span", { style: { color: CSS[1] } }, "━"), " через щель A (x < 0)  ", el("span", { style: { color: CSS[2] } }, "━"), " через щель B  ",
    el("span", { style: { color: CSS[0] } }, "━"), " ещё не прошли / отражены");
  const rightPanels = [panel("Опыт", el("div", {}, stateBox, legend)), panel("Экран", el("div", {}, chart, chartHelp, resBox)),
                       panel("Установка сейчас", setupBox), panel("Слои сцены", env.layersPanel)];
  let H = null, G = null, screens = [], result = null, hits = { x: [], slit: [], t: [] }, tracks = [], slits = null, fates = null, live = null;
  let chartKey = "";
  let waves = [], shownWave = -1, trackT = [], nowT = Infinity, lastSlits = "", lastPanels = 0, panelMeta = null, panelTimer = 0;
  let lastSetup = null;  // the latest set-up message (the plate and the observer as changed live)
  // the plate in force: the header's geometry with the latest set-up's plate (a, d, w, V₀ and the slits' centres are
  // live since review UX-ui U12; a set-up message of an older record carries none)
  const geometryOf = (setup) => (H ? { ...H.geometry, ...((setup && setup.geometry) || {}) } : null);
  // throttled redraws: many messages arrive per animation frame while the run computes fast
  const pending = new Set();
  function later(name, fn) {
    if (pending.has(name)) return;
    pending.add(name);
    requestAnimationFrame(() => { pending.delete(name); fn(); });
  }

  function reset() {
    H = null; G = null; screens = []; result = null; hits = { x: [], slit: [], t: [] }; tracks = []; slits = null; fates = null; chartKey = "";
    waves = []; shownWave = -1; trackT = []; nowT = Infinity; lastSlits = ""; lastPanels = 0; lastSetup = null;
    clearTimeout(panelTimer); panelMeta = null; panelTimer = 0;
  }

  // --- the window of the plane of the experiment (y = 0): |psi|^2 and phase from the run, trajectories over it -------
  function windowMeta(nx, nz, w) {
    const note = w ? `пик |ψ|² — ${num(w.peak_rel, 3)} от начального, в окне ${num(w.norm, 4)} вероятности (каждый снимок — в долях своего пика)` : "";
    return { type: "slice", id: 1, s: [G.x[0], G.x[1], nx], tt: [G.z[0], G.z[1], nz], origin: [0, 0, 0], u: [1, 0, 0], v: [0, 0, 1],
             normal: [0, 1, 0], units: "λ", coord_names: ["x", "y", "z"], depth: true, fixed: true, label: "плоскость опыта y = 0",
             title: "Плоскость опыта (y = 0): волна |ψ|²", route_label: "уравнение Шрёдингера на всей плоскости, без приближений",
             exact: true, approximation: false, verify: { note } };
  }
  function overlay(g, map) {
    // the plate (none in v12's free flight) and the screen's front
    g.strokeStyle = "rgba(200,208,218,0.7)"; g.lineWidth = 1;
    if (G.w > 0) {
      const [xa, za] = map(G.x[0], -G.w / 2), [xb, zb] = map(G.x[1], G.w / 2);
      g.strokeRect(Math.min(xa, xb), Math.min(za, zb), Math.abs(xb - xa), Math.abs(zb - za));
    }
    if (H && H.particle.spin && G.centers && G.centers.length > 1) {  // the which-path mark (spin field or detector) in slit B
      const th = live ? live.mark_deg : 0, [ma, mz0] = map(G.centers[1] - G.a / 2, -G.w / 2), [mb, mz1] = map(G.centers[1] + G.a / 2, G.w / 2);
      g.fillStyle = `rgba(255,138,31,${0.15 + 0.5 * Math.sin(th * Math.PI / 360) ** 2})`;
      g.fillRect(Math.min(ma, mb), Math.min(mz0, mz1), Math.abs(mb - ma), Math.abs(mz1 - mz0));
    }
    const [s0, z0] = map(-G.screen_half, G.zL), [s1] = map(G.screen_half, G.zL);
    g.beginPath(); g.moveTo(s0, z0); g.lineTo(s1, z0); g.stroke();
    // trajectories, up to the time shown (the player may be scrolled back)
    let upto = trackT.length;
    while (upto > 0 && trackT[upto - 1] > nowT) upto -= 1;
    g.lineWidth = 1;
    for (let k = 0; k < tracks.length; k++) {
      const T = tracks[k]; if (!T || T.length < 4) continue;
      g.strokeStyle = CSS[slits ? slits[k] : 0]; g.globalAlpha = 0.8;
      g.beginPath(); let pen = false;
      for (let i = 0; i < Math.min(T.length, 2 * upto); i += 2) {
        if (!Number.isFinite(T[i])) { pen = false; continue; }
        const [px, py] = map(T[i], T[i + 1]);
        if (pen) g.lineTo(px, py); else { g.moveTo(px, py); pen = true; }
      }
      g.stroke();
    }
    g.globalAlpha = 1;
  }

  // the wave's images arrive as accumulative messages; the one shown is the last at or before the time shown. They are
  // kept as the run sent them and decoded only when shown: a view rebuilt from the record is fed every image up to the
  // time shown, and only the last is drawn (review C1-13)
  function addWave(meta, blobs) {
    waves.push({ t: meta.t, nx: meta.shape[0], nz: meta.shape[1], amp: blobs.amp, ph: blobs.phase, peak_rel: meta.peak_rel,
                 norm: meta.norm, eta: blobs.eta || null, sigma_y: meta.sigma_y });
  }
  function decodeWave(w) {
    const { nx, nz, amp, ph } = w;
    const I = new Float32Array(nx * nz), Iw = new Float32Array(nx * nz), Pw = new Float32Array(nx * nz);
    for (let ix = 0; ix < nx; ix++) for (let iz = 0; iz < nz; iz++) {
      const a = amp[ix * nz + iz] / 65535, v = a * a;
      I[ix * nz + iz] = v;
      Iw[iz * nx + ix] = v;
      Pw[iz * nx + ix] = ph[ix * nz + iz] / 255 * 2 * Math.PI - Math.PI;
    }
    return { ...w, I, Iw, Pw };
  }
  // the wave in 3-D: |psi(x, z)|^2 |eta(y)|^2, the outer product of the run's image (reduced to <= VOL_MAX per axis)
  // and the run's y-profile |eta(y, t)|^2 (sampled across the scene's y extent) — drawing only. Records made before
  // the y-factor (no eta) draw no volume
  const VOL_MAX = 96;
  function waveVolume(w) {
    const ny = w.eta.length, s = Math.max(1, Math.ceil(Math.max(w.nx, w.nz) / VOL_MAX));
    const nx = Math.floor(w.nx / s), nz = Math.floor(w.nz / s), I2 = new Float32Array(nx * nz);
    let pk = 0;
    for (let ix = 0; ix < nx; ix++) for (let iz = 0; iz < nz; iz++) {
      let a = 0;
      for (let u = 0; u < s; u++) for (let v = 0; v < s; v++) a += w.I[(ix * s + u) * w.nz + iz * s + v];
      I2[ix * nz + iz] = a / (s * s); pk = Math.max(pk, a / (s * s));
    }
    const data = new Float32Array(nz * nx * ny), inv = pk > 0 ? 1 / pk : 0;
    for (let iz = 0; iz < nz; iz++) for (let ix = 0; ix < nx; ix++) {
      const v = I2[ix * nz + iz] * inv, o = (iz * nx + ix) * ny;
      for (let iy = 0; iy < ny; iy++) data[o + iy] = v * w.eta[iy];
    }
    return { dims: [nz, nx, ny], data };
  }
  function showWave(t) {
    let lo = 0, hi = waves.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (waves[m].t <= t + 1e-30) { k = m; lo = m + 1; } else hi = m - 1; }
    if (k < 0 || k === shownWave) return;
    shownWave = k;
    const w = decodeWave(waves[k]);
    env.scene.setPanelImage("wave", w.nx, w.nz, w.I);
    if (w.eta) {
      const V = waveVolume(w);
      if (!env.scene.updateVolume("wave3d", V.data)) env.scene.setVolume("wave3d", V.dims, V.data);
    }
    env.windows.setSlice(1, windowMeta(w.nx, w.nz, w), { I: w.Iw, phase: w.Pw });
    env.windows.setOverlay(1, overlay);
  }

  // --- the screen: the computed pattern, the Bohm hits by slit, at the end the approximate theories --------------------
  // everything as of the time shown: the player may be scrolled back (review B3-10)
  function screenAt(t) {
    let lo = 0, hi = screens.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (screens[m].t <= t + 1e-30) { k = m; lo = m + 1; } else hi = m - 1; }
    return k < 0 ? null : screens[k];
  }
  const resultNow = () => (result && result.t <= nowT + 1e-30 ? result : null);
  function hitsUpTo(t) { let n = hits.t.length; while (n > 0 && hits.t[n - 1] > t + 1e-30) n -= 1; return n; }
  function drawChart() {
    const screen = screenAt(nowT), result = resultNow();
    const cv = chart, dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, Hh = cv.clientHeight;
    if (!W || !Hh || !G) return;
    cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr);
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = "#0b0e14"; g.fillRect(0, 0, W, Hh);
    const left = 34, right = 6, top = 8, bot = 22, pw = W - left - right, ph = Hh - top - bot;
    const xh = G.screen_half, X = (x) => left + (x + xh) / (2 * xh) * pw;
    let P = null, ymax = 0;
    if (screen && !screen.empty) {
      const n = screen.n, x0 = screen.x0, dx = screen.dx, total = Math.max(screen.total, 1e-300);
      P = []; for (let i = 0; i < n; i++) { const x = x0 + i * dx; if (Math.abs(x) <= xh) { const v = screen.P[i] / (total * dx); P.push([x, v]); ymax = Math.max(ymax, v); } }
    }
    // hits: histogram stacked by slit, normalised to the same area as the pattern (probability density on the screen)
    const nb = 80, bw = 2 * xh / nb, cA = new Float32Array(nb), cB = new Float32Array(nb), c0 = new Float32Array(nb);
    const N = hitsUpTo(nowT);
    for (let i = 0; i < N; i++) {
      const b = Math.floor((hits.x[i] + xh) / bw); if (b < 0 || b >= nb) continue;
      (hits.slit[i] === 1 ? cA : hits.slit[i] === 2 ? cB : c0)[b] += 1;
    }
    const dens = (c) => c / Math.max(N, 1) / bw;
    for (let b = 0; b < nb; b++) ymax = Math.max(ymax, dens(cA[b] + cB[b] + c0[b]));
    const refs = (result && result.refs) || {};
    for (const k of ["paraxial", "kirchhoff"]) if (refs[k]) for (const v of refs[k]) ymax = Math.max(ymax, v);
    ymax = ymax || 1;
    const Y = (v) => top + ph - v / ymax * ph;
    for (let b = 0; b < nb; b++) {
      const x = -xh + b * bw;
      let y = 0;
      for (const [c, col] of [[cA, CSS[1]], [cB, CSS[2]], [c0, CSS[0]]]) {
        const h = dens(c[b]); if (!h) continue;
        g.fillStyle = col; g.globalAlpha = 0.55; g.fillRect(X(x), Y(y + h), Math.max(1, bw / (2 * xh) * pw - 0.5), Y(y) - Y(y + h)); y += h;
      }
    }
    g.globalAlpha = 1;
    if (P) { g.strokeStyle = "#ffffff"; g.lineWidth = 1.4; g.beginPath(); P.forEach(([x, v], i) => (i ? g.lineTo(X(x), Y(v)) : g.moveTo(X(x), Y(v)))); g.stroke(); }
    if (result && screen) {
      const xs = []; for (let i = 0; i < screen.n; i++) xs.push(screen.x0 + i * screen.dx);
      for (const [k, dash, col] of [["paraxial", [5, 4], "#ffd23f"], ["kirchhoff", [2, 3], "#b48cff"]]) {
        const R = refs[k]; if (!R) continue;
        g.setLineDash(dash); g.strokeStyle = col; g.lineWidth = 1.2; g.beginPath(); let pen = false;
        for (let i = 0; i < xs.length; i++) { if (Math.abs(xs[i]) > xh) continue; const p = [X(xs[i]), Y(R[i])]; if (pen) g.lineTo(...p); else { g.moveTo(...p); pen = true; } }
        g.stroke(); g.setLineDash([]);
      }
    }
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    for (let q = 0; q <= 4; q++) { const x = -xh + 2 * xh * q / 4; g.fillText(num(x, 3), X(x) - 8, top + ph + 12); }
    g.fillText("x, λ", left + pw - 22, top + ph + 21);
    g.fillText(num(ymax, 2), 2, top + 8); g.fillText("0", 2, top + ph);
    fill(chartHelp,
      el("span", {}, el("b", {}, "━"), " поток в экран (посчитан, копится) · столбцы — попадания частиц Бома по щелям"),
      result && (refs.paraxial || refs.kirchhoff) ? el("div", {}, el("span", { style: { color: "#ffd23f" } }, "╌"), " параксиальная теория (Френель, Кирхгоф) · ",
        el("span", { style: { color: "#b48cff" } }, "┄"), " граничные значения Кирхгофа, точное распространение — для сравнения, не эталон") : null);
  }

  function drawState(f) {
    if (!H) return;
    const P = H.particle, Gm = G;
    const c = f ? f.counts : null;
    fill(stateBox,
      el("span", {}, "частица"), el("span", {}, `${P.label}, λ = ${num(P.lambda_m * 1e12, 4)} пм, E = ${num(P.Ekin_eV, 4)} эВ`),
      el("span", {}, "щели"), el("span", { class: "mono" }, `a = ${num(Gm.a, 3)} λ, d = ${num(Gm.d, 3)} λ, стенка ${num(Gm.w, 3)} λ × ${num(Gm.V0, 3)} E₀, экран z = ${num(Gm.L, 4)} λ`),
      el("span", {}, "время волны"), el("span", { class: "mono" }, f ? `${num(f.tau, 4)} ед. (${num(f.tau * P.time_unit_s, 3)} с)` : "—"),
      el("span", {}, "вероятность в окне"), el("span", { class: "mono" }, f ? num(f.norm, 4) : "—"),
      el("span", {}, `частицы Бома (${H.n_bohm})`), el("span", { class: "mono" }, c ? Object.entries(FATE).map(([k, t]) => `${t}: ${c[{ 1: "screen", 2: "back", 3: "side", 0: "flight" }[k]]}`).join(" · ") : "—"),
      el("span", {}, "считается на"), el("span", {}, `${H.device.wave === "gpu" ? "GPU 0" : "CPU"} (${H.device.reason})`));
  }
  function drawSetup(live) {
    if (!H || !live) return;
    fill(setupBox,
      G && G.centers && G.centers.length ? el("span", {}, "пластина") : null,
      G && G.centers && G.centers.length ? el("span", { class: "mono" }, `a = ${num(G.a, 4)} λ, d = ${num(G.d, 4)} λ, w = ${num(G.w, 4)} λ, V₀ = ${num(G.V0, 4)} E₀`) : null,
      el("span", {}, "щель A"), el("span", {}, live.slit_a ? "открыта" : "закрыта"),
      el("span", {}, "щель B"), el("span", {}, live.slit_b ? "открыта" : "закрыта"),
      H.particle.spin ? el("span", {}, H.particle.mark === "detector" ? "наблюдатель у щели B" : "метка в щели B") : null,
      H.particle.spin ? el("span", {}, live.mark_deg ? `${H.particle.mark === "detector" ? "состояние детектора" : "спин"} поворачивается на ${num(live.mark_deg, 4)}° (различимость путей sin²(θ/2) = ${num(Math.sin(live.mark_deg * Math.PI / 360) ** 2, 3)})` : "θ = 0: путь не помечен") : null,
      H.particle.charge_e ? el("span", {}, "поток между щелями") : null, H.particle.charge_e ? el("span", {}, `${num(live.flux, 4)} Φ₀`) : null);
  }
  function drawPanels() {
    clearTimeout(panelTimer); panelTimer = 0;
    if (!panelMeta) return;
    lastPanels = performance.now();
    drawState(panelMeta);
    if (panelMeta.live) drawSetup(panelMeta.live);
  }
  function drawResult() {
    const result = resultNow();
    if (!result) { fill(resBox, el("div", { class: "muted" }, "Итог появится, когда волна уйдёт из окна: вся вероятность будет поглощена экраном, краями или отражена.")); return; }
    const F = result.fractions, B = result.bohm;
    fill(resBox, el("div", { class: "kv" },
      el("span", {}, "на экран"), el("span", { class: "mono" }, num(F.screen, 5)),
      el("span", {}, "отражено пластиной"), el("span", { class: "mono" }, num(F.back, 5)),
      el("span", {}, "ушло вбок"), el("span", { class: "mono" }, num(F.side, 5)),
      el("span", {}, "частиц Бома на экране"), el("span", { class: "mono" }, `${B.screen} из ${B.n}: через A ${B.A}, через B ${B.B}; пересекли ось ${B.crossed_axis}`)));
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, "Двухщелевой опыт в 2D"),
      el("p", {}, "Пакет частицы летит на пластину с двумя длинными щелями и дальше на экран. Прогон решает уравнение Шрёдингера на всей плоскости опыта (x, z) — без параксиального приближения и без граничных условий Кирхгофа: стенка — потенциальный барьер конечной высоты и толщины, волна сама отражается, проходит в щели и расходится на любые углы. Экран и края окна поглощают волну (детекторы)."),
      el("p", {}, "Картина на экране — вероятность, втекающая в экран, копится по мере прихода волны. Частицы Бома стартуют из точек, распределённых по |ψ|², и идут по току вероятности той же волны; цвет траектории — щель, через которую частица прошла. При симметричной установке траектории не пересекают ось; с меткой пути пересекают."),
      el("p", {}, "Установку можно менять на ходу (слева): закрыть щель, повернуть спин в щели B (метка пути: интерференция гаснет), включить поток Ааронова–Бома между щелями (полосы сдвигаются), изменить саму пластину — ширину щелей a, расстояние между ними d, толщину w и высоту стенки V₀ (в окне и с экраном этого мира). Изменение действует с этого момента: часть волны, уже прошедшая щели, его не чувствует; если волна была там, где стенка изменилась, событие называет, какая доля вероятности почувствовала изменение сразу."),
      el("p", {}, "Окно справа от сцены — плоскость опыта: интенсивность, амплитуда, логарифм или фаза; траектории поверх. Внизу справа — экран: посчитанная картина, попадания частиц и в конце — приближённые теории для сравнения."),
      el("p", {}, "Третье измерение. Вдоль щелей (ось y) установка не меняется, поэтому трёхмерная волна — точное произведение волны на плоскости (x, z), посчитанной прогоном, и свободного гауссова пакета η(y, t) ширины σy (он только расплывается). В 3D волна показана объёмом (слой «Волна |ψ|² в объёме»; плоскость y = 0 — отдельный слой), частицы Бома и их траектории — во всех трёх координатах (по y траектория растягивается вместе с η), экран — картиной P(x, y). Сверки: сумма P(x, y) по y равна картине P(x), попадания частиц по y — распределению потока по y.")),
    reset() { env.reset(); reset(); drawChart(); },
    // key frames (player.js): lists and track points only grow (lengths); the latest result, set-up, slits and live
    // values are references; the 3-D scene's part is the environment's own key frame
    snapshot() {
      return { env: env.snapshot(), screens: screens.length, hits: hits.t.length, trackT: trackT.length,
               tracks: tracks.map((T) => (T ? T.length : -1)), waves: waves.length, result, slits, fates, lastSlits,
               live, setup: lastSetup };
    },
    restore(k) {
      if (k.setup !== lastSetup && !k.setup) throw new Error("the set-up was changed after this key frame");
      env.restore(k.env);
      screens.length = k.screens; trackT.length = k.trackT; waves.length = k.waves; shownWave = -1;
      for (const a of ["x", "slit", "t"]) hits[a].length = k.hits;
      tracks.length = k.tracks.length;
      k.tracks.forEach((n, i) => { if (n < 0) delete tracks[i]; else tracks[i].length = n; });
      result = k.result; slits = k.slits; fates = k.fates; lastSlits = k.lastSlits;
      if (k.setup !== lastSetup) { env.scene.setObject(k.setup.plate); if (k.setup.observer) env.scene.setObject(k.setup.observer); }
      lastSetup = k.setup; live = k.live; G = geometryOf(lastSetup);
      chartKey = ""; drawSetup(live); drawResult(); later("chart", drawChart); later("window", () => env.windows.redraw());
    },
    onHeader(meta) {
      reset(); H = meta; G = meta.geometry; live = meta.live; env.onHeader(meta);
      drawState(null); drawSetup(meta.live); drawResult(); drawChart();
    },
    onMessage(meta, blobs) {
      if (env.onMessage(meta, blobs)) return;
      switch (meta.type) {
        case "wave": addWave(meta, blobs); later("wave", () => showWave(nowT)); break;  // once, after a batch of messages
        case "tracks": {
          const n = meta.n, xz = blobs.xz, ys = blobs.y;
          slits = blobs.slit; fates = blobs.fate; trackT.push(meta.t);
          for (let k = 0; k < n; k++) { (tracks[k] || (tracks[k] = [])).push(xz[2 * k], xz[2 * k + 1]); }
          const xyz = new Float32Array(3 * n), col = new Float32Array(3 * n);
          for (let k = 0; k < n; k++) { xyz[3 * k] = xz[2 * k]; xyz[3 * k + 1] = ys ? ys[k] : 0.02; xyz[3 * k + 2] = xz[2 * k + 1]; col.set(COLORS[slits[k]] || COLORS[0], 3 * k); }
          env.scene.appendTracks("bohm", xyz, col, { label: "Траектории Бома (по щелям), в 3D" });
          const key = Array.prototype.join.call(slits, "");
          if (key !== lastSlits) { lastSlits = key; env.scene.setTrackColors("bohm", col); }  // a slit became known
          later("window", () => env.windows.redraw());
          break;
        }
        case "hits":
          for (let i = 0; i < meta.count; i++) { hits.x.push(blobs.x[i]); hits.slit.push(blobs.slit[i]); hits.t.push(meta.t); }
          later("chart", drawChart);
          break;
        case "screen": screens.push({ ...meta, P: blobs.P }); later("chart", drawChart); break;
        case "result": result = meta; drawResult(); later("chart", drawChart); break;
        case "setup": lastSetup = meta; G = geometryOf(meta); env.scene.setObject(meta.plate); if (meta.observer) env.scene.setObject(meta.observer); drawSetup(meta.live); live = meta.live; later("window", () => env.windows.redraw()); break;
        default: break;
      }
    },
    render(meta, t, blobs) {
      if (!H || !meta) return;
      nowT = t;
      showWave(t);
      const sc = screenAt(t), key = `${sc ? sc.t : -1}|${hitsUpTo(t)}|${resultNow() ? 1 : 0}`;
      if (key !== chartKey) { chartKey = key; later("chart", drawChart); drawResult(); }
      if (blobs && blobs.pos) {
        const n = blobs.pos.length / 2, xyz = new Float32Array(3 * n), col = new Float32Array(3 * n);
        for (let k = 0; k < n; k++) { xyz[3 * k] = blobs.pos[2 * k]; xyz[3 * k + 1] = blobs.y ? blobs.y[k] : 0.04; xyz[3 * k + 2] = blobs.pos[2 * k + 1]; col.set(COLORS[blobs.slit[k]] || COLORS[0], 3 * k); }
        env.scene.setPoints("particles", xyz, col, { label: "Частицы Бома сейчас" });
      }
      // the panels' tables: a few times a second, and always ending on the frame shown (review C1-17)
      panelMeta = meta;
      const wait = 250 - (performance.now() - lastPanels);
      if (wait <= 0 || meta.done) drawPanels();
      else if (!panelTimer) panelTimer = setTimeout(drawPanels, wait);
      env.scene.requestRender();
    },
  };
}
