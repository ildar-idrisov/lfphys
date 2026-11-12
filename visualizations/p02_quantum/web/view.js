// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// p02 view: the quantum playground (plan P15.3). The 3-D environment (/static/js/env3d.js) with the scene's objects
// (barriers and wells, walls with slits, traps, fields, flux tubes, detectors, markers, the environment's region, flux
// planes: from the run's "shapes" message, the engine's own bounding boxes), the wave |psi|^2 summed over the
// particles (in a plane: an image on the plane z = 0; in space: a volume) and the Bohm points; next to it the window of
// the plane (|psi|^2, amplitude, log, or the phase of a single particle) with the objects' outlines, the Bohm points
// and the outcomes of position measurements over it; the shared playground panels (/static/js/playground.js).
// In a plane the wave lives in that plane, so its window is the main view and takes the whole centre; the 3-D view of
// the flat slab is shown beside it on request (review UX-ui U15, as p04's flow; the choice kept in this browser). In
// space the 3-D view stays the main view, with the slice z = 0 beside it. The grid and the window change at the current
// moment (plan P16.1): the run's "grid" message (with a "box") gives the new axes; the plane's picture follows.
// Drawing only: every number and picture comes from the run.
import { el, fill, num, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createPlayground } from "/static/js/playground.js";

const CATS = [
  { id: "pot", label: "Потенциалы (барьеры, ямы, стенки, ловушки)", types: ["box", "ball", "slit_wall", "step", "trap"], opacity: 0.35 },
  { id: "det", label: "Детекторы и метки пути", types: ["detector", "marker"], opacity: 0.25 },
  { id: "fld", label: "Поля, трубки потока, среда", types: ["bfield", "flux", "env"], opacity: 0.15 },
  { id: "pln", label: "Плоскости потока", types: ["plane"], opacity: 0.2 },
];

function hexRgb(h) { const s = h.replace("#", ""); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16)); }

