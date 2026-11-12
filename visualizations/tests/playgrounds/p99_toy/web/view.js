// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The toy playground's view (tests only): the shared panels, the 3-D environment with the particles as spheres, the
// probes as small spheres and the walls as thin boxes at the run's positions (frame `at`, `pos`, `rad`), and the plane
// z = 0 as a fixed window (no field is computed there: an empty picture under the objects' marks), so that the
// framework's direct manipulation can be tested in the scene and in a window (plan P16.2). Drawing only.
import { t } from "/static/js/i18n.js";
import { el } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createPlayground } from "/static/js/playground.js";

const N = 32;  // the plane's picture: N x N cells, all zero (nothing is computed on it)

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin", plane2d: (H) => (H.toy && H.toy.ndim === 2 ? 2 : null) });
  const pg = createPlayground(ctx, { onSelect: () => { env.windows.redraw(); env.scene.requestRender(); }, env });
  const out = el("pre", { id: "toy-pos", style: { display: "none" } });
  let H = null, frame = null, walls = new Map();  // a wall's layer -> what it was drawn with

  function planeWindow() {
    const h = H.toy.half;
    env.windows.setSlice(1, { type: "slice", id: 1, s: [-h, h, N], tt: [-h, h, N], origin: [0, 0, 0], u: [1, 0, 0], v: [0, 1, 0],
      normal: [0, 0, 1], units: "m", coord_names: ["x", "y", "z"], depth: false, fixed: true, label: t("the plane z = 0"),
      title: t("The plane z = 0 (toy: no field is computed)"), route_label: t("only the objects' positions"), exact: true,
      quantity: { label: "—", unit: "", peak: 1 }, verify: { note: t("the marks are the objects' positions from the frame") } },
    { I: new Float32Array(N * N), phase: null });
    env.windows.setOverlay(1, overlay);
  }
  // the objects' marks in the plane's coordinates (from the frame shown)
  function overlay(g, map) {
    if (!frame || !frame.at) return;
    for (const o of pg.objects()) {
      const p = frame.at[o.id]; if (!p) continue;
      if (o.type === "particle" || o.type === "probe") {
        const [a, b] = map(p[0], p[1]), [c] = map(p[0] + (o.values.r || 0.12), p[1]);
        g.fillStyle = o.type === "particle" ? "#4dabf7" : "#ff922b";
        g.beginPath(); g.arc(a, b, Math.max(3, Math.abs(c - a)), 0, 2 * Math.PI); g.fill();
      } else {
        const ax = { x: 0, y: 1, z: 2, 0: 0, 1: 1, 2: 2 }[o.values.axis];
        if (ax === 2) continue;  // a wall across z is not seen in the plane z = 0
        const h = H.toy.half, q0 = [...p], q1 = [...p];
        q0[1 - ax] = -h; q1[1 - ax] = h;
        const [a, b] = map(q0[0], q0[1]), [c, d] = map(q1[0], q1[1]);
        g.strokeStyle = "#adb5bd"; g.lineWidth = 3; g.beginPath(); g.moveTo(a, b); g.lineTo(c, d); g.stroke();
      }
    }
  }
  function drawWalls() {
    const seen = new Map(), h = H.toy.half, zh = H.toy.ndim === 2 ? 0.2 : h;
    for (const o of pg.objects()) {
      if (!["wall", "mirror", "screen"].includes(o.type) || !frame || !frame.at[o.id]) continue;
      const ax = { x: 0, y: 1, z: 2, 0: 0, 1: 1, 2: 2 }[o.values.axis], size = [2 * h, 2 * h, 2 * zh];
      size[ax] = 0.04 * h;
      const key = JSON.stringify([frame.at[o.id], size, o.label]);
      if (walls.get(`wall_${o.id}`) !== key) env.scene.setObject({ id: `wall_${o.id}`, kind: "box", center: frame.at[o.id], size, color: "#adb5bd", opacity: 0.35, label: o.label });
      seen.set(`wall_${o.id}`, key);
    }
    for (const id of walls.keys()) if (!seen.has(id)) env.scene.removeLayer(id);
    walls = seen;
  }

  return {
    center: el("div", { style: { display: "contents" } }, env.center, out), leftPanels: pg.leftPanels,
    rightPanels: [...pg.rightPanels],
    reset() { env.reset(); pg.reset(); H = null; frame = null; for (const id of walls.keys()) env.scene.removeLayer(id); walls = new Map(); },
    snapshot() { return { env: env.snapshot(), pg: pg.snapshot() }; },
    restore(k) { env.restore(k.env); pg.restore(k.pg); },
    onHeader(meta) { H = meta; env.onHeader(meta); pg.onHeader(meta); planeWindow(); },
    onMessage(meta, blobs) { if (pg.onMessage(meta, blobs)) return; env.onMessage(meta, blobs); },
    render(f, tt, blobs) {
      if (!H || !f) return;
      frame = f;
      const pos = blobs.pos || new Float32Array(0), n = pos.length / 3, rgb = new Float32Array(3 * n);
      for (let i = 0; i < n; i++) rgb.set([0.3, 0.67, 0.97], 3 * i);
      env.scene.setSpheres("particles", pos, blobs.rad || new Float32Array(n), rgb, { label: t("Particles") });
      const probes = pg.objects().filter((o) => o.type === "probe" && f.at && f.at[o.id]);
      const pp = new Float32Array(probes.flatMap((o) => f.at[o.id])), pr = new Float32Array(probes.length).fill(0.12);
      env.scene.setSpheres("probes", pp, pr, new Float32Array(probes.flatMap(() => [1, 0.57, 0.17])), { label: t("Probes") });
      drawWalls();
      out.textContent = JSON.stringify({ t: tt, ids: f.ids, pos: Array.from(pos) });
      pg.render(f, tt, blobs);
      env.windows.redraw();
      env.scene.requestRender();
    },
  };
}
