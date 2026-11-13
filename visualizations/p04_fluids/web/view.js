// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// p04 view: the fluids playground (plan P15.7). The flow lives in one plane, so its window is the main view (review
// UX-ui U15: it was a side window next to a 3-D view of a flat slab): the picture of the field chosen (speed, vorticity,
// pressure or dye) with the obstacles' outlines, the sides' conditions, the dye sources and the probes over it, across the
// whole centre; the 3-D environment (/static/js/env3d.js: the picture on the plane z = 0, the velocity arrows, the
// obstacles as prisms) is shown beside it on request; the shared playground panels (/static/js/playground.js) and a panel
// to choose the field.
// Drawing only: every picture and number comes from the run.
import { el, fill, num, panel } from "/static/js/ui.js";
import { t, fmt, lang } from "/static/js/i18n.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createPlayground } from "/static/js/playground.js";

function hexRgb(h) { const s = h.replace("#", ""); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16)); }

export function createView(ctx) {
  // the flow's plane z = 0 is seen from above (review UX-3d A3)
  const env = createEnv3D(ctx, { scale: "lin", plane2d: () => 2 });
  env.windows.el.classList.add("wide");
  // the plane's window takes the whole centre; the 3-D view of the flat slab is shown beside it on request (a viewer's
  // choice, kept in this browser)
  let show3d = false;
  try { show3d = localStorage.getItem("p04.show3d") === "1"; } catch (e) { /* storage off: the default layout */ }
  const layoutBtn = el("button", { title: t("Show or hide the 3-D view next to the flow plane") });
  function applyLayout() {
    env.scene.el.style.display = show3d ? "" : "none";
    env.windows.el.style.flex = show3d ? "" : "1 1 100%";
    env.windows.el.style.maxWidth = "none";
    layoutBtn.textContent = show3d ? t("Hide the 3-D view (the flow plane fills the central pane)") : t("Show the 3-D view alongside");
    env.windows.redraw(); env.scene.requestRender();
  }
  layoutBtn.onclick = () => { show3d = !show3d; try { localStorage.setItem("p04.show3d", show3d ? "1" : "0"); } catch (e) { /* ignore */ } applyLayout(); };
  applyLayout();
  // size: the domain as of the latest shapes message (the domain may change in the run: P16.1); every picture carries its
  // own, and the 3-D panel is set to the size of the picture shown (panelSize: what it was set to last)
  let H = null, pics = [], shown = -1, shapes = null, shapesKey = "", size = [1, 1], panelSize = null;
  const pg = createPlayground(ctx, { onSelect: () => { env.windows.redraw(); env.scene.requestRender(); }, describeProbe });
  const fieldSel = el("select", {});
  const fieldBox = el("div", {}, el("div", { class: "ctl" }, el("label", {}, t("Picture")), fieldSel),
    el("div", { class: "help" }, t("Which field of the flow to show (a request to the computer: the physics of the world does not change).")),
    el("div", { class: "ctl" }, layoutBtn));
  fieldSel.onchange = () => { if (!(ctx.readOnly && ctx.readOnly())) ctx.send("view", { op: "field", field: fieldSel.value }); };

  function describeProbe(o, r) {
    return Object.entries(r).map(([k, v]) => [t(k), typeof v === "number" ? num(v, 5) : t(v)]);
  }

  // --- obstacles as prisms (one mesh), the rest drawn in the window ------------------------------------------------
  function drawShapes() {
    if (!shapes) return;
    const key = JSON.stringify(shapes);
    if (key === shapesKey) return;
    shapesKey = key;
    const P = [], C = [], I = [], h = 0.02 * Math.max(size[0], size[1]);
    for (const it of shapes) {
      if (it.shape !== "polygon") continue;
      const rgb = hexRgb(it.color), n = it.pts.length, o = P.length / 3;
      let cx = 0, cy = 0; for (const [x, y] of it.pts) { cx += x / n; cy += y / n; }
      for (const [x, y] of it.pts) { P.push(x, y, -h, x, y, h); C.push(...rgb, ...rgb); }
      P.push(cx, cy, -h, cx, cy, h); C.push(...rgb, ...rgb);
      const c0 = o + 2 * n, c1 = c0 + 1;
      for (let k = 0; k < n; k++) {
        const a = o + 2 * k, b = o + 2 * ((k + 1) % n);
        I.push(a, b, b + 1, a, b + 1, a + 1);       // the side
        I.push(c0, b, a); I.push(c1, a + 1, b + 1); // the caps (a fan from the centre: star-shaped outlines)
      }
    }
    if (P.length) env.scene.setMesh("bodies", new Float32Array(P), I, C, { label: t("Obstacles") });  // solid bodies: opaque and lit (review UX-3d A5)
    else env.scene.removeLayer("bodies");
  }

  function lastAt(list, tw) {
    let lo = 0, hi = list.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (list[m].t <= tw + 1e-30) { k = m; lo = m + 1; } else hi = m - 1; }
    return k;
  }
  function showPic(tw) {
    const k = lastAt(pics, tw);
    if (k < 0 || k === shown) return false;
    shown = k;
    const p = pics[k], [nx, ny] = p.shape, I = new Float32Array(nx * ny), Iw = new Float32Array(nx * ny);
    const sz = p.size || size;
    if (!panelSize || panelSize[0] !== sz[0] || panelSize[1] !== sz[1]) {  // the domain grew or shrank: the plane with it
      const o0 = ((H && H.scene3d.objects) || []).find((o) => o.id === "field");
      if (o0) env.scene.setObject({ ...o0, u: [sz[0], 0, 0], v: [0, sz[1], 0] });
      panelSize = [sz[0], sz[1]];
    }
    for (let ix = 0; ix < nx; ix++) for (let iy = 0; iy < ny; iy++) {
      const a = p.img[ix * ny + iy], v = a === 255 ? -1 : a / 254;
      I[ix * ny + iy] = v < 0 ? 0 : v; Iw[iy * nx + ix] = v;
    }
    env.scene.setPanelImage("field", nx, ny, I);
    const [lo, hi] = p.range;
    const meta = { type: "slice", id: 1, s: [0, sz[0], nx], tt: [0, sz[1], ny], origin: [0, 0, 0], u: [1, 0, 0], v: [0, 1, 0],
                   normal: [0, 0, 1], units: t("m"), coord_names: ["x", "y", "z"], depth: false, fixed: true, label: t("flow plane"),
                   title: t("Flow: {field} ({lo:.3g} … {hi:.3g} {unit})", { field: p.label, lo, hi, unit: p.unit }),
                   // an approximation of the 3-D incompressible flow (review B7 L15): marked as such in the window
                   route_label: t("the lattice Boltzmann method D2Q9 (the Navier–Stokes equations, error ~ Ma²): an approximation"), exact: false, approximation: true,
                   reason: t("a 2-D flow (per metre of depth) instead of 3-D; a weakly compressible scheme: the compressibility error ~ Ma² and its sound waves; curved walls as a staircase (first order) or interpolated; the picture shows means over the fluid at the picture's points"),
                   verify: { note: t("scale from {lo:.4g} to {hi:.4g} {unit}; grey is a solid body", { lo, hi, unit: p.unit }) } };
    env.windows.setSlice(1, meta, { I: Iw, phase: null });
    env.windows.setOverlay(1, overlay);
    if (fieldSel.value !== p.name) fieldSel.value = p.name;
    return true;
  }

  function overlay(g, map) {
    if (!shapes) return;
    const sel = pg.selected ? pg.selected() : null;
    for (const it of shapes) {
      g.strokeStyle = it.color; g.fillStyle = it.color; g.lineWidth = it.id === sel ? 3 : 1.5;
      if (it.shape === "polygon") {
        g.beginPath(); it.pts.forEach(([x, y], i) => { const [a, b] = map(x, y); if (i) g.lineTo(a, b); else g.moveTo(a, b); });
        g.closePath(); g.stroke();
      } else if (it.shape === "circle") {
        const [a, b] = map(it.c[0], it.c[1]), [c] = map(it.c[0] + it.r, it.c[1]);
        g.setLineDash([3, 3]); g.beginPath(); g.arc(a, b, Math.max(2, Math.abs(c - a)), 0, 2 * Math.PI); g.stroke(); g.setLineDash([]);
      } else if (it.shape === "point") {
        const [a, b] = map(it.c[0], it.c[1]); g.beginPath(); g.arc(a, b, 4, 0, 2 * Math.PI); g.fill();
      } else if (it.shape === "sides") {
        g.lineWidth = it.id === sel ? 6 : 4;
        for (const sd of it.sides) {
          const seg = { left: [[0, 0], [0, size[1]]], right: [[size[0], 0], [size[0], size[1]]], bottom: [[0, 0], [size[0], 0]], top: [[0, size[1]], [size[0], size[1]]] }[sd];
          const [a, b] = map(...seg[0]), [c, d] = map(...seg[1]);
          if (it.type === "periodic") g.setLineDash([6, 4]);
          g.beginPath(); g.moveTo(a, b); g.lineTo(c, d); g.stroke(); g.setLineDash([]);
        }
      }
    }
  }

  return {
    center: env.center,
    leftPanels: pg.leftPanels,
    rightPanels: [panel(t("Flow picture"), fieldBox), ...pg.rightPanels, panel(t("Scene layers"), env.layersPanel)],
    help: () => el("div", {},
      el("h4", {}, t("Laboratory: fluids")),
      el("p", {}, t("Add obstacles (cylinders, rectangles, wing profiles), flow inlets and outlets on the sides of the domain, moving walls, periodicity, dye and velocity probes at the current moment. The flow is computed by the lattice Boltzmann method (the incompressible Navier–Stokes equations in a plane).")),
      el("p", {}, t("The picture is the chosen field (speed, vorticity, pressure, dye); the arrows are the velocity. The forces on the bodies (drag and lift, their coefficients) are in the body's “now” and in “Checks”: over the last step (they contain the scheme's standing sound wave) and averaged over the domain's sound period (the window is given); there too are the balances of mass, momentum and dye and the Mach and cell Reynolds numbers (stability limits, not accuracy ones).")),
      el("p", {}, t("If the scene is the set-up of a published test (the DFG channel with a cylinder, the Ghia cavity, a Poiseuille channel with a probe), “Checks” (the group “Benchmarks”) show the published range next to the computed number and what the agreement needs (the grid, the wall, a steady flow)."))),
    reset() { env.reset(); pg.reset(); H = null; pics = []; shown = -1; shapes = null; shapesKey = ""; size = [1, 1]; panelSize = null; },
    snapshot() { return { env: env.snapshot(), pg: pg.snapshot(), np: pics.length, shapes, size }; },
    restore(k) {
      env.restore(k.env); pg.restore(k.pg);
      pics.length = k.np; shown = -1; shapes = k.shapes; shapesKey = ""; size = k.size || size; panelSize = null; drawShapes();
    },
    onHeader(meta) {
      H = meta; size = meta.grid.size; panelSize = null;
      fill(fieldSel, ...Object.entries(meta.fields).map(([v, lab]) => el("option", { value: v }, t(lab))));
      fieldSel.value = meta.shown;
      env.onHeader(meta); pg.onHeader(meta); ctx.setScene && ctx.setScene(meta.title);
    },
    onMessage(meta, blobs) {
      if (pg.onMessage(meta, blobs)) return;
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "field") pics.push({ t: meta.t, name: meta.name, label: meta.label, unit: meta.unit, range: meta.range, shape: meta.shape, size: meta.size, img: blobs.img });
      else if (meta.type === "shapes") { shapes = meta.items; size = meta.size || size; drawShapes(); }
    },
    render(frame, tw) {
      if (!H || !frame) return;
      if (!showPic(tw)) env.windows.redraw();
      pg.render(frame, tw);
      env.scene.requestRender();
    },
  };
}