export function createView(ctx) {
  // a 2-D world (the plane z = 0) opens looking at its plane from above (review UX-3d A3)
  const env = createEnv3D(ctx, { scale: "sqrt", logFloor: () => 1e-6, plane2d: (H) => (H.grid && H.grid.ndim === 2 ? 2 : null) });
  env.windows.el.classList.add("wide");
  // the layout: in a plane the wave's window fills the centre and the 3-D view is shown on request (review UX-ui U15)
  let show3d = false, plane = true;
  try { show3d = localStorage.getItem("p02.show3d") === "1"; } catch (e) { /* storage off: the default layout */ }
  const layoutBtn = el("button", { title: "Показать или скрыть 3D-вид рядом с плоскостью опыта" });
  const viewBox = el("div", {});
  function applyLayout() {
    const side = plane && !show3d;  // the window alone, across the whole centre
    env.scene.el.style.display = side ? "none" : "";
    env.windows.el.style.flex = side ? "1 1 100%" : "";
    env.windows.el.style.maxWidth = side ? "none" : "";
    layoutBtn.textContent = show3d ? "Скрыть 3D-вид (плоскость опыта — во весь центр)" : "Показать 3D-вид рядом";
    fill(viewBox, plane
      ? [el("div", { class: "help" }, "Волна живёт в плоскости (x, y): её окно — главный вид. 3D-вид показывает ту же плоскость как пластину в пространстве с объектами сцены."), el("div", { class: "ctl" }, layoutBtn)]
      : el("div", { class: "help" }, "Мир в объёме: главный вид — 3D-сцена, рядом — срез z = 0."));
    env.windows.redraw(); env.scene.requestRender();
  }
  layoutBtn.onclick = () => { show3d = !show3d; try { localStorage.setItem("p02.show3d", show3d ? "1" : "0"); } catch (e) { /* ignore */ } applyLayout(); };
  applyLayout();
  let H = null, G = null, gridRaw = null, gridKey = "", volFresh = false, waves = [], vols = [], shownWave = -1, shownVol = -1, shapes = null, shapesKey = "";
  let marks = [], pts = null;
  const pg = createPlayground(ctx, { onSelect: () => { env.windows.redraw(); env.scene.requestRender(); }, describeProbe, env });

  function describeProbe(o, r) {
    return Object.entries(r).map(([k, v]) => [k, typeof v === "number" ? num(v, 6) : Array.isArray(v) ? v.map((x) => num(x, 4)).join(", ") : String(v)]);
  }

  // --- the scene's objects as meshes (boxes, cylinders, spheres), one mesh per category -------------------------------
  function bounds(it) {
    const lo = it.lo.map((v, i) => (v === null || v === undefined ? G.lo[i] : v)), hi = it.hi.map((v, i) => (v === null || v === undefined ? G.hi[i] : v));
    if (G.ndim === 2) {  // a slab through the plane of the wave: barriers above it, the rest thinner
      const h = 0.5 * (G.hi[2] - G.lo[2]) * (it.type === "plane" ? 1 : ["detector", "marker"].includes(it.type) ? 0.35 : 0.5);
      lo[2] = -h; hi[2] = h;
    }
    for (let i = 0; i < 3; i++) if (hi[i] - lo[i] < 1e-9) { const e = 0.002 * G.size; lo[i] -= e; hi[i] += e; }  // a plane: a thin slab
    return [lo, hi];
  }
  function addBox(B, lo, hi, rgb) {
    const o = B.P.length / 3;
    for (let k = 0; k < 8; k++) B.P.push(k & 1 ? hi[0] : lo[0], k & 2 ? hi[1] : lo[1], k & 4 ? hi[2] : lo[2]);
    for (let k = 0; k < 8; k++) B.C.push(...rgb);
    const F = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]];
    for (const [a, b, c, d] of F) B.I.push(o + a, o + b, o + c, o + a, o + c, o + d);
  }
  function addCylinder(B, c, r, z0, z1, rgb, n = 32) {
    const o = B.P.length / 3;
    for (let k = 0; k < n; k++) {
      const a = 2 * Math.PI * k / n, x = c[0] + r * Math.cos(a), y = c[1] + r * Math.sin(a);
      B.P.push(x, y, z0, x, y, z1); B.C.push(...rgb, ...rgb);
    }
    for (let k = 0; k < n; k++) { const a = o + 2 * k, b = o + 2 * ((k + 1) % n); B.I.push(a, b, b + 1, a, b + 1, a + 1); }
  }
  function addSphere(B, c, r, rgb, n = 16) {
    const o = B.P.length / 3;
    for (let i = 0; i <= n; i++) for (let j = 0; j <= 2 * n; j++) {
      const th = Math.PI * i / n, ph = Math.PI * j / n;
      B.P.push(c[0] + r * Math.sin(th) * Math.cos(ph), c[1] + r * Math.sin(th) * Math.sin(ph), c[2] + r * Math.cos(th)); B.C.push(...rgb);
    }
    const w = 2 * n + 1;
    for (let i = 0; i < n; i++) for (let j = 0; j < 2 * n; j++) { const a = o + i * w + j; B.I.push(a, a + w, a + w + 1, a, a + w + 1, a + 1); }
  }
  function drawShapes() {
    if (!G || !shapes) return;
    const key = JSON.stringify(shapes);
    if (key === shapesKey) return;
    shapesKey = key;
    for (const cat of CATS) {
      const B = { P: [], C: [], I: [] };
      for (const it of shapes.filter((q) => cat.types.includes(q.type))) {
        const rgb = hexRgb(it.color);
        if (it.shape === "box" || it.shape === "plane") { const [lo, hi] = bounds(it); addBox(B, lo, hi, rgb); }
        else if (it.shape === "cylinder") {
          const h = G.ndim === 2 ? 0.5 * (G.hi[2] - G.lo[2]) * 0.5 : 0;
          addCylinder(B, it.center, it.r, G.ndim === 2 ? -h : G.lo[2], G.ndim === 2 ? h : G.hi[2], rgb);
        } else if (it.shape === "ball") {
          if (G.ndim === 2) { const h = 0.25 * (G.hi[2] - G.lo[2]); addCylinder(B, it.center, it.r, -h, h, rgb); }
          else addSphere(B, it.center, it.r, rgb);
        }
      }
      if (B.P.length) env.scene.setMesh(cat.id, new Float32Array(B.P), B.I, B.C, { label: cat.label, opacity: cat.opacity });
      else env.scene.removeLayer(cat.id);
    }
  }

  // --- the grid in force: the header's, or the last "grid" message (a live change of the grid or the window) ----------
  function setGrid(grid) {
    gridRaw = grid;
    G = { ...grid, lo: [grid.x[0], grid.y[0], grid.z[0]], hi: [grid.x[1], grid.y[1], grid.z[1]] };
    const key = JSON.stringify(grid);
    if (key === gridKey) return;
    gridKey = key;
    if (G.ndim === 2) {  // the wave's plate spans the new window
      env.scene.setObject({ id: "wave", label: "Волна |ψ|² (сумма по частицам)", kind: "panel", origin: [G.lo[0], G.lo[1], 0],
                            u: [G.hi[0] - G.lo[0], 0, 0], v: [0, G.hi[1] - G.lo[1], 0], visible: true });
    }
    shownWave = -1; shownVol = -1; shapesKey = ""; drawShapes();
    volFresh = true;  // the volume spans the box: set it anew (the same number of voxels may fill another window)
  }

  // --- the wave: accumulative pictures, the one shown is the last at or before the time shown --------------------------
  function lastAt(list, t) {
    let lo = 0, hi = list.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (list[m].t <= t + 1e-30) { k = m; lo = m + 1; } else hi = m - 1; }
    return k;
  }
  function showWave(t) {
    const k = lastAt(waves, t);
    if (k < 0 || k === shownWave) return;
    shownWave = k;
    const w = waves[k], [nx, ny] = w.shape, I = new Float32Array(nx * ny), Iw = new Float32Array(nx * ny);
    const Pw = w.phase ? new Float32Array(nx * ny) : null;
    for (let ix = 0; ix < nx; ix++) for (let iy = 0; iy < ny; iy++) {
      const a = w.amp[ix * ny + iy] / 255, v = a * a;
      I[ix * ny + iy] = v; Iw[iy * nx + ix] = v;
      if (Pw) Pw[iy * nx + ix] = w.phase[ix * ny + iy] / 255 * 2 * Math.PI - Math.PI;
    }
    if (G.ndim === 2) env.scene.setPanelImage("wave", nx, ny, I);
    const z = G.ndim === 2 ? 0 : 0.5 * (G.lo[2] + G.hi[2]);
    const meta = { type: "slice", id: 1, s: [w.x[0], w.x[1], nx], tt: [w.y[0], w.y[1], ny], origin: [0, 0, z], u: [1, 0, 0], v: [0, 1, 0],
                   normal: [0, 0, 1], units: "нм", coord_names: ["x", "y", "z"], depth: false, fixed: true,
                   label: G.ndim === 2 ? "плоскость опыта" : "срез z = 0",
                   title: G.ndim === 2 ? "Волна |ψ|² (сумма по частицам, доли пика)" : "Срез z = 0: |ψ|² (сумма по частицам, доли пика)",
                   route_label: "уравнение Шрёдингера (Паули) на сетке, расщепление оператора", exact: true, approximation: false,
                   verify: { note: `пик ${num(w.peak, 3)} нм⁻${G.ndim}, в окне ${num(w.total, 4)} вероятности (сумма по частицам)${Pw ? "; фаза — единственной частицы" : ""}` } };
    env.windows.setSlice(1, meta, { I: Iw, phase: Pw });
    env.windows.setOverlay(1, overlay);
  }
  function showVolume(t) {
    const k = lastAt(vols, t);
    if (k < 0 || k === shownVol) return;
    shownVol = k;
    const V = vols[k], data = new Float32Array(V.data.length);
    for (let i = 0; i < data.length; i++) { const a = V.data[i] / 255; data[i] = a * a; }
    if (volFresh || !env.scene.updateVolume("wave3d", data)) env.scene.setVolume("wave3d", V.dims, data);
    volFresh = false;
  }

  // --- the window's overlay: outlines of the objects, Bohm points, measured positions -------------------------------
  function overlay(g, map) {
    if (!shapes) return;
    const sel = pg.selected ? pg.selected() : null;
    for (const it of shapes) {
      g.strokeStyle = it.color; g.lineWidth = it.id === sel ? 2.5 : 1; g.globalAlpha = 0.9;
      if (it.shape === "box" || it.shape === "plane") {
        const lo = it.lo.map((v, i) => (v === null ? G.lo[i] : v)), hi = it.hi.map((v, i) => (v === null ? G.hi[i] : v));
        const [a, b] = map(lo[0], lo[1]), [c, d] = map(hi[0], hi[1]);
        if (it.shape === "plane") { g.beginPath(); g.moveTo(a, b); g.lineTo(c, d); g.stroke(); }
        else g.strokeRect(Math.min(a, c), Math.min(b, d), Math.abs(c - a), Math.abs(d - b));
      } else {
        const [a, b] = map(it.center[0], it.center[1]), [c] = map(it.center[0] + it.r, it.center[1]);
        g.beginPath(); g.arc(a, b, Math.abs(c - a), 0, 2 * Math.PI); g.stroke();
      }
    }
    g.globalAlpha = 1;
    if (pts) {
      const { pos, rgb } = pts;
      for (let i = 0; i < pos.length / 3; i++) {
        const [a, b] = map(pos[3 * i], pos[3 * i + 1]);
        g.fillStyle = `rgb(${Math.round(255 * rgb[3 * i])},${Math.round(255 * rgb[3 * i + 1])},${Math.round(255 * rgb[3 * i + 2])})`;
        g.fillRect(a - 1.5, b - 1.5, 3, 3);
      }
    }
    g.strokeStyle = "#ffffff"; g.lineWidth = 1.5;
    for (const m of marks) { const [a, b] = map(m[0], m[1]); g.beginPath(); g.moveTo(a - 5, b - 5); g.lineTo(a + 5, b + 5); g.moveTo(a - 5, b + 5); g.lineTo(a + 5, b - 5); g.stroke(); }
  }
  return {
    center: env.center,
    leftPanels: pg.leftPanels,
    rightPanels: [panel("Вид", viewBox), ...pg.rightPanels, panel("Слои сцены", env.layersPanel)],
    help: () => el("div", {},
      el("h4", {}, "Плейграунд: квантовые частицы"),
      el("p", {}, "Добавляйте из палитры частицы (волновые пакеты электрона, нейтрона, атомов), барьеры и ямы, стенки со щелями, ловушку, магнитное поле, трубку потока Ааронова–Бома, детекторы, метку пути, среду, плоскости потока — и меняйте их на ходу в инспекторе. Каждая частица — своя волна по уравнению Шрёдингера (Паули для спина); частицы не взаимодействуют."),
      el("p", {}, "Картина — |ψ|², сумма по частицам (каждая — своя вероятность). Детекторы поглощают вероятность: сколько поглотил каждый — в «Датчиках» и в «сейчас» частицы. «Измерить положение» (действие) сжимает волну к исходу по правилу Борна; крестик — исход."),
      el("p", {}, "Частицы Бома (параметр частицы) — интерпретация: точки, ведомые током вероятности; вошедшая в детектор точка им зарегистрирована и остановлена (тусклая)."),
      el("p", {}, "Проверки: норма + поглощённое = 1, энергия замкнутой системы против строгой границы из ошибки шага, поток через плоскости, ошибка шага (компаньон), качество сетки, отражение краёв окна, стоимость шага.")),
    reset() { env.reset(); pg.reset(); H = null; G = null; gridRaw = null; gridKey = ""; volFresh = false; waves = []; vols = []; shownWave = -1; shownVol = -1; shapes = null; shapesKey = ""; marks = []; pts = null; },
    snapshot() { return { env: env.snapshot(), pg: pg.snapshot(), nw: waves.length, nv: vols.length, shapes, marks, grid: gridRaw }; },
    restore(k) {
      env.restore(k.env); pg.restore(k.pg);
      waves.length = k.nw; vols.length = k.nv; shownWave = -1; shownVol = -1;
      if (k.grid) setGrid(k.grid);  // the grid of the key frame (a live change after it is undone)
      shapes = k.shapes; marks = k.marks; shapesKey = ""; drawShapes();
    },
    onHeader(meta) {
      H = meta; G = { ...meta.grid, lo: meta.scene3d.box[0], hi: meta.scene3d.box[1] }; gridRaw = meta.grid; gridKey = JSON.stringify(meta.grid);
      plane = G.ndim === 2; applyLayout();
      env.onHeader(meta); pg.onHeader(meta); ctx.setScene && ctx.setScene(meta.title);
    },
    onMessage(meta, blobs) {
      if (pg.onMessage(meta, blobs)) return;
      if (meta.type === "grid") { setGrid(meta.grid); return; }
      if (meta.type === "marks") { const p = blobs.pos || []; marks = []; for (let i = 0; i < p.length / 3; i++) marks.push([p[3 * i], p[3 * i + 1], p[3 * i + 2]]); }
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "wave") waves.push({ t: meta.t, shape: meta.shape, peak: meta.peak, total: meta.total, x: meta.x, y: meta.y, amp: blobs.amp, phase: blobs.phase || null });
      else if (meta.type === "wave3d") vols.push({ t: meta.t, dims: meta.dims, data: blobs.data });
      else if (meta.type === "shapes") { shapes = meta.items; drawShapes(); }
    },
    render(frame, t, blobs) {
      if (!H || !frame) return;
      const k0 = shownWave;
      showWave(t);  // a new picture redraws the window with its overlay
      if (G.ndim === 3) showVolume(t);
      const pos = blobs.pos || new Float32Array(0), rgb = blobs.rgb || new Float32Array(0), rad = blobs.rad || new Float32Array(0);
      pts = { pos, rgb };
      env.scene.setSpheres("bohm", pos, rad, rgb, { label: "Частицы Бома (интерпретация)" });
      if (shownWave === k0) env.windows.redraw();  // the same picture: the overlay's points moved
      pg.render(frame, t);
      env.scene.requestRender();
    },
  };
}
